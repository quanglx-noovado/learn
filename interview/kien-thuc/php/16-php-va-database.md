# Chương 16. PHP làm việc với database

> [← Mục lục](README.md) · [← Chương 15: PHP và HTTP: request, response, session, cookie, upload](15-php-va-web.md) · [Chương 17: Bảo mật ứng dụng PHP →](17-bao-mat.md)

**Bạn sẽ học được:**

- Từ dòng code PHP tới MySQL server có những tầng nào (PDO, driver, mysqlnd), và vì sao chương này
  chọn PDO thay vì mysqli.
- Mở kết nối bằng DSN, đặt đúng các attribute quan trọng (`ERRMODE_EXCEPTION`, `EMULATE_PREPARES`,
  `DEFAULT_FETCH_MODE`), và hiểu mỗi attribute thay đổi điều gì.
- Prepared statement hoạt động thế nào, vì sao nó chống được SQL injection, chỗ nào nó không bảo vệ
  được; bind tham số kèm kiểu; các fetch mode.
- Transaction với `beginTransaction`/`commit`/`rollBack`, `lastInsertId`, xử lý `PDOException` theo
  SQLSTATE và mã lỗi của MySQL.
- Kiểu dữ liệu PHP nhận về từ MySQL (vì sao `DECIMAL` là string, thay đổi ở PHP 8.1), buffered và
  unbuffered query, mô hình connection của PHP-FPM và rủi ro của persistent connection.
- ORM là gì, và bài toán N+1 nhìn từ tầng PDO.

**Cần biết trước:** [Chương 09: OOP cơ bản](09-oop-co-ban.md) (class, object),
[Chương 12: Lỗi và exception](12-loi-exception.md) (`try/catch`, `Throwable`). Về SQL: biết viết
`SELECT`, `INSERT`, `UPDATE` cơ bản ([giáo trình Database, chương 05](../database/05-select-co-ban.md))
và biết transaction là gì ([giáo trình Database, chương 13](../database/13-transaction-acid.md)). Chưa
đọc hai chương database đó cũng theo được, chỗ nào cần sẽ giải thích ngắn.

Ví dụ viết cho PHP 8.5, output ghi trong comment. Phần lớn ví dụ chạy bằng SQLite (không cần cài
server, xem mục 1.4); ví dụ nào cần MySQL thật sẽ ghi rõ.

## 1. Ứng dụng PHP nói chuyện với database như thế nào

### 1.1 Database là một chương trình khác

Khi code PHP "lấy danh sách user", dữ liệu không nằm trong PHP. Nó nằm trong một chương trình khác:
*database server*. Với MySQL, đó là process `mysqld`, thường chạy trên một máy khác (hoặc một
container khác). PHP đóng vai *client*: mở một *kết nối* (*connection*) tới server, gửi câu SQL dưới
dạng tin nhắn theo *giao thức MySQL* (*MySQL protocol*), rồi chờ server gửi kết quả về.

```
  Máy chạy PHP                                Máy chạy MySQL
 ┌─────────────────────┐   TCP port 3306     ┌──────────────────────┐
 │ process PHP         │ ──── câu SQL ─────▶ │ mysqld               │
 │ (php-fpm worker,    │                     │  parse, tối ưu,      │
 │  hoặc php CLI)      │ ◀── các dòng KQ ─── │  đọc/ghi dữ liệu     │
 └─────────────────────┘                     └──────────────────────┘
```

Ba hệ quả cần nhớ ngay từ đầu:

1. **Mỗi câu query là một lượt đi và về qua mạng** (*round-trip*). Trong cùng data center, một
   round-trip thường chỉ tốn một phần nhỏ của mili giây tới vài mili giây, tuỳ mạng. Một query thì không đáng
   kể, nhưng 500 query nhỏ trong một request là 500 lần chờ. Đây là gốc của bài toán N+1 ở mục 12.
2. **Kết nối là tài nguyên có giới hạn ở phía server.** Server chỉ nhận một số connection tối đa
   (biến `max_connections` của MySQL). Cách PHP mở connection ảnh hưởng trực tiếp tới con số này
   (mục 10).
3. **Server và client có thể hiểu dữ liệu khác nhau.** Ví dụ bảng mã ký tự (charset) hay kiểu số.
   Phần lớn lỗi khó chịu ở tầng này đến từ việc hai bên không thống nhất (mục 2.3 và mục 5).

Ngoại lệ là *SQLite*: nó không có server. SQLite là một thư viện nhúng thẳng vào process PHP, database
là một file (hoặc nằm hẳn trong RAM). Không có mạng, không có connection tới máy khác. Chương này dùng
SQLite để bạn chạy ví dụ ngay, nhưng luôn nói rõ chỗ nào MySQL hành xử khác.

### 1.2 Các tầng từ code tới MySQL

Giữa dòng `$stmt->execute()` và `mysqld` có vài tầng. Biết chúng giúp bạn đọc đúng tài liệu và đoán
đúng chỗ một lỗi phát sinh.

```
 Code của bạn            $stmt = $pdo->prepare('SELECT ... WHERE id = ?'); $stmt->execute([42]);
     │
 PDO (extension lõi)     API chung cho mọi database: class PDO, PDOStatement, PDOException
     │
 Driver PDO_MYSQL        phần riêng cho MySQL: DSN "mysql:...", attribute Pdo\Mysql::ATTR_*
     │
 mysqlnd                 thư viện client viết bằng C, nằm sẵn trong PHP: nói giao thức MySQL,
     │                   nhận kết quả, chuyển giá trị MySQL thành giá trị PHP
     │   (TCP hoặc Unix socket)
 MySQL server (mysqld)
```

- *PDO* (*PHP Data Objects*) là một *lớp trừu tượng truy cập dữ liệu*: cùng một bộ class và method
  cho MySQL, PostgreSQL, SQLite... PDO tự nó không biết nói chuyện với database nào cả.
- *Driver* là phần cắm vào PDO cho từng database: `pdo_mysql`, `pdo_pgsql`, `pdo_sqlite`. Mỗi driver
  là một extension riêng; thiếu driver thì PDO báo "could not find driver".
- *mysqlnd* (*MySQL Native Driver*) là thư viện client mà cả `pdo_mysql` lẫn `mysqli` dùng bên dưới.
  Theo manual, nó là một phần của bản phân phối PHP (có từ PHP 5.3) và là lựa chọn mặc định khi biên
  dịch. Điểm quan trọng với bạn: mysqlnd cấp phát bộ nhớ bằng bộ quản lý bộ nhớ của PHP, nên dữ liệu
  kết quả query nằm trong `memory_limit` của script (mục 9).

PDO chỉ thống nhất **cách gọi** (API), không thống nhất **SQL**. Câu `LIMIT 10` chạy được trên MySQL
và SQLite nhưng không chạy trên SQL Server. Đổi database vẫn phải sửa SQL; PDO chỉ giúp bạn không phải
học lại một bộ hàm mới.

### 1.3 Ba API của PHP cho MySQL

Lịch sử để lại ba cách gọi MySQL. Bạn sẽ gặp cả ba trong code thật:

| API | Ví dụ gọi | Có từ | Tình trạng |
|---|---|---|---|
| `ext/mysql` | `mysql_query("SELECT ...")` | Rất cũ (trước PHP 5) | Deprecated ở PHP 5.5, **bị gỡ hẳn ở PHP 7.0**. Gặp trong code rất cũ, không chạy được trên PHP hiện đại |
| `mysqli` ("MySQL improved") | `$mysqli->query(...)`, `mysqli_query($link, ...)` | PHP 5.0 | Còn phát triển, chỉ dùng cho MySQL/MariaDB, có cả kiểu hàm (procedural) lẫn kiểu object |
| PDO + `pdo_mysql` | `$pdo->prepare(...)` | PHP 5.1 | Còn phát triển, một API cho nhiều database |

Manual PHP đánh giá mysqli và PDO_MySQL đều "recommended for new projects" và hiệu năng ngang nhau
(phần mở rộng chỉ chiếm một phần rất nhỏ thời gian của request). Chương này dạy PDO vì:

1. **Laravel và phần lớn thư viện PHP hiện đại đứng trên PDO.** Mọi query của Eloquent cuối cùng đi
   qua một object `PDO`; hiểu PDO là hiểu Laravel làm gì bên dưới ([chương 27](27-laravel-database-eloquent.md)).
2. **Một API cho nhiều database.** Test bằng SQLite, chạy thật bằng MySQL, cùng một kiểu code.
3. **Placeholder có tên** (`:email`) dễ đọc hơn chuỗi `?` dài, và lỗi được báo bằng exception mặc định
   từ PHP 8.0.

mysqli được nhắc lại ngắn ở mục 11 để bạn đọc được code dùng nó.

### 1.4 Chuẩn bị môi trường chạy ví dụ

**Cách A: SQLite, không cần server.** Image Docker chính thức `php:8.5-cli` đã có sẵn `pdo_sqlite`.
Phần lớn ví dụ trong chương dùng cách này. Tạo file `db-sqlite.php` dưới đây trong một thư mục, các
ví dụ sau sẽ `require` nó:

```php
<?php
declare(strict_types=1);

// db-sqlite.php: tạo database SQLite nằm trong RAM, có sẵn dữ liệu mẫu.
// Mỗi lần gọi là một database mới tinh, mất khi script kết thúc.
function taoDbMau(): PDO
{
    $pdo = new PDO('sqlite::memory:', options: [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);

    $pdo->exec('
        CREATE TABLE users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            email    TEXT NOT NULL UNIQUE,
            name     TEXT NOT NULL,
            password TEXT NOT NULL,
            balance  INTEGER NOT NULL DEFAULT 0  -- tiền tính bằng đồng, số nguyên
        )');
    $pdo->exec('
        CREATE TABLE posts (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title   TEXT NOT NULL
        )');
    $pdo->exec("
        INSERT INTO users (email, name, password, balance) VALUES
            ('an@example.com',   'An',   'mat-khau-an',   150000),
            ('binh@example.com', 'Bình', 'mat-khau-binh', 0),
            ('chi@example.com',  'Chi',  'mat-khau-chi',  9999)");
    $pdo->exec("
        INSERT INTO posts (user_id, title) VALUES
            (1, 'Bài 1 của An'), (1, 'Bài 2 của An'), (2, 'Bài của Bình'), (3, 'Bài của Chi')");

    return $pdo;
}
```

Cột `password` chứa mật khẩu dạng chữ thường chỉ để minh hoạ SQL injection ở mục 3. Ứng dụng thật
không bao giờ lưu mật khẩu như vậy; cách đúng (`password_hash`) ở [chương 17](17-bao-mat.md).

Chạy một ví dụ (trong thư mục chứa file):

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php vi-du.php
```

**Cách B: MySQL 8.4 thật.** Cần hai thứ: một MySQL server và một PHP có extension `pdo_mysql`.
⚠️ Image `php:8.5-cli` có `mysqlnd` nhưng **không** có sẵn `pdo_mysql`/`mysqli` (cũng không có `bcmath`,
dùng ở mục 5.2); phải tự cài bằng script `docker-php-ext-install` có trong image. Các lệnh dưới chạy ở terminal của máy host:

```bash
# 1. MySQL 8.4 (nếu đã có container my84 từ giáo trình Database chương 01 thì bỏ qua)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4

# 2. Một mạng Docker để container PHP gọi được MySQL bằng tên "my84"
docker network create learn-net
docker network connect learn-net my84

# 3. Image PHP 8.5 có thêm pdo_mysql, mysqli và bcmath (Dockerfile đọc từ stdin)
docker build -t php85-mysql - <<'EOF'
FROM php:8.5-cli
RUN docker-php-ext-install pdo_mysql mysqli bcmath
EOF

# 4. Chạy ví dụ (trong thư mục chứa file), DSN dùng host=my84
docker run --rm --network learn-net -v "$PWD":/app -w /app php85-mysql php vi-du.php
```

Dữ liệu mẫu phía MySQL, chạy bằng `docker exec -it my84 mysql -uroot -proot`:

```sql
CREATE DATABASE ch16 CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE ch16;

CREATE TABLE users (
    id         BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    email      VARCHAR(255)  NOT NULL UNIQUE,
    name       VARCHAR(100)  NOT NULL,
    balance    DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    is_active  TINYINT(1)    NOT NULL DEFAULT 1,
    created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE posts (
    id      BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NOT NULL,
    title   VARCHAR(200)    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

INSERT INTO users (email, name, balance) VALUES
    ('an@example.com',   'An',   1500.50),
    ('binh@example.com', 'Bình', 0.00),
    ('chi@example.com',  'Chi',  99.99);

INSERT INTO posts (user_id, title) VALUES
    (1, 'Bài 1 của An'), (1, 'Bài 2 của An'), (2, 'Bài của Bình'), (3, 'Bài của Chi');

-- User riêng cho ứng dụng, không dùng root (giáo trình Database chương 18 nói kỹ về phân quyền).
-- Ở đây cấp mọi quyền trên ch16 cho tiện thử; app thật chỉ nên có đúng quyền nó cần.
CREATE USER 'app'@'%' IDENTIFIED BY 'app-secret';
GRANT ALL PRIVILEGES ON ch16.* TO 'app'@'%';
```

Kiểm tra PHP của bạn có những driver nào:

```php
<?php
declare(strict_types=1);

echo implode(', ', PDO::getAvailableDrivers()), "\n";
// Với image php:8.5-cli gốc, in ra: sqlite
// Với image php85-mysql ở trên, có thêm mysql
```

Ngoài Docker: trên Linux, PHP cài từ gói của bản phân phối thường tách driver MySQL thành một gói
riêng (tên gói có chữ `mysql`); trên macOS, PHP cài bằng Homebrew thường đã có sẵn. Lệnh `php -m`
liệt kê các extension đang bật.

## 2. Mở kết nối: DSN, constructor và attribute

### 2.1 DSN: địa chỉ của database

PDO cần biết ba thứ để kết nối: database nào (driver, máy, cổng, tên database), đăng nhập bằng ai, và
các tuỳ chọn. Phần thứ nhất được gói trong một chuỗi gọi là *DSN* (*Data Source Name*). Dạng chung:

```
<tên driver>:<phần riêng của driver>
```

Với MySQL, phần riêng là các cặp `khoá=giá trị` ngăn bằng dấu `;`:

| Khoá | Ý nghĩa | Ví dụ |
|---|---|---|
| `host` | Tên máy hoặc IP của MySQL server | `host=127.0.0.1`, `host=my84` |
| `port` | Cổng, mặc định của MySQL là 3306 | `port=3307` |
| `dbname` | Database chọn sẵn sau khi kết nối | `dbname=ch16` |
| `unix_socket` | Đường dẫn Unix socket (không dùng cùng `host`/`port`) | `unix_socket=/tmp/mysql.sock` |
| `charset` | Bảng mã của kết nối (mục 2.3) | `charset=utf8mb4` |

```php
$dsn = 'mysql:host=127.0.0.1;port=3306;dbname=ch16;charset=utf8mb4';   // MySQL qua TCP
$dsn = 'mysql:unix_socket=/var/run/mysqld/mysqld.sock;dbname=ch16';   // MySQL qua Unix socket
$dsn = 'sqlite:/var/data/app.db';                                     // SQLite, một file
$dsn = 'sqlite::memory:';                                             // SQLite trong RAM
```

⚠️ `localhost` không giống `127.0.0.1`. Theo manual PDO_MYSQL, trên Unix, `host=localhost` khiến
driver kết nối qua **Unix socket** (file socket cục bộ, vị trí lấy từ ini `pdo_mysql.default_socket`)
chứ không qua TCP. Hệ quả hay gặp:

- PHP và MySQL nằm ở hai container khác nhau: `localhost` trong container PHP là chính container PHP,
  không có file socket nào của MySQL ở đó, kết nối thất bại. Dùng tên container/service (`host=my84`)
  hoặc IP.
- Muốn chắc chắn đi TCP trên cùng máy thì ghi `127.0.0.1`.

DSN cũng chấp nhận `user` và `password`, nhưng tham số thứ hai và ba của constructor được ưu tiên hơn.
Đừng nhét mật khẩu vào DSN: DSN hay bị in ra log khi debug.

### 2.2 Tạo object PDO

```php
<?php
declare(strict_types=1);

$pdo = new PDO(
    'mysql:host=my84;dbname=ch16;charset=utf8mb4',   // DSN
    'app',                                           // username
    'app-secret',                                    // password
    [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION],   // options: mảng attribute => giá trị
);
echo $pdo->getAttribute(PDO::ATTR_SERVER_VERSION), "\n";   // ví dụ: 8.4.7
```

(Cần MySQL thật, cách B ở mục 1.4.)

Constructor kết nối **ngay lập tức**: khi `new PDO(...)` trả về, kết nối TCP đã mở và đã đăng nhập
xong. Nếu không kết nối được, constructor **luôn ném `PDOException`**, bất kể error mode đặt là gì
(manual ghi rõ điều này). Vài thông báo bạn sẽ gặp (chạy thử với MySQL 8.4):

```
SQLSTATE[HY000] [1045] Access denied for user 'app'@'172.18.0.3' (using password: YES)   sai user/mật khẩu
SQLSTATE[HY000] [1049] Unknown database 'khong_ton_tai'                                  sai dbname
SQLSTATE[HY000] [2002] ...                                                               không tới được server
```

Con số trong ngoặc vuông thứ hai là *mã lỗi của MySQL* (1045, 1049) hoặc *mã lỗi phía client* (2xxx,
do mysqlnd sinh ra khi không nói chuyện được với server). IP trong thông báo 1045 là IP mà server nhìn
thấy client, tuỳ mạng của bạn.

⚠️ **Lộ mật khẩu qua stack trace.** Exception không ai bắt sẽ in kèm *stack trace*, và trace có thể in
cả giá trị tham số của mỗi lời gọi hàm. Từ PHP 8.2, tham số `$password` của `PDO::__construct` được
đánh dấu bằng attribute `#[\SensitiveParameter]`, nên trace hiện nó thành một object thay vì giá trị
thật. So sánh trace của cùng một lỗi kết nối:

```
PHP 8.1:  #0 ketnoi.php(5): PDO->__construct('mysql:host=127....', 'app', 'app-secret')
PHP 8.5:  #0 ketnoi.php(5): PDO->__construct('mysql:host=127....', 'app', Object(SensitiveParameterValue))
```

Nhưng hàm **của bạn** bọc quanh PDO (ví dụ `taoKetNoi(string $password)`) thì không được che, trừ khi
bạn tự gắn `#[\SensitiveParameter]` cho tham số đó. Phòng thủ nhiều lớp:

- Production đặt `display_errors = Off` (người dùng không bao giờ thấy trace) và
  `zend.exception_ignore_args = On` (trace không chứa giá trị tham số). Cả hai là giá trị của file
  mẫu `php.ini-production` đi kèm PHP.
- Không truyền mật khẩu qua tham số hàm của bạn khi không cần; đọc thẳng từ biến môi trường hoặc file
  cấu hình ở chỗ tạo PDO.

**`PDO::connect()` và class con theo driver (PHP 8.4).** Từ 8.4 có các class con `Pdo\Mysql`,
`Pdo\Sqlite`, `Pdo\Pgsql`..., chứa method và hằng riêng của từng database. Tạo bằng
`PDO::connect($dsn, ...)`: method này đọc DSN và trả về đúng class con (nếu driver có class con), hoặc
gọi thẳng constructor của class con:

```php
<?php
declare(strict_types=1);

$a = PDO::connect('sqlite::memory:');
echo $a::class, "\n";                    // in ra: Pdo\Sqlite

$b = new PDO('sqlite::memory:');
echo $b::class, "\n";                    // in ra: PDO   (constructor cũ vẫn trả về PDO gốc)

try {
    new Pdo\Mysql('sqlite::memory:');    // class con không khớp driver trong DSN
} catch (PDOException $e) {
    echo $e->getMessage(), "\n";
    // in ra: Pdo\Mysql::__construct() cannot be used for connecting to the "sqlite" driver,
    //        either call Pdo\Sqlite::__construct() or PDO::__construct() instead
}
```

Mọi thứ trong chương này đều dùng được với cả `PDO` gốc lẫn class con, vì class con kế thừa `PDO`.

**Đóng kết nối.** PDO không có method `close()`. Kết nối sống bằng đúng thời gian sống của object
`PDO`: muốn đóng sớm thì xoá **mọi** tham chiếu tới nó (`$pdo = null;`), kể cả các object
`PDOStatement` sinh ra từ nó, vì statement cũng giữ tham chiếu tới connection. Không làm gì thì PHP tự
đóng khi script kết thúc. Với web request ngắn, cứ để PHP tự đóng; đóng sớm chỉ có ý nghĩa với script
chạy lâu (mục 10).

### 2.3 Charset: luôn ghi `charset=utf8mb4` trong DSN

*Charset* (bảng mã) của kết nối quyết định server hiểu các byte bạn gửi lên là chữ gì, và gửi kết quả
về theo bảng mã nào. Cần thống nhất ba nơi: bảng mã của cột trong bảng, bảng mã của kết nối, và bảng
mã PHP đang dùng cho chuỗi (gần như luôn là UTF-8).

- Dùng `utf8mb4`, không dùng `utf8`. Trong MySQL, `utf8` là tên cũ của `utf8mb3`, chỉ chứa ký tự tối
  đa 3 byte, nên không lưu được emoji và một số chữ hiếm (chi tiết ở
  [giáo trình Database, chương 03](../database/03-kieu-du-lieu.md)).
- Không ghi `charset` trong DSN thì mysqlnd dùng charset mà server báo trong lần bắt tay (handshake),
  tức là phụ thuộc cấu hình server. Đừng để việc đúng sai phụ thuộc vào cấu hình ở chỗ khác.

Vì sao ghi trong DSN thay vì chạy `SET NAMES utf8mb4` sau khi kết nối? Manual PHP giải thích: các hàm
escape phía client (`PDO::quote()`, và emulated prepare ở mục 3.5) escape theo charset mà **thư viện
client** biết. `SET NAMES` chỉ đổi charset ở phía server; mysqlnd không biết, vẫn escape theo charset
cũ. Khi hai bên lệch nhau với một số bảng mã nhiều byte (ví dụ GBK), có những chuỗi được escape "đúng"
theo client nhưng server lại đọc ra một dấu nháy thoát khỏi chuỗi: đó là một lỗ SQL injection kinh
điển. Ghi `charset` trong DSN thì client và server cùng biết một bảng mã ngay từ đầu.

Laravel thì sao? Laravel 13 (`MySqlConnector`) không ghi charset vào DSN mà chạy `SET NAMES '...'
COLLATE '...'` sau khi kết nối. Điều này an toàn trong cấu hình mặc định của Laravel vì nó tắt
emulated prepare (mục 3.5): giá trị gửi riêng ở dạng nhị phân, không đi qua bước escape nào.

### 2.4 Attribute: các công tắc của PDO

*Attribute* là các tuỳ chọn điều chỉnh hành vi của PDO. Đặt qua mảng `$options` của constructor, hoặc
sau đó bằng `$pdo->setAttribute(...)`; đọc lại bằng `$pdo->getAttribute(...)`. Một số attribute chỉ có
tác dụng khi đặt **trong constructor**, vì chúng ảnh hưởng tới chính việc kết nối (persistent, SSL,
lệnh chạy lúc kết nối).

Ba attribute nên đặt cho mọi kết nối:

| Attribute | Mặc định | Nên đặt | Vì sao | Mục |
|---|---|---|---|---|
| `PDO::ATTR_ERRMODE` | `ERRMODE_EXCEPTION` (từ PHP 8.0) | `ERRMODE_EXCEPTION` | Lỗi SQL thành exception, không thể bị bỏ qua im lặng. Ghi rõ dù đã là mặc định, để code không phụ thuộc phiên bản | 8 |
| `PDO::ATTR_EMULATE_PREPARES` | `true` với PDO_MYSQL | `false` | Dùng prepared statement thật của MySQL | 3.5 |
| `PDO::ATTR_DEFAULT_FETCH_MODE` | `FETCH_BOTH` | `FETCH_ASSOC` | Mỗi dòng là mảng `tên cột => giá trị`, không bị nhân đôi theo chỉ số số | 4.2 |

Các attribute khác nên biết:

| Attribute | Ý nghĩa | Ghi chú |
|---|---|---|
| `PDO::ATTR_PERSISTENT` | Dùng persistent connection | Chỉ có tác dụng khi đặt trong constructor. Đọc mục 10.2 trước khi bật |
| `PDO::ATTR_STRINGIFY_FETCHES` | Ép mọi giá trị đọc về (trừ `null`) thành string | Mặc định `false`. Bật lên để có lại hành vi cũ trước PHP 8.1 (mục 5.1) |
| `PDO::ATTR_TIMEOUT` | Timeout tính bằng giây | Ý nghĩa **khác nhau theo driver** (manual: SQLite hiểu là thời gian chờ lock ghi, driver khác có thể hiểu là timeout kết nối hoặc đọc) |
| `PDO::ATTR_CASE` | Đổi hoa/thường tên cột trả về | Mặc định `CASE_NATURAL` (giữ nguyên) |
| `PDO::ATTR_ORACLE_NULLS` | Đổi qua lại giữa `null` và chuỗi rỗng | Mặc định `NULL_NATURAL` (không đổi); dùng cho mọi driver, không chỉ Oracle |
| `Pdo\Mysql::ATTR_INIT_COMMAND` | Câu SQL chạy ngay sau khi kết nối | Ví dụ `"SET time_zone = '+00:00'"`. Đặt trong constructor |
| `Pdo\Mysql::ATTR_USE_BUFFERED_QUERY` | Buffered hay unbuffered query | Mặc định `true` (mục 9) |
| `Pdo\Mysql::ATTR_FOUND_ROWS` | `rowCount()` của `UPDATE` đếm dòng *khớp điều kiện* thay vì dòng *thực sự đổi* | Mục 3.3 |
| `Pdo\Mysql::ATTR_SSL_CA`, `ATTR_SSL_CERT`, `ATTR_SSL_KEY`... | Kết nối TLS | Manual: không bật SSL bằng `setAttribute()` được vì kết nối đã tồn tại |

⚠️ **Hằng `PDO::MYSQL_ATTR_*` bị deprecated từ PHP 8.5.** Trước 8.4, attribute riêng của MySQL là hằng
trên class `PDO` (`PDO::MYSQL_ATTR_INIT_COMMAND`, `PDO::MYSQL_ATTR_USE_BUFFERED_QUERY`...). PHP 8.4 thêm
bản mới trên class con (`Pdo\Mysql::ATTR_INIT_COMMAND`...), cùng giá trị. Từ 8.5, dùng hằng cũ sẽ phát
cảnh báo:

```
Deprecated: Constant PDO::MYSQL_ATTR_USE_BUFFERED_QUERY is deprecated since 8.5,
use Pdo\Mysql::ATTR_USE_BUFFERED_QUERY instead
```

Code chỉ chạy trên PHP 8.4 trở lên: dùng `Pdo\Mysql::ATTR_*`. Code phải chạy cả trên PHP cũ hơn 8.4
(thư viện, project chưa nâng cấp): chọn hằng theo phiên bản, như
`PHP_VERSION_ID >= 80400 ? Pdo\Mysql::ATTR_INIT_COMMAND : PDO::MYSQL_ATTR_INIT_COMMAND`.

### 2.5 Gom lại: một hàm tạo kết nối

Đây là hàm tạo kết nối MySQL mà phần còn lại của chương ngầm dùng khi nói "kết nối chuẩn":

```php
<?php
declare(strict_types=1);

// ketnoi-mysql.php (PHP 8.4+). Thông tin đăng nhập lấy từ biến môi trường, không viết cứng trong code.
function taoKetNoiMysql(): PDO
{
    $host = getenv('DB_HOST') ?: 'my84';
    $db   = getenv('DB_NAME') ?: 'ch16';

    return PDO::connect(
        "mysql:host={$host};port=3306;dbname={$db};charset=utf8mb4",
        getenv('DB_USER') ?: 'app',
        getenv('DB_PASS') ?: 'app-secret',
        [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_EMULATE_PREPARES   => false,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            Pdo\Mysql::ATTR_INIT_COMMAND => "SET time_zone = '+00:00'",   // lưu và đọc thời gian theo UTC
        ],
    );
}

$pdo = taoKetNoiMysql();
echo $pdo::class, ' ', $pdo->query('SELECT @@session.time_zone')->fetchColumn(), "\n";
// in ra: Pdo\Mysql +00:00
```

Giá trị mặc định sau `?:` chỉ để chạy thử theo mục 1.4; ứng dụng thật nên báo lỗi khi thiếu biến môi
trường thay vì âm thầm dùng mật khẩu mẫu. Về `time_zone` và cách lưu thời gian, xem
[chương 14](14-file-json-thoi-gian.md) và [giáo trình Database, chương 03](../database/03-kieu-du-lieu.md).

Để so sánh, Laravel 13 đặt sẵn các option này cho mọi kết nối (trích `Illuminate\Database\Connectors\Connector`):

```php
protected $options = [
    PDO::ATTR_CASE => PDO::CASE_NATURAL,
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_ORACLE_NULLS => PDO::NULL_NATURAL,
    PDO::ATTR_STRINGIFY_FETCHES => false,
    PDO::ATTR_EMULATE_PREPARES => false,
];
```

Laravel không đặt `DEFAULT_FETCH_MODE` ở đây; query builder của nó tự chọn fetch mode (mặc định trả về
object `stdClass`), xem [chương 27](27-laravel-database-eloquent.md).

## 3. Chạy câu SQL: exec, query, prepare

### 3.1 Ba cách gửi một câu SQL

| Method | Trả về | Dùng khi |
|---|---|---|
| `$pdo->exec(string $sql)` | `int\|false`: số dòng bị ảnh hưởng | Câu không trả về dòng nào (`CREATE`, `UPDATE`, `DELETE`...) và **không chứa dữ liệu từ bên ngoài** |
| `$pdo->query(string $sql)` | `PDOStatement` (hoặc `false` khi không ở chế độ exception) | Câu `SELECT` cố định, **không chứa dữ liệu từ bên ngoài** |
| `$pdo->prepare(string $sql)` rồi `$stmt->execute([...])` | `prepare` trả `PDOStatement`, `execute` trả `bool` | **Mọi câu có giá trị thay đổi**: từ form, URL, API, file, thậm chí từ chính database |

Quy tắc đơn giản để nhớ: nếu câu SQL có chỗ nào **không phải hằng số viết cứng trong code** thì dùng
`prepare`. Mục 3.2 cho thấy vì sao.

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

$n = $pdo->exec("UPDATE users SET balance = balance + 1000 WHERE balance < 10000");
echo $n, "\n";                                   // in ra: 2   (Bình và Chi)

$stmt = $pdo->query('SELECT COUNT(*) FROM users');
echo $stmt->fetchColumn(), "\n";                 // in ra: 3

$stmt = $pdo->prepare('SELECT name FROM users WHERE id = ?');
$stmt->execute([2]);
echo $stmt->fetchColumn(), "\n";                 // in ra: Bình
```

*`PDOStatement`* là object đại diện cho một câu lệnh đã gửi (hoặc đã chuẩn bị) và kết quả của nó. Bạn
đọc kết quả từ statement (mục 4), có thể `execute()` một statement nhiều lần với giá trị khác nhau.

### 3.2 SQL injection: khi dữ liệu biến thành code

Cách viết tự nhiên nhất với người mới là ghép chuỗi: lấy email người dùng gõ vào, nhét vào giữa câu
SQL. Ví dụ một hàm đăng nhập viết sai (chạy với `db-sqlite.php` ở mục 1.4):

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

// SAI: ghép dữ liệu người dùng vào chuỗi SQL
function dangNhapSai(PDO $pdo, string $email, string $password): ?array
{
    $sql = "SELECT id, name FROM users WHERE email = '$email' AND password = '$password'";
    echo "SQL gửi đi: $sql\n";
    $row = $pdo->query($sql)->fetch();
    return $row === false ? null : $row;
}

echo json_encode(dangNhapSai($pdo, 'an@example.com', 'sai-mat-khau')), "\n";
// SQL gửi đi: SELECT id, name FROM users WHERE email = 'an@example.com' AND password = 'sai-mat-khau'
// null                                   ← sai mật khẩu, đúng là không vào được

echo json_encode(dangNhapSai($pdo, "an@example.com' -- ", 'gi-cung-duoc')), "\n";
// SQL gửi đi: SELECT id, name FROM users WHERE email = 'an@example.com' -- ' AND password = 'gi-cung-duoc'
// {"id":1,"name":"An"}                   ← vào được tài khoản An mà không cần mật khẩu

echo json_encode(dangNhapSai($pdo, "' OR 1=1 -- ", '')), "\n";
// SQL gửi đi: SELECT id, name FROM users WHERE email = '' OR 1=1 -- ' AND password = ''
// {"id":1,"name":"An"}                   ← không cần biết cả email
```

Chuyện gì đã xảy ra? Kẻ tấn công gõ vào ô email một chuỗi có dấu nháy `'`. Dấu nháy đó **đóng chuỗi**
mà bạn mở trong SQL; phần sau nó (`--`, `OR 1=1`) không còn là dữ liệu nữa mà thành **cú pháp SQL**:
`-- ` bắt đầu một comment, nuốt mất điều kiện mật khẩu; `OR 1=1` làm điều kiện luôn đúng. Đây là *SQL
injection* (tiêm SQL): dữ liệu do người ngoài kiểm soát được ghép vào câu lệnh và làm thay đổi ý nghĩa
của câu lệnh. Cùng kỹ thuật đó có thể đọc bảng khác (`UNION SELECT ...`), sửa hoặc xoá dữ liệu.

(Chuỗi tấn công có một dấu cách sau `--` vì MySQL chỉ coi `--` là comment khi theo sau là khoảng trắng;
SQLite thì không đòi điều đó.)

Gốc của vấn đề: **code (câu SQL) và dữ liệu (email) đi chung một chuỗi**, và server không có cách nào
biết đoạn nào do lập trình viên viết, đoạn nào do người dùng gõ. Tự escape bằng `addslashes()` hay
`str_replace("'", ...)` là vá chỗ này hở chỗ khác: quên một chỗ, gặp số không có dấu nháy
(`WHERE id = $id`), gặp bảng mã nhiều byte (mục 2.3). Cách sửa đúng là tách hẳn code khỏi dữ liệu:
prepared statement.

Mục này chỉ nói SQL injection ở góc độ PDO. Toàn cảnh các kiểu tấn công vào ứng dụng PHP (XSS, CSRF,
command injection...) ở [chương 17](17-bao-mat.md).

### 3.3 Prepared statement

*Prepared statement* (câu lệnh chuẩn bị trước) chia việc chạy một câu SQL thành hai bước:

1. **Prepare**: gửi *khuôn* câu lệnh, trong đó mỗi chỗ cần giá trị được thay bằng một *placeholder*
   (chỗ giữ chỗ): dấu `?` (theo vị trí) hoặc `:ten` (theo tên).
2. **Execute**: gửi các giá trị, riêng rẽ khỏi câu lệnh.

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

// ĐÚNG: câu SQL cố định, giá trị đi riêng
function dangNhap(PDO $pdo, string $email, string $password): ?array
{
    $stmt = $pdo->prepare('SELECT id, name FROM users WHERE email = :email AND password = :password');
    $stmt->execute(['email' => $email, 'password' => $password]);
    $row = $stmt->fetch();
    return $row === false ? null : $row;
}

echo json_encode(dangNhap($pdo, 'an@example.com', 'mat-khau-an'), JSON_UNESCAPED_UNICODE), "\n"; // in ra: {"id":1,"name":"An"}
echo json_encode(dangNhap($pdo, "an@example.com' -- ", 'gi-cung-duoc')), "\n";                   // in ra: null
echo json_encode(dangNhap($pdo, "' OR 1=1 -- ", '')), "\n";                                       // in ra: null

// Chuỗi chứa ký tự "nguy hiểm" vẫn được lưu nguyên vẹn, đúng như dữ liệu
$pdo->prepare('INSERT INTO users (email, name, password) VALUES (?, ?, ?)')
    ->execute(["o'reilly@example.com", "O'Reilly -- \"test\"", 'x']);
echo $pdo->query('SELECT name FROM users WHERE id = 4')->fetchColumn(), "\n";   // in ra: O'Reilly -- "test"
```

Vì sao chống được injection: ở bước prepare, server đã phân tích xong cấu trúc câu lệnh (đây là một
`SELECT`, điều kiện `email = <giá trị 1> AND password = <giá trị 2>`). Ở bước execute, giá trị đến
sau và **chỉ được dùng làm giá trị**. Chuỗi `' OR 1=1 -- ` lúc này đơn giản là một email lạ không khớp
dòng nào, giống hệt chuỗi `xyz`. Không có bước "ghép chuỗi" nào để dấu nháy chen vào. (Với emulated
prepare thì cơ chế khác một chút, mục 3.5.)

Lợi ích thứ hai, như manual mô tả: câu lệnh chỉ cần phân tích một lần, rồi `execute()` nhiều lần với
giá trị khác nhau. Lưu ý với PHP-FPM: prepared statement thuộc về **một connection** (MySQL gọi là
*session*) và mất khi connection đóng, tức là thường mất khi request kết thúc. Lợi ích hiệu năng chỉ
có khi bạn execute cùng một statement nhiều lần trong cùng request (ví dụ insert hàng loạt, mục 6.4).

**Quy tắc của placeholder** (theo manual `PDO::prepare` và thử với MySQL 8.4):

- Dùng `?` hoặc `:ten`, **không trộn** hai kiểu trong một câu. Trộn thì ném lỗi `SQLSTATE[HY093]:
  Invalid parameter number: mixed named and positional parameters`.
- Số giá trị truyền vào phải khớp số placeholder, thừa hay thiếu đều ném `HY093`.
- Khoá trong mảng truyền cho `execute()` có hay không có dấu `:` đều được: `['email' => ...]` hay
  `[':email' => ...]`.
- Một tên placeholder chỉ được dùng **một lần** trong câu, trừ khi bật emulated prepare (mục 3.5).
  Cần cùng giá trị hai chỗ thì đặt hai tên: `:min1`, `:min2`.
- ⚠️ **Placeholder chỉ thay được một giá trị trọn vẹn** (*data literal*). Không thay được tên bảng, tên
  cột, từ khoá (`ASC`/`DESC`), hay một phần của chuỗi.

Ba trường hợp hay vướng nhất:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

// 1) LIKE: placeholder là cả chuỗi mẫu, ký tự % ghép ở phía PHP
$tuKhoa = 'An';
$stmt = $pdo->prepare('SELECT title FROM posts WHERE title LIKE ?');   // KHÔNG viết LIKE '%?%'
$stmt->execute(['%' . $tuKhoa . '%']);
echo implode(' | ', $stmt->fetchAll(PDO::FETCH_COLUMN)), "\n";   // in ra: Bài 1 của An | Bài 2 của An

// 2) IN (...) với danh sách động: sinh đúng số dấu ?
$ids = [1, 3];
$cho = implode(', ', array_fill(0, count($ids), '?'));             // "?, ?"
$stmt = $pdo->prepare("SELECT name FROM users WHERE id IN ($cho) ORDER BY id");
$stmt->execute($ids);
echo implode(' | ', $stmt->fetchAll(PDO::FETCH_COLUMN)), "\n";   // in ra: An | Chi

// 3) Tên cột / chiều sắp xếp từ người dùng: so với danh sách cho phép (whitelist)
$cotChoPhep = ['name' => 'name', 'balance' => 'balance'];
$sapXep     = $_GET['sort'] ?? 'balance';                           // giả sử người dùng gửi lên
$chieu      = ($_GET['dir'] ?? 'desc') === 'asc' ? 'ASC' : 'DESC';
$cot        = $cotChoPhep[$sapXep] ?? 'id';                        // không có trong danh sách thì dùng mặc định
$stmt = $pdo->query("SELECT name FROM users ORDER BY $cot $chieu");  // an toàn: $cot, $chieu chỉ là hằng của ta
echo implode(' | ', $stmt->fetchAll(PDO::FETCH_COLUMN)), "\n";   // in ra: An | Chi | Bình
```

⚠️ Danh sách rỗng ở trường hợp 2 sinh ra `IN ()`, là lỗi cú pháp. Kiểm tra `$ids === []` trước và trả
về kết quả rỗng luôn. Ở trường hợp 3, chuỗi từ người dùng **không bao giờ** đi vào SQL; nó chỉ được
dùng làm khoá để tra trong mảng của bạn.

⚠️ Với `LIKE`, ký tự `%` và `_` do người dùng gõ vẫn mang nghĩa đại diện (gõ `%` khớp mọi thứ). Đây
không phải injection (không thoát khỏi chuỗi được) nhưng có thể làm tìm kiếm sai hoặc chậm. Cần tìm
chính xác ký tự đó thì escape chúng trong giá trị và dùng mệnh đề `ESCAPE`.

**Đếm số dòng bị ảnh hưởng.** Sau `execute()` một câu `INSERT`/`UPDATE`/`DELETE`, `$stmt->rowCount()`
trả về số dòng bị ảnh hưởng (với `exec()` thì đó chính là giá trị trả về). Với MySQL, mặc định "bị ảnh
hưởng" nghĩa là **thực sự bị thay đổi**: `UPDATE users SET name = 'An' WHERE id = 1` khi tên đã là
`'An'` trả về `0` dù có một dòng khớp điều kiện. Bật `Pdo\Mysql::ATTR_FOUND_ROWS => true` trong
constructor thì MySQL đếm số dòng khớp (thử với MySQL 8.4: cùng câu đó trả về `1`). Đừng dùng
`rowCount() === 0` để kết luận "không tìm thấy bản ghi" khi chưa biết đang ở chế độ nào.

### 3.4 Bind tham số và kiểu dữ liệu

Có ba cách đưa giá trị vào placeholder:

```php
// Cách 1: mảng truyền cho execute(). Gọn, dùng nhiều nhất.
$stmt->execute(['email' => $email]);

// Cách 2: bindValue(): gắn một GIÁ TRỊ, có thể chỉ rõ kiểu
$stmt->bindValue(':email', $email, PDO::PARAM_STR);
$stmt->bindValue(1, 10, PDO::PARAM_INT);           // với dấu ?, vị trí đếm từ 1
$stmt->execute();

// Cách 3: bindParam(): gắn một BIẾN (tham chiếu), giá trị được đọc lúc execute()
$stmt->bindParam(':email', $email, PDO::PARAM_STR);
$email = 'an@example.com';                         // đổi biến sau khi bind vẫn có tác dụng
$stmt->execute();
```

Các hằng kiểu (`PDO::PARAM_*`) hay dùng:

| Hằng | Nghĩa |
|---|---|
| `PDO::PARAM_STR` | Chuỗi (mặc định của `bindValue`/`bindParam`) |
| `PDO::PARAM_INT` | Số nguyên |
| `PDO::PARAM_BOOL` | Boolean |
| `PDO::PARAM_NULL` | SQL `NULL` |
| `PDO::PARAM_LOB` | Dữ liệu lớn (*large object*), có thể truyền một stream (`fopen(...)`) |

⚠️ **`execute([...])` coi mọi giá trị là `PDO::PARAM_STR`** (manual ghi rõ), riêng `null` vẫn thành SQL
`NULL`. Phần lớn trường hợp không sao vì MySQL tự chuyển chuỗi `'42'` thành số khi so với cột số.
Nhưng có hai chỗ vỡ thật (thử với MySQL 8.4):

1. **Boolean**: `false` bị chuyển thành chuỗi rỗng `''` (cách PHP đổi `false` sang string), `true`
   thành `'1'`. Insert `false` vào cột `TINYINT(1) NOT NULL` với `sql_mode` strict (mặc định của MySQL
   8.4) ném lỗi:
   ```
   SQLSTATE[HY000]: General error: 1366 Incorrect integer value: '' for column 'is_active' at row 1
   ```
   Sửa: `bindValue(1, $active, PDO::PARAM_BOOL)`, hoặc truyền `(int) $active`.
2. **`LIMIT ?` khi bật emulated prepare**: mục 3.5.

⚠️ **Bẫy `bindParam` trong vòng lặp.** `bindParam` gắn **biến**, không gắn giá trị. Gắn trong vòng lặp
`foreach` rồi execute sau vòng lặp thì mọi placeholder nhận giá trị cuối cùng của biến:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

$stmt = $pdo->prepare('SELECT COUNT(*) FROM users WHERE name = :a OR name = :b');
$giaTri = [':a' => 'An', ':b' => 'Bình'];
foreach ($giaTri as $ten => $v) {
    $stmt->bindParam($ten, $v);       // cả :a và :b cùng trỏ vào MỘT biến $v
}
$stmt->execute();                     // lúc này $v === 'Bình' → câu thành name = 'Bình' OR name = 'Bình'
echo $stmt->fetchColumn(), "\n";      // in ra: 1   (mong đợi 2)

foreach ($giaTri as $ten => $v) {
    $stmt->bindValue($ten, $v);       // bindValue chép giá trị ngay lúc gọi
}
$stmt->execute();
echo $stmt->fetchColumn(), "\n";      // in ra: 2
```

Lời khuyên: dùng `execute([...])` cho phần lớn trường hợp, `bindValue` khi cần chỉ rõ kiểu, và chỉ
dùng `bindParam` khi thật sự muốn gắn biến (ví dụ tham số OUT của stored procedure, hoặc execute lặp
lại với biến đổi giá trị như ví dụ trong manual).

### 3.5 Native prepare và emulated prepare

Mục 3.3 nói "server phân tích câu lệnh trước, giá trị gửi sau". Điều đó đúng với *native prepare*
(prepare thật). Nhưng **PDO_MYSQL mặc định dùng emulated prepare** (manual: "PDO_MYSQL uses emulated
prepares by default"), tức là PDO **giả lập** prepared statement ở phía PHP:

```
Native prepare (EMULATE_PREPARES = false)        Emulated prepare (EMULATE_PREPARES = true, mặc định PDO_MYSQL)

prepare():  gửi "SELECT ... WHERE email = ?"     prepare():  chưa gửi gì, PDO chỉ ghi nhớ câu lệnh
            server phân tích, trả về id          execute():  PDO tự escape giá trị theo charset của
execute():  gửi id + giá trị (dạng nhị phân)                 kết nối, thay vào chỗ ?, được câu hoàn chỉnh
            server chạy, trả kết quả                         "SELECT ... WHERE email = 'an@example.com'"
                                                             gửi đi như một query thường
```

So sánh (các dòng "thử với MySQL 8.4" là kết quả chạy thật trên PHP 8.5):

| | Native | Emulated |
|---|---|---|
| Số lượt đi về cho một câu chạy một lần | Ít nhất 2 (prepare, execute) | 1 |
| Giá trị có bao giờ nằm trong văn bản SQL? | Không | Có, sau khi escape |
| Lỗi cú pháp phát hiện ở | `prepare()` | `execute()` (lúc `prepare()` chưa gửi gì lên server) |
| Dùng lại một tên placeholder hai lần | Lỗi `HY093` (thử với MySQL 8.4) | Được |
| `LIMIT ?` với `execute([10])` | Chạy đúng | Lỗi cú pháp 1064 (thử với MySQL 8.4) |
| Mặc định của | Laravel (đặt `false`, mục 2.5) | PDO_MYSQL thuần |

Emulated prepare **vẫn chống được SQL injection** trong điều kiện bình thường: giá trị được escape đúng
theo charset của kết nối, nên dấu nháy trong dữ liệu không đóng được chuỗi. Rủi ro nằm ở chỗ điều kiện
"bình thường" phải giữ được: charset mà client biết phải trùng charset server dùng (mục 2.3). Native
prepare không phụ thuộc điều kiện đó vì giá trị không bao giờ đi vào văn bản SQL.

⚠️ **Bẫy `LIMIT ?` với emulated prepare.** Vì `execute([...])` coi mọi giá trị là chuỗi, emulated
prepare ghép thành `LIMIT '2'`, và MySQL không chấp nhận chuỗi sau `LIMIT`:

```php
<?php
declare(strict_types=1);

// Cần MySQL (cách B, mục 1.4). Kết nối KHÔNG tắt emulated prepare, tức mặc định của PDO_MYSQL.
$pdo = new PDO('mysql:host=my84;dbname=ch16;charset=utf8mb4', 'app', 'app-secret');

$stmt = $pdo->prepare('SELECT id FROM users ORDER BY id LIMIT ?');
try {
    $stmt->execute([2]);
} catch (PDOException $e) {
    echo $e->getMessage(), "\n";
    // in ra: SQLSTATE[42000]: Syntax error or access violation: 1064 You have an error in your SQL
    // syntax; check the manual that corresponds to your MySQL server version for the right syntax
    // to use near ''2'' at line 1
}

$stmt->bindValue(1, 2, PDO::PARAM_INT);   // chỉ rõ kiểu: PDO ghép thành LIMIT 2
$stmt->execute();
echo implode(', ', $stmt->fetchAll(PDO::FETCH_COLUMN)), "\n";   // in ra: 1, 2
```

Với `EMULATE_PREPARES => false`, `execute([2])` (và cả `execute(['2'])`) chạy đúng.

Khuyến nghị: tắt emulated prepare (`PDO::ATTR_EMULATE_PREPARES => false`) như Laravel. Lỗi cú pháp lộ
sớm, không phụ thuộc vào việc escape phía client, không vướng `LIMIT ?`. Cái giá là thêm một lượt đi
về cho mỗi câu, thường không đáng kể so với thời gian chạy query. Manual cũng lưu ý: khi tắt emulate mà
driver không prepare được một câu nào đó, PDO tự quay về emulate cho câu đó.

`PDO::quote()` là hàm escape mà emulated prepare dùng bên trong: nó trả về chuỗi đã escape **kèm dấu
nháy** (`$pdo->quote("O'Reilly")` cho `'O\'Reilly'` với MySQL). Gần như không có lý do để tự gọi nó khi
đã có prepared statement; gặp code dùng `quote()` để ghép SQL thì nên chuyển sang placeholder.

## 4. Đọc kết quả: fetch và fetch mode

### 4.1 Lấy từng dòng, lấy tất cả, lấy một giá trị

Sau khi chạy một câu `SELECT`, kết quả nằm trong `PDOStatement`. Bốn cách đọc:

| Cách | Trả về | Khi hết dòng / không có dòng |
|---|---|---|
| `$stmt->fetch()` | Dòng **tiếp theo** | `false` |
| `$stmt->fetchAll()` | Mảng **mọi dòng còn lại** | `[]` |
| `$stmt->fetchColumn(int $cot = 0)` | Giá trị một cột của dòng tiếp theo | `false` |
| `foreach ($stmt as $row)` | Duyệt từng dòng (`PDOStatement` implement `IteratorAggregate` từ PHP 8.0) | Vòng lặp không chạy |

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

$stmt = $pdo->prepare('SELECT name FROM users WHERE id = ?');
$stmt->execute([999]);
var_dump($stmt->fetch());          // in ra: bool(false)   (không có dòng nào)

$stmt = $pdo->query('SELECT id, name FROM users ORDER BY id');
foreach ($stmt as $i => $row) {
    echo $i, ':', $row['name'], ' ';
}
echo "\n";                         // in ra: 0:An 1:Bình 2:Chi

$soUser = $pdo->query('SELECT COUNT(*) FROM users')->fetchColumn();
var_dump($soUser);                 // in ra: int(3)
```

⚠️ `fetch()` trả `false` khi không có dòng, nên kiểu trả về thực tế là `array|false`. Luôn kiểm tra
trước khi dùng:

```php
$row = $stmt->fetch();
if ($row === false) {
    // không tìm thấy: trả 404, ném exception nghiệp vụ...
}
```

`fetchColumn()` cũng trả `false` khi không có dòng, dễ nhầm với giá trị `false` thật. Với
`SELECT COUNT(*)` thì không sao (luôn có đúng một dòng); với `SELECT email FROM users WHERE id = ?` thì
phải kiểm tra `=== false`.

**`fetch()` trong vòng lặp hay `fetchAll()`?** `fetchAll()` tạo một mảng PHP chứa mọi dòng, tiện khi kết
quả nhỏ (một trang danh sách). Với kết quả lớn, duyệt bằng `foreach`/`fetch()` để không phải giữ cùng
lúc hai bản dữ liệu (bộ đệm của mysqlnd và mảng PHP). Nhưng nhớ rằng với buffered query (mặc định),
mysqlnd đã kéo toàn bộ kết quả vào bộ nhớ trước khi bạn fetch dòng đầu; muốn thật sự tiết kiệm bộ nhớ
xem mục 9.

### 4.2 Fetch mode: mỗi dòng có hình dạng gì

*Fetch mode* quyết định một dòng được trả về dưới dạng gì. Truyền vào `fetch($mode)`/`fetchAll($mode)`,
hoặc đặt mặc định cho cả kết nối bằng `PDO::ATTR_DEFAULT_FETCH_MODE`, hoặc cho một statement bằng
`$stmt->setFetchMode(...)`.

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();
$sql = 'SELECT id, name FROM users ORDER BY id';

echo json_encode($pdo->query($sql)->fetch(PDO::FETCH_BOTH), JSON_UNESCAPED_UNICODE), "\n";
// in ra: {"id":1,"0":1,"name":"An","1":"An"}    ← mỗi giá trị xuất hiện HAI lần
echo json_encode($pdo->query($sql)->fetch(PDO::FETCH_NUM), JSON_UNESCAPED_UNICODE), "\n";
// in ra: [1,"An"]
echo json_encode($pdo->query($sql)->fetch(PDO::FETCH_ASSOC), JSON_UNESCAPED_UNICODE), "\n";
// in ra: {"id":1,"name":"An"}
$obj = $pdo->query($sql)->fetch(PDO::FETCH_OBJ);
echo $obj::class, ' ', $obj->name, "\n";
// in ra: stdClass An
```

| Mode | Một dòng là | Ghi chú |
|---|---|---|
| `FETCH_BOTH` | Mảng có cả khoá tên cột lẫn khoá số | **Mặc định** nếu không đặt gì. Mỗi dòng có gấp đôi số phần tử nên tốn thêm bộ nhớ, `json_encode` ra dữ liệu thừa. Nên đổi |
| `FETCH_ASSOC` | `['id' => 1, 'name' => 'An']` | Lựa chọn phổ biến nhất |
| `FETCH_NUM` | `[1, 'An']` | Dùng với `list()`/destructuring: `[$id, $name] = $row` |
| `FETCH_OBJ` | `stdClass` với property là tên cột | Laravel query builder dùng mode này |
| `FETCH_COLUMN` | Chỉ giá trị một cột | Dùng với `fetchAll`: danh sách id, danh sách email |
| `FETCH_CLASS` | Object của class bạn chỉ định | Mục 4.3 |

⚠️ Hai cột trùng tên (thường gặp khi `JOIN`: `users.id` và `posts.id`) thì với `FETCH_ASSOC` cột sau
**ghi đè** cột trước trong mảng. Đặt alias trong SQL: `SELECT u.id AS user_id, p.id AS post_id ...`.

Vài mode "biến hình" dữ liệu ngay khi `fetchAll`, rất tiện để khỏi viết vòng lặp gom nhóm bằng tay:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

// Cột 1 làm khoá, cột 2 làm giá trị. Câu SELECT phải có đúng 2 cột.
$tenTheoId = $pdo->query('SELECT id, name FROM users ORDER BY id')->fetchAll(PDO::FETCH_KEY_PAIR);
echo json_encode($tenTheoId, JSON_UNESCAPED_UNICODE), "\n";
// in ra: {"1":"An","2":"Bình","3":"Chi"}

// Cột 1 làm khoá, các cột còn lại làm giá trị (mỗi khoá một dòng)
$userTheoId = $pdo->query('SELECT id, name, balance FROM users ORDER BY id')->fetchAll(PDO::FETCH_UNIQUE);
echo json_encode($userTheoId, JSON_UNESCAPED_UNICODE), "\n";
// in ra: {"1":{"name":"An","balance":150000},"2":{"name":"Bình","balance":0},"3":{"name":"Chi","balance":9999}}

// Gom nhóm theo cột 1: mỗi khoá là một DANH SÁCH
$baiTheoUser = $pdo->query('SELECT user_id, title FROM posts ORDER BY id')
    ->fetchAll(PDO::FETCH_GROUP | PDO::FETCH_COLUMN);
echo json_encode($baiTheoUser, JSON_UNESCAPED_UNICODE), "\n";
// in ra: {"1":["Bài 1 của An","Bài 2 của An"],"2":["Bài của Bình"],"3":["Bài của Chi"]}
```

⚠️ Với `FETCH_KEY_PAIR` và `FETCH_UNIQUE`, khoá trùng thì dòng sau ghi đè dòng trước, không có cảnh báo.
Chạy `SELECT user_id, title FROM posts` với `FETCH_KEY_PAIR` chỉ còn một bài cho user 1. Khi khoá có thể
trùng, dùng `FETCH_GROUP`.

### 4.3 Đổ dữ liệu vào object của bạn

Mảng `['id' => 1, 'name' => 'An']` dễ dùng nhưng không có kiểu: gõ sai tên khoá chỉ nhận về warning
lúc chạy. Code lớn thường chuyển mỗi dòng thành một object có kiểu rõ ràng (*DTO*, *data transfer
object*). Có hai cách.

**Cách 1: `FETCH_CLASS`.** PDO tự tạo object và gán từng cột vào property cùng tên:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

final class User
{
    public readonly int $id;
    public readonly string $name;
    private int $balance;

    public function balance(): int
    {
        return $this->balance;
    }
}

$stmt = $pdo->query('SELECT id, name, balance FROM users ORDER BY id');
$users = $stmt->fetchAll(PDO::FETCH_CLASS, User::class);
echo $users[0]->name, ' ', $users[0]->balance(), "\n";    // in ra: An 150000
```

Cách hoạt động, theo manual và thử trên PHP 8.5:

- PDO gán property **trước khi gọi constructor**, bất kể visibility hay `readonly` (miễn constructor
  không tự khởi tạo chúng). Muốn constructor chạy trước thì thêm cờ:
  `PDO::FETCH_CLASS | PDO::FETCH_PROPS_LATE`.
- Giá trị cột **không** được truyền vào constructor dưới dạng tham số. Class có constructor bắt buộc
  tham số (như constructor promotion) không hợp với cách này.
- Cột không có property tương ứng thì PDO tạo *dynamic property*, và từ PHP 8.2 việc đó phát
  `Deprecated: Creation of dynamic property User::$email is deprecated`
  ([chương 09](09-oop-co-ban.md)). Chỉ `SELECT` đúng các cột class có.
- ⚠️ Việc gán kiểu ở đây **luôn theo chế độ ép kiểu lỏng** (coercive), kể cả khi file của bạn có
  `declare(strict_types=1)`: cột chứa `'42'` gán vào property `int` thành `42` không báo gì; cột chứa
  `'abc'` thì ném `TypeError: Cannot assign string to property User::$id of type int`. Nguy hiểm nhất:
  `DECIMAL` của MySQL (string, mục 5.2) gán vào property `float` sẽ âm thầm thành `float` và mất độ
  chính xác.

**Cách 2: tự map bằng một named constructor.** Dài hơn vài dòng nhưng tường minh, chạy qua đúng
constructor của bạn, và `strict_types` được tôn trọng:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

final readonly class UserDto
{
    public function __construct(
        public int $id,
        public string $name,
        public int $balance,
    ) {}

    /** @param array{id: int, name: string, balance: int} $row */
    public static function fromRow(array $row): self
    {
        return new self(id: $row['id'], name: $row['name'], balance: $row['balance']);
    }
}

$rows  = $pdo->query('SELECT id, name, balance FROM users ORDER BY id')->fetchAll();
$users = array_map(UserDto::fromRow(...), $rows);
echo $users[1]->name, ' ', $users[1]->balance, "\n";      // in ra: Bình 0
```

Đây chính là ý tưởng mà các ORM làm giúp bạn ở quy mô lớn (mục 12).

## 5. Kiểu dữ liệu PHP nhận về từ MySQL

### 5.1 Từ PHP 8.1: số nguyên và số thực là kiểu native

Database có hệ thống kiểu riêng (`INT`, `DECIMAL`, `DATETIME`...), PHP có hệ thống kiểu riêng (`int`,
`float`, `string`...). Driver phải chuyển giữa hai hệ. Với PDO_MYSQL trên PHP hiện đại (thử với PHP 8.5
và MySQL 8.4, cả native lẫn emulated prepare cho cùng kết quả):

| Kiểu MySQL | Kiểu PHP nhận được | Ví dụ |
|---|---|---|
| `TINYINT`, `INT`, `BIGINT` (kể cả `UNSIGNED` khi còn trong giới hạn `int` của PHP) | `int` | `int(42)` |
| `BIGINT UNSIGNED` vượt `PHP_INT_MAX` | `string` | `"18446744073709551615"` |
| `TINYINT(1)` (hay dùng làm boolean) | `int` | `int(1)`, **không phải** `true` |
| `FLOAT`, `DOUBLE` | `float` | `float(0.1)` |
| `DECIMAL`/`NUMERIC` | `string` | `"1500.50"` |
| `SUM()`, `AVG()` trên cột `DECIMAL` | `string` | `"1600.49"` |
| `DATETIME`, `DATE`, `TIMESTAMP` | `string` | `"2026-10-03 09:30:00"` |
| `JSON` | `string` | `'{"a": 1}'` |
| `CHAR`, `VARCHAR`, `TEXT` | `string` | `"An"` |
| `NULL` (mọi kiểu) | `null` | `NULL` |

Trước PHP 8.1 thì khác: **emulated prepare** (mặc định của PDO_MYSQL) trả **mọi thứ thành string**
(`"42"`, `"0.1"`), chỉ native prepare mới trả `int`/`float`. PHP 8.1 đổi emulated prepare cho giống
native (UPGRADING 8.1: "Integers and floats in result sets will now be returned using native PHP types
instead of strings when using emulated prepared statements"). PDO_SQLITE cũng đổi tương tự ở 8.1. Cùng
một câu `SELECT id FROM users` với kết nối PDO_MYSQL mặc định:

```
PHP 8.0:  ["id"]=> string(1) "1"
PHP 8.1+: ["id"]=> int(1)
```

⚠️ Hệ quả khi nâng cấp project cũ lên 8.1+: code so sánh chặt kiểu viết cho thời "mọi thứ là string"
bị vỡ âm thầm, ví dụ `if ($row['status'] === '1')` giờ luôn `false` vì `$row['status']` là `int(1)`.
Muốn giữ hành vi cũ trong lúc sửa dần: `PDO::ATTR_STRINGIFY_FETCHES => true` (ép mọi giá trị trừ
`null` thành string).

⚠️ `TINYINT(1)` về PHP là `int`, không phải `bool`: `$row['is_active'] === true` luôn `false`. So với
`1`, hoặc ép `(bool) $row['is_active']` ở chỗ map sang object.

### 5.2 Vì sao `DECIMAL` là string, và tính tiền thế nào

`DECIMAL(12,2)` lưu số thập phân **chính xác**: `1500.50` là đúng `1500.50`. PHP không có kiểu số thập
phân chính xác dựng sẵn; `float` là số thực nhị phân (IEEE 754) nên nhiều số thập phân không biểu diễn
chính xác được ([chương 04](04-kieu-du-lieu.md)):

```php
var_dump(0.1 + 0.2);                 // in ra: float(0.30000000000000004)
var_dump(0.1 + 0.2 === 0.3);         // in ra: bool(false)
```

Nếu driver đổi `DECIMAL` sang `float`, bạn mất độ chính xác ngay lúc đọc mà không hề biết. Trả về
string là cách duy nhất giữ nguyên giá trị; việc chọn kiểu tính toán là của bạn. Ngay cả MySQL cũng
coi `0.1 + 0.2` (hai literal thập phân) là `DECIMAL`: `SELECT 0.1 + 0.2` qua PDO trả về `"0.3"`, còn
`CAST(0.1 AS DOUBLE) + CAST(0.2 AS DOUBLE)` trả về `float(0.30000000000000004)`.

Ba cách xử lý tiền trong PHP:

1. **Giữ string, tính bằng extension `bcmath`** (cần bật extension; image Docker ở mục 1.4 cách B đã có).
   ⚠️ Các hàm `bc*` **cắt bỏ** phần thừa theo `scale`, không làm tròn: `bcmul('1.005', '1', 2)` cho
   `'1.00'`. Cần làm tròn thì dùng `bcround()` (có từ PHP 8.4).
2. **`BcMath\Number` (PHP 8.4+)**: object bất biến bọc bcmath, dùng được toán tử `+ - * /` và so sánh.
3. **Lưu số nguyên theo đơn vị nhỏ nhất** (đồng, cent) trong cột `BIGINT`, như `db-sqlite.php` đang làm.
   Đơn giản và nhanh, nhưng phải thống nhất đơn vị ở mọi nơi.

```php
<?php
declare(strict_types=1);

// Cần extension bcmath. Giá trị như đọc từ cột DECIMAL(12,2).
$balance = '1500.50';
$phi     = '0.10';

echo bcmul($balance, $phi, 2), "\n";                         // in ra: 150.05
echo bcadd($balance, bcmul($balance, $phi, 2), 2), "\n";     // in ra: 1650.55

// PHP 8.4+: BcMath\Number dùng toán tử
$n    = new BcMath\Number($balance);
$tong = $n + $n * new BcMath\Number($phi);
echo $tong, "\n";                                            // in ra: 1650.5500
echo $tong->round(2), "\n";                                  // in ra: 1650.55
var_dump(new BcMath\Number('0.1') + new BcMath\Number('0.2') == new BcMath\Number('0.3'));
// in ra: bool(true)
```

Khi ghi ngược vào DB, truyền string (`'1650.55'`) cho placeholder; MySQL chuyển chuỗi sang `DECIMAL`
chính xác. Đừng truyền `float`. Thiết kế cột tiền ở phía database xem
[giáo trình Database, chương 03](../database/03-kieu-du-lieu.md); Laravel có cast `decimal:2` (cũng trả
string), xem [chương 27](27-laravel-database-eloquent.md).

### 5.3 Thời gian, JSON và các kiểu khác

- **`DATETIME`/`TIMESTAMP`** về dạng chuỗi `'Y-m-d H:i:s'`. Chuyển thành object bằng
  `DateTimeImmutable::createFromFormat('Y-m-d H:i:s', $row['created_at'], new DateTimeZone('UTC'))`,
  và **luôn chỉ rõ múi giờ** mà chuỗi đó được hiểu. Cột `DATETIME` không lưu múi giờ; cột `TIMESTAMP`
  được MySQL đổi theo biến `time_zone` của session. Vì vậy hàm ở mục 2.5 đặt `time_zone = '+00:00'`
  cho mọi kết nối. Chi tiết về thời gian trong PHP: [chương 14](14-file-json-thoi-gian.md).
- **`JSON`** về dạng chuỗi JSON; tự giải mã: `json_decode($row['meta'], true, flags: JSON_THROW_ON_ERROR)`.
  Khi ghi, `json_encode(..., JSON_THROW_ON_ERROR)` rồi truyền chuỗi cho placeholder.
- **`BLOB`** về dạng string (chuỗi byte). Dữ liệu lớn có thể đọc dạng stream bằng `bindColumn()` với
  `PDO::PARAM_LOB`, nhưng thường người ta không lưu file lớn trong database.
- **Ghi giá trị vào DB**: theo chiều ngược lại, nhớ mục 3.4: `execute([...])` gửi mọi thứ dưới dạng
  string (trừ `null`); dùng `bindValue` với `PARAM_INT`/`PARAM_BOOL` khi kiểu quan trọng.

## 6. Transaction

### 6.1 Autocommit và transaction

*Transaction* là một nhóm câu lệnh được database xử lý như **một khối**: hoặc tất cả có hiệu lực
(*commit*), hoặc không câu nào có hiệu lực (*rollback*). Ví dụ kinh điển là chuyển tiền: trừ tiền
người gửi và cộng tiền người nhận phải cùng thành công hoặc cùng không xảy ra. Lý thuyết đầy đủ (ACID,
isolation level, lock) nằm ở giáo trình Database: [chương 13](../database/13-transaction-acid.md),
[chương 14](../database/14-isolation-mvcc.md), [chương 15](../database/15-lock-deadlock.md). Mục này chỉ
nói cách điều khiển transaction từ PHP.

Mặc định, kết nối ở chế độ *autocommit*: **mỗi câu lệnh tự là một transaction** và được commit ngay khi
chạy xong. Hai câu `UPDATE` liên tiếp trong chế độ này là hai transaction riêng; nếu script chết giữa
hai câu, câu thứ nhất đã nằm vĩnh viễn trong database.

### 6.2 `beginTransaction`, `commit`, `rollBack`

| Method | Việc làm |
|---|---|
| `$pdo->beginTransaction()` | Tắt autocommit, bắt đầu transaction |
| `$pdo->commit()` | Ghi nhận mọi thay đổi từ lúc begin, quay lại autocommit |
| `$pdo->rollBack()` | Huỷ mọi thay đổi từ lúc begin, quay lại autocommit |
| `$pdo->inTransaction()` | Đang trong transaction hay không |

Khuôn mẫu chuẩn: begin, làm việc, commit; **bất kỳ lỗi gì** (kể cả lỗi không phải của database) thì
rollback rồi ném tiếp:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

final class KhongDuTien extends RuntimeException {}

function chuyenTien(PDO $pdo, int $tu, int $den, int $soTien): void
{
    $pdo->beginTransaction();
    try {
        // Trừ tiền chỉ khi đủ số dư: điều kiện nằm ngay trong câu UPDATE
        $tru = $pdo->prepare('UPDATE users SET balance = balance - ? WHERE id = ? AND balance >= ?');
        $tru->execute([$soTien, $tu, $soTien]);
        if ($tru->rowCount() !== 1) {
            throw new KhongDuTien("User $tu không đủ $soTien");
        }
        $pdo->prepare('UPDATE users SET balance = balance + ? WHERE id = ?')->execute([$soTien, $den]);
        $pdo->commit();
    } catch (Throwable $e) {
        if ($pdo->inTransaction()) {     // có thể transaction đã kết thúc (xem 6.3)
            $pdo->rollBack();
        }
        throw $e;                        // không nuốt lỗi: người gọi quyết định làm gì
    }
}

function inSoDu(PDO $pdo): void
{
    $soDu = $pdo->query('SELECT name, balance FROM users ORDER BY id')->fetchAll(PDO::FETCH_KEY_PAIR);
    echo json_encode($soDu, JSON_UNESCAPED_UNICODE), "\n";
}

chuyenTien($pdo, 1, 2, 50000);
inSoDu($pdo);                       // in ra: {"An":100000,"Bình":50000,"Chi":9999}

try {
    chuyenTien($pdo, 3, 1, 1000000);
} catch (KhongDuTien $e) {
    echo $e->getMessage(), "\n";    // in ra: User 3 không đủ 1000000
}
inSoDu($pdo);                       // in ra: {"An":100000,"Bình":50000,"Chi":9999}   (không đổi)
var_dump($pdo->inTransaction());    // in ra: bool(false)
```

Vì sao bắt `Throwable` chứ không chỉ `PDOException`: lỗi có thể đến từ code PHP xen giữa các câu SQL
(`TypeError`, exception nghiệp vụ như `KhongDuTien`). Mọi lỗi đều phải dẫn tới rollback
([chương 12](12-loi-exception.md) nói về `Throwable`). Câu `UPDATE ... WHERE balance >= ?` kiểm tra và
trừ trong **một** câu lệnh, tránh kiểu "đọc số dư bằng SELECT, so sánh trong PHP, rồi UPDATE", vốn có
thể sai khi hai request chạy đồng thời (giáo trình Database, chương 14 và 15 giải thích lost update).

Nếu script kết thúc (kể cả chết vì lỗi) khi transaction đang mở, PDO **tự rollback** khi đóng kết nối,
với điều kiện transaction được mở bằng `beginTransaction()`. Mở bằng câu SQL `START TRANSACTION` thì
manual cảnh báo PDO không biết để tự rollback. Với persistent connection, connection không đóng khi
script kết thúc; PDO vẫn rollback transaction còn mở lúc huỷ object `PDO`, nhưng các trạng thái khác
của session thì ở lại cho request sau (mục 10.2).

### 6.3 Những cạm bẫy của transaction trong PDO

**DDL tự commit (MySQL).** Trong MySQL, các câu định nghĩa cấu trúc như `CREATE TABLE`, `ALTER TABLE`,
`DROP TABLE`, `TRUNCATE TABLE`, `CREATE INDEX`, `RENAME TABLE` gây *implicit commit*: MySQL commit
transaction đang mở **trước** khi chạy chúng (danh sách đầy đủ trong MySQL manual, mục "Statements That
Cause an Implicit Commit"). Thay đổi trước đó không rollback được nữa. Từ PHP 8.0, PDO_MYSQL hỏi trạng
thái thật từ server, nên sau implicit commit `inTransaction()` trả `false` và `commit()` ném lỗi (chạy
thử với MySQL 8.4, PHP 8.5):

| Bước | Lệnh | Kết quả |
|---|---|---|
| 1 | `beginTransaction()` | `true` |
| 2 | `exec('UPDATE ... SET balance = balance - 10 WHERE id = 1')` | `1` dòng |
| 3 | `exec('ALTER TABLE ... ADD COLUMN note VARCHAR(10) NULL')` | Implicit commit: bước 2 đã được commit |
| 4 | `inTransaction()` | `false` |
| 5 | `commit()` hoặc `rollBack()` | `PDOException: There is no active transaction` |
| 6 | Đọc lại số dư | Đã bị trừ 10, không lấy lại được |

Đây là lý do khuôn mẫu ở 6.2 kiểm tra `inTransaction()` trước khi `rollBack()`: nếu không, exception
"There is no active transaction" sẽ che mất lỗi gốc. Quy tắc: không đặt DDL trong transaction (migration
trong Laravel cũng chịu đúng giới hạn này với MySQL).

**Không lồng transaction.** Gọi `beginTransaction()` khi đang có transaction ném
`PDOException: There is already an active transaction`. PDO không hỗ trợ transaction lồng nhau. Cần
"transaction con" có thể huỷ riêng thì dùng *savepoint* bằng SQL:

```php
$pdo->beginTransaction();
$pdo->exec('SAVEPOINT sp1');
// ... việc có thể huỷ riêng ...
$pdo->exec('ROLLBACK TO SAVEPOINT sp1');   // chỉ huỷ phần sau sp1, transaction vẫn mở
$pdo->commit();
```

Laravel làm đúng như vậy: `DB::transaction()` lồng nhau thì lớp ngoài là transaction thật, các lớp
trong là savepoint tên `trans2`, `trans3`... ([chương 27](27-laravel-database-eloquent.md)).

**Lỗi một câu không có nghĩa là cả transaction đã bị huỷ.** Theo MySQL manual (InnoDB Error Handling),
lỗi trùng khoá (1062) chỉ rollback **câu lệnh** gây lỗi; transaction vẫn mở và các câu trước vẫn còn.
Deadlock thì ngược lại: InnoDB rollback **toàn bộ** transaction. Vì vậy đừng bắt `PDOException` giữa
transaction rồi "chạy tiếp như không có gì" khi chưa biết đó là lỗi gì; cách an toàn là rollback cả
khối như khuôn mẫu 6.2.

**Bảng không hỗ trợ transaction.** Manual PDO cảnh báo: với bảng MyISAM, `beginTransaction()` vẫn trả
`true` nhưng chẳng có gì được bảo vệ. InnoDB (mặc định của MySQL) thì hỗ trợ đầy đủ.

**Transaction dài.** Transaction giữ lock và giữ phiên bản cũ của dữ liệu tới khi kết thúc. Đừng gọi
API bên ngoài, gửi email, hay chờ người dùng bên trong transaction: API chậm 10 giây là lock bị giữ 10
giây. Làm phần chậm trước hoặc sau transaction (giáo trình Database, chương 13).

### 6.4 Insert hàng loạt trong một transaction

Chế độ autocommit commit sau **mỗi** câu, và với cấu hình mặc định, mỗi lần commit InnoDB phải đảm bảo
redo log đã xuống đĩa (giáo trình Database, chương 16). Chèn 10.000 dòng bằng 10.000 câu autocommit là
10.000 lần như vậy. Gói vào một transaction và dùng lại một prepared statement:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

$ds = [];
for ($i = 1; $i <= 1000; $i++) {
    $ds[] = [1, "Bài tự sinh $i"];
}

$pdo->beginTransaction();
try {
    $stmt = $pdo->prepare('INSERT INTO posts (user_id, title) VALUES (?, ?)');   // prepare MỘT lần
    foreach ($ds as $dong) {
        $stmt->execute($dong);                                                     // execute nhiều lần
    }
    $pdo->commit();
} catch (Throwable $e) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }
    throw $e;
}
echo $pdo->query('SELECT COUNT(*) FROM posts')->fetchColumn(), "\n";   // in ra: 1004
```

Nhanh hơn nữa là *multi-row INSERT*: một câu `INSERT ... VALUES (?, ?), (?, ?), ...` chèn nhiều dòng,
sinh placeholder như trường hợp `IN (...)` ở mục 3.3. Chia lô vừa phải (vài trăm tới vài nghìn dòng một
câu) vì câu lệnh không được vượt `max_allowed_packet` của MySQL, và transaction quá lớn giữ lock lâu.

### 6.5 Deadlock và chạy lại

Khi hai transaction chờ lock của nhau, InnoDB phát hiện *deadlock*, chọn một transaction làm "nạn
nhân" và rollback nó. Phía PHP nhận:

```
SQLSTATE[40001]: Serialization failure: 1213 Deadlock found when trying to get lock; try restarting transaction
```

MySQL manual nói rõ: deadlock là chuyện **bình thường** trên server bận, ứng dụng phải sẵn sàng **chạy
lại toàn bộ transaction**. Một lỗi gần giống là *lock wait timeout* (1205, SQLSTATE `HY000`, "Lock wait
timeout exceeded; try restarting transaction"): mặc định InnoDB chỉ rollback câu lệnh đang chờ, không
rollback cả transaction (trừ khi server bật `innodb_rollback_on_timeout`). Cách deadlock xảy ra và cách
giảm nó: [giáo trình Database, chương 15](../database/15-lock-deadlock.md).

Một hàm bọc transaction có chạy lại, cùng ý tưởng với `DB::transaction($callback, $attempts)` của
Laravel:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

/**
 * Chạy $viec trong một transaction. Gặp deadlock (MySQL 1213) thì chạy lại TOÀN BỘ transaction.
 *
 * @template T
 * @param callable(PDO): T $viec
 * @return T
 */
function trongTransaction(PDO $pdo, callable $viec, int $soLanThu = 3): mixed
{
    for ($lan = 1; ; $lan++) {
        $pdo->beginTransaction();
        try {
            $ketQua = $viec($pdo);
            $pdo->commit();
            return $ketQua;
        } catch (Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            $laDeadlock = $e instanceof PDOException && ($e->errorInfo[1] ?? null) === 1213;
            if (!$laDeadlock || $lan >= $soLanThu) {
                throw $e;
            }
            usleep(random_int(10_000, 50_000) * $lan);   // chờ một chút, tăng dần, có ngẫu nhiên
        }
    }
}

// Giả lập để chạy được trên SQLite: lần đầu ném lỗi giống hệt deadlock của MySQL, lần sau thành công
$soLanGoi = 0;
$id = trongTransaction($pdo, function (PDO $pdo) use (&$soLanGoi): string {
    $soLanGoi++;
    $pdo->prepare('INSERT INTO posts (user_id, title) VALUES (?, ?)')->execute([1, 'Bài mới']);
    $id = $pdo->lastInsertId();        // lấy ngay sau INSERT (mục 7)
    if ($soLanGoi === 1) {
        $e = new PDOException('SQLSTATE[40001]: Serialization failure: 1213 Deadlock found ...');
        $e->errorInfo = ['40001', 1213, 'Deadlock found when trying to get lock; try restarting transaction'];
        throw $e;
    }
    return $id;
});
echo "Số lần chạy: $soLanGoi, id mới: $id\n";   // in ra: Số lần chạy: 2, id mới: 5
echo $pdo->query("SELECT COUNT(*) FROM posts WHERE title = 'Bài mới'")->fetchColumn(), "\n";   // in ra: 1
```

Lần chạy đầu đã insert rồi bị rollback, nên cuối cùng chỉ còn **một** dòng. Hai điều kiện để chạy lại
an toàn:

1. `$viec` chỉ làm việc với database. Nếu bên trong có gửi email hay gọi API thanh toán, chạy lại là
   gửi hai lần. Tác dụng phụ bên ngoài đặt **sau** khi commit thành công.
2. Hàm phải được gọi khi **chưa** ở trong transaction. Chạy lại chỉ có nghĩa ở transaction ngoài cùng,
   vì deadlock đã huỷ toàn bộ transaction chứ không chỉ phần bên trong.

## 7. `lastInsertId`: lấy id vừa tạo

Bảng có cột `AUTO_INCREMENT` thì database tự sinh id khi insert. Lấy id đó bằng `$pdo->lastInsertId()`:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

$pdo->prepare('INSERT INTO users (email, name, password) VALUES (?, ?, ?)')
    ->execute(['dung@example.com', 'Dũng', 'x']);
$id = $pdo->lastInsertId();
var_dump($id);                      // in ra: string(1) "4"
$userId = (int) $id;                // cần int thì tự ép
```

Những điều cần biết (các dòng có ghi MySQL là thử với MySQL 8.4, PHP 8.5, native prepare):

- Trả về **string** (hoặc `false` khi driver không hỗ trợ), không phải `int`. Lý do: id có thể là
  `BIGINT UNSIGNED` vượt `PHP_INT_MAX`, hoặc không phải số với một số database.
- Giá trị gắn với **connection**, không phải toàn server. Hai request insert đồng thời, mỗi request
  nhận đúng id của mình. Không bao giờ dùng `SELECT MAX(id)` để "đoán" id vừa tạo.
- Insert nhiều dòng trong **một** câu (`INSERT ... VALUES (...), (...), (...)`): MySQL trả id của
  **dòng đầu tiên**, không phải dòng cuối.
- ⚠️ Với MySQL, gọi **ngay sau** câu `INSERT`. Chạy thêm câu khác trên cùng connection (kể cả một câu
  `SELECT` hay `UPDATE`) rồi mới gọi thì `lastInsertId()` trả về `"0"`, dù hàm SQL `LAST_INSERT_ID()`
  vẫn còn nhớ id cũ.
- Insert trong transaction rồi rollback: id đã cấp **không được trả lại**; lần insert sau nhận id kế
  tiếp, để lại một khoảng trống. Insert lỗi (trùng khoá) cũng có thể tiêu một id. Id tự tăng chỉ đảm bảo
  duy nhất, **không** đảm bảo liên tục (giáo trình Database, chương 04).
- PostgreSQL cần tên sequence (`lastInsertId('users_id_seq')`) và thường dùng `INSERT ... RETURNING id`
  thay thế. MySQL không có `RETURNING`.

## 8. Xử lý lỗi: `PDOException` và SQLSTATE

### 8.1 Ba error mode

| Mode | Khi câu SQL lỗi | Ghi chú |
|---|---|---|
| `ERRMODE_SILENT` | Method trả `false`, mã lỗi lưu lại, đọc bằng `errorCode()`/`errorInfo()` | Mặc định **trước** PHP 8.0. Quên kiểm tra `false` là lỗi trôi qua im lặng |
| `ERRMODE_WARNING` | Như trên, thêm một `E_WARNING` | Chỉ để debug |
| `ERRMODE_EXCEPTION` | Ném `PDOException` | **Mặc định từ PHP 8.0** (RFC `pdo_default_errmode`) |

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

// Hành vi của code viết cho PHP 7 (SILENT): lỗi biến thành giá trị false
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_SILENT);
$ketQua = $pdo->query('SELECT * FROM bang_khong_co');
var_dump($ketQua);                       // in ra: bool(false)
echo json_encode($pdo->errorInfo()), "\n";
// in ra: ["HY000",1,"no such table: bang_khong_co"]
// Code cũ hay viết tiếp $ketQua->fetchAll() và nhận lỗi "Call to a member function fetchAll() on bool",
// cách xa nguyên nhân thật.
```

Luôn dùng `ERRMODE_EXCEPTION`. Đặt rõ trong options dù đã là mặc định, vì thư viện cũ hoặc code của ai
đó có thể đã đổi nó trên cùng object PDO.

### 8.2 Bên trong một `PDOException`

Một lỗi SQL mang ba thông tin, đọc qua property `errorInfo` của exception:

```
$e->errorInfo = [
    0 => SQLSTATE   chuỗi 5 ký tự, chuẩn SQL, giống nhau giữa các database
    1 => mã lỗi của driver (với MySQL: mã lỗi của server, ví dụ 1062)
    2 => thông báo lỗi của driver
]
```

Ví dụ với MySQL 8.4, insert email đã tồn tại vào cột `UNIQUE`:

```
getMessage(): SQLSTATE[23000]: Integrity constraint violation: 1062 Duplicate entry 'an@example.com' for key 'users.email'
errorInfo:    ["23000", 1062, "Duplicate entry 'an@example.com' for key 'users.email'"]
getCode():    "23000"   (string)
```

⚠️ **`getCode()` không đáng tin để phân loại lỗi.** Với lỗi khi chạy câu lệnh, nó trả về SQLSTATE dạng
**string** (`"23000"`), khác mọi exception khác của PHP trả `int`. Với lỗi lúc kết nối, nó trả mã lỗi
MySQL dạng **int** (`1045`). Với lỗi do chính PDO sinh ra như "There is no active transaction", nó trả
`0`. Phân loại bằng `$e->errorInfo[1]` (mã cụ thể của MySQL) và `$e->errorInfo[0]` (SQLSTATE).

SQLSTATE quá thô để quyết định: `23000` gồm cả trùng khoá, vi phạm khoá ngoại, và `NULL` vào cột
`NOT NULL`. Mã MySQL hay cần xử lý riêng (theo MySQL 8.4 Error Reference):

| Mã MySQL | SQLSTATE | Nghĩa | Ứng dụng thường làm |
|---|---|---|---|
| 1062 | 23000 | Duplicate entry (trùng `UNIQUE`/khoá chính) | Báo "email đã được dùng" |
| 1451 | 23000 | Không xoá/sửa được dòng cha vì còn dòng con tham chiếu (khoá ngoại) | Báo "còn dữ liệu liên quan" |
| 1452 | 23000 | Thêm/sửa dòng con mà dòng cha không tồn tại (khoá ngoại) | Báo dữ liệu không hợp lệ |
| 1048 | 23000 | Cột không được `NULL` | Lỗi lập trình, sửa validate |
| 1366 | HY000 | Giá trị sai kiểu cho cột (mục 3.4) | Lỗi lập trình |
| 1213 | 40001 | Deadlock | Chạy lại transaction (6.5) |
| 1205 | HY000 | Lock wait timeout | Chạy lại câu lệnh hoặc transaction |
| 1146 / 1054 | 42S02 / 42S22 | Bảng / cột không tồn tại | Lỗi triển khai (quên chạy migration) |
| 1064 | 42000 | Lỗi cú pháp SQL | Lỗi lập trình |
| 1040 | 08004 | Too many connections | Xem mục 10 |

(Bảng ghi SQLSTATE theo MySQL. Lỗi lúc kết nối thì message của PDO thường mang `SQLSTATE[HY000]`, như các
ví dụ 1045, 1049 ở mục 2.2.)

### 8.3 Biến lỗi database thành lỗi nghiệp vụ

Chỉ bắt những lỗi bạn **biết cách xử lý**, đổi thành exception có nghĩa với nghiệp vụ, còn lại để bay
lên handler chung:

```php
<?php
declare(strict_types=1);

final class EmailDaTonTai extends RuntimeException {}

function taoUser(PDO $pdo, string $email, string $name): int
{
    try {
        $pdo->prepare('INSERT INTO users (email, name) VALUES (?, ?)')->execute([$email, $name]);
        return (int) $pdo->lastInsertId();
    } catch (PDOException $e) {
        if (($e->errorInfo[1] ?? null) === 1062) {                       // MySQL: trùng khoá UNIQUE
            throw new EmailDaTonTai("Email $email đã được dùng", previous: $e);
        }
        throw $e;                                                         // lỗi khác: không đoán, ném tiếp
    }
}

$pdo = new PDO('mysql:host=my84;dbname=ch16;charset=utf8mb4', 'app', 'app-secret', [
    PDO::ATTR_ERRMODE          => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_EMULATE_PREPARES => false,
]);
try {
    taoUser($pdo, 'an@example.com', 'An thứ hai');
} catch (EmailDaTonTai $e) {
    echo $e->getMessage(), "\n";     // in ra: Email an@example.com đã được dùng
}
```

(Cần MySQL, cách B ở mục 1.4.) Vì sao bắt lỗi trùng thay vì `SELECT` kiểm tra trước rồi mới
`INSERT`? Vì giữa lúc kiểm tra và lúc insert, một request khác có thể chen vào insert cùng email. Ràng
buộc `UNIQUE` trong database mới là chốt chặn thật; kiểm tra trước chỉ để báo lỗi thân thiện sớm hơn.

⚠️ **Không hiển thị `getMessage()` cho người dùng.** Message chứa tên bảng, tên cột, đôi khi cả giá trị
dữ liệu (như email ở trên). Ghi log đầy đủ, trả cho người dùng câu chung chung. Laravel bọc
`PDOException` thành `Illuminate\Database\QueryException` có kèm câu SQL và binding trong message, càng
không được lộ ra ngoài. Về logging và handler chung: [chương 12](12-loi-exception.md); về cấu hình
`display_errors`: [chương 17](17-bao-mat.md).

## 9. Buffered và unbuffered query

### 9.1 Kết quả nằm ở đâu khi bạn fetch?

Khi MySQL chạy xong một câu `SELECT`, các dòng kết quả phải đi qua mạng về PHP. Có hai cách nhận:

```
Buffered (mặc định)                              Unbuffered
query() ──▶ mysqlnd đọc HẾT các dòng từ socket   query() ──▶ chỉ gửi câu lệnh, chưa đọc dòng nào
            vào bộ nhớ của process PHP           fetch() ──▶ đọc MỘT dòng từ socket
fetch() ──▶ lấy dòng từ bộ nhớ, không chạm mạng  fetch() ──▶ đọc dòng tiếp theo ...
```

Theo manual PHP (Buffered and Unbuffered queries):

- **Buffered** (còn gọi là *store result*): toàn bộ kết quả chuyển ngay về PHP. Được: biết số dòng, chạy
  query khác trên cùng connection trong khi đang duyệt. Mất: kết quả lớn tốn nhiều bộ nhớ, và với
  mysqlnd bộ nhớ này **tính vào `memory_limit`**.
- **Unbuffered** (*use result*): PHP tốn ít bộ nhớ, nhưng server phải giữ kết quả lâu hơn, và **chưa
  đọc hết thì không gửi được câu nào khác trên connection đó**. Đọc xong thì không duyệt lại được.

Ví dụ đọc 100.000 dòng, mỗi dòng khoảng 100 byte, mỗi chế độ chạy riêng một process (output minh hoạ:
số MB cụ thể tuỳ phiên bản PHP, kiến trúc máy và dữ liệu; điều đáng nhớ là thứ bậc giữa hai dòng):

| | Bộ nhớ tăng ngay sau `query()` | Peak memory | Chạy query khác giữa chừng |
|---|---|---|---|
| Buffered | cỡ chục MB (tỉ lệ với kích thước kết quả) | cỡ chục MB | Được |
| Unbuffered | gần như không tăng | gần như không tăng | Lỗi 2014 |

Bộ nhớ của buffered query tăng theo kích thước kết quả. Với kết quả cỡ hàng triệu dòng, nó có thể vượt
`memory_limit` mặc định (128M) và làm script chết với "Allowed memory size exhausted", dù code chỉ duyệt
từng dòng bằng `foreach`.

### 9.2 Dùng unbuffered query

```php
<?php
declare(strict_types=1);

// Cần MySQL (cách B, mục 1.4). Xuất toàn bộ bảng users ra CSV mà RAM gần như không đổi.
// Dùng một connection RIÊNG cho việc này.
$export = PDO::connect('mysql:host=my84;dbname=ch16;charset=utf8mb4', 'app', 'app-secret', [
    PDO::ATTR_ERRMODE                  => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE       => PDO::FETCH_ASSOC,
    Pdo\Mysql::ATTR_USE_BUFFERED_QUERY => false,
]);

$out = fopen('php://output', 'w');
foreach ($export->query('SELECT id, email, name FROM users ORDER BY id') as $row) {
    fputcsv($out, $row, escape: '');   // từ PHP 8.4, không truyền $escape tường minh là deprecated
}
fclose($out);
```

Nếu trong vòng lặp bạn chạy thêm một query trên **cùng** connection (thử với MySQL 8.4):

```
SQLSTATE[HY000]: General error: 2014 Cannot execute queries while other unbuffered queries are active.
Consider using PDOStatement::fetchAll().  Alternatively, if your code is only ever going to run against
mysql, you may enable query buffering by setting the Pdo\Mysql::ATTR_USE_BUFFERED_QUERY attribute.
```

Vì vậy unbuffered nên dùng một connection riêng, chỉ để đọc tuần tự. Dừng giữa chừng thì gọi
`$stmt->closeCursor()` (hoặc huỷ statement) để giải phóng connection trước khi chạy câu khác.
`rowCount()` không cho biết số dòng của `SELECT` unbuffered (thử thấy trả về 0).

### 9.3 Lựa chọn khác: đọc theo lô

Unbuffered giữ một câu query mở suốt thời gian xử lý, có thể là nhiều phút. Một cách khác hay dùng hơn
trong ứng dụng web và job là **đọc theo lô bằng khoá** (*keyset pagination*): mỗi lần lấy 1.000 dòng có
`id` lớn hơn `id` cuối của lô trước. Mỗi lô là một query buffered ngắn, bộ nhớ chỉ bằng một lô:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

/** @return Generator<int, array<string, mixed>> */
function docTheoLo(PDO $pdo, int $kichThuocLo): Generator
{
    $stmt = $pdo->prepare('SELECT id, email FROM users WHERE id > ? ORDER BY id LIMIT ?');
    $idCuoi = 0;
    do {
        $stmt->bindValue(1, $idCuoi, PDO::PARAM_INT);
        $stmt->bindValue(2, $kichThuocLo, PDO::PARAM_INT);
        $stmt->execute();
        $lo = $stmt->fetchAll();
        foreach ($lo as $row) {
            yield $row;
        }
        $idCuoi = $lo === [] ? $idCuoi : $lo[array_key_last($lo)]['id'];
    } while (count($lo) === $kichThuocLo);
}

foreach (docTheoLo($pdo, 2) as $row) {
    echo $row['id'], ' ', $row['email'], "\n";
}
// in ra:
// 1 an@example.com
// 2 binh@example.com
// 3 chi@example.com
```

Generator (`yield`) giúp người gọi duyệt như một danh sách bình thường mà không biết bên dưới chia lô
([chương 13](13-generator-iterator-spl.md)). Vì sao keyset nhanh hơn `LIMIT ... OFFSET ...` với bảng
lớn: [giáo trình Database, chương 12](../database/12-explain-toi-uu-query.md). Laravel có sẵn các công cụ
tương đương (`chunkById`, `lazyById`, `cursor`), xem [chương 27](27-laravel-database-eloquent.md).

## 10. Connection trong vòng đời của PHP

### 10.1 Mỗi worker một connection, không có pool

Java hay Go chạy **một process sống lâu**, giữ một *connection pool* (bể connection dùng chung): vài
chục connection mở sẵn, hàng nghìn request lần lượt mượn rồi trả. PHP-FPM hoạt động khác hẳn
([chương 02](02-php-chay-nhu-the-nao.md), [chương 18](18-fpm-nginx-opcache.md)):

```
                      ┌─ worker 1 ── request A: new PDO() ─── connection #1 ─┐
Nginx ─▶ PHP-FPM ─────┼─ worker 2 ── request B: new PDO() ─── connection #2 ─┼──▶ MySQL
  (master)            ├─ worker 3 ── (rảnh, không có connection)              │   max_connections
                      └─ worker N ── request X: new PDO() ─── connection #N ─┘   (mặc định 151)
```

- Mỗi worker xử lý **một request tại một thời điểm**. Request mở connection riêng (với PDO thuần là lúc
  `new PDO`; Laravel trì hoãn tới query đầu tiên), dùng, rồi PHP đóng nó khi request kết thúc. Không có pool dùng chung giữa các worker.
- Hệ quả: **số connection tới MySQL tỉ lệ với số worker đang bận**, không tỉ lệ với số query.

Ước lượng số connection tối đa:

```
≈ số server web × pm.max_children × (số connection mỗi request)
  + queue worker + cron + công cụ admin, monitoring, replica

Ví dụ: 4 server × 50 children × 1 + 10 queue worker + 5 khác = 215
       > max_connections mặc định của MySQL (151)  →  lỗi 1040 "Too many connections"
```

- Một request có thể mở **hai** connection, ví dụ app tách đọc/ghi (một tới replica, một tới primary).
- ⚠️ Autoscale thêm server web là thêm connection. Lúc traffic tăng vọt, database có thể hết connection
  trước khi app kịp chậm. Giới hạn số worker phải tính ngược từ `max_connections`, hoặc đặt một proxy
  pool ở giữa (ProxySQL cho MySQL, PgBouncer cho PostgreSQL). Pool, proxy và cách tính kích thước:
  [giáo trình Database, chương 19](../database/19-database-tu-ung-dung.md).
- Mở connection không miễn phí: bắt tay TCP, xác thực, thêm TLS nếu bật. Với database cùng data center
  thì thường chấp nhận được; database ở xa hoặc qua TLS thì chi phí này lộ rõ.

### 10.2 Persistent connection và rủi ro

*Persistent connection* (`PDO::ATTR_PERSISTENT => true`, chỉ có tác dụng khi đặt trong constructor):
connection **không đóng** khi request kết thúc mà được worker giữ lại; request sau do **cùng worker đó**
phục vụ, kết nối tới cùng host với cùng username và password, sẽ dùng lại nó.

Manual PHP (Persistent Database Connections) nói rất thẳng:

- Persistent connection **không làm được gì** mà connection thường không làm được. Lợi ích duy nhất là
  bỏ chi phí mở kết nối.
- Không chọn được connection cụ thể, nên **không thể** dùng nó để giữ transaction qua nhiều request,
  hay gắn một session database với một người dùng.
- Mỗi worker giữ connection của riêng mình **kể cả khi rảnh**. 20 worker là 20 connection thường trực.
  Sau một đợt spike, các worker rảnh vẫn giữ connection cho tới khi worker bị tắt hoặc server đóng vì
  timeout. Số connection thường **tăng** chứ không giảm.
- ⚠️ **Trạng thái rò sang request sau.** Manual PDO: "PDO does not perform any cleanup of persistent
  connections". Những thứ có thể còn sót: database đang chọn, table lock, transaction, temporary table,
  biến và thiết lập của session. (Riêng transaction đang mở: mã nguồn PDO hiện nay rollback nó khi
  object `PDO` bị huỷ cuối request, kể cả với persistent connection; các thứ còn lại thì không ai dọn.)

Một kịch bản xấu, với persistent connection, xuất phát từ một thiết lập session bị rò:

| Bước | Request 1 (worker 7) | Request 2 (worker 7, sau đó) | Kết quả |
|---|---|---|---|
| 1 | Chạy `SET autocommit = 0` (ví dụ một đoạn code cũ muốn tự quản lý commit) | | Thiết lập này thuộc về session, tức là thuộc về connection |
| 2 | Kết thúc request | | Connection không đóng, session vẫn `autocommit = 0` |
| 3 | | Dùng lại connection đó, chạy vài câu `INSERT` mà không gọi `beginTransaction()` | Với `autocommit = 0`, các câu này nằm trong một transaction chưa commit |
| 4 | | Kết thúc, không biết mình đang ở trong transaction | PDO thấy transaction còn mở nên rollback: dữ liệu request 2 **biến mất** dù không có lỗi nào |

Kết luận của manual: không dùng persistent connection khi chưa cân nhắc kỹ, chưa sửa ứng dụng và chưa
cấu hình database lẫn PHP-FPM tương ứng; nên xem xét proxy pool hoặc runtime chạy lâu. Mặc định nên
**để tắt**. Laravel cũng không bật nó: danh sách option mặc định ở mục 2.5 không có `ATTR_PERSISTENT`.

### 10.3 Script chạy lâu: "MySQL server has gone away"

Queue worker, daemon, và các runtime giữ app sống qua nhiều request (Laravel Octane trên Swoole,
RoadRunner, FrankenPHP) giữ một object PDO rất lâu. Hai chuyện xảy ra:

- MySQL tự đóng connection rảnh quá `wait_timeout` (mặc định 28800 giây, tức 8 giờ; nhiều dịch vụ
  managed đặt thấp hơn). PHP không biết cho tới lần query tiếp theo, rồi nhận lỗi "MySQL server has gone
  away" (2006) hoặc "Lost connection to MySQL server during query" (2013). PHP 8.4 UPGRADING ghi thêm:
  với MySQL server từ 8.0.24, mysqlnd báo mã 4031 thay vì 2006 cho trường hợp server đóng vì timeout.
  Code bắt lỗi mất kết nối bằng cách so mã phải tính cả mã này.
- mysqlnd **không tự kết nối lại** (manual: bảng so sánh thư viện, dòng "Automatic reconnect: No").
  Phải tự bắt lỗi, tạo PDO mới, và chạy lại. ⚠️ Chỉ chạy lại an toàn khi **không** ở giữa transaction:
  connection mất là transaction trên server đã bị rollback, các câu trước trong transaction mất theo.
  Laravel cũng theo đúng nguyên tắc này: tự reconnect và chạy lại query khi mất kết nối, nhưng không
  làm vậy khi đang trong transaction.

Các trạng thái rò rỉ ở 10.2 cũng áp dụng cho runtime chạy lâu, vì connection sống qua nhiều request.
Chi tiết về Octane: [chương 30](30-laravel-testing-octane-deploy.md).

## 11. mysqli: nhắc qua để đọc được code cũ

`mysqli` là extension riêng cho MySQL, cũng chạy trên mysqlnd. Bạn sẽ gặp nó trong WordPress, các
project PHP thuần cũ, và code cần tính năng riêng của MySQL. Cùng các việc ở trên, viết bằng mysqli:

```php
<?php
declare(strict_types=1);

// Cần MySQL (cách B, mục 1.4) và extension mysqli.
$db = new mysqli('my84', 'app', 'app-secret', 'ch16');
$db->set_charset('utf8mb4');                         // cách đặt charset đúng của mysqli, không dùng SET NAMES

// PHP 8.2+: prepare + bind + execute trong một lời gọi
$result = $db->execute_query('SELECT id, name, balance FROM users WHERE email = ?', ['an@example.com']);
var_dump($result->fetch_assoc());
// in ra: array(3) { ["id"]=> int(1) ["name"]=> string(2) "An" ["balance"]=> string(7) "1500.50" }  (rút gọn)

// Kiểu cũ: bind_param với chuỗi kiểu ('i' = int, 's' = string, 'd' = double, 'b' = blob)
$stmt = $db->prepare('SELECT name FROM users WHERE id = ?');
$id = 1;
$stmt->bind_param('i', $id);                         // gắn THAM CHIẾU như bindParam của PDO
$stmt->execute();
var_dump($stmt->get_result()->fetch_assoc());        // in ra: array(1) { ["name"]=> string(2) "An" }  (rút gọn)

try {
    $db->query('SELECT * FROM khong_co');
} catch (mysqli_sql_exception $e) {
    echo $e->getCode(), ' ', $e->getSqlState(), ' ', $e->getMessage(), "\n";
    // in ra: 1146 42S02 Table 'ch16.khong_co' doesn't exist
}
```

| | PDO | mysqli |
|---|---|---|
| Database | Nhiều loại (qua driver) | Chỉ MySQL/MariaDB |
| Kiểu viết | Chỉ object | Object hoặc hàm (`mysqli_query($db, ...)`) |
| Placeholder | `?` và `:ten` | Chỉ `?` |
| Lỗi mặc định | Exception từ PHP 8.0 | Exception từ PHP 8.1 (trước đó im lặng, phải tự kiểm tra) |
| `getCode()` của exception | Lẫn lộn string/int (mục 8.2) | Mã MySQL dạng int; SQLSTATE qua `getSqlState()` |
| Tính năng riêng MySQL | Ít hơn | Đầy đủ hơn (query bất đồng bộ, multi query...) |
| Laravel, Doctrine | Laravel dùng PDO | Doctrine DBAL hỗ trợ cả hai |

Cả hai đều an toàn khi dùng prepared statement, và manual xếp cả hai là "recommended for new projects".
Chọn PDO cho code mới trừ khi cần tính năng chỉ mysqli có.

## 12. Từ SQL viết tay tới ORM, và bài toán N+1

### 12.1 Gom SQL vào một chỗ

Rải `$pdo->prepare(...)` khắp controller làm code khó đọc, khó test, khó đổi schema. Cách tổ chức phổ
biến là gom mọi câu SQL của một loại dữ liệu vào một class, thường gọi là *repository*:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';

final readonly class User
{
    public function __construct(public int $id, public string $email, public string $name) {}
}

final readonly class UserRepository
{
    public function __construct(private PDO $pdo) {}

    public function timTheoId(int $id): ?User
    {
        $stmt = $this->pdo->prepare('SELECT id, email, name FROM users WHERE id = ?');
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        return $row === false ? null : new User($row['id'], $row['email'], $row['name']);
    }

    public function them(string $email, string $name): User
    {
        $this->pdo->prepare('INSERT INTO users (email, name, password) VALUES (?, ?, ?)')
            ->execute([$email, $name, '']);
        return new User((int) $this->pdo->lastInsertId(), $email, $name);
    }
}

$repo = new UserRepository(taoDbMau());
echo $repo->timTheoId(2)?->name, "\n";                     // in ra: Bình
var_dump($repo->timTheoId(999));                           // in ra: NULL
echo $repo->them('dung@example.com', 'Dũng')->id, "\n";    // in ra: 4
```

Phần còn lại của ứng dụng chỉ thấy `User` và `UserRepository`, không thấy SQL. Đổi tên cột chỉ sửa một
chỗ; test có thể truyền một PDO SQLite thay cho MySQL.

### 12.2 ORM là gì

Viết repository cho từng bảng, map từng cột sang property, xử lý quan hệ giữa các bảng... lặp đi lặp
lại. *ORM* (*Object-Relational Mapping*) là thư viện làm phần lặp lại đó: bạn khai báo class tương ứng
với bảng, ORM sinh SQL, chạy qua PDO, và đổ kết quả thành object. Hai trường phái:

| | Active Record | Data Mapper |
|---|---|---|
| Ý tưởng | Object **tự biết** lưu và nạp chính nó: `$user->save()`, `User::find(1)` | Object chỉ chứa dữ liệu; một lớp riêng (mapper/entity manager) lo lưu và nạp |
| Ví dụ PHP | Laravel Eloquent | Doctrine ORM |
| Mạnh | Viết nhanh, ít code | Tách biệt nghiệp vụ khỏi database, dễ test phần nghiệp vụ |
| Yếu | Model dính chặt với bảng; dễ chạy query mà không nhận ra | Nhiều khái niệm hơn, cấu hình nhiều hơn |

Dù dùng ORM nào, bên dưới vẫn là đúng những thứ trong chương này: PDO, prepared statement, transaction,
kiểu dữ liệu trả về. Eloquent chi tiết ở [chương 27](27-laravel-database-eloquent.md); so sánh hai
trường phái từ phía database ở [giáo trình Database, chương 19](../database/19-database-tu-ung-dung.md).

### 12.3 Bài toán N+1

Bài toán kinh điển nhất khi làm việc với database từ code: hiển thị danh sách bài viết kèm tên tác giả.
Cách viết "tự nhiên" chạy **1** query lấy N bài, rồi trong vòng lặp chạy **N** query lấy tác giả của
từng bài. Tổng cộng N+1 query. Ví dụ dưới đếm số query thật sự gửi đi:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/db-sqlite.php';
$pdo = taoDbMau();

$soQuery = 0;   // đếm số câu gửi tới database

/** @return list<array<string, mixed>> */
function chay(PDO $pdo, string $sql, array $thamSo = []): array
{
    global $soQuery;
    $soQuery++;
    $stmt = $pdo->prepare($sql);
    $stmt->execute($thamSo);
    return $stmt->fetchAll();
}

// Cách 1: N+1. Một query lấy bài, mỗi bài thêm một query lấy tác giả
$soQuery = 0;
foreach (chay($pdo, 'SELECT id, user_id, title FROM posts ORDER BY id') as $post) {
    $tacGia = chay($pdo, 'SELECT name FROM users WHERE id = ?', [$post['user_id']])[0];
    echo $post['title'], ' - ', $tacGia['name'], "\n";
}
echo "Số query: $soQuery\n\n";          // in ra: Số query: 5   (1 + 4 bài)

// Cách 2: gom id, MỘT query IN (...), ghép trong PHP (đây là cách eager loading của ORM)
$soQuery = 0;
$posts = chay($pdo, 'SELECT id, user_id, title FROM posts ORDER BY id');
$ids   = array_values(array_unique(array_column($posts, 'user_id')));
$cho   = implode(', ', array_fill(0, count($ids), '?'));
$tenTheoId = array_column(chay($pdo, "SELECT id, name FROM users WHERE id IN ($cho)", $ids), 'name', 'id');
foreach ($posts as $post) {
    echo $post['title'], ' - ', $tenTheoId[$post['user_id']], "\n";
}
echo "Số query: $soQuery\n\n";          // in ra: Số query: 2

// Cách 3: JOIN, một query
$soQuery = 0;
foreach (chay($pdo, 'SELECT p.title, u.name FROM posts p JOIN users u ON u.id = p.user_id ORDER BY p.id') as $dong) {
    echo $dong['title'], ' - ', $dong['name'], "\n";
}
echo "Số query: $soQuery\n";            // in ra: Số query: 1
// Cả ba cách in cùng 4 dòng: "Bài 1 của An - An", "Bài 2 của An - An", "Bài của Bình - Bình", "Bài của Chi - Chi"
```

Vì sao N+1 nguy hiểm dù mỗi query rất nhanh:

- Mỗi query là một round-trip (mục 1.1). 500 bài là 501 lần đi về; mỗi lần 1 ms là nửa giây chỉ để chờ
  mạng.
- Từng query riêng lẻ đều nhanh nên **không bao giờ xuất hiện trong slow query log**. Muốn phát hiện
  phải **đếm số query mỗi request** (như biến `$soQuery` ở trên; Laravel có Debugbar, Telescope, và
  `preventLazyLoading`).
- Nó thường ẩn: không ai viết vòng lặp query một cách cố ý. Với ORM, chỉ cần truy cập
  `$post->author->name` trong template là ORM lặng lẽ chạy một query (*lazy loading*).

Cách 2 chính là điều ORM làm khi bạn yêu cầu *eager loading* (Eloquent: `Post::with('author')`). Cách 3
(JOIN) cũng tốt, nhưng với quan hệ một-nhiều nó nhân bản dữ liệu của phía "một" lên mỗi dòng. N+1 trong
Eloquent và các công cụ phát hiện: [chương 27](27-laravel-database-eloquent.md); từ phía database:
[giáo trình Database, chương 19](../database/19-database-tu-ung-dung.md).

### 12.4 Đối chiếu với Go và Java

| | PHP (PDO, PHP-FPM) | Go (`database/sql`) | Java (JDBC + HikariCP) |
|---|---|---|---|
| Connection | Mỗi request mở/đóng, mỗi worker một connection | `sql.DB` là một **pool** dùng chung cho mọi goroutine | Pool (HikariCP là lựa chọn phổ biến) dùng chung cho mọi thread |
| Prepared statement | `$pdo->prepare()`, placeholder `?`/`:ten` | `db.Query(sql, args...)`, placeholder tuỳ driver (`?` cho MySQL, `$1` cho Postgres) | `PreparedStatement`, placeholder `?` |
| Báo lỗi | Exception (`PDOException`) | Giá trị `error` trả về | Exception (`SQLException`, checked) |
| Transaction | `beginTransaction()`... trên chính connection | `tx, err := db.Begin()`, mọi câu phải chạy trên `tx` | `conn.setAutoCommit(false)`, `commit()` |

Điểm khác lớn nhất là mô hình connection: Go và Java giới hạn số connection bằng kích thước pool trong
process, còn PHP-FPM giới hạn gián tiếp qua số worker (mục 10.1).

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Ghép biến vào chuỗi SQL (`"... WHERE email = '$email'"`) | SQL injection: dữ liệu thành cú pháp (3.2) | Luôn `prepare` + placeholder cho mọi giá trị không phải hằng |
| Dùng placeholder cho tên cột, `ASC`/`DESC`, tên bảng | Placeholder chỉ thay giá trị trọn vẹn | Whitelist trong PHP (3.3) |
| `LIKE '%?%'` | `?` nằm trong chuỗi literal, không phải placeholder | `LIKE ?` và truyền `'%' . $x . '%'` |
| `IN (?)` với cả một mảng | Một placeholder chỉ nhận một giá trị | Sinh đúng số `?`, kiểm tra mảng rỗng (3.3) |
| `execute([false])` vào cột số | `false` thành `''`, strict mode ném lỗi 1366 (3.4) | `bindValue(..., PDO::PARAM_BOOL)` hoặc `(int)` |
| `LIMIT ?` lỗi 1064 | Emulated prepare ghép `LIMIT '10'` (3.5) | `EMULATE_PREPARES => false`, hoặc `bindValue(..., PDO::PARAM_INT)` |
| `bindParam` trong vòng lặp | Gắn tham chiếu, mọi chỗ nhận giá trị cuối (3.4) | `bindValue` hoặc `execute([...])` |
| Không ghi `charset` trong DSN, hoặc dùng `utf8` | Charset phụ thuộc server; `utf8` là `utf8mb3`, mất emoji (2.3) | `charset=utf8mb4` trong DSN |
| `host=localhost` khi MySQL ở container khác | `localhost` đi qua Unix socket cục bộ (2.1) | Tên service/IP, hoặc `127.0.0.1` |
| Để `FETCH_BOTH` mặc định | Mỗi giá trị lặp hai lần, JSON thừa (4.2) | `DEFAULT_FETCH_MODE => FETCH_ASSOC` |
| Không kiểm tra `fetch() === false` | Dùng `false` như mảng (4.1) | Kiểm tra trước khi dùng |
| So `=== '1'` sau khi nâng lên PHP 8.1 | Cột số giờ là `int` (5.1) | So với `int`, hoặc tạm bật `STRINGIFY_FETCHES` |
| Ép `DECIMAL` sang `float` để tính tiền | Mất độ chính xác (5.2) | bcmath, `BcMath\Number`, hoặc lưu số nguyên đơn vị nhỏ |
| `catch (PDOException)` mà không rollback, hoặc rollback khi transaction đã kết thúc | Transaction treo, hoặc lỗi "no active transaction" che lỗi gốc (6.2, 6.3) | Bắt `Throwable`, `if ($pdo->inTransaction()) rollBack()`, ném tiếp |
| DDL trong transaction | MySQL implicit commit (6.3) | Tách DDL khỏi transaction |
| Gọi `lastInsertId()` sau một câu khác | MySQL trả `"0"` (7) | Gọi ngay sau `INSERT` |
| Phân loại lỗi bằng `getCode()` | Lúc string, lúc int, lúc 0 (8.2) | `$e->errorInfo[1]` |
| In `getMessage()` ra cho người dùng | Lộ cấu trúc bảng, dữ liệu (8.3) | Log đầy đủ, hiển thị thông báo chung |
| `SELECT` hàng triệu dòng với buffered query | Toàn bộ kết quả vào `memory_limit` (9) | Unbuffered trên connection riêng, hoặc đọc theo lô |
| Bật `ATTR_PERSISTENT` để "tăng tốc" | Rò trạng thái session (lock, thiết lập, temporary table), tăng số connection (10.2) | Để tắt; cần thì dùng proxy pool |
| Query trong vòng lặp (N+1) | N round-trip, không lên slow log (12.3) | Gom `IN (...)`, JOIN, eager loading |

## Tóm tắt chương

- Code PHP nói chuyện với MySQL qua các tầng: PDO (API chung) → driver `pdo_mysql` → mysqlnd → mạng.
  Mỗi query là một round-trip; kết quả buffered nằm trong `memory_limit`.
- Kết nối bằng DSN `mysql:host=...;dbname=...;charset=utf8mb4`. Constructor kết nối ngay và luôn ném
  `PDOException` khi thất bại. Đặt `ERRMODE_EXCEPTION`, `EMULATE_PREPARES => false`,
  `DEFAULT_FETCH_MODE => FETCH_ASSOC`. Từ 8.5 dùng `Pdo\Mysql::ATTR_*` thay cho `PDO::MYSQL_ATTR_*`.
- Prepared statement tách câu lệnh khỏi dữ liệu nên chống SQL injection; placeholder chỉ thay giá trị,
  phần còn lại (tên cột, chiều sắp xếp) phải whitelist.
- `execute([...])` gửi mọi giá trị dạng string; khi kiểu quan trọng (bool, `LIMIT` với emulate) dùng
  `bindValue` kèm `PDO::PARAM_*`.
- Từ PHP 8.1, cột số nguyên/số thực về PHP là `int`/`float` ở cả hai chế độ prepare; `DECIMAL`, ngày giờ,
  JSON, `BIGINT UNSIGNED` vượt giới hạn vẫn là string.
- Transaction: `beginTransaction` → việc → `commit`; lỗi gì cũng `rollBack` (nếu còn transaction) rồi ném
  tiếp. DDL tự commit trong MySQL. Không lồng transaction, dùng savepoint. Deadlock (1213) thì chạy lại
  toàn bộ transaction, không lặp lại tác dụng phụ bên ngoài.
- `lastInsertId()` trả string, theo connection, gọi ngay sau `INSERT`.
- Phân loại lỗi bằng `errorInfo[1]` (mã MySQL), không bằng `getCode()`; không lộ message cho người dùng.
- PHP-FPM: mỗi worker một connection, không có pool; tổng connection phải nằm dưới `max_connections`.
  Persistent connection có lợi ích hẹp và rủi ro rò trạng thái; script chạy lâu phải xử lý "gone away".
- ORM tự động hoá việc map bảng ↔ object; N+1 là cái bẫy lớn nhất, sửa bằng gom `IN (...)`/eager
  loading hoặc JOIN.

## Câu hỏi tự kiểm tra

1. `host=localhost` và `host=127.0.0.1` trong DSN của PDO_MYSQL khác nhau thế nào trên Linux? Vì sao
   `localhost` thường hỏng khi PHP và MySQL chạy ở hai container? (2.1)
2. Vì sao ghi `charset=utf8mb4` trong DSN an toàn hơn chạy `SET NAMES utf8mb4` sau khi kết nối, xét riêng
   trường hợp bật emulated prepare? (2.3, 3.5)
3. Giải thích bằng lời của bạn vì sao prepared statement chặn được chuỗi `' OR 1=1 -- `, và cho hai ví dụ
   về phần của câu SQL mà prepared statement **không** bảo vệ được.
4. Cùng câu `SELECT ... LIMIT ?` và `execute([10])`, vì sao chạy được khi `EMULATE_PREPARES => false`
   nhưng lỗi 1064 khi bằng `true`?
5. Một project nâng từ PHP 8.0 lên 8.2, không đổi gì về PDO, và một số điều kiện `if` bắt đầu sai. Nguyên
   nhân khả dĩ nhất là gì, và cách sửa nhanh tạm thời? (5.1)
6. Đoạn code bắt `PDOException` trong transaction rồi gọi `rollBack()`, nhưng log lại ghi "There is no
   active transaction" thay vì lỗi gốc. Có những khả năng nào? (6.3)
7. Vì sao không nên dùng `$e->getCode()` để nhận biết lỗi trùng email, và nên dùng gì?
8. Với 3 server web, mỗi server `pm.max_children = 60`, thêm 20 queue worker, cấu hình MySQL mặc định thì
   có thể gặp lỗi gì lúc cao điểm? Kể hai hướng xử lý. (10.1)
9. Persistent connection có thể khiến dữ liệu của request B "biến mất" dù request B không có lỗi nào.
   Mô tả kịch bản đó.
10. Trang danh sách 50 đơn hàng, mỗi đơn hiển thị tên khách hàng, chạy 51 query. Mỗi query mất 0.5 ms
    trên database. Vì sao slow query log không cho thấy vấn đề, và bạn sẽ sửa thế nào? (12.3)

## Bài tập

1. **Lớp kết nối cấu hình đúng.** Viết hàm `taoKetNoi(string $dsn, string $user, #[\SensitiveParameter]
   string $pass): PDO` dùng được cho cả MySQL và SQLite: luôn đặt error mode exception và fetch mode
   assoc, chỉ tắt emulated prepare khi driver là `mysql` (đọc `PDO::ATTR_DRIVER_NAME`). Viết một script
   chứng minh bằng output rằng: kết nối sai mật khẩu ném exception mà trace không lộ mật khẩu; `LIMIT ?`
   với `execute([2])` chạy được trên MySQL.
2. **Sửa code dính SQL injection.** Viết một trang tìm kiếm sản phẩm nhận `q` (từ khoá), `sort`
   (`price`/`name`/`created_at`), `dir` (`asc`/`desc`) và `ids[]` (lọc theo danh sách id) từ query
   string, xây câu `SELECT` an toàn với prepared statement và whitelist. Thử tấn công chính trang của bạn
   bằng ít nhất ba chuỗi độc hại và ghi lại kết quả.
3. **Chuyển khoản có chạy lại.** Dùng MySQL (cách B), tạo bảng `accounts (id, balance DECIMAL(12,2))`.
   Viết `chuyenKhoan(PDO $pdo, int $tu, int $den, string $soTien)` tính tiền bằng `BcMath\Number` hoặc
   bcmath, chạy trong một hàm bọc transaction có retry khi deadlock. Mở hai terminal chạy hai script
   chuyển tiền ngược chiều nhau (A → B và B → A) có `sleep()` xen giữa hai câu `UPDATE` để gây deadlock,
   và cho thấy một bên tự chạy lại thành công.
4. **Đo N+1 và bộ nhớ.** Với SQLite, tạo 1.000 user, mỗi user 5 bài viết. Viết ba phiên bản trang
   "danh sách bài viết kèm tên tác giả" (N+1, `IN (...)`, JOIN), in số query và thời gian của mỗi phiên
   bản. Sau đó với MySQL, so sánh `memory_get_peak_usage()` khi đọc toàn bộ bảng bài viết bằng buffered
   query, unbuffered query, và đọc theo lô 500 dòng.

## Đọc thêm

- PHP Manual: [PDO](https://www.php.net/manual/en/book.pdo.php) ·
  [Connections and Connection management](https://www.php.net/manual/en/pdo.connections.php) ·
  [Transactions and auto-commit](https://www.php.net/manual/en/pdo.transactions.php) ·
  [Prepared statements](https://www.php.net/manual/en/pdo.prepared-statements.php) ·
  [Errors and error handling](https://www.php.net/manual/en/pdo.error-handling.php) ·
  [PDO::__construct](https://www.php.net/manual/en/pdo.construct.php) ·
  [PDO::connect](https://www.php.net/manual/en/pdo.connect.php) ·
  [PDO::setAttribute](https://www.php.net/manual/en/pdo.setattribute.php) ·
  [PDO::prepare](https://www.php.net/manual/en/pdo.prepare.php) ·
  [PDOStatement::execute](https://www.php.net/manual/en/pdostatement.execute.php) ·
  [PDOStatement::bindParam](https://www.php.net/manual/en/pdostatement.bindparam.php) ·
  [PDOStatement::fetch](https://www.php.net/manual/en/pdostatement.fetch.php)
- PHP Manual, phần MySQL: [PDO_MYSQL](https://www.php.net/manual/en/ref.pdo-mysql.php) ·
  [PDO_MYSQL DSN](https://www.php.net/manual/en/ref.pdo-mysql.connection.php) ·
  [Pdo\Mysql](https://www.php.net/manual/en/class.pdo-mysql.php) ·
  [Buffered and Unbuffered queries](https://www.php.net/manual/en/mysqlinfo.concepts.buffering.php) ·
  [Character sets](https://www.php.net/manual/en/mysqlinfo.concepts.charset.php) ·
  [Choosing an API](https://www.php.net/manual/en/mysqlinfo.api.choosing.php) ·
  [Choosing a library](https://www.php.net/manual/en/mysqlinfo.library.choosing.php) ·
  [Persistent Database Connections](https://www.php.net/manual/en/features.persistent-connections.php)
- php-src: UPGRADING của [8.0](https://github.com/php/php-src/blob/PHP-8.0/UPGRADING),
  [8.1](https://github.com/php/php-src/blob/PHP-8.1/UPGRADING),
  [8.4](https://github.com/php/php-src/blob/PHP-8.4/UPGRADING),
  [8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) ·
  RFC: [PDO default error mode](https://wiki.php.net/rfc/pdo_default_errmode),
  [PDO driver specific subclasses](https://wiki.php.net/rfc/pdo_driver_specific_subclasses)
- MySQL 8.4 Reference Manual: [Statements That Cause an Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html) ·
  [InnoDB Error Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html) ·
  [Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html) ·
  [MySQL server has gone away](https://dev.mysql.com/doc/refman/8.4/en/gone-away.html) ·
  [Comments](https://dev.mysql.com/doc/refman/8.4/en/comments.html) ·
  [Server Error Message Reference](https://dev.mysql.com/doc/mysql-errors/8.4/en/server-error-reference.html)
- Laravel 13 (mã nguồn): [Connectors/Connector.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Connectors/Connector.php) ·
  [Connectors/MySqlConnector.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Connectors/MySqlConnector.php) ·
  [Concerns/ManagesTransactions.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Concerns/ManagesTransactions.php)
- [docker-library/php](https://github.com/docker-library/php): Dockerfile của image `php`, xem extension
  nào có sẵn.
