# Chương 04. Tạo và thay đổi bảng: DDL và ràng buộc

> [← Mục lục](README.md) · [← Chương 03: Kiểu dữ liệu](03-kieu-du-lieu.md) · [Chương 05: Thao tác dữ liệu: INSERT, UPDATE, DELETE và SELECT cơ bản →](05-select-co-ban.md)

**Bạn sẽ học được:**

- Tạo database và bảng bằng `CREATE DATABASE`, `CREATE TABLE`; chọn storage engine, charset,
  collation và hiểu chúng được kế thừa từ đâu xuống đâu.
- Khai báo các ràng buộc `NOT NULL`, `DEFAULT`, `UNIQUE`, `PRIMARY KEY`, `FOREIGN KEY`, `CHECK`, và
  biết MySQL phản ứng thế nào khi dữ liệu vi phạm.
- Dùng `AUTO_INCREMENT` và *generated column* đúng cách, hiểu vì sao dãy id luôn có "lỗ".
- Sửa cấu trúc bảng bằng `ALTER TABLE`; phân biệt `DROP`, `TRUNCATE` và `DELETE`.
- Hiểu vì sao DDL trong MySQL tự commit transaction đang mở, khi nào dùng *temporary table*, và cách
  đọc metadata của schema trong `information_schema`.

**Cần biết trước:** [Chương 01](01-database-la-gi.md) (kết nối bằng `mysql` client, các nhóm lệnh
SQL), [Chương 02](02-mo-hinh-quan-he-thiet-ke.md) (khoá chính, khoá ngoại, quan hệ 1-n),
[Chương 03](03-kieu-du-lieu.md) (kiểu dữ liệu, charset và collation).

## 1. DDL là gì và chuẩn bị môi trường

### 1.1 Định nghĩa cấu trúc trước, đổ dữ liệu sau

Database quan hệ lưu dữ liệu trong bảng. Trước khi có dòng dữ liệu nào, bạn phải nói cho database
biết: bảng tên gì, có những cột nào, mỗi cột kiểu gì, và dữ liệu phải tuân theo những luật nào. Bản
mô tả đó gọi là *schema* (lược đồ). Nhóm lệnh SQL dùng để tạo, sửa và xoá schema gọi là *DDL*
(*Data Definition Language*, ngôn ngữ định nghĩa dữ liệu): `CREATE`, `ALTER`, `DROP`, `RENAME`,
`TRUNCATE`. Nhóm lệnh thao tác trên chính dữ liệu (`INSERT`, `UPDATE`, `DELETE`, `SELECT`) là *DML*,
học ở [chương 05](05-select-co-ban.md).

Một hình ảnh dễ nhớ: DDL là đóng kệ và dán nhãn cho từng ngăn ("ngăn này chỉ chứa số nguyên", "ngăn
này không được để trống", "mã hàng ở ngăn này không được trùng"). DML là đặt hàng lên kệ và lấy hàng
xuống. Kệ được đóng chắc chắn thì món hàng đặt sai ngăn bị từ chối ngay ở cửa, dù người đặt là ai.

Vì sao một backend developer cần nắm DDL dù hằng ngày chỉ viết migration bằng framework:

- Migration của Laravel (hay bất kỳ framework nào) cuối cùng cũng sinh ra câu DDL. Khi migration lỗi
  hoặc chạy chậm trên production, bạn phải đọc được câu DDL thật để biết chuyện gì đang xảy ra.
- Các *ràng buộc* (*constraint*) khai báo trong DDL là tuyến phòng thủ cuối cùng cho dữ liệu. Code
  ứng dụng có bug, script sửa tay chạy nhầm, hai service cùng ghi vào một bảng: ràng buộc vẫn chặn
  được dữ liệu sai.
- DDL trong MySQL có những hành vi bất ngờ (tự commit transaction, khoá bảng, `TRUNCATE` không
  rollback được) mà không biết thì sẽ trả giá trên production.

Các lệnh chính của chương:

| Lệnh | Tác dụng | Mục |
|---|---|---|
| `CREATE DATABASE`, `DROP DATABASE` | Tạo, xoá database | 2 |
| `CREATE TABLE` | Tạo bảng cùng các cột và ràng buộc | 3, 4, 5, 6 |
| `ALTER TABLE`, `RENAME TABLE` | Sửa cấu trúc bảng, đổi tên bảng | 7 |
| `DROP TABLE` | Xoá bảng (cả cấu trúc lẫn dữ liệu) | 8 |
| `TRUNCATE TABLE` | Xoá sạch dữ liệu, giữ cấu trúc | 8 |
| `CREATE TEMPORARY TABLE` | Bảng tạm, chỉ tồn tại trong một session | 10 |

### 1.2 Chuẩn bị một MySQL 8.4 để thử

Mọi câu SQL trong chương chạy được trên MySQL 8.4 với cấu hình mặc định. Nếu chưa có MySQL, cách
nhanh nhất là Docker (chi tiết cài đặt ở [chương 01](01-database-la-gi.md)):

```bash
# Chạy trên máy của bạn (cần Docker). Lần đầu sẽ tải image về.
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4

# Đợi server khởi động xong (xem `docker logs my84`), rồi mở mysql client bên trong container:
docker exec -it my84 mysql -uroot -proot
```

Từ đây, các khối `sql` được gõ tại dấu nhắc `mysql>`. Mỗi câu kết thúc bằng `;`. Kết thúc bằng `\G`
thay cho `;` thì kết quả được in theo chiều dọc, dễ đọc với bảng nhiều cột.

Một điều cần biết trước: mọi ví dụ giả định *SQL mode* mặc định của MySQL 8.4, gồm
`ONLY_FULL_GROUP_BY`, `STRICT_TRANS_TABLES`, `NO_ZERO_IN_DATE`, `NO_ZERO_DATE`,
`ERROR_FOR_DIVISION_BY_ZERO` và `NO_ENGINE_SUBSTITUTION`. Trong đó `STRICT_TRANS_TABLES` (gọi tắt là
*strict mode*) quyết định MySQL báo lỗi hay lặng lẽ "sửa" dữ liệu sai, và bạn sẽ gặp nó nhiều lần
trong chương. Kiểm tra mode đang dùng:

```sql
SELECT @@sql_mode;
```

⚠️ Server cũ hoặc server được cấu hình tay đôi khi tắt strict mode. Khi đó nhiều lỗi trong chương
này chỉ còn là *warning* (cảnh báo) và dữ liệu bị cắt xén mà không ai biết. Nếu kết quả bạn thấy khác
mô tả, việc đầu tiên là kiểm tra `@@sql_mode`.

## 2. Database: tạo, xem, xoá

### 2.1 Database trong MySQL là gì

Một *database* trong MySQL là một không gian có tên chứa các bảng (và các đối tượng khác như view,
stored procedure, trigger). Một MySQL server chứa nhiều database; mỗi ứng dụng thường dùng một
database riêng.

Trong MySQL, `DATABASE` và `SCHEMA` là hai từ đồng nghĩa: `CREATE SCHEMA` y hệt `CREATE DATABASE`.
PostgreSQL thì khác: một database chứa nhiều schema, schema là không gian tên bên trong database
([chương 25](25-postgres-doi-chieu.md)). Đọc tài liệu Postgres mà mang nghĩa MySQL vào là dễ lẫn.

Về mặt vật lý, mỗi database của MySQL là một thư mục trong *data directory* của server, các bảng
nằm trong đó dưới dạng file (với InnoDB mặc định, mỗi bảng một file `.ibd`). Đừng bao giờ tự tạo,
xoá, sửa thư mục và file này bằng tay: tài liệu MySQL 8.4 ghi rõ tạo database bằng `mkdir` là không
được hỗ trợ, và đụng tay vào file có thể làm hỏng sự nhất quán.

### 2.2 CREATE DATABASE

Cú pháp (rút gọn từ tài liệu MySQL 8.4):

```sql
CREATE {DATABASE | SCHEMA} [IF NOT EXISTS] db_name
    [ [DEFAULT] CHARACTER SET [=] charset_name ]
    [ [DEFAULT] COLLATE [=] collation_name ];
```

Phần trong ngoặc vuông là tuỳ chọn, `{A | B}` nghĩa là chọn một trong hai. Tạo database cho chương
này:

```sql
CREATE DATABASE lab04;
-- Query OK, 1 row affected

CREATE DATABASE lab04;
-- ERROR 1007 (HY000): Can't create database 'lab04'; database exists

CREATE DATABASE IF NOT EXISTS lab04;
-- Không lỗi; MySQL chỉ sinh một warning (xem bằng SHOW WARNINGS)
```

`IF NOT EXISTS` hữu ích trong script chạy lại nhiều lần (script khởi tạo, seed dữ liệu). Nó chỉ kiểm
tra tên: database đã có thì bỏ qua, không so sánh xem charset có giống cái bạn yêu cầu không.

Khai báo charset và collation tường minh:

```sql
CREATE DATABASE IF NOT EXISTS lab04
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
```

Charset và collation của database chỉ là *giá trị mặc định* cho các bảng tạo sau này trong database
đó (chương 03 đã giải thích charset, collation là gì). Quy tắc chọn, theo tài liệu MySQL:

- Ghi cả `CHARACTER SET` và `COLLATE`: dùng đúng cặp đó.
- Chỉ ghi `CHARACTER SET`: dùng collation mặc định của charset đó.
- Chỉ ghi `COLLATE`: dùng charset của collation đó.
- Không ghi gì: dùng charset và collation của server (`character_set_server`, `collation_server`),
  mặc định là `utf8mb4` và `utf8mb4_0900_ai_ci`.

Xem lại một database được tạo thế nào:

```sql
SHOW CREATE DATABASE lab04\G
```

```text
-- output minh hoạ
*************************** 1. row ***************************
       Database: lab04
Create Database: CREATE DATABASE `lab04` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */
```

Các đoạn `/*!40100 ... */` là *comment có điều kiện* của MySQL: server có phiên bản từ số đó trở lên
thì thực thi phần bên trong, client hoặc database khác thì coi là comment. Bạn sẽ gặp chúng nhiều
trong file dump.

Hoặc truy vấn metadata trong `information_schema` (mục 11):

```sql
SELECT SCHEMA_NAME, DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
FROM information_schema.SCHEMATA
WHERE SCHEMA_NAME = 'lab04';
-- lab04 | utf8mb4 | utf8mb4_0900_ai_ci
```

### 2.3 Chọn database đang làm việc

```sql
SHOW DATABASES;     -- liệt kê các database bạn có quyền thấy
USE lab04;          -- chọn lab04 làm database mặc định của session
SELECT DATABASE();  -- lab04
```

Sau `USE lab04`, câu `CREATE TABLE users (...)` tạo bảng trong `lab04`. Không `USE` thì phải ghi đầy
đủ `lab04.users`. Database mặc định là trạng thái của từng session: mở một kết nối mới là phải chọn
lại (hoặc truyền tên database lúc kết nối, ví dụ `mysql -uroot -proot lab04`).

### 2.4 Đổi và xoá database

`ALTER DATABASE` đổi giá trị mặc định của database:

```sql
ALTER DATABASE lab04 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

⚠️ Câu này chỉ đổi giá trị mặc định cho bảng tạo về sau. Bảng đã có vẫn giữ charset và collation đã
ghi trong định nghĩa của nó; muốn đổi bảng cũ phải `ALTER TABLE ... CONVERT TO CHARACTER SET` từng
bảng (mục 7.6). Stored routine đã tạo cũng giữ giá trị cũ; tài liệu MySQL yêu cầu xoá và tạo lại nếu
muốn chúng dùng giá trị mới.

Đổi lại về mặc định để các ví dụ sau trong chương khớp với output được ghi:

```sql
ALTER DATABASE lab04 COLLATE utf8mb4_0900_ai_ci;
```

Xoá database (thử xong thì tạo lại như hướng dẫn bên dưới):

```sql
DROP DATABASE IF EXISTS lab04;
```

`DROP DATABASE` xoá mọi bảng trong database rồi xoá chính database, trả về số bảng đã xoá. Không có
thùng rác, không có "undo": dữ liệu chỉ quay lại được từ backup ([chương 21](21-backup-restore.md)).

⚠️ Hai điều hay bị quên:

- Quyền đã cấp riêng cho database đó (`GRANT ... ON lab04.* ...`) **không** tự mất khi database bị
  xoá. Tạo lại database cùng tên là các quyền cũ có hiệu lực trở lại
  ([chương 18](18-user-quyen-bao-mat.md)).
- `DROP DATABASE` không xoá temporary table được tạo trong database đó; temporary table chỉ mất khi
  session tạo ra nó kết thúc (mục 10).

Nếu bạn vừa xoá `lab04` để thử, hãy tạo lại để dùng tiếp: `CREATE DATABASE lab04; USE lab04;`.

### 2.5 Đặt tên: độ dài, ký tự, chữ hoa chữ thường

Tên database, bảng, cột, index, constraint gọi chung là *identifier*. Vài quy tắc của MySQL 8.4:

- Độ dài tối đa 64 ký tự cho tên database, bảng, cột, index, constraint, view.
- Tên không đặt trong dấu nháy chỉ nên gồm chữ cái Latin, chữ số, `_` (về lý thuyết MySQL còn nhận
  `$` và một số ký tự Unicode, nhưng đừng dùng). Tên có thể bắt đầu bằng chữ số nhưng không được
  toàn chữ số.
- Tên trùng *từ khoá dành riêng* (*reserved word*) như `order`, `group`, `key`, `select`, hoặc chứa
  ký tự đặc biệt, phải đặt trong dấu backtick mỗi lần dùng:

```sql
CREATE TABLE `order` (id INT PRIMARY KEY);   -- được, nhưng mọi câu sau đều phải viết `order`
SELECT * FROM `order`;
```

  Đó là lý do bảng đơn hàng thường tên `orders` (số nhiều) để khỏi đụng từ khoá `ORDER`.

⚠️ Chữ hoa chữ thường trong tên bảng phụ thuộc hệ điều hành. Vì mỗi database là một thư mục và mỗi
bảng là file, tên database và tên bảng phân biệt hoa thường trên Linux nhưng không phân biệt trên
Windows và macOS (hệ file mặc định không phân biệt). Biến `lower_case_table_names` điều khiển hành vi
này, mặc định `0` trên Unix/Linux, `1` trên Windows, `2` trên macOS, và chỉ đặt được lúc khởi tạo
server, không đổi được về sau. Hệ quả kinh điển: code viết `FROM Users` chạy ngon trên máy macOS của
lập trình viên, lên server Linux thì báo bảng không tồn tại vì bảng thật tên `users`. Tên cột, tên
index thì không phân biệt hoa thường trên mọi nền tảng.

Quy ước an toàn và phổ biến: mọi tên viết thường, nối bằng `_` (*snake_case*), bảng dùng danh từ số
nhiều (`users`, `order_items`), không dùng từ khoá làm tên.

## 3. CREATE TABLE: tạo bảng

### 3.1 Giải phẫu một câu CREATE TABLE

Tạo bảng `users` đầu tiên trong `lab04`:

```sql
USE lab04;

CREATE TABLE users (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email      VARCHAR(255)    NOT NULL,
  full_name  VARCHAR(100)    NOT NULL,
  created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_email (email)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_0900_ai_ci
  COMMENT = 'Người dùng đã đăng ký';
```

Câu lệnh có ba phần:

```text
CREATE TABLE users (                      <- 1. tên bảng
  id BIGINT UNSIGNED NOT NULL ...,        <- 2a. định nghĩa cột: tên, kiểu, thuộc tính
  ...
  PRIMARY KEY (id),                       <- 2b. index và ràng buộc khai báo ở mức bảng
  UNIQUE KEY uq_users_email (email)
) ENGINE = InnoDB ... COMMENT = '...';    <- 3. table option, nằm sau dấu ngoặc đóng
```

1. Tên bảng (mục 2.5 về cách đặt tên).
2. Trong ngoặc là danh sách *định nghĩa*, cách nhau bằng dấu phẩy:
   - Định nghĩa cột: tên cột, kiểu dữ liệu ([chương 03](03-kieu-du-lieu.md)), rồi các thuộc tính như
     `NOT NULL`, `DEFAULT`, `AUTO_INCREMENT`, `COMMENT`. Các thuộc tính ràng buộc được giải thích ở
     mục 4 và 5.
   - Định nghĩa index và ràng buộc ở mức bảng: `PRIMARY KEY (...)`, `UNIQUE KEY tên (...)`,
     `KEY tên (...)`, `FOREIGN KEY ...`, `CHECK (...)`. Viết ở mức bảng thì một ràng buộc có thể bao
     nhiều cột, ví dụ `UNIQUE KEY (user_id, product_id)`.
3. *Table option*: storage engine, charset, collation mặc định cho các cột chuỗi, comment, giá trị
   bắt đầu của `AUTO_INCREMENT`...

⚠️ Dấu phẩy là lỗi cú pháp phổ biến nhất của người mới: thừa một dấu phẩy sau định nghĩa cuối cùng
(`UNIQUE KEY uq_users_email (email),` rồi đóng ngoặc) hay thiếu một dấu phẩy giữa hai cột đều làm câu
lệnh hỏng với lỗi `ERROR 1064 (42000): You have an error in your SQL syntax ...`. Thông báo lỗi này
trích đoạn SQL ngay sau chỗ parser bị vấp; lỗi thật thường nằm ngay trước đoạn đó.

Trong MySQL, từ khoá `KEY` và `INDEX` là đồng nghĩa khi khai báo index (`KEY idx_x (x)` và
`INDEX idx_x (x)` như nhau). Index là gì và vì sao nó làm truy vấn nhanh được học kỹ ở
[chương 11](11-index.md); chương này chỉ dùng index như một phần của ràng buộc.

### 3.2 Xem lại bảng đã tạo

```sql
SHOW TABLES;              -- liệt kê bảng trong database hiện tại
DESCRIBE users;           -- tóm tắt các cột (viết tắt: DESC users)
SHOW CREATE TABLE users\G -- câu CREATE TABLE đầy đủ mà server đang lưu
```

```text
-- output minh hoạ của DESCRIBE users
+------------+-----------------+------+-----+-------------------+-------------------+
| Field      | Type            | Null | Key | Default           | Extra             |
+------------+-----------------+------+-----+-------------------+-------------------+
| id         | bigint unsigned | NO   | PRI | NULL              | auto_increment    |
| email      | varchar(255)    | NO   | UNI | NULL              |                   |
| full_name  | varchar(100)    | NO   |     | NULL              |                   |
| created_at | datetime        | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+------------+-----------------+------+-----+-------------------+-------------------+
```

Cột `Key`: `PRI` là thuộc primary key, `UNI` là cột đầu của một unique index, `MUL` là cột đầu của
một index thường (cho phép trùng). Cột `Default` hiện `NULL` ở dòng `email` chỉ có nghĩa "không khai
báo DEFAULT", không có nghĩa giá trị mặc định là NULL (cột này `NOT NULL` mà).

```text
-- output minh hoạ của SHOW CREATE TABLE users\G
*************************** 1. row ***************************
       Table: users
Create Table: CREATE TABLE `users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='Người dùng đã đăng ký'
```

`SHOW CREATE TABLE` là nguồn sự thật: nó cho thấy server đã *hiểu* câu lệnh của bạn thế nào, gồm cả
những thứ bạn không viết (charset, tên ràng buộc tự sinh, `DEFAULT NULL` cho cột cho phép NULL). Khi
nghi ngờ một migration đã tạo ra cái gì, hãy xem `SHOW CREATE TABLE` thay vì đọc lại code migration.

### 3.3 ENGINE: chọn storage engine

MySQL chia làm hai tầng. Tầng server nhận câu SQL, phân tích, lập kế hoạch thực thi. Tầng *storage
engine* lo việc lưu dữ liệu xuống đĩa, đọc lên, khoá, transaction. Mỗi bảng chọn một storage engine
bằng table option `ENGINE` (kiến trúc chi tiết ở [chương 16](16-ben-trong-innodb.md)).

| Engine | Đặc điểm chính (theo tài liệu MySQL 8.4) | Dùng khi |
|---|---|---|
| InnoDB | Mặc định. Có transaction (ACID), rollback, tự phục hồi sau crash, khoá mức dòng, hỗ trợ `FOREIGN KEY`, lưu dữ liệu theo primary key (clustered index) | Gần như mọi bảng |
| MyISAM | Gọn nhẹ nhưng không có transaction, khoá cả bảng khi ghi, không có khoá ngoại | Hệ cũ; bảng mới thì không |
| MEMORY | Toàn bộ dữ liệu trong RAM, mất khi server khởi động lại | Dữ liệu tạm, không quan trọng; ngày càng ít dùng |
| CSV | Bảng là file văn bản CSV, không có index | Trao đổi dữ liệu dạng CSV |
| ARCHIVE | Nén gọn, không có index | Lưu trữ lịch sử ít đọc |
| BLACKHOLE | Nhận dữ liệu rồi bỏ đi, như `/dev/null` | Một số cấu hình replication đặc biệt |

Xem engine nào khả dụng trên server: `SHOW ENGINES;` (cột `Support` là `DEFAULT` cho engine mặc định).

Từ MySQL 5.5 InnoDB đã là engine mặc định, nên không ghi `ENGINE` thì bảng vẫn là InnoDB. Nhiều team
vẫn ghi `ENGINE=InnoDB` cho rõ ràng, không hại gì.

⚠️ Hai bẫy:

- Trộn bảng InnoDB và MyISAM trong một transaction: khi `ROLLBACK`, thay đổi trên bảng MyISAM không
  được huỷ (MyISAM không có transaction), MySQL chỉ báo một warning. Dữ liệu hai bảng lệch nhau.
- Ghi tên engine không có trên server: với SQL mode mặc định (có `NO_ENGINE_SUBSTITUTION`), MySQL báo
  lỗi và không tạo bảng. Nếu mode này bị tắt, MySQL lặng lẽ tạo bảng bằng engine mặc định và chỉ để
  lại một warning, bảng của bạn không có thứ bạn tưởng.

### 3.4 Charset và collation ở mức bảng và mức cột

Charset và collation được kế thừa theo chuỗi:

```text
server (character_set_server, collation_server)
   └─> database (CREATE DATABASE ... CHARACTER SET ...)
          └─> bảng (table option DEFAULT CHARSET / COLLATE)
                 └─> cột chuỗi (CHARACTER SET / COLLATE trong định nghĩa cột)
```

Ở mỗi tầng, nếu không khai báo thì lấy giá trị của tầng trên. Quy tắc giống hệt mục 2.2: ghi cả hai
thì dùng cả hai; chỉ ghi charset thì lấy collation mặc định của charset đó; chỉ ghi collation thì
lấy charset của collation đó.

Khai báo ở mức cột hữu ích khi một cột cần so sánh khác phần còn lại. Ví dụ mã giảm giá phân biệt
chữ hoa chữ thường (`SALE10` khác `sale10`) trong khi cả bảng dùng collation không phân biệt:

```sql
CREATE TABLE coupons (
  id   INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  code VARCHAR(20) COLLATE utf8mb4_bin NOT NULL,   -- so sánh theo từng byte: phân biệt hoa thường
  note VARCHAR(255) NULL,                          -- kế thừa utf8mb4_0900_ai_ci của bảng
  UNIQUE KEY uq_coupons_code (code)
);
```

Với collation `utf8mb4_bin`, unique index chấp nhận cả `SALE10` lẫn `sale10`; với collation mặc định
`utf8mb4_0900_ai_ci` (`ci` = case-insensitive), hai giá trị này bị coi là trùng nhau.

⚠️ Nên để mọi bảng của một ứng dụng dùng cùng charset và collation. Hai cột khác collation đem so
sánh hay join với nhau có thể gây lỗi "Illegal mix of collations", hoặc khiến MySQL không dùng được
index. Khoá ngoại giữa hai cột chuỗi còn bắt buộc chúng cùng charset và collation (mục 4.6).

### 3.5 IF NOT EXISTS, LIKE và CREATE TABLE ... SELECT

```sql
CREATE TABLE users (id INT PRIMARY KEY);
-- ERROR 1050 (42S01): Table 'users' already exists

CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY);
-- Không lỗi, chỉ một warning. Bảng users cũ giữ nguyên, KHÔNG được thay bằng định nghĩa mới.
```

⚠️ `IF NOT EXISTS` chỉ kiểm tra tên. Nếu bảng đã tồn tại với cấu trúc khác, câu lệnh vẫn "thành công"
và bạn tiếp tục làm việc với cấu trúc cũ mà không hay biết.

Sao chép *cấu trúc* một bảng sang bảng mới, rỗng, bằng `LIKE`:

```sql
CREATE TABLE users_copy LIKE users;
```

Theo tài liệu MySQL 8.4, bảng mới giữ thuộc tính cột, các index, generated column, default dạng biểu
thức và ràng buộc `CHECK` (tên ràng buộc được sinh lại); nhưng **không** giữ khoá ngoại.

Tạo bảng mới kèm dữ liệu từ một câu `SELECT` (*CTAS*, *create table as select*):

```sql
CREATE TABLE users_backup_20261003 AS
SELECT * FROM users;
```

Cột của bảng mới được suy ra từ kết quả `SELECT`. Theo tài liệu MySQL 8.4, CTAS giữ `NULL`/`NOT NULL`,
charset, collation, comment và `DEFAULT` của cột, nhưng:

- **không** tự tạo index nào, kể cả primary key (muốn có thì khai báo trong phần `CREATE TABLE`, ví
  dụ `CREATE TABLE t (PRIMARY KEY (id)) AS SELECT ...`);
- không giữ thuộc tính `AUTO_INCREMENT`;
- cột generated ở bảng nguồn trở thành cột thường.

Một cách sao lưu nhanh trước khi chạy câu `UPDATE` rủi ro, giữ được cả index:

```sql
CREATE TABLE users_bak LIKE users;           -- cấu trúc + index
INSERT INTO users_bak SELECT * FROM users;   -- dữ liệu
```

Đây chỉ là bản sao tiện tay trên cùng server, không thay được backup thật
([chương 21](21-backup-restore.md)). Dọn dẹp các bảng thử:

```sql
DROP TABLE users_copy, users_backup_20261003, users_bak;
```

## 4. Ràng buộc: để database giữ luật cho dữ liệu

### 4.1 Ràng buộc là gì và vì sao không để mỗi code ứng dụng lo

Một *ràng buộc* (*constraint*) là một luật khai báo trong schema mà database tự kiểm tra ở **mọi**
câu ghi dữ liệu (`INSERT`, `UPDATE`, `LOAD DATA`...). Dòng nào vi phạm thì câu lệnh bị từ chối với
một lỗi; với bảng InnoDB và strict mode, câu lệnh lỗi không để lại thay đổi nào.

MySQL 8.4 có sáu loại ràng buộc:

| Ràng buộc | Luật | Mục |
|---|---|---|
| `NOT NULL` | Cột không được để trống (NULL) | 4.2 |
| `DEFAULT` | Không phải luật cấm, mà là giá trị tự điền khi câu `INSERT` không ghi cột đó | 4.3 |
| `UNIQUE` | Không có hai dòng trùng giá trị ở cột (hoặc tổ hợp cột) này | 4.4 |
| `PRIMARY KEY` | Định danh duy nhất cho mỗi dòng: `UNIQUE` + `NOT NULL`, mỗi bảng một cái | 4.5 |
| `FOREIGN KEY` | Giá trị phải tồn tại ở bảng khác (bảng cha) | 4.6 |
| `CHECK` | Biểu thức tuỳ ý phải không sai, ví dụ `price >= 0` | 4.7 |

"Ứng dụng đã validate rồi, cần gì ràng buộc ở database?" Có ba lý do:

1. **Nhiều đường ghi dữ liệu.** Ngoài web app còn có job chạy nền, script import, câu SQL sửa tay của
   người vận hành, một service khác dùng chung database. Validate trong code chỉ bảo vệ được đường
   đi qua đoạn code đó.
2. **Bug.** Code validate cũng là code, và có bug. Ràng buộc là lưới an toàn cuối cùng.
3. **Race condition** (tranh chấp do chạy đồng thời). Kiểu "kiểm tra trước rồi mới ghi" trong code
   không an toàn khi có hai request cùng lúc. Ví dụ đăng ký tài khoản với cùng một email:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `SELECT COUNT(*) FROM users WHERE email = 'an@x.com'` → 0 | | A thấy email chưa có |
| 2 | | `SELECT COUNT(*) FROM users WHERE email = 'an@x.com'` → 0 | B cũng thấy chưa có |
| 3 | `INSERT INTO users (email, ...) VALUES ('an@x.com', ...)` | | Thành công |
| 4 | | `INSERT INTO users (email, ...) VALUES ('an@x.com', ...)` | Không có `UNIQUE`: thành công, hai tài khoản trùng email. Có `UNIQUE`: lỗi 1062, B bị chặn |

   Bước kiểm tra ở tầng ứng dụng vẫn hữu ích để trả thông báo lỗi thân thiện cho người dùng, nhưng
   chỉ ràng buộc trong database mới thực sự *đảm bảo* luật. Nguyên tắc: validate ở app để báo lỗi
   đẹp, ràng buộc ở database để dữ liệu đúng; app bắt lỗi từ database (ví dụ lỗi 1062) và chuyển
   thành thông báo cho người dùng.

Ràng buộc khai báo được ở hai chỗ:

```sql
CREATE TABLE demo (
  a INT NOT NULL UNIQUE,                    -- mức cột: viết ngay trong định nghĩa cột
  b INT NOT NULL,
  c INT NOT NULL,
  CONSTRAINT uq_demo_b_c UNIQUE (b, c),     -- mức bảng: có thể bao nhiều cột, có tên tự đặt
  CONSTRAINT chk_demo_b_lt_c CHECK (b < c)
);
```

`NOT NULL` và `DEFAULT` chỉ viết được ở mức cột. `UNIQUE`, `PRIMARY KEY`, `FOREIGN KEY`, `CHECK` viết
được ở mức bảng, và nên viết ở mức bảng kèm tên tự đặt (`CONSTRAINT tên ...`) vì:

- tên xuất hiện trong thông báo lỗi, đọc lỗi là biết luật nào bị vi phạm;
- muốn xoá hay sửa ràng buộc thì phải gọi đúng tên; tên tự sinh như `orders_ibfk_1`, `demo_chk_1`
  vừa khó nhớ vừa khác nhau giữa các môi trường.

Quy ước đặt tên hay gặp: `uq_<bảng>_<cột>`, `fk_<bảng con>_<bảng cha>`, `chk_<bảng>_<ý nghĩa>`.
Primary key thì luôn có tên `PRIMARY`, không đặt được.

```sql
DROP TABLE demo;
```

### 4.2 NOT NULL

*NULL* là đánh dấu "không có giá trị" hoặc "không biết" (cách NULL tham gia so sánh và tính toán được
học kỹ ở [chương 06](06-ham-bieu-thuc-null.md)). Mặc định, một cột **cho phép** NULL: tài liệu MySQL
ghi rõ không khai báo `NULL` hay `NOT NULL` thì cột được coi như đã khai báo `NULL`.

`NOT NULL` cấm giá trị NULL. Với bảng `users` ở mục 3.1 (`email`, `full_name` đều `NOT NULL`):

```sql
INSERT INTO users (email, full_name) VALUES (NULL, 'An');
-- ERROR 1048 (23000): Column 'email' cannot be null

INSERT INTO users (full_name) VALUES ('An');
-- ERROR 1364 (HY000): Field 'email' doesn't have a default value
```

Hai lỗi khác nhau: lỗi 1048 khi bạn ghi tường minh NULL; lỗi 1364 khi bạn bỏ qua một cột `NOT NULL`
không có `DEFAULT`. Lỗi 1364 là hành vi của strict mode (xem cảnh báo ngay dưới).

⚠️ Khi strict mode bị tắt, câu thứ hai không lỗi mà chỉ sinh warning, và MySQL tự điền *giá trị mặc
định ngầm định* của kiểu dữ liệu: `0` cho số, chuỗi rỗng `''` cho chuỗi, giá trị "zero" cho ngày
giờ. Kết quả là một user có email rỗng nằm trong bảng mà không ai được báo.

Nên dùng `NOT NULL` khi nào? Gần như luôn luôn. Chỉ cho phép NULL khi "không có giá trị" mang nghĩa
thật trong nghiệp vụ: `deleted_at` (chưa bị xoá), `phone` (người dùng không khai), `paid_at` (chưa
thanh toán). Lý do: NULL kéo theo logic ba giá trị (TRUE, FALSE, UNKNOWN) với nhiều cạm bẫy như
`NOT IN` gặp NULL ra tập rỗng ([chương 06](06-ham-bieu-thuc-null.md)); mỗi cột cho phép NULL là thêm
một trường hợp mà mọi đoạn code đọc nó phải xử lý.

⚠️ `NOT NULL` không cấm chuỗi rỗng: `INSERT INTO users (email, full_name) VALUES ('', '')` hợp lệ.
Muốn cấm thì thêm `CHECK (email <> '')` (mục 4.7).

### 4.3 DEFAULT: giá trị mặc định

`DEFAULT` cho biết giá trị được điền khi câu `INSERT` không nhắc tới cột đó, hoặc khi bạn ghi từ khoá
`DEFAULT` ở chỗ giá trị.

```sql
CREATE TABLE orders (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id    BIGINT UNSIGNED NOT NULL,
  status     VARCHAR(20)     NOT NULL DEFAULT 'pending',
  total      DECIMAL(12,2)   NOT NULL DEFAULT 0,
  note       VARCHAR(255)    NULL,                        -- không ghi DEFAULT: ngầm định DEFAULT NULL
  created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
);

INSERT INTO orders (user_id) VALUES (1);
INSERT INTO orders (user_id, status) VALUES (1, DEFAULT);   -- DEFAULT ghi tường minh: như bỏ qua cột
SELECT id, user_id, status, total, note FROM orders;
-- 1 | 1 | pending | 0.00 | NULL
-- 2 | 1 | pending | 0.00 | NULL
```

(Bảng `orders` này chưa có khoá ngoại tới `users`; ta sẽ thêm ở mục 4.6.)

Có ba dạng giá trị mặc định:

1. **Hằng số** (*literal*): `DEFAULT 'pending'`, `DEFAULT 0`.
2. **`CURRENT_TIMESTAMP`** cho cột `DATETIME` và `TIMESTAMP`, viết không cần ngoặc. Kèm theo
   `ON UPDATE CURRENT_TIMESTAMP` thì cột còn tự cập nhật thành thời điểm hiện tại mỗi khi một cột
   khác của dòng thay đổi giá trị. Tài liệu MySQL lưu ý: nếu câu `UPDATE` gán mọi cột về đúng giá trị
   chúng đang có, cột này giữ nguyên. Nếu cột có phần lẻ giây, độ chính xác phải khớp ở mọi chỗ:
   `DATETIME(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)`.
3. **Biểu thức** trong ngoặc tròn (*expression default*, có từ MySQL 8.0.13):

```sql
CREATE TABLE api_tokens (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  public_id  BINARY(16) NOT NULL DEFAULT (UUID_TO_BIN(UUID())),
  expires_at DATETIME   NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL 30 DAY),
  scopes     JSON       NOT NULL DEFAULT (JSON_ARRAY())
);
```

   Theo tài liệu MySQL 8.4, biểu thức mặc định được dùng hằng số, hàm có sẵn (kể cả hàm cho kết quả
   khác nhau mỗi lần gọi như `UUID()`, `RAND()`) và toán tử; **không** được dùng subquery, biến,
   tham số, stored function, và không được tham chiếu cột `AUTO_INCREMENT`.

⚠️ Các bẫy về `DEFAULT`:

- Cột `BLOB`, `TEXT`, `JSON` (và `GEOMETRY`) chỉ nhận default viết dạng biểu thức. `DEFAULT '[]'`
  cho cột JSON báo lỗi 1101 (`BLOB, TEXT, GEOMETRY or JSON column ... can't have a default value`);
  viết `DEFAULT ('[]')` hoặc `DEFAULT (JSON_ARRAY())` thì được.
- Ghi tường minh `NULL` **không** kích hoạt default. Với cột `status VARCHAR(20) NOT NULL DEFAULT
  'pending'`, câu `INSERT INTO orders (user_id, status) VALUES (1, NULL)` báo lỗi 1048 chứ không
  điền `'pending'`. Code ứng dụng hay gặp lỗi này khi truyền thẳng biến `null` vào câu insert;
  muốn dùng default thì bỏ cột khỏi câu `INSERT` hoặc ghi `DEFAULT`.
- Đổi `DEFAULT` của một cột về sau (mục 7) chỉ ảnh hưởng các dòng insert sau đó; dòng cũ giữ nguyên
  giá trị đã lưu.
- `ON UPDATE CURRENT_TIMESTAMP` chỉ chạy khi dòng được sửa bằng `UPDATE` (hoặc các lệnh ghi khác) trong
  database. Nó cho biết "lần cuối dòng đổi", không cho biết ai đổi hay đổi gì; cần lịch sử thì phải
  có bảng audit riêng.

### 4.4 UNIQUE

`UNIQUE` đảm bảo không có hai dòng trùng giá trị ở một cột, hoặc trùng *tổ hợp* giá trị ở nhiều cột.
MySQL hiện thực `UNIQUE` bằng một *unique index* (cấu trúc tra cứu giúp kiểm tra trùng nhanh mà không
phải quét cả bảng; [chương 11](11-index.md)).

```sql
INSERT INTO users (email, full_name) VALUES ('an@x.com', 'An');
INSERT INTO users (email, full_name) VALUES ('an@x.com', 'An giả mạo');
-- ERROR 1062 (23000): Duplicate entry 'an@x.com' for key 'users.uq_users_email'
```

Thông báo lỗi ghi rõ giá trị bị trùng và tên index dạng `bảng.tên_index`: đây là lúc tên đặt cẩn
thận phát huy tác dụng.

Unique trên tổ hợp cột: mỗi user chỉ đánh giá một sản phẩm một lần, nhưng một user đánh giá được nhiều
sản phẩm và một sản phẩm có nhiều đánh giá:

```sql
CREATE TABLE reviews (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id    BIGINT UNSIGNED NOT NULL,
  product_id BIGINT UNSIGNED NOT NULL,
  stars      TINYINT UNSIGNED NOT NULL,
  CONSTRAINT uq_reviews_user_product UNIQUE (user_id, product_id)
);

INSERT INTO reviews (user_id, product_id, stars) VALUES (1, 100, 5);  -- được
INSERT INTO reviews (user_id, product_id, stars) VALUES (1, 101, 4);  -- được: khác product
INSERT INTO reviews (user_id, product_id, stars) VALUES (2, 100, 3);  -- được: khác user
INSERT INTO reviews (user_id, product_id, stars) VALUES (1, 100, 1);
-- ERROR 1062 (23000): Duplicate entry '1-100' for key 'reviews.uq_reviews_user_product'
```

⚠️ **NULL và UNIQUE.** Tài liệu MySQL: với mọi engine, unique index cho phép **nhiều** giá trị NULL ở
cột cho phép NULL. Lý do: NULL nghĩa là "không biết", hai cái "không biết" không được coi là bằng
nhau. Hệ quả hay bị bỏ sót với unique nhiều cột:

```sql
CREATE TABLE phones (
  user_id BIGINT UNSIGNED NOT NULL,
  phone   VARCHAR(20) NULL,
  CONSTRAINT uq_phones_user_phone UNIQUE (user_id, phone)
);
INSERT INTO phones VALUES (1, NULL);
INSERT INTO phones VALUES (1, NULL);   -- KHÔNG lỗi: (1, NULL) và (1, NULL) không bị coi là trùng
SELECT COUNT(*) FROM phones;           -- 2
DROP TABLE phones;
```

Muốn "trùng" được kiểm tra thì các cột trong unique phải `NOT NULL`. Trường hợp kinh điển "email
không trùng giữa các user chưa bị xoá mềm" cần mẹo với generated column, xem mục 6.4.

⚠️ Unique phụ thuộc collation. Với collation mặc định `utf8mb4_0900_ai_ci` (không phân biệt hoa
thường, không phân biệt dấu), `'An@X.com'` trùng với `'an@x.com'`, và `'Hà'` trùng với `'Ha'`. Thường
đó là điều bạn muốn với email; với mã sản phẩm phân biệt hoa thường thì phải dùng collation nhị phân
(mục 3.4).

### 4.5 PRIMARY KEY

*Primary key* (khoá chính, PK) là cột hoặc tổ hợp cột định danh duy nhất mỗi dòng ([chương
02](02-mo-hinh-quan-he-thiet-ke.md) bàn cách chọn khoá). Về mặt ràng buộc, PK = `UNIQUE` + `NOT NULL`,
với các luật riêng theo tài liệu MySQL 8.4:

- Mỗi bảng có tối đa một PK. Khai báo hai lần báo lỗi 1068 `Multiple primary key defined`.
- Mọi cột trong PK phải `NOT NULL`; nếu bạn không ghi, MySQL tự thêm `NOT NULL` một cách im lặng.
- Tên của PK luôn là `PRIMARY`.

Hai cách viết:

```sql
-- PK một cột, viết ở mức cột
CREATE TABLE categories (
  id   INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);

-- PK nhiều cột (composite primary key), bắt buộc viết ở mức bảng.
-- Bảng trung gian của quan hệ n-n: một user có nhiều role, một role có nhiều user
CREATE TABLE user_roles (
  user_id BIGINT UNSIGNED NOT NULL,
  role_id INT UNSIGNED    NOT NULL,
  PRIMARY KEY (user_id, role_id)
);
```

Trong InnoDB, PK còn quyết định cách dữ liệu nằm trên đĩa: các dòng của bảng được lưu sắp xếp theo
PK trong một cấu trúc gọi là *clustered index*, và mọi index khác (secondary index) đều chứa kèm giá
trị PK của dòng. Vì vậy PK nên ngắn và không đổi; chi tiết ở [chương 11](11-index.md) và
[chương 16](16-ben-trong-innodb.md).

Bảng **không** khai báo PK thì sao? Theo tài liệu InnoDB:

1. InnoDB lấy unique index đầu tiên mà mọi cột đều `NOT NULL` làm clustered index.
2. Nếu không có, InnoDB tự tạo một clustered index ẩn tên `GEN_CLUST_INDEX` trên một cột ẩn chứa
   *row ID* 6 byte, tăng dần theo thứ tự insert. Bạn không truy vấn được cột này.

Bảng không có PK vẫn chạy, nhưng gây nhiều phiền toái: không có cách tham chiếu đúng một dòng, row
ID ẩn không dùng được trong query, và chính thông báo lỗi 3750 của MySQL cảnh báo rằng bảng không có
primary key có thể gây vấn đề hiệu năng với *row-based replication* ([chương
22](22-replication-ha.md)). Các công cụ thay đổi schema online ([chương
20](20-thay-doi-schema-migration.md)) cũng cần bảng có khoá duy nhất. Quy tắc thực tế: **mọi bảng đều
có PK tường minh**.

MySQL có hai biến hệ thống liên quan (cả hai mặc định `OFF`):

- `sql_require_primary_key = ON`: `CREATE TABLE` không có PK, hoặc `ALTER TABLE` xoá PK, bị từ chối
  với lỗi 3750. Nhiều đội bật biến này để chặn sai sót từ gốc.
- `sql_generate_invisible_primary_key = ON`: với bảng InnoDB tạo ra không có PK, server tự thêm cột
  `my_row_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT INVISIBLE` làm PK (*GIPK*, generated invisible
  primary key). Cột *invisible* không xuất hiện trong `SELECT *` nhưng vẫn truy vấn được khi gọi đúng
  tên.

### 4.6 FOREIGN KEY: khoá ngoại

#### 4.6.1 Ý tưởng

[Chương 02](02-mo-hinh-quan-he-thiet-ke.md) đã giới thiệu quan hệ 1-n: một user có nhiều đơn hàng,
bảng `orders` có cột `user_id` trỏ tới `users.id`. Nếu không có gì ràng buộc, không ai cấm bạn tạo
đơn hàng với `user_id = 999` trong khi user 999 không tồn tại, hay xoá một user khi đơn hàng của họ
vẫn còn. Những dòng trỏ tới "hư không" như vậy gọi là *dòng mồ côi* (*orphan row*): báo cáo sai, join
mất dữ liệu, code đọc ra thì lỗi.

*Khoá ngoại* (*foreign key*, FK) là ràng buộc: mọi giá trị khác NULL ở cột của *bảng con* (*child
table*, bảng chứa FK, ở đây `orders`) phải tồn tại ở cột được tham chiếu của *bảng cha* (*parent
table*, ở đây `users`).

```text
   users (bảng cha)                 orders (bảng con)
  +----+------------+              +----+---------+
  | id | email      |              | id | user_id |---+  FK: orders.user_id
  +----+------------+              +----+---------+   |      REFERENCES users(id)
  |  1 | an@x.com   | <------------| 10 |    1    |   |
  |  2 | binh@x.com | <------------| 12 |    2    |   |
  |  3 | chi@x.com  |              | 99 |   999   | <-+  bị từ chối: users không có id 999
  +----+------------+              +----+---------+
```

#### 4.6.2 Tạo khoá ngoại

Làm lại dữ liệu cho dễ theo dõi (id ghi tường minh để mọi người thấy cùng kết quả):

```sql
DROP TABLE IF EXISTS orders;
DELETE FROM users;
INSERT INTO users (id, email, full_name) VALUES
  (1, 'an@x.com',   'An'),
  (2, 'binh@x.com', 'Bình'),
  (3, 'chi@x.com',  'Chi');
INSERT INTO coupons (id, code) VALUES (5, 'SALE10');   -- bảng coupons ở mục 3.4

CREATE TABLE orders (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id    BIGINT UNSIGNED NOT NULL,
  coupon_id  INT UNSIGNED    NULL,
  status     VARCHAR(20)     NOT NULL DEFAULT 'pending',
  total      DECIMAL(12,2)   NOT NULL DEFAULT 0,
  created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id),
  CONSTRAINT fk_orders_coupon FOREIGN KEY (coupon_id) REFERENCES coupons (id)
    ON DELETE SET NULL
);

INSERT INTO orders (id, user_id, coupon_id, total) VALUES
  (10, 1, 5,    100.00),
  (11, 1, NULL,  50.00),
  (12, 2, NULL,  70.00);
```

Cú pháp đầy đủ (theo tài liệu MySQL 8.4):

```sql
[CONSTRAINT [symbol]] FOREIGN KEY [index_name] (col_name, ...)
    REFERENCES tbl_name (col_name, ...)
    [ON DELETE reference_option]
    [ON UPDATE reference_option]

reference_option: RESTRICT | CASCADE | SET NULL | NO ACTION | SET DEFAULT
```

Thử vi phạm:

```sql
INSERT INTO orders (user_id, total) VALUES (999, 10);
-- ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails
--   (`lab04`.`orders`, CONSTRAINT `fk_orders_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`))

DELETE FROM users WHERE id = 1;
-- ERROR 1451 (23000): Cannot delete or update a parent row: a foreign key constraint fails (...)

DELETE FROM users WHERE id = 3;   -- được: Chi chưa có đơn nào
```

Lỗi 1452 là từ phía bảng con (thêm hoặc sửa dòng con trỏ tới cha không tồn tại), lỗi 1451 là từ
phía bảng cha (xoá hoặc sửa dòng cha đang có con trỏ tới). Phần trong ngoặc cho biết bảng và tên ràng
buộc bị vi phạm.

Xem lại bảng, bạn sẽ thấy một index mà bạn không hề khai báo:

```text
-- output minh hoạ, trích phần cuối của SHOW CREATE TABLE orders\G
  PRIMARY KEY (`id`),
  KEY `fk_orders_user` (`user_id`),
  KEY `fk_orders_coupon` (`coupon_id`),
  CONSTRAINT `fk_orders_coupon` FOREIGN KEY (`coupon_id`) REFERENCES `coupons` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_orders_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
```

Tài liệu MySQL giải thích: MySQL cần index trên cột FK ở bảng con (với các cột FK đứng **đầu** index,
đúng thứ tự) để việc kiểm tra không phải quét cả bảng; nếu chưa có index phù hợp, InnoDB tự tạo.
Index đó cũng phục vụ luôn các truy vấn kiểu "đơn hàng của user X".

#### 4.6.3 Điều kiện để tạo được khoá ngoại

Theo tài liệu MySQL 8.4, câu tạo FK bị từ chối nếu thiếu một trong các điều kiện:

| Điều kiện | Vi phạm thì sao |
|---|---|
| Bảng cha và con dùng cùng một storage engine hỗ trợ FK (InnoDB), và không phải temporary table | Với engine không hỗ trợ FK như MyISAM, tài liệu MySQL ghi mệnh đề FK được phân tích rồi **bỏ qua**, không báo lỗi |
| Cột con và cột cha có kiểu "tương tự": số nguyên và `DECIMAL` phải cùng kích thước và cùng dấu (`BIGINT UNSIGNED` với `BIGINT UNSIGNED`); chuỗi không cần cùng độ dài nhưng phải cùng charset và collation | Lỗi 3780 `Referencing column ... and referenced column ... are incompatible` |
| Cột cha là `PRIMARY KEY` hoặc `UNIQUE` (MySQL 8.4 mặc định `restrict_fk_on_non_standard_key = ON`) | Lỗi 6125 `Failed to add the foreign key constraint. Missing unique key for constraint ...` |
| Không dùng prefix index, nên cột `TEXT`/`BLOB` không làm FK được | Không tạo được FK |
| Bảng InnoDB không được *partition* ([chương 23](23-partition-sharding-scale.md)) | Không tạo được FK |
| FK không được trỏ tới virtual generated column (mục 6) | Không tạo được FK |
| Dùng `SET NULL` thì cột con phải cho phép NULL | Lỗi 1830 `Column ... cannot be NOT NULL: needed in a foreign key constraint ... SET NULL` |

Về điều kiện thứ ba: các bản InnoDB cũ cho phép FK trỏ tới một index *không unique*, một mở rộng phi
chuẩn. MySQL 8.4 coi đó là tính năng lỗi thời và mặc định chặn.

⚠️ Bẫy kiểu dữ liệu hay gặp: `users.id` là `BIGINT UNSIGNED` (kiểu mà `$table->id()` của Laravel sinh
ra), còn cột con lại khai báo `INT` hoặc `BIGINT` có dấu. FK báo lỗi 3780. Laravel có
`foreignId('user_id')` sinh đúng `BIGINT UNSIGNED` chính vì lý do này.

⚠️⚠️ **Bẫy nguy hiểm nhất: `REFERENCES` viết ngay trong định nghĩa cột bị bỏ qua.**

```sql
CREATE TABLE wishlists (
  id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id BIGINT UNSIGNED NOT NULL REFERENCES users (id)    -- trông như FK, nhưng KHÔNG phải
);
INSERT INTO wishlists (user_id) VALUES (999);   -- thành công, không có FK nào được tạo
DROP TABLE wishlists;
```

Chuẩn SQL cho phép cú pháp này (gọi là *inline REFERENCES*), PostgreSQL chạy đúng. Nhưng tài liệu
MySQL 8.4 ghi rõ: MySQL phân tích cú pháp rồi **lặng lẽ bỏ qua** `REFERENCES` viết trong định nghĩa
cột; chỉ `FOREIGN KEY (...) REFERENCES ...` viết riêng mới tạo khoá ngoại. Câu lệnh không báo lỗi,
không warning. Luôn kiểm tra bằng `SHOW CREATE TABLE` (hoặc truy vấn `information_schema`, mục 11) xem
FK đã thật sự tồn tại chưa.

Tương tự, đừng dùng mệnh đề `MATCH FULL`/`MATCH PARTIAL`: tài liệu MySQL cho biết không engine nào
thực thi `MATCH`, và ghi `MATCH` còn khiến `ON DELETE`/`ON UPDATE` bị bỏ qua.

#### 4.6.4 ON DELETE và ON UPDATE: khi dòng cha bị xoá hoặc đổi khoá

Khi một dòng cha bị `DELETE`, hoặc giá trị khoá của nó bị `UPDATE`, database phải quyết định làm gì
với các dòng con đang trỏ tới. Đó là *referential action* (hành động tham chiếu):

| Hành động | Ý nghĩa (InnoDB) | Ví dụ hợp lý |
|---|---|---|
| `RESTRICT` | Từ chối thao tác trên dòng cha nếu còn dòng con | Không cho xoá user còn đơn hàng |
| `NO ACTION` | Trong InnoDB giống hệt `RESTRICT`, kiểm tra ngay lập tức. Đây là **mặc định** khi không ghi gì | |
| `CASCADE` | Xoá dòng cha thì xoá luôn các dòng con; sửa khoá cha thì sửa theo ở dòng con | Xoá đơn hàng thì xoá các dòng chi tiết đơn |
| `SET NULL` | Xoá hoặc sửa khoá cha thì đặt cột FK ở dòng con thành NULL | Xoá mã giảm giá, đơn hàng cũ vẫn giữ nhưng không còn gắn mã |
| `SET DEFAULT` | Parser nhận, nhưng InnoDB **từ chối** định nghĩa bảng có hành động này | |

`ON DELETE` và `ON UPDATE` được khai báo độc lập. Với primary key kiểu số tự tăng không bao giờ đổi,
`ON UPDATE` gần như không bao giờ được kích hoạt; `ON DELETE` mới là quyết định quan trọng.

Ví dụ `SET NULL` với dữ liệu ở trên (`fk_orders_coupon` khai báo `ON DELETE SET NULL`):

```sql
DELETE FROM coupons WHERE id = 5;
SELECT id, user_id, coupon_id FROM orders ORDER BY id;
-- 10 | 1 | NULL     <- trước đó là 5, InnoDB tự đặt thành NULL
-- 11 | 1 | NULL
-- 12 | 2 | NULL
```

Ví dụ `CASCADE`: chi tiết đơn hàng không có nghĩa khi đơn không còn.

```sql
CREATE TABLE order_items (
  order_id BIGINT UNSIGNED   NOT NULL,
  line_no  SMALLINT UNSIGNED NOT NULL,
  product  VARCHAR(100)      NOT NULL,
  qty      INT UNSIGNED      NOT NULL,
  PRIMARY KEY (order_id, line_no),
  CONSTRAINT fk_items_order FOREIGN KEY (order_id) REFERENCES orders (id)
    ON DELETE CASCADE
);
INSERT INTO order_items VALUES (10, 1, 'Bút', 2), (10, 2, 'Vở', 5), (11, 1, 'Thước', 1);

DELETE FROM orders WHERE id = 10;
SELECT * FROM order_items;
-- 11 | 1 | Thước | 1      <- hai dòng của đơn 10 đã bị xoá theo
```

Ở bảng này InnoDB không cần tạo thêm index cho FK: primary key `(order_id, line_no)` đã có `order_id`
đứng đầu, thoả điều kiện "cột FK đứng đầu index".

Thứ tự tạo và xoá bảng phải tôn trọng quan hệ cha con: tạo bảng cha trước, xoá bảng con trước.

```sql
DROP TABLE users;
-- ERROR 3730 (HY000): Cannot drop table 'users' referenced by a foreign key constraint
--   'fk_orders_user' on table 'orders'.
```

Bảng cũng có thể có FK trỏ về chính nó, ví dụ danh mục nhiều cấp:
`categories.parent_id ... REFERENCES categories (id)`.

⚠️ Những điều cần biết trước khi dùng `CASCADE`:

- Thao tác cascade do InnoDB thực hiện bên trong engine. Tài liệu MySQL ghi: hành động cascade của
  khoá ngoại **không kích hoạt trigger** ([chương 17](17-view-procedure-trigger.md)). Tương tự, ORM như
  Eloquent không biết các dòng con đã bị xoá, nên event `deleting`/`deleted` của model con không chạy.
- Một câu `DELETE` trên bảng cha có thể kéo theo hàng triệu dòng con trong cùng một transaction: giữ
  lock lâu, log phình to, replica bị trễ. Với cây dữ liệu lớn, xoá dòng con theo từng lô bằng job
  trước, rồi mới xoá dòng cha.
- `ON DELETE CASCADE` từ `users` xuống `orders` nghĩa là xoá một user sẽ xoá sạch lịch sử mua hàng,
  thường là điều kế toán không chấp nhận. Dữ liệu có giá trị lịch sử nên dùng `RESTRICT` kèm *soft
  delete* (đánh dấu đã xoá thay vì xoá thật).

#### 4.6.5 Tắt kiểm tra khoá ngoại và cái giá của khoá ngoại

Biến session `foreign_key_checks` (mặc định `ON`) bật/tắt việc kiểm tra:

```sql
SET foreign_key_checks = 0;
-- ... nạp dữ liệu theo thứ tự bất kỳ ...
SET foreign_key_checks = 1;
```

Công cụ dump như `mysqldump` dùng cách này để nạp lại các bảng mà không cần đúng thứ tự cha trước con
sau. ⚠️ Tài liệu MySQL nhấn mạnh: bật lại `foreign_key_checks` **không** quét lại dữ liệu, nên dòng mồ
côi nạp vào trong lúc tắt sẽ nằm đó vĩnh viễn mà không có lỗi nào. Chỉ tắt khi bạn chắc dữ liệu nguồn
đã đúng.

Khoá ngoại không miễn phí:

- Mỗi lần ghi bảng con, InnoDB phải tra bảng cha; mỗi lần xoá dòng cha, phải tra bảng con.
- Khi kiểm tra, InnoDB đặt *shared lock* lên dòng cha liên quan; trong một số mẫu ghi đồng thời, lock
  này dẫn tới deadlock ([chương 15](15-lock-deadlock.md)).
- Khoá ngoại chỉ hoạt động trong một MySQL server. Dữ liệu chia ra nhiều database server (sharding)
  hoặc nhiều service thì không dùng FK được, phải kiểm tra ở tầng ứng dụng
  ([chương 23](23-partition-sharding-scale.md)).

Khuyến nghị cho phần lớn ứng dụng chạy trên một database: **dùng khoá ngoại**. Cái giá ở trên nhỏ so
với chi phí dọn dữ liệu mồ côi về sau.

### 4.7 CHECK: luật tuỳ ý trên giá trị của dòng

#### 4.7.1 CHECK là gì

`CHECK (biểu thức)` buộc mỗi dòng phải thoả một điều kiện: giá không âm, ngày kết thúc sau ngày bắt
đầu, trạng thái thuộc một danh sách cho trước.

⚠️ Mốc phiên bản quan trọng: **trước MySQL 8.0.16, `CHECK` được phân tích cú pháp rồi bỏ qua** (không
kiểm tra gì). Từ 8.0.16 trở đi `CHECK` mới thực sự được thực thi. Tài liệu, bài blog hay câu trả lời
cũ nói "MySQL không hỗ trợ CHECK" là nói về các bản cũ đó.

```sql
CREATE TABLE products (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  sku        VARCHAR(32)     NOT NULL,
  name       VARCHAR(200)    NOT NULL,
  price      DECIMAL(12,2)   NOT NULL,
  sale_price DECIMAL(12,2)   NULL,
  stock      INT             NOT NULL DEFAULT 0,
  status     VARCHAR(20)     NOT NULL DEFAULT 'draft',
  CONSTRAINT uq_products_sku    UNIQUE (sku),
  CONSTRAINT chk_products_price CHECK (price >= 0),
  CONSTRAINT chk_products_sale  CHECK (sale_price < price),
  CONSTRAINT chk_products_stock CHECK (stock >= 0),
  CONSTRAINT chk_products_status CHECK (status IN ('draft', 'active', 'archived'))
);

INSERT INTO products (sku, name, price) VALUES ('P1', 'Bút', 10000);           -- được

INSERT INTO products (sku, name, price) VALUES ('P2', 'Vở', -5);
-- ERROR 3819 (HY000): Check constraint 'chk_products_price' is violated.

INSERT INTO products (sku, name, price, sale_price) VALUES ('P3', 'Thước', 8000, 9000);
-- ERROR 3819 (HY000): Check constraint 'chk_products_sale' is violated.

INSERT INTO products (sku, name, price, sale_price) VALUES ('P4', 'Tẩy', 5000, NULL);  -- được (xem dưới)

UPDATE products SET stock = stock - 1 WHERE sku = 'P1';
-- ERROR 3819 (HY000): Check constraint 'chk_products_stock' is violated.   (stock đang là 0)

UPDATE products SET status = 'deleted' WHERE sku = 'P1';
-- ERROR 3819 (HY000): Check constraint 'chk_products_status' is violated.
```

Ràng buộc `chk_products_stock` là một ví dụ đẹp về "đưa luật xuống database": dù code trừ kho có bug
hay hai request cùng trừ một lúc, tồn kho không bao giờ âm.

#### 4.7.2 CHECK và NULL

Dòng `P4` được chấp nhận dù có `CHECK (sale_price < price)`. Lý do: `NULL < 5000` cho kết quả
UNKNOWN (không biết), không phải FALSE. Tài liệu MySQL: dòng chỉ vi phạm khi biểu thức cho kết quả
**FALSE**; kết quả UNKNOWN (NULL) được cho qua.

Hãy so sánh với `WHERE`: `WHERE` chỉ giữ dòng có điều kiện TRUE, còn `CHECK` chỉ chặn dòng có điều
kiện FALSE. Muốn bắt buộc có giá trị thì phải thêm `NOT NULL`, hoặc viết rõ trong CHECK:
`CHECK (sale_price IS NULL OR sale_price < price)` (đọc dễ hiểu hơn, cùng hành vi).

#### 4.7.3 Luật viết CHECK

Theo tài liệu MySQL 8.4:

- CHECK viết ở **mức cột** chỉ được nhắc tới chính cột đó (nhắc cột khác thì lỗi 3813). CHECK ở
  **mức bảng** nhắc được nhiều cột, kể cả cột định nghĩa phía sau.
- Được dùng: cột thường và generated column (trừ cột `AUTO_INCREMENT`), hằng số, hàm có sẵn cho kết
  quả xác định (*deterministic*), toán tử.
- Không được dùng: hàm không xác định như `NOW()`, `CURRENT_USER()`, `CONNECTION_ID()`; stored function
  và hàm do người dùng nạp vào; biến; subquery; tham chiếu tới bảng khác. Vì vậy
  `CHECK (birth_date < CURDATE())` không viết được: "hôm nay" mỗi ngày một khác.
- Cột đã dùng trong khoá ngoại có hành động làm thay đổi dòng con (`ON DELETE SET NULL`,
  `ON UPDATE SET NULL`, `ON UPDATE CASCADE`) thì không được dùng trong CHECK, và ngược lại (lỗi 3823).
  Lý do: CHECK được server kiểm tra trước khi giao dòng cho storage engine, còn các hành động này do
  InnoDB thực hiện bên trong engine, server không có cơ hội kiểm tra.
- Không đặt tên thì MySQL tự sinh tên dạng `<tên bảng>_chk_<số>`. Tên CHECK phải **duy nhất trong cả
  database**, không chỉ trong bảng: hai bảng cùng database không thể cùng có CHECK tên `chk_price`.
  Đó là lý do quy ước đặt tên có kèm tên bảng.
- Được kiểm tra với `INSERT`, `UPDATE`, `REPLACE`, `LOAD DATA`, `LOAD XML`. Câu lệnh có `IGNORE` thì
  dòng vi phạm bị bỏ qua kèm warning thay vì lỗi.

`CHECK` có thể khai báo `NOT ENFORCED`: ràng buộc được lưu vào định nghĩa bảng nhưng không được kiểm
tra. Dùng khi muốn ghi lại ý định trước rồi bật sau, hoặc tạm tắt khi nạp dữ liệu. Bật lại
(`ALTER TABLE ... ALTER CHECK tên ENFORCED`, mục 7.5) thì MySQL kiểm tra các dòng hiện có, có dòng vi
phạm là lỗi và bảng không đổi.

Hai cách dùng CHECK hay gặp:

```sql
-- Đúng một trong hai cột được có giá trị (comment gắn vào post HOẶC video)
CHECK ((post_id IS NOT NULL) + (video_id IS NOT NULL) = 1)

-- Khoảng thời gian hợp lệ
CHECK (ends_at > starts_at)
```

(Biểu thức thứ nhất dựa vào việc MySQL coi TRUE là 1 và FALSE là 0 khi cộng.)

### 4.8 Tổng kết: ràng buộc nào báo lỗi gì

| Vi phạm | Mã lỗi (SQLSTATE) | Thông báo bắt đầu bằng |
|---|---|---|
| Ghi NULL vào cột `NOT NULL` | 1048 (23000) | `Column '...' cannot be null` |
| Bỏ qua cột `NOT NULL` không có `DEFAULT` | 1364 (HY000) | `Field '...' doesn't have a default value` |
| Trùng `UNIQUE` hoặc `PRIMARY KEY` | 1062 (23000) | `Duplicate entry '...' for key '...'` |
| Dòng con trỏ tới cha không tồn tại | 1452 (23000) | `Cannot add or update a child row: a foreign key constraint fails` |
| Xoá/sửa dòng cha còn dòng con (`RESTRICT`) | 1451 (23000) | `Cannot delete or update a parent row: a foreign key constraint fails` |
| `CHECK` cho kết quả FALSE | 3819 (HY000) | `Check constraint '...' is violated.` |

Code ứng dụng thường bắt lỗi theo mã: ví dụ lỗi 1062 khi đăng ký thì trả "email đã được dùng". Trong
PHP, PDO ném `PDOException` với `getCode()` là SQLSTATE (chuỗi như `'23000'`), còn mã lỗi MySQL
(1062) nằm ở phần tử thứ hai của mảng `errorInfo`; nhiều lỗi ràng buộc khác nhau dùng chung SQLSTATE
`23000`, nên muốn phân biệt chính xác thì xem mã lỗi MySQL ([chương 19](19-database-tu-ung-dung.md)).

## 5. AUTO_INCREMENT: id tự tăng

### 5.1 Cách dùng

Phần lớn bảng dùng *surrogate key* (khoá thay thế, [chương 02](02-mo-hinh-quan-he-thiet-ke.md)): một
cột số không mang nghĩa nghiệp vụ, do database tự cấp. Trong MySQL đó là thuộc tính `AUTO_INCREMENT`:

```sql
CREATE TABLE tickets (
  id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  subject VARCHAR(200)    NOT NULL,
  PRIMARY KEY (id)
);

INSERT INTO tickets (subject) VALUES ('Không đăng nhập được');                  -- id 1
INSERT INTO tickets (subject) VALUES ('Quên mật khẩu'), ('Lỗi thanh toán'), ('Đổi email');  -- id 2, 3, 4
SELECT LAST_INSERT_ID();
-- 2   <- id của dòng ĐẦU TIÊN trong câu INSERT gần nhất, không phải 4
```

Luật của `AUTO_INCREMENT` theo tài liệu MySQL 8.4:

- Mỗi bảng có tối đa một cột `AUTO_INCREMENT`, cột đó phải được index (thường chính là primary key)
  và không được có `DEFAULT`. Khai báo hai cột tự tăng, hoặc cột tự tăng không có index, báo lỗi 1075
  `Incorrect table definition; there can be only one auto column and it must be defined as a key`.
- Không ghi cột đó, hoặc ghi `NULL` hay `0`, thì MySQL cấp giá trị tiếp theo. Dãy bắt đầu từ 1.
  (Nếu SQL mode có `NO_AUTO_VALUE_ON_ZERO` thì chỉ `NULL` mới kích hoạt cấp số, `0` được lưu là 0.)
- Ghi tường minh một giá trị lớn hơn bộ đếm hiện tại thì bộ đếm nhảy lên theo:

```sql
INSERT INTO tickets (id, subject) VALUES (100, 'Nhập tay id 100');
INSERT INTO tickets (subject) VALUES ('Dòng kế tiếp');   -- id 101
```

`LAST_INSERT_ID()` trả về id vừa được cấp **trong chính kết nối của bạn**. Tài liệu MySQL: giá trị
này được giữ theo từng kết nối và không bị ảnh hưởng bởi client khác, kể cả khi họ cũng đang insert.
Đây là cách đúng để lấy id vừa tạo. Phía PHP, `PDO::lastInsertId()` (và Eloquent khi bạn `save()` một
model mới) cũng lấy id vừa cấp theo từng kết nối như vậy ([chương 19](19-database-tu-ung-dung.md)).
Ngược lại, `SELECT MAX(id) FROM tickets` để "lấy id mình vừa insert"
là sai: giữa lúc bạn insert và lúc bạn đọc, người khác có thể đã insert thêm.

### 5.2 Vì sao dãy id luôn có "lỗ"

Người mới hay ngạc nhiên khi thấy id nhảy từ 101 lên 103. Tài liệu InnoDB liệt kê nhiều nguyên nhân,
và tất cả đều là thiết kế có chủ đích:

- **Rollback:** id đã cấp cho một transaction không bao giờ được trả lại, kể cả khi transaction đó
  rollback.
- **Insert thất bại:** câu `INSERT` lỗi vì trùng một cột `UNIQUE` khác, hay `INSERT IGNORE` bỏ qua dòng
  trùng, vẫn có thể đã tiêu một id.
- **Insert nhiều dòng:** với chế độ cấp số mặc định của MySQL 8.4 (`innodb_autoinc_lock_mode = 2`),
  InnoDB có thể cấp dư số cho các câu insert không biết trước số dòng (như `INSERT ... SELECT`), phần
  dư bị bỏ.
- **Xoá dòng:** id của dòng đã `DELETE` không được dùng lại.

Vì sao không trả lại id sau rollback? Hãy xem hai session chạy đồng thời:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `INSERT INTO tickets (subject) VALUES ('A');` | | A được cấp id 102 |
| 2 | | `INSERT INTO tickets (subject) VALUES ('B');` (autocommit) | B được cấp id 103 ngay, không phải chờ A |
| 3 | `ROLLBACK;` | | Dòng 102 biến mất; id 102 không được cấp lại cho ai |
| 4 | | `SELECT id FROM tickets ORDER BY id DESC LIMIT 2;` | 103, 101: có "lỗ" ở 102 |

Nếu muốn dãy liên tục, B ở bước 2 sẽ phải chờ A commit hay rollback xong mới biết được số tiếp theo,
tức là mọi lệnh insert vào bảng phải xếp hàng tuần tự. InnoDB chọn hiệu năng: cấp số ngay, chấp nhận
lỗ.

⚠️ Hệ quả thực tế:

- Đừng dùng id để đếm số dòng, đừng hiển thị id như "số thứ tự" mà người dùng mong liên tục (số hoá
  đơn theo luật phải liên tục thì cần cơ chế riêng).
- Thứ tự id không phải thứ tự commit. Trong bảng trên, id 102 được cấp trước 103; nếu A commit thay vì
  rollback và commit *sau* B, một tiến trình đọc kiểu "lấy các dòng có `id > id_lớn_nhất_đã_xử_lý`"
  có thể đã đọc thấy 103, ghi nhớ mốc 103, và bỏ sót vĩnh viễn dòng 102.

### 5.3 Bộ đếm được lưu ở đâu

Từ MySQL 8.0, giá trị lớn nhất của bộ đếm được ghi vào *redo log* mỗi khi thay đổi và lưu vào *data
dictionary* ở mỗi checkpoint, nên bộ đếm **giữ nguyên qua lần khởi động lại**. Trước 8.0, InnoDB tính
lại bộ đếm bằng giá trị lớn nhất đang có trong bảng khi khởi động: xoá vài dòng cuối rồi restart là các
id đó bị cấp lại, nguy hiểm nếu id cũ đã được gửi ra ngoài (email, hệ thống khác). Tài liệu MySQL vẫn
lưu ý một ngoại lệ: sau khi server dừng đột ngột, không bảo đảm tuyệt đối việc không cấp lại id đã cấp.

Chỉnh bộ đếm bằng tay:

```sql
ALTER TABLE tickets AUTO_INCREMENT = 1000;   -- id tiếp theo là 1000
```

Tài liệu InnoDB: câu này chỉ đẩy được bộ đếm lên cao hơn giá trị lớn nhất đang có trong cột; đặt số
nhỏ hơn không làm các id đã dùng được cấp lại. `TRUNCATE TABLE` thì đưa bộ đếm về đầu (mục 8).

### 5.4 Chọn kiểu dữ liệu: khi nào thì hết số

Giới hạn của kiểu số nguyên ([chương 03](03-kieu-du-lieu.md)):

| Kiểu | Giá trị lớn nhất |
|---|---|
| `INT` (có dấu) | 2.147.483.647 (khoảng 2,1 tỷ) |
| `INT UNSIGNED` | 4.294.967.295 (khoảng 4,3 tỷ) |
| `BIGINT UNSIGNED` | 18.446.744.073.709.551.615 |

Theo tài liệu MySQL, khi cột `AUTO_INCREMENT` chạm giới hạn trên của kiểu, lần cấp số tiếp theo
thất bại: bảng không nhận thêm dòng nào nữa cho tới khi đổi kiểu cột, mà đổi
kiểu cột trên bảng vài tỷ dòng là một thao tác chép lại cả bảng rất lâu. Hai tỷ nghe nhiều, nhưng bảng
log, event, lượt xem có thể chạm mức đó; nhớ rằng id còn bị "tiêu" bởi lỗ (mục 5.2). Với bảng có thể
lớn, dùng `BIGINT UNSIGNED` ngay từ đầu (tốn 8 byte thay vì 4 byte mỗi giá trị); `$table->id()` của
Laravel mặc định đã là `BIGINT UNSIGNED`.

Hai biến `auto_increment_increment` và `auto_increment_offset` (mặc định đều là 1) cho phép cấp id
theo bước nhảy, ví dụ server A cấp 1, 3, 5... còn server B cấp 2, 4, 6..., dùng trong vài mô hình
nhiều server cùng nhận ghi. Ứng dụng thông thường không cần đụng tới.

### 5.5 Đối chiếu PostgreSQL

PostgreSQL không có `AUTO_INCREMENT`; cách chuẩn SQL là *identity column*:

```sql
-- PostgreSQL
CREATE TABLE tickets (
  id      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  subject TEXT NOT NULL
);
INSERT INTO tickets (subject) VALUES ('Quên mật khẩu') RETURNING id;   -- trả về id vừa cấp
```

Bên dưới là một đối tượng *sequence*. Với `GENERATED ALWAYS`, câu `INSERT` ghi tường minh giá trị id
bị từ chối trừ khi có `OVERRIDING SYSTEM VALUE`; với `GENERATED BY DEFAULT` thì giá trị ghi tay được
nhận. Kiểu cũ `SERIAL` vẫn gặp nhiều trong code cũ. Sequence của PostgreSQL cũng có lỗ y như MySQL:
tài liệu PostgreSQL ghi giá trị lấy từ sequence không được thu hồi khi transaction bị huỷ, vì lý do
giống hệt mục 5.2.

## 6. Generated column: cột tính từ cột khác

### 6.1 Generated column là gì

Một *generated column* (cột sinh) có giá trị luôn được tính từ một biểu thức trên các cột khác của
**cùng dòng**. Bạn không ghi giá trị cho nó; database tự tính và giữ nó luôn đúng.

```sql
CREATE TABLE order_lines (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  unit_price DECIMAL(12,2)   NOT NULL,
  qty        INT UNSIGNED    NOT NULL,
  line_total DECIMAL(14,2)   GENERATED ALWAYS AS (unit_price * qty) STORED
);

INSERT INTO order_lines (unit_price, qty) VALUES (15000.00, 3);
SELECT unit_price, qty, line_total FROM order_lines;
-- 15000.00 | 3 | 45000.00

UPDATE order_lines SET qty = 4 WHERE id = 1;
SELECT line_total FROM order_lines WHERE id = 1;
-- 60000.00   <- tự tính lại

INSERT INTO order_lines (unit_price, qty, line_total) VALUES (1000, 1, 1000);
-- ERROR 3105 (HY000): The value specified for generated column 'line_total' in table 'order_lines' is not allowed.
```

Cú pháp: `tên kiểu [GENERATED ALWAYS] AS (biểu thức) [VIRTUAL | STORED]`. `GENERATED ALWAYS` có thể bỏ,
chỉ cần `AS (...)`. Trong `INSERT`/`UPDATE`, giá trị duy nhất được phép ghi vào generated column là từ
khoá `DEFAULT`.

So với `DEFAULT (biểu thức)` ở mục 4.3: default chỉ được tính **một lần** lúc insert và ghi đè được;
generated column được tính lại **mỗi khi** dòng thay đổi và không ghi đè được.

### 6.2 VIRTUAL và STORED

| | `VIRTUAL` (mặc định) | `STORED` |
|---|---|---|
| Lưu trên đĩa | Không, tốn 0 byte | Có, như cột thường |
| Tính lúc nào | Mỗi lần đọc dòng | Lúc insert/update dòng |
| Index | Được (InnoDB gọi là *virtual index*, chỉ là secondary index) | Được, kể cả làm primary key |
| Thêm cột vào bảng có sẵn | Chỉ sửa metadata, gần như tức thì | Phải dựng lại toàn bộ bảng |
| Khoá ngoại | Không dùng được, ở cả phía bảng con lẫn bảng cha | Được, với vài giới hạn về `ON DELETE`/`ON UPDATE` |

Khi index một cột `VIRTUAL`, giá trị của nó được *lưu trong index* (tài liệu gọi là materialized trong
bản ghi của index), nên truy vấn đọc qua index không cần tính lại. Chọn nhanh: mặc định dùng `VIRTUAL`;
chọn `STORED` khi biểu thức tốn kém mà đọc nhiều hơn ghi rất nhiều, hoặc khi cần làm primary key.

### 6.3 Index trên generated column

Cách dùng hay gặp nhất: index một giá trị nằm trong cột JSON. Bản thân cột `JSON` không index trực
tiếp được, nhưng một generated column trích ra từ nó thì được (ví dụ dựa trên tài liệu MySQL):

```sql
CREATE TABLE events (
  id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  payload JSON NOT NULL,
  user_id INT GENERATED ALWAYS AS (payload->'$.user_id') VIRTUAL,
  KEY idx_events_user (user_id)
);

INSERT INTO events (payload) VALUES ('{"user_id": 42, "type": "login"}');
SELECT id FROM events WHERE user_id = 42;   -- có thể dùng index idx_events_user
```

Tài liệu MySQL còn cho biết optimizer nhận ra biểu thức trong query trùng với định nghĩa của một
generated column có index và dùng index đó. Index trên biểu thức (*functional index*) và
*multi-valued index* cho mảng JSON là các cách khác, học ở [chương 11](11-index.md).

### 6.4 Ứng dụng: unique có điều kiện cho soft delete

Bài toán: dùng *soft delete* (xoá mềm, đặt `deleted_at` thay vì xoá thật). Muốn email không trùng giữa
các tài khoản còn hoạt động, nhưng tài khoản đã xoá mềm thì email được đăng ký lại.

Cách ngây thơ `UNIQUE (email, deleted_at)` **không chạy**: mọi dòng còn hoạt động có
`deleted_at = NULL`, mà unique coi các NULL là khác nhau (mục 4.4), nên hai dòng
`('an@x.com', NULL)` không bị coi là trùng. Mẹo: một generated column chỉ có giá trị khi dòng còn
hoạt động, rồi đặt unique trên cột đó.

```sql
CREATE TABLE members (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  email        VARCHAR(255)    NOT NULL,
  deleted_at   DATETIME        NULL,
  email_active VARCHAR(255) GENERATED ALWAYS AS (IF(deleted_at IS NULL, email, NULL)) VIRTUAL,
  CONSTRAINT uq_members_email_active UNIQUE (email_active)
);

INSERT INTO members (email) VALUES ('an@x.com');
INSERT INTO members (email) VALUES ('an@x.com');
-- ERROR 1062 (23000): Duplicate entry 'an@x.com' for key 'members.uq_members_email_active'

UPDATE members SET deleted_at = NOW() WHERE email = 'an@x.com';   -- xoá mềm: email_active thành NULL
INSERT INTO members (email) VALUES ('an@x.com');                  -- được
SELECT email, deleted_at IS NULL AS active FROM members ORDER BY id;
-- an@x.com | 0
-- an@x.com | 1
```

Dòng đã xoá mềm có `email_active = NULL`, và nhiều NULL không vi phạm unique; dòng còn hoạt động thì
bị chặn trùng. PostgreSQL giải bài này gọn hơn bằng *partial index*
`CREATE UNIQUE INDEX ... ON members (email) WHERE deleted_at IS NULL` ([chương 11](11-index.md)).

### 6.5 Luật viết biểu thức

Theo tài liệu MySQL 8.4:

- Được dùng: hằng số, hàm có sẵn cho kết quả xác định, toán tử.
- Không được dùng: hàm không xác định (`NOW()`, `RAND()`, `UUID()`...), stored function, hàm người
  dùng nạp vào, biến, tham số, subquery. Lý do: giá trị phải tính lại được bất cứ lúc nào và luôn ra
  cùng kết quả.
- Tham chiếu được mọi cột thường của bảng (đứng trước hay sau đều được), nhưng chỉ tham chiếu được
  generated column **đứng trước** nó.
- Không tham chiếu được cột `AUTO_INCREMENT`, và bản thân generated column không thể `AUTO_INCREMENT`.
- Trigger không dùng được `NEW.cột` hay `OLD.cột` với generated column.

PostgreSQL có generated column kiểu `STORED` từ bản 12; bản 18 thêm kiểu `VIRTUAL` và lấy nó làm
mặc định, giống MySQL.

## 7. ALTER TABLE: sửa cấu trúc bảng đang có

Schema thay đổi theo sản phẩm: thêm tính năng là thêm cột, đổi nghiệp vụ là đổi ràng buộc.
`ALTER TABLE` sửa bảng đang có mà không mất dữ liệu (trừ khi bạn yêu cầu xoá). Một câu `ALTER TABLE`
có thể gồm nhiều thao tác, cách nhau bằng dấu phẩy.

### 7.1 Thêm cột: ADD COLUMN

```sql
ALTER TABLE users ADD COLUMN phone VARCHAR(20) NULL AFTER email;

ALTER TABLE users
  ADD COLUMN is_active     BOOLEAN  NOT NULL DEFAULT TRUE,
  ADD COLUMN last_login_at DATETIME NULL;

SELECT id, email, phone, is_active, last_login_at FROM users ORDER BY id;
-- 1 | an@x.com   | NULL | 1 | NULL
-- 2 | binh@x.com | NULL | 1 | NULL
```

- Cột mới mặc định nằm cuối bảng; `AFTER cột_khác` hoặc `FIRST` đặt nó ở vị trí khác. Thứ tự cột
  chỉ ảnh hưởng `SELECT *` và cách hiển thị, không ảnh hưởng hiệu năng truy vấn.
- Các dòng đang có nhận giá trị `DEFAULT` của cột mới (ở trên: `is_active = 1`), hoặc NULL nếu cột
  cho phép NULL và không có default.

⚠️ Thêm cột `NOT NULL` **không có** `DEFAULT` vào bảng đã có dữ liệu: MySQL điền giá trị mặc định
ngầm định của kiểu cho các dòng cũ (`0` cho số, chuỗi rỗng cho chuỗi), không báo gì. Riêng cột
`DATE`/`DATETIME` thì giá trị ngầm định là ngày "zero", bị SQL mode mặc định (`NO_ZERO_DATE` cùng
strict mode) chặn, nên câu `ALTER` lỗi nếu bảng không rỗng. Hãy luôn ghi `DEFAULT` rõ ràng khi thêm cột
`NOT NULL`, hoặc thêm cột cho phép NULL, điền dữ liệu, rồi mới đổi sang `NOT NULL`
([chương 20](20-thay-doi-schema-migration.md) có quy trình an toàn cho bảng lớn).

### 7.2 Sửa cột: MODIFY, CHANGE, RENAME COLUMN, ALTER COLUMN

MySQL có bốn mệnh đề, mỗi cái cho một việc:

| Mệnh đề | Đổi tên? | Đổi định nghĩa? | Ví dụ |
|---|---|---|---|
| `MODIFY` | Không | Có | `MODIFY full_name VARCHAR(150) NOT NULL` |
| `CHANGE` | Có | Có (bắt buộc ghi lại định nghĩa) | `CHANGE full_name display_name VARCHAR(150) NOT NULL` |
| `RENAME COLUMN` | Có | Không | `RENAME COLUMN display_name TO full_name` |
| `ALTER COLUMN` | Không | Chỉ default (và visible/invisible) | `ALTER COLUMN status SET DEFAULT 'new'` |

```sql
ALTER TABLE users MODIFY full_name VARCHAR(150) NOT NULL;           -- nới độ dài
ALTER TABLE users RENAME COLUMN full_name TO display_name;            -- chỉ đổi tên (MySQL 8.0+)
ALTER TABLE users RENAME COLUMN display_name TO full_name;            -- đổi lại cho các ví dụ sau
ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'new';             -- đổi default
ALTER TABLE orders ALTER COLUMN status DROP DEFAULT;                  -- bỏ default
ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'pending';         -- đặt lại như cũ
```

⚠️ **Bẫy lớn nhất của `MODIFY`/`CHANGE`: thuộc tính không ghi lại sẽ mất.** Tài liệu MySQL: định nghĩa
mới phải gồm kiểu dữ liệu và **mọi** thuộc tính bạn muốn giữ (trừ thuộc tính index như `PRIMARY KEY`,
`UNIQUE`); thuộc tính có ở định nghĩa cũ mà không ghi ở định nghĩa mới thì không được giữ lại. Ví dụ:

```sql
-- Ý định: chỉ nới full_name lên 200 ký tự
ALTER TABLE users MODIFY full_name VARCHAR(200);
-- Kết quả: full_name thành cột CHO PHÉP NULL, vì không ghi NOT NULL.
-- Tương tự, DEFAULT, COMMENT, UNSIGNED, AUTO_INCREMENT không ghi lại đều bị bỏ.
ALTER TABLE users MODIFY full_name VARCHAR(200) NOT NULL;   -- sửa lại cho đúng
```

Cách làm an toàn: chạy `SHOW CREATE TABLE`, chép nguyên định nghĩa cột hiện tại, chỉ sửa phần cần đổi.
Muốn chỉ đổi tên thì dùng `RENAME COLUMN`, muốn chỉ đổi default thì dùng `ALTER COLUMN`, hai mệnh đề này
không đụng tới phần còn lại của định nghĩa.

⚠️ Thu hẹp kiểu (ví dụ `VARCHAR(255)` thành `VARCHAR(10)` khi đã có giá trị dài hơn): MySQL cố chuyển
giá trị cũ sang kiểu mới. Với strict mode, việc chuyển làm mất dữ liệu thì câu `ALTER` báo lỗi và bảng
không đổi; tài liệu MySQL khuyên bật strict mode trước khi `ALTER` chính vì lý do này. Tắt strict mode
thì dữ liệu bị cắt cụt kèm warning.

Khi đổi tên cột bằng `CHANGE` hoặc `RENAME COLUMN`, MySQL tự cập nhật index và khoá ngoại tham chiếu
cột đó, nhưng **không** cập nhật biểu thức của generated column, view và stored procedure nhắc tới tên
cũ. Và tất nhiên không cập nhật code ứng dụng đang chạy: đổi tên cột trên production trong khi code cũ
vẫn đọc tên cũ là sự cố. [Chương 20](20-thay-doi-schema-migration.md) trình bày cách đổi tên không
downtime (expand/contract).

### 7.3 Xoá cột: DROP COLUMN

```sql
ALTER TABLE users DROP COLUMN last_login_at;
```

Dữ liệu của cột mất vĩnh viễn. Theo tài liệu MySQL:

- Cột bị xoá cũng được gỡ khỏi các index chứa nó; index mà mọi cột đều bị xoá thì bị xoá theo.
- Cột đang dùng trong khoá ngoại thì không xoá được (lỗi 1828 `Cannot drop column ...: needed in a
  foreign key constraint ...`); phải `DROP FOREIGN KEY` trước.
- Cột dùng trong `CHECK` thì không xoá được, trừ khi CHECK đó chỉ nhắc tới riêng cột này (khi đó CHECK
  bị xoá theo).
- Không xoá được cột cuối cùng của bảng (lỗi 1090: `You can't delete all columns with ALTER TABLE; use
  DROP TABLE instead`).

### 7.4 Đổi tên bảng

```sql
RENAME TABLE coupons TO vouchers;            -- cách 1
ALTER TABLE vouchers RENAME TO coupons;      -- cách 2, đổi lại như cũ
```

`RENAME TABLE` đổi được nhiều bảng trong một câu, và tài liệu MySQL bảo đảm việc đó diễn ra
*atomic*: không session nào thấy trạng thái nửa vời. Nhờ vậy có thể tráo hai bảng:

```sql
-- Chỉ là mẫu, đừng chạy trong lab04 (chưa có bảng products_new).
-- Đã dựng xong bảng mới products_new; tráo nó vào chỗ products trong một bước:
RENAME TABLE products TO products_old,
             products_new TO products;
```

Đây chính là bước cuối của các công cụ đổi schema online ([chương 20](20-thay-doi-schema-migration.md)).

⚠️ Khi đổi tên bảng: tên khoá ngoại trỏ tới bảng được MySQL cập nhật, nhưng quyền đã `GRANT` riêng cho
bảng **không** chuyển sang tên mới, và view viết theo tên cũ sẽ hỏng. `RENAME TABLE` không dùng được
cho temporary table (dùng `ALTER TABLE ... RENAME TO`).

### 7.5 Thêm, xoá index và ràng buộc

```sql
-- Index thường (chi tiết ở chương 11)
ALTER TABLE orders ADD INDEX idx_orders_status_created (status, created_at);
ALTER TABLE orders RENAME INDEX idx_orders_status_created TO idx_orders_status_time;
ALTER TABLE orders DROP INDEX idx_orders_status_time;

-- UNIQUE: lỗi 1062 nếu dữ liệu hiện có đã trùng, phải dọn dữ liệu trước
ALTER TABLE users ADD CONSTRAINT uq_users_phone UNIQUE (phone);

-- Khoá ngoại thêm sau: MySQL kiểm tra mọi dòng đang có
ALTER TABLE reviews ADD CONSTRAINT fk_reviews_user
  FOREIGN KEY (user_id) REFERENCES users (id);          -- được: user 1 và 2 đều tồn tại
ALTER TABLE reviews ADD CONSTRAINT fk_reviews_product
  FOREIGN KEY (product_id) REFERENCES products (id);
-- ERROR 1452 (23000): Cannot add or update a child row: a foreign key constraint fails (...)
-- vì reviews đang có product_id 100, 101 mà bảng products không có

-- Xoá khoá ngoại: index đi kèm VẪN CÒN, muốn bỏ thì xoá riêng
ALTER TABLE orders DROP FOREIGN KEY fk_orders_coupon;
ALTER TABLE orders DROP INDEX fk_orders_coupon;

-- CHECK
ALTER TABLE products ADD CONSTRAINT chk_products_name CHECK (name <> '');
ALTER TABLE products ALTER CHECK chk_products_name NOT ENFORCED;   -- tạm tắt
ALTER TABLE products ALTER CHECK chk_products_name ENFORCED;       -- bật lại: kiểm tra mọi dòng đang có
ALTER TABLE products DROP CHECK chk_products_name;

-- Primary key
ALTER TABLE user_roles DROP PRIMARY KEY, ADD PRIMARY KEY (role_id, user_id);
```

Tìm các dòng mồ côi trước khi thêm khoá ngoại bằng `LEFT JOIN` (học ở [chương 07](07-join.md)):

```sql
SELECT r.id, r.product_id
FROM reviews r
LEFT JOIN products p ON p.id = r.product_id
WHERE p.id IS NULL;      -- các review trỏ tới sản phẩm không tồn tại
```

Vài điểm cần nhớ, theo tài liệu MySQL:

- Với `ALTER TABLE ... ADD FOREIGN KEY`, tên index ghi sau `FOREIGN KEY` bị bỏ qua và MySQL tự sinh tên
  ràng buộc; muốn tự đặt tên thì dùng `ADD CONSTRAINT tên FOREIGN KEY ...` như ví dụ trên.
- `DROP CONSTRAINT tên` là cú pháp chung cho mọi loại ràng buộc; nếu hai ràng buộc khác loại trùng tên
  (MySQL cho phép vì mỗi loại có không gian tên riêng) thì phải dùng cú pháp riêng như
  `DROP FOREIGN KEY`, `DROP CHECK`, `DROP PRIMARY KEY`.
- Index đang phục vụ một khoá ngoại thì không xoá được (lỗi 1553 `Cannot drop index ...: needed in a
  foreign key constraint`) cho tới khi xoá khoá ngoại.
- Chỉ `CHECK` mới chuyển được sang `NOT ENFORCED`; các loại ràng buộc khác luôn được thực thi.

### 7.6 Đổi charset của bảng

```sql
ALTER TABLE coupons CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;   -- (1)
ALTER TABLE coupons DEFAULT CHARACTER SET utf8mb4;                                  -- (2)
```

Hai câu trông giống nhau nhưng khác hẳn:

1. `CONVERT TO` đổi default của bảng **và chuyển đổi mọi cột chuỗi** đang có, kể cả dữ liệu bên trong.
   Lưu ý: câu này cũng áp collation mới cho mọi cột, nên cột `code` đang dùng `utf8mb4_bin` ở mục 3.4
   bị đổi thành collation không phân biệt hoa thường; muốn giữ thì `MODIFY` riêng cột đó sau khi
   convert. Tài liệu MySQL còn cảnh báo cột `TEXT` hay `VARCHAR` có thể bị đổi sang kiểu lớn hơn (như
   `MEDIUMTEXT`) để chứa đủ số ký tự khi charset mới cần nhiều byte hơn mỗi ký tự.
2. `DEFAULT CHARACTER SET` chỉ đổi giá trị mặc định cho **cột thêm sau này**; cột đang có giữ nguyên.

Nếu bạn vừa chạy câu (1) trên `coupons`, trả cột `code` về collation nhị phân:
`ALTER TABLE coupons MODIFY code VARCHAR(20) COLLATE utf8mb4_bin NOT NULL;`

### 7.7 ALTER TABLE trên bảng lớn: biết trước khi chạy

Trên bảng vài dòng, mọi câu `ALTER` chạy tức thì. Trên bảng hàng chục triệu dòng đang phục vụ người
dùng thì khác, và đây là chủ đề của cả [chương 20](20-thay-doi-schema-migration.md). Ba ý nền tảng:

- Có thao tác chỉ sửa metadata nên gần như tức thì (thuật toán `INSTANT`, mặc định của MySQL 8.4 cho
  `ADD COLUMN`): thêm cột, đổi tên cột, đặt hoặc bỏ default, thêm cột `VIRTUAL`.
- Có thao tác phải dựng lại toàn bộ bảng. Theo bảng tra cứu online DDL của tài liệu MySQL 8.4, đổi kiểu
  dữ liệu của cột là một ví dụ: dựng lại bảng và **không** cho ghi đồng thời trong suốt thời gian đó.
- Mọi câu `ALTER` đều cần một *metadata lock* độc quyền trên bảng, dù chỉ trong khoảnh khắc. Nếu đang
  có một transaction dài chạm vào bảng, câu `ALTER` phải chờ, và mọi truy vấn tới sau cũng xếp hàng sau
  câu `ALTER` đó: cả bảng "đứng hình".

Một thói quen tốt: ghi rõ thuật toán mong muốn để MySQL báo lỗi thay vì lặng lẽ chọn cách chậm hơn:

```sql
ALTER TABLE users ADD COLUMN nickname VARCHAR(50) NULL, ALGORITHM = INSTANT;
-- Nếu thao tác không làm được bằng INSTANT, MySQL báo lỗi và không làm gì.
```

## 8. Xoá: DROP, TRUNCATE và DELETE

Có ba cách "làm mất dữ liệu" của một bảng, khác nhau về bản chất. Người mới hay coi chúng là một, và
đó là nguồn của nhiều sự cố.

### 8.1 DROP TABLE: xoá cả bảng

```sql
DROP TABLE IF EXISTS order_lines;

DROP TABLE tickets, khong_ton_tai;
-- ERROR 1051 (42S02): Unknown table ...
-- và tickets KHÔNG bị xoá
```

Theo tài liệu MySQL 8.4:

- `DROP TABLE` xoá định nghĩa bảng, toàn bộ dữ liệu, các index và trigger của bảng. Quyền đã `GRANT`
  riêng cho bảng thì **không** tự mất.
- Xoá nhiều bảng một lúc mà có bảng không tồn tại: không có `IF EXISTS` thì câu lệnh lỗi và **không
  thay đổi gì** (nhờ *atomic DDL* có từ MySQL 8.0, mục 9.3); có `IF EXISTS` thì bảng nào có sẽ bị xoá,
  bảng không có chỉ sinh một note.
- `DROP TEMPORARY TABLE` chỉ xoá temporary table (mục 10). Tài liệu MySQL khuyên dùng từ khoá này khi
  xoá bảng tạm để không lỡ tay xoá nhầm bảng thật trùng tên.
- Bảng đang được khoá ngoại của bảng khác trỏ tới thì không xoá được (lỗi 3730, mục 4.6.4).

⚠️ Người quen PostgreSQL chú ý: trong MySQL, từ khoá `RESTRICT` và `CASCADE` ở cuối `DROP TABLE`
**không làm gì cả**, chỉ được chấp nhận cho dễ chuyển code từ hệ khác. `DROP TABLE users CASCADE` trong
PostgreSQL xoá luôn các ràng buộc và view phụ thuộc; trong MySQL thì không.

### 8.2 TRUNCATE TABLE: xoá sạch dữ liệu, giữ cấu trúc

```sql
SELECT COUNT(*) FROM tickets;                        -- vài dòng còn lại từ mục 5
TRUNCATE TABLE tickets;
SELECT COUNT(*) FROM tickets;                        -- 0
INSERT INTO tickets (subject) VALUES ('Sau truncate');
SELECT id FROM tickets;                              -- 1: bộ đếm AUTO_INCREMENT về lại đầu

TRUNCATE TABLE users;
-- ERROR 1701 (42000): Cannot truncate a table referenced in a foreign key constraint (...)
```

Theo tài liệu MySQL 8.4, `TRUNCATE TABLE` trông giống `DELETE` không có `WHERE` nhưng thực chất là
**DDL**:

- Nó xoá rồi tạo lại bảng, nhanh hơn nhiều so với xoá từng dòng, nhất là với bảng lớn.
- Nó gây *implicit commit* nên **không rollback được** (mục 9).
- Nó thất bại nếu bảng khác có khoá ngoại trỏ tới bảng này (khoá ngoại giữa các cột trong cùng một bảng
  thì được).
- Nó không chạy trigger `ON DELETE`.
- Bộ đếm `AUTO_INCREMENT` về giá trị bắt đầu.
- Số dòng báo về thường là "0 rows affected", nghĩa là "không có thông tin", không phải "không xoá dòng
  nào".
- Cần quyền `DROP` trên bảng, không phải quyền `DELETE`.

### 8.3 So sánh DELETE, TRUNCATE và DROP

| Tiêu chí | `DELETE FROM t` (không `WHERE`) | `TRUNCATE TABLE t` | `DROP TABLE t` |
|---|---|---|---|
| Loại lệnh | DML | DDL | DDL |
| Xoá gì | Các dòng (có `WHERE` thì chọn được dòng) | Mọi dòng | Mọi dòng, cấu trúc, index, trigger |
| Rollback được? | Có, nếu trong transaction | Không (implicit commit) | Không (implicit commit) |
| Trigger `ON DELETE` | Chạy cho từng dòng | Không chạy | Trigger bị xoá cùng bảng |
| Khoá ngoại | Kiểm tra và cascade từng dòng | Lỗi nếu bảng khác có FK trỏ tới | Lỗi nếu bảng khác có FK trỏ tới |
| Bộ đếm `AUTO_INCREMENT` | Giữ nguyên | Về giá trị đầu | Mất cùng bảng |
| Với bảng lớn | Chậm: xử lý từng dòng, ghi undo log và binlog cho từng dòng, transaction khổng lồ | Nhanh | Nhanh |
| Dung lượng file của bảng | Không nhỏ đi; chỗ trống được dòng mới dùng lại | Trả lại cho hệ điều hành (InnoDB mặc định mỗi bảng một file) | Trả lại cho hệ điều hành |
| Quyền cần | `DELETE` | `DROP` | `DROP` |

Chọn cái nào:

- Xoá một phần dữ liệu: `DELETE ... WHERE ...` ([chương 05](05-select-co-ban.md)). Xoá rất nhiều dòng
  thì chia lô để không tạo transaction khổng lồ.
- Làm sạch bảng staging, bảng tạm, database test: `TRUNCATE`.
- Bỏ hẳn bảng không dùng nữa: `DROP`, sau khi chắc chắn có backup và không còn code nào đọc nó.

⚠️ Vì `TRUNCATE` và `DROP` không rollback được và chạy rất nhanh, một câu gõ nhầm database (chạy trên
production thay vì staging) là mất dữ liệu ngay lập tức. Khi thao tác tay trên production: kiểm tra
`SELECT DATABASE()` và `@@hostname` trước, và có backup đã kiểm tra khôi phục được
([chương 21](21-backup-restore.md)).

## 9. DDL tự commit: implicit commit

### 9.1 Hiện tượng

Trong MySQL, transaction gom nhiều câu lệnh thành một khối "tất cả hoặc không gì cả" (học kỹ ở
[chương 13](13-transaction-acid.md)). Nhưng DDL không chơi theo luật đó. Tài liệu MySQL: các câu
lệnh thuộc danh sách *implicit commit* sẽ kết thúc transaction đang mở **như thể bạn đã gõ `COMMIT`
ngay trước nó**, và phần lớn còn tự commit ngay sau khi chạy xong.

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | A mở transaction |
| 2 | `INSERT INTO tickets (subject) VALUES ('X');` | | Dòng X chưa commit |
| 3 | | `SELECT COUNT(*) FROM tickets WHERE subject = 'X';` | 0: B chưa thấy X |
| 4 | `ALTER TABLE tickets ADD COLUMN priority TINYINT NOT NULL DEFAULT 0;` | | MySQL commit transaction của A **trước** khi chạy `ALTER` |
| 5 | | `SELECT COUNT(*) FROM tickets WHERE subject = 'X';` | 1: X đã được commit |
| 6 | `ROLLBACK;` | | Không còn gì để rollback: dòng X và cột `priority` đều ở lại |

A tưởng mình đang trong một transaction và `ROLLBACK` sẽ huỷ được cả hai việc; thực tế transaction đã
kết thúc ở bước 4.

### 9.2 Những câu lệnh gây implicit commit

Theo trang "Statements That Cause an Implicit Commit" của tài liệu MySQL 8.4 (danh sách rút gọn):

| Nhóm | Ví dụ |
|---|---|
| DDL | `CREATE`/`ALTER`/`DROP` cho `DATABASE`, `TABLE`, `INDEX`, `VIEW`, `TRIGGER`, `PROCEDURE`, `FUNCTION`, `EVENT`...; `RENAME TABLE`; `TRUNCATE TABLE` |
| Quản lý tài khoản | `CREATE USER`, `ALTER USER`, `DROP USER`, `GRANT`, `REVOKE`, `SET PASSWORD` |
| Điều khiển transaction và khoá | `BEGIN`, `START TRANSACTION` (mở transaction mới thì commit cái đang mở), `LOCK TABLES`, `UNLOCK TABLES`, `SET autocommit = 1` |
| Quản trị | `ANALYZE TABLE`, `CHECK TABLE`, `OPTIMIZE TABLE`, `REPAIR TABLE`, `FLUSH` |

Ngoại lệ đáng nhớ: `CREATE TEMPORARY TABLE` và `DROP TEMPORARY TABLE` **không** gây commit, nhưng tài
liệu cũng lưu ý chúng không rollback được. Các thao tác khác trên temporary table như `ALTER TABLE`,
`CREATE INDEX` thì vẫn gây commit.

### 9.3 Atomic DDL không phải transactional DDL

Từ MySQL 8.0, mỗi câu DDL là *atomic*: các thay đổi trong data dictionary, trong storage engine và trong
binlog của câu đó hoặc cùng được ghi nhận, hoặc cùng bị huỷ, kể cả khi server sập giữa chừng. Ví dụ ở
mục 8.1: `DROP TABLE tickets, khong_ton_tai` lỗi thì `tickets` vẫn còn nguyên (trước 8.0, `tickets` đã
bị xoá trước khi lỗi xảy ra).

Nhưng tài liệu MySQL nhấn mạnh: *atomic DDL không phải transactional DDL*. Mỗi câu DDL tự nó là một
khối; bạn **không** gom được nhiều câu DDL (hay DDL với DML) vào cùng một transaction để rollback chung.

PostgreSQL thì có *transactional DDL*: phần lớn DDL chạy được trong transaction và rollback được.

```sql
-- PostgreSQL
BEGIN;
ALTER TABLE tickets ADD COLUMN priority SMALLINT NOT NULL DEFAULT 0;
DELETE FROM tickets WHERE subject = 'X';
ROLLBACK;   -- cả cột mới lẫn dòng bị xoá đều được khôi phục
```

(Vẫn có ngoại lệ, ví dụ `CREATE INDEX CONCURRENTLY` và `CREATE DATABASE` không chạy được trong
transaction; [chương 25](25-postgres-doi-chieu.md).)

### 9.4 Hệ quả cho code ứng dụng và migration

- **Migration trên MySQL không có tính nguyên tử.** Một file migration chứa ba câu `ALTER`, câu thứ
  hai lỗi: câu thứ nhất đã có hiệu lực, còn framework ghi nhận migration là chưa chạy. Nếu câu thứ nhất
  là `ADD COLUMN` thì chạy lại sẽ lỗi ngay ở câu đó vì cột đã tồn tại (lỗi 1060 `Duplicate column
  name`), phải dọn tay. Laravel 13 chỉ bọc
  migration trong transaction khi schema grammar của database hỗ trợ (PostgreSQL có, MySQL không). Cách
  phòng: mỗi migration chỉ làm một thay đổi schema.
- **Đừng chạy DDL bên trong transaction nghiệp vụ.** Tài liệu Laravel (mục *Implicit Commits*) cảnh
  báo: chạy câu gây implicit commit qua `DB::statement()` hay `DB::unprepared()` bên trong
  `DB::transaction()` sẽ commit cả transaction, và Laravel không biết điều đó (bộ đếm transaction của
  nó lệch với thực tế). Một ví dụ hay gặp: `TRUNCATE` một bảng staging giữa chừng một transaction làm
  commit luôn phần việc trước đó.
- Muốn một thay đổi schema "huỷ được", chỉ có cách viết thêm câu DDL ngược lại (ví dụ `DROP COLUMN` để
  huỷ `ADD COLUMN`), và dữ liệu đã mất do `DROP` thì chỉ backup cứu được.

## 10. Temporary table: bảng tạm của một session

### 10.1 Tạo và dùng

*Temporary table* là bảng chỉ tồn tại trong **một session** (một kết nối) và tự biến mất khi session
đó đóng.

```sql
CREATE TEMPORARY TABLE tmp_top_users AS
SELECT user_id, SUM(total) AS spent
FROM orders
GROUP BY user_id;

SELECT * FROM tmp_top_users ORDER BY spent DESC;
-- 2 | 70.00
-- 1 | 50.00      (đơn 10 của user 1 đã bị xoá ở ví dụ CASCADE, mục 4.6.4)

DROP TEMPORARY TABLE tmp_top_users;
```

Theo tài liệu MySQL 8.4:

- Chỉ session tạo ra mới thấy bảng; hai session khác nhau có thể cùng tạo temporary table trùng tên mà
  không đụng nhau.
- Bảng tự bị xoá khi session đóng.
- Temporary table được phép trùng tên với một bảng thường; khi đó bảng thường bị **che** cho tới khi
  temporary table bị xoá.
- Cần quyền `CREATE TEMPORARY TABLES`; sau khi tạo, server không kiểm tra quyền trên bảng tạm nữa.
- `CREATE TEMPORARY TABLE` không gây implicit commit (mục 9.2).

Dùng khi nào: tính toán nhiều bước (báo cáo cần kết quả trung gian để join nhiều lần), nạp dữ liệu từ
file vào bảng tạm để kiểm tra trước khi đổ vào bảng thật. Nhiều trường hợp đơn giản hơn có thể dùng
*CTE* (`WITH ...`, [chương 09](09-subquery-cte-union.md)) thay cho bảng tạm.

### 10.2 Các giới hạn và cạm bẫy

Theo trang "TEMPORARY Table Problems" của tài liệu MySQL 8.4:

- Không nhắc tới cùng một temporary table hai lần trong một câu truy vấn:

```sql
CREATE TEMPORARY TABLE temp_table (id INT PRIMARY KEY);
SELECT * FROM temp_table JOIN temp_table AS t2;      -- ví dụ lấy từ tài liệu MySQL
-- ERROR 1137 (HY000): Can't reopen table: 'temp_table'
DROP TEMPORARY TABLE temp_table;
```

  (Tài liệu gợi ý dùng CTE nếu truy vấn cho phép.)
- `SHOW TABLES` không liệt kê temporary table.
- `RENAME TABLE` không dùng được, phải dùng `ALTER TABLE ... RENAME`.
- Khoá ngoại không dùng được với temporary table (mục 4.6.3).
- `DROP DATABASE` không xoá temporary table tạo trong database đó.

⚠️ Vòng đời gắn với **kết nối**, không gắn với request. Với PHP-FPM thông thường, mỗi request mở và
đóng kết nối nên bảng tạm biến mất cuối request. Nhưng với *persistent connection* hoặc ứng dụng chạy
lâu giữ kết nối qua nhiều request (Laravel Octane, worker của queue), một temporary table không được
`DROP` sẽ sống sang request sau: request sau `CREATE TEMPORARY TABLE` trùng tên thì lỗi bảng đã tồn
tại, hoặc tệ hơn là đọc phải dữ liệu cũ. Luôn `DROP TEMPORARY TABLE IF EXISTS` khi dùng xong
([chương 19](19-database-tu-ung-dung.md)).

⚠️ Đừng nhầm temporary table do bạn tạo với *internal temporary table* mà MySQL tự tạo khi thực thi
`GROUP BY`, `DISTINCT`, `UNION`... (thấy chữ `Using temporary` trong `EXPLAIN`,
[chương 12](12-explain-toi-uu-query.md)). Cái sau do optimizer quản lý, bạn không tạo hay xoá nó.

## 11. information_schema: hỏi database về chính nó

### 11.1 Metadata và information_schema

*Metadata* là "dữ liệu về dữ liệu": có những bảng nào, mỗi bảng có cột gì, kiểu gì, ràng buộc nào,
index nào. MySQL cho bạn đọc metadata bằng chính SQL qua database đặc biệt `information_schema`.

Theo tài liệu MySQL 8.4:

- `information_schema` có trong mọi MySQL server, chứa thông tin về tất cả database khác.
- Các "bảng" trong đó thật ra là *view* chỉ đọc (từ MySQL 8.0, chúng là view trên *data dictionary*
  của server); không có file nào trên đĩa, và không thể `INSERT`, `UPDATE`, `DELETE` vào đó.
- Mỗi người dùng chỉ thấy các dòng ứng với đối tượng mà họ có quyền truy cập.
- Cấu trúc theo chuẩn SQL (SQL:2003), nên PostgreSQL cũng có `information_schema` với nhiều bảng cùng
  tên (bên cạnh catalog riêng `pg_catalog`).

So với các lệnh `SHOW` (gõ nhanh, đọc bằng mắt), `information_schema` mạnh ở chỗ dùng được
`WHERE`, `JOIN`, `ORDER BY` như mọi truy vấn khác: hợp cho script tự động, kiểm tra schema trong CI,
sinh tài liệu.

| Bảng | Chứa gì |
|---|---|
| `SCHEMATA` | Các database: charset, collation mặc định |
| `TABLES` | Bảng và view: `TABLE_TYPE`, `ENGINE`, `TABLE_ROWS`, `DATA_LENGTH`, `INDEX_LENGTH`, `AUTO_INCREMENT`, `TABLE_COLLATION`, `TABLE_COMMENT` |
| `COLUMNS` | Cột: `COLUMN_TYPE`, `IS_NULLABLE`, `COLUMN_DEFAULT`, `COLUMN_KEY`, `EXTRA`, `GENERATION_EXPRESSION`... |
| `STATISTICS` | Index, mỗi dòng là một cột trong một index |
| `TABLE_CONSTRAINTS` | Ràng buộc của mỗi bảng: `CONSTRAINT_TYPE` là `PRIMARY KEY`, `UNIQUE`, `FOREIGN KEY` hoặc `CHECK`; cột `ENFORCED` |
| `KEY_COLUMN_USAGE` | Cột thuộc PK, UNIQUE, FK, kèm bảng và cột được tham chiếu (`REFERENCED_TABLE_NAME`, `REFERENCED_COLUMN_NAME`) |
| `REFERENTIAL_CONSTRAINTS` | Khoá ngoại: `UPDATE_RULE`, `DELETE_RULE` |
| `CHECK_CONSTRAINTS` | Biểu thức của từng CHECK (`CHECK_CLAUSE`) |

Các lệnh `SHOW` tương ứng để tra nhanh: `SHOW TABLES`, `SHOW COLUMNS FROM t` (hay `DESCRIBE t`),
`SHOW INDEX FROM t`, `SHOW TABLE STATUS`, và `SHOW CREATE TABLE t` (không có bảng tương đương trực
tiếp trong `information_schema`).

### 11.2 Các truy vấn hay dùng

Các cột của một bảng, đúng thứ tự định nghĩa (tài liệu MySQL lưu ý: khác `SHOW COLUMNS`, truy vấn
`COLUMNS` không tự sắp xếp, nên cần `ORDER BY ORDINAL_POSITION`):

```sql
SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'lab04' AND TABLE_NAME = 'orders'
ORDER BY ORDINAL_POSITION;
```

```text
-- output minh hoạ
+-------------+-----------------+-------------+-------------------+-------------------+
| COLUMN_NAME | COLUMN_TYPE     | IS_NULLABLE | COLUMN_DEFAULT    | EXTRA             |
+-------------+-----------------+-------------+-------------------+-------------------+
| id          | bigint unsigned | NO          | NULL              | auto_increment    |
| user_id     | bigint unsigned | NO          | NULL              |                   |
| coupon_id   | int unsigned    | YES         | NULL              |                   |
| status      | varchar(20)     | NO          | pending           |                   |
| total       | decimal(12,2)   | NO          | 0.00              |                   |
| created_at  | datetime        | NO          | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+-------------+-----------------+-------------+-------------------+-------------------+
```

Bảng nào đang trỏ khoá ngoại tới `users`? Câu hỏi bắt buộc phải trả lời trước khi đổi kiểu cột
`users.id` hay xoá bảng `users`:

```sql
SELECT TABLE_NAME, COLUMN_NAME, CONSTRAINT_NAME, REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE REFERENCED_TABLE_SCHEMA = 'lab04'
  AND REFERENCED_TABLE_NAME = 'users'
ORDER BY TABLE_NAME;
-- orders  | user_id | fk_orders_user  | id
-- reviews | user_id | fk_reviews_user | id
```

Hành động `ON DELETE`/`ON UPDATE` của mọi khoá ngoại trong database:

```sql
SELECT TABLE_NAME, CONSTRAINT_NAME, REFERENCED_TABLE_NAME, UPDATE_RULE, DELETE_RULE
FROM information_schema.REFERENTIAL_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'lab04'
ORDER BY TABLE_NAME, CONSTRAINT_NAME;
-- Dòng của fk_items_order có DELETE_RULE = 'CASCADE'.
```

Tìm bảng **không có primary key** (mục 4.5). Tạo thử một bảng thiếu PK để thấy kết quả:

```sql
CREATE TABLE audit_logs (message VARCHAR(255) NOT NULL);

SELECT t.TABLE_NAME
FROM information_schema.TABLES t
LEFT JOIN information_schema.TABLE_CONSTRAINTS c
       ON c.TABLE_SCHEMA = t.TABLE_SCHEMA
      AND c.TABLE_NAME = t.TABLE_NAME
      AND c.CONSTRAINT_TYPE = 'PRIMARY KEY'
WHERE t.TABLE_SCHEMA = 'lab04'
  AND t.TABLE_TYPE = 'BASE TABLE'
  AND c.CONSTRAINT_NAME IS NULL;
-- audit_logs

DROP TABLE audit_logs;
```

Liệt kê các CHECK cùng trạng thái thực thi. Nối hai bảng theo tên ràng buộc là an toàn vì tên CHECK
duy nhất trong một database (mục 4.7.3):

```sql
SELECT tc.TABLE_NAME, cc.CONSTRAINT_NAME, cc.CHECK_CLAUSE, tc.ENFORCED
FROM information_schema.CHECK_CONSTRAINTS cc
JOIN information_schema.TABLE_CONSTRAINTS tc
  ON tc.CONSTRAINT_SCHEMA = cc.CONSTRAINT_SCHEMA
 AND tc.CONSTRAINT_NAME   = cc.CONSTRAINT_NAME
 AND tc.CONSTRAINT_TYPE   = 'CHECK'
WHERE cc.CONSTRAINT_SCHEMA = 'lab04'
ORDER BY tc.TABLE_NAME, cc.CONSTRAINT_NAME;
```

Dung lượng từng bảng:

```sql
SELECT TABLE_NAME, ENGINE, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'lab04' AND TABLE_TYPE = 'BASE TABLE'
ORDER BY DATA_LENGTH + INDEX_LENGTH DESC;
```

### 11.3 Cạm bẫy khi đọc information_schema

⚠️ `TABLE_ROWS` **không phải** số dòng chính xác với InnoDB. Tài liệu MySQL: đó chỉ là ước lượng thô
phục vụ optimizer, có thể lệch tới 40% đến 50% so với thực tế. Cần số chính xác thì `SELECT COUNT(*)`.

⚠️ Các cột thống kê của `TABLES` (như `TABLE_ROWS`, `DATA_LENGTH`, `INDEX_LENGTH`, `AUTO_INCREMENT`)
là giá trị được **cache**. Biến `information_schema_stats_expiry` (mặc định 86400 giây, tức 24 giờ)
quy định bao lâu thì cache hết hạn. Vì vậy bạn vừa insert hàng nghìn dòng mà số liệu không đổi là bình
thường. Muốn số mới: chạy `ANALYZE TABLE tên_bảng` để cập nhật cache cho bảng đó, hoặc
`SET SESSION information_schema_stats_expiry = 0` để luôn lấy trực tiếp từ storage engine.

⚠️ `TABLES` không liệt kê temporary table, và `SHOW TABLES` cũng vậy (mục 10.2).

⚠️ So sánh tên trong `WHERE` tuân theo quy tắc chữ hoa chữ thường của tên bảng trên hệ điều hành đó
(mục 2.5). Viết tên đúng như lúc tạo là cách an toàn.

## 12. Đối chiếu PostgreSQL

Những khác biệt về DDL và ràng buộc mà người dùng MySQL hay vấp khi chuyển sang PostgreSQL (và ngược
lại). Phần lớn đã được nhắc rải rác trong chương; bảng dưới gom lại.

| Chủ đề | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| `DATABASE` và `SCHEMA` | Đồng nghĩa | Một database chứa nhiều schema |
| Storage engine | Chọn theo từng bảng (`ENGINE=`) | Không có khái niệm tương đương thường dùng |
| Id tự tăng | `AUTO_INCREMENT` | `GENERATED ... AS IDENTITY` (dựa trên sequence), kiểu cũ `SERIAL` |
| `REFERENCES` viết trong định nghĩa cột | Bị bỏ qua im lặng | Tạo khoá ngoại bình thường |
| Index cho cột FK ở bảng con | Tự tạo nếu chưa có | **Không** tự tạo; tài liệu PostgreSQL khuyên thường nên tạo |
| `ON DELETE SET DEFAULT` | InnoDB từ chối | Hỗ trợ |
| `NO ACTION` khác `RESTRICT`? | Không, như nhau, kiểm tra ngay | Có: `NO ACTION` cho phép hoãn kiểm tra tới cuối transaction nếu ràng buộc `DEFERRABLE`; `RESTRICT` thì không |
| Ràng buộc `DEFERRABLE` | Không có | Có cho `UNIQUE`, `PRIMARY KEY`, `EXCLUDE`, khoá ngoại (không cho `NOT NULL`, `CHECK`) |
| `CHECK` | Thực thi từ 8.0.16 | Thực thi |
| Generated column | `VIRTUAL` (mặc định) và `STORED`; được tham chiếu generated column đứng trước | `STORED` (từ bản 12) và `VIRTUAL` (từ bản 18, thành mặc định); không được tham chiếu generated column khác |
| Unique với NULL | Nhiều NULL không bị coi là trùng | Như MySQL theo mặc định; thêm `NULLS NOT DISTINCT` để coi các NULL là trùng |
| Unique có điều kiện | Mẹo generated column (mục 6.4) | Partial unique index (`... WHERE deleted_at IS NULL`) |
| DDL trong transaction | Không: DDL gây implicit commit | Có, phần lớn DDL rollback được |
| `TRUNCATE` | Implicit commit, không rollback được | Rollback được nếu transaction không commit; có `CASCADE`, `RESTART IDENTITY` |
| `DROP TABLE ... CASCADE` | Từ khoá không có tác dụng | Xoá các đối tượng phụ thuộc (view; với khoá ngoại thì chỉ xoá ràng buộc) |
| Metadata | `information_schema` | `information_schema` và `pg_catalog` |

Chi tiết hơn ở [chương 25](25-postgres-doi-chieu.md).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Viết `user_id ... REFERENCES users(id)` trong định nghĩa cột và tưởng đã có khoá ngoại | MySQL 8.4 phân tích rồi bỏ qua inline `REFERENCES`, không báo gì | Luôn viết `CONSTRAINT fk_... FOREIGN KEY (...) REFERENCES ...` riêng; kiểm tra bằng `SHOW CREATE TABLE` |
| `MODIFY` cột để đổi độ dài, cột mất `NOT NULL`/`DEFAULT`/`COMMENT` | Thuộc tính không ghi lại trong `MODIFY`/`CHANGE` thì không được giữ | Chép định nghĩa từ `SHOW CREATE TABLE`; chỉ đổi tên thì dùng `RENAME COLUMN`, chỉ đổi default thì dùng `ALTER COLUMN` |
| `UNIQUE (email, deleted_at)` để chặn trùng email với soft delete | Unique coi các NULL là khác nhau | Generated column + unique (mục 6.4), hoặc partial index trên PostgreSQL |
| Khoá ngoại báo lỗi 3780 | Cột con `INT`/`BIGINT` có dấu, cột cha `BIGINT UNSIGNED` | Cùng kiểu, cùng dấu (`foreignId()` trong Laravel) |
| Ghi `NULL` tường minh rồi mong cột nhận `DEFAULT` | `NULL` là một giá trị, không kích hoạt default | Bỏ cột khỏi `INSERT` hoặc ghi từ khoá `DEFAULT` |
| Tin rằng `ROLLBACK` huỷ được `ALTER`, `TRUNCATE`, `DROP` | DDL gây implicit commit; atomic DDL không phải transactional DDL | Không chạy DDL trong transaction nghiệp vụ; mỗi migration một thay đổi; có backup |
| Dùng `TRUNCATE` thay `DELETE` trên bảng có trigger hoặc cần rollback | `TRUNCATE` là DDL, không chạy trigger `ON DELETE`, không rollback được | Dùng `DELETE` khi cần ngữ nghĩa từng dòng |
| `ON DELETE CASCADE` từ `users` xuống dữ liệu lịch sử | Một lệnh xoá kéo theo hàng loạt dòng, không trigger, không event ORM | `RESTRICT` kèm soft delete; xoá theo lô bằng job |
| Bật lại `foreign_key_checks` và nghĩ dữ liệu đã được kiểm tra | Bật lại không quét dữ liệu đã nạp | Chỉ tắt khi nạp dữ liệu nguồn đã đúng; tự đối soát bằng `LEFT JOIN ... IS NULL` |
| Dùng `SELECT MAX(id)` để lấy id vừa insert | Người khác có thể insert xen giữa | `LAST_INSERT_ID()` / `PDO::lastInsertId()` |
| Đọc `TABLE_ROWS` như số dòng thật | Với InnoDB chỉ là ước lượng, lại còn được cache | `SELECT COUNT(*)` khi cần số chính xác |
| Cột `AUTO_INCREMENT` kiểu `INT` cho bảng tăng nhanh | Hết số thì mọi insert đều thất bại | `BIGINT UNSIGNED` cho bảng có thể lớn |
| Code chạy trên macOS nhưng lỗi "bảng không tồn tại" trên Linux | Tên bảng phân biệt hoa thường trên Linux | Tên viết thường, snake_case, nhất quán |

## Tóm tắt chương

- DDL (`CREATE`, `ALTER`, `DROP`, `RENAME`, `TRUNCATE`) định nghĩa schema; `SHOW CREATE TABLE` cho biết
  server đã thật sự hiểu định nghĩa của bạn thế nào.
- Charset/collation kế thừa server → database → bảng → cột; `ALTER DATABASE` và `DEFAULT CHARACTER SET`
  chỉ đổi mặc định cho đối tượng tạo sau, `CONVERT TO` mới chuyển dữ liệu đang có.
- Dùng InnoDB cho mọi bảng; mọi bảng có primary key tường minh, ngắn và không đổi.
- Ràng buộc trong database là tuyến phòng thủ cuối cùng, chặn cả bug lẫn race condition mà validate ở
  app không chặn được. Đặt tên cho ràng buộc.
- `NOT NULL` gần như mặc định nên dùng; `UNIQUE` cho phép nhiều NULL; `CHECK` (thực thi từ 8.0.16) chỉ
  chặn kết quả FALSE, UNKNOWN được cho qua.
- Khoá ngoại: kiểu cột phải khớp, cột cha phải là PK/UNIQUE, InnoDB tự tạo index ở bảng con; inline
  `REFERENCES` bị bỏ qua; `NO ACTION` = `RESTRICT` trong InnoDB; cascade không chạy trigger.
- `AUTO_INCREMENT` luôn có lỗ (rollback, insert lỗi, cấp dư), bộ đếm bền qua restart từ 8.0;
  `LAST_INSERT_ID()` tính theo từng kết nối.
- Generated column (`VIRTUAL` mặc định, `STORED`) giữ giá trị suy ra luôn đúng và index được; dùng nó
  để làm unique có điều kiện.
- `TRUNCATE` là DDL: nhanh, reset bộ đếm, không rollback, không trigger, không chạy khi bị FK trỏ tới.
- Trong MySQL, DDL gây implicit commit; mỗi câu DDL atomic nhưng không gom được vào transaction. Đọc
  metadata qua `information_schema`, nhớ rằng số liệu thống kê là ước lượng và được cache.

## Câu hỏi tự kiểm tra

1. Vì sao kiểm tra "email đã tồn tại chưa" trong code ứng dụng không thay được ràng buộc `UNIQUE`? Hãy
   vẽ timeline hai request. (mục 4.1)
2. Lỗi 1048 và lỗi 1364 khác nhau thế nào? Khi strict mode bị tắt, câu lệnh gây lỗi 1364 sẽ ra kết quả
   gì? (mục 4.2)
3. Bảng có `UNIQUE (user_id, phone)` với `phone` cho phép NULL. Chèn hai lần `(1, NULL)` thì sao, và vì
   sao?
4. Bạn viết `user_id BIGINT UNSIGNED NOT NULL REFERENCES users(id)` trên MySQL 8.4. Insert
   `user_id = 999` (không tồn tại) thì chuyện gì xảy ra? Làm sao phát hiện vấn đề? (mục 4.6.3)
5. `CHECK (sale_price < price)` có chặn dòng có `sale_price = NULL` không? So sánh với cách `WHERE`
   đối xử với cùng biểu thức.
6. Vì sao InnoDB không trả lại id `AUTO_INCREMENT` khi transaction rollback? Hệ quả với một tiến trình
   đọc dữ liệu mới theo kiểu `id > mốc_cuối`? (mục 5.2)
7. `ALTER TABLE t MODIFY c BIGINT` trên cột đang là `INT UNSIGNED NOT NULL DEFAULT 1` cho ra cột thế nào?
8. So sánh `DELETE FROM t`, `TRUNCATE TABLE t`, `DROP TABLE t` theo: rollback, trigger, khoá ngoại, bộ
   đếm `AUTO_INCREMENT`.
9. Trong một transaction đang mở, bạn chạy `INSERT` rồi `CREATE INDEX`, rồi `ROLLBACK`. Dòng vừa insert
   còn không? "Atomic DDL" có giúp gì ở đây không? (mục 9.3)
10. Vì sao `TABLE_ROWS` trong `information_schema.TABLES` có thể không đổi sau khi bạn vừa insert nhiều
    dòng?

## Bài tập

1. **Schema có ràng buộc đầy đủ.** Trong database mới `ex04`, viết `CREATE TABLE` cho `customers`,
   `products`, `orders`, `order_items` sao cho: email khách không trùng (không phân biệt hoa thường);
   giá và số lượng không âm, số lượng ít nhất 1; trạng thái đơn chỉ thuộc
   `('pending', 'paid', 'shipped', 'cancelled')`; xoá đơn thì xoá chi tiết đơn; không xoá được sản phẩm
   đã có trong đơn; mỗi sản phẩm xuất hiện tối đa một lần trong một đơn. Viết thêm các câu `INSERT` cố
   tình vi phạm từng luật và ghi lại mã lỗi nhận được.
2. **Truy vấn metadata.** Viết các truy vấn `information_schema` để: (a) liệt kê mọi khoá ngoại trong
   `ex04` kèm `DELETE_RULE`; (b) tìm các cặp cột khoá ngoại có `COLUMN_TYPE` khác cột được tham chiếu
   (gợi ý: nối `KEY_COLUMN_USAGE` với `COLUMNS` hai lần); (c) tìm cột cho phép NULL mà tên kết thúc bằng
   `_id`.
3. **Migration an toàn bằng tay.** Bảng `customers` đã có dữ liệu. Thêm cột `phone` sao cho cuối cùng
   cột là `NOT NULL` và duy nhất, với các bước: thêm cột cho phép NULL, điền dữ liệu, kiểm tra trùng,
   chuyển sang `NOT NULL`, thêm `UNIQUE`. Sau mỗi bước chạy `SHOW CREATE TABLE` để kiểm tra không mất
   thuộc tính nào.
4. **Thí nghiệm implicit commit và AUTO_INCREMENT.** Mở hai session `mysql`. Lặp lại timeline ở mục 5.2
   và mục 9.1, ghi lại id được cấp và kết quả `SELECT` ở từng bước. Sau đó thử `TRUNCATE` trong một
   transaction đang có `INSERT` chưa commit, rồi `ROLLBACK`, và giải thích kết quả.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [CREATE DATABASE](https://dev.mysql.com/doc/refman/8.4/en/create-database.html) ·
  [CREATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/create-table.html) ·
  [FOREIGN KEY Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html) ·
  [CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html) ·
  [Generated Columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-generated-columns.html) ·
  [Secondary Indexes and Generated Columns](https://dev.mysql.com/doc/refman/8.4/en/create-table-secondary-indexes.html) ·
  [Generated Invisible Primary Keys](https://dev.mysql.com/doc/refman/8.4/en/create-table-gipks.html) ·
  [Data Type Default Values](https://dev.mysql.com/doc/refman/8.4/en/data-type-defaults.html) ·
  [AUTO_INCREMENT Handling in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html) ·
  [ALTER TABLE](https://dev.mysql.com/doc/refman/8.4/en/alter-table.html) ·
  [RENAME TABLE](https://dev.mysql.com/doc/refman/8.4/en/rename-table.html) ·
  [DROP TABLE](https://dev.mysql.com/doc/refman/8.4/en/drop-table.html) ·
  [TRUNCATE TABLE](https://dev.mysql.com/doc/refman/8.4/en/truncate-table.html) ·
  [Statements That Cause an Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html) ·
  [Atomic DDL](https://dev.mysql.com/doc/refman/8.4/en/atomic-ddl.html) ·
  [CREATE TEMPORARY TABLE](https://dev.mysql.com/doc/refman/8.4/en/create-temporary-table.html) ·
  [TEMPORARY Table Problems](https://dev.mysql.com/doc/refman/8.4/en/temporary-table-problems.html) ·
  [INFORMATION_SCHEMA](https://dev.mysql.com/doc/refman/8.4/en/information-schema-introduction.html) ·
  [Identifier Case Sensitivity](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html) ·
  [Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) ·
  [Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html)
- [MySQL 8.4 Error Message Reference](https://dev.mysql.com/doc/mysql-errors/8.4/en/server-error-reference.html)
- PostgreSQL 18:
  [Constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) ·
  [Generated Columns](https://www.postgresql.org/docs/18/ddl-generated-columns.html) ·
  [Identity Columns](https://www.postgresql.org/docs/18/ddl-identity-columns.html) ·
  [TRUNCATE](https://www.postgresql.org/docs/18/sql-truncate.html)
- Laravel 13.x: [Migrations](https://laravel.com/docs/13.x/migrations) ·
  [Database: Implicit Commits](https://laravel.com/docs/13.x/database#implicit-commits-in-transactions)
