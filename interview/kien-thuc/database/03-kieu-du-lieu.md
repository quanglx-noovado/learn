# Chương 03. Kiểu dữ liệu

> [← Mục lục](README.md) · [← Chương 02: Mô hình quan hệ và thiết kế dữ liệu](02-mo-hinh-quan-he-thiet-ke.md) · [Chương 04: Tạo và thay đổi bảng: DDL và ràng buộc →](04-ddl-constraint.md)

**Bạn sẽ học được:**

- Chọn kiểu số đúng việc: số nguyên theo phạm vi giá trị, `DECIMAL` cho tiền, và hiểu vì sao
  `FLOAT`/`DOUBLE` có sai số.
- Phân biệt `CHAR`, `VARCHAR`, `TEXT` và chuỗi nhị phân; hiểu charset `utf8mb4` và collation quyết
  định chuyện `'Hà'` có bằng `'ha'` hay không.
- Lưu ngày giờ không bị lệch múi giờ: `DATE`, `DATETIME`, `TIMESTAMP`, giới hạn năm 2038, phần lẻ
  của giây.
- Biết khi nào dùng `BOOLEAN`, `ENUM`/`SET`, `JSON`; lưu UUID gọn trong `BINARY(16)` và hiểu vì sao
  UUIDv7 hợp làm khoá chính hơn UUIDv4.
- Áp dụng nguyên tắc "kiểu nhỏ nhất mà đủ dùng", và hiểu strict SQL mode bảo vệ dữ liệu ra sao.
- Đối chiếu với PostgreSQL: `numeric`, `text`, `timestamptz`, `jsonb`, `uuid`.

**Cần biết trước:** [Chương 01](01-database-la-gi.md) (chạy được MySQL, mở được client) và
[Chương 02](02-mo-hinh-quan-he-thiet-ke.md) (bảng, cột, dòng, khoá chính).

## Chuẩn bị

Mọi ví dụ SQL viết cho MySQL 8.4, trừ chỗ ghi rõ là PostgreSQL. Nếu chưa có MySQL, chạy bằng Docker
(gõ trong terminal trên máy của bạn):

```sh
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# Server cần một lúc để khởi động. Nếu lệnh dưới báo không kết nối được, đợi thêm rồi thử lại.
docker exec -it my84 mysql -uroot -proot
```

Trong client (dấu nhắc `mysql>`), tạo một database riêng cho chương này:

```sql
CREATE DATABASE IF NOT EXISTS ch03;
USE ch03;
SET NAMES utf8mb4;   -- báo cho server biết client gửi và nhận chuỗi dạng UTF-8 (giải thích ở mục 6.2)
```

Mỗi mục bên dưới tự tạo bảng mẫu nhỏ của nó, nên bạn có thể chạy từng mục độc lập.

## 1. Kiểu dữ liệu là gì và vì sao phải chọn cẩn thận

### 1.1 Kiểu dữ liệu là gì

Ở chương 02, mỗi cột của bảng có một tên và một *kiểu dữ liệu* (data type). Kiểu dữ liệu là lời cam
kết về những giá trị cột đó được phép chứa. Nó quyết định bốn điều:

1. Giá trị nào hợp lệ. Cột `TINYINT UNSIGNED` chỉ chứa số nguyên từ 0 tới 255; cột `DATE` chỉ chứa
   ngày có thật.
2. Mỗi giá trị tốn bao nhiêu byte trên đĩa và trong bộ nhớ.
3. So sánh và sắp xếp ra sao. Số so theo giá trị, chuỗi so theo luật *collation* (mục 6), ngày so
   theo trình tự thời gian.
4. Phép toán và hàm nào dùng được: cộng hai số, cắt chuỗi, cộng thêm 3 ngày vào một ngày.

Một bảng sản phẩm đơn giản:

```sql
CREATE TABLE products (
  id         INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(200) NOT NULL,          -- chuỗi tối đa 200 ký tự
  price      DECIMAL(12,0) NOT NULL,         -- tiền VND: số chính xác, không có phần lẻ
  stock      SMALLINT UNSIGNED NOT NULL,     -- tồn kho từ 0 tới 65535
  is_active  BOOLEAN NOT NULL DEFAULT TRUE,  -- thực chất là TINYINT(1), xem mục 9
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Đối chiếu với PHP: biến PHP mang kiểu của giá trị nó đang giữ, nên `$x = 5;` rồi `$x = 'năm';` vẫn
hợp lệ (*dynamic typing*). Cột SQL thì khác: kiểu gắn với cột, mọi dòng phải tuân theo, và database
kiểm tra mỗi lần ghi. Kiểu cột vì thế là lớp ràng buộc cơ bản nhất của dữ liệu, đứng cạnh `NOT NULL`,
`UNIQUE`, `CHECK` mà chương 04 sẽ học.

### 1.2 Vì sao chọn kiểu lại quan trọng

Chọn sai kiểu thì bảng vẫn chạy, nên rất dễ xem nhẹ. Cái giá chỉ lộ ra khi dữ liệu đã nhiều:

- **Đúng đắn.** Lưu ngày bằng `VARCHAR` dạng `'15/12/2025'` thì `'31/02/2026'` (ngày không tồn tại)
  vẫn vào được, và sắp xếp theo chuỗi đặt `'02/01/2026'` trước `'15/12/2025'` dù nó là ngày sau.
  Lưu tiền bằng `FLOAT` thì cộng dồn ra những số lẻ không ai giải thích được (mục 3).
- **Dung lượng.** Mỗi byte thừa nhân với số dòng, rồi nhân tiếp với số index chứa cột đó. Với 100
  triệu dòng, một cột `BIGINT` (8 byte) thay cho `INT` (4 byte) tốn thêm khoảng 400 MB dữ liệu thô
  cho riêng cột ấy. Khoá chính còn đáng lo hơn: trong InnoDB, mỗi *secondary index* (index phụ) đều
  chứa kèm giá trị khoá chính (chương 11), nên khoá chính rộng làm phình mọi index của bảng.
- **Tốc độ.** InnoDB đọc và ghi theo từng *page* (mặc định 16 KB). Dòng càng nhỏ thì một page chứa
  càng nhiều dòng: cùng lượng RAM cache được nhiều dữ liệu hơn, cùng truy vấn đọc ít page hơn. So
  sánh hai số nguyên cũng rẻ hơn so sánh hai chuỗi theo luật collation.
- **Đổi kiểu về sau rất đắt.** Đổi kiểu một cột trên bảng lớn thường buộc MySQL chép lại toàn bộ bảng,
  trong lúc đó hệ thống chậm hoặc bị chặn ghi (chương 20). Chọn đúng từ đầu rẻ hơn nhiều.

### 1.3 Khi giá trị không vừa kiểu: strict SQL mode

Chuyện gì xảy ra nếu ghi số 256 vào cột `TINYINT` (tối đa 127)? Câu trả lời phụ thuộc *SQL mode*:
biến hệ thống `sql_mode` điều chỉnh mức "khó tính" của MySQL.

Mặc định của MySQL 8.4 gồm sáu chế độ: `ONLY_FULL_GROUP_BY`, `STRICT_TRANS_TABLES`,
`NO_ZERO_IN_DATE`, `NO_ZERO_DATE`, `ERROR_FOR_DIVISION_BY_ZERO`, `NO_ENGINE_SUBSTITUTION`. Khi một
trong hai chế độ `STRICT_TRANS_TABLES` hoặc `STRICT_ALL_TABLES` được bật, ta nói MySQL đang ở
*strict mode*.

```sql
SELECT @@SESSION.sql_mode;
-- ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION
```

Thử ghi giá trị quá phạm vi, lần lượt khi bật và khi tắt strict mode (ví dụ theo tài liệu MySQL):

```sql
CREATE TABLE t_range (i1 TINYINT, i2 TINYINT UNSIGNED);

-- Strict mode đang bật (mặc định):
INSERT INTO t_range VALUES (256, 256);
-- ERROR 1264 (22003): Out of range value for column 'i1' at row 1
SELECT * FROM t_range;
-- Empty set: không có dòng nào được ghi

-- Tắt strict mode cho riêng session này (chỉ để quan sát, đừng làm vậy ở production):
SET SESSION sql_mode = '';
INSERT INTO t_range VALUES (256, 256);
-- Query OK, 1 row affected, 2 warnings
SHOW WARNINGS;
-- | Warning | 1264 | Out of range value for column 'i1' at row 1 |
-- | Warning | 1264 | Out of range value for column 'i2' at row 1 |
SELECT * FROM t_range;
-- i1 = 127, i2 = 255: giá trị bị "kẹp" về biên của kiểu

SET SESSION sql_mode = DEFAULT;   -- trả session về giá trị global (mặc định ở trên)
```

Quy tắc rút ra:

- Strict mode bật: giá trị sai kiểu, vượt phạm vi, hoặc bị thiếu (cột `NOT NULL` không có giá trị mặc
  định) làm câu lệnh ghi báo lỗi. Với bảng InnoDB (có transaction), câu lệnh bị huỷ và rollback toàn
  bộ.
- Strict mode tắt: MySQL tự "điều chỉnh" giá trị (kẹp số về biên, cắt bớt chuỗi quá dài, đổi ngày
  không hợp lệ thành `'0000-00-00'`...) rồi vẫn ghi, chỉ để lại warning mà ứng dụng hầu như không
  bao giờ đọc. Dữ liệu sai một cách im lặng.
- Câu lệnh không ghi dữ liệu như `SELECT` chỉ sinh warning với giá trị không hợp lệ, kể cả khi strict
  mode bật.
- Từ khoá `IGNORE` (`INSERT IGNORE`, `UPDATE IGNORE`) thắng strict mode: lỗi bị hạ thành warning,
  giá trị gây lỗi chuyển đổi được thay bằng giá trị hợp lệ gần nhất.

⚠️ Nhiều người dùng `INSERT IGNORE` chỉ để bỏ qua dòng trùng khoá, mà không biết nó còn nuốt luôn lỗi
kiểu dữ liệu: số quá lớn bị kẹp về biên, chuỗi quá dài bị cắt, không ai hay.

Phía Laravel: kết nối `mysql` trong `config/database.php` (bản mặc định của Laravel 13) có
`'strict' => true`. Khi mở kết nối, Laravel đặt `SESSION sql_mode='ONLY_FULL_GROUP_BY,
STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'`
(với MySQL từ 8.0.11), gộp chung trong một câu `SET` với phần `NAMES` ở mục 6.2. Nếu đặt `'strict' => false`, Laravel đặt `sql_mode='NO_ENGINE_SUBSTITUTION'`,
tức tắt strict mode cho mọi kết nối của ứng dụng, dù server có bật.

⚠️ Lời khuyên hay gặp trên mạng "sửa lỗi `ONLY_FULL_GROUP_BY` bằng `'strict' => false`" tắt luôn cả
strict mode, nên từ đó dữ liệu sai được ghi im lặng. Muốn điều chỉnh từng chế độ thì dùng khoá
`'modes' => [...]` trong cấu hình kết nối (Laravel ghép danh sách đó thành `sql_mode`), hoặc tốt hơn
là sửa câu truy vấn (chương 08).

### 1.4 Bản đồ các nhóm kiểu

| Nhóm | Kiểu MySQL | Thường dùng cho | Mục |
|---|---|---|---|
| Số nguyên | `TINYINT`, `SMALLINT`, `MEDIUMINT`, `INT`, `BIGINT` | id, số lượng, bộ đếm | 2 |
| Số thực xấp xỉ | `FLOAT`, `DOUBLE` | số đo, toạ độ, tính toán khoa học | 3 |
| Số thập phân chính xác | `DECIMAL` | tiền, tỉ lệ cần chính xác tuyệt đối | 4 |
| Chuỗi ký tự | `CHAR`, `VARCHAR`, `TEXT` | tên, email, mô tả, nội dung bài viết | 5, 6 |
| Chuỗi nhị phân | `BINARY`, `VARBINARY`, `BLOB` | hash, UUID dạng gọn, dữ liệu thô | 7 |
| Ngày giờ | `DATE`, `TIME`, `DATETIME`, `TIMESTAMP`, `YEAR` | ngày sinh, thời điểm tạo, giờ mở cửa | 8 |
| Đúng/sai | `BOOLEAN` (thực chất là `TINYINT(1)`) | cờ bật/tắt | 9 |
| Tập giá trị cố định | `ENUM`, `SET` | trạng thái, nhãn | 10 |
| Bán cấu trúc | `JSON` | thuộc tính linh hoạt, payload từ API | 11 |

MySQL còn có kiểu `BIT` và các kiểu không gian (*spatial*: `POINT`, `GEOMETRY`...) cho dữ liệu bản đồ;
chương này không đi sâu vào chúng.

## 2. Số nguyên

### 2.1 Năm kiểu số nguyên

*Số nguyên* (integer) là số không có phần lẻ: 0, 42, -7. MySQL có năm kiểu số nguyên, khác nhau ở số
byte dùng để lưu, và vì thế khác nhau ở phạm vi giá trị:

| Kiểu | Byte | Có dấu (mặc định) | `UNSIGNED` |
|---|---|---|---|
| `TINYINT` | 1 | -128 tới 127 | 0 tới 255 |
| `SMALLINT` | 2 | -32768 tới 32767 | 0 tới 65535 |
| `MEDIUMINT` | 3 | -8388608 tới 8388607 | 0 tới 16777215 (khoảng 16,7 triệu) |
| `INT` (hay `INTEGER`) | 4 | -2147483648 tới 2147483647 (khoảng 2,1 tỉ) | 0 tới 4294967295 (khoảng 4,3 tỉ) |
| `BIGINT` | 8 | -2^63 tới 2^63 - 1 (9223372036854775807) | 0 tới 2^64 - 1 (18446744073709551615) |

Cách nhớ: n byte là 8n bit, biểu diễn được 2^(8n) giá trị khác nhau. Kiểu có dấu chia đôi số giá trị
đó cho phần âm và phần không âm; `UNSIGNED` dành hết cho phần không âm nên giới hạn trên gần gấp đôi.

Chọn kiểu theo giá trị lớn nhất cột có thể đạt trong suốt vòng đời dữ liệu, cộng thêm biên an toàn:

- Tuổi người, số sao đánh giá (1 tới 5): `TINYINT UNSIGNED`.
- Số lượng trong một dòng đơn hàng, số phút trong ngày: `SMALLINT UNSIGNED`.
- Lượt xem bài viết (có thể vượt 2 tỉ với trang lớn): `INT UNSIGNED` hoặc `BIGINT`.
- Khoá chính của bảng nghiệp vụ (`users`, `orders`...): `BIGINT UNSIGNED`, lý do ở mục 2.5.

### 2.2 UNSIGNED

Thuộc tính `UNSIGNED` (không dấu) cấm số âm và dịch phạm vi sang phía dương, như bảng trên. Nó có
hai tác dụng: phạm vi dương rộng gần gấp đôi, và chặn luôn giá trị âm vô nghĩa (tồn kho âm, tuổi âm)
ngay ở tầng kiểu dữ liệu.

```sql
CREATE TABLE t_unsigned (qty SMALLINT UNSIGNED);
INSERT INTO t_unsigned VALUES (-1);
-- ERROR 1264 (22003): Out of range value for column 'qty' at row 1
```

Cái giá phải trả là một cái bẫy ở phép trừ, xem ngay mục sau. PostgreSQL không có `UNSIGNED`; ở đó
người ta dùng ràng buộc `CHECK (qty >= 0)`, cách này MySQL 8.4 cũng hỗ trợ (chương 04).

### 2.3 Tràn số: khi ghi và khi tính

*Tràn số* (overflow) là khi giá trị vượt phạm vi của kiểu. Có hai lúc nó xảy ra.

Khi ghi vào cột: strict mode báo lỗi `1264 Out of range value`, như đã thấy ở mục 1.3.

Khi tính biểu thức: MySQL tính phép `+`, `-`, `*` trên hai số nguyên bằng số học `BIGINT`. Kết quả
vượt phạm vi `BIGINT` là lỗi, bất kể `sql_mode`:

```sql
SELECT 9223372036854775807 + 1;
-- ERROR 1690 (22003): BIGINT value is out of range in '(9223372036854775807 + 1)'

SELECT 9223372036854775807.0 + 1;
-- 9223372036854775808.0: literal có dấu chấm thập phân là DECIMAL (mục 4), phạm vi rộng hơn
```

Bẫy hay gặp hơn nhiều là phép trừ có một vế `UNSIGNED`. Theo mặc định, kết quả của phép trừ đó cũng
là số không dấu; nếu lẽ ra phải âm thì MySQL báo lỗi:

```sql
SELECT CAST(0 AS UNSIGNED) - 1;
-- ERROR 1690 (22003): BIGINT UNSIGNED value is out of range in '(cast(0 as unsigned) - 1)'
```

Tình huống thực tế: tìm các mặt hàng còn đủ 5 cái trong kho.

```sql
CREATE TABLE inventory (
  sku   VARCHAR(20) PRIMARY KEY,
  stock SMALLINT UNSIGNED NOT NULL
);
INSERT INTO inventory VALUES ('A', 3), ('B', 10);

SELECT sku FROM inventory WHERE stock - 5 >= 0;
-- ERROR 1690 (22003): BIGINT UNSIGNED value is out of range in ...
-- (dòng 'A' có stock = 3, phép trừ 3 - 5 không biểu diễn được bằng số không dấu)

SELECT sku FROM inventory WHERE stock >= 5;
-- B
```

Cách viết thứ hai vừa đúng vừa tốt hơn: không có phép trừ nên không tràn, và để cột đứng một mình ở
một vế so sánh thì MySQL mới dùng được index trên cột đó (chương 11).

Trừ tồn kho khi bán hàng cũng theo cùng ý: đặt điều kiện vào `WHERE` thay vì để phép trừ ra số âm.

```sql
UPDATE inventory SET stock = stock - 5 WHERE sku = 'A' AND stock >= 5;
-- Query OK, 0 rows affected: không đủ hàng, ứng dụng xem số dòng bị ảnh hưởng để biết
UPDATE inventory SET stock = stock - 5 WHERE sku = 'B' AND stock >= 5;
-- Query OK, 1 row affected: B còn 5
```

Nếu bỏ điều kiện `stock >= 5`, câu `UPDATE` cho dòng 'A' gặp lỗi tràn ở trên; với strict mode câu lệnh
báo lỗi và cột giữ nguyên giá trị. Cách viết "kiểm tra và trừ trong cùng một câu" còn an toàn khi
nhiều người mua cùng lúc, chương 13 và 15 sẽ giải thích vì sao.

SQL mode `NO_UNSIGNED_SUBTRACTION` khiến phép trừ trả kết quả có dấu (`-1` thay vì lỗi). Biết để đọc
hiểu cấu hình của hệ thống cũ; đừng bật nó chỉ để né lỗi, vì viết lại điều kiện như trên mới là cách
sửa đúng.

### 2.4 INT(11) không có nghĩa là 11 chữ số

Bạn sẽ gặp `int(11)`, `bigint(20)`, `int(10) unsigned` trong schema cũ. Con số trong ngoặc là
*display width* (độ rộng hiển thị), không phải giới hạn giá trị: `SMALLINT(3)` vẫn chứa được 32767 và
hiển thị đủ năm chữ số. Nó chỉ có tác dụng khi đi kèm `ZEROFILL`, thuộc tính đệm số 0 bên trái: cột
`INT(4) ZEROFILL` lưu `5` thì đọc ra `0005` (và `ZEROFILL` tự thêm `UNSIGNED`).

Cả display width của kiểu số nguyên lẫn `ZEROFILL` đã deprecated từ MySQL 8.0.17 và sẽ bị bỏ ở một
phiên bản tương lai. Từ 8.0.19, `SHOW CREATE TABLE` và `DESCRIBE` không còn in display width của số
nguyên, trừ hai trường hợp: `TINYINT(1)` (các connector coi `TINYINT(1)` là cột boolean, mục 9) và cột
có `ZEROFILL`.

⚠️ `int(11)` trong dump cũ chỉ là cách MySQL 5.7 hiển thị `INT` mặc định, không phải lựa chọn có chủ
đích, và nó không giới hạn gì cả. Khi viết schema mới, bỏ con số đi. Cần mã có số 0 ở đầu (mã nhân
viên `00042`) thì định dạng ở tầng ứng dụng, ví dụ `sprintf('%05d', $id)` trong PHP; hoặc, nếu nó là
một mã chứ không phải một con số để tính toán, lưu dạng chuỗi `CHAR(5)`.

### 2.5 AUTO_INCREMENT và kiểu của khoá chính

`AUTO_INCREMENT` (chi tiết ở chương 04) tự sinh số tăng dần cho cột khoá chính. Khi bộ đếm chạm giới
hạn của kiểu, MySQL không tự chuyển sang kiểu lớn hơn: lần `INSERT` tiếp theo báo lỗi trùng khoá
(*duplicate-key error*), và từ đó bảng không nhận thêm dòng mới nào. Chức năng phụ thuộc bảng đó ngừng
hoạt động.

Thử nhẩm với tốc độ đều 100 dòng mỗi giây (8,64 triệu dòng mỗi ngày):

| Kiểu khoá chính | Giới hạn | Hết số sau khoảng |
|---|---|---|
| `INT` | 2.147.483.647 | 249 ngày |
| `INT UNSIGNED` | 4.294.967.295 | 497 ngày |
| `BIGINT` | 9.223.372.036.854.775.807 | 2,9 tỉ năm |

Thực tế số id bị tiêu còn nhanh hơn số dòng: transaction rollback không trả lại số đã cấp, và
`INSERT ... ON DUPLICATE KEY UPDATE` có thể cấp một số rồi không dùng tới. Id vì thế có "lỗ hổng", và
một bảng chỉ vài trăm triệu dòng vẫn có thể chạm trần `INT`. Đổi kiểu khoá chính khi bảng đã lớn
nghĩa là chép lại bảng và sửa mọi cột khoá ngoại trỏ tới nó. Chênh lệch 4 byte mỗi dòng rẻ hơn nhiều
so với sự cố đó, nên mặc định hợp lý cho khoá chính là `BIGINT UNSIGNED`.

MySQL có sẵn tên tắt `SERIAL`, nghĩa là `BIGINT UNSIGNED NOT NULL AUTO_INCREMENT UNIQUE`. Trong
Laravel, `$table->id()` tạo `BIGINT UNSIGNED AUTO_INCREMENT` làm khoá chính, và `$table->foreignId('user_id')`
tạo cột `BIGINT UNSIGNED` khớp với nó.

⚠️ Cột khoá ngoại phải cùng kiểu với cột được trỏ tới: với kiểu số nguyên, cùng kích thước và cùng có
dấu hay không dấu. Trỏ một cột `INT` vào khoá chính `BIGINT UNSIGNED` thì MySQL từ chối tạo khoá ngoại
(chương 04).

### 2.6 Đối chiếu với PHP

Trên bản PHP 64-bit (gần như mọi máy chủ hiện nay), kiểu `int` của PHP là số 64-bit có dấu, cùng phạm
vi với `BIGINT` có dấu. Khác biệt nằm ở cách xử lý tràn: MySQL báo lỗi, còn PHP lặng lẽ chuyển sang
`float` và mất độ chính xác.

```php
<?php
declare(strict_types=1);

var_dump(PHP_INT_MAX);       // in ra: int(9223372036854775807)
var_dump(PHP_INT_MAX + 1);   // in ra: float(9.223372036854776E+18)
```

Hệ quả: giá trị `BIGINT UNSIGNED` lớn hơn `PHP_INT_MAX` không vừa kiểu `int` của PHP, nên driver
`mysqlnd` (mà `pdo_mysql` dùng) trả riêng những giá trị đó về dạng chuỗi. Cùng một cột, dòng này ra
`int`, dòng kia ra `string`: với `===` thì đó là bug chờ xảy ra. Id tăng dần không bao giờ tới mức
đó, nhưng nếu bạn lưu số 64-bit không dấu từ hệ thống khác (hash, id của dịch vụ ngoài) thì phải nhớ
điều này. Từ PHP 8.1, `pdo_mysql` trả cột số nguyên và số thực về kiểu
`int`/`float` của PHP cả khi dùng emulated prepared statement (trước đó là chuỗi), còn `DECIMAL` vẫn
là chuỗi (mục 4.5). Chi tiết phía ứng dụng ở chương 19.

## 3. Số thực xấp xỉ: FLOAT và DOUBLE

### 3.1 Số dấu phẩy động là gì

`FLOAT` và `DOUBLE` lưu *số dấu phẩy động* (floating-point number) theo chuẩn IEEE 754, giống hệt
kiểu `float` của PHP. Ý tưởng tương tự cách viết khoa học 6,02 × 10^23: lưu một phần định trị và một
số mũ, chỉ khác là cơ số 2 thay vì 10. Nhờ vậy phạm vi cực rộng, đổi lại chỉ giữ được một số chữ số
có nghĩa nhất định; phần còn lại bị làm tròn.

| Kiểu | Byte | Độ chính xác | Phạm vi giá trị tuyệt đối (ngoài số 0) |
|---|---|---|---|
| `FLOAT` | 4 | single precision, khoảng 7 chữ số có nghĩa | 1.175494351E-38 tới 3.402823466E+38 |
| `DOUBLE` (tên khác: `DOUBLE PRECISION`, `REAL`) | 8 | double precision, khoảng 15 tới 16 chữ số có nghĩa | 2.2250738585072014E-308 tới 1.7976931348623157E+308 |

(`REAL` là `DOUBLE`, trừ khi bật SQL mode `REAL_AS_FLOAT`.)

### 3.2 Vì sao 0.1 + 0.2 không bằng 0.3

Trong hệ thập phân, 1/3 viết ra là 0,3333... không bao giờ hết; phải dừng ở đâu đó thì giá trị đã bị
làm tròn. Hệ nhị phân cũng vậy, chỉ là với những số khác: 0.1 trong hệ nhị phân là
0.000110011001100... lặp vô hạn. Máy buộc phải cắt, nên cái được lưu là "số gần 0.1 nhất mà kiểu đó
biểu diễn được", không phải 0.1.

PHP dùng cùng chuẩn IEEE 754, nên thấy được ngay:

```php
<?php
declare(strict_types=1);

var_dump(0.1 + 0.2);            // in ra: float(0.30000000000000004)
var_dump(0.1 + 0.2 === 0.3);    // in ra: bool(false)
printf("%.20f\n", 0.1);         // in ra: 0.10000000000000000555

// FLOAT của MySQL chỉ có 4 byte. pack/unpack với mã 'g' ép 0.1 vào 4 byte rồi đọc lại:
$asFloat32 = unpack('g', pack('g', 0.1))[1];
var_dump($asFloat32);           // in ra: float(0.10000000149011612)

// Cộng 0.0001 mười nghìn lần, lẽ ra được đúng 1:
$sum = 0.0;
for ($i = 0; $i < 10000; $i++) {
    $sum += 0.0001;
}
var_dump($sum);                 // in ra: float(0.9999999999999062)
```

Sai số mỗi bước rất nhỏ, nhưng cộng dồn qua hàng triệu phép tính, hoặc đem so sánh bằng, thì thành
sai thật.

Trong MySQL, một literal số có dấu chấm thập phân như `0.1` là *giá trị chính xác* (exact value,
kiểu `DECIMAL`), còn literal viết dạng số mũ như `1E-1` hay `.1E0` là *giá trị xấp xỉ* (approximate
value, kiểu `DOUBLE`). Ví dụ từ tài liệu MySQL:

```sql
SELECT (.1 + .2) = .3;         -- 1: cả ba là giá trị chính xác, tính bằng số học DECIMAL
SELECT (.1E0 + .2E0) = .3E0;   -- 0: giá trị xấp xỉ, sai số lộ ra
```

Một biểu thức chỉ cần chứa một giá trị xấp xỉ (một cột `FLOAT`/`DOUBLE`, một literal dạng mũ, hay một
chuỗi bị đổi sang số) là toàn bộ biểu thức được tính bằng số thực xấp xỉ.

### 3.3 Bẫy so sánh bằng trên cột FLOAT

```sql
CREATE TABLE sensor (id INT PRIMARY KEY, v FLOAT);
INSERT INTO sensor VALUES (1, 0.1);

SELECT v FROM sensor;                  -- 0.1 (MySQL làm tròn khi hiển thị)
SELECT id FROM sensor WHERE v = 0.1;   -- Empty set
```

Giải thích: cột `FLOAT` lưu số 4 byte gần 0.1 nhất, tức 0.10000000149011612... như ở ví dụ PHP trên.
Khi so sánh cột số thực với hằng `0.1`, MySQL so sánh hai bên dưới dạng số thực double. Giá trị đọc
từ cột (0.10000000149011612) khác giá trị double của 0.1 (0.1000000000000000055...), nên không dòng
nào khớp. Tài liệu MySQL nói thẳng: so sánh cột `FLOAT` hay `DOUBLE` với số có phần thập phân thì
không dùng được phép `=`.

Cách xử lý:

- So sánh trong một khoảng sai số chấp nhận được, như tài liệu MySQL gợi ý:
  `WHERE ABS(v - 0.1) <= 0.0001`.
- Nếu nghiệp vụ cần so sánh bằng đúng từng chữ số, thì dữ liệu đó không thuộc về `FLOAT`/`DOUBLE`.
  Dùng `DECIMAL` (mục 4).

`FLOAT` còn kém hơn bạn tưởng: 4 byte chỉ có 24 bit cho phần định trị, nên ngay cả số nguyên lớn hơn
2^24 = 16777216 cũng bắt đầu bị làm tròn.

```php
<?php
declare(strict_types=1);

var_dump(unpack('g', pack('g', 16777217.0))[1]);   // in ra: float(16777216)
```

### 3.4 Cú pháp cũ nên tránh

- `FLOAT(M,D)` và `DOUBLE(M,D)` (tổng `M` chữ số, `D` chữ số sau dấu phẩy) là mở rộng riêng của
  MySQL, đã deprecated. MySQL làm tròn khi lưu: ghi `999.00009` vào cột `FLOAT(7,4)` được khoảng
  `999.0001`. Cần số chữ số cố định thì dùng `DECIMAL`.
- `FLOAT(p)` với `p` là số bit độ chính xác: `p` chỉ dùng để chọn lưu 4 byte hay 8 byte. `p` nhỏ cho
  ra `FLOAT`, `p` lớn (tối đa 53) cho ra `DOUBLE`. Ví dụ: `$table->float('score')` của Laravel sinh
  `float(53)`, và MySQL tạo ra cột `DOUBLE`.
- `UNSIGNED` trên `FLOAT`, `DOUBLE`, `DECIMAL` đã deprecated. Khác với số nguyên, nó chỉ cấm số âm chứ
  không nới phạm vi dương. Muốn cấm số âm, dùng `CHECK` (chương 04).
- Từ MySQL 8.4.0, `AUTO_INCREMENT` trên cột `FLOAT`/`DOUBLE` không còn được hỗ trợ.

Tài liệu MySQL khuyên: để dễ chuyển đổi giữa các hệ quản trị, khai báo `FLOAT` hoặc `DOUBLE PRECISION`
trơn, không kèm số chữ số.

### 3.5 Khi nào nên dùng FLOAT/DOUBLE

Số dấu phẩy động hợp với dữ liệu vốn đã xấp xỉ: số đo từ cảm biến, kết quả tính toán khoa học, điểm
số của mô hình học máy, các chỉ số thống kê. Với những dữ liệu này, sai số ở chữ số thứ 15 không có ý
nghĩa gì, còn phạm vi rộng và tính toán nhanh thì có ích.

Không dùng cho: tiền, số lượng phải khớp sổ sách, bất cứ thứ gì cần so sánh bằng hoặc cần cộng ra
đúng từng đồng. Giữa hai kiểu, chọn `DOUBLE` trừ khi thật sự cần tiết kiệm 4 byte mỗi giá trị; 7 chữ
số có nghĩa của `FLOAT` thiếu cho khá nhiều việc.

## 4. DECIMAL: số thập phân chính xác

### 4.1 DECIMAL(M,D) là gì

`DECIMAL` lưu số thập phân *chính xác* (fixed-point, dấu phẩy cố định): mỗi chữ số thập phân bạn ghi
vào được giữ nguyên, không có chuyện 0.1 biến thành 0.10000000149. Đây là kiểu dành cho tiền và mọi
con số phải khớp tuyệt đối. `NUMERIC` là tên khác; MySQL cài đặt `NUMERIC` như `DECIMAL`.

Cú pháp `DECIMAL(M,D)`:

- `M` (*precision*): tổng số chữ số, tối đa 65.
- `D` (*scale*): số chữ số sau dấu phẩy, tối đa 30, và không được lớn hơn `M`.
- Phần nguyên có tối đa `M - D` chữ số. Ví dụ `DECIMAL(5,2)` chứa từ -999.99 tới 999.99.

⚠️ Giá trị mặc định dễ gây bất ngờ: `DECIMAL` trơn là `DECIMAL(10,0)`, và `DECIMAL(M)` là
`DECIMAL(M,0)`. Tức là không có phần lẻ. Khai `price DECIMAL` cho giá USD thì 19.99 bị làm tròn thành
20. Laravel thì khác: `$table->decimal('amount')` mặc định là `decimal(8, 2)`. Luôn ghi rõ cả `M` và
`D`.

### 4.2 Làm tròn và tràn khi ghi

Hai tình huống, hai cách xử lý khác nhau:

1. Phần nguyên quá dài (vượt `M - D` chữ số): strict mode báo lỗi `1264 Out of range value`, câu lệnh
   bị huỷ.
2. Phần lẻ có nhiều chữ số hơn `D`: MySQL làm tròn về `D` chữ số theo kiểu *round half away from zero*
   (năm làm tròn ra xa số 0: 2.5 thành 3, -2.5 thành -3), và chỉ sinh một Note `1265 Data truncated`.
   Theo tài liệu MySQL, việc này không phải lỗi, kể cả ở strict mode.

```sql
CREATE TABLE price_demo (p DECIMAL(5,2));

INSERT INTO price_demo VALUES (19.995), (19.994), (-19.995);
-- Thành công, kèm các Note 1265 "Data truncated for column 'p'"
SELECT p FROM price_demo;
-- 20.00
-- 19.99
-- -20.00

INSERT INTO price_demo VALUES (1000.00);
-- ERROR 1264 (22003): Out of range value for column 'p' at row 1
-- (DECIMAL(5,2) chỉ có 3 chữ số phần nguyên, tối đa 999.99)
```

Ví dụ từ tài liệu MySQL cho thấy quy tắc này áp dụng cả khi giá trị ghi vào là số xấp xỉ: ghi `2.5`
và `2.5E0` vào cột `DECIMAL(10,0)` đều được `3`.

⚠️ Đừng phó mặc việc làm tròn tiền cho cột. Làm tròn nửa lên, làm tròn kiểu ngân hàng (*banker's
rounding*, về số chẵn gần nhất), làm tròn từng dòng hay làm tròn tổng là quyết định nghiệp vụ. Hãy làm
tròn tường minh ở ứng dụng trước khi ghi, để con số được ghi đúng là con số bạn đã tính.

Hàm `ROUND()` cũng có hai hành vi: với giá trị chính xác, nó làm tròn half away from zero
(`ROUND(2.5)` ra 3); với giá trị xấp xỉ, kết quả phụ thuộc thư viện C, trên nhiều hệ thống là làm tròn
về số chẵn gần nhất (`ROUND(2.5E0)` ra 2).

### 4.3 Bên trong: DECIMAL được lưu và tính thế nào

MySQL lưu `DECIMAL` dạng nhị phân, gói mỗi 9 chữ số thập phân vào 4 byte. Phần nguyên và phần lẻ được
tính riêng; số chữ số lẻ ra (không đủ 9) tốn thêm theo bảng:

| Số chữ số còn lẻ | Byte |
|---|---|
| 0 | 0 |
| 1 tới 2 | 1 |
| 3 tới 4 | 2 |
| 5 tới 6 | 3 |
| 7 tới 9 | 4 |

Ví dụ tính dung lượng:

| Kiểu | Phần nguyên | Phần lẻ | Tổng |
|---|---|---|---|
| `DECIMAL(18,9)` | 9 chữ số: 4 byte | 9 chữ số: 4 byte | 8 byte |
| `DECIMAL(20,6)` | 14 chữ số: 4 + 3 byte | 6 chữ số: 3 byte | 10 byte |
| `DECIMAL(19,4)` | 15 chữ số: 4 + 3 byte | 4 chữ số: 2 byte | 9 byte |
| `DECIMAL(15,0)` | 15 chữ số: 4 + 3 byte | không có | 7 byte |

Dấu `+`, `-` và số 0 vô nghĩa ở đầu không được lưu: ghi `+0003.1` vào `DECIMAL(5,1)` thì được `3.1`.

Khi tính toán, biểu thức chỉ gồm giá trị chính xác có phần lẻ được tính bằng số học thập phân chính
xác tới 65 chữ số; biểu thức chỉ gồm số nguyên thì tính bằng `BIGINT`. Phép chia `/` giữa hai giá trị
chính xác cho kết quả có số chữ số lẻ bằng scale của số bị chia cộng `div_precision_increment` (mặc
định 4):

```sql
SELECT 1 / 3;           -- 0.3333
SELECT 5.05 / 0.014;    -- 360.714286 (scale 2 + 4 = 6, ví dụ của tài liệu MySQL)
```

Nghĩa là "chính xác" vẫn có giới hạn: 1/3 không viết hết được ở hệ thập phân, nên phép chia luôn phải
làm tròn ở đâu đó. Khác biệt với `DOUBLE` là chỗ làm tròn nằm ở hệ thập phân, đúng như cách con người
và kế toán làm tròn, và bạn kiểm soát được số chữ số.

### 4.4 Lưu tiền: DECIMAL hay số nguyên

Có hai cách đúng để lưu tiền, cả hai đều không dùng `FLOAT`/`DOUBLE`:

| | `DECIMAL(M,D)` | `BIGINT` theo đơn vị nhỏ nhất |
|---|---|---|
| Ví dụ | `amount DECIMAL(19,4)` lưu `19.9900` (USD) | `amount_minor BIGINT` lưu `1999` (cent) |
| Ưu điểm | Đọc thẳng được; phép toán SQL (`SUM`, `AVG`) ra đúng đơn vị | Số nguyên: nhanh, chính xác, mọi ngôn ngữ xử lý tốt |
| Nhược điểm | Phía PHP nhận về chuỗi, phải tính bằng bcmath hoặc thư viện | Phải nhớ quy đổi khi hiển thị; đổi đơn vị nhỏ nhất là sửa dữ liệu |
| Hợp với | Giá có phần lẻ nhỏ hơn đơn vị nhỏ nhất (tỉ giá, đơn giá điện) | Hệ thống thanh toán, ví, sổ cái |

Một vài lưu ý:

- Đồng Việt Nam theo ISO 4217 không có đơn vị lẻ, nên với hệ thống chỉ dùng VND thì `BIGINT` (hoặc
  `DECIMAL(15,0)`) đã đủ. USD có 2 chữ số lẻ (cent); có đồng tiền dùng 3 chữ số lẻ. Một cột tiền
  dùng cho nhiều loại tiền phải đủ chỗ cho loại có nhiều chữ số lẻ nhất.
- `DECIMAL(19,4)` là lựa chọn phổ biến khi cần thêm chữ số lẻ cho các phép tính trung gian (thuế, chiết
  khấu theo phần trăm). Bốn chữ số lẻ không thay cho quy tắc làm tròn: vẫn phải làm tròn tường minh
  trước khi chốt số tiền.
- Luôn lưu kèm mã tiền tệ, ví dụ `currency CHAR(3)` theo ISO 4217 (`'VND'`, `'USD'`). Một con số tiền
  không có đơn vị là một con số vô nghĩa.

### 4.5 Phía PHP: đừng biến tiền thành float

`pdo_mysql` trả giá trị cột `DECIMAL` về dạng chuỗi, ví dụ `"19990.50"`, kể cả từ PHP 8.1 (bản đổi số
nguyên và số thực sang kiểu PHP gốc không áp dụng cho `DECIMAL`). Chuỗi là cách duy nhất giữ đủ độ
chính xác, vì PHP không có kiểu số thập phân gốc. Lỗi hay gặp là vô tình biến nó thành `float`:

```php
<?php
declare(strict_types=1);

// Giả sử đây là một dòng PDO trả về từ hai cột DECIMAL(15,2): giá trị là chuỗi
$row = ['price' => '0.10', 'fee' => '0.20'];

$asFloat = (float) $row['price'] + (float) $row['fee'];
var_dump($asFloat);                  // in ra: float(0.30000000000000004)
var_dump($asFloat === 0.3);          // in ra: bool(false)

var_dump('19990.50' * 3);            // in ra: float(59971.5): chuỗi số nhân số là ra float

// Đúng: tính trên chuỗi thập phân bằng bcmath (tham số cuối là số chữ số lẻ của kết quả)
var_dump(bcadd($row['price'], $row['fee'], 2));   // in ra: string(4) "0.30"
var_dump(bcmul('19990.50', '3', 2));              // in ra: string(8) "59971.50"

// PHP 8.4+: class BcMath\Number cho phép dùng toán tử + - * / trực tiếp
$n = new BcMath\Number($row['price']) + new BcMath\Number($row['fee']);
var_dump((string) $n);               // in ra: string(4) "0.30"
```

`declare(strict_types=1)` không cứu được ở đây: nó chỉ kiểm tra kiểu tham số khi gọi hàm, còn phép
toán `'19990.50' * 3` trên chuỗi số vẫn hợp lệ và cho ra `float`.

Các lựa chọn thực tế: hàm bcmath (cần extension `bcmath`), `BcMath\Number` từ PHP 8.4, hoặc thư viện
như `brick/money` (có sẵn khái niệm tiền tệ và quy tắc làm tròn). Trong Laravel, cast `'decimal:2'`
của Eloquent trả về chuỗi, được làm tròn half up bằng thư viện `brick/math`; đừng đổi nó thành cast
`'float'`.

## 5. Chuỗi ký tự: CHAR, VARCHAR, TEXT

### 5.1 Ký tự và byte

Chuỗi là một dãy ký tự. Khi lưu xuống đĩa, mỗi ký tự thành một hoặc vài byte theo quy tắc của
*charset* (mục 6). Với `utf8mb4`, charset bạn nên dùng, số byte thay đổi theo ký tự:

```php
<?php
declare(strict_types=1);

foreach (['a', 'ệ', '😀'] as $ch) {
    printf("%s: %d byte, hex %s\n", $ch, strlen($ch), bin2hex($ch));
}
// in ra:
// a: 1 byte, hex 61
// ệ: 3 byte, hex e1bb87
// 😀: 4 byte, hex f09f9880

var_dump(strlen('Việt'));      // in ra: int(6)  (đếm byte)
var_dump(mb_strlen('Việt'));   // in ra: int(4)  (đếm ký tự)
```

MySQL có cặp hàm tương tự:

```sql
SELECT LENGTH('Việt'), CHAR_LENGTH('Việt');   -- 6, 4
```

Ghi nhớ: số `n` trong `CHAR(n)` và `VARCHAR(n)` là số ký tự. Nhưng nhiều giới hạn khác (kích thước
dòng, độ dài key của index, dung lượng `TEXT`) lại tính bằng byte. Với `utf8mb4`, hai đơn vị này có
thể lệch nhau tới 4 lần.

### 5.2 CHAR và VARCHAR

| | `CHAR(n)` | `VARCHAR(n)` |
|---|---|---|
| `n` tối đa | 255 ký tự | 65.535 trên lý thuyết, thực tế bị giới hạn bởi kích thước dòng (mục 5.5) |
| Cách lưu | Độ dài cố định: đệm khoảng trắng bên phải cho đủ `n` | Độ dài thay đổi: 1 hoặc 2 byte ghi độ dài, rồi tới dữ liệu thật |
| Khi đọc ra | Khoảng trắng ở cuối bị cắt bỏ | Giữ nguyên như lúc ghi |
| Hợp với | Mã ngắn có độ dài cố định: `'VN'`, `'VND'` | Gần như mọi chuỗi khác: tên, email, tiêu đề |

`VARCHAR` dùng 1 byte độ dài nếu giá trị không bao giờ cần quá 255 byte, và 2 byte nếu có thể vượt.
Bảng dưới (theo tài liệu MySQL, giả sử charset 1 byte mỗi ký tự như `latin1`) cho thấy khác biệt:

| Giá trị ghi vào | `CHAR(4)` lưu | Byte | `VARCHAR(4)` lưu | Byte |
|---|---|---|---|---|
| `''` | `'    '` | 4 | `''` | 1 |
| `'ab'` | `'ab  '` | 4 | `'ab'` | 3 |
| `'abcd'` | `'abcd'` | 4 | `'abcd'` | 5 |

Khoảng trắng cuối bị `CHAR` cắt khi đọc:

```sql
CREATE TABLE vc (v VARCHAR(4), c CHAR(4));
INSERT INTO vc VALUES ('ab  ', 'ab  ');
SELECT CONCAT('(', v, ')'), CONCAT('(', c, ')') FROM vc;
-- (ab  )   (ab)
```

Với charset nhiều byte như `utf8mb4`, InnoDB không lưu `CHAR(n)` thành đúng 4n byte: nó dành tối
thiểu `n` byte, cố lưu trong `n` byte bằng cách bỏ khoảng trắng thừa, và chỉ dùng tới 4n byte khi
nội dung cần. Vì thế lợi thế "độ dài cố định" của `CHAR` gần như không còn. Chỉ dùng `CHAR` cho mã
ngắn có độ dài cố định thật sự: mã quốc gia `CHAR(2)`, mã tiền tệ `CHAR(3)`.

### 5.3 Quá độ dài và khoảng trắng cuối

```sql
CREATE TABLE t_len (code VARCHAR(5));

INSERT INTO t_len VALUES ('ABCDEFG');
-- ERROR 1406 (22001): Data too long for column 'code' at row 1

INSERT INTO t_len VALUES ('ABC     ');   -- 'ABC' + 5 khoảng trắng = 8 ký tự
-- Thành công, kèm 1 cảnh báo: phần khoảng trắng vượt quá 5 ký tự bị cắt, còn 'ABC  '
```

Quy tắc theo tài liệu MySQL:

- Ký tự thật vượt độ dài: strict mode báo lỗi; không strict thì cắt bớt và cảnh báo.
- Riêng khoảng trắng thừa ở cuối: với `VARCHAR`, bị cắt kèm cảnh báo, bất kể SQL mode; với `CHAR`, bị
  cắt im lặng.

Khoảng trắng cuối còn ảnh hưởng tới phép so sánh: `'a'` và `'a '` bằng nhau hay khác nhau tuỳ
collation (mục 6.5). ⚠️ Với collation coi chúng bằng nhau, cột có `UNIQUE` sẽ báo trùng khoá khi đã có
`'a'` mà ghi thêm `'a '`. Cách phòng là cắt khoảng trắng hai đầu dữ liệu người dùng nhập ở tầng ứng
dụng (Laravel mặc định có middleware `TrimStrings` làm việc này cho input của request).

### 5.4 TEXT: chuỗi dài

| Kiểu | Dung lượng tối đa | Byte ghi độ dài |
|---|---|---|
| `TINYTEXT` | 255 byte | 1 |
| `TEXT` | 65.535 byte (khoảng 64 KB) | 2 |
| `MEDIUMTEXT` | 16.777.215 byte (khoảng 16 MB) | 3 |
| `LONGTEXT` | 4.294.967.295 byte (khoảng 4 GB) | 4 |

⚠️ Giới hạn tính bằng byte, không phải ký tự. Cột `TEXT` dùng `utf8mb4` chứa được 65.535 byte, tức chỉ
khoảng 21.845 ký tự tiếng Việt có dấu loại 3 byte. Một bài viết dài có thể vượt mức đó; khi ấy dùng
`MEDIUMTEXT` (`$table->mediumText()` trong Laravel; `$table->text()` là `TEXT`).

`TEXT` khác `VARCHAR` ở những điểm sau:

- Không đệm khi ghi, không cắt khoảng trắng khi đọc.
- Chỉ góp 9 tới 12 byte vào giới hạn 65.535 byte của một dòng, vì nội dung được lưu tách ra. Với row
  format mặc định `DYNAMIC`, giá trị dài (của `TEXT`, `BLOB`, và cả `VARCHAR` dài) có thể nằm hẳn ở
  page riêng, dòng chính chỉ giữ một con trỏ 20 byte; `TEXT` từ 40 byte trở xuống được lưu ngay trong
  dòng.
- Index trên `TEXT` bắt buộc chỉ định độ dài tiền tố, ví dụ `INDEX (body(100))`: chỉ 100 ký tự đầu
  được đưa vào index (chương 11).
- Không có giá trị mặc định dạng literal (`DEFAULT ''` bị từ chối); chỉ được dùng biểu thức trong
  ngoặc, ví dụ `DEFAULT ('')`.
- Khi sắp xếp, MySQL chỉ dùng `max_sort_length` byte đầu (mặc định 1024).
- Giá trị lớn nhất truyền được giữa client và server còn bị giới hạn bởi biến `max_allowed_packet`.

Quy tắc chọn: `VARCHAR` cho chuỗi có giới hạn hợp lý mà bạn cần so sánh, lọc, index theo nguyên giá
trị (tên, email, mã); `TEXT` cho nội dung dài mà bạn không tra cứu theo nguyên giá trị (nội dung bài
viết, mô tả, ghi chú).

### 5.5 Giới hạn kích thước dòng và độ dài index

Hai giới hạn tính bằng byte hay làm người mới bất ngờ:

1. **Một dòng tối đa 65.535 byte**, chia chung cho mọi cột (trừ phần nội dung của `TEXT`/`BLOB`). Mỗi
   cột `VARCHAR(n)` được tính theo độ dài tối đa có thể, tức `n` nhân số byte tối đa mỗi ký tự. Vì
   vậy một cột `VARCHAR` dùng `utf8mb4` khai báo được tối đa 16.383 ký tự. Vượt giới hạn thì
   `CREATE TABLE` báo `ERROR 1118 (42000): Row size too large...`; cách sửa là chuyển cột dài sang
   `TEXT`. Ngoài ra, phần dữ liệu InnoDB lưu ngay trong page cho mỗi dòng phải nhỏ hơn khoảng nửa page
   (gần 8 KB với page 16 KB); cột dài vượt mức được tự động đẩy ra page riêng.
2. **Key của index tối đa 3072 byte** với row format `DYNAMIC` (mặc định). `VARCHAR(255)` dùng
   `utf8mb4` tối đa 1020 byte nên index được; `VARCHAR(1000)` tối đa 4000 byte thì không index nguyên
   cột được (MySQL báo `Specified key was too long; max key length is 3072 bytes`), phải dùng index
   tiền tố hoặc index trên một cột hash (mục 7.2).

Lịch sử đáng biết: row format cũ (`COMPACT`, `REDUNDANT`) chỉ cho key 767 byte, tương đương 191 ký tự
`utf8mb4`. Đó là lý do nhiều dự án Laravel cũ có dòng `Schema::defaultStringLength(191)`. Với MySQL 8.4
và row format `DYNAMIC`, không cần dòng đó nữa.

### 5.6 Chọn độ dài cho VARCHAR

Độ dài khai báo không làm tốn chỗ trên đĩa (chỉ dữ liệu thật cộng 1 hoặc 2 byte), nhưng nó vẫn có ý
nghĩa: nó là ràng buộc dữ liệu (strict mode chặn chuỗi dài hơn), và nó quyết định cột có index được
nguyên giá trị hay không, có làm dòng chạm giới hạn 65.535 byte hay không (mục 5.5).

Chọn theo nghiệp vụ, cộng biên an toàn:

| Dữ liệu | Gợi ý |
|---|---|
| Mã sản phẩm, SKU | `VARCHAR(50)` |
| Họ tên | `VARCHAR(100)` |
| Email, tiêu đề | `VARCHAR(255)` |
| URL | `VARCHAR(2048)` hoặc `TEXT`; cần tra cứu theo URL thì index một cột hash của nó (mục 7.2) |
| Nội dung bài viết | `TEXT` hoặc `MEDIUMTEXT` |

Trong Laravel, `$table->string('name')` tạo `VARCHAR(255)`, còn `$table->string('sku', 50)` tạo
`VARCHAR(50)`.

## 6. Charset và collation

### 6.1 Charset: từ ký tự tới byte

Máy tính chỉ lưu byte. *Character set* (charset, bảng mã) là quy ước biến ký tự thành byte và ngược
lại:

- ASCII: 128 ký tự Latin cơ bản, mỗi ký tự 1 byte. Không có chữ có dấu.
- `latin1`: thêm các ký tự Tây Âu, vẫn 1 byte mỗi ký tự. `latin1` của MySQL thực chất là bảng mã
  Windows cp1252. Không đủ cho tiếng Việt.
- Unicode: gán cho mọi ký tự của mọi ngôn ngữ một số hiệu gọi là *code point*, ví dụ `ệ` là U+1EC7,
  `😀` là U+1F600. UTF-8 là cách mã hoá code point thành 1 tới 4 byte, trong đó ký tự ASCII vẫn chỉ
  tốn 1 byte.

MySQL có hai charset tên "utf8", và đây là cái bẫy lịch sử nổi tiếng:

| Charset MySQL | Byte mỗi ký tự | Chứa được | Trạng thái |
|---|---|---|---|
| `utf8mb4` | 1 tới 4 | Toàn bộ Unicode, gồm cả emoji và các ký tự hiếm ngoài BMP | Khuyến nghị, mặc định từ MySQL 8.0 |
| `utf8mb3` | 1 tới 3 | Chỉ BMP (*Basic Multilingual Plane*, U+0000 tới U+FFFF): không có emoji | Deprecated; còn hỗ trợ suốt dòng 8.0 và 8.4, dự kiến bị bỏ ở bản lớn sau |
| `utf8` | | Là tên khác (alias, đã deprecated) của `utf8mb3` | `SHOW CREATE TABLE` hiển thị thành `utf8mb3` |

```sql
CREATE TABLE t_mb3 (nick VARCHAR(20) CHARACTER SET utf8mb3);
-- Tạo được, kèm warning báo utf8mb3 đã deprecated
INSERT INTO t_mb3 VALUES ('Lan 😀');
-- ERROR 1366 (HY000): Incorrect string value: '\xF0\x9F\x98\x80' for column 'nick' at row 1
```

Emoji cần 4 byte (`f09f9880` như ví dụ PHP ở mục 5.1) nên không vào được cột `utf8mb3`. Quy tắc đơn
giản: luôn dùng `utf8mb4`.

Charset và collation được đặt theo bốn cấp, cấp dưới kế thừa cấp trên nếu không ghi rõ: server,
database, bảng, cột. Mặc định của MySQL 8.4 là charset `utf8mb4` với collation `utf8mb4_0900_ai_ci`.

```sql
CREATE DATABASE shop CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE shop.coupons (
  id    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(200) NOT NULL,                             -- theo mặc định của bảng
  code  VARCHAR(20)  NOT NULL COLLATE utf8mb4_0900_as_cs   -- mã giảm giá phân biệt hoa thường
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

SHOW CREATE TABLE shop.coupons\G   -- xem charset và collation thực tế của từng cột
```

### 6.2 Charset của kết nối

Client gửi câu SQL tới server dưới dạng byte, và server cần biết các byte đó theo bảng mã nào. Ba biến
hệ thống của mỗi kết nối đảm nhiệm việc này:

- `character_set_client`: charset của câu lệnh client gửi lên.
- `character_set_connection` (kèm `collation_connection`): charset server chuyển câu lệnh sang để xử
  lý; `collation_connection` dùng khi so sánh hai literal với nhau. Khi so sánh với một cột, collation
  của cột được ưu tiên.
- `character_set_results`: charset của kết quả trả về client.

`SET NAMES utf8mb4` đặt cả ba biến trên thành `utf8mb4`. Phía PHP, PDO nhận charset trong DSN:

```php
<?php
declare(strict_types=1);

$pdo = new PDO('mysql:host=127.0.0.1;dbname=ch03;charset=utf8mb4', 'root', 'root');
```

Laravel đọc khoá `charset` và `collation` trong `config/database.php` rồi đưa
`NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'` vào câu `SET` chạy khi mở kết nối (tác dụng như
`SET NAMES 'utf8mb4' COLLATE 'utf8mb4_unicode_ci'`).

⚠️ Khai báo sai charset kết nối sinh ra *mojibake* (chữ bị biến dạng). Giả sử kết nối khai là
`latin1` nhưng ứng dụng gửi byte UTF-8: MySQL hiểu mỗi byte là một ký tự `latin1`, nên `ệ` (3 byte)
thành ba ký tự `á»‡`.

```php
<?php
declare(strict_types=1);

// Mô phỏng: byte UTF-8 của 'Việt' bị đọc như Windows-1252 (tức latin1 của MySQL)
var_dump(mb_convert_encoding('Việt', 'UTF-8', 'Windows-1252'));   // in ra: string(10) "Viá»‡t"
```

Lỗi này khó phát hiện: chính ứng dụng đó đọc lại qua cùng kết nối sai thì quá trình chuyển đổi đảo
ngược và chữ trông vẫn đúng. Chỉ khi công cụ khác (đọc bằng `utf8mb4`) mở dữ liệu ra thì mới thấy rác.
Khi đó dữ liệu trên đĩa đã sai, và sửa lại rất vất vả.

### 6.3 Collation: luật so sánh và sắp xếp

Cùng một charset có thể so sánh theo nhiều cách: `'a'` có bằng `'A'` không, `'a'` có bằng `'á'`
không, `'Bình'` đứng trước hay sau `'Bính'`. *Collation* là bộ luật trả lời những câu đó. Mỗi
charset có nhiều collation và một collation mặc định. Collation ảnh hưởng tới `=`, `<`, `LIKE`,
`ORDER BY`, `GROUP BY`, `DISTINCT`, `UNIQUE` và thứ tự trong index.

Đọc tên collation:

| Phần tên | Ý nghĩa |
|---|---|
| `utf8mb4_` | Charset |
| `0900` | Dựa trên Unicode Collation Algorithm (UCA) bản 9.0.0. `utf8mb4_unicode_ci` không ghi số là UCA 4.0.0; `utf8mb4_unicode_520_ci` là UCA 5.2.0 |
| `vi_` (hoặc `tr_`, `de_pb_`...) | Có luật riêng của một ngôn ngữ |
| `ai` / `as` | *Accent-insensitive* / *accent-sensitive*: không phân biệt / phân biệt dấu |
| `ci` / `cs` | *Case-insensitive* / *case-sensitive*: không phân biệt / phân biệt hoa thường |
| `bin` | So sánh nhị phân theo mã ký tự |

Nếu tên không ghi `ai`/`as` thì `ci` ngầm hiểu là `ai`, `cs` ngầm hiểu là `as`. Ví dụ
`utf8mb4_unicode_ci` không phân biệt cả hoa thường lẫn dấu.

Bên trong, UCA gán cho mỗi ký tự một bộ *trọng số* (weight) nhiều cấp: cấp 1 là chữ cái gốc, cấp 2 là
dấu, cấp 3 là hoa hay thường. Trích bảng trọng số chuẩn của Unicode 9.0.0 (DUCET) mà các collation
`utf8mb4_0900_*` dùng:

```
Ký tự  Cấp 1 (chữ gốc)  Cấp 2 (dấu)        Cấp 3 (hoa/thường)
a      1C47             0020               0002
à      1C47             0020 + 0025 (huyền) 0002
â      1C47             0020 + 0027 (mũ)    0002
A      1C47             0020               0008
d      1C8F             0020               0002
đ      1C8F             0020 + 0039 (gạch)  0002
```

So sánh hai chuỗi là so sánh dãy trọng số, và collation quyết định so tới cấp nào:

- `utf8mb4_0900_ai_ci`: chỉ cấp 1. Nên `a`, `à`, `â`, `A` bằng nhau, và cả `đ` cũng bằng `d`.
- `utf8mb4_0900_as_ci`: cấp 1 và 2. `a` bằng `A`, nhưng khác `à`.
- `utf8mb4_0900_as_cs`: cả ba cấp. `a`, `à`, `A` đều khác nhau.
- `utf8mb4_bin`, `utf8mb4_0900_bin`: so theo mã ký tự, phân biệt cả hoa thường lẫn dấu.
  `utf8mb4_0900_bin` so thẳng các byte `utf8mb4` nên nhanh hơn nhiều so với `utf8mb4_bin`, dù thứ tự
  sắp xếp như nhau.

Collation cũ `utf8mb4_general_ci` không cài đặt đầy đủ UCA (không có expansion, contraction) nên nhanh
nhưng kém đúng; tài liệu MySQL cho biết các collation dựa trên UCA 9.0.0 trở lên còn nhanh hơn các
collation UCA đời trước.

### 6.4 Collation và tiếng Việt

Bảng dưới là kết quả của phép `=` dưới bốn collation hay gặp. Kết quả được suy từ bảng trọng số và luật
tiếng Việt trong mã nguồn MySQL 8.4; bạn nên tự chạy để kiểm chứng.

| Phép so sánh | `utf8mb4_0900_ai_ci` (mặc định MySQL) | `utf8mb4_unicode_ci` (mặc định Laravel) | `utf8mb4_vi_0900_ai_ci` | `utf8mb4_0900_as_cs` |
|---|---|---|---|---|
| `'Ha' = 'HÀ'` | 1 | 1 | 1 | 0 |
| `'Ha Noi' = 'Hà Nội'` | 1 | 1 | 0 | 0 |
| `'Da Nang' = 'Đà Nẵng'` | 1 | 0 | 0 | 0 |
| `'a' = 'a '` | 0 | 1 | 0 | 0 |

```sql
SELECT 'Ha Noi' = 'Hà Nội' COLLATE utf8mb4_0900_ai_ci    AS c0900,
       'Ha Noi' = 'Hà Nội' COLLATE utf8mb4_unicode_ci    AS cunicode,
       'Ha Noi' = 'Hà Nội' COLLATE utf8mb4_vi_0900_ai_ci AS cvi,
       'Ha Noi' = 'Hà Nội' COLLATE utf8mb4_0900_as_cs    AS cascs;
-- 1, 1, 0, 0
```

Giải thích từng dòng:

- Dòng 2: trong `utf8mb4_vi_0900_ai_ci`, MySQL áp luật tiếng Việt của CLDR: ă, â, đ, ê, ô, ơ, ư là
  những chữ cái riêng (khác nhau ở cấp 1), chỉ có năm dấu thanh (huyền, hỏi, ngã, sắc, nặng) là khác
  biệt cấp 2. `ộ` là chữ `ô` mang dấu nặng, nên khác `o`. Với collation này, `'Hà Nội' = 'Ha Nôi'` mới
  ra 1.
- Dòng 3: trong UCA 9.0.0, `đ` cùng trọng số cấp 1 với `d` (bảng ở mục 6.3), còn trong UCA 4.0.0 mà
  `utf8mb4_unicode_ci` dùng, `đ` có trọng số cấp 1 riêng. Cùng một câu tìm kiếm "Da Nang" có thể ra
  kết quả khác nhau tuỳ bảng được tạo bằng collation nào.
- Dòng 4: xem mục 6.5.

Hệ quả thực tế:

- Tìm kiếm không dấu gần như "miễn phí" với `utf8mb4_0900_ai_ci`: `WHERE city = 'ha noi'` khớp
  `'Hà Nội'`. `LIKE` cũng so sánh theo collation, từng ký tự một.
- ⚠️ `UNIQUE` dùng cùng luật đó. Với cột `username` dùng `_ai_ci`, `'hoang'` và `'Hoàng'` bị coi là
  trùng nên không thể cùng tồn tại. Có khi đó là điều bạn muốn (chống giả mạo tên), có khi không.
- ⚠️ Thứ tự sắp xếp: `utf8mb4_0900_ai_ci` coi `â` như `a` ở cấp 1, nên `'âm'` đứng trước `'an'` (vì
  m đứng trước n), trong khi theo bảng chữ cái tiếng Việt thì `a < ă < â`, tức `'an'` phải đứng trước
  `'âm'`. Cần sắp xếp đúng kiểu từ điển tiếng Việt thì dùng `utf8mb4_vi_0900_ai_ci`.

### 6.5 Khoảng trắng cuối: PAD SPACE và NO PAD

Mỗi collation có một thuộc tính *pad attribute*:

- `PAD SPACE`: bỏ qua khoảng trắng cuối khi so sánh, nên `'a' = 'a '`. Đây là cách của các collation
  UCA đời trước 9.0.0 như `utf8mb4_unicode_ci`, `utf8mb4_general_ci`, và của `utf8mb4_bin`.
- `NO PAD`: khoảng trắng cuối là một ký tự như mọi ký tự khác, nên `'a' <> 'a '`. Đây là cách của mọi
  collation `_0900_`, gồm cả `utf8mb4_0900_bin`.

```sql
SELECT COLLATION_NAME, PAD_ATTRIBUTE
FROM INFORMATION_SCHEMA.COLLATIONS
WHERE COLLATION_NAME IN ('utf8mb4_0900_ai_ci', 'utf8mb4_unicode_ci', 'utf8mb4_bin');
-- utf8mb4_0900_ai_ci  NO PAD
-- utf8mb4_bin         PAD SPACE
-- utf8mb4_unicode_ci  PAD SPACE
-- (thứ tự dòng có thể khác)
```

SQL mode không ảnh hưởng tới chuyện này. Hệ quả: chuyển một bảng từ `utf8mb4_unicode_ci` sang
`utf8mb4_0900_ai_ci` có thể làm hai giá trị trước đây "trùng" (`'a'`, `'a '`) thành khác nhau, và
ngược lại.

### 6.6 Trộn collation: lỗi và mất index

Khi hai vế của phép so sánh có collation khác nhau, MySQL chọn bên có độ ưu tiên cao hơn theo
*coercibility*: `COLLATE` ghi rõ (0) thắng cột (2), cột thắng literal (4). Vì vậy `WHERE name = 'abc'`
luôn dùng collation của cột `name`, không có vấn đề gì.

Rắc rối nảy sinh khi hai cột cùng là Unicode nhưng khác collation, ví dụ join bảng do migration Laravel
tạo (`utf8mb4_unicode_ci`) với bảng tạo tay theo mặc định server (`utf8mb4_0900_ai_ci`):

```sql
CREATE TABLE a_users  (email VARCHAR(255) COLLATE utf8mb4_unicode_ci);
CREATE TABLE b_orders (email VARCHAR(255) COLLATE utf8mb4_0900_ai_ci);

SELECT * FROM a_users u JOIN b_orders o ON o.email = u.email;
-- ERROR 1267 (HY000): Illegal mix of collations (utf8mb4_0900_ai_ci,IMPLICIT)
--   and (utf8mb4_unicode_ci,IMPLICIT) for operation '='
```

Có thể "chữa cháy" bằng `ON o.email = u.email COLLATE utf8mb4_0900_ai_ci`, nhưng ⚠️ khi phải đổi
collation của một cột để so sánh, MySQL không dùng được index trên cột đó cho việc tra cứu, vì index
được sắp xếp theo collation gốc của cột. Cách sửa gốc là thống nhất một collation cho cả database.

Đổi charset/collation của bảng đang có dữ liệu (`ALTER TABLE ... CONVERT TO CHARACTER SET utf8mb4
COLLATE ...`) cần kiểm tra trước: lệnh có thể phải chép lại cả bảng (bảng lớn thì xem chương 20); các
giá trị trước đây khác nhau có thể thành trùng và làm hỏng `UNIQUE`; thứ tự sắp xếp và kết quả tìm
kiếm của ứng dụng đổi theo.

### 6.7 Chọn charset và collation cho dự án

- Charset: luôn `utf8mb4`.
- Collation: chọn một cho cả database và cho cấu hình kết nối của ứng dụng, đừng để mỗi nơi một kiểu.
  - `utf8mb4_0900_ai_ci`: mặc định của MySQL 8.x, nhanh, `NO PAD`, coi `đ` bằng `d`.
  - `utf8mb4_unicode_ci`: mặc định trong `config/database.php` của Laravel, UCA cũ, `PAD SPACE`. Nếu
    database dùng collation khác, sửa biến môi trường `DB_COLLATION` cho khớp.
  - `utf8mb4_vi_0900_ai_ci`: khi sắp xếp đúng thứ tự chữ cái tiếng Việt là yêu cầu quan trọng.
- Từng cột cần phân biệt hoa thường hay dấu (mã giảm giá, token, mã định danh) thì đặt riêng
  `_0900_as_cs` hoặc `_bin` cho cột đó.

## 7. Chuỗi nhị phân: BINARY, VARBINARY, BLOB

### 7.1 Chuỗi byte khác chuỗi ký tự thế nào

`BINARY`, `VARBINARY` và `BLOB` lưu *chuỗi byte* (binary string) thay vì chuỗi ký tự. Chúng không có
charset theo nghĩa thông thường (charset và collation đều là `binary`), độ dài tính bằng byte, và so
sánh hay sắp xếp theo giá trị số của từng byte. Không có chuyện "không phân biệt hoa thường" hay
"không phân biệt dấu": hai giá trị bằng nhau khi và chỉ khi giống nhau từng byte.

Mỗi kiểu chuỗi ký tự có một kiểu nhị phân tương ứng:

| Chuỗi ký tự | Chuỗi byte | Ghi chú |
|---|---|---|
| `CHAR(n)` | `BINARY(n)` | Độ dài cố định `n` byte, đệm bằng byte `0x00` |
| `VARCHAR(n)` | `VARBINARY(n)` | Độ dài thay đổi, tối đa `n` byte, không đệm |
| `TINYTEXT`, `TEXT`, `MEDIUMTEXT`, `LONGTEXT` | `TINYBLOB`, `BLOB`, `MEDIUMBLOB`, `LONGBLOB` | Cùng giới hạn byte như bên `TEXT` |

⚠️ `BINARY(n)` đệm thêm byte `0x00` cho đủ `n` byte và không cắt chúng khi đọc ra. Ví dụ từ tài liệu
MySQL:

```sql
CREATE TABLE t_bin (c BINARY(3));
INSERT INTO t_bin SET c = 'a';
SELECT HEX(c), c = 'a', c = 'a\0\0' FROM t_bin;
-- 610000   0   1
```

Giá trị lưu là `a` cộng hai byte 0, nên không còn bằng `'a'`. Vì vậy `BINARY(n)` chỉ dành cho giá trị
luôn dài đúng `n` byte (hash, UUID); dữ liệu dài ngắn khác nhau thì dùng `VARBINARY`. Vượt độ dài thì
strict mode báo lỗi như với chuỗi ký tự.

### 7.2 Dùng chuỗi byte vào việc gì

Chuỗi byte hợp với dữ liệu vốn là byte, không phải văn bản cho người đọc:

- Giá trị hash. SHA-256 là 32 byte. Lưu dạng hex trong `CHAR(64)` tốn gấp đôi và phải so sánh theo
  collation; lưu `BINARY(32)` thì gọn và so sánh thẳng từng byte.
- UUID dạng gọn 16 byte (mục 12).
- Địa chỉ IP dạng số: `INET6_ATON()` đổi IPv4 thành 4 byte và IPv6 thành 16 byte, vừa cột
  `VARBINARY(16)` (mục 13).
- Token ngẫu nhiên, khoá đã mã hoá.

Ví dụ hay gặp: cần tra cứu theo URL, mà URL dài tới vài nghìn ký tự nên không index nguyên cột được
(mục 5.5). Lưu thêm hash của nó và đặt `UNIQUE` lên hash:

```sql
CREATE TABLE links (
  id       BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  url      VARCHAR(2048) NOT NULL,
  url_hash BINARY(32) NOT NULL,          -- SHA-256 của url, luôn đúng 32 byte
  UNIQUE KEY uq_links_url_hash (url_hash)
);

-- SHA2() trả về chuỗi hex 64 ký tự; UNHEX() đổi nó thành 32 byte
INSERT INTO links (url, url_hash)
VALUES ('https://example.com/a', UNHEX(SHA2('https://example.com/a', 256)));

SELECT id, url FROM links
WHERE url_hash = UNHEX(SHA2('https://example.com/a', 256));   -- tra bằng index trên url_hash

SELECT HEX(url_hash) FROM links;   -- muốn đọc bằng mắt thì đổi sang hex
-- 2DCE0A4C50441BFCCFA9CAF4B58C3CBA6E06C420505DD829F0436DE1AA44BAAC
```

Phía PHP, `hash()` với tham số thứ ba là `true` trả về byte thô, bind thẳng vào cột `BINARY(32)` được:

```php
<?php
declare(strict_types=1);

$url = 'https://example.com/a';
$raw = hash('sha256', $url, true);   // 32 byte thô, dùng để lưu và tra cứu
var_dump(strlen($raw));              // in ra: int(32)
var_dump(hash('sha256', $url));      // dạng hex để hiển thị hoặc ghi log
// in ra: string(64) "2dce0a4c50441bfccfa9caf4b58c3cba6e06c420505dd829f0436de1aa44baac"
```

Muốn chắc chắn tuyệt đối trước khả năng (cực nhỏ) hai URL khác nhau trùng hash, thêm điều kiện
`AND url = ?` vào câu tra cứu: index trên hash vẫn làm phần việc nặng. Cũng có thể để MySQL tự tính
hash bằng *generated column*, phần đó thuộc chương 04.

### 7.3 BLOB và chuyện lưu file trong database

`BLOB` lưu được ảnh, PDF, file bất kỳ. Nhưng thường không nên đưa file lớn vào database. Cách phổ
biến là lưu file ở object storage (S3 hoặc tương tự) hay hệ thống file, còn database giữ đường dẫn
hoặc khoá của file cùng metadata (kích thước, loại MIME, checksum). Lý do:

- Database phình to, sao lưu và khôi phục chậm theo (chương 21).
- Mỗi lần đọc file là dữ liệu lớn đi qua bộ nhớ đệm của InnoDB, binlog và replication (chương 22),
  chen chỗ của dữ liệu nghiệp vụ.
- Kích thước một lần truyền bị giới hạn bởi `max_allowed_packet`.

`BLOB` vẫn hợp với dữ liệu nhị phân nhỏ cần đi cùng transaction với phần còn lại của dòng, ví dụ một
khoá đã mã hoá hay một ảnh thumbnail rất nhỏ.

## 8. Ngày và giờ

### 8.1 Năm kiểu ngày giờ

| Kiểu | Dạng | Phạm vi | Byte | Dùng cho |
|---|---|---|---|---|
| `DATE` | `'YYYY-MM-DD'` | 1000-01-01 tới 9999-12-31 | 3 | Ngày thuần: ngày sinh, ngày hiệu lực |
| `TIME` | `'hh:mm:ss'` | -838:59:59 tới 838:59:59 | 3 + phần lẻ giây | Giờ trong ngày, khoảng thời gian ngắn |
| `DATETIME` | `'YYYY-MM-DD hh:mm:ss'` | 1000-01-01 00:00:00 tới 9999-12-31 23:59:59 | 5 + phần lẻ giây | Một thời điểm, lưu nguyên như được ghi |
| `TIMESTAMP` | `'YYYY-MM-DD hh:mm:ss'` | 1970-01-01 00:00:01 UTC tới 2038-01-19 03:14:07 UTC | 4 + phần lẻ giây | Một thời điểm, tự quy đổi múi giờ |
| `YEAR` | `YYYY` | 1901 tới 2155, và 0000 | 1 | Năm (năm sản xuất, niên khoá) |

Vài điểm cần biết ngay:

- Viết ngày theo dạng `'YYYY-MM-DD'`, phân cách bằng dấu gạch ngang. Dùng ký tự phân cách khác là
  cú pháp "dễ dãi" đã deprecated và sinh warning. Năm hai chữ số bị đoán: 00 tới 69 thành 2000 tới
  2069, 70 tới 99 thành 1970 tới 1999. Luôn ghi đủ bốn chữ số.
- `TIME` có phạm vi lớn hơn 24 giờ và có số âm vì nó dùng được cho cả khoảng thời gian. ⚠️ Cách viết
  tắt dễ nhầm: `'11:12'` là 11:12:00, nhưng `'1112'` (không có dấu hai chấm) là 00:11:12.
- `YEAR(4)` (có display width) đã deprecated, viết `YEAR` là đủ.
- Với strict mode và `NO_ZERO_DATE`, `NO_ZERO_IN_DATE` (cả hai nằm trong `sql_mode` mặc định), ngày
  không tồn tại và "ngày số không" `'0000-00-00'` đều bị từ chối:

```sql
CREATE TABLE t_date (d DATE);
INSERT INTO t_date VALUES ('2026-02-30');
-- ERROR 1292 (22007): Incorrect date value: '2026-02-30' for column 'd' at row 1
INSERT INTO t_date VALUES ('0000-00-00');
-- ERROR 1292 (22007): Incorrect date value: '0000-00-00' for column 'd' at row 1
```

Dữ liệu cũ từ thời tắt strict mode hay chứa `'0000-00-00'`. Khi gặp, nên chuyển chúng thành `NULL`
(nghĩa là "không biết") thay vì giữ một ngày giả.

### 8.2 Phần lẻ của giây

`TIME`, `DATETIME`, `TIMESTAMP` nhận thêm tham số *fsp* (fractional seconds precision): số chữ số sau
dấu chấm của giây, từ 0 tới 6 (micro giây). Mặc định là 0, khác với chuẩn SQL (mặc định 6), vì lý do
tương thích với MySQL đời cũ.

```sql
CREATE TABLE events (
  id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  happened_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)   -- NOW(6) cũng được
);
```

Phần lẻ giây tốn thêm byte: fsp 1 tới 2 thêm 1 byte, 3 tới 4 thêm 2 byte, 5 tới 6 thêm 3 byte. Nó hữu
ích khi cần sắp xếp các sự kiện xảy ra trong cùng một giây, hoặc đo thời gian xử lý.

Ghi giá trị có nhiều chữ số lẻ hơn fsp của cột thì MySQL làm tròn, không cảnh báo, không báo lỗi (bật
SQL mode `TIME_TRUNCATE_FRACTIONAL` nếu muốn cắt bỏ thay vì làm tròn). Ví dụ từ tài liệu MySQL:
`'17:51:04.777'` ghi vào cột `TIME(2)` thành `17:51:04.78`.

⚠️ Làm tròn có thể đẩy sang ngày, thậm chí năm, khác:

```sql
CREATE TABLE t_round (dt DATETIME);   -- fsp = 0
INSERT INTO t_round VALUES ('2026-12-31 23:59:59.999999');
SELECT dt FROM t_round;
-- 2027-01-01 00:00:00
```

Kiểu bug này xuất hiện khi ứng dụng tính "cuối ngày" là `23:59:59.999999` rồi ghi vào cột không có phần
lẻ giây. Lọc theo khoảng thời gian thì dùng cận dưới đóng, cận trên mở (`>= đầu ngày AND < đầu ngày
hôm sau`), không cần tới "cuối ngày" (mục 8.7).

### 8.3 TIMESTAMP và múi giờ

Đây là khác biệt quan trọng nhất giữa `DATETIME` và `TIMESTAMP`:

- `TIMESTAMP`: khi ghi, MySQL hiểu giá trị theo múi giờ của session hiện tại (biến `time_zone`), đổi
  sang UTC rồi lưu. Khi đọc, đổi từ UTC sang múi giờ của session đang đọc.
- `DATETIME`: không đổi gì cả. Ghi `14:00` thì mọi session đều đọc `14:00`. Ý nghĩa "14:00 ở múi giờ
  nào" nằm hoàn toàn ở ứng dụng.

Thử với hai session (mở hai terminal cùng chạy `docker exec -it my84 mysql -uroot -proot`, rồi
`USE ch03;` ở cả hai):

```sql
CREATE TABLE tz_demo (ts TIMESTAMP, dt DATETIME);
```

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `SET time_zone = '+07:00';` | `SET time_zone = '+00:00';` | Mỗi session một múi giờ |
| 2 | `INSERT INTO tz_demo VALUES ('2026-01-01 14:00:00', '2026-01-01 14:00:00');` | | `ts` được hiểu là 14:00 giờ +07:00, lưu thành 07:00 UTC; `dt` lưu nguyên 14:00 |
| 3 | `SELECT * FROM tz_demo;` | | `ts = 2026-01-01 14:00:00`, `dt = 2026-01-01 14:00:00` |
| 4 | | `SELECT * FROM tz_demo;` | `ts = 2026-01-01 07:00:00`, `dt = 2026-01-01 14:00:00` |

Cùng một dòng, hai session đọc ra hai giá trị `ts` khác nhau, và cả hai đều đúng: chúng là cùng một
thời điểm viết theo hai múi giờ.

Biến `time_zone`:

- Mặc định là `SYSTEM`, tức theo múi giờ của máy chạy MySQL (biến `system_time_zone`).
- Nhận dạng offset như `'+07:00'` (phạm vi `-13:59` tới `+14:00`), hoặc tên múi giờ như
  `'Asia/Ho_Chi_Minh'`. Dùng tên thì database phải được nạp bảng múi giờ (công cụ `mysql_tzinfo_to_sql`);
  thiếu thì MySQL báo `ERROR 1298 (HY000): Unknown or incorrect time zone`. Image Docker chính thức
  của MySQL tự nạp các bảng này khi khởi tạo.
- Đặt riêng cho từng kết nối bằng `SET time_zone = ...`.
- Ảnh hưởng tới `NOW()`, `CURTIME()` và cột `TIMESTAMP`; không ảnh hưởng `UTC_TIMESTAMP()` và các cột
  `DATE`, `TIME`, `DATETIME`.

Từ MySQL 8.0.19 có thể ghi kèm offset vào literal, ví dụ `'2026-01-01 14:00:00+07:00'`, khi chèn vào
cột `TIMESTAMP` hoặc `DATETIME`. Offset chỉ dùng để hiểu giá trị lúc ghi; nó không được lưu lại và
không hiện ra khi đọc.

### 8.4 Bug "lệch 7 tiếng"

Lỗi múi giờ hầu như luôn xảy ra khi ba tầng không thống nhất với nhau:

1. Múi giờ của PHP. Trong Laravel là khoá `timezone` của `config/app.php`, mặc định `'UTC'`.
2. `time_zone` của session MySQL. Laravel chỉ đặt biến này nếu cấu hình kết nối có khoá `timezone`;
   bản `config/database.php` mặc định không có khoá đó, nên session theo mặc định của server.
3. Kiểu cột: `TIMESTAMP` thì có quy đổi, `DATETIME` thì không.

Kịch bản điển hình:

1. Ứng dụng đặt múi giờ `'Asia/Ho_Chi_Minh'`. Lúc 14:00 giờ Việt Nam, nó ghi chuỗi
   `'2026-01-01 14:00:00'`. Chuỗi này không mang thông tin múi giờ.
2. Session MySQL đang ở `+00:00`, cột kiểu `TIMESTAMP`. MySQL hiểu đó là 14:00 UTC và lưu như vậy,
   trong khi thời điểm thật là 07:00 UTC.
3. Ứng dụng đọc lại qua cùng cấu hình thì vẫn thấy 14:00, nên không ai phát hiện. Nhưng một job, một
   công cụ báo cáo hay một ứng dụng khác đặt session `+07:00` sẽ đọc ra 21:00. Dữ liệu đã sai 7 tiếng.

Thêm một bẫy riêng của Eloquent: khi gán một đối tượng Carbon vào thuộc tính ngày giờ, Eloquent định
dạng nó theo múi giờ của chính đối tượng đó, không đổi về múi giờ của ứng dụng. `now('Asia/Ho_Chi_Minh')`
được lưu thành giờ Việt Nam dù ứng dụng chạy UTC. Đoạn PHP thuần sau cho thấy vì sao: chuỗi gửi xuống
database chỉ là các con số, phần múi giờ bị bỏ đi.

```php
<?php
declare(strict_types=1);

$vn = new DateTimeImmutable('2026-01-01 14:00:00', new DateTimeZone('Asia/Ho_Chi_Minh'));

echo $vn->format('Y-m-d H:i:s'), "\n";
// in ra: 2026-01-01 14:00:00   (chuỗi này không nói nó là giờ Việt Nam)
echo $vn->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d H:i:s'), "\n";
// in ra: 2026-01-01 07:00:00   (cùng thời điểm, viết theo UTC)
echo $vn->getTimestamp(), "\n";
// in ra: 1767250800            (số giây kể từ 1970-01-01 00:00:00 UTC, không phụ thuộc múi giờ)
```

Nguyên tắc phòng tránh:

- Ứng dụng chạy UTC, session database đặt UTC (trong Laravel có thể thêm `'timezone' => '+00:00'` vào
  cấu hình kết nối `mysql`), dữ liệu lưu UTC. Chỉ đổi sang giờ người dùng ở tầng hiển thị.
- Trước khi lưu một thời điểm, đưa nó về UTC (`->utc()` với Carbon).
- Sự kiện tương lai gắn với lịch địa phương (lịch hẹn 9:00 sáng giờ Hà Nội năm sau) thì lưu giờ địa
  phương kèm tên múi giờ, vì quy tắc múi giờ của một nơi có thể thay đổi trước ngày đó.

### 8.5 Giới hạn năm 2038

Bên trong, `TIMESTAMP` lưu số giây kể từ 1970-01-01 00:00:00 UTC (*Unix time*) trong 4 byte. Giá trị
lớn nhất là 2^31 - 1 = 2147483647 giây, rơi vào 2038-01-19 03:14:07 UTC:

```php
<?php
declare(strict_types=1);

echo gmdate('Y-m-d H:i:s', 2 ** 31 - 1), "\n";   // in ra: 2038-01-19 03:14:07
```

Sau thời điểm đó cột `TIMESTAMP` không chứa được nữa; strict mode báo lỗi khi ghi giá trị ngoài phạm
vi. Đừng nghĩ còn xa: những giá trị sau đây đã vượt hoặc nằm ngoài phạm vi ngay hôm nay:

- Ngày hết hạn hợp đồng, bảo hành, khoản vay 15 tới 30 năm.
- Ngày sinh trước năm 1970 (`TIMESTAMP` bắt đầu từ 1970-01-01 00:00:01 UTC). Ngày sinh vốn nên là
  `DATE`.

Trên nền 64-bit, các hàm `FROM_UNIXTIME()` và `UNIX_TIMESTAMP()` của MySQL 8.4 đã xử lý được tới năm
3001, nhưng phạm vi của kiểu cột `TIMESTAMP` thì không đổi. Laravel `$table->timestamps()` tạo hai cột
`TIMESTAMP` (`created_at`, `updated_at`), nên ứng dụng sống lâu cần có kế hoạch chuyển sang `DATETIME`
trước 2038.

### 8.6 Giá trị mặc định và tự cập nhật

Cả `TIMESTAMP` và `DATETIME` nhận `DEFAULT CURRENT_TIMESTAMP` (điền thời điểm hiện tại khi chèn mà
không ghi giá trị) và `ON UPDATE CURRENT_TIMESTAMP` (tự cập nhật khi dòng thay đổi):

```sql
CREATE TABLE posts (
  id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  title      VARCHAR(255) NOT NULL,
  created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
);
```

- fsp phải giống nhau trong cả định nghĩa: cột `DATETIME(6)` đi với `CURRENT_TIMESTAMP(6)`.
- `ON UPDATE` chỉ chạy khi có cột khác thật sự đổi giá trị. `UPDATE` gán lại đúng giá trị cũ thì
  `updated_at` giữ nguyên.
- Từ MySQL 8.0.2, biến `explicit_defaults_for_timestamp` mặc định là `ON`: cột `TIMESTAMP` không còn
  tự nhận các thuộc tính "thần kỳ" như ở MySQL 5.x (tự `NOT NULL`, tự điền thời điểm hiện tại khi gán
  `NULL`). Muốn hành vi nào thì khai báo tường minh. (Bản thân biến này đã deprecated.)

Laravel: `$table->timestamps()` tạo `created_at`, `updated_at` kiểu `TIMESTAMP` cho phép `NULL`, và
Eloquent tự điền giá trị từ phía PHP (theo giờ của ứng dụng), không dựa vào `DEFAULT` của database.
Muốn database tự điền thì dùng các modifier `useCurrent()` và `useCurrentOnUpdate()`.

### 8.7 Chọn kiểu nào cho dữ liệu thời gian

| Dữ liệu | Kiểu nên dùng | Lý do |
|---|---|---|
| Thời điểm sự kiện (`created_at`, `paid_at`) | `DATETIME` lưu UTC theo quy ước, hoặc `TIMESTAMP` | `DATETIME` không có giới hạn 2038 và không quy đổi ngầm, nhưng cả đội phải giữ quy ước UTC; `TIMESTAMP` gọn 4 byte, tự quy đổi, nhưng hết hạn năm 2038 |
| Ngày thuần (ngày sinh, ngày lễ, kỳ kế toán) | `DATE` | Không có giờ thì không có chuyện lệch múi giờ |
| Giờ trong ngày (giờ mở cửa) | `TIME` | |
| Khoảng thời gian (thời lượng video, thời gian xử lý) | Số nguyên đơn vị giây hoặc mili giây | `TIME` chỉ tới 838 giờ (khoảng 35 ngày); số nguyên dễ cộng trừ và so sánh |
| Năm | `YEAR` hoặc `SMALLINT` | `YEAR` chỉ từ 1901 tới 2155 |

Khi lọc theo khoảng thời gian, dùng cận dưới đóng và cận trên mở:

```sql
-- Các bài viết tạo trong ngày 2026-01-01 (theo UTC):
SELECT id FROM posts
WHERE created_at >= '2026-01-01' AND created_at < '2026-01-02';

-- Tránh: WHERE DATE(created_at) = '2026-01-01'
--   (bọc cột trong hàm làm MySQL không dùng được index trên created_at, chương 11)
-- Tránh: WHERE created_at BETWEEN '2026-01-01' AND '2026-01-02'
--   (BETWEEN gồm cả hai đầu, nên lấy luôn dòng đúng 2026-01-02 00:00:00 của ngày hôm sau)
```

## 9. BOOLEAN

MySQL không có kiểu đúng/sai thật sự. `BOOL` và `BOOLEAN` chỉ là tên khác của `TINYINT(1)`, còn `TRUE`
và `FALSE` chỉ là tên khác của 1 và 0. Trong ngữ cảnh điều kiện, 0 là sai và mọi số khác 0 là đúng.
Ví dụ từ tài liệu MySQL:

```sql
SELECT IF(2, 'true', 'false');          -- true: 2 khác 0 nên là "đúng"
SELECT IF(2 = TRUE, 'true', 'false');   -- false: TRUE chỉ là 1, mà 2 không bằng 1
```

Hệ quả: một cột "boolean" thật ra chứa được bất kỳ số nào từ -128 tới 127.

```sql
CREATE TABLE flags (id INT PRIMARY KEY, is_active BOOLEAN NOT NULL DEFAULT FALSE);
INSERT INTO flags VALUES (1, 1), (2, 0), (3, 2);   -- dòng 3 do một bug nào đó ghi số 2

SELECT id FROM flags WHERE is_active = TRUE;   -- 1     (bỏ sót dòng 3)
SELECT id FROM flags WHERE is_active;          -- 1, 3
SELECT id FROM flags WHERE is_active IS TRUE;  -- 1, 3
```

Cách dùng an toàn:

- Khai `NOT NULL` kèm `DEFAULT`, để cờ chỉ có hai trạng thái. Cột boolean cho phép `NULL` là ba trạng
  thái (đúng, sai, không biết), thường không phải điều bạn muốn.
- Chặn giá trị lạ bằng `CHECK (is_active IN (0, 1))` (chương 04).
- `TINYINT(1)` là trường hợp ngoại lệ vẫn được hiển thị display width (mục 2.4), chính vì các connector
  dựa vào nó để nhận ra cột boolean.

Phía PHP: từ PHP 8.1, `pdo_mysql` trả cột `TINYINT(1)` về `int` (0 hoặc 1), không phải `bool`. Với
thói quen dùng `===`, đây là chỗ dễ sai:

```php
<?php
declare(strict_types=1);

$row = ['is_active' => 1];              // giá trị PDO trả về từ cột TINYINT(1)
var_dump($row['is_active'] === true);   // in ra: bool(false)
var_dump($row['is_active'] === 1);      // in ra: bool(true)
var_dump((bool) $row['is_active']);     // in ra: bool(true)
```

Laravel: `$table->boolean('is_active')` tạo `tinyint(1)`; khai cast `'is_active' => 'boolean'` trong
model để Eloquent đổi giá trị thành `bool` khi đọc.

## 10. ENUM và SET

### 10.1 ENUM

`ENUM` là kiểu chuỗi chỉ nhận một giá trị trong danh sách khai báo trước:

```sql
CREATE TABLE orders_enum (
  id     BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  status ENUM('pending', 'paid', 'shipped', 'cancelled') NOT NULL DEFAULT 'pending'
);
INSERT INTO orders_enum (status) VALUES ('paid'), ('cancelled'), ('pending');

INSERT INTO orders_enum (status) VALUES ('refunded');
-- ERROR 1265 (01000): Data truncated for column 'status' at row 1
```

Bên trong, MySQL không lưu chuỗi mà lưu *số thứ tự* (index) của giá trị trong danh sách, bắt đầu từ
1: `'pending'` là 1, `'paid'` là 2... Danh sách tới 255 phần tử thì tốn 1 byte, tới 65.535 phần tử thì
2 byte. Gọn hơn `VARCHAR` nhiều, và strict mode tự chặn giá trị lạ. (Khi tắt strict mode, giá trị lạ
bị thay bằng chuỗi rỗng `''` mang index 0, một giá trị "lỗi" đặc biệt.)

Chính việc lưu số thứ tự sinh ra các cái bẫy:

- ⚠️ `ORDER BY status` sắp theo số thứ tự khai báo, không theo chữ cái:

  ```sql
  SELECT status, status + 0 AS idx FROM orders_enum ORDER BY status;
  -- pending   1
  -- paid      2
  -- cancelled 4
  ```

  Muốn sắp theo chữ cái thì `ORDER BY CAST(status AS CHAR)`.
- ⚠️ Đừng dùng số làm giá trị của `ENUM`. Số ghi vào bị hiểu là số thứ tự. Ví dụ từ tài liệu MySQL: với
  cột `ENUM('0','1','2')`, ghi số `2` được giá trị `'1'` (phần tử thứ 2), ghi chuỗi `'2'` được `'2'`, ghi
  chuỗi `'3'` (không khớp phần tử nào) bị hiểu là số thứ tự 3 và thành `'2'`.
- Đổi danh sách là đổi schema, phải `ALTER TABLE`. Thêm phần tử vào cuối danh sách thì làm được tức
  thì (`ALGORITHM=INSTANT`), miễn là số byte lưu trữ không đổi. Chèn vào giữa, đổi thứ tự hay xoá
  phần tử làm số thứ tự của các giá trị cũ thay đổi, nên MySQL phải chép lại cả bảng.
- Danh sách nằm trong schema nên không gắn thêm được thông tin như nhãn hiển thị hay thứ tự hiển thị,
  và mỗi hệ quản trị một kiểu (PostgreSQL có `ENUM` riêng, tạo bằng `CREATE TYPE`).

Laravel: `$table->enum('status', ['pending', 'paid', 'shipped', 'cancelled'])`.

### 10.2 SET

`SET` cho phép một ô chứa không, một hoặc nhiều giá trị trong danh sách khai báo (tối đa 64 phần tử).
MySQL lưu nó dạng bitmap: mỗi phần tử một bit, phần tử đầu là bit thấp nhất.

```sql
CREATE TABLE myset (col SET('a', 'b', 'c', 'd'));
INSERT INTO myset (col) VALUES ('a,d'), ('d,a'), ('a,d,d');
SELECT col FROM myset;
-- a,d   (cả ba dòng: thứ tự và phần tử lặp được chuẩn hoá theo khai báo)

SELECT * FROM myset WHERE FIND_IN_SET('d', col) > 0;   -- tìm các dòng có 'd'
```

`SET` vi phạm tinh thần của dạng chuẩn 1 (chương 02): một ô chứa nhiều giá trị. Tìm "các dòng có phần
tử X" không dùng index thông thường được, thêm phần tử là đổi schema, và giới hạn 64 phần tử. Trong
thiết kế mới, gần như luôn nên thay `SET` bằng một bảng trung gian nhiều-nhiều.

### 10.3 Lựa chọn thay thế ENUM

| Cách | Ưu điểm | Nhược điểm |
|---|---|---|
| `ENUM` | Gọn (1 tới 2 byte), tự chặn giá trị lạ | Sắp theo số thứ tự; đổi danh sách là đổi schema; không gắn được metadata |
| `VARCHAR(20)` + `CHECK (status IN (...))` | Dữ liệu đọc ra dễ hiểu, sắp theo chữ, chuyển sang hệ quản trị khác dễ | Tốn chỗ hơn; đổi danh sách vẫn phải sửa ràng buộc |
| Bảng tra cứu `order_statuses(code PK, label, sort_order)` + khoá ngoại | Thêm giá trị chỉ là một câu `INSERT`; gắn được nhãn, thứ tự, cờ còn dùng | Thêm một bảng, đôi khi thêm một phép join |

Dù chọn cách nào ở database, phía PHP nên dùng *backed enum* (PHP 8.1+) để code không rải rác chuỗi
`'paid'`:

```php
<?php
declare(strict_types=1);

enum OrderStatus: string
{
    case Pending = 'pending';
    case Paid = 'paid';
    case Shipped = 'shipped';
    case Cancelled = 'cancelled';
}

var_dump(OrderStatus::from('paid'));          // in ra: enum(OrderStatus::Paid)
var_dump(OrderStatus::tryFrom('refunded'));   // in ra: NULL
var_dump(OrderStatus::Paid->value);           // in ra: string(4) "paid"
```

Trong model Eloquent, khai cast `'status' => OrderStatus::class` để thuộc tính tự đổi qua lại giữa
chuỗi trong database và enum trong code. Enum PHP bảo vệ code; ràng buộc ở database (`ENUM`, `CHECK`
hay khoá ngoại) bảo vệ dữ liệu khỏi mọi đường ghi khác (script, công cụ quản trị, ứng dụng khác).

## 11. JSON

### 11.1 Kiểu JSON là gì

Từ MySQL 5.7, cột kiểu `JSON` lưu tài liệu JSON (object, mảng, chuỗi, số...). So với việc nhét chuỗi
JSON vào cột `TEXT`, kiểu `JSON` có hai lợi thế:

1. Kiểm tra hợp lệ khi ghi: JSON sai cú pháp bị từ chối.
2. Lưu dạng nhị phân tối ưu: đọc một key hay một phần tử mảng mà không phải phân tích lại cả tài liệu.

```sql
CREATE TABLE products_json (
  id    BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  name  VARCHAR(200) NOT NULL,
  attrs JSON NOT NULL
);
INSERT INTO products_json (name, attrs) VALUES
  ('Áo thun', '{"color": "red", "size": "M", "tags": ["sale", "summer"]}'),
  ('Laptop',  '{"ram_gb": 16, "cpu": "M3"}');

INSERT INTO products_json (name, attrs) VALUES ('Lỗi', '[1, 2,');
-- ERROR 3140 (22032): Invalid JSON text: "Invalid value." at position 6 ...
```

Một số đặc điểm theo tài liệu MySQL 8.4:

- Dung lượng xấp xỉ như `LONGBLOB`/`LONGTEXT` chứa cùng nội dung, cộng thêm phần metadata của định
  dạng nhị phân; kích thước một tài liệu bị giới hạn bởi `max_allowed_packet`. Xem dung lượng thực
  bằng `JSON_STORAGE_SIZE(attrs)`.
- Khi ghi, tài liệu được chuẩn hoá: key trùng thì giữ key cuối cùng, khoảng trắng thừa bị bỏ, key được
  sắp lại để tra nhanh. Đừng dựa vào thứ tự key.
- Chuỗi trong JSON so sánh theo `utf8mb4_bin`, tức phân biệt hoa thường: `JSON_ARRAY('x') = JSON_ARRAY('X')`
  ra 0. Các literal `true`, `false`, `null` phải viết thường.
- Không có giá trị mặc định dạng literal; được dùng biểu thức, ví dụ `DEFAULT (JSON_OBJECT())`.

### 11.2 Đọc giá trị bên trong

Toán tử `->` lấy giá trị JSON theo đường dẫn (tương đương `JSON_EXTRACT()`); `->>` lấy rồi bỏ dấu
nháy, ra chuỗi thường (tương đương `JSON_UNQUOTE(JSON_EXTRACT())`):

```sql
SELECT name, attrs->'$.color' AS color_json, attrs->>'$.color' AS color
FROM products_json;
-- Áo thun   "red"   red
-- Laptop    NULL    NULL      (tài liệu không có key color)

SELECT name FROM products_json WHERE attrs->>'$.color' = 'red';
-- Áo thun   (chạy đúng, nhưng phải quét mọi dòng: chưa có index)
```

MySQL còn cả một bộ hàm JSON (`JSON_OBJECT`, `JSON_SET`, `JSON_CONTAINS`, `JSON_TABLE`...); danh sách
đầy đủ ở mục "JSON Functions" của tài liệu MySQL (xem Đọc thêm).

Cập nhật một phần tài liệu: MySQL có thể sửa tại chỗ (*partial update*) khi bạn dùng `JSON_SET()`,
`JSON_REPLACE()` hoặc `JSON_REMOVE()` trên chính cột đó và giá trị mới không lớn hơn giá trị cũ. Gán cả
tài liệu mới (`SET attrs = '...'`, cũng là cách Eloquent `save()` làm với cột cast `array`) thì ghi lại
toàn bộ.

### 11.3 Index cho dữ liệu JSON

Không index thẳng được một cột `JSON`. Các cách thay thế (chi tiết ở chương 11):

1. Tạo *generated column* (cột tính từ biểu thức) lấy giá trị cần tra, rồi index cột đó:

   ```sql
   ALTER TABLE products_json
     ADD COLUMN color VARCHAR(20) GENERATED ALWAYS AS (attrs->>'$.color') VIRTUAL,
     ADD INDEX idx_color (color);

   SELECT name FROM products_json WHERE color = 'red';   -- dùng được idx_color
   ```

2. *Functional index* trên biểu thức JSON (MySQL 8.0.13+); có bẫy về collation, chương 11 giải thích.
3. *Multi-valued index* cho mảng JSON (MySQL 8.0.17+), dùng với `MEMBER OF()`, `JSON_CONTAINS()`,
   `JSON_OVERLAPS()`.

### 11.4 Khi nào nên dùng JSON

JSON hợp lý khi:

- Thuộc tính khác nhau theo từng loại đối tượng (áo có size, laptop có RAM) và hiếm khi lọc theo.
- Cần lưu nguyên một payload để tra cứu về sau: webhook nhận được, phản hồi của cổng thanh toán.
- Cấu hình, tuỳ chọn cá nhân của người dùng.

Dấu hiệu JSON đang bị dùng thay cho thiết kế: thường xuyên lọc, join hoặc sắp xếp theo một field bên
trong; cần `NOT NULL`, `UNIQUE` hay khoá ngoại cho field đó; cần cập nhật riêng field đó với tần suất
cao. Khi ấy field đó nên là một cột thật. Cột thật có kiểu, có ràng buộc, có index tự nhiên; field trong
JSON thì không có gì trong số đó.

Laravel: `$table->json('attrs')`; cast `'attrs' => 'array'` (hoặc `AsArrayObject`) để làm việc như mảng
PHP; truy vấn bằng cú pháp mũi tên `Product::where('attrs->color', 'red')`. ⚠️ Câu truy vấn đó sinh
biểu thức JSON riêng, không tự dùng index `idx_color` của generated column ở trên; muốn chắc dùng index
thì truy vấn thẳng cột `color`.


## 12. UUID và khoá chính

### 12.1 UUID là gì

*UUID* (Universally Unique Identifier) là một số 128 bit, thường viết thành 36 ký tự gồm 32 chữ số hex
và 4 dấu gạch: `019b785b-2d80-72d3-8970-696016ba80c1`. Nó được thiết kế để nhiều máy sinh độc lập mà
gần như không bao giờ trùng, không cần hỏi database "số tiếp theo là gì". Chuẩn hiện hành là RFC 9562
(thay RFC 4122), định nghĩa nhiều *version*; ba version hay gặp:

| Version | Cấu tạo | Ghi chú |
|---|---|---|
| v1 | Thời gian (chia thành nhiều phần, phần thay đổi nhanh nằm đầu) + số định danh máy | Hàm `UUID()` của MySQL sinh loại này |
| v4 | Gần như toàn bộ là số ngẫu nhiên | Phổ biến nhất; `Str::uuid()` của Laravel |
| v7 | 48 bit đầu là thời gian Unix tính bằng mili giây, phần sau ngẫu nhiên | Tăng dần theo thời gian; `HasUuids` của Laravel từ bản 12 |

Chữ số hex đầu tiên của nhóm thứ ba cho biết version: `...-72d3-...` là v7.

So với `AUTO_INCREMENT`, UUID có lợi khi: id phải sinh ở phía ứng dụng trước khi ghi (gửi đi nơi khác,
tạo nhiều bản ghi liên kết trong một lần), dữ liệu gộp từ nhiều database, hoặc không muốn lộ số
lượng bản ghi qua id tuần tự (`/orders/1042` cho biết bạn mới có khoảng 1042 đơn).

### 12.2 Lưu UUID: CHAR(36) hay BINARY(16)

| Cách lưu | Kích thước | Nhận xét |
|---|---|---|
| `CHAR(36)` | Ít nhất 36 byte mỗi giá trị (charset `utf8mb4`) | Dễ đọc; là kiểu mà `$table->uuid()` của Laravel tạo; so sánh theo collation |
| `BINARY(16)` | 16 byte | Gọn hơn một nửa, so sánh từng byte; phải đổi qua lại khi đọc ghi |

Kích thước đáng quan tâm vì khoá chính được chép vào mọi secondary index và mọi cột khoá ngoại trỏ tới
nó (mục 1.2). MySQL có sẵn hàm đổi qua lại:

```sql
CREATE TABLE customers_uuid (
  id   BINARY(16) PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);

INSERT INTO customers_uuid VALUES
  (UUID_TO_BIN('019b785b-2d80-72d3-8970-696016ba80c1'), 'Lan');

SELECT BIN_TO_UUID(id) AS id, name FROM customers_uuid;
-- 019b785b-2d80-72d3-8970-696016ba80c1   Lan

SELECT name FROM customers_uuid
WHERE id = UUID_TO_BIN('019b785b-2d80-72d3-8970-696016ba80c1');   -- tra bằng khoá chính
```

`UUID_TO_BIN()` và `BIN_TO_UUID()` nhận tham số thứ hai `swap_flag`. Với `swap_flag = 1`, MySQL đổi
chỗ nhóm hex thứ nhất (phần thời gian thay đổi nhanh) và nhóm thứ ba (phần thời gian thay đổi chậm), để
giá trị v1 do `UUID()` sinh ra trở nên gần như tăng dần. Ví dụ từ tài liệu MySQL:

```sql
SET @uuid = '6ccd780c-baba-1026-9564-5b8c656024db';
SELECT HEX(UUID_TO_BIN(@uuid));      -- 6CCD780CBABA102695645B8C656024DB
SELECT HEX(UUID_TO_BIN(@uuid, 1));   -- 1026BABA6CCD780C95645B8C656024DB
```

⚠️ Việc đổi chỗ này chỉ có ích với UUID v1. UUID v7 vốn đã đặt thời gian ở đầu, nên lưu bằng
`UUID_TO_BIN(x)` (không swap); dùng `swap_flag = 1` cho v7 lại phá thứ tự. Và đã ghi với
`swap_flag = 1` thì khi đọc cũng phải `BIN_TO_UUID(id, 1)`, nếu không sẽ ra chuỗi sai.

Phía PHP, đổi chuỗi UUID sang 16 byte chỉ là bỏ dấu gạch rồi `hex2bin()` (ví dụ ở mục 12.4).

### 12.3 Vì sao UUIDv4 làm chậm việc ghi, còn UUIDv7 thì không

InnoDB lưu bảng thành một cây B+tree sắp theo khoá chính (*clustered index*, chương 11 và 16). Mỗi
dòng mới phải được chèn đúng vị trí theo giá trị khoá:

```
Khoá tăng dần (AUTO_INCREMENT, UUIDv7)       Khoá ngẫu nhiên (UUIDv4)

 [page 1][page 2][page 3][page 4] ← ghi     [page 1][page 2][page 3][page 4]
                               ▲               ▲        ▲       ▲      ▲
                  luôn chèn vào page cuối      chèn rải rác khắp cây
```

- Khoá tăng dần: dòng mới luôn đi vào page cuối cùng, page này đang nằm sẵn trong bộ nhớ; page đầy
  thì mở page mới, các page cũ được lấp kín.
- Khoá ngẫu nhiên: mỗi dòng mới rơi vào một page bất kỳ. Khi bảng lớn hơn bộ nhớ đệm (buffer pool),
  nhiều lần ghi phải đọc page từ đĩa lên trước; page giữa cây đầy thì phải tách đôi (*page split*),
  để lại các page chỉ đầy một phần, nên bảng và index tốn chỗ hơn.

UUIDv7 có 48 bit đầu là thời gian, nên các giá trị sinh sau lớn hơn giá trị sinh trước (trong cùng
một mili giây thì thứ tự phụ thuộc phần ngẫu nhiên). Nó giữ được lợi ích của UUID mà vẫn ghi gần như
tuần tự như `AUTO_INCREMENT`. Đây là lý do Laravel đổi `HasUuids` sang sinh UUIDv7 từ bản 12 (muốn giữ
kiểu cũ thì dùng trait `HasVersion4Uuids`). Đổi lại, UUIDv7 để lộ thời điểm tạo bản ghi, điều cần cân
nhắc nếu id được đưa ra ngoài.

### 12.4 Sinh UUIDv7 trong PHP

MySQL 8.4 không có hàm sinh UUIDv7 (hàm `UUID()` sinh v1), nên UUIDv7 thường được sinh ở ứng dụng. Thực
tế bạn dùng thư viện (`Str::uuid7()` của Laravel dựa trên `ramsey/uuid`), nhưng tự viết một lần giúp
thấy rõ cấu tạo:

```php
<?php
declare(strict_types=1);

// UUIDv7 theo RFC 9562: 48 bit thời gian (mili giây Unix), 4 bit version, 2 bit variant, còn lại ngẫu nhiên
function uuid7(int $unixMs): string
{
    $bytes = random_bytes(16);
    $time = str_pad(dechex($unixMs), 12, '0', STR_PAD_LEFT);   // 48 bit = 12 chữ số hex
    $bytes = hex2bin($time) . substr($bytes, 6);
    $bytes[6] = chr((ord($bytes[6]) & 0x0F) | 0x70);           // 4 bit version = 7
    $bytes[8] = chr((ord($bytes[8]) & 0x3F) | 0x80);           // 2 bit variant = 10
    $hex = bin2hex($bytes);
    return sprintf('%s-%s-%s-%s-%s', substr($hex, 0, 8), substr($hex, 8, 4),
        substr($hex, 12, 4), substr($hex, 16, 4), substr($hex, 20));
}

$a = uuid7(1767250800000);   // 2026-01-01 07:00:00.000 UTC
$b = uuid7(1767250800001);   // 1 mili giây sau
echo $a, "\n";               // in ra (phần sau ngẫu nhiên): 019b785b-2d80-72d3-8970-696016ba80c1
var_dump(strcmp($a, $b) < 0);                       // in ra: bool(true): sinh sau thì lớn hơn
var_dump(strlen(hex2bin(str_replace('-', '', $a)))); // in ra: int(16): dạng để lưu BINARY(16)
```

Mười hai chữ số hex đầu (`019b785b2d80`) chính là 1767250800000 mili giây; mỗi lần chạy, phần sau thay
đổi nhưng phần đầu thì không.

### 12.5 Chọn kiểu khoá chính

| Lựa chọn | Kích thước | Ghi tuần tự | Sinh ở ứng dụng | Ghi chú |
|---|---|---|---|---|
| `BIGINT UNSIGNED AUTO_INCREMENT` | 8 byte | Có | Không | Mặc định hợp lý cho đa số bảng (`$table->id()`) |
| UUIDv4 trong `BINARY(16)` | 16 byte | Không | Có | Ghi chậm dần khi bảng lớn; tránh làm khoá chính của bảng lớn |
| UUIDv7 trong `BINARY(16)` | 16 byte | Gần như có | Có | Lộ thời điểm tạo |
| UUID trong `CHAR(36)` | Ít nhất 36 byte | Tuỳ version | Có | Dễ đọc, tốn chỗ; là mặc định của Laravel `uuid()` |
| ULID trong `CHAR(26)` | Ít nhất 26 byte | Gần như có | Có | 48 bit thời gian + 80 bit ngẫu nhiên, mã hoá base32 thành 26 ký tự; `HasUlids`, `$table->ulid()` của Laravel |

Một cách kết hợp hay gặp: khoá chính `BIGINT AUTO_INCREMENT` dùng nội bộ cho join, cộng một cột
`public_id BINARY(16)` có `UNIQUE` (UUIDv7) để đưa ra URL và API.

## 13. Chọn kiểu nhỏ nhất mà đủ dùng

### 13.1 Nguyên tắc

"Nhỏ nhất mà đủ dùng" có hai vế, và vế thứ hai quan trọng không kém:

1. Nhỏ nhất: dòng nhỏ thì nhiều dòng trên một page, cache được nhiều hơn, index gọn hơn (mục 1.2).
2. Đủ dùng: cho cả vòng đời dữ liệu, không chỉ dữ liệu hôm nay. Tiết kiệm 4 byte bằng `INT` cho khoá
   chính rồi phải đổi sang `BIGINT` trên bảng một tỉ dòng là một cuộc di chuyển dữ liệu tốn kém
   (chương 20); tiết kiệm 1 byte bằng `TINYINT` cho một số đếm có thể vượt 127 là một bug chờ xảy ra.

Thứ tự ưu tiên khi chọn: đúng ngữ nghĩa trước (tiền thì `DECIMAL` hoặc số nguyên, thời điểm thì kiểu
ngày giờ, không lưu số hay ngày trong chuỗi), rồi đủ phạm vi, rồi mới tới nhỏ gọn.

### 13.2 Bảng gợi ý cho các trường hay gặp

| Trường | Kiểu gợi ý | Ghi chú |
|---|---|---|
| Khoá chính | `BIGINT UNSIGNED AUTO_INCREMENT` | Mục 2.5, 12.5 |
| Khoá ngoại | Cùng kiểu với cột được trỏ tới | Mục 2.5 |
| Tiền | `DECIMAL(19,4)` hoặc `BIGINT` đơn vị nhỏ nhất, kèm `currency CHAR(3)` | Mục 4.4 |
| Số lượng, tồn kho | `INT UNSIGNED` hoặc `SMALLINT UNSIGNED` tuỳ phạm vi | Mục 2.1 |
| Phần trăm, tỉ lệ cần chính xác | `DECIMAL(5,2)` (0.00 tới 100.00, nếu cho phép tới 999.99 cũng vừa) | |
| Cờ đúng/sai | `BOOLEAN NOT NULL DEFAULT FALSE` | Mục 9 |
| Trạng thái | `ENUM`, `VARCHAR` + `CHECK`, hoặc bảng tra cứu | Mục 10.3 |
| Họ tên | `VARCHAR(100)` | |
| Email | `VARCHAR(255)` | Collation `_ci` để không phân biệt hoa thường |
| Số điện thoại | `VARCHAR(20)` | Mục 13.3 |
| Mã quốc gia, mã tiền tệ | `CHAR(2)`, `CHAR(3)` | |
| Mật khẩu đã băm | `VARCHAR(255)` | Kết quả `password_hash()` của PHP có độ dài tuỳ thuật toán |
| Hash, token cố định độ dài | `BINARY(n)` | Mục 7.2 |
| Địa chỉ IP | `VARBINARY(16)` với `INET6_ATON()` | Mục 13.3 |
| Thời điểm | `DATETIME` (UTC) hoặc `TIMESTAMP` | Mục 8.7 |
| Ngày sinh | `DATE` | |
| Nội dung dài | `TEXT` / `MEDIUMTEXT` | Mục 5.4 |
| Thuộc tính linh hoạt | `JSON` | Mục 11.4 |

### 13.3 Hai trường hợp hay chọn sai

Số điện thoại, mã bưu chính, số CMND/CCCD trông như số nhưng không phải số: không ai cộng hai số điện
thoại. Lưu bằng kiểu số sẽ mất số 0 ở đầu (`0912345678` thành `912345678`), không chứa được `+84` hay
dấu cách. Hãy lưu bằng `VARCHAR`. ⚠️ Khi đã lưu bằng `VARCHAR`, so sánh cũng phải dùng chuỗi:

```sql
CREATE TABLE contacts (id INT PRIMARY KEY, phone VARCHAR(20), INDEX idx_phone (phone));
INSERT INTO contacts VALUES (1, '0912345678');

SELECT id FROM contacts WHERE phone = '0912345678';   -- so sánh chuỗi, dùng được idx_phone
SELECT id FROM contacts WHERE phone = 912345678;      -- vẫn ra 1, nhưng...
```

Câu thứ hai so sánh một chuỗi với một số, nên MySQL đổi cả hai vế sang số thực rồi so sánh: `'0912345678'`
thành 912345678 và "khớp". Tài liệu MySQL nêu rõ trường hợp này index trên cột chuỗi không dùng được để
tra cứu, vì rất nhiều chuỗi khác nhau (`'912345678'`, `' 912345678'`, `'0912345678'`...) cùng đổi ra một
số. Bảng lớn sẽ bị quét toàn bộ. Trong PHP, bind tham số kiểu chuỗi cho cột chuỗi.

Địa chỉ IP: lưu dạng chuỗi `VARCHAR(45)` (kiểu mà `$table->ipAddress()` của Laravel tạo) là đơn giản và
đủ cho đa số trường hợp. Khi cần gọn hoặc cần so sánh theo dải địa chỉ, lưu dạng số trong `VARBINARY(16)`:
`INET6_ATON()` trả về 4 byte cho IPv4 và 16 byte cho IPv6, `INET6_NTOA()` đổi ngược lại.

```sql
SELECT HEX(INET6_ATON('10.0.5.9'));                   -- 0A000509 (4 byte)
SELECT HEX(INET6_ATON('fdfe::5a55:caff:fefa:9089'));  -- FDFE0000000000005A55CAFFFEFA9089 (16 byte)
```

## 14. Đối chiếu PostgreSQL

PostgreSQL 18 có nhiều kiểu tương đương, nhưng khác ở vài điểm quan trọng. (Đi sâu hơn ở chương 25.)

| Nhu cầu | MySQL 8.4 | PostgreSQL 18 | Khác biệt đáng nhớ |
|---|---|---|---|
| Số nguyên | `TINYINT` tới `BIGINT`, có `UNSIGNED` | `smallint`, `integer`, `bigint` | Postgres không có `TINYINT`, `MEDIUMINT`, không có `UNSIGNED`; dùng `CHECK (x >= 0)` |
| Số thực | `FLOAT`, `DOUBLE` | `real` (khoảng 6 chữ số), `double precision` (khoảng 15 chữ số) | Cùng IEEE 754, cùng sai số |
| Số chính xác | `DECIMAL(M,D)`, tối đa 65 chữ số | `numeric(p,s)` (= `decimal`) | `numeric` không khai `p` cho phép tới 131072 chữ số trước dấu phẩy; tính toán chậm hơn số nguyên rất nhiều |
| Chuỗi | `CHAR`, `VARCHAR(n)`, `TEXT` (nhiều cỡ) | `char(n)`, `varchar(n)`, `text` | Tài liệu Postgres: ba kiểu không khác nhau về hiệu năng (`char(n)` thường chậm nhất vì tốn chỗ), nên dùng `text` hoặc `varchar` |
| Nhị phân | `BINARY`, `VARBINARY`, `BLOB` | `bytea` | |
| Ngày giờ | `DATETIME`, `TIMESTAMP` (tới 2038) | `timestamp` (không múi giờ), `timestamptz` | Cả hai 8 byte, từ 4713 TCN tới năm 294276, độ chính xác micro giây; không có giới hạn 2038 |
| Đúng/sai | `TINYINT(1)` | `boolean` thật (1 byte) | `WHERE flag` trên `boolean` không có chuyện giá trị 2 |
| Tập giá trị | `ENUM(...)` trong cột | `CREATE TYPE status AS ENUM (...)` | Enum là một kiểu riêng, dùng chung nhiều bảng |
| JSON | `JSON` (nhị phân) | `json` (giữ nguyên văn bản), `jsonb` (nhị phân, index bằng GIN) | Postgres khuyên dùng `jsonb` cho đa số ứng dụng |
| UUID | Không có kiểu riêng; `BINARY(16)` hoặc `CHAR(36)` | `uuid` (128 bit) | Có sẵn `gen_random_uuid()`/`uuidv4()` và `uuidv7()` |

Ba điểm cần hiểu kỹ:

1. **`timestamptz` không lưu múi giờ.** Tên gọi dễ gây hiểu lầm: giá trị có ghi múi giờ trong chuỗi
   nhập thì được đổi sang UTC, không ghi thì hiểu theo tham số `TimeZone` của session; lưu bên trong
   luôn là UTC và múi giờ gốc không được giữ. Khi xuất ra, giá trị được đổi sang `TimeZone` của session.
   Tức là nó giống `TIMESTAMP` của MySQL về cơ chế, nhưng không có giới hạn 2038. Cộng đồng Postgres
   khuyên dùng `timestamptz` cho thời điểm, thay vì `timestamp` không múi giờ.

   ```sql
   -- PostgreSQL
   SET TIME ZONE 'Asia/Ho_Chi_Minh';
   SELECT '2026-01-01 14:00:00+07'::timestamptz;   -- 2026-01-01 14:00:00+07
   SET TIME ZONE 'UTC';
   SELECT '2026-01-01 14:00:00+07'::timestamptz;   -- 2026-01-01 07:00:00+00
   ```

2. **`text` là lựa chọn bình thường.** Trong MySQL, `TEXT` có nhiều hạn chế (không có default literal,
   index phải dùng tiền tố); trong Postgres, `text` và `varchar` như nhau về hiệu năng. Muốn giới hạn độ
   dài thì `varchar(n)` hoặc `CHECK (length(x) <= n)`.
3. **`jsonb` so với `json`.** `json` giữ nguyên văn bản (khoảng trắng, thứ tự key, key trùng) và phải
   phân tích lại mỗi lần xử lý; `jsonb` lưu dạng nhị phân đã phân rã, ghi chậm hơn một chút nhưng xử lý
   nhanh hơn nhiều, bỏ khoảng trắng, không giữ thứ tự key, key trùng chỉ giữ giá trị cuối, và index được.
   `JSON` của MySQL gần với `jsonb` hơn.


## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Tắt strict mode (`'strict' => false` trong Laravel) để hết lỗi | Dữ liệu sai được "điều chỉnh" và ghi im lặng | Giữ strict mode; sửa câu lệnh hoặc chỉnh từng chế độ bằng `'modes'` (mục 1.3) |
| Dùng `INSERT IGNORE` để bỏ qua dòng trùng | Nuốt luôn lỗi kiểu dữ liệu: số bị kẹp, chuỗi bị cắt | Dùng `INSERT ... ON DUPLICATE KEY UPDATE` hoặc kiểm tra trước (mục 1.3) |
| Khoá chính `INT` cho bảng tăng nhanh | Hết số, `INSERT` báo lỗi trùng khoá | `BIGINT UNSIGNED` (mục 2.5) |
| `WHERE stock - 5 >= 0` trên cột `UNSIGNED` | Phép trừ không dấu ra âm thì lỗi 1690 | `WHERE stock >= 5` (mục 2.3) |
| Nghĩ `INT(11)` giới hạn 11 chữ số | Đó là display width, đã deprecated | Bỏ con số, định dạng ở ứng dụng (mục 2.4) |
| Lưu tiền bằng `FLOAT`/`DOUBLE` | Sai số nhị phân, so sánh bằng không tin được | `DECIMAL` hoặc số nguyên đơn vị nhỏ nhất (mục 3, 4.4) |
| Khai `DECIMAL` không ghi `(M,D)` | Mặc định `DECIMAL(10,0)`, mất phần lẻ | Luôn ghi rõ `M` và `D` (mục 4.1) |
| Ép giá trị `DECIMAL` sang `float` trong PHP | Mất chính xác | Giữ chuỗi, tính bằng bcmath / `BcMath\Number` (mục 4.5) |
| Dùng charset `utf8` | Thực chất là `utf8mb3`, không chứa emoji | `utf8mb4` (mục 6.1) |
| Không khai charset kết nối | Mojibake, dữ liệu sai trên đĩa | `charset=utf8mb4` trong DSN (mục 6.2) |
| Bảng Laravel và bảng tạo tay khác collation | Lỗi 1267 khi join, hoặc mất index | Thống nhất một collation cho cả database (mục 6.6) |
| Quên rằng `_ai_ci` coi `'Hà'` bằng `'Ha'` | `UNIQUE` báo trùng bất ngờ, tìm kiếm khớp rộng | Chọn collation có chủ đích, đặt riêng cho cột cần phân biệt (mục 6.4) |
| `BINARY(n)` cho dữ liệu dài ngắn khác nhau | Bị đệm `0x00`, so sánh không khớp | `VARBINARY(n)` (mục 7.1) |
| Ghi giờ địa phương vào `TIMESTAMP`/`DATETIME` khi session ở múi giờ khác | Lệch giờ, chỉ lộ ra ở công cụ khác | UTC ở cả ba tầng (mục 8.4) |
| Dùng `TIMESTAMP` cho ngày hết hạn xa, ngày sinh | Ngoài phạm vi 1970 tới 2038 | `DATETIME`, `DATE` (mục 8.5) |
| `WHERE DATE(created_at) = ...` hoặc `BETWEEN` ngày | Mất index; đếm trùng mốc nửa đêm | `>= đầu ngày AND < đầu ngày hôm sau` (mục 8.7) |
| `WHERE is_active = TRUE` | Bỏ sót giá trị khác 1 | `WHERE is_active`, thêm `CHECK` (mục 9) |
| So sánh `=== true` với giá trị PDO từ `TINYINT(1)` | PDO trả `int` | Cast `boolean` hoặc so `=== 1` (mục 9) |
| Dùng số làm giá trị `ENUM`, `ORDER BY` cột `ENUM` | Số bị hiểu là số thứ tự; sắp theo thứ tự khai báo | Giá trị chữ; `CAST(... AS CHAR)` khi cần sắp chữ cái (mục 10.1) |
| Lọc thường xuyên theo field trong `JSON` | Không có index, không có ràng buộc | Đưa field thành cột thật hoặc generated column có index (mục 11) |
| UUIDv4 làm khoá chính của bảng lớn, lưu `CHAR(36)` | Ghi ngẫu nhiên vào B+tree, index phình | UUIDv7 trong `BINARY(16)`, hoặc `BIGINT` + `public_id` (mục 12) |
| `swap_flag = 1` cho UUIDv7 | Phá thứ tự thời gian | Chỉ dùng swap cho UUID v1 (mục 12.2) |
| Lưu số điện thoại bằng kiểu số, hoặc so sánh cột chuỗi với số | Mất số 0 đầu; mất index | `VARCHAR`, bind tham số dạng chuỗi (mục 13.3) |

## Tóm tắt chương

- Kiểu dữ liệu là ràng buộc đầu tiên của cột: quyết định giá trị hợp lệ, dung lượng, cách so sánh. Strict
  mode (mặc định) biến giá trị sai thành lỗi thay vì âm thầm sửa; đừng tắt nó.
- Số nguyên chọn theo phạm vi cả vòng đời; khoá chính dùng `BIGINT UNSIGNED`. `UNSIGNED` có bẫy ở phép
  trừ. Số trong `INT(11)` không giới hạn gì.
- `FLOAT`/`DOUBLE` là số xấp xỉ, không so sánh bằng, không dùng cho tiền. Tiền dùng `DECIMAL(M,D)` (ghi
  rõ `M`, `D`) hoặc số nguyên đơn vị nhỏ nhất, kèm mã tiền tệ; phía PHP giữ dạng chuỗi và tính bằng bcmath.
- `VARCHAR(n)` đếm ký tự, nhưng giới hạn dòng, index, `TEXT` tính bằng byte. `TEXT` cho nội dung dài,
  không tra theo nguyên giá trị.
- Luôn `utf8mb4`. Collation quyết định so sánh hoa thường, có dấu, khoảng trắng cuối và thứ tự sắp xếp;
  `utf8mb4_0900_ai_ci`, `utf8mb4_unicode_ci`, `utf8mb4_vi_0900_ai_ci` cho kết quả khác nhau với tiếng
  Việt. Thống nhất một collation cho cả database và kết nối.
- `BINARY`/`VARBINARY` cho dữ liệu vốn là byte: hash, UUID, IP. File lớn để ngoài database.
- `TIMESTAMP` quy đổi theo `time_zone` của session và hết hạn năm 2038; `DATETIME` lưu nguyên. Giữ UTC ở
  ứng dụng, session và dữ liệu. Phần lẻ giây được làm tròn, có thể nhảy sang ngày sau.
- `BOOLEAN` là `TINYINT(1)`; `ENUM` lưu số thứ tự (sắp theo thứ tự khai báo); `SET` hầu như nên thay bằng
  bảng trung gian; `JSON` cho dữ liệu bán cấu trúc ít lọc theo.
- UUID lưu `BINARY(16)`; UUIDv7 ghi gần tuần tự nên hợp làm khoá hơn UUIDv4.
- PostgreSQL: không có `UNSIGNED`, có `boolean`, `uuid`, `timestamptz` (không giới hạn 2038), `jsonb`,
  và `text` là lựa chọn bình thường.

## Câu hỏi tự kiểm tra

1. Ghi số 300 vào cột `TINYINT UNSIGNED` khi bật và khi tắt strict mode thì chuyện gì xảy ra? `INSERT
   IGNORE` thay đổi điều đó thế nào? (mục 1.3)
2. Vì sao `SELECT CAST(0 AS UNSIGNED) - 1` báo lỗi, và viết lại điều kiện `WHERE stock - 5 >= 0` thế nào
   cho đúng? (mục 2.3)
3. Vì sao `SELECT 0.1 + 0.2 = 0.3` trong MySQL ra 1, còn `SELECT 0.1E0 + 0.2E0 = 0.3E0` ra 0?
4. Ghi `19.995` vào cột `DECIMAL(5,2)` được giá trị gì, có lỗi không? Ghi `1000` thì sao? (mục 4.2)
5. Cột `VARCHAR(255)` dùng `utf8mb4` tối đa bao nhiêu byte, và vì sao con số đó quan trọng với index?
6. Với dữ liệu tiếng Việt, khác biệt giữa `utf8mb4_0900_ai_ci`, `utf8mb4_unicode_ci` và
   `utf8mb4_vi_0900_ai_ci` là gì? Cho một ví dụ mỗi collation cho kết quả khác. (mục 6.4)
7. Mô tả chuỗi sự kiện dẫn tới dữ liệu lệch 7 tiếng khi ứng dụng chạy giờ Việt Nam còn session MySQL ở
   UTC. (mục 8.4)
8. Vì sao `WHERE is_active = TRUE` có thể bỏ sót dòng, và PDO trả cột `TINYINT(1)` về kiểu gì?
9. Vì sao UUIDv4 làm khoá chính khiến việc ghi chậm dần khi bảng lớn, còn UUIDv7 thì không? Tại sao
   không dùng `swap_flag = 1` với UUIDv7? (mục 12.2, 12.3)
10. `timestamptz` của PostgreSQL có lưu múi giờ không? Nó giống và khác `TIMESTAMP` của MySQL ở đâu?

## Bài tập

1. **Thiết kế bảng.** Viết `CREATE TABLE` cho bảng `orders` của một cửa hàng bán cả VND lẫn USD, gồm:
   khoá chính, mã đơn công khai không đoán được, khách hàng (khoá ngoại tới `users.id` do `$table->id()`
   tạo), tổng tiền, mã tiền tệ, trạng thái, ghi chú của khách (có thể dài), thời điểm tạo và thanh toán
   (micro giây), địa chỉ IP người đặt. Với mỗi cột, ghi một dòng chú thích giải thích vì sao chọn kiểu đó.
   Chạy trên MySQL 8.4, rồi thử chèn các giá trị sai (tiền âm, trạng thái lạ, ngày 2026-02-30) và ghi lại
   lỗi nhận được.
2. **Thí nghiệm collation.** Tạo bảng `cities(name VARCHAR(100))` ba lần với ba collation
   `utf8mb4_0900_ai_ci`, `utf8mb4_unicode_ci`, `utf8mb4_vi_0900_ai_ci`. Chèn các tên: Hà Nội, Ha Noi,
   Đà Nẵng, Da Nang, Huế, Hue, An Giang, Âu Cơ. Với mỗi bảng: chạy `ORDER BY name`, tìm `WHERE name =
   'da nang'`, và thử thêm `UNIQUE (name)`. Lập bảng so sánh kết quả và giải thích bằng trọng số ở mục 6.3.
3. **Script PHP về tiền.** Viết script PHP (`declare(strict_types=1);`) nhận một danh sách giá dạng chuỗi
   như PDO trả về từ cột `DECIMAL(15,2)`, tính tổng, thuế 8% làm tròn tới 2 chữ số theo half up, và tổng
   sau thuế, bằng hai cách: `float` và bcmath (hoặc `BcMath\Number` nếu dùng PHP 8.4+). Tìm một bộ dữ liệu
   làm hai cách cho kết quả khác nhau. Chạy bằng `docker run --rm -v "$PWD":/app -w /app php:8.5-cli php
   money.php`.
4. **Múi giờ.** Làm lại timeline ở mục 8.3 với hai session, rồi thêm: session A chèn
   `'2026-01-01 14:00:00+07:00'` vào cả cột `TIMESTAMP` và `DATETIME`; cả hai session đọc lại. Giải thích
   từng giá trị đọc được, và đề xuất cấu hình (PHP, Laravel, session MySQL) để tránh lệch giờ.

## Đọc thêm

- MySQL 8.4 Reference Manual, chương [Data Types](https://dev.mysql.com/doc/refman/8.4/en/data-types.html),
  đặc biệt: [Integer Types](https://dev.mysql.com/doc/refman/8.4/en/integer-types.html),
  [Numeric Type Attributes](https://dev.mysql.com/doc/refman/8.4/en/numeric-type-attributes.html),
  [Out-of-Range and Overflow Handling](https://dev.mysql.com/doc/refman/8.4/en/out-of-range-and-overflow.html),
  [Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html),
  [Floating-Point Types](https://dev.mysql.com/doc/refman/8.4/en/floating-point-types.html),
  [The CHAR and VARCHAR Types](https://dev.mysql.com/doc/refman/8.4/en/char.html),
  [The BINARY and VARBINARY Types](https://dev.mysql.com/doc/refman/8.4/en/binary-varbinary.html),
  [The BLOB and TEXT Types](https://dev.mysql.com/doc/refman/8.4/en/blob.html),
  [The ENUM Type](https://dev.mysql.com/doc/refman/8.4/en/enum.html),
  [The SET Type](https://dev.mysql.com/doc/refman/8.4/en/set.html),
  [The DATE, DATETIME, and TIMESTAMP Types](https://dev.mysql.com/doc/refman/8.4/en/datetime.html),
  [Fractional Seconds](https://dev.mysql.com/doc/refman/8.4/en/fractional-seconds.html),
  [Automatic Initialization and Updating for TIMESTAMP and DATETIME](https://dev.mysql.com/doc/refman/8.4/en/timestamp-initialization.html),
  [The JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html),
  [Data Type Default Values](https://dev.mysql.com/doc/refman/8.4/en/data-type-defaults.html),
  [Data Type Storage Requirements](https://dev.mysql.com/doc/refman/8.4/en/storage-requirements.html).
- MySQL 8.4: [Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html),
  [Precision Math](https://dev.mysql.com/doc/refman/8.4/en/precision-math.html),
  [Problems with Floating-Point Values](https://dev.mysql.com/doc/refman/8.4/en/problems-with-float.html),
  [Type Conversion in Expression Evaluation](https://dev.mysql.com/doc/refman/8.4/en/type-conversion.html),
  [Unicode Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html),
  [Collation Naming Conventions](https://dev.mysql.com/doc/refman/8.4/en/charset-collation-names.html),
  [Collation Coercibility](https://dev.mysql.com/doc/refman/8.4/en/charset-collation-coercibility.html),
  [Connection Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-connection.html),
  [Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html),
  [Miscellaneous Functions (UUID, INET6_ATON)](https://dev.mysql.com/doc/refman/8.4/en/miscellaneous-functions.html),
  [JSON Functions](https://dev.mysql.com/doc/refman/8.4/en/json-functions.html),
  [InnoDB Limits](https://dev.mysql.com/doc/refman/8.4/en/innodb-limits.html),
  [Limits on Table Column Count and Row Size](https://dev.mysql.com/doc/refman/8.4/en/column-count-limit.html).
- Mã nguồn MySQL 8.4: [strings/ctype-uca.cc](https://github.com/mysql/mysql-server/blob/8.4/strings/ctype-uca.cc)
  (luật collation tiếng Việt `vi_cldr_30`); bảng trọng số Unicode [DUCET 9.0.0](https://www.unicode.org/Public/UCA/9.0.0/allkeys.txt).
- [RFC 9562: Universally Unique IDentifiers (UUIDs)](https://www.rfc-editor.org/rfc/rfc9562).
- PHP: [BCMath](https://www.php.net/manual/en/book.bc.php), [Floating point numbers](https://www.php.net/manual/en/language.types.float.php),
  [php-src UPGRADING 8.1](https://github.com/php/php-src/blob/PHP-8.1/UPGRADING) (PDO MySQL trả số về kiểu gốc).
- Laravel 13: [Migrations: Available Column Types](https://laravel.com/docs/13.x/migrations#available-column-types),
  [Eloquent: Mutators & Casting](https://laravel.com/docs/13.x/eloquent-mutators),
  [Upgrade Guide 12.x: Models and UUIDv7](https://laravel.com/docs/12.x/upgrade#models-and-uuidv7).
- PostgreSQL 18: [Numeric Types](https://www.postgresql.org/docs/18/datatype-numeric.html),
  [Character Types](https://www.postgresql.org/docs/18/datatype-character.html),
  [Date/Time Types](https://www.postgresql.org/docs/18/datatype-datetime.html),
  [JSON Types](https://www.postgresql.org/docs/18/datatype-json.html),
  [UUID Type](https://www.postgresql.org/docs/18/datatype-uuid.html),
  [UUID Functions](https://www.postgresql.org/docs/18/functions-uuid.html);
  [PostgreSQL wiki: Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This).
