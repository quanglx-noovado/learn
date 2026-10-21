# Chương 06. Biểu thức, hàm và NULL

> [← Mục lục](README.md) · [← Chương 05: Thao tác dữ liệu: INSERT, UPDATE, DELETE và SELECT cơ bản](05-select-co-ban.md) · [Chương 07: JOIN: kết hợp nhiều bảng →](07-join.md)

**Bạn sẽ học được:**

- Biểu thức là gì, đặt ở đâu trong câu SQL; toán tử số học, so sánh, logic và thứ tự ưu tiên của
  chúng.
- NULL và *logic ba giá trị*: vì sao `x = NULL` không bao giờ đúng, khi nào dùng `IS NULL` và `<=>`,
  vì sao `NOT IN` gặp NULL thì trả về rỗng, NULL đi qua hàm tổng hợp ra sao.
- Các hàm chuỗi, số, ngày giờ hay dùng nhất của MySQL, kèm những bẫy kinh điển: `LENGTH` đếm byte
  chứ không đếm ký tự, `ROUND` làm tròn khác nhau tuỳ kiểu số, cộng một tháng vào ngày 31, múi giờ.
- Viết logic rẽ nhánh ngay trong SQL bằng `CASE`, `IF`, `COALESCE`, `IFNULL`, `NULLIF`.
- Chuyển kiểu tường minh bằng `CAST`/`CONVERT`, hiểu khi nào MySQL tự ép kiểu ngầm và vì sao
  `'abc' = 0` lại cho kết quả đúng.
- Những điểm PostgreSQL làm khác MySQL ở các chủ đề trên.

**Cần biết trước:** [Chương 03](03-kieu-du-lieu.md) (kiểu số, chuỗi, ngày giờ, collation) và
[Chương 05](05-select-co-ban.md) (`SELECT`, `WHERE`, `ORDER BY`, thứ tự thực thi logic).

## Chuẩn bị

Mọi ví dụ SQL viết cho MySQL 8.4, trừ chỗ ghi rõ là PostgreSQL. Chạy MySQL bằng Docker (gõ trong
terminal trên máy của bạn):

```sh
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# Đợi server khởi động xong (vài chục giây) rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Tuỳ chọn `--default-character-set=utf8mb4` bảo client gửi và nhận chuỗi theo UTF-8. Nếu không chỉ
định, client tự đoán bảng mã theo locale của hệ điều hành nơi nó chạy, và có thể đoán sai. Khi đó
các ví dụ tiếng Việt ở mục 4 (đếm ký tự, đếm byte) sẽ cho số khác sách.

Trong client (dấu nhắc `mysql>`), tạo database và dữ liệu mẫu dùng cho cả chương:

```sql
CREATE DATABASE IF NOT EXISTS ch06;
USE ch06;

CREATE TABLE customers (
  id         INT PRIMARY KEY,
  full_name  VARCHAR(50)  NOT NULL,
  email      VARCHAR(100) NULL,
  phone      VARCHAR(20)  NULL,
  city       VARCHAR(50)  NULL,
  birth_date DATE         NULL
);

INSERT INTO customers VALUES
  (1, 'Nguyễn Văn An', 'an@example.com',  '0912345678', 'Hà Nội',      '1990-05-20'),
  (2, 'Trần Thị Bình', NULL,              '0987654321', 'Hồ Chí Minh', '1985-12-01'),
  (3, '  Lê Chi  ',    'CHI@Example.COM', NULL,         NULL,          NULL),
  (4, 'Phạm Dũng',     '',                '912345678',  'Đà Nẵng',     '2000-02-29');

CREATE TABLE orders (
  id          INT PRIMARY KEY,
  customer_id INT           NULL,
  total       DECIMAL(12,2) NOT NULL,
  discount    DECIMAL(12,2) NULL,
  status      VARCHAR(20)   NULL,
  created_at  DATETIME      NOT NULL
);

INSERT INTO orders VALUES
  (101, 1,    250000.00, 20000.00, 'paid',      '2026-01-31 09:15:00'),
  (102, 1,    120000.00, NULL,     'cancelled', '2026-02-14 20:30:00'),
  (103, 2,    990000.00, 0.00,     'paid',      '2026-02-28 23:59:59'),
  (104, 3,     75500.00, NULL,     NULL,        '2026-03-01 00:00:00'),
  (105, NULL,  50000.00, 5000.00,  'pending',   '2026-03-15 14:00:00');
```

Dữ liệu được cài sẵn vài "vết bẩn" giống đời thật, để các mục sau có cái mà xử lý:

- Khách 3 có tên dính dấu cách hai đầu, email viết hoa lẫn thường, không có số điện thoại, thành phố
  và ngày sinh (NULL).
- Khách 4 có email là chuỗi rỗng `''` (khác NULL), số điện thoại bị mất số 0 đầu, sinh ngày 29/02.
- Đơn 102 và 104 không có giảm giá (`discount` là NULL), đơn 103 có giảm giá bằng 0.
- Đơn 104 chưa có trạng thái, đơn 105 không gắn với khách nào.

## 1. Biểu thức là gì

### 1.1 Từ cột có sẵn tới giá trị tính ra

Ở chương 05 bạn lấy dữ liệu ra nguyên trạng: `SELECT total FROM orders`. Thực tế hiếm khi đủ. Người
ta cần số tiền khách phải trả sau giảm giá, tên in hoa, ngày theo kiểu `31/01/2026`, nhãn "đơn lớn"
hay "đơn nhỏ". Những giá trị đó không nằm sẵn trong bảng (và thường cũng không nên lưu, vì suy ra
được) mà được tính lúc đọc:

```sql
SELECT id, total, discount, total - discount AS phai_tra
FROM orders;
```

Kết quả mong đợi:

```
+-----+-----------+----------+-----------+
| id  | total     | discount | phai_tra  |
+-----+-----------+----------+-----------+
| 101 | 250000.00 | 20000.00 | 230000.00 |
| 102 | 120000.00 |     NULL |      NULL |
| 103 | 990000.00 |     0.00 | 990000.00 |
| 104 |  75500.00 |     NULL |      NULL |
| 105 |  50000.00 |  5000.00 |  45000.00 |
+-----+-----------+----------+-----------+
```

`total - discount` là một *biểu thức* (expression): một công thức mà MySQL tính ra đúng một giá
trị. Hai dòng 102 và 104 ra NULL chứ không ra số tiền; vì sao, và sửa thế nào, là chủ đề của mục 3
và mục 7.

Biểu thức được ghép từ các viên gạch sau:

| Thành phần | Ví dụ | Ghi chú |
|---|---|---|
| Hằng (*literal*) | `42`, `3.14`, `'Hà Nội'`, `DATE '2026-10-03'`, `TRUE`, `NULL` | Giá trị viết thẳng trong câu lệnh |
| Tên cột | `total`, `orders.created_at` | Mỗi dòng cho một giá trị khác nhau |
| Toán tử (*operator*) | `+`, `*`, `=`, `<`, `AND`, `LIKE` | Mục 2 |
| Lời gọi hàm (*function call*) | `UPPER(full_name)`, `NOW()` | Mục 4 tới mục 8 |
| Biểu thức lồng nhau | `ROUND(total * 1.1, 0)` | Kết quả biểu thức trong làm đầu vào cho biểu thức ngoài |

Ngoài ra còn biến, hàm do người dùng tự viết (chương 17) và subquery (chương 09). Cách nghĩ giống
hệt biểu thức trong PHP: `$total - $discount` là một biểu thức PHP. Khác biệt là biểu thức SQL do
database tính, và được tính lặp lại cho từng dòng.

### 1.2 Biểu thức được tính trên từng dòng

Khi một biểu thức có tên cột, MySQL tính nó riêng cho mỗi dòng, lấy giá trị cột của chính dòng đó:

```
 bảng orders                              kết quả SELECT
+-----+-----------+----------+            +-----+-----------+
| id  | total     | discount |            | id  | phai_tra  |
+-----+-----------+----------+            +-----+-----------+
| 101 | 250000.00 | 20000.00 | -- tính -> | 101 | 230000.00 |   250000.00 - 20000.00
| 102 | 120000.00 |     NULL | -- tính -> | 102 |      NULL |   120000.00 - NULL
| 103 | 990000.00 |     0.00 | -- tính -> | 103 | 990000.00 |   990000.00 - 0.00
| ... |           |          |            | ... |           |
+-----+-----------+----------+            +-----+-----------+
```

Ba điều cần nhớ:

- Biểu thức trong danh sách `SELECT` tạo ra một cột mới trong *kết quả*. Nó không sửa dữ liệu trong
  bảng. Muốn sửa thì dùng `UPDATE` (mục 1.3).
- Biểu thức trong `WHERE` cũng được tính cho từng dòng; dòng nào cho kết quả đúng (TRUE) thì được
  giữ lại.
- Biểu thức không chứa tên cột, như `1 + 1` hay `NOW()`, cho cùng một giá trị ở mọi dòng.

### 1.3 Biểu thức đặt được ở đâu

Tài liệu MySQL liệt kê: biểu thức dùng được ở mệnh đề `ORDER BY`, `HAVING` của `SELECT`, ở `WHERE`
của `SELECT`, `DELETE`, `UPDATE`, và trong câu `SET`. Cộng thêm danh sách cột của `SELECT` và giá
trị của `INSERT`, ta có bảng:

| Chỗ đặt | Ví dụ | Tác dụng |
|---|---|---|
| Danh sách cột `SELECT` | `SELECT total - discount AS phai_tra` | Tạo cột tính toán trong kết quả |
| `WHERE` | `WHERE total - discount > 100000` | Lọc dòng |
| `ORDER BY` | `ORDER BY CHAR_LENGTH(full_name)` | Sắp xếp theo kết quả tính |
| `GROUP BY`, `HAVING` | `GROUP BY YEAR(created_at)` | Gom nhóm theo kết quả tính (chương 08) |
| `UPDATE ... SET` | `SET total = total * 0.9` | Giá trị mới tính từ giá trị cũ của dòng đó |
| `INSERT ... VALUES` | `VALUES (106, 1, 10000, NULL, 'paid', NOW())` | Giá trị chèn vào |

*Alias* (bí danh) đặt bằng `AS ten` (từ khoá `AS` có thể bỏ) là tên của cột tính toán trong kết
quả. Alias dùng được trong `ORDER BY`, `GROUP BY`, `HAVING`, nhưng **không** dùng được trong
`WHERE`, vì theo thứ tự thực thi logic (chương 05) `WHERE` chạy trước khi danh sách `SELECT` được
tính:

```sql
SELECT id, total - discount AS phai_tra
FROM orders
WHERE phai_tra > 100000;
-- ERROR 1054 (42S22): Unknown column 'phai_tra' in 'where clause'

-- Cách sửa đơn giản: viết lại biểu thức trong WHERE
SELECT id, total - discount AS phai_tra
FROM orders
WHERE total - discount > 100000
ORDER BY phai_tra DESC;          -- ORDER BY thì dùng alias được
-- 103 | 990000.00
-- 101 | 230000.00
```

Dòng 102, 104 (phải trả là NULL) và 105 (45000) không qua được `WHERE`. Vì sao dòng NULL bị loại
sẽ rõ ở mục 3.

### 1.4 SELECT không cần FROM: dùng MySQL như máy tính bỏ túi

MySQL cho phép `SELECT` mà không đọc bảng nào. Đây là cách nhanh nhất để thử một toán tử hay một
hàm trước khi đưa vào câu truy vấn thật:

```sql
SELECT 1 + 1;                 -- 2
SELECT 1 + 1 FROM DUAL;       -- 2
SELECT 2 + 3 * 4 AS a, UPPER('xin chào') AS b;
```

`DUAL` là một tên bảng giả, chỉ để chiều những người quen viết câu `SELECT` nào cũng có `FROM`;
MySQL không bắt buộc nó. Client `mysql` in kết quả câu cuối như sau (output minh hoạ, thời gian
chạy trên máy bạn sẽ khác):

```
mysql> SELECT 2 + 3 * 4 AS a, UPPER('xin chào') AS b;
+----+----------+
| a  | b        |
+----+----------+
| 14 | XIN CHÀO |
+----+----------+
1 row in set (0.00 sec)
```

Hãy giữ thói quen này suốt chương: thấy hàm mới thì `SELECT` thử nó với vài giá trị, nhất là giá trị
biên (chuỗi rỗng, số âm, NULL, ngày cuối tháng).

Một thói quen thứ hai, quan trọng không kém: **đọc warning**. Khi gặp phép tính đáng ngờ, MySQL
thường không báo lỗi mà vẫn trả về một kết quả và ghi lại một *warning* (cảnh báo). Client chỉ in
số lượng warning ở dòng cuối; muốn xem nội dung thì chạy `SHOW WARNINGS` ngay sau đó:

```sql
SELECT 'abc' + 1;
-- kết quả: 1    (client in: 1 row in set, 1 warning)
SHOW WARNINGS;
-- | Warning | 1292 | Truncated incorrect DOUBLE value: 'abc' |
```

MySQL đã lặng lẽ coi `'abc'` là số 0. Mục 8 giải thích quy tắc này và vì sao nó nguy hiểm.

### 1.5 Gọi hàm

*Hàm* (function) nhận vào các *tham số* (argument) và trả về một giá trị: `UPPER('abc')` trả về
`'ABC'`, `ROUND(2.567, 1)` trả về `2.6`. Vài quy ước cần biết:

- Hàm không có tham số vẫn phải có cặp ngoặc: `NOW()`, `PI()`. Một số ít hàm có dạng viết không
  ngoặc theo chuẩn SQL, ví dụ `CURRENT_DATE`, `CURRENT_TIMESTAMP`.
- Theo tài liệu MySQL, mặc định không được có khoảng trắng giữa tên hàm và dấu mở ngoặc (để parser
  phân biệt lời gọi hàm với tên bảng hay tên cột trùng tên hàm); khoảng trắng quanh các tham số thì
  thoải mái. Hãy viết `COUNT(*)`, `UPPER(name)`, đừng viết `COUNT (*)`.
- Hàm lồng được vào nhau, và tham số có thể là biểu thức bất kỳ: `UPPER(TRIM(full_name))`.
- Quy tắc chung của MySQL: một biểu thức có chứa NULL thì cho ra NULL, trừ khi tài liệu của hàm hay
  toán tử đó nói khác. Vì vậy với mỗi hàm, câu hỏi đầu tiên nên đặt ra là "đưa NULL vào thì ra gì?".

MySQL có vài trăm hàm có sẵn; chương này chỉ đi qua những hàm dân backend dùng hằng ngày. Khi cần
hàm khác, tra mục *Functions and Operators* của tài liệu MySQL (link ở cuối chương).

## 2. Toán tử

*Toán tử* (operator) là ký hiệu hay từ khoá nối các giá trị thành biểu thức lớn hơn: `+` nối hai số
thành tổng, `AND` nối hai điều kiện thành một điều kiện. MySQL có bốn nhóm chính: số học, so sánh,
logic, và vài toán tử bit ít dùng.

### 2.1 Toán tử số học

| Toán tử | Ý nghĩa | Ví dụ | Kết quả |
|---|---|---|---|
| `+` | Cộng | `7 + 2` | `9` |
| `-` | Trừ | `7 - 2` | `5` |
| `*` | Nhân | `7 * 2` | `14` |
| `/` | Chia | `7 / 2` | `3.5000` |
| `DIV` | Chia lấy phần nguyên | `7 DIV 2` | `3` |
| `%` hoặc `MOD` | Chia lấy dư | `7 % 2` | `1` |
| `-` một ngôi | Đổi dấu | `-(7 - 2)` | `-5` |

Bốn điều cần biết về số học trong MySQL:

**Phép chia `/` luôn ra số thập phân, kể cả khi chia hai số nguyên.** Với hai toán hạng là số chính
xác (số nguyên hoặc `DECIMAL`), số chữ số sau dấu phẩy của kết quả bằng số chữ số lẻ của số bị chia
cộng với biến hệ thống `div_precision_increment` (mặc định là 4):

```sql
SELECT 7 / 2;          -- 3.5000      (0 chữ số lẻ + 4)
SELECT 1 / 3;          -- 0.3333
SELECT 5.05 / 0.014;   -- 360.714286  (2 chữ số lẻ + 4, ví dụ lấy từ tài liệu MySQL)
SELECT 7 DIV 2;        -- 3
SELECT -7 DIV 2;       -- -3          (DIV bỏ phần lẻ, tức làm tròn về phía 0)
```

Muốn chia lấy phần nguyên thì dùng `DIV`. Đối chiếu: PHP `7 / 2` ra `float(3.5)` và có
`intdiv(7, 2)` ra `3`; còn PostgreSQL `7 / 2` ra `3` vì hai số nguyên chia nhau thì ra số nguyên
(mục 9). Cùng một công thức, ba môi trường cho ba kết quả.

**Chia cho 0 ra NULL, không ném lỗi trong `SELECT`.** `DIV` và `%` cũng vậy. Vì chế độ
`ERROR_FOR_DIVISION_BY_ZERO` nằm trong SQL mode mặc định của MySQL 8.4, câu `SELECT` vẫn chạy nhưng
kèm warning; còn câu ghi dữ liệu (`INSERT`, `UPDATE`) khi bật strict mode (cũng là mặc định) thì báo
lỗi:

```sql
SELECT 10 / 0, 10 DIV 0, 10 % 0;
-- NULL | NULL | NULL      (kèm warning 1365: Division by 0)

UPDATE orders SET discount = total / 0 WHERE id = 101;
-- ERROR 1365 (22012): Division by 0
```

Trong báo cáo, kiểu lỗi này rất dễ lọt: "giá trị trung bình = doanh thu / số đơn", ngày nào không có
đơn thì ra NULL một cách im lặng. Mục 7.4 chỉ cách viết chủ động với `NULLIF`. So với PHP 8: `10 / 0`
và `10 % 0` ném `DivisionByZeroError`.

**`%` giữ dấu của số bị chia.** `MOD(N, M)` trả về phần dư của `N` chia `M`, dấu của kết quả theo
`N` (giống C và PHP, khác Python):

```sql
SELECT MOD(234, 10), 253 % 7, -7 % 3, 7 % -3, MOD(34.5, 3);
-- 4 | 1 | -1 | 1 | 1.5
```

Hệ quả hay gặp: kiểm tra số lẻ bằng `n % 2 = 1` sai với số âm (`-3 % 2` là `-1`). Viết `n % 2 <> 0`.

**Tràn số là lỗi, không âm thầm quay vòng.** Phép `+`, `-`, `*` trên hai số nguyên được tính bằng
`BIGINT` 64 bit; vượt phạm vi thì MySQL báo lỗi, bất kể SQL mode. Và nếu một toán hạng là
`UNSIGNED` thì mặc định kết quả cũng là `UNSIGNED` (trừ khi bật SQL mode `NO_UNSIGNED_SUBTRACTION`),
nên phép trừ ra số âm cũng là tràn (ví dụ từ tài liệu MySQL):

```sql
SELECT 9223372036854775807 + 1;
-- ERROR 1690 (22003): BIGINT value is out of range in '(9223372036854775807 + 1)'

SELECT CAST(0 AS UNSIGNED) - 1;
-- ERROR 1690 (22003): BIGINT UNSIGNED value is out of range in '(cast(0 as unsigned) - 1)'
```

⚠️ Bẫy thực tế: cột tồn kho `stock INT UNSIGNED` đang bằng 0 mà chạy
`UPDATE products SET stock = stock - 1 WHERE id = 1` thì câu lệnh báo lỗi 1690 và cột giữ nguyên.
Lỗi này sinh ra lúc tính biểu thức `stock - 1`, nên có hay không có strict mode cũng vậy. Câu trừ
kho nên kèm điều kiện `AND stock > 0`, rồi kiểm tra số dòng bị ảnh hưởng ở phía ứng dụng để biết có
trừ được hay không.

Cuối cùng, `+` trong MySQL chỉ cộng số, không nối chuỗi. `'Nguyễn' + ' An'` không ra
`'Nguyễn An'` mà ra `0` kèm warning (MySQL cố đổi hai chuỗi sang số). Nối chuỗi dùng `CONCAT`
(mục 4.1).

### 2.2 Toán tử so sánh

| Toán tử | Ý nghĩa | Ví dụ | Kết quả |
|---|---|---|---|
| `=` | Bằng | `2 = 2` | `1` |
| `<>` hoặc `!=` | Khác | `2 <> 3` | `1` |
| `<`, `<=`, `>`, `>=` | Nhỏ hơn, nhỏ hơn hoặc bằng... | `2 >= 3` | `0` |
| `<=>` | Bằng, an toàn với NULL | `NULL <=> NULL` | `1` (mục 3.4) |
| `BETWEEN a AND b` | Tương đương `a <= x AND x <= b` | `5 BETWEEN 1 AND 5` | `1` |
| `IN (...)` | Bằng một giá trị trong danh sách | `3 IN (1, 2, 3)` | `1` |
| `LIKE` | Khớp mẫu với `%` và `_` | `'Hà Nội' LIKE 'Hà%'` | `1` |
| `IS NULL`, `IS NOT NULL` | Kiểm tra NULL | `NULL IS NULL` | `1` |

`BETWEEN`, `IN`, `LIKE` đã học ở chương 05; ở đây chỉ nhấn mạnh hai điều.

**Kết quả so sánh là một con số.** Một phép so sánh cho ra `1` (đúng), `0` (sai) hoặc `NULL` (không
biết, mục 3). MySQL không có kiểu boolean riêng: hằng `TRUE` và `FALSE` chỉ là `1` và `0`, còn kiểu
cột `BOOLEAN` là tên khác của `TINYINT(1)` (chương 03). Vì vậy kết quả so sánh đem cộng được:

```sql
SELECT TRUE, FALSE, 5 > 3, 5 < 3, (5 > 3) + (2 > 1);
-- 1 | 0 | 1 | 0 | 2

SELECT SUM(status = 'paid') AS so_don_paid FROM orders;
-- 2
```

Câu thứ hai là mẹo đếm có điều kiện đặc trưng của MySQL: mỗi dòng `status = 'paid'` cho 1 hoặc 0
(dòng 104 cho NULL và bị `SUM` bỏ qua, mục 3.7), cộng lại ra số đơn đã trả. PostgreSQL không cộng
được giá trị boolean như vậy (mục 9). Theo chiều ngược lại, ở chỗ cần điều kiện, MySQL coi mọi số
khác 0 và khác NULL là đúng: `SELECT 10 IS TRUE, -10 IS TRUE, 0 IS TRUE` ra `1 | 1 | 0`.

**So sánh chuỗi tuân theo collation.** Với collation mặc định `utf8mb4_0900_ai_ci` (không phân biệt
hoa thường và dấu, chương 03), `'a' = 'A'` và `'Hà' = 'ha'` đều đúng. Dấu cách cuối chuỗi cũng tuỳ
collation: các collation Unicode dựa trên UCA 9.0.0 trở lên (họ `_0900_`) có thuộc tính `NO PAD`,
coi dấu cách cuối là một ký tự như mọi ký tự khác; các collation còn lại có thuộc tính `PAD SPACE`,
bỏ qua dấu cách cuối khi so sánh.

```sql
SELECT 'a' = 'A', 'Hà' = 'ha', 'a' = 'a ';
-- 1 | 1 | 0          (collation mặc định utf8mb4_0900_ai_ci, NO PAD)

SELECT 'a' = 'a ' COLLATE utf8mb4_unicode_ci;
-- 1                  (utf8mb4_unicode_ci là PAD SPACE)
```

Điều này đáng nhớ với người dùng Laravel: file `config/database.php` của Laravel đặt collation mặc
định cho kết nối MySQL là `utf8mb4_unicode_ci`, tức `PAD SPACE`.

### 2.3 Toán tử logic

| Toán tử | Ý nghĩa | Ví dụ | Kết quả |
|---|---|---|---|
| `AND` | Đúng khi cả hai vế đúng | `1 AND 0` | `0` |
| `OR` | Đúng khi ít nhất một vế đúng | `1 OR 0` | `1` |
| `NOT` | Phủ định | `NOT 0` | `1` |
| `XOR` | Đúng khi đúng một trong hai vế | `1 XOR 1` | `0` |

Khi một vế là NULL, các toán tử này theo bảng chân trị riêng của logic ba giá trị (mục 3.3).

MySQL còn chấp nhận `&&`, `||`, `!` làm tên khác của `AND`, `OR`, `NOT`, nhưng tài liệu MySQL 8.4
ghi chúng là phần mở rộng ngoài chuẩn và đã *deprecated* (sẽ bị bỏ). Hãy dùng từ khoá chuẩn.

⚠️ Người quen PostgreSQL, SQLite hay Oracle cần đặc biệt cẩn thận với `||`: ở đó (và trong chuẩn
SQL) `||` là nối chuỗi, còn ở MySQL nó là `OR`. `SELECT 'Hà' || 'Nội'` trong MySQL không ra
`'HàNội'` mà ra `0`, vì cả hai chuỗi bị đổi sang số 0 rồi đem `OR`. Chỉ khi bật SQL mode
`PIPES_AS_CONCAT` thì `||` mới là nối chuỗi. Trong MySQL, hãy nối chuỗi bằng `CONCAT`.

### 2.4 Thứ tự ưu tiên

Khi một biểu thức có nhiều toán tử, MySQL tính theo *thứ tự ưu tiên* (operator precedence). Bảng
đầy đủ theo tài liệu MySQL 8.4, từ cao xuống thấp, toán tử cùng dòng có cùng mức:

```
INTERVAL
BINARY, COLLATE
!
- (đổi dấu), ~ (đảo bit)
^
*, /, DIV, %, MOD
-, +
<<, >>
&
|
= (so sánh), <=>, >=, >, <=, <, <>, !=, IS, LIKE, REGEXP, IN, MEMBER OF
BETWEEN, CASE, WHEN, THEN, ELSE
NOT
AND, &&
XOR
OR, ||
= (gán), :=
```

Các toán tử cùng mức được tính từ trái sang phải (trừ phép gán, tính từ phải sang trái). Ba hệ quả
thực tế:

1. Nhân chia trước cộng trừ, như toán phổ thông: `2 + 3 * 4` là `14`, `(2 + 3) * 4` là `20`.
2. So sánh đứng trên `NOT`, nên `NOT total > 100000` nghĩa là `NOT (total > 100000)`.
3. **`AND` đứng trên `OR`.** Đây là nguồn bug kinh điển.

Ví dụ: cần các đơn `paid` hoặc `pending` có tổng tiền trên 500000. Viết thẳng theo lời nói:

```sql
SELECT id FROM orders
WHERE status = 'paid' OR status = 'pending' AND total > 500000;
-- 101, 103
```

Đơn 101 chỉ có 250000 mà vẫn lọt. MySQL đã đọc câu trên thành
`status = 'paid' OR (status = 'pending' AND total > 500000)`: mọi đơn `paid` đều qua, bất kể tiền.
Viết đúng:

```sql
SELECT id FROM orders
WHERE (status = 'paid' OR status = 'pending') AND total > 500000;
-- 103

-- Gọn hơn, cùng nghĩa:
SELECT id FROM orders
WHERE status IN ('paid', 'pending') AND total > 500000;
-- 103
```

Quy tắc: hễ trộn `AND` với `OR` trong cùng điều kiện thì luôn đặt ngoặc, kể cả khi bạn chắc thứ tự
ưu tiên đã đúng. Người đọc sau (và chính bạn sáu tháng sau) sẽ cảm ơn.

Hai lỗi viết khác cũng hay gặp ở người mới:

- `WHERE status = 'paid' OR 'pending'`: MySQL đọc là `(status = 'paid') OR ('pending')`. Chuỗi
  `'pending'` đứng một mình bị đổi sang số 0, tức sai, nên câu lệnh chỉ trả về đơn `paid`, không báo
  lỗi. Viết `status IN ('paid', 'pending')`.
- `SELECT 2 ^ 3` ra `1`, không phải `8`: `^` trong MySQL là XOR theo bit (`10` XOR `11` = `01`).
  Luỹ thừa dùng hàm `POW(2, 3)`.

## 3. NULL và logic ba giá trị

Trước khi học hàm, cần hiểu NULL, vì gần như hàm nào cũng phải trả lời câu hỏi "gặp NULL thì sao".
NULL là nguồn bug số một trong SQL: nó không làm câu lệnh lỗi, nó làm kết quả sai một cách lặng lẽ.

### 3.1 NULL là gì

*NULL* không phải một giá trị như `0` hay `''`. Nó là dấu hiệu "ở đây không có giá trị". Tài liệu
MySQL mô tả NULL là "a missing unknown value": giá trị bị thiếu, không biết là gì. Trong dữ liệu
thật, NULL thường mang một trong hai nghĩa:

- Không biết: khách 3 chắc chắn có ngày sinh, chỉ là ta chưa biết (`birth_date` NULL).
- Không có, không áp dụng: đơn 105 không thuộc khách nào (`customer_id` NULL).

NULL khác hẳn số 0 và chuỗi rỗng:

| Dữ liệu mẫu | Giá trị | Nghĩa |
|---|---|---|
| Đơn 103, `discount` | `0.00` | Biết chắc: giảm 0 đồng |
| Đơn 102, `discount` | `NULL` | Không có thông tin giảm giá |
| Khách 4, `email` | `''` | Có giá trị, giá trị là chuỗi rỗng (ví dụ: khách đã nói là không có email) |
| Khách 2, `email` | `NULL` | Không biết email là gì |

```sql
SELECT 0 IS NULL, '' IS NULL, NULL IS NULL;
-- 0 | 0 | 1
```

Viết NULL không có dấu nháy. `'NULL'` có nháy là một chuỗi bốn ký tự bình thường. Bug "chữ NULL nằm
trong database" hay gặp khi ứng dụng tự ghép chuỗi SQL, hoặc khi import file CSV mà ô trống được ghi
thành chữ `NULL`.

Cột nào được phép NULL là một quyết định thiết kế (chương 02, chương 04: ràng buộc `NOT NULL`). Chương
này học cách làm việc đúng với NULL khi nó đã có mặt.

### 3.2 NULL lan truyền qua biểu thức

Quy tắc chung đã nhắc ở mục 1.5: biểu thức có NULL thì ra NULL, trừ khi hàm hay toán tử đó được
thiết kế riêng để xử lý NULL.

```sql
SELECT NULL + 1, NULL * 0, CONCAT('Xin chào ', NULL), UPPER(NULL);
-- NULL | NULL | NULL | NULL
```

Để ý `NULL * 0` ra NULL chứ không ra 0: MySQL không "đoán" giá trị bị thiếu. Đây chính là lý do
`total - discount` ở mục 1.1 ra NULL với đơn 102 và 104. Cách sửa là thay NULL bằng một giá trị mặc
định có nghĩa trước khi tính, bằng `COALESCE` (mục 7.3):

```sql
SELECT id, total - COALESCE(discount, 0) AS phai_tra FROM orders;
-- 101 | 230000.00
-- 102 | 120000.00
-- 103 | 990000.00
-- 104 |  75500.00
-- 105 |  45000.00
```

Những thứ được thiết kế để làm việc với NULL, sẽ gặp trong chương: `IS NULL`, `IS NOT NULL`, `<=>`
(mục 3.4), `COALESCE`, `IFNULL`, `NULLIF` (mục 7), `CONCAT_WS` (mục 4.1), và các hàm tổng hợp (mục
3.7).

⚠️ Đối chiếu PHP: trong PHP, `250000 - null` ra `250000` vì `null` bị đổi thành 0. SQL thì ra NULL.
Đừng mang trực giác từ PHP sang.

### 3.3 Logic ba giá trị

Trong logic thông thường, một mệnh đề hoặc đúng hoặc sai. SQL có thêm giá trị thứ ba: *UNKNOWN*
(không biết), sinh ra khi so sánh với NULL. Đó là *logic ba giá trị* (three-valued logic). Trong
MySQL, TRUE là `1`, FALSE là `0`, UNKNOWN chính là `NULL`.

Mẹo để suy ra kết quả: coi UNKNOWN là "có thể đúng, có thể sai". Thử thay nó lần lượt bằng TRUE và
FALSE; nếu kết quả như nhau thì đó là kết quả, nếu khác nhau thì kết quả là UNKNOWN. Ví dụ
`FALSE AND UNKNOWN`: dù UNKNOWN là gì thì `FALSE AND ...` vẫn là FALSE, nên kết quả là FALSE.

Bảng chân trị của `AND`:

| `AND` | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| **TRUE** | TRUE | FALSE | UNKNOWN |
| **FALSE** | FALSE | FALSE | FALSE |
| **UNKNOWN** | UNKNOWN | FALSE | UNKNOWN |

Bảng chân trị của `OR`:

| `OR` | TRUE | FALSE | UNKNOWN |
|---|---|---|---|
| **TRUE** | TRUE | TRUE | TRUE |
| **FALSE** | TRUE | FALSE | UNKNOWN |
| **UNKNOWN** | TRUE | UNKNOWN | UNKNOWN |

Còn `NOT TRUE` là FALSE, `NOT FALSE` là TRUE, `NOT UNKNOWN` vẫn là UNKNOWN. `XOR` có một vế NULL thì
ra NULL. Kiểm tra trong MySQL (các ví dụ này có trong tài liệu MySQL):

```sql
SELECT 1 AND NULL, 0 AND NULL, 1 OR NULL, 0 OR NULL, NOT NULL, 1 XOR NULL;
-- NULL | 0 | 1 | NULL | NULL | NULL
```

### 3.4 So sánh với NULL: IS NULL, IS NOT NULL và <=>

Mọi phép so sánh thông thường (`=`, `<>`, `<`, `>`...) có một vế NULL đều ra NULL, kể cả khi cả hai
vế là NULL: hai giá trị "không biết" thì không thể nói chúng bằng nhau.

```sql
SELECT 1 = NULL, 1 <> NULL, NULL = NULL, NULL <> NULL;
-- NULL | NULL | NULL | NULL
```

Hệ quả: `WHERE cot = NULL` không bao giờ trả về dòng nào, và **không báo lỗi**. Muốn tìm NULL phải
dùng `IS NULL`:

```sql
SELECT id FROM customers WHERE email = NULL;       -- Empty set: sai cách, không lỗi
SELECT id FROM customers WHERE email IS NULL;      -- 2
SELECT id FROM customers WHERE email IS NOT NULL;  -- 1, 3, 4
SELECT id FROM customers WHERE email = '';         -- 4
```

Khi cần so sánh "bằng nhau, coi hai NULL là bằng nhau", MySQL có toán tử `<=>` (*NULL-safe equal*).
Nó giống `=` nhưng không bao giờ trả về NULL: hai vế NULL thì ra 1, một vế NULL thì ra 0.

```sql
SELECT 1 <=> 1, NULL <=> NULL, 1 <=> NULL;
-- 1 | 1 | 0

SELECT id FROM customers WHERE city <=> NULL;   -- 3
```

`<=>` hữu ích khi so sánh hai cột cùng cho phép NULL (ví dụ phát hiện thay đổi: `NOT (old_email <=>
new_email)`), hoặc khi tham số truyền vào có thể là NULL. Tài liệu MySQL ghi `<=>` tương đương toán
tử chuẩn SQL `IS NOT DISTINCT FROM`; PostgreSQL có toán tử chuẩn này, còn bảng toán tử so sánh của
MySQL 8.4 không có, nên ở MySQL hãy dùng `<=>`.

Ngoài ra còn nhóm `IS TRUE`, `IS FALSE`, `IS UNKNOWN` (và dạng `IS NOT ...`), kiểm tra một điều
kiện có đúng là TRUE, FALSE hay UNKNOWN hay không. Chúng luôn trả về 1 hoặc 0, không bao giờ NULL:

```sql
SELECT NULL IS UNKNOWN, (1 = NULL) IS UNKNOWN, (5 > 3) IS TRUE, (1 = NULL) IS NOT TRUE;
-- 1 | 1 | 1 | 1
```

Hàm `ISNULL(expr)` trả về 1 nếu `expr` là NULL, ngược lại 0. ⚠️ Đừng nhầm với SQL Server, nơi
`ISNULL(a, b)` lại có nghĩa "a NULL thì lấy b" (tương đương `IFNULL` của MySQL).

### 3.5 WHERE chỉ giữ dòng TRUE: bẫy của <> và NOT

`WHERE` (và `ON` của JOIN, `HAVING`) chỉ giữ dòng có điều kiện là TRUE. Dòng cho FALSE hoặc UNKNOWN
đều bị loại. Xem chuyện gì xảy ra khi lấy "mọi đơn trừ đơn đã huỷ":

```sql
SELECT id FROM orders WHERE status = 'cancelled';    -- 102
SELECT id FROM orders WHERE status <> 'cancelled';   -- 101, 103, 105
```

Đơn 104 không nằm ở kết quả nào. Bảng có 5 đơn, nhưng "huỷ" cộng "không huỷ" chỉ ra 4:

```
 đơn  status       status = 'cancelled'   status <> 'cancelled'
 101  paid         FALSE                  TRUE     -> lấy
 102  cancelled    TRUE      -> lấy       FALSE
 103  paid         FALSE                  TRUE     -> lấy
 104  NULL         UNKNOWN                UNKNOWN           <- rơi khỏi cả hai
 105  pending      FALSE                  TRUE     -> lấy
```

Đảo bằng `NOT` cũng không cứu được: `WHERE NOT (status = 'cancelled')` vẫn loại 104, vì `NOT
UNKNOWN` vẫn là UNKNOWN. Ba cách viết đúng, đều ra `101, 103, 104, 105`:

```sql
-- 1. Nói thẳng ra là chấp nhận NULL: dễ đọc nhất, chạy được ở mọi database
SELECT id FROM orders WHERE status <> 'cancelled' OR status IS NULL;

-- 2. Dùng so sánh an toàn NULL rồi phủ định
SELECT id FROM orders WHERE NOT (status <=> 'cancelled');

-- 3. "Điều kiện huỷ không đúng" (FALSE hoặc UNKNOWN đều tính)
SELECT id FROM orders WHERE (status = 'cancelled') IS NOT TRUE;
```

Cách triệt để hơn là thiết kế: nếu trạng thái luôn phải có, khai báo cột `NOT NULL` kèm `DEFAULT`
(chương 04), cả lớp bug này biến mất.

Chiều ngược lại với ràng buộc `CHECK`: một dòng chỉ vi phạm `CHECK` khi điều kiện là FALSE; TRUE hoặc
UNKNOWN đều được chấp nhận. Vì vậy `CHECK (discount <= total)` vẫn cho chèn dòng có `discount` NULL.

### 3.6 IN và NOT IN gặp NULL

`x IN (a, b, c)` tương đương `x = a OR x = b OR x = c`. Theo tài liệu MySQL, `IN` trả về NULL không
chỉ khi vế trái là NULL, mà cả khi không tìm thấy giá trị khớp và trong danh sách có một NULL:

```sql
SELECT 2 IN (1, 2, NULL);       -- 1     (tìm thấy 2, phần còn lại không quan trọng)
SELECT 3 IN (1, 2, NULL);       -- NULL  (không thấy 3, nhưng "biết đâu NULL là 3")
SELECT NULL IN (1, 2);          -- NULL
SELECT 2 NOT IN (1, 2, NULL);   -- 0
SELECT 3 NOT IN (1, 2, NULL);   -- NULL
```

Dòng cuối là cái bẫy. `3 NOT IN (1, 2, NULL)` nghĩa là `3 <> 1 AND 3 <> 2 AND 3 <> NULL`, tức
`TRUE AND TRUE AND UNKNOWN`, ra UNKNOWN. Nói cách khác: **danh sách của `NOT IN` chỉ cần có một NULL
là `NOT IN` không bao giờ đúng với bất kỳ dòng nào.**

Với `IN` thì không sao: NULL chỉ biến FALSE thành UNKNOWN, đằng nào dòng đó cũng bị `WHERE` loại.
Với `NOT IN` thì nguy hiểm, nhất là khi danh sách đến từ một subquery (chương 09). Thử câu hỏi "khách
nào chưa từng đặt đơn?" trên dữ liệu mẫu, nơi đơn 105 có `customer_id` NULL:

```sql
SELECT id, full_name FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders);
-- Empty set           <- sai! Đáp án đúng là khách 4
```

Subquery trả về `(1, 1, 2, 3, NULL)`. Có NULL trong đó, nên với khách 4, `4 NOT IN (1, 1, 2, 3,
NULL)` ra UNKNOWN và bị loại. Hai cách sửa:

```sql
-- Cách 1 (nên dùng): NOT EXISTS chỉ trả về TRUE hoặc FALSE, không bị NULL làm hỏng
SELECT id, full_name FROM customers c
WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id);
-- 4 | Phạm Dũng

-- Cách 2: loại NULL khỏi danh sách
SELECT id, full_name FROM customers
WHERE id NOT IN (SELECT customer_id FROM orders WHERE customer_id IS NOT NULL);
-- 4 | Phạm Dũng
```

`EXISTS`, `NOT EXISTS` và các cách viết *anti-join* khác được học kỹ ở chương 07 và chương 09.

### 3.7 NULL trong hàm tổng hợp

*Hàm tổng hợp* (aggregate function) như `COUNT`, `SUM`, `AVG`, `MIN`, `MAX` gộp nhiều dòng thành
một giá trị; chương 08 học chúng đầy đủ. Ở đây chỉ cần nhớ cách chúng đối xử với NULL. Theo tài liệu
MySQL, trừ khi ghi khác, hàm tổng hợp **bỏ qua NULL**; ngoại lệ là `COUNT(*)`, vốn đếm dòng chứ không
đếm giá trị.

```sql
SELECT COUNT(*), COUNT(discount), SUM(discount), AVG(discount), AVG(COALESCE(discount, 0))
FROM orders;
-- 5 | 3 | 25000.00 | 8333.333333 | 5000.000000
```

- `COUNT(*)` đếm 5 dòng; `COUNT(discount)` chỉ đếm 3 giá trị khác NULL (`0.00` vẫn được đếm, vì 0
  không phải NULL).
- `SUM(discount)` cộng 20000 + 0 + 5000, bỏ qua hai NULL.
- `AVG(discount)` chia 25000 cho **3** (số giá trị khác NULL), không phải cho 5. Muốn tính trung bình
  trên mọi đơn, coi đơn không có giảm giá là giảm 0, thì phải viết `AVG(COALESCE(discount, 0))`.
  Câu nào đúng là câu hỏi nghiệp vụ, không phải câu hỏi SQL; điều quan trọng là bạn chọn có chủ ý.

Khi không có dòng nào để gộp, `SUM`, `AVG`, `MIN`, `MAX` trả về NULL, còn `COUNT` trả về 0:

```sql
SELECT SUM(total), COUNT(*) FROM orders WHERE status = 'refunded';
-- NULL | 0

SELECT COALESCE(SUM(total), 0) FROM orders WHERE status = 'refunded';
-- 0.00
```

Báo cáo doanh thu theo ngày mà không bọc `COALESCE` thì ngày không có đơn hiện NULL, và cộng tiếp
NULL vào đâu thì chỗ đó cũng thành NULL.

### 3.8 NULL khi sắp xếp, DISTINCT, GROUP BY và UNIQUE

NULL không được đối xử nhất quán ở mọi chỗ trong SQL. Tóm tắt cho MySQL:

| Ngữ cảnh | Hai NULL được coi là | Ví dụ |
|---|---|---|
| `=`, `<>`, `<`, `IN`... | Không biết (UNKNOWN) | `NULL = NULL` ra NULL |
| `<=>`, `IS NULL` | Bằng nhau | `NULL <=> NULL` ra 1 |
| `DISTINCT`, `GROUP BY`, `ORDER BY` | Bằng nhau | Mọi NULL gom vào một nhóm |
| Index `UNIQUE` | Khác nhau | Cột `UNIQUE` cho phép nhiều dòng NULL |

Thêm hai chi tiết:

- `ORDER BY ... ASC` đặt NULL lên đầu, `DESC` đặt NULL xuống cuối (chương 05). MySQL không có cú pháp
  `NULLS FIRST`/`NULLS LAST` như PostgreSQL; muốn NULL nằm cuối khi sắp tăng dần thì sắp theo một
  biểu thức trước: `ORDER BY status IS NULL, status` (`status IS NULL` là 0 với dòng có giá trị, 1
  với dòng NULL, nên dòng NULL xuống cuối).
- Vì index `UNIQUE` cho phép nhiều NULL nhưng không cho phép hai chuỗi rỗng trùng nhau, nên với cột
  như `email UNIQUE` hãy lưu "không có email" là NULL chứ không phải `''`. Khách 4 của dữ liệu mẫu
  là ví dụ về điều không nên làm.

### 3.9 NULL nhìn từ PHP và Laravel

PDO chuyển NULL của SQL thành `null` của PHP và ngược lại. Nhưng ngữ nghĩa thì khác:

```php
<?php
declare(strict_types=1);

$discount = null;

var_dump(null == null);              // bool(true): PHP coi hai null là bằng nhau
var_dump(250000 - $discount);        // int(250000): null bị đổi thành 0
var_dump(250000 - ($discount ?? 0)); // int(250000)
var_dump($discount ?? 'không có');   // string(10) "không có"
```

Toán tử `??` của PHP giống `COALESCE` của SQL: lấy giá trị đầu tiên khác null.

Query builder của Laravel (bản 13.x) có tự lo một phần chuyện này. Đọc mã nguồn `where()`: khi giá
trị so sánh là `null`, nó tự chuyển thành `whereNull` hoặc `whereNotNull`:

```php
DB::table('customers')->where('email', null);          // ... where `email` is null
DB::table('customers')->where('email', '!=', null);    // ... where `email` is not null
```

Nên qua query builder bạn không viết nhầm `= NULL` được. Nhưng hai bẫy ở mục 3.5 và 3.6 thì Laravel
không che:

- `->where('status', '!=', 'cancelled')` sinh ra `status != ?`, vẫn loại đơn có `status` NULL. Muốn
  giữ thì gom điều kiện vào một nhóm:
  `->where(fn ($q) => $q->where('status', '!=', 'cancelled')->orWhereNull('status'))`, sinh ra
  ``where (`status` != ? or `status` is null)``.
- `->whereNotIn('customer_id', $ids)` bind từng phần tử của `$ids` vào `not in (?, ?, ...)`. Nếu
  `$ids` lỡ chứa `null` thì kết quả rỗng, đúng như mục 3.6. Lọc `null` khỏi mảng trước khi truyền.

## 4. Hàm xử lý chuỗi

Hai quy ước chung cho các hàm chuỗi của MySQL: vị trí ký tự **đánh số từ 1** (không phải từ 0 như
PHP), và hầu hết hàm trả về NULL khi một tham số là NULL.

### 4.1 Nối chuỗi: CONCAT và CONCAT_WS

`CONCAT(s1, s2, ...)` nối các tham số lại. Tham số là số được tự đổi sang chuỗi. Nhưng chỉ cần
**một** tham số là NULL thì cả kết quả là NULL:

```sql
SELECT CONCAT('Đơn #', id, ': ', total) AS mo_ta FROM orders WHERE id = 101;
-- Đơn #101: 250000.00

SELECT id, CONCAT(full_name, ' - ', city) AS nhan FROM customers;
-- 1 | Nguyễn Văn An - Hà Nội
-- 2 | Trần Thị Bình - Hồ Chí Minh
-- 3 | NULL                          <- city NULL làm mất cả dòng chữ
-- 4 | Phạm Dũng - Đà Nẵng
```

`CONCAT_WS(sep, s1, s2, ...)` (*concatenate with separator*) nối các tham số, chèn `sep` vào giữa,
và **bỏ qua các tham số NULL** (nhưng không bỏ qua chuỗi rỗng). Rất hợp để ghép địa chỉ, thông tin
liên hệ, nơi một vài phần có thể thiếu:

```sql
SELECT id, CONCAT_WS(', ', full_name, phone, city) AS lien_he FROM customers;
-- 1 | Nguyễn Văn An, 0912345678, Hà Nội
-- 2 | Trần Thị Bình, 0987654321, Hồ Chí Minh
-- 3 |   Lê Chi                         <- phone và city NULL bị bỏ qua, không thừa dấu phẩy
-- 4 | Phạm Dũng, 912345678, Đà Nẵng

SELECT id, CONCAT_WS(' | ', full_name, email) AS x FROM customers WHERE id IN (2, 4);
-- 2 | Trần Thị Bình                   <- email NULL: bỏ qua
-- 4 | Phạm Dũng |                     <- email '': vẫn nối, thừa dấu ngăn cách
```

Nếu chính `sep` là NULL thì kết quả là NULL. Muốn `CONCAT` thường mà không bị NULL "nuốt" thì bọc
từng phần có thể NULL bằng `COALESCE` (mục 7.3): `CONCAT(full_name, ' - ', COALESCE(city, '?'))`.

Nhắc lại từ mục 2: trong MySQL, `+` không nối chuỗi và `||` là `OR`. Chỉ dùng `CONCAT`.

### 4.2 Độ dài: LENGTH đếm byte, CHAR_LENGTH đếm ký tự

Đây là cặp hàm hay bị dùng nhầm nhất với dữ liệu tiếng Việt:

- `LENGTH(s)` trả về độ dài tính bằng **byte**.
- `CHAR_LENGTH(s)` (tên khác: `CHARACTER_LENGTH`) trả về độ dài tính bằng **ký tự** (chính xác là
  *code point*, mục dưới).

Với chữ cái không dấu thì hai số bằng nhau. Với `utf8mb4` (chương 03), một ký tự chiếm từ 1 tới 4
byte: chữ cái tiếng Anh 1 byte, các chữ như `à`, `ă`, `ê`, `ũ`, `đ` 2 byte, các chữ như `ạ`, `ầ`,
`ễ`, `ị`, `ộ` 3 byte, emoji 4 byte.

```sql
SELECT full_name, CHAR_LENGTH(full_name) AS ky_tu, LENGTH(full_name) AS byte_
FROM customers;
-- Nguyễn Văn An | 13 | 16
-- Trần Thị Bình | 13 | 18
--   Lê Chi      | 10 | 11
-- Phạm Dũng     |  9 | 12

SELECT CHAR_LENGTH('😀'), LENGTH('😀');
-- 1 | 4
```

Dùng hàm nào:

- Kiểm tra độ dài theo cảm nhận người dùng ("tên tối đa 50 ký tự"), hay so với giới hạn `VARCHAR(50)`
  (con số trong `VARCHAR(n)` là số ký tự): dùng `CHAR_LENGTH`.
- Ước lượng dung lượng lưu trữ: dùng `LENGTH`.

⚠️ `WHERE LENGTH(full_name) > 15` để tìm "tên dài" sẽ bắt nhầm tên tiếng Việt ngắn nhưng nhiều dấu
(dòng "Trần Thị Bình" 13 ký tự nhưng 18 byte). PHP có đúng cặp bẫy này: `strlen()` đếm byte,
`mb_strlen()` đếm ký tự.

⚠️ `CHAR_LENGTH` đếm code point, không phải "chữ nhìn thấy trên màn hình". Chữ `ệ` có thể được lưu
ở dạng dựng sẵn (một code point, dạng chuẩn hoá NFC, phổ biến nhất) hoặc dạng tổ hợp (chữ `e` cộng
hai dấu, ba code point, dạng NFD). Cùng một chữ nhìn thấy, `CHAR_LENGTH` có thể ra 1 hoặc 3. Dữ liệu
lẫn hai dạng thì so sánh, đếm, tìm kiếm đều có thể lệch; cách chắc ăn là chuẩn hoá về NFC ở tầng ứng
dụng trước khi ghi (PHP có class `Normalizer` của extension intl).

### 4.3 Cắt chuỗi: SUBSTRING, LEFT, RIGHT, LOCATE, SUBSTRING_INDEX

`SUBSTRING(s, pos)` lấy từ vị trí `pos` tới hết; `SUBSTRING(s, pos, len)` lấy `len` ký tự. `pos` âm
nghĩa là đếm từ cuối. Tên khác: `SUBSTR`, và `MID(s, pos, len)`.

```sql
SELECT SUBSTRING('Hà Nội', 4), SUBSTRING('Hà Nội', 1, 2), SUBSTRING('Hà Nội', -3), SUBSTRING('Hà Nội', 0);
-- 'Nội' | 'Hà' | 'Nội' | ''
```

⚠️ Ô cuối: `pos` bằng 0 trả về chuỗi rỗng, vì vị trí đầu tiên là 1. Người quen `substr($s, 0, 2)`
của PHP rất hay viết `SUBSTRING(s, 0, 2)` và nhận về chuỗi rỗng. Một khác biệt nữa: `SUBSTRING` của
MySQL đếm theo ký tự (tài liệu gọi là *multibyte safe*), tương đương `mb_substr` chứ không phải
`substr` (đếm byte) của PHP.

`LEFT(s, n)` và `RIGHT(s, n)` lấy `n` ký tự đầu hoặc cuối. Ví dụ che số điện thoại khi hiển thị:

```sql
SELECT id, phone, CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 3)) AS phone_an
FROM customers;
-- 1 | 0912345678 | 091****678
-- 2 | 0987654321 | 098****321
-- 3 | NULL       | NULL
-- 4 | 912345678  | 912****678
```

`LOCATE(sub, s)` trả về vị trí xuất hiện đầu tiên của `sub` trong `s`, không thấy thì trả về 0
(`INSTR(s, sub)` y hệt nhưng đảo thứ tự tham số). `SUBSTRING_INDEX(s, delim, count)` cắt theo dấu
phân cách: `count` dương lấy phần bên trái của lần xuất hiện thứ `count` tính từ trái, `count` âm lấy
phần bên phải tính từ phải. Tách tên miền của email:

```sql
SELECT id, email, LOCATE('@', email) AS vi_tri, SUBSTRING_INDEX(email, '@', -1) AS ten_mien
FROM customers;
-- 1 | an@example.com  | 3    | example.com
-- 2 | NULL            | NULL | NULL
-- 3 | CHI@Example.COM | 4    | Example.COM
-- 4 |                 | 0    |
```

⚠️ Khi không tìm thấy dấu phân cách, `SUBSTRING_INDEX` trả về nguyên chuỗi:
`SUBSTRING_INDEX('khong-co-a-cong', '@', -1)` ra `'khong-co-a-cong'`. Dữ liệu bẩn sẽ lọt qua mà
không báo gì; kiểm tra `LOCATE('@', email) > 0` nếu cần chắc chắn.

### 4.4 Đổi hoa thường: LOWER và UPPER

`LOWER(s)` và `UPPER(s)` đổi toàn bộ chuỗi sang chữ thường hoặc chữ hoa, theo bảng chữ của charset
(với `utf8mb4` là theo Unicode, nên chữ Việt có dấu được đổi đúng):

```sql
SELECT LOWER(email), UPPER(city) FROM customers WHERE id IN (3, 4);
-- chi@example.com | NULL
--                 | ĐÀ NẴNG
```

Hai điều cần biết:

- Với collation `_ci` (mặc định), phép so sánh vốn đã không phân biệt hoa thường, nên
  `WHERE email = 'chi@example.com'` đã tìm ra khách 3. Viết `WHERE LOWER(email) = '...'` cho cùng kết
  quả nhưng bọc hàm quanh cột, làm MySQL không dùng được index trên `email` theo cách thông thường
  (chương 11). Nếu muốn email luôn ở dạng chữ thường, hãy chuẩn hoá lúc ghi, không phải lúc đọc.
- `LOWER`/`UPPER` không có tác dụng với chuỗi nhị phân (`BINARY`, `VARBINARY`, `BLOB`), vì với dữ
  liệu nhị phân không có khái niệm chữ hoa chữ thường.

### 4.5 Cắt khoảng trắng: TRIM, LTRIM, RTRIM

`TRIM(s)` bỏ dấu cách ở hai đầu; `LTRIM` chỉ bỏ bên trái, `RTRIM` chỉ bỏ bên phải. Dạng đầy đủ
`TRIM([BOTH | LEADING | TRAILING] [ky_tu] FROM s)` cho phép chọn phía và chọn chuỗi cần bỏ:

```sql
-- Bọc trong [ ] để nhìn thấy dấu cách
SELECT CONCAT('[', full_name, ']') AS truoc, CONCAT('[', TRIM(full_name), ']') AS sau
FROM customers WHERE id = 3;
-- [  Lê Chi  ] | [Lê Chi]

SELECT TRIM(LEADING '0' FROM '000123'), TRIM(BOTH 'x' FROM 'xxabcxx'),
       CONCAT('[', LTRIM('  a  '), ']'), CONCAT('[', RTRIM('  a  '), ']');
-- 123 | abc | [a  ] | [  a]
```

Dữ liệu dính dấu cách gây lỗi tìm kiếm rất khó thấy: `WHERE full_name = 'Lê Chi'` không tìm ra khách
3, vì dấu cách ở đầu luôn có nghĩa khi so sánh (dấu cách ở cuối thì tuỳ collation, mục 2.2). Dọn dữ
liệu thì làm hai bước: `SELECT` xem trước những dòng sẽ bị đổi, rồi mới `UPDATE`:

```sql
SELECT id, full_name FROM customers
WHERE CHAR_LENGTH(full_name) <> CHAR_LENGTH(TRIM(full_name));      -- 3

UPDATE customers SET full_name = TRIM(full_name)
WHERE CHAR_LENGTH(full_name) <> CHAR_LENGTH(TRIM(full_name));      -- 1 dòng bị đổi
```

So độ dài thay vì viết `full_name <> TRIM(full_name)` là có chủ ý: với collation `PAD SPACE`, chuỗi
chỉ thừa dấu cách ở cuối được coi là bằng bản đã cắt, và điều kiện `<>` sẽ bỏ sót nó. (Các ví dụ ở
những mục sau không phụ thuộc vào tên khách 3, nên chạy `UPDATE` này cũng không sao.)

⚠️ `TRIM` mặc định chỉ bỏ **dấu cách**, không bỏ tab, xuống dòng (dữ liệu copy từ Excel hay form
thường dính những ký tự này). Khác với `trim()` của PHP, vốn bỏ cả dấu cách, tab, xuống dòng và vài
ký tự khác. Trong MySQL, dùng `REGEXP_REPLACE` với lớp ký tự `[[:space:]]` (dấu cách, tab, xuống
dòng, về đầu dòng):

```sql
SELECT CHAR_LENGTH(TRIM('\tabc\n'));                                   -- 5: không bỏ được gì
SELECT REGEXP_REPLACE('\tabc\n', '^[[:space:]]+|[[:space:]]+$', '');   -- 'abc'
```

(`'\t'` và `'\n'` trong chuỗi MySQL là ký tự tab và xuống dòng.)

### 4.6 Thay thế và đệm: REPLACE, LPAD, RPAD

`REPLACE(s, tu, thanh)` thay **mọi** lần xuất hiện của `tu` bằng `thanh`. Theo tài liệu MySQL,
`REPLACE` luôn so khớp **phân biệt hoa thường**, kể cả khi collation của cột không phân biệt:

```sql
SELECT REPLACE('090 123 4567', ' ', '');     -- '0901234567'
SELECT REPLACE('Hà Nội', 'hà', 'HN');        -- 'Hà Nội': không đổi gì
SELECT 'Hà Nội' LIKE 'hà%';                  -- 1: LIKE thì theo collation, không phân biệt hoa thường
```

`LPAD(s, n, pad)` đệm thêm `pad` vào bên trái cho tới khi đủ `n` ký tự; `RPAD` đệm bên phải. Ứng dụng:
sinh mã hiển thị có độ dài cố định, hay sửa số điện thoại bị mất số 0 đầu (khách 4):

```sql
SELECT CONCAT('DH', LPAD(id, 6, '0')) AS ma_don FROM orders WHERE id = 101;   -- DH000101

SELECT id, phone, LPAD(phone, 10, '0') AS phone_sua
FROM customers WHERE CHAR_LENGTH(phone) = 9;
-- 4 | 912345678 | 0912345678
```

⚠️ Nếu chuỗi gốc **dài hơn** `n`, `LPAD`/`RPAD` không giữ nguyên mà **cắt** nó còn `n` ký tự:
`LPAD('1234567', 6, '0')` ra `'123456'`. Mã đơn vượt 6 chữ số sẽ bị cắt mất đuôi mà không báo lỗi.

### 4.7 Bảng tra nhanh hàm chuỗi

| Hàm | Làm gì | Ví dụ | Kết quả |
|---|---|---|---|
| `CONCAT(a, b, ...)` | Nối; một tham số NULL thì ra NULL | `CONCAT('a', NULL)` | `NULL` |
| `CONCAT_WS(sep, a, ...)` | Nối có dấu ngăn cách, bỏ qua NULL | `CONCAT_WS('-', 'a', NULL, 'b')` | `'a-b'` |
| `LENGTH(s)` | Độ dài theo byte | `LENGTH('Hà')` | `3` |
| `CHAR_LENGTH(s)` | Độ dài theo ký tự | `CHAR_LENGTH('Hà')` | `2` |
| `SUBSTRING(s, pos, len)` | Cắt chuỗi, vị trí từ 1, `pos` âm đếm từ cuối | `SUBSTRING('abcdef', 2, 3)` | `'bcd'` |
| `LEFT(s, n)`, `RIGHT(s, n)` | `n` ký tự đầu, cuối | `RIGHT('abcdef', 2)` | `'ef'` |
| `LOCATE(sub, s)` | Vị trí xuất hiện đầu tiên, không thấy ra 0 | `LOCATE('c', 'abcabc')` | `3` |
| `SUBSTRING_INDEX(s, d, n)` | Cắt theo dấu phân cách | `SUBSTRING_INDEX('a.b.c', '.', 2)` | `'a.b'` |
| `LOWER(s)`, `UPPER(s)` | Đổi hoa thường | `UPPER('đà')` | `'ĐÀ'` |
| `TRIM(s)`, `LTRIM`, `RTRIM` | Bỏ dấu cách hai đầu, trái, phải | `TRIM('  a ')` | `'a'` |
| `REPLACE(s, a, b)` | Thay mọi `a` bằng `b`, phân biệt hoa thường | `REPLACE('a-b-c', '-', '')` | `'abc'` |
| `LPAD(s, n, p)`, `RPAD` | Đệm (hoặc cắt) cho đủ `n` ký tự | `LPAD('7', 3, '0')` | `'007'` |
| `REPEAT(s, n)` | Lặp `n` lần | `REPEAT('ab', 3)` | `'ababab'` |
| `REVERSE(s)` | Đảo ngược | `REVERSE('abc')` | `'cba'` |
| `REGEXP_REPLACE(s, pat, r)` | Thay theo biểu thức chính quy | `REGEXP_REPLACE('a1b22', '[0-9]+', '#')` | `'a#b#'` |

## 5. Hàm số

### 5.1 Số chính xác và số xấp xỉ

Trước khi làm tròn, cần biết MySQL đang tính trên loại số nào. Tài liệu MySQL chia làm hai:

- Số *chính xác* (exact-value): số nguyên và `DECIMAL`. Hằng số viết có hoặc không có phần thập phân
  thuộc loại này: `1`, `.2`, `3.4`, `-6.78`. Phép tính trên chúng đúng tuyệt đối.
- Số *xấp xỉ* (approximate-value): `FLOAT` và `DOUBLE`. Hằng số viết dạng khoa học (có `E`) thuộc
  loại này: `1.2E3`, `25E-1`. Chúng lưu dạng nhị phân nên có sai số (chương 03).

```sql
SELECT (.1 + .2) = .3;           -- 1: số chính xác, tính đúng
SELECT (.1E0 + .2E0) = .3E0;     -- 0: số xấp xỉ, 0.1 không biểu diễn đúng được ở hệ nhị phân
```

Hai hằng `2.34` và `2.34E0` trông như nhau nhưng một cái là `DECIMAL`, một cái là `DOUBLE`. Với tiền,
quy tắc là: cột `DECIMAL`, và giữ phép tính ở loại chính xác. Cẩn thận với chuỗi bị ép sang số: phép
toán trên chuỗi được tính theo kiểu số thực xấp xỉ (mục 8.2).

### 5.2 Làm tròn: ROUND, TRUNCATE, CEIL, FLOOR

Bốn hàm, bốn cách "bỏ phần lẻ" khác nhau:

| Hàm | Quy tắc | `2.5` | `-2.5` | `1.58` | `-1.58` |
|---|---|---|---|---|---|
| `ROUND(x)` | Về số nguyên gần nhất; đúng nửa thì ra xa số 0 (với số chính xác) | `3` | `-3` | `2` | `-2` |
| `TRUNCATE(x, 0)` | Bỏ phần lẻ, tức đi về phía số 0 | `2` | `-2` | `1` | `-1` |
| `CEIL(x)` (= `CEILING`) | Số nguyên nhỏ nhất không nhỏ hơn `x` | `3` | `-2` | `2` | `-1` |
| `FLOOR(x)` | Số nguyên lớn nhất không lớn hơn `x` | `2` | `-3` | `1` | `-2` |

Để ý cột số âm: `FLOOR(-2.5)` là `-3` nhưng `TRUNCATE(-2.5, 0)` là `-2`. Nhầm hai hàm này là lỗi hay
gặp khi xử lý số âm (tiền hoàn, chênh lệch).

**`ROUND(x, D)`** làm tròn tới `D` chữ số sau dấu phẩy, `D` mặc định là 0. `D` âm thì làm tròn sang
bên trái dấu phẩy, tiện để làm tròn tiền Việt tới hàng nghìn:

```sql
SELECT ROUND(1.298, 1), ROUND(23.298, -1), ROUND(123456, -3), ROUND(123500, -3);
-- 1.3 | 20 | 123000 | 124000
```

Kiểu của kết quả theo kiểu của tham số đầu (ví dụ từ tài liệu MySQL): `ROUND(150.000, 2)` ra `150.00`,
còn `ROUND(150, 2)` ra `150` vì 150 là số nguyên.

⚠️ **Quy tắc làm tròn phụ thuộc loại số.** Với số chính xác, `ROUND` làm tròn "nửa ra xa số 0"
(*round half away from zero*). Với số xấp xỉ, kết quả phụ thuộc thư viện C của hệ điều hành; theo tài
liệu MySQL, trên nhiều hệ thống đó là "làm tròn nửa về số chẵn" (*round half to even*):

```sql
SELECT ROUND(2.5), ROUND(-2.5), ROUND(2.5E0), ROUND(-2.5E0);
-- 3 | -3 | 2 | -2         (ví dụ trong tài liệu MySQL)
```

Hệ quả: cùng một con số, lưu ở cột `DOUBLE` và cột `DECIMAL` có thể làm tròn ra hai kết quả khác
nhau. Thêm một lý do để tiền nằm trong `DECIMAL`. (`round()` của PHP mặc định cũng làm tròn nửa ra xa
số 0: `round(2.5)` ra `3`, `round(-2.5)` ra `-3`.)

**`TRUNCATE(x, D)`** cắt bỏ (không làm tròn) phần sau chữ số thứ `D`; tham số `D` là bắt buộc:

```sql
SELECT TRUNCATE(1.999, 1), TRUNCATE(-1.999, 1), TRUNCATE(122, -2);
-- 1.9 | -1.9 | 100
```

Hàm `TRUNCATE()` không liên quan gì tới câu lệnh `TRUNCATE TABLE` (xoá sạch dữ liệu bảng, chương 04),
chỉ trùng tên.

**`CEIL` và `FLOOR`** hay dùng trong tính toán số lượng. Ví dụ số trang khi có 101 dòng, mỗi trang 20
dòng:

```sql
SELECT CEIL(101 / 20);            -- 6   (101 / 20 = 5.0500, làm tròn lên)
SELECT FLOOR(37 / 10) * 10;       -- 30  (gom tuổi 37 vào nhóm "30-39")
```

### 5.3 Các hàm số khác

| Hàm | Làm gì | Ví dụ | Kết quả |
|---|---|---|---|
| `ABS(x)` | Giá trị tuyệt đối | `ABS(-32)` | `32` |
| `SIGN(x)` | Dấu: -1, 0 hoặc 1 | `SIGN(-32)` | `-1` |
| `MOD(n, m)`, `n % m` | Phần dư, dấu theo `n` (mục 2.1) | `MOD(29, 9)` | `2` |
| `POW(x, y)` | Luỹ thừa (`^` là XOR theo bit, mục 2.4) | `POW(2, -2)` | `0.25` |
| `SQRT(x)` | Căn bậc hai | `SQRT(16)` | `4` |
| `RAND()` | Số ngẫu nhiên trong khoảng [0, 1) | `FLOOR(1 + RAND() * 6)` | Số nguyên 1 tới 6 |
| `GREATEST(a, b, ...)`, `LEAST(...)` | Lớn nhất, nhỏ nhất trong các tham số | `GREATEST(3, 7, 5)` | `7` |

`ABS`, `SIGN`, `MOD`, `POW`, `SQRT` trả về NULL khi tham số là NULL. Riêng `GREATEST` và `LEAST` có
một điểm dễ quên: theo tài liệu, chỉ cần **một** tham số là NULL thì kết quả là NULL, nên
`GREATEST(total - discount, 0)` ra NULL với đơn không có giảm giá. Bọc tham số có thể NULL bằng
`COALESCE` trước.

### 5.4 Làm tròn khi tính tiền, và chuyện hiển thị số

**Làm tròn ở bước nào cũng là một quyết định.** Làm tròn từng dòng rồi cộng khác với cộng rồi mới làm
tròn:

```sql
SELECT SUM(ROUND(x)) AS tron_tung_dong, ROUND(SUM(x)) AS cong_roi_tron
FROM (SELECT 0.4 AS x UNION ALL SELECT 0.4 UNION ALL SELECT 0.4) AS t;
-- 0 | 1
```

Hoá đơn có nhiều dòng hàng, thuế tính trên từng dòng hay trên tổng là quy định nghiệp vụ (và kế
toán). Điều quan trọng là chọn một cách, dùng nhất quán ở mọi nơi (SQL, PHP, báo cáo), và giữ giá trị
chưa làm tròn ở dạng `DECIMAL` càng lâu càng tốt.

**Hiển thị số đẹp: `FORMAT`.** `FORMAT(x, D)` làm tròn `x` tới `D` chữ số lẻ và chèn dấu phân cách
hàng nghìn, theo locale `en_US` nếu không chỉ định (ví dụ từ tài liệu MySQL):

```sql
SELECT FORMAT(12332.123456, 4);       -- '12,332.1235'
SELECT FORMAT(12332.2, 0);            -- '12,332'
SELECT FORMAT(12332.2, 2, 'de_DE');   -- '12.332,20'
```

⚠️ `FORMAT` trả về **chuỗi**. Đừng sắp xếp hay tính toán tiếp trên kết quả của nó:
`ORDER BY FORMAT(total, 0)` so sánh chuỗi từng ký tự, nên `'120,000'` và `'250,000'` đứng trước
`'50,000'` (vì ký tự đầu `'1'`, `'2'` nhỏ hơn `'5'`), ngược với thứ tự số. Thường thì để SQL trả về
số, và định dạng ở tầng hiển thị (PHP: `number_format(250000, 0, ',', '.')` ra `250.000`).

## 6. Hàm ngày giờ

Kiểu `DATE`, `DATETIME`, `TIMESTAMP` và chuyện lưu múi giờ đã học ở chương 03. Mục này học cách tính
toán trên chúng. Mọi ví dụ dùng ngày cố định để bạn ra đúng kết quả như sách; trong code thật, thay
bằng `NOW()` hoặc `CURDATE()`.

### 6.1 Lấy thời điểm hiện tại

| Hàm | Trả về | Ví dụ kết quả (output minh hoạ) |
|---|---|---|
| `NOW()` (= `CURRENT_TIMESTAMP`) | Ngày giờ hiện tại, theo múi giờ của session | `2026-10-03 14:05:09` |
| `CURDATE()` (= `CURRENT_DATE`) | Ngày hiện tại | `2026-10-03` |
| `CURTIME()` | Giờ hiện tại, theo múi giờ của session | `14:05:09` |
| `UTC_TIMESTAMP()` | Ngày giờ hiện tại theo UTC, không phụ thuộc session | `2026-10-03 07:05:09` |
| `NOW(3)` | Như `NOW()` nhưng có 3 chữ số phần lẻ của giây (từ 0 tới 6) | `2026-10-03 14:05:09.123` |

Một điểm tinh tế: theo tài liệu MySQL, các hàm trả về thời điểm hiện tại chỉ được tính **một lần
cho mỗi câu lệnh**, lúc câu lệnh bắt đầu chạy. Gọi `NOW()` ba lần trong một câu thì ra ba giá trị y
hệt, kể cả khi câu chạy mất vài giây. Nhờ vậy một câu `UPDATE` hàng triệu dòng với
`SET updated_at = NOW()` cho mọi dòng cùng một mốc thời gian.

`SYSDATE()` thì khác: trả về thời điểm đúng lúc nó được gọi, nên có thể khác nhau ngay trong một câu
lệnh (ví dụ trong tài liệu MySQL):

```sql
SELECT NOW(), SLEEP(2), NOW();
-- 2006-04-12 13:47:36 | 0 | 2006-04-12 13:47:36

SELECT SYSDATE(), SLEEP(2), SYSDATE();
-- 2006-04-12 13:47:44 | 0 | 2006-04-12 13:47:46
```

Tài liệu MySQL nêu hai hệ quả của `SYSDATE()`: nó không an toàn cho replication khi binary log ghi
theo câu lệnh (statement-based, chương 22), và biểu thức chứa nó không dùng được index. Cứ dùng
`NOW()`.

### 6.2 Tách các phần của ngày giờ

```sql
SELECT DATE('2026-01-31 09:15:00'),          -- 2026-01-31
       YEAR('2026-01-31 09:15:00'),          -- 2026
       MONTH('2026-01-31 09:15:00'),         -- 1
       DAY('2026-01-31 09:15:00'),           -- 31
       HOUR('2026-01-31 09:15:00'),          -- 9
       DAYNAME('2026-01-31'),                -- Saturday
       DAYOFWEEK('2026-01-31'),              -- 7   (1 = Chủ nhật, ..., 7 = thứ Bảy)
       WEEKDAY('2026-01-31'),                -- 5   (0 = thứ Hai, ..., 6 = Chủ nhật)
       LAST_DAY('2026-02-10'),               -- 2026-02-28  (ngày cuối tháng)
       EXTRACT(YEAR_MONTH FROM '2026-01-31 09:15:00');   -- 202601
```

⚠️ `DAYOFWEEK` và `WEEKDAY` đánh số khác nhau: một cái bắt đầu từ Chủ nhật = 1, một cái từ thứ Hai =
0. Viết báo cáo "đơn theo thứ trong tuần" thì kiểm tra lại bằng một ngày đã biết trước khi tin con số.
Tên thứ, tên tháng (`DAYNAME`, `MONTHNAME`, `%W`, `%M`) viết bằng ngôn ngữ do biến `lc_time_names`
quyết định, mặc định là tiếng Anh.

### 6.3 Cộng trừ thời gian: DATE_ADD, DATE_SUB và INTERVAL

Cộng trừ thời gian dùng `DATE_ADD(d, INTERVAL n don_vi)`, `DATE_SUB(...)`, hoặc viết gọn bằng toán tử
`d + INTERVAL n don_vi`, `d - INTERVAL n don_vi`. Đơn vị hay dùng: `SECOND`, `MINUTE`, `HOUR`, `DAY`,
`WEEK`, `MONTH`, `QUARTER`, `YEAR`.

```sql
SELECT DATE_ADD('2026-01-31', INTERVAL 7 DAY);           -- 2026-02-07
SELECT '2026-01-31 09:15:00' + INTERVAL 1 HOUR;          -- 2026-01-31 10:15:00
SELECT '2026-01-01' - INTERVAL 1 SECOND;                 -- 2025-12-31 23:59:59
SELECT id FROM orders WHERE created_at >= '2026-03-15' - INTERVAL 30 DAY;   -- 102, 103, 104, 105
```

Ở câu cuối, mốc là `2026-02-13` (15/03 lùi 30 ngày, nhớ tháng Hai năm 2026 có 28 ngày), nên chỉ đơn
101 ngày 31/01 bị loại. Với điều kiện thời gian, hãy tự tính mốc bằng tay một lần để chắc câu lệnh
đúng ý.

**Cộng tháng vào cuối tháng.** Khi cộng `MONTH`, `YEAR_MONTH` hoặc `YEAR` mà ngày kết quả không tồn tại
trong tháng mới, MySQL lùi về ngày cuối cùng của tháng đó:

```sql
SELECT DATE_ADD('2026-01-31', INTERVAL 1 MONTH);    -- 2026-02-28
SELECT DATE_ADD('2024-01-31', INTERVAL 1 MONTH);    -- 2024-02-29  (2024 là năm nhuận)
SELECT DATE_ADD('2000-02-29', INTERVAL 1 YEAR);     -- 2001-02-28
```

⚠️ Bẫy "trôi ngày": cộng dồn từng tháng một khác với cộng một lần nhiều tháng.

```sql
SELECT DATE_ADD('2026-01-31', INTERVAL 2 MONTH);                               -- 2026-03-31
SELECT DATE_ADD(DATE_ADD('2026-01-31', INTERVAL 1 MONTH), INTERVAL 1 MONTH);   -- 2026-03-28
```

Hệ thống thu phí hàng tháng mà tính kỳ sau bằng "kỳ trước + 1 tháng" sẽ trôi dần về ngày 28 sau khi
đi qua tháng Hai. Cách đúng: luôn tính từ mốc gốc, `ngay_bat_dau + INTERVAL n MONTH` với `n` là số kỳ.

Ngày không hợp lệ hoặc không đầy đủ làm phép cộng trừ ra NULL (ví dụ trong tài liệu MySQL):
`'2005-03-32' + INTERVAL 1 MONTH` ra NULL.

### 6.4 Khoảng cách giữa hai thời điểm: DATEDIFF và TIMESTAMPDIFF

- `DATEDIFF(a, b)` trả về `a - b` tính bằng **ngày**, và **chỉ dùng phần ngày**, bỏ qua giờ phút giây.
- `TIMESTAMPDIFF(don_vi, a, b)` trả về `b - a` theo đơn vị chỉ định, là số nguyên (phần lẻ bị bỏ).

Để ý thứ tự tham số ngược nhau: `DATEDIFF` đặt mốc **sau** lên trước, `TIMESTAMPDIFF` đặt mốc
**trước** lên trước.

```sql
SELECT DATEDIFF('2026-03-15', '2026-01-31');                                   -- 43
SELECT DATEDIFF('2026-03-01 00:00:00', '2026-02-28 23:59:59');                 -- 1
SELECT TIMESTAMPDIFF(SECOND, '2026-02-28 23:59:59', '2026-03-01 00:00:00');    -- 1
SELECT TIMESTAMPDIFF(DAY,    '2026-02-28 23:59:59', '2026-03-01 00:00:00');    -- 0
```

Hai thời điểm cách nhau đúng một giây (đơn 103 và đơn 104): `DATEDIFF` nói "1 ngày" vì chỉ nhìn phần
ngày, `TIMESTAMPDIFF(DAY, ...)` nói "0 ngày" vì chưa đủ 24 giờ. Câu hỏi nghiệp vụ "giao hàng trong
vòng 1 ngày" cần chọn hàm theo đúng nghĩa của chữ "ngày".

**Tính tuổi.** `TIMESTAMPDIFF(YEAR, ngay_sinh, hom_nay)` đếm số năm tròn:

```sql
SELECT id, birth_date,
       TIMESTAMPDIFF(YEAR, birth_date, '2026-10-03') AS tuoi_dung,
       YEAR('2026-10-03') - YEAR(birth_date)         AS tuoi_sai
FROM customers;
-- 1 | 1990-05-20 | 36   | 36
-- 2 | 1985-12-01 | 40   | 41      <- chưa tới sinh nhật tháng 12
-- 3 | NULL       | NULL | NULL
-- 4 | 2000-02-29 | 26   | 26
```

Lấy năm trừ năm là công thức sai kinh điển: nó cộng tuổi ngay từ ngày 1/1 chứ không phải từ ngày
sinh nhật.

### 6.5 Định dạng và đọc ngày: DATE_FORMAT và STR_TO_DATE

`DATE_FORMAT(d, dinh_dang)` đổi ngày giờ thành chuỗi theo mẫu. Mỗi thành phần là một ký hiệu bắt đầu
bằng `%`. Những ký hiệu hay dùng (đầy đủ trong tài liệu MySQL):

| Ký hiệu | Ý nghĩa | Ví dụ với `2026-01-31 09:15:00` |
|---|---|---|
| `%Y` | Năm 4 chữ số | `2026` |
| `%y` | Năm 2 chữ số | `26` |
| `%m` | Tháng 2 chữ số (`00` tới `12`) | `01` |
| `%c` | Tháng không có số 0 đầu | `1` |
| `%d` | Ngày 2 chữ số | `31` |
| `%e` | Ngày không có số 0 đầu | `31` |
| `%H` | Giờ 24h, 2 chữ số | `09` |
| `%h` | Giờ 12h, 2 chữ số | `09` |
| `%i` | **Phút**, 2 chữ số | `15` |
| `%s` | Giây, 2 chữ số | `00` |
| `%p` | `AM` hoặc `PM` | `AM` |
| `%W` | Tên thứ | `Saturday` |
| `%M` | **Tên tháng** | `January` |
| `%T` | Giờ đầy đủ 24h, tương đương `%H:%i:%s` | `09:15:00` |

```sql
SELECT id, DATE_FORMAT(created_at, '%d/%m/%Y %H:%i') AS ngay_vn FROM orders;
-- 101 | 31/01/2026 09:15
-- 102 | 14/02/2026 20:30
-- 103 | 28/02/2026 23:59
-- 104 | 01/03/2026 00:00
-- 105 | 15/03/2026 14:00

SELECT DATE_FORMAT('2026-01-31', '%W, %e %M %Y');      -- Saturday, 31 January 2026
```

⚠️ Phút là `%i`, không phải `%m` (tháng) hay `%M` (tên tháng). Viết `'%H:%m'` thì ra `09:01` cho đơn
101: giờ 9, "phút" là tháng 1. Lỗi này không báo gì, chỉ lặng lẽ in sai. Người quen hàm `date()` của
PHP càng dễ nhầm vì PHP dùng chữ cái không có `%` (`'d/m/Y H:i'`) và ý nghĩa của `M` cũng khác.

`STR_TO_DATE(chuoi, dinh_dang)` làm ngược lại: đọc chuỗi theo mẫu, trả về `DATE`, `TIME` hoặc
`DATETIME`. Hữu ích khi nhập dữ liệu có ngày kiểu Việt Nam:

```sql
SELECT STR_TO_DATE('31/01/2026', '%d/%m/%Y');           -- 2026-01-31
SELECT STR_TO_DATE('31/01/2026 09:15', '%d/%m/%Y %H:%i');   -- 2026-01-31 09:15:00
SELECT STR_TO_DATE('31/01/2026', '%Y-%m-%d');           -- NULL, kèm warning: chuỗi không khớp mẫu
```

Chuỗi không khớp mẫu thì ra NULL kèm warning, không báo lỗi. Khi import, đếm số dòng ra NULL sau
khi chuyển để phát hiện dữ liệu hỏng.

### 6.6 Múi giờ

`NOW()` và `CURTIME()` trả về giờ theo **múi giờ của session**, lưu trong biến `time_zone`. Giá trị
khởi đầu là `'SYSTEM'`, tức theo múi giờ của hệ điều hành chạy MySQL server (biến `system_time_zone`).
Mỗi kết nối có thể đổi múi giờ của riêng mình:

```sql
SELECT @@GLOBAL.time_zone, @@SESSION.time_zone, @@system_time_zone;

SET time_zone = '+07:00';
SELECT NOW(), UTC_TIMESTAMP();      -- NOW() hơn UTC_TIMESTAMP() đúng 7 giờ
```

Múi giờ viết được theo ba cách: `'SYSTEM'`; độ lệch so với UTC như `'+07:00'` (trong khoảng
`'-13:59'` tới `'+14:00'`); hoặc tên múi giờ như `'Asia/Ho_Chi_Minh'`, `'UTC'`. Lưu ý quan trọng từ
chương 03: `time_zone` ảnh hưởng tới cột `TIMESTAMP` (đổi sang UTC khi lưu, đổi ngược khi đọc), còn
cột `DATE`, `TIME`, `DATETIME` thì không bị đổi gì.

`CONVERT_TZ(dt, tu_mui, sang_mui)` đổi một giá trị ngày giờ từ múi giờ này sang múi giờ khác:

```sql
SELECT CONVERT_TZ('2026-01-31 09:15:00', '+00:00', '+07:00');             -- 2026-01-31 16:15:00
SELECT CONVERT_TZ('2026-01-31 09:15:00', 'UTC', 'Asia/Ho_Chi_Minh');       -- 2026-01-31 16:15:00
SELECT CONVERT_TZ('2026-01-31 09:15:00', 'UTC', 'Asia/Khong_Ton_Tai');     -- NULL
```

⚠️ Tên múi giờ (như `'Asia/Ho_Chi_Minh'`, kể cả `'UTC'`) chỉ dùng được khi các bảng múi giờ trong
database `mysql` đã được nạp dữ liệu. Theo tài liệu MySQL, quá trình cài đặt tạo các bảng này nhưng
**không** nạp dữ liệu; phải chạy công cụ `mysql_tzinfo_to_sql`. Image Docker chính thức `mysql:8.4`
tự nạp sẵn khi khởi tạo (trừ khi đặt biến môi trường `MYSQL_INITDB_SKIP_TZINFO`), nên ví dụ trên chạy
được. Trên server chưa nạp, `CONVERT_TZ` với tên múi giờ lặng lẽ trả về NULL, còn
`SET time_zone = 'UTC'` báo `ERROR 1298 (HY000): Unknown or incorrect time zone: 'UTC'`. Kiểm tra
nhanh bằng `SELECT COUNT(*) FROM mysql.time_zone_name;` (ra 0 là chưa nạp).

Dùng độ lệch cố định như `'+07:00'` thì không cần bảng, nhưng độ lệch không biết gì về giờ mùa hè
(*daylight saving time*). Việt Nam không dùng giờ mùa hè nên `'+07:00'` an toàn; khách ở châu Âu hay
Mỹ thì phải dùng tên múi giờ. Cách làm phổ biến và ít bug nhất: lưu mọi thời điểm theo UTC, chỉ đổi
sang múi giờ của người xem lúc hiển thị (thường ở tầng ứng dụng).

### 6.7 Lọc theo khoảng thời gian cho đúng

Bài toán: lấy các đơn trong tháng 2/2026. Ba cách viết:

```sql
-- 1. Bọc hàm quanh cột: đúng, nhưng không dùng được index trên created_at
SELECT id FROM orders WHERE YEAR(created_at) = 2026 AND MONTH(created_at) = 2;
-- 102, 103

-- 2. BETWEEN với ngày: SAI
SELECT id FROM orders WHERE created_at BETWEEN '2026-02-01' AND '2026-02-28';
-- 102           <- mất đơn 103 lúc 2026-02-28 23:59:59

-- 3. Khoảng nửa mở [đầu, cuối): đúng, và dùng được index
SELECT id FROM orders WHERE created_at >= '2026-02-01' AND created_at < '2026-03-01';
-- 102, 103
```

Vì sao cách 2 sai: khi so sánh cột `DATETIME` với một hằng, MySQL đổi hằng sang ngày giờ, nên
`'2026-02-28'` thành `'2026-02-28 00:00:00'`; mọi thời điểm sau nửa đêm ngày 28 bị loại. Vá bằng
`'2026-02-28 23:59:59'` cũng không chắc chắn, vì cột có phần lẻ của giây (`DATETIME(6)`) vẫn có giá
trị như `23:59:59.5`. Khoảng nửa mở "lớn hơn hoặc bằng đầu kỳ, nhỏ hơn đầu kỳ sau" luôn đúng, không
phụ thuộc độ chính xác của cột, và không cần biết tháng có bao nhiêu ngày.

Cách 1 cho kết quả đúng nhưng chậm trên bảng lớn: MySQL phải tính `YEAR()`, `MONTH()` cho từng dòng
thay vì nhảy thẳng tới đoạn cần đọc trong index. Quy tắc "đừng bọc hàm quanh cột trong `WHERE`" sẽ
được giải thích kỹ ở chương 11 và chương 12.

## 7. Biểu thức điều kiện: CASE, IF, IFNULL, COALESCE, NULLIF

Đôi khi giá trị cần tính phụ thuộc điều kiện: đơn lớn hay nhỏ, trạng thái hiển thị bằng chữ gì, NULL
thì thay bằng gì. SQL cho phép viết logic rẽ nhánh ngay trong biểu thức, giống toán tử ba ngôi
`?:` hay biểu thức `match` của PHP.

### 7.1 CASE: rẽ nhánh trong một biểu thức

`CASE` có hai dạng. Dạng *tìm kiếm* (searched CASE), linh hoạt nhất, mỗi nhánh là một điều kiện bất
kỳ:

```sql
CASE
  WHEN dieu_kien_1 THEN ket_qua_1
  WHEN dieu_kien_2 THEN ket_qua_2
  ELSE ket_qua_mac_dinh
END
```

Dạng *đơn giản* (simple CASE) so một biểu thức với từng giá trị bằng phép `=`:

```sql
CASE bieu_thuc
  WHEN gia_tri_1 THEN ket_qua_1
  WHEN gia_tri_2 THEN ket_qua_2
  ELSE ket_qua_mac_dinh
END
```

Quy tắc chung của cả hai dạng:

- Các nhánh được xét **từ trên xuống**, nhánh đầu tiên đúng thắng, các nhánh sau bị bỏ qua.
- Không nhánh nào đúng thì lấy `ELSE`; **không có `ELSE` thì ra NULL**.
- Kết quả của mọi nhánh nên cùng loại. Kiểu của cả biểu thức là kiểu "gộp" của mọi nhánh; trộn số với
  chuỗi thì kết quả là chuỗi.
- `CASE` là chuẩn SQL, chạy được ở mọi database lớn. (Đừng nhầm với *câu lệnh* `CASE ... END CASE`
  dùng trong stored procedure, chương 17; đó là thứ khác.)

**Phân loại theo khoảng giá trị.** Thứ tự nhánh quan trọng khi các khoảng chồng lên nhau:

```sql
SELECT id, total,
       CASE
         WHEN total >= 500000 THEN 'lớn'
         WHEN total >= 100000 THEN 'vừa'
         ELSE 'nhỏ'
       END AS nhom
FROM orders;
-- 101 | 250000.00 | vừa
-- 102 | 120000.00 | vừa
-- 103 | 990000.00 | lớn
-- 104 |  75500.00 | nhỏ
-- 105 |  50000.00 | nhỏ
```

Đảo hai nhánh `WHEN` đầu thì đơn 103 thành "vừa", vì `990000 >= 100000` đúng trước.

**Dịch mã sang chữ** bằng dạng đơn giản:

```sql
SELECT id, status,
       CASE status
         WHEN 'paid'      THEN 'Đã thanh toán'
         WHEN 'pending'   THEN 'Chờ thanh toán'
         WHEN 'cancelled' THEN 'Đã huỷ'
         ELSE 'Không rõ'
       END AS trang_thai
FROM orders;
-- 101 | paid      | Đã thanh toán
-- 102 | cancelled | Đã huỷ
-- 103 | paid      | Đã thanh toán
-- 104 | NULL      | Không rõ
-- 105 | pending   | Chờ thanh toán
```

⚠️ Dạng đơn giản **không bắt được NULL**. `CASE status WHEN NULL THEN ...` so sánh `status = NULL`,
luôn ra UNKNOWN (mục 3.4), nên nhánh đó không bao giờ được chọn. Muốn xử lý NULL phải dùng dạng tìm
kiếm với `IS NULL`:

```sql
SELECT id, CASE status WHEN NULL THEN 'chưa có' ELSE status END AS x
FROM orders WHERE id = 104;
-- 104 | NULL          <- nhánh WHEN NULL bị bỏ qua, rơi xuống ELSE status, mà status là NULL

SELECT id, CASE WHEN status IS NULL THEN 'chưa có' ELSE status END AS x
FROM orders WHERE id = 104;
-- 104 | chưa có
```

**Sắp xếp theo thứ tự tự định nghĩa.** `CASE` dùng được ở mọi chỗ đặt được biểu thức, kể cả
`ORDER BY`. Ví dụ muốn đơn chờ thanh toán lên đầu, rồi tới đơn đã trả, còn lại xuống cuối:

```sql
SELECT id, status FROM orders
ORDER BY CASE status
           WHEN 'pending' THEN 1
           WHEN 'paid'    THEN 2
           ELSE 3
         END,
         id;
-- 105 | pending
-- 101 | paid
-- 103 | paid
-- 102 | cancelled
-- 104 | NULL
```

**Đếm và cộng có điều kiện.** Kết hợp `CASE` với hàm tổng hợp (chương 08 học kỹ) để tính nhiều chỉ
số trong một lần quét bảng:

```sql
SELECT COUNT(*)                                             AS tong_don,
       COUNT(CASE WHEN status = 'paid' THEN 1 END)          AS so_don_paid,
       SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END) AS doanh_thu_paid
FROM orders;
-- 5 | 2 | 1240000.00
```

`COUNT(CASE WHEN ... THEN 1 END)` tận dụng hai quy tắc đã học: `CASE` không có `ELSE` ra NULL với
dòng không khớp, và `COUNT(bieu_thuc)` bỏ qua NULL. Mẹo `SUM(status = 'paid')` ở mục 2.2 cho cùng kết
quả nhưng chỉ chạy được ở MySQL; cách viết bằng `CASE` chạy được ở mọi nơi.

### 7.2 IF: rẽ hai nhánh, kiểu MySQL

`IF(dk, a, b)` trả về `a` nếu `dk` là TRUE (theo tài liệu: `dk <> 0` và `dk IS NOT NULL`), ngược lại
trả về `b`. Nó là cách viết gọn của `CASE WHEN dk THEN a ELSE b END`.

```sql
SELECT IF(1 > 2, 2, 3), IF(1 < 2, 'yes', 'no'), IF(NULL, 'đúng', 'sai');
-- 3 | yes | sai

SELECT id, IF(status = 'cancelled', 'huỷ', 'không huỷ') AS x FROM orders WHERE id IN (102, 104);
-- 102 | huỷ
-- 104 | không huỷ       <- điều kiện là UNKNOWN, không phải TRUE, nên rơi vào nhánh "sai"
```

Để ý dòng 104: `IF` (và `CASE`) xếp UNKNOWN vào nhánh "không đúng". Đó có thể là điều bạn muốn, hoặc
không; hãy quyết định có chủ ý bằng cách xử lý NULL tường minh khi cột có thể NULL.

`IF()` là hàm riêng của MySQL; PostgreSQL không có hàm này, nên code cần chạy trên nhiều database thì
viết `CASE`. Cũng đừng nhầm hàm `IF()` với câu lệnh `IF ... END IF` trong stored procedure.

### 7.3 IFNULL và COALESCE: thay NULL bằng giá trị khác

- `IFNULL(a, b)`: trả về `a` nếu `a` khác NULL, ngược lại trả về `b`. Đúng hai tham số, riêng của
  MySQL.
- `COALESCE(a, b, c, ...)`: trả về tham số **đầu tiên khác NULL**, hoặc NULL nếu tất cả đều NULL.
  Nhận bao nhiêu tham số cũng được, là chuẩn SQL.

```sql
SELECT IFNULL(NULL, 10), IFNULL(1, 0), IFNULL(1/0, 'yes');    -- 10 | 1 | yes   (ví dụ trong tài liệu MySQL)
SELECT COALESCE(NULL, NULL, 'c', 'd'), COALESCE(NULL, NULL);  -- c | NULL
```

Ứng dụng thường gặp nhất là đặt giá trị mặc định trước khi tính, như `total - COALESCE(discount, 0)`
ở mục 3.2, hay chọn thông tin liên hệ đầu tiên có được:

```sql
SELECT id, COALESCE(email, phone, 'không có liên hệ') AS lien_he FROM customers;
-- 1 | an@example.com
-- 2 | 0987654321
-- 3 | CHI@Example.COM
-- 4 |                       <- email là '' (không phải NULL) nên được chọn
```

⚠️ `COALESCE` và `IFNULL` chỉ thay **NULL**. Chuỗi rỗng `''`, số 0 là giá trị thật nên được giữ
nguyên. Khách 4 nhận về một liên hệ rỗng. Cách sửa là kết hợp với `NULLIF` ở mục sau.

Nên chọn `COALESCE`: làm được mọi việc của `IFNULL`, nhận nhiều tham số, và chạy được ở PostgreSQL.
Toán tử `??` của PHP có cùng ý tưởng: `$a ?? $b ?? 'mặc định'`.

### 7.4 NULLIF: biến một giá trị thành NULL

`NULLIF(a, b)` trả về NULL nếu `a = b`, ngược lại trả về `a`. Theo tài liệu MySQL, nó tương đương
`CASE WHEN a = b THEN NULL ELSE a END`, và kết quả có cùng kiểu với `a`.

```sql
SELECT NULLIF(1, 1), NULLIF(1, 2);     -- NULL | 1
```

Nghe thì lạ (ai lại muốn tạo ra NULL?), nhưng nó giải quyết gọn hai bài toán rất phổ biến.

**Bài toán 1: chia cho 0 một cách có chủ ý.**

```sql
SELECT 100 / NULLIF(0, 0), 100 / NULLIF(4, 0);    -- NULL | 25.0000
```

Mẫu `tu_so / NULLIF(mau_so, 0)` biến "chia cho 0" thành "chia cho NULL", ra NULL mà không có warning
1365, và cũng không làm câu `INSERT`/`UPDATE` lỗi trong strict mode. Muốn hiển thị 0 thay cho NULL thì
bọc thêm `COALESCE(tu_so / NULLIF(mau_so, 0), 0)`. Đây cũng là cách viết chuẩn trên PostgreSQL, nơi
chia cho 0 ném lỗi chứ không ra NULL.

**Bài toán 2: coi chuỗi rỗng như NULL.**

```sql
SELECT COUNT(email), COUNT(NULLIF(email, '')) FROM customers;
-- 3 | 2           <- COUNT(email) đếm cả chuỗi rỗng của khách 4

SELECT id, COALESCE(NULLIF(email, ''), phone, 'không có liên hệ') AS lien_he FROM customers;
-- 1 | an@example.com
-- 2 | 0987654321
-- 3 | CHI@Example.COM
-- 4 | 912345678
```

Với dữ liệu có thể chứa toàn dấu cách, dùng `NULLIF(TRIM(email), '')`.

Tài liệu MySQL còn lưu ý: khi hai tham số khác nhau, `a` bị tính **hai lần**. Với cột hay hằng thì
không sao, nhưng nếu `a` là một subquery nặng hoặc hàm cho kết quả khác nhau mỗi lần gọi (như
`RAND()`), hãy cân nhắc.

### 7.5 Chọn hàm nào

| Nhu cầu | MySQL | Chuẩn SQL (chạy cả ở PostgreSQL) | PHP tương tự |
|---|---|---|---|
| Rẽ nhiều nhánh | `CASE WHEN ... END` | `CASE WHEN ... END` | `match (true) { ... }` |
| Rẽ hai nhánh | `IF(dk, a, b)` | `CASE WHEN dk THEN a ELSE b END` | `$dk ? $a : $b` |
| NULL thì lấy giá trị khác | `IFNULL(a, b)`, `COALESCE(a, b, ...)` | `COALESCE(a, b, ...)` | `$a ?? $b` |
| Giá trị này thì coi như NULL | `NULLIF(a, b)` | `NULLIF(a, b)` | (không có toán tử riêng) |

Ưu tiên các dạng chuẩn (`CASE`, `COALESCE`, `NULLIF`): đọc được ở mọi database, và người đọc code
không cần biết hàm riêng của MySQL.

## 8. Chuyển kiểu: CAST, CONVERT và ép kiểu ngầm

Khi một phép toán gặp hai giá trị khác kiểu (chuỗi với số, chuỗi với ngày), MySQL phải đổi chúng về
cùng một kiểu rồi mới tính. Bạn có thể tự đổi một cách *tường minh* (explicit) bằng `CAST`, hoặc để
MySQL tự đổi *ngầm* (implicit). Phần lớn bug khó thấy nằm ở cách thứ hai.

### 8.1 Chuyển kiểu tường minh: CAST và CONVERT

`CAST(bieu_thuc AS kieu)` đổi giá trị sang kiểu chỉ định. `CONVERT(bieu_thuc, kieu)` làm y hệt (cú
pháp ODBC). Các kiểu đích hay dùng:

| Kiểu đích | Kết quả |
|---|---|
| `SIGNED` (hoặc `SIGNED INTEGER`) | Số nguyên có dấu `BIGINT` |
| `UNSIGNED` (hoặc `UNSIGNED INTEGER`) | Số nguyên không dấu `BIGINT UNSIGNED` |
| `DECIMAL(M, D)` | Số thập phân chính xác |
| `DOUBLE` | Số thực xấp xỉ |
| `CHAR` hoặc `CHAR(N)` | Chuỗi |
| `DATE`, `DATETIME`, `TIME` | Ngày, ngày giờ, giờ |
| `JSON` | Giá trị JSON |

⚠️ Không có `CAST(x AS INT)` trong MySQL: tài liệu chỉ liệt kê `SIGNED` và `UNSIGNED` cho số nguyên,
nên viết `INT` là lỗi cú pháp. Người quen PostgreSQL (nơi `CAST(x AS integer)` và `x::int` là chuyện
thường) rất hay vấp chỗ này.

```sql
SELECT CAST('42' AS SIGNED), CAST(42 AS CHAR), CAST('2026-01-31' AS DATE);
-- 42 | '42' | 2026-01-31

SELECT CAST(1 - 2 AS UNSIGNED);                    -- 18446744073709551615 (ví dụ trong tài liệu MySQL)
SELECT CAST('12abc' AS SIGNED), CAST('abc' AS SIGNED);
-- 12 | 0           (kèm warning 1292: Truncated incorrect INTEGER value)
SELECT CAST(3.7 AS SIGNED), CAST('3.7' AS SIGNED);
-- 4 | 3            (số DECIMAL được làm tròn; chuỗi thì chỉ đọc phần số nguyên ở đầu, kèm warning)
```

Ba điều rút ra:

- `CAST` trong MySQL "dễ dãi": chuỗi không phải số vẫn ra một con số (lấy phần số ở đầu, không có thì
  ra 0), chỉ kèm warning. Nó không phải công cụ kiểm tra dữ liệu hợp lệ.
- Số âm đổi sang `UNSIGNED` không báo lỗi mà "quay vòng" thành số rất lớn.
- Cùng là 3.7, dạng số và dạng chuỗi cho hai kết quả khác nhau. Muốn chắc chắn thì làm tròn tường
  minh bằng `ROUND`/`TRUNCATE`/`FLOOR` trước khi `CAST`.

`CONVERT(bieu_thuc USING charset)` là dạng thứ hai, dùng để đổi **bảng mã** của chuỗi, ví dụ
`CONVERT(cot_latin1 USING utf8mb4)` khi chuyển dữ liệu cũ sang `utf8mb4` (chương 03).

### 8.2 Ép kiểu ngầm khi tính toán

Khi phép toán số học gặp chuỗi, MySQL đổi chuỗi sang số, và phép tính được thực hiện bằng số thực
`DOUBLE` (số xấp xỉ, mục 5.1). Khi hàm chuỗi như `CONCAT` gặp số, số được đổi sang chuỗi:

```sql
SELECT 1 + '1', '10' * '2', CONCAT(2, ' test');     -- 2 | 20 | '2 test'
SELECT '12abc' + 1, 'abc' + 1;                      -- 13 | 1   (kèm warning 1292)
```

Quy tắc đổi chuỗi sang số: đọc phần trông giống số ở đầu chuỗi (bỏ qua dấu cách ở đầu), dừng ở ký tự
đầu tiên không hợp lệ; không đọc được gì thì là 0. MySQL ghi warning nhưng vẫn trả kết quả.

### 8.3 Ép kiểu ngầm khi so sánh

Đây là chỗ nguy hiểm nhất. Tài liệu MySQL 8.4 nêu các quy tắc cho phép so sánh hai giá trị khác kiểu
(tóm tắt):

1. Một vế là NULL thì kết quả NULL (trừ `<=>`).
2. Hai vế đều là chuỗi: so sánh như chuỗi (theo collation).
3. Hai vế đều là số nguyên: so sánh như số nguyên.
4. Một vế là cột `DATETIME`/`TIMESTAMP`, vế kia là hằng: hằng được đổi sang ngày giờ (đó là lý do
   `BETWEEN '2026-02-01' AND '2026-02-28'` ở mục 6.7 hiểu `'2026-02-28'` là nửa đêm).
5. Một vế là `DECIMAL`: so sánh như `DECIMAL` nếu vế kia là số nguyên hoặc `DECIMAL`, như số thực nếu
   vế kia là số thực.
6. **Mọi trường hợp còn lại, kể cả chuỗi so với số: cả hai được đổi sang số thực `DOUBLE` rồi so
   sánh.**

Quy tắc 6 sinh ra các kết quả kỳ quặc sau (ví dụ trong tài liệu MySQL):

```sql
SELECT 1 > '6x', 7 > '6x', 0 > 'x6', 0 = 'x6';      -- 0 | 1 | 0 | 1
SELECT 'a' IN (0), 0 IN ('b');                      -- 1 | 1
```

`'x6'` không bắt đầu bằng chữ số nên thành 0, và `0 = 'x6'` là **đúng**. Áp vào bảng thật thì:

**Bẫy 1: so cột chuỗi với số 0 khớp gần như mọi dòng.**

```sql
SELECT id FROM customers WHERE full_name = 0;
-- 1, 2, 3, 4      (kèm warning)
```

Mọi tên đều không bắt đầu bằng chữ số, nên đều thành 0. Tài liệu MySQL nhấn mạnh hiện tượng này xảy
ra **kể cả khi bật strict mode** (strict mode chỉ chặn dữ liệu sai khi ghi, mục 8.4). Viết hằng đúng
kiểu của cột: `WHERE full_name = '0'` thì so sánh chuỗi và không khớp dòng nào.

**Bẫy 2: số điện thoại lưu dạng chuỗi nhưng tìm bằng số.**

```sql
SELECT id, phone FROM customers WHERE phone = 912345678;
-- 1 | 0912345678
-- 4 | 912345678
```

Cả `'0912345678'` và `'912345678'` đều thành số 912345678, nên khớp cả hai, trong khi về mặt dữ liệu
đây là hai chuỗi khác nhau. Tệ hơn, theo tài liệu MySQL, khi so cột chuỗi với số thì MySQL **không
dùng được index** trên cột để tìm nhanh, vì có quá nhiều chuỗi khác nhau cùng đổi ra một số (`'1'`,
`' 1'`, `'1a'` đều ra 1). Trên bảng triệu dòng, câu này thành quét toàn bảng (chương 11, 12). Chiều
ngược lại (cột số so với chuỗi hằng như `WHERE id = '101'`) thì ít hại hơn: chỉ hằng bị đổi một lần.

**Bẫy 3: số nguyên lớn so qua `DOUBLE` bị mất chính xác.** `DOUBLE` không biểu diễn đúng mọi số
nguyên 64 bit, nên hai số khác nhau có thể bị coi là bằng nhau (ví dụ trong tài liệu MySQL):

```sql
SELECT '9223372036854775807' = 9223372036854775807;   -- 1
SELECT '9223372036854775807' = 9223372036854775806;   -- 1   <- hai số khác nhau mà vẫn "bằng"
SELECT CAST('9223372036854775807' AS UNSIGNED) = 9223372036854775806;   -- 0
```

Hay gặp với ID lớn (ID kiểu Snowflake, ID từ hệ thống ngoài) lưu ở cột chuỗi rồi so với số. Cách tránh
là `CAST` tường minh như dòng cuối, hoặc tốt hơn: lưu và so sánh đúng kiểu.

**Bẫy 4: `IN` trộn chuỗi với số.** Tài liệu MySQL khuyên không bao giờ trộn giá trị có nháy và không
nháy trong một danh sách `IN`, vì quy tắc so sánh hai loại khác nhau. Viết `IN ('1', '2', 'a')` chứ
đừng viết `IN (1, 2, 'a')`.

### 8.4 Ép kiểu khi ghi dữ liệu: strict mode

Khi `INSERT`/`UPDATE` đưa một giá trị sai kiểu vào cột, strict mode (mặc định trong MySQL 8.4,
chương 03) biến chuyện "lặng lẽ sửa giá trị kèm warning" thành **lỗi**:

```sql
INSERT INTO orders (id, customer_id, total, created_at) VALUES (106, 'abc', 1000, NOW());
-- ERROR 1366 (HY000): Incorrect integer value: 'abc' for column 'customer_id' at row 1
```

Không bật strict mode thì câu trên chèn `customer_id = 0` kèm warning. Nhưng nhớ: strict mode chỉ áp
cho câu ghi dữ liệu. Với `SELECT`, tài liệu MySQL ghi rõ giá trị không hợp lệ chỉ sinh warning, nên
các bẫy ở mục 8.3 vẫn còn nguyên.

Một dạng ép kiểu khác là giữa chuỗi khác charset hoặc collation. Khi MySQL không tự chọn được
collation chung (ví dụ so sánh hay `JOIN` hai cột khai báo collation khác nhau), câu lệnh lỗi
`ERROR 1267: Illegal mix of collations (...) and (...) for operation '='`; còn khi tự chọn được, nó
phải đổi giá trị của từng dòng và có thể không dùng được index. Khai báo charset, collation thống nhất
cho cả database là cách phòng bệnh (chương 03).

### 8.5 Đối chiếu PHP: PHP 8 đã sửa đúng cái bẫy mà MySQL vẫn giữ

PHP 7 từng có quy tắc giống MySQL: so số với chuỗi không phải số thì đổi chuỗi sang số, nên
`0 == 'abc'` là `true`. PHP 8.0 đổi lại: nếu chuỗi không phải chuỗi số, PHP so sánh như chuỗi (đổi số
thành chuỗi).

```php
<?php
declare(strict_types=1);

var_dump(0 == 'abc');    // PHP 8: bool(false); PHP 7.4: bool(true)
var_dump('1' == '01');   // bool(true) ở cả hai: hai chuỗi số được so như số
var_dump(1 == '1abc');   // PHP 8: bool(false); PHP 7.4: bool(true)
```

MySQL 8.4 vẫn theo quy tắc cũ: `SELECT 0 = 'abc'` ra 1. Đừng mang trực giác PHP 8 vào SQL. Ở cả hai
phía, cách an toàn là giống nhau: so sánh chặt đúng kiểu (`===` trong PHP; hằng cùng kiểu với cột
trong SQL), và bind tham số với kiểu đúng khi dùng prepared statement (chương 19).

## 9. Đối chiếu PostgreSQL

Các khái niệm trong chương (biểu thức, logic ba giá trị, `CASE`, `COALESCE`, `NULLIF`) là chuẩn SQL
nên PostgreSQL giống MySQL. Khác biệt nằm ở chi tiết, và chính chi tiết làm code chuyển database bị
sai. Chương 25 đối chiếu toàn diện; dưới đây là phần liên quan tới chương này (theo tài liệu
PostgreSQL 18).

| Chủ đề | MySQL 8.4 | PostgreSQL |
|---|---|---|
| Chia hai số nguyên | `5 / 2` ra `2.5000` | `5 / 2` ra `2` (bỏ phần lẻ về phía 0) |
| Chia cho 0 | NULL kèm warning (`SELECT`) | Báo lỗi |
| Nối chuỗi | `CONCAT(a, b)`; `\|\|` là `OR` | `a \|\| b` là nối chuỗi |
| `CONCAT` gặp NULL | Cả kết quả là NULL | Bỏ qua tham số NULL |
| `LENGTH(s)` | Số **byte** | Số **ký tự**; số byte dùng `octet_length(s)` |
| Kiểu boolean | Không có riêng, là 1/0 | Có kiểu `boolean` thật; `SUM(boolean)` không tồn tại |
| Đếm có điều kiện | `SUM(dk)` hoặc `COUNT(CASE ...)` | `COUNT(CASE ...)` hoặc `COUNT(*) FILTER (WHERE dk)` |
| So sánh an toàn NULL | `a <=> b` | `a IS NOT DISTINCT FROM b` |
| `IF()`, `IFNULL()` | Có | Không có; dùng `CASE`, `COALESCE` |
| `GREATEST`/`LEAST` gặp NULL | Ra NULL | Bỏ qua NULL, chỉ ra NULL khi mọi tham số NULL |
| NULL khi `ORDER BY ... ASC` | Đứng đầu | Đứng cuối (NULL được coi lớn hơn mọi giá trị) |
| Chọn vị trí NULL khi sắp xếp | Không có cú pháp riêng | `NULLS FIRST` / `NULLS LAST` |
| Ép chuỗi sang số khi so sánh | Tự ép, `0 = 'abc'` đúng | Chặt hơn nhiều; so cột `text` với số thường báo lỗi kiểu |
| `CAST` sang số nguyên | `CAST(x AS SIGNED)` | `CAST(x AS integer)` hoặc `x::integer`; chuỗi không phải số thì báo lỗi |
| `ROUND` số chính xác | Nửa ra xa số 0 | Giống (với `numeric`); với `double precision` tuỳ nền tảng, thường là về số chẵn |
| Cộng tháng vào cuối tháng | Lùi về ngày cuối tháng | Giống: 31/3 cộng 1 tháng ra 30/4 |

Hai bài học từ bảng:

- Code dùng hàm chuẩn (`CASE`, `COALESCE`, `NULLIF`, `CAST`) dễ chuyển database hơn code dùng
  `IF`, `IFNULL`, `<=>`, mẹo `SUM(dk)`.
- PostgreSQL chọn "báo lỗi sớm" ở nhiều chỗ MySQL chọn "trả kết quả kèm warning" (chia cho 0, chuỗi
  không phải số, so sánh khác kiểu). Khi làm với MySQL, bạn phải tự đọc warning và tự kiểm tra dữ
  liệu, vì database sẽ không dừng bạn lại.

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| `WHERE cot = NULL` | So sánh với NULL luôn ra UNKNOWN, không dòng nào khớp, không báo lỗi | `IS NULL`, `IS NOT NULL`, hoặc `<=>` |
| `WHERE status <> 'x'` rồi tưởng đã lấy "mọi dòng trừ x" | Dòng `status` NULL cho UNKNOWN và bị loại | Thêm `OR status IS NULL`, hoặc `NOT (status <=> 'x')`; tốt hơn là cột `NOT NULL` |
| `NOT IN (subquery)` khi subquery có thể trả NULL | Danh sách có NULL thì `NOT IN` không bao giờ đúng, kết quả rỗng | `NOT EXISTS`, hoặc lọc `IS NOT NULL` trong subquery |
| `total - discount` khi `discount` có thể NULL | NULL lan truyền qua phép tính | `total - COALESCE(discount, 0)` |
| `CONCAT(a, b)` với cột có thể NULL | Một tham số NULL làm cả chuỗi NULL | `CONCAT_WS`, hoặc bọc `COALESCE` |
| `AVG(cot)` tưởng chia cho số dòng | `AVG` bỏ qua NULL, chia cho số giá trị khác NULL | Chọn có chủ ý: `AVG(cot)` hay `AVG(COALESCE(cot, 0))` |
| `SUM` trả về NULL khi không có dòng | Hàm tổng hợp trên tập rỗng (trừ `COUNT`) ra NULL | `COALESCE(SUM(x), 0)` |
| Trộn `AND` với `OR` không ngoặc | `AND` ưu tiên hơn `OR` | Luôn đặt ngoặc |
| `WHERE status = 'a' OR 'b'` | `'b'` đứng một mình bị đổi thành số 0 (sai) | `status IN ('a', 'b')` |
| Dùng `\|\|` hay `+` để nối chuỗi | Trong MySQL `\|\|` là `OR`, `+` là cộng số | `CONCAT` |
| `LENGTH` để đếm ký tự tiếng Việt | `LENGTH` đếm byte | `CHAR_LENGTH` |
| `SUBSTRING(s, 0, n)` | Vị trí bắt đầu từ 1; `pos` = 0 ra chuỗi rỗng | `SUBSTRING(s, 1, n)` hoặc `LEFT(s, n)` |
| Tin `TRIM` bỏ cả tab, xuống dòng | `TRIM` mặc định chỉ bỏ dấu cách | `REGEXP_REPLACE` với `[[:space:]]`, hoặc làm sạch ở ứng dụng |
| `LPAD` với chuỗi dài hơn độ dài đích | Chuỗi bị cắt mà không báo | Kiểm tra độ dài trước, hoặc chọn độ dài đủ lớn |
| `ROUND` trên cột `DOUBLE` cho tiền | Số xấp xỉ có sai số và quy tắc làm tròn khác | Cột `DECIMAL` |
| Tính toán hay `ORDER BY` trên kết quả `FORMAT` | `FORMAT` trả về chuỗi | Giữ số trong SQL, định dạng ở tầng hiển thị |
| `BETWEEN '2026-02-01' AND '2026-02-28'` trên cột `DATETIME` | Ngày cuối thành nửa đêm, mất dữ liệu ngày cuối | Khoảng nửa mở `>= đầu AND < đầu kỳ sau` |
| `WHERE YEAR(created_at) = 2026` trên bảng lớn | Bọc hàm quanh cột, không dùng được index | Viết thành khoảng thời gian |
| `'%H:%m'` để in giờ phút | `%m` là tháng, phút là `%i` | Tra bảng ký hiệu `DATE_FORMAT` |
| Tính kỳ sau bằng "kỳ trước + 1 tháng" | Qua tháng Hai thì ngày trôi về 28 | Tính từ mốc gốc: `bat_dau + INTERVAL n MONTH` |
| `YEAR(nay) - YEAR(ngay_sinh)` để tính tuổi | Cộng tuổi từ 1/1, không phải từ sinh nhật | `TIMESTAMPDIFF(YEAR, ngay_sinh, nay)` |
| `CONVERT_TZ` với tên múi giờ trên server chưa nạp bảng múi giờ | Lặng lẽ ra NULL | Nạp bảng bằng `mysql_tzinfo_to_sql`, hoặc dùng độ lệch `'+07:00'` |
| So cột chuỗi với số (`WHERE phone = 912345678`) | Cả hai thành `DOUBLE`: khớp sai, không dùng được index | Hằng đúng kiểu với cột: `WHERE phone = '0912345678'` |
| `CAST(x AS INT)` | MySQL không có kiểu đích `INT` | `CAST(x AS SIGNED)` |
| Phớt lờ dòng "N warnings" của client | MySQL trả kết quả sai kèm warning thay vì báo lỗi | `SHOW WARNINGS` sau câu lệnh đáng ngờ |

## Tóm tắt chương

- Biểu thức là công thức MySQL tính ra một giá trị cho từng dòng; dùng được ở `SELECT`, `WHERE`,
  `ORDER BY`, `UPDATE ... SET`... Alias không dùng được trong `WHERE`.
- `/` luôn ra số thập phân, chia cho 0 ra NULL (kèm warning, còn câu ghi dữ liệu thì lỗi trong strict
  mode). `AND` ưu tiên hơn `OR`: luôn đặt ngoặc. `||` là `OR`, nối chuỗi dùng `CONCAT`.
- NULL là "không có giá trị". Biểu thức có NULL thường ra NULL; so sánh với NULL ra UNKNOWN;
  `WHERE` chỉ giữ TRUE. Dùng `IS NULL`, `<=>`; cẩn thận `<>` và `NOT IN` với cột có thể NULL.
- Hàm tổng hợp bỏ qua NULL (trừ `COUNT(*)`), và ra NULL trên tập rỗng (trừ `COUNT`).
- Hàm chuỗi: vị trí từ 1; `CHAR_LENGTH` đếm ký tự, `LENGTH` đếm byte; `CONCAT` gặp NULL ra NULL,
  `CONCAT_WS` bỏ qua NULL; `TRIM` chỉ bỏ dấu cách; `REPLACE` phân biệt hoa thường.
- Số chính xác (`DECIMAL`, số nguyên) và số xấp xỉ (`DOUBLE`) làm tròn khác nhau; tiền luôn dùng
  `DECIMAL`, và quyết định làm tròn ở bước nào một cách nhất quán.
- Ngày giờ: `NOW()` cố định trong một câu lệnh; cộng tháng vào cuối tháng thì lùi về ngày cuối tháng;
  `DATEDIFF` chỉ nhìn phần ngày; lọc theo khoảng nửa mở; múi giờ theo session, tên múi giờ cần bảng
  múi giờ.
- `CASE` (chuẩn) cho mọi logic rẽ nhánh; `COALESCE` thay NULL; `NULLIF` biến giá trị thành NULL (chia
  cho 0, chuỗi rỗng). Dạng `CASE x WHEN NULL` không bao giờ khớp.
- MySQL tự ép kiểu ngầm và chỉ báo warning: chuỗi so với số thì cả hai thành `DOUBLE`, nên
  `'abc' = 0` đúng và index trên cột chuỗi không dùng được. Luôn viết hằng đúng kiểu, dùng `CAST`
  (`SIGNED`, không phải `INT`) khi cần đổi kiểu.

## Câu hỏi tự kiểm tra

1. Vì sao `SELECT id, total - discount AS x FROM orders WHERE x > 0` lỗi, còn `ORDER BY x` thì không?
   (mục 1.3)
2. `SELECT 7 / 2, 7 DIV 2, -7 % 3, 2 ^ 3` cho ra gì trong MySQL? Trong PostgreSQL, `7 / 2` ra gì?
   (mục 2.1, 2.4, 9)
3. Tính tay `NULL AND 0`, `NULL OR 1`, `NOT NULL`, `NULL = NULL`, `NULL <=> NULL`, `3 NOT IN (1,
   NULL)`. (mục 3.3 tới 3.6)
4. Bảng có 100 đơn, 10 đơn có `status` NULL, 20 đơn `status = 'cancelled'`. `WHERE status <>
   'cancelled'` trả về bao nhiêu dòng? Viết lại để ra 80. (mục 3.5)
5. `COUNT(*)`, `COUNT(discount)`, `AVG(discount)` khác nhau thế nào khi cột có NULL? Khi nào nên dùng
   `AVG(COALESCE(discount, 0))`? (mục 3.7)
6. Tên "Trần Thị Bình" có `LENGTH` và `CHAR_LENGTH` khác nhau vì sao? Hàm PHP nào tương ứng với mỗi
   hàm? (mục 4.2)
7. Vì sao `ROUND(2.5)` và `ROUND(2.5E0)` có thể ra hai kết quả khác nhau? (mục 5.1, 5.2)
8. Vì sao lọc tháng 2 bằng `BETWEEN '2026-02-01' AND '2026-02-28'` trên cột `DATETIME` là sai, và vì
   sao `WHERE MONTH(created_at) = 2` tuy đúng nhưng chậm? (mục 6.7)
9. `CASE status WHEN NULL THEN 'x' END` có bao giờ ra `'x'` không? Vì sao? (mục 7.1)
10. Vì sao `WHERE phone = 912345678` trên cột `VARCHAR` vừa có thể trả sai dòng vừa chậm? Strict mode
    có ngăn được không? (mục 8.3, 8.4)

## Bài tập

Dùng database `ch06` và dữ liệu mẫu ở đầu chương. Tự tính kết quả mong đợi bằng tay trước khi chạy.

1. **Báo cáo đơn hàng.** Viết một câu `SELECT` trên `orders` trả về: mã đơn dạng `DH000101`, ngày tạo
   dạng `31/01/2026 09:15`, số tiền phải trả (`total` trừ giảm giá, NULL coi là 0) làm tròn tới hàng
   nghìn, nhãn trạng thái tiếng Việt (NULL hiển thị là "Chưa rõ"), và cột "nhóm" theo số tiền phải
   trả. Sắp xếp: đơn chờ thanh toán lên đầu, trong cùng nhóm thì đơn mới hơn lên trước.
2. **Làm sạch dữ liệu khách hàng.** Viết các câu `SELECT` xem trước, rồi `UPDATE` để: bỏ khoảng trắng
   (kể cả tab, xuống dòng) ở hai đầu tên; chuyển email về chữ thường và đổi email rỗng hoặc toàn dấu
   cách thành NULL; thêm số 0 vào đầu số điện thoại 9 chữ số. Trước mỗi `UPDATE`, ghi lại số dòng bạn
   dự kiến bị đổi và so với số MySQL báo.
3. **Săn bẫy NULL.** Thêm một khách mới chưa có đơn nào và một đơn mới có `customer_id` NULL. Viết ba
   câu tìm "khách chưa có đơn": bằng `NOT IN`, bằng `NOT EXISTS`, bằng `LEFT JOIN ... IS NULL` (xem
   trước chương 07). Giải thích bằng logic ba giá trị vì sao câu `NOT IN` cho kết quả khác, rồi sửa nó.
4. **Ép kiểu ngầm và PHP.** Viết một script PHP dùng PDO kết nối MySQL (container `my84` ở đầu chương), truy vấn bảng có cột chuỗi `code`, so sánh hai cách: bind tham số kiểu chuỗi và nối thẳng
   số nguyên vào câu SQL. Trên MySQL, dùng `EXPLAIN` (chương 12) để xem cách nào dùng được index trên
   `code`. Ghi lại nhận xét: kết quả và kế hoạch thực thi khác nhau ở đâu, và vì sao.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/functions.html) ·
  [Operator Precedence](https://dev.mysql.com/doc/refman/8.4/en/operator-precedence.html) ·
  [Type Conversion in Expression Evaluation](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html) ·
  [Comparison Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/comparison-operators.html) ·
  [Logical Operators](https://dev.mysql.com/doc/refman/8.4/en/logical-operators.html) ·
  [Arithmetic Operators](https://dev.mysql.com/doc/refman/8.4/en/arithmetic-functions.html) ·
  [Mathematical Functions](https://dev.mysql.com/doc/refman/8.4/en/mathematical-functions.html) ·
  [String Functions](https://dev.mysql.com/doc/refman/8.4/en/string-functions.html) ·
  [Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html) ·
  [Temporal Intervals](https://dev.mysql.com/doc/refman/8.4/en/expressions.html#temporal-intervals) ·
  [Flow Control Functions](https://dev.mysql.com/doc/refman/8.4/en/flow-control-functions.html) ·
  [Cast Functions and Operators](https://dev.mysql.com/doc/refman/8.4/en/cast-functions.html) ·
  [Precision Math Examples](https://dev.mysql.com/doc/refman/8.4/en/precision-math-examples.html) ·
  [Working with NULL Values](https://dev.mysql.com/doc/refman/8.4/en/working-with-null.html) ·
  [Problems with NULL Values](https://dev.mysql.com/doc/refman/8.4/en/problems-with-null.html) ·
  [Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html) ·
  [Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) ·
  [Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html)
- PostgreSQL 18:
  [Mathematical Functions](https://www.postgresql.org/docs/18/functions-math.html) ·
  [String Functions](https://www.postgresql.org/docs/18/functions-string.html) ·
  [Conditional Expressions](https://www.postgresql.org/docs/18/functions-conditional.html) ·
  [Comparison Functions and Operators](https://www.postgresql.org/docs/18/functions-comparison.html) ·
  [Sorting Rows](https://www.postgresql.org/docs/18/queries-order.html)
- PHP RFC: [Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison) (PHP 8.0)
- Mã nguồn `Illuminate\Database\Query\Builder::where()` của
  [laravel/framework 13.x](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Query/Builder.php)
- [modern-sql.com: Three-valued logic](https://modern-sql.com/concept/three-valued-logic)
