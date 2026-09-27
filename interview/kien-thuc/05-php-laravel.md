# 05. PHP và Laravel · Kiến thức

> [← Plan ôn tập](../05-php-laravel.md) · [Mục lục kiến thức](README.md)
> Bài đọc tổng hợp từ tài liệu gốc ở mục "Đọc" của từng module. Đọc sau khi đã xem plan; tick các
> tiêu chí "Nắm chắc khi" ở file plan.

Trọng tâm là PHP 8.4/8.5 và Laravel 13. Các ví dụ PHP ghi output mong đợi trong comment. Để chạy thử
mà không cần cài PHP vào máy:

```sh
# Chạy một file PHP bằng image chính thức (đổi 8.5 thành 8.4 nếu cần so sánh)
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php example.php
# Mở REPL tương tác
docker run --rm -it php:8.5-cli php -a
```

Tầng database của PHP và Laravel (PDO, N+1, transaction, chunk, read/write connection) nằm ở
[03-database-sql.md, module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel); file này không
lặp lại.

## Mục lục

- Chặng 1: Nền
  - [1.1 Type system và so sánh](#11-type-system-và-so-sánh)
  - [1.2 Array, reference và object handle](#12-array-reference-và-object-handle)
  - [1.3 OOP trong PHP](#13-oop-trong-php)
  - [1.4 Exception và xử lý lỗi](#14-exception-và-xử-lý-lỗi)
  - [1.5 Composer và PSR](#15-composer-và-psr)
  - [1.6 Laravel cơ bản](#16-laravel-cơ-bản)
- Chặng 2: Làm chủ
  - [2.1 PHP hiện đại: 8.0 tới 8.5](#21-php-hiện-đại-80-tới-85)
  - [2.2 PHP-FPM và mô hình share-nothing](#22-php-fpm-và-mô-hình-share-nothing)
  - [2.3 OPcache và deploy](#23-opcache-và-deploy)
  - [2.4 Lõi Laravel: lifecycle, container, provider, facade](#24-lõi-laravel-lifecycle-container-provider-facade)
  - [2.5 Eloquent ở mức làm chủ](#25-eloquent-ở-mức-làm-chủ)
  - [2.6 Queue](#26-queue)
  - [2.7 Các thành phần khác của Laravel](#27-các-thành-phần-khác-của-laravel)
  - [2.8 Chất lượng code PHP: PHPStan, Rector, Pint](#28-chất-lượng-code-php-phpstan-rector-pint)
- Chặng 3: Senior
  - [3.1 Bên trong Zend Engine: zval, refcount, copy-on-write](#31-bên-trong-zend-engine-zval-refcount-copy-on-write)
  - [3.2 Bộ nhớ và garbage collection](#32-bộ-nhớ-và-garbage-collection)
  - [3.3 OPcache chuyên sâu, preloading, JIT](#33-opcache-chuyên-sâu-preloading-jit)
  - [3.4 PHP-FPM ở mức vận hành](#34-php-fpm-ở-mức-vận-hành)
  - [3.5 Process sống lâu: queue worker, Octane, daemon](#35-process-sống-lâu-queue-worker-octane-daemon)
  - [3.6 Hiệu năng và profiling](#36-hiệu-năng-và-profiling)
  - [3.7 Bảo mật đặc thù PHP](#37-bảo-mật-đặc-thù-php)
  - [3.8 So sánh kiến trúc: Laravel, Symfony và ngôn ngữ khác](#38-so-sánh-kiến-trúc-laravel-symfony-và-ngôn-ngữ-khác)

---

## Chặng 1: Nền

### 1.1 Type system và so sánh

Module này trả lời: PHP kiểm tra kiểu ở đâu và lúc nào, `strict_types` thật sự bật cái gì (và
không bật cái gì), và vì sao `==` là nguồn gốc của cả một họ bug bảo mật. Phần lớn nội dung xoay
quanh một thay đổi của PHP 8.0 mà người phỏng vấn gần như chắc chắn hỏi: RFC *Saner string to
number comparisons*.

#### Các kiểu dữ liệu và type declaration

PHP là ngôn ngữ *dynamically typed*: biến không có kiểu, **giá trị** mới có kiểu. `$x = 1;` rồi
`$x = "a";` là hợp lệ. *Type declaration* (khai báo kiểu) là lớp kiểm tra gắn vào ba chỗ: tham số,
giá trị trả về, và property của class. PHP kiểm tra lúc chạy, ở đúng thời điểm giá trị đi qua chỗ
đó; sai kiểu thì ném `TypeError` (một `Error`, không phải `Exception`, xem module 1.4).

```
                 PHP không kiểm tra        PHP kiểm tra
$x = "5";        biến cục bộ                function f(int $x): string
$arr[] = 1.5;    phần tử array              public int $count;
```

Bảng kiểu có thể khai báo, kèm phiên bản xuất hiện:

| Nhóm | Kiểu | Ghi chú |
|---|---|---|
| Scalar | `int`, `float`, `string`, `bool` | Chỉ nhóm này chịu ảnh hưởng của `strict_types` |
| Phức hợp | `array`, `object`, `callable`, `iterable` | `callable` không dùng được cho property |
| Class | `Foo`, `self`, `parent`, `static` | `static` chỉ dùng làm return type (8.0) |
| Đặc biệt | `mixed` (8.0), `void`, `never` (8.1), `null`, `false` (8.0 trong union; đứng riêng từ 8.2), `true` (8.2) | `mixed` đã gồm `null`, nên `?mixed` là lỗi |
| Ghép | `?T`, `A\|B` (8.0), `A&B` (8.1), `(A&B)\|null` (8.2, DNF) | |

- `?T` chỉ là cách viết ngắn của `T|null`, có từ 7.1.
- *Union type* `int|string`: giá trị thuộc một trong các kiểu.
- *Intersection type* `Countable&Traversable`: object phải thoả **mọi** kiểu. Chỉ dùng được với
  class/interface, vì một giá trị không thể vừa là `int` vừa là `string`.
- *DNF type* (Disjunctive Normal Form, "hợp của các giao"): `(A&B)|null`. Luật là giao nằm trong
  ngoặc, hợp nằm ngoài; viết `A&(B|null)` là lỗi cú pháp.
- `never` khác `void`: `void` là "trả về nhưng không có giá trị", `never` là "không bao giờ trả về"
  (luôn `throw` hoặc `exit`). Dùng cho hàm kiểu `abort()`, `redirect()->send(); exit;`.
- PHP bắt lỗi kiểu thừa ngay lúc compile: `int|INT`, `bool|false`, `object|Foo` đều là fatal error.

⚠️ *Implicit nullable*. Viết `function f(Foo $x = null)` thì PHP ngầm cho `$x` nhận `null`, dù
kiểu không có `?`. Từ PHP 8.4 cách viết này báo `Deprecated: Implicitly marking parameter $x as
nullable is deprecated, the explicit nullable type must be used instead`. Lý do bỏ: nó trộn hai
khái niệm "có giá trị mặc định" và "nhận null", và gây lỗi khó hiểu khi class con đổi default.
Sửa bằng `?Foo $x = null` (tương thích từ 7.1, nên sửa hàng loạt được bằng Rector, module 2.8).

#### strict_types: chế độ ép kiểu và chế độ chặt

Mặc định PHP chạy *coercive mode* (chế độ ép kiểu): giá trị scalar sai kiểu được ép sang kiểu khai
báo **nếu phép ép "được định nghĩa rõ"**. Bảng dưới là hàm `function f(int $x): int` nhận các giá
trị khác nhau:

| Giá trị truyền vào | Coercive mode (PHP 8.x) | Strict mode |
|---|---|---|
| `5` | `5` | `5` |
| `"5"` | `5` | `TypeError` |
| `" 5 "` | `5` (từ 8.0 khoảng trắng hai đầu đều hợp lệ) | `TypeError` |
| `"5abc"` | `TypeError` (PHP 7: `5` kèm Notice) | `TypeError` |
| `5.0` | `5` | `TypeError` |
| `5.5` | `5` kèm `Deprecated: Implicit conversion from float 5.5 to int loses precision` (8.1) | `TypeError` |
| `true` | `1` | `TypeError` |
| `null` | `TypeError` (hàm userland không ép null) | `TypeError` |

`declare(strict_types=1);` đặt ở **câu lệnh đầu tiên** của file bật *strict mode*: chỉ nhận đúng
kiểu, không ép. Ngoại lệ duy nhất: `int` được nhận ở chỗ khai báo `float` (*widening*, mở rộng, vì
không mất thông tin).

Quy tắc quan trọng nhất, và hay bị hỏi nhất: strict mode **theo file của lời gọi**, không theo file
khai báo hàm.

```php
<?php
// lib.php: KHÔNG có declare
function twice(int $x): int { return $x * 2; }
```

```php
<?php
declare(strict_types=1);
// app.php: strict
require __DIR__ . '/lib.php';

var_dump(twice(5));      // int(10)
var_dump(twice("5"));    // TypeError: twice(): Argument #1 ($x) must be of type int, string given
var_dump(strlen(123));   // TypeError: hàm built-in cũng bị kiểm tra chặt khi gọi từ file strict
```

Đảo lại (lib strict, app không strict) thì `twice("5")` chạy bình thường. Lý do thiết kế: strict là
lựa chọn của người **viết lời gọi**, "code của tôi cam kết truyền đúng kiểu". Người viết thư viện
không áp được ý mình lên code người dùng.

Ba chỗ không theo quy tắc "file gọi":

1. **Return type** kiểm theo file **khai báo hàm**, vì `return` là code của người viết hàm.
2. **Typed property** kiểm theo file nơi **câu lệnh gán** nằm.
3. ⚠️ **Callback do hàm built-in gọi** (`array_map`, `usort`, `array_filter`...) không chịu ảnh
   hưởng của `strict_types`. Manual ghi: "Function calls from within internal functions will not be
   affected by the strict_types declaration." Lời gọi callback xuất phát từ code C của `array_map`,
   không phải từ file của bạn. Vì vậy trong file strict, `array_map(fn(int $x): int => $x, ['1'])`
   vẫn ép `'1'` thành `1` mà không báo lỗi.

⚠️ Strict mode chỉ định nghĩa cho **scalar type declaration**. Nó không ảnh hưởng `==`, `+`, `if`,
`(int)`, hay array key. `"abc" == 0`, `"5" + 1` trong file strict vẫn chạy theo luật type juggling.

⚠️ Truyền `null` vào tham số scalar non-nullable của **hàm built-in** (`strlen(null)`,
`str_replace('a', 'b', null)`) ở coercive mode từng được âm thầm ép thành `""` hoặc `0`. Từ 8.1 việc
này báo Deprecated, và sẽ thành `TypeError` ở bản major sau. Đây là deprecation gặp nhiều nhất khi
nâng từ 7.4 lên 8.x, thường từ dữ liệu `$_GET` hay cột DB nullable.

Đối chiếu: Java và Go kiểm kiểu lúc compile, sai kiểu thì không build được. PHP kể cả strict vẫn
chỉ phát hiện **lúc chạy**, và chỉ ở những dòng thật sự được chạy. Muốn bắt lỗi kiểu trước khi deploy
phải dùng static analysis (PHPStan, module 2.8).

#### Type juggling và toán tử so sánh

*Type juggling* là việc PHP tự đổi kiểu một giá trị theo *ngữ cảnh* dùng nó. Manual chia ra các ngữ
cảnh: số học (`+ - * /`), chuỗi (`.`, `echo`), logic (`if`, `&&`), bitwise, so sánh, và hàm (type
declaration ở trên). Mỗi ngữ cảnh có luật riêng, nên không có một câu "PHP ép kiểu thế này" chung.

Trước khi xem `==`, cần hai định nghĩa:

- *Numeric string* (chuỗi số): theo manual PHP 8, là chuỗi gồm khoảng trắng tuỳ chọn, dấu `+`/`-`
  tuỳ chọn, một số nguyên hoặc số thực (có thể dạng mũ `1e3`), rồi khoảng trắng tuỳ chọn. Ví dụ
  `"42"`, `" 42"`, `"42 "`, `"-1.5"`, `"1e3"`, `".5"`. Kiểm bằng `is_numeric()`.
- *Leading-numeric string* (chuỗi bắt đầu bằng số): bắt đầu như numeric string rồi có ký tự khác,
  ví dụ `"42abc"`, `"10 Small Pigs"`. **Không** phải numeric string.

⚠️ PHP 7 coi `"42 "` (khoảng trắng cuối) là leading-numeric, còn `" 42"` là numeric. RFC *Saner
numeric strings* (8.0) sửa cho hai đầu như nhau. Vì vậy `is_numeric("42 ")` là `false` ở PHP 7,
`true` ở PHP 8.

Ngữ cảnh số học ở PHP 8:

```php
<?php
declare(strict_types=1);

var_dump(1 + "10.5");      // float(11.5)
var_dump(1 + "10 pigs");   // int(11) kèm Warning: A non-numeric value encountered (PHP 7: Notice)
var_dump((int) "10 pigs"); // int(10), cast tường minh không báo gì
var_dump((int) "pigs");    // int(0), cast tường minh không báo gì
var_dump(1 + "pigs");      // TypeError từ 8.0 (PHP 7: int(1) kèm Warning)
```

Hai toán tử so sánh bằng:

- `===` (*identical*): cùng kiểu **và** cùng giá trị. Không đổi kiểu gì. Với array: cùng cặp
  key/value, **cùng thứ tự**, cùng kiểu từng phần tử. Với object: cùng một instance.
- `==` (*equal*): đổi hai bên về kiểu chung theo bảng luật, rồi mới so. Với array: cùng cặp
  key/value, không cần cùng thứ tự, phần tử so bằng `==`. Với object: cùng class và các property
  bằng nhau theo `==`.

Luật của `==` theo manual (xét **theo thứ tự**, gặp dòng nào khớp trước thì dùng dòng đó):

| Vế 1 | Vế 2 | Cách so |
|---|---|---|
| `null` hoặc string | string | Đổi `null` thành `""`, rồi so chuỗi (hai numeric string thì so như số) |
| `bool` hoặc `null` | bất kỳ | Đổi **cả hai** về bool |
| object | object | Cùng class thì so từng property; khác class là không so được |
| string/int/float | string/int/float | So số (từ PHP 8: chỉ khi chuỗi là numeric string, xem RFC bên dưới) |
| array | array | Ít phần tử hơn thì nhỏ hơn; so theo từng key |
| array | bất kỳ khác | Array luôn lớn hơn, nên không bao giờ `==` |

**RFC Saner string to number comparisons (PHP 8.0, tác giả Nikita Popov).** Trước 8.0, so số với
chuỗi bất kỳ bằng `==` thì PHP ép chuỗi thành số rồi so số. `"foobar"` ép thành `0`, nên
`0 == "foobar"` là `true`. RFC gọi đây là nguồn bug lớn nhất của so sánh lỏng, nhất là khi phép so
bị ẩn trong `in_array()` hay `switch`. Luật mới cho `$number == $string`:

1. Nếu `$string` là numeric string: so như số, **giống hệt PHP 7**.
2. Nếu không: đổi `$number` thành chuỗi (`0` thành `"0"`), rồi so hai chuỗi.

Cách nhớ của RFC: "coi như ép số thành chuỗi rồi so lỏng hai chuỗi". Luật mới áp cho mọi phép so
lỏng: `==`, `!=`, `<`, `>`, `<=`, `>=`, `<=>`, `in_array`/`array_search`/`array_keys` không strict,
`switch`, và `sort`/`asort`... với `SORT_REGULAR` (mặc định).

Bảng tổng hợp `==` (PHP 7.4 so với PHP 8.x). Các dòng đánh dấu ★ là dòng đổi kết quả:

| Nhóm | Biểu thức | PHP 7.4 | PHP 8.x | Luật áp dụng |
|---|---|---|---|---|
| Chuỗi số với số | `42 == "42"` | `true` | `true` | Numeric string, so số |
| | `42 == "42.0"` | `true` | `true` | So số: 42 = 42.0 |
| | `100 == "1e2"` | `true` | `true` | `"1e2"` là 100 |
| | `42 == " 42"` | `true` | `true` | Khoảng trắng đầu hợp lệ ở cả hai bản |
| | `42 == "42 "` | `true` | `true` | PHP 7: leading-numeric, vẫn ép ra 42. PHP 8: numeric string |
| | `"1" == "01"` | `true` | `true` | Hai numeric string so như số |
| | `"10" == "1e1"` | `true` | `true` | Như trên |
| | `"0e1" == "0e99"` | `true` | `true` | Hai chuỗi đều là 0 × 10ⁿ = 0 (bẫy "magic hash" bên dưới) |
| Chuỗi không phải số với số | ★ `0 == "a"` | `true` | `false` | PHP 8: `"0"` so với `"a"` |
| | ★ `0 == ""` | `true` | `false` | PHP 8: `"0"` so với `""` |
| | ★ `42 == "42abc"` | `true` | `false` | Leading-numeric không còn được coi là số khi so |
| | `42 == "abc42"` | `false` | `false` | PHP 7 ép `"abc42"` ra 0 |
| | `"1" == "1abc"` | `false` | `false` | Chuỗi với chuỗi: một bên không numeric thì so như chuỗi |
| | ★ `INF == "INF"` | `false` | `true` | PHP 8: `(string) INF` là `"INF"` |
| null | `null == false` | `true` | `true` | Đổi về bool |
| | `null == 0` | `true` | `true` | Dòng "null với bất kỳ": đổi về bool, `false == false` |
| | `null == ""` | `true` | `true` | Dòng "null với string": `null` thành `""` |
| | `null == "0"` | `false` | `false` | `""` so với `"0"` như chuỗi |
| | `null == []` | `true` | `true` | Đổi về bool |
| bool | `true == "php"` | `true` | `true` | Chuỗi khác rỗng, khác `"0"` là `true` |
| | `false == "0"` | `true` | `true` | `"0"` là falsy |
| | `false == "0.0"` | `false` | `false` | `"0.0"` là **truthy** |
| | `true == -1` | `true` | `true` | Mọi số khác 0 là `true` |
| array | `[] == false` | `true` | `true` | Array rỗng là falsy |
| | `[] == 0` | `false` | `false` | Array luôn lớn hơn giá trị không phải array, bool, null |
| | `[1, 2] == [1 => 2, 0 => 1]` | `true` | `true` | `==` không quan tâm thứ tự key (`===` thì `false`) |
| | `["1"] == [1]` | `true` | `true` | Phần tử so bằng `==` |
| | ★ `[0] == ["a"]` | `true` | `false` | Phần tử `0 == "a"` theo luật mới |

Để đọc bảng: dòng nào có một vế bool hoặc null thì **mọi thứ đổi về bool**, và RFC không đụng tới
những dòng đó. RFC chỉ đổi đúng một ô: số so với chuỗi không phải numeric string.

Danh sách giá trị falsy (đổi sang bool ra `false`) cần thuộc: `false`, `0`, `-0`, `0.0`, `-0.0`,
`""`, `"0"`, `[]`, `null`, và object nội bộ tự định nghĩa cách ép sang bool (manual lấy ví dụ
object GMP mang giá trị 0). Mọi thứ khác là truthy, kể cả `"0.0"`, `" "`, `"false"`, `[0]`, và
object thông thường. ⚠️ Từ PHP 8.5, so lỏng một object không so được (enum, `CurlHandle`...) với
bool luôn theo `(bool) $object` (với các object này là `true`); trước 8.5 chỉ đúng khi so với
literal `true`/`false`, còn so với một biến bool thì luôn ra `false`.

⚠️ *Magic hash*. Hai chuỗi hex dạng `"0e"` + toàn chữ số là numeric string có giá trị 0, nên bằng
nhau theo `==`. Ví dụ nổi tiếng: `md5('240610708')` và `md5('QNKCDZO')` đều ra chuỗi `0e` + 30 chữ
số. Code kiểm tra token hay mật khẩu bằng `md5($input) == $storedHash` bị qua mặt, **kể cả ở PHP 8**
vì hai vế đều là numeric string. Cách đúng:

```php
<?php
declare(strict_types=1);

$known = hash_hmac('sha256', $payload, $secret);
if (hash_equals($known, $userToken)) { /* hợp lệ */ }   // so chính xác, thời gian hằng
if (password_verify($plain, $hashFromDb)) { /* đúng mật khẩu */ }
```

`hash_equals` vừa so chính xác từng byte vừa chạy trong thời gian không phụ thuộc vị trí byte sai
đầu tiên, chống *timing attack* (đoán dần token bằng cách đo thời gian phản hồi). `===` so đúng
nhưng dừng ở byte sai đầu tiên.

⚠️ Đừng so float bằng `==`/`===`: `0.1 + 0.2 === 0.3` là `false`. So bằng sai số
(`abs($a - $b) < 1e-9`) hoặc dùng bcmath cho tiền.

Đối chiếu: JavaScript cũng có `==` lỏng và `===` chặt, với bẫy tương tự (`0 == ""` là `true` trong
JS, trong PHP 8 là `false`). Java không có so sánh lỏng giữa kiểu khác nhau; bẫy của Java là `==`
so reference của object (`new String("a") == new String("a")` là `false`), phải dùng `equals()`.
Go không cho so hai kiểu khác nhau, lỗi ngay lúc compile.

#### Hàm và cấu trúc so lỏng ngầm

Nhiều chỗ trong PHP dùng `==` mà code không hề viết `==`:

| Cấu trúc | So bằng | Bật chặt |
|---|---|---|
| `in_array($v, $arr)` | `==` | `in_array($v, $arr, true)` |
| `array_search($v, $arr)` | `==` | Tham số thứ ba `true` |
| `array_keys($arr, $v)` | `==` | Tham số thứ ba `true` |
| `switch` | `==` | Không có; dùng `match` |
| `sort`, `max`, `min` với kiểu lẫn lộn | So lỏng `<=>` | Dùng cờ `SORT_STRING`/`SORT_NUMERIC` hoặc chuẩn hoá kiểu trước |
| `array_unique` | So chuỗi (`SORT_STRING` mặc định): `1` và `"1"` bị coi là trùng | |

```php
<?php
declare(strict_types=1);

var_dump(in_array('abc', [0]));          // PHP 7: bool(true), PHP 8: bool(false)
var_dump(in_array(0, ['a', 'b']));       // PHP 7: bool(true), PHP 8: bool(false)
var_dump(in_array('1e1', ['10']));       // bool(true) ở cả hai: hai numeric string so như số
var_dump(in_array(null, [0]));           // bool(true) ở cả hai: null so với int đổi về bool
var_dump(in_array('1e1', ['10'], true)); // bool(false)
var_dump(array_search('1', [0, 1]));     // int(1), nhưng nếu không tìm thấy thì trả false
```

⚠️ `array_search` trả `false` khi không thấy và `0` khi thấy ở index 0. `if (!array_search(...))`
nhầm hai trường hợp; luôn so `=== false`.

Ví dụ bug kiểm tra quyền: `in_array($request->input('role_id'), $allowedIds)` với `$allowedIds =
[1, 2]` và input `"1 OR 1=1"`. PHP 7 ép chuỗi thành 1 và cho qua; PHP 8 không cho qua, nhưng input
`"1.0"` hay `" 1"` vẫn qua ở cả hai bản. Truyền `true` và ép kiểu input tường minh là cách duy nhất
chắc chắn.

`switch` so bằng `==`, nên đoạn sau in `"0"` ở PHP 7 và `"a"` ở PHP 8 (ví dụ trong manual):

```php
<?php
declare(strict_types=1);   // không đổi gì: strict không áp cho switch

switch ("a") {
    case 0:   echo "0"; break;   // PHP 7 khớp ở đây vì "a" == 0
    case "a": echo "a"; break;   // PHP 8 khớp ở đây
}
```

`match` (8.0) sinh ra để thay `switch` trong phần lớn trường hợp:

```php
<?php
declare(strict_types=1);

enum Status: string { case Paid = 'paid'; case Pending = 'pending'; case Void = 'void'; }

function label(Status $s): string
{
    return match ($s) {
        Status::Paid              => 'Đã thanh toán',
        Status::Pending           => 'Chờ',
        Status::Void              => 'Huỷ',
    };
}

$code = 404;
$kind = match (true) {                    // match(true): mỗi nhánh là một điều kiện
    $code >= 500 => 'server',
    $code >= 400 => 'client',
    default      => 'ok',
};
echo $kind;                               // client

echo match ("1") { 1 => 'int', "1" => 'string' };  // string, vì match so bằng ===
```

| | `switch` | `match` |
|---|---|---|
| So bằng | `==` | `===` |
| Là | Câu lệnh | Biểu thức, trả về giá trị |
| `break` | Bắt buộc, quên là rơi xuống nhánh sau (*fallthrough*) | Không có, mỗi nhánh một biểu thức |
| Không khớp nhánh nào | Lặng lẽ bỏ qua | Ném `UnhandledMatchError` |
| Nhiều giá trị một nhánh | Nhiều `case` liền nhau | `1, 2, 3 => ...` |
| Thân nhánh | Nhiều câu lệnh | Một biểu thức (cần nhiều bước thì gọi hàm, hoặc `throw`) |

⚠️ `match` không `default` gặp giá trị lạ sẽ ném lỗi lúc chạy. Đây là ưu điểm (fail sớm thay vì
chạy sai), nhưng cần biết để không bất ngờ trên production. Với enum, PHPStan cảnh báo được khi
`match` thiếu case.

**Tóm tắt nhanh**
- `strict_types` theo file của lời gọi (return type theo file khai báo), chỉ áp cho scalar type
  declaration; không ảnh hưởng `==`, số học, hay callback do hàm built-in gọi.
- PHP 8 chỉ đổi đúng một luật: số so với chuỗi **không phải** numeric string thì đổi số thành chuỗi.
  `0 == "a"` thành `false`. Hai numeric string (`"1e1" == "10"`, `"0e1" == "0e2"`) vẫn so như số.
- Có vế bool hoặc null thì mọi thứ đổi về bool: `null == 0`, `[] == false` vẫn `true` ở PHP 8.
- `in_array`, `array_search`, `switch` so lỏng ngầm; truyền `true`, dùng `match`.
- So token/hash bằng `hash_equals`, mật khẩu bằng `password_verify`, không bao giờ bằng `==`.

**Nguồn**: [PHP: Type declarations](https://www.php.net/manual/en/language.types.declarations.php) ·
[PHP: Type Juggling](https://www.php.net/manual/en/language.types.type-juggling.php) ·
[PHP: Numeric strings](https://www.php.net/manual/en/language.types.numeric-strings.php) ·
[PHP: Comparison operators](https://www.php.net/manual/en/language.operators.comparison.php) ·
[PHP: Type comparison tables](https://www.php.net/manual/en/types.comparisons.php) ·
[PHP: match](https://www.php.net/manual/en/control-structures.match.php) ·
[RFC: Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison) ·
[RFC: Saner numeric strings](https://wiki.php.net/rfc/saner-numeric-strings) ·
[RFC: Deprecate implicitly nullable parameter types](https://wiki.php.net/rfc/deprecate-implicitly-nullable-types) ·
[RFC: Deprecate implicit non-integer-compatible float to int conversions](https://wiki.php.net/rfc/implicit-float-int-deprecate) ·
[PHP 8.0 UPGRADING](https://github.com/php/php-src/blob/PHP-8.0/UPGRADING)


---

### 1.2 Array, reference và object handle

Module này trả lời: array của PHP thực chất là cấu trúc gì, khi gán hay truyền vào hàm thì cái gì
được copy (array, object, reference khác nhau ra sao), và vì sao `&` thường làm code chậm hơn và
dễ bug hơn. Đây là tầng trên cùng của chuỗi câu hỏi "array copy thế nào, copy-on-write, refcount"
mà module 3.1 đào tiếp.

#### Array là hash table có thứ tự

*Hash table* là cấu trúc lưu cặp key → value: băm key ra một số, dùng số đó tìm ô chứa, nên tra
theo key trung bình O(1). Hash table thông thường không giữ thứ tự. Array của PHP là *ordered hash
table*: các phần tử nằm trong một mảng liên tục theo **thứ tự chèn**, còn phần hash chỉ là bảng chỉ
mục trỏ vào mảng đó. Vì vậy cùng một kiểu `array` đóng được mọi vai: list, map, set (dùng key),
stack (`array_push`/`array_pop`), queue (`array_shift`, nhưng O(n)).

```
Hash array ['b' => 20, 'a' => 10]          Packed array [10, 20, 30]

arHash (chỉ mục)     arData (theo thứ tự chèn)  arData (chỉ có value, không có hash)
 h("a") ─────┐        [0] key "b" h val 20       [0] 10
 h("b") ──┐  └──────► [1] key "a" h val 10       [1] 20
          └─────────► [0]                        [2] 30
                                                 $a[1] = tính thẳng vị trí 1
```

*Packed array*: khi key là số nguyên tăng dần (thường là 0..n-1 do `$a[] = ...`), PHP bỏ hẳn phần
hash và key, tra `$a[$i]` bằng cách tính thẳng vị trí. Từ PHP 8.2, mỗi phần tử packed chỉ là một
*zval* (ô giá trị 16 byte gồm value và thông tin kiểu) thay vì một *bucket* 32 byte, nên list tốn
khoảng một nửa bộ nhớ so với 8.1. Chèn key lung tung (`[1 => 'a', 0 => 'b']`) hoặc thêm key chuỗi
thì array chuyển sang dạng hash, và thường ở luôn dạng đó cho tới khi bạn tạo array mới (ví dụ
bằng `array_values`).

⚠️ Key bị ép kiểu khi ghi. Key chỉ có thể là `int` hoặc `string`:

| Key viết | Key thật | Ghi chú |
|---|---|---|
| `"8"`, `"-5"` | `8`, `-5` | Chuỗi là số nguyên thập phân dạng chuẩn thì thành int |
| `"08"`, `"+8"`, `"8 "`, `"1.5"` | giữ nguyên chuỗi | Không phải dạng chuẩn. Luật này khác luật numeric string của `==` |
| `1.7` | `1` | Cắt phần thập phân; từ 8.1 báo Deprecated khi mất phần lẻ |
| `true`, `false` | `1`, `0` | |
| `null` | `""` | |
| array, object | `TypeError` | Từ PHP 8.0 (trước đó là Warning "Illegal offset type") |

```php
<?php
declare(strict_types=1);

$a = ['1' => 'a', 1 => 'b', true => 'c'];
var_dump($a);            // array(1) { [1]=> string(1) "c" }
var_dump(['01' => 'x']); // array(1) { ["01"]=> string(1) "x" }

$b = [];
$b[-5] = 'x';
$b[] = 'y';
var_dump(array_keys($b)); // PHP 8.3+: [-5, -4]. PHP 8.2 trở về trước: [-5, 0]
```

⚠️ Hệ quả thực tế của ép key: dùng ID dạng chuỗi số làm key (`$byId[$row['id']]`) thì key thành
int; `array_keys()` trả int, và `in_array($id, array_keys($byId), true)` với `$id` là chuỗi sẽ
`false`. Tương tự, `json_decode('{"10": "a"}', true)` cho array có key int `10`.

#### Gộp và kiểm tra array

| Cách gộp | Key số | Key chuỗi trùng |
|---|---|---|
| `array_merge($a, $b)` | Đánh số lại từ 0 | Bên phải (`$b`) thắng |
| `[...$a, ...$b]` (spread; key chuỗi được phép từ 8.1) | Đánh số lại | Bên phải thắng, giống `array_merge` |
| `$a + $b` (*union*) | Giữ nguyên | Bên **trái** thắng; key đã có ở `$a` thì bỏ phần tử của `$b` |
| `array_replace($a, $b)` | Giữ nguyên | Bên phải thắng |

```php
<?php
declare(strict_types=1);

var_dump(array_merge([5 => 'x'], [5 => 'y']));   // [0 => 'x', 1 => 'y']
var_dump([5 => 'x'] + [5 => 'y']);               // [5 => 'x']
var_dump(array_replace([5 => 'x'], [5 => 'y'])); // [5 => 'y']

// Cách dùng đúng của +: điền giá trị mặc định mà không ghi đè thứ người dùng truyền
$options = ['timeout' => 5] + ['timeout' => 30, 'retry' => 3];  // ['timeout' => 5, 'retry' => 3]
```

⚠️ `array_merge` với key số là ID (`[1001 => $userA]`) sẽ làm mất ID vì bị đánh số lại. Muốn giữ
key thì dùng `+` hoặc `array_replace`.

`array_is_list($a)` (8.1): `true` khi key đúng là 0, 1, 2... liên tục theo thứ tự. Đây cũng chính
là điều kiện để `json_encode` xuất ra JSON array `[...]`; không phải list thì ra JSON object `{...}`.

```php
<?php
declare(strict_types=1);

$ids = array_filter([1, 2, 3, 4], fn(int $x): bool => $x % 2 === 0);
var_dump($ids);                            // [1 => 2, 3 => 4]: array_filter GIỮ key
echo json_encode($ids), PHP_EOL;           // {"1":2,"3":4}  <- client nhận object, không phải array
echo json_encode(array_values($ids)), PHP_EOL; // [2,4]
```

Đây là bug API rất hay gặp: sau `array_filter`, `unset($a[$i])`, hay `array_unique`, key có lỗ
hổng và JSON đổi hình dạng. Laravel Collection cũng vậy: `->filter()` giữ key, cần `->values()`
trước khi trả JSON.

Kiểm tra key: `isset($a['k'])` trả `false` nếu giá trị là `null`; `array_key_exists('k', $a)` trả
`true` miễn là key có mặt. `$a['k'] ?? 'mặc định'` hành xử như `isset`.

#### Gán giá trị: array copy, object là handle

PHP có ba kiểu "chia sẻ" khác nhau, và phần lớn nhầm lẫn đến từ việc gộp chúng làm một:

```
Array (giá trị, copy-on-write)   Object (handle)             Reference (&)
$a ─┐                            $a ─┐                        $a ─┐
    ├─► [1,2,3] refcount=2           ├─► handle #7 ─► object      ├─► [ô chứa] ─► giá trị
$b ─┘   ghi vào $b thì tách      $b ─┘   (mỗi biến 1 bản         $b ─┘   hai tên, MỘT ô chứa
        ra bản riêng                     copy của handle)
```

*Array được gán theo giá trị*: về ngữ nghĩa `$b = $a` tạo một bản độc lập. Về cài đặt, PHP dùng
*copy-on-write* (COW): `$b = $a` chỉ tăng *refcount* (bộ đếm số nơi đang dùng chung giá trị) lên 2;
lần đầu tiên có bên **ghi** vào, PHP mới copy thật ("tách", *separation*). Vì vậy gán hoặc truyền
array lớn vào hàm gần như miễn phí nếu bên nhận chỉ đọc.

```php
<?php
declare(strict_types=1);

$a = range(1, 100_000);
$m0 = memory_get_usage();

$b = $a;                        // chỉ tăng refcount, chưa copy
$m1 = memory_get_usage();

$b[0] = -1;                     // ghi lần đầu: copy toàn bộ array cho $b
$m2 = memory_get_usage();

// Output bên dưới là minh hoạ, không phải chạy thật
echo $m1 - $m0, PHP_EOL;        // 0
echo $m2 - $m1, PHP_EOL;        // khoảng 2 MB trên PHP 8.2+ 64-bit (con số chính xác tuỳ phiên bản)
echo $a[0], ' ', $b[0], PHP_EOL; // 1 -1

function total(array $items): int
{
    return array_sum($items);   // chỉ đọc: không copy, dù array có triệu phần tử
}
function withTax(array $items): array
{
    $items[] = 10;              // ghi vào tham số: lúc này mới copy, bản của caller không đổi
    return $items;
}
```

*Object thì khác*. Biến không chứa object; nó chứa một *object handle* (manual gọi là *object
identifier*), một mã số để engine tìm tới object thật nằm ở chỗ khác. `$b = $a` copy **cái handle**,
nên cả hai biến trỏ cùng một object; sửa property qua `$b` thì `$a` thấy. `var_dump` in số handle
sau dấu `#`.

```php
<?php
declare(strict_types=1);

final class Cart { public array $items = []; }

function addItem(Cart $c): void { $c->items[] = 'book'; }   // sửa object: caller thấy
function replace(Cart $c): void { $c = new Cart(); $c->items[] = 'pen'; } // đổi handle cục bộ: caller không thấy
function replaceRef(Cart &$c): void { $c = new Cart(); }    // reference: đổi luôn biến của caller

$cart = new Cart();
$alias = $cart;
addItem($cart);
replace($cart);
var_dump($cart->items);                 // ["book"]
var_dump($alias === $cart);             // bool(true): cùng một instance
var_dump(spl_object_id($alias) === spl_object_id($cart)); // bool(true)

replaceRef($cart);
var_dump($cart->items, $alias->items);  // [] và ["book"]: $cart giờ là object mới, $alias giữ object cũ
```

Vì vậy câu "object trong PHP được truyền by reference" là **sai**, và manual có hẳn một trang để
đính chính: object được truyền **by value**, chỉ có điều giá trị đó là một handle. Khác biệt lộ ra ở
hàm `replace()`: nếu thật là reference thì gán `new Cart()` phải đổi biến của caller. Đối chiếu Java:
giống hệt, Java cũng "pass reference by value"; hàm Java gán lại tham số không đổi biến bên ngoài.
Đối chiếu Go: struct được copy khi gán, muốn chia sẻ phải dùng pointer `*Cart`; handle của PHP gần
với pointer của Go hơn là với struct.

So sánh object: `===` là "cùng một instance"; `==` là "cùng class và mọi property bằng nhau theo
`==`" (so đệ quy, nên object lớn so `==` tốn thời gian).

*Clone*: `clone $obj` tạo object mới và copy từng property kiểu *shallow copy* (copy nông):
property scalar hay array được copy (theo COW), property là object thì chỉ copy handle, nên object
con vẫn dùng chung. Sau khi copy xong, PHP gọi `__clone()` trên bản mới để bạn tự "clone sâu" những
gì cần tách.

```php
<?php
declare(strict_types=1);

final class Money { public function __construct(public int $amount) {} }

final class Order
{
    public array $lines = [];
    public function __construct(public Money $total) {}

    public function __clone(): void
    {
        $this->total = clone $this->total;   // tách Money, nếu không hai Order dùng chung
    }
}

$o1 = new Order(new Money(100));
$o2 = clone $o1;
$o2->total->amount = 999;
$o2->lines[] = 'x';                          // array: tự tách nhờ COW, không cần __clone
echo $o1->total->amount, ' ', count($o1->lines), PHP_EOL;  // 100 0
```

- Property `readonly` được gán lại bên trong `__clone()` từ PHP 8.3.
- PHP 8.5 có `clone($obj, ['prop' => $value])`: ghi đè property trên bản copy (chạy sau
  `__clone()`; được cả property `readonly` khi gọi từ scope có quyền ghi, ví dụ bên trong class),
  rất tiện cho method `withX()` của object bất biến.
- ⚠️ Property là **reference** thì sau clone vẫn là reference (manual: "Any properties that are
  references to other variables will remain references").

#### Reference `&`

*Reference* là hai (hay nhiều) tên cùng trỏ vào **một ô chứa**. Manual nhấn mạnh: `$a =& $b` không
phải "`$a` trỏ tới `$b`", mà cả hai ngang hàng cùng trỏ một chỗ. Reference cũng không phải pointer:
không có số học con trỏ, không có "reference tới reference". Có ba thao tác:

- Gán: `$b = &$a;`
- Truyền: `function inc(int &$n): void { $n++; }` (hàm built-in như `sort`, `preg_match`,
  `array_push` dùng kiểu này).
- Trả về: `function &getRef(): array` (hiếm dùng).

⚠️ Tham số by-reference mà caller truyền biến chưa tồn tại thì PHP tự tạo biến đó với giá trị
`null`, không báo lỗi. Ví dụ `preg_match($re, $s, $m)` tạo `$m`; `foo($arr['k'])` tạo key `'k'`.

⚠️ Cạm bẫy kinh điển: `foreach` by reference rồi dùng lại tên biến.

```php
<?php
declare(strict_types=1);

$a = [1, 2, 3];
foreach ($a as &$v) {}     // xong vòng này, $v vẫn là reference tới $a[2]
foreach ($a as $v) {}      // mỗi vòng GÁN vào $v, tức là ghi vào $a[2]
var_dump($a);              // [1, 2, 2]
```

Theo dõi từng bước của vòng thứ hai (`$v` và `$a[2]` là một ô chứa):

| Vòng | Lệnh ngầm | `$a` sau vòng |
|---|---|---|
| Bắt đầu | | `[1, 2, 3]` |
| 1 | `$v = $a[0]`, tức ghi 1 vào `$a[2]` | `[1, 2, 1]` |
| 2 | `$v = $a[1]`, ghi 2 vào `$a[2]` | `[1, 2, 2]` |
| 3 | `$v = $a[2]`, gán `$a[2]` cho chính nó | `[1, 2, 2]` |

Kết quả luôn là phần tử cuối bị thay bằng phần tử kế cuối. `var_dump($a)` ngay sau vòng thứ nhất in
phần tử cuối là `&int(3)`: dấu `&` cho biết phần tử đó đang nằm trong một *reference set*. Cách sửa:

1. `unset($v);` ngay sau mọi `foreach` by reference. `unset` chỉ xoá **tên** `$v`, cắt liên kết,
   không xoá `$a[2]`.
2. Tốt hơn: tránh `foreach` by reference. Viết `foreach ($a as $k => $v) { $a[$k] = $v * 2; }`
   hoặc `$a = array_map(fn(int $v): int => $v * 2, $a);`.

Một hành vi `foreach` nữa cần biết (từ PHP 7): `foreach` **by value** duyệt trên bản của array tại
lúc bắt đầu vòng lặp, nên thêm/xoá phần tử của `$a` bên trong vòng không đổi số vòng. `foreach` by
reference thì duyệt trực tiếp array thật, phần tử thêm vào cuối trong lúc duyệt sẽ được duyệt tới.

⚠️ Reference sống sót bên trong array. Manual gọi đây là "potentially dangerous": gán array bình
thường (không `&`) nhưng nếu một **phần tử** đang là reference thì phần tử đó vẫn dùng chung giữa bản
gốc và bản copy.

```php
<?php
declare(strict_types=1);

$arr = [1];
$x = &$arr[0];      // $arr[0] giờ nằm trong một reference set
$copy = $arr;       // copy array bình thường
$copy[0]++;         // tưởng chỉ sửa bản copy
var_dump($arr[0]);  // int(2): bản gốc cũng đổi!
```

Bẫy này xuất hiện ngầm sau một `foreach ($arr as &$v)` quên `unset`, hay khi truyền array đó vào
hàm by value rồi hàm sửa phần tử.

⚠️ Reference không phải công cụ tối ưu. Truyền `array &$big` để "khỏi copy" là hiểu sai: nhờ COW,
truyền by value vốn đã không copy nếu hàm chỉ đọc. Ngược lại, trộn biến reference với biến thường
trỏ cùng array buộc engine phải tách copy sớm hơn (chi tiết cơ chế ở module 3.1), nên `&` thường làm
**chậm hơn**, và luôn làm code khó lần theo hơn. Dùng `&` khi thật sự cần hàm sửa biến của caller,
và ưu tiên trả về giá trị mới.

Object không cần `&` để sửa nội dung, vì handle đã trỏ cùng object. `&` với object chỉ cần khi muốn
hàm **thay** object khác vào biến của caller, như `replaceRef()` ở trên.

#### Chi phí bộ nhớ

Mỗi phần tử array PHP mang theo nhiều hơn chỉ giá trị:

| Loại | Chi phí mỗi phần tử (64-bit) | Nguồn |
|---|---|---|
| Hash array (PHP 7+) | khoảng 36 byte: bucket 32 byte (zval 16, hash 8, con trỏ key 8) + 4 byte chỉ mục | Nikita Popov, "PHP's new hashtable implementation" |
| Packed array PHP 7.0 đến 8.1 | khoảng 32 byte (vẫn dùng bucket, bỏ phần hash) | Như trên |
| Packed array PHP 8.2+ | 16 byte (chỉ zval) | `zend_types.h` của 8.2 có thêm `arPacked` |
| Mảng `int` của C/Java/Go | 4 hoặc 8 byte | |

Cộng thêm: dung lượng được cấp theo lũy thừa của 2 (array 100 001 phần tử được cấp chỗ cho 131 072),
và giá trị là chuỗi thì mỗi chuỗi là một khối riêng (khoảng 24 byte header cộng độ dài). Một array
triệu dòng kết quả query, mỗi dòng lại là một array con có key chuỗi, dễ dàng chiếm vài trăm MB và
chạm `memory_limit`.

Cách xử lý dữ liệu lớn, theo thứ tự nên nghĩ tới:

1. Đừng nạp hết vào RAM: xử lý theo lô (`chunkById` của Laravel, xem 03-database-sql module 2.7),
   hoặc stream bằng unbuffered query.
2. *Generator*: hàm dùng `yield` trả từng phần tử khi được hỏi, bộ nhớ chỉ giữ phần tử hiện tại
   (module 2.1).

   ```php
   <?php
   declare(strict_types=1);

   /** @return Generator<int, string> */
   function readLines(string $path): Generator
   {
       $fh = fopen($path, 'rb');
       try {
           while (($line = fgets($fh)) !== false) {
               yield rtrim($line, "\n");
           }
       } finally {
           fclose($fh);
       }
   }
   foreach (readLines('/var/log/app.log') as $line) { /* RAM không đổi theo kích thước file */ }
   ```
3. Object có property khai báo sẵn thay cho array key chuỗi: property khai báo nằm ở các ô cố định
   trong object, không cần bảng hash riêng, nên DTO nhỏ gọn hơn array liên kết cùng nội dung.
4. `SplFixedArray`: kích thước cố định, key chỉ là số. Từ 8.2 packed array đã chỉ tốn 16 byte mỗi
   phần tử nên lợi thế còn lại chủ yếu là không bị cấp dư theo lũy thừa của 2.

Đo thay vì đoán: `memory_get_usage()` (bộ nhớ đang dùng), `memory_get_peak_usage()` (đỉnh), và
profiler (module 3.6).

**Tóm tắt nhanh**
- Array là ordered hash table; list 0..n được lưu dạng packed. Key `"8"` thành `8`, `"08"` giữ
  chuỗi, `true` thành `1`, `null` thành `""`.
- `array_merge` đánh số lại key số, `+` giữ key và bên trái thắng. `array_filter` giữ key, nên
  `json_encode` ra object; gọi `array_values`.
- Array gán theo giá trị với copy-on-write: gán/truyền miễn phí, ghi mới copy. Object gán copy
  handle: cùng instance, nhưng không phải reference.
- `foreach` by reference phải `unset($v)` sau vòng lặp; nếu không, vòng `foreach` sau ghi đè phần
  tử cuối.
- `&` không phải tối ưu hiệu năng; nó thường chậm hơn và để lại reference ẩn trong array.

**Nguồn**: [PHP: Arrays](https://www.php.net/manual/en/language.types.array.php) ·
[PHP: References Explained](https://www.php.net/manual/en/language.references.php) ·
[PHP: What References Do](https://www.php.net/manual/en/language.references.whatdo.php) ·
[PHP: foreach](https://www.php.net/manual/en/control-structures.foreach.php) ·
[PHP: Objects and references](https://www.php.net/manual/en/language.oop5.references.php) ·
[PHP: Object Cloning](https://www.php.net/manual/en/language.oop5.cloning.php) ·
[Nikita Popov: PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html) ·
[php-src 8.2: zend_types.h](https://github.com/php/php-src/blob/PHP-8.2.0/Zend/zend_types.h)


---

### 1.3 OOP trong PHP

Module này trả lời: PHP có những công cụ OOP nào mà Java/Go không có hoặc làm khác (trait,
`static::`, magic method, closure bind được `$this`), và Laravel dùng chúng thế nào để có những cú
pháp trông như "phép thuật" như `User::where(...)` hay `$user->name`.

#### Interface, abstract class, trait

| | Interface | Abstract class | Trait |
|---|---|---|---|
| Là gì | Hợp đồng: method (và từ 8.4 là property) phải có | Class dở dang, không `new` được | Khối code được chép vào class dùng nó |
| Có state (property có giá trị) | Không; có hằng. 8.4 khai báo được property nhưng chỉ là yêu cầu, class phải tự cài | Có | Có |
| Method có thân | Không | Có, trộn với `abstract` method | Có, cả `abstract` method |
| Constructor | Không nên (khai báo được nhưng hiếm khi đúng) | Có | Có thể có, nhưng hiếm khi nên |
| Là một type (`instanceof`, type hint) | Có | Có | **Không** |
| Một class dùng mấy cái | Nhiều (`implements A, B`) | Một (kế thừa đơn) | Nhiều (`use A, B`) |
| Dùng khi | Định nghĩa "làm được gì" cho nhiều class không liên quan | Chia sẻ khung xử lý chung cho một họ class (template method) | Chia sẻ đoạn code cài đặt mà không tạo quan hệ kiểu |

*Interface* định nghĩa hợp đồng. Một interface `extends` được nhiều interface khác. Enum cũng
`implements` được interface. Từ PHP 8.4 interface khai báo được property kèm yêu cầu đọc/ghi
(`public string $name { get; }`), class thoả mãn bằng property thường, property `readonly` hoặc
*property hook* (module 2.1).

*Abstract class* dùng khi các class con chia sẻ cả code lẫn state. Class con override method phải
giữ chữ ký tương thích theo nguyên lý thay thế Liskov: kiểu trả về được hẹp hơn (*covariant*), kiểu
tham số được rộng hơn (*contravariant*), đầy đủ từ PHP 7.4.

```php
<?php
declare(strict_types=1);

interface Animal {}
final class Dog implements Animal {}

abstract class Shelter
{
    abstract public function adopt(string $name): Animal;
}
final class DogShelter extends Shelter
{
    public function adopt(string|int $name): Dog    // tham số rộng hơn, trả về hẹp hơn: hợp lệ
    {
        return new Dog();
    }
}
```

*Trait* là cơ chế tái dùng code theo chiều ngang: khi class `use T`, các method và property của `T`
được chép vào class như thể viết tay ở đó. Hệ quả của "chép vào":

- `self`, `static`, `$this`, `__CLASS__` trong trait chỉ class đang dùng trait, không chỉ trait.
- Thứ tự ưu tiên khi trùng tên method: **method của class > method của trait > method kế thừa từ
  class cha**. Trait đè được method của cha, class đè được method của trait.
- PHP 8.5 đổi thời điểm gắn trait: trait được gắn vào class **trước** class cha. Phần lấy từ trait
  được xử lý như khai báo trực tiếp trong class con rồi mới đối chiếu với class cha, nên một số
  trường hợp trùng tên property/hằng với class cha (hoặc interface của class cha) trước đây báo
  fatal error nay hợp lệ. Thứ tự ưu tiên method ở trên không đổi.

Hai trait cùng có method trùng tên thì phải tự giải quyết, không thì fatal error:

```php
<?php
declare(strict_types=1);

trait Hello { public function greet(): string { return 'Hello'; } }
trait Xin   { public function greet(): string { return 'Xin chào'; } }

final class Greeter
{
    use Hello, Xin {
        Hello::greet insteadof Xin;   // dùng bản của Hello cho tên greet
        Xin::greet as greetVi;        // bản của Xin vẫn gọi được qua tên khác
        Hello::greet as protected hi; // alias kèm đổi visibility
    }
}

$g = new Greeter();
echo $g->greet(), ' / ', $g->greetVi(), PHP_EOL;   // Hello / Xin chào
```

Các điểm chi tiết hay bị hỏi:

- Trait khai báo được `abstract` method để bắt class dùng nó phải cung cấp (ví dụ trait cần
  `getTable()`).
- Static property và biến `static` trong method của trait là **riêng cho mỗi class dùng trait**.
  ⚠️ Trước 8.3, nếu class cha và class con **cùng** `use` trait có static property thì hai class dùng
  chung một biến; từ 8.3 chúng tách riêng.
- Gọi static method hoặc truy cập static property trực tiếp trên trait (`T::foo()`) bị deprecated
  từ 8.1; chỉ gọi qua class dùng trait.
- Trait có hằng từ 8.2; từ 8.3 dùng được `as final` để cấm class con override method lấy từ trait.
- Property trong trait và trong class trùng tên chỉ hợp lệ khi tương thích hoàn toàn (cùng
  visibility, kiểu, `readonly`, giá trị khởi tạo).
- ⚠️ Trait không phải type: không `instanceof`, không type hint được. Muốn biết class có dùng trait
  không thì `class_uses($obj)`, nhưng hàm này **không** tính trait của class cha hay trait lồng
  trong trait. Laravel có helper `class_uses_recursive()` cho việc đó.

Laravel dùng trait rất nhiều trong Eloquent: `SoftDeletes`, `HasFactory`, `HasUuids`,
`Notifiable`. `Model::bootTraits()` (13.x) lấy `class_uses_recursive(static::class)`, rồi với mỗi
trait tên `X` sẽ gọi static method `bootX()` một lần cho mỗi class model (ví dụ `bootSoftDeletes()`
đăng ký global scope lọc `deleted_at`), và ghi nhớ method `initializeX()` để gọi trên mỗi instance
mới. Đây là quy ước tên, không phải tính năng của PHP; từ bản gần đây còn dùng được attribute
`#[Boot]`/`#[Initialize]`.

⚠️ Lạm dụng trait là kế thừa ngầm: method từ đâu tới, property nào đè property nào, trait nào phụ
thuộc method của trait khác, đều rất khó lần. Trait cũng không test riêng được, không thay thế được
bằng mock. Quy tắc thực dụng:

| Tình huống | Chọn |
|---|---|
| Đoạn code nhỏ, không có dependency, lặp ở nhiều class không cùng họ (ví dụ `HasSlug`) | Trait |
| Cần thay cài đặt được (test với fake, đổi driver) | Interface + composition: inject object làm việc đó |
| Trait bắt đầu cần gọi service, config, DB | Đổi sang class riêng được inject |
| Code "gần như interface nhưng có cài đặt mặc định" | Interface + trait cài đặt mặc định (ví dụ cặp `LoggerAwareInterface` + `LoggerAwareTrait` của PSR-3) |

#### Late static binding: `self::` và `static::`

- `self::` gắn với class **nơi dòng code được viết**, xác định lúc compile.
- `static::` gắn với class **được gọi lúc chạy**. Manual định nghĩa chính xác hơn: đó là class của
  lời gọi "không chuyển tiếp" (*non-forwarding call*) gần nhất. Cơ chế này tên là *late static
  binding* ("gắn muộn").
- `parent::` gọi bản của class cha.

```php
<?php
declare(strict_types=1);

class Model
{
    public static function create(): static { return new static(); }
    public static function createSelf(): self { return new self(); }
    public static function name(): string { return static::class; }
}
final class User extends Model {}

echo get_class(User::create()), PHP_EOL;      // User
echo get_class(User::createSelf()), PHP_EOL;  // Model
echo User::name(), PHP_EOL;                   // User
```

*Forwarding call*: gọi qua `self::`, `parent::`, `static::` thì thông tin "class được gọi" được
**chuyển tiếp**; gọi bằng tên class cụ thể (`A::foo()`) thì không, `static` bị đặt lại thành `A`.

```php
<?php
declare(strict_types=1);

class A
{
    public static function foo(): void { static::who(); }
    public static function who(): void { echo 'A', PHP_EOL; }
}
class B extends A
{
    public static function test(): void
    {
        A::foo();       // A: gọi bằng tên, không chuyển tiếp
        parent::foo();  // C: chuyển tiếp, static vẫn là C
        self::foo();    // C: chuyển tiếp
    }
    public static function who(): void { echo 'B', PHP_EOL; }
}
final class C extends B
{
    public static function who(): void { echo 'C', PHP_EOL; }
}
C::test();
```

Trong method thường (không static), `static` là class của object `$this`.

Kiểu trả về `static` (8.0) nói "trả về instance của đúng class được gọi", khác `self` là "instance
của class này (hoặc con)". Đây là kiểu cho fluent API và *named constructor*:
`public static function fromArray(array $a): static`.

Eloquent dựa vào `new static` khắp nơi. `Model::query()` trong 13.x viết đúng một dòng:
`return (new static)->newQuery();`. Nhờ vậy `User::query()` tạo builder cho `User` dù method nằm ở
`Model`. Nếu viết `new self` thì mọi query đều thành query của class trừu tượng `Model`.

⚠️ `new static()` gọi constructor của class con, nên class con đổi chữ ký constructor (thêm tham số
bắt buộc) sẽ làm vỡ `new static()` ở class cha. Eloquent tránh bằng cách mọi model dùng chung
constructor `__construct(array $attributes = [])`. Khi tự thiết kế, đánh dấu class `final` hoặc
constructor `final` nếu dùng `new static`; PHPStan cảnh báo trường hợp "unsafe usage of new static".

#### Magic method

*Magic method* là method tên bắt đầu bằng `__` mà engine tự gọi khi có sự kiện đặc biệt. Manual gọi
nhóm `__get`/`__set`/`__call` là *overloading*, nhưng nghĩa khác hẳn overloading của Java (nhiều
method cùng tên khác tham số, PHP không có). Từ 8.0, magic method nào có khai báo kiểu thì chữ ký
được kiểm tra theo chuẩn. Mọi magic method trừ `__construct`, `__destruct`, `__clone` phải khai
báo `public`, nếu không PHP báo `E_WARNING`.

| Method | Được gọi khi |
|---|---|
| `__construct`, `__destruct` | Tạo object; object bị giải phóng (refcount về 0, hoặc cuối script) |
| `__get($name)`, `__set($name, $value)` | Đọc/ghi property **không tồn tại hoặc không truy cập được** từ scope hiện tại |
| `__isset($name)`, `__unset($name)` | `isset()`/`empty()`, `unset()` trên property như trên |
| `__call($name, $args)` | Gọi method không tồn tại/không truy cập được trên object |
| `__callStatic($name, $args)` | Như trên nhưng gọi kiểu static `Foo::bar()` |
| `__toString()` | Object bị dùng như chuỗi. Từ 8.0 class có method này tự động implement `Stringable` |
| `__invoke(...)` | Gọi object như hàm `$obj()`; object thành `callable` |
| `__clone()` | Sau khi `clone` xong (module 1.2) |
| `__serialize()`, `__unserialize(array)` | `serialize()`/`unserialize()` (7.4) |
| `__sleep()`, `__wakeup()` | Cách serialize cũ, soft-deprecated từ 8.5 (khuyên không dùng, chưa phát cảnh báo) |
| `__set_state(array)` | Khi `var_export()` sinh code tạo lại object |
| `__debugInfo()` | Quyết định `var_dump` in gì. Từ 8.5 trả `null` là deprecated, trả `[]` |

⚠️ `__get` **không** được gọi cho property public đã khai báo và đã có giá trị. Nó chỉ là "lưới đỡ"
cho truy cập không thành. Vì vậy Eloquent model không bao giờ khai báo `public $name;` cho cột DB:
khai báo là chặn mất `__get`, và giá trị không còn đi qua cast, accessor.

Eloquent sống nhờ magic. Hai đường đi cần giải thích được, đọc theo source 13.x:

```
$user->name
  └─ property "name" không khai báo → Model::__get('name')
       └─ getAttribute('name')
            ├─ có trong mảng $attributes hoặc có accessor → getAttributeValue(): cast, accessor
            └─ không có → là relation? → getRelationValue() (lazy load, nguồn gốc N+1)

User::where('active', 1)
  └─ User không có static method where → Model::__callStatic('where', [...])
       └─ (new static)->where(...)                   tạo instance User rỗng
            └─ không có method where → Model::__call('where', [...])
                 └─ forwardCallTo($this->newQuery(), 'where', ...)
                      └─ Eloquent\Builder::where(...) → trả về Builder để nối tiếp ->get()
```

Cùng mô hình đó, `Model::__isset()` gọi `offsetExists()`, nên `isset($user->name)` và
`empty($user->name)` hoạt động đúng. Nếu một class có `__get` mà quên `__isset` thì `isset()` luôn
`false` và `??` luôn rơi về giá trị mặc định: một bug hay gặp khi tự viết class kiểu "attribute bag".

⚠️ *Indirect modification*: `__get` trả về **bản copy** của giá trị, nên sửa trực tiếp một array lấy
qua magic không có tác dụng:

```php
<?php
declare(strict_types=1);

final class Bag
{
    private array $data = ['tags' => []];
    public function __get(string $k): mixed { return $this->data[$k]; }
    public function __set(string $k, mixed $v): void { $this->data[$k] = $v; }
}

$b = new Bag();
$b->tags[] = 'php';      // Notice: Indirect modification of overloaded property Bag::$tags has no effect
var_dump($b->tags);      // array(0) {}

$tags = $b->tags;        // cách đúng: lấy ra, sửa, gán lại (đi qua __set)
$tags[] = 'php';
$b->tags = $tags;
```

Eloquent gặp đúng lỗi này với cột JSON cast sang `array`: `$user->options['theme'] = 'dark'` không
lưu gì; phải gán lại cả mảng, hoặc dùng cast `AsArrayObject`/`AsCollection`.

Liên quan: tạo property không khai báo trên object (*dynamic property*, `$obj->foo = 1` khi class
không có `foo`) bị deprecated từ 8.2. Không bị ảnh hưởng: `stdClass`, class có `__set`, và class
gắn `#[AllowDynamicProperties]`.

⚠️ Cái giá của magic:

- IDE và static analysis không biết `$user->name` hay `User::where` tồn tại, trừ khi có PHPDoc
  `@property`/`@method`, `laravel-ide-helper`, hoặc Larastan (module 2.8).
- Gõ sai tên (`$user->nmae`) không lỗi lúc viết; Eloquent chỉ trả `null` hoặc ném
  `MissingAttributeException` nếu bật chế độ strict của model.
- Chậm hơn truy cập trực tiếp: mỗi lần đi qua vài lời gọi hàm. Không đáng kể cho vài lần mỗi
  request, đáng kể trong vòng lặp hàng trăm nghìn lần.

Facade của Laravel (`Cache::get()`) cũng dùng `__callStatic`, nhưng lấy instance từ container thay
vì `new static` (module 2.4).

#### Closure và arrow function

*Closure* (hàm ẩn danh, *anonymous function*) là hàm không tên, là một giá trị: gán vào biến, truyền
vào hàm, trả về từ hàm. Mỗi closure là một object của class `Closure`. Closure không tự thấy biến bên
ngoài; phải liệt kê trong `use`:

```php
<?php
declare(strict_types=1);

$rate = 0.1;
$byValue = function (int $price) use ($rate): float { return $price * $rate; };
$byRef   = function (int $price) use (&$rate): float { return $price * $rate; };
$arrow   = fn(int $price): float => $price * $rate;   // tự bắt $rate theo giá trị

$rate = 0.2;
echo $byValue(100), ' ', $byRef(100), ' ', $arrow(100), PHP_EOL;   // 10 20 10

$count = 0;
$inc = fn() => $count++;     // tăng bản copy bên trong, biến ngoài không đổi
$inc();
echo $count, PHP_EOL;        // 0
```

| | `function () use (...)` | `fn() =>` (7.4) |
|---|---|---|
| Bắt biến ngoài | Phải liệt kê trong `use` | Tự động, mọi biến được dùng trong thân |
| Theo giá trị hay reference | Giá trị; `use (&$x)` để bắt reference | Chỉ theo giá trị, không sửa được biến ngoài |
| Thời điểm bắt | Lúc **định nghĩa** closure | Lúc định nghĩa |
| Thân | Nhiều câu lệnh, cần `return` | Đúng một biểu thức, tự trả về |

⚠️ "Theo giá trị" áp cho biến, không áp cho object bên trong biến. `use ($order)` copy handle, nên
closure sửa `$order->status` thì bên ngoài vẫn thấy (module 1.2).

*Bind `$this`*. Closure tạo bên trong method của class tự động gắn (*bind*) `$this` và scope của
class đó, nên truy cập được cả property `private`:

- `static function () {...}` hoặc `static fn () => ...` không bind `$this`. Dùng khi closure không
  cần `$this`: nhẹ hơn, và không giữ object sống.
- ⚠️ Trong process sống lâu (queue worker, Octane, module 3.5), closure lưu vào một registry tĩnh
  (event listener, macro, callback của container) giữ luôn `$this`, nên object đó và mọi thứ nó
  tham chiếu không bao giờ được giải phóng. Với PHP-FPM, request kết thúc là dọn hết nên ít ai thấy.
- `Closure::bind($fn, $newThis, $scope)`, `$fn->bindTo($newThis, $scope)` tạo bản closure gắn với
  object/scope khác; `$fn->call($obj, ...$args)` gắn tạm và gọi luôn. Bind object vào closure
  `static` báo Warning và trả về `null`.

`Macroable` của Laravel là ví dụ thật: `Str::macro('slugVi', function (...) {...})` lưu closure vào
mảng static; khi gọi, `__call` chạy `$macro->bindTo($this, static::class)` để trong macro dùng được
`$this` như method thật, còn `__callStatic` chạy `$macro->bindTo(null, static::class)`.

*First-class callable syntax* (8.1): thêm `(...)` sau một lời gọi để lấy closure thay vì gọi.

```php
<?php
declare(strict_types=1);

final class Normalizer
{
    public function run(array $names): array
    {
        return array_map($this->clean(...), $names);   // dùng được method private
    }
    private function clean(string $s): string { return trim(strtolower($s)); }
}

$upper = strtoupper(...);                 // Closure bọc hàm built-in
echo $upper('php'), PHP_EOL;              // PHP
var_dump((new Normalizer())->run([' An ', 'BÌNH']));   // ["an", "bÌnh"]: strtolower chỉ đổi ASCII, dùng mb_strtolower cho tiếng Việt
```

So với callable kiểu cũ (`'strtoupper'`, `[$this, 'clean']`, `[Foo::class, 'bar']`):

- Tên hàm là symbol thật, nên IDE/PHPStan kiểm được, đổi tên (refactor) không bỏ sót chuỗi.
- Scope được chốt **tại chỗ tạo** closure: `$this->clean(...)` tạo trong class nên gọi được method
  private ở bất cứ đâu; chuỗi `[$this, 'clean']` thì bị kiểm quyền truy cập ở nơi gọi.
- Sai tên hàm báo lỗi ngay lúc tạo, không đợi tới lúc callback được gọi.
- `Closure::fromCallable($c)` là cách làm cùng việc trước 8.1.
- Từ 8.5, closure và first-class callable dùng được trong *constant expression* (giá trị mặc định
  của property, tham số attribute, hằng).

Đối chiếu: closure của Go bắt biến **theo reference** (sửa được biến ngoài), nên bẫy kinh điển của
Go là closure trong vòng lặp cùng thấy một biến (Go 1.22 đã đổi thành mỗi vòng một biến mới). Lambda
của Java chỉ bắt biến *effectively final*, không sửa được, gần với `fn` của PHP. PHP mặc định bắt
theo giá trị nên không có bẫy vòng lặp, trừ khi bạn tự viết `use (&$x)`.

**Tóm tắt nhanh**
- Interface là type và hợp đồng; abstract class chia sẻ code và state trong một họ; trait chép code
  vào class, không phải type. Thứ tự ưu tiên: class > trait > class cha.
- `self::` là class chứa dòng code, `static::` là class được gọi lúc chạy; `new static` là nền của
  Eloquent (`Model::query()` là `(new static)->newQuery()`).
- `User::where()` đi qua `__callStatic` → `new static` → `__call` → `forwardCallTo` sang
  `Eloquent\Builder`. `$user->name` đi qua `__get` → `getAttribute`.
- Magic đổi lại sự tiện bằng tính mù với IDE/static analysis, bẫy indirect modification, và tốc độ.
- Closure bắt biến theo giá trị lúc định nghĩa (`use (&$x)` để bắt reference); closure trong class
  giữ `$this`, dùng `static fn` khi không cần. `foo(...)` tạo closure an toàn hơn callable chuỗi.

**Nguồn**: [PHP: Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php) ·
[PHP: Class Abstraction](https://www.php.net/manual/en/language.oop5.abstract.php) ·
[PHP: Traits](https://www.php.net/manual/en/language.oop5.traits.php) ·
[PHP: Late Static Bindings](https://www.php.net/manual/en/language.oop5.late-static-bindings.php) ·
[PHP: Magic Methods](https://www.php.net/manual/en/language.oop5.magic.php) ·
[PHP: Overloading](https://www.php.net/manual/en/language.oop5.overloading.php) ·
[PHP: Anonymous functions](https://www.php.net/manual/en/functions.anonymous.php) ·
[PHP: Arrow Functions](https://www.php.net/manual/en/functions.arrow.php) ·
[PHP: First class callable syntax](https://www.php.net/manual/en/functions.first_class_callable_syntax.php) ·
[laravel/framework 13.x: Eloquent/Model.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Eloquent/Model.php) ·
[laravel/framework 13.x: Macroable.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Macroable/Traits/Macroable.php)

---

### 1.4 Exception và xử lý lỗi

Module này trả lời: PHP có những loại "lỗi" nào (exception, error, warning, fatal), loại nào bắt được
bằng `try/catch` và loại nào không, và vì sao chỉ `catch (Exception)` là nguồn của các bug "lỗi bị
nuốt, log không có gì".

#### Cây Throwable

*Throwable* là interface gốc của mọi thứ `throw` được. Từ PHP 7, cây này có đúng hai nhánh, và hai
nhánh **không kế thừa nhau**:

```text
Throwable (interface)
├── Exception                         lỗi ứng dụng dự kiến được, nên xử lý
│   ├── ErrorException                bọc warning/notice thành exception (dùng với set_error_handler)
│   ├── JsonException                 json_decode/json_encode với JSON_THROW_ON_ERROR (7.3)
│   ├── LogicException                (SPL) lỗi trong code, sửa code chứ không bắt
│   │   ├── BadFunctionCallException
│   │   │   └── BadMethodCallException
│   │   ├── DomainException
│   │   ├── InvalidArgumentException
│   │   ├── LengthException
│   │   └── OutOfRangeException
│   └── RuntimeException              (SPL) lỗi chỉ phát hiện được lúc chạy
│       ├── OutOfBoundsException, OverflowException, RangeException,
│       │   UnderflowException, UnexpectedValueException
│       └── PDOException              lỗi DB (Laravel bọc lại thành QueryException)
└── Error                             lỗi của engine hoặc lỗi lập trình
    ├── ArithmeticError
    │   └── DivisionByZeroError       intdiv(1, 0), 1 % 0, và 1 / 0 (từ 8.0)
    ├── AssertionError
    ├── CompileError
    │   └── ParseError                eval() hoặc include file sai cú pháp
    ├── TypeError
    │   └── ArgumentCountError        gọi hàm thiếu tham số
    ├── ValueError                    đúng kiểu nhưng sai giá trị (8.0), vd str_repeat('x', -1)
    ├── UnhandledMatchError           match không có nhánh khớp (8.0)
    └── FiberError                    dùng Fiber sai trạng thái (8.1)
```

Ý nghĩa hai nhánh:

- `Exception`: tình huống ứng dụng **dự kiến** có thể xảy ra và có cách phản ứng: DB mất kết nối,
  input sai định dạng, API bên ngoài trả lỗi. Code nghiệp vụ ném và bắt loại này.
- `Error`: dấu hiệu **code sai** hoặc engine gặp tình huống không thể tiếp tục: truyền sai kiểu, gọi
  method không tồn tại, chia cho 0. Cách xử lý đúng gần như luôn là sửa code, không phải bắt rồi chạy
  tiếp.

Lịch sử giải thích vì sao có nhánh `Error`: trước PHP 7, các lỗi như gọi hàm không tồn tại là
*fatal error*, script dừng ngay, không `catch` được, `finally` không chạy, không dọn dẹp được gì.
PHP 7 chuyển phần lớn các fatal error đó thành object `Error` được ném ra. Nhưng để code cũ viết
`catch (Exception $e)` không đột nhiên bắt những thứ trước giờ vẫn làm chết script, `Error` được đặt
ở nhánh riêng, không kế thừa `Exception`.

⚠️ Hệ quả: `catch (Exception $e)` **không** bắt `TypeError`, `ArgumentCountError`,
`DivisionByZeroError`...

```php
<?php
declare(strict_types=1);

function qty(int $n): int { return $n; }

try {
    qty('5');                        // strict_types=1 nên không ép kiểu: TypeError
} catch (Exception $e) {
    echo "Exception\n";              // KHÔNG vào đây
} catch (Throwable $e) {
    echo get_class($e), "\n";        // TypeError
}

try {
    echo intdiv(10, 0);
} catch (DivisionByZeroError $e) {
    echo $e->getMessage(), "\n";     // Division by zero
}
```

- Muốn bắt cả hai nhánh: `catch (Throwable $e)`.
- Code của bạn **không** `implements Throwable` trực tiếp được (PHP báo fatal error), phải
  `extends Exception` hoặc `extends Error` (hoặc lớp con của chúng).
- Nên tạo exception theo nghiệp vụ, kế thừa nhánh SPL phù hợp:

  ```php
  <?php
  declare(strict_types=1);

  final class InsufficientStockException extends RuntimeException
  {
      public function __construct(public readonly int $productId, int $wanted, int $left)
      {
          parent::__construct("Sản phẩm {$productId}: cần {$wanted}, còn {$left}");
      }
  }
  ```

  `LogicException` dùng cho lỗi "đáng lẽ không bao giờ xảy ra nếu code đúng" (gọi method khi object
  chưa được khởi tạo đủ). `RuntimeException` dùng cho lỗi phụ thuộc môi trường hoặc dữ liệu lúc chạy.

Đối chiếu Java: Java cũng có `Throwable` với hai nhánh `Exception` và `Error`, và `Error` của Java
(`OutOfMemoryError`, `StackOverflowError`) cũng "không nên bắt". Khác biệt: `TypeError` của PHP
tương ứng với lỗi mà Java bắt được ngay lúc compile.

#### try/catch/finally

Cơ chế khi một exception được ném:

1. Dòng lệnh sau `throw` trong `try` không chạy nữa.
2. PHP duyệt các khối `catch` **theo thứ tự viết**, khối đầu tiên có kiểu khớp (`instanceof`) được
   chạy. Vì vậy đặt kiểu cụ thể trước, kiểu chung (`Throwable`) sau cùng.
3. Không có `catch` nào khớp trong hàm hiện tại thì exception "nổi lên" (*bubble up*) hàm gọi nó,
   chạy mọi `finally` gặp trên đường đi.
4. Nổi tới tận scope ngoài cùng mà không ai bắt: gọi *global exception handler* nếu đã đăng ký bằng
   `set_exception_handler()`, nếu không thì PHP in `PHP Fatal error: Uncaught ...` và dừng.

Cú pháp đáng biết theo phiên bản:

| Cú pháp | Từ bản | Ví dụ |
|---|---|---|
| Multi-catch | 7.1 | `catch (JsonException \| ValueError $e)` |
| Catch không cần biến | 8.0 | `catch (JsonException) { return null; }` |
| `throw` là biểu thức | 8.0 | `$user = $repo->find($id) ?? throw new NotFound();` |
| Tham số `previous` | 5.3 | `new OrderFailed('...', previous: $e)` (viết kiểu named argument cần 8.0) |

*Exception chaining* (nối exception): khi bắt một exception kỹ thuật và ném lại exception nghiệp vụ,
luôn truyền exception gốc vào `previous`. Nếu không, log chỉ còn "Không lưu được đơn" mà mất dấu
"Deadlock found when trying to get lock". Laravel log toàn bộ chuỗi `getPrevious()`.

```php
try {
    $this->orders->save($order);
} catch (PDOException $e) {
    throw new OrderNotSavedException("Đơn {$order->id} lỗi khi lưu", previous: $e);
}
```

*finally* luôn chạy sau `try`/`catch`, dù `try` kết thúc bình thường, `return` sớm, hay ném
exception. Dùng để nhả tài nguyên: đóng file, nhả lock, `DB::rollBack()` khi cần.

Tương tác với `return` (theo manual PHP):

- `return` trong `try` được **tính giá trị ngay** lúc gặp, nhưng chỉ thực sự trả về sau khi
  `finally` chạy xong.
- ⚠️ Nếu `finally` cũng có `return`, giá trị của `finally` thắng. Tệ hơn, nếu lúc đó đang có exception
  bay ra từ `try`, exception đó bị **vứt bỏ** không dấu vết:

  ```php
  <?php
  declare(strict_types=1);

  function charge(): string
  {
      try {
          throw new RuntimeException('Cổng thanh toán timeout');
      } finally {
          return 'ok';               // exception ở trên biến mất
      }
  }

  var_dump(charge());                // string(2) "ok"
  ```

  Quy tắc: không `return`, `break`, `continue` trong `finally`.
- Nếu cả `try` và `finally` cùng ném exception, exception của `finally` được ném ra ngoài, còn
  exception của `try` được gắn vào làm `previous` của nó (hành vi mô tả trong manual).

*JsonException*: `json_decode` mặc định trả `null` khi JSON hỏng, và `null` cũng là kết quả hợp lệ của
chuỗi `"null"`, nên không phân biệt được. Cách cũ là gọi `json_last_error()` sau mỗi lần decode, rất
dễ quên. Từ 7.3:

```php
<?php
declare(strict_types=1);

try {
    $data = json_decode('{"a":1,', associative: true, flags: JSON_THROW_ON_ERROR);
} catch (JsonException $e) {
    echo $e->getMessage();           // Syntax error
}
```

#### Warning, notice và fatal error

Bên cạnh exception, PHP còn cơ chế *error reporting* cũ: engine "phát" một thông báo có mức độ
(`E_WARNING`, `E_NOTICE`, `E_DEPRECATED`...) rồi **chạy tiếp**. Đây không phải exception, `try/catch`
không thấy chúng.

```php
<?php
declare(strict_types=1);

$user = ['name' => 'An'];
try {
    $email = $user['email'];         // Warning: Undefined array key "email"
} catch (Throwable $e) {
    echo "không bao giờ vào đây\n";
}
var_dump($email);                    // NULL, chương trình vẫn chạy tiếp
```

PHP 8.0 (RFC *Reclassifying engine warnings*) nâng mức nhiều lỗi: đọc biến chưa định nghĩa và đọc key
không tồn tại từ notice lên warning; một số trường hợp vô nghĩa (dùng giá trị scalar như array để ghi)
chuyển thẳng thành `Error`.

Ba chỉ thị `php.ini` quyết định số phận của các thông báo này:

| Chỉ thị | Ý nghĩa | Dev | Production |
|---|---|---|---|
| `error_reporting` | Mức nào được báo | `E_ALL` | `E_ALL` (có thể bỏ `E_DEPRECATED`) |
| `display_errors` | In lỗi ra output | On | ⚠️ Off: lỗi có thể lộ đường dẫn, thông tin DB |
| `log_errors` / `error_log` | Ghi lỗi vào file/syslog | Tuỳ | On |

*Error handler*: `set_error_handler()` đăng ký hàm được gọi thay cho xử lý mặc định. Cách phổ biến là
biến mọi warning/notice thành `ErrorException` để chúng đi theo luồng exception thống nhất:

```php
<?php
declare(strict_types=1);

set_error_handler(function (int $severity, string $message, string $file, int $line): bool {
    if (!(error_reporting() & $severity)) {
        return false;                // mức này đang bị tắt (vd dùng @): để PHP xử lý mặc định
    }
    throw new ErrorException($message, 0, $severity, $file, $line);
});

try {
    $empty = [];
    $x = $empty[0];
} catch (ErrorException $e) {
    echo $e->getMessage();           // Undefined array key 0
}
```

- ⚠️ Error handler **không** nhận được các lỗi thật sự fatal: `E_ERROR` (ví dụ hết `memory_limit`,
  vượt `max_execution_time`), `E_PARSE`, `E_CORE_*`, `E_COMPILE_*`. Với loại này chỉ còn
  `register_shutdown_function()` kết hợp `error_get_last()` để ghi log trước khi process chết.
- Toán tử `@` tạm hạ `error_reporting()` trong lúc chạy biểu thức. Từ PHP 8.0 `@` không còn che được
  fatal error. Handler ở trên kiểm tra `error_reporting() & $severity` chính là để tôn trọng `@`.
- PHP 8.5: thông báo fatal error (loại không bắt được) có kèm *stack trace* (danh sách các hàm đang
  gọi dở), điều khiển bởi ini `fatal_error_backtraces`. Trước 8.5, "Allowed memory size exhausted"
  chỉ cho biết dòng cuối cùng, không biết ai gọi tới đó.

Tổng kết "cái gì bắt được bằng gì":

| Loại | Ví dụ | `catch (Exception)` | `catch (Throwable)` | Error handler | Shutdown function |
|---|---|---|---|---|---|
| Exception | `PDOException` | Có | Có | Không | Không |
| Error | `TypeError` | Không | Có | Không | Không |
| Warning/notice/deprecated | Undefined array key | Không (trừ khi handler đổi thành `ErrorException`) | Như cột trái | Có | Không |
| Fatal error | Hết bộ nhớ, timeout | Không | Không | Không | Có (qua `error_get_last()`) |

#### Trong Laravel

Laravel đăng ký cả ba tầng trên ngay lúc khởi động, trong bootstrapper
`Illuminate\Foundation\Bootstrap\HandleExceptions`:

1. `error_reporting(-1)`: báo mọi mức.
2. `set_error_handler`: mọi warning/notice thành `ErrorException`, **ở mọi môi trường** (không chỉ
   dev). Riêng `E_DEPRECATED` không ném mà được ghi vào log channel `deprecations` (skeleton đặt
   `LOG_DEPRECATIONS_CHANNEL=null`, tức mặc định bị bỏ qua).
3. `set_exception_handler`: exception không ai bắt được chuyển cho exception handler của app.
4. `register_shutdown_function`: bắt fatal error, dựng thành `FatalError` để vẫn log được. Laravel
   còn giữ sẵn 32 KB bộ nhớ dự phòng để giải phóng lúc hết RAM, đủ cho việc ghi log.
5. Ngoài môi trường `testing`, `display_errors` bị tắt.

⚠️ Vì bước 2, một dòng `$row['email']` với key không tồn tại, vốn chỉ là warning trong PHP thuần, sẽ
thành exception và trả HTTP 500 trong app Laravel. Đây là chủ đích: bug lộ ra sớm thay vì lặng lẽ
trả `null`.

Cấu hình handler nằm trong `bootstrap/app.php` (Laravel 11+ không còn `app/Exceptions/Handler.php`):

```php
use App\Exceptions\InvalidOrderException;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Http\Request;
use Psr\Log\LogLevel;

->withExceptions(function (Exceptions $exceptions): void {
    // report: exception được ghi/gửi đi đâu. Mặc định vẫn log thêm, trừ khi ->stop() hoặc return false
    $exceptions->report(function (InvalidOrderException $e): void {
        // gửi Slack...
    });
    $exceptions->level(PDOException::class, LogLevel::CRITICAL);
    $exceptions->dontReport([InvalidOrderException::class]);
    $exceptions->context(fn (): array => ['region' => 'ap-southeast-1']);

    // render: exception biến thành HTTP response nào. Closure không trả gì thì dùng render mặc định
    $exceptions->render(function (InvalidOrderException $e, Request $request) {
        return response()->json(['message' => $e->getMessage()], 422);
    });
})
```

- Loại exception mà closure xử lý được Laravel suy ra từ **type-hint** của tham số đầu tiên.
- Exception tự định nghĩa có thể tự mang method `report()`, `render()`, `context()`.
- Laravel mặc định không report một số loại (danh sách `$internalDontReport` trong
  `Illuminate\Foundation\Exceptions\Handler`): `HttpException` (404, 403...), `ModelNotFoundException`,
  `TokenMismatchException` (419, CSRF sai), `ValidationException`, `AuthenticationException`,
  `AuthorizationException`. Đánh dấu một class bằng interface `ShouldntReport` để nó không bao giờ được report.
- `report($e)` helper: log exception nhưng **vẫn chạy tiếp** request. Dùng khi bắt để trả giá trị mặc
  định mà vẫn muốn có dấu vết.
- `APP_DEBUG=true` hiển thị trang lỗi chi tiết (stack trace, biến môi trường). ⚠️ Production luôn
  `APP_DEBUG=false`.

*Vì sao job "chết im lặng"*. Queue worker của Laravel (`Illuminate\Queue\Worker`) bao việc chạy job
bằng `catch (Throwable $e)` và gọi `report()`, nên một `TypeError` bay ra khỏi job vẫn được log và job
bị đánh dấu thất bại/thử lại. "Im lặng" xảy ra khi chính code của bạn chặn đường:

```php
public function handle(): void
{
    try {
        $this->sync();                       // ném TypeError do API trả null thay vì array
    } catch (Exception $e) {                 // không bắt TypeError...
        Log::error('sync lỗi', ['e' => $e]); // ...nên dòng log này không chạy
        $this->release(60);                  // ...và cũng không thử lại theo ý bạn
    }
}
```

Nếu tệ hơn nữa, có người "sửa" bằng `catch (Throwable) {}` rỗng: job luôn báo thành công, lỗi biến
mất hoàn toàn. Các kịch bản im lặng khác: process chết vì fatal error (hết bộ nhớ) trong một script
tự viết không có shutdown function, hoặc `log_errors` tắt. Nguyên tắc:

1. Chỉ bắt exception mà tại chỗ đó bạn **biết cách xử lý**. Không biết thì để nó bay.
2. Bắt `Throwable` chỉ ở **biên** (vòng lặp worker, entry point của script, middleware ngoài cùng),
   và luôn log hoặc ném lại.
3. Bắt rồi ném lại exception nghiệp vụ thì truyền `previous`.

#### Đối chiếu Java/Go

| | PHP | Java | Go |
|---|---|---|---|
| Cơ chế chính | Exception | Exception | Giá trị `error` trả về |
| Bắt buộc khai báo/bắt | Không | Có với *checked exception* | Compiler không ép, nhưng lint (`errcheck`) và convention ép |
| Lỗi "không nên bắt" | Nhánh `Error` | Nhánh `Error` | `panic` (bắt bằng `recover`, hiếm dùng) |
| Nối lỗi | `previous` | `cause` | `fmt.Errorf("...: %w", err)`, `errors.Is/As` |

- *Checked exception* của Java: exception mà method phải khai báo trong `throws` hoặc tự bắt, nếu
  không thì không compile. PHP không có khái niệm này; mọi exception PHP giống *unchecked exception*
  (`RuntimeException`) của Java. PHPDoc `@throws` chỉ là tài liệu (PHPStan có thể kiểm tra nếu bật).
- Go: lỗi là giá trị, kiểm bằng `if err != nil` ngay sau lời gọi ([07-go.md](../07-go.md)). Ưu điểm:
  đường lỗi hiện rõ trong code. Nhược: dài dòng, và quên kiểm `err` thì lỗi bị bỏ qua giống hệt
  `catch` rỗng của PHP.

**Tóm tắt nhanh**
- `Throwable` có hai nhánh không kế thừa nhau: `Exception` (lỗi dự kiến) và `Error` (lỗi code/engine,
  PHP 7+). `catch (Exception)` không bắt `TypeError`.
- Warning/notice không phải exception; chỉ bắt được khi error handler đổi thành `ErrorException`.
  Laravel làm việc đó ở mọi môi trường.
- Fatal error (hết bộ nhớ, timeout) không `catch` được; chỉ shutdown function thấy. PHP 8.5 kèm stack
  trace cho fatal error.
- Không `return` trong `finally`: nó đè giá trị trả về và vứt luôn exception đang bay.
- Bắt `Throwable` chỉ ở biên, luôn log hoặc ném lại, truyền `previous` khi bọc exception.

**Nguồn**: [PHP: Exceptions](https://www.php.net/manual/en/language.exceptions.php) ·
[PHP: Errors in PHP 7](https://www.php.net/manual/en/language.errors.php7.php) ·
[PHP: Error basics](https://www.php.net/manual/en/language.errors.basics.php) ·
[PHP: SPL Exceptions](https://www.php.net/manual/en/spl.exceptions.php) ·
[PHP: set_error_handler](https://www.php.net/manual/en/function.set-error-handler.php) ·
[Laravel: Error Handling](https://laravel.com/docs/errors) ·
[laravel/framework: HandleExceptions.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Bootstrap/HandleExceptions.php)


---

### 1.5 Composer và PSR

Module này trả lời: khi code viết `new App\Models\User`, file nào được nạp và qua những bước nào;
Composer chọn phiên bản dependency ra sao và vì sao `composer.lock` quyết định "máy dev chạy,
production vỡ"; PSR là gì và những chuẩn nào hay gặp.

#### Autoload và PSR-4

*Autoload* (tự nạp class): PHP cho phép đăng ký một hoặc nhiều hàm bằng `spl_autoload_register()`.
Khi code dùng một class, interface, trait hay enum **chưa được định nghĩa**, PHP gọi lần lượt các hàm
đó với tên đầy đủ của class (*fully qualified class name*, FQCN, ví dụ `App\Models\User`). Hàm nào
`require` được file định nghĩa class thì PHP dừng lại và dùng class đó; tất cả đều không tìm thấy thì
PHP ném `Error: Class "App\Models\User" not found`.

Tự viết một autoloader tối giản để thấy cơ chế:

```php
<?php
declare(strict_types=1);

spl_autoload_register(function (string $class): void {
    $prefix  = 'App\\';
    $baseDir = __DIR__ . '/app/';
    if (strncmp($class, $prefix, strlen($prefix)) !== 0) {
        return;                                   // không phải việc của mình, để autoloader khác thử
    }
    $relative = substr($class, strlen($prefix));  // "Models\User"
    $file = $baseDir . str_replace('\\', '/', $relative) . '.php';
    if (is_file($file)) {
        require $file;
    }
});

$u = new App\Models\User();                       // lúc này mới require app/Models/User.php
```

*PSR* (PHP Standards Recommendation) là các chuẩn do nhóm *PHP-FIG* (Framework Interop Group) đặt ra
để thư viện của nhiều bên dùng chung được. *PSR-4* là chuẩn map FQCN sang đường dẫn file:

- Một *namespace prefix* (một hoặc vài đoạn đầu của namespace, ví dụ `App\`) ứng với một hoặc nhiều
  *base directory* (ví dụ `app/`).
- Phần namespace **sau** prefix ứng với thư mục con, dấu `\` thành dấu phân cách thư mục.
- Tên class cuối cùng ứng với tên file `.php`.
- Chữ hoa chữ thường của thư mục và file phải **khớp đúng** với namespace và tên class.
- Autoloader theo PSR-4 không được ném exception, không được phát lỗi (để autoloader khác còn thử).
- Khác PSR-0 (chuẩn cũ, đã deprecated): PSR-4 **không** lặp lại prefix trong đường dẫn, và dấu `_`
  trong tên class không còn ý nghĩa đặc biệt.

Trong `composer.json` của skeleton Laravel:

```json
"autoload": {
    "psr-4": {
        "App\\": "app/",
        "Database\\Factories\\": "database/factories/",
        "Database\\Seeders\\": "database/seeders/"
    }
},
"autoload-dev": { "psr-4": { "Tests\\": "tests/" } }
```

Prefix phải kết thúc bằng `\\` (trong JSON phải escape nên thành hai dấu). Nếu viết `"Foo"` thì nó
khớp cả namespace `FooBar`; `"Foo\\"` và `"FooBar\\"` mới tách bạch.

Từng bước khi `public/index.php` chạy tới `new App\Models\User`:

```
public/index.php
  require vendor/autoload.php
    └─ vendor/composer/autoload_real.php
         tạo Composer\Autoload\ClassLoader, nạp các bảng đã sinh sẵn lúc dump:
           autoload_psr4.php      prefix => [thư mục]
           autoload_classmap.php  FQCN => file
           autoload_files.php     file luôn require ngay (helper functions)
         spl_autoload_register([$loader, 'loadClass'])
  ...
  new App\Models\User  ──►  class chưa có  ──►  PHP gọi ClassLoader::loadClass('App\Models\User')
```

Bên trong `ClassLoader::findFile()` (mã nguồn Composer), thứ tự tra cứu là:

1. Tra *classmap*: `isset($classMap['App\Models\User'])`. Có thì trả đường dẫn ngay, **không chạm
   đĩa**.
2. Nếu bật *authoritative* (xem nhóm sau) hoặc class này đã từng tra hụt trong request này
   (`missingClasses`): trả `false` luôn.
3. Nếu bật APCu: tra cache APCu.
4. Tra PSR-4. Đổi tên class thành đường dẫn logic `App/Models/User.php`, rồi thử từng prefix từ **dài
   nhất** tới ngắn nhất: `App\Models\`, rồi `App\`. Với mỗi prefix có đăng ký, ghép base directory với
   phần còn lại và gọi `file_exists()`:
   `app/` + `Models/User.php` = `app/Models/User.php`. Tồn tại thì trả về.
   (Để nhanh, Composer đánh chỉ mục các prefix theo **chữ cái đầu** của tên class, nên chỉ những
   prefix bắt đầu bằng `A` mới được xét.)
5. Thử các thư mục fallback PSR-4 (prefix rỗng `""`), rồi PSR-0, rồi `include_path` nếu được bật.
6. Không thấy: ghi nhớ vào `missingClasses`, trả `false`. `loadClass` trả `null`, PHP chuyển sang
   autoloader kế tiếp, hết thì ném `Error`.
7. Thấy: `include` file trong một closure `static` không có `$this`, nên file được nạp không truy cập
   được nội bộ của `ClassLoader`.

Các tính chất quan trọng:

- Autoload là **lazy**: chỉ class thật sự được dùng mới được nạp. App có 20.000 class trong `vendor`
  nhưng một request có thể chỉ nạp vài trăm.
- Các loại autoload khác trong `composer.json`: `classmap` (quét thư mục, dùng cho code không theo
  PSR-4) và `files` (**luôn** `require` ở mọi request, dùng cho file chứa hàm như `helpers.php`, vì
  PHP không autoload được hàm).
- Sau khi sửa phần `autoload` trong `composer.json` phải chạy `composer dump-autoload` để sinh lại các
  bảng trong `vendor/composer/`. Thêm class mới theo PSR-4 thì **không** cần, vì bước 4 tìm file lúc
  chạy.
- ⚠️ Bẫy kinh điển: macOS và Windows mặc định dùng filesystem không phân biệt hoa thường, Linux thì
  có. File `app/models/User.php` (chữ `m` thường) chạy ổn trên máy dev macOS, lên server Linux báo
  `Class "App\Models\User" not found`. `composer dump-autoload -o --strict-ambiguous` giúp phát hiện
  các trường hợp như vậy; `--strict-psr` trả exit code lỗi khi có file không khớp PSR-4, nên đưa vào CI.

#### Tối ưu autoloader

Vấn đề: ở bước 4, mỗi class chưa có trong classmap tốn ít nhất một lần `file_exists()`, tức một
syscall `stat` xuống filesystem. Với hàng trăm class mỗi request, cộng lại đáng kể. Trong dev điều này
chấp nhận được, vì thêm class mới là dùng được ngay mà không cần build lại gì. Production thì code
không đổi giữa hai lần deploy, nên có thể tính trước. Composer có ba mức tối ưu:

| Mức | Cách bật | Làm gì | Đánh đổi |
|---|---|---|---|
| 1: Class map generation | `dump-autoload -o`, `install/update -o` (`--optimize-autoloader`), hoặc config `"optimize-autoloader": true` | Quét mọi thư mục PSR-4/PSR-0, sinh classmap đầy đủ. Class có trong map thì trả đường dẫn ngay, không `stat` | Gần như không có. Chỉ là class **không tồn tại** (tra hụt) vẫn rơi xuống PSR-4 và `stat` như cũ |
| 2/A: Authoritative classmap | `-a` / `--classmap-authoritative`, hoặc config `"classmap-authoritative": true` | Tự bật mức 1. Không có trong classmap thì coi như **không tồn tại**, bỏ hẳn bước PSR-4 | ⚠️ Class sinh ra lúc runtime, hoặc file thêm vào sau khi dump, sẽ "not found" |
| 2/B: APCu cache | `--apcu` / `--apcu-autoloader`, hoặc config `"apcu-autoloader": true` | Cache kết quả tra (thấy **và** không thấy) vào APCu, dùng lại qua các request | Cần extension APCu, tốn bộ nhớ APCu. Không tự sinh classmap, nên thường kết hợp với `-o`. An toàn, không gây "not found" |

- 2/A và 2/B **không kết hợp** được với nhau; chúng giải cùng một vấn đề (tra hụt) theo hai cách.
- Mức 1 càng có lợi khi bật OPcache: classmap là một file PHP trả về một array hằng lớn, OPcache giữ
  nó sẵn trong bộ nhớ dùng chung nên gần như không tốn gì để nạp (module 2.3).
- Composer khuyên **không** bật các tối ưu này ở dev. Riêng skeleton Laravel đặt sẵn
  `"optimize-autoloader": true` trong `config`, tức mức 1 được bật cả ở dev. Việc này vô hại vì mức 1
  vẫn fallback về PSR-4: class mới thêm vẫn được tìm thấy, chỉ không nằm trong classmap cho tới lần
  dump sau.

Lệnh deploy điển hình:

```sh
composer install --no-dev --optimize-autoloader --no-interaction --prefer-dist
# hoặc chặt hơn, khi chắc chắn không có class sinh lúc runtime:
composer install --no-dev --classmap-authoritative --no-interaction
```

- `--no-dev`: không cài package trong `require-dev` (PHPUnit, Faker...) và bỏ `autoload-dev`.
- ⚠️ Đã `--no-dev` mà code production lỡ dùng class của package dev (ví dụ Faker trong seeder chạy ở
  prod) thì lỗi chỉ lộ ra trên production. CI nên chạy thử một lượt với `--no-dev`.

#### composer.json, composer.lock và semver

Hai file có vai trò khác nhau:

- `composer.json`: **ràng buộc** do người viết khai báo, ví dụ `"guzzlehttp/guzzle": "^7.8"`.
- `composer.lock`: **kết quả** giải ràng buộc, ghi phiên bản chính xác của **mọi** package, kể cả
  dependency gián tiếp (dependency của dependency), kèm commit/hash nguồn. Thêm một `content-hash` để
  Composer biết lock có khớp với `composer.json` hiện tại không.

| Lệnh | Đọc gì | Làm gì | Khi nào chạy |
|---|---|---|---|
| `composer install` (có lock) | `composer.lock` | Cài **đúng** các bản trong lock, không resolve lại | CI, deploy, máy dev mới clone |
| `composer install` (chưa có lock) | `composer.json` | Resolve như `update` rồi ghi lock | Lần đầu tạo project |
| `composer update` | `composer.json` | Resolve lại: với mỗi package chọn bản **cao nhất** thoả mọi ràng buộc, ghi lại lock, rồi cài | Chủ động nâng dependency, trên máy dev, commit lock mới qua review |
| `composer update vendor/pkg` | `composer.json` | Chỉ nâng package đó (thêm `-W` để nâng cả dependency của nó) | Nâng có kiểm soát |
| `composer require vendor/pkg` | | Thêm ràng buộc vào `composer.json` rồi update riêng package đó | Thêm dependency |

- Nếu `composer.json` đã sửa mà lock chưa cập nhật, `composer install` in cảnh báo lock không khớp.
- ⚠️ App phải commit `composer.lock`. Không có lock, mỗi lần CI/deploy chạy là một lần resolve mới:
  hôm nay ra `7.8.1`, tuần sau ra `7.9.0` có regression, và production khác với thứ bạn đã test.
- ⚠️ Chạy `composer update` trên server production là sai vì hai lẽ: phiên bản cài lên chưa ai test,
  và resolve tốn nhiều RAM/CPU. Production chỉ `install`.
- Library thì khác: lock của library **không** ảnh hưởng project dùng nó, vì project resolve dựa trên
  ràng buộc trong `composer.json` của library. Commit lock ở library chỉ để CI của chính library ổn định.
- *Platform package*: `"php": "^8.3"`, `"ext-redis": "*"` cũng là ràng buộc. Composer kiểm tra chúng
  khi cài và sinh `vendor/composer/platform_check.php` để báo lỗi sớm lúc runtime nếu server chạy
  sai bản PHP. Skeleton Laravel 13 yêu cầu `"php": "^8.3"`.

*Semver* (semantic versioning) quy ước phiên bản `MAJOR.MINOR.PATCH`: tăng MAJOR khi phá vỡ tương
thích, MINOR khi thêm tính năng tương thích ngược, PATCH khi sửa lỗi. Ràng buộc của Composer (theo
tài liệu *Versions and constraints*):

| Ràng buộc | Nghĩa | Ghi chú |
|---|---|---|
| `1.0.2` | Đúng bản này | Xung đột với package khác cần bản khác thì resolve thất bại |
| `>=1.0 <2.0` | Khoảng | Dấu cách hoặc dấu phẩy là AND, `\|\|` là OR |
| `1.0.*` | `>=1.0 <1.1` | Wildcard |
| `1.0 - 2.0` | `>=1.0.0 <2.1` | Vế phải thiếu phần thì được hiểu là wildcard `2.0.*` |
| `~1.2` | `>=1.2 <2.0.0` | `~` cho phép tăng **chữ số cuối cùng được viết ra** |
| `~1.2.3` | `>=1.2.3 <1.3.0` | Chữ số cuối là PATCH, nên chỉ PATCH được tăng |
| `^1.2.3` | `>=1.2.3 <2.0.0` | Mọi bản không đổi MAJOR. Composer khuyên dùng `^` |
| `^0.3` | `>=0.3.0 <0.4.0` | Với `0.x`, MINOR được coi là có thể phá vỡ |
| `^0.0.3` | `>=0.0.3 <0.0.4` | Với `0.0.x`, thực tế chỉ nhận đúng bản `0.0.3` |

Ví dụ: "nhận mọi bản 2.x từ 2.4 trở lên" viết `^2.4` (tương đương `>=2.4.0 <3.0.0`), hoặc `~2.4`.

- ⚠️ Ràng buộc không có cận trên như `>=1.0` hay `*` nghĩa là `composer update` có thể kéo về một bản
  MAJOR mới phá vỡ API.
- *Stability*: Composer mặc định chỉ nhận bản `stable` (`"minimum-stability": "stable"`). Muốn dùng bản
  beta của một package thì thêm flag `"vendor/pkg": "^2.0@beta"` thay vì hạ `minimum-stability` của cả
  project.
- `composer audit` kiểm tra các package trong lock có *security advisory* (thông báo lỗ hổng đã công
  bố) không, trả exit code khác 0 khi có. Chạy trong CI. `update` và `require` cũng tự in một bản tóm
  tắt audit ở cuối; các bản Composer gần đây còn có thể **chặn** cài bản có advisory ngay lúc resolve
  (cấu hình trong `config`, tên key thay đổi theo phiên bản, xem docs Composer).

#### Các PSR cần biết

PSR là chuẩn **interface**, không phải thư viện. Ví dụ PSR-3 chỉ định nghĩa `Psr\Log\LoggerInterface`;
Monolog là một cài đặt của nó. Code của bạn type-hint theo interface thì đổi thư viện cài đặt được mà
không sửa code gọi.

| PSR | Về gì | Gặp ở đâu |
|---|---|---|
| 1, 12, và PER Coding Style | Quy tắc định dạng code. PER CS là bản kế thừa, cập nhật tiếp PSR-12 cho cú pháp PHP mới | Pint, PHP-CS-Fixer (module 2.8) |
| 3 | `LoggerInterface` với 8 mức (debug tới emergency) | `Log` của Laravel là logger PSR-3 |
| 4 | Autoload | Mọi package Composer |
| 6, 16 | Cache (PSR-6 pool/item đầy đủ, PSR-16 simple cache `get/set`) | Cache repository Laravel implement PSR-16 |
| 7, 17 | HTTP message **bất biến** (immutable) và factory tạo chúng | Guzzle, Slim, nyholm/psr7 |
| 11 | Container: `get($id)`, `has($id)` | Container Laravel implement PSR-11 |
| 13 | Hypermedia link | Ít gặp |
| 14 | Event dispatcher | Symfony EventDispatcher |
| 15 | HTTP server handler và middleware (dạng `process($request, $handler)`) | Mezzio, Slim. Middleware Laravel **không** theo PSR-15 |
| 18 | HTTP client: `sendRequest(RequestInterface)` | Guzzle 7 |
| 20 | Clock: `ClockInterface::now()` trả `DateTimeImmutable` | Giả lập thời gian khi test |

PSR-0 (autoload cũ) và PSR-2 (coding style cũ) đã bị đánh dấu *deprecated*.

*Immutable* của PSR-7 nghĩa là mọi method "sửa" đều trả object **mới**:

```php
$req2 = $req->withHeader('X-Trace', 'abc');   // $req không đổi; phải dùng $req2
$req->withHeader('X-Trace', 'abc');           // ⚠️ bug: kết quả bị vứt, không có gì thay đổi
```

⚠️ `Illuminate\Http\Request` của Laravel kế thừa `Symfony\Component\HttpFoundation\Request`, là
object **mutable**: `$request->merge([...])`, `$request->headers->set(...)` sửa trực tiếp object. Nó
**không** implement PSR-7. Khi cần làm việc với thư viện đòi PSR-7, Laravel hỗ trợ type-hint
`Psr\Http\Message\ServerRequestInterface` trong route nếu cài `symfony/psr-http-message-bridge` và
một cài đặt PSR-7 như `nyholm/psr7`; bridge này chuyển đổi qua lại hai kiểu object.

Đối chiếu: Java có Maven/Gradle với file lock tương tự (Gradle lockfile), classpath thay cho
autoload (JVM nạp class lazy qua ClassLoader, rất giống ý tưởng autoload). Go dùng `go.mod` (ràng
buộc) và `go.sum` (hash), nhưng Go chọn bản **thấp nhất** thoả ràng buộc (*minimal version
selection*) thay vì cao nhất như Composer, nên build lặp lại được ngay cả khi không có lock.

**Tóm tắt nhanh**
- Autoload: PHP gọi hàm đã `spl_autoload_register` khi gặp class chưa có. Composer tra classmap, rồi
  PSR-4 (prefix dài nhất trước, `file_exists`), nhớ các lần tra hụt.
- PSR-4: prefix `App\` ↔ `app/`, phần còn lại thành thư mục, tên class thành file; hoa thường phải
  khớp (bẫy macOS vs Linux).
- Tối ưu: mức 1 `-o` (classmap, luôn bật ở prod), mức 2/A `-a` (chỉ classmap, cấm class runtime),
  mức 2/B `--apcu` (cache cả hụt); 2/A và 2/B loại trừ nhau.
- `install` đọc lock, `update` resolve lại và ghi lock. App commit lock; production chỉ `install --no-dev -o`.
- `^1.2.3` = `<2.0.0`, `~1.2` = `<2.0`, `~1.2.3` = `<1.3.0`, `^0.3` = `<0.4.0`.
- Request Laravel mutable, không phải PSR-7; PSR-7 immutable, dùng bridge khi cần.

**Nguồn**: [Composer: Basic usage](https://getcomposer.org/doc/01-basic-usage.md) ·
[Composer: Versions and constraints](https://getcomposer.org/doc/articles/versions.md) ·
[Composer: Autoloader optimization](https://getcomposer.org/doc/articles/autoloader-optimization.md) ·
[Composer: schema, autoload](https://getcomposer.org/doc/04-schema.md#autoload) ·
[Composer: CLI dump-autoload](https://getcomposer.org/doc/03-cli.md#dump-autoload-dumpautoload) ·
[composer/composer: ClassLoader.php](https://github.com/composer/composer/blob/main/src/Composer/Autoload/ClassLoader.php) ·
[PHP-FIG: PSR-4](https://www.php-fig.org/psr/psr-4/) · [PHP-FIG: danh sách PSR](https://www.php-fig.org/psr/) ·
[PER Coding Style](https://www.php-fig.org/per/coding-style/)


---

### 1.6 Laravel cơ bản

Module này trả lời: một project Laravel 11+ được tổ chức thế nào (và khác bản 10 trở về trước ở
đâu), request đi qua routing, middleware, validation, Eloquent ra sao, và ở mỗi bước có lỗ hổng bảo
mật phổ biến nào (IDOR, mass assignment, race condition của `unique`).

#### Skeleton từ Laravel 11

*Skeleton* là bộ khung thư mục của một project mới (`laravel new app` hoặc
`composer create-project laravel/laravel app`). Laravel 11 (03/2024) làm gọn skeleton đáng kể, và
Laravel 12, 13 giữ nguyên cấu trúc này:

```text
app/
  Http/Controllers/        controller (Middleware/, Requests/ chỉ xuất hiện khi make:...)
  Models/User.php
  Providers/AppServiceProvider.php   provider duy nhất mặc định
bootstrap/
  app.php                  cấu hình routing, middleware, exception handler
  providers.php            danh sách provider của app
  cache/                   file cache do framework sinh (config, routes, packages)
config/                    file cấu hình (đọc từ .env qua env())
database/migrations/ factories/ seeders/  (+ database.sqlite)
public/index.php           entry point của mọi HTTP request
routes/web.php             route web (có session, CSRF, cookie mã hoá)
routes/console.php         lệnh closure và lịch chạy (scheduler)
storage/                   log, view đã compile, session/cache dạng file
```

So với Laravel 10: không còn `app/Http/Kernel.php` (middleware), `app/Console/Kernel.php`
(scheduler), `app/Exceptions/Handler.php`; năm provider mặc định (App, Auth, Broadcast, Event, Route)
còn một `AppServiceProvider`. Phần cấu hình của chúng dồn vào `bootstrap/app.php`. File này trong skeleton Laravel 13:

```php
<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Request;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',                                   // route health check cho load balancer
    )
    ->withMiddleware(function (Middleware $middleware): void {
        // append/prepend global middleware, alias, web()/api() group...
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(
            fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
        );
    })->create();
```

Luồng khởi động rút gọn (chi tiết ở module 2.4):

```
public/index.php
  ├─ có storage/framework/maintenance.php? → đang bảo trì, trả 503
  ├─ require vendor/autoload.php            (module 1.5)
  ├─ $app = require bootstrap/app.php        tạo Application (cũng là service container)
  └─ $app->handleRequest(Request::capture())
        → HTTP kernel: bootstrap (env, config, HandleExceptions, provider...)
        → global middleware → router tìm route → middleware group/route → controller
        → response đi ngược qua middleware → gửi về client → terminate()
```

- `routes/api.php` **không có** sẵn. Chạy `php artisan install:api`: cài Laravel Sanctum (xác thực
  bằng token), tạo `routes/api.php`, và đăng ký nó vào `withRouting(api: ...)`. Route trong file này
  tự có prefix `/api` và thuộc middleware group `api` (không session, không CSRF).
- Scheduler khai báo trong `routes/console.php`, ví dụ `Schedule::command('reports:daily')->dailyAt('02:00');`.

Mặc định của app mới (theo `.env.example` của skeleton 13.x):

| Biến `.env` | Mặc định | Production thường đổi thành |
|---|---|---|
| `APP_ENV` / `APP_DEBUG` | `local` / `true` | `production` / `false` |
| `DB_CONNECTION` | `sqlite` (file `database/database.sqlite`, migrate sẵn lúc tạo project) | `mysql` + `DB_HOST`, `DB_PORT`, `DB_DATABASE`, `DB_USERNAME`, `DB_PASSWORD` |
| `QUEUE_CONNECTION` | `database` (bảng `jobs`) | `redis` |
| `CACHE_STORE` | `database` (bảng `cache`) | `redis` |
| `SESSION_DRIVER` | `database` (bảng `sessions`) | `redis` hoặc `database` |
| `REDIS_CLIENT` | `phpredis` (cần extension `redis`) | Giữ, hoặc `predis` (package Composer, không cần extension) |
| `LOG_LEVEL` | `debug` | `info` hoặc `warning` |

- ⚠️ Driver `database` cho queue, cache, session tiện cho dev vì không cần cài gì thêm, nhưng đặt toàn
  bộ tải lên cùng một DB với dữ liệu nghiệp vụ. Lên production với MySQL/Redis phải đổi các biến trên
  **tường minh**; quên đổi `QUEUE_CONNECTION` là worker vẫn poll bảng `jobs` trên MySQL.
- Đổi DB xong, tạo database rồi chạy `php artisan migrate`.
- ⚠️ `php artisan config:cache` (chạy lúc deploy) gộp mọi file config thành một file cache. Sau đó
  `env()` gọi **ngoài** thư mục `config/` trả `null`, vì `.env` không còn được đọc. Chỉ gọi `env()`
  trong file config, còn code dùng `config('...')`.

#### Routing và route model binding

Route khai báo trong `routes/web.php`:

```php
use App\Http\Controllers\PostController;
use Illuminate\Support\Facades\Route;

Route::get('/posts/{post}', [PostController::class, 'show'])->name('posts.show');

Route::middleware(['auth'])->prefix('admin')->name('admin.')->group(function (): void {
    Route::get('/users', [UserController::class, 'index'])->name('users');  // URL /admin/users, tên admin.users
});
```

*Route group* gom các route dùng chung thuộc tính. Khi lồng group: middleware và điều kiện `where`
được **gộp**, còn `prefix` và `name` được **nối** vào nhau. `php artisan route:list` in toàn bộ route
kèm middleware, dùng để kiểm tra một route thực sự có `auth` hay không.

*Route model binding*: thay vì nhận id rồi tự `Post::findOrFail($id)`, khai báo tham số có type-hint
model và Laravel tự tìm.

- *Implicit binding*: tên biến trùng tên segment (`{post}` và `Post $post`). Không tìm thấy thì 404.
- Tìm theo cột khác: `{post:slug}`. Muốn model luôn dùng cột khác, Laravel 13 có attribute
  `#[RouteKey('slug')]` trên model (hoặc override `getRouteKeyName()`).
- Model dùng soft delete: mặc định bản ghi đã xoá mềm không được tìm thấy; thêm `->withTrashed()` vào
  route nếu cần.
- Enum: type-hint một string-backed enum thì segment không phải giá trị hợp lệ sẽ trả 404.
- *Explicit binding*: khai báo trong `AppServiceProvider::boot()` bằng `Route::model('user', User::class)`
  hoặc tự viết logic với `Route::bind('user', fn (string $v) => User::where('name', $v)->firstOrFail())`.

Bên dưới, binding do **middleware** `Illuminate\Routing\Middleware\SubstituteBindings` làm (có sẵn trong
cả hai group `web` và `api`):

1. Router khớp URL với route, lấy các giá trị segment dạng chuỗi (`"42"`).
2. `SubstituteBindings` chạy explicit binding, rồi implicit binding: với mỗi tham số của controller có
   type-hint là model, gọi `$model->resolveRouteBinding($value, $field)`, mặc định là
   `where($field ?? getRouteKeyName(), $value)->first()`.
3. Kết quả `null` thì ném `ModelNotFoundException`; exception handler đổi nó thành 404 (có thể tuỳ biến
   bằng `->missing(fn ...)` trên route).
4. Object model thay thế chuỗi `"42"` trong tham số route, controller nhận model.

*Scoped binding* cho route lồng nhau: `/users/{user}/posts/{post}` mặc định **không** kiểm tra post có
thuộc user không. Laravel chỉ tự scope khi segment con dùng custom key (`{post:slug}`), hoặc khi bạn gọi
`->scopeBindings()`. Khi scope, post được tìm qua relationship `$user->posts()` (Laravel đoán tên
relationship là dạng số nhiều của tên segment).

⚠️ Binding chỉ trả lời "record này có tồn tại không", **không** trả lời "user hiện tại có được xem
không". Thiếu kiểm tra quyền là lỗ hổng *IDOR* (*Insecure Direct Object Reference*, tham chiếu trực
tiếp tới object không kiểm soát): đổi `/orders/1001` thành `/orders/1002` trên URL là xem được đơn của
người khác. Scoped binding cũng không thay được kiểm tra quyền: nó đảm bảo post thuộc `{user}` trên
URL, nhưng `{user}` do chính kẻ tấn công điền.

```php
use App\Models\Post;
use App\Models\User;

Route::get('/users/{user}/posts/{post}', function (User $user, Post $post) {
    return $post;
})->scopeBindings()              // post phải thuộc user trên URL, không thì 404
  ->middleware('can:view,post'); // và user đang đăng nhập phải có quyền xem (PostPolicy::view)
```

Hoặc trong controller: `$this->authorize('view', $post);` hay `Gate::authorize('view', $post);`.

#### Middleware

*Middleware* là lớp code bọc quanh controller: nhận request, có thể chặn lại (trả response luôn), sửa
request, hoặc cho đi tiếp bằng `$next($request)`, rồi xử lý response trên đường về. Nhiều middleware
xếp chồng thành *pipeline* hình củ hành:

```
request ─► [TrustProxies ─► ... ─► StartSession ─► auth ─► controller] 
response ◄─[TrustProxies ◄─ ... ◄─ StartSession ◄─ auth ◄──────┘
```

```php
<?php
declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final class AddRequestId
{
    public function handle(Request $request, Closure $next): Response
    {
        $id = $request->header('X-Request-Id') ?? bin2hex(random_bytes(8));  // TRƯỚC controller
        $response = $next($request);
        $response->headers->set('X-Request-Id', $id);                         // SAU controller
        return $response;
    }
}
```

Ba cấp đăng ký, tất cả trong `bootstrap/app.php` hoặc trên route:

| Cấp | Cách đăng ký | Áp cho |
|---|---|---|
| Global | `$middleware->append(X::class)` / `prepend()` | Mọi request, kể cả khi không khớp route nào |
| Group | `$middleware->web(append: [...])`, `api(...)`, `appendToGroup('name', [...])` | Mọi route trong file routes tương ứng |
| Route | `->middleware(X::class)` hoặc alias `->middleware('auth')` | Route hoặc group cụ thể |

Group mặc định (Laravel 13):

| Group `web` | Group `api` |
|---|---|
| `EncryptCookies`, `AddQueuedCookiesToResponse`, `StartSession`, `ShareErrorsFromSession`, `PreventRequestForgery` (chống CSRF), `SubstituteBindings` | Chỉ `SubstituteBindings` |

- ⚠️ Group `api` mặc định **không có** rate limit. Muốn giới hạn phải tự thêm `throttle:api` (và định
  nghĩa limiter `api`) hoặc `throttle:60,1` trên route.
- Global mặc định có `TrimStrings` và `ConvertEmptyStringsToNull`: chuỗi rỗng từ form thành `null`,
  nên field tuỳ chọn cần rule `nullable`.
- Alias có sẵn: `auth`, `guest`, `can`, `throttle`, `signed`, `verified`... Tham số truyền sau dấu hai
  chấm, nhiều tham số cách nhau dấu phẩy: `throttle:60,1` là 60 request mỗi 1 phút, `can:update,post`.
  Tham số tới `handle()` sau `$next`: `handle(Request $r, Closure $next, string $role)`.
- Thứ tự chạy theo thứ tự đăng ký, nhưng Laravel **sắp lại** theo danh sách *priority* cho các
  middleware có trong danh sách đó (ví dụ `StartSession` luôn trước `SubstituteBindings`, và
  `SubstituteBindings` trước `Authorize`, nên `can:view,post` nhận được model thật). Chỉnh bằng
  `$middleware->priority([...])`.
- *Terminable middleware*: có method `terminate($request, $response)`, chạy **sau** khi response đã gửi
  cho client (với PHP-FPM). Hợp cho việc ghi log nặng. Laravel tạo instance mới để gọi `terminate`,
  trừ khi đăng ký middleware là singleton.

#### Validation và Form Request

Cách nhanh: `$request->validate([...])` trong controller. Cách nên dùng khi logic nhiều: *Form
Request*, một class riêng (`php artisan make:request UpdatePostRequest`) gom kiểm tra quyền và kiểm
tra input. Type-hint nó trong controller, Laravel tự chạy trước khi vào controller.

```php
<?php
declare(strict_types=1);

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

final class UpdateProfileRequest extends FormRequest
{
    protected function prepareForValidation(): void
    {
        $this->merge(['email' => mb_strtolower((string) $this->input('email'))]);
    }

    public function authorize(): bool
    {
        return $this->user()->can('update', $this->route('user'));  // model đã được binding
    }

    /** @return array<string, mixed> */
    public function rules(): array
    {
        return [
            'name'       => ['bail', 'required', 'string', 'max:100'],
            'email'      => ['required', 'email', Rule::unique('users')->ignore($this->route('user'))],
            'team_id'    => ['nullable', 'integer', 'exists:teams,id'],
            'nickname'   => ['sometimes', 'string', 'max:30'],
        ];
    }
}
```

Thứ tự Laravel chạy (theo `ValidatesWhenResolvedTrait::validateResolved`):

1. `prepareForValidation()`: chuẩn hoá input (lưu ý: chạy **trước** cả `authorize`).
2. `authorize()`: trả `false` thì ném `AuthorizationException`, thành HTTP 403, controller không chạy.
3. Chạy `rules()` và các callable trong `after()` (kiểm tra thêm cần nhiều field cùng lúc).
4. Sai thì ném `ValidationException`: request thường thì redirect về trang trước kèm lỗi trong
   session; request mong JSON thì trả 422 kèm danh sách lỗi.
5. `passedValidation()`: hook sau khi qua.

Rule hay dùng:

| Rule | Ý nghĩa |
|---|---|
| `bail` | Dừng kiểm tra field này ở lỗi đầu tiên (các rule chạy theo thứ tự viết) |
| `sometimes` | Chỉ kiểm tra khi field **có mặt** trong input |
| `nullable` | Cho phép `null` (cần vì `ConvertEmptyStringsToNull`) |
| `exists:teams,id` | Giá trị phải có trong bảng `teams`, cột `id` |
| `Rule::unique('users')->ignore($user)` | Không trùng, trừ chính record đang sửa |

- ⚠️ Không bao giờ truyền input của người dùng vào `ignore()`; chỉ truyền id do hệ thống sinh (từ
  model). Docs Laravel cảnh báo đây là đường SQL injection.
- ⚠️ Lấy dữ liệu bằng `$request->validated()` hoặc `$request->safe()->only([...])`, không dùng
  `$request->all()`. `all()` trả **mọi** field client gửi, kể cả field không có trong `rules()`.
- Laravel 13 có attribute `#[FailOnUnknownFields]` trên Form Request (hoặc bật toàn cục bằng
  `FormRequest::failOnUnknownFields()`): field lạ không có trong rules làm validation thất bại. Thêm
  một lớp chặn mass assignment, nhưng không thay thế `$fillable`.

⚠️ Rule `unique` có *race condition* (kết quả phụ thuộc thứ tự hai request chạy xen nhau), vì nó chỉ
là một câu `SELECT COUNT(*)` chạy trước `INSERT`:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | Validate: `SELECT count(*) FROM users WHERE email='an@x.vn'` | | 0, qua |
| 2 | | Validate cùng câu đó | 0, qua (A chưa insert) |
| 3 | `INSERT INTO users ... 'an@x.vn'` | | Thành công |
| 4 | | `INSERT INTO users ... 'an@x.vn'` | Không có unique index: **hai tài khoản trùng email**. Có unique index: lỗi 1062 Duplicate entry |

Validation ở tầng app chỉ để trả thông báo lỗi đẹp cho trường hợp thường gặp. Hàng rào thật là
**unique index** ở DB (`$table->string('email')->unique();` trong migration), và code bắt
`Illuminate\Database\UniqueConstraintViolationException` để trả 422 thay vì 500. Cùng lý do, `exists`
không chống được việc record bị xoá ngay sau khi validate; dùng foreign key.

#### Eloquent cơ bản và mass assignment

*Eloquent* là ORM (*Object-Relational Mapping*, ánh xạ bảng sang object) theo mẫu *Active Record*: mỗi
bảng là một class model, mỗi dòng là một object, và chính object đó biết tự lưu (`$post->save()`).
Quy ước: model `Post` ứng với bảng `posts`, khoá chính `id`, có cột `created_at`/`updated_at`.

Relationship cơ bản:

```php
final class User extends Model
{
    public function posts(): HasMany { return $this->hasMany(Post::class); }        // posts.user_id
    public function profile(): HasOne { return $this->hasOne(Profile::class); }     // profiles.user_id
    public function roles(): BelongsToMany { return $this->belongsToMany(Role::class); } // bảng trung gian role_user
}
final class Post extends Model
{
    public function author(): BelongsTo { return $this->belongsTo(User::class, 'user_id'); }
}

$user->posts;                     // property: chạy query lần đầu, cache lại kết quả (Collection)
$user->posts()->where('published', true)->get();  // method: trả query builder, nối thêm điều kiện
```

*Eager loading*: `Post::with('author')->get()` nạp relationship bằng **một** query riêng
(`WHERE id IN (...)`) thay vì một query cho mỗi post khi duyệt vòng lặp (bài toán N+1). Chi tiết, cách
phát hiện bằng `Model::preventLazyLoading()`, và các biến thể ở
[03-database-sql.md, module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel).

*Mass assignment* (gán hàng loạt) là gán nhiều attribute một lần từ một array: `User::create($data)`,
`$user->fill($data)`, `$user->update($data)`. Nguy cơ: array đó đến từ request, và client gửi thêm
field bạn không lường trước.

Cách Eloquent quyết định một key có được gán không (`GuardsAttributes::isFillable`):

1. Model đang ở chế độ unguarded: được.
2. Key nằm trong danh sách fillable: được.
3. Key nằm trong danh sách guarded (hoặc guarded là `['*']`): không.
4. Còn lại: chỉ được nếu danh sách fillable **rỗng** (tức đang dùng kiểu blacklist).

Khai báo, hai cú pháp tương đương (Laravel 13 dùng attribute trong skeleton, property vẫn được hỗ trợ):

```php
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Attributes\Hidden;

#[Fillable(['name', 'email', 'password'])]      // whitelist: cách nên dùng
#[Hidden(['password', 'remember_token'])]       // không xuất hiện khi toArray()/JSON
final class User extends Authenticatable {}

// Cú pháp property, gặp nhiều ở code Laravel 12 trở về trước:
//   protected $fillable = ['name', 'email', 'password'];
//   protected $guarded  = ['is_admin'];         // blacklist
//   protected $guarded  = [];                   // TẮT bảo vệ hoàn toàn (tương đương #[Unguarded])
```

- Mặc định model không khai gì có `$guarded = ['*']`: **mọi** mass assignment ném
  `MassAssignmentException`. An toàn nhưng buộc bạn khai báo.
- Khi có whitelist, field không nằm trong đó bị **lặng lẽ bỏ qua**. Ở dev, bật
  `Model::preventSilentlyDiscardingAttributes($this->app->isLocal())` để nó ném exception, dễ phát hiện
  quên thêm field.

⚠️ Tấn công mass assignment:

```php
// Model: protected $guarded = [];      Bảng users có cột is_admin
public function register(Request $request)
{
    return User::create($request->all());   // client gửi thêm is_admin=1 → tự thành admin
}
```

Cần **cả hai** lớp: model khai whitelist (`$fillable`/`#[Fillable]`), và controller chỉ đưa dữ liệu đã
validate (`$request->validated()`). Blacklist (`$guarded = ['is_admin']`) mong manh: thêm cột
`role` sau này mà quên cập nhật blacklist là thủng.

#### Artisan và công cụ đi kèm

*Artisan* là CLI của Laravel (`php artisan list` in mọi lệnh). Những lệnh dùng hằng ngày:

| Lệnh | Việc |
|---|---|
| `php artisan about` | Tổng quan: phiên bản PHP/Laravel, môi trường, driver cache/queue/session/DB đang dùng, config/route đã cache chưa. Lệnh đầu tiên nên chạy khi nhận project lạ |
| `make:model Post -mfs` | Tạo model kèm migration, factory, seeder |
| `make:controller`, `make:request`, `make:middleware`, `make:policy` | Sinh class đúng chỗ, đúng namespace |
| `migrate`, `migrate:rollback`, `migrate:status` | Chạy/lùi migration, xem trạng thái |
| `db:seed` | Đổ dữ liệu mẫu từ seeder |
| `route:list` | Liệt kê route kèm middleware |
| `tinker` | REPL chạy code trong context app |
| `config:cache`, `route:cache`, `optimize` | Cache cấu hình và route lúc deploy (module 2.4) |

- *Migration*: file PHP mô tả thay đổi schema (`up()` và `down()`), được version cùng code. Bảng
  `migrations` trong DB ghi file nào đã chạy.
- *Seeder*: đổ dữ liệu ban đầu hoặc dữ liệu mẫu.
- *Factory*: sinh model giả (dùng Faker) cho test và seeder:
  `User::factory()->count(10)->has(Post::factory()->count(3))->create();`
- ⚠️ `migrate:fresh` xoá **toàn bộ** bảng rồi chạy lại từ đầu. Chỉ dùng ở dev; production dùng
  `migrate --force` (`--force` cần thiết vì Artisan hỏi xác nhận khi `APP_ENV=production`).

Đối chiếu: Laravel gần với Rails (Active Record, migration, generator). Spring Boot (Java) dùng
JPA/Hibernate theo mẫu *Data Mapper* (entity không tự lưu, có repository riêng) và cấu hình qua
annotation. Go thường không dùng framework toàn năng; router (`net/http` từ Go 1.22 có pattern
`GET /posts/{id}`) cộng middleware dạng `func(http.Handler) http.Handler`, cùng ý tưởng củ hành.

**Tóm tắt nhanh**
- Laravel 11+: `bootstrap/app.php` thay cho HTTP/Console Kernel và Exception Handler; `routes/api.php`
  chỉ có sau `install:api`. App mới mặc định SQLite và driver `database` cho queue/cache/session.
- Route model binding do middleware `SubstituteBindings` làm; chỉ kiểm tra tồn tại, không kiểm tra
  quyền. Chống IDOR bằng policy (`can:`, `authorize`), scoped binding chỉ là phụ.
- Middleware là pipeline củ hành: global → group → route, sắp lại theo priority. Group `api` không có
  throttle mặc định.
- Form Request: `prepareForValidation` → `authorize` (403) → `rules` (422/redirect). Lấy dữ liệu bằng
  `validated()`, không `all()`.
- `unique` có race condition; unique index ở DB là hàng rào cuối.
- Mass assignment: whitelist `$fillable`/`#[Fillable]` + `validated()`. `$guarded = []` cùng
  `$request->all()` là tự cấp quyền admin cho kẻ tấn công.

**Nguồn**: [Laravel: Directory Structure](https://laravel.com/docs/structure) ·
[Laravel: Installation](https://laravel.com/docs/installation) ·
[Laravel: Routing](https://laravel.com/docs/routing) (mục [Route Model Binding](https://laravel.com/docs/routing#route-model-binding)) ·
[Laravel: Middleware](https://laravel.com/docs/middleware) ·
[Laravel: Validation](https://laravel.com/docs/validation) (mục [Form Request](https://laravel.com/docs/validation#form-request-validation)) ·
[Laravel: Eloquent, Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment) ·
[laravel/laravel 13.x: bootstrap/app.php và .env.example](https://github.com/laravel/laravel/tree/13.x) ·
[laravel/framework: SubstituteBindings, GuardsAttributes, ValidatesWhenResolvedTrait](https://github.com/laravel/framework/tree/13.x/src/Illuminate)

---

## Chặng 2: Làm chủ

### 2.1 PHP hiện đại: 8.0 tới 8.5

Module này trả lời: từ 8.0 tới 8.5 PHP đã thêm những gì, mỗi tính năng giải bài toán nào mà code
PHP 7 phải viết vòng vèo, và khi nâng bản thì cái gì sẽ vỡ. Người phỏng vấn thường hỏi theo kiểu
"viết lại đoạn này bằng PHP 8.x" hoặc "nâng 8.1 lên 8.4 bạn gặp gì", nên phần dưới đi theo từng bản,
mỗi tính năng có ví dụ trước/sau.

#### Bảng tính năng theo bản

Mỗi bản PHP thường ra vào cuối tháng 11 (riêng 8.2 ra ngày 08/12/2022). Bảng dưới chỉ giữ cái hay bị hỏi; danh sách đầy đủ nằm trong file
`UPGRADING` của php-src và trang php.watch cho từng bản.

| Bản | Ngôn ngữ | Thư viện, runtime | Đổi hành vi / deprecation đáng nhớ |
|---|---|---|---|
| 8.0 (2020) | `match`, named arguments, nullsafe `?->`, constructor promotion, union type, `mixed`, `static` return, attributes, `throw` là biểu thức | JIT, `WeakMap`, `Stringable`, `str_contains`/`str_starts_with`/`str_ends_with` | So sánh chuỗi với số theo kiểu mới (`0 == 'a'` thành `false`), hàm built-in ném `TypeError`/`ValueError` thay vì warning, PDO mặc định `ERRMODE_EXCEPTION` |
| 8.1 (2021) | `enum`, `readonly` property, first-class callable `f(...)`, `never`, intersection type `A&B`, `new` trong giá trị mặc định | Fibers, `array_is_list` | Truyền `null` vào tham số không nullable của hàm built-in bị deprecated; float mất phần thập phân khi ép ngầm sang int bị deprecated |
| 8.2 (2022) | `readonly class`, DNF type `(A&B)\|null`, type đứng riêng `null`/`false`/`true`, constant trong trait | Extension `Random`, `#[\SensitiveParameter]` | Dynamic property deprecated; nội suy chuỗi `"${var}"` deprecated |
| 8.3 (2023) | Typed class constant, `#[\Override]`, `C::{$name}`, readonly được gán lại trong `__clone` | `json_validate()`, `str_increment()` | `++` trên chuỗi rỗng hoặc chuỗi không phải chữ-số (alphanumeric) bị deprecated; `get_class()` không tham số deprecated |
| 8.4 (2024) | Property hooks, asymmetric visibility, lazy objects, `#[\Deprecated]`, `new Foo()->bar()` | `array_find`/`array_find_key`/`array_any`/`array_all`, `mb_trim`, `BcMath\Number`, `Pdo\Mysql`, `Dom\HTMLDocument`, JIT viết lại trên IR | Implicit nullable (`string $s = null`) deprecated, bcrypt cost mặc định 10 lên 12, `E_STRICT` bị bỏ, `exit()` hành xử như hàm |
| 8.5 (2025) | Pipe `\|>`, clone with, `#[\NoDiscard]` + cast `(void)`, closure và first-class callable trong constant expression, `final` cho promoted property, `#[\Override]` cho property, asymmetric visibility cho static property | `array_first`/`array_last`, extension URI (`Uri\Rfc3986\Uri`, `Uri\WhatWg\Url`), backtrace cho fatal error, OPcache luôn được build vào binary, INI `max_memory_limit` | Backtick `` `ls` `` deprecated, cast `(integer)`/`(boolean)`/`(double)`/`(binary)` deprecated, `null` làm key mảng deprecated, `case X;` (chấm phẩy) deprecated, `__sleep`/`__wakeup` soft-deprecated |

Mốc hỗ trợ (09/2026): 8.5 là bản mới nhất, 8.4 còn active support tới hết 2026. Laravel 13 cần PHP
≥ 8.3, nên mọi tính năng tới 8.3 dùng được trong mọi dự án Laravel 13.

#### PHP 8.0: match, named arguments, nullsafe, promotion

*`match`* là biểu thức chọn giá trị, thay cho `switch` trong đa số trường hợp. Khác `switch` ở bốn
điểm, và cả bốn đều là lý do nên dùng nó:

| | `switch` | `match` |
|---|---|---|
| So sánh | `==` (lỏng) | `===` (chặt) |
| Là biểu thức, gán được | Không | Có |
| Fall-through khi quên `break` | Có | Không có khái niệm `break` |
| Không nhánh nào khớp | Im lặng bỏ qua | Ném `UnhandledMatchError` |

```php
<?php
declare(strict_types=1);

$code = 404;
$kind = match (true) {                 // match(true): mỗi nhánh là một điều kiện
    $code >= 500 => 'server error',
    $code >= 400 => 'client error',
    default      => 'ok',
};
echo $kind, "\n";                      // client error

echo match ('1') { 1 => 'int', '1' => 'string' }, "\n";   // string  (switch sẽ khớp nhánh 1)

$status = 'refunded';
echo match ($status) {
    'paid', 'shipped' => 'đã thanh toán',                  // nhiều giá trị một nhánh
    'pending'         => 'chờ',
};                                                         // UnhandledMatchError: 'refunded' không có nhánh
```

⚠️ Thiếu `default` mà giá trị lạ lọt vào là exception trên production. Với enum thì đây lại là điểm
mạnh: thêm case mới mà quên xử lý thì lỗi lộ ngay chứ không âm thầm đi nhánh sai.

*Named arguments* là truyền tham số theo tên thay vì theo vị trí. Giải hai bài: bỏ qua các tham số có
giá trị mặc định ở giữa, và làm lời gọi tự giải thích (`true, false, true` không ai hiểu).

```php
<?php
declare(strict_types=1);

function makeUser(string $name, int $age = 18, bool $active = true): string
{
    return sprintf('%s/%d/%s', $name, $age, $active ? 'on' : 'off');
}

echo makeUser('An', active: false), "\n";         // An/18/off   (bỏ qua $age)
echo makeUser(age: 30, name: 'Bình'), "\n";        // Bình/30/on  (đổi thứ tự thoải mái)
echo makeUser(...['name' => 'Chi', 'age' => 20]), "\n";  // Chi/20/on (unpack mảng key chuỗi = named)
echo htmlspecialchars('&amp;', double_encode: false), "\n"; // &amp;  (hàm built-in cũng dùng được)

// makeUser(name: 'An', 25);    // Fatal error lúc compile: positional sau named
// makeUser('An', nme: 'x');    // Error: Unknown named parameter $nme
```

⚠️ Named arguments biến **tên tham số thành một phần của API**. Thư viện đổi `$name` thành
`$fullName` là làm vỡ mọi chỗ gọi `name: ...`. Class con đổi tên tham số khi override cũng vậy: gọi
bằng tên của class cha trên object con sẽ ném `Error`. Đây là lý do một số thư viện ghi rõ "không
đảm bảo tương thích tên tham số".

*Nullsafe `?->`*: nếu vế trái là `null` thì cả chuỗi phía sau bị bỏ qua và biểu thức trả `null`
(gọi là *short-circuit*, ngắt mạch). Tham số của các lời gọi phía sau cũng không được tính.

```php
<?php
declare(strict_types=1);

// PHP 7
$city = null;
if ($order !== null && $order->customer !== null && $order->customer->address !== null) {
    $city = $order->customer->address->city;
}
// PHP 8
$city = $order?->customer?->address?->city;
```

- ⚠️ Chỉ dùng để đọc. `$order?->status = 'paid'` là lỗi compile, vì không có gì để gán khi `$order`
  là `null`.
- So với `??`: `??` xử lý biến/key/property **không tồn tại** (không phát warning), còn `?->` chỉ xử
  lý giá trị `null` khi gọi method/đọc property. Hay dùng chung: `$user?->profile?->nickname ?? 'khách'`.

*Constructor promotion*: khai báo property ngay trong tham số constructor. Vừa ngắn, vừa hết lỗi quên
gán một field.

```php
<?php
declare(strict_types=1);

final class OrderService
{
    public function __construct(
        private readonly OrderRepository $orders,   // khai báo + gán trong một dòng
        private readonly Clock $clock = new SystemClock(),  // 8.1: new trong giá trị mặc định
    ) {}
}
```

Các mảnh khác của 8.0 nên biết: union type `int|string`, `mixed`, `static` làm return type (cho
fluent API), `throw` là biểu thức (`$id = $input['id'] ?? throw new InvalidArgumentException('thiếu id');`),
`$obj::class`, `str_contains`. Thay đổi làm vỡ code nhiều nhất của 8.0 là so sánh chuỗi với số:
`0 == 'abc'` là `true` ở PHP 7 và `false` từ 8.0 (xem module 1.1).

#### PHP 8.1: enum, readonly, first-class callable

*Enum* là kiểu có tập giá trị cố định và được kiểm tra bởi type system. Trước 8.1 người ta dùng hằng
số `const PAID = 'paid'`, nên hàm nhận `string $status` chấp nhận cả `'banana'`.

- *Pure enum*: `enum Suit { case Hearts; case Spades; }`, case không gắn giá trị.
- *Backed enum*: `enum Status: string { case Paid = 'paid'; }`, mỗi case gắn một `int` hoặc `string`
  duy nhất, dùng khi cần lưu DB hoặc trao đổi qua JSON.

```php
<?php
declare(strict_types=1);

interface HasLabel { public function label(): string; }

enum Status: string implements HasLabel
{
    case Pending = 'pending';
    case Paid    = 'paid';
    case Refunded = 'refunded';

    const DEFAULT = self::Pending;          // enum có constant được

    public function label(): string         // method được
    {
        return match ($this) {              // quên một case là UnhandledMatchError
            self::Pending  => 'Chờ thanh toán',
            self::Paid     => 'Đã thanh toán',
            self::Refunded => 'Đã hoàn tiền',
        };
    }

    public function isFinal(): bool
    {
        return $this === self::Paid || $this === self::Refunded;
    }
}

var_dump(Status::from('paid'));          // enum(Status::Paid)
var_dump(Status::tryFrom('banana'));     // NULL
var_dump(Status::Paid->value);           // string(4) "paid"
var_dump(Status::Paid->name);            // string(4) "Paid"
var_dump(Status::from('paid') === Status::Paid);  // bool(true): mỗi case là một object duy nhất
var_dump(count(Status::cases()));        // int(3)
echo Status::DEFAULT->label(), "\n";     // Chờ thanh toán
// Status::from('banana');               // ValueError
```

- `from()` dùng khi dữ liệu **phải** hợp lệ (đọc từ DB của chính mình): sai là lỗi thật, nên ném.
  `tryFrom()` dùng với input người dùng, rồi tự xử lý `null`.
- Enum **không có state**: không khai báo property, không `new`, không clone. Mỗi case là một
  singleton, nên so sánh bằng `===` là đủ.
- Mọi enum implement `UnitEnum`; backed enum implement thêm `BackedEnum`. Dùng để type-hint code dùng
  chung cho mọi enum.
- ⚠️ Enum là object nên **không làm key mảng** được (`$map[Status::Paid]` ném `TypeError`). Dùng
  `$map[Status::Paid->value]` hoặc `SplObjectStorage`/`WeakMap`.
- ⚠️ Enum không có thứ tự: `Status::Paid < Status::Refunded` vô nghĩa. Muốn thứ tự thì viết method
  `rank(): int`.
- Laravel: cast `'status' => Status::class` trên model tự đổi cột DB thành enum, route binding và
  rule validation `Rule::enum(Status::class)` cũng hiểu enum.

*`readonly` property* chỉ được gán **đúng một lần**, sau đó mọi phép gán (kể cả từ trong class) ném
`Error`. Quy tắc:

1. Bắt buộc có type (`public readonly int $x`, không được `public readonly $x`).
2. Không có giá trị mặc định ở khai báo (giá trị mặc định của tham số promoted thì được).
3. Chỉ được khởi tạo từ bên trong class. Tới 8.3 là "chỉ class khai báo"; từ 8.4 readonly ngầm định
   là `protected(set)` nên class con cũng khởi tạo được.
4. Không `unset()` được sau khi đã gán.

```php
<?php
declare(strict_types=1);

final class Money
{
    public function __construct(
        public readonly int $amount,
        public readonly string $currency,
        public readonly \ArrayObject $tags = new \ArrayObject(),
    ) {}
}

$m = new Money(100, 'VND');
// $m->amount = 200;          // Error: Cannot modify readonly property Money::$amount
$m->tags->append('sale');     // CHẠY ĐƯỢC: readonly là nông
var_dump(count($m->tags));    // int(1)
```

⚠️ Readonly là **nông** (shallow): nó khoá việc gán lại property, không khoá nội dung object mà
property trỏ tới. Value object thật sự bất biến thì các field object bên trong cũng phải bất biến
(`DateTimeImmutable` thay vì `DateTime`, không dùng `ArrayObject`). Mảng thì an toàn hơn vì mảng
được copy theo giá trị: `$m->list[] = 1` trên property readonly kiểu `array` ném `Error`.

*First-class callable* `f(...)`: tạo một `Closure` từ hàm hoặc method bằng cú pháp gọi hàm với `...`
làm tham số.

```php
<?php
declare(strict_types=1);

$lengths = array_map(strlen(...), ['a', 'bb', 'ccc']);   // [1, 2, 3]

final class Importer
{
    /** @param list<string> $rows */
    public function run(array $rows): array
    {
        // PHP 7: array_filter($rows, [$this, 'isValid']) - chuỗi/mảng, IDE không theo dấu được
        return array_filter($rows, $this->isValid(...));   // private method vẫn gọi được
    }

    private function isValid(string $row): bool { return $row !== ''; }
}
```

Vì sao hơn callable dạng chuỗi `'strlen'` hay mảng `[$this, 'isValid']`: IDE và PHPStan hiểu được đó
là hàm nào (rename, find usages chạy đúng), scope được chốt tại chỗ tạo (callable mảng trỏ tới private
method mà truyền sang chỗ khác gọi sẽ lỗi), và gõ sai tên lỗi ngay tại dòng đó.

Các mảnh khác của 8.1: `never` (hàm không bao giờ trả về, luôn ném hoặc `exit`), intersection type
`Countable&Iterator`, `array_is_list()`, Fibers (nhóm riêng bên dưới).

#### PHP 8.2 và 8.3: readonly class, DNF, typed constant, Override

- *`readonly class`* (8.2): mọi property của class thành readonly, và class đó không có dynamic
  property. Mọi property phải có type.
- *DNF type* (Disjunctive Normal Form, 8.2): kết hợp union và intersection, `(Countable&Iterator)|null`.
- *Type `null`, `false`, `true` đứng riêng* (8.2): ví dụ `function isOk(): true`.
- *`#[\SensitiveParameter]`* (8.2): tham số gắn attribute này bị thay bằng `SensitiveParameterValue`
  trong stack trace, nên mật khẩu không lọt vào log lỗi.
- *Typed class constant* (8.3): `const string TABLE = 'users';`. Class con override constant phải giữ
  type tương thích.
- *`#[\Override]`* (8.3): gắn lên method để khẳng định "method này ghi đè method của cha/interface".
  Nếu cha đổi tên hoặc xoá method đó, PHP báo lỗi lúc compile thay vì để method con thành một method
  mồ côi không ai gọi.

  ```php
  final class JsonLogger extends BaseLogger
  {
      #[\Override]
      public function format(string $msg): string { return json_encode(['m' => $msg], JSON_THROW_ON_ERROR); }
  }
  ```
- *`json_validate()`* (8.3): kiểm tra chuỗi có phải JSON hợp lệ mà không dựng mảng/object kết quả,
  tốn ít bộ nhớ hơn `json_decode()` rồi kiểm tra lỗi.
- *Dynamic class constant fetch* (8.3): `Status::{$name}` thay cho `constant(Status::class . '::' . $name)`.
- Readonly được gán lại **trong `__clone()`** (8.3). Giúp deep-clone field object của value object,
  nhưng không giải bài wither vì `__clone()` không nhận tham số (xem clone with ở 8.5).

#### PHP 8.4: property hooks, asymmetric visibility, lazy objects

*Property hooks* là logic `get`/`set` gắn thẳng lên property. Bên ngoài vẫn đọc ghi `$obj->email`
như property thường, bên trong có kiểm tra/biến đổi. Thay cho cặp `getEmail()`/`setEmail()` viết tay,
và thay cho magic `__get`/`__set` mà IDE không hiểu.

```php
<?php
declare(strict_types=1);

final class User
{
    public string $email {
        set(string $value) {
            if (!str_contains($value, '@')) {
                throw new \InvalidArgumentException("Email không hợp lệ: $value");
            }
            $this->email = strtolower($value);   // $this->email trong hook = giá trị thật (backing value)
        }
    }

    // Virtual property: không hook nào dùng $this->domain, nên không có ô nhớ riêng
    public string $domain {
        get => explode('@', $this->email, 2)[1];
    }

    public function __construct(string $email)
    {
        $this->email = $email;                   // đi qua set hook
    }
}

$u = new User('An@Example.COM');
echo $u->email, "\n";        // an@example.com
echo $u->domain, "\n";       // example.com
// $u->domain = 'x';         // Error: property virtual chỉ có get thì không ghi được
// $u->email = 'khong-hop-le'; // InvalidArgumentException
```

- *Backed property*: có ít nhất một hook dùng `$this->tênProperty`, nên có ô nhớ thật. *Virtual
  property*: không hook nào dùng, nên không có ô nhớ, giống một method trá hình.
- Dạng ngắn: `set => strtolower($value);` nghĩa là giá trị của biểu thức được ghi vào backing value.
- Interface khai báo được property: `interface HasName { public string $name { get; } }`. Đây là thay
  đổi lớn về thiết kế: trước 8.4 interface chỉ có method.
- ⚠️ Hook **không đi cùng `readonly`** (lỗi compile). Muốn "đọc công khai, ghi có kiểm soát" thì dùng
  asymmetric visibility hoặc set hook.
- ⚠️ Property kiểu mảng có `set` hook thì không sửa từng phần tử được: `$obj->items[] = 1` ném `Error`,
  vì sửa tại chỗ sẽ đi vòng qua hook. Phải gán cả mảng mới: `$obj->items = [...$obj->items, 1]`.
- Khi nào dùng: chuẩn hoá/kiểm tra khi gán, property dẫn xuất (`fullName`). Không nên nhét logic nặng
  (query DB) vào `get`: người đọc code thấy `$x->total` sẽ nghĩ đó là phép đọc rẻ.

*Asymmetric visibility*: quyền đọc và quyền ghi khác nhau, cú pháp `public private(set)`.

```php
<?php
declare(strict_types=1);

final class Cart
{
    public private(set) int $count = 0;          // ngoài đọc được, chỉ Cart ghi
    private(set) array $items = [];              // viết tắt: bỏ "public" ở vế đọc

    public function add(string $sku): void
    {
        $this->items[] = $sku;
        $this->count++;
    }
}

$c = new Cart();
$c->add('A1');
echo $c->count, "\n";          // 1
// $c->count = 99;             // Error: Cannot modify private(set) property Cart::$count from global scope
// $c->items[] = 'B2';         // Error: sửa mảng cần quyền set
```

- Chỉ dùng được với property có type.
- Property `private(set)` tự động là `final` (class con không khai báo lại được).
- Từ 8.4, `readonly` ngầm định nghĩa là `protected(set)`. Tức `public readonly int $x` = "đọc public,
  ghi một lần, từ class này hoặc class con".
- ⚠️ Giống readonly, giới hạn chỉ áp lên việc **gán lại** property; object mà property trỏ tới vẫn sửa
  được qua method của nó.
- So với readonly: readonly là "ghi một lần rồi khoá", `private(set)` là "class tự ghi bao nhiêu lần
  cũng được, bên ngoài chỉ đọc". Entity có state thay đổi (bộ đếm, trạng thái) hợp `private(set)`;
  value object hợp readonly.

*Lazy objects*: object mà việc khởi tạo thật bị hoãn tới lần đầu có ai đọc/ghi property của nó. Tạo
qua Reflection:

```php
<?php
declare(strict_types=1);

final class Report
{
    public array $rows;
    public function __construct(int $id) { echo "load $id\n"; $this->rows = [1, 2, 3]; }
}

$ref = new \ReflectionClass(Report::class);
$report = $ref->newLazyGhost(function (Report $r): void {
    $r->__construct(42);                  // chỉ chạy khi object được dùng tới
});
echo "đã tạo\n";                          // đã tạo      (chưa có "load 42")
echo count($report->rows), "\n";          // load 42 \n 3
```

- *Ghost*: chính object đó được khởi tạo tại chỗ. *Proxy* (`newLazyProxy`): lần đầu dùng mới tạo object
  thật và chuyển mọi truy cập sang nó; `$proxy === $real` là `false`.
- Dành cho framework: DI container (service chỉ khởi tạo khi thật sự được gọi), ORM (entity chưa load
  từ DB). Trước 8.4 Doctrine/Symfony phải sinh code proxy; giờ engine làm sẵn.

*Các mảnh khác của 8.4*

```php
<?php
declare(strict_types=1);

$users = [['id' => 1, 'active' => false], ['id' => 2, 'active' => true]];
$isActive = static fn(array $u): bool => $u['active'];

var_dump(array_find($users, $isActive)['id']);   // int(2)   phần tử đầu tiên thoả, không có thì NULL
var_dump(array_find_key($users, $isActive));     // int(1)
var_dump(array_any($users, $isActive));          // bool(true)
var_dump(array_all($users, $isActive));          // bool(false)

$len = new ArrayObject([1, 2])->count();         // 8.4: bỏ được cặp ngoặc quanh new Foo()
var_dump($len);                                  // int(2)
```

- `new Foo()->bar()` chỉ hợp lệ khi có `()` sau tên class; `new Foo->bar()` vẫn là lỗi cú pháp.
- `#[\Deprecated('dùng sendV2()', since: '3.0')]` gắn lên hàm/method/constant của chính bạn: gọi tới là
  phát `E_USER_DEPRECATED`, giống hệt hàm built-in bị deprecated.
- `password_hash()` với `PASSWORD_BCRYPT`/`PASSWORD_DEFAULT` mặc định cost 12 (trước là 10): hash chậm
  hơn khoảng 4 lần. Hash cũ vẫn verify được; `password_needs_rehash()` sẽ trả `true` cho hash cost 10.
- `Pdo\Mysql`, `Pdo\Pgsql`: subclass PDO theo driver, tạo bằng `PDO::connect()`. Tới 8.5 hằng
  `PDO::MYSQL_ATTR_*` bị deprecated để chuyển sang `Pdo\Mysql::ATTR_*`.
- `BcMath\Number` dùng được toán tử `+ - * /` với số thập phân chính xác.

⚠️ Deprecation hay gặp nhất khi lên 8.4 là *implicit nullable*: `function find(string $id = null)`
ngầm hiểu `$id` là `?string`. Sửa thành `?string $id = null`. Rector có rule tự sửa.

#### PHP 8.5: pipe, clone with, NoDiscard, URI

*Pipe operator `|>`*: lấy giá trị bên trái làm **tham số duy nhất** cho callable bên phải. Chuỗi xử lý
đọc từ trên xuống, thay vì đọc hàm lồng từ trong ra ngoài.

```php
<?php
declare(strict_types=1);

$title = '  PHP 8.5 Released  ';

// Trước 8.5: đọc từ trong ra ngoài
$slug = strtolower(str_replace(' ', '-', str_replace('.', '', trim($title))));

// 8.5
$slug = $title
    |> trim(...)
    |> (fn(string $s): string => str_replace('.', '', $s))   // arrow function PHẢI có ngoặc
    |> (fn(string $s): string => str_replace(' ', '-', $s))
    |> strtolower(...);

var_dump($slug);   // string(15) "php-85-released"
```

- Callable bên phải phải nhận được đúng một tham số. Hàm cần nhiều tham số (`str_replace`) phải bọc
  trong arrow function như trên.
- ⚠️ Arrow function trong pipe **bắt buộc có ngoặc**. Không có ngoặc thì arrow function "nuốt" hết
  phần còn lại của chuỗi pipe; quy tắc này được thêm sau khi RFC đã thông qua (errata 08/2025).
- ⚠️ Không dùng được hàm nhận tham số theo reference (`sort(...)`, `array_push(...)`) bên phải: báo lỗi.
- Pipe được compiler biến thành các lời gọi tuần tự, nên với `f(...)` gần như không tốn thêm chi phí;
  arrow function bọc ngoài thì tốn thêm một closure mỗi bước.
- Thứ tự ưu tiên: pipe chạy sau toán tử số học, trước phép so sánh và `??`. Nên
  `'beep' |> strlen(...) === 4` là `true`, và `$id |> findName(...) ?? 'khách'` áp `??` lên kết quả
  cả chuỗi.

*Clone with*: `clone` giờ là một hàm nhận thêm mảng property cần gán lại, `clone($obj, ['x' => 1])`.
Giải bài *wither* của value object readonly. Toàn bộ tiến hoá của một value object:

```php
<?php
declare(strict_types=1);

// PHP 7.4: private + getter + wither, clone rồi gán vì property không readonly
final class MoneyV7
{
    private int $amount;
    private string $currency;
    public function __construct(int $amount, string $currency) { $this->amount = $amount; $this->currency = $currency; }
    public function amount(): int { return $this->amount; }
    public function withAmount(int $amount): self { $c = clone $this; $c->amount = $amount; return $c; }
}

// PHP 8.2 (readonly class; 8.1 thì readonly từng property): wither phải gọi lại constructor và liệt kê MỌI field
final readonly class MoneyV82
{
    public function __construct(public int $amount, public string $currency) {}
    public function withAmount(int $amount): self { return new self($amount, $this->currency); }
}

// PHP 8.5: clone with, chỉ nêu field đổi
final readonly class Money
{
    public function __construct(public int $amount, public string $currency) {}
    public function withAmount(int $amount): static { return clone($this, ['amount' => $amount]); }
}

$a = new Money(100, 'VND');
$b = $a->withAmount(200);
var_dump($a->amount, $b->amount, $a === $b);   // int(100) int(200) bool(false)
// clone($a, ['amount' => 1]);                  // Error từ bên ngoài: readonly ngầm là protected(set)
```

Cơ chế, theo RFC:

1. Tạo bản sao nông của object (như `clone` cũ).
2. Gọi `__clone()` nếu có (chạy **trước** khi gán property mới).
3. Gán từng cặp key/value theo thứ tự trong mảng, như phép gán bình thường nhưng "mở khoá" readonly:
   visibility vẫn được kiểm tra, set hook vẫn chạy, type vẫn được kiểm tra. Lỗi ở key nào thì dừng
   tại key đó.

- ⚠️ Visibility vẫn áp dụng: code bên ngoài không dùng clone with để sửa property private/readonly
  được. Chỉ property `public` (không readonly) hoặc `public(set)` mới sửa được từ ngoài.
- ⚠️ Vẫn là bản sao nông: field object bên trong vẫn dùng chung giữa bản cũ và bản mới.
- Vì `clone` là hàm, dùng được làm callable: `array_map(clone(...), $objects)`.
- Khi nào dùng cách nào: `private(set)` cho entity có state đổi qua method; readonly + clone with cho
  value object (Money, DateRange); readonly + `new self(...)` khi cần chạy lại validation của
  constructor (clone with không gọi constructor).

*`#[\NoDiscard]`* đánh dấu hàm mà bỏ qua giá trị trả về gần như chắc chắn là bug. Gọi mà không dùng kết
quả sẽ phát warning (`E_USER_WARNING` với hàm của bạn, `E_WARNING` với hàm built-in). Cố ý bỏ qua thì
viết `(void)`:

```php
<?php
declare(strict_types=1);

#[\NoDiscard('kết quả cho biết có ghi được hay không')]
function tryWrite(string $path, string $data): bool
{
    return file_put_contents($path, $data) !== false;
}

tryWrite('/tmp/a.txt', 'x');           // Warning: giá trị trả về nên được dùng...
(void) tryWrite('/tmp/a.txt', 'x');    // cố ý bỏ qua, không warning
$ok = tryWrite('/tmp/a.txt', 'x');     // dùng kết quả, không warning
```

Bẫy mà RFC nêu làm ví dụ: `DateTimeImmutable::setTime()` và các method `set*()` khác không sửa object
mà trả về object mới, nên `$d->setTime(0, 0);` không gán lại là một dòng không làm gì. Loại hàm cần
gắn `#[\NoDiscard]` là hàm trả về kết quả quan trọng (thành công/thất bại, object mới) mà người gọi
dễ quên.

*URI extension*: parse URL theo chuẩn, thay cho `parse_url()` vốn không theo chuẩn nào và parse khác
trình duyệt ở nhiều ca biên (nguồn gốc của lỗi SSRF khi kiểm tra host).

```php
<?php
declare(strict_types=1);

use Uri\Rfc3986\Uri;

$uri = new Uri('https://php.net/releases/8.5/en.php');
var_dump($uri->getHost());   // string(7) "php.net"
// Uri\WhatWg\Url: parse giống hệt trình duyệt (chuẩn WHATWG), hợp khi kiểm tra URL người dùng nhập
```

*Các mảnh khác của 8.5*

- `array_first()`/`array_last()`: phần tử đầu/cuối bất kể key, mảng rỗng trả `null`.
  `array_first(['b' => 2, 'a' => 1])` là `2`.
- Closure trong constant expression: dùng được làm tham số attribute, giá trị mặc định của tham số.
  Closure phải `static`, không `use`, không dùng arrow function.
- Fatal error (ví dụ hết `max_execution_time`) giờ kèm backtrace: biết request chết ở hàm nào mà không
  cần slow log.
- OPcache luôn được build vào binary (không còn file `opcache.so`); vẫn bật/tắt bằng `opcache.enable`.
- `final` cho promoted property, `#[\Override]` cho property, `max_memory_limit` (INI đặt lúc khởi động,
  chặn code nâng `memory_limit` vượt trần).

#### Deprecation sẽ gặp khi nâng cấp

Deprecation không làm dừng chương trình, chỉ phát `E_DEPRECATED`. Nhưng nó thành lỗi thật khi error
handler của app biến mọi notice thành exception, khi test suite cấu hình fail trên deprecation
(PHPUnit `failOnDeprecation`), và chắc chắn thành lỗi ở bản major tiếp theo (PHP 9).

| Từ bản | Deprecation | Sửa |
|---|---|---|
| 8.1 | Truyền `null` vào tham số không nullable của hàm built-in: `strlen(null)`, `trim($maybeNull)` | `trim($s ?? '')`, hoặc sửa để giá trị không null từ nguồn |
| 8.1 | Implement `Serializable` mà không có `__serialize`/`__unserialize` | Thêm hai method mới |
| 8.2 | Dynamic property `$this->foo = 1` khi chưa khai báo `$foo` | Khai báo property; `#[\AllowDynamicProperties]` chỉ là cách tạm; `WeakMap` nếu gắn dữ liệu vào object của thư viện khác |
| 8.2 | `"${name}"` trong chuỗi | `"{$name}"` |
| 8.4 | Implicit nullable `string $s = null` | `?string $s = null` |
| 8.4 | `trigger_error(..., E_USER_ERROR)` | Ném exception |
| 8.5 | Backtick `` `ls -la` `` | `shell_exec('ls -la')` |
| 8.5 | Cast `(integer)`, `(boolean)`, `(double)` | `(int)`, `(bool)`, `(float)` |
| 8.5 | `null` làm key mảng, `array_key_exists(null, $a)` | Dùng `''` nếu thật sự cần |

Quy trình nâng bản an toàn: chạy test với `error_reporting=E_ALL` và log deprecation; chạy PHPStan với
`phpVersion` mới; dùng Rector (`LevelSetList::UP_TO_PHP_84`) để sửa hàng loạt; kiểm tra
`composer why-not php 8.5` để biết package nào chặn.

#### Attributes

*Attribute* là metadata có cấu trúc gắn lên class, method, property, tham số, constant, viết
`#[Tên(tham số)]`. Thay cho annotation trong docblock (`@Route("/users")`) vốn chỉ là comment mà thư
viện phải tự parse.

Attribute **tự nó không làm gì**. Phải có code đọc nó bằng Reflection rồi hành động:

```php
<?php
declare(strict_types=1);

#[\Attribute(\Attribute::TARGET_METHOD)]
final class Route
{
    public function __construct(public string $path, public string $method = 'GET') {}
}

final class UserController
{
    #[Route('/users')]
    public function index(): void {}

    #[Route('/users', method: 'POST')]
    public function store(): void {}
}

foreach ((new \ReflectionClass(UserController::class))->getMethods() as $m) {
    foreach ($m->getAttributes(Route::class) as $attr) {
        $route = $attr->newInstance();          // lúc này mới chạy constructor của Route
        echo "{$route->method} {$route->path} -> {$m->getName()}\n";
    }
}
// GET /users -> index
// POST /users -> store
```

- ⚠️ `getAttributes()` không kiểm tra gì; lỗi (class attribute không tồn tại, sai target, sai tham số)
  chỉ lộ ra khi gọi `newInstance()`.
- Attribute của engine có tác dụng thật vì engine tự đọc: `#[\Override]`, `#[\Deprecated]`,
  `#[\NoDiscard]`, `#[\SensitiveParameter]`, `#[\AllowDynamicProperties]`.
- Laravel dùng ngày càng nhiều: `#[ObservedBy(UserObserver::class)]` trên model,
  `#[Tries(5)]` (`Illuminate\Queue\Attributes\Tries`) trên job ở Laravel 13.
- Framework thường cache kết quả đọc attribute (Reflection không rẻ nếu chạy mỗi request).

#### Generator và iterator

*Generator* là hàm có `yield`. Gọi hàm không chạy thân hàm ngay, mà trả về một object `Generator`. Mỗi
lần được hỏi giá trị tiếp theo, thân hàm chạy tới `yield` kế tiếp, trả giá trị ra rồi **tạm dừng**,
giữ nguyên biến cục bộ. Nhờ vậy xử lý dãy lớn mà chỉ giữ một phần tử trong RAM.

```php
<?php
declare(strict_types=1);

/** @return \Generator<int, array{int, string}> */
function readCsv(string $path): \Generator
{
    $fh = fopen($path, 'r');
    try {
        $line = 0;
        while (($row = fgetcsv($fh, escape: '')) !== false) {
            yield ++$line => $row;          // yield key => value
        }
    } finally {
        fclose($fh);                        // chạy cả khi vòng foreach bên ngoài break sớm
    }
}

foreach (readCsv('/tmp/big.csv') as $no => $row) {
    // file 5 GB vẫn chỉ tốn RAM cho một dòng
}
```

Giao tiếp hai chiều với `send()` và `getReturn()`:

```php
<?php
declare(strict_types=1);

function counter(): \Generator
{
    $received = yield 1;           // trả 1 ra ngoài, dừng; khi được send thì $received nhận giá trị
    echo "nhận: $received\n";
    yield 2;
    return 99;
}

$g = counter();
echo $g->current(), "\n";      // 1
echo $g->send('A'), "\n";      // nhận: A  rồi  2
$g->next();                    // chạy tới return
echo $g->getReturn(), "\n";    // 99
```

- `yield from other()` uỷ quyền cho generator hoặc mảng khác, giá trị trả về của nó là `return` của
  generator con.
- ⚠️ Generator chỉ duyệt được **một lần** và không tua lại được: `foreach` lần hai trên generator đã
  chạy xong ném `Exception`. Cần duyệt lại thì gọi hàm tạo generator mới, hoặc bọc bằng
  `IteratorAggregate` mà `getIterator()` tạo generator mới mỗi lần.
- ⚠️ Generator lười: nếu không ai duyệt thì thân hàm không chạy, kể cả phần kiểm tra tham số ở đầu hàm.
- `LazyCollection` của Laravel (`LazyCollection::make(fn () => yield ...)`, `Model::cursor()`,
  `lazy()`) bọc generator để có API map/filter như Collection mà vẫn tiết kiệm RAM.

Interface để object tự định nghĩa cách được dùng như mảng:

| Interface | Cho phép | Ghi chú |
|---|---|---|
| `Iterator` | `foreach ($obj ...)` | Tự viết 5 method `current/key/next/rewind/valid` |
| `IteratorAggregate` | `foreach` | Chỉ cần `getIterator(): Iterator`, thường `yield` bên trong. Cách gọn nhất |
| `ArrayAccess` | `$obj['key']`, `isset($obj['key'])` | Collection của Laravel implement |
| `Countable` | `count($obj)` | |

#### Fibers

*Fiber* (8.1) là một đoạn code có call stack riêng, tự dừng ở giữa chừng (`Fiber::suspend()`) và được
code bên ngoài tiếp tục sau (`$fiber->resume()`). Khác generator ở chỗ có thể dừng ở **bất kỳ độ sâu
nào** của call stack, không chỉ ở chính hàm có `yield`, nên code thư viện bên trong không cần biết mình
đang chạy trong fiber.

```php
<?php
declare(strict_types=1);

$fiber = new Fiber(function (string $x): string {
    $y = Fiber::suspend($x . '-1');   // dừng, đưa 'a-1' ra ngoài
    return $y . '-3';
});

$v = $fiber->start('a');
echo $v, "\n";                        // a-1
$fiber->resume('b-2');                // $y = 'b-2', chạy tới return
echo $fiber->getReturn(), "\n";       // b-2-3
```

- ⚠️ Fiber **không phải thread**: tại một thời điểm chỉ một fiber chạy, chuyển qua lại do code gọi
  `suspend`/`resume` một cách tường minh (cooperative), không có song song trên nhiều core.
- ⚠️ Fiber **không tự biến I/O thành non-blocking**. `PDO::query()` bên trong fiber gọi thẳng socket ở
  chế độ blocking: cả process đứng chờ DB, mọi fiber khác cũng đứng. Muốn chạy đồng thời phải có
  *event loop* (vòng lặp theo dõi nhiều socket, fiber nào có dữ liệu thì resume fiber đó) và driver
  I/O viết riêng cho event loop đó. Revolt (event loop) và AMPHP v3 xây trên Fiber làm đúng việc này.
- Fiber là công cụ cho tác giả thư viện async, người viết app gần như không gọi trực tiếp.

**Tóm tắt nhanh**

- `match` so sánh `===`, là biểu thức, không fall-through, không khớp thì ném `UnhandledMatchError`.
- Named arguments biến tên tham số thành API; nullsafe `?->` ngắt mạch cả chuỗi và chỉ dùng để đọc.
- Enum là singleton, so bằng `===`, không có state, không làm key mảng; `from` ném, `tryFrom` trả null.
- readonly là nông; 8.4 thêm property hooks (không đi cùng readonly) và `public private(set)`;
  8.5 clone with giải bài wither nhưng vẫn tôn trọng visibility.
- Pipe `|>` truyền đúng một tham số, arrow function trong pipe phải có ngoặc.
- Deprecation nâng bản hay gặp: null vào hàm built-in (8.1), dynamic property (8.2), implicit nullable
  (8.4), backtick và cast tên dài (8.5). Fiber không làm PDO non-blocking.

**Nguồn**: [PHP 8.4 release](https://www.php.net/releases/8.4/en.php) ·
[PHP 8.5 release](https://www.php.net/releases/8.5/en.php) ·
[PHP.Watch versions](https://php.watch/versions) ·
[UPGRADING 8.0–8.5 trong php-src](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) ·
[RFC Property hooks](https://wiki.php.net/rfc/property-hooks) ·
[RFC Asymmetric visibility v2](https://wiki.php.net/rfc/asymmetric-visibility-v2) ·
[RFC Pipe operator v3](https://wiki.php.net/rfc/pipe-operator-v3) ·
[RFC Clone with v2](https://wiki.php.net/rfc/clone_with_v2) ·
[RFC NoDiscard](https://wiki.php.net/rfc/marking_return_value_as_important) ·
[RFC new without parentheses](https://wiki.php.net/rfc/new_without_parentheses) ·
[RFC array_first/array_last](https://wiki.php.net/rfc/array_first_last) ·
[RFC Closures in const expr](https://wiki.php.net/rfc/closures_in_const_expr) ·
[Manual: Enumerations](https://www.php.net/manual/en/language.enumerations.php) ·
[Manual: Lazy Objects](https://www.php.net/manual/en/language.oop5.lazy-objects.php) ·
[Manual: Generators](https://www.php.net/manual/en/language.generators.php) ·
[Manual: Fibers](https://www.php.net/manual/en/language.fibers.php)


---

### 2.2 PHP-FPM và mô hình share-nothing

Module này trả lời: một HTTP request đi từ Nginx vào code PHP qua những process nào, vì sao mỗi
request bắt đầu từ trạng thái trắng, FPM quyết định giữ bao nhiêu worker, và tính `pm.max_children`
thế nào cho khỏi hết RAM mà cũng khỏi 502. Đây là tầng mà sự cố production của app PHP hay nằm ở đó
nhất.

#### Kiến trúc master, pool, worker

*PHP-FPM* (FastCGI Process Manager) là chương trình chạy code PHP cho web server. Nginx không tự chạy
PHP được; nó chỉ chuyển request sang FPM qua giao thức *FastCGI* và nhận lại output.

```
                        Máy chủ web
 Client ── HTTPS ──> ┌──────────────┐
                     │    Nginx     │  vài worker process, event loop, phục vụ file tĩnh,
                     │              │  TLS, gzip; gặp *.php thì fastcgi_pass
                     └──────┬───────┘
                            │ FastCGI qua unix socket /run/php/php-fpm.sock (hoặc TCP 127.0.0.1:9000)
                            v
            ┌──────────────────────────────────────┐
            │ socket đang listen của pool "www"    │  kernel giữ hàng đợi kết nối
            │ [conn][conn][conn]...                │  (listen queue, dài tối đa listen.backlog)
            └──────┬──────────┬──────────┬─────────┘
                   │ accept() │ accept() │ accept()      worker rảnh tự nhận kết nối
                   v          v          v
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │ worker 1 │ │ worker 2 │ │ worker 3 │  user www-data, mỗi worker MỘT request
            │ (bận)    │ │ (rảnh)   │ │ (bận)    │  tại một thời điểm, chạy index.php
            └──────────┘ └──────────┘ └──────────┘
                   ^ fork / kill / theo dõi
            ┌──────┴───────────────────────────────┐
            │ FPM master (thường chạy bằng root)   │  đọc php-fpm.conf + pool/*.conf, tạo socket,
            │                                      │  fork worker, kill worker thừa/treo, reload,
            │                                      │  KHÔNG chạy code PHP của bạn
            └──────────────────────────────────────┘
      (pool "api" khác: socket riêng, user riêng, số worker riêng, cùng master)
```

- *Master process*: một process duy nhất. Đọc cấu hình, mở socket, fork worker, mỗi giây kiểm tra số
  worker rảnh/bận để tạo thêm hoặc giết bớt, giết worker vượt `request_terminate_timeout`, xử lý tín
  hiệu reload (`SIGUSR2`) và tắt êm (`SIGQUIT`).
- *Pool*: một nhóm worker có cấu hình riêng (khai trong `[www]`, `[api]`...): user/group chạy, socket
  lắng nghe, chế độ `pm`, số worker, `php_admin_value[...]` riêng. Tách pool để một loại traffic chậm
  không ăn hết worker của loại khác (module 3.4).
- *Worker process*: process chạy PHP thật. Worker nhận kết nối trực tiếp từ socket của pool (socket được
  mở bởi master rồi kế thừa khi fork), chạy xong một request mới nhận request tiếp.
- Hệ quả quan trọng nhất: **số request chạy song song tối đa của một pool bằng số worker của pool đó**.
  Request thứ `max_children + 1` phải xếp hàng.

Một pool tối thiểu và đoạn Nginx tương ứng:

```ini
; /etc/php/8.4/fpm/pool.d/www.conf (đường dẫn kiểu Debian/Ubuntu)
[www]
user = www-data
group = www-data
listen = /run/php/php8.4-fpm.sock
listen.owner = www-data
listen.group = www-data
pm = dynamic
pm.max_children = 50
pm.start_servers = 10
pm.min_spare_servers = 5
pm.max_spare_servers = 15
pm.max_requests = 1000
request_terminate_timeout = 30s
request_slowlog_timeout = 5s
slowlog = /var/log/php-fpm/www-slow.log
pm.status_path = /fpm-status
ping.path = /fpm-ping
```

```nginx
location ~ \.php$ {
    fastcgi_pass unix:/run/php/php8.4-fpm.sock;
    include fastcgi_params;
    fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
    fastcgi_read_timeout 60s;        # mặc định của Nginx là 60s
}
```

*FastCGI* là giao thức nhị phân giữa web server và FPM. Nginx gửi một loạt *record*: bắt đầu request,
các biến môi trường (`fastcgi_param`: `REQUEST_METHOD`, `SCRIPT_FILENAME`, `QUERY_STRING`, header HTTP
dạng `HTTP_*`), rồi body. FPM đẩy các biến đó vào `$_SERVER`, body vào `php://input`/`$_POST`, rồi gửi
ngược output (header + body) và record kết thúc. Unix socket nhanh hơn TCP một chút và không mở port
ra mạng, nhưng chỉ dùng được khi Nginx và FPM cùng máy (hoặc cùng pod chia sẻ volume); khác máy thì
phải TCP.

#### Vòng đời một request

1. Nginx nhận HTTP request, khớp `location ~ \.php$` (hoặc `try_files ... /index.php?$query_string`
   của Laravel), mở kết nối tới socket của pool.
2. Kernel đặt kết nối vào *listen queue* của socket. Nếu có worker đang rảnh chờ ở `accept()`, nó nhận
   ngay. Nếu mọi worker bận, kết nối nằm chờ trong queue.
3. Nếu queue đã đầy (vượt `listen.backlog`, và bị kernel chặn trên bởi `net.core.somaxconn`), kết nối
   bị từ chối ngay: với unix socket, Nginx nhận lỗi `EAGAIN` ("Resource temporarily unavailable") và
   trả **502** cho client.
4. Worker nhận request. Engine chạy phần khởi tạo cho request (các extension chạy *RINIT*, module 3.4),
   dựng `$_GET`, `$_POST`, `$_SERVER`.
5. Worker chạy `public/index.php`: nạp autoloader, boot Laravel, chạy middleware, controller, trả
   response. Mã đã compile lấy từ OPcache nên không phải parse lại file (module 2.3).
6. Output được gửi về Nginx, Nginx gửi cho client.
7. Worker dọn toàn bộ state của request: huỷ mọi biến, object, đóng file và connection không
   persistent, giải phóng bộ nhớ request về allocator (*RSHUTDOWN*). Worker quay lại `accept()`.
8. Nếu worker đã phục vụ đủ `pm.max_requests` request, nó thoát và master fork worker mới thay.

Các lỗi cổng (gateway) mà Nginx trả tương ứng với các bước trên:

| Nginx trả | Nguyên nhân thường gặp | Dòng log Nginx hay thấy |
|---|---|---|
| 502 Bad Gateway | FPM không chạy / sai đường dẫn socket / sai quyền socket | `connect() to unix:... failed (2: No such file or directory)` hoặc `(13: Permission denied)` |
| 502 | Listen queue đầy vì hết worker lâu | `connect() ... failed (11: Resource temporarily unavailable)` |
| 502 | Worker chết giữa request: segfault, bị `request_terminate_timeout` kill, bị OOM killer giết | `upstream prematurely closed connection` |
| 504 Gateway Timeout | Worker chạy quá `fastcgi_read_timeout` (mặc định 60s) mà chưa trả gì | `upstream timed out (110: Connection timed out)` |

⚠️ Khi Nginx trả 504, worker **vẫn đang chạy tiếp** request đó (Nginx chỉ bỏ cuộc, không kill được
worker). Worker bị chiếm cho tới khi chạy xong hoặc tới `request_terminate_timeout`.

`fastcgi_finish_request()` (chỉ có trong FPM): gửi xong response cho client ngay, rồi worker chạy tiếp
phần sau (ghi log, gửi email). Client thấy nhanh, nhưng **worker vẫn bận** tới khi xong, nên dùng nhiều
là âm thầm giảm số worker rảnh. Việc chậm nên đưa vào queue (module 2.6).

#### Mô hình share-nothing

*Share-nothing*: không có gì của request này còn sống sang request sau. Hết request, mọi biến global,
biến `static`, singleton, object trong container Laravel, connection DB thường đều bị huỷ. Request sau,
dù rơi đúng vào worker cũ, bắt đầu từ trạng thái trắng.

```php
<?php
declare(strict_types=1);

// public/counter.php, chạy dưới FPM
final class Counter
{
    private static int $hits = 0;
    public static function hit(): int { return ++self::$hits; }
}

echo Counter::hit(), "\n";   // luôn in 1, dù gọi 1000 lần và rơi vào cùng một worker
```

Cùng đoạn code đó chạy trên Octane/Swoole (process sống lâu) sẽ in 1, 2, 3... Đó chính là nguồn bug
kinh điển khi chuyển sang Octane (module 3.5).

| | PHP-FPM (share-nothing) | Java Spring, Go net/http (process sống lâu) |
|---|---|---|
| Đơn vị đồng thời | Process, một request mỗi process | Thread (Java) / goroutine (Go), hàng nghìn trong một process |
| State giữa các request | Không có, trừ khi cố ý lưu ra ngoài (Redis, DB, OPcache) | Mọi biến global/singleton dùng chung, phải lo thread-safety |
| Memory leak | Bị dọn sau mỗi request, hiếm khi tích tụ | Tích tụ tới khi process chết |
| Chi phí khởi động | Boot framework **mỗi request** | Boot một lần lúc start |
| Connection pool DB | Không có pool dùng chung; mỗi worker một connection | Pool vài chục connection dùng chung |
| Một request crash/treo | Chỉ mất một worker | Có thể kéo cả process |

Thứ duy nhất sống qua các request nằm ở tầng extension C và bộ nhớ dùng chung: OPcache (bytecode trong
shared memory), APCu, persistent connection (`PDO::ATTR_PERSISTENT`), realpath cache. Userland không
tự giữ được gì.

Cái giá của share-nothing là boot lại mỗi request: nạp file config, đăng ký hàng chục service provider,
dựng route. Các cách giảm: OPcache và `composer dump-autoload --optimize` (module 2.3),
`php artisan optimize` (cache config, route, event, view), và cuối cùng là bỏ hẳn share-nothing bằng
Octane (module 3.5), đổi lại phải tự lo state.

#### Process manager (`pm`)

*Process manager* là chiến lược master dùng để quyết định giữ bao nhiêu worker. Cả ba chế độ đều bị chặn
trên bởi `pm.max_children`.

| `pm` | Hành vi | Tham số dùng | Ưu | Nhược | Khi nào dùng |
|---|---|---|---|---|---|
| `static` | Luôn giữ đúng `pm.max_children` worker từ lúc khởi động | `max_children` | Không tốn thời gian fork khi traffic tăng, latency đều, RAM dự đoán được | Giữ RAM kể cả lúc rảnh | Server/pod dành riêng cho một app; container |
| `dynamic` | Giữ số worker **rảnh** trong khoảng `min_spare`..`max_spare`, tổng không quá `max_children` | `max_children`, `start_servers`, `min_spare_servers`, `max_spare_servers`, `max_spawn_rate` | Co giãn theo tải, vẫn có worker chờ sẵn | Spike đột ngột phải chờ fork dần | Mặc định; VM chạy nhiều thứ |
| `ondemand` | Lúc đầu không có worker; có kết nối mới fork, worker rảnh quá `process_idle_timeout` thì bị kill | `max_children`, `process_idle_timeout` | Gần như không tốn RAM khi rảnh | Request đầu sau lúc rảnh phải chờ fork; fork liên tục khi tải dao động | Nhiều pool ít traffic trên một máy (shared hosting, admin nội bộ) |

Cơ chế của `dynamic` (theo `fpm_process_ctl.c` trong php-src), master chạy vòng kiểm tra **mỗi giây**:

1. Đếm worker rảnh (idle) và bận (active).
2. Nếu số rảnh > `max_spare_servers`: kill **một** worker rảnh (worker cũ nhất), rồi chờ giây sau. Vì
   mỗi giây chỉ kill một, sau spike số worker giảm từ từ.
3. Nếu số rảnh < `min_spare_servers`:
   - Nếu đã đủ `max_children`: ghi log cảnh báo `server reached pm.max_children setting (N), consider
     raising it` và tăng bộ đếm `max children reached` trên status page.
   - Nếu chưa: fork thêm, số lượng tăng gấp đôi mỗi giây liên tiếp còn thiếu (1, 2, 4, 8...) tới trần
     `pm.max_spawn_rate` (mặc định 32, có từ 8.1). Khi tốc độ fork đạt từ 8 trở lên, log có dòng
     `seems busy (you may need to increase pm.start_servers, or pm.min/max_spare_servers)`.

Giá trị mặc định trong file `www.conf` đi kèm PHP:

| Tham số | Mặc định | Ghi chú |
|---|---|---|
| `pm` | `dynamic` | |
| `pm.max_children` | `5` | ⚠️ Rất nhỏ, chỉ hợp máy yếu. Gần như luôn phải chỉnh |
| `pm.start_servers` | `2` | Nếu bỏ trống: `(min_spare + max_spare) / 2` |
| `pm.min_spare_servers` / `pm.max_spare_servers` | `1` / `3` | |
| `pm.max_spawn_rate` | `32` | |
| `pm.process_idle_timeout` | `10s` | Chỉ cho `ondemand` |
| `pm.max_requests` | `0` | 0 = worker không bao giờ tự khởi động lại |

*Fork* là tạo process con bằng cách nhân bản process hiện tại (xem [01-os-linux.md](../01-os-linux.md)).
Fork rẻ nhờ copy-on-write của bộ nhớ, nhưng worker mới vẫn phải "làm nóng" (realpath cache, autoload),
nên request đầu của worker mới thường chậm hơn một chút.

*`pm.max_requests`*: worker tự thoát sau N request và được thay bằng worker mới. Dùng để chặn leak bộ
nhớ tích tụ trong extension C hoặc thư viện (share-nothing dọn bộ nhớ userland, nhưng không chữa được
leak trong C). Đặt khoảng 500 tới vài nghìn là phổ biến; đặt quá thấp thì fork liên tục.

#### Tính `pm.max_children`

Nguyên tắc: `pm.max_children` là số worker **tối đa có thể chạy cùng lúc**, nên phải đảm bảo khi cả
`max_children` worker cùng ở mức RAM cao nhất thì máy vẫn không hết RAM.

```
pm.max_children ≈ (RAM dành cho PHP-FPM) / (bộ nhớ thật trung bình mỗi worker lúc tải cao)
RAM dành cho PHP-FPM = tổng RAM - OS - Nginx - Redis/MySQL chạy cùng máy - OPcache shm - dự phòng
```

Các bước làm thật:

1. Chạy tải giống production (hoặc đo ngay trên production giờ cao điểm), không đo lúc worker vừa
   khởi động.
2. Đo bộ nhớ worker:

   ```sh
   # RSS trung bình của các worker (MB). Tên process tuỳ distro: php-fpm, php-fpm8.4...
   ps --no-headers -o rss -C php-fpm8.4 | awk '{s+=$1; n++} END {printf "%.1f MB x %d\n", s/n/1024, n}'
   # PSS: chia đều phần bộ nhớ dùng chung (OPcache, thư viện) cho các process, sát thực tế hơn
   for p in $(pgrep -f 'php-fpm: pool www'); do grep '^Pss:' /proc/$p/smaps_rollup; done \
     | awk '{s+=$2; n++} END {printf "PSS TB %.1f MB\n", s/n/1024}'
   ```
3. Chia, rồi chừa biên 10–20% cho request nặng bất thường.

*RSS* (Resident Set Size) là lượng RAM thật process đang chiếm, **kể cả phần dùng chung** với process
khác. Mỗi worker đều đọc bytecode trong OPcache shared memory, nên phần đó bị đếm lặp lại trong RSS của
từng worker. Cộng RSS của 100 worker sẽ ra con số lớn hơn RAM thật đang dùng. *PSS* (Proportional Set
Size) chia phần dùng chung theo số process dùng nó, nên cộng PSS xấp xỉ đúng RAM thật. Chia theo RSS
là cách tính **an toàn** (thừa RAM); chia theo PSS sát hơn nhưng cần tính OPcache riêng một lần.

Ví dụ: server 8 GB chạy Nginx + FPM + Redis.

```
Tổng RAM                         8192 MB
- OS, sshd, agent giám sát       -800 MB
- Nginx                          -100 MB
- Redis (maxmemory 1 GB + overhead)  -1300 MB
- OPcache (opcache.memory_consumption=256) -256 MB
- Dự phòng                       -700 MB
= RAM cho worker                 5036 MB
PSS trung bình mỗi worker đo được: 55 MB (đỉnh ở request export: 120 MB)
5036 / 55  ≈ 91   -> chọn khoảng 80 để còn chỗ cho vài request nặng
5036 / 120 ≈ 42   -> nếu MỌI request đều nặng như export, chỉ được khoảng 40
```

Kiểm tra chéo bằng nhu cầu thực tế, theo *định luật Little*: số worker bận trung bình = số request mỗi
giây × thời gian xử lý trung bình. 200 req/s × 0,25 s = 50 worker bận. Nếu con số này sát
`max_children` thì lúc spike sẽ xếp hàng; nếu nhỏ hơn nhiều thì đặt `max_children` cao cũng không được
lợi gì.

- ⚠️ **Không lấy `memory_limit` để chia.** `memory_limit` (mặc định `128M`) là **trần** một request được
  phép dùng, không phải mức dùng thật. 5036 / 128 ≈ 39 worker là lãng phí nếu worker thật chỉ dùng 55 MB.
  Ngược lại cũng đừng quên: về lý thuyết mọi worker cùng chạm trần một lúc được, nên chừa biên.
- ⚠️ Đặt quá cao: lúc tải cao mọi worker cùng phình, máy hết RAM, bắt đầu *swap* (đẩy trang bộ nhớ
  xuống đĩa, chậm hàng trăm lần), rồi *OOM killer* của Linux giết process (có khi giết nhầm MySQL hoặc
  Redis chạy cùng máy). Máy swap thì chậm toàn bộ, tệ hơn nhiều so với vài request phải xếp hàng.
- ⚠️ Đặt quá thấp: request xếp hàng ở listen queue, latency tăng vọt, rồi 502 khi queue đầy. Log FPM có
  `server reached pm.max_children setting`.
- ⚠️ Nhiều worker hơn không làm request CPU-bound nhanh hơn. Nếu request chủ yếu tính toán (render,
  xử lý ảnh), worker nhiều hơn số core chỉ làm chúng tranh CPU. `max_children` cao chỉ có ích khi
  worker chủ yếu **chờ** I/O (DB, API ngoài).
- ⚠️ Giới hạn **downstream**: mỗi worker có thể giữ một connection DB. 80 worker × 4 server = 320
  connection tiềm năng, cộng queue worker, vượt `max_connections` mặc định 151 của MySQL. Tính chi tiết
  ở [03-database-sql.md, module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel).
- Nhiều pool trên một máy: tổng `max_children` của mọi pool mới là con số phải khớp với RAM.

#### Timeout và giới hạn

| Giới hạn | Ở đâu | Mặc định | Đo cái gì | Vượt thì |
|---|---|---|---|---|
| `memory_limit` | php.ini | `128M` | Bộ nhớ mà Zend allocator cấp cho một request | Fatal error "Allowed memory size ... exhausted", request đó chết, worker sống |
| `max_execution_time` | php.ini | `30` (CLI luôn là `0`) | Thời gian **thực thi script** (trên Linux là thời gian CPU) | Fatal error "Maximum execution time of N seconds exceeded" |
| `request_terminate_timeout` | pool FPM | `0` (tắt) | Thời gian **thực** (wall clock) từ lúc worker nhận request | Master kill worker, Nginx thấy kết nối đứt, trả 502 |
| `fastcgi_read_timeout` | Nginx | `60s` | Khoảng thời gian giữa hai lần đọc được dữ liệu từ FPM | Nginx trả 504, worker vẫn chạy |

⚠️ Theo tài liệu PHP, `max_execution_time` và `set_time_limit()` **chỉ tính thời gian thực thi của chính
script**; thời gian nằm trong system call, stream, query DB không được tính (trừ trên Windows, nơi đo
thời gian thực). `sleep()` cũng vậy, vì process nằm chờ trong system call, không đốt CPU. Một request chờ API ngoài 10 phút có thể không bao giờ chạm `max_execution_time = 30`:

```php
<?php
declare(strict_types=1);

set_time_limit(2);

sleep(5);                                   // KHÔNG bị cắt trên Linux: nằm trong system call
echo "vẫn sống sau 5 giây\n";

$end = microtime(true) + 3;
while (microtime(true) < $end) {}           // vòng lặp đốt CPU
// Fatal error: Maximum execution time of 2 seconds exceeded
```

Vì vậy chặn theo thời gian thực phải dùng các tầng khác:

1. Timeout của từng lời gọi ra ngoài: HTTP client (`Http::timeout(5)` trong Laravel, `CURLOPT_TIMEOUT`),
   `default_socket_timeout`, timeout của Redis/DB client. Đây là tầng quan trọng nhất vì code PHP còn
   bắt được lỗi và xử lý.
2. `request_terminate_timeout` ở FPM: lưới an toàn cuối, kill cứng worker (không chạy `finally`, không
   log gì từ PHP).
3. `fastcgi_read_timeout` ở Nginx: đặt lớn hơn `request_terminate_timeout`, để FPM cắt trước Nginx
   (thứ tự đầy đủ ở module 3.4).

- `memory_limit` của CLI và FPM đọc từ file ini khác nhau (Debian/Ubuntu: `/etc/php/8.4/cli/php.ini` và
  `/etc/php/8.4/fpm/php.ini`), nên `php -i` trên terminal không cho biết cấu hình FPM. Xem cấu hình FPM
  qua `phpinfo()` chạy dưới web hoặc `php-fpm8.4 -tt`.
- Có thể nâng giới hạn cho riêng một pool: `php_admin_value[memory_limit] = 256M` (code không ghi đè
  được bằng `ini_set`). PHP 8.5 thêm `max_memory_limit` để đặt trần cho mọi lần nâng `memory_limit`.

#### Quan sát

*Slow log*: đặt `request_slowlog_timeout = 5s` và `slowlog = ...`. Request nào chạy quá ngưỡng, master
tạm dừng worker đó (qua `ptrace`), đọc call stack PHP đang chạy, ghi vào file, rồi cho chạy tiếp. Mặc
định lấy 20 frame (`request_slowlog_trace_depth`). Một bản ghi trông như sau (đọc từ trên xuống: dòng
đầu là hàm đang chạy, các dòng sau là nơi gọi nó; output minh hoạ, không phải chạy thật):

```
[27-Sep-2026 10:15:02]  [pool www] pid 21873
script_filename = /var/www/app/public/index.php
[0x00007f3a8c01e2a0] curl_exec() /var/www/app/vendor/guzzlehttp/guzzle/src/Handler/CurlHandler.php:44
[0x00007f3a8c01e1f0] __invoke() /var/www/app/vendor/guzzlehttp/guzzle/src/Handler/Proxy.php:28
...
[0x00007f3a8c01d8a0] charge() /var/www/app/app/Services/PaymentGateway.php:61
[0x00007f3a8c01d7b0] store() /var/www/app/app/Http/Controllers/OrderController.php:37
```

Đọc: request đặt hàng (`OrderController::store`) đang đứng ở `curl_exec()` trong lúc gọi cổng thanh
toán, tức chậm vì chờ API ngoài, không phải vì code PHP. Hướng sửa: timeout cho HTTP client, hoặc đưa
việc gọi ra queue. Nếu dòng đầu là `PDOStatement->execute()` thì chậm ở DB; lúc đó mở slow query log
của MySQL.

*Status page*: bật `pm.status_path = /fpm-status` rồi cho Nginx chuyển đường dẫn đó vào FPM, chỉ cho
phép IP nội bộ (`allow 127.0.0.1; deny all;`), vì trang lộ URI và thông tin nội bộ. Hỗ trợ các định dạng
`?json`, `?xml`, `?openmetrics` (cho Prometheus) và `?full` để xem từng worker.

```sh
curl -s 'http://127.0.0.1/fpm-status?json' | jq
```

| Trường | Ý nghĩa | Đọc thế nào |
|---|---|---|
| `listen queue` | Số request đang chờ worker rảnh | Lớn hơn 0 kéo dài là thiếu worker hoặc worker bị chặn |
| `max listen queue` | Đỉnh của listen queue từ lúc FPM start | Từng bị xếp hàng hay chưa |
| `listen queue len` | Kích thước tối đa của queue | So với `listen queue` để biết sắp 502 chưa |
| `idle processes` / `active processes` | Worker rảnh / đang chạy | `idle` về 0 lúc cao điểm là báo động |
| `max active processes` | Đỉnh số worker bận | Gần bằng `max_children` là từng chạm trần |
| `max children reached` | Số lần chạm `pm.max_children` | Tăng dần theo thời gian là cần xem lại |
| `slow requests` | Số request vượt `request_slowlog_timeout` | Tăng đột ngột: downstream đang chậm |

Với `?full`, mỗi worker có `state`, `request duration`, `request uri`, `last request memory`: cách nhanh
để tìm URI nào tốn bộ nhớ nhất khi tính `max_children`.

*`ping.path`* (ví dụ `/fpm-ping`, trả `pong`): health check rẻ cho load balancer hoặc Kubernetes, chỉ
chứng minh FPM còn nhận request, không chứng minh app khoẻ.

**Tóm tắt nhanh**

- Nginx chuyển request qua FastCGI tới socket của pool; worker tự `accept()`, mỗi worker một request,
  master chỉ quản lý chứ không chạy code. Song song tối đa = số worker.
- Share-nothing: hết request mọi state userland bị huỷ (biến `static` luôn về đầu), đổi lại phải boot
  framework mỗi request. Chỉ extension (OPcache, persistent connection) giữ được gì đó.
- `static` cho server/pod dành riêng, `dynamic` là mặc định (kiểm tra mỗi giây, fork gấp đôi tới
  `max_spawn_rate`, kill một worker mỗi giây), `ondemand` cho pool ít traffic.
- `max_children` = RAM còn lại cho PHP / bộ nhớ thật mỗi worker lúc tải cao (RSS an toàn, PSS sát hơn),
  không chia cho `memory_limit`, và phải kiểm tra số connection DB.
- 502 là không kết nối được hoặc worker chết giữa chừng; 504 là Nginx hết `fastcgi_read_timeout` trong
  khi worker vẫn chạy.
- `max_execution_time` trên Linux không tính thời gian chờ I/O; chặn theo thời gian thực bằng timeout
  HTTP client và `request_terminate_timeout`.

**Nguồn**: [PHP Manual: FPM](https://www.php.net/manual/en/install.fpm.php) ·
[FPM Configuration](https://www.php.net/manual/en/install.fpm.configuration.php) ·
[FPM Status Page](https://www.php.net/manual/en/fpm.status.php) ·
[`www.conf.in` trong php-src](https://github.com/php/php-src/blob/master/sapi/fpm/www.conf.in) ·
[`fpm_process_ctl.c` trong php-src](https://github.com/php/php-src/blob/master/sapi/fpm/fpm/fpm_process_ctl.c) ·
[set_time_limit](https://www.php.net/manual/en/function.set-time-limit.php) ·
[max_execution_time](https://www.php.net/manual/en/info.configuration.php#ini.max-execution-time) ·
[memory_limit](https://www.php.net/manual/en/ini.core.php#ini.memory-limit) ·
[Nginx: ngx_http_fastcgi_module](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html)


---

### 2.3 OPcache và deploy

Module này trả lời: OPcache giữ cái gì trong RAM và biết file đổi bằng cách nào, vì sao production
tắt kiểm tra timestamp rồi phải reload FPM mỗi lần deploy, và vì sao deploy kiểu đổi symlink hay
"deploy xong vẫn chạy code cũ". Phần cuối ráp lại thành một script deploy Laravel đủ bước.

#### PHP chạy một file thế nào

Mỗi lần gặp `require`/`include` (kể cả qua autoloader của Composer), Zend Engine phải biến văn bản
mã nguồn thành thứ chạy được:

```text
  index.php (văn bản)
      │ 1. Lexer: cắt thành token          T_VARIABLE($x) '=' T_LNUMBER(1) ';'
      ▼
  token stream
      │ 2. Parser: dựng AST                 ASSIGN(VAR x, CONST 1)
      ▼
  AST (Abstract Syntax Tree)
      │ 3. Compiler: sinh opcode            ASSIGN !0, 1
      ▼
  op_array (opcode + bảng hằng + thông tin class/hàm)
      │ 4. Zend VM: chạy từng opcode
      ▼
  kết quả
```

- *Token*: đơn vị nhỏ nhất có nghĩa (từ khoá, tên biến, số, dấu). *AST*: cây mô tả cấu trúc chương
  trình. *Opcode*: lệnh của máy ảo PHP, ví dụ `ASSIGN`, `ADD`, `INIT_FCALL`, `DO_FCALL`.
- Bước 1–3 tốn CPU và tốn cả syscall (mở file, `stat`, đọc). Bước 4 mới là "code của bạn chạy".
- Không có OPcache, **mỗi request** lặp lại bước 1–3 cho **mọi file** được nạp. Một request Laravel
  nạp vài trăm file (framework, vendor, app), nên phần lớn thời gian CPU có thể đi vào việc biên dịch
  lại cùng một đống code không đổi.

Muốn tự thấy opcode: extension `vld`, hoặc bật `opcache.opt_debug_level=0x10000` (dump opcode trước
tối ưu) / `0x20000` (sau tối ưu) khi chạy CLI với `opcache.enable_cli=1`.

#### OPcache

*OPcache* lưu kết quả bước 3 (op_array đã tối ưu) vào *shared memory*: một vùng RAM mà nhiều process
cùng ánh xạ vào. Vùng này do master process của FPM tạo lúc khởi động, nên **mọi worker của cùng một
FPM master dùng chung một cache**. Request sau chỉ còn bước 4, cộng một lần tra bảng băm.

Từ PHP 8.5, OPcache luôn được build tĩnh vào PHP (RFC *Make OPcache a non-optional part of PHP*):
không còn flag `--disable-opcache`, không còn dòng `zend_extension=opcache` trong php.ini. RFC nói rõ
việc "luôn được nạp" không có nghĩa là "luôn bật": `opcache.enable` và `opcache.enable_cli` vẫn giữ
nguyên. Một lý do RFC nêu: với image Docker chính thức, OPcache phải tự build và nạp, rất dễ vô tình
chạy production không có cache; lý do còn lại là hai đường code riêng (có và không có OPcache) dễ sinh bug.

Các ini quan trọng (giá trị mặc định theo php.net):

| Directive | Mặc định | Ý nghĩa |
|---|---|---|
| `opcache.enable` | 1 | Bật cho SAPI web/FPM. `ini_set` chỉ tắt được, không bật được |
| `opcache.enable_cli` | 0 | CLI mặc định **không** dùng OPcache |
| `opcache.memory_consumption` | 128 (MB) | Dung lượng shared memory cho opcode. Tối thiểu 8. Khi bật JIT, tổng segment = giá trị này + `jit_buffer_size` |
| `opcache.interned_strings_buffer` | 8 (MB) | Vùng chứa *interned string* (chuỗi dùng chung như tên class, tên hàm, literal; module 3.1) |
| `opcache.max_accelerated_files` | 10000 | Số key tối đa trong bảng băm. Giá trị thật là số nguyên tố đầu tiên ≥ cấu hình trong dãy {223, 463, 983, 1979, 3907, 7963, 16229, 32531, 65407, 130987, 262237, 524521, 1048793}, nên 10000 thành 16229. Min 200, max 1000000 |
| `opcache.max_wasted_percentage` | 5 | Phần trăm bộ nhớ "phí" tối đa trước khi lên lịch restart cache khi thiếu chỗ |
| `opcache.validate_timestamps` | 1 | Có kiểm tra file đã đổi hay không |
| `opcache.revalidate_freq` | 2 (giây) | Kiểm tra tối đa mỗi N giây một lần mỗi script. 0 là kiểm mọi request |
| `opcache.file_update_protection` | 2 (giây) | Không cache file có mtime mới hơn N giây, tránh cache file đang được ghi dở |
| `opcache.save_comments` | 1 | Giữ docblock. Tắt đi thì hỏng các thư viện đọc annotation (Doctrine, PHPUnit) |

*OPcache biết file đổi bằng cách nào.* Khi `validate_timestamps=1`, mỗi lần một script được nạp mà
đã quá `revalidate_freq` giây kể từ lần kiểm trước, OPcache `stat` file và so *mtime* (thời điểm sửa
đổi cuối) với mtime lúc cache. Khác thì biên dịch lại và thay bản cũ. Bản cũ **không được giải phóng
ngay** mà thành *wasted memory* (bộ nhớ phí), vì shared memory của OPcache chỉ cấp phát thêm, không
dồn lại.

Production thường đặt:

```ini
; production: code chỉ đổi khi deploy
opcache.validate_timestamps=0      ; không bao giờ stat file, bỏ hẳn syscall kiểm tra
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=20000
```

Tắt kiểm tra thì theo php.net, thay đổi trên đĩa chỉ có hiệu lực khi bạn gọi `opcache_reset()`,
`opcache_invalidate()`, hoặc khởi động lại server. Trong thực tế là **reload FPM** (`systemctl reload
php8.4-fpm`, tức gửi `SIGUSR2` cho master): master khởi động lại chính nó và các worker, shared memory
được tạo mới, cache trống. Với container (Docker, Kubernetes), mỗi lần deploy là container mới nên
cache vốn đã trống; `validate_timestamps=0` là lựa chọn tự nhiên.

⚠️ `opcache_reset()` chạy từ CLI (`php -r 'opcache_reset();'`) **không** xoá cache của FPM. CLI là
process khác, có cache riêng (mặc định còn tắt hẳn vì `enable_cli=0`, khi đó lệnh trả `false`; bật `enable_cli=1` thì lệnh trả `true` nhưng chỉ xoá cache của chính process CLI đó). Muốn
reset cache FPM mà không reload thì phải gọi hàm đó **bên trong FPM**: qua một URL nội bộ, hoặc công
cụ như `cachetool` nói chuyện thẳng với socket FastCGI. Tương tự, `opcache_get_status()` chạy ở CLI
cho bạn trạng thái của CLI (thường là `false`), không phải của FPM.

*Cache đầy mà không báo lỗi.* Có ba giới hạn độc lập, cái nào chạm trần trước cũng làm file mới không
được cache:

1. `memory_consumption` hết chỗ cho opcode.
2. `max_accelerated_files` hết key. Lưu ý một file có thể chiếm hơn một key (đường dẫn gốc và đường
   dẫn qua symlink là hai key, xem nhóm dưới).
3. `interned_strings_buffer` đầy: chuỗi mới rơi về bộ nhớ riêng của từng worker, mất lợi ích dùng
   chung, log có cảnh báo tràn buffer.

Khi (1) hoặc (2) đầy, OPcache chỉ lên lịch *restart* (xoá sạch và làm lại từ đầu) nếu tỉ lệ wasted
vượt `max_wasted_percentage`. Nếu không, nó đặt `cache_full = true` và từ đó mọi file chưa có trong
cache bị **biên dịch lại mỗi request**. App không lỗi, chỉ chậm dần và CPU tăng. Deploy nhiều lần với
`validate_timestamps=1` hoặc với thư mục release mới mà không reload là cách nhanh nhất để lấp đầy
cache bằng bản cũ.

Đọc trạng thái. Đặt file này sau một route nội bộ có xác thực và gọi **qua HTTP**, để đọc đúng cache
của FPM:

```php
<?php
declare(strict_types=1);

// opcache-health.php
$s = opcache_get_status(false);   // false: bỏ danh sách từng script cho nhẹ
if ($s === false) {
    exit("OPcache tắt, hoặc bị opcache.restrict_api chặn\n");
}

$mem  = $s['memory_usage'];
$stat = $s['opcache_statistics'];
$istr = $s['interned_strings_usage'];
$total = $mem['used_memory'] + $mem['free_memory'] + $mem['wasted_memory'];

printf("memory   : %.1f%% dùng, %.1f%% wasted\n",
    100 * $mem['used_memory'] / $total, $mem['current_wasted_percentage']);
printf("keys     : %d / %d\n", $stat['num_cached_keys'], $stat['max_cached_keys']);
printf("interned : %.1f%% dùng\n", 100 * $istr['used_memory'] / $istr['buffer_size']);
printf("hit rate : %.2f%%  cache_full=%s  oom_restarts=%d  hash_restarts=%d\n",
    $stat['opcache_hit_rate'], var_export($s['cache_full'], true),
    $stat['oom_restarts'], $stat['hash_restarts']);
// Ví dụ một server khoẻ (output minh hoạ, không phải chạy thật):
// memory   : 61.3% dùng, 0.4% wasted
// keys     : 4120 / 16229
// interned : 72.5% dùng
// hit rate : 99.97%  cache_full=false  oom_restarts=0  hash_restarts=0
```

Cách đọc:

- `cache_full = true`, hoặc `free_memory` gần 0: tăng `memory_consumption`.
- `num_cached_keys` sát `max_cached_keys`: tăng `max_accelerated_files` (đếm số file PHP trong project
  bằng `find . -name '*.php' | wc -l`, đặt cao hơn con số đó).
- `oom_restarts` / `hash_restarts` tăng dần: cache đang bị xoá sạch định kỳ vì hết chỗ, mỗi lần như
  vậy là một đợt spike CPU.
- `opcache_hit_rate` dưới ~99% ở trạng thái ổn định: có gì đó đang làm miss (cache đầy, blacklist,
  file mới liên tục).
- Từ 8.3, `scripts[n]['revalidate']` (khi gọi với `true`) là timestamp lần kiểm mtime kế tiếp.

#### Deploy kiểu symlink và realpath cache

Deploy kiểu *symlink swap* (còn gọi là atomic deploy, kiểu Capistrano/Deployer/Envoyer):

```text
/var/www/app/
├── current  ->  releases/20260927_1015     (Nginx root = /var/www/app/current/public)
├── releases/
│   ├── 20260926_1730/                      bản trước, giữ lại để rollback
│   └── 20260927_1015/                      bản mới
└── shared/
    ├── .env                                symlink vào từng release
    └── storage/                            log, file upload, cache file; symlink vào từng release
```

Chuẩn bị xong bản mới trong thư mục riêng rồi mới đổi `current`, nên không có lúc nào đĩa chứa một
nửa code cũ một nửa code mới. So với `git pull` hay `rsync` đè lên chỗ cũ: request đang chạy có thể
`require` một file mới từ một file cũ, và với `validate_timestamps=1` OPcache còn có thể cache file
đang ghi dở (đó là lý do có `file_update_protection`).

⚠️ Đổi symlink mà không làm gì thêm thì vẫn chạy code cũ. Để hiểu vì sao cần biết hai cache:

*Realpath cache* là cache **riêng của từng process PHP** (không nằm trong shared memory), nhớ kết quả
"đường dẫn này sau khi giải hết symlink, `.`, `..` thì là file thật nào". Mục đích: đỡ gọi `lstat`
lặp lại cho từng thành phần đường dẫn mỗi lần `require`. Mặc định `realpath_cache_size = 4M` (trước
7.0.16/7.1.2 là 16K), `realpath_cache_ttl = 120` giây. Bật `open_basedir` sẽ tắt cache này.

*Key của OPcache.* Nginx truyền cho FPM `SCRIPT_FILENAME=/var/www/app/current/public/index.php`. Đọc
mã nguồn `ext/opcache/ZendAccelerator.c` (hàm `persistent_compile_file`), OPcache làm như sau:

1. Tra bảng băm bằng **đúng đường dẫn được đưa vào**, `.../current/public/index.php`.
2. Không thấy thì mở file, lấy đường dẫn thật (`.../releases/20260926_1730/public/index.php`), tra theo
   đường dẫn thật đó.
3. Thấy (hoặc biên dịch mới xong) thì **thêm key phụ** `.../current/...` trỏ tới cùng entry.

Hệ quả khi đổi `current` sang release mới:

| Cấu hình | Chuyện gì xảy ra |
|---|---|
| `validate_timestamps=0` | Key `current/public/index.php` vẫn trỏ tới bản đã cache của release cũ. Không có gì kiểm lại, nên **chạy code cũ mãi** cho tới khi reset cache |
| `validate_timestamps=1` | Tới lượt revalidate, OPcache giải lại đường dẫn và thấy không còn khớp file đã cache, nên biên dịch lại. Nhưng việc giải đường dẫn đi qua realpath cache của worker, nên mỗi worker có thể còn nhìn thấy release cũ tới 120 giây. Trong khoảng đó các worker trả code **lẫn lộn** cũ và mới |

Khi `index.php` đã được giải thành release cũ, mọi `require __DIR__.'/../vendor/autoload.php'` phía
sau cũng đi theo đường dẫn thật của release cũ, nên cả request chạy trọn trong một release. Đây là
điểm tốt của symlink swap: không bao giờ trộn file trong **một** request, chỉ có thể trộn giữa các
worker.

Hai cách xử lý, thường dùng cả hai:

1. **Reload FPM sau khi đổi symlink.** Xoá OPcache và realpath cache của mọi worker (worker mới là
   process mới). ⚠️ Reload chỉ để worker đang chạy request làm nốt khi `process_control_timeout`
   (trong `php-fpm.conf`) lớn hơn 0. Mặc định là 0: master gửi `SIGQUIT` cho worker rồi gần như ngay
   sau đó gửi `SIGTERM`, request đang chạy dở bị cắt. Đặt ví dụ `process_control_timeout = 30s`.
2. **Cho Nginx tự giải symlink**: dùng `$realpath_root` thay cho `$document_root`. Nginx giải symlink
   mỗi request, gửi cho FPM đường dẫn thật `.../releases/20260927_1015/public/index.php`. Đó là một key
   OPcache mới hẳn, nên bản mới được biên dịch ngay cả khi `validate_timestamps=0` và chưa reload.

```nginx
location ~ \.php$ {
    fastcgi_pass unix:/run/php/php8.4-fpm.sock;
    include fastcgi_params;
    # Giải symlink ở Nginx: PHP nhận đường dẫn thật của release hiện tại
    fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
    fastcgi_param DOCUMENT_ROOT   $realpath_root;
}
```

⚠️ Với cách 2 mà không reload, bản cũ vẫn nằm trong shared memory thành rác. Sau vài chục lần deploy,
cache đầy (nhóm trên). Nên vẫn reload FPM định kỳ hoặc mỗi lần deploy.

⚠️ Đừng mặc định `ln -sfn new current` là atomic: `ln` của GNU coreutils trước 8.27 và `ln` kiểu BSD
(macOS) xoá symlink cũ rồi mới tạo cái mới, có một khoảnh khắc `current` không tồn tại và Nginx trả
404. Từ coreutils 8.27, `ln -f` tự tạo link tạm rồi rename, nhưng script deploy nên làm tường minh:
tạo symlink tạm rồi `rename` đè lên (`mv -T` trên GNU coreutils), vì `rename(2)` trên cùng filesystem
là thao tác nguyên tử.

#### Quy trình deploy Laravel

Script tối thiểu cho một server FPM, deploy bằng symlink swap:

```sh
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/app
REL=$APP/releases/$(date +%Y%m%d_%H%M%S)

git clone --depth 1 --branch main git@github.com:acme/shop.git "$REL"
cd "$REL"
ln -s "$APP/shared/.env" .env
rm -rf storage && ln -s "$APP/shared/storage" storage

composer install --no-dev --optimize-autoloader --no-interaction   # 1
php artisan optimize                                               # 2
php artisan migrate --force                                        # 3

ln -s "$REL" "$APP/current.tmp" && mv -T "$APP/current.tmp" "$APP/current"   # 4. đổi symlink atomic
sudo systemctl reload php8.4-fpm                                   # 5. xoá OPcache + realpath cache
php artisan reload                                                 # 6. process sống lâu nạp code mới
```

Từng bước và hậu quả nếu bỏ:

1. `composer install --no-dev -o`: không cài package dev; `-o` (`--optimize-autoloader`) sinh
   *classmap* đầy đủ để autoloader tra mảng thay vì dò file theo PSR-4 (module 1.5). Bỏ `--no-dev`:
   production có Debugbar, Faker... Bỏ `-o`: mỗi class lạ là vài lần `file_exists`.
2. `php artisan optimize`: trong 13.x chạy `config:cache`, `event:cache`, `route:cache`, `view:cache`
   (cộng các lệnh package tự đăng ký). Kết quả là các file PHP trong `bootstrap/cache/` và
   `storage/framework/views/`, mà OPcache cache được như code thường. Bỏ bước này: mỗi request đọc
   và gộp lại hàng chục file config, đăng ký lại mọi route, Blade biên dịch view lúc có request đầu.
3. `migrate --force`: production mặc định hỏi xác nhận, `--force` để chạy không tương tác. Chạy
   **trước** khi đổi symlink nghĩa là code cũ sẽ chạy trên schema mới trong vài giây, nên migration
   phải tương thích ngược (expand/contract, [03-database-sql.md](03-database-sql.md) module 3.3).
4. Đổi symlink: từ đây request mới vào release mới (nếu dùng `$realpath_root`).
5. Reload FPM: bỏ bước này với `validate_timestamps=0` là chạy code cũ.
6. `php artisan reload` (có trong Laravel 13): dừng các dịch vụ sống lâu để process manager
   (Supervisor, systemd) khởi động lại với code mới. Trong mã nguồn nó chạy `queue:restart`,
   `schedule:interrupt`, cộng các lệnh reload mà package đăng ký qua `ServiceProvider::$reloadCommands`
   (docs nêu Reverb, Octane). Bản cũ hơn thì gọi từng lệnh: `queue:restart`, `horizon:terminate`,
   `octane:reload`.

⚠️ *Config cache và `env()`.* `config:cache` gộp mọi file `config/*.php` thành một file
`bootstrap/cache/config.php` đã tính sẵn giá trị. Trong mã nguồn, bootstrapper
`LoadEnvironmentVariables` return sớm khi `$app->configurationIsCached()`, tức **file `.env` không còn
được đọc nữa**. Hệ quả:

```php
<?php
declare(strict_types=1);

// app/Services/PaymentClient.php: SAI
$key = env('STRIPE_KEY');                 // null sau config:cache (nếu STRIPE_KEY chỉ có trong .env)

// config/services.php: ĐÚNG, env() chỉ gọi trong file config
return ['stripe' => ['key' => env('STRIPE_KEY')]];

// Code ứng dụng đọc qua config
$key = config('services.stripe.key');     // 'sk_live_...' kể cả khi đã cache
```

Chính xác hơn, docs nói sau khi cache thì `env()` "chỉ trả về biến môi trường thật ở mức hệ thống".
Biến đặt bằng Docker/Kubernetes env, systemd `Environment=`, hoặc `env[...]` trong pool FPM vẫn đọc
được; biến chỉ nằm trong `.env` thì ra `null`. Đây là lý do bug kiểu này hay "chỉ xảy ra trên một số
server". Cũng vì vậy: sửa `.env` trên production phải chạy lại `config:cache` rồi reload.

⚠️ *Process sống lâu.* Queue worker, Horizon, Octane, scheduler chạy `schedule:work` nạp code **một
lần** rồi chạy mãi. `queue:restart` không kill ngay: nó ghi một tín hiệu vào **cache** (nên cache
driver phải dùng chung giữa các server, không được là `array`), mỗi worker kiểm tín hiệu sau khi làm
xong job hiện tại rồi tự thoát, và Supervisor khởi động lại. Không có process manager thì worker thoát
luôn và queue dừng.

Checklist "deploy xong vẫn chạy code cũ", từ dễ tới khó kiểm:

| Nguyên nhân | Kiểm tra |
|---|---|
| OPcache chưa xoá (`validate_timestamps=0`, chưa reload FPM) | `opcache_get_status()` qua HTTP: `start_time`/`last_restart_time` trước giờ deploy |
| Symlink + key OPcache/realpath cache trỏ release cũ | `readlink -f current`; so với `$_SERVER['SCRIPT_FILENAME']`, `__DIR__` in ra từ app |
| Queue worker / Horizon / Octane chưa restart | `ps -o lstart= -p <pid>` của worker: khởi động trước giờ deploy |
| Config/route cache cũ (cache sinh từ code cũ, hoặc sinh trước khi sửa `.env`) | Thời gian sửa file `bootstrap/cache/config.php`, `routes-v7.php`; `php artisan about` |
| Load balancer còn gửi traffic tới server chưa deploy; CDN/browser cache asset cũ | Header phản hồi có tên server/phiên bản; hash trong tên file asset build |

**Tóm tắt nhanh**

- OPcache lưu opcode đã biên dịch trong shared memory dùng chung cho mọi worker của một FPM master, bỏ
  được lexer/parser/compiler mỗi request. Từ 8.5 luôn được build vào PHP, vẫn tắt được bằng ini.
- Production đặt `validate_timestamps=0` và reload FPM mỗi lần deploy; `opcache_reset()` từ CLI không
  đụng tới cache của FPM.
- Cache đầy (memory, số key, interned strings) không báo lỗi: `cache_full`, hit rate, `oom_restarts`
  trong `opcache_get_status()` là chỗ phải nhìn.
- Symlink swap: OPcache giữ key theo đường dẫn `current/...` và realpath cache của từng worker nhớ đích
  cũ tới 120 giây. Dùng `$realpath_root` ở Nginx và reload FPM.
- Deploy Laravel: `composer install --no-dev -o` → `optimize` → `migrate --force` → đổi symlink → reload
  FPM → `artisan reload`/`queue:restart`. Sau `config:cache`, `env()` ngoài file config không đọc `.env`.

**Nguồn**: [PHP: OPcache runtime configuration](https://www.php.net/manual/en/opcache.configuration.php) ·
[PHP: opcache_get_status](https://www.php.net/manual/en/function.opcache-get-status.php) ·
[PHP: opcache_reset](https://www.php.net/manual/en/function.opcache-reset.php) ·
[PHP: opcache_invalidate](https://www.php.net/manual/en/function.opcache-invalidate.php) ·
[PHP: realpath cache ini](https://www.php.net/manual/en/ini.core.php#ini.sect.performance) ·
[RFC: Make OPcache a non-optional part of PHP](https://wiki.php.net/rfc/make_opcache_required) ·
[php-src: ZendAccelerator.c](https://github.com/php/php-src/blob/PHP-8.5/ext/opcache/ZendAccelerator.c) ·
[Laravel: Deployment](https://laravel.com/docs/deployment#optimization) ·
[Laravel: Configuration Caching](https://laravel.com/docs/configuration#configuration-caching) ·
[Laravel: Queue Workers and Deployment](https://laravel.com/docs/queues#queue-workers-and-deployment) ·
[Quy trình deploy tổng quát (plan 19)](../19-devops-cloud.md)

---

### 2.4 Lõi Laravel: lifecycle, container, provider, facade

Module này trả lời: từ lúc Nginx gọi `public/index.php` tới lúc response về trình duyệt, Laravel đi
qua những class và method nào; service container tạo object bằng cách nào (kể cả khi bạn chưa đăng ký
gì); `register` và `boot` khác nhau ở đâu; và `Cache::get()` thật ra là lời gọi gì. Mọi tên class,
method dưới đây lấy từ mã nguồn `laravel/framework` nhánh 13.x (bản 13.33) và skeleton `laravel/laravel`
13.x.

#### Request lifecycle

*Lifecycle* là chuỗi bước từ khi request vào tới khi response ra. Trên PHP-FPM, toàn bộ chuỗi này
chạy lại **mỗi request** (share-nothing, module 2.2).

**Bước 1: `public/index.php`** (skeleton 13.x, rút gọn):

```php
define('LARAVEL_START', microtime(true));

// Chế độ bảo trì: file này do `php artisan down` tạo, chạy TRƯỚC cả autoloader
if (file_exists($maintenance = __DIR__.'/../storage/framework/maintenance.php')) {
    require $maintenance;
}

require __DIR__.'/../vendor/autoload.php';            // autoloader của Composer

$app = require_once __DIR__.'/../bootstrap/app.php';  // Application = service container
$app->handleRequest(Request::capture());              // Request dựng từ $_GET, $_POST, $_SERVER...
```

**Bước 2: `bootstrap/app.php`** tạo và cấu hình `Illuminate\Foundation\Application`:

```php
return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(web: __DIR__.'/../routes/web.php', commands: __DIR__.'/../routes/console.php', health: '/up')
    ->withMiddleware(function (Middleware $middleware): void { /* thêm/bớt middleware */ })
    ->withExceptions(function (Exceptions $exceptions): void { /* report/render */ })
    ->create();
```

Bên dưới, `Application::configure()` gọi `new Application($basePath)`. Constructor làm bốn việc:
`registerBaseBindings()` (đặt chính nó vào container dưới key `app` và `Container::class`, gọi
`Container::setInstance($this)`), `registerBaseServiceProviders()` (Event, Log, Context, Routing),
`registerCoreContainerAliases()` (bảng alias kiểu `'cache' => [CacheManager::class,
Contracts\Cache\Factory::class]`), và một hook cho Laravel Cloud. Sau đó `ApplicationBuilder` gọi sẵn
`withKernels()` (bind singleton `Contracts\Http\Kernel` → `Foundation\Http\Kernel`), `withEvents()`,
`withCommands()`, `withProviders()` (đọc `bootstrap/providers.php`). Điểm cần nhớ: **`Application`
kế thừa `Illuminate\Container\Container`**, nên "app" và "container" là một object.

Lưu ý thời điểm: `withMiddleware()` không áp cấu hình ngay mà đăng ký `afterResolving(HttpKernel)`,
tức chạy khi Kernel được resolve ở bước 3. `withRouting()` đăng ký một callback `booting` để
`AppRouteServiceProvider` nạp file route trong giai đoạn boot.

**Bước 3: `Application::handleRequest()`** chỉ có ba dòng:

```php
$kernel = $this->make(HttpKernelContract::class);
$response = $kernel->handle($request)->send();
$kernel->terminate($request, $response);
```

**Bước 4: `Kernel::handle()` → `sendRequestThroughRouter()`**:

1. `$app->instance('request', $request)`: đưa request vào container.
2. `bootstrap()`: nếu chưa bootstrap thì `$app->bootstrapWith($this->bootstrappers)`. Sáu bootstrapper,
   đúng thứ tự trong `Illuminate\Foundation\Http\Kernel::$bootstrappers`:

   | Bootstrapper | Làm gì |
   |---|---|
   | `LoadEnvironmentVariables` | Đọc `.env` bằng phpdotenv. **Bỏ qua** nếu config đã cache (module 2.3) |
   | `LoadConfiguration` | Nạp `config/*.php`, hoặc một file `bootstrap/cache/config.php` nếu đã cache |
   | `HandleExceptions` | Đăng ký `set_error_handler`, `set_exception_handler`, shutdown handler |
   | `RegisterFacades` | `Facade::clearResolvedInstances()`, `Facade::setFacadeApplication($app)`, đăng ký `AliasLoader` |
   | `RegisterProviders` | `$app->registerConfiguredProviders()`: gọi `register()` của mọi provider không deferred |
   | `BootProviders` | `$app->boot()`: gọi `boot()` của mọi provider đã register |

   Trước và sau mỗi bootstrapper, app bắn event `bootstrapping: <Class>` / `bootstrapped: <Class>`.
3. Chạy `Illuminate\Routing\Pipeline` qua **global middleware** rồi tới đích `dispatchToRouter()`.
4. Mọi `Throwable` văng ra được bắt ngay trong `handle()`: `reportException()` (ghi log) rồi
   `renderException()` (biến thành response lỗi). Cuối cùng bắn event `RequestHandled`.

Global middleware mặc định trong 13.x (`Foundation\Configuration\Middleware::getGlobalMiddleware()`):
`ValidatePathEncoding`, `InvokeDeferredCallbacks`, `TrustHosts` (nếu bật), `TrustProxies`,
`HandleCors`, `PreventRequestsDuringMaintenance`, `ValidatePostSize`, `TrimStrings`,
`ConvertEmptyStringsToNull`.

**Bước 5: Router.** `Router::dispatch()` → `dispatchToRoute()` → `findRoute()` (khớp method + URI; lỗi
thì `NotFoundHttpException`/`MethodNotAllowedHttpException`) → `runRoute()` (bắn `RouteMatched`) →
`runRouteWithinStack()`: một Pipeline thứ hai qua **middleware của group và của route**, đã được sắp
xếp theo `$middlewarePriority` của Kernel. Group `web` mặc định: `EncryptCookies`,
`AddQueuedCookiesToResponse`, `StartSession`, `ShareErrorsFromSession`, `PreventRequestForgery`,
`SubstituteBindings` (đổi `{user}` trong URI thành model).

**Bước 6: Controller.** `Route::run()` → `runController()`. Controller được tạo bằng
`$container->make(ControllerClass)` (nên constructor injection hoạt động), rồi `ControllerDispatcher`
resolve tham số của method (route parameter, model binding, và các class type hint như `Request`).

**Bước 7: Response.** Controller trả về gì cũng được `Router::toResponse()` chuẩn hoá: mảng,
`Arrayable`, `JsonSerializable` → `JsonResponse`; model vừa tạo (`wasRecentlyCreated`) → `JsonResponse`
status 201; chuỗi → `Response` HTML; `Responsable` → gọi `toResponse()`. Response đi ngược ra qua các
middleware (phần code sau `$next($request)`), về tới `handleRequest()`.

**Bước 8: `send()`.** `Symfony\Component\HttpFoundation\Response::send()` gửi header và body, rồi nếu
có hàm `fastcgi_finish_request()` (luôn có trên FPM) thì gọi nó: kết nối với client đóng, trình duyệt
nhận đủ response, **nhưng worker chạy tiếp**.

**Bước 9: `Kernel::terminate()`.** Bắn event `Terminating`, gọi `terminate()` của mọi middleware có
method đó (`terminateMiddleware()`), rồi `$app->terminate()` chạy các callback đăng ký bằng
`$app->terminating(...)`, cuối cùng là các handler `whenRequestLifecycleIsLongerThan()`.

```text
public/index.php
  ├─ maintenance.php? ─ vendor/autoload.php
  ├─ bootstrap/app.php: Application::configure()->with...()->create()      [container ra đời]
  └─ $app->handleRequest(Request::capture())
       ├─ make(HttpKernel)  → afterResolving: áp cấu hình withMiddleware
       ├─ Kernel::handle()
       │    ├─ bootstrapWith: env → config → exceptions → facades
       │    │                 → RegisterProviders  (register() mọi provider)       [REGISTER]
       │    │                 → BootProviders      (boot() mọi provider, nạp route) [BOOT]
       │    ├─ Pipeline(global middleware)
       │    │    └─ Router::dispatch → findRoute → Pipeline(route/group middleware)
       │    │         └─ Route::run → container->make(Controller) → method → toResponse
       │    └─ catch Throwable → report + render ; event RequestHandled
       ├─ $response->send()  → fastcgi_finish_request()   [client đã có response]
       └─ Kernel::terminate() → terminable middleware → $app->terminating callbacks
```

*Middleware là củ hành.* `Pipeline::then()` dùng `array_reduce(array_reverse($pipes), $this->carry(),
$destination)` để lồng các middleware thành một chuỗi closure: middleware đầu danh sách là lớp ngoài
cùng. Mỗi middleware string được tạo bằng `$container->make($name)` ngay lúc chạy.

```php
<?php
declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final class AddTiming
{
    public function handle(Request $request, Closure $next): Response
    {
        $start = hrtime(true);                 // chạy TRÊN ĐƯỜNG VÀO, trước các lớp bên trong
        $response = $next($request);           // đi sâu vào lớp tiếp theo, cuối cùng là controller
        $ms = (hrtime(true) - $start) / 1e6;   // chạy TRÊN ĐƯỜNG RA
        $response->headers->set('Server-Timing', sprintf('app;dur=%.1f', $ms));
        return $response;
    }
}
```

⚠️ Middleware không gọi `$next()` mà tự trả response (ví dụ redirect về login) thì các lớp bên trong
và controller **không chạy**. Middleware quên `return $response` thì kiểu trả về `Response` báo
`TypeError`.

#### Service container: đăng ký

*Service container* là object giữ "công thức" tạo các object khác. Code xin một *abstract* (thường là
tên interface hoặc class, cũng có thể là chuỗi như `'cache'`), container tìm *concrete* (công thức
thật) và trả về instance. *Dependency injection* (DI) là việc class nhận dependency qua constructor
(hoặc tham số method) thay vì tự `new`; container là công cụ làm DI tự động.

Bên trong `Illuminate\Container\Container` có vài mảng chính:

| Thuộc tính | Chứa gì |
|---|---|
| `$bindings` | `abstract => ['concrete' => Closure, 'shared' => bool]` |
| `$instances` | Object đã tạo của các binding shared (singleton, scoped, instance) |
| `$scopedInstances` | Danh sách abstract là scoped, để xoá khi hết request/job |
| `$aliases` / `$abstractAliases` | `'cache'` ↔ `CacheManager::class` ↔ `Contracts\Cache\Factory::class` |
| `$contextual` | Contextual binding: `[class đang build][abstract] => concrete` |
| `$extenders`, các mảng callback `resolving`... | Decorator và hook chạy khi resolve |

Các cách đăng ký, và chúng thật ra là gì trong mã nguồn:

```php
// Trong register() của một service provider, $this->app là container
$this->app->bind(PaymentGateway::class, StripeGateway::class);        // mỗi lần make: object mới
$this->app->singleton(Clock::class, fn () => new SystemClock());      // tạo một lần, dùng lại
$this->app->scoped(TenantContext::class);                             // một lần mỗi request/job
$this->app->instance(Config::class, $alreadyBuiltObject);            // đưa object có sẵn vào
```

- `bind($abstract, $concrete, $shared = false)`: nếu `$concrete` là tên class thì bọc thành closure
  (`getClosure()`), lưu vào `$bindings`. Có thể bỏ `$abstract` và để container suy ra từ kiểu trả về
  của closure: `bind(fn (Application $app): Transistor => ...)`.
- `singleton()` đúng nghĩa đen là `bind($abstract, $concrete, true)`.
- `scoped()` là `singleton()` cộng thêm việc ghi abstract vào `$scopedInstances`.
- `instance()` ghi thẳng vào `$instances`.
- Bản `bindIf`, `singletonIf`, `scopedIf` chỉ đăng ký nếu chưa có ai đăng ký (package hay dùng để app
  ghi đè được).

"Vòng đời" của singleton phụ thuộc vòng đời của **process**, không phải của request:

| | PHP-FPM | Octane / queue worker |
|---|---|---|
| Container sống bao lâu | Một request | Cả process (hàng nghìn request/job) |
| `bind` | Object mới mỗi lần `make` | Như vậy |
| `singleton` | Một object mỗi request | **Một object cho mọi request** của worker đó |
| `scoped` | Như singleton | Bị xoá giữa các request (Octane) và giữa các job (queue: callback reset trong `QueueServiceProvider` gọi `$app->forgetScopedInstances()` và `Facade::clearResolvedInstances()`) |

⚠️ Hệ quả trên Octane: singleton nhận `$app['request']` hoặc cả container trong constructor sẽ giữ
**request (hoặc container) của lần đầu** mãi mãi. Docs Octane khuyên: không inject request/container vào singleton;
nếu cần thì inject closure `fn () => Container::getInstance()`, hoặc truyền dữ liệu request vào tham số
method lúc gọi. State theo user (tenant hiện tại, user đăng nhập) phải là `scoped`, không phải
`singleton`.

Các cách đăng ký nâng cao:

- *Contextual binding*: cùng một interface, class khác nhau nhận bản khác nhau.

  ```php
  $this->app->when(PhotoController::class)
      ->needs(Filesystem::class)
      ->give(fn () => Storage::disk('local'));
  $this->app->when(ReportAggregator::class)->needs('$timezone')->giveConfig('app.timezone');
  ```

  Bên trong, container nhớ mình đang build class nào qua `$buildStack`, và `findInContextualBindings()`
  tra `$contextual[end($buildStack)][$abstract]`.
- *Contextual attribute* (gắn trên tham số constructor): `#[Config('app.timezone')] string $tz`,
  `#[Storage('s3')] Filesystem $disk`, `#[Cache('redis')] Repository $cache`, `#[DB('mysql')]`,
  `#[Log('daily')]`, `#[Auth('web')]`, `#[Give(DatabaseRepository::class)]`, `#[Tag('reports')]`,
  `#[RouteParameter]`, `#[CurrentUser]`. Namespace `Illuminate\Container\Attributes`. Tự viết được bằng
  cách implement `ContextualAttribute` với static method `resolve()`.
- *Attribute trên class/interface* thay cho việc đăng ký trong provider:

  ```php
  use Illuminate\Container\Attributes\{Bind, Singleton};

  #[Bind(RedisEventPusher::class)]
  #[Bind(FakeEventPusher::class, environments: ['local', 'testing'])]
  #[Singleton]
  interface EventPusher {}
  ```

  Container đọc các attribute này bằng Reflection ở lần resolve đầu (`getConcreteBindingFromAttributes()`,
  `getScopedTyped()`) và nhớ kết quả. Có thêm `#[Scoped]`, và `#[BindWhen(Concrete::class, closure)]`
  (docs ghi cần PHP 8.5, vì dùng closure trong biểu thức hằng của attribute).
- *Tagging*: `$this->app->tag([CpuReport::class, MemoryReport::class], 'reports')` rồi
  `$this->app->tagged('reports')` trả về iterable resolve lười từng phần tử.
- `extend($abstract, fn ($service, $app) => new LoggingDecorator($service))`: *decorator*, chạy mỗi khi
  abstract được build (trong `resolve()`, ngay sau `build()`).
- Hook: `beforeResolving`, `resolving`, `afterResolving`. Chính Laravel dùng `afterResolving(HttpKernel)`
  để áp cấu hình middleware (bước 2 ở trên).

#### Service container: auto-wiring

*Auto-wiring* (Laravel gọi là *zero configuration resolution*): container tự tạo được class mà không
cần đăng ký, bằng cách đọc type hint của constructor qua *Reflection* (API của PHP để đọc cấu trúc
class, method, tham số lúc chạy). Khi gọi `app(OrderService::class)`, đường đi trong mã nguồn:

1. `Application::make()`: đổi alias thành tên thật (`getAlias()`), và nếu abstract thuộc một deferred
   provider thì nạp provider đó trước (`loadDeferredProviderIfNeeded()`).
2. `Container::resolve()`:
   1. Bắn `beforeResolving` callback.
   2. Tìm contextual binding cho class đang build. Nếu có instance shared trong `$instances` và không
      có tham số/contextual đặc biệt thì **trả luôn** (đường tắt của singleton).
   3. `getConcrete()`: có trong `$bindings` thì lấy closure; không có thì đọc attribute `#[Bind]`;
      không có nữa thì concrete chính là tên class.
   4. `isBuildable()` (concrete trùng abstract hoặc là closure) thì `build()`, ngược lại `make()` đệ quy
      concrete (ví dụ interface → class).
   5. Áp các `extend()`; nếu shared thì lưu vào `$instances`; bắn `resolving`/`afterResolving`.
3. `Container::build($concrete)`:
   1. Concrete là closure: gọi `$concrete($this, $parameters)`.
   2. `new ReflectionClass($concrete)`; class không tồn tại thì `BindingResolutionException("Target
      class [X] does not exist.")`.
   3. `isInstantiable()` sai (interface, abstract class, constructor private) thì
      `notInstantiable()`: "Target [App\Contracts\Clock] is not instantiable while building
      [App\Services\OrderService]."
   4. Không có constructor thì `new $concrete`.
   5. Có constructor thì `resolveDependencies($constructor->getParameters())`, rồi
      `new $concrete(...$instances)`.
4. `resolveDependencies()` với từng `ReflectionParameter`:
   1. Có giá trị truyền tay qua `makeWith(X::class, ['name' => ...])` thì dùng.
   2. Có contextual attribute (`#[Config]`...) thì để attribute resolve.
   3. Type là class/interface: `resolveClass()`, tức `make()` **đệ quy**. Riêng trường hợp tham số có
      giá trị mặc định và kiểu đó không được bind thì dùng giá trị mặc định.
   4. Type là scalar hoặc không có type: `resolvePrimitive()`: contextual `'$name'` → giá trị mặc định
      → variadic thì `[]` → kiểu nullable thì `null` → còn lại ném "Unresolvable dependency resolving
      [Parameter #0 [ <required> string $apiKey ]] in class ...".

Tự viết một container mini để thấy rõ ý tưởng (chạy `php mini-container.php`):

```php
<?php
declare(strict_types=1);

final class MiniContainer
{
    /** @var array<string, array{factory: Closure, shared: bool}> */
    private array $bindings = [];
    /** @var array<string, object> */
    private array $instances = [];
    /** @var list<string> class đang build, để phát hiện vòng phụ thuộc */
    private array $buildStack = [];

    public function bind(string $abstract, Closure|string|null $concrete = null, bool $shared = false): void
    {
        $concrete ??= $abstract;
        $factory = $concrete instanceof Closure
            ? $concrete
            // như Container::getClosure(): trùng tên thì build, khác tên thì make (đi tiếp qua binding)
            : fn (self $c): object => $concrete === $abstract ? $c->build($concrete) : $c->make($concrete);
        $this->bindings[$abstract] = ['factory' => $factory, 'shared' => $shared];
        unset($this->instances[$abstract]);
    }

    public function singleton(string $abstract, Closure|string|null $concrete = null): void
    {
        $this->bind($abstract, $concrete, true);
    }

    public function make(string $abstract): object
    {
        if (isset($this->instances[$abstract])) {
            return $this->instances[$abstract];                  // đường tắt của singleton
        }
        $binding = $this->bindings[$abstract] ?? null;
        $object = $binding !== null ? ($binding['factory'])($this) : $this->build($abstract);
        if ($binding !== null && $binding['shared'] === true) {
            $this->instances[$abstract] = $object;
        }
        return $object;
    }

    private function build(string $class): object
    {
        if (in_array($class, $this->buildStack, true)) {
            throw new LogicException('Vòng phụ thuộc: ' . implode(' -> ', [...$this->buildStack, $class]));
        }
        $ref = new ReflectionClass($class);                      // ReflectionException nếu không tồn tại
        if (!$ref->isInstantiable()) {
            throw new LogicException('Target [' . $class . '] is not instantiable');
        }
        $ctor = $ref->getConstructor();
        if ($ctor === null) {
            return new $class();
        }
        $this->buildStack[] = $class;
        try {
            $args = [];
            foreach ($ctor->getParameters() as $param) {
                $type = $param->getType();
                if ($type instanceof ReflectionNamedType && !$type->isBuiltin()) {
                    $args[] = $this->make($type->getName());     // đệ quy
                } elseif ($param->isDefaultValueAvailable()) {
                    $args[] = $param->getDefaultValue();
                } else {
                    throw new LogicException('Unresolvable $' . $param->getName() . ' in ' . $class);
                }
            }
        } finally {
            array_pop($this->buildStack);
        }
        return new $class(...$args);
    }
}

interface Clock { public function today(): string; }
final class FixedClock implements Clock { public function today(): string { return '2026-09-27'; } }
final class Mailer { public function __construct(public string $from = 'no-reply@shop.test') {} }
final class OrderService { public function __construct(public Clock $clock, public Mailer $mailer) {} }
final class NeedsKey { public function __construct(public string $apiKey) {} }

$c = new MiniContainer();
$c->singleton(Clock::class, FixedClock::class);

$a = $c->make(OrderService::class);          // không đăng ký OrderService, Mailer: auto-wiring
$b = $c->make(OrderService::class);
var_dump($a === $b);                         // bool(false): OrderService không shared
var_dump($a->clock === $b->clock);           // bool(true): Clock là singleton
echo $a->clock->today(), ' ', $a->mailer->from, PHP_EOL;   // 2026-09-27 no-reply@shop.test

foreach ([fn () => (new MiniContainer())->make(OrderService::class), fn () => $c->make(NeedsKey::class)] as $try) {
    try { $try(); } catch (LogicException $e) { echo $e->getMessage(), PHP_EOL; }
}
// Target [Clock] is not instantiable
// Unresolvable $apiKey in NeedsKey
```

So với container thật, bản mini thiếu: alias, contextual binding, attribute, extender, callback,
deferred provider, cache kết quả Reflection. Nhưng lõi `build()` + `resolveDependencies()` đúng là thế.

⚠️ Type hint là **interface** mà chưa bind (và interface không có `#[Bind]`) thì ném
`BindingResolutionException` "not instantiable". Tham số scalar không có default, không nullable,
không có contextual binding thì ném "Unresolvable dependency".

⚠️ Vòng phụ thuộc (A cần B, B cần A): container 13.x **không** có bước kiểm tra vòng như bản mini ở
trên (chỉ khai báo `@throws CircularDependencyException` trong docblock). Đệ quy chạy tới khi hết stack
hoặc hết `memory_limit`. Thấy fatal error khó hiểu khi resolve thì nghĩ tới vòng phụ thuộc.

⚠️ *Service locator*: rải `app(X::class)` hoặc `resolve()` trong domain code, tức class tự đi xin
dependency thay vì nhận qua constructor. Dependency bị giấu khỏi chữ ký, khó đọc, test phải dựng cả
container. Dùng `app()` ở chỗ "biên" (provider, route closure, factory), còn domain code nhận qua
constructor.

Container còn gọi được **method** với injection: `$app->call([$obj, 'handle'], ['id' => 5])` resolve các
tham số còn lại theo type hint. Đây là cách `boot()` của provider, `handle()` của job, method của
controller nhận dependency.

#### Service provider

*Service provider* là class nơi app (và package) khai báo service với container. Hai method, hai giai
đoạn:

| | `register()` | `boot()` |
|---|---|---|
| Khi nào chạy | Bootstrapper `RegisterProviders`, lần lượt từng provider | Bootstrapper `BootProviders`, sau khi **mọi** provider đã register |
| Được làm gì | Chỉ `bind`/`singleton`/`scoped`/`extend`... vào container | Dùng service bất kỳ: route, event listener, observer, macro, view composer, `Gate::define`, `Model::preventLazyLoading()` |
| Injection | Không (không tham số) | Có: `Application::bootProvider()` gọi `$this->call([$provider, 'boot'])`, nên type hint tham số của `boot()` được resolve |

Thứ tự register, theo `Application::registerConfiguredProviders()`: provider của framework
(`Illuminate\...`) trước, rồi provider của package (tự phát hiện qua `extra.laravel.providers` trong
composer.json của package, đọc từ `PackageManifest`), rồi provider của app trong `bootstrap/providers.php`.
Provider cũng có thể khai báo mảng `$bindings` và `$singletons` thay vì viết tay trong `register()`;
`Application::register()` đọc hai thuộc tính này ngay sau khi gọi `register()`.

⚠️ Vì sao không được **dùng** service trong `register()`:

```php
<?php
declare(strict_types=1);

namespace App\Providers;

use App\Services\Reporting;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\ServiceProvider;

final class ReportingServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(Reporting::class);          // ĐÚNG: chỉ khai báo công thức

        // SAI: resolve ngay trong register
        // $this->app->make(Reporting::class)->warmUp();
        //   Reporting (và dependency của nó) được tạo khi provider phía sau chưa register:
        //   binding của dependency có thể chưa có, callback resolving() đăng ký sau không chạy
        //   cho instance đã tạo, và vì là singleton nên bản "thiếu" đó bị giữ lại.
        // Route::get('/reports', ...);
        //   Route đăng ký ở đây đi trước mọi thứ ở boot, dễ lệch thứ tự.
    }

    public function boot(Reporting $reporting): void      // injection trong boot
    {
        Route::middleware('web')->get('/reports', fn () => $reporting->summary());
    }
}
```

Nếu app **đã boot** rồi mà bạn gọi `$app->register(new XProvider($app))`, `Application::register()` gọi
luôn `boot()` của provider đó.

*Deferred provider*: provider chỉ đăng ký binding có thể hoãn tới khi có người thật sự cần.

```php
<?php
declare(strict_types=1);

namespace App\Providers;

use App\Services\Riak\Connection;
use Illuminate\Contracts\Support\DeferrableProvider;
use Illuminate\Support\ServiceProvider;

final class RiakServiceProvider extends ServiceProvider implements DeferrableProvider
{
    public function register(): void
    {
        $this->app->singleton(Connection::class, fn ($app) => new Connection($app['config']['riak']));
    }

    /** @return list<string> */
    public function provides(): array
    {
        return [Connection::class];
    }
}
```

Cơ chế (`Illuminate\Foundation\ProviderRepository`):

1. Lần đầu (hoặc khi danh sách provider đổi), Laravel tạo từng provider, hỏi `isDeferred()`, và ghi
   *manifest* ra `bootstrap/cache/services.php`: mảng `eager` (nạp mọi request), `deferred`
   (`service => provider`), `when` (event kích hoạt nạp provider).
2. Mỗi request: chỉ `register()` các provider `eager`; danh sách `deferred` được đưa vào
   `$app->addDeferredServices()`.
3. Khi code `make(Connection::class)`, `Application::make()` thấy đây là deferred service, gọi
   `loadDeferredProvider()`: register provider đó, và boot nó (ngay, hoặc qua callback `booting` nếu
   app chưa boot).

Chính framework dùng cơ chế này nhiều: `CacheServiceProvider` là deferred, nên request không đụng tới
cache thì không bao giờ tạo `CacheManager`.

⚠️ Deferred provider không được làm gì trong `boot()` mà request cần có sẵn (đăng ký route, listener),
vì nếu không ai resolve service của nó thì `boot()` không bao giờ chạy.

#### Facade

*Facade* là class cho phép gọi kiểu static (`Cache::get('k')`) nhưng thật ra chuyển lời gọi tới một
object lấy từ container. Class `Illuminate\Support\Facades\Cache` không có method `get` nào; phần cốt
lõi của nó là:

```php
protected static function getFacadeAccessor()
{
    return 'cache';                                 // tên binding trong container
}
```

`Cache::get('user:1')` đi qua những hàm sau (đọc thẳng từ mã nguồn 13.x):

1. PHP không thấy static method `get` trên `Cache` nên gọi magic method
   `Facade::__callStatic('get', ['user:1'])` (module 1.3).
2. `__callStatic` gọi `static::getFacadeRoot()`, tức
   `static::resolveFacadeInstance(static::getFacadeAccessor())` với tên `'cache'`.
3. `resolveFacadeInstance('cache')`: có trong `static::$resolvedInstance['cache']` thì trả luôn. Chưa
   có thì lấy `static::$app['cache']` (`Container::offsetGet()` → `make('cache')`) và, vì
   `static::$cached = true` mặc định, lưu vào `$resolvedInstance`.
4. `Application::make('cache')`: `'cache'` là deferred service, nên nạp `CacheServiceProvider`, provider
   này `singleton('cache', fn ($app) => new CacheManager($app))`. Container build `CacheManager`, lưu
   vào `$instances`.
5. Không có root thì ném `RuntimeException('A facade root has not been set.')` (hay gặp khi dùng
   facade ngoài Laravel hoặc trong unit test không boot app). Có root thì `$instance->get('user:1')`.
6. `CacheManager` cũng không có method `get`: `CacheManager::__call()` chuyển sang
   `$this->store()->get(...)`. `store()` lấy store mặc định theo `config('cache.default')`, ví dụ
   `redis`, trả về `Illuminate\Cache\Repository` bọc một `RedisStore`.
7. `Repository::get()`: bắn event `RetrievingKey`, gọi `$this->store->get($this->itemKey($key))`; miss
   thì bắn `CacheMissed` và trả default; hit thì `CacheHit`.
8. `RedisStore::get()`: `$this->connection()->get($this->prefix.$key)` qua phpredis/predis, rồi
   unserialize giá trị.

```text
Cache::get('user:1')
 → Facade::__callStatic('get', ['user:1'])
   → getFacadeRoot() → resolveFacadeInstance('cache')
       → static::$resolvedInstance['cache'] ?? static::$app['cache']
            → Application::make('cache')  (nạp deferred CacheServiceProvider lần đầu)
            → CacheManager (singleton)
 → CacheManager::__call('get') → store() → Repository(RedisStore)
 → Repository::get() → RedisStore::get() → Redis GET "<prefix>user:1" → unserialize
```

Một số chi tiết đáng biết:

- `$resolvedInstance` là static property của **class cha** `Facade`, dùng chung cho mọi facade, key là
  accessor. Bootstrapper `RegisterFacades` gọi `Facade::clearResolvedInstances()` mỗi lần boot; queue
  worker gọi lại giữa các job; Octane cũng reset.
- *Alias* như `Cache` (không namespace) trong Blade hay code cũ là nhờ `AliasLoader`: đăng ký
  `spl_autoload_register` ở đầu hàng đợi, gặp tên alias thì `class_alias()` về class facade thật.
- Test: `Cache::shouldReceive('get')->with('k')->andReturn('v')` thay root bằng một Mockery mock
  (`swap()` ghi vào cả `$resolvedInstance` và container). Các facade có `fake()` (`Queue::fake()`,
  `Mail::fake()`, `Event::fake()`) cũng dựa trên `swap()`.
- Helper và facade tương đương: `cache('k')` gọi đúng object mà facade `Cache` dùng, nên
  `Cache::shouldReceive()` vẫn bắt được.
- *Real-time facade*: `use Facades\App\Services\Payment;` rồi gọi `Payment::charge()`. `AliasLoader`
  thấy tiền tố `Facades\`, sinh một class facade có accessor là `App\Services\Payment` và lưu ở
  `storage/framework/cache/facade-<sha1>.php`.

Mô phỏng cơ chế trong một file (chạy `php mini-facade.php`):

```php
<?php
declare(strict_types=1);

final class Registry
{
    /** @var array<string, Closure(): object> */
    private array $factories = [];
    public int $made = 0;

    public function set(string $name, Closure $factory): void { $this->factories[$name] = $factory; }
    public function make(string $name): object { $this->made++; return ($this->factories[$name])(); }
}

abstract class Facade
{
    protected static ?Registry $app = null;
    /** @var array<string, object> dùng chung cho mọi facade con, key là accessor */
    protected static array $resolvedInstance = [];

    abstract protected static function getFacadeAccessor(): string;

    public static function setFacadeApplication(Registry $app): void { static::$app = $app; }

    public static function swap(object $fake): void
    {
        static::$resolvedInstance[static::getFacadeAccessor()] = $fake;
    }

    /** @param array<int, mixed> $args */
    public static function __callStatic(string $method, array $args): mixed
    {
        $name = static::getFacadeAccessor();
        $instance = static::$resolvedInstance[$name] ??= static::$app->make($name);
        return $instance->$method(...$args);
    }
}

final class ArrayStore
{
    /** @param array<string, mixed> $data */
    public function __construct(private array $data = []) {}
    public function get(string $key, mixed $default = null): mixed { return $this->data[$key] ?? $default; }
    public function put(string $key, mixed $value): void { $this->data[$key] = $value; }
}

final class Cache extends Facade
{
    protected static function getFacadeAccessor(): string { return 'cache'; }
}

$app = new Registry();
$app->set('cache', fn (): ArrayStore => new ArrayStore());
Facade::setFacadeApplication($app);

Cache::put('k', 42);
var_dump(Cache::get('k'));                        // int(42)
var_dump($app->made);                             // int(1): lần gọi thứ hai lấy từ $resolvedInstance

Cache::swap(new ArrayStore(['k' => 'fake']));     // ý tưởng của shouldReceive()/fake()
var_dump(Cache::get('k'));                        // string(4) "fake"
```

Tranh luận facade hay DI: docs Laravel nêu rủi ro chính là *scope creep*. Constructor dài là tín hiệu
trực quan "class này làm quá nhiều", còn facade gọi được ở bất kỳ dòng nào nên class phình ra mà không
ai thấy. Cách dùng thực tế: facade ở controller, route, code mỏng; DI qua constructor (type hint
contract như `Illuminate\Contracts\Cache\Repository`) trong domain service quan trọng. Về test thì hai
cách ngang nhau, vì facade mock được.

#### Chạy sau khi gửi response

Ba cơ chế cùng chạy ở bước 9 của lifecycle, **sau** `fastcgi_finish_request()`:

1. *Terminable middleware*: middleware có method `terminate(Request $request, Response $response)`.
   Phải nằm trong danh sách global hoặc route middleware.
2. `$app->terminating(fn () => ...)`: callback đăng ký lúc chạy.
3. `defer()` (hàm `Illuminate\Support\defer`, từ Laravel 11): closure được gom vào
   `DeferredCallbackCollection` và chạy bởi global middleware `InvokeDeferredCallbacks` trong
   `terminate()` của nó.

```php
use function Illuminate\Support\defer;   // import tường minh, tránh đụng hàm defer() của Swoole

Route::post('/orders', function (StoreOrderRequest $request) {   // FormRequest: có validated()
    $order = Order::create($request->validated());
    defer(fn () => Metrics::reportOrder($order));            // chỉ chạy khi status < 400
    defer(fn () => Audit::log('order.create'))->always();    // chạy cả khi 4xx/5xx
    return $order;                                           // model mới tạo → JSON 201
});
```

⚠️ `terminate()` được gọi trên một instance **mới** resolve từ container (`terminateMiddleware()` gọi
`$this->app->make($name)`), không phải instance đã chạy `handle()`. Muốn giữ state giữa `handle()` và
`terminate()` thì đăng ký middleware đó là `singleton` trong `register()`.

⚠️ Sau `fastcgi_finish_request()` client đã xong, nhưng worker FPM **vẫn bận** tới khi phần terminate
chạy xong: không nhận request khác. Mặc định `request_terminate_timeout` **không** còn áp sau
`fastcgi_finish_request()` (trừ khi bật `request_terminate_timeout_track_finished`), nên phần terminate
treo có thể giữ worker lâu hơn giới hạn bạn nghĩ. 100 request mỗi cái
defer 2 giây là 100 worker bị giữ thêm 2 giây. Việc nặng, việc cần retry, việc phải chạy chắc chắn: đưa
vào queue (module 2.6). `defer()` hợp với việc nhỏ, mất cũng không sao (ghi metric, xoá cache).

⚠️ Trên server không có `fastcgi_finish_request()` (ví dụ `php artisan serve` thuần, một số SAPI
khác), `send()` chỉ flush output, và client có thể phải chờ cả phần terminate.

#### Laravel 13

- Attribute cho controller, namespace `Illuminate\Routing\Attributes\Controllers`: `#[Middleware]`
  (tham số `middleware`, `only`, `except`; lặp lại được; gắn trên class hoặc method) và `#[Authorize]`
  (kế thừa `Middleware`, dựng middleware `can` từ ability và model).

  ```php
  use Illuminate\Routing\Attributes\Controllers\{Authorize, Middleware};

  #[Middleware('auth')]
  #[Middleware('throttle:60,1', only: ['store'])]
  final class PostController
  {
      #[Authorize('update', 'post')]
      public function update(Post $post): RedirectResponse { /* ... */ }
  }
  ```

- `PreventRequestForgery` là middleware CSRF trong group `web` mặc định (class cũ `VerifyCsrfToken`
  vẫn còn trong framework). *CSRF* (Cross-Site Request Forgery): trang web khác lừa trình duyệt của
  user gửi request kèm cookie đăng nhập. Thứ tự kiểm trong `handle()`: method đọc (`GET`, `HEAD`,
  `OPTIONS`) cho qua; URI trong danh sách except cho qua; header `Sec-Fetch-Site` (trình duyệt tự gắn,
  cho biết request đến từ đâu) là `same-origin` thì cho qua (`same-site` nếu bật cho phép); còn lại so
  token `_token`/`X-CSRF-TOKEN`/`X-XSRF-TOKEN` với session bằng `hash_equals`, sai thì
  `TokenMismatchException` (trang 419). Chế độ chỉ kiểm origin bỏ hẳn token: bật bằng
  `$middleware->preventRequestForgery(originOnly: true)` trong `bootstrap/app.php` (bên dưới gọi
  `PreventRequestForgery::useOriginOnly()`); origin không khớp thì ném `OriginMismatchException`.
- Laravel 13 yêu cầu PHP ≥ 8.3 (`composer.json` của framework), dùng `symfony/http-foundation` 7.4 hoặc
  8.x.

**Tóm tắt nhanh**

- Lifecycle: `index.php` → `bootstrap/app.php` tạo `Application` (chính là container) →
  `handleRequest` → `Kernel::handle`: 6 bootstrapper (env, config, exceptions, facades, **register**,
  **boot**) → global middleware → Router → route middleware → controller → `toResponse` → `send()`
  (`fastcgi_finish_request`) → `terminate()`.
- `singleton` = `bind(..., shared: true)`; `scoped` = singleton bị xoá bởi `forgetScopedInstances()`
  giữa request Octane/job queue. Trên FPM ba cái gần như như nhau; trên Octane singleton sống cả
  process, đừng nhét request/user vào đó.
- Auto-wiring: `build()` dùng `ReflectionClass`, `resolveDependencies()` đệ quy `make()` theo type hint;
  interface chưa bind và scalar không default là hai lỗi `BindingResolutionException` kinh điển.
- `register()` chỉ khai báo binding; `boot()` chạy sau khi mọi provider đã register và được method
  injection. Deferred provider ghi vào `bootstrap/cache/services.php`, chỉ nạp khi service được resolve.
- `Cache::get()` = `__callStatic` → `getFacadeAccessor()` (`'cache'`) → `$app['cache']` (cache vào
  `$resolvedInstance`) → `CacheManager::__call` → `Repository` → `RedisStore`.

**Nguồn**: [Laravel: Request Lifecycle](https://laravel.com/docs/lifecycle) ·
[Laravel: Service Container](https://laravel.com/docs/container) ·
[Laravel: Service Providers](https://laravel.com/docs/providers) ·
[Laravel: Facades](https://laravel.com/docs/facades#how-facades-work) ·
[Laravel: Terminable Middleware](https://laravel.com/docs/middleware#terminable-middleware) ·
[Laravel: Deferred Functions](https://laravel.com/docs/helpers#deferred-functions) ·
[Laravel: Octane, Dependency Injection](https://laravel.com/docs/octane#dependency-injection-and-octane) ·
[Container.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Container/Container.php) ·
[Application.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Application.php) ·
[Http/Kernel.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Http/Kernel.php) ·
[Facade.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Support/Facades/Facade.php) ·
[ProviderRepository.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/ProviderRepository.php) ·
[Configuration/Middleware.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Configuration/Middleware.php) ·
[skeleton bootstrap/app.php](https://github.com/laravel/laravel/blob/13.x/bootstrap/app.php) ·
[PHP: fastcgi_finish_request](https://www.php.net/manual/en/function.fastcgi-finish-request.php)


---

### 2.5 Eloquent ở mức làm chủ

Module này trả lời: model Eloquent làm những gì ngầm khi bạn đọc, ghi, xoá (cast, accessor, scope,
event), những hành vi ngầm đó biến mất ở đâu (query builder, mass update), và vì sao chúng là nguồn
của các bug "observer không chạy", "báo cáo thiếu dữ liệu".

Phần tầng DB đã viết kỹ ở [03-database-sql.md, module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel),
ở đây chỉ nhắc lại để nối mạch:

- N+1: lazy loading trong vòng lặp; không lên slow query log vì từng query đều nhanh. Sửa bằng
  `with`, `load`, `withCount`; bắt ở dev bằng `preventLazyLoading`.
- `chunkById` thay cho `chunk` khi callback sửa cột đang lọc; `cursor()` vẫn buffer raw row.
- `DB::transaction(fn, attempts)` chạy lại cả closure khi deadlock/lock wait timeout; job dispatch
  trong transaction cần `afterCommit`; muốn chắc chắn tuyệt đối thì outbox.
- `sticky` chỉ giữ read-your-writes trong một request.

Soft delete và unique index, polymorphic không có FK: phần schema ở
[03-database-sql.md, module 2.8](03-database-sql.md#28-thiết-kế-schema-nâng-cao). Module này chỉ bàn
phần thuộc về model.

Một điểm mới của Laravel 13 cần biết khi đọc docs: cấu hình model có thể viết bằng PHP attribute
(`#[Table('flights')]`, `#[Fillable(['name'])]`, `#[ScopedBy(...)]`, `#[ObservedBy(...)]`,
`#[Appends(...)]`). Property kiểu cũ (`protected $fillable = [...]`) vẫn chạy; mã nguồn
`GuardsAttributes` 13.x gộp giá trị từ attribute `Fillable` vào `$fillable`. Ví dụ dưới đây dùng
property vì đa số codebase hiện có viết như vậy.

#### Relationship nâng cao

*Has-many-through* là quan hệ "đi xuyên" một bảng trung gian mà bảng đích không có khoá trỏ thẳng
về bảng nguồn. Ví dụ `countries` → `users` (có `country_id`) → `posts` (có `user_id`). Bảng `posts`
không có `country_id`, nhưng muốn lấy mọi bài viết của một nước:

```php
<?php
declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasManyThrough;

class Country extends Model
{
    public function posts(): HasManyThrough
    {
        // tham số 1: model đích, tham số 2: model trung gian
        return $this->hasManyThrough(Post::class, User::class);
        // Khoá mặc định: users.country_id, posts.user_id.
        // Viết tường minh: hasManyThrough(Post::class, User::class, 'country_id', 'user_id', 'id', 'id')
    }
}

// $country->posts sinh một query JOIN qua bảng trung gian, đại ý:
// SELECT posts.*, users.country_id FROM posts
//   INNER JOIN users ON users.id = posts.user_id
//   WHERE users.country_id = ?
```

- `hasOneThrough` giống vậy nhưng trả một model (ví dụ `Mechanic` → `Car` → `Owner`).
- Nếu các quan hệ từng chặng đã có sẵn, viết gọn `$this->through('users')->has('posts')`: tái dùng
  quy ước khoá của các quan hệ đã khai báo, đỡ nhầm thứ tự bốn tham số khoá.

*Many-to-many* (`belongsToMany`): một user có nhiều role, một role thuộc nhiều user. Cần *pivot
table* (bảng nối) chứa hai khoá ngoại. Quy ước tên: tên hai model số ít, xếp theo **thứ tự bảng chữ
cái**, nối bằng `_`: `Role` và `User` thành `role_user` (không phải `user_role`).

```php
public function roles(): BelongsToMany
{
    return $this->belongsToMany(Role::class)
        ->withPivot('expires_at', 'granted_by')  // mặc định pivot chỉ có hai khoá, cột khác phải khai
        ->withTimestamps()                       // pivot phải có đủ created_at VÀ updated_at
        ->wherePivotNull('revoked_at');          // lọc theo cột của bảng nối
}

foreach ($user->roles as $role) {
    echo $role->pivot->expires_at;               // đổi tên 'pivot' bằng ->as('grant')
}
```

Các thao tác ghi lên bảng nối:

| Method | Làm gì | Ghi chú |
|---|---|---|
| `attach($id, [...])` | INSERT một dòng pivot | Gọi hai lần là hai dòng trùng nếu không có unique `(user_id, role_id)` |
| `detach($id)` / `detach()` | DELETE dòng pivot (không có id là xoá hết) | Hai model hai đầu vẫn còn |
| `sync([1, 2, 3])` | Đưa pivot về đúng tập này: thêm cái thiếu, **xoá cái không có trong mảng** | Truyền nhầm mảng rỗng là xoá sạch |
| `syncWithoutDetaching([...])` | Chỉ thêm, không xoá | Dùng khi "cấp thêm quyền" |
| `toggle([...])` | Có thì bỏ, chưa có thì thêm | |
| `attachOrFail`, `syncOrFail`... | Như trên nhưng bọc transaction | Có trong docs 13.x |

⚠️ Mặc định Laravel ghi pivot bằng query builder, nên không có model event nào. Khai báo model pivot
riêng bằng `->using(RoleUser::class)` (class kế thừa `Pivot`) thì `attach`/`detach`/
`updateExistingPivot` đi qua model đó và event của pivot mới chạy. Pivot model không dùng được
`SoftDeletes`; cần xoá mềm quan hệ thì biến bảng nối thành model thật.

*Polymorphic relationship*: một bảng con thuộc về nhiều loại cha qua cặp cột `*_type` + `*_id`.

```php
<?php
declare(strict_types=1);

// migration: $table->morphs('commentable');
//   tạo commentable_type VARCHAR, commentable_id BIGINT UNSIGNED, index (type, id)

class Comment extends Model
{
    public function commentable(): MorphTo
    {
        return $this->morphTo();          // đọc commentable_type để biết phải query bảng nào
    }
}

class Post extends Model
{
    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }
}

// AppServiceProvider::boot()
Relation::enforceMorphMap([
    'post'  => Post::class,
    'video' => Video::class,
]);
// Không có morph map: commentable_type = 'App\Models\Post'. Có: commentable_type = 'post'.
```

- ⚠️ Không có morph map thì cột type lưu tên class đầy đủ; đổi namespace hay đổi tên model là dữ
  liệu cũ trỏ vào class không tồn tại. `enforceMorphMap` (khác `morphMap`) còn **ném exception** khi
  gặp model chưa khai báo alias, nên không thể lỡ tay ghi tên class vào DB. Thêm morph map vào app
  đang chạy thì phải migrate các giá trị type cũ.
- ⚠️ Cái giá: `commentable_id` trỏ tới nhiều bảng tuỳ giá trị cột khác, nên **không đặt được khoá
  ngoại**. Không có cascade, comment mồ côi khi xoá post, sai type không ai chặn. Hai thiết kế thay
  thế có FK nằm ở module 2.8 file 03.
- Eager load `morphTo` phải chạy **một query cho mỗi loại cha** (một cho posts, một cho videos), và
  muốn nạp tiếp quan hệ con khác nhau theo từng loại thì dùng `morphWith`.

Hai công cụ chống N+1 ở quan hệ ngược, có trong docs 13.x:

- `chaperone()`: `Post::with('comments')` rồi truy cập `$comment->post` trong vòng lặp vẫn N+1, vì
  Eloquent không tự gán cha vào con. `hasMany(Comment::class)->chaperone()` gán sẵn.
- `withAttributes([...])` trên quan hệ có điều kiện (`featuredPosts()`): vừa thêm `where`, vừa tự
  điền giá trị khi `create()` qua quan hệ đó. Chỉ `where('featured', true)` thì bài tạo qua
  `featuredPosts()->create()` vẫn có `featured = false`.

#### Eager loading nâng cao và strict mode

Phần cơ bản (`with`, `load`, `withCount`) ở file 03. Các biến thể cần biết thêm:

```php
// Nạp quan hệ kèm điều kiện: chỉ comment đã duyệt, mới nhất trước
$posts = Post::with(['comments' => fn (Builder $q) => $q->where('approved', true)->latest()])->get();

// Số liệu tổng hợp bằng subquery, không nạp model con nào
$posts = Post::withCount('comments')             // $post->comments_count
    ->withSum('orderItems', 'price')             // $post->order_items_sum_price
    ->withExists('likes')                        // $post->likes_exists (bool)
    ->get();

// Collection đã có: chỉ nạp những quan hệ chưa nạp
$posts->loadMissing('author');

// whereHas lọc CHA theo điều kiện con; with nạp CON. Hai việc khác nhau, hay phải dùng cùng lúc:
Post::whereHas('comments', fn ($q) => $q->where('flagged', true))
    ->with(['comments' => fn ($q) => $q->where('flagged', true)])
    ->get();
```

⚠️ `whereHas` không nạp gì cả. Viết `whereHas` rồi truy cập `$post->comments` là thêm N query và
nhận **toàn bộ** comment, không chỉ comment thoả điều kiện. `withWhereHas('comments', fn)` gộp hai
việc trên làm một.

*Automatic eager loading* (Laravel 12.x trở đi, có trong 13): `Model::automaticallyEagerLoadRelationships()`
trong `AppServiceProvider::boot()`. Khi truy cập một quan hệ chưa nạp trên model thuộc một
collection, Laravel lazy eager load quan hệ đó cho **cả collection gốc** một lần, kể cả lồng nhiều
tầng (`$user->posts` rồi `$post->comments`). Bật cho riêng một collection: `$users->withRelationshipAutoloading()`.
Nó giảm số query, không giảm lượng dữ liệu kéo về; các endpoint quan trọng vẫn nên `with` có chủ
đích.

*Strict mode*: `Model::shouldBeStrict(bool)` là phím tắt gọi cùng lúc ba method (đọc từ `Model.php`
13.x):

| Method | Chặn gì | Không bật thì |
|---|---|---|
| `preventLazyLoading()` | Truy cập quan hệ chưa nạp: ném `LazyLoadingViolationException` | Âm thầm chạy thêm query (N+1) |
| `preventSilentlyDiscardingAttributes()` | `fill`/`create`/`update` với key không nằm trong `$fillable`: ném `MassAssignmentException` | Key đó bị **bỏ qua lặng lẽ**, dữ liệu không được lưu mà không ai biết |
| `preventAccessingMissingAttributes()` | Đọc attribute không có trong kết quả: ném `MissingAttributeException` | Trả `null`, không phân biệt được "cột NULL" với "quên select cột" |

```php
<?php
declare(strict_types=1);

namespace App\Providers;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        Model::shouldBeStrict(! $this->app->isProduction());

        // Production: không ném, chỉ log để thấy N+1 còn sót
        if ($this->app->isProduction()) {
            Model::handleLazyLoadingViolationUsing(function (Model $model, string $relation): void {
                logger()->warning('lazy load', ['model' => $model::class, 'relation' => $relation]);
            });
        }
    }
}
```

Hai chi tiết đọc từ mã nguồn mà người phỏng vấn hay dùng để hỏi vặn:

1. `preventLazyLoading` chỉ có hiệu lực với model được hydrate từ một kết quả có **nhiều hơn một
   dòng** (`Builder::hydrate` chỉ gán cờ khi `count($items) > 1`). `User::find(1)->posts` không bị
   chặn, vì một model đơn lẻ không thể gây N+1.
2. `preventAccessingMissingAttributes` không ném với model vừa tạo (`wasRecentlyCreated`), vì model
   mới tạo không có đủ mọi cột mặc định từ DB.

⚠️ Khi bật strict mode trên project cũ, lỗi hay gặp nhất không phải N+1 mà là
`MassAssignmentException`: rất nhiều `update($request->all())` đang âm thầm vứt field. Đó chính là
bug đã tồn tại từ trước, strict mode chỉ làm nó hiện ra.

#### Cast, accessor, mutator

*Cast* là khai báo kiểu cho một attribute: Eloquent tự đổi khi đọc ra từ DB và khi ghi vào DB. Từ
Laravel 11, khai báo trong method `casts()` (property `$casts` vẫn chạy):

```php
protected function casts(): array
{
    return [
        'is_admin'    => 'boolean',              // 0/1 trong DB, true/false trong PHP
        'options'     => 'array',                // cột JSON <-> array
        'settings'    => AsArrayObject::class,   // như array nhưng sửa được từng key
        'paid_at'     => 'immutable_datetime',   // CarbonImmutable
        'amount'      => 'decimal:2',            // trả về STRING "1234.50", không phải float
        'status'      => OrderStatus::class,     // backed enum
        'api_token'   => 'encrypted',            // mã hoá bằng APP_KEY khi lưu
        'password'    => 'hashed',               // tự hash khi gán chuỗi thô
    ];
}
```

Cạm bẫy của từng loại:

- ⚠️ `array`: `$user->options['theme'] = 'dark'` **không** có tác dụng và PHP báo lỗi *indirect
  modification of overloaded property*. Lý do: `$user->options` đi qua magic `__get`, trả về một bản
  **copy** của mảng (module 1.2), sửa bản copy không đổi gì trên model. Phải lấy ra, sửa, gán lại;
  hoặc dùng `AsArrayObject`/`AsCollection`; hoặc `update(['options->theme' => 'dark'])` (cần khai
  `options->theme` trong fillable).
- ⚠️ Tiền: cast `float`/`double` mang sai số nhị phân (`0.1 + 0.2 !== 0.3`). `decimal:2` trả chuỗi
  để giữ chính xác, tính toán bằng bcmath hoặc lưu số nguyên theo đơn vị nhỏ nhất (xem
  [22-practical-data.md](../22-practical-data.md)).
- ⚠️ `encrypted`: kết quả dài hơn và không đoán trước độ dài, cột phải là `TEXT`; không `WHERE` hay
  index được trên cột mã hoá; đổi `APP_KEY` mà không cấu hình key rotation là mất khả năng đọc.
- Attribute có giá trị `null` không được cast. Không đặt cast trùng tên một relationship, không cast
  primary key.
- Enum cast: gán giá trị không có trong enum thì ném `ValueError` lúc gán, lỗi sớm thay vì lưu rác.

*Accessor* (biến đổi khi đọc) và *mutator* (biến đổi khi ghi) viết bằng một method `protected` trả
`Attribute`, tên method camelCase ứng với attribute snake_case:

```php
use Illuminate\Database\Eloquent\Casts\Attribute;

protected function email(): Attribute
{
    return Attribute::make(
        get: fn (string $value): string => $value,
        set: fn (string $value): string => mb_strtolower(trim($value)),  // chuẩn hoá trước khi lưu
    );
}

// Accessor tính từ nhiều cột, trả value object
protected function address(): Attribute
{
    return Attribute::make(
        get: fn (mixed $value, array $attributes): Address =>
            new Address($attributes['line1'], $attributes['city']),
    );
}
```

- Accessor trả object được Eloquent giữ lại (cache) và trả cùng instance cho các lần đọc sau; sửa
  object rồi `save()` thì thay đổi được đồng bộ ngược về model (accessor cần có cả `set` để tách
  object ngược về các cột). Tắt bằng `->withoutObjectCaching()`;
  cache cả giá trị nguyên thuỷ tốn kém bằng `->shouldCache()`.
- Muốn accessor xuất hiện trong `toArray()`/JSON thì thêm vào `$appends` (hoặc `#[Appends]` ở 13.x).

⚠️ Accessor chạy query cộng với `$appends` là N+1 ẩn khó thấy nhất:

```php
protected $appends = ['display_city'];

protected function displayCity(): Attribute
{
    return Attribute::make(get: fn (): string => $this->city->name);  // lazy load city
}

return User::paginate(100);   // serialize 100 user = 100 query SELECT * FROM cities, không có vòng lặp nào trong code
```

Sửa: eager load (`User::with('city')`), hoặc bỏ khỏi `$appends` và chỉ `append()` ở endpoint cần.

#### Scope

*Local scope* đóng gói một điều kiện hay dùng thành method gọi được trên query:

```php
use Illuminate\Database\Eloquent\Attributes\Scope;

#[Scope]                                   // cú pháp mới; kiểu cũ: public function scopeActive($query)
protected function active(Builder $query): void
{
    $query->where('status', 'active');
}

#[Scope]
protected function ofType(Builder $query, string $type): void   // scope có tham số
{
    $query->where('type', $type);
}

User::active()->ofType('admin')->get();
```

⚠️ Ghép scope bằng `orWhere` phải nhóm lại: `User::popular()->orWhere(fn ($q) => $q->active())`
(hoặc dạng tắt `User::popular()->orWhere->active()`). Không nhóm thì thành `a OR b AND c`, sai logic.

*Global scope* tự thêm điều kiện vào **mọi** query Eloquent của model. `SoftDeletes` chính là một
global scope. Ví dụ thực tế là multi-tenant:

```php
<?php
declare(strict_types=1);

namespace App\Models\Scopes;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Scope;

final class TenantScope implements Scope
{
    public function apply(Builder $builder, Model $model): void
    {
        $builder->where($model->qualifyColumn('tenant_id'), app('tenant')->id);
    }
}

// Gắn: #[ScopedBy([TenantScope::class])] trên class model,
// hoặc static::addGlobalScope(new TenantScope) trong booted().
// Bỏ: Invoice::withoutGlobalScope(TenantScope::class)->get(); withoutGlobalScopes() bỏ hết.
```

⚠️ Global scope làm query "thiếu dữ liệu" mà người đọc code không thấy nguyên nhân:

- Báo cáo tổng doanh thu toàn hệ thống viết `Invoice::sum('total')` chạy trong command không có
  tenant, hoặc có tenant mặc định, thì ra số của một tenant.
- Scope thêm cột vào `SELECT` phải dùng `addSelect`, không phải `select`, nếu không nó thay mất
  select của query gốc.
- Scope chỉ áp cho Eloquent: `DB::table('invoices')`, raw SQL, `join('invoices', ...)` từ model khác
  không có điều kiện đó. Với dữ liệu phân tách tenant, lọt scope là lộ dữ liệu giữa khách hàng; nên
  có thêm lớp bảo vệ ở DB hoặc test tự động.
- Scope phụ thuộc trạng thái request (`auth()->user()`) chạy trong queue worker hay Octane có thể
  đọc nhầm người dùng hoặc null (module 3.5).

#### Model event và observer

Eloquent bắn event quanh vòng đời model: `retrieved`, `creating`/`created`, `updating`/`updated`,
`saving`/`saved`, `deleting`/`deleted`, `trashed`, `forceDeleting`/`forceDeleted`,
`restoring`/`restored`, `replicating`. Event đuôi `-ing` chạy **trước** khi ghi DB (listener trả
`false` là huỷ thao tác); đuôi `-ed` chạy sau khi ghi.

Thứ tự khi `$model->save()` trên model đã tồn tại (đọc từ `Model::save()` và `performUpdate()`
13.x):

```
save()
 ├─ saving          luôn bắn, kể cả khi không có gì thay đổi
 ├─ isDirty()? không → bỏ qua UPDATE, updating/updated KHÔNG bắn
 │   có ↓
 ├─ updating
 ├─ UPDATE ... SET <chỉ các cột dirty> WHERE id = ?
 ├─ updated
 └─ saved           (trong finishSave)
```

Với model mới: `saving` → `creating` → `INSERT` → `created` → `saved`.

*Observer* là class gom handler của nhiều event cho một model: gắn bằng `#[ObservedBy([UserObserver::class])]`
hoặc `User::observe(UserObserver::class)`. Cần kiểm tra trường nào đổi thì dùng `isDirty('status')`
(trong `-ing`) hoặc `wasChanged('status')` (trong `-ed`), `getOriginal('status')` cho giá trị cũ.

⚠️ Điểm hay bị hỏi nhất: các lệnh trên **query builder** không tạo object model (không *hydrate*,
tức là không dựng model từ dòng DB), nên **không** bắn event, **không** chạy observer, **không** áp
cast hay mutator (riêng timestamp: `update()` qua Eloquent builder vẫn tự thêm `updated_at`, `upsert`
tự set timestamps, còn `insert` thì không):

```php
$order = Order::findOrFail($id);
$order->update(['status' => 'paid']);                     // SELECT rồi UPDATE: saving, updating, updated, saved

Order::where('id', $id)->update(['status' => 'paid']);    // một câu UPDATE: KHÔNG event nào
Order::whereIn('id', $ids)->delete();                     // một câu DELETE: không deleting/deleted
Order::insert([...]);                                     // không creating/created, không timestamps
Order::upsert([...], ['id'], ['status']);                 // không event (upsert có tự set timestamps)
```

Docs ghi rõ lý do: model "không bao giờ thực sự được lấy ra" khi mass update/delete. Ngược lại,
`Order::destroy([1, 2, 3])` **có** bắn `deleting`/`deleted` vì nó nạp từng model rồi gọi `delete()`
(đổi lại là N+1 câu lệnh).

Chọn cách nào là đánh đổi: mass update nhanh (một câu SQL cho 10.000 dòng) nhưng mất event; nạp
từng model thì có event nhưng chậm. Nếu logic trong observer là bắt buộc (ghi audit log, xoá cache,
gửi email), việc hàng loạt phải tự làm phần đó, ví dụ dispatch một job sau khi update.

Tắt event có chủ đích:

- `$model->saveQuietly()`, `deleteQuietly()`, `forceDeleteQuietly()`, `restoreQuietly()`.
- `Model::withoutEvents(fn () => ...)`: mọi thứ trong closure không bắn model event.

Observer và transaction: handler trong observer chạy ngay khi event bắn, tức là **trước** khi
transaction ngoài commit. Observer gửi email trong `created` mà transaction sau đó rollback là email
cho một bản ghi không tồn tại. `implements ShouldHandleEventsAfterCommit` trên observer làm handler
chờ commit (không có transaction thì chạy ngay).

⚠️ Chi phí kiến trúc của observer: logic nghiệp vụ nằm ở nơi đọc controller không thấy. Seeder,
import CSV, `factory()->create()` trong test đều kích hoạt observer, gây gửi email thật hoặc gọi API
thật. Quy tắc thực dụng: observer cho việc kỹ thuật gắn với dữ liệu (xoá cache, cập nhật search
index, audit); luồng nghiệp vụ quan trọng (thanh toán xong thì gửi hoá đơn) viết tường minh trong
service hoặc action.

#### Soft delete

`use SoftDeletes` trên model: `delete()` chỉ ghi `deleted_at = now()` và bắn thêm event `trashed`.
Trait đăng ký global scope `SoftDeletingScope` tự thêm `WHERE deleted_at IS NULL`.

```php
Post::withTrashed()->find($id);     // gồm cả bản ghi đã xoá mềm
Post::onlyTrashed()->get();         // chỉ bản đã xoá
$post->restore();                   // deleted_at = NULL, bắn restoring/restored
$post->forceDelete();               // DELETE thật
$post->trashed();                   // bool
```

⚠️ Cạm bẫy (chi tiết ở module 2.8 file 03):

- Unique index `(email)` chặn đăng ký lại email của user đã xoá mềm; `(email, deleted_at)` thì vô
  dụng vì các NULL khác nhau. Sửa bằng generated column (MySQL) hoặc partial index (Postgres).
- Scope chỉ bảo vệ query Eloquent của model đó. `DB::table`, raw SQL, `join` sang bảng soft delete,
  công cụ BI đọc thẳng DB đều thấy dòng đã xoá.
- Quan hệ: `$post->comments` không tự ẩn comment khi post bị xoá mềm; xoá mềm cha không xoá mềm
  con. Cascade phải tự làm (trong event `deleting` hoặc package).
- Mass delete `Post::where(...)->delete()` trên model có `SoftDeletes` vẫn là soft delete (Builder
  của trait đổi thành UPDATE `deleted_at`), nhưng không bắn event.
- Trait `Prunable` (method `prunable()` trả query cần xoá) cộng lệnh `model:prune` chạy theo lịch để
  xoá hẳn bản ghi cũ. Xoá mềm không phải xoá dữ liệu cá nhân theo yêu cầu pháp lý.

#### Query builder, Eloquent, và kiến trúc

| Tiêu chí | Query builder (`DB::table`) | Eloquent |
|---|---|---|
| Kết quả | `stdClass` / mảng | Object model |
| Event, observer | Không | Có (trừ mass operation) |
| Cast, accessor, mutator | Không | Có |
| Global scope (soft delete, tenant) | Không | Có |
| Chi phí mỗi dòng | Thấp | Cao hơn: hydrate model, cast, giữ `original` để so dirty |
| Hợp với | Báo cáo, thao tác hàng loạt, ETL | Nghiệp vụ theo từng bản ghi |

Cả hai sinh prepared statement nên an toàn với giá trị. Chỗ hở là các method nhận **SQL thô**:

```php
// SAI: injection
User::whereRaw("name = '$name'")->get();
User::orderBy($request->input('sort'))->get();          // tên cột không bind được bằng ?

// ĐÚNG
User::whereRaw('name = ?', [$name])->get();
$sort = in_array($request->input('sort'), ['name', 'created_at'], true)
    ? $request->input('sort')
    : 'created_at';
User::orderBy($sort)->get();                             // whitelist tên cột
```

*Active Record* (Fowler): object vừa mang dữ liệu một dòng vừa biết tự lưu mình (`$user->save()`).
Eloquent, Rails ActiveRecord thuộc nhóm này. *Data Mapper*: entity là object PHP thuần, không biết
DB; một lớp riêng (Doctrine `EntityManager`) ánh xạ entity xuống bảng. Hibernate/JPA của Java cũng
là Data Mapper.

| | Active Record (Eloquent) | Data Mapper (Doctrine) |
|---|---|---|
| Model phụ thuộc DB | Có, kế thừa `Model` | Không |
| Lưu | `$user->save()` ngay lập tức | `persist()` rồi `flush()` gom thay đổi (*unit of work*) |
| Test logic domain | Khó tách DB | Test entity như object thường |
| Tốc độ viết CRUD | Rất nhanh | Nhiều code hơn |
| Hợp với | CRUD, domain vừa phải | Domain phức tạp, nhiều bất biến |

Khi domain phức tạp lên, cách thường gặp trong Laravel là giữ Eloquent nhưng đặt logic vào
service/action và không để controller gọi `Model::where` rải rác. So sánh sâu hơn ở module 3.8.

**Tóm tắt nhanh**
- Query builder và mass update/delete/insert/upsert không hydrate model: không event, không
  observer, không cast. `destroy()` thì có event vì nạp từng model.
- `save()` luôn bắn `saving`/`saved`; `updating`/`updated` chỉ khi có cột dirty.
- `shouldBeStrict()` = chặn lazy load (chỉ model từ kết quả nhiều dòng) + chặn vứt field ngoài
  fillable + chặn đọc cột không select. Bật ngoài production.
- Morph map bằng `enforceMorphMap` để cột type không phụ thuộc tên class; polymorphic không có FK.
- Global scope làm query thiếu dữ liệu ngầm và chỉ áp cho Eloquent; accessor + `$appends` gọi quan
  hệ là N+1 ẩn khi serialize.

**Nguồn**: [Laravel: Eloquent](https://laravel.com/docs/13.x/eloquent) (Strictness, Mass Updates,
Deleting, Soft Deleting, Query Scopes, Events, Observers) ·
[Laravel: Eloquent Relationships](https://laravel.com/docs/13.x/eloquent-relationships) (Has Many
Through, Many to Many, Polymorphic, Custom Polymorphic Types, Automatic Eager Loading) ·
[Laravel: Mutators & Casting](https://laravel.com/docs/13.x/eloquent-mutators) ·
[Laravel: Serialization](https://laravel.com/docs/13.x/eloquent-serialization) ·
mã nguồn `laravel/framework` 13.x (`Eloquent/Model.php`, `Eloquent/Builder.php`,
`Concerns/HasAttributes.php`, `Concerns/GuardsAttributes.php`,
`Relations/Concerns/InteractsWithPivotTable.php`) ·
Martin Fowler: [Active Record](https://martinfowler.com/eaaCatalog/activeRecord.html),
[Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html)


---

### 2.6 Queue

Module này trả lời: một job đi từ `dispatch()` tới lúc chạy xong qua những bước nào, "một attempt"
thực sự là gì, vì sao cùng một job có thể chạy hai lần (hoặc vừa chạy xong vừa nằm trong
`failed_jobs`), và các công cụ Laravel đưa ra để điều khiển: tries, backoff, timeout, unique,
overlap, chain, batch, Horizon.

```
Web request                    Queue backend (Redis)                      Worker (queue:work)
-----------                    ---------------------                      -------------------
dispatch($job)                                                            vòng lặp daemon:
  serialize job  ------------> queues:default        (LIST: đang chờ)      1. pop(): chuyển job hết hạn
  (model -> class + id)        queues:default:delayed (ZSET: release/delay)     từ :delayed, :reserved về
                               queues:default:reserved(ZSET: đang chạy,         hàng chờ, rồi lấy 1 job
                                  score = lúc hết hạn = now + retry_after)  2. attempts++, đưa vào :reserved
                                                                            3. hẹn SIGALRM sau `timeout` giây
                                                                            4. chạy middleware -> handle()
                                                                            5. OK: xoá khỏi :reserved
                                                                               lỗi: release (backoff) hoặc fail
                                                                            6. kiểm restart/memory/max-jobs
```

#### Driver và worker

*Queue* là hàng đợi việc: code web đẩy *job* (một đơn vị việc đã serialize) vào, *worker* (process
chạy nền) lấy ra xử lý. Hai khái niệm dễ lẫn trong `config/queue.php`:

- *Connection*: backend lưu hàng đợi (`database`, `redis`, `sqs`, `beanstalkd`, `sync`, `null`).
  App mới mặc định dùng `database` (`QUEUE_CONNECTION=database`).
- *Queue*: tên một hàng đợi trong connection đó (`default`, `emails`, `high`...). Một connection
  có nhiều queue.

| Driver | Cơ chế lấy job | Ghi chú |
|---|---|---|
| `sync` | Chạy ngay trong request | Chỉ dev/test; job lỗi không vào `failed_jobs` |
| `database` | `SELECT ... FOR UPDATE SKIP LOCKED` (MySQL 8+, Postgres) trên bảng `jobs`, đặt `reserved_at` | Không cần thêm hạ tầng; tải cao thì bảng `jobs` thành điểm nóng |
| `redis` | Lua script: pop từ LIST, đưa vào ZSET `:reserved` | Nhanh, cần cho Horizon. Redis Cluster: tên queue phải có hash tag `{default}` |
| `sqs` | Visibility timeout của SQS | Không dùng `retry_after`; giao *at-least-once* |
| `deferred`, `background` | Chạy sau khi đã trả response (cùng process / process PHP riêng) | Có trong docs 13.x; không cần worker |

Laravel 13 còn có driver `failover`: đẩy vào connection đầu danh sách, lỗi thì thử connection tiếp
theo (ví dụ `redis` rồi `database`), bắn event `QueueFailedOver`. Mỗi connection trong danh sách
vẫn cần worker riêng.

`queue:work` boot framework **một lần** rồi xử lý job liên tục; nhanh nhưng giữ nguyên code và
state trong RAM, nên phải restart khi deploy và phải cẩn thận với static state (module 3.5).
`queue:listen` boot lại cho mỗi job, chậm hơn nhiều, chỉ để dev.

Giá trị mặc định (đọc từ `WorkerOptions` 13.x và docs):

| Tuỳ chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--tries` | 1 | Số attempt tối đa; `0` là vô hạn |
| `--timeout` | 60 | Giây tối đa cho một job trước khi worker tự kill |
| `--backoff` | 0 | Giây chờ trước khi thử lại sau exception |
| `--sleep` | 3 | Giây nghỉ khi hàng đợi trống |
| `--memory` | 128 | MB; vượt thì worker thoát sau job hiện tại |
| `--max-jobs`, `--max-time` | 0 (tắt) | Thoát sau N job / N giây để process manager khởi động lại |
| `--queue=high,default,low` | queue mặc định của connection | Ưu tiên tuyệt đối: chỉ lấy `default` khi `high` trống |

⚠️ Ưu tiên kiểu `--queue=high,low` là *strict priority*: `high` luôn có job thì `low` đói mãi.
Nếu cần đảm bảo `low` vẫn chạy, cấp worker riêng cho nó.

Định tuyến job vào queue không cần sửa từng chỗ dispatch (Laravel 13): `Queue::route(ProcessPodcast::class, connection: 'redis', queue: 'podcasts')`,
nhận cả interface/trait/class cha. Job tự khai `onQueue()` thì ghi đè route.

#### Cấu hình trên job

Hai khái niệm nền trước khi đọc cấu hình:

- *Attempt* là một lần worker lấy job ra khỏi hàng đợi. Theo docs, attempt bị "tiêu" khi: job ném
  exception, job bị `release()` (tự gọi hoặc do middleware như `RateLimited`, `WithoutOverlapping`),
  job timeout, hoặc job chạy xong. Attempt **không** đồng nghĩa với "`handle()` đã chạy".
- Số attempt được tăng **lúc lấy job ra** (Redis tăng trong Lua script khi reserve), không phải lúc
  job lỗi. Worker chết giữa chừng thì lần lấy sau đã là attempt 2.

```php
<?php
declare(strict_types=1);

namespace App\Jobs;

use App\Models\Order;
use DateTimeInterface;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\Attributes\Backoff;
use Illuminate\Queue\Attributes\MaxExceptions;
use Illuminate\Queue\Attributes\Timeout;
use Illuminate\Queue\Attributes\Tries;
use Throwable;

#[Tries(10)]                 // tối đa 10 attempt (tính cả release do rate limit)
#[MaxExceptions(3)]          // nhưng chỉ chịu 3 lần exception thật
#[Backoff([10, 60, 300])]    // chờ 10s, 60s, rồi 300s cho các lần sau
#[Timeout(120)]              // job chạy quá 120s thì worker tự kill
final class SyncOrderToErp implements ShouldQueue
{
    use Queueable;           // gồm Dispatchable, InteractsWithQueue, Queueable (bus), SerializesModels

    public function __construct(public Order $order) {}

    public function handle(ErpClient $erp): void
    {
        $erp->push($this->order);
    }

    // Có retryUntil thì Laravel dùng nó thay cho Tries
    // public function retryUntil(): DateTimeInterface { return now()->addMinutes(30); }

    public function failed(?Throwable $e): void
    {
        // Chạy trên một INSTANCE MỚI: property đổi trong handle() đã mất
        // $e có thể là MaxAttemptsExceededException hoặc TimeoutExceededException
    }
}
```

- Cú pháp attribute (`#[Tries]`, `#[Backoff]`, `#[Timeout]`, `#[MaxExceptions]`, `#[FailOnTimeout]`,
  `#[UniqueFor]`, `#[DeleteWhenMissingModels]`...) là cách docs 13.x viết. Property kiểu cũ
  (`public $tries = 10;`) vẫn được đọc; method `tries()`, `backoff()` dùng khi cần tính động.
- Giá trị trên job thắng giá trị `--tries`/`--timeout` của worker.
- `Tries` so với `MaxExceptions`: `Tries` đếm mọi attempt; `MaxExceptions` chỉ đếm lần job ném
  exception (Laravel đếm trong cache với key `job-exceptions:<uuid>`). Cặp `Tries(25)` +
  `MaxExceptions(3)` nghĩa là "được release chờ rate limit nhiều lần, nhưng lỗi thật 3 lần là fail".
- `Backoff` chỉ áp khi job ném exception; `release(N)` tự chọn độ trễ. Mảng backoff hết phần tử
  thì dùng mãi phần tử cuối.
- `FailOnTimeout`: mặc định job timeout thì tốn một attempt và được thử lại; có attribute này thì
  fail luôn, không thử lại.
- Dừng thử lại theo loại exception: `$exceptions->dontRetry([...])` trong `bootstrap/app.php`, hoặc
  middleware `FailOnException([...])`, hoặc `$this->fail($e)` trong `handle()`.

*Timeout hoạt động thế nào* (đọc từ `Worker::registerTimeoutHandler` 13.x): trước khi chạy job,
worker đăng ký handler cho tín hiệu `SIGALRM` rồi gọi `pcntl_alarm($timeout)`. Hết giờ, handler:
đánh dấu job failed nếu đã hết attempt (hoặc có `FailOnTimeout`), bắn event `JobTimedOut`, rồi **kill
chính process worker** (`posix_kill(getmypid(), SIGKILL)`). Hệ quả:

- ⚠️ Cần extension `pcntl`; không có thì `timeout` không có tác dụng. Windows không có `pcntl`.
- Worker chết cả process, không phải "huỷ job". Process manager phải khởi động lại nó.
- Job bị kill **không** được đưa lại hàng đợi ngay; nó nằm trong `:reserved` cho tới khi hết
  `retry_after`, lúc đó mới hiện lại.
- `finally` trong job **không chạy** khi bị SIGKILL, nên lock tự tay lấy trong job không được nhả
  (lý do `WithoutOverlapping` cần `expireAfter`, xem bên dưới).
- I/O chặn (socket, HTTP) có thể không bị ngắt đúng hạn; luôn đặt timeout riêng cho HTTP client
  (`Http::timeout(10)->connectTimeout(3)`).

#### retry_after và timeout

Hai con số khác nhau, đặt ở hai nơi, do hai bên khác nhau thực thi:

| | `retry_after` | `timeout` |
|---|---|---|
| Đặt ở | `config/queue.php`, từng connection (mặc định 90 trong skeleton) | `--timeout` của worker (mặc định 60) hoặc `#[Timeout]` trên job |
| Ai thực thi | **Hàng đợi**: job reserved quá N giây thì cho hiện lại | **Worker**: job chạy quá N giây thì tự kill |
| Mục đích | Cứu job của worker đã chết (OOM, server sập) | Không để job treo giữ worker mãi |
| SQS | Không dùng; SQS có visibility timeout riêng | Vẫn áp |

Hàng đợi không biết worker còn sống hay không. Nó chỉ biết "job này được lấy ra lúc T, quá
`T + retry_after` chưa bị xoá thì coi như worker đã chết". Nên nếu job chạy lâu hơn `retry_after`,
hàng đợi sẽ "cứu" một job đang chạy bình thường.

⚠️ Tình huống: `retry_after = 90`, job gửi email xác nhận rồi gọi API mất tổng 120 giây,
`#[Timeout(150)]`, `#[Tries(3)]`, hai worker A và B.

| Giây | Worker A | Worker B | Trạng thái Redis |
|---|---|---|---|
| 0 | `pop()`: lấy job, attempts = 1, bắt đầu `handle()` | Rảnh, đang chờ | Job trong `:reserved`, hết hạn ở giây 90 |
| 5 | Gửi email lần 1 | | |
| 90 | Vẫn đang gọi API | `pop()` gọi `migrate()`: job trong `:reserved` đã quá hạn, bị chuyển về hàng chờ | Job lại nằm trong hàng chờ |
| 90 | | Lấy job, attempts = 2 (≤ 3 nên chạy), bắt đầu `handle()` | Job trong `:reserved`, hết hạn ở giây 180 |
| 95 | | Gửi email **lần 2** | |
| 120 | Xong, xoá bản reserved của mình (đã không còn), A rảnh | Vẫn chạy | Không đổi |
| 180 | `pop()`: bản của B đã quá hạn, A lấy job, attempts = 3 (≤ 3 nên chạy) | Vẫn chạy | Job trong `:reserved`, hết hạn ở giây 270 |
| 185 | Gửi email **lần 3** | | |
| 210 | Vẫn chạy | Xong, xoá bản reserved của mình (đã không còn) | Không đổi |
| 270 | Vẫn chạy | `pop()`: lấy job với attempts = 4 > 3, đánh dấu failed, ghi `failed_jobs` | Job bị xoá khỏi hàng đợi |
| 300 | Xong | | |

Kết quả: các worker chạy **chồng lên nhau** cùng một job, email gửi ba lần, API bị gọi ba lần, và
cuối cùng job còn bị ghi vào `failed_jobs` dù mọi lần chạy đều thành công. Không có exception nào
trong `handle()`, log trông bình thường.

Biến thể khó chẩn đoán hơn, với mặc định `Tries = 1`: ở giây 90, B lấy job ra với attempts = 2 > 1.
Trước khi chạy, `Worker::process()` gọi `markJobAsFailedIfAlreadyExceedsMaxAttempts`: B **đánh dấu
job failed**, ghi vào `failed_jobs`, gọi `failed()` với `MaxAttemptsExceededException` ("has been
attempted too many times"), trong khi A vẫn đang chạy và sẽ thành công. Nếu `failed()` làm việc bù
trừ (hoàn tiền, huỷ đơn) thì hậu quả còn nặng hơn chạy trùng.

Cấu hình đúng: `timeout` < `retry_after`, cách nhau vài giây (docs: "at least several seconds
shorter"). Ví dụ job dài nhất 120 giây: `#[Timeout(150)]` và `retry_after = 180`. Diễn biến khi job
treo:

1. Giây 0: A lấy job, attempts = 1, hẹn `SIGALRM` sau 150 giây.
2. Giây 150: alarm, A kiểm tra attempts (hết lượt thì đánh dấu job failed), rồi tự kill; supervisor
   khởi động lại A.
3. Giây 180: `retry_after` hết, job hiện lại hàng chờ, một worker lấy với attempts = 2.

Không lúc nào có hai worker cùng chạy job. Gom nhóm các quy tắc thời gian:

```
timeout của job dài nhất  <  retry_after  (vài giây trở lên)
timeout của job dài nhất  <  stopwaitsecs của supervisor   (không bị kill khi deploy)
timeout của job dài nhất  <  timeout của supervisor trong Horizon
SQS: timeout  <  visibility timeout của queue
```

⚠️ Job dài bất thường (import file lớn) nên tách sang connection riêng có `retry_after` lớn, thay
vì tăng `retry_after` cho mọi job: `retry_after` lớn nghĩa là job của worker chết thật phải chờ lâu
mới được cứu.

#### Idempotent và job thất bại

*Idempotent*: chạy một lần hay nhiều lần cho cùng một kết quả. Job **phải** idempotent vì có nhiều
đường làm nó chạy lại mà không cấu hình nào chặn được hết:

1. Retry sau exception, kể cả khi exception xảy ra **sau** bước có side effect (đã trừ tiền rồi mới
   lỗi lúc ghi log).
2. `retry_after` ngắn hơn thời gian chạy (bảng trên).
3. Worker bị kill sau khi làm xong việc nhưng trước khi kịp xoá job khỏi hàng đợi.
4. SQS và nhiều broker giao *at-least-once* (ít nhất một lần, có thể nhiều hơn).
5. Người vận hành chạy `queue:retry all` sau sự cố.

Các kỹ thuật (lý thuyết delivery semantics ở [12-messaging.md](../12-messaging.md)):

```php
public function handle(PaymentGateway $gateway): void
{
    // 1. Kiểm trạng thái trước khi làm
    if ($this->order->fresh()->status === OrderStatus::Paid) {
        return;
    }

    // 2. Idempotency key gửi sang đối tác: cổng thanh toán nhận cùng key hai lần thì trả kết quả cũ
    $charge = $gateway->charge($this->order->total, idempotencyKey: 'order-charge-'.$this->order->id);

    // 3. Ràng buộc ở DB: UPDATE có điều kiện, chỉ một lần thành công
    Order::whereKey($this->order->id)
        ->where('status', OrderStatus::Pending)
        ->update(['status' => OrderStatus::Paid, 'charge_id' => $charge->id]);
}
```

- Unique index cũng là idempotency: bảng `sent_emails (order_id, type)` UNIQUE, INSERT trước khi gửi,
  trùng thì bỏ qua.
- ⚠️ `ShouldBeUnique` và `WithoutOverlapping` **không** thay được idempotent. Unique chỉ chặn lúc
  dispatch. `WithoutOverlapping` chặn chạy song song, nhưng trong kịch bản `retry_after` ở trên,
  B không lấy được lock sẽ `release()` job lại hàng đợi; A xong không xoá được bản B đã release, nên
  job vẫn chạy thêm lần nữa sau đó.

*Job thất bại*: hết attempt (hoặc `fail()`, `FailOnTimeout`, `dontRetry`) thì job được ghi vào bảng
`failed_jobs` (chỉ job chạy bất đồng bộ; job `sync` ném exception thẳng ra) và method `failed()` được
gọi.

| Lệnh | Việc |
|---|---|
| `queue:failed` | Liệt kê job lỗi (id, connection, queue, thời điểm) |
| `queue:retry <uuid>` / `--queue=name` / `all` | Đẩy lại vào hàng đợi, attempts reset |
| `queue:forget <uuid>` | Xoá một job lỗi (Horizon: `horizon:forget`) |
| `queue:flush [--hours=48]` | Xoá job lỗi |
| `queue:prune-failed [--hours=48]` | Xoá bản ghi cũ hơn N giờ (mặc định 24), nên chạy theo lịch |

Lỗi biết chắc là vĩnh viễn (dữ liệu sai, user bị xoá quyền) thì fail ngay bằng `$this->fail($e)`
hoặc `FailOnException`, không phí lượt thử và không làm chậm hàng đợi.

#### Điều phối job: chain, batch, unique job, job middleware

*Chain*: chạy tuần tự, job sau chỉ bắt đầu khi job trước thành công.

```php
Bus::chain([
    new ProcessPodcast($podcast),
    new OptimizePodcast($podcast),
    new ReleasePodcast($podcast),
])->onQueue('podcasts')
  ->catch(function (Throwable $e): void {
      // một job trong chuỗi đã fail (sau khi hết attempt), các job sau không chạy
  })
  ->dispatch();
```

- Chuỗi được lưu **bên trong payload** của job đầu; job xong thì dispatch job kế tiếp. Trong job có
  thể `prependToChain()`/`appendToChain()`.
- ⚠️ `$this->delete()` trong job không dừng chuỗi; chỉ job **fail** mới dừng.
- ⚠️ Callback của chain và batch bị serialize để chạy sau trong worker; không dùng `$this` trong đó.

*Batch*: chạy song song một nhóm job, theo dõi tiến độ, có callback khi xong. Cần bảng
`job_batches` (`make:queue-batches-table`), job dùng trait `Batchable`.

```php
$batch = Bus::batch([
    new ImportCsv($file, 1, 1000),
    new ImportCsv($file, 1001, 2000),
])->then(fn (Batch $b) => /* mọi job thành công */ null)
  ->catch(fn (Batch $b, Throwable $e) => /* job fail ĐẦU TIÊN, chỉ gọi một lần */ null)
  ->finally(fn (Batch $b) => /* batch kết thúc, dù thế nào */ null)
  ->name('Import CSV')
  ->dispatch();

// Trong ImportCsv::handle()
if ($this->batch()->cancelled()) {
    return;                     // hoặc gắn middleware SkipIfBatchCancelled
}
```

- Mặc định một job fail thì batch bị đánh dấu **cancelled**, các job còn lại vẫn được lấy ra nhưng
  nên tự kiểm `cancelled()` để bỏ qua. `allowFailures()` để batch tiếp tục; `then` chỉ chạy khi không
  có job nào fail.
- `$batch->totalJobs`, `pendingJobs`, `failedJobs`, `progress()`; `Bus::findBatch($id)` trả JSON
  được cho UI thanh tiến độ. `queue:retry-batch <id>` thử lại các job lỗi của batch.
- Batch trong chain và chain trong batch lồng nhau được (`Bus::chain([new A, Bus::batch([...])])`).
- ⚠️ Mọi job trong batch phải cùng connection và queue. Bảng `job_batches` phình nhanh: lên lịch
  `queue:prune-batches` (mặc định xoá batch đã xong quá 24 giờ; thêm `--unfinished`, `--cancelled`).
- ⚠️ Ràng buộc unique không áp cho job trong batch.

*Unique job*: `implements ShouldBeUnique` đảm bảo tại một thời điểm chỉ có một job cùng khoá đang
chờ hoặc đang chạy.

```php
#[UniqueFor(3600)]                    // lock tự hết hạn sau 1 giờ nếu job chưa xong
final class UpdateSearchIndex implements ShouldQueue, ShouldBeUnique
{
    use Queueable;

    public function __construct(public Product $product) {}

    public function uniqueId(): string
    {
        return (string) $this->product->id;
    }
}
```

Bên dưới (đọc từ `Bus/UniqueLock.php` 13.x):

1. Lúc dispatch, Laravel lấy cache lock với key `laravel_unique_job:<class>:<uniqueId>`, thời hạn
   `uniqueFor` giây.
2. Lấy không được (đã có job cùng khoá) thì **lặng lẽ không dispatch**, không exception.
3. Lock được nhả khi job chạy xong hoặc fail hẳn. `ShouldBeUniqueUntilProcessing` nhả ngay khi job
   bắt đầu chạy, nên trong lúc job đang chạy đã dispatch được bản mới.

- ⚠️ Không đặt `uniqueFor` thì lock không có hạn (thời hạn 0). Job bị mất (xoá tay khỏi Redis,
  lỗi lúc serialize) thì lock treo và job cùng khoá không bao giờ dispatch được nữa.
- ⚠️ Cần cache hỗ trợ atomic lock (`redis`, `memcached`, `database`, `dynamodb`; `file`/`array`
  chỉ trong một máy) và **dùng chung giữa mọi server** dispatch job. Đổi store bằng method
  `uniqueVia()`.
- Docs 13.x có *debounced job* (`#[DebounceFor(30)]` + `debounceId()`): dispatch nhiều lần trong
  30 giây thì chỉ bản **mới nhất** chạy, bản cũ bị gỡ khỏi hàng đợi. Unique giữ bản đầu, debounce giữ
  bản cuối; hai cơ chế loại trừ nhau.

*Job middleware*: bọc quanh `handle()` giống middleware HTTP, khai trong method `middleware()` của
job.

| Middleware | Làm gì | Lưu ý |
|---|---|---|
| `RateLimited('name')` | Theo `RateLimiter::for('name', ...)`; vượt hạn mức thì `release()` với độ trễ phù hợp | `dontRelease()` để bỏ job thay vì thử lại; bản Redis: `RateLimitedWithRedis` |
| `WithoutOverlapping($key)` | Cache lock theo key; không lấy được lock thì `release()` | `releaseAfter(60)`, `expireAfter(180)`, `dontRelease()`, `shared()` để dùng chung khoá giữa nhiều class |
| `ThrottlesExceptions(10, 300)` | 10 exception liên tiếp thì hoãn 5 phút | Nên đi với `retryUntil()`; `by('key')` chung bucket giữa các job gọi cùng dịch vụ |
| `Skip::when(...)` / `Release::when(...)` | Bỏ hẳn / đẩy lại theo điều kiện | |
| `FailOnException([...])` | Gặp exception này thì fail ngay | |
| `SkipIfBatchCancelled` | Bỏ qua nếu batch đã huỷ | |

⚠️ Hai bẫy hay gặp với middleware:

1. **Release vẫn tiêu attempt.** Với mặc định `Tries = 1`, job bị `RateLimited` hay
   `WithoutOverlapping` release một lần là lần lấy sau đã vượt số attempt, và job **fail dù chưa
   từng chạy `handle()`**. Docs nêu rõ ví dụ này. Dùng `retryUntil()` (giới hạn theo thời gian)
   cộng `MaxExceptions` thay cho `Tries` nhỏ.
2. **`WithoutOverlapping` không có `expireAfter` thì lock không hết hạn.** Mã nguồn 13.x: thời hạn
   mặc định là 0 và lock được nhả trong khối `finally`. Worker bị kill vì timeout (SIGKILL) thì
   `finally` không chạy, lock treo vĩnh viễn, mọi job cùng key bị release mãi rồi fail. Luôn đặt
   `expireAfter` lớn hơn `timeout` của job một chút.

Phân biệt ba công cụ trông giống nhau:

| | Chặn ở thời điểm | Job trùng bị | Câu hỏi nó trả lời |
|---|---|---|---|
| `ShouldBeUnique` | Dispatch | Không được đẩy vào hàng đợi | "Đã có việc này trong hàng đợi chưa?" |
| `WithoutOverlapping` | Chạy | Release lại (tốn attempt) hoặc xoá | "Có ai đang làm việc này không?" |
| `RateLimited` | Chạy | Release lại với độ trễ | "Đã làm quá nhiều trong khoảng thời gian này chưa?" |

#### Model trong job và transaction

`SerializesModels` (có sẵn trong trait `Queueable`) khi dispatch chỉ lưu model dưới dạng class,
id, connection và tên các quan hệ đã nạp. Lúc worker chạy, model được **query lại** từ DB. Hệ quả:

- Model đã bị xoá thì job ném `ModelNotFoundException` trước cả khi vào `handle()`. Muốn bỏ job
  lặng lẽ: `#[DeleteWhenMissingModels]` (hoặc `public $deleteWhenMissingModels = true;`).
- Job thấy dữ liệu **lúc chạy**, không phải lúc dispatch. Cần giá trị tại thời điểm dispatch (giá
  lúc đặt hàng) thì truyền giá trị nguyên thuỷ vào constructor.
- Quan hệ đã nạp được nạp lại **toàn bộ**, điều kiện ràng buộc lúc eager load bị mất; payload cũng
  phình to. Dùng `$model->withoutRelations()`, hoặc attribute `#[WithoutRelations]` trên tham số
  constructor hay trên cả class.
- Collection model: quan hệ của từng phần tử **không** được nạp lại (tránh tốn tài nguyên), nên
  truy cập quan hệ trong job lại thành N+1.
- Dữ liệu nhị phân (nội dung ảnh) phải `base64_encode` trước khi đưa vào job, vì payload là JSON.

⚠️ Dispatch trong transaction: job có thể được worker lấy ra **trước khi** transaction commit,
query lại model thì không thấy (hoặc thấy dữ liệu cũ), hoặc transaction rollback nhưng job vẫn
chạy. Sửa bằng `->afterCommit()` hoặc `'after_commit' => true` cho connection; timeline chi tiết,
các biến thể cho event/listener/mail và giới hạn (cần outbox để đảm bảo tuyệt đối) ở
[03-database-sql.md, module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel). Tương tự với read
replica: job đọc từ replica chưa kịp nhận dữ liệu vừa ghi.

⚠️ Docs ghi rằng job trong batch được bọc trong database transaction, nên không chạy câu lệnh gây
implicit commit (DDL như `ALTER TABLE`) trong job của batch.

#### Horizon, restart và supervisor

*Horizon* là dashboard và bộ quản lý worker cho queue **Redis** (chỉ Redis). Thay vì tự chạy nhiều
`queue:work`, bạn chạy một process `php artisan horizon`; nó sinh và quản lý các worker theo
`config/horizon.php`.

```php
// config/horizon.php
'environments' => [
    'production' => [
        'supervisor-default' => [
            'connection'          => 'redis',
            'queue'               => ['default', 'notifications'],
            'balance'             => 'auto',
            'autoScalingStrategy' => 'time',   // time | size | log
            'minProcesses'        => 1,        // tối thiểu mỗi queue
            'maxProcesses'        => 10,       // tổng tối đa
            'balanceMaxShift'     => 1,        // mỗi lần tăng/giảm tối đa 1 process
            'balanceCooldown'     => 3,        // mỗi 3 giây
            'tries'               => 3,
            'timeout'             => 150,      // < retry_after của connection redis
        ],
        'supervisor-images' => [               // queue nặng: tách supervisor, giới hạn process
            'connection' => 'redis', 'queue' => ['images'],
            'balance' => 'simple', 'processes' => 2,
        ],
    ],
],
```

- *Supervisor* trong Horizon là một nhóm worker cùng cấu hình, không phải chương trình Supervisor
  của Linux.
- Ba chiến lược cân bằng:

| `balance` | Số process | Thứ tự queue |
|---|---|---|
| `auto` (mặc định) | Co giãn giữa `minProcesses` và `maxProcesses` theo tải từng queue | **Không** ưu tiên theo thứ tự khai báo |
| `simple` | Cố định `processes`, chia đều cho các queue | |
| `false` | Vẫn co giãn tổng số | Ưu tiên nghiêm ngặt theo thứ tự, như `--queue=a,b` |

- ⚠️ Với `auto`, liệt kê `['high', 'default']` **không** làm `high` được ưu tiên. Cần ưu tiên thì
  tách supervisor riêng hoặc dùng `balance => false`.
- ⚠️ Khi `auto` thu nhỏ số process, Horizon coi worker đang chạy quá `timeout` của supervisor là
  treo và force kill; `timeout` supervisor phải lớn hơn timeout của mọi job, và vẫn nhỏ hơn
  `retry_after`.
- Tag: Horizon tự gắn tag theo model trong job (`App\Models\Video:1`), lọc được job theo đơn hàng
  hay user. Metrics cần lên lịch `horizon:snapshot` mỗi 5 phút; `waits` cấu hình ngưỡng "chờ lâu"
  (mặc định 60 giây) để gửi cảnh báo.
- Deploy: `php artisan horizon:terminate`, Horizon làm xong job đang chạy rồi thoát, process manager
  khởi động lại với code mới. Nếu `failover` có `database`, vẫn cần `queue:work database` riêng.

*Restart khi deploy*: worker giữ code cũ trong RAM, deploy xong mà không restart là worker chạy code
cũ với schema mới. `queue:restart` **không** kill worker:

1. Lệnh ghi timestamp hiện tại vào cache, key `illuminate:queue:restart`.
2. Worker đọc key này lúc khởi động, và sau **mỗi** vòng lặp (`stopIfNecessary`) so lại.
3. Thấy khác thì worker thoát êm sau job hiện tại với exit code 0.
4. Process manager thấy process thoát và khởi động lại, lần này nạp code mới.

⚠️ Hệ quả: cache phải **dùng chung** giữa các server (Redis), không phải `file` (mỗi máy một bản);
phải có process manager, nếu không `queue:restart` chỉ làm worker tắt hẳn. Worker nhận `SIGTERM`
(`SIGQUIT`, `SIGINT`) cũng làm xong job hiện tại rồi thoát; job muốn phản ứng sớm (lưu tiến độ
import) thì `implements Interruptible` và viết `interrupted(int $signal)`. Với Redis, đặt
`block_for = 0` làm worker chặn vô hạn chờ job và không xử lý được `SIGTERM` cho tới job kế tiếp.

`queue:pause connection:queue` / `queue:continue` tạm ngừng lấy job mới mà không dừng worker (docs
13.x), dùng khi bảo trì hệ thống phía sau.

*Supervisor* (chương trình quản lý process trên Linux) giữ worker luôn chạy:

```ini
; /etc/supervisor/conf.d/laravel-worker.conf
[program:laravel-worker]
process_name=%(program_name)s_%(process_num)02d
command=php /var/www/app/artisan queue:work redis --sleep=3 --tries=3 --max-time=3600
autostart=true
autorestart=true          ; worker thoát (restart, timeout, max-time) thì chạy lại
stopasgroup=true
killasgroup=true
user=www-data
numprocs=8                ; 8 worker song song
redirect_stderr=true
stdout_logfile=/var/www/app/storage/logs/worker.log
stopwaitsecs=3600         ; chờ tối đa 3600s cho worker tự dừng trước khi SIGKILL
```

```sh
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start "laravel-worker:*"
```

⚠️ `stopwaitsecs`: khi dừng hoặc restart chương trình, Supervisor gửi `SIGTERM`, chờ `stopwaitsecs`
giây, quá hạn thì `SIGKILL`. Mặc định của Supervisor là 10 giây. Job 120 giây gặp deploy với
`stopwaitsecs=10` là bị giết giữa chừng mỗi lần deploy, rồi chạy lại sau `retry_after`. Đặt
`stopwaitsecs` lớn hơn timeout của job dài nhất. Kubernetes tương đương là
`terminationGracePeriodSeconds` (mặc định 30 giây).

Đối chiếu: Java/Spring thường dùng broker thật (RabbitMQ, Kafka) với consumer là thread trong một
process sống lâu; Go dùng goroutine đọc từ channel hoặc broker. Khái niệm "process worker tự kill
khi timeout, hàng đợi tự cứu job sau `retry_after`" là đặc thù của mô hình một job một process của
PHP; ở các broker khác, tương đương của `retry_after` là visibility timeout (SQS) hay ack timeout
(RabbitMQ consumer timeout).

**Tóm tắt nhanh**
- Attempt tăng lúc lấy job ra; release (rate limit, overlap) và timeout đều tiêu attempt. Mặc định
  `tries = 1`, `timeout = 60`, `retry_after = 90`.
- `timeout` < `retry_after` (vài giây trở lên), nếu không job chạy chồng nhiều lần, hoặc với
  `tries = 1` thì bị ghi `failed_jobs` trong khi bản đầu vẫn chạy thành công.
- Timeout = worker tự SIGKILL chính nó, cần `pcntl`; `finally` không chạy nên `WithoutOverlapping`
  cần `expireAfter`.
- Unique chặn lúc dispatch, WithoutOverlapping chặn lúc chạy, cả hai đều không thay được job
  idempotent (kiểm trạng thái, idempotency key, unique constraint).
- `SerializesModels` query lại model lúc chạy; dispatch trong transaction cần `afterCommit`.
- `queue:restart` ghi timestamp vào cache chung, worker tự thoát sau job; cần supervisor với
  `stopwaitsecs` lớn hơn job dài nhất. Horizon `auto` không ưu tiên queue theo thứ tự.

**Nguồn**: [Laravel: Queues](https://laravel.com/docs/13.x/queues) (Unique Jobs, Debounced Jobs, Job
Middleware, Queue Routing, Max Attempts and Timeout, Job Expirations and Timeouts, Job Batching,
Supervisor Configuration, Dealing With Failed Jobs) ·
[Laravel: Horizon](https://laravel.com/docs/13.x/horizon) (Balancing Strategies, Job Timeout,
Deploying Horizon) ·
mã nguồn `laravel/framework` 13.x (`Queue/Worker.php`, `Queue/WorkerOptions.php`,
`Queue/RedisQueue.php`, `Queue/DatabaseQueue.php`, `Queue/Middleware/WithoutOverlapping.php`,
`Bus/UniqueLock.php`, `Queue/CallQueuedHandler.php`) ·
[laravel/laravel 13.x `config/queue.php`](https://github.com/laravel/laravel/blob/13.x/config/queue.php) ·
[Supervisor: program configuration](http://supervisord.org/configuration.html#program-x-section-settings)

---

### 2.7 Các thành phần khác của Laravel

Module này trả lời: scheduler, cache, session, rate limiter, event, auth của Laravel hoạt động thế
nào bên dưới, và vì sao phần lớn lỗi của chúng chỉ lộ ra khi app chạy trên nhiều server. Mẫu câu
hỏi phỏng vấn điển hình là "chạy tốt trên một server, thêm server thứ hai thì X hỏng, vì sao".

Quy tắc chung của cả module: mọi thứ cần **phối hợp giữa các process** (lock, bộ đếm, session,
trạng thái "task đã chạy chưa") phải nằm ở một kho **dùng chung** mà mọi server cùng thấy. Đĩa cục
bộ và RAM của từng process không đạt yêu cầu đó.

```
             Load balancer
            /      |      \
      Web A      Web B      Web C        mỗi server có cron + FPM riêng
        |          |          |
   storage/    storage/    storage/      file cache, file session: KHÔNG dùng chung
        \          |          /
         +---- Redis / DB ---+           cache lock, rate limit, session, queue: dùng chung
```

#### Scheduler

*Scheduler* là bộ lập lịch của Laravel: bạn khai báo task trong code (thường ở
`routes/console.php`), và server chỉ cần **một** dòng cron:

```sh
* * * * * cd /path-to-your-project && php artisan schedule:run >> /dev/null 2>&1
```

Mỗi phút cron khởi động một process `schedule:run`, process này:

1. Boot app, nạp danh sách task đã khai báo.
2. Với từng task, so biểu thức cron của task với thời điểm hiện tại (`isDue`), rồi áp các điều
   kiện lọc (`when`, `skip`, maintenance mode, lock của `withoutOverlapping`).
3. Chạy các task đến giờ **tuần tự** theo thứ tự khai báo, trừ task có `runInBackground()`.
4. Thoát. Nếu có task chạy dưới một phút (`everySecond()`, `everyTenSeconds()`), process ở lại tới
   hết phút hiện tại để gọi các task đó.

```php
<?php
// routes/console.php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schedule;

Schedule::command('report:generate')
    ->fridays()->at('17:00')
    ->timezone('Asia/Ho_Chi_Minh')
    ->onOneServer();                 // chỉ một server chạy

Schedule::command('emails:send')
    ->everyMinute()
    ->withoutOverlapping(10)         // lock hết hạn sau 10 phút thay vì 24 giờ
    ->runInBackground();             // không chặn các task khác cùng phút

Schedule::call(fn (): int => DB::table('recent_users')->delete())
    ->name('purge-recent-users')     // closure muốn dùng onOneServer phải có name
    ->daily()
    ->onOneServer();
```

⚠️ Bẫy kinh điển: scale từ 1 lên 3 server, mỗi server đều có dòng cron, nên mỗi task chạy 3 lần.
Báo cáo gửi 3 lần, cron trừ tiền chạy 3 lần.

| Bước | Server A | Server B | Server C | Kết quả |
|---|---|---|---|---|
| 1 | 17:00 cron gọi `schedule:run` | 17:00 cron gọi `schedule:run` | 17:00 cron gọi `schedule:run` | Cả ba thấy `report:generate` đến giờ |
| 2 | Không có `onOneServer`: chạy | Chạy | Chạy | 3 báo cáo |
| 2' | Có `onOneServer`: lấy được lock, chạy | Lấy lock thất bại, bỏ qua | Lấy lock thất bại, bỏ qua | 1 báo cáo |

Cơ chế `onOneServer()` (đọc trong `CacheSchedulingMutex` của framework): tên lock là tên mutex của
task ghép với giờ phút hiện tại (định dạng `Hi`, ví dụ `1700`), lấy bằng cache lock (hoặc
`Cache::add`, cũng là thao tác nguyên tử) với TTL 3600 giây. Server nào lấy được trước thì chạy.
Lock **không** được nhả sau khi chạy xong; nó chỉ phục vụ đúng lượt 17:00 đó và tự hết hạn.

Điều kiện để `onOneServer` có tác dụng: cache store mặc định (hoặc store chỉ định qua
`Schedule::useCache('redis')`) phải là `database`, `memcached`, `dynamodb` hoặc `redis`, và mọi
server nối tới **cùng** một cache server. Để cache là `file` thì mỗi server có lock riêng trên đĩa
của nó, và cả ba vẫn chạy.

Hai cách sửa vụ "báo cáo gửi 3 lần":

1. Thêm `->onOneServer()` cho các task chỉ được chạy một lần, dùng cache Redis/DB chung.
2. Chỉ đặt cron trên **một** instance (một container "scheduler" riêng, hoặc một node được chỉ định).
   Đơn giản hơn, nhưng instance đó là điểm lỗi đơn: chết thì không task nào chạy.

`withoutOverlapping()` giải bài toán khác: không cho lần chạy mới bắt đầu khi lần trước **của chính
task đó** chưa xong (task chạy mỗi phút nhưng có lúc mất 3 phút).

| | `onOneServer()` | `withoutOverlapping()` |
|---|---|---|
| Chặn | Nhiều server cùng chạy **một lượt** | Lượt mới chồng lên lượt cũ đang chạy |
| Tên lock | Tên task + giờ phút của lượt | Tên task (không kèm thời gian) |
| Thời hạn lock | 3600 giây, không nhả chủ động | Mặc định 1440 phút (24 giờ), nhả khi task xong |
| Cần cache dùng chung | Có | Có, nếu muốn chặn chồng lấn giữa các server |

⚠️ Lock của `withoutOverlapping` kẹt khi process chết đột ngột. Framework có đăng ký handler cho
`SIGTERM`, `SIGINT`, `SIGQUIT` để xoá lock trước khi thoát, nhưng chỉ khi có extension `pcntl` và
task không chạy nền. `SIGKILL` (ví dụ OOM killer, `kill -9`, container bị giết cứng) không bắt được,
nên lock nằm đó tới khi hết hạn: với mặc định là 24 giờ task không chạy. Cách xử lý: đặt thời hạn
sát với thời gian chạy tối đa (`withoutOverlapping(10)`), và khi kẹt thì chạy
`php artisan schedule:clear-cache`.

Các chi tiết khác hay bị hỏi:

- `runInBackground()` chỉ dùng được với task `command` và `exec` (chạy thành process con riêng).
- Task không chạy khi app ở maintenance mode, trừ khi có `evenInMaintenanceMode()`.
- ⚠️ `timezone()` với múi giờ có daylight saving time: lúc đổi giờ task có thể chạy hai lần hoặc không
  chạy. Docs khuyên tránh đặt timezone theo task nếu được.
- Có task dưới một phút thì `schedule:run` sống cả phút, tức vẫn chạy code cũ sau khi deploy. Thêm
  `php artisan schedule:interrupt` vào script deploy.
- Máy dev dùng `php artisan schedule:work` thay cho cron.

#### Cache

API cơ bản (TTL tính bằng giây, hoặc truyền `DateTimeInterface`):

| Method | Làm gì |
|---|---|
| `get($k, $default)` | Đọc, không có thì trả default (mặc định `null`) |
| `put($k, $v, $ttl)` | Ghi đè; không truyền TTL là lưu vô hạn |
| `add($k, $v, $ttl)` | Chỉ ghi khi key chưa có, trả `true`/`false`; thao tác **nguyên tử** |
| `remember($k, $ttl, fn)` | Có thì trả, chưa có thì gọi closure, lưu, trả |
| `rememberForever`, `forever`, `forget`, `pull` | Lưu vô hạn, xoá, đọc rồi xoá |
| `increment`, `decrement` | Tăng/giảm số nguyên (nguyên tử trên Redis, Memcached, DB) |
| `touch($k, $ttl)` | Laravel 13: gia hạn TTL mà không đọc rồi ghi lại giá trị |
| `memo()` | Bọc một store, nhớ giá trị đã đọc trong phạm vi một request/job |

`Cache::memo()->get('k')` lần đầu gọi Redis, các lần sau trong cùng request lấy từ bộ nhớ. Mọi
thao tác ghi (`put`, `increment`, `remember`...) tự xoá bản nhớ rồi chuyển xuống store thật. Tính
năng này có từ Laravel 12 (bản 12.x, 2025), không phải mới ở 13.

*Tag* gắn nhãn nhiều key để xoá cả nhóm: `Cache::tags(['people', 'authors'])->put(...)`, rồi
`Cache::tags('authors')->flush()`. Muốn đọc lại phải truyền đúng danh sách tag đã dùng lúc ghi.
⚠️ Không hỗ trợ ở driver `file`, `dynamodb`, `database`, `storage`; trên thực tế là Redis hoặc
Memcached.

⚠️ `Cache::flush()` xoá **toàn bộ** store, không tôn trọng `prefix`. Redis dùng chung với app khác
(hoặc chung với queue) thì flush là xoá luôn dữ liệu của họ.

*Atomic lock* (khoá phân tán qua cache):

```php
<?php
declare(strict_types=1);

use Illuminate\Contracts\Cache\LockTimeoutException;
use Illuminate\Support\Facades\Cache;

$lock = Cache::lock('invoice:42', 10);        // lock tự hết hạn sau 10 giây
try {
    $lock->block(5);                          // chờ tối đa 5 giây, quá thì ném LockTimeoutException
    // ... phần chỉ một process được làm tại một thời điểm
} catch (LockTimeoutException) {
    // không lấy được lock
} finally {
    $lock->release();                         // chỉ owner (bên giữ token) nhả được
}

// Dạng ngắn: tự nhả sau khi closure chạy xong
Cache::lock('invoice:42', 10)->block(5, function (): void { /* ... */ });
```

- Mỗi lock có một *owner token* ngẫu nhiên. `release()` chỉ xoá lock nếu token khớp, nên process A
  không nhả nhầm lock mà process B vừa lấy sau khi lock của A hết hạn.
- Nhả lock ở process khác (lấy trong request, nhả trong job): truyền `$lock->owner()` vào job rồi
  `Cache::restoreLock('invoice:42', $owner)->release()`. `forceRelease()` bỏ qua owner.
- ⚠️ TTL lock phải dài hơn thời gian làm việc. Việc chạy 15 giây mà lock 10 giây thì từ giây thứ 10
  process khác vào được. Việc dài: lấy lock ngắn rồi gọi `$lock->refresh()` định kỳ.
- Driver hỗ trợ: `memcached`, `redis`, `dynamodb`, `database`, `file`, `array`. `file` và `array` chỉ
  có nghĩa trong một máy/một process.
- `Cache::funnel('k')->limit(3)` cho phép tối đa 3 process chạy song song (giới hạn đồng thời, không
  phải loại trừ).

*Cache stampede* (còn gọi là *dog-pile*): một key nóng hết hạn, hàng trăm request cùng thấy "miss",
cùng chạy câu query nặng, DB quá tải đúng lúc cao điểm. `remember` **không** chống được: nó chỉ là
"get, nếu null thì tính rồi put", không có lock nào giữa các request.

`Cache::flexible($key, [$fresh, $stale], fn)` áp dụng *stale-while-revalidate* (trả bản cũ trong lúc
làm mới ở nền). Đọc mã nguồn `Repository::flexible` ở 13.x:

1. Đọc cùng lúc giá trị và một key phụ lưu thời điểm tạo. Cả hai được lưu với TTL bằng `$stale`
   (số thứ hai).
2. Chưa có giá trị: tính **ngay** trong request, lưu, trả về (lúc cache lạnh vẫn có thể stampede).
3. Tuổi giá trị nhỏ hơn `$fresh`: trả luôn.
4. Tuổi nằm giữa `$fresh` và `$stale`: trả **bản cũ ngay**, và đăng ký một `defer` chạy sau khi gửi
   response. Hàm defer lấy một cache lock, kiểm tra chưa ai làm mới, rồi mới tính lại. Nhờ lock, chỉ
   một request thực sự chạy query.

| Bước (key `users`, `[5, 10]`) | Request A | Request B | Kết quả |
|---|---|---|---|
| t = 0 | Miss, tính, lưu | | Lưu giá trị + mốc tạo, TTL 10 giây |
| t = 3 | Tuổi 3 < 5: trả luôn | | Không query |
| t = 7 | Tuổi 7, stale: trả bản cũ, defer làm mới | Cùng lúc: trả bản cũ, defer làm mới | Chỉ bên lấy được lock chạy query, sau response |
| t = 12 (kịch bản khác: không có request nào từ t = 5 tới t = 10) | | Key đã hết hạn ở t = 10, miss, tính đồng bộ | Chậm như `remember` |

Cách khác chống stampede: bọc phần tính bằng `Cache::lock` (một process tính, số còn lại chờ rồi đọc
lại), cộng *jitter* ngẫu nhiên vào TTL để các key không cùng hết hạn, hoặc làm ấm cache bằng job định
kỳ. Chi tiết ở [11-cache.md](../11-cache.md).

#### Session và rate limiting

Driver session: `file` (thư mục `storage/framework/sessions`), `cookie` (mã hoá, nằm trong cookie),
`database` (**mặc định** của app Laravel mới), `memcached`/`redis`, `dynamodb`, `array` (cho test).

⚠️ `file` hỏng khi có nhiều server sau load balancer: user đăng nhập ở server A, session nằm trên đĩa
A; request sau được chia sang B, B không thấy file, user bị đăng xuất hoặc lỗi CSRF 419. *Sticky
session* (load balancer ghim user vào một server) chỉ che bệnh: server đó chết là mất session, và tải
phân bổ lệch. Cách đúng là `database` hoặc `redis`.

*Session blocking*: mặc định hai request cùng session chạy song song; nếu cả hai cùng ghi session,
bên ghi sau đè bên ghi trước. `Route::post(...)->block($lockSeconds = 10, $waitSeconds = 10)` bắt các
request cùng session xếp hàng, dùng atomic lock của cache (không dùng được với driver session
`cookie`).

*Rate limiting* cho route:

```php
<?php
// app/Providers/AppServiceProvider.php, trong boot()
declare(strict_types=1);

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;

RateLimiter::for('api', function (Request $request): Limit {
    return Limit::perMinute(60)->by($request->user()?->id ?: $request->ip());
});

RateLimiter::for('login', fn (Request $request): array => [
    Limit::perMinute(500),                                     // trần chung
    Limit::perMinute(3)->by('email:' . $request->string('email')), // theo từng email
]);

// routes/api.php
// Route::middleware('throttle:api')->group(...);
```

- Vượt giới hạn: Laravel trả HTTP 429 kèm header thời gian chờ; đổi response bằng `->response(fn)`.
- `->after(fn (Response $r): bool => $r->status() === 404)` chỉ đếm response thoả điều kiện, ví dụ
  chống dò id bằng cách giới hạn số lần 404.
- Nhiều limit trùng giá trị `by` phải thêm tiền tố (`minute:`, `day:`) để không đè key của nhau.
- Thuật toán (đọc `RateLimiter::increment`): *fixed window*. Lần đầu tạo key đếm với TTL bằng độ dài
  cửa sổ bằng `add`, rồi `increment`. ⚠️ Hệ quả: dồn 60 request ở giây cuối cửa sổ này và 60 ở giây
  đầu cửa sổ sau, tức 120 request trong 2 giây vẫn lọt.
- ⚠️ Bộ đếm nằm trong cache (store mặc định, hoặc key `limiter` trong `config/cache.php`). Cache là
  `file` trên 3 server thì mỗi server đếm riêng, giới hạn thực tế thành gấp 3.

#### Event, notification, broadcasting

*Event/listener*: code bắn một event (`OrderShipped::dispatch($order)`), mọi listener đăng ký cho
event đó được gọi. Laravel tự tìm listener bằng cách quét thư mục `app/Listeners` (method `handle`
hoặc `__invoke` có type-hint event). Production nên cache danh sách này bằng `php artisan optimize`
hoặc `event:cache`.

⚠️ Listener thường (không queue) chạy **đồng bộ trong request**: chậm thì request chậm, ném exception
thì exception lan ra và request lỗi, dù việc chính (lưu đơn hàng) đã xong.

Listener implement `ShouldQueue` được đẩy vào queue, chạy trong worker. Vấn đề còn lại là thời điểm
so với transaction:

| Bước | Request (trong `DB::transaction`) | Queue worker | Kết quả |
|---|---|---|---|
| 1 | `INSERT orders` (chưa commit) | | Dòng chỉ thấy trong transaction của request |
| 2 | `OrderPlaced::dispatch($order)`, listener queued được push vào Redis ngay | | |
| 3 | Vẫn đang làm việc khác | Lấy job, `Order::findOrFail($id)` | `ModelNotFoundException`: dòng chưa commit nên worker không thấy |
| 4 | Commit (hoặc rollback) | | Rollback thì job vẫn đã chạy với dữ liệu không tồn tại |

Ba interface giải quyết, ở ba vị trí khác nhau:

| Interface | Gắn vào | Tác dụng |
|---|---|---|
| `ShouldDispatchAfterCommit` | Event | Cả event chỉ được dispatch sau commit; rollback thì bỏ event |
| `ShouldQueueAfterCommit` | Listener queued | Job của listener chỉ được push sau commit |
| `ShouldHandleEventsAfterCommit` | Listener (kể cả đồng bộ) | Listener được gọi qua callback sau commit của transaction manager |

Không có transaction nào đang mở thì cả ba chạy ngay như bình thường. Muốn áp cho mọi job, đặt
`'after_commit' => true` trong cấu hình connection của queue. Larastan có rule
`JobDispatchedInTransactionUsesAfterCommitRule` bắt lỗi cùng loại với **job** dispatch trong
`DB::transaction(...)` ở mức static analysis (tắt mặc định, bật bằng
`checkDispatchInTransactionAfterCommit: true`; module 2.8).

Thêm hai công cụ trong docs 13.x: `Event::defer(fn)` gom mọi event bắn trong closure lại, chỉ
dispatch sau khi closure chạy xong (không dispatch nếu closure ném lỗi); thuộc tính
`#[DebounceFor(30)]` trên listener queued chỉ xử lý event **cuối cùng** trong 30 giây cho cùng
`debounceId` (cần cache dùng chung giữa các server).

*Notification*: một class gửi thông báo qua nhiều kênh; method `via()` trả danh sách kênh (`mail`,
`database`, `broadcast`, Slack, SMS...). Implement `ShouldQueue` thì mỗi cặp (người nhận, kênh) thành
**một job**: 3 người nhận × 2 kênh = 6 job. *On-demand notification* gửi cho địa chỉ không phải user
trong DB: `Notification::route('mail', 'ops@example.com')->notify(new DeployFailed($d))`.

🟡 *Broadcasting*: đẩy event từ server xuống trình duyệt qua WebSocket (driver Mercure dùng
server-sent events), thay cho việc client poll.

```
Event implements ShouldBroadcast
   | (mặc định đi qua queue; ShouldBroadcastNow thì gửi ngay)
Queue worker  --HTTP-->  WebSocket server (Reverb, Pusher, Ably) hoặc hub Mercure (SSE)
                                 |  push
                         Trình duyệt (Laravel Echo) đang subscribe channel
```

- Ba loại channel: public `Channel`, `PrivateChannel` (client phải qua xác thực), `PresenceChannel`
  (private và biết thêm ai đang ở trong channel, dùng cho "đang online", "đang gõ").
- Quyền nghe private/presence channel khai báo trong `routes/channels.php`:
  `Broadcast::channel('orders.{orderId}', fn (User $u, int $orderId): bool => $u->id === Order::findOrFail($orderId)->user_id)`.
- `broadcast(new Event)->toOthers()` không gửi lại cho chính người vừa thao tác.
- Driver `log` cho dev, `null` cho test.

#### Auth

Hai khái niệm lõi trong `config/auth.php`:

- *Guard*: **cách** xác định user của request. Guard `session` đọc session cookie; guard `sanctum`
  đọc cookie hoặc Bearer token.
- *Provider*: lấy user **từ đâu**, ví dụ driver `eloquent` với model `User`, hoặc `database` (query
  builder).

`Route::middleware('auth:admin')` nghĩa là "xác thực bằng guard `admin`".

*Sanctum* giải hai bài toán tách biệt:

1. *SPA authentication*: SPA của chính bạn gọi API Laravel. Sanctum **không dùng token**; nó dùng
   session cookie như web thường (guard `web`), nên có sẵn CSRF protection và token không bao giờ nằm
   trong JavaScript (XSS không lấy được).
2. *API token*: *personal access token* kiểu GitHub cho mobile app, script, bên thứ ba. Gửi qua
   header `Authorization: Bearer <token>`.

Luồng SPA mode:

1. SPA và API phải chung *top-level domain* (được khác subdomain, ví dụ `app.shop.vn` và
   `api.shop.vn`); domain của SPA khai trong cấu hình `stateful`; `bootstrap/app.php` gọi
   `$middleware->statefulApi()`.
2. SPA gọi `GET /sanctum/csrf-cookie`, Laravel đặt cookie `XSRF-TOKEN`.
3. SPA `POST /login`, gửi kèm header `X-XSRF-TOKEN` (Axios tự làm khi bật `withCredentials` và
   `withXSRFToken`). Login bằng guard session chuẩn.
4. Các request sau tự mang session cookie. Cần CORS `supports_credentials = true`, client
   `withCredentials`, và `session.domain = '.shop.vn'`.

Luồng token mode:

```php
<?php
declare(strict_types=1);

// Tạo token: plainTextToken chỉ xem được đúng lúc này
$token = $user->createToken('ci-deploy', ['server:update'])->plainTextToken;   // dạng "<id>|<chuỗi ngẫu nhiên>"

// Trong request đã xác thực bằng auth:sanctum
if ($request->user()->tokenCan('server:update')) {
    // ...
}
```

- DB chỉ lưu **SHA-256 hash** của token. Lộ bảng `personal_access_tokens` không lộ token dùng được.
- *Abilities* giống *scope* của OAuth. Middleware `abilities:a,b` (phải có đủ) và `ability:a,b` (có
  một là được).
- ⚠️ Với request từ SPA (cookie), `tokenCan()` **luôn trả `true`**. Vì vậy trong policy vẫn phải
  kiểm cả quyền của user, không chỉ quyền của token.
- ⚠️ Mặc định token **không hết hạn**; đặt `expiration` (phút) trong `config/sanctum.php` nếu cần.
- Sanctum xét cookie trước, không có cookie mới xét Bearer token.
- Sanctum **không** phải OAuth2 server: không có authorization code flow, không có refresh token,
  không có khái niệm "client app bên thứ ba xin quyền thay user".

| | Sanctum SPA | Sanctum token | Passport |
|---|---|---|---|
| Dành cho | SPA của chính bạn | Mobile, script, API key | Bên thứ ba đăng nhập bằng tài khoản của bạn |
| Cơ chế | Session cookie + CSRF | Bearer token, hash trong DB | OAuth2 đầy đủ (authorization code, PKCE, refresh token, client) |
| Độ phức tạp | Thấp | Thấp | Cao |

*Phân quyền* (authorization, khác với xác thực):

```php
<?php
declare(strict_types=1);

namespace App\Policies;

use App\Models\Post;
use App\Models\User;

final class PostPolicy
{
    // Chạy trước mọi method của policy
    public function before(User $user, string $ability): ?bool
    {
        return $user->isAdministrator() ? true : null;   // null: để method cụ thể quyết định
    }

    public function update(User $user, Post $post): bool
    {
        return $user->id === $post->user_id;
    }
}
// Dùng: Gate::authorize('update', $post); hoặc $user->can('update', $post)
```

- *Gate*: closure kiểm quyền, `Gate::define('edit-settings', fn (User $u): bool => ...)`.
- *Policy*: class gom quyền theo một model, Laravel tự tìm theo quy ước tên (`Post` với `PostPolicy`).
- `Gate::before(fn)`: kết quả **khác `null`** được dùng luôn làm kết quả kiểm tra. ⚠️ Viết
  `return $user->isAdmin();` là sai: user thường nhận `false` và bị từ chối **mọi** quyền. Phải trả
  `true` hoặc `null`. `Gate::after` chỉ có tác dụng khi gate/policy trả `null`.
- Laravel 13 thêm attribute `#[Authorize('create', [Comment::class, 'post'])]` và `#[Middleware]`
  đặt thẳng trên controller method.
- Lý thuyết JWT/session/OAuth: [10-security.md](../10-security.md).

#### Tiện ích mới từ Laravel 11

(`defer`, `Concurrency` và `Context` có từ Laravel 11; `Http::pool()` và `Process` có từ trước
đó, đặt chung ở đây để so sánh.)

`defer(fn)` (hàm `Illuminate\Support\defer`): chạy closure **sau khi response đã gửi** cho user.

- Middleware `InvokeDeferredCallbacks` gọi các callback ở pha `terminate`, chỉ khi status < 400,
  trừ callback có `->always()`. Có thể đặt tên rồi huỷ: `defer(fn, 'name')`, `defer()->forget('name')`.
- ⚠️ Dưới PHP-FPM, user đã nhận response nhưng **worker FPM vẫn bận** tới khi callback chạy xong.
  Callback 5 giây là mất một worker 5 giây; nhiều thì cạn `pm.max_children` (module 2.2).
- ⚠️ Không bền: process chết giữa chừng là mất, không retry. Việc bắt buộc phải xảy ra thì dùng queue.

`Concurrency::run([...])`: chạy nhiều closure song song. Cơ chế theo docs: closure được **serialize**,
gửi cho một Artisan command ẩn, command đó chạy trong **process PHP con** riêng, kết quả serialize
ngược về process cha.

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\Concurrency;
use Illuminate\Support\Facades\DB;

[$users, $orders] = Concurrency::run([
    fn (): int => DB::table('users')->count(),
    fn (): int => DB::table('orders')->count(),
], timeout: 30);
```

- Driver: `process` (mặc định), `fork` (nhanh hơn, cần `spatie/fork`, **chỉ ở CLI** vì PHP không fork
  được trong web request), `sync` (chạy tuần tự, cho test).
- ⚠️ Không phải thread, không chia sẻ bộ nhớ: biến bị `use` vào closure phải serialize được, sửa biến
  trong closure không ảnh hưởng process cha. Mỗi process con boot lại app và mở connection DB riêng.
- `Concurrency::defer([...])`: chạy song song sau khi gửi response, không cần kết quả.

`Http::pool()`: gửi nhiều HTTP request song song **trong cùng process** (Guzzle đẩy nhiều request lên
curl cùng lúc, chờ I/O chồng lên nhau). Không tốn process con như `Concurrency`. Tham số
`concurrency:` giới hạn số request đang bay; request lỗi ở tầng kết nối trả về
`ConnectionException` trong mảng kết quả thay vì ném.

```php
<?php
declare(strict_types=1);

use Illuminate\Http\Client\Pool;
use Illuminate\Support\Facades\Http;

$r = Http::pool(fn (Pool $pool): array => [
    $pool->as('rates')->timeout(3)->get('https://api.example.com/rates'),
    $pool->as('stock')->timeout(3)->get('https://api.example.com/stock'),
    $pool->as('promo')->timeout(3)->get('https://api.example.com/promo'),
]);
// Thời gian chờ xấp xỉ request chậm nhất, không phải tổng ba request
```

`Context`: gắn dữ liệu (trace id, tenant, URL) một lần, ví dụ trong middleware
`Context::add('trace_id', (string) Str::uuid())`. Dữ liệu đó tự xuất hiện ở phần metadata của **mọi
dòng log**, và khi dispatch job nó được *dehydrate* (đóng gói) vào payload rồi *hydrate* (khôi phục)
lại khi worker chạy job. Log của job vì vậy cùng trace id với request đã tạo ra nó.
`Context::addHidden()` truyền sang job nhưng không ghi vào log (dữ liệu nhạy cảm).

`Process` facade (bọc Symfony Process): `Process::timeout(120)->run(['pg_dump', '-Fc', $db])`.
Mặc định ném `ProcessTimedOutException` sau **60 giây**. `->throw()` ném lỗi khi exit code khác 0.
⚠️ Truyền **mảng** thì lệnh chạy trực tiếp không qua shell (source: mảng đi vào `new Process`, chuỗi đi
vào `Process::fromShellCommandline`), nên tham số từ user không gây *command injection*. Truyền chuỗi
có ghép input người dùng là lỗ hổng.

Chọn công cụ cho ba ca của tiêu chí "Nắm chắc khi":

| Ca | Chọn | Vì sao |
|---|---|---|
| Ghi metric sau request | `defer()` | Nhanh, mất vài bản ghi chấp nhận được, không cần hạ tầng queue |
| Gửi email xác nhận | Queued job (hoặc notification `ShouldQueue`) | Cần bền và retry khi SMTP lỗi; không giữ worker FPM |
| Gọi 3 API lấy dữ liệu cho response | `Http::pool()` | Cần kết quả ngay; I/O song song trong một process. `Concurrency::run` chỉ đáng dùng khi việc song song là CPU hoặc không phải HTTP |

Laravel 13 (phát hành 17/03/2026, yêu cầu PHP ≥ 8.3) còn thêm: JSON:API resources, vector search
`whereVectorSimilarTo` trên PostgreSQL + pgvector, Laravel AI SDK, `Queue::route(Job::class, ...)`,
middleware CSRF đổi tên thành `PreventRequestForgery` (kiểm thêm origin), và nhiều PHP attribute
(`#[Tries]`, `#[Backoff]`, `#[Timeout]`...). AI SDK xem [23-ai-llm-backend.md](../23-ai-llm-backend.md).

**Tóm tắt nhanh**
- Nhiều server: cron chạy ở mọi server; `onOneServer()` + cache Redis/DB chung, hoặc cron chỉ trên
  một instance. `withoutOverlapping` chặn chồng lượt, lock mặc định 24 giờ, kẹt khi process bị
  `SIGKILL`.
- `remember` không chống stampede; `flexible` trả bản cũ và làm mới sau response, dưới một lock.
- Session `file` và rate limit trên cache `file` hỏng khi có nhiều server. Rate limiter là fixed
  window.
- Job/listener dispatch trong transaction phải after commit (`ShouldQueueAfterCommit`,
  `ShouldDispatchAfterCommit`, `after_commit`).
- Sanctum SPA dùng session cookie + CSRF, token mode lưu hash SHA-256; không phải OAuth2, cần bên thứ
  ba thì Passport. `Gate::before` trả `null`, đừng trả `false`.
- `defer` vẫn giữ worker FPM; `Concurrency` là process con, closure bị serialize; `Http::pool` cho
  gọi API song song.

**Nguồn**: [Laravel: Task Scheduling](https://laravel.com/docs/scheduling) ·
[Laravel: Cache](https://laravel.com/docs/cache) · [Laravel: Session](https://laravel.com/docs/session) ·
[Laravel: Routing, Rate Limiting](https://laravel.com/docs/routing#rate-limiting) ·
[Laravel: Events](https://laravel.com/docs/events) · [Laravel: Notifications](https://laravel.com/docs/notifications) ·
[Laravel: Broadcasting](https://laravel.com/docs/broadcasting) · [Laravel: Authentication](https://laravel.com/docs/authentication) ·
[Laravel: Sanctum](https://laravel.com/docs/sanctum) · [Laravel: Authorization](https://laravel.com/docs/authorization) ·
[Laravel: Concurrency](https://laravel.com/docs/concurrency) · [Laravel: Context](https://laravel.com/docs/context) ·
[Laravel: HTTP Client](https://laravel.com/docs/http-client#concurrent-requests) · [Laravel: Processes](https://laravel.com/docs/processes) ·
[Laravel: Helpers, Deferred Functions](https://laravel.com/docs/helpers#deferred-functions) ·
[Laravel: Release Notes](https://laravel.com/docs/releases) ·
mã nguồn [laravel/framework 13.x](https://github.com/laravel/framework/tree/13.x/src/Illuminate)
(`Console/Scheduling/CacheSchedulingMutex.php`, `Console/Scheduling/Event.php`, `Cache/Repository.php`,
`Cache/RateLimiter.php`, `Events/Dispatcher.php`, `Process/PendingProcess.php`)


---

### 2.8 Chất lượng code PHP: PHPStan, Rector, Pint

Module này trả lời: PHP không có bước compile kiểm kiểu thì team lấy gì bắt lỗi trước production, ba
công cụ PHPStan (phân tích), Rector (sửa tự động), Pint (định dạng) làm gì khác nhau, và đưa chúng
vào một codebase cũ hàng trăm nghìn dòng thế nào mà không bắt cả team dừng lại để sửa lỗi.

```
                 đọc code, KHÔNG sửa        sửa code theo rule          sửa khoảng trắng, xuống dòng
PR mở  -->  Pint --test  -->  Rector --dry-run  -->  PHPStan analyse  -->  PHPUnit/Pest  -->  merge
            (style)           (refactor còn sót)     (lỗi kiểu, logic)     (hành vi)
```

#### Vì sao cần static analysis

*Static analysis* (phân tích tĩnh) là đọc code mà không chạy nó để tìm lỗi: gọi method không tồn tại,
truyền sai kiểu, dùng biến có thể `null`, nhánh code không bao giờ chạy tới.

Java và Go kiểm những lỗi này lúc compile; chương trình sai kiểu không build được. PHP chỉ kiểm kiểu
**lúc chạy**, và chỉ ở dòng thực sự được chạy tới:

```php
<?php
declare(strict_types=1);

final class User
{
    public function __construct(public string $name) {}
}

function findUser(int $id): ?User
{
    return $id === 1 ? new User('An') : null;
}

function greet(int $id): string
{
    return 'Hi ' . findUser($id)->name;   // id = 1: chạy tốt. id = 2: Warning "Attempt to read property on null"
}

echo greet(1), PHP_EOL;   // Hi An
echo greet(2), PHP_EOL;   // Warning: Attempt to read property "name" on null ... rồi in "Hi "
```

(PHP 7.x báo Notice "Trying to get property 'name' of non-object"; PHP 8 nâng lên Warning. Cả hai
đều không dừng chương trình, và response sai vẫn được trả về.)

Test chỉ bắt được nếu có test cho id không tồn tại. PHPStan ở level 8 báo ngay dòng đó mà không cần
chạy: không truy cập được property `$name` trên kiểu `User|null`. Vì vậy trong hệ sinh thái PHP,
static analysis đóng vai **compiler thứ hai**.

#### PHPStan

Cách PHPStan làm việc:

1. Parse mọi file thành *AST* (cây cú pháp, dùng thư viện `nikic/php-parser`).
2. Đọc type khai báo native (`int`, `?User`) **và** type trong PHPDoc (`@param list<User>`), đọc
   reflection của class trong `vendor/` qua autoload của Composer.
3. Suy luận kiểu của từng biểu thức theo luồng code (sau `if ($u === null) return;` thì `$u` là
   `User`), rồi áp các rule tương ứng với level.
4. Không chạy code của bạn (Larastan là ngoại lệ, xem bên dưới). Kết quả được cache; lần sau chỉ phân
   tích lại file thay đổi và file phụ thuộc.

*Rule level*: 11 mức từ 0 (lỏng nhất) tới 10 (chặt nhất), mặc định 0. Level **cộng dồn**: level 5 gồm
mọi kiểm tra của 0 đến 4. `--level max` là bí danh cho level cao nhất của bản đang cài.

| Level | Thêm kiểm tra gì |
|---|---|
| 0 | Class, function không tồn tại; method không tồn tại trên `$this`; sai số lượng tham số; biến chắc chắn chưa định nghĩa |
| 1 | Biến *có thể* chưa định nghĩa; method/property magic không rõ trên class có `__call`, `__get` |
| 2 | Method không tồn tại trên **mọi** biểu thức (không chỉ `$this`); kiểm PHPDoc hợp lệ |
| 3 | Kiểu trả về, kiểu gán vào property |
| 4 | Dead code cơ bản: `instanceof` luôn false, nhánh `else` chết, code sau `return` |
| 5 | Kiểu của tham số truyền vào function/method |
| 6 | Báo thiếu type hint (kể cả thiếu kiểu phần tử của `array`) |
| 7 | Union type sai một phần: gọi method chỉ có trên một số kiểu trong union |
| 8 | Gọi method, truy cập property trên kiểu *nullable* |
| 9 | Chặt với `mixed` **khai báo rõ**: chỉ được truyền nó cho chỗ nhận `mixed` |
| 10 | Mới từ PHPStan 2.0: chặt cả với `mixed` **ngầm** (thiếu type hint) |

*Mixed ngầm* và *mixed rõ*: tham số không có type là mixed ngầm; `@param mixed $x` hoặc `mixed $x` là
mixed rõ. Level 6 chấp nhận mixed rõ nhưng không chấp nhận thiếu type. Level 9 cấm thao tác trên mixed
rõ. Level 10 cấm cả trên mixed ngầm. PHPStan 2.x còn bỏ các tuỳ chọn cũ `checkMissingIterableValueType`
và `checkGenericClassInNonGenericObjectType`; muốn tắt thì bỏ qua theo *error identifier*
`missingType.iterableValue`, `missingType.generics`.

*Kiểu trong PHPDoc* mô tả chi tiết hơn những gì PHP native có:

| Cú pháp | Nghĩa |
|---|---|
| `array<int, User>` | Array key int, value `User` (generic array) |
| `list<string>` | Array key liên tục 0, 1, 2...; `array_values()` trả `list` |
| `non-empty-list<int>`, `non-empty-array<...>` | Như trên, có ít nhất một phần tử |
| `array{id: int, name: string, email?: string}` | *Array shape*: từng key có kiểu riêng, `?` là key tuỳ chọn |
| `list{int, string}` | Tuple: key 0 là int, key 1 là string |
| `int<1, 100>`, `positive-int`, `non-negative-int` | Khoảng số nguyên |
| `non-empty-string`, `numeric-string` | Chuỗi khác `''`; chuỗi dạng số |
| `class-string<Model>` | Chuỗi là tên class con của `Model` |
| `'draft'\|'paid'` | Literal type: chỉ nhận hai giá trị này |
| `Collection<int, Order>` | Class generic với tham số kiểu |

⚠️ Theo docs PHPStan hiện tại, array shape mặc định là *sealed*: không cho key thừa. Muốn cho phép thì
thêm `...` ở cuối: `array{id: int, ...}` (cú pháp *unsealed* có từ PHPStan 2.2, 5/2026). Trước đó
PHPStan không kiểm key thừa khi truyền array vào tham số kiểu shape; ở 2.2 việc kiểm chặt này chỉ bật
khi dùng *bleeding edge*, nên code cũ có key thừa có thể bắt đầu báo lỗi khi bật nó.

*Generics*: PHP không có generics native (RFC năm 2016 không đi tới đâu), nên PHPStan định nghĩa qua
PHPDoc bằng *type variable* `@template`. PHPStan suy ra `T` từ tham số ở mỗi lần gọi, rồi áp vào kiểu
trả về.

```php
<?php
declare(strict_types=1);

/**
 * @template T
 */
final class TypedList
{
    /** @var list<T> */
    private array $items = [];

    /** @param T $item */
    public function add(mixed $item): void
    {
        $this->items[] = $item;
    }

    /** @return T|null */
    public function first(): mixed
    {
        return $this->items[0] ?? null;
    }
}

/**
 * @template T of object
 * @param class-string<T> $class
 * @return T
 */
function make(string $class): object
{
    return new $class();
}

/** @var TypedList<DateTimeImmutable> $dates */
$dates = new TypedList();
$dates->add(new DateTimeImmutable());
$dates->add('2026-01-01');                         // PHPStan level 5: tham số phải là DateTimeImmutable, string được truyền
\PHPStan\dumpType($dates->first());                // PHPStan in: Dumped type: DateTimeImmutable|null
\PHPStan\dumpType(make(ArrayObject::class));       // PHPStan in: Dumped type: ArrayObject
```

`\PHPStan\dumpType()` chỉ có tác dụng lúc phân tích (in kiểu suy luận được thành một dòng báo cáo);
xoá trước khi commit. `@template T of object` đặt *upper bound*; class con chỉ định kiểu cho cha bằng
`@extends Base<User>`, `@implements Repo<User>`, `@use Trait<User>`.

*Baseline*: file ghi lại toàn bộ lỗi hiện có để tạm bỏ qua, nhờ vậy chạy được level cao ngay mà không
phải sửa hết trước.

```sh
vendor/bin/phpstan analyse --level 6 --generate-baseline      # tạo phpstan-baseline.neon
vendor/bin/phpstan analyse --generate-baseline phpstan-baseline.php  # dạng PHP, nhanh hơn khi file rất lớn
```

```neon
# phpstan-baseline.neon (PHPStan tự sinh)
parameters:
	ignoreErrors:
		-
			message: '#^Cannot access property \$name on App\\Models\\User\|null\.$#'
			identifier: property.nonObject
			count: 2
			path: app/Http/Controllers/ProfileController.php
```

- Baseline ghi theo **file + nội dung lỗi + số lần**, không theo số dòng, nên sửa code chỗ khác trong
  file không làm baseline lệch. Nhưng thêm một lỗi **cùng loại** vào cùng file thì `count` vượt, và
  lỗi mới được báo.
- Sửa xong một lỗi mà không cập nhật baseline: PHPStan báo "ignored error pattern was not matched"
  (`reportUnmatchedIgnoredErrors`, mặc định bật). Chạy lại `--generate-baseline` để baseline chỉ nhỏ
  dần.
- ⚠️ Đừng regenerate baseline để giấu lỗi **mới**. Docs PHPStan nói thẳng mục tiêu sống của baseline
  là biến mất. Lỗi mới thật sự không sửa được thì bỏ qua tại chỗ, có identifier và lý do:
  `// @phpstan-ignore argument.type (thư viện X khai báo sai kiểu)`. Từ 2.1.41 có
  `reportIgnoresWithoutComments: true` bắt buộc phải có lý do.

Quy trình đưa vào codebase cũ (tiêu chí "Nắm chắc khi" và bài tập 6):

1. `composer require --dev phpstan/phpstan larastan/larastan phpstan/phpstan-deprecation-rules`.
2. Viết `phpstan.neon` (mẫu bên dưới), chọn level mục tiêu hợp lý (thường 5 hoặc 6 cho app cũ).
3. `--generate-baseline`, commit cả config và baseline.
4. CI chạy `phpstan analyse` trên mọi PR: lỗi cũ nằm trong baseline, **lỗi mới làm PR đỏ**.
5. Sửa dần lỗi trong baseline (mỗi lần chạm vào file nào thì dọn file đó). Baseline nhỏ lại thì nâng
   level một bậc và tạo baseline mới cho các lỗi của level đó.

```neon
# phpstan.neon
includes:
    - vendor/larastan/larastan/extension.neon
    - vendor/phpstan/phpstan-deprecation-rules/rules.neon   # bỏ nếu đã cài phpstan/extension-installer
    - phpstan-baseline.neon

parameters:
    level: 6
    paths:
        - app/
        - config/
        - database/
        - routes/
    excludePaths:
        - app/Legacy/Generated/*
    reportUnmatchedIgnoredErrors: true
```

⚠️ Codebase lớn hay gặp `Allowed memory size exhausted`: chạy với `--memory-limit=2G`.

*Larastan*: extension PHPStan cho Laravel. Laravel nhiều "magic" mà PHPStan thuần không hiểu: facade
gọi static tới object trong container, property của Eloquent model đến từ cột DB, relationship, query
scope. Larastan xử lý bằng cách **boot container của app** để biết facade trỏ tới class nào, và quét
**migration** để suy ra cột (tức property) của model. Chính README gọi đây là "code analysis" thay vì
"static analysis" vì nó có chạy một phần app.

- Phiên bản: Larastan 3.x cho Laravel 11.16+ (yêu cầu PHP 8.2+), cài `larastan/larastan:^3.0`.
- Relationship phải khai generic thì Larastan mới biết model đích:

```php
<?php
declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

final class Post extends Model
{
    /** @return BelongsTo<User, $this> */
    public function author(): BelongsTo
    {
        return $this->belongsTo(User::class, 'user_id');
    }

    /** @return HasMany<Comment, $this> */
    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }
}
```

- Rule riêng đáng biết: `NoEnvCallsOutsideOfConfig` (bật mặc định: `env()` ngoài thư mục `config/`
  trả `null` khi đã `config:cache`), `JobDispatchedInTransactionUsesAfterCommitRule` (tắt mặc định:
  job dispatch trong `DB::transaction` thiếu after commit, xem module 2.7), `OctaneCompatibilityRule`
  (tắt mặc định),
  `checkModelProperties` (tắt mặc định: kiểm tên cột trong `User::create([...])`).
- Kiểu PHPDoc riêng: `view-string`, `model-property<User>`, `collection-of<...>`, `builder-of<...>`.

⚠️ Vì sao level 9 và 10 hay bắn lỗi ở `$request->input()`: method này khai báo `@return mixed` trong
framework. Phép toán số học, gọi method, truyền giá trị đó vào tham số kiểu `int` hay trả nó ra làm
`int` đều bị level 9 chặn. (So sánh như `$age > 60` thì không bị báo, vì PHP 8 cho so sánh mọi kiểu;
đã thử trên PHPStan playground.)

```php
<?php
declare(strict_types=1);

use Illuminate\Http\Request;

enum Tier: string
{
    case Basic = 'basic';
    case Vip = 'vip';
}

function isSenior(int $age): bool
{
    return $age > 60;
}

// SAI ở level 9
function discountBad(Request $request): int
{
    $age = $request->input('age');       // mixed
    return isSenior($age) ? 20 : 0;      // level 9: Parameter #1 $age expects int, mixed given
}

// Cách 1: getter có kiểu của Request (trait InteractsWithData)
function discountTyped(Request $request): int
{
    $age  = $request->integer('age');                       // int, thiếu thì 0
    $name = $request->string('name')->trim()->toString();   // string
    $tier = $request->enum('tier', Tier::class);            // Tier|null
    return ($age > 60 || $tier === Tier::Vip) ? 20 : 0;
}

// Cách 2: thu hẹp kiểu bằng kiểm tra runtime; PHPStan hiểu is_int, instanceof, assert
function discountNarrowed(Request $request): int
{
    $raw = $request->input('age');
    if (!is_int($raw)) {
        throw new InvalidArgumentException('age must be int');
    }
    return $raw > 60 ? 20 : 0;           // từ đây $raw là int
}
```

Cách 3, bền nhất: validate trong FormRequest rồi map ngay sang một DTO có property khai kiểu
(`final readonly class DiscountInput { public function __construct(public int $age) {} }`), để phần
còn lại của code không bao giờ chạm vào mixed.

*phpstan-deprecation-rules*: báo mọi chỗ dùng class, method, property, constant có `@deprecated`.
Chạy trước khi nâng Laravel hoặc thư viện: thứ bị đánh dấu deprecated ở bản hiện tại thường bị xoá ở
major sau. Code của vendor không có `@deprecated` thì khai thêm qua *stub file*.

*Psalm* là công cụ tương tự PHPStan (của Vimeo). Điểm mạnh riêng là *taint analysis*
(`--taint-analysis`): đánh dấu dữ liệu từ nguồn không tin cậy (`$_GET`, request) và lần theo tới
*sink* nguy hiểm (câu SQL ghép chuỗi, `echo` HTML, `exec`), báo SQL injection, XSS ở mức static. Nhiều
team chạy PHPStan cho kiểu và Psalm chỉ cho taint.

#### Rector

*Rector* **sửa code tự động** theo rule: parse thành AST, mỗi rule tìm một mẫu và biến đổi nút AST, rồi
in lại code. Rector dùng PHPStan để biết kiểu, nên thứ PHPStan chỉ thấy là `mixed` thì Rector cũng
không dám đổi.

Ví dụ diff sinh ra khi bật set PHP 8.0 và set `typeDeclarations`:

```diff
 final class Money
 {
-    private int $amount;
-
-    public function __construct(int $amount)
-    {
-        $this->amount = $amount;
-    }
+    public function __construct(private int $amount)      // php80: constructor promotion
+    {
+    }

-    public function hasCode(string $s)
+    public function hasCode(string $s): bool              // typeDeclarations: thêm return type
     {
-        return strpos($s, 'VND') !== false;
+        return str_contains($s, 'VND');                     // php80: StrContainsRector
     }
 }
```

Cấu hình `rector.php`:

```php
<?php
declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Php80\Rector\Class_\ClassPropertyAssignToConstructorPromotionRector;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/app', __DIR__ . '/tests'])
    ->withPhpSets()                            // nâng cú pháp tới bản PHP khai trong composer.json
    ->withComposerBased(laravel: true)         // rule nâng cấp Laravel theo bản đang cài (rector-laravel)
    ->withTypeCoverageLevel(0)                 // thêm type, tăng dần từng bậc
    ->withDeadCodeLevel(0)
    ->withSkip([
        ClassPropertyAssignToConstructorPromotionRector::class => [__DIR__ . '/app/Models'],
    ])
    ->withCache(cacheDirectory: '/tmp/rector'); // đường dẫn cố định để cache được giữa các lần chạy CI
```

- *Set list*: nhóm rule theo chủ đề. `withPhpSets()` đọc bản PHP trong `composer.json`; hoặc chỉ định
  `withPhpSets(php84: true)`. `withPreparedSets(deadCode: true, codeQuality: true, typeDeclarations: true, ...)`.
- ⚠️ Bật cả set một lúc trên codebase cũ sinh diff chạm 90% file, không ai review nổi. Docs Rector
  khuyên dùng *level*: `withPhpLevel(N)`, `withTypeCoverageLevel(N)` bật N+1 rule đầu tiên của set,
  xếp từ an toàn nhất. Mỗi lần tăng một, chạy, review diff nhỏ, merge, lặp lại. Đạt hết level thì
  chuyển sang set đầy đủ.
- Ví dụ docs: project khai `"php": "^7.4"` mà bật `withPhpSets()` là chạy cả set từ 5.3 tới 7.4, hơn
  100 rule một lần.
- `vendor/bin/rector process --dry-run` chỉ in diff; exit code 1 khi có file sẽ bị đổi, nên CI dùng
  lệnh này để bắt code mới viết theo kiểu cũ. `--output-format=github` hiện chú thích ngay trên PR.
- *rector-laravel* (`driftingly/rector-laravel`): `withComposerBased(laravel: true)` tự áp các set nâng
  cấp tới bản Laravel đang cài; các set `LaravelLevelSetList::UP_TO_LARAVEL_130` kiểu cũ đã deprecated.
  Có thêm set chất lượng như `LARAVEL_CODE_QUALITY`, `LARAVEL_COLLECTION`, `LARAVEL_TYPE_DECLARATIONS`.
- ⚠️ Rector in lại code qua php-parser nên có thể lệch style; luôn chạy formatter **sau** Rector.
- Docs Rector khuyên có coding standard và PHPStan (khoảng level 3 đến 4, **không** baseline) trước
  khi dùng Rector.

Đọc diff của Rector như review code của đồng nghiệp: kiểm rule đổi hành vi hay chỉ đổi cú pháp. Ví dụ
thêm return type `: int` vào method mà class con override trả `string` sẽ làm fatal error lúc load
class con.

#### Formatter

*Formatter* tự sắp code theo một style thống nhất: thụt lề, khoảng trắng, vị trí ngoặc, thứ tự
`use`. Mục đích là để review không phải bàn chuyện dấu cách, và diff chỉ chứa thay đổi thật.

*Laravel Pint* được cài sẵn trong app Laravel mới, xây trên *PHP-CS-Fixer*. Không cần cấu hình: mặc
định dùng preset `laravel`. Các preset: `laravel`, `per`, `psr12`, `symfony`, `empty` (tự khai từ đầu).
*PSR-12* là chuẩn style cũ của PHP-FIG; *PER Coding Style* là bản kế nhiệm, cập nhật theo cú pháp PHP
mới.

```json
{
    "preset": "laravel",
    "rules": {
        "declare_strict_types": true,
        "strict_comparison": true,
        "ordered_imports": { "sort_algorithm": "alpha" }
    },
    "exclude": ["storage", "bootstrap/cache"]
}
```

Mọi rule của PHP-CS-Fixer đều dùng được trong `pint.json`. ⚠️ `declare_strict_types` và
`strict_comparison` là rule *risky*: chúng đổi hành vi (thêm `declare(strict_types=1)` làm một số lời
gọi đang chạy nhờ ép kiểu thành `TypeError`; đổi `==` thành `===` đổi kết quả so sánh). Bật trên code
cũ thì phải chạy test.

| Lệnh | Dùng khi |
|---|---|
| `vendor/bin/pint` | Sửa toàn bộ |
| `vendor/bin/pint --test` | CI: chỉ kiểm, exit code khác 0 nếu có lỗi style |
| `vendor/bin/pint --dirty` | Pre-commit: chỉ file có thay đổi chưa commit |
| `vendor/bin/pint --diff=main` | CI: chỉ file khác nhánh `main` |
| `vendor/bin/pint --repair` | Sửa, nhưng vẫn trả exit code khác 0 nếu đã phải sửa |
| `vendor/bin/pint --parallel` | Chạy song song (thử nghiệm) |

Có thể dùng PHP-CS-Fixer trực tiếp (file `.php-cs-fixer.php`) nếu cần cấu hình mà Pint không cho, hoặc
project không phải Laravel.

#### Kiểm tra khi nâng cấp và test

Checklist trước khi nâng PHP hoặc Laravel:

1. `composer audit`: đối chiếu package đang cài với cơ sở dữ liệu lỗ hổng bảo mật đã công bố.
2. PHPStan + `phpstan-deprecation-rules`: tìm chỗ dùng API sắp bị xoá.
3. Nâng ràng buộc `php` trong `composer.json`, chạy Rector (`withPhpSets()` đọc bản đó,
   `withComposerBased(laravel: true)` đọc bản Laravel), `--dry-run` rồi review.
4. Chạy toàn bộ test trên bản mới (CI matrix hai bản PHP trong thời gian chuyển).

Một job CI gộp đủ các bước:

```yaml
# .github/workflows/quality.yml
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: shivammathur/setup-php@v2
        with: { php-version: '8.4' }
      - run: composer install --no-interaction --prefer-dist
      - run: composer audit
      - run: vendor/bin/pint --test
      - run: vendor/bin/rector process --dry-run --no-progress-bar
      - run: vendor/bin/phpstan analyse --no-progress --memory-limit=2G
      - run: php artisan test
```

Test: PHPUnit hoặc Pest, cộng các fake của Laravel (`Queue::fake()`, `Http::fake()`,
`Notification::fake()`...). Chiến lược chi tiết ở [20-testing-quality.md](../20-testing-quality.md).

⚠️ Test phải trỏ **DB riêng**. Trait `RefreshDatabase`, ở test đầu tiên của lần chạy, gọi
`migrate:fresh` (xoá **mọi bảng** rồi chạy lại migration), sau đó bọc từng test trong một transaction
và rollback. Nếu `DB_DATABASE` lúc chạy test vẫn là DB dev (hoặc tệ hơn, DB staging trong `.env`) thì
dữ liệu đó mất sạch. Cách chặn:

```xml
<!-- phpunit.xml -->
<php>
    <env name="APP_ENV" value="testing"/>
    <env name="DB_CONNECTION" value="mysql"/>
    <env name="DB_DATABASE" value="app_testing"/>
</php>
```

Hoặc để trong `.env.testing`. Thêm lớp bảo vệ ở production:
`DB::prohibitDestructiveCommands($this->app->isProduction())` trong `AppServiceProvider::boot()` chặn
các lệnh như `migrate:fresh`, `db:wipe`.

**Tóm tắt nhanh**
- PHP chỉ kiểm kiểu lúc chạy; PHPStan là compiler thứ hai. Level 0 đến 10, cộng dồn; 8 là nullable, 9
  là mixed rõ, 10 (mới từ 2.0) là cả mixed ngầm.
- Codebase cũ: baseline + CI chặn lỗi mới + sửa dần + nâng level. Không regenerate baseline để giấu lỗi
  mới; bỏ qua tại chỗ bằng `@phpstan-ignore <identifier> (lý do)`.
- Generics qua PHPDoc: `@template`, `list<T>`, `array{...}`, `class-string<T>`. Larastan boot app và
  quét migration; relationship cần `HasMany<Post, $this>`.
- `$request->input()` trả `mixed`; ở level 9 dùng `integer()`, `string()`, `enum()`, thu hẹp kiểu,
  hoặc DTO.
- Rector sửa code, đi từng level nhỏ, CI chạy `--dry-run`; Pint chạy sau Rector, CI dùng `--test`.
- Test phải có DB riêng: `RefreshDatabase` chạy `migrate:fresh`.

**Nguồn**: [PHPStan: Rule Levels](https://phpstan.org/user-guide/rule-levels) ·
[PHPStan: Baseline](https://phpstan.org/user-guide/baseline) ·
[PHPStan: Ignoring Errors](https://phpstan.org/user-guide/ignoring-errors) ·
[PHPStan: PHPDoc Types](https://phpstan.org/writing-php-code/phpdoc-types) ·
[PHPStan blog: Generics in PHP using PHPDocs](https://phpstan.org/blog/generics-in-php-using-phpdocs) ·
[PHPStan UPGRADING 1.x → 2.0](https://github.com/phpstan/phpstan/blob/2.1.x/UPGRADING.md) ·
[Larastan](https://github.com/larastan/larastan) (README, `docs/rules.md`, `docs/features.md`,
`docs/custom-config-parameters.md`) ·
[phpstan-deprecation-rules](https://github.com/phpstan/phpstan-deprecation-rules) ·
[Rector documentation](https://getrector.com/documentation) (Set Lists, Levels, Composer-Based Sets,
Integration To New Project, Run in CI) · [rector-laravel](https://github.com/driftingly/rector-laravel) ·
[Laravel: Pint](https://laravel.com/docs/pint) · [PHP-CS-Fixer](https://cs.symfony.com/) ·
[Psalm](https://psalm.dev/) · mã nguồn laravel/framework 13.x (`Http/Concerns/InteractsWithInput.php`,
`Support/Traits/InteractsWithData.php`, `Foundation/Testing/RefreshDatabase.php`)


---

## Chặng 3: Senior

### 3.1 Bên trong Zend Engine: zval, refcount, copy-on-write

Module này trả lời: một biến PHP thực sự là gì trong bộ nhớ, khi nào gán hay truyền array là "miễn
phí" và khi nào nó copy cả khối dữ liệu, và vì sao PHP 7 trở đi dùng ít RAM hơn PHP 5 đến vài lần
cho cùng một array. Mọi mô tả dưới đây là cho PHP 7 trở lên (nhánh 8.x vẫn cùng thiết kế), trên máy
64-bit.

#### zval: một biến PHP trông thế nào bên trong

PHP viết bằng C. Mọi giá trị PHP (một biến, một phần tử array, một property, một tham số) đều được
biểu diễn bằng struct C tên *zval* ("Zend value"). Định nghĩa thật trong `Zend/zend_types.h` của
PHP 8.4, lược bớt:

```c
struct _zval_struct {
    zend_value value;          /* 8 byte: giá trị hoặc con trỏ */
    union {
        uint32_t type_info;    /* 4 byte: type (1 byte) + type_flags (1 byte) + phần phụ */
        ...
    } u1;
    union {
        uint32_t next;         /* 4 byte "mượn": chuỗi va chạm trong hashtable, */
        uint32_t fe_pos;       /* vị trí foreach, số dòng của AST node, ... */
        ...
    } u2;
};

typedef union _zend_value {
    zend_long    lval;         /* int: nằm thẳng ở đây */
    double       dval;         /* float: nằm thẳng ở đây */
    zend_string *str;          /* còn lại đều là con trỏ */
    zend_array  *arr;
    zend_object *obj;
    zend_resource  *res;
    zend_reference *ref;
    ...
} zend_value;
```

Vẽ ra thành 16 byte:

```
zval (16 byte)
+---------------------------------+-----------------------------+---------------------+
| value (8 byte)                  | u1.type_info (4 byte)       | u2 (4 byte)         |
| lval | dval | con trỏ tới       | type | type_flags | extra   | next / fe_pos /     |
| zend_string/zend_array/...      | (IS_LONG, IS_ARRAY...)      | lineno ... tuỳ chỗ  |
+---------------------------------+-----------------------------+---------------------+
```

- `value` là một *union* (các trường dùng chung một vùng nhớ, tại một thời điểm chỉ một trường có
  nghĩa). `type` cho biết đang dùng trường nào.
- `u2` tồn tại vì một lý do rất thực dụng: 8 byte value cộng 4 byte type đã bị *padding* (căn lề)
  lên 16 byte, nên 4 byte thừa được đem cho engine dùng theo ngữ cảnh. Hashtable dùng nó để nối
  chuỗi va chạm (xem nhóm hashtable bên dưới), coi như "miễn phí".
- Các type chính (PHP 8.4): `IS_UNDEF` (0, biến chưa gán hoặc đã `unset`), `IS_NULL`, `IS_FALSE`,
  `IS_TRUE`, `IS_LONG`, `IS_DOUBLE`, `IS_STRING`, `IS_ARRAY`, `IS_OBJECT`, `IS_RESOURCE`,
  `IS_REFERENCE`. Chú ý `bool` được tách thành hai type `IS_FALSE`/`IS_TRUE`: giá trị nằm luôn
  trong type, value không dùng tới.

Điểm cốt lõi của PHP 7: **zval không tự cấp phát và không tự đếm tham chiếu**. Zval được nhúng
thẳng vào chỗ chứa nó (bucket của array, bảng biến của hàm, bảng property của object). Refcount
được đẩy ra các cấu trúc lớn mà zval trỏ tới.

Các cấu trúc lớn này đều mở đầu bằng cùng một header 8 byte:

```c
typedef struct _zend_refcounted_h {
    uint32_t refcount;                 /* số chỗ đang dùng chung giá trị này */
    union { uint32_t type_info; } u;   /* type, flag (IMMUTABLE, PERSISTENT...), thông tin GC */
} zend_refcounted_h;
```

Trong `type_info` của header có chỗ để cycle collector ghi vị trí của giá trị trong *root buffer*
và "màu" khi đánh dấu (module 3.2).

#### Kiểu nào refcounted, kiểu nào không

*Refcounted* nghĩa là giá trị có refcount và được chia sẻ bằng cách tăng refcount. *Collectable*
nghĩa là giá trị có thể nằm trong một vòng tham chiếu nên cycle collector phải để ý tới nó. Hai
thuộc tính này được ghi thành bit trong `type_flags` của zval (`IS_TYPE_REFCOUNTED`,
`IS_TYPE_COLLECTABLE`), nên engine kiểm tra rất nhanh mà không cần nhìn vào giá trị.

| Kiểu PHP | Nằm ở đâu | Refcounted | Collectable | Ghi chú |
|---|---|---|---|---|
| `null`, `bool`, `int`, `float` | Thẳng trong zval | Không | Không | Copy = copy 16 byte |
| `string` thường | `zend_string` riêng | Có | Không | String không thể chứa gì khác nên không tạo vòng được |
| `string` interned | `zend_string` dùng chung | Không | Không | Cờ `IS_STR_INTERNED` |
| `array` thường | `zend_array` (HashTable) | Có | Có | |
| `array` immutable | `zend_array` trong shared memory của OPcache, hoặc array rỗng hằng | Không | Không | Cờ `IS_ARRAY_IMMUTABLE` |
| `object` | `zend_object` | Có | Có | Không có copy-on-write |
| `resource` | `zend_resource` | Có | Không | |
| reference (`&`) | `zend_reference` | Có | Không (GC nhìn vào giá trị bên trong) | |

Vì string và array lúc refcounted lúc không, engine không thể quyết định chỉ dựa trên type; nó xem
bit `IS_TYPE_REFCOUNTED` trong từng zval. Đó là lý do "immutable" là một khái niệm quan trọng: giá
trị immutable được dùng lại ở bất kỳ đâu mà **không cần tăng/giảm refcount**, và không bao giờ bị
giải phóng giữa request. Có ba nguồn chính: dữ liệu trong shared memory của OPcache (nhiều process
cùng đọc, ghi refcount vào đó là hỏng), array rỗng hằng của engine, và string persistent dùng chung
giữa các thread.

Nhìn tận mắt bằng `debug_zval_dump()`. Hàm này nhận tham số theo giá trị, nên con số refcount luôn
**cộng thêm 1** cho chính tham số của nó. Từ PHP 8.4 nó còn in chữ `packed` cho packed array.

```php
<?php
declare(strict_types=1);

$n = 42;
debug_zval_dump($n);            // int(42)                  không có refcount
$s = 'hello';
debug_zval_dump($s);            // string(5) "hello" interned  literal trong code là interned
$t = str_repeat('ab', 3);
debug_zval_dump($t);            // string(6) "ababab" refcount(2)  $t + tham số của hàm
$a = range(1, 3);
debug_zval_dump($a);            // array(3) packed refcount(2){ ... }   (8.4+ mới in "packed")
$b = $a;
debug_zval_dump($a);            // array(3) packed refcount(3){ ... }   $a, $b, tham số
$o = new stdClass();
debug_zval_dump($o);            // object(stdClass)#1 (0) refcount(2){ }
```

⚠️ Với literal array (`$x = [1, 2, 3];`) con số in ra phụ thuộc OPcache có bật cho CLI hay không
(`opcache.enable_cli` mặc định 0): có OPcache thì literal thành immutable và hiện `interned`, không
có thì refcount có thể cao hơn bạn đoán vì chính opcode cũng đang giữ một bản. Đừng kết luận gì từ
refcount của literal; dùng `range()` hay array tạo lúc chạy khi thí nghiệm. Output trong comment ở
trên suy ra từ mã nguồn `ext/standard/var.c` cho CLI mặc định (OPcache tắt), không phải chạy thật.
Bật OPcache thì optimizer có thể tính sẵn `str_repeat('ab', 3)` lúc compile (tham số là hằng), và
`$t` sẽ hiện `interned`.

#### Refcount và copy-on-write

*Copy-on-write* (COW): gán hoặc truyền một giá trị refcounted không copy dữ liệu, chỉ copy zval 16
byte và tăng refcount. Chỉ khi **ghi** vào một bên mà refcount > 1 thì engine mới copy ra bản riêng
cho bên ghi. Bước đó gọi là *separation* (tách).

Theo dõi một array qua bốn bước:

```php
<?php
declare(strict_types=1);

function f(array $param): void
{
    // (3) lúc vào hàm: $a, $b, $param cùng trỏ zend_array_1, refcount = 3
    $param[] = 4;
    // (4) ghi khi refcount > 1: separation.
    //     $param -> zend_array_2 (bản copy, refcount 1), zend_array_1 về refcount 2
}

$a = range(1, 3);   // (1) zend_array_1, refcount = 1
$b = $a;            // (2) $b trỏ cùng zend_array_1, refcount = 2, không copy gì
f($a);              // sau khi hàm trả về: $param bị huỷ, zend_array_2 về 0 và được giải phóng
var_dump($a === $b, count($a)); // bool(true) int(3)
```

```
(2)  $a ──┐                      (4)  $a ──┐
          ├──> zend_array_1 rc=2           ├──> zend_array_1 rc=2  [1,2,3]
     $b ──┘    [1,2,3]                $b ──┘
                                     $param ──> zend_array_2 rc=1  [1,2,3,4]
```

Với int thì không có gì để chia sẻ: `$b = $a` với `$a = 42` tạo hai zval độc lập, mỗi cái chứa số
42. Đơn giản và rẻ hơn cả tăng refcount.

Hệ quả thực dụng:

- Truyền array lớn vào hàm, trả array lớn ra khỏi hàm, gán cho biến khác: đều gần như miễn phí,
  chừng nào không ai sửa nó.
- `foreach ($arr as $v)` (by value) không copy array; nó giữ thêm một refcount trong lúc duyệt, nên
  sửa `$arr` trong vòng lặp sẽ tách ra bản mới và vòng lặp vẫn duyệt bản cũ.
- Gán array 100 MB cho biến khác, `memory_get_usage()` gần như không đổi. Sửa một phần tử của bản
  kia thì mới trả tiền:

```php
<?php
declare(strict_types=1);

$a = range(1, 1_000_000);
$m1 = memory_get_usage();
$b = $a;                                   // chỉ tăng refcount
echo memory_get_usage() - $m1, "\n";       // 0 hoặc gần 0
$b[] = 1;                                  // ghi: separation, copy cả array
echo memory_get_usage() - $m1, "\n";       // khoảng 16 MiB trên PHP 8.2+ (khoảng 32 MiB trên 7.x/8.1)
```

Con số 16 MiB đến từ nhóm hashtable bên dưới: packed array của PHP 8.2+ tốn 16 byte mỗi phần tử,
dung lượng làm tròn lên luỹ thừa 2 (1.000.000 phần tử thành 2^20 ô). Giá trị chính xác có thể lệch
một chút tuỳ bản build; hãy tự chạy.

⚠️ String cũng COW: `$s2 = $s1` không copy, `$s2 .= 'x'` thì copy (trừ khi refcount là 1, lúc đó
engine có thể nối tại chỗ). Vì vậy nối chuỗi trong vòng lặp vào một biến không ai khác giữ là rẻ.

#### Reference và vì sao `&` thường chậm hơn

Khi viết `$r = &$a`, PHP 7 tạo một `zend_reference` (một zval có refcount, bọc giá trị thật), rồi
cả `$a` và `$r` đều thành zval kiểu `IS_REFERENCE` trỏ tới nó:

```
$a ──┐                                    
     ├──> zend_reference rc=2 { val: zval ──> zend_array rc=1 }
$r ──┘
```

- Mọi lần đọc `$a` giờ phải đi qua thêm một lớp gián tiếp.
- Ghi qua reference không tách, vì mục đích của reference là mọi bên cùng thấy thay đổi. Nhưng
  zend_array bên trong vẫn có refcount riêng: nếu array đó cũng đang được một biến thường chia sẻ,
  ghi qua reference vẫn phải tách array ra.
- PHP 5 tệ hơn nhiều: cờ `is_ref` nằm trên zval, nên một giá trị không thể vừa là reference vừa
  được chia sẻ bởi biến thường. Truyền một biến reference vào hàm nhận by-value (ví dụ `count()`)
  buộc copy toàn bộ array. PHP 7 bỏ được ca này vì array bên trong reference vẫn chia sẻ bình
  thường.

⚠️ "Dùng `&` để tránh copy array lớn" là hiểu sai. Khi hàm chỉ đọc, COW đã không copy rồi; `&`
không tiết kiệm gì mà còn thêm lớp gián tiếp và làm engine bỏ qua một số tối ưu. Chỉ dùng `&` khi
thật sự muốn hàm sửa biến của phía gọi. Cạm bẫy kinh điển còn lại của `&`:

```php
<?php
declare(strict_types=1);

$xs = [1, 2, 3];
foreach ($xs as &$x) { $x *= 2; }
foreach ($xs as $x) { }        // $x vẫn là reference tới $xs[2], mỗi vòng ghi đè $xs[2]
var_dump($xs);                 // [2, 4, 4]  phần tử cuối bị ghi đè
// Sửa: unset($x); ngay sau vòng foreach có &
```

#### zend_string và interned string

String là `zend_string`:

```c
struct _zend_string {
    zend_refcounted_h gc;   /* 8 byte: refcount + flag */
    zend_ulong        h;    /* 8 byte: hash cache, 0 = chưa tính */
    size_t            len;  /* 8 byte: độ dài */
    char              val[1]; /* nội dung nằm liền ngay sau, cộng 1 byte '\0' cuối */
};
```

- Header 24 byte, nội dung nằm liền phía sau trong cùng một lần cấp phát (kỹ thuật "struct hack").
- `len` lưu tường minh nên string PHP chứa được byte `\0` (binary-safe) và `strlen()` là O(1).
- `h` lưu hash của string, tính một lần ở lần đầu dùng làm key array, các lần tra cứu sau dùng lại.
- Nhờ có header refcount riêng, một `zend_string` có thể vừa là giá trị của biến vừa là key trong
  array mà không phải copy. PHP 5 không làm được việc này.

*Interned string* là string được lưu **một bản duy nhất** cho mỗi nội dung, không đếm refcount, và
sống tới hết request (hoặc lâu hơn):

1. Khi compile, mọi literal string, tên biến, tên hàm, tên class, tên property được intern: engine
   tra bảng interned string, có sẵn nội dung đó thì dùng lại, chưa có thì thêm vào.
2. Nhờ vậy key `'status'` xuất hiện ở hàng nghìn array trỏ tới cùng một `zend_string`, và so sánh
   hai interned string có thể dừng ở so sánh con trỏ.
3. Không có OPcache: interned string tạo trong request bị huỷ khi request kết thúc; loại tạo trước
   request (tên hàm có sẵn...) gọi là *permanent* và được giữ lại.
4. Có OPcache: interned string của script nằm trong **shared memory**, dùng chung mọi worker FPM và
   không bao giờ bị huỷ. Vùng này có kích thước `opcache.interned_strings_buffer` (mặc định 8, đơn
   vị MB). Đầy thì string mới không được intern vào đó nữa, mất một phần lợi ích; `opcache_get_status()`
   có mục `interned_strings_usage` để kiểm tra.

String tạo lúc chạy (`str_repeat`, nối chuỗi, dữ liệu đọc từ DB) là string thường, refcounted.

#### Packed array và hash array

Mọi array PHP là một *ordered dictionary*: map key sang value và **nhớ thứ tự chèn**. Cài đặt là
`zend_array` (tên khác: `HashTable`), header 56 byte:

```c
struct _zend_array {
    zend_refcounted_h gc;
    union { uint32_t flags; ... } u;   /* có cờ HASH_FLAG_PACKED */
    uint32_t nTableMask;
    union {
        uint32_t *arHash;    /* hash array (nằm ngay TRƯỚC vùng dữ liệu) */
        Bucket   *arData;    /* hash array: mảng Bucket */
        zval     *arPacked;  /* packed array (8.2+): mảng zval trơn */
    };
    uint32_t nNumUsed;          /* số ô đã dùng, tính cả ô đã unset */
    uint32_t nNumOfElements;    /* số phần tử thật, count() trả số này */
    uint32_t nTableSize;        /* dung lượng, luỹ thừa 2, tối thiểu 8 */
    uint32_t nInternalPointer;
    zend_long nNextFreeElement; /* key int tiếp theo cho $a[] = ... */
    dtor_func_t pDestructor;
};

typedef struct _Bucket {
    zval         val;   /* 16 byte, zval nhúng thẳng */
    zend_ulong   h;     /* hash của key string, hoặc chính key int */
    zend_string *key;   /* NULL nếu key là int */
} Bucket;               /* 32 byte */
```

*Hash array* (dạng tổng quát, dùng khi có key string hoặc key int không tăng dần):

```
                 hash array (uint32, 2 x nTableSize ô)     arData: Bucket theo THỨ TỰ CHÈN
                 +------+------+------+------+             +---------------------------------+
 h | nTableMask->|  -1  |  1   |  -1  |  0   | ...    [0]  | key="id"   h=...  val=int(7)    |
                 +------+--|---+------+--|---+        [1]  | key="name" h=...  val=string    |--+
                           |             +------------>    +---------------------------------+  |
                           +-------------------------> [1] (đầu chuỗi va chạm)                   |
                                                       [2]  | UNDEF (tombstone sau unset)     |  |
                                                            +---------------------------------+  |
                                                val.u2.next: chỉ số bucket tiếp theo trong chuỗi <+
```

Tra `$arr['name']`:

1. Lấy hash của key: đã cache trong `zend_string->h`, chưa có thì tính (thuật toán DJBX33A).
2. Kết hợp hash với `nTableMask` ra một ô trong hash array; ô đó chứa chỉ số bucket đầu tiên của
   chuỗi va chạm (hoặc "rỗng").
3. So bucket đó: cùng `h` và cùng nội dung key thì trả về (interned string thường khớp ngay bằng so
   con trỏ).
4. Không khớp thì theo `val.u2.next` sang bucket kế trong chuỗi, lặp lại tới khi hết chuỗi.

Thứ tự chèn có được "miễn phí" vì bucket được thêm tuần tự vào `arData`. `foreach` chỉ việc đi dọc
`arData` từ 0 tới `nNumUsed`, bỏ qua ô `UNDEF`: một lượt quét bộ nhớ liền nhau, rất hợp CPU cache.

*Packed array* là tối ưu cho "list": key toàn int **tăng dần** (không nhất thiết liền nhau, nhưng
khoảng trống quá lớn sẽ khiến engine chuyển sang hash). Khi đó key chính là vị trí, không cần hash
array. Từ PHP 8.2, packed array còn bỏ luôn `Bucket` và lưu thẳng mảng zval (`arPacked`), vì `h`
luôn bằng vị trí và `key` luôn NULL.

| Loại | Byte cho mỗi phần tử (64-bit, chưa tính dữ liệu mà zval trỏ tới) | Khi nào |
|---|---|---|
| Packed, PHP 8.2+ | 16 (một zval) | `range()`, `$a[] = ...`, `array_values()`, kết quả `json_decode` của JSON array |
| Packed, PHP 7.x/8.1 | 32 (một Bucket) | Như trên |
| Hash, PHP 7.3+ | 40 (32 Bucket + 2 ô hash 4 byte) | Có key string, key int lộn xộn |
| PHP 5.x | khoảng 144 | Mọi array |

Dung lượng luôn là luỹ thừa 2 (tối thiểu 8), đầy thì nhân đôi. Array rỗng `[]` chưa cấp phát gì cả
cho tới lần chèn đầu tiên.

Những thao tác làm packed thành hash (tốn thêm RAM và chậm hơn chút):

```php
<?php
declare(strict_types=1);

$list = [];
for ($i = 0; $i < 3; $i++) { $list[] = $i; }
debug_zval_dump($list);     // array(3) packed refcount(2){ ... }

$list['x'] = 1;             // thêm key string: chuyển sang hash
$rev = [];
$rev[2] = 'c'; $rev[1] = 'b';   // key int giảm dần: không packed được vì phải giữ thứ tự
unset($list[0]);            // unset: để lại tombstone UNDEF, không dời phần tử
```

⚠️ Hai cạm bẫy bộ nhớ đến từ thiết kế này:

- `unset` không thu nhỏ array. Ô bị xoá thành tombstone; khi `nNumUsed` chạm `nTableSize` engine
  mới dồn các tombstone lại, và dung lượng gần như không bao giờ giảm. Array 1 triệu phần tử bị
  `unset` dần tới còn 10 phần tử vẫn giữ vùng nhớ lớn. Muốn thu nhỏ: tạo array mới
  (`$a = array_values($a)` hoặc copy sang biến mới rồi bỏ biến cũ).
- Dùng array làm hàng đợi bằng `array_shift()` là O(n) mỗi lần vì phải đánh lại key 0..n-1. Dùng
  `SplQueue` hoặc giữ chỉ số đầu hàng.

Vì sao PHP 7 dùng ít RAM hơn PHP 5 hẳn: nikic đo `range(1, 100000)` trên 64-bit được 13,97 MiB ở
PHP 5.6 và 4,00 MiB ở PHP 7.0. Các nguồn tiết kiệm:

1. Zval không còn cấp phát riêng từng cái (mỗi lần cấp phát tốn thêm header của allocator), mà
   nhúng thẳng vào bucket.
2. Bucket cũng không cấp phát riêng; cả mảng bucket là một khối liền.
3. Zval nhỏ đi (PHP 5 là 24 byte, cộng thông tin GC thành 32 byte, cộng header cấp phát).
4. PHP 5 dùng hai danh sách liên kết đôi, một giữ thứ tự và một cho chuỗi va chạm (tổng 4 con trỏ
   mỗi phần tử); PHP 7 giữ thứ tự bằng vị trí trong mảng, không tốn gì.
5. Chuỗi va chạm là danh sách liên kết đơn bằng chỉ số 32-bit, cất trong `u2` sẵn có của zval.
6. Int, float, bool không còn refcount và thông tin GC.

Từ PHP 8.2, packed array còn giảm tiếp một nửa (32 xuống 16 byte mỗi phần tử), nên cùng
`range(1, 100000)` theo tính toán chỉ còn khoảng 2 MiB (2^17 ô × 16 byte).

#### Object: handle, không COW

- `zend_object` gồm header refcount, *handle* (số thứ tự trong *object store*, bảng mọi object đang
  sống của request, chính là số `#1` mà `var_dump` in ra và `spl_object_id()` trả về), con trỏ class,
  bảng handler, và **mảng property khai báo nằm liền ngay trong object**.
- Property khai báo trong class được gán chỉ số lúc compile, nên object không cần hashtable riêng
  cho chúng. Một object có 5 property khai báo tốn ít RAM hơn array 5 key tương ứng. Hashtable
  `properties` chỉ được tạo khi cần, ví dụ khi thêm *dynamic property* (deprecated từ 8.2) hoặc khi
  code cần xem object như một bảng property (ví dụ `foreach` trên object, `var_dump`).
- Object không có copy-on-write: `$o2 = $o1` chỉ copy zval (con trỏ tới cùng `zend_object`) và tăng
  refcount, hai biến cùng sửa một object. Muốn bản riêng thì `clone` (copy nông, xem `__clone` ở
  module 1.2).
- ⚠️ `spl_object_id()` được tái dùng sau khi object bị giải phóng, nên dùng nó làm key cache lâu dài
  là sai (module 3.2, `WeakMap`).

#### Hashtable, opcode và VM

- Mỗi hàm sau khi compile thành một *op array*: dãy *opcode* (lệnh của máy ảo, ví dụ `ASSIGN`,
  `ADD`, `INIT_FCALL`, `DO_FCALL`) cùng bảng biến. Biến cục bộ là *CV* (compiled variable), được
  đánh chỉ số sẵn nên truy cập biến không cần tra tên.
- Khi gọi hàm, VM cấp một *call frame* trên VM stack, trong đó các CV là mảng zval liền nhau. Đây
  chính là chỗ "zval nhúng thẳng" thay vì cấp phát riêng.
- *VM executor* chạy lần lượt từng opcode bằng một handler C tương ứng. OPcache lưu op array để
  khỏi compile lại (module 2.3); JIT biến opcode nóng thành mã máy (module 3.3).
- Xem opcode để học:

```sh
# 0x10000: opcode ngay sau compile; 0x20000: opcode sau khi optimizer của OPcache chạy
php -d opcache.enable_cli=1 -d opcache.opt_debug_level=0x20000 script.php
```

  Chỉ để học, không bật trên production.

#### Đối chiếu Java/Go

| | PHP array | PHP object | Java | Go |
|---|---|---|---|---|
| Gán cho biến khác | Chia sẻ, tách khi ghi (COW) | Chia sẻ, không tách | Mọi object: chia sẻ tham chiếu | Struct và array: copy giá trị; slice/map: copy header, dùng chung dữ liệu |
| Giá trị nhỏ | Nằm trong zval 16 byte | | Primitive nằm trên stack/field; `Integer` là object trên heap | Nằm thẳng trong biến |
| Giải phóng | Refcount về 0 là giải phóng ngay | Như array | Tracing GC | Tracing GC |

`List` trong Java giống object của PHP chứ không giống array: gán là hai biến cùng sửa một list.
Muốn ngữ nghĩa "giá trị" như array PHP thì phải copy tay hoặc dùng collection bất biến
(`List.copyOf`). Go gần PHP hơn ở chỗ array `[N]T` được copy khi gán, nhưng copy **ngay**, không
đợi tới lúc ghi; còn slice thì hai biến dùng chung mảng nền, một lỗi rất hay gặp khi `append`.

**Tóm tắt nhanh**
- zval 16 byte = 8 byte value + 4 byte type info + 4 byte phụ (`u2`). Int, float, bool, null nằm
  thẳng trong zval, không refcount. String, array, object, resource, reference nằm riêng, có
  refcount trong header chung.
- Gán/truyền array và string là copy-on-write: chỉ tăng refcount, tách khi ghi mà refcount > 1.
  Object không COW, chỉ chia sẻ. `&` không giúp tránh copy, còn thêm gián tiếp.
- Interned string: một bản cho mỗi literal/tên, không refcount; có OPcache thì nằm trong shared
  memory, giới hạn bởi `opcache.interned_strings_buffer`.
- Array = mảng bucket theo thứ tự chèn + hash array trỏ vào. Packed array (key int tăng dần) bỏ hash
  array; từ 8.2 chỉ tốn 16 byte mỗi phần tử. PHP 5 tốn khoảng 144 byte.
- `unset` để lại tombstone và không thu nhỏ array; `debug_zval_dump()` cho xem refcount (cộng 1 do
  chính tham số của nó).

**Nguồn**: [PHP Internals Book: Basic structure](https://www.phpinternalsbook.com/php7/zvals/basic_structure.html) ·
[PHP Internals Book: Memory management](https://www.phpinternalsbook.com/php7/zvals/memory_management.html) (immutable value) ·
[PHP Internals Book: zend_string](https://www.phpinternalsbook.com/php7/internal_types/strings/zend_strings.html) ·
[nikic: Internal value representation in PHP 7, part 1](https://www.npopov.com/2015/05/05/Internal-value-representation-in-PHP-7-part-1.html) và
[part 2](https://www.npopov.com/2015/06/19/Internal-value-representation-in-PHP-7-part-2.html) ·
[nikic: PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html) ·
[PHP: debug_zval_dump](https://www.php.net/manual/en/function.debug-zval-dump.php) ·
[PHP: OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) (`interned_strings_buffer`, `opt_debug_level`) ·
mã nguồn [`Zend/zend_types.h`](https://github.com/php/php-src/blob/PHP-8.4/Zend/zend_types.h) nhánh PHP-8.4 (zval, `zend_array`, `arPacked`, cờ type) và
`ext/standard/var.c` (output của `debug_zval_dump`)

---

### 3.2 Bộ nhớ và garbage collection

Module này trả lời: PHP giải phóng bộ nhớ lúc nào, vì sao refcount một mình không đủ, cycle
collector tìm rác vòng bằng cách nào và tốn gì, và vì sao một worker sống lâu có thể phình RAM mãi
dù code "không leak". Đây là nền trực tiếp cho module 3.5 (queue worker, Octane).

#### Reference counting là cơ chế chính

Như module 3.1: mỗi giá trị refcounted (string, array, object...) có một bộ đếm. Mỗi lần có thêm
một chỗ dùng (gán, truyền tham số, đưa vào array) thì tăng; mỗi lần bớt (biến ra khỏi scope, bị
gán đè, `unset`) thì giảm. **Về 0 là giải phóng ngay tại chỗ**, không đợi ai:

```php
<?php
declare(strict_types=1);

final class Conn
{
    public function __construct(private string $name) { echo "mở {$this->name}\n"; }
    public function __destruct() { echo "đóng {$this->name}\n"; }
}

function work(): void
{
    $c = new Conn('db');       // refcount 1
    echo "đang làm\n";
}                              // hết hàm: CV $c bị huỷ, refcount 0, __destruct chạy NGAY đây

work();
echo "sau work\n";
// Output:
// mở db
// đang làm
// đóng db
// sau work
```

Hệ quả: destructor của PHP **tất định** (đoán trước được thời điểm), nên pattern "mở ở constructor,
đóng ở destructor" (giống RAII của C++) hoạt động được, miễn là object không nằm trong vòng.

So với *tracing GC* của Java và Go: loại GC này không đếm gì lúc gán. Định kỳ nó đi từ các *root*
(biến trên stack, biến global, static) lần theo mọi con trỏ, đánh dấu những gì còn với tới được, rồi
dọn phần còn lại. Chi phí dồn vào lúc GC chạy thay vì rải đều trên từng phép gán, và thời điểm dọn
không đoán trước được.

#### Vòng tham chiếu

*Vòng tham chiếu* (cycle): một nhóm giá trị trỏ vòng vào nhau. Refcount của mỗi phần tử luôn ≥ 1 vì
phần tử khác trong vòng còn trỏ tới nó, kể cả khi chương trình không còn đường nào với tới cả
nhóm. Refcount một mình không bao giờ dọn được nhóm này.

```php
<?php
declare(strict_types=1);

$a = new stdClass();
$b = new stdClass();
$a->peer = $b;          // b: refcount 2 ($b và $a->peer)
$b->peer = $a;          // a: refcount 2 ($a và $b->peer)
unset($a, $b);          // mỗi cái còn refcount 1: rác, nhưng refcount không về 0
```

```
trước unset:                          sau unset:
$a ──> [obj A rc=2] ──peer──┐         [obj A rc=1] ──peer──┐
        ^                   v            ^                  v
        └──peer── [obj B rc=2] <── $b    └──peer── [obj B rc=1]     (không ai ngoài vòng trỏ vào)
```

Một array chứa chính nó (`$x = []; $x[] = &$x;`) cũng là vòng. Các dạng hay gặp trong code thật:

- Cây có con trỏ ngược: node con giữ `parent`, node cha giữ mảng `children`.
- Quan hệ hai chiều: Eloquent model cha nạp con, con lại `setRelation('parent', $cha)`.
- Closure giữ `$this` (closure khai báo trong method tự bắt `$this`) được gán vào property của chính
  object đó: `$this->handler = function () { ... };`.
- Event dispatcher/observer: object đăng ký listener là closure của chính nó vào một dispatcher mà
  nó cũng giữ.

⚠️ Object nằm trong vòng thì `__destruct` **không** chạy lúc `unset`, mà chạy khi cycle collector
dọn nhóm đó (có thể rất lâu sau, hoặc lúc kết thúc script). Nếu destructor đóng connection hay
xoá file tạm, hành vi sẽ khác hẳn mong đợi.

#### Cycle collector: root buffer và thuật toán đánh dấu

PHP (từ 5.3) có thêm một *cycle collector* chạy song song với refcount, dựa trên thuật toán đồng
bộ trong bài báo "Concurrent Cycle Collection in Reference Counted Systems" (Bacon và Rajan). Ý
tưởng dựa trên hai quan sát:

1. Refcount **tăng** thì giá trị còn đang dùng, không thể là rác. Refcount **giảm về 0** thì đã
   giải phóng xong. Vậy rác vòng chỉ có thể sinh ra ở thời điểm refcount **giảm nhưng chưa về 0**.
2. Trong một vòng rác, nếu trừ đi các tham chiếu *nội bộ* (từ phần tử này sang phần tử kia trong
   vòng) thì refcount của mọi phần tử về 0. Nếu có phần tử còn > 0 sau khi trừ, tức là có ai đó bên
   ngoài vòng đang giữ nó.

Cơ chế cụ thể:

**Bước A, ghi nhận nghi phạm.** Mỗi khi refcount của một array hoặc object giảm mà chưa về 0, giá
trị đó được ghi vào *root buffer* và tô màu *tím* (purple, "có thể là gốc của một vòng"). Mỗi giá
trị chỉ vào buffer một lần; nếu sau đó nó bị giải phóng bình thường thì được gỡ khỏi buffer. Chỉ
array và object vào buffer, vì string, int, resource không thể tạo vòng.

**Bước B, thử trừ (mark grey).** Khi số root chạm ngưỡng, thuật toán duyệt theo chiều sâu từ từng
root, với mỗi giá trị gặp được thì trừ 1 refcount cho mỗi cạnh trỏ tới nó, tô *xám* để không trừ
hai lần.

**Bước C, phân loại (scan).** Duyệt lại từ từng root:
- Giá trị có refcount (sau khi trừ) bằng 0: chỉ được giữ sống bởi chính các cạnh nội bộ, tô
  *trắng* (rác).
- Giá trị có refcount > 0: còn chỗ bên ngoài giữ. Tô *đen* và **cộng trả lại** refcount cho nó và
  mọi thứ nó với tới, vì những thứ đó cũng còn sống.

**Bước D, dọn (collect white).** Đi qua root buffer: gỡ các root, gọi `__destruct` cho object
trắng, rồi giải phóng mọi giá trị trắng. Nếu một destructor "hồi sinh" object (gán nó vào đâu đó
còn sống), engine phát hiện và không giải phóng object đó.

Áp vào ví dụ A và B ở trên: sau `unset`, cả hai vào root buffer (refcount giảm 2 xuống 1). Bước B
trừ cạnh A→B và B→A, cả hai về 0. Bước C thấy 0, tô trắng. Bước D gọi destructor và giải phóng cả
hai.

```
Màu:   PURPLE  nghi phạm trong root buffer
       GREY    đã thử trừ refcount
       WHITE   rác, sẽ giải phóng
       BLACK   còn sống (màu mặc định)
```

Ngưỡng và kích thước buffer. Tài liệu PHP ghi root buffer có "kích thước cố định 10.000 root";
đó là mô tả từ thời PHP 5.3. Từ PHP 7.3 (GC được viết lại), mã nguồn `Zend/zend_gc.c` cho thấy:

| Hằng số | Giá trị | Ý nghĩa |
|---|---|---|
| `GC_THRESHOLD_DEFAULT` | 10.000 (+1 ô dành riêng) | Ngưỡng ban đầu: số root làm GC tự chạy |
| `GC_THRESHOLD_TRIGGER` | 100 | Một lần chạy dọn được ít hơn 100 giá trị thì bị coi là "chạy phí công" |
| `GC_THRESHOLD_STEP` | 10.000 | Mỗi lần phí công, ngưỡng tăng thêm chừng này; chạy hiệu quả thì giảm dần về mặc định |
| `GC_THRESHOLD_MAX` | 1.000.000.000 | Trần của ngưỡng |
| `GC_DEFAULT_BUF_SIZE` | 16.384 | Kích thước buffer ban đầu; buffer tự nới khi cần |

Cơ chế ngưỡng tự điều chỉnh sinh ra vì ca xấu nhất: app giữ hàng trăm nghìn object sống thật (ví
dụ một ORM nạp nhiều entity). Chúng liên tục vào buffer, GC chạy, duyệt hết, không dọn được gì,
lặp lại. Tăng ngưỡng giảm số lần chạy vô ích đó.

⚠️ Chi phí của GC tỉ lệ với **số giá trị với tới được từ các root**, không chỉ số root. Một root trỏ
vào cây object khổng lồ còn sống vẫn làm GC duyệt cả cây. Benchmark trong manual (PHP 5.3) ghi nhận
bật GC chậm hơn khoảng 7% ở một script tạo vòng liên tục, đổi lại bộ nhớ đỉnh giảm từ 931 MB còn 10
MB.

#### gc_collect_cycles, gc_disable, gc_status

| Hàm / ini | Làm gì |
|---|---|
| `zend.enable_gc` (ini, mặc định bật) | Bật/tắt việc GC tự chạy khi chạm ngưỡng |
| `gc_enable()` / `gc_disable()` / `gc_enabled()` | Như ini nhưng lúc chạy |
| `gc_collect_cycles(): int` | Chạy thu gom ngay, trả về số giá trị đã dọn. Chạy được cả khi GC đang tắt |
| `gc_status(): array` | `runs`, `collected`, `threshold`, `roots`; từ 8.3 thêm `running`, `protected`, `full`, `buffer_size`, `application_time`, `collector_time`, `destructor_time`, `free_time` |
| `gc_mem_caches(): int` | Bảo Zend MM trả các khối nhớ đang cache (không dùng) về OS, trả về số byte |

⚠️ Tắt GC không tắt việc ghi root. Manual cũ nói root vượt buffer thì bị bỏ qua (và gây leak vĩnh
viễn); từ 7.3 mã nguồn cho thấy buffer tự nới thêm, nên tắt GC lâu thì root buffer và các vòng rác
cùng phình ra. Mẫu dùng hợp lý khi có một đoạn cực nhạy độ trễ: `gc_collect_cycles(); gc_disable();`
đoạn nhạy cảm, rồi `gc_enable();`.

Script thí nghiệm (tiêu chí "Nắm chắc khi" đầu tiên): tạo vòng trong vòng lặp, đo có và không có GC.

```php
<?php
declare(strict_types=1);

final class Node
{
    public ?Node $peer = null;
    /** @var list<int> */
    public array $payload = [];
}

function makeGarbageCycles(int $n): void
{
    for ($i = 0; $i < $n; $i++) {
        $a = new Node();
        $b = new Node();
        $a->peer = $b;
        $b->peer = $a;               // vòng a <-> b
        $a->payload = range(1, 50);
    }                                // vòng lặp sau gán đè $a, $b: cặp cũ thành rác vòng
}

$mib = static fn (int $bytes): string => number_format($bytes / 1048576, 1) . ' MiB';

gc_disable();
$base = memory_get_usage();
makeGarbageCycles(20_000);
echo 'GC tắt:  +', $mib(memory_get_usage() - $base), "\n";   // cỡ chục MiB, tăng tuyến tính theo n
echo 'roots:   ', gc_status()['roots'], "\n";                 // cỡ 40.000: mỗi object vào buffer một lần
echo 'dọn:     ', gc_collect_cycles(), "\n";                  // cỡ vài chục nghìn (đếm cả object và array)
echo 'sau dọn: +', $mib(memory_get_usage() - $base), "\n";    // gần 0

gc_enable();
$base = memory_get_usage();
$runsBefore = gc_status()['runs'];
makeGarbageCycles(20_000);
echo 'GC bật:  +', $mib(memory_get_usage() - $base), "\n";   // nhỏ, bị chặn quanh ngưỡng root buffer
echo 'số lần GC tự chạy: ', gc_status()['runs'] - $runsBefore, "\n";
```

Các con số trong comment là ước lượng minh hoạ, không phải output chạy thật; con số cụ thể tuỳ máy
và phiên bản. Điều cần thấy là hình dạng: GC tắt thì bộ nhớ tăng tuyến tính
theo số vòng, GC bật thì bộ nhớ dao động răng cưa quanh một mức cố định.

Trong PHP-FPM gần như không phải quan tâm: hết request, toàn bộ bộ nhớ của request bị huỷ, vòng
hay không cũng vậy. Trong worker sống lâu (`queue:work`, Octane, daemon) thì vòng rác tích qua hàng
nghìn job, và GC chạy vào lúc không đoán trước.

#### Weak reference

*Weak reference* là tham chiếu **không tăng refcount**, nên không giữ object sống. Dùng khi muốn
"nhớ" một object mà không kéo dài đời sống của nó.

- `WeakReference` (7.4): `WeakReference::create($obj)`, rồi `->get()` trả object hoặc `null` nếu
  object đã bị giải phóng.
- `WeakMap` (8.0): map với **key là object**, key yếu. Khi object không còn ai giữ, mục tương ứng tự
  biến mất (và value của mục đó cũng được thả). Khác `SplObjectStorage`, vốn giữ key sống.

Cache kết quả tính theo object:

```php
<?php
declare(strict_types=1);

final class Order
{
    /** @param list<int> $prices */
    public function __construct(public array $prices) {}
}

final class TotalCache
{
    /** @var WeakMap<Order, int> */
    private WeakMap $map;

    public function __construct() { $this->map = new WeakMap(); }

    public function totalOf(Order $o): int
    {
        return $this->map[$o] ??= array_sum($o->prices);
    }

    public function size(): int { return count($this->map); }
}

$cache = new TotalCache();
$order = new Order([100, 250]);
echo $cache->totalOf($order), "\n";   // 350
echo $cache->size(), "\n";            // 1
unset($order);                        // không ai giữ Order nữa
echo $cache->size(), "\n";            // 0  mục tự biến mất
```

⚠️ Vì sao array thường là sai:

- `$cache[spl_object_id($o)] = ...`: mục không bao giờ tự mất nên cache phình mãi trong worker sống
  lâu. Tệ hơn, id được **tái dùng** cho object mới sau khi object cũ bị giải phóng, nên object mới
  đọc nhầm kết quả của object cũ.
- `SplObjectStorage` hay array chứa chính object: cache giữ object sống, không bao giờ được giải
  phóng. Đó chính là leak.
- Một bẫy khác: value trong `WeakMap` trỏ ngược về chính key thì key vẫn bị giữ gián tiếp qua value
  (từ PHP 8.3, GC xử lý được vòng dạng này; ở bản cũ hơn hãy tránh).

#### Đo bộ nhớ

| Hàm | Đo gì |
|---|---|
| `memory_get_usage()` | Byte mà Zend MM đang cấp cho script (làm tròn theo kích thước khối của allocator) |
| `memory_get_usage(true)` | Byte Zend MM đã xin từ OS, kể cả phần đang rảnh. `memory_limit` so với con số này |
| `memory_get_peak_usage()` / `(true)` | Mức cao nhất của hai con số trên; `memory_reset_peak_usage()` (8.2) đặt lại |

*Zend MM* (Zend Memory Manager) là allocator riêng của PHP cho dữ liệu trong request. Nó xin OS theo
*chunk* 2 MiB, chia chunk thành trang 4 KiB, và cấp khối nhỏ (tới 3.072 byte) từ các "ngăn" kích
thước cố định. Khối từ cỡ một chunk trở lên (lớn hơn 2 MiB trừ 4 KiB) được xin thẳng từ OS và trả
ngay khi giải phóng.

⚠️ Những điều hay bị hiểu sai:

- Cả hai con số đều **không phải RSS** (bộ nhớ OS thấy process dùng). Manual ghi rõ bộ nhớ extension
  tự `malloc` và bộ nhớ persistent không được tính, kể cả với `true`. Shared memory của OPcache cũng
  không nằm trong đó.
- Giải phóng giá trị PHP không có nghĩa trả RAM về OS. Zend MM giữ lại chunk đã rảnh để dùng lại, và
  phân mảnh khiến chunk khó rảnh hẳn. Một job ăn 500 MB xong, `memory_get_usage()` về thấp nhưng
  RSS của worker vẫn cao. `gc_mem_caches()` giúp được một phần.
- Vì vậy các cơ chế "khởi động lại định kỳ" rất có giá trị: `pm.max_requests` của FPM,
  `queue:work --max-jobs`, `--max-time`, và `--memory` (mặc định 128). Laravel so `--memory` với
  `memory_get_usage(true)` sau mỗi job, vượt thì worker tự thoát để supervisor khởi động lại.
- PHP 8.5 thêm ini `max_memory_limit` (INI_SYSTEM): trần mà `ini_set('memory_limit', ...)` trong
  code không nâng vượt được.

#### Đối chiếu Java/Go

| | PHP | Java (HotSpot) | Go |
|---|---|---|---|
| Cơ chế | Refcount + cycle collector | Tracing GC chia thế hệ (G1 mặc định, ZGC...) | Tracing GC concurrent mark-sweep, không chia thế hệ |
| Khi nào giải phóng | Ngay khi refcount về 0; vòng thì khi collector chạy | Khi GC chạy | Khi GC chạy |
| Chi phí | Mỗi phép gán tăng/giảm refcount; collector duyệt các root nghi vấn | Pause (ngắn với G1/ZGC), cần chỉnh heap | Tốn CPU chạy song song, pause rất ngắn; chỉnh bằng `GOGC`, `GOMEMLIMIT` |
| Destructor | `__destruct` tất định (trừ khi trong vòng) | Không có; `finalize()` deprecated, dùng try-with-resources | Không có; `runtime.SetFinalizer`/`AddCleanup` không đoán được lúc chạy, dùng `defer` |
| Vòng tham chiếu | Cần collector riêng | Không phải vấn đề | Không phải vấn đề |
| Gây đau khi | Vòng rác tích trong process sống lâu; GC duyệt đồ thị object sống khổng lồ | Heap lớn, nhiều object sống lâu | Tạo rất nhiều object nhỏ trên heap |

Điểm cộng khi phỏng vấn: nói được vì sao PHP vẫn chọn refcount. Mô hình request ngắn hạn của PHP
khiến giải phóng tức thời và destructor tất định có giá trị, còn vòng rác hiếm và bị xoá sạch khi hết
request. Cái giá chỉ lộ ra khi PHP chạy như process sống lâu.

**Tóm tắt nhanh**
- Refcount về 0 là giải phóng ngay, `__destruct` chạy ngay: tất định. Vòng tham chiếu thì refcount
  không bao giờ về 0.
- Cycle collector: array/object bị giảm refcount mà chưa về 0 vào root buffer (tím); chạm ngưỡng
  (mặc định 10.000 root) thì thử trừ cạnh nội bộ (xám), cái nào về 0 là rác (trắng), còn lại khôi
  phục (đen), rồi gọi destructor và giải phóng.
- Từ 7.3 ngưỡng tự tăng 10.000 mỗi khi một lần chạy dọn được dưới 100 giá trị; buffer tự nới.
  `gc_collect_cycles()` chạy ngay, `gc_status()` xem số liệu.
- `WeakMap` cho cache theo object không giữ object sống; key `spl_object_id` vừa leak vừa sai vì id
  bị tái dùng.
- `memory_get_usage()` không phải RSS; Zend MM ít trả RAM về OS, nên worker sống lâu cần
  `--max-jobs`/`--memory`/`pm.max_requests`.

**Nguồn**: [PHP: Garbage Collection](https://www.php.net/manual/en/features.gc.php) ·
[PHP: Reference Counting Basics](https://www.php.net/manual/en/features.gc.refcounting-basics.php) ·
[PHP: Collecting Cycles](https://www.php.net/manual/en/features.gc.collecting-cycles.php) ·
[PHP: Performance Considerations](https://www.php.net/manual/en/features.gc.performance-considerations.php) ·
[PHP: gc_status](https://www.php.net/manual/en/function.gc-status.php) ·
[PHP: memory_get_usage](https://www.php.net/manual/en/function.memory-get-usage.php) ·
[PHP: WeakMap](https://www.php.net/manual/en/class.weakmap.php) ·
[PHP: WeakReference](https://www.php.net/manual/en/class.weakreference.php) ·
[nikic: Internal value representation in PHP 7, part 1](https://www.npopov.com/2015/05/05/Internal-value-representation-in-PHP-7-part-1.html) (root buffer, cycle collector) ·
mã nguồn [`Zend/zend_gc.c`](https://github.com/php/php-src/blob/PHP-8.4/Zend/zend_gc.c) nhánh PHP-8.4 (hằng số ngưỡng, màu, `gc_adjust_threshold`) ·
`laravel/framework` 13.x `Queue/Worker.php` (`memoryExceeded`)


---

### 3.3 OPcache chuyên sâu, preloading, JIT

Module này trả lời: sau khi đã có OPcache (module 2.3), còn những tầng tối ưu nào nữa, mỗi tầng bỏ
được bước nào của việc chạy PHP, và vì sao bật JIT thường không làm app Laravel nhanh lên. Kèm theo
là cái giá vận hành của preloading và JIT khi deploy.

Nhắc lại các bước chạy một file PHP và tầng nào cắt bước nào:

```
source .php ──parse──> AST ──compile──> opcode ──VM thông dịch──> kết quả
               └────── OPcache: làm một lần, lưu opcode vào shared memory ──────┘
                                   Preloading: nạp sẵn class/hàm lúc khởi động,
                                   request không cần autoload/include
                                                     JIT: opcode nóng ──> mã máy,
                                                     bỏ bước VM thông dịch
```

#### OPcache làm thêm những gì

Ngoài cache opcode, OPcache còn:

- *Optimizer*: chạy một chuỗi *pass* tối ưu opcode trước khi lưu, điều khiển bằng bitmask
  `opcache.optimization_level` (mặc định `0x7FFEBFFF`, gần như bật hết). Ví dụ: tính sẵn biểu thức
  hằng (`60 * 60 * 24` thành `86400`), bỏ nhánh không bao giờ chạy, thay biến tạm, và suy luận kiểu
  dạng SSA (*Static Single Assignment*, mỗi biến chỉ được gán một lần trong biểu diễn trung gian).
  Chính thông tin kiểu này là đầu vào của JIT.
- *Interned string* và *immutable array* trong shared memory (module 3.1): literal string và
  literal array của script được dùng chung mọi worker, không đếm refcount.
- *File cache* (`opcache.file_cache=/đường/dẫn`): lưu opcode ra đĩa làm cache cấp hai. Có ích khi
  shared memory bị reset, khi server khởi động lạnh, và cho CLI (mỗi lần chạy CLI là process mới,
  shared memory mất theo). PHP 8.5 thêm `opcache.file_cache_read_only` để dùng file cache dựng sẵn
  trong image container có filesystem chỉ đọc.
- PHP 8.5: OPcache trở thành phần **bắt buộc**, luôn được build vào mọi binary PHP (trước đó hay có
  image Docker quên cài). Vẫn tắt được bằng ini (`opcache.enable=0`).

#### Preloading

*Preloading* (PHP 7.4+, RFC của Dmitry Stogov, lấy cảm hứng từ Class Data Sharing của Java
HotSpot) giải quyết phần "gần như" còn lại của OPcache. Có OPcache rồi, mỗi request vẫn phải: gọi
autoloader, kiểm tra file có đổi không (nếu `validate_timestamps` bật), rồi copy/liên kết class từ
shared memory vào bảng class của request. Preloading làm các việc đó **một lần lúc server khởi
động**.

Cách hoạt động:

1. Khai `opcache.preload` trỏ tới một script PHP. Khi FPM (hoặc mod_php) khởi động, script đó chạy
   một lần.
2. Mọi file mà script `include`/`require` hoặc `opcache_compile_file()` được compile vào shared
   memory; class, interface, trait, hàm trong đó được liên kết sẵn.
3. Từ request đầu tiên, các symbol này có sẵn như class dựng sẵn của PHP (kiểu `stdClass`),
   autoloader không bao giờ được gọi cho chúng.

```ini
; php.ini (FPM)
opcache.enable=1
opcache.preload=/var/www/app/preload.php
opcache.preload_user=www-data   ; chỉ cần khi master FPM chạy bằng root
```

```php
<?php
// preload.php: chạy một lần khi FPM khởi động
declare(strict_types=1);

// opcache_compile_file() KHÔNG gọi autoloader: class cha, interface, trait (kể cả ở vendor/)
// phải được compile hoặc include trong script này, nếu không class con không được preload.

$files = new RegexIterator(
    new RecursiveIteratorIterator(new RecursiveDirectoryIterator(__DIR__ . '/src')),
    '/\.php$/'
);
foreach ($files as $file) {
    opcache_compile_file($file->getPathname());   // compile, không thực thi code của file
}
```

`include` khác `opcache_compile_file()`: `include` **thực thi** file (nên nạp theo đúng thứ tự cha
trước con, và khai báo có điều kiện trong `if` vẫn chạy), còn `opcache_compile_file()` chỉ compile
nên nạp theo thứ tự nào cũng được.

Giới hạn cần biết:

- Chỉ class đã liên kết đầy đủ được (class cha, interface, trait đều có mặt và hằng số đã giải
  được) mới được preload thật. Class không thoả thì không bị fatal, chỉ sinh warning "Can't preload
  unlinked class ..." và không được preload.
- Hằng số global (`define`, `const` ở top-level) **không** được preload.
- Không hỗ trợ Windows. Với CLI thì gần như vô nghĩa vì không có process sống qua nhiều request
  (ngoại lệ: preload thư viện FFI).
- `opcache.preload_user`: manual ghi rõ preload bằng root bị cấm mặc định; directive này để chỉ định
  user chạy preload khi server khởi động bằng root rồi mới hạ quyền. Không chạy bằng root thì không
  cần đặt.

Đánh giá:

- RFC ghi "speed-up" khoảng 30% (ZF1 hello world: 3620 so với 2650 req/s) và 50% (ZF2 test app:
  1300 so với 670 req/s). Đó là app
  "hello world", nơi chi phí nạp class chiếm phần lớn. App thật có query DB thì phần trăm nhỏ hơn
  nhiều.
- Đổi lấy: bộ nhớ nền cao hơn (mọi thứ được preload nằm sẵn trong shared memory dù request có dùng
  hay không) và mất tính linh hoạt khi deploy.
- Symfony sinh sẵn file preload (`config/preload.php` trỏ vào file do container tạo ra). Laravel
  không sinh sẵn file preload; muốn dùng phải tự viết hoặc dùng package cộng đồng.

⚠️ Code đã preload **nằm trong shared memory tới khi process PHP tắt**. Sửa file nguồn không có tác
dụng, và `opcache_reset()` cũng không nạp lại (RFC giải thích: lúc reset có thể process khác đang
dùng, đổi giữa chừng sẽ crash). Deploy code mới phải **khởi động lại PHP-FPM** để master tạo lại
shared memory. Quy trình deploy chỉ "reload" hay chỉ reset OPcache sẽ chạy song song code mới và
class cũ đã preload: bug rất khó lần. Vì vậy preloading chỉ hợp production, không hợp môi trường
dev.

#### JIT: tracing và function

*JIT* (Just-In-Time compiler, PHP 8.0+) là một phần của OPcache. Nó biến opcode thành **mã máy** của
CPU (x86-64, AArch64), lưu mã máy trong một vùng riêng của shared memory OPcache (kích thước
`opcache.jit_buffer_size`), và cho opcode trỏ thẳng tới mã máy đó. Vì nằm trong shared memory, mã
máy đã compile được **dùng chung mọi worker FPM và sống qua các request**.

JIT có lợi ở đâu: VM thông dịch phải, với mỗi opcode, nhảy tới handler C, đọc toán hạng từ bộ nhớ,
kiểm tra kiểu (vì biến PHP có thể là bất cứ gì). Khi JIT biết chắc (hoặc đoán và kiểm tra) một biến
luôn là `int` hay `float`, nó sinh mã máy giữ giá trị trong thanh ghi CPU, bỏ hết các bước trên.
Vòng lặp số học chặt là nơi được lợi nhất.

Hai chế độ:

| | `tracing` | `function` |
|---|---|---|
| Đơn vị compile | *Trace*: một đường chạy thực tế (một vòng lặp, một chuỗi lời gọi) | Nguyên cả hàm |
| Khi nào compile | Khi đếm thấy nóng: vòng lặp chạy `opcache.jit_hot_loop` lần (61 từ 8.5, trước đó 64), hàm được gọi `jit_hot_func` lần (127) | Với `function` (1205, chữ số T = 0): compile mọi hàm ngay khi nạp script |
| Thông tin kiểu | Kiểu **quan sát được lúc chạy**, kèm *guard* kiểm tra | Chỉ kiểu suy luận tĩnh được |
| Mã CRTO tương ứng | 1254 | 1205 |
| Khuyến nghị | Manual: "Recommended for most users" | Ít dùng |

Tracing JIT hoạt động theo các bước:

1. VM chạy bình thường và tăng bộ đếm ở đầu vòng lặp, đầu hàm.
2. Bộ đếm chạm ngưỡng: VM ghi lại một trace, tức đúng dãy opcode vừa chạy cùng kiểu thực tế của
   từng biến.
3. JIT compile trace thành mã máy, chèn *guard* ở những chỗ giả định kiểu ("`$i` là int").
4. Lần sau chạy mã máy. Guard sai (ví dụ `$i` bỗng là float) thì thoát ra VM qua *side exit*.
5. Side exit nào xảy ra nhiều (`jit_hot_side_exit`, mặc định 8) thì được compile thành *side trace*
   riêng.

`opcache.jit` cũng nhận dạng số 4 chữ số *CRTO* (C: tối ưu theo CPU như AVX; R: cấp phát thanh ghi;
T: trigger, khi nào compile; O: mức tối ưu). Chỉ cần nhớ `tracing` = 1254, `function` = 1205.

#### opcache.jit trong PHP 8.4 và JIT dựa trên IR

PHP 8.4 có hai thay đổi riêng rẽ về JIT, hay bị nhập làm một:

*1. JIT mới dựa trên IR framework* (RFC "A new JIT implementation based on IR Framework", Dmitry
Stogov, thông qua tháng 10/2023, có từ 8.4):

- JIT cũ (8.0 đến 8.3) sinh mã máy **trực tiếp** từ opcode bằng DynAsm (công cụ của LuaJIT), với
  backend viết tay riêng cho x86 và cho AArch64 (backend AArch64 thêm từ 8.1).
- JIT mới dựng một *IR* (Intermediate Representation, biểu diễn trung gian dạng đồ thị) rồi để IR
  framework lo tối ưu không phụ thuộc máy, cấp phát thanh ghi, lập lịch lệnh và sinh mã. Một backend
  duy nhất, dễ bảo trì, mở đường cho tối ưu mạnh hơn và kiến trúc CPU mới.
- Số đo trong RFC: mã sinh ra nhanh hơn khoảng 5 đến 10% và nhỏ hơn trên benchmark tổng hợp; **app
  thực tế không thay đổi**. Tốc độ compile của tracing JIT gần như cũ, function JIT compile chậm hơn
  tới 4 lần.
- Không đổi hành vi userland, không thêm ini (chỉ thêm bit debug cho `opcache.jit_debug`).

*2. Đổi giá trị mặc định của ini* (cùng bản 8.4):

| | Trước 8.4 | Từ 8.4 |
|---|---|---|
| `opcache.jit` | `tracing` | `disable` |
| `opcache.jit_buffer_size` | `0` | `64M` |
| Cách bật JIT | Đặt `jit_buffer_size` khác 0 | Đặt `opcache.jit=tracing` (hoặc `function`) |

JIT vẫn **tắt mặc định** ở cả hai thời kỳ; chỉ công tắc là đổi chỗ. ⚠️ Mang cấu hình cũ (chỉ có
`opcache.jit_buffer_size=128M`) lên 8.4 thì JIT vẫn tắt mà không có cảnh báo gì. Thêm nữa, từ 8.4
nếu JIT được bật mà khởi tạo thất bại thì PHP dừng với fatal error lúc khởi động thay vì âm thầm
chạy tiếp.

```ini
; PHP 8.4+ (FPM)
opcache.enable=1
opcache.jit=tracing
opcache.jit_buffer_size=64M
```

Các giá trị của `opcache.jit`: `disable` (tắt hẳn, không bật lại lúc chạy được), `off` (tắt nhưng
bật lại được lúc chạy), `tracing`/`on`, `function`. `opcache.jit_buffer_size` là INI_SYSTEM, chỉ đặt
được trong php.ini.

Kiểm tra JIT có thật sự chạy:

```sh
php -d opcache.enable_cli=1 -d opcache.jit=tracing \
    -r 'var_dump(opcache_get_status()["jit"]["on"] ?? null);'
# bool(true) nếu JIT đang chạy. Trong FPM thì gọi opcache_get_status() từ một trang nội bộ,
# xem thêm buffer_size và buffer_free để biết buffer có bị đầy không.
```

⚠️ Extension ghi đè `zend_execute_ex` (điển hình là Xdebug, một số profiler) làm JIT tự tắt kèm
cảnh báo lúc khởi động. Đo hiệu năng JIT với Xdebug đang bật là đo sai.

#### Khi nào JIT có lợi và cách đo

Số liệu từ chính RFC JIT (2019), rất đáng nhớ để trả lời phỏng vấn:

| Workload | Kết quả |
|---|---|
| Mandelbrot (vòng lặp số thực thuần) | Nhanh hơn hơn 4 lần (0,011 s so với 0,046 s) |
| PHP-Parser | Nhanh hơn khoảng 1,3 lần |
| amphp hello world | Nhanh hơn khoảng 5% |
| WordPress | 326 req/s so với 315 req/s, gần như không đổi |

Giải thích:

- JIT chỉ tăng tốc phần **thời gian CPU chạy code PHP**. Workload *CPU-bound* (thời gian chủ yếu là
  tính toán: xử lý ảnh bằng PHP thuần, parser, thuật toán nặng, mô phỏng) được lợi rõ.
- Web app thường *I/O-bound*: một request 80 ms có thể chỉ 10 ms là CPU chạy PHP, phần còn lại là
  chờ MySQL, Redis, HTTP. JIT làm 10 ms đó nhanh gấp đôi thì request vẫn 75 ms.
- Trong 10 ms CPU đó, phần lớn lại nằm trong hàm C có sẵn (`array_*`, PDO, `json_encode`,
  `preg_*`), vốn đã là mã máy, JIT không làm gì thêm được. Code framework nhiều lời gọi, nhiều kiểu
  hỗn hợp cũng khó cho JIT.

Câu trả lời senior: "Đo trước khi bật; nút thắt thường là query chứ không phải CPU." Cách đo:

1. Xác định request có CPU-bound không: profiler (Blackfire, Tideways, SPX, xem module 3.6) cho thấy
   tỉ lệ thời gian CPU so với thời gian chờ I/O.
2. Chạy benchmark cùng tải (`wrk`, `k6`, `ab`) trên cùng máy, cùng dữ liệu, hai cấu hình: JIT tắt và
   `tracing`. Warm-up trước để OPcache và JIT đã compile xong.
3. So p50/p95/p99 (độ trễ mà 50%, 95%, 99% request nằm dưới) và CPU của máy, không chỉ req/s.
4. Theo dõi `buffer_free` của JIT: buffer đầy thì code nóng mới không được compile.

Rủi ro khi bật: JIT là tầng phức tạp, có lịch sử bug riêng (kết quả sai, crash) khó debug hơn nhiều so
với VM. Nếu không đo được lợi ích rõ thì không có lý do mang rủi ro đó lên production.

#### Đối chiếu Java

- JVM HotSpot cũng thông dịch trước, đếm độ nóng rồi compile (JIT phân tầng C1 rồi C2), và cần
  *warm-up*: code phải chạy nhiều lần trong một process sống lâu mới đạt tốc độ đỉnh. JIT là lý do
  chính Java nhanh; bỏ JIT đi Java chậm hơn rất nhiều.
- PHP khác ở hai điểm. Thứ nhất, không có JIT thì PHP vẫn đã nhanh nhờ OPcache và VM tối ưu, nên
  biên lợi ích của JIT nhỏ hơn. Thứ hai, trong PHP-FPM mã máy JIT nằm trong shared memory nên cũng
  "ấm dần" qua các request, nhưng **trạng thái userland** (container Laravel, config, route) thì dựng
  lại mỗi request. Chi phí boot framework mỗi request là thứ JIT không xoá được; cái xoá được nó là
  process sống lâu như Octane (module 3.5), và Octane cũng mang theo đúng các rủi ro bộ nhớ ở module
  3.2.
- Preloading của PHP tương tự Class Data Sharing (CDS/AppCDS) của Java: đổi thời gian nạp class lúc
  chạy lấy một bản dựng sẵn lúc khởi động.

**Tóm tắt nhanh**
- OPcache bỏ parse và compile; preloading bỏ autoload và liên kết class mỗi request; JIT bỏ bước VM
  thông dịch cho code nóng. Ba tầng độc lập, lợi ích giảm dần với app I/O-bound.
- Preloading (7.4+): chạy script một lần lúc FPM khởi động; không preload hằng số global; sửa code
  phải restart FPM, `opcache_reset()` không đủ. `preload_user` chỉ cần khi chạy bằng root.
- JIT `tracing` (khuyến nghị) compile đường chạy nóng theo kiểu quan sát được, có guard và side exit;
  `function` compile cả hàm. Mã máy nằm trong shared memory, dùng chung các worker.
- PHP 8.4: JIT viết lại trên IR framework (mã nhanh hơn 5 đến 10% trên benchmark, app thật không
  đổi), và công tắc đổi: phải đặt `opcache.jit=tracing`, `jit_buffer_size` mặc định đã là 64M.
- JIT giúp code CPU-bound (Mandelbrot hơn 4 lần), gần như không giúp WordPress/Laravel. Đo bằng
  profiler và benchmark p95 trước khi bật; Xdebug làm JIT tự tắt.

**Nguồn**: [PHP: Preloading](https://www.php.net/manual/en/opcache.preloading.php) ·
[PHP: OPcache runtime configuration](https://www.php.net/manual/en/opcache.configuration.php) (`opcache.jit`, CRTO, `jit_buffer_size`, `jit_hot_*`, `preload`, `preload_user`, `file_cache`, `optimization_level`) ·
[RFC: Preloading](https://wiki.php.net/rfc/preload) ·
[RFC: JIT](https://wiki.php.net/rfc/jit) (phần Performance) ·
[RFC: New JIT implementation based on IR framework](https://wiki.php.net/rfc/jit-ir) ·
[PHP.Watch: PHP 8.4 JIT INI changes](https://php.watch/versions/8.4/opcache-jit-ini-default-changes) ·
[Tideways: What's new in PHP 8.5 for performance, debugging and operations](https://tideways.com/profiler/blog/whats-new-in-php-8-5-in-terms-of-performance-debugging-and-operations) (OPcache bắt buộc, `file_cache_read_only`, `max_memory_limit`)


---

### 3.4 PHP-FPM ở mức vận hành

Module này trả lời: khi FPM gặp sự cố trên production (502/504 lúc cao điểm, worker bị giết giữa
chừng, pod OOM, deploy làm rớt request), bạn nhìn vào đâu, đọc con số nào, và sửa theo thứ tự nào.
Module 2.2 là cấu hình; module này là chẩn đoán và vận hành.

#### Lifecycle ở mức engine

Bên dưới code PHP của bạn, engine có một vòng đời riêng cho *extension* (thư viện C nạp vào PHP như
PDO, OPcache, redis, Xdebug). Theo PHP Internals Book, mỗi extension có thể đăng ký các *hook* (hàm
được engine gọi ở những thời điểm cố định):

```
Master FPM khởi động
 └─ MINIT      (module init)     1 lần, ở master trước khi fork. Cấp phát "persistent" (pemalloc), đăng ký ini
    fork ra các worker (kế thừa kết quả MINIT); trong mỗi worker:
     ├─ RINIT      request 1      cấp phát theo request (emalloc, qua Zend Memory Manager)
     │   script PHP chạy
     ├─ RSHUTDOWN  request 1      giải phóng mọi thứ của request (share-nothing nằm ở đây)
     ├─ RINIT      request 2
     │   ...
     └─ RSHUTDOWN  request N
 └─ MSHUTDOWN  process tắt       giải phóng tài nguyên persistent
```

(Còn có GINIT/GSHUTDOWN cho biến global của extension và một bước post-deactivate, ít gặp khi
phỏng vấn.)

Hai hệ quả vận hành:

1. Userland (code PHP) là share-nothing: bộ nhớ cấp qua Zend Memory Manager bị dọn ở RSHUTDOWN, kể
   cả khi code quên giải phóng. Nhưng extension **giữ được state giữa các request** bằng bộ nhớ
   persistent cấp ở MINIT hoặc trong lúc chạy. Đó là cách OPcache giữ opcode, cách
   `PDO::ATTR_PERSISTENT` giữ connection.
2. Nếu một extension cấp phát persistent trong RINIT mà quên giải phóng, bộ nhớ đó **không bao giờ
   được dọn** và cộng dồn theo số request (Internals Book cảnh báo đúng tình huống này, kết cục là
   OOM). Code PHP thuần không gây ra được kiểu leak này trong FPM; extension thì có. Đây là lý do
   tồn tại của `pm.max_requests`.

#### pm.max_requests và vòng đời worker

- `pm.max_requests = N`: worker tự thoát sau khi phục vụ N request, master fork worker mới thay thế.
  Mặc định **0** (không bao giờ tái sinh). File mẫu `www.conf` có dòng gợi ý `;pm.max_requests = 500`
  nhưng bị comment, nên đừng nhầm 500 là mặc định.
- Dùng khi: RSS của worker tăng dần theo thời gian (leak ở extension, thư viện C như ImageMagick,
  hoặc allocator giữ lại vùng nhớ đã dùng). Giá trị thường thấy: vài trăm tới vài nghìn.
- Cái giá: mỗi lần tái sinh là một lần fork và cache cục bộ của worker (ví dụ realpath cache) phải
  làm nóng lại. Rất nhỏ so với rủi ro OOM.
- ⚠️ Với `pm = static` và mọi worker khởi động cùng lúc, chúng cũng chạm N request gần cùng lúc.
  Thường không sao vì tái sinh rất nhanh, nhưng nếu thấy latency nhảy theo chu kỳ thì đây là nghi
  phạm.

#### Đọc status page theo thời gian

Bật trong pool: `pm.status_path = /fpm-status` (và `ping.path = /ping` cho health check). Theo
php.net, trang này lộ URL request và thông tin tài nguyên, nên **chỉ cho IP nội bộ truy cập**. Thêm
`?json`, `?xml`, `?html`, `?openmetrics` (từ PHP 8.1, dùng thẳng cho Prometheus) để đổi định dạng,
`?full` để xem từng worker. Ví dụ output (minh hoạ, phỏng theo ví dụ trong `www.conf.in`; cột bên
phải là chú thích):

```
pool:                 www
process manager:      static
accepted conn:        190460     tổng request đã nhận từ lúc start
listen queue:         0          số request ĐANG chờ worker rảnh (hàng đợi của socket)
max listen queue:     1          đỉnh của listen queue từ lúc start
listen queue len:     511        kích thước hàng đợi tối đa (listen.backlog)
idle processes:       4
active processes:     11
max active processes: 12
max children reached: 0          số lần muốn fork thêm mà đã chạm pm.max_children
slow requests:        0          số request vượt request_slowlog_timeout
```

Cách đọc:

| Tín hiệu (kéo dài, không phải một lần) | Nghĩa |
|---|---|
| `listen queue` > 0 | Request đang xếp hàng, mọi worker đều bận |
| `active` ≈ tổng, `idle` ≈ 0 | Pool bão hoà |
| `max children reached` tăng | Master đã nhiều lần muốn fork thêm mà không được |
| `slow requests` tăng | Có request chạy lâu, xem slow log |
| `listen queue` chạm `listen queue len` | Hàng đợi đầy, kernel từ chối connection mới, Nginx trả 502 |

- ⚠️ `max children reached` **chỉ hoạt động với `pm = dynamic` và `ondemand`** (ghi rõ trong
  `www.conf.in`). Với `pm = static` nó luôn là 0 dù pool đã bão hoà. Pod chạy `static` phải nhìn
  `listen queue` và `active processes`.
- Mọi số đều là của pool và bị reset khi FPM restart. Đưa vào dashboard, nhìn theo thời gian.
- `?full` cho từng worker: `state` (Idle/Running), `request duration` (**micro giây**, của request
  đang chạy nếu worker Running, của request vừa xong nếu Idle), `request URI`, `last request memory`.
  Lúc sự cố, lọc worker `Running` có `request duration` lớn để biết worker đang kẹt ở URI nào.
- ⚠️ Khi pool bão hoà, chính request tới status page cũng phải xếp hàng. `pm.status_listen` (từ PHP
  8.0) tạo một pool ẩn nghe ở địa chỉ riêng, nên vẫn đọc được status lúc pool chính kẹt.

```sh
# Đọc status trực tiếp qua FastCGI, không cần đi qua Nginx (cgi-fcgi trong gói libfcgi)
SCRIPT_NAME=/fpm-status SCRIPT_FILENAME=/fpm-status QUERY_STRING=full REQUEST_METHOD=GET \
  cgi-fcgi -bind -connect /run/php/php-fpm.sock
```

#### Slow log

```ini
; trong pool
slowlog = /var/log/php-fpm/$pool.slow.log
request_slowlog_timeout = 5s          ; 0 = tắt (mặc định)
request_slowlog_trace_depth = 20      ; mặc định 20
```

Khi một request chạy quá 5 giây, master **tạm dừng worker** bằng `ptrace`, đọc call stack của engine,
ghi vào file rồi cho worker chạy tiếp. Worker không bị giết. Một bản ghi trông như sau (stack đọc từ
trên xuống là từ hàm trong cùng ra ngoài; bản ghi minh hoạ, không phải log chạy thật):

```
[27-Sep-2026 10:15:02] [pool www] pid 4182
script_filename = /var/www/app/public/index.php
[0x00007f3a1c2150a0] curl_exec() /var/www/app/vendor/guzzlehttp/guzzle/src/Handler/CurlHandler.php:44
[0x00007f3a1c214f80] __invoke() /var/www/app/vendor/guzzlehttp/guzzle/src/Handler/Proxy.php:28
...
[0x00007f3a1c213e10] charge() /var/www/app/app/Services/PaymentGateway.php:87
[0x00007f3a1c213c90] store() /var/www/app/app/Http/Controllers/OrderController.php:41
```

Đọc: dòng đầu cho biết worker đang **ở đâu** lúc hết 5 giây (đang trong `curl_exec`, tức chờ mạng).
Dò xuống tới dòng đầu tiên thuộc `app/` để biết code của mình gọi từ đâu (`PaymentGateway::charge`).
Slow log chỉ in tên hàm, không in tên class. Nếu nhiều bản ghi cùng đứng ở `execute()` (của
`PDOStatement`) thì nút thắt là DB; ở `curl_exec` là API
ngoài; ở `session_start` hoặc `flock` là lock.

- ⚠️ Trong container, `ptrace` cần capability `SYS_PTRACE`. Thiếu nó, slow log chỉ có dòng lỗi kiểu
  "failed to ptrace(ATTACH) child 4182: Operation not permitted (1)". Docker: `cap_add: [SYS_PTRACE]`;
  Kubernetes: `securityContext.capabilities.add`.
- Slow log chỉ chụp một khoảnh khắc. Nó trả lời "đang chờ cái gì", không trả lời "tốn thời gian ở
  đâu trong cả request". Câu sau cần profiler (module 3.6).

#### request_terminate_timeout: cái kéo cuối cùng

- FPM **giết worker** (gửi SIGTERM) khi một request chạy quá N giây thời gian thực. Mặc định
  0 (tắt). php.net mô tả nó là biện pháp khi `max_execution_time` "vì lý do nào đó" không dừng được
  script, đúng với trường hợp chờ I/O (module 2.2).
- Log FPM khi xảy ra (minh hoạ, định dạng theo mã nguồn FPM):
  ```
  WARNING: [pool www] child 4182, script '/var/www/app/public/index.php' (request: "POST /index.php") execution timed out (30.004163 sec), terminating
  WARNING: [pool www] child 4182 exited on signal 15 (SIGTERM) after 812.301722 seconds from start
  ```
  Nginx thấy upstream đóng kết nối và trả **502** (không phải 504).
- ⚠️ Worker bị giết từ bên ngoài nên **không có gì chạy tiếp**: không `finally`, không exception
  handler, không log của Laravel, không `register_shutdown_function`. Transaction dở dang được MySQL
  tự rollback khi connection đóng, nhưng side effect bên ngoài (API đã gọi, file đã ghi) thì không.
  Vì vậy đây là lưới an toàn cuối, không phải cơ chế timeout chính.
- `request_terminate_timeout_track_finished` (mặc định `no`): mặc định timeout **không áp dụng** sau
  khi code gọi `fastcgi_finish_request()` hoặc khi đang chạy shutdown function. Code "trả response
  sớm rồi làm tiếp việc nặng" có thể chạy vô hạn nếu không bật cái này.

#### Chuỗi timeout

Mỗi tầng có đồng hồ riêng. Tầng **trong cùng phải hết giờ trước**:

```
Client → Load balancer → Nginx ─FastCGI→ FPM worker → Code PHP → HTTP client / DB
 LB idle timeout      fastcgi_read_timeout   request_terminate_timeout   timeout của Guzzle/PDO
     (ví dụ 60s)   >      (ví dụ 55s)      >        (ví dụ 50s)       >   (ví dụ 5-10s)
```

Vì sao thứ tự quan trọng:

1. Tầng trong cùng (HTTP client, timeout của query) hết giờ trước: code PHP nhận exception, log được,
   trả response có nghĩa (503 kèm thông báo), worker rảnh ngay.
2. Nếu `request_terminate_timeout` hết trước timeout của HTTP client: worker bị giết, mất log, Nginx
   trả 502.
3. Nếu LB hoặc Nginx hết giờ trước FPM: client nhận 504, nhưng **worker vẫn chạy tiếp** và vẫn chiếm
   chỗ. Client (hoặc người dùng bấm F5) retry, gửi thêm request vào một pool đã đầy. Đây là vòng xoáy
   làm sự cố nhỏ thành sập.

Giá trị mặc định cần nhớ: Nginx `fastcgi_read_timeout` 60s; AWS ALB idle timeout 60s; Guzzle mặc định
**không có timeout** (`timeout = 0`), Laravel `Http` client mặc định 30s. Kiểm tra từng tầng trong hệ
thống thật, đừng giả định.

#### Chẩn đoán 502/504 lúc cao điểm khi CPU không cao

Tình huống kinh điển: 20h tối, Nginx trả 502/504 hàng loạt, CPU server web chỉ 30%.

1. **Xác nhận pool bão hoà**: status page có `listen queue` > 0, `idle processes` ≈ 0. Log FPM có
   "server reached pm.max_children setting" (dynamic) hoặc "server reached max_children setting"
   (ondemand); `static` không có dòng này.
2. **CPU thấp mà hết worker** nghĩa là worker không bận tính toán mà đang **chờ**: DB chậm, API ngoài
   treo, lock (session file, `SELECT ... FOR UPDATE`), Redis đầy connection.
3. **Tìm chúng chờ gì**: slow log (dòng đầu của stack), `?full` của status page (URI nào đang
   Running lâu), APM. Đối chiếu với phía downstream: slow query log của MySQL, `SHOW PROCESSLIST`
   (module 2.3 của [03-database-sql.md](03-database-sql.md)).
4. **Sửa nguyên nhân theo thứ tự ưu tiên**:
   - Thêm timeout ngắn cho HTTP client, circuit breaker cho API ngoài hay treo.
   - Sửa query chậm, thêm index, bỏ N+1.
   - Đưa việc chậm vào queue (gửi email, gọi đối tác, sinh PDF).
   - Tách pool cho endpoint chậm để nó không ăn hết worker của phần còn lại.
5. **Chỉ tăng `pm.max_children`** khi còn RAM **và** downstream chịu được thêm connection. Tăng worker
   khi DB đang là nút thắt chỉ dồn thêm query vào DB, làm nó chậm hơn nữa.

Cách nhận biết 502 và 504: 502 thường là Nginx không nói chuyện được với FPM (hàng đợi socket đầy,
worker bị giết, FPM chết); 504 là Nginx đã gửi request nhưng chờ quá `fastcgi_read_timeout`. Error log
của Nginx ghi rõ: "connect() to unix:/run/php/php-fpm.sock failed (11: Resource temporarily
unavailable)" là hàng đợi đầy; "upstream timed out" là 504.

#### Signal: điều khiển master

Master FPM phản ứng với các signal sau (theo man page `php-fpm.8`):

| Signal | Hành vi |
|---|---|
| `SIGINT`, `SIGTERM` | Dừng **ngay** (immediate termination). Request đang chạy bị cắt |
| `SIGQUIT` | Dừng **êm** (graceful stop): worker làm xong request hiện tại rồi thoát |
| `SIGUSR1` | Mở lại file log (dùng sau logrotate) |
| `SIGUSR2` | Reload êm: đọc lại cấu hình, thay toàn bộ worker |

Bên dưới, khi reload hoặc dừng êm, master gửi `SIGQUIT` cho các worker, chờ
`process_control_timeout` giây, nếu còn worker thì gửi `SIGTERM`, một giây sau còn nữa thì `SIGKILL`
(mã nguồn `fpm_process_ctl.c`). ⚠️ `process_control_timeout` mặc định **0**, tức gần như leo thang
ngay; đặt bằng thời gian request dài nhất bạn chấp nhận chờ (ví dụ `10s`) trong `php-fpm.conf`.

```sh
kill -USR2 $(cat /run/php/php-fpm.pid)   # reload êm, tương đương systemctl reload php8.4-fpm
kill -QUIT $(cat /run/php/php-fpm.pid)   # dừng êm
```

⚠️ Bẫy container: Kubernetes và Docker dừng container bằng `SIGTERM` theo mặc định, mà `SIGTERM` với
FPM là **dừng ngay**. Image `php:*-fpm` chính thức khai báo `STOPSIGNAL SIGQUIT` để sửa đúng chuyện
này; image tự build từ base khác phải tự khai. Thêm hai điểm khi deploy lên K8s:

- `terminationGracePeriodSeconds` (mặc định 30s) phải lớn hơn `process_control_timeout`, nếu không
  kubelet `SIGKILL` trước khi FPM xong.
- Thêm `preStop` chờ vài giây (`sleep 5`) để endpoint của pod bị gỡ khỏi Service trước khi FPM ngừng
  nhận request, tránh 502 trong lúc rolling update.

Đối chiếu: queue worker của Laravel cũng coi `SIGQUIT`/`SIGTERM` là "làm xong job rồi thoát", nhưng
`SIGUSR2` với queue worker lại là **tạm dừng** chứ không phải reload (module 3.5). Cùng tên signal,
nghĩa do từng chương trình tự định.

#### Tính cỡ pool theo PSS

Module 2.2 dùng RSS để chia RAM. Ở mức vận hành, RSS **đếm trùng** bộ nhớ dùng chung:

- *RSS* (Resident Set Size): mọi trang RAM process đang chạm tới, kể cả trang dùng chung với process
  khác.
- Worker FPM dùng chung rất nhiều: vùng shared memory của OPcache (`opcache.memory_consumption`, mặc
  định 128 MB), code của binary PHP và extension, các trang kế thừa từ master lúc fork (copy-on-write,
  chỉ tách riêng khi bị ghi).
- *PSS* (Proportional Set Size): trang riêng tính đủ, trang dùng chung bởi N process thì mỗi process
  tính 1/N. Tổng PSS của mọi worker ≈ RAM thật cả pool đang dùng.
- *USS* (Unique Set Size): chỉ phần riêng. Đây là phần tăng thêm khi bạn thêm một worker.

Ví dụ: 50 worker, mỗi worker RSS 90 MB, trong đó 60 MB là OPcache và code dùng chung. Cộng RSS ra
4,5 GB; thật ra chỉ khoảng 50 × 30 MB + 60 MB ≈ 1,6 GB. Chia RAM theo RSS làm bạn đặt
`pm.max_children` thấp hơn cần thiết gần 3 lần.

```sh
# PSS và RSS của từng worker (Linux 4.14+ có smaps_rollup)
for pid in $(pgrep -f 'php-fpm: pool www'); do
  awk -v p="$pid" '/^Rss:/ {r=$2} /^Pss:/ {s=$2} END {printf "%s rss=%dMB pss=%dMB\n", p, r/1024, s/1024}' \
    "/proc/$pid/smaps_rollup"
done
# Hoặc: smem -k -P 'php-fpm'   (có cột USS, PSS, RSS)
```

Công thức thực dụng:

```
pm.max_children ≈ (RAM dành cho PHP − phần dùng chung đếm 1 lần) / USS trung bình lúc tải cao
                  rồi trừ biên 10-20% cho request đột biến (upload, export)
```

- Đo **lúc tải thật** và sau khi worker đã chạy một lúc; worker mới fork có USS rất nhỏ vì chưa ghi
  vào trang nào.
- ⚠️ Trong container, cgroup tính mỗi trang **một lần** cho cả container, nên `memory.current` gần với
  tổng PSS (cộng page cache). Vượt memory limit thì OOM killer của cgroup giết một process trong pod,
  thường là worker lớn nhất; Nginx thấy worker chết và trả 502.
- ⚠️ Một request có thể dùng tới `memory_limit`. Nếu vài request export cùng lúc chạm trần, USS trung
  bình không còn đúng. Tách endpoint nặng ra pool riêng có `memory_limit` và `max_children` riêng.

#### Tách pool và chạy trên container

- Nhiều pool trên một máy, mỗi pool một socket, một `pm.max_children`, có thể `request_terminate_timeout`
  riêng và `memory_limit` riêng (qua `php_admin_value[...]`):
  ```ini
  [api]
  listen = /run/php/api.sock
  pm = static
  pm.max_children = 40
  request_terminate_timeout = 15s

  [admin]
  listen = /run/php/admin.sock
  pm = ondemand
  pm.max_children = 5
  request_terminate_timeout = 300s
  php_admin_value[memory_limit] = 512M
  ```
  Nginx định tuyến `/admin` sang `admin.sock`. Báo cáo admin chậm không bao giờ ăn worker của API.
- Kubernetes:
  - Mỗi pod một pool `pm = static`: số worker cố định, bộ nhớ dự đoán được, scale bằng **số pod**
    thay vì số worker. Latency đều vì không fork lúc có tải.
  - `pm.max_children` tính từ memory limit của pod theo công thức PSS ở trên; `requests.memory` đặt
    gần mức dùng thật để scheduler xếp pod đúng.
  - Nginx chạy sidecar cùng pod, nói chuyện với FPM qua unix socket trong `emptyDir` hoặc TCP
    `127.0.0.1:9000`.
  - Readiness probe gọi `ping.path` qua FastCGI, không gọi một route Laravel nặng.
  - ⚠️ Autoscale thêm pod là nhân thêm connection DB: 30 pod × 20 worker = 600 connection tiềm năng.
    Giới hạn `maxReplicas` theo `max_connections` của MySQL, hoặc đặt ProxySQL ở giữa.
- *Persistent connection* (`PDO::ATTR_PERSISTENT`): mỗi worker giữ connection qua nhiều request, kể cả
  lúc rảnh, và rủi ro rò trạng thái (transaction chưa commit, biến session) sang request sau. Chi tiết
  ở module 2.7 của [03-database-sql.md](03-database-sql.md).

**Tóm tắt nhanh**

- Status page nhìn theo thời gian: `listen queue` > 0 kéo dài là thiếu worker hoặc worker đang chờ
  downstream. `max children reached` luôn 0 với `pm = static`.
- CPU thấp mà hết worker thì worker đang chờ I/O: đọc slow log (dòng đầu stack) trước, tăng worker
  sau cùng và chỉ khi downstream chịu nổi.
- Chuỗi timeout: HTTP client < `request_terminate_timeout` < `fastcgi_read_timeout` < LB. Worker bị
  `request_terminate_timeout` giết thì không có `finally`, không log.
- `SIGQUIT` là dừng êm, `SIGTERM` là dừng ngay, `SIGUSR2` là reload; container phải dừng FPM bằng
  `SIGQUIT` và `process_control_timeout` phải khác 0.
- Tính `pm.max_children` theo PSS/USS, không theo RSS (RSS đếm trùng OPcache và trang copy-on-write).

**Nguồn**: [PHP Internals Book: PHP lifecycle](https://www.phpinternalsbook.com/php7/extensions_design/php_lifecycle.html) · [PHP: FPM Status Page](https://www.php.net/manual/en/fpm.status.php) · [PHP: FPM Configuration](https://www.php.net/manual/en/install.fpm.configuration.php) · [php-src: www.conf.in](https://github.com/php/php-src/blob/master/sapi/fpm/www.conf.in) · [php-src: php-fpm.8.in (signals)](https://github.com/php/php-src/blob/master/sapi/fpm/php-fpm.8.in) · [php-src: fpm_process_ctl.c](https://github.com/php/php-src/blob/master/sapi/fpm/fpm/fpm_process_ctl.c) · [docker-library/php Dockerfile](https://github.com/docker-library/php) · [PHP: Persistent Connections](https://www.php.net/manual/en/features.persistent-connections.php)

---

### 3.5 Process sống lâu: queue worker, Octane, daemon

Module này trả lời: khi một process PHP boot app một lần rồi xử lý hàng nghìn job hoặc request, cái gì
thay đổi so với FPM, vì sao RAM tăng tới OOM và dữ liệu của user A lọt sang user B, và Laravel đã
làm sẵn những gì (cũng như không làm gì) để đỡ cho bạn.

#### Mất lợi thế share-nothing

*Process sống lâu* (long-running process) là process boot framework một lần rồi xử lý nhiều đơn vị
việc: `queue:work`, Horizon, Octane, consumer Kafka/RabbitMQ, daemon tự viết bằng vòng `while (true)`.

```
FPM (share-nothing)                          Process sống lâu
request 1: boot → xử lý → RSHUTDOWN dọn hết  boot 1 lần
request 2: boot → xử lý → dọn hết            ├─ job 1 ─┐
request 3: boot → xử lý → dọn hết            ├─ job 2  │  static, singleton, listener, connection,
                                             ├─ job 3  │  vòng tham chiếu... còn nguyên giữa các lần
                                             └─ ...   ─┘
```

Không còn RSHUTDOWN giữa các job, nên:

- Mọi thứ gắn vào process sống mãi: static property, instance singleton trong container, listener đã
  đăng ký, connection DB/Redis, `ini_set()`, `setlocale()`, `date_default_timezone_set()`.
- Cái gì tích luỹ thì tích luỹ mãi (memory leak). Cái gì thay đổi thì job sau thấy bản đã đổi
  (state leak).
- Code mới deploy không được nạp: process vẫn chạy bản đã nạp lúc boot (và OPcache của CLI, nếu bật).

Đây là thói quen mà dev Java/Go có sẵn: ở đó process luôn sống lâu, nên state dùng chung và thread
safety được nghĩ tới từ đầu ([06-java-spring.md](../06-java-spring.md), [07-go.md](../07-go.md)). Dev PHP
chuyển sang worker/Octane phải học lại đúng thói quen đó.

#### queue:work bên trong: vòng đời một worker

Đọc `Illuminate\Queue\Worker::daemon()` (Laravel 13), vòng lặp trông như sau:

```
queue:work
 1. listenForSignals()          nếu có ext pcntl: SIGTERM/SIGQUIT/SIGINT, SIGUSR2, SIGCONT
 2. lastRestart = cache('illuminate:queue:restart')
 └─ while (true)
     3. daemonShouldRun?        maintenance mode, worker bị tạm dừng (SIGUSR2) → ngủ rồi kiểm tra lại
     4. resetScope()            forgetScopedInstances, xoá Facade đã resolve, xoá log context,
                                reset bộ đếm thời gian query, memory_reset_peak_usage()
     5. job = getNextJob()      pop từ các queue theo thứ tự --queue=high,default, bỏ qua queue đang bị pause
     6. registerTimeoutHandler  pcntl_alarm(timeout): quá giờ thì SIGALRM giết cả process
     7. có job → runJob()       fire → handle() của job; lỗi thì release/fail theo tries
        không có job → sleep(--sleep, mặc định 3s)
     8. resetTimeoutHandler     pcntl_alarm(0)
     9. stopIfNecessary()       kiểm tra theo thứ tự:
          mất connection · nhận signal dừng · memory ≥ --memory (exit code 12)
          · cache restart đổi · --stop-when-empty · --max-time · --max-jobs
        → có lý do thì thoát; supervisor/systemd/K8s khởi động lại
```

Những điểm hay bị hỏi:

- Mặc định của `queue:work` (xem `WorkCommand`): `--memory=128` (MB), `--timeout=60`, `--sleep=3`,
  `--max-jobs=0` và `--max-time=0` (không giới hạn), `--rest=0`.
- `--memory` được kiểm tra **sau** mỗi job, bằng `memory_get_usage(true)` (bộ nhớ engine đã xin từ
  OS). Nó không chặn một job đơn lẻ ăn quá nhiều; việc đó do `memory_limit` của PHP CLI. ⚠️ Nếu
  `memory_limit` của CLI nhỏ hơn `--memory`, PHP chết với fatal error trước khi Laravel kịp thoát
  êm.
- `--timeout` cần extension `pcntl`. Không có `pcntl` thì không có timeout, không có dừng êm, không
  có pause.
- `scoped` binding được xoá **mỗi job** (bước 4), nên `scoped` là cách đúng để có "singleton trong
  phạm vi một job", y như trong một request Octane.
- Worker không reset static property và không reset singleton thường. Laravel docs nói thẳng: "any
  static state created or modified by your application will not be automatically reset between
  jobs".

#### Nguồn leak hay gặp

| Nguồn | Vì sao tăng mãi | Sửa |
|---|---|---|
| Static array làm cache (`self::$cache[$id] = ...`) | Không bao giờ xoá | Giới hạn kích thước (LRU), hoặc dùng cache ngoài, hoặc `scoped` object |
| `Event::listen()` / `Model::observe()` gọi bên trong job | Mỗi job đăng ký thêm một lần, dispatcher giữ closure | Đăng ký một lần trong service provider |
| `DB::enableQueryLog()` | Mảng query log trong RAM phình theo mỗi query | Chỉ bật tạm khi debug, `DB::flushQueryLog()` |
| Telescope, Debugbar, Ray trong worker | Ghi lại mọi query, event, job | Tắt trong worker production |
| Collection/model gán vào property của singleton | Singleton sống mãi, giữ luôn dữ liệu | Không giữ state theo job trong singleton |
| Vòng tham chiếu (object trỏ vòng qua nhau) | Refcount không về 0, chờ GC chu kỳ (module 3.2) | Phá vòng, `gc_collect_cycles()` |
| Tài nguyên extension (ảnh GD/Imagick, file handle) | Không được RSHUTDOWN dọn | Giải phóng tường minh (Laravel docs lấy ví dụ `imagedestroy`), `fclose` |

Một leak tối giản chạy được bằng `php leak.php`:

```php
<?php
declare(strict_types=1);

final class PriceCache
{
    /** @var array<string, float> */
    public static array $items = [];
}

function handleJob(int $i): void
{
    // "cache cho nhanh", nhưng không bao giờ xoá
    PriceCache::$items['sku-' . $i] = $i * 1.5;
}

for ($i = 1; $i <= 300_000; $i++) {
    handleJob($i);
    if ($i % 100_000 === 0) {
        printf("%d jobs: %.1f MB\n", $i, memory_get_usage() / 1_048_576);
    }
}
// Ba dòng in ra có số MB tăng dần đều: bộ nhớ tỉ lệ với số job đã chạy.
// Trong FPM đoạn code này vô hại vì mảng bị xoá cuối mỗi request.
```

#### Phòng và tìm leak

Lưới an toàn (không sửa leak, chỉ giới hạn thiệt hại):

```sh
php artisan queue:work redis --queue=high,default \
    --memory=256 --max-jobs=1000 --max-time=3600 --timeout=120
```

Worker thoát khi chạm một trong các ngưỡng, process manager khởi động lại, RAM về mức lúc boot.
`--max-time` còn có lợi phụ: worker không giữ connection DB quá lâu.

Tìm gốc:

1. **Đo theo từng job**. Nhờ bước 4 ở trên, `memory_get_peak_usage()` được reset đầu mỗi job, nên
   đỉnh đo được là của riêng job đó:
   ```php
   use Illuminate\Queue\Events\JobProcessed;
   use Illuminate\Support\Facades\Log;
   use Illuminate\Support\Facades\Queue;

   // AppServiceProvider::boot()
   Queue::after(function (JobProcessed $event): void {
       Log::info('job.memory', [
           'job'     => $event->job->resolveName(),
           'mem_mb'  => round(memory_get_usage() / 1_048_576, 1),       // còn lại SAU job
           'peak_mb' => round(memory_get_peak_usage() / 1_048_576, 1),  // đỉnh TRONG job
       ]);
   });
   ```
2. **Tìm loại job** mà `mem_mb` sau job tăng dần qua các lần chạy (peak cao nhưng mem sau job trở về
   bình thường thì không phải leak, chỉ là job nặng).
3. **Cô lập**: chạy riêng loại job đó nhiều lần trong một worker (`--queue=suspect`, dispatch 1000 job
   giống nhau), xem có tăng tuyến tính không.
4. **Tìm chỗ giữ tham chiếu**: static, singleton, listener, query log. Gọi thử `gc_collect_cycles()`
   sau job: nếu bộ nhớ tụt về thì đó là vòng tham chiếu, nếu không thì có ai đó đang giữ tham chiếu
   thật. Profiler bộ nhớ (SPX với metric `zm`, `zo`: số object đang sống) chỉ ra hàm cấp phát.

Hai loại "rò" không phải bộ nhớ nhưng cùng gốc:

- ⚠️ Connection DB/Redis bị server đóng (MySQL `wait_timeout`, failover, proxy cắt connection rảnh).
  Laravel tự reconnect và chạy lại query khi thấy lỗi mất kết nối, **trừ khi đang trong transaction**.
  Worker cũng tự thoát khi gặp lỗi mất kết nối (`stopWorkerIfLostConnection`), để process manager khởi
  động lại sạch.
- ⚠️ Transaction bỏ dở: job gọi `DB::beginTransaction()` rồi ném exception trước `commit()`/
  `rollBack()` thì connection vẫn ở trong transaction, và **job kế tiếp chạy luôn bên trong nó**, lock
  bị giữ tới khi worker chết. Dùng `DB::transaction(fn () => ...)` (tự rollback khi có exception)
  thay vì begin/commit tay.

#### queue:restart và deploy

`queue:restart` không kill ai cả. Nó chỉ ghi timestamp hiện tại vào cache key
`illuminate:queue:restart`. Mỗi worker nhớ giá trị key đó lúc khởi động (bước 2), và sau mỗi vòng lặp
(bước 9) so sánh lại; khác thì thoát êm sau job hiện tại.

| Bước | Worker A (khởi động 10:00) | Lệnh deploy | Kết quả |
|---|---|---|---|
| 1 | Nhớ `lastRestart` = giá trị key lúc 10:00 | | |
| 2 | Đang chạy job X | `php artisan queue:restart` ghi timestamp mới | Cache đổi |
| 3 | Xong job X, `stopIfNecessary` thấy cache khác `lastRestart` | | A thoát với exit 0 |
| 4 | | Supervisor thấy A thoát, khởi động lại | Worker mới boot code mới |

Các bẫy:

- ⚠️ Cache phải **dùng chung** giữa mọi server chạy worker (Redis, database). Driver `file` hay
  `array` thì worker ở server khác không bao giờ thấy tín hiệu.
- ⚠️ Không có process manager thì `queue:restart` chỉ là `queue:stop`: worker thoát và không ai bật
  lại.
- ⚠️ `Queue::withoutInterruptionPolling()` hoặc `Worker::$restartable = false` (tối ưu bỏ việc hỏi
  cache mỗi vòng) làm worker **phớt lờ** `queue:restart`.
- Job dài: worker chỉ thoát sau khi job xong. `stopwaitsecs` của Supervisor (hoặc
  `terminationGracePeriodSeconds` của K8s) phải lớn hơn thời gian job dài nhất (module 2.6).
- Horizon dùng `horizon:terminate` thay vì `queue:restart`.

#### Signal và dừng êm

*Signal* là thông báo OS gửi tới process. Worker Laravel lắng nghe (cần `pcntl`, dùng
`pcntl_async_signals(true)` để handler chạy ngay giữa chừng code, không phải chờ tick):

| Signal | Worker Laravel làm gì | So với master FPM |
|---|---|---|
| `SIGTERM`, `SIGQUIT`, `SIGINT` | Đặt cờ `shouldQuit`, **làm xong job hiện tại** rồi thoát | FPM: `SIGTERM` là dừng ngay, `SIGQUIT` mới là dừng êm |
| `SIGUSR2` | **Tạm dừng** nhận job mới | FPM: reload cấu hình và worker |
| `SIGCONT` | Tiếp tục | |
| `SIGALRM` | Do chính worker hẹn giờ cho `--timeout`: job quá giờ thì giết process | |

Laravel 13 cho job phản ứng với signal qua interface `Illuminate\Contracts\Queue\Interruptible`:
method `interrupted(int $signal)` được gọi khi worker nhận signal dừng **trong lúc** job đang chạy.
Job import dài dùng nó để dừng vòng lặp và lưu tiến độ trước khi bị orchestrator kill:

```php
<?php
declare(strict_types=1);

namespace App\Jobs;

use App\Models\Import;
use Illuminate\Contracts\Queue\Interruptible;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;

final class ImportProducts implements ShouldQueue, Interruptible
{
    use Queueable;

    private bool $shouldStop = false;

    public function __construct(public Import $import) {}

    public function handle(): void
    {
        foreach ($this->import->pendingRows() as $row) {
            if ($this->shouldStop) {
                break;                       // dừng ở ranh giới an toàn giữa hai dòng
            }
            // ... xử lý $row
        }
        $this->import->saveProgress();       // lần chạy sau tiếp tục từ đây
    }

    public function interrupted(int $signal): void
    {
        $this->shouldStop = true;            // chỉ đặt cờ, không làm việc nặng trong signal handler
    }
}
```

Daemon tự viết (consumer Kafka chẳng hạn) phải tự làm phần này:

```php
<?php
declare(strict_types=1);

pcntl_async_signals(true);
$running = true;
foreach ([SIGTERM, SIGINT, SIGQUIT] as $sig) {
    pcntl_signal($sig, static function () use (&$running): void { $running = false; });
}

while ($running) {
    $message = fetchNext();          // hàm giả định: lấy 1 message, có timeout
    if ($message !== null) {
        process($message);           // xong trọn message rồi mới quay lại kiểm tra cờ
    }
}
// đóng connection, commit offset... rồi thoát với exit code 0
```

#### Octane: một app, nhiều request

*Octane* chạy Laravel trên một *application server* sống lâu. App boot **một lần mỗi worker** (chạy
`register` và `boot` của mọi service provider một lần), rồi worker đó phục vụ nhiều request liên tiếp.
Bỏ được chi phí boot framework mỗi request.

Ba server Octane hỗ trợ:

| | FrankenPHP | RoadRunner | Swoole / Open Swoole |
|---|---|---|---|
| Viết bằng | Go, xây trên web server Caddy, **nhúng PHP như một thư viện** | Go, điều khiển các process PHP CLI qua pipe | Extension C của PHP |
| Đơn vị worker | Thread trong một process (PHP bản ZTS, thread-safe) | Process PHP riêng | Process, mỗi process có event loop |
| Cần Nginx phía trước | Không bắt buộc (có HTTPS, HTTP/2, HTTP/3 sẵn) | Tuỳ | Tuỳ |
| Tính năng Octane riêng | | | `Octane::concurrently()` (task worker), `Octane::tick()`, Octane cache và Swoole table dùng chung giữa worker |

Swoole có *coroutine*: nhiều luồng việc xen kẽ trong một process, chuyển qua lại khi gặp I/O. Octane
**không** chạy nhiều request đồng thời trong một worker; `concurrently()` đẩy việc sang *task worker*
(process khác), và giới hạn tối đa 1024 task mỗi lần gọi.

Cấu hình quan trọng (docs Octane và `config/octane.php`):

- `--workers`: mặc định một worker mỗi core CPU. Swoole thêm `--task-workers`.
- `--max-requests`: mặc định **500**, worker được tái sinh êm sau 500 request để chặn leak lặt vặt.
- `max_execution_time`: mặc định 30 giây mỗi request; đổi phải restart server.
- `garbage`: ngưỡng MB (mặc định 50) để listener `CollectGarbage` gọi `gc_collect_cycles()`. ⚠️
  Listener này bị **comment sẵn** trong config, muốn dùng phải bật.
- `octane:reload` sau deploy (giống `queue:restart`), chạy dưới Supervisor với `stopwaitsecs` đủ lớn.

Khi nào đáng dùng: khi phần boot framework chiếm phần lớn thời gian request (API nhỏ, nhiều request
ngắn). Đo trước: một route trả chuỗi rỗng trên FPM tốn bao nhiêu ms, so với tổng thời gian endpoint
thật. Nếu endpoint tốn 300 ms chờ DB thì bỏ 20 ms boot không đáng so với rủi ro state leak.

#### Octane bên trong: sandbox và rò trạng thái giữa request

Đọc `Laravel\Octane\Worker::handle()`: với mỗi request, Octane **clone** application đã boot thành một
*sandbox*, chạy request trên sandbox, rồi `flush()` và bỏ sandbox. Clone là shallow: mảng
`$instances` của container được sao chép, nhưng các object bên trong thì **dùng chung** với app gốc.

```
Worker boot 1 lần: app gốc
  instances = { router, db, cache, config, log, events, ... , ServiceResolvedLúcBoot }
                                  │ (object dùng chung)
Request 1: sandbox1 = clone app ──┤  + instances resolve LẦN ĐẦU trong request 1 → chỉ nằm ở sandbox1
Request 2: sandbox2 = clone app ──┘  sandbox1 đã bị bỏ, nên thứ resolve trong request 1 cũng mất
```

Hệ quả, chính xác hơn câu "singleton luôn leak":

- Singleton **được resolve lúc boot** (trong `boot()` của provider, trong danh sách `warm`, hoặc là
  dependency của một service đã warm) là **một object dùng cho mọi request** của worker. Nếu nó giữ
  `Request`, user, config hay container lúc boot, mọi request sau thấy bản cũ. Octane docs cảnh báo
  đúng trường hợp này.
- Singleton resolve lần đầu bên trong một request nằm ở sandbox và bị bỏ cùng sandbox, nên thường
  không leak. Nhưng bạn khó biết chắc lúc nào nó được resolve (chỉ cần một provider gọi nó trong
  `boot()`), nên đừng dựa vào điều này.
- **Static property** không liên quan tới container: luôn sống qua mọi request.
- Object dùng chung bị **sửa** trong request (gọi setter trên một service đã warm, thêm listener vào
  dispatcher, `config([...])`) thì request sau thấy thay đổi, trừ những thứ Octane tự reset.

Octane tự reset nhiều state của framework trước và sau mỗi request (danh sách listener trong
`config/octane.php`): tạo sandbox mới cho config và URL generator, đưa application mới cho auth gate,
DB manager, cache, queue, router, view, validation..., xoá auth state, session, locale, cookie đã
queue, query log, log context, cache `Str`, `once()`, và xoá mọi `scoped` instance
(`FlushTemporaryContainerInstances`). Controller cache trên route cũng được flush sau mỗi request.
⚠️ Package bên thứ ba và code của bạn không nằm trong danh sách đó.

Ví dụ leak user giữa hai request và cách sửa:

```php
<?php
declare(strict_types=1);

namespace App\Services;

use App\Models\User;

final class AuditLogger
{
    private ?User $actor = null;

    public function setActor(?User $actor): void { $this->actor = $actor; }

    public function log(string $action): void
    {
        // ghi $this->actor?->id cùng $action vào bảng audit
    }
}
```

```php
// AppServiceProvider
public function register(): void
{
    $this->app->singleton(AuditLogger::class);          // SAI trong Octane
}

public function boot(): void
{
    $this->app->make(AuditLogger::class);                // resolve lúc boot → dùng chung mọi request
}

// Middleware chạy mỗi request
public function handle(Request $request, Closure $next): Response
{
    if ($request->user() !== null) {
        app(AuditLogger::class)->setActor($request->user());   // chỉ set khi đã đăng nhập
    }
    return $next($request);
}
```

| Bước | Worker Octane | Kết quả |
|---|---|---|
| 1 | Request 1 của user An (id 7): middleware `setActor(An)` | `actor = An` |
| 2 | Request 2 của khách chưa đăng nhập, gọi `log('view_invoice')` | Middleware không set gì, `actor` **vẫn là An**. Audit ghi An xem hoá đơn |
| 3 | Trên FPM | Không xảy ra: mỗi request một object mới |

Ba cách sửa, theo thứ tự nên chọn:

1. Không giữ state theo request trong service: truyền thẳng vào method, `log(string $action, ?User
   $actor)`. Octane docs gọi đây là cách được khuyên nhất.
2. Đăng ký bằng `scoped`: `$this->app->scoped(AuditLogger::class);`. Mỗi request (và mỗi job của
   queue worker) có một instance mới, trong request vẫn dùng chung như singleton.
3. Nếu buộc phải là singleton: inject *resolver* thay vì giá trị, ví dụ `fn () => $app['request']`,
   `fn () => Container::getInstance()`, hoặc gọi helper `request()`, `config()` ngay lúc dùng. Docs
   Octane ghi rõ hai helper này luôn trả về bản hiện tại (request đang xử lý, config mới nhất).

Type-hint `Request` trong method của controller và route closure là an toàn (docs Octane ghi rõ).

#### Bảng các bẫy khi chạy process sống lâu

| Bẫy | Queue worker | Octane | Sửa |
|---|---|---|---|
| Static array/cache tự chế tăng mãi | Có | Có | Giới hạn kích thước, cache ngoài, `scoped` |
| Singleton giữ `Request`/user/config lúc boot | Ít gặp (không có request) nhưng giữ config/tenant của job đầu | Có, nguy hiểm nhất | Truyền qua method, `scoped`, resolver closure |
| Setter trên service dùng chung (`setTenant`, `setActor`) | Có | Có | Không giữ state theo request/job trong singleton |
| `Event::listen` trong job/request | Có | Có | Đăng ký trong provider |
| `config([...])` lúc chạy | Còn nguyên cho job sau | Octane reset (config sandbox) | Đừng đổi config lúc chạy |
| `setlocale`, `date_default_timezone_set`, `ini_set` | Còn nguyên | Còn nguyên (là state của process) | Đặt một lần lúc boot, hoặc đặt lại mỗi lần |
| Transaction mở tay không đóng | Job sau chạy trong transaction cũ | Request sau chạy trong transaction cũ | `DB::transaction(closure)` |
| Connection bị server đóng | "server has gone away" | Như bên trái | Laravel reconnect ngoài transaction; `--max-time`; listener `DisconnectFromDatabases` của Octane |
| Code deploy mới không được nạp | Có | Có | `queue:restart`, `horizon:terminate`, `octane:reload` |
| Package bên thứ ba lưu state trong static | Có | Có | Kiểm tra tài liệu Octane của package; `flush` trong config Octane |
| Telescope/Debugbar/query log | RAM tăng | RAM tăng | Tắt trong process sống lâu |
| `exit()`/`die()` trong code | Kết thúc cả worker | Hành vi tuỳ server, có thể kết thúc worker | Ném exception, trả response |

**Tóm tắt nhanh**

- Process sống lâu không có RSHUTDOWN giữa các job/request: static, singleton, listener, connection
  và state của process sống mãi. Cái gì tích luỹ thì leak, cái gì bị sửa thì rò sang lần sau.
- `queue:work` mỗi vòng: reset scoped/facade → lấy job → hẹn giờ `pcntl_alarm` → chạy → kiểm tra
  memory, restart, `--max-jobs`, `--max-time` rồi mới thoát. `--memory` kiểm sau job, mặc định 128 MB.
- `queue:restart` chỉ ghi timestamp vào cache; cần cache dùng chung và process manager.
- Octane clone app mỗi request: singleton resolve lúc boot và static là thứ dùng chung. Sửa bằng
  truyền qua method, `scoped`, hoặc resolver closure. Mặc định tái sinh worker sau 500 request.
- Tìm leak: log `memory_get_usage()` sau mỗi job theo tên job, cô lập loại job tăng dần, tìm chỗ giữ
  tham chiếu, thử `gc_collect_cycles()`.

**Nguồn**: [Laravel: Queues (Running the Queue Worker, Resource Considerations, Worker Signals)](https://laravel.com/docs/queues#running-the-queue-worker) · [laravel/framework: Queue/Worker.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Queue/Worker.php) · [laravel/framework: QueueServiceProvider.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Queue/QueueServiceProvider.php) · [Laravel: Octane](https://laravel.com/docs/octane) (mục Dependency Injection and Octane, Managing Memory Leaks) · [laravel/octane: Worker.php](https://github.com/laravel/octane/blob/2.x/src/Worker.php) · [laravel/octane: config/octane.php](https://github.com/laravel/octane/blob/2.x/config/octane.php) · [FrankenPHP worker mode](https://frankenphp.dev/docs/worker/) · [RoadRunner docs](https://roadrunner.dev/docs) · [PHP: PCNTL](https://www.php.net/manual/en/book.pcntl.php)


---

### 3.6 Hiệu năng và profiling

Module này trả lời: "endpoint này chậm, bạn làm gì" theo đúng thứ tự đo, tìm, sửa, đo lại; mỗi loại
công cụ (APM, profiler instrument, profiler sampling) cho biết gì và không cho biết gì; đọc flame
graph thế nào; và xử lý dữ liệu lớn (import/export triệu dòng) mà RAM không tăng theo số dòng.

#### Quy trình tìm nút thắt

1. **Đo và khoanh vùng**: APM hoặc log cho biết endpoint nào chậm, chậm bao nhiêu, ở percentile nào
   (p95, p99 quan trọng hơn trung bình), chậm lúc nào (luôn chậm, hay chỉ lúc cao điểm).
2. **Phân rã thời gian**: một request chậm gồm những gì? Thời gian chờ worker (hàng đợi FPM), thời
   gian DB, thời gian gọi HTTP ra ngoài, thời gian CPU của PHP. Trace của APM hoặc Telescope/Pulse
   trả lời được phần lớn.
3. **Tái hiện** ở môi trường profile được (local, staging) với dữ liệu cỡ gần thật. Endpoint chậm vì
   bảng 10 triệu dòng sẽ nhanh trên máy dev có 100 dòng.
4. **Profile** để biết hàm nào tốn: đây là lúc dùng Xdebug, SPX, Blackfire.
5. **Sửa đúng chỗ tốn nhất**. Theo kinh nghiệm chung của app Laravel: query (N+1, thiếu index), gọi
   API tuần tự, serialize/hydrate quá nhiều model; hiếm khi là thuật toán PHP thuần.
6. **Đo lại cùng điều kiện** (cùng dữ liệu, cùng tải, cùng số lần lặp) và so sánh. Không có số trước
   sau thì chưa có cải thiện ([17-performance.md](../17-performance.md)).

⚠️ Sai lầm hay gặp: tối ưu thứ mình đoán (đổi `array_map` sang `foreach`, bỏ Collection) trước khi
đo. Hàm chiếm 2% thời gian thì làm nó nhanh gấp đôi cũng chỉ lợi 1%.

#### Hai kiểu profiler: instrument và sampling

*Profiler* ghi lại thời gian và bộ nhớ tiêu tốn theo từng hàm trong một lần chạy. Có hai cách thu:

| | Instrumenting (đo mọi lời gọi) | Sampling (lấy mẫu) |
|---|---|---|
| Cơ chế | Hook vào mọi lần vào/ra hàm, ghi thời gian chính xác | Cứ mỗi N micro giây chụp call stack một lần, đếm tần suất |
| Cho biết | Số lần gọi chính xác, thời gian mỗi hàm | Tỉ lệ thời gian theo stack, không có số lần gọi chính xác |
| Overhead | Lớn, tỉ lệ với số lời gọi hàm | Nhỏ và gần như cố định |
| ⚠️ Méo | Hàm nhỏ gọi hàng triệu lần bị **phóng đại** (chi phí đo lớn hơn chi phí hàm) | Hàm quá ngắn có thể không bị bắt mẫu |
| Ví dụ | Xdebug profiler, XHProf, SPX mặc định, Blackfire | SPX với `SPX_SAMPLING_PERIOD`, Excimer (Wikimedia), APM continuous profiling |

Hai con số cần phân biệt khi đọc mọi profiler:

- *Inclusive* (Incl., "tổng"): thời gian của hàm **cộng mọi hàm nó gọi**. Dùng để đi từ trên xuống:
  controller tốn 800 ms, trong đó service A 700 ms.
- *Exclusive* (Excl., *self*): thời gian chỉ tính thân hàm, trừ các hàm con. Dùng để tìm chỗ thực
  sự đốt thời gian: `PDOStatement::execute` self 600 ms nghĩa là 600 ms chờ DB.
- *Wall time* là thời gian đồng hồ thật; *CPU time* là thời gian CPU chạy. Wall lớn hơn CPU nhiều thì
  process đang chờ (I/O, lock, sleep); SPX gọi phần chênh là *idle time*.

#### Công cụ

| Công cụ | Loại | Dùng ở đâu |
|---|---|---|
| Xdebug profiler | Instrument, xuất file cachegrind | Chỉ dev. ⚠️ Overhead lớn khi profile; chỉ `xdebug.mode=off` mới gần như không tốn gì |
| SPX | Instrument hoặc sampling, có web UI (timeline, flat profile, flame graph) | Dev, staging. Tác giả ghi rõ là experimental, dùng cho môi trường không phải production |
| XHProf (và các fork) | Instrument, gộp theo cặp caller/callee | Dev, staging |
| Excimer | Sampling, xuất flame graph | Được thiết kế để chạy cả production |
| Blackfire, Tideways | Thương mại: profiler theo yêu cầu + giám sát | Production được, chỉ profile request được kích hoạt |
| Telescope, Debugbar | Xem query, request, job của Laravel | Dev |
| Pulse, Nightwatch | Giám sát Laravel (request chậm, query chậm, job, exception) | Production |
| APM (New Relic, Datadog, OpenTelemetry) | Trace phân tán, theo dõi toàn hệ thống | Production, bức tranh tổng |

APM cho biết **endpoint nào** chậm và chậm ở **tầng nào**. Profiler cho biết **hàm nào** trong
endpoint đó. Đừng dùng cái này thay cái kia.

*Xdebug profiler*

```ini
; 99-xdebug.ini (Xdebug 3)
zend_extension = xdebug
xdebug.mode = profile
xdebug.start_with_request = trigger      ; chỉ profile khi có XDEBUG_TRIGGER
xdebug.output_dir = /tmp/xdebug
; tên file mặc định: cachegrind.out.%p (theo PID), nén .gz khi xdebug.use_compression bật
```

```sh
curl -b 'XDEBUG_TRIGGER=1' https://app.test/orders   # hoặc ?XDEBUG_TRIGGER=1, hoặc biến môi trường cho CLI
XDEBUG_TRIGGER=1 php artisan report:daily
```

Response có header `X-Xdebug-Profile-Filename` chỉ ra file vừa tạo. Mở bằng KCachegrind/QCachegrind
(macOS: `brew install qcachegrind`), Webgrind (web), hoặc PhpStorm. Trong KCachegrind: pane "Flat
Profile" bên trái, cột *Incl.* và *Self*, cột *Called* (số lần gọi); pane bên phải là *callers* (ai
gọi hàm này) và *callees* (hàm này gọi ai). Hàm nội bộ của PHP có tiền tố `php::`, ví dụ
`php::PDOStatement->execute`.

⚠️ Không bao giờ để `xdebug.mode` khác `off` trên production; tốt nhất là không cài extension. File
profile của một request Laravel có thể nặng hàng chục MB.

*SPX*: cài như một extension (`pie install noisebynorthwest/php-spx`), rồi:

```ini
; chỉ cho môi trường dev riêng
spx.http_enabled = 1
spx.http_key = "dev"
spx.http_ip_whitelist = "127.0.0.1"
```

```sh
# Web: mở http://localhost/?SPX_KEY=dev&SPX_UI_URI=/ , bật "Enabled", rồi tải lại trang cần đo
curl --cookie "SPX_ENABLED=1; SPX_KEY=dev" http://localhost/orders

# CLI: in flat profile ra stderr khi script kết thúc (kể cả khi Ctrl-C)
SPX_ENABLED=1 php artisan report:daily
# Báo cáo đầy đủ để xem trên web UI, kèm sampling để không phóng đại hàm nhỏ
SPX_ENABLED=1 SPX_REPORT=full SPX_SAMPLING_PERIOD=100 php artisan report:daily
```

SPX mặc định đo hai metric `wt` (wall time) và `zm` (bộ nhớ Zend Engine); có thêm `ct` (CPU), `it`
(idle), `zo` (số object đang sống, hữu ích khi tìm leak), `io`. Với worker sống lâu, tắt tự động
(`SPX_AUTO_START=0`) và bọc từng job bằng `spx_profiler_start()` / `spx_profiler_stop()`, vì profile
cả vòng đời một worker chờ việc là vô nghĩa. ⚠️ Trên FPM, metric đọc từ `/proc` (`mor`, `io`) cần
`process.dumpable = yes` trong pool.

*Blackfire, Tideways*: extension (probe) trong PHP cộng một agent/daemon gửi dữ liệu về dịch vụ. Chỉ
request được kích hoạt (bằng browser extension hoặc CLI như `blackfire curl`, `blackfire run`) mới bị
profile, nên chạy trên production được với request tổng hợp. Điểm mạnh so với công cụ miễn phí: call
graph có đường nóng (*hot path*) được tô sẵn, so sánh hai profile trước/sau, đếm query SQL và gọi
HTTP, viết assertion hiệu năng chạy trong CI (Blackfire), kết hợp giám sát liên tục (Tideways).

#### Đọc flame graph

*Flame graph* là cách vẽ hàng nghìn call stack gộp lại thành một hình:

```
                           ┌──────────────┐
                           │PDO::execute  │                   ┌────────┐
               ┌───────────┴──────────────┤  ┌───────────┐    │json_enc│
               │ Builder::get             │  │ curl_exec │    ├────────┤
┌──────────────┴──────────────────────────┼──┴───────────┴──┐ │toArray │
│ OrderController::index                  │ PaymentClient   │ ├────────┤
├─────────────────────────────────────────┴─────────────────┴─┴────────┤
│ Kernel::handle                                                        │
└───────────────────────────────────────────────────────────────────────┘
  trục ngang: tỉ lệ thời gian (KHÔNG phải thứ tự thời gian)
  trục dọc: độ sâu stack, hàm ở dưới gọi hàm ở trên
  (hình minh hoạ, tên hàm rút gọn: PDO::execute là PDOStatement::execute)
```

Cách đọc:

1. **Chiều rộng là tất cả**: một khối rộng 40% nghĩa là 40% tổng thời gian nằm trong hàm đó (inclusive).
   Màu thường chỉ để phân biệt, không mang nghĩa.
2. **Trục ngang không phải thời gian**: các khối được xếp (thường theo tên) và gộp các stack giống
   nhau. Muốn xem thứ tự theo thời gian thì dùng *timeline* / *flame chart* (SPX có sẵn).
3. **Tìm "cao nguyên"**: khối rộng mà phía trên không còn gì (hoặc chỉ khối con hẹp) là hàm tốn thời
   gian *tự thân* (exclusive). Ví dụ trên: `PDO::execute` rộng và nằm trên đỉnh, tức phần lớn thời gian
   là chờ DB.
4. **Đi từ dưới lên** theo khối rộng nhất để biết code nào của mình dẫn tới đó (`OrderController::index`
   → `Builder::get` → `PDO::execute`).
5. **N+1**: flame graph gộp các stack giống nhau, nên hàng trăm lần lazy load cùng một stack
   (`Model::getRelationValue → ... → Builder::get → PDOStatement::execute`) hiện thành **một** khối
   rộng. Muốn thấy đó là nhiều lời gọi nhỏ lặp lại thì xem timeline / flame chart (nhiều khối hẹp
   giống nhau nối tiếp) hoặc cột số lần gọi của profiler instrument.
6. *Icicle graph* là flame graph lật ngược (gốc ở trên); đọc giống hệt.

#### Đọc file lớn

- ⚠️ `file_get_contents()` và `file()` nạp **cả file** vào RAM. File CSV 2 GB là ít nhất 2 GB, và vượt
  `memory_limit` là fatal error.
- Đọc từng dòng bằng `fopen` + `fgetcsv`, bọc trong *generator* (hàm có `yield`, trả từng phần tử khi
  được hỏi) để code gọi dùng như một danh sách mà bộ nhớ chỉ giữ một dòng:

```php
<?php
declare(strict_types=1);

/** @return \Generator<int, list<string|null>> */
function csvRows(string $path): \Generator
{
    $h = fopen($path, 'rb');
    if ($h === false) {
        throw new \RuntimeException("Không mở được $path");
    }
    try {
        // PHP 8.4+: không truyền $escape là E_DEPRECATED; '' tắt cơ chế escape riêng của PHP
        while (($row = fgetcsv($h, null, ',', '"', '')) !== false) {
            if ($row === [null]) {
                continue;                  // dòng trống được fgetcsv trả về là [null]
            }
            yield $row;
        }
    } finally {
        fclose($h);                        // chạy cả khi vòng foreach bên ngoài break sớm
    }
}

$count = 0;
foreach (csvRows('/tmp/users.csv') as $row) {
    $count++;
}
echo $count, PHP_EOL;
printf("peak: %.1f MB\n", memory_get_peak_usage() / 1_048_576);  // gần như không đổi theo cỡ file
```

- ⚠️ PHP 8.4 deprecate việc dựa vào giá trị mặc định của tham số `$escape` trong `fgetcsv`, `fputcsv`,
  `str_getcsv` (và `SplFileObject::setCsvControl`). Luôn truyền tường minh, `''` là lựa chọn đúng
  chuẩn RFC 4180.
- `SplFileObject` với cờ `READ_CSV | SKIP_EMPTY | READ_AHEAD` là lựa chọn hướng đối tượng tương đương.

#### Import dữ liệu lớn

Thiết kế import CSV 5 triệu dòng chạy tiếp được khi lỗi:

1. Upload file lên storage (S3/local), tạo bản ghi `imports` (trạng thái, `byte_offset`, số dòng đã
   xử lý), dispatch job. **Không** xử lý trong request HTTP.
2. Job mở file, `fseek()` tới `byte_offset` đã lưu, đọc từng lô (ví dụ 1000 dòng).
3. Mỗi lô: validate, rồi insert batch (một câu `INSERT` nhiều dòng, 500-1000 dòng) hoặc `upsert()`
   nếu cần idempotent theo khoá tự nhiên.
4. Mỗi lô một **transaction ngắn**, commit xong thì lưu `byte_offset = ftell($h)` vào `imports`
   (trong cùng transaction thì càng chắc: dữ liệu và tiến độ commit cùng nhau).
5. Lỗi hoặc worker bị dừng: lần chạy lại đọc `byte_offset` và tiếp tục; dùng `Interruptible`
   (module 3.5) để dừng ở ranh giới lô.
6. ⚠️ Không bọc cả file trong một transaction: undo log phình to, lock giữ hàng chục phút, replica trễ.
   ⚠️ Tắt query log và event model (`Model::withoutEvents`, hoặc dùng query builder) khi insert hàng
   triệu dòng.

#### Export dữ liệu lớn

Streaming CSV: đọc DB theo lô, ghi thẳng xuống client, bộ nhớ gần như hằng số.

```php
<?php
declare(strict_types=1);

use App\Models\Order;
use Symfony\Component\HttpFoundation\StreamedResponse;

Route::get('/orders/export', function (): StreamedResponse {
    return response()->streamDownload(function (): void {
        $out = fopen('php://output', 'wb');
        fwrite($out, "\xEF\xBB\xBF");                       // BOM để Excel đọc đúng UTF-8 tiếng Việt
        fputcsv($out, ['id', 'khach_hang', 'tong'], ',', '"', '');

        foreach (Order::query()->select(['id', 'customer_name', 'total'])->lazyById(1000) as $o) {
            fputcsv($out, [$o->id, csvSafe($o->customer_name), $o->total], ',', '"', '');
        }
        fclose($out);
    }, 'orders.csv', [
        'Content-Type'      => 'text/csv; charset=UTF-8',
        'X-Accel-Buffering' => 'no',                           // bảo Nginx không gom response vào buffer
    ]);
});

function csvSafe(string $v): string
{
    // CSV injection: ô bắt đầu bằng = + - @ (và tab, CR) bị Excel hiểu là công thức
    return in_array($v[0] ?? '', ['=', '+', '-', '@', "\t", "\r"], true) ? "'" . $v : $v;
}
```

- `lazyById(1000)` chạy nhiều query `WHERE id > ? ORDER BY id LIMIT 1000`, mỗi lần chỉ giữ 1000 model.
  Khác `lazy()` (dùng OFFSET, chậm dần) và `cursor()` (một query, nhưng với mysqlnd buffered thì kết
  quả vẫn nằm hết trong RAM, xem module 2.7 của [03-database-sql.md](03-database-sql.md)).
- ⚠️ Các tầng buffer giữ dữ liệu lại thay vì gửi dần:
  - Output buffering của PHP (`output_buffering`, bản php.ini-production đặt 4096 byte) và mọi
    `ob_start()` đang mở.
  - Nginx gom response từ FastCGI (`fastcgi_buffering`): tắt cho response này bằng header
    `X-Accel-Buffering: no`.
  - Nén gzip ở proxy, CDN cũng có thể gom.
- ⚠️ Timeout: export 2 triệu dòng mất vài phút, vượt `fastcgi_read_timeout`, LB timeout,
  `request_terminate_timeout` (module 3.4). Export rất lớn nên chạy nền: job ghi file lên S3, gửi link
  có hạn cho user.

#### Gọi nhiều API

Gọi tuần tự 3 API, mỗi cái 300 ms, là 900 ms. `Http::pool()` gửi đồng thời (Guzzle, curl multi bên
dưới), tổng xấp xỉ API chậm nhất:

```php
use Illuminate\Http\Client\Pool;
use Illuminate\Support\Facades\Http;

$responses = Http::pool(fn (Pool $pool) => [
    $pool->as('user')->timeout(2)->get('https://api.example.com/users/7'),
    $pool->as('orders')->timeout(2)->get('https://api.example.com/users/7/orders'),
    $pool->as('points')->timeout(2)->get('https://loyalty.example.com/points/7'),
]);

$orders = $responses['orders']->json();
```

⚠️ Luôn đặt timeout cho từng request trong pool; một API treo vẫn giữ cả request lại tới khi hết giờ.

**Tóm tắt nhanh**

- Quy trình: đo (APM, p95) → phân rã thời gian → tái hiện với dữ liệu thật → profile → sửa chỗ tốn
  nhất → đo lại cùng điều kiện.
- Instrument (Xdebug, SPX mặc định) chính xác số lần gọi nhưng phóng đại hàm nhỏ; sampling (SPX
  sampling, Excimer) nhẹ và đúng tỉ lệ. Xdebug chỉ dùng ở dev.
- Inclusive để đi từ trên xuống, exclusive để tìm chỗ đốt thời gian; wall ≫ CPU nghĩa là đang chờ I/O.
- Flame graph: chiều rộng là thời gian, trục ngang không phải thứ tự; tìm khối rộng trên đỉnh.
- Dữ liệu lớn: generator + `fgetcsv` (truyền `$escape` từ PHP 8.4), insert batch, transaction ngắn mỗi
  lô, lưu offset; export bằng `streamDownload` + `lazyById` + `X-Accel-Buffering: no`.

**Nguồn**: [Xdebug: Profiling](https://xdebug.org/docs/profiler) · [php-spx README](https://github.com/NoiseByNorthwest/php-spx) · [Blackfire docs](https://docs.blackfire.io/) · [Laravel: Pulse](https://laravel.com/docs/pulse) · [Laravel: Telescope](https://laravel.com/docs/telescope) · [Laravel: HTTP Client, Concurrent Requests](https://laravel.com/docs/http-client#concurrent-requests) · [PHP: fgetcsv (changelog 8.4)](https://www.php.net/manual/en/function.fgetcsv.php) · [PHP: SplFileObject](https://www.php.net/manual/en/class.splfileobject.php) · [Brendan Gregg: Flame Graphs](https://www.brendangregg.com/flamegraphs.html)


---

### 3.7 Bảo mật đặc thù PHP

Module này trả lời: những lỗ hổng mang dấu vân tay của riêng PHP mà một checklist OWASP chung
không nói kỹ, gồm object injection qua `unserialize`, magic hash trong so sánh, include file theo
input, mass assignment, và hậu quả khi lộ `APP_KEY`. Đây là nhóm câu senior thích hỏi vì nó buộc
bạn hiểu cơ chế ngôn ngữ chứ không chỉ nhớ tên lỗ hổng.

#### unserialize và object injection (POP chain)

`serialize()` biến một giá trị PHP thành chuỗi văn bản, `unserialize()` dựng lại giá trị đó. Điểm
nguy hiểm: chuỗi serialize của một object có ghi sẵn tên class, nên `unserialize()` sẽ *tạo instance
của đúng class đó* rồi gán property theo nội dung chuỗi. Kẻ tấn công kiểm soát chuỗi vào tức là
kiểm soát được class nào được tạo và property mang giá trị gì.

Lỗ hổng gọi là *object injection*, và kỹ thuật khai thác gọi là *POP chain* (Property-Oriented
Programming): ghép các đoạn code có sẵn trong app hoặc trong `vendor/` thành một chuỗi hành động
nguy hiểm, khởi động bằng một *magic method* chạy tự động lúc deserialize.

Trình tự khai thác:

1. Kẻ tấn công gửi một chuỗi serialize chứa object của class có sẵn (thường lấy từ một thư viện
   trong `vendor/`), với property do họ đặt.
2. `unserialize()` tạo object đó. `__wakeup()` chạy ngay sau khi dựng xong; `__destruct()` chạy khi
   object bị giải phóng. Đây là hai điểm khởi động không cần app gọi hàm gì thêm.
3. Magic method đó thao tác trên một property, mà property này lại là một object khác do kẻ tấn công
   nhét vào. Thao tác đó (ví dụ gọi một method, ép object thành string kích hoạt `__toString()`)
   chuyền tiếp sang gadget kế. Nối nhiều gadget lại thành chain.
4. Gadget cuối làm việc thật sự nguy hiểm: ghi file, gọi `system()`, xoá dữ liệu. Kết quả thường là
   *RCE* (Remote Code Execution, chạy lệnh tuỳ ý trên server).

Ví dụ tối giản một gadget khởi động qua `__destruct`:

```php
<?php
declare(strict_types=1);

class Logger
{
    public string $file = '/tmp/app.log';
    public string $data = '';

    public function __destruct()
    {
        // Ý định vô hại: ghi log khi object bị huỷ.
        file_put_contents($this->file, $this->data);
    }
}

// Kẻ tấn công không cần viết class này, chỉ cần nó tồn tại trong codebase.
// Họ gửi lên payload sau (đây là chuỗi họ tự dựng, không phải app tạo):
$payload = 'O:6:"Logger":2:{s:4:"file";s:23:"/var/www/html/shell.php";'
         . 's:4:"data";s:23:"<?php system($_GET[0]);";}';

$obj = unserialize($payload);   // ⚠️ tạo Logger với file/data do kẻ tấn công chọn
// Khi $obj bị huỷ, __destruct ghi một web shell vào webroot -> RCE.
```

Ở đây `Logger` hoàn toàn hợp lệ trong app; lỗ hổng nằm ở chỗ `unserialize()` chạy trên dữ liệu
ngoài. Trong thực tế chain dài hơn nhiều vì gadget ghi-file trực tiếp hiếm; công cụ **phpggc**
(PHP Generic Gadget Chains) có sẵn payload cho Laravel, Symfony, Monolog, Guzzle... nên kẻ tấn công
không phải tự tìm chain.

Cách phòng, theo thứ tự ưu tiên:

- Đừng `unserialize()` dữ liệu người dùng. Dùng JSON (`json_encode`/`json_decode`) cho dữ liệu đi
  qua ranh giới tin cậy: JSON chỉ dựng lại mảng và kiểu vô hướng, không tạo object nên không có
  gadget nào chạy.
- Bắt buộc phải deserialize object thì truyền `allowed_classes`:

  ```php
  <?php
  declare(strict_types=1);

  $safe = unserialize($raw, ['allowed_classes' => false]);      // mọi object thành __PHP_Incomplete_Class
  $ok   = unserialize($raw, ['allowed_classes' => [Money::class]]); // chỉ cho phép class trong whitelist
  ```

  ⚠️ Từ PHP 8.4, nếu `allowed_classes` không phải mảng tên class hoặc bool thì `unserialize()` ném
  `TypeError`/`ValueError` (trước đó chỉ trả `false` kèm warning). PHP 7.4 thêm `max_depth` chống
  tràn stack; PHP 8.3 bắt đầu phát `E_WARNING` khi chuỗi thừa dữ liệu hoặc không giải được.
- Nếu payload đến từ nơi bạn kiểm soát nhưng vẫn muốn chống giả mạo: ký HMAC lên chuỗi và kiểm chữ
  ký bằng `hash_equals` (xem dưới) *trước khi* deserialize.

⚠️ Bẫy `phar://`: trước PHP 8.0, chỉ cần một hàm thao tác file (`file_exists`, `is_file`,
`fopen`...) chạy trên đường dẫn `phar://kẻ-tấn-công-upload.phar` là metadata trong file phar bị
`unserialize` ngầm, kích hoạt object injection mà không có lời gọi `unserialize()` nào trong code.
PHP 8.0 (RFC *phar_stop_autoloading_metadata*) đã tắt hành vi tự deserialize metadata này.

⚠️ Từ PHP 8.5, `__sleep()`/`__wakeup()` bị *soft-deprecate*; khuyến nghị chuyển sang
`__serialize()`/`__unserialize()`. Điều này không làm object injection an toàn hơn: hai magic method
mới vẫn chạy khi deserialize, nên nguyên tắc "không unserialize dữ liệu ngoài" không đổi.

Đối chiếu: đây chính là lớp lỗ hổng "insecure deserialization" trong OWASP; Java gặp bản tương
đương với `ObjectInputStream.readObject()` và các gadget chain qua thư viện (Commons-Collections...).
Bài học chung: định dạng serialize gốc của ngôn ngữ (PHP serialize, Java native) không bao giờ dùng
cho dữ liệu không tin cậy; JSON là ranh giới an toàn.

#### Type juggling trong so sánh: magic hash và bypass xác thực

`==` ép kiểu hai vế về cùng kiểu rồi mới so; `===` so cả kiểu lẫn giá trị, không ép (chi tiết ở
module 1.1). Trong bảo mật, `==` gây ra *authentication bypass* khi so token, hash, hoặc chữ ký.

*Magic hash* là ca kinh điển:

```php
<?php
declare(strict_types=1);

var_dump(md5('240610708') === md5('QNKCDZO'));  // bool(false)  <- đúng
var_dump(md5('240610708') == md5('QNKCDZO'));   // bool(true)   <- ⚠️ nguy hiểm
// md5('240610708') = '0e462097431906509019562988736854'
// md5('QNKCDZO')   = '0e830400451993494058024219903391'
```

Cả hai hash có dạng `0e` theo sau toàn chữ số. PHP thấy đây là *numeric string* dạng ký hiệu khoa
học: `0e462...` nghĩa là 0 × 10^462..., tức bằng 0. `==` so hai numeric string như số, cả hai đều
là 0 nên bằng nhau. Quy tắc này *vẫn đúng ở PHP 8*: PHP 8 chỉ đổi cách so số với chuỗi *không phải
số* (`0 == "abc"` giờ là `false`); hai chuỗi *đều là số* vẫn so như số (`"1e1" == "10"` là `true`).
Vậy nên đừng trả lời "PHP 8 đã sửa magic hash rồi".

Hệ quả: nếu app so `if (md5($input) == $stored_hash)` thì kẻ tấn công thử các chuỗi cho ra hash
`0e...` để khớp với bất kỳ hash `0e...` nào khác. Cách so đúng cho mọi bí mật (token, hash, chữ ký
webhook):

```php
<?php
declare(strict_types=1);

// So chặt, constant-time. Chuỗi bí mật là tham số 1, chuỗi từ người dùng là tham số 2.
if (hash_equals($knownSignature, $userSignature)) {
    // hợp lệ
}
```

`hash_equals()` so từng byte theo kiểu *constant-time*: thời gian chạy không phụ thuộc vào vị trí
byte đầu tiên sai. Nếu dùng `===` (hay `==`) để so chữ ký, thời gian trả lời rò rỉ chỗ khác nhau
đầu tiên, và kẻ tấn công đo thời gian để đoán dần từng byte chữ ký (*timing attack*). ⚠️ Hai chuỗi
khác độ dài thì `hash_equals` trả `false` ngay, nên độ dài của chuỗi bí mật vẫn có thể lộ qua thời
gian; với HMAC/hash độ dài cố định thì điều này không đáng ngại.

Ví dụ xác thực chữ ký webhook đúng cách (raw body, không parse trước):

```php
<?php
declare(strict_types=1);

function verifyWebhook(string $rawBody, string $headerSig, string $secret): bool
{
    $expected = hash_hmac('sha256', $rawBody, $secret);   // tính trên raw body y hệt lúc bên gửi ký
    return hash_equals($expected, $headerSig);            // so constant-time
}
```

⚠️ Phải ký trên *raw body* nhận được, không phải trên mảng đã `json_decode` rồi `json_encode` lại,
vì re-encode đổi khoảng trắng, thứ tự key, unicode escaping và làm HMAC lệch.

#### include/require theo input: LFI và RFI

`include`/`require` với đường dẫn do người dùng điều khiển là lỗ hổng *file inclusion*:

```php
<?php
declare(strict_types=1);

include $_GET['page'] . '.php';   // ⚠️ ?page=../../config  hoặc  ?page=php://filter/convert.base64-encode/resource=config
// (mẹo %00 cắt đuôi '.php' chỉ còn tác dụng ở PHP rất cũ, trước 5.3.4)
```

- *LFI* (Local File Inclusion): include file bất kỳ trên server (đọc `.env`, source, log rồi
  include log đã bị nhét code...).
- *RFI* (Remote File Inclusion): include file từ URL ngoài, chỉ xảy ra khi `allow_url_include=On`
  (mặc định `Off`). Bật lên là cho phép chạy code từ máy kẻ tấn công.

Phòng: whitelist tên trang, không ghép input vào đường dẫn.

```php
<?php
declare(strict_types=1);

$pages = ['home' => 'home.php', 'about' => 'about.php'];
$key   = $_GET['page'] ?? 'home';
include $pages[$key] ?? $pages['home'];   // input chỉ chọn khoá, không tạo đường dẫn
```

Trong `php.ini` (đối chiếu OWASP PHP Configuration Cheat Sheet): `allow_url_fopen=Off` và
`allow_url_include=Off` chặn RFI leo thang từ LFI; `open_basedir` giới hạn thư mục PHP được mở, là
lớp phòng thủ chiều sâu chứ không thay được whitelist. Path traversal ở tầng "download/đọc file"
sửa bằng `basename()` để bỏ phần thư mục trong input.

#### Mass assignment

*Mass assignment* là gán hàng loạt trường từ input HTTP vào model trong một lời gọi. Bug xảy ra khi
input mang một trường nhạy cảm mà lập trình viên không lường:

```php
<?php
declare(strict_types=1);

// ⚠️ Nếu bảng users có cột is_admin, request gửi is_admin=1 sẽ leo thang quyền.
User::create($request->all());
$user->forceFill($request->all())->save();   // forceFill bỏ qua mọi bảo vệ
```

Eloquent chặn mặc định: mọi model được bảo vệ, chỉ trường nằm trong whitelist `$fillable` mới được
gán qua `create`/`fill`/`update`. Ngược lại `$guarded` là blacklist (mặc định `['*']`, tức chặn hết
cho tới khi bạn khai `$fillable`). Trường ngoài `$fillable` bị lặng lẽ bỏ qua. Trong mã nguồn
`GuardsAttributes` của framework 13.x, `isFillable()` kiểm `$fillable` trước, rồi `isGuarded()`;
Laravel 13 còn cho khai bằng attribute `#[Fillable([...])]`/`#[Guarded([...])]` trên class.

Nguyên tắc (theo OWASP Laravel Cheat Sheet):

- Whitelist an toàn hơn blacklist: khai `$fillable`, đừng để `$guarded = []` hay gọi
  `Model::unguard()` (tắt sạch bảo vệ).
- Ở controller, đừng đưa cả `$request->all()` vào model. Dùng `$request->validated()` (dữ liệu đã
  qua FormRequest) hoặc `$request->only([...])` để tự kiểm soát tập trường.
- Tránh `forceFill`/`forceCreate` với input thô, vì chúng bỏ qua guard.
- Bật `Model::preventSilentlyDiscardingAttributes()` ở dev để việc gán trường không có trong
  `$fillable` ném lỗi thay vì im lặng, giúp lộ nhầm lẫn sớm (xem module 2.7 về `shouldBeStrict`).

Đối chiếu: Rails gọi đúng lỗ hổng này là mass assignment và chống bằng strong parameters
(`params.require(...).permit(...)`); tư duy giống hệt: chỉ cho qua tập trường đã liệt kê.

#### Lộ APP_KEY và hậu quả

`APP_KEY` là khoá đối xứng Laravel dùng cho `Crypt`/`encrypt()`, mã hoá cookie (kể cả session
cookie), signed URL, và token reset mật khẩu. `Encrypter` dùng cipher trong `config/app.php`, mặc
định `AES-256-CBC` kèm MAC HMAC-SHA256 (có hỗ trợ AES-GCM, khi đó trường `tag` mới có giá trị):
`encrypt()` mặc định `serialize()` giá trị rồi mã hoá, kết quả là JSON `{iv, value, mac, tag}` base64.

⚠️ Lộ `APP_KEY` là sự cố cực nặng vì hai lớp hậu quả:

1. Kẻ tấn công giải mã và *giả mạo* được mọi cookie, session, dữ liệu `encrypt()`. Vì chúng ký được
   payload hợp lệ, chúng vượt qua kiểm tra MAC.
2. Nối với object injection: khi session/cache lưu bằng PHP serialize, kẻ tấn công có key sẽ tạo
   một cookie/giá trị mã hoá chứa payload serialize của một POP chain. App giải mã thành công (vì
   MAC hợp lệ nhờ key lộ) rồi `unserialize()` payload đó, kích hoạt gadget chain tới RCE. Đây chính
   là lớp CVE Laravel "APP_KEY leak -> RCE" từng gây chấn động.

Laravel 13 vá hướng thứ hai bằng cách đổi mặc định của skeleton sang serialize dạng JSON thay vì
PHP, để dù key lộ vẫn không có object nào được dựng:

- `config/session.php`: `'serialization' => 'json'` (mặc định mới). Comment trong file nói thẳng:
  đặt `'php'` cho phép lưu object PHP trong session nhưng khiến app dễ bị "gadget chain serialization
  attacks nếu APP_KEY lộ".
- `config/cache.php`: `'serializable_classes' => false` (mặc định mới), tức không class PHP nào được
  unserialize từ cache; muốn lưu object thì phải liệt kê class cụ thể vào mảng này.

⚠️ Khi *nâng cấp* app cũ lên 13 và đồng bộ config: đổi session serialization từ `php` sang `json` sẽ
làm mất hiệu lực mọi session đang hoạt động (người dùng phải đăng nhập lại). Cân nhắc: giữ `php` để
không rớt session, hoặc chuyển `json` và chấp nhận re-auth để an toàn hơn.

Xử lý khi lộ key: coi như secret cấp cao nhất, xoay vòng ngay bằng `php artisan key:generate`. Đưa
key cũ vào `APP_PREVIOUS_KEYS` (danh sách phân tách bằng dấu phẩy) để dữ liệu cũ vẫn giải mã được
trong thời gian chuyển: `Encrypter::decrypt` thử key hiện tại trước, thất bại thì thử lần lượt các
key cũ; còn `encrypt` luôn dùng key hiện tại.

#### Debug mode và lộ cấu hình

⚠️ `APP_DEBUG=true` trên production là một trong những cấu hình sai nguy hiểm nhất: trang lỗi debug
của Laravel hiển thị stack trace, đoạn code, chi tiết request và lỗi. Chỉ cần kích một exception là
kẻ tấn công thấy được cấu trúc code và có thể cả giá trị cấu hình nhạy cảm. Docs Laravel cảnh báo
thẳng: production phải để `APP_DEBUG=false`, nếu không là "risk exposing sensitive configuration
values".

Ở tầng PHP thuần, tương đương là `display_errors`: production đặt `display_errors=Off`,
`log_errors=On`, ghi ra file ngoài webroot (OWASP PHP Configuration Cheat Sheet). Thêm
`expose_php=Off` để không lộ phiên bản PHP qua header `X-Powered-By`. Laravel tự giấu một số trường
nhạy cảm khi flash input lại form nhờ mảng `$dontFlash` trong exception handler (`password`,
`current_password`, `password_confirmation`).

#### Những chỗ khác cần nhớ

- Blade `{{ $x }}` tự escape HTML; `{!! $x !!}` *không* escape, đưa input người dùng vào đó là XSS.
- Upload file: kiểm MIME theo *nội dung* (`finfo`, rule `mimes:jpg,png` của Laravel), không tin
  extension hay header `Content-Type` do client gửi. Đặt tên ngẫu nhiên, lưu ngoài webroot hoặc lên
  S3. ⚠️ Cấu hình Nginx chỉ được chạy PHP cho `index.php`, tuyệt đối không cho thư mục upload; nếu
  không, upload `shell.php` (hoặc ảnh nhét code PHP) rồi truy cập là chạy được. ⚠️ File SVG chứa
  được JavaScript, phục vụ trực tiếp trên domain của bạn là XSS.
- Mật khẩu: `password_hash()` (mặc định bcrypt, cost mặc định tăng từ 10 lên **12 kể từ PHP 8.4**;
  hoặc argon2id), `password_verify()`, `password_needs_rehash()` để hash lại khi đổi cost. ⚠️ bcrypt
  cắt mật khẩu ở 72 byte. Không dùng md5/sha1 cho mật khẩu.
- Số ngẫu nhiên cho bảo mật (token, OTP): `random_bytes()`, `random_int()`, `Str::random()`. Không
  dùng `rand()`, `mt_rand()`, `uniqid()` vì đoán được.
- `extract()`, biến-biến `$$var`, `eval()`: biến input thành biến hoặc code, tránh.
- `shell_exec`/`exec` với input: bọc `escapeshellarg()`, hoặc dùng Symfony `Process` với tham số
  dạng mảng (không qua shell).
- `#[\SensitiveParameter]` (PHP 8.2) gắn lên tham số nhạy cảm (mật khẩu, key) để giá trị bị che
  trong stack trace khi ghi log; `Encrypter::encrypt` của Laravel dùng attribute này.
- `composer audit`: chạy trong CI để chặn dependency có advisory hoặc bị bỏ rơi. Lệnh gọi
  Packagist API, trả exit code 0 nếu sạch, 1 nếu có vấn đề (Composer 2.10+ chuẩn hoá còn 0/1).
  Composer 2.9+ có *version blocking*: mặc định *chặn cài* phiên bản dính advisory (`block-insecure`
  bật sẵn) khi `update`/`require`; 2.10 gộp cấu hình vào khối `config.policy` mới, đồng thời thêm
  chặn gói bị đánh dấu malware. Deploy production: `composer install --no-dev -o` (chỉ đọc lock, bỏ
  dev dependency, tối ưu autoloader). Xem module 1.5 về `composer.lock`.

Đối chiếu OWASP Top 10 (bản 2021): gần như mọi mục trên ánh xạ vào Top 10, nhưng dưới lớp vỏ đặc
thù PHP: object injection (CWE-502) và mass assignment (CWE-915) = A08 Software and Data Integrity
Failures (A08 gộp mục Insecure Deserialization của bản 2017); debug mode = A05 Security
Misconfiguration; magic hash/`==` dẫn tới bypass xác thực = A07 Identification & Authentication
Failures; LFI/RFI = A03 Injection (CWE-98), path traversal = A01 Broken Access Control;
`composer audit` = A06 Vulnerable & Outdated Components. Giá trị
của việc học riêng phần PHP là hiểu *tại sao ngôn ngữ này* dễ dính từng lỗi.

**Tóm tắt nhanh**
- `unserialize()` dữ liệu ngoài = object injection: magic method (`__wakeup`/`__destruct`) khởi động
  POP chain tới RCE; phpggc có sẵn chain cho Laravel. Dùng JSON, hoặc `allowed_classes => false`.
- `==` so hash/token bị magic hash (`0e...` = 0) qua mặt; PHP 8 *không* sửa ca hai chuỗi số. Luôn
  `hash_equals()` (constant-time) cho token và chữ ký webhook, ký trên raw body.
- Mass assignment: khai `$fillable`, dùng `validated()`/`only()`, không `unguard`/`forceFill` input
  thô. include theo input = LFI/RFI: whitelist, `allow_url_include=Off`.
- Lộ `APP_KEY` = giả mạo cookie/session và, khi serialize dạng `php`, RCE qua gadget chain. Laravel
  13 mặc định session `json` và cache `serializable_classes=false`; xoay key, dùng `APP_PREVIOUS_KEYS`.
- Production: `APP_DEBUG=false`, `display_errors=Off`; `password_hash` (cost bcrypt 12 từ PHP 8.4);
  `random_int`/`random_bytes`; `composer audit` trong CI, `install --no-dev -o` khi deploy.

**Nguồn**: [PHP: unserialize](https://www.php.net/manual/en/function.unserialize.php) ·
[PHP: hash_equals](https://www.php.net/manual/en/function.hash-equals.php) ·
[PHP: password_hash](https://www.php.net/manual/en/function.password-hash.php) ·
[RFC: phar stop autoloading metadata](https://wiki.php.net/rfc/phar_stop_autoloading_metadata) ·
[PHP 8.5 UPGRADING](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) (soft-deprecate `__wakeup`) ·
[phpggc](https://github.com/ambionics/phpggc) ·
[OWASP: Laravel Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html) ·
[OWASP: PHP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html) ·
[OWASP: Deserialization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html) ·
[Laravel: Encryption](https://laravel.com/docs/13.x/encryption) ·
[Laravel 13 Upgrade Guide](https://laravel.com/docs/13.x/upgrade) (session/cache serialization) ·
[Composer: audit](https://getcomposer.org/doc/03-cli.md#audit) ·
mã nguồn `laravel/framework` 13.x (`Encryption/Encrypter.php`, `Eloquent/Concerns/GuardsAttributes.php`)

---

### 3.8 So sánh kiến trúc: Laravel, Symfony và ngôn ngữ khác

Module này trả lời: khi được hỏi "vì sao team chọn Laravel" hay "Laravel hay Symfony cho dự án
này", làm sao nói được điểm mạnh *và điểm yếu thật* của công cụ mình dùng hằng ngày, và đặt PHP
cạnh Java/Go ở mức kiến trúc runtime. Câu này kiểm tra độ chín: người mới khen framework của mình
vô điều kiện, người senior chỉ ra được đánh đổi.

#### Laravel so với Symfony

Hai framework PHP lớn nhất, khác nhau ở triết lý chứ không phải ở "cái nào tốt hơn".

| Tiêu chí | Laravel | Symfony |
|---|---|---|
| Triết lý | Convention over configuration, tối ưu tốc độ phát triển, "magic" có chủ đích | Tường minh, component tách rời, cấu hình rõ ràng |
| ORM mặc định | Eloquent (Active Record) | Doctrine (Data Mapper + Unit of Work) |
| Container | Resolve lúc runtime bằng reflection | Compile container thành PHP code, kiểm wiring lúc build |
| Truy cập service | Facade, helper toàn cục, DI | DI + autowiring, hạn chế truy cập container trực tiếp |
| Event | Observer/listener, discovery tự động | EventDispatcher với priority số, stopPropagation, subscriber |
| Nhịp phát hành | Major mỗi năm (v13 = 03/2026) | Major 2 năm/lần, có LTS |

*ORM: Active Record so với Data Mapper.* Eloquent theo *Active Record*: model vừa mang dữ liệu vừa
biết cách tự lưu (`$user->save()`), một model ánh xạ một bảng. Viết nhanh, ít lớp, nhưng domain
object bị dính chặt vào tầng DB, khó giữ sạch. Doctrine theo *Data Mapper*: entity là object PHP
thuần không biết gì về DB; một lớp riêng (EntityManager) lo việc ánh xạ và lưu. Tách bạch hơn, hợp
domain phức tạp, nhưng nhiều khái niệm và code hơn.

*Unit of Work* (cơ chế cốt lõi của Doctrine): trong một phiên, EntityManager giữ một *identity map*
(mỗi entity theo id chỉ có đúng một instance trong phiên) và chụp *snapshot* trạng thái ban đầu của
mỗi entity đã nạp. Bạn cứ sửa object PHP như bình thường; tới `flush()`, Doctrine duyệt identity
map, so snapshot với giá trị hiện tại, tính ra *changeset*, rồi sinh SQL theo thứ tự INSERT ->
UPDATE -> DELETE (tôn trọng ràng buộc khoá ngoại) và gửi xuống trong một transaction. Hệ quả: chỉ
cột thay đổi mới vào câu UPDATE, và nhiều thay đổi gộp thành một đợt ghi. Đối chiếu với Eloquent:
`save()` ghi ngay từng model, không có khái niệm gom cả phiên; đơn giản hơn nhưng bạn tự lo thứ tự
và gom nhóm.

*Container: runtime so với compile.* Laravel `Container::build()` dùng `ReflectionClass` đọc
constructor lúc request chạy tới để tự dựng dependency. Linh hoạt (bind runtime, contextual
binding) nhưng lỗi wiring (thiếu binding, sai kiểu) chỉ lộ khi request chạm tới đoạn code đó.
Symfony *compile* container: lúc build, nó đọc toàn bộ định nghĩa service, chạy một chuỗi *compiler
pass* (kiểm circular reference, resolve tham số, loại service không dùng, tối ưu), rồi *dump* ra một
class PHP chứa sẵn code tạo từng service, cache vào `var/cache/`. Vì vậy binding thiếu hoặc sai kiểu
bị bắt *lúc build/deploy*, không phải lúc production chạy tới; và request không tốn chi phí phản
chiếu. Service để *private* mặc định còn cho compiler inline/loại bỏ để nhanh hơn và báo lỗi tham
chiếu sai sớm. Đây là lý do chính khi nói "Symfony bắt lỗi wiring sớm hơn".

*Event.* Laravel: listener gắn với event, có thể auto-discovery, dừng chain bằng `return false`,
listener queue được qua `ShouldQueue`. Symfony EventDispatcher: listener có *priority* (số nguyên,
cao chạy trước), gọi `stopPropagation()` để chặn, và có *event subscriber* (class tự khai mình nghe
event nào). Cùng mô hình observer, Symfony cho kiểm soát thứ tự tường minh hơn.

Điểm hay nhắc: Laravel *dùng lại* nhiều component của Symfony (HttpFoundation cho request/response,
Console, Mailer, Routing bên dưới...). Không phải hai hệ tách rời hoàn toàn; Laravel là lớp trải
nghiệm dev đặt trên nền một phần Symfony.

*Chọn thế nào* (trả lời phỏng vấn): chọn theo đội và domain, không theo "framework nào xịn hơn".
- Domain nhiều *invariant* (quy tắc nghiệp vụ luôn phải đúng, ví dụ "tổng tiền đơn = tổng các dòng"),
  cần giữ entity sạch: Data Mapper của Doctrine hợp hơn vì entity không dính logic lưu DB.
- CRUD, admin, startup cần ra sản phẩm nhanh, đội quen Laravel: Laravel nhanh hơn nhiều.
- Điểm yếu thật của Laravel cần dám nói: "magic" (facade, resolve runtime) làm khó truy vết và test
  nếu lạm dụng; Active Record kéo domain dính DB; lỗi wiring lộ muộn. Vẫn làm *DDD* được trong
  Laravel nếu có kỷ luật tách domain khỏi Eloquent, thêm service layer và PHPStan level cao
  (xem 15-architecture.md).

#### PHP-FPM so với Node, Go, Java ở mức kiến trúc

Khác biệt gốc rễ nhất giữa PHP và các runtime kia là *mô hình vòng đời process cho mỗi request*.

```
PHP-FPM (share-nothing)          Node / Go / Java (process sống lâu)
------------------------          -----------------------------------
request -> [worker] -> response   requests --> [ 1 process ]
           bootstrap lại               |         event loop / goroutine / thread
           chạy, rồi VỨT state         |         giữ state trong RAM giữa các request
                                       v
mỗi request bắt đầu từ số 0       kết nối, cache, singleton nằm sẵn trong bộ nhớ
```

*PHP-FPM* (FastCGI Process Manager) chạy một pool worker process. Mỗi request HTTP được gán cho một
worker; worker *khởi tạo lại toàn bộ* (nạp autoloader, dựng container, kết nối...), chạy xong thì
dọn sạch bộ nhớ request và trở về pool chờ request kế. Đây là mô hình *share-nothing*: không có
state PHP nào sống qua ranh giới request (ngoại lệ: OPcache giữ bytecode đã biên dịch, APCu giữ
cache trong shared memory, và persistent connection). Ưu điểm lớn: một request rò bộ nhớ hay để lại rác không lây sang request
khác, nên PHP "tự lành" và cực dễ suy luận. Nhược điểm: phải bootstrap lại mỗi lần, và không giữ
được state trong tiến trình (cache dùng chung phải ra Redis/DB, hoặc APCu nếu chỉ cần trong một máy). Song song đạt bằng *nhiều
process* (`pm.max_children`), không bằng nhiều luồng trong một process (xem module 2.2/3.4).

*Node.js*: một process, *event loop* đơn luồng, I/O bất đồng bộ. State sống trong RAM giữa các
request, nên nhanh và giữ được cache/connection sẵn, nhưng lập trình viên phải cẩn thận: một
exception không bắt hoặc một biến toàn cục bẩn ảnh hưởng mọi request sau; CPU-bound chặn cả loop.

*Go*: một process, mỗi request một *goroutine* (luồng nhẹ do runtime lập lịch trên vài OS thread).
Chia sẻ state qua biến package/struct server, đồng bộ bằng channel/mutex. Song song thật trên nhiều
core trong cùng một process; đây là điểm PHP-FPM không có.

*Java/Spring*: JVM sống rất lâu, thread pool (từ Java 21 thêm *virtual thread* nhẹ như goroutine).
State giữ trong singleton bean; JIT của JVM ấm dần nên càng chạy càng nhanh. Đổi lại: khởi động
chậm, tốn RAM, và phải xử lý an toàn luồng (thread safety) mà PHP share-nothing gần như miễn nhiễm.

PHP thu hẹp khoảng cách bằng *worker sống lâu*: Octane (Swoole/RoadRunner/FrankenPHP) giữ app đã
bootstrap trong RAM giữa các request, biến PHP thành mô hình giống Node/Go về hiệu năng boot, và
kéo theo đúng rủi ro của mô hình đó (state leak giữa request), phải sửa các singleton mang state
(xem module 3.5).

Bảng đối chiếu tổng:

| Khía cạnh | PHP/Laravel (FPM) | Node.js | Go | Java/Spring |
|---|---|---|---|---|
| Mô hình chạy | process/request, share-nothing | 1 process, event loop | 1 process, goroutine/request | JVM lâu, thread pool (virtual thread 21+) |
| State giữa request | Không (trừ Octane/worker) | Có, trong RAM | Có, biến package/struct | Có, singleton bean |
| Song song | Nhiều process | Đơn luồng + async I/O | Goroutine trên nhiều core | Thread/virtual thread |
| Cô lập lỗi | Rất mạnh (mỗi request sạch) | Yếu (loop chung) | Trung bình (panic recover) | Trung bình |
| Bộ nhớ | Refcount + cycle collector | Tracing GC (V8) | Tracing GC concurrent | Tracing GC chia thế hệ |
| Lỗi | Exception, không checked | Exception + reject/callback | `error` là giá trị trả về | Checked + unchecked |
| DI | Container runtime, reflection | Thủ công / thư viện | Truyền tay qua constructor | IoC container, proxy |
| ORM | Eloquent (Active Record) | Prisma/TypeORM | database/sql, sqlc, GORM | JPA/Hibernate (Data Mapper) |
| Job nền | Queue + worker process | Bull + worker | goroutine + channel | Executor, Spring Batch |
| Khởi động | Nhanh, nhưng lặp mỗi request | Nhanh, một lần | Nhanh, một lần | Chậm, JIT ấm dần |

Vài chi tiết dễ ghi điểm khi so ngôn ngữ:
- Array PHP giữ thứ tự chèn (nó là ordered hashtable). `HashMap` của Java và `map` của Go *không*
  đảm bảo thứ tự.
- Enum PHP (8.1) gần enum Java (có method, implement interface được) hơn là `iota` của Go (chỉ là
  hằng số nguyên tăng dần).
- Xử lý lỗi: Go coi `error` là giá trị trả về phải kiểm từng lời gọi (đối chiếu với exception của
  PHP/Java bung lên trên); đây là khác biệt triết lý hay được hỏi vặn.

**Tóm tắt nhanh**
- Laravel = Active Record + container runtime (reflection) + facade, tối ưu tốc độ dev; Symfony =
  Data Mapper (Doctrine) + container compile + DI tường minh, tối ưu domain phức tạp và bắt lỗi sớm.
- Unit of Work: Doctrine gom cả phiên, so snapshot rồi flush theo thứ tự INSERT/UPDATE/DELETE trong
  một transaction; Eloquent `save()` ghi ngay từng model.
- Container compile của Symfony bắt lỗi wiring lúc build và bỏ chi phí reflection lúc request; đó là
  lý do lỗi lộ sớm hơn Laravel. Laravel dùng lại nhiều component Symfony.
- Chọn theo đội + domain, nói được điểm yếu thật của Laravel (magic khó test, Active Record dính DB).
- PHP-FPM = share-nothing, mỗi request bootstrap lại và vứt state: cực dễ suy luận, cô lập lỗi mạnh,
  nhưng không giữ state trong process (Octane mới có, kèm rủi ro leak). Node/Go/Java giữ state trong
  process sống lâu, đổi lại phải lo thread safety và state bẩn.

**Nguồn**: [Symfony: Service Container](https://symfony.com/doc/current/service_container.html) ·
[Symfony: Compiling the Container](https://symfony.com/doc/current/service_container/compiler_passes.html) ·
[Symfony: EventDispatcher](https://symfony.com/doc/current/components/event_dispatcher.html) ·
[Doctrine: Unit of Work](https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/unitofwork.html) ·
[Laravel: Container](https://laravel.com/docs/13.x/container) ·
[Laravel: Events](https://laravel.com/docs/13.x/events) ·
[Laravel: Eloquent](https://laravel.com/docs/13.x/eloquent) ·
mã nguồn `laravel/framework` 13.x (`Container/Container.php`)
