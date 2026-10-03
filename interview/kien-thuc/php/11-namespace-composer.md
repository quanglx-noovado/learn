# Chương 11. Namespace, autoload và Composer

> [← Mục lục](README.md) · [← Chương 10: OOP nâng cao và các tính năng hiện đại](10-oop-nang-cao.md) · [Chương 12: Lỗi và exception →](12-loi-exception.md)

**Bạn sẽ học được:**

- Namespace giải quyết vấn đề gì, khai báo ra sao, và PHP biến một cái tên trong code (`User`,
  `Models\User`, `\App\Models\User`) thành tên đầy đủ theo những quy tắc nào.
- Dùng `use` để import class, hàm, hằng và đặt alias; vì sao trong namespace `strlen()` vẫn chạy được
  mà `new DateTime()` lại báo lỗi.
- Autoload là gì, viết autoloader bằng `spl_autoload_register()`, và chuẩn PSR-4 ánh xạ namespace sang
  thư mục như thế nào.
- Dùng Composer: `composer.json`, `composer.lock`, ràng buộc phiên bản (`^`, `~`, `*`, bản `0.x`),
  `install` khác `update` ra sao, `require` khác `require-dev` ra sao.
- Tối ưu autoloader cho production, dùng `scripts`, `vendor/bin`, `composer audit`, và biết Packagist là gì.
- Nắm các PSR quan trọng (PSR-1, PSR-12, PER Coding Style, PSR-3, 4, 7, 11, 14, 15, 17, 18) để đọc hiểu
  code của Laravel và các thư viện.

**Cần biết trước:** [Chương 09: OOP cơ bản](09-oop-co-ban.md) (class, interface, trait),
[Chương 08: Hàm](08-ham.md) (khai báo hàm), [Chương 03](03-cu-phap-bien-hang.md) (hằng `const`/`define`,
magic constant `__DIR__`, `__NAMESPACE__`). Nên đọc mục 2.7 của [Chương 02](02-php-chay-nhu-the-nao.md)
(PHP biên dịch từng file vào lúc file được nạp).

Cách chạy ví dụ: lưu thành file `.php` rồi chạy `php ten-file.php`. Nhiều ví dụ trong chương gồm vài
file nằm trong vài thư mục; khi đó cây thư mục được vẽ ngay trước code, bạn tạo đúng cây đó rồi chạy
file chính. Output ghi trong comment là output thật trên PHP 8.5. Đường dẫn trong thông báo lỗi được
rút gọn (ví dụ `/app/main.php`) cho dễ đọc. Máy chưa cài PHP thì dùng Docker, chạy trong thư mục gốc
của ví dụ:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php main.php
```

Phần Composer (mục 8 trở đi) cần Composer. Không muốn cài thì dùng image chính thức `composer`, chạy
trong thư mục dự án:

```bash
docker run --rm -it -v "$PWD":/app -w /app composer:2 composer --version
```

## 1. Namespace là gì và vì sao cần

### 1.1 Bài toán: hai thứ cùng tên

Trong PHP, mỗi class, interface, trait, enum, hàm và hằng có một cái tên, và tên đó phải là duy nhất
trong cả chương trình đang chạy. Khi dự án chỉ có vài file do bạn tự viết, điều này dễ giữ. Khi dự án
dùng thêm thư viện của người khác, nó không còn dễ nữa.

Giả sử ứng dụng của bạn có class `Logger`, và bạn tải về một thư viện gửi email cũng có class `Logger`
của riêng nó. Cây thư mục:

```
clash/
├── app-logger.php
├── lib-logger.php
└── main.php
```

```php
<?php
// app-logger.php: Logger của ứng dụng
declare(strict_types=1);

class Logger
{
    public function log(string $msg): void { echo "[app] $msg\n"; }
}
```

```php
<?php
// lib-logger.php: Logger của thư viện email
declare(strict_types=1);

class Logger
{
    public function write(string $msg): void { echo "[lib] $msg\n"; }
}
```

```php
<?php
// main.php
declare(strict_types=1);

require __DIR__ . '/app-logger.php';
require __DIR__ . '/lib-logger.php';   // nạp file thứ hai: chết ngay ở đây
echo "không tới được dòng này\n";
```

Output trên PHP 8.5:

```
Fatal error: Cannot redeclare class Logger (previously declared in /app/app-logger.php:5) in /app/lib-logger.php on line 5
```

(`require` nạp và chạy một file khác, học kỹ ở mục 5. Từ PHP 8.4 thông báo có dạng "Cannot redeclare
class ... (previously declared in ...)"; PHP 8.3 trở về trước là "Cannot declare class Logger, because
the name is already in use".)

Hai class không liên quan gì nhau, chỉ trùng tên, mà chương trình không chạy được. Bạn không sửa được
code của thư viện, và thư viện cũng không thể biết trước mọi cái tên mà mọi ứng dụng trên thế giới
sẽ dùng. Ngoài ra, PHP có sẵn hàng nghìn hàm và class (`Exception`, `DateTime`, `Iterator`,
`strlen`...), và bản PHP sau có thể thêm tên mới trùng với tên bạn đang dùng.

### 1.2 Cách làm trước khi có namespace: tiền tố dài

Namespace có từ PHP 5.3 (2009). Trước đó, cộng đồng tránh trùng tên bằng quy ước: gắn tên nhà cung cấp
và đường dẫn vào chính tên class, phân cách bằng dấu gạch dưới. Đây là kiểu của PEAR và Zend Framework 1,
ví dụ `Zend_Db_Table_Abstract`, `PHPUnit_Framework_TestCase`.

Cách này tránh được trùng tên nhưng có hai cái giá:

- Tên dài, phải gõ đầy đủ ở mọi chỗ dùng: `new Zend_Db_Table_Abstract(...)`, `extends
  PHPUnit_Framework_TestCase`.
- Không có cách nào viết tắt. Muốn đổi thư viện thì phải sửa tên ở mọi chỗ.

Manual PHP nói đúng hai vấn đề này khi giới thiệu namespace: tránh xung đột tên giữa code của bạn, code
có sẵn của PHP và code của bên thứ ba; và cho phép đặt alias (viết tắt) cho những cái tên dài vốn sinh ra
để tránh xung đột.

### 1.3 Namespace: "thư mục" cho tên

*Namespace* (không gian tên) là một cách nhóm các tên lại dưới một tên chung, giống thư mục nhóm các
file. Hai file cùng tên `foo.txt` không cùng nằm được trong một thư mục, nhưng nằm ở `/home/an/foo.txt` và
`/home/binh/foo.txt` thì được. Tương tự, hai class cùng tên `Logger` nằm được trong cùng một chương trình
nếu chúng thuộc hai namespace khác nhau:

```
App\Logging\Logger          ← Logger của ứng dụng
Mailer\Logging\Logger       ← Logger của thư viện email
```

Tên đầy đủ, gồm cả namespace, gọi là *fully qualified name* (tên đầy đủ). Với class, người ta hay viết
tắt là *FQCN* (fully qualified class name). PHP dùng dấu gạch chéo ngược `\` làm dấu phân cách, gọi là
*namespace separator*.

Chương trình ở mục 1.1 sửa lại: mỗi file khai báo một namespace ở đầu file.

```php
<?php
// app-logger.php
declare(strict_types=1);

namespace App\Logging;

class Logger
{
    public function log(string $msg): void { echo "[app] $msg\n"; }
}
```

```php
<?php
// lib-logger.php
declare(strict_types=1);

namespace Mailer\Logging;

class Logger
{
    public function write(string $msg): void { echo "[lib] $msg\n"; }
}
```

```php
<?php
// main.php
declare(strict_types=1);

require __DIR__ . '/app-logger.php';
require __DIR__ . '/lib-logger.php';

(new \App\Logging\Logger())->log('xin chào');        // in ra: [app] xin chào
(new \Mailer\Logging\Logger())->write('xin chào');   // in ra: [lib] xin chào
```

Hai class giờ là hai tên khác nhau: `App\Logging\Logger` và `Mailer\Logging\Logger`. Dấu `\` đứng đầu
`\App\Logging\Logger` nghĩa là "tính từ gốc", giống `/` ở đầu đường dẫn tuyệt đối; mục 3 giải thích.

### 1.4 Namespace tác động lên những gì

Theo manual, namespace chỉ ảnh hưởng tới sáu loại tên:

| Chịu ảnh hưởng của namespace | Không chịu ảnh hưởng |
|---|---|
| class (kể cả abstract class), interface, trait, enum | biến (`$x`), kể cả biến toàn cục |
| hàm (function) | method, property, hằng class (chúng thuộc về class, class đã có namespace) |
| hằng khai báo bằng `const` ở cấp file | hằng tạo bằng `define('X', ...)` với tên không ghi namespace (Chương 03, mục về hằng) |

Biến không có namespace: `$config` trong file có `namespace App;` vẫn là `$config`. Hằng `define()` là
trường hợp dễ nhầm: `define()` nhận tên dạng chuỗi và không tự gắn namespace hiện tại
([Chương 03](03-cu-phap-bien-hang.md) đã nói; muốn hằng nằm trong namespace thì dùng `const`).

⚠️ Namespace chỉ là một phần của **tên**. Nó không tạo ra phạm vi truy cập như `private` hay `package`
của Java: code ở namespace nào cũng dùng được class ở namespace khác, miễn là gọi đúng tên. Nó cũng không
liên quan gì tới thư mục trên đĩa; việc đặt file `App\Models\User` vào `app/Models/User.php` là quy ước
của autoloader (mục 7), không phải yêu cầu của ngôn ngữ.

## 2. Khai báo namespace

### 2.1 Cú pháp và vị trí

```php
<?php
declare(strict_types=1);

namespace Shop\Billing;

const TAX_RATE = 10;

class Invoice {}

function total(int $amount): int
{
    return $amount + intdiv($amount * TAX_RATE, 100);
}

echo Invoice::class, "\n";          // in ra: Shop\Billing\Invoice
echo __NAMESPACE__, "\n";           // in ra: Shop\Billing
echo total(1000), "\n";             // in ra: 1100
```

Khai báo `namespace Shop\Billing;` khiến mọi class, interface, trait, enum, hàm, hằng `const` khai báo
sau nó trong file nhận tên đầy đủ có tiền tố `Shop\Billing\`: class `Shop\Billing\Invoice`, hàm
`Shop\Billing\total`, hằng `Shop\Billing\TAX_RATE`. `X::class` cho ra tên đầy đủ của class dưới dạng
chuỗi; `__NAMESPACE__` cho ra tên namespace hiện tại (chuỗi rỗng nếu ở ngoài mọi namespace).

Quy tắc vị trí:

- `namespace` phải là câu lệnh **đầu tiên** của file. Ngoại lệ duy nhất là `declare` (ví dụ
  `declare(strict_types=1);`), được đứng trước. Comment đứng trước thì không sao.
- Không được có output nào trước nó, kể cả một dấu cách hay dòng trống trước thẻ `<?php`.

```php
<?php
declare(strict_types=1);

echo "xin chào\n";
namespace App;
```

```
Fatal error: Namespace declaration statement has to be the very first statement or after any declare call in the script in /app/nsfirst.php on line 5
```

Thử thêm một dấu cách trước `<?php` (file bắt đầu bằng `" <?php"`): cùng lỗi trên, vì dấu cách đó là
output HTML nằm trước khai báo.

Thứ tự chuẩn ở đầu một file PHP hiện đại, như [Chương 01](01-php-la-gi.md) đã giới thiệu: thẻ mở,
`declare`, `namespace`, các dòng `use` (mục 4), rồi tới code.

### 2.2 Namespace con chỉ là tên dài hơn

`Shop\Billing` trông như "namespace `Billing` nằm trong namespace `Shop`", và người ta gọi nó là
*sub-namespace* (namespace con). Nhưng với PHP, đó chỉ là một chuỗi tên có dấu `\`. Không có đối tượng
"namespace `Shop`" nào được tạo ra, không cần khai báo `namespace Shop;` ở đâu cả, và code trong
`Shop\Billing` không có quyền gì đặc biệt với `Shop`.

Hệ quả thực tế: bạn đặt cấp bậc namespace theo cách tổ chức code (thường bám theo thư mục), không phải
vì ngôn ngữ đòi hỏi.

### 2.3 Một namespace nhiều file, nhiều namespace một file

Cùng một namespace được khai báo ở bao nhiêu file cũng được. Đây là cách dùng bình thường: mọi model của
Laravel nằm trong `App\Models`, mỗi model một file.

Ngược lại, một file có thể chứa nhiều namespace. Manual cho hai cú pháp, và khuyên nếu bắt buộc phải gộp
thì dùng cú pháp ngoặc nhọn:

```php
<?php
declare(strict_types=1);

namespace Shop\Billing {
    class Invoice {}
}

namespace Shop\Shipping {
    class Invoice {}               // cùng tên Invoice nhưng khác namespace: hợp lệ
}

namespace {                        // namespace không tên = namespace toàn cục
    echo Shop\Billing\Invoice::class, "\n";    // in ra: Shop\Billing\Invoice
    echo Shop\Shipping\Invoice::class, "\n";   // in ra: Shop\Shipping\Invoice
}
```

- Dùng cú pháp ngoặc thì mọi code phải nằm trong một khối `namespace ... { }`; code toàn cục đặt trong
  `namespace { }` (không tên). Chỉ `declare` được đứng ngoài, ở đầu file.
- Không được lồng khối namespace này trong khối namespace khác.
- Manual nói rõ việc gộp nhiều namespace vào một file "strongly discouraged" (rất không nên) trong code
  thường; trường hợp dùng chính là gộp nhiều file thành một.

Trong chương này, một số ví dụ dùng cú pháp ngoặc để gói nhiều namespace vào một file cho tiện chạy thử.
Code thật: **một file, một namespace, một class**. Autoloader (mục 6, 7) dựa vào quy ước đó.

### 2.4 Namespace toàn cục

File không có khai báo `namespace` thì mọi thứ trong đó thuộc *global namespace* (namespace toàn cục),
giống PHP trước 5.3. Mọi hàm, class, hằng có sẵn của PHP (`strlen`, `Exception`, `PHP_VERSION`...) đều
nằm ở namespace toàn cục, trừ phần nhỏ đã được đưa vào namespace riêng như `Random\Randomizer`
(PHP 8.2) hay `Dom\HTMLDocument` (PHP 8.4).

Tên của một thứ ở namespace toàn cục khi viết đầy đủ là `\Exception`, `\strlen`: dấu `\` đứng đầu và
không có gì khác.

### 2.5 Quy tắc đặt tên namespace

- Tên namespace **không phân biệt hoa thường** (*case-insensitive*), giống tên class và tên hàm.
  `\app\models\USER` và `\App\Models\User` chỉ cùng một class. Hằng thì khác: phần namespace không phân
  biệt hoa thường, nhưng phần tên hằng thì có.

```php
<?php
declare(strict_types=1);

namespace App\Config;

const Region = 'vn';

class User {}

$u = new \app\config\USER();
echo get_class($u), "\n";                   // in ra: App\Config\User (tên lúc khai báo)
echo \app\config\Region, "\n";              // in ra: vn
echo \APP\CONFIG\user::class, "\n";         // in ra: APP\CONFIG\user
try {
    echo \App\Config\REGION, "\n";
} catch (\Error $e) {
    echo $e->getMessage(), "\n";            // in ra: Undefined constant "App\Config\REGION"
}
```

  Dòng `::class` in ra đúng như bạn gõ, vì `::class` chỉ là phép biến đổi tên lúc biên dịch, không tra
  xem class có tồn tại không (mục 3.6). ⚠️ "Không phân biệt hoa thường" chỉ đúng với engine. Autoloader
  đổi tên thành đường dẫn file, và filesystem trên Linux phân biệt hoa thường; viết sai hoa thường là
  nguồn lỗi kinh điển "máy tôi chạy, server không chạy" (mục 7.5). Luôn viết đúng như lúc khai báo.
- Namespace `PHP` và mọi tên bắt đầu bằng `PHP\` được manual dành riêng cho ngôn ngữ, code của bạn không
  nên dùng. (PHP không báo lỗi khi bạn dùng, đó là quy ước.)
- Từ PHP 8.0, tên có namespace được tokenizer coi là **một token** (RFC "Treat namespaced names as single
  token"). Hai hệ quả:
  - Một đoạn của tên được phép trùng từ khoá: `namespace App\List\Match;` hợp lệ trên 8.0+, còn PHP 7.4
    báo `syntax error, unexpected 'List' (T_LIST)`. Tên class thì vẫn không được là từ khoá: `class List`
    vẫn lỗi.
  - Không được có khoảng trắng hay comment giữa các đoạn: `Foo \ Bar` là lỗi cú pháp.
- Không viết dấu `\` ở đầu tên trong khai báo: `namespace \App;` là sai (manual: tên đầy đủ không được
  phép trong khai báo namespace).

### 2.6 Từ khoá `namespace\` và `__NAMESPACE__`

Ngoài việc khai báo, từ khoá `namespace` còn dùng như một tiền tố nghĩa là "namespace hiện tại", tương
tự `self` cho class. Manual gọi dạng này là *relative name* (tên tương đối).

```php
<?php
declare(strict_types=1);

namespace Shop;

function hello(): string { return __FUNCTION__; }

echo namespace\hello(), "\n";        // in ra: Shop\hello
echo __NAMESPACE__ . '\Cart', "\n";  // in ra: Shop\Cart (ghép chuỗi tên lúc chạy)
```

`namespace\hello()` hiếm gặp trong code thật; `__NAMESPACE__` hay gặp hơn khi cần ghép tên class thành
chuỗi lúc chạy (mục 3.6).

## 3. Gọi một cái tên: PHP phân giải ra sao

### 3.1 Ba dạng tên, so với đường dẫn file

Manual so sánh với cách gọi file: `foo.txt` (tên file, tính từ thư mục hiện tại), `sub/foo.txt` (đường
dẫn tương đối), `/main/foo.txt` (đường dẫn tuyệt đối). Tên trong PHP có ba dạng tương ứng:

| Dạng | Ví dụ | Giống đường dẫn | Ở trong `namespace Shop;` thì thành |
|---|---|---|---|
| *Unqualified name* (tên trơn) | `Invoice` | `foo.txt` | `Shop\Invoice` (với class) |
| *Qualified name* (tên có tiền tố) | `Billing\Invoice` | `sub/foo.txt` | `Shop\Billing\Invoice` |
| *Fully qualified name* (tên đầy đủ) | `\Billing\Invoice` | `/main/foo.txt` | `Billing\Invoice`, đúng như viết |

Thêm dạng thứ tư ít gặp là *relative name* `namespace\Invoice` (mục 2.6).

Bảng trên là quy tắc **khi không có `use`**. Mục 4 thêm bước tra bảng import vào giữa.

### 3.2 Class luôn được tìm trong namespace hiện tại

Với tên của class (và interface, trait, enum), quy tắc rất cứng: tên trơn hoặc tên có tiền tố mà không
khớp `use` nào thì **ghép namespace hiện tại vào trước**. Không có bước "thử ở namespace toàn cục".

```php
<?php
declare(strict_types=1);

namespace App\Util;

try {
    $d = new DateTime('2026-01-01');      // PHP tìm App\Util\DateTime
} catch (\Error $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
    // in ra: Error: Class "App\Util\DateTime" not found
}

$d = new \DateTime('2026-01-01');         // \ ở đầu: lấy DateTime ở namespace toàn cục
echo $d->format('Y'), "\n";               // in ra: 2026
```

Có hai cách đúng để dùng class có sẵn của PHP trong namespace: viết `\DateTime`, hoặc `use DateTime;` ở
đầu file rồi viết `DateTime` (mục 4). Dự án dùng Laravel thường theo cách thứ hai.

Vì sao class không được "thử ở namespace toàn cục"? Manual chỉ nêu quy tắc, không giải thích lý do. Thảo
luận lúc thiết kế PHP 5.3 cho thấy một vấn đề liên quan tới *autoload* (mục 6). Trong bản phát triển năm
2008, class tên trơn từng được thử thêm class có sẵn của PHP, và RFC
["Namespace Issues"](https://wiki.php.net/rfc/namespaceissues) (Greg Beaver) chỉ ra chỗ vướng: trong
namespace `blah`, nếu `blah\Exception` chưa được nạp thì `new Exception()` lấy luôn `\Exception` có sẵn
và không bao giờ gọi autoload cho `blah\Exception`; còn nếu file định nghĩa `blah\Exception` đã được nạp
từ trước thì lại ra class đó. Cùng một dòng code chỉ tới hai class khác nhau tuỳ thứ tự nạp file. Quy tắc
cứng cho class (bản PHP 5.3 phát hành dùng quy tắc này) tránh được chuyện đó.

### 3.3 Bẫy kinh điển: `catch (Exception $e)` trong namespace

Hệ quả của mục 3.2 mà gần như ai học PHP cũng dính một lần:

```php
<?php
declare(strict_types=1);

namespace App\Service;

function chia(int $a, int $b): int
{
    if ($b === 0) {
        throw new \InvalidArgumentException('b = 0');
    }
    return intdiv($a, $b);
}

try {
    echo chia(1, 0), "\n";
} catch (Exception $e) {          // ⚠️ thiếu \ hoặc use: đây là App\Service\Exception
    echo "bắt được: ", $e->getMessage(), "\n";
}
echo "không tới đây\n";
```

```
Fatal error: Uncaught InvalidArgumentException: b = 0 in /app/catchtrap.php:9
```

`catch (Exception $e)` ở đây bắt class `App\Service\Exception`, một class không hề tồn tại. PHP không
báo lỗi "class không tồn tại" cho tên trong `catch`: nó chỉ kiểm tra exception đang bay có phải
`instanceof` tên đó không, câu trả lời là không, nên exception đi tiếp và làm chết chương trình. Lỗi
không lộ ra cho tới khi exception thật sự xảy ra, thường là trên production. Sửa: `catch (\Exception $e)`
hoặc thêm `use Exception;`. Type hint cũng vậy: `function f(DateTime $d)` trong namespace `App` nghĩa là
`App\DateTime`, và lỗi chỉ hiện ra khi hàm được gọi. Công cụ phân tích tĩnh (PHPStan, Psalm,
[Chương 21](21-chat-luong-code.md)) và IDE bắt được lỗi này ngay khi bạn gõ.

### 3.4 Hàm và hằng: có bước dự phòng về namespace toàn cục

Với hàm và hằng, quy tắc khác class. Gặp một tên **trơn** (không có `\`) trong namespace, PHP:

1. Thử tên trong namespace hiện tại.
2. Nếu không có, dùng tên ở namespace toàn cục.

Bước 2 gọi là *fallback to global* (dự phòng về toàn cục). Nhờ nó, code trong namespace vẫn gọi
`strlen()`, `count()`, `PHP_EOL` mà không cần viết `\`.

```php
<?php
declare(strict_types=1);

namespace App\Util;

const E_ERROR = 45;                 // hằng App\Util\E_ERROR, che hằng E_ERROR có sẵn

function strlen(string $s): int     // hàm App\Util\strlen, che strlen có sẵn
{
    return \strlen($s) - 1;         // \strlen: gọi thẳng hàm toàn cục
}

echo E_ERROR, "\n";       // in ra: 45   (tìm thấy App\Util\E_ERROR)
echo INI_ALL, "\n";       // in ra: 7    (không có App\Util\INI_ALL, dùng \INI_ALL)
echo strlen('hi'), "\n";  // in ra: 1    (tìm thấy App\Util\strlen)
echo \strlen('hi'), "\n"; // in ra: 2
```

Lưu ý:

- Fallback chỉ áp dụng cho tên **trơn**. Tên có `\` (`Util\foo()`, `\foo()`) được phân giải một lần, không
  thử lại. Hằng có `\` mà không tồn tại thì ném `Error: Undefined constant "..."`.
- Đây là lý do [Chương 08](08-ham.md) nói được phép đặt hàm trùng tên với hàm có sẵn khi ở trong
  namespace: `App\Util\strlen` và `\strlen` là hai tên khác nhau.

### 3.5 Fallback có giá: phân giải lúc chạy và opcode chuyên biệt

Vì hàm `App\Util\strlen` có thể được định nghĩa vào **bất cứ lúc nào** (ở một file `require` sau), khi
biên dịch một lời gọi `strlen($s)` trong namespace, trình biên dịch không biết nó sẽ trỏ tới hàm nào. Nó
phải sinh lệnh "tìm hàm theo tên lúc chạy, có dự phòng". Còn khi bạn viết `\strlen($s)`, hoặc import bằng
`use function strlen;`, trình biên dịch biết chắc đó là hàm có sẵn, và với một số hàm như `strlen`,
`count`, `is_int` nó thay lời gọi bằng một opcode riêng, nhanh hơn
([Chương 02](02-php-chay-nhu-the-nao.md) giải thích opcode là gì).

Xem bằng chứng: in opcode của file sau bằng OPcache (lệnh chạy ở thư mục chứa file, cần PHP có OPcache):

```php
<?php
declare(strict_types=1);

namespace App;

function a(string $s): int { return strlen($s); }
function b(string $s): int { return \strlen($s); }
```

```bash
php -d opcache.enable_cli=1 -d opcache.opt_debug_level=0x10000 opc.php
```

Phần liên quan trong output (PHP 8.5, đã lược các dòng khác):

```
App\a:
0000 CV0($s) = RECV 1
0001 INIT_NS_FCALL_BY_NAME 1 string("App\\strlen")
0002 SEND_VAR_EX CV0($s) 1
0003 V1 = DO_FCALL_BY_NAME
...
App\b:
0000 CV0($s) = RECV 1
0001 T1 = STRLEN CV0($s)
...
```

Hàm `a` (gọi `strlen` trơn) cần ba lệnh: chuẩn bị lời gọi theo tên `App\strlen` có dự phòng, truyền tham
số, gọi. Hàm `b` (gọi `\strlen`) chỉ có một opcode `STRLEN`. Thêm `use function strlen;` ở đầu file thì
hàm `a` cũng ra `STRLEN`.

Hai điều nên biết thêm:

- Kết quả phân giải lúc chạy được nhớ lại (cache) tại từng chỗ gọi. Lần đầu chỗ gọi đó chạy, PHP tìm
  `App\strlen`, không thấy, dùng `\strlen` và ghi nhớ; những lần sau không tìm lại nữa. Vì vậy chi phí
  thật sự không lớn, và không phải dự án nào cũng cần viết `\` trước mọi hàm. Một số dự án (và công cụ như
  PHP-CS-Fixer với rule `native_function_invocation`) chọn làm vậy; [Chương 20](20-hieu-nang.md) bàn về
  việc có đáng không.
- Kỹ thuật "che hàm có sẵn" được dùng thật trong test (ví dụ `ClockMock` của Symfony PHPUnit Bridge):
  thư viện test định nghĩa hàm `App\Billing\time()` để code gọi `time()` trong `App\Billing` nhận thời
  gian giả. Nhưng vì cái cache vừa nói, hàm giả phải được
  định nghĩa **trước** lần đầu chỗ gọi chạy. Thử nghiệm (ba file):

```
mock/
├── code.php
├── mock.php
└── main.php
```

```php
<?php
// code.php
declare(strict_types=1);

namespace App\Billing;

function now(): int { return time(); }   // time() trơn: phân giải lúc chạy
```

```php
<?php
// mock.php
declare(strict_types=1);

namespace App\Billing;

function time(): int { return 42; }      // hàm giả, che \time trong App\Billing
```

```php
<?php
// main.php
declare(strict_types=1);

require __DIR__ . '/code.php';
echo \App\Billing\now() === 42 ? "giả\n" : "thật\n";   // in ra: thật
require __DIR__ . '/mock.php';
echo \App\Billing\now() === 42 ? "giả\n" : "thật\n";   // in ra: thật (chỗ gọi đã nhớ \time)
```

Đảo hai dòng `require` lên trước lời gọi đầu tiên thì kết quả là `giả`. Ngược lại, code viết `\time()` thì
không giả lập được bằng cách này (docs Symfony PHPUnit Bridge cảnh báo đúng điều đó): một cái giá nhỏ của
thói quen viết `\` trước mọi hàm.

### 3.6 Tên trong chuỗi luôn là tên đầy đủ; `::class` không nạp gì

Tên viết thẳng trong code được phân giải **lúc biên dịch** theo namespace và `use` của file. Tên nằm
trong chuỗi (`new $ten`, `$tenHam()`, `class_exists($ten)`, `constant($ten)`, tên class trong config) thì
chỉ được biết **lúc chạy**, khi đó PHP không còn biết file đang ở namespace nào hay có `use` gì. Vì vậy:

- Tên trong chuỗi luôn được hiểu là tên đầy đủ, không áp dụng `use`, không ghép namespace hiện tại.
- Dấu `\` ở đầu là tuỳ chọn: `'\App\Models\User'` và `'App\Models\User'` như nhau.
- Trong chuỗi nháy kép, `\` là ký tự escape: `"App\Models\name"` chứa `\n` là ký tự xuống dòng. Dùng nháy
  đơn, hoặc tốt hơn nữa là `User::class`.

```php
<?php
declare(strict_types=1);

namespace App\Http;

use App\Models\User as Member;

spl_autoload_register(function (string $class): void {   // autoloader chỉ in ra tên được hỏi (mục 6)
    echo "[autoload] ", $class, "\n";
});

echo Member::class, "\n";                  // in ra: App\Models\User   (không có dòng [autoload])

var_dump(class_exists('Member'));          // in ra: [autoload] Member, rồi bool(false)
var_dump(class_exists('App\Models\User')); // in ra: [autoload] App\Models\User, rồi bool(false)
var_dump(class_exists('\App\Models\User'));// in ra: [autoload] App\Models\User, rồi bool(false)
```

Ba điều rút ra:

- `Member::class` được thay bằng chuỗi `'App\Models\User'` ngay lúc biên dịch, theo bảng `use`. Nó không
  kiểm tra class có tồn tại không, không gọi autoloader. Đó là lý do cách viết `User::class` an toàn và
  được dùng khắp nơi trong Laravel (khai báo route, binding container, relationship).
- `'Member'` trong chuỗi là class `\Member` ở namespace toàn cục, alias không có tác dụng.
- `'\App\Models\User'` được bỏ dấu `\` đầu trước khi chuyển cho autoloader.

Quy tắc thực dụng: hễ cần tên class dạng chuỗi, viết `X::class` thay vì gõ chuỗi tay. IDE và công cụ phân
tích tĩnh hiểu được `X::class`, đổi tên class thì nó đổi theo; chuỗi gõ tay thì không.

## 4. `use`: import và alias

### 4.1 Vì sao cần `use`

Gõ `\Shop\Billing\Invoice` ở mọi chỗ dùng thì an toàn nhưng dài, và nếu một ngày class chuyển namespace
thì phải sửa khắp nơi. Câu lệnh `use` ở đầu file khai báo "trong file này, tên ngắn `Invoice` nghĩa là
`Shop\Billing\Invoice`". Manual gọi việc này là *importing* (import) hoặc *aliasing* (đặt alias), và so
sánh nó với symbolic link trên Unix: tạo một tên ngắn trỏ tới tên thật.

### 4.2 Các dạng `use`

Ví dụ gói nhiều namespace vào một file (cú pháp ngoặc, mục 2.3) để chạy được ngay:

```php
<?php
declare(strict_types=1);

namespace Shop\Billing {
    class Invoice
    {
        public function __construct(public readonly int $total) {}
    }
}

namespace Shop\Support {
    const CURRENCY = 'VND';

    function money(int $amount): string
    {
        return number_format($amount, 0, ',', '.') . ' ' . CURRENCY;
    }
}

namespace Vendor\Logging {
    class Logger
    {
        public function log(string $msg): void { echo "[vendor] $msg\n"; }
    }
}

namespace Shop\Logging {
    class Logger
    {
        public function log(string $msg): void { echo "[shop] $msg\n"; }
    }
}

namespace Shop\Http {
    use Shop\Billing\Invoice;                  // import class
    use Shop\Logging\Logger;                   // import class
    use Vendor\Logging\Logger as VendorLogger; // alias vì trùng tên Logger
    use Shop\Billing;                          // import namespace
    use function Shop\Support\money;           // import hàm
    use const Shop\Support\CURRENCY;           // import hằng

    $inv = new Invoice(1500000);
    echo money($inv->total), "\n";             // in ra: 1.500.000 VND
    echo CURRENCY, "\n";                       // in ra: VND

    (new Logger())->log('đã tạo hoá đơn');     // in ra: [shop] đã tạo hoá đơn
    (new VendorLogger())->log('cùng tên');     // in ra: [vendor] cùng tên

    $inv2 = new Billing\Invoice(10);           // Billing\ được thay bằng Shop\Billing\
    echo get_class($inv2), "\n";               // in ra: Shop\Billing\Invoice
    echo VendorLogger::class, "\n";            // in ra: Vendor\Logging\Logger
}
```

Giải thích từng dạng:

| Câu lệnh | Tạo ra tên ngắn | Dùng cho |
|---|---|---|
| `use Shop\Billing\Invoice;` | `Invoice` (đoạn cuối của tên) | class, interface, trait, enum |
| `use Vendor\Logging\Logger as VendorLogger;` | `VendorLogger` | Như trên, khi tên cuối bị trùng hoặc quá chung chung |
| `use Shop\Billing;` | `Billing` dùng làm **tiền tố**: `Billing\Invoice` | Một namespace, khi dùng nhiều class trong đó |
| `use function Shop\Support\money;` | Hàm `money()` | Hàm |
| `use const Shop\Support\CURRENCY;` | Hằng `CURRENCY` | Hằng |

Vài điều cần để ý:

- Tên trong `use` luôn được hiểu là tên đầy đủ, nên không cần (và manual khuyên không nên) viết `\` ở đầu:
  `use App\Models\User;`, không phải `use \App\Models\User;`.
- `use` cho class và `use` cho namespace có cùng cú pháp. `use Shop\Billing;` không "biết" `Shop\Billing`
  là namespace hay class; nó chỉ tạo tên ngắn `Billing`. Viết `new Billing()` thì PHP tìm class
  `Shop\Billing`, viết `new Billing\Invoice()` thì tìm `Shop\Billing\Invoice`.
- Class ở namespace toàn cục cũng import được: `use DateTime;`, `use Exception;`. Manual gọi đây là
  "importing a global class". Trong file không có namespace thì dòng đó vô nghĩa (và PHP báo warning
  "The use statement with non-compound name ... has no effect").
- Viết nhiều tên trong một câu `use` bằng dấu phẩy được (`use A\B, C\D;`), nhưng hiếm gặp trong code
  hiện đại: người ta viết mỗi dòng một `use`, hoặc dùng group use (mục 4.3).

### 4.3 Group use

Import nhiều tên cùng một tiền tố có thể gộp bằng ngoặc nhọn (PHP 7.0):

```php
use Shop\Billing\{Invoice, Payment, Refund as RefundRecord};
use function Shop\Support\{money, percent};
use const Shop\Support\{CURRENCY, TAX_RATE};
```

tương đương bảy dòng `use` riêng. Nhiều dự án vẫn chọn viết mỗi dòng một tên vì diff trong git dễ đọc
hơn; cả hai đều hợp lệ, và ví dụ mẫu của PSR-12 dùng cả group use.

### 4.4 Quy tắc của `use`

**1. `use` chạy lúc biên dịch, theo từng file.** Bảng alias được dựng khi PHP biên dịch file, áp dụng
cho phần còn lại của file đó (hoặc khối `namespace { }` đó). File được `require` từ file này không thừa
hưởng các `use` của nó; manual ghi rõ "importing rules are per file basis". Vì là lúc biên dịch, `use`
không có tác dụng với tên trong chuỗi (mục 3.6).

**2. `use` chỉ được đặt ở cấp ngoài cùng của file hoặc của khối namespace**, không được đặt trong hàm,
trong `if`, trong class:

```php
<?php
declare(strict_types=1);

namespace Languages;

function toGreenlandic(): void
{
    use Languages\Danish;
}
```

```
Parse error: syntax error, unexpected token "use" in /app/usefn.php on line 8
```

(Từ khoá `use` bên trong thân class là chuyện khác: đó là dùng trait, [Chương 09](09-oop-co-ban.md).
`use` sau `function (...)` là bắt biến cho closure, [Chương 08](08-ham.md). Ba nghĩa, một từ khoá.)

**3. `use` không nạp gì cả.** Nó chỉ ghi vào bảng alias. `use` một class không tồn tại không gây lỗi;
lỗi chỉ xảy ra khi bạn thật sự dùng tên đó (tạo object, gọi static method...).

```php
<?php
declare(strict_types=1);

namespace App;

use Khong\Ton\Tai;
use function Khong\ham;

echo "use một tên không tồn tại: không lỗi\n";   // in ra dòng này bình thường
```

Hệ quả hay: một file có hai mươi dòng `use` không làm chậm gì, vì không có class nào được nạp chỉ vì dòng
`use`. Hệ quả cần cẩn thận: `use` gõ sai tên không bị phát hiện cho tới khi chạy tới chỗ dùng (lại là
việc của IDE và PHPStan).

**4. Một tên ngắn chỉ trỏ tới một thứ.**

```php
use Foo\Logger;
use Bar\Logger;      // Fatal error: Cannot use Bar\Logger as Logger because the name is already in use
```

Alias cũng không được trùng tên một class khai báo trong cùng file:

```php
<?php
declare(strict_types=1);

namespace My\Stuff;

use Another\Thing as MyClass;

class MyClass {}
```

PHP 8.5 báo `Fatal error: Cannot redeclare class My\Stuff\MyClass (previously declared as local import)`
(PHP 8.3 báo "Cannot declare class My\Stuff\MyClass because the name is already in use"). Nếu class
`My\Stuff\MyClass` nằm ở **file khác** thì không xung đột: trong file này `MyClass` nghĩa là
`Another\Thing`, hết.

**5. Bảng import của class, hàm và hằng là ba bảng riêng.** `use Foo\bar;` (không có `function`) không
import hàm `Foo\bar()`. Lời gọi hàm `bar()` chỉ nhìn bảng của `use function`.

### 4.5 Thuật toán phân giải tên đầy đủ

Gộp mục 3 và 4, đây là cách PHP biến một tên trong code thành tên đầy đủ (theo trang "Name resolution
rules" của manual):

```
Tên bắt đầu bằng \ (fully qualified)
    → bỏ dấu \ đầu, xong. \A\B thành A\B

Tên bắt đầu bằng namespace\ (relative)
    → thay "namespace" bằng namespace hiện tại

Tên có \ ở giữa (qualified), ví dụ C\D\E
    → đoạn đầu "C" có trong bảng import class/namespace?
          có:    thay C bằng tên đã import    (use A\B\C;  →  A\B\C\D\E)
          không: ghép namespace hiện tại vào trước

Tên trơn (unqualified), ví dụ Foo
    → tra bảng import ứng với loại tên (class / function / const)
          có:    dùng tên đã import
          không, và là class/interface/trait/enum:
                 ghép namespace hiện tại → nếu chưa nạp thì gọi autoload → không có thì Error
          không, và là hàm hoặc hằng, ở trong một namespace:
                 lúc chạy: thử Namespace\Foo, không có thì dùng \Foo
```

Ví dụ của manual, trong `namespace A;` với `use B\D, C\E as F;`:

| Code | Phân giải thành |
|---|---|
| `foo();` | thử `A\foo()`, không có thì `\foo()` |
| `\foo();` | `foo()` toàn cục |
| `my\foo();` | `A\my\foo()` |
| `F();` | thử `A\F()`, rồi `\F()` (alias `F` là của bảng class, không áp dụng cho hàm) |
| `new B();` | `A\B` |
| `new D();` | `B\D` (theo `use`) |
| `new F();` | `C\E` (theo alias) |
| `new \F();` | `F` toàn cục |
| `B\foo();` | `A\B\foo()` |
| `D::foo();` | method `foo` của class `B\D` |
| `A\B::foo();` | method `foo` của class `A\A\B` (`A\B` là tên có tiền tố, bị ghép thêm `A\`) |

Dòng cuối là cái bẫy nhỏ: trong `namespace A;`, viết `A\B` không có nghĩa là `\A\B` mà là `\A\A\B`.

### 4.6 Quy ước trong dự án thật

- Mỗi file một namespace, khai báo ngay sau `declare(strict_types=1);`.
- Namespace bám theo thư mục (để autoloader tìm được, mục 7): file `app/Http/Controllers/UserController.php`
  có `namespace App\Http\Controllers;`.
- Mọi class dùng trong file đều `use` ở đầu, kể cả class toàn cục như `Exception`, `DateTimeImmutable`
  (một số đội thích `\Exception` thay vì `use`; chọn một kiểu và giữ nhất quán, thường do công cụ format
  code quyết định).
- PSR-12 và PER Coding Style quy định thứ tự: các `use` class trước, rồi `use function`, rồi `use const`,
  mỗi nhóm cách nhau một dòng trống. Không cần nhớ: Laravel Pint, PHP-CS-Fixer tự sắp xếp
  ([Chương 21](21-chat-luong-code.md)).
- Đặt alias khi trùng tên, và đặt tên alias nói lên nguồn gốc: `use Illuminate\Http\Request;` cùng
  `use Psr\Http\Message\ServerRequestInterface as PsrRequest;`.

## 5. Nạp code từ file khác: `include` và `require`

Namespace giải quyết chuyện **tên**. Còn một chuyện khác: code nằm ở nhiều file, làm sao để file này
dùng được class khai báo ở file kia? PHP không tự đi tìm file. Mỗi lần chạy, engine chỉ biết file bạn
gọi trực tiếp; muốn dùng file khác thì phải nạp nó vào.

### 5.1 Bốn cấu trúc nạp file

PHP có bốn *language construct* (cấu trúc của ngôn ngữ, không phải hàm, nên không bắt buộc có ngoặc)
để nạp và chạy một file khác ngay tại chỗ:

| Cấu trúc | Không tìm thấy file | Nạp lại file đã nạp |
|---|---|---|
| `include` | `E_WARNING`, trả `false`, chạy tiếp | Có, nạp lại |
| `require` | Ném `Error` (trước PHP 8.0 là fatal error `E_COMPILE_ERROR`) | Có, nạp lại |
| `include_once` | Như `include` | Không, bỏ qua và trả `true` |
| `require_once` | Như `require` | Không, bỏ qua và trả `true` |

Ví dụ với ba file:

```
inc/
├── config.php
├── helpers.php
└── main.php
```

```php
<?php
// config.php: file có thể trả về một giá trị bằng return
declare(strict_types=1);

return [
    'db_host' => '127.0.0.1',
    'debug'   => true,
];
```

```php
<?php
// helpers.php
declare(strict_types=1);

echo "[đang nạp helpers.php]\n";

function chao(string $ten): string
{
    return "Xin chào, $ten";
}
```

```php
<?php
// main.php
declare(strict_types=1);

$config = require __DIR__ . '/config.php';      // nhận giá trị mà config.php return
var_dump($config['debug']);                      // in ra: bool(true)

require_once __DIR__ . '/helpers.php';           // in ra: [đang nạp helpers.php]
$lan2 = require_once __DIR__ . '/helpers.php';   // đã nạp rồi: bỏ qua, không in gì
var_dump($lan2);                                 // in ra: bool(true)
echo chao('An'), "\n";                           // in ra: Xin chào, An

$kq = @include __DIR__ . '/khong-co.php';        // include hụt: warning (bị @ nuốt), trả false
var_dump($kq);                                   // in ra: bool(false)
```

Những điều cần biết:

- File được nạp **chạy ngay** tại dòng `include`/`require`, như thể code của nó được dán vào đó. Code
  ở cấp ngoài cùng của file (như dòng `echo` trong `helpers.php`) chạy; hàm và class khai báo trong file
  được đăng ký và dùng được từ đó về sau. Biến của file được nạp dùng chung *scope* (phạm vi biến) với
  dòng gọi; hàm và class thì luôn ở phạm vi toàn cục.
- File được nạp bắt đầu ở chế độ HTML: code PHP trong đó phải nằm trong thẻ `<?php`. `declare(strict_types=1)`
  chỉ có hiệu lực cho file chứa nó, mỗi file phải tự khai báo ([Chương 04](04-kieu-du-lieu.md)).
- File có thể `return` một giá trị; `include`/`require` trả về giá trị đó (không có `return` thì trả
  `1`). Laravel dùng đúng cơ chế này cho thư mục `config/`: mỗi file `config/*.php` là
  `return [ ... ];`.
- `require` hai lần một file khai báo hàm hay class thì lần hai báo
  `Fatal error: Cannot redeclare function chao() (previously declared in ...)`. Đó là lý do có bản `_once`.
- Một file như `helpers.php` của ví dụ, vừa khai báo hàm vừa in ra màn hình khi được nạp, là thiết kế
  xấu: chỉ nạp file thôi mà đã có *side effect* (tác dụng phụ). PSR-1 (mục 13) khuyến nghị (mức SHOULD)
  một file **hoặc** khai báo (class, hàm, hằng) **hoặc** chạy logic có side effect, không vừa cả hai. Ví
  dụ trên vi phạm có chủ ý để bạn thấy lúc nào file được nạp.

### 5.2 Luôn dùng `__DIR__` cho đường dẫn

Đường dẫn trong `include`/`require` được xử lý theo manual như sau:

- Đường dẫn tuyệt đối (`/var/www/app/x.php`) hoặc bắt đầu bằng `./`, `../`: dùng đúng như vậy. `./` và
  `../` tính từ **thư mục làm việc hiện tại** (*current working directory*) của tiến trình, không phải
  thư mục của file đang viết code.
- Tên trơn (`'helpers.php'`, `'lib/x.php'`): tìm lần lượt trong các thư mục của ini `include_path`, rồi
  thư mục của file đang chạy, rồi thư mục làm việc hiện tại.

Cả hai cách tương đối đều phụ thuộc vào việc chương trình được chạy từ đâu. Script chạy đúng khi bạn
`cd` vào thư mục dự án, nhưng hỏng khi cron gọi nó từ `/`. Cách chắc chắn: ghép với `__DIR__` (thư mục
chứa file hiện tại, [Chương 03](03-cu-phap-bien-hang.md)) để luôn có đường dẫn tuyệt đối. Laravel làm
đúng như vậy: `public/index.php` viết `require __DIR__.'/../vendor/autoload.php';`.

### 5.3 Vì sao `require` bằng tay không đủ

Với vài file, viết `require` bằng tay là được. Với một dự án thật thì không:

- Laravel mới cài đã có hàng nghìn file PHP trong `vendor/`. Không ai viết tay hàng nghìn dòng `require`.
- Phải nạp **theo đúng thứ tự**: class `Invoice extends BaseDocument` thì file của `BaseDocument` phải
  được nạp trước. Đổi quan hệ kế thừa là phải sắp lại danh sách.
- Nạp hết mọi file ở mọi request là phí: một request chỉ dùng vài trăm trong số hàng nghìn class.
  [Chương 02](02-php-chay-nhu-the-nao.md) đã nói PHP biên dịch từng file khi file được nạp; nạp thừa là
  biên dịch thừa (OPcache giảm được phần biên dịch, nhưng vẫn tốn công nạp).
- Mỗi file phải tự biết các file nó phụ thuộc nằm ở đâu.

Câu trả lời của PHP là autoload.

## 6. Autoload: nạp class khi cần

### 6.1 Ý tưởng

*Autoload* (tự nạp) là cơ chế: khi code dùng một class (hoặc interface, trait, enum) **chưa được định
nghĩa**, thay vì báo lỗi ngay, PHP gọi một hàm do bạn đăng ký, truyền cho nó tên đầy đủ của class. Hàm đó
gọi là *autoloader*. Nó có nhiệm vụ đổi tên class thành đường dẫn file và `require` file đó. Sau khi
autoloader chạy xong, nếu class đã tồn tại thì PHP dùng nó như chưa có chuyện gì; nếu chưa thì PHP mới báo
lỗi.

```
new Shop\Billing\Invoice()
        │
        ▼
class Shop\Billing\Invoice đã được định nghĩa?
        │ có ─────────────────────────────────────────► dùng luôn
        │ chưa
        ▼
gọi lần lượt từng autoloader đã đăng ký, truyền 'Shop\Billing\Invoice'
        │   autoloader: 'Shop\Billing\Invoice' → src/Billing/Invoice.php → require
        ▼
sau mỗi autoloader: class đã có chưa?
        │ có ─────────────────────────────────────────► dừng, dùng class
        │ hết autoloader mà vẫn chưa có
        ▼
Error: Class "Shop\Billing\Invoice" not found
```

Manual mô tả autoload là "cơ hội cuối" (*last chance*) để nạp class trước khi PHP báo lỗi.

### 6.2 `spl_autoload_register()`

Chữ ký (manual PHP 8):

```php
spl_autoload_register(?callable $callback = null, bool $throw = true, bool $prepend = false): bool
```

- `$callback`: autoloader, một callable nhận `string $class`. Tên class truyền vào **không có** dấu `\`
  ở đầu.
- `$throw`: từ PHP 8.0 bị bỏ qua (luôn ném `TypeError` nếu đối số sai); truyền `false` thì PHP phát notice.
- `$prepend`: `true` thì đặt autoloader lên **đầu** hàng đợi thay vì cuối.

Gọi `spl_autoload_register()` bao nhiêu lần cũng được; PHP giữ một **hàng đợi** autoloader và gọi theo
thứ tự đăng ký, dừng ngay khi class xuất hiện:

```php
<?php
declare(strict_types=1);

spl_autoload_register(function (string $class): void {
    echo "loader A hỏi: $class\n";
});

spl_autoload_register(function (string $class): void {
    echo "loader B hỏi: $class\n";
    if ($class === 'Hello') {
        eval('class Hello { }');      // giả lập "require file định nghĩa class"
    }
});

spl_autoload_register(function (string $class): void {
    echo "loader C hỏi: $class\n";
});

spl_autoload_register(function (string $class): void {
    echo "loader Z (prepend) hỏi: $class\n";
}, prepend: true);

new Hello();
echo "---\n";
echo count(spl_autoload_functions()), "\n";
try {
    new Missing();
} catch (\Error $e) {
    echo $e->getMessage(), "\n";
}
```

Output:

```
loader Z (prepend) hỏi: Hello
loader A hỏi: Hello
loader B hỏi: Hello
---
4
loader Z (prepend) hỏi: Missing
loader A hỏi: Missing
loader B hỏi: Missing
loader C hỏi: Missing
Class "Missing" not found
```

- Loader Z đăng ký sau cùng nhưng có `prepend: true` nên được hỏi đầu tiên.
- Với `Hello`, loader B định nghĩa được class, nên loader C không được hỏi.
- Với `Missing`, cả bốn loader đều được hỏi, không ai nạp được, PHP ném `Error`.
- `spl_autoload_functions()` trả về danh sách autoloader đang đăng ký; `spl_autoload_unregister()` gỡ
  một autoloader.
- (`eval` chỉ dùng ở đây cho ví dụ gọn trong một file. Code thật không dùng `eval`.)

Trước PHP 8.0 còn một cách cũ là định nghĩa hàm toàn cục tên `__autoload()`. Nó chỉ cho phép **một**
autoloader, bị deprecated từ 7.2 và bị xoá ở 8.0. Khai báo hàm đó trên PHP 8 báo
`Fatal error: __autoload() is no longer supported, use spl_autoload_register() instead`.

### 6.3 Autoloader đầu tiên

Một dự án nhỏ, namespace gốc `Shop\` ứng với thư mục `src/`:

```
shop/
├── src/
│   ├── Billing/
│   │   ├── Discount.php      (Shop\Billing\Discount)
│   │   └── Invoice.php       (Shop\Billing\Invoice)
│   └── Models/
│       └── Product.php       (Shop\Models\Product)
├── autoload.php
└── main.php
```

```php
<?php
// src/Models/Product.php
declare(strict_types=1);

namespace Shop\Models;

final class Product
{
    public function __construct(
        public readonly string $name,
        public readonly int $price,
    ) {}
}
```

```php
<?php
// src/Billing/Invoice.php
declare(strict_types=1);

namespace Shop\Billing;

use Shop\Models\Product;

final class Invoice
{
    /** @var list<Product> */
    private array $items = [];

    public function add(Product $p): void
    {
        $this->items[] = $p;
    }

    public function total(): int
    {
        return array_sum(array_map(fn (Product $p): int => $p->price, $this->items));
    }
}
```

```php
<?php
// src/Billing/Discount.php
declare(strict_types=1);

namespace Shop\Billing;

final class Discount
{
    public static function apply(int $amount, int $percent): int
    {
        return $amount - intdiv($amount * $percent, 100);
    }
}
```

```php
<?php
// autoload.php
declare(strict_types=1);

spl_autoload_register(function (string $class): void {
    $prefix  = 'Shop\\';              // namespace prefix của dự án
    $baseDir = __DIR__ . '/src/';     // thư mục ứng với prefix đó

    // 1. Class không thuộc prefix của mình: im lặng trả về, để autoloader khác thử.
    if (!str_starts_with($class, $prefix)) {
        return;
    }

    // 2. Bỏ prefix: 'Shop\Billing\Invoice' -> 'Billing\Invoice'
    $relative = substr($class, strlen($prefix));

    // 3. Đổi \ thành /, thêm .php: 'src/Billing/Invoice.php'
    $file = $baseDir . str_replace('\\', '/', $relative) . '.php';

    // 4. Có file thì nạp. Không có thì im lặng (không throw, không báo lỗi).
    if (is_file($file)) {
        echo "  [autoload] $class -> ", substr($file, strlen(__DIR__) + 1), "\n";
        require $file;
    }
});
```

```php
<?php
// main.php
declare(strict_types=1);

use Shop\Billing\Discount;
use Shop\Billing\Invoice;
use Shop\Models\Product;

require __DIR__ . '/autoload.php';

echo "Bắt đầu\n";
$invoice = new Invoice();
echo "Đã tạo Invoice\n";
$invoice->add(new Product('Bút', 15000));
$invoice->add(new Product('Vở', 25000));
echo "Tổng: ", $invoice->total(), "\n";

if ($invoice->total() > 1_000_000) {
    echo Discount::apply($invoice->total(), 10), "\n";   // nhánh không chạy: Discount không bị nạp
}

var_dump(class_exists(\Shop\Billing\Refund::class));
```

Output:

```
Bắt đầu
  [autoload] Shop\Billing\Invoice -> src/Billing/Invoice.php
Đã tạo Invoice
  [autoload] Shop\Models\Product -> src/Models/Product.php
Tổng: 40000
bool(false)
```

(Dòng `[autoload]` chỉ để quan sát; autoloader thật không in gì.) Đọc output kỹ:

- `main.php` chỉ `require` đúng một file: `autoload.php`. Không còn danh sách `require` nào.
- `Invoice.php` được nạp đúng lúc `new Invoice()` chạy, không phải lúc gặp dòng `use`.
- `Invoice.php` có `use Shop\Models\Product;` và type hint `Product`, nhưng `Product.php` chỉ được nạp
  khi `new Product(...)` chạy. Biên dịch một file không kéo theo nạp các class nó nhắc tới.
- `Discount` nằm trong nhánh `if` không chạy, nên `Discount.php` không bao giờ được đọc. Autoload là
  *lazy* (lười): chỉ nạp thứ thật sự dùng.
- `class_exists()` với class không có file trả `false` một cách êm đẹp, vì autoloader im lặng.

### 6.4 Những thao tác nào gọi autoloader

Thử nghiệm với một autoloader chỉ in ra tên được hỏi (PHP 8.5):

| Thao tác (class chưa được nạp) | Gọi autoloader? |
|---|---|
| `new X()`, `X::method()`, `X::CONST`, `X::$prop` | Có |
| Khai báo `class Y extends X`, `implements X`, `use X;` (trait) trong class | Có, lúc class `Y` được khai báo |
| `class_exists('X')`, `interface_exists`, `enum_exists`, `trait_exists` | Có (tham số thứ hai `$autoload` mặc định `true`) |
| `class_exists('X', false)` | Không |
| `method_exists('X', 'm')`, `is_subclass_of('X', ...)` với chuỗi | Có |
| `unserialize()` gặp object class `X` | Có ([Chương 10](10-oop-nang-cao.md)) |
| `X::class` | Không (chỉ là chuỗi, lúc biên dịch) |
| `$obj instanceof X` | Không ([Chương 07](07-toan-tu-dieu-khien.md)) |
| `catch (X $e)` | Không |
| Type hint `function f(X $x)`, kể cả khi truyền object sai kiểu | Không |
| `is_a($obj, 'X')` với `$obj` là object | Không |
| Dòng `use X;` ở đầu file | Không |

Quy luật đằng sau: PHP chỉ autoload khi nó **thật sự cần định nghĩa** của class (để tạo object, đọc
hằng, kế thừa...). Còn khi chỉ cần **so sánh tên** (một object có phải `instanceof X` không), nếu `X`
chưa được nạp thì chắc chắn không object nào là instance của nó, khỏi cần nạp.

### 6.5 Autoload chỉ dành cho class

Autoload chỉ áp dụng cho class, interface, trait, enum. Hàm và hằng **không** autoload được: gọi một hàm
chưa định nghĩa thì PHP báo lỗi ngay, không hỏi autoloader nào.

```php
<?php
declare(strict_types=1);

namespace App;

spl_autoload_register(function (string $c): void { echo "hỏi $c\n"; });

try { helper(); } catch (\Error $e) { echo $e->getMessage(), "\n"; }
// in ra: Call to undefined function App\helper()     (không có dòng "hỏi ...")
try { echo HANG; } catch (\Error $e) { echo $e->getMessage(), "\n"; }
// in ra: Undefined constant "App\HANG"
```

Hệ quả: file chứa hàm (như `helpers.php` với các hàm tiện ích) phải được nạp sẵn từ đầu. Composer có
mục `files` làm việc này (mục 11.1). Đây là một trong các lý do code PHP hiện đại hay gom hàm tiện ích vào
class (static method) thay vì để hàm rời.

### 6.6 Autoloader phải lặng lẽ

Manual khuyến cáo mạnh không ném exception từ autoloader, và PSR-4 bắt buộc autoloader "MUST NOT throw
exceptions, MUST NOT raise errors of any level". Lý do: exception làm **dừng cả hàng đợi**, các
autoloader sau không được hỏi nữa.

```php
<?php
declare(strict_types=1);

spl_autoload_register(function (string $class): void {
    throw new \RuntimeException("Không tìm thấy $class");    // ⚠️ sai
});
spl_autoload_register(function (string $class): void {
    echo "loader thứ hai hỏi: $class\n";                    // không bao giờ được gọi
    if ($class === 'Hello') {
        eval('class Hello { }');
    }
});

try {
    new Hello();
} catch (\Throwable $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
    // in ra: RuntimeException: Không tìm thấy Hello
}
```

Loader thứ hai nạp được `Hello` nhưng không bao giờ có cơ hội. Ngoài ra, ném exception còn làm hỏng
`class_exists('X')`: lẽ ra trả `false`, giờ lại ném. Quy tắc: không tìm thấy thì `return` và để PHP tự
báo "Class not found" khi hết hàng đợi.

Một chi tiết khác: PHP không nhớ các lần tra hụt. Gọi `class_exists('X')` hai lần với `X` không tồn tại
thì autoloader bị gọi hai lần. Với autoloader đọc đĩa, việc tra hụt lặp lại tốn kém; autoloader của
Composer tự nhớ các lần hụt trong một request (mục 11.2).

## 7. PSR-4: chuẩn ánh xạ namespace sang thư mục

### 7.1 Vì sao cần một chuẩn

Autoloader ở mục 6.3 dùng quy ước của riêng bạn: `Shop\` ứng với `src/`. Thư viện A có thể chọn quy ước
khác: `A_B_C` ứng với `A/B/C.php`. Nếu mỗi thư viện một quy ước, dự án dùng 50 thư viện phải đăng ký 50
autoloader khác nhau.

*PHP-FIG* (PHP Framework Interop Group) là nhóm gồm đại diện của nhiều dự án PHP (framework, thư viện)
cùng bàn cách để các dự án dùng chung được với nhau. Nhóm đặt ra các khuyến nghị chung gọi là *PSR* (PHP Standards Recommendation), đánh số PSR-0, PSR-1... (mục 13).
*PSR-4* là chuẩn autoload: nó quy định cách đặt file sao cho **một** thuật toán duy nhất tìm được class
của mọi thư viện. Nhờ vậy Composer chỉ cần một autoloader cho cả dự án.

### 7.2 Nội dung PSR-4

Tóm tắt phần quy định (chữ in hoa như MUST là từ khoá theo RFC 2119, nghĩa là "bắt buộc"):

1. "Class" ở đây gồm class, interface, trait và các cấu trúc tương tự (enum).
2. Tên đầy đủ có dạng `\<NamespaceName>(\<SubNamespaceNames>)*\<ClassName>`:
   - BẮT BUỘC có namespace cấp cao nhất, gọi là *vendor namespace* (namespace của nhà cung cấp:
     `Illuminate`, `Symfony`, `GuzzleHttp`, hoặc `App` của bạn).
   - Có thể có một hoặc nhiều namespace con.
   - BẮT BUỘC kết thúc bằng tên class.
   - Dấu gạch dưới `_` không có ý nghĩa đặc biệt ở bất cứ đâu trong tên.
   - Chữ cái hoa thường kết hợp tuỳ ý, nhưng mọi chỗ tham chiếu tới class BẮT BUỘC viết đúng hoa thường.
3. Khi nạp file cho một tên đầy đủ:
   - Một dãy liên tiếp gồm một hoặc vài đoạn **đầu** của namespace (không tính dấu `\` đầu), gọi là
     *namespace prefix*, ứng với ít nhất một *base directory* (thư mục gốc).
   - Các đoạn namespace con **sau** prefix ứng với thư mục con bên trong base directory, dấu `\` thành
     dấu phân cách thư mục. Tên thư mục con BẮT BUỘC khớp hoa thường với namespace.
   - Tên class cuối cùng ứng với tên file đuôi `.php`, BẮT BUỘC khớp hoa thường.
4. Autoloader BẮT BUỘC không ném exception, không phát lỗi ở bất kỳ mức nào, và KHÔNG NÊN trả về giá trị.

Bảng ví dụ trong chính văn bản PSR-4:

| Tên đầy đủ | Namespace prefix | Base directory | File |
|---|---|---|---|
| `\Acme\Log\Writer\File_Writer` | `Acme\Log\Writer` | `./acme-log-writer/lib/` | `./acme-log-writer/lib/File_Writer.php` |
| `\Aura\Web\Response\Status` | `Aura\Web` | `/path/to/aura-web/src/` | `/path/to/aura-web/src/Response/Status.php` |
| `\Symfony\Core\Request` | `Symfony\Core` | `./vendor/Symfony/Core/` | `./vendor/Symfony/Core/Request.php` |
| `\Zend\Acl` | `Zend` | `/usr/includes/Zend/` | `/usr/includes/Zend/Acl.php` |

Cách đọc dòng thứ hai: bỏ prefix `Aura\Web` khỏi tên, còn `Response\Status`; đổi `\` thành `/` và thêm
`.php`, được `Response/Status.php`; ghép vào base directory. Dòng đầu cho thấy `_` trong `File_Writer` giữ
nguyên, không bị đổi thành `/`.

Điểm then chốt của PSR-4 so với chuẩn cũ PSR-0: phần prefix **không** xuất hiện trong đường dẫn. Với
PSR-0, class `Vendor\Package\ClassName` bắt buộc nằm ở `.../Vendor/Package/ClassName.php`, nên package
Composer phải có những cây thư mục lặp lại như `src/Vendor/Package/`. PSR-4 cho phép
`src/ClassName.php` với prefix `Vendor\Package\` ứng với `src/`. PSR-0 còn đổi `_` trong tên class thành
`/` (di sản từ thời tiền tố kiểu PEAR). PSR-0 hiện đã bị PHP-FIG đánh dấu *deprecated*.

### 7.3 Autoloader PSR-4 nhiều prefix

Dự án thật có nhiều prefix: code chính, code test, vài thư viện. Và các prefix có thể lồng nhau: `Shop\`
ứng với `src/`, nhưng `Shop\Tests\` ứng với `tests/`. Class `Shop\Tests\InvoiceTest` khớp cả hai prefix;
phải thử prefix **dài hơn** trước, và prefix khớp mà không có file thì thử tiếp prefix khác. Mở rộng dự án
ở mục 6.3:

```
shop/
├── lib/acme-log/src/Writer.php     (Acme\Log\Writer, giả làm một thư viện)
├── src/...                         (như mục 6.3)
├── tests/InvoiceTest.php           (Shop\Tests\InvoiceTest)
├── Psr4Autoloader.php
└── main2.php
```

```php
<?php
// Psr4Autoloader.php
declare(strict_types=1);

final class Psr4Autoloader
{
    /** @var array<string, list<string>> prefix => danh sách base directory */
    private array $prefixes = [];

    public function addNamespace(string $prefix, string $baseDir): void
    {
        $prefix  = trim($prefix, '\\') . '\\';                 // luôn kết thúc bằng một dấu \
        $baseDir = rtrim($baseDir, '/') . '/';
        $this->prefixes[$prefix][] = $baseDir;
        // prefix dài xếp trước: Shop\Tests\ phải được thử trước Shop\
        uksort($this->prefixes, fn (string $a, string $b): int => strlen($b) <=> strlen($a));
    }

    public function register(): void
    {
        spl_autoload_register($this->loadClass(...));
    }

    public function loadClass(string $class): void
    {
        foreach ($this->prefixes as $prefix => $dirs) {
            if (!str_starts_with($class, $prefix)) {
                continue;
            }
            $relative = str_replace('\\', '/', substr($class, strlen($prefix))) . '.php';
            foreach ($dirs as $dir) {
                if (is_file($dir . $relative)) {
                    require $dir . $relative;
                    return;
                }
            }
            // prefix khớp nhưng không có file: thử tiếp prefix ngắn hơn
        }
        // không thấy: im lặng, để autoloader khác (nếu có) thử
    }
}
```

```php
<?php
// tests/InvoiceTest.php
declare(strict_types=1);

namespace Shop\Tests;

final class InvoiceTest
{
    public function run(): string { return 'InvoiceTest chạy'; }
}
```

```php
<?php
// lib/acme-log/src/Writer.php
declare(strict_types=1);

namespace Acme\Log;

final class Writer
{
    public function write(string $m): string { return "[acme] $m"; }
}
```

```php
<?php
// main2.php
declare(strict_types=1);

require __DIR__ . '/Psr4Autoloader.php';

$loader = new Psr4Autoloader();
$loader->addNamespace('Shop', __DIR__ . '/src');
$loader->addNamespace('Shop\Tests', __DIR__ . '/tests');
$loader->addNamespace('Acme\Log', __DIR__ . '/lib/acme-log/src');
$loader->register();

echo (new Shop\Tests\InvoiceTest())->run(), "\n";            // in ra: InvoiceTest chạy
echo (new Acme\Log\Writer())->write('xin chào'), "\n";       // in ra: [acme] xin chào
echo (new Shop\Billing\Invoice())->total(), "\n";            // in ra: 0
var_dump(class_exists('Shop\Billing\Refund'));               // in ra: bool(false)
```

Đây về cơ bản là việc Composer làm, cộng thêm nhiều tối ưu (mục 11). Một chi tiết: prefix được chuẩn hoá
để luôn kết thúc bằng `\`. Nếu không, prefix `Shop` sẽ khớp nhầm cả class `ShopAdmin\Foo`.

### 7.4 Quy ước bám theo PSR-4 trong dự án

- Một file chứa đúng một class (interface, trait, enum), tên file trùng tên class: `Invoice.php` chứa
  `Invoice`. Đặt hai class trong một file thì class thứ hai không autoload được (autoloader chỉ biết tìm
  file theo tên class).
- Thư mục khớp namespace từng chữ, kể cả hoa thường. Laravel: prefix `App\` ứng với `app/` (chữ thường,
  vì nằm trong phần base directory), nhưng bên trong là `app/Models/User.php` cho `App\Models\User`.
- Tên dùng trong code phải khớp hoa thường với tên khai báo, dù engine không bắt buộc (mục 2.5).

### 7.5 Bẫy hoa thường: "máy tôi chạy, server không chạy"

Filesystem mặc định trên macOS (APFS) và Windows (NTFS) không phân biệt hoa thường; ext4 trên Linux thì
có. Hậu quả:

| Bước | Máy dev (macOS) | Server (Linux) |
|---|---|---|
| File đặt nhầm `app/models/User.php` (chữ `m` thường), namespace `App\Models` | | |
| Code gọi `new User()` | Autoloader tìm `app/Models/User.php`; macOS coi `models` và `Models` là một, tìm thấy, chạy | Không có thư mục `app/Models`, `is_file()` trả `false` |
| Kết quả | Mọi test đều xanh | `Error: Class "App\Models\User" not found` |

Tương tự khi code viết `new user()` (chữ thường) trong khi file là `User.php`, hoặc đổi tên file chỉ khác
hoa thường mà git trên macOS không ghi nhận. Cách phòng:

- Luôn viết tên class, namespace, thư mục, file đúng hoa thường; để IDE tạo file và namespace.
- Chạy test trên CI bằng Linux (Docker), không chỉ trên máy dev.
- Composer có cờ kiểm tra file không khớp PSR-4 (mục 11.3).

## 8. Composer: trình quản lý dependency

### 8.1 Bài toán: thư viện của thư viện

Giả sử dự án cần ghi log vào file. Bạn có thể tự viết, hoặc dùng thư viện Monolog. Muốn dùng Monolog
bằng tay, bạn phải:

1. Tải mã nguồn Monolog đúng phiên bản hợp với bản PHP của mình.
2. Phát hiện Monolog cần thêm thư viện `psr/log` (interface logger chuẩn, mục 13), tải tiếp, đúng phiên
   bản Monolog yêu cầu.
3. Đăng ký autoloader cho cả hai, mỗi thư viện một prefix, một thư mục.
4. Khi Monolog ra bản sửa lỗi bảo mật, lặp lại cả quy trình, và kiểm tra bản mới có còn hợp với các thư
   viện khác đang dùng `psr/log` không.

Thư viện mà dự án dùng gọi là *dependency* (phụ thuộc). Dependency của dependency gọi là *transitive
dependency* (phụ thuộc gián tiếp). Một dự án Laravel mới có vài chục package như vậy, chằng chịt ràng
buộc phiên bản lẫn nhau. Làm tay là bất khả thi.

### 8.2 Composer là gì

*Composer* là công cụ quản lý dependency cho PHP. Docs của Composer tóm tắt: bạn khai báo những thư viện
dự án cần; Composer tìm ra **những phiên bản nào** của **những package nào** cần cài (kể cả dependency
gián tiếp) để thoả mọi ràng buộc, rồi tải chúng về; và một lệnh là cập nhật được tất cả.

Vài điểm phân biệt:

- Composer quản lý theo **từng dự án**: package được cài vào thư mục `vendor/` của dự án đó, không cài
  vào hệ thống. Hai dự án trên cùng máy dùng hai bản Monolog khác nhau thoải mái. Docs nhấn mạnh Composer không
  phải package manager theo nghĩa như Yum hay Apt, mà là *dependency manager*, lấy cảm hứng từ npm của
  Node và Bundler của Ruby.
- Composer sinh luôn autoloader, dựa trên khai báo autoload của từng package (thường là PSR-4, mục 7) và
  của code bạn. Một dòng `require __DIR__ . '/vendor/autoload.php';` là dùng được mọi class.
- *Packagist* (packagist.org) là kho package mặc định mà Composer tìm tới. Package mã nguồn mở được đăng
  ở đó; Composer đọc thông tin phiên bản từ Packagist và tải mã nguồn về (mục 12.4).
- Bản thân Composer là một chương trình PHP, đóng gói thành một file `composer.phar` (PHAR là định dạng
  lưu trữ chạy được của PHP). Thời điểm viết (10/2026), bản mới nhất là Composer 2.10.

Cài Composer: làm theo trang getcomposer.org/download (tải installer, chạy bằng PHP, được
`composer.phar`), rồi chuyển nó vào thư mục trong `PATH`, ví dụ `mv composer.phar /usr/local/bin/composer`.
Không muốn cài thì dùng image Docker `composer` như phần đầu chương.

### 8.3 Dự án đầu tiên với Composer

Trong một thư mục trống `my-app/` (lệnh chạy tại thư mục đó, cần mạng):

```bash
composer require monolog/monolog
```

Composer sẽ: tạo `composer.json` (nếu chưa có) và ghi vào đó ràng buộc cho `monolog/monolog`; giải ràng
buộc; tải Monolog cùng dependency `psr/log` của nó về `vendor/`; ghi `composer.lock`; sinh autoloader.
Khi bạn không ghi ràng buộc, Composer tự chọn dựa vào bản mới nhất: nếu đó là `3.10.2` thì nó ghi `^3.10` (bỏ số
PATCH, thêm `^`; ý nghĩa của `^` ở mục 9). Kết quả:

```
my-app/
├── composer.json          ← bạn khai báo: cần gì, ràng buộc phiên bản ra sao
├── composer.lock          ← Composer ghi: đã chọn chính xác bản nào
└── vendor/                ← mã nguồn các package, do Composer quản lý
    ├── autoload.php       ← file duy nhất code của bạn cần require
    ├── bin/               ← lệnh chạy được do các package cung cấp (mục 12.2)
    ├── composer/          ← autoloader và các bảng ánh xạ do Composer sinh ra
    ├── monolog/monolog/
    └── psr/log/
```

Dùng thử, file `my-app/index.php`:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use Monolog\Handler\StreamHandler;
use Monolog\Level;
use Monolog\Logger;

$log = new Logger('app');
$log->pushHandler(new StreamHandler('php://stdout', Level::Warning));
$log->warning('Sắp hết dung lượng', ['free_mb' => 120]);
$log->info('Dòng này thấp hơn mức Warning nên không được ghi');
```

```bash
php index.php
```

Output minh hoạ (đây là định dạng mặc định của `LineFormatter` trong Monolog 3; ngày giờ và múi giờ là
của máy bạn):

```
[2026-10-03T09:15:02.123456+00:00] app.WARNING: Sắp hết dung lượng {"free_mb":120} []
```

Không có dòng `require` nào trỏ vào `vendor/monolog/...`. `vendor/autoload.php` đăng ký autoloader, và
`new Logger(...)` khiến autoloader tự tìm `vendor/monolog/monolog/src/Monolog/Logger.php`.
(`Monolog\Level` là enum có từ Monolog 3; Monolog 2 dùng hằng `Logger::WARNING`.)

⚠️ Thư mục `vendor/` **không** commit vào git (docs Composer khuyên thêm `vendor` vào `.gitignore`). Nó
tái tạo được hoàn toàn từ `composer.lock` bằng `composer install`. Còn `composer.json` và `composer.lock`
thì commit (mục 10).

### 8.4 `composer.json` của một ứng dụng thật

Trích `composer.json` của skeleton Laravel 13 (nhánh `13.x` của repo `laravel/laravel` lúc viết; số phiên
bản sẽ đổi theo thời gian; đã lược bớt khoá `keywords`, `extra`, vài package trong `require-dev` và phần
lớn `scripts`):

```json
{
    "$schema": "https://getcomposer.org/schema.json",
    "name": "laravel/laravel",
    "type": "project",
    "description": "The skeleton application for the Laravel framework.",
    "license": "MIT",
    "require": {
        "php": "^8.3",
        "laravel/framework": "^13.17",
        "laravel/tinker": "^3.0"
    },
    "require-dev": {
        "fakerphp/faker": "^1.23",
        "laravel/pint": "^1.27",
        "mockery/mockery": "^1.6",
        "phpunit/phpunit": "^12.5.12"
    },
    "autoload": {
        "psr-4": {
            "App\\": "app/",
            "Database\\Factories\\": "database/factories/",
            "Database\\Seeders\\": "database/seeders/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "Tests\\": "tests/"
        }
    },
    "scripts": {
        "post-autoload-dump": [
            "Illuminate\\Foundation\\ComposerScripts::postAutoloadDump",
            "@php artisan package:discover --ansi"
        ]
    },
    "config": {
        "optimize-autoloader": true,
        "preferred-install": "dist",
        "sort-packages": true,
        "allow-plugins": {
            "pestphp/pest-plugin": true,
            "php-http/discovery": true
        }
    },
    "minimum-stability": "stable",
    "prefer-stable": true
}
```

Từng khoá (theo trang "The composer.json schema" của docs Composer):

| Khoá | Ý nghĩa |
|---|---|
| `name` | Tên package dạng `vendor/project`, chữ thường. Bắt buộc với thư viện muốn đăng lên Packagist; với ứng dụng thì không cần |
| `type` | Mặc định `library`. `project` cho ứng dụng hoàn chỉnh (như skeleton Laravel) |
| `require` | Package cần để **chạy** ứng dụng, kèm ràng buộc phiên bản |
| `require-dev` | Package chỉ cần khi **phát triển**: test, format code, dữ liệu giả. Chỉ có tác dụng ở dự án gốc (*root-only*, xem dưới) |
| `autoload` | Ánh xạ namespace sang thư mục cho code của bạn (mục 11.1) |
| `autoload-dev` | Như trên nhưng chỉ cho code dùng khi phát triển, ví dụ thư mục `tests/` |
| `scripts` | Lệnh chạy ở các sự kiện của Composer hoặc lệnh tự đặt tên (mục 12.1) |
| `config` | Cấu hình hành vi của Composer cho dự án này (root-only) |
| `minimum-stability` | Mức ổn định thấp nhất được chấp nhận, mặc định `stable` (mục 9.4) |
| `prefer-stable` | Ưu tiên bản ổn định khi có thể (mục 9.4) |

*Root package* là package ứng với `composer.json` ở gốc dự án bạn đang chạy Composer. Các khoá đánh dấu
*root-only* (`require-dev`, `autoload-dev`, `config`, `scripts`, `minimum-stability`...) chỉ được đọc
từ root package; trong `composer.json` của các dependency thì bị bỏ qua. Ví dụ PHPUnit trong `require-dev`
của Monolog không bao giờ được cài vào dự án của bạn, và docs Scripts ghi rõ chỉ script của root package
mới được chạy.

### 8.5 Tên package và platform package

Tên package gồm **tên nhà cung cấp** (*vendor name*) và **tên dự án**, cách nhau bằng `/`:
`monolog/monolog`, `laravel/framework`, `guzzlehttp/guzzle`. Vendor name tồn tại để tránh trùng tên, giống
namespace: hai người cùng viết thư viện `json` thì một là `igorw/json`, một là `seldaek/json`.

⚠️ Tên package (`guzzlehttp/guzzle`) và namespace PHP (`GuzzleHttp\`) là hai thứ khác nhau, chỉ thường
giống nhau theo quy ước. Tên package dùng trong `composer.json`; namespace dùng trong code. Muốn biết một
package dùng namespace gì, xem khoá `autoload` trong `composer.json` của chính package đó (ở
`vendor/<vendor>/<project>/composer.json`).

Ngoài package thật, `require` còn nhận *platform package*: những thứ đã có trên máy, Composer không cài
được, nhưng kiểm tra được:

- `php`: bản PHP. `"php": "^8.3"` nghĩa là cần PHP 8.3 trở lên, dưới 9.0.
- `ext-<tên>`: extension của PHP, ví dụ `"ext-redis": "*"`, `"ext-intl": "*"`. Docs khuyên dùng `*` vì
  cách đánh số phiên bản của extension không thống nhất.
- `lib-<tên>`: thư viện hệ thống mà PHP dùng, ví dụ `lib-openssl`, `lib-icu`.

`composer show --platform` liệt kê các platform package có trên máy. Hai lợi ích của việc khai báo:

- Cài trên máy thiếu extension hay sai bản PHP thì `composer install` báo lỗi ngay, thay vì chạy được rồi
  vỡ lúc runtime. Docs nhắc: đừng giả định extension nào cũng có sẵn (bản cài tối giản trên một số
  distro Linux thiếu cả `ext-mysqli`).
- Composer sinh file `vendor/composer/platform_check.php`, được nạp khi `vendor/autoload.php` chạy. Mặc
  định (config `platform-check` là `php-only`) nó chỉ kiểm tra bản PHP lúc runtime: deploy lên server chạy
  PHP thấp hơn yêu cầu thì ứng dụng dừng ngay, ném `RuntimeException` với thông báo bắt đầu bằng
  "Composer detected issues in your platform".

## 9. Phiên bản và ràng buộc phiên bản

### 9.1 Semantic versioning

*Semantic versioning* (gọi tắt *semver*, đặc tả tại semver.org) là quy ước đánh số phiên bản dạng
`MAJOR.MINOR.PATCH`, ví dụ `3.9.1`:

| Tăng | Khi | Ví dụ |
|---|---|---|
| MAJOR | Thay đổi **không tương thích ngược** với API công khai (xoá method, đổi chữ ký...) | `3.9.1` → `4.0.0` |
| MINOR | Thêm tính năng mới, **tương thích ngược** | `3.9.1` → `3.10.0` |
| PATCH | Sửa lỗi, tương thích ngược | `3.9.1` → `3.9.2` |

Vài quy định trong đặc tả:

- Mỗi phần là số nguyên không âm, so sánh theo số: `1.9.0` → `1.10.0` → `1.11.0` (không phải so chuỗi).
- Bản đã phát hành thì không được sửa nội dung; sửa gì cũng phải ra bản mới.
- Bản `0.y.z` là giai đoạn phát triển ban đầu: "Anything MAY change at any time", API chưa được coi là ổn
  định. Bản `1.0.0` mới định nghĩa API công khai.
- Có thể thêm nhãn *pre-release* sau dấu `-`: `2.0.0-beta.1`, `2.0.0-RC1`.

Semver là **lời hứa** của người viết thư viện, không phải thứ máy kiểm tra được. Thư viện làm vỡ tương
thích trong một bản MINOR vẫn xảy ra; đó là một lý do cần `composer.lock` (mục 10) và test tự động.

### 9.2 Viết ràng buộc

Chuỗi sau tên package trong `require` (`"^3.9"`) không phải "phiên bản" mà là *version constraint* (ràng
buộc phiên bản): một tập các phiên bản được chấp nhận. Các dạng theo docs "Versions and constraints":

| Ràng buộc | Tương đương | Ghi chú |
|---|---|---|
| `1.0.2` | Đúng `1.0.2` | Package khác cần bản khác thì giải ràng buộc thất bại |
| `>=1.0` | Từ `1.0` trở lên, không cận trên | ⚠️ Có thể kéo về bản MAJOR mới làm vỡ code |
| `>=1.0 <2.0` | Khoảng | Dấu cách hoặc dấu phẩy là AND, `\|\|` là OR; AND ưu tiên hơn OR |
| `1.0 - 2.0` | `>=1.0.0 <2.1` | Gạch nối có dấu cách hai bên, bao gồm hai đầu; vế phải thiếu phần thì hiểu là `2.0.*` |
| `1.0.*` | `>=1.0 <1.1` | Wildcard |
| `*` | Mọi bản | ⚠️ Chỉ hợp với `ext-*` |
| `~1.2` | `>=1.2 <2.0.0` | `~` cho phép tăng **chữ số cuối cùng được viết ra** |
| `~1.2.3` | `>=1.2.3 <1.3.0` | Chữ số cuối là PATCH nên chỉ PATCH được tăng |
| `^1.2.3` | `>=1.2.3 <2.0.0` | Mọi bản không đổi MAJOR |
| `^0.3` | `>=0.3.0 <0.4.0` | Với `0.x`, MINOR được coi như MAJOR |
| `^0.0.3` | `>=0.0.3 <0.0.4` | Với `0.0.x`, thực tế chỉ nhận đúng `0.0.3` |

Hai toán tử hay dùng nhất là `~` (tilde) và `^` (caret), docs gọi chung là *next significant release
operators*:

- `^` bám sát semver: "cho mọi bản không làm vỡ tương thích". `^1.2.3` nhận `1.2.4`, `1.9.0`, không nhận
  `2.0.0`. Docs Composer khuyên dùng `^` cho thư viện để tương thích rộng nhất, và lệnh
  `composer require` cũng tự sinh ràng buộc dạng `^`.
- `~` dựa vào **số chữ số bạn viết**: `~1.2` (hai chữ số) cho phép số thứ hai tăng, tức `>=1.2 <2.0`, giống
  `^1.2`; `~1.2.3` (ba chữ số) chỉ cho số thứ ba tăng, tức `>=1.2.3 <1.3.0`, chặt hơn `^1.2.3`. Docs ghi
  thêm: `~1` được hiểu như `~1.0`, vẫn không cho MAJOR tăng.

Ví dụ: "nhận mọi bản 2.x từ 2.4 trở lên" viết `^2.4` (hoặc `~2.4`), tương đương `>=2.4.0 <3.0.0`.

### 9.3 Bẫy với bản `0.x`

Theo semver, bản `0.y.z` không hứa gì về tương thích. Composer xử lý `^` cho bản `0.x` một cách thận
trọng: `^0.3` chỉ nhận `0.3.*`, không nhận `0.4.0`. Hệ quả:

- Package đang ở `0.x` thì mỗi bản MINOR (`0.3` → `0.4`) có thể làm vỡ code, và `composer update` sẽ **không**
  tự nâng qua; bạn phải sửa ràng buộc bằng tay. Đó là chủ ý, không phải lỗi.
- Ngược lại, viết `>=0.3` cho package `0.x` là mời rủi ro vào nhà.

### 9.4 Stability: bản ổn định và chưa ổn định

Composer phân loại mỗi phiên bản theo *stability* (độ ổn định), từ thấp tới cao: `dev`, `alpha`, `beta`,
`RC`, `stable`. Stability đọc từ hậu tố của tag: `v1.1-BETA` là `beta`, `v1.1-RC1` là `RC`, `v1.1` không
hậu tố là `stable`. Nhánh git (không phải tag) có stability `dev`: nhánh `main` thành phiên bản
`dev-main`, nhánh `2.x` thành `2.x-dev`.

- `minimum-stability` (root-only) mặc định `stable`: mọi bản kém ổn định hơn bị bỏ qua khi giải ràng
  buộc. Docs nhắc: nếu Composer báo lỗi về stability khi bạn `require` một package, rất có thể ràng buộc
  bạn ghi chỉ khớp với bản dev, alpha, beta hay RC.
- Muốn dùng bản beta của **một** package, thêm *stability flag* vào ràng buộc: `"vendor/pkg": "^2.0@beta"`.
  Cách này tốt hơn hạ `minimum-stability` của cả dự án.
- `"prefer-stable": true`: khi buộc phải hạ `minimum-stability` (ví dụ xuống `dev`), vẫn ưu tiên bản
  stable cho những package có bản stable thoả ràng buộc.
- Trỏ thẳng vào một nhánh: `"vendor/pkg": "dev-main"`. Chỉ nên tạm thời, vì nhánh thay đổi liên tục.

### 9.5 Chọn ràng buộc nào

| Tình huống | Nên dùng | Vì sao |
|---|---|---|
| Ứng dụng dùng thư viện tuân semver | `^x.y` (thường để `composer require` tự sinh) | Nhận bản sửa lỗi, tính năng mới; không nhận bản phá vỡ. Lock file giữ cho mọi máy giống nhau |
| Thư viện (package bạn phát hành) | `^x.y`, có khi nhiều MAJOR: `^2.0 \|\| ^3.0` | Ràng buộc quá chặt trong thư viện gây xung đột cho người dùng nó |
| Package không tin cậy semver, hoặc `0.x` | `~x.y.z` hoặc khoá chặt | Chỉ nhận bản sửa lỗi |
| Extension PHP | `*` | Docs khuyên vậy |
| Bất kỳ | Tránh `*`, `>=x` không cận trên | `update` có thể kéo về bản MAJOR mới |

## 10. `composer.lock`, `install` và `update`

### 10.1 Ràng buộc và kết quả

`composer.json` chứa **ràng buộc**: "Monolog bản `^3.9`". Nhưng tập `>=3.9.0 <4.0.0` có thể có nhiều bản,
và hôm nay bản mới nhất là `3.9.1`, tháng sau có thể là `3.10.0`. Nếu mỗi lần cài, Composer lại chọn "bản
mới nhất thoả ràng buộc", thì máy bạn, máy đồng nghiệp, CI và production có thể chạy những bộ phiên bản
khác nhau dù cùng một `composer.json`.

`composer.lock` là **kết quả** của lần giải ràng buộc: nó ghi phiên bản chính xác của **mọi** package
được cài, kể cả dependency gián tiếp, kèm nguồn tải (URL, commit) và metadata. Đoạn trích minh hoạ (rút
gọn, các giá trị là giả):

```json
{
    "content-hash": "6d1f0c8e...",
    "packages": [
        {
            "name": "monolog/monolog",
            "version": "3.9.1",
            "source": { "type": "git", "url": "https://github.com/Seldaek/monolog.git", "reference": "a1b2c3..." },
            "require": { "php": ">=8.1", "psr/log": "^2.0 || ^3.0" }
        },
        {
            "name": "psr/log",
            "version": "3.0.2"
        }
    ],
    "packages-dev": []
}
```

`content-hash` là hash tính từ các phần liên quan của `composer.json`. Nhờ nó Composer biết `composer.json`
đã bị sửa sau lần ghi lock gần nhất hay chưa.

### 10.2 `install` khác `update` thế nào

| Lệnh | Đọc gì | Làm gì | Khi nào dùng |
|---|---|---|---|
| `composer install` (đã có lock) | `composer.lock` | Cài **đúng** các bản ghi trong lock, không giải ràng buộc lại | Máy dev vừa clone/pull, CI, deploy |
| `composer install` (chưa có lock) | `composer.json` | Giải ràng buộc, ghi lock, rồi cài | Lần đầu tạo dự án |
| `composer update` | `composer.json` | Giải ràng buộc lại từ đầu: với mỗi package chọn bản cao nhất thoả mọi ràng buộc, **ghi lại lock**, rồi cài | Khi chủ động nâng dependency, trên máy dev; commit lock mới qua code review |
| `composer update vendor/pkg` | `composer.json` | Chỉ nâng package đó; `-w` nâng thêm dependency của nó, `-W` nâng cả những cái cũng là dependency trực tiếp của bạn | Nâng có kiểm soát |
| `composer require vendor/pkg` | | Thêm ràng buộc vào `composer.json`, rồi update riêng package đó | Thêm dependency |
| `composer remove vendor/pkg` | | Xoá khỏi `composer.json`, gỡ package | Bỏ dependency |

Nói gọn: `update` **quyết định** phiên bản và ghi vào lock; `install` **thực hiện** đúng quyết định đã ghi.

- Sửa `composer.json` bằng tay mà quên chạy `update`, rồi chạy `install`: Composer in cảnh báo lock không
  khớp `composer.json` (dựa vào `content-hash`); nếu `composer.json` đòi một package mà lock không có thì
  `install` báo lỗi.
- `composer validate` kiểm tra `composer.json` hợp lệ và lock có cập nhật không. Docs khuyên chạy trước khi
  commit.

### 10.3 Vì sao ứng dụng phải commit `composer.lock`

Kịch bản khi đội **không** commit lock (giả định thư viện `acme/pdf` có ràng buộc `^2.3` trong
`composer.json`):

| Bước | Máy dev của An | CI | Production | Kết quả |
|---|---|---|---|---|
| 1. Thứ Hai | `composer install` (không có lock) chọn `acme/pdf 2.3.4`. An viết code, test xanh | | | Mọi thứ ổn |
| 2. Thứ Ba | | | | Tác giả `acme/pdf` phát hành `2.4.0`, lỡ đổi hành vi một method (vi phạm semver) |
| 3. Thứ Tư | | `composer install` không có lock nên giải lại, chọn `2.4.0`. Test xanh vì không có test chạm đúng chỗ đó | | CI xanh, không ai biết phiên bản đã đổi |
| 4. Thứ Năm | | | Deploy: `composer install` chọn `2.4.0` | Xuất hoá đơn lỗi trên production; máy An vẫn chạy `2.3.4` nên An không tái hiện được |

Có lock thì cả ba nơi đều cài `2.3.4` cho tới khi có người chủ động `composer update acme/pdf`, chạy test,
và commit lock mới qua review. Docs Composer: commit lock để "everything and everyone runs on the same
dependencies", và ngay cả làm một mình, sáu tháng sau cài lại vẫn ra đúng bộ phiên bản đã chạy.

Hai lỗi vận hành kinh điển:

- ⚠️ Chạy `composer update` trên server production: cài lên những phiên bản chưa ai test, và việc giải
  ràng buộc tốn nhiều RAM, CPU. Production chỉ chạy `install`.
- ⚠️ Conflict trong `composer.lock` khi merge hai nhánh: đừng sửa tay hay để git tự trộn văn bản; lock trộn
  bằng văn bản có thể là một tổ hợp phiên bản không hợp lệ. Docs Composer khuyên: lấy nguyên
  `composer.json` và `composer.lock` của một nhánh, chạy lại các lệnh `composer require`/`remove` của nhánh
  kia, rồi `composer validate`. Nếu chỉ dòng `content-hash` bị conflict, docs nói `composer update --lock` có thể là đủ.

### 10.4 Thư viện khác ứng dụng

Lock file chỉ có tác dụng với **root package**. Khi dự án của bạn cài Monolog, Composer không đọc
`composer.lock` của Monolog (nếu có), mà giải ràng buộc theo khoá `require` trong `composer.json` của
Monolog. Vì vậy:

- Ứng dụng: luôn commit lock.
- Thư viện: commit lock hay không tuỳ ý (docs: "you may commit"); nó chỉ giúp CI của chính thư viện ổn định,
  không ảnh hưởng người dùng thư viện. Điều quan trọng với thư viện là ràng buộc trong `require` đủ rộng
  và đúng.

### 10.5 `require` và `require-dev`

| | `require` | `require-dev` |
|---|---|---|
| Dùng cho | Code chạy trên production | Công cụ phát triển: PHPUnit, Pest, Mockery, Faker, Pint, PHPStan |
| Thêm bằng | `composer require vendor/pkg` | `composer require --dev vendor/pkg` |
| `install` mặc định | Cài | Cài |
| `install --no-dev` | Cài | **Không** cài, và autoloader bỏ qua `autoload-dev` |
| Khi dự án là dependency của dự án khác | Được cài theo | Không bao giờ được cài (root-only) |

Production deploy với `--no-dev`: ít package hơn, ít code hơn, ít bề mặt tấn công hơn.

⚠️ Bẫy: code production dùng nhầm class của package dev. Ví dụ seeder chạy trên production gọi Faker,
mà Faker nằm trong `require-dev`. Máy dev và CI (cài đủ cả dev) đều chạy tốt; production (`--no-dev`) báo
`Class "Faker\Factory" not found`. Cách phòng: trong CI có một bước cài `--no-dev` rồi chạy thử những lệnh
production cần chạy.

### 10.6 Các lệnh dùng hằng ngày

| Lệnh | Làm gì |
|---|---|
| `composer require vendor/pkg` | Thêm dependency (ràng buộc tự chọn dạng `^x.y`) |
| `composer require vendor/pkg:^2.4` | Thêm với ràng buộc cụ thể |
| `composer require --dev vendor/pkg` | Thêm vào `require-dev` |
| `composer remove vendor/pkg` | Gỡ dependency |
| `composer install` | Cài theo lock |
| `composer update vendor/pkg` | Nâng một package trong khuôn khổ ràng buộc |
| `composer outdated` (thêm `--direct` để chỉ xem dependency trực tiếp) | Liệt kê package có bản mới hơn. Docs: đỏ là có bản mới tương thích semver, nên nâng; vàng là bản mới có thay đổi phá vỡ theo semver |
| `composer show vendor/pkg` | Xem thông tin package đã cài |
| `composer why vendor/pkg` (`depends`) | Package nào kéo `vendor/pkg` vào dự án |
| `composer why-not vendor/pkg 3.0` (`prohibits`) | Vì sao không nâng lên `3.0` được; `composer why-not php 8.5` cho biết package nào chặn việc nâng PHP |
| `composer validate` | Kiểm tra `composer.json` và độ khớp của lock |
| `composer bump` | Nâng cận dưới của ràng buộc lên bản đang cài (docs: không nên chạy bừa trên thư viện) |
| `composer audit` | Kiểm tra lỗ hổng bảo mật đã công bố (mục 12.3) |
| `composer dump-autoload` | Sinh lại autoloader (mục 11.3) |

## 11. Autoload của Composer

### 11.1 Bốn cách khai báo autoload

Trong khoá `autoload` (và `autoload-dev`) của `composer.json`:

**`psr-4`** (cách được docs khuyên dùng): map namespace prefix sang thư mục, đúng như mục 7.

```json
{
    "autoload": {
        "psr-4": {
            "Shop\\": "src/",
            "Shop\\Legacy\\": ["lib/", "old/"]
        }
    }
}
```

- Prefix phải kết thúc bằng `\\` (trong JSON, `\` phải escape thành `\\`). Docs giải thích: `"Foo"` sẽ khớp
  cả namespace `FooBar`; `"Foo\\"` và `"FooBar\\"` mới tách bạch.
- Một prefix có thể ứng với nhiều thư mục (mảng).
- Prefix rỗng `""` là thư mục *fallback*: class thuộc namespace nào cũng được tìm ở đó.
- Thêm class mới theo PSR-4 **không** cần chạy lại gì: autoloader tìm file lúc chạy.

**`classmap`**: Composer quét các thư mục/file được liệt kê, tìm mọi class trong các file `.php` và
`.inc`, ghi thành bảng "tên class → file". Dùng cho code không theo PSR-4 (code cũ, thư viện cũ).

```json
{ "autoload": { "classmap": ["legacy/", "lib/OldHelper.php"] } }
```

Thêm class mới vào thư mục classmap thì **phải** chạy `composer dump-autoload` để quét lại.

**`files`**: danh sách file được `require` **ngay khi** `vendor/autoload.php` chạy, ở mọi request, dù có
dùng hay không. Đây là cách duy nhất để Composer nạp file chứa **hàm** (mục 6.5), ví dụ các hàm helper
`app()`, `config()`, `collect()` của Laravel nằm trong file được khai báo kiểu này.

```json
{ "autoload": { "files": ["src/helpers.php"] } }
```

Thứ tự nạp `files` theo docs: file của package được phụ thuộc nạp trước file của package phụ thuộc vào
nó; file của root package nạp **sau cùng**. Hệ quả: bạn không thể dùng `files` để định nghĩa hàm "đè" hàm
của một dependency (hàm của dependency đã được định nghĩa trước). Docs khuyên: nếu thật sự cần, `require`
file hàm của bạn **trước** dòng `require vendor/autoload.php`. Các helper của Laravel (trong
`src/Illuminate/Foundation/helpers.php` và các file `helpers.php`, `functions.php` khác mà package
`laravel/framework` khai báo trong `files`) được bọc trong `if (! function_exists('tên_hàm'))`, nên hàm
cùng tên định nghĩa trước sẽ được giữ.

⚠️ Vì `files` chạy ở mọi request, đừng để file nặng hay có tác dụng phụ trong đó.

**`psr-0`**: chuẩn cũ, đã deprecated; chỉ gặp ở dự án rất cũ.

Ngoài ra `exclude-from-classmap` loại bớt đường dẫn khỏi classmap (ví dụ thư mục test nằm lẫn trong `src/`).

### 11.2 `vendor/autoload.php` làm gì

```
require 'vendor/autoload.php'
  └─ require_once vendor/composer/autoload_real.php, gọi ComposerAutoloaderInit<hash>::getLoader()
       ├─ require platform_check.php          (kiểm tra bản PHP, mục 8.5)
       ├─ new Composer\Autoload\ClassLoader
       ├─ require autoload_static.php: đổ vào loader các bảng đã tính sẵn lúc dump
       │     classMap          FQCN => file
       │     prefixDirsPsr4    prefix => [thư mục]
       │     (bảng PSR-0, thư mục fallback...)
       ├─ $loader->register()  →  spl_autoload_register([$loader, 'loadClass'])
       └─ require từng file của mục "files" (mỗi file một lần)
```

(Đọc từ mã nguồn `AutoloadGenerator` của Composer 2.10. Composer cũng sinh các file
`autoload_classmap.php`, `autoload_psr4.php`, `autoload_namespaces.php`, `autoload_files.php` chứa cùng
thông tin dưới dạng mảng PHP; docs nói chúng dành cho trường hợp bạn muốn tự cấu hình autoloader riêng.)

Khi PHP cần một class chưa có, `ClassLoader::loadClass()` gọi `findFile()`. Đọc mã nguồn
(`src/Composer/Autoload/ClassLoader.php`, nhánh 2.10), thứ tự tra là:

1. Tra *classmap*: `isset($this->classMap[$class])`. Có thì trả đường dẫn ngay, không chạm đĩa.
2. Nếu bật *authoritative classmap* (mục 11.4), hoặc class này đã tra hụt trước đó trong cùng tiến trình
   (mảng `missingClasses`): trả `false` luôn.
3. Nếu bật APCu: tra cache APCu.
4. Tra PSR-4: đổi tên class thành đường dẫn logic `Shop/Billing/Invoice.php`, rồi cắt dần từng đoạn cuối
   của namespace để thử từ prefix **dài nhất** (`Shop\Billing\`) tới ngắn nhất (`Shop\`). Với prefix có
   đăng ký, ghép thư mục với phần còn lại và gọi `file_exists()`. (Để nhanh, các prefix được đánh chỉ mục
   theo **ký tự đầu** của tên class.)
5. Thử thư mục fallback PSR-4, rồi PSR-0, rồi `include_path` nếu được bật.
6. Không thấy: ghi vào `missingClasses`, trả `false`; `loadClass()` trả về và PHP chuyển sang autoloader
   kế tiếp (nếu có).
7. Thấy: `include` file bên trong một closure `static` được bind riêng, nên code trong file được nạp
   không truy cập được `$this` hay biến nội bộ của `ClassLoader`.

Bạn có thể lấy lại đối tượng `ClassLoader` để đăng ký thêm namespace lúc chạy (docs Composer):

```php
$loader = require __DIR__ . '/vendor/autoload.php';
$loader->addPsr4('Acme\\Test\\', __DIR__);
```

### 11.3 Khi nào phải chạy `composer dump-autoload`

| Thay đổi | Cần `dump-autoload`? |
|---|---|
| Thêm class mới vào thư mục PSR-4 (khi chưa bật tối ưu) | Không |
| Sửa khoá `autoload`/`autoload-dev` trong `composer.json` (thêm prefix, thêm `files`) | Có |
| Thêm class mới vào thư mục khai báo bằng `classmap` | Có |
| Đã bật `optimize-autoloader` (mức 1, mục 11.4) và thêm class PSR-4 mới | Không bắt buộc (vẫn tìm thấy qua PSR-4), nhưng class mới chưa vào classmap cho tới lần dump sau |
| Đã bật authoritative classmap (mức 2/A) và thêm bất kỳ class mới nào | Có, nếu không sẽ "Class not found" |

`install`, `update`, `require`, `remove` đều tự sinh lại autoloader ở cuối.

Kiểm tra code có đặt đúng chỗ theo PSR-4 không: khi tạo classmap tối ưu (`-o`), Composer so đường dẫn thật
của từng file với đường dẫn mà PSR-4 suy ra từ tên class (so sánh phân biệt hoa thường), file nào lệch thì
bị bỏ qua kèm cảnh báo. Output minh hoạ, dựng theo mã nguồn `composer/class-map-generator`:

```
Class App\Models\User located in ./app/models/User.php does not comply with psr-4 autoloading standard (rule: App\ => ./app). Skipping.
```

Thêm cờ `--strict-psr` để lệnh trả exit code lỗi khi có vi phạm (chỉ xét code của dự án, không xét
dependency), đưa vào CI. Phép so ở đây là so chuỗi đường dẫn lấy từ danh sách file trên đĩa với đường dẫn
suy từ tên class, không nhờ filesystem tra, nên về nguyên tắc nó bắt được kiểu lệch hoa thường giữa thư
mục/tên file và namespace như mục 7.5 cả trên macOS. Nó không bắt lỗi gõ sai hoa thường trong code (như
`new user()`), vì nó chỉ xét file và thư mục:

```bash
composer dump-autoload --optimize --strict-psr
```

Cờ `--strict-ambiguous` (cũng cần `--optimize`) báo lỗi khi cùng một class được tìm thấy ở nhiều file. Từ
Composer 2.10, `install` và `update` cũng có cờ `--strict-psr-autoloader` tương tự.

### 11.4 Tối ưu autoloader cho production

Ở bước 4 của mục 11.2, mỗi class chưa có trong classmap tốn ít nhất một lần `file_exists()`, tức một lời
gọi hệ thống xuống filesystem. Docs Composer ước lượng autoloader có thể chiếm "50-100ms per request in
large frameworks using a lot of classes". Ở môi trường dev, cái giá đó đổi lấy sự tiện: thêm class là
dùng được ngay. Ở production, code không đổi giữa hai lần deploy, nên tính trước được. Theo bài
"Autoloader optimization" của docs Composer, có ba mức:

| Mức | Cách bật | Làm gì | Đánh đổi |
|---|---|---|---|
| 1: Class map generation | `install/update -o` (`--optimize-autoloader`), `dump-autoload -o` (`--optimize`), hoặc config `"optimize-autoloader": true` | Quét mọi thư mục PSR-4/PSR-0, chuyển thành classmap đầy đủ. Class có trong map thì trả đường dẫn ngay, không kiểm tra filesystem | Docs: "no real trade-offs", nên luôn bật ở production. Chỉ có class **không tồn tại** (tra hụt) vẫn rơi xuống PSR-4 và kiểm tra filesystem |
| 2/A: Authoritative classmap | `-a` (`--classmap-authoritative`), hoặc config `"classmap-authoritative": true` | Tự bật mức 1. Không có trong classmap thì coi như không tồn tại, bỏ hẳn bước PSR-4 | ⚠️ Class sinh ra lúc runtime, hay file thêm vào sau khi dump, sẽ "Class not found" |
| 2/B: APCu cache | `install/update --apcu-autoloader`, `dump-autoload --apcu`, hoặc config `"apcu-autoloader": true` | Cache kết quả tra (cả thấy lẫn không thấy) vào APCu, dùng lại qua các request | Cần extension APCu, tốn bộ nhớ APCu. Không tự sinh classmap nên thường đi cùng `-o`. An toàn, không gây "not found" |

- 2/A và 2/B **không kết hợp** được; chúng giải cùng một vấn đề (tra hụt) theo hai cách.
- Mức 1 càng hiệu quả khi bật OPcache: classmap là một file PHP trả về mảng lớn, OPcache giữ nó trong bộ
  nhớ dùng chung nên nạp gần như tức thì ([Chương 18](18-fpm-nginx-opcache.md)).
- Docs khuyên **không** bật các tối ưu ở môi trường dev. Riêng skeleton Laravel đặt sẵn
  `"optimize-autoloader": true` trong `config` (mục 8.4), tức mức 1 bật cả ở dev. Điều này vô hại vì mức 1
  vẫn rơi về PSR-4 khi không thấy trong map.

### 11.5 Lệnh cài đặt khi deploy

```bash
# chạy trong thư mục dự án trên máy build hoặc server
composer install --no-dev --optimize-autoloader --no-interaction --prefer-dist
```

- `--no-dev`: không cài `require-dev`, bỏ `autoload-dev`.
- `--optimize-autoloader`: mức 1.
- `--no-interaction`: không hỏi gì (chạy trong script).
- `--prefer-dist`: tải bản đóng gói (zip) thay vì clone git; đây cũng là mặc định.

Nếu chắc chắn không có class nào sinh ra lúc runtime, thay `--optimize-autoloader` bằng
`--classmap-authoritative`. Quy trình deploy Laravel đầy đủ ở [Chương 30](30-laravel-testing-octane-deploy.md).

## 12. Scripts, `vendor/bin`, audit và Packagist

### 12.1 Scripts

Khoá `scripts` cho phép chạy lệnh vào những thời điểm Composer định sẵn (*event*), hoặc định nghĩa lệnh
riêng để cả đội gọi giống nhau. Một script có thể là lệnh shell, hoặc một static method PHP (class phải
autoload được).

Một số event hay dùng (docs "Scripts"):

| Event | Xảy ra khi |
|---|---|
| `pre-install-cmd`, `post-install-cmd` | Trước/sau `install` khi đã có lock |
| `pre-update-cmd`, `post-update-cmd` | Trước/sau `update` (hoặc `install` khi chưa có lock) |
| `pre-autoload-dump`, `post-autoload-dump` | Trước/sau khi sinh autoloader (trong `install`/`update` hoặc `dump-autoload`) |
| `post-root-package-install` | Sau khi root package được cài trong `create-project` (trước khi cài dependency) |
| `post-create-project-cmd` | Sau `create-project` |

Laravel dùng `post-autoload-dump` để chạy `php artisan package:discover`: mỗi lần autoloader được sinh lại,
Laravel đọc metadata của các package đã cài để tự đăng ký service provider của chúng
([Chương 26](26-laravel-container-provider-facade.md)).

Lệnh tự đặt tên:

```json
{
    "scripts": {
        "test": "phpunit",
        "lint": "pint --test",
        "check": [
            "@lint",
            "@test"
        ],
        "migrate-fresh": "@php artisan migrate:fresh --seed"
    }
}
```

```bash
composer test                      # chạy phpunit
composer test -- --filter=Invoice  # tham số sau -- được chuyển cho phpunit
composer check                     # chạy lint rồi test
```

- `@tên` gọi một script khác; `@php` là đúng tiến trình PHP đang chạy Composer; `@composer` là đúng
  Composer đang chạy.
- Trước khi chạy script, Composer thêm `vendor/bin` vào đầu `PATH`, nên viết `phpunit` thay vì
  `vendor/bin/phpunit` được.
- Script có timeout mặc định 300 giây (config `process-timeout`). Lệnh chạy lâu (ví dụ dev server) bọc thêm
  `Composer\Config::disableProcessTimeout`, như script `dev` của skeleton Laravel.
- Chỉ script của root package được chạy; script trong `composer.json` của dependency bị bỏ qua.

⚠️ Script chạy lệnh tuỳ ý trên máy bạn. Đọc kỹ `scripts` của dự án lạ trước khi `composer install`. Còn
*plugin* của Composer (package loại `composer-plugin`, chạy code ngay trong tiến trình Composer) thì từ
Composer 2.2 phải được cho phép rõ ràng trong `config.allow-plugins`, như khối `allow-plugins` trong
skeleton Laravel ở mục 8.4.

### 12.2 `vendor/bin`

Package có thể khai báo khoá `bin` (danh sách file lệnh). Khi cài package đó vào dự án, Composer tạo file
*proxy* trong `vendor/bin/` trỏ tới file thật. Nhờ vậy công cụ dev được cài **theo dự án**, đúng phiên bản
dự án cần, không cần cài toàn cục:

```bash
# chạy ở thư mục gốc dự án
vendor/bin/phpunit
vendor/bin/pint
vendor/bin/phpstan analyse
composer exec phpunit       # tương đương, Composer tự thêm vendor/bin vào PATH
```

Hai dự án dùng PHPUnit 11 và 12 sống chung một máy không vấn đề gì, vì mỗi dự án có `vendor/bin/phpunit`
riêng.

### 12.3 `composer audit` và chặn package có lỗ hổng

Thư viện cũng có lỗ hổng. Khi lỗ hổng được công bố, người ta ghi nó thành *security advisory* (thông báo
bảo mật: package nào, những phiên bản nào bị ảnh hưởng, mức độ). `composer audit` đối chiếu các package
đang cài với các advisory (mặc định lấy qua API của Packagist), đồng thời báo package đã bị bỏ rơi
(*abandoned*):

```bash
composer audit             # kiểm tra package đang cài
composer audit --locked    # kiểm tra theo composer.lock, không cần thư mục vendor
composer audit --no-dev    # bỏ qua require-dev
```

- Từ Composer 2.10, exit code là `0` nếu không có vấn đề, `1` nếu có. Chạy `composer audit` trong CI để
  pipeline đỏ khi có lỗ hổng mới được công bố, kể cả khi bạn không sửa dòng code nào.
- `update` và `require` tự in tóm tắt audit ở cuối.
- Composer 2.9 (11/2025) bắt đầu **chặn** việc cài bản có advisory ngay khi `update`/`require`: các bản đó
  bị loại trước khi giải ràng buộc (config `audit.block-insecure`, mặc định `true`). Composer 2.10 gom các
  thiết lập này vào khối `config.policy` (`policy.advisories.block`, mặc định `true`), thêm chặn package bị
  đánh dấu chứa mã độc (*malware*) cả khi `install`; các khoá `audit.*` cũ vẫn được đọc nhưng đã
  deprecated. Bỏ chặn tạm thời cho một lệnh: cờ `--no-blocking`.

`audit` chỉ bắt được lỗ hổng **đã công bố** trong các package. Nó không thay thế việc cập nhật dependency
thường xuyên và kiểm tra code của chính bạn ([Chương 17](17-bao-mat.md)).

### 12.4 Packagist và các nguồn package khác

*Packagist.org* là kho mặc định của Composer. Thực chất nó lưu **metadata** (tên, các phiên bản, ràng
buộc, URL nguồn) đọc từ repository git của tác giả; mã nguồn được tải từ nơi lưu trữ (ví dụ GitHub). Phát
hành một thư viện: đặt `composer.json` ở gốc repo git, đăng URL repo lên Packagist, và mỗi tag git dạng
`v1.2.0` thành một phiên bản (Composer bỏ chữ `v` ở đầu tag). Docs khuyên **không** ghi khoá `version`
trong `composer.json`, để phiên bản lấy từ tag.

Khi package không có trên Packagist, khai báo thêm nguồn trong `repositories` (root-only):

```json
{
    "repositories": [
        { "type": "vcs",  "url": "https://github.com/cong-ty/thu-vien-noi-bo" },
        { "type": "path", "url": "../packages/billing" }
    ],
    "require": {
        "cong-ty/thu-vien-noi-bo": "^1.0",
        "cong-ty/billing": "*"
    }
}
```

- `vcs`: lấy thẳng từ một repo git (kể cả repo private, cần cấu hình xác thực).
- `path`: dùng một thư mục trên máy, tiện khi phát triển nhiều package trong cùng một repo (monorepo).
- Công ty có nhiều package nội bộ thường dùng Private Packagist (dịch vụ trả phí, có bản cloud và bản tự host) hoặc Satis (tự host),
  docs Composer có mục "Hosting your own".

⚠️ Mỗi dependency là code của người khác chạy với toàn quyền của ứng dụng bạn. Trước khi thêm package:
xem nó còn được bảo trì không, bao nhiêu người dùng, ai là tác giả, và gõ đúng tên (kẻ xấu có thể đăng
package tên na ná package nổi tiếng).

## 13. Các PSR quan trọng

### 13.1 PSR là gì, và không là gì

PSR (mục 7.1) là văn bản khuyến nghị của PHP-FIG. Mỗi PSR có trạng thái: *Draft* (nháp), *Accepted* (đã
thông qua), *Deprecated* (đã thay thế), *Abandoned* (bỏ dở). Trên trang danh sách PSR của PHP-FIG lúc viết:
PSR-0 (autoload cũ) và PSR-2 (coding style cũ) là Deprecated; PSR-1, 3, 4, 6, 7, 11, 12, 13, 14, 15, 16, 17,
18, 20 là Accepted.

PSR chia làm hai loại:

- **Quy ước** (PSR-1, PSR-12, PER Coding Style, PSR-4): quy định cách viết, cách đặt file. Không có code
  để cài.
- **Interface** (PSR-3, 7, 11, 14, 15, 17, 18...): PHP-FIG phát hành package chỉ chứa interface, ví dụ
  `psr/log` chỉ có `Psr\Log\LoggerInterface` và vài lớp phụ trợ. Ai muốn thì viết *implementation* (cài
  đặt) cho interface đó: Monolog là một implementation của PSR-3.

Giá trị của PSR interface: thư viện A cần một logger, thay vì phụ thuộc vào Monolog (buộc mọi người dùng A
phải cài Monolog), A chỉ type hint `Psr\Log\LoggerInterface`. Ứng dụng dùng A truyền vào logger nào cũng
được, miễn implement interface đó. Thư viện không trói ứng dụng vào lựa chọn của mình.

Ví dụ chạy được, dùng bản rút gọn của interface PSR-3 viết ngay trong file để không cần Composer (dự án
thật thì `composer require psr/log` và bỏ khối `namespace Psr\Log`):

```php
<?php
declare(strict_types=1);

// Bản RÚT GỌN của interface PSR-3 để chạy không cần Composer.
// Dự án thật: composer require psr/log, rồi xoá khối namespace Psr\Log này.
namespace Psr\Log {
    interface LoggerInterface
    {
        public function error(string|\Stringable $message, array $context = []): void;
        public function info(string|\Stringable $message, array $context = []): void;
        // ... bản thật còn emergency, alert, critical, warning, notice, debug, log
    }
}

// Thư viện thanh toán: chỉ biết interface, không biết logger cụ thể nào.
namespace Acme\Payment {
    use Psr\Log\LoggerInterface;

    final class Gateway
    {
        public function __construct(private LoggerInterface $logger) {}

        public function charge(int $amount): bool
        {
            if ($amount <= 0) {
                $this->logger->error('Số tiền không hợp lệ: {amount}', ['amount' => $amount]);
                return false;
            }
            $this->logger->info('Đã thu {amount} VND', ['amount' => $amount]);
            return true;
        }
    }
}

// Ứng dụng: chọn cài đặt logger nào cũng được, miễn implement interface.
namespace App\Logging {
    use Psr\Log\LoggerInterface;

    final class EchoLogger implements LoggerInterface
    {
        public function error(string|\Stringable $message, array $context = []): void
        {
            echo '[ERROR] ', $this->interpolate((string) $message, $context), "\n";
        }

        public function info(string|\Stringable $message, array $context = []): void
        {
            echo '[INFO] ', $this->interpolate((string) $message, $context), "\n";
        }

        /** Thay {key} bằng giá trị trong $context, như ví dụ trong văn bản PSR-3. */
        private function interpolate(string $message, array $context): string
        {
            $replace = [];
            foreach ($context as $key => $value) {
                if (is_scalar($value) || $value instanceof \Stringable) {
                    $replace['{' . $key . '}'] = (string) $value;
                }
            }
            return strtr($message, $replace);
        }
    }

    final class MemoryLogger implements LoggerInterface
    {
        /** @var list<string> */
        public array $lines = [];

        public function error(string|\Stringable $message, array $context = []): void
        {
            $this->lines[] = 'error: ' . $message;
        }

        public function info(string|\Stringable $message, array $context = []): void
        {
            $this->lines[] = 'info: ' . $message;
        }
    }
}

namespace {
    use Acme\Payment\Gateway;
    use App\Logging\EchoLogger;
    use App\Logging\MemoryLogger;

    $gw = new Gateway(new EchoLogger());
    $gw->charge(50000);   // in ra: [INFO] Đã thu 50000 VND
    $gw->charge(-1);      // in ra: [ERROR] Số tiền không hợp lệ: -1

    $mem = new MemoryLogger();                 // đổi logger: Gateway không phải sửa dòng nào
    (new Gateway($mem))->charge(10);
    print_r($mem->lines);
    // in ra: Array ( [0] => info: Đã thu {amount} VND )   (print_r in trên nhiều dòng)
}
```

`Gateway` không `use` một class logger cụ thể nào, chỉ dùng interface. Đây là nguyên tắc *dependency
inversion* (phụ thuộc vào trừu tượng), và container của Laravel được xây quanh nó
([Chương 26](26-laravel-container-provider-facade.md)).

### 13.2 PSR-1, PSR-12 và PER Coding Style: quy ước viết code

**PSR-1 (Basic Coding Standard)** là phần tối thiểu:

- Chỉ dùng thẻ `<?php` và `<?=`.
- File PHP dùng UTF-8 không BOM.
- Một file nên **hoặc** khai báo (class, hàm, hằng) **hoặc** gây side effect (in ra, sửa ini, `require`
  file khác, ghi file...), không nên cả hai (mục 5.1).
- Namespace và class theo một PSR autoload (nay là PSR-4): mỗi class một file, có ít nhất một cấp
  namespace là vendor name.
- Tên class viết `StudlyCaps` (PSR-12 nói rõ là PascalCase: `InvoiceItem`), hằng class viết hoa có gạch
  dưới (`MAX_ITEMS`), method viết `camelCase` (`addItem`). Tên property thì PSR-1 cố ý không quy định, chỉ
  yêu cầu nhất quán.

**PSR-12 (Extended Coding Style)** (2019) thay thế PSR-2, quy định định dạng chi tiết. Vài quy tắc:

- Thụt lề 4 dấu cách, không dùng tab. Xuống dòng kiểu Unix (LF). Bỏ thẻ đóng `?>` ở file chỉ có PHP.
- Giới hạn mềm 120 ký tự mỗi dòng; không có giới hạn cứng.
- Từ khoá và kiểu viết thường; dùng dạng ngắn `bool`, `int` thay vì `boolean`, `integer`.
- Phần đầu file theo thứ tự: thẻ `<?php`, docblock của file, `declare`, `namespace`, các `use` class, các
  `use function`, các `use const`, rồi code; mỗi khối cách nhau một dòng trống. Dòng `use` không bắt đầu
  bằng `\`.

**PER Coding Style** (*PHP Evolving Recommendation*) là bản kế thừa PSR-12. PSR một khi Accepted thì gần
như đóng băng, không theo kịp cú pháp mới (enum, `readonly`, property hooks...). PER được thiết kế để cập
nhật theo phiên bản; lúc viết là PER Coding Style 3.1, có quy tắc cho cả property hooks. Văn bản PER ghi rõ
nó "extends, expands and replaces PSR-12".

Không ai nhớ hết các quy tắc này; công cụ làm thay: PHP-CS-Fixer, PHP_CodeSniffer, và Laravel Pint (bọc
PHP-CS-Fixer, preset mặc định là `laravel`, có preset `psr12` và `per`). Xem
[Chương 21](21-chat-luong-code.md).

### 13.3 PSR-3: Logger Interface

`Psr\Log\LoggerInterface` có tám method ứng với tám mức log của RFC 5424, từ nặng tới nhẹ: `emergency`,
`alert`, `critical`, `error`, `warning`, `notice`, `info`, `debug`; và method thứ chín `log($level, ...)`
nhận mức log làm tham số đầu.

- Mỗi method nhận `$message` (chuỗi hoặc object `Stringable`) và mảng `$context`.
- `$message` có thể chứa *placeholder* dạng `{tên}`, được thay bằng `$context['tên']` (như ví dụ ở mục
  13.1). Người gọi không nên tự escape giá trị, vì không biết log sẽ hiển thị ở đâu.
- Exception đính kèm phải đặt ở khoá `'exception'` của `$context`, để logger lấy được stack trace.
- Package `psr/log` còn có `NullLogger` (logger "hố đen", nhận mà không ghi gì), `AbstractLogger`,
  `LoggerTrait`, `LoggerAwareInterface`/`LoggerAwareTrait`, và class `LogLevel` chứa hằng tám mức.

Trong Laravel: `Illuminate\Log\LogManager` (thứ đứng sau facade `Log`) và `Illuminate\Log\Logger` đều
implement `Psr\Log\LoggerInterface`, nên type hint `LoggerInterface` trong constructor là nhận được logger
của Laravel; bên dưới là Monolog.

### 13.4 PSR-7 và PSR-17: HTTP message và factory

**PSR-7** định nghĩa interface cho thông điệp HTTP: `RequestInterface` và `ResponseInterface` (cùng kế
thừa `MessageInterface`), `ServerRequestInterface` (request phía server, có thêm query, cookie, file
upload, attribute), `StreamInterface` (body), `UriInterface`, `UploadedFileInterface`.

Đặc điểm quan trọng nhất: message là **bất biến** (*immutable*). Văn bản PSR-7 viết: mọi method có thể
thay đổi trạng thái phải giữ nguyên object hiện tại và trả về một object mới chứa thay đổi. Các method đó
có tiền tố `with`: `withHeader()`, `withStatus()`, `withBody()`...

Mô phỏng phong cách đó để thấy cái bẫy:

```php
<?php
declare(strict_types=1);

// Mô phỏng phong cách PSR-7: object bất biến, mọi method with...() trả về object MỚI.
final class Request
{
    /** @param array<string, string> $headers */
    public function __construct(
        public readonly string $method,
        public readonly string $uri,
        private array $headers = [],
    ) {}

    public function withHeader(string $name, string $value): static
    {
        $new = clone $this;                      // giữ nguyên $this
        $new->headers[strtolower($name)] = $value;
        return $new;
    }

    public function getHeaderLine(string $name): string
    {
        return $this->headers[strtolower($name)] ?? '';
    }
}

$req = new Request('GET', '/orders');

$req->withHeader('X-Trace-Id', 'abc');            // ⚠️ bug: kết quả bị vứt đi
var_dump($req->getHeaderLine('X-Trace-Id'));      // in ra: string(0) ""

$req2 = $req->withHeader('X-Trace-Id', 'abc');    // đúng: nhận object mới
var_dump($req2->getHeaderLine('x-trace-id'));     // in ra: string(3) "abc"
var_dump($req === $req2);                         // in ra: bool(false)
```

Với object PSR-7 thật (ví dụ của Guzzle hay `nyholm/psr7`) cũng vậy: gọi `with...()` mà không gán kết
quả là không có gì thay đổi. (Cách làm "wither" bằng `clone` đã học ở [Chương 10](10-oop-nang-cao.md).)

**PSR-17** bổ sung các interface *factory* để tạo object PSR-7 mà không phụ thuộc vào thư viện cụ thể:
`RequestFactoryInterface::createRequest($method, $uri)`, `ResponseFactoryInterface::createResponse($code,
$reasonPhrase)`, `StreamFactoryInterface::createStream($content)`, `UriFactoryInterface`,
`ServerRequestFactoryInterface`, `UploadedFileFactoryInterface`. Thư viện cần tạo request (ví dụ SDK gọi
API) nhận một factory PSR-17 thay vì `new` một class Request cụ thể.

⚠️ `Illuminate\Http\Request` của Laravel kế thừa `Symfony\Component\HttpFoundation\Request`, **không**
implement PSR-7 và **có thể thay đổi** (*mutable*): `$request->merge([...])` sửa thẳng object. Docs
Laravel 13 hướng dẫn: muốn nhận request PSR-7, cài `symfony/psr-http-message-bridge` và `nyholm/psr7`, rồi
type hint `Psr\Http\Message\ServerRequestInterface` trong route hoặc controller; trả về response PSR-7 thì
Laravel tự chuyển lại thành response của nó.

### 13.5 PSR-18: HTTP client

`Psr\Http\Client\ClientInterface` có đúng một method:

```php
public function sendRequest(RequestInterface $request): ResponseInterface;
```

Kèm các interface exception: `ClientExceptionInterface` (mọi lỗi của client), `RequestExceptionInterface`
(request không hợp lệ), `NetworkExceptionInterface` (lỗi mạng, không nhận được response). Guzzle 7
implement PSR-18 (`GuzzleHttp\Client implements ... \Psr\Http\Client\ClientInterface`). Một SDK viết theo
PSR-18 + PSR-17 chạy được với bất kỳ HTTP client nào mà ứng dụng chọn. HTTP client của Laravel (facade
`Http`) là lớp bọc quanh Guzzle.

### 13.6 PSR-15: request handler và middleware

PSR-15 chuẩn hoá phía server, dựa trên PSR-7:

```php
interface RequestHandlerInterface
{
    public function handle(ServerRequestInterface $request): ResponseInterface;
}

interface MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface;
}
```

Middleware nhận request, có thể trả response luôn (ví dụ chưa đăng nhập thì trả 401) hoặc gọi
`$handler->handle($request)` để chuyển tiếp cho tầng trong rồi xử lý response trả về. Framework theo
PSR-15: Mezzio, Slim 4.

⚠️ Middleware của Laravel **không** theo PSR-15: nó nhận `Illuminate\Http\Request` và một `Closure $next`
(`handle($request, Closure $next)`), xem [Chương 24](24-laravel-routing-controller-middleware.md). Ý tưởng
"củ hành" giống nhau, interface khác nhau.

### 13.7 PSR-11: container

```php
interface ContainerInterface
{
    public function get(string $id);           // lấy entry; không có thì ném NotFoundExceptionInterface
    public function has(string $id): bool;
}
```

PSR-11 chỉ chuẩn hoá phần **đọc** từ container (*dependency injection container*: nơi giữ và tạo các
object của ứng dụng). Cách đăng ký (bind) thì mỗi container một kiểu. Contract
`Illuminate\Contracts\Container\Container` của Laravel kế thừa `Psr\Container\ContainerInterface`, nên
container Laravel dùng được ở chỗ nào đòi container PSR-11. ([Chương 26](26-laravel-container-provider-facade.md).)

### 13.8 PSR-14: event dispatcher

```php
interface EventDispatcherInterface
{
    public function dispatch(object $event);
}

interface ListenerProviderInterface
{
    public function getListenersForEvent(object $event): iterable;
}

interface StoppableEventInterface
{
    public function isPropagationStopped(): bool;
}
```

Event là một object bất kỳ; *listener* là một callable nhận đúng một tham số là event. Dispatcher hỏi
*listener provider* danh sách listener cho event đó rồi gọi lần lượt; event implement
`StoppableEventInterface` thì dispatcher dừng khi `isPropagationStopped()` trả `true`. Symfony
EventDispatcher theo PSR-14. Dispatcher event của Laravel (`Illuminate\Events\Dispatcher`) dùng contract
riêng, không implement PSR-14 ([Chương 29](29-laravel-queue-event-schedule-cache.md)).

### 13.9 Bảng tổng hợp

| PSR | Về gì | Interface chính | Gặp ở đâu |
|---|---|---|---|
| 1, 12, PER CS | Quy ước viết và định dạng code | (không có) | Pint, PHP-CS-Fixer, PHP_CodeSniffer |
| 3 | Logger | `LoggerInterface` | Monolog; logger của Laravel |
| 4 | Autoload | (không có) | Mọi package Composer |
| 6, 16 | Cache (PSR-6 đầy đủ với pool/item; PSR-16 đơn giản `get`/`set`) | `CacheItemPoolInterface`; `CacheInterface` | Contract `Cache\Repository` của Laravel kế thừa PSR-16 `CacheInterface` |
| 7 | HTTP message bất biến | `RequestInterface`, `ResponseInterface`, `ServerRequestInterface`... | Guzzle, Slim, `nyholm/psr7` |
| 11 | Container (phần đọc) | `ContainerInterface` | Container Laravel |
| 14 | Event dispatcher | `EventDispatcherInterface` | Symfony EventDispatcher |
| 15 | Server request handler, middleware | `RequestHandlerInterface`, `MiddlewareInterface` | Mezzio, Slim 4 (không phải Laravel) |
| 17 | Factory tạo object PSR-7 | `RequestFactoryInterface`, `ResponseFactoryInterface`... | Thư viện cần tạo request/response |
| 18 | HTTP client | `ClientInterface::sendRequest()` | Guzzle 7 |
| 20 | Đồng hồ | `ClockInterface::now()` | Giả lập thời gian khi test |

Khi một package khai báo trong `composer.json` rằng nó `provide` một "virtual package" như
`psr/log-implementation`, thư viện khác có thể `require` thứ đó để đòi "một implementation PSR-3 bất kỳ".
`laravel/framework` khai báo `provide` cho `psr/container-implementation`, `psr/log-implementation` và
`psr/simple-cache-implementation`.

## 14. Đối chiếu với Java và Go

| Khía cạnh | PHP | Java | Go |
|---|---|---|---|
| Nhóm tên | `namespace App\Billing;` | `package com.acme.billing;` | `package billing` (theo quy ước trùng tên thư mục) |
| Gắn với thư mục | Chỉ là quy ước của autoloader (PSR-4) | Quy ước chuẩn, công cụ build và classpath dựa vào nó | Bắt buộc: một thư mục là một package |
| Import | `use App\Billing\Invoice;` lúc biên dịch, theo file | `import com.acme.billing.Invoice;` lúc biên dịch | `import "example.com/shop/billing"`, import cả package |
| Kiểm soát truy cập theo nhóm | Không có (namespace không ảnh hưởng visibility) | Có: package-private | Có: tên viết hoa mới được export |
| Nạp code lúc chạy | Autoload lazy theo class | ClassLoader nạp class lazy, ý tưởng rất giống | Biên dịch tĩnh cả chương trình, không có nạp lúc chạy |
| Quản lý dependency | Composer, kho Packagist | Maven/Gradle, kho Maven Central | `go` command, module proxy |
| Ràng buộc và kết quả | `composer.json` + `composer.lock` | `pom.xml`/`build.gradle` (+ Gradle lockfile tuỳ chọn) | `go.mod` + `go.sum` (checksum) |
| Chọn phiên bản | Bản **cao nhất** thoả ràng buộc, rồi khoá lại | Maven: bản "gần nhất" trong cây; Gradle: bản cao nhất khi xung đột | *Minimal version selection*: bản **thấp nhất** thoả mọi yêu cầu, nên lặp lại được ngay cả không có lock |

Điểm đáng nhớ nhất: Composer cần lock file để build lặp lại được, vì mặc định nó chọn bản mới nhất. Go
chọn bản tối thiểu nên `go.mod` tự nó đã xác định kết quả; `go.sum` chỉ để kiểm tra tính toàn vẹn.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| `Class "App\Util\DateTime" not found` | Trong namespace, tên class trơn được ghép namespace hiện tại; class không fallback về toàn cục | `use DateTime;` hoặc viết `\DateTime` |
| `catch (Exception $e)` trong namespace không bắt được gì | `catch` một class không tồn tại không báo lỗi, chỉ không khớp | `use Exception;`/`\Exception`; bật PHPStan |
| `new $ten` với `$ten = 'User'` tìm sai class | Tên trong chuỗi luôn là tên đầy đủ, `use` không áp dụng | Dùng `User::class` |
| `"App\Models\name"` trong nháy kép hỏng | `\n` là ký tự xuống dòng | Nháy đơn, hoặc `::class` |
| `require 'config.php'` chạy được ở máy này, hỏng ở cron | Đường dẫn tương đối phụ thuộc thư mục làm việc và `include_path` | `require __DIR__ . '/config.php';` |
| Autoloader `throw` khi không tìm thấy | Exception chặn các autoloader sau; `class_exists()` thành ném lỗi | Không thấy thì `return` im lặng (PSR-4) |
| Hai class trong một file, class thứ hai "not found" | Autoloader tìm file theo tên class | Một file một class |
| Chạy trên macOS, "Class not found" trên Linux | Filesystem macOS không phân biệt hoa thường, Linux có | Đúng hoa thường; CI chạy Linux; `dump-autoload -o --strict-psr` |
| Thêm prefix vào `autoload` nhưng class vẫn "not found" | Bảng autoload chỉ được sinh lại khi dump | `composer dump-autoload` |
| Không commit `composer.lock` | Mỗi lần cài là một lần giải ràng buộc mới, mỗi nơi một bộ phiên bản | Ứng dụng luôn commit lock |
| `composer update` trên production | Cài bản chưa test, tốn tài nguyên | Production chỉ `composer install --no-dev -o` |
| Ràng buộc `*` hoặc `>=1.0` | `update` có thể kéo về bản MAJOR mới | Dùng `^x.y` |
| Nghĩ `^0.3` sẽ tự lên `0.4` | Với `0.x`, `^` khoá MINOR | Hiểu luật `0.x`, tự nâng có chủ đích |
| Code production dùng package trong `require-dev` | Production cài `--no-dev` | Package cần lúc chạy để trong `require`; CI thử `--no-dev` |
| Bật `--classmap-authoritative` khi có class sinh lúc runtime | Không có trong classmap là coi như không tồn tại | Chỉ dùng mức 1 (`-o`) hoặc APCu |
| Sửa tay conflict trong `composer.lock` | Lock trộn bằng văn bản có thể không hợp lệ | Lấy lock một bên, chạy lại `require`/`remove` của bên kia |
| `$req->withHeader(...)` không gán lại | Object PSR-7 bất biến, method trả object mới | `$req = $req->withHeader(...)` |

## Tóm tắt chương

- Namespace là "thư mục" cho tên class, interface, trait, enum, hàm và hằng `const`; nó chỉ là một phần
  của tên, không tạo ra quyền truy cập và không gắn với thư mục trên đĩa.
- Tên có ba dạng: trơn (`User`), có tiền tố (`Models\User`), đầy đủ (`\App\Models\User`). `use` thêm một
  bảng alias, phân giải lúc biên dịch, theo từng file, và không nạp gì cả.
- Class không bao giờ fallback về namespace toàn cục (fallback cho class từng gây rắc rối với autoload,
  mục 3.2); hàm và hằng tên trơn thì có. Viết
  `\strlen` hay `use function strlen;` giúp trình biên dịch dùng opcode chuyên biệt.
- Tên trong chuỗi luôn là tên đầy đủ; `X::class` là cách an toàn để có chuỗi đó, và không gây autoload.
- `include`/`require` nạp và chạy file ngay tại chỗ; luôn ghép đường dẫn với `__DIR__`. Autoload thay
  danh sách `require` bằng một hàm được gọi khi gặp class chưa có; nó lazy và chỉ dành cho class.
- PSR-4: namespace prefix ứng với base directory, phần còn lại thành thư mục con, tên class thành tên
  file; hoa thường phải khớp; autoloader không được ném lỗi.
- Composer: `composer.json` là ràng buộc, `composer.lock` là kết quả. `update` quyết định và ghi lock,
  `install` cài đúng lock. Ứng dụng commit lock; production chạy `install --no-dev --optimize-autoloader`.
- `^1.2.3` = `>=1.2.3 <2.0.0`, `~1.2` = `>=1.2 <2.0`, `~1.2.3` = `>=1.2.3 <1.3.0`, `^0.3` = `>=0.3.0 <0.4.0`.
- Tối ưu autoloader: mức 1 (`-o`, classmap) luôn bật ở production; 2/A (`-a`) hoặc 2/B (APCu), chọn một.
  `composer audit` trong CI; Composer 2.9+ chặn sẵn bản có advisory khi update.
- PSR interface (3, 7, 11, 14, 15, 17, 18) cho phép thư viện phụ thuộc vào trừu tượng; Laravel implement
  PSR-3, PSR-11, PSR-16, nhưng Request và middleware của nó không theo PSR-7/PSR-15.

## Câu hỏi tự kiểm tra

1. Trong file có `namespace App\Report;`, ba dòng `new Pdf()`, `new Export\Pdf()`, `new \Pdf()` lần lượt
   tìm class nào? Thêm `use Vendor\Pdf;` ở đầu file thì sao?
2. Vì sao `strlen('abc')` chạy được trong namespace mà `new ArrayObject()` thì không? Vì sao PHP thiết kế
   như vậy? (mục 3.2, 3.4)
3. Một đồng nghiệp viết `catch (Exception $e)` trong service thuộc namespace `App\Services`. Chuyện gì
   xảy ra khi có exception, và vì sao PHP không báo lỗi ngay từ đầu?
4. `use App\Models\User;` có làm PHP nạp file `User.php` không? `User::class` thì sao? `new User()` thì
   sao? (mục 4.4, 6.4)
5. Theo PSR-4, với prefix `Acme\Shop\` ứng với `packages/shop/src/`, class `Acme\Shop\Cart\Item` nằm ở file
   nào? Class `Acme\Shop_Admin\User` có được autoloader đó tìm không?
6. Vì sao autoloader không được ném exception khi không tìm thấy class?
7. Giải thích bằng lời của bạn sự khác nhau giữa `composer install` và `composer update`. Lệnh nào chạy
   trên CI, lệnh nào chạy trên production, lệnh nào chạy khi muốn nâng thư viện?
8. Ràng buộc `^2.4`, `~2.4`, `~2.4.1`, `^0.4.1` lần lượt nhận những phiên bản nào? Bản `2.10.0` có thoả
   `~2.4.1` không?
9. Ba mức tối ưu autoloader khác nhau ở đâu? Vì sao mức 2/A có thể làm production báo "Class not found"
   trong khi mức 1 thì không? (mục 11.4)
10. Một thư viện cần ghi log và gọi HTTP. Nên type hint những interface nào để không trói người dùng vào
    Monolog hay Guzzle? (mục 13)

## Bài tập

1. **Tự viết autoloader PSR-4 có cache tra hụt.** Mở rộng `Psr4Autoloader` ở mục 7.3: thêm một mảng ghi
   nhớ các class đã tra hụt để lần sau trả về ngay mà không gọi `is_file()`, và một method đếm số lần
   `is_file()` đã được gọi. Viết `main.php` gọi `class_exists()` ba lần cho cùng một class không tồn tại
   và in số lần `is_file()` trước và sau khi có cache. Chạy bằng `php main.php`.
2. **Bẫy namespace.** Tạo một file trong `namespace App\Jobs;` có: một hàm `retry()` dùng `sleep()` và
   `time()`, một khối `try/catch` bắt `RuntimeException`, và một chỗ `new DateTimeImmutable()`. Viết sai
   cố ý (không `use`, không `\`) rồi chạy để quan sát lỗi nào lộ ra ngay, lỗi nào im lặng. Sửa lại theo
   hai cách: dùng `use` và dùng `\`. Ghi lại nhận xét.
3. **Dự án Composer đầu tiên** (cần Composer và mạng). Tạo thư mục `shop/`, chạy `composer init`, khai
   báo autoload PSR-4 `"Shop\\": "src/"`, chuyển ba class của mục 6.3 vào `src/`, bỏ `autoload.php` tự
   viết và dùng `vendor/autoload.php`. Thêm một package thật bằng `composer require` (ví dụ
   `ramsey/uuid` để sinh mã đơn hàng), một package dev bằng `composer require --dev` (ví dụ
   `phpunit/phpunit`). Sau đó: mở `composer.lock` tìm phiên bản chính xác đã chọn; xoá `vendor/` và chạy
   `composer install --no-dev`, kiểm tra `vendor/bin/phpunit` còn không; chạy
   `composer dump-autoload -o --strict-psr` sau khi cố ý đổi tên thư mục `src/Models` thành `src/models`.
4. **Đọc ràng buộc.** Với package giả định có các bản `1.4.0, 1.4.7, 1.5.0, 1.10.2, 2.0.0-RC1, 2.0.0, 2.1.3`,
   lập bảng cho biết `composer update` sẽ chọn bản nào với từng ràng buộc: `^1.4`, `~1.4`, `~1.4.0`,
   `1.4.*`, `>=1.5 <2.0`, `^2.0`, `^2.0@RC` (giả sử `minimum-stability` là `stable`). Kiểm tra lại bằng
   semver.madewithlove.com.

## Đọc thêm

- PHP Manual, Namespaces: [Overview](https://www.php.net/manual/en/language.namespaces.rationale.php),
  [Defining namespaces](https://www.php.net/manual/en/language.namespaces.definition.php),
  [Using namespaces: Basics](https://www.php.net/manual/en/language.namespaces.basics.php),
  [Aliasing/Importing](https://www.php.net/manual/en/language.namespaces.importing.php),
  [Fallback to global](https://www.php.net/manual/en/language.namespaces.fallback.php),
  [Name resolution rules](https://www.php.net/manual/en/language.namespaces.rules.php),
  [FAQ](https://www.php.net/manual/en/language.namespaces.faq.php)
- PHP RFC: [Treat namespaced names as single token](https://wiki.php.net/rfc/namespaced_names_as_token) (PHP 8.0)
- PHP Manual: [include](https://www.php.net/manual/en/function.include.php),
  [require](https://www.php.net/manual/en/function.require.php),
  [Autoloading Classes](https://www.php.net/manual/en/language.oop5.autoload.php),
  [spl_autoload_register](https://www.php.net/manual/en/function.spl-autoload-register.php)
- PHP-FIG: [danh sách PSR](https://www.php-fig.org/psr/), [PSR-1](https://www.php-fig.org/psr/psr-1/),
  [PSR-4](https://www.php-fig.org/psr/psr-4/) (và [ví dụ cài đặt](https://www.php-fig.org/psr/psr-4/examples/)),
  [PSR-12](https://www.php-fig.org/psr/psr-12/), [PER Coding Style](https://www.php-fig.org/per/coding-style/),
  [PSR-3](https://www.php-fig.org/psr/psr-3/), [PSR-7](https://www.php-fig.org/psr/psr-7/),
  [PSR-11](https://www.php-fig.org/psr/psr-11/), [PSR-14](https://www.php-fig.org/psr/psr-14/),
  [PSR-15](https://www.php-fig.org/psr/psr-15/), [PSR-17](https://www.php-fig.org/psr/psr-17/),
  [PSR-18](https://www.php-fig.org/psr/psr-18/)
- [Semantic Versioning 2.0.0](https://semver.org/)
- Composer docs: [Introduction](https://getcomposer.org/doc/00-intro.md),
  [Basic usage](https://getcomposer.org/doc/01-basic-usage.md),
  [Libraries](https://getcomposer.org/doc/02-libraries.md),
  [Command-line interface](https://getcomposer.org/doc/03-cli.md),
  [The composer.json schema](https://getcomposer.org/doc/04-schema.md),
  [Config](https://getcomposer.org/doc/06-config.md),
  [Versions and constraints](https://getcomposer.org/doc/articles/versions.md),
  [Autoloader optimization](https://getcomposer.org/doc/articles/autoloader-optimization.md),
  [Scripts](https://getcomposer.org/doc/articles/scripts.md),
  [Vendor binaries](https://getcomposer.org/doc/articles/vendor-binaries.md),
  [Resolving merge conflicts](https://getcomposer.org/doc/articles/resolving-merge-conflicts.md),
  [CHANGELOG](https://github.com/composer/composer/blob/main/CHANGELOG.md)
- Mã nguồn Composer: [ClassLoader.php](https://github.com/composer/composer/blob/2.10/src/Composer/Autoload/ClassLoader.php),
  [AutoloadGenerator.php](https://github.com/composer/composer/blob/2.10/src/Composer/Autoload/AutoloadGenerator.php)
- Laravel 13: [composer.json của skeleton](https://github.com/laravel/laravel/blob/13.x/composer.json),
  [Requests: PSR-7 Requests](https://laravel.com/docs/13.x/requests#psr7-requests)
