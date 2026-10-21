# Chương 09. Subquery, CTE, UNION

> [← Mục lục](README.md) · [← Chương 08: Gom nhóm và hàm tổng hợp](08-group-by-aggregate.md) · [Chương 10: Window function →](10-window-function.md)

**Bạn sẽ học được:**

- Viết một câu `SELECT` lồng trong câu khác (subquery) ở mọi vị trí: trong `WHERE`, trong danh sách `SELECT`, trong `FROM`, và biết mỗi vị trí đòi subquery trả về hình dạng gì.
- Dùng đúng `IN`, `EXISTS`, `ANY`, `ALL`; hiểu vì sao `NOT IN` gặp một giá trị NULL là trả về tập rỗng.
- Phân biệt subquery độc lập với correlated subquery, ước lượng được chi phí, và biết optimizer MySQL viết lại subquery ra sao.
- Đặt tên cho các bước trung gian bằng CTE (`WITH`), dùng recursive CTE để duyệt cây và sinh dãy số, dãy ngày, kèm cách chặn đệ quy vô hạn.
- Ghép kết quả của nhiều câu `SELECT` bằng `UNION`, `UNION ALL`, `INTERSECT`, `EXCEPT`.
- Viết "có rồi thì sửa, chưa có thì thêm" trong một câu lệnh: `INSERT ... ON DUPLICATE KEY UPDATE`, `REPLACE`, `INSERT IGNORE`, và đối chiếu với `ON CONFLICT` của PostgreSQL.

**Cần biết trước:** [Chương 05](05-select-co-ban.md) (`SELECT`, `WHERE`, `ORDER BY`, `LIMIT`), [Chương 06](06-ham-bieu-thuc-null.md) (NULL và logic ba giá trị), [Chương 07](07-join.md) (JOIN), [Chương 08](08-group-by-aggregate.md) (`GROUP BY`, hàm tổng hợp). Phần upsert cần thêm [Chương 04](04-ddl-constraint.md) (`PRIMARY KEY`, `UNIQUE`).

## 1. Dữ liệu mẫu của chương

Mọi ví dụ trong chương chạy trên bộ dữ liệu dưới đây (trừ phần upsert ở mục 11 và 12, có bảng riêng).
Mở client `mysql` như ở chương 01. Nếu dùng Docker:

```bash
# Chạy trên máy của bạn (terminal thường)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
docker exec -it my84 mysql -uroot -proot      # đợi vài giây cho server khởi động xong
```

Rồi dán đoạn SQL sau vào client `mysql`:

```sql
DROP DATABASE IF EXISTS ch09;      -- database riêng của chương này, xoá đi tạo lại cho sạch
CREATE DATABASE ch09;
USE ch09;

CREATE TABLE customers (
  id   INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  city VARCHAR(50) NOT NULL
);

CREATE TABLE orders (
  id          INT PRIMARY KEY,
  customer_id INT NULL,              -- NULL: đơn của khách vãng lai (mua không cần tài khoản)
  order_date  DATE NOT NULL,
  status      VARCHAR(10) NOT NULL,  -- 'paid', 'pending', 'cancelled'
  total       INT NOT NULL,          -- đơn vị: nghìn đồng
  INDEX idx_orders_customer (customer_id),
  CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers (id)
);

CREATE TABLE suppliers (
  id   INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL,
  city VARCHAR(50) NOT NULL
);

CREATE TABLE categories (
  id        INT PRIMARY KEY,
  parent_id INT NULL,                -- NULL: danh mục gốc
  name      VARCHAR(50) NOT NULL,
  INDEX idx_categories_parent (parent_id),
  CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES categories (id)
);

INSERT INTO customers VALUES
  (1, 'An',   'Hà Nội'),
  (2, 'Bình', 'Đà Nẵng'),
  (3, 'Chi',  'Hà Nội'),
  (4, 'Dũng', 'Huế');

INSERT INTO orders VALUES
  (101, 1,    '2026-01-05', 'paid',      300),
  (102, 1,    '2026-02-10', 'paid',      150),
  (103, 2,    '2026-01-20', 'paid',      500),
  (104, 2,    '2026-02-15', 'cancelled',  80),
  (105, 3,    '2026-02-20', 'pending',   170),
  (106, NULL, '2026-02-25', 'paid',       60);

INSERT INTO suppliers VALUES
  (1, 'NCC Sao Mai',   'Hà Nội'),
  (2, 'NCC Bến Thành', 'Hồ Chí Minh'),
  (3, 'NCC Hàn Giang', 'Đà Nẵng');

INSERT INTO categories VALUES
  (1, NULL, 'Điện tử'),
  (2, 1,    'Điện thoại'),
  (3, 2,    'Android'),
  (4, 2,    'iPhone'),
  (5, 1,    'Laptop'),
  (6, NULL, 'Sách'),
  (7, 6,    'Lập trình');
```

Vài con số nên nhớ vì chúng sẽ xuất hiện liên tục, bạn có thể tự cộng lại để kiểm tra:

| Đại lượng | Giá trị |
|---|---|
| Tổng `total` của 6 đơn | 300 + 150 + 500 + 80 + 170 + 60 = 1260 |
| Trung bình `total` mỗi đơn | 1260 / 6 = 210 |
| Tổng theo khách | An (1): 450, Bình (2): 580, Chi (3): 170, khách vãng lai (NULL): 60 |
| Khách chưa có đơn nào | Dũng (4) |

Hai chi tiết được cài cố ý để lộ ra cạm bẫy ở các mục sau: Dũng không có đơn nào, và đơn 106 có
`customer_id` là NULL. Cây danh mục trong bảng `categories` trông như sau:

```
Điện tử (1)
├── Điện thoại (2)
│   ├── Android (3)
│   └── iPhone (4)
└── Laptop (5)
Sách (6)
└── Lập trình (7)
```

## 2. Subquery là gì

### 2.1 Câu hỏi cần hai bước

Câu hỏi: "Những đơn nào có giá trị lớn hơn mức trung bình?". Để trả lời, ta phải làm hai bước: tính
trung bình trước, rồi mới lọc. Cách ngây thơ là chạy hai câu và chép tay con số ở giữa:

```sql
SELECT AVG(total) FROM orders;                    -- bước 1: ra 210
SELECT id, total FROM orders WHERE total > 210;   -- bước 2: chép tay con số 210 vào
```

Cách này có ba vấn đề: hai lần đi lại giữa ứng dụng và database; con số bị chép tay sẽ sai ngay khi
có đơn mới; và giữa hai câu, dữ liệu có thể đã bị người khác thay đổi.

Bạn cũng không thể viết gộp là `WHERE total > AVG(total)`. MySQL báo
`ERROR 1111 (HY000): Invalid use of group function`, vì như chương 08 đã giải thích, `WHERE` chạy
trước khi gom nhóm nên lúc đó chưa có "trung bình" nào cả.

*Subquery* (truy vấn con) giải quyết đúng chỗ này: nó là một câu `SELECT` nằm bên trong một câu lệnh
khác. Câu bên ngoài gọi là *outer query* (truy vấn ngoài).

```sql
SELECT id, total
FROM orders
WHERE total > (SELECT AVG(total) FROM orders);
```

```
+-----+-------+
| id  | total |
+-----+-------+
| 101 |   300 |
| 103 |   500 |
+-----+-------+
```

Về logic, DB tính subquery `(SELECT AVG(total) FROM orders)` ra 210, rồi dùng con số đó như một hằng
số cho câu ngoài. Tất cả nằm trong một câu lệnh, nên cũng nằm trong một lần đọc dữ liệu nhất quán.

### 2.2 Subquery đặt ở đâu

Tài liệu MySQL định nghĩa rất gọn: subquery là một câu `SELECT` nằm trong một câu lệnh khác, và câu
lệnh ngoài có thể là `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `SET` hoặc `DO`. Subquery luôn phải nằm
trong cặp ngoặc tròn, và có thể lồng subquery trong subquery nhiều tầng.

Bên trong subquery bạn viết gần như mọi thứ một câu `SELECT` bình thường có: `DISTINCT`, `GROUP BY`,
`ORDER BY`, `LIMIT`, JOIN, `UNION`, hàm... (có vài ngoại lệ, sẽ nêu ở chỗ liên quan).

Các vị trí hay gặp nhất:

```sql
SELECT c.name,
       (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS so_don    -- (1) trong danh sách SELECT
FROM customers c
JOIN (SELECT customer_id, SUM(total) AS tong
      FROM orders GROUP BY customer_id) AS t ON t.customer_id = c.id          -- (2) trong FROM
WHERE c.id IN (SELECT customer_id FROM orders WHERE status = 'paid');         -- (3) trong WHERE
```

| Vị trí | Tên gọi thường dùng | Đọc ở mục |
|---|---|---|
| (1) Danh sách `SELECT` | Scalar subquery, thường là correlated | 3.3 |
| (2) Mệnh đề `FROM` | *Derived table* (bảng dẫn xuất) | 7 |
| (3) `WHERE` hoặc `HAVING` | Subquery làm điều kiện: so sánh, `IN`, `EXISTS`, `ANY`, `ALL` | 3, 4, 5 |

Ngoài ra subquery còn xuất hiện trong `UPDATE ... SET cot = (SELECT ...)`, `DELETE ... WHERE id IN
(SELECT ...)`, `INSERT INTO ... SELECT ...` (mục 6.5 nói về một hạn chế quan trọng của MySQL ở đây).

⚠️ Có vài chỗ chỉ nhận hằng số, và subquery không dùng được ở đó. Ví dụ tài liệu MySQL nêu: `LIMIT`
chỉ nhận số nguyên viết thẳng, nên `LIMIT (SELECT ...)` là lỗi.

### 2.3 Bốn hình dạng kết quả

Một câu `SELECT` trả về một bảng: có số dòng và số cột. Tài liệu MySQL chia subquery theo hình dạng
kết quả thành bốn loại, và mỗi loại chỉ dùng được ở một số chỗ:

| Loại | Trả về | Dùng với | Ví dụ |
|---|---|---|---|
| *Scalar subquery* | 1 dòng, 1 cột (một giá trị) | Gần như mọi chỗ đặt được một giá trị: `=`, `>`, hàm, danh sách `SELECT` | `(SELECT AVG(total) FROM orders)` |
| *Row subquery* | 1 dòng, nhiều cột | So sánh với một bộ giá trị `(a, b)` | `(customer_id, status) = (SELECT customer_id, status FROM ...)` |
| *Column subquery* | Nhiều dòng, 1 cột | `IN`, `ANY`, `ALL` | `id IN (SELECT customer_id FROM orders)` |
| *Table subquery* | Nhiều dòng, nhiều cột | `FROM` (derived table), `EXISTS`, `(a, b) IN (...)` | `FROM (SELECT ...) AS t` |

Hình dạng là thứ DB kiểm tra khi chạy: bạn đặt một subquery trả về hai dòng vào chỗ cần một giá trị
thì nhận lỗi (mục 3.2). Vì vậy trước khi viết subquery, hãy tự hỏi: "chỗ này cần một giá trị, một
cột, hay một bảng?".

### 2.4 Subquery độc lập và correlated subquery

Subquery ở mục 2.1 là *subquery độc lập* (non-correlated): nó không nhắc gì tới bảng của câu ngoài.
Bạn có thể cắt nó ra chạy riêng và nhận cùng kết quả 210. Về logic, nó chỉ cần tính một lần.

Subquery (1) trong ví dụ mục 2.2 thì khác:

```sql
(SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id)
```

Nó nhắc tới `c.id`, một cột của bảng `customers` ở câu ngoài. Cắt riêng ra thì không chạy được, vì
`c` là gì? Loại này gọi là *correlated subquery* (subquery tương quan): về logic, nó được tính lại cho
mỗi dòng của câu ngoài, mỗi lần với một giá trị `c.id` khác. Đây là nguồn gốc của câu "subquery chậm",
và cũng là chỗ optimizer làm nhiều việc nhất để tránh đúng điều đó. Mục 6 đi sâu vào chi phí và cách
MySQL xử lý.

| | Subquery độc lập | Correlated subquery |
|---|---|---|
| Nhắc tới cột câu ngoài? | Không | Có |
| Chạy riêng được? | Được | Không |
| Số lần tính về logic | Một lần | Một lần cho mỗi dòng ngoài |
| Ví dụ | `total > (SELECT AVG(total) FROM orders)` | `(SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id)` |

## 3. Scalar subquery: subquery trả về một giá trị

### 3.1 So sánh với một giá trị được tính ra

Scalar subquery là dạng đơn giản nhất: kết quả có đúng một dòng và một cột. Tài liệu MySQL mô tả nó
là một toán hạng bình thường, đặt được ở hầu hết những chỗ một giá trị cột hay một hằng số đặt được.

Dạng hay gặp nhất là `toán_hạng phép_so_sánh (subquery)`, với phép so sánh là một trong
`=  >  <  >=  <=  <>  !=  <=>`. Vài ví dụ trên dữ liệu mẫu:

```sql
-- Đơn mới nhất
SELECT id, order_date
FROM orders
WHERE order_date = (SELECT MAX(order_date) FROM orders);
-- 106  2026-02-25

-- Khách ở cùng thành phố với An (id = 1)
SELECT id, name
FROM customers
WHERE city = (SELECT city FROM customers WHERE id = 1)
ORDER BY id;
-- 1  An
-- 3  Chi
```

Câu thứ hai trả về cả An, vì An cũng ở Hà Nội. Muốn bỏ An thì thêm `AND id <> 1`.

Câu thứ nhất là kiểu câu hỏi mà tài liệu MySQL gọi là "không làm được bằng JOIN": nó cần tổng hợp cả
bảng (`MAX`) trước rồi mới so sánh từng dòng với kết quả đó.

### 3.2 Không có dòng thì NULL, nhiều dòng thì lỗi

Hai tình huống bất thường, và DB xử lý chúng rất khác nhau.

Trường hợp 1: subquery không trả về dòng nào. Khi đó giá trị của nó là NULL.

```sql
SELECT (SELECT city FROM customers WHERE name = 'Zoe') AS thanh_pho;
-- NULL

SELECT id, name
FROM customers
WHERE city = (SELECT city FROM customers WHERE name = 'Zoe');
-- Empty set
```

Câu thứ hai không lỗi, chỉ ra tập rỗng: `city = NULL` cho UNKNOWN với mọi dòng, và `WHERE` chỉ giữ
dòng TRUE (chương 06). Chú ý: cột `city` khai báo `NOT NULL`, nhưng scalar subquery trên cột đó vẫn có
thể ra NULL. Tài liệu MySQL nói rõ: tính chất "có thể NULL" không được chép từ cột sang subquery, vì
subquery rỗng luôn cho NULL.

Trường hợp 2: subquery trả về nhiều hơn một dòng. Đây là lỗi lúc chạy:

```sql
SELECT id, name
FROM customers
WHERE city = (SELECT city FROM customers WHERE id IN (1, 2));
-- ERROR 1242 (21000): Subquery returns more than 1 row
```

Tương tự, subquery trả về nhiều hơn một cột ở chỗ cần một giá trị:

```sql
SELECT (SELECT id, name FROM customers WHERE id = 1);
-- ERROR 1241 (21000): Operand should contain 1 column(s)
```

⚠️ Lỗi 1242 nguy hiểm vì nó phụ thuộc dữ liệu, không phụ thuộc cú pháp. Câu
`WHERE customer_id = (SELECT id FROM customers WHERE name = 'An')` chạy tốt suốt thời gian phát triển,
rồi một ngày có khách thứ hai tên An và trang web bắt đầu trả lỗi 500. Cách phòng:

- Chỉ dùng scalar subquery trên điều kiện chắc chắn ra tối đa một dòng: lọc theo `PRIMARY KEY` hoặc cột
  có `UNIQUE`. Ràng buộc trong schema là bảo đảm, còn "hiện tại dữ liệu chỉ có một dòng" thì không.
- Nếu thật sự chỉ muốn một giá trị trong nhiều giá trị, hãy nói rõ là giá trị nào: dùng hàm tổng hợp
  (`MAX`, `MIN`), hoặc `ORDER BY ... LIMIT 1`. `LIMIT` được phép trong scalar subquery; hạn chế về
  `LIMIT` chỉ áp dụng cho subquery đi với `IN`, `ANY`, `ALL`, `SOME` (mục 4.1).
- Nếu nhiều giá trị là hợp lệ, đổi phép so sánh thành `IN` (mục 4).

### 3.3 Scalar subquery trong danh sách SELECT

Đặt scalar subquery trong danh sách `SELECT` để tính thêm một cột cho mỗi dòng. Gần như luôn là
correlated subquery:

```sql
SELECT c.id, c.name,
       (SELECT COUNT(*)   FROM orders o WHERE o.customer_id = c.id) AS so_don,
       (SELECT SUM(total) FROM orders o WHERE o.customer_id = c.id) AS tong_tien
FROM customers c
ORDER BY c.id;
```

```
+----+------+--------+-----------+
| id | name | so_don | tong_tien |
+----+------+--------+-----------+
|  1 | An   |      2 |       450 |
|  2 | Bình |      2 |       580 |
|  3 | Chi  |      1 |       170 |
|  4 | Dũng |      0 |      NULL |
+----+------+--------+-----------+
```

Nhìn dòng của Dũng: `so_don` là 0 nhưng `tong_tien` là NULL. Lý do: một câu có hàm tổng hợp mà không
có `GROUP BY` luôn trả về đúng một dòng, kể cả khi không có dòng nào để gom. Trên tập rỗng, `COUNT`
cho 0, còn `SUM`, `AVG`, `MIN`, `MAX` cho NULL (chương 08). Muốn hiển thị 0 thì bọc
`COALESCE((SELECT SUM(total) ...), 0)`.

⚠️ Hai cạm bẫy của kiểu viết này:

- Subquery trong `SELECT` phải ra tối đa một dòng cho mỗi dòng ngoài. Viết
  `(SELECT id FROM orders o WHERE o.customer_id = c.id)` sẽ lỗi 1242 ngay khi gặp khách có hai đơn.
- Mỗi subquery là một lần tra cứu riêng cho mỗi dòng ngoài. Câu trên có hai subquery cùng đọc bảng
  `orders` theo cùng điều kiện, tức về logic là 2 lần tra cứu cho mỗi khách. Với vài trăm dòng thì không
  sao; khi trang danh sách hiển thị nhiều cột kiểu này trên hàng chục nghìn dòng thì nên viết lại bằng
  một derived table gom một lần (mục 7.3).

### 3.4 Row subquery: so sánh nhiều cột một lúc

*Row subquery* trả về một dòng có nhiều cột. Nó được so sánh với một *row constructor* (bộ giá trị),
viết `(a, b)` hoặc `ROW(a, b)`, hai cách viết tương đương.

```sql
-- Các đơn cùng khách và cùng trạng thái với đơn 101
SELECT id, customer_id, status
FROM orders
WHERE (customer_id, status) = (SELECT customer_id, status FROM orders WHERE id = 101)
ORDER BY id;
-- 101  1  paid
-- 102  1  paid
```

`(a, b) = (x, y)` nghĩa là `a = x AND b = y`. Đơn 106 có `(NULL, 'paid')`: `NULL = 1` là UNKNOWN, nên
cả biểu thức không TRUE và đơn 106 bị loại. Quy tắc giống scalar subquery: row subquery đi với `=` phải
ra tối đa một dòng (nhiều dòng thì lỗi), và ra không dòng nào thì kết quả so sánh là UNKNOWN.

Khi subquery trả về nhiều dòng nhiều cột, dùng row constructor với `IN`. Ví dụ "đơn mới nhất của mỗi
khách":

```sql
SELECT id, customer_id, order_date
FROM orders
WHERE (customer_id, order_date) IN (
  SELECT customer_id, MAX(order_date) FROM orders GROUP BY customer_id
)
ORDER BY id;
```

Subquery trả về bốn cặp: `(1, 2026-02-10)`, `(2, 2026-02-15)`, `(3, 2026-02-20)`,
`(NULL, 2026-02-25)`. Kết quả:

```
+-----+-------------+------------+
| id  | customer_id | order_date |
+-----+-------------+------------+
| 102 |           1 | 2026-02-10 |
| 104 |           2 | 2026-02-15 |
| 105 |           3 | 2026-02-20 |
+-----+-------------+------------+
```

Đơn 106 vắng mặt dù nhóm NULL có trong subquery, vì `(NULL, ...) = (NULL, ...)` vẫn là UNKNOWN. `GROUP
BY` gom các NULL vào một nhóm, nhưng phép `=` thì không bao giờ coi hai NULL là bằng nhau.

⚠️ MySQL chỉ hỗ trợ so sánh nhiều cột với `=`, `IN` và các phép so sánh thường. Dạng
`(a, b) > ANY (SELECT ...)`, tức row constructor đi với `ANY`, `ALL`, `SOME`, không được hỗ trợ: với
ba từ khoá này, vế trái phải là một giá trị đơn và subquery phải trả về một cột.

## 4. Subquery trả về một tập: IN, ANY, ALL

### 4.1 IN: "có nằm trong tập không"

Khi subquery trả về một cột nhiều dòng (column subquery), bạn không so sánh bằng `=` được nữa mà hỏi
"giá trị có nằm trong tập này không":

```sql
-- Khách có ít nhất một đơn đã thanh toán
SELECT id, name
FROM customers
WHERE id IN (SELECT customer_id FROM orders WHERE status = 'paid')
ORDER BY id;
-- 1  An
-- 2  Bình
```

Subquery trả về cột gồm `1, 1, 2, NULL` (từ các đơn 101, 102, 103, 106). Giá trị lặp lại không quan
trọng: `IN` chỉ hỏi có hay không.

Theo tài liệu MySQL, `IN` đi với subquery là tên gọi khác của `= ANY` (mục 4.4). Nhưng `IN` còn nhận
được danh sách hằng `IN (1, 2, 3)`, còn `= ANY (1, 2, 3)` thì không hợp lệ.

⚠️ MySQL không cho dùng `LIMIT` trong subquery đi với `IN`, `ALL`, `ANY`, `SOME`:

```sql
-- Khách sở hữu 2 đơn lớn nhất
SELECT id, name FROM customers
WHERE id IN (SELECT customer_id FROM orders ORDER BY total DESC LIMIT 2);
-- ERROR 1235 (42000): This version of MySQL doesn't yet support 'LIMIT & IN/ALL/ANY/SOME subquery'
```

Cách lách thường dùng: bọc phần có `LIMIT` vào một derived table (mục 7), để `IN` đọc từ bảng tạm đó:

```sql
SELECT id, name FROM customers
WHERE id IN (
  SELECT customer_id FROM (
    SELECT customer_id FROM orders ORDER BY total DESC LIMIT 2
  ) AS top2
)
ORDER BY id;
-- 1  An     (đơn 101, 300)
-- 2  Bình   (đơn 103, 500)
```

### 4.2 IN khác JOIN ở chỗ nào

Viết lại câu ở mục 4.1 bằng JOIN:

```sql
SELECT c.id, c.name
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.status = 'paid'
ORDER BY c.id;
-- 1  An
-- 1  An
-- 2  Bình
```

An xuất hiện hai lần, vì JOIN tạo một dòng cho mỗi cặp (khách, đơn) khớp nhau và An có hai đơn đã
thanh toán. `IN` thì khác về bản chất: mỗi dòng của `customers` xuất hiện tối đa một lần, dù có bao
nhiêu đơn khớp. Phép "giữ dòng bên trái nếu có ít nhất một dòng bên phải khớp, và giữ đúng một lần"
có tên là *semijoin*.

Thêm `DISTINCT` vào câu JOIN cũng cho kết quả đúng ở ví dụ này, nhưng đó là đi đường vòng: tạo dòng
trùng rồi bỏ đi (tốn thêm một bước sort hoặc hash), và nếu danh sách cột không chứa khoá
(`SELECT DISTINCT c.name` khi có hai khách khác nhau cùng tên) thì `DISTINCT` gộp nhầm hai người làm
một. Khi câu hỏi là "dòng nào có liên quan tới bảng kia", hãy viết `IN` hoặc `EXISTS` để nói đúng ý.
Khi cần lấy cột của bảng kia ra hiển thị, đó mới là việc của JOIN.

### 4.3 NOT IN và cái bẫy NULL

Câu hỏi: "Khách nào chưa có đơn nào?". Trên dữ liệu mẫu, đáp án là Dũng. Cách viết tự nhiên nhất:

```sql
SELECT id, name
FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders);
-- Empty set
```

Kết quả rỗng, không có lỗi nào, và đây là loại bug nguy hiểm nhất: sai mà im lặng. Thủ phạm là đơn
106 của khách vãng lai. Subquery trả về `1, 1, 2, 2, 3, NULL`, và `x NOT IN (...)` được tính như một
chuỗi `<>` nối bằng `AND` (tài liệu MySQL ghi `NOT IN` là tên khác của `<> ALL`):

```
4 NOT IN (1, 1, 2, 2, 3, NULL)
= 4<>1  AND 4<>1  AND 4<>2  AND 4<>2  AND 4<>3  AND 4<>NULL
= TRUE  AND TRUE  AND TRUE  AND TRUE  AND TRUE  AND UNKNOWN
= UNKNOWN
```

| Khách | `id NOT IN (1, 1, 2, 2, 3, NULL)` | Được giữ? |
|---|---|---|
| An (1) | FALSE, vì `1 <> 1` là FALSE | Không |
| Bình (2) | FALSE | Không |
| Chi (3) | FALSE | Không |
| Dũng (4) | UNKNOWN, vì `4 <> NULL` là UNKNOWN | Không |

Chỉ cần subquery có một NULL, `NOT IN` không bao giờ cho TRUE với bất kỳ dòng nào, nên kết quả luôn
rỗng. Hai cách sửa:

```sql
-- Cách 1: loại NULL ngay trong subquery
SELECT id, name FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL);
-- 4  Dũng

-- Cách 2 (nên dùng): NOT EXISTS, xem mục 5.2
SELECT c.id, c.name FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
-- 4  Dũng
```

NULL ở vế trái cũng gây bất ngờ. Câu hỏi ngược: "Đơn nào không thuộc về khách hàng nào?". Đáp án mong
đợi là đơn 106.

```sql
SELECT id FROM orders
WHERE customer_id NOT IN (SELECT id FROM customers);
-- Empty set: với đơn 106, NULL NOT IN (1, 2, 3, 4) là UNKNOWN

SELECT o.id FROM orders o
WHERE NOT EXISTS (SELECT 1 FROM customers c WHERE c.id = o.customer_id);
-- 106
```

⚠️ Đừng tự trấn an "cột của tôi không có NULL". Hôm nay cột có thể `NOT NULL`, nhưng mai có người sửa
schema cho phép NULL, hoặc subquery được sửa thành có `LEFT JOIN` sinh ra NULL. Thói quen an toàn: viết
anti-join (lấy dòng không có dòng tương ứng) bằng `NOT EXISTS`.

### 4.4 ANY (SOME) và ALL

`ANY` và `ALL` mở rộng `IN` cho các phép so sánh khác ngoài `=`. Cả hai phải đứng sau một phép so sánh:

- `x > ANY (subquery)`: TRUE nếu phép so sánh TRUE với ít nhất một giá trị trong tập. `SOME` là tên
  khác của `ANY`.
- `x > ALL (subquery)`: TRUE nếu phép so sánh TRUE với mọi giá trị trong tập.

Ví dụ với tập là các đơn của Bình, gồm hai giá trị 500 và 80:

```sql
-- Đơn lớn hơn ÍT NHẤT MỘT đơn của Bình, tức lớn hơn 80
SELECT id, total FROM orders
WHERE total > ANY (SELECT total FROM orders WHERE customer_id = 2)
ORDER BY id;
-- 101  300
-- 102  150
-- 103  500
-- 105  170

-- Đơn lớn hơn MỌI đơn của Bình, tức lớn hơn 500
SELECT id, total FROM orders
WHERE total > ALL (SELECT total FROM orders WHERE customer_id = 2);
-- Empty set

-- Đơn nhỏ hơn mọi đơn của Bình, tức nhỏ hơn 80
SELECT id, total FROM orders
WHERE total < ALL (SELECT total FROM orders WHERE customer_id = 2);
-- 106  60
```

Bảng quy đổi để dễ nhớ:

| Viết | Nghĩa | Tương đương (khi tập không rỗng và không có NULL) |
|---|---|---|
| `x = ANY (S)` | Bằng ít nhất một phần tử | `x IN (S)` |
| `x <> ALL (S)` | Khác mọi phần tử | `x NOT IN (S)` |
| `x > ANY (S)` | Lớn hơn ít nhất một phần tử | `x > (SELECT MIN(...))` |
| `x > ALL (S)` | Lớn hơn mọi phần tử | `x > (SELECT MAX(...))` |
| `x <> ANY (S)` | Khác ít nhất một phần tử | Không phải `NOT IN`! |

⚠️ `x <> ANY (S)` là cái bẫy ngôn ngữ. Đọc "x khác bất kỳ phần tử nào" thì tưởng là `NOT IN`, nhưng
nghĩa thật là "có ít nhất một phần tử khác x", tức gần như luôn TRUE khi tập có từ hai giá trị khác
nhau trở lên. Tài liệu MySQL nhấn mạnh: `NOT IN` là tên khác của `<> ALL`, không phải của `<> ANY`, và
gợi ý viết `<> SOME` nếu bạn thật sự muốn nghĩa "khác ít nhất một" để người đọc không hiểu nhầm.

### 4.5 ALL với tập rỗng và với NULL

Cột "tương đương" trong bảng trên có điều kiện đi kèm, và chính hai trường hợp ngoài điều kiện đó là
chỗ hay sai.

Tập rỗng. Dũng không có đơn nào:

```sql
SELECT id, total FROM orders
WHERE total > ALL (SELECT total FROM orders WHERE customer_id = 4);
-- trả về cả 6 đơn

SELECT id, total FROM orders
WHERE total > (SELECT MAX(total) FROM orders WHERE customer_id = 4);
-- Empty set
```

`ALL` trên tập rỗng là TRUE (không có phần tử nào làm điều kiện sai, giống mệnh đề "mọi con kỳ lân đều
màu tím" đúng vì không có con kỳ lân nào). Còn `MAX` trên tập rỗng là NULL, so sánh với NULL là
UNKNOWN. Tài liệu MySQL có ví dụ cùng ý: `1 > ALL (subquery rỗng)` là TRUE, còn
`1 > (subquery rỗng)` là NULL. Ngược lại, `ANY` trên tập rỗng là FALSE.

Tập có NULL. Cột `customer_id` của `orders` gồm `1, 1, 2, 2, 3, NULL`:

```sql
SELECT 10 > ALL (SELECT customer_id FROM orders) AS a,   -- NULL: lớn hơn mọi số, nhưng 10 > NULL là UNKNOWN
       2  > ALL (SELECT customer_id FROM orders) AS b,   -- 0: 2 > 2 là FALSE, đủ để kết luận
       10 > ANY (SELECT customer_id FROM orders) AS c,   -- 1: 10 > 1 là TRUE, đủ để kết luận
       0  > ANY (SELECT customer_id FROM orders) AS d;   -- NULL: không số nào nhỏ hơn 0, còn lại NULL
```

MySQL in TRUE là `1`, FALSE là `0`, UNKNOWN là `NULL`. Quy luật: một NULL trong tập làm kết quả thành
UNKNOWN trừ khi các phần tử khác đã đủ để kết luận.

Bảng tổng kết cho các phép trên tập (x khác NULL):

| Biểu thức | Tập rỗng | Tập có NULL, các phần tử còn lại không đủ để kết luận |
|---|---|---|
| `x IN (S)`, `x = ANY (S)` | FALSE | UNKNOWN |
| `x NOT IN (S)`, `x <> ALL (S)` | TRUE | UNKNOWN |
| `x > ANY (S)` | FALSE | UNKNOWN |
| `x > ALL (S)` | TRUE | UNKNOWN |
| `EXISTS (S)` | FALSE | TRUE (tập có dòng, dù dòng đó chứa NULL) |

Còn khi chính x là NULL: theo tài liệu MySQL, `NULL IN (subquery)` là NULL nếu subquery có ít nhất một
dòng, và FALSE nếu subquery rỗng.

## 5. EXISTS và NOT EXISTS

### 5.1 EXISTS: "có ít nhất một dòng không"

`EXISTS (subquery)` là TRUE nếu subquery trả về ít nhất một dòng, FALSE nếu không có dòng nào. Nó
không quan tâm dòng đó chứa gì.

```sql
-- Khách có ít nhất một đơn đã thanh toán (cùng câu hỏi với mục 4.1)
SELECT c.id, c.name
FROM customers c
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.customer_id = c.id AND o.status = 'paid'
)
ORDER BY c.id;
-- 1  An
-- 2  Bình
```

Vài điểm cần biết:

- Danh sách cột của subquery bị bỏ qua. `SELECT *`, `SELECT 1`, `SELECT 5` cho kết quả như nhau; tài
  liệu MySQL nói rõ MySQL không quan tâm phần này. `SELECT 1` là quy ước phổ biến để người đọc hiểu "chỉ
  hỏi có hay không".
- `EXISTS` chỉ trả TRUE hoặc FALSE, không bao giờ UNKNOWN. Đây là lý do nó an toàn với NULL.
- `EXISTS` gần như luôn đi với correlated subquery: điều kiện `o.customer_id = c.id` nối subquery với
  dòng ngoài đang xét. Về logic, với mỗi khách, DB chỉ cần tìm thấy một đơn khớp là đủ kết luận, không
  cần đọc tiếp.

⚠️ Quên điều kiện nối với câu ngoài là lỗi rất hay gặp:

```sql
SELECT c.id, c.name FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.status = 'pending');
-- trả về cả 4 khách
```

Subquery không nhắc tới `c`, nên với mọi khách nó đều trả về cùng một kết quả (có đơn 105 đang
`pending`), và `EXISTS` TRUE cho tất cả. Câu chạy không lỗi, chỉ sai.

### 5.2 NOT EXISTS: anti-join an toàn với NULL

```sql
-- Khách chưa có đơn nào
SELECT c.id, c.name
FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
-- 4  Dũng

-- Khách chưa có đơn ĐÃ THANH TOÁN nào
SELECT c.id, c.name
FROM customers c
WHERE NOT EXISTS (
  SELECT 1 FROM orders o
  WHERE o.customer_id = c.id AND o.status = 'paid'
)
ORDER BY c.id;
-- 3  Chi
-- 4  Dũng
```

Vì sao đơn 106 không phá `NOT EXISTS` như đã phá `NOT IN`? Khi xét Dũng, subquery tìm các đơn có
`o.customer_id = 4`. Với đơn 106, `NULL = 4` là UNKNOWN, nên đơn 106 đơn giản là không được tính là
"đơn của Dũng". Subquery không có dòng nào, `NOT EXISTS` là TRUE. NULL chỉ có thể làm một dòng không
khớp, không thể làm cả biểu thức thành UNKNOWN.

Ba cách viết anti-join, đặt cạnh nhau:

| Cách | Đúng khi cột so sánh có NULL? | Ghi chú |
|---|---|---|
| `WHERE id NOT IN (SELECT customer_id FROM orders)` | Không: ra tập rỗng | Chỉ an toàn khi cả hai vế chắc chắn `NOT NULL` |
| `WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)` | Có | Nên là lựa chọn mặc định |
| `LEFT JOIN orders o ON o.customer_id = c.id WHERE o.id IS NULL` | Có | Chương 07; phải kiểm tra `IS NULL` trên cột không thể NULL của bảng phải, thường là khoá chính |

### 5.3 Nên chọn IN, EXISTS hay JOIN

| Bạn cần | Viết |
|---|---|
| Lấy cột của cả hai bảng (tên khách và số tiền từng đơn) | `JOIN`, cẩn thận nhân dòng (chương 07) |
| Lọc dòng bảng A theo "có dòng liên quan ở B" | `IN (subquery)` hoặc `EXISTS` |
| Lọc dòng bảng A theo "không có dòng liên quan ở B" | `NOT EXISTS` (hoặc `LEFT JOIN ... IS NULL`) |
| So sánh với một giá trị tổng hợp (trung bình, lớn nhất) | Scalar subquery |

Có một lời khuyên cũ hay được nhắc: "đừng dùng `IN (subquery)`, hãy dùng `EXISTS` hoặc JOIN cho nhanh".
Lời khuyên này đến từ thời MySQL 5.5 trở về trước, khi `IN (subquery)` thường bị chạy lại cho từng dòng
ngoài. Từ MySQL 5.6, optimizer biết chuyển `IN` thành semijoin, và từ 8.0.16 `EXISTS` cũng được xử lý
bằng cùng các phép biến đổi như `IN` tương đương (mục 6.3). Ở MySQL 8.4, `IN` và `EXISTS` cho cùng
câu hỏi thường ra cùng kế hoạch thực thi. Hãy chọn theo ngữ nghĩa và độ dễ đọc, rồi kiểm tra bằng
`EXPLAIN` (chương 12) khi câu đó thật sự chậm, thay vì tin vào quy tắc truyền miệng.

## 6. Correlated subquery và chi phí

### 6.1 Mô hình "chạy lại cho mỗi dòng ngoài"

Câu hỏi: "Đơn mới nhất của mỗi khách". Viết bằng correlated subquery:

```sql
SELECT o.id, o.customer_id, o.order_date
FROM orders o
WHERE o.order_date = (
  SELECT MAX(o2.order_date)
  FROM orders o2
  WHERE o2.customer_id = o.customer_id      -- nhắc tới o của câu ngoài
)
ORDER BY o.id;
-- 102  1  2026-02-10
-- 104  2  2026-02-15
-- 105  3  2026-02-20
```

Về logic, DB làm như đoạn giả mã sau:

```
với mỗi dòng o trong orders:                         -- 6 dòng ngoài
    m = SELECT MAX(order_date) FROM orders o2
        WHERE o2.customer_id = <o.customer_id hiện tại>
    nếu o.order_date = m thì giữ o
```

| Dòng ngoài | `o.customer_id` | `m` tính được | `o.order_date = m`? |
|---|---|---|---|
| 101 | 1 | 2026-02-10 | Không |
| 102 | 1 | 2026-02-10 | Có |
| 103 | 2 | 2026-02-15 | Không |
| 104 | 2 | 2026-02-15 | Có |
| 105 | 3 | 2026-02-20 | Có |
| 106 | NULL | NULL (không đơn nào có `customer_id = NULL`) | UNKNOWN, loại |

⚠️ Bảng `orders` xuất hiện ở cả hai tầng nên phải đặt alias khác nhau (`o` và `o2`). Nếu bạn viết
`FROM orders o` ở cả hai tầng, quy tắc phạm vi của MySQL ("tìm từ trong ra ngoài") sẽ gắn `o` trong
subquery vào bảng của chính subquery. Điều kiện thành `o.customer_id = o.customer_id`, đúng với mọi
dòng có `customer_id` khác NULL. Subquery hết tương quan và trả về cùng một giá trị cho mọi dòng ngoài:
ngày lớn nhất trong các đơn có `customer_id` khác NULL, tức 2026-02-20 (đơn 106 bị loại vì
`NULL = NULL` là UNKNOWN). Câu vẫn chạy, chỉ ra kết quả khác hẳn: chỉ còn đơn 105.

### 6.2 Chi phí: N lần chạy, và vai trò của index

Nếu câu ngoài có N dòng, subquery về logic chạy N lần. Tổng chi phí phụ thuộc vào giá của mỗi lần chạy:

| Tình huống | Mỗi lần chạy subquery | Tổng cho N dòng ngoài |
|---|---|---|
| Không có index trên cột tương quan (`orders.customer_id`) | Quét cả bảng `orders`, M dòng | Khoảng N × M dòng phải đọc |
| Có index trên cột tương quan | Tra index, đọc vài dòng của đúng khách đó | Khoảng N lần tra index |

Với 100 000 đơn ngoài và 100 000 đơn trong, trường hợp đầu là cỡ 10 tỷ lần đọc dòng: câu lệnh coi như
treo. Trường hợp sau là 100 000 lần tra index, thường xong trong thời gian chấp nhận được. Vì vậy quy
tắc thực hành đầu tiên với correlated subquery là: cột dùng để nối với câu ngoài phải có index. Ở dữ
liệu mẫu, `orders.customer_id` đã có index `idx_orders_customer`. Với câu "ngày lớn nhất của mỗi khách",
index ghép `(customer_id, order_date)` còn tốt hơn, vì `MAX(order_date)` lấy được ngay ở cuối đoạn index
của khách đó (chương 11).

MySQL cũng có một mẹo nhỏ giúp giảm số lần chạy. Khi `EXPLAIN` (chương 12) hiện `select_type` là
`DEPENDENT SUBQUERY`, tài liệu MySQL cho biết subquery chỉ được tính lại một lần cho mỗi bộ giá trị
khác nhau của các cột ngoài mà nó phụ thuộc. Ở ví dụ trên, đơn 101 và 102 cùng `customer_id = 1` nên
về nguyên tắc không cần tính `MAX` hai lần.

### 6.3 Optimizer MySQL viết lại subquery thế nào

"Chạy lại cho mỗi dòng" là ngữ nghĩa, không phải cách thực thi bắt buộc. Optimizer MySQL 8.4 được phép
biến đổi câu lệnh miễn kết quả không đổi, và nó làm rất nhiều việc với subquery:

| Dạng subquery | MySQL 8.4 thường làm gì |
|---|---|
| `IN`, `= ANY`, `EXISTS` đứng ở mức trên cùng của `WHERE` hoặc `ON` (có thể là một vế của `AND`) | Chuyển thành semijoin, rồi chọn theo chi phí một chiến lược thực thi (bảng dưới) |
| `NOT IN`, `NOT EXISTS` (và các dạng phủ định tương đương) | Chuyển thành *antijoin* (từ 8.0.17): phép join chỉ giữ dòng không có dòng khớp |
| `IN` không đủ điều kiện làm semijoin | Materialize subquery thành bảng tạm, hoặc dùng chiến lược EXISTS: đẩy điều kiện `ngoài = trong` vào trong subquery |
| Derived table, CTE | Merge vào câu ngoài hoặc materialize (mục 7.4) |
| Scalar subquery tương quan | Thường chạy như `DEPENDENT SUBQUERY`. Cờ `subquery_to_derived` có thể chuyển nó thành derived table, nhưng mặc định tắt vì tài liệu ghi là đa số trường hợp không nhanh hơn |

Các chiến lược semijoin, theo mô tả của tài liệu MySQL:

| Chiến lược | Ý tưởng |
|---|---|
| Table pullout | Kéo bảng trong subquery ra thành inner join thường (khi chắc chắn không sinh dòng trùng, ví dụ nối theo khoá chính) |
| Duplicate Weedout | Chạy như join thường rồi loại dòng trùng bằng bảng tạm |
| FirstMatch | Với mỗi dòng ngoài, gặp dòng khớp đầu tiên thì dừng, không tìm tiếp |
| LooseScan | Quét bảng trong theo index, mỗi nhóm giá trị chỉ lấy một dòng |
| Materialization | Tính subquery một lần ra bảng tạm có index, rồi join với bảng tạm đó |

Không phải subquery nào cũng được làm semijoin. Theo tài liệu, subquery phải là một `SELECT` đơn (không
`UNION`), không có `HAVING`, không có hàm tổng hợp, không có `LIMIT`. Ngược lại, `DISTINCT`, `GROUP BY`
(khi không có hàm tổng hợp) và `ORDER BY` trong subquery kiểu này được chấp nhận nhưng bị bỏ qua, vì
semijoin tự lo việc khử trùng và thứ tự không ảnh hưởng tới kết quả.

⚠️ Với antijoin, tài liệu nói rõ: phần lớn trường hợp không áp dụng được khi các biểu thức được so sánh
có thể NULL. Đây là thêm một lý do để khai báo `NOT NULL` cho cột thật sự không bao giờ NULL; tài liệu
MySQL cũng khuyên như vậy vì nó giúp optimizer đơn giản hoá điều kiện. Và `NOT IN` trên cột cho phép
NULL vừa có nguy cơ sai nghĩa (mục 4.3), vừa khó được tối ưu.

Bài học thực tế: viết subquery cho đúng nghĩa, để optimizer lo phần thực thi; biết những thứ làm mất cơ
hội tối ưu (hàm tổng hợp, `LIMIT`, `UNION` trong subquery `IN`); và khi câu chậm, xem `EXPLAIN` thay vì
đoán. Chương 12 dạy đọc `EXPLAIN` cho từng chiến lược ở trên.

### 6.4 Khi nào nên tự viết lại

Ba tình huống thường gặp:

1. Nhiều scalar subquery trong danh sách `SELECT` cùng tổng hợp một bảng (ví dụ mục 3.3). Viết lại bằng
   một derived table gom một lần rồi `LEFT JOIN` (mục 7.3).
2. "Dòng có giá trị lớn nhất trong nhóm" bằng correlated subquery như mục 6.1. Có thể viết lại bằng
   derived table:

   ```sql
   SELECT o.id, o.customer_id, o.order_date
   FROM orders o
   JOIN (
     SELECT customer_id, MAX(order_date) AS last_date
     FROM orders
     GROUP BY customer_id
   ) AS m ON m.customer_id = o.customer_id AND m.last_date = o.order_date
   ORDER BY o.id;
   -- 102, 104, 105: giống mục 6.1
   ```

   hoặc bằng window function (chương 10). Cách nào nhanh hơn tuỳ dữ liệu và index; đo bằng
   `EXPLAIN ANALYZE` (chương 12).
3. Ngược lại, correlated subquery có `ORDER BY ... LIMIT 1` kèm index tốt lại thường là cách rẻ nhất khi
   số dòng ngoài ít và mỗi dòng chỉ cần "một vài dòng đầu" của nhóm. Dạng tổng quát của nó là `LATERAL`
   (mục 7.5).

### 6.5 Subquery trong UPDATE và DELETE: lỗi 1093

MySQL có một hạn chế mà PostgreSQL không có: nói chung bạn không thể sửa một bảng và đồng thời đọc chính
bảng đó trong subquery. Thử trên một bản sao để không làm hỏng dữ liệu mẫu:

```sql
CREATE TABLE orders_copy AS SELECT * FROM orders;     -- bản sao để thử

DELETE FROM orders_copy
WHERE total < (SELECT AVG(total) FROM orders_copy);
-- ERROR 1093 (HY000): You can't specify target table 'orders_copy' for update in FROM clause
```

Tài liệu MySQL đưa ra ngoại lệ: hạn chế này không áp dụng nếu phần đọc bảng nằm trong một derived table
được materialize (chứ không phải được merge vào câu ngoài). Khi đó kết quả đọc đã nằm sẵn trong bảng
tạm trước khi việc sửa bắt đầu. Vì thế cách lách là bọc thêm một tầng:

```sql
DELETE FROM orders_copy
WHERE total < (
  SELECT avg_total FROM (SELECT AVG(total) AS avg_total FROM orders_copy) AS t
);
-- Query OK, 4 rows affected   (trung bình 210: xoá 102 (150), 104 (80), 105 (170), 106 (60))

DROP TABLE orders_copy;
```

Derived table `t` chứa hàm tổng hợp nên không thể merge, chắc chắn được materialize. ⚠️ Nếu derived
table đủ đơn giản để merge được (không có hàm tổng hợp, `DISTINCT`, `GROUP BY`, `LIMIT`...), optimizer có
thể gộp nó vào câu ngoài và lỗi 1093 quay lại. Khi đó tài liệu gợi ý ép materialize bằng optimizer hint
`NO_MERGE`. CTE (mục 8) được optimizer xử lý như derived table, nên một CTE được materialize cũng lách được theo cùng ngoại lệ này. Một lựa chọn nữa là cú pháp `DELETE`
hoặc `UPDATE` nhiều bảng, JOIN bảng cần sửa với một derived table có hàm tổng hợp hoặc window function
(loại derived table luôn được materialize).

PostgreSQL không có hạn chế này: `DELETE FROM t WHERE x < (SELECT AVG(x) FROM t)` chạy bình thường.

## 7. Derived table: subquery trong FROM

### 7.1 Cú pháp

Kết quả của một câu `SELECT` là một bảng, nên nó đứng được ở chỗ của một bảng: trong `FROM`. Tài liệu
MySQL gọi đó là *derived table* (bảng dẫn xuất):

```sql
SELECT ... FROM (subquery) [AS] ten_bang ...
SELECT ... FROM (subquery) [AS] ten_bang (cot1, cot2, ...) ...   -- đặt lại tên cột
```

Tên (alias) là bắt buộc, vì mọi bảng trong `FROM` đều phải có tên để câu ngoài gọi tới:

```sql
SELECT * FROM (SELECT id, total FROM orders WHERE status = 'paid');
-- ERROR 1248 (42000): Every derived table must have its own alias

SELECT * FROM (SELECT id, total FROM orders WHERE status = 'paid') AS p
ORDER BY p.id;
-- 101 300, 102 150, 103 500, 106 60
```

PostgreSQL từ bản 16 cho phép bỏ alias của subquery trong `FROM`; MySQL thì không, nên cứ đặt tên cho
mọi derived table.

Derived table bình thường không được nhắc tới các bảng khác đứng cùng `FROM` với nó. Muốn làm điều đó
phải dùng `LATERAL` (mục 7.5).

### 7.2 Tổng hợp hai tầng

Câu hỏi: "Trung bình mỗi khách đã chi bao nhiêu?". Phải tính tổng theo từng khách trước (tầng 1), rồi
mới lấy trung bình của các tổng đó (tầng 2). Viết lồng hàm tổng hợp `AVG(SUM(total))` là không hợp lệ
(MySQL báo `Invalid use of group function`). Derived table tách hai tầng ra:

```sql
SELECT AVG(tong) AS tb_moi_khach
FROM (
  SELECT customer_id, SUM(total) AS tong
  FROM orders
  WHERE customer_id IS NOT NULL          -- bỏ khách vãng lai
  GROUP BY customer_id
) AS t;
```

Tầng trong ra ba dòng `(1, 450)`, `(2, 580)`, `(3, 170)`. Tầng ngoài tính (450 + 580 + 170) / 3 = 400.
MySQL in ra `400.0000`: `AVG` trên số nguyên hoặc `DECIMAL` trả về `DECIMAL` có thêm chữ số thập phân.
Nếu bỏ dòng `WHERE customer_id IS NOT NULL`, nhóm NULL với tổng 60 cũng được tính và kết quả thành
1260 / 4 = 315. Hai con số đều "đúng", tuỳ câu hỏi có tính khách vãng lai hay không; hãy quyết định
có chủ đích.

Tên cột đặt trong derived table (`tong`) dùng được ở câu ngoài, như một cột của bảng thật.

### 7.3 Gom trước rồi mới JOIN

Viết lại ví dụ mục 3.3 (hai scalar subquery cho mỗi khách) bằng một derived table:

```sql
SELECT c.id, c.name,
       COALESCE(t.so_don, 0)    AS so_don,
       COALESCE(t.tong_tien, 0) AS tong_tien
FROM customers c
LEFT JOIN (
  SELECT customer_id, COUNT(*) AS so_don, SUM(total) AS tong_tien
  FROM orders
  GROUP BY customer_id
) AS t ON t.customer_id = c.id
ORDER BY c.id;
```

```
+----+------+--------+-----------+
| id | name | so_don | tong_tien |
+----+------+--------+-----------+
|  1 | An   |      2 |       450 |
|  2 | Bình |      2 |       580 |
|  3 | Chi  |      1 |       170 |
|  4 | Dũng |      0 |         0 |
+----+------+--------+-----------+
```

Bảng `orders` chỉ được đọc và gom một lần. Sau khi gom, mỗi khách có tối đa một dòng trong `t`, nên
JOIN là 1-1 và không có chuyện nhân dòng. Đây là cách sửa chuẩn cho lỗi "JOIN qua quan hệ một-nhiều rồi
`SUM` bị cộng lặp" ở chương 07 và 08: gom phía "nhiều" trong derived table trước, rồi mới JOIN.

`LEFT JOIN` giữ Dũng (không có dòng trong `t`), `COALESCE` đổi NULL thành 0. Nhóm `customer_id` NULL
trong `t` không khớp khách nào (vì `NULL = c.id` là UNKNOWN) nên tự biến mất.

### 7.4 Merge hay materialize

Optimizer có hai cách xử lý một derived table (cũng áp dụng cho view và CTE):

- *Merge*: gộp derived table vào câu ngoài, như thể bạn viết thẳng. Ví dụ
  `SELECT * FROM (SELECT id, total FROM orders WHERE status = 'paid') AS p WHERE p.total > 100` được xử
  lý như `SELECT id, total FROM orders WHERE status = 'paid' AND total > 100`. Không có bảng tạm nào.
- *Materialize*: chạy derived table ra một bảng tạm nội bộ, rồi câu ngoài đọc bảng tạm đó. Trong lúc
  chạy, optimizer có thể tự thêm index vào bảng tạm nếu việc đó giúp JOIN nhanh hơn.

Merge thường rẻ hơn, và được bật mặc định (cờ `derived_merge` trong `optimizer_switch`). Nhưng có những
thứ làm derived table không merge được; theo tài liệu MySQL đó là: hàm tổng hợp hoặc window function,
`DISTINCT`, `GROUP BY`, `HAVING`, `LIMIT`, `UNION` hoặc `UNION ALL`, subquery trong danh sách `SELECT`,
gán giá trị cho biến người dùng, và derived table chỉ gồm hằng số (không đọc bảng nào). Derived table ở
mục 7.2 và 7.3 có `GROUP BY` nên được materialize.

Khi phải materialize, MySQL từ 8.0.22 còn có *derived condition pushdown*: đẩy điều kiện `WHERE` của
câu ngoài vào bên trong derived table trước khi materialize, để bảng tạm nhỏ hơn. Tối ưu này cũng có
giới hạn, ví dụ không đẩy được vào derived table có `LIMIT`, và không đẩy được điều kiện chứa subquery.

Bạn hiếm khi phải can thiệp, nhưng cần biết hai điều: derived table không tự động là "bảng tạm đắt
tiền" (nó có thể được merge), và cũng không tự động được tối ưu như viết thẳng (nếu có `GROUP BY`,
`LIMIT`... thì nó được tính riêng). Có thể điều khiển bằng optimizer hint `MERGE` / `NO_MERGE`; chi
tiết ở chương 12.

### 7.5 LATERAL: derived table nhìn được bảng đứng trước

Câu hỏi: "Hai đơn lớn nhất của mỗi khách". Với mỗi khách, ta muốn chạy
`SELECT ... WHERE customer_id = <khách đó> ORDER BY total DESC LIMIT 2`. Derived table thường không làm
được, vì nó không được nhắc tới `c.id` của bảng đứng trước trong cùng `FROM`. Từ MySQL 8.0.14, thêm từ
khoá `LATERAL` để cho phép điều đó:

```sql
SELECT c.name, t.id, t.total
FROM customers c
JOIN LATERAL (
  SELECT o.id, o.total
  FROM orders o
  WHERE o.customer_id = c.id          -- được nhắc tới c nhờ LATERAL
  ORDER BY o.total DESC
  LIMIT 2
) AS t ON TRUE
ORDER BY c.id, t.total DESC;
```

```
+------+-----+-------+
| name | id  | total |
+------+-----+-------+
| An   | 101 |   300 |
| An   | 102 |   150 |
| Bình | 103 |   500 |
| Bình | 104 |    80 |
| Chi  | 105 |   170 |
+------+-----+-------+
```

Theo tài liệu MySQL, lateral derived table được tính lại mỗi khi bảng đứng trước mà nó phụ thuộc chuyển
sang dòng mới. Về bản chất, đây là correlated subquery được đặt trong `FROM`, nên nó trả về được nhiều
dòng và nhiều cột (scalar subquery thì không).

- Dũng không có đơn nên vắng mặt. Muốn giữ Dũng (với `id`, `total` là NULL) thì đổi thành
  `LEFT JOIN LATERAL (...) AS t ON TRUE`. Tài liệu cho phép lateral derived table nằm ở vế phải của
  `INNER JOIN`, `CROSS JOIN` hoặc `LEFT JOIN` khi nó nhắc tới vế trái.
- Cũng có thể viết dạng dấu phẩy như ví dụ trong tài liệu: `FROM customers c, LATERAL (...) AS t`.
- Chi phí tuân theo mục 6.2: subquery chạy cho mỗi khách, nên cần index. Với index
  `(customer_id, total)`, mỗi lần chạy chỉ đọc đúng 2 dòng đầu của đoạn index thuộc khách đó.

PostgreSQL có `LATERAL` từ lâu (bản 9.3) với cùng ngữ nghĩa. Bài "top N mỗi nhóm" còn một lời giải
khác bằng window function ở chương 10. Nói chung `LATERAL` có lợi khi số nhóm cần xử lý ít, N nhỏ và có
index phù hợp; window function có lợi khi đằng nào cũng phải đọc gần như toàn bộ bảng. Đo bằng
`EXPLAIN ANALYZE` trước khi kết luận.

## 8. CTE: đặt tên cho subquery bằng WITH

### 8.1 Cú pháp

Derived table ở mục 7.2 có một nhược điểm về cách đọc: phần chạy trước (gom theo khách) lại nằm bên
trong, phải đọc từ trong ra ngoài. *CTE* (Common Table Expression) cho phép đặt tên cho subquery đó và
đưa nó lên đầu câu lệnh:

```sql
WITH ten_cte [(cot1, cot2, ...)] AS (subquery)
   [, ten_cte_2 [(...)] AS (subquery)] ...
SELECT ... FROM ten_cte ...;
```

Viết lại mục 7.2:

```sql
WITH tong_theo_khach AS (
  SELECT customer_id, SUM(total) AS tong
  FROM orders
  WHERE customer_id IS NOT NULL
  GROUP BY customer_id
)
SELECT AVG(tong) AS tb_moi_khach
FROM tong_theo_khach;
-- 400.0000, giống mục 7.2
```

Bây giờ câu đọc từ trên xuống như các bước của một thuật toán: "bước 1, tính tổng theo khách; bước 2,
lấy trung bình". CTE chỉ tồn tại trong đúng một câu lệnh; câu sau muốn dùng thì phải viết lại.

Tên cột của CTE lấy từ danh sách trong ngoặc sau tên CTE nếu có (số tên phải bằng số cột), nếu không thì
lấy từ danh sách cột của câu `SELECT` đầu tiên bên trong.

### 8.2 Nhiều CTE nối tiếp, và dùng một CTE nhiều lần

Câu hỏi: "Khách nào có tổng tiền đã thanh toán lớn hơn mức trung bình của các khách?"

```sql
WITH
tong_theo_khach AS (
  SELECT customer_id, SUM(total) AS tong
  FROM orders
  WHERE status = 'paid' AND customer_id IS NOT NULL
  GROUP BY customer_id
),
trung_binh AS (
  SELECT AVG(tong) AS tb FROM tong_theo_khach          -- CTE sau dùng CTE trước
)
SELECT c.name, t.tong
FROM tong_theo_khach t                                  -- dùng lại lần thứ hai
JOIN customers c ON c.id = t.customer_id
WHERE t.tong > (SELECT tb FROM trung_binh);
-- Bình  500
```

Tính tay: đơn đã thanh toán của khách có tài khoản là 101, 102 (An, 300 + 150 = 450) và 103 (Bình, 500).
Trung bình là (450 + 500) / 2 = 475, chỉ Bình vượt mức này.

Ví dụ này dùng hai khả năng mà derived table không có:

- `trung_binh` dùng lại `tong_theo_khach` được định nghĩa trước nó. Quy tắc: một CTE được nhắc tới các CTE
  định nghĩa trước nó trong cùng `WITH`, không được nhắc tới CTE định nghĩa sau.
- `tong_theo_khach` được dùng hai lần. Với derived table, bạn phải viết lại nguyên subquery ở cả hai chỗ.

Hai quy tắc cú pháp nữa: mỗi cấp chỉ có một mệnh đề `WITH` (viết `WITH a AS (...) WITH b AS (...)` là
sai, phải dùng dấu phẩy), và tên CTE trong một `WITH` không được trùng nhau.

### 8.3 CTE, derived table và view

| | Derived table | CTE | View (chương 17) |
|---|---|---|---|
| Sống bao lâu | Trong một chỗ của một câu | Trong một câu lệnh | Lưu trong database, dùng cho mọi câu |
| Dùng nhiều lần trong cùng câu | Phải viết lại | Được | Được |
| Nhắc tới nhau | Không (trừ `LATERAL`) | CTE sau nhắc tới CTE trước | View dựa trên view khác |
| Đệ quy | Không | Có, với `WITH RECURSIVE` | Định nghĩa view được phép chứa `WITH` |
| Cách đọc | Lồng từ trong ra | Từ trên xuống | Tách hẳn khỏi câu |

Chọn thế nào: logic chỉ dùng một lần và ngắn thì derived table là đủ. Logic nhiều bước, hoặc cần dùng
một kết quả trung gian nhiều lần, thì CTE. Logic cần dùng lại ở nhiều câu lệnh khác nhau thì cân nhắc
view.

### 8.4 CTE có làm câu chạy nhanh hơn hay chậm hơn không

Ở MySQL, optimizer xử lý CTE giống derived table (mục 7.4): merge vào câu ngoài hoặc materialize. Hai
điểm riêng mà tài liệu MySQL nêu:

- Nếu CTE được materialize thì nó chỉ được materialize một lần cho cả câu, dù được nhắc tới nhiều lần.
  Đây là lợi thế thật so với viết hai derived table giống nhau.
- Khi materialize, optimizer có thể tự thêm index cho bảng tạm của CTE nếu ước lượng thấy có lợi.

PostgreSQL có lịch sử khác, và là nguồn gốc của lời đồn "CTE chậm". Trước bản 12, Postgres luôn tính
CTE riêng trước phần còn lại của câu, nên điều kiện ở câu ngoài không được đẩy vào trong CTE (CTE là một
"hàng rào tối ưu"). Từ bản 12, CTE được tự động gộp vào câu ngoài nếu nó không có tác dụng phụ, không
đệ quy và chỉ được nhắc tới một lần. Muốn điều khiển thì viết `WITH x AS MATERIALIZED (...)` (ép tính
riêng) hoặc `WITH x AS NOT MATERIALIZED (...)` (ép gộp).

Kết luận: CTE trước hết là công cụ để viết cho dễ đọc. Đừng mặc định nó nhanh hơn hay chậm hơn
subquery; khi cần biết thì xem `EXPLAIN`.

### 8.5 WITH đi cùng UPDATE, DELETE, INSERT

Theo tài liệu MySQL, `WITH` được đặt ở các vị trí sau:

| Vị trí | Dạng |
|---|---|
| Đầu câu `SELECT`, `UPDATE`, `DELETE` | `WITH ... SELECT ...`, `WITH ... UPDATE ...`, `WITH ... DELETE ...` |
| Đầu một subquery, kể cả derived table | `... WHERE id IN (WITH ... SELECT ...)`, `FROM (WITH ... SELECT ...) AS dt` |
| Ngay trước `SELECT` trong câu có chứa `SELECT` | `INSERT ... WITH ... SELECT ...`, `REPLACE ... WITH ... SELECT ...`, `CREATE TABLE ... WITH ... SELECT ...`, `CREATE VIEW ... WITH ... SELECT ...` |

⚠️ Với `INSERT`, `WITH` đứng sau phần `INSERT INTO ...` và ngay trước `SELECT`, không đứng đầu câu như
`SELECT`, `UPDATE`, `DELETE`. Bảng trên không có dạng `WITH ... INSERT ...`, nên đừng viết như vậy.

CTE được xử lý như derived table (mục 7.4), nên CTE chứa hàm tổng hợp được materialize và lách được lỗi 1093 theo cùng ngoại lệ ở mục 6.5. Làm lại ví dụ xoá đơn dưới trung bình:

```sql
CREATE TABLE orders_copy AS SELECT * FROM orders;

WITH tb AS (SELECT AVG(total) AS avg_total FROM orders_copy)
DELETE FROM orders_copy
WHERE total < (SELECT avg_total FROM tb);
-- 4 rows affected, giống mục 6.5

DROP TABLE orders_copy;
```

PostgreSQL đi xa hơn: phần bên trong `WITH` có thể chính là một câu `INSERT`, `UPDATE`, `DELETE` (hoặc
`MERGE`) có `RETURNING`, ví dụ xoá các dòng cũ và chép chúng sang bảng log trong một câu:
`WITH moved AS (DELETE FROM t WHERE ... RETURNING *) INSERT INTO t_log SELECT * FROM moved`. MySQL không
có tính năng này.

## 9. Recursive CTE

### 9.1 Ví dụ nhỏ nhất: đếm từ 1 tới 5

Một CTE được phép nhắc tới chính nó nếu khai báo `WITH RECURSIVE`. Ví dụ nhỏ nhất:

```sql
WITH RECURSIVE seq (n) AS (
  SELECT 1                              -- phần gốc: chạy một lần, không nhắc tới seq
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 5     -- phần đệ quy: nhắc tới seq
)
SELECT n FROM seq ORDER BY n;
-- 1, 2, 3, 4, 5  (5 dòng)
```

Một recursive CTE luôn có hai phần nối bằng `UNION ALL` (hoặc `UNION DISTINCT`):

- *Phần gốc* (tài liệu MySQL gọi là nonrecursive part, sách khác hay gọi là *anchor member*): sinh
  ra các dòng ban đầu, không được nhắc tới tên CTE.
- *Phần đệ quy* (recursive part): nhắc tới tên CTE trong `FROM`, sinh thêm dòng từ các dòng đã có.

### 9.2 Cơ chế từng vòng

Chữ "đệ quy" dễ gây hiểu nhầm. Thực tế DB chạy một vòng lặp, và điểm mấu chốt nằm ở câu này của tài
liệu MySQL: mỗi vòng của phần đệ quy chỉ làm việc trên các dòng do vòng trước sinh ra, không phải trên
toàn bộ kết quả đã có.

```
phần gốc ──► R0 ──► phần đệ quy(R0) ──► R1 ──► phần đệ quy(R1) ──► R2 ... ──► Rk rỗng: dừng
kết quả cuối = R0 ∪ R1 ∪ ... ∪ R(k-1)
```

Chạy tay ví dụ `seq`:

| Vòng | `seq` mà phần đệ quy nhìn thấy | Dòng mới sinh ra | Kết quả tích luỹ |
|---|---|---|---|
| 0 (phần gốc) | | 1 | 1 |
| 1 | {1} | 2 | 1, 2 |
| 2 | {2} | 3 | 1, 2, 3 |
| 3 | {3} | 4 | 1, 2, 3, 4 |
| 4 | {4} | 5 | 1, 2, 3, 4, 5 |
| 5 | {5} | không có (`5 < 5` sai) | dừng |

Ở vòng 2, `seq` chỉ chứa `{2}` chứ không phải `{1, 2}`. Nếu nó chứa toàn bộ kết quả, vòng 2 sẽ sinh lại
số 2 từ số 1 và dòng sẽ nhân lên không ngừng. Đệ quy dừng khi một vòng không sinh ra dòng mới nào, nên
phần đệ quy phải có điều kiện khiến nó tới lúc hết dòng (`WHERE n < 5`, hoặc hết cha con để JOIN).

### 9.3 Duyệt cây danh mục từ trên xuống

Bảng `categories` lưu cây theo kiểu *adjacency list*: mỗi dòng ghi id của cha (`parent_id`). Lấy toàn
bộ cây con của "Điện tử", kèm độ sâu và đường đi:

```sql
WITH RECURSIVE tree AS (
  SELECT id, name, 0 AS depth,
         CAST(id AS CHAR(200)) AS path            -- CAST đủ rộng, xem mục 9.5
  FROM categories
  WHERE id = 1                                    -- phần gốc: Điện tử
  UNION ALL
  SELECT c.id, c.name, t.depth + 1,
         CONCAT(t.path, ',', c.id)
  FROM tree t
  JOIN categories c ON c.parent_id = t.id         -- con của các dòng vòng trước
)
SELECT id, CONCAT(REPEAT('  ', depth), name) AS cay, depth, path
FROM tree
ORDER BY path;
```

```
+----+----------------+-------+-------+
| id | cay            | depth | path  |
+----+----------------+-------+-------+
|  1 | Điện tử        |     0 | 1     |
|  2 |   Điện thoại   |     1 | 1,2   |
|  3 |     Android    |     2 | 1,2,3 |
|  4 |     iPhone     |     2 | 1,2,4 |
|  5 |   Laptop       |     1 | 1,5   |
+----+----------------+-------+-------+
```

Theo từng vòng: R0 = `{1}`; R1 là con của 1, tức `{2, 5}`; R2 là con của 2 và 5, tức `{3, 4}`; R3 là
con của 3 và 4, rỗng, dừng. Danh mục 6, 7 không xuất hiện vì không nằm dưới gốc 1. Muốn lấy cả rừng
cây thì đổi phần gốc thành `WHERE parent_id IS NULL`.

Vài chi tiết:

- Sắp theo `path` cho ra thứ tự duyệt theo chiều sâu, cây con nằm liền dưới cha. Nhưng đó là so sánh
  chuỗi: anh em `10` sẽ đứng trước anh em `2` vì ký tự `'1' < '2'`. Cần thứ tự số thì đệm số 0,
  ví dụ `LPAD(id, 6, '0')`, khi ghép `path`.
- Phần đệ quy chạy một lần cho mỗi tầng và JOIN theo `c.parent_id`, nên cột `parent_id` cần index
  (dữ liệu mẫu đã có `idx_categories_parent`).

### 9.4 Đi ngược lên: breadcrumb

Đổi chiều JOIN để đi từ một nút lên gốc, ví dụ làm dòng điều hướng "Điện tử > Điện thoại > Android":

```sql
WITH RECURSIVE ancestors AS (
  SELECT id, name, parent_id, 0 AS lvl
  FROM categories
  WHERE id = 3                                    -- bắt đầu từ Android
  UNION ALL
  SELECT c.id, c.name, c.parent_id, a.lvl + 1
  FROM ancestors a
  JOIN categories c ON c.id = a.parent_id         -- đi lên cha
)
SELECT GROUP_CONCAT(name ORDER BY lvl DESC SEPARATOR ' > ') AS breadcrumb
FROM ancestors;
-- Điện tử > Điện thoại > Android
```

R0 là Android (cha là 2), R1 là Điện thoại (cha là 1), R2 là Điện tử (cha là NULL), R3 rỗng vì
`c.id = NULL` không khớp dòng nào. `GROUP_CONCAT` ở câu cuối ghép tên theo `lvl` giảm dần. Hàm tổng hợp
được phép ở câu `SELECT` cuối, nhưng không được phép trong phần đệ quy (mục 9.8).

### 9.5 Kiểu và độ rộng cột lấy từ phần gốc

Tài liệu MySQL ghi: kiểu của các cột trong kết quả CTE chỉ được suy ra từ phần gốc, phần đệ quy bị bỏ
qua khi xác định kiểu. Hệ quả là một cái bẫy với cột chuỗi. Ví dụ của tài liệu:

```sql
WITH RECURSIVE cte AS (
  SELECT 1 AS n, 'abc' AS str
  UNION ALL
  SELECT n + 1, CONCAT(str, str) FROM cte WHERE n < 3
)
SELECT * FROM cte;
-- ERROR 1406 (22001): Data too long for column 'str' at row 1
```

Cột `str` lấy kiểu từ `'abc'`, tức chuỗi dài 3 ký tự. Vòng sau sinh ra `'abcabc'` (6 ký tự) không vừa.
Với strict mode (mặc định), câu báo lỗi như trên; nếu tắt strict mode, tài liệu cho biết giá trị bị cắt
im lặng về `'abc'`, còn tệ hơn. Cách sửa là khai báo độ rộng đủ lớn ngay ở phần gốc:

```sql
WITH RECURSIVE cte AS (
  SELECT 1 AS n, CAST('abc' AS CHAR(20)) AS str
  UNION ALL
  SELECT n + 1, CONCAT(str, str) FROM cte WHERE n < 3
)
SELECT * FROM cte;
-- 1  abc
-- 2  abcabc
-- 3  abcabcabcabc
```

Đây là lý do ví dụ cây ở mục 9.3 viết `CAST(id AS CHAR(200))` cho cột `path`: chọn độ rộng đủ cho cây sâu
nhất bạn chấp nhận.

### 9.6 Giới hạn đệ quy: cte_max_recursion_depth và các chốt chặn khác

Một recursive CTE quên điều kiện dừng sẽ chạy mãi. MySQL có lưới an toàn: biến hệ thống
`cte_max_recursion_depth`, mặc định 1000. CTE đệ quy quá số tầng này thì bị dừng với lỗi. Thử sinh 2000
số:

```sql
WITH RECURSIVE seq (n) AS (
  SELECT 1
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 2000
)
SELECT COUNT(*) FROM seq;
-- ERROR 3636 (HY000): Recursive query aborted after 1001 iterations. Try increasing @@cte_max_recursion_depth to a larger value.

SET SESSION cte_max_recursion_depth = 5000;    -- chỉ ảnh hưởng phiên làm việc hiện tại
-- chạy lại câu trên: 2000
```

Ở đây giới hạn chặn nhầm một câu hoàn toàn hợp lệ (cần khoảng 2000 vòng), nên tăng giới hạn cho phiên
là đúng. Khi lỗi 3636 xuất hiện ở một câu đáng lẽ chỉ cần vài vòng (duyệt cây danh mục vài tầng), đừng
tăng giới hạn; đó là dấu hiệu của bug trong điều kiện dừng hoặc dữ liệu có vòng (mục 9.7).

Các chốt chặn khác theo tài liệu MySQL:

- `LIMIT` trong phần đệ quy (từ MySQL 8.0.19): giới hạn tổng số dòng sinh ra; DB dừng sinh dòng ngay khi
  đủ số lượng. Ví dụ `SELECT n + 1 FROM seq LIMIT 10000`.
- Giới hạn thời gian: biến `max_execution_time` (mili giây) hoặc optimizer hint
  `SELECT /*+ MAX_EXECUTION_TIME(1000) */ * FROM cte` để cắt câu chạy quá 1 giây.

### 9.7 Dữ liệu có vòng

Cây danh mục chỉ là cây khi không có vòng. Một bug khi sửa danh mục (gán cha của một nút thành chính
con cháu của nó) tạo ra vòng, và mọi truy vấn duyệt cây bắt đầu chạy mãi. Tạo vòng có chủ đích để thử:

```sql
UPDATE categories SET parent_id = 3 WHERE id = 1;   -- Điện tử thành con của Android: 1 → 2 → 3 → 1

WITH RECURSIVE tree AS (
  SELECT id, parent_id FROM categories WHERE id = 1
  UNION ALL
  SELECT c.id, c.parent_id FROM tree t JOIN categories c ON c.parent_id = t.id
)
SELECT COUNT(*) FROM tree;
-- ERROR 3636 (HY000): Recursive query aborted after 1001 iterations. ...
```

Vòng R3 tìm con của 3 và 4, gặp lại 1; R4 lại ra `{2, 5}`... mãi mãi, tới khi chạm giới hạn 1000.

Ba cách phòng:

1. `UNION DISTINCT` thay cho `UNION ALL`. Tài liệu MySQL ghi rằng khi đó dòng trùng bị loại, hữu ích để
   tránh lặp vô hạn. Ở câu trên, R3 sinh lại dòng `(1, 3)` đã có nên bị loại, R3 rỗng, đệ quy dừng và
   `COUNT(*)` ra 5. ⚠️ Cách này chỉ hiệu quả khi dòng lặp lại giống hệt. Có cột `depth` hay `path` thì
   mỗi vòng sinh dòng khác nhau, và `UNION DISTINCT` không còn chặn được gì.
2. Tự ghi lại đường đi và không đi vào nút đã thăm, kèm một giới hạn độ sâu:

   ```sql
   WITH RECURSIVE tree AS (
     SELECT id, 0 AS depth, CAST(id AS CHAR(200)) AS path
     FROM categories WHERE id = 1
     UNION ALL
     SELECT c.id, t.depth + 1, CONCAT(t.path, ',', c.id)
     FROM tree t JOIN categories c ON c.parent_id = t.id
     WHERE FIND_IN_SET(c.id, t.path) = 0      -- c.id đã có trên đường đi: đây là vòng, không đi tiếp
       AND t.depth < 20                        -- không bao giờ sâu quá 20 tầng
   )
   SELECT id, depth, path FROM tree ORDER BY path;
   -- 1 0 1 | 2 1 1,2 | 3 2 1,2,3 | 4 2 1,2,4 | 5 1 1,5   (bước 3 → 1 bị chặn)
   ```

   `FIND_IN_SET(x, 'a,b,c')` trả về vị trí của x trong danh sách phân cách bằng dấu phẩy, 0 nếu không có.
3. Chặn từ gốc: kiểm tra trước khi ghi, không cho gán cha là chính nó hoặc con cháu của nó (dùng chính
   truy vấn cây con ở mục 9.3 để kiểm tra). Dữ liệu sạch thì truy vấn mới đơn giản được.

Trả dữ liệu về như cũ:

```sql
UPDATE categories SET parent_id = NULL WHERE id = 1;
```

### 9.8 Ràng buộc cú pháp của phần đệ quy

Theo tài liệu MySQL, phần đệ quy:

- Không được chứa hàm tổng hợp (`SUM()`...), window function, `GROUP BY`, `ORDER BY`, `DISTINCT`.
- Chỉ được nhắc tới tên CTE một lần, và chỉ trong `FROM` của nó, không trong subquery.
- Được JOIN CTE với bảng khác, nhưng CTE không được nằm ở vế phải của `LEFT JOIN`.
- Được dùng `LIMIT` (kèm `OFFSET` nếu cần), như mục 9.6.

Muốn tổng hợp (đếm số nút con cháu, tính tổng giá trị cả cây) thì làm ở câu `SELECT` cuối, sau khi CTE
đã sinh xong mọi dòng.

### 9.9 Sinh dãy ngày để lấp chỗ trống trong báo cáo

Báo cáo doanh thu theo tháng bằng `GROUP BY` thuần sẽ không có dòng cho tháng không bán được gì: tháng
đó biến mất khỏi biểu đồ thay vì hiện số 0. Cách sửa chuẩn: sinh đủ dãy tháng bằng recursive CTE, rồi
`LEFT JOIN` dữ liệu vào.

```sql
WITH RECURSIVE months (m) AS (
  SELECT DATE '2026-01-01'
  UNION ALL
  SELECT m + INTERVAL 1 MONTH FROM months WHERE m < DATE '2026-04-01'
)
SELECT DATE_FORMAT(months.m, '%Y-%m') AS thang,
       COUNT(o.id)                    AS so_don,
       COALESCE(SUM(o.total), 0)      AS doanh_thu
FROM months
LEFT JOIN orders o
  ON  o.order_date >= months.m
  AND o.order_date <  months.m + INTERVAL 1 MONTH
  AND o.status = 'paid'                              -- điều kiện bảng phải đặt ở ON (chương 07)
GROUP BY months.m
ORDER BY months.m;
```

```
+---------+--------+-----------+
| thang   | so_don | doanh_thu |
+---------+--------+-----------+
| 2026-01 |      2 |       800 |
| 2026-02 |      2 |       210 |
| 2026-03 |      0 |         0 |
| 2026-04 |      0 |         0 |
+---------+--------+-----------+
```

Tháng 1 có đơn 101 và 103 (300 + 500), tháng 2 có đơn 102 và 106 (150 + 60). `COUNT(o.id)` thay vì
`COUNT(*)` để tháng không có đơn ra 0 chứ không phải 1 (chương 08). Điều kiện ngày viết dạng khoảng
`>= đầu tháng AND < đầu tháng sau` thay vì `DATE_FORMAT(o.order_date, ...) = ...`, để còn dùng được index
trên `order_date` (chương 11).

⚠️ Dãy theo ngày dài hơn khoảng 1000 ngày (gần 3 năm) sẽ chạm `cte_max_recursion_depth` mặc định. Tăng
giới hạn cho phiên (mục 9.6), hoặc dùng một bảng lịch (calendar table) tạo sẵn nếu báo cáo kiểu này chạy
thường xuyên.

### 9.10 PostgreSQL: SEARCH và CYCLE

PostgreSQL dùng cùng cú pháp `WITH RECURSIVE` và cùng cơ chế vòng lặp (tài liệu Postgres mô tả bằng một
"working table" chứa các dòng của vòng trước). Khác biệt đáng nhớ:

- Postgres không có biến giới hạn số vòng như `cte_max_recursion_depth`; tài liệu Postgres nhắc bạn phải
  tự bảo đảm phần đệ quy tới lúc hết dòng, nếu không câu sẽ lặp vô hạn.
- Từ bản 14 có hai mệnh đề chuẩn SQL viết sau CTE: `SEARCH DEPTH FIRST BY id SET ordercol` (hoặc
  `BREADTH FIRST`) tự sinh cột để sắp xếp theo chiều sâu hoặc chiều rộng, thay cho mẹo `path` ở mục 9.3;
  và `CYCLE id SET is_cycle USING path` tự phát hiện vòng, thêm cột `is_cycle` và `path`, thay cho mẹo
  `FIND_IN_SET` ở mục 9.7.

```sql
-- PostgreSQL 14+
WITH RECURSIVE tree AS (
  SELECT id, parent_id, name FROM categories WHERE id = 1
  UNION ALL
  SELECT c.id, c.parent_id, c.name FROM categories c JOIN tree t ON c.parent_id = t.id
) CYCLE id SET is_cycle USING path
SELECT id, name, is_cycle FROM tree;
```

Recursive CTE trên adjacency list là cách mặc định để làm việc với cây. Khi cây rất lớn và bị đọc liên
tục (menu danh mục trên mọi trang), có những cách lưu cây khác như materialized path hay closure table,
đổi chi phí ghi lấy tốc độ đọc. Đó là bài toán thiết kế schema, nằm ngoài phạm vi chương này.

## 10. Ghép kết quả: UNION, UNION ALL, INTERSECT, EXCEPT

### 10.1 Ghép dọc, không phải ghép ngang

JOIN ghép hai bảng theo chiều ngang: mỗi dòng kết quả có cột của cả hai bảng. Các phép toán tập hợp
(*set operations*) ghép theo chiều dọc: chồng dòng của câu `SELECT` này lên dòng của câu `SELECT` kia.

```
JOIN (thêm cột)                      UNION (thêm dòng)
+-------+-------+                    +-------+
| cột A | cột B |                    | dòng của SELECT 1
+-------+-------+                    +-------+
                                     | dòng của SELECT 2
                                     +-------+
```

MySQL 8.4 có ba phép: `UNION` (hợp), `INTERSECT` (giao), `EXCEPT` (hiệu). `INTERSECT` và `EXCEPT` có
từ MySQL 8.0.31; trước đó phải viết bằng `IN`/`EXISTS`.

Luật ghép, áp dụng cho cả ba phép:

- Các câu `SELECT` phải có cùng số cột, nếu không sẽ lỗi
  `ERROR 1222 (21000): The used SELECT statements have a different number of columns`.
- Cột được ghép theo vị trí, không theo tên. Cột thứ nhất của câu 1 ghép với cột thứ nhất của câu 2,
  bất kể tên.
- Tên cột của kết quả lấy từ câu `SELECT` đầu tiên.
- Các cột cùng vị trí nên có cùng kiểu. Nếu không, kiểu và độ dài của cột kết quả được tính dựa trên giá
  trị của tất cả các câu (khác với recursive CTE ở mục 9.5, nơi chỉ phần gốc quyết định kiểu).

⚠️ Vì ghép theo vị trí, đảo thứ tự cột ở một câu là lỗi im lặng:
`SELECT name, city FROM customers UNION ALL SELECT city, name FROM suppliers` chạy bình thường, nhưng
cột `name` của kết quả chứa lẫn tên thành phố của nhà cung cấp.

### 10.2 UNION và UNION ALL

```sql
SELECT city FROM customers
UNION ALL
SELECT city FROM suppliers
ORDER BY city;
-- 7 dòng: Đà Nẵng, Đà Nẵng, Hà Nội, Hà Nội, Hà Nội, Hồ Chí Minh, Huế

SELECT city FROM customers
UNION
SELECT city FROM suppliers
ORDER BY city;
-- 4 dòng: Đà Nẵng, Hà Nội, Hồ Chí Minh, Huế
```

- `UNION ALL` nối thẳng mọi dòng: 4 dòng từ `customers` cộng 3 dòng từ `suppliers`.
- `UNION` (viết đầy đủ là `UNION DISTINCT`, và đây là mặc định khi không ghi gì) loại mọi dòng trùng
  trong toàn bộ kết quả, kể cả dòng trùng nằm trong cùng một câu (Hà Nội xuất hiện hai lần ngay trong
  `customers`).

Khi khử trùng, hai NULL được coi là giống nhau, như `DISTINCT` và `GROUP BY`:

```sql
SELECT NULL AS x UNION SELECT NULL;       -- 1 dòng: NULL
SELECT NULL AS x UNION ALL SELECT NULL;   -- 2 dòng
```

Chi phí: để khử trùng, `UNION` phải đưa kết quả vào bảng tạm nội bộ và loại dòng trùng. Tài liệu MySQL
liệt kê các trường hợp `UNION` được chạy không cần bảng tạm: là `UNION ALL`, không có `ORDER BY` cho toàn
bộ kết quả, và không phải phần trên cùng của một câu `INSERT ... SELECT`. Với kết quả lớn, khác biệt là
đáng kể.

Quy tắc thực hành: mặc định viết `UNION ALL`. Chỉ viết `UNION` khi bạn thật sự muốn khử trùng và đã nghĩ
xem "trùng" nghĩa là gì.

⚠️ `UNION` có thể nuốt mất dữ liệu hợp lệ. Hai khoản thanh toán khác nhau cùng của khách 1, cùng 100 nghìn:

```sql
SELECT 1 AS customer_id, 100 AS amount
UNION
SELECT 1, 100;
-- 1 dòng: hai khoản tiền khác nhau bị gộp làm một, tổng tiền sai
```

Nếu dòng của bạn đại diện cho những thực thể khác nhau, hoặc đưa khoá chính vào danh sách cột, hoặc dùng
`UNION ALL`.

### 10.3 Gộp dữ liệu từ nhiều bảng

Ứng dụng thường gặp nhất: gộp những bảng có ý nghĩa tương tự thành một danh sách, kèm một cột hằng để
biết dòng đến từ đâu.

```sql
SELECT 'customer' AS loai, id, name, city FROM customers
UNION ALL
SELECT 'supplier', id, name, city FROM suppliers
ORDER BY city, loai, id;
```

```
+----------+----+---------------+-------------+
| loai     | id | name          | city        |
+----------+----+---------------+-------------+
| customer |  2 | Bình          | Đà Nẵng     |
| supplier |  3 | NCC Hàn Giang | Đà Nẵng     |
| customer |  1 | An            | Hà Nội      |
| customer |  3 | Chi           | Hà Nội      |
| supplier |  1 | NCC Sao Mai   | Hà Nội      |
| supplier |  2 | NCC Bến Thành | Hồ Chí Minh |
| customer |  4 | Dũng          | Huế         |
+----------+----+---------------+-------------+
```

Câu `SELECT` thứ hai không cần đặt alias: tên cột `loai` lấy từ câu đầu. Các trường hợp tương tự: gộp
bảng `orders` với bảng lưu trữ `orders_archive` có cùng cấu trúc; gộp nhiều loại sự kiện (đơn hàng, thanh
toán, đánh giá) thành một dòng thời gian hoạt động.

### 10.4 ORDER BY và LIMIT khi có UNION

Ba quy tắc, theo tài liệu MySQL:

1. `ORDER BY` và `LIMIT` viết sau câu `SELECT` cuối cùng áp dụng cho toàn bộ kết quả.
2. Muốn `ORDER BY`/`LIMIT` cho riêng một câu thì phải bọc câu đó trong ngoặc. Bản thân các dòng do
   phép toán tập hợp sinh ra không có thứ tự, nên `ORDER BY` riêng trong một câu chỉ có ý nghĩa khi đi
   cùng `LIMIT` (chọn những dòng nào); `ORDER BY` riêng mà không có `LIMIT` bị optimizer bỏ đi.
3. `ORDER BY` cho toàn bộ kết quả không được dùng tên cột có tiền tố bảng (`c.city`). Dùng tên cột (hoặc
   alias) của câu đầu tiên; nếu cột đã được đặt alias thì phải dùng alias.

Ví dụ "đơn lớn nhất của tháng 1 và đơn lớn nhất của tháng 2":

```sql
(SELECT id, order_date, total FROM orders
 WHERE order_date <  '2026-02-01' ORDER BY total DESC LIMIT 1)
UNION ALL
(SELECT id, order_date, total FROM orders
 WHERE order_date >= '2026-02-01' ORDER BY total DESC LIMIT 1)
ORDER BY order_date;
-- 103  2026-01-20  500
-- 105  2026-02-20  170
```

Thiếu ngoặc thì `ORDER BY`/`LIMIT` không còn gắn với câu bạn muốn: phần viết sau câu cuối được hiểu là
của cả phép `UNION` (quy tắc 1), không phải của riêng tháng 2.

### 10.5 INTERSECT và EXCEPT

- `A INTERSECT B`: các dòng có mặt ở cả A và B.
- `A EXCEPT B`: các dòng có trong A mà không có trong B. Thứ tự hai vế quan trọng.

```sql
-- Thành phố vừa có khách vừa có nhà cung cấp
SELECT city FROM customers
INTERSECT
SELECT city FROM suppliers
ORDER BY city;
-- Đà Nẵng, Hà Nội

-- Thành phố có khách nhưng không có nhà cung cấp
SELECT city FROM customers
EXCEPT
SELECT city FROM suppliers;
-- Huế

-- Đảo vế: có nhà cung cấp nhưng không có khách
SELECT city FROM suppliers
EXCEPT
SELECT city FROM customers;
-- Hồ Chí Minh
```

Giống `UNION`, mặc định của `INTERSECT` và `EXCEPT` là `DISTINCT` (kết quả không có dòng trùng); viết
`INTERSECT ALL`, `EXCEPT ALL` để giữ dòng trùng. Theo chuẩn SQL, với dạng `ALL`, một dòng xuất hiện m
lần ở vế trái và n lần ở vế phải sẽ có mặt min(m, n) lần trong kết quả `INTERSECT ALL` và m - n lần
(nếu dương) trong kết quả `EXCEPT ALL`. Trong thực tế dạng `DISTINCT` mặc định được dùng nhiều hơn hẳn.

So với cách viết bằng subquery:

| Phép tập hợp | Viết tương tự bằng subquery | Khác biệt cần nhớ |
|---|---|---|
| `A INTERSECT B` | `SELECT DISTINCT ... FROM A WHERE EXISTS (... khớp mọi cột ...)` | Phép tập hợp so cả dòng; subquery tự chọn cột để so |
| `A EXCEPT B` | `SELECT DISTINCT ... FROM A WHERE NOT EXISTS (...)` | Theo chuẩn SQL, phép tập hợp coi hai NULL là giống nhau khi so dòng, còn `=` trong subquery cho UNKNOWN |

Phép tập hợp gọn khi hai vế có cùng "hình dạng" và bạn cần so nguyên dòng. Khi cần trả về thêm cột không
tham gia so sánh (tên khách, ngày đặt), `EXISTS`/`NOT EXISTS` linh hoạt hơn.

### 10.6 Thứ tự ưu tiên khi trộn nhiều phép

- `INTERSECT` được tính trước `UNION` và `EXCEPT`. Tài liệu MySQL ví dụ:
  `TABLE r EXCEPT TABLE s INTERSECT TABLE t` được hiểu là `TABLE r EXCEPT (TABLE s INTERSECT TABLE t)`.
  (`TABLE t` là cách viết gọn của `SELECT * FROM t` trong MySQL.)
- Trộn `ALL` và `DISTINCT`: một phép `DISTINCT` ghi đè mọi phép `ALL` đứng bên trái nó. Ví dụ
  `A UNION ALL B UNION C` cho kết quả không có dòng trùng nào, vì `UNION` (DISTINCT) cuối cùng khử trùng
  cả phần `A UNION ALL B` đứng trước.

Khi trộn nhiều phép, hãy đặt ngoặc cho rõ ý thay vì bắt người đọc nhớ thứ tự ưu tiên.

### 10.7 Giả lập FULL OUTER JOIN

MySQL không có `FULL OUTER JOIN` (chương 07). Câu hỏi: "Mỗi thành phố có bao nhiêu khách và bao nhiêu nhà
cung cấp?", kể cả thành phố chỉ có một trong hai loại. Cách viết: `LEFT JOIN` lấy mọi thành phố có khách,
rồi `UNION ALL` thêm các thành phố chỉ có nhà cung cấp:

```sql
WITH kh  AS (SELECT city, COUNT(*) AS so_khach FROM customers GROUP BY city),
     ncc AS (SELECT city, COUNT(*) AS so_ncc   FROM suppliers GROUP BY city)
SELECT kh.city, kh.so_khach, ncc.so_ncc
FROM kh LEFT JOIN ncc ON ncc.city = kh.city
UNION ALL
SELECT ncc.city, NULL, ncc.so_ncc
FROM ncc LEFT JOIN kh ON kh.city = ncc.city
WHERE kh.city IS NULL                             -- chỉ thành phố KHÔNG có khách
ORDER BY city;
```

```
+-------------+----------+--------+
| city        | so_khach | so_ncc |
+-------------+----------+--------+
| Đà Nẵng     |        1 |      1 |
| Hà Nội      |        2 |      1 |
| Hồ Chí Minh |     NULL |      1 |
| Huế         |        1 |   NULL |
+-------------+----------+--------+
```

Vế sau chỉ lấy phần "chưa có ở vế trước" (`WHERE kh.city IS NULL`), nên không có dòng trùng và dùng được
`UNION ALL`. Cách viết khác hay gặp là `LEFT JOIN ... UNION ... RIGHT JOIN`, dựa vào `UNION` để khử các
cặp khớp bị lặp; nó ngắn hơn nhưng trả thêm chi phí khử trùng, và sẽ gộp nhầm nếu dữ liệu có những dòng
trùng hợp lệ. Câu trên cũng là ví dụ CTE được dùng hai lần (`kh` và `ncc` đều xuất hiện ở cả hai vế).

Một ứng dụng nữa của `UNION ALL` là tách điều kiện `OR` trên hai cột khác nhau thành hai câu, mỗi câu dùng
được một index riêng. Kỹ thuật này và cách kiểm chứng nó thuộc chương 12.

## 11. Upsert: INSERT ... ON DUPLICATE KEY UPDATE

Ba mục cuối không còn là câu `SELECT` lồng nhau, nhưng thuộc cùng nhóm "một câu lệnh làm việc của nhiều
bước": thêm dòng nếu chưa có, sửa dòng nếu đã có. Tạo bảng dùng riêng cho mục 11 và 12 (vẫn trong
database `ch09`):

```sql
USE ch09;

CREATE TABLE page_views (
  page  VARCHAR(100) NOT NULL,
  day   DATE         NOT NULL,
  views INT          NOT NULL DEFAULT 0,
  title VARCHAR(100) NULL,
  PRIMARY KEY (page, day)
);
```

Mỗi dòng đếm số lượt xem một trang trong một ngày. Khoá chính `(page, day)` bảo đảm mỗi cặp trang và
ngày chỉ có một dòng.

### 11.1 Bài toán "có rồi thì sửa, chưa có thì thêm"

Mỗi lượt xem, ứng dụng cần cộng 1 vào bộ đếm của (trang, ngày), hoặc tạo dòng mới nếu đây là lượt xem
đầu tiên trong ngày. Cách viết ngây thơ ở tầng ứng dụng: `SELECT` xem có dòng chưa, có thì `UPDATE`,
chưa thì `INSERT`. Khi hai request đến cùng lúc:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `SELECT ... WHERE page = '/blog' AND day = '2026-10-01'` | | Không có dòng |
| 2 | | Cùng câu `SELECT` | Không có dòng |
| 3 | `INSERT ... ('/blog', '2026-10-01', 1)` | | Thành công |
| 4 | | `INSERT ... ('/blog', '2026-10-01', 1)` | Lỗi duplicate key (`ERROR 1062`) nhờ khoá chính; nếu bảng không có khoá thì thành hai dòng trùng |

Bọc hai bước trong transaction cũng không cứu được: ở mức isolation mặc định, `SELECT` thường không khoá
gì cả (chương 14, 15). Cách đúng là để database làm cả "kiểm tra" và "ghi" trong một câu lệnh, dựa vào
`PRIMARY KEY` hoặc `UNIQUE` index để phát hiện trùng. Việc này gọi là *upsert* (update + insert).

⚠️ Upsert cần một `PRIMARY KEY` hoặc `UNIQUE` index trên các cột xác định "cùng một dòng". Không có index
đó thì không bao giờ có "trùng", và câu upsert nào cũng chỉ là `INSERT`.

### 11.2 Cú pháp cơ bản

```sql
INSERT INTO page_views (page, day, views)
VALUES ('/home', '2026-10-01', 1)
ON DUPLICATE KEY UPDATE views = views + 1;
-- lần chạy 1: Query OK, 1 row affected   (thêm mới, views = 1)
-- lần chạy 2: Query OK, 2 rows affected  (trùng khoá chính, cập nhật views = 2)
```

Theo tài liệu MySQL: nếu dòng định chèn làm trùng giá trị trong một `UNIQUE` index hoặc `PRIMARY KEY`,
MySQL thực hiện `UPDATE` dòng cũ thay vì chèn. Trong vế `UPDATE`, tên cột (`views` ở vế phải) chỉ giá
trị hiện có của dòng cũ. Câu trên tương đương
`UPDATE page_views SET views = views + 1 WHERE page = '/home' AND day = '2026-10-01'` khi dòng đã tồn tại,
nhưng gói cả hai nhánh vào một câu lệnh.

### 11.3 Tham chiếu giá trị định chèn: alias AS new

Khi chèn nhiều dòng một lúc, hoặc khi giá trị cộng thêm không phải hằng số, vế `UPDATE` cần biết "giá trị
mà dòng này định chèn". Từ MySQL 8.0.19, đặt alias cho dòng định chèn bằng `AS` sau `VALUES`:

```sql
INSERT INTO page_views (page, day, views)
VALUES ('/home',  '2026-10-01', 5),
       ('/about', '2026-10-01', 2) AS new
ON DUPLICATE KEY UPDATE views = page_views.views + new.views;
-- Query OK, 3 rows affected: /home cập nhật (2) + /about thêm mới (1)
-- /home: 2 + 5 = 7, /about: 2
```

`page_views.views` là giá trị đang có, `new.views` là giá trị định chèn. Có thể đặt tên cho từng cột của
alias để viết gọn hơn, ví dụ `AS new(p, d, v) ON DUPLICATE KEY UPDATE views = views + v`.

Code cũ (và nhiều bài viết trên mạng) dùng hàm `VALUES(views)` cho cùng mục đích. Tài liệu MySQL ghi cách
này deprecated từ 8.0.20 và có thể bị bỏ ở bản sau. Code mới nên dùng alias.

### 11.4 Affected rows cho biết điều gì đã xảy ra

Tài liệu MySQL quy định, với mỗi dòng:

| Affected rows | Nghĩa |
|---|---|
| 1 | Dòng được thêm mới |
| 2 | Dòng cũ được cập nhật |
| 0 | Dòng cũ được "cập nhật" thành đúng giá trị nó đang có, tức không đổi gì |

Câu nhiều dòng trả về tổng của từng dòng (ví dụ mục 11.3: 2 + 1 = 3). Trường hợp 0:

```sql
INSERT INTO page_views (page, day, views)
VALUES ('/about', '2026-10-01', 2) AS new
ON DUPLICATE KEY UPDATE views = new.views;
-- Query OK, 0 rows affected: /about đang có views = 2, gán lại 2 không đổi gì
```

Nếu client kết nối với cờ `CLIENT_FOUND_ROWS`, trường hợp này trả về 1 thay vì 0. Ở tầng ứng dụng, đây
là con số bạn nhận được từ `rowCount()` của PDO; chương 19 nói cách cấu hình và đọc nó.

### 11.5 Cạm bẫy

⚠️ Bảng có nhiều unique index. Tài liệu MySQL giải thích: nếu cả `a` (khoá chính) và `b` đều unique, câu
upsert tương đương `UPDATE ... WHERE a = 1 OR b = 2 LIMIT 1`. Khi dòng định chèn trùng `a` với một dòng
và trùng `b` với một dòng khác, chỉ một dòng được cập nhật, và bạn không chọn được là dòng nào:

```sql
CREATE TABLE accounts (
  id       INT PRIMARY KEY,
  email    VARCHAR(100) NOT NULL UNIQUE,
  username VARCHAR(50)  NOT NULL UNIQUE,
  name     VARCHAR(50)  NOT NULL
);
INSERT INTO accounts VALUES (1, 'an@vd.vn', 'an', 'An'), (2, 'binh@vd.vn', 'binh', 'Bình');

-- Trùng email với tài khoản 1 VÀ trùng username với tài khoản 2
INSERT INTO accounts VALUES (3, 'an@vd.vn', 'binh', 'Ai đây?')
ON DUPLICATE KEY UPDATE name = 'Ai đây?';
-- chỉ MỘT trong hai tài khoản 1, 2 bị đổi tên; logic nghiệp vụ gần như chắc chắn đã sai
```

Tài liệu khuyên nói chung nên tránh `ON DUPLICATE KEY UPDATE` trên bảng có nhiều unique index, và câu
upsert trên bảng có nhiều hơn một unique key hoặc primary key bị đánh dấu là không an toàn với
statement-based replication (chương 22). Nếu buộc phải dùng, hãy chắc rằng chỉ một unique index có thể
xung đột trong luồng nghiệp vụ đó.

⚠️ Auto-increment bị tiêu. Tài liệu MySQL ghi: với bảng InnoDB có cột `AUTO_INCREMENT`, câu `INSERT ...
ON DUPLICATE KEY UPDATE` vẫn làm tăng giá trị auto-increment dù cuối cùng nó chỉ cập nhật dòng cũ. Bảng
được upsert liên tục sẽ có id nhảy cóc. Đó là chuyện bình thường: đừng viết code giả định id liên tục,
và với bảng kiểu này hãy dùng `BIGINT` cho id (chương 03).

⚠️ Khoá (lock). Khi gặp trùng, InnoDB đặt exclusive lock lên dòng sẽ được cập nhật (index-record lock nếu
trùng khoá chính, next-key lock nếu trùng một unique key khác). Nhiều upsert đồng thời trên cùng vùng
khoá vì vậy có thể phải chờ nhau, thậm chí deadlock. Chi tiết ở chương 15.

Thêm hai điểm nhỏ theo tài liệu MySQL:

- `INSERT ... SELECT ... ON DUPLICATE KEY UPDATE` bị đánh dấu không an toàn với statement-based
  replication, vì kết quả phụ thuộc thứ tự dòng của `SELECT`, mà thứ tự đó không phải lúc nào cũng xác
  định.
- Trigger: với mỗi dòng, `BEFORE INSERT` luôn chạy, sau đó là `AFTER INSERT` hoặc cặp `BEFORE UPDATE`,
  `AFTER UPDATE` tuỳ dòng có bị trùng hay không (chương 17).

## 12. REPLACE và INSERT IGNORE

### 12.1 REPLACE: xoá rồi chèn

`REPLACE` trông giống upsert nhưng ngữ nghĩa khác hẳn. Theo tài liệu MySQL: nếu dòng cũ có cùng giá trị
`PRIMARY KEY` hoặc `UNIQUE` với dòng mới, dòng cũ bị xoá trước khi dòng mới được chèn. Thuật toán được mô
tả là: thử chèn; trong khi còn lỗi trùng khoá, xoá dòng gây xung đột rồi thử chèn lại.

```sql
UPDATE page_views SET title = 'Trang chủ' WHERE page = '/home';

REPLACE INTO page_views (page, day, views) VALUES ('/home', '2026-10-01', 1);
-- Query OK, 2 rows affected   (1 dòng bị xoá + 1 dòng được chèn)

SELECT page, views, title FROM page_views WHERE page = '/home';
-- /home  1  NULL
```

Hai thứ đã mất: bộ đếm 7 bị thay bằng 1 (`REPLACE` không đọc được giá trị cũ để cộng dồn), và `title`
thành NULL vì cột không được nêu trong `REPLACE` nhận giá trị mặc định, như một `INSERT` mới. Tài liệu
nói rõ: không thể dùng giá trị của dòng hiện có trong dòng mới; viết `SET views = views + 1` thì `views` ở
vế phải được hiểu là `DEFAULT(views)`.

Những hệ quả khác của việc "xoá thật":

- Affected rows là tổng số dòng bị xoá và được chèn. Bảng có nhiều unique index thì một câu `REPLACE`
  một dòng có thể xoá nhiều dòng cũ cùng lúc (mỗi dòng trùng một index khác nhau).
- Trigger `DELETE` chạy (tài liệu trigger ghi rõ `REPLACE` kích hoạt cả trigger `INSERT` và `DELETE`).
- Nếu bảng được bảng khác tham chiếu bằng khoá ngoại, dòng cha bị xoá thật: `ON DELETE CASCADE` sẽ xoá
  luôn các dòng con, còn khoá ngoại kiểu `RESTRICT` làm câu `REPLACE` lỗi.
- Nếu khoá chính là `AUTO_INCREMENT` mà câu `REPLACE` không ghi id (trùng ở một unique key khác), dòng mới
  nhận id mới. Mọi chỗ đang tham chiếu id cũ trở thành tham chiếu treo.
- Cần cả quyền `INSERT` lẫn `DELETE` trên bảng.

`REPLACE` là mở rộng riêng của MySQL, không có trong chuẩn SQL. Nó hợp với một trường hợp hẹp: bảng không
ai tham chiếu tới, và bạn thật sự muốn ghi đè toàn bộ dòng (ví dụ bảng cache tính sẵn). Trong mọi trường
hợp còn lại, `ON DUPLICATE KEY UPDATE` an toàn hơn.

### 12.2 INSERT IGNORE

`INSERT IGNORE` chèn dòng, và nếu dòng trùng khoá thì bỏ qua dòng đó, không báo lỗi:

```sql
INSERT IGNORE INTO page_views (page, day, views) VALUES ('/home', '2026-10-01', 100);
-- Query OK, 0 rows affected, 1 warning    (dòng trùng bị bỏ qua, views vẫn là 1)
```

Nghe rất tiện cho bài toán "chèn nếu chưa có". Nhưng tài liệu MySQL mô tả `IGNORE` rộng hơn thế: các lỗi
"bỏ qua được" đều bị hạ thành warning, kể cả lỗi chuyển đổi dữ liệu. Không có `IGNORE`, giá trị sai làm
câu lệnh dừng; có `IGNORE`, giá trị sai được chỉnh về giá trị gần nhất rồi vẫn được chèn:

```sql
INSERT INTO page_views (page, day, views) VALUES ('/contact', '2026-10-01', 'abc');
-- ERROR 1366 (HY000): Incorrect integer value: 'abc' for column 'views' at row 1

INSERT IGNORE INTO page_views (page, day, views) VALUES ('/contact', '2026-10-01', 'abc');
-- Query OK, 1 row affected, 1 warning     (dòng được chèn với views = 0)
```

Nghĩa là với câu lệnh đó, strict mode coi như bị tắt: dữ liệu rác lọt vào bảng, chỉ để lại warning mà
hầu như không ai đọc. Muốn "chèn nếu chưa có, có rồi thì thôi" mà không nuốt lỗi khác, dùng upsert không
làm gì:

```sql
INSERT INTO page_views (page, day, views) VALUES ('/home', '2026-10-01', 100)
ON DUPLICATE KEY UPDATE views = views;
-- Query OK, 0 rows affected: dòng đã có nên giữ nguyên; giá trị sai kiểu vẫn bị báo lỗi như INSERT thường
```

### 12.3 So sánh ba cách

| | `INSERT ... ON DUPLICATE KEY UPDATE` | `REPLACE` | `INSERT IGNORE` |
|---|---|---|---|
| Khi gặp dòng trùng | Cập nhật dòng cũ theo biểu thức bạn viết | Xoá dòng cũ, chèn dòng mới | Bỏ dòng mới, dòng cũ giữ nguyên |
| Cột không được nhắc tới | Giữ nguyên | Về giá trị mặc định | Giữ nguyên (dòng cũ không đổi) |
| Dùng giá trị cũ (`views + 1`) | Được | Không | Không áp dụng |
| Lỗi khác (sai kiểu, quá dài) | Vẫn báo lỗi | Vẫn báo lỗi | Thành warning, dữ liệu bị chỉnh |
| Khoá ngoại, trigger `DELETE` | Không liên quan | Bị kích hoạt vì có xoá thật | Không liên quan |
| Nên dùng khi | Hầu hết các trường hợp upsert | Ghi đè cả dòng trên bảng không ai tham chiếu | Hiếm khi; ưu tiên upsert không làm gì |

## 13. PostgreSQL: ON CONFLICT, và upsert từ Laravel

### 13.1 INSERT ... ON CONFLICT

PostgreSQL viết upsert bằng mệnh đề `ON CONFLICT` của `INSERT`:

```sql
-- PostgreSQL
INSERT INTO page_views (page, day, views)
VALUES ('/home', '2026-10-01', 1)
ON CONFLICT (page, day) DO UPDATE
  SET views = page_views.views + EXCLUDED.views;

-- Chèn nếu chưa có, có rồi thì thôi
INSERT INTO page_views (page, day, views)
VALUES ('/home', '2026-10-01', 1)
ON CONFLICT DO NOTHING;
```

Các điểm chính theo tài liệu PostgreSQL:

- `(page, day)` là *conflict target*: các cột (hoặc tên constraint, viết `ON CONFLICT ON CONSTRAINT ten`)
  mà xung đột trên đó mới được xử lý. Với `DO UPDATE`, conflict target là bắt buộc; với `DO NOTHING` thì
  được bỏ trống, khi đó mọi xung đột unique đều được bỏ qua. Vì phải nói rõ xung đột trên index nào,
  Postgres không có bẫy "nhiều unique index" như MySQL: xung đột trên một unique index khác vẫn báo lỗi.
- `EXCLUDED` là dòng định chèn, tương đương `new` của MySQL. Tên bảng (hoặc alias) chỉ dòng đang có.
- `DO UPDATE ... WHERE điều_kiện` cho phép chỉ cập nhật khi thoả điều kiện.
- `ON CONFLICT DO UPDATE` bảo đảm kết quả là một `INSERT` hoặc một `UPDATE` nguyên tử, kể cả khi có nhiều
  phiên chạy đồng thời.
- Một câu `INSERT ... ON CONFLICT DO UPDATE` không được tác động lên cùng một dòng hai lần; nếu danh sách
  `VALUES` có hai dòng cùng khoá, câu lệnh báo lỗi. MySQL thì xử lý tuần tự: dòng đầu chèn, dòng sau cập
  nhật dòng vừa chèn.
- `RETURNING` trả về các dòng đã được chèn hoặc cập nhật. MySQL không có `RETURNING`.

PostgreSQL 15 trở lên còn có lệnh `MERGE` theo chuẩn SQL cho các kịch bản đồng bộ phức tạp hơn; MySQL 8.4
không có `MERGE`. Postgres cũng không có lệnh tương đương `REPLACE`.

### 13.2 Bảng đối chiếu

| | MySQL 8.4 | PostgreSQL |
|---|---|---|
| Cú pháp | `INSERT ... [AS new] ON DUPLICATE KEY UPDATE ...` | `INSERT ... ON CONFLICT (cột) DO UPDATE SET ...` |
| "Trùng" được xác định bởi | Mọi `PRIMARY KEY` và `UNIQUE` của bảng | Conflict target (bắt buộc với `DO UPDATE`) |
| Giá trị định chèn | `new.cot` (8.0.19+), cũ: `VALUES(cot)` | `EXCLUDED.cot` |
| Bỏ qua dòng trùng | `INSERT IGNORE` (nuốt cả lỗi khác) hoặc upsert không làm gì | `ON CONFLICT DO NOTHING` (chỉ bỏ qua xung đột) |
| Cập nhật có điều kiện | Biểu thức `IF()`/`CASE` trong vế `UPDATE` | `WHERE` trong `DO UPDATE` |
| Lấy lại kết quả sau khi ghi | Chỉ có affected rows (1/2/0 mỗi dòng) | `RETURNING` trả về các dòng đã chèn hoặc cập nhật |
| Cùng một dòng bị đụng hai lần trong một câu | Được, xử lý tuần tự | Lỗi |

### 13.3 Nhìn từ Laravel

Các hàm của Laravel 13 dưới đây sinh ra đúng những câu SQL trong chương này; chương 19 đi sâu hơn.

| Laravel | SQL sinh ra trên MySQL | Ghi chú |
|---|---|---|
| `->whereHas('orders')`, `->has('orders')` | `WHERE EXISTS (SELECT * FROM orders WHERE ...)` | `doesntHave` sinh `NOT EXISTS` |
| `->withCount('orders')` | Scalar subquery `(SELECT COUNT(*) ...) AS orders_count` trong danh sách `SELECT` | Chi phí như mục 3.3 |
| `->joinLateral($sub, 't')` | `JOIN LATERAL (...) AS t ON TRUE` | Mục 7.5 |
| `DB::table(...)->upsert($rows, $uniqueBy, $update)` | `INSERT ... ON DUPLICATE KEY UPDATE ...` | Xem bên dưới |
| `DB::table(...)->insertOrIgnore($rows)` | `INSERT IGNORE ...` | Tài liệu Laravel cảnh báo nó bỏ qua strict mode của MySQL |

Ba điều về `upsert` cần biết:

- Tài liệu Laravel ghi: driver MySQL và MariaDB bỏ qua tham số thứ hai (`$uniqueBy`) và luôn dùng mọi
  `PRIMARY KEY`, `UNIQUE` của bảng. Đó chính là bẫy nhiều unique index ở mục 11.5.
- Các cột trong tham số thứ ba bị ghi đè bằng giá trị mới, không cộng dồn.
- Trong mã nguồn Laravel 13, grammar MySQL chỉ sinh dạng alias (`... AS laravel_upsert_alias ON DUPLICATE
  KEY UPDATE col = laravel_upsert_alias.col`) khi cấu hình kết nối có `'use_upsert_alias' => true`; mặc định
  nó sinh dạng `col = VALUES(col)`, chính là cú pháp MySQL đã deprecated từ 8.0.20 (mục 11.3).

⚠️ `Model::firstOrCreate()` và `updateOrCreate()` không phải một câu upsert. Trong mã nguồn Laravel 13,
`firstOrCreate()` chạy `SELECT` trước; không thấy thì gọi `createOrFirst()`: thử `INSERT`, nếu gặp lỗi vi
phạm unique thì `SELECT` lại dòng mà request khác vừa chèn. `updateOrCreate()` đi qua `firstOrCreate()` rồi
mới `UPDATE`. Cơ chế này chỉ an toàn khi các cột tra cứu có unique index; không có index đó thì dưới tải
đồng thời vẫn sinh dòng trùng như bảng timeline ở mục 11.1.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| `NOT IN (subquery)` ra tập rỗng, không báo lỗi | Subquery có một NULL, `x <> NULL` là UNKNOWN nên `NOT IN` không bao giờ TRUE | Viết anti-join bằng `NOT EXISTS`; hoặc lọc `IS NOT NULL` trong subquery (mục 4.3) |
| Scalar subquery chạy tốt lúc dev, lỗi 1242 trên production | Điều kiện không bảo đảm tối đa một dòng; dữ liệu tăng thì lộ ra | Lọc theo `PRIMARY KEY`/`UNIQUE`; nói rõ lấy dòng nào bằng `MAX` hoặc `ORDER BY ... LIMIT 1`; hoặc đổi sang `IN` (mục 3.2) |
| `EXISTS` trả về mọi dòng hoặc không dòng nào | Quên điều kiện nối subquery với câu ngoài | Luôn có điều kiện kiểu `o.customer_id = c.id` (mục 5.1) |
| Correlated subquery trả về kết quả lạ | Bảng trong và ngoài cùng alias, cột bị gắn vào bảng của subquery | Đặt alias khác nhau cho hai tầng (mục 6.1) |
| Correlated subquery chậm khủng khiếp | Không có index trên cột tương quan: N × M lần đọc | Index cột tương quan; hoặc viết lại bằng derived table, `LATERAL`, window function và đo bằng `EXPLAIN` (mục 6.2, 6.4) |
| Dùng JOIN để lọc "có liên quan", kết quả bị nhân dòng | JOIN tạo một dòng cho mỗi cặp khớp; `DISTINCT` vá tạm có thể gộp nhầm | Dùng `IN`/`EXISTS` (semijoin) khi chỉ cần lọc (mục 4.2) |
| `> ALL (subquery)` trả về mọi dòng | `ALL` trên tập rỗng là TRUE | Nghĩ trước trường hợp tập rỗng; dùng `MAX` nếu muốn tập rỗng cho kết quả rỗng (mục 4.5) |
| Viết `<> ANY` với ý "không nằm trong" | `<> ANY` nghĩa là "khác ít nhất một phần tử" | Dùng `NOT EXISTS`, `NOT IN` (cẩn thận NULL) hoặc `<> ALL` (mục 4.4) |
| `ERROR 1248: Every derived table must have its own alias` | Mọi bảng trong `FROM` phải có tên | Luôn đặt alias cho derived table (mục 7.1) |
| `ERROR 1093` khi `UPDATE`/`DELETE` đọc chính bảng đó | Hạn chế của MySQL | Bọc phần đọc trong derived table được materialize hoặc CTE (mục 6.5, 8.5) |
| Recursive CTE lỗi `Data too long` hoặc chuỗi bị cắt | Kiểu và độ rộng cột lấy từ phần gốc | `CAST(... AS CHAR(n))` đủ rộng ở phần gốc (mục 9.5) |
| Recursive CTE lỗi 3636 | Thiếu điều kiện dừng, hoặc dữ liệu có vòng | Kiểm tra điều kiện dừng; chặn vòng bằng `path` và `depth`; chỉ tăng `cte_max_recursion_depth` khi câu thật sự cần nhiều vòng (mục 9.6, 9.7) |
| `UNION` làm mất dòng hợp lệ, hoặc chậm | `UNION` khử trùng toàn bộ kết quả | Mặc định `UNION ALL` (mục 10.2) |
| Kết quả `UNION` bị lệch cột | Cột được ghép theo vị trí, không theo tên | Viết các câu `SELECT` với cùng thứ tự cột (mục 10.1) |
| `ORDER BY`/`LIMIT` áp dụng sai phạm vi trong `UNION` | Thiếu ngoặc quanh câu con | Bọc từng câu cần `ORDER BY ... LIMIT` riêng trong ngoặc (mục 10.4) |
| Upsert cập nhật nhầm dòng | Bảng có nhiều unique index, MySQL chỉ cập nhật một dòng trùng | Tránh upsert trên bảng nhiều unique index (mục 11.5) |
| `REPLACE` làm mất dữ liệu cột, xoá dòng con, đổi id | `REPLACE` là xoá rồi chèn | Dùng `ON DUPLICATE KEY UPDATE` (mục 12.1) |
| `INSERT IGNORE` để lọt dữ liệu sai | `IGNORE` hạ mọi lỗi bỏ qua được, kể cả sai kiểu, thành warning | Dùng upsert không làm gì `ON DUPLICATE KEY UPDATE cot = cot` (mục 12.2) |
| `firstOrCreate`/`updateOrCreate` sinh dòng trùng dưới tải | Đây là `SELECT` rồi `INSERT` ở tầng ứng dụng | Thêm unique index cho các cột tra cứu (mục 13.3) |

## Tóm tắt chương

- Subquery là một câu `SELECT` lồng trong câu lệnh khác, luôn nằm trong ngoặc. Theo hình dạng kết quả có
  bốn loại: scalar (một giá trị), row (một dòng), column (một cột), table (bảng); vị trí đặt subquery quyết
  định hình dạng được phép.
- Scalar subquery không có dòng thì ra NULL, nhiều hơn một dòng thì lỗi 1242. Trên tập rỗng `COUNT` cho 0,
  còn `SUM`, `AVG`, `MAX`, `MIN` cho NULL.
- `IN` và `EXISTS` là semijoin: mỗi dòng ngoài xuất hiện tối đa một lần. `NOT IN` gặp một NULL là ra tập
  rỗng, nên anti-join viết bằng `NOT EXISTS`. `ALL` trên tập rỗng là TRUE, `ANY` trên tập rỗng là FALSE.
- Correlated subquery về logic chạy lại cho mỗi dòng ngoài; index trên cột tương quan quyết định chi phí.
  MySQL 8.4 chuyển `IN`/`EXISTS` thành semijoin và `NOT IN`/`NOT EXISTS` thành antijoin khi đủ điều kiện;
  hãy viết đúng nghĩa rồi kiểm tra bằng `EXPLAIN`.
- Derived table là subquery trong `FROM`, bắt buộc có alias; công dụng chính là tổng hợp hai tầng và "gom
  trước rồi mới JOIN". Optimizer merge hoặc materialize nó. `LATERAL` (8.0.14+) cho phép derived table
  nhắc tới bảng đứng trước, hợp với bài "N dòng đầu của mỗi nhóm".
- CTE (`WITH`) đặt tên cho các bước trung gian, đọc từ trên xuống, dùng lại được nhiều lần trong một câu.
  Ở MySQL nó được xử lý như derived table; nó không tự động nhanh hơn hay chậm hơn.
- Recursive CTE gồm phần gốc và phần đệ quy nối bằng `UNION ALL`; mỗi vòng chỉ thấy dòng của vòng trước và
  dừng khi không còn dòng mới. Kiểu cột lấy từ phần gốc; `cte_max_recursion_depth` mặc định 1000; dữ liệu có
  vòng phải được chặn bằng `path` và `depth`.
- `UNION ALL` nối thẳng, `UNION` khử trùng và tốn thêm. Cột ghép theo vị trí, tên lấy từ câu đầu.
  `INTERSECT` và `EXCEPT` có từ 8.0.31, mặc định `DISTINCT`, và `INTERSECT` được tính trước.
- Upsert MySQL: `INSERT ... AS new ON DUPLICATE KEY UPDATE` (alias từ 8.0.19, `VALUES()` deprecated từ
  8.0.20); affected rows 1, 2, 0; tránh dùng trên bảng nhiều unique index. `REPLACE` là xoá rồi chèn,
  `INSERT IGNORE` nuốt cả lỗi dữ liệu. PostgreSQL dùng `ON CONFLICT`, bắt buộc chỉ rõ conflict target cho
  `DO UPDATE`.

## Câu hỏi tự kiểm tra

1. Một subquery đặt sau dấu `=` lần lượt trả về 0 dòng, 1 dòng, 3 dòng. Chuyện gì xảy ra trong từng trường
   hợp, và trường hợp nào nguy hiểm nhất khi đưa lên production? (mục 3.2)
2. Trên dữ liệu mẫu, vì sao `WHERE id NOT IN (SELECT customer_id FROM orders)` ra tập rỗng, còn bản
   `NOT EXISTS` ra Dũng? Viết từng bước logic ba giá trị cho dòng của Dũng ở cả hai cách. (mục 4.3, 5.2)
3. `x > ALL (subquery)` và `x > (SELECT MAX(...) ...)` cho kết quả khác nhau trong những tình huống nào?
4. Khi bảng bên phải có nhiều dòng khớp, `IN (subquery)` và `JOIN` khác nhau ra sao về số dòng kết quả?
   Semijoin là gì?
5. Một correlated subquery chạy trên 50 000 dòng ngoài. Yếu tố nào quyết định nó chạy trong chưa tới một
   giây hay mất nhiều phút? `EXPLAIN` hiện gì để bạn nhận ra subquery đang chạy theo kiểu phụ thuộc vào
   câu ngoài? (mục 6.2)
6. Vì sao bọc phần đọc vào derived table giúp tránh lỗi 1093? Khi nào cách đó lại không có tác dụng?
   (mục 6.5, 7.4)
7. Kể ba thứ khiến một derived table không thể merge vào câu ngoài. Merge và materialize khác nhau thế nào?
8. Trong recursive CTE, ở vòng thứ k phần đệ quy nhìn thấy những dòng nào? Điều gì sẽ xảy ra nếu nó nhìn
   thấy toàn bộ kết quả tích luỹ? (mục 9.2)
9. Vì sao `UNION DISTINCT` chặn được vòng lặp ở ví dụ chỉ có cột `id, parent_id`, nhưng không chặn được khi
   CTE có thêm cột `depth`? (mục 9.7)
10. So sánh `ON DUPLICATE KEY UPDATE`, `REPLACE`, `INSERT IGNORE` trong hai tình huống: bảng có cột không
    được nhắc tới trong câu lệnh, và giá trị chèn sai kiểu. (mục 12.3)

## Bài tập

Mọi bài làm trên database `ch09` của chương. Tự tính tay kết quả mong đợi trước khi chạy, rồi so sánh.

**Bài 1. Subquery ở mọi vị trí.**

a) Liệt kê các khách có tổng tiền đơn đã thanh toán lớn hơn tổng tiền đơn đã thanh toán của An, dùng scalar
subquery.

b) Với mỗi thành phố của khách, tìm đơn có `total` lớn nhất (cần JOIN `orders` với `customers`). Viết hai
cách: correlated subquery và derived table. Thêm một đơn để tạo trường hợp hai đơn bằng nhau trong cùng
thành phố, rồi kiểm tra cả hai cách xử lý trường hợp đó thế nào.

c) Tìm các khách chưa từng có đơn `cancelled`, viết bằng ba cách `NOT IN`, `NOT EXISTS`, `LEFT JOIN ... IS
NULL`. Giải thích vì sao các cách cho kết quả giống hoặc khác nhau trên dữ liệu mẫu. Sau đó chèn thêm một
đơn `cancelled` của khách vãng lai (`customer_id` NULL), chạy lại và giải thích.

**Bài 2. CTE và recursive CTE.**

a) Tạo bảng `employees (id, name, manager_id)` với ít nhất 7 người, 3 cấp quản lý. Viết recursive CTE in ra
chuỗi báo cáo từ một nhân viên lên tới giám đốc, dạng `Giám đốc > Trưởng phòng > Nhân viên`.

b) Với mỗi người quản lý, đếm tổng số người dưới quyền trực tiếp và gián tiếp. Gợi ý: sinh các cặp
(quản lý, nhân viên dưới quyền) bằng recursive CTE, rồi gom ở câu `SELECT` cuối.

c) Cố ý tạo một vòng trong `employees`. Chạy lại câu ở ý (a) và (b), quan sát lỗi, rồi sửa câu truy vấn để nó
dừng an toàn mà không cần tăng `cte_max_recursion_depth`.

d) Viết báo cáo doanh thu theo ngày từ 2026-01-01 đến 2026-02-28 có đủ mọi ngày, ngày không có đơn hiện 0.
Sau đó đổi khoảng thời gian thành 3 năm, quan sát lỗi và xử lý.

**Bài 3. Phép toán tập hợp.**

Trên bảng `orders`: tìm các `customer_id` có đơn ở cả tháng 1 và tháng 2 năm 2026 bằng `INTERSECT`; các
`customer_id` có đơn tháng 2 mà không có đơn tháng 1 bằng `EXCEPT`. Viết lại hai câu bằng `EXISTS`/`NOT
EXISTS`, rồi viết thêm câu thứ hai bằng `NOT IN`. So sánh kết quả của cả ba cách cho câu hỏi thứ hai và giải
thích sự khác nhau (gợi ý: đơn 106).

**Bài 4. Upsert.**

a) Tạo bảng `stock_moves (product_id INT, day DATE, qty INT NOT NULL, PRIMARY KEY (product_id, day))`. Viết
một câu duy nhất nhận một lô nhiều dòng nhập kho và cộng dồn `qty` cho các cặp (sản phẩm, ngày) đã có. Cho
lô có hai dòng trùng khoá với nhau và một dòng trùng khoá với dữ liệu đã có. Dự đoán affected rows trước
khi chạy, rồi kiểm tra.

b) Viết câu tương đương cho PostgreSQL. Lô ở ý (a) chạy trên PostgreSQL sẽ ra sao? Đọc mục 13.1 và giải
thích.

c) (PHP) Viết hàm `recordView(PDO $pdo, string $page, string $day): string` dùng upsert để ghi một lượt xem
vào bảng `page_views`, trả về `'inserted'` hoặc `'updated'` dựa vào số affected rows. Chạy với MySQL trong
Docker, gọi hàm hai lần liên tiếp cho cùng trang và ngày để kiểm tra.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [Subqueries](https://dev.mysql.com/doc/refman/8.4/en/subqueries.html) và các trang con
  ([scalar](https://dev.mysql.com/doc/refman/8.4/en/scalar-subqueries.html),
  [ANY/IN/SOME](https://dev.mysql.com/doc/refman/8.4/en/any-in-some-subqueries.html),
  [ALL](https://dev.mysql.com/doc/refman/8.4/en/all-subqueries.html),
  [row subqueries](https://dev.mysql.com/doc/refman/8.4/en/row-subqueries.html),
  [EXISTS](https://dev.mysql.com/doc/refman/8.4/en/exists-and-not-exists-subqueries.html),
  [correlated](https://dev.mysql.com/doc/refman/8.4/en/correlated-subqueries.html),
  [derived tables](https://dev.mysql.com/doc/refman/8.4/en/derived-tables.html),
  [lateral derived tables](https://dev.mysql.com/doc/refman/8.4/en/lateral-derived-tables.html),
  [subquery errors](https://dev.mysql.com/doc/refman/8.4/en/subquery-errors.html),
  [restrictions](https://dev.mysql.com/doc/refman/8.4/en/subquery-restrictions.html))
- MySQL 8.4, tối ưu subquery:
  [semijoin và antijoin](https://dev.mysql.com/doc/refman/8.4/en/semijoins.html),
  [EXISTS strategy](https://dev.mysql.com/doc/refman/8.4/en/subquery-optimization-with-exists.html),
  [merge hay materialize derived table, view, CTE](https://dev.mysql.com/doc/refman/8.4/en/derived-table-optimization.html),
  [derived condition pushdown](https://dev.mysql.com/doc/refman/8.4/en/derived-condition-pushdown-optimization.html),
  [switchable optimizations](https://dev.mysql.com/doc/refman/8.4/en/switchable-optimizations.html),
  [EXPLAIN output](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html)
- MySQL 8.4: [WITH (Common Table Expressions)](https://dev.mysql.com/doc/refman/8.4/en/with.html)
- MySQL 8.4: [Set operations](https://dev.mysql.com/doc/refman/8.4/en/set-operations.html),
  [INTERSECT](https://dev.mysql.com/doc/refman/8.4/en/intersect.html),
  [EXCEPT](https://dev.mysql.com/doc/refman/8.4/en/except.html),
  [internal temporary tables](https://dev.mysql.com/doc/refman/8.4/en/internal-temporary-tables.html)
- MySQL 8.4: [INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html),
  [REPLACE](https://dev.mysql.com/doc/refman/8.4/en/replace.html),
  [INSERT (IGNORE)](https://dev.mysql.com/doc/refman/8.4/en/insert.html),
  [locks set by SQL statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html),
  [CREATE TRIGGER](https://dev.mysql.com/doc/refman/8.4/en/create-trigger.html)
- MySQL blog: [A new, simple way to figure out why your recursive CTE is running away](https://dev.mysql.com/blog-archive/a-new-simple-way-to-figure-out-why-your-recursive-cte-is-running-away/)
- PostgreSQL: [WITH Queries](https://www.postgresql.org/docs/current/queries-with.html),
  [INSERT (ON CONFLICT)](https://www.postgresql.org/docs/current/sql-insert.html),
  release notes [12](https://www.postgresql.org/docs/release/12.0/) (CTE inlining),
  [14](https://www.postgresql.org/docs/release/14.0/) (`SEARCH`, `CYCLE`),
  [16](https://www.postgresql.org/docs/release/16.0/) (bỏ alias cho subquery trong `FROM`)
- Laravel 13: [Query Builder](https://laravel.com/docs/13.x/queries) (upserts, insertOrIgnore, whereExists),
  mã nguồn [laravel/framework 13.x](https://github.com/laravel/framework/tree/13.x/src/Illuminate/Database)
  (`MySqlGrammar::compileUpsert`, `Eloquent\Builder::firstOrCreate`)
