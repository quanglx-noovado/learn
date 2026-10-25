# Chương 12. EXPLAIN và tối ưu truy vấn

> [← Mục lục](README.md) · [← Chương 11: Index](11-index.md) · [Chương 13: Transaction và ACID →](13-transaction-acid.md)

**Bạn sẽ học được:**

- Query optimizer là gì, vì sao MySQL phải "chọn" cách chạy một câu SQL, và chọn dựa trên cái gì
  (cost model, statistics, histogram).
- Đọc thành thạo `EXPLAIN` dạng bảng (các cột `type`, `key`, `key_len`, `rows`, `filtered`, `Extra`),
  dạng cây `FORMAT=TREE`, và `EXPLAIN ANALYZE` với số đo thật.
- Hiểu hai thuật toán join của MySQL (nested loop và hash join) và nhận ra chúng trong plan.
- Tìm ra query chậm trên server thật bằng slow query log, `performance_schema`, schema `sys` và
  `pt-query-digest`, rồi đi theo một quy trình tối ưu có thứ tự.
- Giải các bài kinh điển: phân trang sâu (OFFSET và keyset), `COUNT(*)` trên bảng lớn, update/delete
  hàng triệu dòng theo batch.
- Biết khi nào và cách dùng optimizer hint, `FORCE INDEX`, và vì sao chúng là giải pháp cuối cùng.

**Cần biết trước:** [Chương 05](05-select-co-ban.md) (SELECT, thứ tự thực thi logic, `LIMIT`),
[Chương 07](07-join.md) (JOIN), [Chương 08](08-group-by-aggregate.md) (`GROUP BY`, `COUNT`),
[Chương 09](09-subquery-cte-union.md) (subquery, recursive CTE dùng để sinh dữ liệu), và quan trọng
nhất [Chương 11](11-index.md) (B+tree, clustered index, secondary index, composite index và quy tắc
leftmost prefix, covering index). Chương này giả định bạn đã hiểu index là gì; ở đây ta học cách
nhìn xem MySQL có dùng index đó không và dùng như thế nào.

## 1. Dữ liệu mẫu của chương

Muốn thấy optimizer làm việc thì bảng phải đủ lớn: với vài chục dòng, quét cả bảng luôn rẻ nhất và
mọi plan trông giống nhau. Chương này dùng một bảng một triệu đơn hàng và mười nghìn người dùng.

Chạy MySQL 8.4 bằng Docker nếu chưa có (xem [Chương 01](01-database-la-gi.md)):

```bash
# Chạy trên máy của bạn (terminal thường)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi vài giây cho server khởi động xong, rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Dán đoạn SQL sau vào client `mysql`. Dữ liệu được sinh theo công thức (không dùng `RAND()`), nên trên
máy bạn ra đúng cùng dữ liệu như trong sách và bạn có thể tự kiểm các con số đếm:

```sql
DROP DATABASE IF EXISTS ch12;      -- database riêng của chương, xoá đi tạo lại cho sạch
CREATE DATABASE ch12;
USE ch12;

CREATE TABLE users (
  id      BIGINT PRIMARY KEY,
  name    VARCHAR(50) NOT NULL,
  country CHAR(2)     NOT NULL
);

CREATE TABLE orders (
  id         BIGINT PRIMARY KEY,
  user_id    BIGINT        NOT NULL,
  status     VARCHAR(10)   NOT NULL,      -- 'paid' | 'pending' | 'cancelled'
  total      DECIMAL(12,2) NOT NULL,
  created_at DATETIME      NOT NULL
);

-- Recursive CTE mặc định chỉ cho đệ quy 1000 tầng (Chương 09); nâng lên để sinh 1 triệu dòng.
SET SESSION cte_max_recursion_depth = 1000000;

INSERT INTO users
WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 10000)
SELECT n, CONCAT('user', n), IF(n % 100 = 0, 'VN', 'US') FROM s;      -- 100 user VN, 9900 user US

INSERT INTO orders
WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 1000000)
SELECT n,                                                          -- id
       1 + n % 10000,                                              -- user_id: mỗi user đúng 100 đơn
       ELT(1 + (n DIV 10000) % 3, 'paid', 'pending', 'cancelled'),  -- trạng thái xoay vòng
       (n * 7919) % 50000 / 100,                                   -- total từ 0 tới 499.99
       '2025-01-01' + INTERVAL (n DIV 2) MINUTE                     -- cứ 2 đơn chung một phút
FROM s;

ANALYZE TABLE users, orders;       -- tính thống kê ngay (mục 5 giải thích)
```

Lệnh `INSERT` thứ hai mất từ vài giây tới vài chục giây tuỳ máy. Kiểm tra nhanh:

```sql
SELECT COUNT(*) FROM orders;                                   -- 1000000
SELECT status, COUNT(*) FROM orders WHERE user_id = 42 GROUP BY status;
-- paid 34, pending 33, cancelled 33  (thứ tự dòng có thể khác)
SELECT MIN(created_at), MAX(created_at) FROM orders;
-- 2025-01-01 00:00:00 | 2025-12-14 05:20:00
```

Vì sao user 42 có 34 đơn `paid`: các đơn của user 42 là những `n` có `n % 10000 = 41`, tức
`n = 41, 10041, 20041, ..., 990041` (100 giá trị, `n DIV 10000` chạy từ 0 tới 99). Trạng thái là
`paid` khi `(n DIV 10000) % 3 = 0`, tức 0, 3, 6, ..., 99: có 34 số như vậy.

Bảng hiện chỉ có PRIMARY KEY, chưa có index phụ nào. Ta sẽ thêm index dần trong chương và quan sát plan
thay đổi.

⚠️ Mọi output `EXPLAIN`, `EXPLAIN ANALYZE`, slow log trong chương này là **output minh hoạ** theo định
dạng của MySQL 8.4, không phải chạy thật để chép vào. Các con số `cost`, `rows` ước lượng, thời gian
trên máy bạn sẽ khác (đôi khi cả cách trình bày một dòng cũng khác chút ít). Điều cần học là cách đọc
và xu hướng thay đổi; hãy tự chạy để thấy số thật.

## 2. Query optimizer là gì

### 2.1 Một câu SQL có nhiều cách chạy

SQL là ngôn ngữ *khai báo* (*declarative*): bạn nói muốn **cái gì**, không nói **làm thế nào**.
Câu sau:

```sql
SELECT u.name, o.total
FROM users u JOIN orders o ON o.user_id = u.id
WHERE u.country = 'VN' AND o.status = 'paid';
```

có thể được thực hiện theo nhiều cách khác nhau, tất cả cho cùng một kết quả:

- Quét `users`, giữ user VN, với mỗi user đó tìm đơn của họ trong `orders`.
- Quét `orders`, giữ đơn `paid`, với mỗi đơn tra user tương ứng trong `users` theo PK rồi kiểm country.
- Đọc cả hai bảng, dựng bảng băm trên một bên rồi dò bên kia (hash join, mục 6).
- Với mỗi bảng: quét toàn bộ, hay dùng index nào (nếu có vài index), đọc index rồi quay về bảng hay
  chỉ đọc index...

Số phương án tăng rất nhanh theo số bảng: với `n` bảng có `n!` thứ tự join (5 bảng là 120 thứ tự, 10
bảng là hơn 3,6 triệu), nhân thêm số cách truy cập mỗi bảng. Các phương án có thể chênh nhau hàng
nghìn lần về thời gian. Thành phần của MySQL chịu trách nhiệm chọn phương án gọi là *query optimizer*
(gọi tắt là *optimizer*), và phương án được chọn gọi là *execution plan* (*query plan*, gọi tắt là
*plan*).

### 2.2 Đường đi của một câu lệnh trong server

Một cách hình dung đơn giản (gộp bớt chi tiết) những gì xảy ra khi client gửi một câu `SELECT`:

```
  client gửi chuỗi SQL
          │
          ▼
  ┌───────────────┐   tách từ, kiểm cú pháp → cây cú pháp
  │    Parser     │   (sai cú pháp: lỗi 1064 ở bước này)
  └───────┬───────┘
          ▼
  ┌───────────────┐   tên bảng/cột có tồn tại không, quyền, kiểu dữ liệu,
  │ Resolver /    │   mở rộng SELECT *, gắn cột với bảng
  │ Prepare       │
  └───────┬───────┘
          ▼
  ┌───────────────┐   1. biến đổi logic: bỏ điều kiện thừa, gộp hằng số,
  │   Optimizer   │      chuyển subquery thành semijoin, gộp derived table...
  │               │   2. chọn theo chi phí: thứ tự join, cách đọc từng bảng,
  │               │      thuật toán join, có cần sort/bảng tạm không
  └───────┬───────┘          ▲ đọc statistics từ storage engine (InnoDB)
          ▼
  ┌───────────────┐   chạy plan: cây các iterator, mỗi iterator kéo
  │   Executor    │   từng dòng từ iterator con
  └───────┬───────┘          ▲ gọi InnoDB đọc dòng / đọc index
          ▼
  kết quả trả về client
```

`EXPLAIN` cho bạn xem kết quả của bước Optimizer mà không chạy bước Executor. `EXPLAIN ANALYZE` chạy
cả hai và đo bước Executor.

### 2.3 Rule-based và cost-based

Có hai triết lý để chọn plan:

- *Rule-based optimizer*: dùng các luật cố định, ví dụ "có index trên cột trong `WHERE` thì dùng
  index". Đơn giản, đoán trước được, nhưng sai khi dữ liệu không như luật giả định: nếu 90% dòng
  thoả điều kiện, dùng index (tra từng dòng một ở vị trí ngẫu nhiên) chậm hơn quét thẳng cả bảng.
- *Cost-based optimizer*: với mỗi phương án, **ước lượng chi phí** (số dòng phải đọc, số page phải
  đọc, số lần so sánh, có sort không...) rồi chọn phương án có chi phí ước lượng thấp nhất.

MySQL (và PostgreSQL, Oracle, SQL Server) dùng cost-based optimizer. Hệ quả quan trọng nhất cho người
viết query:

1. Plan phụ thuộc vào **dữ liệu**, không chỉ vào câu SQL và index. Cùng một câu, cùng index, trên máy
   dev 1.000 dòng và production 10 triệu dòng có thể ra plan khác nhau. Vì vậy phải `EXPLAIN` trên dữ
   liệu có kích thước và phân bố giống thật.
2. Plan phụ thuộc vào **ước lượng**. Ước lượng sai thì plan sai, dù query và index không đổi một chữ.
   Nguồn của ước lượng là *statistics* (mục 5).
3. "Chi phí thấp nhất" là theo **mô hình**, không phải theo đồng hồ. Mô hình có thể lệch thực tế, ví
   dụ không biết page nào đang nằm sẵn trong RAM.

### 2.4 Cost model của MySQL

*Cost model* là bộ công thức và hằng số để quy mọi thao tác ra một con số chi phí chung. MySQL giữ các
hằng số này trong hai bảng hệ thống:

- `mysql.server_cost`: chi phí các thao tác ở tầng server, ví dụ `row_evaluate_cost` (đánh giá điều
  kiện trên một dòng), `key_compare_cost` (so sánh khoá, ảnh hưởng chi phí sort),
  `memory_temptable_create_cost`, `disk_temptable_row_cost` (bảng tạm trong RAM và trên đĩa).
- `mysql.engine_cost`: chi phí phía storage engine, chủ yếu `io_block_read_cost` (đọc một block từ
  đĩa) và `memory_block_read_cost` (đọc một block đã nằm trong buffer).

```sql
SELECT cost_name, cost_value, default_value FROM mysql.server_cost;
SELECT engine_name, cost_name, cost_value, default_value FROM mysql.engine_cost;
```

Cột `cost_value` là `NULL` nghĩa là đang dùng giá trị mặc định biên dịch sẵn (cột `default_value`).
Có thể sửa rồi chạy `FLUSH OPTIMIZER_COSTS` để server đọc lại; giá trị mới chỉ áp dụng cho session mở
sau đó, và không được replicate sang replica. Trên thực tế gần như không ai chỉnh các hằng số này;
biết chúng tồn tại để hiểu con số `cost=...` trong `EXPLAIN` từ đâu ra là đủ.

⚠️ Con số `cost` trong `EXPLAIN` là **đơn vị chi phí nội bộ**, không phải mili giây hay số page. Nó
chỉ có ý nghĩa khi so sánh các plan của cùng một câu query trên cùng một server. Đừng so `cost` giữa
hai câu khác nhau để kết luận câu nào nhanh hơn.

### 2.5 Optimizer quyết định những gì

Những quyết định chính, ta sẽ lần lượt thấy trong `EXPLAIN`:

| Quyết định | Ví dụ lựa chọn | Thấy ở đâu trong `EXPLAIN` |
|---|---|---|
| Cách đọc từng bảng (*access method*) | quét bảng, tra PK, tra index, quét một khoảng index, quét cả index | cột `type`, `key` |
| Dùng tới cột nào của composite index | chỉ cột đầu, hay hai cột đầu... | cột `key_len` |
| Thứ tự join | `users` trước hay `orders` trước | thứ tự các dòng |
| Thuật toán join | nested loop, hash join | `Extra`, dạng `TREE` |
| Biến đổi subquery | semijoin, materialization, `EXISTS` | `select_type`, `SHOW WARNINGS` |
| Sort và gom nhóm | dùng thứ tự sẵn của index hay sort thêm, có bảng tạm không | `Extra: Using filesort`, `Using temporary` |

Optimizer lập plan mỗi khi câu lệnh được chạy, dựa trên statistics ở thời điểm đó. Vì vậy cùng một
câu SQL có thể chạy theo plan khác nhau vào hai thời điểm khác nhau nếu statistics đã thay đổi ở giữa;
đây là nguồn gốc của hiện tượng "query đang nhanh bỗng chậm" mà mục 5.6 sẽ phân tích. Với câu join rất
nhiều bảng, bản thân việc tìm thứ tự join cũng tốn đáng kể (mục 12.4 nói về biến
`optimizer_search_depth`).

## 3. EXPLAIN dạng bảng

### 3.1 Cú pháp và tính an toàn

```sql
EXPLAIN SELECT ...;                 -- dạng bảng (TRADITIONAL), mặc định
EXPLAIN FORMAT=TREE SELECT ...;     -- dạng cây (mục 3.8)
EXPLAIN FORMAT=JSON SELECT ...;     -- dạng JSON, chi tiết nhất
EXPLAIN ANALYZE SELECT ...;         -- CHẠY THẬT và đo (mục 4)
```

- `EXPLAIN` dùng được với `SELECT`, `TABLE`, `INSERT`, `REPLACE`, `UPDATE`, `DELETE`. Nó chỉ lập plan,
  **không chạy** câu lệnh, nên `EXPLAIN DELETE ...` không xoá gì.
- `DESCRIBE`/`DESC` là từ đồng nghĩa với `EXPLAIN` (thói quen: `DESC t` để xem cấu trúc bảng,
  `EXPLAIN` để xem plan).
- Định dạng mặc định khi không ghi `FORMAT` do biến `explain_format` quyết định (mặc định
  `TRADITIONAL`).
- `EXPLAIN` cần cùng quyền như khi chạy chính câu lệnh đó.
- Kết thúc bằng `\G` thay cho `;` trong client `mysql` để in mỗi cột một dòng, dễ đọc hơn bảng ngang.

### 3.2 Ví dụ đầu tiên

Query cần tối ưu xuyên suốt chương: 20 đơn `paid` mới nhất của user 42.

```sql
EXPLAIN SELECT id, total, created_at FROM orders
WHERE user_id = 42 AND status = 'paid'
ORDER BY created_at DESC LIMIT 20\G
```

Khi bảng chưa có index phụ (output minh hoạ):

```
           id: 1
  select_type: SIMPLE
        table: orders
   partitions: NULL
         type: ALL
possible_keys: NULL
          key: NULL
      key_len: NULL
          ref: NULL
         rows: 997423
     filtered: 1.00
        Extra: Using where; Using filesort
```

Mỗi dòng output ứng với **một bảng** (hoặc một bảng dẫn xuất) mà plan đọc. Ý nghĩa từng cột:

| Cột | Giá trị ở trên | Nghĩa |
|---|---|---|
| `id` | 1 | Số thứ tự của khối `SELECT` trong câu. Query có subquery hoặc `UNION` có nhiều id. Các dòng cùng id thuộc một join, đọc theo thứ tự từ trên xuống |
| `select_type` | `SIMPLE` | Loại khối: `SIMPLE` (không subquery, không union), `PRIMARY` (khối ngoài cùng), `SUBQUERY`, `DEPENDENT SUBQUERY` (subquery tương quan), `DERIVED` (bảng dẫn xuất trong `FROM`), `MATERIALIZED`, `UNION`, `UNION RESULT` |
| `table` | `orders` | Bảng được đọc; `<derivedN>` là kết quả của khối id N, `<unionM,N>` là kết quả union, `<subqueryN>` là subquery đã materialize |
| `partitions` | NULL | Các partition bị đọc (chỉ có nghĩa với bảng partition, Chương 23) |
| `type` | `ALL` | Cách truy cập bảng (*access type*, tài liệu gọi là *join type*). Cột quan trọng nhất, mục 3.3 |
| `possible_keys` | NULL | Các index optimizer thấy **có thể** dùng. NULL nghĩa là không có index liên quan |
| `key` | NULL | Index **thực sự** được chọn |
| `key_len` | NULL | Số byte của phần index được dùng; suy ra dùng tới cột nào của composite index, mục 3.5 |
| `ref` | NULL | Cái gì đem so với index: `const` là hằng số, `ch12.u.id` là cột của bảng đọc trước, `func` là kết quả một hàm |
| `rows` | 997423 | Số dòng optimizer **ước lượng** phải đọc (examine) ở bước này. Với InnoDB luôn là ước lượng |
| `filtered` | 1.00 | Phần trăm ước lượng của `rows` còn lại sau khi áp các điều kiện còn lại |
| `Extra` | `Using where; Using filesort` | Thông tin thêm, mục 3.6 |

Diễn giải bằng lời: đọc toàn bộ khoảng một triệu dòng (`ALL`), lọc bằng `WHERE` (`Using where`),
ước lượng giữ lại 1%, rồi sort phần còn lại (`Using filesort`) để lấy 20 dòng.

### 3.3 Cột `type`: cách truy cập bảng

Thứ tự từ tốt tới tệ theo tài liệu MySQL:

| `type` | Nghĩa | Ví dụ trên dữ liệu mẫu |
|---|---|---|
| `system` | Bảng chỉ có một dòng; trường hợp đặc biệt của `const` | |
| `const` | So **mọi** cột của PK hoặc unique index với hằng số: tối đa 1 dòng, đọc một lần lúc tối ưu rồi coi như hằng | `WHERE id = 5` |
| `eq_ref` | Trong join, mỗi tổ hợp dòng của các bảng trước khớp đúng 1 dòng qua PK hoặc unique `NOT NULL` | `orders o JOIN users u ON u.id = o.user_id`: dòng của `u` là `eq_ref` |
| `ref` | Tra index bằng `=` (hoặc `<=>`), có thể ra nhiều dòng (index không unique, hoặc chỉ dùng prefix bên trái) | `WHERE user_id = 42` khi có index trên `user_id` |
| `fulltext` | Dùng FULLTEXT index | |
| `ref_or_null` | Như `ref`, thêm một lượt tìm các dòng NULL | `WHERE c = 1 OR c IS NULL` |
| `index_merge` | Dùng vài index rồi hợp/giao kết quả; `key` liệt kê nhiều index | `WHERE a = 1 OR b = 2` với index riêng trên `a` và `b` |
| `unique_subquery`, `index_subquery` | Thay subquery `IN (SELECT ...)` bằng tra index | |
| `range` | Quét một hoặc vài khoảng của index | `BETWEEN`, `>`, `<`, `IN (...)`, `LIKE 'abc%'` |
| `index` | Quét **toàn bộ** cây index từ đầu tới cuối | `SELECT user_id FROM orders` khi có index trên `user_id` |
| `ALL` | Quét toàn bộ bảng (với InnoDB là quét cả clustered index) | Không có index dùng được |

⚠️ Hai cái bẫy khi đọc cột này:

- `type: index` **không** có nghĩa "đã dùng index tốt". Nó là quét hết index, chỉ rẻ hơn `ALL` vì
  index thường nhỏ hơn bảng. Thường đi cùng `Extra: Using index` (chỉ đọc index, không quay về bảng).
- `type: ref` tốt hay xấu tuỳ số dòng khớp. `ref` trên cột `status` khớp 1/3 bảng (333.000 dòng) có
  thể còn chậm hơn `ALL`; thực tế optimizer khi đó sẽ tự chọn `ALL`. Luôn nhìn `type` cùng với `rows`.

### 3.4 `rows` và `filtered`: ước lượng số dòng

`rows` là số dòng ước lượng **phải đọc** ở bước đó, không phải số dòng trả về. `filtered` là phần trăm
ước lượng còn lại sau khi áp các điều kiện chưa được index xử lý. Tích:

```
số dòng chuyển sang bước sau ≈ rows × filtered / 100
```

Ví dụ trên: 997.423 × 1% ≈ 9.974 dòng phải sort. Với join, con số này là **số lần bảng kế tiếp bị tra**,
nên nó quyết định thứ tự join. Tài liệu MySQL cũng gợi ý: nhân các giá trị `rows` của mọi dòng trong
`EXPLAIN` cho ra cỡ số dòng MySQL phải xét cho cả câu join.

⚠️ Vì sao lại là 1%? Hai cột `user_id` và `status` chưa có index hay histogram, nên optimizer **không
biết gì** về phân bố dữ liệu và dùng hệ số đoán cố định. Trong mã nguồn MySQL 8.4 (`sql/item.h`) có các
hằng `COND_FILTER_EQUALITY = 0.1` (điều kiện `=`), `COND_FILTER_INEQUALITY = 0.3333` (`<`, `>`...),
`COND_FILTER_BETWEEN = 0.1111`. Hai điều kiện bằng: 10% × 10% = 1%. Thực tế chỉ có 34 dòng khớp
(0,0034%). Ước lượng lệch hàng trăm lần như vậy là nguồn gốc của nhiều plan tệ trong query nhiều bảng.
Mục 5 nói cách cho optimizer dữ liệu tốt hơn.

### 3.5 Thêm index và đọc `key`, `key_len`, `ref`

Thêm index chỉ trên `user_id`:

```sql
CREATE INDEX idx_user ON orders (user_id);
EXPLAIN SELECT id, total, created_at FROM orders
WHERE user_id = 42 AND status = 'paid'
ORDER BY created_at DESC LIMIT 20\G
```

```
         type: ref
possible_keys: idx_user
          key: idx_user
      key_len: 8
          ref: const
         rows: 100
     filtered: 10.00
        Extra: Using where; Using filesort
```
(output minh hoạ, chỉ in các cột thay đổi)

- `type: ref`, `ref: const`: tra index bằng hằng số 42.
- `rows: 100`: khi điều kiện nằm trên cột có index, optimizer không đoán mà *index dive*: đi xuống cây
  đếm xấp xỉ số entry trong khoảng, nên ra sát con số thật (user 42 có đúng 100 đơn).
- `filtered: 10.00`: `status` vẫn bị đoán 10%, và được lọc sau khi đọc dòng (`Using where`).
- Vẫn `Using filesort`: 100 dòng phải sort theo `created_at`. Nhỏ, nhưng có thể bỏ hẳn.

Thay bằng composite index đúng thứ tự: cột so sánh bằng trước, cột sort sau (quy tắc ở Chương 11):

```sql
DROP INDEX idx_user ON orders;
CREATE INDEX idx_user_status_created ON orders (user_id, status, created_at);
```

```
         type: ref
possible_keys: idx_user_status_created
          key: idx_user_status_created
      key_len: 50
          ref: const,const
         rows: 34
     filtered: 100.00
        Extra: Backward index scan
```
(output minh hoạ)

- `ref: const,const`: hai cột đầu của index được so với hai hằng số (42 và `'paid'`).
- `rows: 34`: đúng số đơn paid của user 42.
- `filtered: 100.00`: không còn điều kiện nào phải lọc thêm.
- Hết `Using filesort`: trong cùng `(user_id, status)`, các entry đã xếp theo `created_at`; chỉ cần đọc
  ngược (`Backward index scan`) và dừng sau 20 entry.
- Không có `Using index` vì `total` không nằm trong index: mỗi entry vẫn phải quay về clustered index
  lấy `total` (20 lần). Thêm `total` vào cuối index sẽ thành covering, nhưng với 20 lần tra thì không đáng.

**Tính `key_len`** để biết index được dùng tới cột nào:

| Kiểu cột | Số byte |
|---|---|
| `INT` / `BIGINT` | 4 / 8 |
| `DATETIME` | 5 (cộng thêm phần lẻ giây nếu khai báo `DATETIME(fsp)`) |
| `CHAR(n)` / `VARCHAR(n)` | n × số byte tối đa mỗi ký tự của charset (`utf8mb4` là 4); `VARCHAR` cộng thêm 2 byte độ dài |
| Cột cho phép NULL | cộng thêm 1 byte |

Ở ví dụ: `user_id BIGINT NOT NULL` = 8; `status VARCHAR(10) NOT NULL` utf8mb4 = 10 × 4 + 2 = 42; tổng
50, tức index dùng tới hết cột thứ hai. Nếu thêm `AND created_at >= '2025-06-01'`, `key_len` thành 55
(thêm 5 byte của `DATETIME`) và `type` thành `range`. Nếu chỉ thấy 8, nghĩa là chỉ cột đầu được dùng để
tra, các cột sau bị bỏ (thiếu điều kiện trên cột giữa, hoặc cột trước là điều kiện khoảng).

`key` đôi khi là một index không có trong `possible_keys`: khi không index nào giúp tìm dòng, nhưng có
một index chứa đủ mọi cột cần đọc, MySQL quét index đó (`type: index`) vì rẻ hơn quét bảng.

### 3.6 Cột `Extra`

Những giá trị hay gặp:

| `Extra` | Nghĩa | Tốt hay xấu |
|---|---|---|
| `Using index` | *Covering index*: mọi cột cần đều có trong index, không quay về bảng | Tốt |
| `Using where` | Có điều kiện được lọc ở tầng server sau khi storage engine trả dòng | Bình thường; đáng lo nếu đi cùng `ALL`/`index` trên bảng lớn |
| `Using index condition` | *Index Condition Pushdown* (ICP): điều kiện trên cột có trong index được kiểm ngay trên entry index, trước khi đọc dòng đầy đủ | Tốt |
| `Using filesort` | Phải sort thêm một bước vì không có index cho sẵn thứ tự. Tên gây hiểu lầm: sort có thể diễn ra hoàn toàn trong RAM | Xấu nếu số dòng sort lớn |
| `Using temporary` | Phải tạo bảng tạm, thường do `GROUP BY`, `DISTINCT`, `UNION`, hoặc `GROUP BY` và `ORDER BY` khác cột | Xấu nếu nhiều dòng |
| `Using join buffer (hash join)` | Join bằng hash join (mục 6) | Trong query OLTP thường là thiếu index trên cột join |
| `Backward index scan` | Đọc index theo chiều ngược | Tốt, tránh được sort |
| `Using MRR` | *Multi-Range Read*: gom các khoá cần đọc rồi sắp lại để đọc bảng gần tuần tự | Tốt |
| `Using index for group-by` | Gom nhóm bằng cách nhảy qua index, mỗi nhóm đọc vài entry | Tốt |
| `Using index for skip scan` | *Skip scan*: dùng được composite index dù thiếu điều kiện cột đầu | Chấp nhận được, đừng thiết kế dựa vào nó |
| `Impossible WHERE` | `WHERE` luôn sai | Thường là bug trong query |
| `Select tables optimized away` | Trả lời được ngay lúc tối ưu, ví dụ `MIN(id)` | Tốt |
| `Not exists` | Tối ưu `LEFT JOIN ... WHERE t2.id IS NULL` hoặc antijoin: gặp một dòng khớp là dừng | Tốt |

Tài liệu MySQL khuyên: muốn query nhanh nhất có thể, hãy để ý `Using filesort` và `Using temporary`.

### 3.7 Nhiều dòng: join và subquery

```sql
EXPLAIN SELECT u.name, o.total
FROM users u JOIN orders o ON o.user_id = u.id
WHERE u.country = 'VN' AND o.status = 'paid'\G
```

Output minh hoạ (rút gọn, đang có `idx_user_status_created`):

```
*************************** 1. row ***************************
           id: 1
  select_type: SIMPLE
        table: u
         type: ALL
          key: NULL
         rows: 9980
     filtered: 10.00
        Extra: Using where
*************************** 2. row ***************************
           id: 1
  select_type: SIMPLE
        table: o
         type: ref
          key: idx_user_status_created
      key_len: 50
          ref: ch12.u.id,const
         rows: 33
     filtered: 100.00
        Extra: NULL
```

Đọc: cùng `id` 1 nên là một join; `u` đọc trước (bảng ngoài), ước lượng 9.980 × 10% ≈ 998 user VN
(thật là 100, vì `country` không có index hay histogram nên bị đoán 10%). Với mỗi user đó, tra `o`
bằng index theo `(u.id, 'paid')` (`ref: ch12.u.id,const`). Đây là nested loop join (mục 6).

Muốn xem câu SQL sau khi optimizer đã viết lại (gộp subquery, đổi `IN` thành semijoin...), chạy
`SHOW WARNINGS` ngay sau `EXPLAIN`. Cột `Message` (code 1003) chứa câu đã viết lại, có thể kèm các
ký hiệu như `<in_optimizer>`, `<exists>`, `<cache>`; câu này không nhất thiết là SQL hợp lệ, chỉ để đọc.

### 3.8 FORMAT=TREE và FORMAT=JSON

`EXPLAIN FORMAT=TREE` in plan dạng cây các *iterator*, gần với cách MySQL 8 thực sự thực thi: mỗi node
kéo dòng từ node con. Tài liệu MySQL ghi `TREE` mô tả cách xử lý chính xác hơn dạng bảng.

```
mysql> EXPLAIN FORMAT=TREE SELECT id, total, created_at FROM orders
    -> WHERE user_id = 42 AND status = 'paid' ORDER BY created_at DESC LIMIT 20\G
EXPLAIN: -> Limit: 20 row(s)  (cost=11.9 rows=20)
    -> Index lookup on orders using idx_user_status_created (user_id=42, status='paid') (reverse)  (cost=11.9 rows=34)
```
(output minh hoạ)

Đọc từ node thụt sâu nhất ra ngoài. `cost` và `rows` là ước lượng. Dạng cây đặc biệt có ích với join
(thấy rõ `Nested loop inner join`, `Inner hash join`, `Hash semijoin`...), subquery và CTE.

`EXPLAIN FORMAT=JSON` chi tiết nhất: có `cost_info` từng phần (`read_cost`, `eval_cost`,
`prefix_cost`), `used_key_parts` (tên các cột index được dùng, rõ hơn tự tính `key_len`),
`attached_condition` (điều kiện lọc). MySQL 8.4 cho phép lưu JSON vào biến:
`EXPLAIN FORMAT=JSON INTO @plan SELECT ...;` rồi `SELECT JSON_EXTRACT(@plan, '$.query_block.table.key');`.

Ngoài ra `EXPLAIN FOR CONNECTION <id>` xem plan của câu đang chạy ở connection khác (lấy id từ
`SHOW PROCESSLIST`), có ích khi một query đang treo trên production.

## 4. EXPLAIN ANALYZE: số đo thật

### 4.1 Là gì

`EXPLAIN` chỉ cho biết optimizer **định** làm gì và **đoán** bao nhiêu dòng. `EXPLAIN ANALYZE` **chạy
query thật**, đo từng iterator trong lúc chạy, rồi in cây plan với số đo thật đặt cạnh số ước lượng.

Theo tài liệu MySQL 8.4:

- Dùng được với `SELECT`, `TABLE`, và `UPDATE`/`DELETE` nhiều bảng.
- Output luôn ở dạng `TREE`; ghi `FORMAT=JSON` hay `FORMAT=TRADITIONAL` sẽ báo lỗi.
- Vì chạy thật, query 10 phút thì `EXPLAIN ANALYZE` cũng 10 phút; dừng bằng `KILL QUERY` hoặc Ctrl-C.
- Thời gian tính bằng mili giây.

### 4.2 Đọc output

Xoá index để thấy plan tệ trước:

```sql
DROP INDEX idx_user_status_created ON orders;
EXPLAIN ANALYZE SELECT id, total, created_at FROM orders
WHERE user_id = 42 AND status = 'paid' ORDER BY created_at DESC LIMIT 20\G
```

```
EXPLAIN: -> Limit: 20 row(s)  (cost=101000 rows=20) (actual time=398..398 rows=20 loops=1)
    -> Sort: orders.created_at DESC, limit input to 20 row(s) per chunk  (cost=101000 rows=9974) (actual time=398..398 rows=20 loops=1)
        -> Filter: ((orders.user_id = 42) and (orders.`status` = 'paid'))  (cost=101000 rows=9974) (actual time=3.1..398 rows=34 loops=1)
            -> Table scan on orders  (cost=101000 rows=997423) (actual time=0.07..352 rows=1e+6 loops=1)
```
(output minh hoạ)

Năm quy tắc đọc:

1. **Đọc từ trong ra ngoài, từ dưới lên.** Node thụt sâu nhất chạy trước, đẩy dòng lên cha. Ở đây:
   quét bảng → lọc → sort → cắt 20 dòng.
2. **Hai cặp ngoặc.** `(cost=... rows=...)` là ước lượng, giống `EXPLAIN`. `(actual time=A..B rows=R
   loops=L)` là số đo thật:
   - `A`: mili giây tới khi node trả dòng **đầu tiên**; `B`: tới khi trả dòng **cuối cùng**.
   - `R`: số dòng node trả lên; `L`: số lần node được chạy.
   - Khi `L > 1`, `A`, `B`, `R` là **trung bình mỗi loop**. Tổng thời gian ≈ `B × L`, tổng dòng = `R × L`.
3. **Thời gian của cha đã gồm thời gian của con.** Node tự tốn bao nhiêu = `B` của nó trừ `B` của con.
   Ở đây `Table scan` tốn khoảng 352 ms, `Filter` thêm khoảng 46 ms, `Sort` và `Limit` gần như không
   tốn. Bước tốn nhất là quét bảng.
4. **So `rows` ước lượng với `rows` thật ở cùng node.** `Filter` ước lượng 9.974, thật 34: lệch gần 300
   lần, đúng như mục 3.4 đã giải thích. Lệch cỡ 10 lần trở lên là dấu hiệu optimizer đang đoán mù.
5. **`A` gần bằng `B`** (ở `Sort`: 398..398) nghĩa là node "chặn": phải nhận hết input mới trả được dòng
   đầu. `Table scan` có `A` rất nhỏ: trả dòng đầu gần như ngay.

Số trong output được in gọn: `1e+6` là một triệu; số không có số 0 thừa ở cuối.

Tạo lại index rồi chạy lại:

```sql
CREATE INDEX idx_user_status_created ON orders (user_id, status, created_at);
```

```
EXPLAIN: -> Limit: 20 row(s)  (cost=11.9 rows=20) (actual time=0.058..0.112 rows=20 loops=1)
    -> Index lookup on orders using idx_user_status_created (user_id=42, status='paid') (reverse)  (cost=11.9 rows=34) (actual time=0.056..0.108 rows=20 loops=1)
```
(output minh hoạ)

Node index lookup chỉ trả 20 dòng dù ước lượng 34: `Limit` ngừng kéo khi đủ 20. Vì không phải sort,
node con dừng sớm được. Đây là sức mạnh của mô hình iterator kéo dòng.

### 4.3 `loops` trong join

```sql
EXPLAIN ANALYZE SELECT u.name, o.total FROM users u
JOIN orders o ON o.user_id = u.id WHERE u.country = 'VN'\G
```

```
EXPLAIN: -> Nested loop inner join  (cost=36000 rows=99800) (actual time=0.35..21.4 rows=10000 loops=1)
    -> Filter: (u.country = 'VN')  (cost=1010 rows=998) (actual time=0.07..2.9 rows=100 loops=1)
        -> Table scan on u  (cost=1010 rows=9980) (actual time=0.06..2.4 rows=10000 loops=1)
    -> Index lookup on o using idx_user_status_created (user_id=u.id)  (cost=25.1 rows=100) (actual time=0.04..0.18 rows=100 loops=100)
```
(output minh hoạ)

- Node `Index lookup on o` chạy 100 lần (một lần cho mỗi user VN), mỗi lần trung bình 0,18 ms và 100
  dòng: tổng khoảng 18 ms và 10.000 dòng. Đọc `0.18` mà quên nhân với `loops` là lỗi đọc plan phổ
  biến nhất.
- `Filter` ước lượng 998, thật 100: cột `country` bị đoán 10%. Ở đây vô hại; với bảng lớn hơn, ước
  lượng sai kiểu này có thể làm optimizer đảo thứ tự join.

### 4.4 Cẩn thận khi dùng

⚠️ `EXPLAIN ANALYZE` với `UPDATE`/`DELETE` nhiều bảng là **thay đổi dữ liệu thật**. Bọc trong
transaction rồi rollback (Chương 13):

```sql
START TRANSACTION;
EXPLAIN ANALYZE DELETE o FROM orders o JOIN users u ON u.id = o.user_id WHERE u.country = 'VN';
ROLLBACK;
```

Trong lúc đó các dòng bị ảnh hưởng vẫn bị khoá tới khi rollback (Chương 15), nên đừng làm trên
production giờ cao điểm. Query nặng thì chạy `EXPLAIN ANALYZE` trên replica hoặc bản sao dữ liệu.

⚠️ Lần chạy đầu có thể chậm hơn các lần sau vì dữ liệu chưa nằm trong buffer pool (Chương 16). Chạy vài
lần và nhìn số ổn định.

Đối chiếu PostgreSQL: `EXPLAIN ANALYZE` cũng in `actual time=A..B rows=R loops=L` với `time` và `rows`
là giá trị mỗi loop. Postgres có thêm `EXPLAIN (ANALYZE, BUFFERS)` cho biết số page đọc từ cache và từ
đĩa (từ PostgreSQL 18, `BUFFERS` tự bật khi có `ANALYZE`).

## 5. Statistics, histogram và ANALYZE TABLE

### 5.1 Optimizer biết gì về dữ liệu

Cost model cần ước lượng "điều kiện này giữ lại bao nhiêu dòng" (*selectivity*). Nguồn thông tin:

1. **Index dive**: với điều kiện trên cột có index, optimizer đi xuống B+tree tới hai đầu khoảng và ước
   lượng số entry ở giữa. Chính xác nhưng tốn công, nên chỉ làm khi số khoảng nhỏ hơn
   `eq_range_index_dive_limit` (mặc định 200). Ví dụ `IN (...)` có từ 200 giá trị trở lên thì chuyển
   sang dùng số trung bình trong thống kê index.
2. **Thống kê index lưu sẵn** (*persistent statistics*): số dòng của bảng, *cardinality* (số giá trị
   khác nhau) của từng index, lưu trong `mysql.innodb_table_stats` và `mysql.innodb_index_stats`.
3. **Histogram** cho cột (mục 5.4).
4. Không có gì: hệ số đoán cố định (mục 3.4).

### 5.2 InnoDB tính thống kê thế nào

- `innodb_stats_persistent` (mặc định ON): thống kê được lưu xuống đĩa, giữ qua restart.
- Thống kê được tính bằng cách **lấy mẫu** một số page của index, không đọc hết:
  `innodb_stats_persistent_sample_pages` mặc định 20. Nhanh nhưng không chính xác 100%.
- `innodb_stats_auto_recalc` (mặc định ON): tự tính lại khi hơn 10% số dòng của bảng thay đổi. Việc
  tính lại chạy nền, nên có độ trễ sau một đợt ghi lớn.
- Khi thêm index mới, thống kê của index đó được tính ngay.
- Có thể đặt riêng cho từng bảng: `ALTER TABLE orders STATS_SAMPLE_PAGES = 100;` (mẫu lớn hơn, chính xác
  hơn, `ANALYZE TABLE` chậm hơn).

Xem thống kê:

```sql
SHOW INDEX FROM orders;            -- cột Cardinality: số giá trị khác nhau ước lượng
SELECT TABLE_ROWS FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'ch12' AND TABLE_NAME = 'orders';   -- số dòng ước lượng
```

Với dữ liệu mẫu, `Cardinality` của cột `user_id` trong `idx_user_status_created` sẽ xấp xỉ 10.000,
của cặp `(user_id, status)` xấp xỉ 30.000. Đây là ước lượng; con số trên máy bạn có thể lệch.

### 5.3 ANALYZE TABLE

```sql
ANALYZE TABLE orders;
```

Tính lại ngay thống kê index của bảng (theo mẫu như trên). Chạy sau khi import, xoá hoặc cập nhật một
lượng lớn dữ liệu, hoặc khi nghi plan sai do thống kê cũ. Với InnoDB lệnh này nhanh vì chỉ lấy mẫu.

### 5.4 Histogram

Index dive chỉ có với cột có index. Cột không có index (ví dụ `country`, hoặc `status` khi đứng một
mình) thì optimizer đoán 10%. *Histogram* mô tả phân bố giá trị của một cột, để optimizer ước lượng
`filtered` bằng dữ liệu thật.

```sql
ANALYZE TABLE users UPDATE HISTOGRAM ON country WITH 16 BUCKETS;
EXPLAIN SELECT * FROM users WHERE country = 'VN';      -- filtered giờ ≈ 1.00 thay vì 10.00
SELECT HISTOGRAM FROM information_schema.COLUMN_STATISTICS
WHERE SCHEMA_NAME = 'ch12' AND TABLE_NAME = 'users' AND COLUMN_NAME = 'country';
ANALYZE TABLE users DROP HISTOGRAM ON country;          -- xoá khi không cần
```

Các điểm cần nhớ (theo tài liệu MySQL 8.4):

- Hai loại: *singleton* (mỗi bucket một giá trị, dùng khi số giá trị khác nhau không vượt số bucket) và
  *equi-height* (mỗi bucket một khoảng giá trị). Cột `country` có 2 giá trị nên ra singleton.
- Số bucket mặc định 100 khi bỏ `WITH N BUCKETS`, từ 1 tới 1024.
- Mặc định `MANUAL UPDATE`: histogram **không** tự cập nhật khi dữ liệu đổi. MySQL 8.4 có
  `... WITH N BUCKETS AUTO UPDATE` để histogram được cập nhật theo các lần tính lại thống kê tự động.
- Tài liệu ghi histogram "useful primarily for nonindexed columns"; khi range optimizer dùng được
  (cột có index) thì optimizer dùng ước lượng của nó và không dùng histogram.
- Histogram rẻ hơn index: không phải cập nhật mỗi lần `INSERT`/`UPDATE`. Hợp với cột dữ liệu lệch mà
  bạn không muốn đánh index, ví dụ `status` 99% `done`, 1% `pending`.

### 5.5 Join order và ước lượng

Quay lại câu join ở mục 3.7. Sau khi có histogram trên `country`, optimizer biết chỉ 100 user VN thay
vì đoán 998. Ở bài này plan không đổi, nhưng nguyên lý là: với join, ước lượng số dòng của bảng ngoài
quyết định chọn bảng nào làm bảng ngoài và dùng thuật toán join nào. Ước lượng sai lệch hàng chục lần
là lý do hay gặp nhất của plan join tệ.

### 5.6 Sự cố kinh điển: query đang nhanh bỗng chậm

Query chạy 20 ms bỗng thành 8 giây, code và index không đổi. Nguyên nhân hay gặp:

1. Sau một đợt import hoặc xoá lớn, thống kê được tính lại (hoặc chưa kịp tính lại), optimizer đổi
   plan: chọn index khác, đảo thứ tự join.
2. Dữ liệu vượt ngưỡng khiến so sánh chi phí đảo chiều, ví dụ một user "cá voi" có hàng triệu đơn.
3. Mẫu 20 page không đại diện cho dữ liệu lệch.

Cách xử lý theo thứ tự: `EXPLAIN` lại để xác nhận plan đã đổi → `ANALYZE TABLE` → nếu vẫn sai, thêm
histogram hoặc tăng `STATS_SAMPLE_PAGES` cho bảng đó → cuối cùng mới dùng hint (mục 12).

## 6. Thuật toán join

### 6.1 Nested loop join

Với mỗi dòng của bảng ngoài (*outer*), tìm các dòng khớp trong bảng trong (*inner*):

```
for each u in users where country = 'VN':              -- 100 dòng
    for each o in index idx_user_status_created(user_id = u.id):   -- tra B+tree
        emit (u, o)
```

Chi phí xấp xỉ `số dòng ngoài × chi phí một lần tra bảng trong`. Rất nhanh khi bảng ngoài ít dòng và
bảng trong có index trên cột join (`type` của bảng trong là `ref` hoặc `eq_ref`). Không có index thì
mỗi vòng ngoài phải quét cả bảng trong: `m × n` dòng. Với 3 bảng thì lồng 3 vòng, theo đúng thứ tự
các dòng trong `EXPLAIN`.

### 6.2 Hash join

Có từ MySQL 8.0.18; từ 8.0.20 thay hẳn thuật toán *block nested loop* cũ. Hai pha:

1. *Build*: đọc một bảng (thường bảng nhỏ hơn), dựng hash table trong bộ nhớ, key là cột join.
2. *Probe*: đọc bảng kia, với mỗi dòng tính hash của cột join và dò trong hash table.

```
build:  users (VN) ──► hash table { user_id → dòng user }
probe:  quét orders, mỗi dòng: hash(o.user_id) có trong bảng? → emit
```

Chi phí xấp xỉ `m + n`, tốt hơn hẳn `m × n` khi không có index. Bộ nhớ giới hạn bởi `join_buffer_size`;
vượt thì tràn xuống file tạm trên đĩa. Tài liệu MySQL 8.4 ghi: mặc định MySQL dùng hash join "whenever
possible" khi không có index áp dụng được cho điều kiện join; nó dùng được cho inner join, outer join,
semijoin, antijoin, cả điều kiện không phải dấu bằng và tích Descartes.

Thử bằng cách giả lập thiếu index với `IGNORE INDEX`:

```sql
EXPLAIN FORMAT=TREE SELECT COUNT(*) FROM users u
JOIN orders o IGNORE INDEX (idx_user_status_created) ON o.user_id = u.id
WHERE u.country = 'VN'\G
```

```
EXPLAIN: -> Aggregate: count(0)  (cost=...)
    -> Inner hash join (o.user_id = u.id)  (cost=... rows=...)
        -> Table scan on o  (cost=... rows=997423)
        -> Hash
            -> Filter: (u.country = 'VN')  (cost=1010 rows=998)
                -> Table scan on u  (cost=1010 rows=9980)
```
(output minh hoạ)

Nhánh dưới `Hash` là phía build (user VN), nhánh còn lại là phía probe. Ở dạng bảng, dấu hiệu là
`Extra: Using join buffer (hash join)` ở dòng của bảng probe. Bật/tắt bằng hint `BNL(...)`/`NO_BNL(...)`
hoặc cờ `block_nested_loop` trong `optimizer_switch` (tên cũ được giữ lại).

⚠️ Thấy hash join trên bảng lớn trong query OLTP (phục vụ request người dùng) thường là dấu hiệu
**thiếu index trên cột join**, không phải "MySQL đã tối ưu giùm". Hash join hợp với báo cáo quét nhiều
dòng; request web cần nested loop trên index.

### 6.3 So sánh

| Thuật toán | MySQL 8.4 | PostgreSQL | Hợp khi |
|---|---|---|---|
| Nested loop | Có | Có | Bảng ngoài ít dòng, bảng trong có index trên cột join |
| Hash join | Có (từ 8.0.18) | Có | Không có index dùng được, hai phía lớn |
| Merge join | Không | Có | Hai phía đã sắp theo cột join, tập lớn |

## 7. Tìm query chậm trên server thật

Trên production bạn không biết trước câu nào chậm. Ba công cụ có sẵn trong MySQL và một công cụ ngoài.

### 7.1 Slow query log

Ghi các câu lệnh chạy lâu hơn `long_query_time` giây (và đã đọc ít nhất `min_examined_row_limit` dòng).

```sql
SET GLOBAL slow_query_log = ON;            -- mặc định tắt
SET GLOBAL long_query_time = 0.2;          -- mặc định 10 giây, quá cao cho web; nhận tới micro giây
SET GLOBAL log_slow_extra = ON;            -- thêm trường chi tiết vào log dạng file
SHOW VARIABLES LIKE 'slow_query_log_file'; -- file log nằm ở đâu
```

⚠️ `SET GLOBAL long_query_time` chỉ áp dụng cho các connection mở **sau** lệnh này (connection cũ giữ
giá trị session của nó). Muốn giữ qua restart thì ghi vào file cấu hình hoặc dùng `SET PERSIST`.

Một entry (output minh hoạ):

```
# Time: 2026-10-01T03:12:45.123456Z
# User@Host: app[app] @ 10.0.0.5 []  Id: 1234
# Query_time: 0.398112  Lock_time: 0.000004 Rows_sent: 20  Rows_examined: 1000000
SET timestamp=1790824365;
SELECT id, total, created_at FROM orders WHERE user_id = 42 AND status = 'paid' ORDER BY created_at DESC LIMIT 20;
```

`Rows_examined` lớn gấp nhiều lần `Rows_sent` là dấu hiệu kinh điển của thiếu index. Thời gian chờ lấy
lock ban đầu không tính vào thời gian thực thi khi so với `long_query_time`.
`log_queries_not_using_indexes` ghi cả câu không dùng index dù nhanh (dễ làm log phình to).

### 7.2 performance_schema: thống kê theo digest

MySQL chuẩn hoá mỗi câu lệnh thành *digest* (thay hằng số bằng `?`, ví dụ `... WHERE user_id = ?`) và
cộng dồn số liệu cho từng digest, không cần bật slow log:

```sql
SELECT DIGEST_TEXT,
       COUNT_STAR                       AS calls,
       ROUND(SUM_TIMER_WAIT / 1e12, 1)  AS total_s,   -- timer tính bằng picosecond
       ROUND(AVG_TIMER_WAIT / 1e9, 2)   AS avg_ms,
       SUM_ROWS_EXAMINED, SUM_ROWS_SENT, SUM_NO_INDEX_USED
FROM performance_schema.events_statements_summary_by_digest
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 10;
```

Số liệu cộng dồn từ lúc server khởi động (hoặc từ lần `TRUNCATE` bảng này gần nhất).

### 7.3 Schema sys

Schema `sys` là tập view dễ đọc dựng trên `performance_schema`:

```sql
SELECT * FROM sys.statement_analysis LIMIT 10;               -- câu tốn nhiều thời gian nhất
SELECT * FROM sys.statements_with_full_table_scans LIMIT 10;  -- câu quét bảng
SELECT * FROM sys.statements_with_sorting LIMIT 10;          -- câu có sort
SELECT * FROM sys.processlist;                               -- đang chạy gì, như SHOW PROCESSLIST
```

### 7.4 pt-query-digest

`pt-query-digest` thuộc Percona Toolkit (công cụ ngoài, cài riêng). Nó đọc slow log, gom câu theo
*fingerprint* (bỏ giá trị cụ thể, gộp danh sách `IN`) và xếp hạng:

```sh
# Chạy trên máy chủ database (hoặc máy có bản copy file slow log)
pt-query-digest --limit 10 /var/lib/mysql/host-slow.log
```

```
# Rank Query ID           Response time   Calls  R/Call V/M   Item
# ==== ================== =============== ====== ====== ===== ==============
#    1 0x3A99CC42AEDCCFCD 1824.3200 61.2%  36480 0.0500  0.01 SELECT orders
#    2 0x8F2B0E1D77A1B6C4  412.9000 13.8%     83 4.9747  1.20 SELECT users orders
```
(output minh hoạ)

`Response time` là tổng thời gian và tỉ lệ trên toàn bộ; `R/Call` là trung bình mỗi lần; `V/M`
(variance-to-mean) cao nghĩa là thời gian dao động mạnh giữa các lần (gợi ý lock hoặc dữ liệu lệch).
Phần chi tiết từng câu có percentile 95%, số dòng examine, và một câu mẫu để đem đi `EXPLAIN`.

### 7.5 SHOW PROCESSLIST

Ảnh chụp tức thời: đang có câu nào chạy, bao lâu, trạng thái gì (`executing`,
`Waiting for table metadata lock`...). Dùng khi "DB đang chậm ngay lúc này". Câu treo quá lâu có thể
dừng bằng `KILL QUERY <id>`.

## 8. Quy trình tối ưu một query chậm

### 8.1 Năm bước

1. **Tìm** câu chậm: slow log, `performance_schema`/`sys`, APM của ứng dụng (cho biết câu đến từ
   endpoint nào).
2. **Xếp hạng theo tổng tải = tần suất × thời gian**. Một câu 50 ms chạy 10.000 lần mỗi phút tốn 500
   giây DB mỗi phút; một câu 5 giây chạy mỗi giờ một lần tốn chưa tới 0,1 giây mỗi phút. Sửa câu đầu trước.
3. **Phân tích**: `EXPLAIN`, rồi `EXPLAIN ANALYZE` (trên replica hoặc bản sao nếu câu nặng). Tìm node
   tốn thời gian nhất và chỗ ước lượng lệch thật.
4. **Sửa**, theo thứ tự chi phí tăng dần:
   - thêm hoặc đổi index (composite đúng thứ tự, covering);
   - viết lại query: bỏ hàm bọc quanh cột trong `WHERE`, tránh so sánh khác kiểu, đổi `OFFSET` sang
     keyset, tách `OR` thành `UNION ALL` khi cần;
   - chỉ lấy cột cần (bỏ `SELECT *`);
   - cập nhật thống kê (`ANALYZE TABLE`, histogram);
   - cache ở tầng ứng dụng; đổi thiết kế (bảng tổng hợp, denormalize);
   - hint, khi mọi cách trên không được.
5. **Đo lại** bằng đúng công cụ ở bước 1, theo dõi vài ngày; kiểm tra index mới không làm chậm ghi.

### 8.2 Khi nguyên nhân không nằm trong câu query

Nhiều câu khác nhau cùng chậm một lúc thì hãy nghĩ tới tài nguyên dùng chung:

| Triệu chứng | Nguyên nhân có thể | Kiểm tra |
|---|---|---|
| Câu tra PK đơn giản cũng chậm, thời gian chờ cao | Lock wait: một transaction dài giữ lock (Chương 15) | `SELECT * FROM sys.innodb_lock_waits;`, `information_schema.INNODB_TRX` |
| App báo "Too many connections" | Connection cạn | `SHOW STATUS LIKE 'Threads_%';` so với `max_connections` |
| Chậm đều, disk I/O cao | Dữ liệu nóng không vừa buffer pool (Chương 16) | `Innodb_buffer_pool_reads` so với `Innodb_buffer_pool_read_requests` |
| Chậm theo giờ cố định | Cron, backup, batch job | Đối chiếu lịch job |

### 8.3 Các mẫu query làm hỏng index

Đã học ở Chương 11, nhắc lại ở dạng "dấu hiệu trong EXPLAIN":

| Viết | Vấn đề | Viết lại |
|---|---|---|
| `WHERE DATE(created_at) = '2025-06-01'` | Hàm bọc cột: không seek được, `type: ALL`/`index` | `WHERE created_at >= '2025-06-01' AND created_at < '2025-06-02'` |
| `WHERE phone = 912345678` khi `phone` là `VARCHAR` | So chuỗi với số: MySQL chuyển từng dòng sang số, không dùng index | `WHERE phone = '912345678'` |
| `WHERE name LIKE '%an'` | Wildcard ở đầu: không có khoảng để seek | FULLTEXT, hoặc lưu thêm cột đảo ngược |
| `WHERE a = 1 OR b = 2` | Có thể thành `ALL` nếu không index merge được | `UNION ALL` hai câu (cẩn thận trùng dòng) |
| `ORDER BY RAND() LIMIT 1` | Sort toàn bảng | Chọn id ngẫu nhiên ở ứng dụng |

## 9. Phân trang: OFFSET và keyset

### 9.1 Vì sao OFFSET sâu thì chậm

`LIMIT 20 OFFSET 100000` nghĩa là "sắp xếp, bỏ 100.000 dòng đầu, lấy 20 dòng". Không có cách nào nhảy
thẳng tới dòng thứ 100.001: MySQL phải đọc (và thường quay về bảng lấy dòng đầy đủ) cả 100.020 dòng rồi
vứt 100.000. Trang càng sâu càng chậm, tăng tuyến tính theo offset.

```sql
CREATE INDEX idx_created ON orders (created_at, id);
EXPLAIN ANALYZE SELECT id, total, created_at FROM orders
ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 500000\G
```

```
-> Limit/Offset: 20/500000 row(s)  (...) (actual time=... rows=20 loops=1)
    -> Index scan on orders using idx_created (reverse)  (...) (actual time=... rows=500020 loops=1)
```
(output minh hoạ, rút gọn)

Node index scan trả 500.020 dòng để `Limit/Offset` giữ lại 20. Tuỳ dữ liệu, optimizer còn có thể
chọn quét bảng rồi sort, vì 500.020 lần quay về bảng quá đắt.

Offset còn có vấn đề về **tính đúng**: nó chỉ biết bỏ bao nhiêu dòng, không biết bỏ dòng nào. Có đơn
mới chèn vào giữa lúc người dùng xem trang 1 và trang 2 thì mọi dòng bị đẩy xuống, dòng cuối trang 1
hiện lại ở đầu trang 2. Xoá dòng thì ngược lại: có dòng bị bỏ sót.

### 9.2 Keyset pagination

*Keyset pagination* (còn gọi *seek method*, *cursor pagination*) nhớ giá trị sort của dòng cuối trang
trước và dùng nó làm điều kiện `WHERE`. Index `(created_at, id)` cho phép đi thẳng xuống cây tới vị trí
đó rồi đọc đúng 20 entry, trang nào cũng rẻ như trang đầu:

```sql
-- Trang đầu
SELECT id, total, created_at FROM orders
ORDER BY created_at DESC, id DESC LIMIT 20;

-- Trang sau: dòng cuối trang trước có created_at = '2025-11-02 10:00:00', id = 879600
SELECT id, total, created_at FROM orders
WHERE created_at < '2025-11-02 10:00:00'
   OR (created_at = '2025-11-02 10:00:00' AND id < 879600)
ORDER BY created_at DESC, id DESC LIMIT 20;
```

Các điểm then chốt:

- **Thứ tự sort phải tất định**: mỗi dòng một vị trí duy nhất. Dữ liệu mẫu cố ý cho cứ 2 đơn chung một
  `created_at`; chỉ sort theo `created_at` thì ở ranh giới trang sẽ lặp hoặc sót dòng. Thêm cột unique
  (`id`) làm *tie-breaker*, đưa nó vào cả `ORDER BY`, `WHERE` và index.
- Chuẩn SQL cho viết gọn bằng *row constructor*: `WHERE (created_at, id) < (?, ?)`. PostgreSQL dùng
  index tốt với dạng này. ⚠️ Với MySQL, tài liệu (Row Constructor Expression Optimization) cho ví dụ
  optimizer dùng ít cột index hơn khi viết bằng row constructor và khuyên viết lại dạng `AND`/`OR`.
  Viết như trên là cách chắc ăn; luôn `EXPLAIN` để thấy `type: range` và `key_len` đủ hai cột.
- Giữ cùng chiều sort cho các cột; trộn `DESC` và `ASC` làm điều kiện phức tạp hơn.
- Đi lùi (trang trước) phải đảo cả dấu so sánh lẫn chiều sort, rồi đảo lại kết quả ở ứng dụng.

| | Offset | Keyset |
|---|---|---|
| Tốc độ trang sâu | Chậm dần theo offset | Như nhau mọi trang |
| Nhảy tới trang N | Được | Không |
| Hiện "trang 3/250" | Được (kèm `COUNT(*)`, cũng tốn) | Không tự nhiên |
| Dữ liệu thay đổi giữa hai lần tải | Lặp hoặc sót dòng | Ổn định |
| Hợp với | Admin, bảng nhỏ, cần số trang | Infinite scroll, API, feed, export |

Laravel có sẵn cả hai: `paginate()` (offset kèm `COUNT(*)`), `simplePaginate()` (offset, không đếm),
`cursorPaginate()` (keyset, mã hoá giá trị cột sort thành chuỗi cursor; cần `ORDER BY` có cột unique).

Một cách cứu offset khi bắt buộc phải nhảy trang là *deferred join*: lấy id trên index covering trước,
rồi mới join về bảng lấy dòng đầy đủ cho đúng 20 id:

```sql
SELECT o.id, o.total, o.created_at
FROM orders o
JOIN (SELECT id FROM orders ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 500000) AS page
  ON page.id = o.id
ORDER BY o.created_at DESC, o.id DESC;
```

Subquery chỉ đọc index `(created_at, id)` (covering, vì `id` là PK nằm sẵn trong secondary index),
không quay về bảng 500.020 lần. Vẫn phải duyệt 500.020 entry, nên chỉ đỡ chứ không giải quyết tận gốc.

## 10. COUNT(*) trên bảng lớn

InnoDB **không lưu sẵn** số dòng của bảng, vì với MVCC (Chương 14) mỗi transaction có thể thấy số dòng
khác nhau ở cùng một thời điểm. Theo tài liệu MySQL, InnoDB xử lý `SELECT COUNT(*)` bằng cách duyệt
secondary index **nhỏ nhất** hiện có (không có secondary index thì quét clustered index). Nhanh hơn
quét bảng nhưng vẫn tỉ lệ với số dòng: bảng 100 triệu dòng thì đếm mất nhiều giây.

- `COUNT(*)` và `COUNT(1)` được InnoDB xử lý như nhau. `COUNT(col)` khác nghĩa: bỏ qua NULL (Chương 08).
- `COUNT(*)` có `WHERE` trên cột có index chỉ đếm trong khoảng đó: `SELECT COUNT(*) FROM orders WHERE
  user_id = 42` rất rẻ khi có index bắt đầu bằng `user_id`.

Khi cần số dòng của cả bảng lớn:

| Cách | Ưu | Nhược |
|---|---|---|
| `TABLE_ROWS` trong `information_schema.TABLES`, hoặc `rows` của `EXPLAIN SELECT * FROM t` | Tức thì | Ước lượng, có thể lệch rất nhiều (tài liệu ghi tới 40–50%) |
| Bảng counter riêng, cập nhật trong cùng transaction với insert/delete | Chính xác, đọc rẻ | Dòng counter thành điểm nóng tranh lock (Chương 15); có thể chia thành N dòng rồi cộng |
| Đổi giao diện: "hơn 10.000 kết quả" | Rẻ | Không ra số chính xác |
| Cache ở ứng dụng, tính lại định kỳ | Rẻ | Cũ vài phút |

Đếm có giới hạn trên cho kiểu "hơn 10.000":

```sql
SELECT COUNT(*) FROM (SELECT 1 FROM orders WHERE status = 'pending' LIMIT 10001) AS x;
-- trả 10001 nghĩa là "hơn 10.000"; dừng đọc sau 10.001 dòng khớp
```

## 11. Update và delete hàng triệu dòng theo batch

### 11.1 Vì sao không chạy một câu

`DELETE FROM orders WHERE created_at < '2025-03-01'` xoá khoảng 170.000 dòng (trên bảng thật có thể là
hàng chục triệu) trong **một transaction**:

- Khoá mọi dòng (và khoảng trống giữa chúng) suốt thời gian chạy, chặn các ghi khác (Chương 15).
- Undo log phình to; nếu bị kill giữa chừng, rollback có thể lâu ngang lúc chạy (Chương 16).
- Binlog ghi một transaction khổng lồ, replica áp lại đúng khối đó một lượt và bị trễ (Chương 22).

### 11.2 Chia batch theo khoá chính

Mỗi batch một transaction nhỏ, đi theo PK, nghỉ giữa các batch:

```php
<?php
declare(strict_types=1);

// Chạy: php purge.php  (cần MySQL và extension pdo_mysql; sửa DSN cho đúng máy bạn)
$pdo = new PDO('mysql:host=127.0.0.1;dbname=ch12', 'root', 'root', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);

$cutoff    = '2025-03-01';
$batchSize = 5000;
$lastId    = 0;

$select = $pdo->prepare(
    'SELECT id FROM orders WHERE id > ? AND created_at < ? ORDER BY id LIMIT ' . $batchSize
);
$delete = $pdo->prepare('DELETE FROM orders WHERE id BETWEEN ? AND ? AND created_at < ?');

while (true) {
    $select->execute([$lastId, $cutoff]);
    /** @var list<int> $ids */
    $ids = array_map('intval', $select->fetchAll(PDO::FETCH_COLUMN));
    if ($ids === []) {
        break;
    }
    $from = $ids[0];
    $to   = $ids[count($ids) - 1];
    $delete->execute([$from, $to, $cutoff]);   // autocommit: mỗi batch là một transaction
    $lastId = $to;
    echo "Đã xoá tới id {$to}: {$delete->rowCount()} dòng\n";
    usleep(100_000);                           // nghỉ 100 ms cho replica và các query khác
}
```

Vì sao đi theo PK (`id > lastId`) thay vì lặp `DELETE ... LIMIT 5000`: mỗi vòng đi thẳng tới chỗ đã xoá
tới, không phải quét lại các vùng đầu bảng (giống lý do keyset nhanh hơn offset). Điều kiện
`created_at < ?` được lặp lại trong `DELETE` để không xoá nhầm dòng bị sửa giữa hai câu.

- Kích thước batch: đo thời gian mỗi batch và giữ ở mức dưới vài trăm mili giây; vài nghìn dòng là điểm
  khởi đầu hay dùng.
- Câu `SELECT` tìm id ở đây quét theo PK và lọc `created_at`. Bảng này `created_at` tăng theo `id` nên
  nhanh; với bảng mà điều kiện không tương quan với PK, nên có index trên cột điều kiện.
- `UPDATE` hàng loạt làm y hệt, thay câu `DELETE` bằng `UPDATE ... WHERE id BETWEEN ? AND ?`.
- Dọn dữ liệu cũ định kỳ trên bảng rất lớn: partition theo thời gian rồi `DROP PARTITION` rẻ hơn nhiều
  (Chương 23).

## 12. Điều khiển optimizer: index hint, optimizer hint, optimizer_switch

Khi optimizer chọn sai mà thống kê, histogram và viết lại query đều không giúp được, MySQL cho phép bạn
"chỉ đường". Đây là giải pháp cuối cùng, vì nó khoá cứng plan: dữ liệu thay đổi thì hint có thể từ
đúng thành sai, và không ai nhớ để gỡ.

### 12.1 Index hint: USE, FORCE, IGNORE INDEX

Đặt ngay sau tên bảng:

```sql
SELECT ... FROM orders USE INDEX (idx_created) WHERE ...;     -- chỉ được chọn trong các index này
SELECT ... FROM orders FORCE INDEX (idx_created) WHERE ...;   -- như USE, và coi quét bảng là rất đắt
SELECT ... FROM orders IGNORE INDEX (idx_user_status_created) WHERE ...;   -- không dùng index này
```

- `FORCE INDEX` không "ép bằng mọi giá": nếu index không dùng được cho câu đó (ví dụ cột bị bọc trong
  hàm), MySQL vẫn quét bảng.
- Có thể giới hạn phạm vi: `FORCE INDEX FOR ORDER BY (idx_created)`, `FOR JOIN`, `FOR GROUP BY`.
- ⚠️ Hint gắn với **tên** index. Đổi tên hoặc xoá index thì câu có hint báo lỗi.
- Tài liệu MySQL 8.4 ghi: các optimizer hint `INDEX`, `JOIN_INDEX`, `GROUP_INDEX`, `ORDER_INDEX` (và
  `NO_INDEX`...) tương đương và được dự định thay thế `FORCE INDEX`/`IGNORE INDEX`; `USE INDEX`,
  `FORCE INDEX`, `IGNORE INDEX` dự kiến sẽ bị deprecate ở bản tương lai. Code mới nên dùng optimizer hint.

### 12.2 Optimizer hint

Viết trong comment đặc biệt `/*+ ... */` ngay sau từ khoá `SELECT`, `UPDATE`, `DELETE`...:

```sql
SELECT /*+ INDEX(o idx_created) */ id, total FROM orders o ORDER BY created_at DESC LIMIT 20;
SELECT /*+ NO_INDEX(o idx_user_status_created) */ COUNT(*) FROM orders o WHERE user_id = 42;
SELECT /*+ JOIN_ORDER(u, o) */ u.name, o.total
FROM users u JOIN orders o ON o.user_id = u.id WHERE u.country = 'VN';
SELECT /*+ NO_BNL(o) */ ...;                              -- không dùng hash join cho bảng o
SELECT /*+ MAX_EXECUTION_TIME(1000) */ ...;               -- huỷ câu SELECT nếu chạy quá 1000 ms
SELECT /*+ SET_VAR(optimizer_switch = 'index_merge=off') */ ...;   -- đổi biến chỉ cho câu này
```

Một số hint hay dùng:

| Hint | Tác dụng |
|---|---|
| `INDEX`, `NO_INDEX` | Dùng / không dùng index chỉ định |
| `JOIN_ORDER`, `JOIN_PREFIX`, `JOIN_SUFFIX`, `JOIN_FIXED_ORDER` | Ràng buộc thứ tự join |
| `BNL`, `NO_BNL` | Bật / tắt hash join |
| `INDEX_MERGE`, `NO_INDEX_MERGE`, `SKIP_SCAN`, `NO_SKIP_SCAN` | Điều khiển các access method đặc biệt |
| `NO_RANGE_OPTIMIZATION` | Không dùng range access cho index chỉ định |
| `MAX_EXECUTION_TIME(N)` | Timeout N mili giây, chỉ cho `SELECT` |
| `SET_VAR(var = value)` | Đặt biến hệ thống chỉ trong câu này |

Ưu điểm so với index hint: phạm vi rõ ràng (từng bảng, từng khối query), và hint sai cú pháp hoặc tham
chiếu sai chỉ sinh warning thay vì lỗi (xem bằng `SHOW WARNINGS`). Mặt trái: gõ sai tên thì hint lặng lẽ
không có tác dụng, nên luôn `EXPLAIN` để xác nhận.

### 12.3 optimizer_switch

Biến `optimizer_switch` là tập cờ bật/tắt từng kỹ thuật tối ưu (`index_merge`, `index_condition_pushdown`,
`mrr`, `block_nested_loop`, `semijoin`, `skip_scan`, `use_invisible_indexes`...):

```sql
SELECT @@optimizer_switch\G
SET SESSION optimizer_switch = 'index_condition_pushdown=off';   -- chỉ session này, để thử nghiệm
```

Dùng để thử nghiệm và chẩn đoán ("plan có đổi không nếu tắt X?"). Đổi ở mức `GLOBAL` trên production
ảnh hưởng mọi câu, rất hiếm khi đáng.

### 12.4 Biến điều khiển việc tìm plan

- `optimizer_search_depth`: optimizer nhìn trước bao nhiêu bảng khi tìm thứ tự join. Giá trị nhỏ giảm
  mạnh thời gian lập plan cho câu join rất nhiều bảng, đổi lại có thể bỏ sót plan tốt; 0 nghĩa là để
  server tự chọn.
- `optimizer_prune_level` (mặc định 1): bỏ sớm các plan dở dựa trên ước lượng số dòng.

Câu join dưới khoảng 7 bảng thì hầu như không cần quan tâm hai biến này.

### 12.5 Trước khi viết hint

Tự hỏi theo thứ tự:

1. Thống kê có cũ không? Thử `ANALYZE TABLE`.
2. Cột lọc có dữ liệu lệch mà không có index? Thử histogram.
3. Index có đúng thứ tự cột không? Có thể làm covering không?
4. Viết lại query có giúp optimizer không?
5. Chỉ khi cả bốn câu là "không": dùng hint, kèm comment trong code giải thích lý do và ngày, và đưa
   câu đó vào danh sách kiểm tra lại định kỳ.

## 13. Đối chiếu PostgreSQL

| Chủ đề | MySQL 8.4 | PostgreSQL |
|---|---|---|
| Xem plan | `EXPLAIN`, `FORMAT=TREE/JSON` | `EXPLAIN`, `FORMAT TEXT/JSON/YAML/XML` |
| Chạy thật và đo | `EXPLAIN ANALYZE` (luôn dạng tree) | `EXPLAIN (ANALYZE, BUFFERS)`; PG 18 tự bật `BUFFERS` khi có `ANALYZE` |
| Thuật toán join | Nested loop, hash join | Nested loop, hash join, merge join |
| Thống kê | `ANALYZE TABLE`, thống kê index lấy mẫu, histogram tạo thủ công | `ANALYZE` (autovacuum tự chạy), thống kê theo cột tự động, `CREATE STATISTICS` cho cột tương quan |
| Hint | Có sẵn (index hint, optimizer hint) | Không có hint trong bản chuẩn (cần extension như `pg_hint_plan`); điều khiển gián tiếp qua `enable_*` |
| Thống kê câu lệnh | `performance_schema`, `sys` | extension `pg_stat_statements` |
| Slow log | `slow_query_log`, `long_query_time` | `log_min_duration_statement`, extension `auto_explain` |

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| `EXPLAIN` trên máy dev vài trăm dòng rồi kết luận | Plan phụ thuộc kích thước và phân bố dữ liệu | Thử trên dữ liệu cỡ production (bản sao, dữ liệu sinh) |
| Thấy `possible_keys` có index là yên tâm | `key` mới là index được chọn; có thể là NULL | Đọc `key`, `type`, `rows` |
| Coi `type: index` là tốt | Là quét hết index | Tìm cách thành `ref`/`range` |
| Đọc `rows` như số dòng trả về | Là số dòng ước lượng phải đọc | Nhân `rows × filtered`, so với `EXPLAIN ANALYZE` |
| Quên nhân `loops` trong `EXPLAIN ANALYZE` | `time`, `rows` là trung bình mỗi loop | Tổng = giá trị × `loops` |
| Cộng thời gian của cha và con | Thời gian cha đã gồm con | Lấy cha trừ con |
| `EXPLAIN ANALYZE DELETE ...` trên production | Câu chạy thật, xoá thật | Transaction + `ROLLBACK`, hoặc chạy trên bản sao |
| So `cost` giữa hai câu khác nhau | `cost` là đơn vị nội bộ | Chỉ so plan của cùng một câu; đo bằng thời gian thật |
| Tối ưu câu chậm nhất thay vì câu tốn tải nhất | Câu nhanh nhưng chạy rất nhiều mới là gánh nặng | Xếp hạng theo tổng thời gian (tần suất × thời gian) |
| Phân trang sâu bằng `OFFSET` | Đọc rồi vứt hết các dòng trước | Keyset; nếu buộc offset thì deferred join |
| Keyset không có tie-breaker | Lặp hoặc sót dòng ở ranh giới | Thêm cột unique vào `ORDER BY`, `WHERE`, index |
| `DELETE`/`UPDATE` hàng triệu dòng một câu | Lock lâu, undo phình, replica trễ | Batch theo PK |
| Gặp plan sai là thêm `FORCE INDEX` ngay | Khoá cứng plan, sai khi dữ liệu đổi | `ANALYZE TABLE`, histogram, sửa index/query trước |
| `SET GLOBAL long_query_time` rồi thấy connection cũ không ghi log | Biến chỉ áp dụng cho connection mới | Kết nối lại, hoặc chờ pool tạo connection mới |

## Tóm tắt chương

- MySQL dùng cost-based optimizer: ước lượng chi phí các phương án dựa trên statistics và chọn rẻ nhất.
  Plan phụ thuộc dữ liệu, nên có thể đổi khi dữ liệu và thống kê đổi.
- `EXPLAIN` không chạy query. Đọc `type` (`ALL`, `index` là quét hết), `key`, `key_len` (dùng tới cột nào
  của composite index), `rows × filtered`, và `Extra` (`Using filesort`, `Using temporary`, `Using index`).
- Cột không có index hay histogram bị đoán bằng hệ số cố định (10% cho `=`), là nguồn ước lượng lệch.
- `EXPLAIN ANALYZE` chạy thật: đọc từ trong ra, thời gian cha gồm con, `time`/`rows` là trung bình mỗi
  loop, so ước lượng với thật để tìm chỗ optimizer đoán sai.
- `ANALYZE TABLE` làm mới thống kê index; histogram cho cột không có index, không tự cập nhật trừ khi
  dùng `AUTO UPDATE`.
- MySQL có nested loop và hash join (8.0.18+), không có merge join; hash join trong query OLTP thường là
  thiếu index trên cột join.
- Quy trình: tìm (slow log, `performance_schema`, `sys`, `pt-query-digest`) → xếp hạng theo tổng tải →
  `EXPLAIN ANALYZE` → sửa theo thứ tự chi phí → đo lại.
- Phân trang sâu dùng keyset với tie-breaker unique; `COUNT(*)` toàn bảng InnoDB luôn phải duyệt index;
  sửa/xoá hàng loạt theo batch PK.
- Hint (`FORCE INDEX`, `/*+ INDEX(...) */`, `JOIN_ORDER`...) là giải pháp cuối cùng.

## Câu hỏi tự kiểm tra

1. Vì sao cùng một câu SQL và cùng index lại có thể có plan khác nhau trên máy dev và production? (2.3)
2. `type: index` và `type: ref` khác nhau thế nào? Khi nào `ref` lại tệ? (3.3)
3. Một index `(user_id BIGINT NOT NULL, status VARCHAR(10) NOT NULL, created_at DATETIME NOT NULL)` với
   utf8mb4, `key_len` là 8, 50 và 55 lần lượt cho biết điều gì? (3.5)
4. `EXPLAIN` báo `rows: 997423, filtered: 1.00` trong khi chỉ 34 dòng khớp. Con số 1% đến từ đâu, và
   làm sao để optimizer ước lượng tốt hơn? (3.4, 5.4)
5. Trong `EXPLAIN ANALYZE`, một node có `actual time=0.04..0.18 rows=100 loops=100`. Node này tốn tổng
   bao nhiêu thời gian và trả bao nhiêu dòng? (4.3)
6. Histogram khác thống kê index ở chỗ nào? Vì sao tạo histogram trên cột đã có index thường vô ích? (5.4)
7. Khi nào hash join là dấu hiệu tốt, khi nào là dấu hiệu xấu? (6.2)
8. Một câu 2 giây chạy 10 lần mỗi ngày và một câu 30 ms chạy 50 lần mỗi giây: sửa câu nào trước, vì sao? (8.1)
9. Vì sao keyset pagination cần tie-breaker, và vì sao trên MySQL nên viết điều kiện dạng `OR`/`AND`
   thay vì `(a, b) < (?, ?)`? (9.2)
10. `FORCE INDEX` có đảm bảo index được dùng không? Vì sao hint là giải pháp cuối cùng? (12.1, 12.5)

## Bài tập

1. **Đọc plan qua từng bước.** Trên dữ liệu mẫu, với câu "20 đơn `pending` mới nhất của user 777 trong
   tháng 6/2025", ghi lại `EXPLAIN` và `EXPLAIN ANALYZE` khi: (a) chỉ có PK, (b) có index `(user_id)`,
   (c) có index bạn tự thiết kế để không còn `Using filesort`. Trước mỗi lần chạy, viết ra dự đoán `type`,
   `key_len`, `rows`, rồi so với thật. Tự đếm số dòng khớp bằng một câu `COUNT(*)` để kiểm `rows`.
2. **Histogram.** Thêm 10.000 đơn `status = 'refunded'` (dùng recursive CTE như mục 1, id từ 1000001).
   So `filtered` của `EXPLAIN SELECT * FROM orders WHERE status = 'refunded'` (khi `status` không đứng đầu
   index nào) trước và sau khi tạo histogram trên `status`. Giải thích con số trước và sau.
3. **Phân trang.** Viết hai câu lấy trang thứ 25.000 (20 dòng mỗi trang, sắp theo `created_at DESC, id
   DESC`): một bằng `OFFSET`, một bằng keyset (bạn tự tìm giá trị dòng cuối trang trước). So `EXPLAIN
   ANALYZE` hai câu. Thêm câu deferred join và so tiếp.
4. **Batch update.** Viết một script (PHP với PDO hoặc ngôn ngữ bạn chọn) chuyển mọi đơn `pending` tạo
   trước 2025-04-01 thành `cancelled` theo batch 2.000 dòng, in thời gian mỗi batch. Trong lúc script
   chạy, mở một client khác và kiểm tra `SHOW PROCESSLIST` cùng `sys.innodb_lock_waits`.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [EXPLAIN Statement](https://dev.mysql.com/doc/refman/8.4/en/explain.html),
  [EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html),
  [Extended EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-extended.html),
  [The Optimizer Cost Model](https://dev.mysql.com/doc/refman/8.4/en/cost-model.html),
  [Optimizer Statistics](https://dev.mysql.com/doc/refman/8.4/en/optimizer-statistics.html),
  [Configuring Persistent Optimizer Statistics Parameters](https://dev.mysql.com/doc/refman/8.4/en/innodb-persistent-stats.html),
  [ANALYZE TABLE Statement](https://dev.mysql.com/doc/refman/8.4/en/analyze-table.html),
  [Nested-Loop Join Algorithms](https://dev.mysql.com/doc/refman/8.4/en/nested-loop-joins.html),
  [Hash Join Optimization](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html),
  [The Slow Query Log](https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html),
  [Performance Schema Statement Digests](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-statement-digests.html),
  [sys statement_analysis](https://dev.mysql.com/doc/refman/8.4/en/sys-statement-analysis.html),
  [LIMIT Query Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html),
  [Row Constructor Expression Optimization](https://dev.mysql.com/doc/refman/8.4/en/row-constructor-optimization.html),
  [Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html) (COUNT),
  [Index Hints](https://dev.mysql.com/doc/refman/8.4/en/index-hints.html),
  [Optimizer Hints](https://dev.mysql.com/doc/refman/8.4/en/optimizer-hints.html),
  [Switchable Optimizations](https://dev.mysql.com/doc/refman/8.4/en/switchable-optimizations.html),
  [Controlling Query Plan Evaluation](https://dev.mysql.com/doc/refman/8.4/en/controlling-query-plan-evaluation.html).
- Mã nguồn MySQL 8.4, `sql/item.h` (các hằng `COND_FILTER_*`):
  https://github.com/mysql/mysql-server/blob/8.4/sql/item.h
- Percona Toolkit: [pt-query-digest](https://docs.percona.com/percona-toolkit/pt-query-digest.html).
- Markus Winand, Use The Index, Luke: [No Offset](https://use-the-index-luke.com/no-offset),
  [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page).
- PostgreSQL: [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html).
