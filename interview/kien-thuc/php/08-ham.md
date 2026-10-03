# Chương 08. Hàm

> [← Mục lục](README.md) · [← Chương 07: Toán tử và cấu trúc điều khiển](07-toan-tu-dieu-khien.md) · [Chương 09: OOP cơ bản: class và object →](09-oop-co-ban.md)

**Bạn sẽ học được:**

- Khai báo và gọi hàm, khai báo kiểu cho tham số và giá trị trả về (kể cả `void`, `never`, `static`),
  và `strict_types` tác động lên lời gọi hàm chính xác ra sao.
- Các cách truyền đối số: giá trị mặc định, named arguments, variadic `...$args`, truyền tham chiếu
  `&`, và khi nào nên hoặc không nên dùng từng cách.
- Phạm vi biến trong hàm, từ khoá `global`, biến `static`.
- Hàm ẩn danh (closure) với `use`, arrow function `fn`, callable, first-class callable `strlen(...)`,
  `Closure::fromCallable()` và `Closure::bind()`.
- Viết hàm đệ quy đúng và biết giới hạn của đệ quy trong PHP.
- Phân biệt hàm có sẵn với hàm tự viết, và dùng attribute `#[\NoDiscard]` của PHP 8.5.

**Cần biết trước:** [Chương 03](03-cu-phap-bien-hang.md) (biến), [Chương 04](04-kieu-du-lieu.md)
(kiểu dữ liệu, type declaration, `strict_types`), [Chương 06](06-mang.md) (mảng, destructuring),
[Chương 07](07-toan-tu-dieu-khien.md) (toán tử, `if`, vòng lặp).

Mọi ví dụ trong chương đã được chạy thật trên PHP 8.5 (và các bản cũ hơn khi chương nói về khác biệt
giữa các bản). Cách chạy thử không cần cài PHP lên máy:

```bash
# Chạy trên máy của bạn (cần Docker). Mở REPL tương tác:
docker run --rm -it php:8.5-cli php -a
# Hoặc chạy một file trong thư mục hiện tại:
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php vidu.php
```

## 1. Hàm là gì

### 1.1 Ý tưởng

*Hàm* (*function*) là một đoạn code được đặt tên, nhận đầu vào, làm một việc, rồi trả lại kết quả.
Hình dung như một cái máy: bỏ nguyên liệu vào, máy chạy, ra thành phẩm. Bạn không cần biết bên trong
máy làm gì mỗi lần dùng, chỉ cần biết nó nhận gì và trả gì.

Vì sao cần hàm:

1. Không lặp code. Một công thức viết ở một chỗ. Khi công thức đổi, sửa đúng một chỗ.
2. Đặt tên cho một ý. Đọc `orderTotal(2, 150_000, 30_000)` hiểu ngay đang tính tổng tiền đơn
   hàng, không phải giải mã `2 * 150_000 + 30_000`.
3. Chia nhỏ để kiểm tra. Mỗi hàm nhỏ test riêng được, sai thì biết sai ở đâu.
4. Cô lập biến. Biến tạo trong hàm không lọt ra ngoài và không đè lên biến bên ngoài (mục 9).

```php
<?php
declare(strict_types=1);

// Không dùng hàm: công thức lặp lại ở mọi chỗ cần tính
$total1 = 2 * 150_000 + 30_000;
$total2 = 1 * 99_000 + 30_000;

// Dùng hàm: công thức nằm ở một chỗ và có tên
function orderTotal(int $quantity, int $unitPrice, int $shippingFee): int
{
    return $quantity * $unitPrice + $shippingFee;
}

echo orderTotal(2, 150_000, 30_000), "\n";   // in ra: 330000
echo orderTotal(1, 99_000, 30_000), "\n";    // in ra: 129000
```

Chuyện gì xảy ra khi gọi `orderTotal(2, 150_000, 30_000)`:

```
code gọi hàm                               bên trong orderTotal()
------------                               ----------------------
orderTotal(2, 150000, 30000)  ──────────►  $quantity    = 2
                                           $unitPrice   = 150000
                                           $shippingFee = 30000
                                           return 2 * 150000 + 30000
                    330000    ◄──────────  hàm kết thúc, giá trị trả về
echo 330000                                 "thay vào" chỗ gọi hàm
```

Hai từ cần phân biệt ngay từ đầu, vì manual PHP và thông báo lỗi dùng cả hai:

- *Tham số* (*parameter*): biến khai báo trong định nghĩa hàm, ở đây là `$quantity`, `$unitPrice`,
  `$shippingFee`.
- *Đối số* (*argument*): giá trị thật truyền vào lúc gọi, ở đây là `2`, `150_000`, `30_000`.

PHP tính các đối số từ trái sang phải, xong hết rồi mới gán vào tham số và chạy hàm (manual gọi là
*eager evaluation*).

### 1.2 Cú pháp khai báo

```
function  orderTotal  ( int $quantity, int $unitPrice, int $shippingFee )  : int  { ... }
   │          │                          │                                   │        │
 từ khoá   tên hàm             danh sách tham số (có thể rỗng)          kiểu trả về  thân hàm
```

- Tên hàm theo luật đặt tên chung của PHP: bắt đầu bằng chữ cái hoặc `_`, sau đó là chữ cái, chữ số,
  `_`. Byte từ `0x80` tới `0xff` cũng hợp lệ, nên về kỹ thuật tên tiếng Việt có dấu chạy được, nhưng
  đừng dùng.
- Tên hàm không phân biệt hoa thường với các chữ cái ASCII: `greet()`, `GREET()`, `Greet()` là
  một hàm. Biến thì ngược lại, `$name` và `$Name` là hai biến khác nhau. Vẫn nên gọi đúng như lúc khai
  báo cho dễ đọc và dễ tìm kiếm.
- Quy ước đặt tên: hàm có sẵn của PHP dùng `snake_case` (`str_contains`, `array_map`), helper của
  Laravel cũng vậy (`data_get`). Method trong class theo chuẩn PSR-1 dùng `camelCase`. Chọn một kiểu
  và giữ nhất quán trong dự án.
- Từ PHP 8.0 danh sách tham số được phép có dấu phẩy thừa ở cuối (*trailing comma*); danh sách đối số
  lúc gọi thì được phép từ PHP 7.3. Rất tiện khi xuống dòng mỗi tham số một dòng:

```php
function createUser(
    string $email,
    string $name,
    bool $isAdmin = false,   // dấu phẩy cuối hợp lệ từ PHP 8.0
): void {
    // ...
}
```

### 1.3 Gọi trước khi khai báo, và hàm khai báo có điều kiện

Hàm khai báo ở cấp cao nhất của file (không nằm trong `if`, trong hàm khác...) được PHP đăng ký ngay
lúc biên dịch file, nên gọi ở dòng phía trên chỗ khai báo vẫn chạy. Hàm nằm trong `if` thì chỉ
tồn tại khi dòng khai báo đó được chạy tới:

```php
<?php
declare(strict_types=1);

echo greet('An'), "\n";        // in ra: Xin chào, An!  (gọi trước dòng khai báo vẫn được)
echo GREET('Bình'), "\n";      // in ra: Xin chào, Bình!  (tên hàm không phân biệt hoa thường)

function greet(string $name): string
{
    return "Xin chào, {$name}!";
}

var_dump(function_exists('debugLog'));   // in ra: bool(false)

$debug = true;
if ($debug) {
    // Hàm khai báo trong if chỉ tồn tại khi dòng này được chạy tới
    function debugLog(string $msg): void
    {
        echo "[debug] {$msg}\n";
    }
}

var_dump(function_exists('debugLog'));   // in ra: bool(true)
debugLog('đã định nghĩa');               // in ra: [debug] đã định nghĩa
```

Nếu gọi `debugLog()` ở dòng trước khối `if`, PHP ném `Error: Call to undefined function
debugLog()`.

Bạn sẽ gặp kiểu khai báo có điều kiện này trong code thật: các file `helpers.php` của Laravel bọc mỗi
helper trong `if (! function_exists('data_get')) { function data_get(...) {...} }`. Nhờ vậy nếu ứng
dụng đã tự định nghĩa một hàm cùng tên trước đó thì Laravel bỏ qua, không gây lỗi khai báo trùng.

Hàm khai báo bên trong một hàm khác cũng vậy: nó chỉ xuất hiện khi hàm ngoài chạy, và khi đã xuất hiện
thì là hàm toàn cục (gọi được từ bất cứ đâu), không phải hàm "con" riêng của hàm ngoài. Gọi hàm
ngoài lần thứ hai sẽ khai báo lại hàm trong và gây lỗi (mục 1.5). Trong code hiện đại gần như không
ai viết hàm lồng hàm; muốn một hàm "dùng tạm" bên trong hàm khác thì dùng closure (mục 10).

### 1.4 `return`: trả kết quả và kết thúc hàm

`return biểu_thức;` làm hai việc: kết thúc hàm ngay lập tức và đưa giá trị về chỗ gọi. Hàm không
có `return` (hoặc chỉ có `return;`) trả về `null`.

```php
<?php
declare(strict_types=1);

function shippingFee(int $weightGram): int
{
    if ($weightGram <= 0) {
        return 0;                 // return kết thúc hàm ngay, các dòng dưới không chạy
    }
    if ($weightGram <= 1000) {
        return 20_000;
    }
    return 20_000 + intdiv($weightGram - 1000, 500) * 5_000;
}

function sayHi(string $name)
{
    echo "Hi {$name}\n";          // không có return
}

echo shippingFee(0), ' ', shippingFee(800), ' ', shippingFee(2600), "\n";   // in ra: 0 20000 35000
var_dump(sayHi('An'));            // in ra: Hi An  rồi  NULL

function minMax(array $numbers): array
{
    return [min($numbers), max($numbers)];
}

[$lo, $hi] = minMax([3, 9, 1, 7]);
echo "{$lo} {$hi}\n";             // in ra: 1 9
```

Hai thói quen tốt rút ra từ ví dụ:

- Return sớm (*early return*, *guard clause*): xử lý các trường hợp đặc biệt trước và `return`
  luôn, phần còn lại của hàm là "đường chính" không bị lồng trong nhiều tầng `if/else`.
- Trả nhiều giá trị bằng array: một hàm PHP chỉ trả một giá trị. Muốn trả nhiều thứ thì trả
  array rồi tách bằng destructuring `[$lo, $hi] = ...` (xem [Chương 06](06-mang.md)), hoặc trả array có
  key `['min' => ..., 'max' => ...]` để rõ nghĩa hơn. Khi nhóm giá trị đó có ý nghĩa riêng và được dùng
  ở nhiều nơi, nên tạo một class nhỏ ([Chương 09](09-oop-co-ban.md)).

Đối chiếu: Go cho phép trả nhiều giá trị thật sự (`func minMax(xs []int) (int, int)`), và dùng điều
đó để trả lỗi kèm kết quả (`v, err := f()`). PHP không có cơ chế này; lỗi trong PHP được báo bằng
exception ([Chương 12](12-loi-exception.md)).

### 1.5 Không overload, không khai báo lại

- PHP không có overload (*function overloading*): không thể có hai hàm cùng tên khác danh sách
  tham số như Java. Muốn một hàm nhận nhiều dạng đầu vào thì dùng tham số mặc định (mục 5), union type
  (mục 3), hoặc variadic (mục 7). Go cũng không có overload.
- Không thể khai báo lại hay xoá một hàm đã tồn tại. Khai báo hai lần cùng tên (kể cả khác hoa
  thường) là lỗi fatal ngay lúc biên dịch:

```php
<?php
declare(strict_types=1);

function hello(): void {}
function HELLO(): void {}
// Fatal error: Cannot redeclare function HELLO() (previously declared in ...:4) in ... on line 5
```

- Hàm có sẵn cũng không khai báo lại được: viết `function strlen(...)` trong file không có namespace
  báo `Fatal error: Cannot redeclare function strlen()`. (Từ PHP 8.4 thông báo có thêm chữ `function`;
  PHP 8.3 trở về trước là `Cannot redeclare strlen()`.) Bên trong một namespace thì bạn được đặt hàm
  trùng tên với hàm có sẵn, xem [Chương 11](11-namespace-composer.md).
- Mọi hàm (và class) trong PHP đều có phạm vi toàn cục: một khi đã được định nghĩa, nó gọi được từ bất
  cứ đâu trong request đó.

## 2. Tham số và đối số

### 2.1 Truyền theo giá trị là mặc định

Mặc định PHP truyền đối số *theo giá trị* (*by value*): tham số nhận một bản sao của giá trị. Hàm
sửa tham số thì chỉ sửa bản sao, biến bên ngoài giữ nguyên.

```php
<?php
declare(strict_types=1);

function addTax(int $price): int
{
    $price = $price + intdiv($price, 10);   // sửa bản sao bên trong hàm
    return $price;
}

$p = 100;
echo addTax($p), "\n";   // in ra: 110
echo $p, "\n";           // in ra: 100  (biến bên ngoài không đổi)

function addItem(array $cart, string $item): array
{
    $cart[] = $item;     // sửa bản sao của array
    return $cart;
}

$cart = ['táo'];
$newCart = addItem($cart, 'cam');
echo count($cart), ' ', count($newCart), "\n";   // in ra: 1 2
```

Array cũng được truyền theo giá trị. Khác với Java, nơi biến kiểu `List` giữ tham chiếu tới object nên
hàm nhận cùng một danh sách, và khác với slice của Go (slice chia sẻ mảng nền bên dưới). Hai câu hỏi tự nhiên:

- *Truyền array lớn vào hàm có chậm không?* Không, nếu hàm chỉ đọc. PHP dùng *copy-on-write*: lúc truyền, hàm và bên
  ngoài cùng trỏ tới một array, chỉ khi một bên sửa thì PHP mới thật sự copy. Hàm chỉ đọc array thì
  không tốn chi phí copy. Cơ chế bên trong ở [Chương 19](19-ben-trong-engine.md).
- *Object thì sao?* Biến object trong PHP chứa một *handle* (mã định danh trỏ tới object), nên truyền
  object vào hàm là copy cái handle. Hàm gọi method hay sửa property của object thì bên ngoài thấy
  thay đổi. Chi tiết ở [Chương 09](09-oop-co-ban.md).

Muốn hàm sửa được biến của người gọi thì phải truyền *theo tham chiếu* bằng `&` (mục 8).

### 2.2 Thiếu và thừa đối số

```php
<?php
declare(strict_types=1);

function add(int $a, int $b): int
{
    return $a + $b;
}

echo add(1, 2, 3), "\n";           // in ra: 3  (đối số thừa bị bỏ qua, không lỗi)

try {
    echo add(1), "\n";             // thiếu đối số
} catch (ArgumentCountError $e) {
    echo $e->getMessage(), "\n";
    // in ra: Too few arguments to function add(), 1 passed in ... on line 12 and exactly 2 expected
}

try {
    echo strlen('abc', 'thừa'), "\n";
} catch (ArgumentCountError $e) {
    echo $e->getMessage(), "\n";   // in ra: strlen() expects exactly 1 argument, 2 given
}
```

- Thiếu đối số cho tham số không có giá trị mặc định: ném `ArgumentCountError` (từ PHP 7.1; trước
  đó chỉ là Warning). Đây là một `Error`, không phải `Exception`, xem cây phân loại ở
  [Chương 12](12-loi-exception.md).
- Thừa đối số: với hàm tự viết, PHP im lặng bỏ qua. Với hàm có sẵn, từ PHP 8.0 là
  `ArgumentCountError` (RFC *Consistent type errors for internal functions*; trước 8.0 là Warning và
  hàm trả `null`). Lý do hàm tự viết được dễ dãi: thân hàm vẫn đọc được cả đối số không có tên trong
  danh sách tham số bằng `func_get_args()`, nên PHP không coi đối số thừa là sai.
- `ArgumentCountError` là lớp con của `TypeError`, nên `catch (TypeError $e)` cũng bắt được nó.

`func_get_args()` trả về array mọi đối số đã truyền, `func_num_args()` trả về số lượng. Đây là cách cũ
để viết hàm nhận số đối số tuỳ ý; code mới dùng variadic `...$args` (mục 7) vì có tên, có kiểu và
nhìn chữ ký hàm là biết.

### 2.3 Đối số được tính trước khi hàm chạy

PHP tính từng đối số từ trái sang phải, rồi mới vào hàm:

```php
<?php
declare(strict_types=1);

function trace(string $label): int
{
    echo "tính {$label}\n";
    return strlen($label);
}

function three(int $a, int $b, int $c): void
{
    echo "trong hàm: {$a} {$b} {$c}\n";
}

three(trace('a'), trace('bb'), trace('ccc'));
// in ra:
// tính a
// tính bb
// tính ccc
// trong hàm: 1 2 3
```

Hệ quả: đối số đắt (gọi database, đọc file) luôn bị tính dù hàm có dùng tới nó hay không. Muốn trì hoãn
việc tính thì truyền một closure và để hàm tự gọi khi cần (mục 10). Laravel dùng đúng ý này:
`Cache::remember('key', 60, fn () => DB::table(...)->get())` chỉ chạy truy vấn khi cache không có.

## 3. Khai báo kiểu cho tham số và giá trị trả về

### 3.1 Vì sao khai báo kiểu

Không khai báo kiểu, hàm `discount($price, $percent)` nhận mọi thứ: chuỗi, array, `null`. Lỗi sai kiểu
chỉ lộ ra ở đâu đó sâu bên trong, hoặc tệ hơn là ra kết quả sai mà không báo gì. *Type declaration*
(khai báo kiểu) đặt một "cổng kiểm tra" ở đầu vào (tham số) và đầu ra (giá trị trả về) của hàm.
Sai kiểu thì PHP ném `TypeError` ngay tại cổng, với thông báo chỉ rõ tham số nào:

```php
<?php
declare(strict_types=1);

function discount(int $price, float $percent): float
{
    return $price * $percent / 100;
}

var_dump(discount(200_000, 10.0));   // in ra: float(20000)
var_dump(discount(200_000, 10));     // in ra: float(20000)  (int được nhận ở chỗ khai báo float)

try {
    discount('200000', 10.0);
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: discount(): Argument #1 ($price) must be of type int, string given, called in ... on line 13
}

function findName(int $id): string
{
    $names = [1 => 'An', 2 => 'Bình'];
    return $names[$id] ?? null;      // lỗi logic: có lúc trả null dù khai báo string
}

echo findName(1), "\n";              // in ra: An
try {
    findName(99);
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";     // in ra: findName(): Return value must be of type string, null returned
}
```

Lợi ích thứ hai: chữ ký hàm trở thành tài liệu luôn đúng. IDE và công cụ phân tích tĩnh như PHPStan
([Chương 21](21-chat-luong-code.md)) đọc kiểu để gợi ý và bắt lỗi trước khi chạy.

Nhắc lại từ [Chương 04](04-kieu-du-lieu.md): PHP kiểm kiểu lúc chạy, đúng lúc giá trị đi qua cổng.
Dòng code nào chưa từng chạy thì lỗi kiểu ở đó chưa bị phát hiện.

⚠️ Kiểu của tham số chỉ được kiểm lúc vào hàm. Bên trong thân hàm, tham số là biến bình thường, gán
giá trị kiểu khác vẫn được:

```php
function f(int $x): void
{
    $x = 'không còn là int';   // không lỗi
    var_dump($x);              // in ra: string(19) "không còn là int"
}
```

Đừng làm vậy: người đọc tin vào chữ ký `int $x`. Cần biến mới thì đặt tên mới.

### 3.2 Những kiểu dùng được trong chữ ký hàm

[Chương 04](04-kieu-du-lieu.md) giải thích từng kiểu. Bảng dưới chỉ tóm tắt cái nào đặt được ở đâu:

| Kiểu | Tham số | Trả về | Ghi chú |
|---|---|---|---|
| `int`, `float`, `string`, `bool` | có | có | Kiểu scalar; chịu ảnh hưởng của `strict_types` (mục 4) |
| `array`, `iterable`, `object`, `callable` | có | có | `callable` không dùng được cho property của class |
| Tên class, interface | có | có | Ví dụ `DateTimeInterface $at` |
| `mixed` (8.0) | có | có | Mọi giá trị, kể cả `null` |
| `?T` (7.1) | có | có | Viết ngắn của `T\|null` |
| `A\|B` union (8.0) | có | có | Giá trị thuộc một trong các kiểu |
| `A&B` intersection (8.1), DNF `(A&B)\|null` (8.2) | có | có | Chỉ dùng với class/interface |
| `null`, `false`, `true` | có | có | `false` trong union từ 8.0; đứng riêng và `true` từ 8.2 |
| `self`, `parent` | có | có | Chỉ dùng trong class |
| `static` (8.0) | không | có | Chỉ dùng làm kiểu trả về của method |
| `void` (7.1) | không | có | Đứng riêng, không ghép union |
| `never` (8.1) | không | có | Đứng riêng, không ghép union |

Ví dụ với vài kiểu hay gặp trong code hằng ngày:

```php
<?php
declare(strict_types=1);

// ?string: trả về chuỗi, hoặc null khi không tìm thấy
function findUserName(int $id): ?string
{
    $names = [1 => 'An', 2 => 'Bình'];
    return $names[$id] ?? null;
}

var_dump(findUserName(2));    // in ra: string(5) "Bình"
var_dump(findUserName(99));   // in ra: NULL

// int|string: nhận một trong hai kiểu, hàm tự phân nhánh
function formatId(int|string $id): string
{
    return is_int($id) ? sprintf('#%06d', $id) : strtoupper($id);
}

echo formatId(42), ' ', formatId('ab-1'), "\n";   // in ra: #000042 AB-1

// string|false: dạng "...|false" gặp ở nhiều hàm có sẵn (strpos trả int|false, file_get_contents trả string|false)
function firstWord(string $s): string|false
{
    $pos = strpos($s, ' ');
    return $pos === false ? false : substr($s, 0, $pos);
}

var_dump(firstWord('xin chào'));   // in ra: string(3) "xin"
var_dump(firstWord('một'));        // in ra: bool(false)
```

Cách viết `...|false` có trong bảng vì bạn sẽ gặp nó khắp manual. Với hàm tự viết, `?string` (trả
`null` khi không có) hoặc ném exception thường rõ ràng hơn trả `false`.

### 3.3 `void`: hàm không trả giá trị

`void` (7.1) nghĩa là "hàm này chạy xong thì quay về, nhưng không trả giá trị gì có ý nghĩa". Dùng cho
hàm làm việc *bên lề* (*side effect*): ghi log, in ra màn hình, gửi email.

```php
<?php
declare(strict_types=1);

function logLine(string $msg): void
{
    if ($msg === '') {
        return;              // được: return không kèm giá trị
    }
    echo "[log] {$msg}\n";
}

var_dump(logLine('x'));      // in ra: [log] x  rồi  NULL
```

- Trong hàm `void`, `return;` được phép, còn `return null;` hay `return 1;` là lỗi biên dịch:
  `Fatal error: A void function must not return a value (did you mean "return;" instead of "return
  null;"?)`.
- Người gọi vẫn nhận được giá trị: luôn là `null`. Manual ghi rõ điều này. `void` là lời hứa của người
  viết hàm, không phải "hàm không có giá trị" theo nghĩa đen.
- `void` không ghép với kiểu khác: `?void` hay `void|int` là lỗi biên dịch.

### 3.4 `never`: hàm không bao giờ quay về

`never` (8.1) mạnh hơn `void`: hàm không bao giờ kết thúc bình thường. Nó chỉ có thể ném exception,
gọi `exit()`, hoặc chạy vòng lặp vô hạn. Dùng cho hàm kiểu "báo lỗi rồi dừng": hàm ném exception đã
định dạng sẵn, hàm redirect rồi `exit`. Helper `abort(404)` của Laravel thuộc loại này (Laravel ghi
`@return never` trong PHPDoc thay vì khai báo kiểu thật).

```php
<?php
declare(strict_types=1);

function fail(string $message): never
{
    throw new RuntimeException($message);
}

function parsePositive(string $s): int
{
    $n = (int) $s;
    if ($n <= 0) {
        fail("Không phải số dương: {$s}");
        // Công cụ phân tích tĩnh biết dòng này không bao giờ tới,
        // nên không đòi phải có return ở nhánh này
    }
    return $n;
}

echo parsePositive('5'), "\n";        // in ra: 5
try {
    parsePositive('-3');
} catch (RuntimeException $e) {
    echo $e->getMessage(), "\n";      // in ra: Không phải số dương: -3
}

function badNever(bool $flag): never
{
    if ($flag) {
        throw new LogicException('x');
    }
    // quên throw ở nhánh này
}

try {
    badNever(false);
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";      // in ra: badNever(): never-returning function must not implicitly return
}
```

- Viết `return;` trong hàm `never` là lỗi biên dịch (`A never-returning function must not return`).
- Chạy tới cuối hàm mà không ném exception hay `exit` thì PHP ném `TypeError` lúc chạy, như ví dụ trên.
- `never` không đứng trong union. Theo lý thuyết kiểu, `never` là *bottom type* (kiểu con của mọi
  kiểu), nên class con được phép thu hẹp kiểu trả về của method cha thành `never`.

So sánh nhanh:

| | Hàm trả về bình thường? | Người gọi nhận | Ví dụ |
|---|---|---|---|
| `: int`, `: string`... | có | giá trị đúng kiểu | `strlen()` |
| `: void` | có | luôn `null` | ghi log |
| `: never` | không bao giờ | không có gì để nhận | `abort()`, `fail()` |

### 3.5 `static`: trả về đúng class được gọi

`static` (8.0) chỉ dùng làm kiểu trả về của *method* (hàm nằm trong class, [Chương 09](09-oop-co-ban.md)).
Nó nghĩa là "trả về object thuộc chính class mà method được gọi trên đó lúc chạy", kể cả khi
method được viết ở class cha. Đây là nền của *fluent interface* (gọi nối `->where()->active()`) trong
query builder:

```php
<?php
declare(strict_types=1);

class Query
{
    protected array $wheres = [];

    public function where(string $condition): static
    {
        $this->wheres[] = $condition;
        return $this;
    }

    public function fresh(): static
    {
        return new Query();      // sai: luôn tạo Query, kể cả khi được gọi trên class con
    }
}

class UserQuery extends Query
{
    public function active(): static
    {
        return $this->where('active = 1');
    }
}

$q = (new UserQuery())->where('age > 18')->active();
echo get_class($q), "\n";                        // in ra: UserQuery

try {
    (new UserQuery())->fresh();
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: Query::fresh(): Return value must be of type UserQuery, Query returned
}
```

So với `self`: `self` là class chứa dòng code (`Query`), nên trả về một `UserQuery` vẫn hợp lệ
(class con thoả kiểu cha), nhưng IDE và PHPStan chỉ biết kết quả là `Query` và sẽ báo `->active()`
không tồn tại. `static` vừa cho công cụ biết kiểu chính xác, vừa được PHP kiểm lúc chạy như ví dụ
`fresh()` cho thấy (sửa đúng là `return new static();`). Cơ chế "class được gọi lúc chạy" này là *late
static binding*, học kỹ ở [Chương 10](10-oop-nang-cao.md).

### 3.6 Nullable: viết `?T`, đừng dựa vào `= null`

Hai cách cho tham số nhận `null`:

```php
function greet(?string $name = null): string { /* ... */ }   // đúng: kiểu ghi rõ là nullable
function greet(string $name = null): string { /* ... */ }    // cách cũ: "nullable ngầm"
```

Cách thứ hai gọi là *implicitly nullable*: kiểu ghi `string` nhưng vì mặc định là `null` nên PHP ngầm
cho nhận `null`. Từ PHP 8.4 nó báo:

```
Deprecated: greet(): Implicitly marking parameter $name as nullable is deprecated, the explicit
nullable type must be used instead in ... on line 4
```

Lý do bỏ (theo RFC *Deprecate implicitly nullable parameter types*): chữ ký `string $name` nói sai về kiểu
thật sự được nhận, cú pháp này trộn hai ý "có giá trị mặc định" và "nhận null", và gây lỗi khó hiểu khi class
con chỉ đổi giá trị mặc định. Sửa bằng `?string $name = null` hoặc `string|null $name = null`. Cách viết
`?string` chạy từ PHP 7.1 nên sửa hàng loạt an toàn (công cụ Rector làm tự động được,
[Chương 21](21-chat-luong-code.md)).

⚠️ `?string $name` không có `= null` thì vẫn là tham số bắt buộc: người gọi phải truyền, dù
truyền `null`. Nullable và optional là hai chuyện khác nhau.

## 4. `strict_types` và lời gọi hàm

[Chương 04](04-kieu-du-lieu.md) đã giới thiệu hai chế độ kiểm kiểu: *coercive mode* (mặc định, PHP thử
ép giá trị scalar sang kiểu khai báo) và *strict mode* (bật bằng `declare(strict_types=1);` ở câu lệnh
đầu tiên của file, chỉ nhận đúng kiểu). Mục này trả lời câu hỏi mà người mới hay hiểu sai: khi lời gọi
và hàm nằm ở hai file khác nhau, file nào quyết định?

### 4.1 Đối số theo file gọi, `return` theo file khai báo

Thử với hai thư viện, một không strict, một strict:

```php
<?php
// lib_loose.php: KHÔNG có declare(strict_types=1)
function twice(int $x): int
{
    return $x * 2;
}

function parseQty(string $s): int
{
    return $s;          // trả string ở chỗ khai báo int
}
```

```php
<?php
declare(strict_types=1);
// lib_strict.php

function triple(int $x): int
{
    return $x * 3;
}

function parseQtyStrict(string $s): int
{
    return $s;          // trả string ở chỗ khai báo int
}
```

File gọi có strict, dùng thư viện không strict:

```php
<?php
declare(strict_types=1);
// app_strict.php
require __DIR__ . '/lib_loose.php';

var_dump(twice(5));          // in ra: int(10)
try {
    var_dump(twice('5'));    // lời gọi nằm trong file strict nên không ép
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: twice(): Argument #1 ($x) must be of type int, string given, called in .../app_strict.php on line 8
}
var_dump(parseQty('7'));     // in ra: int(7)  (return kiểm theo lib_loose.php, không strict, nên ép được)

try {
    var_dump(strlen(123));   // hàm có sẵn cũng bị kiểm chặt khi gọi từ file strict
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";   // in ra: strlen(): Argument #1 ($string) must be of type string, int given
}
```

File gọi không strict, dùng thư viện strict:

```php
<?php
// app_loose.php: KHÔNG có declare(strict_types=1)
require __DIR__ . '/lib_strict.php';

var_dump(triple('5'));       // in ra: int(15)  (file gọi không strict nên '5' được ép thành 5)
try {
    var_dump(parseQtyStrict('7'));
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: parseQtyStrict(): Return value must be of type int, string returned
}
```

Quy tắc rút ra (manual: "Strict typing applies to function calls made from within the file with strict
typing enabled, not to the functions declared within that file"):

| Điểm kiểm tra | Chế độ lấy theo |
|---|---|
| Đối số truyền vào hàm | File chứa **lời gọi** |
| Giá trị `return` | File chứa **khai báo hàm** |
| Callback mà hàm có sẵn gọi (`array_map`, `usort`...) | Luôn coercive (mục 4.2) |

Vì sao thiết kế như vậy: strict là cam kết của người viết code. Người viết lời gọi cam kết "tôi truyền
đúng kiểu"; người viết hàm cam kết "tôi trả đúng kiểu". Thư viện bật strict không ép được người dùng thư
viện phải strict, và ngược lại.

Hệ quả thực tế: chỉ bật `strict_types` ở thư viện thì không bảo vệ được thư viện khỏi đối số sai kiểu
từ code người dùng. Muốn được bảo vệ, chính file gọi phải bật. Đó là lý do quy ước của giáo trình này (và
của nhiều dự án) là mọi file đều mở đầu bằng `declare(strict_types=1);`.

### 4.2 Callback do hàm có sẵn gọi thì không strict

Manual có một cảnh báo riêng: "Function calls from within internal functions will not be affected by the
strict_types declaration." Khi bạn đưa callback cho `array_map`, chính code C của `array_map` gọi
callback, không phải file của bạn, nên lời gọi đó luôn ở coercive mode:

```php
<?php
declare(strict_types=1);

$doubled = array_map(fn(int $x): int => $x * 2, ['1', '2']);
var_dump($doubled);   // in ra (viết gọn): array(2) { [0]=> int(2) [1]=> int(4) }
                      // không TypeError dù file đang strict
```

⚠️ Đừng dựa vào `strict_types` để kiểm dữ liệu đi qua `array_map`, `array_filter`, `usort`... Dữ liệu từ
bên ngoài (request, CSV, database) nên được kiểm và chuyển kiểu rõ ràng trước, ví dụ bằng validation.

### 4.3 Coercive mode ép những gì

Với hàm `function triple(int $x): int`, giá trị `$x` nhận được tuỳ theo chế độ của file chứa lời gọi:

| Đối số | Coercive mode | Strict mode |
|---|---|---|
| `5` | `5` | `5` |
| `'5'` | `5` | `TypeError` |
| `5.0` | `5` | `TypeError` |
| `5.5` | `5` kèm `Deprecated: Implicit conversion from float 5.5 to int loses precision` (từ 8.1) | `TypeError` |
| `null` | `TypeError` | `TypeError` |

Riêng `int` truyền vào chỗ khai báo `float` thì cả hai chế độ đều nhận: đây là ngoại lệ duy nhất manual nêu
cho strict mode, giá trị được đổi thành `float`. Lưu ý số nguyên lớn hơn 2^53 có thể mất độ chính xác khi
thành `float`.

⚠️ Dòng `null` ở trên áp cho hàm tự viết. Hàm có sẵn thì vì lý do lịch sử, ở coercive mode tham số
scalar của chúng từng nhận `null` và ép thành `''`, `0`... Từ PHP 8.1 việc này báo Deprecated, ở strict
mode là `TypeError`:

```php
<?php
// file KHÔNG strict
var_dump(strlen(null));
// in ra: Deprecated: strlen(): Passing null to parameter #1 ($string) of type string is deprecated in ...
//        int(0)
```

Đây là một trong những deprecation hay gặp nhất khi nâng ứng dụng cũ lên PHP 8.x: giá trị `null` từ cột database cho
phép NULL hay từ tham số request vắng mặt, rồi đi thẳng vào `trim()`, `strlen()`, `str_replace()`.

## 5. Tham số có giá trị mặc định

### 5.1 Cú pháp và cách hoạt động

Tham số có *giá trị mặc định* (*default value*) là tham số không bắt buộc (*optional*): người gọi không
truyền thì PHP dùng giá trị mặc định.

```php
<?php
declare(strict_types=1);

function makeCoffee(string $type = 'cappuccino', int $cups = 1): string
{
    return "{$cups} ly {$type}";
}

echo makeCoffee(), "\n";              // in ra: 1 ly cappuccino
echo makeCoffee('espresso'), "\n";    // in ra: 1 ly espresso
echo makeCoffee('latte', 2), "\n";    // in ra: 2 ly latte

function greet(?string $name = 'bạn'): string
{
    return 'Chào ' . ($name ?? '(null)');
}

echo greet(), "\n";                   // in ra: Chào bạn
echo greet(null), "\n";               // in ra: Chào (null)
```

⚠️ Dòng cuối là điểm hay hiểu nhầm: giá trị mặc định chỉ dùng khi **không truyền** đối số. Truyền `null`
là có truyền, nên `$name` nhận `null` chứ không nhận `'bạn'`. Manual: "passing null does not assign the
default value". Muốn "null thì dùng mặc định" phải tự viết `$name ??= 'bạn';` trong thân hàm.

### 5.2 Giá trị mặc định được phép là gì

Giá trị mặc định phải là *constant expression* (biểu thức hằng): giá trị PHP tính được mà không cần chạy
code tuỳ ý.

| Được | Không được |
|---|---|
| Literal: `1`, `'abc'`, `true`, `null`, `[]`, `['sort' => 'asc']` | Biến: `$x` |
| Hằng: `PHP_INT_MAX`, `DEFAULT_PAGE_SIZE`, `Config::LIMIT` | Lời gọi hàm: `time()`, `config('x')` |
| Phép tính trên hằng: `60 * 60`, `'a' . 'b'` | |
| `new ClassName(...)` (từ 8.1) | |
| Closure `static function` và first-class callable như `strtoupper(...)` (từ 8.5) | Arrow function `fn` (vì `fn` tự bắt biến) |

Vi phạm thì lỗi ngay lúc biên dịch:

```php
<?php
declare(strict_types=1);

function stamp(int $t = time()): int   // Fatal error: Constant expression contains invalid operations
{
    return $t;
}
```

Cách quen thuộc để có "mặc định là thời điểm hiện tại" là dùng `null` rồi gán trong thân hàm, hoặc từ
PHP 8.1 dùng `new` thẳng trong giá trị mặc định:

```php
function logAt(string $msg, ?int $at = null): string
{
    $at ??= time();                  // cách cổ điển, chạy mọi bản PHP 7.4+
    return date('H:i:s', $at) . " {$msg}";
}

function logAt2(string $msg, DateTimeImmutable $at = new DateTimeImmutable()): string   // PHP 8.1+
{
    return $at->format('H:i:s') . " {$msg}";
}
```

### 5.3 Giá trị mặc định được tính lại ở mỗi lời gọi

RFC *New in initializers* (8.1) ghi rõ: giá trị mặc định của tham số "are evaluated from left to right on
every call to the function where the parameter is not explicitly passed". Mỗi lời gọi không truyền đối
số thì có một object mới:

```php
<?php
declare(strict_types=1);

function freshList(string $item, ArrayObject $list = new ArrayObject()): int
{
    $list[] = $item;
    return count($list);
}

echo freshList('a'), freshList('b'), freshList('c'), "\n";   // in ra: 111
```

Đối chiếu: Python tính giá trị mặc định một lần lúc định nghĩa hàm, nên `def f(items=[])` dùng chung
một list cho mọi lời gọi, một bẫy kinh điển. PHP không có bẫy này. Thêm nữa, array trong PHP là kiểu giá
trị, nên `array $items = []` luôn là array rỗng mới.

### 5.4 PHP 8.5: closure làm giá trị mặc định

Từ PHP 8.5 (RFC *Closures in constant expressions* và *First class callables in constant
expressions*), closure được phép xuất hiện trong constant expression, nên dùng được làm giá trị mặc
định. Ràng buộc: closure phải là `static`, không có `use`, và không dùng được arrow function. Closure và
callable được giải thích ở mục 10 đến 12; ví dụ ở đây chỉ để biết cú pháp này tồn tại:

```php
<?php
declare(strict_types=1);

// Chạy trên PHP 8.5. PHP 8.4 trở về trước: Fatal error: Constant expression contains invalid operations
function keepIf(
    array $items,
    Closure $keep = static function (mixed $v): bool {
        return $v !== null && $v !== '';
    },
): array {
    return array_values(array_filter($items, $keep));
}

function transform(string $s, Closure $fn = strtoupper(...)): string
{
    return $fn($s);
}

var_dump(keepIf(['a', '', null, 'b']));   // in ra: array(2) { [0]=> string(1) "a" [1]=> string(1) "b" } (viết gọn)
echo transform('abc'), "\n";              // in ra: ABC
```

Trước 8.5, cách viết tương đương là `?Closure $keep = null` rồi `$keep ??= static fn (mixed $v): bool
=> ...;` trong thân hàm.

### 5.5 Tham số tuỳ chọn phải đứng sau tham số bắt buộc

```php
<?php
declare(strict_types=1);

function makeYogurt(string $container = 'bowl', string $flavour): string
{
    return "{$container} {$flavour}";
}
// Deprecated: makeYogurt(): Optional parameter $container declared before required parameter
// $flavour is implicitly treated as a required parameter in ... on line 4
```

Tham số `$container` có mặc định nhưng đứng trước một tham số bắt buộc, nên với lời gọi kiểu vị trí
người gọi không bao giờ bỏ được nó: mặc định vô dụng. Từ PHP 8.0, PHP báo Deprecated; về thực chất
`$container` là tham số bắt buộc: gọi `makeYogurt('dâu')` ném `ArgumentCountError: Too few arguments to function
makeYogurt(), 1 passed ... and exactly 2 expected`. (Nội dung Deprecated khác nhau theo bản: 8.0 ghi
`Required parameter $flavour follows optional parameter $container`; 8.1 tới 8.3 giống trên nhưng không
có tiền tố `makeYogurt():`.) Sửa: đưa tham số tuỳ chọn ra sau, hoặc bỏ giá trị mặc định.

## 6. Named arguments

### 6.1 Vấn đề: hàng đối số không ai hiểu

Đọc dòng này và đoán `false, false` nghĩa là gì:

```php
createUser('an@x.vn', '', false, false);
```

Không mở định nghĩa hàm thì không đoán được. *Named arguments* (đối số đặt tên, PHP 8.0) cho phép
truyền đối số theo tên tham số thay vì theo vị trí: viết `tên: giá trị`.

```php
<?php
declare(strict_types=1);

function createUser(
    string $email,
    string $name = '',
    bool $isAdmin = false,
    bool $sendWelcomeEmail = true,
): string {
    return sprintf('%s|%s|admin=%s|mail=%s', $email, $name,
        var_export($isAdmin, true), var_export($sendWelcomeEmail, true));
}

// Vị trí: phải điền cả $name, $isAdmin chỉ để tới được $sendWelcomeEmail
echo createUser('an@x.vn', '', false, false), "\n";
// in ra: an@x.vn||admin=false|mail=false

// Named: tự giải thích, và bỏ qua được các tham số tuỳ chọn ở giữa
echo createUser('an@x.vn', sendWelcomeEmail: false), "\n";
// in ra: an@x.vn||admin=false|mail=false

// Thứ tự các named argument không quan trọng
echo createUser(sendWelcomeEmail: false, email: 'binh@x.vn', isAdmin: true), "\n";
// in ra: binh@x.vn||admin=true|mail=false
```

Ba lợi ích: đọc tự hiểu, không phụ thuộc thứ tự, và bỏ qua tuỳ ý những tham số tuỳ chọn muốn giữ mặc định.

Named arguments dùng được với hàm có sẵn. Tên tham số chính là tên ghi trong manual:

```php
echo str_pad('7', 3, '0', STR_PAD_LEFT), "\n";                                // in ra: 007
echo str_pad(string: '7', length: 3, pad_string: '0', pad_type: STR_PAD_LEFT), "\n";   // in ra: 007

// Chỉ muốn đổi tham số thứ 4, giữ mặc định của tham số 2 và 3:
echo htmlspecialchars('&amp; <b>', double_encode: false), "\n";              // in ra: &amp; &lt;b&gt;
```

### 6.2 Luật và lỗi

```php
// (createUser như trên; mỗi dòng dưới là một lỗi riêng, thử từng dòng một)

createUser(emial: 'x@y.z');
// Error: Unknown named parameter $emial            (gõ sai tên: lỗi lúc chạy)

createUser('a@b.c', email: 'x@y.z');
// Error: Named parameter $email overwrites previous argument   ($email đã nhận đối số vị trí)

createUser(name: 'An');
// ArgumentCountError: createUser(): Argument #1 ($email) not passed   (bỏ sót tham số bắt buộc)

createUser(email: 'a@b.c', 'An');
// Fatal error: Cannot use positional argument after named argument     (lỗi biên dịch)
```

- Đối số vị trí đứng trước, named đứng sau. Ngược lại là lỗi biên dịch.
- Tên phải viết thẳng trong code; không đặt tên động kiểu `f($tenThamSo: 1)` được. Muốn tên động thì dùng
  unpacking array có key là chuỗi (mục 7.3).
- Với hàm có sẵn, có vài tham số "không có giá trị mặc định biết trước" nên không được bỏ qua:

```php
array_keys(['a' => 1], strict: true);
// ArgumentCountError: array_keys(): Argument #2 ($filter_value) must be passed explicitly,
// because the default value is not known
```

### 6.3 Tên tham số trở thành một phần của API

Trước PHP 8.0, đổi tên tham số là chuyện nội bộ của hàm. Có named arguments thì người gọi có thể đang
viết `createUser(isAdmin: true)`; đổi `$isAdmin` thành `$admin` sẽ làm code của họ hỏng với `Unknown named
parameter`. Với thư viện dùng chung, đổi tên tham số là một *breaking change*.

⚠️ Với class kế thừa và interface, PHP không kiểm tên tham số khi class con đổi tên. Lỗi chỉ lộ lúc
gọi bằng tên:

```php
<?php
declare(strict_types=1);

interface Notifier
{
    public function send(string $to, string $message): void;
}

final class SmsNotifier implements Notifier
{
    public function send(string $phone, string $message): void   // đổi $to thành $phone: PHP không báo gì
    {
        echo "SMS tới {$phone}: {$message}\n";
    }
}

$n = new SmsNotifier();
$n->send('0909', 'xin chào');                  // in ra: SMS tới 0909: xin chào
$n->send(to: '0909', message: 'xin chào');     // Error: Unknown named parameter $to
```

RFC named arguments chọn cách này (giống Python, Ruby) để không phá hàng loạt code cũ, và khuyến nghị
để công cụ phân tích tĩnh phát hiện. Quy tắc an toàn: class con giữ đúng tên tham số của class cha và
interface.

Khi nào nên dùng named arguments:

- Đối số kiểu `bool` hoặc con số "ma thuật" mà nhìn vào không hiểu: `send(retry: false)`.
- Muốn bỏ qua nhiều tham số tuỳ chọn để đặt một tham số ở cuối.
- Hàm nhiều tham số cùng kiểu dễ đảo nhầm thứ tự, ví dụ `transfer(from: $a, to: $b, amount: 100)`.

Không cần dùng khi hàm có một hai tham số và nghĩa đã rõ: `strlen($s)` không cần thành `strlen(string: $s)`.

## 7. Variadic `...$args` và unpacking đối số

### 7.1 Hàm nhận số đối số tuỳ ý

Có những hàm tự nhiên nhận "bao nhiêu cũng được": cộng nhiều số, gắn nhiều tag, ghi log nhiều giá trị.
*Variadic parameter* (tham số variadic) viết `...$ten` ở cuối danh sách tham số, gom mọi đối số còn
lại thành một array:

```php
<?php
declare(strict_types=1);

function sum(int ...$numbers): int
{
    // $numbers là array: [] khi không truyền gì, [1, 2, 3] khi gọi sum(1, 2, 3)
    return array_sum($numbers);
}

echo sum(), "\n";            // in ra: 0
echo sum(1, 2, 3), "\n";     // in ra: 6

function tagLine(string $title, string ...$tags): string
{
    return $title . ' [' . implode(', ', $tags) . ']';
}

echo tagLine('Bài 8'), "\n";                  // in ra: Bài 8 []
echo tagLine('Bài 8', 'php', 'hàm'), "\n";    // in ra: Bài 8 [php, hàm]

try {
    sum(1, 2, '3');
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: sum(): Argument #3 must be of type int, string given, called in ... on line 22
}
```

- Tham số thường đứng trước nhận đối số trước; variadic gom phần còn lại.
- Kiểu khai báo (`int ...$numbers`) áp cho từng phần tử. Đây là cách duy nhất có sẵn trong ngôn ngữ để
  PHP tự kiểm "mọi phần tử đều là int", vì PHP không có kiểu dạng `array<int>` (PHPDoc `@param int[]` chỉ
  dành cho công cụ phân tích tĩnh, PHP không kiểm lúc chạy).
- Chỉ tham số cuối được là variadic (`Fatal error: Only the last parameter can be variadic`), và nó
  không có giá trị mặc định được (`Variadic parameter cannot have a default value`): không truyền gì thì
  nó là array rỗng.
- Variadic theo tham chiếu được: `int &...$counters` (mục 8).
- Named argument không khớp tham số nào sẽ được variadic gom vào với key là chuỗi:
  `tagLine('Bài 8', 'php', level: 'senior')` cho `$tags` là `[0 => 'php', 'level' => 'senior']`.

Đối chiếu: Java viết `int... nums`, Go viết `nums ...int`. Cùng ý: phần đuôi danh sách đối số thành một
mảng/slice.

### 7.2 Unpacking: trải array thành các đối số

Chiều ngược lại: có sẵn một array, muốn truyền từng phần tử như từng đối số. Đặt `...` trước array
ở chỗ gọi (*argument unpacking*, hay gọi là *spread*):

```php
<?php
declare(strict_types=1);

function sum(int ...$numbers): int
{
    return array_sum($numbers);
}

$nums = [4, 5, 6];
echo sum(...$nums), "\n";             // in ra: 15   (như sum(4, 5, 6))
echo sum(1, ...$nums), "\n";          // in ra: 16
echo sum(...[1, 2], ...[3]), "\n";    // in ra: 6    (trải nhiều lần được)

function gen(): Generator
{
    yield 10;
    yield 20;
}
echo sum(...gen()), "\n";             // in ra: 30   (trải được cả Traversable, ví dụ generator)
```

Unpacking không bắt buộc hàm nhận phải là variadic; `add(...[1, 2])` gọi được `function add(int $a, int
$b)`. Sau phần trải không được viết thêm đối số vị trí: `sum(...$nums, 3)` là lỗi biên dịch `Cannot use
positional argument after argument unpacking`. Named argument sau phần trải thì được (từ 8.1).

Generator là chủ đề của [Chương 13](13-generator-iterator-spl.md); ở đây chỉ cần biết nó là một thứ
"duyệt được" như array.

### 7.3 Key chuỗi khi unpacking là named argument

Từ PHP 8.0, phần tử có key chuỗi khi trải được hiểu là named argument; key số nguyên là đối số vị trí
(giá trị của key số bị bỏ qua):

```php
$args = ['email' => 'c@x.vn', 'isAdmin' => true];
echo createUser(...$args), "\n";   // như createUser(email: 'c@x.vn', isAdmin: true)
// in ra: c@x.vn||admin=true|mail=true
```

Đây cũng là cách "đặt tên đối số động" mà mục 6.2 nói tới. Nhưng nó sinh ra một cái bẫy hay gặp:

```php
<?php
declare(strict_types=1);

$groups = [
    'admins' => ['an', 'binh'],
    'guests' => ['chi'],
];

try {
    $all = array_merge(...$groups);
} catch (ArgumentCountError $e) {
    echo $e->getMessage(), "\n";
    // in ra: array_merge() does not accept unknown named parameters
    // Key 'admins', 'guests' bị hiểu là tên tham số!
}

$all = array_merge(...array_values($groups));   // bỏ key trước khi trải
echo implode(',', $all), "\n";                    // in ra: an,binh,chi
```

Trước PHP 8.0, trải một array có key chuỗi vào lời gọi hàm vốn đã là lỗi, nên cách viết trên chưa bao giờ
chạy được. Cái thật sự vỡ khi nâng từ PHP 7 lên 8 là cách viết cũ `call_user_func_array('array_merge',
$groups)`: PHP 7 lặng lẽ bỏ qua key, còn PHP 8 hiểu key chuỗi là tên tham số và ném đúng lỗi
`ArgumentCountError` như trên (RFC named arguments ghi đây là thay đổi phá tương thích duy nhất của nó).
Khi dữ liệu đem trải có thể có key chuỗi, bọc bằng `array_values()`.

## 8. Truyền tham chiếu `&`

### 8.1 Tham chiếu là gì

Một *tham chiếu* (*reference*) trong PHP là **một cái tên nữa cho cùng một biến**. Sau `$b = &$a;`, `$a`
và `$b` cùng trỏ vào một nội dung; gán qua tên nào thì tên kia cũng thấy. Nó không phải con trỏ như trong
C hay Go: không có địa chỉ để in ra hay so sánh, không có phép `*p` để lấy giá trị.

Đặt `&` trước tên tham số thì tham số đó trở thành tên thứ hai cho biến của người gọi:

```php
<?php
declare(strict_types=1);

function addSuffix(string &$s, string $suffix = '!'): void
{
    $s .= $suffix;      // sửa thẳng biến của người gọi
}

$msg = 'Xin chào';
addSuffix($msg);
echo $msg, "\n";        // in ra: Xin chào!
```

```
Truyền theo giá trị f($x)            Truyền tham chiếu f(&$x)

 $msg ──► "Xin chào"                  $msg ─┐
 $s   ──► "Xin chào" (bản riêng)            ├──► "Xin chào!"
                                      $s   ─┘   (cùng một nội dung)
```

### 8.2 Hàm có sẵn dùng tham chiếu

Bạn dùng tham chiếu hằng ngày qua các hàm có sẵn, kể cả khi không để ý:

```php
<?php
declare(strict_types=1);

$scores = [7, 3, 9];
$ok = sort($scores);              // sort SỬA array tại chỗ và trả về true
var_dump($ok);                    // in ra: bool(true)
echo implode(',', $scores), "\n"; // in ra: 3,7,9

if (preg_match('/(\d{4})-(\d{2})/', 'Kỳ 2026-10', $m) === 1) {   // $m nhận kết quả qua tham chiếu
    echo $m[1], ' ', $m[2], "\n"; // in ra: 2026 10
}

$text = str_replace('a', 'o', 'banana', $count);   // tham số thứ 4 nhận số lần thay
echo "{$text} {$count}\n";        // in ra: bonono 3
```

⚠️ Bẫy kinh điển: viết `$sorted = sort($scores);` rồi dùng `$sorted` như array. `sort()` trả `true`, còn
array đã sắp xếp nằm trong chính `$scores`. Manual ghi rõ hàm nào làm việc *trên biến được truyền vào*
(như `usort()`) và hàm nào *trả về giá trị mới* (như `str_replace()`); đọc kỹ chữ ký: tham số có `&` là
hàm sẽ sửa biến của bạn.

### 8.3 Luật khi truyền tham chiếu

```php
// Mỗi lời gọi dưới đây minh hoạ một trường hợp riêng
function addSuffix(string &$s): void { $s .= '!'; }
function name(): string { return 'An'; }

addSuffix('abc');
// Error: addSuffix(): Argument #1 ($s) could not be passed by reference   (literal không có biến để tham chiếu)

addSuffix(name());
// Notice: Only variables should be passed by reference   (hàm vẫn chạy, nhưng sửa một giá trị tạm rồi bỏ)

$last = end(explode('/', 'a/b/report.csv'));
// Notice: Only variables should be passed by reference   (end() nhận tham chiếu; tách thành 2 dòng)
```

- Chỉ biến (hoặc phần tử array, property) mới truyền tham chiếu được.
- ⚠️ Truyền tham chiếu một phần tử chưa tồn tại sẽ âm thầm tạo nó:

```php
$config = [];
function touch2(?string &$v): void {}
touch2($config['missing']);
var_dump($config);   // in ra: array(1) { ["missing"]=> NULL }  (viết gọn)
```

- Kiểu của tham số tham chiếu chỉ được kiểm lúc vào hàm. Hàm có thể gán kiểu khác vào, và biến của
  người gọi đổi kiểu theo (manual có ví dụ tương tự: một hàm dạng `function f(array &$a) { $a = 1; }` làm
  biến bên ngoài thành `int(1)`).
- Tham số tham chiếu được phép có giá trị mặc định.

### 8.4 Khi nào nên dùng, khi nào không

Ngày nay `&` hiếm khi là lựa chọn tốt trong code bạn tự viết:

1. Người đọc không thấy biến bị sửa. Ở chỗ gọi, `addSuffix($msg)` trông y như lời gọi bình thường;
   dấu `&` chỉ nằm trong định nghĩa. So với Go, nơi chỗ gọi phải viết rõ `addSuffix(&msg)`, PHP che mất
   thông tin quan trọng này.
2. Trả về giá trị mới rõ ràng hơn: `$msg = withSuffix($msg);` nói rõ cái gì đổi.
3. ⚠️ "Truyền tham chiếu cho nhanh" chỉ đúng trong một trường hợp hẹp. Nhờ copy-on-write (mục 2.1),
   hàm chỉ đọc array thì truyền theo giá trị không copy gì, thêm `&` không nhanh hơn chút nào. Chỉ khi
   hàm sửa một array lớn thì truyền theo giá trị mới tốn một lần copy cả array mỗi lần gọi. Gọi kiểu
   `$list = append($list, $x);` trong vòng lặp hàng nghìn lần thì tổng chi phí tăng theo bình phương số
   phần tử (đo minh hoạ với 20 000 lần thêm: bản theo giá trị khoảng 200 ms, bản `&` khoảng 2 ms; con số
   tuỳ máy). Cách sửa thường tốt hơn `&` là đổi thiết kế: để hàm nhận cả lô dữ liệu và tự lặp bên trong,
   hoặc gom dữ liệu vào một object. Cơ chế copy-on-write ở [Chương 19](19-ben-trong-engine.md).
4. Object không cần `&` để sửa: biến chứa handle, hàm sửa object thì người gọi thấy luôn
   ([Chương 09](09-oop-co-ban.md)).

Dùng `&` khi việc chính của hàm là sửa biến tại chỗ và điều đó là quy ước quen thuộc (giống `sort()`),
hoặc cần trả thêm "kết quả phụ" như `$count` của `str_replace()`. Khi đó đặt tên hàm cho thấy rõ việc sửa.

PHP còn có *return by reference* (`function &getRef()`, gọi bằng `$x = &getRef();`, cần `&` ở cả hai
chỗ) để trả về một tham chiếu. Tính năng này hiếm gặp; manual viết thẳng: "Do not use return-by-reference
to increase performance. The engine will automatically optimize this on its own."

## 9. Phạm vi biến

### 9.1 Mỗi hàm có phạm vi riêng

*Phạm vi* (*scope*) của biến là vùng code mà tên biến đó có nghĩa. PHP chỉ có hai loại: *phạm vi toàn
cục* (*global scope*, code nằm ngoài mọi hàm) và *phạm vi hàm* (*function scope*). Biến tạo trong hàm là
biến *cục bộ* (*local*): chỉ sống trong một lần chạy của hàm, và hàm không tự thấy biến bên ngoài.

```php
<?php
declare(strict_types=1);

$taxRate = 0.1;              // biến toàn cục

function priceWithTax(int $price): float
{
    return $price * (1 + $taxRate);   // $taxRate ở đây là biến CỤC BỘ, chưa từng được gán
}

echo priceWithTax(100), "\n";
// in ra: Warning: Undefined variable $taxRate in ... on line 8
//        100     (biến chưa gán coi như null, nên 1 + null = 1)
```

Đây là điểm khác lớn so với JavaScript hay Python, nơi hàm đọc được biến của phạm vi bao ngoài. PHP cố ý
làm vậy: hàm chỉ phụ thuộc vào những gì đi qua tham số, nên đọc chữ ký là biết hàm cần gì. Cách sửa đúng
là truyền vào: `priceWithTax(int $price, float $taxRate)`.

⚠️ PHP **không có phạm vi khối** (*block scope*): biến tạo trong `if`, `for`, `foreach` vẫn sống tiếp sau
khối đó, tới hết hàm.

```php
<?php
declare(strict_types=1);

function demo(): void
{
    $inside = 'tạo trong hàm';
    if (true) {
        $fromIf = 'tạo trong if';
    }
    for ($i = 0; $i < 3; $i++) {
        $last = $i;
    }
    echo "{$fromIf} | i={$i} | last={$last}\n";   // in ra: tạo trong if | i=3 | last=2
}

demo();
var_dump(isset($inside));    // in ra: bool(false)  (biến cục bộ biến mất khi hàm kết thúc)
```

Java và Go đều có block scope: biến khai báo trong `if` hay `for` chết khi ra khỏi khối.

### 9.2 `global` và `$GLOBALS`

Hai cách để hàm chạm vào biến toàn cục:

```php
<?php
declare(strict_types=1);

$requestCount = 0;

function countWithGlobal(): void
{
    global $requestCount;      // tạo biến cục bộ là tham chiếu tới biến toàn cục cùng tên
    $requestCount++;
}

function countWithGlobalsArray(): void
{
    $GLOBALS['requestCount']++;   // $GLOBALS: array chứa mọi biến toàn cục, dùng được ở mọi nơi
}

countWithGlobal();
countWithGlobalsArray();
echo $requestCount, "\n";      // in ra: 2
```

- `global $x;` thực chất tạo một tham chiếu cục bộ tới biến toàn cục `$x`; nếu biến toàn cục chưa có
  thì nó được tạo với giá trị `null`.
- `$GLOBALS` là một *superglobal*: biến có sẵn ở mọi phạm vi, cùng nhóm với `$_GET`, `$_POST`, `$_SERVER`
  ([Chương 15](15-php-va-web.md)). Từ PHP 8.1, đọc/ghi từng phần tử `$GLOBALS['x']` và đọc cả array vẫn
  được, nhưng ghi vào cả array thì không: `$GLOBALS = [];` là lỗi biên dịch, `array_pop($GLOBALS)` là lỗi.

⚠️ Tránh biến toàn cục trong code ứng dụng:

- *Phụ thuộc ẩn*: chữ ký hàm không cho biết hàm đọc/sửa biến nào, nên khó đọc và khó test (test phải dựng
  lại trạng thái toàn cục).
- Trong tiến trình sống lâu (queue worker, Laravel Octane), trạng thái toàn cục không được dọn giữa các
  job/request, dữ liệu của request trước có thể rò sang request sau
  ([Chương 30](30-laravel-testing-octane-deploy.md)).

Cách thay thế: truyền qua tham số, hoặc gom vào object và dùng *dependency injection*
([Chương 26](26-laravel-container-provider-facade.md)). Hằng số (`const`, `define`) thì khác: chúng là toàn
cục, không đổi được, và dùng trong hàm thoải mái ([Chương 03](03-cu-phap-bien-hang.md)).

### 9.3 Biến `static`: nhớ giá trị giữa các lần gọi

Biến khai báo `static` trong hàm vẫn là biến cục bộ (chỉ hàm đó thấy), nhưng không mất khi hàm kết
thúc: lần gọi sau thấy giá trị lần trước để lại. Nó được khởi tạo một lần, ở lần đầu dòng khai báo
được chạy.

```php
<?php
declare(strict_types=1);

function nextNumber(): string
{
    $plain = 0;          // biến thường: tạo lại mỗi lần gọi
    static $seq = 0;     // biến static: khởi tạo một lần, giữ giá trị giữa các lần gọi
    $plain++;
    $seq++;
    return "plain={$plain} seq={$seq}";
}

echo nextNumber(), "\n";   // in ra: plain=1 seq=1
echo nextNumber(), "\n";   // in ra: plain=1 seq=2
echo nextNumber(), "\n";   // in ra: plain=1 seq=3
```

Ứng dụng phổ biến nhất là *memoization* (ghi nhớ kết quả) và khởi tạo lười (*lazy initialization*): làm
việc đắt một lần, các lần sau dùng lại.

```php
<?php
declare(strict_types=1);

function loadRates(): array
{
    echo "(đọc tỷ giá từ nguồn chậm)\n";
    return ['USD' => 25_000, 'EUR' => 27_000];
}

function rate(string $currency): int
{
    static $rates = loadRates();   // PHP 8.3+: giá trị khởi tạo được là biểu thức bất kỳ
    return $rates[$currency];
}

echo rate('USD'), "\n";   // in ra: (đọc tỷ giá từ nguồn chậm)  rồi  25000
echo rate('EUR'), "\n";   // in ra: 27000   (không đọc lại)
```

- Trước PHP 8.3, giá trị khởi tạo của biến `static` phải là constant expression; viết `static $rates =
  loadRates();` trên 8.2 báo `Fatal error: Constant expression contains invalid operations`. Cách viết
  chạy được mọi bản: `static $rates = null; $rates ??= loadRates();`.
- Từ 8.3 cũng không được khai báo `static` cùng một biến hai lần trong một hàm (`Fatal error: Duplicate
  declaration of static variable $x`).
- Biến `static` trong closure gắn với từng object closure: closure được tạo lại mỗi lần thì biến
  `static` cũng bắt đầu lại.
- Biến `static` trong method của class: từ PHP 8.1, class con kế thừa (không override) method đó sẽ dùng
  chung biến static với class cha (class và kế thừa ở [Chương 09](09-oop-co-ban.md)).

⚠️ Biến `static` là trạng thái toàn cục trá hình, nên mang cùng rủi ro với mục 9.2: sống suốt request ở
PHP-FPM, và sống suốt đời worker ở Octane hay queue worker. Cache tỷ giá như trên trong một worker chạy
nhiều ngày sẽ không bao giờ cập nhật; cache dữ liệu theo người dùng trong biến static có thể đưa dữ liệu
của người này cho người khác. Chỉ dùng cho dữ liệu thật sự bất biến trong suốt đời tiến trình.

## 10. Hàm ẩn danh (closure)

### 10.1 Hàm cũng là một giá trị

Tới giờ mọi hàm đều có tên và được khai báo một lần. *Hàm ẩn danh* (*anonymous function*), trong PHP
thường gọi là *closure*, là hàm không tên được viết ngay tại chỗ như một biểu thức. Kết quả của biểu
thức đó là một giá trị: gán vào biến được, truyền vào hàm khác được, trả về từ hàm được.

```php
<?php
declare(strict_types=1);

$greet = function (string $name): string {
    return "Chào {$name}";
};                                     // có dấu ; vì cả khối là một câu lệnh gán

echo $greet('An'), "\n";               // in ra: Chào An
var_dump($greet instanceof Closure);   // in ra: bool(true)
echo get_class($greet), "\n";          // in ra: Closure
```

Mỗi closure là một object của class có sẵn `Closure`. Gọi nó bằng cú pháp gọi hàm thường: `$greet('An')`.

Vì sao cần hàm không tên? Vì rất nhiều hàm có sẵn nhận *callback*: một đoạn logic bạn đưa vào để hàm kia
gọi lại. Logic đó thường ngắn, chỉ dùng một lần, đặt tên riêng cho nó là thừa:

```php
<?php
declare(strict_types=1);

$products = [
    ['name' => 'Bút', 'price' => 5_000, 'stock' => 10],
    ['name' => 'Vở', 'price' => 12_000, 'stock' => 0],
    ['name' => 'Thước', 'price' => 8_000, 'stock' => 3],
];

// array_filter gọi closure cho từng phần tử, giữ phần tử nào closure trả true
$inStock = array_filter($products, function (array $p): bool {
    return $p['stock'] > 0;
});

// usort gọi closure để so sánh từng cặp: âm, 0, dương (toán tử <=> ở Chương 07)
usort($inStock, function (array $a, array $b): int {
    return $a['price'] <=> $b['price'];
});

echo implode(', ', array_column($inStock, 'name')), "\n";   // in ra: Bút, Thước
```

Các chỗ bạn sẽ gặp closure trong Laravel: route `Route::get('/', function () {...})`, `Cache::remember(...,
fn () => ...)`, method của Collection như `$users->filter(fn ($u) => $u->active)`, transaction
`DB::transaction(function () {...})`, event listener.

### 10.2 `use`: mang biến bên ngoài vào closure

Closure tuân theo luật phạm vi ở mục 9: nó không tự thấy biến bên ngoài. Muốn dùng, liệt kê trong
`use (...)`:

```php
<?php
declare(strict_types=1);

$rate = 0.1;

$byValue = function (int $price) use ($rate): float {
    return $price * $rate;           // $rate được chụp lại lúc TẠO closure
};
$byRef = function (int $price) use (&$rate): float {
    return $price * $rate;           // $rate là tham chiếu tới chính biến bên ngoài
};

$rate = 0.2;                         // đổi SAU khi đã tạo closure

echo $byValue(100), "\n";            // in ra: 10   (vẫn dùng 0.1 đã chụp)
echo $byRef(100), "\n";              // in ra: 20   (thấy giá trị mới)

$noUse = function (): void {
    var_dump(isset($rate));          // in ra: bool(false)  (không có use thì không thấy)
};
$noUse();
```

- `use ($x)` (*theo giá trị*): chụp lại giá trị của `$x` **tại thời điểm tạo closure**. Đổi `$x` bên ngoài
  sau đó không ảnh hưởng closure, và closure sửa `$x` cũng không ảnh hưởng bên ngoài.
- `use (&$x)` (*theo tham chiếu*): closure và bên ngoài dùng chung một biến. Hai chiều đều thấy thay đổi.
- Kiểu trả về đặt sau `use`: `function (...) use (...): float { ... }`.
- Không được `use` superglobal (`$_GET`...), `$this`, hay biến trùng tên tham số; cả ba là lỗi biên dịch,
  ví dụ `Cannot use lexical variable $x as a parameter name`.

⚠️ Với `use` theo giá trị, mỗi lần gọi closure bắt đầu lại từ giá trị đã chụp, thay đổi bên trong không
được giữ lại giữa các lần gọi:

```php
<?php
declare(strict_types=1);

$count = 0;
$inc = function () use ($count): int {
    $count++;                       // sửa bản sao, mất khi lời gọi kết thúc
    return $count;
};
echo $inc(), $inc(), ' ', $count, "\n";      // in ra: 11 0

$count = 0;
$incRef = function () use (&$count): int {
    return ++$count;
};
echo $incRef(), $incRef(), ' ', $count, "\n";   // in ra: 12 2
```

⚠️ "Theo giá trị" là giá trị của biến. Nếu biến chứa object thì cái được chụp là handle của object,
closure gọi method hay sửa property thì bên ngoài vẫn thấy ([Chương 09](09-oop-co-ban.md)).

### 10.3 Closure giữ môi trường sau khi hàm ngoài kết thúc

Đây là lý do có cái tên *closure* ("bao đóng"): một hàm kèm theo những biến nó đã "đóng gói" từ nơi nó
được tạo. Hàm ngoài chạy xong, biến cục bộ của nó lẽ ra biến mất, nhưng những biến đã được closure `use`
thì sống tiếp cùng closure.

```php
<?php
declare(strict_types=1);

function makeDiscount(float $percent): Closure
{
    return function (int $price) use ($percent): int {
        return (int) round($price * (1 - $percent / 100));
    };
}

$tet = makeDiscount(20);          // makeDiscount đã chạy xong, nhưng $percent = 20 vẫn sống trong closure
$blackFriday = makeDiscount(50);
echo $tet(100_000), ' ', $blackFriday(100_000), "\n";   // in ra: 80000 50000

function makeCounter(): Closure
{
    $count = 0;
    return function () use (&$count): int {
        return ++$count;
    };
}

$c1 = makeCounter();
$c2 = makeCounter();                       // mỗi lần gọi makeCounter có một $count riêng
echo $c1(), $c1(), $c1(), ' ', $c2(), "\n";   // in ra: 123 1
```

Hàm trả về hàm, hay nhận hàm làm tham số, gọi là *higher-order function* (hàm bậc cao). `array_map`,
`array_filter`, `usort` là hàm bậc cao có sẵn; `makeDiscount` là hàm bậc cao tự viết.

### 10.4 Không có bẫy "closure trong vòng lặp"

```php
<?php
declare(strict_types=1);

$handlers = [];
for ($i = 0; $i < 3; $i++) {
    $handlers[] = function () use ($i): int {
        return $i;
    };
}
echo implode(',', array_map(fn(Closure $h): int => $h(), $handlers)), "\n";   // in ra: 0,1,2

$handlersRef = [];
for ($i = 0; $i < 3; $i++) {
    $handlersRef[] = function () use (&$i): int {
        return $i;
    };
}
echo implode(',', array_map(fn(Closure $h): int => $h(), $handlersRef)), "\n";   // in ra: 3,3,3
```

Đối chiếu: closure của JavaScript (với `var`) và của Go (trước Go 1.22) bắt biến, nên mọi closure tạo
trong vòng lặp cùng thấy một biến đếm và đều trả giá trị cuối. Lambda của Java chỉ được dùng biến
*effectively final* (không bao giờ bị gán lại). PHP mặc định chụp giá trị nên tự nhiên cho `0,1,2`; chỉ
khi bạn tự viết `use (&$i)` mới gặp hành vi `3,3,3`.

### 10.5 Closure trong class: `$this` và `static function`

Phần này cần biết class ([Chương 09](09-oop-co-ban.md)); đọc lướt nếu chưa học. Closure tạo bên trong
method của class tự động gắn (*bind*) `$this` và phạm vi của class đó, nên dùng được cả property
`private`:

```php
<?php
declare(strict_types=1);

final class PriceList
{
    private array $prices = ['bút' => 5_000, 'vở' => 12_000];
    private int $vatPercent = 10;

    public function withVat(): array
    {
        return array_map(function (int $p): int {
            return $p + intdiv($p * $this->vatPercent, 100);   // $this có sẵn, đọc được private
        }, $this->prices);
    }

    public function broken(): array
    {
        return array_map(static function (int $p): int {
            return $p + intdiv($p * $this->vatPercent, 100);   // static: không có $this
        }, $this->prices);
    }
}

$list = new PriceList();
print_r($list->withVat());   // in ra: Array ( [bút] => 5500 [vở] => 13200 )  (viết gọn)
$list->broken();             // Error: Using $this when not in object context
```

Thêm `static` trước `function` (hoặc `fn`) tạo *static closure*: không gắn `$this`, và cũng không gắn
object vào được về sau. Theo RFC arrow functions, static closure chủ yếu dùng để tránh vòng tham chiếu qua
`$this` làm việc thu gom bộ nhớ khó đoán; phần lớn code không cần bận tâm. Có một trường hợp nên bận tâm:
closure được cất giữ lâu (đăng ký vào danh sách listener, macro, cache tĩnh) trong tiến trình sống lâu
như Octane hay queue worker. Closure không static giữ `$this`, nên object đó và mọi thứ nó tham chiếu tới
không được giải phóng chừng nào closure còn nằm trong danh sách đó, tức là thường suốt đời worker. Khi
closure không cần `$this`, viết `static` là thói quen an toàn.

## 11. Arrow function `fn`

### 11.1 Cú pháp ngắn cho closure một biểu thức

Phần lớn callback chỉ là một biểu thức: so sánh, tính toán, lấy một field. Viết `function (...) use
(...) { return ...; }` cho chúng thì dài. *Arrow function* (PHP 7.4) là cú pháp ngắn:

```
fn (tham_số) => biểu_thức
```

```php
<?php
declare(strict_types=1);

$prices = [5_000, 12_000, 8_000];
$vatPercent = 10;

// function + use
$withVat1 = array_map(function (int $p) use ($vatPercent): int {
    return $p + intdiv($p * $vatPercent, 100);
}, $prices);

// arrow function: không cần use, không cần return
$withVat2 = array_map(fn(int $p): int => $p + intdiv($p * $vatPercent, 100), $prices);

var_dump($withVat1 === $withVat2);    // in ra: bool(true)
echo implode(',', $withVat2), "\n";   // in ra: 5500,13200,8800
```

Arrow function cũng là object `Closure`, cũng có kiểu tham số, kiểu trả về, giá trị mặc định, variadic,
tham chiếu, và cũng tự gắn `$this` khi tạo trong method (viết `static fn` để không gắn).

### 11.2 Tự bắt biến, nhưng chỉ theo giá trị

Khác biệt cốt lõi: arrow function **tự động** bắt mọi biến bên ngoài mà nó dùng, **theo giá trị**, tại thời
điểm tạo. Tương đương với viết `use ($x)` cho từng biến `$x` xuất hiện trong biểu thức.

```php
<?php
declare(strict_types=1);

$rate = 0.1;
$calc = fn(int $p): float => $p * $rate;
$rate = 0.5;
var_dump($calc(100));     // in ra: float(10)  (chụp $rate = 0.1 lúc tạo)

$x = 1;
$fn = fn(): int => $x++;  // tăng bản sao bên trong, biến ngoài không đổi
$fn();
var_dump($x);             // in ra: int(1)

$z = 1;
$curried = fn(int $a) => fn(int $b) => $a * $b + $z;   // lồng nhau: $z được chuyền vào tới hàm trong
var_dump($curried(5)(10));                              // in ra: int(51)
```

- Arrow function không thể sửa biến bên ngoài (không có cú pháp bắt theo tham chiếu). Cần sửa thì dùng
  `function () use (&$x)`.
- Chỉ những biến viết ra trực tiếp trong biểu thức mới được bắt. Biến được truy cập gián tiếp kiểu
  `$$name` không được bắt và sẽ là undefined bên trong.
- Bắt theo giá trị một array lớn không tốn copy (copy-on-write, mục 2.1).

### 11.3 Giới hạn: đúng một biểu thức

Thân của `fn` là một biểu thức, không phải khối lệnh. Không có `{ ... }`, không có nhiều câu lệnh, không
có `return`:

```php
$f = fn(int $x) => { return $x; };
// Parse error: syntax error, unexpected token "{"
```

`fn` có độ ưu tiên thấp nhất: mọi thứ bên phải `=>` thuộc về thân hàm. `fn($x) => $x + $y` là `fn($x) =>
($x + $y)`. Khi đặt arrow function giữa một biểu thức dài hơn thì bọc nó trong ngoặc. Với toán tử pipe `|>`
của PHP 8.5 ([Chương 07](07-toan-tu-dieu-khien.md)) thì ngoặc là bắt buộc: thiếu ngoặc là lỗi biên dịch
`Arrow functions on the right hand side of |> must be parenthesized`.

### 11.4 Chọn `function` hay `fn`

| | `function (...) use (...) { }` | `fn (...) => expr` |
|---|---|---|
| Có từ | 5.3 | 7.4 |
| Bắt biến ngoài | Phải liệt kê trong `use` | Tự động, mọi biến dùng trong biểu thức |
| Theo giá trị / tham chiếu | Cả hai (`use ($x)`, `use (&$x)`) | Chỉ theo giá trị |
| Thời điểm bắt | Lúc tạo closure | Lúc tạo closure |
| Thân | Nhiều câu lệnh, cần `return` | Đúng một biểu thức, tự trả về |
| Gắn `$this` trong class | Có (trừ khi `static`) | Có (trừ khi `static`) |

Quy tắc thực dụng: callback một dòng dùng `fn`; cần nhiều câu lệnh, cần sửa biến ngoài, hoặc logic đủ dài
để cần đọc kỹ thì dùng `function`. Logic dài và dùng ở nhiều nơi thì nên thành hàm có tên hoặc method.

## 12. Callable và first-class callable

### 12.1 Callable là gì

*Callable* là "thứ gì đó gọi được". Hàm nhận callback (như `array_map`) khai báo tham số kiểu `callable`.
PHP chấp nhận nhiều dạng:

| Dạng | Ví dụ |
|---|---|
| Chuỗi tên hàm | `'shout'`, `'strrev'` |
| Chuỗi `'Class::method'` (static method) | `'Formatter::dash'` |
| Array `[tên class, tên method]` (static method) | `[Formatter::class, 'dash']` |
| Array `[object, tên method]` | `[$f, 'wrap']` |
| Object có method `__invoke()` | `$f` |
| `Closure` (closure, arrow function, first-class callable) | `fn(string $s): string => "({$s})"` |

```php
<?php
declare(strict_types=1);

function shout(string $s): string
{
    return strtoupper($s) . '!';
}

final class Formatter
{
    public function wrap(string $s): string { return "[{$s}]"; }
    public static function dash(string $s): string { return "-{$s}-"; }
    public function __invoke(string $s): string { return "<{$s}>"; }   // object gọi được như hàm
}

$f = new Formatter();

$callables = [
    'shout',
    'strrev',
    'Formatter::dash',
    [Formatter::class, 'dash'],
    [$f, 'wrap'],
    $f,
    fn(string $s): string => "({$s})",
];

foreach ($callables as $c) {
    echo $c('abc'), ' ';        // gọi callable bằng cú pháp gọi hàm thường
}
echo "\n";
// in ra: ABC! cba -abc- -abc- [abc] <abc> (abc)
```

Class và `__invoke` thuộc [Chương 09](09-oop-co-ban.md) và [Chương 10](10-oop-nang-cao.md); ở đây chỉ cần
biết chúng là callable.

### 12.2 Gọi và kiểm tra callable

```php
// (shout, Formatter và $f như ví dụ trên)

function apply(callable $fn, string $value): string
{
    return $fn($value);
}

echo apply('shout', 'hello'), "\n";                      // in ra: HELLO!
echo call_user_func([$f, 'wrap'], 'a'), "\n";            // in ra: [a]
echo call_user_func_array('str_pad', ['7', 3, '0', STR_PAD_LEFT]), "\n";   // in ra: 007
// Từ 8.0, key chuỗi trong call_user_func_array là named argument:
echo call_user_func_array('str_pad', ['string' => '7', 'length' => 3, 'pad_type' => STR_PAD_LEFT]), "\n";
// in ra:   7   (hai dấu cách rồi số 7, vì pad_string giữ mặc định là dấu cách)

var_dump(is_callable('shout'));    // in ra: bool(true)
var_dump(is_callable('shuot'));    // in ra: bool(false)
var_dump(is_callable('isset'));    // in ra: bool(false)

try {
    apply('shuot', 'x');           // gõ sai tên: chỉ lộ ra khi chạy tới đây
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: apply(): Argument #1 ($fn) must be of type callable, string given, called in ... on line ...
}
```

- Biến chứa callable gọi được trực tiếp: `$fn = 'shout'; $fn('x');` (manual gọi là *variable functions*).
  `call_user_func()` và `call_user_func_array()` làm cùng việc, hữu ích khi danh sách đối số nằm sẵn trong
  một array; với cú pháp `...` (mục 7.2) thì `$fn(...$args)` thường gọn hơn.
- ⚠️ *Language construct* (cấu trúc ngôn ngữ) như `echo`, `print`, `isset`, `empty`, `unset`, `include`,
  `require`, `array()`, `list()`, `eval` không phải hàm, nên không phải callable: `$c = 'empty'; $c('');`
  ném `Error: Call to undefined function empty()`. Cần thì bọc trong closure: `fn($v) => empty($v)`.
- ⚠️ Kiểu `callable` dùng được cho tham số và giá trị trả về, nhưng không dùng được cho property của
  class (`Property Box::$fn cannot have type callable`). Dùng kiểu `Closure` thay thế.

### 12.3 First-class callable syntax: `strlen(...)` (PHP 8.1)

Callable dạng chuỗi và array có ba nhược điểm: gõ sai tên chỉ lộ khi chạy tới lúc gọi; IDE và công cụ phân
tích tĩnh khó lần theo (đổi tên hàm không tự đổi chuỗi `'shout'`); và quyền truy cập method `private` bị kiểm
tại nơi gọi, không phải nơi tạo.

PHP 8.1 thêm *first-class callable syntax*: viết lời gọi như bình thường nhưng thay danh sách đối số bằng
`(...)`. Thay vì **gọi**, PHP trả về một `Closure` trỏ tới hàm đó. Ba chấm là cú pháp thật, không phải lược
bớt.

```php
<?php
declare(strict_types=1);

function shout(string $s): string
{
    return strtoupper($s) . '!';
}

final class Normalizer
{
    public function run(array $names): array
    {
        return array_map($this->clean(...), $names);   // method private, dùng trong class
    }

    public function getCleaner(): Closure
    {
        return $this->clean(...);       // scope được chốt tại đây, nơi được phép gọi clean()
    }

    public function getCleanerOld(): array
    {
        return [$this, 'clean'];        // callable kiểu cũ: quyền truy cập kiểm ở nơi gọi
    }

    private function clean(string $s): string
    {
        return ucfirst(strtolower(trim($s)));
    }

    public static function slug(string $s): string
    {
        return strtolower(str_replace(' ', '-', trim($s)));
    }
}

$up   = strtoupper(...);           // Closure bọc hàm có sẵn
$sh   = shout(...);                // Closure bọc hàm tự viết
$slug = Normalizer::slug(...);     // Closure bọc static method
echo $up('abc'), ' ', $sh('hi'), ' ', $slug(' Hello World '), "\n";   // in ra: ABC HI! hello-world

$n = new Normalizer();
print_r($n->run(['  aN ', 'BINH']));    // in ra: Array ( [0] => An [1] => Binh )  (viết gọn)

$cleaner = $n->getCleaner();
echo $cleaner('  cHI '), "\n";          // in ra: Chi   (gọi được từ ngoài class)

$old = $n->getCleanerOld();
try {
    $old('  cHI ');
} catch (Error $e) {
    echo $e->getMessage(), "\n";      // in ra: Call to private method Normalizer::clean() from global scope
}

try {
    $typo = shuot(...);                 // gõ sai tên: lỗi ngay lúc tạo closure, không đợi tới lúc gọi
} catch (Error $e) {
    echo $e->getMessage(), "\n";      // in ra: Call to undefined function shuot()
}
```

Các dạng viết được: `strlen(...)`, `$obj->method(...)`, `Foo::method(...)`, `$closure(...)`,
`$invokableObject(...)`, và cả dạng cũ `'strlen'(...)`, `[$obj, 'method'](...)` để đổi callable cũ thành
`Closure`. Không viết được:

- `new Foo(...)`: tạo object không phải lời gọi hàm (`Fatal error: Cannot create Closure for new
  expression`). Cần thì viết `fn(...$args) => new Foo(...$args)`.
- `$obj?->method(...)`: không kết hợp với nullsafe (`Cannot combine nullsafe operator with Closure creation`).

Về `strict_types`: theo RFC, chế độ ở **chỗ tạo** `strlen(...)` không quan trọng; chỉ chế độ ở **chỗ gọi**
closure được tính, giống mọi lời gọi hàm khác (mục 4).

First-class callable kết hợp tự nhiên với toán tử pipe `|>` của PHP 8.5 ([Chương 07](07-toan-tu-dieu-khien.md)):

```php
<?php
declare(strict_types=1);

$slug = '  Hello World  '
    |> trim(...)
    |> strtolower(...)
    |> (fn(string $s): string => str_replace(' ', '-', $s));

echo $slug, "\n";   // in ra: hello-world
```

### 12.4 `Closure::fromCallable()`

`Closure::fromCallable($callable)` (7.1) đổi một callable bất kỳ thành `Closure`, kiểm tra callable đó gọi
được trong phạm vi hiện tại, sai thì ném `TypeError`. Manual ghi rõ: từ 8.1, first-class callable syntax
có cùng ngữ nghĩa với method này. Vì vậy `Closure::fromCallable([$this, 'clean'])` và `$this->clean(...)` là
một; code mới dùng cú pháp `(...)` cho ngắn, còn `fromCallable` vẫn có ích khi callable là một giá trị
nhận từ nơi khác (ví dụ cấu hình chứa `'App\Support\slugify'`).

### 12.5 Closure là object: `bind`, `bindTo`, `call`

Một closure mang theo hai thứ ngoài thân hàm: *bound object* (giá trị của `$this` bên trong) và *class scope*
(phạm vi class, quyết định closure đọc được member `private`/`protected` của class nào). Ba method của class
`Closure` tạo ra closure gắn với object hoặc scope khác:

- `Closure::bind($closure, $newThis, $newScope)` và `$closure->bindTo($newThis, $newScope)`: trả về một
  bản sao mới của closure, gắn với object và scope mới (closure gốc không đổi).
- `$closure->call($newThis, ...$args)` (7.0): gắn tạm vào `$newThis` (scope là class của nó) và gọi luôn.

```php
<?php
declare(strict_types=1);

final class Wallet
{
    private int $balance = 100;
}

$peek = function (): int {
    return $this->balance;               // tạo ngoài class: chưa có $this
};

$bound = Closure::bind($peek, new Wallet(), Wallet::class);
echo $bound(), "\n";                     // in ra: 100   (đọc được property private)

$w = new Wallet();
$topUp = function (int $amount): int {
    $this->balance += $amount;
    return $this->balance;
};
echo $topUp->call($w, 50), "\n";         // in ra: 150
echo $topUp->call($w, 50), "\n";         // in ra: 200

$reader = $peek->bindTo($w, Wallet::class);
echo $reader(), "\n";                    // in ra: 200

$peek();                                 // Error: Using $this when not in object context  (bản gốc vẫn chưa gắn)
```

Ví dụ cho thấy `bind` phá vỡ đóng gói: ai có closure và object là đọc/sửa được `private`. Trong code ứng
dụng hiếm khi cần; nó là công cụ cho framework và thư viện. Ví dụ thật: trait `Macroable` của Laravel 13 cho
phép "gắn thêm method" vào class lúc chạy bằng `Str::macro('tenMacro', function (...) {...})`. Closure được
cất vào một array static; khi gọi, `__call` chạy `$macro->bindTo($this, static::class)` để trong closure
dùng `$this` như một method thật, còn `__callStatic` chạy `$macro->bindTo(null, static::class)`.

⚠️ Gắn object vào static closure không làm được: PHP báo Warning và trả về `null`. PHP 8.5 xếp trường hợp
này (cùng vài trường hợp bind sai khác) vào diện deprecated, thông báo đổi thành `Warning: Cannot bind an
instance to a static closure, this will be an error in PHP 9`.

### 12.6 Khai báo kiểu: `callable` hay `Closure`

- `callable` nhận mọi dạng ở mục 12.1, nhưng không dùng được cho property, và không mô tả được chữ ký hàm
  (nhận gì, trả gì). Manual: "Closure is the preferred way to create callables."
- `Closure` chỉ nhận object closure, dùng được ở mọi chỗ kể cả property. Người gọi có callable cũ thì đổi
  bằng `(...)` hoặc `Closure::fromCallable()`.
- Từ PHP 8.5, `Closure` được coi là kiểu con thật sự của `callable`: class con có thể thu hẹp kiểu trả về
  `callable` của method cha thành `Closure` (PHP 8.4 báo lỗi `Declaration of B::get(): Closure must be
  compatible with A::get(): callable`).
- Muốn mô tả chữ ký của callback (ví dụ `Closure(int): bool`), PHP chưa có cú pháp; dùng PHPDoc
  `@param Closure(int): bool $filter` cho PHPStan/Psalm ([Chương 21](21-chat-luong-code.md)).

## 13. Đệ quy

### 13.1 Hàm tự gọi chính nó

*Đệ quy* (*recursion*) là khi một hàm gọi lại chính nó để giải một phiên bản nhỏ hơn của cùng bài toán.
Mọi hàm đệ quy đúng đều có hai phần:

1. *Điểm dừng* (*base case*): trường hợp đủ nhỏ để trả lời ngay, không gọi đệ quy nữa.
2. *Bước đệ quy* (*recursive case*): đưa bài toán về bài toán nhỏ hơn, gọi lại chính hàm, rồi ghép kết quả.

Ví dụ kinh điển: giai thừa `n! = n × (n-1)!`, với `1! = 1`.

```php
<?php
declare(strict_types=1);

function factorial(int $n): int
{
    if ($n <= 1) {
        return 1;                       // điểm dừng
    }
    return $n * factorial($n - 1);      // bước đệ quy: bài toán nhỏ hơn
}

echo factorial(5), "\n";                // in ra: 120
echo factorial(20), "\n";               // in ra: 2432902008176640000
factorial(21);
// TypeError: factorial(): Return value must be of type int, float returned
```

Dòng cuối là một bài học về kiểu: `21!` vượt `PHP_INT_MAX` (trên hệ 64-bit) nên phép nhân tràn sang `float`
([Chương 04](04-kieu-du-lieu.md)), và kiểu trả về `int` chặn lại thay vì để một số sai âm thầm đi tiếp.

Mỗi lời gọi hàm tạo một *stack frame* (khung lưu tham số, biến cục bộ và chỗ quay về) đặt lên *call stack*.
Với `factorial(4)`:

```
gọi xuống (stack lớn dần)                quay lên (stack nhỏ dần)

factorial(4)  chờ 4 * factorial(3)       factorial(4) = 4 * 6  = 24
  factorial(3)  chờ 3 * factorial(2)       factorial(3) = 3 * 2  = 6
    factorial(2)  chờ 2 * factorial(1)       factorial(2) = 2 * 1  = 2
      factorial(1)  điểm dừng, trả 1   ──►     factorial(1) = 1
```

Thiếu điểm dừng, hoặc bước đệ quy không thật sự làm bài toán nhỏ đi (ví dụ quên `- 1`), thì hàm gọi mãi
cho tới khi hết tài nguyên (mục 13.3).

### 13.2 Đệ quy hợp với dữ liệu dạng cây

Giai thừa viết bằng vòng lặp cũng dễ. Đệ quy thật sự toả sáng khi dữ liệu tự lồng chính nó: cây danh mục,
menu nhiều cấp, bình luận trả lời bình luận, thư mục chứa thư mục, JSON lồng nhau. Mỗi nút con là một cây nhỏ
có cùng cấu trúc với cây lớn, nên hàm xử lý cây lớn cũng xử lý được cây con:

```php
<?php
declare(strict_types=1);

$categories = [
    ['name' => 'Điện tử', 'children' => [
        ['name' => 'Điện thoại', 'children' => [
            ['name' => 'Android', 'children' => []],
            ['name' => 'iPhone', 'children' => []],
        ]],
        ['name' => 'Laptop', 'children' => []],
    ]],
    ['name' => 'Sách', 'children' => []],
];

function renderTree(array $nodes, int $depth = 0): string
{
    $out = '';
    foreach ($nodes as $node) {
        $out .= str_repeat('  ', $depth) . '- ' . $node['name'] . "\n";
        $out .= renderTree($node['children'], $depth + 1);   // cây con xử lý y hệt cây lớn
    }
    return $out;   // danh sách rỗng: vòng lặp không chạy, không gọi đệ quy nữa (điểm dừng)
}

echo renderTree($categories);
// in ra:
// - Điện tử
//   - Điện thoại
//     - Android
//     - iPhone
//   - Laptop
// - Sách

function flatten(array $items): array
{
    $result = [];
    foreach ($items as $item) {
        if (is_array($item)) {
            array_push($result, ...flatten($item));   // phần tử là array: làm phẳng nó trước
        } else {
            $result[] = $item;                        // phần tử thường: điểm dừng
        }
    }
    return $result;
}

echo implode(',', flatten([1, [2, [3, [4]], 5], [[6]]])), "\n";   // in ra: 1,2,3,4,5,6
```

Điểm dừng ở đây không phải một câu `if` riêng mà nằm sẵn trong dữ liệu: nút lá có `children` rỗng, phần tử
không phải array. Khi viết hàm đệ quy, luôn tự hỏi: "trường hợp nhỏ nhất là gì, và mỗi lần gọi có tiến gần
tới nó không?"

### 13.3 Giới hạn của đệ quy trong PHP

- PHP không có *tail call optimization* (tối ưu lời gọi đuôi): kể cả khi lời gọi đệ quy là việc cuối
  cùng của hàm, mỗi lần gọi vẫn tốn một frame mới. Java và Go cũng không có tối ưu này.
- Đệ quy thuần PHP (hàm PHP gọi hàm PHP) cấp phát frame trong vùng nhớ do PHP quản lý, tính vào
  `memory_limit`. Đệ quy vô hạn thường kết thúc bằng `Fatal error: Allowed memory size of ... bytes exhausted
  (tried to allocate ... bytes)` (output minh hoạ, con số tuỳ cấu hình).
- Khi bật Xdebug (thường có ở máy dev), Xdebug ném `Error` khi độ sâu vượt `xdebug.max_nesting_level`
  (mặc định 512; trước Xdebug 3.3 là 256). Vì vậy code đệ quy sâu chạy được trên production có thể lỗi trên
  máy dev.
- Đệ quy đi qua hàm có sẵn (ví dụ callback của `array_map` gọi lại chính hàm đang chạy), hoặc qua các
  magic method như `__toString`, `__destruct`, dùng C stack của tiến trình; trước đây tràn C stack là crash
  (segfault). Từ PHP 8.3, PHP ném `Error: Maximum call stack size of ... bytes
  (zend.max_allowed_stack_size - zend.reserved_stack_size) reached. Infinite recursion?`, điều chỉnh bằng
  các ini `zend.max_allowed_stack_size` và `zend.reserved_stack_size`.

Hệ quả thực tế: đệ quy theo độ sâu của **cấu trúc dữ liệu** (cây danh mục vài cấp, JSON vài chục tầng) là an
toàn. Đệ quy theo **kích thước dữ liệu** (đệ quy một lần cho mỗi phần tử của danh sách 1 triệu dòng) thì
không. Dữ liệu lồng nhau do người ngoài gửi tới có thể bị cố ý làm sâu bất thường; các hàm có sẵn tự vệ bằng
giới hạn độ sâu, ví dụ `json_decode()` có tham số `$depth` mặc định 512. Hàm đệ quy tự viết cho dữ liệu đầu
vào nên làm tương tự: nhận thêm tham số độ sâu và dừng khi vượt ngưỡng.

### 13.4 Đổi đệ quy thành vòng lặp với stack tự quản lý

Mọi hàm đệ quy đều viết lại được bằng vòng lặp và một array đóng vai stack, nhờ đó độ sâu chỉ còn bị giới hạn
bởi bộ nhớ cho array:

```php
<?php
declare(strict_types=1);

function flattenIterative(array $items): array
{
    $result = [];
    $stack = [$items];                   // stack tự quản lý thay cho call stack
    while ($stack !== []) {
        $current = array_pop($stack);    // lấy phần tử trên cùng
        if (!is_array($current)) {
            $result[] = $current;
            continue;
        }
        foreach (array_reverse($current) as $child) {
            $stack[] = $child;           // đẩy ngược để phần tử đầu được lấy ra trước
        }
    }
    return $result;
}

echo implode(',', flattenIterative([1, [2, [3, [4]], 5], [[6]]])), "\n";   // in ra: 1,2,3,4,5,6
```

Đổi lại, code khó đọc hơn bản đệ quy. Chọn đệ quy khi độ sâu có giới hạn hợp lý và code rõ hơn; chọn vòng lặp
khi độ sâu phụ thuộc dữ liệu không kiểm soát được.

### 13.5 Memoization: đừng tính lại cái đã tính

Fibonacci `F(n) = F(n-1) + F(n-2)` viết đệ quy thẳng thì mỗi lời gọi đẻ ra hai lời gọi, và cùng một `F(k)` bị
tính lại rất nhiều lần:

```php
<?php
declare(strict_types=1);

function fibSlow(int $n, int &$calls): int
{
    $calls++;
    return $n < 2 ? $n : fibSlow($n - 1, $calls) + fibSlow($n - 2, $calls);
}

$calls = 0;
echo fibSlow(25, $calls), " sau {$calls} lần gọi\n";   // in ra: 75025 sau 242785 lần gọi

function fibMemo(int $n): int
{
    static $memo = [0 => 0, 1 => 1];     // biến static: nhớ kết quả giữa các lần gọi (mục 9.3)
    if (!isset($memo[$n])) {
        $memo[$n] = fibMemo($n - 1) + fibMemo($n - 2);
    }
    return $memo[$n];
}

echo fibMemo(25), "\n";                  // in ra: 75025
echo fibMemo(90), "\n";                  // in ra: 2880067194370816120  (mỗi F(k) chỉ tính một lần)
```

`fibSlow` có số lời gọi tăng theo hàm mũ; `fibMemo` chỉ tính mỗi `F(k)` một lần nên số bước tăng tuyến
tính. Kỹ thuật "ghi nhớ kết quả của hàm theo đối số" gọi là *memoization*. Nó chỉ đúng với hàm *thuần*
(*pure function*): cùng đối số luôn cho cùng kết quả và không có tác dụng phụ. Nhớ cảnh báo ở mục 9.3: cache
trong biến `static` sống suốt đời tiến trình.

### 13.6 Closure đệ quy

Closure không có tên, vậy làm sao nó gọi lại chính nó? Cách truyền thống là bắt chính biến chứa nó theo
tham chiếu:

```php
<?php
declare(strict_types=1);

$fact = function (int $n) use (&$fact): int {    // phải là &: lúc tạo closure, $fact chưa được gán
    return $n <= 1 ? 1 : $n * $fact($n - 1);
};
echo $fact(5), "\n";      // in ra: 120

// PHP 8.5: Closure::getCurrent() trả về closure đang chạy, không cần use
$fact2 = function (int $n): int {
    return $n <= 1 ? 1 : $n * Closure::getCurrent()($n - 1);
};
echo $fact2(5), "\n";     // in ra: 120
```

- Phải là `use (&$fact)`. Viết `use ($fact)` thì closure chụp giá trị của `$fact` trước khi phép gán xong,
  tức là chưa có gì.
- Arrow function bắt theo giá trị nên không tự gọi lại được bằng tên biến. Viết
  `$f = fn(int $n): int => $n <= 1 ? 1 : $n * $f($n - 1);` rồi gọi `$f(3)` sẽ báo
  `Warning: Undefined variable $f` rồi `Error: Value of type null is not callable`. Trên PHP 8.5 dùng
  `Closure::getCurrent()` bên trong `fn` thì được.
- `Closure::getCurrent()` gọi ngoài closure ném `Error: Current function is not a closure`; trên PHP 8.4 trở về
  trước method này không tồn tại.

## 14. Hàm có sẵn và hàm tự viết

### 14.1 Hai nguồn gốc của hàm

- *Hàm có sẵn* (*built-in*, manual gọi là *internal function*): viết bằng C, nằm trong lõi PHP hoặc trong
  các *extension* (phần mở rộng). `strlen`, `array_map`, `json_encode`, `preg_match` đều thuộc loại này.
  Gọi được ngay, không cần `include`.
- *Hàm tự viết* (*user-defined function*): viết bằng PHP, của bạn hoặc của thư viện cài qua Composer.

Hàm của extension chỉ tồn tại khi extension đó được nạp. Gọi `mb_strlen()` trên một bản PHP thiếu
`mbstring` sẽ ném `Error: Call to undefined function mb_strlen()`. Kiểm tra bằng `function_exists()`,
`extension_loaded()`, hoặc chạy `php -m` (trên terminal của máy hay container chạy PHP) để liệt kê extension.

```php
<?php
declare(strict_types=1);

function slugify(string $s): string
{
    return strtolower(trim($s));
}

$fns = get_defined_functions();                  // ['internal' => [...], 'user' => [...]]
var_dump($fns['user']);                          // in ra: array(1) { [0]=> string(7) "slugify" }  (viết gọn)
var_dump(in_array('strlen', $fns['internal'], true));   // in ra: bool(true)

var_dump(function_exists('SLUGIFY'));            // in ra: bool(true)  (không phân biệt hoa thường)
var_dump(extension_loaded('mbstring'));          // in ra: bool(true) nếu bản PHP có mbstring

var_dump((new ReflectionFunction('strlen'))->isInternal());        // in ra: bool(true)
var_dump((new ReflectionFunction('slugify'))->isUserDefined());    // in ra: bool(true)
```

### 14.2 Khác nhau ở đâu

Phần lớn thời gian hai loại hàm cư xử giống nhau. Những chỗ khác đã gặp rải rác trong chương:

| | Hàm có sẵn | Hàm tự viết |
|---|---|---|
| Viết bằng | C | PHP |
| Truyền thừa đối số | `ArgumentCountError` (từ 8.0) | Bỏ qua, đọc được bằng `func_get_args()` (mục 2.2) |
| `null` vào tham số scalar không nullable, coercive mode | Deprecated (từ 8.1), rồi ép thành `''`/`0` | `TypeError` (mục 4.3) |
| Callback mà nó gọi | Luôn coercive mode (mục 4.2) | Theo file chứa lời gọi |
| Tham số không bỏ qua được bằng named argument | Có (ví dụ `$filter_value` của `array_keys`) | Không (mục 6.2) |
| Định nghĩa lại | Không được | Không được (mục 1.5) |

Vài điều thực dụng rút ra:

- Ưu tiên hàm có sẵn thay vì tự viết vòng lặp làm cùng việc (`array_sum`, `in_array`, `array_column`,
  `str_contains`...): đã được kiểm thử kỹ, người đọc nhận ra ngay, và thường nhanh hơn vì chạy bằng C. Một
  số hàm như `strlen()`, `count()`, `is_int()` còn được trình biên dịch thay bằng opcode riêng
  khi nó biết chắc tên đang trỏ tới hàm có sẵn; điều này liên quan tới cách viết `\strlen()` trong namespace
  ([Chương 11](11-namespace-composer.md), [Chương 20](20-hieu-nang.md)).
- Đọc chữ ký trong manual trước khi dùng. Ví dụ chữ ký của `str_replace` trên php.net:

```
str_replace(
    array|string $search,
    array|string $replace,
    string|array $subject,
    int &$count = null
): string|array
```

  Đọc ra được: hai tham số đầu nhận chuỗi hoặc array; `&$count` là tham số tham chiếu tuỳ chọn để nhận số
  lần thay (mục 8.2); kiểu trả về đi theo kiểu của `$subject`. Tên tham số (`search`, `replace`, `subject`)
  là tên dùng cho named argument.
- ⚠️ Nhiều hàm cũ trả `false` khi thất bại, kể cả hàm mà kết quả thành công có thể là `0` hay `''`. Bẫy
  kinh điển với `strpos()`:

```php
<?php
declare(strict_types=1);

$email = 'admin@example.com';

if (strpos($email, 'admin')) {             // strpos trả 0 (vị trí đầu chuỗi), if coi 0 là false
    echo "tìm thấy\n";
} else {
    echo "KHÔNG tìm thấy?!\n";             // in ra dòng này: sai!
}

if (strpos($email, 'admin') !== false) {   // so sánh chặt với false
    echo "tìm thấy\n";                     // in ra: tìm thấy
}

var_dump(str_contains($email, 'admin'));   // in ra: bool(true)  (PHP 8.0+: hàm trả bool, hết bẫy)
```

  Luôn so kết quả kiểu `int|false`, `string|false` bằng `=== false` / `!== false` ([Chương 07](07-toan-tu-dieu-khien.md)).
  `strict_types` không cứu được chỗ này, vì nó không áp cho điều kiện của `if`.

## 15. `#[\NoDiscard]`: đừng bỏ quên giá trị trả về (PHP 8.5)

### 15.1 Vấn đề

Có những hàm mà gọi xong bỏ quên kết quả gần như chắc chắn là bug, nhưng bug đó im lặng:

- Hàm xử lý hàng loạt trả về danh sách phần tử thất bại: không đọc kết quả thì không ai biết có lỗi.
- Method của object *immutable* (không đổi được) trả về object mới thay vì sửa object cũ. Ví dụ
  `DateTimeImmutable::setDate()`: viết `$d->setDate(2026, 12, 31);` rồi dùng tiếp `$d` thì `$d` vẫn là ngày cũ.

Exception không hợp cho các trường hợp này, vì hàm không thất bại hẳn, nó chỉ trả về một thông tin quan trọng.

### 15.2 Cách dùng

PHP 8.5 thêm attribute `#[\NoDiscard]` (*attribute* là "nhãn" gắn lên hàm, class...; học kỹ ở
[Chương 10](10-oop-nang-cao.md)). Gắn nó lên hàm hoặc method thì mỗi khi kết quả bị bỏ đi, PHP báo Warning:

```php
<?php
declare(strict_types=1);

/**
 * Gửi email cho từng người nhận, trả về danh sách địa chỉ gửi THẤT BẠI.
 *
 * @param list<string> $recipients
 * @return list<string>
 */
#[\NoDiscard('vì một số địa chỉ có thể gửi thất bại')]
function sendNewsletter(array $recipients): array
{
    $failed = [];
    foreach ($recipients as $email) {
        if (!str_contains($email, '@')) {    // giả lập: địa chỉ sai thì gửi lỗi
            $failed[] = $email;
        }
    }
    return $failed;
}

$list = ['an@x.vn', 'binh-khong-hop-le', 'chi@x.vn'];

sendNewsletter($list);                       // bỏ quên kết quả
// Warning: The return value of function sendNewsletter() should either be used or intentionally
// ignored by casting it as (void), vì một số địa chỉ có thể gửi thất bại in ... on line 24

$failed = sendNewsletter($list);             // dùng kết quả: không cảnh báo
echo 'Gửi lỗi: ', implode(', ', $failed), "\n";   // in ra: Gửi lỗi: binh-khong-hop-le

(void) sendNewsletter($list);                // cố ý bỏ qua: không cảnh báo
```

- Thông điệp tuỳ chọn (`'vì một số địa chỉ...'`) được nối vào cuối Warning.
- "Dùng" kết quả nghĩa là giá trị trả về nằm trong một biểu thức bất kỳ: gán vào biến (kể cả biến bỏ đi như
  `$_`), truyền vào hàm khác, so sánh...
- *(void) cast* (cũng mới ở 8.5) là cách nói "tôi cố ý bỏ kết quả". Nó là một câu lệnh, không phải biểu thức:
  `if ((void) f())` là lỗi cú pháp.
- Hàm khai báo `: void` hoặc `: never` mà gắn `#[\NoDiscard]` là lỗi biên dịch, ví dụ với `: void`:
  `A void function does not return a value, but #[\NoDiscard] requires a return value` (với `: never`
  thông báo bắt đầu bằng `A never returning function`).

Hàm có sẵn cũng dùng attribute này. Trên PHP 8.5, các method trả về object mới của `DateTimeImmutable`
(`setDate`, `setTime`, `modify`, `add`, `sub`, `setTimezone`...) được gắn `#[\NoDiscard]`:

```php
<?php
declare(strict_types=1);

$d = new DateTimeImmutable('2026-01-15');
$d->setDate(2026, 12, 31);
// Warning: The return value of method DateTimeImmutable::setDate() should either be used or
// intentionally ignored by casting it as (void), as DateTimeImmutable::setDate() does not modify
// the object itself in ... on line 5
echo $d->format('Y-m-d'), "\n";                       // in ra: 2026-01-15  ($d không đổi)
echo $d->setDate(2026, 12, 31)->format('Y-m-d'), "\n";  // in ra: 2026-12-31
```

(RFC ban đầu đề xuất gắn cả cho `flock()`, nhưng trong bản 8.5 phát hành, chữ ký của `flock()` không có
attribute này và gọi bỏ kết quả không sinh cảnh báo.)

### 15.3 Những điều cần biết thêm

- Tương thích ngược: attribute không có tác dụng trên PHP 8.4 trở về trước (PHP bỏ qua attribute có class
  không tồn tại; chỉ khi có code gọi `newInstance()` trên nó qua Reflection mới báo lỗi), nên thư viện gắn
  `#[\NoDiscard]` vẫn chạy trên bản cũ.
  Nhưng cú pháp `(void)` thì không có trên bản cũ: trên PHP 8.4, `(void) sendNewsletter($list);` là
  `Parse error`. Code cần chạy cả 8.4 nên dùng `$_ = sendNewsletter($list);`.
- Kiểm tra trước khi gọi: PHP kiểm "kết quả có được dùng không" ngay trước khi gọi hàm. Nếu ứng dụng
  có error handler đổi Warning thành exception (Laravel làm vậy, [Chương 12](12-loi-exception.md)), hàm sẽ
  **không được chạy** và exception được ném ra. RFC gọi đây là cơ chế "fail-closed": thà không chạy còn hơn
  chạy mà bỏ quên kết quả.
- Theo khai báo thật sự được gọi: gắn `#[\NoDiscard]` lên method của interface hay method abstract
  không sinh cảnh báo, vì method chạy là method của class cài đặt. Method override cũng không thừa hưởng
  attribute của method cha, trừ khi tự gắn.
- Khi nào nên dùng: chỉ cho hàm mà bỏ quên kết quả là bug khó phát hiện, như hai ví dụ trên. RFC khuyên
  không gắn cho hàm thuần như `str_contains()`: bỏ quên kết quả của nó chỉ là phí công, không gây sai.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Dùng biến bên ngoài trong hàm mà không truyền vào, nhận `Warning: Undefined variable` và giá trị `null` | Hàm có phạm vi riêng, không tự thấy biến toàn cục (mục 9.1) | Truyền qua tham số; closure thì dùng `use` hoặc `fn` |
| Truyền `null` và mong hàm dùng giá trị mặc định | Mặc định chỉ dùng khi **không truyền** đối số (mục 5.1) | Không truyền đối số đó, hoặc trong hàm viết `$x ??= 'mặc định';` |
| Viết `string $x = null` | Nullable ngầm, Deprecated từ PHP 8.4 (mục 3.6) | Viết `?string $x = null` |
| Tham số tuỳ chọn đứng trước tham số bắt buộc | Mặc định không bao giờ dùng được; Deprecated từ 8.0 (mục 5.5) | Đưa tham số tuỳ chọn ra cuối |
| Đổi tên tham số của hàm/method public, hoặc class con đặt tên tham số khác class cha | Tên tham số là API khi người gọi dùng named argument; PHP không kiểm lúc khai báo (mục 6.3) | Coi đổi tên là breaking change; giữ đúng tên của interface/class cha |
| `array_merge(...$groups)` với `$groups` có key chuỗi | Key chuỗi khi unpacking là named argument (mục 7.3) | `array_merge(...array_values($groups))` |
| `$sorted = sort($arr);` | `sort()` sửa array qua tham chiếu và trả `true` (mục 8.2) | Đọc chữ ký: tham số có `&` là hàm sửa biến của bạn |
| Thêm `&` "cho nhanh" | Copy-on-write đã tránh copy khi chỉ đọc; `&` làm code khó đọc (mục 8.4) | Truyền theo giá trị, trả về giá trị mới |
| `if (strpos($s, 'x'))` | `strpos` trả `0` khi tìm thấy ở đầu chuỗi (mục 14.2) | `!== false`, hoặc `str_contains()` |
| Closure dùng biến ngoài mà quên `use`, hoặc mong `use ($x)` thấy giá trị mới của `$x` | `use` theo giá trị chụp lúc tạo closure (mục 10.2) | Liệt kê trong `use`; cần thấy thay đổi thì `use (&$x)` |
| Arrow function `fn() => $count++` mong tăng biến ngoài | `fn` chỉ bắt theo giá trị (mục 11.2) | Dùng `function () use (&$count)` |
| Closure trong class được cất lâu trong worker làm bộ nhớ tăng mãi | Closure không static giữ `$this` (mục 10.5) | Dùng `static function`/`static fn` khi không cần `$this` |
| Callable dạng chuỗi gõ sai tên, chỉ lỗi khi chạy tới | Chuỗi không được kiểm lúc viết (mục 12.3) | Dùng first-class callable `tenHam(...)`, lỗi ngay lúc tạo, IDE kiểm được |
| Tin `strict_types` kiểm cả dữ liệu đi qua `array_map`, `usort` | Callback do hàm có sẵn gọi luôn ở coercive mode (mục 4.2) | Kiểm và chuyển kiểu dữ liệu đầu vào trước |
| Đệ quy thiếu điểm dừng, hoặc đệ quy một tầng cho mỗi phần tử của danh sách lớn | Mỗi lời gọi tốn một frame, PHP không tối ưu lời gọi đuôi (mục 13.3) | Kiểm điểm dừng; giới hạn độ sâu; đổi sang vòng lặp với stack tự quản lý |
| Biến `static` hay biến toàn cục giữ dữ liệu theo request trong Octane/queue worker | Trạng thái sống suốt đời tiến trình (mục 9.3) | Chỉ cache dữ liệu bất biến; dữ liệu theo request đi qua tham số hoặc container |
| `$d->setDate(...)` trên `DateTimeImmutable` rồi dùng tiếp `$d` | Method trả object mới, `$d` không đổi; PHP 8.5 báo Warning nhờ `#[\NoDiscard]` (mục 15.2) | `$d = $d->setDate(...)` |

## Tóm tắt chương

- Hàm đóng gói một việc có tên, nhận tham số, trả một giá trị (`return` kết thúc hàm ngay; không `return`
  thì trả `null`). Tên hàm không phân biệt hoa thường, không overload, không khai báo lại được.
- Đối số mặc định truyền theo giá trị; copy-on-write làm việc truyền array lớn rẻ khi hàm chỉ đọc. Thiếu đối
  số là `ArgumentCountError`; thừa đối số thì hàm tự viết bỏ qua, hàm có sẵn báo lỗi.
- Khai báo kiểu ở tham số và giá trị trả về là cổng kiểm tra lúc chạy. `?T` cho nullable (đừng dùng `= null`
  ngầm), `void` là trả về không giá trị, `never` là không bao giờ trả về, `static` là trả về đúng class được gọi.
- `strict_types` kiểm đối số theo file **gọi**, kiểm `return` theo file **khai báo**, và không áp cho callback
  do hàm có sẵn gọi.
- Giá trị mặc định phải là constant expression (thêm `new` từ 8.1, closure static và `f(...)` từ 8.5), được tính
  lại ở mỗi lời gọi. Named arguments (8.0) giúp đọc dễ và bỏ qua tham số tuỳ chọn, đổi lại tên tham số thành API.
- `...$args` gom đối số còn lại thành array có kiểm kiểu từng phần tử; `...$array` ở chỗ gọi trải array thành
  đối số, key chuỗi thành named argument.
- `&` cho hàm sửa biến của người gọi; dùng tiết kiệm và đừng dùng vì hiệu năng.
- Hàm chỉ thấy tham số và biến của mình; `global`/`$GLOBALS` và biến `static` là trạng thái dùng chung, cẩn thận
  trong tiến trình sống lâu.
- Closure là object `Closure`; `use` chụp theo giá trị lúc tạo (hoặc `&` theo tham chiếu); `fn` tự chụp theo giá
  trị, một biểu thức. First-class callable `f(...)` (8.1) là cách tạo closure từ hàm/method an toàn nhất;
  `bind`/`bindTo`/`call` đổi `$this` và scope của closure.
- Đệ quy cần điểm dừng và bài toán nhỏ dần; hợp với dữ liệu dạng cây; không có tối ưu lời gọi đuôi; memoization
  tránh tính lại. PHP 8.5 có `Closure::getCurrent()` cho closure đệ quy và `#[\NoDiscard]` cùng `(void)` để
  không bỏ quên giá trị trả về quan trọng.

## Câu hỏi tự kiểm tra

1. Gọi một hàm ở dòng phía trên chỗ khai báo nó lúc nào chạy được, lúc nào không? (gợi ý: mục 1.3)
2. Hàm khai báo `: void` trả gì cho người gọi? Khác gì `: never`? Viết `return null;` trong hàm `void` thì sao?
3. File `a.php` có `declare(strict_types=1)` gọi hàm `f(int $x): int` khai báo trong `b.php` không strict, truyền
   `'5'`. Chuyện gì xảy ra? Nếu đảo vị trí `declare` sang `b.php` thì sao? Còn giá trị `return` của `f`?
   (gợi ý: mục 4.1)
4. Vì sao `function f(string $s = null)` bị Deprecated, và vì sao `?string $s` (không có `= null`) vẫn là tham số
   bắt buộc?
5. Giải thích vì sao `array_merge(...$groups)` ném `ArgumentCountError` khi `$groups` là array có key chuỗi.
   (gợi ý: mục 7.3)
6. Truyền một array 100 000 phần tử vào hàm chỉ đếm và tính tổng có tốn bộ nhớ gấp đôi không? Khi nào truyền
   theo giá trị thật sự tốn kém? (gợi ý: mục 2.1, 8.4)
7. Với `$x = 1; $f = function () use ($x) { return $x; }; $x = 2;`, `$f()` trả gì? Đổi thành `use (&$x)` thì
   sao? Đổi thành `fn() => $x` thì sao?
8. `$this->clean(...)` và `[$this, 'clean']` khác nhau thế nào khi `clean` là method `private` và callable được
   gọi từ bên ngoài class? (gợi ý: mục 12.3)
9. Vì sao đệ quy theo độ sâu của cây danh mục thì an toàn còn đệ quy một tầng cho mỗi dòng của file CSV một
   triệu dòng thì không? Đệ quy vô hạn trong PHP thường kết thúc bằng lỗi gì? (gợi ý: mục 13.3)
10. Trong một ứng dụng Laravel có error handler đổi Warning thành exception, gọi một hàm `#[\NoDiscard]` mà bỏ
    kết quả thì hàm đó có chạy không? (gợi ý: mục 15.3)

## Bài tập

**Bài 1. Hàm ghép bước.** Viết `compose(Closure ...$steps): Closure` trả về một closure nhận một chuỗi và lần
lượt cho nó đi qua từng bước. Dùng nó để tạo `$slugify = compose(trim(...), strtolower(...), ...)` biến
`'  Học PHP 8.5  '` thành dạng slug (chữ thường, khoảng trắng thành `-`; chưa cần bỏ dấu tiếng Việt). Yêu cầu:
`declare(strict_types=1)`, khai báo kiểu đầy đủ, `compose()` không có bước nào thì trả về chính chuỗi đầu
vào. Viết thêm phiên bản dùng toán tử `|>` (PHP 8.5) và so sánh cách đọc.

**Bài 2. Memoize.** Viết `memoize(Closure $fn): Closure` trả về một closure có cùng tác dụng với `$fn` nhưng
ghi nhớ kết quả theo đối số (gợi ý: khoá cache là `serialize($args)` hoặc `json_encode($args)`, với `$args`
nhận qua `...$args`). Kiểm chứng bằng một hàm chậm có biến đếm số lần thật sự chạy. Trả lời thêm bằng lời: vì
sao không dùng biến `static` bên trong `memoize()` để làm cache, và điều gì xảy ra nếu bọc một hàm không thuần
(ví dụ hàm trả về thời gian hiện tại)?

**Bài 3. Cây danh mục.** Cho danh sách phẳng như khi đọc từ bảng `categories`:

```php
$rows = [
    ['id' => 1, 'parent_id' => null, 'name' => 'Điện tử'],
    ['id' => 2, 'parent_id' => 1, 'name' => 'Điện thoại'],
    ['id' => 3, 'parent_id' => 2, 'name' => 'Android'],
    ['id' => 4, 'parent_id' => 1, 'name' => 'Laptop'],
    ['id' => 5, 'parent_id' => null, 'name' => 'Sách'],
];
```

Viết `buildTree(array $rows, ?int $parentId = null): array` (đệ quy) trả về cây lồng nhau có key `children`,
và `renderTree(array $tree, int $maxDepth = 10): string` in cây có thụt lề, dừng khi vượt `$maxDepth`. Sau đó
viết lại `renderTree` không dùng đệ quy (stack tự quản lý) và kiểm tra hai bản cho cùng kết quả. Câu hỏi thêm:
nếu dữ liệu có vòng (`parent_id` của 1 là 3) thì bản đệ quy của bạn làm gì?

**Bài 4. Thí nghiệm strict_types và NoDiscard.** Tạo hai file `lib.php` (không strict) và `app.php` (strict)
như mục 4.1. Trước khi chạy, ghi ra dự đoán kết quả của 6 lời gọi do bạn tự chọn (truyền `'5'`, `5.0`, `5.5`,
`null`, gọi hàm có sẵn, callback qua `array_map`), rồi chạy để đối chiếu. Sau đó thêm vào `lib.php` một hàm
`saveAll(array $rows): array` gắn `#[\NoDiscard]`, trả về danh sách dòng lưu lỗi, và thử ba cách gọi (bỏ kết quả,
gán vào biến, `(void)`) trên cả PHP 8.5 và PHP 8.4
(`docker run --rm -v "$PWD":/app -w /app php:8.4-cli php app.php`). Giải thích từng khác biệt.

## Đọc thêm

- PHP Manual, mục Functions:
  [User-defined functions](https://www.php.net/manual/en/functions.user-defined.php) ·
  [Function parameters and arguments](https://www.php.net/manual/en/functions.arguments.php) ·
  [Returning values](https://www.php.net/manual/en/functions.returning-values.php) ·
  [Variable functions](https://www.php.net/manual/en/functions.variable-functions.php) ·
  [Internal functions](https://www.php.net/manual/en/functions.internal.php) ·
  [Anonymous functions](https://www.php.net/manual/en/functions.anonymous.php) ·
  [Arrow Functions](https://www.php.net/manual/en/functions.arrow.php) ·
  [First class callable syntax](https://www.php.net/manual/en/functions.first_class_callable_syntax.php)
- PHP Manual, liên quan:
  [Variable scope](https://www.php.net/manual/en/language.variables.scope.php) ·
  [Type declarations](https://www.php.net/manual/en/language.types.declarations.php) ·
  [Callables](https://www.php.net/manual/en/language.types.callable.php) ·
  [never](https://www.php.net/manual/en/language.types.never.php) ·
  [void](https://www.php.net/manual/en/language.types.void.php) ·
  [Passing by reference](https://www.php.net/manual/en/language.references.pass.php) ·
  [Returning references](https://www.php.net/manual/en/language.references.return.php) ·
  [Closure](https://www.php.net/manual/en/class.closure.php) ·
  [Closure::bindTo](https://www.php.net/manual/en/closure.bindto.php) ·
  [Closure::getCurrent](https://www.php.net/manual/en/closure.getcurrent.php) ·
  [NoDiscard](https://www.php.net/manual/en/class.nodiscard.php)
- RFC:
  [Named Arguments](https://wiki.php.net/rfc/named_params) ·
  [Arrow Functions 2.0](https://wiki.php.net/rfc/arrow_functions_v2) ·
  [First-class callable syntax](https://wiki.php.net/rfc/first_class_callable_syntax) ·
  [New in initializers](https://wiki.php.net/rfc/new_in_initializers) ·
  [Consistent type errors for internal functions](https://wiki.php.net/rfc/consistent_type_errors) ·
  [Arbitrary static variable initializers](https://wiki.php.net/rfc/arbitrary_static_variable_initializers) ·
  [Deprecate implicitly nullable parameter types](https://wiki.php.net/rfc/deprecate-implicitly-nullable-types) ·
  [Closures in constant expressions](https://wiki.php.net/rfc/closures_in_const_expr) ·
  [First class callables in constant expressions](https://wiki.php.net/rfc/fcc_in_const_expr) ·
  [Marking return value as important (#\[\NoDiscard\])](https://wiki.php.net/rfc/marking_return_value_as_important) ·
  [Deprecations for PHP 8.5](https://wiki.php.net/rfc/deprecations_php_8_5)
- php-src: [UPGRADING của PHP 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) (Closure::getCurrent,
  NoDiscard, (void) cast, closure trong constant expression), [UPGRADING của PHP 8.3](https://github.com/php/php-src/blob/PHP-8.3/UPGRADING)
  (giới hạn stack `zend.max_allowed_stack_size`), [UPGRADING của PHP 8.1](https://github.com/php/php-src/blob/PHP-8.1/UPGRADING)
  (giới hạn `$GLOBALS`, null vào hàm có sẵn, biến static trong method kế thừa).
- [Xdebug: xdebug.max_nesting_level](https://xdebug.org/docs/all_settings#max_nesting_level)
- Laravel 13 (mã nguồn):
  [Macroable.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Macroable/Traits/Macroable.php) ·
  [Collections/helpers.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Collections/helpers.php) (`data_get`) ·
  [Foundation/helpers.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/helpers.php) (`abort`) ·
  [HandleExceptions.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Bootstrap/HandleExceptions.php)
