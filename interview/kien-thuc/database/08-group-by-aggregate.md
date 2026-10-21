# Chương 08. Gom nhóm và hàm tổng hợp

> [← Mục lục](README.md) · [← Chương 07: JOIN: kết hợp nhiều bảng](07-join.md) · [Chương 09: Subquery, CTE, UNION →](09-subquery-cte-union.md)

**Bạn sẽ học được:**

- Hàm tổng hợp (*aggregate function*) là gì; dùng đúng `COUNT(*)`, `COUNT(col)`,
  `COUNT(DISTINCT ...)`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP_CONCAT`, và mỗi hàm đối xử với NULL ra sao.
- Chia dữ liệu thành nhóm bằng `GROUP BY` theo một cột, nhiều cột hoặc một biểu thức.
- Phân biệt `WHERE` (lọc dòng) với `HAVING` (lọc nhóm) dựa trên thứ tự thực thi logic của câu `SELECT`.
- Hiểu chế độ `ONLY_FULL_GROUP_BY`, khái niệm phụ thuộc hàm, `ANY_VALUE()`, và vì sao không nên tắt
  chế độ này.
- Thêm dòng tổng phụ, tổng cộng bằng `WITH ROLLUP` và `GROUPING()`; xoay dữ liệu thành cột bằng
  aggregate có điều kiện.
- Viết các báo cáo hay gặp (doanh thu theo ngày, theo tháng, top khách hàng) và tránh ba cái bẫy
  lớn: NULL, nhân dòng (*fan-out*) khi join, chia cho 0.

**Cần biết trước:** [Chương 05](05-select-co-ban.md) (SELECT, WHERE, ORDER BY, LIMIT, thứ tự thực
thi logic), [Chương 06](06-ham-bieu-thuc-null.md) (NULL, `CASE`, `COALESCE`, `NULLIF`, hàm ngày
giờ), [Chương 07](07-join.md) (JOIN, đặc biệt LEFT JOIN).

Các ví dụ SQL chạy trên MySQL 8.4; chỗ nào là PostgreSQL sẽ ghi rõ. Nếu chưa có MySQL, chạy bằng
Docker (trên máy của bạn, ở terminal bất kỳ):

```bash
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi vài giây cho server khởi động xong, rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Tuỳ chọn `--default-character-set=utf8mb4` để client gửi và hiển thị tiếng Việt đúng.

---

## 1. Gom nhóm để làm gì, và dữ liệu mẫu của chương

### 1.1 Từ "liệt kê dòng" tới "trả lời câu hỏi tổng hợp"

Ở các chương trước, câu `SELECT` trả về từng dòng: danh sách đơn hàng, danh sách khách kèm đơn của
họ. Nhưng phần lớn câu hỏi của người làm kinh doanh không phải "cho tôi xem các dòng", mà là "cho tôi
một con số":

- Tháng này có bao nhiêu đơn? Doanh thu bao nhiêu?
- Mỗi khách đã mua bao nhiêu tiền? Ai mua nhiều nhất?
- Sản phẩm nào bán chạy? Mỗi danh mục đóng góp bao nhiêu phần trăm doanh thu?

Để trả lời, SQL có hai công cụ đi cùng nhau:

- *Aggregate function* (hàm tổng hợp, hay hàm gộp): nhận vào nhiều giá trị, lấy từ nhiều dòng, và trả
  về một giá trị duy nhất. Ví dụ `COUNT` đếm, `SUM` cộng, `AVG` tính trung bình.
- `GROUP BY` (gom nhóm): chia các dòng thành từng nhóm theo giá trị của một hay nhiều cột. Hàm tổng
  hợp chạy riêng trên từng nhóm, và mỗi nhóm cho ra đúng một dòng kết quả.

Cách nghĩ dễ nhớ nhất là ba bước *split, apply, combine* (chia, tính, ghép). Bạn làm việc này bằng PHP
nhiều lần rồi, chỉ là chưa gọi tên nó:

```php
<?php
declare(strict_types=1);

// Giả sử đã kéo hết đơn 'paid' từ DB về PHP, mỗi phần tử là một dòng.
// Tiền tính bằng nghìn đồng, để kiểu int cho gọn.
$orders = [
    ['id' => 101, 'customer_id' => 1, 'total' => 300],
    ['id' => 102, 'customer_id' => 1, 'total' => 150],
    ['id' => 103, 'customer_id' => 2, 'total' => 500],
    ['id' => 105, 'customer_id' => 3, 'total' => 250],
    ['id' => 107, 'customer_id' => 4, 'total' => 400],
    ['id' => 108, 'customer_id' => 1, 'total' => 120],
];

// Bước 1 (split): chia từng dòng vào "ngăn" của customer_id tương ứng.
$groups = [];
foreach ($orders as $row) {
    $groups[$row['customer_id']][] = $row;
}

// Bước 2 (apply) và 3 (combine): mỗi ngăn thu gọn thành MỘT dòng kết quả.
foreach ($groups as $customerId => $rows) {
    $count   = count($rows);
    $revenue = array_sum(array_column($rows, 'total'));
    echo "{$customerId} | {$count} | {$revenue}\n";
}
// in ra:
// 1 | 3 | 570
// 2 | 1 | 500
// 3 | 1 | 250
// 4 | 1 | 400
```

Cùng việc đó bằng SQL chỉ là một câu, chạy ngay trong database:

```sql
SELECT customer_id, COUNT(*) AS so_don, SUM(total) AS doanh_thu
FROM orders
WHERE status = 'paid'
GROUP BY customer_id;
```

Hình dung những gì xảy ra bên trong:

```
Các dòng sau WHERE            Chia nhóm theo customer_id        Mỗi nhóm thu gọn thành 1 dòng
(đơn đã thanh toán)

 id   customer_id total        customer_id = 1                  customer_id so_don doanh_thu
 101  1           300    ──►    101  300                    ──►  1           3        570
 102  1           150           102  150
 103  2           500           108  120
 105  3           250          customer_id = 2              ──►  2           1        500
 107  4           400           103  500
 108  1           120          customer_id = 3              ──►  3           1        250
                                105  250
                               customer_id = 4              ──►  4           1        400
                                107  400
```

Vì sao nên để database làm thay vì kéo dữ liệu về PHP rồi tự cộng:

- Chỉ vài dòng kết quả đi qua mạng, thay vì toàn bộ dòng gốc. Với bảng triệu dòng, khác biệt có thể
  là vài KB so với hàng trăm MB.
- PHP không phải giữ hết dữ liệu trong bộ nhớ (mỗi request PHP bị giới hạn bởi `memory_limit`).
- Database có thể dùng index để đọc dữ liệu theo thứ tự nhóm, hoặc chỉ đọc index mà không đọc bảng
  (mục 10).

⚠️ Với người dùng Laravel: `Order::all()->groupBy('customer_id')` và
`DB::table('orders')->groupBy('customer_id')` trùng tên nhưng khác hẳn nhau. Cái đầu kéo toàn bộ bảng
về PHP rồi chia nhóm trong một `Collection`; cái sau sinh câu SQL `GROUP BY` chạy trong database. Mục
11 nói kỹ hơn.

### 1.2 Dữ liệu mẫu

Cả chương dùng một cửa hàng nhỏ: khách hàng, sản phẩm, đơn hàng, chi tiết đơn và đánh giá. Dữ liệu cố
ý nhỏ để bạn tự tính tay mọi kết quả và đối chiếu. Tiền tính bằng nghìn đồng. Chạy toàn bộ khối
dưới đây trong client `mysql`:

```sql
CREATE DATABASE IF NOT EXISTS ch08 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE ch08;

DROP TABLE IF EXISTS reviews, order_items, orders, products, customers;

CREATE TABLE customers (
  id   INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  city VARCHAR(50) NULL                  -- Dũng không khai báo thành phố
);

CREATE TABLE products (
  id       INT PRIMARY KEY,
  name     VARCHAR(50) NOT NULL,
  category VARCHAR(30) NOT NULL,
  price    DECIMAL(10,2) NOT NULL
);

CREATE TABLE orders (
  id          INT PRIMARY KEY,
  customer_id INT NOT NULL,
  status      VARCHAR(10) NOT NULL,      -- 'paid' | 'pending' | 'cancelled'
  total       DECIMAL(10,2) NOT NULL,    -- tổng tiền hàng của đơn
  discount    DECIMAL(10,2) NULL,        -- NULL nghĩa là đơn không dùng voucher
  created_at  DATETIME NOT NULL,         -- lưu theo giờ UTC
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE TABLE order_items (
  order_id   INT NOT NULL,
  product_id INT NOT NULL,
  qty        INT NOT NULL,
  unit_price DECIMAL(10,2) NOT NULL,
  PRIMARY KEY (order_id, product_id),
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE reviews (
  id          INT PRIMARY KEY,
  customer_id INT NOT NULL,
  product_id  INT NOT NULL,
  stars       TINYINT NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO customers VALUES
  (1, 'An',   'Hà Nội'),
  (2, 'Bình', 'Hà Nội'),
  (3, 'Chi',  'Đà Nẵng'),
  (4, 'Dũng', NULL),
  (5, 'Em',   'TP.HCM');                 -- Em chưa có đơn nào

INSERT INTO products VALUES
  (1, 'Bút bi',       'Văn phòng phẩm',  10.00),
  (2, 'Sổ tay',       'Văn phòng phẩm',  50.00),
  (3, 'Tai nghe',     'Điện tử',        200.00),
  (4, 'Sạc dự phòng', 'Điện tử',        150.00),
  (5, 'Sách SQL',     'Sách',           120.00);

INSERT INTO orders VALUES
  (101, 1, 'paid',      300.00, 20.00, '2026-01-05 09:15:00'),
  (102, 1, 'paid',      150.00, NULL,  '2026-01-05 14:00:00'),
  (103, 2, 'paid',      500.00, 50.00, '2026-01-31 20:30:00'),
  (104, 2, 'cancelled', 200.00, NULL,  '2026-02-02 10:00:00'),
  (105, 3, 'paid',      250.00, NULL,  '2026-02-02 11:45:00'),
  (106, 3, 'pending',    80.00, 10.00, '2026-02-14 08:00:00'),
  (107, 4, 'paid',      400.00, NULL,  '2026-02-14 09:30:00'),
  (108, 1, 'paid',      120.00, NULL,  '2026-03-01 07:00:00');

INSERT INTO order_items VALUES
  (101, 3, 1, 200.00), (101, 2, 2, 50.00),
  (102, 4, 1, 150.00),
  (103, 3, 2, 200.00), (103, 1, 10, 10.00),
  (104, 3, 1, 200.00),
  (105, 5, 1, 120.00), (105, 1, 3, 10.00), (105, 2, 2, 50.00),
  (106, 1, 8, 10.00),
  (107, 4, 2, 150.00), (107, 1, 10, 10.00),
  (108, 5, 1, 120.00);

INSERT INTO reviews VALUES
  (1, 1, 3, 5),
  (2, 1, 4, 4),
  (3, 3, 5, 5);
```

Bảng `orders` là nhân vật chính, nên đây là nó dưới dạng bảng để bạn tra khi tự tính:

| id | customer_id | status | total | discount | created_at (UTC) |
|---|---|---|---|---|---|
| 101 | 1 (An) | paid | 300.00 | 20.00 | 2026-01-05 09:15:00 |
| 102 | 1 (An) | paid | 150.00 | NULL | 2026-01-05 14:00:00 |
| 103 | 2 (Bình) | paid | 500.00 | 50.00 | 2026-01-31 20:30:00 |
| 104 | 2 (Bình) | cancelled | 200.00 | NULL | 2026-02-02 10:00:00 |
| 105 | 3 (Chi) | paid | 250.00 | NULL | 2026-02-02 11:45:00 |
| 106 | 3 (Chi) | pending | 80.00 | 10.00 | 2026-02-14 08:00:00 |
| 107 | 4 (Dũng) | paid | 400.00 | NULL | 2026-02-14 09:30:00 |
| 108 | 1 (An) | paid | 120.00 | NULL | 2026-03-01 07:00:00 |

Vài điều được cài sẵn để làm ví dụ cho các mục sau:

- Tổng tiền các dòng `order_items` của mỗi đơn đúng bằng `orders.total` (ví dụ đơn 101: 1 × 200 +
  2 × 50 = 300). Nhờ vậy ta thấy rõ con số bị phóng đại khi join sai (mục 9.2).
- `discount` có NULL, `city` của Dũng là NULL: dùng để xem aggregate xử lý NULL ra sao.
- Em không có đơn nào: dùng để xem LEFT JOIN kết hợp với `COUNT`.
- Đơn 103 tạo lúc 20:30 ngày 31/01 giờ UTC, tức 03:30 ngày 01/02 giờ Việt Nam: dùng cho bài báo cáo
  theo múi giờ (mục 8.4).

---

## 2. Các hàm tổng hợp

### 2.1 Hàm tổng hợp là gì

Một hàm hay biểu thức thường như `UPPER(name)` hay `total * 2` làm việc trên từng dòng: một dòng vào,
một giá trị ra, nên câu `SELECT` có bao nhiêu dòng thì kết quả có bấy nhiêu dòng. Hàm tổng hợp khác ở chỗ nó "nuốt"
cả một tập dòng và nhả ra một giá trị duy nhất.

Khi câu lệnh có hàm tổng hợp mà không có `GROUP BY`, toàn bộ các dòng (còn lại sau `WHERE`) được coi
là một nhóm duy nhất. Tài liệu MySQL viết: dùng hàm tổng hợp trong câu không có `GROUP BY` thì tương
đương với gom tất cả các dòng thành một nhóm. Hệ quả: kết quả luôn có đúng một dòng.

```sql
SELECT COUNT(*)   AS so_don,
       SUM(total) AS tong_tien,
       MIN(total) AS nho_nhat,
       MAX(total) AS lon_nhat
FROM orders;
```

```
+--------+-----------+----------+----------+
| so_don | tong_tien | nho_nhat | lon_nhat |
+--------+-----------+----------+----------+
|      8 |   2000.00 |    80.00 |   500.00 |
+--------+-----------+----------+----------+
```

Thêm `WHERE` thì hàm tổng hợp chỉ thấy những dòng lọt qua `WHERE`:

```sql
SELECT COUNT(*) AS so_don, SUM(total) AS doanh_thu
FROM orders
WHERE status = 'paid';
-- so_don = 6, doanh_thu = 1720.00   (300 + 150 + 500 + 250 + 400 + 120)
```

Quy tắc chung cần thuộc lòng trước khi đi vào từng hàm: trừ khi có ghi chú riêng, hàm tổng hợp bỏ
qua giá trị NULL. Ngoại lệ đáng nhớ nhất là `COUNT(*)`.

### 2.2 COUNT: ba dạng, ba ý nghĩa

| Cách viết | Đếm cái gì |
|---|---|
| `COUNT(*)` | Số dòng, bất kể dòng đó có NULL hay không |
| `COUNT(expr)` | Số dòng mà `expr` khác NULL |
| `COUNT(DISTINCT expr)` | Số giá trị khác nhau của `expr`, không tính NULL |

Thử trên bảng `customers` (Dũng có `city` là NULL):

```sql
SELECT COUNT(*)             AS so_khach,       -- 5
       COUNT(city)          AS co_thanh_pho,   -- 4: dòng của Dũng không được đếm
       COUNT(DISTINCT city) AS so_thanh_pho    -- 3: Hà Nội, Đà Nẵng, TP.HCM
FROM customers;
```

Và trên `orders`:

```sql
SELECT COUNT(*)                            AS so_don,         -- 8
       COUNT(discount)                     AS don_co_voucher, -- 3 (đơn 101, 103, 106)
       COUNT(DISTINCT customer_id)         AS so_khach_dat,   -- 4 (Em chưa đặt đơn nào)
       COUNT(DISTINCT customer_id, status) AS so_cap          -- 6
FROM orders;
```

Cột cuối dùng một mở rộng của MySQL: `COUNT(DISTINCT a, b)` đếm số tổ hợp `(a, b)` khác nhau mà không
chứa NULL. Ở đây có 6 cặp: (1, paid), (2, paid), (2, cancelled), (3, paid), (3, pending), (4, paid).
Chuẩn SQL không có cú pháp nhiều đối số này và PostgreSQL báo lỗi với nó. Cách viết chạy được ở mọi
database là đếm trên một subquery `SELECT DISTINCT` ([chương 09](09-subquery-cte-union.md)).

Vài điều nên biết thêm:

- `COUNT` trả về kiểu `BIGINT` và không bao giờ trả NULL: không có dòng nào thì ra `0`.
- `COUNT(1)` và `COUNT(*)` là một. Tài liệu MySQL nói rõ InnoDB xử lý `SELECT COUNT(*)` và
  `SELECT COUNT(1)` theo cùng một cách, không có khác biệt hiệu năng. Hãy viết `COUNT(*)` vì nó nói
  đúng ý "đếm dòng".
- `COUNT(col)` không phải "phiên bản nhanh hơn" của `COUNT(*)`: nó mang nghĩa khác (bỏ qua NULL). Chỉ
  dùng khi bạn thật sự muốn bỏ qua NULL, ví dụ `COUNT(o.id)` sau LEFT JOIN (mục 9.1).
- InnoDB không lưu sẵn số dòng của bảng, vì các transaction chạy đồng thời có thể "thấy" số dòng khác
  nhau. Nên `SELECT COUNT(*) FROM bang_lon` phải đếm thật và có thể chậm. Cách xử lý để ở
  [chương 12](12-explain-toi-uu-query.md).

⚠️ `COUNT(status = 'paid')` không đếm số đơn đã thanh toán. Phép so sánh trả về 1 hoặc 0, cả hai đều
khác NULL, nên kết quả là 8 (mọi dòng). Cách đếm có điều kiện đúng ở mục 7.

### 2.3 SUM và AVG

`SUM(expr)` cộng các giá trị khác NULL. `AVG(expr)` là trung bình cộng của các giá trị khác NULL,
tức là tổng chia cho số giá trị khác NULL, không phải chia cho số dòng.

```sql
SELECT SUM(total)                 AS tong,           -- 2000.00
       AVG(total)                 AS tb_moi_don,     -- 250.000000
       SUM(discount)              AS tong_giam,      -- 80.00
       AVG(discount)              AS tb_giam,        -- 26.666667  = 80 / 3
       AVG(COALESCE(discount, 0)) AS tb_giam_moi_don -- 10.000000  = 80 / 8
FROM orders;
```

Hai cột cuối khác nhau vì trả lời hai câu hỏi khác nhau:

- `AVG(discount)`: "những đơn có dùng voucher thì trung bình được giảm bao nhiêu?" Chỉ 3 đơn có
  `discount` khác NULL nên chia cho 3.
- `AVG(COALESCE(discount, 0))`: "trung bình mỗi đơn được giảm bao nhiêu?" Đơn không có voucher được
  tính là giảm 0, nên chia cho 8.

Không có cột nào "đúng" sẵn; bạn phải biết mình đang hỏi câu nào. Lỗi thường gặp là muốn hỏi câu thứ
hai nhưng viết câu thứ nhất, và con số bị thổi phồng lên gần ba lần mà không ai để ý.

Kiểu dữ liệu của kết quả:

- Với đối số là số chính xác (số nguyên hoặc `DECIMAL`), `SUM` và `AVG` trả về `DECIMAL`; với đối số
  `FLOAT`/`DOUBLE` thì trả về `DOUBLE`. Vì vậy tiền nên lưu bằng `DECIMAL` (xem
  [chương 03](03-kieu-du-lieu.md)): cộng một triệu giá trị `DECIMAL` vẫn ra kết quả chính xác, còn cộng
  `DOUBLE` có thể lệch ở các chữ số cuối.
- `SUM` giữ nguyên số chữ số thập phân của cột (`2000.00`). `AVG` thêm số chữ số thập phân bằng biến
  hệ thống `div_precision_increment` (mặc định 4), giống phép chia `/`. Do đó `AVG` trên cột
  `DECIMAL(10,2)` cho 6 chữ số thập phân, trên cột số nguyên cho 4 chữ số:

```sql
SELECT AVG(stars) FROM reviews;   -- 4.6667  (= 14 / 3)
```

Muốn hiển thị gọn thì làm tròn ở bước cuối: `ROUND(AVG(stars), 1)` cho `4.7`. Đừng làm tròn từng dòng
rồi mới cộng, sai số sẽ cộng dồn.

Thêm vài chi tiết:

- `SUM(DISTINCT expr)` và `AVG(DISTINCT expr)` chỉ cộng các giá trị khác nhau. Với tiền thì gần như
  luôn sai: hai đơn khác nhau cùng giá 150 sẽ chỉ được cộng một lần.
- `SUM` và `AVG` không làm việc đúng với giá trị ngày giờ: MySQL đổi giá trị sang số và mất mọi thứ
  sau ký tự không phải số đầu tiên. Muốn cộng thời lượng, đổi sang đơn vị số trước, ví dụ
  `SEC_TO_TIME(SUM(TIME_TO_SEC(duration)))`.

### 2.4 MIN và MAX

`MIN` và `MAX` trả về giá trị nhỏ nhất, lớn nhất, bỏ qua NULL. Chúng dùng được với số, chuỗi và ngày
giờ:

```sql
SELECT MIN(total), MAX(total), MIN(created_at), MAX(created_at)
FROM orders;
-- 80.00 | 500.00 | 2026-01-05 09:15:00 | 2026-03-01 07:00:00

SELECT MIN(name), MAX(name) FROM customers;
-- An | Em
```

Với chuỗi, "nhỏ" và "lớn" được so theo *collation* của cột, giống `ORDER BY`. Trong collation không
phân biệt hoa thường như `utf8mb4_0900_ai_ci`, `'an'` và `'An'` bằng nhau.

⚠️ Với cột `ENUM` và `SET`, `MIN`/`MAX` so sánh theo chuỗi, còn `ORDER BY` so theo vị trí khai báo.
Tài liệu MySQL ghi rõ hai cách này khác nhau. Ví dụ cột `size ENUM('small', 'medium', 'large')` chứa
đủ ba giá trị: `ORDER BY size DESC` đưa `'large'` lên đầu (vị trí 3), nhưng `MAX(size)` trả về
`'small'` (theo bảng chữ cái, `s` đứng sau `m` và `l`).

⚠️ `MAX(created_at)` cho bạn thời điểm của đơn mới nhất, nhưng không cho bạn các cột khác của đơn đó.
Viết `SELECT customer_id, id, MAX(created_at) ... GROUP BY customer_id` với hy vọng `id` là id của đơn
mới nhất là một lỗi kinh điển; mục 5.6 giải thích vì sao và cách làm đúng.

### 2.5 GROUP_CONCAT: nối các giá trị thành một chuỗi

`GROUP_CONCAT` nối các giá trị khác NULL trong nhóm thành một chuỗi. Cú pháp đầy đủ:

```sql
GROUP_CONCAT([DISTINCT] expr [, expr ...]
             [ORDER BY {unsigned_integer | col_name | expr} [ASC | DESC] [, col_name ...]]
             [SEPARATOR str_val])
```

- Dấu phân cách mặc định là dấu phẩy `,` (không có khoảng trắng).
- `ORDER BY` bên trong quyết định thứ tự các phần tử trong chuỗi. Không ghi thì thứ tự không được đảm
  bảo.
- `DISTINCT` bỏ phần tử trùng.
- Không có giá trị nào khác NULL thì kết quả là NULL.

Ví dụ: danh sách đơn của từng khách.

```sql
SELECT customer_id,
       GROUP_CONCAT(id ORDER BY id SEPARATOR ', ') AS cac_don
FROM orders
GROUP BY customer_id
ORDER BY customer_id;
```

```
+-------------+---------------+
| customer_id | cac_don       |
+-------------+---------------+
|           1 | 101, 102, 108 |
|           2 | 103, 104      |
|           3 | 105, 106      |
|           4 | 107           |
+-------------+---------------+
```

Ví dụ: tên các sản phẩm trong đơn 105, theo thứ tự id sản phẩm.

```sql
SELECT GROUP_CONCAT(p.name ORDER BY p.id SEPARATOR ' + ') AS san_pham
FROM order_items i
JOIN products p ON p.id = i.product_id
WHERE i.order_id = 105;
-- Bút bi + Sổ tay + Sách SQL
```

⚠️ Kết quả bị cắt ngắn ở `group_concat_max_len` byte, mặc định 1024. Lưu ý đơn vị là byte, không phải
ký tự: chữ tiếng Việt có dấu trong `utf8mb4` chiếm 2 hoặc 3 byte, nên 1024 byte chứa ít hơn 1024 chữ.
Khi bị cắt, MySQL không báo lỗi mà chỉ sinh một warning:

```sql
SHOW WARNINGS;
-- Warning | 1260 | Row 3 was cut by GROUP_CONCAT()     (output minh hoạ)
```

Code ứng dụng hầu như không đọc warning, nên chuỗi cụt đi thẳng vào báo cáo hoặc vào một câu `IN (...)`
khác. Nếu thật sự cần chuỗi dài, tăng biến này cho session trước khi chạy:

```sql
SET SESSION group_concat_max_len = 1000000;
```

Độ dài thực tế còn bị chặn bởi `max_allowed_packet` (mặc định 64MB). Kiểu trả về là `TEXT` (hoặc
`BLOB`), trừ khi `group_concat_max_len` nhỏ hơn hoặc bằng 512 thì là `VARCHAR` (hoặc `VARBINARY`).

Khi nào dùng `GROUP_CONCAT`: hiển thị danh sách ngắn trong báo cáo, gỡ lỗi, xuất file. Khi ứng dụng
cần đọc lại từng phần tử, cân nhắc `JSON_ARRAYAGG(expr)`: nó trả về mảng JSON, không phải lo phần tử
chứa dấu phẩy. Nhược điểm là tài liệu MySQL nói thứ tự phần tử trong mảng không xác định.

PostgreSQL không có `GROUP_CONCAT`. Hàm tương đương là `string_agg(expr, ', ' ORDER BY ...)`, ngoài
ra có `array_agg` và `json_agg`. PostgreSQL không có biến giới hạn độ dài kiểu `group_concat_max_len`.

### 2.6 Khi không có dòng nào

Đây là chỗ nhiều người bất ngờ. Không có `GROUP BY` thì kết quả luôn có một dòng, kể cả khi không dòng
nào thoả `WHERE`. Khi đó `COUNT` ra 0, còn mọi hàm khác ra NULL:

```sql
SELECT COUNT(*), COUNT(discount), SUM(total), AVG(total), MAX(total), GROUP_CONCAT(id)
FROM orders
WHERE status = 'refunded';     -- không có đơn nào như vậy
-- 0 | 0 | NULL | NULL | NULL | NULL
```

Tổng của "không có gì" là NULL, không phải 0. Đây là quy định của chuẩn SQL chứ không riêng MySQL;
tài liệu PostgreSQL cũng nhắc: trừ `count`, các hàm tổng hợp trả NULL khi không có dòng nào, và `sum`
của không dòng nào là NULL chứ không phải 0 như nhiều người tưởng. Trong báo cáo, người đọc chờ số 0,
và code PHP nhận `null` có thể hỏng ở phép tính sau. Hãy viết:

```sql
SELECT COALESCE(SUM(total), 0) AS doanh_thu
FROM orders
WHERE status = 'refunded';
-- 0.00
```

Có `GROUP BY` thì khác hẳn: không có dòng nào thì không có nhóm nào, kết quả là tập rỗng (mục 3.7).

### 2.7 Tổng kết các hàm tổng hợp

| Hàm | Tính gì | Gặp NULL | Không có dòng nào | Kiểu kết quả |
|---|---|---|---|---|
| `COUNT(*)` | Số dòng | Vẫn đếm | `0` | `BIGINT` |
| `COUNT(expr)` | Số giá trị khác NULL | Bỏ qua | `0` | `BIGINT` |
| `COUNT(DISTINCT expr)` | Số giá trị khác nhau | Bỏ qua | `0` | `BIGINT` |
| `SUM(expr)` | Tổng | Bỏ qua | NULL | `DECIMAL` (đối số chính xác) hoặc `DOUBLE` |
| `AVG(expr)` | Tổng chia số giá trị khác NULL | Bỏ qua | NULL | Như `SUM`, thêm chữ số thập phân |
| `MIN(expr)`, `MAX(expr)` | Nhỏ nhất, lớn nhất | Bỏ qua | NULL | Như kiểu của đối số |
| `GROUP_CONCAT(expr)` | Chuỗi nối | Bỏ qua | NULL | `TEXT`/`VARCHAR` (hoặc bản binary) |

MySQL 8.4 còn có `JSON_ARRAYAGG`, `JSON_OBJECTAGG`, nhóm thống kê `STD`/`STDDEV`/`STDDEV_POP`/
`STDDEV_SAMP`/`VARIANCE`/`VAR_POP`/`VAR_SAMP`, và nhóm bit `BIT_AND`/`BIT_OR`/`BIT_XOR`. Danh sách hàm
tổng hợp của MySQL 8.4 không có hàm trung vị (*median*) hay *percentile*; muốn tính phải tự viết,
thường bằng window function ([chương 10](10-window-function.md)). PostgreSQL có sẵn `percentile_cont`,
`percentile_disc`, `mode`, cùng `bool_and`/`bool_or`.

---

## 3. GROUP BY: chia dòng thành nhóm

### 3.1 Cú pháp và cách đọc

```sql
SELECT cot_gom_nhom, ..., ham_tong_hop(...), ...
FROM bang
WHERE dieu_kien_tren_tung_dong
GROUP BY cot_gom_nhom, ...
```

Đọc câu này theo thứ tự database xử lý: lấy các dòng từ `FROM`, bỏ những dòng không thoả `WHERE`, chia
các dòng còn lại thành nhóm sao cho mọi dòng trong cùng nhóm có cùng giá trị ở các cột `GROUP BY`, rồi
với mỗi nhóm tính các hàm tổng hợp và trả về đúng một dòng.

Vì mỗi nhóm chỉ còn một dòng, mỗi thứ bạn đưa vào `SELECT` phải có đúng một giá trị cho cả nhóm. Có hai
loại thứ như vậy: cột nằm trong `GROUP BY` (cả nhóm cùng giá trị, theo định nghĩa) và hàm tổng hợp (thu
cả nhóm về một giá trị). Một cột "trần" khác thì mỗi dòng trong nhóm có thể mang một giá trị khác nhau,
và database không biết phải chọn giá trị nào. Mục 5 bàn kỹ quy tắc này.

### 3.2 Gom theo một cột

Đếm số đơn và tổng tiền theo trạng thái:

```sql
SELECT status, COUNT(*) AS so_don, SUM(total) AS tong_tien
FROM orders
GROUP BY status
ORDER BY status;
```

```
+-----------+--------+-----------+
| status    | so_don | tong_tien |
+-----------+--------+-----------+
| cancelled |      1 |    200.00 |
| paid      |      6 |   1720.00 |
| pending   |      1 |     80.00 |
+-----------+--------+-----------+
```

Có ba giá trị `status` khác nhau nên có ba nhóm, ba dòng. Cộng cột `so_don` lại được 8, đúng bằng số
dòng của bảng: mỗi dòng thuộc đúng một nhóm.

### 3.3 Gom theo nhiều cột

Ghi nhiều cột trong `GROUP BY` thì mỗi nhóm là một tổ hợp giá trị khác nhau của các cột đó:

```sql
SELECT customer_id, status, COUNT(*) AS so_don, SUM(total) AS tong_tien
FROM orders
GROUP BY customer_id, status
ORDER BY customer_id, status;
```

```
+-------------+-----------+--------+-----------+
| customer_id | status    | so_don | tong_tien |
+-------------+-----------+--------+-----------+
|           1 | paid      |      3 |    570.00 |
|           2 | cancelled |      1 |    200.00 |
|           2 | paid      |      1 |    500.00 |
|           3 | paid      |      1 |    250.00 |
|           3 | pending   |      1 |     80.00 |
|           4 | paid      |      1 |    400.00 |
+-------------+-----------+--------+-----------+
```

Sáu nhóm, khớp với `COUNT(DISTINCT customer_id, status) = 6` ở mục 2.2. Khách 2 xuất hiện ở hai dòng vì
có hai trạng thái khác nhau.

Thứ tự các cột trong `GROUP BY` không làm thay đổi tập nhóm: `GROUP BY status, customer_id` cho ra đúng
sáu nhóm như trên. Thứ tự hiển thị là việc của `ORDER BY`. Thứ tự cột trong `GROUP BY` chỉ đổi kết quả
khi dùng `WITH ROLLUP` (mục 6).

### 3.4 Gom theo biểu thức

Bạn không bị giới hạn ở cột có sẵn; có thể gom theo bất kỳ biểu thức nào tính từ cột. Đếm đơn theo
tháng:

```sql
SELECT DATE_FORMAT(created_at, '%Y-%m') AS thang, COUNT(*) AS so_don
FROM orders
GROUP BY DATE_FORMAT(created_at, '%Y-%m')
ORDER BY thang;
```

```
+---------+--------+
| thang   | so_don |
+---------+--------+
| 2026-01 |      3 |
| 2026-02 |      4 |
| 2026-03 |      1 |
+---------+--------+
```

Phân loại đơn theo khoảng giá bằng `CASE` (xem [chương 06](06-ham-bieu-thuc-null.md)):

```sql
SELECT CASE
         WHEN total < 200 THEN 'Nhỏ (dưới 200)'
         WHEN total < 400 THEN 'Vừa (200 đến dưới 400)'
         ELSE 'Lớn (từ 400)'
       END AS nhom_gia,
       COUNT(*) AS so_don
FROM orders
GROUP BY nhom_gia
ORDER BY MIN(total);
```

```
+--------------------------+--------+
| nhom_gia                 | so_don |
+--------------------------+--------+
| Nhỏ (dưới 200)           |      3 |
| Vừa (200 đến dưới 400)   |      3 |
| Lớn (từ 400)             |      2 |
+--------------------------+--------+
```

Nhóm nhỏ gồm 150, 80, 120; nhóm vừa gồm 300, 200, 250; nhóm lớn gồm 500, 400. `ORDER BY MIN(total)` sắp
các nhóm theo giá trị nhỏ nhất của từng nhóm, một mẹo để có thứ tự tự nhiên thay vì thứ tự chữ cái.

Ở câu này `GROUP BY nhom_gia` dùng alias đặt trong `SELECT`. Đây là một mở rộng của MySQL; PostgreSQL
cũng cho phép dùng tên cột output trong `GROUP BY`. Chuẩn SQL thì không, ở đó bạn phải chép lại nguyên
biểu thức `CASE`. Ngoài ra MySQL còn cho viết vị trí cột, `GROUP BY 1`, nhưng tài liệu MySQL ghi rõ dùng
vị trí cột là cách viết đã lỗi thời (*deprecated*) vì chuẩn SQL đã bỏ nó. Hãy viết tên hoặc biểu thức.

### 3.5 NULL tạo thành một nhóm

Ở [chương 06](06-ham-bieu-thuc-null.md) bạn đã biết `NULL = NULL` không phải TRUE. Nhưng khi gom nhóm,
SQL coi mọi NULL là "giống nhau" và gom chúng vào chung một nhóm, giống cách `DISTINCT` xử lý NULL:

```sql
SELECT city, COUNT(*) AS so_khach
FROM customers
GROUP BY city
ORDER BY so_khach DESC, city;
```

```
+----------+----------+
| city     | so_khach |
+----------+----------+
| Hà Nội   |        2 |
| NULL     |        1 |
| Đà Nẵng  |        1 |
| TP.HCM   |        1 |
+----------+----------+
```

Dòng NULL là nhóm của những khách không khai báo thành phố (ở đây chỉ có Dũng). Nếu nhiều khách cùng
có `city` NULL, họ vẫn chỉ tạo ra một nhóm. Muốn hiển thị dễ đọc, đặt nhãn bằng `COALESCE`:

```sql
SELECT COALESCE(city, '(chưa rõ)') AS thanh_pho, COUNT(*) AS so_khach
FROM customers
GROUP BY city
ORDER BY so_khach DESC, city;
-- Hà Nội 2, (chưa rõ) 1, Đà Nẵng 1, TP.HCM 1
```

### 3.6 Collation quyết định thế nào là "giống nhau"

Với cột chuỗi, hai giá trị thuộc cùng nhóm khi chúng bằng nhau theo collation của cột. Collation mặc
định của MySQL 8.4 là `utf8mb4_0900_ai_ci`: *ai* là *accent-insensitive* (không phân biệt dấu), *ci*
là *case-insensitive* (không phân biệt hoa thường). Với dữ liệu tiếng Việt, điều này nghĩa là "Hà
Nội", "ha noi" và "HÀ NỘI" rơi vào cùng một nhóm:

```sql
CREATE TEMPORARY TABLE t_city (city VARCHAR(50))
  CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
INSERT INTO t_city VALUES ('Hà Nội'), ('ha noi'), ('HÀ NỘI'), ('Huế');

SELECT city, COUNT(*) AS n FROM t_city GROUP BY city ORDER BY n DESC;
-- 2 nhóm: một nhóm có n = 3 (cột city hiện MỘT trong ba cách viết), và 'Huế' có n = 1

SELECT city COLLATE utf8mb4_0900_as_cs AS city_cs, COUNT(*) AS n
FROM t_city
GROUP BY city_cs;
-- 4 nhóm, mỗi nhóm n = 1: so sánh phân biệt dấu (as) và hoa thường (cs)
```

Gom chung như vậy thường là điều bạn muốn (người dùng gõ thiếu dấu vẫn được tính cho Hà Nội). Nhưng
hãy biết hai hệ quả:

- Giá trị hiển thị cho nhóm là một trong các cách viết, đừng dựa vào việc nó là cách viết nào.
- Cùng câu query chạy trên cột có collation khác (`utf8mb4_bin`, hay cột ở PostgreSQL vốn mặc định
  phân biệt hoa thường) sẽ ra số nhóm khác. Charset và collation được giải thích ở
  [chương 03](03-kieu-du-lieu.md).

Cách bền vững là chuẩn hoá dữ liệu ngay khi ghi (ví dụ lưu `city_id` tham chiếu bảng thành phố thay vì
chuỗi người dùng gõ tự do), thay vì trông vào collation lúc đọc.

### 3.7 Không có dòng nào thì không có nhóm nào

Ở mục 2.6, câu không có `GROUP BY` luôn trả về một dòng. Thêm `GROUP BY` vào thì khác:

```sql
SELECT status, COUNT(*) FROM orders WHERE status = 'refunded' GROUP BY status;
-- Empty set: không có dòng nào nên không có nhóm nào, kết quả rỗng

SELECT COUNT(*) FROM orders WHERE status = 'refunded';
-- 1 dòng: 0
```

Trong code PHP, câu thứ nhất làm `$stmt->fetch()` trả về `false` chứ không phải một dòng có số 0. Nếu
bạn cần "mọi trạng thái, kể cả trạng thái không có đơn nào" thì phải lấy danh sách trạng thái từ một
nơi khác rồi LEFT JOIN, giống bài báo cáo theo ngày ở mục 8.3.

### 3.8 Thứ tự kết quả: GROUP BY không sắp xếp

Ở MySQL 5.7 trở về trước, `GROUP BY` ngầm sắp xếp kết quả theo các cột gom nhóm trong một số điều kiện,
và nhiều code cũ vô tình dựa vào điều đó. Từ MySQL 8.0, việc sắp xếp ngầm này không còn; tài liệu nói
rõ kết quả có thể khác các bản trước, và muốn có thứ tự nào thì phải viết `ORDER BY`. Bản 8.0.13 còn
bỏ hẳn cú pháp `GROUP BY cot ASC|DESC` từng được dùng để chọn chiều sắp xếp.

Quy tắc đơn giản: cần thứ tự thì viết `ORDER BY`. Điều này đúng với mọi database, PostgreSQL cũng vậy.
`ORDER BY` dùng được cả hàm tổng hợp, ví dụ `ORDER BY COUNT(*) DESC` hay `ORDER BY SUM(total) DESC`.

### 3.9 GROUP BY và DISTINCT

Khi không có hàm tổng hợp, `GROUP BY` cho cùng kết quả với `DISTINCT`:

```sql
SELECT DISTINCT customer_id, status FROM orders;
SELECT customer_id, status FROM orders GROUP BY customer_id, status;
-- cả hai đều ra 6 cặp (customer_id, status) không trùng
```

Dùng `DISTINCT` khi chỉ cần bỏ trùng, dùng `GROUP BY` khi cần tính gì đó cho mỗi nhóm. Viết đúng ý
giúp người đọc code hiểu nhanh hơn. Đừng viết `SELECT DISTINCT ... GROUP BY ...` cho cùng các cột: thừa.

---

## 4. Lọc dòng và lọc nhóm: WHERE và HAVING

### 4.1 Thứ tự thực thi logic

Bạn viết `SELECT` đầu tiên, nhưng database xử lý câu lệnh theo một thứ tự logic khác. Thứ tự này đã
gặp ở [chương 05](05-select-co-ban.md); với gom nhóm nó đầy đủ hơn:

```
1. FROM, JOIN, ON   lấy và ghép các dòng
2. WHERE            lọc TỪNG DÒNG               (chưa có nhóm, chưa có hàm tổng hợp)
3. GROUP BY         chia các dòng thành nhóm
4. (tính aggregate) mỗi nhóm có COUNT, SUM, ...
5. HAVING           lọc TỪNG NHÓM               (đã có giá trị hàm tổng hợp)
6. SELECT           tính biểu thức, đặt alias    (window function ở đây, chương 10)
7. DISTINCT         bỏ dòng trùng
8. ORDER BY         sắp xếp                      (dùng được alias và hàm tổng hợp)
9. LIMIT, OFFSET    cắt
```

Đây là thứ tự logic, dùng để suy luận câu lệnh có nghĩa gì và viết được không. Bộ tối ưu (*optimizer*)
được phép thực hiện khác về mặt vật lý, miễn kết quả giống hệt.

Từ thứ tự này suy ra ngay:

- `WHERE` không dùng được hàm tổng hợp: ở bước 2 chưa có nhóm nào để mà đếm hay cộng.
- `HAVING` dùng được hàm tổng hợp: ở bước 5 mọi nhóm đã có giá trị tổng hợp.
- `WHERE` loại dòng trước khi gom, nên nó thay đổi con số mà hàm tổng hợp tính ra. `HAVING` chỉ chọn
  hiển thị nhóm nào, không thay đổi con số của nhóm được giữ lại.

### 4.2 Ví dụ: khách có doanh thu trên 450

```sql
SELECT customer_id, SUM(total) AS doanh_thu
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total) > 450
ORDER BY doanh_thu DESC;
```

Đi từng bước:

| Bước | Dữ liệu |
|---|---|
| Sau `WHERE status = 'paid'` | 6 dòng: 101, 102, 103, 105, 107, 108 |
| Sau `GROUP BY customer_id` | 4 nhóm: khách 1 (101, 102, 108), khách 2 (103), khách 3 (105), khách 4 (107) |
| Tính `SUM(total)` | khách 1: 570, khách 2: 500, khách 3: 250, khách 4: 400 |
| Sau `HAVING SUM(total) > 450` | còn khách 1 và khách 2 |
| Sau `ORDER BY doanh_thu DESC` | khách 1 rồi khách 2 |

```
+-------------+-----------+
| customer_id | doanh_thu |
+-------------+-----------+
|           1 |    570.00 |
|           2 |    500.00 |
+-------------+-----------+
```

Thử chuyển điều kiện tổng hợp vào `WHERE` sẽ bị từ chối:

```sql
SELECT customer_id, SUM(total) FROM orders WHERE SUM(total) > 450 GROUP BY customer_id;
-- ERROR 1111 (HY000): Invalid use of group function
```

### 4.3 WHERE thay đổi con số, HAVING chỉ chọn nhóm

Hai câu dưới trông giống nhau nhưng trả lời hai câu hỏi khác nhau:

```sql
-- (a) "Tính trên các ĐƠN từ 300 trở lên": lọc dòng trước, rồi mới cộng
SELECT customer_id, COUNT(*) AS so_don, SUM(total) AS tong
FROM orders
WHERE status = 'paid' AND total >= 300
GROUP BY customer_id
ORDER BY customer_id;
-- 1 | 1 | 300.00     (đơn 102 giá 150 và 108 giá 120 bị loại trước khi cộng)
-- 2 | 1 | 500.00
-- 4 | 1 | 400.00

-- (b) "Những KHÁCH có tổng từ 300 trở lên": cộng hết, rồi mới chọn nhóm
SELECT customer_id, COUNT(*) AS so_don, SUM(total) AS tong
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING SUM(total) >= 300
ORDER BY customer_id;
-- 1 | 3 | 570.00
-- 2 | 1 | 500.00
-- 4 | 1 | 400.00
```

Cùng ba khách, nhưng con số của khách 1 khác nhau: 300 so với 570. Câu (a) đổi nội dung của nhóm, câu
(b) giữ nguyên nhóm và chỉ chọn nhóm nào được in ra. Khi viết báo cáo, hãy tự hỏi "điều kiện này nói về
một dòng hay về cả nhóm?" để biết đặt nó ở đâu.

### 4.4 Điều kiện trên dòng thì đặt ở WHERE

Một điều kiện chỉ nhắc tới cột gom nhóm, không có hàm tổng hợp, có thể đặt ở cả hai nơi và cho cùng
kết quả:

```sql
SELECT customer_id, SUM(total) FROM orders GROUP BY customer_id HAVING customer_id = 1;  -- được, nhưng đừng
SELECT customer_id, SUM(total) FROM orders WHERE customer_id = 1 GROUP BY customer_id;   -- nên viết thế này
```

Tài liệu MySQL khuyên thẳng: đừng dùng `HAVING` cho những điều kiện lẽ ra thuộc về `WHERE`, và mô tả
`HAVING` được áp dụng gần như cuối cùng, ngay trước khi gửi kết quả cho client, không qua tối ưu. Đặt ở
`WHERE` thì database loại dòng sớm, có thể dùng index để chỉ đọc dòng của khách 1, và gom ít dữ liệu
hơn. Quy tắc: `HAVING` chỉ dành cho điều kiện có hàm tổng hợp.

### 4.5 Alias trong HAVING: tiện ở MySQL, lỗi ở PostgreSQL

MySQL cho `HAVING` dùng alias đặt trong `SELECT`:

```sql
SELECT customer_id, SUM(total) AS doanh_thu
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
HAVING doanh_thu > 450;          -- chạy được trên MySQL
```

Theo thứ tự logic, alias được đặt ở bước 6, sau `HAVING`, nên chuẩn SQL không cho phép điều này. Tài
liệu MySQL gọi đây là một mở rộng. PostgreSQL thì nói rõ tên cột output dùng được trong `ORDER BY` và
`GROUP BY` nhưng không dùng được trong `WHERE` hay `HAVING`; câu trên chạy trên PostgreSQL sẽ báo lỗi
không tìm thấy cột `doanh_thu`. Nếu code có khả năng chạy trên nhiều database (hoặc bạn đang học để đi
phỏng vấn), hãy viết lại biểu thức: `HAVING SUM(total) > 450`.

⚠️ Khi alias trùng tên một cột thật, MySQL ưu tiên cột trong `GROUP BY` (theo chuẩn) và sinh warning.
Ví dụ tài liệu đưa ra: `SELECT COUNT(col1) AS col2 FROM t GROUP BY col2 HAVING col2 = 2;`. Đặt alias
khác tên cột để tránh nhầm.

### 4.6 HAVING không có GROUP BY, và hàm tổng hợp lồng nhau

`HAVING` có thể đứng một mình. Khi đó cả tập dòng là một nhóm, `HAVING` quyết định có trả về dòng tổng
hợp duy nhất đó hay không:

```sql
SELECT COUNT(*) AS so_don FROM orders HAVING COUNT(*) > 100;
-- Empty set (chỉ có 8 đơn)
```

Cách này ít gặp, nhưng giải thích được vì sao `HAVING` không phụ thuộc `GROUP BY`.

Không thể lồng hàm tổng hợp vào nhau trong cùng một tầng. Muốn biết "khách có nhiều đơn nhất có bao
nhiêu đơn", câu `SELECT MAX(COUNT(*)) FROM orders GROUP BY customer_id` báo `ERROR 1111 (HY000): Invalid
use of group function`. Lý do: `COUNT(*)` cho mỗi nhóm một giá trị, rồi `MAX` cần gom các giá trị đó
lần nữa, tức là cần thêm một tầng gom nhóm. Có hai cách:

```sql
-- Cách 1: gom một tầng, sắp xếp rồi lấy dòng đầu
SELECT customer_id, COUNT(*) AS so_don
FROM orders
GROUP BY customer_id
ORDER BY so_don DESC, customer_id
LIMIT 1;
-- 1 | 3

-- Cách 2: tầng trong gom theo khách, tầng ngoài lấy MAX (derived table, chương 09)
SELECT MAX(so_don) AS nhieu_nhat
FROM (SELECT customer_id, COUNT(*) AS so_don FROM orders GROUP BY customer_id) AS t;
-- 3
```

Cách 1 chỉ trả về một khách kể cả khi có nhiều khách cùng số đơn lớn nhất; cách 2 trả về con số, muốn
lấy mọi khách đạt con số đó thì so sánh lại với nó ([chương 09](09-subquery-cte-union.md)) hoặc dùng
`RANK()` ([chương 10](10-window-function.md)).

---

## 5. ONLY_FULL_GROUP_BY và phụ thuộc hàm

### 5.1 Một câu hỏi không có câu trả lời

Thử câu này:

```sql
SELECT customer_id, status, COUNT(*) AS so_don
FROM orders
GROUP BY customer_id;
```

Nhóm của khách 2 gồm đơn 103 (`paid`) và đơn 104 (`cancelled`). Mỗi nhóm chỉ ra một dòng, vậy cột
`status` của dòng đó nên là `paid` hay `cancelled`? Không có đáp án đúng, vì câu hỏi sai từ gốc. MySQL
8.4 từ chối chạy:

```
ERROR 1055 (42000): Expression #2 of SELECT list is not in GROUP BY clause and contains
nonaggregated column 'ch08.orders.status' which is not functionally dependent on columns in
GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

Thông báo dài nhưng đọc được: biểu thức thứ 2 của `SELECT` (cột `status`) không nằm trong `GROUP BY`,
không nằm trong hàm tổng hợp, và không *phụ thuộc hàm* vào các cột `GROUP BY`, nên không tương thích
với chế độ `only_full_group_by`.

### 5.2 Quy tắc của ONLY_FULL_GROUP_BY

`ONLY_FULL_GROUP_BY` là một trong các *SQL mode*, những công tắc điều chỉnh mức "khó tính" của MySQL.
Theo tài liệu, khi bật, MySQL từ chối câu lệnh mà danh sách `SELECT`, điều kiện `HAVING` hoặc danh
sách `ORDER BY` nhắc tới một cột không nằm trong hàm tổng hợp, và cột đó:

- không có tên trong `GROUP BY`, và
- không phụ thuộc hàm vào (không được xác định duy nhất bởi) các cột `GROUP BY`.

Chế độ này bật sẵn trong MySQL 8.4. SQL mode mặc định của 8.4 gồm sáu chế độ: `ONLY_FULL_GROUP_BY`,
`STRICT_TRANS_TABLES`, `NO_ZERO_IN_DATE`, `NO_ZERO_DATE`, `ERROR_FOR_DIVISION_BY_ZERO`,
`NO_ENGINE_SUBSTITUTION`. Kiểm tra trên server của bạn:

```sql
SELECT @@SESSION.sql_mode;
SELECT @@GLOBAL.sql_mode;
```

Quy tắc áp dụng cả khi không có `GROUP BY`. Câu có hàm tổng hợp mà không có `GROUP BY` là một nhóm duy
nhất, nên cột "trần" bên cạnh hàm tổng hợp cũng vô nghĩa:

```sql
SELECT name, COUNT(*) FROM customers;
-- ERROR 1140 (42000): In aggregated query without GROUP BY, expression #1 of SELECT list
-- contains nonaggregated column 'ch08.customers.name'; this is incompatible with
-- sql_mode=only_full_group_by
```

Năm khách mà chỉ một dòng kết quả, `name` là tên ai? Lại một câu hỏi không có câu trả lời.

### 5.3 Phụ thuộc hàm: khi MySQL tự chứng minh được

Cột B *phụ thuộc hàm* (*functionally dependent*) vào cột A nếu mỗi giá trị của A xác định duy nhất một
giá trị của B. Ví dụ `customers.id` là khoá chính, nên biết `id` là biết đúng một `name`, một `city`.
Khái niệm này đã xuất hiện khi chuẩn hoá dữ liệu ở [chương 02](02-mo-hinh-quan-he-thiet-ke.md).

Nếu B phụ thuộc hàm vào cột gom nhóm A, mọi dòng trong nhóm có cùng giá trị B, nên đưa B vào `SELECT`
là an toàn. MySQL tự phát hiện được phụ thuộc hàm trong các trường hợp sau (theo tài liệu "Detection of
Functional Dependence"):

Trường hợp 1: gom theo khoá chính hoặc cột `UNIQUE NOT NULL`, thì mọi cột khác của bảng đó đều hợp lệ.

```sql
SELECT c.id, c.name, c.city, COUNT(o.id) AS so_don
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id
ORDER BY c.id;
```

```
+----+------+----------+--------+
| id | name | city     | so_don |
+----+------+----------+--------+
|  1 | An   | Hà Nội   |      3 |
|  2 | Bình | Hà Nội   |      2 |
|  3 | Chi  | Đà Nẵng  |      2 |
|  4 | Dũng | NULL     |      1 |
|  5 | Em   | TP.HCM   |      0 |
+----+------+----------+--------+
```

`name` và `city` không có trong `GROUP BY` nhưng hợp lệ, vì `c.id` là khoá chính. (Vì sao Em có 0 chứ
không phải 1: `COUNT(o.id)` bỏ qua NULL, mục 9.1.)

Trường hợp 2: đẳng thức trong `WHERE` hoặc trong `ON` của INNER JOIN truyền phụ thuộc từ bảng này sang
bảng kia.

```sql
SELECT o.customer_id, c.name, COUNT(*) AS so_don
FROM orders o
JOIN customers c ON c.id = o.customer_id
GROUP BY o.customer_id
ORDER BY o.customer_id;
-- 1 An 3 | 2 Bình 2 | 3 Chi 2 | 4 Dũng 1
```

Chuỗi suy luận: `o.customer_id` bằng `c.id` (điều kiện `ON`), và `c.id` là khoá chính nên xác định
`c.name`. Vậy `c.name` phụ thuộc hàm vào `o.customer_id`.

Trường hợp 3: cột bị `WHERE` ép về đúng một giá trị.

```sql
SELECT customer_id, SUM(total) AS tong FROM orders WHERE customer_id = 1;
-- 1 | 570.00
```

Không có `GROUP BY`, nhưng `WHERE customer_id = 1` làm cột này chỉ có một giá trị, nên MySQL chấp nhận.

⚠️ Với LEFT JOIN, đẳng thức trong `ON` chỉ truyền phụ thuộc theo một chiều, từ bảng bên trái sang bảng
bên phải. Tài liệu MySQL có ví dụ: gom theo cột của bảng bên phải rồi chọn cột của bảng bên trái bị từ
chối, vì mọi dòng bên trái không ghép được đều có cột bên phải là NULL và rơi chung vào một nhóm NULL,
trong khi cột bên trái của chúng khác nhau. Thói quen an toàn: khi LEFT JOIN, gom theo khoá chính của
bảng bên trái, như trường hợp 1.

### 5.4 Gặp lỗi 1055 thì sửa thế nào

Trước hết hãy tự hỏi "với mỗi nhóm, mình muốn cột này hiển thị giá trị nào?". Câu trả lời quyết định
cách sửa:

1. "Mình muốn tách nhóm theo cả cột đó": thêm nó vào `GROUP BY`, như câu ở mục 3.3.
2. "Mình muốn một bản tóm tắt của cột đó": bọc nó trong hàm tổng hợp.

   ```sql
   SELECT customer_id,
          GROUP_CONCAT(DISTINCT status ORDER BY status) AS cac_trang_thai,
          COUNT(*) AS so_don
   FROM orders
   GROUP BY customer_id
   ORDER BY customer_id;
   -- 1 | paid           | 3
   -- 2 | cancelled,paid | 2
   -- 3 | paid,pending   | 2
   -- 4 | paid           | 1
   ```

3. "Mình biết chắc mọi dòng trong nhóm có cùng giá trị, chỉ là MySQL không chứng minh được": dùng
   `ANY_VALUE(cot)`. Ví dụ gom theo ngày và muốn hiện thứ trong tuần. Thứ được xác định bởi ngày,
   nhưng MySQL không suy ra được rằng `DAYNAME(created_at)` phụ thuộc hàm vào `DATE(created_at)`:

   ```sql
   SELECT DATE(created_at) AS ngay,
          ANY_VALUE(DAYNAME(created_at)) AS thu,
          COUNT(*) AS so_don
   FROM orders
   GROUP BY DATE(created_at)
   ORDER BY ngay;
   ```

   ```
   +------------+----------+--------+
   | ngay       | thu      | so_don |
   +------------+----------+--------+
   | 2026-01-05 | Monday   |      2 |
   | 2026-01-31 | Saturday |      1 |
   | 2026-02-02 | Monday   |      2 |
   | 2026-02-14 | Saturday |      2 |
   | 2026-03-01 | Sunday   |      1 |
   +------------+----------+--------+
   ```

   `ANY_VALUE()` không phải hàm tổng hợp; nó chỉ tắt việc kiểm tra cho riêng biểu thức đó và trả về giá
   trị của một dòng bất kỳ trong nhóm. Ở đây mọi dòng cùng ngày có cùng thứ nên "bất kỳ" cũng là
   đúng. Nếu dùng `ANY_VALUE` cho cột mà các dòng trong nhóm khác nhau thật, bạn nhận về một giá trị
   ngẫu nhiên và bug sẽ âm thầm nằm đó.
4. "Mình muốn các cột của một dòng cụ thể trong nhóm (dòng mới nhất, dòng lớn nhất)": đó là bài toán
   khác, xem mục 5.6.

### 5.5 Đừng tắt ONLY_FULL_GROUP_BY

Một "cách sửa" phổ biến trên mạng là xoá `ONLY_FULL_GROUP_BY` khỏi `sql_mode`. Khi chế độ tắt, câu ở
mục 5.1 chạy được, và MySQL lấy cho mỗi nhóm một giá trị `status` bất kỳ. Tài liệu MySQL nói rõ: giá trị
được chọn là không tất định (*nondeterministic*), và thêm `ORDER BY` cũng không ảnh hưởng được việc chọn
giá trị nào, vì sắp xếp diễn ra sau khi giá trị đã được chọn. Query chạy đúng trên máy dev, rồi sai trên
production khi dữ liệu hay execution plan đổi, và không có lỗi nào báo cho bạn biết.

Với Laravel: file `config/database.php` của Laravel 13 để `'strict' => true` cho kết nối `mysql`. Khi
đó, mỗi lần kết nối Laravel tự chạy `SET SESSION sql_mode=...` với đúng sáu chế độ mặc định ở trên (với
MySQL từ 8.0.11). Nhiều project đổi thành `'strict' => false` cho "hết lỗi GROUP BY", nhưng mã nguồn
`MySqlConnector` cho thấy khi `strict` là `false`, `sql_mode` bị đặt thành chỉ còn
`NO_ENGINE_SUBSTITUTION`. Tức là bạn tắt luôn strict mode (MySQL âm thầm cắt dữ liệu sai kiểu thay vì
báo lỗi) và `ERROR_FOR_DIVISION_BY_ZERO`, không chỉ riêng `ONLY_FULL_GROUP_BY`. Nếu thật sự phải tuỳ
chỉnh, Laravel có tuỳ chọn `'modes' => [...]` để liệt kê chính xác từng chế độ; nhưng cách đúng vẫn là sửa
câu query.

### 5.6 Bài toán "dòng mới nhất của mỗi nhóm"

Yêu cầu: với mỗi khách, lấy đơn gần nhất (id, trạng thái, thời điểm). Bản năng đầu tiên thường là:

```sql
-- SAI
SELECT customer_id, id, status, MAX(created_at) AS gan_nhat
FROM orders
GROUP BY customer_id;
```

Với `ONLY_FULL_GROUP_BY` bật, câu này bị lỗi 1055 vì `id` và `status`. Nếu tắt chế độ, nó chạy, nhưng
`MAX(created_at)` và `id` được tính độc lập: `MAX` cho thời điểm lớn nhất, còn `id` là của một dòng bất
kỳ trong nhóm, không có gì bảo đảm đó là dòng có thời điểm lớn nhất. Đây chính là loại bug mà
`ONLY_FULL_GROUP_BY` được sinh ra để chặn.

Cách đúng với những gì đã học: tìm thời điểm lớn nhất của mỗi khách trong một query con, rồi join ngược
lại để lấy nguyên dòng.

```sql
SELECT o.customer_id, o.id, o.status, o.created_at
FROM orders o
JOIN (
  SELECT customer_id, MAX(created_at) AS gan_nhat
  FROM orders
  GROUP BY customer_id
) m ON m.customer_id = o.customer_id AND m.gan_nhat = o.created_at
ORDER BY o.customer_id;
```

```
+-------------+-----+-----------+---------------------+
| customer_id | id  | status    | created_at          |
+-------------+-----+-----------+---------------------+
|           1 | 108 | paid      | 2026-03-01 07:00:00 |
|           2 | 104 | cancelled | 2026-02-02 10:00:00 |
|           3 | 106 | pending   | 2026-02-14 08:00:00 |
|           4 | 107 | paid      | 2026-02-14 09:30:00 |
+-------------+-----+-----------+---------------------+
```

⚠️ Nếu một khách có hai đơn cùng đúng thời điểm lớn nhất, cách này trả về cả hai dòng. Muốn đúng một dòng
mỗi nhóm, kèm luật phá hoà rõ ràng, cách gọn nhất là `ROW_NUMBER()`, bài kinh điển "top N mỗi nhóm"
của [chương 10](10-window-function.md). Query con trong `FROM` (*derived table*) được giải thích ở
[chương 09](09-subquery-cte-union.md).

### 5.7 Đối chiếu PostgreSQL

- PostgreSQL luôn áp dụng quy tắc này, không có công tắc để tắt.
- Tài liệu PostgreSQL ghi: phụ thuộc hàm tồn tại khi các cột gom nhóm (hoặc một tập con của chúng) là
  khoá chính của bảng chứa cột không gom nhóm. PostgreSQL không suy luận qua đẳng thức như MySQL. Câu ở
  trường hợp 2 (gom theo `o.customer_id`, chọn `c.name`) bị PostgreSQL từ chối; viết `GROUP BY c.id`
  thì chạy được ở cả hai.
- PostgreSQL có hàm tổng hợp `any_value()` từ bản 16, trả về một giá trị bất kỳ trong các giá trị khác
  NULL của nhóm.

---

## 6. Dòng tổng phụ và tổng cộng: WITH ROLLUP

### 6.1 Vấn đề

Báo cáo thường cần thêm dòng tổng: tổng của từng khách, rồi tổng toàn bộ ở cuối bảng. Không có công cụ
riêng, bạn phải chạy thêm một query không `GROUP BY` và ghép bằng `UNION ALL`, hoặc cộng trong PHP.
`WITH ROLLUP` làm việc đó ngay trong một câu: nó thêm các dòng *super-aggregate* (tổng hợp ở mức cao
hơn) vào kết quả.

### 6.2 ROLLUP một cột

```sql
SELECT status, COUNT(*) AS so_don, SUM(total) AS tong_tien
FROM orders
GROUP BY status WITH ROLLUP;
```

```
+-----------+--------+-----------+
| status    | so_don | tong_tien |
+-----------+--------+-----------+
| cancelled |      1 |    200.00 |
| paid      |      6 |   1720.00 |
| pending   |      1 |     80.00 |
| NULL      |      8 |   2000.00 |
+-----------+--------+-----------+
```

Dòng cuối là dòng tổng cộng: cột gom nhóm `status` mang giá trị NULL với nghĩa "tất cả các trạng
thái", còn các hàm tổng hợp được tính trên toàn bộ dòng. Thứ tự in ở trên (dòng tổng nằm sau các nhóm)
là thứ tự bạn thường thấy, giống các ví dụ trong tài liệu MySQL; mục 6.3 chỉ cách viết `ORDER BY` để
chắc chắn về thứ tự.

### 6.3 ROLLUP nhiều cột: thứ tự cột là thứ bậc

Với nhiều cột, `ROLLUP` tạo tổng phụ theo thứ bậc từ phải sang trái: bỏ dần cột cuối cùng.
`GROUP BY customer_id, status WITH ROLLUP` sinh ra ba mức:

- mức chi tiết: mỗi cặp (khách, trạng thái);
- tổng phụ cho mỗi khách: `status` là NULL;
- tổng cộng: cả hai cột là NULL.

```sql
SELECT customer_id, status, COUNT(*) AS so_don, SUM(total) AS tong_tien
FROM orders
GROUP BY customer_id, status WITH ROLLUP
ORDER BY GROUPING(customer_id), customer_id, GROUPING(status), status;
```

```
+-------------+-----------+--------+-----------+
| customer_id | status    | so_don | tong_tien |
+-------------+-----------+--------+-----------+
|           1 | paid      |      3 |    570.00 |
|           1 | NULL      |      3 |    570.00 |
|           2 | cancelled |      1 |    200.00 |
|           2 | paid      |      1 |    500.00 |
|           2 | NULL      |      2 |    700.00 |
|           3 | paid      |      1 |    250.00 |
|           3 | pending   |      1 |     80.00 |
|           3 | NULL      |      2 |    330.00 |
|           4 | paid      |      1 |    400.00 |
|           4 | NULL      |      1 |    400.00 |
|        NULL | NULL      |      8 |   2000.00 |
+-------------+-----------+--------+-----------+
```

`ORDER BY GROUPING(...)` ở cuối giúp mỗi dòng tổng phụ đứng ngay sau các dòng chi tiết của nó và dòng
tổng cộng đứng cuối cùng; hàm `GROUPING()` được giải thích ngay dưới đây. Các ví dụ trong tài liệu MySQL
không có `ORDER BY` và các dòng tổng vẫn nằm sau nhóm của chúng, nhưng như mục 3.8 đã nói, muốn chắc về
thứ tự thì viết `ORDER BY`.

Đảo thứ tự cột thành `GROUP BY status, customer_id WITH ROLLUP` thì tổng phụ là theo từng trạng thái
(mọi khách), không phải theo từng khách. ROLLUP không tạo tổng phụ cho mọi tổ hợp; nó chỉ đi theo một
thứ bậc.

### 6.4 GROUPING(): NULL thật hay NULL của dòng tổng?

Vấn đề: dữ liệu cũng có thể chứa NULL thật. Gom khách theo thành phố, nhớ rằng `city` của Dũng là NULL:

```sql
SELECT city, COUNT(*) AS so_khach
FROM customers
GROUP BY city WITH ROLLUP;
```

Kết quả có hai dòng với `city` là NULL: một dòng là nhóm của Dũng (`so_khach` = 1), một dòng là tổng
cộng (`so_khach` = 5). Nhìn vào NULL thì không phân biệt được.

`GROUPING(expr)` trả về 1 nếu NULL ở cột đó trong dòng hiện tại là NULL của dòng super-aggregate, và 0
trong mọi trường hợp khác (giá trị thường, hoặc NULL thật của dữ liệu). Dùng nó để gắn nhãn:

```sql
SELECT IF(GROUPING(city) = 1, 'Tổng cộng', COALESCE(city, '(chưa rõ)')) AS thanh_pho,
       COUNT(*) AS so_khach
FROM customers
GROUP BY city WITH ROLLUP
ORDER BY GROUPING(city), city;
```

```
+-------------+----------+
| thanh_pho   | so_khach |
+-------------+----------+
| (chưa rõ)   |        1 |
| Đà Nẵng     |        1 |
| Hà Nội      |        2 |
| TP.HCM      |        1 |
| Tổng cộng   |        5 |
+-------------+----------+
```

Áp dụng cho ví dụ hai cột ở mục 6.3 để có bảng dễ đọc:

```sql
SELECT IF(GROUPING(customer_id) = 1, 'Tất cả khách', customer_id) AS khach,
       IF(GROUPING(status) = 1, 'Mọi trạng thái', status)         AS trang_thai,
       COUNT(*)   AS so_don,
       SUM(total) AS tong_tien
FROM orders
GROUP BY customer_id, status WITH ROLLUP
ORDER BY GROUPING(customer_id), customer_id, GROUPING(status), status;
-- ...
-- 2            | cancelled      | 1 | 200.00
-- 2            | paid           | 1 | 500.00
-- 2            | Mọi trạng thái | 2 | 700.00
-- ...
-- Tất cả khách | Mọi trạng thái | 8 | 2000.00
```

Vài quy tắc của `GROUPING()` theo tài liệu MySQL:

- Dùng được trong danh sách `SELECT`, trong `HAVING` và trong `ORDER BY`.
- Mỗi đối số phải khớp đúng một biểu thức trong `GROUP BY`, và không được là số thứ tự cột.
- Có thể truyền nhiều đối số, `GROUPING(a, b)`; khi đó kết quả là một *bitmask*, bit thấp nhất ứng với
  đối số bên phải nhất. Kết quả khác 0 nghĩa là dòng đó là một dòng tổng nào đó. Ví dụ chỉ giữ các dòng
  tổng:

```sql
SELECT customer_id, status, SUM(total) AS tong_tien
FROM orders
GROUP BY customer_id, status WITH ROLLUP
HAVING GROUPING(customer_id, status) <> 0;
-- 5 dòng: tổng của khách 1, 2, 3, 4 và dòng tổng cộng
```

### 6.5 Những điều cần nhớ khi dùng ROLLUP

- Không lọc dòng tổng bằng `WHERE`. NULL của dòng super-aggregate được tạo ở giai đoạn rất muộn, sau
  `WHERE`, nên tài liệu nói bạn chỉ kiểm tra được chúng trong `SELECT` hoặc `HAVING`. Muốn lọc thì dùng
  `HAVING` với `GROUPING()` như ví dụ trên.
- `LIMIT` áp dụng sau `ROLLUP`, nên nó đếm cả các dòng tổng được thêm vào. `LIMIT 5` có thể cắt mất
  dòng tổng cộng, và kết quả khó hiểu.
- Một số dòng chi tiết có thể trùng giá trị với dòng tổng (khách 1 chỉ có trạng thái `paid` nên dòng
  chi tiết và dòng tổng phụ đều là 3 đơn, 570). Đó là đúng, không phải lỗi.
- Dòng tổng phụ được tính trên toàn bộ các dòng gốc của nhóm lớn, không phải bằng cách cộng các dòng
  hiển thị phía trên nó. Với `SUM` và `COUNT` thì hai cách cho cùng kết quả, nhưng với `AVG` thì không:
  trung bình của cả bảng khác trung bình của các trung bình. Nếu bạn tự tính dòng tổng trong PHP từ
  các dòng đã gom, phải nhớ điều này.
- MySQL 8.4 còn chấp nhận cú pháp chuẩn `GROUP BY ROLLUP (customer_id, status)`, tương đương
  `WITH ROLLUP`. MySQL 8.0 chỉ có cách viết `WITH ROLLUP`.
- Tài liệu MySQL 8.4 chỉ mô tả ROLLUP (bộ phân tích cú pháp có nhận `GROUP BY CUBE (...)`, nhưng mã
  nguồn chỉ cho chạy nó trên secondary engine HeatWave, không chạy trên InnoDB). PostgreSQL có thêm `CUBE` (tổng phụ cho mọi tổ hợp cột) và
  `GROUPING SETS` (tự liệt kê các mức cần tổng), cùng hàm `GROUPING()` tương tự. Cú pháp PostgreSQL:
  `GROUP BY ROLLUP (customer_id, status)`, không có dạng `WITH ROLLUP`.

---

## 7. Aggregate có điều kiện và xoay bảng (pivot)

### 7.1 Đếm và cộng có điều kiện

Thường bạn muốn nhiều con số với các điều kiện khác nhau trong cùng một dòng kết quả: tổng số đơn, số
đơn đã thanh toán, số đơn bị huỷ. Dùng `WHERE` thì chỉ được một điều kiện cho cả câu. Mẹo là đưa điều
kiện vào bên trong hàm tổng hợp bằng `CASE`:

```sql
SELECT DATE_FORMAT(created_at, '%Y-%m') AS thang,
       COUNT(*)                                             AS tat_ca,
       COUNT(CASE WHEN status = 'paid' THEN 1 END)          AS da_tt,
       COUNT(CASE WHEN status = 'cancelled' THEN 1 END)     AS da_huy,
       SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END) AS doanh_thu
FROM orders
GROUP BY thang
ORDER BY thang;
```

```
+---------+--------+-------+--------+-----------+
| thang   | tat_ca | da_tt | da_huy | doanh_thu |
+---------+--------+-------+--------+-----------+
| 2026-01 |      3 |     3 |      0 |    950.00 |
| 2026-02 |      4 |     2 |      1 |    650.00 |
| 2026-03 |      1 |     1 |      0 |    120.00 |
+---------+--------+-------+--------+-----------+
```

Vì sao chạy đúng:

- `CASE WHEN status = 'paid' THEN 1 END` không có `ELSE`, nên trả NULL cho dòng không thoả. `COUNT`
  bỏ qua NULL, vậy là chỉ đếm dòng thoả điều kiện.
- `SUM(CASE WHEN ... THEN total ELSE 0 END)` cộng `total` của dòng thoả, cộng 0 cho dòng không thoả.
  `ELSE 0` quan trọng: nếu một tháng không có đơn `paid` nào mà bạn bỏ `ELSE 0`, mọi giá trị đều NULL
  và kết quả là NULL thay vì 0.

MySQL có cách viết ngắn hơn: phép so sánh trả về 1 (đúng) hoặc 0 (sai), nên `SUM(status = 'paid')` đếm
số đơn đã thanh toán. Cách này gọn nhưng là đặc thù MySQL; PostgreSQL không cộng được kiểu `boolean`.

⚠️ Nhắc lại bẫy ở mục 2.2: `COUNT(status = 'paid')` đếm mọi dòng (vì 0 cũng khác NULL). Đếm có điều
kiện thì dùng `COUNT(CASE WHEN ... THEN 1 END)` hoặc `SUM(...)`, không dùng `COUNT(dieu_kien)`.

PostgreSQL có cú pháp chuẩn SQL dành riêng cho việc này, mệnh đề `FILTER`: chỉ những dòng thoả điều
kiện mới được đưa vào hàm tổng hợp. MySQL 8.4 không hỗ trợ `FILTER`.

```sql
-- PostgreSQL
SELECT to_char(created_at, 'YYYY-MM') AS thang,
       count(*)                                   AS tat_ca,
       count(*) FILTER (WHERE status = 'paid')    AS da_tt,
       sum(total) FILTER (WHERE status = 'paid')  AS doanh_thu
FROM orders
GROUP BY thang
ORDER BY thang;
```

Lưu ý `sum(...) FILTER (...)` cũng ra NULL khi không có dòng nào thoả, giống `SUM` không có `ELSE 0`.

### 7.2 Xoay bảng: mỗi giá trị một cột

*Pivot* (xoay bảng) là biến giá trị của một cột thành nhiều cột. Báo cáo doanh thu theo tháng, mỗi danh
mục sản phẩm một cột:

```sql
SELECT DATE_FORMAT(o.created_at, '%Y-%m') AS thang,
       SUM(CASE WHEN p.category = 'Điện tử'        THEN i.qty * i.unit_price ELSE 0 END) AS dien_tu,
       SUM(CASE WHEN p.category = 'Văn phòng phẩm' THEN i.qty * i.unit_price ELSE 0 END) AS van_phong_pham,
       SUM(CASE WHEN p.category = 'Sách'           THEN i.qty * i.unit_price ELSE 0 END) AS sach,
       SUM(i.qty * i.unit_price)                                                         AS tong
FROM orders o
JOIN order_items i ON i.order_id = o.id
JOIN products p    ON p.id = i.product_id
WHERE o.status = 'paid'
GROUP BY thang
ORDER BY thang;
```

```
+---------+---------+----------------+--------+--------+
| thang   | dien_tu | van_phong_pham | sach   | tong   |
+---------+---------+----------------+--------+--------+
| 2026-01 |  750.00 |         200.00 |   0.00 | 950.00 |
| 2026-02 |  300.00 |         230.00 | 120.00 | 650.00 |
| 2026-03 |    0.00 |           0.00 | 120.00 | 120.00 |
+---------+---------+----------------+--------+--------+
```

Tự kiểm tra tháng 1: đơn 101 có tai nghe 200 (điện tử) và 2 sổ tay 100 (văn phòng phẩm); đơn 102 có sạc
150 (điện tử); đơn 103 có 2 tai nghe 400 (điện tử) và 10 bút bi 100 (văn phòng phẩm). Điện tử: 200 +
150 + 400 = 750; văn phòng phẩm: 100 + 100 = 200; tổng 950, khớp doanh thu tháng 1 ở mục 7.1.

Ở đây join từ `orders` sang `order_items` là join một-nhiều, nhưng không bị nhân dòng sai, vì ta cộng
các cột của phía "nhiều" (`qty`, `unit_price`), mỗi dòng chi tiết đúng một lần. Nếu cộng `o.total` thì
sẽ sai; mục 9.2 giải thích.

Giới hạn của pivot bằng SQL: danh sách cột phải viết cứng trong câu lệnh. Thêm một danh mục mới thì phải
sửa query. Nếu số cột thay đổi theo dữ liệu, hãy lấy dữ liệu dạng dọc (`GROUP BY thang, p.category`) rồi
xoay ở tầng ứng dụng, hoặc sinh câu SQL động trong code (cẩn thận SQL injection khi ghép tên cột).

---

## 8. Các bài toán báo cáo thường gặp

Mục này ghép mọi thứ đã học thành những query bạn sẽ viết thật trong công việc. Với mỗi bài, hãy tự
viết trước rồi mới xem lời giải mẫu.

### 8.1 Doanh thu theo ngày

```sql
SELECT DATE(created_at) AS ngay,
       COUNT(*)         AS so_don,
       SUM(total)       AS doanh_thu
FROM orders
WHERE status = 'paid'
  AND created_at >= '2026-01-01'
  AND created_at <  '2026-04-01'
GROUP BY DATE(created_at)
ORDER BY ngay;
```

```
+------------+--------+-----------+
| ngay       | so_don | doanh_thu |
+------------+--------+-----------+
| 2026-01-05 |      2 |    450.00 |
| 2026-01-31 |      1 |    500.00 |
| 2026-02-02 |      1 |    250.00 |
| 2026-02-14 |      1 |    400.00 |
| 2026-03-01 |      1 |    120.00 |
+------------+--------+-----------+
```

Hai thói quen đáng học từ câu này:

- Lọc khoảng thời gian bằng khoảng nửa mở trên chính cột gốc: `created_at >= đầu` và `created_at <
  đầu_kỳ_sau`. Đừng viết `WHERE YEAR(created_at) = 2026` hay `WHERE DATE(created_at) BETWEEN ...`: bọc
  cột trong hàm thường làm database không dùng được index trên `created_at` ([chương 11](11-index.md)).
- ⚠️ Đừng viết `created_at BETWEEN '2026-01-01' AND '2026-03-31'` với cột `DATETIME`. Chuỗi
  `'2026-03-31'` được hiểu là `2026-03-31 00:00:00`, nên mọi đơn trong ngày 31/03 sau nửa đêm bị bỏ sót.
  Khoảng nửa mở `< '2026-04-01'` không có lỗ hổng này.

Việc gom theo `DATE(created_at)` thì không sao: hàm ở `GROUP BY` chỉ áp dụng cho các dòng đã lọt qua
`WHERE`.

### 8.2 Doanh thu theo tháng

```sql
SELECT DATE_FORMAT(created_at, '%Y-%m') AS thang,
       COUNT(*)             AS so_don,
       SUM(total)           AS doanh_thu,
       ROUND(AVG(total), 2) AS gia_tri_tb
FROM orders
WHERE status = 'paid'
GROUP BY thang
ORDER BY thang;
```

```
+---------+--------+-----------+------------+
| thang   | so_don | doanh_thu | gia_tri_tb |
+---------+--------+-----------+------------+
| 2026-01 |      3 |    950.00 |     316.67 |
| 2026-02 |      2 |    650.00 |     325.00 |
| 2026-03 |      1 |    120.00 |     120.00 |
+---------+--------+-----------+------------+
```

`gia_tri_tb` là giá trị trung bình mỗi đơn (*average order value*, AOV), một chỉ số hay gặp. Tháng 1:
950 / 3 = 316.666..., làm tròn còn 316.67.

⚠️ `GROUP BY MONTH(created_at)` gộp tháng 1 năm 2025 với tháng 1 năm 2026 thành một nhóm. Luôn gom theo
cả năm và tháng: `DATE_FORMAT(created_at, '%Y-%m')` hoặc `GROUP BY YEAR(created_at), MONTH(created_at)`.
Định dạng `%m` cho tháng có hai chữ số (01 đến 12) nên chuỗi `'2026-02'` sắp xếp đúng trước `'2026-10'`;
nếu dùng `%c` (tháng không có số 0 đứng đầu) thì `'2026-10'` lại đứng trước `'2026-2'` khi so chuỗi.

### 8.3 Ngày không có đơn bị "biến mất"

`GROUP BY` chỉ tạo nhóm cho giá trị có trong dữ liệu. Ngày không có đơn nào thì không có dòng nào, và
biểu đồ vẽ từ kết quả sẽ nối thẳng từ ngày 02/02 sang 14/02 như thể ở giữa không có gì. Muốn ngày trống
hiện số 0, cần một danh sách đủ các ngày rồi LEFT JOIN dữ liệu vào. Danh sách ngày có thể là một bảng lịch
(*calendar table*) tạo sẵn, hoặc sinh tại chỗ bằng recursive CTE ([chương 09](09-subquery-cte-union.md)):

```sql
WITH RECURSIVE lich AS (
  SELECT DATE('2026-02-01') AS d
  UNION ALL
  SELECT d + INTERVAL 1 DAY FROM lich WHERE d < '2026-02-07'
)
SELECT lich.d                     AS ngay,
       COUNT(o.id)                AS so_don,
       COALESCE(SUM(o.total), 0)  AS doanh_thu
FROM lich
LEFT JOIN orders o
       ON o.status = 'paid'
      AND o.created_at >= lich.d
      AND o.created_at <  lich.d + INTERVAL 1 DAY
GROUP BY lich.d
ORDER BY lich.d;
```

```
+------------+--------+-----------+
| ngay       | so_don | doanh_thu |
+------------+--------+-----------+
| 2026-02-01 |      0 |      0.00 |
| 2026-02-02 |      1 |    250.00 |
| 2026-02-03 |      0 |      0.00 |
| 2026-02-04 |      0 |      0.00 |
| 2026-02-05 |      0 |      0.00 |
| 2026-02-06 |      0 |      0.00 |
| 2026-02-07 |      0 |      0.00 |
+------------+--------+-----------+
```

Ba chi tiết làm câu này đúng:

- Điều kiện của `orders` (`status`, khoảng thời gian) nằm trong `ON`, không nằm trong `WHERE`. Đặt ở
  `WHERE` sẽ loại các ngày không ghép được và LEFT JOIN thành INNER JOIN ([chương 07](07-join.md)).
- `COUNT(o.id)` chứ không phải `COUNT(*)`: ngày không có đơn vẫn có một dòng (bên `orders` toàn NULL),
  `COUNT(*)` sẽ đếm nó thành 1.
- `COALESCE(SUM(o.total), 0)`: `SUM` của toàn NULL là NULL.

MySQL mặc định dừng một recursive CTE sau 1000 vòng lặp (biến `cte_max_recursion_depth`), đủ cho gần ba
năm tính theo ngày. Báo cáo dài hơn thì tăng biến này hoặc dùng bảng lịch.

### 8.4 Ngày của ai? Báo cáo theo múi giờ

Trong dữ liệu mẫu, `created_at` là `DATETIME` lưu giờ UTC, một quy ước phổ biến (ví dụ ứng dụng Laravel
để `timezone` là `UTC`). Nhưng kế toán ở Việt Nam muốn doanh thu theo ngày, theo tháng giờ Việt Nam
(UTC+7). Đơn 103 tạo lúc 20:30 ngày 31/01 giờ UTC, tức 03:30 sáng ngày 01/02 giờ Việt Nam: nó thuộc
tháng 1 hay tháng 2 tuỳ bạn hỏi theo giờ nào.

```sql
SELECT DATE_FORMAT(CONVERT_TZ(created_at, '+00:00', '+07:00'), '%Y-%m') AS thang_vn,
       COUNT(*)   AS so_don,
       SUM(total) AS doanh_thu
FROM orders
WHERE status = 'paid'
GROUP BY thang_vn
ORDER BY thang_vn;
```

| thang_vn | so_don | doanh_thu | So với cách tính theo UTC ở mục 8.2 |
|---|---|---|---|
| 2026-01 | 2 | 450.00 | UTC: 3 đơn, 950.00 |
| 2026-02 | 3 | 1150.00 | UTC: 2 đơn, 650.00 |
| 2026-03 | 1 | 120.00 | UTC: 1 đơn, 120.00 |

Chỉ một đơn đổi tháng mà con số tháng 1 lệch hơn một nửa. Đây là loại sai lệch khiến hai bộ phận cãi
nhau vì "số của tôi khác số của anh".

Vài lưu ý:

- `CONVERT_TZ` với múi giờ dạng độ lệch như `'+07:00'` luôn chạy được. Múi giờ có tên như
  `'Asia/Ho_Chi_Minh'` chỉ dùng được khi các bảng thông tin múi giờ trong database `mysql` đã được nạp.
  ⚠️ Nếu chưa nạp, `CONVERT_TZ` không báo lỗi mà trả về NULL (tài liệu: hàm trả NULL khi có đối số không
  hợp lệ), và mọi đơn dồn vào một nhóm NULL duy nhất. Việt Nam không đổi giờ theo mùa nên độ lệch cố
  định là đủ; với múi giờ có giờ mùa hè (*DST*) thì phải dùng tên múi giờ.
- Để lọc "tháng 2 theo giờ Việt Nam" mà vẫn dùng được index, đổi mốc thời gian chứ đừng đổi cột:
  `created_at >= '2026-01-31 17:00:00' AND created_at < '2026-02-28 17:00:00'` (0 giờ ngày 01/02 và
  01/03 giờ Việt Nam, đổi ra UTC).
- Chọn kiểu `DATETIME` hay `TIMESTAMP` và cách MySQL xử lý múi giờ của từng kiểu được bàn ở
  [chương 03](03-kieu-du-lieu.md).

### 8.5 Top khách hàng, và cái bẫy đồng hạng

Ba khách mua nhiều tiền nhất (chỉ tính đơn đã thanh toán):

```sql
SELECT c.id, c.name, COUNT(*) AS so_don, SUM(o.total) AS doanh_thu
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid'
GROUP BY c.id
ORDER BY doanh_thu DESC, c.id
LIMIT 3;
```

```
+----+------+--------+-----------+
| id | name | so_don | doanh_thu |
+----+------+--------+-----------+
|  1 | An   |      3 |    570.00 |
|  2 | Bình |      1 |    500.00 |
|  4 | Dũng |      1 |    400.00 |
+----+------+--------+-----------+
```

`c.name` hợp lệ dù không có trong `GROUP BY`, vì `c.id` là khoá chính (mục 5.3). Cột `c.id` ở cuối
`ORDER BY` đóng vai trò phá hoà; vì sao cần nó thì xem bài tiếp theo.

Ba sản phẩm bán chạy nhất theo số lượng:

```sql
SELECT p.id, p.name, SUM(i.qty) AS so_luong
FROM order_items i
JOIN orders o   ON o.id = i.order_id
JOIN products p ON p.id = i.product_id
WHERE o.status = 'paid'
GROUP BY p.id
ORDER BY so_luong DESC
LIMIT 3;
```

Bỏ `LIMIT` để thấy toàn bộ bảng xếp hạng: Bút bi 23, Sổ tay 4, Tai nghe 3, Sạc dự phòng 3, Sách SQL 2.
Tai nghe và Sạc dự phòng đồng hạng ba. Với `ORDER BY so_luong DESC LIMIT 3`, dòng thứ ba là một trong hai
sản phẩm đó, và database không hứa là sản phẩm nào; lần chạy sau, sau khi dữ liệu hay execution plan
đổi, có thể ra sản phẩm kia. Báo cáo "nhảy" mà không ai sửa gì.

Cách xử lý tuỳ yêu cầu nghiệp vụ:

- Cần đúng 3 dòng và ổn định: thêm cột phá hoà vào cuối `ORDER BY`, ví dụ `ORDER BY so_luong DESC, p.id`
  (lúc này Tai nghe, id 3, được chọn).
- Cần lấy đủ mọi sản phẩm đồng hạng: PostgreSQL có `FETCH FIRST 3 ROWS WITH TIES` (bắt buộc có
  `ORDER BY`); MySQL không có cú pháp này, dùng `RANK()` hoặc `DENSE_RANK()` ở
  [chương 10](10-window-function.md).

"Top N trong mỗi nhóm" (ví dụ khách mua nhiều nhất ở mỗi thành phố) cũng là bài của window function,
chương 10.

### 8.6 Tỷ trọng: mỗi phần chiếm bao nhiêu phần trăm

Tỷ trọng doanh thu theo danh mục cần hai thứ: doanh thu của từng danh mục (gom nhóm) và tổng doanh thu
(một con số cho cả bảng). Cách dùng kiến thức đến giờ là một subquery vô hướng ở mẫu số:

```sql
SELECT p.category,
       SUM(i.qty * i.unit_price) AS doanh_thu,
       ROUND(100 * SUM(i.qty * i.unit_price) / (
         SELECT SUM(i2.qty * i2.unit_price)
         FROM order_items i2
         JOIN orders o2 ON o2.id = i2.order_id
         WHERE o2.status = 'paid'
       ), 1) AS phan_tram
FROM order_items i
JOIN orders o   ON o.id = i.order_id
JOIN products p ON p.id = i.product_id
WHERE o.status = 'paid'
GROUP BY p.category
ORDER BY doanh_thu DESC;
```

```
+----------------+-----------+-----------+
| category       | doanh_thu | phan_tram |
+----------------+-----------+-----------+
| Điện tử        |   1050.00 |      61.0 |
| Văn phòng phẩm |    430.00 |      25.0 |
| Sách           |    240.00 |      14.0 |
+----------------+-----------+-----------+
```

Nhân 100 trước khi chia, và chỉ làm tròn ở bước cuối. Với window function, mẫu số viết gọn hơn nhiều:
`SUM(SUM(...)) OVER ()` ([chương 10](10-window-function.md)).

### 8.7 Tìm dữ liệu trùng

`GROUP BY` kết hợp `HAVING COUNT(*) > 1` là cách chuẩn để tìm trùng. Ví dụ: khách đặt hơn một đơn trong
cùng một ngày, dấu hiệu của việc bấm nút "Đặt hàng" hai lần:

```sql
SELECT customer_id,
       DATE(created_at)              AS ngay,
       COUNT(*)                      AS so_don,
       GROUP_CONCAT(id ORDER BY id)  AS cac_don
FROM orders
GROUP BY customer_id, DATE(created_at)
HAVING COUNT(*) > 1;
-- 1 | 2026-01-05 | 2 | 101,102
```

Cùng khuôn đó: tìm email trùng trước khi thêm ràng buộc `UNIQUE` (`GROUP BY email HAVING COUNT(*) > 1`),
tìm sản phẩm bị nhập hai lần cùng mã. Lưu ý collation (mục 3.6): với collation không phân biệt hoa
thường, `An@x.com` và `an@x.com` được tính là trùng, đúng như một unique index trên cột đó sẽ coi chúng
là trùng.

### 8.8 Khách đã mua đủ mọi danh mục

Bài kinh điển này (trong lý thuyết gọi là *relational division*, phép chia quan hệ) giải gọn bằng
`COUNT(DISTINCT)` trong `HAVING`: một khách mua đủ khi số danh mục khác nhau họ đã mua bằng tổng số danh
mục.

```sql
SELECT o.customer_id
FROM orders o
JOIN order_items i ON i.order_id = o.id
JOIN products p    ON p.id = i.product_id
WHERE o.status = 'paid'
GROUP BY o.customer_id
HAVING COUNT(DISTINCT p.category) = (SELECT COUNT(DISTINCT category) FROM products);
-- 1   (An: điện tử ở đơn 101 và 102, văn phòng phẩm ở đơn 101, sách ở đơn 108)
```

Bình, Chi, Dũng mỗi người mới mua hai trong ba danh mục.

---

## 9. Ba cái bẫy lớn: NULL, nhân dòng, chia cho 0

Ba lỗi dưới đây có chung một đặc điểm nguy hiểm: query chạy bình thường, không lỗi, không warning đáng
chú ý, chỉ có con số là sai.

### 9.1 NULL

Bẫy 1: `COUNT(*)` sau LEFT JOIN. Đếm số đơn đã thanh toán của mọi khách, kể cả khách chưa mua:

```sql
SELECT c.name,
       COUNT(*)    AS sai,
       COUNT(o.id) AS dung
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'paid'
GROUP BY c.id
ORDER BY c.id;
```

```
+------+-----+------+
| name | sai | dung |
+------+-----+------+
| An   |   3 |    3 |
| Bình |   1 |    1 |
| Chi  |   1 |    1 |
| Dũng |   1 |    1 |
| Em   |   1 |    0 |
+------+-----+------+
```

Em không có đơn nào nhưng LEFT JOIN vẫn giữ một dòng cho Em, với mọi cột của `orders` là NULL.
`COUNT(*)` đếm dòng nên ra 1; `COUNT(o.id)` bỏ qua NULL nên ra 0. Quy tắc: sau LEFT JOIN, đếm bằng
`COUNT(cot_khong_null_cua_bang_ben_phai)`, thường là khoá chính của nó.

Bẫy 2: phép tính có NULL bên trong hàm tổng hợp. Doanh thu thuần là tổng tiền trừ giảm giá:

```sql
SELECT SUM(total - discount)              AS sai,    -- 730.00
       SUM(total - COALESCE(discount, 0)) AS dung    -- 1650.00
FROM orders
WHERE status = 'paid';
```

Với đơn không dùng voucher, `discount` là NULL nên `total - discount` là NULL, và `SUM` lặng lẽ bỏ qua
cả đơn đó. Kết quả "sai" chỉ còn đơn 101 (300 - 20 = 280) và 103 (500 - 50 = 450): 730, thay vì 1720 -
70 = 1650. Không có lỗi nào xuất hiện, chỉ là mất hơn một nửa doanh thu trên báo cáo. Quy tắc: cột có thể
NULL nằm trong biểu thức thì bọc `COALESCE` trước khi đưa vào hàm tổng hợp. (Viết `SUM(total) -
SUM(discount)` cũng ra 1650 ở đây, nhưng nếu không đơn nào có voucher thì `SUM(discount)` là NULL và cả
hiệu số thành NULL.)

Những bẫy NULL khác đã gặp trong chương:

- `AVG` chia cho số giá trị khác NULL, không phải số dòng (mục 2.3).
- `SUM`, `AVG`, `MIN`, `MAX` trên tập rỗng ra NULL, không phải 0 (mục 2.6).
- Mọi NULL rơi vào chung một nhóm khi `GROUP BY` (mục 3.5).
- NULL của dữ liệu và NULL của dòng tổng `WITH ROLLUP` trông giống nhau; phân biệt bằng `GROUPING()`
  (mục 6.4).

### 9.2 Nhân dòng (fan-out) khi join rồi mới tổng hợp

[Chương 07](07-join.md) đã cảnh báo: join bảng "một" với bảng "nhiều" thì mỗi dòng bên "một" bị lặp lại
theo số dòng khớp bên "nhiều". Với hàm tổng hợp, sự lặp lại này biến thành con số bị thổi phồng.

Ví dụ: muốn số đơn và doanh thu của từng khách, nhưng tiện tay join luôn `order_items` (có thể để lọc
theo sản phẩm sau này):

```sql
-- SAI
SELECT c.name, COUNT(*) AS so_don, SUM(o.total) AS doanh_thu
FROM customers c
JOIN orders o      ON o.customer_id = c.id
JOIN order_items i ON i.order_id = o.id
WHERE o.status = 'paid'
GROUP BY c.id
ORDER BY c.id;
```

| name | so_don | doanh_thu | Đúng ra phải là | Vì sao |
|---|---|---|---|---|
| An | 4 | 870.00 | 3, 570.00 | Đơn 101 có 2 dòng hàng nên 300 bị cộng 2 lần |
| Bình | 2 | 1000.00 | 1, 500.00 | Đơn 103 có 2 dòng hàng |
| Chi | 3 | 750.00 | 1, 250.00 | Đơn 105 có 3 dòng hàng |
| Dũng | 2 | 800.00 | 1, 400.00 | Đơn 107 có 2 dòng hàng |

Hình dung những gì `GROUP BY` thực sự nhìn thấy cho khách An:

```
Sau JOIN orders + order_items (khách An, đơn paid):

 o.id  o.total  i.product_id          Nhóm của An:
 101   300.00   3   ┐ đơn 101 bị        COUNT(*)     = 4   (lẽ ra 3)
 101   300.00   2   ┘ lặp 2 lần         SUM(o.total) = 300 + 300 + 150 + 120
 102   150.00   4                                    = 870 (lẽ ra 570)
 108   120.00   5
```

Cách phát hiện: so `COUNT(*)` với `COUNT(DISTINCT o.id)` trong cùng nhóm; khác nhau là có nhân dòng. Mỗi
khi query có `SUM`/`COUNT` và có join đi qua một quan hệ một-nhiều, hãy nghi ngờ trước.

Cách sửa: gom phía "nhiều" về mức của phía "một" trước, rồi mới join. Nếu cần cả số món hàng của mỗi
khách:

```sql
SELECT c.name,
       COUNT(*)       AS so_don,
       SUM(o.total)   AS doanh_thu,
       SUM(x.so_mon)  AS so_mon
FROM customers c
JOIN orders o ON o.customer_id = c.id
JOIN (
  SELECT order_id, SUM(qty) AS so_mon
  FROM order_items
  GROUP BY order_id
) x ON x.order_id = o.id
WHERE o.status = 'paid'
GROUP BY c.id
ORDER BY c.id;
-- An   | 3 | 570.00 | 5     (đơn 101: 1 + 2, đơn 102: 1, đơn 108: 1)
-- Bình | 1 | 500.00 | 12
-- Chi  | 1 | 250.00 | 6
-- Dũng | 1 | 400.00 | 12
```

Query con gom `order_items` thành đúng một dòng cho mỗi đơn, nên join với `orders` là một-một và không
còn gì bị lặp. Còn nếu không cần cột nào của `order_items` thì đơn giản nhất là đừng join nó.

⚠️ `DISTINCT` không phải cách sửa. `COUNT(DISTINCT o.id)` cho số đơn đúng, nhưng `SUM(DISTINCT o.total)`
cộng các giá trị tiền khác nhau chứ không phải các đơn khác nhau. Trong dữ liệu mẫu nó tình cờ ra đúng
570 cho An (ba đơn 300, 150, 120 có giá khác nhau); chỉ cần An có hai đơn cùng giá 150 là sai. Một query
"đúng nhờ may mắn" là loại bug khó tìm nhất.

Nhân dòng kép: khi join hai quan hệ một-nhiều độc lập vào cùng một bảng, số dòng bị nhân bằng tích của
hai bên. Ví dụ đếm số đơn và số đánh giá của mỗi khách:

```sql
-- SAI
SELECT c.name,
       COUNT(o.id)  AS so_don,
       SUM(o.total) AS doanh_thu,
       COUNT(r.id)  AS so_danh_gia
FROM customers c
LEFT JOIN orders o  ON o.customer_id = c.id AND o.status = 'paid'
LEFT JOIN reviews r ON r.customer_id = c.id
GROUP BY c.id
ORDER BY c.id;
```

```
+------+--------+-----------+-------------+
| name | so_don | doanh_thu | so_danh_gia |
+------+--------+-----------+-------------+
| An   |      6 |   1140.00 |           6 |
| Bình |      1 |    500.00 |           0 |
| Chi  |      1 |    250.00 |           1 |
| Dũng |      1 |    400.00 |           0 |
| Em   |      0 |      NULL |           0 |
+------+--------+-----------+-------------+
```

An có 3 đơn và 2 đánh giá, nên mỗi đơn ghép với mỗi đánh giá: 3 × 2 = 6 dòng. Mọi con số của An đều
sai (đúng phải là 3 đơn, 570, 2 đánh giá), trong khi các khách khác đúng vì họ có tối đa một dòng ở một
bên. Lỗi kiểu này lọt qua kiểm thử dễ dàng nếu dữ liệu test không có khách nào "nhiều ở cả hai bên".

Cách sửa: gom từng nhánh riêng rồi mới join, mỗi nhánh cho đúng một dòng mỗi khách:

```sql
SELECT c.name,
       COALESCE(o.so_don, 0)      AS so_don,
       COALESCE(o.doanh_thu, 0)   AS doanh_thu,
       COALESCE(r.so_danh_gia, 0) AS so_danh_gia
FROM customers c
LEFT JOIN (
  SELECT customer_id, COUNT(*) AS so_don, SUM(total) AS doanh_thu
  FROM orders
  WHERE status = 'paid'
  GROUP BY customer_id
) o ON o.customer_id = c.id
LEFT JOIN (
  SELECT customer_id, COUNT(*) AS so_danh_gia
  FROM reviews
  GROUP BY customer_id
) r ON r.customer_id = c.id
ORDER BY c.id;
```

```
+------+--------+-----------+-------------+
| name | so_don | doanh_thu | so_danh_gia |
+------+--------+-----------+-------------+
| An   |      3 |    570.00 |           2 |
| Bình |      1 |    500.00 |           0 |
| Chi  |      1 |    250.00 |           1 |
| Dũng |      1 |    400.00 |           0 |
| Em   |      0 |      0.00 |           0 |
+------+--------+-----------+-------------+
```

Một cách khác là subquery vô hướng cho từng con số ngay trong `SELECT`, ví dụ `(SELECT COUNT(*) FROM
reviews r WHERE r.customer_id = c.id) AS so_danh_gia`. Đây cũng là cách `withCount` của Laravel sinh SQL
(mục 11). Về hiệu năng của hai cách, xem [chương 09](09-subquery-cte-union.md) và
[chương 12](12-explain-toi-uu-query.md).

### 9.3 Chia cho 0

Giá trị trung bình mỗi đơn của từng khách, tính bằng tổng chia số đơn:

```sql
SELECT c.name,
       COUNT(o.id)                             AS so_don,
       COALESCE(SUM(o.total), 0)               AS doanh_thu,
       COALESCE(SUM(o.total), 0) / COUNT(o.id) AS aov
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'paid'
GROUP BY c.id
ORDER BY c.id;
```

```
+------+--------+-----------+------------+
| name | so_don | doanh_thu | aov        |
+------+--------+-----------+------------+
| An   |      3 |    570.00 | 190.000000 |
| Bình |      1 |    500.00 | 500.000000 |
| Chi  |      1 |    250.00 | 250.000000 |
| Dũng |      1 |    400.00 | 400.000000 |
| Em   |      0 |      0.00 |       NULL |
+------+--------+-----------+------------+
```

Em có 0 đơn nên phép tính là 0 / 0. MySQL xử lý chia cho 0 như sau (theo tài liệu về SQL mode):

- Trong `SELECT`, chia cho 0 trả về NULL. Khi `ERROR_FOR_DIVISION_BY_ZERO` bật (mặc định), MySQL sinh
  thêm warning, client báo "5 rows in set, 1 warning" và `SHOW WARNINGS` cho thấy
  `Warning | 1365 | Division by 0` (output minh hoạ). Code ứng dụng gần như không bao giờ đọc warning,
  nên trên thực tế bạn chỉ thấy một ô NULL.
- Trong câu thay đổi dữ liệu (`INSERT`, `UPDATE`), khi chế độ này và strict mode cùng bật (mặc định),
  chia cho 0 là lỗi, trừ khi dùng `INSERT IGNORE`/`UPDATE IGNORE`. Hệ quả bất ngờ: câu `SELECT` báo cáo
  chạy được, nhưng đem nó vào `INSERT INTO bang_tong_hop SELECT ...` để lưu kết quả thì báo lỗi.
- Tài liệu cũng ghi `ERROR_FOR_DIVISION_BY_ZERO` đã bị đánh dấu deprecated và dự kiến sẽ được gộp vào
  strict mode ở bản sau.

PostgreSQL nghiêm khắc hơn: chia cho 0 là lỗi `division by zero` và cả câu query thất bại, kể cả khi chỉ
một dòng trong hàng triệu dòng có mẫu số bằng 0.

Cách viết đúng ở cả hai database là nói rõ ý định:

```sql
SELECT c.name,
       COALESCE(SUM(o.total), 0) / NULLIF(COUNT(o.id), 0) AS aov,      -- Em: NULL, không warning
       AVG(o.total)                                       AS aov_avg   -- Em: NULL
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'paid'
GROUP BY c.id
ORDER BY c.id;
```

- `NULLIF(x, 0)` trả NULL khi `x` bằng 0 ([chương 06](06-ham-bieu-thuc-null.md)), và chia cho NULL
  thì ra NULL, không phải "chia cho 0".
- Với trung bình, dùng thẳng `AVG`: nó tự chia cho số giá trị khác NULL và trả NULL khi không có giá
  trị nào, không bao giờ chia cho 0.
- Sau đó quyết định hiển thị gì cho NULL: AOV của khách chưa mua không phải là 0 đồng, nó là "không
  có". Hiển thị "-" ở giao diện thường đúng hơn ép thành 0.

Trong một nhóm, `COUNT(*)` luôn ít nhất là 1, nên mẫu số dễ bằng 0 nhất là các con số có điều kiện:
`COUNT(o.id)` sau LEFT JOIN, `SUM(status = 'paid')`, doanh thu kỳ trước khi tính tăng trưởng. Gặp phép
chia nào có mẫu số như vậy, bọc `NULLIF` ngay từ đầu.

⚠️ Một khác biệt nữa giữa hai database: MySQL `7 / 2` ra `3.5000` (phép `/` luôn cho số thập phân; chia
lấy phần nguyên thì dùng `DIV`), còn PostgreSQL chia hai số nguyên thì ra số nguyên, `7 / 2` là `3`. Ở
PostgreSQL, `count(*) FILTER (WHERE status = 'cancelled') / count(*)` gần như luôn ra 0 vì `count` trả
`bigint`. Phải ép kiểu một vế, ví dụ `count(...)::numeric / count(*)`, hoặc nhân `100.0` trước.

---

## 10. Bên trong: MySQL gom nhóm như thế nào

Phần này chỉ để bạn có hình dung đúng; cách thiết kế index và đọc `EXPLAIN` được dạy kỹ ở
[chương 11](11-index.md) và [chương 12](12-explain-toi-uu-query.md).

Để gom nhóm, database cần đặt các dòng cùng nhóm "cạnh nhau" hoặc ít nhất là tìm được nhóm của mỗi dòng
thật nhanh. Tài liệu MySQL mô tả hai hướng:

1. Dùng bảng tạm (*internal temporary table*). Theo tài liệu, đây là cách tổng quát nhất: quét các dòng,
   đưa vào một bảng tạm sao cho các dòng cùng nhóm nằm liền nhau, rồi dùng bảng tạm đó để xác định nhóm
   và tính hàm tổng hợp. `EXPLAIN` khi đó có `Using temporary` ở cột `Extra`. Bảng tạm nằm trong bộ nhớ
   (engine mặc định là `TempTable`); khi vượt giới hạn `tmp_table_size` (mặc định 16 MiB), MySQL tự
   chuyển nó thành bảng tạm InnoDB trên đĩa, chậm hơn nhiều. Tài liệu cũng liệt kê việc tính `GROUP_CONCAT` và
   `COUNT(DISTINCT)` trong số các trường hợp MySQL có thể dùng bảng tạm.
2. Dùng index. Index B+tree lưu khoá đã sắp xếp, nên đọc theo index thì các dòng cùng nhóm tự nhiên đi
   liền nhau, và MySQL có thể tính hàm tổng hợp khi đọc lướt qua, không cần bảng tạm. Điều kiện quan
   trọng nhất: mọi cột `GROUP BY` thuộc cùng một index và index lưu khoá có thứ tự. Có hai kiểu:
   - *Loose Index Scan*: chỉ đọc một phần nhỏ các khoá, nhảy từ nhóm này sang nhóm kia. Dùng được khi
     query chỉ trên một bảng, `GROUP BY` là tiền tố bên trái (*leftmost prefix*) của index, hàm tổng hợp
     chỉ có `MIN()`/`MAX()` trên cùng một cột và cột đó đứng ngay sau các cột `GROUP BY` trong index (cùng
     vài điều kiện khác). `EXPLAIN` ghi `Using index for group-by`.
   - *Tight Index Scan*: không đủ điều kiện cho loose scan thì vẫn có thể đọc hết các khoá trong khoảng
     cần thiết theo thứ tự index và gom nhóm khi đọc, tránh được bảng tạm.

Hình dung loose index scan cho `SELECT customer_id, MAX(created_at) FROM orders GROUP BY customer_id`
khi có index `(customer_id, created_at)`:

```
Index (customer_id, created_at), các khoá đã sắp xếp:

 (1, 01-05 09:15) (1, 01-05 14:00) (1, 03-01 07:00) | (2, 01-31 20:30) (2, 02-02 10:00) | (3, ...) ...
                                   ^^^^^^^^^^^^^^^^                    ^^^^^^^^^^^^^^^^
                                   MAX của khách 1                     MAX của khách 2

Loose index scan: với mỗi customer_id, nhảy thẳng tới khoá cuối của nhóm,
bỏ qua các khoá ở giữa. Nhóm càng lớn, phần bỏ qua càng nhiều.
```

```sql
CREATE INDEX idx_customer_created ON orders (customer_id, created_at);
EXPLAIN SELECT customer_id, MAX(created_at) FROM orders GROUP BY customer_id;
-- Extra: Using index for group-by        (output minh hoạ; với bảng chỉ 8 dòng,
--                                          optimizer có thể chọn cách khác vì quét hết còn rẻ hơn)
```

Vài hệ quả thực tế:

- `WHERE` loại bớt dòng trước khi gom, nên lọc càng sớm càng ít việc cho bước gom nhóm.
- Báo cáo gom hàng triệu dòng mỗi lần chạy thì tối ưu thế nào cũng tốn. Khi báo cáo chạy thường xuyên
  trên dữ liệu lớn, người ta lưu sẵn kết quả đã gom (ví dụ bảng doanh thu theo ngày, cập nhật định kỳ)
  rồi báo cáo đọc từ bảng đó, thay vì gom lại từ dữ liệu gốc mỗi lần.
- Không có index nào giúp `COUNT(*)` của cả bảng lớn thành tức thì, vì InnoDB không lưu sẵn số dòng
  (mục 2.2).

---

## 11. Từ phía ứng dụng: PHP và Laravel

Phần này chỉ nêu những điểm liên quan trực tiếp đến gom nhóm; làm việc với database từ ứng dụng được
bàn đầy đủ ở [chương 19](19-database-tu-ung-dung.md). Các đoạn code dưới đây là trích đoạn, chạy bên
trong một project Laravel đã cấu hình kết nối MySQL.

Query builder có đủ các mảnh ghép:

```php
use Illuminate\Support\Facades\DB;

$rows = DB::table('orders')
    ->select('customer_id')
    ->selectRaw('COUNT(*) AS so_don, SUM(total) AS doanh_thu')
    ->where('status', 'paid')
    ->groupBy('customer_id')
    ->havingRaw('SUM(total) > ?', [450])
    ->orderByDesc('doanh_thu')
    ->get();
// SQL tương ứng (minh hoạ):
// select `customer_id`, COUNT(*) AS so_don, SUM(total) AS doanh_thu from `orders`
// where `status` = ? group by `customer_id` having SUM(total) > ? order by `doanh_thu` desc
```

Những điểm cần biết:

- Laravel có `->having('doanh_thu', '>', 450)`, nhưng tham chiếu alias trong `HAVING` chỉ chạy trên
  MySQL (mục 4.5). `havingRaw` với biểu thức đầy đủ chạy được ở mọi nơi; luôn truyền giá trị qua tham số
  `?`, không nối chuỗi.
- Các hàm tổng hợp nhanh: `->count()`, `->sum('total')`, `->avg('total')`, `->min(...)`, `->max(...)`.
  Theo mã nguồn Laravel 13, `sum()` trả `0` khi SQL trả NULL (không có dòng nào), còn `avg()`, `min()`,
  `max()` trả `null`. Giá trị `DECIMAL` từ MySQL về PHP qua PDO là chuỗi, ví dụ `"570.00"`; đừng ép sang
  `float` cho tiền (xem [chương 03](03-kieu-du-lieu.md)).
- ⚠️ `DB::table('orders')->groupBy('customer_id')->count()` không trả về số nhóm. Laravel sinh
  `select count(*) as aggregate from orders group by customer_id`, nhận về bốn dòng (một dòng mỗi khách),
  rồi chỉ lấy giá trị của dòng đầu tiên: số đơn của một khách nào đó. Muốn đếm số khách có đơn, viết
  `DB::table('orders')->distinct()->count('customer_id')`, sinh ra `COUNT(DISTINCT customer_id)`.
  (Khi query có `having`, Laravel bọc query thành subquery rồi mới đếm; phân trang `paginate()` cũng có
  xử lý riêng cho query có `groupBy`.)
- ⚠️ `Order::all()->groupBy('customer_id')` là `groupBy` của `Collection`: kéo toàn bộ bảng về PHP rồi
  chia nhóm trong bộ nhớ (mục 1.1). Chỉ dùng cho tập dữ liệu nhỏ đã nằm sẵn trong bộ nhớ.

Eloquent có cách đếm và cộng theo quan hệ mà không bị nhân dòng (mục 9.2):

```php
// Giả sử model Customer có quan hệ orders() kiểu hasMany
$customers = Customer::withCount('orders')
    ->withSum('orders', 'total')
    ->get();

foreach ($customers as $c) {
    echo $c->name, ': ', $c->orders_count, ' đơn, ', $c->orders_sum_total ?? 0, "\n";
}
```

`withCount` và `withSum` thêm vào câu `SELECT` một subquery tương quan cho mỗi con số, đặt tên theo mẫu
`{quan_hệ}_count` và `{quan_hệ}_{hàm}_{cột}`. Mỗi con số được tính riêng nên không có chuyện nhân dòng
kép. Lưu ý `orders_sum_total` của khách chưa có đơn là `null` (tổng của tập rỗng, mục 2.6), vì vậy mới
có `?? 0` ở trên.

Cuối cùng, nhắc lại mục 5.5: giữ `'strict' => true` trong `config/database.php`. Lỗi
`only_full_group_by` là tín hiệu query đang hỏi một câu không có câu trả lời, hãy sửa query thay vì tắt
tín hiệu.

---

## 12. Tóm tắt khác biệt MySQL 8.4 và PostgreSQL

| Điểm | MySQL 8.4 | PostgreSQL |
|---|---|---|
| Cột không gom nhóm trong `SELECT` | Bị chặn bởi `ONLY_FULL_GROUP_BY` (bật mặc định, tắt được) | Luôn bị chặn |
| Phụ thuộc hàm được nhận ra | Qua khoá chính, `UNIQUE NOT NULL`, đẳng thức trong `WHERE`/`ON` | Chỉ qua khoá chính của bảng chứa cột |
| Lấy giá trị bất kỳ | `ANY_VALUE()` | `any_value()` từ bản 16 |
| Alias trong `HAVING` | Được (mở rộng của MySQL) | Không |
| Alias, số thứ tự cột trong `GROUP BY` | Được (số thứ tự là deprecated) | Được |
| `COUNT(DISTINCT a, b)` | Được | Không |
| Nối chuỗi trong nhóm | `GROUP_CONCAT`, giới hạn `group_concat_max_len` (1024 byte) | `string_agg`, `array_agg` |
| Aggregate có điều kiện | `SUM(CASE ...)`, `SUM(dieu_kien)` | `FILTER (WHERE ...)`, hoặc `CASE` |
| Tổng phụ | `WITH ROLLUP`, `GROUP BY ROLLUP (...)`, `GROUPING()` | `ROLLUP`, `CUBE`, `GROUPING SETS`, `GROUPING()` |
| Chia cho 0 trong `SELECT` | NULL kèm warning | Lỗi, query thất bại |
| Số nguyên chia số nguyên | Ra số thập phân (`7 / 2` = 3.5000) | Ra số nguyên (`7 / 2` = 3) |
| Trung vị, percentile | Không có hàm sẵn | `percentile_cont`, `percentile_disc` |
| Lấy cả các dòng đồng hạng khi cắt top N | Không có cú pháp riêng (dùng window function) | `FETCH FIRST n ROWS WITH TIES` |

---

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| `COUNT(*)` sau LEFT JOIN, khách chưa có đơn được đếm là 1 | LEFT JOIN vẫn giữ một dòng toàn NULL cho khách đó | `COUNT(cot_cua_bang_ben_phai)`, thường là khoá chính (9.1) |
| `COUNT(status = 'paid')` để đếm có điều kiện | So sánh trả 0 hoặc 1, cả hai đều khác NULL nên mọi dòng được đếm | `SUM(status = 'paid')` hoặc `COUNT(CASE WHEN ... THEN 1 END)` (7.1) |
| `SUM(total - discount)` khi `discount` có NULL | Dòng có NULL làm cả biểu thức NULL và bị bỏ qua | `SUM(total - COALESCE(discount, 0))` (9.1) |
| Báo cáo hiện NULL thay vì 0 | `SUM` của tập rỗng hoặc toàn NULL là NULL | `COALESCE(SUM(x), 0)` (2.6) |
| `AVG(col)` khi `col` có NULL mà muốn "trung bình mỗi dòng" | `AVG` chia cho số giá trị khác NULL | Xác định câu hỏi; dùng `AVG(COALESCE(col, 0))` nếu NULL nghĩa là 0 (2.3) |
| Join một-nhiều rồi `SUM` cột của bảng bên "một" | Mỗi dòng bên "một" lặp lại theo số dòng khớp (fan-out) | Gom phía "nhiều" trước rồi mới join; hoặc subquery vô hướng (9.2) |
| Dùng `SUM(DISTINCT ...)` để "chữa" fan-out | Gộp các giá trị tiền bằng nhau của những đơn khác nhau | Sửa cấu trúc query như trên (9.2) |
| `WHERE SUM(total) > 450` | `WHERE` chạy trước khi có nhóm; lỗi 1111 | Điều kiện có hàm tổng hợp đặt ở `HAVING` (4.2) |
| Điều kiện trên dòng đặt ở `HAVING` | Gom nhiều dữ liệu hơn cần, khó dùng index | Đặt ở `WHERE` (4.4) |
| `HAVING alias > x` rồi mang sang PostgreSQL | Alias trong `HAVING` là mở rộng của MySQL | Viết lại biểu thức trong `HAVING` (4.5) |
| Tắt `ONLY_FULL_GROUP_BY`, hoặc `'strict' => false` trong Laravel | Giá trị không tất định; Laravel còn tắt luôn strict mode | Sửa query: thêm vào `GROUP BY`, dùng hàm tổng hợp, `ANY_VALUE` khi có lý do (5.4, 5.5) |
| `GROUP BY customer_id` kèm `MAX(created_at)` và `id` để lấy đơn mới nhất | `id` không gắn với dòng có `MAX` | Join lại với kết quả `MAX`, hoặc `ROW_NUMBER()` (5.6) |
| Dựa vào thứ tự kết quả của `GROUP BY` | Từ MySQL 8.0 không còn sắp xếp ngầm | Luôn viết `ORDER BY` (3.8) |
| `GROUP BY MONTH(created_at)` | Gộp cùng tháng của các năm khác nhau | Gom theo năm và tháng (8.2) |
| `created_at BETWEEN '2026-01-01' AND '2026-03-31'` | Bỏ sót mọi thời điểm sau 00:00 ngày cuối | Khoảng nửa mở `>= đầu AND < đầu_kỳ_sau` (8.1) |
| Báo cáo theo ngày trên dữ liệu lưu UTC | Ranh giới ngày, tháng lệch so với giờ địa phương | `CONVERT_TZ`, hoặc đổi mốc lọc sang UTC (8.4) |
| Chia cho một `COUNT`/`SUM` có thể bằng 0 | MySQL trả NULL kèm warning, `INSERT ... SELECT` lỗi; PostgreSQL lỗi | `NULLIF(mau_so, 0)`, hoặc dùng `AVG` (9.3) |
| `ORDER BY ... LIMIT N` khi có đồng hạng | Dòng nào được lấy không xác định | Thêm cột phá hoà, hoặc `RANK()` (8.5) |
| Chuỗi `GROUP_CONCAT` dài bị cụt | Giới hạn `group_concat_max_len` 1024 byte, chỉ có warning | Tăng biến cho session, hoặc dùng `JSON_ARRAYAGG` (2.5) |
| `->groupBy(...)->count()` trong Laravel | Trả số dòng của nhóm đầu tiên, không phải số nhóm | `->distinct()->count('cot')` (11) |

---

## Tóm tắt chương

- Hàm tổng hợp biến nhiều dòng thành một giá trị. Trừ `COUNT(*)`, mọi hàm tổng hợp bỏ qua NULL; trên
  tập rỗng, `COUNT` ra 0 còn `SUM`, `AVG`, `MIN`, `MAX`, `GROUP_CONCAT` ra NULL.
- `COUNT(*)` đếm dòng, `COUNT(col)` đếm giá trị khác NULL, `COUNT(DISTINCT col)` đếm giá trị khác nhau.
  `AVG` chia cho số giá trị khác NULL.
- `GROUP BY` chia các dòng thành nhóm theo tổ hợp giá trị của các cột hoặc biểu thức; mỗi nhóm ra một
  dòng. NULL tạo thành một nhóm; collation quyết định hai chuỗi có cùng nhóm không. Không có
  `GROUP BY` thì luôn ra đúng một dòng, có `GROUP BY` mà không có dữ liệu thì ra tập rỗng.
- Thứ tự logic: `FROM` → `WHERE` → `GROUP BY` → hàm tổng hợp → `HAVING` → `SELECT` → `ORDER BY` →
  `LIMIT`. `WHERE` lọc dòng và thay đổi con số; `HAVING` lọc nhóm. Điều kiện không có hàm tổng hợp đặt ở
  `WHERE`.
- `ONLY_FULL_GROUP_BY` (bật mặc định) chặn cột không gom nhóm, không tổng hợp và không phụ thuộc hàm vào
  cột gom nhóm. Sửa query, đừng tắt chế độ; `ANY_VALUE()` chỉ dùng khi chắc mọi giá trị trong nhóm như
  nhau.
- `WITH ROLLUP` thêm dòng tổng phụ và tổng cộng theo thứ bậc các cột; `GROUPING()` phân biệt NULL của
  dòng tổng với NULL của dữ liệu và dùng được trong `SELECT`, `HAVING`, `ORDER BY`.
- Aggregate có điều kiện (`SUM(CASE ...)`, `COUNT(CASE ...)`) cho nhiều con số trên một dòng và dùng để
  xoay bảng; PostgreSQL có `FILTER`.
- Báo cáo theo thời gian: lọc bằng khoảng nửa mở trên cột gốc, gom theo năm và tháng, lấp ngày trống
  bằng bảng lịch và LEFT JOIN, chú ý múi giờ. Top N cần cột phá hoà.
- Ba bẫy lớn đều cho kết quả sai mà không báo lỗi: NULL (`COUNT(*)` sau LEFT JOIN, biểu thức có NULL),
  nhân dòng khi join một-nhiều rồi tổng hợp (gom trước rồi mới join), chia cho 0 (`NULLIF`).

---

## Câu hỏi tự kiểm tra

1. Trên bảng `orders` mẫu, không chạy query, hãy đoán kết quả của `COUNT(*)`, `COUNT(discount)`,
   `COUNT(DISTINCT discount)` và `AVG(discount)`, rồi chạy để kiểm tra. Vì sao các con số khác nhau?
2. Vì sao `SELECT COUNT(*) FROM orders WHERE status = 'refunded'` trả về một dòng, nhưng thêm
   `GROUP BY status` thì trả về tập rỗng? Điều này ảnh hưởng gì tới code PHP đọc kết quả? (mục 2.6, 3.7)
3. Dựa vào thứ tự thực thi logic, giải thích vì sao `WHERE` không dùng được `SUM(...)` còn `HAVING` thì
   được, và vì sao chuẩn SQL không cho `HAVING` dùng alias đặt trong `SELECT`.
4. Cho `GROUP BY customer_id`, chọn `HAVING SUM(total) >= 300` hay `WHERE total >= 300` cho hai yêu cầu:
   "khách lớn" và "đơn lớn". Vì sao con số của khách An khác nhau giữa hai cách? (mục 4.3)
5. Phụ thuộc hàm là gì? Vì sao `GROUP BY c.id` cho phép chọn `c.name`, nhưng `GROUP BY c.name` (giả sử
   tên không unique) lại không cho phép chọn `c.city`? Khi nào dùng `ANY_VALUE` là hợp lý, khi nào là
   che giấu bug? (mục 5.3, 5.4)
6. Trong kết quả có `WITH ROLLUP`, làm thế nào phân biệt một NULL là dữ liệu thật hay là dòng tổng? Vì
   sao không thể dùng `WHERE` để bỏ các dòng tổng? (mục 6.4, 6.5)
7. Một query join `customers`, `orders`, `order_items` rồi `SUM(o.total)`. Làm sao phát hiện nó bị nhân
   dòng, và nêu hai cách sửa. Vì sao `SUM(DISTINCT o.total)` không phải cách sửa đúng dù đôi khi cho kết
   quả đúng? (mục 9.2)
8. Cùng phép chia cho 0, MySQL và PostgreSQL phản ứng thế nào? Vì sao một câu `SELECT` chạy được nhưng
   đưa vào `INSERT ... SELECT` lại báo lỗi? (mục 9.3)
9. Bạn và bộ phận kế toán cùng tính doanh thu tháng 1 trên một bảng dữ liệu nhưng ra hai con số khác
   nhau. Hãy nêu ít nhất ba nguyên nhân có thể có từ những gì đã học trong chương.
10. Vì sao `ORDER BY so_luong DESC LIMIT 3` có thể cho kết quả khác nhau giữa hai lần chạy dù dữ liệu
    không đổi về giá trị? (mục 8.5)

---

## Bài tập

Các bài dùng dữ liệu mẫu ở mục 1.2. Bài 1 đến 3 chạy trong client `mysql`; bài 4 chạy bằng
`php bai4.php`, không cần MySQL.

**Bài 1. Báo cáo danh mục theo tháng có tổng phụ.** Viết một query trả về doanh thu (đơn `paid`, tính từ
`qty * unit_price`) theo danh mục sản phẩm và theo tháng, có dòng tổng cho mỗi danh mục và dòng tổng
cộng cuối bảng. Dòng tổng phải có nhãn dễ đọc ("Cả năm", "Mọi danh mục") thay vì NULL, và thứ tự các
dòng phải được bảo đảm bằng `ORDER BY`. Tự kiểm tra: tổng cộng phải bằng 1720.00, tổng của danh mục
Điện tử phải bằng 1050.00.

**Bài 2. Bảng thông tin khách hàng.** Viết một query trả về đúng một dòng cho mỗi khách, kể cả Em, gồm:
tên, số đơn đã thanh toán, doanh thu, giá trị trung bình mỗi đơn (NULL nếu chưa mua), số đánh giá, điểm
đánh giá trung bình, thời điểm mua gần nhất. Query không được nhân dòng và không được sinh warning chia
cho 0. Tự kiểm tra với An: 3 đơn, 570.00, trung bình 190 mỗi đơn, 2 đánh giá, điểm trung bình 4.5, mua
gần nhất lúc 2026-03-01 07:00:00. Sau đó thêm một đánh giá cho An và một đơn `paid` mới cho Bình, chạy lại
và tự kiểm tra rằng chỉ những con số liên quan thay đổi.

**Bài 3. Kiểm tra toàn vẹn dữ liệu bằng gom nhóm.** Chạy
`UPDATE orders SET total = 260.00 WHERE id = 105;` để cố ý làm lệch dữ liệu. Sau đó viết các query:
(a) tìm những đơn có `total` khác tổng `qty * unit_price` của các dòng hàng (in cả hai giá trị);
(b) tìm sản phẩm chưa từng được bán trong đơn `paid` nào, và sản phẩm có tổng số lượng bán dưới 3;
(c) tìm khách có từ hai đơn trở lên trong cùng một tháng. Chạy lại `UPDATE` để trả `total` về 250.00 khi
xong.

**Bài 4. Tự cài GROUP BY bằng PHP.** Viết file `bai4.php` (`declare(strict_types=1);`, khai báo kiểu đầy
đủ) chứa dữ liệu bảng `orders` dưới dạng mảng, và một hàm
`groupBy(array $rows, callable $key, array $aggregates): array` nhận các "hàm tổng hợp" dạng closure.
Cài các aggregate `count_star`, `count_col`, `sum`, `avg`, `max` với đúng ngữ nghĩa NULL của SQL (bỏ qua
NULL, tập rỗng trả `null` trừ count). Dùng nó tái tạo kết quả các query ở mục 2.3 (`AVG(discount)` phải ra
26.67 khi làm tròn hai chữ số) và mục 8.2, rồi so với kết quả MySQL. Gợi ý thêm cho người muốn thử thách:
cài thêm tuỳ chọn ROLLUP một cấp.

---

## Đọc thêm

MySQL 8.4 Reference Manual:

- [Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html):
  từng hàm, cách xử lý NULL, kiểu trả về, `GROUP_CONCAT`.
- [GROUP BY Modifiers](https://dev.mysql.com/doc/refman/8.4/en/group-by-modifiers.html): `WITH ROLLUP`,
  `GROUPING()`, các lưu ý về `ORDER BY`, `LIMIT`.
- [MySQL Handling of GROUP BY](https://dev.mysql.com/doc/refman/8.4/en/group-by-handling.html) và
  [Detection of Functional Dependence](https://dev.mysql.com/doc/refman/8.4/en/group-by-functional-dependence.html):
  `ONLY_FULL_GROUP_BY`, các mở rộng của MySQL, phụ thuộc hàm.
- [Miscellaneous Functions](https://dev.mysql.com/doc/refman/8.4/en/miscellaneous-functions.html):
  `ANY_VALUE()`, `GROUPING()`.
- [Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html): sql_mode mặc định,
  `ONLY_FULL_GROUP_BY`, `ERROR_FOR_DIVISION_BY_ZERO`.
- [SELECT Statement](https://dev.mysql.com/doc/refman/8.4/en/select.html): cú pháp `GROUP BY`,
  `HAVING`.
- [Arithmetic Operators](https://dev.mysql.com/doc/refman/8.4/en/arithmetic-functions.html): phép `/`,
  `DIV`, chia cho 0.
- [GROUP BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/group-by-optimization.html) và
  [Internal Temporary Table Use](https://dev.mysql.com/doc/refman/8.4/en/internal-temporary-tables.html).
- [MySQL Server Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html) và
  [Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html)
  (`CONVERT_TZ`, `DATE_FORMAT`).
- [ORDER BY Optimization, bản 8.0](https://dev.mysql.com/doc/refman/8.0/en/order-by-optimization.html)
  và [Release notes MySQL 8.0.13](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-13.html):
  `GROUP BY` thôi sắp xếp ngầm, bỏ `ASC`/`DESC` trong `GROUP BY`.

PostgreSQL 18:

- [Aggregate Functions](https://www.postgresql.org/docs/18/functions-aggregate.html): `string_agg`,
  `any_value`, `percentile_cont`, kiểu trả về của `sum`/`avg`.
- [Aggregate Expressions](https://www.postgresql.org/docs/18/sql-expressions.html#SYNTAX-AGGREGATES):
  `FILTER`, `ORDER BY` trong hàm tổng hợp.
- [SELECT](https://www.postgresql.org/docs/18/sql-select.html): `GROUP BY`, `HAVING`, phụ thuộc hàm,
  `FETCH FIRST ... WITH TIES`.

Laravel 13:

- [Query Builder: Aggregates, Grouping, Raw Methods](https://laravel.com/docs/13.x/queries).
- [Eloquent: Aggregating Related Models](https://laravel.com/docs/13.x/eloquent-relationships#aggregating-related-models).
- Mã nguồn [`MySqlConnector.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Connectors/MySqlConnector.php)
  (cách `strict` quyết định `sql_mode`) và
  [`Query/Builder.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Query/Builder.php)
  (`count`, `sum`, `aggregate`).
