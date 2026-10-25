# Chương 11. Index

> [← Mục lục](README.md) · [← Chương 10: Window function](10-window-function.md) · [Chương 12: EXPLAIN và tối ưu truy vấn →](12-explain-toi-uu-query.md)

**Bạn sẽ học được:**

- Vì sao một câu `SELECT` đơn giản có thể chậm dần theo kích thước bảng, và index giải quyết chuyện
  đó bằng cách nào.
- Cấu trúc B+tree mà InnoDB dùng cho index: page, node gốc, node nhánh, node lá, độ cao của cây, và
  vì sao cây chỉ cao 3 đến 4 tầng cho hàng trăm triệu dòng.
- Cách InnoDB lưu bảng thành *clustered index*, cách *secondary index* tìm về dòng đầy đủ, và cái giá
  của bước *lookup* đó.
- Tạo, xem, xoá index; dùng đúng composite index (quy tắc leftmost prefix, thứ tự cột), covering
  index, index cho `ORDER BY` và `GROUP BY`.
- Nhận ra những câu truy vấn làm index không được dùng, và biết khi nào cần functional index, prefix
  index, multi-valued index cho JSON, invisible index, descending index, full-text index.
- Biết cái giá của index để không thêm bừa, và đối chiếu với các loại index của PostgreSQL.

**Cần biết trước:** [Chương 04](04-ddl-constraint.md) (`CREATE TABLE`, `PRIMARY KEY`, `UNIQUE`,
`ALTER TABLE`, generated column), [Chương 05](05-select-co-ban.md) (`SELECT`, `WHERE`, `ORDER BY`,
`LIMIT`), [Chương 08](08-group-by-aggregate.md) (`GROUP BY`), [Chương 09](09-subquery-cte-union.md)
(recursive CTE, dùng để sinh dữ liệu mẫu). Chương này dùng lệnh `EXPLAIN` ở mức đơn giản nhất; đọc
`EXPLAIN` đầy đủ là việc của [chương 12](12-explain-toi-uu-query.md).

## 1. Dữ liệu mẫu của chương

Index chỉ thể hiện tác dụng khi bảng có đủ nhiều dòng: với bảng 10 dòng, MySQL đọc cả bảng còn nhanh
hơn dùng index, và bạn sẽ không thấy gì khác biệt. Vì vậy chương này sinh dữ liệu bằng recursive CTE
(chương 09): 10.000 khách hàng và 200.000 đơn hàng.

Nếu chưa có MySQL, chạy bằng Docker:

```bash
# Chạy trên máy của bạn (terminal thường)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi vài giây cho server khởi động xong, rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Rồi dán đoạn SQL sau vào client `mysql`:

```sql
DROP DATABASE IF EXISTS ch11;      -- database riêng của chương này, xoá đi tạo lại cho sạch
CREATE DATABASE ch11;
USE ch11;

-- Recursive CTE mặc định chỉ cho đệ quy 1000 tầng (biến cte_max_recursion_depth).
-- Ta cần sinh 200.000 dòng nên nâng giới hạn cho session hiện tại.
SET SESSION cte_max_recursion_depth = 200000;

-- Khách hàng: CỐ Ý chỉ có PRIMARY KEY, chưa có index nào khác.
CREATE TABLE customers (
  id         INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email      VARCHAR(100) NOT NULL,
  full_name  VARCHAR(100) NOT NULL,
  city       VARCHAR(30)  NOT NULL,
  phone      VARCHAR(15)  NOT NULL,      -- số điện thoại lưu dạng CHUỖI (cố ý, dùng ở mục 9)
  created_at DATETIME     NOT NULL
);

INSERT INTO customers (email, full_name, city, phone, created_at)
WITH RECURSIVE seq (n) AS (
  SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 10000
)
SELECT CONCAT('user', n, '@example.com'),                          -- user1@example.com ...
       CONCAT('Khách ', n),
       ELT(n % 5 + 1, 'Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Huế', 'Cần Thơ'),
       CONCAT('09', LPAD(n, 8, '0')),                              -- 0900000001 ...
       TIMESTAMP '2024-01-01 00:00:00' + INTERVAL n HOUR
FROM seq;

-- Đơn hàng: cũng chỉ có PRIMARY KEY.
CREATE TABLE orders (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  customer_id INT UNSIGNED  NOT NULL,
  status      VARCHAR(10)   NOT NULL,    -- 'pending', 'paid', 'shipped', 'cancelled'
  total       DECIMAL(10,2) NOT NULL,
  created_at  DATETIME      NOT NULL,
  note        VARCHAR(200)  NULL
);

INSERT INTO orders (customer_id, status, total, created_at)
WITH RECURSIVE seq (n) AS (
  SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 200000
)
SELECT n % 10000 + 1,                                              -- mỗi khách đúng 20 đơn
       CASE WHEN n % 1000 = 0 THEN 'pending'                       -- pending rất hiếm: 200 đơn
            ELSE ELT(n % 3 + 1, 'paid', 'shipped', 'cancelled') END,
       n % 500 + 0.99,
       TIMESTAMP '2025-01-01 00:00:00' + INTERVAL n * 4 MINUTE     -- đơn sau tạo muộn hơn đơn trước
FROM seq;

-- Cập nhật thống kê để optimizer ước lượng đúng (giải thích ở chương 12)
ANALYZE TABLE customers, orders;
```

Vài con số tự kiểm được bằng tay, sẽ dùng lại trong chương:

- `customers` có 10.000 dòng, `id` từ 1 tới 10000. Khách `id = n` có email `user<n>@example.com`,
  điện thoại `09` + `n` đệm đủ 8 chữ số. Ví dụ khách 42: `user42@example.com`, `0900000042`.
- `orders` có 200.000 dòng. Đơn thứ `n` thuộc khách `n % 10000 + 1`, nên mỗi khách có đúng 20 đơn.
  Khách 7 có các đơn `id` = 6, 10006, 20006, ..., 190006.
- Có đúng 200 đơn `pending` (các đơn có `id` chia hết cho 1000). Phần còn lại chia gần đều cho
  `paid`, `shipped`, `cancelled`.
- `created_at` của đơn tăng theo `id`, từ `2025-01-01 00:04:00` (đơn 1) tới `2026-07-10 13:20:00` (đơn 200000).

Chương này dùng `EXPLAIN` để hỏi MySQL "anh định chạy câu này thế nào". Chỉ cần đặt `EXPLAIN` trước câu
`SELECT`. Ta chỉ đọc vài cột:

| Cột | Ý nghĩa (đủ dùng cho chương này) |
|---|---|
| `type` | Cách truy cập bảng. `ALL` là đọc cả bảng; `const`, `eq_ref`, `ref`, `range` là có dùng index để thu hẹp; `index` là đọc toàn bộ một index |
| `possible_keys` | Các index có thể dùng |
| `key` | Index thực sự được chọn (`NULL` là không dùng index nào) |
| `key_len` | Số byte của phần index được dùng, cho biết dùng tới cột thứ mấy của index (mục 6.5) |
| `rows` | Ước lượng số dòng phải xem xét (là ước lượng, không phải đếm thật) |
| `Extra` | Ghi chú thêm, ví dụ `Using index`, `Using where`, `Using filesort` |

⚠️ Các bảng `EXPLAIN` trong chương là **output minh hoạ, đã rút gọn cột**. Con số `rows` trên máy bạn
có thể lệch một chút vì nó là ước lượng từ thống kê lấy mẫu; các cột `type`, `key` thường khớp, nhưng
nếu khác thì đó chính là lý do chương 12 tồn tại. Kết quả của các câu `SELECT` thường (không có
`EXPLAIN`) thì tính được bằng tay từ dữ liệu trên.

## 2. Vì sao cần index

### 2.1 Bài toán mở đầu: tìm một khách theo email

Màn hình đăng nhập cần tìm khách hàng theo email:

```sql
SELECT id, full_name FROM customers WHERE email = 'user4242@example.com';
```

```
+------+------------+
| id   | full_name  |
+------+------------+
| 4242 | Khách 4242 |
+------+------------+
```

Kết quả đúng, chạy cũng nhanh. Nhưng MySQL đã làm gì để tìm ra dòng đó? Hỏi bằng `EXPLAIN`:

```sql
EXPLAIN SELECT id, full_name FROM customers WHERE email = 'user4242@example.com';
```

```
-- output minh hoạ, rút gọn
+-----------+------+---------------+------+-------+-------------+
| table     | type | possible_keys | key  | rows  | Extra       |
+-----------+------+---------------+------+-------+-------------+
| customers | ALL  | NULL          | NULL | 10000 | Using where |
+-----------+------+---------------+------+-------+-------------+
```

`type = ALL` và `key = NULL` nghĩa là: không có index nào giúp được, MySQL đọc **từng dòng** trong
bảng, so `email` của dòng đó với chuỗi cần tìm, giữ lại dòng khớp. Cách này gọi là *full table scan*
(quét toàn bảng). `rows = 10000` là số dòng MySQL ước lượng phải xem.

Tài liệu MySQL mô tả đúng điều này: không có index, MySQL phải bắt đầu từ dòng đầu tiên và đọc hết cả
bảng để tìm các dòng liên quan; bảng càng lớn thì càng tốn.

Chi phí của full table scan tỉ lệ với số dòng của bảng, không phụ thuộc vào số dòng khớp:

| Số dòng trong bảng | Số dòng phải đọc để tìm 1 email |
|---|---|
| 10.000 | 10.000 |
| 1 triệu | 1 triệu |
| 100 triệu | 100 triệu |

Với 10.000 dòng, cả bảng nằm gọn trong bộ nhớ, quét hết vẫn chỉ mất vài mili giây, nên bạn không cảm
thấy gì. Với 100 triệu dòng thì một lần đăng nhập phải đọc hàng chục GB dữ liệu. Đây là kiểu chậm nguy
hiểm nhất: **chạy tốt trên máy dev, chết trên production**, vì dữ liệu dev nhỏ.

### 2.2 Index là gì

Hãy nghĩ tới một cuốn sách giáo khoa 800 trang. Muốn tìm trang nói về "quang hợp", bạn có hai cách:

1. Lật từng trang từ đầu tới cuối. Đó là full table scan.
2. Mở phần *chỉ mục* (index) ở cuối sách: các thuật ngữ được **sắp theo vần A, B, C**, mỗi thuật ngữ
   ghi số trang. Vì đã sắp theo vần, bạn nhảy thẳng tới vần Q, tìm "quang hợp", đọc số trang, lật tới
   đúng trang đó.

Index trong database là đúng ý tưởng số 2:

- *Index* là một **cấu trúc dữ liệu riêng**, đi kèm bảng, chứa **bản sao giá trị** của một hoặc vài
  cột (gọi là *key* của index).
- Các key được giữ **luôn ở trạng thái đã sắp xếp**, nên tìm một giá trị không cần xem mọi phần tử.
- Mỗi key có **đường dẫn về dòng đầy đủ** trong bảng (như số trang trong chỉ mục sách).

Tạo index cho cột `email` rồi hỏi lại:

```sql
CREATE INDEX idx_email ON customers (email);

EXPLAIN SELECT id, full_name FROM customers WHERE email = 'user4242@example.com';
```

```
-- output minh hoạ, rút gọn
+-----------+------+---------------+-----------+------+-------+
| table     | type | possible_keys | key       | rows | Extra |
+-----------+------+---------------+-----------+------+-------+
| customers | ref  | idx_email     | idx_email |    1 | NULL  |
+-----------+------+---------------+-----------+------+-------+
```

Bây giờ `key = idx_email`, `type = ref` (tra index theo một giá trị cụ thể), và `rows = 1`: MySQL đi
thẳng tới đúng chỗ thay vì đọc 10.000 dòng. Câu `SELECT` vẫn trả về đúng kết quả cũ. Index **không bao
giờ làm thay đổi kết quả** của truy vấn, nó chỉ thay đổi **cách** MySQL tìm ra kết quả đó.

Quan trọng: bạn không bao giờ phải viết "hãy dùng index này" trong câu `SELECT`. Phần của MySQL gọi là
*optimizer* (bộ tối ưu truy vấn) tự xem có những index nào, ước lượng chi phí từng cách, rồi tự chọn.
Việc của bạn là **tạo đúng index** và **viết câu truy vấn sao cho index dùng được**. Cả chương này xoay
quanh hai việc đó.

### 2.3 Index được dùng vào những việc gì

Tài liệu MySQL liệt kê các thao tác dùng index. Viết lại bằng lời thường:

| Việc | Ví dụ | Học ở |
|---|---|---|
| Tìm các dòng khớp điều kiện `WHERE` | `WHERE email = ?`, `WHERE created_at >= ?` | Mục 3, 6, 9 |
| Loại bớt dòng khi có nhiều lựa chọn: optimizer thường chọn index lọc ra ít dòng nhất | Hai index trên `city` và `email`, `WHERE` có cả hai | Mục 6, chương 12 |
| Lấy dòng ở bảng khác khi JOIN | `JOIN orders o ON o.customer_id = c.id` cần index trên `orders.customer_id` | Mục 6.6 |
| Tìm `MIN()`, `MAX()` của một cột có index mà không đọc cả bảng | `SELECT MAX(created_at) FROM orders` | Mục 8.4 |
| Sắp xếp, gom nhóm mà không phải sort | `ORDER BY created_at LIMIT 20` | Mục 8 |
| Trả kết quả chỉ từ index, không cần đọc dòng đầy đủ | *Covering index* | Mục 7 |

Và tài liệu cũng nói rõ điều ngược lại: index ít quan trọng với bảng nhỏ, hoặc với các truy vấn báo
cáo phải xử lý gần hết bảng. Khi truy vấn cần đọc phần lớn các dòng, đọc tuần tự cả bảng nhanh hơn đi
qua index. Mục 9.6 giải thích vì sao.

### 2.4 Không có bữa trưa miễn phí

Nếu index nhanh như vậy, sao không index mọi cột? Vì index là một **bản sao có sắp xếp** của dữ liệu,
mà bản sao thì phải được giữ cho khớp với bảng:

- Mỗi `INSERT` phải thêm một entry vào **mọi** index của bảng; mỗi `DELETE` phải xoá ở mọi index; mỗi
  `UPDATE` một cột có index phải sửa index đó.
- Index chiếm chỗ trên đĩa và trong bộ nhớ đệm.

Nói gọn: index **làm đọc nhanh hơn và làm ghi chậm hơn**. Thiết kế index là cân bằng hai thứ này cho
đúng các câu truy vấn thật của ứng dụng. Mục 11 đi vào chi tiết cái giá.

Để hiểu vì sao index tìm được nhanh, vì sao đôi khi nó không giúp gì, ta cần nhìn vào cấu trúc bên
trong: B+tree.

## 3. B+tree: cấu trúc bên trong của index

### 3.1 Đĩa đọc theo page, không theo dòng

InnoDB không đọc đĩa từng dòng một mà theo khối cố định gọi là *page*. Kích thước page mặc định là
16 KB, đặt bằng biến `innodb_page_size`; tài liệu MySQL ghi biến này chỉ cấu hình được trước khi khởi
tạo instance và không đổi được sau đó. Page vừa đọc được giữ trong vùng nhớ đệm gọi là *buffer pool*
(chương 16). Đọc 1 byte hay đọc cả page tốn gần như cùng một lần I/O, nên một cấu trúc tra cứu tốt là
cấu trúc **chạm vào ít page nhất**.

Thử hai cấu trúc đơn giản trước:

| Cấu trúc | Tìm một giá trị | Chèn một giá trị | Vấn đề |
|---|---|---|---|
| Mảng đã sắp xếp | Nhanh (binary search) | Chậm: phải dời mọi phần tử phía sau | Ghi quá đắt |
| Danh sách liên kết đã sắp xếp | Chậm: đi từng nút | Nhanh: chỉ sửa con trỏ | Đọc quá đắt |

B+tree kết hợp ưu điểm của cả hai: tầng dưới cùng là danh sách liên kết (chèn rẻ), phía trên là một
cây tìm kiếm cân bằng (tìm nhanh).

### 3.2 Các thành phần của cây

```
                         [ root:  1 | 4000 | 8000 ]                       <- level 2
                     /              |             \
       [ 1 | 1500 | 2700 ]   [ 4000 | 5300 | 6600 ]   [ 8000 | 9200 ]     <- level 1 (branch)
        /      |      \           ...                      ...
  [1..1499] <-> [1500..2699] <-> [2700..3999] <-> [4000..5299] <-> ...    <- level 0 (leaf)
```

- *Node lá* (leaf node, level 0): chứa các entry của index **theo thứ tự key**. Các lá nối nhau thành
  *danh sách liên kết hai chiều* (mỗi page có con trỏ tới page trước và page sau), nên đi tiến hoặc
  lùi đều được. Bên trong một page, các record cũng được nối theo thứ tự key tăng dần.
- *Node nhánh* (branch, Jeremy Cole gọi là *internal page*) và *node gốc* (root): không chứa dữ liệu,
  chỉ chứa các *node pointer*: cặp (key nhỏ nhất của page con, số hiệu page con). Nhìn vào node pointer
  là biết đi xuống page con nào.
- Cây *cân bằng* (balanced): mọi lá cách gốc cùng một số tầng, nên tìm giá trị nào cũng tốn cùng số
  bước. Lưu ý: B-tree là cây cân bằng nhiều nhánh, **không phải** cây nhị phân.
- Mỗi node là một page. Page gốc có vị trí cố định, ghi trong data dictionary. Theo Jeremy Cole, khi
  gốc đầy, InnoDB chuyển các record của gốc sang một page mới rồi tách page đó; gốc "được nâng lên"
  một tầng và cây cao thêm 1.

Phân biệt tên gọi: *B-tree* cổ điển lưu dữ liệu ở cả node nhánh; *B+tree* chỉ lưu dữ liệu ở lá, node
nhánh chỉ để định hướng, nhờ vậy node nhánh chứa được nhiều key hơn và range scan chỉ cần đi dọc tầng
lá. Tài liệu MySQL thường viết "B-tree", nhưng cấu trúc InnoDB dùng là B+tree.

### 3.3 Tìm một giá trị: đi từ gốc xuống lá

Tìm `id = 5000` trong cây ở trên:

1. Đọc page gốc: 5000 nằm giữa 4000 và 8000, theo node pointer `4000` xuống page con.
2. Đọc page nhánh `[4000 | 5300 | 6600]`: 5000 nằm giữa 4000 và 5300, xuống lá `[4000..5299]`.
3. Đọc page lá, tìm record `5000` trong page.

Ba page cho một lần tìm, dù bảng có 10.000 hay vài triệu dòng. Số page phải đọc bằng **chiều cao
cây**.

### 3.4 Range scan: đi dọc tầng lá

Với `WHERE id BETWEEN 3900 AND 4100`:

1. Đi xuống cây như trên để tìm điểm bắt đầu `3900` (nằm trong lá `[2700..3999]`).
2. Đọc tuần tự các entry trong lá đó; hết lá thì theo con trỏ "page sau" sang lá `[4000..5299]`.
3. Dừng khi gặp entry đầu tiên lớn hơn `4100`.

Không cần quay lại gốc. Đây là lý do B+tree phục vụ tốt `>`, `<`, `BETWEEN`, `LIKE 'abc%'`, và
`ORDER BY` (mục 8): mọi thứ đã nằm sẵn theo thứ tự ở tầng lá.

### 3.5 Vì sao cây rất thấp

Mỗi node nhánh là một page 16 KB, mà một node pointer chỉ gồm key và số page, nên một page nhánh chứa
được hàng trăm tới hơn một nghìn node pointer. Số này gọi là *fan-out*. Cây có fan-out F và chiều
cao h chứa được khoảng F^(h-1) lá: mỗi tầng thêm vào nhân sức chứa lên F lần.

Jeremy Cole tính cho một bảng InnoDB đơn giản chỉ có một cột `INT UNSIGNED` làm primary key, giả sử
page đầy hoàn hảo: 468 record mỗi page lá, 1203 record mỗi page nhánh. Sức chứa tối đa theo chiều cao:

| Chiều cao | Số dòng tối đa |
|---|---|
| 1 | 468 |
| 2 | hơn 563 nghìn |
| 3 | hơn 677 triệu |
| 4 | hơn 814 tỉ |

Thực tế page không bao giờ đầy hoàn hảo và dòng thật dài hơn nhiều, nên số thật nhỏ hơn, nhưng thứ
bậc vẫn vậy: dữ liệu tăng gấp nghìn lần chỉ thêm khoảng một tầng. Cole nhận xét đa số bảng có primary
key hợp lý cao 2 tới 3 tầng, một số đạt 4. Use The Index, Luke ghi nhận index thực tế với hàng triệu
record thường sâu 4 hoặc 5 tầng, hiếm khi thấy 6. Các tầng trên được dùng liên tục nên gần như luôn
nằm trong buffer pool; một lần tra thực tế chỉ tốn rất ít lần đọc đĩa.

So với các cấu trúc khác:

| Cấu trúc | Tìm `=` | Range, sort, `LIKE 'abc%'` | Ghi chú |
|---|---|---|---|
| Cây nhị phân cân bằng | log₂(n) bước | Được | Mỗi node 1 key nên cây rất cao: 1 tỉ dòng cần khoảng 30 tầng, mỗi tầng có thể là một lần đọc page |
| Hash index | Rất nhanh | Không | Hash làm mất thứ tự; tài liệu MySQL ghi hash index chỉ dùng cho `=` và `<=>`, không dùng cho `ORDER BY` |
| B+tree | log_F(n), F hàng trăm | Được | Ghi phải giữ cây cân bằng (tách page) |

Với InnoDB, kiểu index duy nhất cho phép trong `USING` là `BTREE`; ghi `USING HASH` thì MySQL dùng
kiểu mặc định của engine thay thế (bảng "Index Types Per Storage Engine" trong tài liệu `CREATE INDEX`).
Hash index thật có ở engine `MEMORY`.

### 3.6 Ba bước của một lần tra index, và vì sao "có index vẫn chậm"

Use The Index, Luke chia một lần tra index thành ba bước:

1. **Đi xuống cây** từ gốc tới lá. Số page bị chặn bởi chiều cao cây: luôn rẻ.
2. **Đi dọc chuỗi lá** để lấy mọi entry khớp. Không có giới hạn trên: khớp 1 triệu entry là đọc
   1 triệu entry.
3. **Lấy dữ liệu dòng** cho mỗi entry khớp, thường ở các page rải rác (với InnoDB là bước *lookup*,
   mục 4.3).

Chỉ bước 1 có giới hạn. Bước 2 và 3 là lý do một truy vấn có dùng index vẫn chậm. Sách gọi niềm tin
"index chậm vì cây bị lệch, rebuild là hết" là một huyền thoại: B+tree luôn cân bằng; chậm là do quét
quá nhiều lá và lấy quá nhiều dòng. Nhớ ba bước này, phần còn lại của chương sẽ dễ hiểu hơn nhiều.

## 4. Clustered index và secondary index trong InnoDB

### 4.1 Bảng chính là một cây: clustered index

Ở mục 3, index được mô tả như một cấu trúc riêng "trỏ về dòng". InnoDB đi xa hơn: **mỗi bảng InnoDB
có một index đặc biệt gọi là *clustered index*, chứa chính dữ liệu dòng**. Đó là một B+tree sắp theo
primary key, và node lá chứa **toàn bộ các cột** của dòng. Không có "bảng" nào nằm riêng bên ngoài
cây này.

```
Clustered index của customers (sắp theo id)

                 [ root: 1 | 4000 | 8000 ]                 <- chỉ có id + số page con
               /            |             \
    [ ... ]           [ 4000 | 5300 | ... ]      [ ... ]   <- branch
                        /
   leaf: (4000, user4000@example.com, Khách 4000, Hà Nội, 0900004000, ...)   <- DÒNG ĐẦY ĐỦ
         (4001, user4001@example.com, Khách 4001, Hồ Chí Minh, ...)
         ...                                      <-> lá kế tiếp <-> ...
```

InnoDB chọn clustered index như sau (tài liệu "Clustered and Secondary Indexes"):

1. Có `PRIMARY KEY` thì dùng primary key.
2. Không có thì dùng index `UNIQUE` đầu tiên mà mọi cột đều `NOT NULL`.
3. Không có nốt thì InnoDB tạo clustered index ẩn tên `GEN_CLUST_INDEX` trên một cột ẩn chứa row ID
   6 byte, tăng dần theo thứ tự insert.

Tài liệu khuyên mỗi bảng nên có primary key; không có cột tự nhiên phù hợp thì thêm cột
auto-increment (chương 04).

Hệ quả:

- **Tra theo primary key là nhanh nhất**: đi xuống một cây là tới dòng. Tài liệu nói truy cập dòng qua
  clustered index nhanh vì lần tìm dẫn thẳng tới page chứa dữ liệu dòng.
- **Range theo primary key rất rẻ**: `WHERE id BETWEEN 1000 AND 2000` đọc một dải lá liền nhau.
- **Mỗi bảng chỉ có một clustered index**, vì dữ liệu chỉ sắp được theo một thứ tự.
- **Đổi giá trị primary key là đắt**: dòng phải chuyển chỗ trong cây và mọi secondary index phải sửa
  theo (mục 4.2). Đừng chọn cột hay thay đổi (email, số điện thoại) làm primary key.

### 4.2 Secondary index: entry chứa key cộng primary key

Mọi index không phải clustered index gọi là *secondary index*. Theo tài liệu MySQL, mỗi record của
secondary index chứa **các cột được index cộng với các cột primary key** của dòng; InnoDB dùng giá trị
primary key đó để tìm dòng trong clustered index. Secondary index **không** chứa địa chỉ vật lý của
dòng.

```
Secondary index idx_email (sắp theo email)           Clustered index (sắp theo id)
 leaf: (user4241@example.com, 4241)                   leaf: (4241, user4241@..., Khách 4241, ...)
       (user4242@example.com, 4242) --- id = 4242 --->       (4242, user4242@..., Khách 4242, ...)
       (user4243@example.com, 4243)                          (4243, user4243@..., Khách 4243, ...)
```

Vì sao lưu primary key mà không lưu địa chỉ? Dòng trong clustered index **di chuyển** khi page bị tách
hoặc gộp. Nếu secondary index lưu địa chỉ page thì mỗi lần tách page phải sửa hàng loạt index; lưu
primary key thì dòng chạy đi đâu cũng tìm lại được. Cái giá là bước lookup tốn thêm một lượt đi xuống
cây.

Lưu ý thứ tự trong lá: hai entry cùng email (nếu index không unique) được sắp tiếp theo primary key.
Tức là entry thật của `idx_email` là `(email, id)`.

### 4.3 Lookup: tra hai cây

Đường đi của `SELECT id, full_name FROM customers WHERE email = 'user4242@example.com'` với `idx_email`:

1. Đi từ gốc xuống lá của `idx_email` theo `'user4242@example.com'`.
2. Đọc entry `(user4242@example.com, 4242)`, lấy được `id = 4242`.
3. Đi từ gốc xuống lá của **clustered index** theo `id = 4242`.
4. Lấy `full_name` từ dòng đầy đủ.

Bước 3 gọi là *lookup* (có tài liệu gọi là *bookmark lookup* hay "tra lại bảng"). Một dòng thì không
đáng kể. Nhưng một câu khớp 50.000 entry là 50.000 lần đi xuống clustered index ở các vị trí rải rác:
đây chính là bước 3 "lấy dữ liệu dòng" của mục 3.6, và là lý do optimizer đôi khi bỏ index (mục 9.6).

### 4.4 Hệ quả: primary key nên ngắn, tăng dần, không đổi

- **Primary key dài làm mọi secondary index phình to.** Tài liệu MySQL: primary key dài thì secondary
  index tốn nhiều chỗ hơn, nên dùng primary key ngắn. Primary key `CHAR(36)` (UUID dạng chuỗi) bị chép
  vào mọi secondary index, so với 4 hoặc 8 byte của `INT`/`BIGINT`.
- **Insert theo thứ tự tăng dần là rẻ nhất.** Tài liệu "Physical Structure of an InnoDB Index": InnoDB
  cố để trống 1/16 mỗi page; nếu record được chèn tuần tự (tăng hoặc giảm), page đầy khoảng 15/16; nếu
  chèn ngẫu nhiên, page chỉ đầy từ 1/2 tới 15/16. Primary key ngẫu nhiên (UUIDv4) làm mỗi insert rơi
  vào một lá bất kỳ, gây tách page và tốn bộ nhớ hơn. Chọn kiểu primary key (auto-increment, UUIDv7)
  được bàn ở chương 02 và chương 16.
- **Primary key có mặt miễn phí trong mọi secondary index**, điều này giúp covering index (mục 7).

### 4.5 Đối chiếu nhanh: PostgreSQL không có clustered index kiểu InnoDB

PostgreSQL lưu dòng trong *heap* (các page không sắp theo thứ tự nào); mọi index, kể cả primary key,
đều chứa key và địa chỉ vật lý của dòng (*ctid*). Tra index xong nhảy thẳng tới dòng, không phải đi
xuống cây thứ hai. Đổi lại, `UPDATE` trong PostgreSQL ghi một bản dòng mới ở vị trí khác nên có thể
phải thêm entry vào các index. Chi tiết ở mục 13 và chương 25.

## 5. Tạo, xem và xoá index

### 5.1 Các cách tạo index

```sql
-- Cách 1: khai báo ngay khi tạo bảng (tài liệu khuyên làm vậy khi có thể)
CREATE TABLE demo_tags (
  id   INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  slug VARCHAR(50) NOT NULL,
  name VARCHAR(50) NOT NULL,
  UNIQUE KEY uk_slug (slug),          -- KEY và INDEX là từ đồng nghĩa (chương 04)
  INDEX idx_name (name)
);

-- Cách 2: CREATE INDEX trên bảng đã có
CREATE INDEX idx_city ON customers (city);

-- Cách 3: ALTER TABLE, gộp được nhiều thay đổi trong một lệnh
ALTER TABLE orders ADD INDEX idx_customer (customer_id);
```

Tài liệu MySQL ghi `CREATE INDEX` được ánh xạ thành một câu `ALTER TABLE`, và `CREATE INDEX` không tạo
được `PRIMARY KEY` (phải dùng `ALTER TABLE ... ADD PRIMARY KEY`).

Đặt tên index có quy ước (ví dụ `idx_<cột>`, `uk_<cột>` cho unique) để đọc `EXPLAIN` và thông báo lỗi
dễ hơn. Không đặt tên thì MySQL tự đặt theo tên cột đầu tiên.

Tạo index trên bảng lớn đang chạy production tốn thời gian và tài nguyên; cách làm an toàn (online
DDL, công cụ như gh-ost) là chủ đề của [chương 20](20-thay-doi-schema-migration.md). Sau khi tạo index,
tài liệu khuyên chạy `ANALYZE TABLE` khi `innodb_stats_persistent` đang bật (mặc định) để cập nhật
thống kê.

### 5.2 Xem các index của bảng

```sql
SHOW INDEX FROM customers;
```

```
-- output minh hoạ, rút gọn cột
+-----------+------------+-----------+--------------+-------------+-------------+---------+
| Table     | Non_unique | Key_name  | Seq_in_index | Column_name | Cardinality | Visible |
+-----------+------------+-----------+--------------+-------------+-------------+---------+
| customers |          0 | PRIMARY   |            1 | id          |       10000 | YES     |
| customers |          1 | idx_email |            1 | email       |       10000 | YES     |
| customers |          1 | idx_city  |            1 | city        |           5 | YES     |
+-----------+------------+-----------+--------------+-------------+-------------+---------+
```

- `Non_unique`: 0 là index unique (gồm primary key), 1 là cho phép trùng.
- `Seq_in_index`: vị trí của cột trong index nhiều cột (mục 6).
- `Cardinality`: **ước lượng** số giá trị khác nhau, lấy từ thống kê lấy mẫu (chương 12).
- `Visible`: index có hiện với optimizer không (mục 10.4).

Cách khác: `SHOW CREATE TABLE customers\G` in lại toàn bộ định nghĩa bảng kèm index.

### 5.3 Xoá index

```sql
DROP INDEX idx_city ON customers;
-- hoặc
ALTER TABLE customers DROP INDEX idx_city;
```

⚠️ Xoá index trên production là thao tác rủi ro: nếu có câu truy vấn đang dựa vào nó, câu đó lập tức
chuyển sang full table scan. Cách an toàn là làm index *invisible* trước (mục 10.4).

### 5.4 UNIQUE index: vừa là ràng buộc, vừa là index

`UNIQUE` index (chương 04) bắt mọi giá trị trong index phải khác nhau. Thêm dòng trùng key sẽ lỗi:

```sql
DROP INDEX idx_email ON customers;
CREATE UNIQUE INDEX uk_email ON customers (email);

INSERT INTO customers (email, full_name, city, phone, created_at)
VALUES ('user1@example.com', 'Trùng', 'Huế', '0999999999', NOW());
-- ERROR 1062 (23000): Duplicate entry 'user1@example.com' for key 'customers.uk_email'
```

Vì là index nên nó còn tăng tốc tra cứu. Và vì MySQL biết chắc mỗi giá trị khớp tối đa một dòng, kiểu
truy cập trong `EXPLAIN` tốt hơn `ref`:

```sql
EXPLAIN SELECT id, full_name FROM customers WHERE email = 'user4242@example.com';
-- output minh hoạ: type = const, key = uk_email, rows = 1
```

Ba điểm cần nhớ:

- Tài liệu `CREATE INDEX`: unique index **cho phép nhiều NULL** ở cột nhận NULL. Muốn "mỗi người tối đa
  một giá trị nhưng được để trống" thì đây đúng là hành vi mong muốn; muốn cấm trống thì khai `NOT NULL`.
- Unique index trên chuỗi tuân theo collation: với collation mặc định không phân biệt hoa thường,
  `User1@example.com` bị coi là trùng `user1@example.com` (chương 03, chương 04).
- Index **thường** và unique index tra cứu nhanh như nhau. Chọn `UNIQUE` vì đó là **luật nghiệp vụ**,
  không phải vì tốc độ. Ngược lại, đừng bỏ `UNIQUE` để "ghi nhanh hơn": mất ràng buộc là dữ liệu bẩn.

## 6. Composite index và quy tắc leftmost prefix

### 6.1 Composite index là gì

Index trên nhiều cột gọi là *composite index* (tài liệu MySQL gọi là *multiple-column index*). Tài
liệu ghi giá trị key được tạo bằng cách **nối** giá trị các cột theo thứ tự khai báo; InnoDB cho tối
đa 16 cột trong một index.

```sql
CREATE INDEX idx_cust_status_created ON orders (customer_id, status, created_at);
```

Cây được sắp theo `customer_id`; các entry cùng `customer_id` sắp theo `status`; cùng cả hai thì sắp
theo `created_at`; cuối cùng là `id` (primary key, mục 4.2). Giống danh bạ sắp theo họ, rồi tên đệm,
rồi tên:

```
Lá của idx_cust_status_created (rút gọn, chỉ khách 7 và 8):
 ... (7, cancelled, 2025-…) (7, cancelled, ...) ... (7, paid, ...) ... (7, shipped, ...) ...
     (8, cancelled, ...) ... (8, paid, ...) ... (8, shipped, ...) ...
     ^ sắp theo customer_id trước     ^ trong cùng khách, theo status     ^ rồi theo created_at
```

### 6.2 Leftmost prefix

Hệ quả của cách sắp xếp: các entry có `status = 'paid'` nằm **rải rác** trong từng khách, không liền
một đoạn. Vì vậy index chỉ "đi thẳng xuống cây" (*seek*) được khi điều kiện dùng một *leftmost prefix*
(tiền tố bên trái) của danh sách cột. Tài liệu MySQL: index `(col1, col2, col3)` cho khả năng tìm kiếm
trên `(col1)`, `(col1, col2)` và `(col1, col2, col3)`.

| Điều kiện trên index `(customer_id, status, created_at)` | Seek được? | Số cột dùng để thu hẹp |
|---|---|---|
| `customer_id = 7` | Có | 1 |
| `customer_id = 7 AND status = 'paid'` | Có | 2 |
| `customer_id = 7 AND status = 'paid' AND created_at >= '2026-01-01'` | Có | 3 |
| `status = 'paid' AND customer_id = 7` | Có: thứ tự viết trong `WHERE` không quan trọng | 2 |
| `customer_id = 7 AND created_at >= '2026-01-01'` | Có, nhưng chỉ thu hẹp theo `customer_id`; `created_at` lọc sau | 1 |
| `status = 'paid'` hoặc `created_at >= ...` | Không seek được (thiếu cột đầu) | 0 |
| `customer_id = 7 OR status = 'paid'` | Không dùng index này cho cả điều kiện | 0 |

Ví dụ trong tài liệu với `INDEX name (last_name, first_name)`: `WHERE last_name = 'Jones' AND
first_name >= 'M' AND first_name < 'N'` dùng được index; `WHERE first_name = 'John'` và
`WHERE last_name = 'Jones' OR first_name = 'John'` thì không.

Hệ quả thiết kế: index `(a, b)` phục vụ được cả truy vấn lọc theo `a` lẫn `a, b`, nên **thay được index
`(a)` riêng**. Có `(a, b)` rồi mà còn `(a)` thì `(a)` thường thừa (mục 11).

⚠️ "Không seek được" không có nghĩa là chắc chắn không dùng. MySQL có thể quét toàn bộ index
(`type = index`) nếu index nhỏ hơn bảng và chứa đủ cột cần (mục 7), hoặc dùng *skip scan* trong một số
trường hợp hẹp (chương 12). Nhưng đó không phải tra cứu nhanh.

### 6.3 Thứ tự cột: cột so sánh bằng trước, cột khoảng sau

Use The Index, Luke phân biệt hai vai trò của điều kiện khi đi qua index:

- *Access predicate*: quyết định điểm bắt đầu và điểm dừng của đoạn lá cần quét, tức thực sự thu hẹp.
- *Filter predicate*: chỉ được kiểm tra trên từng entry trong đoạn đã quét, không làm đoạn ngắn đi.

Mục tiêu là biến càng nhiều điều kiện thành access predicate càng tốt. Quy tắc ngắn gọn: **cột so
sánh `=` đứng trước, cột so sánh khoảng (range) đứng sau**.

So sánh hai index cho `WHERE customer_id = 7 AND created_at >= '2026-01-01'`:

```
index (created_at, customer_id):
  (2026-01-01 00:00, 1401) (2026-01-01 00:04, 1402) ... (… , 7) ... (…, 9001) ...   <- quét HẾT mọi đơn từ 2026-01-01,
                                                                                       lọc ra khách 7
index (customer_id, created_at):
  ... (7, 2025-…) | (7, 2026-01-…) (7, 2026-02-…) ... (7, 2026-06-…) | (8, …) ...  <- chỉ quét đoạn giữa hai vạch
```

Với index thứ nhất, đoạn `created_at >= '2026-01-01'` chứa đơn của mọi khách, `customer_id` trong đoạn
đó lộn xộn, chỉ còn là filter. Với index thứ hai, đơn của khách 7 nằm liền nhau và bên trong đã sắp theo
thời gian, nên cả hai điều kiện là access predicate.

Tài liệu "Range Optimization" phát biểu cùng quy tắc theo cách của optimizer: đi từ trái sang phải;
cột dùng `=`, `<=>` hoặc `IS NULL` thì đi tiếp sang cột sau; gặp cột đầu tiên dùng toán tử khoảng
(`>`, `<`, `>=`, `<=`, `BETWEEN`, `!=`, `<>`, `LIKE 'abc%'`) thì cột đó vẫn tham gia thu hẹp nhưng các
cột phía sau không tham gia nữa.

Vài lưu ý:

- `IN (...)` được xem như nhiều điểm `=`, nên cột phía sau vẫn tham gia thu hẹp. Nhưng `IN` phá thứ tự
  sort (mục 8.2).
- Khi có nhiều cột `=`, thứ tự giữa chúng ít ảnh hưởng đến chính câu đó; hãy chọn sao cho prefix phục
  vụ được nhiều câu truy vấn khác nhất. Lời khuyên "cột nhiều giá trị khác nhau đặt trước" chỉ là tiêu
  chí phụ.
- Hai câu cần range trên hai cột khác nhau thì một index không phục vụ tốt cả hai: chấp nhận hai index
  hoặc chấp nhận filter.

### 6.4 Thử trên dữ liệu mẫu

```sql
-- Cả 3 cột là access predicate
EXPLAIN SELECT * FROM orders
WHERE customer_id = 7 AND status = 'paid' AND created_at >= '2026-01-01';

-- Thiếu status: chỉ customer_id thu hẹp, created_at thành filter
EXPLAIN SELECT * FROM orders
WHERE customer_id = 7 AND created_at >= '2026-01-01';

-- status là khoảng: thu hẹp theo (customer_id, status), created_at thành filter
EXPLAIN SELECT * FROM orders
WHERE customer_id = 7 AND status > 'c' AND created_at >= '2026-01-01';
```

Cả ba câu đều dùng `idx_cust_status_created` (nếu bạn đã tạo `idx_customer` ở mục 5.1, optimizer có
thể chọn index đó cho câu thứ hai, vì với nó cả hai index đều chỉ thu hẹp theo `customer_id`). Cách
biết dùng tới cột nào là đọc `key_len`.

### 6.5 Đọc key_len để biết index dùng tới cột nào

`key_len` là tổng số byte của các cột index được dùng để thu hẹp. Cách tính cho bảng `orders`:

| Cột | Kiểu | Byte trong key_len |
|---|---|---|
| `customer_id` | `INT UNSIGNED NOT NULL` | 4 |
| `status` | `VARCHAR(10) NOT NULL`, utf8mb4 | 10 × 4 (tối đa 4 byte mỗi ký tự) + 2 (độ dài) = 42 |
| `created_at` | `DATETIME NOT NULL` | 5 |

Cột cho phép NULL cộng thêm 1 byte. Vậy ba câu ở mục 6.4 có `key_len` lần lượt khoảng 51 (cả ba cột),
4 (chỉ `customer_id`), 46 (`customer_id` và `status`). Chương 12 đọc `key_len` kỹ hơn.

### 6.6 Index cho JOIN

```sql
SELECT c.full_name, o.id, o.total
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE c.id = 7;
```

Kết quả: 20 dòng (đơn 6, 10006, ..., 190006 của Khách 7). Để làm câu này, MySQL lấy khách 7 qua primary
key, rồi cần tìm "các đơn có `customer_id = 7`". Không có index nào bắt đầu bằng `orders.customer_id`
thì mỗi dòng ở bảng ngoài kéo theo một lần quét 200.000 đơn. Quy tắc thực dụng: **cột dùng để join
(thường là khoá ngoại) cần có index ở phía bảng được tra**. Với `FOREIGN KEY`, InnoDB tự tạo index trên
cột khoá ngoại nếu chưa có index phù hợp (chương 04). Index `(customer_id, status, created_at)` ở trên
cũng phục vụ được, vì `customer_id` là cột đầu.

Tài liệu "How MySQL Uses Indexes" thêm: MySQL dùng index trên cột join hiệu quả hơn khi hai cột cùng
kiểu và cùng kích thước; so sánh hai cột chuỗi khác charset (ví dụ `utf8mb4` với `latin1`) làm index
không dùng được. Thuật toán join là chủ đề của chương 12.

## 7. Covering index và index condition pushdown

### 7.1 Covering index: trả lời chỉ bằng index

Nhắc lại mục 4.3: tra qua secondary index tốn thêm bước lookup về clustered index để lấy các cột còn
thiếu. Nếu **mọi cột câu truy vấn cần** (trong `SELECT`, `WHERE`, `ORDER BY`, `GROUP BY`) đều có sẵn
trong index, kể cả primary key luôn có sẵn, thì không cần lookup nữa. Index như vậy gọi là *covering
index* cho câu đó. Tài liệu MySQL: nếu truy vấn chỉ dùng các cột nằm trong một index, giá trị có thể lấy
từ cây index cho nhanh hơn. `EXPLAIN` hiện `Extra: Using index`.

```sql
-- Covering: customer_id, status, created_at, id đều nằm trong idx_cust_status_created
SELECT id, created_at FROM orders WHERE customer_id = 7 AND status = 'paid';
-- 7 dòng (khách 7 có 7 đơn paid, 7 đơn shipped, 6 đơn cancelled)

EXPLAIN SELECT id, created_at FROM orders WHERE customer_id = 7 AND status = 'paid';
-- output minh hoạ: type = ref, key = idx_cust_status_created, Extra = Using index

-- Không covering: total chỉ có ở clustered index, phải lookup
EXPLAIN SELECT id, total FROM orders WHERE customer_id = 7 AND status = 'paid';
-- output minh hoạ: type = ref, key = idx_cust_status_created, Extra = NULL (không có Using index)
```

Câu đếm cũng là covering: `SELECT COUNT(*) FROM orders WHERE customer_id = 7 AND status = 'paid'` (kết
quả 7) chỉ cần đếm entry trong index.

Covering mạnh nhất khi câu khớp nhiều dòng: hàng nghìn lookup ngẫu nhiên được thay bằng đọc tuần tự vài
page lá. Cái giá: thêm cột vào index làm index to hơn, và mọi `UPDATE` trên cột đó phải sửa index. Chỉ
làm covering cho những câu nóng nhất, đừng nhồi mọi cột vào index. MySQL không có mệnh đề `INCLUDE` như
PostgreSQL (mục 13); muốn covering thì thêm cột vào cuối key.

### 7.2 Index condition pushdown (ICP)

Xét câu `WHERE customer_id = 7 AND created_at >= '2026-01-01'` trên index `(customer_id, status,
created_at)`. Ở mục 6.4, `created_at` không phải access predicate vì thiếu `status`. Nhưng giá trị
`created_at` **có sẵn trong entry index**. Tài liệu "Index Condition Pushdown Optimization" mô tả:

Không có ICP:
1. Storage engine đọc entry index trong đoạn quét (mọi đơn của khách 7: 20 entry).
2. Lookup dòng đầy đủ cho từng entry (20 lần).
3. Trả dòng lên tầng server để kiểm tra phần còn lại của `WHERE`.

Có ICP:
1. Storage engine đọc entry index.
2. Kiểm tra ngay phần điều kiện chỉ cần cột trong index (`created_at >= ...`). Không thoả thì bỏ qua,
   **không lookup**.
3. Thoả thì mới lookup và trả lên server.

Câu này trả về 6 dòng (đơn 140006 tới 190006), nên ICP giảm từ 20 xuống 6 lần lookup. `EXPLAIN` hiện
`Extra: Using index condition`.

Theo tài liệu: ICP áp dụng cho kiểu truy cập `range`, `ref`, `eq_ref`, `ref_or_null` khi cần đọc dòng
đầy đủ; với InnoDB chỉ áp dụng cho secondary index; được bật mặc định (cờ
`index_condition_pushdown` trong `optimizer_switch`).

⚠️ Ba chữ hay nhầm trong `Extra`:

| `Extra` | Nghĩa |
|---|---|
| `Using index` | Covering: không lookup. Tốt nhất |
| `Using index condition` | ICP: lọc sớm trên index, vẫn lookup các entry thoả |
| `Using where` | Tầng server lọc thêm dòng sau khi storage engine trả về |

## 8. Index cho ORDER BY và GROUP BY

### 8.1 Index thay cho việc sort

Lá của index đã sắp sẵn. Nếu thứ tự đọc index trùng với `ORDER BY`, MySQL không cần sort, và với
`LIMIT` thì dừng ngay sau khi đủ số dòng. Use The Index, Luke gọi đây là *pipelined order by*.

```sql
CREATE INDEX idx_cust_created ON orders (customer_id, created_at);

SELECT id, created_at FROM orders
WHERE customer_id = 7
ORDER BY created_at DESC
LIMIT 5;
```

```
+--------+---------------------+
| id     | created_at          |
+--------+---------------------+
| 190006 | 2026-06-12 19:04:00 |
| 180006 | 2026-05-16 00:24:00 |
| 170006 | 2026-04-18 05:44:00 |
| 160006 | 2026-03-21 11:04:00 |
| 150006 | 2026-02-21 16:24:00 |
+--------+---------------------+
```

```sql
EXPLAIN SELECT id, created_at FROM orders WHERE customer_id = 7 ORDER BY created_at DESC LIMIT 5;
-- output minh hoạ: type = ref, key = idx_cust_created, Extra = Backward index scan; Using index
```

`Backward index scan`: MySQL đi ngược tầng lá (lá nối hai chiều), không sort. Trong index, sau khi cố
định `customer_id = 7`, các entry đã sắp theo `created_at`, nên chỉ cần đọc 5 entry cuối đoạn.

Điều kiện để index thay được sort (tài liệu "ORDER BY Optimization"):

1. Các cột `ORDER BY` là các cột **liên tiếp** của index, **sau** các cột đã cố định bằng `=` trong
   `WHERE`. Ví dụ index `(key_part1, key_part2)`: `WHERE key_part1 = c ORDER BY key_part2` dùng được.
2. Chiều sort thống nhất (cùng `ASC` hoặc cùng `DESC` thì đi xuôi hoặc ngược cả index), hoặc khớp với
   chiều khai báo của một descending index (mục 8.5).
3. `ORDER BY` không phải biểu thức trên cột (`ORDER BY ABS(x)` phải sort).
4. Index không phải prefix index trên cột chuỗi (mục 10.2).

### 8.2 Khi nào vẫn phải sort

- `WHERE customer_id IN (7, 8) ORDER BY created_at`: trong index, `created_at` chỉ sắp đúng bên trong
  từng khách; ghép hai đoạn thì không còn thứ tự chung.
- `WHERE customer_id > 9000 ORDER BY created_at`: range ở cột đầu kéo theo nhiều nhóm, cùng lý do.
- `WHERE status = 'paid' ORDER BY created_at` với index `(customer_id, created_at)`: thiếu cột đầu.
- `ORDER BY` trộn cột của hai index khác nhau.

Khi phải sort, `EXPLAIN` hiện `Using filesort`. Tên này dễ gây hiểu lầm: filesort là thuật toán sort
chung, dùng bộ nhớ tới `sort_buffer_size`; chỉ khi dữ liệu không vừa mới ghi ra file tạm. Filesort 50
dòng không phải vấn đề; filesort 2 triệu dòng để lấy 20 dòng mới là vấn đề. Chương 12 bàn cách xử lý.

### 8.3 Index cho GROUP BY

Cách tổng quát để làm `GROUP BY` là quét các dòng, gom vào bảng tạm rồi tính (thấy `Using temporary` trong
`EXPLAIN`). Nếu có index mà cột `GROUP BY` là leftmost prefix, các dòng cùng nhóm đã nằm liền nhau trong
index, MySQL chỉ cần đọc theo thứ tự và tính từng nhóm:

```sql
SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id;
-- 10000 dòng, mỗi dòng COUNT(*) = 20
-- output minh hoạ EXPLAIN: type = index, key = idx_customer hoặc idx_cust_created, Extra = Using index
```

Tài liệu "GROUP BY Optimization" mô tả thêm *Loose Index Scan*: với một số dạng truy vấn, MySQL chỉ đọc
**một phần** các entry, nhảy từ nhóm này sang nhóm kế. Điều kiện chính: truy vấn trên một bảng; các cột
`GROUP BY` là leftmost prefix của index; nếu có hàm tổng hợp thì chỉ là `MIN()`/`MAX()` trên cùng một cột,
và cột đó nằm trong index ngay sau các cột `GROUP BY`. `EXPLAIN` hiện `Using index for group-by`.

```sql
SELECT customer_id, MAX(created_at) FROM orders GROUP BY customer_id;
-- với idx_cust_created: mỗi khách chỉ cần đọc entry cuối nhóm
-- output minh hoạ EXPLAIN: type = range, key = idx_cust_created, Extra = Using index for group-by
```

⚠️ Từ MySQL 8.0, `GROUP BY` không còn ngầm sắp xếp kết quả (chương 08). Cần thứ tự thì luôn viết
`ORDER BY`.

### 8.4 MIN() và MAX()

Tài liệu "How MySQL Uses Indexes": tìm `MIN()`/`MAX()` của cột có index được tối ưu nếu mọi cột đứng
trước nó trong index bị cố định bằng `=` hằng số. Khi đó MySQL chỉ cần một lần đi xuống cây tới đầu
hoặc cuối đoạn:

```sql
SELECT MAX(created_at) FROM orders WHERE customer_id = 7;
-- 2026-06-12 19:04:00
-- output minh hoạ EXPLAIN: Extra = Select tables optimized away (giá trị tìm được ngay lúc tối ưu)
```

### 8.5 Descending index

Mặc định mỗi cột trong index sắp tăng dần (`ASC`). Từ MySQL 8.0 có thể khai `DESC` cho từng cột; tài
liệu "Descending Indexes" ghi `DESC` không còn bị bỏ qua mà làm giá trị được lưu theo thứ tự giảm dần.

Với index một cột, đi ngược (`Backward index scan`) đã đủ cho `ORDER BY ... DESC`. Descending index cần
thiết khi `ORDER BY` **trộn chiều**:

```sql
CREATE TABLE t (
  c1 INT, c2 INT,
  INDEX idx1 (c1 ASC,  c2 ASC),
  INDEX idx2 (c1 ASC,  c2 DESC),
  INDEX idx3 (c1 DESC, c2 ASC),
  INDEX idx4 (c1 DESC, c2 DESC)
);
-- ORDER BY c1 ASC,  c2 DESC  -> dùng idx2 không cần sort
-- ORDER BY c1 DESC, c2 ASC   -> dùng idx3
```

(Ví dụ lấy từ tài liệu; thực tế chỉ tạo index cho tổ hợp bạn cần.) Đi ngược `idx1` cho ra
`c1 DESC, c2 DESC`, không bao giờ cho `c1 ASC, c2 DESC`, nên trước 8.0 câu trộn chiều luôn phải sort.

Giới hạn theo tài liệu: chỉ InnoDB; chỉ cho `BTREE`, không cho `HASH`, `FULLTEXT`, `SPATIAL`;
index có cột `DESC` không được dùng cho tối ưu `MIN()`/`MAX()` khi truy vấn không có `GROUP BY`.

## 9. Khi có index mà không được dùng

Nguyên tắc chung: index sắp theo **giá trị gốc của cột**. Điều kiện nào buộc MySQL biến đổi giá trị
cột trước khi so sánh thì MySQL không biết đi xuống cây theo hướng nào. Chuẩn bị:

```sql
CREATE INDEX idx_created ON orders (created_at);
CREATE INDEX idx_phone   ON customers (phone);
CREATE INDEX idx_status  ON orders (status);
```

### 9.1 Bọc hàm quanh cột

```sql
-- Không dùng được idx_created: cây sắp theo created_at, không có sẵn thứ tự của DATE(created_at)
SELECT COUNT(*) FROM orders WHERE DATE(created_at) = '2026-01-24';            -- 360

-- Viết lại thành khoảng trên chính cột: dùng được idx_created
SELECT COUNT(*) FROM orders
WHERE created_at >= '2026-01-24' AND created_at < '2026-01-25';               -- 360
```

Mỗi ngày có 1440 / 4 = 360 đơn. Hai câu cho cùng kết quả, nhưng `EXPLAIN` câu đầu là `type = index`
hoặc `ALL` (đọc hết), câu sau là `type = range`. Dùng khoảng nửa mở `[a, b)` để không phải lo phần giây
lẻ cuối ngày. Tương tự với `YEAR(created_at) = 2026`, `LOWER(email) = ?`, `SUBSTRING(phone, 1, 4) = ?`.
Khi bắt buộc phải lọc theo biểu thức thì dùng functional index (mục 10.1).

### 9.2 Phép tính trên cột

`WHERE total * 1.1 > 100` không dùng được index trên `total`; viết thành `WHERE total > 100 / 1.1` thì
được. Quy tắc: để cột **đứng một mình** ở một vế.

### 9.3 LIKE bắt đầu bằng ký tự đại diện

Tài liệu "Comparison of B-Tree and Hash Indexes": index dùng được cho `LIKE` khi đối số là chuỗi hằng
**không bắt đầu bằng ký tự đại diện**. `LIKE 'Patrick%'` được xử lý như khoảng
`'Patrick' <= key < 'Patricl'`; còn `LIKE '%Patrick%'` và `LIKE other_col` thì không dùng index.

```sql
SELECT COUNT(*) FROM customers WHERE email LIKE 'user42%';          -- 111, dùng uk_email (range)
-- (user42, user420..user429, user4200..user4299: 1 + 10 + 100)
SELECT COUNT(*) FROM customers WHERE email LIKE '%42@example.com';  -- không seek được
```

Tìm "chứa chuỗi ở giữa" trên văn bản cần full-text index (mục 12) hoặc công cụ tìm kiếm riêng.

### 9.4 Ép kiểu ngầm

Cột `phone` là chuỗi. So sánh nó với một **số**:

```sql
SELECT id, phone FROM customers WHERE phone = 900000042;     -- quên dấu nháy
-- +----+------------+
-- | id | phone      |
-- +----+------------+
-- | 42 | 0900000042 |
-- +----+------------+
-- EXPLAIN (minh hoạ): type = ALL, possible_keys = idx_phone, key = NULL

SELECT id, phone FROM customers WHERE phone = '0900000042';  -- đúng kiểu: type = ref, key = idx_phone
```

Kết quả giống nhau, nhưng câu đầu quét cả bảng. Khi so chuỗi với số, MySQL chuyển cả hai về số để so
(chương 06), tức phải chuyển `phone` của **từng dòng**. Tài liệu "How MySQL Uses Indexes" giải thích:
giá trị số `1` có thể bằng nhiều chuỗi khác nhau (`'1'`, `' 1'`, `'00001'`, `'01.e1'`), nên không dùng
được index trên cột chuỗi. Chiều ngược lại (cột số so với hằng chuỗi `WHERE id = '42'`) vẫn dùng được
index, vì chỉ hằng số bị chuyển.

⚠️ Bẫy này hay gặp ở code ứng dụng: tham số truyền vào dạng số nguyên cho một cột `VARCHAR` (mã số,
số điện thoại). Cũng xảy ra khi JOIN hai cột khác kiểu hoặc khác charset (mục 6.6).

### 9.5 OR giữa các cột khác nhau

Tài liệu nêu `WHERE index_part1 = 1 OR index_part2 = 10` không dùng được index `(index_part1,
index_part2)`: không có một đoạn lá nào chứa tất cả các dòng thoả. MySQL có thể dùng *index merge* nếu
có index riêng trên từng cột (chương 12), hoặc bạn viết lại bằng `UNION` / `UNION ALL` (chương 09).

### 9.6 Selectivity thấp: optimizer bỏ index là đúng

```sql
EXPLAIN SELECT * FROM orders WHERE status = 'paid';
-- output minh hoạ: type = ALL, possible_keys = idx_status, key = NULL     (66.600 dòng khớp)
EXPLAIN SELECT * FROM orders WHERE status = 'pending';
-- output minh hoạ: type = ref, key = idx_status, rows khoảng 200          (200 dòng khớp)
```

*Selectivity* là tỉ lệ dòng khớp một điều kiện. `status = 'paid'` khớp 66.600 / 200.000 (một phần ba
bảng). Nhớ ba bước ở mục 3.6: mỗi entry khớp là một lookup ở vị trí ngẫu nhiên trong clustered index.
66.600 lookup ngẫu nhiên đắt hơn đọc tuần tự cả bảng. Tài liệu MySQL: khi optimizer ước lượng dùng index
phải truy cập một tỉ lệ rất lớn các dòng, quét bảng thường nhanh hơn vì cần ít lần seek hơn; nhưng nếu
câu có `LIMIT` lấy vài dòng thì MySQL vẫn dùng index. Không có ngưỡng cố định; optimizer tính chi phí
từ thống kê (chương 12).

Ví dụ trên còn cho thấy: cột chỉ có 4 giá trị (cardinality thấp) **vẫn đáng index** nếu dữ liệu lệch và
bạn chỉ truy vấn phần hiếm (`pending` chiếm 0,1%). Và câu covering như `SELECT COUNT(*) FROM orders
WHERE status = 'paid'` vẫn có thể dùng `idx_status`, vì không cần lookup.

⚠️ Bẫy hay gặp: thử trên máy dev vài nghìn dòng thì full scan không lộ ra. Luôn xem `EXPLAIN`, đừng chỉ
nhìn thời gian chạy trên dữ liệu nhỏ.

Tóm tắt mục 9:

| Viết thế này | Index trên cột | Sửa thành |
|---|---|---|
| `DATE(created_at) = '2026-01-24'` | Không dùng | `created_at >= '2026-01-24' AND created_at < '2026-01-25'` |
| `total * 1.1 > 100` | Không dùng | `total > 100 / 1.1` |
| `email LIKE '%abc'` | Không seek | Full-text, hoặc thiết kế lại |
| `phone = 900000042` (cột chuỗi) | Không dùng | `phone = '0900000042'` |
| `a = 1 OR b = 2` | Không dùng một index `(a, b)` | Index riêng (index merge) hoặc `UNION` |
| Điều kiện khớp phần lớn bảng | Optimizer bỏ qua | Đúng như vậy; cân nhắc covering |

## 10. Các loại index đặc biệt

### 10.1 Functional index: index trên biểu thức

Từ MySQL 8.0.13, phần tử của index có thể là một **biểu thức** (tài liệu gọi là *functional key
part*). Cú pháp bắt buộc bọc biểu thức trong **thêm một cặp ngoặc**:

```sql
CREATE INDEX idx_created_date ON orders ((DATE(created_at)));

SELECT COUNT(*) FROM orders WHERE DATE(created_at) = '2026-01-24';   -- 360, giờ dùng được idx_created_date
```

Theo tài liệu `CREATE INDEX`:

- Functional index được hiện thực bằng một *virtual generated column* ẩn (chương 04): cột ảo không tốn
  chỗ, còn index thì tốn như mọi index.
- Câu truy vấn phải viết **đúng biểu thức** đã khai báo. Ví dụ trong tài liệu: index trên
  `SUBSTRING(col1, 1, 10)` không được dùng cho `WHERE SUBSTRING(col1, 1, 9) = ...`.
- Không được chỉ là tên cột trần (`INDEX ((col1))` báo lỗi); không chứa subquery, tham số, biến, stored
  function; không dùng trong primary key hay foreign key; được phép `UNIQUE`.
- Mỗi functional key part tính vào giới hạn số cột của bảng.

Cách tương đương, tường minh hơn: tự tạo generated column rồi index nó (chương 04). Ưu điểm là cột có
tên, câu truy vấn đọc dễ hiểu.

### 10.2 Prefix index: chỉ index phần đầu chuỗi

Với cột chuỗi dài, có thể chỉ index N ký tự đầu:

```sql
CREATE INDEX idx_note10 ON orders (note(10));
```

Theo tài liệu `CREATE INDEX`:

- Độ dài prefix tính theo **ký tự** với kiểu chuỗi thường (`CHAR`, `VARCHAR`, `TEXT`) và theo **byte**
  với kiểu nhị phân (`BINARY`, `VARBINARY`, `BLOB`).
- Cột `TEXT`/`BLOB` **bắt buộc** phải khai prefix mới index được.
- Giới hạn: InnoDB với row format `DYNAMIC` (mặc định) hoặc `COMPRESSED` cho key tối đa 3072 byte;
  `REDUNDANT`/`COMPACT` là 767 byte (với page 16 KB).
- `UNIQUE` trên prefix nghĩa là giá trị phải khác nhau **trong phạm vi prefix**.

Lợi: index nhỏ hơn nhiều. Giá phải trả:

- Index không chứa đủ giá trị, nên MySQL vẫn phải đọc dòng để so nốt: **không bao giờ covering**, và
  **không dùng được để sort** (mục 8.1).
- Prefix quá ngắn làm nhiều dòng chung prefix, index lọc kém. Cách chọn N: so số giá trị khác nhau của
  prefix với của cả cột, ví dụ
  `SELECT COUNT(DISTINCT LEFT(note, 10)) / COUNT(DISTINCT note) FROM orders;` rồi tăng N tới khi tỉ lệ
  gần 1.

### 10.3 Multi-valued index cho mảng JSON

Không index thẳng được cả một tài liệu JSON. Với một giá trị vô hướng trong JSON, dùng generated
column hoặc functional index. ⚠️ Tài liệu `CREATE INDEX` cảnh báo: `INDEX ((data->>'$.name'))` báo lỗi,
vì `->>` trả về `LONGTEXT` mà functional key part không nhận prefix; phải `CAST(... AS CHAR(30))`, và
khi đó còn bẫy collation: `CAST` trả collation mặc định `utf8mb4_0900_ai_ci`, còn `->>` trả
`utf8mb4_bin`, nên index không được dùng cho `WHERE data->>'$.name' = 'James'` trừ khi thêm
`COLLATE utf8mb4_bin` vào biểu thức index, hoặc câu truy vấn viết nguyên biểu thức `CAST`. Hai cách cho
kết quả khác nhau: bản `_bin` phân biệt hoa thường, bản `_ai_ci` thì không.

Với **mảng** JSON (một dòng chứa nhiều giá trị), MySQL có *multi-valued index*: một dòng sinh ra nhiều
entry, mỗi phần tử một entry. Ví dụ phỏng theo tài liệu (đổi tên bảng cho khỏi trùng):

```sql
CREATE TABLE cust_zip (
  id       BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  custinfo JSON,
  INDEX zips ((CAST(custinfo->'$.zipcode' AS UNSIGNED ARRAY)))
);
INSERT INTO cust_zip (custinfo) VALUES
  ('{"user":"Jack","user_id":37,"zipcode":[94582,94536]}'),
  ('{"user":"Jill","user_id":22,"zipcode":[94568,94507,94582]}'),
  ('{"user":"Bob","user_id":31,"zipcode":[94477,94507]}'),
  ('{"user":"Mary","user_id":72,"zipcode":[94536]}'),
  ('{"user":"Ted","user_id":56,"zipcode":[94507,94582]}');

SELECT id FROM cust_zip WHERE 94507 MEMBER OF (custinfo->'$.zipcode');                      -- 2, 3, 5
SELECT id FROM cust_zip WHERE JSON_CONTAINS(custinfo->'$.zipcode', CAST('[94507,94582]' AS JSON));  -- 2, 5
SELECT id FROM cust_zip WHERE JSON_OVERLAPS(custinfo->'$.zipcode', CAST('[94507,94582]' AS JSON));  -- 1, 2, 3, 5
```

Trong tài liệu, `EXPLAIN` của câu `MEMBER OF` cho `type = ref, key = zips`, hai câu còn lại
`type = range, key = zips`. Optimizer chỉ dùng multi-valued index với `MEMBER OF()`, `JSON_CONTAINS()`,
`JSON_OVERLAPS()`.

Giới hạn theo tài liệu: một multi-valued key part mỗi index; không khai `ASC`/`DESC`; không làm primary
key, không dùng trong foreign key; **không covering và không range scan** (các entry của một dòng nằm
rải rác); mảng rỗng không sinh entry; không tạo online được (dùng `ALGORITHM=COPY`). Nếu phải tra mảng
JSON thường xuyên và phức tạp, đó thường là dấu hiệu nên tách ra bảng con chuẩn hoá (chương 02).

### 10.4 Invisible index

Tài liệu "Invisible Indexes": index *invisible* là index optimizer không dùng, nhưng **vẫn được cập
nhật** khi dữ liệu thay đổi, và unique index invisible **vẫn chặn trùng**. Index mặc định visible.

```sql
ALTER TABLE orders ALTER INDEX idx_status INVISIBLE;
-- Theo dõi slow log, APM đủ lâu (gồm cả job cuối tháng). Có vấn đề thì bật lại ngay:
ALTER TABLE orders ALTER INDEX idx_status VISIBLE;

-- Thử plan "như thể index còn visible" cho riêng một câu:
EXPLAIN SELECT /*+ SET_VAR(optimizer_switch = 'use_invisible_indexes=on') */ *
FROM orders WHERE status = 'pending';
```

Công dụng chính: **thử xoá index một cách an toàn**. Xoá rồi tạo lại index trên bảng lớn tốn nhiều thời
gian; đổi visible/invisible thì nhanh và quay lui được. Ổn định rồi mới `DROP INDEX`.

Không làm invisible được primary key, kể cả primary key ngầm (index `UNIQUE` trên cột `NOT NULL` đóng
vai primary key khi bảng không khai).

## 11. Cái giá của index

### 11.1 Ghi chậm hơn

Mỗi index là một B+tree phải luôn khớp với bảng:

- `INSERT` một dòng: thêm vào clustered index **và** thêm một entry vào mỗi secondary index. Bảng có 6
  secondary index thì một insert là 7 lần ghi vào 7 cây.
- `DELETE`: xoá ở mọi cây.
- `UPDATE`: sửa clustered index; secondary index nào chứa cột bị đổi thì phải xoá entry cũ, thêm entry
  mới (vị trí trong cây thay đổi). Update cột không nằm trong secondary index nào thì không chạm vào
  chúng. Đổi primary key thì chạm vào **mọi** index (mục 4.1).
- Chèn vào giữa một page đầy gây *page split* (mục 4.4).

Bảng nhận rất nhiều ghi mà ít đọc (log, event thô) là nơi mỗi index thừa trả giá đắt nhất.

### 11.2 Tốn đĩa và tốn bộ nhớ

Mỗi index chiếm chỗ trên đĩa, có khi xấp xỉ cả bảng (index nhiều cột, cột chuỗi dài, primary key dài bị
chép vào mỗi entry). Quan trọng hơn: index chỉ nhanh khi các page hay dùng nằm trong buffer pool. Index
thừa chiếm chỗ của dữ liệu nóng, đẩy page khác ra khỏi bộ nhớ.

### 11.3 Optimizer có thêm lựa chọn để chọn sai

Nhiều index na ná nhau làm optimizer phải cân nhắc nhiều phương án hơn, và đôi khi chọn nhầm khi thống
kê lệch. Chương 12 bàn cách phát hiện và sửa.

### 11.4 Index thừa và index trùng

- **Trùng tiền tố**: có `(customer_id, created_at)` rồi thì `(customer_id)` thường thừa, vì leftmost
  prefix đã phục vụ (mục 6.2). Trong chương này, `idx_customer` (mục 5.1) là thừa so với
  `idx_cust_created`. Ngoại lệ hiếm: index ngắn nhỏ hơn hẳn và có câu cần quét toàn bộ nó.
- **Trùng hoàn toàn**: MySQL cho tạo hai index giống hệt nhau (chỉ báo warning với index thường; tài liệu
  ghi index có functional key part thì không có cả warning này).
- **Index không ai dùng**: schema `sys` có sẵn hai view giúp tìm:

```sql
SELECT * FROM sys.schema_unused_indexes    WHERE object_schema = 'ch11';
SELECT table_name, redundant_index_name, dominant_index_name, sql_drop_index
FROM sys.schema_redundant_indexes WHERE table_schema = 'ch11';
```

⚠️ `schema_unused_indexes` dựa trên số liệu Performance Schema tính từ lần khởi động server gần nhất.
Server mới restart hôm qua thì index chỉ dùng cho báo cáo cuối tháng sẽ bị liệt kê là "không dùng". Replica
phục vụ đọc có thể dùng index mà primary không dùng, nên phải kiểm trên mọi node. Trước khi xoá, cho
index invisible một thời gian (mục 10.4).

### 11.5 Khi nào không nên thêm index

- Bảng nhỏ: vài nghìn dòng nằm gọn trong ít page, quét hết còn rẻ.
- Cột hiếm khi xuất hiện trong `WHERE`, `JOIN`, `ORDER BY`, `GROUP BY` của câu truy vấn thật.
- Cột selectivity thấp và phân bố đều (cờ true/false chia đôi), trừ khi câu truy vấn chỉ nhắm phần
  hiếm hoặc index đó covering.
- "Mỗi cột trong `WHERE` một index riêng": thường kém hơn một composite index đúng thứ tự, vì thông thường
  optimizer chỉ dùng một index cho mỗi bảng trong một câu (index merge là ngoại lệ, chương 12).

InnoDB cho tối đa 64 secondary index mỗi bảng (tài liệu "InnoDB Limits"), nhưng nếu bạn tới gần con số
đó thì vấn đề nằm ở thiết kế.

## 12. Full-text index (giới thiệu)

B+tree không giúp được `LIKE '%từ khoá%'`. Bài toán "tìm các bài viết chứa từ X" cần một cấu trúc khác:
*inverted index* (chỉ mục ngược), tức danh sách "từ → các tài liệu chứa từ đó", giống chỉ mục cuối sách.
Tài liệu MySQL ghi full-text index của InnoDB có thiết kế inverted index.

```sql
CREATE TABLE articles (
  id    INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  body  TEXT NOT NULL,
  FULLTEXT INDEX ft_title_body (title, body)
);
INSERT INTO articles (title, body) VALUES
  ('Index trong MySQL',     'B+tree giúp tìm kiếm nhanh'),
  ('Transaction cơ bản',    'ACID và rollback'),
  ('Tối ưu index',          'Composite index và covering index');

-- Natural language mode (mặc định): xếp theo độ liên quan
SELECT id, title, MATCH(title, body) AGAINST ('index') AS score
FROM articles
WHERE MATCH(title, body) AGAINST ('index')
ORDER BY score DESC;

-- Boolean mode: + bắt buộc có, - không được có
SELECT id, title FROM articles
WHERE MATCH(title, body) AGAINST ('+index -covering' IN BOOLEAN MODE);
```

Kết quả mong đợi theo nghĩa: câu đầu trả về bài 1 và 3 (bài 3 chứa "index" nhiều lần hơn nên thường có
điểm cao hơn; con số `score` cụ thể phụ thuộc thuật toán xếp hạng, không tính tay được). Câu boolean trả
về bài 1.

Những điều cần biết trước khi dùng (tài liệu `CREATE INDEX` và "Full-Text Search Functions"):

- Chỉ InnoDB và MyISAM; chỉ cột `CHAR`, `VARCHAR`, `TEXT`; luôn index toàn bộ cột (không có prefix).
- Danh sách cột trong `MATCH(...)` phải khớp đúng một full-text index.
- Có ngưỡng độ dài từ tối thiểu (biến `innodb_ft_min_token_size` với InnoDB) và danh sách *stopword*
  (từ quá phổ biến bị bỏ qua); từ ngắn hơn ngưỡng không tìm được.
- Parser mặc định tách từ theo khoảng trắng và dấu câu. Tiếng Trung, Nhật, Hàn cần parser `ngram`.
- InnoDB thêm một cột ẩn `FTS_DOC_ID` và một bộ bảng phụ cho mỗi bảng có full-text index.

Full-text của MySQL đủ cho tìm kiếm đơn giản. Khi cần tìm kiếm mờ, gợi ý, xếp hạng tuỳ biến, đa ngôn
ngữ, thường dùng hệ riêng như Elasticsearch, OpenSearch, Meilisearch, đồng bộ dữ liệu từ database sang.

## 13. Đối chiếu PostgreSQL

| Chủ đề | MySQL 8.4 (InnoDB) | PostgreSQL 18 |
|---|---|---|
| Lưu bảng | Clustered index theo primary key | *Heap* không sắp xếp; mọi index trỏ tới địa chỉ dòng (*ctid*) |
| Secondary index tìm dòng | Qua primary key, đi xuống cây thứ hai | Nhảy thẳng tới heap theo ctid |
| Covering | Thêm cột vào key | Có `INCLUDE (cột)`: cột chỉ nằm ở lá, không phải key; index-only scan còn phụ thuộc *visibility map* |
| Index trên biểu thức | Functional key part (cặp ngoặc kép) | *Expression index*: `CREATE INDEX ON t ((lower(email)))` |
| Partial index | Không có | Có: `CREATE INDEX ... WHERE status = 'pending'` |
| Tạo index không khoá ghi | Online DDL (chương 20) | `CREATE INDEX CONCURRENTLY` |
| Loại index | B-tree, full-text, spatial (R-tree), multi-valued | B-tree (mặc định), Hash, GiST, SP-GiST, GIN, BRIN |

Vài loại index của PostgreSQL đáng biết tên:

- *Partial index*: chỉ index các dòng thoả một điều kiện. Index nhỏ, ghi rẻ, rất hợp với dữ liệu lệch:

  ```sql
  -- PostgreSQL
  CREATE INDEX orders_pending ON orders (created_at) WHERE status = 'pending';
  CREATE UNIQUE INDEX one_active_sub ON subscriptions (user_id) WHERE active;  -- mỗi user một gói active
  ```

  Planner chỉ dùng khi chứng minh được `WHERE` của câu truy vấn suy ra điều kiện của index. MySQL không
  có partial index.
- *GIN* (Generalized Inverted Index): inverted index cho giá trị chứa nhiều phần tử: `jsonb`, mảng,
  full-text (`tsvector`). Tương đương ý tưởng multi-valued index và full-text index của MySQL, nhưng
  dùng chung một cơ chế.
- *GiST* và *SP-GiST*: khung tổng quát cho dữ liệu hình học, khoảng (range type), tìm láng giềng gần
  nhất.
- *BRIN* (Block Range Index): chỉ lưu tóm tắt (ví dụ min/max) cho từng dải page liên tiếp. Rất nhỏ, hợp
  với bảng cực lớn mà giá trị tăng theo thứ tự vật lý, như `created_at` của bảng log chỉ insert.
- *Hash*: chỉ cho `=`.

Ngoài ra, ở PostgreSQL `UPDATE` ghi một bản dòng mới ở vị trí khác, nên về nguyên tắc mọi index phải
thêm entry trỏ tới bản mới, trừ trường hợp *HOT update* (không đổi cột được index và page còn chỗ).
Chương 25 so sánh kỹ hơn.

## 14. Ghép lại: thiết kế index từ câu truy vấn

Quy trình đúng là bắt đầu từ **danh sách câu truy vấn thật**, không bắt đầu từ danh sách cột. Ví dụ với
bảng `orders`:

| # | Câu truy vấn | Ghi chú |
|---|---|---|
| Q1 | `WHERE customer_id = ? ORDER BY created_at DESC LIMIT 20` | Trang "đơn của tôi" |
| Q2 | `WHERE customer_id = ? AND status = ? ORDER BY created_at DESC LIMIT 20` | Lọc theo trạng thái |
| Q3 | `SELECT COUNT(*) ... WHERE customer_id = ? AND status = ?` | Số trên badge |
| Q4 | `WHERE status = 'pending' AND created_at < NOW() - INTERVAL 1 DAY` | Job huỷ đơn treo |

Lập luận:

1. Q2: hai cột `=` rồi sort theo `created_at` → `(customer_id, status, created_at)`. Index này phục vụ
   luôn Q3 dạng covering.
2. Q1 thiếu `status`, nên với index trên chỉ thu hẹp theo `customer_id` rồi phải sort mọi đơn của khách.
   Mỗi khách vài chục đơn thì chấp nhận được; có khách hàng chục nghìn đơn thì thêm
   `(customer_id, created_at)`.
3. Q4: `status` là `=`, `created_at` là range → `(status, created_at)`. Dữ liệu lệch nên đoạn quét nhỏ.
4. Không còn cần `(customer_id)` riêng, `(status)` riêng hay `(created_at)` riêng, trừ khi có câu khác
   cần.

Sau đó: tạo index, chạy `EXPLAIN` từng câu để kiểm dự đoán (chương 12), và theo dõi index không dùng
theo thời gian (mục 11.4).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Index mọi cột, mỗi cột một index | Optimizer thường chỉ dùng một index mỗi bảng; ghi chậm, tốn bộ nhớ | Composite index theo câu truy vấn thật (mục 6, 14) |
| Composite index sai thứ tự cột | Thiếu cột đầu thì không seek được; cột range đứng trước làm cột sau thành filter | Cột `=` trước, cột range/sort sau (mục 6.3) |
| `WHERE DATE(col) = ...`, `YEAR(col) = ...` | Hàm quanh cột, index sắp theo giá trị gốc | Viết thành khoảng nửa mở, hoặc functional index (mục 9.1, 10.1) |
| So cột chuỗi với số (`phone = 0912...`) | Ép kiểu ngầm từng dòng | Truyền tham số đúng kiểu (mục 9.4) |
| `LIKE '%x%'` trên bảng lớn | Không biết bắt đầu từ đâu trong cây | Full-text hoặc search engine (mục 9.3, 12) |
| Thắc mắc "có index sao vẫn full scan" | Điều kiện khớp phần lớn bảng | Đúng là rẻ hơn; xem selectivity, cân nhắc covering (mục 9.6) |
| Primary key dài hoặc ngẫu nhiên (UUIDv4 dạng `CHAR(36)`) | Chép vào mọi secondary index, insert rải rác gây page split | Primary key ngắn, tăng dần (mục 4.4) |
| Nhầm `Using index` với `Using index condition` | Một cái là covering, một cái là ICP | Bảng ở mục 7.2 |
| Giữ cả `(a)` lẫn `(a, b)` | `(a)` thừa theo leftmost prefix | Xoá sau khi cho invisible và theo dõi (mục 10.4, 11.4) |
| Drop index trực tiếp trên production | Câu đang dựa vào nó đột ngột full scan | Invisible trước, theo dõi đủ lâu rồi mới drop |
| Functional index không được dùng | Câu truy vấn viết biểu thức khác (hoặc khác collation) | Viết đúng nguyên biểu thức như lúc tạo index (mục 10.1, 10.3) |
| Tin `Cardinality` là con số chính xác | Là ước lượng từ lấy mẫu | `ANALYZE TABLE` sau thay đổi lớn (chương 12) |
| Đo hiệu năng trên dữ liệu dev nhỏ | Full scan không lộ ra | Dữ liệu cỡ thật và `EXPLAIN` |

## Tóm tắt chương

- Không có index, tìm dòng là full table scan: chi phí tỉ lệ với kích thước bảng.
- Index là bản sao có sắp xếp của một vài cột, cấu trúc B+tree: page 16 KB, lá nối hai chiều, cây cân
  bằng và rất thấp (thường 2 tới 4 tầng).
- Một lần tra có ba bước: đi xuống cây (rẻ, có giới hạn), đi dọc lá và lấy dòng (không giới hạn, nơi
  gây chậm).
- InnoDB: bảng là clustered index sắp theo primary key; secondary index chứa key cộng primary key và
  phải lookup về clustered index. Primary key nên ngắn, tăng dần, không đổi.
- Composite index chỉ seek được theo leftmost prefix; cột `=` trước, cột range sau; đọc `key_len` để
  biết dùng tới cột nào.
- Covering index bỏ được lookup (`Using index`); ICP lọc sớm trên index (`Using index condition`).
- Index thay được sort và gom nhóm khi thứ tự index khớp `ORDER BY`/`GROUP BY` sau các cột `=`.
- Hàm hoặc phép tính quanh cột, `LIKE '%x'`, ép kiểu ngầm, `OR` giữa các cột, selectivity thấp làm index
  không được dùng.
- Functional, prefix, multi-valued, descending, invisible, full-text index giải các bài toán riêng, mỗi
  loại có giới hạn riêng.
- Index làm đọc nhanh và ghi chậm, tốn đĩa và buffer pool: thiết kế từ câu truy vấn thật, dọn index thừa.

## Câu hỏi tự kiểm tra

1. Vì sao full table scan trên bảng 10.000 dòng không thấy chậm, nhưng là vấn đề nghiêm trọng trên bảng
   100 triệu dòng? (mục 2.1)
2. Vì sao B+tree có fan-out lớn lại phù hợp với đĩa hơn cây nhị phân? Thêm một tầng cây thì sức chứa
   tăng khoảng bao nhiêu lần? (mục 3.5)
3. Ba bước của một lần tra index là gì? Bước nào có giới hạn trên? (mục 3.6)
4. Trong InnoDB, entry của secondary index chứa gì? Vì sao không chứa địa chỉ vật lý của dòng? (mục 4.2)
5. Với index `(a, b, c)`, các điều kiện sau thu hẹp được theo mấy cột: `a = 1 AND c = 3`;
   `b = 2`; `a = 1 AND b > 5 AND c = 3`? (mục 6.2, 6.3)
6. `SELECT id FROM t WHERE a = ?` có covering với index `(a)` trên InnoDB không? Vì sao? (mục 4.2, 7.1)
7. Vì sao `WHERE customer_id IN (1, 2) ORDER BY created_at` vẫn phải sort dù có index
   `(customer_id, created_at)`? (mục 8.2)
8. Cột `VARCHAR` có index, câu `WHERE code = 123` quét cả bảng. Giải thích và sửa. (mục 9.4)
9. Optimizer bỏ qua index khi điều kiện khớp 40% bảng: đó là lỗi hay quyết định đúng? Khi nào cột chỉ
   có vài giá trị vẫn đáng index? (mục 9.6)
10. Invisible index dùng để làm gì, và nó có còn được cập nhật khi ghi không? (mục 10.4)

## Bài tập

1. **Đo full scan và index.** Trên dữ liệu mẫu, tăng `orders` lên 2 triệu dòng (sửa CTE). Chạy
   `SELECT COUNT(*) FROM orders WHERE customer_id = 7` trước và sau khi tạo index `(customer_id)`, ghi
   lại thời gian và `EXPLAIN`. Rồi so `SELECT * ... WHERE customer_id = 7` với
   `SELECT id ... WHERE customer_id = 7`: câu nào có `Using index`, vì sao?
2. **Thiết kế index cho màn hình.** Màn hình quản trị cần: (a) tìm khách theo số điện thoại chính xác;
   (b) liệt kê khách theo thành phố, mới nhất trước, 50 dòng mỗi trang; (c) đếm số khách mỗi thành phố.
   Đề xuất bộ index tối thiểu cho `customers`, dự đoán `type`, `key`, `Extra` cho từng câu, rồi chạy
   `EXPLAIN` để kiểm.
3. **Săn index không được dùng.** Viết năm câu truy vấn trên `orders`/`customers`, mỗi câu rơi vào một
   trường hợp ở mục 9 (hàm, phép tính, `LIKE '%'`, ép kiểu, `OR`). Với mỗi câu, xác nhận bằng `EXPLAIN`
   rồi viết lại (hoặc thêm index phù hợp) để index được dùng.
4. **Dọn index.** Liệt kê toàn bộ index đã tạo trong chương này trên `orders`, chỉ ra index nào thừa
   theo leftmost prefix, kiểm bằng `sys.schema_redundant_indexes`, rồi thực hiện quy trình invisible →
   theo dõi → drop cho một index.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [How MySQL Uses Indexes](https://dev.mysql.com/doc/refman/8.4/en/mysql-indexes.html) ·
  [Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html) ·
  [The Physical Structure of an InnoDB Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html) ·
  [CREATE INDEX Statement](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) ·
  [Multiple-Column Indexes](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html) ·
  [Comparison of B-Tree and Hash Indexes](https://dev.mysql.com/doc/refman/8.4/en/index-btree-hash.html) ·
  [Range Optimization](https://dev.mysql.com/doc/refman/8.4/en/range-optimization.html) ·
  [Index Condition Pushdown](https://dev.mysql.com/doc/refman/8.4/en/index-condition-pushdown-optimization.html) ·
  [ORDER BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html) ·
  [GROUP BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/group-by-optimization.html) ·
  [Invisible Indexes](https://dev.mysql.com/doc/refman/8.4/en/invisible-indexes.html) ·
  [Descending Indexes](https://dev.mysql.com/doc/refman/8.4/en/descending-indexes.html) ·
  [InnoDB Full-Text Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-fulltext-index.html) ·
  [InnoDB Limits](https://dev.mysql.com/doc/refman/8.4/en/innodb-limits.html) ·
  [Type Conversion in Expression Evaluation](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html)
- Markus Winand, *Use The Index, Luke*: [Anatomy of an Index](https://use-the-index-luke.com/sql/anatomy) ·
  [Slow Indexes](https://use-the-index-luke.com/sql/anatomy/slow-indexes) ·
  [Access và filter predicate](https://use-the-index-luke.com/sql/where-clause/searching-for-ranges/greater-less-between-tuning-sql-access-filter-predicates) ·
  [Indexed Order By](https://use-the-index-luke.com/sql/sorting-grouping/indexed-order-by)
- Jeremy Cole, [B+Tree index structures in InnoDB](https://blog.jcole.us/2013/01/10/btree-index-structures-in-innodb/)
- PostgreSQL: [Index Types](https://www.postgresql.org/docs/current/indexes-types.html) ·
  [Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html) ·
  [Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)
