# Chương 01. Database là gì và cài đặt MySQL

> [← Mục lục](README.md) · [Chương 02: Mô hình quan hệ và thiết kế dữ liệu →](02-mo-hinh-quan-he-thiet-ke.md)

**Bạn sẽ học được:**

- Vì sao ứng dụng cần một database thay vì tự ghi dữ liệu ra file, và một DBMS làm giúp bạn những việc gì.
- Mô hình quan hệ (bảng, dòng, cột), SQL là gì và bốn nhóm lệnh DDL, DML, DCL, TCL.
- Các hệ quản trị phổ biến (MySQL, PostgreSQL, SQLite, SQL Server, Oracle) khác nhau ở đâu, và khi
  nào người ta nghĩ tới NoSQL.
- Kiến trúc client-server: server MySQL, client, kết nối qua TCP hay qua Unix socket.
- Cài MySQL 8.4 bằng Docker hoặc Homebrew, kết nối bằng chương trình `mysql`.
- Tạo database đầu tiên và khám phá nó bằng `SHOW DATABASES`, `SHOW TABLES`, `DESCRIBE`,
  `SHOW CREATE TABLE`.

**Cần biết trước:** không cần gì. Biết mở terminal và gõ lệnh là đủ. Vài ví dụ PHP trong chương chỉ
để minh hoạ, đọc hiểu được là được.

## 1. Dữ liệu và vì sao cần database

### 1.1 Dữ liệu là gì

*Dữ liệu* (data) là các sự việc được ghi lại: "khách hàng An có email an@example.com", "đơn hàng số
17 trị giá 250.000đ, tạo lúc 9 giờ sáng nay". Gần như mọi ứng dụng backend tồn tại để làm ba việc với
dữ liệu: nhận vào, lưu lại, rồi trả ra đúng phần người dùng cần.

Phần "lưu lại" là phần khó. Biến trong PHP chỉ sống trong một request: request kết thúc là biến mất.
Dữ liệu của ứng dụng phải sống lâu hơn request, lâu hơn tiến trình PHP, và còn nguyên sau khi server
khởi động lại. Dữ liệu như vậy gọi là dữ liệu *persistent* (bền vững), và muốn bền thì cuối cùng nó
phải nằm trên ổ đĩa.

Câu hỏi của cả mục này: ghi dữ liệu xuống đĩa bằng cách nào cho đúng?

### 1.2 Cách đơn giản nhất: tự ghi ra file

Cách đầu tiên ai cũng nghĩ tới là ghi ra một file (CSV, JSON...). Muốn đọc thì mở file. Muốn sửa thì
đọc cả file vào RAM, sửa, rồi ghi đè lại cả file. Thử làm một "database" tài khoản như vậy:

```php
<?php
declare(strict_types=1);

// "Database" tự chế: toàn bộ dữ liệu nằm trong một file JSON cạnh script.
$file = __DIR__ . '/accounts.json';
file_put_contents($file, json_encode([
    ['id' => 1, 'name' => 'An', 'balance' => 500],
    ['id' => 2, 'name' => 'Binh', 'balance' => 300],
], JSON_THROW_ON_ERROR));

/** @return list<array{id: int, name: string, balance: int}> */
function loadAll(string $file): array
{
    return json_decode((string) file_get_contents($file), true, 512, JSON_THROW_ON_ERROR);
}

/** @param list<array{id: int, name: string, balance: int}> $rows */
function saveAll(string $file, array $rows): void
{
    file_put_contents($file, json_encode($rows, JSON_THROW_ON_ERROR));
}

// Hai request tới gần như cùng lúc. Mỗi request: đọc cả file -> sửa trong RAM -> ghi đè cả file.
// Request A nạp thêm 100 cho An, request B trừ 50 của An. Thứ tự xen kẽ dưới đây hoàn toàn có thể
// xảy ra khi hai tiến trình PHP-FPM chạy song song:
$a = loadAll($file);        // A đọc: balance của An = 500
$b = loadAll($file);        // B đọc: cũng thấy 500 vì A chưa ghi
$a[0]['balance'] += 100;    // A tính: 600
saveAll($file, $a);         // A ghi file: 600
$b[0]['balance'] -= 50;     // B tính trên bản cũ: 500 - 50 = 450
saveAll($file, $b);         // B ghi đè cả file: 450

echo loadAll($file)[0]['balance'], PHP_EOL; // in ra: 450 (đúng phải là 550, khoản +100 của A biến mất)
```

Lưu thành `luu-file.php` rồi chạy `php luu-file.php`. Máy chưa có PHP thì chạy trong Docker, đứng ở
thư mục chứa file:
`docker run --rm -v "$PWD":/app -w /app php:8.5-cli php luu-file.php`.

Từng dòng code đều đúng, chương trình không báo lỗi gì, vậy mà số dư của An sai. Đây là lỗi *lost
update* (mất cập nhật): hai bên cùng đọc một giá trị cũ, cùng tính toán trên giá trị đó, rồi cùng ghi
lại; bên ghi sau xoá mất kết quả của bên ghi trước.

| Bước | Request A (+100) | Request B (-50) | Giá trị trong file |
|---|---|---|---|
| 1 | đọc file, thấy 500 | | 500 |
| 2 | | đọc file, thấy 500 | 500 |
| 3 | tính 600, ghi file | | 600 |
| 4 | | tính 450, ghi đè file | 450 ⚠️ mất khoản +100 |

Ở đây ta xếp hai request xen kẽ bằng tay cho dễ thấy. Trên server thật, PHP-FPM chạy nhiều tiến trình
song song, nên thứ tự như trên xảy ra một cách ngẫu nhiên: thỉnh thoảng mới gặp, gặp rồi cũng rất khó
tái hiện khi debug. Đó là loại lỗi tệ nhất.

### 1.3 Những vấn đề của việc tự quản lý file

Lost update mới chỉ là vấn đề đầu tiên. Khi ứng dụng lớn dần, cách lưu file tự quản lý lần lượt gặp
những vấn đề sau:

| Vấn đề | Chuyện gì xảy ra với file tự quản lý | Database giải quyết bằng gì |
|---|---|---|
| Nhiều người cùng ghi | Lost update như trên. Muốn tránh phải tự khoá file (`flock()`, cờ `LOCK_EX`) ở mọi chỗ đọc và ghi; quên một chỗ là hỏng | Kiểm soát đồng thời: lock, MVCC ([chương 14](14-isolation-mvcc.md), [chương 15](15-lock-deadlock.md)) |
| Server sập giữa chừng | `file_put_contents()` mở file ở chế độ ghi, chế độ này cắt file về rỗng trước khi ghi nội dung mới. Sập đúng lúc đó là file rỗng hoặc dở dang, mất sạch dữ liệu | Log ghi trước và cơ chế phục hồi sau sự cố ([chương 16](16-ben-trong-innodb.md)) |
| Nhiều thay đổi phải đi cùng nhau | Chuyển tiền: trừ tài khoản A rồi cộng tài khoản B. Sập giữa hai bước là tiền bốc hơi | Transaction: hoặc tất cả, hoặc không gì cả ([chương 13](13-transaction-acid.md)) |
| Tìm kiếm | Muốn tìm một khách theo email phải đọc và duyệt toàn bộ file. File 1 GB thì mỗi lần tìm đọc 1 GB | Index ([chương 11](11-index.md)) |
| Dữ liệu sai | Không có gì ngăn một đoạn code ghi `"balance": -999`, hai khách trùng email, hay `"balance": "abc"` | Kiểu dữ liệu và ràng buộc ([chương 03](03-kieu-du-lieu.md), [chương 04](04-ddl-constraint.md)) |
| Liên kết giữa các tập dữ liệu | Đơn hàng trỏ tới một khách hàng đã bị xoá mà không ai hay | Khoá ngoại ([chương 04](04-ddl-constraint.md)) |
| Phân quyền | Ai đọc được file là đọc được tất cả | User và quyền tới từng database, bảng, thậm chí từng cột ([chương 18](18-user-quyen-bao-mat.md)) |
| Nhiều ứng dụng dùng chung | Mỗi ứng dụng (web, worker, báo cáo) phải hiểu định dạng file và tự viết lại logic đọc ghi, khoá | Mọi ứng dụng nói cùng một ngôn ngữ (SQL) với cùng một server |

Còn một chi tiết ít người để ý: khi `file_put_contents()` trả về, dữ liệu thường mới nằm trong bộ nhớ
đệm của hệ điều hành, chưa chắc đã xuống tới đĩa. Mất điện ngay lúc đó vẫn mất dữ liệu. Muốn chắc
chắn phải gọi thêm lệnh ép ghi xuống đĩa (`fsync`), và làm việc đó đúng lúc, đúng chỗ là một bài toán
riêng.

Bạn hoàn toàn có thể vá từng lỗi: thêm `flock()`, ghi ra file tạm rồi đổi tên đè lên file cũ, tự viết
cấu trúc tra cứu nhanh, tự viết cơ chế phục hồi... Làm hết những việc đó cho đúng, nhanh, và chịu được
sự cố, thì bạn đã tự viết ra một hệ quản trị cơ sở dữ liệu. Đó là thứ mà các đội phát triển MySQL,
PostgreSQL, SQLite đã mất hàng chục năm để làm cho đúng. Ta dùng lại thành quả của họ.

### 1.4 Database và DBMS

Hai khái niệm hay bị dùng lẫn:

- *Database* (cơ sở dữ liệu): một tập dữ liệu có tổ chức, được lưu trữ bền vững, phục vụ một hoặc
  nhiều ứng dụng. Ví dụ: database `shop` chứa khách hàng, sản phẩm, đơn hàng của một cửa hàng.
- *DBMS* (Database Management System, hệ quản trị cơ sở dữ liệu): phần mềm quản lý database. Nó lưu
  trữ dữ liệu, nhận và thực thi yêu cầu truy vấn, bảo đảm an toàn khi nhiều người dùng cùng lúc, phục
  hồi sau sự cố. MySQL, PostgreSQL, SQLite là các DBMS.

Câu "MySQL là một database" là cách nói tắt quen miệng. Nói chính xác thì MySQL là một DBMS, và một
server MySQL quản lý nhiều database cùng lúc (xem mục 9). Khi dùng DBMS, ứng dụng không đụng trực tiếp
vào file dữ liệu nữa: nó gửi yêu cầu cho DBMS, DBMS lo phần còn lại.

```
   Ứng dụng PHP                   DBMS (ví dụ MySQL)                    Ổ đĩa
 +------------------+  yêu cầu  +------------------------------+     +--------------+
 | "cộng 100 vào    | --------> | phân tích, chọn cách thực thi |     | file dữ liệu |
 |  tài khoản số 1" |           | khoá, transaction             | <-> | file log     |
 |                  | <-------- | đọc ghi qua bộ nhớ đệm        |     |              |
 +------------------+  kết quả  +------------------------------+     +--------------+
```

Những việc một DBMS quan hệ như MySQL làm giúp bạn:

1. Lưu dữ liệu theo cấu trúc đã khai báo, kiểm tra kiểu và ràng buộc trước khi ghi.
2. Cho bạn một ngôn ngữ truy vấn (SQL) để nói "cần dữ liệu gì", thay vì tự viết vòng lặp duyệt file.
3. Tìm nhanh nhờ index, tự chọn cách thực thi câu truy vấn hiệu quả.
4. Kiểm soát đồng thời: nhiều kết nối cùng đọc ghi mà không giẫm lên nhau.
5. Transaction: gom nhiều thay đổi thành một khối, hoặc thành công hết, hoặc huỷ hết.
6. Phục hồi sau sự cố: server sập rồi khởi động lại, dữ liệu đã xác nhận ghi (commit) vẫn còn.
7. Bảo mật: tài khoản, mật khẩu, phân quyền.
8. Công cụ vận hành: sao lưu, nhân bản dữ liệu sang máy khác (replication), giám sát.

Cùng bài toán tài khoản ở trên, giờ giao cho một DBMS. Để chạy được ngay mà không cần cài server, ví dụ
dùng SQLite, một DBMS nhỏ chạy ngay bên trong tiến trình PHP (mục 4.3). PDO là lớp truy cập database
có sẵn của PHP, sẽ học kỹ ở [chương 19](19-database-tu-ung-dung.md).

```php
<?php
declare(strict_types=1);

// SQLite là một DBMS dạng nhúng: không cần server, chạy ngay trong tiến trình PHP.
// 'sqlite::memory:' tạo database trong RAM, mất khi script kết thúc.
$pdo = new PDO('sqlite::memory:');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION); // từ PHP 8.0 đây đã là mặc định

// Mô tả cấu trúc dữ liệu một lần. CHECK là một ràng buộc: số dư không được âm.
$pdo->exec('CREATE TABLE accounts (
    id      INTEGER PRIMARY KEY,
    name    TEXT    NOT NULL,
    balance INTEGER NOT NULL CHECK (balance >= 0)
)');
$pdo->exec("INSERT INTO accounts (id, name, balance) VALUES (1, 'An', 500), (2, 'Binh', 300)");

// Không còn "đọc cả file, sửa, ghi đè". Ta nói với DBMS cần thay đổi gì,
// DBMS tự tìm đúng dòng, tự đọc-sửa-ghi dòng đó.
$pdo->exec('UPDATE accounts SET balance = balance + 100 WHERE id = 1');
$pdo->exec('UPDATE accounts SET balance = balance - 50 WHERE id = 1');
echo $pdo->query('SELECT balance FROM accounts WHERE id = 1')->fetchColumn(), PHP_EOL;
// in ra: 550

// Thử làm số dư của Binh thành âm: DBMS từ chối cả câu lệnh.
try {
    $pdo->exec('UPDATE accounts SET balance = balance - 1000 WHERE id = 2');
} catch (PDOException $e) {
    echo $e->getMessage(), PHP_EOL;
    // in ra: SQLSTATE[23000]: Integrity constraint violation: 19 CHECK constraint failed: balance >= 0
}
echo $pdo->query('SELECT balance FROM accounts WHERE id = 2')->fetchColumn(), PHP_EOL;
// in ra: 300 (dữ liệu giữ nguyên)
```

So với bản dùng file, có ba khác biệt đáng chú ý:

- Ứng dụng không còn đọc cả "file" vào RAM để sửa một con số. Câu `UPDATE ... SET balance = balance +
  100` mô tả thay đổi, DBMS thực hiện nó trên đúng một dòng. Khi hai kết nối cùng chạy câu như vậy
  trên cùng một dòng, DBMS bắt câu sau chờ câu trước xong (bằng lock), câu sau tính trên giá trị câu
  trước đã ghi, nên không còn lost update. Script trên chỉ có một kết nối nên không cho thấy điều này;
  [chương 15](15-lock-deadlock.md) sẽ dựng lại cảnh hai kết nối tranh nhau.
- Quy tắc "số dư không âm" được khai báo một lần ở database, có hiệu lực với mọi đoạn code, mọi ứng
  dụng ghi vào. Không ai "quên kiểm tra" được nữa.
- Câu lệnh vi phạm bị từ chối nguyên vẹn: dữ liệu giữ như cũ chứ không bị ghi dở.

⚠️ Chuyển sang database không tự động hết lost update. Nếu bạn vẫn viết theo kiểu cũ: `SELECT` số dư
lên PHP, cộng trong PHP, rồi `UPDATE ... SET balance = 600`, thì hai request vẫn có thể giẫm lên nhau y
như với file. Cách viết đúng và các cách chống lost update được bàn ở [chương 14](14-isolation-mvcc.md)
và [chương 15](15-lock-deadlock.md).

### 1.5 Khi nào file vẫn là lựa chọn đúng

Database không thay thế file trong mọi trường hợp:

- Log của ứng dụng: chủ yếu ghi nối vào cuối, hiếm khi sửa, thường ghi ra file hoặc đẩy vào hệ thống
  log chuyên dụng.
- File người dùng tải lên (ảnh, video, PDF): thường lưu trên đĩa hoặc dịch vụ lưu trữ object (như
  Amazon S3); database chỉ lưu đường dẫn và thông tin mô tả (tên, kích thước, chủ sở hữu).
- File cấu hình, dữ liệu xuất ra một lần để gửi đi (báo cáo CSV).

Database đáng dùng khi dữ liệu được đọc ghi thường xuyên, nhiều nơi cùng truy cập, cần tìm kiếm theo
nhiều tiêu chí, và cần đúng. Đó là gần như toàn bộ dữ liệu nghiệp vụ của một ứng dụng backend.

## 2. Mô hình quan hệ: bảng, dòng, cột

Có nhiều cách tổ chức dữ liệu bên trong một DBMS. Cách phổ biến nhất trong các ứng dụng nghiệp vụ là
*mô hình quan hệ* (relational model), và DBMS dùng mô hình này gọi là *RDBMS* (Relational DBMS).
MySQL, PostgreSQL, SQLite, SQL Server, Oracle đều là RDBMS.

### 2.1 Bảng, dòng, cột

Database quan hệ chứa dữ liệu trong các *bảng* (table). Mỗi bảng mô tả một loại đối tượng: khách
hàng, đơn hàng, sản phẩm. Trong một bảng:

- mỗi *dòng* (row) là một đối tượng cụ thể: một khách hàng, một đơn hàng;
- mỗi *cột* (column) là một thuộc tính của đối tượng, có tên và có *kiểu dữ liệu* (data type) cố
  định: số nguyên, chuỗi, ngày giờ...

```
Bảng customers
+----+------+------------------+----------+
| id | name | email            | city     |   <- tên các cột
+----+------+------------------+----------+
|  1 | An   | an@example.com   | Hà Nội   |   <- một dòng = một khách hàng
|  2 | Bình | binh@example.com | Đà Nẵng  |
|  3 | Chi  | chi@example.com  | Hà Nội   |
+----+------+------------------+----------+
  cột id: số nguyên       cột email: chuỗi

Bảng orders
+----+-------------+--------+---------------------+
| id | customer_id | total  | created_at          |
+----+-------------+--------+---------------------+
| 10 |           1 | 250000 | 2026-10-01 09:00:00 |
| 11 |           1 |  90000 | 2026-10-02 14:30:00 |
| 12 |           3 | 120000 | 2026-10-02 15:00:00 |
+----+-------------+--------+---------------------+
```

Mỗi ô (giao của một dòng và một cột) chứa một giá trị. Nếu một khách hàng có ba số điện thoại, ta không
nhét cả ba vào một ô dạng `"090..., 091..., 098..."`; cách tổ chức đúng cho trường hợp đó là nội dung
của [chương 02](02-mo-hinh-quan-he-thiet-ke.md).

Nếu bạn quen với PHP: một bảng giống một mảng các mảng có cùng bộ key, mỗi dòng giống
`['id' => 1, 'name' => 'An', 'email' => 'an@example.com', 'city' => 'Hà Nội']`. Khác biệt là DBMS ép
mọi dòng phải có đúng bộ cột đó, đúng kiểu đó, và cho bạn công cụ để tìm, lọc, nối các bảng mà không
phải tự viết vòng lặp.

### 2.2 Thuật ngữ

Cùng một thứ có nhiều tên, tuỳ bạn đọc sách lý thuyết hay tài liệu thực hành:

| Lý thuyết quan hệ | Trong SQL | Cách gọi khác hay gặp |
|---|---|---|
| *relation* | table (bảng) | |
| *tuple* | row (dòng) | record (bản ghi) |
| *attribute* | column (cột) | field (trường) |
| *domain* (miền giá trị) | kiểu dữ liệu của cột, cộng các ràng buộc | |

Chữ "quan hệ" trong "database quan hệ" nghĩa là *relation*, tức là cái bảng, chứ không phải "mối quan
hệ giữa các bảng" như nhiều người vẫn nghĩ. Tài liệu PostgreSQL viết thẳng: relation về cơ bản là một
thuật ngữ toán học chỉ cái bảng.

Thêm một từ sẽ gặp liên tục: *schema*. Nghĩa thứ nhất là cấu trúc của dữ liệu: có những bảng nào, mỗi
bảng có cột gì, kiểu gì, ràng buộc gì. Câu "thay đổi schema" theo nghĩa này là thêm cột, đổi kiểu cột.
Nghĩa thứ hai, riêng trong MySQL, schema là tên khác của database (mục 9.1). Đọc theo ngữ cảnh để biết
đang nói nghĩa nào.

### 2.3 Khoá: các bảng liên kết với nhau thế nào

Nhìn lại hai bảng ở mục 2.1. Làm sao biết đơn hàng 10 là của ai? Cột `orders.customer_id` lưu giá trị
`1`, và trong bảng `customers` dòng có `id = 1` là An. Hai khái niệm làm việc này:

- *Primary key* (khoá chính): cột (hoặc nhóm cột) mà giá trị của nó xác định duy nhất một dòng trong
  bảng. `customers.id` là primary key: không có hai khách hàng cùng `id`, và dòng nào cũng phải có
  `id`.
- *Foreign key* (khoá ngoại): cột trong một bảng lưu giá trị primary key của một bảng khác, để "trỏ"
  sang dòng bên đó. `orders.customer_id` là foreign key trỏ tới `customers.id`.

Điểm cốt lõi của mô hình quan hệ: các bảng liên kết với nhau bằng giá trị. Đơn hàng không chứa con trỏ
bộ nhớ hay đường dẫn tới file của khách hàng, nó chỉ chứa con số `1`. Khi cần thông tin khách của đơn
hàng, ta ghép hai bảng lại lúc truy vấn bằng phép *JOIN* ([chương 07](07-join.md)). Nhờ vậy dữ liệu khách
hàng chỉ nằm ở một chỗ: An đổi email thì sửa đúng một dòng trong `customers`, mọi đơn hàng của An tự
động "thấy" email mới.

```
customers                         orders
+----+------+                     +----+-------------+
| id | name |                     | id | customer_id |
+----+------+                     +----+-------------+
|  1 | An   | <-------------------| 10 |           1 |
|    |      | <-------------------| 11 |           1 |
|  2 | Bình |                     |    |             |
|  3 | Chi  | <-------------------| 12 |           3 |
+----+------+                     +----+-------------+
 primary key                       foreign key
```

Chọn khoá thế nào, các loại quan hệ một-nhiều, nhiều-nhiều, và cách chia dữ liệu thành bảng là nội dung
của [chương 02](02-mo-hinh-quan-he-thiet-ke.md). Cú pháp khai báo khoá chính, khoá ngoại nằm ở
[chương 04](04-ddl-constraint.md).

### 2.4 Bốn tính chất cần nhớ ngay từ đầu

1. **Cấu trúc khai báo trước.** Bảng phải được tạo (có tên cột, kiểu cột) trước khi ghi dữ liệu vào.
   Dữ liệu không khớp cấu trúc bị DBMS từ chối hoặc chuyển đổi theo luật của kiểu dữ liệu
   ([chương 03](03-kieu-du-lieu.md)). Đây là khác biệt lớn với file JSON, nơi muốn ghi gì cũng được.
2. **Dòng không có thứ tự.** Một bảng là một tập hợp các dòng, không phải danh sách. Tài liệu
   PostgreSQL nhấn mạnh: SQL không bảo đảm thứ tự các dòng trong bảng theo bất kỳ cách nào; muốn có thứ
   tự thì phải yêu cầu sắp xếp khi truy vấn (`ORDER BY`). ⚠️ Câu `SELECT * FROM orders` có thể trả về
   theo thứ tự `id` tăng dần hàng trăm lần liên tiếp, rồi một ngày đổi thứ tự (sau khi thêm index, đổi
   phiên bản, dữ liệu lớn lên). Code nào cần thứ tự mà không có `ORDER BY` là code có lỗi chờ ngày phát
   tác.
3. **Mỗi ô một giá trị, và có thể "không có giá trị".** Ô chưa biết giá trị chứa `NULL`, một giá trị
   đặc biệt với luật so sánh riêng rất dễ gây lỗi ([chương 06](06-ham-bieu-thuc-null.md)).
4. **Cột có thứ tự nhưng đừng dựa vào nó.** `SELECT *` trả các cột theo thứ tự định nghĩa trong bảng,
   nhưng code nên luôn gọi cột bằng tên (`SELECT id, name ...`, `INSERT INTO t (id, name) ...`), để thêm hay đổi thứ tự cột
   sau này không làm hỏng code.

Một chi tiết cho người thích chính xác: bảng SQL không hoàn toàn giống relation trong toán học. Theo lý
thuyết, relation là một tập hợp nên không có hai tuple trùng nhau, và các attribute không có thứ tự.
Bảng SQL thì cho phép hai dòng giống hệt nhau (nếu bảng không có khoá), và cột có thứ tự. Đây là một
lý do nên cho mọi bảng một primary key.

### 2.5 Một chút lịch sử

Mô hình quan hệ được Edgar F. Codd, một nhà nghiên cứu của IBM, mô tả trong bài báo "A Relational
Model of Data for Large Shared Data Banks" (tạp chí Communications of the ACM, tháng 6/1970). Trước đó,
các hệ thống phổ biến tổ chức dữ liệu theo mô hình phân cấp (hierarchical) hoặc mô hình mạng (network):
chương trình phải tự đi theo các liên kết vật lý giữa các bản ghi để tìm dữ liệu, nên thay đổi cách lưu
trữ hay thêm một kiểu truy vấn mới thường kéo theo sửa chương trình. Ý tưởng của Codd là tách hẳn cách
dữ liệu được nhìn (các bảng và giá trị) khỏi cách nó được lưu trên đĩa, để người dùng hỏi được cả những
câu hỏi mà người thiết kế database chưa từng nghĩ tới. Hơn năm mươi năm sau, đây vẫn là lựa chọn mặc
định cho dữ liệu nghiệp vụ của phần lớn ứng dụng.

## 3. SQL là gì

### 3.1 Ngôn ngữ để nói chuyện với database

*SQL* (Structured Query Language) là ngôn ngữ chuẩn để làm việc với database quan hệ: tạo bảng, ghi,
đọc, sửa, xoá dữ liệu, phân quyền, điều khiển transaction. Có hai cách đọc đều phổ biến: đánh vần
"ét-kiu-eo" hoặc đọc như từ "sequel".

Điểm quan trọng nhất của SQL: nó là ngôn ngữ *khai báo* (declarative). Bạn mô tả kết quả muốn có, còn
cách lấy ra kết quả đó do DBMS quyết định. Lấy danh sách khách ở Hà Nội, sắp theo tên:

```sql
SELECT name, email
FROM customers
WHERE city = 'Hà Nội'
ORDER BY name;
```

Với dữ liệu ở mục 2.1, kết quả mong đợi:

```
+------+-----------------+
| name | email           |
+------+-----------------+
| An   | an@example.com  |
| Chi  | chi@example.com |
+------+-----------------+
```

So với cách *mệnh lệnh* (imperative) quen thuộc trong PHP, nơi bạn phải nói từng bước làm thế nào:

```php
// $customers là mảng các dòng đã nạp vào RAM
$result = [];
foreach ($customers as $c) {
    if ($c['city'] === 'Hà Nội') {
        $result[] = ['name' => $c['name'], 'email' => $c['email']];
    }
}
usort($result, fn (array $x, array $y): int => strcmp($x['name'], $y['name']));
```

Câu SQL không nói gì về việc duyệt dòng nào trước, dùng cấu trúc tra cứu nào, sắp xếp bằng thuật toán
gì. Bộ phận *query optimizer* (bộ tối ưu truy vấn) của DBMS tự chọn: có thể đọc hết bảng, có thể tra
index trên cột `city` nếu có, tuỳ dữ liệu. Dữ liệu tăng từ một nghìn lên mười triệu dòng, câu SQL vẫn
giữ nguyên, chỉ cách thực thi thay đổi. Cách đọc "kế hoạch thực thi" mà optimizer chọn là nội dung của
[chương 12](12-explain-toi-uu-query.md).

### 3.2 Chuẩn SQL và các "phương ngữ"

SQL ra đời ở IBM đầu những năm 1970 (Donald Chamberlin và Raymond Boyce), ban đầu tên là SEQUEL, sau đổi
thành SQL vì vướng nhãn hiệu. SQL trở thành chuẩn ANSI năm 1986 và chuẩn ISO năm 1987. Tên chính thức
của chuẩn là ISO/IEC 9075, được sửa đổi nhiều lần; bản gần nhất là SQL:2023.

Không DBMS nào cài đặt đầy đủ chuẩn. Mỗi hệ cài một phần lớn của chuẩn, cộng thêm phần mở rộng riêng,
nên trên thực tế mỗi hệ nói một *phương ngữ* (dialect) SQL. Phần lõi (`SELECT`, `INSERT`, `UPDATE`,
`DELETE`, `CREATE TABLE`) gần như giống nhau giữa các hệ; khác biệt nằm ở chi tiết:

| Việc cần làm | MySQL | PostgreSQL | Ghi chú |
|---|---|---|---|
| Lấy 10 dòng đầu | `LIMIT 10` | `LIMIT 10` hoặc `FETCH FIRST 10 ROWS ONLY` | `FETCH FIRST` là cú pháp của chuẩn (từ SQL:2008); MySQL không hỗ trợ |
| Bao tên cột trùng từ khoá | `` `order` `` (dấu backtick) | `"order"` (nháy kép, theo chuẩn) | MySQL chỉ hiểu nháy kép là tên khi bật chế độ `ANSI_QUOTES` |
| `'a' \|\| 'b'` | phép OR logic (cách dùng này đã deprecated), kết quả `0` | nối chuỗi, kết quả `'ab'` | Nối chuỗi trong MySQL dùng `CONCAT('a', 'b')` |

Giáo trình này viết SQL cho MySQL 8.4, và ghi rõ khi đối chiếu PostgreSQL.

### 3.3 Bốn nhóm lệnh: DDL, DML, DCL, TCL

Các câu lệnh SQL thường được chia thành bốn nhóm theo mục đích:

| Nhóm | Tên đầy đủ | Dùng để | Lệnh tiêu biểu | Học kỹ ở |
|---|---|---|---|---|
| *DDL* | Data Definition Language | định nghĩa cấu trúc: tạo, sửa, xoá database, bảng, index | `CREATE`, `ALTER`, `DROP`, `RENAME`, `TRUNCATE` | [Chương 04](04-ddl-constraint.md) |
| *DML* | Data Manipulation Language | đọc và thay đổi dữ liệu trong bảng | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | [Chương 05](05-select-co-ban.md) tới [10](10-window-function.md) |
| *DCL* | Data Control Language | cấp và thu hồi quyền truy cập | `GRANT`, `REVOKE` | [Chương 18](18-user-quyen-bao-mat.md) |
| *TCL* | Transaction Control Language | điều khiển transaction | `START TRANSACTION` (hoặc `BEGIN`), `COMMIT`, `ROLLBACK`, `SAVEPOINT` | [Chương 13](13-transaction-acid.md) |

Đoạn dưới để nhận mặt từng nhóm, chưa cần chạy (bảng `accounts` và user `'app'@'%'` chưa tồn tại):

```sql
-- DDL: tạo cấu trúc
CREATE TABLE notes (
    id   INT PRIMARY KEY AUTO_INCREMENT,
    body VARCHAR(200) NOT NULL
);

-- DML: thao tác dữ liệu
INSERT INTO notes (body) VALUES ('Học SQL');
SELECT id, body FROM notes;
UPDATE notes SET body = 'Học SQL mỗi ngày' WHERE id = 1;
DELETE FROM notes WHERE id = 1;

-- DCL: cho user app được đọc và ghi bảng notes trong database shop, rồi thu lại quyền ghi
GRANT SELECT, INSERT ON shop.notes TO 'app'@'%';
REVOKE INSERT ON shop.notes FROM 'app'@'%';

-- TCL: hai lệnh UPDATE thành công cùng nhau hoặc không lệnh nào có hiệu lực
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

Vài điều cần biết về cách chia nhóm:

- Đây là quy ước phổ biến để dễ nói chuyện, không phải ranh giới cứng. Có tài liệu tách `SELECT` ra
  thành nhóm riêng *DQL* (Data Query Language). Tài liệu MySQL thì chia chương theo cách riêng: Data
  Definition Statements, Data Manipulation Statements, Transactional and Locking Statements, Database
  Administration Statements (`GRANT`, `REVOKE`, `CREATE USER` nằm trong mục Account Management
  Statements ở đây), Utility Statements (`DESCRIBE`, `EXPLAIN`, `USE`)...
- `TRUNCATE TABLE` xoá sạch dữ liệu của bảng, nghe giống `DELETE`, nhưng tài liệu MySQL xếp nó vào DDL:
  nó thực hiện bằng cách xoá bảng đi và tạo lại, nhanh hơn nhiều so với xoá từng dòng.

⚠️ Trong MySQL, cách chia nhóm có hệ quả thật: các lệnh DDL (`CREATE TABLE`, `ALTER TABLE`,
`DROP TABLE`, `TRUNCATE TABLE`...) và các lệnh quản lý tài khoản (`CREATE USER`, `GRANT`, `REVOKE`...)
gây *implicit commit*: trước khi chạy, MySQL tự động commit transaction đang mở. Nghĩa là nếu bạn đang
giữa một transaction, đã `UPDATE` vài dòng, rồi chạy một câu `ALTER TABLE`, thì các `UPDATE` kia đã được
commit, `ROLLBACK` sau đó không lấy lại được. PostgreSQL khác: phần lớn lệnh DDL chạy được bên trong
transaction và rollback được (trừ một số lệnh, ví dụ `CREATE DATABASE` không được chạy trong
transaction). Khác biệt này ảnh hưởng tới cách viết migration ([chương 13](13-transaction-acid.md),
[chương 20](20-thay-doi-schema-migration.md)).

### 3.4 Quy tắc viết SQL cơ bản

```sql
-- Từ khoá viết hoa hay thường đều được; ba câu sau là một:
SELECT VERSION(), CURRENT_DATE;
select version(), current_date;
SeLeCt vErSiOn(), current_DATE;

-- Câu lệnh được phép trải trên nhiều dòng; dấu ; đánh dấu kết thúc câu
SELECT name,
       email
FROM customers
WHERE city = 'Hà Nội';

# Đây cũng là comment (kiểu riêng của MySQL)
/* Comment
   nhiều dòng */
SELECT 1 + 1; -- comment tới hết dòng; sau "--" bắt buộc có khoảng trắng
```

- **Từ khoá** (`SELECT`, `FROM`, `WHERE`...) không phân biệt hoa thường. Quy ước phổ biến: viết hoa từ
  khoá, viết thường tên bảng và tên cột cho dễ đọc.
- **Dấu `;`** kết thúc một câu lệnh. Trong chương trình `mysql` (mục 8), chưa gõ `;` thì client hiểu là
  câu lệnh chưa xong và chờ dòng tiếp theo. Khi gửi SQL từ PHP qua PDO, thường mỗi lần gửi một câu và
  không cần `;` ở cuối.
- **Chuỗi** đặt trong dấu nháy đơn: `'Hà Nội'`. MySQL mặc định cũng chấp nhận nháy kép cho chuỗi, nhưng
  đó là cách riêng của MySQL; trong PostgreSQL và trong chuẩn SQL, nháy kép bao tên (identifier) chứ
  không phải chuỗi. Tập thói quen dùng nháy đơn cho chuỗi ngay từ đầu.
- **Tên** (*identifier*: tên database, bảng, cột...) có thể viết trần như `customers`, hoặc bao trong
  dấu backtick như `` `customers` ``. Bắt buộc phải bao khi tên chứa ký tự đặc biệt hoặc trùng từ khoá
  dành riêng (reserved word), ví dụ một bảng tên `order`: `` SELECT * FROM `order` ``. Đặt tên tránh
  từ khoá (`orders` thay vì `order`) là cách đỡ phiền nhất.
- **Comment** có ba kiểu: `-- ` tới hết dòng (MySQL đòi sau hai dấu gạch phải có ít nhất một khoảng
  trắng hoặc ký tự điều khiển), `#` tới hết dòng (không thuộc chuẩn SQL, PostgreSQL không hiểu), và
  `/* ... */` có thể trải nhiều dòng.

## 4. Các hệ quản trị cơ sở dữ liệu phổ biến

Năm cái tên bạn sẽ gặp nhiều nhất. Cả năm đều là RDBMS, đều dùng SQL, nên kiến thức học với một hệ
chuyển sang hệ khác được phần lớn.

### 4.1 MySQL

- **Nguồn gốc.** Phiên bản đầu tiên ra năm 1995, do công ty MySQL AB (Thuỵ Điển) phát triển. Sun
  Microsystems mua MySQL AB năm 2008; Oracle mua lại Sun (hoàn tất năm 2010) nên hiện nay MySQL do
  Oracle phát triển. Cách đọc chính thức theo tài liệu là "My Ess Que Ell", nhưng đọc "my sequel" cũng
  không ai trách.
- **Giấy phép.** Cấp phép kép: dùng miễn phí theo giấy phép mã nguồn mở GPL (bản Community), hoặc mua
  giấy phép thương mại của Oracle (ví dụ khi cần nhúng MySQL vào sản phẩm đóng).
- **Vị trí.** Rất phổ biến cho ứng dụng web; là chữ M trong bộ LAMP (Linux, Apache, MySQL, PHP).
  Laravel hỗ trợ chính thức năm hệ: MariaDB, MySQL, PostgreSQL, SQLite, SQL Server.
- **Kiến trúc.** MySQL tách lớp xử lý SQL khỏi lớp lưu trữ, gọi là *storage engine*. Engine mặc định là
  *InnoDB*: có transaction, khoá ở mức dòng, tự phục hồi sau sự cố, có khoá ngoại. Một `CREATE TABLE`
  không ghi engine sẽ tạo bảng InnoDB. Gần như mọi thứ trong giáo trình này nói về InnoDB; bên trong
  nó hoạt động thế nào là [chương 16](16-ben-trong-innodb.md).
- **Các nhánh (fork).** *MariaDB* tách ra từ MySQL năm 2009, khi Oracle chuẩn bị mua Sun, do chính
  Michael "Monty" Widenius (một nhà sáng lập MySQL) khởi xướng. Ban đầu MariaDB thay thế được MySQL
  nguyên vẹn, nhưng hai bên đã đi những hướng khác nhau nhiều năm, nên giờ có khác biệt về tính năng,
  cú pháp và hành vi; đừng mặc định cái gì đúng với MySQL cũng đúng với MariaDB. *Percona Server for
  MySQL* là một bản phân phối khác bám sát MySQL, thêm công cụ và tính năng vận hành.
- **Phiên bản.** Từ năm 2023 (bản Innovation đầu tiên là 8.1.0), MySQL chia bản phát hành thành hai
  dòng:
  - *LTS* (Long-Term Support): ổn định, trong cùng một dòng LTS chỉ có bản vá cần thiết, không bỏ
    tính năng, không đổi định dạng dữ liệu; được hỗ trợ 5 năm premier cộng 3 năm extended. MySQL 8.4
    (ra tháng 4/2024) là dòng LTS đầu tiên theo mô hình này; dòng LTS tiếp theo là 9.7 (ra tháng
    4/2026).
  - *Innovation*: có tính năng mới nhưng cũng có thể thay đổi hành vi, mỗi bản chỉ được hỗ trợ tới khi
    bản Innovation kế tiếp ra đời (các bản 9.0 tới 9.6 là Innovation).
  - 9.7 là dòng cuối cùng đánh số kiểu cũ. Các bản sau (cả Innovation lẫn LTS) đánh số theo lịch
    dạng `YY.M.P` (năm, tháng, số bản vá): bản đầu tiên là 26.7.0, bản Innovation tháng 7/2026.
  - MySQL 8.0, dòng rất nhiều hệ thống đang chạy, đã hết hỗ trợ (end of life: hết extended support
    theo Oracle Lifetime Support Policy) vào tháng 4/2026. Còn
    gặp 8.0 thì nên lên kế hoạch nâng cấp.

Giáo trình này bám MySQL 8.4 LTS. Phần lớn kiến thức dùng được cho các bản mới hơn; khi nâng cấp phiên
bản, luôn đọc release notes để biết thay đổi hành vi.

### 4.2 PostgreSQL

- **Nguồn gốc.** Bắt nguồn từ dự án POSTGRES ở Đại học California, Berkeley, do giáo sư Michael
  Stonebraker dẫn dắt, bắt đầu cài đặt từ năm 1986. Năm 1994 dự án được thêm trình thông dịch SQL
  (thành Postgres95), năm 1996 đổi tên thành PostgreSQL. Thường gọi tắt là Postgres.
- **Giấy phép và tổ chức.** Mã nguồn mở theo PostgreSQL License, một giấy phép rất thoáng, tương tự BSD
  hay MIT. Do cộng đồng (PostgreSQL Global Development Group) phát triển, không thuộc sở hữu của một
  công ty nào.
- **Điểm mạnh hay được nhắc.** Bám chuẩn SQL sát; kiểu dữ liệu phong phú (JSONB, mảng, khoảng giá
  trị...); mở rộng được bằng extension (ví dụ PostGIS cho dữ liệu bản đồ); phần lớn lệnh DDL chạy được
  trong transaction (mục 3.3).
- **Kiến trúc kết nối.** Mỗi kết nối được phục vụ bởi một tiến trình (process) riêng do server tạo ra
  (fork). Khi có rất nhiều kết nối, người ta thường đặt một *connection pooler* phía trước
  ([chương 25](25-postgres-doi-chieu.md)).
- **Phiên bản.** PostgreSQL 18 phát hành tháng 9/2025.

### 4.3 SQLite

- **Nhúng, không có server.** SQLite là một thư viện được nhúng thẳng vào ứng dụng. Không có tiến trình
  server riêng: ứng dụng gọi hàm của thư viện, thư viện đọc ghi thẳng vào file. Cả một database (nhiều
  bảng, index, trigger, view) nằm trong một file duy nhất, và định dạng file dùng được trên mọi nền
  tảng, copy sang máy khác là chạy.
- **Giấy phép.** Public domain: dùng vào việc gì cũng được.
- **Vị trí.** Trang chủ SQLite tự nhận đây là database được triển khai nhiều nhất thế giới: có mặt
  trong mọi điện thoại Android và iPhone, các trình duyệt Firefox, Chrome, Safari, và cả trong PHP.
  Trang SQLite còn có một câu đáng nhớ: "SQLite does not compete with client/server databases. SQLite
  competes with fopen()." Nghĩa là SQLite thay thế việc tự ghi file như ở mục 1.2, chứ không thay thế
  MySQL.
- **Giới hạn.** SQLite cho nhiều người đọc cùng lúc nhưng mỗi file database chỉ có một người ghi tại một
  thời điểm. Không có tài khoản, phân quyền, và không có server để máy khác kết nối tới qua mạng. Hợp
  với ứng dụng di động và desktop, công cụ dòng lệnh, prototype, chạy test; không hợp với web app có
  nhiều request cùng ghi.

⚠️ Một cái bẫy thực tế: dùng SQLite để chạy test cho nhanh, còn production chạy MySQL. Hai hệ khác nhau
ở nhiều chi tiết, và test xanh không chứng minh code chạy đúng trên MySQL. Ví dụ, SQLite mặc định dùng
*flexible typing*: kiểu khai báo của cột chỉ là gợi ý, cột `INTEGER` vẫn nhận chuỗi:

```php
<?php
declare(strict_types=1);

$pdo = new PDO('sqlite::memory:');
$pdo->exec('CREATE TABLE products (id INTEGER PRIMARY KEY, price INTEGER NOT NULL)');
$pdo->exec("INSERT INTO products (id, price) VALUES (1, 'abc')"); // SQLite vẫn nhận
$row = $pdo->query('SELECT price, typeof(price) AS t FROM products WHERE id = 1')->fetch(PDO::FETCH_ASSOC);
var_dump($row);
// in ra:
// array(2) {
//   ["price"]=>
//   string(3) "abc"
//   ["t"]=>
//   string(4) "text"
// }
```

Cùng câu `INSERT` đó trên MySQL 8.4 với `sql_mode` mặc định (có `STRICT_TRANS_TABLES`) bị từ chối bằng
lỗi `ERROR 1366 (HY000): Incorrect integer value: 'abc' for column 'price' at row 1`. SQLite có chế độ
bảng `STRICT` (từ bản 3.37.0) để kiểm kiểu chặt hơn, nhưng nguyên tắc chung vẫn là: test trên đúng hệ
quản trị mà production dùng.

### 4.4 SQL Server và Oracle

- **Microsoft SQL Server.** Phương ngữ SQL của nó tên là *T-SQL* (Transact-SQL). Từ SQL Server 2017
  có thêm bản chạy trên Linux. Hay gặp trong hệ sinh thái Microsoft (.NET, Azure). Phần mềm thương
  mại, có bản Express miễn phí cho việc học và ứng dụng nhỏ.
- **Oracle Database.** Sản phẩm của Oracle Corporation, ra đời từ cuối những năm 1970 và là một trong
  những hệ SQL thương mại đầu tiên. Ngôn ngữ thủ tục đi kèm là *PL/SQL*. Nhiều tính năng cho hệ thống
  doanh nghiệp lớn, chi phí bản quyền cao; có bản miễn phí giới hạn tài nguyên cho phát triển và học.

Lưu ý tên gọi: Oracle (công ty) sở hữu cả Oracle Database lẫn MySQL, nhưng đây là hai sản phẩm hoàn toàn
khác nhau.

### 4.5 So sánh nhanh

| | MySQL | PostgreSQL | SQLite | SQL Server | Oracle Database |
|---|---|---|---|---|---|
| Kiểu chạy | client-server | client-server | nhúng trong ứng dụng | client-server | client-server |
| Giấy phép | GPL hoặc thương mại | PostgreSQL License (mã nguồn mở) | public domain | thương mại, có bản miễn phí | thương mại, có bản miễn phí |
| Phục vụ mỗi kết nối bằng | một thread | một process | (không có kết nối mạng) | | |
| Hay gặp ở | web, PHP/Laravel, SaaS | web, hệ thống cần kiểu dữ liệu và tính năng SQL phong phú | mobile, desktop, test, prototype | hệ sinh thái Microsoft | doanh nghiệp lớn |

Ngoài việc tự cài, production ngày nay thường dùng database dạng dịch vụ được quản lý (*managed
database*) của các nhà cung cấp cloud, ví dụ Amazon RDS, Google Cloud SQL, Azure Database. Bên dưới
vẫn là MySQL hay PostgreSQL, nên SQL và kiến thức trong giáo trình áp dụng nguyên vẹn; phần việc cài
đặt, sao lưu, nâng cấp được nhà cung cấp làm hộ một phần.

Giáo trình này dùng MySQL 8.4 làm hệ chính (hợp với hệ sinh thái PHP/Laravel), và đối chiếu PostgreSQL ở
những chỗ hai hệ khác nhau đáng kể; [chương 25](25-postgres-doi-chieu.md) dành riêng cho việc so sánh.

## 5. Database quan hệ và NoSQL

### 5.1 NoSQL là gì

*NoSQL* là tên gọi chung cho các hệ database không lấy mô hình bảng quan hệ làm trung tâm. Ngày nay chữ
này thường được hiểu là "Not only SQL" (không chỉ SQL) hơn là "không có SQL". Nhóm này phổ biến mạnh
từ khoảng cuối những năm 2000, khi các công ty internet lớn cần lưu lượng dữ liệu và lượng ghi rất lớn
trên nhiều máy, và cần cấu trúc dữ liệu linh hoạt hơn bảng có schema cố định.

NoSQL không phải một loại duy nhất, mà là nhiều nhóm rất khác nhau:

| Nhóm | Dữ liệu trông như thế nào | Ví dụ | Hay dùng cho |
|---|---|---|---|
| *Key-value* | Mỗi khoá trỏ tới một giá trị, giống một mảng kết hợp khổng lồ | Redis, Amazon DynamoDB | Cache, session, bộ đếm, tra cứu theo khoá |
| *Document* | Mỗi bản ghi là một document dạng JSON, có thể lồng nhau | MongoDB, Couchbase | Dữ liệu cấu trúc hay thay đổi, đọc ghi cả "cục" một lúc |
| *Wide-column* | Dòng với tập cột linh hoạt, phân tán trên nhiều máy | Apache Cassandra, Apache HBase | Lượng ghi rất lớn, truy vấn theo các mẫu biết trước |
| *Graph* | Đỉnh (node) và cạnh (quan hệ) | Neo4j | Quan hệ nhiều tầng: mạng xã hội, gợi ý, phát hiện gian lận |

Hai loại hệ thống khác cũng hay được xếp chung nhóm: *search engine* như Elasticsearch, OpenSearch (tìm
kiếm toàn văn, lọc theo nhiều tiêu chí), và *time-series database* cho dữ liệu đo theo thời gian.

So sánh cùng một dữ liệu. Trong database quan hệ, đơn hàng và các món trong đơn nằm ở hai bảng, nối với
nhau bằng khoá:

```
orders                              order_items
+----+-------------+--------+       +----------+---------+-----+
| id | customer_id | total  |       | order_id | product | qty |
+----+-------------+--------+       +----------+---------+-----+
| 10 |           1 | 250000 |       |       10 | Bút     |   2 |
+----+-------------+--------+       |       10 | Vở      |   5 |
                                    +----------+---------+-----+
```

Trong một document database, cả đơn hàng thường được lưu thành một document:

```json
{
  "_id": 10,
  "customer": { "id": 1, "name": "An" },
  "items": [
    { "product": "Bút", "qty": 2 },
    { "product": "Vở", "qty": 5 }
  ],
  "total": 250000
}
```

Đọc cả đơn hàng là một lần lấy một document, rất tiện. Đổi lại, tên khách "An" giờ được chép vào mọi
đơn hàng của An; An đổi tên thì phải sửa ở mọi nơi, hoặc chấp nhận dữ liệu cũ. Còn câu hỏi kiểu "sản phẩm
nào bán chạy nhất tháng này" phải duyệt vào bên trong mọi document. Mỗi mô hình tối ưu cho một kiểu
truy cập.

### 5.2 So sánh khái quát

| Tiêu chí | Database quan hệ (MySQL, PostgreSQL) | NoSQL (khác nhau nhiều tuỳ hệ) |
|---|---|---|
| Cấu trúc | Bảng, schema khai báo trước, DBMS kiểm tra dữ liệu khi ghi | Linh hoạt; cấu trúc thường do ứng dụng tự hiểu khi đọc |
| Truy vấn | SQL; JOIN tuỳ ý; hỏi được cả câu hỏi chưa lường trước khi thiết kế | API hoặc ngôn ngữ riêng; thường tối ưu cho các mẫu truy cập đã biết trước; JOIN hạn chế hoặc không có |
| Toàn vẹn dữ liệu | Khoá ngoại, ràng buộc, transaction trên nhiều bảng | Thường ít ràng buộc hơn; transaction trên nhiều bản ghi có ở một số hệ, kèm giới hạn |
| Mở rộng | Tăng sức mạnh một máy thì dễ; chia dữ liệu ra nhiều máy (sharding) cần nhiều công sức ([chương 23](23-partition-sharding-scale.md)) | Nhiều hệ được thiết kế phân tán ngay từ đầu, thêm máy dễ hơn |
| Nhất quán | Trên một server, dữ liệu đã commit hiện ra cho mọi transaction bắt đầu sau đó; đọc từ máy bản sao (replica) thì có thể bị trễ ([chương 22](22-replication-ha.md)) | Một số hệ mặc định chấp nhận *eventual consistency* (dữ liệu giữa các máy khớp nhau sau một lúc) để đổi lấy tốc độ và tính sẵn sàng; thường cấu hình được |

### 5.3 Chọn thế nào

- Dữ liệu nghiệp vụ cốt lõi (người dùng, đơn hàng, thanh toán, kho) nên mặc định đặt trong database
  quan hệ: dữ liệu đúng nhờ ràng buộc và transaction, truy vấn linh hoạt, công cụ và người có kinh
  nghiệm đều nhiều.
- Thêm một hệ NoSQL khi có nhu cầu cụ thể mà database quan hệ làm kém: cache và bộ đếm tốc độ cao
  (Redis), tìm kiếm toàn văn phức tạp (Elasticsearch), lượng ghi khổng lồ phân tán trên nhiều máy.
  Rất nhiều hệ thống dùng song song: MySQL là nguồn dữ liệu gốc (*source of truth*), Redis làm cache,
  Elasticsearch phục vụ tìm kiếm. Cách dùng nhiều loại database cho nhiều việc như vậy gọi là
  *polyglot persistence*.
- Ranh giới đang mờ dần. MySQL có kiểu dữ liệu `JSON` riêng: tự kiểm tra document hợp lệ khi ghi, lưu ở
  định dạng nhị phân để đọc nhanh từng phần tử. PostgreSQL có `JSONB`. Ở chiều ngược lại, MongoDB
  hỗ trợ transaction trên nhiều document. Khi nào nên dùng cột JSON trong MySQL được bàn ở
  [chương 03](03-kieu-du-lieu.md).

⚠️ Hai lý do chọn NoSQL hay gặp nhưng không đứng vững:

- "Không phải thiết kế schema, thêm trường thoải mái." Schema vẫn tồn tại, chỉ là không được khai báo ở
  một chỗ mà nằm rải rác trong code đọc ghi. Sau vài năm, cùng một collection có document kiểu cũ lẫn
  kiểu mới, và mọi đoạn code đọc phải xử lý hết các biến thể.
- "NoSQL nhanh hơn." Nhanh cho đúng mẫu truy cập nó được thiết kế. Với dữ liệu có nhiều liên kết (đơn
  hàng, khách hàng, sản phẩm), bạn sẽ phải tự ghép dữ liệu trong code hoặc chép dữ liệu ra nhiều nơi
  rồi tự giữ cho chúng khớp nhau, tức là tự làm lại phần việc database quan hệ vốn làm sẵn.

## 6. Kiến trúc client-server

### 6.1 Server và client

MySQL hoạt động theo mô hình *client-server*:

- *Server* là một chương trình chạy liên tục, giữ và quản lý dữ liệu, chờ người khác kết nối tới. Server
  của MySQL là chương trình `mysqld` (chữ `d` là *daemon*, cách gọi tiến trình chạy nền trên Unix).
  Tài liệu MySQL mô tả `mysqld` là một chương trình duy nhất, đa luồng (multithreaded), làm phần lớn
  công việc của một bản cài MySQL.
- *Client* là bất kỳ chương trình nào kết nối tới server, gửi câu lệnh SQL và nhận kết quả về: chương
  trình dòng lệnh `mysql` (mục 8), MySQL Shell (`mysqlsh`), công cụ đồ hoạ như MySQL Workbench, DBeaver,
  TablePlus, và quan trọng nhất là ứng dụng của bạn: PHP kết nối qua PDO hoặc mysqli, Laravel thì chạy
  trên nền PDO.

```
   Các client                                           Server database
 +---------------------------+                       +----------------------------------+
 | mysql (dòng lệnh)          |---\                   | mysqld (MySQL Server)            |
 +---------------------------+    \                  |  - nhận kết nối                  |
 | PHP-FPM: PDO, Laravel      |-----+-- TCP 3306 ---> |  - mỗi kết nối một thread        |
 +---------------------------+    /   (hoặc socket)  |  - phân tích, tối ưu, thực thi SQL |
 | DBeaver, Workbench...      |---/                   |  - InnoDB đọc ghi dữ liệu        |
 +---------------------------+                       +----------------+-----------------+
                                                                       |
                                                      thư mục dữ liệu (datadir): file dữ liệu, log
```

⚠️ Đừng nhầm `mysqld` với `mysql`. `mysqld` là server, chứa dữ liệu. `mysql` chỉ là một client, giống
một trình duyệt web: cài client trên máy không có nghĩa là máy có database, và tắt client không ảnh
hưởng gì tới dữ liệu.

Vì sao lại tách ra như vậy, thay vì để mỗi ứng dụng tự đọc file dữ liệu như SQLite?

- Nhiều ứng dụng, trên nhiều máy, dùng chung một nguồn dữ liệu: web server, worker xử lý hàng đợi, công
  cụ báo cáo đều kết nối về cùng một server.
- Server là nơi duy nhất chạm vào file dữ liệu, nên nó điều phối được mọi thao tác đồng thời, kiểm tra
  quyền của từng tài khoản, và tự phục hồi sau sự cố.
- Server database có thể đặt trên máy riêng, cấu hình riêng (nhiều RAM, ổ đĩa nhanh), không tranh tài
  nguyên với ứng dụng.

### 6.2 Muốn kết nối cần biết gì

Một kết nối tới MySQL cần các thông tin:

| Thông tin | Ý nghĩa | Ví dụ |
|---|---|---|
| host | Máy chạy server: tên máy hoặc địa chỉ IP | `127.0.0.1`, `db.internal` |
| port | Cổng TCP server đang nghe, mặc định 3306 | `3306` |
| user, password | Tài khoản MySQL (tài khoản riêng của MySQL, không phải tài khoản hệ điều hành) | `root`, `app` |
| database | Database mặc định cho các câu lệnh (không bắt buộc) | `shop` |

Trong PHP, các thông tin đó nằm trong *DSN* (Data Source Name) của PDO:

```php
<?php
declare(strict_types=1);

$pdo = new PDO(
    'mysql:host=127.0.0.1;port=3306;dbname=shop;charset=utf8mb4', // DSN
    'app',      // user
    'secret',   // password
);
```

Ứng dụng Laravel đặt chúng trong file `.env` (`DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`,
`DB_PASSWORD`). Lưu ý: file `.env.example` của project Laravel 13 mới tạo đặt sẵn `DB_CONNECTION=sqlite`
và để các dòng `DB_HOST`... ở dạng comment; muốn dùng MySQL thì đổi thành `DB_CONNECTION=mysql` và điền
các dòng kia. Chi tiết kết nối từ PHP là nội dung của [chương 19](19-database-tu-ung-dung.md).

Một tài khoản MySQL được xác định bằng cả tên lẫn nơi kết nối tới, viết dạng `'tên'@'host'`: `'app'@'%'`
(từ bất kỳ đâu) khác `'app'@'localhost'` (chỉ từ chính máy chạy server). Chương
[18](18-user-quyen-bao-mat.md) nói kỹ về tài khoản và quyền.

### 6.3 Hai đường kết nối: TCP và Unix socket

Server MySQL nghe kết nối qua nhiều "cửa":

- **TCP/IP**: kết nối qua mạng, dùng được cả từ máy khác lẫn từ chính máy chạy server. Port mặc định
  3306.
- **Unix socket file** (trên Linux, macOS): một file đặc biệt làm điểm hẹn cho các tiến trình trên
  cùng một máy, không đi qua tầng mạng. Chỉ dùng được khi client và server ở cùng máy (và cùng nhìn
  thấy file đó). Vị trí mặc định theo tài liệu MySQL là `/tmp/mysql.sock`; một số bản cài đặt dùng chỗ
  khác.

⚠️ Bẫy kinh điển: trên Unix, các chương trình client của MySQL đối xử đặc biệt với tên `localhost`.
Khi bạn ghi host là `localhost`, client **không** kết nối TCP tới 127.0.0.1 như hầu hết phần mềm mạng
khác, mà kết nối qua Unix socket file. Muốn chắc chắn dùng TCP, ghi host là `127.0.0.1`, hoặc thêm
`--protocol=TCP`. Driver PDO_MYSQL của PHP cũng làm y như vậy: `host=localhost` trên Unix nghĩa là đi
qua socket.

Hệ quả thực tế: chạy MySQL trong Docker rồi kết nối từ máy thật bằng `mysql -h localhost ...`, client đi
tìm file socket trên máy thật, không thấy, và báo lỗi dạng:

```
ERROR 2002 (HY000): Can't connect to local MySQL server through socket '/tmp/mysql.sock' (2)
```

(output minh hoạ; đường dẫn socket tuỳ cách client được cài). Đổi thành `-h 127.0.0.1` là kết nối TCP
qua port mà Docker đã mở. Còn khi server chưa chạy hoặc sai port, kết nối TCP báo lỗi dạng
`ERROR 2003 (HY000): Can't connect to MySQL server on '127.0.0.1:3306' (61)` (minh hoạ; số trong ngoặc
cuối là mã lỗi của hệ điều hành, khác nhau giữa macOS và Linux).

### 6.4 Mỗi kết nối là một session

Khi một client kết nối thành công, server giao cho kết nối đó một thread riêng lo xác thực và xử lý mọi
câu lệnh của nó. Thread được lấy lại từ một bộ đệm thread (thread cache) nếu có sẵn, để đỡ tốn công tạo
mới. Từ lúc kết nối tới lúc ngắt, kết nối đó là một *session* với trạng thái riêng:

- database đang chọn (lệnh `USE`, mục 9.2);
- các biến cấu hình mức session (ví dụ `SET SESSION sql_mode = ...`);
- transaction đang mở.

Trạng thái này không chia sẻ giữa các kết nối: `USE shop` ở cửa sổ terminal này không ảnh hưởng cửa sổ
kia. Khi kết nối đóng, trạng thái mất theo; transaction đang mở mà chưa `COMMIT` sẽ bị rollback.

Xem các kết nối đang mở bằng `SHOW PROCESSLIST` (cần quyền `PROCESS` để thấy kết nối của người khác,
user `root` thì có), và xem id kết nối của chính mình bằng `CONNECTION_ID()`:

```sql
SELECT CONNECTION_ID();
SHOW PROCESSLIST;
```

```
+----+-----------------+-----------+------+---------+------+------------------------+------------------+
| Id | User            | Host      | db   | Command | Time | State                  | Info             |
+----+-----------------+-----------+------+---------+------+------------------------+------------------+
|  5 | event_scheduler | localhost | NULL | Daemon  |  812 | Waiting on empty queue | NULL             |
|  9 | root            | localhost | NULL | Query   |    0 | NULL                   | SHOW PROCESSLIST |
+----+-----------------+-----------+------+---------+------+------------------------+------------------+
```

(output minh hoạ; id, thời gian, trạng thái sẽ khác trên máy bạn). Dòng `event_scheduler` là thread nội
bộ của bộ lập lịch sự kiện, được bật mặc định ([chương 17](17-view-procedure-trigger.md)); dòng `root`
chính là kết nối của bạn.

Số kết nối đồng thời có giới hạn, đặt bởi biến `max_connections` (mặc định 151). Server thực ra cho
phép `max_connections + 1` kết nối: kết nối dư ra dành cho tài khoản có quyền `CONNECTION_ADMIN`, để
quản trị viên vẫn vào được xem chuyện gì đang xảy ra. Vượt giới hạn, client mới nhận lỗi
`Too many connections`. ⚠️ Với PHP-FPM, mỗi tiến trình worker đang xử lý request có dùng database giữ
một kết nối riêng, nên số kết nối tăng theo số worker nhân số server ứng dụng; 4 server, mỗi server 50
worker là đã có thể cần tới 200 kết nối, vượt mặc định 151. Cách tính và xử lý ở
[chương 19](19-database-tu-ung-dung.md) và [chương 24](24-van-hanh-monitoring.md).

### 6.5 So sánh ba kiểu kiến trúc

| | MySQL | PostgreSQL | SQLite |
|---|---|---|---|
| Có server riêng | có, `mysqld` | có, `postgres` | không, là thư viện nằm trong tiến trình ứng dụng |
| Phục vụ mỗi kết nối bằng | một thread trong tiến trình `mysqld` | một process riêng, fork từ tiến trình chính | không có khái niệm kết nối mạng; ứng dụng mở thẳng file |
| Kết nối từ máy khác | có, TCP | có, TCP | không (chỉ mở file) |
| Port mặc định | 3306 | 5432 | không có |

## 7. Cài đặt MySQL 8.4

### 7.1 Chọn cách cài

| Cách | Ưu điểm | Nhược điểm | Hợp với |
|---|---|---|---|
| Docker | Không cài gì vào máy ngoài Docker; chạy nhiều phiên bản song song; xoá sạch trong một lệnh; môi trường Linux giống production | Cần cài Docker; dữ liệu nằm trong volume, phải hiểu volume để không mất dữ liệu | Học, phát triển, mọi hệ điều hành |
| Homebrew (macOS) | Chạy trực tiếp trên máy, tự khởi động cùng máy | Một số hành vi mặc định của MySQL trên macOS khác Linux (mục 9.4); dễ đụng port với bản cài khác | Người dùng macOS muốn cài thẳng |
| Bộ cài chính thức hoặc trình quản lý gói của Linux | Cách cài cho server thật | Nhiều bước cấu hình | Máy chủ, môi trường production |

Giáo trình khuyên dùng Docker: một lệnh là có MySQL 8.4 sạch, hỏng thì xoá đi chạy lại. Mục 7.3 dành cho
ai muốn cài bằng Homebrew trên macOS.

### 7.2 Cài bằng Docker

**Bước 1. Cài Docker.** Trên macOS và Windows là Docker Desktop, trên Linux là Docker Engine. Kiểm tra
bằng lệnh `docker --version` ở terminal. Image MySQL chính thức có bản cho cả chip Intel/AMD (amd64)
lẫn chip ARM (arm64, như Mac chip Apple), Docker tự chọn đúng bản.

**Bước 2. Chạy container MySQL 8.4.** Ở terminal của máy bạn (máy host):

```sh
docker run -d --name my84 \
  -e MYSQL_ROOT_PASSWORD=root \
  -p 3306:3306 \
  -v my84data:/var/lib/mysql \
  mysql:8.4
```

Từng phần của lệnh:

| Phần | Ý nghĩa |
|---|---|
| `docker run` | Tạo và chạy một container từ một image |
| `-d` | Chạy nền (detached), trả lại terminal ngay |
| `--name my84` | Đặt tên container là `my84` để các lệnh sau gọi tên |
| `-e MYSQL_ROOT_PASSWORD=root` | Biến môi trường mà image MySQL đọc khi khởi tạo lần đầu: mật khẩu của tài khoản `root`. Image bắt buộc có biến này (hoặc một trong các biến thay thế như `MYSQL_RANDOM_ROOT_PASSWORD`) |
| `-p 3306:3306` | Mở port: port 3306 của máy host chuyển vào port 3306 trong container, để client trên máy host kết nối được |
| `-v my84data:/var/lib/mysql` | Gắn volume tên `my84data` vào `/var/lib/mysql`, thư mục MySQL ghi dữ liệu trong container. Dữ liệu nằm trong volume nên còn nguyên khi xoá container |
| `mysql:8.4` | Image `mysql`, tag `8.4`: trỏ tới bản vá mới nhất của dòng 8.4 |

Image còn nhận vài biến tiện lợi khác, ví dụ `-e MYSQL_DATABASE=shop` để tạo sẵn database `shop`, kèm
`-e MYSQL_USER=app -e MYSQL_PASSWORD=secret` để tạo user `app` có toàn quyền trên database đó.

⚠️ Luôn ghi rõ tag `mysql:8.4`. Image `mysql` không ghi tag (tức `mysql:latest`) hiện trỏ tới dòng
Innovation mới nhất (lúc viết là 26.7), còn tag `mysql:lts` trỏ tới dòng LTS mới nhất (9.7), không phải
8.4. Không ghi tag là mỗi lần tải image có thể nhận một phiên bản khác.

⚠️ Mật khẩu `root` ở đây chỉ dùng cho máy học tập. Server thật cần mật khẩu mạnh và không dùng `root`
cho ứng dụng ([chương 18](18-user-quyen-bao-mat.md)).

⚠️ Các biến `MYSQL_ROOT_PASSWORD`, `MYSQL_DATABASE`... chỉ có tác dụng ở lần khởi tạo đầu tiên, khi thư
mục dữ liệu còn trống. Nếu volume `my84data` đã có dữ liệu từ lần chạy trước, chạy lại với mật khẩu khác
cũng không đổi được mật khẩu cũ.

**Bước 3. Chờ khởi tạo xong.** Lần chạy đầu, container mất một lúc để tạo dữ liệu hệ thống, và trong
lúc đó chưa nhận kết nối. Theo dõi log:

```sh
docker logs -f my84     # Ctrl+C để thoát xem log, container vẫn chạy
```

Script khởi động của image chạy một server tạm (không mở mạng) để làm các bước khởi tạo, tắt nó đi, rồi
mới chạy server thật. Khởi tạo xong khi thấy các dòng kiểu:

```
... [Note] [Entrypoint]: MySQL init process done. Ready for start up.
...
... /usr/sbin/mysqld: ready for connections. Version: '8.4.11'  socket: '/var/run/mysqld/mysqld.sock'  port: 3306  MySQL Community Server - GPL.
```

(output minh hoạ, đã rút gọn; số phiên bản và thời gian sẽ khác). Có thể thấy dòng `ready for
connections` hai lần: lần đầu của server tạm, có `port: 0` vì server tạm không mở mạng; dòng có
`port: 3306` mới là server thật.

**Bước 4. Kết nối.** Cách không cần cài thêm gì: chạy chương trình `mysql` có sẵn bên trong container.

```sh
docker exec -it my84 mysql -uroot -p
# Enter password: (gõ root, màn hình không hiện ký tự, rồi Enter)
```

`docker exec -it my84 ...` chạy một lệnh bên trong container đang chạy, `-it` để tương tác được bằng bàn
phím. Lệnh `mysql` bên trong container không ghi host nên dùng mặc định `localhost`, tức là đi qua Unix
socket trong container (mục 6.3). Ý nghĩa từng tuỳ chọn của `mysql` ở mục 8.

Nếu máy host có cài sẵn client `mysql` (mục 7.3 có cách cài riêng client), kết nối qua port đã mở:

```sh
mysql -h 127.0.0.1 -P 3306 -u root -p
```

Nhớ dùng `127.0.0.1` chứ không phải `localhost` (mục 6.3). Image tạo tài khoản root ở dạng `'root'@'%'`
(kết nối từ đâu cũng được) bên cạnh `'root'@'localhost'`, nên kết nối từ máy host qua TCP được chấp nhận.

**Quản lý container:**

```sh
docker stop my84          # dừng server (dữ liệu giữ nguyên)
docker start my84         # chạy lại
docker rm -f my84         # xoá container; dữ liệu vẫn còn trong volume my84data
docker volume rm my84data # xoá hẳn dữ liệu (chỉ làm khi container đã bị xoá)
```

⚠️ Port 3306 trên máy host chỉ một chương trình chiếm được. Nếu đã có MySQL khác (ví dụ bản Homebrew)
đang chạy, `docker run` sẽ báo lỗi port đã bị chiếm. Tắt bản kia, hoặc đổi port phía host:
`-p 3307:3306`, rồi kết nối bằng `-P 3307`.

**Thêm PostgreSQL 18 để đối chiếu (tuỳ chọn).** Những chỗ giáo trình đối chiếu PostgreSQL, bạn có thể
chạy song song:

```sh
docker run -d --name pg18 -e POSTGRES_PASSWORD=pg -p 5432:5432 -v pg18data:/var/lib/postgresql postgres:18
docker exec -it pg18 psql -U postgres
```

Image `postgres` bắt buộc có `POSTGRES_PASSWORD`; user mặc định là `postgres`. Từ bản 18, image đổi chỗ
lưu dữ liệu nên volume gắn vào `/var/lib/postgresql` (các bản cũ hơn là `/var/lib/postgresql/data`).

### 7.3 Cài bằng Homebrew (macOS)

Homebrew có formula riêng cho dòng 8.4 là `mysql@8.4`. ⚠️ Đừng cài `mysql` không kèm số: formula đó
trỏ tới một phiên bản mới hơn, không phải 8.4.

```sh
brew install mysql@8.4
```

`mysql@8.4` là formula *keg-only*: Homebrew cài nó nhưng không tạo lối tắt vào thư mục `bin` chung, vì nó
là phiên bản phụ của formula `mysql`. Vì vậy lệnh `mysql` chưa gọi được ngay; thêm thư mục `bin` của nó
vào `PATH` (lệnh dưới dành cho zsh, shell mặc định của macOS):

```sh
# Mac chip Apple (Homebrew nằm ở /opt/homebrew):
echo 'export PATH="/opt/homebrew/opt/mysql@8.4/bin:$PATH"' >> ~/.zshrc
# Mac chip Intel (Homebrew nằm ở /usr/local) thì dùng dòng này thay cho dòng trên:
# echo 'export PATH="/usr/local/opt/mysql@8.4/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
mysql --version   # kiểm tra: phải hiện phiên bản 8.4.x
```

Không chắc máy mình thuộc loại nào thì chạy `brew --prefix mysql@8.4`: lệnh này in ra đúng thư mục cài
(ví dụ `/opt/homebrew/opt/mysql@8.4`), thêm `/bin` vào sau là thư mục cần đưa vào `PATH`.

Chạy server như một dịch vụ nền, tự khởi động cùng máy:

```sh
brew services start mysql@8.4   # chạy server
brew services list              # xem trạng thái
brew services stop mysql@8.4    # dừng server
```

Theo thông báo của chính formula: database được khởi tạo với tài khoản `root` **chưa có mật khẩu**, và
server cấu hình chỉ nhận kết nối từ chính máy đó (file cấu hình Homebrew đặt `bind-address = 127.0.0.1`).
Kết nối và đặt mật khẩu:

```sh
mysql -u root                 # chưa có mật khẩu nên không cần -p
mysql_secure_installation     # chạy ở terminal, trả lời từng câu hỏi
```

`mysql_secure_installation` là công cụ đi kèm MySQL, hỏi lần lượt để: đặt mật khẩu cho `root`, xoá các
tài khoản `root` đăng nhập được từ máy khác, xoá tài khoản ẩn danh, xoá database `test`.

Vài thông tin về bản cài Homebrew:

- Thư mục dữ liệu: `$(brew --prefix)/var/mysql`, tức `/opt/homebrew/var/mysql` trên Mac chip Apple.
- Client kết nối `localhost` qua Unix socket, mặc định là `/tmp/mysql.sock`.
- Chỉ cần client (ví dụ để kết nối vào MySQL trong Docker) thì cài `mysql-client@8.4` thay vì cả
  server; formula này cũng keg-only, thêm vào `PATH` tương tự.

### 7.4 Kiểm tra sau khi cài

Dù cài cách nào, khi đã vào được dấu nhắc `mysql>`, chạy:

```sql
SELECT VERSION();
SELECT CURRENT_USER();
```

Kết quả mong đợi (giá trị cụ thể tuỳ máy):

```
+-----------+
| VERSION() |
+-----------+
| 8.4.11    |
+-----------+
1 row in set (0.00 sec)

+----------------+
| CURRENT_USER() |
+----------------+
| root@localhost |
+----------------+
1 row in set (0.00 sec)
```

`VERSION()` phải bắt đầu bằng `8.4`. `CURRENT_USER()` cho biết bạn đang đăng nhập bằng tài khoản nào:
qua `docker exec` là `root@localhost`, còn kết nối từ máy host qua TCP vào Docker sẽ là `root@%`.

## 8. Làm việc với chương trình `mysql`

`mysql` là client dòng lệnh đi kèm MySQL: bạn gõ câu lệnh, nó gửi tới server và in kết quả ra dạng bảng.
Công cụ đồ hoạ tiện hơn khi duyệt dữ liệu, nhưng `mysql` có mặt ở mọi nơi có MySQL (trong container,
trên server production), nên đáng để thành thạo.

### 8.1 Cú pháp kết nối

```sh
mysql [các tuỳ chọn] [tên_database]
```

| Tuỳ chọn | Dạng dài | Ý nghĩa | Mặc định |
|---|---|---|---|
| `-h` | `--host` | Máy chạy server | `localhost` (trên Unix nghĩa là đi qua socket, mục 6.3) |
| `-P` | `--port` | Port TCP (P viết hoa) | 3306 |
| `-u` | `--user` | Tên tài khoản MySQL | Trên Unix là tên đăng nhập hệ điều hành của bạn |
| `-p` | `--password` | Mật khẩu (p viết thường); không kèm giá trị thì client hỏi | |
| `-D` | `--database` | Database mặc định; cũng có thể ghi tên database ở cuối lệnh | |
| `-e` | `--execute` | Chạy câu lệnh rồi thoát | |
| `-S` | `--socket` | Đường dẫn Unix socket file khi kết nối `localhost` | |
| | `--protocol` | Ép kiểu kết nối, ví dụ `--protocol=TCP` | |

Ví dụ (chạy ở terminal):

```sh
# Vào MySQL trong container Docker (qua socket bên trong container)
docker exec -it my84 mysql -u root -p

# Từ máy host vào container qua TCP, chọn sẵn database shop (khi shop đã tồn tại)
mysql -h 127.0.0.1 -P 3306 -u root -p shop

# Chạy một câu rồi thoát, tiện cho script
mysql -h 127.0.0.1 -u root -p -e "SELECT VERSION()"
```

Với các tuỳ chọn dạng ngắn, viết `-u root` hay `-uroot` đều được. Riêng `-p` thì khác, và đây là chỗ
người mới vấp nhiều nhất:

| Bạn gõ | Client hiểu là | Kết quả |
|---|---|---|
| `-p` | Hỏi mật khẩu | Gõ mật khẩu (không hiện trên màn hình). Cách an toàn khi làm tay |
| `-proot` (dính liền) | Mật khẩu là `root` | Vào được, nhưng client in cảnh báo `mysql: [Warning] Using a password on the command line interface can be insecure.` |
| `-p root` (có dấu cách) | Hỏi mật khẩu; `root` là **tên database** | Gõ đúng mật khẩu rồi vẫn lỗi `ERROR 1049 (42000): Unknown database 'root'` |

⚠️ Vì sao mật khẩu trên dòng lệnh không an toàn: nó nằm lại trong lịch sử shell (`~/.zsh_history`,
`~/.bash_history`), và trên một số hệ thống người dùng khác có thể nhìn thấy dòng lệnh đang chạy qua các
chương trình như `ps`. Dùng tạm trên máy học tập thì được; trong script thật, đọc mật khẩu từ file cấu
hình (mục 8.5).

### 8.2 Màn hình tương tác

Kết nối thành công, client in lời chào rồi hiện dấu nhắc `mysql>`:

```
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 9
Server version: 8.4.11 MySQL Community Server - GPL

...(thông tin bản quyền)...

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql>
```

(output minh hoạ; connection id và phiên bản tuỳ máy). Connection id chính là `Id` của kết nối trong
`SHOW PROCESSLIST` (mục 6.4).

Câu lệnh SQL chỉ được gửi đi khi gặp dấu kết thúc (`;`, `\g` hoặc `\G`). Gõ Enter khi câu chưa kết thúc,
client đổi dấu nhắc để báo nó đang chờ gì:

| Dấu nhắc | Ý nghĩa |
|---|---|
| `mysql>` | Sẵn sàng nhận câu lệnh mới |
| `->` | Đang chờ dòng tiếp theo của câu lệnh nhiều dòng (thường là bạn quên `;`) |
| `'>` | Đang chờ đóng chuỗi mở bằng nháy đơn `'` |
| `">` | Đang chờ đóng chuỗi mở bằng nháy kép `"` |
| `` `> `` | Đang chờ đóng tên mở bằng backtick `` ` `` |
| `/*>` | Đang chờ đóng comment mở bằng `/*` |

Hai tình huống hay gặp:

```
mysql> SELECT VERSION()
    -> ;
```

Quên `;` thì client hiện `->` và chờ. Gõ `;` rồi Enter là câu lệnh chạy.

```
mysql> SELECT * FROM customers WHERE name = 'An;
    '> \c
    '>
```

Quên đóng nháy (`'An` thiếu dấu `'` thứ hai) thì client coi mọi thứ gõ sau là một phần của chuỗi, kể cả
`;` và `\c`: câu lệnh không chạy, mà `\c` cũng không huỷ được. Cách thoát: gõ dấu `'` để đóng chuỗi, rồi
ngay sau đó gõ `\c` để huỷ câu đang gõ:

```
    '> '\c
mysql>
```

### 8.3 Lệnh của client và câu lệnh SQL

Những gì bạn gõ ở dấu nhắc `mysql>` thuộc một trong hai loại:

- **Câu lệnh SQL** (`SELECT`, `CREATE TABLE`, `SHOW DATABASES`...): được gửi tới server, server thực thi.
  Cần dấu kết thúc.
- **Lệnh của client**: chính chương trình `mysql` xử lý, không gửi tới server. Mỗi lệnh có dạng dài (không
  phân biệt hoa thường, có thể có `;` ở cuối hoặc không) và dạng ngắn bắt đầu bằng `\` (phân biệt hoa
  thường, không nên thêm `;`).

| Dạng dài | Dạng ngắn | Làm gì |
|---|---|---|
| `help` | `\h` hoặc `\?` | Liệt kê các lệnh của client |
| `clear` | `\c` | Bỏ câu lệnh đang gõ dở |
| `go` | `\g` | Gửi câu lệnh (giống `;`) |
| `ego` | `\G` | Gửi câu lệnh, in kết quả theo chiều dọc: mỗi cột một dòng |
| `status` | `\s` | In thông tin kết nối: user, phiên bản server, kết nối qua socket hay TCP |
| `use` | `\u` | Chọn database mặc định |
| `source` | `\.` | Chạy các câu lệnh trong một file SQL |
| `warnings` | `\W` | Tự in warning sau mỗi câu lệnh |
| `system` | `\!` | Chạy một lệnh shell (Unix) |
| `quit` hoặc `exit` | `\q` | Thoát |

`\G` rất hữu ích khi bảng có nhiều cột, kết quả dạng bảng ngang bị tràn màn hình:

```
mysql> SELECT VERSION(), CURRENT_USER()\G
*************************** 1. row ***************************
     VERSION(): 8.4.11
CURRENT_USER(): root@localhost
1 row in set (0.00 sec)
```

(output minh hoạ). `\s` cho biết bạn đang kết nối kiểu gì, rất có ích khi nghi ngờ chuyện `localhost`
với `127.0.0.1`:

```
mysql> \s
--------------
...
Connection id:          9
Current database:
Current user:           root@localhost
...
Server version:         8.4.11 MySQL Community Server - GPL
...
Connection:             Localhost via UNIX socket
...
UNIX socket:            /var/run/mysqld/mysqld.sock
...
```

(output minh hoạ, đã rút gọn). Nếu kết nối qua TCP, dòng `Connection:` sẽ là `127.0.0.1 via TCP/IP` và
thay cho dòng `UNIX socket:` là dòng `TCP port:`.

### 8.4 Chạy cả một file SQL

Khi có sẵn nhiều câu lệnh (tạo bảng, nạp dữ liệu mẫu), ghi chúng vào một file `.sql` rồi cho client chạy
cả file. Hai cách:

```sh
# Cách 1, ở terminal: đưa file vào client qua chuyển hướng đầu vào (batch mode)
mysql -h 127.0.0.1 -u root -p shop < schema.sql

# Với Docker, file nằm trên máy host: thêm -i (không có -t) để chuyển nội dung file vào container
docker exec -i my84 mysql -uroot -proot shop < schema.sql
```

```sql
-- Cách 2, khi đang ở dấu nhắc mysql>: lệnh source của client (đường dẫn là đường dẫn trên máy chạy client)
source schema.sql
```

Khi chạy kiểu batch như cách 1, kết quả của các câu `SELECT` in ra dạng các cột cách nhau bằng tab thay
vì khung bảng (thêm `-t` nếu muốn khung bảng). Mặc định, gặp câu lệnh lỗi đầu tiên là client dừng; tuỳ
chọn `--force` cho phép chạy tiếp các câu sau.

Ở lệnh Docker trên, mật khẩu `-proot` nằm trên dòng lệnh vì `docker exec -i` đang nhận nội dung file từ
đầu vào chuẩn, không còn chỗ để gõ mật khẩu. Chấp nhận được trên máy học tập, không dùng trên server thật.

### 8.5 Không gõ lại thông tin kết nối mỗi lần

Client đọc tuỳ chọn mặc định từ các *option file*. Trên Linux và macOS, file riêng của từng người dùng là
`~/.my.cnf`; nhóm `[client]` trong file này được mọi chương trình client của MySQL đọc (server `mysqld`
thì không):

```ini
# ~/.my.cnf
[client]
host=127.0.0.1
port=3306
user=root
password=root
```

Sau đó chỉ cần gõ `mysql` là kết nối. Vì file chứa mật khẩu dạng chữ thường, hãy giới hạn quyền đọc chỉ
cho chính bạn: `chmod 600 ~/.my.cnf`.

Cách thứ hai là `mysql_config_editor`, công cụ lưu thông tin đăng nhập vào file `~/.mylogin.cnf` ở dạng
đã làm rối (obfuscated), không phải chữ thường:

```sh
mysql_config_editor set --login-path=local84 --host=127.0.0.1 --user=root --password
mysql --login-path=local84
```

Tài liệu MySQL nói rõ việc làm rối này không chặn được một kẻ tấn công quyết tâm có quyền đọc file của
bạn; nó chỉ tránh việc mật khẩu nằm trần trong file.

## 9. Database (schema) trong MySQL

### 9.1 Database là một "ngăn chứa" bảng

Một server MySQL chứa nhiều *database*; mỗi database chứa các bảng (và các đối tượng khác như view, stored
procedure, trigger). Thường mỗi ứng dụng dùng một database riêng: database `shop` cho cửa hàng, database
`blog` cho blog, cùng nằm trên một server.

```
Server MySQL (một tiến trình mysqld)
├── shop                 <- database của ứng dụng cửa hàng
│   ├── customers        <- bảng
│   └── orders
├── blog
│   └── posts
├── mysql                <- các database hệ thống (mục 9.3)
├── information_schema
├── performance_schema
└── sys
```

Trong MySQL, *schema* và *database* là một: tài liệu MySQL ghi `CREATE SCHEMA` là từ đồng nghĩa của
`CREATE DATABASE`, `DROP SCHEMA` đồng nghĩa với `DROP DATABASE`. Công cụ đồ hoạ như MySQL Workbench gọi
database là schema, nên bạn sẽ gặp cả hai từ. (PostgreSQL thì khác hẳn, xem mục 9.5.)

Về mặt lưu trữ, mỗi database trong MySQL là một thư mục con nằm trong thư mục dữ liệu (datadir) của
server, và mỗi bảng tương ứng với ít nhất một file trong thư mục đó. Đây là lý do tên database và tên bảng
chịu ảnh hưởng của hệ điều hành (mục 9.4).

### 9.2 Tạo, chọn, xoá database

Từ đây trở đi là các lệnh chạy được ở dấu nhắc `mysql>`.

```sql
-- Tạo database. IF NOT EXISTS: đã có thì bỏ qua (chỉ sinh một warning) thay vì báo lỗi
CREATE DATABASE IF NOT EXISTS shop;

-- Có thể ghi rõ bảng mã và collation mặc định cho database
CREATE DATABASE IF NOT EXISTS blog
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;
```

Không ghi `CHARACTER SET` thì database nhận giá trị mặc định của server; với MySQL 8.4 mặc định là bảng mã
`utf8mb4` (lưu được mọi ký tự Unicode, kể cả tiếng Việt và emoji) với collation `utf8mb4_0900_ai_ci`.
Bảng mã và collation là gì, chọn thế nào: [chương 03](03-kieu-du-lieu.md).

Chạy lại `CREATE DATABASE shop;` (không có `IF NOT EXISTS`) khi `shop` đã tồn tại:

```
ERROR 1007 (HY000): Can't create database 'shop'; database exists
```

Chọn database mặc định cho các câu lệnh tiếp theo, và kiểm tra đang đứng ở database nào:

```sql
SELECT DATABASE();   -- chưa chọn database nào: trả về NULL
USE shop;            -- từ giờ "customers" nghĩa là shop.customers
SELECT DATABASE();   -- trả về 'shop'
```

`USE` vừa là câu lệnh SQL, vừa được client `mysql` nhận như lệnh riêng của nó (`use`, dạng ngắn `\u`), nên
trong client có hay không có `;` đều được. Database được chọn giữ nguyên tới khi kết thúc session hoặc gặp một lệnh `USE` khác; nó là trạng thái của riêng kết
nối hiện tại (mục 6.4). Chưa chọn database mà truy vấn một bảng không ghi tên database, server báo:

```
ERROR 1046 (3D000): No database selected
```

`USE` không giới hạn bạn trong một database. Luôn có thể ghi tên đầy đủ `database.bảng` để truy vấn bảng
ở database khác trên cùng server, kể cả ghép bảng của hai database trong một câu:

```sql
USE blog;
SELECT COUNT(*) FROM shop.customers;   -- vẫn đọc được bảng của database shop
                                       -- (chạy được sau khi tạo bảng customers ở mục 10.1)
```

Xoá database:

```sql
DROP DATABASE IF EXISTS blog;
```

⚠️ `DROP DATABASE` xoá mọi bảng trong database cùng toàn bộ dữ liệu, không hỏi lại, và là DDL nên không
rollback được (mục 3.3). Tài liệu MySQL viết: "Be very careful with this statement!". Trên server thật,
trước khi chạy hãy chắc chắn có bản sao lưu ([chương 21](21-backup-restore.md)) và kiểm tra lại bằng
`SELECT DATABASE();`, `\s` xem mình đang kết nối tới server nào.

### 9.3 Các database hệ thống

Một server MySQL 8.4 mới cài đã có sẵn bốn database:

| Database | Chứa gì |
|---|---|
| `mysql` | *System schema*: các bảng server cần khi chạy, gồm *data dictionary* (siêu dữ liệu về mọi database, bảng, cột), bảng tài khoản và quyền, múi giờ... |
| `information_schema` | Cách đọc *metadata* (thông tin về dữ liệu: có database nào, bảng nào, cột kiểu gì, quyền gì) bằng câu `SELECT` chuẩn. Toàn là view chỉ đọc, không có file hay thư mục thật |
| `performance_schema` | Số liệu theo dõi hoạt động bên trong server ở mức thấp: câu lệnh, chờ khoá, I/O ([chương 24](24-van-hanh-monitoring.md)) |
| `sys` | Các view và thủ tục giúp đọc số liệu của `performance_schema` dễ hơn |

⚠️ Không tạo bảng của ứng dụng trong các database này, và không sửa tay dữ liệu trong `mysql`. Muốn
thêm user, phân quyền thì dùng `CREATE USER`, `GRANT` ([chương 18](18-user-quyen-bao-mat.md)), không
`INSERT` thẳng vào bảng hệ thống.

### 9.4 Đặt tên database và bảng

Quy tắc của MySQL cho tên (identifier) không bao trong backtick:

- Ký tự được dùng: chữ cái Latin cơ bản, chữ số, `$`, `_` (và các ký tự Unicode từ U+0080 tới U+FFFF).
- Được bắt đầu bằng chữ số, nhưng không được chỉ gồm toàn chữ số.
- Tên database, bảng, cột không được kết thúc bằng dấu cách.
- Dài tối đa 64 ký tự với database, bảng, cột.

Quy tắc là vậy, còn quy ước nên theo thì đơn giản hơn: chỉ dùng chữ thường không dấu, chữ số và `_`,
dạng *snake_case* (`order_items`, `created_at`); bảng thường đặt tên số nhiều (`customers`, `orders`),
cũng là quy ước mặc định của Laravel. Không dấu tiếng Việt, không dấu cách, không trùng từ khoá.

⚠️ Chữ hoa chữ thường trong tên database và tên bảng. Vì mỗi database là một thư mục và mỗi bảng là file,
việc phân biệt hoa thường phụ thuộc hệ điều hành, điều khiển bởi biến `lower_case_table_names`:

| Giá trị | Ý nghĩa | Mặc định trên |
|---|---|---|
| `0` | Lưu đúng chữ hoa thường như khi tạo; so sánh tên **phân biệt** hoa thường | Unix, Linux (gồm cả MySQL chạy trong Docker) |
| `1` | Lưu tên bảng dạng chữ thường; so sánh không phân biệt | Windows |
| `2` | Lưu đúng như khi tạo, nhưng khi tra cứu thì đổi sang chữ thường; so sánh không phân biệt | macOS |

Hệ quả: bảng tạo tên `customers`, code viết `SELECT * FROM Customers`. Trên MySQL cài bằng Homebrew trên
macOS câu này chạy bình thường; lên server Linux (hoặc MySQL trong Docker) nó báo:

```
ERROR 1146 (42S02): Table 'shop.Customers' doesn't exist
```

Ngoài ra, giá trị này chỉ đặt được lúc khởi tạo server lần đầu, đổi về sau bị cấm. Cách tránh tận gốc:
luôn đặt và gọi tên database, bảng bằng chữ thường. Tên cột thì khác: tài liệu MySQL ghi tên cột, tên
index, tên stored routine không phân biệt hoa thường trên mọi nền tảng.

### 9.5 Đối chiếu PostgreSQL: database và schema là hai tầng khác nhau

Trong PostgreSQL, cấu trúc có thêm một tầng:

```
PostgreSQL cluster (một server)
├── database shop
│   ├── schema public        <- schema mặc định, có sẵn trong mọi database mới
│   │   ├── customers
│   │   └── orders
│   └── schema reporting
│       └── daily_sales
└── database blog
    └── schema public
        └── posts
```

- Một *cluster* (một server PostgreSQL) chứa nhiều database.
- Mỗi database chứa nhiều *schema*; schema chứa bảng. Tạo bảng không ghi schema thì bảng vào schema
  `public`, có sẵn trong mọi database mới.
- Một kết nối chỉ truy cập được dữ liệu của đúng một database, là database ghi trong yêu cầu kết nối.
  Muốn đọc bảng ở database khác phải mở kết nối khác (hoặc dùng extension chuyên dụng). Ngược lại, giữa
  các schema trong cùng một database thì truy vấn qua lại thoải mái: `SELECT ... FROM reporting.daily_sales`.

| | MySQL | PostgreSQL |
|---|---|---|
| Tầng chứa bảng | server → database (= schema) → bảng | cluster → database → schema → bảng |
| `CREATE SCHEMA x` | Giống hệt `CREATE DATABASE x` | Tạo một schema bên trong database đang kết nối |
| Truy vấn chéo | `db_khac.bang` được, cùng server | `schema_khac.bang` được; `database_khac` thì không, trong một kết nối |
| Đổi database đang dùng | `USE ten_db;` | Kết nối lại: trong `psql` dùng `\c ten_db` |

Vì vậy, khi chuyển một hệ thống gồm nhiều database MySQL sang PostgreSQL, cách tương ứng thường là nhiều
schema trong một database PostgreSQL, chứ không phải nhiều database.

## 10. Khám phá một database

Khi được giao một database lạ (dự án mới vào, server production cần điều tra), việc đầu tiên là nhìn xem
trong đó có gì. Mục này dùng bốn lệnh `SHOW`/`DESCRIBE` của MySQL và cách tương đương bằng
`information_schema`.

### 10.1 Dữ liệu mẫu

Chạy đoạn sau ở dấu nhắc `mysql>` (hoặc lưu thành `shop.sql` rồi chạy theo mục 8.4). Cú pháp `CREATE
TABLE`, kiểu dữ liệu và ràng buộc sẽ học kỹ ở [chương 03](03-kieu-du-lieu.md) và
[chương 04](04-ddl-constraint.md); ở đây chỉ cần chạy để có cái mà khám phá.

```sql
CREATE DATABASE IF NOT EXISTS shop;
USE shop;

CREATE TABLE customers (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    name       VARCHAR(100) NOT NULL,
    email      VARCHAR(255) NOT NULL,
    city       VARCHAR(100) NULL,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_customers_email (email)
);

CREATE TABLE orders (
    id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    customer_id INT UNSIGNED  NOT NULL,
    total       DECIMAL(12,2) NOT NULL,
    created_at  DATETIME      NOT NULL,
    PRIMARY KEY (id),
    KEY idx_orders_customer (customer_id),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) REFERENCES customers (id)
);

INSERT INTO customers (name, email, city) VALUES
    ('An',   'an@example.com',   'Hà Nội'),
    ('Bình', 'binh@example.com', 'Đà Nẵng'),
    ('Chi',  'chi@example.com',  'Hà Nội');

INSERT INTO orders (id, customer_id, total, created_at) VALUES
    (10, 1, 250000, '2026-10-01 09:00:00'),
    (11, 1,  90000, '2026-10-02 14:30:00'),
    (12, 3, 120000, '2026-10-02 15:00:00');
```

Đây đúng là hai bảng ở mục 2.1. Bảng `customers` không ghi `id` khi `INSERT` nên MySQL tự cấp 1, 2, 3
(nhờ `AUTO_INCREMENT`); bảng `orders` ghi `id` tường minh là 10, 11, 12 cho khớp hình minh hoạ.

### 10.2 `SHOW DATABASES`: server có những database nào

```sql
SHOW DATABASES;
```

```
+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| shop               |
| sys                |
+--------------------+
5 rows in set (0.00 sec)
```

(output minh hoạ). Bốn database hệ thống (mục 9.3) cộng `shop` vừa tạo. Danh sách chỉ gồm các database mà
tài khoản của bạn có quyền nào đó; đăng nhập bằng user ít quyền sẽ thấy ít hơn. `SHOW SCHEMAS` là từ
đồng nghĩa. Lọc theo tên bằng `LIKE`, trong đó `%` khớp chuỗi ký tự bất kỳ:

```sql
SHOW DATABASES LIKE 'sh%';   -- chỉ những database có tên bắt đầu bằng "sh"
```

### 10.3 `SHOW TABLES`: database có những bảng nào

```sql
USE shop;
SHOW TABLES;
```

```
+----------------+
| Tables_in_shop |
+----------------+
| customers      |
| orders         |
+----------------+
2 rows in set (0.00 sec)
```

(output minh hoạ). Tên cột kết quả có dạng `Tables_in_<tên database>`. Vài biến thể:

```sql
SHOW TABLES FROM mysql;      -- xem bảng của database khác mà không cần USE
SHOW TABLES LIKE 'cust%';    -- lọc theo tên
SHOW FULL TABLES;            -- thêm cột Table_type: BASE TABLE (bảng thật) hay VIEW
```

`SHOW TABLES` liệt kê cả view (sẽ học ở [chương 17](17-view-procedure-trigger.md)), nhưng không liệt kê
bảng tạm (`TEMPORARY`), và bỏ qua những bảng bạn không có quyền gì.

### 10.4 `DESCRIBE`: bảng có những cột nào

```sql
DESCRIBE customers;
```

```
+------------+--------------+------+-----+-------------------+-------------------+
| Field      | Type         | Null | Key | Default           | Extra             |
+------------+--------------+------+-----+-------------------+-------------------+
| id         | int unsigned | NO   | PRI | NULL              | auto_increment    |
| name       | varchar(100) | NO   |     | NULL              |                   |
| email      | varchar(255) | NO   | UNI | NULL              |                   |
| city       | varchar(100) | YES  |     | NULL              |                   |
| created_at | datetime     | NO   |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+------------+--------------+------+-----+-------------------+-------------------+
5 rows in set (0.00 sec)
```

(output minh hoạ). Ý nghĩa từng cột của kết quả, theo tài liệu MySQL:

| Cột | Ý nghĩa |
|---|---|
| `Field` | Tên cột |
| `Type` | Kiểu dữ liệu |
| `Null` | `YES` nếu cột được chứa `NULL`, `NO` nếu không |
| `Key` | Cột có nằm trong index không: `PRI` là (một phần của) primary key; `UNI` là cột đầu của một index `UNIQUE`; `MUL` là cột đầu của một index không unique, nơi một giá trị được lặp nhiều lần; rỗng là không được index (hoặc chỉ là cột phụ trong một index nhiều cột không unique). Nhiều giá trị cùng đúng thì hiện theo ưu tiên `PRI`, rồi `UNI`, rồi `MUL` |
| `Default` | Giá trị mặc định. `NULL` khi mặc định là `NULL` hoặc khi cột không khai báo `DEFAULT` |
| `Extra` | Thông tin thêm: `auto_increment`; `on update CURRENT_TIMESTAMP`; `VIRTUAL GENERATED`/`STORED GENERATED` cho cột sinh tự động; `DEFAULT_GENERATED` khi giá trị mặc định là một biểu thức (như `CURRENT_TIMESTAMP` ở cột `created_at`) |

⚠️ Cột `Default` hiện `NULL` cho `name` không có nghĩa `name` mặc định bằng `NULL`: cột đó là
`NOT NULL` và không khai báo `DEFAULT`, nên `INSERT` mà thiếu `name` sẽ bị từ chối (ở `sql_mode` mặc
định). Đọc `Default` luôn đi cùng cột `Null`.

Thử với bảng `orders`, cột `customer_id` có `Key` là `MUL` vì nó là cột đầu của index không unique
`idx_orders_customer`: nhiều đơn hàng có cùng một `customer_id`.

Các cách viết tương đương: `DESC customers`, `SHOW COLUMNS FROM customers`, `EXPLAIN customers` (tài
liệu MySQL ghi `DESCRIBE` và `EXPLAIN` là từ đồng nghĩa, nhưng thực tế `EXPLAIN` hầu như chỉ dùng để xem
kế hoạch thực thi câu truy vấn, [chương 12](12-explain-toi-uu-query.md)). `SHOW FULL COLUMNS FROM
customers` hiện thêm collation, quyền và comment của từng cột.

### 10.5 `SHOW CREATE TABLE`: câu lệnh tạo ra bảng

`DESCRIBE` cho thấy các cột nhưng không cho thấy hết: tên index, khoá ngoại, engine, bảng mã. `SHOW CREATE
TABLE` in lại câu `CREATE TABLE` đầy đủ mà server dùng để tạo lại đúng bảng đó. Câu này dài nên kết thúc
bằng `\G` để in theo chiều dọc:

```sql
SHOW CREATE TABLE orders\G
```

```
*************************** 1. row ***************************
       Table: orders
Create Table: CREATE TABLE `orders` (
  `id` int unsigned NOT NULL AUTO_INCREMENT,
  `customer_id` int unsigned NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `created_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_orders_customer` (`customer_id`),
  CONSTRAINT `fk_orders_customer` FOREIGN KEY (`customer_id`) REFERENCES `customers` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
1 row in set (0.00 sec)
```

(output minh hoạ). Những điều đọc được mà `DESCRIBE` không cho thấy:

- Bảng dùng engine `InnoDB` dù câu tạo bảng không ghi engine (InnoDB là engine mặc định, mục 4.1).
- Bảng mã và collation mặc định của bảng được thừa hưởng từ database: `utf8mb4`, `utf8mb4_0900_ai_ci`.
- Tên và định nghĩa đầy đủ của index, khoá ngoại.
- `AUTO_INCREMENT=13`: giá trị tự tăng tiếp theo sẽ là 13, vì ta đã chèn `id` lớn nhất là 12.
- Server viết lại câu lệnh theo dạng chuẩn hoá của nó: từ khoá kiểu dữ liệu viết thường, mọi tên đều
  bao trong backtick. Nó không phải nguyên văn câu bạn đã gõ.

`SHOW CREATE TABLE` là cách nhanh nhất để chép cấu trúc một bảng sang nơi khác, hoặc so sánh cấu trúc bảng
giữa môi trường dev và production. Có các lệnh cùng họ: `SHOW CREATE DATABASE shop`, `SHOW CREATE VIEW`...

### 10.6 Cùng thông tin đó qua `information_schema`

Các lệnh `SHOW` là cú pháp riêng của MySQL. `information_schema` (mục 9.3) cho phép lấy cùng thông tin
bằng câu `SELECT` bình thường, nên lọc, sắp xếp, ghép bảng tuỳ ý, và tên `information_schema` cùng nhiều
view của nó cũng có trong PostgreSQL:

```sql
-- Các bảng của database shop
SELECT TABLE_NAME, TABLE_TYPE, ENGINE
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'shop'
ORDER BY TABLE_NAME;

-- Các cột của bảng customers, theo đúng thứ tự trong bảng
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'shop' AND TABLE_NAME = 'customers'
ORDER BY ORDINAL_POSITION;
```

Kết quả mong đợi của câu thứ nhất:

```
+------------+------------+--------+
| TABLE_NAME | TABLE_TYPE | ENGINE |
+------------+------------+--------+
| customers  | BASE TABLE | InnoDB |
| orders     | BASE TABLE | InnoDB |
+------------+------------+--------+
```

Một câu hỏi `SHOW` không trả lời được, nhưng `information_schema` thì được: "trong cả server, bảng nào có
cột tên `email`?"

```sql
SELECT TABLE_SCHEMA, TABLE_NAME
FROM information_schema.COLUMNS
WHERE COLUMN_NAME = 'email';
```

### 10.7 Đối chiếu: các lệnh tương đương trong `psql`

`psql` là client dòng lệnh của PostgreSQL. Thay vì lệnh `SHOW`, nó dùng các *meta-command* bắt đầu bằng
`\`, do chính `psql` xử lý:

| Việc | MySQL (client `mysql`) | PostgreSQL (client `psql`) |
|---|---|---|
| Liệt kê database | `SHOW DATABASES;` | `\l` |
| Chuyển database | `USE shop;` | `\c shop` (mở kết nối mới tới database đó) |
| Liệt kê schema | (schema chính là database) | `\dn` |
| Liệt kê bảng | `SHOW TABLES;` | `\dt` |
| Xem cấu trúc bảng | `DESCRIBE customers;` | `\d customers` (gồm cả index, ràng buộc) |
| Thoát | `\q`, `exit`, `quit` | `\q` |

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| `ERROR 2002 (HY000): Can't connect to local MySQL server through socket ...` | Host là `localhost` nên client đi qua Unix socket, nhưng server không chạy trên máy này (ví dụ đang chạy trong Docker) hoặc socket nằm chỗ khác | Dùng `-h 127.0.0.1` để kết nối TCP (mục 6.3) |
| `ERROR 2003 (HY000): Can't connect to MySQL server on '127.0.0.1:3306'` | Server chưa chạy, chưa khởi tạo xong, sai port, hoặc container chưa mở port | `docker ps`, `docker logs my84` chờ dòng `ready for connections` có `port: 3306`; kiểm tra `-p` khi `docker run` (mục 7.2) |
| `ERROR 1045 (28000): Access denied for user 'root'@'...' (using password: YES)` | Sai mật khẩu, hoặc volume cũ còn mật khẩu từ lần khởi tạo trước (biến `MYSQL_ROOT_PASSWORD` chỉ dùng lúc khởi tạo) | Dùng đúng mật khẩu cũ, hoặc xoá container và volume rồi tạo lại nếu là dữ liệu học tập |
| `ERROR 1049 (42000): Unknown database 'root'` sau khi gõ `-p root` | Có dấu cách sau `-p` nên `root` bị hiểu là tên database | `-p` rồi gõ mật khẩu khi được hỏi (mục 8.1) |
| `ERROR 1046 (3D000): No database selected` | Truy vấn bảng mà chưa chọn database | `USE shop;` hoặc ghi `shop.customers` (mục 9.2) |
| `ERROR 1146 (42S02): Table 'shop.Customers' doesn't exist` trên Linux, chạy được trên macOS | Tên bảng phân biệt hoa thường trên Linux (`lower_case_table_names=0`) | Đặt và gọi tên bảng bằng chữ thường (mục 9.4) |
| Câu lệnh "treo", dấu nhắc thành `->` hoặc `'>` | Quên `;` hoặc quên đóng nháy | Gõ `;`; nếu là `'>` thì gõ `'` rồi `\c` (mục 8.2) |
| Chạy `mysql:latest` hoặc `brew install mysql` và nhận bản không phải 8.4 | Tag và formula không ghi phiên bản trỏ tới bản mới hơn | `mysql:8.4`, `mysql@8.4` (mục 7.2, 7.3) |
| Kết quả `SELECT` đổi thứ tự giữa các lần chạy | Bảng không có thứ tự dòng; không có `ORDER BY` thì không có gì bảo đảm | Luôn ghi `ORDER BY` khi cần thứ tự (mục 2.4) |
| `ROLLBACK` không lấy lại được thay đổi | Giữa transaction đã chạy một lệnh DDL, gây implicit commit | Không trộn DDL vào transaction trong MySQL (mục 3.3) |
| Test chạy xanh trên SQLite, lỗi trên MySQL production | Hai hệ khác hành vi (ví dụ SQLite nhận chuỗi vào cột `INTEGER`) | Test trên đúng hệ quản trị production dùng (mục 4.3) |
| `Too many connections` | Số kết nối vượt `max_connections` (mặc định 151), thường do nhiều worker PHP-FPM | Tính số kết nối tối đa của ứng dụng (mục 6.4, chương 19) |

## Tóm tắt chương

- Tự ghi file gặp lost update, mất dữ liệu khi sập, tìm kiếm chậm, không ràng buộc, không phân quyền.
  DBMS giải quyết các vấn đề đó; database là dữ liệu, DBMS (MySQL, PostgreSQL...) là phần mềm quản lý nó.
- Mô hình quan hệ lưu dữ liệu trong bảng: dòng là đối tượng, cột là thuộc tính có kiểu. Các bảng liên kết
  bằng giá trị qua primary key và foreign key. Dòng trong bảng không có thứ tự nếu không `ORDER BY`.
- SQL là ngôn ngữ khai báo: mô tả kết quả, DBMS chọn cách thực thi. Các nhóm lệnh: DDL (cấu trúc), DML
  (dữ liệu), DCL (quyền), TCL (transaction). Trong MySQL, DDL gây implicit commit.
- MySQL, PostgreSQL, SQL Server, Oracle chạy kiểu client-server; SQLite nhúng trong ứng dụng. Giáo trình
  dùng MySQL 8.4 LTS, đối chiếu PostgreSQL 18.
- NoSQL gồm nhiều nhóm (key-value, document, wide-column, graph) tối ưu cho các mẫu truy cập riêng;
  database quan hệ là lựa chọn mặc định cho dữ liệu nghiệp vụ.
- Server `mysqld` nghe TCP (port 3306) và Unix socket; `localhost` trên Unix nghĩa là socket, muốn TCP
  dùng `127.0.0.1`. Mỗi kết nối là một session có trạng thái riêng, phục vụ bởi một thread;
  `max_connections` mặc định 151.
- Cài bằng Docker: `docker run ... mysql:8.4`, ghi rõ tag, dùng volume giữ dữ liệu. Homebrew:
  `mysql@8.4`, keg-only, root chưa có mật khẩu.
- Trong MySQL, database và schema là một; trong PostgreSQL schema là tầng nằm trong database.
- Khám phá: `SHOW DATABASES`, `USE`, `SHOW TABLES`, `DESCRIBE`, `SHOW CREATE TABLE`, hoặc `SELECT` từ
  `information_schema`.

## Câu hỏi tự kiểm tra

1. Hai request cùng cộng tiền vào một tài khoản lưu trong file JSON. Mô tả một thứ tự thực thi làm mất
   một khoản cộng. Vì sao `UPDATE ... SET balance = balance + 100` trong database không gặp vấn đề này,
   còn `SELECT` rồi tính trong PHP rồi `UPDATE ... SET balance = 600` thì vẫn có thể gặp? (mục 1.2, 1.4)
2. Phân biệt database và DBMS. Câu "công ty dùng database MySQL" chính xác ra nghĩa là gì?
3. Vì sao một câu `SELECT` không có `ORDER BY` không được phép dựa vào thứ tự kết quả? (mục 2.4)
4. `TRUNCATE TABLE` thuộc nhóm lệnh nào trong MySQL, và điều đó ảnh hưởng gì nếu bạn đang ở giữa một
   transaction? (mục 3.3)
5. Khi nào bạn chọn SQLite, khi nào chọn MySQL? Vì sao dùng SQLite để chạy test cho ứng dụng MySQL là
   rủi ro?
6. Lệnh `mysql -h localhost -u root -p` và `mysql -h 127.0.0.1 -u root -p` khác nhau ở đâu trên Linux,
   macOS? Tình huống nào cái đầu lỗi mà cái sau chạy được? (mục 6.3)
7. Bạn mở hai cửa sổ `mysql`, cửa sổ thứ nhất `USE shop;`. Cửa sổ thứ hai `SELECT DATABASE();` trả về
   gì? Vì sao?
8. Đã chạy `docker run ... -e MYSQL_ROOT_PASSWORD=root -v my84data:/var/lib/mysql mysql:8.4`, sau đó xoá
   container và chạy lại với `MYSQL_ROOT_PASSWORD=secret`, cùng volume. Mật khẩu root lúc này là gì?
9. Trong kết quả `DESCRIBE`, cột `Key` có các giá trị `PRI`, `UNI`, `MUL` nghĩa là gì? Cột `Default`
   hiện `NULL` có chắc là cột đó mặc định bằng `NULL` không?
10. `CREATE SCHEMA reporting;` làm gì trong MySQL, và làm gì trong PostgreSQL? (mục 9.5)

## Bài tập

1. **Lost update bằng file.** Viết lại ví dụ ở mục 1.2 nhưng cho hai tiến trình PHP thật chạy song song
   (chạy hai lệnh `php` cùng lúc ở hai terminal, mỗi tiến trình lặp 1000 lần "đọc file, cộng 1, ghi
   file"). Kết quả cuối có phải 2000 không? Sau đó thêm `flock()` cho đúng và chạy lại. Ghi nhận xét về
   những gì bạn phải tự lo mà một DBMS làm sẵn.
2. **Cài đặt và kết nối.** Cài MySQL 8.4 bằng Docker theo mục 7.2. Kết nối bằng `docker exec` và (nếu có
   client trên máy) bằng `-h 127.0.0.1`. Ở mỗi kết nối, chạy `\s`, `SELECT CURRENT_USER();`,
   `SELECT CONNECTION_ID();` và giải thích vì sao kết quả khác nhau. Mở thêm một kết nối và tìm cả hai
   kết nối trong `SHOW PROCESSLIST`.
3. **Khám phá.** Tạo dữ liệu mẫu ở mục 10.1 bằng cách lưu thành `shop.sql` và chạy theo mục 8.4. Sau
   đó, chỉ dùng các lệnh trong mục 10, trả lời: bảng nào có khoá ngoại và trỏ tới đâu; cột nào cho phép
   `NULL`; giá trị `AUTO_INCREMENT` tiếp theo của `customers` là bao nhiêu. Viết thêm một câu `SELECT` trên
   `information_schema.COLUMNS` liệt kê mọi cột kiểu `datetime` trong database `shop`.
4. **Đối chiếu PostgreSQL (tuỳ chọn).** Chạy PostgreSQL 18 bằng Docker (mục 7.2), tạo database `shop`,
   trong đó tạo schema `reporting` với một bảng bất kỳ. Dùng `\l`, `\dn`, `\dt reporting.*`, `\d` để
   khám phá, và thử truy vấn một bảng ở database khác để thấy lỗi.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  - [What is MySQL?](https://dev.mysql.com/doc/refman/8.4/en/what-is-mysql.html)
  - [MySQL Releases: Innovation and LTS](https://dev.mysql.com/doc/refman/8.4/en/mysql-releases.html)
  - [Connecting to the MySQL Server Using Command Options](https://dev.mysql.com/doc/refman/8.4/en/connecting.html)
  - [mysql: The MySQL Command-Line Client](https://dev.mysql.com/doc/refman/8.4/en/mysql.html), [mysql Client Commands](https://dev.mysql.com/doc/refman/8.4/en/mysql-commands.html), [Entering Queries](https://dev.mysql.com/doc/refman/8.4/en/entering-queries.html), [Using mysql in Batch Mode](https://dev.mysql.com/doc/refman/8.4/en/batch-mode.html)
  - [Connection Interfaces](https://dev.mysql.com/doc/refman/8.4/en/connection-interfaces.html)
  - [SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/sql-statements.html), [Statements That Cause an Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html)
  - [CREATE DATABASE](https://dev.mysql.com/doc/refman/8.4/en/create-database.html), [USE](https://dev.mysql.com/doc/refman/8.4/en/use.html), [Identifier Case Sensitivity](https://dev.mysql.com/doc/refman/8.4/en/identifier-case-sensitivity.html), [Schema Object Names](https://dev.mysql.com/doc/refman/8.4/en/identifiers.html)
  - [SHOW COLUMNS](https://dev.mysql.com/doc/refman/8.4/en/show-columns.html), [SHOW TABLES](https://dev.mysql.com/doc/refman/8.4/en/show-tables.html), [INFORMATION_SCHEMA Introduction](https://dev.mysql.com/doc/refman/8.4/en/information-schema-introduction.html)
- [Docker Official Image: mysql](https://hub.docker.com/_/mysql), [postgres](https://hub.docker.com/_/postgres)
- PostgreSQL 18: [Concepts](https://www.postgresql.org/docs/18/tutorial-concepts.html), [Architectural Fundamentals](https://www.postgresql.org/docs/18/tutorial-arch.html), [Schemas](https://www.postgresql.org/docs/18/ddl-schemas.html), [A Brief History of PostgreSQL](https://www.postgresql.org/docs/18/history.html), [SQL Conformance](https://www.postgresql.org/docs/18/features.html)
- SQLite: [About SQLite](https://www.sqlite.org/about.html), [Appropriate Uses For SQLite](https://www.sqlite.org/whentouse.html), [Datatypes In SQLite](https://www.sqlite.org/datatype3.html)
- E. F. Codd, "A Relational Model of Data for Large Shared Data Banks", Communications of the ACM 13(6), 1970: [doi:10.1145/362384.362685](https://doi.org/10.1145/362384.362685)
- [PHP: PDO_MYSQL DSN](https://www.php.net/manual/en/ref.pdo-mysql.connection.php)
