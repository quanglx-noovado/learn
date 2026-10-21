# Chương 05. Thao tác dữ liệu: INSERT, UPDATE, DELETE và SELECT cơ bản

> [← Mục lục](README.md) · [← Chương 04: Tạo và thay đổi bảng: DDL và ràng buộc](04-ddl-constraint.md) · [Chương 06: Biểu thức, hàm và NULL →](06-ham-bieu-thuc-null.md)

**Bạn sẽ học được:**

- Dựng bộ dữ liệu mẫu "cửa hàng online" (`shop`) dùng xuyên suốt các chương sau, và tự tính được kết quả của mọi câu truy vấn trên nó.
- Thêm dữ liệu bằng `INSERT`: một dòng, nhiều dòng, `INSERT ... SELECT`, và hiểu `INSERT IGNORE` thực sự "bỏ qua" những gì.
- Đọc dữ liệu bằng `SELECT`: chọn cột, đặt alias, `DISTINCT`, lọc bằng `WHERE` (so sánh, `AND`/`OR`/`NOT`, `IN`, `BETWEEN`, `LIKE`, `IS NULL`).
- Sắp xếp bằng `ORDER BY` (nhiều cột, `ASC`/`DESC`, NULL đứng đâu) và lấy một phần kết quả bằng `LIMIT`/`OFFSET`.
- Phân biệt thứ tự viết và thứ tự thực thi logic của `SELECT`, từ đó tự giải thích vì sao alias dùng được ở chỗ này mà không dùng được ở chỗ kia.
- Sửa và xoá dữ liệu bằng `UPDATE`, `DELETE` một cách an toàn: luôn có `WHERE`, kiểm tra trước bằng `SELECT`, bật `sql_safe_updates`.

**Cần biết trước:** [Chương 01](01-database-la-gi.md) (kết nối bằng mysql client), [Chương 03](03-kieu-du-lieu.md) (kiểu dữ liệu, collation), [Chương 04](04-ddl-constraint.md) (`CREATE TABLE`, khoá chính, khoá ngoại, `AUTO_INCREMENT`).

## 1. Bốn câu lệnh thao tác dữ liệu

### 1.1 CRUD và DML

Gần như mọi ứng dụng chỉ làm bốn việc với dữ liệu: tạo mới, đọc, sửa, xoá. Giới lập trình gọi tắt là
*CRUD* (Create, Read, Update, Delete). Trong SQL, bốn việc đó ứng với bốn câu lệnh, gọi chung là
*DML* (Data Manipulation Language, ngôn ngữ thao tác dữ liệu):

| Việc | Câu lệnh SQL | Ví dụ trong cửa hàng online |
|---|---|---|
| Create | `INSERT` | Khách đăng ký tài khoản, đặt một đơn hàng |
| Read | `SELECT` | Hiện danh sách sản phẩm, xem lịch sử đơn |
| Update | `UPDATE` | Đổi trạng thái đơn sang "đã giao", trừ tồn kho |
| Delete | `DELETE` | Xoá sản phẩm nhập nhầm, dọn log cũ |

Chương 04 đã dùng *DDL* (Data Definition Language: `CREATE`, `ALTER`, `DROP`) để tạo cái "khung"
là bảng và cột. DML làm việc với "ruột": các dòng dữ liệu nằm trong khung đó. Hai nhóm này khác
nhau ở một điểm quan trọng trong MySQL: câu DDL tự commit (không rollback được, xem
[chương 04](04-ddl-constraint.md)), còn câu DML chạy trong transaction nên có thể rollback
([chương 13](13-transaction-acid.md)). Mục 11 của chương này sẽ dùng tính chất đó làm lưới an toàn.

Trong bốn lệnh, `SELECT` được viết nhiều nhất và có nhiều phần nhất, nên chiếm phần lớn chương.
Thứ tự trình bày: dựng dữ liệu mẫu (mục 2), `INSERT` (mục 3), `SELECT` và các mệnh đề của nó (mục
4 đến 8), rồi mới tới `UPDATE`, `DELETE` (mục 9, 10) vì hai lệnh này dùng lại `WHERE`, `ORDER BY`,
`LIMIT` của `SELECT`, và cuối cùng là cách sửa xoá an toàn (mục 11).

### 1.2 Chạy ví dụ ở đâu

Mọi ví dụ viết cho MySQL 8.4. Cách nhanh nhất là chạy MySQL trong Docker (cách cài khác xem
[chương 01](01-database-la-gi.md)):

```sh
# Chạy trên terminal của máy bạn. Lần đầu sẽ tải image mysql:8.4.
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4

# Đợi vài giây cho server khởi động xong, rồi mở mysql client nằm sẵn trong container.
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Client sẽ in một cảnh báo về việc gõ mật khẩu trên dòng lệnh; với máy học thì bỏ qua được. Tuỳ
chọn `--default-character-set=utf8mb4` bảo client gửi và nhận chữ theo bảng mã utf8mb4, để tiếng
Việt có dấu được lưu đúng (charset là chủ đề của [chương 03](03-kieu-du-lieu.md)).

Vài điều về mysql client cần biết trước khi gõ lệnh:

- Mỗi câu lệnh kết thúc bằng dấu `;`. Quên dấu `;` thì client chưa gửi gì cả mà hiện dấu nhắc `->`
  chờ bạn gõ tiếp. Gõ `;` rồi Enter là xong.
- Kết thúc bằng `\G` thay cho `;` thì kết quả được in theo chiều dọc, mỗi cột một dòng. Rất tiện
  khi bảng có nhiều cột.
- Gõ `\c` để huỷ câu đang gõ dở.
- Từ khoá SQL không phân biệt hoa thường (`select` hay `SELECT` đều được). Viết hoa từ khoá chỉ là
  quy ước cho dễ đọc, giáo trình này theo quy ước đó.

Ba kiểu chú thích (*comment*) MySQL hiểu:

```sql
SELECT 1;   -- chú thích tới hết dòng; sau hai dấu gạch PHẢI có ít nhất một khoảng trắng
SELECT 2;   # chú thích tới hết dòng, kiểu riêng của MySQL
SELECT /* chú thích nằm giữa câu, được phép kéo dài nhiều dòng */ 3;
```

⚠️ `--chú thích` (không có khoảng trắng sau `--`) không được MySQL coi là chú thích. Đây là điểm
MySQL khác chuẩn SQL một chút; cứ luôn để một dấu cách sau `--` là an toàn ở mọi hệ quản trị.

Về cách viết giá trị:

- Chuỗi viết trong nháy đơn: `'Hà Nội'`. MySQL cũng nhận nháy kép `"Hà Nội"` là chuỗi, nhưng đừng
  tập thói quen đó: trong chuẩn SQL và PostgreSQL, nháy kép dùng cho tên cột, tên bảng (mục 4.2).
- Số viết trực tiếp, không có nháy: `15990000`.
- Ngày giờ viết như chuỗi theo dạng `'YYYY-MM-DD hh:mm:ss'`: `'2026-03-31 23:59:59'`.
- `NULL` (không có nháy) nghĩa là "không có giá trị". `'NULL'` có nháy là chuỗi bốn chữ cái, hoàn
  toàn khác.

## 2. Dữ liệu mẫu dùng xuyên suốt giáo trình

### 2.1 Bài toán: một cửa hàng online nhỏ

Từ chương này trở đi, các ví dụ dùng chung một database tên `shop`, mô phỏng cửa hàng bán điện
thoại, laptop, phụ kiện và sách. Thiết kế của nó đi theo [chương 02](02-mo-hinh-quan-he-thiet-ke.md)
nhưng rút gọn còn năm bảng:

| Bảng | Mỗi dòng là | Cột đáng chú ý |
|---|---|---|
| `users` | Một khách hàng | `email` không trùng; `city`, `phone` có thể NULL |
| `categories` | Một danh mục | `parent_id` trỏ về chính bảng này, tạo thành cây danh mục |
| `products` | Một sản phẩm | `sku` (mã hàng) không trùng; `category_id` có thể NULL |
| `orders` | Một đơn hàng | `status`; `shipped_at` NULL khi chưa giao |
| `order_items` | Một dòng hàng trong đơn | Khoá chính ghép `(order_id, product_id)` |

Quan hệ giữa các bảng (1 và n là "một" và "nhiều", xem chương 02):

```
+----------------+          +----------------+          +-------------------+
| users          | 1------n | orders         | 1------n | order_items       |
+----------------+          +----------------+          +-------------------+
| id         PK  |          | id         PK  |          | order_id   PK, FK |
| email      UQ  |          | user_id    FK  |          | product_id PK, FK |
| name           |          | status         |          | qty               |
| city           |          | total          |          | unit_price        |
| phone          |          | created_at     |          +-------------------+
| created_at     |          | shipped_at     |                    | n
+----------------+          +----------------+                    |
                                                                  | 1
+----------------+                                      +-------------------+
| categories     | 1----------------------------------n | products          |
+----------------+                                      +-------------------+
| id         PK  |                                      | id          PK    |
| name           |                                      | sku         UQ    |
| parent_id  FK  |                                      | name              |
+----------------+                                      | category_id FK    |
  parent_id trỏ về categories.id                        | price             |
  (cây danh mục)                                        | stock             |
                                                        +-------------------+
```

PK là khoá chính (*primary key*), FK là khoá ngoại (*foreign key*), UQ là ràng buộc không trùng
(*unique*); cả ba đã học ở [chương 04](04-ddl-constraint.md). Tiền lưu bằng `DECIMAL(12,0)` vì đơn vị là đồng, không có phần lẻ (vì sao không dùng `FLOAT` cho
tiền: [chương 03](03-kieu-du-lieu.md)).

### 2.2 Script tạo database và bảng

Lưu toàn bộ phần SQL của mục 2.2 và 2.3 vào một file `shop.sql` trên máy bạn rồi nạp một lần:

```sh
# Chạy trên terminal của máy bạn, ở thư mục chứa shop.sql
docker exec -i my84 mysql -uroot -proot --default-character-set=utf8mb4 < shop.sql
```

(`-i` không có `-t`: chuyển nội dung file vào client qua stdin.) Cũng có thể dán thẳng từng đoạn
vào mysql client đang mở.

⚠️ Script bắt đầu bằng `DROP DATABASE IF EXISTS shop`, tức là xoá sạch database `shop` cũ nếu có.
Đó là chủ ý: chạy lại script bất cứ lúc nào để đưa dữ liệu về trạng thái ban đầu. Đừng đổi tên
database trong script thành tên của một database thật.

```sql
-- shop.sql: dữ liệu mẫu dùng xuyên suốt giáo trình (MySQL 8.4)
SET NAMES utf8mb4;   -- báo cho server: các chuỗi trong script này là utf8mb4

DROP DATABASE IF EXISTS shop;
CREATE DATABASE shop CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE shop;

CREATE TABLE users (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email      VARCHAR(100)    NOT NULL,
  name       VARCHAR(100)    NOT NULL,
  city       VARCHAR(50)     NULL,          -- khách chưa khai báo thì NULL
  phone      VARCHAR(20)     NULL,
  created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
);

CREATE TABLE categories (
  id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  name      VARCHAR(100) NOT NULL,
  parent_id INT UNSIGNED NULL,              -- NULL: danh mục gốc
  PRIMARY KEY (id),
  CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES categories (id)
);

CREATE TABLE products (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  sku         VARCHAR(20)   NOT NULL,       -- mã hàng
  name        VARCHAR(100)  NOT NULL,
  category_id INT UNSIGNED  NULL,           -- NULL: chưa xếp danh mục
  price       DECIMAL(12,0) NOT NULL,       -- giá bán hiện tại, đơn vị đồng
  stock       INT UNSIGNED  NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uq_products_sku (sku),
  CONSTRAINT fk_products_category FOREIGN KEY (category_id) REFERENCES categories (id)
);

CREATE TABLE orders (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id    BIGINT UNSIGNED NOT NULL,
  status     VARCHAR(20)     NOT NULL DEFAULT 'pending', -- pending, paid, shipped, cancelled
  total      DECIMAL(12,0)   NOT NULL DEFAULT 0,
  created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  shipped_at DATETIME        NULL,          -- NULL: chưa giao
  PRIMARY KEY (id),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE order_items (
  order_id   BIGINT UNSIGNED NOT NULL,
  product_id INT UNSIGNED    NOT NULL,
  qty        INT UNSIGNED    NOT NULL,
  unit_price DECIMAL(12,0)   NOT NULL,      -- giá tại thời điểm mua
  PRIMARY KEY (order_id, product_id),
  CONSTRAINT fk_items_order   FOREIGN KEY (order_id)   REFERENCES orders (id),
  CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products (id)
);
```

### 2.3 Script nạp dữ liệu

Phần này nối tiếp vào cuối `shop.sql`. Cú pháp `INSERT` được giải thích kỹ ở mục 3; lúc này chỉ cần
chạy. Các `id` được ghi tường minh để mọi người có cùng một bộ id khi làm bài; trong ứng dụng thật
bạn để `AUTO_INCREMENT` tự sinh (mục 3.2).

```sql
INSERT INTO users (id, email, name, city, phone, created_at) VALUES
  (1, 'an@example.com',    'Nguyễn Văn An',  'Hà Nội',      '0901000001', '2026-01-05 09:00:00'),
  (2, 'binh@example.com',  'Trần Thị Bình',  'Hồ Chí Minh', NULL,         '2026-01-12 14:30:00'),
  (3, 'chi@example.com',   'Lê Minh Chi',    'Đà Nẵng',     '0901000003', '2026-02-01 08:15:00'),
  (4, 'dung@example.com',  'Phạm Quốc Dũng', 'Hà Nội',      '0901000004', '2026-02-20 20:45:00'),
  (5, 'em@example.com',    'Hoàng Thu Em',   NULL,          NULL,         '2026-03-03 11:00:00'),
  (6, 'giang@example.com', 'Vũ Hương Giang', 'Hồ Chí Minh', '0901000006', '2026-03-15 16:20:00');

-- Danh mục cha phải có trước danh mục con, vì khoá ngoại parent_id được kiểm tra từng dòng.
INSERT INTO categories (id, name, parent_id) VALUES
  (1, 'Điện tử',             NULL),
  (2, 'Điện thoại',          1),
  (3, 'Laptop',              1),
  (4, 'Phụ kiện điện thoại', 2),
  (5, 'Sách',                NULL),
  (6, 'Sách lập trình',      5);

INSERT INTO products (id, sku, name, category_id, price, stock) VALUES
  (1, 'DT-X1',    'Điện thoại X1',     2,     8990000,   25),
  (2, 'DT-X2P',   'Điện thoại X2 Pro', 2,    15990000,    8),
  (3, 'LT-L14',   'Laptop L14',        3,    18500000,    5),
  (4, 'LT-L16P',  'Laptop L16 Pro',    3,    32000000,    0),
  (5, 'PK-OP1',   'Ốp lưng X1',        4,      150000,  100),
  (6, 'PK-SAC30', 'Sạc nhanh 30W',     4,      390000,   40),
  (7, 'SA-SQL',   'Sách SQL căn bản',  6,      180000,   30),
  (8, 'SA-PHP',   'Sách PHP hiện đại', 6,      250000,   12),
  (9, 'GC_500K',  'Thẻ quà tặng 500k', NULL,   500000, 1000);

INSERT INTO orders (id, user_id, status, total, created_at, shipped_at) VALUES
  (1, 1, 'shipped',    9140000, '2026-03-02 10:15:00', '2026-03-04 09:00:00'),
  (2, 2, 'shipped',   18500000, '2026-03-05 08:05:00', '2026-03-07 15:30:00'),
  (3, 3, 'cancelled', 15990000, '2026-03-10 13:00:00', NULL),
  (4, 1, 'paid',        180000, '2026-03-20 21:40:00', NULL),
  (5, 3, 'pending',     430000, '2026-03-31 23:59:59', NULL),
  (6, 4, 'paid',      16380000, '2026-04-01 00:00:00', NULL),
  (7, 2, 'shipped',     780000, '2026-04-02 09:30:00', '2026-04-03 10:00:00'),
  (8, 6, 'pending',    8990000, '2026-04-05 19:00:00', NULL);

INSERT INTO order_items (order_id, product_id, qty, unit_price) VALUES
  (1, 1, 1,  8990000), (1, 5, 1,   150000),
  (2, 3, 1, 18500000),
  (3, 2, 1, 15990000),
  (4, 7, 1,   180000),
  (5, 7, 1,   180000), (5, 8, 1,   250000),
  (6, 2, 1, 15990000), (6, 6, 1,   390000),
  (7, 6, 2,   390000),
  (8, 1, 1,  8990000);
```

Kiểm tra nhanh sau khi nạp (đếm số dòng mỗi bảng; `COUNT(*)` học kỹ ở
[chương 08](08-group-by-aggregate.md)):

```sql
SELECT COUNT(*) FROM users;        -- 6
SELECT COUNT(*) FROM categories;   -- 6
SELECT COUNT(*) FROM products;     -- 9
SELECT COUNT(*) FROM orders;       -- 8
SELECT COUNT(*) FROM order_items;  -- 11
```

### 2.4 Toàn cảnh dữ liệu

Dữ liệu cố tình nhỏ để bạn tự tính kết quả bằng tay rồi so với máy. Hãy giữ mục này trong tầm mắt
khi đọc các mục sau.

`users`

| id | email | name | city | phone | created_at |
|---|---|---|---|---|---|
| 1 | an@example.com | Nguyễn Văn An | Hà Nội | 0901000001 | 2026-01-05 09:00:00 |
| 2 | binh@example.com | Trần Thị Bình | Hồ Chí Minh | NULL | 2026-01-12 14:30:00 |
| 3 | chi@example.com | Lê Minh Chi | Đà Nẵng | 0901000003 | 2026-02-01 08:15:00 |
| 4 | dung@example.com | Phạm Quốc Dũng | Hà Nội | 0901000004 | 2026-02-20 20:45:00 |
| 5 | em@example.com | Hoàng Thu Em | NULL | NULL | 2026-03-03 11:00:00 |
| 6 | giang@example.com | Vũ Hương Giang | Hồ Chí Minh | 0901000006 | 2026-03-15 16:20:00 |

`categories` (cây: Điện tử > Điện thoại > Phụ kiện điện thoại; Điện tử > Laptop; Sách > Sách lập trình)

| id | name | parent_id |
|---|---|---|
| 1 | Điện tử | NULL |
| 2 | Điện thoại | 1 |
| 3 | Laptop | 1 |
| 4 | Phụ kiện điện thoại | 2 |
| 5 | Sách | NULL |
| 6 | Sách lập trình | 5 |

`products`

| id | sku | name | category_id | price | stock |
|---|---|---|---|---|---|
| 1 | DT-X1 | Điện thoại X1 | 2 | 8990000 | 25 |
| 2 | DT-X2P | Điện thoại X2 Pro | 2 | 15990000 | 8 |
| 3 | LT-L14 | Laptop L14 | 3 | 18500000 | 5 |
| 4 | LT-L16P | Laptop L16 Pro | 3 | 32000000 | 0 |
| 5 | PK-OP1 | Ốp lưng X1 | 4 | 150000 | 100 |
| 6 | PK-SAC30 | Sạc nhanh 30W | 4 | 390000 | 40 |
| 7 | SA-SQL | Sách SQL căn bản | 6 | 180000 | 30 |
| 8 | SA-PHP | Sách PHP hiện đại | 6 | 250000 | 12 |
| 9 | GC_500K | Thẻ quà tặng 500k | NULL | 500000 | 1000 |

`orders`

| id | user_id | status | total | created_at | shipped_at |
|---|---|---|---|---|---|
| 1 | 1 | shipped | 9140000 | 2026-03-02 10:15:00 | 2026-03-04 09:00:00 |
| 2 | 2 | shipped | 18500000 | 2026-03-05 08:05:00 | 2026-03-07 15:30:00 |
| 3 | 3 | cancelled | 15990000 | 2026-03-10 13:00:00 | NULL |
| 4 | 1 | paid | 180000 | 2026-03-20 21:40:00 | NULL |
| 5 | 3 | pending | 430000 | 2026-03-31 23:59:59 | NULL |
| 6 | 4 | paid | 16380000 | 2026-04-01 00:00:00 | NULL |
| 7 | 2 | shipped | 780000 | 2026-04-02 09:30:00 | 2026-04-03 10:00:00 |
| 8 | 6 | pending | 8990000 | 2026-04-05 19:00:00 | NULL |

`order_items`

| order_id | product_id | qty | unit_price |
|---|---|---|---|
| 1 | 1 | 1 | 8990000 |
| 1 | 5 | 1 | 150000 |
| 2 | 3 | 1 | 18500000 |
| 3 | 2 | 1 | 15990000 |
| 4 | 7 | 1 | 180000 |
| 5 | 7 | 1 | 180000 |
| 5 | 8 | 1 | 250000 |
| 6 | 2 | 1 | 15990000 |
| 6 | 6 | 1 | 390000 |
| 7 | 6 | 2 | 390000 |
| 8 | 1 | 1 | 8990000 |

Vài "điểm đặc biệt" được cài sẵn để các chương sau có chất liệu:

- Khách số 5 (Em) chưa có đơn nào và không có `city`, `phone`: dùng cho `LEFT JOIN`, anti-join
  ([chương 07](07-join.md)) và các bài về NULL ([chương 06](06-ham-bieu-thuc-null.md)).
- Sản phẩm 4 (Laptop L16 Pro) và 9 (thẻ quà tặng) chưa bán được cái nào; sản phẩm 9 không thuộc danh
  mục nào và có `sku` chứa dấu gạch dưới `_` (dùng ở mục 5.6 về `LIKE`).
- Đơn 5 tạo lúc `2026-03-31 23:59:59` và đơn 6 tạo đúng `2026-04-01 00:00:00`: hai đơn nằm sát ranh
  giới tháng, dùng ở mục 5.5 về `BETWEEN`.
- Cột `total` của đơn bằng tổng `qty * unit_price` của các dòng hàng trong đơn đó (đơn 7 mua 2 cái
  sạc nên 780000). Bạn có thể tự kiểm lại.

Nếu bạn làm hỏng dữ liệu khi thử các lệnh `INSERT`, `UPDATE`, `DELETE` ở các mục sau, chỉ cần nạp
lại `shop.sql`.

## 3. INSERT: thêm dữ liệu

Các ví dụ trong mục này thay đổi dữ liệu. Những con số `id` được nêu giả sử bạn bắt đầu từ dữ liệu
vừa nạp và chạy các ví dụ theo đúng thứ tự. Xong mục 3, hãy nạp lại `shop.sql` để các kết quả ở mục
4 trở đi khớp với bảng ở mục 2.4.

### 3.1 Cú pháp cơ bản

`INSERT` thêm dòng mới vào một bảng. Dạng hay dùng nhất:

```sql
INSERT INTO tên_bảng (cột_1, cột_2, ...)
VALUES (giá_trị_1, giá_trị_2, ...);
```

Giá trị thứ nhất vào cột thứ nhất trong danh sách, giá trị thứ hai vào cột thứ hai, cứ thế. Ví dụ
thêm một khách hàng:

```sql
INSERT INTO users (email, name, city, phone)
VALUES ('hoa@example.com', 'Ngô Thanh Hoa', 'Cần Thơ', '0901000007');
```

mysql client trả lời (output minh hoạ, thời gian trong ngoặc mỗi máy mỗi khác):

```
Query OK, 1 row affected (0.01 sec)
```

"1 row affected" là số dòng mà câu lệnh đã tác động. Xem lại dòng vừa thêm:

```sql
SELECT * FROM users WHERE email = 'hoa@example.com';
```

Kết quả mong đợi: một dòng có `id = 7`, `city = 'Cần Thơ'`, và `created_at` là thời điểm bạn chạy
lệnh. Câu `INSERT` không hề nhắc tới `id` và `created_at`, vậy giá trị của chúng từ đâu ra? Mục 3.2
trả lời.

Số giá trị phải khớp số cột trong danh sách, thiếu hay thừa đều bị từ chối ngay:

```sql
INSERT INTO users (email, name, city) VALUES ('x@example.com', 'X');
-- ERROR 1136 (21S01): Column count doesn't match value count at row 1
```

⚠️ Luôn ghi danh sách cột. SQL cho phép bỏ danh sách cột, nhưng khi đó bạn phải đưa giá trị cho mọi
cột, đúng theo thứ tự các cột trong bảng:

```sql
-- Ví dụ để đọc, đừng tập viết kiểu này
INSERT INTO users VALUES (NULL, 'ha@example.com', 'Mai Thu Hà', 'Hà Nội', '0901000008', NOW());
```

Câu này phụ thuộc vào số cột và thứ tự cột của bảng tại thời điểm viết. Khi có người thêm một cột
(`ALTER TABLE users ADD COLUMN ...`, [chương 04](04-ddl-constraint.md)), nó bắt đầu báo lỗi 1136.
Tệ hơn, nếu bảng ở môi trường khác được tạo với hai cột cùng kiểu đổi chỗ cho nhau (chẳng hạn
`city` và `phone`, đều là `VARCHAR`), câu lệnh vẫn chạy "thành công" và lặng lẽ ghi số điện thoại
vào cột thành phố. Có danh sách cột thì câu lệnh tự mô tả và không phụ thuộc thứ tự cột.

MySQL còn có dạng `INSERT ... SET`, viết từng cặp cột = giá trị như `UPDATE`:

```sql
INSERT INTO users SET email = 'tam@example.com', name = 'Đinh Văn Tâm';
```

Dạng này dễ đọc khi có nhiều cột, nhưng là mở rộng riêng của MySQL (PostgreSQL không có) và chỉ
thêm được một dòng mỗi câu. Phần còn lại của giáo trình dùng dạng `VALUES`.

### 3.2 Cột không được nhắc tới nhận giá trị gì

Khi một cột không có trong danh sách cột, MySQL tự điền theo định nghĩa cột (đã học ở chương 04):

| Định nghĩa cột | Không nhắc tới trong `INSERT` thì | Ví dụ trong `shop` |
|---|---|---|
| `AUTO_INCREMENT` | Nhận số tiếp theo của bộ đếm | `users.id`, `orders.id` |
| Có `DEFAULT ...` | Nhận giá trị mặc định | `orders.status` thành `'pending'`, `created_at` thành thời điểm hiện tại, `products.stock` thành `0` |
| Cho phép NULL, không có `DEFAULT` | Nhận `NULL` | `users.city`, `users.phone` |
| `NOT NULL`, không có `DEFAULT` | Lỗi (khi bật strict mode, mặc định của MySQL 8.4) | `users.name`, `products.price` |

Dòng cuối là lưới an toàn quan trọng:

```sql
INSERT INTO users (email) VALUES ('x@example.com');
-- ERROR 1364 (HY000): Field 'name' doesn't have a default value
```

*Strict mode* (`STRICT_TRANS_TABLES` nằm trong `sql_mode` mặc định) biến những tình huống "thiếu giá
trị" hoặc "giá trị sai kiểu" thành lỗi. Khi tắt strict mode, MySQL lặng lẽ điền một giá trị ngầm
định (chuỗi rỗng, số 0...) kèm một warning mà hầu như không ai đọc. Đừng tắt nó.

Về `AUTO_INCREMENT`: nếu bạn tự ghi một giá trị cho cột này (như script ở mục 2.3 ghi `id` từ 1 tới
6), bộ đếm được đặt lại để số tự sinh tiếp theo nối sau giá trị lớn nhất trong cột. Vì vậy khách
hàng đầu tiên được thêm sau khi nạp dữ liệu nhận `id = 7`. Ghi `NULL` hoặc `0` vào cột này thì MySQL
vẫn tự sinh số (trường hợp `0` có ngoại lệ khi bật mode `NO_AUTO_VALUE_ON_ZERO`).

Muốn ghi rõ "dùng giá trị mặc định" ngay trong `VALUES`, dùng từ khoá `DEFAULT`:

```sql
INSERT INTO products (sku, name, category_id, price, stock)
VALUES ('PK-CAP1', 'Cáp USB-C 1m', 4, 90000, DEFAULT);   -- stock nhận DEFAULT là 0
```

Sản phẩm này nhận `id = 10` (bảng `products` đang có id lớn nhất là 9).

### 3.3 Lấy id vừa sinh: LAST_INSERT_ID()

Sau khi thêm một đơn hàng, ứng dụng gần như luôn cần biết `id` của đơn để thêm tiếp các dòng
`order_items`. Hàm `LAST_INSERT_ID()` trả về giá trị `AUTO_INCREMENT` đầu tiên được tự sinh bởi câu
`INSERT` thành công gần nhất trong cùng kết nối:

```sql
SELECT LAST_INSERT_ID();   -- 10, id của sản phẩm 'PK-CAP1' vừa thêm ở mục 3.2
```

Ba điều cần nhớ:

- Giá trị được lưu theo từng kết nối (*per-connection*). Client khác thêm dòng cùng lúc cũng không
  làm thay đổi kết quả của bạn. Đó chính là lý do phải dùng hàm này, thay vì tự tìm id lớn nhất.
- Nếu một câu `INSERT` thêm nhiều dòng (mục 3.4), hàm trả về id của dòng *đầu tiên*, không phải
  dòng cuối.
- Tự ghi giá trị cho cột `AUTO_INCREMENT` (không phải `NULL`, không phải `0`) thì `LAST_INSERT_ID()`
  không đổi, vì không có số nào được tự sinh.

⚠️ Đừng dùng `SELECT MAX(id)` để đoán id vừa thêm. Hai kết nối chạy xen kẽ là đủ làm nó sai:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `INSERT INTO products ...` | | A được id 11 |
| 2 | | `INSERT INTO products ...` | B được id 12 |
| 3 | `SELECT MAX(id) FROM products;` | | Ra 12: A tưởng 12 là của mình, sai |
| 4 | `SELECT LAST_INSERT_ID();` | | Ra 11: đúng, không bị B ảnh hưởng |

Từ PHP, PDO có method `lastInsertId()` cho cùng mục đích, Laravel có `insertGetId()`
([chương 19](19-database-tu-ung-dung.md)). PostgreSQL không có `LAST_INSERT_ID()` mà dùng
`RETURNING` (mục 3.7).

### 3.4 Thêm nhiều dòng trong một câu

Một câu `INSERT` có thể mang nhiều bộ giá trị, mỗi bộ trong một cặp ngoặc, cách nhau bởi dấu phẩy.
Script ở mục 2.3 đã dùng cách này.

```sql
INSERT INTO users (email, name, city) VALUES
  ('khanh@example.com', 'Đặng Gia Khánh', 'Huế'),
  ('lan@example.com',   'Bùi Ngọc Lan',   NULL);
```

Output minh hoạ:

```
Query OK, 2 rows affected (0.01 sec)
Records: 2  Duplicates: 0  Warnings: 0
```

Với câu nhiều dòng, MySQL in thêm một dòng thông tin: `Records` là số dòng câu lệnh đã xử lý,
`Duplicates` là số dòng không thêm được vì trùng giá trị của một unique index (sẽ gặp ở mục 3.6),
`Warnings` là số lần một giá trị có vấn đề. Sau câu này, `SELECT LAST_INSERT_ID()` trả về id của
Khánh (dòng đầu), không phải của Lan.

Vì sao nên gộp nhiều dòng vào một câu thay vì chạy từng câu một dòng? Mỗi câu lệnh đều tốn chi phí
cố định: gửi câu qua mạng, server phân tích (*parse*) câu, và khi ở chế độ autocommit thì thêm một
lần commit ([chương 13](13-transaction-acid.md)). Tài liệu MySQL ghi rằng thêm nhiều dòng bằng một
câu `INSERT` nhiều bộ `VALUES` nhanh hơn đáng kể (có trường hợp nhanh hơn nhiều lần) so với nhiều câu
một dòng. Khi nạp hàng chục nghìn dòng, hãy chia thành nhiều câu, mỗi câu một lô vừa phải, vì toàn
bộ câu lệnh phải nằm gọn trong một gói tin không vượt quá `max_allowed_packet` (mặc định 64MB ở
MySQL 8.4).

⚠️ Một câu là một khối "tất cả hoặc không có gì". Với bảng InnoDB, nếu một dòng bất kỳ trong câu bị
lỗi (trùng khoá, sai kiểu khi đang strict mode...), cả câu bị huỷ, kể cả những dòng đứng trước dòng
lỗi:

```sql
INSERT INTO users (email, name) VALUES
  ('minh@example.com', 'Lý Minh'),
  ('an@example.com',   'Trùng email');   -- email này đã thuộc về khách số 1
-- ERROR 1062 (23000): Duplicate entry 'an@example.com' for key 'users.uq_users_email'

SELECT * FROM users WHERE email = 'minh@example.com';   -- rỗng: dòng của Minh cũng không được thêm
```

Đây là điều tốt: bạn không bao giờ phải đoán "câu lỗi đã thêm được bao nhiêu dòng rồi".

### 3.5 INSERT ... SELECT: thêm dòng lấy từ một truy vấn

Thay vì tự viết `VALUES`, bạn có thể lấy kết quả của một câu `SELECT` làm các dòng cần thêm. Ứng
dụng điển hình: sao chép dữ liệu, lưu trữ (*archive*) dòng cũ sang bảng khác. Ví dụ chuyển các đơn
đã huỷ sang bảng lưu trữ:

```sql
-- Bảng rỗng có cùng cột và index với orders (CREATE TABLE ... LIKE không chép khoá ngoại)
CREATE TABLE orders_archive LIKE orders;

INSERT INTO orders_archive (id, user_id, status, total, created_at, shipped_at)
SELECT id, user_id, status, total, created_at, shipped_at
FROM orders
WHERE status = 'cancelled'
ORDER BY id;
```

Output minh hoạ:

```
Query OK, 1 row affected (0.01 sec)
Records: 1  Duplicates: 0  Warnings: 0
```

`SELECT * FROM orders_archive;` cho đúng một dòng: đơn số 3, đơn duy nhất có trạng thái
`cancelled`. (Phần "xoá đơn đã lưu trữ khỏi bảng gốc" để dành cho mục 10, khi học `DELETE`.)

Ba điểm cần để ý:

- Cột được ghép theo *vị trí*, không theo tên. Cột thứ nhất của `SELECT` vào cột thứ nhất trong danh
  sách của `INSERT`, bất kể tên là gì. Viết nhầm thứ tự hai cột cùng kiểu trong `SELECT` thì dữ liệu
  bị tráo cột mà không có lỗi nào.
- Không có `ORDER BY` thì thứ tự các dòng mà `SELECT` trả về là không xác định (mục 4.5). Tài liệu
  MySQL khuyên luôn kèm `ORDER BY` cho `INSERT ... SELECT` khi có replication, để server chính và
  bản sao thêm các dòng theo cùng một thứ tự, nhất là khi bảng đích có cột `AUTO_INCREMENT`
  ([chương 22](22-replication-ha.md)).
- Bảng đích được phép xuất hiện trong `FROM` của phần `SELECT` (thêm vào chính bảng đang đọc). Khi
  đó MySQL đọc hết kết quả `SELECT` vào một bảng tạm nội bộ trước rồi mới thêm, nên không có chuyện
  "vừa đọc vừa thêm" lặp vô hạn.

### 3.6 INSERT IGNORE: bỏ qua lỗi, và cái giá của nó

Chạy lại đúng câu `INSERT ... SELECT` ở mục 3.5 lần thứ hai. Đơn số 3 đã nằm trong `orders_archive`,
nên khoá chính bị trùng:

```sql
INSERT INTO orders_archive (id, user_id, status, total, created_at, shipped_at)
SELECT id, user_id, status, total, created_at, shipped_at
FROM orders WHERE status = 'cancelled' ORDER BY id;
-- ERROR 1062 (23000): Duplicate entry '3' for key 'orders_archive.PRIMARY'
```

Thêm từ khoá `IGNORE` thì lỗi được hạ thành *warning* (cảnh báo) và dòng trùng bị bỏ đi:

```sql
INSERT IGNORE INTO orders_archive (id, user_id, status, total, created_at, shipped_at)
SELECT id, user_id, status, total, created_at, shipped_at
FROM orders WHERE status = 'cancelled' ORDER BY id;
```

Output minh hoạ:

```
Query OK, 0 rows affected, 1 warning (0.00 sec)
Records: 1  Duplicates: 1  Warnings: 1
```

Xem warning bằng `SHOW WARNINGS`, chạy ngay sau câu lệnh vì nó chỉ hiện warning của câu lệnh gần
nhất (output minh hoạ):

```
+---------+------+--------------------------------------------------------+
| Level   | Code | Message                                                |
+---------+------+--------------------------------------------------------+
| Warning | 1062 | Duplicate entry '3' for key 'orders_archive.PRIMARY'   |
+---------+------+--------------------------------------------------------+
```

Đến đây `IGNORE` trông như đúng thứ ta cần: "thêm nếu chưa có". Nhưng `IGNORE` không chỉ bỏ qua
trùng khoá. Theo tài liệu MySQL, nó hạ một nhóm lỗi thành warning, và với lỗi chuyển đổi dữ liệu thì
nó sửa giá trị về "giá trị hợp lệ gần nhất" rồi vẫn ghi vào bảng, *kể cả khi đang bật strict mode*:

```sql
-- Ai đó gửi chữ vào ô số lượng tồn kho
INSERT IGNORE INTO products (sku, name, price, stock)
VALUES ('PK-TEST', 'Hàng thử', 120000, 'nhiều');
-- Query OK, 1 row affected, 1 warning   (output minh hoạ)

SHOW WARNINGS;
-- Warning | 1366 | Incorrect integer value: 'nhiều' for column 'stock' at row 1

SELECT stock FROM products WHERE sku = 'PK-TEST';   -- 0
```

Không có `IGNORE`, câu này bị từ chối với `ERROR 1366`. Có `IGNORE`, sản phẩm được tạo với tồn kho 0
và chỉ để lại một warning. Tương tự, dòng vi phạm khoá ngoại (ví dụ `user_id` không tồn tại) bị bỏ
qua lặng lẽ thay vì báo lỗi.

Tóm lại những gì `IGNORE` làm:

| Tình huống | Không có `IGNORE` (strict mode) | Có `IGNORE` |
|---|---|---|
| Trùng `PRIMARY KEY` hoặc `UNIQUE` | Lỗi 1062, cả câu bị huỷ | Dòng trùng bị bỏ, các dòng khác vẫn thêm, warning |
| Giá trị sai kiểu, tràn, quá dài | Lỗi, cả câu bị huỷ | Giá trị bị sửa về giá trị hợp lệ gần nhất rồi ghi, warning |
| Vi phạm khoá ngoại | Lỗi 1452, cả câu bị huỷ | Dòng vi phạm bị bỏ, warning |

Thêm hai hệ quả ít người biết:

- Dòng bị bỏ qua vẫn có thể "đốt" một giá trị `AUTO_INCREMENT`. Với InnoDB ở chế độ khoá
  auto-increment mặc định, bộ đếm vẫn tăng dù dòng không được thêm, nên id bị nhảy cóc. (Id có khoảng
  trống là chuyện bình thường; đừng bao giờ viết logic dựa trên việc id liền nhau.)
- Nếu dòng bị bỏ qua, `LAST_INSERT_ID()` giữ nguyên giá trị cũ, không phải id của một dòng mới.

⚠️ Quy tắc dùng: chỉ dùng `IGNORE` khi bạn thật sự chấp nhận mọi loại lỗi trong bảng trên bị nuốt,
và có kiểm tra số warning. Nếu ý định chỉ là "trùng thì thôi" hoặc "trùng thì cập nhật", MySQL có
`INSERT ... ON DUPLICATE KEY UPDATE` ([chương 09](09-subquery-cte-union.md)), chỉ phản ứng với trùng
khoá còn các lỗi khác vẫn là lỗi.

Liên hệ Laravel: `DB::table('users')->insertOrIgnore([...])` trên MySQL được dịch thành `insert ignore
into ...` (xem `MySqlGrammar::compileInsertOrIgnore` trong mã nguồn Laravel 13), và tài liệu Laravel
cũng cảnh báo rằng method này bỏ qua strict mode của MySQL. Trên PostgreSQL, cùng method đó được dịch
thành `... on conflict do nothing`, chỉ bỏ qua xung đột unique. Cùng một dòng code PHP, hai hành vi
khác nhau.

### 3.7 Đối chiếu PostgreSQL

| Việc | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| Nhiều dòng một câu | `VALUES (...), (...)` | Giống |
| `INSERT ... SELECT` | Có | Có |
| Lấy id vừa sinh | `LAST_INSERT_ID()` sau câu `INSERT` | `INSERT ... RETURNING id` trả về ngay trong câu `INSERT` |
| Bỏ qua dòng trùng | `INSERT IGNORE` (nuốt cả lỗi khác) | `ON CONFLICT DO NOTHING` (chỉ xung đột unique hoặc exclusion constraint) |
| `INSERT ... SET` | Có | Không có |

Ví dụ PostgreSQL (không chạy được trên MySQL):

```sql
-- PostgreSQL
INSERT INTO users (email, name) VALUES ('hoa@example.com', 'Ngô Thanh Hoa')
RETURNING id, created_at;    -- trả về luôn một dòng kết quả gồm id và created_at vừa sinh

INSERT INTO users (email, name) VALUES ('an@example.com', 'Trùng')
ON CONFLICT (email) DO NOTHING;   -- trùng email thì bỏ qua, không lỗi
```

`RETURNING` tiện hơn `LAST_INSERT_ID()` ở chỗ trả về được mọi cột (kể cả giá trị `DEFAULT` vừa điền)
của mọi dòng vừa thêm, trong cùng một lần gọi. MySQL không hỗ trợ `RETURNING`.

## 4. SELECT: chọn cột, alias, DISTINCT

Từ mục này trở đi, các kết quả mong đợi được tính trên dữ liệu gốc ở mục 2.4. Nếu đã thử các lệnh
ở mục 3, hãy nạp lại `shop.sql` trước.

### 4.1 Câu SELECT đơn giản nhất

`SELECT` đọc dữ liệu và trả về một *tập kết quả* (*result set*): một bảng tạm gồm các cột và các
dòng, chỉ để xem, không thay đổi gì trong database.

```sql
SELECT name, city FROM users;
```

Đọc là: "lấy cột `name` và `city` từ bảng `users`". Kết quả mong đợi (thứ tự dòng có thể khác, mục
4.5 giải thích vì sao):

| name | city |
|---|---|
| Nguyễn Văn An | Hà Nội |
| Trần Thị Bình | Hồ Chí Minh |
| Lê Minh Chi | Đà Nẵng |
| Phạm Quốc Dũng | Hà Nội |
| Hoàng Thu Em | NULL |
| Vũ Hương Giang | Hồ Chí Minh |

`SELECT *` lấy mọi cột theo thứ tự cột của bảng. Rất tiện khi khám phá dữ liệu trong mysql client,
nhưng trong code ứng dụng nên liệt kê cột cần dùng:

- Lấy thừa cột là tốn thêm I/O, băng thông mạng và bộ nhớ, nhất là khi bảng có cột `TEXT`/`JSON` lớn
  được thêm vào sau này mà code cũ không hề cần.
- Khi chỉ lấy đúng các cột có trong một index, MySQL có thể trả lời bằng index mà không cần đọc bảng
  (*covering index*, [chương 11](11-index.md)). `SELECT *` gần như luôn làm mất cơ hội này.
- Khi nối nhiều bảng ([chương 07](07-join.md)), `SELECT *` trả về nhiều cột trùng tên (ví dụ hai cột
  `id`). Mảng kết quả trong PHP chỉ giữ được một giá trị cho mỗi tên cột, nên một trong hai bị mất.

### 4.2 Biểu thức và alias cột

Danh sách sau `SELECT` không chỉ là tên cột mà có thể là biểu thức bất kỳ. Ví dụ tính giá trị hàng
tồn kho của từng sản phẩm:

```sql
SELECT sku, price, stock, price * stock AS stock_value
FROM products;
```

Kết quả mong đợi:

| sku | price | stock | stock_value |
|---|---|---|---|
| DT-X1 | 8990000 | 25 | 224750000 |
| DT-X2P | 15990000 | 8 | 127920000 |
| LT-L14 | 18500000 | 5 | 92500000 |
| LT-L16P | 32000000 | 0 | 0 |
| PK-OP1 | 150000 | 100 | 15000000 |
| PK-SAC30 | 390000 | 40 | 15600000 |
| SA-SQL | 180000 | 30 | 5400000 |
| SA-PHP | 250000 | 12 | 3000000 |
| GC_500K | 500000 | 1000 | 500000000 |

`AS stock_value` đặt *alias* (tên hiển thị) cho cột tính toán. Không có alias, tên cột trong kết quả
là nguyên văn biểu thức `price * stock`, vừa khó đọc vừa khó dùng trong code. Alias không thay đổi
gì trong bảng, nó chỉ là tên của cột trong tập kết quả. Các hàm dùng được trong biểu thức (nối chuỗi,
làm tròn, xử lý ngày giờ...) là chủ đề của [chương 06](06-ham-bieu-thuc-null.md). `SELECT` thậm chí
chạy được không cần bảng: `SELECT 1 + 1;` trả về `2`.

⚠️ Từ khoá `AS` là tuỳ chọn: `price * stock stock_value` cũng hợp lệ. Chính vì thế, quên một dấu
phẩy sẽ không báo lỗi mà biến cột thứ hai thành alias của cột thứ nhất:

```sql
SELECT name price FROM products;
-- Chạy bình thường: một cột duy nhất tên "price" nhưng chứa... tên sản phẩm
```

Tài liệu MySQL khuyên luôn viết `AS` tường minh để mắt người đọc bắt được lỗi này.

Alias có dấu cách hoặc ký tự đặc biệt thì phải bọc lại. Có ba cách, và chỉ một cách an toàn:

```sql
SELECT name AS `tên sản phẩm` FROM products;   -- backtick: cách quote tên (identifier) của MySQL
SELECT name AS 'tên sản phẩm' FROM products;   -- nháy đơn: MySQL chấp nhận trong danh sách SELECT
SELECT name AS "tên sản phẩm" FROM products;   -- nháy kép: cũng chạy trên MySQL mặc định
```

Cả ba đều chạy, nhưng tài liệu MySQL lưu ý: ở những chỗ khác trong câu lệnh, alias viết trong nháy
đơn hoặc nháy kép bị hiểu là *chuỗi*, không phải tên cột (mục 6.3 có ví dụ hậu quả). Thói quen tốt
nhất: đặt alias kiểu `snake_case` không dấu, không cần quote; nếu buộc phải quote thì dùng backtick.

Nhân tiện, về nháy kép: trong MySQL mặc định, `"paid"` là một chuỗi, giống `'paid'`. Trong chuẩn
SQL và PostgreSQL, `"paid"` là *tên cột* tên paid. Câu `WHERE status = "paid"` chạy đúng trên MySQL
nhưng báo lỗi không tìm thấy cột trên PostgreSQL (MySQL cũng hành xử như vậy nếu bật `sql_mode`
`ANSI_QUOTES`). Dùng nháy đơn cho chuỗi thì không bao giờ gặp chuyện này.

### 4.3 Alias bảng

Bảng cũng đặt alias được, thường là một hai chữ cái, để viết ngắn và để phân biệt khi một câu dùng
nhiều bảng:

```sql
SELECT p.sku, p.name, p.price
FROM products AS p
WHERE p.price > 20000000;
-- Kết quả mong đợi: một dòng, LT-L16P | Laptop L16 Pro | 32000000
```

`p.sku` nghĩa là "cột `sku` của bảng có alias `p`". Với một bảng thì alias chỉ để gọn; sang chương
07, khi nối nhiều bảng có cột trùng tên (bảng nào cũng có `id`), alias trở thành bắt buộc. Đã đặt
alias thì phải dùng alias: viết `products.sku` trong câu trên sẽ bị báo lỗi không tìm thấy cột.

### 4.4 DISTINCT: bỏ dòng trùng

Khách hàng của shop ở những thành phố nào?

```sql
SELECT city FROM users;            -- 6 dòng, "Hà Nội" và "Hồ Chí Minh" mỗi tên xuất hiện hai lần
SELECT DISTINCT city FROM users;   -- 4 dòng
```

Kết quả mong đợi của câu thứ hai (thứ tự có thể khác): `Hà Nội`, `Hồ Chí Minh`, `Đà Nẵng`, `NULL`.

Ba điều cần hiểu đúng về `DISTINCT`:

1. Nó áp dụng cho *cả dòng* của tập kết quả, tức tổ hợp mọi cột được chọn, không riêng cột đầu
   tiên:

   ```sql
   SELECT DISTINCT status FROM orders;            -- 4 dòng: shipped, cancelled, paid, pending
   SELECT DISTINCT user_id, status FROM orders;   -- 7 dòng: chỉ cặp (2, shipped) bị lặp (đơn 2 và 7)
   ```

2. Viết `SELECT DISTINCT(city), name` không làm `DISTINCT` chỉ áp lên `city`. `DISTINCT` không phải
   hàm; cặp ngoặc chỉ bao quanh biểu thức `city` và câu này giống hệt `SELECT DISTINCT city, name`,
   trả về 6 dòng vì không có hai người nào trùng cả tên lẫn thành phố.
3. Với `DISTINCT`, mọi giá trị NULL được coi là bằng nhau, nên chỉ còn một dòng `NULL`. (Đây là chỗ
   NULL được đối xử "bằng nhau"; phép so sánh `=` thì không, xem mục 5.7.) Chuỗi cũng được so theo
   collation: với `utf8mb4_0900_ai_ci`, `'Hà Nội'` và `'HÀ NỘI'` bị coi là trùng.

`DISTINCT` không miễn phí: để biết dòng nào trùng, MySQL thường phải dựng bảng tạm hoặc sắp xếp toàn
bộ kết quả (trừ khi có index phù hợp). Nếu bạn thấy mình thêm `DISTINCT` chỉ để "chữa" kết quả bị lặp dòng sau khi nối bảng, nhiều
khả năng câu JOIN đang sai (chương 07 gọi hiện tượng này là *fan-out*).

### 4.5 Không có ORDER BY thì không có thứ tự

Một bảng trong mô hình quan hệ là một *tập hợp* dòng, và tập hợp thì không có thứ tự. Khi câu
`SELECT` không có `ORDER BY`, database được quyền trả các dòng theo bất cứ thứ tự nào tiện nhất cho
nó. Tài liệu MySQL nói rõ thứ tự đó là *không xác định* (*nondeterministic*); tài liệu PostgreSQL
viết: thứ tự thực tế phụ thuộc kiểu quét, kiểu join và thứ tự trên đĩa, và "không được dựa vào".

Hôm nay `SELECT * FROM users` có thể trả về đúng thứ tự `id` vì InnoDB đọc bảng theo khoá chính.
Ngày mai, khi optimizer chọn đọc qua một index khác, hoặc câu lệnh có thêm `DISTINCT`, thứ tự đổi
mà không có cảnh báo nào. Quy tắc: thứ tự nào quan trọng với bạn thì phải viết ra bằng `ORDER BY`
(mục 6).

## 5. WHERE: lọc dòng

### 5.1 WHERE làm gì

`WHERE` đặt một điều kiện; database xét điều kiện đó cho *từng dòng* và chỉ giữ lại những dòng mà
điều kiện cho kết quả đúng (TRUE).

```sql
SELECT id, name, price FROM products WHERE price < 1000000;
```

Kết quả mong đợi:

| id | name | price |
|---|---|---|
| 5 | Ốp lưng X1 | 150000 |
| 6 | Sạc nhanh 30W | 390000 |
| 7 | Sách SQL căn bản | 180000 |
| 8 | Sách PHP hiện đại | 250000 |
| 9 | Thẻ quà tặng 500k | 500000 |

Một điều kiện trong SQL có thể ra ba kết quả chứ không phải hai: TRUE, FALSE, và UNKNOWN (không xác
định, xuất hiện khi có NULL tham gia). `WHERE` chỉ giữ dòng TRUE; dòng FALSE và dòng UNKNOWN đều bị
loại. Chi tiết logic ba giá trị ở [chương 06](06-ham-bieu-thuc-null.md); chương này chỉ cần nhớ hệ
quả ở các mục 5.3 và 5.7.

`WHERE` cũng là thứ quyết định một câu `UPDATE` hay `DELETE` tác động lên những dòng nào (mục 9,
10), nên mọi điều học ở mục này dùng lại nguyên vẹn ở đó.

### 5.2 Toán tử so sánh

| Toán tử | Nghĩa | Ví dụ |
|---|---|---|
| `=` | Bằng | `status = 'paid'` |
| `<>` hoặc `!=` | Khác (`<>` là chuẩn SQL) | `status <> 'shipped'` |
| `<`, `<=`, `>`, `>=` | Nhỏ hơn, nhỏ hơn hoặc bằng... | `total >= 1000000` |

So sánh dùng được cho số, chuỗi và ngày giờ:

```sql
SELECT id, status FROM orders WHERE status <> 'shipped';              -- đơn 3, 4, 5, 6, 8
SELECT id, created_at FROM orders WHERE created_at >= '2026-04-01';   -- đơn 6, 7, 8
```

Đơn 6 tạo đúng lúc `2026-04-01 00:00:00` nên thoả `>=`.

Chuỗi được so sánh theo *collation* của cột ([chương 03](03-kieu-du-lieu.md)). Collation mặc định
`utf8mb4_0900_ai_ci` không phân biệt hoa thường (`ci`, case-insensitive) và không phân biệt dấu
(`ai`, accent-insensitive), nên câu sau vẫn tìm ra hai khách ở Hà Nội:

```sql
SELECT id, name FROM users WHERE city = 'ha noi';   -- 1 Nguyễn Văn An, 4 Phạm Quốc Dũng
```

Tiện cho tìm kiếm, nhưng cũng có nghĩa là `'Hà Nội'` và `'ha noi'` bị coi là trùng nếu cột có ràng
buộc `UNIQUE`.

⚠️ So sánh hai giá trị khác kiểu làm MySQL tự chuyển kiểu ngầm (*implicit conversion*). Ví dụ cột
chuỗi `phone` so với một số, `WHERE phone = 901000001`, khiến MySQL đổi cả hai vế sang số thực rồi mới
so: số `'0901000001'` vẫn khớp (số 0 đầu bị mất khi đổi sang số), và index trên `phone` (nếu có)
không dùng được. Luôn so sánh cùng kiểu: chuỗi với chuỗi trong nháy đơn, số với số. Quy tắc chuyển kiểu
chi tiết ở [chương 06](06-ham-bieu-thuc-null.md), ảnh hưởng tới index ở [chương 11](11-index.md).

### 5.3 AND, OR, NOT và độ ưu tiên

Ghép nhiều điều kiện bằng `AND` (cả hai cùng đúng), `OR` (ít nhất một đúng), `NOT` (phủ định):

```sql
-- Khách ở Hồ Chí Minh đăng ký từ tháng 2 trở đi
SELECT id, name FROM users
WHERE city = 'Hồ Chí Minh' AND created_at >= '2026-02-01';     -- 6 Vũ Hương Giang

-- Đơn đã thanh toán hoặc đang chờ
SELECT id, status FROM orders
WHERE status = 'paid' OR status = 'pending';                     -- đơn 4, 5, 6, 8

-- Đơn không phải "đã giao" và cũng không phải "đã huỷ"
SELECT id, status FROM orders
WHERE NOT (status = 'shipped' OR status = 'cancelled');          -- đơn 4, 5, 6, 8
```

⚠️ `AND` được ưu tiên hơn `OR`, giống phép nhân được ưu tiên hơn phép cộng. Giả sử bạn muốn "các đơn
đang chờ hoặc đã thanh toán, có giá trị trên 1 triệu":

```sql
-- SAI: được hiểu là  pending  OR  (paid AND total > 1000000)
SELECT id, status, total FROM orders
WHERE status = 'pending' OR status = 'paid' AND total > 1000000;     -- đơn 5, 6, 8

-- ĐÚNG: ngoặc nói rõ ý định
SELECT id, status, total FROM orders
WHERE (status = 'pending' OR status = 'paid') AND total > 1000000;   -- đơn 6, 8
```

Câu sai trả về thêm đơn 5 (pending, 430000) vì vế `total > 1000000` chỉ gắn với `paid`. Không có lỗi
nào được báo; bạn chỉ nhận về số liệu sai. Quy tắc: hễ trộn `AND` với `OR` là đặt ngoặc, kể cả khi
bạn nhớ chắc độ ưu tiên, vì người đọc sau bạn chưa chắc nhớ.

Độ ưu tiên từ cao xuống thấp của các toán tử hay gặp trong `WHERE` (theo tài liệu MySQL): phép tính
số học, rồi nhóm so sánh (`=`, `<>`, `<`, `IS`, `LIKE`, `IN`...), rồi `BETWEEN`, rồi `NOT`, rồi `AND`,
cuối cùng là `OR`. MySQL còn nhận `&&`, `||`, `!` thay cho `AND`, `OR`, `NOT`, nhưng ba ký hiệu này
không chuẩn và đã bị đánh dấu *deprecated* (sẽ bị bỏ); đừng dùng.

⚠️ Cạm bẫy phủ định với NULL. "Khách không ở Hà Nội" có vẻ là bốn người (Bình, Chi, Em, Giang):

```sql
SELECT id, name, city FROM users WHERE city <> 'Hà Nội';   -- chỉ 3 dòng: 2, 3, 6
```

Em (id 5) có `city` là NULL. `NULL <> 'Hà Nội'` không phải TRUE mà là UNKNOWN (không biết Em ở đâu
thì không thể nói Em "không ở Hà Nội"), nên dòng bị loại. Muốn tính cả người chưa khai báo thành
phố, phải nói rõ:

```sql
SELECT id, name, city FROM users
WHERE city <> 'Hà Nội' OR city IS NULL;                      -- 4 dòng: 2, 3, 5, 6
```

### 5.4 IN và NOT IN

`IN (danh sách)` là cách viết gọn của một chuỗi `OR` với `=`:

```sql
SELECT id, status FROM orders WHERE status IN ('paid', 'shipped');   -- đơn 1, 2, 4, 6, 7
-- tương đương: WHERE status = 'paid' OR status = 'shipped'
```

`NOT IN` là phủ định của `IN`, và mang theo đúng cạm bẫy NULL ở mục trước:

```sql
SELECT id, name, city FROM users
WHERE city NOT IN ('Hà Nội', 'Hồ Chí Minh');    -- chỉ 3 Lê Minh Chi; Em (city NULL) bị loại
```

Tệ hơn, nếu *danh sách* có một NULL thì `NOT IN` không bao giờ đúng với dòng nào:

```sql
SELECT id, name FROM users WHERE city NOT IN ('Hà Nội', NULL);   -- rỗng
```

Lý do: với Chi, `'Đà Nẵng' IN ('Hà Nội', NULL)` không tìm được giá trị khớp nhưng danh sách có NULL,
nên theo chuẩn SQL kết quả là NULL (UNKNOWN) chứ không phải FALSE; phủ định của UNKNOWN vẫn là
UNKNOWN, dòng bị loại. Gõ tay một NULL vào danh sách thì hiếm, nhưng `NOT IN (SELECT ...)` với một
subquery trả về cột có NULL thì rất hay gặp, và đó là bug kinh điển
([chương 06](06-ham-bieu-thuc-null.md), [chương 09](09-subquery-cte-union.md)).

Tài liệu MySQL còn khuyên đừng trộn giá trị có nháy và không nháy trong cùng một danh sách `IN`
(`IN (1, 2, 'a')`), vì quy tắc so sánh chuỗi và số khác nhau, kết quả dễ sai lệch.

### 5.5 BETWEEN: trong một khoảng

`x BETWEEN a AND b` nghĩa là `a <= x AND x <= b`, *tính cả hai đầu mút*:

```sql
SELECT id, total FROM orders WHERE total BETWEEN 500000 AND 10000000;   -- đơn 1, 7, 8
```

Đơn 1 (9140000), 7 (780000), 8 (8990000) nằm trong khoảng. Hai lưu ý nhỏ: giá trị nhỏ phải đứng
trước (`BETWEEN 10000000 AND 500000` luôn rỗng), và `NOT BETWEEN a AND b` là `NOT (x BETWEEN a AND
b)`.

⚠️ Cạm bẫy kinh điển là dùng `BETWEEN` với cột `DATETIME`. "Các đơn trong tháng 3":

```sql
SELECT id, created_at FROM orders
WHERE created_at BETWEEN '2026-03-01' AND '2026-03-31';    -- đơn 1, 2, 3, 4: THIẾU đơn 5
```

Khi so một cột `DATETIME` với hằng chuỗi, MySQL đổi hằng sang kiểu ngày giờ; chuỗi `'2026-03-31'`
không có phần giờ nên thành `2026-03-31 00:00:00`. Đơn 5 tạo lúc `2026-03-31 23:59:59`, lớn hơn mốc
đó, nên bị loại. Sửa thành `BETWEEN '2026-03-01' AND '2026-04-01'` thì lại sai theo hướng ngược lại:
đơn 6 tạo đúng `2026-04-01 00:00:00` bị tính vào tháng 3. Cách đúng là khoảng nửa mở, gồm mốc đầu,
không gồm mốc cuối:

```sql
SELECT id, created_at FROM orders
WHERE created_at >= '2026-03-01' AND created_at < '2026-04-01';   -- đơn 1, 2, 3, 4, 5
```

Cách viết này đúng với mọi độ chính xác của thời gian (kể cả cột có phần lẻ giây như
`DATETIME(6)`), và vẫn dùng được index trên `created_at`. Đừng "vá" bằng `'2026-03-31 23:59:59'`:
một cột lưu phần lẻ giây sẽ có giá trị như `23:59:59.5` lọt ra ngoài.

### 5.6 LIKE: so khớp theo mẫu

`LIKE` so một chuỗi với một *mẫu* (*pattern*) có hai ký tự đại diện (*wildcard*):

| Ký tự | Khớp với | Ví dụ mẫu | Khớp | Không khớp |
|---|---|---|---|---|
| `%` | Bất kỳ chuỗi nào, kể cả chuỗi rỗng | `'PK-%'` | `PK-OP1`, `PK-SAC30` | `SA-PHP` |
| `_` | Đúng một ký tự bất kỳ | `'DT-X_'` | `DT-X1` | `DT-X2P` (thừa một ký tự) |

```sql
SELECT id, name FROM users WHERE name LIKE 'Nguyễn%';   -- bắt đầu bằng "Nguyễn": 1
SELECT id, name FROM users WHERE name LIKE '%Thị%';     -- chứa "Thị" ở bất kỳ đâu: 2
SELECT sku FROM products WHERE sku LIKE 'DT-X_';        -- DT-X1
```

Không có ký tự đại diện thì `LIKE` gần giống `=`: `sku LIKE 'DT-X1'` chỉ khớp đúng `DT-X1`.

`LIKE` cũng so theo collation, nên với collation mặc định thì không phân biệt hoa thường, không
phân biệt dấu: `name LIKE 'nguyen%'` vẫn khớp `Nguyễn Văn An`.

Muốn tìm chính ký tự `%` hoặc `_` thì phải *escape* (thoát nghĩa đặc biệt) nó. Ký tự escape mặc định
là dấu `\`, hoặc tự chọn ký tự khác bằng mệnh đề `ESCAPE`:

```sql
SELECT sku FROM products WHERE sku LIKE '%_%';                -- cả 9 sản phẩm: "_" khớp mọi ký tự
SELECT sku FROM products WHERE sku LIKE '%\_%';               -- GC_500K: "\_" là dấu gạch dưới thật
SELECT sku FROM products WHERE sku LIKE '%!_%' ESCAPE '!';    -- GC_500K, cách viết rõ ràng hơn
```

⚠️ Ba cạm bẫy:

- Dữ liệu người dùng nhập vào ô tìm kiếm có thể chứa `%` hoặc `_`. Nếu bạn ghép thẳng vào mẫu (kể
  cả khi đã dùng prepared statement để chống SQL injection), người dùng gõ `_` sẽ khớp mọi thứ. Hãy
  escape `%`, `_` và chính ký tự escape trước khi ghép vào mẫu.
- Trong chuỗi của MySQL, dấu `\` vốn đã là ký tự escape (như `\n` là xuống dòng). Muốn tìm một dấu
  `\` thật bằng `LIKE` phải viết `'%\\\\%'` (bốn dấu), vì chuỗi bị bỏ escape một lần khi phân tích câu
  lệnh và thêm một lần khi so mẫu. Đây là lý do dùng `ESCAPE` với một ký tự khác cho dễ đọc.
- Mẫu bắt đầu bằng `%` (`'%Thị%'`) không cho MySQL dùng index để nhảy thẳng tới vùng cần tìm, nên
  phải xét lần lượt mọi dòng; mẫu có phần đầu cố định (`'Nguyễn%'`) thì dùng được. Chi tiết ở [chương 11](11-index.md); tìm kiếm
  văn bản thật sự thì dùng full-text index.

Đối chiếu PostgreSQL: với collation mặc định, `LIKE` của PostgreSQL *phân biệt* hoa thường; muốn
không phân biệt thì dùng `ILIKE` (mở rộng riêng của PostgreSQL). Cùng một câu `LIKE 'nguyen%'`, MySQL
khớp mà PostgreSQL không.

### 5.7 IS NULL và IS NOT NULL

NULL nghĩa là "không có giá trị" hoặc "không biết". Nó không phải số 0, không phải chuỗi rỗng `''`.
Muốn tìm dòng có cột là NULL, phải dùng `IS NULL`; dùng `=` thì không bao giờ ra gì:

```sql
SELECT id, name FROM users WHERE phone = NULL;       -- rỗng, với MỌI dữ liệu
SELECT id, name FROM users WHERE phone IS NULL;      -- 2 Trần Thị Bình, 5 Hoàng Thu Em
SELECT id, name FROM users WHERE phone IS NOT NULL;  -- 1, 3, 4, 6
```

Lý do: mọi phép so sánh với NULL (`=`, `<>`, `<`...) đều cho UNKNOWN, kể cả `NULL = NULL`, nên điều
kiện không bao giờ TRUE. `IS NULL` là toán tử riêng, luôn trả về TRUE hoặc FALSE. Toán tử so sánh an
toàn với NULL `<=>`, hàm `COALESCE`, `IFNULL` và toàn bộ logic ba giá trị nằm ở
[chương 06](06-ham-bieu-thuc-null.md).

Tóm tắt mục 5 bằng một bảng:

| Muốn lọc | Viết | Lưu ý |
|---|---|---|
| Bằng, khác, lớn, nhỏ | `=`, `<>`, `<`, `<=`, `>`, `>=` | Chuỗi so theo collation; cùng kiểu hai vế |
| Nhiều điều kiện | `AND`, `OR`, `NOT` | `AND` trước `OR`: luôn đặt ngoặc khi trộn |
| Thuộc một danh sách | `IN (...)`, `NOT IN (...)` | `NOT IN` gặp NULL là hỏng |
| Trong một khoảng | `BETWEEN a AND b` | Tính cả hai đầu; ngày giờ dùng `>=` và `<` |
| Theo mẫu | `LIKE` với `%`, `_` | Escape ký tự đại diện trong dữ liệu người dùng |
| Là NULL | `IS NULL`, `IS NOT NULL` | Không bao giờ dùng `= NULL` |

## 6. ORDER BY: sắp xếp kết quả

### 6.1 Một cột, tăng và giảm dần

```sql
SELECT id, name, price FROM products ORDER BY price;
```

Kết quả mong đợi:

| id | name | price |
|---|---|---|
| 5 | Ốp lưng X1 | 150000 |
| 7 | Sách SQL căn bản | 180000 |
| 8 | Sách PHP hiện đại | 250000 |
| 6 | Sạc nhanh 30W | 390000 |
| 9 | Thẻ quà tặng 500k | 500000 |
| 1 | Điện thoại X1 | 8990000 |
| 2 | Điện thoại X2 Pro | 15990000 |
| 3 | Laptop L14 | 18500000 |
| 4 | Laptop L16 Pro | 32000000 |

Mặc định là tăng dần (`ASC`, ascending). Thêm `DESC` (descending) để giảm dần:
`ORDER BY price DESC` cho đúng bảng trên theo thứ tự ngược lại.

### 6.2 Nhiều cột

Khi giá trị cột thứ nhất bằng nhau, cột thứ hai quyết định thứ tự, cứ thế tiếp. Liệt kê đơn theo
trạng thái, trong cùng trạng thái thì đơn giá trị lớn đứng trước:

```sql
SELECT id, status, total FROM orders ORDER BY status, total DESC;
```

Kết quả mong đợi (chuỗi trạng thái sắp theo bảng chữ cái: cancelled, paid, pending, shipped):

| id | status | total |
|---|---|---|
| 3 | cancelled | 15990000 |
| 6 | paid | 16380000 |
| 4 | paid | 180000 |
| 8 | pending | 8990000 |
| 5 | pending | 430000 |
| 2 | shipped | 18500000 |
| 1 | shipped | 9140000 |
| 7 | shipped | 780000 |

⚠️ `ASC`/`DESC` gắn với *từng cột*, không áp cho cả danh sách. `ORDER BY status, total DESC` nghĩa là
`status ASC, total DESC`. Muốn cả hai giảm dần phải viết `ORDER BY status DESC, total DESC`.

### 6.3 Sắp theo alias, biểu thức, cột không được chọn

`ORDER BY` dùng được alias của `SELECT` (mục 8 giải thích vì sao), biểu thức, và cả cột không có
trong danh sách `SELECT`:

```sql
-- Theo alias: sản phẩm có giá trị tồn kho lớn nhất trước (GC_500K, DT-X1, DT-X2P, ...)
SELECT sku, price * stock AS stock_value FROM products ORDER BY stock_value DESC;

-- Theo biểu thức, kết quả như trên
SELECT sku FROM products ORDER BY price * stock DESC;

-- Theo cột không được chọn: khách đăng ký gần nhất trước (Giang, Em, Dũng, Chi, Bình, An)
SELECT name FROM users ORDER BY created_at DESC;
```

MySQL còn cho sắp theo *số thứ tự* cột trong danh sách `SELECT`: `ORDER BY 2` nghĩa là theo cột thứ
hai. Tài liệu MySQL ghi cách này đã *deprecated* vì chuẩn SQL đã bỏ cú pháp đó; nó cũng dễ vỡ khi ai
đó chèn thêm một cột vào `SELECT`. Hãy dùng tên hoặc alias.

⚠️ Hậu quả của alias trong nháy (đã nhắc ở mục 4.2):

```sql
SELECT sku, price * stock AS 'gia tri ton' FROM products
ORDER BY 'gia tri ton' DESC;       -- KHÔNG sắp xếp gì cả
```

Trong `ORDER BY`, `'gia tri ton'` là một hằng chuỗi, mọi dòng có cùng giá trị đó, nên câu lệnh chạy
không lỗi mà thứ tự kết quả là tuỳ ý. Viết `` ORDER BY `gia tri ton` DESC `` (backtick) thì mới đúng
là sắp theo alias.

### 6.4 NULL đứng ở đâu

Trong MySQL, NULL được coi là nhỏ hơn mọi giá trị khác: sắp tăng dần thì NULL đứng đầu, giảm dần thì
NULL đứng cuối.

```sql
SELECT id, name, city FROM users ORDER BY city, id;
```

Kết quả mong đợi:

| id | name | city |
|---|---|---|
| 5 | Hoàng Thu Em | NULL |
| 3 | Lê Minh Chi | Đà Nẵng |
| 1 | Nguyễn Văn An | Hà Nội |
| 4 | Phạm Quốc Dũng | Hà Nội |
| 2 | Trần Thị Bình | Hồ Chí Minh |
| 6 | Vũ Hương Giang | Hồ Chí Minh |

Với `ORDER BY city DESC, id`, Em xuống cuối. Tương tự, `SELECT id, sku FROM products ORDER BY
category_id` đưa thẻ quà tặng (`category_id` NULL) lên đầu.

PostgreSQL làm ngược lại: NULL được coi là *lớn hơn* mọi giá trị, nên mặc định đứng cuối khi tăng dần
và đứng đầu khi giảm dần. PostgreSQL có cú pháp `NULLS FIRST` / `NULLS LAST` để chọn tường minh;
MySQL không có cú pháp này. Cách đưa NULL xuống cuối khi tăng dần trên MySQL:

```sql
SELECT id, name, city FROM users ORDER BY city IS NULL, city, id;
-- 3 Đà Nẵng, 1 Hà Nội, 4 Hà Nội, 2 Hồ Chí Minh, 6 Hồ Chí Minh, 5 NULL
```

`city IS NULL` cho 0 với dòng có thành phố và 1 với dòng NULL; sắp tăng dần theo giá trị đó trước
thì các dòng NULL dồn xuống cuối.

| | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| NULL khi `ASC` | Đầu | Cuối |
| NULL khi `DESC` | Cuối | Đầu |
| Chọn vị trí NULL | Mẹo `ORDER BY col IS NULL, col` | `ORDER BY col NULLS FIRST` hoặc `NULLS LAST` |

Hai điều nữa về sắp chuỗi: thứ tự chuỗi do collation quyết định (với `utf8mb4_0900_ai_ci`, `'a'`,
`'A'`, `'á'` được coi là bằng nhau khi sắp), và số lưu trong cột chuỗi được sắp như chữ, nên `'10'`
đứng trước `'9'` (so ký tự đầu, `'1'` nhỏ hơn `'9'`). Lưu số thì dùng kiểu số.

### 6.5 Giá trị bằng nhau và thứ tự không tất định

```sql
SELECT id, status FROM orders ORDER BY status;
```

Kết quả chắc chắn có đơn 3 (cancelled) đứng đầu, rồi hai đơn paid, hai đơn pending, ba đơn shipped.
Nhưng giữa hai đơn paid (4 và 6), đơn nào đứng trước thì *không xác định*. Tài liệu MySQL nói rõ: khi
nhiều dòng có cùng giá trị ở các cột `ORDER BY`, server được trả chúng theo thứ tự bất kỳ, và thứ tự
đó có thể khác nhau giữa các lần chạy tuỳ kế hoạch thực thi; riêng việc thêm `LIMIT` cũng có thể làm
thứ tự này thay đổi.

Muốn thứ tự hoàn toàn xác định, thêm một cột có giá trị duy nhất làm "trọng tài" (*tie-breaker*),
thường là khoá chính:

```sql
SELECT id, status FROM orders ORDER BY status, id;   -- 3, 4, 6, 5, 8, 1, 2, 7: luôn như vậy
```

Điều này trông như chi tiết vụn vặt, nhưng nó là nguyên nhân của lỗi phân trang ở mục 7.3.

## 7. LIMIT và OFFSET: lấy một phần kết quả

### 7.1 LIMIT

`LIMIT n` giữ lại tối đa `n` dòng đầu tiên của kết quả. Đi cùng `ORDER BY`, nó trả lời các câu hỏi
"top N":

```sql
-- Ba sản phẩm đắt nhất
SELECT id, name, price FROM products ORDER BY price DESC LIMIT 3;
```

| id | name | price |
|---|---|---|
| 4 | Laptop L16 Pro | 32000000 |
| 3 | Laptop L14 | 18500000 |
| 2 | Điện thoại X2 Pro | 15990000 |

`LIMIT` cắt *sau* khi đã sắp xếp: MySQL không lấy ba dòng bất kỳ rồi mới sắp ba dòng đó. (Bên trong,
khi có `LIMIT`, MySQL được phép dừng sắp xếp ngay khi đã tìm đủ `n` dòng đầu, nên `ORDER BY ... LIMIT`
thường rẻ hơn sắp toàn bộ.)

### 7.2 OFFSET và phân trang

`OFFSET m` bỏ qua `m` dòng đầu rồi mới bắt đầu lấy. Phân trang danh sách sản phẩm, mỗi trang 3 sản
phẩm, sắp theo giá giảm dần (thêm `id` làm trọng tài):

```sql
SELECT id, name, price FROM products ORDER BY price DESC, id LIMIT 3 OFFSET 0;   -- trang 1: 4, 3, 2
SELECT id, name, price FROM products ORDER BY price DESC, id LIMIT 3 OFFSET 3;   -- trang 2: 1, 9, 6
SELECT id, name, price FROM products ORDER BY price DESC, id LIMIT 3 OFFSET 6;   -- trang 3: 8, 7, 5
SELECT id, name, price FROM products ORDER BY price DESC, id LIMIT 3 OFFSET 9;   -- trang 4: rỗng
```

Công thức: với trang `p` (đánh số từ 1) và kích thước trang `s`, viết `LIMIT s OFFSET (p - 1) * s`.
Phép tính phải làm ở ứng dụng, vì `LIMIT` chỉ nhận số nguyên không âm viết sẵn (hằng số), hoặc dấu
`?` trong prepared statement, hoặc biến trong stored procedure. `LIMIT 3 OFFSET (2 - 1) * 3` là lỗi cú
pháp.

MySQL còn có cách viết có dấu phẩy, đọc rất dễ nhầm:

```sql
SELECT id FROM products ORDER BY price DESC, id LIMIT 3, 3;   -- = LIMIT 3 OFFSET 3: trang 2
```

Trong `LIMIT a, b`, số *đầu* là offset, số *sau* mới là số dòng. Nên dùng dạng `LIMIT ... OFFSET ...`
cho rõ (và PostgreSQL chỉ nhận dạng này).

Giao diện phân trang thường cần tổng số dòng để vẽ "trang 1/3". Cách khuyến nghị là chạy thêm một câu
đếm riêng với cùng `WHERE`, không có `LIMIT`: `SELECT COUNT(*) FROM products;` cho 9. Cặp
`SQL_CALC_FOUND_ROWS` / `FOUND_ROWS()` mà bạn có thể thấy trong code cũ đã bị MySQL đánh dấu deprecated,
và chính tài liệu MySQL khuyên thay bằng câu `COUNT(*)` riêng.

### 7.3 Cạm bẫy của LIMIT/OFFSET

1. *LIMIT không có ORDER BY.* `SELECT ... LIMIT 10` trả về "10 dòng nào đó", có thể khác nhau giữa các
   lần chạy. Gần như mọi `LIMIT` trong code ứng dụng phải đi kèm `ORDER BY`.
2. *Sắp theo cột không duy nhất rồi phân trang.* Theo mục 6.5, các dòng bằng nhau có thể đổi chỗ giữa
   hai câu truy vấn, và câu của trang 1 khác câu của trang 2 (khác `OFFSET`) nên hoàn toàn có thể có
   kế hoạch thực thi khác. Hậu quả có thể xảy ra (ví dụ minh hoạ, mỗi trang 2 dòng, sắp theo `status`):

   | Bước | Truy vấn | Kết quả có thể nhận | Vấn đề |
   |---|---|---|---|
   | 1 | `ORDER BY status LIMIT 2 OFFSET 0` | đơn 3, đơn 6 | |
   | 2 | `ORDER BY status LIMIT 2 OFFSET 2` | đơn 6, đơn 5 | Đơn 6 xuất hiện hai lần, đơn 4 biến mất |

   Cách chữa: luôn có tie-breaker duy nhất, `ORDER BY status, id`.
3. *OFFSET lớn thì chậm.* Database không "nhảy" thẳng tới dòng thứ 100000 được; nó vẫn phải tạo ra
   và bỏ đi 100000 dòng đầu. Tài liệu PostgreSQL ghi rõ các dòng bị bỏ qua bởi `OFFSET` vẫn phải được
   tính bên trong server, và MySQL cũng vậy. Trang càng sâu càng chậm. Giải pháp là *keyset
   pagination*: thay vì đếm `OFFSET`, lọc bằng `WHERE` theo giá trị của dòng cuối cùng ở trang trước
   (học ở [chương 12](12-explain-toi-uu-query.md)).
4. *Dữ liệu thay đổi giữa hai lần bấm trang.* Một đơn mới được thêm vào đầu danh sách khiến mọi dòng
   lùi xuống một vị trí; người dùng sang trang 2 sẽ thấy lại dòng cuối của trang 1. `OFFSET` đếm vị
   trí, không nhớ "đã xem tới đâu"; keyset pagination thì nhớ.
5. *Truyền tham số cho LIMIT từ PHP.* Giá trị cho `LIMIT ?` phải được bind là số nguyên
   (`PDO::PARAM_INT`). Bind như chuỗi có thể sinh ra `LIMIT '10'` và lỗi cú pháp
   ([chương 19](19-database-tu-ung-dung.md)).

### 7.4 Đối chiếu PostgreSQL

| | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| `LIMIT n OFFSET m` | Có | Có |
| `LIMIT m, n` | Có | Không (báo lỗi "LIMIT #,# syntax is not supported") |
| Cú pháp chuẩn SQL `OFFSET m ROWS FETCH FIRST n ROWS ONLY` | Không | Có |
| Lấy thêm các dòng "hoà" với dòng cuối: `FETCH FIRST n ROWS WITH TIES` | Không | Có |
| `LIMIT` trong `UPDATE`/`DELETE` | Có (mục 9.5, 10.2) | Không |

## 8. Thứ tự viết và thứ tự thực thi logic của SELECT

### 8.1 Thứ tự viết

Các mệnh đề của `SELECT` phải được viết theo một thứ tự cố định; đảo chỗ (chẳng hạn `WHERE` đặt sau
`ORDER BY`) là lỗi cú pháp 1064:

```sql
SELECT [DISTINCT] danh_sách_biểu_thức
FROM bảng
WHERE điều_kiện_cho_từng_dòng
GROUP BY ...             -- chương 08
HAVING điều_kiện_cho_từng_nhóm   -- chương 08
ORDER BY ...
LIMIT ... OFFSET ...
```

### 8.2 Thứ tự thực thi logic

Thứ tự viết bắt đầu bằng `SELECT`, nhưng database *hiểu* câu lệnh theo một thứ tự khác. Thứ tự logic
này (mô tả trong tài liệu `SELECT` của PostgreSQL và phần window function của tài liệu MySQL) cho
biết mỗi mệnh đề "nhìn thấy" dữ liệu ở trạng thái nào:

```
 1. FROM / JOIN ... ON   lấy các dòng nguồn (nối bảng: chương 07)
 2. WHERE                lọc từng dòng
 3. GROUP BY             gom các dòng thành nhóm           (chương 08)
 4. HAVING               lọc từng nhóm                      (chương 08)
 5. Window function      tính các biểu thức OVER (...)      (chương 10)
 6. SELECT               tính các biểu thức, đặt alias
 7. DISTINCT             bỏ dòng trùng
 8. ORDER BY             sắp xếp
 9. LIMIT / OFFSET       cắt lấy một phần
```

Theo dõi từng bước với một câu cụ thể: "hai trạng thái đầu tiên theo bảng chữ cái, trong số các đơn
trên 1 triệu":

```sql
SELECT DISTINCT status
FROM orders
WHERE total > 1000000
ORDER BY status
LIMIT 2;
```

```
FROM orders            8 dòng: đơn 1..8
   |
WHERE total > 1000000  còn 5 dòng: đơn 1 (shipped), 2 (shipped), 3 (cancelled), 6 (paid), 8 (pending)
   |
SELECT status          shipped, shipped, cancelled, paid, pending
   |
DISTINCT               shipped, cancelled, paid, pending
   |
ORDER BY status        cancelled, paid, pending, shipped
   |
LIMIT 2                cancelled, paid          <- kết quả cuối cùng
```

### 8.3 Hệ quả: alias dùng được ở đâu, và các lỗi kinh điển

Từ thứ tự logic suy ra được hàng loạt quy tắc mà nếu học thuộc riêng lẻ thì rất dễ quên:

1. *`WHERE` không dùng được alias của `SELECT`*, vì `WHERE` (bước 2) chạy trước khi `SELECT` (bước 6)
   đặt alias:

   ```sql
   SELECT sku, price * stock AS stock_value
   FROM products
   WHERE stock_value > 100000000;
   -- ERROR 1054 (42S22): Unknown column 'stock_value' in 'where clause'
   ```

   Sửa bằng cách lặp lại biểu thức, `WHERE price * stock > 100000000` (ra GC_500K, DT-X1, DT-X2P),
   hoặc bọc câu trong một subquery ([chương 09](09-subquery-cte-union.md)).
2. *`ORDER BY` dùng được alias*, vì nó chạy sau `SELECT` (mục 6.3).
3. *`WHERE` không dùng được hàm tổng hợp* như `COUNT`, `SUM` (lỗi 1111, "Invalid use of group
   function"), vì lúc `WHERE` chạy chưa có nhóm nào. Lọc theo kết quả tổng hợp là việc của `HAVING`
   ([chương 08](08-group-by-aggregate.md)). Tương tự, window function không dùng được trong `WHERE`.
4. *`LIMIT` luôn cắt sau cùng*: sau `DISTINCT`, sau `ORDER BY`. Câu ví dụ ở mục 8.2 trả về hai
   *trạng thái khác nhau*, không phải "hai đơn đầu tiên rồi bỏ trùng".
5. *`DISTINCT` cùng `ORDER BY` theo cột không được chọn thì lỗi:*

   ```sql
   SELECT DISTINCT city FROM users ORDER BY created_at;
   -- ERROR 3065 (HY000): Expression #1 of ORDER BY clause is not in SELECT list, references
   -- column 'shop.users.created_at' which is not in SELECT list; this is incompatible with DISTINCT
   -- (output minh hoạ)
   ```

   Sau bước `DISTINCT`, dòng `'Hà Nội'` đại diện cho cả An (đăng ký 2026-01-05) lẫn Dũng
   (2026-02-20); sắp theo `created_at` nào? Không có câu trả lời, nên MySQL từ chối (PostgreSQL cũng
   vậy, với lỗi "for SELECT DISTINCT, ORDER BY expressions must appear in select list"). Không có
   `DISTINCT` thì không có vấn đề này, như ví dụ cuối mục 6.3.

MySQL có một mở rộng riêng: cho dùng alias của `SELECT` trong `GROUP BY` và `HAVING`. PostgreSQL cho
dùng trong `GROUP BY` nhưng không cho trong `HAVING`. Viết SQL chạy được ở nhiều hệ quản trị thì đừng
dựa vào alias ở hai chỗ này (chi tiết ở [chương 08](08-group-by-aggregate.md)).

### 8.4 Logic không phải là vật lý

Thứ tự ở mục 8.2 là thứ tự *logic*: kết quả cuối cùng phải giống như khi chạy lần lượt từng bước.
Còn *thực tế* bên trong, optimizer được tự do làm khác miễn là ra cùng kết quả: đọc theo một index
vốn đã có thứ tự để khỏi phải sắp, dừng sớm khi đã đủ số dòng của `LIMIT`, áp điều kiện `WHERE` ngay
khi đọc index... Vì vậy hai câu trả về cùng kết quả có thể chạy nhanh chậm rất khác nhau. Xem
optimizer thực sự làm gì bằng `EXPLAIN` là chủ đề của [chương 12](12-explain-toi-uu-query.md).

## 9. UPDATE: sửa dữ liệu

Như mục 3, các ví dụ từ đây thay đổi dữ liệu; nạp lại `shop.sql` khi cần đưa về ban đầu.

### 9.1 Cú pháp

```sql
UPDATE tên_bảng
SET cột_1 = giá_trị_1, cột_2 = giá_trị_2, ...
WHERE điều_kiện;
```

`UPDATE` tìm mọi dòng thoả `WHERE` (đúng như `WHERE` của `SELECT` ở mục 5) rồi gán giá trị mới cho
các cột trong `SET`. Ví dụ giảm giá Điện thoại X1, và chuyển đơn 6 sang "đã giao":

```sql
UPDATE products SET price = 8490000 WHERE id = 1;

UPDATE orders
SET status = 'shipped', shipped_at = '2026-04-06 08:00:00'
WHERE id = 6;
```

Mỗi câu in ra (output minh hoạ):

```
Query OK, 1 row affected (0.01 sec)
Rows matched: 1  Changed: 1  Warnings: 0
```

⚠️ Không có `WHERE` thì *mọi dòng* của bảng bị sửa. `UPDATE products SET price = 8490000;` biến
toàn bộ cửa hàng thành đồng giá 8.490.000 đồng, và không có câu hỏi "bạn có chắc không?" nào cả.
Mục 11 dành riêng cho cách phòng tránh.

### 9.2 Gán bằng biểu thức dùng giá trị hiện tại

Vế phải của `SET` có thể dùng chính giá trị hiện tại của dòng đang sửa:

```sql
-- Bán 2 ốp lưng: trừ tồn kho ngay trong database (100 -> 98)
UPDATE products SET stock = stock - 2 WHERE id = 5;

-- Sách lập trình tăng giá 10%: 180000 -> 198000, 250000 -> 275000
UPDATE products SET price = price * 1.1 WHERE category_id = 6;
```

Viết `stock = stock - 2` trong một câu tốt hơn nhiều so với cách "đọc tồn kho lên PHP, trừ 2, rồi
ghi số mới xuống": giữa lúc đọc và lúc ghi, một request khác có thể đã bán mất hàng, và một trong hai
lần trừ bị mất. Hiện tượng *lost update* này và các cách chống nó ở
[chương 14](14-isolation-mvcc.md).

### 9.3 Rows matched và Changed

```sql
UPDATE orders SET status = 'paid' WHERE id IN (4, 5);
```

Output minh hoạ:

```
Query OK, 1 row affected (0.01 sec)
Rows matched: 2  Changed: 1  Warnings: 0
```

Hai dòng thoả `WHERE` (*matched*), nhưng đơn 4 vốn đã là `paid`. Tài liệu MySQL ghi: nếu bạn gán cho
một cột đúng giá trị nó đang có, MySQL nhận ra và không cập nhật. Nên chỉ đơn 5 thật sự thay đổi
(*changed*), và con số "rows affected" mà `UPDATE` trả về mặc định là số dòng *đã thay đổi*: 1, không
phải 2.

Hệ quả cho code PHP: `PDOStatement::rowCount()` sau một câu `UPDATE` trên MySQL, và giá trị trả về
của `DB::table(...)->update([...])` trong Laravel (vốn lấy từ `rowCount()`), là số dòng đã thay đổi.
Viết `if ($affected === 0) { throw new NotFoundException(); }` sẽ báo "không tìm thấy" cho một dòng có
tồn tại, chỉ vì người dùng bấm lưu mà không sửa gì. Muốn nhận số dòng matched thì truyền tuỳ chọn
`Pdo\Mysql::ATTR_FOUND_ROWS => true` khi tạo kết nối PDO (tên cũ `PDO::MYSQL_ATTR_FOUND_ROWS`, bị
deprecated từ PHP 8.5), hoặc đơn giản là kiểm tra sự tồn tại bằng một câu `SELECT` riêng. PostgreSQL thì đếm cả các dòng matched
không đổi giá trị.

### 9.4 Thứ tự các phép gán trong SET

Trong chuẩn SQL, mọi biểu thức ở vế phải của `SET` đều dùng giá trị *cũ* của dòng (trước khi câu lệnh
chạy). MySQL thì khác: với `UPDATE` một bảng, các phép gán được thực hiện *lần lượt từ trái sang
phải*, và phép gán sau nhìn thấy giá trị mới mà phép gán trước vừa ghi. Ví dụ kinh điển là đổi chỗ
hai cột (chạy thử để quan sát, rồi nạp lại dữ liệu):

```sql
UPDATE users SET city = phone, phone = city WHERE id = 3;
SELECT city, phone FROM users WHERE id = 3;
```

| Hệ quản trị | `city` | `phone` | Giải thích |
|---|---|---|---|
| MySQL 8.4 | `0901000003` | `0901000003` | `phone = city` đọc `city` đã bị gán lại; `'Đà Nẵng'` mất hẳn |
| PostgreSQL 18 | `0901000003` | `Đà Nẵng` | Cả hai vế phải đều đọc giá trị cũ: đổi chỗ đúng |

Với `UPDATE` nhiều bảng, tài liệu MySQL còn nói không có bảo đảm nào về thứ tự các phép gán. Quy tắc
thực dụng: đừng viết một phép gán phụ thuộc vào cột vừa được gán trong cùng câu.

### 9.5 UPDATE với ORDER BY và LIMIT

Với `UPDATE` một bảng, MySQL cho thêm `ORDER BY` (sửa theo thứ tự nào) và `LIMIT` (tối đa bao nhiêu
dòng). Đây là mở rộng của MySQL; PostgreSQL không có `LIMIT` trong `UPDATE`.

```sql
-- Huỷ đơn pending cũ nhất (đơn 5, tạo 2026-03-31)
UPDATE orders SET status = 'cancelled'
WHERE status = 'pending'
ORDER BY created_at
LIMIT 1;
```

`LIMIT` ở đây giới hạn số dòng *matched*: câu lệnh dừng khi đã tìm đủ số dòng thoả `WHERE`, dù các
dòng đó có thực sự đổi giá trị hay không. Công dụng chính trong thực tế là sửa dữ liệu lớn theo từng
lô nhỏ (mục 10.2 có cùng ý tưởng cho `DELETE`). Luôn kèm `ORDER BY` khi dùng `LIMIT`, để biết chắc
những dòng nào bị sửa; tài liệu MySQL cũng cảnh báo `LIMIT` không có `ORDER BY` trong `UPDATE`,
`DELETE` là không an toàn với replication dạng statement-based ([chương 22](22-replication-ha.md)).

### 9.6 Vài dạng khác

- *UPDATE nhiều bảng*: sửa bảng này dựa trên dữ liệu bảng kia, ví dụ
  `UPDATE orders o JOIN users u ON u.id = o.user_id SET ... WHERE u.city = 'Hà Nội'`. Cần JOIN nên
  để dành cho [chương 07](07-join.md). Dạng này không dùng được `ORDER BY`, `LIMIT`.
- Một câu `UPDATE` (hoặc `DELETE`) không được đọc chính bảng đang sửa trong một subquery của nó; MySQL
  báo lỗi 1093. Cách vòng qua ở [chương 09](09-subquery-cte-union.md).
- `UPDATE IGNORE` có cùng tác dụng và cùng rủi ro như `INSERT IGNORE` (mục 3.6): dòng gây trùng
  unique bị bỏ qua, giá trị sai kiểu bị sửa về giá trị hợp lệ gần nhất. Hiếm khi là thứ bạn muốn.
- PostgreSQL có `UPDATE ... RETURNING` để lấy lại các dòng vừa sửa, và `UPDATE ... FROM` thay cho
  cú pháp JOIN của MySQL.

## 10. DELETE: xoá dữ liệu

### 10.1 Cú pháp và khoá ngoại

```sql
DELETE FROM tên_bảng WHERE điều_kiện;
```

Xoá khách số 5 (Em chưa có đơn nào):

```sql
DELETE FROM users WHERE id = 5;    -- Query OK, 1 row affected (output minh hoạ)
```

Còn xoá khách số 1 thì bị từ chối, vì An có đơn 1 và 4 trong bảng `orders`:

```sql
DELETE FROM users WHERE id = 1;
-- ERROR 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails
-- (`shop`.`orders`, CONSTRAINT `fk_orders_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`))
-- (output minh hoạ)
```

Khoá ngoại `fk_orders_user` không khai báo `ON DELETE`, nên InnoDB không cho xoá dòng cha khi còn
dòng con trỏ tới nó. Đây là bảo vệ, không phải trở ngại: nếu xoá được, các đơn của An sẽ trỏ tới một
khách không tồn tại. Muốn xoá thì phải xoá (hoặc chuyển) dòng con trước, hoặc khai báo khoá ngoại với
`ON DELETE CASCADE` / `SET NULL` ([chương 04](04-ddl-constraint.md)) nếu đó thật sự là nghiệp vụ mong
muốn.

Quay lại ví dụ lưu trữ ở mục 3.5: sau khi chép đơn đã huỷ sang `orders_archive`, xoá nó khỏi bảng gốc
phải đi theo thứ tự con trước, cha sau:

```sql
DELETE FROM order_items WHERE order_id = 3;   -- 1 dòng hàng của đơn 3
DELETE FROM orders WHERE id = 3;              -- rồi mới tới chính đơn 3
```

Chép sang bảng lưu trữ rồi xoá là nhiều câu lệnh phải cùng thành công hoặc cùng thất bại; gói chúng
trong một transaction là việc của [chương 13](13-transaction-acid.md).

Hai điều nữa về `DELETE`:

- Không có `WHERE` thì mọi dòng bị xoá. Muốn làm rỗng cả bảng một cách chủ động thì `TRUNCATE TABLE`
  nhanh hơn, nhưng nó là DDL với những khác biệt quan trọng (xem [chương 04](04-ddl-constraint.md)).
- Xoá dòng mang giá trị `AUTO_INCREMENT` lớn nhất không làm giá trị đó được dùng lại với InnoDB: khách
  hàng tiếp theo vẫn nhận số mới. Id bị "thủng" là chuyện bình thường.

### 10.2 Xoá theo lô với ORDER BY và LIMIT

Xoá vài triệu dòng log cũ bằng một câu `DELETE` duy nhất là một transaction khổng lồ: giữ khoá lâu,
sinh rất nhiều undo log, và làm các bản sao (replica) chậm theo. Cách làm phổ biến là xoá từng lô nhỏ,
lặp lại tới khi không còn dòng nào:

```sql
-- Bảng logs giả định (không có trong shop). Chạy lặp lại cho tới khi "0 rows affected".
DELETE FROM logs
WHERE created_at < '2026-01-01'
ORDER BY id
LIMIT 1000;
```

Giống `UPDATE`, `ORDER BY` và `LIMIT` chỉ dùng được với `DELETE` một bảng, và PostgreSQL không có
`LIMIT` trong `DELETE` (tài liệu PostgreSQL hướng dẫn cách thay thế bằng CTE). Batch delete và cách
chọn kích thước lô được bàn thêm ở [chương 12](12-explain-toi-uu-query.md).

### 10.3 Xoá thật hay xoá mềm

Nhiều ứng dụng không xoá dòng thật mà thêm một cột `deleted_at`: "xoá" là
`UPDATE ... SET deleted_at = NOW()`, và mọi câu đọc phải thêm `WHERE deleted_at IS NULL`. Laravel gọi
đó là *soft delete* (trait `SoftDeletes` của Eloquent tự thêm điều kiện này). Ưu điểm: khôi phục được,
giữ lịch sử. Cái giá: mọi truy vấn phải nhớ điều kiện lọc, bảng phình ra theo thời gian, và ràng buộc
`UNIQUE` (ví dụ email) phải được thiết kế lại vì dòng "đã xoá" vẫn chiếm giá trị. Đây là quyết định
thiết kế, không phải mặc định nên dùng cho mọi bảng.

## 11. Sửa và xoá an toàn

`UPDATE` và `DELETE` thiếu `WHERE`, hoặc có `WHERE` nhưng sai, là một trong những sự cố dữ liệu phổ
biến nhất. Không có lệnh "undo" nào sau khi đã commit; cứu dữ liệu lúc đó phải nhờ tới backup và
binlog ([chương 21](21-backup-restore.md)). Mục này gom các lớp phòng vệ, từ thói quen cá nhân tới
cấu hình.

### 11.1 Quy trình bốn bước khi sửa dữ liệu bằng tay

Giả sử cần huỷ mọi đơn `pending` tạo trước ngày 2026-04-01:

| Bước | Lệnh | Mục đích |
|---|---|---|
| 1 | `SELECT COUNT(*) FROM orders WHERE status = 'pending' AND created_at < '2026-04-01';` | Biết trước sẽ ảnh hưởng bao nhiêu dòng (ở đây: 1, đơn 5). Xem thêm vài dòng mẫu bằng `SELECT *` với cùng `WHERE` |
| 2 | `START TRANSACTION;` | Mở transaction: từ đây các thay đổi chưa được ghi vĩnh viễn |
| 3 | `UPDATE orders SET status = 'cancelled' WHERE status = 'pending' AND created_at < '2026-04-01';` | Dùng *đúng* `WHERE` của bước 1 (copy, đừng gõ lại). So "rows affected" với con số ở bước 1 |
| 4 | `SELECT ...` kiểm tra, rồi `COMMIT;` nếu đúng hoặc `ROLLBACK;` nếu sai | `ROLLBACK` huỷ toàn bộ thay đổi từ bước 2 |

Mặc định MySQL chạy ở chế độ *autocommit*: mỗi câu lệnh tự commit ngay khi chạy xong, nên một `UPDATE`
lỡ tay là vĩnh viễn ngay lập tức. `START TRANSACTION` tạm tắt cơ chế đó cho tới `COMMIT`/`ROLLBACK`.
Hai lưu ý: trong lúc transaction còn mở, các dòng bị sửa đang bị khoá, nên làm nhanh rồi kết thúc
([chương 15](15-lock-deadlock.md)); và câu DDL (`ALTER`, `DROP`, `TRUNCATE`...) tự commit transaction
đang mở, không rollback được. Transaction được học đầy đủ ở [chương 13](13-transaction-acid.md).

### 11.2 sql_safe_updates

MySQL có một lưới an toàn được thiết kế cho đúng lỗi "quên `WHERE`": biến hệ thống
`sql_safe_updates` (mặc định `OFF`). Khi bật, `UPDATE` và `DELETE` bị từ chối nếu `WHERE` không dùng
một key (cột có index) và câu lệnh cũng không có `LIMIT`; chỉ cần có một trong hai là câu được chạy.

```sql
SET sql_safe_updates = 1;   -- chỉ cho phiên (session) hiện tại

UPDATE products SET stock = 0;
-- ERROR 1175 (HY000): You are using safe update mode and you tried to update a table
-- without a WHERE that uses a KEY column. ...   (output minh hoạ)

UPDATE products SET stock = 0 WHERE name = 'Laptop L14';
-- Cũng lỗi 1175: name không có index nên WHERE không dùng key

UPDATE products SET stock = 0 WHERE id = 3;                    -- được: id là khoá chính
UPDATE products SET stock = 0 WHERE name = 'Laptop L14' LIMIT 1;   -- được: có LIMIT
```

Cách bật:

- Trong một phiên: `SET sql_safe_updates = 1;` (tắt lại: `SET sql_safe_updates = 0;`).
- Khi mở mysql client: tuỳ chọn `--safe-updates` (có tên khác vui vẻ là `--i-am-a-dummy`). Client sẽ
  tự chạy `SET sql_safe_updates=1, sql_select_limit=1000, max_join_size=1000000;` khi kết nối.
  Hai biến sau cũng là lưới an toàn: mọi `SELECT` không có `LIMIT` chỉ trả tối đa 1000 dòng, và câu
  `SELECT` nhiều bảng bị từ chối nếu server ước tính phải xét hơn 1.000.000 tổ hợp dòng.
- Bật vĩnh viễn cho client trên máy của bạn: thêm dòng `safe-updates` vào nhóm `[mysql]` trong file
  cấu hình `~/.my.cnf`.

```ini
# ~/.my.cnf trên máy của bạn (nhóm [mysql] chỉ áp cho chương trình mysql client)
[mysql]
safe-updates
```

⚠️ Hiểu đúng giới hạn của nó:

- Nó kiểm tra *hình thức* (có dùng key hay `LIMIT` không), không kiểm tra *ý nghĩa*. `WHERE` dùng khoá
  chính nhưng gõ sai điều kiện vẫn sửa nhầm hàng loạt; `LIMIT 1000000` vẫn qua được.
- Có `WHERE` theo key mà vẫn bị từ chối là chuyện có thể xảy ra, khi optimizer không dùng được index,
  ví dụ so cột chuỗi có index với một số (`WHERE sku = 123`, xem cạm bẫy ép kiểu ở mục 5.2). Tài liệu
  MySQL gợi ý chạy `EXPLAIN` cho câu lệnh đó rồi `SHOW WARNINGS` để xem lý do.
- Đây là thiết lập cho phiên làm việc của con người. Ứng dụng thường không bật nó; phòng vệ phía ứng
  dụng là review code, test, và user database chỉ có quyền tối thiểu
  ([chương 18](18-user-quyen-bao-mat.md)).

### 11.3 Từ phía ứng dụng

Code ứng dụng hiếm khi "quên" `WHERE` theo nghĩa đen, mà thường quên theo cách tinh vi hơn: điều
kiện được ghép động và có lúc rỗng. Ví dụ với Laravel, tài liệu query builder viết rõ
`DB::table('users')->delete()` xoá mọi dòng; chỉ khi có `->where(...)` đứng trước thì mới xoá có
điều kiện. Một hàm kiểu "xoá theo bộ lọc" nhận mảng bộ lọc rỗng từ request sẽ sinh ra đúng câu
`DELETE FROM users`. Phòng bằng cách kiểm tra trong code rằng bộ lọc không rỗng trước khi gọi
`update()`/`delete()` hàng loạt, và viết test cho trường hợp đó.

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| `UPDATE`/`DELETE` quên `WHERE` | Sửa hoặc xoá toàn bộ bảng, autocommit ghi vĩnh viễn ngay | `SELECT` trước với cùng `WHERE`, làm trong transaction, bật `sql_safe_updates` (mục 11) |
| `INSERT` không ghi danh sách cột | Phụ thuộc số cột và thứ tự cột; thêm cột là lỗi, đổi thứ tự là ghi nhầm cột | Luôn ghi danh sách cột (mục 3.1) |
| Dùng `INSERT IGNORE` để "bỏ qua trùng" | Nó nuốt cả lỗi sai kiểu (sửa giá trị thành giá trị gần nhất) và lỗi khoá ngoại | `ON DUPLICATE KEY UPDATE` ([chương 09](09-subquery-cte-union.md)), hoặc kiểm tra warning (mục 3.6) |
| `SELECT MAX(id)` để lấy id vừa thêm | Kết nối khác có thể vừa thêm dòng mới hơn | `LAST_INSERT_ID()`, PDO `lastInsertId()`, PostgreSQL `RETURNING` (mục 3.3) |
| Quên dấu phẩy giữa hai cột trong `SELECT` | Cột sau bị hiểu là alias của cột trước, không có lỗi | Luôn viết `AS` khi đặt alias (mục 4.2) |
| `WHERE col = NULL` | So sánh với NULL luôn ra UNKNOWN | `IS NULL`, `IS NOT NULL` (mục 5.7) |
| `col <> 'x'` hoặc `col NOT IN (...)` bỏ sót dòng NULL | `NULL <> 'x'` là UNKNOWN, dòng bị loại | Thêm `OR col IS NULL` nếu nghiệp vụ cần (mục 5.3, 5.4) |
| Trộn `AND` với `OR` không có ngoặc | `AND` được ưu tiên hơn `OR` | Luôn đặt ngoặc (mục 5.3) |
| `BETWEEN` với cột `DATETIME` | Mốc cuối `'2026-03-31'` thành `00:00:00`, mất gần trọn ngày cuối | `>= mốc_đầu AND < mốc_sau` (mục 5.5) |
| Ghép thẳng chữ người dùng gõ vào mẫu `LIKE` | `%`, `_` trong dữ liệu trở thành ký tự đại diện | Escape `%`, `_` và ký tự escape (mục 5.6) |
| Dựa vào thứ tự dòng khi không có `ORDER BY` | Thứ tự không xác định, đổi theo kế hoạch thực thi | Viết `ORDER BY` (mục 4.5) |
| Phân trang theo cột không duy nhất | Dòng bằng nhau đổi chỗ giữa các trang: lặp hoặc mất dòng | Thêm tie-breaker duy nhất, ví dụ `id` (mục 6.5, 7.3) |
| Đọc `LIMIT 10, 20` là "10 dòng" | Trong `LIMIT a, b`, `a` là offset | Viết `LIMIT 20 OFFSET 10` (mục 7.2) |
| Dùng alias của `SELECT` trong `WHERE` | `WHERE` chạy trước `SELECT`: lỗi 1054 | Lặp lại biểu thức hoặc dùng subquery (mục 8.3) |
| Alias trong nháy đơn dùng lại ở `ORDER BY` | Thành hằng chuỗi, không sắp gì cả | Không quote, hoặc quote bằng backtick (mục 6.3) |
| `rowCount() === 0` sau `UPDATE` coi là "không tìm thấy" | MySQL trả số dòng *changed*, dòng không đổi giá trị không được đếm | `Pdo\Mysql::ATTR_FOUND_ROWS` hoặc `SELECT` kiểm tra riêng (mục 9.3) |
| `SET a = b, b = a` để đổi chỗ hai cột | MySQL gán từ trái sang phải, phép gán sau thấy giá trị mới | Không viết phép gán phụ thuộc nhau trong một câu (mục 9.4) |

## Tóm tắt chương

- DML gồm bốn lệnh `INSERT`, `SELECT`, `UPDATE`, `DELETE`, ứng với CRUD. Bộ dữ liệu `shop` (năm bảng
  `users`, `categories`, `products`, `orders`, `order_items`) được dùng cho các chương sau; nạp lại
  `shop.sql` bất cứ lúc nào để về trạng thái ban đầu.
- `INSERT` luôn kèm danh sách cột; một câu có thể thêm nhiều dòng và là một khối "tất cả hoặc không"
  với InnoDB. `LAST_INSERT_ID()` cho id tự sinh (của dòng đầu tiên) theo từng kết nối.
- `INSERT ... SELECT` ghép cột theo vị trí. `INSERT IGNORE` hạ nhiều loại lỗi thành warning, kể cả
  lỗi sai kiểu và khoá ngoại, nên chỉ dùng khi chấp nhận được điều đó.
- `SELECT` nên liệt kê cột và đặt alias bằng `AS`; `DISTINCT` áp lên cả dòng; không có `ORDER BY`
  thì không có thứ tự.
- `WHERE` chỉ giữ dòng có điều kiện TRUE; NULL làm điều kiện thành UNKNOWN, nên `= NULL`, `<>`, `NOT IN`
  có thể âm thầm loại dòng. `AND` ưu tiên hơn `OR`; `BETWEEN` tính cả hai đầu; ngày giờ dùng khoảng
  nửa mở; `LIKE` có `%`, `_` và phải escape khi dữ liệu chứa chúng.
- `ORDER BY` có hướng riêng cho từng cột. MySQL đặt NULL đầu khi tăng dần, PostgreSQL đặt cuối. Thêm
  cột duy nhất làm tie-breaker để thứ tự tất định.
- `LIMIT n OFFSET m` cắt kết quả sau cùng; phân trang bằng `OFFSET` cần `ORDER BY` tất định và chậm
  dần khi trang sâu.
- Thứ tự logic: FROM, WHERE, GROUP BY, HAVING, window, SELECT, DISTINCT, ORDER BY, LIMIT. Từ đó suy
  ra alias không dùng được trong `WHERE` nhưng dùng được trong `ORDER BY`.
- `UPDATE` trả số dòng thực sự thay đổi; MySQL gán `SET` từ trái sang phải, khác chuẩn SQL.
  `UPDATE`/`DELETE` một bảng nhận được `ORDER BY ... LIMIT` để xử lý theo lô.
- Sửa xoá an toàn: `SELECT` đếm trước, transaction, so số dòng, `COMMIT`/`ROLLBACK`; `sql_safe_updates`
  chặn câu không dùng key và không có `LIMIT`, nhưng không thay được sự cẩn thận.

## Câu hỏi tự kiểm tra

1. Nêu hai tình huống mà một câu `INSERT` không ghi danh sách cột gây lỗi hoặc ghi sai dữ liệu.
   (mục 3.1)
2. Một câu `INSERT` ba dòng vào `users`, dòng thứ ba trùng email đã có. Sau câu lệnh, bảng có thêm bao
   nhiêu dòng? Nếu thêm `IGNORE` thì sao, và `LAST_INSERT_ID()` trả về gì? (mục 3.3, 3.4, 3.6)
3. Vì sao cùng một lời gọi `insertOrIgnore()` của Laravel lại có thể cho kết quả khác nhau trên MySQL
   và PostgreSQL khi dữ liệu có giá trị sai kiểu? (mục 3.6)
4. `SELECT DISTINCT user_id, status FROM orders` trả về bao nhiêu dòng trên dữ liệu mẫu? Vì sao không
   phải 5, số khách có đơn?
5. Trên bảng `users`, `WHERE city <> 'Hà Nội'` trả về bao nhiêu dòng? `WHERE city NOT IN ('Hà Nội',
   NULL)` thì sao? Giải thích từng dòng bị loại. (mục 5.3, 5.4)
6. Vì sao `created_at BETWEEN '2026-03-01' AND '2026-03-31'` bỏ sót dữ liệu, và vì sao sửa thành
   `'2026-04-01'` cũng sai?
7. Trên MySQL và trên PostgreSQL, NULL đứng ở đâu khi `ORDER BY ... ASC` và khi `DESC`? Viết câu đưa NULL
   xuống cuối khi sắp tăng dần trên MySQL.
8. Một API phân trang sắp đơn hàng theo `status`. Người dùng báo có đơn xuất hiện ở cả trang 1 lẫn
   trang 2. Giải thích nguyên nhân và cách sửa. (mục 6.5, 7.3)
9. Dựa vào thứ tự thực thi logic, giải thích: vì sao alias dùng được trong `ORDER BY` nhưng không trong
   `WHERE`; vì sao `SELECT DISTINCT city ... ORDER BY created_at` bị từ chối. (mục 8.3)
10. Khi bật `sql_safe_updates`, câu nào trong bốn câu sau bị từ chối: không `WHERE`; `WHERE` theo cột
    không có index; `WHERE` theo khoá chính; `WHERE` theo cột không có index kèm `LIMIT 1`? Kể một sai
    lầm mà `sql_safe_updates` không chặn được. (mục 11.2)

## Bài tập

**Bài 1. Truy vấn trên dữ liệu mẫu.** Với mỗi yêu cầu, tự tính kết quả bằng tay từ mục 2.4 *trước*,
rồi mới viết SQL và chạy để so:

- a. `sku`, `name`, `price` của các sản phẩm thuộc danh mục 2 hoặc 4, giá từ 300.000 tới 10.000.000
  đồng (tính cả hai đầu), sắp giá giảm dần.
- b. Khách hàng không có số điện thoại *hoặc* không ở Hà Nội (tính cả người chưa khai báo thành phố),
  sắp theo `name`.
- c. Các đơn tạo trong tháng 4/2026 mà chưa giao (`shipped_at` là NULL), dùng khoảng thời gian nửa mở.
- d. Trang 2 của danh sách đơn hàng, mỗi trang 3 đơn, đơn mới nhất trước, thứ tự phải tất định.
- e. Các trạng thái đơn khác nhau đang có, sắp theo bảng chữ cái, nhưng đặt `cancelled` cuối cùng
  (gợi ý: sắp theo một biểu thức trước).

**Bài 2. Thí nghiệm với INSERT ... SELECT và IGNORE.** Tạo bảng `newsletter (email VARCHAR(100) NOT
NULL PRIMARY KEY, city VARCHAR(50) NULL)`. Dùng `INSERT ... SELECT` chép email và thành phố của mọi
khách có `city` khác NULL. Chạy lại đúng câu đó lần hai, rồi lần ba với `IGNORE`. Ghi lại thông báo
`Records/Duplicates/Warnings` và `SHOW WARNINGS` của từng lần, giải thích bằng lời. Cuối cùng thêm một
cột `INT` vào bảng, thử `INSERT IGNORE` với một giá trị chữ vào cột đó và mô tả điều xảy ra.

**Bài 3. Sửa dữ liệu an toàn.** Bật `sql_safe_updates` trong phiên. Trước khi chạy, dự đoán câu nào bị
từ chối trong bốn câu ở câu hỏi 10, rồi chạy để kiểm chứng (trên bảng `products`). Sau đó thực hiện
đủ quy trình bốn bước ở mục 11.1 để tăng giá 5% cho các sản phẩm còn dưới 10 cái trong kho, nhưng kết
thúc bằng `ROLLBACK`, và chứng minh bằng một câu `SELECT` rằng dữ liệu vẫn nguyên như cũ.

**Bài 4 (PHP). Escape mẫu LIKE.** Viết hàm PHP `escapeLike(string $input): string` trả về chuỗi an
toàn để đặt vào mẫu `LIKE ... ESCAPE '!'` (dùng `!` làm ký tự escape như mục 5.6): mọi `!`, `%`, `_` trong
dữ liệu phải được thoát nghĩa. Viết vài dòng kiểm tra cho các đầu vào `'GC_500K'`, `'50%'`, `'a!b'` và
chuỗi rỗng, chạy bằng `docker run --rm -it -v "$PWD":/app -w /app php:8.5-cli php escape_like.php`.
Viết file với `declare(strict_types=1);` và so sánh bằng `===`.

## Đọc thêm

MySQL 8.4 Reference Manual:

- [INSERT Statement](https://dev.mysql.com/doc/refman/8.4/en/insert.html) và
  [INSERT ... SELECT](https://dev.mysql.com/doc/refman/8.4/en/insert-select.html)
- [UPDATE Statement](https://dev.mysql.com/doc/refman/8.4/en/update.html),
  [DELETE Statement](https://dev.mysql.com/doc/refman/8.4/en/delete.html)
- [SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html) (alias, `ORDER BY`, `LIMIT`)
- [Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) (strict mode, mục "The
  Effect of IGNORE on Statement Execution")
- [Information Functions](https://dev.mysql.com/doc/refman/8.4/en/information-functions.html)
  (`LAST_INSERT_ID()`, `ROW_COUNT()`, `FOUND_ROWS()`)
- [AUTO_INCREMENT Handling in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html),
  [InnoDB Error Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html)
- [Comparison Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/comparison-operators.html),
  [Logical Operators](https://dev.mysql.com/doc/refman/8.4/en/logical-operators.html),
  [Operator Precedence](https://dev.mysql.com/doc/refman/8.4/en/operator-precedence.html),
  [String Comparison Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/string-comparison-functions.html) (`LIKE`)
- [Problems with NULL Values](https://dev.mysql.com/doc/refman/8.4/en/problems-with-null.html),
  [Working with NULL Values](https://dev.mysql.com/doc/refman/8.4/en/working-with-null.html)
- [LIMIT Query Optimization](https://dev.mysql.com/doc/refman/8.4/en/limit-optimization.html)
- [mysql Client Tips](https://dev.mysql.com/doc/refman/8.4/en/mysql-tips.html) (mục "Using
  Safe-Updates Mode")
- [Schema Object Names](https://dev.mysql.com/doc/refman/8.4/en/identifiers.html) (quote tên và alias)
- [Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html)
  (vị trí của window function trong thứ tự thực thi)

PostgreSQL 18:

- [SELECT](https://www.postgresql.org/docs/18/sql-select.html) (mục "general processing of SELECT")
- [Sorting Rows (ORDER BY)](https://www.postgresql.org/docs/18/queries-order.html),
  [LIMIT and OFFSET](https://www.postgresql.org/docs/18/queries-limit.html)
- [INSERT](https://www.postgresql.org/docs/18/sql-insert.html),
  [UPDATE](https://www.postgresql.org/docs/18/sql-update.html),
  [DELETE](https://www.postgresql.org/docs/18/sql-delete.html)
- [Pattern Matching](https://www.postgresql.org/docs/18/functions-matching.html) (`LIKE`, `ILIKE`)

Laravel 13:

- [Database: Query Builder](https://laravel.com/docs/13.x/queries) (`insertOrIgnore`, `update`, `delete`)
