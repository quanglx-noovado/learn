# Chương 12. Lỗi và exception

> [← Mục lục](README.md) · [← Chương 11: Namespace, autoload và Composer](11-namespace-composer.md) · [Chương 13: Generator, iterator và SPL →](13-generator-iterator-spl.md)

**Bạn sẽ học được:**

- PHP có hai cơ chế báo lỗi chạy song song (error reporting kiểu cũ và exception), vì sao lại có hai,
  và mỗi loại "lỗi" (warning, notice, deprecated, `Error`, `Exception`, fatal error) bắt được bằng gì.
- Dùng `throw`, `try`, `catch`, `finally` đúng cách, hiểu exception "nổi lên" call stack thế nào và các
  bẫy của `finally` khi gặp `return`.
- Cây `Throwable`: nhánh `Error` và nhánh `Exception`, chọn class nào để ném, tự định nghĩa exception
  và nối exception bằng `previous`.
- Cấu hình `error_reporting`, `display_errors`, `log_errors` cho môi trường dev và production.
- Dùng `set_error_handler`, `ErrorException`, `set_exception_handler`, `register_shutdown_function` để
  không lỗi nào lọt lưới, và đọc được backtrace của fatal error trên PHP 8.5.
- Những thói quen xử lý lỗi tốt, và Laravel ghép các mảnh trên lại thế nào.

**Cần biết trước:** [Chương 08: Hàm](08-ham.md) (hàm, closure, khai báo kiểu tham số và giá trị trả về),
[Chương 09: OOP cơ bản](09-oop-co-ban.md) (class, kế thừa, interface, `instanceof`). Biết toán tử `@`
ở [Chương 07](07-toan-tu-dieu-khien.md) mục 10 thì tốt, không bắt buộc.

Cách chạy ví dụ: lưu thành file `.php` rồi chạy `php ten-file.php` trong terminal, ở thư mục chứa
file. Output ghi trong comment là output trên PHP 8.5 ở chế độ dòng lệnh (CLI). Đường dẫn file trong
thông báo lỗi được rút gọn thành `.../ten-file.php`. Máy chưa cài PHP thì dùng Docker:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

## 1. Bức tranh tổng thể: PHP báo lỗi bằng hai cơ chế

### 1.1 "Lỗi" là những chuyện gì

Chương trình nào cũng gặp chuyện không như ý. Gom lại có ba nhóm khác nhau về bản chất:

| Nhóm | Ví dụ | Ai có lỗi | Phản ứng hợp lý |
|---|---|---|---|
| Tình huống dự kiến được | Người dùng nhập email sai định dạng, file cấu hình không tồn tại, database mất kết nối, API bên ngoài trả 500 | Không ai cả, thế giới bên ngoài vốn vậy | Xử lý: báo lại cho người dùng, thử lại, dùng giá trị dự phòng |
| Bug trong code | Truyền chuỗi vào hàm cần `int`, gọi method trên `null`, chia cho 0, đọc key mảng không tồn tại | Lập trình viên | Sửa code. Lúc chạy thì ghi log đầy đủ để biết mà sửa |
| Sự cố không cứu được | Hết bộ nhớ (`memory_limit`), chạy quá thời gian cho phép (`max_execution_time`) | Thường là thiết kế hoặc dữ liệu quá lớn | Process dừng. Chỉ còn kịp ghi log |

Một ngôn ngữ cần cho lập trình viên cách để: (1) báo hiệu "có chuyện" từ chỗ phát hiện, (2) xử lý nó
ở chỗ có đủ thông tin để quyết định, (3) không để chuyện nào trôi qua im lặng. PHP làm việc này bằng
hai cơ chế ra đời ở hai thời kỳ khác nhau, và ngày nay vẫn sống chung.

### 1.2 Cơ chế thứ nhất: error reporting (thông báo có mức độ)

Đây là cơ chế có từ những phiên bản PHP đầu tiên. Khi engine hoặc một hàm có sẵn gặp vấn đề, nó *phát*
(*raise*) một thông báo lỗi. Mỗi thông báo có một *mức* (*level*, manual gọi là *error type*) như
`E_WARNING`, `E_NOTICE`, `E_DEPRECATED`, `E_ERROR`. Rồi:

- Thông báo được in ra màn hình và/hoặc ghi vào log, tuỳ cấu hình (mục 9).
- Nếu mức đó không nghiêm trọng (warning, notice, deprecated), script **chạy tiếp** từ câu lệnh sau.
- Nếu mức đó là *fatal* (chết người), script **dừng ngay**.

Code của bạn không "bắt" được thông báo theo kiểu `try/catch`. Thông báo không phải object, không đi
ngược lên hàm gọi, nó chỉ được phát ra rồi xử lý tại chỗ theo cấu hình.

### 1.3 Cơ chế thứ hai: exception (ném và bắt)

PHP 5 (2004) thêm *exception*. Exception là một object mô tả chuyện đã xảy ra. Chỗ phát hiện vấn đề
*ném* (*throw*) object đó; PHP dừng đoạn code đang chạy và đi ngược lên các hàm gọi để tìm một khối
`catch` chịu *bắt* (*catch*) nó. Không ai bắt thì script dừng với fatal error "Uncaught ...".

Từ PHP 7, chính engine cũng dùng exception: phần lớn những lỗi trước đây là fatal error (gọi hàm không
tồn tại, gọi method trên `null`, truyền sai kiểu) chuyển thành object thuộc class `Error` được ném ra
(RFC *Exceptions in the engine*). PHP 8 đi tiếp: nhiều hàm có sẵn trước đây chỉ phát warning rồi trả
`null` khi nhận đối số sai, nay ném `TypeError` hoặc `ValueError`.

### 1.4 Nhìn tận mắt cả bốn loại

```php
<?php
declare(strict_types=1);

// 1) Warning: PHP báo rồi chạy tiếp
$gio = ['tao' => 3];
$soCam = $gio['cam'];
var_dump($soCam);
echo "Vẫn chạy tiếp sau warning\n";

// 2) Exception: code của bạn chủ động ném, và có chỗ bắt
function rutTien(int $soDu, int $soTien): int
{
    if ($soTien > $soDu) {
        throw new RuntimeException("Không đủ tiền: còn $soDu, cần $soTien");
    }
    return $soDu - $soTien;
}

try {
    rutTien(100, 500);
    echo "Dòng này không chạy\n";
} catch (RuntimeException $e) {
    echo "Bắt được: ", $e->getMessage(), "\n";
}

// 3) Error: engine phát hiện code sai và tự ném
try {
    rutTien(100, '50');
} catch (TypeError $e) {
    echo "Bắt được TypeError: ", $e->getMessage(), "\n";
}

// 4) Exception không ai bắt: thành fatal error, script dừng
rutTien(10, 20);
echo "Không bao giờ in dòng này\n";
```

Output:

```
Warning: Undefined array key "cam" in .../s1a.php on line 6
NULL
Vẫn chạy tiếp sau warning
Bắt được: Không đủ tiền: còn 100, cần 500
Bắt được TypeError: rutTien(): Argument #2 ($soTien) must be of type int, string given, called in .../s1a.php on line 28

Fatal error: Uncaught RuntimeException: Không đủ tiền: còn 10, cần 20 in .../s1a.php:14
Stack trace:
#0 .../s1a.php(34): rutTien(10, 20)
#1 {main}
  thrown in .../s1a.php on line 14
```

Đọc lại từng phần:

1. Đọc key không tồn tại: PHP phát `Warning`, coi giá trị là `null` rồi chạy tiếp. Không có
   exception nào cả.
2. `throw new RuntimeException(...)`: hàm `rutTien` dừng ngay ở dòng `throw`, dòng `echo "Dòng này
   không chạy"` bị bỏ qua, quyền điều khiển nhảy vào khối `catch`.
3. Truyền `'50'` (chuỗi) cho tham số `int` khi bật `strict_types`: engine ném `TypeError`, một object
   giống hệt exception về cách bắt.
4. Không có `try/catch` bao quanh: exception đi lên tới ngoài cùng, PHP in `Fatal error: Uncaught ...`
   kèm *stack trace* (danh sách các lời gọi hàm đang dở dang lúc ném) rồi dừng.

### 1.5 Bảng phân loại cần nhớ suốt chương

| Loại | Ví dụ | Là object? | Script có dừng? | Bắt bằng `catch`? | Mục |
|---|---|---|---|---|---|
| `Exception` (và class con) | `RuntimeException`, `PDOException`, `JsonException` | Có | Chỉ khi không ai bắt | Có | 2 đến 7 |
| `Error` (và class con) | `TypeError`, `DivisionByZeroError`, `Error: Call to undefined function` | Có | Chỉ khi không ai bắt | Có, nhưng `catch (Exception)` không bắt được | 4 |
| Warning, notice, deprecated | `Undefined array key`, `Undefined variable`, hàm deprecated | Không | Không, chạy tiếp | Không (trừ khi có error handler đổi thành exception) | 8, 10 |
| Fatal error | Hết bộ nhớ, quá `max_execution_time` | Không | Có, ngay lập tức | Không. Chỉ quan sát được bằng shutdown function | 12 |

Chữ "error" trong PHP vì vậy mang ba nghĩa, dễ lẫn:

- *error* nói chung: mọi thông báo của cơ chế error reporting (warning cũng là một "error" theo nghĩa
  này, nên hàm `set_error_handler` nhận cả warning).
- `Error` viết hoa: class gốc của nhánh lỗi engine, là một object ném được.
- *fatal error*: thông báo mức fatal, không bắt được, làm script dừng.

Khi đọc tài liệu, nhìn ngữ cảnh để biết đang nói nghĩa nào.

### 1.6 Đối chiếu với Java và Go

| | PHP | Java | Go |
|---|---|---|---|
| Báo lỗi chính | Exception | Exception | Giá trị `error` trả về cùng kết quả |
| Lỗi do code sai | `Error` (`TypeError`...) | Unchecked exception (`NullPointerException`...) | `panic` (ví dụ truy cập ngoài slice) |
| Bắt buộc khai báo/bắt exception (*checked exception*) | Không có | Có (`throws`) | Không áp dụng |
| Cảnh báo "chạy tiếp" | Warning, notice, deprecated | Không có cơ chế tương đương ở runtime | Không có |

PHP gần Java nhất: cũng có `Throwable` chia hai nhánh `Exception` và `Error`. Khác biệt lớn là PHP không
có *checked exception*: Java bắt bạn khai báo `throws IOException` hoặc phải bắt nó, nếu không thì không
biên dịch được; PHP không kiểm gì cả, mọi exception giống *unchecked exception* của Java. Go thì không
dùng exception cho lỗi thông thường: hàm trả thêm một giá trị `error` và người gọi kiểm `if err != nil`
ngay sau mỗi lời gọi. Cơ chế "warning rồi chạy tiếp" là đặc sản của PHP, và cũng là nguồn của nhiều bug
lặng lẽ, nên phần lớn chương này xoay quanh việc thuần hoá nó.

## 2. Exception cơ bản: `throw`, `try`, `catch`

### 2.1 Ném một exception

Cú pháp:

```php
throw new RuntimeException('Mô tả chuyện gì đã xảy ra');
```

Hai việc diễn ra trong một dòng: `new RuntimeException(...)` tạo một object bình thường (giống mọi
`new` khác), rồi `throw` ném object đó. Constructor của `Exception` (và mọi class con có sẵn) nhận ba
tham số, đều không bắt buộc:

```php
public function __construct(string $message = "", int $code = 0, ?Throwable $previous = null)
```

- `$message`: câu mô tả cho người đọc log. Viết đủ ngữ cảnh: "Không tìm thấy đơn hàng 1234" tốt hơn
  "Not found".
- `$code`: một số nguyên tuỳ ý. Ít dùng trong code ứng dụng; một số extension dùng nó để mang mã lỗi
  gốc (ví dụ mã lỗi của thư viện bên dưới).
- `$previous`: exception gốc gây ra exception này (mục 7).

Ngay khi gặp `throw`, PHP dừng thực thi tại đó. Các dòng phía sau trong cùng khối không chạy.

### 2.2 Bắt bằng `try`/`catch`

```php
try {
    // code có thể ném exception
} catch (KieuException $e) {
    // chạy khi có exception thuộc KieuException (hoặc class con) bay ra từ khối try
}
// chạy tiếp ở đây
```

Luồng chạy:

- Khối `try` chạy hết mà không có exception: bỏ qua mọi `catch`, chạy tiếp sau chúng.
- Có exception bay ra từ `try` (ném trực tiếp trong `try`, hoặc ném từ một hàm được gọi trong `try`, sâu
  bao nhiêu tầng cũng được): phần còn lại của `try` bị bỏ qua, PHP tìm khối `catch` có kiểu khớp, chạy
  khối đó, rồi chạy tiếp sau chuỗi `catch`. Exception coi như đã được xử lý.
- Biến `$e` giữ object exception; sau khối `catch` nó vẫn còn trong scope (PHP không có block scope),
  nhưng đừng dựa vào điều đó.

Mỗi `try` phải đi kèm ít nhất một `catch` hoặc một `finally` (mục 3).

### 2.3 Exception đi ngược lên call stack

Khi hàm `c()` ném mà chính nó không có `catch` phù hợp, exception không dừng ở đó: nó "nổi lên"
(*bubble up*) hàm đã gọi `c()`, rồi hàm gọi hàm đó, cho tới khi gặp một `catch` khớp. Quá trình thoát
dần từng hàm này gọi là *stack unwinding* (tháo call stack).

```php
<?php
declare(strict_types=1);

function c(): void
{
    echo "c: bắt đầu\n";
    throw new RuntimeException('Hỏng ở c');
    echo "c: kết thúc\n";
}

function b(): void
{
    echo "b: bắt đầu\n";
    c();
    echo "b: kết thúc\n";
}

function a(): void
{
    echo "a: bắt đầu\n";
    try {
        b();
        echo "a: sau b()\n";
    } catch (RuntimeException $e) {
        echo "a: bắt được '", $e->getMessage(), "'\n";
    }
    echo "a: kết thúc\n";
}

a();
echo "main: kết thúc\n";
// in ra:
// a: bắt đầu
// b: bắt đầu
// c: bắt đầu
// a: bắt được 'Hỏng ở c'
// a: kết thúc
// main: kết thúc
```

Ba dòng "c: kết thúc", "b: kết thúc", "a: sau b()" không bao giờ in. Hình dung call stack lúc ném:

```
  call stack lúc throw            exception đi lên
  ┌──────────────────────┐
  │ c()   throw ──────── │──┐  c không có catch: thoát c
  ├──────────────────────┤  │
  │ b()   đang chờ c()   │◄─┘──┐  b không có catch: thoát b
  ├──────────────────────┤     │
  │ a()   try { b() }    │◄────┘  a có catch (RuntimeException): DỪNG, chạy catch
  ├──────────────────────┤
  │ {main} đang chờ a()  │      main không hề biết có exception
  └──────────────────────┘
```

Đây là điểm mạnh nhất của exception so với "trả mã lỗi": `b()` không cần viết dòng nào để chuyển lỗi
từ `c()` lên `a()`. Chỗ phát hiện lỗi (`c`) và chỗ quyết định xử lý thế nào (`a`) có thể cách nhau nhiều
tầng. So sánh với Go, nơi `b` phải viết `if err != nil { return err }` sau lời gọi `c()`.

### 2.4 Không ai bắt: "Uncaught"

Nếu exception nổi tới tận phạm vi ngoài cùng (`{main}`, tức code nằm ngoài mọi hàm) mà không gặp `catch`
nào khớp, PHP gọi *exception handler toàn cục* nếu bạn đã đăng ký (mục 11). Nếu không có, exception biến
thành fatal error và script dừng. Bạn đã thấy output này ở mục 1.4:

```
Fatal error: Uncaught RuntimeException: Không đủ tiền: còn 10, cần 20 in .../s1a.php:14
Stack trace:
#0 .../s1a.php(34): rutTien(10, 20)
#1 {main}
  thrown in .../s1a.php on line 14
```

Cách đọc:

- `Uncaught RuntimeException`: class của exception. `Không đủ tiền...`: message.
- `in .../s1a.php:14`: nơi exception được **tạo** (dòng có `new`, xem mục 2.8).
- `Stack trace`: đọc từ trên xuống là đi từ chỗ gần lỗi nhất ra ngoài. Dòng `#0 .../s1a.php(34):
  rutTien(10, 20)` nghĩa là: tại dòng 34, có lời gọi `rutTien(10, 20)`, và exception bay ra từ bên trong
  lời gọi đó. `{main}` là code cấp ngoài cùng của file.

Ở chế độ CLI, script chết vì fatal error kết thúc với mã thoát (*exit code*) 255 thay vì 0, nhờ vậy
cron job hay CI biết là đã có lỗi.

### 2.5 Nhiều khối `catch` và thứ tự của chúng

Một `try` có thể đi với nhiều `catch` để xử lý mỗi loại một kiểu:

```php
<?php
declare(strict_types=1);

function docCauHinh(string $tenFile): array
{
    if (!is_file($tenFile)) {
        throw new InvalidArgumentException("Không thấy file $tenFile");
    }
    $json = file_get_contents($tenFile);
    return json_decode($json, true, flags: JSON_THROW_ON_ERROR);
}

foreach (['/khong/co.json', __FILE__] as $f) {     // __FILE__: chính file PHP này, không phải JSON
    try {
        docCauHinh($f);
    } catch (InvalidArgumentException $e) {
        echo "Sai đầu vào: ", $e->getMessage(), "\n";
    } catch (JsonException $e) {
        echo "JSON hỏng: ", $e->getMessage(), "\n";
    }
}
// in ra:
// Sai đầu vào: Không thấy file /khong/co.json
// JSON hỏng: Syntax error
```

PHP xét các khối `catch` theo thứ tự từ trên xuống, và khối đầu tiên có kiểu khớp được chạy. "Khớp"
nghĩa là `$exception instanceof KieuTrongCatch`, tức là đúng class đó hoặc class con của nó. Vì vậy
một `catch` kiểu cha đặt trước sẽ "nuốt" luôn các kiểu con đặt sau:

```php
<?php
declare(strict_types=1);

try {
    throw new InvalidArgumentException('x');
} catch (LogicException $e) {
    echo "Vào LogicException vì InvalidArgumentException là con của nó\n";
} catch (InvalidArgumentException $e) {
    echo "Không bao giờ tới đây\n";
}
// in ra: Vào LogicException vì InvalidArgumentException là con của nó
```

Quy tắc: kiểu cụ thể đặt trước, kiểu chung đặt sau. ⚠️ PHP không cảnh báo khi một `catch` không bao giờ
tới được (Java thì báo lỗi biên dịch), nên sai thứ tự sẽ không ai nhắc bạn.

### 2.6 Multi-catch (7.1) và catch không cần biến (8.0)

Khi vài loại exception cụ thể được xử lý giống nhau (mà bạn không muốn bắt cả class cha chung của chúng), gộp chúng bằng dấu `|` thay vì
chép cùng một khối `catch` nhiều lần:

```php
<?php
declare(strict_types=1);

function parseTuoi(string $s): int
{
    $n = filter_var($s, FILTER_VALIDATE_INT);
    if ($n === false) {
        throw new InvalidArgumentException("'$s' không phải số nguyên");
    }
    if ($n < 0 || $n > 150) {
        throw new OutOfRangeException("Tuổi $n ngoài khoảng 0..150");
    }
    return $n;
}

foreach (['30', 'abc', '200'] as $input) {
    try {
        $tuoi = parseTuoi($input);
        echo "Tuổi: $tuoi\n";
    } catch (InvalidArgumentException | OutOfRangeException $e) {
        echo get_class($e), ": ", $e->getMessage(), "\n";
    }
}
// in ra:
// Tuổi: 30
// InvalidArgumentException: 'abc' không phải số nguyên
// OutOfRangeException: Tuổi 200 ngoài khoảng 0..150
```

Từ PHP 8.0, nếu khối `catch` không cần đọc object exception, bỏ luôn tên biến:

```php
function coPhaiSoNguyen(string $s): bool
{
    try {
        parseTuoi($s);
        return true;
    } catch (InvalidArgumentException) {      // không có $e
        return false;
    }
}

var_dump(coPhaiSoNguyen('12'), coPhaiSoNguyen('x'));
// in ra:
// bool(true)
// bool(false)
```

Viết không có biến còn là một tín hiệu cho người đọc: "tôi cố ý bỏ qua chi tiết lỗi ở đây".

### 2.7 Ném lại (rethrow)

Trong `catch`, bạn có thể làm vài việc (dọn dẹp, ghi thêm ngữ cảnh) rồi ném lại chính exception đó cho
tầng trên xử lý tiếp:

```php
<?php
declare(strict_types=1);

function ghiFile(string $path, string $noiDung): void
{
    throw new RuntimeException("Ổ đĩa đầy khi ghi $path");
}

function luuBaoCao(): void
{
    try {
        ghiFile('/tmp/bao-cao.txt', '...');
    } catch (RuntimeException $e) {
        echo "luuBaoCao: dọn file tạm rồi ném tiếp\n";
        throw $e;          // ném lại chính object đó
    }
}

try {
    luuBaoCao();
} catch (RuntimeException $e) {
    echo "main: ", $e->getMessage(), " (dòng ", $e->getLine(), ")\n";
}
// in ra:
// luuBaoCao: dọn file tạm rồi ném tiếp
// main: Ổ đĩa đầy khi ghi /tmp/bao-cao.txt (dòng 6)
```

`throw $e` không tạo object mới, nên dòng, file và stack trace vẫn là của nơi tạo ban đầu (dòng 6), thông
tin gốc không mất. Nếu bạn muốn đổi sang một exception khác có ý nghĩa với tầng trên, hãy tạo exception
mới và truyền `$e` làm `previous` (mục 7), đừng vứt `$e` đi.

### 2.8 Bên trong một object exception

Mọi exception (và mọi `Error`) đều có các method sau, khai báo trong interface `Throwable`:

| Method | Trả về |
|---|---|
| `getMessage()` | Message truyền vào constructor |
| `getCode()` | Code truyền vào constructor (mặc định `0`) |
| `getFile()`, `getLine()` | File và dòng nơi object **được tạo** |
| `getTrace()` | Stack trace dạng mảng, mỗi phần tử là một frame (`file`, `line`, `function`, `class`, `args`...) |
| `getTraceAsString()` | Stack trace dạng chuỗi như trong thông báo lỗi |
| `getPrevious()` | Exception gốc (mục 7), hoặc `null` |
| `__toString()` | Chuỗi đầy đủ: class, message, file:dòng, stack trace |

Trong class `Exception`, các method `get...()` đều khai báo `final`: class con không override được. Muốn
tuỳ biến message thì truyền message khác vào `parent::__construct()` (mục 6).

⚠️ `getFile()`/`getLine()` là nơi gọi `new`, **không phải** nơi `throw`. Thường hai chỗ là một dòng nên
không ai để ý, cho tới khi bạn tạo exception ở một hàm và ném ở hàm khác:

```php
<?php
declare(strict_types=1);

function taoLoi(): RuntimeException
{
    return new RuntimeException('tạo ở dòng 6');
}

function nemLoi(): void
{
    $e = taoLoi();
    throw $e;               // dòng 12
}

try {
    nemLoi();
} catch (RuntimeException $e) {
    echo "getLine(): ", $e->getLine(), "\n";
    echo $e->getTraceAsString(), "\n";
}
// in ra:
// getLine(): 6
// #0 .../s2c.php(11): taoLoi()
// #1 .../s2c.php(16): nemLoi()
// #2 {main}
```

Trace cũng là trace lúc tạo: nó có `taoLoi()` (đã chạy xong từ lâu) và không có dòng 12. Đây là lý do
các "factory" tạo exception (mục 6.2) vẫn ổn: trace chỉ dài thêm một frame, còn `throw` nằm ngay ở nơi
gọi factory.

Mỗi frame trong `getTrace()` mặc định chứa cả đối số `args` của lời gọi hàm. Đối số có thể là mật khẩu,
token, dữ liệu cá nhân, nên `php.ini-production` đặt `zend.exception_ignore_args = On` để bỏ đối số khỏi
trace (mặc định của PHP và `php.ini-development` là `Off`). Khi đó trace in `rutTien()` thay vì
`rutTien(10, 20)`. Với tham số nhạy cảm cụ thể, đánh dấu bằng attribute `#[\SensitiveParameter]` (8.2,
xem [Chương 10](10-oop-nang-cao.md) mục 9.4) để giá trị của nó luôn bị che trong trace.

### 2.9 Chỉ ném được `Throwable`, và bẫy tên class trong `catch`

Thứ được ném phải là object implement interface `Throwable`. Ném thứ khác là chính một `Error`:

```php
<?php
declare(strict_types=1);

try {
    throw new stdClass();
} catch (Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Cannot throw objects that do not implement Throwable
}

try {
    $x = 'chuỗi';
    throw $x;
} catch (Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Can only throw objects
}
```

Bạn cũng không thể tự `implements Throwable`:

```php
<?php
declare(strict_types=1);

class A implements Throwable {}
// Fatal error: Class A cannot implement interface Throwable, extend Exception or Error instead in ... on line 4
// Stack trace:
// #0 {main}
```

(Hai dòng `Stack trace` cuối chỉ có từ PHP 8.5, mục 12.4.)

Muốn có class exception riêng thì `extends Exception` (hoặc một class con của nó, mục 6).

⚠️ Ngược lại, tên class trong `catch` **không được kiểm tra**. Viết `catch (KhongTonTaiException $e)`
không báo lỗi gì, khối đó đơn giản là không bao giờ khớp. Bẫy kinh điển nằm ở namespace
([Chương 11](11-namespace-composer.md)):

```php
<?php
declare(strict_types=1);

namespace App\Services;

function lamViec(): void
{
    throw new \RuntimeException('Hỏng');
}

try {
    lamViec();
} catch (Exception $e) {          // PHP hiểu là App\Services\Exception, một class không tồn tại
    echo "Bắt được\n";
}
// Fatal error: Uncaught RuntimeException: Hỏng in .../s2f.php:8
```

Trong file có `namespace`, `Exception` không có dấu `\` đầu được phân giải thành
`App\Services\Exception`. Không có class nào tên đó, nên `catch` không bao giờ khớp, và cũng không có
cảnh báo nào. Sửa bằng `catch (\Exception $e)` hoặc thêm `use Exception;` ở đầu file. Công cụ phân tích
tĩnh như PHPStan ([Chương 21](21-chat-luong-code.md)) bắt được lỗi này.

## 3. `finally`: đoạn code luôn chạy

### 3.1 Cú pháp và ba con đường

Khối `finally` đặt sau các `catch` (hoặc thay cho chúng). Code trong `finally` chạy sau `try` và
`catch`, bất kể khối `try` kết thúc theo cách nào:

```php
<?php
declare(strict_types=1);

function thu(string $cach): string
{
    try {
        echo "  try ($cach)\n";
        if ($cach === 'return') {
            return 'giá trị từ try';
        }
        if ($cach === 'throw') {
            throw new RuntimeException('lỗi từ try');
        }
        echo "  try chạy hết\n";
    } catch (RuntimeException $e) {
        echo "  catch: ", $e->getMessage(), "\n";
        return 'giá trị từ catch';
    } finally {
        echo "  finally\n";
    }
    return 'giá trị cuối hàm';
}

foreach (['binh-thuong', 'return', 'throw'] as $cach) {
    echo $cach, ":\n";
    $kq = thu($cach);
    echo "  => $kq\n";
}
// in ra:
// binh-thuong:
//   try (binh-thuong)
//   try chạy hết
//   finally
//   => giá trị cuối hàm
// return:
//   try (return)
//   finally
//   => giá trị từ try
// throw:
//   try (throw)
//   catch: lỗi từ try
//   finally
//   => giá trị từ catch
```

Ba con đường: chạy hết `try`; `return` sớm từ `try` (hoặc `catch`); exception bay ra (dù có `catch` bắt
hay không). Cả ba đều đi qua `finally`. Khi exception không có `catch` nào khớp ở hàm hiện tại, `finally`
vẫn chạy trước, rồi exception mới tiếp tục nổi lên hàm gọi.

### 3.2 Dùng `finally` để trả tài nguyên

Mục đích chính của `finally`: tài nguyên mở ra thì phải đóng lại, dù đường đi có suôn sẻ hay không. Tài
nguyên ở đây là file đang mở, lock đang giữ, kết nối mượn từ pool, file tạm, cờ "đang xử lý"...

```php
<?php
declare(strict_types=1);

function demDong(string $path): int
{
    $f = fopen($path, 'r');
    if ($f === false) {
        throw new RuntimeException("Không mở được $path");
    }
    try {
        $n = 0;
        while (($line = fgets($f)) !== false) {
            if (str_contains($line, 'HỎNG')) {
                throw new UnexpectedValueException("Dòng " . ($n + 1) . " hỏng");
            }
            $n++;
        }
        return $n;
    } finally {
        fclose($f);
        echo "Đã đóng file\n";
    }
}

$tmp = __DIR__ . '/demo.txt';
file_put_contents($tmp, "a\nb\nc\n");
echo demDong($tmp), " dòng\n";

file_put_contents($tmp, "a\nHỎNG\nc\n");
try {
    demDong($tmp);
} catch (UnexpectedValueException $e) {
    echo "Lỗi: ", $e->getMessage(), "\n";
}
unlink($tmp);
// in ra:
// Đã đóng file
// 3 dòng
// Đã đóng file
// Lỗi: Dòng 2 hỏng
```

Để ý cấu trúc: mở tài nguyên trước `try`, đóng trong `finally`. Nếu `fopen` thất bại thì chưa có gì
để đóng, nên nó nằm ngoài `try`.

Mẫu giống hệt nhưng dùng `catch` + ném lại thay vì `finally` là transaction database: chỉ rollback khi có
lỗi, còn đường suôn sẻ thì commit.

```php
<?php
declare(strict_types=1);

$pdo = new PDO('sqlite::memory:');
$pdo->exec('CREATE TABLE tai_khoan (id INTEGER PRIMARY KEY, so_du INTEGER NOT NULL CHECK (so_du >= 0))');
$pdo->exec('INSERT INTO tai_khoan VALUES (1, 100), (2, 0)');

function chuyenTien(PDO $pdo, int $tu, int $den, int $soTien): void
{
    $pdo->beginTransaction();
    try {
        $pdo->prepare('UPDATE tai_khoan SET so_du = so_du + ? WHERE id = ?')->execute([$soTien, $den]);
        $pdo->prepare('UPDATE tai_khoan SET so_du = so_du - ? WHERE id = ?')->execute([$soTien, $tu]);
        $pdo->commit();
    } catch (Throwable $e) {
        $pdo->rollBack();     // hoàn tác cả lệnh UPDATE thứ nhất
        throw $e;             // rồi báo lỗi lên trên, không nuốt
    }
}

try {
    chuyenTien($pdo, 1, 2, 500);
} catch (PDOException $e) {
    echo "Chuyển thất bại: ", $e->getMessage(), "\n";
}
print_r($pdo->query('SELECT id, so_du FROM tai_khoan')->fetchAll(PDO::FETCH_KEY_PAIR));
// in ra:
// Chuyển thất bại: SQLSTATE[23000]: Integrity constraint violation: 19 CHECK constraint failed: so_du >= 0
// Array
// (
//     [1] => 100
//     [2] => 0
// )
```

Ở đây bắt `Throwable` (mục 4) là đúng: bất kể lỗi gì, kể cả `TypeError` do bug, transaction cũng phải
được rollback; và vì ném lại ngay nên không nuốt mất lỗi nào. Chi tiết về PDO và transaction ở
[Chương 16](16-php-va-database.md); Laravel gói mẫu này trong `DB::transaction()`
([Chương 27](27-laravel-database-eloquent.md)).

Đối chiếu: Java có *try-with-resources* tự đóng tài nguyên, Go có `defer f.Close()`. PHP không có cú pháp
tương đương, nên `finally` là công cụ chính. (Destructor `__destruct` cũng hay được dùng để dọn dẹp, nhưng
thời điểm nó chạy phụ thuộc vào lúc object hết tham chiếu, khó đoán hơn, xem
[Chương 09](09-oop-co-ban.md).)

### 3.3 `finally` và `return`: hai luật cần nhớ

Manual mô tả hai luật:

1. `return` trong `try` (hoặc `catch`) được **tính giá trị ngay** lúc gặp, nhưng chỉ thực sự trả về sau
   khi `finally` chạy xong. Thay đổi biến trong `finally` không làm đổi giá trị đã tính.
2. Nếu `finally` cũng có `return`, giá trị của `finally` thắng.

```php
<?php
declare(strict_types=1);

function demo(): int
{
    $x = 1;
    try {
        return $x;          // giá trị 1 được tính ngay tại đây
    } finally {
        $x = 2;             // không ảnh hưởng tới giá trị đã tính
        echo "finally: \$x = $x\n";
    }
}
var_dump(demo());
// in ra:
// finally: $x = 2
// int(1)
```

⚠️ Luật 2 có một hệ quả nguy hiểm: `return` trong `finally` **nuốt luôn exception** đang bay ra từ `try`,
không để lại dấu vết nào:

```php
<?php
declare(strict_types=1);

function charge(): string
{
    try {
        throw new RuntimeException('Cổng thanh toán timeout');
    } finally {
        return 'ok';        // exception ở trên biến mất
    }
}

var_dump(charge());
// in ra: string(2) "ok"
```

Người gọi nhận `'ok'` và tưởng thanh toán thành công. Quy tắc: **không `return` trong `finally`**.
`finally` chỉ để dọn dẹp. Với `break` và `continue`, PHP chặn từ lúc biên dịch nếu chúng nhảy ra khỏi
khối `finally` (`Fatal error: jump out of a finally block is disallowed`); vòng lặp nằm trọn bên trong
`finally` thì vẫn dùng `break` bình thường.

### 3.4 Exception trong cả `try` lẫn `finally`

Nếu `try` ném exception A, rồi trong lúc chạy `finally` lại ném exception B, thì B là exception bay ra
ngoài, còn A được gắn vào chuỗi `previous` của B (mục 7) nên không mất:

```php
<?php
declare(strict_types=1);

try {
    try {
        throw new RuntimeException('A: lỗi trong try');
    } finally {
        throw new LogicException('B: lỗi trong finally');
    }
} catch (Exception $e) {
    echo get_class($e), ": ", $e->getMessage(), "\n";
    $p = $e->getPrevious();
    echo "previous: ", get_class($p), ": ", $p->getMessage(), "\n";
}
// in ra:
// LogicException: B: lỗi trong finally
// previous: RuntimeException: A: lỗi trong try
```

Nếu bản thân B đã có `previous` riêng, A được nối vào **cuối** chuỗi của B (ví dụ 9 trong manual
*Exceptions* minh hoạ chuỗi bốn exception). Dù vậy, exception chính mà `catch` nhìn thấy là B, nên code
dọn dẹp trong `finally` nên viết sao cho ít khả năng ném nhất.

### 3.5 Khi nào `finally` không chạy

"Luôn chạy" có ngoại lệ. `finally` **không** chạy khi:

- Gọi `exit()` (hoặc `die()`) bên trong `try`. Script kết thúc ngay; các shutdown function (mục 12) và
  destructor vẫn chạy, nhưng `finally` thì không:

  ```php
  <?php
  declare(strict_types=1);

  function f(): void
  {
      try {
          echo "try\n";
          exit(0);
      } finally {
          echo "finally sau exit\n";      // không in
      }
  }

  register_shutdown_function(fn() => print("shutdown chạy\n"));
  f();
  // in ra:
  // try
  // shutdown chạy
  ```

- Script chết vì fatal error (hết bộ nhớ, quá thời gian chạy...). Fatal error không đi qua cơ chế
  exception nên không có gì để "unwind" (mục 12).
- Process bị giết từ bên ngoài (`kill -9`, container bị dừng).

Vì vậy đừng đặt những việc "bắt buộc phải xảy ra" (như ghi sổ cái tiền) chỉ trong `finally`. Với dữ
liệu quan trọng, dựa vào transaction của database: transaction chưa commit sẽ bị database rollback khi
kết nối đứt.

## 4. Cây `Throwable`: hai nhánh `Error` và `Exception`

### 4.1 Toàn cảnh

*Throwable* là interface gốc của mọi thứ ném được (có từ PHP 7, và từ 8.0 nó kế thừa `Stringable` nên
mọi exception đều ép được sang chuỗi). Bên dưới có đúng hai class gốc, và hai nhánh **không kế thừa
nhau**:

```text
Throwable (interface)
│
├── Error                              lỗi do engine phát hiện, thường là bug
│   ├── ArithmeticError                phép toán không thực hiện được
│   │   └── DivisionByZeroError        chia cho 0 bằng /, %, intdiv()
│   ├── AssertionError                 assert() thất bại
│   ├── CompileError                   một số lỗi biên dịch (7.3)
│   │   └── ParseError                 sai cú pháp khi eval() hoặc include
│   ├── TypeError                      sai kiểu
│   │   └── ArgumentCountError         sai số lượng đối số (7.1)
│   ├── ValueError                     đúng kiểu nhưng giá trị không hợp lệ (8.0)
│   ├── UnhandledMatchError            match không có nhánh nào khớp (8.0)
│   └── FiberError                     dùng Fiber sai trạng thái (8.1)
│
└── Exception                          tình huống ứng dụng dự kiến được
    ├── ErrorException                 bọc một warning/notice thành exception (mục 10)
    ├── JsonException                  json_encode/json_decode với JSON_THROW_ON_ERROR (7.3)
    ├── LogicException                 (SPL) lỗi logic: phải sửa code
    │   ├── BadFunctionCallException
    │   │   └── BadMethodCallException
    │   ├── DomainException
    │   ├── InvalidArgumentException
    │   ├── LengthException
    │   └── OutOfRangeException
    └── RuntimeException               (SPL) lỗi chỉ phát hiện được lúc chạy
        ├── OutOfBoundsException
        ├── OverflowException
        ├── RangeException
        ├── UnderflowException
        ├── UnexpectedValueException
        └── PDOException               lỗi database qua PDO
```

Cây trên chỉ gồm các class bạn gặp thường xuyên. Các extension còn thêm class riêng, ví dụ
`ReflectionException`, `Random\RandomException` (8.2), họ `DateMalformedStringException` (8.3) của
DateTime, `Filter\FilterFailedException` (8.5, khi dùng cờ `FILTER_THROW_ON_FAILURE`). Muốn xem đầy đủ
trên máy của bạn, chạy:

```php
<?php
declare(strict_types=1);

$con = [];
foreach (get_declared_classes() as $c) {
    if (is_subclass_of($c, Throwable::class)) {
        $con[get_parent_class($c)][] = $c;
    }
}

function inCay(string $c, array $con, int $muc = 0): void
{
    echo str_repeat('    ', $muc), $c, "\n";
    $ds = $con[$c] ?? [];
    sort($ds);
    foreach ($ds as $k) {
        inCay($k, $con, $muc + 1);
    }
}

inCay('Error', $con);
inCay('Exception', $con);
```

### 4.2 Nhánh `Error`: engine báo code của bạn sai

Object trong nhánh này thường do engine hoặc hàm có sẵn ném ra, khi code làm điều không thể làm. Chạy
đoạn sau để thấy từng loại:

```php
<?php
declare(strict_types=1);

final class Diem
{
    public function __construct(public readonly int $x) {}
}

function binhPhuong(int $n): int { return $n * $n; }
function tra(): int { return 'abc'; }

$thu = [
    'gọi hàm không tồn tại'      => fn() => khongCo(),
    'gọi method trên null'       => function () { $u = null; $u->tinh(); },
    'sửa property readonly'      => function () { $d = new Diem(1); $d->x = 2; },
    'hằng chưa định nghĩa'       => fn() => KHONG_CO_HANG,
    'sai kiểu tham số'           => fn() => binhPhuong('3'),
    'sai kiểu trả về'            => fn() => tra(),
    'hàm có sẵn nhận sai kiểu'   => fn() => strlen([]),
    'thiếu đối số'               => fn() => binhPhuong(),
    'thừa đối số cho hàm có sẵn' => fn() => strlen('a', 'b'),
    'đúng kiểu, sai giá trị'     => fn() => str_repeat('x', -1),
    'mảng rỗng cho max()'        => fn() => max([]),
    'chia lấy dư cho 0'          => fn() => 10 % 0,
    'chia cho 0'                 => fn() => 10 / 0,
    'intdiv tràn'                => fn() => intdiv(PHP_INT_MIN, -1),
    'dịch bit số âm'             => fn() => 1 << -1,
    'match không có nhánh'       => fn() => match (5) { 1 => 'một', 2 => 'hai' },
    'eval code sai cú pháp'      => fn() => eval('echo ;'),
];

foreach ($thu as $moTa => $f) {
    try {
        $f();
    } catch (Error $e) {
        echo $moTa, ' => ', get_class($e), ': ', $e->getMessage(), "\n";
    }
}
```

Output, gom lại thành bảng (đường dẫn file rút gọn):

| Tình huống | Class | Message |
|---|---|---|
| Gọi hàm không tồn tại | `Error` | `Call to undefined function khongCo()` |
| Gọi method trên `null` | `Error` | `Call to a member function tinh() on null` |
| Sửa property `readonly` | `Error` | `Cannot modify readonly property Diem::$x` |
| Hằng chưa định nghĩa | `Error` | `Undefined constant "KHONG_CO_HANG"` |
| Sai kiểu tham số | `TypeError` | `binhPhuong(): Argument #1 ($n) must be of type int, string given, called in ... on line 17` |
| Sai kiểu trả về | `TypeError` | `tra(): Return value must be of type int, string returned` |
| Hàm có sẵn nhận sai kiểu | `TypeError` | `strlen(): Argument #1 ($string) must be of type string, array given` |
| Thiếu đối số | `ArgumentCountError` | `Too few arguments to function binhPhuong(), 0 passed in ... on line 20 and exactly 1 expected` |
| Thừa đối số cho hàm có sẵn | `ArgumentCountError` | `strlen() expects exactly 1 argument, 2 given` |
| Đúng kiểu, sai giá trị | `ValueError` | `str_repeat(): Argument #2 ($times) must be greater than or equal to 0` |
| Mảng rỗng cho `max()` | `ValueError` | `max(): Argument #1 ($value) must contain at least one element` |
| `10 % 0` | `DivisionByZeroError` | `Modulo by zero` |
| `10 / 0` | `DivisionByZeroError` | `Division by zero` |
| `intdiv(PHP_INT_MIN, -1)` | `ArithmeticError` | `Division of PHP_INT_MIN by -1 is not an integer` |
| `1 << -1` | `ArithmeticError` | `Bit shift by negative number` |
| `match` không có nhánh khớp | `UnhandledMatchError` | `Unhandled match case 5` |
| `eval('echo ;')` | `ParseError` | `syntax error, unexpected token ";"` |

Vài điều đáng chú ý:

- `Error` "trơn" (không phải class con) là loại phổ biến nhất trong log: gọi method trên `null` gần như
  chắc chắn là bug "quên kiểm tra kết quả tìm kiếm có rỗng không".
- `TypeError` và `ValueError` từ hàm có sẵn được chuẩn hoá ở PHP 8.0. Trên PHP 7.x, file không bật
  `strict_types` gọi `strlen([])` chỉ nhận warning và giá trị `null`; còn `str_repeat('x', -1)` phát
  warning và trả `null` ở mọi chế độ. Từ 8.0 cả hai đều ném (RFC *Consistent type errors for internal
  functions* và việc thêm `ValueError`). Code cũ dựa vào giá trị `null` đó sẽ vỡ khi nâng cấp.
- Toán tử `/` chia cho 0 ném `DivisionByZeroError` từ 8.0; trước đó chỉ là warning và trả `INF`
  ([Chương 07](07-toan-tu-dieu-khien.md)). `fmod(10, 0)` vẫn trả `NAN`, không ném.
- `ValueError` cũng là thứ `BackedEnum::from()` ném khi giá trị không thuộc enum
  ([Chương 10](10-oop-nang-cao.md) mục 3.3).

`AssertionError` và `FiberError`:

```php
<?php
declare(strict_types=1);

function chia(int $a, int $b): int
{
    assert($b !== 0, 'b phải khác 0');
    return intdiv($a, $b);
}

try {
    chia(1, 0);
} catch (AssertionError $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
}
// in ra (khi zend.assertions = 1): AssertionError: b phải khác 0

$f = new Fiber(fn() => 1);
try {
    $f->resume();
} catch (FiberError $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
}
// in ra: FiberError: Cannot resume a fiber that is not suspended
```

⚠️ `assert()` phụ thuộc ini `zend.assertions`: `1` là sinh và chạy code assert (mặc định của PHP và
của `php.ini-development`), `0` là sinh code nhưng nhảy qua, `-1` là không sinh code luôn (giá trị trong
`php.ini-production`). Nghĩa là trên production, dòng `assert(...)` coi như không tồn tại. Manual nói rõ:
không dùng `assert()` để kiểm tra đầu vào; code phải chạy đúng cả khi assertion bị tắt. `assert()` chỉ để
"tự kiểm" giả định nội bộ trong lúc dev và test.

### 4.3 Nhánh `Exception`: tình huống dự kiến được

Mọi class trong nhánh này dành cho những chuyện có thể xảy ra dù code đúng, và có cách phản ứng hợp
lý. Bản thân engine hầu như không ném `Exception`; chúng đến từ extension (PDO, JSON, DateTime...),
từ thư viện, và từ code của bạn.

*SPL* (Standard PHP Library, [Chương 13](13-generator-iterator-spl.md)) cung cấp sẵn hai họ để bạn kế thừa
hoặc dùng trực tiếp. Mô tả lấy từ manual:

| Class | Manual mô tả | Ví dụ dùng |
|---|---|---|
| `LogicException` | Lỗi trong logic chương trình, "nên dẫn thẳng tới việc sửa code" | Gọi method khi object chưa cấu hình đủ |
| `BadFunctionCallException` | Callback trỏ tới hàm không tồn tại, hoặc thiếu đối số | |
| `BadMethodCallException` | Callback trỏ tới method không tồn tại, hoặc thiếu đối số | Ném trong `__call` khi tên method không hỗ trợ |
| `DomainException` | Giá trị không thuộc miền dữ liệu hợp lệ đã định nghĩa | Trạng thái đơn hàng không cho phép thao tác này |
| `InvalidArgumentException` | Đối số không như mong đợi | Email sai định dạng truyền vào constructor của `Email` |
| `LengthException` | Độ dài không hợp lệ | |
| `OutOfRangeException` | Yêu cầu một chỉ số không hợp lệ, loại lỗi "đáng lẽ phát hiện được lúc biên dịch" | Truy cập vị trí cố định ngoài mảng hằng |
| `RuntimeException` | Lỗi chỉ phát hiện được lúc chạy | Gọi API thất bại, file bị khoá |
| `OutOfBoundsException` | Giá trị không phải key hợp lệ, loại lỗi "không phát hiện được lúc biên dịch" | Key do người dùng gửi lên không có trong danh sách |
| `OverflowException` | Thêm phần tử vào container đã đầy | Hàng đợi có giới hạn bị đầy |
| `UnderflowException` | Thao tác không hợp lệ trên container rỗng, như lấy phần tử ra | `pop()` trên stack rỗng |
| `RangeException` | Lỗi miền giá trị lúc chạy, "phiên bản runtime của `DomainException`" | |
| `UnexpectedValueException` | Giá trị không thuộc tập giá trị mong đợi, thường là kết quả trả về từ hàm khác | Dịch vụ ngoài trả trạng thái lạ |

Ranh giới giữa các class này không sắc nét và cộng đồng dùng khá tự do. Hai class bạn sẽ dùng nhiều nhất
là `InvalidArgumentException` (đầu vào không hợp lệ) và `RuntimeException` (sự cố lúc chạy), và thường
dùng chúng làm class cha cho exception riêng của bạn (mục 6).

`ValueError` hay `InvalidArgumentException`? Cả hai đều nói "giá trị sai". Quy ước phổ biến: `ValueError`
và `TypeError` là của engine và hàm có sẵn; code ứng dụng và thư viện ném class trong nhánh `Exception`
(`InvalidArgumentException` hoặc class con của nó). Lý do thực tế: code xử lý lỗi nghiệp vụ thường
`catch (Exception)` hoặc `catch` một class cụ thể, và chẳng ai chờ đợi lỗi nghiệp vụ nằm trong nhánh
`Error`.

### 4.4 Vì sao `Error` không kế thừa `Exception`

Trước PHP 7, gọi hàm không tồn tại hay gọi method trên `null` là fatal error: script chết ngay, không
`catch` được, `finally` không chạy, không dọn dẹp được gì. PHP 7 (RFC *Exceptions in the engine*) đổi
phần lớn các lỗi đó thành exception để chương trình có cơ hội phản ứng.

Nhưng có một vấn đề tương thích: rất nhiều code PHP 5 viết `catch (Exception $e)` ở tầng ngoài cùng, với
giả định "fatal error thì chết, còn lại là `Exception`". Nếu lỗi engine kế thừa `Exception`, khối `catch`
đó đột nhiên bắt cả bug lập trình rồi chạy tiếp như không có gì (RFC gọi kiểu "bắt hết" này là *Pokemon
exception handling*). RFC *Exceptions in the engine* vì thế cho lỗi engine một nhánh riêng không nằm dưới
`Exception`, và RFC *Throwable Interface* chốt lại tên gọi: interface `Throwable` ở gốc, class `Error` cho
lỗi engine, cùng cấp với `Exception`. RFC *Throwable Interface* cũng khuyên: nói chung đừng bắt `Error`
ngoại trừ để ghi log hoặc dọn dẹp, vì nó báo hiệu code cần sửa chứ không phải tình huống để xử lý.

⚠️ Hệ quả quan trọng nhất của chương: `catch (Exception $e)` **không** bắt `TypeError`,
`ArgumentCountError`, `DivisionByZeroError`, hay `Error` "gọi method trên null".

```php
<?php
declare(strict_types=1);

function soLuong(int $n): int
{
    return $n;
}

try {
    soLuong('5');                    // strict_types=1 nên không tự ép kiểu: TypeError
} catch (Exception $e) {
    echo "Exception\n";              // KHÔNG vào đây
} catch (Throwable $e) {
    echo get_class($e), "\n";        // in ra: TypeError
}
```

### 4.5 Chọn kiểu nào trong `catch`

| Viết | Bắt được | Dùng khi |
|---|---|---|
| `catch (CuThe $e)` | Đúng loại đó và class con | Hầu hết mọi chỗ: bạn biết loại lỗi nào và biết phải làm gì với nó |
| `catch (Exception $e)` | Mọi exception nghiệp vụ, không có `Error` | Hiếm khi cần; thường là dấu hiệu bắt quá rộng |
| `catch (Throwable $e)` | Tất cả | Chỉ ở **ranh giới**: vòng lặp của worker xử lý job, tầng ngoài cùng của request, code dọn dẹp rồi ném lại (như rollback ở mục 3.2) |

Ví dụ ranh giới hợp lý cho `Throwable`: một worker xử lý 1000 job, một job hỏng vì bug không được kéo chết
999 job còn lại. Worker bắt `Throwable`, ghi log đầy đủ, đánh dấu job thất bại, chuyển sang job tiếp theo.
Nếu worker chỉ bắt `Exception`, một `TypeError` sẽ bay qua và giết cả process, và nếu không ai ghi log
thì "job chết im lặng". Queue worker của Laravel bắt `Throwable` ở chỗ này vì đúng lý do đó.

Đối chiếu Java: Java cũng có `Throwable` với hai nhánh `Exception` và `Error`, nhưng `Error` của Java là sự
cố của JVM (`OutOfMemoryError`, `StackOverflowError`), còn bug lập trình như `NullPointerException` lại
nằm trong `RuntimeException`, tức nhánh `Exception`. PHP thì ngược lại: bug lập trình nằm ở `Error`. Người
từ Java sang hay mặc định `catch (Exception)` là "bắt hết bug", trong PHP thì không phải vậy.

## 5. `throw` là biểu thức (PHP 8.0) và kiểu trả về `never`

### 5.1 Câu lệnh và biểu thức

Nhắc lại ([Chương 07](07-toan-tu-dieu-khien.md)): *biểu thức* (*expression*) là thứ có giá trị và đặt
được vào giữa các toán tử (`$a + 1`, `f()`, `$x ?? 'mặc định'`); *câu lệnh* (*statement*) là một bước
thực thi đứng riêng (`if`, `foreach`, `return`). Trước PHP 8.0, `throw` là câu lệnh, nên không đặt được ở
những chỗ chỉ nhận biểu thức: vế phải của `??`, thân arrow function, nhánh của `match`. RFC *throw
expression* (8.0) biến `throw` thành biểu thức, đặt được ở bất cứ đâu cần một biểu thức.

### 5.2 Các chỗ dùng thường gặp

```php
<?php
declare(strict_types=1);

final class NguoiDung
{
    public function __construct(public readonly int $id, public readonly string $ten) {}
}

$kho = [1 => new NguoiDung(1, 'An')];

function tim(array $kho, int $id): ?NguoiDung
{
    return $kho[$id] ?? null;
}

// 1) Vế phải của ??: "có thì lấy, không có thì là lỗi"
$u = tim($kho, 1) ?? throw new OutOfBoundsException('Không có người dùng 1');
echo $u->ten, "\n";                    // in ra: An

// 2) Thân arrow function (chỉ nhận một biểu thức)
$batBuoc = fn(?string $v): string => $v ?? throw new InvalidArgumentException('Thiếu giá trị');
echo $batBuoc('x'), "\n";              // in ra: x

// 3) Nhánh default của match
function phiVanChuyen(string $vung): int
{
    return match ($vung) {
        'HN', 'HCM' => 20_000,
        'tinh'      => 35_000,
        default     => throw new DomainException("Không giao tới vùng '$vung'"),
    };
}
echo phiVanChuyen('HN'), "\n";         // in ra: 20000

// 4) Vế phải của ?: (giá trị "rỗng" theo nghĩa falsy là lỗi)
$ten = trim('   ') ?: throw new LengthException('Tên rỗng');
// Fatal error: Uncaught LengthException: Tên rỗng in .../s5a.php:36
```

Mẫu 1 đặc biệt hữu ích: biến `$u` sau dòng đó chắc chắn có kiểu `NguoiDung`, không còn `null`, nên
các dòng phía sau không cần kiểm tra lại. Công cụ phân tích tĩnh cũng hiểu điều này.

Mẫu 3 nên so với hành vi mặc định của `match`: không có `default` thì giá trị lạ gây `UnhandledMatchError`
(một `Error`, mục 4.2), nghĩa là "bug". Viết `default => throw new DomainException(...)` là nói rõ
"giá trị này có thể xảy ra trong thực tế và là lỗi nghiệp vụ", kèm message có nghĩa.

### 5.3 Độ ưu tiên: mọi thứ sau `throw` thuộc về `throw`

RFC chọn cho `throw` độ ưu tiên thấp nhất có thể. Nghĩa là `throw` "ăn" toàn bộ biểu thức phía sau nó:

```php
throw $dieuKien ? new ForbiddenException() : new UnauthorizedException();
// được hiểu là: throw ($dieuKien ? new ForbiddenException() : new UnauthorizedException());

throw $e ?? new Exception();
// được hiểu là: throw ($e ?? new Exception());
```

Thường đó đúng là điều bạn muốn. Chỗ dễ sai là nối nhiều `throw` bằng toán tử logic:

```php
$a || throw new Exception('a sai') && $b || throw new Exception('b sai');
// được hiểu là: $a || (throw new Exception('a sai') && $b || (throw new Exception('b sai')));
```

Kết quả chạy thử: với `$a = true, $b = false`, dòng trên **không ném gì** (vế trái của `||` đầu tiên đã
đúng nên cả phần sau bị bỏ qua, kể cả việc kiểm `$b`); với `$a = false, $b = true`, nó ném
`Error: Can only throw objects` vì thứ được `throw` là kết quả `bool` của cả cụm `&&`/`||`; với
`$a = false, $b = false`, exception bay ra lại là `'b sai'` chứ không phải `'a sai'`. Muốn viết
kiểu đó thì phải tự thêm ngoặc. Tốt hơn: dùng `if` cho rõ ràng. Cũng đừng lạm dụng
`$x or throw ...` hay `$dieuKien && throw ...` (RFC cho phép nhưng chính tác giả gọi là "gây tranh cãi");
một câu `if` dễ đọc hơn nhiều.

### 5.4 Kiểu trả về `never` (8.1)

Một hàm luôn kết thúc bằng `throw` (hoặc `exit`) có thể khai báo kiểu trả về `never`. Đây là cam kết "hàm
này không bao giờ trả về bình thường":

```php
<?php
declare(strict_types=1);

function khongTimThay(string $thu): never
{
    throw new OutOfBoundsException("Không tìm thấy $thu");
}

function layGia(array $bangGia, string $ma): int
{
    if (!isset($bangGia[$ma])) {
        khongTimThay("mã $ma");
    }
    return $bangGia[$ma];
}

try {
    echo layGia(['A' => 10], 'A'), "\n";
    echo layGia(['A' => 10], 'B'), "\n";
} catch (OutOfBoundsException $e) {
    echo $e->getMessage(), "\n";
}
// in ra:
// 10
// Không tìm thấy mã B
```

Lợi ích: người đọc và công cụ phân tích tĩnh biết sau dòng `khongTimThay(...)` không còn gì chạy tiếp.
Nếu hàm `never` lỡ kết thúc bình thường, PHP ném `TypeError`:

```php
function sai(): never
{
    echo "quên ném\n";
}
sai();
// in ra: quên ném
// rồi: TypeError: sai(): never-returning function must not implicitly return
```

`never` khác `void`: `void` là "trả về nhưng không có giá trị", `never` là "không bao giờ trả về". Chi
tiết về các kiểu trả về ở [Chương 08](08-ham.md).

## 6. Tự định nghĩa exception

### 6.1 Khi nào cần class exception riêng

Dùng `RuntimeException` trơn cho mọi chuyện thì người gọi chỉ còn cách đọc message để phân biệt lỗi, mà
so sánh chuỗi message là cách làm rất mong manh. Tạo class riêng khi:

- Người gọi cần **phản ứng khác nhau** với lỗi này: "thẻ bị từ chối" thì báo khách đổi thẻ, "cổng thanh
  toán timeout" thì thử lại sau.
- Lỗi cần **mang theo dữ liệu** để xử lý: mã đơn hàng, số lượng còn trong kho, thời điểm được thử lại.
- Bạn viết một thư viện hoặc module và muốn người dùng bắt được "mọi lỗi của module này" bằng một kiểu.

Không cần class riêng khi lỗi không ai xử lý riêng, chỉ để ghi log: một `RuntimeException` hoặc
`LogicException` với message rõ ràng là đủ.

### 6.2 Viết một exception đầy đủ

```php
<?php
declare(strict_types=1);

namespace App\ThanhToan;

use RuntimeException;
use Throwable;

// Interface đánh dấu: mọi exception của module thanh toán
interface ThanhToanException extends Throwable {}

final class TheBiTuChoi extends RuntimeException implements ThanhToanException
{
    private function __construct(
        string $message,
        public readonly string $maDonHang,
        public readonly string $lyDo,
        ?Throwable $previous = null,
    ) {
        parent::__construct($message, 0, $previous);
    }

    public static function vi(string $maDonHang, string $lyDo, ?Throwable $previous = null): self
    {
        return new self("Thẻ bị từ chối cho đơn $maDonHang: $lyDo", $maDonHang, $lyDo, $previous);
    }
}

final class CongThanhToanLoi extends RuntimeException implements ThanhToanException {}

function thanhToan(string $maDon, int $soTien): void
{
    if ($soTien > 1_000_000) {
        throw TheBiTuChoi::vi($maDon, 'vượt hạn mức');
    }
    throw new CongThanhToanLoi('Cổng thanh toán không phản hồi sau 10 giây');
}

foreach ([2_000_000, 500] as $soTien) {
    try {
        thanhToan('DH-42', $soTien);
    } catch (TheBiTuChoi $e) {
        echo "Báo khách đổi thẻ. Đơn: {$e->maDonHang}, lý do: {$e->lyDo}\n";
    } catch (ThanhToanException $e) {
        echo "Lỗi thanh toán khác (", $e::class, "): ", $e->getMessage(), "\n";
    }
}
// in ra:
// Báo khách đổi thẻ. Đơn: DH-42, lý do: vượt hạn mức
// Lỗi thanh toán khác (App\ThanhToan\CongThanhToanLoi): Cổng thanh toán không phản hồi sau 10 giây
```

Từng quyết định trong ví dụ:

1. **Kế thừa `RuntimeException`**, không kế thừa `Exception` trực tiếp. Người gọi nào đã bắt
   `RuntimeException` vẫn bắt được, và tên class cha nói lên bản chất "sự cố lúc chạy". Lỗi do người gọi
   truyền sai thì kế thừa `InvalidArgumentException`; vi phạm quy tắc nghiệp vụ có thể dùng
   `DomainException`.
2. **Interface đánh dấu** (*marker interface*) `ThanhToanException extends Throwable`. Class không được
   `implements Throwable` trực tiếp (mục 2.9), nhưng một interface thì được phép kế thừa `Throwable`, và
   class nào implement interface đó vẫn phải `extends Exception` hoặc `Error`. Nhờ vậy các exception trong
   module có thể có class cha khác nhau (`RuntimeException`, `InvalidArgumentException`...) mà người dùng
   vẫn `catch (ThanhToanException $e)` một lần cho tất cả. Nhiều thư viện lớn làm đúng như vậy (Guzzle có
   `GuzzleException`, PSR-18 có `Psr\Http\Client\ClientExceptionInterface`).
3. **Property `readonly` mang dữ liệu.** Người bắt đọc `$e->maDonHang` thay vì tách chuỗi message.
4. **Named constructor** (`TheBiTuChoi::vi(...)`, một static method tạo object) gom việc soạn message vào
   một chỗ, chỗ ném chỉ còn một dòng dễ đọc. Constructor để `private` để mọi nơi đi qua factory.
5. **`final`**: không ai cần kế thừa exception lá; `final` ngăn cây exception phình ra ngoài ý muốn.
6. Luôn **cho phép truyền `$previous`** để nối chuỗi khi bọc một exception khác (mục 7).

### 6.3 Những luật của class `Exception` cần biết khi kế thừa

- Nếu viết constructor riêng, **gọi `parent::__construct(...)`**. Quên gọi thì message rỗng và code là 0
  (file và dòng vẫn đúng vì chúng được gán lúc tạo object, trước khi constructor của bạn chạy):

  ```php
  <?php
  declare(strict_types=1);

  class A extends Exception
  {
      public function __construct(public readonly int $x) {}   // quên parent::__construct
  }

  $a = new A(5);
  var_dump($a->getMessage(), $a->getCode());
  // in ra:
  // string(0) ""
  // int(0)
  ```

- Các method `getMessage()`, `getCode()`, `getFile()`, `getLine()`, `getTrace()`, `getPrevious()`,
  `getTraceAsString()` là `final`, không override được. `__toString()` thì override được.
- Muốn có message/code mặc định, khai báo lại property `protected $message` / `protected $code`. Không
  được thêm kiểu cho chúng, vì trong class `Exception` chúng không khai báo kiểu:

  ```php
  <?php
  declare(strict_types=1);

  class B extends RuntimeException
  {
      protected $message = 'Mặc định';
      protected $code = 42;
  }

  var_dump((new B())->getMessage(), (new B())->getCode(), (new B('khác'))->getMessage());
  // in ra:
  // string(13) "Mặc định"
  // int(42)
  // string(5) "khác"

  // Viết `protected string $message = 'x';` thì:
  // Fatal error: Type of C::$message must be omitted to match the parent definition in class Exception
  ```

- Exception không clone được: `clone $e` ném `Error: Trying to clone an uncloneable object of class
  RuntimeException`. Muốn "sửa" một exception thì tạo exception mới và nối bằng `previous`.

### 6.4 Thiết kế cây exception cho một dự án

Vài nguyên tắc thực tế:

- **Nông và theo nghiệp vụ**: `DonHangKhongTonTai`, `KhongDuTonKho`, `TheBiTuChoi`. Đừng dựng cây năm tầng
  `AppException → DomainException → OrderException → OrderStateException → ...`; không ai bắt ở tầng giữa.
- **Đặt tên theo chuyện đã xảy ra**, không theo nơi xảy ra: `KhongDuTonKho` tốt hơn `OrderServiceException`.
- **Message cho lập trình viên, không cho người dùng cuối.** Message sẽ vào log, có thể chứa mã đơn, tên
  bảng. Thông báo hiển thị cho người dùng nên được soạn riêng ở tầng giao diện (Laravel làm việc này ở
  exception handler, mục 14).
- ⚠️ **Không đưa bí mật vào message**: mật khẩu, token, số thẻ đầy đủ. Log thường được nhiều người đọc
  hơn database.

## 7. Nối exception: `previous` và `getPrevious()`

### 7.1 Vì sao phải nối

Tình huống điển hình: tầng database ném `PDOException` với message "Deadlock found when trying to get
lock". Tầng nghiệp vụ không muốn để lộ chi tiết PDO cho tầng trên, nên bắt lại và ném
`KhongLuuDuocDonHang`. Nếu chỉ ném exception mới, log chỉ còn "Không lưu được đơn 42", và người trực sự cố
lúc 3 giờ sáng không có cách nào biết nguyên nhân là deadlock. Giải pháp: truyền exception gốc vào tham số
`previous` của exception mới. Đây gọi là *exception chaining* (nối exception), có từ PHP 5.3.

### 7.2 Cách làm

```php
<?php
declare(strict_types=1);

final class KhongLuuDuocDonHang extends RuntimeException {}

function ghiVaoDb(int $maDon): void
{
    // giả lập lỗi ở tầng database
    throw new PDOException('SQLSTATE[40001]: Serialization failure: 1213 Deadlock found when trying to get lock');
}

function luuDonHang(int $maDon): void
{
    try {
        ghiVaoDb($maDon);
    } catch (PDOException $e) {
        throw new KhongLuuDuocDonHang("Không lưu được đơn $maDon", previous: $e);
    }
}

try {
    luuDonHang(42);
} catch (KhongLuuDuocDonHang $e) {
    // Duyệt cả chuỗi nguyên nhân
    $muc = 0;
    for ($x = $e; $x !== null; $x = $x->getPrevious()) {
        echo str_repeat('  ', $muc++), $x::class, ': ', $x->getMessage(), "\n";
    }
}
// in ra:
// KhongLuuDuocDonHang: Không lưu được đơn 42
//   PDOException: SQLSTATE[40001]: Serialization failure: 1213 Deadlock found when trying to get lock
```

`previous: $e` dùng named argument (8.0) để khỏi phải truyền `$code` ở giữa; viết theo vị trí thì là
`new KhongLuuDuocDonHang("...", 0, $e)`. `getPrevious()` trả exception gốc, hoặc `null` ở cuối chuỗi.

### 7.3 Đọc thông báo "Uncaught" của một chuỗi exception

Nếu chuỗi đó không ai bắt (thêm dòng `luuDonHang(43);` vào cuối file trên), PHP in toàn bộ chuỗi:

```
Fatal error: Uncaught PDOException: SQLSTATE[40001]: Serialization failure: 1213 Deadlock found when trying to get lock in .../s7a.php:9
Stack trace:
#0 .../s7a.php(15): ghiVaoDb(43)
#1 .../s7a.php(33): luuDonHang(43)
#2 {main}

Next KhongLuuDuocDonHang: Không lưu được đơn 43 in .../s7a.php:17
Stack trace:
#0 .../s7a.php(33): luuDonHang(43)
#1 {main}
  thrown in .../s7a.php on line 17
```

⚠️ Thứ tự ngược với trực giác: PHP in exception gốc (trong cùng) trước, rồi mỗi exception bọc ngoài
bắt đầu bằng chữ `Next`. Dòng `Uncaught PDOException` ở đầu không có nghĩa exception bay ra ngoài là
`PDOException`; exception thật sự bay ra là cái cuối cùng (`KhongLuuDuocDonHang`), và dòng `thrown in`
cuối cùng chỉ vị trí của nó. Chuỗi do `(string) $e` hay `$e->__toString()` trả về cũng theo thứ tự này.

### 7.4 Quy tắc

- Mỗi khi bắt một exception rồi ném một exception khác, luôn truyền `previous`. Đây là lỗi phổ biến
  nhất khi review code xử lý lỗi.
- Ném lại chính exception đó (`throw $e;`) thì không cần, vì không có gì bị mất.
- Logger tốt (Monolog, và do đó Laravel) ghi cả chuỗi `previous` vào log. Nếu bạn tự ghi log bằng
  `$e->getMessage()`, bạn chỉ có message của tầng ngoài cùng. Ghi `(string) $e` hoặc truyền cả object
  exception cho logger.

## 8. Warning, notice, deprecated: "lỗi" không phải exception

### 8.1 Các mức lỗi

Quay lại cơ chế thứ nhất ở mục 1.2. Mỗi thông báo có một mức, là một hằng số nguyên. Các hằng là các bit
khác nhau, nên có thể ghép bằng toán tử bit (`|`, `&`, `~`, [Chương 07](07-toan-tu-dieu-khien.md)) thành
một *bitmask* (mặt nạ bit) để nói "những mức nào".

| Hằng | Giá trị | Ý nghĩa | Script có dừng? |
|---|---|---|---|
| `E_ERROR` | 1 | Lỗi fatal lúc chạy (hết bộ nhớ, quá thời gian) | Có |
| `E_WARNING` | 2 | Cảnh báo lúc chạy | Không |
| `E_PARSE` | 4 | Lỗi cú pháp lúc biên dịch | Có |
| `E_NOTICE` | 8 | Thông báo: có thể là lỗi, cũng có thể là cố ý | Không |
| `E_CORE_ERROR` | 16 | Fatal lúc PHP khởi động, do chính core PHP phát | Có |
| `E_CORE_WARNING` | 32 | Cảnh báo lúc PHP khởi động | Không |
| `E_COMPILE_ERROR` | 64 | Fatal lúc biên dịch (ví dụ khai báo trùng hàm) | Có |
| `E_COMPILE_WARNING` | 128 | Cảnh báo lúc biên dịch | Không |
| `E_USER_ERROR` | 256 | Fatal do code gọi `trigger_error()`. Dùng nó với `trigger_error()` bị deprecated từ 8.4 | Có |
| `E_USER_WARNING` | 512 | Warning do `trigger_error()` | Không |
| `E_USER_NOTICE` | 1024 | Notice do `trigger_error()` | Không |
| `E_STRICT` | 2048 | Không còn dùng; hằng bị deprecated từ 8.4 | |
| `E_RECOVERABLE_ERROR` | 4096 | Di sản; manual ghi gần như không còn xảy ra | Có, nếu không có handler |
| `E_DEPRECATED` | 8192 | Tính năng sẽ bị bỏ ở bản sau | Không |
| `E_USER_DEPRECATED` | 16384 | Deprecated do `trigger_error()` | Không |
| `E_ALL` | 30719 | Tất cả các mức trên, trừ `E_STRICT` | |

`E_ALL` bằng 32767 trước PHP 8.4; giảm còn 30719 vì bit của `E_STRICT` (2048) bị bỏ khỏi `E_ALL`. Đây là
lý do luôn dùng **tên hằng** chứ đừng ghi số.

Trong code hằng ngày bạn gặp chủ yếu bốn loại: Warning, Notice, Deprecated (không dừng) và
Fatal error (dừng). Các mức `CORE_*`, `COMPILE_*` là của engine lúc khởi động và biên dịch.

### 8.2 Những thông báo bạn sẽ gặp nhiều nhất

```php
<?php
declare(strict_types=1);

$a = [1, 2];
echo $khongCo;                           // biến chưa định nghĩa
echo $a[5];                              // key không tồn tại
$o = new stdClass();
echo $o->ten;                            // property không tồn tại
$n = null;
echo $n->ten;                            // đọc property trên null
echo "Mảng: " . $a . "\n";               // mảng thành chuỗi
$s = file_get_contents('/khong/co.txt'); // hàm I/O thất bại
echo end(explode(',', 'x,y')), "\n";     // truyền giá trị cho tham số tham chiếu
echo "Vẫn chạy tới cuối\n";
```

Output:

```
Warning: Undefined variable $khongCo in .../s8a.php on line 5

Warning: Undefined array key 5 in .../s8a.php on line 6

Warning: Undefined property: stdClass::$ten in .../s8a.php on line 8

Warning: Attempt to read property "ten" on null in .../s8a.php on line 10

Warning: Array to string conversion in .../s8a.php on line 11
Mảng: Array

Warning: file_get_contents(/khong/co.txt): Failed to open stream: No such file or directory in .../s8a.php on line 12

Notice: Only variables should be passed by reference in .../s8a.php on line 13
y
Vẫn chạy tới cuối
```

Sáu warning và một notice, và chương trình chạy tới dòng cuối với một đống giá trị `null` và chuỗi
`"Array"` vô nghĩa. Đây là điều nguy hiểm của cơ chế cũ: bug không làm chương trình dừng, nó làm chương
trình chạy tiếp với **dữ liệu sai**. Một đơn hàng có thể được lưu với tổng tiền `0` vì `$gia['VND']` không
tồn tại.

Hàm I/O (`file_get_contents`, `fopen`, `mkdir`...) là trường hợp đặc biệt: chúng báo lỗi theo cả hai
cách cũ, vừa phát warning vừa trả `false`. Code phải kiểm `=== false`, và warning vẫn in ra (hoặc thành
exception nếu có error handler, mục 10).

Một thông báo `Deprecated` trông thế này:

```php
<?php
declare(strict_types=1);

function f(int $x = null): ?int { return $x; }
// Deprecated: f(): Implicitly marking parameter $x as nullable is deprecated, the explicit nullable type must be used instead in ... on line 4
```

Đây là deprecation của PHP 8.4: phải viết `?int $x = null`. Deprecation không làm gì hỏng hôm nay, nhưng
báo trước rằng bản PHP lớn tiếp theo có thể biến nó thành lỗi. Để ý rằng deprecation này phát ra **lúc
biên dịch** file, trước khi bất kỳ dòng nào chạy.

### 8.3 PHP 8 đã siết lại nhiều mức

RFC *Reclassifying engine warnings* (PHP 8.0) đánh giá lại mức của các thông báo cũ theo nguyên tắc "lỗi
lập trình thì nên là `Error`". Theo UPGRADING của 8.0:

- Nhiều notice thành warning: đọc biến chưa định nghĩa, đọc property chưa định nghĩa, đọc key mảng
  không tồn tại, đọc property trên thứ không phải object, mảng thành chuỗi...
- Nhiều warning thành `Error`: ghi property lên thứ không phải object (trước đây với `null` thì PHP
  tự tạo `stdClass`), dùng mảng hoặc object làm key mảng, ghi vào phần tử mảng của một giá trị scalar...
- `error_reporting` mặc định thành `E_ALL` (trước đó bỏ qua `E_NOTICE` và `E_DEPRECATED`).

Nguyên tắc chung của RFC: cái gì phụ thuộc dữ liệu lúc chạy (ví dụ key mảng đến từ input) thì giữ ở mức
warning, cái gì gần như chắc chắn là bug và gây mất dữ liệu thì thành `Error`. Đó là lý do đọc key không
tồn tại vẫn chỉ là warning. Chính vì nhiều thứ vẫn chỉ là warning, các framework cài error handler để biến
chúng thành exception (mục 10).

### 8.4 Tự phát thông báo: `trigger_error()`

Code của bạn cũng phát được thông báo, với các mức `E_USER_*`:

```php
<?php
declare(strict_types=1);

/** @deprecated dùng tinhTongMoi() */
function tinhTongCu(array $xs): int
{
    trigger_error('tinhTongCu() đã lỗi thời, hãy dùng tinhTongMoi()', E_USER_DEPRECATED);
    return array_sum($xs);
}

echo tinhTongCu([1, 2, 3]), "\n";
trigger_error('Cấu hình cache thiếu, dùng mặc định', E_USER_WARNING);
trigger_error('Chỉ để thông báo');          // mặc định là E_USER_NOTICE
echo "chạy tiếp\n";
```

Output:

```
Deprecated: tinhTongCu() đã lỗi thời, hãy dùng tinhTongMoi() in .../s8c.php on line 7
6

Warning: Cấu hình cache thiếu, dùng mặc định in .../s8c.php on line 12

Notice: Chỉ để thông báo in .../s8c.php on line 13
chạy tiếp
```

Công dụng thực tế nhất là `E_USER_DEPRECATED`: thư viện báo cho người dùng rằng một API sắp bị bỏ, mà
không làm hỏng code của họ. Symfony có hẳn hàm `trigger_deprecation()` (gói
`symfony/deprecation-contracts`) làm đúng việc này. Laravel thì gom các deprecation vào một log channel
riêng (mục 14).

⚠️ Đừng dùng `E_USER_ERROR`. Từ PHP 8.4, `trigger_error(..., E_USER_ERROR)` phát thêm:

```
Deprecated: Passing E_USER_ERROR to trigger_error() is deprecated since 8.4, throw an exception or call exit with a string message instead
```

Muốn dừng vì lỗi thì ném exception.

### 8.5 Đọc lỗi gần nhất: `error_get_last()`

`error_get_last()` trả mảng mô tả thông báo gần nhất (kể cả thông báo bị che bằng `@`), hoặc `null` nếu
chưa có. `error_clear_last()` xoá nó.

```php
<?php
declare(strict_types=1);

$kq = @file_get_contents('/khong/co.txt');
print_r(error_get_last());
error_clear_last();
var_dump(error_get_last());
// in ra:
// Array
// (
//     [type] => 2
//     [message] => file_get_contents(/khong/co.txt): Failed to open stream: No such file or directory
//     [file] => .../s8e.php
//     [line] => 4
// )
// NULL
```

`type` là 2, tức `E_WARNING`. Toán tử `@` và cơ chế bên trong của nó (tạm hạ `error_reporting`, không
che được fatal error từ 8.0, không chặn exception) đã được giải thích ở
[Chương 07](07-toan-tu-dieu-khien.md) mục 10. Ở chương này chỉ cần nhớ: `@` là cách cũ để "biết lỗi mà
không in ra", và trong code mới nên tránh nó (mục 13).

`error_get_last()` có vai trò quan trọng hơn nhiều trong shutdown function (mục 12): đó là cách duy nhất
để biết script vừa chết vì fatal error gì.

## 9. Cấu hình: báo gì, in ra đâu, ghi log ở đâu

Khi một thông báo được phát ra (và không có error handler nào chặn nó, mục 10), PHP xử lý theo ba câu
hỏi, mỗi câu do một nhóm chỉ thị `php.ini` quyết định:

```
         thông báo (E_WARNING, E_NOTICE, ...)
                        │
          mức này có trong error_reporting?
              │ không                 │ có
           bỏ qua           ┌─────────┴─────────┐
                     display_errors?       log_errors?
                        │ On                  │ On
             in ra output (stdout,      ghi vào error_log
             hoặc stderr nếu đặt        (file, syslog, hoặc
             display_errors=stderr)      logger của SAPI)
```

### 9.1 `error_reporting`: báo những mức nào

Giá trị là một bitmask ghép từ các hằng ở mục 8.1. Đặt trong `php.ini`, hoặc lúc chạy bằng hàm
`error_reporting()` (hàm trả về giá trị cũ):

```ini
; php.ini: trong file ini chỉ dùng được các toán tử | ~ ^ ! &
error_reporting = E_ALL & ~E_DEPRECATED
```

- Mặc định của PHP từ 8.0 là `E_ALL`. Trước 8.0 mặc định bỏ qua `E_NOTICE`, `E_STRICT`, `E_DEPRECATED`.
- Manual khuyên: dev luôn `E_ALL`; production có thể giảm bớt (file `php.ini-production` đặt
  `E_ALL & ~E_DEPRECATED`), nhưng `E_ALL` cũng thường hợp lý vì nó báo sớm vấn đề.
- `error_reporting` chỉ quyết định thông báo có được báo (in hoặc ghi log) hay không. Nó không làm
  script dừng hay chạy tiếp khác đi, và không ảnh hưởng exception.
- Manual cũng khuyên đặt nó trong `php.ini` thay vì chỉ gọi hàm lúc chạy, vì có những lỗi xảy ra trước khi
  script kịp chạy dòng đầu tiên.

```php
<?php
declare(strict_types=1);

$a = [];
$cu = error_reporting(E_ALL & ~E_WARNING);   // trả về giá trị cũ
var_dump($cu === E_ALL);                     // in ra: bool(true)
echo $a['z'];                                // E_WARNING đã bị loại: im lặng
echo "không thấy warning\n";
error_reporting(E_ALL);
echo $a['z'];                                // Warning: Undefined array key "z" ...
```

⚠️ Tắt warning bằng `error_reporting` không sửa được bug, nó chỉ làm bạn không thấy bug nữa.

### 9.2 `display_errors`: có in lỗi ra output không

| Giá trị | Ý nghĩa |
|---|---|
| `Off` (hoặc `0`) | Không in |
| `On`, `1` hoặc `stdout` | In vào output chuẩn, tức là lẫn vào HTML/JSON trả cho trình duyệt |
| `stderr` | In ra stderr. Chỉ có tác dụng với CLI, phpdbg và CGI |

Mặc định của PHP là `On`. `php.ini-development` để `On`, `php.ini-production` để `Off`.

⚠️ Production phải `Off`. Manual cảnh báo thông báo lỗi có thể chứa thông tin mật như mật khẩu database.
Thực tế: đường dẫn thư mục trên server, tên bảng, câu SQL, và với stack trace có đối số thì cả dữ liệu người
dùng. Ngoài lộ thông tin, nó còn làm hỏng response: một dòng `Warning:` chèn vào đầu JSON làm client không
parse được.

Hai chi tiết khi `display_errors` tắt:

- Nếu script chết vì fatal error khi chưa gửi header nào và mã response vẫn là 200, PHP tự đổi mã HTTP
  thành 500 (đọc ở hàm `php_error_cb()` trong `main/main.c` của mã nguồn PHP). Người dùng thấy trang trắng hoặc trang lỗi của web server, không thấy
  chi tiết.
- Bật `display_errors` lúc chạy bằng `ini_set()` không giúp gì cho lỗi biên dịch của chính file đó (lỗi cú
  pháp chẳng hạn), vì file lỗi không chạy được tới dòng `ini_set`. Manual ghi rõ điều này.

Ở chế độ web, `html_errors` (mặc định `On`) bọc thông báo trong thẻ HTML; với CLI nó luôn tắt.

`display_startup_errors` điều khiển riêng các lỗi xảy ra lúc PHP khởi động (trước khi chạy script, ví dụ
không nạp được extension). Mặc định `On` từ 8.0; production nên `Off`.

### 9.3 `log_errors` và `error_log`: ghi lỗi vào đâu

- `log_errors = On`: ghi mọi thông báo được báo (theo `error_reporting`) vào log. Mặc định của PHP là
  `Off`, nhưng cả `php.ini-development` lẫn `php.ini-production` đều bật `On`. Manual khuyên production
  dùng log thay cho hiển thị.
- `error_log`: đích ghi log. Là đường dẫn file (user chạy PHP phải có quyền ghi), hoặc giá trị đặc biệt
  `syslog`. Không đặt thì lỗi đi tới logger của SAPI: với CLI là stderr, với Apache là error log của Apache.
  Với PHP-FPM, xem [Chương 18](18-fpm-nginx-opcache.md).
- Hàm `error_log('...')` ghi một dòng tuỳ ý vào cùng đích đó.

```php
<?php
declare(strict_types=1);

$log = __DIR__ . '/php-errors.log';
ini_set('display_errors', '0');     // không in lỗi ra output
ini_set('log_errors', '1');         // ghi lỗi vào log
ini_set('error_log', $log);         // log nằm ở file này

$a = [];
echo $a['x'] ?? 'mặc định', "\n";   // ?? không phát warning
echo $a['y'];                       // Warning, nhưng không in ra màn hình
error_log('Ghi một dòng tuỳ ý vào log');

echo "--- nội dung log:\n", file_get_contents($log);
unlink($log);
// in ra (thời gian sẽ khác):
// mặc định
// --- nội dung log:
// [03-Oct-2026 10:09:06 UTC] PHP Warning:  Undefined array key "y" in .../s9a.php on line 11
// [03-Oct-2026 10:09:06 UTC] Ghi một dòng tuỳ ý vào log
```

Để ý tiền tố `PHP Warning:` trong log (bản hiển thị thì không có chữ `PHP`). Đây là lý do khi chạy CLI với
`log_errors = On` mà không đặt `error_log` bạn thấy mỗi lỗi hai lần, một dòng `PHP Warning: ...` (bản log,
ra stderr) và một dòng `Warning: ...` (bản hiển thị, ra stdout), như đã nhắc ở
[Chương 01](01-php-la-gi.md).

Hai chỉ thị đi kèm: `ignore_repeated_errors` (không ghi lặp lại cùng một lỗi ở cùng file, cùng dòng) và
`ignore_repeated_source` (bỏ qua cả điều kiện cùng nguồn). Cả hai mặc định `Off`.

### 9.4 Cấu hình khuyến nghị

Giá trị lấy từ `php.ini-development` và `php.ini-production` của PHP 8.5 (hai file mẫu đi kèm mã nguồn
PHP; bản cài từ package thường copy một trong hai làm `php.ini`):

| Chỉ thị | Mặc định của PHP | `php.ini-development` | `php.ini-production` |
|---|---|---|---|
| `error_reporting` | `E_ALL` | `E_ALL` | `E_ALL & ~E_DEPRECATED` |
| `display_errors` | `On` | `On` | `Off` |
| `display_startup_errors` | `On` | `On` | `Off` |
| `log_errors` | `Off` | `On` | `On` |
| `zend.exception_ignore_args` | `Off` | `Off` | `On` |
| `zend.exception_string_param_max_len` | `15` | `15` | `0` |
| `zend.assertions` | `1` | `1` | `-1` |
| `fatal_error_backtraces` (8.5) | `1` | không đặt | không đặt |

Ghi chú:

- `zend.exception_string_param_max_len`: độ dài tối đa của đối số kiểu chuỗi khi in trong stack trace (mục
  2.8). Production đặt `0` để không lộ nội dung chuỗi.
- Chỉ thị nào ghi "không đặt" thì nhận giá trị mặc định của PHP.
- Có thể bạn muốn giữ `E_DEPRECATED` ở production và ghi chúng vào log để chuẩn bị nâng cấp; đó là lựa chọn
  hợp lý nếu log không bị ngập.

Xem cấu hình đang có hiệu lực:

```bash
# chạy ở terminal
php --ini                                  # php.ini nào đang được nạp
php -i | grep -E 'error_reporting|display_errors|log_errors|error_log'
```

⚠️ CLI và PHP-FPM thường dùng **hai file `php.ini` khác nhau** (ví dụ trên Debian/Ubuntu là
`/etc/php/8.x/cli/php.ini` và `/etc/php/8.x/fpm/php.ini`). `php -i` ở terminal cho biết cấu hình của CLI,
không phải của web. Muốn biết web đang chạy cấu hình gì, gọi `ini_get()` hoặc `phpinfo()` trong một request
(và xoá file đó ngay sau khi xem).

Các chỉ thị trong mục này đều thuộc loại `INI_ALL` (bảng *Runtime Configuration* của manual), tức đặt
được ở mọi nơi: `php.ini`, cấu hình pool của FPM (`php_admin_value[...]`), file `.user.ini`, và `ini_set()`
lúc chạy.

## 10. Error handler: `set_error_handler()` và `ErrorException`

### 10.1 Thay cách PHP xử lý thông báo

`set_error_handler()` đăng ký một callable được gọi **thay cho** cách xử lý mặc định ở mục 9 mỗi khi có
thông báo. Chữ ký:

```php
set_error_handler(?callable $callback, int $error_levels = E_ALL): ?callable
```

Handler nhận tới bốn tham số và trả `bool`:

```php
function handler(int $errno, string $errstr, string $errfile, int $errline): bool
```

- `$errno`: mức của thông báo (`E_WARNING`...). `$errstr`: nội dung. `$errfile`, `$errline`: vị trí.
  (Tham số thứ năm `$errcontext` đã bị bỏ từ PHP 8.0.)
- Trả `true` (hoặc không trả gì, xem dưới): thông báo coi như đã xử lý, PHP không in và không ghi log nữa.
- Trả `false`: PHP tiếp tục xử lý mặc định (in, ghi log theo cấu hình) sau khi handler chạy xong.
- Sau khi handler chạy xong (không ném exception), script chạy tiếp từ câu lệnh sau chỗ phát thông
  báo, như không có gì. Handler muốn dừng script thì phải tự `exit` hoặc ném exception.

(Manual chỉ nói "trả `false` thì handler mặc định chạy tiếp". Handler `void` không `return` gì thực tế
trả `null`, và PHP coi đó như "đã xử lý". Khai báo `: bool` và trả rõ ràng để khỏi phải nhớ chi tiết này.)

```php
<?php
declare(strict_types=1);

function boXuLy(int $errno, string $errstr, string $errfile, int $errline): bool
{
    echo "[handler] mức $errno: $errstr (dòng $errline)\n";
    return true;    // đã xử lý xong, PHP không in thông báo mặc định nữa
}

$cu = set_error_handler(boXuLy(...));
var_dump($cu);                       // handler trước đó: chưa có nên là null

$a = [];
echo $a['x'];                        // warning đi vào handler
echo $khongCo;                       // warning đi vào handler
echo "chạy tiếp\n";

restore_error_handler();             // trả lại handler trước đó (ở đây là cách xử lý mặc định)
echo $a['y'];                        // lại in theo kiểu mặc định
// in ra:
// NULL
// [handler] mức 2: Undefined array key "x" (dòng 14)
// [handler] mức 2: Undefined variable $khongCo (dòng 15)
// chạy tiếp
//
// Warning: Undefined array key "y" in .../s10a.php on line 19
```

Mỗi lần `set_error_handler()` được gọi, handler đang hoạt động được cất vào một ngăn xếp; hàm trả về handler
đó (hoặc `null` nếu đang dùng cách mặc định). `restore_error_handler()` lấy lại handler ở đỉnh ngăn xếp.
Truyền `null` vào `set_error_handler()` là quay về xử lý mặc định. Từ PHP 8.5 có thêm
`get_error_handler()` trả handler đang hoạt động (hoặc `null`) mà không phải đặt rồi khôi phục như trước.

Tham số `$error_levels` giới hạn những mức gọi handler. Các mức không nằm trong mặt nạ đi thẳng tới cách xử
lý mặc định của PHP, không đi tới handler cũ trong ngăn xếp:

```php
set_error_handler(function (int $errno, string $errstr): bool {
    echo "[chỉ notice] $errstr\n";
    return true;
}, E_NOTICE | E_USER_NOTICE);

$a = [];
echo $a['k'];                 // Warning: không nằm trong mặt nạ, PHP in theo kiểu mặc định
trigger_error('một notice');  // in ra: [chỉ notice] một notice
```

### 10.2 Handler được gọi cả khi `error_reporting` tắt mức đó

Manual nhấn mạnh: khi có handler, `error_reporting` **không** chặn việc gọi handler. Handler vẫn được gọi,
và có trách nhiệm tự đọc `error_reporting()` để quyết định. Toán tử `@` cũng vậy: nó chỉ tạm hạ
`error_reporting`, handler vẫn chạy:

```php
<?php
declare(strict_types=1);

set_error_handler(function (int $no, string $s): bool {
    echo "[handler] $s, error_reporting()=", error_reporting(), "\n";
    return true;
});

$a = [];
error_reporting(0);
echo $a['x'];
error_reporting(E_ALL);
echo @$a['y'];
// in ra:
// [handler] Undefined array key "x", error_reporting()=0
// [handler] Undefined array key "y", error_reporting()=4437
```

`4437` là mặt nạ chỉ gồm các mức fatal mà `@` để lại từ PHP 8.0 (chi tiết ở
[Chương 07](07-toan-tu-dieu-khien.md) mục 10.2). Cách kiểm tra đúng là theo bit:
`if (!(error_reporting() & $errno))`, nghĩa là "mức này hiện không được báo". Đừng viết
`error_reporting() === 0` như code trước PHP 8.

### 10.3 Biến warning thành exception bằng `ErrorException`

Đây là cách dùng phổ biến nhất của error handler, và là cách mọi framework hiện đại làm: ném một
`ErrorException` từ handler, để mọi warning/notice đi theo một luồng duy nhất là exception. Lợi ích:

- Không còn chuyện "chạy tiếp với dữ liệu sai": warning làm dừng đoạn code đang chạy ngay tại chỗ.
- Bắt được bằng `try/catch`, có stack trace, đi tới cùng logger và exception handler như mọi exception
  khác.

`ErrorException` là class con của `Exception`, có thêm `severity` (mức lỗi gốc). Constructor:

```php
public function __construct(
    string $message = "", int $code = 0, int $severity = E_ERROR,
    ?string $filename = null, ?int $line = null, ?Throwable $previous = null
)
```

Truyền `$errfile`, `$errline` của handler vào `$filename`, `$line` để exception chỉ đúng chỗ phát thông báo
(chứ không phải dòng `new ErrorException` trong handler).

```php
<?php
declare(strict_types=1);

set_error_handler(function (int $errno, string $errstr, string $errfile, int $errline): bool {
    if (!(error_reporting() & $errno)) {
        return false;     // mức này đang bị tắt (ví dụ bị che bằng @): để PHP xử lý mặc định
    }
    if ($errno === E_DEPRECATED || $errno === E_USER_DEPRECATED) {
        echo "[log] DEPRECATED: $errstr\n";   // thực tế: ghi vào logger
        return true;      // deprecation: ghi log, không làm dừng chương trình
    }
    throw new ErrorException($errstr, 0, $errno, $errfile, $errline);
});

// 1) Warning giờ bắt được bằng try/catch
$gia = ['USD' => 25_000];
try {
    $tong = 3 * $gia['VND'];
    echo "Không tới đây\n";
} catch (ErrorException $e) {
    echo "Bắt được: ", $e->getMessage(), " (severity ", $e->getSeverity(), ")\n";
}

// 2) Hàm I/O: thay vì trả false, giờ ném exception
try {
    $noiDung = file_get_contents('/khong/co.txt');
} catch (ErrorException $e) {
    echo "Bắt được: ", $e->getMessage(), "\n";
}

// 3) Toán tử @ vẫn được tôn trọng
$x = @$gia['EUR'];
var_dump($x);

// 4) Deprecation chỉ ghi log
trigger_error('API cũ', E_USER_DEPRECATED);
echo "Vẫn chạy\n";

// 5) Không ai bắt: thành Uncaught ErrorException
echo $gia['JPY'];
```

Output:

```
Bắt được: Undefined array key "VND" (severity 2)
Bắt được: file_get_contents(/khong/co.txt): Failed to open stream: No such file or directory
NULL
[log] DEPRECATED: API cũ
Vẫn chạy

Fatal error: Uncaught ErrorException: Undefined array key "JPY" in .../s10c.php:40
Stack trace:
#0 .../s10c.php(40): {closure:.../s10c.php:4}(2, 'Undefined array...', '/path/to/projec...', 40)
#1 {main}
  thrown in .../s10c.php on line 40
```

Đọc output:

- Ở (1), dòng `$tong = 3 * ...` không chạy xong: `$tong` không được gán, không có đơn hàng nào bị tính
  sai. Đây là toàn bộ giá trị của mẫu này.
- Ở (5), frame `#0` là chính closure handler, được gọi từ dòng 40. Tên `{closure:file:4}` (closure khai báo
  ở dòng 4) là định dạng từ PHP 8.4; bản cũ hơn chỉ in `{closure}`. Các đối số chuỗi bị cắt còn 15 ký tự
  kèm `...` do `zend.exception_string_param_max_len` mặc định là 15 (mục 9.4).
- Vì sao không ném với deprecation: manual (ví dụ của trang `ErrorException`) giải thích rằng deprecation
  mới hoặc không lường trước (ví dụ sau khi nâng cấp PHP hay nâng cấp thư viện) sẽ làm hỏng ứng dụng nếu
  bị biến thành exception. Deprecation là lời nhắc cho lập trình viên, nên vào log.

⚠️ Hệ quả cần biết khi bật mẫu này trong một codebase cũ: code nào viết theo kiểu "gọi hàm I/O rồi kiểm
`=== false`" sẽ không bao giờ tới được nhánh kiểm `false`, vì exception đã bay ra trước. Đó thường là điều
tốt, nhưng phải rà lại những chỗ cố ý chịu lỗi (ví dụ "đọc file cache, không có thì thôi") và chuyển chúng
sang kiểm tra trước (`is_file()`) hoặc `try/catch`.

### 10.4 Handler không nhận được gì

Manual liệt kê các mức **không** xử lý được bằng handler: `E_ERROR`, `E_PARSE`, `E_CORE_ERROR`,
`E_CORE_WARNING`, `E_COMPILE_ERROR`, `E_COMPILE_WARNING` (bất kể phát ở đâu). Lỗi xảy ra trước khi script
chạy (ví dụ khi xử lý file upload) cũng không tới handler vì lúc đó handler chưa được đăng ký.

Nói cách khác: fatal error, ví dụ hết bộ nhớ, đi thẳng qua handler. Với chúng chỉ còn
`register_shutdown_function()` (mục 12).

Một handler cũng không thấy được thông báo phát ra trước dòng `set_error_handler()`, kể cả deprecation lúc
biên dịch chính file chứa nó (mục 8.2). Vì vậy framework đăng ký handler càng sớm càng tốt, ngay khi khởi
động.

## 11. Exception handler toàn cục: `set_exception_handler()`

### 11.1 Lưới cuối cùng cho exception

Mục 2.4 nói exception không ai bắt sẽ thành fatal error "Uncaught". Trước khi tới bước đó, PHP gọi
*exception handler toàn cục* nếu bạn đã đăng ký bằng `set_exception_handler()`. Manual mô tả: hiệu quả
giống như bọc cả chương trình trong một `try/catch` với handler đó là khối `catch`.

```php
set_exception_handler(?callable $callback): ?callable
// handler có dạng: function (Throwable $e): void
```

```php
<?php
declare(strict_types=1);

register_shutdown_function(function (): void {
    echo "[shutdown] chạy sau cùng\n";
});

set_exception_handler(function (Throwable $e): void {
    // Thực tế: ghi log đầy đủ (class, message, trace, chuỗi previous),
    // rồi trả trang lỗi chung chung cho người dùng
    echo "[exception handler] ", $e::class, ": ", $e->getMessage(), "\n";
    echo "Xin lỗi, đã có lỗi xảy ra.\n";
});

function xuLy(int $id): void
{
    if ($id < 0) {
        throw new InvalidArgumentException("id âm: $id");
    }
}

echo "Bắt đầu\n";
xuLy(-1);
echo "Không bao giờ in dòng này\n";
// in ra:
// Bắt đầu
// [exception handler] InvalidArgumentException: id âm: -1
// Xin lỗi, đã có lỗi xảy ra.
// [shutdown] chạy sau cùng
```

Những điều cần biết:

- Handler nhận `Throwable`, tức nhận cả `Error`. Khai báo tham số `Exception $e` là sai: khi một `Error`
  lọt lưới, chính lời gọi handler thất bại, và thông báo cuối cùng chỉ nói về lỗi kiểu của handler, che
  mất lỗi gốc:

  ```
  Fatal error: Uncaught TypeError: {closure:.../s11e.php:3}(): Argument #1 ($e) must be of type Exception, Error given in .../s11e.php:3
  ```
- **Script dừng sau khi handler chạy xong** (manual: "Execution will stop after the callback is called").
  Handler không phải chỗ để "cứu" và chạy tiếp; nó là chỗ ghi log và trả lời lịch sự.
- Shutdown function và destructor vẫn chạy sau đó (từ PHP 8.0, exception không ai bắt đi qua quy trình
  "clean shutdown", nên destructor được gọi).
- Nếu chính handler ném exception, exception mới đó không quay lại handler mà thành fatal error "Uncaught":

  ```php
  <?php
  declare(strict_types=1);

  set_exception_handler(function (Throwable $e): void {
      echo "[handler] ", $e->getMessage(), "\n";
      throw new RuntimeException('lỗi trong chính handler');
  });

  throw new LogicException('lỗi gốc');
  // in ra:
  // [handler] lỗi gốc
  //
  // Fatal error: Uncaught RuntimeException: lỗi trong chính handler in .../s11b.php:6
  // Stack trace:
  // #0 [internal function]: {closure:.../s11b.php:4}(Object(LogicException))
  // #1 {main}
  //   thrown in .../s11b.php on line 6
  ```

  Vì vậy code trong handler phải tối giản và tự bọc phần dễ hỏng (gửi log qua mạng chẳng hạn) trong
  `try/catch` riêng.
- Ở CLI, khi handler xử lý xong, đừng trông vào mã thoát mặc định. Nếu cron hoặc CI cần biết script thất
  bại, gọi `exit(1)` ở cuối handler. (Laravel làm vậy khi chạy console mà chính exception handler của nó
  cũng hỏng.)
- `set_exception_handler()` trả handler trước đó; `restore_exception_handler()` khôi phục handler trước;
  `get_exception_handler()` (8.5) đọc handler hiện tại. Manual khuyên không đổi exception handler từ bên
  trong chính nó, vì hành vi ở trường hợp này đã thay đổi qua các bản 8.3.0 và 8.3.5.

### 11.2 Exception handler hay `try/catch` ở tầng ngoài cùng?

Hai cách cho cùng kết quả "không exception nào lọt ra mà không có log". Framework thường làm cả hai:

- Trong luồng chính (xử lý một HTTP request, một lệnh console), framework bọc lời gọi controller bằng
  `try/catch (Throwable $e)` để biến exception thành response HTTP phù hợp (404, 422, 500...).
- `set_exception_handler()` là lưới an toàn cho những exception thoát ra ngoài luồng đó, ví dụ ném ra từ
  chính code khởi động của framework.

Trong PHP thuần không framework, một `set_exception_handler()` đăng ký ở đầu `index.php` là mức tối thiểu.

## 12. Fatal error và `register_shutdown_function()`

### 12.1 Fatal error là gì, khi nào còn gặp

Sau PHP 7 và 8, phần lớn lỗi engine đã thành `Error` bắt được. Những gì còn lại là fatal error thật sự,
loại mà engine không thể (hoặc không an toàn để) tiếp tục chạy code PHP nào trong ngữ cảnh đó:

| Fatal error | Mức | Ví dụ thông báo |
|---|---|---|
| Hết bộ nhớ | `E_ERROR` | `Allowed memory size of 134217728 bytes exhausted (tried to allocate ... bytes)` |
| Chạy quá thời gian | `E_ERROR` | `Maximum execution time of 30 seconds exceeded` |
| Lỗi biên dịch | `E_COMPILE_ERROR` | `Cannot redeclare function f() (previously declared in ...)` |
| Lỗi cú pháp của file chính | `E_PARSE` | `syntax error, unexpected ...` |
| Exception không ai bắt, không có handler | `E_ERROR` | `Uncaught RuntimeException: ...` |

(Lỗi cú pháp trong file được `include`/`require` hoặc trong `eval()` thì ném `ParseError` bắt được, như
[Chương 02](02-php-chay-nhu-the-nao.md) đã minh hoạ. File chính sai cú pháp thì không có code nào chạy để
bắt cả.)

Cả hai file `php.ini` mẫu đặt `memory_limit = 128M` và `max_execution_time = 30` (giây). Riêng CLI, PHP đặt
`max_execution_time` thành 0 (không giới hạn) sau khi đọc xong `php.ini`, nên giá trị trong `php.ini` không
có tác dụng; muốn giới hạn thì gọi `set_time_limit()` hoặc `ini_set()` lúc chạy.

Khi fatal error xảy ra:

1. Thông báo được in/ghi log theo cấu hình ở mục 9. Error handler không được gọi (mục 10.4).
2. Code PHP đang chạy dừng ngay: không `catch`, không `finally`.
3. Shutdown function được gọi.
4. Ở CLI, mã thoát là 255. Ở web, nếu `display_errors` tắt, header chưa gửi và mã response đang là 200,
   PHP đổi nó thành 500 (mục 9.2).

### 12.2 Shutdown function: đoạn code chạy lúc script kết thúc

`register_shutdown_function(callable $callback, mixed ...$args)` đăng ký một callable chạy **khi script kết
thúc**, bất kể kết thúc thế nào: chạy hết bình thường, gọi `exit()`, exception không ai bắt, hay fatal error.

Manual ghi các luật:

- Đăng ký nhiều lần thì chạy theo đúng thứ tự đăng ký. Một shutdown function có thể đăng ký thêm shutdown
  function khác, cái mới được thêm vào cuối hàng.
- Gọi `exit()` bên trong một shutdown function thì dừng hẳn, các shutdown function sau không chạy.
- Shutdown function vẫn là một phần của request: nó in được output, đọc được output buffer.
- Shutdown function chạy tách khỏi bộ đếm `max_execution_time`: kể cả khi script bị dừng vì chạy quá lâu,
  shutdown function vẫn được gọi, và không bị ngắt nếu chính nó chạy quá thời gian.
- Không chạy nếu process bị giết bằng tín hiệu `SIGTERM` hoặc `SIGKILL` (mục 3.5).

Kết hợp với `error_get_last()` (mục 8.5), shutdown function là cách duy nhất để **ghi log một fatal
error** bằng code của bạn:

```php
<?php
declare(strict_types=1);

ini_set('memory_limit', '8M');

register_shutdown_function(function (): void {
    $loi = error_get_last();
    $fatal = E_ERROR | E_PARSE | E_CORE_ERROR | E_COMPILE_ERROR | E_USER_ERROR | E_RECOVERABLE_ERROR;
    if ($loi !== null && ($loi['type'] & $fatal)) {
        // Thực tế: ghi vào log, gửi cảnh báo. Ở đây in ra để xem.
        echo "[shutdown] Script chết vì fatal error: {$loi['message']}\n";
        echo "[shutdown] Tại ", basename($loi['file']), ":", $loi['line'], "\n";
        echo "[shutdown] Có trace? ", isset($loi['trace']) ? 'có, ' . count($loi['trace']) . ' frame' : 'không', "\n";
    }
});

function docBaoCao(int $soDong): array
{
    $dong = [];
    for ($i = 0; $i < $soDong; $i++) {
        $dong[] = str_repeat('x', 1024);    // giả lập nạp cả file vào bộ nhớ
    }
    return $dong;
}

function xuatBaoCao(): void
{
    try {
        docBaoCao(100_000);
    } catch (Throwable $e) {
        echo "Không bao giờ vào đây: fatal error không phải exception\n";
    } finally {
        echo "finally cũng không chạy\n";
    }
}

xuatBaoCao();
```

Output minh hoạ trên PHP 8.5 (số byte trong thông báo, và cả dòng, frame nơi hết bộ nhớ, có thể khác trên máy bạn):

```
Fatal error: Allowed memory size of 8388608 bytes exhausted (tried to allocate 20480 bytes) in .../s12a.php on line 21
Stack trace:
#0 .../s12a.php(21): str_repeat('x', 1024)
#1 .../s12a.php(29): docBaoCao(100000)
#2 .../s12a.php(37): xuatBaoCao()
#3 {main}
[shutdown] Script chết vì fatal error: Allowed memory size of 8388608 bytes exhausted (tried to allocate 20480 bytes)
[shutdown] Tại s12a.php:21
[shutdown] Có trace? có, 3 frame
```

Cùng file đó trên PHP 8.4 (output minh hoạ):

```
Fatal error: Allowed memory size of 8388608 bytes exhausted (tried to allocate 20480 bytes) in .../s12a.php on line 21
[shutdown] Script chết vì fatal error: Allowed memory size of 8388608 bytes exhausted (tried to allocate 20480 bytes)
[shutdown] Tại s12a.php:21
[shutdown] Có trace? không
```

Để ý: cả `catch (Throwable)` lẫn `finally` đều không chạy. Fatal error không phải exception.

⚠️ Bẫy kinh điển: hết bộ nhớ thì chính shutdown function cũng cần bộ nhớ để chạy (soạn chuỗi log, gọi
logger), và nếu không còn đủ thì nó có thể chết theo trước khi kịp ghi gì. Mẹo mà Laravel dùng: lúc khởi động, cấp phát sẵn một chuỗi 32 KB "dự phòng"
(`str_repeat('x', 32768)`) giữ trong một static property; việc đầu tiên shutdown function làm là gán
property đó về `null` để trả lại 32 KB cho việc ghi log.

### 12.3 Shutdown function không chỉ cho lỗi

Shutdown function chạy cả khi script kết thúc bình thường, nên còn dùng cho: đẩy nốt log hoặc metric đang
gom trong bộ nhớ, giải phóng lock, ghi thời gian chạy của request. Theo trình tự kết thúc request trong mã
nguồn PHP (`php_request_shutdown()` trong `main/main.c`), shutdown function chạy trước khi PHP gọi
destructor của các object còn sống và trước khi output buffer được đẩy ra. Vì vậy ở môi trường web, việc nặng trong shutdown function làm client
phải chờ, trừ khi response đã được gửi sớm bằng `fastcgi_finish_request()` (PHP-FPM, xem
[Chương 18](18-fpm-nginx-opcache.md)).

### 12.4 PHP 8.5: fatal error có stack trace

Trước 8.5, thông báo fatal error chỉ có một dòng: "hết bộ nhớ ở dòng 21". Dòng 21 thường nằm trong một hàm
tiện ích được gọi từ hàng trăm nơi, nên thông tin đó gần như vô dụng. RFC *Error Backtraces v2* (PHP 8.5)
thêm ini `fatal_error_backtraces`:

- Bật (`1`, mặc định) thì mọi fatal error (mức `E_ERROR`, `E_CORE_ERROR`, `E_COMPILE_ERROR`, `E_USER_ERROR`,
  `E_RECOVERABLE_ERROR`, `E_PARSE`) kèm phần `Stack trace:` như output ở trên.
- `error_get_last()` trong shutdown function có thêm key `trace` (mảng các frame). Riêng fatal error do
  exception không ai bắt thì không có key này (exception đã có trace riêng, in trong message).
- Trace tôn trọng `zend.exception_ignore_args` và attribute `#[\SensitiveParameter]` (mục 2.8), nên trên
  production với `php.ini-production`, đối số không bị in ra.
- Chỉ áp dụng cho fatal error. Warning và notice vẫn không có trace (RFC giải thích: giữ trace cho mọi
  thông báo làm các đối số sống lâu hơn dự kiến; ai cần trace cho warning thì đã có mẫu `ErrorException`).

Ví dụ trong RFC với lỗi quá thời gian do đệ quy vô hạn: trước 8.5 chỉ có
`Fatal error: Maximum execution time of 1 second exceeded in example.php on line 7`; từ 8.5 có thêm danh sách
một loạt frame `recurse()` lồng nhau, nhìn là biết đệ quy không dừng.

Tắt tính năng (ví dụ vì công cụ đọc log của bạn chưa hiểu định dạng nhiều dòng):

```php
<?php
declare(strict_types=1);

ini_set('fatal_error_backtraces', '0');
ini_set('memory_limit', '4M');

function f(): string
{
    return str_repeat('x', 8 * 1024 * 1024);
}

f();
// Fatal error: Allowed memory size of 4194304 bytes exhausted (tried to allocate 8388640 bytes) in ... on line 9
// (không có Stack trace; 8388640 là số byte trên bản PHP 64-bit: 8 MB chuỗi cộng phần header của zend_string)
```

⚠️ Đây là thay đổi định dạng log: công cụ nào đang parse dòng `Fatal error:` theo giả định "một lỗi một
dòng" sẽ cần cập nhật khi lên 8.5.

## 13. Thói quen xử lý lỗi tốt

Phần này gom các nguyên tắc rút ra từ những mục trên. Chúng không phải luật của ngôn ngữ, mà là kinh
nghiệm chung của cộng đồng.

### 13.1 Ba tầng phòng thủ cho một ứng dụng PHP

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │ Tầng 3: register_shutdown_function + error_get_last                  │
  │         → ghi log fatal error (hết RAM, quá giờ)                     │
  │  ┌────────────────────────────────────────────────────────────────┐  │
  │  │ Tầng 2: set_exception_handler (và try/catch Throwable ở biên)  │  │
  │  │         → ghi log mọi exception lọt lưới, trả trang lỗi 500    │  │
  │  │  ┌──────────────────────────────────────────────────────────┐  │  │
  │  │  │ Tầng 1: set_error_handler → ErrorException               │  │  │
  │  │  │         → warning/notice thành exception                 │  │  │
  │  │  │  ┌────────────────────────────────────────────────────┐  │  │  │
  │  │  │  │ Code ứng dụng: throw / try / catch cụ thể / finally │  │  │  │
  │  │  │  └────────────────────────────────────────────────────┘  │  │  │
  │  │  └──────────────────────────────────────────────────────────┘  │  │
  │  └────────────────────────────────────────────────────────────────┘  │
  └──────────────────────────────────────────────────────────────────────┘
  Cấu hình: error_reporting = E_ALL, display_errors = Off (production), log_errors = On
```

Mọi framework hiện đại (Laravel, Symfony) dựng sẵn cả ba tầng. Viết PHP thuần thì bạn tự dựng, ở đầu file
vào (*front controller*, thường là `public/index.php`).

### 13.2 Ném sớm, bắt muộn

- **Ném sớm** (*fail fast*): kiểm tra đầu vào ngay ở chỗ nó đi vào (constructor, đầu hàm public) và ném
  exception ngay khi thấy sai. Đừng để một giá trị `null` hay chuỗi rỗng đi qua năm hàm rồi mới gây
  `TypeError` ở nơi chẳng liên quan.
- **Bắt muộn**: chỉ `catch` ở nơi **làm được gì đó có ích** với lỗi. Có bốn việc có ích:
  1. Phục hồi: thử lại, dùng giá trị dự phòng, chuyển sang nguồn khác.
  2. Dịch: đổi exception kỹ thuật thành exception có nghĩa với tầng trên (kèm `previous`, mục 7).
  3. Dọn dẹp rồi ném lại (rollback, xoá file tạm).
  4. Ở ranh giới: ghi log và trả lời (response 500, đánh dấu job thất bại).

  Không làm được việc nào trong bốn việc đó thì **đừng bắt**, cứ để exception đi lên.

### 13.3 Không nuốt lỗi

```php
// ❌ Nuốt lỗi: chuyện gì đã xảy ra? Không ai biết, không có log
try {
    $this->guiEmailXacNhan($donHang);
} catch (Exception $e) {
}

// ✅ Cố ý bỏ qua thì nói rõ: bắt đúng loại, ghi log, có comment
try {
    $this->guiEmailXacNhan($donHang);
} catch (MailTransportException $e) {
    // Gửi mail thất bại không được làm hỏng việc đặt hàng; đã có job gửi lại định kỳ.
    $this->logger->warning('Không gửi được email xác nhận', ['don' => $donHang->id, 'exception' => $e]);
}
```

Khối `catch` rỗng là một trong những lỗi tốn kém nhất: bug vẫn còn đó, chỉ là không còn dấu vết. Các biến
thể khác của "nuốt lỗi": `return null` trong `catch` mà không log; `@` trước lời gọi hàm; `return` trong
`finally` (mục 3.3).

### 13.4 Log một lần, ở ranh giới

```php
// ❌ Mỗi tầng đều log rồi ném lại: một sự cố thành ba dòng log giống nhau
catch (PDOException $e) {
    $this->logger->error($e->getMessage());
    throw $e;
}
```

Nếu đã có exception handler ở ranh giới ghi log, tầng giữa chỉ cần ném (hoặc dịch rồi ném). Log trùng làm
người đọc log tưởng có nhiều sự cố, và làm đếm lỗi sai. Khi ghi log, truyền **cả object exception** cho
logger (ví dụ `['exception' => $e]` với Monolog) thay vì chỉ `$e->getMessage()`, để có class, file, dòng,
stack trace và chuỗi `previous`.

### 13.5 Exception cho chuyện bất thường, giá trị trả về cho chuyện bình thường

"Không tìm thấy" có phải lỗi không? Tuỳ ngữ cảnh:

- Hàm `timTheoEmail(string $email): ?NguoiDung` trong form đăng ký: không tìm thấy là chuyện bình thường
  (email chưa được dùng), trả `null` là hợp lý.
- Hàm `layDonHang(int $id): DonHang` khi người dùng bấm vào đơn của chính họ: không tìm thấy là bất thường,
  ném exception.

Laravel làm cả hai: `User::find($id)` trả `null`, `User::findOrFail($id)` ném `ModelNotFoundException`
(và Laravel tự đổi nó thành response 404). Đừng dùng exception để điều khiển luồng thông thường (ví dụ ném
exception để thoát khỏi vòng lặp khi tìm thấy phần tử): code khó đọc, và tạo exception tốn chi phí hơn
nhiều so với một `return` vì phải thu thập stack trace.

### 13.6 Chọn chế độ "ném" khi API cho phép

Nhiều API của PHP có cả chế độ cũ (trả `false`/`null`, phát warning) và chế độ ném exception. Luôn chọn chế
độ ném:

| API | Chế độ ném | Exception |
|---|---|---|
| `json_decode`, `json_encode` | cờ `JSON_THROW_ON_ERROR` (7.3) | `JsonException` |
| PDO | `PDO::ERRMODE_EXCEPTION`, mặc định từ 8.0 | `PDOException` |
| `filter_var` và họ hàm filter | cờ `FILTER_THROW_ON_FAILURE` (8.5) | `Filter\FilterFailedException` |
| `new DateTimeImmutable(...)` | luôn ném; class riêng từ 8.3 | `DateMalformedStringException` |
| `mysqli` | `mysqli_report(MYSQLI_REPORT_ERROR \| MYSQLI_REPORT_STRICT)`, mặc định từ 8.1 | `mysqli_sql_exception` |

```php
<?php
declare(strict_types=1);

try {
    $tuoi = filter_var('abc', FILTER_VALIDATE_INT, FILTER_THROW_ON_FAILURE);
} catch (Filter\FilterFailedException $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
}
// in ra (PHP 8.5): Filter\FilterFailedException: filter validation failed: filter int not satisfied by 'abc'
```

Lý do: giá trị trả về `false` rất dễ bị quên kiểm tra, và `false` còn dễ bị nhầm với một giá trị hợp lệ
(`json_decode('null')` trả `null` hợp lệ, y hệt `null` khi JSON hỏng). Exception thì không bị "quên": không
ai bắt, nó dừng chương trình. Chi tiết `JSON_THROW_ON_ERROR` ở [Chương 14](14-file-json-thoi-gian.md), PDO ở
[Chương 16](16-php-va-database.md).

### 13.7 Viết message cho người trực sự cố lúc 3 giờ sáng

- Nói cái gì sai, với đối tượng nào, mong đợi gì, nhận gì: "Đơn DH-42: số lượng phải từ 1 tới
  100, nhận 0" thay vì "Invalid quantity".
- Không đưa bí mật vào message (mật khẩu, token, số thẻ). Dùng `#[\SensitiveParameter]` cho tham số nhạy
  cảm.
- Message không phải thông báo cho người dùng cuối. Thông báo thân thiện được tạo ở tầng hiển thị.

### 13.8 Cấu hình đúng theo môi trường

- Dev: `error_reporting = E_ALL`, `display_errors = On`. Thấy warning nào sửa warning đó, đừng để log dev đầy
  cảnh báo "quen mắt".
- Production: `display_errors = Off`, `log_errors = On`, `zend.exception_ignore_args = On`. Gom log về một
  chỗ và có cảnh báo khi số lỗi tăng (dịch vụ như Sentry, Flare, hay stack log tự dựng).
- Theo dõi `E_DEPRECATED` trong log trước mỗi lần nâng PHP (lên kế hoạch nâng cấp ở
  [Chương 22](22-phien-ban-moi.md)).

## 14. Laravel xử lý lỗi thế nào (nhìn lướt)

Phần này chỉ để bạn thấy các khái niệm của chương được dùng trong một framework thật. Chi tiết về Laravel
nằm ở [Chương 23](23-laravel-gioi-thieu.md) tới [Chương 26](26-laravel-container-provider-facade.md).

### 14.1 Ba tầng, dựng sẵn khi khởi động

Ngay khi ứng dụng khởi động, class `Illuminate\Foundation\Bootstrap\HandleExceptions` (mã nguồn
laravel/framework nhánh 13.x) chạy method `bootstrap()`, làm đúng những gì mục 10 tới 12 mô tả:

1. Cấp phát 32 KB bộ nhớ dự phòng: `static::$reservedMemory = str_repeat('x', 32768);` (mục 12.2).
2. `error_reporting(-1)`: báo mọi mức (`-1` có mọi bit đều bật).
3. `set_error_handler(...)`: deprecation (`E_DEPRECATED`, `E_USER_DEPRECATED`) được ghi vào log channel
   `deprecations`; mọi mức khác, nếu nằm trong `error_reporting()`, thành `ErrorException`. Áp dụng **ở mọi
   môi trường**, không chỉ dev.
4. `set_exception_handler(...)`: exception lọt lưới được chuyển cho exception handler của ứng dụng để
   report (ghi log) và render (thành response, hoặc output console).
5. `register_shutdown_function(...)`: trả lại 32 KB dự phòng, rồi nếu `error_get_last()` là fatal error
   (`E_COMPILE_ERROR`, `E_CORE_ERROR`, `E_ERROR`, `E_PARSE`) thì dựng một object `FatalError` (của Symfony
   ErrorHandler) và đưa vào cùng luồng report/render.
6. Ngoài môi trường `testing`, `ini_set('display_errors', 'Off')`.

⚠️ Hệ quả của bước 3: dòng `$row['email']` với key không tồn tại, vốn chỉ là warning trong PHP thuần, trong
ứng dụng Laravel là `ErrorException` và (nếu không ai bắt) thành response 500. Đây là chủ đích: bug lộ ra
sớm thay vì lặng lẽ cho ra `null`.

Với deprecation: skeleton Laravel 13 đặt `LOG_DEPRECATIONS_CHANNEL=null` trong `.env.example`, tức mặc định
deprecation bị bỏ đi. Muốn theo dõi chúng (nên làm trước khi nâng PHP hay nâng Laravel), trỏ biến này tới một
channel thật.

### 14.2 Cấu hình trong `bootstrap/app.php`

Từ Laravel 11 không còn file `app/Exceptions/Handler.php`; cấu hình nằm trong `bootstrap/app.php`, qua
`withExceptions()` (ví dụ theo tài liệu Laravel 13.x):

```php
use App\Exceptions\InvalidOrderException;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Http\Request;
use Psr\Log\LogLevel;

->withExceptions(function (Exceptions $exceptions): void {
    // report: exception được ghi/gửi đi đâu (mặc định vẫn log thêm, trừ khi ->stop() hoặc return false)
    $exceptions->report(function (InvalidOrderException $e) {
        // gửi Slack, Sentry...
    });

    // mức log cho một loại exception
    $exceptions->level(PDOException::class, LogLevel::CRITICAL);

    // không bao giờ report loại này
    $exceptions->dontReport([InvalidOrderException::class]);

    // render: exception biến thành HTTP response nào
    $exceptions->render(function (InvalidOrderException $e, Request $request) {
        return response()->json(['message' => $e->getMessage()], 422);
    });
})
```

Những điểm nối với chương này:

- Laravel đọc type-hint của tham số đầu tiên trong closure để biết closure xử lý loại exception nào,
  giống cơ chế `instanceof` của `catch` (mục 2.5).
- Một số loại mặc định không được report (danh sách `$internalDontReport` trong
  `Illuminate\Foundation\Exceptions\Handler`), như `HttpException`, `ModelNotFoundException`,
  `ValidationException`, `AuthenticationException`, `AuthorizationException`, `TokenMismatchException`. Chúng
  là tình huống bình thường của web (404, 422, 401, 403, 419), không phải sự cố.
- Trước khi render, Laravel "dịch" một số exception, và luôn giữ exception gốc làm `previous` (mục 7): ví dụ
  `ModelNotFoundException` thành `NotFoundHttpException` (404), `TokenMismatchException` thành
  `HttpException` 419.
- Helper `report($e)` ghi log một exception mà **không** dừng request: dùng trong `catch` khi bạn phục hồi
  được nhưng vẫn muốn có dấu vết (mục 13.3).
- `abort(404)` ném một `HttpException`; Laravel render nó thành trang lỗi tương ứng.
- `APP_DEBUG` quyết định trang lỗi có hiện chi tiết (stack trace, biến môi trường) hay không. Tài liệu
  Laravel cảnh báo: production phải để `false`, cùng lý do với `display_errors = Off` (mục 9.2).
- Queue worker của Laravel bắt `Throwable` quanh mỗi job (mục 4.5) để một job hỏng không giết cả worker.

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| `catch (Exception $e)` để "bắt hết" | Không bắt `Error` (`TypeError`, gọi method trên `null`...); job/request chết mà không qua xử lý của bạn | Bắt loại cụ thể; ở ranh giới thì `catch (Throwable $e)` (mục 4.5) |
| `catch (Exception $e)` trong file có `namespace` mà không `use` | Tên được hiểu là `App\...\Exception`, class không tồn tại, `catch` không bao giờ khớp và PHP không cảnh báo | `use Exception;` hoặc `\Exception`; chạy PHPStan (mục 2.9) |
| `catch` kiểu cha đặt trước kiểu con | Khối đầu tiên khớp thắng, khối sau không bao giờ chạy | Cụ thể trước, chung sau (mục 2.5) |
| `catch` rỗng | Lỗi biến mất không dấu vết | Không bắt nếu không làm được gì; nếu cố ý bỏ qua thì bắt đúng loại, ghi log, viết comment (mục 13.3) |
| `return` trong `finally` | Đè giá trị trả về và nuốt luôn exception đang bay | `finally` chỉ để dọn dẹp (mục 3.3) |
| Ném exception mới trong `catch` mà không truyền `previous` | Mất nguyên nhân gốc trong log | Luôn `previous: $e` (mục 7) |
| Tin `getLine()` là dòng `throw` | Đó là dòng `new` | Nhớ quy tắc, nhất là khi dùng factory (mục 2.8) |
| Nghĩ `try/catch` bắt được warning | Warning không phải exception | Error handler đổi sang `ErrorException` (mục 10.3) |
| Error handler bỏ qua `@` hoặc kiểm `error_reporting() === 0` | Từ 8.0, bên trong `@` giá trị là 4437, không phải 0 | Kiểm theo bit `!(error_reporting() & $errno)` (mục 10.2) |
| Biến cả deprecation thành exception | Nâng cấp PHP/thư viện làm ứng dụng chết vì cảnh báo vô hại | Deprecation chỉ ghi log (mục 10.3) |
| Exception handler khai báo `Exception $e` | `Error` lọt lưới làm chính handler lỗi kiểu | Khai báo `Throwable $e` (mục 11.1) |
| Trông vào `catch`/`finally` khi hết bộ nhớ | Fatal error không phải exception | Shutdown function + `error_get_last()` (mục 12.2) |
| `display_errors = On` trên production | Lộ đường dẫn, SQL, dữ liệu; làm hỏng response JSON | `Off` + `log_errors = On` (mục 9.4) |
| Xem `php -i` ở terminal rồi kết luận về cấu hình web | CLI và FPM thường dùng hai `php.ini` khác nhau | Kiểm bằng `ini_get()` trong một request (mục 9.4) |
| Dùng `assert()` để kiểm tra input | Production (`zend.assertions = -1`) bỏ hẳn code assert | Kiểm tra bằng `if` và ném exception (mục 4.2) |
| `trigger_error(..., E_USER_ERROR)` | Deprecated từ 8.4 | Ném exception (mục 8.4) |

## Tóm tắt chương

- PHP có hai cơ chế báo lỗi: error reporting (thông báo có mức: warning, notice, deprecated chạy tiếp;
  fatal dừng ngay) và exception (object được ném, đi ngược call stack tới `catch` khớp đầu tiên).
- `Throwable` có hai nhánh không kế thừa nhau: `Error` (engine báo code sai: `TypeError`, `ValueError`,
  `DivisionByZeroError`...) và `Exception` (tình huống dự kiến được; SPL có `LogicException`,
  `RuntimeException` và các class con). `catch (Exception)` không bắt `Error`.
- `catch` xét từ trên xuống theo `instanceof`; multi-catch `A | B` (7.1); bỏ biến (8.0); `throw` là biểu
  thức (8.0) dùng được sau `??`, `?:`, trong arrow function và `match`; kiểu trả về `never` (8.1).
- `finally` chạy cả khi `return` hay có exception, nhưng không chạy khi `exit()` hay fatal error. `return`
  trong `finally` nuốt exception.
- Tự định nghĩa exception: kế thừa class SPL phù hợp, mang dữ liệu bằng property, dùng marker interface cho
  cả module; khi bọc exception khác luôn truyền `previous`.
- `error_reporting` chọn mức được báo; `display_errors` in ra (production: `Off`); `log_errors` và
  `error_log` ghi log (production: `On`).
- `set_error_handler` + `ErrorException` biến warning/notice thành exception; tôn trọng `@` bằng kiểm tra
  bit; deprecation chỉ ghi log. Handler không nhận được fatal error.
- `set_exception_handler` là lưới cuối cho exception, script dừng sau khi handler chạy.
  `register_shutdown_function` + `error_get_last()` là cách duy nhất ghi log fatal error; từ 8.5 fatal error
  có stack trace (`fatal_error_backtraces`).
- Laravel dựng sẵn cả ba tầng trong `HandleExceptions`: mọi warning thành `ErrorException` ở mọi môi trường,
  deprecation vào log channel riêng, fatal error thành `FatalError`.

## Câu hỏi tự kiểm tra

1. `catch (Exception $e)` có bắt được `TypeError` không? Vì sao PHP 7 thiết kế `Error` không kế thừa
   `Exception`? (mục 4.4)
2. Hàm có `try { return 1; } finally { return 2; }` trả gì? Nếu khối `try` ném exception thay vì `return 1`
   thì người gọi nhận được gì? (mục 3.3)
3. Một exception được tạo ở hàm A và ném ở hàm B. `getLine()` và stack trace chỉ về đâu? (mục 2.8)
4. Trong file có `namespace App\Jobs;`, khối `catch (Exception $e)` không bao giờ chạy dù code ném
   `RuntimeException`. Giải thích và nêu hai cách sửa. (mục 2.9)
5. Vì sao `try/catch` không bắt được "Undefined array key"? Làm cách nào để bắt được, và cách đó ảnh hưởng
   thế nào tới code kiểu `if (file_get_contents($f) === false)`? (mục 8, 10.3)
6. Error handler có được gọi cho lỗi bị che bằng `@` không? Handler nên kiểm tra gì, và vì sao
   `error_reporting() === 0` là sai từ PHP 8? (mục 10.2)
7. Script hết bộ nhớ trong một khối `try` có `catch (Throwable)` và `finally`. Những gì chạy, những gì
   không? Làm sao ghi được log về sự cố? PHP 8.5 thay đổi gì ở thông báo lỗi? (mục 12)
8. Trong thông báo "Uncaught" có chữ `Next`, exception nào là exception thật sự bay ra ngoài? (mục 7.3)
9. Nêu giá trị nên dùng trên production cho `display_errors`, `log_errors`, `error_reporting`,
   `zend.exception_ignore_args`, và lý do của từng cái. (mục 9.4)
10. Trong ứng dụng Laravel, dòng `$row['email']` với key không tồn tại dẫn tới gì? Còn một lời gọi hàm
    deprecated? (mục 14.1)

## Bài tập

**Bài 1. Đọc cấu hình an toàn.** Viết `docCauHinh(string $path): array` đọc một file JSON và trả mảng. Tạo
class `CauHinhKhongHopLe extends RuntimeException` và ném nó (kèm `previous` khi có exception gốc) trong các
trường hợp: file không tồn tại, JSON hỏng (dùng `JSON_THROW_ON_ERROR`), JSON hợp lệ nhưng không phải object
(ví dụ `"abc"` hay `42`), thiếu key bắt buộc `db_host`. Viết script thử cả năm trường hợp (bốn lỗi và một
file đúng), in class, message và message của `getPrevious()` nếu có.

**Bài 2. Ba tầng phòng thủ cho PHP thuần.** Viết `bootstrap.php` (được `require` ở đầu mọi script) gồm:
error handler đổi warning/notice thành `ErrorException`, tôn trọng `@`, ghi deprecation vào file
`deprecations.log`; exception handler ghi class, message, file:dòng, toàn bộ chuỗi `previous` và trace vào
`errors.log`, in ra màn hình chỉ một câu "Đã có lỗi, mã tham chiếu: ..." rồi `exit(1)`; shutdown function
ghi fatal error vào `errors.log`. Viết bốn script thử: đọc key không tồn tại, ném exception không ai bắt,
gọi một hàm có tham số kiểu ngầm nullable (`int $x = null`, phát deprecation) đặt trong file được `require`
sau bootstrap, và làm hết bộ nhớ với `ini_set('memory_limit', '8M')`. Kiểm tra nội dung từng file log. Nếu có
cả PHP 8.4 và 8.5, so sánh dòng log của fatal error giữa hai bản.

**Bài 3. Ngăn xếp có giới hạn.** Viết class `NganXep` với `push(mixed $x): void`, `pop(): mixed`,
`peek(): mixed` và sức chứa tối đa truyền vào constructor. Constructor nhận sức chứa `<= 0` thì ném
`InvalidArgumentException`; `push` khi đầy ném `OverflowException`; `pop`/`peek` khi rỗng ném
`UnderflowException`. Tất cả exception của class implement một marker interface `NganXepException`. Viết
script thử từng trường hợp và một khối `catch (NganXepException $e)` chung.

**Bài 4. Bắt lỗi trong code xử lý lỗi.** Đoạn code dưới có ít nhất năm vấn đề trong cách xử lý lỗi. Tìm
chúng, giải thích hậu quả của từng cái, sửa lại, rồi chạy để xác nhận hành vi mới.

```php
<?php
declare(strict_types=1);

namespace App\Billing;

final class ChargeFailed extends \RuntimeException {}

function callGateway(int $amount): string
{
    if ($amount > 1000) {
        throw new \RuntimeException('Gateway timeout');
    }
    return 'tx_' . $amount;
}

function charge(int $amount): string
{
    try {
        return callGateway($amount);
    } catch (Exception $e) {
        throw new ChargeFailed('Charge failed');
    } finally {
        if ($amount > 5000) {
            return 'tx_unknown';
        }
    }
}

function chargeAll(array $amounts): array
{
    $ids = [];
    foreach ($amounts as $a) {
        try {
            $ids[] = charge($a);
        } catch (ChargeFailed $e) {
        }
    }
    return $ids;
}

print_r(chargeAll([100, 2000, 9000, '300']));
```

## Đọc thêm

- PHP Manual: [Errors](https://www.php.net/manual/en/language.errors.php),
  [Basics](https://www.php.net/manual/en/language.errors.basics.php),
  [Errors in PHP 7](https://www.php.net/manual/en/language.errors.php7.php)
- PHP Manual: [Exceptions](https://www.php.net/manual/en/language.exceptions.php),
  [Extending Exceptions](https://www.php.net/manual/en/language.exceptions.extending.php),
  [Throwable](https://www.php.net/manual/en/class.throwable.php),
  [Exception](https://www.php.net/manual/en/class.exception.php),
  [ErrorException](https://www.php.net/manual/en/class.errorexception.php),
  [SPL Exceptions](https://www.php.net/manual/en/spl.exceptions.php)
- PHP Manual: [Error handling configuration](https://www.php.net/manual/en/errorfunc.configuration.php),
  [Error constants](https://www.php.net/manual/en/errorfunc.constants.php),
  [set_error_handler](https://www.php.net/manual/en/function.set-error-handler.php),
  [set_exception_handler](https://www.php.net/manual/en/function.set-exception-handler.php),
  [register_shutdown_function](https://www.php.net/manual/en/function.register-shutdown-function.php),
  [error_get_last](https://www.php.net/manual/en/function.error-get-last.php),
  [assert](https://www.php.net/manual/en/function.assert.php)
- RFC: [Exceptions in the engine (PHP 7)](https://wiki.php.net/rfc/engine_exceptions_for_php7),
  [Throwable Interface](https://wiki.php.net/rfc/throwable-interface),
  [Reclassifying engine warnings](https://wiki.php.net/rfc/engine_warnings),
  [Consistent type errors for internal functions](https://wiki.php.net/rfc/consistent_type_errors),
  [throw expression](https://wiki.php.net/rfc/throw_expression),
  [Error Backtraces v2](https://wiki.php.net/rfc/error_backtraces_v2),
  [get_error_handler / get_exception_handler](https://wiki.php.net/rfc/get-error-exception-handler),
  [Filter throw on failure](https://wiki.php.net/rfc/filter_throw_on_failure)
- php-src: [UPGRADING 8.0](https://github.com/php/php-src/blob/PHP-8.0/UPGRADING),
  [UPGRADING 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING),
  [php.ini-production](https://github.com/php/php-src/blob/PHP-8.5/php.ini-production),
  [php.ini-development](https://github.com/php/php-src/blob/PHP-8.5/php.ini-development)
- Laravel 13.x: [Error Handling](https://laravel.com/docs/13.x/errors),
  [HandleExceptions.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Bootstrap/HandleExceptions.php)
