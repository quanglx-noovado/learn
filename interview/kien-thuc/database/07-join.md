# Chương 07. JOIN: kết hợp nhiều bảng

> [← Mục lục](README.md) · [← Chương 06: Biểu thức, hàm và NULL](06-ham-bieu-thuc-null.md) · [Chương 08: Gom nhóm và hàm tổng hợp →](08-group-by-aggregate.md)

**Bạn sẽ học được:**

- Vì sao dữ liệu nằm rải ở nhiều bảng, và JOIN ghép chúng lại theo mô hình "ghép mọi cặp rồi lọc".
- Các kiểu join: INNER, LEFT, RIGHT, CROSS, self join, và cách giả lập FULL OUTER JOIN trên MySQL.
- Khác nhau giữa `ON` và `USING`, và vì sao cùng một điều kiện đặt ở `ON` hay ở `WHERE` lại cho kết
  quả khác nhau khi dùng LEFT JOIN.
- Semi-join ("có ít nhất một") và anti-join ("không có cái nào"): viết bằng JOIN, `EXISTS`, `IN`, và
  bẫy `NOT IN` khi gặp NULL.
- Fan-out: vì sao join qua quan hệ 1-n rồi `SUM` ra số sai mà không hề báo lỗi, và cách sửa.
- Đọc và viết câu join nhiều bảng, nhận ra chỗ một LEFT JOIN bị "vô hiệu hoá" một cách âm thầm.

**Cần biết trước:** [Chương 02](02-mo-hinh-quan-he-thiet-ke.md) (khoá chính, khoá ngoại, quan hệ
1-n và n-n), [Chương 05](05-select-co-ban.md) (`SELECT`, `WHERE`, `ORDER BY`),
[Chương 06](06-ham-bieu-thuc-null.md) (NULL và logic ba giá trị TRUE/FALSE/UNKNOWN).

## 1. Vì sao cần JOIN

### 1.1 Dữ liệu nằm rải ở nhiều bảng

Ở [chương 02](02-mo-hinh-quan-he-thiet-ke.md) ta tách dữ liệu ra nhiều bảng để mỗi sự thật chỉ lưu
ở một chỗ: tên khách nằm trong bảng `customers`, còn mỗi đơn hàng trong bảng `orders` chỉ giữ cột
`customer_id` trỏ tới khách. Nhờ vậy khi khách đổi tên, ta sửa đúng một dòng.

Cái giá phải trả: hầu hết câu hỏi thực tế cần dữ liệu từ nhiều bảng cùng lúc.

- "Liệt kê đơn hàng kèm tên khách" cần `orders` và `customers`.
- "Khách nào chưa mua gì?" cần biết khách nào *không có* dòng tương ứng trong `orders`.
- "Mỗi sản phẩm bán được bao nhiêu cái?" cần `order_items` và `products`.

*JOIN* là phép toán đặt trong mệnh đề `FROM`, ghép các dòng của hai bảng thành các dòng kết quả theo
một điều kiện bạn đưa ra. Điều kiện thường gặp nhất là "khoá ngoại bên này bằng khoá chính bên kia",
ví dụ `orders.customer_id = customers.id`. Kết quả của một phép JOIN lại là một tập dòng có cột,
giống như một bảng, nên có thể join tiếp với bảng thứ ba, lọc bằng `WHERE`, sắp xếp bằng `ORDER BY`
như với một bảng bình thường.

Không dùng JOIN, bạn có thể chạy hai câu query rồi tự ghép trong code ứng dụng. Đôi khi đó là lựa
chọn đúng: eager loading của Laravel (`Order::with('customer')->get()`) làm chính xác như vậy, một query
lấy các đơn, một query lấy các khách có `id` nằm trong danh sách `customer_id` vừa lấy được. Nhưng
với các việc như lọc theo dữ liệu bảng kia, tìm "cái không có", đếm, làm báo cáo, để database ghép
thường gọn hơn và tránh chuyển dữ liệu thừa qua mạng. [Chương 19](19-database-tu-ung-dung.md) bàn
kỹ chuyện chọn cách nào từ phía ứng dụng.

### 1.2 Dữ liệu mẫu dùng cho cả chương

Mọi ví dụ trong chương chạy trên MySQL 8.4. Nếu chưa có MySQL, chạy bằng Docker như
[chương 01](01-database-la-gi.md) (gõ ở terminal máy bạn):

```bash
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi khoảng nửa phút cho server khởi động xong, rồi mở mysql client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Trong mysql client, chạy đoạn sau để tạo dữ liệu (dùng database riêng `ch07` để không đụng bảng của
chương khác):

```sql
CREATE DATABASE IF NOT EXISTS ch07;
USE ch07;

CREATE TABLE customers (
  id   INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  city VARCHAR(50) NULL                  -- NULL: khách chưa khai báo thành phố
);

CREATE TABLE orders (
  id          INT PRIMARY KEY,
  customer_id INT NULL,                  -- NULL: đơn của khách vãng lai, không có tài khoản
  status      VARCHAR(10) NOT NULL,      -- 'paid' hoặc 'pending'
  total       DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (customer_id) REFERENCES customers (id)
);

CREATE TABLE products (
  id    INT PRIMARY KEY,
  name  VARCHAR(50) NOT NULL,
  price DECIMAL(10,2) NOT NULL
);

CREATE TABLE order_items (               -- mỗi dòng là một mặt hàng trong một đơn
  id         INT PRIMARY KEY,
  order_id   INT NOT NULL,
  product_id INT NOT NULL,
  qty        INT NOT NULL,
  price      DECIMAL(10,2) NOT NULL,     -- đơn giá lúc bán
  FOREIGN KEY (order_id)   REFERENCES orders (id),
  FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE payments (                  -- một đơn có thể được trả làm nhiều lần
  id       INT PRIMARY KEY,
  order_id INT NOT NULL,
  amount   DECIMAL(10,2) NOT NULL,
  FOREIGN KEY (order_id) REFERENCES orders (id)
);

INSERT INTO customers VALUES (1, 'An', 'Hà Nội'), (2, 'Bình', NULL), (3, 'Chi', 'Đà Nẵng');
INSERT INTO orders VALUES
  (10, 1, 'paid', 100.00), (11, 1, 'pending', 50.00),
  (12, 2, 'pending', 70.00), (13, NULL, 'paid', 30.00);
INSERT INTO products VALUES (1, 'Bút', 10.00), (2, 'Vở', 20.00), (3, 'Thước', 5.00), (4, 'Balo', 60.00);
INSERT INTO order_items VALUES
  (1, 10, 1, 2, 10.00), (2, 10, 2, 1, 20.00), (3, 10, 4, 1, 60.00),
  (4, 11, 1, 5, 10.00),
  (5, 12, 4, 1, 60.00), (6, 12, 1, 1, 10.00),
  (7, 13, 1, 3, 10.00);
INSERT INTO payments VALUES (1, 10, 60.00), (2, 10, 40.00), (3, 13, 30.00);
```

Nội dung các bảng, để bạn tự tính kết quả bằng tay khi đọc:

```
customers                 orders                                products
+----+------+---------+   +----+-------------+---------+--------+   +----+-------+-------+
| id | name | city    |   | id | customer_id | status  | total  |   | id | name  | price |
+----+------+---------+   +----+-------------+---------+--------+   +----+-------+-------+
|  1 | An   | Hà Nội  |   | 10 |           1 | paid    | 100.00 |   |  1 | Bút   | 10.00 |
|  2 | Bình | NULL    |   | 11 |           1 | pending |  50.00 |   |  2 | Vở    | 20.00 |
|  3 | Chi  | Đà Nẵng |   | 12 |           2 | pending |  70.00 |   |  3 | Thước |  5.00 |
+----+------+---------+   | 13 |        NULL | paid    |  30.00 |   |  4 | Balo  | 60.00 |
                          +----+-------------+---------+--------+   +----+-------+-------+

order_items                                  payments
+----+----------+------------+-----+-------+   +----+----------+--------+
| id | order_id | product_id | qty | price |   | id | order_id | amount |
+----+----------+------------+-----+-------+   +----+----------+--------+
|  1 |       10 |          1 |   2 | 10.00 |   |  1 |       10 |  60.00 |
|  2 |       10 |          2 |   1 | 20.00 |   |  2 |       10 |  40.00 |
|  3 |       10 |          4 |   1 | 60.00 |   |  3 |       13 |  30.00 |
|  4 |       11 |          1 |   5 | 10.00 |   +----+----------+--------+
|  5 |       12 |          4 |   1 | 60.00 |
|  6 |       12 |          1 |   1 | 10.00 |
|  7 |       13 |          1 |   3 | 10.00 |
+----+----------+------------+-----+-------+
```

Dữ liệu được dựng có chủ ý để lộ ra các trường hợp biên. Hãy nhớ mấy điểm này, cả chương sẽ dùng tới:

- An có 2 đơn (10 đã trả, 11 chưa trả), Bình có 1 đơn chưa trả (12), Chi chưa có đơn nào.
- Đơn 13 của khách vãng lai: `customer_id` là NULL.
- Bình chưa khai báo thành phố: `city` là NULL.
- Thước chưa bán được cái nào.
- Đơn 10 có 3 dòng hàng và được trả làm 2 lần (60 + 40). Tổng tiền mỗi đơn khớp với tổng
  `qty * price` các dòng hàng của nó.

### 1.3 Mô hình tư duy: ghép mọi cặp, rồi lọc

Cách dễ nhất để hiểu và dự đoán kết quả của mọi kiểu join là tưởng tượng hai bước:

1. Ghép mỗi dòng bảng trái với mỗi dòng bảng phải. Tập tất cả các cặp này gọi là *tích Descartes*
   (*Cartesian product*): bảng m dòng ghép với bảng n dòng cho m × n cặp.
2. Giữ lại những cặp mà điều kiện `ON` cho ra TRUE.

Ví dụ với câu:

```sql
SELECT c.id, c.name, o.id, o.customer_id
FROM customers c
JOIN orders o ON o.customer_id = c.id;
```

Bước 1: `customers` có 3 dòng, `orders` có 4 dòng, nên có 3 × 4 = 12 cặp. Bước 2: tính điều kiện
`o.customer_id = c.id` cho từng cặp:

| c.id | c.name | o.id | o.customer_id | `o.customer_id = c.id` | Giữ? |
|---|---|---|---|---|---|
| 1 | An | 10 | 1 | TRUE | giữ |
| 1 | An | 11 | 1 | TRUE | giữ |
| 1 | An | 12 | 2 | FALSE | loại |
| 1 | An | 13 | NULL | UNKNOWN | loại |
| 2 | Bình | 10 | 1 | FALSE | loại |
| 2 | Bình | 11 | 1 | FALSE | loại |
| 2 | Bình | 12 | 2 | TRUE | giữ |
| 2 | Bình | 13 | NULL | UNKNOWN | loại |
| 3 | Chi | 10 | 1 | FALSE | loại |
| 3 | Chi | 11 | 1 | FALSE | loại |
| 3 | Chi | 12 | 2 | FALSE | loại |
| 3 | Chi | 13 | NULL | UNKNOWN | loại |

Còn lại 3 cặp: (An, 10), (An, 11), (Bình, 12). Chú ý dòng của đơn 13: `NULL = 1` không ra FALSE mà
ra UNKNOWN (xem [chương 06](06-ham-bieu-thuc-null.md)), và `ON` cũng như `WHERE` chỉ giữ cặp có kết
quả TRUE, nên UNKNOWN bị loại giống FALSE. Hệ quả quan trọng: khi so bằng `=`, giá trị NULL ở cột
join không bao giờ khớp với bất cứ thứ gì, kể cả với một NULL khác. (MySQL có toán tử `<=>` coi hai
NULL là bằng nhau, xem [chương 06](06-ham-bieu-thuc-null.md); join theo khoá thì hầu như không cần
tới nó.)

Các kiểu join khác nhau (INNER, LEFT, RIGHT...) chỉ khác nhau ở chuyện xử lý những dòng không tìm được
cặp nào: bỏ đi, hay giữ lại và điền NULL vào phần thiếu. Các mục sau đi lần lượt từng kiểu.

⚠️ Đây là mô hình *logic* để hiểu kết quả, không phải cách MySQL chạy thật. MySQL không dựng 12 cặp
rồi lọc. Optimizer chọn cách rẻ hơn, ví dụ duyệt từng khách rồi dùng index trên
`orders.customer_id` để nhảy thẳng tới các đơn của khách đó. Dù chạy kiểu nào, kết quả phải đúng
như mô hình logic. Cách MySQL thực thi join (nested loop, hash join) và cách xem bằng `EXPLAIN` nằm
ở [chương 12](12-explain-toi-uu-query.md).

### 1.4 Cú pháp cơ bản, alias và tên cột đầy đủ

```sql
SELECT c.name, o.id AS order_id, o.status, o.total
FROM customers AS c
JOIN orders AS o ON o.customer_id = c.id
ORDER BY o.id;
```

Kết quả mong đợi:

| name | order_id | status | total |
|---|---|---|---|
| An | 10 | paid | 100.00 |
| An | 11 | pending | 50.00 |
| Bình | 12 | pending | 70.00 |

Các thành phần:

- `customers AS c`: đặt *alias* (tên tắt) `c` cho bảng. Từ khoá `AS` có thể bỏ: `customers c`.
  Đã đặt alias thì trong câu đó dùng alias, không dùng tên bảng gốc nữa.
- `ON o.customer_id = c.id`: điều kiện ghép. Thứ tự hai vế không quan trọng, `c.id = o.customer_id`
  cho cùng kết quả.
- `c.name`, `o.id`: tên cột kèm tiền tố bảng (*qualified name*). Bắt buộc khi tên cột có ở cả hai
  bảng. Cả `customers` và `orders` đều có cột `id`, nên viết trống không sẽ lỗi:

```sql
SELECT id FROM customers c JOIN orders o ON o.customer_id = c.id;
-- ERROR 1052 (23000): Column 'id' in field list is ambiguous
```

- `ORDER BY o.id`: không có `ORDER BY` thì thứ tự dòng trả về không được bảo đảm, có thể đổi khi dữ
  liệu hoặc execution plan đổi. Mọi kết quả ghi trong chương này đều đi kèm `ORDER BY` để bạn so khớp.

Thói quen nên có: trong câu có join, ghi tiền tố bảng cho mọi cột, kể cả cột không trùng tên. Câu dễ
đọc hơn (biết ngay cột nào của bảng nào), và không bị vỡ khi sau này bảng kia được thêm một cột trùng
tên.

⚠️ `SELECT *` trong câu join trả về mọi cột của cả hai bảng, theo thứ tự cột bảng trái rồi tới cột
bảng phải, nên có hai cột cùng tên `id`. Trong mysql client bạn thấy đủ cả hai. Nhưng khi PHP lấy
dòng thành mảng kết hợp hoặc object, hai cột cùng tên chỉ còn lại một, vì mảng PHP không thể có hai
key trùng nhau. Tài liệu PDO ghi rõ giá trị nào được giữ lại là *không xác định* (undefined). Ví dụ
dưới chạy bằng SQLite cho tiện, vì vấn đề nằm ở phía PHP chứ không ở database:

```php
<?php
declare(strict_types=1);

$pdo = new PDO('sqlite::memory:');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->exec('CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL)');
$pdo->exec('CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, total REAL NOT NULL)');
$pdo->exec("INSERT INTO customers VALUES (1, 'An')");
$pdo->exec('INSERT INTO orders VALUES (10, 1, 100)');

$sql = 'SELECT * FROM customers c JOIN orders o ON o.customer_id = c.id';

$row = $pdo->query($sql)->fetch(PDO::FETCH_ASSOC);
echo $row['id'], "\n";              // in ra: 10  (id của đơn, không phải id của khách)

$named = $pdo->query($sql)->fetch(PDO::FETCH_NAMED);
echo json_encode($named['id']), "\n"; // in ra: [1,10]  (FETCH_NAMED giữ cả hai, gom thành mảng)

$sql2 = 'SELECT c.id AS customer_id, c.name, o.id AS order_id, o.total
         FROM customers c JOIN orders o ON o.customer_id = c.id';
$row2 = $pdo->query($sql2)->fetch(PDO::FETCH_ASSOC);
echo $row2['customer_id'], ' ', $row2['order_id'], "\n"; // in ra: 1 10
```

Output trên là kết quả chạy thật với PHP 8.5 và pdo_sqlite; với driver khác, đừng dựa vào việc cột nào
"thắng". Cách chữa duy nhất đáng tin: chọn cột cụ thể và đặt alias khi trùng tên, như `$sql2`. Laravel
cũng dính bẫy này: `Customer::join('orders', 'orders.customer_id', '=', 'customers.id')->get()` sinh ra
`select *`, và model `Customer` có thể nhận `id` của đơn hàng. Khi join trong Eloquent, luôn thêm
`->select('customers.*', ...)`.

## 2. INNER JOIN: chỉ giữ các cặp khớp

### 2.1 Định nghĩa và ví dụ

*INNER JOIN* giữ lại đúng những cặp dòng thoả điều kiện `ON`. Dòng nào, ở bảng nào, không tìm được
cặp thì biến mất khỏi kết quả. Đây là kiểu join mặc định: viết `JOIN` trống không nghĩa là
`INNER JOIN`.

```sql
SELECT c.name, o.id AS order_id, o.status, o.total
FROM customers c
INNER JOIN orders o ON o.customer_id = c.id
ORDER BY o.id;
```

Kết quả mong đợi (3 dòng, đúng 3 cặp TRUE ở bảng mục 1.3):

| name | order_id | status | total |
|---|---|---|---|
| An | 10 | paid | 100.00 |
| An | 11 | pending | 50.00 |
| Bình | 12 | pending | 70.00 |

Hình dung các "sợi dây" nối giữa hai bảng. INNER JOIN chỉ giữ những dòng có dây:

```
customers                orders
+-----------+            +---------------------+
| 1 An      |------+---->| 10  customer_id=1   |
|           |      +---->| 11  customer_id=1   |
| 2 Bình    |----------->| 12  customer_id=2   |
| 3 Chi     |  (không có | 13  customer_id=NULL|  (không trỏ tới ai)
+-----------+   dây nào) +---------------------+
```

Hai dòng bị mất, mỗi dòng một lý do:

- Chi: không có đơn nào trỏ tới.
- Đơn 13: `customer_id` là NULL, không khớp với khách nào.

Vì INNER JOIN loại dòng ở cả hai phía, đổi chỗ hai bảng (`FROM orders o JOIN customers c ...`) cho
cùng một tập dòng, chỉ khác thứ tự cột khi bạn `SELECT *`.

### 2.2 Một dòng có thể xuất hiện nhiều lần

An xuất hiện hai lần vì An có hai đơn. Join qua quan hệ 1-n (một khách, nhiều đơn) cho ra số dòng
bằng số dòng phía "nhiều" khớp được, và mỗi dòng phía "một" bị lặp lại cho từng dòng phía "nhiều".

Đây không phải lỗi, mà là đúng định nghĩa. Nó chỉ thành lỗi khi bạn quên mất điều này rồi đem cộng
một cột của phía "một": giả sử `customers` có cột hạn mức tín dụng `credit_limit`, cộng cột đó trên
kết quả trên sẽ cộng hạn mức của An hai lần. Hiện tượng này gọi là *fan-out*, có hẳn
[mục 10](#10-fan-out-join-1-n-rồi-sum-ra-số-sai) dành cho nó.

### 2.3 Kết hợp JOIN với WHERE và ORDER BY

Kết quả của join được lọc, sắp xếp như một bảng bình thường. Ví dụ "các đơn đã thanh toán của khách
ở Hà Nội":

```sql
SELECT c.name, o.id AS order_id, o.total
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid'
  AND c.city = 'Hà Nội'
ORDER BY o.id;
```

Kết quả mong đợi:

| name | order_id | total |
|---|---|---|
| An | 10 | 100.00 |

Về logic, database xử lý theo thứ tự: `FROM` cùng các `JOIN ... ON` tạo ra tập dòng trước, rồi
`WHERE` lọc từng dòng, rồi `SELECT` tính các cột, rồi `ORDER BY` sắp xếp. (Giữa `WHERE` và `SELECT`
còn `GROUP BY`, `HAVING`, học ở [chương 08](08-group-by-aggregate.md).) Thứ tự này là chìa khoá để
hiểu mục 4: `ON` chạy lúc ghép cặp, `WHERE` chạy sau khi đã ghép xong.

### 2.4 Cú pháp dấu phẩy kiểu cũ, và JOIN không có ON

Bạn sẽ gặp cách viết cũ, liệt kê các bảng bằng dấu phẩy rồi đặt điều kiện ghép trong `WHERE`:

```sql
SELECT c.name, o.id AS order_id
FROM customers c, orders o
WHERE o.customer_id = c.id
ORDER BY o.id;
```

Kết quả giống hệt INNER JOIN ở mục 2.1. Dấu phẩy trong `FROM` nghĩa là tích Descartes, và `WHERE`
lọc lại. Tài liệu MySQL ghi rõ: khi không có điều kiện join, `INNER JOIN` và dấu phẩy tương đương về
ngữ nghĩa, cả hai đều tạo tích Descartes.

Nên dùng `JOIN ... ON` thay cho dấu phẩy vì:

- Điều kiện ghép nằm ngay cạnh bảng nó ghép, không lẫn với điều kiện lọc trong `WHERE`.
- Quên điều kiện ghép thì dấu phẩy vẫn chạy và âm thầm trả về m × n dòng (mục 6.3).
- Outer join (LEFT, RIGHT) phải viết bằng cú pháp `LEFT JOIN`/`RIGHT JOIN`; dấu phẩy không diễn
  đạt được.
- Trộn dấu phẩy với `JOIN` dễ dính lỗi do thứ tự ưu tiên (mục 11.5).

Một điểm riêng của MySQL: `JOIN`, `INNER JOIN` và `CROSS JOIN` là ba cách viết tương đương nhau, và
`ON` của chúng là tuỳ chọn. `FROM customers c JOIN orders o` không có `ON` vẫn chạy, cho 12 dòng
tích Descartes. Chuẩn SQL và PostgreSQL thì khác: `INNER JOIN` bắt buộc có điều kiện (`ON`, `USING`
hoặc `NATURAL`), `CROSS JOIN` thì không được có `ON`. Để code mang sang được database khác, hãy viết
`JOIN ... ON` khi có điều kiện ghép, và `CROSS JOIN` khi thật sự muốn tích Descartes.

### 2.5 Điều kiện join không nhất thiết là dấu bằng

`ON` nhận bất kỳ biểu thức điều kiện nào dùng được trong `WHERE`. Join bằng điều kiện không phải dấu
bằng gọi là *non-equi join*. Ví dụ tra phí giao hàng theo khoảng giá trị đơn:

```sql
CREATE TABLE fee_tiers (
  id        INT PRIMARY KEY,
  min_total DECIMAL(10,2) NOT NULL,      -- tính từ (gồm cả mốc này)
  max_total DECIMAL(10,2) NOT NULL,      -- tới trước mốc này (không gồm)
  fee       DECIMAL(10,2) NOT NULL
);
INSERT INTO fee_tiers VALUES
  (1, 0.00, 50.00, 15.00), (2, 50.00, 100.00, 10.00), (3, 100.00, 99999999.99, 0.00);

SELECT o.id, o.total, t.id AS tier, t.fee
FROM orders o
JOIN fee_tiers t ON o.total >= t.min_total AND o.total < t.max_total
ORDER BY o.id;
```

Kết quả mong đợi:

| id | total | tier | fee |
|---|---|---|---|
| 10 | 100.00 | 3 | 0.00 |
| 11 | 50.00 | 2 | 10.00 |
| 12 | 70.00 | 2 | 10.00 |
| 13 | 30.00 | 1 | 15.00 |

Khoảng được viết dạng "từ mốc dưới (gồm) tới trước mốc trên (không gồm)" để hai bậc liền nhau không
chồng lên nhau: đơn 50.00 chỉ thuộc bậc 2. Nếu viết `BETWEEN 0 AND 50` và `BETWEEN 50 AND 100`, đơn
50.00 khớp cả hai bậc và xuất hiện hai lần.

⚠️ Với non-equi join, một dòng có thể khớp nhiều dòng bên kia mà nhìn câu SQL không thấy ngay. Dữ
liệu bậc phí bị nhập chồng nhau một lần là mọi báo cáo dùng join này bị nhân dòng. Nếu mỗi đơn chỉ
được thuộc một bậc, hãy kiểm tra dữ liệu bậc (không chồng, không hở) trước khi tin kết quả.

## 3. LEFT JOIN và RIGHT JOIN: giữ cả dòng không có cặp

### 3.1 LEFT JOIN

Nhiều câu hỏi cần giữ cả những dòng không có cặp: "liệt kê mọi khách, kèm đơn hàng nếu có". INNER
JOIN làm mất Chi, nên không dùng được. Đây là việc của *outer join*.

*LEFT JOIN* (viết đầy đủ là `LEFT OUTER JOIN`, từ `OUTER` có thể bỏ) giữ mọi dòng của bảng bên trái,
tức bảng viết trước chữ `LEFT JOIN`. Mô hình logic có thêm bước 3:

1. Ghép mọi cặp (tích Descartes).
2. Giữ các cặp thoả `ON`. Tới đây giống hệt INNER JOIN.
3. Với mỗi dòng bảng trái không còn cặp nào, thêm đúng một dòng: dữ liệu của dòng trái, mọi cột của
   bảng phải điền NULL. Dòng thêm vào này gọi là *dòng bù NULL* (*NULL-complemented row*).

```sql
SELECT c.id, c.name, o.id AS order_id, o.status
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
ORDER BY c.id, o.id;
```

Bước 2 cho 3 cặp như mục 1.3. Bước 3 duyệt từng khách:

| Khách | Số cặp sau bước 2 | Bước 3 làm gì |
|---|---|---|
| An | 2 (đơn 10, 11) | không thêm gì |
| Bình | 1 (đơn 12) | không thêm gì |
| Chi | 0 | thêm dòng (Chi, NULL, NULL) |

Kết quả mong đợi (4 dòng):

| id | name | order_id | status |
|---|---|---|---|
| 1 | An | 10 | paid |
| 1 | An | 11 | pending |
| 2 | Bình | 12 | pending |
| 3 | Chi | NULL | NULL |

Đơn 13 vẫn không có mặt: LEFT JOIN chỉ bảo vệ bảng bên trái. Dòng của bảng phải không khớp với ai
vẫn bị loại như INNER JOIN.

Từ mô hình trên rút ra cách đếm số dòng: số dòng LEFT JOIN = số cặp khớp + số dòng trái không có cặp
nào (ở đây 3 + 1 = 4). Hệ quả: kết quả LEFT JOIN không bao giờ ít dòng hơn bảng trái, nhưng có thể
nhiều hơn (khi một dòng trái khớp nhiều dòng phải, như An).

⚠️ MySQL bắt buộc LEFT JOIN và RIGHT JOIN phải có `ON` hoặc `USING`. Viết `customers c LEFT JOIN
orders o` không kèm điều kiện là lỗi cú pháp, khác với `JOIN` trống ở mục 2.4.

### 3.2 NULL "do không khớp" và NULL "có sẵn trong dữ liệu"

Sau một LEFT JOIN, một ô NULL ở cột bảng phải có thể mang hai nghĩa khác nhau. Đảo chiều, lấy mọi
đơn kèm khách:

```sql
SELECT o.id, o.customer_id, c.name, c.city
FROM orders o
LEFT JOIN customers c ON c.id = o.customer_id
ORDER BY o.id;
```

Kết quả mong đợi:

| id | customer_id | name | city |
|---|---|---|---|
| 10 | 1 | An | Hà Nội |
| 11 | 1 | An | Hà Nội |
| 12 | 2 | Bình | NULL |
| 13 | NULL | NULL | NULL |

- Đơn 12: `city` là NULL vì dữ liệu của Bình có `city` NULL. Khách có tồn tại.
- Đơn 13: `name` và `city` là NULL vì không có khách nào khớp. Đây là dòng bù NULL.

Muốn biết một dòng có khớp hay không, hãy nhìn vào cột *không thể NULL* của bảng phải. Lựa chọn tốt
nhất là khoá chính (`c.id`): dòng có khớp thì `c.id` chắc chắn khác NULL, nên `c.id IS NULL` chỉ
đúng với dòng bù NULL. Nhìn vào `c.city` thì đơn 12 và 13 trông giống nhau. Ý này quay lại ở mục 9
(anti-join).

Khi hiển thị, có thể thay NULL bằng chữ dễ đọc bằng `COALESCE` (học ở
[chương 06](06-ham-bieu-thuc-null.md)): `COALESCE(c.name, '(khách vãng lai)')`.

### 3.3 RIGHT JOIN

*RIGHT JOIN* ngược lại: giữ mọi dòng của bảng bên phải, bảng trái thiếu thì điền NULL.

```sql
SELECT c.name, o.id AS order_id, o.total
FROM customers c
RIGHT JOIN orders o ON o.customer_id = c.id
ORDER BY o.id;
```

Kết quả mong đợi (mọi đơn đều có mặt, kể cả đơn 13):

| name | order_id | total |
|---|---|---|
| An | 10 | 100.00 |
| An | 11 | 50.00 |
| Bình | 12 | 70.00 |
| NULL | 13 | 30.00 |

`A RIGHT JOIN B ON ...` luôn viết lại được thành `B LEFT JOIN A ON ...` với cùng tập dòng. Câu trên
tương đương:

```sql
SELECT c.name, o.id AS order_id, o.total
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id
ORDER BY o.id;
```

Chính MySQL cũng làm vậy: ngay ở bước phân tích cú pháp, nó đổi mọi RIGHT JOIN thành LEFT JOIN tương
đương. Tài liệu MySQL khuyên dùng LEFT JOIN thay cho RIGHT JOIN để code dễ mang sang database khác.
Trong thực tế, gần như mọi người chỉ viết LEFT JOIN, theo quy ước: bảng "chính" (bảng bạn muốn giữ
đủ dòng) đứng đầu `FROM`, các bảng "kèm thêm nếu có" LEFT JOIN vào sau. Đọc câu từ trên xuống là biết
bảng nào được bảo vệ.

### 3.4 Đếm sau LEFT JOIN: COUNT(*) khác COUNT(cột)

"Mỗi khách có bao nhiêu đơn, kể cả khách chưa có đơn nào" là câu hỏi rất hay gặp. Câu trả lời cần
`GROUP BY` và `COUNT` của [chương 08](08-group-by-aggregate.md); ở đây chỉ cần biết `GROUP BY c.id`
gom các dòng cùng khách lại thành một, và `COUNT` đếm trong mỗi nhóm.

```sql
SELECT c.name,
       COUNT(o.id) AS so_don,     -- đếm giá trị khác NULL của o.id
       COUNT(*)    AS so_dong     -- đếm số dòng, kể cả dòng bù NULL
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
GROUP BY c.id, c.name
ORDER BY c.id;
```

Kết quả mong đợi:

| name | so_don | so_dong |
|---|---|---|
| An | 2 | 2 |
| Bình | 1 | 1 |
| Chi | 0 | 1 |

⚠️ Chi có 0 đơn nhưng `COUNT(*)` ra 1, vì dòng bù NULL vẫn là một dòng. Sau LEFT JOIN, muốn đếm số
dòng khớp thì đếm một cột không thể NULL của bảng phải: `COUNT(o.id)`.

## 4. Điều kiện đặt ở ON hay ở WHERE

Đây là chỗ sinh ra nhiều bug báo cáo nhất khi dùng LEFT JOIN, và câu hỏi phỏng vấn SQL rất hay gặp.

### 4.1 Với INNER JOIN: đặt đâu cũng cho cùng kết quả

INNER JOIN giữ cặp thoả `ON`, rồi `WHERE` giữ dòng thoả `WHERE`. Cả hai đều là "giữ khi điều kiện là
TRUE", nên chuyển một điều kiện từ chỗ này sang chỗ kia không đổi kết quả. Hai câu sau tương đương:

```sql
SELECT c.name, o.id FROM customers c
JOIN orders o ON o.customer_id = c.id AND o.status = 'paid';

SELECT c.name, o.id FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid';
```

Cả hai cho một dòng (An, 10). Optimizer của MySQL cũng coi chúng như nhau: nó gộp điều kiện `ON`
của INNER JOIN vào chung với điều kiện `WHERE`. Quy ước nên theo, cũng là lời khuyên trong tài liệu
MySQL: `ON` mô tả cách ghép hai bảng, `WHERE` mô tả dòng nào được giữ trong kết quả.

### 4.2 Với LEFT JOIN: kết quả khác nhau

Yêu cầu: "liệt kê mọi khách, kèm các đơn đã thanh toán nếu có". Hai cách viết:

```sql
-- Cách A: điều kiện status nằm trong ON
SELECT c.name, o.id AS order_id, o.status
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND o.status = 'paid'
ORDER BY c.id, o.id;

-- Cách B: điều kiện status nằm trong WHERE
SELECT c.name, o.id AS order_id, o.status
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid'
ORDER BY c.id, o.id;
```

Cách A, đi theo ba bước của LEFT JOIN. Điều kiện ghép bây giờ là "đúng khách VÀ đơn đã trả":

| Khách | Cặp thoả ON (bước 2) | Bước 3 |
|---|---|---|
| An | (An, 10). Đơn 11 là pending nên không thoả | không thêm |
| Bình | không có. Đơn 12 là pending | thêm (Bình, NULL, NULL) |
| Chi | không có | thêm (Chi, NULL, NULL) |

Kết quả cách A:

| name | order_id | status |
|---|---|---|
| An | 10 | paid |
| Bình | NULL | NULL |
| Chi | NULL | NULL |

Cách B: LEFT JOIN chạy xong trước với điều kiện chỉ có khoá, ra đúng 4 dòng ở mục 3.1. Sau đó
`WHERE` mới lọc:

| name | order_id | status | `o.status = 'paid'` | |
|---|---|---|---|---|
| An | 10 | paid | TRUE | giữ |
| An | 11 | pending | FALSE | loại |
| Bình | 12 | pending | FALSE | loại |
| Chi | NULL | NULL | UNKNOWN | loại |

Kết quả cách B chỉ còn một dòng:

| name | order_id | status |
|---|---|---|
| An | 10 | paid |

Cách A đúng yêu cầu. Cách B làm mất cả Bình lẫn Chi.

Bản chất của sự khác nhau:

- Điều kiện ở `ON` trả lời câu hỏi "dòng phải nào được tính là khớp?". Không thoả `ON` chỉ có nghĩa
  là "không khớp", và dòng trái vẫn được giữ nhờ bước 3.
- Điều kiện ở `WHERE` trả lời câu hỏi "dòng kết quả nào được giữ?". Nó chạy sau khi join xong, lúc
  này dòng bù NULL chỉ là một dòng bình thường, và không thoả `WHERE` là bị xoá cả dòng, kể cả phần
  dữ liệu của bảng trái.

### 4.3 WHERE trên cột bảng phải biến LEFT JOIN thành INNER JOIN

Trong cách B, điều kiện `o.status = 'paid'` không thể TRUE trên dòng bù NULL, vì mọi cột `o.*` ở
đó đều là NULL và `NULL = 'paid'` là UNKNOWN. Nên mọi dòng bù NULL đều bị `WHERE` loại, và phần còn
lại giống hệt kết quả INNER JOIN. Bạn viết LEFT JOIN nhưng nhận về INNER JOIN, không có lỗi, không
có cảnh báo.

Tài liệu MySQL gọi một điều kiện như vậy là *null-rejected* (từ chối NULL): điều kiện cho ra FALSE
hoặc UNKNOWN với mọi dòng bù NULL. Optimizer phát hiện được điều này và tự đổi outer join thành inner
join để có thêm lựa chọn thứ tự đọc bảng. Việc đổi đó không làm sai thêm gì, vì kết quả vốn đã giống
INNER JOIN. Lỗi nằm ở logic câu SQL của bạn.

Với `customers c LEFT JOIN orders o ON o.customer_id = c.id`, các điều kiện `WHERE` sau là
null-rejected, tức là biến câu thành INNER JOIN:

```sql
WHERE o.status = 'paid'
WHERE o.total > 50
WHERE o.id IS NOT NULL
WHERE o.total > 50 OR o.status = 'paid'   -- cả hai vế đều không thể TRUE trên dòng bù NULL
```

Còn các điều kiện sau thì không, vì chúng có thể TRUE trên dòng bù NULL:

```sql
WHERE o.id IS NULL                        -- chính là mẫu anti-join, mục 9
WHERE c.city = 'Hà Nội' OR o.total > 50   -- vế đầu chỉ dùng cột bảng trái
WHERE COALESCE(o.status, 'none') <> 'paid'
```

⚠️ Một cách "sửa" hay gặp mà vẫn sai: thêm `OR o.id IS NULL` vào `WHERE`.

```sql
SELECT c.name, o.id AS order_id, o.status
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid' OR o.id IS NULL
ORDER BY c.id, o.id;
```

Đi qua 4 dòng của LEFT JOIN: (An, 10, paid) giữ, (An, 11, pending) loại, (Bình, 12, pending) loại vì
`o.id` khác NULL và status không phải paid, (Chi, NULL) giữ. Kết quả: An 10, Chi NULL. Chi được cứu,
nhưng Bình vẫn mất: Bình có đơn, chỉ là không có đơn nào đã trả, nên không có dòng bù NULL nào cho
Bình. Muốn "mọi khách, kèm đơn đã trả nếu có" thì chỉ có một cách đúng: đưa điều kiện vào `ON`
(cách A).

### 4.4 Điều kiện của bảng trái đặt ở ON: không lọc được dòng nào

Lỗi ngược lại cũng hay gặp: muốn chỉ lấy khách ở Hà Nội, nhưng lại đặt điều kiện vào `ON`.

```sql
SELECT c.name, o.id AS order_id
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND c.city = 'Hà Nội'
ORDER BY c.id, o.id;
```

Ở bước 2, chỉ An thoả `c.city = 'Hà Nội'` nên chỉ An có cặp (đơn 10, 11). Bình (`city` NULL, so
sánh ra UNKNOWN) và Chi (Đà Nẵng) không có cặp nào, và bước 3 thêm dòng bù NULL cho cả hai. Kết quả:

| name | order_id |
|---|---|
| An | 10 |
| An | 11 |
| Bình | NULL |
| Chi | NULL |

Cả ba khách vẫn có mặt. Điều kiện trên bảng trái trong `ON` của LEFT JOIN không bao giờ loại được
dòng trái nào; nó chỉ làm những dòng trái không thoả bị "mất cặp". Muốn lọc khách thì đặt ở `WHERE`:

```sql
SELECT c.name, o.id AS order_id
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE c.city = 'Hà Nội'
ORDER BY c.id, o.id;
-- An 10, An 11
```

### 4.5 Quy tắc tóm gọn

Với `A LEFT JOIN B` (A là bảng được giữ, B là bảng có thể bị bù NULL):

| Loại điều kiện | Đặt ở đâu | Đặt nhầm chỗ thì sao |
|---|---|---|
| Cách ghép A với B (khoá) | `ON` | |
| Lọc B ("chỉ tính những dòng B thoả...") | `ON` | Ở `WHERE`: thành INNER JOIN, mất dòng A không có B thoả |
| Lọc A ("chỉ lấy những dòng A thoả...") | `WHERE` | Ở `ON`: không lọc được dòng A nào |
| Tìm A không có B nào | `WHERE B.khoá_chính IS NULL` | (mục 9.2) |

Với INNER JOIN, `ON` và `WHERE` cho cùng kết quả; vẫn nên giữ quy ước "ghép ở `ON`, lọc ở `WHERE`"
cho dễ đọc.

Trong Laravel, `leftJoin('orders', 'orders.customer_id', '=', 'customers.id')->where('orders.status',
'paid')` đặt điều kiện vào `WHERE`, tức là cách B. Muốn điều kiện nằm trong `ON` thì truyền closure
và gọi `where` trên `JoinClause`:

```php
use Illuminate\Database\Query\JoinClause;
use Illuminate\Support\Facades\DB;

$rows = DB::table('customers')
    ->leftJoin('orders', function (JoinClause $join): void {
        $join->on('orders.customer_id', '=', 'customers.id')
             ->where('orders.status', '=', 'paid');      // nằm trong ON
    })
    ->select('customers.name', 'orders.id as order_id')
    ->get();
```

## 5. ON và USING (và vì sao nên tránh NATURAL JOIN)

### 5.1 USING: viết tắt khi cột ghép trùng tên

Khi cột dùng để ghép có cùng tên ở cả hai bảng, có thể viết `USING (tên_cột)` thay cho `ON`.
`a JOIN b USING (c1, c2)` có cùng điều kiện ghép với `a JOIN b ON a.c1 = b.c1 AND a.c2 = b.c2`.

Dữ liệu mẫu riêng cho mục này (tồn kho và bảng giá, cùng dùng mã `sku`):

```sql
USE ch07;
CREATE TABLE stock  (sku VARCHAR(10) PRIMARY KEY, qty INT NOT NULL);
CREATE TABLE prices (sku VARCHAR(10) PRIMARY KEY, price DECIMAL(10,2) NOT NULL);
INSERT INTO stock  VALUES ('A', 5), ('B', 0);
INSERT INTO prices VALUES ('B', 20.00), ('C', 30.00);
```

So sánh `SELECT *` của hai cách viết:

```sql
SELECT * FROM stock JOIN prices ON prices.sku = stock.sku;
```

| sku | qty | sku | price |
|---|---|---|---|
| B | 0 | B | 20.00 |

```sql
SELECT * FROM stock JOIN prices USING (sku);
```

| sku | qty | price |
|---|---|---|
| B | 0 | 20.00 |

Cả hai chọn ra cùng một tập dòng (chỉ `B` có ở cả hai bảng). Khác nhau ở các cột mà `SELECT *` trả
về:

- Với `ON`, `SELECT *` trả mọi cột của bảng trái rồi mọi cột của bảng phải, nên `sku` xuất hiện hai
  lần.
- Với `USING`, các cột chung được gộp thành một cột duy nhất và đứng đầu. Thứ tự theo chuẩn SQL mà
  MySQL tuân theo: các cột chung (theo thứ tự trong bảng thứ nhất), rồi các cột chỉ có ở bảng thứ
  nhất, rồi các cột chỉ có ở bảng thứ hai.

### 5.2 Cột gộp trong outer join

Cột gộp của `USING` được định nghĩa là `COALESCE(a.cột, b.cột)`: lấy giá trị khác NULL trong hai
bên. Với INNER JOIN hai bên luôn bằng nhau nên không có gì đáng nói. Với LEFT JOIN thì có:

```sql
SELECT * FROM stock LEFT JOIN prices USING (sku) ORDER BY sku;
```

| sku | qty | price |
|---|---|---|
| A | 5 | NULL |
| B | 0 | 20.00 |

```sql
SELECT * FROM stock LEFT JOIN prices ON prices.sku = stock.sku ORDER BY stock.sku;
```

| sku | qty | sku | price |
|---|---|---|---|
| A | 5 | NULL | NULL |
| B | 0 | B | 20.00 |

Ở dòng `A` không có giá, cột `sku` gộp vẫn là `'A'` (lấy từ `stock`), còn ở bản `ON`, cột
`prices.sku` là NULL. Trong câu dùng `USING`, viết `sku` trống không là đang nói tới cột gộp, nên
`ORDER BY sku` ở trên không bị lỗi "ambiguous" như mục 1.4.

### 5.3 Khi nào dùng USING, khi nào dùng ON

| Tiêu chí | `ON` | `USING` |
|---|---|---|
| Điều kiện | Bất kỳ biểu thức nào | Chỉ phép bằng trên các cột cùng tên |
| Cột chung trong `SELECT *` | Lặp lại, mỗi bảng một cột | Gộp thành một |
| Hợp với quy ước đặt tên Laravel (`customers.id` và `orders.customer_id`) | Có | Không, vì tên khác nhau |
| Dùng khi | Mặc định cho mọi trường hợp | Hai bên dùng cùng tên cho cột khoá: schema đặt khoá chính trùng tên khoá ngoại (`customers.customer_id` và `orders.customer_id`), hoặc hai bảng tạm cùng gom theo `order_id` (mục 10.4) |

Với schema theo quy ước Laravel, khoá chính tên `id` còn khoá ngoại tên `<bảng>_id`, nên join cha với
con gần như luôn phải dùng `ON`. `USING` hữu ích khi ghép hai thứ cùng "nói về" một cột, như ở
[mục 10.4](#104-cách-sửa-gom-phía-nhiều-trước-rồi-mới-join) khi ghép hai bảng tạm cùng gom theo
`order_id`.

### 5.4 NATURAL JOIN: tự đoán điều kiện ghép, đừng dùng

`NATURAL JOIN` là `USING` với danh sách cột được tự động lấy là *mọi* cột trùng tên giữa hai bảng.
Nghe tiện, nhưng điều kiện ghép phụ thuộc vào tên cột chứ không vào ý bạn:

- Với quy ước Laravel, hầu hết bảng đều có `id`, `created_at`, `updated_at` (do `$table->id()` và
  `$table->timestamps()` trong migration). `customers NATURAL JOIN orders` khi đó sẽ ghép theo
  `id = id AND created_at = created_at AND updated_at = updated_at`, hoàn toàn vô nghĩa, và không báo
  lỗi.
- Câu đang chạy đúng có thể đổi nghĩa khi ai đó thêm một cột trùng tên vào một trong hai bảng, dù
  không ai sửa câu SQL. Tài liệu PostgreSQL cũng cảnh báo đúng điểm này.
- Tài liệu PostgreSQL ghi thêm: nếu hai bảng không có cột nào trùng tên, `NATURAL JOIN` hoạt động như
  `CROSS JOIN`.

Hãy luôn viết rõ điều kiện ghép bằng `ON` (hoặc `USING` với danh sách cột cụ thể).

## 6. CROSS JOIN: mọi tổ hợp

### 6.1 Định nghĩa

*CROSS JOIN* trả về tích Descartes, đúng bước 1 của mô hình ở mục 1.3, không lọc gì: m dòng ghép với
n dòng ra m × n dòng. Không có khái niệm "dòng không khớp" vì cặp nào cũng được giữ.

```sql
CREATE TABLE sizes  (size  VARCHAR(5)  PRIMARY KEY);
CREATE TABLE colors (color VARCHAR(10) PRIMARY KEY);
INSERT INTO sizes  VALUES ('S'), ('M'), ('L');
INSERT INTO colors VALUES ('Hồng'), ('Xanh');

SELECT s.size, c.color
FROM sizes s
CROSS JOIN colors c
ORDER BY s.size, c.color;
```

Kết quả mong đợi: 3 × 2 = 6 dòng (sắp theo chữ cái nên L đứng trước M và S):

| size | color |
|---|---|
| L | Hồng |
| L | Xanh |
| M | Hồng |
| M | Xanh |
| S | Hồng |
| S | Xanh |

Ứng dụng: sinh mọi biến thể sản phẩm (size × màu), mọi tổ hợp cấu hình để test, hoặc dựng "khung"
cho báo cáo như mục dưới. Laravel có `crossJoin` cho việc này.

### 6.2 Dựng khung báo cáo rồi LEFT JOIN dữ kiện vào

Một mẫu rất thực tế: báo cáo cần hiện đủ mọi ô, kể cả ô bằng 0. Ví dụ "số đơn của từng khách theo
từng trạng thái". Đếm thẳng từ `orders` chỉ ra những tổ hợp có đơn; ô (Chi, paid) không bao giờ xuất
hiện. Cách làm: CROSS JOIN để có đủ mọi tổ hợp (khách × trạng thái), rồi LEFT JOIN đơn hàng vào khung.

```sql
SELECT c.name, s.status, COUNT(o.id) AS so_don
FROM customers c
CROSS JOIN (SELECT 'paid' AS status UNION ALL SELECT 'pending') AS s   -- bảng tạm 2 dòng
LEFT JOIN orders o ON o.customer_id = c.id AND o.status = s.status
GROUP BY c.id, c.name, s.status
ORDER BY c.id, s.status;
```

`(SELECT ... UNION ALL SELECT ...) AS s` là một bảng tạm hai dòng `'paid'`, `'pending'` dựng ngay
trong câu (gọi là *derived table*, học ở [chương 09](09-subquery-cte-union.md)). Kết quả mong đợi:

| name | status | so_don |
|---|---|---|
| An | paid | 1 |
| An | pending | 1 |
| Bình | paid | 0 |
| Bình | pending | 1 |
| Chi | paid | 0 |
| Chi | pending | 0 |

Để ý điều kiện `o.status = s.status` nằm trong `ON` (theo đúng quy tắc mục 4). Đặt nó ở `WHERE` thì
các ô 0 lại biến mất. Cùng mẫu này dùng cho báo cáo theo ngày: dựng đủ dãy ngày (bằng recursive CTE ở
[chương 09](09-subquery-cte-union.md)) rồi LEFT JOIN doanh thu vào, ngày không có đơn vẫn hiện số 0.

### 6.3 Cross join ngoài ý muốn

⚠️ Nguy hiểm thật sự của tích Descartes là khi bạn không cố ý tạo ra nó:

- Viết dấu phẩy trong `FROM` mà quên điều kiện trong `WHERE`.
- Viết `JOIN` mà quên `ON`: MySQL vẫn chạy (mục 2.4).
- Điều kiện `ON` luôn đúng do gõ nhầm, ví dụ `ON o.customer_id = o.customer_id` (so cột với chính
  nó): đúng với mọi đơn có `customer_id` khác NULL, nên mỗi khách ghép với gần như mọi đơn.

Với dữ liệu nhỏ lúc dev, kết quả chỉ "hơi nhiều dòng". Lên production, 10.000 khách nhân 1.000.000
đơn là 10 tỷ dòng: query chạy mãi, ngốn CPU và bộ nhớ của server. Dấu hiệu nhận biết: số dòng kết quả
xấp xỉ tích số dòng hai bảng, hoặc cùng một dòng lặp lại nhiều lần.

## 7. Self join: join một bảng với chính nó

### 7.1 Bảng nhân viên và quản lý

*Self join* là join một bảng với chính nó. Trường hợp kinh điển: nhân viên và quản lý cùng nằm trong
một bảng, cột `manager_id` trỏ về `id` của một nhân viên khác.

```sql
CREATE TABLE employees (
  id         INT PRIMARY KEY,
  name       VARCHAR(50) NOT NULL,
  manager_id INT NULL,                   -- NULL: không có quản lý (giám đốc)
  FOREIGN KEY (manager_id) REFERENCES employees (id)
);
INSERT INTO employees VALUES (1, 'Hà', NULL), (2, 'Khoa', 1), (3, 'Lan', 1), (4, 'Minh', 2);
```

```
            Hà (1)
           /      \
     Khoa (2)    Lan (3)
        |
     Minh (4)
```

Câu "mỗi nhân viên kèm tên quản lý":

```sql
SELECT e.name AS nhan_vien, m.name AS quan_ly
FROM employees e
LEFT JOIN employees m ON m.id = e.manager_id
ORDER BY e.id;
```

Kết quả mong đợi:

| nhan_vien | quan_ly |
|---|---|
| Hà | NULL |
| Khoa | Hà |
| Lan | Hà |
| Minh | Khoa |

Cách hiểu: hãy tưởng tượng có hai bản sao của bảng `employees`, một bản đóng vai "nhân viên" (alias
`e`), một bản đóng vai "quản lý" (alias `m`). Mọi thứ khác giống hệt join hai bảng khác nhau. Dùng
LEFT JOIN vì Hà không có quản lý; với INNER JOIN, Hà biến mất khỏi danh sách nhân viên.

Alias ở đây là bắt buộc: viết `FROM employees JOIN employees ON ...` thì hai bản sao trùng tên, không
có cách nào chỉ ra cột nào thuộc bản nào, và MySQL báo
`ERROR 1066 (42000): Not unique table/alias: 'employees'`. Hãy đặt alias theo vai trò (`e`, `m`, hoặc
`staff`, `boss`) chứ đừng `e1`, `e2`, để đọc câu là hiểu.

### 7.2 Mỗi tầng là thêm một join

Muốn lấy cả quản lý của quản lý thì join thêm một bản sao nữa:

```sql
SELECT e.name AS nhan_vien, m.name AS quan_ly, g.name AS quan_ly_cap_2
FROM employees e
LEFT JOIN employees m ON m.id = e.manager_id
LEFT JOIN employees g ON g.id = m.manager_id
ORDER BY e.id;
```

| nhan_vien | quan_ly | quan_ly_cap_2 |
|---|---|---|
| Hà | NULL | NULL |
| Khoa | Hà | NULL |
| Lan | Hà | NULL |
| Minh | Khoa | Hà |

Join thứ hai dùng `m.manager_id`, tức là đi tiếp từ bản sao `m`. Với Hà, `m` đã là dòng bù NULL nên
`m.manager_id` là NULL, và `g` cũng bù NULL; đây là lý do join thứ hai cũng phải là LEFT JOIN (mục
11.3 giải thích kỹ).

Self join chỉ đi được một số tầng cố định, mỗi tầng một join. Cây có độ sâu không biết trước (sơ đồ
tổ chức, danh mục nhiều cấp, cây bình luận) cần *recursive CTE*, học ở
[chương 09](09-subquery-cte-union.md).

### 7.3 So sánh các dòng trong cùng một bảng

Self join cũng dùng để ghép các dòng của cùng bảng với nhau theo một tiêu chí. Ví dụ "các cặp nhân
viên có cùng quản lý":

```sql
SELECT a.name AS nguoi_1, b.name AS nguoi_2
FROM employees a
JOIN employees b ON b.manager_id = a.manager_id
ORDER BY a.id, b.id;
```

Kết quả thử lần đầu có 5 dòng, không như mong muốn:

| nguoi_1 | nguoi_2 |
|---|---|
| Khoa | Khoa |
| Khoa | Lan |
| Lan | Khoa |
| Lan | Lan |
| Minh | Minh |

Hai vấn đề: mỗi người tự ghép với chính mình, và mỗi cặp xuất hiện hai lần theo hai chiều. Thêm
`a.id < b.id` vào `ON` giải quyết cả hai, vì chỉ giữ cặp theo một chiều duy nhất:

```sql
SELECT a.name AS nguoi_1, b.name AS nguoi_2
FROM employees a
JOIN employees b ON b.manager_id = a.manager_id AND a.id < b.id
ORDER BY a.id, b.id;
-- Khoa | Lan
```

Hà không ghép được với ai, kể cả chính mình: `manager_id` của Hà là NULL, và `NULL = NULL` là
UNKNOWN. Nếu dùng `a.id <> b.id` thay cho `<`, bạn bỏ được cặp tự ghép nhưng vẫn còn cả (Khoa, Lan)
lẫn (Lan, Khoa).

## 8. FULL OUTER JOIN và cách giả lập trên MySQL

### 8.1 FULL OUTER JOIN là gì

*FULL OUTER JOIN* giữ mọi dòng của cả hai bảng: các cặp khớp, cộng dòng trái không có cặp (bù NULL
bên phải), cộng dòng phải không có cặp (bù NULL bên trái). Nói cách khác, nó là hợp của LEFT JOIN và
RIGHT JOIN. Dùng khi đối soát hai nguồn dữ liệu: "cái nào có ở A mà không có ở B, cái nào có ở B mà
không có ở A, cái nào có ở cả hai".

Với khách và đơn, kết quả mong muốn là 5 dòng: 3 cặp khớp, Chi (không có đơn), và đơn 13 (không có
khách). PostgreSQL viết trực tiếp được:

```sql
-- PostgreSQL, không chạy trên MySQL
SELECT c.id AS customer_id, c.name, o.id AS order_id, o.total
FROM customers c
FULL JOIN orders o ON o.customer_id = c.id
ORDER BY customer_id, order_id;
```

### 8.2 MySQL không có FULL OUTER JOIN

Về outer join, cú pháp join của MySQL 8.4 chỉ có `LEFT [OUTER] JOIN` và `RIGHT [OUTER] JOIN` (kể cả
dạng `NATURAL`), không có `FULL`.

⚠️ Bẫy riêng của MySQL: `FULL` không phải từ khoá dành riêng (*reserved word*), nên nó có thể bị hiểu
là alias của bảng đứng trước. Bug report #69858 (báo trên MySQL 5.6) mô tả câu
`SELECT * FROM Employee FULL JOIN Department USING (dept_no)` chạy không lỗi, không cảnh báo, như
`Employee AS FULL JOIN Department USING (dept_no)`, tức là một INNER JOIN, trả về ít dòng hơn bạn
nghĩ. Tới MySQL 8.4, `FULL` vẫn chưa thành từ khoá dành riêng. Từ 8.0.32, dùng `full` làm tên không
có dấu nháy (tên bảng, cột, alias) bị đánh dấu deprecated và sinh warning 4119 "Using FULL as unquoted
identifier is deprecated...", nhưng vẫn được chấp nhận. Còn `FULL OUTER JOIN` thì báo lỗi cú pháp, vì
`OUTER` là từ khoá dành riêng. Tóm lại: đừng viết `FULL` trong câu join trên MySQL, và khi một câu chạy
xong kèm "N warnings" thì hãy `SHOW WARNINGS` để xem.

### 8.3 Giả lập bằng LEFT JOIN và UNION

Vì FULL OUTER JOIN là hợp của LEFT JOIN và RIGHT JOIN, cách giả lập phổ biến là nối kết quả hai câu
bằng `UNION`. `UNION` nối kết quả của hai câu `SELECT` có cùng số cột, và mặc định loại các dòng trùng
nhau (học kỹ ở [chương 09](09-subquery-cte-union.md)).

```sql
SELECT c.id AS customer_id, c.name, o.id AS order_id, o.total
FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
UNION
SELECT c.id, c.name, o.id, o.total
FROM customers c RIGHT JOIN orders o ON o.customer_id = c.id
ORDER BY customer_id, order_id;
```

Từng bước:

- Nửa trên (LEFT JOIN): 4 dòng, (An, 10), (An, 11), (Bình, 12), (Chi, NULL).
- Nửa dưới (RIGHT JOIN): 4 dòng, (An, 10), (An, 11), (Bình, 12), (NULL, 13).
- `UNION` gộp lại và loại trùng: 3 cặp khớp xuất hiện ở cả hai nửa nên chỉ giữ một bản. Còn 5 dòng.

Kết quả mong đợi (MySQL xếp NULL lên đầu khi sắp tăng dần; PostgreSQL thì mặc định xếp NULL cuối):

| customer_id | name | order_id | total |
|---|---|---|---|
| NULL | NULL | 13 | 30.00 |
| 1 | An | 10 | 100.00 |
| 1 | An | 11 | 50.00 |
| 2 | Bình | 12 | 70.00 |
| 3 | Chi | NULL | NULL |

`ORDER BY` đặt sau câu `SELECT` cuối cùng sẽ sắp xếp toàn bộ kết quả sau `UNION`. Nó dùng tên
cột của câu đầu tiên (`customer_id`, `order_id`); MySQL không cho dùng dạng có tên bảng như `c.id` ở đây.

⚠️ Cách này đúng chỉ khi mỗi dòng kết quả có thể phân biệt được với nhau, thường là nhờ có khoá chính
của cả hai bảng trong danh sách cột. `UNION` không biết dòng nào là "cặp khớp bị lặp ở hai nửa", dòng
nào là "hai dòng thật tình cờ giống nhau"; nó xoá mọi dòng trùng. Thử chỉ lấy tên khách:

```sql
SELECT c.name FROM customers c LEFT JOIN orders o ON o.customer_id = c.id
UNION
SELECT c.name FROM customers c RIGHT JOIN orders o ON o.customer_id = c.id
ORDER BY name;
-- NULL, An, Bình, Chi: 4 dòng
```

FULL OUTER JOIN thật cho 5 dòng (An hai lần, vì An có hai đơn), nhưng `UNION` gộp hai dòng `An` thật
thành một.

### 8.4 Cách an toàn hơn: UNION ALL với nửa sau là anti-join

Cách chắc chắn đúng, không phụ thuộc cột nào được chọn: nửa trên lấy LEFT JOIN đầy đủ, nửa dưới chỉ
lấy những dòng bảng phải *không có* cặp (một anti-join, mục 9), rồi nối bằng `UNION ALL` (nối thẳng,
không loại trùng):

```sql
SELECT c.id AS customer_id, c.name, o.id AS order_id, o.total
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
UNION ALL
SELECT c.id, c.name, o.id, o.total
FROM orders o
LEFT JOIN customers c ON c.id = o.customer_id
WHERE c.id IS NULL                       -- chỉ các đơn không có khách
ORDER BY customer_id, order_id;
```

Nửa dưới chỉ ra một dòng (đơn 13), nên kết quả vẫn là 5 dòng như bảng ở mục 8.3. Hai nửa không bao
giờ chứa cùng một cặp, nên không cần loại trùng, và dòng thật giống nhau cũng không bị gộp. `UNION
ALL` còn rẻ hơn `UNION` vì database không phải tìm và loại dòng trùng trên toàn bộ kết quả.

## 9. Semi-join và anti-join: "có ít nhất một" và "không có cái nào"

Hai dạng câu hỏi xuất hiện liên tục trong thực tế:

- "Khách nào đã từng đặt hàng?", "sản phẩm nào đã bán được?": giữ dòng bảng A nếu có *ít nhất một*
  dòng tương ứng ở bảng B. Phép này gọi là *semi-join*.
- "Khách nào chưa đặt hàng?", "sản phẩm nào chưa bán được cái nào?": giữ dòng bảng A nếu *không có*
  dòng tương ứng nào ở B. Phép này gọi là *anti-join*.

Điểm chung: kết quả chỉ gồm dòng của A, mỗi dòng nhiều nhất một lần, không lấy cột nào của B. SQL
không có từ khoá `SEMI JOIN` hay `ANTI JOIN`; ta diễn đạt chúng bằng JOIN, `EXISTS` hoặc `IN`.

### 9.1 Semi-join

Thử bằng INNER JOIN trước:

```sql
SELECT c.id, c.name
FROM customers c
JOIN orders o ON o.customer_id = c.id
ORDER BY c.id;
```

Kết quả có An hai lần (1 An, 1 An, 2 Bình), vì INNER JOIN trả mỗi dòng trái một lần cho *mỗi* dòng
phải khớp. Câu hỏi chỉ cần biết "có hay không", nên lặp là thừa. Thêm `DISTINCT` thì hết lặp, nhưng
đó là sinh ra mọi dòng khớp rồi mới loại trùng, tốn công vô ích. Cách diễn đạt đúng ý hơn:

```sql
-- Cách 1: EXISTS
SELECT c.id, c.name
FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)
ORDER BY c.id;

-- Cách 2: IN
SELECT c.id, c.name
FROM customers c
WHERE c.id IN (SELECT o.customer_id FROM orders o)
ORDER BY c.id;
```

Cả hai cho 2 dòng: (1, An), (2, Bình).

- `EXISTS (subquery)` là TRUE nếu subquery trả về ít nhất một dòng, FALSE nếu không có dòng nào.
  MySQL bỏ qua danh sách cột trong subquery của `EXISTS`, nên viết `SELECT 1` hay `SELECT *` như nhau;
  `SELECT 1` là quy ước cho thấy "tôi chỉ quan tâm có dòng hay không".
- Subquery trong cách 1 nhắc tới `c.id` của câu ngoài. Subquery như vậy gọi là *correlated subquery*
  (subquery tương quan): về mặt logic, nó được tính lại cho từng dòng `c`. Subquery được học kỹ ở
  [chương 09](09-subquery-cte-union.md).
- `c.id IN (subquery)` là TRUE nếu `c.id` bằng một giá trị nào đó trong cột subquery trả về. Ở đây
  subquery trả về `1, 1, 2, NULL`. Với Chi, `3 IN (1, 1, 2, NULL)` không ra TRUE (ra UNKNOWN vì có NULL),
  nên Chi bị loại, đúng ý. NULL trong subquery không làm hỏng `IN` dạng khẳng định; nó chỉ phá dạng phủ
  định `NOT IN` (mục 9.3).

Ví dụ thứ hai, cần join bên trong subquery: "khách nào đã từng mua Bút (sản phẩm 1)?"

```sql
SELECT c.id, c.name
FROM customers c
WHERE EXISTS (
  SELECT 1
  FROM orders o
  JOIN order_items i ON i.order_id = o.id
  WHERE o.customer_id = c.id
    AND i.product_id = 1
)
ORDER BY c.id;
-- 1 An, 2 Bình
```

Viết bằng JOIN thẳng (`customers JOIN orders JOIN order_items WHERE i.product_id = 1`) sẽ ra An hai
lần vì An mua Bút trong cả đơn 10 lẫn đơn 11.

Khi cần lấy cả cột của bảng B (ví dụ tên khách kèm mã từng đơn), đó không còn là semi-join nữa; dùng
JOIN và chấp nhận mỗi dòng B một dòng kết quả.

### 9.2 Anti-join: ba cách viết

"Khách nào chưa đặt đơn nào?" Câu trả lời đúng là Chi.

Cách 1: LEFT JOIN rồi lọc dòng bù NULL.

```sql
SELECT c.id, c.name
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
WHERE o.id IS NULL
ORDER BY c.id;
-- 3 Chi
```

Từng bước: LEFT JOIN cho 4 dòng như mục 3.1; trong đó chỉ dòng của Chi là dòng bù NULL, nên chỉ nó
thoả `o.id IS NULL`. Đây là ngoại lệ có chủ đích của quy tắc ở mục 4: điều kiện trên bảng phải đặt ở
`WHERE`, và chính vì nó chạy sau join nên mới lọc ra được dòng bù NULL. Tài liệu MySQL dùng đúng mẫu
này để "tìm các dòng trong một bảng không có dòng tương ứng ở bảng kia".

Cách 2: `NOT EXISTS`.

```sql
SELECT c.id, c.name
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)
ORDER BY c.id;
-- 3 Chi
```

Đọc gần như nguyên văn câu hỏi: "khách mà không tồn tại đơn nào của họ". Không phải chọn cột để kiểm
NULL, không bao giờ trả dòng trùng.

Cách 3: `NOT IN`.

```sql
SELECT c.id, c.name
FROM customers c
WHERE c.id NOT IN (SELECT o.customer_id FROM orders o)
ORDER BY c.id;
-- Không có dòng nào! (Empty set)
```

Cách 3 trả về rỗng thay vì Chi. Lý do ở mục 9.3.

### 9.3 Bẫy NOT IN gặp NULL

`x NOT IN (a, b, c)` nghĩa là `x <> a AND x <> b AND x <> c` (tài liệu MySQL: `NOT IN` là tên khác
của `<> ALL`). Subquery `SELECT o.customer_id FROM orders o` trả về `1, 1, 2, NULL`, vì đơn 13 có
`customer_id` NULL. Tính cho từng khách:

| c.id | `c.id NOT IN (1, 1, 2, NULL)` khai triển | Kết quả | Giữ? |
|---|---|---|---|
| 1 | `1 <> 1` là FALSE | FALSE | loại |
| 2 | `2 <> 2` là FALSE | FALSE | loại |
| 3 | `3 <> 1` TRUE, `3 <> 2` TRUE, `3 <> NULL` UNKNOWN | TRUE AND UNKNOWN = UNKNOWN | loại |

Chi đáng lẽ được giữ, nhưng phép so sánh với NULL cho UNKNOWN, và `WHERE` chỉ giữ TRUE. Chỉ cần
subquery trả về *một* giá trị NULL là `NOT IN` không bao giờ TRUE với bất kỳ dòng nào, và kết quả rỗng.
Logic ba giá trị được giải thích kỹ ở [chương 06](06-ham-bieu-thuc-null.md).

⚠️ Bug này rất khó thấy vì nó phụ thuộc dữ liệu: câu chạy đúng nhiều tháng, rồi một ngày có một dòng
NULL lọt vào cột đó (đơn khách vãng lai, dữ liệu import), báo cáo "khách chưa mua hàng" bỗng trống
trơn mà không có lỗi nào.

`NOT IN` còn một bẫy NULL thứ hai, ở phía ngoài. "Đơn nào không gắn với khách nào?":

```sql
SELECT o.id FROM orders o
WHERE o.customer_id NOT IN (SELECT c.id FROM customers c)
ORDER BY o.id;
-- rỗng: với đơn 13, NULL NOT IN (1, 2, 3) là UNKNOWN

SELECT o.id FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.id = o.customer_id)
ORDER BY o.id;
-- 13
```

Cách tránh:

- Dùng `NOT EXISTS` cho anti-join. Đây là lựa chọn mặc định nên tập thói quen.
- Nếu buộc phải dùng `NOT IN` với subquery, loại NULL ngay trong subquery:
  `WHERE c.id NOT IN (SELECT o.customer_id FROM orders o WHERE o.customer_id IS NOT NULL)` cho đúng Chi.
- Khai báo `NOT NULL` cho cột khi nghiệp vụ cho phép; cột không thể NULL thì không có bẫy này.

`NOT IN` với danh sách hằng số do bạn tự viết (`status NOT IN ('cancelled', 'refunded')`) thì an toàn
hơn nhiều, vì bạn biết chắc trong danh sách không có NULL. Chỉ còn bẫy phía ngoài: dòng có `status`
là NULL cũng bị loại.

### 9.4 Bẫy của cách LEFT JOIN: kiểm IS NULL nhầm cột

Cách 1 ở mục 9.2 chỉ đúng khi cột được kiểm `IS NULL` *không thể* NULL trong một dòng có khớp. Lấy lại
ví dụ mục 3.2 ("đơn nào không gắn với khách nào?"):

```sql
-- SAI: city có thể NULL sẵn trong dữ liệu
SELECT o.id FROM orders o
LEFT JOIN customers c ON c.id = o.customer_id
WHERE c.city IS NULL
ORDER BY o.id;
-- 12, 13: đơn 12 bị tính nhầm vì Bình chưa khai báo thành phố

-- ĐÚNG: kiểm khoá chính của bảng phải
SELECT o.id FROM orders o
LEFT JOIN customers c ON c.id = o.customer_id
WHERE c.id IS NULL
ORDER BY o.id;
-- 13
```

Cột an toàn để kiểm: khoá chính của bảng phải, hoặc cột của bảng phải nằm trong một phép bằng của
`ON` khi `ON` chỉ gồm các điều kiện nối bằng `AND` (dòng có khớp thì phép bằng đó là TRUE, nên cột
không thể là NULL). Ở câu này, `c.id` an toàn còn `c.city` thì không. Ở câu "khách chưa có đơn" của
mục 9.2 (`customers c LEFT JOIN orders o`), `o.id` hay `o.customer_id` đều an toàn; `o.status` cũng an
toàn vì khai báo `NOT NULL`, nhưng sẽ hỏng nếu sau này có ai đổi cột thành cho phép NULL. Kiểm khoá
chính là thói quen ít rủi ro nhất.

### 9.5 MySQL thực thi semi-join và anti-join thế nào

Optimizer MySQL 8.4 nhận ra các mẫu trên và không chạy chúng một cách ngây thơ:

- Subquery dạng `IN (SELECT ...)`, `= ANY (SELECT ...)` hay `EXISTS (SELECT ...)` đứng ở mức ngoài
  cùng của `WHERE` hoặc `ON` được biến đổi thành semi-join, miễn là subquery thoả một số điều kiện
  (là một `SELECT` đơn không có `UNION`, không có `HAVING`, không có hàm tổng hợp, không có `LIMIT`,
  cùng vài điều kiện khác). Optimizer chọn theo chi phí giữa nhiều chiến lược: kéo bảng ra thành join
  thường (*table pullout*), join rồi loại trùng bằng bảng tạm (*duplicate weedout*), dừng ở dòng khớp
  đầu tiên (*FirstMatch*), *LooseScan*, hoặc materialize subquery thành bảng tạm có index.
- Các dạng phủ định `NOT IN (SELECT ...)`, `NOT EXISTS (SELECT ...)` (với cùng các điều kiện trên)
  được biến đổi thành antijoin: với mỗi dòng ngoài, tìm thấy một dòng khớp là bỏ ngay dòng ngoài đó.
  Tài liệu ghi rõ: trong đa số trường hợp, phép biến đổi antijoin không áp dụng được nếu các biểu thức
  được so sánh có thể NULL, thêm một lý do để khai báo `NOT NULL`.
- Với mẫu LEFT JOIN ... `IS NULL`, nếu cột được kiểm khai báo `NOT NULL`, MySQL ngừng tìm thêm dòng ở
  bảng phải ngay khi thấy một dòng khớp.

Hệ quả thực tế: đừng chọn giữa JOIN, `EXISTS`, `IN` vì lời đồn "subquery luôn chậm". Hãy chọn cách
viết đúng ngữ nghĩa và an toàn với NULL, rồi xem plan bằng `EXPLAIN` ([chương 12](12-explain-toi-uu-query.md))
nếu cần tối ưu.

### 9.6 Chọn cách nào

| Mục đích | Cách viết | Đúng khi có NULL? | Có thể trả dòng trùng? | Ghi chú |
|---|---|---|---|---|
| Semi-join | `EXISTS (...)` | Đúng | Không | Nên dùng |
| Semi-join | `IN (subquery)` | Đúng | Không | Tốt khi so một cột |
| Semi-join | `JOIN` | Đúng | Có | Chỉ dùng khi cần cột của bảng kia |
| Anti-join | `NOT EXISTS (...)` | Đúng | Không | Nên dùng |
| Anti-join | `LEFT JOIN ... WHERE b.pk IS NULL` | Đúng nếu kiểm cột không thể NULL | Không | Hay gặp, đúng nếu kiểm khoá chính |
| Anti-join | `NOT IN (subquery)` | Sai: subquery có NULL là ra rỗng; dòng ngoài mang NULL luôn bị loại | Không | Tránh, hoặc lọc `IS NOT NULL` |

Trong Laravel: `whereExists(...)` sinh `where exists (...)`; `has('orders')` và
`whereHas('orders', ...)` sinh `EXISTS`; `doesntHave('orders')` và `whereDoesntHave(...)` sinh
`NOT EXISTS`. Còn `whereNotIn('id', $subquery)` sinh `NOT IN` và mang nguyên bẫy NULL ở mục 9.3.

## 10. Fan-out: join 1-n rồi SUM ra số sai

Phần này dùng `SUM` (cộng các giá trị) và `GROUP BY` (gom nhóm), được học đầy đủ ở
[chương 08](08-group-by-aggregate.md). Ở đây chỉ cần hiểu `SUM(cột)` cộng giá trị cột đó trên mọi dòng
đi vào nó.

### 10.1 Hiện tượng

Yêu cầu: "tổng doanh thu các đơn đã thanh toán, và tổng số món đã bán trong các đơn đó". Câu viết
thẳng:

```sql
SELECT SUM(o.total) AS doanh_thu, SUM(i.qty) AS so_mon
FROM orders o
JOIN order_items i ON i.order_id = o.id
WHERE o.status = 'paid';
```

Đơn đã trả là 10 (100.00) và 13 (30.00), nên doanh thu đúng là 130.00. Nhưng câu trên trả về:

| doanh_thu | so_mon |
|---|---|
| 330.00 | 7 |

Nhìn tập dòng mà `SUM` thực sự cộng, tức kết quả join trước khi gom:

| o.id | o.total | i.id | i.qty |
|---|---|---|---|
| 10 | 100.00 | 1 | 2 |
| 10 | 100.00 | 2 | 1 |
| 10 | 100.00 | 3 | 1 |
| 13 | 30.00 | 7 | 3 |

Đơn 10 có 3 dòng hàng nên `o.total` của nó xuất hiện 3 lần: 100 × 3 + 30 = 330. Còn `SUM(i.qty)` =
2 + 1 + 1 + 3 = 7 lại đúng, vì mỗi dòng hàng xuất hiện đúng một lần.

Đây là *fan-out* (nhân dòng): join từ phía "một" sang phía "nhiều" làm mỗi dòng phía "một" bị nhân
lên theo số dòng khớp ở phía "nhiều". Câu SQL không sai cú pháp, không có cảnh báo, con số trông hợp
lý. Lỗi chỉ lộ ra khi có người đối chiếu với nguồn khác.

Quy tắc để tự kiểm: sau mỗi phép join, hãy hỏi "*mỗi dòng bây giờ đại diện cho cái gì?*" (người làm
dữ liệu gọi là *grain*, độ hạt của dòng). Sau `orders JOIN order_items`, mỗi dòng là một *dòng hàng*,
không còn là một đơn. Cộng một cột của dòng hàng (`qty`) thì đúng; cộng một cột của đơn (`total`) trên
các dòng hàng thì sai.

### 10.2 Hai nhánh 1-n cùng lúc: nhân chéo

Tệ hơn khi join cùng lúc hai bảng con của cùng một cha. Yêu cầu: "với mỗi đơn đã trả, số món và số
tiền đã thu":

```sql
SELECT o.id, SUM(i.qty) AS so_mon, SUM(p.amount) AS da_tra
FROM orders o
JOIN order_items i ON i.order_id = o.id
JOIN payments    p ON p.order_id = o.id
WHERE o.status = 'paid'
GROUP BY o.id
ORDER BY o.id;
```

Kết quả sai:

| id | so_mon | da_tra |
|---|---|---|
| 10 | 8 | 300.00 |
| 13 | 3 | 30.00 |

Đơn 10 đúng ra có 4 món và đã thu 100.00. Tập dòng của đơn 10 trước khi gom: 3 dòng hàng ghép với 2
lần thanh toán thành 3 × 2 = 6 dòng.

| o.id | i.id | i.qty | p.id | p.amount |
|---|---|---|---|---|
| 10 | 1 | 2 | 1 | 60.00 |
| 10 | 1 | 2 | 2 | 40.00 |
| 10 | 2 | 1 | 1 | 60.00 |
| 10 | 2 | 1 | 2 | 40.00 |
| 10 | 3 | 1 | 1 | 60.00 |
| 10 | 3 | 1 | 2 | 40.00 |

Mỗi dòng hàng lặp 2 lần (theo số lần thanh toán) nên `so_mon` = 4 × 2 = 8; mỗi lần thanh toán lặp 3
lần (theo số dòng hàng) nên `da_tra` = 100 × 3 = 300. Hai bảng con không liên quan gì với nhau, nhưng
join qua cha chung khiến chúng thành tích Descartes của nhau trong phạm vi từng đơn. Lần này ngay cả
cột của phía "nhiều" cũng sai. Đơn 13 trông đúng chỉ vì nó có đúng 1 dòng hàng và 1 lần thanh toán:
dữ liệu test nhỏ rất dễ che lỗi này.

### 10.3 Phát hiện fan-out

So số dòng với số giá trị khác nhau của khoá phía "một":

```sql
SELECT COUNT(*) AS so_dong, COUNT(DISTINCT o.id) AS so_don
FROM orders o
JOIN order_items i ON i.order_id = o.id
WHERE o.status = 'paid';
-- so_dong = 4, so_don = 2: mỗi đơn xuất hiện nhiều lần, cộng cột của orders sẽ sai
```

Hai số khác nhau nghĩa là các dòng của `orders` đang bị nhân. Dấu hiệu trong code review: câu có
`SUM`/`COUNT`/`AVG` và có join theo chiều một sang nhiều; hoặc có hai bảng con cùng join vào một cha.

⚠️ `COUNT(DISTINCT o.id)` sửa được phép *đếm* đơn, nhưng `SUM(DISTINCT o.total)` không sửa được phép
*cộng*. `SUM(DISTINCT ...)` cộng các *giá trị* khác nhau, không phải các *đơn* khác nhau: hai đơn khác
nhau có cùng tổng tiền thì một đơn bị bỏ. Với dữ liệu hiện tại, `SUM(DISTINCT o.total)` của đơn đã trả
tình cờ ra đúng 130.00 (100 và 30 khác nhau), và đó chính là cái nguy hiểm. Thử thêm một đơn đã trả
30.00 nữa:

```sql
INSERT INTO orders VALUES (14, 3, 'paid', 30.00);
INSERT INTO order_items VALUES (8, 14, 1, 3, 10.00);

SELECT SUM(DISTINCT o.total) AS sum_distinct
FROM orders o
JOIN order_items i ON i.order_id = o.id
WHERE o.status = 'paid';
-- 130.00, trong khi doanh thu đúng là 100 + 30 + 30 = 160.00

DELETE FROM order_items WHERE id = 8;   -- dọn lại dữ liệu mẫu
DELETE FROM orders WHERE id = 14;
```

### 10.4 Cách sửa: gom phía nhiều trước rồi mới join

Nguyên tắc chung: đưa phía "nhiều" về cùng độ hạt với phía "một" *trước khi* join. Gom `order_items`
theo `order_id` thành một bảng tạm (derived table, [chương 09](09-subquery-cte-union.md)), mỗi đơn
một dòng, rồi join 1-1 với `orders`:

```sql
SELECT SUM(o.total) AS doanh_thu, SUM(x.so_mon) AS so_mon
FROM orders o
JOIN (SELECT order_id, SUM(qty) AS so_mon
      FROM order_items
      GROUP BY order_id) AS x ON x.order_id = o.id
WHERE o.status = 'paid';
```

Bảng tạm `x` có 4 dòng: (10, 4), (11, 5), (12, 2), (13, 3). Mỗi đơn khớp đúng một dòng của `x`, nên
không đơn nào bị nhân. Kết quả mong đợi:

| doanh_thu | so_mon |
|---|---|
| 130.00 | 7 |

Với hai nhánh, gom từng nhánh riêng rồi mới join:

```sql
SELECT o.id, x.so_mon, y.da_tra
FROM orders o
JOIN (SELECT order_id, SUM(qty) AS so_mon
      FROM order_items GROUP BY order_id) AS x ON x.order_id = o.id
JOIN (SELECT order_id, SUM(amount) AS da_tra
      FROM payments GROUP BY order_id) AS y ON y.order_id = o.id
WHERE o.status = 'paid'
ORDER BY o.id;
```

| id | so_mon | da_tra |
|---|---|---|
| 10 | 4 | 100.00 |
| 13 | 3 | 30.00 |

⚠️ Bảng tạm `y` chỉ có dòng cho đơn đã có thanh toán. Nếu muốn liệt kê mọi đơn, kể cả đơn chưa thu
đồng nào, phải LEFT JOIN và đổi NULL thành 0:

```sql
SELECT o.id, o.status, x.so_mon, COALESCE(y.da_tra, 0.00) AS da_tra
FROM orders o
LEFT JOIN (SELECT order_id, SUM(qty) AS so_mon
           FROM order_items GROUP BY order_id) AS x ON x.order_id = o.id
LEFT JOIN (SELECT order_id, SUM(amount) AS da_tra
           FROM payments GROUP BY order_id) AS y ON y.order_id = o.id
ORDER BY o.id;
```

| id | status | so_mon | da_tra |
|---|---|---|---|
| 10 | paid | 4 | 100.00 |
| 11 | pending | 5 | 0.00 |
| 12 | pending | 2 | 0.00 |
| 13 | paid | 3 | 30.00 |

Khi hai bảng tạm cùng có cột `order_id` ở cùng độ hạt, đây là chỗ `USING` (mục 5) hợp lý:

```sql
SELECT order_id, x.so_mon, y.da_tra
FROM (SELECT order_id, SUM(qty) AS so_mon FROM order_items GROUP BY order_id) AS x
JOIN (SELECT order_id, SUM(amount) AS da_tra FROM payments GROUP BY order_id) AS y
  USING (order_id)
ORDER BY order_id;
-- 10 | 4 | 100.00
-- 13 | 3 | 30.00     (chỉ các đơn có cả dòng hàng lẫn thanh toán)
```

Cách sửa thứ hai: subquery tương quan trong `SELECT`, mỗi số liệu một subquery, tính riêng cho từng
đơn nên không bao giờ nhân chéo:

```sql
SELECT o.id,
       (SELECT SUM(i.qty)    FROM order_items i WHERE i.order_id = o.id) AS so_mon,
       (SELECT SUM(p.amount) FROM payments    p WHERE p.order_id = o.id) AS da_tra
FROM orders o
WHERE o.status = 'paid'
ORDER BY o.id;
-- 10 | 4 | 100.00
-- 13 | 3 | 30.00
```

Đây cũng là dạng SQL mà `withCount`, `withSum` của Laravel sinh ra (mã nguồn Laravel mô tả chúng là
"subselect queries"): với model `Order` có quan hệ `items` và `payments`,
`Order::withSum('items', 'qty')->withSum('payments', 'amount')->get()` an toàn với fan-out.

Cách sửa thứ ba, cho trường hợp join chỉ để *lọc*: dùng semi-join (mục 9) thay cho join. Yêu cầu:
"doanh thu của các đơn có ít nhất một món giá từ 20.00 trở lên".

```sql
-- SAI: đơn 10 có hai món như vậy (Vở 20.00 và Balo 60.00) nên bị cộng hai lần
SELECT SUM(o.total) AS doanh_thu
FROM orders o
JOIN order_items i ON i.order_id = o.id
WHERE i.price >= 20;
-- 270.00

-- ĐÚNG: chỉ cần biết "có hay không"
SELECT SUM(o.total) AS doanh_thu
FROM orders o
WHERE EXISTS (SELECT 1 FROM order_items i
              WHERE i.order_id = o.id AND i.price >= 20);
-- 170.00 (đơn 10 và đơn 12)
```

Join để lọc là nguồn fan-out khó thấy nhất, vì người viết không hề định cộng gì của bảng con.

### 10.5 Bảng chọn cách sửa

| Tình huống | Cách sửa |
|---|---|
| Cần số liệu tổng hợp của bảng con, kèm cột của bảng cha | Gom bảng con trong derived table theo khoá cha, rồi join 1-1 |
| Cần số liệu từ hai bảng con trở lên | Gom từng bảng con riêng rồi mới join; hoặc subquery tương quan cho từng số liệu |
| Join chỉ để lọc bảng cha theo điều kiện trên bảng con | `EXISTS` / `IN` (semi-join) |
| Chỉ cần đếm số dòng cha | `COUNT(DISTINCT cha.id)` dùng được; `SUM(DISTINCT ...)` thì không |

Eager loading của Laravel (`with`) chạy query riêng cho từng quan hệ nên không bị fan-out. Nhưng
`Order::join('order_items', ...)->sum('orders.total')` thì sinh đúng câu SQL sai ở mục 10.1.

## 11. Join nhiều bảng

### 11.1 Đọc từ trái sang phải

`A JOIN B ON ... JOIN C ON ...` được hiểu là `(A JOIN B ON ...) JOIN C ON ...`: mỗi `JOIN` ghép thêm
một bảng vào tập dòng đã có. Điều kiện `ON` của join sau được dùng cột của mọi bảng đã ghép trước nó,
nhưng không được dùng cột của bảng ghép sau (tài liệu MySQL: một mệnh đề `ON` chỉ được nhắc tới các
toán hạng của nó):

```sql
SELECT *
FROM customers c
JOIN orders o ON o.customer_id = c.id AND i.qty > 1   -- i chưa được ghép tới
JOIN order_items i ON i.order_id = o.id;
-- ERROR 1054 (42S22): Unknown column 'i.qty' in 'on clause'
```

Sơ đồ quan hệ của dữ liệu mẫu, đọc `1 --<` là "một ... nhiều":

```
customers 1 --< orders 1 --< order_items >-- 1 products
                  1
                  |
                  +--< payments
```

Khi lần theo một chuỗi join, hãy theo dõi độ hạt (mục 10.1):

- Join theo chiều "nhiều sang một" (dòng hàng sang sản phẩm, đơn sang khách) không làm tăng số dòng:
  mỗi dòng hàng chỉ có đúng một sản phẩm.
- Join theo chiều "một sang nhiều" (đơn sang dòng hàng) làm số dòng tăng theo phía nhiều, và độ hạt
  đổi theo.

### 11.2 Ví dụ bốn bảng, từng bước

"Liệt kê từng món đã bán: tên khách, mã đơn, tên sản phẩm, số lượng, thành tiền":

```sql
SELECT c.name AS khach, o.id AS order_id, p.name AS san_pham,
       i.qty, i.qty * i.price AS thanh_tien
FROM orders o
JOIN order_items i   ON i.order_id = o.id
JOIN products p      ON p.id = i.product_id
LEFT JOIN customers c ON c.id = o.customer_id
ORDER BY o.id, i.id;
```

Đi từng bước:

| Bước | Tập dòng sau bước | Số dòng | Mỗi dòng là |
|---|---|---|---|
| `FROM orders o` | 4 đơn | 4 | một đơn |
| `JOIN order_items i` | mỗi đơn nhân theo số dòng hàng (3 + 1 + 2 + 1) | 7 | một dòng hàng |
| `JOIN products p` | mỗi dòng hàng gắn đúng một sản phẩm | 7 | một dòng hàng |
| `LEFT JOIN customers c` | mỗi dòng gắn khách; dòng của đơn 13 bù NULL | 7 | một dòng hàng |

Kết quả mong đợi:

| khach | order_id | san_pham | qty | thanh_tien |
|---|---|---|---|---|
| An | 10 | Bút | 2 | 20.00 |
| An | 10 | Vở | 1 | 20.00 |
| An | 10 | Balo | 1 | 60.00 |
| An | 11 | Bút | 5 | 50.00 |
| Bình | 12 | Balo | 1 | 60.00 |
| Bình | 12 | Bút | 1 | 10.00 |
| NULL | 13 | Bút | 3 | 30.00 |

`customers` được LEFT JOIN vì đơn 13 không có khách; INNER JOIN thì dòng hàng của đơn 13 biến mất
khỏi danh sách hàng đã bán. Các join còn lại là INNER vì khoá ngoại `NOT NULL` bảo đảm dòng hàng nào
cũng có đơn và sản phẩm.

`orders` và `products` là quan hệ nhiều-nhiều (một đơn nhiều sản phẩm, một sản phẩm nằm trong nhiều
đơn), và `order_items` là *bảng trung gian* (*junction table*) nối chúng. Đi từ bảng này sang bảng kia
trong quan hệ nhiều-nhiều luôn cần hai join qua bảng trung gian. Câu "sản phẩm nào chưa bán được cái
nào" là anti-join trên bảng trung gian:

```sql
SELECT p.id, p.name
FROM products p
WHERE NOT EXISTS (SELECT 1 FROM order_items i WHERE i.product_id = p.id)
ORDER BY p.id;
-- 3 Thước
```

### 11.3 Bẫy: INNER JOIN phía sau một LEFT JOIN

Yêu cầu: "mọi khách, kèm các món họ đã mua nếu có".

```sql
SELECT c.name, o.id AS order_id, i.product_id
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id
JOIN order_items i ON i.order_id = o.id        -- INNER JOIN
ORDER BY c.id, o.id, i.id;
```

Từng bước:

1. `customers LEFT JOIN orders`: 4 dòng, trong đó có (Chi, NULL) với `o.id` là NULL.
2. `JOIN order_items i ON i.order_id = o.id`: với dòng của Chi, `i.order_id = NULL` là UNKNOWN với mọi
   dòng hàng, nên dòng của Chi không có cặp, và INNER JOIN loại nó.

Kết quả có 6 dòng (An 4 dòng, Bình 2 dòng), Chi biến mất. INNER JOIN phía sau đã xoá đúng những dòng
bù NULL mà LEFT JOIN phía trước cố công giữ lại. Đây là cùng một hiện tượng với mục 4.3: điều kiện
`ON` của INNER JOIN này "từ chối NULL" đối với `orders`.

Hai cách sửa:

```sql
-- Cách A: LEFT JOIN suốt chuỗi
SELECT c.name, o.id AS order_id, i.product_id
FROM customers c
LEFT JOIN orders o      ON o.customer_id = c.id
LEFT JOIN order_items i ON i.order_id = o.id
ORDER BY c.id, o.id, i.id;

-- Cách B: nhóm phần INNER JOIN trong ngoặc, LEFT JOIN cả nhóm vào
SELECT c.name, o.id AS order_id, i.product_id
FROM customers c
LEFT JOIN (orders o JOIN order_items i ON i.order_id = o.id)
       ON o.customer_id = c.id
ORDER BY c.id, o.id, i.id;
```

Với dữ liệu mẫu, cả hai cho 7 dòng: 6 dòng như trên cộng (Chi, NULL, NULL). Chúng chỉ khác nhau khi có
đơn không có dòng hàng nào: cách A vẫn giữ đơn đó (cột dòng hàng là NULL), cách B coi "đơn không có
hàng" là không khớp, như thể khách không có đơn đó. Chọn theo ý nghĩa bạn cần.

Quy tắc: một khi bảng X đã được LEFT JOIN vào (cột của X có thể là NULL), mọi join "treo" vào X phía
sau cũng phải là LEFT JOIN, hoặc được nhóm cùng X trong ngoặc. Self join hai tầng ở mục 7.2 là một ví
dụ: đổi join thứ hai thành INNER JOIN thì chỉ còn mỗi Minh (người duy nhất có quản lý cấp 2).

Tài liệu MySQL cũng lưu ý: với join có outer join, dấu ngoặc có thể thay đổi kết quả, không được bỏ
ngoặc tuỳ tiện như với chuỗi toàn INNER JOIN.

### 11.4 Thứ tự viết và thứ tự thực thi

- Với chuỗi chỉ gồm INNER JOIN, thứ tự viết các bảng không ảnh hưởng tới kết quả. Optimizer tự chọn
  thứ tự đọc bảng mà nó ước tính là rẻ nhất, có thể khác hẳn thứ tự bạn viết.
- Với LEFT JOIN, thứ tự ảnh hưởng tới kết quả (`A LEFT JOIN B` khác `B LEFT JOIN A`), và optimizer chỉ
  xét các plan đọc bảng được giữ (bảng ngoài) trước bảng có thể bù NULL (bảng trong). Đây là một lý
  do khiến LEFT JOIN không cần thiết (dùng LEFT JOIN trong khi INNER JOIN là đủ) có thể làm query chậm
  hơn: optimizer bị bớt lựa chọn. Tuy vậy, như mục 4.3, khi `WHERE` từ chối NULL thì MySQL tự đổi nó
  thành inner join.
- `STRAIGHT_JOIN` thay cho `JOIN` buộc MySQL đọc bảng trái trước bảng phải. Tài liệu MySQL nói nó dành
  cho số ít trường hợp optimizer chọn thứ tự kém, và cảnh báo nó có thể khiến index không được dùng vì
  nó tắt các biến đổi semi-join. Ưu tiên tìm nguyên nhân (thiếu index, thống kê sai) trước khi ép thứ
  tự; xem [chương 12](12-explain-toi-uu-query.md).
- Một câu join được tham chiếu tối đa 61 bảng (kể cả bảng của view và derived table được gộp vào câu
  ngoài).

### 11.5 Trộn dấu phẩy với JOIN

`JOIN` (cùng `INNER JOIN`, `CROSS JOIN`, `LEFT JOIN`, `RIGHT JOIN`) có độ ưu tiên cao hơn dấu phẩy. Vì
vậy `t1, t2 JOIN t3` được hiểu là `t1, (t2 JOIN t3)`, không phải `(t1, t2) JOIN t3`:

```sql
SELECT c.name, o.id, i.qty
FROM customers c, orders o
JOIN order_items i ON i.order_id = o.id AND o.customer_id = c.id;
-- ERROR 1054 (42S22): Unknown column 'c.id' in 'on clause'
```

`ON` ở đây chỉ thấy hai toán hạng của nó là `orders o` và `order_items i`; `c` nằm ngoài. Cách sửa
tốt nhất là không dùng dấu phẩy nữa, viết toàn bộ bằng `JOIN ... ON`. (Thêm ngoặc
`(customers c, orders o) JOIN ...` cũng chạy, nhưng chỉ là vá.) Lỗi này hay gặp khi sửa một câu SQL
cũ viết kiểu dấu phẩy bằng cách thêm một `JOIN` vào cuối.

### 11.6 Cột join và index

Một câu join nhanh hay chậm phụ thuộc rất nhiều vào việc MySQL có tra được bảng phía sau bằng index
trên cột join hay không. Vài điểm cần biết ngay từ bây giờ (chi tiết ở [chương 11](11-index.md) và
[chương 12](12-explain-toi-uu-query.md)):

- InnoDB yêu cầu cột khoá ngoại có index, và tự tạo index nếu chưa có. Vì vậy các join theo khoá
  ngoại đã khai báo (`orders.customer_id`, `order_items.order_id`...) thường có sẵn index để tra.
- Join theo cột không có index (join theo email, theo mã tự do, theo cột không khai báo khoá ngoại)
  buộc MySQL quét nhiều hơn hẳn; MySQL 8.4 có *hash join* cho trường hợp này, nhưng với bảng lớn
  trong query phục vụ người dùng, thiếu index trên cột join thường là lỗi thiết kế.
- Hai cột đem so trong `ON` nên cùng kiểu dữ liệu (và cùng charset, collation với chuỗi). Lệch kiểu
  có thể khiến MySQL phải chuyển đổi giá trị và không dùng được index.

## 12. Đối chiếu: MySQL, PostgreSQL và Laravel

### 12.1 MySQL 8.4 so với PostgreSQL

| Điểm | MySQL 8.4 | PostgreSQL |
|---|---|---|
| INNER, LEFT, RIGHT, CROSS JOIN | Có | Có |
| `FULL [OUTER] JOIN` | Không có; giả lập bằng `UNION ALL` (mục 8.4) | Có |
| `JOIN` không có `ON` | Chạy, cho tích Descartes | Lỗi cú pháp: `INNER JOIN` phải có `ON`, `USING` hoặc `NATURAL` |
| `JOIN`, `INNER JOIN`, `CROSS JOIN` | Ba cách viết tương đương | `CROSS JOIN` không nhận điều kiện ghép |
| `USING`, `NATURAL JOIN` | Có, gộp cột chung theo chuẩn SQL | Có, cũng gộp cột chung và đặt lên đầu (cột chung theo thứ tự trong danh sách `USING`) |
| Vị trí NULL khi `ORDER BY ... ASC` | Đứng đầu | Mặc định đứng cuối |

Ngữ nghĩa cốt lõi của mọi kiểu join (mô hình ba bước, ON so với WHERE, NULL không khớp với gì) là
chuẩn SQL nên giống nhau ở cả hai. Phần khác biệt chủ yếu nằm ở cú pháp được chấp nhận và ở cách
optimizer thực thi ([chương 25](25-postgres-doi-chieu.md)).

### 12.2 Laravel query builder

| SQL | Laravel |
|---|---|
| `JOIN orders ON orders.customer_id = customers.id` | `->join('orders', 'orders.customer_id', '=', 'customers.id')` |
| `LEFT JOIN` / `RIGHT JOIN` | `->leftJoin(...)` / `->rightJoin(...)`, cùng tham số với `join` |
| `CROSS JOIN colors` | `->crossJoin('colors')` |
| Thêm điều kiện vào `ON` | Closure nhận `JoinClause`: `$join->on(...)->where(...)` (mục 4.5) |
| Join với derived table | `->joinSub($sub, 'alias', fn (JoinClause $join) => ...)`, `->leftJoinSub(...)` |
| `EXISTS` / `NOT EXISTS` | `->whereExists(...)`; với Eloquent: `has`, `whereHas`, `doesntHave`, `whereDoesntHave` |
| Số liệu tổng hợp của bảng con không fan-out | Eloquent `withCount`, `withSum`... (subquery trong `SELECT`) |

Ba điều cần nhớ khi join trong Laravel:

1. Luôn `select` cột cụ thể khi có join; `select *` làm các cột trùng tên (`id`, `created_at`...) đè
   nhau (mục 1.4).
2. `->where()` sau `->leftJoin()` là điều kiện `WHERE`, không phải `ON` (mục 4.5).
3. `->sum()`, `->count()` trên query có join theo chiều một sang nhiều là fan-out (mục 10).

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Điều kiện lọc bảng phải của LEFT JOIN đặt ở `WHERE` | `WHERE` chạy sau join, loại luôn dòng bù NULL; LEFT JOIN thành INNER JOIN | Đặt điều kiện lọc bảng phải trong `ON` (mục 4) |
| Thêm `OR b.id IS NULL` để "cứu" | Chỉ cứu dòng trái không có cặp nào; dòng trái có cặp nhưng không cặp nào thoả vẫn mất | Đưa điều kiện vào `ON` (mục 4.3) |
| Điều kiện lọc bảng trái đặt trong `ON` của LEFT JOIN | `ON` chỉ quyết định khớp hay không; dòng trái luôn được giữ | Đặt ở `WHERE` (mục 4.4) |
| INNER JOIN nối tiếp sau LEFT JOIN | `ON` của INNER JOIN loại dòng bù NULL | LEFT JOIN suốt chuỗi hoặc nhóm bằng ngoặc (mục 11.3) |
| `NOT IN (subquery)` trả về rỗng | Subquery có NULL làm mọi phép so sánh thành UNKNOWN | `NOT EXISTS`, hoặc lọc `IS NOT NULL` trong subquery (mục 9.3) |
| Anti-join kiểm `IS NULL` trên cột có thể NULL sẵn | Không phân biệt được NULL dữ liệu với dòng bù NULL | Kiểm khoá chính của bảng phải (mục 9.4) |
| `SUM` sau join một sang nhiều | Dòng phía "một" bị nhân theo số dòng phía "nhiều" | Gom phía nhiều trước rồi join, subquery tương quan, hoặc `EXISTS` (mục 10) |
| Join hai bảng con của cùng một cha rồi tổng hợp | Hai bảng con nhân chéo nhau trong từng cha | Gom từng nhánh riêng rồi mới join (mục 10.2) |
| Dùng `SUM(DISTINCT ...)` để sửa fan-out | Loại giá trị trùng, không phải dòng trùng | Không dùng; gom trước rồi join (mục 10.3) |
| `COUNT(*)` sau LEFT JOIN để đếm dòng con | Dòng bù NULL vẫn là một dòng | `COUNT(b.id)` (mục 3.4) |
| Quên `ON` hoặc dùng dấu phẩy mà quên điều kiện | Tích Descartes, m × n dòng | Luôn viết `JOIN ... ON`; kiểm số dòng kết quả (mục 6.3) |
| Trộn dấu phẩy với `JOIN` | `JOIN` ưu tiên cao hơn dấu phẩy, `ON` không thấy bảng trước dấu phẩy, lỗi 1054 | Chỉ dùng `JOIN` (mục 11.5) |
| `SELECT *` trong join rồi đọc `$row['id']` trong PHP | Hai cột cùng tên, mảng/object PHP chỉ giữ một | Chọn cột cụ thể, đặt alias (mục 1.4) |
| Viết `FULL JOIN` trên MySQL | `FULL` có thể bị hiểu là alias, câu chạy như INNER JOIN | Giả lập bằng LEFT JOIN `UNION ALL` anti-join (mục 8) |
| Giả lập FULL JOIN bằng `UNION` mà không chọn khoá | `UNION` xoá cả dòng thật trùng nhau | Chọn khoá của hai bảng, hoặc dùng `UNION ALL` với anti-join (mục 8.3, 8.4) |
| Dùng `NATURAL JOIN` | Điều kiện ghép phụ thuộc tên cột, đổi nghĩa khi schema đổi | `ON`, hoặc `USING` với danh sách cột cụ thể (mục 5.4) |
| Non-equi join với các khoảng chồng nhau | Một dòng khớp nhiều khoảng, bị nhân dòng | Khoảng "từ ... tới trước ...", kiểm dữ liệu bậc (mục 2.5) |
| Tin vào thứ tự dòng khi không có `ORDER BY` | Thứ tự không được bảo đảm, đổi theo plan | Luôn `ORDER BY` khi thứ tự có ý nghĩa (mục 1.4) |

## Tóm tắt chương

- JOIN về logic là: ghép mọi cặp dòng (tích Descartes), giữ cặp có `ON` là TRUE, rồi tuỳ kiểu join mà
  bù lại dòng không có cặp bằng NULL. MySQL không thực thi đúng như vậy, nhưng kết quả luôn như vậy.
- INNER JOIN chỉ giữ cặp khớp. LEFT JOIN giữ mọi dòng bảng trái; RIGHT JOIN ngược lại và nên viết lại
  thành LEFT JOIN. CROSS JOIN là mọi tổ hợp. FULL OUTER JOIN giữ cả hai phía; MySQL không có, giả lập
  bằng LEFT JOIN `UNION ALL` anti-join.
- Khi so bằng `=`, NULL ở cột join không khớp với bất cứ thứ gì, kể cả NULL. Self join là join một
  bảng với chính nó qua hai alias đóng hai vai.
- `ON` trả lời "dòng nào được tính là khớp", `WHERE` trả lời "dòng kết quả nào được giữ". Với LEFT
  JOIN: lọc bảng phải ở `ON`, lọc bảng trái ở `WHERE`; điều kiện trên bảng phải đặt ở `WHERE` biến LEFT
  JOIN thành INNER JOIN.
- `USING` là cách viết tắt cho phép bằng trên cột cùng tên, và gộp cột chung thành một. Tránh `NATURAL
  JOIN`.
- Semi-join ("có ít nhất một") viết bằng `EXISTS` hoặc `IN`; anti-join ("không có") viết bằng
  `NOT EXISTS` hoặc LEFT JOIN kiểm khoá chính `IS NULL`. `NOT IN` gặp NULL thì trả về rỗng.
- Join theo chiều một sang nhiều làm thay đổi độ hạt của dòng; `SUM` cột của phía "một" sau đó là
  fan-out. Sửa bằng cách gom phía nhiều trước rồi join, subquery tương quan, hoặc `EXISTS` khi chỉ
  cần lọc.
- Trong chuỗi join, sau một LEFT JOIN thì các join treo vào bảng đó cũng phải là LEFT JOIN (hoặc nhóm
  trong ngoặc). Không trộn dấu phẩy với `JOIN`.

## Câu hỏi tự kiểm tra

1. Bảng A có 5 dòng, bảng B có 4 dòng. `A CROSS JOIN B` cho bao nhiêu dòng? `A LEFT JOIN B ON ...` cho
   ít nhất và nhiều nhất bao nhiêu dòng, và khi nào đạt mỗi giới hạn? (mục 1.3, 3.1)
2. Vì sao `customers c LEFT JOIN orders o ON o.customer_id = c.id WHERE o.status = 'paid'` cho kết quả
   giống INNER JOIN? Viết lại để giữ mọi khách. (mục 4.2, 4.3)
3. Một đồng nghiệp sửa câu ở câu 2 bằng cách đổi `WHERE` thành `WHERE o.status = 'paid' OR o.id IS NULL`.
   Câu mới còn sai với khách nào trong dữ liệu mẫu, và vì sao?
4. Vì sao `WHERE c.id NOT IN (SELECT customer_id FROM orders)` trả về rỗng trên dữ liệu mẫu dù Chi chưa
   mua gì? Nêu hai cách sửa. (mục 9.3)
5. Khi viết anti-join bằng LEFT JOIN, nên kiểm `IS NULL` trên cột nào của bảng phải? Cho một ví dụ
   kiểm sai cột dẫn tới kết quả sai.
6. Câu `SELECT SUM(o.total) FROM orders o JOIN order_items i ON ...` sai ở đâu? Làm sao phát hiện
   bằng `COUNT`? Vì sao `SUM(DISTINCT o.total)` không phải cách sửa? (mục 10)
7. `USING (sku)` khác `ON a.sku = b.sku` thế nào khi `SELECT *`, và cột `sku` nhận giá trị gì ở dòng
   không khớp của LEFT JOIN? (mục 5.2)
8. Trên MySQL, câu `SELECT * FROM a FULL JOIN b USING (k)` có thể chạy mà không lỗi. Nó thực sự làm gì?
   (mục 8.2)
9. Giả lập FULL OUTER JOIN bằng `LEFT JOIN ... UNION ... RIGHT JOIN` sai trong trường hợp nào, và cách
   viết nào tránh được? (mục 8.3, 8.4)
10. Trong `customers c LEFT JOIN orders o ON ... JOIN order_items i ON i.order_id = o.id`, khách nào
    biến mất khỏi kết quả và vì sao? Nêu hai cách sửa.

## Bài tập

Làm trên database `ch07` (mục 1.2). Với mỗi bài, tự tính kết quả mong đợi bằng tay từ bảng dữ liệu
trước, rồi mới chạy để so.

1. **Doanh số theo sản phẩm.** Liệt kê mọi sản phẩm kèm tổng số lượng đã bán và tổng tiền bán được
   (`qty * price` của dòng hàng), sản phẩm chưa bán hiện 0 (không phải NULL). Sau đó viết thêm một
   phiên bản chỉ tính các đơn đã thanh toán, và kiểm tra rằng cả 4 sản phẩm vẫn xuất hiện (sản phẩm
   không nằm trong đơn đã thanh toán nào hiện 0). Gợi ý: điều kiện về trạng thái đơn đặt ở đâu?
2. **Cây nhân viên.** Với bảng `employees` ở mục 7:
   - Liệt kê mỗi người kèm số cấp dưới trực tiếp, kể cả người không có cấp dưới nào (0).
   - Liệt kê những người không quản lý ai, viết theo ba cách: `NOT EXISTS`, LEFT JOIN `IS NULL`, và
     `NOT IN (SELECT manager_id FROM employees)`. Giải thích vì sao cách thứ ba cho kết quả khác, và
     sửa nó.
3. **Báo cáo theo khách, không fan-out.** Với mỗi khách (kể cả khách chưa có đơn; không tính đơn khách
   vãng lai) in ra: số đơn, tổng tiền các đơn, tổng số món đã đặt, tổng tiền đã thu. Cả bốn cột phải
   đúng; khách không có gì hiện 0. Sau đó chạy
   `INSERT INTO payments VALUES (4, 11, 20.00);` và kiểm tra rằng chỉ đúng một con số của An thay đổi,
   đúng 20.00. Dọn lại bằng `DELETE FROM payments WHERE id = 4;`.
4. **Đối soát hai nguồn.** Tạo hai bảng `bank_tx(ref VARCHAR(20) PRIMARY KEY, amount DECIMAL(10,2))` và
   `app_payments(ref VARCHAR(20) PRIMARY KEY, amount DECIMAL(10,2))`, chèn khoảng 5 dòng mỗi bảng sao
   cho có: giao dịch chỉ có ở ngân hàng, giao dịch chỉ có ở app, giao dịch có ở cả hai và khớp tiền,
   giao dịch có ở cả hai nhưng lệch tiền. Viết một câu trên MySQL (giả lập FULL OUTER JOIN) trả về mỗi
   giao dịch một dòng với cột `ket_luan` là `'chi_ngan_hang'`, `'chi_app'`, `'lech_tien'` hoặc `'khop'`.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [JOIN Clause](https://dev.mysql.com/doc/refman/8.4/en/join.html) ·
  [Outer Join Optimization](https://dev.mysql.com/doc/refman/8.4/en/outer-join-optimization.html) ·
  [Outer Join Simplification](https://dev.mysql.com/doc/refman/8.4/en/outer-join-simplification.html) ·
  [Nested Join Optimization](https://dev.mysql.com/doc/refman/8.4/en/nested-join-optimization.html) ·
  [Semijoin and Antijoin Transformations](https://dev.mysql.com/doc/refman/8.4/en/semijoins-antijoins.html) ·
  [Subqueries with EXISTS or NOT EXISTS](https://dev.mysql.com/doc/refman/8.4/en/exists-and-not-exists-subqueries.html) ·
  [Subqueries with ALL](https://dev.mysql.com/doc/refman/8.4/en/all-subqueries.html) ·
  [Set Operations with UNION, INTERSECT, and EXCEPT](https://dev.mysql.com/doc/refman/8.4/en/set-operations.html) ·
  [Hash Join Optimization](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html) ·
  [FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html) ·
  [Keywords and Reserved Words](https://dev.mysql.com/doc/refman/8.4/en/keywords.html)
- [MySQL Bug #69858: Make FULL a reserved word](https://bugs.mysql.com/bug.php?id=69858) và
  [MySQL 8.0.32 Release Notes](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-32.html)
  (deprecate `FULL` làm identifier không có dấu nháy).
- PostgreSQL 18: [Table Expressions, Joined Tables](https://www.postgresql.org/docs/18/queries-table-expressions.html) ·
  [Sorting Rows (NULLS FIRST/LAST)](https://www.postgresql.org/docs/18/queries-order.html)
- PHP manual: [PDO fetch modes, Handling of Duplicated Column Names](https://www.php.net/manual/en/pdo.constants.fetch-modes.php)
- Laravel 13.x: [Query Builder, Joins](https://laravel.com/docs/13.x/queries#joins) ·
  [Eloquent Relationships (eager loading, `withCount`, `withSum`)](https://laravel.com/docs/13.x/eloquent-relationships)
- Markus Winand, Use The Index, Luke: [The Join Operation](https://use-the-index-luke.com/sql/join),
  cách các thuật toán join dùng index (đọc kèm [chương 11](11-index.md), [chương 12](12-explain-toi-uu-query.md)).
