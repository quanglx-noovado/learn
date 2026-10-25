# Chương 17. View, stored procedure, function, trigger, event

> [← Mục lục](README.md) · [← Chương 16: Bên trong InnoDB](16-ben-trong-innodb.md) · [Chương 18: Người dùng, phân quyền và bảo mật →](18-user-quyen-bao-mat.md)

**Bạn sẽ học được:**

- Năm loại *stored object* của MySQL (view, stored procedure, stored function, trigger, event): mỗi
  loại là gì, sống ở đâu, ai gọi nó và chạy với quyền của ai.
- Tạo và dùng view; biết khi nào view cập nhật được (`UPDATE`/`INSERT`/`DELETE` qua view), `WITH
  CHECK OPTION`, hai thuật toán `MERGE`/`TEMPTABLE`, và dùng view để che bớt dữ liệu.
- Viết stored procedure và stored function: `DELIMITER`, tham số `IN`/`OUT`/`INOUT`, biến cục bộ so
  với biến `@user`, `IF`/`CASE`/vòng lặp, cursor, xử lý lỗi bằng `DECLARE ... HANDLER`, `SIGNAL`,
  `RESIGNAL`, `GET DIAGNOSTICS`.
- Viết trigger `BEFORE`/`AFTER` với `NEW`/`OLD`, hiểu trigger chạy trong transaction nào, và khi nào
  nên, khi nào không nên dùng trigger.
- Lên lịch việc định kỳ bằng event scheduler.
- Dùng prepared statement phía server (`PREPARE`/`EXECUTE`), và cân nhắc được "logic đặt trong
  database hay trong ứng dụng" như một kỹ sư senior.

**Cần biết trước:** [Chương 04](04-ddl-constraint.md) (`CREATE TABLE`, constraint),
[Chương 05](05-select-co-ban.md) (`INSERT`/`UPDATE`/`DELETE`/`SELECT`),
[Chương 09](09-subquery-cte-union.md) (subquery, derived table), [Chương 13](13-transaction-acid.md)
(transaction, `COMMIT`/`ROLLBACK`). Phần bảo mật của view và routine nhắc tới quyền (`GRANT`); chi
tiết tài khoản và phân quyền nằm ở [Chương 18](18-user-quyen-bao-mat.md).

## 1. Stored object là gì

### 1.1 Từ câu lệnh rời rạc tới đối tượng lưu trong database

Tới giờ, mọi câu SQL bạn viết đều là câu *rời rạc*: ứng dụng (hoặc bạn ở client `mysql`) gửi một câu
lên server, server chạy, trả kết quả, rồi quên câu đó đi. Nếu mai bạn cần lại câu ấy, bạn phải gửi lại
nguyên văn.

MySQL cho phép bạn đặt tên cho một đoạn SQL và *lưu nó vào trong database*, cạnh các bảng. Những thứ
được lưu như vậy gọi chung là *stored object* (đối tượng lưu trữ). Có năm loại:

| Loại | Nó là gì | Ai kích hoạt | Ví dụ dùng |
|---|---|---|---|
| *View* | Một câu `SELECT` có tên, dùng như một bảng ảo | Người dùng, khi `SELECT ... FROM view` | Che cột nhạy cảm, đặt tên cho một query hay dùng |
| *Stored procedure* | Một chương trình nhỏ, gọi bằng `CALL` | Người dùng, bằng `CALL p(...)` | Chuyển tiền giữa hai tài khoản, một job dọn dữ liệu |
| *Stored function* | Hàm trả về một giá trị, dùng trong biểu thức | Người dùng, trong `SELECT f(x)` | Tính phí ship, chuẩn hoá chuỗi |
| *Trigger* | Đoạn code gắn với một bảng, tự chạy khi có `INSERT`/`UPDATE`/`DELETE` | Server, tự động | Ghi lịch sử thay đổi, kiểm tra dữ liệu |
| *Event* | Đoạn code chạy theo lịch | Server (event scheduler), theo giờ | Xoá session hết hạn mỗi đêm |

Tài liệu MySQL gọi procedure, function, trigger và event là *stored program* (chương trình lưu trữ),
và gọi riêng procedure với function là *stored routine*. View không phải "chương trình" (nó chỉ là một
câu `SELECT`), nhưng được xếp chung nhóm stored object vì cùng được định nghĩa trước, lưu trong
database và có chung cơ chế bảo mật `DEFINER`/`SQL SECURITY` (mục 2.6).

Trong MySQL 8, định nghĩa của mọi stored object được lưu trong *data dictionary* (từ điển dữ liệu, các
bảng hệ thống mà [Chương 16](16-ben-trong-innodb.md) đã nhắc tới) và bạn xem được qua các bảng
`INFORMATION_SCHEMA.VIEWS`, `ROUTINES`, `TRIGGERS`, `EVENTS`.

### 1.2 Vì sao lại muốn đặt code vào database

Ba lý do chính, và cũng là ba thứ bạn sẽ cân lại ở mục 10:

1. **Gần dữ liệu.** Một procedure chạy mười câu SQL ngay trên server chỉ tốn một lượt đi về mạng
   (*round trip*), thay vì mười lượt nếu ứng dụng gửi từng câu.
2. **Một chỗ dùng chung.** Nhiều ứng dụng (PHP, Go, công cụ BI, người chạy tay) cùng đọc một database
   thì logic đặt trong database được áp dụng cho tất cả, không ai "quên" được.
3. **Kiểm soát quyền.** Bạn có thể cho một tài khoản quyền gọi một procedure mà không cho nó quyền sửa
   trực tiếp bảng bên dưới; hoặc cho nó đọc một view mà không cho đọc bảng gốc.

Cái giá phải trả (khó test, khó deploy, khó scale, khó debug) sẽ được bàn kỹ ở mục 10. Bây giờ cứ học
công cụ trước.

### 1.3 Dữ liệu mẫu của chương

Mọi ví dụ chạy trên MySQL 8.4; chỗ nào là PostgreSQL sẽ ghi rõ. Nếu chưa có MySQL:

```bash
# Chạy trên máy của bạn (terminal thường)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi vài giây cho server khởi động xong, rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Dán đoạn sau vào client `mysql`:

```sql
DROP DATABASE IF EXISTS ch17;      -- database riêng của chương, xoá đi tạo lại cho sạch
CREATE DATABASE ch17;
USE ch17;

CREATE TABLE customers (
  id    INT PRIMARY KEY,
  name  VARCHAR(50)  NOT NULL,
  email VARCHAR(100) NOT NULL,     -- dữ liệu cá nhân: sẽ dùng view để che đi
  phone VARCHAR(20),
  city  VARCHAR(30)  NOT NULL
);
INSERT INTO customers VALUES
  (1, 'An',   'an@example.com',   '0901', 'Hà Nội'),
  (2, 'Bình', 'binh@example.com', NULL,   'HCM'),
  (3, 'Chi',  'chi@example.com',  '0903', 'Hà Nội');

CREATE TABLE products (
  id    INT PRIMARY KEY,
  name  VARCHAR(50)   NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  stock INT           NOT NULL,
  CONSTRAINT chk_stock CHECK (stock >= 0)   -- tồn kho không được âm
);
INSERT INTO products VALUES
  (1, 'Bàn phím', 500.00,  10),
  (2, 'Chuột',    200.00,  0),
  (3, 'Màn hình', 3000.00, 5);

CREATE TABLE orders (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  customer_id INT           NOT NULL,
  status      VARCHAR(20)   NOT NULL DEFAULT 'new',   -- new | paid | cancelled
  total       DECIMAL(10,2) NOT NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);
INSERT INTO orders (id, customer_id, status, total, created_at) VALUES
  (1, 1, 'paid',      700.00,  '2026-09-01 10:00:00'),
  (2, 1, 'new',       3000.00, '2026-09-02 11:00:00'),
  (3, 2, 'paid',      200.00,  '2026-09-03 12:00:00'),
  (4, 3, 'cancelled', 500.00,  '2026-09-04 09:00:00');

CREATE TABLE accounts (
  id      INT PRIMARY KEY,
  owner   VARCHAR(50)   NOT NULL,
  balance DECIMAL(12,2) NOT NULL,
  CONSTRAINT chk_balance CHECK (balance >= 0)   -- số dư không được âm
);
INSERT INTO accounts VALUES (1, 'An', 1000.00), (2, 'Bình', 500.00);
```

Mỗi mục lớn có thể làm thay đổi dữ liệu. Nếu kết quả của bạn lệch với kết quả ghi trong sách, chạy lại
đoạn trên để về trạng thái ban đầu.

## 2. View

### 2.1 View là gì

*View* là một câu `SELECT` được đặt tên và lưu lại. Sau khi tạo, bạn dùng tên view ở chỗ nào dùng được
tên bảng trong `FROM`, như thể nó là một bảng. Nhưng view **không chứa dữ liệu**: mỗi lần bạn đọc view,
MySQL chạy lại câu `SELECT` bên trong trên dữ liệu hiện tại của các bảng gốc (gọi là *base table*).

```sql
CREATE VIEW v_paid_orders AS
SELECT o.id, c.name AS customer, o.total, o.created_at
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.status = 'paid';

SELECT * FROM v_paid_orders;
```

Kết quả mong đợi:

```
+----+----------+--------+---------------------+
| id | customer | total  | created_at          |
+----+----------+--------+---------------------+
|  1 | An       | 700.00 | 2026-09-01 10:00:00 |
|  3 | Bình     | 200.00 | 2026-09-03 12:00:00 |
+----+----------+--------+---------------------+
```

(Thứ tự dòng không được đảm bảo khi không có `ORDER BY`; ở đây có thể ra theo `id`.)

Đổi dữ liệu gốc rồi đọc lại view, bạn thấy ngay thay đổi, vì không có bản sao nào cả:

```sql
UPDATE orders SET status = 'paid' WHERE id = 2;
SELECT id, customer, total FROM v_paid_orders;   -- giờ có 3 dòng: 1, 2, 3
UPDATE orders SET status = 'new' WHERE id = 2;   -- trả lại như cũ
```

Hình dung:

```
  SELECT * FROM v_paid_orders WHERE total > 500
              │
              ▼  MySQL thay tên view bằng định nghĩa của nó
  SELECT o.id, c.name, o.total, o.created_at
  FROM orders o JOIN customers c ON c.id = o.customer_id
  WHERE (o.status = 'paid') AND (o.total > 500)
              │
              ▼  chạy trên bảng thật
  orders, customers  (dữ liệu chỉ nằm ở đây)
```

### 2.2 Vì sao dùng view

- **Đặt tên cho một query phức tạp.** Query join năm bảng mà cả đội hay dùng thì gói vào view, mọi
  người `SELECT` từ view, không ai phải chép lại (và chép sai) điều kiện join.
- **Che dữ liệu.** Cho nhóm phân tích đọc view không có cột `email`, `phone`, thay vì cho đọc bảng
  `customers` (mục 2.6).
- **Giữ tương thích khi đổi schema.** Bạn tách bảng `users` làm hai; tạo một view tên `users` cũ ghép
  lại hai bảng để code cũ còn chạy trong lúc chuyển đổi.

View **không** làm query nhanh hơn: nó chỉ là cách viết gọn. MySQL không có *materialized view* (view
lưu sẵn kết quả); xem mục 2.8.

### 2.3 Tạo, xem, sửa, xoá view

Cú pháp đầy đủ theo tài liệu MySQL 8.4:

```sql
CREATE
    [OR REPLACE]
    [ALGORITHM = {UNDEFINED | MERGE | TEMPTABLE}]
    [DEFINER = user]
    [SQL SECURITY { DEFINER | INVOKER }]
    VIEW view_name [(column_list)]
    AS select_statement
    [WITH [CASCADED | LOCAL] CHECK OPTION]
```

Các thao tác thường dùng:

```sql
-- Đặt tên cột cho view bằng column_list (số tên phải bằng số cột của SELECT)
CREATE VIEW v_customer_revenue (customer_id, paid_total) AS
SELECT customer_id, SUM(total)
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;

SELECT * FROM v_customer_revenue;
-- customer_id | paid_total
--           1 |     700.00
--           2 |     200.00

SHOW CREATE VIEW v_customer_revenue\G      -- xem lại định nghĩa (MySQL đã chuẩn hoá lại câu chữ)
SHOW FULL TABLES WHERE Table_type = 'VIEW'; -- liệt kê các view trong database hiện tại

-- Thay định nghĩa: CREATE OR REPLACE hoặc ALTER VIEW
CREATE OR REPLACE VIEW v_customer_revenue (customer_id, paid_total, order_count) AS
SELECT customer_id, SUM(total), COUNT(*)
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;

DROP VIEW IF EXISTS v_customer_revenue;
```

Một số quy tắc cần nhớ (đều nằm trong trang `CREATE VIEW` của tài liệu):

- View và bảng dùng chung không gian tên trong một database: không thể có bảng và view trùng tên.
- Câu `SELECT` của view không được dùng biến hệ thống, biến `@user`, tham số của prepared statement,
  và không được tham chiếu bảng `TEMPORARY`. Không có "view tạm".
- Không gắn trigger lên view được.
- `ORDER BY` trong view được phép nhưng bị bỏ qua nếu câu đọc view có `ORDER BY` riêng. Các mệnh đề
  khác như `LIMIT` trong view mà câu ngoài cũng có `LIMIT` thì tài liệu nói rõ: không xác định cái nào
  được áp dụng. Đừng dựa vào `ORDER BY`/`LIMIT` bên trong view.

### 2.4 ⚠️ Định nghĩa view bị "đóng băng" lúc tạo

Đây là cái bẫy hay gặp nhất. Khi bạn viết `SELECT *` trong view, MySQL **mở `*` thành danh sách cột cụ
thể ngay lúc tạo view**. Tài liệu viết: định nghĩa view bị "frozen" lúc tạo, không bị ảnh hưởng bởi
thay đổi định nghĩa bảng sau đó.

```sql
CREATE VIEW v_all_customers AS SELECT * FROM customers;

ALTER TABLE customers ADD COLUMN vip TINYINT NOT NULL DEFAULT 0;
SELECT * FROM v_all_customers;      -- KHÔNG có cột vip: view vẫn chỉ có id, name, email, phone, city
SHOW CREATE VIEW v_all_customers\G  -- thấy rõ danh sách cột cụ thể, không còn dấu *
```

Chiều ngược lại còn nguy hiểm hơn: xoá hoặc đổi tên một cột mà view dùng, `ALTER TABLE` vẫn chạy
thành công **không một lời cảnh báo**, và lỗi chỉ nổ ra lúc ai đó đọc view:

```sql
ALTER TABLE customers DROP COLUMN phone;
SELECT * FROM v_all_customers;
-- ERROR 1356 (HY000): View 'ch17.v_all_customers' references invalid table(s) or column(s)
-- or function(s) or definer/invoker of view lack rights to use them

CHECK TABLE v_all_customers;   -- cách tài liệu gợi ý để phát hiện view đã hỏng
```

Bài học thực tế: trước khi xoá/đổi tên cột trong migration, tìm xem view nào dùng nó:

```sql
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS
WHERE TABLE_SCHEMA = 'ch17' AND VIEW_DEFINITION LIKE '%phone%';
```

(Cách tìm bằng `LIKE` thô, có thể ra cả kết quả thừa, nhưng đủ để không bỏ sót.)

Dọn lại để các ví dụ sau chạy đúng:

```sql
DROP VIEW v_all_customers;
ALTER TABLE customers DROP COLUMN vip, ADD COLUMN phone VARCHAR(20) AFTER email;
UPDATE customers SET phone = CASE id WHEN 1 THEN '0901' WHEN 3 THEN '0903' END;
```

(Hoặc chạy lại toàn bộ dữ liệu mẫu ở mục 1.3.)

### 2.5 MySQL xử lý view thế nào: MERGE và TEMPTABLE

Khi một câu lệnh dùng view, MySQL có hai cách xử lý:

- *MERGE*: ghép định nghĩa view vào câu lệnh, như sơ đồ ở mục 2.1. Điều kiện `WHERE` của câu ngoài
  được nối với `WHERE` của view bằng `AND`, sau đó optimizer tối ưu câu đã ghép như một câu thường, nên
  **index của bảng gốc vẫn dùng được**.
- *TEMPTABLE*: chạy câu `SELECT` của view trước, đổ kết quả vào một bảng tạm (*temporary table*), rồi
  câu ngoài đọc từ bảng tạm. Bảng tạm không có index của bảng gốc, nên điều kiện của câu ngoài không
  tận dụng được index gốc.

Ví dụ trong tài liệu: view `v_merge` định nghĩa `CREATE ALGORITHM = MERGE VIEW v_merge (vc1, vc2) AS
SELECT c1, c2 FROM t WHERE c3 > 100` (cột `vc1`, `vc2` của view ứng với `c1`, `c2`), thì câu
`SELECT * FROM v_merge WHERE vc1 < 100` trở thành:

```sql
SELECT c1, c2 FROM t WHERE (c3 > 100) AND (c1 < 100);
```

Bạn chọn bằng `ALGORITHM`:

| `ALGORITHM` | Ý nghĩa |
|---|---|
| `UNDEFINED` (mặc định khi không ghi) | MySQL tự chọn; ưu tiên `MERGE` nếu được, vì thường hiệu quả hơn và vì view dùng bảng tạm thì không cập nhật được |
| `MERGE` | Yêu cầu ghép. Nếu view không ghép được, MySQL sinh warning và chuyển thành `UNDEFINED` |
| `TEMPTABLE` | Luôn dùng bảng tạm |

Khi nào không ghép được? Cùng các điều kiện khiến một derived table (subquery trong `FROM`, Chương 09)
không ghép được vào câu ngoài; tài liệu nêu ví dụ `SELECT DISTINCT` hoặc `LIMIT` trong view. Thực tế,
view có aggregate (`SUM`, `COUNT`), `GROUP BY`, `DISTINCT`, `UNION` thường phải *materialize* (tính ra
bảng tạm). Dùng `EXPLAIN` (Chương 12) để xem: nếu thấy một dòng có `select_type` là `DERIVED` và bảng
tên dạng `<derived2>` thì view đã bị materialize.

```sql
EXPLAIN SELECT * FROM v_paid_orders WHERE id = 1;
-- view ghép được: kế hoạch chỉ có orders và customers, tra orders theo PRIMARY KEY

-- v_customer_revenue đã bị DROP ở cuối mục 2.3: tạo lại bằng câu CREATE VIEW đầu tiên của mục đó
EXPLAIN SELECT * FROM v_customer_revenue WHERE customer_id = 1;
-- view có GROUP BY: thường thấy <derived2>, tức đã tính view ra bảng tạm
```

(Phần chú thích ở trên là mô tả định tính; output `EXPLAIN` cụ thể tuỳ phiên bản và dữ liệu. Optimizer
MySQL 8 còn có thể đẩy điều kiện `WHERE` của câu ngoài vào trong derived table trước khi materialize,
gọi là *derived condition pushdown*, nên không phải lúc nào materialize cũng chậm.)

⚠️ Điều này giải thích một nhận xét hay gặp: "dùng view chậm". View đơn giản (không aggregate) gần như
không tốn gì thêm, vì nó được ghép. View có `GROUP BY` trên bảng lớn mà bạn lọc lại một khách hàng thì
có thể phải gom nhóm cả bảng trước rồi mới lọc. Khi nghi ngờ, luôn `EXPLAIN`.

Một lý do để cố ý chọn `TEMPTABLE` mà tài liệu nêu: lock trên bảng gốc được nhả ngay sau khi bảng tạm
được tạo, trước khi câu lệnh xử lý xong, nên client khác bị chặn ít hơn.

### 2.6 Bảo mật: DEFINER và SQL SECURITY

Câu hỏi: người đọc view cần quyền gì? Chỉ quyền trên view, hay cả quyền trên bảng gốc? MySQL trả lời
bằng hai thuộc tính:

- `DEFINER = 'user'@'host'`: tài khoản "chủ" của view. Không ghi thì mặc định là người chạy
  `CREATE VIEW` (giống `DEFINER = CURRENT_USER`).
- `SQL SECURITY DEFINER | INVOKER`: khi view chạy, quyền trên các bảng gốc được kiểm tra theo ai.
  - `DEFINER` (mặc định): kiểm theo quyền của tài khoản DEFINER. Người đọc chỉ cần quyền `SELECT` trên
    chính view.
  - `INVOKER`: kiểm theo quyền của người đang đọc view (*invoker*). Người đọc phải có quyền trên cả
    bảng gốc.

Nhờ `SQL SECURITY DEFINER`, view thành công cụ che dữ liệu:

```sql
-- Chạy bằng root (hoặc tài khoản có đủ quyền)
CREATE VIEW v_customers_public AS
SELECT id, name, city FROM customers;          -- không có email, phone

CREATE USER 'analyst'@'%' IDENTIFIED BY 'Analyst#2026';
GRANT SELECT ON ch17.v_customers_public TO 'analyst'@'%';
-- analyst KHÔNG có quyền gì trên bảng customers
```

Đăng nhập bằng `analyst`:

```sql
SELECT * FROM ch17.v_customers_public;  -- được: 3 dòng id, name, city
SELECT * FROM ch17.customers;
-- ERROR 1142 (42000): SELECT command denied to user 'analyst'@'...' for table 'customers'
```

View vẫn đọc được bảng `customers` vì nó chạy với quyền của DEFINER (root). Nếu tạo view với `SQL
SECURITY INVOKER`, câu `SELECT` trên view của `analyst` cũng sẽ bị từ chối, vì giờ quyền được kiểm theo
`analyst`.

Một cách khác để giới hạn theo dòng: view lọc theo `CURRENT_USER()`. Trong view `SQL SECURITY
DEFINER`, `CURRENT_USER()` trả về DEFINER (không phải người đang đọc); trong view `SQL SECURITY
INVOKER` nó trả về người đang đọc. Nếu bạn cần biết ai đang đọc trong view DEFINER, dùng `USER()`
(tài khoản client đăng nhập). Đây là chi tiết dễ nhầm.

⚠️ Hai cái bẫy vận hành:

1. **DEFINER không tồn tại (orphan).** Nếu tài khoản DEFINER bị xoá, view `SQL SECURITY DEFINER` báo
   lỗi khi được dùng. MySQL 8.4 chặn việc này từ phía quản trị: `DROP USER` và `RENAME USER` **thất
   bại** nếu tài khoản đó đang là DEFINER của một stored object nào đó (trừ khi người chạy có quyền
   `SET_ANY_DEFINER` hoặc `ALLOW_NONEXISTENT_DEFINER`, khi đó `DROP USER` chạy được, chỉ còn
   warning). Hay gặp khi restore dump từ server khác:
   view mang `DEFINER='dev'@'%'` mà server mới không có tài khoản `dev`.
2. **DEFINER quá nhiều quyền.** View tạo bởi root mang quyền root. Ai được `SELECT` trên view sẽ đọc
   được mọi thứ view đọc. Tài liệu MySQL khuyên dùng `SQL SECURITY INVOKER` khi có thể, và khi dùng
   DEFINER thì đặt một tài khoản chỉ có đúng quyền cần thiết.

Chi tiết về tài khoản, `GRANT`, role ở [Chương 18](18-user-quyen-bao-mat.md).

### 2.7 Cập nhật dữ liệu qua view

Một số view *updatable* (cập nhật được): bạn chạy `UPDATE`, `DELETE`, thậm chí `INSERT` vào view, và
MySQL đổi dữ liệu ở bảng gốc. Điều kiện cốt lõi theo tài liệu: phải có **quan hệ một-một giữa dòng của
view và dòng của bảng gốc**. Nếu một dòng view là tổng của nhiều dòng gốc thì "sửa dòng này" không có
nghĩa.

View **không** updatable nếu chứa một trong các thứ sau (danh sách rút từ tài liệu MySQL 8.4):

- Hàm aggregate hoặc window function (`SUM`, `COUNT`, `MIN`, `MAX`...).
- `DISTINCT`, `GROUP BY`, `HAVING`, `UNION`/`UNION ALL`.
- Subquery trong danh sách cột (chi tiết: subquery không tương quan vẫn cho `UPDATE`/`DELETE` nhưng
  không cho `INSERT`; subquery tương quan thì không cho gì cả).
- Subquery trong `WHERE` tham chiếu tới một bảng trong `FROM`.
- Tham chiếu tới một view không updatable trong `FROM`.
- Chỉ gồm giá trị hằng (không có bảng gốc nào để sửa).
- `ALGORITHM = TEMPTABLE`.
- Một số kiểu join (outer join...; xem dưới).

Ví dụ với view lọc khách hàng ở Hà Nội:

```sql
CREATE VIEW v_hn_customers AS
SELECT id, name, email, city FROM customers WHERE city = 'Hà Nội';

UPDATE v_hn_customers SET name = 'An Nguyễn' WHERE id = 1;   -- được: đổi bảng customers
SELECT name FROM customers WHERE id = 1;                      -- An Nguyễn

UPDATE v_hn_customers SET name = 'Bình 2' WHERE id = 2;
-- Query OK, 0 rows affected: dòng id=2 (HCM) không nằm trong view nên không bị đụng tới
```

Server biết sẵn view có updatable không, ghi ở cột `IS_UPDATABLE`:

```sql
SELECT TABLE_NAME, IS_UPDATABLE, CHECK_OPTION, SECURITY_TYPE
FROM INFORMATION_SCHEMA.VIEWS WHERE TABLE_SCHEMA = 'ch17';
-- v_customer_revenue (nếu còn) có IS_UPDATABLE = NO vì có GROUP BY
```

Sửa view không updatable:

```sql
CREATE OR REPLACE VIEW v_customer_revenue (customer_id, paid_total) AS
SELECT customer_id, SUM(total) FROM orders WHERE status = 'paid' GROUP BY customer_id;

UPDATE v_customer_revenue SET paid_total = 0 WHERE customer_id = 1;
-- ERROR 1288 (HY000): The target table v_customer_revenue of the UPDATE is not updatable
```

**INSERT qua view** còn đòi thêm (view khi đó gọi là *insertable*):

- Không có tên cột trùng.
- View phải chứa mọi cột của bảng gốc không có giá trị mặc định (ở đây `customers.phone` cho phép
  NULL nên không bắt buộc, còn `id`, `name`, `email`, `city` là `NOT NULL` không default nên view
  phải có đủ).
- Các cột của view phải là tham chiếu cột thuần, không phải biểu thức như `price * 2`, `UPPER(name)`.

Một view có cột biểu thức thì không insertable, nhưng vẫn `UPDATE` được các cột không phải biểu thức.

**View có JOIN.** View nhiều bảng có thể updatable nếu xử lý được bằng `MERGE` và dùng *inner join*.
Mỗi câu `UPDATE` chỉ được sửa cột của một bảng; `DELETE` từ join view thì không được:

```sql
UPDATE v_paid_orders SET total = 750.00 WHERE id = 1;      -- được: chỉ sửa cột của orders
UPDATE v_paid_orders SET total = 750.00, customer = 'X' WHERE id = 1;
-- ERROR 1393 (HY000): Can not modify more than one base table through a join view 'ch17.v_paid_orders'
DELETE FROM v_paid_orders WHERE id = 1;
-- ERROR 1395 (HY000): Can not delete from join view 'ch17.v_paid_orders'
UPDATE v_paid_orders SET total = 700.00 WHERE id = 1;      -- trả lại
```

### 2.8 WITH CHECK OPTION: không cho dòng "trốn" khỏi view

Nhìn lại view `v_hn_customers` (lọc `city = 'Hà Nội'`). Câu sau là hợp lệ:

```sql
UPDATE v_hn_customers SET city = 'HCM' WHERE id = 3;
-- Query OK, 1 row affected
SELECT * FROM v_hn_customers;   -- Chi biến mất khỏi view
UPDATE customers SET city = 'Hà Nội' WHERE id = 3;   -- trả lại
```

Bạn sửa một dòng qua view, và dòng đó tự "biến mất" khỏi chính view đó. Tương tự, có thể `INSERT` qua
view một dòng không thoả điều kiện của view. Nếu view được dùng để giới hạn "người này chỉ được thao
tác khách ở Hà Nội", đây là lỗ hổng. `WITH CHECK OPTION` chặn nó: mọi `INSERT`/`UPDATE` qua view phải
cho ra dòng thoả `WHERE` của view.

```sql
CREATE OR REPLACE VIEW v_hn_customers AS
SELECT id, name, email, city FROM customers WHERE city = 'Hà Nội'
WITH CHECK OPTION;

UPDATE v_hn_customers SET city = 'HCM' WHERE id = 3;
-- ERROR 1369 (HY000): CHECK OPTION failed 'ch17.v_hn_customers'

INSERT INTO v_hn_customers (id, name, email, city) VALUES (4, 'Dũng', 'dung@example.com', 'Huế');
-- ERROR 1369 (HY000): CHECK OPTION failed 'ch17.v_hn_customers'

INSERT INTO v_hn_customers (id, name, email, city) VALUES (4, 'Dũng', 'dung@example.com', 'Hà Nội');
-- được
DELETE FROM customers WHERE id = 4;   -- dọn
```

Khi view xây trên view khác, có hai mức:

- `WITH CASCADED CHECK OPTION` (mặc định khi chỉ ghi `WITH CHECK OPTION`): kiểm điều kiện của view
  này **và** điều kiện của mọi view bên dưới, kể cả view bên dưới không có check option.
- `WITH LOCAL CHECK OPTION`: kiểm điều kiện của view này; với các view bên dưới, chỉ kiểm những view
  nào tự có check option.

Ví dụ trong tài liệu:

```sql
CREATE TABLE t1 (a INT);
CREATE VIEW v1 AS SELECT * FROM t1 WHERE a < 2 WITH CHECK OPTION;
CREATE VIEW v2 AS SELECT * FROM v1 WHERE a > 0 WITH LOCAL CHECK OPTION;
CREATE VIEW v3 AS SELECT * FROM v1 WHERE a > 0 WITH CASCADED CHECK OPTION;

INSERT INTO v2 VALUES (2);   -- ERROR 1369: CHECK OPTION failed 'ch17.v2'
INSERT INTO v3 VALUES (2);   -- ERROR 1369: CHECK OPTION failed 'ch17.v3'
```

Cả hai đều lỗi: `v2` kiểm `a > 0` (đúng), rồi đi xuống `v1`, `v1` có check option nên kiểm `a < 2`
(sai). Khác biệt chỉ lộ ra khi view bên dưới **không** có check option: khi đó `LOCAL` bỏ qua điều
kiện của nó, còn `CASCADED` vẫn kiểm.

### 2.9 Không có materialized view trong MySQL

*Materialized view* là view **lưu sẵn kết quả** thành dữ liệu thật trên đĩa, đọc nhanh như một bảng,
và được làm mới (*refresh*) định kỳ hoặc theo yêu cầu. Nó hữu ích cho báo cáo tổng hợp tốn kém.

- MySQL 8.4 **không có** materialized view. Cách làm tương đương: tạo một bảng tổng hợp thường (ví dụ
  `daily_revenue`) rồi làm mới bằng event (mục 8), bằng job của ứng dụng, hoặc cập nhật dần bằng
  trigger (mục 7).
- PostgreSQL có `CREATE MATERIALIZED VIEW` và `REFRESH MATERIALIZED VIEW` (thêm `CONCURRENTLY` để
  không chặn người đọc trong lúc làm mới; điều kiện là materialized view có một unique index).

### 2.10 Đối chiếu PostgreSQL về view

| Tiêu chí | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| `SELECT *` trong view | Mở thành danh sách cột lúc tạo | Cũng mở lúc tạo |
| Xoá cột mà view dùng | `ALTER TABLE` vẫn chạy, view hỏng khi dùng | Bị chặn: báo lỗi vì có object phụ thuộc (cần `CASCADE` để xoá luôn view) |
| View updatable | Theo các quy tắc ở mục 2.7 | "Simple view" tự động updatable; view phức tạp thì dùng trigger `INSTEAD OF` hoặc rule |
| Trigger trên view | Không | Có, loại `INSTEAD OF` |
| Bảo mật | `SQL SECURITY DEFINER` (mặc định) / `INVOKER` | Mặc định kiểm quyền bảng gốc theo chủ view; từ PostgreSQL 15 có tuỳ chọn `security_invoker` |
| Materialized view | Không | Có |

Điểm đáng chú ý: PostgreSQL theo dõi phụ thuộc giữa object nên chặn bạn làm hỏng view; MySQL thì để
bạn làm hỏng rồi mới báo khi dùng. Đây là một lý do để có bước kiểm tra view trong quy trình migration
MySQL ([Chương 20](20-thay-doi-schema-migration.md)).

## 3. Stored procedure

### 3.1 Procedure đầu tiên và chuyện DELIMITER

*Stored procedure* là một chương trình nhỏ viết bằng SQL, lưu trong database, gọi bằng `CALL`. Thân
procedure thường là một khối `BEGIN ... END` chứa nhiều câu lệnh, mỗi câu kết thúc bằng `;`.

Vấn đề: client `mysql` cũng dùng `;` để biết "hết một câu, gửi lên server". Nếu bạn gõ thẳng một
procedure nhiều câu, client sẽ cắt ở dấu `;` đầu tiên trong thân và gửi một câu `CREATE PROCEDURE` dở
dang lên server. Lệnh `DELIMITER` của client (không phải lệnh SQL, server không biết nó) đổi dấu kết
thúc tạm thời:

```sql
DELIMITER //

CREATE PROCEDURE p_hello()
BEGIN
  SELECT 'Xin chào từ procedure' AS msg;
  SELECT COUNT(*) AS so_don FROM orders;
END//

DELIMITER ;

CALL p_hello();
-- trả về hai result set:
-- msg: 'Xin chào từ procedure'
-- so_don: 4
```

⚠️ `DELIMITER` chỉ cần khi gõ trong client `mysql` hoặc chạy file `.sql` bằng client đó. Khi gửi từ
ứng dụng (PDO, Laravel migration bằng `DB::unprepared(...)`), mỗi lần gửi đã là một câu trọn vẹn nên
**không** viết `DELIMITER`; viết vào sẽ bị lỗi cú pháp vì server không hiểu từ này.

Một procedure có thể trả về **result set** (như trên, bằng `SELECT` không có `INTO`), thậm chí nhiều
result set. Đây là điểm khác lớn với stored function (mục 4), vốn không được trả result set.

Quản lý procedure:

```sql
SHOW CREATE PROCEDURE p_hello\G
SHOW PROCEDURE STATUS WHERE Db = 'ch17';
SELECT ROUTINE_NAME, ROUTINE_TYPE, DEFINER, SECURITY_TYPE
FROM INFORMATION_SCHEMA.ROUTINES WHERE ROUTINE_SCHEMA = 'ch17';

DROP PROCEDURE IF EXISTS p_hello;
```

`ALTER PROCEDURE` chỉ đổi được các đặc tính (như `COMMENT`, `SQL SECURITY`), không đổi được thân. Muốn
sửa thân: `DROP` rồi `CREATE` lại. MySQL 8.4 có `CREATE PROCEDURE IF NOT EXISTS` nhưng không có `CREATE
OR REPLACE PROCEDURE` (PostgreSQL có `CREATE OR REPLACE FUNCTION/PROCEDURE`).

### 3.2 Tham số IN, OUT, INOUT

Cú pháp tham số: `[IN | OUT | INOUT] tên kiểu`. Không ghi thì là `IN`.

| Loại | Chiều | Giá trị ban đầu trong procedure | Người gọi thấy thay đổi? |
|---|---|---|---|
| `IN` | Vào | Giá trị người gọi truyền | Không |
| `OUT` | Ra | `NULL` | Có |
| `INOUT` | Vào và ra | Giá trị người gọi truyền | Có |

Với `OUT`/`INOUT`, người gọi phải truyền một **biến** (ở client là biến `@user`) để nhận kết quả:

```sql
DELIMITER //
CREATE PROCEDURE p_customer_stats(
  IN  p_customer_id INT,
  OUT p_order_count INT,
  OUT p_paid_total  DECIMAL(12,2)
)
BEGIN
  SELECT COUNT(*), COALESCE(SUM(CASE WHEN status = 'paid' THEN total END), 0)
  INTO p_order_count, p_paid_total
  FROM orders
  WHERE customer_id = p_customer_id;
END//
DELIMITER ;

CALL p_customer_stats(1, @cnt, @paid);
SELECT @cnt, @paid;
-- @cnt = 2, @paid = 700.00   (khách 1 có đơn 1 'paid' 700 và đơn 2 'new' 3000)

CALL p_customer_stats(3, @cnt, @paid);
SELECT @cnt, @paid;
-- @cnt = 1, @paid = 0.00     (đơn duy nhất của khách 3 đã huỷ)
```

`INOUT` ví dụ: tăng một bộ đếm.

```sql
DELIMITER //
CREATE PROCEDURE p_add(INOUT p_counter INT, IN p_step INT)
BEGIN
  SET p_counter = p_counter + p_step;
END//
DELIMITER ;

SET @c = 10;
CALL p_add(@c, 5);
SELECT @c;   -- 15
```

⚠️ Truyền một hằng vào vị trí `OUT`/`INOUT` (ví dụ `CALL p_add(10, 5)`) bị lỗi 1414
(`ER_SP_NOT_VAR_ARG`), thông báo dạng `OUT or INOUT argument 1 for routine ch17.p_add is not a
variable or NEW pseudo-variable in BEFORE trigger`.

Từ ứng dụng PHP, cách đơn giản nhất để lấy `OUT` là chạy hai câu trên cùng một kết nối:
`CALL p_customer_stats(1, @cnt, @paid)` rồi `SELECT @cnt, @paid`. Biến `@` sống theo kết nối (session)
nên hai câu phải đi cùng một connection (Chương 19 nói về connection pool và hệ quả của nó).

### 3.3 Ba loại biến: local, @user, system

Trong stored program bạn gặp ba thứ trông giống nhau nhưng khác hẳn:

| | Biến cục bộ (*local variable*) | Biến người dùng (*user-defined variable*) | Biến hệ thống (*system variable*) |
|---|---|---|---|
| Viết | `v_total` | `@total` | `@@sql_mode`, `@@GLOBAL.x` |
| Khai báo | `DECLARE v_total DECIMAL(12,2) DEFAULT 0;` | Không cần, gán là có | Có sẵn |
| Kiểu | Có kiểu cố định | Không khai báo kiểu, lấy theo giá trị gán | Theo định nghĩa |
| Phạm vi | Khối `BEGIN ... END` chứa nó | Cả session, còn lại sau khi procedure kết thúc | Session hoặc toàn server |
| Dùng ở | Chỉ trong stored program | Ở đâu cũng được | Ở đâu cũng được |

```sql
DELIMITER //
CREATE PROCEDURE p_vars()
BEGIN
  DECLARE v_count INT DEFAULT 0;          -- local: phải DECLARE ở đầu khối
  SELECT COUNT(*) INTO v_count FROM customers;
  SET @last_count = v_count;              -- @user: rò ra ngoài procedure
  SELECT v_count AS local_value;
END//
DELIMITER ;

CALL p_vars();          -- local_value = 3
SELECT @last_count;     -- 3: biến @ vẫn còn sau khi procedure kết thúc
SELECT v_count;         -- ERROR 1054: Unknown column 'v_count' in 'field list'
```

Quy tắc của `DECLARE` (theo tài liệu):

- Chỉ dùng được bên trong `BEGIN ... END`, ở **đầu khối**, trước mọi câu lệnh khác.
- Thứ tự bắt buộc: khai báo biến và condition trước, rồi cursor, rồi handler.
- Không có `DEFAULT` thì giá trị ban đầu là `NULL`.
- Phạm vi là khối khai báo nó và các khối lồng bên trong (trừ khối lồng tự khai báo biến trùng tên).

⚠️ **Trùng tên biến với tên cột.** Nếu một biến cục bộ (hoặc tham số) trùng tên một cột, MySQL hiểu tên
đó là **biến**, không phải cột. Câu sau trông vô hại nhưng sai hoàn toàn:

```sql
DELIMITER //
CREATE PROCEDURE p_bad(IN status VARCHAR(20))
BEGIN
  SELECT COUNT(*) FROM orders WHERE status = status;   -- so sánh tham số với chính nó!
END//
DELIMITER ;

CALL p_bad('paid');   -- trả 4 (mọi dòng), không phải 2
DROP PROCEDURE p_bad;
```

Tài liệu nêu rõ: khi một câu SQL tham chiếu một tên vừa là cột vừa là biến, MySQL hiểu đó là biến (tham
số của procedure cũng là một biến như vậy). Quy ước phòng thân: đặt tiền tố
`p_` cho tham số, `v_` cho biến cục bộ, như các ví dụ trong chương.

⚠️ **Biến `@` gõ sai tên không báo lỗi.** `SELECT @totl` (gõ thiếu chữ) trả `NULL` chứ không báo "biến
không tồn tại". Đây là lý do nên dùng biến cục bộ trong stored program, và chỉ dùng `@` để trao đổi với
bên ngoài.

### 3.4 SELECT ... INTO: đưa kết quả vào biến

`SELECT cột1, cột2 INTO biến1, biến2 FROM ...` gán một dòng kết quả vào biến. Ba trường hợp theo tài
liệu:

- Đúng một dòng: gán bình thường.
- Không có dòng nào: có warning mã 1329 (`No data`), **biến giữ nguyên giá trị cũ**.
- Nhiều hơn một dòng: lỗi 1172 (`Result consisted of more than one row`).

⚠️ Trường hợp thứ hai là bẫy: nếu biến đã có giá trị từ lần trước (ví dụ trong vòng lặp), một lần
`SELECT INTO` không tìm thấy gì sẽ để lại giá trị cũ và code của bạn tưởng là tìm thấy. Cách an toàn:
gán `NULL` cho biến ngay trước câu `SELECT INTO`, hoặc dùng `SET v = (SELECT ...)`, vì subquery vô
hướng không có dòng thì trả `NULL`.

### 3.5 Điều khiển luồng: IF, CASE, vòng lặp

MySQL có đủ cấu trúc điều khiển cơ bản. Lưu ý: không có vòng `FOR` (tài liệu ghi rõ phần này của chuẩn
SQL:2003 chưa được hỗ trợ).

**IF:**

```sql
IF điều_kiện THEN
  ...
ELSEIF điều_kiện_khác THEN
  ...
ELSE
  ...
END IF;
```

**CASE** (câu lệnh, khác với biểu thức `CASE` ở Chương 06):

```sql
CASE v_status
  WHEN 'new'  THEN SET v_label = 'Mới';
  WHEN 'paid' THEN SET v_label = 'Đã thanh toán';
  ELSE SET v_label = 'Khác';
END CASE;
```

⚠️ Câu lệnh `CASE` không có `ELSE` mà không nhánh nào khớp thì **báo lỗi** 1339 `Case not found for
CASE statement`, khác với biểu thức `CASE` (trả `NULL`). Luôn viết `ELSE`, kể cả `ELSE BEGIN END;`.

**Vòng lặp:** ba kiểu, đều có thể gắn *nhãn* (label) để thoát hoặc nhảy vòng:

| Cú pháp | Kiểm điều kiện | Ghi chú |
|---|---|---|
| `WHILE cond DO ... END WHILE;` | Trước mỗi vòng | Có thể không chạy lần nào |
| `REPEAT ... UNTIL cond END REPEAT;` | Sau mỗi vòng | Chạy ít nhất một lần |
| `nhan: LOOP ... END LOOP nhan;` | Không tự kiểm | Phải tự thoát bằng `LEAVE nhan` |

`LEAVE nhan` thoát khỏi khối/vòng mang nhãn đó (như `break`); `ITERATE nhan` nhảy sang vòng tiếp theo
(như `continue`, chỉ dùng trong vòng lặp).

Ví dụ: tổng các số lẻ từ 1 tới n, viết bằng `LOOP` để thấy cả `LEAVE` lẫn `ITERATE`:

```sql
DELIMITER //
CREATE PROCEDURE p_sum_odd(IN p_n INT, OUT p_sum INT)
BEGIN
  DECLARE v_i INT DEFAULT 0;
  SET p_sum = 0;
  vong: LOOP
    SET v_i = v_i + 1;
    IF v_i > p_n THEN
      LEAVE vong;              -- thoát vòng
    END IF;
    IF v_i % 2 = 0 THEN
      ITERATE vong;            -- bỏ qua số chẵn
    END IF;
    SET p_sum = p_sum + v_i;
  END LOOP vong;
END//
DELIMITER ;

CALL p_sum_odd(10, @s);
SELECT @s;   -- 25  (1+3+5+7+9)
```

Viết lại bằng `WHILE` gọn hơn:

```sql
-- thân procedure tương đương
SET p_sum = 0;
WHILE v_i < p_n DO
  SET v_i = v_i + 1;
  IF v_i % 2 = 1 THEN SET p_sum = p_sum + v_i; END IF;
END WHILE;
```

⚠️ Vòng lặp trong SQL để xử lý **từng dòng** dữ liệu gần như luôn chậm hơn một câu SQL xử lý cả tập
(*set-based*). Ví dụ trên chỉ để học cú pháp; tổng số lẻ từ 1 tới n là bài toán nên giải bằng công
thức hoặc một câu `SELECT`. Vòng lặp hợp lý khi cần làm theo lô (ví dụ xoá 1000 dòng một lần cho tới
hết, mục 8.4).

### 3.6 Procedure gọi procedure, và đệ quy

Procedure gọi được procedure khác bằng `CALL`, truyền biến cục bộ hoặc tham số của mình vào vị trí
`OUT`/`INOUT`. Procedure gọi đệ quy chính nó thì bị chặn mặc định: biến hệ thống
`max_sp_recursion_depth` có mặc định là `0`, nghĩa là không cho đệ quy. Stored function thì không bao
giờ được đệ quy. Bài toán dạng cây (danh mục cha con) nên dùng recursive CTE
([Chương 09](09-subquery-cte-union.md)) thay vì procedure đệ quy.

### 3.7 Những thứ cần biết thêm về môi trường chạy

- **`sql_mode` bị "đóng băng".** MySQL lưu `sql_mode` tại thời điểm tạo routine và luôn chạy routine
  với `sql_mode` đó, bất kể session gọi đang dùng `sql_mode` nào. Routine tạo trên server có
  `sql_mode` lỏng sẽ tiếp tục chạy lỏng sau khi bạn siết `sql_mode` của server. Xem bằng cột
  `SQL_MODE` của `INFORMATION_SCHEMA.ROUTINES`.
- **Database mặc định.** Khi routine chạy, MySQL tạm `USE` database chứa routine (và trả lại sau khi
  xong). Không được viết `USE` trong routine. Bảng ở database khác phải ghi `db.bang`.
- **Transaction.** Procedure được dùng `START TRANSACTION`, `COMMIT`, `ROLLBACK` (mục 6.5). Lưu ý:
  trong stored program, `BEGIN` luôn được hiểu là mở khối `BEGIN ... END`, nên phải dùng `START
  TRANSACTION`.
- **Quyền.** Cần quyền `CREATE ROUTINE` để tạo; người tạo mặc định được tự cấp `ALTER ROUTINE` và
  `EXECUTE` trên routine đó. Người gọi cần `EXECUTE`. `DEFINER`/`SQL SECURITY` hoạt động giống view
  (mục 2.6): mặc định `SQL SECURITY DEFINER`.
- **Không có debugger.** Tài liệu ghi thẳng: không có công cụ debug cho stored routine. Cách debug
  phổ biến là chèn `SELECT` in giá trị trung gian, hoặc ghi vào một bảng log.

## 4. Stored function

### 4.1 Function khác procedure ở đâu

*Stored function* trả về **một giá trị** và được dùng **trong biểu thức**, giống hàm có sẵn như
`UPPER()` hay `ROUND()`:

```sql
DELIMITER //
CREATE FUNCTION f_shipping_fee(p_total DECIMAL(10,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC
NO SQL
BEGIN
  IF p_total >= 1000 THEN
    RETURN 0;          -- đơn từ 1000 trở lên: miễn phí ship
  END IF;
  RETURN 30;
END//
DELIMITER ;

SELECT id, total, f_shipping_fee(total) AS ship FROM orders ORDER BY id;
-- id | total   | ship
--  1 |  700.00 | 30.00
--  2 | 3000.00 |  0.00
--  3 |  200.00 | 30.00
--  4 |  500.00 | 30.00
```

| | Procedure | Function |
|---|---|---|
| Gọi bằng | `CALL p(...)` | Trong biểu thức: `SELECT f(x)`, `WHERE f(x) = ...` |
| Tham số | `IN`, `OUT`, `INOUT` | Chỉ `IN` (không ghi chữ `IN`) |
| Trả về | Qua `OUT`, hoặc result set | Đúng một giá trị qua `RETURN`, bắt buộc có `RETURNS kiểu` |
| Trả result set (`SELECT` không `INTO`) | Được | Không được |
| `COMMIT`/`ROLLBACK`/`START TRANSACTION` | Được | Không được |
| Dynamic SQL (`PREPARE`/`EXECUTE`) | Được | Không được |
| Đệ quy | Được nếu tăng `max_sp_recursion_depth` | Không bao giờ |

Function chạy tới cuối mà không gặp `RETURN` sẽ lỗi 1321 `FUNCTION ... ended without RETURN`.

### 4.2 DETERMINISTIC, NO SQL, READS SQL DATA và lỗi 1418

Khi tạo function, bạn khai báo các *characteristic* (đặc tính):

- `DETERMINISTIC` / `NOT DETERMINISTIC` (mặc định): cùng đầu vào có luôn cho cùng kết quả không.
- `CONTAINS SQL` (mặc định) / `NO SQL` / `READS SQL DATA` / `MODIFIES SQL DATA`: function có đọc/ghi
  dữ liệu không.

Tài liệu nhấn mạnh hai điều: MySQL **tin lời bạn**, không kiểm tra function có thật sự deterministic
hay không; và nhóm `NO SQL`/`READS SQL DATA`... chỉ là thông tin tham khảo, server không dùng chúng để
cấm câu lệnh nào. Khai báo sai `DETERMINISTIC` cho một hàm không deterministic có thể khiến optimizer
chọn kế hoạch sai và cho kết quả không mong đợi.

Vì sao lại phải khai báo? Vì **binary log** (nhật ký thay đổi dùng cho replication và khôi phục, xem
[Chương 22](22-replication-ha.md)). Binary log được bật mặc định trong MySQL 8. Khi đó, mặc định MySQL
**từ chối** tạo function không khai báo ít nhất một trong `DETERMINISTIC`, `NO SQL`, `READS SQL DATA`:

```sql
DELIMITER //
CREATE FUNCTION f_now_label() RETURNS VARCHAR(40)
BEGIN
  RETURN CONCAT('Lúc ', NOW());
END//
DELIMITER ;
-- ERROR 1418 (HY000): This function has none of DETERMINISTIC, NO SQL, or READS SQL DATA in
-- its declaration and binary logging is enabled (you *might* want to use the less safe
-- log_bin_trust_function_creators variable)
```

Lý do: với binary log dạng statement, replica chạy lại *câu gọi* function; nếu function cho kết quả
khác nhau ở hai nơi (dùng `UUID()`, đọc dữ liệu khác nhau...) thì dữ liệu source và replica lệch nhau.
Cách xử lý đúng là khai báo trung thực (function trên chỉ đọc giờ, có thể khai `NO SQL`; nó không
deterministic nên đừng khai `DETERMINISTIC`). Đặt `log_bin_trust_function_creators = 1` (mặc định 0)
tắt bước kiểm tra này: đó là "tôi tự chịu trách nhiệm", chỉ dùng khi hiểu rõ, ví dụ khi binlog dạng
`ROW` (mặc định của MySQL 8) vì khi đó thay đổi được ghi theo từng dòng chứ không theo câu gọi.

### 4.3 Function đọc bảng và cái giá hiệu năng

Function có thể đọc bảng:

```sql
DELIMITER //
CREATE FUNCTION f_customer_paid(p_customer_id INT)
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
  DECLARE v_sum DECIMAL(12,2);
  SELECT COALESCE(SUM(total), 0) INTO v_sum
  FROM orders
  WHERE customer_id = p_customer_id AND status = 'paid';
  RETURN v_sum;
END//
DELIMITER ;

SELECT id, name, f_customer_paid(id) AS paid FROM customers ORDER BY id;
-- 1 | An   | 700.00
-- 2 | Bình | 200.00
-- 3 | Chi  |   0.00
```

Gọn, dễ đọc, nhưng ⚠️ hàm chạy **một lần cho mỗi dòng**, và mỗi lần là một câu `SELECT` riêng. Với
100 000 khách hàng, đó là 100 000 câu truy vấn con: đúng bản chất của lỗi N+1 (Chương 19), chỉ là
nằm trong database. Câu `JOIN` + `GROUP BY` (Chương 07, 08) làm việc này trong một lượt. Thêm nữa,
optimizer không "nhìn vào trong" function được, nên không gộp hay viết lại nó như với subquery.

⚠️ Dùng function trên cột trong `WHERE`, ví dụ `WHERE f_normalize(email) = 'x'`, khiến index trên
`email` không dùng được (cùng lý do với `WHERE LOWER(email) = ...` ở Chương 11). Nếu thật sự cần,
dùng *functional index* hoặc generated column có index; generated column và functional index chỉ được
dùng hàm có sẵn deterministic, không dùng stored function.

⚠️ Function (và trigger) **không được sửa** bảng đang được câu lệnh gọi nó đọc hoặc ghi. Ví dụ
`UPDATE orders SET total = f_x(id)` mà `f_x` lại `UPDATE orders` sẽ lỗi 1442 `Can't update table
'orders' in stored function/trigger because it is already used by statement which invoked this
stored function/trigger.`

## 5. Cursor: duyệt kết quả từng dòng

### 5.1 Cursor là gì

`SELECT ... INTO` chỉ nhận được một dòng. Khi cần đi qua **nhiều dòng** của một kết quả, từng dòng
một, bạn dùng *cursor* (con trỏ): một "đầu đọc" trỏ vào kết quả của một câu `SELECT`, mỗi lần `FETCH`
lấy ra một dòng rồi tiến tới dòng kế.

Cursor của MySQL có ba tính chất (theo tài liệu):

- *Read only*: chỉ đọc, không `UPDATE ... WHERE CURRENT OF` được như một số hệ khác.
- *Nonscrollable*: chỉ đi một chiều từ đầu tới cuối, không nhảy, không lùi.
- *Asensitive*: server có thể tạo hoặc không tạo bản sao của kết quả, nên đừng dựa vào việc cursor
  "thấy" hay "không thấy" thay đổi xảy ra trong lúc đang duyệt.

Cursor chỉ dùng được bên trong stored program.

### 5.2 Bốn bước: DECLARE, OPEN, FETCH, CLOSE

```sql
-- (Nếu đã đổi tên khách 1 ở mục 2.7, chạy lại dữ liệu mẫu mục 1.3 trước.)
DELIMITER //
CREATE PROCEDURE p_hn_names(OUT p_names VARCHAR(500))
BEGIN
  DECLARE v_done BOOLEAN DEFAULT FALSE;                -- 1. biến trước
  DECLARE v_name VARCHAR(50);
  DECLARE cur CURSOR FOR                                -- 2. rồi cursor
    SELECT name FROM customers WHERE city = 'Hà Nội' ORDER BY id;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = TRUE;   -- 3. rồi handler

  SET p_names = '';
  OPEN cur;                                             -- chạy câu SELECT
  doc: LOOP
    FETCH cur INTO v_name;                              -- lấy một dòng
    IF v_done THEN                                      -- hết dòng: handler đã đặt v_done
      LEAVE doc;
    END IF;
    SET p_names = CONCAT_WS(', ', NULLIF(p_names, ''), v_name);
  END LOOP doc;
  CLOSE cur;                                            -- giải phóng
END//
DELIMITER ;

CALL p_hn_names(@names);
SELECT @names;   -- 'An, Chi'
```

Cơ chế "hết dòng": khi `FETCH` không còn dòng nào, server phát ra *condition* (tình trạng) "No Data"
với SQLSTATE `'02000'`, thuộc nhóm `NOT FOUND`. Handler `CONTINUE HANDLER FOR NOT FOUND` bắt nó, đặt
`v_done = TRUE`, rồi chương trình chạy tiếp ở câu sau `FETCH`, nơi ta kiểm `v_done` và thoát vòng. Cơ
chế handler được giải thích đầy đủ ở mục 6.

Thứ tự khai báo bắt buộc: **biến/condition → cursor → handler**. Sai thứ tự thì `CREATE PROCEDURE` bị
từ chối ngay (lỗi 1337 `Variable or condition declaration after cursor or handler declaration` hoặc
1338 `Cursor declaration after handler declaration`).

⚠️ Ba cái bẫy với cursor:

1. **Kiểm `v_done` ngay sau `FETCH`.** Nếu xử lý `v_name` trước rồi mới kiểm, dòng cuối sẽ bị xử lý
   hai lần (lần `FETCH` thất bại không đổi `v_name`, biến vẫn giữ giá trị dòng trước).
2. **Handler `NOT FOUND` bắt cả những thứ khác.** Một `SELECT ... INTO` không tìm thấy dòng nào nằm
   trong vòng lặp cũng phát `NOT FOUND`, kích hoạt cùng handler, đặt `v_done = TRUE` và vòng lặp thoát
   sớm một cách khó hiểu. Tài liệu khuyên: đặt thao tác đó trong một khối `BEGIN ... END` riêng có
   handler riêng.
3. **Cursor là xử lý từng dòng.** Ví dụ trên chỉ để học; một câu `SELECT GROUP_CONCAT(name ORDER BY
   id SEPARATOR ', ') FROM customers WHERE city = 'Hà Nội'` làm cùng việc nhanh hơn và ngắn hơn.
   Cursor hợp lý khi với mỗi dòng bạn phải làm một việc không diễn đạt được bằng một câu SQL, ví dụ
   chạy một câu SQL động khác nhau cho mỗi bảng (kết hợp với `PREPARE`, mục 9).

## 6. Xử lý lỗi trong stored program

### 6.1 Condition, và chuyện gì xảy ra khi không xử lý

Mỗi câu lệnh có thể sinh ra *condition*: lỗi, cảnh báo, hoặc "không có dữ liệu". Mỗi condition có một
**mã lỗi MySQL** (số, ví dụ 1062) và một **SQLSTATE** (chuỗi 5 ký tự theo chuẩn SQL, ví dụ `'23000'`).
Hai ký tự đầu của SQLSTATE cho biết *lớp*:

| SQLSTATE bắt đầu bằng | Lớp | Từ khoá đại diện trong handler |
|---|---|---|
| `'00'` | Thành công | (không phải condition lỗi) |
| `'01'` | Cảnh báo | `SQLWARNING` |
| `'02'` | Không có dữ liệu | `NOT FOUND` |
| Còn lại | Lỗi | `SQLEXCEPTION` |

Nếu không có handler nào, tài liệu nêu hành vi mặc định:

- `SQLEXCEPTION`: chương trình **dừng** ngay tại câu lỗi (như có `EXIT` handler); nếu nó được gọi từ
  một stored program khác thì lỗi được chuyển lên chương trình gọi.
- `SQLWARNING`: chạy tiếp.
- `NOT FOUND`: chạy tiếp (trừ khi do `SIGNAL`/`RESIGNAL` phát ra, khi đó dừng).

### 6.2 DECLARE ... HANDLER

```sql
DECLARE {CONTINUE | EXIT} HANDLER
  FOR condition_value [, condition_value] ...
  câu_lệnh_hoặc_khối_BEGIN_END;

-- condition_value có thể là:
--   1062                  mã lỗi MySQL
--   SQLSTATE '23000'      giá trị SQLSTATE
--   ten_condition         tên đặt bằng DECLARE ... CONDITION
--   SQLWARNING | NOT FOUND | SQLEXCEPTION
```

- `CONTINUE`: chạy thân handler rồi tiếp tục ở câu **sau** câu gây lỗi.
- `EXIT`: chạy thân handler rồi **kết thúc khối `BEGIN ... END` chứa khai báo handler** (không phải
  kết thúc cả procedure, trừ khi handler khai ở khối ngoài cùng).
- `UNDO` có trong cú pháp nhưng chưa được hỗ trợ.

Ví dụ trong tài liệu, viết lại theo dữ liệu của chương: chèn trùng khoá thì ghi nhận rồi đi tiếp.

```sql
DELIMITER //
CREATE PROCEDURE p_handler_demo()
BEGIN
  DECLARE CONTINUE HANDLER FOR SQLSTATE '23000' SET @dup = 1;
  SET @dup = 0, @step = 1;
  INSERT INTO customers VALUES (10, 'Test', 't@example.com', NULL, 'Huế');
  SET @step = 2;
  INSERT INTO customers VALUES (10, 'Test', 't@example.com', NULL, 'Huế');  -- trùng khoá chính
  SET @step = 3;
END//
DELIMITER ;

CALL p_handler_demo();
SELECT @dup, @step;   -- 1, 3: lỗi đã được bắt, procedure chạy tới cuối
DELETE FROM customers WHERE id = 10;
```

Không có handler, procedure dừng ở `INSERT` thứ hai, `@step` là 2 và client nhận
`ERROR 1062 (23000): Duplicate entry '10' for key 'customers.PRIMARY'`.

Đặt tên cho condition để code dễ đọc:

```sql
DECLARE duplicate_key CONDITION FOR 1062;
DECLARE CONTINUE HANDLER FOR duplicate_key SET @dup = 1;
```

**Nhiều handler cùng khớp thì chọn cái nào?** Server tìm handler ở khối hiện tại trước, không có mới
ra khối ngoài. Trong cùng một khối, thứ tự ưu tiên: handler theo mã lỗi MySQL > handler theo SQLSTATE
> `SQLEXCEPTION` > `SQLWARNING`. Lưu ý hệ quả tài liệu nêu: handler ở khối trong cùng luôn thắng
handler ở khối ngoài, kể cả khi handler ngoài cụ thể hơn.

⚠️ `DECLARE CONTINUE HANDLER FOR SQLEXCEPTION BEGIN END;` (nuốt mọi lỗi rồi chạy tiếp) là mẫu code tệ
nhất trong stored program: lỗi biến mất, dữ liệu nằm ở trạng thái nửa vời, không ai biết. Nếu bắt
`SQLEXCEPTION`, thường là để dọn dẹp (rollback, ghi log) rồi **ném lại** bằng `RESIGNAL`.

### 6.3 SIGNAL: tự phát ra lỗi

`SIGNAL` là cách stored program "throw" một lỗi của riêng mình, giống `throw new Exception()` trong
PHP. Không có `SIGNAL`, người ta từng phải cố tình truy vấn một bảng không tồn tại để gây lỗi.

```sql
SIGNAL SQLSTATE '45000'
  SET MESSAGE_TEXT = 'Không đủ số dư', MYSQL_ERRNO = 5001;
```

- SQLSTATE `'45000'` nghĩa là "unhandled user-defined exception", giá trị chung cho lỗi tự định nghĩa.
  Không được dùng giá trị bắt đầu bằng `'00'`.
- `MESSAGE_TEXT`: thông báo; `MYSQL_ERRNO`: mã lỗi bạn chọn. Không đặt `MYSQL_ERRNO` thì với lỗi
  `'45000'` client nhận mã 1644 (`ER_SIGNAL_EXCEPTION`).
- `SIGNAL` cũng dùng được trong trigger (mục 7) để chặn một thao tác.

Phía PHP, lỗi do `SIGNAL` đến dưới dạng `PDOException` bình thường: `$e->getCode()` là SQLSTATE
(`'45000'`), `$e->errorInfo[1]` là mã MySQL, `$e->errorInfo[2]` là `MESSAGE_TEXT`.

### 6.4 RESIGNAL và GET DIAGNOSTICS

Bên trong handler:

- `RESIGNAL;` ném lại đúng lỗi đang được xử lý cho tầng ngoài (như `throw $e;` trong `catch`). Có thể
  sửa thông tin trước khi ném: `RESIGNAL SET MESSAGE_TEXT = 'Chuyển tiền thất bại';`.
- `GET DIAGNOSTICS` đọc chi tiết lỗi từ *diagnostics area* (vùng chẩn đoán, nơi server ghi lại kết quả
  của câu lệnh vừa chạy). Trong handler, dùng `GET STACKED DIAGNOSTICS` để đọc lỗi đã kích hoạt
  handler (vùng "stacked" chỉ tồn tại trong ngữ cảnh handler).

```sql
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
  GET STACKED DIAGNOSTICS CONDITION 1
    v_state = RETURNED_SQLSTATE,
    v_errno = MYSQL_ERRNO,
    v_msg   = MESSAGE_TEXT;
  -- ghi log, rollback..., rồi ném lại:
  RESIGNAL;
END;
```

(`v_state`, `v_errno`, `v_msg` là biến cục bộ đã `DECLARE` trước đó.)

### 6.5 Ghép lại: procedure chuyển tiền có transaction

Đây là ví dụ tổng hợp: kiểm tra đầu vào, transaction, khoá dòng, lỗi nghiệp vụ, rollback khi có lỗi.

```sql
DELIMITER //
CREATE PROCEDURE p_transfer(IN p_from INT, IN p_to INT, IN p_amount DECIMAL(12,2))
BEGIN
  DECLARE v_balance DECIMAL(12,2) DEFAULT NULL;

  -- Mọi lỗi (của MySQL hay do SIGNAL bên dưới): rollback rồi ném lại cho người gọi
  DECLARE EXIT HANDLER FOR SQLEXCEPTION
  BEGIN
    ROLLBACK;
    RESIGNAL;
  END;

  IF p_amount IS NULL OR p_amount <= 0 THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Số tiền phải lớn hơn 0';
  END IF;
  IF p_from = p_to THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Hai tài khoản phải khác nhau';
  END IF;

  START TRANSACTION;           -- không dùng BEGIN: trong stored program BEGIN là mở khối

  -- Khoá dòng tài khoản nguồn để không ai rút song song (Chương 15)
  SELECT balance INTO v_balance FROM accounts WHERE id = p_from FOR UPDATE;
  IF v_balance IS NULL THEN    -- không tìm thấy: SELECT INTO để nguyên NULL
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tài khoản nguồn không tồn tại';
  END IF;
  IF v_balance < p_amount THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Không đủ số dư';
  END IF;

  UPDATE accounts SET balance = balance - p_amount WHERE id = p_from;
  UPDATE accounts SET balance = balance + p_amount WHERE id = p_to;
  IF ROW_COUNT() = 0 THEN      -- số dòng bị UPDATE vừa rồi thay đổi
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tài khoản đích không tồn tại';
  END IF;

  COMMIT;
END//
DELIMITER ;
```

Chạy thử (bắt đầu từ An 1000.00, Bình 500.00):

```sql
CALL p_transfer(1, 2, 300);
SELECT id, balance FROM accounts;      -- 1: 700.00, 2: 800.00

CALL p_transfer(2, 1, 5000);
-- ERROR 1644 (45000): Không đủ số dư
CALL p_transfer(1, 99, 100);
-- ERROR 1644 (45000): Tài khoản đích không tồn tại
SELECT id, balance FROM accounts;      -- vẫn 1: 700.00, 2: 800.00 (cả hai lần đều đã rollback)
```

Đọc kỹ vài điểm:

- `SIGNAL` bên trong procedure cũng kích hoạt `EXIT HANDLER FOR SQLEXCEPTION` của chính procedure
  (SQLSTATE `'45000'` thuộc lớp lỗi). Handler rollback rồi `RESIGNAL` đưa nguyên thông báo ra ngoài.
- Không có `RESIGNAL` trong handler thì procedure kết thúc "êm", client nhận `Query OK` và tưởng
  chuyển tiền thành công. Đây là lỗi kinh điển.
- `SELECT ... INTO` không thấy dòng chỉ sinh `NOT FOUND` (không phải `SQLEXCEPTION`), nên không kích
  hoạt handler; ta tự kiểm `v_balance IS NULL`.
- ⚠️ Chỉ khoá tài khoản nguồn và cập nhật theo thứ tự "nguồn rồi đích" thì hai giao dịch chuyển ngược
  chiều nhau (A→B và B→A) cùng lúc có thể deadlock. Cách phổ biến là khoá cả hai dòng theo thứ tự `id`
  tăng dần trước khi cập nhật ([Chương 15](15-lock-deadlock.md)). Bài tập 2 cuối chương yêu cầu bạn
  sửa điều này.
- ⚠️ Procedure tự `START TRANSACTION`/`COMMIT` thì **không lồng được** vào transaction của ứng dụng:
  nếu ứng dụng đã mở transaction rồi `CALL p_transfer(...)`, câu `START TRANSACTION` bên trong sẽ
  commit ngầm transaction đang mở của ứng dụng (Chương 13). Phải thống nhất: hoặc procedure quản lý
  transaction, hoặc ứng dụng quản lý, không trộn.

Phía PHP:

```php
<?php
declare(strict_types=1);

// $pdo: kết nối PDO tới MySQL với PDO::ERRMODE_EXCEPTION (Chương 19)
function transfer(PDO $pdo, int $from, int $to, string $amount): void
{
    $stmt = $pdo->prepare('CALL p_transfer(?, ?, ?)');
    try {
        $stmt->execute([$from, $to, $amount]);
    } catch (PDOException $e) {
        if ($e->getCode() === '45000') {
            // lỗi nghiệp vụ do SIGNAL: errorInfo[2] là MESSAGE_TEXT
            throw new DomainException((string) $e->errorInfo[2], 0, $e);
        }
        throw $e; // lỗi khác (mất kết nối, deadlock 1213...) để tầng trên xử lý
    }
}
```

(`getCode()` của `PDOException` trả SQLSTATE dạng chuỗi nên so sánh `=== '45000'`.)

## 7. Trigger

### 7.1 Trigger là gì

*Trigger* là một đoạn code gắn với **một bảng**, được server **tự động** chạy mỗi khi có dòng bị
thêm, sửa hoặc xoá trong bảng đó. Không ai `CALL` trigger: nó "nổ" theo sự kiện, giống event listener.

```sql
CREATE [DEFINER = user] TRIGGER [IF NOT EXISTS] ten_trigger
  {BEFORE | AFTER} {INSERT | UPDATE | DELETE}
  ON ten_bang FOR EACH ROW
  [{FOLLOWS | PRECEDES} trigger_khac]
  than_trigger;
```

- *Thời điểm* (`trigger_time`): `BEFORE` chạy trước khi dòng được ghi, `AFTER` chạy sau.
- *Sự kiện* (`trigger_event`): `INSERT`, `UPDATE`, `DELETE`. Đây là **loại thao tác trên dòng**, không
  phải tên câu lệnh: trigger `INSERT` cũng chạy với `LOAD DATA` và `REPLACE`; trigger `DELETE` cũng
  chạy với `REPLACE` (khi nó xoá dòng cũ).
- `FOR EACH ROW`: MySQL chỉ có trigger **cấp dòng**. Câu `UPDATE` sửa 10 000 dòng thì trigger chạy
  10 000 lần. (PostgreSQL có thêm trigger cấp câu lệnh, `FOR EACH STATEMENT`.)
- Mỗi bảng có thể có nhiều trigger cùng thời điểm và sự kiện; mặc định chạy theo thứ tự tạo, đổi được
  bằng `FOLLOWS`/`PRECEDES`.
- Không gắn được trigger lên view hay bảng `TEMPORARY`. Tên trigger là duy nhất trong một database.

### 7.2 NEW và OLD

Trong thân trigger, hai tên đặc biệt cho phép đọc dòng đang được xử lý:

| Sự kiện | `OLD.cot` | `NEW.cot` |
|---|---|---|
| `INSERT` | Không có | Dòng sắp/vừa thêm |
| `UPDATE` | Dòng trước khi sửa | Dòng sau khi sửa |
| `DELETE` | Dòng sắp/vừa xoá | Không có |

- `OLD` luôn **chỉ đọc**.
- `NEW` sửa được bằng `SET NEW.cot = ...` nhưng **chỉ trong trigger `BEFORE`**. Trong `AFTER`, dòng
  đã được ghi rồi nên đổi `NEW` không còn ý nghĩa; viết `SET NEW.cot = ...` trong trigger `AFTER` thì
  `CREATE TRIGGER` bị từ chối với lỗi 1362 (`ER_TRG_CANT_CHANGE_ROW`, thông báo dạng `Updating of NEW
  row is not allowed in after trigger`). Trang `CREATE TRIGGER` của tài liệu chỉ nói câu `SET` đó "không
  có tác dụng", nhưng mã nguồn server kiểm tra ngay lúc phân tích câu lệnh và báo lỗi.
- Trong `BEFORE INSERT`, `NEW.id` của cột `AUTO_INCREMENT` là `0`, chưa phải giá trị sẽ được cấp.
  Muốn biết id thật thì dùng `AFTER INSERT`.

### 7.3 Ví dụ 1: chuẩn hoá dữ liệu bằng BEFORE

```sql
DELIMITER //
CREATE TRIGGER trg_customers_bi BEFORE INSERT ON customers
FOR EACH ROW
BEGIN
  SET NEW.email = LOWER(TRIM(NEW.email));
END//
DELIMITER ;

INSERT INTO customers (id, name, email, city) VALUES (5, 'Em', '  EM@Example.COM ', 'HCM');
SELECT email FROM customers WHERE id = 5;   -- 'em@example.com'
```

Lưu ý: trigger này chỉ chạy khi `INSERT`. Ai đó `UPDATE customers SET email = 'ABC@X.COM'` thì vẫn
lọt; muốn chặn cả hai đường phải có thêm `BEFORE UPDATE`. Tài liệu cũng lưu ý: các kiểm tra cơ bản về
kiểu của cột chạy **trước** trigger, nên không dùng `BEFORE` trigger để "sửa" một giá trị sai kiểu
thành đúng được.

### 7.4 Ví dụ 2: chặn thao tác không hợp lệ bằng SIGNAL

Quy tắc nghiệp vụ: đơn đã huỷ thì không được mở lại.

```sql
DELIMITER //
CREATE TRIGGER trg_orders_bu BEFORE UPDATE ON orders
FOR EACH ROW
BEGIN
  IF OLD.status = 'cancelled' AND NEW.status <> 'cancelled' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đã huỷ không được mở lại';
  END IF;
END//
DELIMITER ;

UPDATE orders SET status = 'new' WHERE id = 4;
-- ERROR 1644 (45000): Đơn đã huỷ không được mở lại
```

Lỗi trong trigger làm **cả câu lệnh** thất bại. Với bảng InnoDB, mọi thay đổi câu lệnh đó đã làm
(kể cả ở các dòng trước và trong trigger) được rollback. Ví dụ `UPDATE orders SET status = 'new'` (không
`WHERE`) sẽ không sửa dòng nào cả, vì dòng 4 làm cả câu thất bại.

⚠️ Với kiểm tra chỉ dựa trên giá trị của chính dòng mới (ví dụ `stock >= 0`), hãy dùng `CHECK`
constraint ([Chương 04](04-ddl-constraint.md)) thay vì trigger: khai báo, rõ ràng, nằm ngay trong
`SHOW CREATE TABLE`. Trigger chỉ cần khi quy tắc phụ thuộc giá trị cũ (`OLD`) hoặc bảng khác.

### 7.5 Ví dụ 3: ghi lịch sử (audit) bằng AFTER

```sql
CREATE TABLE order_status_history (
  id          BIGINT AUTO_INCREMENT PRIMARY KEY,
  order_id    INT          NOT NULL,
  old_status  VARCHAR(20),
  new_status  VARCHAR(20)  NOT NULL,
  changed_by  VARCHAR(100) NOT NULL,     -- tài khoản MySQL, không phải user của ứng dụng
  changed_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

DELIMITER //
CREATE TRIGGER trg_orders_au AFTER UPDATE ON orders
FOR EACH ROW
BEGIN
  IF NOT (OLD.status <=> NEW.status) THEN     -- <=> so sánh an toàn với NULL (Chương 06)
    INSERT INTO order_status_history (order_id, old_status, new_status, changed_by)
    VALUES (NEW.id, OLD.status, NEW.status, USER());
  END IF;
END//
DELIMITER ;

UPDATE orders SET status = 'paid' WHERE id = 2;
UPDATE orders SET total = 2900.00 WHERE id = 2;     -- không đổi status: không ghi lịch sử
SELECT order_id, old_status, new_status FROM order_status_history;
-- 2 | new | paid
```

Vì sao `AFTER` mà không phải `BEFORE`? `AFTER` chỉ chạy khi thao tác trên dòng đã thành công (tài
liệu: `AFTER` trigger chỉ chạy nếu mọi `BEFORE` trigger và thao tác trên dòng đều thành công), nên lịch
sử không ghi những thay đổi bị từ chối.

⚠️ `USER()` ở đây là tài khoản MySQL (`app@10.0.0.5`), mà ứng dụng web thường dùng một tài khoản cho
mọi người dùng. Trigger không biết "user id 42 của ứng dụng" là ai. Mẹo hay gặp: ứng dụng `SET
@app_user_id = 42` đầu mỗi request rồi trigger đọc `@app_user_id`; nhưng với connection pool hoặc kết
nối dùng lại (Chương 19), biến này có thể còn sót từ request trước nếu quên đặt lại.

### 7.6 Trigger chạy trong transaction nào

Trigger chạy **bên trong câu lệnh** đã kích hoạt nó, nên nằm trong cùng transaction. Hệ quả:

| Bước | Session A | Kết quả |
|---|---|---|
| 1 | `START TRANSACTION;` | |
| 2 | `UPDATE orders SET status = 'cancelled' WHERE id = 3;` | Trigger `trg_orders_au` chèn 1 dòng lịch sử, cũng trong transaction này |
| 3 | `ROLLBACK;` | Cả thay đổi ở `orders` lẫn dòng lịch sử đều biến mất |

Vì cùng transaction, trigger:

- **Không được** dùng `START TRANSACTION`, `COMMIT`, `ROLLBACK` (được `ROLLBACK TO SAVEPOINT`, vì không
  kết thúc transaction). Không thể "ghi log cho dù câu chính bị rollback" bằng trigger.
- Giữ lock trên các dòng nó đọc/ghi tới hết transaction. Một trigger cập nhật một dòng "bộ đếm" chung
  (ví dụ tổng doanh thu trong bảng `stats`) biến dòng đó thành điểm nghẽn: mọi transaction chèn đơn đều
  phải xếp hàng chờ lock dòng đó ([Chương 15](15-lock-deadlock.md)).

### 7.7 Những trường hợp trigger KHÔNG chạy

Đây là phần dễ gây sai dữ liệu nhất, vì người ta tưởng trigger "bắt được mọi thay đổi":

- **Hành động cascade của foreign key không kích hoạt trigger.** `DELETE` khách hàng làm `ON DELETE
  CASCADE` xoá các đơn của họ thì trigger `DELETE` trên `orders` không chạy cho các đơn đó.
- `TRUNCATE TABLE` và `DROP TABLE` không kích hoạt trigger `DELETE` (chúng không xoá từng dòng). Xoá
  partition cũng vậy.
- Trên replica dùng binlog dạng `ROW` (mặc định), trigger trên replica **không** chạy với thay đổi đến
  từ source, vì thay đổi do trigger ở source đã được ghi thành dòng trong binlog. (Với binlog dạng
  statement thì ngược lại: trigger trên replica chạy.)
- Trigger không gắn được lên bảng trong database `mysql`, `INFORMATION_SCHEMA`, `performance_schema`.

Và một trường hợp chạy "lạ": `INSERT ... ON DUPLICATE KEY UPDATE` luôn chạy `BEFORE INSERT` cho mỗi
dòng, sau đó hoặc `AFTER INSERT` (không trùng khoá), hoặc `BEFORE UPDATE` + `AFTER UPDATE` (trùng khoá).

### 7.8 Giới hạn khác

- Trigger không được sửa chính bảng đã kích hoạt nó (lỗi 1442 như stored function ở mục 4.3). Muốn
  đổi giá trị của dòng đang ghi thì dùng `BEFORE` + `SET NEW.cot`.
- Trigger không trả result set, không có `RETURN` (thoát sớm bằng `LEAVE` khỏi khối có nhãn), không
  dùng `PREPARE`/`EXECUTE` (không có SQL động).
- Trigger luôn chạy với quyền của `DEFINER` (không có `SQL SECURITY INVOKER`), vì không có "người gọi".
  Một người dùng bình thường chèn dòng vào bảng cũng làm trigger chạy với quyền của DEFINER.
- Không có lệnh tắt trigger tạm thời trong MySQL; muốn "tắt" phải `DROP TRIGGER` rồi tạo lại.
- Xem trigger: `SHOW TRIGGERS FROM ch17;`, `SHOW CREATE TRIGGER trg_orders_au\G`,
  `INFORMATION_SCHEMA.TRIGGERS`. Xoá: `DROP TRIGGER IF EXISTS trg_orders_au;`.

### 7.9 Khi nào nên, khi nào không nên dùng trigger

Nên cân nhắc trigger khi:

- Quy tắc phải đúng cho **mọi** đường ghi, kể cả người chạy SQL tay, script cũ, nhiều ứng dụng khác
  ngôn ngữ cùng ghi vào một bảng, và bạn không kiểm soát được hết các đường đó.
- Audit cấp thấp mà không được phép sót (nhớ các ngoại lệ ở mục 7.7).
- Duy trì một giá trị suy diễn đơn giản trong cùng transaction (ví dụ cột `updated_at`; tuy nhiên với
  cột này, `ON UPDATE CURRENT_TIMESTAMP` của Chương 04 đã đủ).
- Công cụ đổi schema online kiểu pt-online-schema-change dùng trigger để chép thay đổi sang bảng mới
  ([Chương 20](20-thay-doi-schema-migration.md)).

Không nên khi:

- Logic nghiệp vụ phức tạp, cần gọi dịch vụ ngoài, gửi email, đẩy queue: trigger không làm được và
  không nên làm.
- Hiệu năng ghi quan trọng: trigger chạy theo từng dòng, trong transaction, làm mọi câu ghi chậm hơn và
  giữ lock lâu hơn.
- Đội phát triển chủ yếu đọc code ứng dụng: trigger là **logic ẩn**. Một lập trình viên đọc
  `$order->update(['status' => 'paid'])` không hề thấy có một `INSERT` vào bảng lịch sử xảy ra theo.
  Khi debug "tại sao bảng này tự có dữ liệu", trigger thường là thứ cuối cùng người ta nghĩ tới.

Đối chiếu với Laravel: *model event* / *observer* của Eloquent (`updating`, `updated`...) là phiên bản
"trigger phía ứng dụng". Nó dễ đọc, dễ test, gọi được dịch vụ ngoài, nhưng chỉ chạy khi đi qua model:
`Order::where('status', 'new')->update([...])` (mass update) và `DB::table('orders')->update(...)`
**không** bắn model event, trong khi trigger của database vẫn chạy. Đó chính là đánh đổi: trigger
không sót đường ghi nào (trừ mục 7.7), event của ứng dụng thì dễ hiểu và linh hoạt hơn.

## 8. Event scheduler

### 8.1 Event là gì

*Event* là một đoạn SQL được MySQL tự chạy **theo lịch**, giống một dòng crontab nằm ngay trong
database. Một luồng riêng của server, gọi là *event scheduler*, theo dõi lịch và chạy các event tới
giờ.

```sql
CREATE [DEFINER = user] EVENT [IF NOT EXISTS] ten_event
  ON SCHEDULE {AT thoi_diem | EVERY khoang [STARTS thoi_diem] [ENDS thoi_diem]}
  [ON COMPLETION [NOT] PRESERVE]
  [ENABLE | DISABLE | DISABLE ON REPLICA]
  [COMMENT 'chuỗi']
  DO than_event;
```

### 8.2 Bật scheduler và tạo event

Biến hệ thống `event_scheduler` có ba giá trị: `ON` (mặc định trong MySQL 8.4), `OFF`, `DISABLED`
(chỉ đặt được lúc khởi động server; khi đó không bật lại được lúc đang chạy).

```sql
SHOW VARIABLES LIKE 'event_scheduler';   -- ON
SET GLOBAL event_scheduler = ON;          -- nếu đang OFF (cần quyền quản trị)
```

Ví dụ: mỗi ngày lúc 03:00, xoá các đơn `new` quá 30 ngày chưa thanh toán (chuyển sang `cancelled`).

```sql
CREATE EVENT ev_cancel_stale_orders
  ON SCHEDULE EVERY 1 DAY
  STARTS '2026-10-26 03:00:00'
  COMMENT 'Huỷ đơn new quá 30 ngày'
  DO
    UPDATE orders
    SET status = 'cancelled'
    WHERE status = 'new' AND created_at < NOW() - INTERVAL 30 DAY;
```

Event chạy một lần:

```sql
CREATE EVENT ev_once
  ON SCHEDULE AT CURRENT_TIMESTAMP + INTERVAL 1 MINUTE
  DO INSERT INTO order_status_history (order_id, old_status, new_status, changed_by)
     VALUES (0, NULL, 'ping', 'event');
```

Sau khi chạy xong, event một lần bị **xoá tự động** (mặc định `ON COMPLETION NOT PRESERVE`); ghi `ON
COMPLETION PRESERVE` nếu muốn giữ lại định nghĩa. Tạo event `AT` một thời điểm đã qua với `NOT
PRESERVE` thì MySQL tạo rồi xoá ngay, kèm warning 1588.

Quản lý:

```sql
SHOW EVENTS FROM ch17;
SELECT EVENT_NAME, STATUS, LAST_EXECUTED FROM INFORMATION_SCHEMA.EVENTS WHERE EVENT_SCHEMA = 'ch17';
ALTER EVENT ev_cancel_stale_orders DISABLE;      -- tạm dừng
ALTER EVENT ev_cancel_stale_orders ENABLE;
DROP EVENT IF EXISTS ev_cancel_stale_orders;
```

Thân event phức tạp nên viết thành procedure rồi `DO CALL p_ten_procedure();`, vì procedure dễ chạy thử
bằng tay hơn.

### 8.3 Những điều cần biết khi vận hành event

- **Thời gian không tuyệt đối chính xác.** Tài liệu nói event có thể trễ 1 đến 2 giây, và không có
  cách quy định thứ tự giữa các event cùng giây.
- **Chạy chồng lên nhau.** Nếu một lần chạy kéo dài hơn khoảng lặp, lần sau có thể bắt đầu khi lần
  trước chưa xong, và hai bản cùng chạy song song. Tài liệu gợi ý tự chống bằng `GET_LOCK()` hoặc
  lock bảng/dòng.
- **Lỗi đi đâu?** Không có client nào nhận lỗi. Lỗi hoặc cảnh báo khi chạy event được ghi vào **error
  log** của server. Nếu không ai đọc error log, event có thể hỏng nhiều tuần mà không ai biết. Cách làm
  tốt hơn: trong procedure được event gọi, bắt lỗi bằng handler và ghi vào một bảng log có giám sát.
- **Múi giờ.** Thời điểm trong `ON SCHEDULE` được hiểu theo `time_zone` của session lúc tạo event, và
  đó trở thành múi giờ của event.
- **Quyền.** Event chạy với quyền của DEFINER, trong một kết nối riêng. DEFINER bị xoá thì event lỗi
  khi chạy (mục 2.6).
- **Replication.** Event tạo trên source khi sang replica luôn bị đặt trạng thái
  `REPLICA_SIDE_DISABLED` (cột `STATUS` của `INFORMATION_SCHEMA.EVENTS`; tên cũ đã deprecated là
  `SLAVESIDE_DISABLED`; mệnh đề tương ứng trong `CREATE EVENT` là `DISABLE ON REPLICA`): tồn tại nhưng
  không chạy, tránh việc cùng một job chạy hai lần. Sau failover (replica lên làm source) bạn phải tự
  bật lại từng event bằng `ALTER EVENT ... ENABLE` ([Chương 22](22-replication-ha.md)).
- Event không tạo được từ trong stored program; event không được tạo/sửa/xoá stored routine hay trigger.
- `ON SCHEDULE` có giới hạn thời điểm khoảng năm 2038 (giới hạn của Unix epoch theo tài liệu).

### 8.4 Mẫu: xoá dữ liệu cũ theo lô

Xoá một triệu dòng bằng một câu `DELETE` tạo ra một transaction khổng lồ: giữ lock lâu, undo log
phình to, replica bị trễ (Chương 16, 22). Cách chuẩn là xoá từng lô nhỏ:

```sql
DELIMITER //
CREATE PROCEDURE p_purge_history(IN p_days INT, IN p_batch INT)
BEGIN
  DECLARE v_deleted INT DEFAULT 1;
  WHILE v_deleted > 0 DO
    DELETE FROM order_status_history
    WHERE changed_at < NOW() - INTERVAL p_days DAY
    ORDER BY id
    LIMIT p_batch;
    SET v_deleted = ROW_COUNT();     -- số dòng câu DELETE vừa xoá
    DO SLEEP(0.1);                   -- nghỉ ngắn cho các truy vấn khác và replica kịp thở
  END WHILE;
END//
DELIMITER ;

CREATE EVENT ev_purge_history
  ON SCHEDULE EVERY 1 DAY STARTS '2026-10-26 04:00:00'
  DO CALL p_purge_history(90, 1000);
```

Ở chế độ autocommit, mỗi câu `DELETE ... LIMIT` là một transaction riêng, commit ngay, nên lock được
nhả sau mỗi lô. (`DELETE ... ORDER BY ... LIMIT` cần một index phù hợp trên `changed_at` hoặc `id` để
không phải quét cả bảng mỗi lô; xem [Chương 11](11-index.md).)

### 8.5 Event hay cron/Laravel scheduler?

| Tiêu chí | MySQL event | Cron / Laravel scheduler |
|---|---|---|
| Chạy ở đâu | Trong server MySQL | Trên máy ứng dụng |
| Việc làm được | Chỉ SQL | Mọi thứ: gọi API, gửi mail, xử lý file |
| Version control, review | Phải tự đưa vào migration | Code nằm trong repo |
| Giám sát, báo lỗi | Error log của MySQL | Log ứng dụng, alert sẵn có |
| Chạy một lần trong cụm nhiều máy | Tự nhiên (chỉ source chạy) | Cần cơ chế khoá, ví dụ `onOneServer()` của Laravel |
| Sau failover | Phải bật lại event trên source mới | Không bị ảnh hưởng |

Trong hệ thống có ứng dụng Laravel, lựa chọn mặc định thường là Laravel scheduler, vì việc định kỳ hiếm
khi chỉ là SQL thuần và đội vận hành đã giám sát log ứng dụng. Event hợp với việc bảo trì thuần dữ liệu
mà bạn muốn gắn chặt với database (ví dụ dọn bảng log), nhất là khi không có ứng dụng nào chạy cron.

## 9. Prepared statement phía server

### 9.1 Prepared statement là gì

Bình thường, mỗi câu SQL gửi lên server đều được *parse* (phân tích cú pháp), kiểm tra, tối ưu rồi mới
chạy. *Prepared statement* tách việc này làm hai bước:

1. **Prepare**: gửi câu SQL có chỗ trống `?` (*parameter marker*). Server phân tích và lưu lại cấu trúc
   đã xử lý, đặt cho nó một tên/id.
2. **Execute**: gửi giá trị cho các `?` và chạy. Có thể execute nhiều lần với giá trị khác nhau.

Tài liệu MySQL nêu hai lợi ích: bớt chi phí parse khi chạy lặp lại nhiều câu gần giống nhau, và
**chống SQL injection**, vì giá trị gửi riêng, không bao giờ trở thành một phần văn bản SQL nên chứa
dấu nháy hay `;` cũng vô hại.

Có hai cách dùng prepared statement phía server:

- **Giao thức nhị phân** (*binary protocol*): thư viện client gửi lệnh prepare/execute riêng. Đây là
  cách PDO (khi tắt emulate) và mysqli dùng. Hiệu quả hơn.
- **Cú pháp SQL**: `PREPARE`, `EXECUTE`, `DEALLOCATE PREPARE`, gõ được trong client `mysql` hoặc dùng
  trong stored procedure. Tài liệu nói nó kém hiệu quả hơn giao thức nhị phân, hợp để thử nghiệm và cho
  SQL động trong procedure.

Chuyện PDO "emulate prepare" so với "native prepare", và lý do Laravel tắt emulate, được bàn ở
[Chương 19](19-database-tu-ung-dung.md). Ở đây ta học phần phía server.

### 9.2 PREPARE, EXECUTE, DEALLOCATE PREPARE

```sql
PREPARE st_by_status FROM
  'SELECT id, total FROM orders WHERE status = ? AND total >= ? ORDER BY id';

SET @s = 'paid', @min = 500;
EXECUTE st_by_status USING @s, @min;       -- 1 | 700.00  (và đơn 2 nếu bạn đã đổi nó sang paid ở mục 7.5)

SET @min = 100;
EXECUTE st_by_status USING @s, @min;       -- thêm đơn 3 | 200.00

DEALLOCATE PREPARE st_by_status;           -- giải phóng
```

Quy tắc theo tài liệu:

- Câu chuẩn bị là một chuỗi hằng hoặc một **biến `@user`** chứa câu SQL; chỉ một câu, không nhiều câu.
- `?` chỉ đứng được ở chỗ của **giá trị dữ liệu**, không thay cho từ khoá, tên bảng, tên cột. `SELECT *
  FROM ?` là sai. `?` không đặt trong dấu nháy kể cả khi giá trị là chuỗi.
- `EXECUTE ... USING` chỉ nhận **biến `@user`**, số biến bằng số `?`.
- Prepared statement thuộc về **session**: session khác không thấy; session kết thúc thì bị huỷ. Tạo
  trong stored procedure thì vẫn còn sau khi procedure kết thúc (nên phải `DEALLOCATE`).
- `PREPARE` lại một tên đã có thì bản cũ bị huỷ trước.
- Tổng số prepared statement của mọi session bị giới hạn bởi `max_prepared_stmt_count` (mặc định
  16382). Ứng dụng prepare mà không bao giờ đóng statement sẽ chạm trần này và nhận lỗi 1461 `Can't
  create more than max_prepared_stmt_count statements`.
- Prepared statement dùng được trong stored procedure, **không** dùng được trong stored function và
  trigger.

Bên trong: server cache cấu trúc đã xử lý của prepared statement (và cả của stored program) **theo
từng session**. Khi bảng mà statement dùng bị đổi cấu trúc (DDL như `ALTER TABLE`), server phát hiện
và tự *reprepare* (chuẩn bị lại) ở lần execute sau, nên kết quả không bị sai vì cấu trúc cũ.

### 9.3 SQL động trong procedure và nguy cơ injection

SQL động (*dynamic SQL*) là câu SQL được ghép thành chuỗi lúc chạy, cần khi tên bảng/cột chỉ biết lúc
chạy, vì `?` không thay được tên. Ví dụ: đếm dòng của một bảng bất kỳ.

Cách viết **sai**, bị SQL injection:

```sql
-- ĐỪNG LÀM THẾ NÀY
SET @sql = CONCAT('SELECT COUNT(*) FROM ', p_table);
```

Nếu `p_table` là `customers; DROP TABLE orders` thì sao? `PREPARE` chỉ nhận **một** câu nên chuỗi có
hai câu sẽ lỗi, nhưng kẻ tấn công vẫn có nhiều cách khác trong phạm vi một câu, ví dụ `p_table =
'customers UNION SELECT COUNT(*) FROM mysql.user'`. Nguyên tắc giống hệt ở ứng dụng: không bao giờ ghép
đầu vào vào văn bản SQL.

Cách viết đúng: kiểm tra tên trong danh sách hợp lệ (whitelist), quote tên bằng backtick, và mọi giá
trị dữ liệu đi qua `?`:

```sql
DELIMITER //
CREATE PROCEDURE p_count_rows(IN p_table VARCHAR(64), IN p_min_id INT)
BEGIN
  -- 1. Whitelist: tên phải là một bảng có thật trong database hiện tại
  IF NOT EXISTS (
    SELECT 1 FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = p_table
  ) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bảng không hợp lệ';
  END IF;

  -- 2. Quote tên bằng backtick (nhân đôi backtick bên trong nếu có)
  SET @sql = CONCAT('SELECT COUNT(*) AS n FROM `', REPLACE(p_table, '`', '``'), '` WHERE id >= ?');
  -- 3. Giá trị đi qua ? và biến @
  SET @min_id = p_min_id;

  PREPARE st FROM @sql;
  EXECUTE st USING @min_id;
  DEALLOCATE PREPARE st;
END//
DELIMITER ;

CALL p_count_rows('customers', 2);   -- n = 2 (id 2, 3; thêm id 5 nếu bạn đã chạy mục 7.3)
CALL p_count_rows('nope', 1);        -- ERROR 1644 (45000): Bảng không hợp lệ
```

⚠️ Hai điều dễ quên:

- Câu SQL động không thấy được biến cục bộ hay tham số của procedure (vì prepared statement sống theo
  session, có thể chạy sau khi procedure đã kết thúc). Phải chuyển qua biến `@`, như `@min_id` ở trên.
- Biến `@sql`, `@min_id` còn lại trong session sau khi procedure chạy xong. Thường vô hại, nhưng đừng
  dựa vào giá trị của chúng ở nơi khác.

Nếu bắt buộc phải ghép một **giá trị** vào chuỗi (hiếm), dùng hàm `QUOTE()` để có chuỗi SQL được quote
và escape đúng; nhưng `?` vẫn là lựa chọn đầu tiên.

## 10. Logic trong database hay trong ứng dụng

Đây là câu hỏi phỏng vấn senior kinh điển, và câu trả lời tốt luôn là "tuỳ, và đây là các tiêu chí".

### 10.1 Bảng cân nhắc

| Tiêu chí | Logic trong database (procedure, function, trigger, event) | Logic trong ứng dụng (PHP/Laravel) |
|---|---|---|
| Round trip mạng | Ít: nhiều câu chạy trong một lần gọi | Mỗi câu một round trip (giảm được bằng batch, transaction ngắn) |
| Áp dụng cho mọi client | Có: mọi đường ghi đều qua (trigger) | Chỉ khi mọi client đi qua cùng code |
| Ngôn ngữ, thư viện | SQL thủ tục, hạn chế, không gọi được dịch vụ ngoài | Đầy đủ: HTTP, queue, mail, thư viện |
| Test | Khó: cần database thật, ít công cụ | Unit test, mock, CI quen thuộc |
| Debug | Không có debugger (tài liệu MySQL ghi rõ) | Debugger, log, APM |
| Version control, deploy | Phải đưa vào migration; đổi procedure là `DROP` + `CREATE`, khó deploy song song hai phiên bản | Theo deploy code, rollback dễ |
| Scale | Tốn CPU của database, thứ khó scale ngang nhất | Thêm máy ứng dụng dễ dàng |
| Đổi hệ quản trị | Cú pháp riêng của MySQL, gần như viết lại khi sang PostgreSQL | Ít phụ thuộc |
| Quyền | Cấp `EXECUTE` mà không cấp quyền bảng (`SQL SECURITY DEFINER`) | Dựa vào tài khoản database của ứng dụng |
| Khả năng "nhìn thấy" | Logic ẩn: đọc code ứng dụng không thấy | Nằm cạnh code nghiệp vụ |

### 10.2 Hướng dẫn thực tế

Với một hệ thống web điển hình (Laravel + MySQL), đội ngũ phần lớn là lập trình viên ứng dụng:

- **Mặc định đặt logic nghiệp vụ ở ứng dụng.** Database lo việc nó giỏi nhất: lưu trữ, ràng buộc toàn
  vẹn (`PRIMARY KEY`, `UNIQUE`, `FOREIGN KEY`, `CHECK`, `NOT NULL`), transaction, truy vấn tập hợp.
- **Ràng buộc khai báo trước trigger.** Một `CHECK` hay `UNIQUE` tốt hơn một trigger làm cùng việc.
- **View**: dùng thoải mái cho báo cáo, cho phân quyền đọc, cho tương thích khi đổi schema; nhớ quản
  lý chúng trong migration.
- **Procedure**: hợp với tác vụ thuần dữ liệu chạy trên lượng lớn dòng (dọn dữ liệu theo lô, chuyển
  đổi dữ liệu một lần), hoặc khi nhiều ứng dụng khác ngôn ngữ phải dùng chung một thao tác.
- **Trigger**: giữ ít, đơn giản, có tài liệu; hợp cho audit cấp thấp hoặc công cụ migration online.
- **Event**: chỉ cho bảo trì dữ liệu thuần SQL; còn lại dùng scheduler của ứng dụng.

Ngược lại, có những tổ chức (ngân hàng, hệ thống cũ nhiều client, đội DBA mạnh) đặt nhiều logic trong
database có chủ đích. Không có lựa chọn đúng tuyệt đối; điều quan trọng là quyết định có lý do và nhất
quán, không phải "một nửa quy tắc ở trigger, một nửa ở observer" mà không ai biết.

### 10.3 Quản lý stored object như code

Nếu đã dùng, hãy đối xử với chúng như code:

- Tạo/sửa trong migration (Laravel: `DB::unprepared('CREATE PROCEDURE ...')`, không có `DELIMITER`).
  ⚠️ `CREATE`/`DROP` procedure, trigger, view là DDL gây *implicit commit* (Chương 13): đừng chạy chúng
  bên trong một transaction mà bạn mong rollback được.
- Ghi rõ `DEFINER` hoặc chấp nhận DEFINER là tài khoản chạy migration, và kiểm soát quyền tài khoản đó
  (mục 2.6).
- Khi backup bằng `mysqldump`, routine và event **không** được dump mặc định: cần `--routines` và
  `--events` (trigger thì được dump mặc định). Chi tiết ở [Chương 21](21-backup-restore.md).
- Theo dõi: `INFORMATION_SCHEMA.ROUTINES`, `TRIGGERS`, `EVENTS`, `VIEWS` để biết trong database đang
  có những gì; đưa danh sách này vào kiểm tra định kỳ.

## 11. Đối chiếu PostgreSQL

| Chủ đề | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| Ngôn ngữ routine | Chỉ SQL/PSM kiểu MySQL | PL/pgSQL, SQL, và các ngôn ngữ khác qua extension (PL/Python, PL/Perl...) |
| Procedure và function | `PROCEDURE` (gọi bằng `CALL`) và `FUNCTION` | Lâu nay chủ yếu `FUNCTION`; `PROCEDURE` có từ PostgreSQL 11, cho phép `COMMIT`/`ROLLBACK` bên trong |
| Function trả nhiều dòng | Không (function chỉ trả một giá trị vô hướng) | Có: `RETURNS TABLE (...)`, `RETURNS SETOF ...`, dùng như bảng trong `FROM` |
| Sửa routine | `DROP` + `CREATE` | `CREATE OR REPLACE` |
| Thân routine | Viết thẳng, cần `DELIMITER` ở client | Đặt trong chuỗi `$$ ... $$`, không cần đổi delimiter |
| Trigger | Thân viết trực tiếp, chỉ `FOR EACH ROW` | Trigger gọi một *trigger function*; có `FOR EACH ROW` và `FOR EACH STATEMENT`, `INSTEAD OF` trên view, điều kiện `WHEN`, transition table |
| Tắt trigger tạm thời | Không có | `ALTER TABLE ... DISABLE TRIGGER` |
| Xử lý lỗi | `DECLARE ... HANDLER`, `SIGNAL`, `RESIGNAL` | `BEGIN ... EXCEPTION WHEN ... THEN ... END`, `RAISE` |
| Lịch chạy | Event scheduler có sẵn | Không có sẵn trong lõi; thường dùng extension `pg_cron` hoặc cron ngoài |
| Materialized view | Không | Có |
| Prepared statement SQL | `PREPARE st FROM '...'`, `EXECUTE st USING @v` | `PREPARE st(int) AS ...`, `EXECUTE st(1)` |

PostgreSQL mạnh hơn đáng kể về lập trình trong database, nên ở các đội dùng PostgreSQL, việc đặt một
phần logic vào function (ví dụ function trả về tập dòng thay cho view có tham số) phổ biến hơn. Chi tiết
đối chiếu tổng thể ở [Chương 25](25-postgres-doi-chieu.md).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Tạo view `SELECT *` rồi thêm cột vào bảng, view không có cột mới | `*` được mở thành danh sách cột lúc tạo view | Liệt kê cột rõ ràng; tạo lại view khi đổi schema |
| Xoá/đổi tên cột, view hỏng lúc chạy (lỗi 1356) | MySQL không chặn DDL làm hỏng view | Tra `INFORMATION_SCHEMA.VIEWS` trước migration; `CHECK TABLE` view sau migration |
| Restore dump sang server mới, view/routine lỗi vì DEFINER không tồn tại | DEFINER là tài khoản của server cũ | Tạo tài khoản tương ứng hoặc sửa DEFINER; thống nhất một tài khoản DEFINER |
| Viết `DELIMITER //` trong migration Laravel | `DELIMITER` là lệnh của client `mysql`, server không hiểu | Gửi nguyên câu `CREATE PROCEDURE` qua `DB::unprepared` |
| Tham số/biến trùng tên cột, `WHERE status = status` luôn đúng | Biến được ưu tiên hơn cột | Tiền tố `p_`, `v_` |
| `SELECT ... INTO` không thấy dòng nhưng biến vẫn có giá trị | Không có dòng thì biến giữ giá trị cũ | Gán `NULL` trước, hoặc `SET v = (SELECT ...)` |
| Câu lệnh `CASE` không có `ELSE` gây lỗi 1339 | Câu lệnh `CASE` khác biểu thức `CASE` | Luôn có `ELSE` |
| `CONTINUE HANDLER FOR SQLEXCEPTION` rỗng, lỗi biến mất | Handler nuốt lỗi | Bắt để rollback/log rồi `RESIGNAL` |
| Handler `EXIT` rollback nhưng không `RESIGNAL`, client tưởng thành công | Procedure kết thúc êm | Luôn `RESIGNAL` sau khi dọn dẹp |
| `CREATE FUNCTION` lỗi 1418 | Binary log bật, function không khai `DETERMINISTIC`/`NO SQL`/`READS SQL DATA` | Khai báo trung thực đặc tính của function |
| Function đọc bảng dùng trong `SELECT` trên bảng lớn rất chậm | Hàm chạy một truy vấn cho mỗi dòng (N+1 trong database) | Viết lại bằng `JOIN`/`GROUP BY` |
| Trigger audit "bỏ sót" thay đổi | FK cascade, `TRUNCATE` không kích hoạt trigger | Biết các ngoại lệ ở mục 7.7; audit thêm ở tầng khác nếu cần |
| Trigger cập nhật một dòng thống kê chung gây chờ lock | Mọi transaction cùng tranh một dòng | Tổng hợp theo lô (event/job) thay vì cập nhật mỗi lần ghi |
| Event hỏng nhiều tuần không ai biết | Lỗi event chỉ vào error log | Bắt lỗi, ghi vào bảng log có giám sát; hoặc dùng scheduler của ứng dụng |
| Sau failover, job định kỳ không chạy | Event trên replica ở trạng thái `REPLICA_SIDE_DISABLED` | Đưa bước bật event vào quy trình failover |
| SQL động ghép chuỗi đầu vào | SQL injection ngay trong procedure | Whitelist tên, backtick, giá trị qua `?` |
| Ứng dụng chạm trần `max_prepared_stmt_count` | Prepare mà không đóng statement | Đóng/tái dùng statement; theo dõi số prepared statement |

## Tóm tắt chương

- Stored object gồm view, procedure, function, trigger, event; định nghĩa nằm trong data dictionary,
  xem qua `INFORMATION_SCHEMA`.
- View là câu `SELECT` có tên, không chứa dữ liệu; định nghĩa bị đóng băng lúc tạo (`SELECT *` được mở
  ra), và MySQL không chặn DDL làm hỏng view.
- View được xử lý bằng `MERGE` (ghép, dùng được index) hoặc `TEMPTABLE` (bảng tạm); view có quan hệ
  một-một với bảng gốc thì updatable, `WITH CHECK OPTION` chặn dòng "trốn" khỏi view.
- `DEFINER` + `SQL SECURITY` quyết định quyền khi chạy view/routine; trigger và event luôn chạy với
  quyền DEFINER.
- Procedure: `CALL`, tham số `IN`/`OUT`/`INOUT`, trả được result set, được dùng transaction và SQL động.
  Function: dùng trong biểu thức, một giá trị, không transaction, phải khai đặc tính khi binlog bật.
- Xử lý lỗi bằng `DECLARE CONTINUE|EXIT HANDLER`, phát lỗi bằng `SIGNAL SQLSTATE '45000'`, ném lại bằng
  `RESIGNAL`, đọc chi tiết bằng `GET DIAGNOSTICS`.
- Trigger cấp dòng, `BEFORE` sửa được `NEW`, `AFTER` hợp để ghi lịch sử; chạy trong cùng transaction;
  không chạy với FK cascade và `TRUNCATE`.
- Event scheduler chạy SQL theo lịch, mặc định `ON` trong 8.4; lỗi chỉ vào error log; trên replica bị
  tắt (`REPLICA_SIDE_DISABLED`).
- Prepared statement phía server tách prepare và execute, `?` chỉ thay giá trị; SQL động phải whitelist
  tên và truyền giá trị qua `?`.
- Mặc định đặt logic nghiệp vụ ở ứng dụng, ràng buộc toàn vẹn ở database; dùng stored program có lý do
  và quản lý chúng như code.

## Câu hỏi tự kiểm tra

1. View có lưu dữ liệu không? Vì sao đọc một view có `GROUP BY` có thể chậm hơn nhiều so với một view
   chỉ có `WHERE`? (mục 2.5)
2. Bạn thêm một cột vào bảng mà một view `SELECT *` đang dùng. View có cột mới không? Nếu bạn xoá một
   cột thì chuyện gì xảy ra, và lúc nào bạn phát hiện ra? (mục 2.4)
3. Liệt kê ba thứ làm view không updatable. Một view join hai bảng có `UPDATE` được không, có `DELETE`
   được không? (mục 2.7)
4. Khác biệt giữa `WITH LOCAL CHECK OPTION` và `WITH CASCADED CHECK OPTION` chỉ lộ ra khi nào? (mục 2.8)
5. `SQL SECURITY DEFINER` và `INVOKER` khác nhau thế nào? Vì sao trigger và event không có `INVOKER`?
   (mục 2.6, 7.8)
6. Biến `v_total` và `@total` khác nhau ở những điểm nào? Vì sao gõ sai tên biến `@` nguy hiểm hơn gõ
   sai tên biến cục bộ? (mục 3.3)
7. Trong procedure chuyển tiền ở mục 6.5, điều gì xảy ra nếu bỏ dòng `RESIGNAL;` trong handler?
8. Kể ba trường hợp dữ liệu trong bảng thay đổi mà trigger `DELETE`/`UPDATE` của bảng đó không chạy.
   (mục 7.7)
9. Vì sao `CREATE FUNCTION` có thể bị lỗi 1418, và vì sao không nên "chữa" bằng cách khai
   `DETERMINISTIC` cho một hàm dùng `NOW()`? (mục 4.2)
10. Trong một procedure, vì sao không viết được `PREPARE st FROM CONCAT('SELECT ... WHERE id = ',
    p_id)` một cách an toàn, và cách đúng là gì? (mục 9.3)

## Bài tập

1. **View phân quyền.** Tạo view `v_order_summary` gồm mã đơn, tên khách, trạng thái, tổng tiền, chỉ
   các đơn không bị huỷ, với `WITH CHECK OPTION` nếu được (giải thích vì sao được hoặc không được).
   Tạo tài khoản `report` chỉ có quyền `SELECT` trên view đó, chứng minh tài khoản này không đọc được
   `customers.email`. Kiểm tra `IS_UPDATABLE` của view trong `INFORMATION_SCHEMA.VIEWS` và giải thích
   kết quả.
2. **Sửa procedure chuyển tiền chống deadlock.** Viết lại `p_transfer` sao cho luôn khoá cả hai dòng
   tài khoản theo thứ tự `id` tăng dần trước khi kiểm tra số dư và cập nhật. Mở hai session, chạy
   `CALL p_transfer(1, 2, 10)` và `CALL p_transfer(2, 1, 10)` xen kẽ theo dạng bảng timeline
   (Bước | Session A | Session B | Kết quả) để kiểm chứng không còn deadlock. Đồng thời ghi mỗi lần
   chuyển thành công vào bảng `transfers(id, from_id, to_id, amount, created_at)`.
3. **Trigger audit đầy đủ.** Tạo bảng `products_audit` và các trigger để ghi lại mọi thay đổi giá
   (`price`) và tồn kho (`stock`) của `products`: giá trị cũ, mới, thời điểm, và `@app_user_id` nếu có.
   Thử ba tình huống và ghi lại kết quả: `UPDATE` bình thường; `UPDATE` vi phạm `chk_stock`;
   `UPDATE` bên trong một transaction rồi `ROLLBACK`. Giải thích bảng audit ở mỗi tình huống.
4. **Dọn dữ liệu bằng event.** Viết procedure xoá theo lô các dòng `order_status_history` cũ hơn N
   ngày, ghi số dòng đã xoá và lỗi (nếu có, dùng `GET STACKED DIAGNOSTICS`) vào bảng `job_log`, chống
   chạy chồng bằng `GET_LOCK()`. Lên lịch bằng event chạy mỗi giờ. Sau đó viết một đoạn ngắn: nếu hệ
   thống của bạn có Laravel, bạn sẽ giữ event này hay chuyển sang Laravel scheduler, vì sao?

## Đọc thêm

- MySQL 8.4 Reference Manual, Chapter 27 "Stored Objects":
  https://dev.mysql.com/doc/refman/8.4/en/stored-objects.html
  - Using Views, View Processing Algorithms, Updatable and Insertable Views, The View WITH CHECK
    OPTION Clause: https://dev.mysql.com/doc/refman/8.4/en/views.html
  - Stored Object Access Control (DEFINER, SQL SECURITY, orphan object):
    https://dev.mysql.com/doc/refman/8.4/en/stored-objects-security.html
  - Stored Program Binary Logging: https://dev.mysql.com/doc/refman/8.4/en/stored-programs-logging.html
  - Restrictions on Stored Programs: https://dev.mysql.com/doc/refman/8.4/en/stored-program-restrictions.html
  - Restrictions on Views: https://dev.mysql.com/doc/refman/8.4/en/view-restrictions.html
  - Using Triggers: https://dev.mysql.com/doc/refman/8.4/en/triggers.html
  - Using the Event Scheduler: https://dev.mysql.com/doc/refman/8.4/en/event-scheduler.html
- MySQL 8.4 Reference Manual, các câu lệnh: `CREATE VIEW`, `CREATE PROCEDURE and CREATE FUNCTION`,
  `CREATE TRIGGER`, `CREATE EVENT`, Compound Statement Syntax (`DECLARE`, flow control, cursors,
  `DECLARE ... HANDLER`, `SIGNAL`, `RESIGNAL`, `GET DIAGNOSTICS`):
  https://dev.mysql.com/doc/refman/8.4/en/sql-compound-statements.html
- MySQL 8.4 Reference Manual, Prepared Statements và Caching of Prepared Statements and Stored
  Programs: https://dev.mysql.com/doc/refman/8.4/en/sql-prepared-statements.html,
  https://dev.mysql.com/doc/refman/8.4/en/statement-caching.html
- MySQL Server Error Message Reference (mã lỗi 1288, 1356, 1369, 1393, 1395, 1418, 1442, 1644...):
  https://dev.mysql.com/doc/mysql-errors/8.4/en/server-error-reference.html
- PostgreSQL 18 Documentation: CREATE VIEW, CREATE MATERIALIZED VIEW, PL/pgSQL, CREATE TRIGGER:
  https://www.postgresql.org/docs/18/sql-createview.html,
  https://www.postgresql.org/docs/18/plpgsql.html,
  https://www.postgresql.org/docs/18/sql-createtrigger.html
- gh-ost, phần lý do không dùng trigger khi đổi schema online:
  https://github.com/github/gh-ost/blob/master/doc/why-triggerless.md
