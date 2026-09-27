# 03. Database quan hệ và SQL · Kiến thức

> [← Plan ôn tập](../03-database-sql.md) · [Mục lục kiến thức](README.md)
> Bài đọc tổng hợp từ tài liệu gốc ở mục "Đọc" của từng module. Đọc sau khi đã xem plan; tick các
> tiêu chí "Nắm chắc khi" ở file plan.

Trọng tâm là MySQL 8.4 LTS với engine InnoDB, có đối chiếu PostgreSQL 18. Mọi ví dụ SQL viết cho
MySQL 8.4 trừ khi ghi rõ là Postgres. Để chạy thử nhanh không cần cài đặt gì lâu dài:

```sh
# MySQL 8.4 trong Docker, mật khẩu root là "root"
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 mysql:8.4
docker exec -it my84 mysql -uroot -proot
# Postgres 18 để đối chiếu
docker run -d --name pg18 -e POSTGRES_PASSWORD=pg -p 5432:5432 postgres:18
docker exec -it pg18 psql -U postgres
```

Các ví dụ timeline hai session (module 2.5, 2.6, 3.2) cần mở hai terminal cùng chạy lệnh
`docker exec -it my84 mysql -uroot -proot`.

## Mục lục

- Chặng 1: Nền
  - [1.1 SQL viết tay](#11-sql-viết-tay)
  - [1.2 Index cơ bản](#12-index-cơ-bản)
  - [1.3 Transaction cơ bản](#13-transaction-cơ-bản)
  - [1.4 Kiểu dữ liệu và schema cơ bản](#14-kiểu-dữ-liệu-và-schema-cơ-bản)
- Chặng 2: Làm chủ
  - [2.1 InnoDB lưu dữ liệu thế nào](#21-innodb-lưu-dữ-liệu-thế-nào)
  - [2.2 Index nâng cao](#22-index-nâng-cao)
  - [2.3 Đọc EXPLAIN và xử lý query chậm](#23-đọc-explain-và-xử-lý-query-chậm)
  - [2.4 SQL nâng cao](#24-sql-nâng-cao)
  - [2.5 Isolation level và anomaly](#25-isolation-level-và-anomaly)
  - [2.6 Lock thực dụng](#26-lock-thực-dụng)
  - [2.7 Tầng PHP: PDO và Laravel](#27-tầng-php-pdo-và-laravel)
  - [2.8 Thiết kế schema nâng cao](#28-thiết-kế-schema-nâng-cao)
- Chặng 3: Senior
  - [3.1 Bên trong InnoDB: log, bộ nhớ, MVCC](#31-bên-trong-innodb-log-bộ-nhớ-mvcc)
  - [3.2 Lock chuyên sâu](#32-lock-chuyên-sâu)
  - [3.3 Thay đổi schema online và migration không downtime](#33-thay-đổi-schema-online-và-migration-không-downtime)
  - [3.4 Replication và failover](#34-replication-và-failover)
  - [3.5 Backup, PITR, RPO/RTO](#35-backup-pitr-rporto)
  - [3.6 Scale: partitioning, sharding, archiving](#36-scale-partitioning-sharding-archiving)
  - [3.7 MySQL so với Postgres](#37-mysql-so-với-postgres)

---

## Chặng 1: Nền

### 1.1 SQL viết tay

Module này trả lời: một câu SQL thực sự được DB hiểu theo thứ tự nào, và vì sao JOIN, GROUP BY,
NULL là ba chỗ làm báo cáo ra số sai mà không hề báo lỗi.

Dữ liệu mẫu dùng cho cả module:

```sql
CREATE DATABASE IF NOT EXISTS learn; USE learn;
CREATE TABLE users  (id BIGINT PRIMARY KEY, name VARCHAR(50));
CREATE TABLE orders (id BIGINT PRIMARY KEY, user_id BIGINT, total DECIMAL(12,2), status VARCHAR(10));
CREATE TABLE order_items (id BIGINT PRIMARY KEY, order_id BIGINT, qty INT);
INSERT INTO users VALUES (1,'An'),(2,'Bình'),(3,'Chi');
INSERT INTO orders VALUES (10,1,100,'paid'),(11,1,50,'pending'),(12,2,70,'paid');
INSERT INTO order_items VALUES (1,10,1),(2,10,2),(3,10,1),(4,12,5);
```

#### Các kiểu JOIN

Hãy nghĩ JOIN như hai bước: (1) ghép mọi dòng bảng trái với mọi dòng bảng phải (tích Descartes),
(2) giữ lại những cặp thoả điều kiện `ON`. Các kiểu JOIN khác nhau ở chỗ xử lý dòng không tìm được
cặp.

| Kiểu | Giữ lại gì | Dòng không có cặp |
|---|---|---|
| `INNER JOIN` | Chỉ các cặp khớp | Bị loại ở cả hai phía |
| `LEFT JOIN` | Mọi dòng bảng trái | Dòng trái không có cặp: cột bảng phải thành NULL |
| `RIGHT JOIN` | Mọi dòng bảng phải | Ngược lại với LEFT |
| `CROSS JOIN` | Mọi cặp, m × n dòng | Không có khái niệm "không khớp" |
| `FULL OUTER JOIN` | Mọi dòng cả hai phía | MySQL không hỗ trợ; Postgres có |

Ví dụ trên dữ liệu mẫu: `users INNER JOIN orders` ra 3 dòng (Chi biến mất vì không có đơn),
`users LEFT JOIN orders` ra 4 dòng (Chi có `o.id = NULL`).

- *Self join*: join bảng với chính nó qua hai alias, ví dụ
  `FROM employees e JOIN employees m ON m.id = e.manager_id` để lấy nhân viên cùng tên quản lý.
- Giả lập `FULL OUTER JOIN` trên MySQL: `LEFT JOIN` hợp với `RIGHT JOIN` bằng `UNION` (UNION khử
  dòng trùng, nên các cặp khớp chỉ xuất hiện một lần).

*Anti-join* là "lấy dòng A không có B tương ứng", ví dụ user chưa có đơn nào. Có ba cách viết
thường gặp, và chỉ một cách có bẫy:

```sql
-- Cách 1: LEFT JOIN rồi lọc NULL ở cột KHÔNG thể NULL của bảng phải (thường là PK)
SELECT u.* FROM users u LEFT JOIN orders o ON o.user_id = u.id WHERE o.id IS NULL;
-- Cách 2: NOT EXISTS. An toàn với NULL, thường là cách nên dùng
SELECT u.* FROM users u WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id);
-- Cách 3: NOT IN. SAI khi orders.user_id có dòng NULL (xem nhóm NULL bên dưới)
SELECT u.* FROM users u WHERE u.id NOT IN (SELECT user_id FROM orders);
```

⚠️ Bẫy 1: điều kiện của bảng phải đặt ở `WHERE` biến LEFT JOIN thành INNER JOIN. Lý do nằm ở
thứ tự thực thi: `ON` chạy lúc ghép, `WHERE` chạy sau khi ghép xong. Dòng của Chi đã được ghép với
NULL, rồi `WHERE o.status = 'paid'` gặp `NULL = 'paid'`, ra UNKNOWN, và dòng bị loại. Quy tắc: điều
kiện lọc bảng bên phải của LEFT JOIN đặt ở `ON`; điều kiện lọc bảng bên trái đặt ở `WHERE`.

```sql
SELECT u.name, o.id FROM users u
LEFT JOIN orders o ON o.user_id = u.id AND o.status = 'paid';   -- An 10, Bình 12, Chi NULL
```

⚠️ Bẫy 2: fan-out (nhân dòng). Đơn 10 có 3 item nên join với `order_items` sinh 3 dòng cho đơn 10:

```sql
-- SAI: đơn 10 (100) bị cộng 3 lần, ra 370 thay vì 170
SELECT SUM(o.total) FROM orders o JOIN order_items i ON i.order_id = o.id;
-- ĐÚNG: gom phía "nhiều" trong subquery trước, rồi mới join 1-1
SELECT SUM(o.total), SUM(x.items)
FROM orders o
JOIN (SELECT order_id, SUM(qty) AS items FROM order_items GROUP BY order_id) x
  ON x.order_id = o.id;
```

Dấu hiệu nhận biết: query có `SUM`/`COUNT` và join qua một quan hệ 1-n. Cách tự kiểm: chạy
`COUNT(*)` và `COUNT(DISTINCT o.id)`, nếu khác nhau thì đang bị nhân dòng. `COUNT(DISTINCT ...)`
sửa được phép đếm nhưng không sửa được `SUM` (hai đơn khác nhau có thể cùng số tiền).

#### Thứ tự thực thi logic

Bạn viết `SELECT` trước, nhưng DB xử lý theo thứ tự logic sau (optimizer được phép làm khác về vật
lý miễn là kết quả như nhau):

```
1. FROM / JOIN / ON     tạo tập dòng
2. WHERE                lọc từng dòng
3. GROUP BY             gom nhóm
4. HAVING               lọc từng nhóm
5. Window function      tính OVER(...)
6. SELECT               tính biểu thức, đặt alias, DISTINCT
7. ORDER BY             sắp xếp (đã thấy alias)
8. LIMIT / OFFSET       cắt
```

Hệ quả trực tiếp:

- `WHERE` không dùng được alias của `SELECT`, vì ở bước 2 alias chưa tồn tại. `ORDER BY` thì dùng
  được. MySQL còn cho `HAVING` và `GROUP BY` dùng alias; đây là mở rộng riêng của MySQL, chuẩn SQL
  và Postgres (với `HAVING`) không cho, nên đừng mang thói quen này sang DB khác.
- `WHERE` không dùng được aggregate (`WHERE COUNT(*) > 1` là lỗi), vì lúc đó chưa có nhóm. Lọc theo
  aggregate phải dùng `HAVING`.
- Lọc được ở `WHERE` thì đừng để tới `HAVING`: `WHERE` loại dòng trước khi gom nên gom ít hơn.
- Window function chạy sau `WHERE` nên không lọc được bằng `WHERE` (module 2.4).

`ONLY_FULL_GROUP_BY`: chế độ này từ chối query mà `SELECT`, `HAVING` hoặc `ORDER BY` nhắc tới cột
không nằm trong `GROUP BY`, không nằm trong aggregate, và không *phụ thuộc hàm* vào cột `GROUP BY`
(phụ thuộc hàm nghĩa là giá trị cột đó được xác định duy nhất, ví dụ `GROUP BY u.id` thì `u.name`
hợp lệ vì `id` là PK). MySQL 8.4 mặc định bật sáu mode: `ONLY_FULL_GROUP_BY`,
`STRICT_TRANS_TABLES`, `NO_ZERO_IN_DATE`, `NO_ZERO_DATE`, `ERROR_FOR_DIVISION_BY_ZERO`,
`NO_ENGINE_SUBSTITUTION`.

```sql
SELECT @@SESSION.sql_mode;
SELECT user_id, status, COUNT(*) FROM orders GROUP BY user_id;   -- lỗi 1055 khi mode bật
SELECT user_id, ANY_VALUE(status), COUNT(*) FROM orders GROUP BY user_id; -- chủ động chấp nhận "giá trị bất kỳ"
```

⚠️ Nhiều project cũ (và một số cấu hình framework) tắt mode này để hết lỗi. Khi tắt, MySQL trả về
giá trị của một dòng bất kỳ trong nhóm, không tất định, và bug chỉ lộ ra khi dữ liệu thay đổi.

Strict mode (`STRICT_TRANS_TABLES`) cũng liên quan tới tính đúng: với bảng InnoDB, giá trị sai
kiểu hoặc tràn (`INSERT ... VALUES ('abc')` vào cột `INT`) làm câu lệnh lỗi và rollback. Khi tắt
strict, MySQL âm thầm lưu `0` hoặc giá trị gần nhất kèm một warning mà hầu như không ai đọc.

#### Subquery và UNION

- Subquery vô hướng (*scalar subquery*) trả về một giá trị: `SELECT name, (SELECT COUNT(*) FROM
  orders o WHERE o.user_id = u.id) AS n FROM users u`.
- *Correlated subquery* là subquery tham chiếu cột của câu ngoài (như `u.id` ở trên). Về logic nó
  chạy lại cho mỗi dòng ngoài; thực tế optimizer MySQL 8 thường chuyển `IN`/`EXISTS` thành
  *semijoin* (join chỉ lấy dòng bên trái một lần) hoặc *antijoin*, nên tốc độ gần như viết JOIN tay.
- Subquery trong `FROM` gọi là *derived table*; phải có alias.
- `IN` so với `EXISTS`: ở MySQL 8 hiệu năng thường tương đương. Khác biệt đáng nhớ là ngữ nghĩa với
  NULL khi phủ định: `NOT EXISTS` chỉ trả TRUE/FALSE, còn `NOT IN` có thể trả UNKNOWN.
- `UNION` khử trùng nên phải sort hoặc hash toàn bộ kết quả; `UNION ALL` nối thẳng. Mặc định hãy
  viết `UNION ALL`, chỉ dùng `UNION` khi thật sự cần khử trùng.

#### NULL

NULL nghĩa là "không biết" hoặc "không có". SQL dùng *logic ba giá trị* (three-valued logic):
TRUE, FALSE, UNKNOWN. Mọi phép so sánh với NULL (`=`, `<>`, `<`...) cho ra UNKNOWN, kể cả
`NULL = NULL`, vì hai cái "không biết" không chắc bằng nhau.

| Biểu thức | Kết quả | Ghi chú |
|---|---|---|
| `NULL = NULL` | UNKNOWN (MySQL in ra `NULL`) | Dùng `IS NULL` |
| `NULL <=> NULL` | 1 | Toán tử "so sánh an toàn NULL" của MySQL; chuẩn SQL là `IS NOT DISTINCT FROM` (Postgres có) |
| `TRUE AND UNKNOWN` | UNKNOWN | |
| `FALSE AND UNKNOWN` | FALSE | Kết quả đã chắc chắn bất kể vế kia |
| `TRUE OR UNKNOWN` | TRUE | Tương tự |
| `NOT UNKNOWN` | UNKNOWN | Phủ định không "cứu" được |
| `3 NOT IN (1, NULL)` | UNKNOWN | Bằng `3<>1 AND 3<>NULL` = `TRUE AND UNKNOWN` |
| `1 NOT IN (1, NULL)` | FALSE | |

`WHERE`, `HAVING`, `ON` chỉ giữ dòng có kết quả TRUE, nên UNKNOWN bị đối xử như FALSE. Ngược lại,
ràng buộc `CHECK` chỉ từ chối FALSE: `CHECK (a + b <= 10)` vẫn cho insert khi `a` là NULL.

⚠️ Vì `x NOT IN (..., NULL)` không bao giờ TRUE, chỉ cần subquery trả về một NULL là `NOT IN
(subquery)` ra tập rỗng. Thử trên dữ liệu mẫu:

```sql
INSERT INTO orders VALUES (13, NULL, 5, 'paid');           -- một đơn không gắn user
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM orders);           -- rỗng!
SELECT * FROM users u WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.user_id = u.id); -- Chi
DELETE FROM orders WHERE id = 13;
```

Aggregate và NULL:

- `COUNT(*)` đếm dòng; `COUNT(col)` bỏ qua dòng có `col` NULL. Vì vậy `COUNT(o.id)` sau LEFT JOIN
  đếm đúng số đơn (user không có đơn ra 0), còn `COUNT(*)` ra 1.
- `SUM`, `AVG`, `MIN`, `MAX` bỏ qua NULL. `AVG` chia cho số giá trị khác NULL, không phải số dòng.
- `SUM` trên tập rỗng là NULL, không phải 0. Viết `COALESCE(SUM(total), 0)` khi hiển thị hoặc
  cộng tiếp.
- `GROUP BY` và `DISTINCT` gom mọi NULL vào một nhóm; unique index thì coi các NULL là khác nhau
  (điểm này quay lại ở module 2.8).

**Tóm tắt nhanh**
- Điều kiện của bảng phải trong LEFT JOIN đặt ở `ON`; đặt ở `WHERE` là thành INNER JOIN.
- Join 1-n rồi `SUM` là nhân dòng; gom phía nhiều trước rồi mới join.
- Thứ tự logic: FROM, WHERE, GROUP BY, HAVING, window, SELECT, ORDER BY, LIMIT. Từ đó suy ra alias
  dùng được ở đâu.
- Mọi so sánh với NULL là UNKNOWN; `NOT IN` gặp NULL thì rỗng, dùng `NOT EXISTS`.
- `ONLY_FULL_GROUP_BY` và strict mode là lưới an toàn, đừng tắt.

**Nguồn**: [MySQL: Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) ·
[modern-sql: Three-valued logic](https://modern-sql.com/concept/three-valued-logic) ·
[modern-sql.com](https://modern-sql.com/) · [SQLBolt](https://sqlbolt.com/)


---

### 1.2 Index cơ bản

Module này trả lời: index thực chất là cấu trúc gì, vì sao nó làm query nhanh hơn hàng nghìn lần,
và vì sao có index mà DB vẫn không dùng.

#### Index là gì

Không có index, câu `SELECT * FROM users WHERE email = 'a@x.com'` chỉ có một cách: đọc từng dòng
của bảng và so sánh. Cách này gọi là *full table scan*, chi phí tỉ lệ với số dòng: bảng 10 triệu
dòng thì đọc 10 triệu dòng, dù chỉ có một dòng khớp.

Index là một cấu trúc dữ liệu riêng, chứa bản sao giá trị của một hoặc vài cột, **luôn được giữ ở
trạng thái đã sắp xếp**, và mỗi entry có đường dẫn về dòng đầy đủ. Vì đã sắp xếp nên tìm kiếm được
như tra từ điển: mở giữa, thấy chữ cần tìm đứng trước thì lật về trái, không cần đọc từng trang.

Khó khăn thật sự không nằm ở việc tìm, mà ở việc **giữ thứ tự khi dữ liệu liên tục thay đổi**. Một
mảng đã sắp xếp tìm rất nhanh, nhưng chèn một phần tử vào giữa phải dời mọi phần tử phía sau. DB
giải bài toán này bằng hai cấu trúc kết hợp: danh sách liên kết hai chiều giữa các node lá, và một
cây tìm kiếm cân bằng phía trên (Use The Index, Luke nói hai cấu trúc này giải thích phần lớn đặc tính hiệu năng của DB).

Index không miễn phí. Ba cái giá:

1. **Ghi chậm hơn**: mỗi `INSERT`/`DELETE` phải thêm/xoá entry ở mọi index của bảng; `UPDATE` một
   cột có index phải xoá entry cũ, thêm entry mới. Với InnoDB, bảng có 8 secondary index thì một insert
   là 9 lần ghi vào 9 cây (thêm clustered index chứa chính bảng).
2. **Tốn đĩa**: mỗi index là một cây riêng, có khi lớn ngang bảng.
3. **Tốn RAM**: index chỉ nhanh khi các page hay dùng nằm trong buffer pool (module 3.1). Index thừa
   chiếm chỗ của dữ liệu nóng, đẩy thứ khác ra khỏi RAM.

Ngoài ra còn một cái giá ẩn: optimizer có nhiều lựa chọn hơn để cân nhắc, và đôi khi chọn sai.

#### Vì sao là B+tree

DB không đọc đĩa theo dòng mà theo khối cố định gọi là *page* (InnoDB mặc định 16 KB, cấu hình bằng
`innodb_page_size` lúc khởi tạo). Đọc 1 byte hay 16 KB tốn gần như cùng một lần I/O, nên cấu trúc
tốt là cấu trúc **đọc ít page nhất**. B+tree được thiết kế cho đúng mục tiêu đó.

Cấu trúc:

- *Node lá* (leaf) chứa các entry của index theo thứ tự: giá trị key và đường dẫn tới dòng. Các lá
  nối với nhau thành danh sách liên kết hai chiều, nên có thể đi tiến hoặc lùi.
- *Node nhánh* (branch) và *node gốc* (root) chỉ chứa key phân cách và con trỏ xuống tầng dưới. Mỗi
  entry của node nhánh cho biết khoảng giá trị của một node con.
- Cây *cân bằng*: mọi lá cách gốc cùng một số tầng, nên mọi lần tìm tốn cùng một số bước.

```
                        [ root: 40 | 80 ]
                  /            |             \
        [ 10 | 25 ]       [ 50 | 65 ]        [ 90 | 120 ]        <- branch
        /    |    \        /   |   \          /    |    \
     [1..9][10..24][25..39][40..49][50..64][65..79][80..89]...   <- leaf
        <->   <->     <->    <->     <->     <->                  (lá nối hai chiều)

Range query "WHERE k BETWEEN 45 AND 70":
  1. root: 45 nằm giữa 40 và 80  -> xuống nhánh giữa
  2. branch: 45 < 50             -> xuống lá [40..49]
  3. lá: tìm tới 45, đọc tới hết lá, đi sang lá kế [50..64], rồi [65..79], dừng khi gặp > 70
```

Vì sao cây rất thấp: mỗi node là một page 16 KB. Node nhánh chỉ chứa key và con trỏ nên chứa được
khoảng hơn một nghìn entry với key `BIGINT` (ước lượng thô; con số thật tuỳ độ dài key và overhead
của record). Nếu mỗi lá chứa khoảng 100 dòng thì:

| Số tầng | Số dòng tối đa (ước lượng) |
|---|---|
| 2 | ~1.000 × 100 = 100 nghìn |
| 3 | ~1.000² × 100 = 100 triệu |
| 4 | ~1.000³ × 100 = 100 tỉ |

Số tầng tăng theo log của số dòng: dữ liệu gấp nghìn lần chỉ thêm một tầng. Use The Index, Luke ghi
nhận index thực tế với hàng triệu dòng thường sâu 4 đến 5 tầng, hiếm khi quá 6. Các tầng trên cùng
được truy cập liên tục nên gần như luôn nằm trong RAM; nhờ vậy một lần tra thực tế chỉ tốn rất ít
lần đọc đĩa.

So với các cấu trúc khác:

| Cấu trúc | Tra `=` | Range, `ORDER BY`, prefix | Vấn đề |
|---|---|---|---|
| Binary search tree | log₂(n) bước | Được | Mỗi node 1 key: 1 tỉ dòng cần khoảng 30 tầng, mỗi tầng là một lần đọc page |
| Hash index | O(1) | Không | Hash làm mất thứ tự, nên không làm được `>`, `BETWEEN`, `LIKE 'abc%'`, sort |
| B+tree | log_fanout(n), fanout hàng trăm tới hơn nghìn | Được, đi dọc lá | Ghi phải giữ cây cân bằng (tách page) |

Phân biệt B-tree và B+tree: B-tree cổ điển lưu dữ liệu ở cả node nhánh; B+tree chỉ lưu dữ liệu ở
lá, còn node nhánh chỉ để định hướng. Nhờ vậy node nhánh chứa được nhiều key hơn (cây thấp hơn) và
range scan chỉ cần đi dọc tầng lá. Tài liệu MySQL thường viết "B-tree" nhưng cấu trúc InnoDB thực tế
là B+tree.

Một lần tra index có ba bước, và đây là chỗ nhiều người hiểu sai "có index là nhanh":

1. **Đi xuống cây** từ gốc tới lá: số bước bị chặn bởi độ sâu cây, luôn rẻ.
2. **Đi dọc chuỗi lá** để lấy mọi entry khớp: không có giới hạn trên, khớp 1 triệu entry là đọc
   1 triệu entry.
3. **Lấy dòng đầy đủ** từ bảng cho mỗi entry khớp: mỗi entry có thể là một lần đọc ở vị trí ngẫu
   nhiên.

Bước 2 và 3 là lý do một index lookup chậm. Use The Index, Luke gọi niềm tin "index chậm vì cây bị
mất cân bằng, rebuild là hết" là một huyền thoại: B+tree luôn cân bằng, chậm là do quét quá nhiều lá
và nhảy về bảng quá nhiều lần.

#### Composite index và leftmost prefix

Index nhiều cột (*composite index*, hay *concatenated index*) `(a, b, c)` là một cây duy nhất, entry
được sắp theo `a`; các entry cùng `a` sắp theo `b`; cùng `a, b` thì sắp theo `c`. Giống danh bạ điện
thoại sắp theo họ, rồi tên đệm, rồi tên. MySQL cho tối đa 16 cột trong một index.

```
index (last_name, first_name):
  (Le, An) (Le, Binh) (Le, Chi) (Nguyen, An) (Nguyen, Duc) (Tran, An) (Tran, Hoa)
  ^ sắp theo last_name trước    ^ trong cùng Nguyen thì sắp theo first_name
  Các entry có first_name = 'An' nằm rải rác ở ba chỗ -> không tìm nhanh theo first_name được
```

Vì vậy index chỉ "tra được" (seek, tức đi thẳng xuống cây tới đúng chỗ) khi điều kiện dùng một
*leftmost prefix* (tiền tố bên trái) của danh sách cột:

| Điều kiện trên index `(a, b, c)` | Seek được? | Dùng mấy cột để thu hẹp |
|---|---|---|
| `a = 1` | Có | 1 |
| `a = 1 AND b = 2` | Có | 2 |
| `a = 1 AND b = 2 AND c = 3` | Có | 3 |
| `b = 2 AND a = 1` | Có (thứ tự viết trong WHERE không quan trọng) | 2 |
| `a = 1 AND c = 3` | Có, nhưng chỉ thu hẹp theo `a`; `c` lọc sau | 1 |
| `b = 2` hoặc `b = 2 AND c = 3` | Không (thiếu `a`) | 0 |
| `a = 1 OR b = 2` | Không dùng được index này cho cả điều kiện | 0 |
| `a = 1 AND b > 5 AND c = 3` | Có, `c` không thu hẹp được sau range trên `b` | 2 |

Ví dụ trong tài liệu MySQL với `INDEX name (last_name, first_name)`: `WHERE last_name='Jones' AND
first_name >= 'M' AND first_name < 'N'` dùng được index, còn `WHERE first_name='John'` và `WHERE
last_name='Jones' OR first_name='John'` thì không.

Hệ quả thiết kế: một index `(a, b)` phục vụ được cả query lọc theo `a` và query lọc theo `a, b`, nên
thay được index `(a)` riêng. Chọn thứ tự cột là chọn xem index phục vụ được những tổ hợp điều kiện
nào; module 2.2 đi sâu vào quy tắc chọn thứ tự. Use The Index, Luke nhấn mạnh một điểm: người hiểu
query của ứng dụng nhất là developer, nên thiết kế index là việc của developer chứ không phải để DBA
làm sau.

```sql
CREATE TABLE people (id BIGINT AUTO_INCREMENT PRIMARY KEY,
  last_name VARCHAR(50), first_name VARCHAR(50), city VARCHAR(50),
  INDEX idx_name (last_name, first_name));
EXPLAIN SELECT * FROM people WHERE last_name = 'Le' AND first_name = 'An';  -- key: idx_name, type: ref (output minh hoạ, không phải chạy thật)
EXPLAIN SELECT * FROM people WHERE first_name = 'An';                       -- type: ALL, không seek được (minh hoạ)
```

#### Khi có index mà không được dùng

Nguyên tắc chung: index sắp theo **giá trị gốc của cột**. Điều kiện nào buộc DB phải biến đổi giá
trị cột trước khi so sánh thì DB không biết đi xuống cây theo hướng nào.

1. **Bọc hàm quanh cột**: `WHERE DATE(created_at) = '2026-01-01'`, `WHERE YEAR(created_at) = 2026`,
   `WHERE LOWER(email) = ?`. Cây sắp theo `created_at`, không có sẵn thứ tự của `DATE(created_at)`.
   Sửa bằng cách chuyển phép biến đổi sang phía hằng số:

   ```sql
   -- dùng được index trên created_at; dùng khoảng nửa mở [a, b) để không lo phần giây lẻ
   WHERE created_at >= '2026-01-01' AND created_at < '2026-01-02'
   ```

   Trường hợp bắt buộc phải lọc theo biểu thức thì dùng functional index (module 2.2).
2. **Phép tính trên cột**: `WHERE price * 1.1 > 100` nên viết thành `WHERE price > 100 / 1.1`.
3. **`LIKE` bắt đầu bằng ký tự đại diện**: `LIKE '%abc'` không biết bắt đầu từ chỗ nào trong cây.
   `LIKE 'abc%'` thì được, vì nó tương đương range `>= 'abc' AND < 'abd'`. Tìm kiếm chứa chuỗi ở giữa
   cần full-text index hoặc search engine riêng.
4. **Ép kiểu ngầm** (*implicit conversion*): cột `phone VARCHAR` so với số `WHERE phone = 912345678`.
   Khi so chuỗi với số, MySQL chuyển cả hai về số để so, tức phải chuyển giá trị **từng dòng**, và
   nhiều chuỗi khác nhau (`'0912345678'`, `'912345678'`, `' 912345678'`) cùng ra một số, nên không thể
   seek. Ngược lại, cột `INT` so với chuỗi `'123'` thì vẫn dùng được index, vì chỉ hằng số bị chuyển.
   Tương tự khi join hai cột khác kiểu hoặc khác collation.
5. **Selectivity thấp**: `WHERE gender = 'F'` khớp khoảng một nửa bảng. Nhớ lại ba bước tra index:
   mỗi entry khớp là một lần nhảy về bảng ở vị trí ngẫu nhiên. Đọc tuần tự cả bảng (đọc nhiều page
   liền nhau một lượt) rẻ hơn hàng triệu lần nhảy ngẫu nhiên, nên optimizer bỏ index. Đây là quyết
   định đúng, không phải lỗi. Không có ngưỡng cố định; optimizer ước lượng chi phí dựa trên thống kê
   (module 2.3).
6. **`OR` giữa các cột khác nhau**: `WHERE a = 1 OR b = 2` không dùng được một index `(a, b)`. MySQL
   có thể dùng *index merge* nếu có index riêng trên `a` và trên `b`, hoặc bạn viết lại bằng
   `UNION ALL`.

⚠️ Bẫy hay gặp: dev test trên bảng vài nghìn dòng thấy nhanh, full scan không lộ ra. Lên production
10 triệu dòng mới chậm. Luôn xem `EXPLAIN`, đừng chỉ nhìn thời gian chạy trên máy dev.

#### Khi không nên thêm index

- **Bảng nhỏ**: vài nghìn dòng nằm gọn trong vài chục page; quét hết còn nhanh hơn đi qua index.
- **Bảng ghi nhiều, đọc ít** (log, event thô): mỗi index làm chậm mọi lần ghi mà hiếm khi được đọc.
- **Index trùng tiền tố**: có `(a, b)` rồi thì `(a)` là thừa. Ngoại lệ hiếm: `(a)` nhỏ hơn nhiều và
  có query cần quét toàn bộ index theo `a`.
- **Cột selectivity thấp và phân bố đều** như giới tính, cờ true/false chia đôi. Ngoại lệ: dữ liệu
  lệch và bạn chỉ query phần hiếm (ví dụ `status = 'pending'` chiếm 0,1%), module 2.2.
- **"Index mọi cột trong WHERE"**: mỗi cột một index riêng thường tệ hơn một composite index đúng
  thứ tự, vì optimizer thường chỉ dùng một index cho mỗi bảng trong một query (index merge là
  trường hợp đặc biệt và thường chậm hơn composite).

Quy trình đúng là bắt đầu từ danh sách query thực tế, không bắt đầu từ danh sách cột.

**Tóm tắt nhanh**
- Index là cấu trúc sắp sẵn; B+tree vì mỗi node là một page chứa rất nhiều key, cây 3 đến 4 tầng
  cho hàng trăm triệu dòng, lá nối nhau nên range và sort rẻ.
- Ba bước tra: đi xuống cây (rẻ, có giới hạn), đi dọc lá và nhảy về bảng (không giới hạn, là nơi
  chậm).
- Composite `(a, b, c)` chỉ seek được khi có leftmost prefix; sau cột range thì cột sau hết thu hẹp.
- Hàm quanh cột, `LIKE '%x'`, ép kiểu ngầm, selectivity thấp làm index không được dùng.
- Ba cái giá: ghi chậm, tốn đĩa, tốn RAM (buffer pool).

**Nguồn**: [Use The Index, Luke: Anatomy of an Index](https://use-the-index-luke.com/sql/anatomy) ·
[The Leaf Nodes](https://use-the-index-luke.com/sql/anatomy/the-leaf-nodes) ·
[The B-Tree](https://use-the-index-luke.com/sql/anatomy/the-tree) ·
[Slow Indexes](https://use-the-index-luke.com/sql/anatomy/slow-indexes) ·
[Concatenated Keys](https://use-the-index-luke.com/sql/where-clause/the-equals-operator/concatenated-keys) ·
[MySQL: Multiple-Column Indexes](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html)


---

### 1.3 Transaction cơ bản

Module này trả lời: transaction đảm bảo được những gì, dựa vào cơ chế nào, và vì sao "đã bọc trong
transaction" vẫn chưa đủ an toàn.

#### Transaction là gì

Transaction là một nhóm câu lệnh được DB đối xử như một đơn vị: hoặc mọi thay đổi cùng có hiệu lực
(`COMMIT`), hoặc không thay đổi nào có hiệu lực (`ROLLBACK`). Không có trạng thái "làm được một nửa"
mà người khác nhìn thấy.

```sql
START TRANSACTION;                      -- hoặc BEGIN
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;                                 -- hoặc ROLLBACK để huỷ cả hai
```

*Autocommit*: MySQL mặc định `autocommit = 1`. Khi bạn không mở transaction, mỗi câu lệnh lẻ tự là
một transaction và được commit ngay khi chạy xong. `START TRANSACTION` tạm tắt autocommit cho tới khi
`COMMIT` hoặc `ROLLBACK`. Trong PHP, `PDO::beginTransaction()` làm đúng việc này, và
`DB::transaction()` của Laravel gọi nó bên dưới.

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

// Closure chạy xong thì commit; ném exception thì rollback rồi ném lại exception đó
DB::transaction(function (): void {
    DB::update('UPDATE accounts SET balance = balance - ? WHERE id = ?', [100, 1]);
    DB::update('UPDATE accounts SET balance = balance + ? WHERE id = ?', [100, 2]);
});
```

⚠️ Một số câu lệnh gây *implicit commit* (tự commit transaction đang mở), điển hình là DDL như
`CREATE TABLE`, `ALTER TABLE`. Tài liệu Laravel cảnh báo: chạy chúng qua `DB::statement()` hoặc
`DB::unprepared()` bên trong transaction sẽ commit toàn bộ transaction mà Laravel không biết (module
2.7).

#### ACID, mỗi chữ một ví dụ

ACID là bốn tính chất mà transaction hứa hẹn. Kleppmann (DDIA ch.7) lưu ý rằng mỗi DB hiểu các chữ
này hơi khác nhau, nên khi phỏng vấn đừng đọc định nghĩa mà hãy nói cơ chế và ví dụ.

**A, Atomicity (nguyên tử)**: nếu transaction lỗi giữa chừng (lỗi logic, mất kết nối, crash), mọi
thay đổi đã làm được huỷ. Kleppmann gợi ý nghĩ về chữ A như *abortability* (khả năng huỷ bỏ): nhờ
nó, app chỉ cần retry cả khối mà không lo dữ liệu dở dang. Ví dụ chuyển tiền: không bao giờ có trạng
thái đã trừ tài khoản 1 mà chưa cộng tài khoản 2. Cơ chế: InnoDB ghi bản cũ của mỗi dòng bị sửa vào
*undo log*, rollback là áp ngược undo log (module 3.1).

**C, Consistency (nhất quán)**: dữ liệu luôn thoả các *bất biến* (invariant) của hệ thống. Điểm quan
trọng: DB chỉ giữ được những bất biến đã khai báo thành ràng buộc (`PRIMARY KEY`, `UNIQUE`,
`FOREIGN KEY`, `CHECK`, `NOT NULL`). Luật nghiệp vụ như "tổng tiền vào bằng tổng tiền ra" hay "số dư
không âm" mà không khai báo là trách nhiệm của app. Vì vậy Kleppmann cho rằng C là tính chất của ứng
dụng hơn là của DB. Từ MySQL 8.0.16, `CHECK` thực sự được kiểm tra (trước đó bị bỏ qua), nên
`balance DECIMAL(19,4) CHECK (balance >= 0)` là cách đưa luật xuống DB.

**I, Isolation (cô lập)**: các transaction chạy đồng thời không giẫm lên nhau. Lý tưởng là
*serializable*: kết quả giống như chạy lần lượt từng cái. Thực tế DB mặc định dùng mức yếu hơn để
nhanh hơn (MySQL: Repeatable Read, Postgres: Read Committed), và mức yếu này để lọt một số anomaly
(module 2.5). Ví dụ: đang chuyển tiền thì báo cáo tổng số dư không thấy trạng thái "đã trừ mà chưa
cộng".

**D, Durability (bền vững)**: đã báo `COMMIT` thành công thì dữ liệu không mất dù ngay sau đó mất
điện. Cơ chế là *write-ahead log* (WAL, ghi log trước):

1. Transaction sửa page dữ liệu trong RAM (buffer pool), chưa ghi page xuống đĩa.
2. Khi `COMMIT`, InnoDB ghi mô tả thay đổi vào *redo log* trên đĩa và gọi `fsync` (lệnh buộc hệ điều
   hành đẩy dữ liệu từ cache xuống thiết bị thật).
3. Chỉ sau khi `fsync` xong mới báo commit thành công cho client.
4. Page dữ liệu được ghi xuống đĩa sau, ở chế độ nền. Nếu crash trước lúc đó, khởi động lại InnoDB
   đọc redo log và áp lại các thay đổi đã commit.

Ghi redo log là ghi nối tiếp vào cuối file, nhanh hơn nhiều so với ghi các page 16 KB nằm rải rác.
Durability phụ thuộc cấu hình: `innodb_flush_log_at_trx_commit = 1` (mặc định) mới fsync mỗi lần
commit; đặt 0 hoặc 2 thì có thể mất khoảng một giây giao dịch cuối khi máy sập (module 3.1). Không
có durability tuyệt đối: đĩa hỏng thì cần replica và backup.

#### Hai bẫy

⚠️ Bẫy 1: transaction không tự chống *lost update* (mất cập nhật). Tồn kho còn 1, hai request cùng
mua. Mỗi request đều chạy trong transaction, ở mức mặc định Repeatable Read của MySQL:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | `START TRANSACTION;` | |
| 2 | `SELECT stock FROM products WHERE id=1;` | | A thấy 1 |
| 3 | | `SELECT stock FROM products WHERE id=1;` | B cũng thấy 1 |
| 4 | App thấy còn hàng, `UPDATE products SET stock = 0 WHERE id=1;` | | A giữ lock dòng 1 |
| 5 | | App thấy còn hàng, `UPDATE products SET stock = 0 WHERE id=1;` | B chờ lock của A |
| 6 | `INSERT INTO orders ...; COMMIT;` | | B được chạy tiếp, ghi stock = 0 |
| 7 | | `INSERT INTO orders ...; COMMIT;` | Hai đơn cho một món hàng |

Transaction chỉ đảm bảo mỗi request "hoặc xong hết, hoặc không gì cả", không đảm bảo quyết định dựa
trên dữ liệu đã đọc còn đúng lúc ghi. Lỗi nằm ở mẫu *read-modify-write* (đọc, tính ở app, ghi lại).
Cách sửa đơn giản nhất là để DB tự kiểm tra lúc ghi:

```sql
UPDATE products SET stock = stock - 1 WHERE id = 1 AND stock > 0;
-- affected rows = 1: mua được; = 0: hết hàng. B chờ A commit rồi đọc lại stock mới nhất là 0
```

Các cách khác (`SELECT ... FOR UPDATE`, optimistic lock) ở module 2.5 và 2.6.

⚠️ Bẫy 2: làm việc chậm hoặc không hoàn tác được bên trong transaction.

- Gọi API thanh toán mất 30 giây trong transaction nghĩa là giữ lock dòng 30 giây; mọi request khác
  cần dòng đó xếp hàng, connection bị chiếm, dễ dẫn tới lock wait timeout dây chuyền.
- Rollback DB không thu hồi được email đã gửi, file đã upload, hay tiền đã trừ ở cổng thanh toán.
- Transaction mở lâu còn giữ *snapshot* cũ, cản việc dọn undo log (module 3.1).

Mẫu đúng: làm việc với hệ thống ngoài trước hoặc sau transaction; nếu cần đảm bảo "DB commit thì
chắc chắn có email", ghi yêu cầu vào một bảng outbox trong cùng transaction rồi để worker gửi sau
(module 2.7, [12-messaging.md](../12-messaging.md)).

**Tóm tắt nhanh**
- Transaction là đơn vị all-or-nothing; MySQL mặc định autocommit mỗi câu lệnh.
- A nhờ undo log; D nhờ redo log ghi trước kèm `fsync` trước khi báo commit.
- C chủ yếu là việc của app; DB chỉ giữ ràng buộc đã khai báo (`CHECK` có hiệu lực từ 8.0.16).
- I mặc định yếu hơn serializable; "đã bọc transaction" vẫn bán quá tồn kho nếu đọc rồi ghi.
- Không gọi API ngoài, gửi email trong transaction.

**Nguồn**: *Designing Data-Intensive Applications* ch.7 (phần *The Meaning of ACID*) ·
[Laravel: Database Transactions](https://laravel.com/docs/database#database-transactions) ·
[MySQL: InnoDB Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)

---

### 1.4 Kiểu dữ liệu và schema cơ bản

Module này trả lời: tổ chức bảng thế nào để mỗi sự thật chỉ lưu một chỗ, và chọn kiểu dữ liệu nào
cho tiền, thời gian, chuỗi, id để không phải sửa khi bảng đã lớn.

#### Normalization (chuẩn hoá)

Chuẩn hoá là tách dữ liệu sao cho mỗi sự thật chỉ được lưu ở một nơi. Nếu tên khách hàng được chép
vào mọi đơn hàng, đổi tên phải sửa hàng nghìn dòng, và chỉ cần sót một dòng là dữ liệu mâu thuẫn
(*update anomaly*).

| Dạng chuẩn | Quy tắc | Vi phạm | Sửa |
|---|---|---|---|
| 1NF | Mỗi ô một giá trị nguyên tử, không lặp nhóm cột | `tags = 'php,mysql'`, hoặc `phone1, phone2, phone3` | Bảng `post_tags(post_id, tag_id)` |
| 2NF | 1NF, và cột không khoá phụ thuộc **toàn bộ** khoá chính (chỉ liên quan khi PK nhiều cột) | `order_items(order_id, product_id, qty, product_name)`: `product_name` chỉ phụ thuộc `product_id` | Đưa `product_name` về `products` |
| 3NF | 2NF, và không có phụ thuộc bắc cầu (cột không khoá phụ thuộc cột không khoá khác) | `orders(id, customer_id, customer_city)`: city phụ thuộc customer | Đưa city về `customers` |

⚠️ Lưu dạng `'php,mysql'` phá mọi thứ: không index được từng tag, không có khoá ngoại, đếm hay xoá
một tag phải xử lý chuỗi. `FIND_IN_SET()` không dùng index để tra được, nên phải quét toàn bộ.

Các loại quan hệ:

- **1-n**: khoá ngoại nằm ở phía "nhiều" (`orders.user_id` trỏ `users.id`). Nhớ index cột khoá ngoại;
  InnoDB tự tạo index cho FK nếu chưa có.
- **n-n**: bảng trung gian `user_roles(user_id, role_id)` với `PRIMARY KEY (user_id, role_id)`, thêm
  index `(role_id, user_id)` nếu cần tra chiều ngược lại. PK trên cặp cột vừa chặn trùng, vừa là
  index cho chiều xuôi.
- **1-1**: `users` và `user_profiles(user_id PK)`; dùng để tách cột ít dùng hoặc rất lớn, giữ bảng
  chính gọn.

Denormalize có chủ đích (lưu thêm dữ liệu dẫn xuất để đọc nhanh) là chủ đề của module 2.8. Nguyên tắc:
chuẩn hoá trước, chỉ denormalize khi có số đo cho thấy cần.

#### Tiền

⚠️ Không dùng `FLOAT`/`DOUBLE` cho tiền. Đây là số dấu phẩy động nhị phân (IEEE 754): giống như 1/3
không viết chính xác được ở hệ thập phân, 0.1 không biểu diễn chính xác được ở hệ nhị phân. Sai số
nhỏ ở mỗi phép tính, nhưng cộng dồn hàng triệu giao dịch hoặc so sánh bằng thì sai thật.

```php
<?php
declare(strict_types=1);

var_dump(0.1 + 0.2 === 0.3);        // bool(false)
printf("%.17f\n", 0.1 + 0.2);       // 0.30000000000000004
var_dump(bcadd('0.1', '0.2', 2) === '0.30');   // bool(true): bcmath tính trên chuỗi thập phân
```

```sql
SELECT 0.1 + 0.2 = 0.3;        -- 1: trong MySQL, literal 0.1 là giá trị chính xác (DECIMAL)
SELECT 1e-1 + 2e-1 = 3e-1;     -- 0: literal dạng mũ là DOUBLE, sai số lộ ra
```

Hai cách đúng:

- `DECIMAL(M, D)`: số thập phân chính xác, `M` là tổng số chữ số (tối đa 65), `D` là số chữ số sau dấu
  phẩy. Không khai gì thì là `DECIMAL(10,0)`, tức không có phần thập phân, một bẫy khác. Cho tiền hay
  dùng `DECIMAL(19,4)`. ⚠️ Giá trị có nhiều chữ số thập phân hơn `D` bị đưa về `D` chữ số mà không
  báo lỗi (chỉ có warning); khi INSERT vào cột `DECIMAL`, MySQL làm tròn kiểu "round half away from
  zero" (`2.5` thành `3`).
- `BIGINT` theo đơn vị nhỏ nhất: đồng (VND không có đơn vị lẻ), cent (USD). Phép cộng trừ là số nguyên
  nên nhanh và chính xác; chia (tính thuế, chia đều) thì phải quyết định làm tròn một cách tường minh.

Luôn lưu kèm mã tiền tệ (`currency CHAR(3)` theo ISO 4217, ví dụ `'VND'`). Ở PHP, giá trị `DECIMAL`
đọc từ PDO là chuỗi `"1234.5000"`; giữ nguyên dạng chuỗi và tính bằng bcmath hoặc thư viện như
`brick/money` (module 2.7).

#### Thời gian

| Kiểu | Khoảng giá trị | Timezone | Ghi chú |
|---|---|---|---|
| `DATE` | 1000-01-01 tới 9999-12-31 | Không | Ngày sinh, ngày hiệu lực |
| `DATETIME` | 1000-01-01 00:00:00 tới 9999-12-31 23:59:59 | Không quy đổi | Lưu nguyên con số bạn đưa vào |
| `TIMESTAMP` | 1970-01-01 00:00:01 UTC tới 2038-01-19 03:14:07 UTC | Quy đổi theo `time_zone` của session | Lưu nội bộ dạng UTC |

Cả `DATETIME` và `TIMESTAMP` hỗ trợ phần lẻ giây tới 6 chữ số (`DATETIME(6)`).

Cơ chế của `TIMESTAMP`: khi ghi, MySQL hiểu giá trị theo timezone của **session hiện tại** rồi đổi
sang UTC để lưu; khi đọc, đổi từ UTC sang timezone của session đang đọc. Vì vậy cùng một dòng, hai
session có `time_zone` khác nhau đọc ra hai giá trị khác nhau. `DATETIME` không làm gì cả: bạn ghi
`14:00` thì mọi session đều đọc `14:00`, và ý nghĩa "14:00 ở múi giờ nào" nằm hoàn toàn ở app.

```sql
CREATE TABLE tz_demo (ts TIMESTAMP, dt DATETIME);
SET time_zone = '+07:00';
INSERT INTO tz_demo VALUES ('2026-01-01 14:00:00', '2026-01-01 14:00:00');
SET time_zone = '+00:00';
SELECT * FROM tz_demo;   -- ts = 07:00:00 (đã quy đổi), dt = 14:00:00 (giữ nguyên)
```

⚠️ Bug "lệch 7 tiếng" xảy ra khi ba tầng không thống nhất: timezone của PHP (`date.timezone`,
khoá `timezone` trong `config/app.php` của Laravel), `time_zone` của session MySQL, và kiểu cột. Kịch bản điển hình:

1. App Laravel đặt `'timezone' => 'Asia/Ho_Chi_Minh'`. Lúc 14:00 giờ Việt Nam, Laravel ghi chuỗi
   `'2026-01-01 14:00:00'` (chuỗi không mang timezone).
2. Session MySQL để `+00:00`, cột kiểu `TIMESTAMP`. MySQL hiểu `14:00` là 14:00 UTC và lưu như vậy,
   trong khi thực tế là 07:00 UTC.
3. App đọc lại qua cùng session thì vẫn thấy 14:00, nên không ai phát hiện. Nhưng một job khác, một
   tool báo cáo, hoặc một app khác đặt session `+07:00` sẽ đọc ra 21:00. Dữ liệu đã sai 7 tiếng.

Nguyên tắc tránh: app chạy UTC, session DB đặt UTC, cột lưu UTC; chỉ đổi sang giờ người dùng ở tầng
hiển thị. Thời điểm tương lai gắn với lịch địa phương (lịch hẹn 9:00 sáng giờ Hà Nội năm sau) thì lưu
thêm tên timezone. `TIMESTAMP` còn bị giới hạn năm 2038, nên dữ liệu như ngày hết hạn hợp đồng 20 năm
phải dùng `DATETIME`.

Đối chiếu Postgres (theo wiki "Don't Do This"): dùng `timestamptz`, không dùng `timestamp` không có
timezone, vì `timestamptz` biểu diễn một thời điểm tuyệt đối. ⚠️ Không dùng `BETWEEN` cho khoảng thời
gian: `BETWEEN '2026-01-01' AND '2026-01-02'` gồm cả đúng nửa đêm ngày 2, gây đếm trùng. Viết
`>= '2026-01-01' AND < '2026-01-02'`. Lời khuyên này đúng cho cả MySQL.

#### Chuỗi

- *Charset* (bảng mã) quyết định ký tự được lưu thành byte ra sao. `utf8` cũ của MySQL thực chất là
  `utf8mb3`: tối đa 3 byte mỗi ký tự, chỉ chứa được Basic Multilingual Plane, nên không lưu được emoji
  và một số chữ Hán hiếm (cần 4 byte). Tên `utf8`/`utf8mb3` đã deprecated. Luôn dùng `utf8mb4`
  (tối đa 4 byte mỗi ký tự, là mặc định từ MySQL 8.0).
- *Collation* là bộ luật so sánh và sắp xếp chuỗi. Mặc định của `utf8mb4` trong MySQL 8.x là
  `utf8mb4_0900_ai_ci`: `ai` là accent-insensitive (không phân biệt dấu), `ci` là case-insensitive
  (không phân biệt hoa thường). Laravel mặc định cấu hình `utf8mb4_unicode_ci` trong
  `config/database.php`, cũng không phân biệt hoa thường và dấu trong đa số trường hợp.
- ⚠️ Hệ quả với tiếng Việt: `'Hà' = 'Ha' = 'HA'` là TRUE, và unique index trên `name` coi chúng là
  trùng nhau. Cần phân biệt thì dùng collation `_as_cs` (ví dụ `utf8mb4_0900_as_cs`) hoặc `_bin` (so
  byte), có thể đặt riêng cho từng cột.

```sql
SELECT 'Hà' = 'Ha';                                          -- 1
SELECT 'Hà' = 'Ha' COLLATE utf8mb4_0900_as_cs;               -- 0
```

Đổi collation hoặc charset trên bảng đã có dữ liệu:

```sql
ALTER TABLE users CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_as_cs;
```

Rủi ro cần kiểm tra trước:

1. **Dựng lại bảng**: đổi charset/collation của cột có dữ liệu thường phải copy toàn bộ bảng (khoá
   ghi); bảng lớn thì dùng tool online (module 3.3).
2. **Unique bị vỡ hoặc mới xuất hiện**: chuyển từ `_cs` sang `_ci`, hai giá trị trước đây khác nhau
   (`'An'`, `'an'`) trở thành trùng, và `ALTER` thất bại vì vi phạm unique. Chạy trước
   `SELECT col COLLATE <mới>, COUNT(*) ... GROUP BY 1 HAVING COUNT(*) > 1`.
3. **Join giữa cột khác collation**: lỗi "Illegal mix of collations", hoặc MySQL phải chuyển đổi giá
   trị và không dùng được index để join. Đổi đồng bộ mọi cột liên quan.
4. **Độ dài index**: `utf8mb4` tính 4 byte mỗi ký tự; `VARCHAR(255)` là 1020 byte. InnoDB với row
   format `DYNAMIC` (mặc định) cho key tối đa 3072 byte; giới hạn cũ 767 byte là lý do nhiều project
   Laravel cũ có `Schema::defaultStringLength(191)`.
5. **Hành vi app đổi theo**: thứ tự sắp xếp, kết quả tìm kiếm, và việc đăng nhập bằng email có phân
   biệt hoa thường hay không.

#### Id

- Dùng `BIGINT UNSIGNED AUTO_INCREMENT` (hoặc `BIGINT`) cho id. `INT` có dấu hết ở 2.147.483.647
  (khoảng 2,1 tỉ); bảng log, event, bảng nối nhiều-nhiều chạm mốc này nhanh hơn bạn nghĩ, và id còn
  bị "lỗ" do rollback và upsert (module 2.4). Đổi kiểu PK trên bảng lớn phải copy bảng và sửa mọi
  cột khoá ngoại trỏ tới nó.
- Laravel `$table->id()` tạo sẵn `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY`.
- Chọn giữa auto-increment, UUID, ULID là chủ đề của module 2.1.

**Tóm tắt nhanh**
- 1NF không lưu danh sách trong một ô; 3NF không lưu thông tin của thực thể khác.
- Tiền: `DECIMAL(19,4)` hoặc `BIGINT` đơn vị nhỏ nhất, kèm mã tiền tệ; không bao giờ `FLOAT`.
- `TIMESTAMP` quy đổi theo timezone của session và hết hạn 2038; `DATETIME` giữ nguyên. Thống nhất
  UTC ở cả PHP, session, dữ liệu.
- `utf8mb4` luôn luôn; collation mặc định không phân biệt dấu và hoa thường, ảnh hưởng unique.
- Id là `BIGINT`.

**Nguồn**: [MySQL: Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html) ·
[MySQL: DATE, DATETIME, TIMESTAMP](https://dev.mysql.com/doc/refman/8.4/en/datetime.html) ·
[MySQL: utf8mb4](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb4.html) ·
[PostgreSQL wiki: Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This) ·
[Laravel: Database configuration](https://laravel.com/docs/database#configuration)


---

## Chặng 2: Làm chủ

### 2.1 InnoDB lưu dữ liệu thế nào

Module này trả lời: một dòng dữ liệu thực sự nằm ở đâu trong InnoDB, một câu `SELECT` qua secondary
index đi qua những bước nào, và vì sao việc chọn primary key quyết định hiệu năng của cả bảng.

Dữ liệu mẫu dùng cho module:

```sql
USE learn;
CREATE TABLE members (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  email      VARCHAR(100) NOT NULL,
  name       VARCHAR(50)  NOT NULL,
  city       VARCHAR(50),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_email (email)
);
INSERT INTO members (email, name, city) VALUES
  ('an@x.com','An','Hà Nội'), ('binh@x.com','Bình','Huế'), ('chi@x.com','Chi','Đà Nẵng');
```

#### Clustered index: bảng chính là một cây

Ở module 1.2, index là "một cấu trúc riêng, có đường dẫn về dòng đầy đủ". InnoDB đi xa hơn: **bảng
không tồn tại tách rời khỏi index**. Toàn bộ dữ liệu của bảng được lưu trong một B+tree sắp theo
primary key, và node lá của cây này chứa **toàn bộ các cột** của dòng. Cây đó gọi là *clustered
index* (index gom cụm: dữ liệu được gom theo thứ tự của key).

```
Clustered index của members (sắp theo id)

                    [ root: 1 | 5000 | 9000 ]                 <- chỉ có id + số page con
                  /            |             \
   [ 1 | 2000 | 3500 ]   [ 5000 | 6500 ]   [ 9000 | ... ]     <- branch
      /     |      \
 [id=1, an@x.com, An, Hà Nội, ...]                           <- leaf: DÒNG ĐẦY ĐỦ
 [id=2, binh@x.com, Bình, Huế, ...]
 [id=3, chi@x.com, Chi, Đà Nẵng, ...]   <-> lá kế tiếp <-> ...
```

Một vài chi tiết cấu trúc (theo bài của Jeremy Cole về B+tree trong InnoDB):

- Mỗi node là một page (mặc định 16 KB). Lá được đánh level 0, lên mỗi tầng level tăng 1. Các page cùng level
  nối thành danh sách liên kết hai chiều qua con trỏ "page trước" và "page sau".
- Node không phải lá chỉ chứa cặp (key nhỏ nhất của page con, số hiệu page con), không chứa dữ liệu.
- Trong một page, các record được nối với nhau theo thứ tự key tăng dần, nhưng vị trí vật lý bên
  trong page thì không nhất thiết theo thứ tự.
- Ví dụ của Cole với bảng `INT` PK cộng một cột `CHAR(10)`: khoảng 468 record mỗi page lá và khoảng
  1.203 record mỗi page nhánh; 1 triệu dòng chỉ cần 3 tầng.
- Page gốc không bao giờ bị tách vì vị trí của nó được ghi cố định trong data dictionary. Khi gốc
  đầy, InnoDB chuyển toàn bộ record của gốc sang một page mới rồi tách page mới đó, gốc "được nâng
  lên" một tầng.

Hệ quả thực tế:

1. **Tra theo PK là nhanh nhất**: đi xuống một cây là tới dòng, không có bước nào thêm. Tài liệu MySQL
   nói tìm qua clustered index dẫn thẳng tới page chứa dữ liệu dòng.
2. **Range theo PK rất rẻ**: `WHERE id BETWEEN 1000 AND 2000` đọc một dải lá liền nhau, các dòng đã
   nằm cạnh nhau sẵn.
3. **Mỗi bảng chỉ có đúng một clustered index**, vì dữ liệu chỉ sắp theo một thứ tự được.
4. **Đổi giá trị PK là đắt**: dòng phải chuyển sang vị trí mới trong cây, và mọi secondary index
   phải sửa theo (lý do ở nhóm tiếp theo). Đừng dùng cột có thể thay đổi (email, số điện thoại) làm
   PK.

Nếu bảng không khai PK, InnoDB vẫn phải có clustered index, nên nó tự chọn theo thứ tự:

1. Có `PRIMARY KEY` thì dùng PK.
2. Không có thì dùng **index `UNIQUE` đầu tiên mà mọi cột của nó đều `NOT NULL`**.
3. Không có nốt thì InnoDB tạo một clustered index ẩn tên `GEN_CLUST_INDEX` trên một cột row ID
   6 byte, tăng dần theo thứ tự insert. Bạn không select, không join, không tra được bằng cột này.

⚠️ Bảng không có PK (hay gặp ở bảng log, bảng pivot tạo vội) vẫn chạy được, nhưng row ID ẩn là một
bộ đếm dùng chung cho mọi bảng như vậy trong cả instance, và nhiều công cụ (replication theo row,
tool online schema change ở module 3.3, một số cluster như Group Replication) yêu cầu hoặc hoạt
động tốt hơn nhiều khi bảng có PK tường minh. Từ MySQL 8.0.13 có biến `sql_require_primary_key` (mặc định
`OFF`) để cấm tạo bảng thiếu PK. Tài liệu MySQL khuyên: luôn khai PK, không có cột tự nhiên phù hợp thì thêm cột
auto-increment.

#### Secondary index: tra hai lần

Mọi index không phải clustered index gọi là *secondary index*. Mỗi entry của nó chứa: các cột được
index **cộng với toàn bộ các cột của PK**. Nó không chứa con trỏ tới vị trí vật lý của dòng.

```
Secondary index uk_email (sắp theo email)        Clustered index (sắp theo id)
 leaf: (an@x.com,   1)                            leaf: (1, an@x.com, An, Hà Nội, ...)
       (binh@x.com, 2)  ----- id = 2 ---------->        (2, binh@x.com, Bình, Huế, ...)
       (chi@x.com,  3)                                  (3, chi@x.com, Chi, Đà Nẵng, ...)
```

Đường đi của `SELECT * FROM members WHERE email = 'binh@x.com'`:

1. Đi từ gốc xuống lá của `uk_email` theo giá trị `'binh@x.com'` (số page bằng chiều cao cây).
2. Đọc entry `(binh@x.com, 2)`, lấy được PK là `2`.
3. Đi từ gốc xuống lá của **clustered index** theo `id = 2` (thêm một lượt đi xuống cây nữa).
4. Lấy các cột `name`, `city`, `created_at` từ dòng đầy đủ.

Bước 3 gọi là *lookup* (tra lại bảng, có tài liệu gọi là *bookmark lookup*). Với một dòng thì không
đáng kể vì các tầng trên của cây thường nằm sẵn trong RAM. Với một query khớp 50.000 entry thì đó là
50.000 lần đi xuống clustered index ở các vị trí rải rác. Đây chính là bước "nhảy về bảng" đã nói ở
module 1.2, và là lý do optimizer bỏ index khi selectivity thấp.

Vì sao InnoDB chọn lưu PK thay vì địa chỉ vật lý? Vì dòng trong clustered index **di chuyển** khi page
bị tách hoặc gộp. Nếu secondary index lưu địa chỉ page, mỗi lần tách page phải sửa hàng loạt index.
Lưu PK thì dòng chạy đi đâu cũng tìm lại được. Cái giá là mỗi lookup tốn một lần đi xuống cây thay
vì một lần nhảy thẳng.

Hai hệ quả phải nhớ:

- **PK càng dài, mọi secondary index càng phình**. Tài liệu MySQL nói thẳng: PK dài thì secondary
  index tốn nhiều đĩa hơn, nên dùng PK ngắn. Bảng có 6 secondary index và PK là `CHAR(36)` thì mỗi
  dòng phải chép chuỗi 36 byte đó thêm 6 lần, so với 8 byte của `BIGINT`. Index to hơn nghĩa là ít
  entry trên mỗi page hơn, cây có thể cao hơn, buffer pool chứa được ít hơn.
- **Covering index có sẵn một cột miễn phí**: PK luôn nằm trong secondary index. Nếu mọi cột query
  cần đều nằm trong index (tính cả PK) thì bỏ được bước 3. Đó là *covering index* (module 2.2).

```sql
EXPLAIN SELECT id FROM members WHERE email = 'binh@x.com';
-- Extra: Using index  -> covering: id đã có sẵn trong entry của uk_email
EXPLAIN SELECT id, name FROM members WHERE email = 'binh@x.com';
-- Không có "Using index": name chỉ có ở clustered index, phải lookup
```

Ví dụ thứ hai trong plan: với index `(a)` thì `SELECT id FROM t WHERE a = ?` là covering, vì entry
thật của index là `(a, id)`. Tương tự, `SELECT COUNT(*) FROM t` trên InnoDB thường quét secondary
index nhỏ nhất thay vì clustered index, vì mỗi entry nhỏ hơn dòng đầy đủ nên ít page hơn.

#### Chọn primary key

| | Auto-increment `BIGINT` | UUIDv4 | UUIDv7 / ULID |
|---|---|---|---|
| Giá trị | Tăng dần | Ngẫu nhiên hoàn toàn (122 bit ngẫu nhiên) | 48 bit đầu là timestamp mili giây, phần sau ngẫu nhiên |
| Vị trí insert trong cây | Luôn ở lá cuối cùng | Bất kỳ lá nào | Gần lá cuối |
| Kích thước | 8 byte | 16 byte (`BINARY(16)`) | 16 byte |
| Sinh ở app, nhiều service, offline | Không, phải chờ DB cấp | Được | Được |
| Lộ thông tin | Lộ số lượng, đoán được id kế tiếp | Không | Lộ thời điểm tạo |

Vì sao insert ngẫu nhiên đắt, theo từng bước:

1. InnoDB cố để trống khoảng 1/16 mỗi page cho các update sau. Với insert tuần tự, page được lấp
   tới khoảng 15/16 rồi InnoDB mở page mới ở cuối; lá cuối luôn "nóng" nên luôn nằm trong RAM.
2. Với UUIDv4, mỗi insert rơi vào một lá bất kỳ. Nếu lá đó không còn trong buffer pool, InnoDB phải
   đọc nó từ đĩa trước khi chèn. Bảng càng lớn hơn RAM, tỉ lệ này càng cao.
3. Lá đó thường đã gần đầy, nên phải *page split*: tách thành hai page, mỗi page đầy khoảng một nửa,
   và thêm một entry vào node cha (có khi làm node cha tách tiếp).
4. Kết quả lâu dài: tài liệu MySQL ghi page của index insert ngẫu nhiên chỉ đầy từ 1/2 tới 15/16, so
   với khoảng 15/16 khi insert tuần tự. Cùng dữ liệu mà tốn nhiều page hơn, tốn RAM hơn, và các page
   liền nhau về logic nằm rải rác trên đĩa.

UUIDv7 (RFC 9562 mục 5.7) giải quyết điều này: 48 bit đầu là Unix timestamp tính bằng mili giây, 4
bit version, 12 bit `rand_a`, 2 bit variant, 62 bit `rand_b`. Vì timestamp đứng đầu và được so sánh
byte theo byte, các id sinh sau luôn lớn hơn id sinh ở mili giây trước, nên insert dồn về cuối cây
như auto-increment. Trong cùng một mili giây, RFC mô tả các cách giữ thứ tự tăng (mục 6.2): dùng một
bộ đếm ngay sau timestamp, hoặc dùng phần ngẫu nhiên như bộ đếm có seed ngẫu nhiên, hoặc dùng tới 12
bit cho phần lẻ dưới mili giây. ULID cùng ý tưởng (48 bit thời gian + 80 bit ngẫu nhiên), khác ở cách
viết dạng chuỗi (26 ký tự Crockford Base32 so với 36 ký tự hex có gạch).

RFC 9562 cũng lưu ý hai điều hay bị bỏ qua: lưu UUID dạng nhị phân tốn ít chỗ và thường truy cập
nhanh hơn dạng chuỗi (mục 6.13), và UUID không được dùng như một bí mật: "Implementations SHOULD NOT
assume that UUIDs are hard to guess" (mục 8). Link reset mật khẩu phải dùng token ngẫu nhiên riêng,
không dùng UUID của bản ghi.

Lưu UUID trong MySQL:

```sql
CREATE TABLE events (
  id      BINARY(16) PRIMARY KEY,     -- 16 byte, không phải CHAR(36)
  payload JSON
);
-- Hiển thị cho người đọc
SELECT BIN_TO_UUID(id) FROM events;
-- Tra theo chuỗi từ API
SELECT * FROM events WHERE id = UUID_TO_BIN('0198c7a2-4b1e-7c3d-9f00-1a2b3c4d5e6f');
```

⚠️ `UUID()` của MySQL sinh UUID version 1, không phải v7. `UUID_TO_BIN(x, 1)` có cờ *swap* để đảo
các phần timestamp của UUIDv1 lên đầu cho có thứ tự. Đừng bật cờ này với UUIDv7: v7 vốn đã có thứ
tự, đảo lên thì mất thứ tự. MySQL 8.4 chưa có hàm sinh UUIDv7, nên sinh ở app. Postgres 18 có sẵn
hàm `uuidv7()` và kiểu `uuid` 16 byte.

Sinh UUIDv7 bằng PHP thuần, chạy `php uuid7.php`:

```php
<?php
declare(strict_types=1);

// Sinh UUIDv7 dạng 16 byte nhị phân, đúng bố cục RFC 9562 mục 5.7
function uuid7Bytes(): string
{
    $ms = (int) floor(microtime(true) * 1000);
    $bytes = substr(pack('J', $ms), 2) . random_bytes(10);   // 6 byte timestamp + 10 byte ngẫu nhiên
    $bytes[6] = chr((ord($bytes[6]) & 0x0F) | 0x70);          // 4 bit version = 7
    $bytes[8] = chr((ord($bytes[8]) & 0x3F) | 0x80);          // 2 bit variant = 10
    return $bytes;
}

function uuidToString(string $bytes): string
{
    $h = bin2hex($bytes);
    return sprintf('%s-%s-%s-%s-%s', substr($h, 0, 8), substr($h, 8, 4),
        substr($h, 12, 4), substr($h, 16, 4), substr($h, 20));
}

$a = uuid7Bytes();
usleep(2000);
$b = uuid7Bytes();
echo uuidToString($a), PHP_EOL, uuidToString($b), PHP_EOL;
var_dump(strcmp($a, $b) < 0);   // bool(true): sinh sau thì lớn hơn khi so byte
```

Ở Laravel: từ Laravel 12, trait `HasUuids` sinh UUID tương thích v7 (có thứ tự), còn `HasUlids` sinh
ULID. ⚠️ Nhưng migration `$table->uuid('id')` trên MySQL tạo cột `CHAR(36)`, và `$table->ulid()` tạo
`CHAR(26)`, không phải `BINARY(16)`. Muốn lưu nhị phân phải tự khai cột và tự chuyển đổi (custom
cast); nhiều team chấp nhận `CHAR(36)` vì tiện, nhưng hãy biết là đang trả giá ở mọi secondary index.

Auto-increment cũng có điểm cần biết:

- Id không liên tục: transaction rollback, `INSERT IGNORE`, upsert đều có thể "tiêu" một giá trị mà
  không tạo dòng. Đừng dùng id để đếm số bản ghi.
- Id lộ ra API cho phép đoán `/orders/1001` rồi thử `/orders/1002` (nếu phân quyền lỏng, đây là lỗ
  hổng IDOR), và cho đối thủ ước lượng số đơn mỗi ngày.

Mẫu hay dùng, và là câu trả lời tốt cho câu hỏi "bảng orders sinh ra từ nhiều service thì chọn PK
gì":

```sql
CREATE TABLE orders_v2 (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,  -- PK nội bộ: 8 byte, insert tuần tự, join rẻ
  public_id  BINARY(16) NOT NULL,                          -- UUIDv7 do service sinh, đưa ra API
  user_id    BIGINT UNSIGNED NOT NULL,
  total      DECIMAL(19,4) NOT NULL,
  UNIQUE KEY uk_public (public_id),
  KEY idx_user (user_id)
);
```

Lập luận nên trình bày: nếu các service cần tự sinh id trước khi ghi (tạo id offline, gửi event trước
khi insert, gộp dữ liệu nhiều shard), `BIGINT` do DB cấp không đáp ứng được, nên cần UUIDv7/ULID.
Dùng thẳng UUIDv7 làm PK là chấp nhận được: insert vẫn gần tuần tự, cái giá là 16 byte ở mọi
secondary index và lộ thời điểm tạo. Nếu bảng có nhiều secondary index và join nhiều, tách `id`
nội bộ và `public_id` như trên. Tránh UUIDv4 làm PK của bảng lớn trên InnoDB.

#### Cột lớn

Với row format `DYNAMIC` (mặc định, biến `innodb_default_row_format`), InnoDB xử lý cột độ dài thay
đổi (`VARCHAR`, `TEXT`, `BLOB`, `JSON`) như sau:

1. Nếu cả dòng vừa trong page của clustered index thì lưu tại chỗ (*inline*).
2. Nếu dòng quá dài, InnoDB chọn **các cột dài nhất** đẩy ra các *overflow page* riêng (*off-page*),
   cho tới khi dòng vừa. Trong dòng chỉ còn con trỏ 20 byte trỏ tới overflow page.
3. `TEXT`/`BLOB` từ 40 byte trở xuống luôn được lưu inline.

Hệ quả:

- `SELECT *` trên bảng có cột `TEXT` hay `JSON` lớn phải đọc thêm các overflow page cho mỗi dòng,
  dù app không dùng tới cột đó. Liệt kê cột cần thiết, đặc biệt ở các query danh sách.
- Cột lớn được giữ inline làm mỗi page lá chứa ít dòng hơn, range scan theo PK đọc nhiều page hơn.
  Tách cột lớn ít dùng sang bảng 1-1 (module 1.4) là cách giữ bảng chính gọn.
- ⚠️ Eloquent mặc định `SELECT *`. Trang danh sách 50 bài viết kéo cả `body` dài vài chục KB mỗi
  bài. Dùng `->select([...])` hoặc tách bảng.

#### Đối chiếu Postgres

Postgres tổ chức ngược lại hoàn toàn:

```
InnoDB                                   Postgres
secondary (email, PK) --> clustered      index (email, ctid) --> heap
  (tra 2 cây)              (có dòng)       (tra 1 cây)            (dòng nằm lộn xộn)
```

- Dữ liệu nằm trong *heap*: các page chứa dòng không sắp theo thứ tự nào. Mỗi dòng (Postgres gọi là
  *tuple*) có địa chỉ vật lý *ctid* dạng (số page, vị trí trong page), xem được bằng
  `SELECT ctid, * FROM t`.
- Mọi index, kể cả PK, đều là "secondary": entry chứa key và ctid. Tra index xong nhảy thẳng tới dòng,
  không phải đi xuống cây thứ hai. PK trong Postgres không có vai trò đặc biệt về lưu trữ, nên UUIDv4
  làm PK ít tai hại hơn InnoDB (vẫn làm index PK phân mảnh, nhưng không phân mảnh bảng).
- Cái giá nằm ở update. Theo MVCC của Postgres, `UPDATE` không sửa tại chỗ mà ghi **một bản dòng mới**
  ở vị trí khác, bản cũ chờ `VACUUM` dọn. Dòng mới có ctid mới, nên về nguyên tắc **mọi index** của
  bảng phải thêm entry trỏ tới ctid mới, kể cả index trên cột không đổi.
- Ngoại lệ là *HOT update* (Heap-Only Tuple). Điều kiện cần cả hai: (1) update không đổi cột nào
  được index tham chiếu (trừ index tóm tắt kiểu BRIN), và (2) page chứa dòng cũ còn đủ chỗ cho bản
  mới. Khi đó không cần thêm entry vào các index thường (index tóm tắt như BRIN vẫn có thể phải
  cập nhật); index vẫn trỏ về vị trí cũ và Postgres đi theo chuỗi
  phiên bản trong cùng page. Các bản trung gian còn được dọn ngay trong lúc đọc thông thường, không
  cần đợi vacuum. Giảm `fillfactor` của bảng để chừa chỗ trống giúp HOT xảy ra nhiều hơn; theo dõi
  tỉ lệ HOT qua `pg_stat_all_tables` (cột `n_tup_hot_upd` so với `n_tup_upd`).

So sánh để trả lời phỏng vấn: InnoDB sửa dòng tại chỗ trong clustered index, đưa bản cũ vào undo log
(module 3.1), và chỉ phải sửa secondary index nào chứa cột bị đổi. Postgres tra đọc nhanh hơn một
bước nhưng mỗi update có thể phải ghi vào mọi index. Bảng update nhiều lần trên cột không index (ví
dụ bộ đếm `view_count`) là chỗ HOT phát huy tác dụng.

**Tóm tắt nhanh**
- InnoDB: bảng là B+tree sắp theo PK, lá chứa dòng đầy đủ; không khai PK thì dùng unique NOT NULL
  đầu tiên, không có nữa thì row ID ẩn 6 byte.
- Secondary index lưu (cột, PK); `SELECT *` qua secondary index là hai lần đi xuống cây. Query chỉ
  cần cột index và PK thì covering.
- PK ngắn, tăng dần, không đổi. UUIDv4 làm PK gây insert ngẫu nhiên, page split, page chỉ đầy
  1/2 đến 15/16.
- UUID lưu `BINARY(16)`; UUIDv7/ULID khi cần sinh id ngoài DB; tách `id` nội bộ và `public_id` khi
  bảng có nhiều index.
- Postgres: heap không sắp xếp, index trỏ ctid, update tạo bản mới và sửa mọi index trừ khi HOT.

**Nguồn**: [MySQL: Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html) ·
[MySQL: InnoDB Row Formats](https://dev.mysql.com/doc/refman/8.4/en/innodb-row-format.html) ·
[MySQL: Physical Structure of an InnoDB Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html) ·
[Jeremy Cole: B+Tree index structures in InnoDB](https://blog.jcole.us/2013/01/10/btree-index-structures-in-innodb/) ·
[RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) ·
[Postgres: Heap-Only Tuples](https://www.postgresql.org/docs/current/storage-hot.html)


---

### 2.2 Index nâng cao

Module này trả lời: cho trước danh sách query, chọn cột nào vào index, theo thứ tự nào, và đoán
trước `EXPLAIN` sẽ ra gì. Nền tảng là hai ý của module 1.2 và 2.1: index là cây sắp theo
leftmost prefix, và mỗi entry của secondary index có sẵn PK.

Dữ liệu mẫu (đủ lớn để optimizer chịu dùng index):

```sql
USE learn;
CREATE TABLE orders2 (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id    BIGINT UNSIGNED NOT NULL,
  status     TINYINT NOT NULL,              -- 0 pending, 1 paid, 2 shipped, 3 cancelled
  total      DECIMAL(12,2) NOT NULL,
  created_at DATETIME NOT NULL,
  note       VARCHAR(200)
);
SET SESSION cte_max_recursion_depth = 200000;
INSERT INTO orders2 (user_id, status, total, created_at)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 200000)
SELECT n % 5000 + 1,
       IF(n % 1000 = 0, 0, n % 3 + 1),          -- pending chỉ chiếm 0,1%
       n % 500, '2025-01-01' + INTERVAL (n % 600) DAY
FROM seq;
ANALYZE TABLE orders2;
```

#### Thứ tự cột trong composite index

Use The Index, Luke phân biệt hai vai trò của một điều kiện khi đi qua index:

- *Access predicate* (điều kiện truy cập): quyết định điểm bắt đầu và điểm dừng của đoạn lá cần
  quét. Đây là điều kiện thực sự thu hẹp phạm vi.
- *Filter predicate* (điều kiện lọc): chỉ được kiểm tra trên từng entry trong đoạn đã quét, không
  làm đoạn đó ngắn đi.

Mục tiêu khi chọn thứ tự cột là biến càng nhiều điều kiện thành access predicate càng tốt. Quy tắc
ngắn gọn của sách: "index for equality first, then for ranges", tức cột so sánh `=` đứng trước, cột
so sánh khoảng hoặc cột sort đứng sau.

Vì sao: trong index `(user_id, created_at)`, các entry có cùng `user_id = 7` nằm liền nhau và bên
trong nhóm đó `created_at` đã sắp sẵn, nên `user_id = 7 AND created_at > X` là một đoạn liền mạch.
Đảo lại thành `(created_at, user_id)` thì đoạn `created_at > X` chứa mọi user, và `user_id` trong
đoạn đó lộn xộn, chỉ còn là filter.

```
index (created_at, user_id), WHERE created_at > '2026-03-01' AND user_id = 7
  (03-01, 2) (03-01, 7) (03-01, 9) (03-02, 1) (03-02, 7) (03-03, 4) ...  <- quét HẾT đoạn, lọc user 7
index (user_id, created_at), cùng điều kiện
  ... (7, 02-28) | (7, 03-01) (7, 03-02) (7, 03-05) | (8, 01-01) ...     <- chỉ quét đúng phần giữa hai vạch
```

Trong ví dụ của sách (nhân viên sinh trong 9 ngày ở chi nhánh 27), đặt cột ngày trước làm DB quét
5 lá, đặt cột chi nhánh trước chỉ quét 1 lá; khoảng ngày càng rộng thì chênh lệch càng lớn.

Tài liệu MySQL (Range Optimization) phát biểu cùng quy tắc theo cách của optimizer: đi từ trái sang
phải, cột dùng `=`, `<=>`, `IS NULL` thì đi tiếp sang cột sau; gặp cột đầu tiên dùng toán tử khoảng
(`>`, `<`, `>=`, `<=`, `BETWEEN`, `!=`, `<>`, `LIKE 'abc%'`) thì dừng, cột đó vẫn thu hẹp nhưng các cột sau không
tham gia dựng khoảng quét nữa.

```sql
CREATE INDEX idx_u_s_c ON orders2 (user_id, status, created_at);
-- Cả 3 cột là access predicate
EXPLAIN SELECT * FROM orders2 WHERE user_id = 7 AND status = 1 AND created_at > '2026-01-01';
-- Chỉ thu hẹp theo user_id: thiếu status nên created_at không nối tiếp được prefix
EXPLAIN SELECT * FROM orders2 WHERE user_id = 7 AND created_at > '2026-01-01';
-- status là khoảng: thu hẹp theo (user_id, status), created_at thành filter
EXPLAIN SELECT * FROM orders2 WHERE user_id = 7 AND status > 0 AND created_at > '2026-01-01';
```

Cách đọc số cột được dùng: xem cột `key_len` của `EXPLAIN`. `BIGINT` là 8 byte, `TINYINT` 1 byte,
`DATETIME` 5 byte (cộng 1 byte nếu cột cho phép NULL). Ba câu trên lần lượt cho `key_len` 14, 8 và 9.

Một số lưu ý khi áp dụng quy tắc:

- `IN (...)` được xem như nhiều điểm `=`, nên cột `IN` vẫn cho cột sau tham gia thu hẹp (range gồm
  nhiều khoảng con). Nhưng nó phá thứ tự sort (nhóm ORDER BY bên dưới).
- Khi có nhiều cột `=`, thứ tự giữa chúng ít ảnh hưởng tới query đó; hãy chọn sao cho prefix phục vụ
  được nhiều query khác nhất. Lời khuyên "cột selectivity cao đặt trước" chỉ là tiêu chí phụ.
- Nếu hai query cần hai cột range khác nhau thì một index không phục vụ tốt cả hai; chấp nhận hai
  index hoặc chấp nhận filter.

#### Covering index và index condition pushdown

*Covering index*: mọi cột query cần (trong `SELECT`, `WHERE`, `ORDER BY`, `GROUP BY`) đều có trong
index, tính cả PK có sẵn. InnoDB trả kết quả chỉ từ index, bỏ hẳn bước lookup về clustered index.
`EXPLAIN` hiện `Extra: Using index`. Postgres gọi đây là *index-only scan*.

```sql
-- Covering: user_id, status, created_at, id đều nằm trong idx_u_s_c
EXPLAIN SELECT id, created_at FROM orders2 WHERE user_id = 7 AND status = 1;   -- Using index
-- Không covering: total chỉ có ở clustered index
EXPLAIN SELECT id, total FROM orders2 WHERE user_id = 7 AND status = 1;
```

Covering mạnh nhất khi query khớp nhiều dòng: 10.000 lookup ngẫu nhiên bị thay bằng đọc tuần tự vài
chục page lá. Cái giá là index phình to và mọi update trên cột được thêm vào phải sửa index. Đừng
nhồi mọi cột vào index chỉ để covering; làm điều đó cho query nóng nhất.

*Index condition pushdown* (ICP) giải quyết trường hợp điều kiện nằm trên cột có trong index nhưng
không phải access predicate. Theo tài liệu MySQL:

Không có ICP:
1. Storage engine đọc entry index trong đoạn quét.
2. Dùng PK trong entry để lookup, đọc dòng đầy đủ.
3. Trả dòng lên tầng server để kiểm tra phần còn lại của `WHERE`.

Có ICP:
1. Storage engine đọc entry index.
2. Kiểm tra ngay phần điều kiện chỉ cần cột trong index. Không thoả thì bỏ qua, **không lookup**.
3. Thoả thì mới lookup dòng đầy đủ và trả lên server kiểm tra phần còn lại.

Ví dụ trong tài liệu với index `(zipcode, lastname, firstname)`:

```sql
SELECT * FROM people
WHERE zipcode = '95054' AND lastname LIKE '%etrunia%' AND address LIKE '%Main Street%';
```

`zipcode` là access predicate. `lastname LIKE '%etrunia%'` không thu hẹp được đoạn quét (ký tự đại
diện ở đầu) nhưng kiểm tra được trên entry index, nên InnoDB loại bớt người cùng zipcode sai họ
trước khi lookup. `address` không có trong index nên vẫn phải lọc sau lookup. `EXPLAIN` hiện
`Extra: Using index condition`.

Điều kiện áp dụng ICP: kiểu truy cập `range`, `ref`, `eq_ref` hoặc `ref_or_null`, và phải cần đọc dòng
đầy đủ. Với InnoDB chỉ áp dụng cho secondary index (clustered index đã có sẵn dòng, không có lookup
để tiết kiệm). Không áp dụng cho điều kiện chứa subquery, stored function, hoặc index trên virtual
generated column. Bật mặc định, tắt bằng `SET optimizer_switch = 'index_condition_pushdown=off'`.

⚠️ Phân biệt ba chữ hay nhầm trong `Extra`:

| `Extra` | Nghĩa |
|---|---|
| `Using index` | Covering, không lookup. Tốt nhất |
| `Using index condition` | Có ICP: lọc sớm trên index, vẫn lookup phần còn lại |
| `Using where` | Tầng server lọc thêm dòng sau khi storage engine trả về |

#### Index phục vụ ORDER BY

Index đã sắp sẵn, nên nếu thứ tự đọc index trùng với `ORDER BY` thì DB không cần sort. Use The
Index, Luke gọi đây là *pipelined order by*: dòng đầu tiên có thể trả ra ngay, không phải đợi đọc hết
rồi mới sort. Với top-N (`LIMIT 20`), đây là khác biệt giữa đọc 20 entry và đọc, sort 1 triệu dòng.

```sql
CREATE INDEX idx_u_c ON orders2 (user_id, created_at);
EXPLAIN SELECT * FROM orders2 WHERE user_id = 7 ORDER BY created_at DESC LIMIT 20;
-- key: idx_u_c, type: ref, Extra: Backward index scan (đi ngược lá, không sort)
```

Điều kiện để index thay được sort (theo tài liệu ORDER BY Optimization):

1. Các cột `ORDER BY` là các cột liên tiếp của index, **sau** các cột đã bị cố định bằng `=` trong
   `WHERE`. Ví dụ `WHERE key_part1 = c ORDER BY key_part2` dùng được.
2. Chiều sort thống nhất (cùng ASC hoặc cùng DESC, đi ngược cả index), hoặc khớp với chiều khai báo
   trong một *descending index* như `INDEX (a DESC, b ASC)` cho `ORDER BY a DESC, b ASC`.
3. `ORDER BY` không phải là biểu thức (`ORDER BY ABS(k)`, `ORDER BY -k` đều phải sort).
4. Index không phải prefix index trên cột chuỗi (`INDEX (name(10))` không đủ để sort cả chuỗi).

Các trường hợp phải sort:

- `WHERE user_id IN (1,2,3) ORDER BY created_at`: trong index, `created_at` chỉ sắp đúng bên trong
  từng user; ghép ba đoạn lại thì không còn thứ tự chung.
- `WHERE user_id > 100 ORDER BY created_at`: cùng lý do, range trên cột đầu kéo theo nhiều nhóm.
  Sách minh hoạ bằng index `(sale_date, product_id)`: lọc `sale_date = ?` rồi sort theo
  `product_id` thì không cần sort; đổi thành `sale_date >= ?` là phải sort lại.
- `WHERE status = 1 ORDER BY created_at` với index `(user_id, created_at)`: thiếu cột đầu.
- `ORDER BY` trộn cột của hai index khác nhau.

Khi phải sort, `EXPLAIN` hiện `Using filesort`. Tên này gây hiểu lầm: filesort là thuật toán sort
chung, cấp bộ nhớ dần tới `sort_buffer_size`; chỉ khi dữ liệu vượt quá bộ nhớ đó mới ghi file tạm
và merge (theo dõi status `Sort_merge_passes`). Với `ORDER BY ... LIMIT N` trên một bảng, MySQL có thể
sort hoàn toàn trong bộ nhớ chỉ giữ N dòng tốt nhất. Filesort trên 50 dòng không phải vấn đề;
filesort trên 2 triệu dòng để lấy 20 dòng mới là vấn đề.

⚠️ Thay đổi ở MySQL 8.x: `GROUP BY` không còn tự sort kết quả như 5.7. Code cũ dựa vào thứ tự đó phải
thêm `ORDER BY` tường minh.

Phân trang: `LIMIT 20 OFFSET 100000` vẫn phải đi qua 100.020 entry rồi bỏ 100.000 cái đầu. *Seek
method* (keyset pagination) dùng giá trị cuối trang trước làm điểm bắt đầu, nên trang nào cũng rẻ.
Thứ tự sort phải tất định, nên thêm PK làm cột phụ:

```sql
CREATE INDEX idx_u_c_id ON orders2 (user_id, created_at, id);
SELECT id, created_at FROM orders2
WHERE user_id = 7
  AND (created_at < '2026-03-01 00:00:00' OR (created_at = '2026-03-01 00:00:00' AND id < 91234))
ORDER BY created_at DESC, id DESC LIMIT 20;
```

Sách ghi nhận khác biệt bắt đầu rõ từ khoảng trang 20. Nhược điểm: không nhảy thẳng tới trang bất
kỳ, hợp với infinite scroll và API cursor (Laravel `cursorPaginate()` dùng cách này). Chuẩn SQL cho
viết gọn `(created_at, id) < (?, ?)`, nhưng sách lưu ý MySQL tính đúng biểu thức này mà không dùng
được nó làm access predicate khi đi qua index; trên MySQL hãy kiểm `EXPLAIN`, dạng `OR` ở trên là dạng
an toàn.

#### Index trên biểu thức và JSON

*Functional index* (MySQL 8.0.13+, tài liệu gọi là *functional key part*) index kết quả của một biểu
thức. Cú pháp bắt buộc có **hai lớp ngoặc**:

```sql
CREATE INDEX idx_email_lower ON members ((LOWER(email)));
EXPLAIN SELECT id FROM members WHERE LOWER(email) = 'an@x.com';   -- dùng index
EXPLAIN SELECT id FROM members WHERE email = 'an@x.com';          -- KHÔNG dùng idx_email_lower
CREATE INDEX idx_month ON orders2 ((YEAR(created_at)), (MONTH(created_at)));
```

Cơ chế: MySQL tạo một *virtual generated column* ẩn (cột tính từ biểu thức, không lưu vào dòng) và
index cột đó. Hệ quả và giới hạn:

- Query phải viết **đúng biểu thức** đã khai báo thì optimizer mới nhận ra.
- Không được chỉ là tên cột trần (`INDEX ((col1))` lỗi), không dùng trong PK hay khoá ngoại, không
  chứa subquery, biến, hay stored function.
- Mỗi functional key part tính vào giới hạn số cột của bảng.

Với cột `JSON`, không index thẳng được cả tài liệu JSON. Hai cách:

1. Tạo generated column lấy giá trị cần tra, rồi index cột đó. Cách này rõ ràng nhất, query đọc được:

   ```sql
   CREATE TABLE products (id BIGINT PRIMARY KEY, data JSON,
     sku VARCHAR(64) AS (data->>'$.sku') VIRTUAL,
     INDEX idx_sku (sku));
   SELECT * FROM products WHERE sku = 'A-100';
   ```

2. Functional index trực tiếp trên biểu thức JSON. ⚠️ Bẫy collation mà tài liệu `CREATE INDEX` nêu:
   `->>` trả chuỗi collation `utf8mb4_bin`, còn `CAST(... AS CHAR)` mang collation mặc định
   (`utf8mb4_0900_ai_ci`). Index khai `((CAST(data->>'$.name' AS CHAR(30))))` sẽ không được dùng cho
   `WHERE data->>'$.name' = 'James'`, trừ khi thêm `COLLATE utf8mb4_bin` vào định nghĩa index, hoặc
   query viết đúng nguyên biểu thức `CAST`. Hai lựa chọn còn cho kết quả khác nhau: bản `_bin` phân
   biệt hoa thường, bản `_ai_ci` thì không.

Mảng JSON cần *multi-valued index* (MySQL 8.0.17+): một dòng sinh ra nhiều entry, mỗi phần tử một
entry.

```sql
CREATE TABLE customers (id BIGINT AUTO_INCREMENT PRIMARY KEY, custinfo JSON,
  INDEX zips ((CAST(custinfo->'$.zipcode' AS UNSIGNED ARRAY))));
INSERT INTO customers (custinfo) VALUES
  ('{"user":"Jack","zipcode":[94582,94536]}'), ('{"user":"Jill","zipcode":[94568,94507,94582]}');
SELECT * FROM customers WHERE 94507 MEMBER OF (custinfo->'$.zipcode');            -- dùng zips
SELECT * FROM customers WHERE JSON_OVERLAPS(custinfo->'$.zipcode', '[94536,94568]');
```

Optimizer chỉ dùng multi-valued index với `MEMBER OF()`, `JSON_CONTAINS()`, `JSON_OVERLAPS()`. Giới
hạn: một multi-valued key part mỗi index, không khai được `ASC`/`DESC`, không covering, không dùng
cho range scan, không tạo online được (phải `ALGORITHM=COPY`). Nếu phải tra mảng JSON thường xuyên và phức tạp, đó thường là
dấu hiệu nên tách thành bảng con chuẩn hoá (module 1.4).

#### Cardinality và selectivity

- *Cardinality*: số giá trị khác nhau của cột. `SHOW INDEX FROM orders2` hiện cột `Cardinality`, là
  **ước lượng** từ lấy mẫu, cập nhật khi `ANALYZE TABLE` hoặc khi dữ liệu đổi đủ nhiều.
- *Selectivity*: tỉ lệ dòng khớp một điều kiện cụ thể. `user_id = 7` khớp 40/200.000 dòng là
  selectivity tốt; `status = 1` khớp khoảng một phần ba là tệ.

Vì sao khớp nhiều thì optimizer bỏ index: mỗi entry khớp tốn một lookup ở vị trí ngẫu nhiên trong
clustered index. Đọc tuần tự cả bảng đọc từng page một lần, nhiều page liền nhau một lượt. Khi số
lookup vượt một ngưỡng (không cố định, optimizer tính theo mô hình chi phí), quét cả bảng rẻ hơn.

```sql
CREATE INDEX idx_status ON orders2 (status);
EXPLAIN SELECT * FROM orders2 WHERE status = 1;   -- type: ALL dù có idx_status: đúng, không phải lỗi
EXPLAIN SELECT id FROM orders2 WHERE status = 1;  -- thường chọn idx_status: covering nên không lookup
```

Dữ liệu lệch là nơi cardinality đánh lừa. Cột `status` chỉ có 4 giá trị (cardinality 4, nghe như
không đáng index), nhưng `status = 0` chỉ chiếm 0,1% nên index trên `status` rất có ích cho đúng câu
query tìm đơn pending:

```sql
EXPLAIN SELECT * FROM orders2 WHERE status = 0;   -- ref trên idx_status, rows khoảng 200
EXPLAIN SELECT * FROM orders2 WHERE status = 1;   -- vẫn ALL
```

Optimizer biết được sự lệch nhờ đâu? Với cột có index và điều kiện `=`/`IN` trên hằng số, MySQL làm
*index dive*: đi thật xuống index ở hai đầu khoảng để đếm ước lượng số entry, nên thấy ngay
`status = 0` ít dòng. Tài liệu MySQL nói rõ histogram "useful primarily for nonindexed columns", và
khi range optimizer áp dụng được thì optimizer ưu tiên ước lượng của nó hơn histogram. Histogram
(`ANALYZE TABLE t UPDATE HISTOGRAM ON col`) có ích cho cột **không** index, ví dụ để chọn thứ tự
join (module 2.3). ⚠️ Khi số giá trị trong `IN` chạm ngưỡng `eq_range_index_dive_limit` (mặc định
200; muốn dive cho tối đa N giá trị thì đặt N + 1), MySQL bỏ index dive và dùng thống kê trung bình từ cardinality, lúc đó sự lệch bị mất và ước lượng
có thể sai nhiều.

#### Công cụ nên biết

*Skip scan* (MySQL 8.0.13+; Postgres có từ bản 18): cho phép dùng index `(f1, f2)` với
`WHERE f2 > 40` dù thiếu điều kiện trên `f1`. Cơ chế: lấy từng giá trị khác nhau của `f1`, dựng khoảng
`f1 = v AND f2 > 40` cho từng giá trị, quét lần lượt. Chỉ có lợi khi `f1` có ít giá trị. Điều kiện ở
MySQL khá hẹp: query một bảng, không `GROUP BY`/`DISTINCT`, chỉ dùng cột có trong index (covering), có
điều kiện khoảng trên cột được skip tới. `EXPLAIN` hiện `Using index for skip scan`. Biết là có để
đọc được `EXPLAIN`; đừng thiết kế index dựa vào nó.

*Invisible index* (MySQL 8.0+): index vẫn được cập nhật khi ghi và vẫn chặn trùng nếu là `UNIQUE`,
nhưng optimizer bỏ qua. Đổi trạng thái là thao tác in-place, nhanh, trong khi xoá rồi tạo lại index
trên bảng lớn tốn hàng giờ. Quy trình xoá index an toàn:

```sql
ALTER TABLE orders2 ALTER INDEX idx_status INVISIBLE;
-- Theo dõi slow log, APM vài ngày đến vài tuần (gồm cả job cuối tháng!). Có vấn đề thì:
ALTER TABLE orders2 ALTER INDEX idx_status VISIBLE;
-- Thử plan với index ẩn cho một câu, không ảnh hưởng người khác:
EXPLAIN SELECT /*+ SET_VAR(optimizer_switch = 'use_invisible_indexes=on') */ * FROM orders2 WHERE status = 0;
-- Ổn định thì mới xoá thật
DROP INDEX idx_status ON orders2;
```

PK không ẩn được, kể cả PK ngầm (index `UNIQUE NOT NULL` đang đóng vai PK vì bảng không khai PK)
thì cũng báo lỗi 3522.

Tìm index thừa với schema `sys` (có sẵn trong MySQL 8):

```sql
SELECT * FROM sys.schema_unused_indexes WHERE object_schema = 'learn';
SELECT table_name, redundant_index_name, dominant_index_name, sql_drop_index
FROM sys.schema_redundant_indexes WHERE table_schema = 'learn';
```

⚠️ `schema_unused_indexes` dựa trên thống kê Performance Schema tính từ lần khởi động server gần
nhất. Server mới restart hôm qua thì index dùng cho báo cáo tháng sẽ bị liệt kê là "không dùng".
Replica phục vụ đọc có thể dùng index mà primary không bao giờ dùng, nên phải kiểm trên mọi node.

#### Đối chiếu Postgres

- *Partial index*: chỉ index các dòng thoả điều kiện. Index nhỏ, ghi rẻ (dòng không thoả không phải
  cập nhật index):

  ```sql
  -- Postgres
  CREATE INDEX orders_pending ON orders (created_at) WHERE status = 0;
  CREATE UNIQUE INDEX one_active_sub ON subscriptions (user_id) WHERE active;  -- mỗi user một gói active
  ```

  Planner chỉ dùng partial index khi chứng minh được `WHERE` của query suy ra điều kiện của index;
  khả năng suy luận hạn chế nên nên viết điều kiện giống hệt. ⚠️ Với prepared statement có tham số
  (`WHERE status = $1`), planner không biết giá trị lúc lập plan chung nên không dùng được. Tài liệu
  cũng khuyên không tạo hàng loạt partial index thay cho partitioning. MySQL không có partial index;
  cách gần nhất là functional index trên biểu thức trả NULL cho dòng không quan tâm, hoặc bảng riêng.
- `INCLUDE`: `CREATE INDEX ON tab (x) INCLUDE (y)` đưa `y` vào lá chỉ để covering, không thành một
  phần của key. `UNIQUE (x) INCLUDE (y)` chỉ ràng buộc unique trên `x`. MySQL không có `INCLUDE`; muốn
  covering thì thêm cột vào cuối key.
- Index-only scan của Postgres còn phụ thuộc *visibility map*: vì thông tin phiên bản dòng nằm ở heap,
  Postgres chỉ bỏ qua heap được với page đã được vacuum đánh dấu "mọi dòng đều visible". Bảng ghi
  nhiều mà vacuum chưa theo kịp thì "index-only" vẫn đọc heap (xem dòng `Heap Fetches` trong
  `EXPLAIN ANALYZE`). InnoDB không có vấn đề này ở mức tương tự.
- Các loại index khác: *GIN* (inverted index cho `jsonb`, mảng, full-text; không làm index-only scan
  được), *GiST* và *SP-GiST* (dữ liệu hình học, khoảng, tìm gần đúng), *BRIN* (lưu min/max theo từng
  khối page, rất nhỏ, hợp với bảng lớn mà giá trị tăng theo thứ tự vật lý như `created_at` của log),
  và *Hash*.

#### Ghép lại: thiết kế bộ index tối thiểu

Bảng `orders2`, năm query thực tế:

| # | Query | Ghi chú |
|---|---|---|
| Q1 | `WHERE user_id = ? ORDER BY created_at DESC LIMIT 20` | Trang "đơn của tôi" |
| Q2 | `WHERE user_id = ? AND status = ? ORDER BY created_at DESC LIMIT 20` | Lọc theo trạng thái |
| Q3 | `SELECT COUNT(*) WHERE user_id = ? AND status = ?` | Badge đếm |
| Q4 | `WHERE status = 0 AND created_at < NOW() - INTERVAL 1 DAY` | Job huỷ đơn pending quá hạn |
| Q5 | `WHERE created_at >= ? AND created_at < ?` (báo cáo theo ngày) | Chạy ban đêm |

Lập luận:

1. Q2 cần `user_id`, `status` bằng `=` rồi sort theo `created_at`: index `(user_id, status,
   created_at)`. Index này phục vụ luôn Q3 dạng covering (`Using index`).
2. Q1 thiếu `status`, nên `(user_id, status, created_at)` chỉ thu hẹp theo `user_id` rồi phải
   filesort mọi đơn của user. Nếu mỗi user chỉ vài chục đơn thì chấp nhận được; nếu có user hàng
   chục nghìn đơn thì thêm `(user_id, created_at)`.
3. Q4: `status = 0` là `=`, `created_at` là range, nên `(status, created_at)`. Dữ liệu lệch nên index
   này nhỏ về số entry được quét dù cardinality của `status` thấp.
4. Q5 chỉ có range trên `created_at`: cần index `(created_at)` riêng, vì trong `(status,
   created_at)` cột `created_at` không phải prefix. Nếu Q5 chỉ chạy ban đêm trên replica và full scan
   chấp nhận được thì cân nhắc bỏ, đổi lại ghi nhanh hơn.

Kết quả: `(user_id, status, created_at)`, `(status, created_at)`, có thể thêm `(user_id, created_at)` và
`(created_at)`. Dự đoán `EXPLAIN` cho Q2 trước khi chạy: `type: ref`, `key: idx_u_s_c`,
`key_len: 9`, `Extra: Backward index scan` (không có `Using filesort`). Chạy thử để tự kiểm.

**Tóm tắt nhanh**
- Cột `=` trước, cột range hoặc sort sau; sau cột range đầu tiên, các cột sau chỉ là filter. Đọc
  `key_len` để biết dùng tới cột nào.
- `Using index` là covering (không lookup); `Using index condition` là ICP (lọc trên index trước khi
  lookup); đừng nhầm hai cái.
- Index thay được sort khi `ORDER BY` là các cột nối tiếp sau các cột `=`; `IN` hoặc range ở cột
  trước phá thứ tự. Phân trang sâu dùng keyset thay `OFFSET`.
- Functional index cần query viết đúng biểu thức; JSON dùng generated column hoặc multi-valued index.
- Optimizer bỏ index khi selectivity thấp là đúng; dữ liệu lệch thì index dive thấy được, histogram
  dành cho cột không index.
- Xoá index: invisible trước, theo dõi đủ lâu, rồi mới drop.

**Nguồn**: [Use The Index, Luke: Greater, Less and Between](https://use-the-index-luke.com/sql/where-clause/searching-for-ranges/greater-less-between-tuning-sql-access-filter-predicates) ·
[Indexed Order By](https://use-the-index-luke.com/sql/sorting-grouping/indexed-order-by) ·
[Fetch Next Page](https://use-the-index-luke.com/sql/partial-results/fetch-next-page) ·
[MySQL: Index Condition Pushdown](https://dev.mysql.com/doc/refman/8.4/en/index-condition-pushdown-optimization.html) ·
[ORDER BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html) ·
[Range Optimization](https://dev.mysql.com/doc/refman/8.4/en/range-optimization.html) ·
[CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) ·
[Invisible Indexes](https://dev.mysql.com/doc/refman/8.4/en/invisible-indexes.html) ·
[Optimizer Statistics](https://dev.mysql.com/doc/refman/8.4/en/optimizer-statistics.html) ·
[Postgres: Index Types](https://www.postgresql.org/docs/current/indexes-types.html) ·
[Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html) ·
[Index-Only Scans](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)

---

### 2.3 Đọc EXPLAIN và xử lý query chậm

Module này trả lời: làm sao biết một query đang được chạy theo cách nào, bước nào tốn thời gian, và
khi production báo "DB chậm" thì đi từ đâu tới đâu để tìm ra nguyên nhân.

Dữ liệu mẫu cho cả module: một triệu đơn hàng, mười nghìn user. Script sinh dữ liệu chạy mất vài chục
giây:

```sql
USE learn;
SET SESSION cte_max_recursion_depth = 1000000;   -- mặc định 1000, không đủ để sinh 1 triệu dòng

CREATE TABLE big_users (
  id BIGINT PRIMARY KEY, name VARCHAR(50) NOT NULL, country CHAR(2) NOT NULL);
CREATE TABLE big_orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT NOT NULL,
  status VARCHAR(10) NOT NULL,
  total DECIMAL(12,2) NOT NULL,
  created_at DATETIME NOT NULL);

INSERT INTO big_users
WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 10000)
SELECT n, CONCAT('user', n), IF(n % 100 = 0, 'VN', 'US') FROM s;          -- 100 user VN

INSERT INTO big_orders (user_id, status, total, created_at)
WITH RECURSIVE s(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM s WHERE n < 1000000)
SELECT 1 + FLOOR(RAND() * 10000),
       ELT(1 + FLOOR(RAND() * 3), 'paid', 'pending', 'cancelled'),
       ROUND(RAND() * 500, 2),
       '2025-01-01' + INTERVAL FLOOR(RAND() * 31536000) SECOND
FROM s;
ANALYZE TABLE big_users, big_orders;
```

Mỗi user có khoảng 100 đơn, trong đó khoảng một phần ba là `paid`. Các output `EXPLAIN` bên dưới là
output minh hoạ theo định dạng của MySQL 8.4, không phải chạy thật; con số `cost`, `rows` ước lượng,
thời gian, và cả cách trình bày từng dòng trên máy bạn sẽ khác một chút (dữ liệu sinh ngẫu nhiên).
Hãy chạy lại để thấy output thật.

#### Đọc EXPLAIN

*Optimizer* là thành phần của MySQL quyết định chạy một câu SQL như thế nào: đọc bảng nào trước, dùng
index nào, join bằng thuật toán gì, sort ở đâu. Kết quả quyết định đó gọi là *execution plan* (plan).
`EXPLAIN` in ra plan **mà không chạy query**, nên an toàn với mọi câu lệnh và trả kết quả tức thì.

Query cần tối ưu: 20 đơn `paid` mới nhất của một user.

```sql
EXPLAIN SELECT id, total, created_at FROM big_orders
WHERE user_id = 42 AND status = 'paid'
ORDER BY created_at DESC LIMIT 20\G
```

`\G` ở cuối (thay cho `;`) in mỗi cột một dòng, dễ đọc hơn bảng ngang. Khi chưa có index nào ngoài PK:

```
           id: 1
  select_type: SIMPLE
        table: big_orders
   partitions: NULL
         type: ALL
possible_keys: NULL
          key: NULL
      key_len: NULL
          ref: NULL
         rows: 996513
     filtered: 1.00
        Extra: Using where; Using filesort
```

Đọc từng cột:

| Cột | Giá trị ở trên | Nghĩa |
|---|---|---|
| `id` | 1 | Số thứ tự của khối `SELECT`. Query có subquery hoặc `UNION` sẽ có nhiều id. Các dòng cùng id là các bảng trong cùng một join, đọc theo thứ tự từ trên xuống |
| `select_type` | `SIMPLE` | Loại khối: `SIMPLE` (không subquery, không union), `PRIMARY` (khối ngoài cùng), `SUBQUERY`, `DERIVED` (bảng dẫn xuất trong `FROM`), `UNION` |
| `table` | `big_orders` | Bảng được đọc ở dòng này; `<derived2>` là kết quả của khối id 2 |
| `partitions` | NULL | Các partition bị đọc, chỉ có nghĩa với bảng partition (module 3.6) |
| `type` | `ALL` | Cách truy cập bảng (access type), cột quan trọng nhất; xem bảng dưới |
| `possible_keys` | NULL | Các index optimizer thấy **có thể** dùng |
| `key` | NULL | Index **thực sự** được chọn. `possible_keys` có mà `key` là NULL nghĩa là optimizer thấy quét bảng rẻ hơn |
| `key_len` | NULL | Số byte của phần index được dùng để tra, dùng để suy ra composite index được dùng tới cột thứ mấy |
| `ref` | NULL | Giá trị đem so với index: `const` là hằng số, `learn.u.id` là cột của bảng join trước |
| `rows` | 996513 | Số dòng optimizer **ước lượng** phải đọc ở bước này, không phải số dòng trả về |
| `filtered` | 1.00 | Phần trăm ước lượng của `rows` còn lại sau khi áp các điều kiện còn lại của `WHERE` |
| `Extra` | `Using where; Using filesort` | Thông tin thêm; xem bảng dưới |

Diễn giải: đọc toàn bộ khoảng một triệu dòng (`ALL`), lọc bằng `WHERE` ở tầng server (`Using where`),
ước lượng giữ lại 1% tức khoảng 9.965 dòng, rồi sort chúng (`Using filesort`) để lấy 20 dòng. Nhân
`rows × filtered / 100` ra số dòng ước lượng mà bước này chuyển sang bước sau; với join, đây là số lần
bảng tiếp theo bị tra.

⚠️ Con số 1% ở trên không đến từ dữ liệu. Cột `user_id` và `status` chưa có index hay histogram, nên
optimizer dùng hệ số đoán cố định (khoảng 10% cho mỗi điều kiện bằng, hai điều kiện là 10% × 10%).
Thực tế chỉ khoảng 33 dòng khớp. Ước lượng sai như vậy là nguồn gốc của nhiều plan tệ khi query có
join, vì optimizer dựa vào nó để chọn thứ tự bảng.

Các giá trị của `type`, từ tốt tới tệ (theo tài liệu MySQL):

| `type` | Nghĩa | Ví dụ |
|---|---|---|
| `system`, `const` | Tra PK hoặc unique bằng hằng số, tối đa 1 dòng; đọc một lần ở giai đoạn tối ưu rồi coi như hằng | `WHERE id = 5` |
| `eq_ref` | Trong join, mỗi dòng của bảng trước khớp đúng 1 dòng qua PK/unique `NOT NULL` | `JOIN users u ON u.id = o.user_id` |
| `ref` | Tra index bằng `=` nhưng có thể ra nhiều dòng (index không unique, hoặc chỉ dùng prefix) | `WHERE user_id = 42` |
| `ref_or_null` | Như `ref` và thêm các dòng NULL | `WHERE a = 1 OR a IS NULL` |
| `index_merge` | Dùng vài index rồi hợp/giao kết quả | `WHERE a = 1 OR b = 2` với index riêng trên `a`, `b` |
| `range` | Quét một hoặc vài khoảng của index | `BETWEEN`, `>`, `IN (...)`, `LIKE 'abc%'` |
| `index` | Quét **toàn bộ** index từ đầu tới cuối | `SELECT user_id FROM big_orders` khi có index trên `user_id` |
| `ALL` | Quét toàn bộ bảng (clustered index) | Không có index dùng được |

⚠️ `type: index` nghĩa là quét hết index, không phải "đã dùng index tốt". Nó chỉ rẻ hơn `ALL` vì
index thường nhỏ hơn bảng. Hay gặp cùng `Extra: Using index`: query chỉ cần cột có trong index nên
đọc index thay cho bảng, nhưng vẫn đọc hết.

Các giá trị `Extra` hay gặp:

| `Extra` | Nghĩa | Tốt hay xấu |
|---|---|---|
| `Using index` | *Covering index*: mọi cột cần đều có trong index, không phải quay về bảng (module 2.2) | Tốt |
| `Using where` | Có điều kiện được lọc ở tầng server sau khi storage engine trả dòng lên | Bình thường; xấu nếu đi cùng `ALL` trên bảng lớn |
| `Using index condition` | *Index Condition Pushdown* (ICP): điều kiện trên cột có trong index được lọc ngay trong index, trước khi đọc dòng đầy đủ (module 2.2) | Tốt |
| `Using filesort` | Phải sort thêm một bước vì không có index cho sẵn thứ tự; tên gọi gây hiểu lầm, sort có thể diễn ra hoàn toàn trong RAM | Xấu nếu số dòng phải sort lớn |
| `Using temporary` | Phải tạo bảng tạm, thường do `GROUP BY`, `DISTINCT`, `UNION`, hoặc `GROUP BY` và `ORDER BY` khác cột | Xấu nếu nhiều dòng |
| `Using join buffer (hash join)` | Join bằng hash join vì không có index dùng được cho điều kiện join | Xem nhóm thuật toán join |
| `Backward index scan` | Đọc index theo chiều ngược để phục vụ `ORDER BY ... DESC` | Tốt, không phải sort |
| `Using MRR` | *Multi-Range Read*: gom các PK cần đọc rồi sắp lại để đọc bảng gần tuần tự | Tốt |
| `Impossible WHERE` | Điều kiện luôn sai, ví dụ cột `NOT NULL` so với `IS NULL` | Thường là bug trong query |
| `Select tables optimized away` | Trả lời được ngay từ index, ví dụ `MIN(id)` | Tốt |

Giờ thêm một index chỉ trên `user_id` và chạy lại `EXPLAIN`:

```sql
CREATE INDEX idx_user ON big_orders (user_id);
```

```
         type: ref
possible_keys: idx_user
          key: idx_user
      key_len: 8
          ref: const
         rows: 101
     filtered: 10.00
        Extra: Using where; Using filesort
```

Tiến bộ lớn: chỉ đọc khoảng 101 dòng thay vì một triệu. Nhưng vẫn còn lọc `status` sau khi đọc
(`Using where`, `filtered` 10%) và vẫn sort. Thay bằng composite index đúng thứ tự (bằng trước, cột
sort sau, theo quy tắc ở module 2.2):

```sql
DROP INDEX idx_user ON big_orders;
CREATE INDEX idx_user_status_created ON big_orders (user_id, status, created_at);
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

- `ref: const,const`: hai cột đầu của index được so với hai hằng số (`42` và `'paid'`).
- `rows: 34`: khi có index, optimizer không đoán nữa mà *index dive* (xuống cây đếm thử số entry trong
  khoảng), nên ước lượng sát thực tế.
- `filtered: 100.00`: không còn điều kiện nào phải lọc thêm sau khi tra index.
- Không còn `Using filesort`: trong cùng `(user_id, status)` các entry đã sắp theo `created_at`, chỉ cần
  đọc ngược (`Backward index scan`) và dừng sau 20 entry.
- Không có `Using index` vì `total` không nằm trong index, nên mỗi entry vẫn phải quay về bảng lấy
  `total` (20 lần). Thêm `total` vào cuối index sẽ thành covering, nhưng với 20 dòng thì không đáng.

Cách tính `key_len` để biết index được dùng tới cột nào:

| Kiểu cột | Số byte |
|---|---|
| `INT` / `BIGINT` | 4 / 8 |
| `DATETIME` | 5 (cộng phần lẻ giây nếu có) |
| `VARCHAR(n)` / `CHAR(n)` | n × số byte tối đa mỗi ký tự của charset (`utf8mb4` là 4), `VARCHAR` cộng thêm 2 byte lưu độ dài |
| Cột cho phép NULL | Cộng thêm 1 byte |

Ở ví dụ: `user_id BIGINT NOT NULL` là 8, `status VARCHAR(10) NOT NULL` utf8mb4 là 10 × 4 + 2 = 42,
tổng 50: index được dùng để tra tới hết cột thứ hai. Nếu query có thêm `AND created_at >= '2025-06-01'`,
`key_len` sẽ thành 55 và `type` đổi thành `range`. Nếu chỉ thấy 8, tức mới dùng `user_id`, cột sau bị
bỏ (thường do thiếu điều kiện, hoặc cột trước là range).

Ngoài dạng bảng, `EXPLAIN FORMAT=TREE` in plan dạng cây, gần với cách MySQL 8 thực sự thực thi (mô hình
*iterator*: mỗi node kéo từng dòng từ node con):

```
mysql> EXPLAIN FORMAT=TREE SELECT id, total, created_at FROM big_orders
    -> WHERE user_id = 42 AND status = 'paid' ORDER BY created_at DESC LIMIT 20\G
EXPLAIN: -> Limit: 20 row(s)  (cost=11.9 rows=20)
    -> Index lookup on big_orders using idx_user_status_created (user_id=42, status='paid') (reverse)  (cost=11.9 rows=34)
```

`cost` là đơn vị chi phí nội bộ của optimizer (không phải mili giây), chỉ dùng để so các plan với nhau.
`EXPLAIN FORMAT=JSON` in chi tiết nhất, có cả chi phí từng phần.

#### EXPLAIN ANALYZE

`EXPLAIN ANALYZE` **chạy query thật**, đo từng iterator trong lúc chạy, rồi in cây plan kèm số liệu
thật bên cạnh số ước lượng. Tài liệu MySQL 8.4 ghi nó dùng được với `SELECT`, `TABLE`, và `UPDATE`,
`DELETE` nhiều bảng; output luôn ở dạng `TREE`. Vì chạy thật nên query 10 phút thì `EXPLAIN ANALYZE`
cũng 10 phút; dừng được bằng `KILL QUERY` hoặc Ctrl-C.

Chạy với bảng chưa có index phụ (xoá index vừa tạo để so sánh):

```sql
DROP INDEX idx_user_status_created ON big_orders;
EXPLAIN ANALYZE SELECT id, total, created_at FROM big_orders
WHERE user_id = 42 AND status = 'paid' ORDER BY created_at DESC LIMIT 20\G
```

```
EXPLAIN: -> Limit: 20 row(s)  (cost=100712 rows=20) (actual time=398..398 rows=20 loops=1)
    -> Sort: big_orders.created_at DESC, limit input to 20 row(s) per chunk  (cost=100712 rows=996513) (actual time=398..398 rows=20 loops=1)
        -> Filter: ((big_orders.user_id = 42) and (big_orders.status = 'paid'))  (cost=100712 rows=9965) (actual time=2.9..398 rows=34 loops=1)
            -> Table scan on big_orders  (cost=100712 rows=996513) (actual time=0.071..352 rows=1e+6 loops=1)
```

Cách đọc:

1. **Đọc từ trong ra ngoài, từ dưới lên**. Node thụt sâu nhất chạy trước và đẩy dòng lên node cha.
   Ở đây: quét bảng, lọc, sort, cắt 20 dòng.
2. Mỗi node có hai cặp ngoặc. Cặp đầu `(cost=... rows=...)` là **ước lượng**, giống `EXPLAIN`. Cặp sau
   `(actual time=A..B rows=R loops=L)` là **số đo thật**:
   - `A`: số mili giây tới khi node trả dòng đầu tiên; `B`: tới khi trả dòng cuối cùng.
   - `R`: số dòng node trả lên; `L`: số lần node được chạy.
   - Khi `loops > 1`, `A`, `B` và `R` là **trung bình mỗi loop**. Tổng thời gian xấp xỉ `B × L`, tổng
     số dòng là `R × L`.
3. **Thời gian của node cha đã bao gồm node con**. Muốn biết node tự tốn bao nhiêu, lấy `B` của nó trừ
   `B` của con. Ở đây: `Table scan` tốn 352 ms, `Filter` tốn thêm khoảng 46 ms, `Sort` và `Limit` gần
   như không tốn. Bước tốn nhất là quét bảng.
4. **So `rows` ước lượng với `rows` thật ở cùng node**. `Filter` ước lượng 9.965, thật là 34, lệch gần
   300 lần. Lệch 10 tới 100 lần trở lên nghĩa là optimizer đang đoán mù; ở query có join, đó thường là
   lý do nó chọn sai thứ tự bảng hoặc sai thuật toán.
5. `A` lớn gần bằng `B` ở node `Sort` (398..398): sort là thao tác "chặn", phải nhận hết dòng rồi mới
   trả được dòng đầu tiên. Ngược lại `Table scan` có `A` = 0.071: trả dòng đầu gần như ngay.

Sau khi tạo lại index `(user_id, status, created_at)`:

```
EXPLAIN: -> Limit: 20 row(s)  (cost=11.9 rows=20) (actual time=0.058..0.112 rows=20 loops=1)
    -> Index lookup on big_orders using idx_user_status_created (user_id=42, status='paid') (reverse)  (cost=11.9 rows=34) (actual time=0.056..0.108 rows=20 loops=1)
```

Từ 398 ms xuống 0,1 ms. Node index lookup chỉ trả 20 dòng dù ước lượng 34: `Limit` ngừng kéo khi đủ 20,
và nhờ không phải sort nên node con dừng sớm được.

Một ví dụ join để thấy ý nghĩa của `loops`:

```sql
EXPLAIN ANALYZE SELECT u.name, o.total FROM big_users u
JOIN big_orders o ON o.user_id = u.id WHERE u.country = 'VN'\G
```

```
EXPLAIN: -> Nested loop inner join  (cost=35912 rows=99700) (actual time=0.35..21.4 rows=10043 loops=1)
    -> Filter: (u.country = 'VN')  (cost=1005 rows=1000) (actual time=0.068..2.91 rows=100 loops=1)
        -> Table scan on u  (cost=1005 rows=9975) (actual time=0.062..2.36 rows=10000 loops=1)
    -> Index lookup on o using idx_user_status_created (user_id=u.id)  (cost=25.1 rows=99.7) (actual time=0.041..0.176 rows=100 loops=100)
```

- Node dưới cùng của join (`Index lookup on o`) chạy 100 lần, một lần cho mỗi user VN. Mỗi lần trung
  bình 0,176 ms và 100 dòng, tổng khoảng 17,6 ms và 10.000 dòng. Đọc `0.176` mà quên nhân với `loops`
  là sai lầm hay gặp nhất khi đọc plan.
- Ước lượng của node lookup (99,7 dòng mỗi lần) khớp thực tế vì cột có index và thống kê
  cardinality. Còn `Filter` ước lượng 1.000 user VN, thật là 100: cột `country` không có index hay histogram nên
  optimizer đoán 10%. Ở đây sai lệch không gây hại, nhưng với bảng lớn hơn nó có thể làm optimizer
  chọn bảng `o` làm bảng ngoài.

⚠️ Vì `EXPLAIN ANALYZE` chạy thật, dùng với `UPDATE`/`DELETE` là dữ liệu thay đổi thật. Bọc trong
transaction và rollback:

```sql
START TRANSACTION;
EXPLAIN ANALYZE DELETE o FROM big_orders o JOIN big_users u ON u.id = o.user_id WHERE u.country = 'VN';
ROLLBACK;
```

Chú ý: câu lệnh vẫn giữ lock trên các dòng bị ảnh hưởng cho tới khi rollback, nên đừng làm vậy trên
production giờ cao điểm.

Đối chiếu Postgres: `EXPLAIN ANALYZE` cũng in `actual time=A..B rows=R loops=L`, và tài liệu Postgres
nói rõ `actual time` và `rows` là **giá trị mỗi loop**, phải nhân với `loops`. Postgres dùng thêm
`EXPLAIN (ANALYZE, BUFFERS)` để thấy số page đọc từ cache và từ đĩa (từ PostgreSQL 18, `BUFFERS` được
bật mặc định khi có `ANALYZE`). Plan Postgres dài thì dán vào [explain.dalibo.com](https://explain.dalibo.com/)
để xem dạng hình.

#### Statistics

Optimizer chọn plan theo *cost model*: ước lượng số dòng mỗi bước, nhân với chi phí đọc page, so sánh
các phương án rồi chọn cái rẻ nhất. Mọi ước lượng dựa vào *statistics* (thống kê) về dữ liệu, nên
thống kê sai thì plan sai, dù code không đổi một dòng.

InnoDB có hai nguồn ước lượng:

1. **Index dive**: với điều kiện trên cột có index và số khoảng nhỏ, optimizer đi xuống cây để đếm
   xấp xỉ số entry trong khoảng. Chính xác nhưng tốn công, nên chỉ làm khi số khoảng dưới
   `eq_range_index_dive_limit` (mặc định 200). `IN (...)` có từ 200 giá trị trở lên thì chuyển sang dùng số
   trung bình trong thống kê.
2. **Thống kê lưu sẵn** (*persistent statistics*, bật mặc định bằng `innodb_stats_persistent=ON`): số
   dòng của bảng và *cardinality* (số giá trị khác nhau) của từng index, tính bằng cách lấy mẫu một số
   page (`innodb_stats_persistent_sample_pages`, mặc định 20) chứ không đọc hết. InnoDB tự tính lại
   khi hơn khoảng 10% số dòng của bảng thay đổi (`innodb_stats_auto_recalc`), việc tính lại chạy nền
   nên có độ trễ.

Xem thống kê:

```sql
SHOW INDEX FROM big_orders;                      -- cột Cardinality là số ước lượng
SELECT TABLE_ROWS FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'learn' AND TABLE_NAME = 'big_orders';   -- cũng là ước lượng
ANALYZE TABLE big_orders;                        -- tính lại ngay
```

*Histogram* bổ sung cho cột **không có index**: nó mô tả phân bố giá trị của cột, để optimizer ước
lượng `filtered` bằng dữ liệu thật thay cho hệ số đoán 10%.

```sql
ANALYZE TABLE big_users UPDATE HISTOGRAM ON country WITH 16 BUCKETS;
EXPLAIN SELECT * FROM big_users WHERE country = 'VN';   -- filtered giờ khoảng 1.00 thay vì 10.00
SELECT HISTOGRAM FROM information_schema.COLUMN_STATISTICS
WHERE TABLE_NAME = 'big_users' AND COLUMN_NAME = 'country';
ANALYZE TABLE big_users DROP HISTOGRAM ON country;       -- xoá khi không cần
```

- Hai loại: *singleton* khi số giá trị khác nhau không vượt số bucket (mỗi bucket một giá trị kèm tần
  suất cộng dồn), *equi-height* khi nhiều hơn (mỗi bucket là một khoảng giá trị có số dòng xấp xỉ
  nhau). Số bucket mặc định 100, tối đa 1024.
- Histogram dùng được cho các điều kiện so với hằng số: `=`, `<>`, `<`, `>`, `BETWEEN`, `IN`, `IS NULL`.
- ⚠️ Mặc định (`MANUAL UPDATE`) histogram **không tự cập nhật** khi dữ liệu đổi; phải chạy lại
  `ANALYZE TABLE ... UPDATE HISTOGRAM`. MySQL 8.4 có thêm tuỳ chọn `... WITH N BUCKETS AUTO UPDATE`
  để histogram được cập nhật cùng các lần tính lại thống kê. Với cột đã có index, histogram thường
  không cần thiết, vì index dive cho ước lượng tốt hơn.
- Ứng dụng điển hình: cột dữ liệu lệch như `status` có 99% `done` và 1% `pending`, nhưng không muốn
  thêm index vì bảng ghi nhiều.

⚠️ Sự cố kinh điển: query đang chạy 20 ms bỗng thành 8 giây, code và index không đổi. Nguyên nhân hay
gặp:

1. Sau một đợt import hoặc xoá lớn, thống kê bị cũ hoặc vừa được tính lại, optimizer đổi plan (chọn
   index khác, hoặc đảo thứ tự join).
2. Dữ liệu vượt một ngưỡng khiến ước lượng chi phí đảo chiều, ví dụ một user "cá voi" có hàng triệu
   đơn làm `ref` trên index đó không còn rẻ.
3. Mẫu lấy thống kê (20 page) không đại diện cho dữ liệu lệch.

Cách xử lý: `EXPLAIN` lại để xác nhận plan đổi; `ANALYZE TABLE`; nếu vẫn sai thì thêm histogram, tăng
`STATS_SAMPLE_PAGES` cho bảng đó, hoặc cuối cùng mới dùng hint (`FORCE INDEX`, `JOIN_ORDER`). Hint là
giải pháp tạm vì nó khoá cứng plan, dữ liệu đổi tiếp thì hint thành sai.

#### Thuật toán join

MySQL 8.4 có hai thuật toán join:

**Nested loop join**: với mỗi dòng của bảng ngoài (*outer*), tra bảng trong (*inner*).

```
for each u in big_users where country = 'VN':         -- 100 dòng
    for each o in index idx_user(user_id = u.id):     -- tra B+tree, ~100 dòng mỗi lần
        emit (u, o)
```

Rất nhanh khi bảng ngoài ít dòng và bảng trong có index trên cột join: chi phí xấp xỉ
`số dòng ngoài × chi phí một lần tra index`. Không có index thì mỗi vòng ngoài phải quét cả bảng trong,
thành `m × n`, và đó là lý do MySQL cần thuật toán thứ hai. Ví dụ `EXPLAIN ANALYZE` ở trên là nested
loop, `type` của bảng trong là `ref` hoặc `eq_ref`.

**Hash join** (có từ MySQL 8.0.18; từ 8.0.20 thay hẳn thuật toán *block nested loop* cũ):

1. *Build*: đọc bảng nhỏ hơn, dựng hash table trong RAM với key là cột join.
2. *Probe*: đọc bảng lớn, với mỗi dòng tính hash của cột join rồi dò trong hash table.
3. Hash table lớn hơn `join_buffer_size` thì tràn xuống file tạm trên đĩa và xử lý theo từng phần.

Chi phí xấp xỉ `m + n`, tốt hơn hẳn `m × n` khi không có index. Thử bằng cách join trên cột không có
index (`IGNORE INDEX` giả lập việc thiếu index trên `user_id`):

```sql
EXPLAIN FORMAT=TREE SELECT COUNT(*) FROM big_users u
JOIN big_orders o IGNORE INDEX (idx_user_status_created) ON o.user_id = u.id
WHERE u.country = 'VN'\G
```

```
EXPLAIN: -> Aggregate: count(0)  (cost=...)
    -> Inner hash join (o.user_id = u.id)  (cost=... rows=...)
        -> Table scan on o  (cost=... rows=996513)
        -> Hash
            -> Filter: (u.country = 'VN')  (cost=1005 rows=998)
                -> Table scan on u  (cost=1005 rows=9975)
```

Node dưới `Hash` là phía build (100 user VN), node còn lại là phía probe (quét một triệu đơn, dò
mỗi dòng trong hash table). Ở dạng bảng, dấu hiệu là
`Extra: Using join buffer (hash join)`. Hash join dùng được cả cho outer join, semijoin, antijoin và
điều kiện không phải dấu bằng (từ 8.0.20). Bật/tắt bằng hint `BNL(...)` / `NO_BNL(...)` hoặc
`optimizer_switch` (`block_nested_loop`).

⚠️ Thấy hash join trên bảng lớn trong query OLTP (query phục vụ request người dùng) thường là dấu hiệu
thiếu index trên cột join, không phải "MySQL đã tối ưu giùm". Hash join hợp với báo cáo quét nhiều
dòng; request web cần nested loop trên index.

| Thuật toán | MySQL 8.4 | Postgres | Hợp khi |
|---|---|---|---|
| Nested loop | Có | Có | Bảng ngoài ít dòng, bảng trong có index trên cột join |
| Hash join | Có (8.0.18+) | Có | Không có index, hai bảng lớn, điều kiện bằng |
| Merge join | Không | Có | Cả hai phía đã sắp theo cột join (ví dụ cùng có index), tập lớn |

#### Quy trình xử lý query chậm

Khi có cảnh báo "DB chậm", làm theo thứ tự sau. Đi phỏng vấn, kể được cả quy trình quan trọng hơn biết
một mẹo tối ưu riêng lẻ.

**1. Tìm query.** Ba nguồn chính:

- *Slow query log*: ghi mọi câu lệnh chạy lâu hơn `long_query_time` giây. Mặc định tắt, và ngưỡng mặc
  định 10 giây là quá cao cho web; thường đặt 0,1 tới 1 giây (hỗ trợ tới micro giây).

  ```sql
  SET GLOBAL slow_query_log = ON;
  SET GLOBAL long_query_time = 0.2;          -- chỉ áp dụng cho connection mở sau lệnh này
  SET GLOBAL log_slow_extra = ON;            -- thêm Bytes_sent, số lần đọc handler, bảng tạm...
  SHOW VARIABLES LIKE 'slow_query_log_file';
  ```

  Mỗi entry có dòng `# Query_time: 1.204  Lock_time: 0.000012  Rows_sent: 20  Rows_examined: 1000000`.
  `Rows_examined` lớn gấp nhiều lần `Rows_sent` là dấu hiệu thiếu index. Thời gian chờ lấy lock ban
  đầu không được tính khi so với `long_query_time`. Các biến liên quan: `min_examined_row_limit`,
  `log_queries_not_using_indexes` (ghi cả query không dùng index dù nhanh; dễ làm log phình).
- *performance_schema*: MySQL gom mọi câu lệnh theo *digest* (dạng chuẩn hoá, thay hằng số bằng `?`)
  và đếm sẵn, không cần bật slow log:

  ```sql
  SELECT DIGEST_TEXT, COUNT_STAR AS calls,
         ROUND(SUM_TIMER_WAIT / 1e12, 1) AS total_s,     -- timer tính bằng picosecond
         ROUND(AVG_TIMER_WAIT / 1e9, 2) AS avg_ms,
         SUM_ROWS_EXAMINED, SUM_ROWS_SENT
  FROM performance_schema.events_statements_summary_by_digest
  ORDER BY SUM_TIMER_WAIT DESC LIMIT 10;
  ```

  Schema `sys` có sẵn view dễ đọc hơn: `sys.statement_analysis`, `sys.statements_with_full_table_scans`.
- *APM* (New Relic, Datadog, Sentry...) nối query với endpoint gây ra nó, rất có ích để biết sửa ở đâu
  trong code.

**2. Xếp hạng theo tổng tải: tần suất × thời gian.** Một query 50 ms chạy 10.000 lần mỗi phút tốn 500
giây DB mỗi phút; một query 5 giây chạy mỗi giờ một lần tốn chưa tới 0,1 giây mỗi phút. Sửa cái đầu
trước. `pt-query-digest` (Percona Toolkit) đọc slow log, gom query theo *fingerprint* (bỏ giá trị cụ
thể, gộp danh sách `IN`), rồi in bảng profile:

```sh
pt-query-digest --limit 10 /var/lib/mysql/host-slow.log
```

```
# Rank Query ID           Response time   Calls  R/Call V/M   Item
# ==== ================== =============== ====== ====== ===== ==============
#    1 0x3A99CC42AEDCCFCD 1824.3200 61.2%  36480 0.0500  0.01 SELECT big_orders
#    2 0x8F2B0E1D77A1B6C4  412.9000 13.8%     83 4.9747  1.20 SELECT big_users big_orders
```

`Response time` là tổng thời gian và phần trăm trên toàn bộ; `R/Call` là trung bình mỗi lần;
`V/M` (variance-to-mean) cao nghĩa là thời gian dao động mạnh giữa các lần chạy (có lúc nhanh lúc chậm,
gợi ý lock hoặc dữ liệu lệch). Bảng trên là output minh hoạ, không phải chạy thật. Phần chi tiết từng
query có cột percentile 95%, số dòng đã examine, và một câu mẫu để copy ra chạy `EXPLAIN`.

**3. `EXPLAIN ANALYZE`** câu mẫu (trên replica hoặc bản sao dữ liệu nếu query nặng) để thấy node tốn
nhất và chỗ ước lượng lệch.

**4. Sửa**, theo thứ tự chi phí tăng dần: thêm hoặc đổi index; viết lại query (bỏ hàm quanh cột, đổi
`OFFSET` sang keyset, tách `OR` thành `UNION ALL`); chỉ lấy cột cần; `ANALYZE TABLE`; cache ở tầng app;
đổi thiết kế (bảng tổng hợp, denormalize, module 2.8).

**5. Đo lại** bằng cùng công cụ ở bước 1 và theo dõi vài ngày; kiểm tra index mới không làm chậm ghi.

Không phải lúc nào nguyên nhân cũng nằm trong câu query. Khi nhiều query khác nhau cùng chậm một lúc,
hãy nghĩ tới tài nguyên dùng chung:

| Triệu chứng | Nguyên nhân có thể | Kiểm tra |
|---|---|---|
| Query đơn giản theo PK cũng chậm, `Lock_time` hoặc thời gian chờ cao | Lock wait: một transaction dài giữ lock | `SELECT * FROM sys.innodb_lock_waits;`, `SHOW ENGINE INNODB STATUS\G`, tìm transaction mở lâu trong `information_schema.INNODB_TRX` |
| App báo "Too many connections" hoặc chờ lấy connection | Connection cạn: query chậm giữ connection lâu, hoặc pool quá nhỏ/lớn | `SHOW STATUS LIKE 'Threads_%';` so với `max_connections` (mặc định 151) |
| Chậm đều, disk I/O cao | Dữ liệu nóng không vừa buffer pool | Tỉ lệ `Innodb_buffer_pool_reads` (phải đọc đĩa) trên `Innodb_buffer_pool_read_requests` tăng |
| Chỉ đọc trên replica bị sai hoặc cũ | Replica lag | `SHOW REPLICA STATUS\G` (module 3.4) |
| Chậm theo giờ cố định | Cron, backup, batch job | Đối chiếu lịch job với biểu đồ |

`SHOW PROCESSLIST` (hoặc `SELECT * FROM sys.processlist`) là ảnh chụp nhanh nhất: đang có những câu
lệnh nào, chạy bao lâu, ở trạng thái gì (`executing`, `Waiting for table metadata lock`...). Trạng thái `Sending data` hay
thấy trong bài blog cũ nay đã được gộp vào `executing`.

#### Pagination

*Offset pagination*: `LIMIT 20 OFFSET 100000` nghĩa là "sắp xếp, bỏ 100.000 dòng đầu, lấy 20 dòng".
DB không có cách nào nhảy thẳng tới dòng thứ 100.001; nó phải đọc (và thường quay về bảng lấy dòng
đầy đủ) cả 100.020 dòng rồi vứt 100.000 dòng. Trang càng sâu càng chậm, tuyến tính theo số trang.

```sql
CREATE INDEX idx_created ON big_orders (created_at, id);
EXPLAIN ANALYZE SELECT id, total, created_at FROM big_orders
ORDER BY created_at DESC, id DESC LIMIT 20 OFFSET 500000\G
-- Output minh hoạ, rút gọn:
-- Limit/Offset: 20/500000 row(s) ... rows=20
--   -> Index scan on big_orders using idx_created (reverse) ... rows=500020
```

Use The Index, Luke chỉ ra thêm một vấn đề về tính đúng: offset chỉ biết bỏ **bao nhiêu** dòng, không
biết bỏ **những dòng nào**. Nếu có đơn mới được thêm giữa lúc người dùng xem trang 1 và trang 2, mọi
dòng bị đẩy xuống một vị trí, và dòng cuối trang 1 xuất hiện lại ở đầu trang 2. Xoá dòng thì ngược lại:
có dòng bị bỏ sót.

*Keyset pagination* (còn gọi *seek method* hay *cursor pagination*) nhớ giá trị sort của dòng cuối
trang trước, và dùng nó làm điều kiện `WHERE`. Index `(created_at, id)` cho phép đi thẳng xuống cây tới
vị trí đó, rồi đọc đúng 20 entry:

```sql
-- Trang đầu
SELECT id, total, created_at FROM big_orders
ORDER BY created_at DESC, id DESC LIMIT 20;
-- Trang sau: dòng cuối trang trước có created_at = '2025-11-02 10:00:00', id = 734501
SELECT id, total, created_at FROM big_orders
WHERE created_at < '2025-11-02 10:00:00'
   OR (created_at = '2025-11-02 10:00:00' AND id < 734501)
ORDER BY created_at DESC, id DESC LIMIT 20;
```

Các điểm then chốt:

- **Thứ tự sort phải tất định** (*deterministic*): mỗi dòng có một vị trí duy nhất. Nhiều đơn cùng
  `created_at` thì chỉ sort theo `created_at` không xác định được dòng nào đứng trước, và keyset sẽ bỏ
  sót hoặc lặp dòng ở ranh giới. Thêm cột unique (`id`) làm *tie-breaker*, và đưa nó vào cả `ORDER BY`,
  điều kiện `WHERE`, và index.
- Chuẩn SQL cho viết gọn bằng *row value*: `WHERE (created_at, id) < (?, ?)`. Postgres dùng index tốt với
  dạng này. ⚠️ Với MySQL, Use The Index, Luke ghi nhận optimizer không dùng row value làm điều kiện tra
  index. Tài liệu MySQL 8.4 (Row Constructor Expression Optimization) cho ví dụ optimizer dùng ít cột
  index hơn khi viết bằng row constructor, dùng đủ cột khi viết lại dạng `OR`/`AND`, và khuyên không
  trộn row constructor với `AND`/`OR`. Viết dạng `OR`/`AND` như trên là cách chắc ăn. Luôn `EXPLAIN` để
  thấy `type: range` và `key_len` đủ hai cột.
- Chiều sort khác nhau giữa các cột (`created_at DESC, id ASC`) làm điều kiện phức tạp hơn; giữ cùng
  chiều cho đơn giản.
- Đi lùi (trang trước) phải đảo cả dấu so sánh và chiều sort, rồi đảo lại kết quả ở app.

| | Offset | Keyset |
|---|---|---|
| Tốc độ trang sâu | Chậm dần, tuyến tính theo offset | Như nhau ở mọi trang |
| Nhảy tới trang N | Được | Không |
| Hiện "trang 3/250" | Được (kèm `COUNT(*)`, cũng tốn) | Không tự nhiên |
| Dữ liệu thay đổi giữa hai lần tải | Lặp hoặc sót dòng | Ổn định |
| Hợp với | Admin, bảng nhỏ, cần số trang | Infinite scroll, API, feed, export |

Laravel có sẵn cả hai: `paginate()` (offset kèm `COUNT(*)`), `simplePaginate()` (offset, không đếm), và
`cursorPaginate()` (keyset, mã hoá giá trị cột sort thành chuỗi cursor). `cursorPaginate()` yêu cầu
`ORDER BY` trên cột unique hoặc tổ hợp có cột unique:

```php
<?php
declare(strict_types=1);

use App\Models\Order;

// SELECT ... ORDER BY created_at DESC, id DESC LIMIT 21 (lấy dư 1 dòng để biết còn trang sau)
$orders = Order::query()
    ->orderByDesc('created_at')
    ->orderByDesc('id')          // tie-breaker bắt buộc
    ->cursorPaginate(20);
// $orders->nextCursor() mã hoá (created_at, id) của dòng cuối; client gửi lại qua ?cursor=...
```

#### Mấy thứ hay bị hỏi

**`COUNT(*)` trên bảng lớn chậm.** MyISAM ngày xưa lưu sẵn số dòng, InnoDB thì không, vì với MVCC
(module 3.1) mỗi transaction có snapshot riêng và có thể thấy số dòng khác nhau vào cùng một thời
điểm. InnoDB đếm bằng cách quét index nhỏ nhất có sẵn (thường là một secondary index, vì nhỏ hơn
clustered index); nhanh hơn quét bảng nhưng vẫn là O(n). Cách xử lý:

- Hiện số ước lượng: `TABLE_ROWS` trong `information_schema.TABLES` (tài liệu MySQL ghi có thể lệch
  40 tới 50% so với thực tế), hoặc cột `rows` của `EXPLAIN SELECT * FROM t`.
- Bảng counter riêng cập nhật cùng transaction với insert/delete (cẩn thận: dòng counter thành điểm
  nóng tranh lock, có thể chia thành nhiều dòng rồi cộng lại).
- Đổi giao diện: "hơn 10.000 kết quả" bằng `SELECT COUNT(*) FROM (SELECT 1 FROM t WHERE ... LIMIT 10001) x`.
- `COUNT(*)` có `WHERE` trên cột có index thì chỉ đếm trong khoảng đó, không có vấn đề.

`COUNT(*)`, `COUNT(1)` như nhau trong InnoDB; `COUNT(col)` khác nghĩa (bỏ qua NULL, module 1.1).

**`SELECT *`.** Ba vấn đề:

1. Kéo cả cột lớn (`TEXT`, `JSON`, `BLOB`) mà có thể không cần: tốn I/O (cột lớn có thể lưu ở page
   riêng, phải đọc thêm), tốn băng thông mạng, tốn RAM phía PHP.
2. Không bao giờ thành covering index, vì cần mọi cột.
3. Code phụ thuộc vào thứ tự hoặc tập cột, dễ vỡ khi bảng thêm cột; view hoặc `INSERT ... SELECT *` bị
   lệch cột.

**Update hoặc delete hàng triệu dòng.** Một câu `DELETE FROM logs WHERE created_at < '2025-01-01'` xoá
10 triệu dòng trong một transaction gây ra:

- Lock trên hàng triệu dòng (và gap) suốt thời gian chạy, chặn các ghi khác.
- Undo log phình to; nếu bị kill giữa chừng, rollback có thể lâu ngang lúc chạy.
- Binlog ghi một transaction khổng lồ, replica phải áp lại đúng khối đó một lượt, gây lag nhiều phút.

Cách làm: chia batch theo PK, mỗi batch một transaction nhỏ, nghỉ giữa các batch để replica theo kịp:

```php
<?php
declare(strict_types=1);

// Chạy: php purge.php  (cần extension pdo_mysql)
$pdo = new PDO('mysql:host=127.0.0.1;dbname=learn', 'root', 'root', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);

$batchSize = 5000;
$lastId = 0;
$select = $pdo->prepare(
    'SELECT id FROM big_orders WHERE id > ? AND created_at < ? ORDER BY id LIMIT ' . $batchSize
);
$delete = $pdo->prepare('DELETE FROM big_orders WHERE id BETWEEN ? AND ? AND created_at < ?');

while (true) {
    $select->execute([$lastId, '2025-02-01']);
    /** @var list<int> $ids */
    $ids = array_map('intval', $select->fetchAll(PDO::FETCH_COLUMN));
    if ($ids === []) {
        break;
    }
    $from = $ids[0];
    $to = $ids[count($ids) - 1];
    $delete->execute([$from, $to, '2025-02-01']);   // autocommit: mỗi batch là một transaction
    $lastId = $to;
    echo "Đã xoá tới id {$to}: {$delete->rowCount()} dòng\n";
    usleep(100_000);                                 // nghỉ 100 ms cho replica và các query khác
}
```

Vì sao đi theo PK (`id > lastId`) thay vì lặp `DELETE ... LIMIT 5000`: mỗi vòng đi thẳng tới vị trí đã
xoá tới, không phải quét lại từ đầu qua các vùng đã xoá (giống lý do keyset nhanh hơn offset). Batch
1.000 tới 10.000 dòng là khoảng hay dùng; đo thời gian mỗi batch và giữ dưới vài trăm mili giây. Với
việc dọn dữ liệu cũ định kỳ trên bảng rất lớn, partition theo thời gian rồi `DROP PARTITION` còn rẻ hơn
nhiều (module 3.6).

**Tóm tắt nhanh**
- `EXPLAIN` không chạy query; nhìn `type` (`ALL`, `index` là quét hết), `key`, `key_len` (dùng tới cột
  nào của composite), `rows × filtered`, và `Extra` (`Using filesort`, `Using temporary`).
- `EXPLAIN ANALYZE` chạy thật: đọc từ node sâu nhất lên, thời gian node cha gồm cả con, `time` và `rows`
  là trung bình mỗi loop, so ước lượng với thật để tìm chỗ optimizer đoán sai.
- Plan đổi khi thống kê đổi: `ANALYZE TABLE`, histogram cho cột không index, hint là giải pháp cuối.
- MySQL có nested loop và hash join (8.0.18+), không có merge join; hash join trong query OLTP thường là
  thiếu index.
- Quy trình: tìm (slow log, performance_schema), xếp hạng theo tổng tải, `EXPLAIN ANALYZE`, sửa, đo lại;
  loại trừ lock wait, connection, buffer pool.
- Keyset pagination cần tie-breaker unique; trên MySQL viết điều kiện dạng `OR` thay cho row value.

**Nguồn**: [MySQL: EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html) ·
[MySQL: EXPLAIN / EXPLAIN ANALYZE](https://dev.mysql.com/doc/refman/8.4/en/explain.html) ·
[MySQL: Optimizer Statistics](https://dev.mysql.com/doc/refman/8.4/en/optimizer-statistics.html) ·
[MySQL: Hash Joins](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html) ·
[MySQL: Slow Query Log](https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html) ·
[MySQL: Row Constructor Expression Optimization](https://dev.mysql.com/doc/refman/8.4/en/row-constructor-optimization.html) ·
[pt-query-digest](https://docs.percona.com/percona-toolkit/pt-query-digest.html) ·
[Use The Index, Luke: No Offset](https://use-the-index-luke.com/no-offset) ·
[Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page) ·
[PostgreSQL: Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)


---

### 2.4 SQL nâng cao

Module này trả lời: làm sao tính "so với dòng khác" (xếp hạng, cộng dồn, so với hôm qua) mà không phải
tự join bảng với chính nó, làm sao duyệt dữ liệu dạng cây bằng một câu SQL, và làm sao "có thì sửa,
chưa có thì thêm" mà không bị race condition.

Dữ liệu mẫu:

```sql
USE learn;
CREATE TABLE emp (id INT PRIMARY KEY, dept VARCHAR(10), name VARCHAR(20), salary INT);
INSERT INTO emp VALUES (1,'eng','An',3000),(2,'eng','Bình',2500),(3,'eng','Chi',2500),
                       (4,'eng','Dũng',2000),(5,'ops','Em',1800),(6,'ops','Giang',1500);
CREATE TABLE sales (id INT PRIMARY KEY, day DATE, amount INT);
INSERT INTO sales VALUES (1,'2026-01-01',100),(2,'2026-01-02',50),(3,'2026-01-02',30),
                         (4,'2026-01-03',20);
```

#### Window function

*Window function* tính cho **mỗi dòng** một giá trị dựa trên một nhóm dòng liên quan tới nó (gọi là
*window*, cửa sổ). Khác biệt với `GROUP BY`: `GROUP BY` gộp mỗi nhóm thành một dòng, còn window function
giữ nguyên mọi dòng và chỉ thêm một cột. Nhờ vậy có thể đặt "lương của An" cạnh "lương trung bình phòng
của An" trong cùng một dòng. MySQL hỗ trợ từ 8.0.

```sql
SELECT name, dept, salary,
       AVG(salary) OVER (PARTITION BY dept) AS dept_avg,        -- trung bình phòng, lặp trên mỗi dòng
       salary - AVG(salary) OVER (PARTITION BY dept) AS diff
FROM emp;
```

Cú pháp đầy đủ gồm ba phần, phần nào cũng tuỳ chọn:

```
f(...) OVER (
    PARTITION BY dept          -- chia dòng thành các nhóm độc lập; không có thì cả bảng là một nhóm
    ORDER BY salary DESC       -- thứ tự các dòng trong nhóm
    ROWS BETWEEN ... AND ...   -- frame: tập dòng con mà hàm aggregate nhìn thấy (xem bên dưới)
)
```

Cách thực thi: MySQL chạy xong `FROM`, `WHERE`, `GROUP BY`, `HAVING`, rồi sort các dòng theo
`PARTITION BY` và `ORDER BY` của window, đi qua từng dòng để tính giá trị, rồi mới tới `SELECT` cuối,
`ORDER BY` và `LIMIT` (thứ tự logic ở module 1.1). Hệ quả: window function chỉ được viết trong danh sách
`SELECT` và `ORDER BY`, không dùng được trong `WHERE`, `GROUP BY`, `HAVING`.

Ba hàm xếp hạng khác nhau ở cách xử lý giá trị bằng nhau (*peers*, các dòng có cùng giá trị sort):

```sql
SELECT dept, name, salary,
       ROW_NUMBER() OVER w AS rn,
       RANK()       OVER w AS rnk,
       DENSE_RANK() OVER w AS drnk
FROM emp
WINDOW w AS (PARTITION BY dept ORDER BY salary DESC);    -- đặt tên window để dùng lại
```

```
+------+-------+--------+----+-----+------+
| dept | name  | salary | rn | rnk | drnk |
+------+-------+--------+----+-----+------+
| eng  | An    |   3000 |  1 |   1 |    1 |
| eng  | Bình  |   2500 |  2 |   2 |    2 |
| eng  | Chi   |   2500 |  3 |   2 |    2 |
| eng  | Dũng  |   2000 |  4 |   4 |    3 |
| ops  | Em    |   1800 |  1 |   1 |    1 |
| ops  | Giang |   1500 |  2 |   2 |    2 |
+------+-------+--------+----+-----+------+
```

| Hàm | Giá trị bằng nhau | Sau nhóm bằng nhau | Dùng khi |
|---|---|---|---|
| `ROW_NUMBER()` | Số khác nhau, thứ tự tuỳ ý | Liên tục | Cần đúng N dòng, khử trùng, phân trang |
| `RANK()` | Cùng hạng | Nhảy số (1, 2, 2, 4): hạng = 1 + số dòng đứng trước | Bảng xếp hạng thi đấu |
| `DENSE_RANK()` | Cùng hạng | Không nhảy (1, 2, 2, 3): hạng = số giá trị khác nhau đứng trước + 1 | "Mức lương cao thứ N" |

⚠️ Bình và Chi cùng 2500 nên `ROW_NUMBER` cho ai số 2 là không xác định; chạy lại, hoặc đổi plan, có
thể ra khác. Muốn ổn định thì thêm tie-breaker: `ORDER BY salary DESC, id`.

`LAG(col, n, default)` lấy giá trị của dòng đứng trước `n` vị trí (mặc định 1) trong cùng partition,
`LEAD` lấy dòng đứng sau. Dòng không có "hàng xóm" nhận `default` (mặc định NULL). Ví dụ so doanh thu
với hôm trước:

```sql
WITH d AS (SELECT day, SUM(amount) AS revenue FROM sales GROUP BY day)
SELECT day, revenue,
       LAG(revenue) OVER (ORDER BY day)            AS prev,
       revenue - LAG(revenue) OVER (ORDER BY day)  AS diff
FROM d;
-- 2026-01-01  100  NULL  NULL
-- 2026-01-02   80   100   -20
-- 2026-01-03   20    80   -60
```

⚠️ `LAG` lấy dòng liền trước, không phải "ngày hôm qua". Nếu thiếu dữ liệu ngày 02, dòng 03 sẽ so với
ngày 01. Báo cáo theo ngày cần sinh đủ dãy ngày trước (recursive CTE ở nhóm dưới) rồi `LEFT JOIN`.

*Frame* là phần của partition mà hàm aggregate (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`) và
`FIRST_VALUE`/`LAST_VALUE`/`NTH_VALUE` nhìn thấy khi tính cho dòng hiện tại. Các hàm xếp hạng và
`LAG`/`LEAD` bỏ qua frame. Có hai đơn vị:

- `ROWS`: đếm theo vị trí dòng. `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` là dòng hiện tại và hai dòng
  trước nó (trung bình trượt 3 ngày).
- `RANGE`: theo giá trị của cột sort. `CURRENT ROW` trong `RANGE` nghĩa là **dòng hiện tại và mọi peer
  của nó**. Với cột ngày giờ có thể viết `RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT ROW`.

Frame mặc định (theo tài liệu MySQL):

| `OVER` có | Frame mặc định | Hệ quả |
|---|---|---|
| Không có `ORDER BY` | `RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` | Cả partition: `SUM() OVER (PARTITION BY dept)` là tổng phòng |
| Có `ORDER BY` | `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | Từ đầu tới dòng hiện tại **và các peer**: running total |

⚠️ Bẫy running total "nhảy bậc": hai đơn cùng ngày 02 là peers, nên với frame mặc định cả hai cùng thấy
tổng tới hết ngày 02.

```sql
SELECT id, day, amount,
       SUM(amount) OVER (ORDER BY day)                                           AS range_default,
       SUM(amount) OVER (ORDER BY day, id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS by_row
FROM sales;
```

```
+----+------------+--------+---------------+--------+
| id | day        | amount | range_default | by_row |
+----+------------+--------+---------------+--------+
|  1 | 2026-01-01 |    100 |           100 |    100 |
|  2 | 2026-01-02 |     50 |           180 |    150 |
|  3 | 2026-01-02 |     30 |           180 |    180 |
|  4 | 2026-01-03 |     20 |           200 |    200 |
+----+------------+--------+---------------+--------+
```

Cả hai đều "đúng", tuỳ câu hỏi: "tổng lũy kế tới hết ngày" là `RANGE`, "số dư sau từng giao dịch" là
`ROWS` kèm tie-breaker. Cùng cơ chế đó, `LAST_VALUE(x) OVER (ORDER BY ...)` với frame mặc định trả về
giá trị của dòng hiện tại (hoặc peer cuối) chứ không phải dòng cuối partition; muốn dòng cuối thì ghi
`ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`, hoặc dùng `FIRST_VALUE` với sort ngược.

Lọc theo kết quả window function: vì `WHERE` chạy trước window, phải tính ở tầng trong rồi lọc ở tầng
ngoài. Top 3 đơn lớn nhất của mỗi user:

```sql
WITH ranked AS (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total DESC, id) AS rn
  FROM big_orders o
)
SELECT * FROM ranked WHERE rn <= 3;
```

- `ROW_NUMBER` cho đúng 3 dòng mỗi user. `RANK() <= 3` có thể ra nhiều hơn 3 nếu có đồng hạng, và
  `DENSE_RANK() <= 3` là "ba mức giá trị cao nhất", có thể ra rất nhiều dòng. Hỏi lại người ra đề muốn
  nghĩa nào; đó là điểm cộng.
- ⚠️ Hiệu năng: câu trên đánh số **mọi** dòng của bảng (quét và sort một triệu dòng) chỉ để giữ 3 dòng
  mỗi user. Nếu chỉ cần cho một vài user, lọc `WHERE user_id IN (...)` ở tầng trong. Khi cần cho nhiều
  user và có index `(user_id, total)`, MySQL 8.0.14+ có `LATERAL` để tra 3 dòng mỗi user bằng index:

  ```sql
  SELECT u.id, t.id AS order_id, t.total
  FROM big_users u
  JOIN LATERAL (
    SELECT id, total FROM big_orders o
    WHERE o.user_id = u.id ORDER BY total DESC LIMIT 3
  ) t ON TRUE
  WHERE u.country = 'VN';
  ```

Một số DB (Snowflake, DuckDB...) có mệnh đề `QUALIFY` để lọc window function trực tiếp; MySQL và
Postgres không có, nên luôn dùng subquery hoặc CTE.

#### CTE

*CTE* (Common Table Expression) là subquery được đặt tên bằng `WITH`, dùng như một bảng tạm chỉ tồn tại
trong một câu lệnh. Lợi ích chính là dễ đọc: logic đi từ trên xuống thay vì lồng từ trong ra.

```sql
WITH paid AS (
  SELECT user_id, SUM(total) AS spent FROM big_orders WHERE status = 'paid' GROUP BY user_id
),
vip AS (
  SELECT user_id FROM paid WHERE spent > 20000       -- CTE sau dùng được CTE trước
)
SELECT u.id, u.name, p.spent
FROM vip JOIN paid p USING (user_id) JOIN big_users u ON u.id = vip.user_id;
```

So với derived table (subquery trong `FROM`): CTE tham chiếu được nhiều lần trong cùng câu, và CTE sau
tham chiếu được CTE trước. Optimizer MySQL 8 có thể *merge* CTE vào câu ngoài (như viết thẳng) hoặc
*materialize* (tính một lần ra bảng tạm); CTE không tự động là "rào chắn tối ưu". Postgres trước bản 12
luôn materialize CTE, từ 12 thì inline nếu CTE được dùng một lần và không có tác dụng phụ; cần ép thì
viết `WITH x AS MATERIALIZED (...)`.

*Recursive CTE* dùng để duyệt dữ liệu có quan hệ tự tham chiếu: danh mục cha con, sơ đồ tổ chức, chuỗi
giới thiệu. Cấu trúc:

```sql
WITH RECURSIVE tên (cột...) AS (
  <phần gốc (anchor): không tham chiếu tên>
  UNION ALL
  <phần đệ quy: tham chiếu tên đúng một lần, trong FROM>
)
SELECT ... FROM tên;
```

Cơ chế thực thi:

1. Chạy phần gốc, được tập dòng R0. Đưa R0 vào kết quả.
2. Chạy phần đệ quy, trong đó `tên` chỉ chứa **các dòng mới của vòng trước** (không phải toàn bộ kết
   quả), được R1. Đưa R1 vào kết quả.
3. Lặp lại với R1 để ra R2, và tiếp tục cho tới khi một vòng không sinh ra dòng mới nào.

Ví dụ lấy toàn bộ cây con của danh mục "Điện tử", kèm độ sâu và đường đi:

```sql
CREATE TABLE categories (id INT PRIMARY KEY, parent_id INT NULL, name VARCHAR(50), INDEX (parent_id));
INSERT INTO categories VALUES (1,NULL,'Điện tử'),(2,1,'Điện thoại'),(3,2,'Android'),
                              (4,2,'iPhone'),(5,1,'Laptop'),(6,NULL,'Sách');

WITH RECURSIVE tree AS (
  SELECT id, name, 0 AS depth, CAST(id AS CHAR(500)) AS path
  FROM categories WHERE id = 1                                   -- R0: gốc
  UNION ALL
  SELECT c.id, c.name, t.depth + 1, CONCAT(t.path, ',', c.id)
  FROM tree t JOIN categories c ON c.parent_id = t.id            -- con của các dòng vòng trước
  WHERE t.depth < 20                                             -- chặn độ sâu
    AND FIND_IN_SET(c.id, t.path) = 0                            -- chặn vòng lặp
)
SELECT id, CONCAT(REPEAT('  ', depth), name) AS name, depth, path FROM tree ORDER BY path;
```

```
+----+----------------+-------+-------+
| id | name           | depth | path  |
+----+----------------+-------+-------+
|  1 | Điện tử        |     0 | 1     |
|  2 |   Điện thoại   |     1 | 1,2   |
|  3 |     Android    |     2 | 1,2,3 |
|  4 |     iPhone     |     2 | 1,2,4 |
|  5 |   Laptop       |     1 | 1,5   |
+----+----------------+-------+-------+
```

Vòng 0 ra `{1}`, vòng 1 ra các con của 1 là `{2, 5}`, vòng 2 ra con của 2 và 5 là `{3, 4}`, vòng 3 không
ra gì nên dừng. Đổi chiều join (`c.id = t.parent_id`) là đi ngược lên để lấy chuỗi cha tới gốc
(breadcrumb).

Các cạm bẫy:

- ⚠️ **Dữ liệu có vòng** (A là cha của B, B là cha của A, thường do bug khi sửa cây) làm phần đệ quy
  không bao giờ hết dòng. MySQL tự chặn ở `cte_max_recursion_depth` (mặc định 1000 vòng) và báo lỗi
  `ERROR 3636 ... Recursive query aborted after 1001 iterations`. Đừng dựa vào giới hạn này: tự chặn
  bằng cột `depth` và kiểm tra `path` như ví dụ. Có thể thêm `LIMIT` trong phần đệ quy (giới hạn tổng
  số dòng) hoặc hint `/*+ MAX_EXECUTION_TIME(1000) */` (mili giây). Postgres 14+ có mệnh đề `CYCLE`
  làm việc này sẵn.
- ⚠️ **Kiểu cột lấy từ phần gốc**. `path` ở phần gốc mà viết `CAST(id AS CHAR)` hoặc `'abc'` thì cột chỉ
  rộng bằng giá trị đầu tiên; `CONCAT` ở các vòng sau dài hơn sẽ lỗi `Data too long` (strict mode) hoặc
  bị cắt. Luôn `CAST(... AS CHAR(n))` đủ rộng ở phần gốc.
- Phần đệ quy không được chứa aggregate, window function, `GROUP BY`, `ORDER BY`, `DISTINCT`; `tên` chỉ
  được tham chiếu một lần và không nằm ở phía phải của `LEFT JOIN`. Aggregate thì làm ở câu `SELECT`
  cuối.
- `UNION DISTINCT` thay cho `UNION ALL` sẽ bỏ dòng trùng ở mỗi vòng, cũng là một cách chặn vòng khi dòng
  lặp lại giống hệt; nhưng có `path` hay `depth` thì dòng không còn giống hệt nên cách này không có tác
  dụng.
- Cần index trên cột join của phần đệ quy (`parent_id`), vì phần đệ quy chạy một lần mỗi tầng.

Ứng dụng khác hay dùng: sinh dãy số, dãy ngày để lấp chỗ trống trong báo cáo:

```sql
WITH RECURSIVE days (d) AS (
  SELECT DATE '2026-01-01'
  UNION ALL
  SELECT d + INTERVAL 1 DAY FROM days WHERE d < '2026-01-05'
)
SELECT days.d, COALESCE(SUM(s.amount), 0) AS revenue
FROM days LEFT JOIN sales s ON s.day = days.d
GROUP BY days.d ORDER BY days.d;      -- ngày 04, 05 hiện 0 thay vì biến mất
```

Cây sâu, đọc rất nhiều (menu danh mục trên mọi trang) thì recursive CTE mỗi request có thể là quá tốn;
các cách lưu cây khác (materialized path, closure table) là chủ đề thiết kế schema ở module 2.8.

#### UPSERT

*UPSERT* (update + insert) là "có rồi thì cập nhật, chưa có thì thêm mới", thực hiện trong **một câu
lệnh atomic**. "Có rồi" được xác định bằng xung đột trên `PRIMARY KEY` hoặc `UNIQUE` index; không có
unique index thì không có upsert.

Vì sao không viết SELECT rồi mới INSERT hoặc UPDATE ở app:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `SELECT ... WHERE user_id=1 AND product_id=100` | | Không có dòng |
| 2 | | `SELECT ... WHERE user_id=1 AND product_id=100` | Không có dòng |
| 3 | `INSERT ... (1, 100, 2)` | | Thành công |
| 4 | | `INSERT ... (1, 100, 1)` | Có unique: lỗi duplicate key, request B trả 500. Không có unique: hai dòng trùng |

Transaction Repeatable Read không cứu được: `SELECT` thường đọc snapshot, không lock gì cả (module 2.5).

MySQL viết `INSERT ... ON DUPLICATE KEY UPDATE`:

```sql
CREATE TABLE cart_items (
  user_id BIGINT, product_id BIGINT, qty INT NOT NULL,
  PRIMARY KEY (user_id, product_id));

INSERT INTO cart_items (user_id, product_id, qty) VALUES (1, 100, 2) AS new
ON DUPLICATE KEY UPDATE qty = cart_items.qty + new.qty;
-- chạy lần 1: thêm dòng (qty = 2); lần 2: qty = 4
```

- `AS new` (từ 8.0.19) đặt tên cho dòng định chèn, để vế `UPDATE` tham chiếu `new.qty`. Cách cũ
  `VALUES(qty)` đã deprecated từ 8.0.20 và sẽ bị bỏ; code cũ và nhiều bài blog vẫn dùng. Có thể đặt cả
  tên cột: `AS new(u, p, q) ... UPDATE qty = qty + q`.
- Nhiều dòng một lúc: `VALUES (1,100,2),(1,101,1) AS new ON DUPLICATE KEY UPDATE ...`.
- *Affected rows* báo điều gì đã xảy ra: 1 là thêm mới, 2 là đã cập nhật dòng có sẵn, 0 là dòng có sẵn
  và giá trị không đổi. PDO có thể được cấu hình cờ `CLIENT_FOUND_ROWS` (`PDO::MYSQL_ATTR_FOUND_ROWS`),
  khi đó trường hợp cuối trả 1.

Các cạm bẫy:

- ⚠️ **Bảng có nhiều unique key**. Bảng `users` có `UNIQUE(email)` và `UNIQUE(username)`; chèn một dòng
  trùng email với user 5 và trùng username với user 9. MySQL chỉ cập nhật **một** dòng (tài liệu mô tả
  như `UPDATE ... WHERE email=... OR username=... LIMIT 1`), và không nói trước là dòng nào. Tài liệu
  khuyên tránh dùng `ON DUPLICATE KEY UPDATE` trên bảng có nhiều unique index.
- ⚠️ **Auto-increment bị tiêu**. InnoDB cấp id trước khi biết có trùng hay không; nhánh update vẫn làm
  mất một giá trị. Bảng upsert liên tục thì id nhảy cóc rất nhanh (kèm rollback, insert lỗi cũng tạo
  "lỗ"). Đây là chuyện bình thường; đừng viết code giả định id liên tục hay dùng `MAX(id)` để đếm, và
  đây là thêm một lý do dùng `BIGINT` cho id (module 1.4).
- **Lock**: khi gặp trùng, InnoDB đặt lock exclusive lên index record bị trùng (next-key lock nếu là
  unique key phụ), nên nhiều upsert đồng thời trên cùng vùng key có thể deadlock (module 3.2).
- `INSERT ... SELECT ... ON DUPLICATE KEY UPDATE` bị coi là không an toàn với statement-based
  replication vì thứ tự dòng của `SELECT` không xác định.
- Hai lựa chọn khác trông giống nhưng nguy hiểm hơn:
  - `REPLACE INTO` gặp trùng thì **xoá dòng cũ rồi chèn dòng mới**: cột không nêu tên bị về mặc định,
    FK `ON DELETE CASCADE` xoá luôn dữ liệu con, trigger delete chạy, và nếu không truyền id thì dòng mới nhận id auto-increment mới.
  - `INSERT IGNORE` bỏ qua dòng trùng, nhưng cũng biến nhiều lỗi khác (dữ liệu quá dài, sai kiểu) thành
    warning và lưu giá trị đã bị cắt, tức tắt strict mode cho câu lệnh đó.

Đối chiếu Postgres: `ON CONFLICT ... DO UPDATE` bắt buộc chỉ rõ xung đột trên cột hoặc constraint nào,
nên không có bẫy nhiều unique key (`DO NOTHING` thì được bỏ trống); `EXCLUDED` là dòng định chèn.

```sql
-- Postgres
INSERT INTO cart_items (user_id, product_id, qty) VALUES (1, 100, 2)
ON CONFLICT (user_id, product_id) DO UPDATE SET qty = cart_items.qty + EXCLUDED.qty;
-- hoặc ON CONFLICT DO NOTHING
```

Ở Laravel:

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

// Sinh ra INSERT ... ON DUPLICATE KEY UPDATE trên MySQL, ON CONFLICT trên Postgres
DB::table('cart_items')->upsert(
    [['user_id' => 1, 'product_id' => 100, 'qty' => 2]],
    ['user_id', 'product_id'],   // uniqueBy: MySQL bỏ qua tham số này, dùng mọi PK/unique của bảng
    ['qty'],                     // cột được cập nhật khi trùng (ghi đè, không cộng dồn)
);
```

⚠️ `Model::updateOrCreate()` và `firstOrCreate()` của Eloquent là SELECT rồi INSERT ở app, **không phải
một câu atomic**. Ở Laravel 10.x trở về sau, khi SELECT không thấy dòng, `firstOrCreate()` gọi
`createOrFirst()`: thử INSERT, gặp lỗi unique thì SELECT lại dòng vừa được request khác chèn
(`updateOrCreate()` đi qua `firstOrCreate()` nên cũng vậy). Cơ chế này **chỉ an toàn khi có unique
index** trên các cột tra cứu; không có unique index thì dưới tải đồng thời vẫn có race như bảng
timeline ở trên và sinh dòng trùng. Bản Laravel cũ hơn không có bước này, request thua nhận lỗi
duplicate key.

#### Các bài kinh điển nên tự viết được

Các bài này xuất hiện liên tục trong vòng live coding. Mỗi bài dưới đây nêu kỹ thuật; hãy tự gõ lại
trên dữ liệu mẫu cho tới khi không cần nhìn.

**Top N mỗi nhóm**: `ROW_NUMBER() OVER (PARTITION BY nhóm ORDER BY tiêu chí DESC, id)` trong CTE, lọc
`rn <= N` ở ngoài (nhóm Window function ở trên). Nhớ hỏi cách xử lý đồng hạng.

**Running total**: `SUM(x) OVER (ORDER BY thời_gian, id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT
ROW)`; thêm `PARTITION BY` để cộng dồn riêng cho từng tài khoản.

**Tìm và xoá bản ghi trùng**: tìm bằng `GROUP BY` có `HAVING COUNT(*) > 1`, xoá bằng `ROW_NUMBER` để
giữ lại một dòng mỗi nhóm:

```sql
CREATE TABLE subscribers (id INT PRIMARY KEY, email VARCHAR(100));
INSERT INTO subscribers VALUES (1,'a@x.com'),(2,'b@x.com'),(3,'a@x.com'),(4,'a@x.com');

SELECT email, COUNT(*) FROM subscribers GROUP BY email HAVING COUNT(*) > 1;   -- a@x.com, 3

DELETE s FROM subscribers s
JOIN (
  SELECT id, ROW_NUMBER() OVER (PARTITION BY email ORDER BY id) AS rn FROM subscribers
) d ON d.id = s.id
WHERE d.rn > 1;                                          -- giữ id 1, xoá id 3 và 4

ALTER TABLE subscribers ADD UNIQUE (email);              -- chặn trùng từ gốc
```

MySQL không cho `DELETE FROM t WHERE id IN (SELECT ... FROM t ...)` trực tiếp trên cùng bảng (lỗi
1093); join với derived table như trên thì được vì derived table được tính ra trước. Bảng lớn thì xoá
theo batch (module 2.3). Việc xoá xong mà không thêm unique constraint thì trùng sẽ quay lại.

**Gaps and islands**: tìm các "đảo" là chuỗi giá trị liên tiếp, ví dụ chuỗi ngày đăng nhập liên tục.
Mẹo: trong một chuỗi ngày liên tiếp, ngày tăng 1 và `ROW_NUMBER` cũng tăng 1, nên **hiệu của chúng
không đổi** trong cả chuỗi và đổi khi có khoảng trống. Hiệu đó làm khoá nhóm:

```sql
CREATE TABLE logins (user_id INT, login_date DATE);
INSERT INTO logins VALUES (1,'2026-01-01'),(1,'2026-01-02'),(1,'2026-01-02'),(1,'2026-01-03'),
                          (1,'2026-01-05'),(1,'2026-01-06'),(2,'2026-01-01');

WITH d AS (SELECT DISTINCT user_id, login_date FROM logins),          -- một ngày đăng nhập nhiều lần
g AS (
  SELECT user_id, login_date,
         login_date - INTERVAL ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) DAY AS grp
  FROM d
)
SELECT user_id, MIN(login_date) AS start_day, MAX(login_date) AS end_day, COUNT(*) AS days
FROM g GROUP BY user_id, grp ORDER BY user_id, start_day;
```

```
login_date   rn   grp            đảo
2026-01-01    1   2025-12-31     A
2026-01-02    2   2025-12-31     A
2026-01-03    3   2025-12-31     A
2026-01-05    4   2026-01-01     B   (khoảng trống ngày 04 làm grp đổi)
2026-01-06    5   2026-01-01     B
```

Kết quả: user 1 có đảo 01 tới 03 (3 ngày) và 05 tới 06 (2 ngày), user 2 có một đảo 1 ngày. ⚠️ Bước
`DISTINCT` là bắt buộc: hai lần đăng nhập ngày 02 sẽ làm `rn` tăng mà ngày không tăng, phá khoá nhóm.
Từ kết quả này, "chuỗi dài nhất của mỗi user" chỉ cần thêm một tầng nữa; phần đó để bạn tự viết.
Cách khác: dùng `LAG` để đánh dấu dòng bắt đầu đảo mới (ngày khác ngày trước + 1), rồi `SUM` cộng dồn
các dấu đó thành số thứ tự đảo.

**Giá trị lớn thứ N** (ví dụ mức lương cao thứ 2):

```sql
-- Cách 1: DENSE_RANK, đúng nghĩa "mức thứ N" khi có giá trị trùng
SELECT DISTINCT salary FROM (
  SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS r FROM emp
) t WHERE r = 2;                                                    -- 2500
-- Cách 2: DISTINCT + OFFSET; bọc làm scalar subquery để trả NULL khi không có mức thứ N
SELECT (SELECT DISTINCT salary FROM emp ORDER BY salary DESC LIMIT 1 OFFSET 1) AS second_highest;
```

⚠️ Bỏ `DISTINCT` ở cách 2 thì 3000, 2500, 2500 cho ra "thứ 3" là 2500, sai nghĩa "mức lương". Thứ N
trong từng phòng thì thêm `PARTITION BY dept`, và đó là lúc cách 1 thắng rõ.

**Tóm tắt nhanh**
- Window function giữ nguyên dòng, tính theo `PARTITION BY` và `ORDER BY`; chạy sau `WHERE`/`HAVING` nên
  lọc kết quả của nó phải bọc CTE hoặc subquery.
- `ROW_NUMBER` 1,2,3,4; `RANK` 1,2,2,4; `DENSE_RANK` 1,2,2,3. Thêm tie-breaker để kết quả ổn định.
- Có `ORDER BY` trong `OVER` thì frame mặc định là `RANGE ... CURRENT ROW`, gộp các peer; running total
  từng dòng cần `ROWS`.
- Recursive CTE: gốc `UNION ALL` phần đệ quy; mỗi vòng chỉ thấy dòng mới của vòng trước; chặn độ sâu và
  vòng lặp, `CAST` cột chuỗi đủ rộng ở phần gốc.
- Upsert MySQL: `INSERT ... AS new ON DUPLICATE KEY UPDATE`; bẫy nhiều unique key, auto-increment bị
  tiêu, `REPLACE` là delete + insert; `updateOrCreate` của Laravel không atomic.
- Gaps and islands: `ngày - ROW_NUMBER` không đổi trong một chuỗi liên tiếp.

**Nguồn**: [MySQL: Window Functions](https://dev.mysql.com/doc/refman/8.4/en/window-functions.html) ·
[MySQL: Window Function Frame Specification](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html) ·
[MySQL: WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.4/en/with.html) ·
[MySQL: INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html) ·
[modern-sql.com](https://modern-sql.com/) ·
[Laravel: Upserts](https://laravel.com/docs/queries#upserts)


---

### 2.5 Isolation level và anomaly

Module này trả lời: khi nhiều transaction chạy cùng lúc thì DB để lọt những kiểu sai nào, mỗi
isolation level chặn được kiểu nào, và vì sao Repeatable Read mặc định của MySQL vẫn để mất tiền
nếu code viết theo kiểu "đọc, tính ở app, rồi ghi".

Dữ liệu mẫu cho cả module 2.5 và 2.6. Mọi timeline bên dưới đều chạy lại từ dữ liệu này, mỗi bên
một terminal `mysql`:

```sql
CREATE DATABASE IF NOT EXISTS learn; USE learn;
DROP TABLE IF EXISTS products, accounts, doctors;
CREATE TABLE products (id BIGINT PRIMARY KEY, name VARCHAR(50), price INT NOT NULL, stock INT NOT NULL);
INSERT INTO products VALUES (1, 'Bàn phím', 100, 1), (2, 'Chuột', 50, 10);
CREATE TABLE accounts (id BIGINT PRIMARY KEY, balance DECIMAL(12,2) NOT NULL);
INSERT INTO accounts VALUES (1, 100), (2, 100);
CREATE TABLE doctors (id BIGINT PRIMARY KEY, name VARCHAR(20), shift_id INT NOT NULL,
  on_call BOOLEAN NOT NULL, KEY idx_shift (shift_id));
INSERT INTO doctors VALUES (1, 'Alice', 1, TRUE), (2, 'Bob', 1, TRUE);

-- Xem và đổi isolation level của session hiện tại
SELECT @@transaction_isolation;                              -- REPEATABLE-READ
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;      -- cho mọi transaction sau của session
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;                -- chỉ cho transaction KẾ TIẾP
```

⚠️ `SET TRANSACTION` không có chữ `SESSION` chỉ áp dụng cho đúng một transaction kế tiếp, rồi quay
về mức của session. Nhiều người thử nghiệm sai vì tưởng nó đổi luôn cả session. Biến cũ
`tx_isolation` đã bị bỏ ở MySQL 8.0; dùng `transaction_isolation`.

#### Anomaly là gì

Lý tưởng của isolation là *serializability*: kết quả của một nhóm transaction chạy đồng thời phải
giống như khi chúng chạy lần lượt từng cái, theo một thứ tự nào đó. Mọi kết quả không thể có được
bằng bất kỳ thứ tự tuần tự nào gọi là *anomaly* (hiện tượng bất thường). DB mặc định không đảm bảo
serializable vì phải trả giá bằng khoá nhiều hơn hoặc huỷ transaction nhiều hơn, nên nó chấp nhận
để lọt một số anomaly. Việc của developer là biết anomaly nào lọt ở mức mình đang dùng.

| Anomaly | Định nghĩa bằng lời thường | Ví dụ | Tên trong tài liệu |
|---|---|---|---|
| Dirty write | Ghi đè lên dữ liệu transaction khác **chưa commit** | Hai transaction cùng sửa một dòng xen kẽ, rollback bên nào cũng hỏng | P0, G0 |
| Dirty read | Đọc dữ liệu transaction khác chưa commit | Thấy số dư đã trừ, rồi transaction kia rollback | P1, G1a/G1b |
| Non-repeatable read | Đọc cùng một dòng hai lần, lần sau khác lần trước vì có người commit ở giữa | Đọc giá 100, người khác sửa thành 120, đọc lại ra 120 | P2 |
| Phantom | Chạy lại cùng một điều kiện, tập dòng khớp thay đổi (thêm hoặc mất dòng) | Đếm đơn hôm nay ra 10, đếm lại ra 11 | P3 |
| Read skew | Đọc hai dòng liên quan ở hai thời điểm khác nhau, thấy trạng thái không bao giờ tồn tại | Tổng hai tài khoản lệch vì đọc đúng lúc đang chuyển tiền | A5A, G-single |
| Lost update | Hai transaction cùng đọc, sửa ở app, ghi lại; bản ghi sau đè mất bản trước | Hai người cùng rút và nạp tiền, một thao tác biến mất | P4 |
| Write skew | Hai transaction đọc cùng một tập dữ liệu, mỗi bên ghi một dòng **khác nhau**, gộp lại vi phạm ràng buộc | Hai bác sĩ cùng xin nghỉ vì đều thấy vẫn còn người trực | A5B, G2-item |

Cột cuối là mã dùng trong bài *A Critique of ANSI SQL Isolation Levels* (Berenson và cộng sự, 1995)
và trong bảng Hermitage. Bài báo 1995 chỉ ra rằng chuẩn ANSI SQL định nghĩa isolation level qua
đúng ba hiện tượng P1, P2, P3 bằng lời văn mơ hồ, và thiếu hẳn dirty write, lost update, read skew,
write skew. Hệ quả thực tế: tên level như "Repeatable Read" ở hai DB khác nhau có thể đảm bảo những
điều khác nhau. [Hermitage](https://github.com/ept/hermitage) (Kleppmann) sinh ra để đo đúng điều
này: mỗi anomaly là một kịch bản hai hoặc ba session gõ tay, chạy trên từng DB, từng level.

Hai ý để phân biệt các anomaly khi bị hỏi:

- Non-repeatable read và phantom là chuyện của **đọc**: một dòng đổi giá trị, hoặc tập dòng khớp điều
  kiện đổi thành viên. Read skew là non-repeatable read nhìn từ góc "hai dòng liên quan".
- Lost update và write skew là chuyện của **đọc rồi quyết định ghi**. Lost update là hai bên ghi cùng
  một dòng; write skew là hai bên ghi hai dòng khác nhau, nên mọi cơ chế chỉ phát hiện xung đột trên
  cùng một dòng đều bỏ sót nó.

Dirty write bị chặn ở mọi level của cả MySQL lẫn Postgres, vì mọi câu ghi đều lấy khoá dòng và giữ
tới lúc commit: transaction thứ hai muốn sửa cùng dòng phải chờ (Hermitage test G0).

#### Isolation level

Isolation level là mức DB cam kết chặn anomaly; mức càng cao càng ít anomaly nhưng càng nhiều chờ
khoá hoặc lỗi phải retry. Chuẩn SQL có bốn mức: Read Uncommitted, Read Committed (RC), Repeatable
Read (RR), Serializable. MySQL InnoDB mặc định RR; Postgres mặc định RC (Read Uncommitted của
Postgres chạy y như RC).

Cách mỗi DB hiện thực mới là điều quyết định. InnoDB và Postgres đều dùng *MVCC* (multi-version
concurrency control: giữ nhiều phiên bản của mỗi dòng để người đọc không phải chờ người ghi, chi tiết
ở module 3.1). Khác nhau ở thời điểm chụp *snapshot*, tức "ảnh chụp" tập dữ liệu đã commit mà một
câu đọc được thấy:

| Level | Snapshot cho `SELECT` thường | Ghi chú InnoDB | Ghi chú Postgres |
|---|---|---|---|
| Read Uncommitted | Không dùng snapshot, đọc cả bản chưa commit | Có dirty read | Không có dirty read, chạy như RC |
| Read Committed | Mới cho **mỗi câu lệnh** | Không dùng gap lock (trừ kiểm tra FK và duplicate key) | Mặc định |
| Repeatable Read | Chụp ở **lần đọc đầu tiên** của transaction, dùng tới cuối | Mặc định; locking read dùng next-key lock | Snapshot isolation; ghi đụng dòng đã bị sửa thì lỗi 40001 |
| Serializable | InnoDB: như RR nhưng biến `SELECT` thường thành `FOR SHARE` (khi autocommit tắt, ví dụ trong `START TRANSACTION`) | Chặn bằng khoá, hay ra deadlock 1213 | SSI: theo dõi phụ thuộc, huỷ bằng lỗi 40001 |

Bảng anomaly theo từng DB, đã đối chiếu với kết quả Hermitage:

| Anomaly | MySQL RC | MySQL RR (mặc định) | MySQL Serializable | PG RC (mặc định) | PG RR | PG Serializable |
|---|---|---|---|---|---|---|
| Dirty read | Chặn | Chặn | Chặn | Chặn | Chặn | Chặn |
| Non-repeatable read, read skew | Lọt | Chặn nếu transaction chỉ đọc; lọt khi trộn với câu ghi | Chặn | Lọt | Chặn | Chặn |
| Phantom (với `SELECT` thường) | Lọt | Chặn nếu chỉ đọc; lọt khi trộn với câu ghi | Chặn | Lọt | Chặn | Chặn |
| Lost update | Lọt | **Lọt** | Chặn (deadlock 1213) | Lọt | Chặn (lỗi 40001) | Chặn (lỗi 40001) |
| Write skew | Lọt | Lọt | Chặn (deadlock 1213) | Lọt | Lọt | Chặn (lỗi 40001) |

Hermitage xếp RR của MySQL vào cùng nhóm "monotonic atomic view" với RC, tức yếu hơn *snapshot
isolation* mà RR của Postgres đạt được. Lý do nằm ở nhóm tiếp theo.

⚠️ Điểm hay bị hỏi vặn: snapshot của RR được chụp ở **câu đọc đầu tiên**, không phải ở `START
TRANSACTION`. Nếu session khác commit sau khi bạn `START TRANSACTION` nhưng trước câu `SELECT` đầu
tiên, bạn vẫn thấy thay đổi đó. Muốn chụp ngay lúc bắt đầu thì dùng
`START TRANSACTION WITH CONSISTENT SNAPSHOT;` (mysqldump `--single-transaction` dùng đúng câu này).
Postgres tương tự: snapshot chụp ở câu lệnh đầu tiên không phải lệnh điều khiển transaction.

Timeline 1: non-repeatable read ở RC. B mở transaction tường minh để thấy rõ lúc chưa commit và
lúc đã commit.

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 0 | `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;` | | |
| 1 | `START TRANSACTION;` `SELECT price FROM products WHERE id = 1;` | | A thấy 100 |
| 2 | | `START TRANSACTION;` `UPDATE products SET price = 120 WHERE id = 1;` | B đã sửa nhưng chưa commit |
| 3 | `SELECT price FROM products WHERE id = 1;` | | Vẫn 100: RC không có dirty read |
| 4 | | `COMMIT;` | |
| 5 | `SELECT price FROM products WHERE id = 1;` | | **120**: cùng một câu, trong cùng transaction, ra hai kết quả |
| 6 | `COMMIT;` | | |

Chạy lại với A ở RR (bỏ bước 0, hoặc `SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;`):
bước 5 vẫn ra 100, vì A đọc từ snapshot chụp ở bước 1. Chỉ sau khi A commit và mở transaction mới,
A mới thấy 120. Đổi lại RC có lợi: mỗi câu thấy dữ liệu mới nhất, ít gap lock hơn nên ít chờ và ít
deadlock hơn; nhiều hệ thống lớn chạy MySQL ở RC có chủ đích. ⚠️ MySQL ở RC chỉ hỗ trợ binlog dạng
row-based (`binlog_format = ROW`, là mặc định; nếu đặt `MIXED` thì server tự ghi dạng row), điểm này
quan trọng với replication (module 3.4).

Read skew là cùng cơ chế ở hai dòng: ở RC, A đọc tài khoản 1 được 100; B chuyển 50 từ tài khoản 1
sang 2 rồi commit; A đọc tài khoản 2 được 150. A thấy tổng 250 trong khi tổng thật chưa bao giờ khác
200. Với báo cáo, backup, hay bất kỳ việc gì đọc nhiều dòng cần nhất quán với nhau, chạy ở RR hoặc
dùng một câu lệnh duy nhất.

#### MySQL RR thật ra hoạt động thế nào

InnoDB có hai kiểu đọc, và chúng nhìn thấy hai "thế giới" khác nhau ngay trong một transaction:

1. **Consistent read** (đọc nhất quán, không khoá): là `SELECT` thường. Ở RR nó đọc từ snapshot của
   transaction. Nó không lấy khoá và cũng không chờ khoá của ai: nếu dòng đang bị người khác sửa,
   InnoDB dựng lại phiên bản cũ từ undo log.
2. **Locking read** (đọc có khoá): `SELECT ... FOR UPDATE`, `SELECT ... FOR SHARE`, và phần tìm dòng
   của `UPDATE`, `DELETE`. Kiểu này đọc **phiên bản mới nhất đã commit**, không phải snapshot, rồi
   khoá dòng tìm được. Nếu dòng đang bị khoá thì chờ.

Lý do phải như vậy: không thể ghi đè lên một phiên bản cũ. Muốn sửa dòng thì phải sửa bản mới nhất.
Tài liệu MySQL mô tả rõ hệ quả: `SELECT` không thấy dòng mà session khác vừa commit, nhưng `UPDATE`
hay `DELETE` thì vẫn chạm vào chúng, và sau khi chạm thì chính dòng đó trở nên nhìn thấy được với
`SELECT` tiếp theo của transaction. Tài liệu khuyên không nên trộn câu có khoá với `SELECT` không khoá
trong một transaction RR.

Timeline 2: "phantom" xuất hiện ở RR khi trộn hai kiểu đọc.

| Bước | Session A (RR) | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT id, price FROM products WHERE price >= 100;` | | 1 dòng: id 1 (100) |
| 2 | | `INSERT INTO products VALUES (3, 'Màn hình', 300, 5);` | Autocommit, B commit ngay |
| 3 | `SELECT id, price FROM products WHERE price >= 100;` | | Vẫn 1 dòng: đọc từ snapshot, không phantom |
| 4 | `UPDATE products SET price = price + 10 WHERE price >= 100;` | | `Rows matched: 2  Changed: 2`: UPDATE đọc bản mới nhất nên chạm cả id 3 |
| 5 | `SELECT id, price FROM products WHERE price >= 100;` | | **2 dòng**: id 1 (110), id 3 (310). Dòng 3 hiện ra vì giờ nó là phiên bản do chính A tạo |
| 6 | `COMMIT;` | | |

Bước 3 cho thấy RR chặn phantom với `SELECT` thường. Bước 4 và 5 cho thấy nó không chặn được khi
transaction có ghi. Cách chặn phantom thật sự ở InnoDB là dùng locking read ngay từ đầu:

| Bước | Session A (RR) | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT id, price FROM products WHERE price >= 100 FOR UPDATE;` | | 1 dòng; A giữ *next-key lock* |
| 2 | | `INSERT INTO products VALUES (3, 'Màn hình', 300, 5);` | **B chờ** |
| 3 | `UPDATE products SET price = price + 10 WHERE price >= 100;` `COMMIT;` | | Chỉ id 1 bị sửa. B được chạy tiếp và chèn id 3 với giá 300 |

*Next-key lock* là khoá trên một bản ghi index cộng với "khe" (gap) ngay trước nó; khoá khe ngăn
người khác chèn dòng mới vào khoảng đã quét. Ở đây cột `price` không có index nên InnoDB quét cả
clustered index và khoá mọi dòng cùng mọi khe, tức B không chèn được dòng nào cả; nếu có index trên
`price` thì chỉ các bản ghi và khe của index trong vùng đã quét (quanh `price >= 100`) bị khoá. Cơ chế gap lock đi sâu ở module 3.2. Ở RC không có gap
lock, nên cùng timeline này B chèn được ngay và câu `FOR UPDATE` thứ hai của A sẽ thấy phantom.

Hermitage còn một ví dụ kỳ quặc hơn cho thấy vì sao RR của MySQL không phải snapshot isolation: T1
đọc dòng 1 (thấy 10), T2 sửa dòng 1 thành 12 và dòng 2 từ 20 thành 18 rồi commit; T1 chạy
`DELETE FROM test WHERE value = 20` thì không xoá gì (vì bản mới nhất là 18), nhưng ngay sau đó
`SELECT * FROM test WHERE id = 2` vẫn trả về 20. Cùng một transaction vừa "thấy" vừa "không thấy" giá
trị 20. Postgres RR ở tình huống này báo lỗi 40001 thay vì lặng lẽ cho kết quả mâu thuẫn.

Timeline 3: lost update ở MySQL RR. Tài khoản 1 có 100; A rút 30, B nạp 50, đúng ra phải còn 120.

| Bước | Session A (RR) | Session B (RR) | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 1;` | | A thấy 100 |
| 2 | | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 1;` | B cũng thấy 100 |
| 3 | App tính 100 - 30. `UPDATE accounts SET balance = 70 WHERE id = 1;` | | A giữ khoá X dòng 1 |
| 4 | | App tính 100 + 50. `UPDATE accounts SET balance = 150 WHERE id = 1;` | B chờ khoá của A |
| 5 | `COMMIT;` | | B được chạy tiếp, **không lỗi**, ghi 150 |
| 6 | | `COMMIT;` | Số dư 150. Khoản rút 30 biến mất |

Lỗi không nằm ở việc B ghi được, mà ở chỗ giá trị B ghi được tính từ snapshot đã cũ. InnoDB không
kiểm tra "dòng mình định ghi có bị ai sửa từ lúc mình đọc không"; nó chỉ bắt B chờ khoá rồi ghi.

Timeline 3b: cùng kịch bản trên Postgres RR (`BEGIN ISOLATION LEVEL REPEATABLE READ;` ở cả hai bên).

| Bước | Session A (PG RR) | Session B (PG RR) | Kết quả |
|---|---|---|---|
| 1-4 | Như trên | Như trên | B chờ khoá của A ở bước 4 |
| 5 | `COMMIT;` | | B nhận `ERROR: could not serialize access due to concurrent update` (SQLSTATE 40001) |
| 6 | | `ROLLBACK;` rồi chạy lại cả transaction | Lần chạy lại chụp snapshot mới, thấy 70, ghi 120. Đúng |

Postgres RR có quy tắc: một câu ghi gặp dòng đã bị transaction khác sửa và commit sau khi snapshot
của mình được chụp thì không được ghi đè, mà huỷ cả transaction. Còn ở Postgres RC thì hành vi giống
MySQL: B chờ rồi ghi đè (Hermitage test P4). Và ở MySQL Serializable, bước 1 và 2 trở thành
`FOR SHARE`, cả hai cùng giữ khoá S; bước 3 A chờ B, bước 4 B chờ A, InnoDB phát hiện deadlock và huỷ
một bên với lỗi 1213. Cũng an toàn, nhưng trả giá bằng khoá.

#### Bốn cách chống lost update

1. **Update atomic có điều kiện**: đưa phép tính vào câu SQL để DB tính trên bản mới nhất, dưới khoá.

   ```sql
   UPDATE accounts SET balance = balance - 30 WHERE id = 1 AND balance >= 30;
   -- Kiểm tra affected rows: 1 là thành công, 0 là không đủ tiền (hoặc không có dòng)
   ```

   Ở MySQL (mọi level), nếu hai câu này chạy đồng thời, câu thứ hai chờ khoá rồi đọc lại bản mới nhất
   đã commit (vì `UPDATE` là locking read), nên kết quả đúng. Ở Postgres RC cũng đúng: sau khi chờ,
   Postgres đánh giá lại `WHERE` trên phiên bản mới của dòng. ⚠️ Nhưng ở Postgres RR và Serializable,
   câu thứ hai **báo lỗi 40001** thay vì chạy tiếp, nên vẫn cần retry. Đây là lựa chọn đầu tiên khi
   logic gói gọn được trong một câu SQL.
2. **Pessimistic lock**: `SELECT ... FOR UPDATE` trong transaction. Câu này đọc bản mới nhất và khoá
   dòng, người thứ hai chờ ngay ở bước đọc, nên dữ liệu app dùng để tính chắc chắn còn đúng lúc ghi.
   Dùng khi logic phức tạp, phải tính ở app (kiểm tra hạn mức, gọi nhiều bảng). Chi tiết ở 2.6.
3. **Optimistic lock**: không khoá, ghi kèm điều kiện `WHERE version = ?`, 0 dòng bị ảnh hưởng tức là
   có người ghi trước (module 2.6).
4. **Isolation level cao hơn kèm retry**: Postgres RR hoặc Serializable tự phát hiện và huỷ; MySQL
   Serializable chặn bằng khoá và deadlock. Cả hai đều bắt buộc app phải retry.

⚠️ Hai cách hay bị nêu nhưng **không** chống được lost update ở MySQL: chuyển sang RR (vì đã là mặc
định và vẫn lọt, timeline 3), và dùng `SELECT ... FOR SHARE` rồi `UPDATE` (hai bên cùng giữ khoá S,
cùng xin nâng lên X, ra deadlock; tài liệu MySQL khuyên dùng `FOR UPDATE` cho mẫu đọc rồi tăng bộ
đếm).

Retry trong Laravel: `DB::transaction()` nhận tham số thứ hai là số lần thử, **mặc định là 1**, tức
không retry. Laravel coi exception là lỗi đồng thời và thử lại khi mã SQLSTATE là `40001` (cả
deadlock 1213 của MySQL lẫn serialization failure của Postgres đều mang mã này) hoặc thông điệp chứa
"Deadlock found" hay "Lock wait timeout exceeded".

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

function withdraw(int $accountId, string $amount): void
{
    // Thử tối đa 3 lần nếu gặp deadlock / serialization failure; mỗi lần là transaction mới
    DB::transaction(function () use ($accountId, $amount): void {
        $affected = DB::update(
            'UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?',
            [$amount, $accountId, $amount],
        );
        if ($affected !== 1) {
            throw new DomainException('Không đủ số dư');
        }
        DB::insert('INSERT INTO ledger (account_id, amount) VALUES (?, ?)', [$accountId, $amount]);
    }, 3);
}
```

⚠️ Retry phải chạy lại **cả transaction từ đầu**, kể cả các câu đọc, vì lần chạy lại cần snapshot
mới. Code bên trong closure vì thế không được có tác dụng phụ ra ngoài DB (gửi email, gọi API), nếu
không mỗi lần retry lại gửi một lần.

#### Write skew

Bài kinh điển trong DDIA: bệnh viện yêu cầu mỗi ca trực luôn có ít nhất một bác sĩ. Alice và Bob
đang cùng trực ca 1, cả hai cùng thấy mệt và bấm "xin nghỉ" gần như cùng lúc. Code của nút này: đếm
số bác sĩ đang trực, nếu còn ít nhất 2 thì cho người bấm nghỉ.

Timeline 4: write skew ở MySQL RR (Postgres RR cho kết quả y hệt, Hermitage test G2-item).

| Bước | Session A (Alice, RR) | Session B (Bob, RR) | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT COUNT(*) FROM doctors WHERE shift_id = 1 AND on_call = TRUE;` | | A thấy 2 |
| 2 | | `START TRANSACTION;` `SELECT COUNT(*) FROM doctors WHERE shift_id = 1 AND on_call = TRUE;` | B thấy 2 |
| 3 | App: 2 ≥ 2, cho nghỉ. `UPDATE doctors SET on_call = FALSE WHERE id = 1;` | | A khoá dòng 1 |
| 4 | | App: 2 ≥ 2, cho nghỉ. `UPDATE doctors SET on_call = FALSE WHERE id = 2;` | Không chờ: dòng 2 không ai khoá |
| 5 | `COMMIT;` | `COMMIT;` | Cả hai thành công. Ca 1 không còn ai trực |

Mỗi transaction, nếu chạy một mình, đều đúng. Không có dòng nào bị ghi đè, nên cả bốn cách chống
lost update ở dạng "phát hiện xung đột trên cùng một dòng" đều không bắt được. Cấu trúc chung của
write skew theo DDIA:

1. Một câu `SELECT` kiểm tra điều kiện (còn ít nhất 2 người trực, phòng chưa có ai đặt, username chưa
   ai dùng).
2. App quyết định dựa trên kết quả.
3. App ghi, và **chính câu ghi làm thay đổi kết quả của bước 1**. Vì bước 1 đọc snapshot cũ nên điều
   kiện đã sai mà không ai biết.

Ba cách sửa:

**Cách 1: khoá cả tập đã đọc.** Đổi câu kiểm tra thành locking read:

| Bước | Session A (Alice) | Session B (Bob) | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT id FROM doctors WHERE shift_id = 1 AND on_call = TRUE FOR UPDATE;` | | 2 dòng, A khoá cả hai |
| 2 | | `START TRANSACTION;` `SELECT id FROM doctors WHERE shift_id = 1 AND on_call = TRUE FOR UPDATE;` | B chờ |
| 3 | `UPDATE doctors SET on_call = FALSE WHERE id = 1;` `COMMIT;` | | B được chạy tiếp; locking read đọc bản mới nhất: chỉ còn 1 dòng (Bob) |
| 4 | | App: 1 < 2, từ chối. `ROLLBACK;` | Ràng buộc được giữ |

⚠️ Cách này chỉ ổn khi điều kiện nói về **các dòng đang tồn tại**. Khi điều kiện là "chưa có dòng
nào thoả" (đặt phòng họp không trùng giờ, đăng ký username) thì không có dòng để khoá. InnoDB ở RR
vẫn cứu được nhờ gap lock trên khoảng đã quét, nhưng hai session cùng khoá một khe trống rồi cùng
`INSERT` rất dễ ra deadlock (module 2.6). Ở RC của MySQL và ở mọi level dưới Serializable của
Postgres, `FOR UPDATE` trên tập rỗng không khoá gì cả.

**Cách 2: đưa ràng buộc xuống DB.** Biến điều kiện thành thứ mà DB tự kiểm tra trên một dòng duy nhất:

- Điều kiện dạng "không trùng": `UNIQUE` index (username, email, cặp phòng và khung giờ cố định).
  Postgres còn có *exclusion constraint* để chặn hai khoảng thời gian chồng nhau; MySQL không có.
- Điều kiện dạng đếm: *materialize conflict* (DDIA gọi là "vật chất hoá xung đột"), tức tạo ra một
  dòng đại diện để mọi transaction liên quan phải tranh nhau:

  ```sql
  CREATE TABLE shifts (id INT PRIMARY KEY, on_call_count INT NOT NULL CHECK (on_call_count >= 1));
  INSERT INTO shifts VALUES (1, 2);
  -- Xin nghỉ: một câu atomic trên dòng chung của ca, rồi mới sửa bác sĩ
  UPDATE shifts SET on_call_count = on_call_count - 1 WHERE id = 1 AND on_call_count >= 2;
  -- affected rows = 0: không được nghỉ. = 1: được, tiếp tục:
  UPDATE doctors SET on_call = FALSE WHERE id = 1;
  ```

  Hai người xin nghỉ giờ cùng sửa dòng `shifts.id = 1`, nên bài toán write skew trở thành bài toán
  lost update, và câu atomic đã giải được. `CHECK` là lưới an toàn cuối.
- ⚠️ Trigger chỉ giúp được nếu nó thao tác trên một dòng chung như trên. Trigger tự `SELECT COUNT(*)`
  để kiểm tra thì đọc cùng snapshot cũ và lọt y như code app.

**Cách 3: Serializable.** MySQL Serializable biến câu đếm ở bước 1, 2 thành `FOR SHARE`: cả hai giữ
khoá S trên dòng 1 và 2; A muốn ghi dòng 1 phải chờ S của B, B muốn ghi dòng 2 phải chờ S của A, ra
deadlock và một bên nhận lỗi 1213. Postgres Serializable không chờ: cả hai câu `UPDATE` đều chạy,
A commit thành công, B khi `COMMIT` nhận `ERROR: could not serialize access due to read/write
dependencies among transactions` (40001). Retry của B sẽ đếm lại, thấy 1, và từ chối. Đây là cách
duy nhất không phải nghĩ riêng cho từng ràng buộc, đổi lại mọi transaction phải có retry.

#### Đối chiếu Postgres (🔴)

- **RR của Postgres là snapshot isolation** thật sự: mọi câu đọc lẫn câu ghi trong transaction dùng
  cùng một snapshot, và ghi đụng dòng đã bị sửa sau snapshot thì lỗi 40001. Nhờ vậy không có kiểu
  "đọc thấy 20 mà xoá không thấy 20" như MySQL, phantom cũng không xảy ra (tài liệu Postgres ghi chuẩn
  SQL cho phép phantom ở RR "but not in PG"). Nhưng write skew vẫn lọt.
- **Serializable của Postgres là SSI** (*Serializable Snapshot Isolation*, có từ Postgres 9.1, bài của
  Ports và Grittner). Cơ chế:
  1. Chạy y như RR, không thêm khoá chặn nào.
  2. Ghi lại dữ liệu mỗi transaction đã đọc bằng *predicate lock* (hiện trong `pg_locks` với mode
     `SIReadLock`). Tên có chữ lock nhưng nó **không chặn ai**, chỉ để đánh dấu.
  3. Khi một transaction ghi vào thứ mà transaction đồng thời khác đã đọc, SSI ghi nhận một cạnh phụ
     thuộc đọc-ghi (*rw-antidependency*). Nếu xuất hiện cấu trúc nguy hiểm (hai cạnh như vậy nối
     tiếp nhau qua một transaction ở giữa), SSI huỷ một transaction với lỗi 40001.
  4. Vì chỉ nhìn cấu trúc chứ không dựng lại đủ đồ thị, SSI có *false positive*: đôi khi huỷ cả những
     transaction thực ra không gây anomaly.
- Ví dụ trong tài liệu Postgres: bảng `mytab(class, value)`. A tính `SUM(value) WHERE class = 1` được
  30 rồi chèn `(2, 30)`; B đồng thời tính `SUM WHERE class = 2` được 300 rồi chèn `(1, 300)`. Không có
  thứ tự tuần tự nào cho ra đúng hai con số 30 và 300, nên ở Serializable một bên bị huỷ; ở RR cả hai
  đều commit.
- Khuyến nghị của tài liệu Postgres khi dùng Serializable: khai báo `READ ONLY` khi có thể; giữ
  transaction nhỏ; không để connection "idle in transaction"; giới hạn số connection bằng pool; bỏ các
  `FOR UPDATE` không còn cần; seq scan buộc phải lấy predicate lock cả bảng nên làm tăng số lần huỷ.
- ⚠️ Vì sao chạy Postgres ở RR hoặc Serializable mà không retry là bug: ở hai level này lỗi 40001
  **là cơ chế hoạt động bình thường**, không phải sự cố. DB chọn huỷ thay vì cho kết quả sai; nếu app
  không bắt 40001 và chạy lại cả transaction thì request đó thất bại với người dùng, và dưới tải cao
  tỉ lệ thất bại tăng theo mức tranh chấp. Retry cũng chỉ đúng khi chạy lại từ câu đọc đầu tiên.
- Đối chiếu với [Jepsen: Consistency Models](https://jepsen.io/consistency): bản đồ này đặt read
  committed, repeatable read, snapshot isolation, serializable vào một đồ thị "mô hình nào kéo theo
  mô hình nào". Mức trên cùng là *strict serializable*: serializable cộng thêm ràng buộc thời gian
  thực (transaction commit trước thì transaction bắt đầu sau phải thấy). Khác biệt này quan trọng
  nhất khi đọc từ replica hoặc dùng DB phân tán (xem
  [14-distributed-systems.md](../14-distributed-systems.md)).

Đối chiếu ngôn ngữ khác: trong Java, Spring dịch deadlock và serialization failure thành các lớp con
của `ConcurrencyFailureException`, và thường retry bằng `@Retryable` bọc quanh method
`@Transactional`; trong Go, `database/sql` không tự retry transaction khi gặp deadlock hay serialization failure, bạn
tự viết vòng lặp quanh `BeginTx`.
Ở cả ba ngôn ngữ, nguyên tắc như nhau: retry ở tầng bọc cả transaction, không phải từng câu lệnh.

**Tóm tắt nhanh**
- Anomaly là kết quả không có được bằng bất kỳ thứ tự tuần tự nào; tên level không nói hết, phải biết
  từng DB chặn được gì (Hermitage).
- MySQL RR: `SELECT` thường đọc snapshot chụp ở lần đọc đầu, còn `UPDATE`/`DELETE`/`FOR UPDATE` đọc
  bản mới nhất. Trộn hai kiểu thì thấy phantom và kết quả mâu thuẫn.
- MySQL RR **để lọt lost update**; Postgres RR báo 40001. Chống bằng update atomic, `FOR UPDATE`,
  version, hoặc level cao hơn kèm retry.
- Write skew ghi hai dòng khác nhau nên RR của cả hai DB đều lọt; sửa bằng khoá cả tập đã đọc,
  materialize conflict hoặc unique, hoặc Serializable.
- Postgres RR/Serializable và MySQL Serializable bắt buộc retry cả transaction; Laravel
  `DB::transaction($fn, 3)`, mặc định chỉ 1 lần.

**Nguồn**: *Designing Data-Intensive Applications* ch.7 (*Weak Isolation Levels*, *Serializability*) ·
[MySQL: Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html) ·
[MySQL: Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html) ·
[PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) ·
[Hermitage](https://github.com/ept/hermitage) ·
[A Critique of ANSI SQL Isolation Levels](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/) ·
[Serializable Snapshot Isolation in PostgreSQL](https://arxiv.org/abs/1208.4179) ·
[Jepsen: Consistency Models](https://jepsen.io/consistency)

---

### 2.6 Lock thực dụng

Module này trả lời: khi nào khoá dòng, khoá kiểu gì, làm sao để khoá không biến thành deadlock hay
hàng đợi chờ 50 giây, và dùng DB làm job queue hay khoá phân tán ở mức nào là đủ. Dùng lại dữ liệu
mẫu ở đầu module 2.5.

#### Shared lock và exclusive lock

InnoDB khoá ở mức dòng (chính xác là khoá bản ghi index, module 3.2). Có hai loại cơ bản:

- **Shared lock (S)**, lấy bằng `SELECT ... FOR SHARE` (cú pháp cũ `LOCK IN SHARE MODE` vẫn chạy):
  nhiều transaction cùng giữ S trên một dòng được, nhưng khi còn ai giữ S thì không ai sửa được.
- **Exclusive lock (X)**, lấy bằng `SELECT ... FOR UPDATE`, `UPDATE`, `DELETE`: chỉ một transaction
  giữ; ai muốn lấy S hoặc X trên dòng đó đều phải chờ.

| Đang có người giữ → / Mình xin ↓ | Không ai giữ | S | X |
|---|---|---|---|
| S (`FOR SHARE`) | Được | Được | Chờ |
| X (`FOR UPDATE`, `UPDATE`, `DELETE`) | Được | Chờ | Chờ |
| `SELECT` thường | Được | Được | **Được**, đọc bản cũ từ undo log |

Dòng cuối là điểm hay quên: consistent read bỏ qua mọi khoá dòng, nên một `SELECT` thường không bao
giờ chờ và không chặn ai (ngoại lệ duy nhất là Serializable khi autocommit tắt, như ở 2.5). Hệ quả:
khoá chỉ bảo vệ bạn khỏi những người **cũng khoá**. Nếu một đoạn code khác đọc bằng `SELECT` thường
rồi ghi, khoá của bạn không ngăn được nó.

Các quy tắc đi kèm:

1. Khoá giữ tới khi transaction `COMMIT` hoặc `ROLLBACK`, không nhả sớm ở giữa. Đây là *two-phase
   locking*: pha lấy khoá, rồi pha nhả toàn bộ một lúc.
2. ⚠️ Locking read chỉ có tác dụng trong transaction. Với autocommit bật và không có `START
   TRANSACTION`, câu `SELECT ... FOR UPDATE` tự là một transaction và nhả khoá ngay khi chạy xong.
   Tài liệu Laravel ghi bọc trong transaction là "không bắt buộc nhưng nên làm"; thực tế thiếu
   transaction thì `lockForUpdate()` gần như vô nghĩa.
3. ⚠️ `FOR UPDATE` ở câu ngoài không khoá các dòng mà subquery đọc:
   `SELECT * FROM t1 WHERE c1 = (SELECT c1 FROM t2) FOR UPDATE` chỉ khoá `t1`. Muốn khoá cả `t2` thì
   subquery cũng phải có `FOR UPDATE`. Khi join nhiều bảng, `FOR UPDATE OF t1` chỉ khoá dòng của `t1`.

Khi nào dùng `FOR SHARE`: ví dụ trong tài liệu MySQL là chèn dòng con và muốn chắc dòng cha không bị
xoá giữa chừng: `SELECT * FROM parent WHERE name = 'Jones' FOR SHARE;` rồi mới `INSERT` vào `child`.
Ai muốn xoá cha phải chờ, còn những người khác cùng chèn con thì không chặn nhau. ⚠️ Đừng dùng
`FOR SHARE` cho mẫu đọc rồi sửa chính dòng đó: hai bên cùng giữ S, cùng xin nâng lên X, và ra
deadlock. Đọc để sửa thì luôn `FOR UPDATE`.

#### Optimistic lock và pessimistic lock

Hai chiến lược đối lập về cách xử lý xung đột:

- **Pessimistic** (bi quan): tin rằng xung đột sẽ xảy ra, nên khoá trước khi đọc. Người đến sau chờ.
- **Optimistic** (lạc quan): tin rằng xung đột hiếm, nên không khoá gì; lúc ghi mới kiểm tra "dữ liệu
  có bị ai sửa từ lúc mình đọc không", nếu có thì báo xung đột hoặc thử lại.

Optimistic lock thường cài bằng cột `version` tăng mỗi lần ghi:

```sql
CREATE TABLE posts (id BIGINT PRIMARY KEY, body TEXT NOT NULL, version INT NOT NULL DEFAULT 1);
INSERT INTO posts (id, body) VALUES (1, 'Bản gốc');
```

Timeline 5: hai biên tập viên cùng sửa một bài.

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `SELECT body, version FROM posts WHERE id = 1;` | | A thấy version 1. Không khoá, không giữ transaction |
| 2 | | `SELECT body, version FROM posts WHERE id = 1;` | B cũng thấy version 1 |
| 3 | (người dùng A sửa bài 3 phút) | (người dùng B sửa bài 5 phút) | Không ai chờ ai, không connection nào bị giữ |
| 4 | `UPDATE posts SET body = 'Bản của A', version = version + 1 WHERE id = 1 AND version = 1;` | | 1 dòng bị ảnh hưởng, version thành 2 |
| 5 | | `UPDATE posts SET body = 'Bản của B', version = version + 1 WHERE id = 1 AND version = 1;` | **0 dòng**: điều kiện `version = 1` không còn đúng |
| 6 | | App báo "bài đã bị người khác sửa", tải bản mới cho B so sánh hoặc merge | Bản của A không bị đè |

Bước 5 đúng kể cả khi B đang ở trong một transaction RR đã đọc snapshot cũ, vì `UPDATE` là locking
read, luôn đánh giá `WHERE` trên bản mới nhất. Nếu A chưa commit ở bước 4 thì B chờ, rồi vẫn ra 0 dòng.

Cạm bẫy khi cài optimistic lock:

- ⚠️ Kiểm tra số dòng bị ảnh hưởng là **bắt buộc**; quên kiểm tra thì optimistic lock không làm gì cả.
  Với MySQL, PDO mặc định trả về số dòng *thật sự thay đổi*, không phải số dòng *khớp* `WHERE`; một
  câu `UPDATE` ghi đúng giá trị cũ trả về 0. Có `version = version + 1` thì luôn thay đổi nên không
  sao; muốn đếm số dòng khớp thì bật `PDO::MYSQL_ATTR_FOUND_ROWS` khi tạo kết nối.
- ⚠️ Dùng `updated_at` làm version là rủi ro: độ phân giải giây (hoặc micro giây) và đồng hồ các máy
  app lệch nhau có thể cho hai lần ghi cùng giá trị. Dùng số nguyên.
- Mọi đường ghi vào bảng đều phải tăng version, kể cả job, script sửa dữ liệu, admin panel.

Đối chiếu: JPA/Hibernate có sẵn `@Version` sinh đúng câu `WHERE version = ?` và ném
`OptimisticLockException` khi 0 dòng; Eloquent không có sẵn, phải tự viết điều kiện.

Luồng trừ tồn kho theo ba cách (tiêu chí "Nắm chắc khi" của plan):

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

final class OutOfStock extends RuntimeException {}

// Cách 1: update atomic có điều kiện. Một câu, một round-trip, khoá dòng trong vài mili giây
function reserveAtomic(int $productId, int $qty): void
{
    $affected = DB::update(
        'UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?',
        [$qty, $productId, $qty],
    );
    if ($affected !== 1) {
        throw new OutOfStock();
    }
}

// Cách 2: pessimistic. Đọc và khoá, tính ở app, ghi, commit. Người thứ hai chờ ở lockForUpdate()
function reservePessimistic(int $productId, int $qty): void
{
    DB::transaction(function () use ($productId, $qty): void {
        $p = DB::table('products')->where('id', $productId)->lockForUpdate()->first();
        if ($p === null || $p->stock < $qty) {
            throw new OutOfStock();
        }
        // Chỗ này có thể chạy luật nghiệp vụ phức tạp: hạn mức mỗi khách, combo, flash sale...
        DB::table('products')->where('id', $productId)->update(['stock' => $p->stock - $qty]);
    }, 3);
}

// Cách 3: optimistic. Không khoá; xung đột thì đọc lại và thử lại vài lần
function reserveOptimistic(int $productId, int $qty, int $maxAttempts = 5): void
{
    for ($i = 1; $i <= $maxAttempts; $i++) {
        $p = DB::table('products')->where('id', $productId)->first(['stock', 'version']);
        if ($p === null || $p->stock < $qty) {
            throw new OutOfStock();
        }
        $affected = DB::table('products')
            ->where('id', $productId)
            ->where('version', $p->version)
            ->update(['stock' => $p->stock - $qty, 'version' => $p->version + 1]);
        if ($affected === 1) {
            return;
        }
        usleep(random_int(1_000, 20_000)); // lùi ngẫu nhiên để các bên không đụng nhau lần nữa
    }
    throw new RuntimeException('Tranh chấp quá cao, thử lại sau');
}
```

Cách 3 cần thêm cột `ALTER TABLE products ADD version INT NOT NULL DEFAULT 1;`.

| Tiêu chí | Atomic `UPDATE ... WHERE` | Pessimistic `FOR UPDATE` | Optimistic `version` |
|---|---|---|---|
| Logic dùng được | Diễn đạt được trong một câu SQL | Tuỳ ý, tính ở app | Tuỳ ý, tính ở app |
| Tranh chấp cao (flash sale một sản phẩm) | Tốt nhất | Ổn, các request xếp hàng | Tệ: đa số lần thử thất bại, tốn round-trip |
| Thao tác kéo dài, có người dùng suy nghĩ giữa chừng | Không áp dụng | Không được: giữ khoá và connection hàng phút | Đúng chỗ của nó |
| Rủi ro | Quên kiểm tra affected rows | Deadlock, lock wait, transaction dài | Quên kiểm tra affected rows, bỏ sót đường ghi không tăng version |

Quy tắc chọn: atomic trước; logic không gói được vào một câu thì pessimistic cho thao tác ngắn;
optimistic khi "đọc" và "ghi" cách nhau cả một lần tương tác của người dùng (form sửa bài, sửa cấu
hình), hoặc khi dữ liệu đi qua nhiều request HTTP.

#### Deadlock

Deadlock là tình huống mỗi transaction giữ một khoá mà transaction kia cần, tạo thành vòng chờ
không bao giờ tự gỡ. Tình huống điển hình: hai đơn hàng cùng chứa hai sản phẩm nhưng trừ tồn kho theo
thứ tự khác nhau.

Timeline 6: deadlock hai sản phẩm. Đơn của A có sản phẩm 1 rồi 2; đơn của B có sản phẩm 2 rồi 1.

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `UPDATE products SET stock = stock - 1 WHERE id = 1;` | | A giữ X dòng 1 |
| 2 | | `START TRANSACTION;` `UPDATE products SET stock = stock - 1 WHERE id = 2;` | B giữ X dòng 2 |
| 3 | `UPDATE products SET stock = stock - 1 WHERE id = 2;` | | A chờ B |
| 4 | | `UPDATE products SET stock = stock - 1 WHERE id = 1;` | Vòng chờ khép lại. InnoDB phát hiện **ngay lập tức**, chọn một bên (giả sử B) và trả `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction` |
| 5 | | (toàn bộ transaction B đã bị rollback, kể cả câu ở bước 2) | Khoá dòng 2 được nhả; câu ở bước 3 của A chạy xong |
| 6 | `COMMIT;` | App retry cả transaction B | Lần retry thành công |

Cơ chế phát hiện của InnoDB:

1. Mỗi khi một transaction phải chờ khoá, InnoDB duyệt *wait-for graph* (đồ thị ai chờ ai) để tìm
   vòng. Bật mặc định qua `innodb_deadlock_detect = ON`.
2. Có vòng thì InnoDB chọn *victim* (nạn nhân) để rollback, ưu tiên transaction "nhỏ", đo bằng số
   dòng đã insert, update, delete. Rollback nạn nhân là rollback **cả transaction**, khác với lock wait
   timeout ở nhóm sau.
3. Nếu danh sách chờ dài hơn 200 transaction, hoặc phải xét hơn 1.000.000 khoá, InnoDB coi luôn là
   deadlock và rollback transaction đang kiểm tra.
4. Với hệ thống rất nhiều luồng cùng chờ một dòng nóng, chính việc duyệt đồ thị làm chậm; tài liệu
   cho phép tắt `innodb_deadlock_detect` và dựa vào `innodb_lock_wait_timeout`, nhưng khi đó
   deadlock thật phải chờ đủ timeout mới gỡ.

Chẩn đoán: `SHOW ENGINE INNODB STATUS\G`, mục `LATEST DETECTED DEADLOCK` cho biết hai transaction,
câu lệnh, khoá đang giữ và khoá đang xin, nhưng chỉ của **deadlock gần nhất**. Bật
`innodb_print_all_deadlocks = ON` (mặc định OFF) để ghi mọi deadlock vào error log; nên bật trên
production vì deadlock thường thưa và khó tái hiện.

Cách phòng, theo tài liệu MySQL:

- **Khoá theo thứ tự cố định**: sort id sản phẩm trước khi trừ. Ở timeline 6, nếu B cũng trừ 1 rồi 2
  thì B chờ ngay ở câu đầu và không có vòng. Đây là cách hiệu quả nhất.

  ```php
  <?php
  declare(strict_types=1);

  use Illuminate\Support\Facades\DB;

  /** @param array<int, int> $items productId => qty */
  function reserveOrder(array $items): void
  {
      ksort($items); // mọi request khoá theo cùng thứ tự id tăng dần
      DB::transaction(function () use ($items): void {
          foreach ($items as $productId => $qty) {
              $affected = DB::update(
                  'UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?',
                  [$qty, $productId, $qty],
              );
              if ($affected !== 1) {
                  throw new OutOfStock(); // rollback cả đơn, không trừ dở dang
              }
          }
      }, 3);
  }
  ```

- **Transaction ngắn**, commit ngay khi xong; không để session tương tác mở transaction rồi bỏ đó.
- **Index đúng** cho `WHERE` của `UPDATE` và `FOR UPDATE`, để khoá ít bản ghi nhất (nhóm sau).
- **Bớt locking read** khi không cần; cân nhắc RC, vì RC không có gap lock nên ít deadlock kiểu khe
  hơn.
- ⚠️ Không thể loại bỏ hoàn toàn deadlock, chỉ giảm tần suất. App **luôn phải có retry** cho lỗi 1213,
  và retry phải chạy lại cả transaction (Laravel `DB::transaction($fn, 3)`).

Một kiểu deadlock hay gặp mà không có "hai dòng ngược thứ tự": hai session cùng
`SELECT ... WHERE id = 5 FOR UPDATE` trên một id **chưa tồn tại** ở RR. Cả hai đều lấy được gap lock
(gap lock không xung đột với nhau), rồi cả hai cùng `INSERT` id 5, mỗi bên chờ gap lock của bên kia,
ra deadlock. Mẫu "kiểm tra chưa có thì chèn" nên thay bằng `INSERT ... ON DUPLICATE KEY UPDATE` hoặc
`INSERT` rồi bắt lỗi duplicate key 1062 (module 2.4, 3.2).

#### Hai bẫy hay gặp

⚠️ **Bẫy 1: `UPDATE`/`FOR UPDATE` trên cột không có index.** InnoDB khoá mọi bản ghi index mà nó
*quét qua*, không chỉ bản ghi khớp `WHERE`. Không có index thì phải quét cả clustered index, nên ở RR
nó khoá mọi dòng cùng mọi khe, gần như khoá cả bảng. Ví dụ trong tài liệu MySQL:

```sql
CREATE TABLE t (a INT NOT NULL, b INT) ENGINE = InnoDB;   -- không có index nào
INSERT INTO t VALUES (1,2),(2,3),(3,2),(4,3),(5,2);
```

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `UPDATE t SET b = 5 WHERE b = 3;` | | Ở RR: A giữ X trên **cả 5 dòng** dù chỉ sửa 2 |
| 2 | | `START TRANSACTION;` `UPDATE t SET b = 4 WHERE b = 2;` | Ở RR: B chờ ngay ở dòng (1,2), dù hai câu không chung dòng nào |
| 3 | `COMMIT;` | | B mới chạy được |

Ở RC, sau khi đánh giá `WHERE`, InnoDB nhả khoá của các dòng không khớp, nên A chỉ còn giữ khoá dòng
(2,3) và (4,3). Câu `UPDATE` của B còn được *semi-consistent read*: gặp dòng đang bị khoá, InnoDB trả
về bản mới nhất đã commit để kiểm tra `WHERE`; dòng không khớp thì bỏ qua, không phải chờ. Vì vậy ở
RC, B không chờ. Nhưng cách sửa đúng vẫn là thêm index trên `b`, không phải đổi level. Tự kiểm tra:
`EXPLAIN UPDATE ...` ra `type: ALL` là dấu hiệu sắp khoá cả bảng.

⚠️ **Bẫy 2: lock wait timeout chỉ rollback câu lệnh.** Khác với deadlock, khi một câu chờ khoá quá
`innodb_lock_wait_timeout` giây (mặc định 50, đặt được theo session), InnoDB chỉ rollback **câu lệnh
đang chờ**, transaction vẫn mở và mọi câu trước đó vẫn còn hiệu lực.

Timeline 7: commit một nửa.

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 0 | | `SET SESSION innodb_lock_wait_timeout = 5;` | Rút xuống 5 giây cho dễ thử |
| 1 | `START TRANSACTION;` `UPDATE accounts SET balance = balance - 10 WHERE id = 1;` | | A giữ X dòng 1 và để đó |
| 2 | | `START TRANSACTION;` `UPDATE accounts SET balance = balance + 100 WHERE id = 2;` | Chuyển tiền từ 1 sang 2: bước cộng đã chạy |
| 3 | | `UPDATE accounts SET balance = balance - 100 WHERE id = 1;` | Chờ A. 5 giây sau: `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction` |
| 4 | | `COMMIT;` | Câu ở bước 2 được commit: tài khoản 2 có thêm 100 mà tài khoản 1 không bị trừ |
| 5 | `ROLLBACK;` | | Tiền "từ trên trời rơi xuống" đã nằm trong DB |

Cách tránh:

1. Gặp 1205 thì **luôn `ROLLBACK`** cả transaction rồi mới quyết định retry hay báo lỗi.
2. Hoặc bật `innodb_rollback_on_timeout = ON` để InnoDB tự rollback cả transaction khi timeout. Biến
   này mặc định OFF, là biến global và không đổi được lúc chạy, phải khởi động lại server.
3. Trong Laravel, `DB::transaction()` rollback khi closure ném bất kỳ exception nào, nên an toàn. Bẫy
   nằm ở code tự `try/catch` bên trong closure rồi nuốt exception, hoặc code PDO thuần tự
   `beginTransaction()` rồi `catch` xong vẫn `commit()`.

```php
<?php
declare(strict_types=1);

function transfer(PDO $pdo, int $from, int $to, string $amount): void
{
    $pdo->beginTransaction();
    try {
        $pdo->prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?')->execute([$amount, $to]);
        $pdo->prepare('UPDATE accounts SET balance = balance - ? WHERE id = ?')->execute([$amount, $from]);
        $pdo->commit();
    } catch (Throwable $e) {
        $pdo->rollBack();   // KHÔNG được commit() ở đây, kể cả khi lỗi "chỉ là" 1205
        throw $e;
    }
}
```

Timeout 50 giây cũng là con số quá dài với request web: người dùng đã bỏ đi từ lâu mà connection vẫn
bị giữ. Nhiều hệ thống đặt thấp hơn cho session của app (vài giây) và giữ mặc định cho job chạy nền.

#### Job queue bằng DB

Nhu cầu: nhiều worker cùng lấy job từ một bảng, mỗi job chỉ một worker xử lý. Với `FOR UPDATE` thường,
mọi worker cùng nhắm vào job cũ nhất và xếp hàng chờ nhau. MySQL 8.0 (và Postgres 9.5) thêm hai tuỳ
chọn chỉ áp dụng cho khoá dòng:

- `FOR UPDATE SKIP LOCKED`: không chờ, **bỏ qua** các dòng đang bị khoá, trả về phần còn lại. Tài liệu
  MySQL nói rõ kết quả là một view không nhất quán, không dùng cho việc giao dịch thông thường, chỉ hợp
  với bảng dạng hàng đợi.
- `FOR UPDATE NOWAIT`: không chờ; dòng bị khoá thì lỗi ngay `ERROR 3572 (HY000): Do not wait for lock.`
  Hợp khi muốn báo "đang có người xử lý" thay vì bắt người dùng chờ.

```sql
CREATE TABLE jobs (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  payload JSON NOT NULL,
  status ENUM('pending','running','done','failed') NOT NULL DEFAULT 'pending',
  run_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  attempts INT NOT NULL DEFAULT 0,
  locked_at DATETIME NULL,
  locked_by VARCHAR(64) NULL,
  KEY idx_pick (status, run_at)            -- để câu lấy job chỉ quét và khoá đúng vùng pending
);

-- Worker: nhận job trong một transaction RẤT ngắn
START TRANSACTION;
SELECT id FROM jobs
 WHERE status = 'pending' AND run_at <= NOW()
 ORDER BY run_at LIMIT 10
 FOR UPDATE SKIP LOCKED;
UPDATE jobs SET status = 'running', locked_at = NOW(), locked_by = 'worker-7', attempts = attempts + 1
 WHERE id IN (/* các id vừa lấy */);
COMMIT;
-- Xử lý job NGOÀI transaction, xong thì:
UPDATE jobs SET status = 'done' WHERE id = ? AND locked_by = 'worker-7';
```

Hai worker chạy câu `SELECT ... SKIP LOCKED` cùng lúc sẽ nhận hai nhóm job rời nhau: worker thứ hai
bỏ qua 10 dòng worker thứ nhất đang khoá và lấy 10 dòng tiếp theo.

Vì sao tách "nhận job" và "xử lý job" thành hai bước: nếu giữ transaction (và khoá) suốt lúc xử lý,
worker chết thì khoá tự nhả khi connection đứt, nghe thì tiện; nhưng job chạy 5 phút là transaction
mở 5 phút, chiếm connection, và cản InnoDB dọn undo log (module 3.1). Tách ra thì phải tự lo các
trường hợp sau:

1. **Worker chết giữa chừng**: job kẹt ở `running`. Một tiến trình dọn định kỳ trả job quá hạn về
   pending: `UPDATE jobs SET status = 'pending', locked_by = NULL WHERE status = 'running' AND
   locked_at < NOW() - INTERVAL 15 MINUTE;`. Ngưỡng phải lớn hơn thời gian chạy dài nhất của một job,
   hoặc worker định kỳ cập nhật `locked_at` như nhịp tim (heartbeat).
2. **Giới hạn số lần thử**: `attempts` vượt ngưỡng thì chuyển `failed` để người xem, không lặp vô hạn
   với job lỗi vĩnh viễn (poison job). Lần thử sau nên lùi `run_at` theo cấp số nhân.
3. **Idempotent**: job có thể chạy hai lần (worker xử lý xong nhưng chết trước khi ghi `done`, rồi bị
   trả về pending). Xử lý phải cho cùng kết quả khi chạy lại, ví dụ kiểm tra theo khoá idempotency
   hoặc dùng unique constraint ở bảng đích.
4. **Dọn bảng**: job `done` xoá hoặc chuyển sang bảng lưu trữ theo lô, để bảng hàng đợi luôn nhỏ.

Bài của Brandur (2015, trên Postgres) cho thấy vì sao hàng đợi trong DB có thể "tự làm mình chậm dần":
một transaction chạy lâu ở đâu đó giữ snapshot cũ, nên các dòng job đã xoá không được dọn (Postgres
đánh dấu là *dead tuple* chứ chưa xoá thật). Index không biết dòng nào còn sống, nên mỗi lần worker
tìm job phải đi qua hàng nghìn dòng chết. Trong thí nghiệm của ông, sau một giờ có transaction dài, số
dead tuple lên gần 100 nghìn, thời gian khoá job tăng khoảng 15 lần và backlog lên khoảng 60 nghìn
job. Bài viết trước khi Postgres có `SKIP LOCKED` (thư viện Que trong bài khoá job bằng advisory lock), nhưng bài học vẫn đúng với MySQL: transaction
dài làm undo log phình (history list length tăng, module 3.1) và mọi thứ đọc qua đó chậm theo. Giữ
transaction ngắn và không để transaction nào treo trên cùng DB với hàng đợi.

Trong Laravel, queue driver `database` đã dùng đúng kỹ thuật này: với MySQL từ 8.0.1 và Postgres từ
9.5, nó lấy job bằng `FOR UPDATE SKIP LOCKED`. Query builder cũng nhận chuỗi khoá tuỳ ý:
`DB::table('jobs')->where(...)->lock('for update skip locked')->get()`. Khi tải lớn hơn khả năng của
DB (hàng nghìn job mỗi giây), chuyển sang Redis hoặc message broker ([12-messaging.md](../12-messaging.md)).

#### Advisory lock

Advisory lock là khoá theo **một cái tên tuỳ ý** do app đặt ra, không gắn với dòng hay bảng nào. DB
chỉ đảm bảo tại một thời điểm chỉ một session giữ được tên đó; ý nghĩa của tên là do app quy ước (vì
vậy mới gọi là "advisory", chỉ mang tính thoả thuận).

```sql
SELECT GET_LOCK('cron:daily-report', 0);   -- 1: lấy được; 0: người khác đang giữ (hết timeout); NULL: lỗi
-- ... chạy job ...
SELECT RELEASE_LOCK('cron:daily-report');  -- 1: đã nhả; 0: khoá không phải của mình; NULL: không tồn tại
SELECT IS_USED_LOCK('cron:daily-report');  -- connection id đang giữ, hoặc NULL
```

Tham số thứ hai là số giây chờ; `0` là thử một lần rồi thôi, số âm là chờ vô hạn. Tên dài tối đa 64
ký tự. Dùng điển hình: đảm bảo chỉ một instance chạy một cron job khi app có nhiều server.

Đặc điểm cần nhớ:

- ⚠️ Khoá gắn với **session** (connection), không với transaction: `COMMIT` hay `ROLLBACK` không nhả.
  Nó chỉ nhả khi gọi `RELEASE_LOCK`, `RELEASE_ALL_LOCKS()`, hoặc khi connection đóng.
- ⚠️ Connection đóng là mất khoá, kể cả khi tiến trình PHP vẫn đang chạy job: mất mạng, proxy cắt
  connection idle, hay `wait_timeout` có thể khiến instance khác lấy được khoá trong lúc job cũ chưa
  xong. Với persistent connection hoặc connection pool thì ngược lại: quên `RELEASE_LOCK` là khoá còn
  mãi trên connection được tái sử dụng.
- Chỉ có tác dụng trong một server MySQL; với nhiều primary, hoặc app đọc ghi ở các DB khác nhau, nó
  không còn là khoá chung.

Postgres có bộ hàm tương tự nhưng khoá theo số nguyên và có cả hai phạm vi: `pg_advisory_lock(key)`
theo session, `pg_advisory_xact_lock(key)` tự nhả khi transaction kết thúc (thường an toàn hơn), cùng
các bản `pg_try_...` không chờ. Trong Laravel, `withoutOverlapping()` và `onOneServer()` của scheduler
dựa trên cache lock (`Cache::lock()`), thường chạy trên Redis; so sánh khoá DB với khoá Redis, fencing
token và vì sao khoá phân tán khó đúng ở [14-distributed-systems.md](../14-distributed-systems.md).

**Tóm tắt nhanh**
- S cho nhau cùng đọc, X độc quyền; `SELECT` thường bỏ qua mọi khoá. Khoá giữ tới commit và chỉ có
  tác dụng trong transaction.
- Trừ tồn kho: atomic `UPDATE ... WHERE stock >= ?` trước; logic phức tạp thì `FOR UPDATE`; thao tác
  dài qua nhiều request thì optimistic `version`. Luôn kiểm tra affected rows.
- Deadlock: InnoDB phát hiện ngay, rollback cả transaction nạn nhân (1213). Phòng bằng khoá theo thứ
  tự cố định, transaction ngắn, index đúng; không tránh hết được nên luôn retry.
- `UPDATE` trên cột không index khoá mọi dòng quét qua. Lock wait timeout (1205, 50 giây) chỉ rollback
  câu lệnh: luôn `ROLLBACK` cả transaction.
- Job queue: `FOR UPDATE SKIP LOCKED` + index `(status, run_at)` + dọn job kẹt + giới hạn thử +
  idempotent. `GET_LOCK` gắn với connection, không với transaction.

**Nguồn**: [MySQL: Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html) ·
[MySQL: Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html) ·
[MySQL: Deadlock Detection](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-detection.html) ·
[MySQL: How to Minimize and Handle Deadlocks](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html) ·
[MySQL: Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html) ·
[MySQL: InnoDB Startup Options and System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html) ·
[Brandur: Postgres Job Queues & Failure By MVCC](https://brandur.org/postgres-queues) ·
[Laravel: Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking)


---

### 2.7 Tầng PHP: PDO và Laravel

Module này trả lời: giữa dòng code Eloquent và câu SQL chạy trên MySQL có những tầng nào (Laravel,
PDO, driver mysqlnd), mỗi tầng mặc định làm gì, và những mặc định đó gây ra bug gì khi hệ thống lớn
lên. Đây là chỗ người phỏng vấn phân biệt "dùng được Laravel" với "hiểu Laravel làm gì bên dưới".

```
Eloquent / Query Builder      Post::with('author')->where(...)->get()
        |  sinh SQL có placeholder + mảng binding
Illuminate\Database\Connection   chọn read/write PDO, transaction level, retry, event QueryExecuted
        |  prepare / execute
PDO + driver PDO_MYSQL (mysqlnd)  emulate hay native prepare, buffered result, kiểu trả về
        |  giao thức MySQL qua TCP/socket
MySQL server                   max_connections, wait_timeout, auth plugin
```

#### PDO

*PDO* (PHP Data Objects) là lớp truy cập DB chung của PHP: cùng một API cho MySQL, Postgres,
SQLite, còn phần riêng của từng DB nằm trong *driver* (với MySQL là `PDO_MYSQL`, chạy trên thư viện
client `mysqlnd`). Laravel không tự nói chuyện với MySQL; `DB::connection()->getPdo()` trả về đúng
object PDO mà mọi query của Laravel đi qua.

*Prepared statement* tách câu SQL khỏi giá trị: câu lệnh chứa chỗ trống (`?` hoặc `:name`), giá trị
gửi riêng. Vì giá trị không bao giờ được ghép thành chuỗi SQL, chuỗi `' OR 1=1 --` chỉ là một chuỗi
dữ liệu, không phải cú pháp. Đây là cách chống *SQL injection* (chèn mã SQL qua dữ liệu đầu vào).

```php
<?php
declare(strict_types=1);

$pdo = new PDO(
    'mysql:host=127.0.0.1;port=3306;dbname=learn;charset=utf8mb4',  // charset trong DSN, không dùng SET NAMES
    'root',
    'root',
    [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,   // mặc định từ PHP 8.0, ghi rõ cho chắc
        PDO::ATTR_EMULATE_PREPARES   => false,                    // dùng prepare thật của MySQL
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ],
);

$email = $_GET['email'] ?? '';
$stmt = $pdo->prepare('SELECT id, name, total FROM users WHERE email = ?');
$stmt->execute([$email]);
$row = $stmt->fetch();   // array|false
```

Có hai cách PDO thực hiện một prepared statement:

| | Emulate prepare | Native prepare |
|---|---|---|
| Cơ chế | PHP tự escape từng giá trị, ghép thành một chuỗi SQL hoàn chỉnh, gửi một lần (`COM_QUERY`) | Gửi câu có `?` cho server compile (`COM_STMT_PREPARE`), rồi gửi giá trị ở dạng nhị phân (`COM_STMT_EXECUTE`) |
| Số round-trip | 1 | 2 (prepare + execute), tái dùng statement thì các lần sau chỉ execute |
| Lỗi cú pháp phát hiện lúc | `execute()` (lúc `prepare()` chưa có gì gửi đi) | `prepare()` |
| Tên placeholder lặp lại (`:id` hai lần) | Được | Không được với PDO_MYSQL |
| Mặc định | **Của PDO_MYSQL thuần** | **Của Laravel** (connector đặt `ATTR_EMULATE_PREPARES => false`) |

Emulate prepare an toàn ở chỗ nào: PHP escape giá trị theo đúng charset của kết nối, nên với
`charset=utf8mb4` trong DSN thì giá trị vẫn không thoát ra khỏi dấu nháy. Lỗ hổng cổ điển xảy ra khi
charset mà client tưởng khác charset mà server dùng, ví dụ đổi charset bằng câu `SET NAMES gbk` thay
vì khai trong DSN: client escape theo bảng mã này, server giải mã theo bảng mã khác, và một số chuỗi
multi-byte "nuốt" mất dấu `\` escape. Native prepare không có rủi ro này vì giá trị không bao giờ nằm
trong văn bản SQL.

Vẫn nên dùng native prepare (như Laravel đang làm) vì:

1. Không phụ thuộc vào việc escape ở client đúng hay sai.
2. Lỗi cú pháp lộ ra sớm, ở `prepare()`.
3. ⚠️ Bẫy `LIMIT ?` với emulate: `execute([10])` bind mọi giá trị dạng chuỗi, câu gửi đi thành
   `LIMIT '10'` và MySQL báo lỗi cú pháp. Phải `bindValue(1, 10, PDO::PARAM_INT)`. Native prepare
   không gặp chuyện này.

Kiểu dữ liệu trả về: trước PHP 8.1, emulate prepare trả mọi cột dạng chuỗi (`"42"`), native trả
`int`. Từ PHP 8.1, PDO_MYSQL với emulate cũng trả `int`/`float` như native (muốn kiểu cũ thì bật
`PDO::ATTR_STRINGIFY_FETCHES`). Vì vậy nhiều code cũ có `if ($row['id'] === '42')` bị vỡ khi nâng PHP.

⚠️ `DECIMAL` luôn được trả về dạng chuỗi, ví dụ `"1234.50"`, ở cả hai chế độ. Đây là thiết kế đúng:
PHP không có kiểu số thập phân chính xác, ép sang `float` là mất độ chính xác (module 1.4). Giữ chuỗi,
tính bằng bcmath (từ PHP 8.4 có class `BcMath\Number` dùng được toán tử `+ - * /`) hoặc thư viện
`brick/money`. Cast `'decimal:2'` của Eloquent cũng trả về chuỗi, không phải float.

```php
<?php
declare(strict_types=1);

$total = '1234.50';                        // giá trị DECIMAL(12,2) đọc từ PDO
$vat   = bcmul($total, '0.10', 2);         // '123.45'
$grand = bcadd($total, $vat, 2);           // '1357.95'
var_dump($grand === '1357.95');            // bool(true)
```

*Error mode*: `ERRMODE_SILENT` chỉ đặt mã lỗi và trả `false`, `ERRMODE_WARNING` phát `E_WARNING`,
`ERRMODE_EXCEPTION` ném `PDOException`. Từ PHP 8.0 mặc định là exception; code cũ viết cho PHP 7 mà
không kiểm tra `false` thì lỗi SQL trôi qua im lặng. Laravel bọc `PDOException` thành
`Illuminate\Database\QueryException` (kèm câu SQL và binding trong message).

*Buffered query*: mặc định mysqlnd kéo **toàn bộ** result set từ server về bộ nhớ của process PHP
ngay khi query chạy xong, rồi bạn mới duyệt. Nhờ vậy đếm được số dòng, và chạy được query khác trên
cùng connection trong lúc đang duyệt. Cái giá: query ra 1 triệu dòng chiếm RAM tương ứng, và với
mysqlnd bộ nhớ này **được tính vào** `memory_limit`.

*Unbuffered query* (tắt `ATTR_USE_BUFFERED_QUERY`): server gửi dòng dần dần khi PHP fetch, PHP chỉ
giữ dòng hiện tại. Nhưng:

- Chưa fetch hết thì **không chạy được query nào khác trên connection đó** (lỗi 2014 "Cannot execute
  queries while other unbuffered queries are active"), nên thường phải mở một connection riêng.
- Không biết trước số dòng, không duyệt lại được.
- Server phải giữ result set mở lâu hơn, tải dồn về phía DB.

```php
<?php
declare(strict_types=1);

// Connection riêng để export, không dùng chung với phần còn lại của request
$export = new PDO('mysql:host=127.0.0.1;dbname=learn;charset=utf8mb4', 'root', 'root', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);
// PHP 8.5: hằng PDO::MYSQL_ATTR_* bị deprecated, dùng Pdo\Mysql::ATTR_*
$attr = PHP_VERSION_ID >= 80500 ? Pdo\Mysql::ATTR_USE_BUFFERED_QUERY : PDO::MYSQL_ATTR_USE_BUFFERED_QUERY;
$export->setAttribute($attr, false);

$out = fopen('php://output', 'w');
foreach ($export->query('SELECT id, email FROM users') as $row) {
    fputcsv($out, $row, escape: '');   // RAM gần như không đổi dù bảng có chục triệu dòng
    // (từ PHP 8.4, không truyền $escape tường minh là deprecated)
}
```

#### Connection

Java và Go chạy một process sống lâu, giữ *connection pool* (bể connection dùng chung): vài chục
connection phục vụ hàng nghìn request đồng thời, request mượn connection vài mili giây rồi trả lại.
PHP-FPM hoạt động khác: mỗi *worker* (process con) xử lý đúng một request tại một thời điểm và tự mở
connection riêng khi request đó chạy query đầu tiên (Laravel mở connection lazy, lúc cần mới
connect). Không có pool dùng chung giữa các worker.

Hệ quả: số connection tới MySQL tỉ lệ với số worker, không tỉ lệ với số query.

```
Tổng connection tối đa ≈ (số server web × pm.max_children × số connection mỗi request)
                        + số queue worker + cron/scheduler + tool admin, replica, monitoring

Ví dụ: 4 server × 50 children × 1 + 10 queue worker + 5 khác = 215
       > max_connections mặc định của MySQL (151)  -> lỗi 1040 "Too many connections"
```

- "Số connection mỗi request" có thể là 2: khi cấu hình read/write (bên dưới), một request vừa đọc
  vừa ghi mở một connection tới replica và một tới primary. Cộng riêng cho từng máy DB.
- ⚠️ Autoscale thêm server web là thêm connection. Lúc traffic tăng vọt, autoscaler thêm 10 máy, DB
  hết connection và sập trước khi app kịp chậm. Giới hạn trên của autoscale phải tính từ
  `max_connections`, hoặc đặt một proxy pool ở giữa (ProxySQL cho MySQL, PgBouncer cho Postgres).
- Mỗi connection MySQL tốn bộ nhớ ở server (buffer theo từng session), nên không thể đơn giản đặt
  `max_connections` thật lớn.

*Persistent connection* (`PDO::ATTR_PERSISTENT => true`): connection không đóng khi request kết thúc;
request sau được worker đó phục vụ sẽ dùng lại nếu cùng host, user, password. Theo tài liệu PHP:

- Không có gì mà persistent làm được còn connection thường không làm được. Lợi ích duy nhất là bỏ chi
  phí mở kết nối, đáng kể khi DB ở xa hoặc dùng TLS.
- Mỗi worker giữ connection của riêng nó, kể cả lúc rảnh. Sau một đợt spike, hàng trăm worker rảnh vẫn
  giữ connection cho tới khi worker bị kill hoặc server đóng vì timeout.
- ⚠️ Trạng thái của request trước rò sang request sau: database đang `USE`, table lock, **transaction
  chưa commit**, temporary table, biến session. Một request lỗi giữa transaction mà không rollback thì
  request kế tiếp chạy luôn trong transaction đó, và lock bị giữ vô thời hạn.
- Không thể dùng persistent để giữ transaction qua nhiều request, vì không chọn được connection cụ
  thể. PHP docs khuyên cân nhắc proxy pool hoặc runtime sống lâu thay vì persistent.

*Runtime sống lâu* (Laravel Octane chạy trên Swoole, RoadRunner, FrankenPHP): app boot một lần và
phục vụ nhiều request trong cùng process, nên connection cũng sống qua nhiều request, với đúng các rủi
ro trên. Thêm hai điểm:

- MySQL tự đóng connection rảnh quá `wait_timeout` (mặc định 28800 giây, tức 8 giờ; nhiều hệ managed
  đặt thấp hơn). App không biết cho tới query tiếp theo, và nhận lỗi "MySQL server has gone away"
  (2006) hoặc "Lost connection" (2013). Laravel tự reconnect và chạy lại query khi phát hiện mất
  kết nối, **nhưng chỉ khi không ở trong transaction**; trong transaction thì exception được ném ra,
  vì các câu trước đó của transaction đã mất theo connection.
- Octane mặc định reset trạng thái "đã ghi" của connection sau mỗi request (liên quan tới `sticky`
  bên dưới) và có listener `DisconnectFromDatabases` (tắt sẵn trong config) nếu muốn ngắt sau mỗi
  request.

⚠️ MySQL 8.4 tắt plugin xác thực `mysql_native_password` mặc định (plugin mặc định là
`caching_sha2_password`). PHP hỗ trợ đầy đủ `caching_sha2_password` từ 7.4.4. User cũ tạo bằng
`mysql_native_password` sẽ không đăng nhập được sau khi nâng lên 8.4 cho tới khi đổi plugin
(`ALTER USER ... IDENTIFIED WITH caching_sha2_password BY '...'`). Nếu kết nối không dùng TLS, lần
xác thực đầu cần trao đổi khoá RSA hoặc dùng socket; lỗi hay gặp khi chuyển là "Authentication
requires secure connection".

#### Eloquent và N+1

*Lazy loading*: truy cập `$post->author` khi quan hệ chưa được load thì Eloquent chạy một query ngay
lúc đó. Trong vòng lặp, mỗi phần tử một query:

```php
<?php
declare(strict_types=1);

use App\Models\Post;

$posts = Post::all();                       // 1 query: SELECT * FROM posts
foreach ($posts as $post) {
    echo $post->author->name;               // N query: SELECT * FROM users WHERE id = ? LIMIT 1
}
```

Ví dụ trong tài liệu Laravel: 25 cuốn sách là 26 query. Mỗi query chỉ vài mili giây nên **không bao
giờ lên slow query log**, nhưng 500 bài viết là 501 round-trip, cộng lại vài giây. Muốn thấy N+1 phải
đếm số query mỗi request, không phải nhìn từng query.

*Eager loading* nạp quan hệ cho cả tập trong một query:

```php
<?php
declare(strict_types=1);

use App\Models\Post;
use App\Models\User;

$posts = Post::with('author')->get();
// Query 1: SELECT * FROM posts
// Query 2: SELECT * FROM users WHERE users.id IN (3, 7, 12, ...)   -- rồi ghép trong PHP
$posts = Post::with(['author:id,name', 'comments' => fn ($q) => $q->latest()->limit(5)])->get();
// Chỉ lấy cột cần (phải có khoá id để ghép)

$posts->load('tags');                       // lazy eager load: đã có collection rồi mới nạp thêm
$users = User::withCount('posts')->get();   // $user->posts_count, subquery COUNT, không load post nào
```

⚠️ Eager loading có cái giá riêng: `with('comments')` trên 1.000 bài mỗi bài 500 comment là kéo
500.000 model vào RAM, dù trang chỉ hiển thị 5 comment mới nhất. Cần đếm thì `withCount`, cần tổng
thì `withSum`, cần vài bản ghi thì giới hạn trong closure.

Chỗ N+1 hay ẩn trong code thật:

1. Blade/API Resource truy cập quan hệ: `$post->author->name` trong view, `'author' =>
   $this->author->name` trong `JsonResource`. Controller không có vòng lặp nào nhưng view có.
2. Accessor hoặc `$appends` gọi quan hệ: `getFullAddressAttribute()` đọc `$this->city->name`; mỗi lần
   serialize model là một query.
3. Policy/Gate trong vòng lặp: `@can('update', $post)` với policy kiểm tra `$post->team->owner_id`.
4. Queue job nhận collection model: job serialize model, lúc chạy lấy lại từ DB mà không có quan hệ
   đã load.

Bắt ở môi trường dev thay vì chờ production chậm:

```php
<?php
declare(strict_types=1);

// app/Providers/AppServiceProvider.php, trong boot()
use Illuminate\Database\Eloquent\Model;

Model::preventLazyLoading(! $this->app->isProduction());
// Ném LazyLoadingViolationException mỗi khi lazy load. Production vẫn chạy bình thường.

Model::shouldBeStrict(! $this->app->isProduction());
// Gộp ba kiểm tra: preventLazyLoading, preventSilentlyDiscardingAttributes (gán thuộc tính
// không có trong $fillable thì ném lỗi thay vì lặng lẽ bỏ qua), preventAccessingMissingAttributes
// (đọc cột không có trong SELECT thì ném lỗi thay vì trả null).

Model::handleLazyLoadingViolationUsing(function (Model $model, string $relation): void {
    info(sprintf('Lazy load [%s] trên [%s]', $relation, $model::class));   // chỉ log, không ném
});
```

*Automatic eager loading* (`Model::automaticallyEagerLoadRelationships()`, có ở Laravel 12.x và 13):
khi bạn truy cập một quan hệ chưa load trên một model thuộc collection, Laravel lazy eager load
quan hệ đó cho **cả collection** gốc, biến N query thành 1. Bật riêng cho một collection bằng
`$users->withRelationshipAutoloading()`. Tiện, nhưng nó chỉ giảm số query, không giảm lượng dữ liệu:
vẫn phải biết nó đang kéo những gì vào RAM, và không thay được việc chọn `with`/`withCount` có chủ
đích ở các endpoint quan trọng.

Đối chiếu: Hibernate/JPA của Java có đúng vấn đề này (quan hệ `LAZY` truy cập trong vòng lặp), sửa
bằng `JOIN FETCH` hoặc `@EntityGraph`. Go thường dùng `database/sql` hoặc sqlc viết SQL tay nên N+1 ít
ẩn hơn, nhưng vẫn gặp khi gọi query trong vòng lặp.

#### Transaction trong Laravel

```php
<?php
declare(strict_types=1);

use App\Models\Order;
use Illuminate\Support\Facades\DB;

$order = DB::transaction(function () use ($cart): Order {
    $order = Order::create(['user_id' => $cart->userId, 'total' => $cart->total]);
    $order->items()->createMany($cart->items);
    DB::table('products')->where('id', $cart->productId)->where('stock', '>', 0)->decrement('stock');
    return $order;                          // giá trị trả về của closure là giá trị của transaction()
}, attempts: 3);
```

Laravel làm gì bên dưới (đọc từ `ManagesTransactions` của framework):

1. `beginTransaction()`: nếu chưa có transaction thì gửi `BEGIN`; nếu đang trong transaction (lồng
   nhau) thì tạo `SAVEPOINT trans2`, `trans3`... Transaction lồng nhau trong Laravel là savepoint,
   rollback lớp trong chỉ quay về savepoint.
2. Chạy closure. Nếu closure ném exception: rollback rồi ném lại exception.
3. Nếu exception là *lỗi concurrency* và còn lượt: chạy lại **toàn bộ closure** từ đầu. Laravel coi là
   lỗi concurrency: SQLSTATE `40001`, message chứa "Deadlock found", "Lock wait timeout exceeded", và
   vài message tương tự của DB khác. Nghĩa là không chỉ deadlock mà cả lock wait timeout cũng được
   retry.
4. Nếu đang ở transaction lồng (`transactions > 1`) mà gặp deadlock: không retry ở lớp trong, mà ném
   `DeadlockException` ra ngoài. Lý do: khi deadlock, InnoDB rollback **cả transaction**, savepoint
   của lớp trong cũng mất, nên chỉ lớp ngoài cùng retry được.
5. Closure chạy xong: nếu là lớp ngoài cùng thì `COMMIT`, rồi chạy các callback đăng ký bằng
   `DB::afterCommit()`.

⚠️ Vì closure có thể chạy lại, nó phải *chạy lại được an toàn* (idempotent với thế giới bên ngoài).
Gửi email, gọi API thanh toán, ghi file, tăng counter trên Redis trong closure thì mỗi lần retry làm
thêm một lần, còn rollback DB không thu hồi được chúng. Chỉ để thao tác DB bên trong.

⚠️ *Implicit commit*: DDL (`CREATE`, `ALTER`, `DROP`, `TRUNCATE`...) trong MySQL tự commit transaction
đang mở. Tài liệu Laravel cảnh báo chạy chúng qua `DB::statement()`/`DB::unprepared()` bên trong
transaction sẽ commit cả transaction mà Laravel không biết, và bộ đếm transaction level của Laravel
lệch với thực tế. Cùng lý do, migration của MySQL **không có tính nguyên tử**: migration có ba câu
`ALTER` lỗi ở câu thứ hai thì câu thứ nhất đã có hiệu lực, bảng `migrations` không ghi nhận, chạy lại
thì lỗi "column already exists". Mỗi migration nên chỉ làm một thay đổi schema. Postgres có
transactional DDL nên không gặp chuyện này.

⚠️ Bug kinh điển: **dispatch job bên trong transaction**.

```php
<?php
declare(strict_types=1);

use App\Jobs\SendOrderConfirmation;
use App\Models\Order;
use Illuminate\Support\Facades\DB;

DB::transaction(function () use ($data): void {
    $order = Order::create($data);
    SendOrderConfirmation::dispatch($order);   // job vào Redis NGAY, trước COMMIT
    // ... thêm vài query tốn 200ms
});
```

| Bước | Request web | Queue worker | Kết quả |
|---|---|---|---|
| 1 | `BEGIN`; `INSERT INTO orders` (id 42) | | Dòng 42 chưa commit, session khác không thấy |
| 2 | `dispatch()`: đẩy job `{order_id: 42}` vào Redis | | Job đã nằm trong queue |
| 3 | Đang chạy tiếp các query khác | Lấy job, `SELECT * FROM orders WHERE id = 42` | Không thấy dòng: `ModelNotFoundException`, job fail |
| 4 | `COMMIT` | | Đơn có trong DB nhưng email không được gửi (trừ khi job còn lượt retry) |
| 4' | (nhánh khác) Query sau lỗi, `ROLLBACK` | Job chạy sau khi đơn đã bị rollback | Email xác nhận cho một đơn không tồn tại |

Job được serialize chỉ gồm id của model (`SerializesModels`), worker phải đọc lại từ DB, và ở mức
isolation nào worker cũng không thấy dữ liệu chưa commit. Cách sửa:

```php
SendOrderConfirmation::dispatch($order)->afterCommit();   // chờ transaction ngoài cùng commit
```

- Bật `'after_commit' => true` cho queue connection trong `config/queue.php`: mọi job, queued
  listener, mailable, notification, broadcast dispatch trong transaction đều chờ commit; transaction
  rollback thì job bị bỏ. Có thể ép ngược một job cụ thể bằng `->beforeCommit()`.
- Các biến thể: event `implements ShouldDispatchAfterCommit`, listener
  `implements ShouldQueueAfterCommit`, observer `implements ShouldHandleEventsAfterCommit`, mailable và
  notification `->afterCommit()`.
- Không có transaction nào đang mở thì job được dispatch ngay, như bình thường.

⚠️ `afterCommit` vẫn để hở một khe: sau khi DB commit mà process chết (deploy, OOM) trước khi kịp đẩy
job vào Redis, hoặc Redis đang lỗi, thì job mất. Muốn "DB commit thì chắc chắn có job" phải dùng
*outbox pattern*: ghi một dòng vào bảng `outbox` trong **cùng transaction** với đơn hàng, một worker
riêng đọc bảng outbox và đẩy vào queue, chấp nhận gửi trùng nên consumer phải idempotent
([12-messaging.md](../12-messaging.md)).

#### Đọc tập dữ liệu lớn

`Order::where(...)->get()` trên 2 triệu dòng tạo 2 triệu object Eloquent (mỗi model tốn cỡ vài KB)
và chắc chắn vượt `memory_limit`. Các cách chia nhỏ:

| Cách | SQL sinh ra | RAM | Khi nào dùng |
|---|---|---|---|
| `get()` | 1 query, lấy hết | Toàn bộ | Tập nhỏ, có giới hạn rõ |
| `chunk(1000, fn)` | `ORDER BY id LIMIT 1000 OFFSET 0`, `OFFSET 1000`... | 1 chunk | Chỉ đọc, không sửa cột trong điều kiện lọc |
| `chunkById(1000, fn)` | `WHERE ... AND id > :last ORDER BY id LIMIT 1000` | 1 chunk | Mặc định nên dùng, nhất là khi callback sửa dữ liệu |
| `lazy()` / `lazyById()` | Như `chunk` / `chunkById` | 1 chunk | Muốn viết kiểu pipeline `->filter()->each()` |
| `cursor()` | 1 query duy nhất | 1 model hydrate, nhưng raw row vẫn buffered | Chỉ đọc, không cần eager load |

⚠️ Bẫy `chunk()` khi callback sửa chính cột đang lọc:

```php
<?php
declare(strict_types=1);

use App\Models\Invoice;
use Illuminate\Database\Eloquent\Collection;

// SAI: chỉ xử lý được khoảng một nửa
Invoice::where('status', 'pending')->chunk(1000, function (Collection $invoices): void {
    foreach ($invoices as $invoice) {
        $invoice->update(['status' => 'sent']);
    }
});
```

Diễn biến với 3.000 hoá đơn pending:

1. Chunk 1: `WHERE status='pending' LIMIT 1000 OFFSET 0` lấy hoá đơn 1..1000, đổi sang `sent`. Còn
   2.000 pending (hoá đơn 1001..3000).
2. Chunk 2: `OFFSET 1000` trên tập **mới** 2.000 dòng, bỏ qua 1001..2000, lấy 2001..3000.
3. Chunk 3: `OFFSET 2000` trên tập còn 1.000 dòng, rỗng, dừng. Hoá đơn 1001..2000 bị bỏ sót.

`chunkById` không bị vì nó không đếm vị trí mà nhớ id cuối cùng (`WHERE id > 1000`), đây chính là
*keyset pagination* (module 2.4). Nó còn nhanh hơn trên bảng lớn: `OFFSET 1000000` bắt MySQL đọc rồi
vứt một triệu dòng, còn `id > ?` seek thẳng vào index.

```php
Invoice::where('status', 'pending')->chunkById(1000, function (Collection $invoices): void {
    Invoice::whereKey($invoices->modelKeys())->update(['status' => 'sent']);   // 1 UPDATE mỗi chunk
});
```

Các bẫy nhỏ hơn, đều có trong tài liệu Laravel:

- `chunkById` tự thêm `where id > ?`. Nếu điều kiện của bạn có `orWhere` mà không bọc trong closure
  thì thành `a OR b AND id > ?`, sai logic và có thể lặp vô hạn. Luôn nhóm:
  `->where(fn ($q) => $q->where('credits', 1)->orWhere('credits', 2))->chunkById(...)`.
- Callback sửa khoá chính hoặc khoá ngoại dùng trong điều kiện thì chunk vẫn có thể bỏ sót.
- Query Builder `chunk()` bắt buộc có `orderBy` (thiếu thì ném exception); Eloquent tự thêm
  `ORDER BY` khoá chính. Không có thứ tự ổn định thì `LIMIT/OFFSET` trả về dòng lặp hoặc sót.
- `cursor()` chỉ giữ một model tại một thời điểm, nhưng như tài liệu Laravel ghi, PDO vẫn buffer
  toàn bộ raw result nên với tập rất lớn vẫn hết RAM; khi đó dùng `lazyById()`. `cursor()` cũng không
  eager load được quan hệ.
- Script chạy lâu (command, job) nhớ tắt query log nếu có bật (`DB::disableQueryLog()`), vì log giữ
  mọi câu SQL trong RAM.

#### Read/write connection

```php
// config/database.php
'mysql' => [
    'driver' => 'mysql',
    'read'  => ['host' => ['10.0.0.11', '10.0.0.12']],   // replica, chọn ngẫu nhiên mỗi request
    'write' => ['host' => ['10.0.0.10']],                // primary
    'sticky' => true,
    // các khoá còn lại (database, username, charset...) dùng chung cho cả read và write
],
```

Laravel chọn connection theo loại câu lệnh: `select()` dùng read PDO; `insert/update/delete/statement`
dùng write PDO. Hai ngoại lệ tự động: **trong transaction mọi câu đều đi primary**, và
`->useWritePdo()` (hoặc `lockForUpdate()`) ép một query đọc từ primary.

Vấn đề cần giải: replication từ primary sang replica là bất đồng bộ (module 3.4), có *replication lag*
từ vài mili giây tới vài phút. User vừa đổi tên, trang redirect đọc từ replica, thấy tên cũ, bấm lưu
lần nữa. Đây là vi phạm *read-your-writes* (đọc thấy chính dữ liệu mình vừa ghi).

`sticky => true`: trong một request, sau khi đã có một câu ghi, mọi câu đọc tiếp theo trong **cùng
request** dùng primary. Giới hạn cần nói được khi phỏng vấn:

- Chỉ trong phạm vi một request (một process). Request kế tiếp (sau redirect), queue job, request tới
  server khác đều không biết, vẫn đọc replica. Muốn read-your-writes xuyên request thì phải tự làm, ví
  dụ ghi một cờ "vừa ghi lúc T" vào session và đọc primary trong vài giây sau đó.
- Queue job dispatch ngay sau khi ghi có thể chạy trên replica chưa kịp nhận dữ liệu, gặp lỗi giống
  bug dispatch trong transaction. Job cần dữ liệu mới nhất thì đọc từ primary.
- Với Octane, trạng thái "đã ghi" được reset sau mỗi request, nên sticky vẫn đúng nghĩa per-request.

#### ORM sinh SQL tệ

| Viết | SQL thực tế | Nên viết |
|---|---|---|
| `Order::where(...)->get()->count()` | `SELECT *`, kéo hết về PHP rồi đếm | `->count()`: `SELECT COUNT(*)` |
| `->get()->sum('total')` | Như trên | `->sum('total')` |
| `if (Order::where(...)->count() > 0)` | Đếm hết các dòng khớp | `->exists()`: `SELECT EXISTS(SELECT * ...) AS exists` |
| `foreach ($rows as $r) { Model::find($r['id'])->update([...]); }` | 2N query | `upsert()` hoặc một `UPDATE ... WHERE id IN (...)` |
| `foreach (...) { Model::create([...]); }` | N `INSERT`, N lần fire event | `Model::insert([...])` theo lô (bỏ qua event và timestamps) |
| `Post::whereHas('comments', ...)` | `WHERE EXISTS (SELECT ... correlated)` | Ổn nếu có index trên `comments.post_id`; bảng lớn thì cân nhắc `whereIn` với subquery hoặc join |
| `->orderBy('created_at')->paginate()` trang 5000 | `LIMIT 15 OFFSET 74985` | `cursorPaginate()` (keyset) |

Về `upsert`: trên MySQL nó sinh `INSERT ... ON DUPLICATE KEY UPDATE`. ⚠️ Tài liệu Laravel ghi rõ:
driver MySQL/MariaDB **bỏ qua** tham số `uniqueBy`, luôn dùng mọi PRIMARY/UNIQUE index của bảng để
phát hiện trùng. Bảng có hai unique index thì một dòng có thể "trùng" theo index mà bạn không nghĩ
tới và update nhầm dòng.

Raw SQL hợp cho báo cáo, window function, CTE, thao tác hàng loạt. Raw vẫn phải bind:

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

// ĐÚNG: binding
$rows = DB::select('SELECT user_id, SUM(total) AS s FROM orders WHERE created_at >= ? GROUP BY user_id', [$from]);
// SAI: ghép chuỗi, injection
$rows = DB::select("SELECT * FROM orders WHERE status = '$status'");
// ⚠️ binding không dùng được cho tên cột/bảng hay hướng sort; whitelist thay vì bind
$input = (string) request()->query('dir', 'asc');
$dir = in_array($input, ['asc', 'desc'], true) ? $input : 'asc';
$q = DB::table('orders')->orderBy('created_at', $dir);
```

⚠️ `orderBy($request->input('sort'))`, `DB::raw($input)`, `whereRaw("... $input")` nhận chuỗi rồi
đưa thẳng vào SQL; binding chỉ bảo vệ **giá trị**. Tương tự, `whereIn` với hàng chục nghìn giá trị
sinh hàng chục nghìn placeholder (native prepare của MySQL giới hạn 65.535 placeholder mỗi câu); với
mảng số nguyên lớn dùng `whereIntegerInRaw`.

#### Quan sát

```php
<?php
declare(strict_types=1);

use Illuminate\Database\Connection;
use Illuminate\Database\Events\QueryExecuted;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

// AppServiceProvider::boot()
DB::listen(function (QueryExecuted $query): void {
    if ($query->time > 100) {                          // ms, thời gian của từng query
        Log::warning('slow query', ['sql' => $query->toRawSql(), 'ms' => $query->time]);
    }
});

DB::whenQueryingForLongerThan(500, function (Connection $connection, QueryExecuted $event): void {
    // Tổng thời gian query của cả request vượt 500 ms: bắt được N+1 mà từng query đều nhanh
    Log::warning('request tốn nhiều thời gian query', ['connection' => $connection->getName()]);
});
```

- `DB::listen` nhận mọi query kèm `sql`, `bindings`, `time`; `toRawSql()` ghép binding vào để copy
  sang `EXPLAIN`. Đừng log binding ra hệ thống log chung nếu có dữ liệu nhạy cảm.
- Laravel Debugbar (dev) và Telescope (dev/staging) hiển thị số query và query trùng lặp của từng
  request. Dấu hiệu N+1: cùng một câu SQL lặp lại hàng chục lần chỉ khác tham số.
- Production: APM (New Relic, Datadog, OpenTelemetry) cho số query mỗi transaction; phía MySQL có slow
  query log và `performance_schema` (module 2.3).
- Test có thể khoá số query: đếm qua `DB::listen` rồi `assertLessThanOrEqual`, để N+1 mới xuất hiện
  làm đỏ CI.

**Tóm tắt nhanh**
- PDO_MYSQL thuần mặc định emulate prepare (an toàn khi charset khai trong DSN); Laravel đặt native
  prepare. `DECIMAL` luôn là chuỗi, tính bằng bcmath.
- PHP-FPM không có pool: tổng connection ≈ server × `pm.max_children` (× 2 nếu read/write) + worker +
  cron, so với `max_connections` 151. Persistent connection rò trạng thái giữa request.
- N+1 không lên slow log; sửa bằng `with`/`load`/`withCount`, bắt bằng `preventLazyLoading` ở dev.
- `DB::transaction(fn, attempts)` chạy lại cả closure khi deadlock hoặc lock wait timeout, chỉ ở lớp
  ngoài; DDL tự commit; job dispatch trong transaction phải `afterCommit`, đảm bảo tuyệt đối thì outbox.
- Sửa dữ liệu khi duyệt lớn: `chunkById`, không `chunk`. `sticky` chỉ giữ read-your-writes trong một
  request.

**Nguồn**: [PHP: PDO_MYSQL](https://www.php.net/manual/en/ref.pdo-mysql.php) ·
[PHP: PDO::setAttribute](https://www.php.net/manual/en/pdo.setattribute.php) ·
[PHP: Persistent Connections](https://www.php.net/manual/en/features.persistent-connections.php) ·
[PHP: Buffered and Unbuffered queries](https://www.php.net/manual/en/mysqlinfo.concepts.buffering.php) ·
[PHP 8.1 UPGRADING (PDO MySQL)](https://github.com/php/php-src/blob/PHP-8.1/UPGRADING) ·
[Laravel: Database](https://laravel.com/docs/13.x/database) (read/write, sticky, deadlocks, implicit
commits, cumulative query time) ·
[Laravel: Chunking](https://laravel.com/docs/13.x/queries#chunking-results) ·
[Laravel: Eager Loading](https://laravel.com/docs/13.x/eloquent-relationships#eager-loading) ·
[Laravel: Eloquent Strictness](https://laravel.com/docs/13.x/eloquent#configuring-eloquent-strictness) ·
[Laravel: Jobs & Database Transactions](https://laravel.com/docs/13.x/queues#jobs-and-database-transactions) ·
mã nguồn `laravel/framework` 13.x (`Connectors/Connector.php`, `Concerns/ManagesTransactions.php`,
`ConcurrencyErrorDetector.php`)


---

### 2.8 Thiết kế schema nâng cao

Module này trả lời: khi nào được phá quy tắc chuẩn hoá, và các mẫu thiết kế hay gặp (soft delete,
cây, JSON, polymorphic, audit, enum) có cái giá nào mà ORM giấu đi. Các quyết định ở đây rất khó đổi
khi bảng đã có trăm triệu dòng, nên người phỏng vấn muốn nghe bạn nói được cái giá của từng lựa chọn.

#### Denormalize có kiểm soát

*Denormalize* là cố ý lưu thêm dữ liệu dẫn xuất (tính ra được từ dữ liệu khác) để đọc nhanh hơn. Ví dụ
kinh điển là `posts.comments_count`: trang danh sách hiển thị 50 bài, mỗi bài kèm số comment. Không có
cột đếm thì mỗi lần hiển thị phải `COUNT(*)` trên bảng comments (hoặc `withCount`), với bài hot có
hàng trăm nghìn comment thì tốn thật.

Cái giá là phải giữ bản sao khớp với nguồn. Ba cách, từ chặt tới lỏng:

1. **Cập nhật trong cùng transaction** với thao tác gốc. Luôn khớp, nhưng mọi comment mới đều ghi
   vào **cùng một dòng** `posts`, và dòng đó thành *hot row*: các transaction xếp hàng chờ lock dòng
   (module 2.6). Bài viral có hàng nghìn comment mỗi phút là thấy ngay.
2. **Cập nhật bất đồng bộ** qua event/queue, hoặc gom lại cộng theo lô mỗi vài giây. Không tranh lock,
   chấp nhận lệch trong vài giây.
3. **Job đối soát** định kỳ tính lại từ nguồn và sửa chỗ lệch. Nên có kể cả khi đã dùng cách 1 hoặc 2,
   vì bug, xoá tay, import dữ liệu đều làm lệch.

```php
<?php
declare(strict_types=1);

use App\Models\Post;

// SAI: read-modify-write ở PHP, hai request đồng thời làm mất một lần cộng (lost update, module 1.3)
$post->comments_count = $post->comments_count + 1;
$post->save();

// ĐÚNG: để DB cộng nguyên tử: UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?
$post->increment('comments_count');
```

Phân biệt denormalize với dữ liệu lịch sử. ⚠️ `order_items.unit_price` (giá lúc mua) **không phải**
bản sao thừa của `products.price`: giá sản phẩm đổi thì đơn cũ không được đổi theo. Tương tự với tên
sản phẩm, địa chỉ giao hàng, thuế suất tại thời điểm đặt. Đây là *snapshot*, là sự thật riêng của
đơn hàng, nên bắt buộc lưu, không có chuyện "đồng bộ".

Khi cần tổng hợp nặng hơn (doanh thu theo ngày), dùng *bảng tổng hợp* (summary table) cập nhật định
kỳ. MySQL không có materialized view; Postgres có `CREATE MATERIALIZED VIEW` kèm
`REFRESH MATERIALIZED VIEW CONCURRENTLY`.

Nguyên tắc: chuẩn hoá trước, denormalize khi có số đo chứng minh cần, và khi làm thì ghi rõ nguồn
thật là gì và cách đối soát.

#### Soft delete và unique

*Soft delete* là không xoá dòng mà đặt `deleted_at = NOW()`; dòng "đã xoá" vẫn nằm trong bảng.

- Lợi: khôi phục được khi user xoá nhầm, giữ lịch sử và tham chiếu (đơn hàng cũ vẫn trỏ tới sản phẩm
  đã ngừng bán).
- Giá: mọi query phải nhớ lọc `deleted_at IS NULL`. Trait `SoftDeletes` của Laravel thêm một *global
  scope* tự chèn `whereNull('deleted_at')` vào query Eloquent của model đó (bỏ qua bằng
  `withTrashed()`, chỉ lấy dòng đã xoá bằng `onlyTrashed()`, xoá thật bằng `forceDelete()`). Nhưng
  `DB::table(...)`, raw SQL, `join()` sang bảng soft delete, báo cáo BI đọc thẳng DB thì không có scope,
  và đây là nơi bug "user đã xoá vẫn hiện" xuất hiện.
- Bảng phình dần; index nên có `deleted_at` (ví dụ `(tenant_id, deleted_at, created_at)`) vì gần như
  mọi query đều lọc nó.
- ⚠️ Soft delete không phải là xoá dữ liệu cá nhân theo yêu cầu pháp lý (GDPR, quy định bảo vệ dữ
  liệu cá nhân của Việt Nam): dữ liệu vẫn nằm đó. Cần quy trình xoá thật hoặc ẩn danh hoá.

⚠️ Bẫy unique. Muốn "email không trùng giữa các user chưa xoá, nhưng user đã xoá được đăng ký lại":

```sql
CREATE TABLE users (id BIGINT AUTO_INCREMENT PRIMARY KEY, email VARCHAR(255) NOT NULL,
  deleted_at DATETIME NULL, UNIQUE KEY uq_email_deleted (email, deleted_at));
INSERT INTO users (email) VALUES ('a@x.com');
INSERT INTO users (email) VALUES ('a@x.com');   -- THÀNH CÔNG: hai user active trùng email!
```

Unique index coi các NULL là khác nhau (module 1.1), nên `('a@x.com', NULL)` và `('a@x.com', NULL)`
không vi phạm. Index này chỉ chặn trùng giữa các dòng đã xoá cùng thời điểm, tức là vô dụng. Cách sửa:

```sql
-- MySQL: generated column chỉ có giá trị khi dòng còn active, unique trên cột đó
CREATE TABLE users (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255) NOT NULL,
  deleted_at DATETIME NULL,
  email_active VARCHAR(255) GENERATED ALWAYS AS (IF(deleted_at IS NULL, email, NULL)) VIRTUAL,
  UNIQUE KEY uq_email_active (email_active)
);
-- Dòng đã xoá có email_active = NULL, nhiều NULL không vi phạm unique; dòng active thì bị chặn trùng.

-- Postgres: partial unique index, chỉ index các dòng thoả WHERE
CREATE UNIQUE INDEX uq_email_active ON users (email) WHERE deleted_at IS NULL;
```

Postgres 15 trở lên còn có `UNIQUE NULLS NOT DISTINCT` nếu muốn coi các NULL là bằng nhau. Một cách
khác cho cả hai DB: không soft delete mà chuyển dòng đã xoá sang bảng `users_archive`, bảng chính giữ
unique đơn giản.

#### Khoá ngoại

*Khoá ngoại* (foreign key, FK) là ràng buộc "giá trị ở cột này phải tồn tại ở bảng cha". DB từ chối
`INSERT INTO orders (user_id) VALUES (999)` nếu user 999 không có, kể cả khi app có bug, script sửa
tay chạy sai, hay hai service cùng ghi. Đó là bất biến mà code app không đảm bảo được một cách tuyệt
đối.

Cơ chế trong InnoDB:

1. Cột con phải có index; InnoDB tự tạo nếu chưa có. Laravel:
   `$table->foreignId('user_id')->constrained()` tạo cột và FK (index do InnoDB tự thêm).
2. Khi insert/update dòng con, InnoDB kiểm tra dòng cha và đặt **shared lock** (S lock) trên dòng cha
   để nó không bị xoá trong lúc transaction con chưa xong.
3. Khi xoá/sửa khoá dòng cha, InnoDB tra index của bảng con, rồi làm theo *referential action*:
   `RESTRICT`/`NO ACTION` (mặc định, trong InnoDB hai cái như nhau: từ chối ngay), `CASCADE` (xoá/sửa
   theo), `SET NULL`.
4. MySQL 8.4 mặc định `restrict_fk_on_non_standard_key = ON`: FK phải trỏ tới PRIMARY KEY hoặc UNIQUE
   key của bảng cha (trước đây InnoDB cho trỏ tới index không unique, một mở rộng phi chuẩn).

Cái giá:

- Mỗi lần ghi bảng con là thêm một lần tra bảng cha.
- S lock trên dòng cha gây deadlock trong một mẫu rất phổ biến: thêm item vào đơn rồi cập nhật tổng
  tiền của đơn.

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `BEGIN; INSERT INTO order_items (order_id, ...) VALUES (42, ...);` | | A giữ S lock trên `orders` id 42 (do FK) |
| 2 | | `BEGIN; INSERT INTO order_items (order_id, ...) VALUES (42, ...);` | B cũng giữ S lock trên id 42 (S tương thích S) |
| 3 | `UPDATE orders SET total = total + 10 WHERE id = 42;` | | A cần X lock, chờ S của B |
| 4 | | `UPDATE orders SET total = total + 5 WHERE id = 42;` | B cần X lock, chờ S của A: deadlock, một bên bị rollback |

  Sửa: khoá dòng cha trước (`SELECT ... FROM orders WHERE id = 42 FOR UPDATE`, hoặc `UPDATE orders`
  trước rồi mới insert item), để mọi transaction xếp hàng ở cùng một chỗ.
- `ON DELETE CASCADE` trên cây quan hệ lớn: xoá một user kéo theo xoá hàng triệu dòng trong một
  transaction, giữ lock lâu, undo log phình. Ngoài ra thao tác cascade của FK **không kích hoạt
  trigger** của bảng con, và không fire event Eloquent (`deleting`) của model con.
- FK không hoạt động giữa hai database server, hai shard, hai service. Bảng InnoDB *partitioned* cũng
  không được có FK (module 3.6).
- Import dữ liệu lớn thường tắt tạm `SET foreign_key_checks = 0`; khi bật lại, MySQL **không** kiểm tra
  lại dữ liệu đã nạp, dữ liệu mồ côi lọt vào im lặng.

Thực tế: monolith một DB thì nên dùng FK, cái giá nhỏ so với dữ liệu mồ côi phải dọn sau này. Hệ đã
shard hoặc chia microservice thì kiểm tra ở tầng app kèm job đối soát tìm dòng mồ côi. Dùng FK nhưng
tránh `CASCADE` trên bảng lớn, xoá theo lô bằng job.

#### Dữ liệu dạng cây

Danh mục sản phẩm, comment lồng nhau, sơ đồ tổ chức, thư mục. SQL không có kiểu "cây", nên có bốn
cách mã hoá, mỗi cách tối ưu một loại thao tác:

| Cách | Lưu thế nào | Lấy cả cây con | Di chuyển một node | Khi nào dùng |
|---|---|---|---|---|
| Adjacency list | Cột `parent_id` | Recursive CTE | Rẻ, sửa 1 dòng | Mặc định, đủ cho hầu hết trường hợp |
| Materialized path | Cột `path = '/1/5/12/'` | `LIKE '/1/5/%'`, dùng được index | Sửa path của cả cây con | Đọc nhiều, ít di chuyển |
| Nested set | Hai cột `lft`, `rgt` | Một range query | Rất đắt, đánh số lại nửa bảng | Cây gần như không đổi |
| Closure table | Bảng riêng lưu mọi cặp (tổ tiên, con cháu, độ sâu) | Join đơn giản | Xoá/thêm các cặp của cây con | Cần linh hoạt, chấp nhận tốn dòng |

*Adjacency list* là cách tự nhiên nhất: mỗi node trỏ về cha. Bill Karwin (*SQL Antipatterns*, chương
*Naive Trees*) gọi nó là "naive" vì trước khi có recursive CTE, lấy cả cây con phải join N lần hoặc
query lặp trong app. Từ MySQL 8.0 thì không còn là vấn đề:

```sql
CREATE TABLE categories (id INT PRIMARY KEY, parent_id INT NULL, name VARCHAR(50),
  INDEX (parent_id), FOREIGN KEY (parent_id) REFERENCES categories(id));
INSERT INTO categories VALUES (1,NULL,'Điện tử'),(2,1,'Điện thoại'),(3,2,'Android'),(4,1,'Laptop');

WITH RECURSIVE sub AS (
  SELECT id, name, 0 AS depth FROM categories WHERE id = 1          -- anchor: node gốc
  UNION ALL
  SELECT c.id, c.name, s.depth + 1 FROM categories c JOIN sub s ON c.parent_id = s.id  -- mỗi vòng xuống 1 tầng
)
SELECT * FROM sub;   -- Điện tử 0, Điện thoại 1, Laptop 1, Android 2 (minh hoạ; không ORDER BY thì thứ tự dòng không đảm bảo)
```

Mỗi vòng đệ quy là một lần tra index `parent_id`. ⚠️ Dữ liệu lỗi có vòng (A là cha B, B là cha A) làm
CTE chạy mãi; MySQL chặn ở `cte_max_recursion_depth` (mặc định 1000) và báo lỗi. Có thể giữ thêm cột
`depth` hoặc kiểm tra vòng khi di chuyển node.

*Materialized path* lưu đường dẫn từ gốc: Android có `path = '/1/2/3/'`. Lấy cây con của Điện tử là
`WHERE path LIKE '/1/%'`, là prefix nên seek được index (module 1.2); tổ tiên của một node đọc thẳng
từ chuỗi; độ sâu là số dấu `/`. Di chuyển node phải sửa mọi con cháu:
`UPDATE categories SET path = CONCAT('/9/', SUBSTRING(path, LENGTH('/1/') + 1)) WHERE path LIKE '/1/2/%'`.
Không có FK nào bảo vệ tính đúng của `path`.

*Closure table* lưu mọi cặp tổ tiên và con cháu, kể cả cặp node với chính nó:

```sql
CREATE TABLE category_paths (ancestor INT, descendant INT, depth INT,
  PRIMARY KEY (ancestor, descendant), INDEX (descendant));
-- Cây trên: (1,1,0),(1,2,1),(1,3,2),(1,4,1),(2,2,0),(2,3,1),(3,3,0),(4,4,0)
SELECT c.* FROM categories c JOIN category_paths p ON p.descendant = c.id WHERE p.ancestor = 1;  -- cây con
SELECT c.* FROM categories c JOIN category_paths p ON p.ancestor = c.id WHERE p.descendant = 3; -- tổ tiên
```

Có FK được trên cả hai cột, query đơn giản, nhưng số dòng có thể tới O(n × độ sâu).

*Nested set* đánh số mỗi node bằng hai giá trị `lft`, `rgt` theo thứ tự duyệt cây, cây con là
`WHERE lft BETWEEN parent.lft AND parent.rgt`. Đọc rất nhanh, nhưng chèn một node phải dịch `lft/rgt`
của gần nửa bảng, nên chỉ hợp với cây gần như tĩnh.

Chọn theo thao tác: mặc định adjacency list + recursive CTE; cần đọc tổ tiên/cây con cực nhiều thì
thêm materialized path hoặc closure table bên cạnh `parent_id`.

#### JSON và EAV

Kiểu `JSON` của MySQL không lưu văn bản mà chuyển sang **định dạng nhị phân** lúc ghi: server kiểm tra
JSON hợp lệ (không hợp lệ thì lỗi), và đọc được một key hay phần tử mảng mà không phải parse lại cả
tài liệu. Một số chi tiết theo tài liệu MySQL 8.4:

- Kích thước xấp xỉ `LONGBLOB`, bị giới hạn bởi `max_allowed_packet`. Xem thực tế bằng
  `JSON_STORAGE_SIZE()`.
- Key trùng thì giữ key **cuối cùng**; thứ tự key không được đảm bảo; chuỗi so sánh theo
  `utf8mb4_bin` (phân biệt hoa thường).
- `col->'$.a'` trả giá trị JSON (còn dấu nháy), `col->>'$.a'` trả chuỗi đã bỏ nháy (tương đương
  `JSON_UNQUOTE(JSON_EXTRACT(...))`).
- Không index trực tiếp cột JSON. Index qua generated column, hoặc *multi-valued index* cho mảng
  (InnoDB, dùng được với `MEMBER OF()`, `JSON_CONTAINS()`, `JSON_OVERLAPS()`; chuỗi trong index này
  dùng collation `utf8mb4_0900_as_cs`, tức phân biệt hoa thường).
- Cập nhật từng phần tại chỗ (*partial update*) chỉ khi dùng `JSON_SET`, `JSON_REPLACE`,
  `JSON_REMOVE` trên chính cột đó và giá trị mới không lớn hơn giá trị cũ; gán cả tài liệu
  (`SET attrs = '...'`, cũng là cách Eloquent `save()` làm) thì ghi lại toàn bộ.

```sql
CREATE TABLE products (
  id BIGINT PRIMARY KEY,
  type VARCHAR(20) NOT NULL,
  attrs JSON NOT NULL,
  color VARCHAR(20) GENERATED ALWAYS AS (attrs->>'$.color') VIRTUAL,
  INDEX idx_color (color),
  INDEX idx_tags ((CAST(attrs->'$.tags' AS CHAR(30) ARRAY)))        -- multi-valued index
);
INSERT INTO products VALUES (1, 'shirt', '{"color":"red","size":"M","tags":["sale","summer"]}', DEFAULT);
EXPLAIN SELECT id FROM products WHERE color = 'red';                  -- dùng idx_color
EXPLAIN SELECT id FROM products WHERE 'sale' MEMBER OF (attrs->'$.tags');  -- dùng idx_tags
```

Laravel đọc/ghi field JSON bằng cú pháp mũi tên: `Product::where('attrs->color', 'red')` sinh
`json_unquote(json_extract(attrs, '$."color"'))`, và cast `'attrs' => 'array'` hoặc `AsArrayObject`.
⚠️ Query kiểu này **không** dùng được `idx_color` trừ khi biểu thức khớp với định nghĩa generated
column; muốn chắc thì query thẳng cột `color`.

JSON hợp lý khi:

- Thuộc tính khác nhau theo từng loại sản phẩm (áo có size, laptop có RAM) và hiếm khi lọc theo.
- Lưu nguyên payload để tra cứu về sau (webhook nhận được, response của cổng thanh toán).
- Dữ liệu cấu hình, preference của user.

Dấu hiệu JSON đang được dùng thay cho thiết kế: thường xuyên lọc, join hoặc sort theo một field bên
trong; cần ràng buộc (NOT NULL, FK, unique) trên field đó; cần cập nhật từng field với tần suất cao.
Khi đó field ấy nên là cột thật. Cần ràng buộc hình dạng thì có thể thêm
`CHECK (JSON_SCHEMA_VALID('{...schema...}', attrs))`.

⚠️ *EAV* (entity-attribute-value) là thiết kế "một bảng cho mọi thuộc tính tuỳ ý":

```sql
CREATE TABLE product_attributes (product_id BIGINT, attribute VARCHAR(50), value VARCHAR(255),
  PRIMARY KEY (product_id, attribute));
-- Lấy một sản phẩm với 3 thuộc tính dạng cột: mỗi thuộc tính một lần join (hoặc pivot bằng GROUP BY)
SELECT p.id, c.value AS color, s.value AS size, w.value AS weight
FROM products p
LEFT JOIN product_attributes c ON c.product_id = p.id AND c.attribute = 'color'
LEFT JOIN product_attributes s ON s.product_id = p.id AND s.attribute = 'size'
LEFT JOIN product_attributes w ON w.product_id = p.id AND w.attribute = 'weight';
```

Karwin liệt kê các vấn đề: mọi giá trị là chuỗi nên mất kiểu (không biết `'10'` là số hay chữ, sort
sai); không đặt được `NOT NULL`, FK, `CHECK` cho từng thuộc tính; gõ nhầm tên thuộc tính
(`'colour'`) tạo thuộc tính mới; lấy một object cần nhiều join nên query dài và chậm. Magento là
ví dụ nổi tiếng: EAV cho catalog linh hoạt, nhưng phải thêm các bảng "flat" và index riêng mới chạy
nổi. Thay thế: cột thật cho thuộc tính chung, cột JSON cho phần thay đổi theo loại, hoặc mỗi loại
sản phẩm một bảng riêng (*class table inheritance*).

#### Polymorphic association

Laravel `morphTo`/`morphMany` cho một bảng `comments` gắn được vào cả `posts` và `videos`:

```php
// migration: $table->morphs('commentable') tạo commentable_type VARCHAR, commentable_id BIGINT
// và index (commentable_type, commentable_id)
// comments: (id, body, commentable_type = 'App\Models\Post', commentable_id = 42)
```

Cột `commentable_id` trỏ tới bảng nào tuỳ giá trị của cột khác, nên **không đặt được FK**: DB không
biết phải kiểm tra bảng nào. Hệ quả: xoá post thì comment mồ côi ở lại, gõ sai type không ai chặn, join
trong SQL thuần phải `CASE` theo type. Karwin xếp đây là antipattern.

⚠️ Mặc định Laravel lưu **tên class đầy đủ** vào cột type. Đổi namespace hay tên model là dữ liệu cũ
hỏng. Luôn dùng `Relation::enforceMorphMap(['post' => Post::class, 'video' => Video::class])` để lưu
alias ngắn và ổn định; thêm morph map vào app đang chạy thì phải migrate các giá trị type cũ.

Hai cách thay thế có FK (nằm trong *Nắm chắc khi* của plan):

```sql
-- Cách 1: "exclusive arc": mỗi loại cha một cột FK nullable, CHECK đúng một cột có giá trị
CREATE TABLE comments (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  body TEXT NOT NULL,
  post_id  BIGINT NULL,
  video_id BIGINT NULL,
  FOREIGN KEY (post_id)  REFERENCES posts(id),
  FOREIGN KEY (video_id) REFERENCES videos(id),
  CHECK ((post_id IS NOT NULL) + (video_id IS NOT NULL) = 1)
);

-- Cách 2: bảng comments chung, mỗi loại cha một bảng nối riêng
CREATE TABLE post_comments  (post_id BIGINT, comment_id BIGINT PRIMARY KEY,
  FOREIGN KEY (post_id) REFERENCES posts(id), FOREIGN KEY (comment_id) REFERENCES comments(id));
CREATE TABLE video_comments (video_id BIGINT, comment_id BIGINT PRIMARY KEY,
  FOREIGN KEY (video_id) REFERENCES videos(id), FOREIGN KEY (comment_id) REFERENCES comments(id));
```

- Cách 1 đơn giản, query nhanh; thêm loại cha mới là thêm cột. ⚠️ Theo tài liệu MySQL, cột nằm trong
  `CHECK` không được dùng trong referential action của FK (`ON DELETE CASCADE`, `SET NULL`...), nên
  cách này phải xoá comment ở tầng app hoặc để FK mặc định từ chối xoá cha còn comment.
- Cách 2 linh hoạt, `comment_id PRIMARY KEY` đảm bảo một comment thuộc tối đa một cha mỗi loại (muốn
  chặn một comment vừa thuộc post vừa thuộc video thì cần thêm kiểm tra ở app).
- Cách thứ ba Karwin nêu: tạo *bảng cha chung* (`commentables(id)`), `posts.id` và `videos.id` đều là
  FK tới nó, `comments.commentable_id` trỏ FK vào bảng chung.

#### Audit và history

Ghi lại ai đổi gì, lúc nào. Ba cách, khác nhau ở độ đầy đủ và ngữ cảnh:

| Cách | Không bao giờ sót? | Biết user/lý do? | Ghi chú |
|---|---|---|---|
| Từ app (observer Eloquent, package kiểu `owen-it/laravel-auditing`) | Không: `DB::table()`, raw SQL, `update()` hàng loạt, sửa tay đều lọt | Có | Dễ làm nhất, chạy trong cùng transaction |
| Trigger trong DB | Có, mọi đường ghi đều qua | Không trực tiếp; mẹo: app `SET @app_user_id = 42` đầu request, trigger đọc biến session | Logic nằm trong DB, khó test, làm chậm mọi lần ghi |
| CDC (*change data capture*, ví dụ Debezium đọc binlog) | Có | Không, trừ khi app ghi user vào chính dòng dữ liệu (`updated_by`) | Không đụng code app, không làm chậm ghi, nhưng thêm hạ tầng (Kafka...) |

Với đơn hàng, trạng thái là thứ hay bị hỏi: lưu `orders.status` (trạng thái hiện tại, để query nhanh)
**và** bảng `order_status_history(order_id, from_status, to_status, changed_by, reason, created_at)`
ghi trong cùng transaction với lần đổi trạng thái. Bảng history là nguồn để trả lời "đơn này bị huỷ
lúc nào, bởi ai".

Dữ liệu cần tra "tại thời điểm X" (bảng giá, hợp đồng, thuế suất) thì lưu theo khoảng hiệu lực:

```sql
CREATE TABLE product_prices (product_id BIGINT, price DECIMAL(19,4), valid_from DATETIME NOT NULL,
  valid_to DATETIME NULL, PRIMARY KEY (product_id, valid_from));
-- Giá lúc 2026-03-01 10:00; khoảng nửa mở [valid_from, valid_to), NULL là "còn hiệu lực"
SELECT price FROM product_prices
WHERE product_id = 1 AND valid_from <= '2026-03-01 10:00'
  AND (valid_to IS NULL OR valid_to > '2026-03-01 10:00');
```

Đổi giá là đóng dòng cũ (`valid_to = NOW()`) và thêm dòng mới trong một transaction. DB không tự chặn
hai khoảng chồng nhau (Postgres chặn được bằng exclusion constraint), nên phải khoá theo
`product_id` khi ghi.

⚠️ Bảng audit/history lớn nhanh hơn mọi bảng khác và gần như chỉ ghi thêm. Partition theo thời gian
(theo tháng) ngay từ đầu để xoá dữ liệu cũ bằng `DROP PARTITION` thay vì `DELETE` hàng trăm triệu
dòng (module 3.6). Lưu ý hai giới hạn của partitioning trong MySQL: bảng partitioned không có FK, và
cột partition phải nằm trong **mọi** unique key kể cả PK, nên PK thường thành `(id, created_at)`.

#### Enum

`ENUM('pending','paid','shipped')` của MySQL lưu mỗi giá trị bằng số thứ tự 1 hoặc 2 byte, gọn và tự
chặn giá trị lạ (strict mode báo lỗi). Các cái giá:

- Thêm giá trị mới phải `ALTER TABLE`. Thêm vào **cuối** danh sách thường là thay đổi metadata tức thì
  (online DDL, trừ khi số phần tử vượt ngưỡng làm đổi kích thước lưu trữ); chèn vào giữa, đổi thứ tự,
  xoá giá trị thì phải dựng lại bảng.
- `ORDER BY status` sort theo **thứ tự khai báo** (số thứ tự bên trong), không theo chữ cái.
- Danh sách giá trị nằm trong schema, không gắn được thêm thông tin (nhãn hiển thị, thứ tự, cờ active),
  và các DB khác không có kiểu tương đương (Postgres có `CREATE TYPE ... AS ENUM` với hạn chế riêng).

Cách thay thế:

- `VARCHAR(20)` kèm `CHECK (status IN ('pending','paid','shipped'))`: đọc dữ liệu ra dễ hiểu, sort theo
  chữ; đổi danh sách vẫn phải sửa constraint.
- Bảng lookup `order_statuses(code PK, label, sort_order)` kèm FK: thêm giá trị là `INSERT`, gắn được
  metadata. Hợp khi danh sách do nghiệp vụ quản lý.
- Tầng app dùng *backed enum* của PHP 8.1 với cast Eloquent, để code không còn chuỗi rời rạc:

```php
<?php
declare(strict_types=1);

namespace App\Enums;

enum OrderStatus: string
{
    case Pending = 'pending';
    case Paid    = 'paid';
    case Shipped = 'shipped';
}

// Trong model Order:
// protected function casts(): array { return ['status' => OrderStatus::class]; }
// $order->status === OrderStatus::Paid;        // so sánh enum, không so chuỗi
// Order::where('status', OrderStatus::Paid)->get();
```

Enum PHP và CHECK/lookup ở DB bổ sung cho nhau: enum bảo vệ code, ràng buộc DB bảo vệ dữ liệu khỏi
mọi đường ghi khác.

#### Áp dụng: các quyết định khi thiết kế schema đơn hàng

Tiêu chí "Nắm chắc khi" của plan yêu cầu tự thiết kế `orders`, `order_items`, `payments`, lịch sử
trạng thái. Đây là các câu hỏi bạn phải có câu trả lời và lý do cho từng bảng (tự viết DDL rồi đối
chiếu với các nhóm ở trên):

1. Những giá trị nào là snapshot tại lúc đặt (giá, tên sản phẩm, địa chỉ, thuế) và phải lưu trong đơn?
2. Tổng tiền của đơn là cột lưu sẵn hay tính từ items? Nếu lưu, giữ đồng bộ bằng cách nào và tránh
   deadlock FK ra sao?
3. Một đơn có thể có nhiều payment (thanh toán thất bại rồi thử lại, hoàn tiền một phần) không? Khoá
   nào chặn ghi nhận trùng một giao dịch từ cổng thanh toán (idempotency)?
4. Trạng thái lưu kiểu gì, chuyển trạng thái nào hợp lệ, lịch sử ghi ở đâu và trong transaction nào?
5. Kiểu cột cho tiền, tiền tệ, thời gian (module 1.4); FK nào đặt, `CASCADE` hay không; đơn có được
   soft delete không.
6. Bảng nào sẽ lớn nhanh nhất, index nào phục vụ các query chính ("đơn của user X mới nhất", "đơn
   pending quá 30 phút")?

**Tóm tắt nhanh**
- Denormalize có chủ đích: có nguồn thật, cách đồng bộ và job đối soát; giá tại lúc mua là snapshot
  chứ không phải bản sao thừa.
- `UNIQUE(email, deleted_at)` không chặn trùng vì NULL khác NULL; MySQL dùng generated column,
  Postgres dùng partial index.
- FK giữ dữ liệu sạch nhưng đặt S lock trên dòng cha (deadlock insert con rồi update cha), không qua
  shard/service, không dùng với bảng partitioned.
- Cây: mặc định `parent_id` + recursive CTE; closure table hoặc materialized path khi đọc nhiều.
- JSON cho thuộc tính biến thiên, index qua generated column; EAV và polymorphic mất kiểu, mất FK.
  Nêu được exclusive arc và bảng nối riêng.
- Audit: app biết ai, trigger/CDC không sót; bảng history partition theo thời gian từ đầu.

**Nguồn**: [MySQL: The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html) ·
[MySQL: CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html) ·
[MySQL: FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html) ·
[MySQL: Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html) ·
[MySQL: WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.4/en/with.html) ·
[Laravel: Polymorphic Relationships](https://laravel.com/docs/13.x/eloquent-relationships#polymorphic-relationships) ·
[Laravel: Soft Deleting](https://laravel.com/docs/13.x/eloquent#soft-deleting) ·
*SQL Antipatterns* (Bill Karwin): các chương *Naive Trees*, *Entity-Attribute-Value*, *Polymorphic
Associations* · *High Performance MySQL* 4th ed., chương *Schema Design and Management*

---

## Chặng 3: Senior

### 3.1 Bên trong InnoDB: log, bộ nhớ, MVCC

Module này trả lời hai câu senior hay bị hỏi: "từ lúc `COMMIT` tới lúc dữ liệu an toàn, InnoDB làm
gì", và "vì sao một transaction quên đóng làm cả DB chậm dần". Cả hai đều cần một bức tranh chung
về các thành phần bên trong InnoDB, nên bắt đầu từ sơ đồ.

```
                        MySQL server (tầng SQL: parser, optimizer, executor)
                                  |                         |
                                  |                   binlog cache (mỗi session)
                                  v                         |
 +-------------------- InnoDB, trong RAM ---------------+   |
 |  Buffer pool (innodb_buffer_pool_size, mặc định 128MB)|   |
 |   +-------------------------------------------+       |   |
 |   | page dữ liệu + index (16 KB mỗi page)     |       |   |
 |   | LRU: [ young 5/8 | old 3/8 ]  dirty pages |       |   |
 |   | page undo (bản cũ của dòng)               |       |   |
 |   +-------------------------------------------+       |   |
 |  Log buffer (redo chưa ghi xuống đĩa)                 |   |
 +------------|--------------------------|---------------+   |
              | khi COMMIT               | flush nền          | khi COMMIT
              v (ghi tuần tự + fsync)    v (page cũ trước)    v (ghi + fsync)
 +--------------------+    +---------------------+     +-------------------+
 | Redo log           |    | Doublewrite files   |     | Binlog            |
 | #innodb_redo/      |    | #ib_16384_0.dblwr   |     | binlog.000123 ... |
 | 32 file, vòng tròn |    | (bản sao an toàn)   |     | (replication,PITR)|
 +--------------------+    +----------|----------+     +-------------------+
                                      v
                           +----------------------------+
                           | Tablespace: t.ibd (bảng),  |
                           | undo_001, undo_002 (undo), |
                           | ibdata1 (system)           |
                           +----------------------------+
```

Đọc sơ đồ theo ba luồng: (1) query đọc/sửa page trong buffer pool; (2) lúc commit, InnoDB ghi redo
và MySQL ghi binlog, cả hai đều tuần tự và nhỏ; (3) page dirty được ghi xuống tablespace sau, ở chế
độ nền, và luôn đi qua doublewrite trước.

#### Buffer pool

*Buffer pool* là vùng RAM nơi InnoDB giữ các page (16 KB) của bảng và index. Mọi đọc ghi đều diễn
ra trên page trong buffer pool; đĩa chỉ được chạm khi page chưa có trong RAM (đọc vào) hoặc khi
page đã sửa cần ghi ra (flush).

- Mặc định `innodb_buffer_pool_size` chỉ 128 MB, quá nhỏ cho production. Tài liệu MySQL ghi rằng
  trên máy chỉ chạy DB, thường cấp tới 80% RAM cho buffer pool. Phần còn lại dành cho hệ điều hành,
  bộ nhớ theo từng connection (sort buffer, join buffer, bảng tạm) và binlog cache.
- Buffer pool lớn được chia thành nhiều *instance* (`innodb_buffer_pool_instances`, chỉ áp dụng
  khi pool từ 1 GB trở lên) để giảm tranh chấp mutex giữa các thread.
- Có thể đổi kích thước lúc đang chạy: `SET GLOBAL innodb_buffer_pool_size = ...`.

Cơ chế thay thế page là một biến thể của LRU (*least recently used*, bỏ page lâu không dùng nhất)
có *midpoint insertion*:

1. Danh sách page chia hai phần: *young* (đầu danh sách, 5/8) và *old* (đuôi, 3/8, chỉnh bằng
   `innodb_old_blocks_pct`, mặc định 37).
2. Page mới đọc từ đĩa được chèn vào giữa, tức đầu phần old, không phải đầu danh sách.
3. Page ở phần old chỉ được đẩy lên young nếu được truy cập lại sau ít nhất
   `innodb_old_blocks_time` (mặc định 1000 ms) kể từ lần đầu.
4. Page không ai dùng trôi dần về đuôi old và bị loại khi cần chỗ.

Vì sao phức tạp vậy: một full table scan (báo cáo, `mysqldump`) đọc hàng triệu page chỉ một lần.
Với LRU thường, chúng sẽ đẩy sạch dữ liệu nóng ra khỏi RAM. Với midpoint insertion, page của lần
scan chỉ đi qua phần old rồi bị loại, phần young (working set thật) được giữ nguyên.

*Dirty page* là page đã sửa trong RAM nhưng chưa ghi xuống tablespace. InnoDB không ghi ngay vì ghi
page ngẫu nhiên đắt; nó dựa vào redo log để đảm bảo an toàn (nhóm tiếp theo), rồi flush page dần ở
chế độ nền.

Theo dõi trong `SHOW ENGINE INNODB STATUS`, mục `BUFFER POOL AND MEMORY` (output minh hoạ, không phải chạy thật):

```
Buffer pool size   131072        -- tính bằng page: 131072 × 16 KB = 2 GB
Free buffers       124908
Database pages     5720
Modified db pages  910           -- số dirty page
Buffer pool hit rate 1000 / 1000 -- 1000/1000 là mọi lần đọc đều trúng RAM
```

Mục tiêu hit rate thường trên 99%. Khi working set (dữ liệu hay dùng) vượt buffer pool, hit rate rơi,
query phải đọc đĩa liên tục, và độ trễ tăng nhiều lần. ⚠️ Sau khi restart, buffer pool rỗng
("lạnh"). InnoDB mặc định dump danh sách page khi tắt (`innodb_buffer_pool_dump_at_shutdown`, dump
25% page nóng nhất) và nạp lại khi bật để rút ngắn thời gian "làm nóng".

#### Ba loại log

| Log | Thuộc tầng | Ghi gì | Dùng để làm gì | Khi nào bỏ được |
|---|---|---|---|---|
| Redo log | InnoDB | Thay đổi vật lý: page nào, offset nào, byte nào | Crash recovery | Khi page tương ứng đã flush (sau checkpoint) |
| Undo log | InnoDB | Bản cũ của dòng trước khi sửa (logic) | Rollback và MVCC | Khi không transaction nào còn cần bản cũ |
| Binlog | MySQL server | Thay đổi logic: dòng (ROW) hoặc câu SQL | Replication, PITR | Theo thời hạn giữ (`binlog_expire_logs_seconds`) |

**Redo log** là write-ahead log của InnoDB (ý tưởng WAL đã gặp ở module 1.3).

- Từ MySQL 8.0.30, redo log nằm trong thư mục `#innodb_redo` gồm 32 file, mỗi file bằng 1/32 của
  `innodb_redo_log_capacity` (mặc định 100 MB, có thể đổi khi đang chạy). Hai biến cũ
  `innodb_log_file_size` và `innodb_log_files_in_group` đã deprecated.
- Mỗi bản ghi redo có một *LSN* (*log sequence number*), là số tăng dần theo lượng byte đã ghi vào
  redo. Mỗi page cũng ghi LSN của lần sửa cuối, nhờ vậy khi recovery InnoDB biết page nào đã có thay
  đổi nào.
- Redo dùng vòng tròn. *Checkpoint* là điểm LSN mà mọi thay đổi trước đó đã nằm trong tablespace;
  phần redo trước checkpoint được tái sử dụng. Khi crash, recovery bắt đầu từ checkpoint cuối cùng
  và áp lại redo tới cuối.
- ⚠️ Redo quá nhỏ so với lượng ghi: InnoDB phải flush dirty page gấp để đẩy checkpoint lên, gây các
  đợt chậm đột ngột khi ghi nhiều. Quá lớn: recovery sau crash lâu hơn.

```sql
SELECT FILE_NAME, START_LSN, END_LSN FROM performance_schema.innodb_redo_log_files;
SHOW GLOBAL STATUS LIKE 'Innodb_redo_log_%lsn';     -- current, flushed_to_disk, checkpoint
```

**Undo log** lưu cách "đảo ngược" một thay đổi trên clustered index. Từ 8.0, undo nằm trong các
*undo tablespace* riêng (mặc định hai file `undo_001`, `undo_002`), không còn nằm trong `ibdata1` như
thời 5.x. Có hai loại:

- *Insert undo*: chỉ cần cho rollback (dòng mới chưa có "bản cũ" nào cho người khác đọc), nên bỏ
  được ngay khi commit.
- *Update undo* (cả update và delete): cần cho rollback và cho MVCC, chỉ bỏ được khi không còn
  snapshot nào cần nó.

`innodb_undo_log_truncate` bật mặc định: undo tablespace vượt `innodb_max_undo_log_size` (mặc định
1 GB) thì được đánh dấu và thu nhỏ khi không còn ai dùng.

**Binlog** thuộc tầng MySQL server, không phụ thuộc engine. MySQL 8.4 bật binlog mặc định. Nó ghi
thay đổi ở mức logic nên replica (có thể khác phiên bản, khác cấu hình) áp lại được, và công cụ PITR
có thể replay tới một thời điểm (module 3.4, 3.5).

Đối chiếu: redo nói "byte thứ 200 của page 57 thành X" (chỉ InnoDB hiểu, chỉ để sửa chính máy đó);
binlog nói "dòng id=5 của bảng orders đổi status từ A sang B" (máy khác hiểu được).

#### Two-phase commit nội bộ

Vấn đề: một transaction phải nằm trong cả redo (để primary tự khôi phục) và binlog (để replica áp
lại). Đây là hai file khác nhau, không ghi nguyên tử cùng lúc được. Nếu crash giữa hai lần ghi:

- Có trong redo, không có trong binlog: primary sau recovery có dòng đó, replica không bao giờ có.
- Có trong binlog, không có trong redo: replica có, primary mất.

MySQL giải bằng *two-phase commit* (2PC) nội bộ, trong đó binlog đóng vai trò "người quyết định".
Mỗi transaction có một *XID* (mã định danh) được ghi vào cả hai log. Các bước khi `COMMIT` (với
`innodb_flush_log_at_trx_commit = 1`, `sync_binlog = 1`):

1. **Prepare (InnoDB)**: InnoDB đánh dấu transaction là *prepared* trong undo/redo, ghi redo xuống
   đĩa và `fsync`. Từ đây InnoDB cam kết "có thể commit nếu được bảo".
2. **Ghi binlog**: toàn bộ event của transaction (đã gom trong binlog cache của session) được ghi
   vào file binlog kèm XID, rồi `fsync`. Đây là *điểm commit thật*: đã vào binlog thì transaction
   chắc chắn sẽ được commit.
3. **Commit (InnoDB)**: InnoDB ghi dấu commit, giải phóng lock, và client nhận OK. Bước này không
   cần fsync riêng, vì nếu mất thì recovery vẫn suy ra được từ binlog.

Recovery sau crash (theo tài liệu Binary Log):

1. InnoDB rollback mọi transaction chưa tới trạng thái prepared.
2. Server đọc file binlog cuối, gom các XID có trong đó, xác định vị trí hợp lệ cuối cùng.
3. Transaction ở trạng thái prepared mà XID **có trong binlog**: được commit. **Không có**: rollback.
4. Binlog bị cắt về vị trí hợp lệ cuối (bỏ phần ghi dở).

Kết quả: InnoDB và binlog luôn khớp nhau, replica không bao giờ nhận thứ primary đã rollback.

Hai fsync mỗi commit rất đắt, nên MySQL dùng *group commit*: nhiều transaction commit cùng lúc được
xếp hàng và chia chung một lần fsync. Binlog group commit có ba giai đoạn (flush, sync, commit),
mỗi giai đoạn có một "leader" làm hộ cả nhóm. Vì vậy throughput khi nhiều client commit song song
cao hơn nhiều so với con số "mỗi giây chỉ fsync được N lần".

#### Đánh đổi giữa độ bền và throughput

| Biến | Giá trị | Ý nghĩa | Mất gì khi sập |
|---|---|---|---|
| `innodb_flush_log_at_trx_commit` | 1 (mặc định) | Ghi redo và fsync mỗi lần commit | Không mất |
| | 2 | Ghi vào file (cache của OS) mỗi commit, fsync khoảng mỗi giây | MySQL crash: không mất; OS/mất điện: tới khoảng 1 giây |
| | 0 | Ghi và fsync khoảng mỗi giây | Kể cả chỉ mysqld crash cũng mất tới khoảng 1 giây |
| `sync_binlog` | 1 (mặc định) | fsync binlog mỗi lần commit (theo nhóm) | Không mất |
| | N | fsync sau mỗi N nhóm commit | Tới N nhóm cuối trong binlog |
| | 0 | Để OS tự quyết khi nào ghi | Không xác định |

⚠️ Hạ một trong hai biến không chỉ mất dữ liệu mà còn làm vỡ đảm bảo của 2PC: sau khi mất điện,
redo và binlog có thể lệch nhau, replica lệch primary. Chỉ hạ khi chấp nhận được, ví dụ replica chỉ
dùng để báo cáo, hoặc lúc import dữ liệu một lần.

#### Doublewrite buffer

Vấn đề *torn page* (page bị ghi dở): page InnoDB 16 KB, còn hệ điều hành và đĩa thường chỉ đảm bảo
ghi nguyên tử đơn vị 4 KB. Mất điện giữa lúc ghi page thì trên đĩa là page nửa mới nửa cũ, checksum
sai. Redo không cứu được, vì redo mô tả thay đổi *trên một page gốc hợp lệ*; page gốc đã hỏng thì
không có gì để áp lên.

Cơ chế:

1. Khi flush một lô dirty page, InnoDB ghi chúng trước vào *doublewrite file* thành một khối tuần
   tự lớn, kèm một lần fsync.
2. Sau đó mới ghi từng page vào vị trí thật trong tablespace.
3. Khi recovery, gặp page hỏng trong tablespace thì InnoDB lấy bản nguyên vẹn trong doublewrite
   file, rồi áp redo lên.

Chi phí nhỏ hơn "ghi hai lần" nghe có vẻ: lần ghi thứ nhất là tuần tự và gom lô. Từ 8.0.20,
doublewrite nằm ở file riêng (`#ib_16384_0.dblwr`, `#ib_16384_1.dblwr` với page 16 KB), mặc định hai
file cho mỗi buffer pool instance, có thể đặt trên đĩa nhanh nhất qua `innodb_doublewrite_dir`. `innodb_doublewrite` mặc định
`ON`; `DETECT_ONLY` chỉ phát hiện page hỏng chứ không sửa; `OFF` chỉ dùng khi benchmark hoặc khi hệ
thống file/thiết bị đảm bảo ghi nguyên tử 16 KB.

Tổng hợp lại, trả lời câu "từ `COMMIT` tới lúc an toàn":

1. Trong transaction: sửa page trong buffer pool, sinh redo vào log buffer, sinh undo, gom event vào
   binlog cache.
2. `COMMIT`: redo prepare + fsync; binlog + fsync; InnoDB commit; trả OK.
3. Sau đó (giây, phút): dirty page được flush qua doublewrite rồi vào tablespace; checkpoint tiến
   lên; undo được purge khi hết người cần.

#### MVCC

*MVCC* (*multi-version concurrency control*) nghĩa là một dòng có thể tồn tại nhiều phiên bản cùng
lúc, mỗi transaction thấy phiên bản đúng với *snapshot* của nó. Nhờ vậy `SELECT` thường (consistent
read) không cần lock: đọc không chặn ghi, ghi không chặn đọc.

Cơ chế ở InnoDB:

- Mỗi dòng trong clustered index có hai cột ẩn: `DB_TRX_ID` (6 byte, id của transaction sửa dòng
  lần cuối; delete được coi là update có bật cờ xoá) và `DB_ROLL_PTR` (7 byte, trỏ tới bản ghi undo
  chứa phiên bản trước). Bảng không có PK thì thêm `DB_ROW_ID` (6 byte) làm clustered index ẩn.
- Mỗi bản ghi undo lại trỏ tới bản cũ hơn, tạo thành *version chain* (chuỗi phiên bản). Bản mới nhất
  luôn nằm trong bảng; bản cũ nằm trong undo.

```
 Clustered index (bản mới nhất)          Undo log
 +--------------------------------+
 | id=5 | stock=7 | trx=300 | ptr-+----> [stock=8, trx=250, ptr] ----> [stock=10, trx=100, ptr=null]
 +--------------------------------+
 Transaction có read view tạo trước khi trx 250 commit sẽ đi ngược chuỗi tới bản stock=10.
```

- *Read view* là snapshot của một transaction: danh sách các transaction đang hoạt động lúc tạo
  view, cùng hai mốc id thấp nhất và cao nhất. Quy tắc nhìn thấy một phiên bản có `trx_id`:
  1. `trx_id` là của chính mình: thấy.
  2. `trx_id` nhỏ hơn id nhỏ nhất đang hoạt động lúc tạo view: đã commit trước đó, thấy.
  3. `trx_id` lớn hơn hoặc bằng id tiếp theo sẽ cấp lúc tạo view: bắt đầu sau view, không thấy.
  4. Ở giữa: thấy nếu không nằm trong danh sách đang hoạt động.
  Không thấy thì theo `DB_ROLL_PTR` sang bản cũ hơn và kiểm tra lại.
- Khác biệt giữa isolation level nằm ở lúc tạo read view: RR tạo một lần ở lần đọc consistent đầu
  tiên và dùng cho cả transaction; RC tạo mới cho mỗi câu lệnh (module 2.5).
- Secondary index không có cột ẩn và không sửa tại chỗ: bản cũ bị đánh dấu xoá, bản mới được chèn.
  ⚠️ Khi gặp entry bị đánh dấu xoá hoặc page vừa bị transaction mới hơn sửa, InnoDB phải quay về
  clustered index để kiểm tra phiên bản, nên covering index (module 2.2) tạm mất tác dụng.

*Purge*: `DELETE` chỉ đánh dấu dòng là đã xoá. Các *purge thread* chạy nền mới thật sự gỡ dòng đó
và giải phóng undo, nhưng chỉ khi không còn read view nào có thể cần phiên bản cũ.

*History list length* (HLL) là số bản ghi undo của các transaction đã commit mà purge chưa dọn được.
Nó là chỉ số sức khoẻ quan trọng nhất của MVCC:

```sql
SHOW ENGINE INNODB STATUS\G          -- mục TRANSACTIONS: "History list length 1234"
SELECT count FROM information_schema.INNODB_METRICS WHERE name = 'trx_rseg_history_len';
-- tìm thủ phạm: transaction mở lâu nhất
SELECT trx_id, trx_started, trx_mysql_thread_id, trx_query
FROM information_schema.innodb_trx ORDER BY trx_started LIMIT 5;
```

HLL ở mức vài trăm tới vài nghìn là bình thường với hệ thống ghi nhiều. Tăng đều tới hàng trăm nghìn,
hàng triệu mà không giảm là dấu hiệu có transaction giữ snapshot cũ.

⚠️ Chuỗi sự cố "transaction quên đóng", thử được bằng hai session:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION; SELECT * FROM products WHERE id = 1;` | | A tạo read view, rồi bỏ đó (dev mở console quên commit) |
| 2 | | Chạy 100.000 lần `UPDATE products SET stock = stock - 1 WHERE id = 1;` (autocommit) | Mỗi update sinh một bản undo |
| 3 | | `SHOW ENGINE INNODB STATUS\G` | History list length tăng liên tục, purge không dọn được vì A có thể cần mọi bản cũ |
| 4 | `SELECT * FROM products WHERE id = 1;` | | A đi ngược chuỗi 100.000 phiên bản để tìm bản của mình: chậm rõ rệt |
| 5 | | Query khác đọc bảng này | Cũng phải lướt qua các phiên bản và dòng đã đánh dấu xoá chưa purge |
| 6 | `COMMIT;` | | Purge chạy, HLL giảm dần |

Hệ quả: undo tablespace phình, mọi đọc chậm dần, và nó đến từ một transaction chỉ `SELECT`. Tài
liệu MySQL khuyến nghị commit đều đặn, kể cả transaction chỉ đọc. Phòng ở tầng app: không để
transaction mở qua thời gian chờ người dùng hay gọi API; ở tầng vận hành: cảnh báo khi có
transaction trong `innodb_trx` sống quá vài phút.

#### Binlog format

| Format | Ghi gì | Ưu | Nhược |
|---|---|---|---|
| `ROW` (mặc định) | Giá trị dòng trước/sau cho mỗi dòng đổi | Tất định, replica ra đúng như primary | `UPDATE` một triệu dòng sinh một triệu event, binlog to |
| `STATEMENT` | Câu SQL | Binlog nhỏ | Câu không tất định cho kết quả khác trên replica |
| `MIXED` | Mặc định statement, tự chuyển sang row khi câu "unsafe" | Cân bằng | Khó dự đoán |

⚠️ Câu không an toàn với `STATEMENT`: `NOW()` thì an toàn (binlog ghi kèm timestamp), nhưng
`UUID()`, `RAND()` không seed, `SYSDATE()`, `UPDATE ... LIMIT` không có `ORDER BY` (replica có thể
chọn dòng khác), hay `INSERT ... SELECT` với auto-increment ở lock mode 2 (module 3.2) thì không.
Trong MySQL 8.x hãy giữ `ROW`; `binlog_row_image = MINIMAL` giảm kích thước nếu cần.

#### Đối chiếu Postgres

| Khía cạnh | InnoDB | PostgreSQL |
|---|---|---|
| Bản cũ của dòng nằm ở đâu | Undo log, tách khỏi bảng | Ngay trong heap (file bảng), dưới dạng tuple cũ |
| Update | Sửa tại chỗ, bản cũ sang undo | Ghi tuple mới, tuple cũ đánh dấu hết hạn (`xmax`) |
| Dọn rác | Purge thread | `VACUUM` (autovacuum chạy nền) |
| Hệ quả khi không dọn kịp | Undo phình, HLL cao, đọc chậm | Bảng và index *bloat* (phình), scan chậm |
| Rollback | Phải áp ngược undo (rollback transaction lớn tốn thời gian) | Gần như tức thì: chỉ đánh dấu transaction là aborted |
| WAL | Redo log (vật lý) + binlog (logic, cho replication) | Một WAL duy nhất cho cả recovery và replication |

- Mỗi tuple Postgres có `xmin` (transaction tạo) và `xmax` (transaction xoá/thay thế). Update ghi
  tuple mới, nên mọi index cũng phải thêm entry mới, trừ khi là *HOT update* (heap-only tuple):
  không cột nào có index bị đổi và page còn chỗ, thì tuple mới nằm cùng page, index không phải sửa.
- ⚠️ *Transaction ID wraparound*: xid của Postgres là 32 bit, so sánh theo vòng tròn nên chỉ khoảng
  2 tỉ transaction là "quá khứ" nhìn thấy được. VACUUM phải *freeze* các tuple cũ (đánh dấu là
  "nhìn thấy với mọi người") trước khi vòng quay tới. Autovacuum chủ động freeze khi tuổi bảng vượt
  `autovacuum_freeze_max_age` (mặc định 200 triệu). Nếu để trôi quá gần giới hạn, Postgres từ chối
  cấp xid mới, tức ngừng nhận ghi, cho tới khi vacuum xong.
- Transaction mở lâu gây hại ở cả hai phía: InnoDB không purge được, Postgres không vacuum được
  tuple chết mà transaction đó còn có thể thấy. Ở Postgres còn có thêm nguồn giữ snapshot là
  replication slot bị bỏ quên và `hot_standby_feedback` từ replica.

#### LSM tree

B+tree (InnoDB, Postgres) sửa page tại chỗ. *LSM tree* (*log-structured merge tree*, dùng trong
RocksDB, MyRocks, Cassandra, ScyllaDB) chỉ ghi nối:

1. Ghi vào WAL (để bền) và vào *memtable* (cây sắp xếp trong RAM).
2. Memtable đầy thì được ghi ra đĩa thành *SSTable*: file bất biến, đã sắp xếp.
3. *Compaction* chạy nền, gộp các SSTable, bỏ bản cũ và dấu xoá (*tombstone*).
4. Đọc phải xem memtable rồi nhiều SSTable từ mới tới cũ; *bloom filter* giúp bỏ qua nhanh file
   chắc chắn không chứa key.

| Tiêu chí | B+tree | LSM tree |
|---|---|---|
| Ghi | Ghi ngẫu nhiên vào page, kèm WAL | Ghi tuần tự, rất nhanh |
| Đọc điểm | Một đường từ gốc xuống lá | Có thể phải xem nhiều file |
| Khuếch đại | Ghi cả page 16 KB cho vài byte đổi | Compaction ghi lại dữ liệu nhiều lần |
| Nén | Kém hơn (page có chỗ trống) | Tốt (file bất biến, sắp xếp) |
| Hợp với | OLTP đọc nhiều, cần độ trễ đọc ổn định | Ghi dày: log, metric, time series, event |

**Tóm tắt nhanh**
- Buffer pool giữ page trong RAM, LRU có midpoint để scan lớn không đẩy dữ liệu nóng ra; theo dõi
  hit rate, cấp tới khoảng 80% RAM trên máy riêng.
- Redo cho crash recovery (vật lý), undo cho rollback và MVCC, binlog cho replication và PITR (logic).
- Commit = redo prepare + fsync, binlog + fsync (điểm commit thật), InnoDB commit. Recovery: prepared
  mà có trong binlog thì commit, không có thì rollback.
- `innodb_flush_log_at_trx_commit = 1` và `sync_binlog = 1` là mặc định an toàn; hạ xuống là chấp
  nhận mất khoảng 1 giây và có thể lệch replica.
- Doublewrite chống torn page, thứ redo không sửa được.
- Transaction mở lâu, kể cả chỉ đọc, chặn purge: history list length tăng, mọi đọc chậm dần. Postgres
  tương tự với VACUUM, cộng thêm rủi ro wraparound.

**Nguồn**: [MySQL: InnoDB Architecture](https://dev.mysql.com/doc/refman/8.4/en/innodb-architecture.html) ·
[Buffer Pool](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html) ·
[Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html) ·
[Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html) ·
[Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html) ·
[Doublewrite Buffer](https://dev.mysql.com/doc/refman/8.4/en/innodb-doublewrite-buffer.html) ·
[Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html) ·
[InnoDB Startup Options](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html) ·
[Jeremy Cole: The basics of InnoDB undo logging and history system](https://blog.jcole.us/2014/04/16/the-basics-of-the-innodb-undo-logging-and-history-system/) ·
[PostgreSQL: MVCC](https://www.postgresql.org/docs/current/mvcc-intro.html) ·
[PostgreSQL: Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html) ·
*Designing Data-Intensive Applications* ch.3


---

### 3.2 Lock chuyên sâu

Module này trả lời: một câu lệnh ở Repeatable Read thực sự khoá những gì, vì sao hai request "kiểm
tra chưa có thì tạo" lại deadlock nhau, đọc deadlock log ra sao, và vì sao một `ALTER TABLE` chưa
chạy được dòng nào đã làm sập cả app.

Dữ liệu mẫu dùng cho cả module:

```sql
USE learn;
CREATE TABLE members (
  id  BIGINT PRIMARY KEY,
  age INT NOT NULL,
  name VARCHAR(50),
  INDEX idx_age (age)
);
INSERT INTO members VALUES (1, 20, 'An'), (2, 30, 'Bình'), (3, 40, 'Chi');
```

#### InnoDB khoá cái gì

Nguyên tắc gốc: InnoDB không khoá "dòng" theo nghĩa trừu tượng mà khoá **entry trong index** mà câu
lệnh đi qua. Bảng không có index nào thì InnoDB vẫn có clustered index ẩn, và khoá trên đó. Hệ quả
rút ra từ tài liệu "Locks Set by Different SQL Statements":

1. `SELECT ... FOR UPDATE`, `FOR SHARE`, `UPDATE`, `DELETE` khoá **mọi entry đã quét**, không chỉ
   entry thoả `WHERE`. InnoDB chỉ biết khoảng index nó đã đi qua, không nhớ điều kiện `WHERE`.
2. Không có index phù hợp thì phải quét cả bảng, tức khoá mọi dòng và mọi khoảng: không ai insert
   được gì vào bảng.
3. Khoá entry của secondary index thì InnoDB khoá luôn entry tương ứng trong clustered index.
4. Ngoại lệ quan trọng: điều kiện `=` trên unique index (hoặc PK) và dòng **có tồn tại** thì chỉ cần
   record lock, không cần gap lock. Dòng **không tồn tại** thì vẫn phải khoá khoảng.

Các loại lock mức dòng (ký hiệu trong ngoặc là cách `performance_schema.data_locks` hiện
`LOCK_MODE`):

| Lock | Khoá gì | Mục đích | `LOCK_MODE` |
|---|---|---|---|
| Record lock | Đúng một entry | Không ai sửa/xoá entry đó | `X,REC_NOT_GAP` / `S,REC_NOT_GAP` |
| Gap lock | Khoảng trống trước một entry (không gồm entry) | Chỉ để chặn insert vào khoảng | `X,GAP` / `S,GAP` |
| Next-key lock | Entry cộng với khoảng ngay trước nó: `(prev, entry]` | Chặn phantom ở RR | `X` / `S` |
| Insert intention | Một điểm trong khoảng, lấy trước khi insert | Báo "tôi sắp chèn vào đây" | `X,INSERT_INTENTION` |

Ba tính chất của gap lock cần nhớ, vì chúng giải thích mọi deadlock ở nhóm sau:

- Gap lock *chỉ có tác dụng ngăn chặn*: nó chặn insert, không chặn đọc hay khoá khác.
- Gap lock của các transaction khác nhau **không xung đột nhau**, kể cả `S,GAP` với `X,GAP`. Hai
  transaction có thể cùng giữ gap lock trên một khoảng.
- Insert intention **xung đột với gap lock** của transaction khác trên cùng khoảng, nhưng hai insert
  intention không xung đột nhau nếu chèn khác vị trí (chèn 5 và 6 vào khoảng giữa 4 và 7 không chờ
  nhau).

Next-key lock chia index thành các khoảng nửa mở. Với index có các giá trị 10, 11, 13, 20, các
next-key lock có thể là `(-∞, 10]`, `(10, 11]`, `(11, 13]`, `(13, 20]`, `(20, +∞)`. Khoảng cuối khoá
bản ghi giả *supremum* (luôn đứng sau entry lớn nhất của page), nên chặn mọi insert giá trị lớn hơn 20.

Ví dụ trên dữ liệu mẫu, ở RR:

```sql
START TRANSACTION;
SELECT * FROM members WHERE age BETWEEN 20 AND 30 FOR UPDATE;

SELECT INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_DATA
FROM performance_schema.data_locks WHERE OBJECT_NAME = 'members';
```

Kết quả kiểu (output minh hoạ, không phải chạy thật):

```
INDEX_NAME | LOCK_TYPE | LOCK_MODE     | LOCK_DATA
NULL       | TABLE     | IX            | NULL
idx_age    | RECORD    | X             | 20, 1     <- next-key (-∞, 20]
idx_age    | RECORD    | X             | 30, 2     <- next-key (20, 30]
idx_age    | RECORD    | X             | 40, 3     <- next-key (30, 40]: entry đầu tiên vượt khoảng
PRIMARY    | RECORD    | X,REC_NOT_GAP | 1
PRIMARY    | RECORD    | X,REC_NOT_GAP | 2
```

`LOCK_DATA` của secondary index là `giá trị index, PK`. Đọc ra được: vì `idx_age` không unique,
InnoDB phải quét tới entry đầu tiên lớn hơn 30 (là 40) mới biết dừng, và entry đã quét thì bị khoá.
Nên session khác bị chặn khi insert `age = 15`, `25`, `35`, và khi sửa dòng có `age = 40`, dù những
giá trị đó nằm ngoài `BETWEEN 20 AND 30`. Chi tiết chính xác (có khoá entry 40 hay không, là
next-key hay gap) thay đổi theo phiên bản và kế hoạch thực thi; luôn kiểm tra bằng `data_locks`
thay vì đoán.

Từ đó, cách trả lời câu "`UPDATE` này khoá gì" ở RR:

1. Xác định index mà câu lệnh dùng (`EXPLAIN`).
2. Liệt kê các entry mà nó quét trên index đó, kể cả entry đầu tiên vượt khỏi điều kiện.
3. Unique index với `=` và dòng tồn tại: record lock. Còn lại: next-key lock trên mỗi entry quét,
   cộng gap nếu dòng không tồn tại.
4. Cộng thêm record lock trên PK của các dòng khớp.
5. Không có index dùng được: cả bảng.

```sql
UPDATE members SET name = 'x' WHERE id = 2;     -- record lock PRIMARY 2
UPDATE members SET name = 'x' WHERE id = 5;     -- không có id 5: gap lock trước supremum, chặn insert id > 3
UPDATE members SET name = 'x' WHERE age = 30;   -- next-key (20,30] + gap (30,40) trên idx_age, record PK 2
UPDATE members SET name = 'x' WHERE name = 'Bình'; -- không có index trên name: khoá mọi dòng và mọi khoảng
```

**Intention lock** là lock mức bảng. Trước khi lấy lock S trên một dòng, transaction phải có IS (hoặc
mạnh hơn) trên bảng; trước khi lấy X trên dòng phải có IX. Mục đích: câu `LOCK TABLES ... WRITE`
hoặc DDL muốn khoá cả bảng chỉ cần nhìn lock mức bảng, không phải duyệt từng dòng. Intention lock
không chặn nhau, chỉ chặn lock cả bảng:

|    | X | IX | S | IS |
|---|---|---|---|---|
| X  | Xung đột | Xung đột | Xung đột | Xung đột |
| IX | Xung đột | Tương thích | Xung đột | Tương thích |
| S  | Xung đột | Xung đột | Tương thích | Tương thích |
| IS | Xung đột | Tương thích | Tương thích | Tương thích |

**Ở Read Committed**, InnoDB tắt gap lock cho tìm kiếm và scan (chỉ còn dùng khi kiểm tra khoá ngoại
và kiểm tra trùng khoá). Thêm hai khác biệt: lock trên dòng không khớp `WHERE` được nhả ngay sau khi
đánh giá điều kiện, và `UPDATE` dùng *semi-consistent read* (gặp dòng đang bị khoá thì đọc bản đã
commit mới nhất để xem có khớp `WHERE` không; không khớp thì bỏ qua, không chờ). Kết quả: ít chờ và ít
deadlock hơn hẳn, đổi lại chấp nhận phantom. Nhiều hệ thống lớn chạy RC vì lý do này (module 2.5).

#### Deadlock kinh điển do gap lock

*Deadlock* là vòng chờ: A giữ thứ B cần, B giữ thứ A cần, không ai đi tiếp được. InnoDB phát hiện
bằng *wait-for graph* (đồ thị "ai đang chờ ai"): mỗi lần một transaction phải chờ lock, InnoDB kiểm
tra xem có tạo thành vòng không. Có vòng thì chọn một *victim* để rollback toàn bộ, thường là
transaction đã insert/update/delete ít dòng nhất, và trả lỗi `1213 (40001) Deadlock found when trying
to get lock; try restarting transaction`.

Mẫu code gây deadlock hay gặp nhất: "kiểm tra chưa có thì tạo mới" (*check-then-insert*), dùng
`FOR UPDATE` với ý định "khoá lại cho chắc":

```sql
CREATE TABLE wallets (user_id BIGINT PRIMARY KEY, balance BIGINT NOT NULL);
INSERT INTO wallets VALUES (90, 0), (200, 0);   -- user 100 chưa có ví; khoảng (90, 200) trống
```

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | `START TRANSACTION;` | |
| 2 | `SELECT * FROM wallets WHERE user_id = 100 FOR UPDATE;` | | Rỗng. Không có dòng để khoá nên A lấy `X,GAP` trên khoảng (90, 200), ghi ở entry 200 |
| 3 | | `SELECT * FROM wallets WHERE user_id = 100 FOR UPDATE;` | Rỗng. B cũng lấy `X,GAP` trên cùng khoảng, **không chờ** vì gap lock không xung đột nhau |
| 4 | App thấy chưa có: `INSERT INTO wallets VALUES (100, 0);` | | A xin insert intention trong (90, 200), xung đột với gap lock của B: **A chờ B** |
| 5 | | App thấy chưa có: `INSERT INTO wallets VALUES (100, 0);` | B xin insert intention, xung đột với gap lock của A: **B chờ A**. Vòng chờ |
| 6 | | `ERROR 1213: Deadlock found` | InnoDB rollback B (victim), nhả gap lock của B |
| 7 | Insert thành công; `COMMIT;` | | A tạo được ví. B phải retry, lần này thấy dòng đã có |

Vì sao `FOR UPDATE` "khoá cho chắc" lại gây hại: nó không khoá được thứ chưa tồn tại, chỉ khoá được
khoảng, và khoá khoảng thì ai cũng lấy được cùng lúc. Nó không tạo ra loại trừ lẫn nhau mà dev mong.

Cách sửa, theo thứ tự nên thử:

1. **Để unique constraint làm việc**: bỏ `SELECT ... FOR UPDATE`, insert thẳng và xử lý lỗi trùng.
   Bên thua nhận lỗi `1062 Duplicate entry`, không phải deadlock.

   ```sql
   INSERT INTO wallets (user_id, balance) VALUES (100, 0)
   ON DUPLICATE KEY UPDATE user_id = user_id;     -- "tạo nếu chưa có", một câu, nguyên tử
   -- hoặc INSERT IGNORE ... rồi SELECT lại
   ```

   ⚠️ `INSERT ... ON DUPLICATE KEY UPDATE` lấy X lock trên dòng trùng (next-key lock nếu trùng ở
   unique index phụ), nên vẫn có thể deadlock khi chạy song song dày đặc, chỉ hiếm hơn nhiều.
2. **Chạy ở RC** cho các transaction dạng này: không có gap lock ở bước 2, 3.
3. **Tạo trước dòng cha rồi khoá dòng có thật**: ví dụ khoá dòng `users.id = 100` (luôn tồn tại)
   bằng `FOR UPDATE`, để mọi request cho cùng user xếp hàng trên một record lock.
4. **Luôn có retry** ở tầng app, vì deadlock không thể loại bỏ hoàn toàn. Tài liệu MySQL coi
   deadlock là chuyện bình thường của hệ thống có transaction, miễn là không quá thường xuyên.

Một biến thể trong tài liệu MySQL không cần `SELECT` nào: ba session cùng `INSERT` một khoá, session
1 giữ X lock; session 2 và 3 nhận lỗi trùng khoá và xin S lock trên dòng đó; session 1 rollback, 2 và
3 cùng được S lock, rồi cùng muốn X để insert, và deadlock nhau.

Retry đúng cách trong PHP (thuần PDO; Laravel có sẵn `DB::transaction($callback, attempts: 3)`, tự
chạy lại khi gặp deadlock):

```php
<?php
declare(strict_types=1);

/**
 * Chạy $work trong transaction, thử lại khi deadlock (1213) hoặc lock wait timeout (1205).
 * $work phải chạy lại được từ đầu (idempotent trong phạm vi transaction).
 */
function withRetry(PDO $pdo, callable $work, int $maxAttempts = 3): mixed
{
    for ($attempt = 1; ; $attempt++) {
        $pdo->beginTransaction();
        try {
            $result = $work($pdo);
            $pdo->commit();
            return $result;
        } catch (Throwable $e) {
            // Bắt mọi lỗi để luôn rollback, kể cả lỗi không phải PDOException
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            $code = $e instanceof PDOException ? ($e->errorInfo[1] ?? 0) : 0;
            $retryable = $code === 1213 || $code === 1205;
            if (!$retryable || $attempt >= $maxAttempts) {
                throw $e;
            }
            usleep(random_int(10_000, 50_000) * $attempt);   // backoff có jitter
        }
    }
}
```

⚠️ Hai lỗi khác nhau về phạm vi rollback. Deadlock (1213) rollback **cả transaction**. Lock wait
timeout (1205, sau `innodb_lock_wait_timeout`, mặc định 50 giây) mặc định chỉ rollback **câu lệnh
đang chạy** (`innodb_rollback_on_timeout = OFF`), transaction vẫn mở với các thay đổi trước đó. Code
bắt 1205 rồi `COMMIT` tiếp là commit nửa transaction. Luôn rollback cả transaction khi gặp một trong
hai lỗi, như hàm trên.

Các nguyên tắc phòng deadlock chung (tài liệu MySQL):

- Transaction ngắn, ít dòng; không chờ I/O ngoài khi đang giữ lock.
- Mọi code path khoá các bảng và các dòng theo **cùng một thứ tự** (ví dụ chuyển tiền: khoá tài khoản
  có id nhỏ hơn trước).
- Có index cho cột trong `WHERE` của `UPDATE`/`DELETE`/`FOR UPDATE`, để quét và khoá ít entry.
- Dùng RC khi chấp nhận được.
- Ở hệ thống cực nhiều luồng cùng chờ một dòng nóng, bản thân việc dò deadlock tốn CPU; có thể tắt
  `innodb_deadlock_detect` và dựa vào `innodb_lock_wait_timeout` ngắn. Khi đang bật, nếu danh sách chờ
  vượt 200 transaction, hoặc thread đang kiểm tra phải xem quá 1.000.000 lock của các transaction trong
  danh sách chờ, InnoDB coi luôn là deadlock.

#### AUTO-INC lock

Bảng có cột `AUTO_INCREMENT` cần cấp id duy nhất cho các insert đồng thời. `innodb_autoinc_lock_mode`
quyết định cách cấp:

| Mode | Tên | Cách cấp | Id liên tục? | An toàn với binlog `STATEMENT`? |
|---|---|---|---|---|
| 0 | traditional | Lock mức bảng tới hết câu lệnh cho mọi insert | Có | Có |
| 1 | consecutive | *Bulk insert* (số dòng không biết trước, như `INSERT ... SELECT`, `LOAD DATA`) giữ lock mức bảng; *simple insert* (biết trước số dòng) chỉ dùng mutex nhẹ lúc cấp | Có trong một câu lệnh | Có |
| 2 (mặc định từ 8.0) | interleaved | Không có lock mức bảng; các câu lệnh cấp id xen kẽ nhau | Không | Không |

- Mode 2 thành mặc định vì replication mặc định đã chuyển từ statement-based sang row-based. Với `ROW` hoặc `MIXED`, mọi mode
  đều an toàn vì binlog ghi giá trị id cụ thể.
- Id có "lỗ" ở mọi mode: transaction rollback không trả lại id đã cấp; mode 1 và 2 có thể cấp dư cho
  bulk insert và *mixed-mode insert* (một số dòng tự cho id, một số để NULL); upsert cũng tiêu id. Đừng
  dùng id để đếm số dòng hay giả định không có khoảng trống.
- Từ 8.0, bộ đếm auto-increment được lưu bền qua restart (trước 8.0, restart có thể cấp lại id của
  dòng đã bị xoá ở cuối bảng).

#### Đọc deadlock log

`SHOW ENGINE INNODB STATUS\G` chỉ giữ **deadlock gần nhất** trong mục `LATEST DETECTED DEADLOCK`. Bật
`innodb_print_all_deadlocks = ON` (mặc định OFF) để mọi deadlock được ghi vào error log, đây là thứ
nên bật trên production. Đếm số deadlock:
`SELECT count FROM information_schema.INNODB_METRICS WHERE name = 'lock_deadlocks';`.

Log rút gọn của kịch bản ví tiền ở trên (định dạng MySQL 8.x, đã bỏ bớt dòng; output minh hoạ, không
phải chạy thật):

```
------------------------
LATEST DETECTED DEADLOCK
------------------------
2026-09-27 10:15:02 140211
*** (1) TRANSACTION:
TRANSACTION 5001, ACTIVE 14 sec inserting
mysql tables in use 1, locked 1
LOCK WAIT 3 lock struct(s), heap size 1128, 2 row lock(s)
MySQL thread id 21, OS thread handle 1402, query id 310 localhost root update
INSERT INTO wallets VALUES (100, 0)

*** (1) HOLDS THE LOCK(S):
RECORD LOCKS space id 30 page no 4 n bits 72 index PRIMARY of table `learn`.`wallets`
trx id 5001 lock_mode X locks gap before rec
Record lock, heap no 3 PHYSICAL RECORD: n_fields 4; compact format; info bits 0
 0: len 8; hex 80000000000000c8; asc         ;;

*** (1) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 30 page no 4 n bits 72 index PRIMARY of table `learn`.`wallets`
trx id 5001 lock_mode X locks gap before rec insert intention waiting
Record lock, heap no 3 PHYSICAL RECORD: n_fields 4; compact format; info bits 0
 0: len 8; hex 80000000000000c8; asc         ;;

*** (2) TRANSACTION:
TRANSACTION 5002, ACTIVE 9 sec inserting
LOCK WAIT 3 lock struct(s), heap size 1128, 2 row lock(s)
MySQL thread id 22, OS thread handle 1403, query id 311 localhost root update
INSERT INTO wallets VALUES (100, 0)

*** (2) HOLDS THE LOCK(S):
RECORD LOCKS ... index PRIMARY of table `learn`.`wallets` trx id 5002 lock_mode X locks gap before rec
 0: len 8; hex 80000000000000c8; asc         ;;

*** (2) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS ... index PRIMARY of table `learn`.`wallets` trx id 5002 lock_mode X locks gap before rec insert intention waiting
 0: len 8; hex 80000000000000c8; asc         ;;

*** WE ROLL BACK TRANSACTION (2)
```

Cách đọc, theo từng bước:

1. **Mỗi transaction**: `ACTIVE 14 sec` là đã mở bao lâu (lâu bất thường là dấu hiệu transaction
   ôm việc chậm); `inserting` là đang làm gì; `2 row lock(s)` là số lock dòng đang giữ; `MySQL thread
   id 21` đối chiếu được với `SHOW PROCESSLIST` và log app.
2. **Câu SQL** ngay dưới là câu đang chạy lúc deadlock, ở đây cả hai cùng `INSERT` id 100.
3. **HOLDS THE LOCK(S)**: đang giữ gì. Dòng `index PRIMARY of table learn.wallets` cho biết index và
   bảng. `lock_mode X locks gap before rec` là gap lock trước bản ghi được in bên dưới.
4. **Giải mã bản ghi**: trường `0:` là cột đầu của index, ở đây PK `BIGINT`. InnoDB lưu số nguyên có
   dấu với bit dấu bị đảo, nên `80000000000000c8` là `0xc8` = 200. Vậy lock là "khoảng trước 200",
   tức (90, 200). Nếu thấy `asc supremum;;` thì là khoảng sau entry lớn nhất.
5. **WAITING FOR THIS LOCK**: đang chờ gì. `insert intention waiting` trên cùng khoảng trước 200.
6. **Ghép vòng**: (1) giữ gap (90, 200) và chờ insert intention trong đó, bị chặn bởi gap của (2);
   (2) giữ gap đó và chờ insert intention, bị chặn bởi gap của (1). Hai gap lock không chặn nhau nên
   cả hai cùng lấy được từ trước, rồi cùng bị chặn khi insert: đúng mẫu check-then-insert.
7. **WE ROLL BACK TRANSACTION (2)**: victim là (2). App của (2) nhận lỗi 1213.

Các mẫu `lock_mode` hay gặp trong log:

| Chuỗi trong log | Nghĩa |
|---|---|
| `lock_mode X locks rec but not gap` | Record lock X |
| `lock mode S locks rec but not gap` | Record lock S (từ `FOR SHARE`, kiểm tra FK, hoặc lỗi trùng khoá) |
| `lock_mode X` (không có gì thêm) | Next-key lock X |
| `lock_mode X locks gap before rec` | Gap lock |
| `... insert intention waiting` | Insert đang chờ vì có gap lock của người khác |

⚠️ Log chỉ in câu lệnh **đang chạy** của mỗi transaction, không in các câu trước đó. Lock ở mục
HOLDS có thể do một câu `SELECT ... FOR UPDATE` chạy trước đó trong cùng transaction (như bước 2 ở
kịch bản trên: log không hề nhắc tới `SELECT`). Muốn biết đầy đủ phải đối chiếu với code, hoặc bật
`performance_schema.events_statements_history` để xem các câu gần nhất của thread đó.

Khi chưa deadlock mà đang *chờ lock*, xem trực tiếp ai chặn ai:

```sql
SELECT r.ENGINE_TRANSACTION_ID AS waiting_trx, b.ENGINE_TRANSACTION_ID AS blocking_trx,
       r.INDEX_NAME, r.LOCK_MODE AS waiting_mode, b.LOCK_MODE AS blocking_mode, r.LOCK_DATA
FROM performance_schema.data_lock_waits w
JOIN performance_schema.data_locks r ON r.ENGINE_LOCK_ID = w.REQUESTING_ENGINE_LOCK_ID
JOIN performance_schema.data_locks b ON b.ENGINE_LOCK_ID = w.BLOCKING_ENGINE_LOCK_ID;
-- hoặc gọn hơn: SELECT * FROM sys.innodb_lock_waits\G  (có sẵn câu KILL gợi ý)
```

#### Metadata lock (MDL)

*Metadata lock* là lock của tầng MySQL server (không phải InnoDB) trên *định nghĩa* của đối tượng:
bảng, schema, stored procedure, trigger. Mục đích: không cho cấu trúc bảng bị đổi khi đang có
transaction dùng bảng đó.

- Mọi câu lệnh chạm vào bảng, kể cả `SELECT` thường, lấy MDL dạng shared (`SHARED_READ` cho đọc,
  `SHARED_WRITE` cho DML).
- MDL được giữ **tới hết transaction**, không phải tới hết câu lệnh. Ở autocommit thì mỗi câu là một
  transaction nên nhả ngay.
- DDL (`ALTER`, `DROP`, `RENAME`, `TRUNCATE`) cần MDL `EXCLUSIVE`. Kể cả `ALTER` online (`INPLACE`,
  `INSTANT`) cũng cần exclusive trong một khoảnh khắc, ở đầu và/hoặc cuối thao tác.
- Yêu cầu lock ghi được ưu tiên hơn lock đọc: một yêu cầu exclusive đang chờ sẽ chặn cả các yêu cầu
  shared đến sau nó. Đây là mắt xích gây sập.
- `lock_wait_timeout` (thời gian chờ MDL) mặc định 31.536.000 giây, tức một năm. Không đặt gì thì
  `ALTER` chờ gần như vô hạn.

Timeline sự cố, tái hiện được bằng ba session:

| Bước | Session A | Session B (migration) | Session C (app) | Kết quả |
|---|---|---|---|---|
| 1 | `START TRANSACTION; SELECT * FROM members WHERE id = 1;` | | | A giữ `SHARED_READ` trên `members`, rồi không commit (console bỏ quên, job báo cáo dài, worker treo) |
| 2 | | `ALTER TABLE members ADD COLUMN note VARCHAR(20);` | | B xin `EXCLUSIVE`, phải chờ A: trạng thái `Waiting for table metadata lock` |
| 3 | | | `SELECT * FROM members WHERE id = 2;` | C xin `SHARED_READ`, **xếp hàng sau B** vì B là yêu cầu exclusive đang chờ. C treo |
| 4 | | | Hàng trăm request khác | Tất cả treo sau B; connection pool cạn, PHP-FPM hết worker, health check fail: app "sập" |
| 5 | `COMMIT;` (hoặc bị kill) | | | A nhả lock |
| 6 | | `ALTER` chạy (với `INSTANT` là tức thì) | | |
| 7 | | | Các query được chạy tiếp | App hồi lại |

Điểm then chốt khi giải thích: `ALTER` chưa làm gì cả, bảng không bị khoá bởi thao tác nặng nào.
Nguyên nhân là hàng đợi MDL: một transaction cũ chặn `ALTER`, và `ALTER` chặn mọi người đến sau. Chạy
lúc nửa đêm không chữa được, vì thủ phạm là transaction dài chứ không phải lưu lượng.

Nhận biết và tìm thủ phạm:

```sql
SHOW PROCESSLIST;       -- nhiều dòng State = 'Waiting for table metadata lock'
-- ai đang giữ, ai đang chờ (instrument MDL bật sẵn ở 8.x)
SELECT OBJECT_NAME, LOCK_TYPE, LOCK_STATUS, OWNER_THREAD_ID
FROM performance_schema.metadata_locks
WHERE OBJECT_SCHEMA = 'learn' AND OBJECT_NAME = 'members';
-- LOCK_STATUS = GRANTED là đang giữ, PENDING là đang chờ
SELECT * FROM sys.schema_table_lock_waits\G     -- gom sẵn: ai chặn, câu KILL gợi ý
```

⚠️ Thủ phạm thường **không hiện** câu lệnh nào trong processlist (`Command = Sleep`), vì nó đang
rảnh giữa transaction. Tìm theo `information_schema.innodb_trx` (transaction mở lâu) hoặc theo
`OWNER_THREAD_ID` của lock `GRANTED`.

Cách phòng khi chạy migration:

1. Đặt timeout ngắn cho session DDL và retry:

   ```sql
   SET SESSION lock_wait_timeout = 5;       -- chờ MDL tối đa 5 giây rồi báo lỗi 1205
   ALTER TABLE members ADD COLUMN note VARCHAR(20), ALGORITHM=INSTANT;
   ```

   Nếu không lấy được lock trong 5 giây, `ALTER` bỏ cuộc và nhả chỗ trong hàng đợi, app chỉ bị chậm
   tối đa 5 giây. Script migration thử lại vài lần có nghỉ. Trong Laravel có thể chạy
   `DB::statement('SET SESSION lock_wait_timeout = 5')` ở đầu migration.
2. Trước khi migrate, kiểm tra transaction dài (`innodb_trx` với `trx_started` cũ hơn vài phút) và
   xử lý chúng trước.
3. Ở tầng app: không để transaction mở lâu, đặt timeout cho job báo cáo, tránh mở transaction trong
   console production.
4. Tool online như gh-ost, pt-online-schema-change cũng cần MDL exclusive ở bước đổi tên bảng cuối
   cùng, nên vẫn cần timeout ngắn và retry (module 3.3).

Đối chiếu Postgres: `ALTER TABLE` phần lớn lấy `ACCESS EXCLUSIVE`, mức lock bảng xung đột với mọi mức
khác, kể cả `ACCESS SHARE` mà `SELECT` thường lấy. Hàng đợi cũng xếp theo thứ tự, nên cùng một chuỗi
sự cố xảy ra y hệt. Cách phòng tương đương: `SET lock_timeout = '5s'` trước DDL rồi retry.

| Mức lock bảng Postgres | Ai lấy | Xung đột với `ACCESS EXCLUSIVE`? |
|---|---|---|
| `ACCESS SHARE` | `SELECT` | Có |
| `ROW EXCLUSIVE` | `INSERT`, `UPDATE`, `DELETE` | Có |
| `SHARE` | `CREATE INDEX` (không `CONCURRENTLY`) | Có |
| `ACCESS EXCLUSIVE` | Phần lớn `ALTER TABLE`, `DROP`, `TRUNCATE` | Có |

**Tóm tắt nhanh**
- InnoDB khoá entry index đã quét, không phải dòng khớp `WHERE`; không có index là khoá cả bảng.
  Kiểm tra thực tế bằng `performance_schema.data_locks`.
- Gap lock chỉ chặn insert và không xung đột nhau; insert intention xung đột với gap lock. Từ đó ra
  deadlock check-then-insert. Sửa bằng unique constraint + upsert, RC, hoặc khoá dòng có thật, và
  luôn retry.
- Deadlock rollback cả transaction; lock wait timeout mặc định chỉ rollback câu lệnh.
- Đọc deadlock log: mỗi bên giữ gì, chờ gì, trên index nào; log chỉ in câu đang chạy.
- AUTO-INC mode 2 mặc định: nhanh, id có lỗ, cần binlog `ROW`/`MIXED`.
- Sự cố MDL: transaction dài giữ shared, `ALTER` chờ exclusive, mọi query sau xếp sau `ALTER`.
  Phòng bằng `lock_wait_timeout` ngắn + retry và dọn transaction dài trước khi migrate.

**Nguồn**: [MySQL: InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html) ·
[Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html) ·
[Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html) ·
[An InnoDB Deadlock Example](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-example.html) ·
[AUTO_INCREMENT Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html) ·
[Metadata Locking](https://dev.mysql.com/doc/refman/8.4/en/metadata-locking.html) ·
[PostgreSQL: Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)


---

### 3.3 Thay đổi schema online và migration không downtime

Module này trả lời: một câu `ALTER TABLE` trên bảng lớn đang nhận ghi sẽ khoá những gì và trong bao
lâu, khi nào phải dùng tool như gh-ost, và làm sao đổi schema mà code cũ lẫn code mới cùng chạy được
trong lúc deploy.

#### Online DDL của MySQL

*DDL* (Data Definition Language) là các câu đổi cấu trúc: `CREATE`, `ALTER`, `DROP`. "Online DDL"
nghĩa là InnoDB cố gắng đổi cấu trúc trong khi bảng vẫn cho đọc và ghi. Mỗi câu `ALTER` được thực
hiện theo một trong ba *algorithm*:

| Algorithm | Làm gì | Bảng có bị dựng lại? | Ghi đồng thời |
|---|---|---|---|
| `INSTANT` | Chỉ sửa metadata trong data dictionary | Không | Được |
| `INPLACE` | Làm việc bên trong InnoDB, không tạo bảng tạm ở tầng SQL. Có thể có hoặc không dựng lại bảng | Tuỳ thao tác | Thường được (`LOCK=NONE`) |
| `COPY` | Tạo bảng mới, copy từng dòng sang, rồi đổi tên | Có | Không: chỉ cho đọc |

Không khai `ALGORITHM` thì MySQL chọn cách nhẹ nhất mà thao tác hỗ trợ, theo thứ tự INSTANT, rồi
INPLACE, rồi COPY. Cái nguy là sự "âm thầm": bạn tưởng thao tác nhẹ, MySQL lại lặng lẽ chọn COPY và
khoá ghi hai tiếng. Vì vậy trên production luôn khai rõ:

```sql
ALTER TABLE orders ADD COLUMN note VARCHAR(255) NULL, ALGORITHM=INSTANT;
ALTER TABLE orders ADD INDEX idx_user_created (user_id, created_at), ALGORITHM=INPLACE, LOCK=NONE;
-- Nếu thao tác không làm được theo cách đã khai, MySQL báo lỗi NGAY, chưa đụng dữ liệu:
-- ERROR 1846 (0A000): ALGORITHM=INPLACE is not supported. Reason: ... Try ALGORITHM=COPY.
```

Mệnh đề `LOCK` quy định mức đồng thời tối thiểu bạn chấp nhận:

| `LOCK=` | Ý nghĩa |
|---|---|
| `NONE` | Cho cả đọc và ghi |
| `SHARED` | Cho đọc, chặn ghi |
| `EXCLUSIVE` | Chặn cả đọc lẫn ghi |
| `DEFAULT` (hoặc không ghi) | Cho đồng thời nhiều nhất mà thao tác hỗ trợ |

Nếu bạn yêu cầu mức lỏng hơn mức thao tác cho phép (ví dụ `LOCK=NONE` với thao tác bắt buộc chặn
ghi), câu lệnh thất bại ngay. Đây là lưới an toàn thứ hai.

Bảng tra các thao tác hay gặp, theo tài liệu MySQL 8.4 (trang "Online DDL Operations"):

| Thao tác | INSTANT | INPLACE | Dựng lại bảng | Cho ghi đồng thời | Ghi chú |
|---|---|---|---|---|---|
| Thêm cột | Có | Có | Không | Có | INSTANT ở mọi vị trí từ 8.0.29; xem giới hạn bên dưới |
| Xoá cột | Có | Có | Có (nếu INPLACE) | Có | INSTANT từ 8.0.29 |
| Đổi tên cột | Có | Có | Không | Có | Cột được bảng khác tham chiếu bằng FK: chỉ INPLACE |
| Đổi thứ tự cột (`AFTER`, `FIRST` với cột có sẵn) | Không | Có | Có | Có | Dựng lại cả bảng |
| Đặt hoặc bỏ `DEFAULT` | Có | Có | Không | Có | |
| Đổi kiểu dữ liệu (`INT` sang `BIGINT`...) | Không | Không | Có | **Không** | Chỉ COPY, khoá ghi suốt quá trình |
| Nới `VARCHAR` | Không | Có | Không | Có | Chỉ khi không vượt ranh giới 255 byte (bên dưới) |
| Thu nhỏ `VARCHAR` | Không | Không | Có | Không | COPY |
| Đổi cột thành `NULL` | Không | Có | Có | Có | |
| Đổi cột thành `NOT NULL` | Không | Có | Có | Có | Cần strict mode; lỗi nếu còn dòng NULL |
| Sửa `ENUM`/`SET` (thêm giá trị vào cuối) | Có | Có | Không | Có | |
| Thêm secondary index | Không | Có | Không | Có | |
| Xoá hoặc đổi tên index | Không | Có | Không | Có | Chỉ sửa metadata |
| Thêm `FULLTEXT` index | Không | Có | Có với index đầu tiên | **Không** | |
| Thêm primary key | Không | Có | Có | Có | Đắt: tổ chức lại toàn bộ dữ liệu |
| Xoá primary key (không thêm cái mới) | Không | Không | Có | Không | COPY |
| Thêm foreign key | Không | Có | Không | Có | INPLACE chỉ khi `foreign_key_checks=0`, nếu không thì COPY |
| Thêm cột `STORED` generated | Không | Không | Có | Không | COPY. Cột `VIRTUAL` thì INSTANT được |
| Thêm cột `AUTO_INCREMENT` | Không | Có | Có | **Không** | Tối thiểu `LOCK=SHARED` |
| Đổi charset (`CONVERT TO CHARACTER SET`) | Không | Có | Có | **Không** | |
| Đổi tên bảng | Có | Có | Không | Có | |
| `OPTIMIZE TABLE`, `ALTER TABLE ... FORCE` | Không | Có | Có | Có | Không dùng được với bảng có FULLTEXT |

Ba chi tiết hay bị hỏi vặn:

1. **Ranh giới 255 byte của `VARCHAR`**: InnoDB lưu độ dài của giá trị bằng 1 byte nếu độ dài tối đa
   của cột không quá 255 byte, và bằng 2 byte nếu lớn hơn. Nới trong cùng một nhóm là INPLACE, chỉ sửa
   metadata. Nới vượt ranh giới (1 byte thành 2 byte) buộc phải COPY. Ranh giới tính theo **byte**,
   nên với `utf8mb4` (4 byte mỗi ký tự) thì `VARCHAR(63)` là 252 byte, còn `VARCHAR(64)` đã là 256
   byte. Nới `VARCHAR(50)` lên `VARCHAR(100)` trên cột `utf8mb4` là đi từ 200 lên 400 byte, tức vượt
   ranh giới, phải COPY.
2. **Giới hạn của INSTANT khi thêm hoặc xoá cột**:
   - Mỗi lần thêm hoặc xoá cột bằng INSTANT tạo một *row version*. Tối đa 64 row version (MySQL 9.1
     nâng lên 255); hết thì gặp `ERROR 4092 ... Maximum row versions reached`, và phải dựng lại bảng
     bằng INPLACE/COPY (dựng lại thì bộ đếm về 0). Xem bằng
     `SELECT NAME, TOTAL_ROW_VERSIONS FROM INFORMATION_SCHEMA.INNODB_TABLES WHERE NAME = 'shop/orders';`
   - Không dùng được với bảng `ROW_FORMAT=COMPRESSED`, bảng có `FULLTEXT` index, bảng tạm.
   - Không gộp được với thao tác khác không hỗ trợ INSTANT trong cùng một câu `ALTER`.
3. **Đổi kiểu cột luôn là COPY**, kể cả `INT` sang `BIGINT`. Đây là lý do module 1.4 khuyên dùng
   `BIGINT` cho id ngay từ đầu.

#### Các pha của một câu ALTER và metadata lock

"Online" không có nghĩa là không khoá gì. Mọi algorithm đều đi qua ba pha, và đều cần *MDL
exclusive* (metadata lock độc quyền, module 3.2) trong một khoảnh khắc:

```
1. Initialization   lấy MDL "shared upgradable": vẫn cho mọi người đọc/ghi
2. Execution        có thể nâng lên MDL exclusive RẤT NGẮN lúc chuẩn bị; rồi copy/dựng index
                    trong khi DML chạy song song (INPLACE ghi lại DML vào một "online log")
3. Commit           nâng lên MDL exclusive để thay định nghĩa bảng cũ bằng mới, rất ngắn
```

Khoảnh khắc ngắn đó là nơi sự cố xảy ra. Tài liệu MySQL mô tả đúng kịch bản của module 3.2:

| Bước | Session A | Session B (migration) | Session C (app) | Kết quả |
|---|---|---|---|---|
| 1 | `START TRANSACTION; SELECT * FROM t1;` (chưa commit) | | | A giữ MDL shared trên `t1` |
| 2 | | `ALTER TABLE t1 ADD COLUMN x INT, ALGORITHM=INSTANT;` | | B chờ MDL exclusive: `Waiting for table metadata lock` |
| 3 | | | `SELECT * FROM t1;` | C **bị chặn** vì xếp hàng sau yêu cầu exclusive của B |
| 4 | | | (mọi request mới đều xếp hàng) | Pool cạn, app sập dù `ALTER` chỉ cần vài mili giây |
| 5 | `COMMIT;` | Chạy xong ngay | Chạy tiếp | |

Phòng bằng `lock_wait_timeout` (mặc định 31536000 giây, tức một năm) đặt ngắn cho session chạy
migration, thất bại thì thử lại sau:

```sql
SET SESSION lock_wait_timeout = 5;   -- chờ MDL tối đa 5 giây rồi bỏ cuộc, trả lại hàng đợi cho app
ALTER TABLE orders ADD COLUMN note VARCHAR(255) NULL, ALGORITHM=INSTANT;
-- Trước khi chạy: có transaction nào mở lâu không?
SELECT trx_id, trx_started, trx_mysql_thread_id FROM information_schema.innodb_trx
WHERE trx_started < NOW() - INTERVAL 30 SECOND;
```

Ba giới hạn khác của online DDL ở dạng INPLACE:

- Các DML chạy song song được ghi vào một *online log* tạm, áp lại ở cuối. Log này bị giới hạn bởi
  `innodb_online_alter_log_max_size` (mặc định 128 MB); bảng ghi quá nhiều trong lúc `ALTER` chạy thì
  log đầy và `ALTER` thất bại, phải chạy lại từ đầu.
- Không tạm dừng hay điều tốc được: đã chạy là chạy hết, ăn I/O và CPU của primary.
- ⚠️ **Replica lag**: DDL được ghi vào binlog như một câu lệnh và chỉ được gửi sang replica **sau
  khi** chạy xong trên primary. Replica chạy lại đúng câu đó, và trong lúc chạy thì các transaction
  phía sau phải chờ. `ALTER` mất 2 tiếng trên primary nghĩa là replica trễ khoảng 2 tiếng ngay sau đó.
  Đây là lý do chính để dùng tool bên ngoài ngay cả khi thao tác là INPLACE.

#### Tool cho các thao tác phải COPY

Ý tưởng chung của các tool: thay vì để MySQL copy bảng trong một câu lệnh không kiểm soát được, tool
tự copy theo từng khúc nhỏ, vừa copy vừa đồng bộ thay đổi mới, và chỉ đổi bảng ở giây cuối.

**pt-online-schema-change** (Percona Toolkit), cách dùng trigger:

1. Tạo bảng rỗng `_orders_new` có cấu trúc mới.
2. Tạo ba trigger `AFTER INSERT/UPDATE/DELETE` trên `orders`, chép mọi thay đổi sang `_orders_new`
   trong **cùng transaction** với câu lệnh gốc.
3. Copy dữ liệu cũ theo khúc (mặc định điều chỉnh kích thước khúc để mỗi khúc chạy khoảng 0,5 giây,
   `--chunk-time 0.5`), dừng lại khi replica trễ quá `--max-lag` (mặc định 1s) hoặc
   `Threads_running` vượt `--max-load` (mặc định 25); vượt `--critical-load` (mặc định 50) thì huỷ.
4. `RENAME TABLE orders TO _orders_old, _orders_new TO orders` (một câu, nguyên tử), rồi xoá bảng cũ.

Yêu cầu bảng có primary key hoặc unique index. Khoá ngoại là phần rắc rối nhất: các bảng con trỏ tới
`orders` vẫn trỏ vào bảng cũ sau khi rename, nên tool có tuỳ chọn `--alter-foreign-keys-method`
(`rebuild_constraints`, `drop_swap`...), mỗi cách có rủi ro riêng.

**gh-ost** (GitHub), cách không dùng trigger (*triggerless*). Tài liệu gh-ost nêu các vấn đề của
trigger đã gặp ở production:

- Trigger là stored routine được *thông dịch*, chạy cho **từng dòng** trong transaction của app, nên
  mọi câu ghi của app chậm thêm.
- Trigger tranh lock cùng lúc với câu lệnh gốc, không phối hợp với nhau; GitHub từng thấy bảng,
  thậm chí cả DB, gần như bị khoá cứng.
- **Không tạm dừng thật được**: tool chỉ dừng được phần copy, còn trigger vẫn phải chạy (tắt trigger
  là mất dữ liệu). Primary đang quá tải thì tải của trigger vẫn còn nguyên.
- Không thử được trên replica một cách đáng tin.

gh-ost thay trigger bằng binlog. Nó giả làm một replica, kết nối tới MySQL và nhận luồng binlog ở
dạng `ROW` (mỗi dòng bị đổi là một event riêng), lọc ra các event của bảng đang migrate. Từng bước:

1. **Chuẩn bị** (không có gì chạy song song):
   - Tạo bảng changelog `_orders_ghc` (dùng để ghi trạng thái và heartbeat) và bảng ghost
     `_orders_gho` giống hệt `orders`, rồi chạy `ALTER` lên bảng ghost (bảng rỗng nên tức thì).
   - So hai bảng, chọn một *shared unique key* (thường là PK) có ở cả hai bảng để chia khúc.
   - Bắt đầu nghe binlog, rồi ghi một dòng "good to go" vào changelog; khi thấy chính dòng đó đi qua
     binlog là biết luồng đã thông.
   - Đọc giá trị min/max của key.
2. **Copy và áp thay đổi song song**:
   - Copy từng khúc theo key, mặc định `--chunk-size 1000` dòng, bằng
     `INSERT IGNORE INTO _orders_gho SELECT ... FROM orders WHERE id BETWEEN ? AND ?`.
   - Đồng thời đọc event binlog của `orders` và áp lên bảng ghost (insert thành `REPLACE INTO`,
     update và delete tương ứng).
   - Chỉ một connection ghi vào bảng ghost, xen kẽ giữa copy và áp binlog, nên không có tranh lock.
     Vì sao kết quả đúng dù thứ tự lộn xộn: copy dùng `INSERT IGNORE` nên không bao giờ ghi đè dòng mà
     binlog đã áp; binlog dùng `REPLACE` nên luôn đè lên bản copy cũ hơn. Trạng thái cuối của mỗi dòng
     là trạng thái mới nhất trong binlog.
   - Liên tục ghi heartbeat vào changelog để đo lag của chính replica mà nó đọc.
3. **Điều tốc** (*throttle*): khi throttle, gh-ost dừng **cả** copy lẫn áp binlog, primary không
   phải ghi gì thêm cho migration. Các điều kiện:
   - `--max-lag-millis`: replica nào trong danh sách `--throttle-control-replicas` trễ quá ngưỡng.
   - `--max-load`, ví dụ `Threads_running=25`; `--critical-load` vượt thì huỷ hẳn.
   - Có file cờ throttle, hoặc lệnh `throttle` gửi qua unix socket.
4. **Hoãn cut-over**: với `--postpone-cut-over-flag-file=/tmp/ghost.postpone`, copy xong gh-ost vẫn
   tiếp tục áp binlog để bảng ghost luôn bắt kịp, nhưng không đổi bảng cho tới khi bạn xoá file (hoặc
   gửi lệnh `unpostpone`). Nhờ vậy bước rủi ro nhất diễn ra lúc bạn đang ngồi theo dõi.
5. **Cut-over nguyên tử**. gh-ost được thiết kế từ thời MySQL 5.x, khi một connection đang giữ
   `LOCK TABLES` không được `RENAME` bảng (MySQL 8.4 đã cho phép với bảng khoá `WRITE`), nên gh-ost
   dùng hai connection và một bảng "lính gác" (*sentry*) `_orders_del`:
   1. Connection 1 tạo bảng `_orders_del`, rồi `LOCK TABLES orders WRITE, _orders_del WRITE`. Từ đây
      mọi câu ghi của app vào `orders` phải chờ.
   2. Connection 2 chạy `RENAME TABLE orders TO _orders_del, _orders_gho TO orders`. Câu này bị chặn,
      vì `orders` đang bị khoá và vì `_orders_del` đã tồn tại.
   3. gh-ost kiểm tra trong processlist là câu `RENAME` đang chờ, rồi áp nốt các event binlog còn tồn.
   4. Connection 1 `DROP TABLE _orders_del` rồi `UNLOCK TABLES`. MySQL ưu tiên câu `RENAME` đang chờ
      trước các câu DML, nên bảng được đổi ngay, và các câu ghi đang chờ chạy tiếp trên bảng mới.
   5. Nếu có sự cố: connection 1 chết thì lock tự nhả, nhưng `RENAME` thất bại vì `_orders_del` vẫn
      còn, nên bảng gốc nguyên vẹn. Connection 2 chết thì connection 1 xoá sentry và nhả lock. Giữ
      lock quá `--cut-over-lock-timeout-seconds` (mặc định 3) thì bỏ và thử lại sau. Cả hai trường hợp
      đều quay về trạng thái trước cut-over, app chỉ bị chặn ghi vài giây.
6. **Dọn dẹp**: bảng cũ nằm lại dưới tên `_orders_del` (chỉ tự xoá khi có `--ok-to-drop-table`, vì
   `DROP` một bảng lớn cũng có thể gây khựng). Giữ nó lại vài ngày là một cách rollback.

Điều khiển khi đang chạy, qua unix socket:

```sh
gh-ost --host=replica-1 --database=shop --table=orders \
  --alter="MODIFY amount BIGINT NOT NULL" \
  --chunk-size=1000 --max-lag-millis=1500 --max-load=Threads_running=25 \
  --critical-load=Threads_running=200 --throttle-control-replicas=replica-2,replica-3 \
  --postpone-cut-over-flag-file=/tmp/ghost.postpone --assume-rbr --execute
# Mặc định gh-ost kết nối vào replica để đọc binlog, tự tìm ra primary để ghi.
# Bỏ --execute là chạy thử (noop): kiểm tra tạo bảng và tính hợp lệ của migration, không đụng dữ liệu.
echo status             | nc -U /tmp/gh-ost.shop.orders.sock   # tiến độ, ETA, lag
echo "chunk-size=500"   | nc -U /tmp/gh-ost.shop.orders.sock   # đổi tốc độ khi đang chạy
echo throttle           | nc -U /tmp/gh-ost.shop.orders.sock   # tạm dừng hẳn
rm /tmp/ghost.postpone                                         # cho phép cut-over
```

Yêu cầu và giới hạn của gh-ost: binlog `ROW` với `binlog_row_image=FULL` (cả hai là mặc định của
MySQL 8.x); **không hỗ trợ foreign key và trigger** trên bảng migrate; bảng cũ và mới phải chung một
PK hoặc unique key không chứa NULL.

| | Online DDL INPLACE | pt-online-schema-change | gh-ost |
|---|---|---|---|
| Cơ chế đồng bộ thay đổi | Online log trong InnoDB | Trigger, đồng bộ trong transaction của app | Đọc binlog, bất đồng bộ |
| Tạm dừng, điều tốc | Không | Chỉ dừng được phần copy | Dừng hẳn, đổi tham số khi đang chạy |
| Lag trên replica | Trễ bằng cả thời gian `ALTER` | Theo khúc, điều tốc theo lag | Theo khúc, điều tốc theo lag |
| Foreign key | Được | Được, có tuỳ chọn riêng | Không |
| Dung lượng đĩa thêm | Có nếu dựng lại bảng | Khoảng bằng một bảng nữa | Khoảng bằng một bảng nữa |

⚠️ Cả hai tool cần thêm dung lượng khoảng bằng kích thước bảng (cộng binlog sinh ra do copy), và
cut-over vẫn cần MDL, nên vẫn phải lo transaction dài như ở trên.

Tóm lại quy trình quyết định cho bảng lớn:

1. Tra bảng trên: thao tác có INSTANT không? Có thì chạy trực tiếp, khai `ALGORITHM=INSTANT` và
   `lock_wait_timeout` ngắn.
2. Không có INSTANT nhưng INPLACE `LOCK=NONE` được: bảng nhỏ hoặc chấp nhận replica trễ thì chạy trực
   tiếp; bảng lớn có replica phục vụ đọc thì dùng gh-ost.
3. Phải COPY: dùng gh-ost (hoặc pt-osc nếu bảng có foreign key).

#### Expand/contract

Tool giải quyết chuyện "đổi schema mà không khoá bảng". Còn một vấn đề nữa nằm ở tầng app: trong lúc
deploy (rolling deploy, nhiều server lần lượt nhận code mới), code cũ và code mới cùng chạy trên một
schema trong vài phút. Nếu bạn đổi tên cột `amount` thành `amount_minor` (một thao tác INSTANT, tức
thì), mọi server còn chạy code cũ lập tức lỗi `Unknown column 'amount'`. Schema đổi nhanh không cứu
được bạn khỏi lỗi tương thích.

*Parallel change* (Martin Fowler), hay *expand/contract*, chia một thay đổi không tương thích thành
ba pha, mỗi pha đều an toàn với cả code trước và sau nó:

1. **Expand**: thêm cái mới bên cạnh cái cũ. Cả hai cùng tồn tại.
2. **Migrate**: chuyển dần mọi nơi dùng sang cái mới (code, dữ liệu, job, báo cáo).
3. **Contract**: xoá cái cũ khi chắc chắn không còn ai dùng.

Fowler lưu ý cái giá: trong lúc chuyển có hai phiên bản cùng tồn tại, dễ gây nhầm, và nếu không đủ kỷ
luật làm nốt pha contract thì hệ thống còn tệ hơn lúc đầu.

Ví dụ cụ thể: bảng `orders` 200 triệu dòng có cột `amount INT` lưu tiền theo đồng, sắp tràn
2.147.483.647 vì có đơn hàng doanh nghiệp. Mục tiêu: cột `amount_minor BIGINT NOT NULL`. Đổi kiểu
trực tiếp là COPY khoá ghi hàng giờ, nên ta làm expand/contract; mỗi bước là **một lần deploy riêng**.

Bước 1, expand schema (migration riêng, deploy trước mọi thay đổi code):

```php
<?php
declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        // Chờ MDL tối đa 5 giây; thất bại thì deploy báo lỗi và ta chạy lại, app không bị treo
        DB::statement('SET SESSION lock_wait_timeout = 5');

        Schema::table('orders', function (Blueprint $table): void {
            // nullable: cột mới chưa có dữ liệu. instant(): sinh "ALGORITHM=INSTANT" (Laravel 13, MySQL);
            // Laravel không cho gộp instant() với after()/first(), cột sẽ nằm cuối bảng
            $table->bigInteger('amount_minor')->nullable()->instant();
        });
    }

    public function down(): void
    {
        Schema::table('orders', function (Blueprint $table): void {
            $table->dropColumn('amount_minor');
        });
    }
};
```

Code cũ không biết cột mới nên không bị ảnh hưởng. Rollback bước này: xoá cột, không mất gì.

Bước 2, deploy code ghi cả hai cột, vẫn đọc cột cũ:

```php
<?php
declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

final class Order extends Model
{
    protected static function booted(): void
    {
        // Mọi lần save qua Eloquent đều ghi cả hai cột. Chỗ nào update bằng query builder
        // hoặc SQL tay (import, job hàng loạt) cũng phải sửa theo: grep toàn bộ codebase
        static::saving(function (Order $order): void {
            if ($order->isDirty('amount')) {
                $order->amount_minor = (int) $order->amount;
            }
        });
    }
}
```

Rollback: deploy lại code cũ, cột mới chỉ đơn giản ngừng được cập nhật.

Bước 3, backfill dữ liệu cũ theo batch, điều tốc theo replica lag (chạy bằng artisan command, không
phải migration, vì có thể mất nhiều giờ):

```php
<?php
declare(strict_types=1);

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;

final class BackfillOrderAmountMinor extends Command
{
    protected $signature = 'orders:backfill-amount-minor {--batch=2000} {--max-lag=2}';

    public function handle(): int
    {
        $batch = (int) $this->option('batch');
        $maxLag = (int) $this->option('max-lag');
        $lastId = 0;
        $maxId = (int) DB::table('orders')->max('id');

        while ($lastId < $maxId) {
            // Mỗi batch là một câu UPDATE ngắn theo khoảng PK: lock ít dòng, transaction ngắn,
            // binlog nhỏ nên replica áp nhanh. Tính từ cột cũ NGAY TRONG câu UPDATE, nên không có
            // khoảng hở để ghi đè giá trị mà code bước 2 vừa ghi.
            DB::update(
                'UPDATE orders SET amount_minor = amount
                 WHERE id > ? AND id <= ? AND amount_minor IS NULL',
                [$lastId, $lastId + $batch],
            );
            $lastId += $batch;

            while (($lag = $this->replicaLagSeconds()) === null || $lag > $maxLag) {
                $this->warn('Replica lag ' . var_export($lag, true) . 's, tạm dừng');
                sleep(1);
            }
        }

        return self::SUCCESS;
    }

    private function replicaLagSeconds(): ?int
    {
        // Cần connection 'mysql_replica' trỏ thẳng vào replica, user có quyền REPLICATION CLIENT.
        // NULL nghĩa là replication đang dừng: coi như nguy hiểm, không chạy tiếp.
        $row = DB::connection('mysql_replica')->selectOne('SHOW REPLICA STATUS');
        $lag = $row?->Seconds_Behind_Source ?? null;

        return $lag === null ? null : (int) $lag;
    }
}
```

Xong backfill thì kiểm tra: `SELECT COUNT(*) FROM orders WHERE amount_minor IS NULL` phải bằng 0,
và `SELECT COUNT(*) FROM orders WHERE amount_minor <> amount` bằng 0 (chạy trên replica, theo khoảng
id). Nên dùng heartbeat thay cho `Seconds_Behind_Source` nếu có (module 3.4).

Bước 4, deploy code đọc cột mới (vẫn ghi cả hai). Nếu có lỗi, quay về code bước 2 là xong, vì cột
cũ vẫn đầy đủ.

Bước 5, deploy code chỉ ghi `amount_minor`, bỏ hẳn `amount` khỏi model, `$fillable`, `$casts`, query.
Từ bước này rollback về bước 4 không còn an toàn tuyệt đối: dòng mới không có giá trị ở `amount`.
Trước bước này cột cũ phải cho NULL hoặc có default, nếu không insert từ code mới sẽ lỗi. Đổi
`amount` thành nullable là INPLACE nhưng dựng lại bảng, nên với bảng lớn hãy gộp nó vào một lần chạy
gh-ost từ sớm (ví dụ ngay ở bước 1: `--alter="ADD COLUMN amount_minor BIGINT NULL, MODIFY amount INT
NULL"`).

⚠️ Chú ý riêng của ví dụ này: trong các bước 2 tới 4, code vẫn ghi `amount INT`, nên đơn vượt
2.147.483.647 vẫn chưa nhận được (strict mode báo lỗi tràn). Expand/contract mất nhiều ngày, vì vậy
phải bắt đầu khi còn cách ngưỡng xa, không phải khi đã chạm ngưỡng.

Bước 6, contract schema, sau vài ngày chạy ổn:

```php
// Đặt NOT NULL cho cột mới: INPLACE nhưng dựng lại bảng, bảng 200 triệu dòng thì dùng gh-ost:
//   --alter="MODIFY amount_minor BIGINT NOT NULL"
// Xoá cột cũ: INSTANT được từ 8.0.29
DB::statement('SET SESSION lock_wait_timeout = 5');
Schema::table('orders', function (Blueprint $table): void {
    $table->dropColumn('amount');
});
```

Các bẫy của expand/contract:

- ⚠️ Xoá cột khi code cũ còn đọc hoặc ghi nó: lỗi ngay trong lúc deploy. Eloquent `SELECT *` nên đọc
  không lỗi, nhưng code cũ có `$order->amount` hay `insert` có cột `amount` thì lỗi. Một số ORM khác
  (ActiveRecord của Rails) còn cache danh sách cột lúc khởi động, nên phải khai "bỏ qua cột" trước khi
  xoá.
- ⚠️ Migration huỷ dữ liệu (`dropColumn`, `drop`) tách khỏi lần deploy code, và chỉ chạy khi đã chắc
  không cần lùi. Có backup hoặc giữ bảng/cột cũ vài ngày.
- ⚠️ `->change()` trong Laravel phải khai **lại mọi modifier** muốn giữ (`unsigned`, `default`,
  `nullable`, `comment`); thiếu cái nào là mất cái đó. Và `change()` đổi kiểu cột thì vẫn là COPY.
- Thêm cột `NOT NULL` cho bảng lớn: thêm cột nullable (INSTANT), backfill, rồi mới đặt `NOT NULL`.
  Thêm thẳng `NOT NULL DEFAULT x` thì INSTANT được, nhưng mọi dòng cũ nhận giá trị default, có thể
  không đúng nghiệp vụ.
- Deploy nhiều server cùng chạy `php artisan migrate`: dùng `--isolated` để Laravel lấy lock qua
  cache, chỉ một server chạy. `php artisan migrate --pretend` in ra SQL để kiểm tra algorithm trước.

#### Đối chiếu Postgres

Postgres có mô hình khác: phần lớn `ALTER TABLE` lấy lock `ACCESS EXCLUSIVE`, chặn cả `SELECT`, và
cũng có vấn đề xếp hàng giống MDL (một `ALTER` đang chờ làm mọi query sau phải chờ). Đổi lại, DDL
của Postgres chạy được trong transaction và rollback được.

- `CREATE INDEX CONCURRENTLY`: dựng index mà không chặn ghi, bằng cách quét bảng hai lần và chờ các
  transaction đang chạy kết thúc. Không chạy được trong transaction block (Laravel sinh câu này khi
  gọi `->online()` trên index; migration Postgres của Laravel mặc định bọc transaction, nên kiểm tra
  kỹ trước khi dùng). Nếu lỗi giữa chừng (ví dụ trùng khi tạo unique), nó để lại
  một index `INVALID` vẫn tốn chi phí ghi; phải `DROP INDEX CONCURRENTLY` rồi làm lại.
- Thêm ràng buộc trên bảng lớn chia hai bước: `ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY
  (user_id) REFERENCES users(id) NOT VALID;` (nhanh, chỉ kiểm tra dòng mới), rồi
  `ALTER TABLE orders VALIDATE CONSTRAINT fk_user;` (quét bảng nhưng lấy lock nhẹ hơn, không chặn ghi).
- `SET lock_timeout = '5s'` trước DDL, tương đương `lock_wait_timeout` của MySQL.
- Thêm cột có default không đổi (non-volatile) chỉ sửa metadata từ Postgres 11, tương tự INSTANT.

**Tóm tắt nhanh**
- Luôn khai `ALGORITHM=INSTANT/INPLACE` và `LOCK=NONE` để MySQL báo lỗi thay vì âm thầm COPY.
- Thêm/xoá/đổi tên cột: INSTANT. Thêm index: INPLACE cho ghi. Đổi kiểu cột: COPY, khoá ghi.
- Mọi DDL đều cần MDL exclusive một khoảnh khắc: đặt `lock_wait_timeout` ngắn và kiểm tra transaction
  dài trước khi chạy.
- Bảng lớn: gh-ost copy theo khúc, đọc binlog, dừng được, điều tốc theo replica lag, cut-over nguyên
  tử; đổi lại không hỗ trợ foreign key. Có FK thì dùng pt-osc.
- Expand/contract: thêm mới, ghi cả hai, backfill theo batch, đọc mới, ngừng ghi cũ, xoá cũ; mỗi bước
  một lần deploy, bước nào cũng chạy được với code trước nó.

**Nguồn**: [MySQL: Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html) ·
[MySQL: Online DDL Performance and Concurrency](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-performance.html) ·
[gh-ost](https://github.com/github/gh-ost) ([Why triggerless](https://github.com/github/gh-ost/blob/master/doc/why-triggerless.md),
[Triggerless design](https://github.com/github/gh-ost/blob/master/doc/triggerless-design.md),
[Cut-over](https://github.com/github/gh-ost/blob/master/doc/cut-over.md)) ·
[pt-online-schema-change](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html) ·
[Martin Fowler: Parallel Change](https://martinfowler.com/bliki/ParallelChange.html) ·
[Laravel: Migrations](https://laravel.com/docs/migrations)

---

### 3.4 Replication và failover

Module này trả lời: dữ liệu đi từ primary sang replica qua những bước nào, mỗi mức đồng bộ (async,
semi-sync) hứa hẹn gì khi primary chết, và làm sao để user không thấy dữ liệu cũ ngay sau khi vừa sửa.

#### Cơ chế

*Replication* là giữ một hoặc nhiều bản sao (*replica*) của DB chính (*primary*, tài liệu MySQL gọi
là *source*). MySQL 8.4 đã bỏ hẳn các lệnh dùng từ "master/slave": `SHOW SLAVE STATUS` thành
`SHOW REPLICA STATUS`, `CHANGE MASTER TO` thành `CHANGE REPLICATION SOURCE TO`, `SHOW MASTER STATUS`
thành `SHOW BINARY LOG STATUS`.

Luồng một transaction đi qua ba thread:

```
PRIMARY                                   REPLICA
 app COMMIT                                
   │ ghi binlog (sync_binlog=1: fsync)     
   ▼                                       
 [binlog] ──► Binlog Dump thread ──mạng──► Receiver (I/O) thread
                                             │ ghi vào relay log (file cục bộ)
                                             ▼
                                           [relay log]
                                             │
                                           Coordinator thread
                                             │ phân việc
                                   ┌─────────┼─────────┐
                                   ▼         ▼         ▼
                                Worker 1  Worker 2  Worker N   áp transaction, ghi binlog riêng
```

1. Primary ghi transaction vào *binlog* (binary log) lúc commit. Format mặc định là `ROW`: ghi giá trị
   của từng dòng bị đổi, không ghi câu SQL.
2. Khi replica kết nối, primary tạo một thread *Binlog Dump* cho replica đó, đẩy binlog sang.
3. *Receiver thread* (tên cũ: I/O thread) trên replica nhận và ghi vào *relay log*, một bản sao cục bộ
   của binlog.
4. *Applier* (tên cũ: SQL thread) đọc relay log và áp. Khi `replica_parallel_workers` lớn hơn 0 (mặc
   định là 4 từ 8.0.27), có một coordinator đọc tuần tự và chia transaction cho các worker áp song
   song. Từ 8.4, primary luôn dùng *writeset* để tính phụ thuộc: hai transaction không đụng chung
   dòng nào thì replica áp song song được.

Hệ quả quan trọng: replica **không giảm tải ghi**. Mỗi replica phải áp lại mọi thao tác ghi của
primary. Replica giúp scale đọc, dự phòng khi primary chết, và chạy backup hay báo cáo nặng.

*GTID* (Global Transaction Identifier) là mã định danh duy nhất cho mỗi transaction đã commit, dạng
`source_uuid:transaction_id`, ví dụ `3E11FA47-71CA-11E1-9E33-C80AA9429562:23` là transaction thứ 23
commit trên server có UUID đó. Một *GTID set* gộp các khoảng liên tiếp:
`3E11FA47-...:1-5:11:47-49`, nhiều server cách nhau bằng dấu phẩy.

Trước GTID, replica nhớ vị trí bằng cặp (tên file binlog, offset). Cặp này chỉ có nghĩa trên đúng một
server: khi primary chết và một replica khác lên thay, các replica còn lại không biết vị trí tương ứng
trong binlog của primary mới, và phải dò bằng tay. GTID giải quyết:

- Mỗi server có `@@GLOBAL.gtid_executed`: tập GTID đã áp. Transaction từ primary giữ nguyên GTID khi
  sang replica.
- Với `SOURCE_AUTO_POSITION = 1`, replica gửi tập `gtid_executed` của mình, primary tự tìm các
  transaction còn thiếu và gửi tiếp. Đổi primary chỉ cần trỏ sang host mới.
- Một GTID đã commit trên server thì lần sau gặp lại sẽ bị bỏ qua, không lỗi. Nhờ vậy không áp một
  transaction hai lần.

```sql
-- Bật GTID (my.cnf): gtid_mode=ON, enforce_gtid_consistency=ON
CHANGE REPLICATION SOURCE TO SOURCE_HOST='db-primary', SOURCE_USER='repl',
  SOURCE_PASSWORD='...', SOURCE_AUTO_POSITION=1;
START REPLICA;
SHOW REPLICA STATUS\G
-- Retrieved_Gtid_Set: GTID đã NHẬN vào relay log
-- Executed_Gtid_Set:  GTID đã ÁP xong (bằng @@GLOBAL.gtid_executed)
-- Hai tập khác nhau nghĩa là còn việc chưa áp
SELECT GTID_SUBTRACT(@@GLOBAL.gtid_executed, '<gtid_executed của primary>');  -- xem bên dưới
```

`enforce_gtid_consistency=ON` từ chối các câu lệnh không ghi được thành một transaction an toàn, ví
dụ trộn bảng InnoDB và bảng không transaction (MyISAM) trong cùng transaction.

#### Các mức đồng bộ

**Async** (mặc định): primary commit và trả lời client ngay, không chờ replica. Nhanh nhất, nhưng khi
primary chết, những transaction chưa kịp sang replica sẽ mất nếu ta đưa replica lên làm primary.

**Semi-sync**: plugin `rpl_semi_sync_source` trên primary và `rpl_semi_sync_replica` trên replica.
Primary chờ ít nhất `rpl_semi_sync_source_wait_for_replica_count` (mặc định 1) replica xác nhận đã
**nhận và ghi xuống đĩa** các event vào relay log, rồi mới trả lời client. Replica chưa chắc đã áp.

```sql
-- primary
INSTALL PLUGIN rpl_semi_sync_source SONAME 'semisync_source.so';
SET GLOBAL rpl_semi_sync_source_enabled = ON;
-- replica
INSTALL PLUGIN rpl_semi_sync_replica SONAME 'semisync_replica.so';
SET GLOBAL rpl_semi_sync_replica_enabled = ON;
STOP REPLICA IO_THREAD; START REPLICA IO_THREAD;   -- kết nối lại để đăng ký semi-sync
-- theo dõi trên primary
SHOW STATUS LIKE 'Rpl_semi_sync_source_status';    -- ON: đang semi-sync, OFF: đã rơi về async
SHOW STATUS LIKE 'Rpl_semi_sync_source_no_tx';     -- số transaction commit mà KHÔNG được xác nhận
```

Chờ ở điểm nào, cấu hình bằng `rpl_semi_sync_source_wait_point`:

| | `AFTER_SYNC` (mặc định) | `AFTER_COMMIT` |
|---|---|---|
| Thứ tự | Ghi binlog, fsync, **chờ replica**, rồi mới commit vào InnoDB | Ghi binlog, commit vào InnoDB, rồi mới chờ replica |
| Client khác thấy dữ liệu khi nào | Sau khi có xác nhận | Ngay khi commit, trước khi có xác nhận |
| Primary chết lúc đang chờ, failover sang replica | Không ai từng thấy dữ liệu chưa có ở replica: *lossless* | Có thể có client đã đọc thấy dữ liệu, rồi dữ liệu đó biến mất trên primary mới |

Semi-sync đảm bảo gì và không đảm bảo gì:

- Đảm bảo: với `AFTER_SYNC`, mọi transaction đã được báo commit thành công đều có mặt trên đĩa của ít
  nhất một replica. Failover sang **đúng replica đó** thì không mất.
- Không đảm bảo replica đã áp: đọc từ replica ngay sau khi ghi vẫn có thể thấy dữ liệu cũ.
- Không đảm bảo mọi replica có dữ liệu: replica bạn chọn làm primary mới phải là replica mới nhất
  (so bằng GTID).
- ⚠️ Không đảm bảo mãi mãi: chờ quá `rpl_semi_sync_source_timeout` (mặc định 10000 ms) mà không có
  xác nhận thì primary **tự rơi về async**, commit tiếp, và chỉ quay lại semi-sync khi có replica bắt
  kịp. Nếu primary chết đúng giai đoạn đó thì vẫn mất dữ liệu như async. Phải cảnh báo khi
  `Rpl_semi_sync_source_status` là OFF.
- ⚠️ Client có thể nhận lỗi (mất kết nối vì primary chết) cho một transaction mà thực tế đã có trên
  replica. Sau failover, transaction đó xuất hiện. App retry mù quáng có thể tạo bản ghi trùng, nên các
  thao tác quan trọng cần *idempotency key* (khoá chống lặp).
- Latency ghi tăng thêm ít nhất một vòng mạng tới replica. Đặt replica semi-sync cùng vùng mạng gần.
- Tài liệu MySQL khuyến cáo: sau khi failover, primary cũ **không được** dùng lại làm source mà nên
  loại bỏ, vì nó có thể chứa transaction chưa được replica nào xác nhận.

**Group Replication / InnoDB Cluster**: một nhóm server (thường 3 hoặc 5) đồng thuận qua một giao thức
kiểu Paxos trước khi commit; transaction chỉ commit khi đa số nhóm đồng ý. Có tự phát hiện node hỏng
và tự bầu primary mới (chế độ single-primary). *InnoDB Cluster* đóng gói Group Replication với MySQL
Shell để quản trị và MySQL Router để app tự trỏ đúng primary. Mức phỏng vấn thường chỉ cần biết: mạnh
hơn semi-sync về chống mất dữ liệu và tự failover, đổi lại latency cao hơn và vận hành phức tạp hơn.

| | Async | Semi-sync | Group Replication |
|---|---|---|---|
| Primary chờ gì | Không chờ | 1 replica ghi relay log xuống đĩa | Đa số nhóm đồng thuận |
| Mất dữ liệu khi failover | Có thể | Không, nếu chưa rơi về async và chọn đúng replica | Không (với đa số còn sống) |
| Latency ghi | Thấp nhất | Thêm một vòng mạng | Cao hơn |
| Tự failover | Không, cần tool ngoài | Không, cần tool ngoài | Có |

#### Replication lag

*Replication lag* là khoảng trễ giữa lúc primary commit và lúc replica áp xong. Nguyên nhân thường gặp:

1. **Transaction rất lớn**: `UPDATE` 10 triệu dòng chạy 5 phút trên primary, rồi sang replica chạy
   thêm 5 phút nữa, và trong lúc đó các transaction sau (phụ thuộc vào thứ tự commit) phải chờ. Cách
   phòng: chia batch như ở module 3.3.
2. **DDL lớn**: `ALTER TABLE` chỉ sang replica sau khi xong trên primary (module 3.3).
3. **Replica yếu hơn** primary, hoặc đang chạy query báo cáo nặng tranh I/O.
4. **Áp log không đủ song song**: transaction đụng chung dòng nóng (một dòng counter) không áp song
   song được dù có nhiều worker.
5. **Mạng chậm** giữa primary và replica, hay gặp khi replica ở vùng khác.

Đo lag:

- `Seconds_Behind_Source` trong `SHOW REPLICA STATUS`: hiệu giữa giờ hiện tại trên replica và
  timestamp gốc của event đang được áp. Tức là nó chỉ đo applier đuổi theo receiver.
  - ⚠️ Mạng chậm thì receiver tụt xa primary, còn applier đã áp hết relay log, nên chỉ số hiện **0**
    trong khi replica thực tế trễ. Tài liệu MySQL viết thẳng: cột này "chỉ hữu ích với mạng nhanh".
  - ⚠️ Là `NULL` khi applier không chạy, hoặc khi đã áp hết relay log mà receiver đã dừng. Code giám
    sát phải coi `NULL` là lỗi, không phải "không trễ".
  - Không có event nào đang áp thì bằng 0; lệch đồng hồ (NTP chỉnh giờ) cũng làm số liệu sai.
  - Chỉ có độ phân giải giây.
- *Heartbeat table* (`pt-heartbeat`): một process ghi timestamp hiện tại vào một bảng trên primary mỗi
  giây; trên replica, lag bằng giờ hiện tại trừ timestamp đọc được. Đo đúng đầu cuối từ primary tới
  replica, gồm cả mạng. gh-ost dùng đúng cách này để điều tốc.
- So GTID: `GTID_SUBTRACT(<gtid_executed của primary>, <gtid_executed của replica>)` là các
  transaction replica còn thiếu.

#### Read-your-writes

*Read-your-writes* (đọc được cái mình vừa ghi) là đảm bảo rằng sau khi user ghi, chính user đó luôn
thấy thay đổi của mình (người khác có thể thấy muộn hơn). Kleppmann (DDIA ch.5) xếp nó vào nhóm vấn
đề của replication lag.

Triệu chứng: user sửa tên, request `POST` ghi vào primary, redirect về trang hồ sơ, request `GET` đọc
từ một replica đang trễ 2 giây, và user thấy tên cũ.

| Bước | Request 1 (POST) | Request 2 (GET, ngay sau) | Kết quả |
|---|---|---|---|
| 1 | `UPDATE users SET name='Bình' WHERE id=7` trên primary | | Primary: Bình |
| 2 | Commit, redirect | | Replica vẫn là An (lag 2s) |
| 3 | | `SELECT name FROM users WHERE id=7` trên replica | User thấy **An** |
| 4 | | (2 giây sau) | Replica: Bình |

Laravel cấu hình read/write tách nhau trong `config/database.php`:

```php
'mysql' => [
    'driver' => 'mysql',
    'read'  => ['host' => [env('DB_READ_HOST_1'), env('DB_READ_HOST_2'), env('DB_READ_HOST_3')]],
    'write' => ['host' => [env('DB_WRITE_HOST')]],
    'sticky' => true,
    // ... database, username, password dùng chung
],
```

Mỗi request, Laravel chọn ngẫu nhiên một host trong `read`. `SELECT` đi qua read connection, còn
`INSERT/UPDATE/DELETE` qua write connection. Theo source của `Connection::getReadPdo()`, read vẫn đi
vào **primary** trong ba trường hợp: đang trong transaction; đã gọi `useWriteConnectionWhenReading()`;
hoặc `sticky` bật và connection đã ghi gì đó từ đầu request.

Các cách xử lý, từ đơn giản tới chặt:

1. **`sticky`**: chỉ có tác dụng **trong cùng một request**. Không giải quyết được ví dụ trên, vì GET
   là một request khác.
2. **Ép đọc primary ở chỗ cần**: `User::onWriteConnection()->find($id)` với Eloquent,
   `DB::table('users')->useWritePdo()->...` với query builder. Hợp với dữ liệu "của chính mình": trang
   hồ sơ, giỏ hàng, số dư của user đang đăng nhập.
3. **Đọc primary trong một khoảng sau khi user ghi**: lưu mốc thời gian vào session, và trong N giây
   sau đó mọi read của user này đi primary. N chọn lớn hơn lag p99, và lag vượt N thì phải có cảnh báo.
4. **Chờ theo GTID**: sau khi ghi, lấy `@@GLOBAL.gtid_executed` từ primary lưu vào session. Request
   sau hỏi replica "đã có tập này chưa" bằng `GTID_SUBSET(tập, @@GLOBAL.gtid_executed)`. Có thì đọc
   replica, chưa thì đọc primary. Chính xác hơn cách 3 vì không phụ thuộc vào ước lượng lag. Biến thể:
   `SELECT WAIT_FOR_EXECUTED_GTID_SET(tập, 1)` chờ tối đa 1 giây, trả 0 là đã bắt kịp, 1 là hết giờ;
   cách này làm request chậm đi nên thường chỉ dùng cho job, không dùng cho web.

Middleware kết hợp cách 3 và 4:

```php
<?php
declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Symfony\Component\HttpFoundation\Response;

final class ReadYourWrites
{
    private const WINDOW_SECONDS = 5;

    public function handle(Request $request, Closure $next): Response
    {
        $session = $request->session();
        $gtid = $session->get('db.last_gtid');
        $writtenAt = $session->get('db.last_write_at');

        if (is_string($gtid) && is_int($writtenAt) && time() - $writtenAt < self::WINDOW_SECONDS) {
            // Hỏi replica (read connection) xem đã áp tới GTID của lần ghi gần nhất chưa
            $caughtUp = DB::selectOne(
                'SELECT GTID_SUBSET(?, @@GLOBAL.gtid_executed) AS ok',
                [$gtid],
            )->ok ?? 0;

            if ((int) $caughtUp !== 1) {
                DB::connection()->useWriteConnectionWhenReading();   // cả request này đọc primary
            }
        }

        $response = $next($request);

        if (DB::connection()->hasModifiedRecords()) {
            // Request này có ghi: nhớ vị trí của primary. gtid_executed là tập của CẢ server nên là
            // tập cha của lần ghi này; chờ theo nó có thể chờ dư một chút, nhưng không bao giờ thiếu
            $row = DB::connection()->selectOne('SELECT @@GLOBAL.gtid_executed AS g', [], false);
            $session->put('db.last_gtid', (string) $row->g);
            $session->put('db.last_write_at', time());
        }

        return $response;
    }
}
```

(Tham số thứ ba `false` của `selectOne` nghĩa là không dùng read PDO, tức đọc từ primary.)

⚠️ Các bẫy:

- **Đọc để ghi không bao giờ đi replica**: kiểm tra số dư rồi trừ, kiểm tra tồn kho rồi đặt hàng,
  kiểm tra email đã tồn tại chưa. Đọc dữ liệu cũ ở đây là sai tiền, sai kho. Đặt những luồng này trong
  `DB::transaction()` (read tự đi primary) kèm lock phù hợp (module 2.6).
- **Queue job**: job chạy trong process khác, `sticky` và session đều không có tác dụng. Job được
  dispatch sau khi tạo đơn có thể đọc replica và không thấy đơn. Dùng `afterCommit` và đọc bằng
  `onWriteConnection()`, hoặc truyền sẵn dữ liệu cần thiết vào job.
- **Process sống lâu** (queue worker, Octane): cờ "đã ghi" nằm trên object connection, sống qua nhiều
  job hoặc request nếu không được reset. Có thể gọi `DB::forgetRecordModificationState()` ở đầu mỗi
  đơn vị việc; kiểm tra framework của bạn đã tự làm chưa.
- **Nhiều thiết bị**: user sửa trên điện thoại, xem trên laptop. Mốc lưu trong session hay cookie không
  đi theo; cần lưu ở phía server theo user id nếu yêu cầu chặt.
- Chấp nhận *eventual consistency* ở những màn hình không quan trọng (bảng tin, thống kê) để giữ tải
  đọc trên replica; không phải chỗ nào cũng cần read-your-writes.

#### Failover

*Failover* là chuyển vai trò primary sang một replica khi primary hỏng. Các bước, dù làm bằng tay hay
bằng tool:

1. **Phát hiện** primary hỏng. Khó hơn tưởng: primary chậm hay mạng chập chờn trông giống primary
   chết. Phát hiện quá nhạy thì failover oan; quá chậm thì downtime dài.
2. **Chặn primary cũ** (*fencing*): chắc chắn nó không nhận ghi nữa, bằng cách tắt hẳn máy (STONITH:
   "shoot the other node in the head"), rút khỏi proxy, hoặc bật `super_read_only`.
3. **Chọn replica mới nhất**: so `Executed_Gtid_Set` của các replica. Với semi-sync, replica đã xác
   nhận là ứng viên an toàn.
4. **Cho replica đó áp nốt relay log**, rồi tắt `read_only`/`super_read_only`.
5. **Trỏ các replica còn lại** sang primary mới: với GTID chỉ cần `CHANGE REPLICATION SOURCE TO
   SOURCE_HOST='db-2', SOURCE_AUTO_POSITION=1`.
6. **Trỏ app** sang primary mới, qua DNS, proxy (ProxySQL, MySQL Router) hoặc VIP (IP ảo chuyển được
   giữa các máy).

Tool thường dùng: Orchestrator (tự phát hiện, tự chọn và nâng replica), MySQL InnoDB Cluster với MySQL
Router, hoặc dịch vụ managed (RDS, Cloud SQL, Aurora) tự lo toàn bộ.

⚠️ Các bẫy khi failover:

- **Mất dữ liệu với async**: các transaction cuối chưa sang replica nào sẽ mất. Muốn không mất, dùng
  semi-sync `AFTER_SYNC` và theo dõi việc nó rơi về async.
- ***Split brain***: primary cũ không thật sự chết (chỉ mất mạng tạm thời), sống lại và vẫn nhận ghi từ
  một phần app còn trỏ vào nó. Hai primary cùng nhận ghi, dữ liệu phân nhánh và rất khó gộp lại. Đó là
  lý do bước fencing phải đi trước bước nâng replica ([14-distributed-systems.md](../14-distributed-systems.md)).
- ***Errant transaction***: ai đó chạy lệnh ghi trực tiếp trên replica (sửa tay, script chạy nhầm
  host). Transaction đó mang UUID của replica. Khi replica được nâng lên, các replica khác thấy GTID lạ
  và cố áp nó, hoặc gặp lỗi vì binlog đã bị xoá. Phòng bằng `super_read_only=ON` trên mọi replica; kiểm
  tra bằng `GTID_SUBTRACT(<gtid_executed của replica>, <gtid_executed của primary>)` phải rỗng.
- **Phía app**:
  - Connection đang mở bị đứt giữa chừng: lỗi `2006 MySQL server has gone away` hoặc `2013 Lost
    connection`. Laravel tự kết nối lại khi mất kết nối nếu **không** ở trong transaction; trong
    transaction thì ném lỗi, app phải retry cả transaction.
  - DNS TTL: TTL dài thì app còn phân giải ra IP cũ nhiều phút. PHP-FPM còn có persistent connection
    hoặc queue worker sống lâu, giữ nguyên connection tới node cũ cho tới khi bị đứt.
  - Thao tác ghi không idempotent (trừ tiền, gửi email) mà retry sau lỗi kết nối có thể chạy hai lần,
    vì không biết lần đầu đã commit hay chưa.

**Tóm tắt nhanh**
- Binlog trên primary, receiver ghi relay log, applier (nhiều worker) áp. Replica scale đọc, không
  scale ghi.
- GTID `uuid:số` cho mỗi transaction: replica tự định vị khi đổi primary, không áp trùng, so được ai
  mới nhất.
- Semi-sync `AFTER_SYNC`: commit thành công thì đã nằm trên đĩa một replica, nhưng chưa chắc đã áp; quá
  timeout 10 giây thì rơi về async.
- `Seconds_Behind_Source` có thể bằng 0 hoặc NULL một cách đánh lừa; đo lag bằng heartbeat.
- Read-your-writes trong Laravel: `sticky` chỉ trong một request; qua request thì ép primary trong N
  giây hoặc so GTID; luồng đọc để ghi luôn ở primary trong transaction.
- Failover: fencing trước, chọn replica mới nhất theo GTID, chống split brain và errant transaction.

**Nguồn**: [MySQL: Replication](https://dev.mysql.com/doc/refman/8.4/en/replication.html) ·
[Replication Threads](https://dev.mysql.com/doc/refman/8.4/en/replication-threads.html) ·
[GTID Concepts](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids-concepts.html) ·
[GTID Functions](https://dev.mysql.com/doc/refman/8.4/en/gtid-functions.html) ·
[Semisynchronous Replication](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html) ·
[SHOW REPLICA STATUS](https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html) ·
[MySQL 8.4.0 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/8.4/en/news-8-4-0.html) ·
[Laravel: Read and Write Connections](https://laravel.com/docs/database#read-and-write-connections) ·
*Designing Data-Intensive Applications* ch.5


---

### 3.5 Backup, PITR, RPO/RTO

Module này trả lời: có những cách backup MySQL nào, khôi phục dữ liệu về đúng một thời điểm (ví dụ
ngay trước câu `DELETE` quên `WHERE`) cụ thể gồm những lệnh gì, và mất bao nhiêu dữ liệu, bao nhiêu
thời gian.

#### Hai loại backup

*Logical backup* xuất dữ liệu ra dạng văn bản, thường là các câu `CREATE TABLE` và `INSERT`. Muốn
restore thì chạy lại toàn bộ các câu SQL đó.

- `mysqldump` là công cụ đi kèm MySQL. Với bảng InnoDB, dùng `--single-transaction`: mysqldump mở
  một transaction ở mức Repeatable Read bằng `START TRANSACTION WITH CONSISTENT SNAPSHOT`, rồi đọc
  mọi bảng qua cùng một read view (module 3.1). Kết quả là một snapshot nhất quán mà không phải khoá
  bảng, app vẫn ghi bình thường trong lúc dump.
- `mydumper`/`myloader` (mã nguồn mở) và dump utility của MySQL Shell (`util.dumpInstance()`) chạy
  song song nhiều luồng, cả lúc dump lẫn lúc load, nên nhanh hơn mysqldump nhiều lần với DB lớn.
- Ưu điểm: file đọc được bằng mắt, chọn được từng DB hay từng bảng, restore sang phiên bản MySQL
  khác hoặc máy khác kiến trúc được.
- Nhược điểm: restore phải chạy lại từng `INSERT` và dựng lại mọi index. DB vài trăm GB có thể mất
  nhiều giờ tới cả ngày để load.

⚠️ `--single-transaction` chỉ nhất quán với bảng InnoDB. Nếu trong lúc dump có ai chạy DDL
(`ALTER TABLE`, `DROP`, `RENAME`, `TRUNCATE`) trên bảng đang dump, snapshot không còn đáng tin: bảng
có thể ra rỗng hoặc lỗi. Lên lịch dump tránh giờ chạy migration.

*Physical backup* copy thẳng các file dữ liệu của InnoDB.

- Percona XtraBackup (miễn phí) và MySQL Enterprise Backup (trả phí) copy file `.ibd` trong khi
  server vẫn chạy, đồng thời ghi lại phần redo log phát sinh trong lúc copy. Bước `--prepare` sau
  đó áp redo log lên bản copy, giống crash recovery (module 3.1), để ra một bản nhất quán.
- Snapshot ổ đĩa (EBS snapshot, LVM snapshot) và snapshot của dịch vụ managed (RDS, Cloud SQL)
  cũng là physical backup.
- Clone plugin (có từ MySQL 8.0.17) copy dữ liệu từ một server sang server khác qua mạng, hay dùng để
  dựng replica mới.
- Ưu điểm: restore gần như chỉ là copy file về và khởi động, nhanh hơn logical nhiều lần với DB lớn.
- Nhược điểm: gắn với phiên bản MySQL và cấu hình (page size, định dạng file); không chọn lẻ một
  bảng dễ dàng; XtraBackup phải dùng bản khớp với dòng MySQL (MySQL 8.4 cần XtraBackup 8.4).

| | Logical (`mysqldump`, mydumper) | Physical (XtraBackup, snapshot) |
|---|---|---|
| Tốc độ backup | Chậm với DB lớn | Nhanh |
| Tốc độ restore | Rất chậm (chạy lại SQL, dựng index) | Nhanh (copy file) |
| Chọn từng bảng | Dễ | Khó |
| Chuyển phiên bản, kiến trúc | Được | Không, hoặc hạn chế |
| Kích thước | Nén tốt | Bằng dữ liệu thật, có thể incremental |
| Dùng cho | DB nhỏ, lấy lẻ một bảng, chuyển phiên bản | Backup chính cho DB lớn, dựng replica |

Thực tế nhiều đội dùng cả hai: physical backup hằng ngày làm nền cho PITR, logical dump định kỳ để
có thể lấy lẻ một bảng hoặc chuyển phiên bản.

Mỗi bản full backup phải ghi lại **toạ độ binlog** ứng với thời điểm snapshot, vì PITR bắt đầu replay
từ đúng điểm đó:

- `mysqldump --source-data=2` ghi toạ độ vào đầu file dưới dạng comment
  (`-- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='binlog.001002', SOURCE_LOG_POS=27284;`). Tên cũ
  là `--master-data`, đã deprecated. Để lấy toạ độ chính xác, mysqldump giữ global read lock trong
  chốc lát lúc bắt đầu (`FLUSH TABLES WITH READ LOCK`), nên tránh chạy khi đang có query rất dài.
- Khi bật GTID, dump ghi thêm `SET @@GLOBAL.GTID_PURGED=...` để server được restore biết những
  transaction nào đã có.
- XtraBackup ghi toạ độ vào file `xtrabackup_binlog_info`.

⚠️ Tài liệu MySQL nhắc: đừng tin vị trí binlog mà InnoDB in ra sau khi restore; hãy dùng toạ độ do
công cụ backup ghi lại.

#### Binlog: nguyên liệu của PITR

*Binary log* (binlog) ghi lại mọi thay đổi dữ liệu đã commit theo thứ tự (module 3.4 dùng nó cho
replication). Các giá trị mặc định cần biết ở MySQL 8.4:

| Biến | Mặc định | Ý nghĩa với backup |
|---|---|---|
| `log_bin` | Bật (từ 8.0) | Không có binlog thì không PITR được |
| `binlog_format` | `ROW` | Ghi giá trị từng dòng trước/sau thay đổi, nên đảo ngược được |
| `binlog_row_image` | `FULL` | Ghi đủ mọi cột, cần cho các tool flashback |
| `binlog_expire_logs_seconds` | 2592000 (30 ngày) | Binlog cũ hơn bị xoá; cửa sổ PITR không dài hơn mức này nếu không copy ra ngoài |
| `sync_binlog` | 1 | fsync binlog mỗi lần commit, crash không mất transaction đã commit |
| `gtid_mode` | `OFF` | Bật GTID giúp chọn/bỏ transaction theo ID thay vì byte offset |

Binlog chỉ có ích nếu nó sống sót khi máy chủ chết, nên phải copy liên tục ra chỗ khác.
`mysqlbinlog` làm được việc này bằng cách đóng vai một replica:

```bash
# Chạy trên máy backup, kéo binlog từ primary về dạng nhị phân gốc, không dừng
mysqlbinlog --read-from-remote-server --host=db-primary --user=binlog_backup --password \
  --raw --stop-never --connection-server-id=9001 \
  --result-file=/backup/binlog/ binlog.000130
```

- `--raw` ghi file nhị phân y hệt file gốc; `--stop-never` giữ kết nối và nhận event mới liên tục.
- `--connection-server-id` phải khác server id của mọi replica (mặc định là 1, dễ trùng).
- ⚠️ mysqlbinlog **không tự kết nối lại** khi mất mạng hoặc primary restart; phải bọc trong
  systemd hoặc một vòng lặp script có cảnh báo.
- ⚠️ Binlog đã mã hoá trên server khi copy về bằng cách này sẽ ở dạng **không mã hoá**; phải tự mã hoá
  nơi lưu.

Dịch vụ managed (RDS, Aurora, Cloud SQL) làm sẵn phần này và cho PITR theo giây trong khoảng
retention đã cấu hình.

#### Khôi phục tới một thời điểm

*PITR* (point-in-time recovery) = restore full backup gần nhất trước sự cố, rồi replay binlog từ toạ
độ của backup tới **ngay trước** event gây hại.

```
  full backup 02:00            DELETE nhầm 14:03:17        bây giờ 14:20
  (binlog.001002:27284)                 |                       |
  ──────●───────────────────────────────✖───────────────────────●──> thời gian
        |<──── replay binlog ──────────>|  bỏ event này  |<── replay tiếp (tuỳ chọn) ──>|
```

Tình huống: 14:05 có người báo "bảng `orders` mất sạch". Điều tra ra lúc 14:03 ai đó chạy
`DELETE FROM orders` quên `WHERE`. Quy trình từng bước:

1. **Cầm máu**. Chặn thêm thiệt hại: tạm dừng job/tính năng đang ghi vào bảng đó, hoặc bật chế độ
   bảo trì. Nếu có delayed replica (xem phần sau), **dừng ngay** SQL thread của nó trước khi nó áp
   câu `DELETE`: `STOP REPLICA SQL_THREAD;`.
2. **Giữ lại bằng chứng**. Không restart, không restore đè lên primary. Chạy `FLUSH BINARY LOGS;` để
   đóng file binlog hiện tại, và đảm bảo các file binlog từ lúc backup tới giờ đã được copy ra ngoài.
3. **Dựng một instance tạm** (máy khác hoặc container) và restore bản full backup lúc 02:00 lên đó.
   Restore lên instance riêng để primary vẫn phục vụ các bảng khác, và để có thể thử lại nếu sai.

   ```bash
   mysql -h restore-tmp -u root -p < full_0200.sql          # logical
   # hoặc: xtrabackup --prepare, copy về datadir, khởi động mysqld   # physical
   ```

4. **Lấy toạ độ bắt đầu** từ backup:

   ```bash
   head -50 full_0200.sql | grep 'SOURCE_LOG'
   # -- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='binlog.001002', SOURCE_LOG_POS=27284;
   ```

5. **Tìm chính xác vị trí của câu `DELETE`**. Dùng khoảng thời gian để thu hẹp, rồi đọc vị trí byte.
   Với binlog dạng ROW, phải thêm `--base64-output=DECODE-ROWS -v` mới đọc được nội dung dòng:

   ```bash
   mysqlbinlog --start-datetime="2026-09-27 14:02:00" --stop-datetime="2026-09-27 14:05:00" \
     --base64-output=DECODE-ROWS --verbose /backup/binlog/binlog.001004 \
     | grep -n -B 12 'DELETE FROM `shop`.`orders`' | head -40
   ```

   Output có dạng (output minh hoạ, không phải chạy thật):

   ```
   # at 51155
   #260927 14:03:17 server id 1  end_log_pos 51234 CRC32 ...  Anonymous_GTID ...
   SET @@SESSION.GTID_NEXT= 'ANONYMOUS'/*!*/;
   # at 51234
   #260927 14:03:17 server id 1  end_log_pos 51313 CRC32 ...  Query  thread_id=812 ...
   BEGIN
   # at 51313
   #260927 14:03:17 server id 1  end_log_pos 51377 ...  Table_map: `shop`.`orders` mapped to number 93
   # at 51377
   #260927 14:03:17 server id 1  end_log_pos 59605 ...  Delete_rows: table id 93
   ### DELETE FROM `shop`.`orders`
   ### WHERE
   ###   @1=1001
   ...
   ```

   Transaction chứa câu `DELETE` bắt đầu ở `# at 51155`: event GTID (`Anonymous_GTID` khi tắt GTID,
   `Gtid` khi bật) đứng ngay trước `BEGIN`, và thuộc về transaction đó. Ghi lại hai số: vị trí bắt
   đầu transaction (51155) và vị trí ngay sau `COMMIT`/`Xid` của nó. Với GTID thì ghi lại GTID của
   transaction đó (dòng `SET @@SESSION.GTID_NEXT= '3e11fa47-...:9121'`).

6. **Replay từ backup tới ngay trước transaction xấu**, tất cả trong **một lệnh mysqlbinlog duy
   nhất**:

   ```bash
   mysqlbinlog --start-position=27284 --stop-position=51155 \
     /backup/binlog/binlog.001002 /backup/binlog/binlog.001003 /backup/binlog/binlog.001004 \
     | mysql -h restore-tmp -u root -p
   ```

   `--start-position` áp cho file đầu tiên trong danh sách, `--stop-position` áp cho file cuối cùng.
   Khi dùng GTID, cách gọn hơn là bỏ đúng transaction đó và replay tất cả phần còn lại:

   ```bash
   mysqlbinlog --exclude-gtids='3e11fa47-71ca-11e1-9e33-c80aa9429562:9121' \
     binlog.001002 binlog.001003 binlog.001004 binlog.001005 | mysql -h restore-tmp -u root -p
   ```

   (Server restore từ backup đã có `GTID_PURGED` nên tự bỏ qua các transaction có trước backup.)
7. **Kiểm tra** trên instance tạm: `SELECT COUNT(*), MAX(created_at) FROM orders;` so với con số
   kỳ vọng, đối chiếu vài đơn cụ thể với log của app.
8. **Đưa dữ liệu về production**. Thường không thay cả DB mà chỉ lấy lại bảng bị hỏng:

   ```bash
   mysqldump -h restore-tmp --single-transaction shop orders > orders_fixed.sql
   ```

   Rồi nạp vào primary (vào bảng tạm `orders_restored` trước, đối soát, rồi đổi tên hoặc
   `INSERT ... SELECT` các dòng thiếu). Nếu từ 14:03 tới lúc chặn, app đã ghi đơn mới vào `orders`,
   phải gộp các dòng đó chứ không ghi đè mất.
9. **Hậu kiểm**: viết postmortem, thu quyền `DELETE` trực tiếp trên production, bật
   `sql_safe_updates` cho client của người vận hành (`mysql --safe-updates` từ chối `UPDATE`/`DELETE`
   không có `WHERE` dùng key hoặc `LIMIT`).

⚠️ Các cạm bẫy khi replay, đều có trong tài liệu MySQL:

- **Nhiều file binlog phải đi chung một kết nối** như bước 6. Nếu chạy `mysqlbinlog file1 | mysql`
  rồi `mysqlbinlog file2 | mysql`, một temporary table tạo ở file 1 sẽ biến mất khi kết nối đầu đóng,
  và file 2 lỗi. Cách thay thế: nối tất cả vào một file `.sql` rồi `source` một lần.
- **Chỉ dùng `--start-datetime`/`--stop-datetime` để tìm vị trí**, không dùng để giới hạn replay.
  Nhiều event cùng một giây, và dừng theo thời gian có thể bỏ sót hoặc thừa event. Replay bằng
  `--start-position`/`--stop-position` hoặc GTID.
- Nếu binlog chứa ký tự `\0`, thêm `mysql --binary-mode`.
- Binlog đã mã hoá trên server thì đọc qua server bằng `--read-from-remote-server`.

Cách nhanh hơn cho riêng một câu `DELETE`: với `binlog_format=ROW` và `binlog_row_image=FULL`, binlog
chứa toàn bộ giá trị của mọi dòng đã xoá. Các tool *flashback* (ví dụ `binlog2sql`, hoặc
`mysqlbinlog --flashback` của MariaDB) đọc đúng transaction đó và sinh ra các câu `INSERT` ngược lại.
Không cần restore full backup, RTO chỉ tính bằng phút. Đây là tool bên thứ ba, cần kiểm tra độ
tương thích với phiên bản trước khi phải dùng thật.

#### RPO, RTO và ước lượng cho tình huống 14:03

- *RPO* (Recovery Point Objective): được phép mất tối đa bao nhiêu dữ liệu, đo bằng thời gian. RPO
  15 phút nghĩa là chấp nhận mất tối đa 15 phút giao dịch cuối.
- *RTO* (Recovery Time Objective): được phép mất tối đa bao lâu từ lúc sự cố tới lúc hệ thống chạy
  lại.

Hai con số này do business quyết định (mất một giờ đơn hàng tốn bao nhiêu tiền), còn kỹ thuật chọn
kiến trúc backup để đạt được. Chi tiết về DR nằm ở [18-reliability-observability.md](../18-reliability-observability.md).

| Cách làm | RPO thực tế | RTO thực tế |
|---|---|---|
| Chỉ full backup hằng đêm | Tới 24 giờ | Thời gian restore full |
| Full backup + copy binlog theo giờ | Tới 1 giờ (nếu mất cả primary) | Restore + replay |
| Full backup + stream binlog liên tục | Vài giây | Restore + replay |
| Delayed replica 1 giờ | Gần 0 với lỗi logic phát hiện trong 1 giờ | Vài phút tới vài chục phút |
| Flashback từ binlog ROW | Gần 0 | Vài phút |

Ước lượng cho sự cố 14:03, với full backup 02:00 và binlog stream liên tục:

- **RPO**: primary vẫn sống nên binlog tới 14:05 còn nguyên. Dữ liệu trước 14:03:17 lấy lại đủ.
  Phần có rủi ro là các ghi sau 14:03 vào bảng `orders` (đơn mới đặt, hoặc update lên dòng đã bị
  xoá bị "trượt" vì không còn dòng để update). RPO thực tế gần 0 nếu gộp đúng, còn nếu chỉ restore về
  14:03 thì mất khoảng 2 phút ghi của bảng đó.
- **RTO**: thời gian dựng instance + restore backup (với DB lớn, restore logical thường lâu hơn
  physical nhiều lần) + replay 12 giờ binlog (tuỳ lưu lượng ghi) + đối soát và đưa bảng về. Đây là lý do nên đo thời gian thật qua diễn tập, không đoán.

#### Những điều hay bị quên

- ⚠️ **Replica không phải backup.** `DELETE` hay `DROP TABLE` chạy trên primary được replicate sang
  mọi replica gần như ngay lập tức (chỉ chậm bằng độ trễ replication). Replica bảo vệ khỏi hỏng phần cứng, không bảo vệ khỏi lỗi logic
  của người và code.
- **Delayed replica** là ngoại lệ: một replica cố ý áp chậm.

  ```sql
  STOP REPLICA;
  CHANGE REPLICATION SOURCE TO SOURCE_DELAY = 3600;   -- áp event sau 1 giờ
  START REPLICA;
  -- Khi có sự cố: dừng SQL thread, rồi cho chạy tới ngay trước transaction xấu
  STOP REPLICA SQL_THREAD;
  START REPLICA SQL_THREAD UNTIL SQL_BEFORE_GTIDS = '3e11fa47-71ca-11e1-9e33-c80aa9429562:9121';
  ```

  Chỉ cứu được nếu phát hiện sự cố trong khoảng delay.
- ⚠️ **Backup chưa từng restore thử coi như chưa có.** Lỗi hay gặp: file dump bị cắt ngang vì hết
  đĩa, thiếu `--routines --events --triggers`, mất khoá giải mã, binlog có lỗ vì mysqlbinlog đã chết
  một tuần mà không ai biết. Diễn tập định kỳ, tự động restore sang một instance và chạy truy vấn
  kiểm tra, ghi lại thời gian để biết RTO thật.
- **Cô lập backup**: mã hoá, dùng account hoặc region khác với production, quyền xoá tách riêng
  (object lock, bản bất biến). Kẻ tấn công ransomware có quyền production thường xoá backup đầu tiên.
- **Theo dõi binlog stream**: cảnh báo khi file binlog mới nhất ở chỗ backup cũ hơn vài phút.
- **Retention**: cửa sổ PITR = từ full backup cũ nhất còn giữ tới binlog mới nhất. Giữ binlog ở nơi
  backup lâu hơn `binlog_expire_logs_seconds` trên server.

**Tóm tắt nhanh**
- Logical dễ chọn lẻ và chuyển phiên bản nhưng restore chậm; physical restore nhanh, là nền cho DB lớn.
- PITR = full backup có toạ độ binlog + binlog liên tục ở nơi khác; replay tới ngay trước transaction
  xấu bằng position hoặc GTID, không dừng theo datetime.
- Luôn restore ra instance tạm, rồi mới đưa bảng về production và gộp dữ liệu ghi sau sự cố.
- Nhiều file binlog replay trong một kết nối mysqlbinlog; mysqlbinlog stream không tự reconnect.
- Replica không phải backup; delayed replica và flashback từ binlog ROW cho RTO ngắn nhất với lỗi
  logic.
- Backup chưa restore thử là chưa có backup; RPO/RTO phải đo bằng diễn tập.

**Nguồn**: [MySQL: Point-in-Time Recovery](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery.html) ·
[MySQL: PITR Using Binary Log](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-binlog.html) ·
[MySQL: PITR Using Event Positions](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-positions.html) ·
[MySQL: Using mysqlbinlog to Back Up Binary Log Files](https://dev.mysql.com/doc/refman/8.4/en/mysqlbinlog-backup.html)


---

### 3.6 Scale: partitioning, sharding, archiving

Module này trả lời: khi một DB MySQL bắt đầu quá tải thì nên thử những gì theo thứ tự nào,
partitioning và sharding khác nhau ra sao, và các công ty đã shard thật (Notion, Figma) làm thế nào.

Một lưu ý thuật ngữ: sách DDIA dùng chữ *partitioning* cho việc chia dữ liệu ra nhiều máy, tức cái mà
cộng đồng MySQL gọi là *sharding*. Trong module này, "partitioning" là tính năng chia bảng **trong
một server MySQL**, còn "sharding" là chia ra **nhiều server**.

#### Thứ tự nên thử trước khi shard

Sharding làm mọi thứ về sau khó hơn (query, migration, backup, debug), nên nó là lựa chọn cuối cùng.
Mỗi bước dưới đây rẻ hơn bước sau và nên làm trước:

1. **Tối ưu query và index** (module 2.2, 2.3). Một query full scan chạy 1.000 lần mỗi giây có thể
   chiếm phần lớn CPU; thêm đúng index là giảm hàng chục lần tải. Luôn bắt đầu bằng slow query log
   và `performance_schema` để biết tải đến từ đâu.
2. **Cache** dữ liệu đọc nhiều, ít đổi ([11-cache.md](../11-cache.md)).
3. **Read replica** gánh tải đọc (module 3.4). Chú ý replication lag với các luồng "vừa ghi xong đọc
   lại".
4. **Scale dọc**: máy lớn hơn. Hiện nay một máy có hàng trăm core, vài TB RAM, NVMe hàng trăm nghìn
   IOPS; nhiều hệ lớn chạy trên một primary lâu hơn người ta tưởng.
5. **Tách DB theo chức năng** (*vertical partitioning*): bảng của billing sang một cluster, bảng của
   chat sang cluster khác. Không phải viết lại query trong mỗi miền; chỉ mất join và transaction giữa
   các miền.
6. **Partition và archive** dữ liệu cũ để bảng nóng nhỏ lại.
7. **Shard** (*horizontal sharding*).

Dấu hiệu thật sự cần shard: **tải ghi** hoặc **kích thước dữ liệu** của một nhóm bảng vượt quá một
máy lớn nhất có thể mua, và không tách tiếp theo chức năng được nữa. Replica không giúp được tải ghi,
vì mọi replica đều phải áp toàn bộ lượng ghi.

Ví dụ lập luận "chưa shard" cho hệ 2 TB, 5.000 QPS:

- 2 TB vừa trên một máy; working set (dữ liệu nóng) thường nhỏ hơn nhiều và vừa buffer pool của một
  máy vài trăm GB RAM.
- 5.000 QPS, phần lớn là đọc, là mức một primary cỡ vừa cộng vài replica xử lý tốt nếu query có index.
- Việc cần làm: đo tỉ lệ đọc/ghi, tìm top query theo tổng thời gian, archive dữ liệu cũ, và theo dõi
  tốc độ tăng trưởng để biết còn bao nhiêu tháng runway. Chỉ lên kế hoạch shard khi dự báo cho thấy
  sẽ chạm trần trong 12 đến 18 tháng.
- Vẫn nên chuẩn bị rẻ từ sớm: mọi bảng của tenant đều có cột `tenant_id`, query luôn lọc theo nó. Bài
  học của Notion (phía dưới) là thiếu cột này khiến migration khó hơn rất nhiều.

#### Partitioning (vẫn trong một DB)

*Partitioning* chia một bảng logic thành nhiều phần vật lý (với InnoDB, mỗi partition là một file
`.ibd` riêng), dựa trên giá trị của một biểu thức gọi là *partitioning key*. App vẫn query `orders`
như bình thường; MySQL tự biết dòng nằm ở partition nào.

Bốn kiểu chính:

| Kiểu | Chia theo | Ví dụ dùng |
|---|---|---|
| `RANGE` / `RANGE COLUMNS` | Khoảng giá trị liên tiếp | Theo tháng của `created_at` |
| `LIST` / `LIST COLUMNS` | Danh sách giá trị rời | Theo `region` |
| `HASH` | Biểu thức số nguyên mod số partition | Chia đều theo `user_id` |
| `KEY` | Như HASH nhưng MySQL tự băm, nhận nhiều kiểu cột | Chia đều theo cột chuỗi |

Biểu thức của `RANGE`, `LIST`, `HASH` phải ra số nguyên. `RANGE COLUMNS` và `LIST COLUMNS` cho dùng
trực tiếp cột chuỗi, `DATE`, `DATETIME`, nên gọn hơn khi chia theo ngày.

Ví dụ bảng event chia theo tháng:

```sql
CREATE TABLE events (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  tenant_id  BIGINT UNSIGNED NOT NULL,
  type       VARCHAR(50) NOT NULL,
  payload    JSON,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id, created_at),               -- bắt buộc chứa cột partition
  KEY idx_tenant_time (tenant_id, created_at)
)
PARTITION BY RANGE COLUMNS (created_at) (
  PARTITION p2026_07 VALUES LESS THAN ('2026-08-01'),
  PARTITION p2026_08 VALUES LESS THAN ('2026-09-01'),
  PARTITION p2026_09 VALUES LESS THAN ('2026-10-01'),
  PARTITION pmax     VALUES LESS THAN (MAXVALUE)
);
```

*Partition pruning*: optimizer so điều kiện `WHERE` với định nghĩa partition và bỏ qua các partition
chắc chắn không có dòng khớp. Xem bằng cột `partitions` của `EXPLAIN`:

```sql
EXPLAIN SELECT COUNT(*) FROM events
WHERE created_at >= '2026-09-01' AND created_at < '2026-09-15';
-- partitions: p2026_09        (chỉ đọc một partition)

EXPLAIN SELECT * FROM events WHERE tenant_id = 42;
-- partitions: p2026_07,p2026_08,p2026_09,pmax   (không có điều kiện trên created_at: đọc tất cả)
```

Pruning hoạt động với `=`, `IN`, `<`, `>`, `BETWEEN`, và với biểu thức dùng `YEAR()`, `TO_DAYS()`,
`TO_SECONDS()`. Với `HASH`/`KEY`, một range chỉ được prune khi nó đủ ngắn để MySQL đổi thành danh sách
`IN` (số giá trị ít hơn số partition) và cột là số nguyên.

Lợi ích lớn nhất trong thực tế không phải tốc độ đọc mà là **quản lý vòng đời dữ liệu**:

```sql
-- Xoá cả tháng 7: gần như tức thì, không sinh undo log cho từng dòng, không làm replica trễ
ALTER TABLE events DROP PARTITION p2026_07;
-- Giữ cấu trúc, xoá dữ liệu:
ALTER TABLE events TRUNCATE PARTITION p2026_08;
-- Thêm tháng mới: tách pmax (partition rỗng thì rất nhanh)
ALTER TABLE events REORGANIZE PARTITION pmax INTO (
  PARTITION p2026_10 VALUES LESS THAN ('2026-11-01'),
  PARTITION pmax     VALUES LESS THAN (MAXVALUE)
);
-- Đẩy một partition ra thành bảng thường để archive (bảng đích cùng cấu trúc, không partition)
CREATE TABLE events_2026_08 LIKE events;
ALTER TABLE events_2026_08 REMOVE PARTITIONING;
ALTER TABLE events EXCHANGE PARTITION p2026_08 WITH TABLE events_2026_08;
```

So sánh: `DELETE FROM events WHERE created_at < '2026-08-01'` trên 100 triệu dòng phải ghi undo và
binlog cho từng dòng, giữ lock lâu, và làm replica trễ hàng giờ. `DROP PARTITION` chỉ xoá một file.

Việc thêm partition tháng mới phải chạy định kỳ (cron, scheduler của Laravel). ⚠️ Quên thêm thì dữ
liệu mới dồn vào `pmax`, và lúc tách `pmax` đã có dữ liệu sẽ phải copy dòng, rất chậm. Laravel Schema
Builder không có API cho partition, dùng `DB::statement()` với câu SQL thô.

Giới hạn cần nhớ (MySQL 8.4):

- ⚠️ **Mọi unique key, kể cả primary key, phải chứa mọi cột dùng trong biểu thức partition.** Lý do:
  mỗi partition có index riêng, MySQL chỉ kiểm tra unique trong phạm vi một partition. Nếu cột partition
  nằm trong key thì hai dòng trùng key chắc chắn rơi vào cùng partition, nên kiểm tra cục bộ là đủ. Hệ
  quả: `PRIMARY KEY (id)` phải thành `(id, created_at)`, và **không thể** có `UNIQUE (email)` trên bảng
  partition theo `created_at`.

  ```sql
  CREATE TABLE t (id INT NOT NULL, created_at DATE NOT NULL, PRIMARY KEY (id))
  PARTITION BY RANGE COLUMNS (created_at) (PARTITION p0 VALUES LESS THAN (MAXVALUE));
  -- ERROR 1503: A PRIMARY KEY must include all columns in the table's partitioning function
  ```

- ⚠️ **Không có foreign key**: bảng InnoDB đã partition không được có khoá ngoại, và cũng không bảng
  nào được có khoá ngoại trỏ tới nó.
- Tối đa 8192 partition mỗi bảng (tính cả subpartition). Tài liệu MySQL khuyên cẩn thận khi vượt quá
  vài trăm, vì mỗi partition là một file phải mở, cần `open_files_limit` đủ lớn.
- Không hỗ trợ `FULLTEXT` index, cột spatial, temporary table.
- Sau khi `ADD COLUMN ... ALGORITHM=INSTANT`, không `EXCHANGE PARTITION` được nữa.
- ⚠️ Query không lọc theo cột partition phải quét mọi partition, mỗi partition một lần đi qua cây
  index riêng. Với truy vấn theo secondary key (như `tenant_id = 42` ở trên), bảng partition có thể
  **chậm hơn** bảng thường. Partition không phải cách tăng tốc query chung chung.

Khi nào partition: bảng rất lớn, có một cột thời gian mà hầu hết query và việc xoá đều theo nó (log,
event, lịch sử giao dịch). Khi nào không: bảng cần unique trên cột khác, cần foreign key, hoặc query
chủ yếu theo cột khác.

#### Sharding (nhiều DB)

*Sharding* chia các dòng của cùng một bảng ra nhiều server MySQL độc lập. Mỗi server (hoặc mỗi cụm
primary + replica) giữ một phần gọi là *shard*. Khác với replica, mỗi shard nhận một phần tải ghi, nên
đây là cách duy nhất vượt trần ghi của một máy.

**Shard key** là cột quyết định dòng nằm ở shard nào. Tiêu chí chọn:

1. **Phần lớn query có chứa key đó**, để mỗi request chỉ chạm một shard. Với SaaS multi-tenant,
   đó thường là `tenant_id` (hay `workspace_id`, `org_id`): mọi thứ của một khách hàng nằm chung một
   shard, join và transaction trong một tenant vẫn là join và transaction bình thường.
2. **Tải chia đều**. Nhiều giá trị khác nhau, không có giá trị nào chiếm phần quá lớn.
3. **Không đổi theo thời gian**. Đổi shard key của một dòng nghĩa là chuyển dòng sang shard khác.

- ⚠️ Shard theo thời gian tạo (hay theo id tăng dần theo kiểu range) làm mọi ghi mới dồn vào shard mới
  nhất (*hot spot*). DDIA gọi đây là nhược điểm chính của chia theo khoảng key; chia theo hash của key
  khắc phục được, đổi lại mất khả năng range scan theo key.
- ⚠️ Chọn sai shard key rất khó sửa: đổi key là di chuyển gần như toàn bộ dữ liệu.

**Tenant rất lớn** (*whale tenant*): một khách hàng chiếm 20% tải thì shard chứa nó quá tải dù hash
đều. Các cách xử lý:

- Dùng *directory* (bảng tra) thay cho hash thuần, để đặt tenant lớn lên một shard riêng, máy mạnh
  hơn.
- Chia tenant lớn bằng khoá phụ: shard key thành `(tenant_id, project_id)` hoặc hash của
  `(tenant_id, user_id)` riêng cho tenant đó. Cái giá là query toàn tenant phải scatter-gather.
- Cô lập tài nguyên (rate limit theo tenant) để một tenant không kéo sập tenant khác trên cùng shard.

**Định tuyến** (tìm shard cho một key):

| Cách | Cách làm | Thêm shard thì | Nhược |
|---|---|---|---|
| `hash(key) % N` | Chia lấy dư theo số shard | Đổi N thành N+1 làm gần như mọi key đổi chỗ | Không mở rộng được |
| Consistent hashing | Đặt shard và key lên một vòng hash, key thuộc shard gần nhất theo chiều kim đồng hồ | Chỉ khoảng 1/(N+1) số key phải chuyển | Cần virtual node để chia đều |
| Directory | Bảng `tenant_id → shard` | Chuyển từng tenant tuỳ ý | Thêm một thành phần phải luôn sống và được cache |
| Shard logic cố định | Nhiều shard logic (ví dụ 1024) cố định, `hash % 1024`, rồi bảng tra shard logic → máy | Chỉ chuyển nguyên shard logic sang máy mới | Phải chọn số shard logic đủ lớn từ đầu |

Cách cuối là cách DDIA gọi là "số partition cố định" và là cách Notion, Figma đều dùng dưới
một dạng nào đó: key không bao giờ đổi shard logic, chỉ shard logic đổi máy.

**Những gì mất đi khi shard**:

- Join, `GROUP BY`, `ORDER BY ... LIMIT` xuyên shard phải làm ở tầng app hoặc proxy: gửi query tới mọi
  shard rồi gộp kết quả (*scatter-gather*). Figma nhận xét mỗi query scatter-gather tạo tải bằng
  đúng một query trên DB chưa shard, vì nó chạm mọi shard; dùng nhiều thì shard vô nghĩa.
- Transaction xuyên shard cần 2PC hoặc saga ([14-distributed-systems.md](../14-distributed-systems.md)).
  Nhiều hệ chọn thiết kế sao cho không cần, và chấp nhận xử lý lỗi từng phần.
- Unique toàn cục (`UNIQUE(email)`) chỉ còn đúng trong một shard. Cần một bảng hoặc service riêng giữ
  unique, hoặc chỉ cho unique trên key có chứa shard key.
- `AUTO_INCREMENT` mỗi shard đếm riêng, trùng nhau; phải sinh ID phân tán (Snowflake, UUIDv7, ULID;
  module 2.1).
- Schema migration phải chạy trên mọi shard, và có lúc các shard ở trạng thái schema khác nhau.
- Secondary index theo cột không phải shard key: DDIA phân biệt *local index* (mỗi shard index riêng
  dữ liệu của mình, đọc phải hỏi mọi shard) và *global index* (index cũng được shard theo giá trị cột
  đó, đọc nhanh nhưng ghi phải cập nhật shard khác, thường bất đồng bộ).

**Resharding** (chuyển dữ liệu khi thêm máy), quy trình online điển hình:

1. Copy dữ liệu của shard logic sang máy mới theo batch, đồng thời bắt thay đổi đang diễn ra qua
   binlog (*CDC*, change data capture).
2. Đối soát (so checksum hoặc so từng dòng) giữa nguồn và đích.
3. Chuyển đọc sang đích, theo dõi.
4. Cutover ghi: chặn ghi vào nguồn trong vài giây, đợi đích bắt kịp, đổi bảng định tuyến, mở ghi.

Shopify dùng Ghostferry (mã nguồn mở) cho việc này: copy theo batch kết hợp đọc binlog, verify rồi
cutover với downtime rất ngắn, chủ yếu để chuyển từng shop giữa các shard MySQL. Thiết kế của nó được
đặc tả bằng TLA+.

**Vitess** (sinh ra ở YouTube, PlanetScale phát triển tiếp) là lớp đứng trước nhiều MySQL:

- *Keyspace*: một DB logic, có thể gồm nhiều shard.
- *Vindex*: hàm ánh xạ giá trị cột thành *keyspace ID*. Shard được đặt tên theo khoảng keyspace
  ID (`-80` là nửa đầu, `80-` là nửa sau). *Primary vindex* (ví dụ `xxhash` trên shard key) quyết định
  dòng nằm ở đâu; *lookup vindex* là bảng tra phụ để định tuyến query theo cột khác.
- VTGate nhận query như một MySQL bình thường, định tuyến theo vindex, scatter-gather khi cần.
- Resharding online bằng cách chia một khoảng keyspace ID thành hai rồi chuyển dần.

#### Case study: Notion (Postgres, 2020–2021)

- **Vì sao**: một Postgres monolith. `VACUUM` bắt đầu thường xuyên bị treo, không thu hồi được chỗ
  của các dead tuple (module 3.7), và có nguy cơ *TXID wraparound*, tình trạng Postgres buộc phải dừng
  nhận ghi để bảo vệ dữ liệu.
- **Shard gì**: bảng `block` (mỗi khối nội dung là một dòng) cùng mọi bảng liên hệ tới nó qua khoá
  ngoại (`space`, `discussion`, `comment`...).
- **Shard key**: workspace ID. Mỗi block thuộc đúng một workspace, và người dùng gần như luôn làm việc
  trong một workspace, nên không cần join xuyên shard.
- **Kiến trúc**: 480 shard logic trên 32 máy vật lý, mỗi máy 15 shard. Mỗi shard logic là một schema
  Postgres riêng (`schema001.block`, `schema002.block`...), không dùng partitioning native, để app
  định tuyến một bước thẳng tới máy và schema.
- **Vì sao 480**: 480 chia hết cho rất nhiều số (2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20, 24, 30, 32,
  40, 48, 60...), nên thêm hay bớt máy mà vẫn chia đều được. Chọn 512 thì chỉ tăng được theo luỹ thừa
  của 2 (32 lên 64 máy).
- **Migration**:
  1. Ghi đôi qua *audit log*: mọi ghi vào DB cũ được ghi vào một bảng audit, một script catch-up áp
     chúng sang DB mới. Họ chuẩn bị cả audit log chiều ngược lại để rollback.
  2. Backfill dữ liệu cũ: khoảng 3 ngày trên một máy 96 CPU; script so version của bản ghi và bỏ qua
     dòng đã có bản mới hơn.
  3. Verify: một script lấy mẫu ngẫu nhiên để so, cộng *dark read* (đọc cả hai nơi, so kết quả, trả
     kết quả cũ). Người viết verify khác người viết migration để không lặp cùng một lỗi.
  4. Cutover: 5 phút bảo trì có lịch để catch-up script chạy xong.
- **Bài học**: nên shard sớm hơn, khi chưa quá căng thì có nhiều lựa chọn hơn; nên nhắm tới zero
  downtime; nên gộp partition key vào primary key từ đầu thay vì có `id` và `space_id` tách rời phải
  truyền khắp code.

#### Case study: Figma (Postgres trên RDS, 2020–2023)

- **Bối cảnh**: DB tăng gần 100 lần từ 2020. Ban đầu một Postgres trên RDS.
- **Tách dọc trước**: tới cuối 2022, họ chuyển các nhóm bảng liên quan (ví dụ nhóm "files", nhóm
  "organizations") sang các DB riêng. Cách này cho thêm runway nhanh với rủi ro thấp.
- **Vì sao vẫn phải shard ngang**: một số bảng đã lên vài TB, hàng tỉ dòng; vacuum không còn đáng tin,
  bảng ghi nhiều chạm trần IOPS của RDS. Đơn vị nhỏ nhất của tách dọc là một bảng, không chia nhỏ hơn
  được.
- **Colo** (*colocation*): nhóm các bảng có cùng shard key và cùng cách bố trí vật lý. Join và
  transaction trong một colo trên shard key vẫn chạy được. Họ dùng vài shard key (UserID, FileID,
  OrgID) vì gần như mọi bảng đều gắn được với một trong số đó.
- **Hash shard key** để tránh hot spot do ID tăng dần; đổi lại range scan theo shard key kém hiệu quả.
- **Tách shard logic và shard vật lý**: trước khi di chuyển dữ liệu, họ tạo các Postgres view cho từng
  shard logic trên chính DB cũ (`CREATE VIEW table_shard1 AS SELECT * FROM table WHERE hash(key) >= min
  AND hash(key) < max`) và cho app đọc/ghi qua đó. Overhead đo được dưới 10% trong trường hợp xấu. Nhờ
  vậy có thể bật, tắt, rollback phần định tuyến mà chưa phải chuyển byte nào.
- **DBProxy** (viết bằng Go): parse SQL thành cây cú pháp, planner logic tìm shard ID, planner vật lý
  ánh xạ sang DB thật và viết lại query.
- **Giới hạn cố ý**: dùng *shadow planning* trên traffic thật để xem query nào hay gặp, rồi chỉ hỗ trợ
  nhóm chiếm khoảng 90%: point query, range query, join chỉ khi hai bảng cùng colo và join trên shard
  key. Không hỗ trợ transaction nguyên tử xuyên shard.
- **Kết quả**: mất khoảng 9 tháng; lần failover vật lý đầu tiên (09/2023) chỉ có khoảng 10 giây sẵn
  sàng một phần trên primary, không ảnh hưởng replica, không thấy suy giảm latency hay availability.
- **Việc còn lại** họ tự nêu: schema change trên nhiều shard, ID toàn cục, unique index phân tán, tự
  động split shard.

Điểm chung của hai case: tận dụng hết các bước rẻ trước; chọn shard key theo đơn vị mà query tự nhiên
đã giới hạn (workspace, file, org); chia nhiều shard logic cố định trên ít máy; migration có ghi đôi,
verify độc lập, và đường rollback.

#### Archiving

Ví dụ bảng `orders` có 5 năm dữ liệu nhưng chỉ 3 tháng gần nhất hay được đọc. Dữ liệu cũ vẫn chiếm
buffer pool khi bị quét, làm index sâu hơn, làm backup và `ALTER TABLE` lâu hơn. Chuyển nó đi:

- Sang bảng archive (`orders_archive`) hoặc DB archive cùng cấu trúc.
- Sang kho OLAP (ClickHouse, BigQuery) nếu chỉ còn để báo cáo.
- Sang object storage (Parquet trên S3) nếu chỉ giữ vì pháp lý.

Nếu bảng đã partition theo thời gian, archive là `EXCHANGE PARTITION` hoặc dump partition rồi
`DROP PARTITION`. Nếu không, phải xoá theo batch:

⚠️ Một câu `DELETE ... WHERE created_at < ...` xoá hàng triệu dòng là một transaction khổng lồ: giữ
lock trên mọi dòng tới khi xong, undo log phình to (purge không dọn được, module 3.1), replica phải áp
nguyên transaction đó nên trễ theo, và nếu bị kill giữa chừng thì rollback còn lâu hơn.

```php
<?php
declare(strict_types=1);

// Chuyển đơn cũ sang bảng archive theo batch nhỏ; mỗi batch một transaction ngắn.
function archiveOldOrders(PDO $pdo, string $before, int $batchSize = 1000): int
{
    $total = 0;
    $selectIds = $pdo->prepare(
        'SELECT id FROM orders WHERE created_at < ? ORDER BY id LIMIT ' . $batchSize
    );
    while (true) {
        $selectIds->execute([$before]);
        /** @var list<int> $ids */
        $ids = array_map('intval', $selectIds->fetchAll(PDO::FETCH_COLUMN));
        if ($ids === []) {
            break;
        }
        $in = implode(',', array_fill(0, count($ids), '?'));
        $pdo->beginTransaction();
        $pdo->prepare("INSERT INTO orders_archive SELECT * FROM orders WHERE id IN ($in)")->execute($ids);
        $pdo->prepare("DELETE FROM orders WHERE id IN ($in)")->execute($ids);
        $pdo->commit();
        $total += count($ids);
        usleep(100_000); // nhường thời gian cho replica bắt kịp; tốt hơn là kiểm tra lag thật
    }
    return $total;
}
```

Điểm quan trọng: lọc theo cột có index, mỗi batch vài nghìn dòng, commit sau mỗi batch, nghỉ giữa các
batch hoặc dừng khi replica lag vượt ngưỡng. `pt-archiver` của Percona Toolkit làm sẵn đúng việc này.

**Tóm tắt nhanh**
- Thứ tự: query/index, cache, replica, máy lớn hơn, tách theo chức năng, partition/archive, rồi mới
  shard. Shard khi tải ghi hoặc dung lượng vượt một máy.
- Partition giúp chủ yếu ở vòng đời dữ liệu (`DROP PARTITION`), không phải tăng tốc chung; mọi unique
  key phải chứa cột partition, không có foreign key.
- Shard key: có trong phần lớn query, chia đều, không đổi; SaaS thì `tenant_id`, có kế hoạch cho
  tenant lớn.
- Nhiều shard logic cố định trên ít máy (Notion: 480 trên 32) để resharding chỉ là di chuyển shard logic.
- Shard làm mất join/transaction/unique/auto-increment xuyên shard; scatter-gather phải hiếm.
- Xoá dữ liệu lớn theo batch hoặc drop partition, không bao giờ một câu `DELETE` khổng lồ.

**Nguồn**: [MySQL: Partitioning](https://dev.mysql.com/doc/refman/8.4/en/partitioning.html) ·
[MySQL: Partition Pruning](https://dev.mysql.com/doc/refman/8.4/en/partitioning-pruning.html) ·
[MySQL: Restrictions and Limitations](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html) ·
[MySQL: Partitioning Keys, Primary Keys, Unique Keys](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html) ·
[Vitess: Vindexes](https://vitess.io/docs/reference/features/vindexes/) ·
[Notion: Sharding Postgres](https://www.notion.com/blog/sharding-postgres-at-notion) ·
[Figma: How Figma's databases team lived to tell the scale](https://www.figma.com/blog/how-figmas-databases-team-lived-to-tell-the-scale/) ·
[Shopify Ghostferry](https://github.com/shopify/ghostferry) · DDIA ch.6

---

### 3.7 MySQL so với Postgres

Module này trả lời: MySQL (InnoDB) và PostgreSQL khác nhau ở tầng cơ chế nào, các khác biệt đó gây
ra vấn đề vận hành gì, và khi được hỏi "chọn cái nào" thì lập luận ra sao. Trọng tâm là bài viết nổi
tiếng của Uber năm 2016 và các phản biện của nó.

#### So sánh 10 điểm

| | MySQL 8.4 (InnoDB) | PostgreSQL 18 |
|---|---|---|
| Lưu trữ | Bảng là clustered index theo PK; secondary index chứa giá trị PK | Heap (dòng xếp không theo thứ tự); mọi index chứa địa chỉ vật lý `ctid` |
| MVCC | Sửa dòng tại chỗ, bản cũ vào undo log, purge thread dọn | Mỗi UPDATE ghi một bản dòng mới trong bảng, bản cũ thành *dead tuple*, VACUUM dọn |
| Isolation mặc định | Repeatable Read | Read Committed |
| Connection | Một thread mỗi connection | Một process mỗi connection |
| Join | Nested loop, hash join (từ 8.0.18) | Nested loop, hash join, merge join |
| Index | B-tree, full-text, spatial, functional, multi-valued (JSON) | B-tree, hash, GIN, GiST, SP-GiST, BRIN; partial index, expression index |
| DDL trong transaction | Không; mỗi DDL tự commit | Có; migration lỗi thì rollback sạch |
| Kiểu dữ liệu | Cơ bản, `JSON` | `jsonb`, mảng, range, `inet`, `uuid`, enum, kiểu tự định nghĩa |
| Mở rộng | Plugin, hạn chế | Extension: PostGIS, pg_trgm, pgvector, TimescaleDB, Citus |
| Công cụ scale, HA | Vitess, ProxySQL, gh-ost, Orchestrator, Group Replication | Citus, Patroni, PgBouncer, logical replication |

Giải thích các dòng quan trọng nhất:

- **Lưu trữ.** InnoDB lưu dòng ngay trong lá của cây PK (module 2.1). Secondary index trỏ tới giá trị
  PK, nên tra theo secondary index là hai lần đi cây: cây secondary rồi cây PK. Postgres để dòng trong
  heap; mọi index, kể cả PK, trỏ thẳng tới vị trí vật lý, nên tra secondary index chỉ một lần đi cây
  rồi nhảy vào heap. Hệ quả ngược lại: ở InnoDB, dòng di chuyển (page split) thì secondary index không
  phải sửa; ở Postgres, dòng có vị trí mới thì mọi index phải có entry mới.
- **MVCC.** Cả hai đều cho người đọc thấy snapshot mà không chặn người ghi, nhưng cất bản cũ ở chỗ
  khác nhau. InnoDB: bảng luôn chứa bản mới nhất, bản cũ tái tạo từ undo log (module 3.1). Postgres:
  bảng chứa nhiều phiên bản của cùng một dòng, mỗi bản có `xmin`/`xmax` (transaction tạo và xoá nó);
  người đọc chọn bản hợp với snapshot của mình.
- **Isolation.** Repeatable Read của Postgres là snapshot isolation thật: hai transaction cùng update
  một dòng thì transaction sau nhận lỗi serialization (SQLSTATE `40001`) và phải retry. Repeatable
  Read của InnoDB thì `UPDATE` đọc bản mới nhất (*current read*) và không báo lỗi, nên dễ dính lost
  update nếu không dùng `SELECT ... FOR UPDATE` (module 2.5).
- **DDL.** Ở MySQL, một migration gồm ba câu `ALTER` mà câu thứ hai lỗi thì câu đầu đã commit, schema
  ở trạng thái dở. Ở Postgres cả migration nằm trong một transaction. (Một số lệnh như
  `CREATE INDEX CONCURRENTLY` của Postgres vẫn không chạy được trong transaction.)

#### Cùng một workload update nhiều, hai DB đau ở chỗ khác nhau

Đây là câu hay bị hỏi nhất, vì nó kiểm tra bạn có hiểu MVCC ở mức cơ chế không. Giả sử bảng `trips`
có 10 index, mỗi giây cập nhật `status` và `updated_at` hàng nghìn lần.

*Postgres*:

1. Mỗi `UPDATE` ghi một tuple mới vào heap, tuple cũ thành dead tuple.
2. Nếu không cột nào có index bị đổi **và** page hiện tại còn chỗ, Postgres làm *HOT update*
   (heap-only tuple): tuple mới nằm cùng page, nối từ tuple cũ, index không phải sửa. Tăng khoảng
   trống mỗi page bằng `fillfactor` (ví dụ 80) làm HOT xảy ra nhiều hơn.
3. Nếu không được HOT (ví dụ `updated_at` hay `status` có index), **mọi index** đều phải thêm entry
   trỏ tới tuple mới, kể cả index trên cột không đổi. 10 index là 10 lần ghi index thêm, cộng WAL
   tương ứng. Đây là *write amplification*.
4. Dead tuple và entry index cũ nằm đó tới khi VACUUM dọn. Autovacuum chạy không kịp thì bảng và index
   phình (*bloat*), query chậm vì phải đọc nhiều page hơn.
5. Một transaction mở lâu (hoặc replica bật `hot_standby_feedback`) giữ lại mốc `xmin` cũ nhất, VACUUM
   không được xoá dead tuple nào mới hơn mốc đó, bloat tăng không giới hạn.
6. ID transaction là số 32 bit; nếu VACUUM không kịp "đóng băng" (freeze) các dòng cũ, Postgres tiến
   gần tới *wraparound* và cuối cùng từ chối ghi để bảo vệ dữ liệu. Đây chính là rủi ro đẩy Notion
   đi shard (module 3.6).

*MySQL (InnoDB)*:

1. `UPDATE` sửa dòng tại chỗ trong cây PK, ghi bản cũ vào undo log.
2. Chỉ những secondary index chứa cột bị đổi mới phải sửa (xoá đánh dấu entry cũ, thêm entry mới). Đổi
   `status` mà chỉ một index chứa `status` thì chỉ một index bị động tới.
3. Purge thread dọn undo và entry index đã đánh dấu xoá khi không còn read view nào cần. Transaction
   mở lâu làm *history list length* tăng, undo log phình, và các lần đọc nhất quán phải lần ngược chuỗi
   undo dài hơn (module 3.1).
4. Điểm đau thường gặp khác là **lock**: nhiều request cùng update các dòng "nóng" (một bộ đếm, một
   dòng tồn kho) xếp hàng chờ row lock, deadlock (module 2.6, 3.2).

Câu trả lời 3 phút gói lại: Postgres trả giá ở **dung lượng và bảo trì** (write amplification lên
index, bloat, phụ thuộc autovacuum, wraparound); InnoDB trả giá ở **undo/purge và tranh chấp lock**,
và ở chi phí tra secondary index hai lần. Cách giảm đau của Postgres: ít index hơn, `fillfactor` thấp
để được HOT, tinh chỉnh autovacuum theo bảng, không để transaction mở lâu. Của MySQL: transaction ngắn,
theo dõi history list length, tránh dòng nóng (chia bộ đếm thành nhiều dòng).

#### Connection và PgBouncer

Postgres fork một process cho mỗi connection. Process tốn bộ nhớ riêng (vài MB trở lên) và chuyển
ngữ cảnh đắt hơn thread, nên vài trăm connection đang hoạt động đã là nhiều. App PHP-FPM với 50 máy x
50 worker = 2.500 connection sẽ làm Postgres khổ. Giải pháp chuẩn là đặt *connection pooler* như
PgBouncer ở giữa: nhiều client dùng chung một số ít connection thật tới server.

PgBouncer có ba chế độ:

| Chế độ | Connection thật được gán cho client | Mức tiết kiệm |
|---|---|---|
| Session | Suốt thời gian client kết nối | Thấp; gần như không đổi ngữ nghĩa |
| Transaction | Chỉ trong một transaction, xong thì trả về pool | Cao; phổ biến nhất |
| Statement | Từng câu lệnh, cấm transaction nhiều câu | Cao nhất, ít dùng |

⚠️ Ở transaction mode, hai transaction liên tiếp của cùng một client có thể chạy trên hai connection
server khác nhau, nên mọi thứ gắn với *session* đều hỏng. Theo bảng tính năng của PgBouncer, các thứ
không dùng được: `SET`/`RESET` (ví dụ `SET search_path`, `SET statement_timeout`), `LISTEN`, cursor
`WITH HOLD`, `PREPARE`/`DEALLOCATE` bằng SQL, advisory lock cấp session, `LOAD`. Prepared statement ở
mức protocol thì được hỗ trợ ở các bản mới (từ 1.21, điều khiển bằng `max_prepared_statements`; từ 1.24 mặc định
đã bật, giá trị 200).

Liên hệ PHP: `pdo_pgsql` mặc định dùng prepared statement phía server (khác `pdo_mysql` mặc định giả
lập, module 2.7). Qua PgBouncer transaction mode bản cũ, lỗi kiểu `prepared statement
"pdo_stmt_00000001" does not exist` xuất hiện ngẫu nhiên. Cách xử lý: nâng PgBouncer và bật
`max_prepared_statements`, hoặc bật `PDO::ATTR_EMULATE_PREPARES => true` cho connection Postgres.
Dùng `SET LOCAL` (chỉ có hiệu lực trong transaction) thay cho `SET`.

MySQL dùng thread nên chịu được nhiều connection hơn (Uber nói khoảng 10.000 connection đồng thời là chuyện thường), nhưng mỗi connection
vẫn tốn bộ nhớ và `max_connections` mặc định là 151; ProxySQL đóng vai tương tự PgBouncer.

#### Bài viết của Uber (2016) và các phản biện

Bối cảnh: Uber chạy Postgres 9.2, primary ở một datacenter phía tây và replica ở phía đông, rồi chuyển
sang MySQL, cụ thể là **Schemaless**, một lớp sharding tự viết chạy trên MySQL.

Lập luận của Uber:

1. **Write amplification**: mọi index trỏ tới `ctid`, nên update một cột làm mọi index phải ghi thêm,
   và mọi thứ đó đi vào WAL. InnoDB chỉ sửa index có cột thay đổi.
2. **Replication tốn băng thông**: replication của Postgres lúc đó là physical (gửi WAL, tức thay đổi
   ở mức byte của page, gồm cả thay đổi index), rất dài dòng khi đi qua link giữa hai datacenter.
   Binlog dạng ROW của MySQL chỉ mô tả thay đổi logic của dòng; replica tự suy ra việc sửa index.
3. **Hỏng dữ liệu**: một bug của 9.2 khiến replica áp sai WAL khi đổi timeline, sinh dòng trùng, khác
   nhau giữa các replica. Vì replication ở mức vật lý, lỗi có thể lan ra cả cây B-tree. Replication
   logic thì không có loại lỗi này.
4. **Replica không có MVCC thật**: transaction mở lâu trên replica chặn việc áp WAL; Postgres sẽ huỷ
   query đó sau một thời gian chờ. Dev giữ transaction mở trong lúc gửi email là đủ gây sự cố.
5. **Nâng cấp khó**: WAL không tương thích giữa các major version, nên không replicate từ bản cũ sang
   bản mới được. Họ nâng 9.1 lên 9.2 bằng `pg_upgrade` mất nhiều giờ và không dám làm lại. MySQL nâng
   từng replica một, gần như không downtime.
6. **Connection**: process mỗi connection, khó vượt vài trăm connection đang hoạt động, phải dùng
   PgBouncer; bug app để connection "idle in transaction" gây sự cố.
7. **Cache**: Postgres dựa vào page cache của OS (replica lớn nhất có 768 GB RAM nhưng chỉ khoảng
   25 GB là bộ nhớ của chính các process Postgres), mỗi lần đọc qua system call `lseek` + `read`. InnoDB tự quản buffer pool trong bộ nhớ
   của process, không cần system call.

Phản biện, từ Robert Haas (một committer lâu năm của Postgres) và Markus Winand (tác giả Use The Index,
Luke):

- **Đồng ý**: write amplification là vấn đề thật và khó sửa nhất, vì định dạng tuple ăn sâu vào toàn
  hệ thống (Haas). Postgres khi đó thiếu logical replication trong core là điểm yếu thật.
- **HOT bị bỏ qua**: bài của Uber không nhắc HOT. Winand suy ra các update của Uber hay đổi chính
  những cột có index, nên HOT không giúp được, tức đây là đặc thù workload chứ không phải mọi workload.
- **Cái giá của clustered index bị xem nhẹ**: Uber gọi việc tra secondary index hai lần của InnoDB là
  "bất lợi nhỏ"; Winand cho rằng đó là bất lợi lớn với workload dựa nhiều vào secondary index. Việc Uber
  thấy nó nhỏ cho thấy họ chủ yếu tra theo PK, tức gần như key-value.
- **Cấu hình và công cụ có sẵn**: Haas hỏi Uber có biết `hot_standby_feedback = on` (tránh huỷ query
  trên replica, đổi lại có thể gây bloat trên primary), nén WAL, và các tool logical replication bên
  ngoài (Slony, Bucardo, Londiste) chưa. Ông cũng nói một số vấn đề hiệu năng của `pg_upgrade` đã được sửa ở các bản mới hơn,
  nên có thể trên 9.4, 9.5 tình hình đã khá hơn.
- **Kết luận của Winand**: Uber không thật sự "chuyển từ Postgres sang MySQL" cho một workload quan
  hệ; họ xây một kho key-value (Schemaless) và InnoDB là storage engine hợp với kiểu đó.

Điều gì đã thay đổi từ 2016:

- PostgreSQL 10 (2017) có logical replication native (publication/subscription), dùng được để nâng
  major version gần như không downtime và để replicate một phần dữ liệu.
- `pg_upgrade` ngày càng nhanh; PostgreSQL 18 giữ lại thống kê của optimizer qua lần nâng cấp và có
  chế độ `--swap`.
- PostgreSQL 18 có hệ thống I/O bất đồng bộ (`io_method`), cải thiện sequential scan, bitmap scan,
  vacuum; và skip scan trên B-tree nhiều cột.
- Write amplification và VACUUM về bản chất vẫn còn: đó là hệ quả của thiết kế heap + MVCC trong bảng.
- Phía MySQL, replication vẫn có bug riêng của nó qua các năm; "replication logic không bao giờ hỏng"
  là nói quá.

Cách dùng bài này khi phỏng vấn: không kể "Uber bỏ Postgres nên MySQL tốt hơn", mà dùng nó để nói
rằng **lựa chọn DB phụ thuộc workload**: update nhiều trên cột có index, tra theo PK, replicate xa thì
thiết kế của InnoDB có lợi; query phức tạp theo nhiều index, cần kiểu dữ liệu và extension phong phú
thì Postgres có lợi.

#### PostgreSQL 18: những điểm nên biết

Phát hành 25/09/2025. Những thay đổi hay được nhắc:

- I/O bất đồng bộ (`io_method`), đã nói ở trên.
- Skip scan: index `(a, b)` dùng được cho `WHERE b = ?` khi `a` có ít giá trị khác nhau. MySQL có skip
  scan từ 8.0.13.
- `uuidv7()`: sinh UUID có thứ tự thời gian, tốt cho PK (lý do ở module 2.1).
- Virtual generated column là mặc định (tính lúc đọc); muốn lưu thì ghi `STORED`.
- `RETURNING old.*, new.*` trong `INSERT`/`UPDATE`/`DELETE`/`MERGE`.
- Ràng buộc thời gian `WITHOUT OVERLAPS` cho PK/unique.
- `initdb` bật data checksum mặc định; xác thực OAuth; mật khẩu MD5 bị cảnh báo deprecated.

#### Chọn cái nào

Không có đáp án chung. Các câu hỏi dẫn tới quyết định:

1. **Đội ngũ đang vận hành giỏi cái gì?** Chi phí vận hành một DB mình không hiểu lớn hơn mọi khác biệt
   hiệu năng. Stack PHP/Laravel lâu năm thường có kinh nghiệm MySQL.
2. **Cần tính năng gì?** GIS (PostGIS), tìm kiếm mờ (pg_trgm), vector (pgvector), `jsonb` với GIN
   index, partial index, kiểu range: nghiêng về Postgres.
3. **Workload ra sao?** Update rất nhiều, chủ yếu tra theo PK, nhiều connection ngắn: InnoDB dễ chịu
   hơn. Query phân tích phức tạp, nhiều kiểu join: optimizer của Postgres mạnh hơn.
4. **Hệ sinh thái scale cần dùng?** Shard MySQL thì có Vitess, PlanetScale đã chạy ở quy mô rất lớn;
   Postgres có Citus.
5. **Managed service nào có sẵn** ở cloud đang dùng, và ở mức giá nào.

Một câu trả lời tốt nêu 2 đến 3 tiêu chí này áp vào bài toán cụ thể, rồi nói điều kiện nào sẽ làm bạn
đổi ý.

**Tóm tắt nhanh**
- Khác biệt gốc: InnoDB clustered + undo log; Postgres heap + nhiều phiên bản dòng trong bảng + VACUUM.
  Phần lớn khác biệt vận hành suy ra từ đây.
- Update nhiều: Postgres đau ở write amplification lên mọi index (trừ HOT), bloat, autovacuum,
  wraparound; InnoDB đau ở undo/purge, lock trên dòng nóng, và tra secondary hai lần.
- Postgres mặc định Read Committed, RR của nó báo lỗi serialization; InnoDB mặc định RR, không báo.
- Postgres cần PgBouncer; transaction mode làm hỏng `SET`, `LISTEN`, advisory lock session, `PREPARE`
  SQL; PDO pgsql cần chú ý prepared statement.
- Bài Uber đúng cho workload của Uber (gần key-value, update cột có index, replicate xa); phản biện chỉ
  ra HOT, cái giá của clustered index, và nhiều điểm đã được Postgres 10+ giải quyết.

**Nguồn**: [Uber: Why Uber Engineering Switched from Postgres to MySQL](https://www.uber.com/us/en/blog/postgres-to-mysql-migration/) ·
[Robert Haas: Uber's move away from PostgreSQL](https://rhaas.blogspot.com/2016/08/ubers-move-away-from-postgresql.html) ·
[Markus Winand: On Uber's Choice of Databases](https://use-the-index-luke.com/blog/2016-07-29/on-ubers-choice-of-databases) ·
[PgBouncer features](https://www.pgbouncer.org/features.html) ·
[PostgreSQL 18 release notes](https://www.postgresql.org/docs/current/release-18.html)
