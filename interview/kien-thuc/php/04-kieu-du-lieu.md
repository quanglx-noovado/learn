# Chương 04. Kiểu dữ liệu và hệ thống kiểu

> [← Mục lục](README.md) · [← Chương 03: Cú pháp cơ bản, biến và hằng](03-cu-phap-bien-hang.md) · [Chương 05: Chuỗi (string) →](05-chuoi.md)

**Bạn sẽ học được:**

- PHP có những kiểu dữ liệu nào, mỗi kiểu lưu gì và có giới hạn gì (vì sao `PHP_INT_MAX + 1` thành
  float, vì sao `0.1 + 0.2` không bằng `0.3`).
- Cách khai báo kiểu cho tham số, giá trị trả về, property: nullable, union, intersection, DNF,
  `mixed`, `void`, `never`, `static`.
- *Type juggling*: PHP tự đổi kiểu một giá trị khi nào và theo luật gì; ép kiểu tường minh (cast);
  luật *numeric string* của PHP 8.
- Khác nhau giữa `==` và `===`, và PHP 8 đã đổi gì trong phép so sánh lỏng so với PHP 7.
- `declare(strict_types=1)` thật sự bật cái gì, áp dụng ở đâu và không áp dụng ở đâu.
- Cách xem kiểu của một giá trị: `var_dump`, `gettype`, `get_debug_type`, các hàm `is_*`.

**Cần biết trước:** [Chương 01](01-php-la-gi.md) (chạy được một file PHP) và
[Chương 03](03-cu-phap-bien-hang.md) (biến, `var_dump`, `isset`/`empty`).

Mọi ví dụ trong chương là file PHP hoàn chỉnh, lưu thành file rồi chạy bằng `php ten_file.php`. Không
cài PHP thì chạy bằng Docker, đứng trong thư mục chứa file:
`docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten_file.php`. Output ghi trong comment đã
được chạy thật trên PHP 8.5; chỗ nào khác giữa các phiên bản thì ghi rõ.

## 1. Kiểu dữ liệu là gì và PHP quản lý kiểu ra sao

### 1.1 Kiểu dữ liệu là gì

Mọi giá trị trong chương trình đều thuộc một *kiểu dữ liệu* (data type): số nguyên, số thực, chuỗi
chữ, danh sách... Kiểu quyết định hai điều:

1. Giá trị được lưu thế nào trong bộ nhớ (một số nguyên 64 bit, một dãy byte, một bảng băm...).
2. Những phép toán nào làm được với giá trị đó, và kết quả là gì.

Cùng ký tự `5` nhưng khác kiểu thì hành xử khác hẳn:

```php
<?php
declare(strict_types=1);

var_dump(5 + 5);     // in ra: int(10)       cộng hai số nguyên
var_dump("5" . "5"); // in ra: string(2) "55" nối hai chuỗi
var_dump("5" + 5);   // in ra: int(10)       PHP tự đổi "5" thành số rồi mới cộng
```

Dòng thứ ba là đặc trưng của PHP: khi một phép toán cần kiểu khác với kiểu đang có, PHP cố *tự đổi
kiểu* giá trị cho hợp (gọi là *type juggling*, mục 12). Cơ chế này tiện, nhưng cũng là nguồn gốc của
phần lớn bug "kỳ lạ" trong PHP. Hiểu kiểu dữ liệu chính là hiểu khi nào PHP tự đổi kiểu và đổi theo
luật nào. Để ý file trên có `declare(strict_types=1)` mà dòng ba vẫn chạy: strict mode không áp dụng
cho toán tử (mục 14).

### 1.2 Biến không có kiểu, giá trị mới có kiểu

PHP là ngôn ngữ *dynamically typed* (kiểu động): bạn không khai báo kiểu khi tạo biến, và một biến có
thể lần lượt chứa giá trị thuộc nhiều kiểu khác nhau. Nói chính xác: **biến không có kiểu, giá trị
mới có kiểu**. Biến chỉ là cái tên trỏ tới một giá trị; hỏi "biến `$x` kiểu gì" thực ra là hỏi "giá
trị `$x` đang chứa thuộc kiểu gì".

```php
<?php
declare(strict_types=1);

$x = 42;
var_dump($x);   // in ra: int(42)
$x = "bốn hai";
var_dump($x);   // in ra: string(9) "bốn hai"   (9 byte vì "ố" chiếm 3 byte UTF-8, xem chương 05)
$x = [4, 2];
var_dump($x);   // in ra: array(2) { [0]=> int(4) [1]=> int(2) }  (var_dump in nhiều dòng, ở đây gộp lại)
$x = null;
var_dump($x);   // in ra: NULL
```

Đối chiếu: Java và Go là ngôn ngữ *statically typed* (kiểu tĩnh). Biến có kiểu cố định, trình biên
dịch kiểm tra trước khi chạy: `int x = 42; x = "hi";` trong Java, hay `var x int = 42; x = "hi"`
trong Go, đều không biên dịch được.

PHP vẫn cho bạn "cam kết" kiểu ở một số chỗ bằng *type declaration* (khai báo kiểu): tham số hàm,
giá trị trả về, property của class, hằng của class (mục 11). Khác Java/Go ở chỗ PHP kiểm tra cam kết
đó **lúc chạy** (runtime), đúng lúc giá trị đi qua chỗ khai báo. Manual mô tả: PHP dùng hệ kiểu
*nominal* (kiểu xác định theo tên class/interface), quan hệ kiểu con được kiểm lúc biên dịch, còn
việc xác minh giá trị đúng kiểu thì diễn ra động lúc chạy.

```
                     PHP KHÔNG kiểm tra kiểu        PHP CÓ kiểm tra kiểu (lúc chạy)
                     ─────────────────────────      ─────────────────────────────────
$x = "5";            biến cục bộ                    function f(int $x): string { ... }
$arr[] = 1.5;        phần tử array                  public int $count;
$obj->dynamic = 1;   (nếu class cho phép)           const int MAX = 10;  (hằng class, 8.3)
```

### 1.3 Bản đồ các kiểu của PHP

Theo manual, mọi biểu thức trong PHP mang một trong các kiểu dựng sẵn sau: `null`, `bool`, `int`,
`float`, `string`, `array`, `object`, `callable`, `resource`. Cách nhóm dễ nhớ:

| Nhóm | Kiểu | Chứa gì | Đọc ở |
|---|---|---|---|
| *Scalar* (vô hướng: một giá trị đơn) | `bool` | `true` hoặc `false` | mục 2 |
| | `int` | số nguyên có dấu | mục 3 |
| | `float` | số thực dấu phẩy động | mục 4 |
| | `string` | dãy byte | mục 5 |
| Ghép (compound) | `array` | bảng key/value có thứ tự | mục 6 |
| | `object` | thể hiện (instance) của một class | mục 7 |
| Đặc biệt | `null` | chỉ một giá trị: `null` | mục 8 |
| | `resource` | "tay cầm" tới tài nguyên bên ngoài (file đang mở...) | mục 9 |
| Mô tả khả năng | `callable` | giá trị gọi được như hàm | mục 10 |
| | `iterable` | `array` hoặc object duyệt được bằng `foreach` | mục 10 |

Manual định nghĩa: một giá trị là *scalar* nếu thuộc kiểu `int`, `float`, `string` hoặc `bool`.
`null` không phải scalar (`is_scalar(null)` là `false`).

Hai dòng cuối hơi khác các dòng trên. Lúc chạy, không có giá trị nào "thuộc kiểu callable" theo
nghĩa `get_debug_type()` trả về `"callable"`: một callable cụ thể luôn là một `string` (tên hàm), một
`array` (object hoặc tên class, kèm tên method), hoặc một `object` (ví dụ `Closure`). `callable` mô
tả *khả năng được gọi* của giá trị. Tương tự, `iterable` là *type alias* (bí danh kiểu) của `array|Traversable`.

Ngoài ra còn một nhóm kiểu **chỉ dùng trong khai báo kiểu**, không giá trị nào "là" chúng: `mixed`,
`void`, `never`, `self`/`parent`/`static`, `false`/`true` (đứng riêng), và các cách ghép kiểu
`?T`, `A|B`, `A&B`, `(A&B)|C`. Mục 11 đi qua từng cái.

### 1.4 Xem kiểu của một giá trị

PHP cho bốn công cụ, mỗi cái hợp với một việc:

- `var_dump($v)`: in kiểu kèm giá trị, đi sâu vào array/object. Dùng khi debug (chi tiết cách in ở
  [chương 03](03-cu-phap-bien-hang.md)).
- `get_debug_type($v)` (PHP 8.0): trả tên kiểu dạng chuỗi, đúng tên bạn viết trong khai báo kiểu
  (`int`, `float`, `bool`, `null`), với object thì trả **tên class**.
- `gettype($v)`: hàm cũ, trả tên kiểu theo lối lịch sử (`"integer"`, `"double"`, `"boolean"`,
  `"NULL"`), với object chỉ trả `"object"`.
- Các hàm `is_*`: trả `bool`, dùng để **kiểm tra** trong code: `is_int`, `is_float`, `is_string`,
  `is_bool`, `is_array`, `is_object`, `is_null`, `is_resource`, `is_scalar`, `is_numeric`,
  `is_callable`, `is_iterable`, `is_countable`. Với class thì dùng `instanceof`.

So sánh `gettype` và `get_debug_type` trên cùng các giá trị:

```php
<?php
declare(strict_types=1);

enum Suit { case Hearts; }   // enum có từ PHP 8.1 (chương 10)

$f = fopen('php://memory', 'r');   // mở một stream trong RAM: tạo ra một resource
$values = [
    'null'      => null,
    'bool'      => true,
    'int'       => 42,
    'float'     => 3.14,
    'string'    => 'xin chào',
    'array'     => [1, 2],
    'stdClass'  => new stdClass(),
    'closure'   => fn (int $n): int => $n * 2,
    'enum'      => Suit::Hearts,
    'anonymous' => new class {},
    'resource'  => $f,
];
foreach ($values as $label => $v) {
    printf("%-10s gettype=%-10s get_debug_type=%s\n", $label, gettype($v), get_debug_type($v));
}
fclose($f);
printf("%-10s gettype=%-10s get_debug_type=%s\n", 'closed', gettype($f), get_debug_type($f));
var_dump(is_resource($f));
```

Output (PHP 8.5):

```
null       gettype=NULL       get_debug_type=null
bool       gettype=boolean    get_debug_type=bool
int        gettype=integer    get_debug_type=int
float      gettype=double     get_debug_type=float
string     gettype=string     get_debug_type=string
array      gettype=array      get_debug_type=array
stdClass   gettype=object     get_debug_type=stdClass
closure    gettype=object     get_debug_type=Closure
enum       gettype=object     get_debug_type=Suit
anonymous  gettype=object     get_debug_type=class@anonymous
resource   gettype=resource   get_debug_type=resource (stream)
closed     gettype=resource (closed) get_debug_type=resource (closed)
bool(false)
```

Mấy điều rút ra:

- Closure và enum case đều là object (`gettype` nói `"object"`), `get_debug_type` cho biết class cụ
  thể. Thông báo lỗi kiểu của PHP 8 dùng đúng các tên này (`must be of type int, string given`).
- `gettype` trả `"double"` cho float "vì lý do lịch sử" (lời manual). Tiện biết thêm: trong mã C của
  engine, giá trị float được lưu ở một trường kiểu `double` của C.
- Resource đã đóng vẫn mang kiểu resource (`"resource (closed)"`), nhưng `is_resource()` trả `false`.

⚠️ Đừng kiểm tra kiểu bằng cách so chuỗi của `gettype()`. `gettype(9.99) === 'float'` luôn là
`false` vì `gettype` trả `"double"`. Dùng `is_float()`, hoặc `get_debug_type()` khi cần tên kiểu.

⚠️ `is_numeric` khác `is_int`/`is_float`. `is_int("42")` là `false` (giá trị là chuỗi), còn
`is_numeric("42")` là `true` (chuỗi trông như số, mục 12.2). Dữ liệu từ form HTML, query string,
cookie luôn là **chuỗi** (hoặc array chứa chuỗi, khi tên tham số có `[]`), nên `is_int($_GET['id'])`
không bao giờ là `true`.

```php
<?php
declare(strict_types=1);

var_dump(is_int("42"), is_numeric("42"));          // in ra: bool(false) bool(true)
var_dump(is_scalar(null), is_scalar(1.5));          // in ra: bool(false) bool(true)
var_dump(is_callable('strlen'), is_callable('khong_co_ham_nay')); // in ra: bool(true) bool(false)
var_dump(is_iterable([1]), is_iterable('abc'));     // in ra: bool(true) bool(false)
```

### 1.5 Bên trong engine: mỗi giá trị mang một nhãn kiểu

Vì biến không có kiểu, engine phải lưu kiểu **cùng với giá trị**. Trong Zend Engine (phần lõi chạy
code PHP, [chương 02](02-php-chay-nhu-the-nao.md)), mỗi giá trị nằm trong một cấu trúc C tên là
*zval*: một phần chứa giá trị, một phần chứa nhãn kiểu. Tên các nhãn trong mã nguồn php-src
(`Zend/zend_types.h`) là `IS_NULL`, `IS_FALSE`, `IS_TRUE`, `IS_LONG` (int), `IS_DOUBLE` (float),
`IS_STRING`, `IS_ARRAY`, `IS_OBJECT`, `IS_RESOURCE`...

```
 $a = 42;                       $b = "xin chào";
 ┌─────────────────────┐        ┌─────────────────────┐      ┌──────────────────────────────┐
 │ zval                │        │ zval                │      │ zend_string                  │
 │  value: 42          │        │  value: con trỏ ────┼────► │  refcount, độ dài 9,         │
 │  type : IS_LONG     │        │  type : IS_STRING   │      │  các byte "xin chào"         │
 └─────────────────────┘        └─────────────────────┘      └──────────────────────────────┘
   int, float, bool, null           string, array, object: zval chỉ giữ con trỏ tới vùng nhớ
   nằm gọn trong zval               riêng, vùng đó có bộ đếm tham chiếu (refcount)
```

Hai hệ quả bạn sẽ gặp lại:

- Khi PHP "đổi kiểu" một giá trị để so sánh hay tính toán, nó tạo **giá trị tạm** kiểu mới; giá trị
  gốc không đổi. Manual: "When a value needs to be interpreted as a different type, the value itself
  does not change types."
- `bool` không có một nhãn `IS_BOOL` mà có hai nhãn `IS_FALSE` và `IS_TRUE`: kiểu và giá trị được
  mã hoá chung trong nhãn.

Chi tiết zval, refcount, copy-on-write ở [chương 19](19-ben-trong-engine.md). Chương này chỉ cần nhớ:
**kiểu đi theo giá trị**.

## 2. bool: đúng hay sai

### 2.1 Giá trị và cú pháp

`bool` chỉ có hai giá trị: `true` và `false`. Đây là hai hằng, không phân biệt hoa thường (`True`,
`TRUE` vẫn chạy), nhưng chuẩn code PSR-12/PER yêu cầu viết thường.

Bạn hiếm khi gõ `true`/`false` trực tiếp. Giá trị bool thường đến từ phép so sánh (`$a > $b`), toán
tử logic (`&&`, `||`, `!`), hoặc hàm kiểm tra (`is_int()`, `in_array()`...), rồi được đưa vào `if`,
`while`, toán tử ba ngôi.

### 2.2 Đổi sang bool: thuộc lòng danh sách falsy

Khi một giá trị không phải bool đứng ở chỗ cần bool (`if ($x)`, `!$x`, `$x && $y`), PHP đổi nó sang
bool. Ép tường minh thì viết `(bool) $x` hoặc `boolval($x)`.

Theo manual, các giá trị sau đổi thành `false`, gọi chung là *falsy*:

| Giá trị | Ghi chú |
|---|---|
| `false` | |
| `0` | số nguyên không |
| `0.0`, `-0.0` | số thực không |
| `""` | chuỗi rỗng |
| `"0"` | chuỗi đúng một ký tự `0` |
| `[]` | array không có phần tử |
| `null` | kể cả biến chưa gán hoặc đã `unset()` |
| object nội bộ tự định nghĩa cách ép sang bool | manual lấy ví dụ object GMP mang giá trị 0 |

Mọi giá trị khác là *truthy* (đổi thành `true`), kể cả resource và `NAN`. Những trường hợp hay đoán
sai:

```php
<?php
declare(strict_types=1);

$tests = [
    'false' => false, '0' => 0, '0.0' => 0.0, '-0.0' => -0.0,
    '""' => "", '"0"' => "0", '[]' => [], 'null' => null,
    '-1' => -1, '"0.0"' => "0.0", '" "' => " ", '"00"' => "00",
    '"false"' => "false", '[0]' => [0], 'new stdClass' => new stdClass(),
];
foreach ($tests as $label => $v) {
    printf("%-14s => %s\n", $label, var_export((bool) $v, true));
}
```

Output:

```
false          => false
0              => false
0.0            => false
-0.0           => false
""             => false
"0"            => false
[]             => false
null           => false
-1             => true
"0.0"          => true
" "            => true
"00"           => true
"false"        => true
[0]            => true
new stdClass   => true
```

⚠️ Chuỗi `"0"` là falsy nhưng `"0.0"`, `"00"`, `" "` (một dấu cách), `"false"` đều truthy. Quy tắc
cho chuỗi chỉ có hai ngoại lệ: `""` và `"0"`. PHP **không** xét xem chuỗi có "trông giống số 0" hay
không.

⚠️ `-1` là truthy, như mọi số khác 0 (manual có hẳn một khung cảnh báo cho điều này).

⚠️ Object luôn truthy, kể cả object không có property nào. Muốn biết "có dữ liệu không" thì kiểm tra
cụ thể (`count($arr) > 0`, `$obj->items !== []`), đừng dựa vào `if ($obj)`.

⚠️ Từ PHP 8.5, đổi `NAN` sang bool (kể cả ngầm trong `if (NAN)`) vẫn ra `true` nhưng kèm
`Warning: unexpected NAN value was coerced to bool`. PHP 8.4 trở về trước không báo gì.

Đối chiếu: Python cũng coi list rỗng là falsy nhưng chuỗi `"0"` là truthy; JavaScript coi `"0"` là
truthy và `[]` (array rỗng) cũng truthy. Mỗi ngôn ngữ một bảng, đừng mang thói quen từ ngôn ngữ khác
sang. Java và Go không tự đổi gì sang boolean: `if (1)` là lỗi biên dịch.

### 2.3 Cạm bẫy kinh điển: hàm trả về `int|false`

Nhiều hàm có sẵn trả về **vị trí hoặc số lượng** (một `int`, có thể là `0`) khi thành công, và
`false` khi thất bại. `strpos()` là ví dụ nổi tiếng nhất:

```php
<?php
declare(strict_types=1);

$pos = strpos('abc', 'a');   // tìm thấy 'a' ở vị trí 0
var_dump($pos);              // in ra: int(0)

if ($pos) {                  // 0 là falsy nên nhánh này KHÔNG chạy
    echo "thấy\n";
} else {
    echo "không thấy\n";     // in ra: không thấy   (sai!)
}

if ($pos !== false) {        // đúng: so chặt với false
    echo "thấy ở vị trí $pos\n";   // in ra: thấy ở vị trí 0
}
```

Quy tắc: kết quả kiểu `int|false` (hay `string|false`, `array|false`) phải so bằng `=== false` hoặc
`!== false`, không bao giờ để PHP tự đổi sang bool. Với `strpos` riêng, PHP 8 có `str_contains()`
trả thẳng `bool` (chương 05).

⚠️ Biến chưa gán đứng trong `if` được coi là `null`, tức falsy, nhưng PHP 8 báo
`Warning: Undefined variable $ten_bien` (PHP 7 chỉ là Notice). Đừng dùng điều này làm cách kiểm tra
"biến có tồn tại không"; dùng `isset()` (chương 03).

## 3. int: số nguyên

### 3.1 Cách viết một số nguyên

`int` là số nguyên có dấu: `..., -2, -1, 0, 1, 2, ...`. Có bốn cách viết *literal* (giá trị viết thẳng
trong code):

```php
<?php
declare(strict_types=1);

var_dump(1234);        // in ra: int(1234)     hệ 10
var_dump(0x1A);        // in ra: int(26)       hệ 16, tiền tố 0x
var_dump(0123);        // in ra: int(83)       hệ 8, tiền tố 0 (dễ nhầm!)
var_dump(0o123);       // in ra: int(83)       hệ 8, tiền tố 0o (PHP 8.1+), rõ ràng hơn
var_dump(0b11111111);  // in ra: int(255)      hệ 2, tiền tố 0b
var_dump(1_234_567);   // in ra: int(1234567)  dấu _ giữa các chữ số cho dễ đọc (PHP 7.4+)
var_dump(-42);         // in ra: int(-42)      dấu - là toán tử phủ định đặt trước literal
```

⚠️ Số 0 đứng đầu biến literal thành hệ 8: `0123` là 83, không phải 123. Viết mã bưu chính hay số
điện thoại thành `int` literal có số 0 đầu là sai; những thứ đó là **chuỗi**, không phải số. Từ PHP
8.1 nên viết hệ 8 bằng `0o` cho rõ ý.

Dấu `_` chỉ để người đọc dễ nhìn, trình phân tích của PHP bỏ nó đi. Nó chỉ hợp lệ **giữa hai chữ
số** trong code; chuỗi `"1_000"` không phải numeric string (mục 12.2).

### 3.2 Giới hạn: PHP_INT_MAX, PHP_INT_MIN, PHP_INT_SIZE

Kích thước `int` phụ thuộc bản build PHP. Ngày nay gần như mọi máy chủ chạy bản 64 bit:

| Hằng | Bản 64 bit | Bản 32 bit |
|---|---|---|
| `PHP_INT_SIZE` (số byte) | `8` | `4` |
| `PHP_INT_MAX` | `9223372036854775807` (2⁶³ − 1, khoảng 9,2 × 10¹⁸) | `2147483647` (2³¹ − 1) |
| `PHP_INT_MIN` | `-9223372036854775808` (−2⁶³) | `-2147483648` |

PHP **không có số nguyên không dấu** (unsigned int), khác C, Go (`uint64`) hay cột `BIGINT UNSIGNED`
của MySQL.

### 3.3 Tràn số: int vượt giới hạn thì thành float

Khi một phép toán số học (`+`, `-`, `*`, `**`, `++`...) trên `int` cho kết quả vượt `PHP_INT_MAX` hoặc
dưới `PHP_INT_MIN`, PHP **không báo lỗi và không quay vòng**, mà trả về `float`:

```php
<?php
declare(strict_types=1);

var_dump(PHP_INT_MAX);        // in ra: int(9223372036854775807)
var_dump(PHP_INT_MAX + 1);    // in ra: float(9.223372036854776E+18)
var_dump(PHP_INT_MIN - 1);    // in ra: float(-9.223372036854776E+18)
var_dump(PHP_INT_MAX * 2);    // in ra: float(1.8446744073709552E+19)
var_dump(2 ** 62);            // in ra: int(4611686018427387904)
var_dump(2 ** 63);            // in ra: float(9.223372036854776E+18)

$i = PHP_INT_MAX;
$i++;
var_dump($i);                 // in ra: float(9.223372036854776E+18)

// float không đủ chữ số để phân biệt hai số gần nhau ở cỡ 10^18:
var_dump(PHP_INT_MAX + 1 == PHP_INT_MAX + 2);   // in ra: bool(true)
```

Dòng cuối cho thấy cái giá của việc "thành float": kết quả không còn chính xác tới từng đơn vị. Code
không báo gì, chương trình chạy tiếp với một con số sai. Đây là lý do mục 3.5 tồn tại.

Literal quá lớn cũng thành float ngay khi PHP đọc code:

```php
<?php
declare(strict_types=1);

var_dump(9223372036854775807);    // in ra: int(9223372036854775807)
var_dump(9223372036854775808);    // in ra: float(9.223372036854776E+18)
var_dump(-9223372036854775808);   // in ra: float(-9.223372036854776E+18)   (!)
var_dump(PHP_INT_MIN);            // in ra: int(-9223372036854775808)
```

⚠️ Dòng thứ ba bất ngờ: `-9223372036854775808` bằng đúng `PHP_INT_MIN` nhưng lại ra float. Lý do:
PHP đọc literal `9223372036854775808` trước (vượt `PHP_INT_MAX`, thành float), rồi mới áp toán tử
`-`. Cần số nhỏ nhất thì dùng hằng `PHP_INT_MIN`.

Đối chiếu: Java và Go xử lý tràn số nguyên bằng cách *quay vòng* (wrap around) trong im lặng:
`Integer.MAX_VALUE + 1` trong Java ra `Integer.MIN_VALUE`; Go cũng quay vòng lúc chạy (còn hằng số
tràn thì là lỗi biên dịch). Java có `Math.addExact()` ném exception khi tràn. PHP chọn đường thứ ba:
đổi sang float, tránh số âm vô lý nhưng mất độ chính xác.

### 3.4 Phép chia, chia lấy dư và lỗi chia cho 0

PHP không có toán tử chia nguyên. Toán tử `/` trả `int` chỉ khi cả hai vế là int (hoặc chuỗi số nguyên như `"10"`) và chia
hết; còn lại trả `float`. Muốn chia lấy phần nguyên thì dùng `intdiv()`:

```php
<?php
declare(strict_types=1);

var_dump(6 / 2);            // in ra: int(3)      chia hết
var_dump(7 / 2);            // in ra: float(3.5)
var_dump(intdiv(7, 2));     // in ra: int(3)
var_dump(intdiv(-7, 2));    // in ra: int(-3)     làm tròn về phía 0
var_dump((int) (7 / 2));    // in ra: int(3)      ép kiểu cũng cắt về phía 0
var_dump(7 % 3);            // in ra: int(1)
var_dump(-7 % 3);           // in ra: int(-1)     dấu của kết quả theo số bị chia
var_dump(7 % -3);           // in ra: int(1)

foreach ([fn () => 1 / 0, fn () => 1 % 0, fn () => intdiv(PHP_INT_MIN, -1)] as $f) {
    try {
        $f();
    } catch (\Throwable $e) {
        echo get_class($e), ': ', $e->getMessage(), "\n";
    }
}
// in ra:
// DivisionByZeroError: Division by zero
// DivisionByZeroError: Modulo by zero
// ArithmeticError: Division of PHP_INT_MIN by -1 is not an integer

var_dump(fdiv(1, 0));       // in ra: float(INF)  fdiv (PHP 8.0) theo IEEE 754, không ném lỗi
```

Chia cho 0 ném `DivisionByZeroError` (một `Error`, không phải `Exception`, xem
[chương 12](12-loi-exception.md)): với `%` và `intdiv()` là từ PHP 7, với `/` là từ PHP 8 (PHP 7 chỉ
báo Warning rồi trả `INF`, `-INF` hoặc `NAN`). `intdiv(PHP_INT_MIN, -1)` ném `ArithmeticError` vì kết
quả đúng (2⁶³) không vừa `int`.

### 3.5 Khi con số vượt quá int: ID lớn, JSON, tiền tệ

Ba tình huống thực tế hay gặp:

- **Cột `BIGINT UNSIGNED` trong MySQL** có thể chứa tới 2⁶⁴ − 1, lớn hơn `PHP_INT_MAX`. Giá trị vượt
  `PHP_INT_MAX` không vừa `int`; giữ nó dưới dạng chuỗi.
- **JSON từ hệ thống khác** có số nguyên rất lớn. `json_decode` mặc định biến nó thành float (mất
  chính xác); cờ `JSON_BIGINT_AS_STRING` giữ nó thành chuỗi:

  ```php
  <?php
  declare(strict_types=1);

  var_dump(json_decode('12345678901234567890'));
  // in ra: float(1.2345678901234567E+19)       chữ số cuối đã sai
  var_dump(json_decode('12345678901234567890', false, 512, JSON_BIGINT_AS_STRING));
  // in ra: string(20) "12345678901234567890"
  ```

- **Số nguyên lớn hơn 2⁵³ đổi sang float là mất chính xác** (float chỉ có 53 bit cho phần định trị,
  mục 4.1). Đây cũng là lý do nhiều API trả ID lớn dạng chuỗi: kiểu `Number` của JavaScript ở phía
  client là float 64 bit.

Cần tính toán với số nguyên tuỳ ý lớn thì dùng extension GMP hoặc BCMath (mục 4.8).

## 4. float: số thực dấu phẩy động

### 4.1 Cách viết và cách lưu

`float` (manual cũng gọi là "double" hay "real number") là số có phần thập phân:

```php
<?php
declare(strict_types=1);

var_dump(1.234);       // in ra: float(1.234)
var_dump(1.2e3);       // in ra: float(1200)     ký hiệu khoa học: 1.2 × 10³
var_dump(7E-10);       // in ra: float(7.0E-10)
var_dump(1_234.567);   // in ra: float(1234.567) PHP 7.4+
var_dump(10 / 4);      // in ra: float(2.5)
```

Bên trong, PHP thường lưu float theo chuẩn *IEEE 754 double precision* (manual: tuỳ hệ thống, nhưng
thực tế gần như luôn là chuẩn này): 64 bit gồm 1 bit dấu, 11 bit số mũ và 52 bit phần định trị (cộng
một bit ngầm định, thành 53 bit độ chính xác). Hệ quả:

| Hằng (PHP 7.2+) | Giá trị (64 bit) | Ý nghĩa |
|---|---|---|
| `PHP_FLOAT_DIG` | `15` | Số chữ số thập phân có thể đi vào float rồi đi ra mà không sai |
| `PHP_FLOAT_EPSILON` | `2.220446049250313E-16` | Số dương nhỏ nhất `x` sao cho `1.0 + x != 1.0` |
| `PHP_FLOAT_MAX` | `1.7976931348623157E+308` | Float lớn nhất |
| `PHP_FLOAT_MIN` | `2.2250738585072014E-308` | Float **dương** nhỏ nhất (dạng chuẩn hoá); số âm nhỏ nhất là `-PHP_FLOAT_MAX` |

Nói gọn: float giữ được khoảng 15 chữ số có nghĩa. Con số 9 chữ số `1234567.89` lưu tốt; con số 20
chữ số thì không.

### 4.2 Vì sao 0.1 + 0.2 không bằng 0.3

```php
<?php
declare(strict_types=1);

$x = 0.1 + 0.2;
var_dump($x);              // in ra: float(0.30000000000000004)
var_dump($x == 0.3);       // in ra: bool(false)
printf("%.20f\n", $x);     // in ra: 0.30000000000000004441
```

Đây không phải bug của PHP; mọi ngôn ngữ dùng IEEE 754 (Java `double`, Go `float64`, JavaScript
`Number`, Python `float`) đều cho cùng kết quả. Lý do: máy lưu số ở **hệ 2**. Giống như `1/3` trong
hệ 10 là `0.3333...` kéo dài vô hạn, số `0.1` trong hệ 2 là `0.000110011001100...` kéo dài vô hạn.
Phần định trị chỉ có 52 bit nên phải cắt và làm tròn; `0.1` thật sự được lưu là một số rất gần nhưng không
đúng bằng 0,1. Cộng hai số đã làm tròn, sai số cộng dồn, kết quả lệch khỏi số float gần 0,3 nhất.

Manual cảnh báo một ví dụ nổi tiếng:

```php
<?php
declare(strict_types=1);

printf("%.20f\n", (0.1 + 0.7) * 10);  // in ra: 7.99999999999999911182
var_dump(floor((0.1 + 0.7) * 10));    // in ra: float(7)   không phải 8
var_dump((int) ((0.1 + 0.7) * 10));   // in ra: int(7)
```

Quy tắc của manual: đừng bao giờ tin chữ số cuối cùng của kết quả float, và đừng so sánh bằng hai
float.

### 4.3 echo và var_dump in float khác nhau

Bạn sẽ gặp cảnh `echo` in `0.3` mà `var_dump` in `0.30000000000000004`. Hai cách in dùng hai thiết lập
`php.ini` khác nhau:

| Thiết lập | Mặc định | Ai dùng | Ý nghĩa |
|---|---|---|---|
| `precision` | `14` | `echo`, `print`, ép sang string, nối chuỗi | Số chữ số có nghĩa khi hiển thị |
| `serialize_precision` | `-1` (từ PHP 7.1; trước đó là `17`) | `var_dump`, `var_export`, `json_encode`, `serialize` | `-1` nghĩa là dùng thuật toán in ra **ngắn nhất mà đọc lại vẫn đúng số đó** |

```php
<?php
declare(strict_types=1);

$x = 0.1 + 0.2;
echo $x, "\n";                    // in ra: 0.3                    (làm tròn còn 14 chữ số)
var_dump($x);                     // in ra: float(0.30000000000000004)
echo json_encode(['x' => $x]), "\n";  // in ra: {"x":0.30000000000000004}
echo 1/3, "\n";                   // in ra: 0.33333333333333
var_dump(1/3);                    // in ra: float(0.3333333333333333)
echo 1e15, "\n";                  // in ra: 1.0E+15                (số lớn: echo dùng dạng mũ)
var_dump(1.0);                    // in ra: float(1)
var_export(1.0); echo "\n";       // in ra: 1.0
```

⚠️ `echo` "giấu" sai số: thấy `0.3` trên màn hình không có nghĩa giá trị bằng `0.3`. Khi debug số
thực, dùng `var_dump` hoặc `printf('%.20f', ...)`.

⚠️ Từ PHP 8.0, ép float sang string **không phụ thuộc locale** nữa: `(string) 3.14` luôn là `"3.14"`,
kể cả khi `setlocale()` đặt locale dùng dấu phẩy thập phân. PHP 7 thì có thể ra `"3,14"`.

### 4.4 So sánh hai float

Không so bằng `==` hay `===`. So xem hiệu của chúng có đủ nhỏ không, theo một *sai số cho phép*
(epsilon) hợp với bài toán. Manual dùng ví dụ "bằng nhau tới 5 chữ số thập phân":

```php
<?php
declare(strict_types=1);

$a = 1.23456789;
$b = 1.23456780;
$epsilon = 0.00001;
var_dump(abs($a - $b) < $epsilon);              // in ra: bool(true)

$x = 0.1 + 0.2;
var_dump(abs($x - 0.3) < PHP_FLOAT_EPSILON);    // in ra: bool(true)
```

⚠️ `PHP_FLOAT_EPSILON` chỉ là khoảng cách giữa các float **quanh giá trị 1.0**. Với số cỡ hàng triệu,
khoảng cách giữa hai float liền kề lớn hơn nhiều, nên khi hai số chỉ lệch nhau do làm tròn, phép so
`abs($a - $b) < PHP_FLOAT_EPSILON` vẫn thường ra `false`. Chọn epsilon theo độ lớn của dữ liệu và độ chính xác
bài toán cần (ví dụ so tương đối: `abs($a - $b) <= 1e-9 * max(abs($a), abs($b))`).

### 4.5 Float sang int: cắt phần thập phân

Ép float sang int **cắt về phía 0** (bỏ phần thập phân), không làm tròn:

```php
<?php
declare(strict_types=1);

var_dump((int) 3.99);     // in ra: int(3)
var_dump((int) -3.99);    // in ra: int(-3)
var_dump(intval(8.1));    // in ra: int(8)
var_dump(round(3.5));     // in ra: float(4)    muốn làm tròn thì dùng round(), kết quả vẫn là float
```

Ba cạm bẫy:

- ⚠️ **PHP 8.1+: đổi ngầm float có phần lẻ sang int bị Deprecated.** "Đổi ngầm" là khi bạn không viết
  `(int)` nhưng PHP phải đổi: float làm key array (`$arr[1.5]`), toán hạng của `%` hay toán tử bitwise,
  truyền vào tham số `int` ở chế độ ép kiểu (mục 14). Ép tường minh `(int)`/`intval()` thì không báo.

  ```php
  <?php
  // file KHÔNG có strict_types, để thấy chế độ ép kiểu
  function f(int $x): int { return $x; }

  var_dump(f(8.0));   // in ra: int(8)    float không có phần lẻ: đổi êm
  var_dump(f(8.1));   // Deprecated: Implicit conversion from float 8.1 to int loses precision
                      // rồi in ra: int(8)
  var_dump(7.5 % 2);  // Deprecated: Implicit conversion from float 7.5 to int loses precision
                      // rồi in ra: int(1)
  ```

- ⚠️ **Float ngoài khoảng của int: kết quả không xác định.** Manual: nếu float vượt giới hạn int, kết
  quả là *undefined*, đừng dựa vào nó. `NAN` và `INF` ép sang int luôn ra `0`. **Từ PHP 8.5** các phép
  ép này (tường minh hay ngầm) báo Warning; trước 8.5 ép tường minh không báo gì (còn đổi ngầm thì từ
  8.1 đã báo Deprecated như gạch đầu dòng trên):

  ```php
  <?php
  declare(strict_types=1);

  var_dump((int) 1e19);
  // PHP 8.5: Warning: The float 1.0E+19 is not representable as an int, cast occurred
  // rồi in ra một số int vô nghĩa (PHP 8.4 trở về trước: không báo gì)
  var_dump((int) NAN);
  // PHP 8.5: Warning: The float NAN is not representable as an int, cast occurred
  // in ra: int(0)
  ```

- ⚠️ **Đừng ép một kết quả tính toán có phần lẻ sang int** khi nó lẽ ra là số nguyên: ví dụ
  `(int) ((0.1 + 0.7) * 10)` ra `7` (mục 4.2). Làm tròn trước bằng `round()` rồi mới ép.

### 4.6 Int sang float: mất chính xác trên 2⁵³

Chiều ngược lại cũng có giới hạn. Float có 53 bit độ chính xác, nên số nguyên có trị tuyệt đối tới
2⁵³ (9007199254740992) đổi sang float vẫn đúng; lớn hơn thì có thể bị làm tròn:

```php
<?php
declare(strict_types=1);

var_dump(2 ** 53);                                         // in ra: int(9007199254740992)
var_dump((float) (2 ** 53) + 1.0 === (float) (2 ** 53));   // in ra: bool(true)    2^53 + 1 không biểu diễn được
var_dump(9007199254740993 === (int) (float) 9007199254740993); // in ra: bool(false)  đi qua float là mất số
```

Khi nào int bị đổi sang float mà bạn không để ý? Khi trộn int với float trong phép tính (`$id * 1.0`,
`$id + 0.5`), khi tràn số (mục 3.3), khi truyền int vào tham số `float`.

### 4.7 NAN và INF

IEEE 754 có hai loại giá trị đặc biệt mà PHP đặt tên bằng hằng:

- `INF` / `-INF` (*infinity*, vô cực): kết quả vượt `PHP_FLOAT_MAX`, ví dụ `PHP_FLOAT_MAX * 2`,
  `fdiv(1, 0)`.
- `NAN` (*Not a Number*): kết quả không xác định, ví dụ `sqrt(-1)`, `INF - INF`, `fdiv(0, 0)`.

```php
<?php
declare(strict_types=1);

var_dump(PHP_FLOAT_MAX * 2);        // in ra: float(INF)
var_dump(INF - INF);                // in ra: float(NAN)

$nan = sqrt(-1);
var_dump($nan == $nan);             // in ra: bool(false)  NAN không bằng chính nó
var_dump($nan === NAN);             // in ra: bool(false)
var_dump(is_nan($nan));             // in ra: bool(true)   cách đúng để kiểm tra
var_dump(is_infinite(INF), is_finite(1.5));   // in ra: bool(true) bool(true)
var_dump(in_array(NAN, [NAN]));     // in ra: bool(false)
var_dump(json_encode(NAN));         // in ra: bool(false)  JSON không có NAN/INF
```

Theo manual, so sánh `NAN` (lỏng hay chặt) với bất kỳ giá trị nào, kể cả chính nó, đều ra `false`;
ngoại lệ duy nhất là so lỏng với `true` (vì so với bool thì `NAN` đổi sang bool là `true`). Luôn
kiểm tra bằng `is_nan()`.

⚠️ PHP 8.5 thêm Warning khi `NAN` bị đổi sang kiểu khác (`(string) NAN`, `(bool) NAN`, `(int) NAN`).
Nếu log của bạn bắt đầu có `unexpected NAN value was coerced to ...` (với string, bool) hoặc
`The float NAN is not representable as an int` (với int) sau khi nâng lên 8.5, đó là dấu hiệu một phép
tính đâu đó đã ra `NAN` từ trước mà không ai biết.

### 4.8 Tiền tệ: đừng dùng float

Tiền cần chính xác tới từng đồng, float thì không:

```php
<?php
declare(strict_types=1);

// Sai: float, cộng 0.1 mười lần
$total = 0.0;
for ($i = 0; $i < 10; $i++) {
    $total += 0.1;
}
var_dump($total);           // in ra: float(0.9999999999999999)
var_dump($total === 1.0);   // in ra: bool(false)

// Cách 1: lưu số nguyên theo đơn vị nhỏ nhất (xu, cent)
$cents = 0;
for ($i = 0; $i < 10; $i++) {
    $cents += 10;           // 0.10 = 10 xu
}
var_dump($cents === 100);   // in ra: bool(true)

// Cách 2: bcmath, tính trên chuỗi thập phân với số chữ số sau dấu phẩy (scale) cố định
$sum = '0';
for ($i = 0; $i < 10; $i++) {
    $sum = bcadd($sum, '0.1', 2);
}
var_dump($sum);                       // in ra: string(4) "1.00"
var_dump(bcmul('19.99', '3', 2));     // in ra: string(5) "59.97"
var_dump(bcdiv('10', '3', 4));        // in ra: string(6) "3.3333"
```

Hai lựa chọn đúng:

1. **Số nguyên đơn vị nhỏ nhất**: lưu `1999` thay cho `19.99`. Nhanh, đơn giản, hợp khi mọi số tiền
   có cùng số chữ số lẻ. Với tiền VND không có phần lẻ thì `int` là đủ.
2. **Số thập phân chính xác**: extension BCMath (`bcadd`, `bcmul`, `bcdiv`...) nhận và trả **chuỗi**.
   BCMath có sẵn trong mã nguồn PHP nhưng phải được bật khi build; image Docker chính thức `php:*-cli`
   không bật sẵn, cần chạy thêm `docker-php-ext-install bcmath`. Từ PHP 8.4 có thêm class
   `BcMath\Number` cho phép viết toán tử bình thường:

   ```php
   <?php
   declare(strict_types=1);

   use BcMath\Number;   // PHP 8.4+, cần extension bcmath

   $price = new Number('19.99');
   $total = $price * 3;           // toán tử được nạp chồng (operator overloading)
   echo $total, "\n";             // in ra: 59.97
   ```

Ở phía database, cột tiền dùng `DECIMAL`, không dùng `FLOAT`/`DOUBLE` (giáo trình Database,
[chương Kiểu dữ liệu](../database/03-kieu-du-lieu.md)). Đối chiếu: Java dùng `BigDecimal`, Go thường
dùng số nguyên xu hoặc thư viện decimal bên ngoài; ở ngôn ngữ nào thì float nhị phân cũng không hợp
với tiền.

## 5. string: dãy byte

Mục này chỉ nói về `string` ở góc độ **kiểu**; cú pháp, hàm xử lý chuỗi, UTF-8 nằm ở
[chương 05](05-chuoi.md).

Manual định nghĩa: string là một dãy ký tự, trong đó **một ký tự là một byte**. Bên trong, PHP lưu
string bằng một mảng byte kèm độ dài, không ghi nhận gì về *encoding* (bảng mã). Hệ quả:

- PHP không có kiểu `char` riêng như Java/Go; một ký tự lấy ra (`$s[0]`) vẫn là string dài 1 byte.
- PHP không có kiểu "mảng byte" riêng; dữ liệu nhị phân (ảnh, file nén, dữ liệu đọc từ socket) cũng
  là string. String có thể chứa cả byte `0`.
- `strlen()` đếm **byte**, không đếm chữ. Với tiếng Việt UTF-8 thì khác số chữ:

```php
<?php
declare(strict_types=1);

var_dump(strlen("bốn"));      // in ra: int(5)   "ố" chiếm 3 byte trong UTF-8
var_dump(mb_strlen("bốn"));   // in ra: int(3)   đếm theo ký tự (extension mbstring)
```

Đổi các kiểu khác sang string (bằng `(string) $x`, `strval($x)`, hoặc ngầm khi `echo`, nối chuỗi `.`,
chèn vào chuỗi `"...$x..."`):

| Giá trị | Thành | Ghi chú |
|---|---|---|
| `true` | `"1"` | |
| `false` | `""` | chuỗi rỗng, nên `echo false;` không in gì |
| `null` | `""` | |
| `42` | `"42"` | |
| `4.1e6` | `"4100000"` | float theo `precision` (mục 4.3) |
| `1.5e20` | `"1.5E+20"` | số lớn dùng dạng mũ |
| array | `"Array"` | kèm `Warning: Array to string conversion` |
| object | gọi `__toString()` | class không có `__toString()` thì ném `Error` |
| resource | `"Resource id #N"` | `N` là ID của resource (ví dụ `"Resource id #5"`); manual dặn đừng dựa vào định dạng này |

```php
<?php
declare(strict_types=1);

$s = (string) [1, 2];   // Warning: Array to string conversion
var_dump($s);           // in ra: string(5) "Array"

try {
    $x = (string) new stdClass();
} catch (\Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Object of class stdClass could not be converted to string
}
```

⚠️ `echo $array;` không in nội dung array, chỉ in chữ `Array` kèm Warning. Muốn xem nội dung thì dùng
`print_r()`/`var_dump()` (chương 03) hoặc `json_encode()`.

## 6. array: bảng key/value có thứ tự

Chi tiết ở [chương 06](06-mang.md); ở đây chỉ cần nắm array là kiểu gì.

Array của PHP không giống mảng của C/Java/Go (một dãy phần tử đánh số từ 0). Nó là một *ordered map*
(bảng ánh xạ có thứ tự): mỗi phần tử là một cặp **key → value**, giữ đúng thứ tự thêm vào. Cùng một kiểu `array` đóng
vai list, dictionary, stack, queue, set...

- **Key** chỉ có thể là `int` hoặc `string`. Giá trị khác dùng làm key bị đổi kiểu: chuỗi số nguyên
  thập phân như `"8"` thành `8`, `true` thành `1`, float bị cắt phần lẻ (`1.5` thành `1`, kèm
  Deprecated từ 8.1), `null` thành `""` (dùng `null` làm key bị Deprecated từ 8.5).
- **Value** có thể là bất kỳ kiểu nào, kể cả array khác (array nhiều chiều).

```php
<?php
declare(strict_types=1);

$a = [];
$a["1"] = 'chuỗi "1"';
$a[1]   = 'số 1';         // cùng key 1 với dòng trên: ghi đè
$a[true] = 'true';        // true thành key 1: ghi đè lần nữa
$a["01"] = 'chuỗi "01"';  // "01" không phải số nguyên chuẩn: giữ là key string
var_dump($a);
// in ra: array(2) { [1]=> string(4) "true" ["01"]=> string(12) "chuỗi "01"" }  (gộp dòng)
```

Ép sang array bằng `(array)`:

| Giá trị | `(array)` cho ra |
|---|---|
| scalar hoặc resource (`'abc'`, `1.5`...) | array một phần tử: `[0 => 'abc']` |
| `null` | `[]` |
| object | array các property; property `private`/`protected` có tên bị "trộn" thêm tên class hoặc `*`, bao bởi byte `\0` |

⚠️ Ép object sang array để "lấy dữ liệu ra" là thói quen dễ hỏng vì cách đặt tên key với property
private/protected ở trên. Viết method `toArray()` rõ ràng thì an toàn hơn.

## 7. object: thể hiện của class

Chi tiết ở [chương 09](09-oop-co-ban.md) và [chương 10](10-oop-nang-cao.md).

Một *object* là một thể hiện (instance) của một *class*, tạo bằng `new`. Mỗi class (và interface, enum)
bạn định nghĩa là một **kiểu mới**, dùng được trong khai báo kiểu: `function save(User $user)`. Vài
object bạn đã gặp mà có thể chưa để ý:

- Closure (`function () {}`, `fn () =>`) là object của class `Closure`.
- Case của enum (`Suit::Hearts`) là object (mục 1.4).
- `stdClass` là class rỗng dựng sẵn, thường xuất hiện khi ép array sang object hoặc khi
  `json_decode` không có cờ trả array.

```php
<?php
declare(strict_types=1);

$o = (object) ['ten' => 'An', 'tuoi' => 30];   // array thành stdClass, key thành property
echo $o->ten, "\n";                            // in ra: An
echo get_debug_type($o), "\n";                 // in ra: stdClass

$s = (object) 'ciao';                          // scalar thành stdClass có property "scalar"
echo $s->scalar, "\n";                         // in ra: ciao
```

Hai tính chất của object ảnh hưởng tới type juggling: object **luôn truthy** (mục 2.2), và chỉ đổi
được sang string nếu class có `__toString()` (mục 5). Biến chứa object thực chất giữ một *handle* trỏ
tới object, nên gán `$b = $a` không sao chép object; phần này ở chương 09.

## 8. null: "không có giá trị"

`null` là kiểu chỉ có **một** giá trị, cũng tên là `null` (hằng không phân biệt hoa thường; theo
chuẩn code thì viết thường). Một biến mang giá trị `null` khi:

1. được gán `null`;
2. đã bị `unset()`;
3. chưa từng được gán (đọc nó cho ra `null` kèm `Warning: Undefined variable`).

```php
<?php
declare(strict_types=1);

$a = null;
var_dump($a === null);   // in ra: bool(true)   cách kiểm tra rõ ràng nhất
var_dump(is_null($a));   // in ra: bool(true)   tương đương
var_dump(isset($a));     // in ra: bool(false)  isset coi null là "không có" (chương 03)

var_dump(null + 1);      // in ra: int(1)       ngữ cảnh số: null thành 0
var_dump(null . 'a');    // in ra: string(1) "a" ngữ cảnh chuỗi: null thành ""
var_dump(null == 0);     // in ra: bool(true)   so lỏng: cả hai đổi về bool (mục 13)
var_dump(null === 0);    // in ra: bool(false)
```

Liên quan tới null trong chương này và chương khác:

- Khai báo "nhận thêm null": `?string` hoặc `string|null` (mục 11.4).
- Truyền `null` vào tham số không nullable của **hàm có sẵn** bị Deprecated từ 8.1 (mục 14.6).
- Toán tử `??`, `??=`, `?->` xử lý null gọn gàng: [chương 07](07-toan-tu-dieu-khien.md).
- Ép kiểu `(unset) $x` (cho ra null) đã bị bỏ từ PHP 8.0; muốn gán null thì viết `$x = null`.

Đối chiếu: Java có `null` cho mọi kiểu tham chiếu (nguồn gốc `NullPointerException`), Go dùng `nil`
cho pointer, slice, map, interface... và giá trị mặc định "zero value" (`0`, `""`) cho kiểu cơ bản.
PHP gần Java hơn nhưng bắt buộc bạn nói rõ chỗ nào nhận null khi đã khai báo kiểu: `string` không
nhận null, `?string` mới nhận.

## 9. resource: tay cầm tới tài nguyên bên ngoài

Một *resource* là biến đặc biệt giữ tham chiếu tới tài nguyên **bên ngoài** PHP: file đang mở, stream,
tiến trình con... Nó được tạo và dùng bởi các hàm chuyên biệt (`fopen`, `opendir`, `proc_open`...).
PHP không cho bạn "nhìn vào trong" resource; bạn chỉ chuyền nó qua lại giữa các hàm.

```php
<?php
declare(strict_types=1);

$f = fopen('php://memory', 'r+');
var_dump(get_resource_type($f));   // in ra: string(6) "stream"
var_dump(get_resource_id($f));     // in ra: int(...)  một số định danh, PHP 8.0+
fclose($f);
var_dump(is_resource($f));         // in ra: bool(false)  đã đóng
var_dump(get_debug_type($f));      // in ra: string(17) "resource (closed)"
```

Resource được giải phóng tự động khi không còn biến nào trỏ tới (nhờ cơ chế đếm tham chiếu), nên
hiếm khi bắt buộc phải tự đóng; gọi `fclose()` là để **giải phóng sớm**. Ngoại lệ là kết nối database
*persistent* (dùng lại giữa các request): chúng không bị dọn theo cách này.

`resource` là kiểu duy nhất **không** dùng được trong khai báo kiểu (manual: mọi kiểu PHP hỗ trợ, trừ
resource, đều khai báo được). RFC *Resource to object conversion* liệt kê đây là một trong các nhược
điểm của resource, và PHP 8 đang dần thay resource bằng object:

| Phiên bản | Ví dụ resource thành object |
|---|---|
| 8.0 | `curl_init()` trả `CurlHandle`; GD dùng `GdImage`; OpenSSL dùng `OpenSSLCertificate`... |
| 8.1 | fileinfo dùng `finfo`; FTP dùng `FTP\Connection`; PostgreSQL dùng `PgSql\Connection`... |
| 8.4 | DBA dùng `Dba\Connection`; ODBC dùng `Odbc\Connection` |

⚠️ Khi nâng phiên bản, code kiểu `if (!is_resource($ch)) { ... }` sau `curl_init()` sẽ sai, vì
`$ch` giờ là object. UPGRADING của PHP khuyên đổi sang kiểm tra `=== false`. Stream của `fopen()` thì
tới PHP 8.5 vẫn là resource.

## 10. callable và iterable: kiểu mô tả khả năng

### 10.1 callable: thứ gọi được như hàm

`callable` nghĩa là "giá trị này gọi được bằng cú pháp `$fn(...)`". Nhiều dạng giá trị thoả điều
này:

```php
<?php
declare(strict_types=1);

final class Greeter
{
    public function hello(string $name): string { return "Chào $name"; }
    public static function bye(string $name): string { return "Tạm biệt $name"; }
    public function __invoke(string $name): string { return "Hi $name"; }
}

function run(callable $fn, string $arg): string
{
    return $fn($arg);
}

$g = new Greeter();
echo run('strtoupper', 'an'), "\n";                       // in ra: AN            tên hàm dạng chuỗi
echo run([$g, 'hello'], 'An'), "\n";                      // in ra: Chào An       [object, 'method']
echo run([Greeter::class, 'bye'], 'An'), "\n";            // in ra: Tạm biệt An   [tên class, 'static method']
echo run('Greeter::bye', 'Bình'), "\n";                   // in ra: Tạm biệt Bình 'Class::method'
echo run(fn (string $s): string => "<$s>", 'An'), "\n";   // in ra: <An>          Closure
echo run($g, 'Chi'), "\n";                                // in ra: Hi Chi        object có __invoke
echo run(strrev(...), 'abc'), "\n";                       // in ra: cba           first-class callable (8.1)

try {
    run('khong_ton_tai', 'x');
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: run(): Argument #1 ($fn) must be of type callable, string given, called in ... on line ...
}
```

Để ý: `get_debug_type('strtoupper')` là `"string"` và `get_debug_type([$g, 'hello'])` là `"array"`.
Một callable dạng chuỗi chỉ là chuỗi bình thường; PHP chỉ biết nó gọi được hay không khi kiểm tra
(`is_callable()`, hoặc lúc truyền vào tham số `callable`).

⚠️ `callable` **không dùng được làm kiểu của property**:
`public callable $fn;` là `Fatal error: Property Box::$fn cannot have type callable`. Khi cần lưu
hàm vào property, khai báo kiểu `Closure` (một class bình thường) và chuyển mọi thứ thành Closure
bằng cú pháp `strlen(...)` hoặc `Closure::fromCallable()`.

⚠️ Callable dạng chuỗi/array (`'strtoupper'`, `[$g, 'hello']`) không được IDE và công cụ phân tích
tĩnh kiểm tra tốt: gõ sai tên method chỉ lộ ra lúc chạy. Cú pháp *first-class callable*
`$g->hello(...)` (PHP 8.1) tạo Closure và báo lỗi ngay tại dòng đó nếu method không tồn tại. Chi tiết
về closure, `use`, arrow function ở [chương 08](08-ham.md).

### 10.2 iterable: thứ duyệt được bằng foreach

`iterable` chấp nhận **array hoặc object cài đặt `Traversable`** (iterator, generator...). Từ PHP 8.2
nó chính thức là *type alias* của `array|Traversable` (trước đó, từ 7.1, là một "pseudo-type" có tác
dụng tương tự). Thông báo lỗi từ 8.2 hiện đúng dạng alias đã được mở ra:

```php
<?php
declare(strict_types=1);

function sum(iterable $numbers): int
{
    $total = 0;
    foreach ($numbers as $n) {
        $total += $n;
    }
    return $total;
}

function numbers(): Generator
{
    yield 1;
    yield 2;
    yield 3;
}

echo sum([1, 2, 3]), "\n";                   // in ra: 6   array
echo sum(new ArrayIterator([4, 5])), "\n";   // in ra: 9   object Traversable
echo sum(numbers()), "\n";                   // in ra: 6   generator cũng là Traversable

try {
    sum('123');
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // PHP 8.2+: sum(): Argument #1 ($numbers) must be of type Traversable|array, string given, ...
    // PHP 8.1:  sum(): Argument #1 ($numbers) must be of type iterable, string given, ...
}
```

Dùng `iterable` khi hàm chỉ cần duyệt một lượt và muốn nhận cả generator (tiết kiệm bộ nhớ với dữ
liệu lớn). Nếu hàm cần `count()` hay truy cập theo key thì khai báo `array`. Iterator và generator ở
[chương 13](13-generator-iterator-spl.md).

## 11. Khai báo kiểu (type declarations)

### 11.1 Khai báo kiểu ở đâu, để làm gì

*Type declaration* là việc ghi kiểu mong muốn vào một "cửa" mà giá trị đi qua. PHP có bốn cửa như vậy:

```php
<?php
declare(strict_types=1);

final class Order
{
    public const int MAX_ITEMS = 50;      // 4. hằng của class (PHP 8.3+)
    public ?string $note = null;          // 3. property (PHP 7.4+)

    public function addItem(string $sku, int $qty): bool   // 1. tham số, 2. giá trị trả về
    {
        return $qty <= self::MAX_ITEMS;
    }
}
```

Khi giá trị đi qua cửa mà sai kiểu, PHP ném `TypeError` (một `Error`, xem
[chương 12](12-loi-exception.md)). Lợi ích: lỗi lộ ra **ngay tại ranh giới** (dòng gọi hàm, dòng
`return`), thay vì một giá trị sai chạy sâu vào hệ thống rồi gây hậu quả ở chỗ khác. Kiểu khai báo
còn là tài liệu sống cho người đọc, và là đầu vào cho IDE, công cụ phân tích tĩnh.

```php
<?php
declare(strict_types=1);

function findName(int $id): string
{
    return $id === 1 ? 'An' : null;   // nhánh thứ hai trả sai kiểu
}

echo findName(1), "\n";               // in ra: An
try {
    echo findName(2), "\n";
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";      // in ra: findName(): Return value must be of type string, null returned
}
```

Ba dạng thông báo `TypeError` bạn sẽ gặp hằng ngày (PHP 8):

| Cửa | Thông báo |
|---|---|
| Tham số | `f(): Argument #1 ($x) must be of type int, string given, called in ... on line ...` |
| Giá trị trả về | `f(): Return value must be of type string, null returned` |
| Property | `Cannot assign string to property Order::$id of type int` |

⚠️ PHP kiểm tra **lúc chạy**, và chỉ ở những dòng thật sự chạy. Trong ví dụ trên, `findName(1)` chạy
êm; bug chỉ nổ khi có ai gọi `findName(2)`, có thể là trên production. Java/Go bắt lỗi kiểu loại này
lúc biên dịch. Muốn bắt sớm trong PHP thì dùng công cụ phân tích tĩnh (PHPStan, Psalm), xem
[chương 21](21-chat-luong-code.md).

### 11.2 Lịch sử ngắn

Hệ thống kiểu của PHP lớn dần qua từng phiên bản. Bảng này giúp đọc hiểu code cũ và biết tính năng
nào dùng được ở phiên bản bạn đang chạy:

| Phiên bản | Thêm gì |
|---|---|
| PHP 5 | Kiểu cho tham số: tên class/interface, `array`, `callable` |
| 7.0 | Kiểu scalar `int`, `float`, `string`, `bool`; kiểu trả về; `declare(strict_types=1)` |
| 7.1 | Nullable `?T`; `void`; `iterable` |
| 7.2 | `object` |
| 7.4 | Kiểu cho property |
| 8.0 | Union `A\|B`; `mixed`; `static` làm kiểu trả về; `false` trong union |
| 8.1 | `never`; intersection `A&B` |
| 8.2 | DNF `(A&B)\|C`; `null` và `false` đứng riêng; `true` |
| 8.3 | Kiểu cho hằng của class |
| 8.4 | Nullable ngầm (`T $x = null`) bị Deprecated |

### 11.3 Kiểu đơn và các kiểu đặc biệt

Mọi kiểu ở mục 2 đến 10 đều khai báo được, **trừ `resource`** (và `callable` không dùng được cho
property, mục 10.1). Thêm vào đó là vài kiểu chỉ có ý nghĩa trong khai báo:

| Kiểu | Dùng ở đâu | Ý nghĩa |
|---|---|---|
| `self` | trong class | instance của chính class chứa khai báo |
| `parent` | trong class | instance của class cha |
| `static` | chỉ kiểu trả về (8.0) | instance của class **mà method được gọi trên đó** (late static binding, chương 10) |
| `void` | chỉ kiểu trả về (7.1) | hàm không trả giá trị |
| `never` | chỉ kiểu trả về (8.1) | hàm **không bao giờ** trả về bình thường |
| `mixed` | mọi chỗ (8.0) | bất kỳ giá trị nào, kể cả `null` |
| `null`, `false`, `true` | đứng riêng từ 8.2 | đúng một giá trị đó |

**`void` và `never` khác nhau thế nào?** `void` nghĩa là "hàm chạy xong và quay về, nhưng không đưa
lại giá trị gì" (ví dụ hàm ghi log). `never` nghĩa là "hàm không bao giờ quay về chỗ gọi": nó luôn ném
exception, gọi `exit()`, hoặc lặp vô hạn (ví dụ hàm `abort(404)`, `redirect()->send(); exit;`).

```php
<?php
declare(strict_types=1);

function logLine(string $msg): void
{
    echo $msg, "\n";
    return;                 // được: return không kèm giá trị
}
var_dump(logLine('xin chào'));   // in ra: xin chào, rồi NULL (hàm void vẫn "trả" null khi bị dùng làm giá trị)

function fail(string $msg): never
{
    throw new RuntimeException($msg);
}

try {
    fail('hết hàng');
} catch (RuntimeException $e) {
    echo 'Bắt được: ', $e->getMessage(), "\n";   // in ra: Bắt được: hết hàng
}
```

Các lỗi tương ứng khi vi phạm (đã chạy thử trên PHP 8.5):

| Code | Lỗi |
|---|---|
| `function f(): void { return null; }` | `Fatal error: A void function must not return a value (did you mean "return;" instead of "return null;"?)` (lỗi lúc biên dịch) |
| `function f(): never { echo "x"; }` rồi gọi `f()` | `TypeError: f(): never-returning function must not implicitly return` |
| `function f(): mixed {}` rồi gọi `f()` | `TypeError: f(): Return value must be of type mixed, none returned` |
| `function f(void $x) {}` | `Fatal error: void cannot be used as a parameter type` |

Dòng thứ ba đáng chú ý: `mixed` nhận cả `null`, nhưng hàm khai báo `: mixed` vẫn phải `return` một
giá trị tường minh (kể cả `return null;`).

**`static` khác `self`:**

```php
<?php
declare(strict_types=1);

class Model
{
    public static function create(): static   // trả về đúng class được gọi
    {
        return new static();
    }
}
final class User extends Model {}

echo get_class(User::create()), "\n";   // in ra: User   (nếu khai báo : self thì vẫn chạy, nhưng kiểu khai báo chỉ hứa là Model)
```

⚠️ Tên kiểu phải viết đúng tên chuẩn: `bool`, `int`, `float`, `string`. PHP **không** nhận bí danh
`boolean`, `integer`, `double` trong khai báo kiểu; nó hiểu đó là **tên class**:

```php
<?php
declare(strict_types=1);

function f(boolean $x) {}
f(true);
// Warning: "boolean" will be interpreted as a class name. Did you mean "bool"? Write "\boolean" to suppress this warning
// Fatal error: Uncaught TypeError: f(): Argument #1 ($x) must be of type boolean, true given, ...
```

### 11.4 Nullable: `?T`

`?T` nghĩa là "kiểu `T` hoặc `null`", là cách viết ngắn của `T|null` (có từ 7.1, trước cả union type).

```php
<?php
declare(strict_types=1);

function greet(?string $name): string
{
    return $name === null ? 'Chào bạn' : "Chào $name";
}

echo greet('An'), "\n";   // in ra: Chào An
echo greet(null), "\n";   // in ra: Chào bạn
// greet();               // ArgumentCountError: ?string vẫn là tham số BẮT BUỘC, chỉ là được phép truyền null
```

⚠️ "Nullable" khác "không bắt buộc" (optional). `?string $name` vẫn bắt buộc truyền (dù truyền
`null`). Muốn bỏ qua được thì cần giá trị mặc định: `?string $name = null`.

⚠️ `?` chỉ đi với **một** kiểu. `?int|string` là lỗi cú pháp; viết `int|string|null`. `?mixed` cũng
lỗi (`Type mixed cannot be marked as nullable since mixed already includes null`), vì `mixed` đã
gồm `null`.

⚠️ **Nullable ngầm bị Deprecated từ PHP 8.4.** Code cũ hay viết tham số có kiểu và mặc định `null`
nhưng không có `?`:

```php
<?php
declare(strict_types=1);

class Logger {}

function a(Logger $l = null) {}    // PHP 8.4+: Deprecated: a(): Implicitly marking parameter $l as nullable is deprecated,
                                   // the explicit nullable type must be used instead
function b(?Logger $l = null) {}   // đúng: nói rõ là nhận null
```

PHP cũ ngầm hiểu `Logger $l = null` là `?Logger`. Cách viết này trộn hai ý "có giá trị mặc định" và
"nhận null", nên bị bỏ dần. Sửa bằng cách thêm `?` (tương thích ngược tới 7.1, sửa hàng loạt được
bằng công cụ như Rector).

### 11.5 Union type: `A|B`

*Union type* (PHP 8.0) cho phép một giá trị thuộc **một trong** nhiều kiểu: `int|string`,
`array|Traversable`, `string|false`. Rất nhiều hàm có sẵn được mô tả bằng union: `strpos()` trả
`int|false`, `file_get_contents()` trả `string|false`.

```php
<?php
declare(strict_types=1);

function formatId(int|string $id): string
{
    return is_int($id) ? sprintf('#%06d', $id) : strtoupper($id);
}

echo formatId(42), "\n";      // in ra: #000042
echo formatId('ab-1'), "\n";  // in ra: AB-1
```

PHP chặn ngay lúc biên dịch những union thừa hoặc vô lý, để bắt lỗi gõ nhầm:

| Khai báo | Lỗi |
|---|---|
| `int\|INT` | `Duplicate type int is redundant` (tên kiểu không phân biệt hoa thường) |
| `bool\|false` | `Duplicate type false is redundant` (`bool` đã gồm `false`) |
| `true\|false` | `Type contains both true and false, bool must be used instead` |
| `object\|stdClass` | `Type stdClass\|object contains both object and a class type, which is redundant` |
| `mixed\|null` | `Type mixed can only be used as a standalone type` |
| `void\|int` | `Void can only be used as a standalone type` |
| `never\|int` | `never can only be used as a standalone type` |

**Union ở chế độ ép kiểu.** Khi file không bật `strict_types` và giá trị không thuộc kiểu nào trong
union, PHP thử ép theo thứ tự ưu tiên `int` → `float` → `string` → `bool`, lấy kiểu đầu tiên có trong
union mà ép được. Ngoại lệ: chuỗi số mà union có cả `int` lẫn `float` thì chọn theo dạng của chuỗi
(`"42"` thành int, `"42.0"` thành float). Không bao giờ ép ngầm sang `null`, `false`, `true`.

```php
<?php
// KHÔNG strict_types: xem PHP chọn kiểu đích trong union
final class WithToString { public function __toString(): string { return 'từ __toString'; } }
function is(int|string $v): string { return var_export($v, true); }
function ifb(int|float|bool $v): string { return var_export($v, true); }

echo is(42), "\n";                  // in ra: 42                đúng kiểu, giữ nguyên
echo is("42"), "\n";                // in ra: '42'              đúng kiểu string, giữ nguyên
echo is(new WithToString()), "\n";  // in ra: 'từ __toString'   object không thành int được, thử string
echo is(42.0), "\n";                // in ra: 42                float không lẻ: thành int
echo is(1e100), "\n";               // in ra: '1.0E+100'        quá lớn cho int: thành string
echo is(true), "\n";                // in ra: 1                 bool thành int
echo ifb("45"), "\n";               // in ra: 45
echo ifb("45.0"), "\n";             // in ra: 45.0
echo ifb("45X"), "\n";              // in ra: true              không phải numeric string: rơi xuống bool
echo ifb(""), "\n";                 // in ra: false
```

Bảng trên cho thấy vì sao nhiều người khuyên bật `strict_types`: các luật ép ngầm đúng là có quy tắc,
nhưng khó đoán khi đọc code.

### 11.6 Intersection type `A&B` và DNF type

*Intersection type* (PHP 8.1) yêu cầu giá trị thoả **tất cả** các kiểu cùng lúc. Vì một giá trị không
thể vừa là `int` vừa là `string`, intersection chỉ dùng được với class và interface:

```php
<?php
declare(strict_types=1);

function countAndList(Countable&Traversable $items): void
{
    echo count($items), ' phần tử: ';
    foreach ($items as $item) {
        echo $item, ' ';
    }
    echo "\n";
}

countAndList(new ArrayIterator(['a', 'b', 'c']));   // in ra: 3 phần tử: a b c
// countAndList(['a']);   // TypeError: array không phải object
```

`ArrayIterator` cài đặt cả `Countable` lẫn `Traversable` nên hợp lệ. Viết `int&string` thì báo
`Type int cannot be part of an intersection type`.

*DNF type* (Disjunctive Normal Form, PHP 8.2) là **hợp của các giao**: mỗi intersection đặt trong
ngoặc, nối với nhau hoặc với kiểu khác bằng `|`:

```php
<?php
declare(strict_types=1);

function process((Countable&Traversable)|null $items): int
{
    return $items === null ? 0 : count($items);
}

echo process(null), "\n";                          // in ra: 0
echo process(new ArrayIterator([1, 2])), "\n";     // in ra: 2
```

Luật cú pháp: giao nằm **trong** ngoặc, hợp nằm **ngoài**. `A&(B|C)` là lỗi cú pháp; phải viết lại
thành `(A&B)|(A&C)`.

### 11.7 Property có kiểu và hằng có kiểu

Property có kiểu (7.4) có thêm một trạng thái lạ: *uninitialized* (chưa khởi tạo). Property
`public int $id;` không có giá trị mặc định thì **không phải `null`**, mà là "chưa có gì"; đọc nó trước
khi gán là lỗi:

```php
<?php
declare(strict_types=1);

final class Order
{
    public const int MAX_ITEMS = 50;   // hằng có kiểu (8.3)
    public int $id;                    // chưa gán: uninitialized
}

$o = new Order();
try {
    echo $o->id;
} catch (\Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Typed property Order::$id must not be accessed before initialization
}
try {
    $o->id = "5";
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";   // in ra: Cannot assign string to property Order::$id of type int
}
$o->id = 5;
var_dump($o->id, Order::MAX_ITEMS); // in ra: int(5) int(50)
```

Phép gán `$o->id = "5"` bị từ chối vì file có `strict_types`; file không strict thì `"5"` được ép
thành `5` (mục 14.3). Constructor, readonly, property hooks... ở chương 09 và 10.

Một ghi chú cho chương OOP: khi class con override method, kiểu trả về được phép **hẹp hơn** (ví dụ
cha trả `iterable`, con trả `array`), kiểu tham số được phép **rộng hơn**; manual gọi đây là luật
*variance*. `never` là kiểu con của mọi kiểu nên luôn thay được kiểu trả về của cha.

## 12. Type juggling: khi PHP tự đổi kiểu

### 12.1 Sáu ngữ cảnh đổi kiểu

*Type juggling* (tung hứng kiểu) là việc PHP tự đổi kiểu của một giá trị cho hợp với **ngữ cảnh**
đang dùng nó. Không có một luật chung "PHP đổi kiểu thế này"; manual chia ra sáu ngữ cảnh, mỗi ngữ
cảnh một luật:

| Ngữ cảnh | Xảy ra khi | Giá trị bị đổi sang | Đọc ở |
|---|---|---|---|
| Số học (numeric) | `+ - * / % **` | `int` hoặc `float` | mục này |
| Chuỗi (string) | `echo`, `print`, chèn biến vào chuỗi, nối chuỗi `.` | `string` | mục 5 |
| Logic (logical) | `if`, `while`, toán tử ba ngôi, `!`, `&&`, `\|\|` | `bool` | mục 2 |
| Bitwise (integral and string) | `& \| ^ ~ << >>` | `int`; riêng `& \| ^` khi cả hai vế là string, và `~` khi vế là string, thì xử lý từng byte và cho ra string | chương 07 |
| So sánh (comparative) | `== != < > <= >= <=>` | tuỳ cặp kiểu | mục 13 |
| Hàm (function) | truyền tham số, `return`, gán property có khai báo kiểu | kiểu khai báo | mục 14 |

Nhắc lại từ mục 1.5: đổi kiểu tạo ra **giá trị tạm**, giá trị gốc trong biến không đổi. Muốn đổi hẳn
kiểu của biến thì gán lại (`$x = (int) $x;`) hoặc dùng `settype()`.

**Luật của ngữ cảnh số học** (theo manual): nếu một trong hai toán hạng là float, hoặc không diễn giải
được thành int, thì cả hai được coi là float và kết quả là float; ngược lại cả hai là int và kết quả là
int. `bool` thành `0`/`1`, `null` thành `0`, string theo luật numeric string (mục 12.2).

```php
<?php
declare(strict_types=1);

var_dump(7 + 1.0);        // in ra: float(8)   có một float: kết quả float
var_dump("7" + "1");      // in ra: int(8)     hai numeric string kiểu nguyên: kết quả int
var_dump("5" * "4");      // in ra: int(20)
var_dump(1 + "1e3");      // in ra: float(1001) "1e3" là numeric string dạng float
var_dump(true + true);    // in ra: int(2)
var_dump(null + 5);       // in ra: int(5)
```

Từ PHP 8.0, toán tử số học và bitwise gặp array, resource, object (trừ object của vài class nội bộ có
nạp chồng toán tử như GMP hay `BcMath\Number`), hoặc chuỗi không phải số (mục 12.2) thì ném
`TypeError` thay vì đoán một con số:

```php
<?php
declare(strict_types=1);

foreach ([fn () => [] + 1, fn () => new stdClass() + 1, fn () => 1 + "pigs"] as $f) {
    try {
        $f();
    } catch (TypeError $e) {
        echo $e->getMessage(), "\n";
    }
}
// in ra:
// Unsupported operand types: array + int
// Unsupported operand types: stdClass + int
// Unsupported operand types: int + string
```

(Ngoại lệ: `array + array` là phép **hợp** hai array, không phải phép cộng số; xem
[chương 06](06-mang.md).)

### 12.2 Numeric string: chuỗi nào được coi là số

Dữ liệu từ form, URL, cookie, file CSV... đều tới PHP dưới dạng **chuỗi** (dữ liệu từ database thì tuỳ
driver và cấu hình, xem [chương 16](16-php-va-database.md)). Vì vậy câu hỏi "chuỗi này có phải số
không" xuất hiện khắp nơi. PHP 8 chia chuỗi làm ba loại:

1. *Numeric string* (chuỗi số): khoảng trắng tuỳ chọn, dấu `+`/`-` tuỳ chọn, một số nguyên hoặc số
   thực (có thể có dấu chấm thập phân, có thể dạng mũ `e`), rồi khoảng trắng tuỳ chọn. **Toàn bộ**
   chuỗi phải khớp. Kiểm tra bằng `is_numeric()`.
2. *Leading-numeric string* (chuỗi bắt đầu bằng số): phần đầu là numeric string, theo sau là ký tự
   bất kỳ. Ví dụ `"42abc"`, `"10 pigs"`.
3. *Non-numeric string*: không thuộc hai loại trên. Ví dụ `"abc"`, `""`.

Kết quả `is_numeric()` trên PHP 8.5 (đã chạy thử):

| Chuỗi | Numeric? | Ghi chú |
|---|---|---|
| `"42"`, `"+7"`, `"-1.5"` | có | |
| `" 42"`, `"42 "`, `"\t42\n"` | có | khoảng trắng ở **hai đầu** đều hợp lệ (PHP 8) |
| `".5"`, `"5."`, `"0042"` | có | `"0042"` là 42 hệ 10, **không** phải hệ 8 |
| `"1e3"`, `"1.5e-3"` | có | ⚠️ dạng mũ: `"1e3"` là 1000 |
| `"0x1A"`, `"0b11"`, `"1_000"` | không | tiền tố hệ 16/hệ 2 và dấu `_` chỉ có nghĩa trong **code**, không có nghĩa trong chuỗi |
| `"42abc"`, `"1e"` | không | leading-numeric |
| `""`, `" "`, `"abc"`, `"- 1"` | không | chuỗi rỗng **không** phải số 0 |
| `"\u{A0}42"` | không | dấu cách không ngắt dòng (NBSP, hay gặp khi copy từ web) không được tính là khoảng trắng |

⚠️ Dạng mũ là nguồn bất ngờ: chuỗi có chữ `e` (hoặc `E`) kẹp giữa các chữ số là số. `"2E1"` là 20,
`"0E1"` là 0. Mục 13.5 cho thấy điều này dẫn tới lỗ hổng bảo mật thế nào.

**Chuỗi trong ngữ cảnh số học.** Luật của PHP 8 và khác biệt so với PHP 7 (RFC *Saner numeric
strings*, PHP 8.0):

| Loại chuỗi | Ví dụ | PHP 8 | PHP 7.x |
|---|---|---|---|
| Numeric | `1 + "10.5"` | `float(11.5)` | `float(11.5)` |
| Numeric, khoảng trắng cuối | `1 + "42 "` | `int(43)` | `int(43)` kèm Notice (PHP 7 coi là leading-numeric) |
| Leading-numeric | `1 + "10 pigs"` | `int(11)` kèm `Warning: A non-numeric value encountered` | `int(11)` kèm `Notice: A non well formed numeric value encountered` |
| Non-numeric | `1 + "pigs"`, `1 + ""` | `TypeError: Unsupported operand types: int + string` | `int(1)` kèm `Warning: A non-numeric value encountered` |

Tóm lại PHP 8 "nâng" mỗi mức lên một bậc: Notice thành Warning, Warning thành `TypeError`; riêng
khoảng trắng cuối thì từ "có vấn đề" thành hợp lệ.

### 12.3 Ép kiểu tường minh (cast)

*Type casting* là khi **bạn** chủ động đổi kiểu, bằng cách đặt tên kiểu trong ngoặc trước giá trị:

| Cast | Đổi sang | Hàm tương đương |
|---|---|---|
| `(int)` | `int` | `intval($x)` |
| `(float)` | `float` | `floatval($x)` |
| `(string)` | `string` | `strval($x)` |
| `(bool)` | `bool` | `boolval($x)` |
| `(array)` | `array` | |
| `(object)` | `object` (`stdClass`) | |

`settype($var, 'int')` đổi kiểu **ngay trên biến** (truyền tham chiếu) và trả `true`/`false`. PHP 8.5
còn có `(void)`, nhưng đó không phải phép đổi kiểu mà là cách nói "cố ý bỏ qua giá trị trả về" (đi kèm
attribute `#[\NoDiscard]`, chương 08).

Các tên cũ cần biết khi đọc code cũ:

| Cách viết | Tình trạng |
|---|---|
| `(integer)`, `(boolean)`, `(double)`, `(binary)` | Bí danh của `(int)`, `(bool)`, `(float)`, `(string)`. **Deprecated từ PHP 8.5**: `Deprecated: Non-canonical cast (integer) is deprecated, use the (int) cast instead` |
| `(real)` | Đã bỏ ở PHP 8.0: `Parse error: The (real) cast has been removed, use (float) instead` |
| `(unset)` | Đã bỏ ở PHP 8.0: `Fatal error: The (unset) cast is no longer supported` |

**Chuỗi sang số bằng cast.** Luật: numeric hoặc leading-numeric thì lấy phần số; còn lại ra `0`.
Khác ngữ cảnh số học, cast **không báo gì cả**, kể cả với chuỗi rác:

```php
<?php
declare(strict_types=1);

var_dump((int) "12abc");   // in ra: int(12)     leading-numeric: lấy phần đầu, KHÔNG có Warning
var_dump((int) "abc");     // in ra: int(0)      không phải số: ra 0, KHÔNG có lỗi
var_dump((int) "");        // in ra: int(0)
var_dump((int) " 12 ");    // in ra: int(12)
var_dump((int) "1.9");     // in ra: int(1)      cắt phần lẻ
var_dump((int) "1e3");     // in ra: int(1000)   dạng mũ được hiểu trọn
var_dump((int) "012");     // in ra: int(12)     KHÔNG phải hệ 8
var_dump((int) "0x1A");    // in ra: int(0)      KHÔNG phải hệ 16
var_dump((float) "1.5kg"); // in ra: float(1.5)
```

Muốn đọc chuỗi theo hệ cơ số khác thì dùng tham số thứ hai của `intval()`. Với `$base = 0`, PHP tự
đoán theo tiền tố: `0x` là hệ 16, `0b` là hệ 2, `0` là hệ 8, còn lại hệ 10:

```php
<?php
declare(strict_types=1);

var_dump(intval("42", 8));      // in ra: int(34)   "42" đọc theo hệ 8
var_dump(intval("101", 2));     // in ra: int(5)
var_dump(intval("0x1A", 16));   // in ra: int(26)
var_dump(intval("0x1A", 0));    // in ra: int(26)   base 0: tự nhận tiền tố 0x
var_dump(intval("012", 0));     // in ra: int(10)   base 0: số 0 đầu nghĩa là hệ 8
var_dump(intval("0b101", 0));   // in ra: int(5)
```

⚠️ **Cast không bao giờ thất bại**, nên nó không phải công cụ kiểm tra dữ liệu. `(int) $_GET['id']`
với input `"abc"` cho ra `0` trong im lặng, và `0` có thể là một ID hợp lệ trong logic của bạn. Khi
cần **kiểm tra** chuỗi có phải số nguyên không, dùng `filter_var()`, nó trả `int` hoặc `false`:

```php
<?php
declare(strict_types=1);

var_dump(filter_var("12", FILTER_VALIDATE_INT));     // in ra: int(12)
var_dump(filter_var("-5", FILTER_VALIDATE_INT));     // in ra: int(-5)
var_dump(filter_var(" 12 ", FILTER_VALIDATE_INT));   // in ra: int(12)     bỏ khoảng trắng hai đầu
var_dump(filter_var("12abc", FILTER_VALIDATE_INT));  // in ra: bool(false)
var_dump(filter_var("012", FILTER_VALIDATE_INT));    // in ra: bool(false) không nhận số 0 đầu
var_dump(filter_var("1e3", FILTER_VALIDATE_INT));    // in ra: bool(false)
var_dump(ctype_digit("123"), ctype_digit("-1"));      // in ra: bool(true) bool(false)  chỉ toàn chữ số?
```

Kiểm tra dữ liệu đầu vào một cách hệ thống (validation) ở [chương 15](15-php-va-web.md) và
[chương 25](25-laravel-request-validation-response.md).

### 12.4 Bảng tổng hợp đổi kiểu

Kết quả chạy thật trên PHP 8.5, để tra nhanh:

| Giá trị | `(bool)` | `(int)` | `(float)` | `(string)` |
|---|---|---|---|---|
| `true` | `true` | `1` | `1.0` | `"1"` |
| `false` | `false` | `0` | `0.0` | `""` |
| `null` | `false` | `0` | `0.0` | `""` |
| `0` | `false` | `0` | `0.0` | `"0"` |
| `-7` | `true` | `-7` | `-7.0` | `"-7"` |
| `1.9` | `true` | `1` | `1.9` | `"1.9"` |
| `""` | `false` | `0` | `0.0` | `""` |
| `"0"` | `false` | `0` | `0.0` | `"0"` |
| `" 12 "` | `true` | `12` | `12.0` | `" 12 "` |
| `"12abc"` | `true` | `12` | `12.0` | `"12abc"` |
| `"abc"` | `true` | `0` | `0.0` | `"abc"` |
| `"1e3"` | `true` | `1000` | `1000.0` | `"1e3"` |
| `[]` | `false` | `0` | `0.0` | `"Array"` kèm Warning |
| `[0]` | `true` | `1` | `1.0` | `"Array"` kèm Warning |

Với array, manual của `intval()` ghi: array rỗng cho `0`, array khác rỗng cho `1`. Ép object sang int
hay float thì manual nói hành vi là không xác định, đừng dựa vào.

## 13. So sánh: `==` và `===`

### 13.1 Hai toán tử, hai câu hỏi khác nhau

PHP có hai toán tử so sánh bằng, trả lời hai câu hỏi khác nhau:

- `$a === $b` (*identical*, đồng nhất): "cùng **kiểu** và cùng **giá trị**?" Không đổi kiểu gì cả.
  `1 === 1.0` là `false` vì một bên int, một bên float. Phủ định là `!==`.
- `$a == $b` (*equal*, bằng): "bằng nhau **sau khi** đã type juggling?" PHP đổi hai vế về cùng kiểu
  theo một bảng luật rồi mới so. `1 == 1.0` là `true`. Phủ định là `!=` (hoặc `<>`).

Với array và object, hai toán tử còn khác nhau về cách so:

| | `==` | `===` |
|---|---|---|
| array | cùng các cặp key/value (value so bằng `==`), **không** cần cùng thứ tự | cùng các cặp key/value, **cùng thứ tự**, value so bằng `===` |
| object | cùng class và các property bằng nhau theo `==` | **cùng một instance** (cùng một object trong bộ nhớ) |

```php
<?php
declare(strict_types=1);

var_dump([1, 2] == [1 => 2, 0 => 1]);    // in ra: bool(true)   cùng cặp key/value, khác thứ tự
var_dump([1, 2] === [1 => 2, 0 => 1]);   // in ra: bool(false)  khác thứ tự
var_dump(["1"] == [1]);                  // in ra: bool(true)   phần tử so bằng ==

final class Point
{
    public function __construct(public int $x, public int $y) {}
}
$p1 = new Point(1, 2);
$p2 = new Point(1, 2);
$p3 = $p1;
var_dump($p1 == $p2);    // in ra: bool(true)   cùng class, property bằng nhau
var_dump($p1 === $p2);   // in ra: bool(false)  hai object khác nhau
var_dump($p1 === $p3);   // in ra: bool(true)   cùng một object
```

### 13.2 Luật của `==`

Manual liệt kê luật so lỏng theo **thứ tự**: xét từ trên xuống, dòng nào khớp cặp kiểu trước thì dùng
dòng đó.

| Vế 1 | Vế 2 | Cách so |
|---|---|---|
| `null` hoặc string | string | Đổi `null` thành `""`, rồi so như số (nếu cả hai là numeric string) hoặc so chuỗi |
| `bool` hoặc `null` | bất kỳ | Đổi **cả hai vế** sang bool (`false < true`) |
| object | object | Class dựng sẵn có thể tự định nghĩa; khác class thì không so được; cùng class thì so từng property |
| string, resource, int, float | string, resource, int, float | So như số (từ PHP 8: chuỗi phải là numeric string, xem 13.3) |
| array | array | Ít phần tử hơn thì nhỏ hơn; so từng key |
| object | bất kỳ | object luôn lớn hơn |
| array | bất kỳ | array luôn lớn hơn |

Hai dòng hay dùng nhất để tự suy luận:

- **Một vế là `bool`, hoặc một vế là `null` mà vế kia không phải string**: cả hai đổi về bool, rồi
  dùng bảng falsy của mục 2.2. Vì vậy `null == 0`, `null == []`, `"0" == false` đều là
  `true`.
- **Hai chuỗi**: nếu **cả hai** là numeric string thì so như số (`"1" == "01"`, `"10" == "1e1"`
  đều `true`), ngược lại so từng byte (`"abc" == "ABC"` là `false`).

### 13.3 PHP 8 đã đổi gì: RFC Saner string to number comparisons

Trước PHP 8, so một **số** với một **chuỗi** bằng `==` thì PHP luôn ép chuỗi thành số rồi so hai số.
Chuỗi không phải số bị ép thành `0`, nên `0 == "foobar"` là `true`. RFC (tác giả Nikita Popov, áp dụng
từ PHP 8.0) gọi đây có lẽ là nguồn bug lớn nhất của so sánh lỏng, nhất là khi phép so bị giấu trong
`in_array()` hay `switch`. Luật mới cho `$number == $string`:

1. Nếu `$string` là numeric string: so như số, **giống hệt PHP 7**.
2. Nếu không: đổi `$number` thành chuỗi (`0` thành `"0"`), rồi so hai chuỗi.

Cách nhớ của RFC: "coi như đổi số thành chuỗi, rồi so lỏng hai chuỗi". Luật mới áp cho mọi phép so
lỏng: `==`, `!=`, `<`, `>`, `<=`, `>=`, `<=>`, `in_array()`/`array_search()`/`array_keys()` khi không
bật strict, `switch`, và các hàm sắp xếp như `sort()` với cờ mặc định `SORT_REGULAR`.

Bảng tổng hợp, PHP 7.4 so với PHP 8.x. Cả hai cột đã chạy thật: cột PHP 7.4 trên 7.4.33, cột PHP 8
trên 8.0 và 8.5 (cho cùng kết quả). Dòng đánh dấu ★ là dòng **đổi kết quả**:

| Nhóm | Biểu thức | PHP 7.4 | PHP 8.x | Giải thích |
|---|---|---|---|---|
| Số với numeric string | `42 == "42"` | `true` | `true` | so số |
| | `42 == "42.0"` | `true` | `true` | 42 = 42.0 |
| | `42 == "000042"` | `true` | `true` | số 0 đầu không ảnh hưởng |
| | `100 == "1e2"` | `true` | `true` | `"1e2"` là 100 |
| | `42 == " 42"` | `true` | `true` | khoảng trắng đầu hợp lệ ở cả hai bản |
| | `42 == "42 "` | `true` | `true` | PHP 7: leading-numeric, vẫn ép ra 42; PHP 8: numeric string |
| Chuỗi với chuỗi | `"1" == "01"` | `true` | `true` | hai numeric string: so số |
| | `"10" == "1e1"` | `true` | `true` | như trên |
| | `"0e1" == "0e99"` | `true` | `true` | cả hai là 0 × 10ⁿ = 0 (bẫy ở mục 13.5) |
| | `"1" == "1abc"` | `false` | `false` | một bên không numeric: so chuỗi |
| Số với chuỗi không phải số | ★ `0 == "a"` | `true` | `false` | PHP 8: `"0"` so với `"a"` |
| | ★ `0 == ""` | `true` | `false` | PHP 8: `"0"` so với `""` |
| | ★ `42 == "42abc"` | `true` | `false` | leading-numeric không còn được coi là số khi so |
| | `42 == "abc42"` | `false` | `false` | PHP 7 ép `"abc42"` ra 0 |
| | ★ `INF == "INF"` | `false` | `true` | PHP 8: `(string) INF` là `"INF"` |
| Có null | `null == false` | `true` | `true` | đổi về bool |
| | `null == 0` | `true` | `true` | đổi về bool: `false == false` |
| | `null == ""` | `true` | `true` | dòng "null với string": `null` thành `""` |
| | `null == "0"` | `false` | `false` | `""` so với `"0"` như chuỗi |
| | `null == []` | `true` | `true` | đổi về bool |
| Có bool | `true == "php"` | `true` | `true` | chuỗi khác rỗng, khác `"0"` là truthy |
| | `false == "0"` | `true` | `true` | `"0"` là falsy |
| | `false == "0.0"` | `false` | `false` | `"0.0"` là **truthy** |
| | `true == -1` | `true` | `true` | mọi số khác 0 là truthy |
| Có array | `[] == false` | `true` | `true` | array rỗng là falsy |
| | `[] == 0` | `false` | `false` | array luôn lớn hơn giá trị không phải array (trừ khi so với bool/null) |
| | ★ `[0] == ["a"]` | `true` | `false` | phần tử `0 == "a"` theo luật mới |

Để đọc bảng: dòng nào có một vế là bool hoặc null thì **mọi thứ đổi về bool**, và RFC không đụng tới
các dòng đó. RFC chỉ đổi đúng một ô của bảng luật: số so với chuỗi không phải numeric string.

Ví dụ trong manual, chạy trên hai phiên bản:

```php
<?php
declare(strict_types=1);   // không đổi gì: strict_types không áp dụng cho ==, switch (mục 14.5)

var_dump(0 == "a");       // PHP 7: bool(true)   PHP 8: bool(false)
var_dump("1" == "01");    // cả hai: bool(true)
var_dump("10" == "1e1");  // cả hai: bool(true)
var_dump(100 == "1e2");   // cả hai: bool(true)

switch ("a") {
    case 0:   echo "0\n"; break;   // PHP 7 khớp ở đây vì "a" == 0
    case "a": echo "a\n"; break;   // PHP 8 khớp ở đây
}
```

⚠️ Đây là thay đổi **im lặng**: code chạy được ở cả hai phiên bản nhưng cho kết quả khác, không có
Warning nào. Khi nâng một dự án cũ từ 7.x lên 8.x, mọi `==`, `in_array()` không strict, `switch` so
số với chuỗi đều cần xem lại.

### 13.4 So lỏng ẩn trong hàm và cấu trúc điều khiển

Nhiều chỗ trong PHP dùng `==` mà code không hề viết `==`:

| Cấu trúc | So bằng | Cách bật so chặt |
|---|---|---|
| `in_array($v, $arr)` | `==` | `in_array($v, $arr, true)` |
| `array_search($v, $arr)` | `==` | tham số thứ ba `true` |
| `array_keys($arr, $v)` | `==` | tham số thứ ba `true` |
| `switch` | `==` | không có; dùng `match` (PHP 8.0, so bằng `===`) |

```php
<?php
declare(strict_types=1);

var_dump(in_array('abc', [0]));           // in ra: bool(false)  (PHP 7: true)
var_dump(in_array('1e1', ['10']));        // in ra: bool(true)   hai numeric string so như số
var_dump(in_array(null, [0]));            // in ra: bool(true)   null với int: đổi về bool
var_dump(in_array('1e1', ['10'], true));  // in ra: bool(false)  so chặt

var_dump(array_search('x', ['x', 'y']));  // in ra: int(0)       tìm thấy ở vị trí 0, mà 0 là falsy!

echo match ("1") {
    1   => "khớp int 1",
    "1" => "khớp string \"1\"",
}, "\n";                                   // in ra: khớp string "1"   match so bằng ===
```

Ví dụ bug kiểm tra quyền: `in_array($input, [1, 2])` để kiểm tra `role_id` gửi lên. Với input chuỗi
`"1.0"` hay `" 1"`, cả PHP 7 lẫn PHP 8 đều cho qua (numeric string so như số). Truyền `true` ở tham số
thứ ba **và** ép/kiểm tra kiểu input tường minh (mục 12.3) mới chắc chắn. Chi tiết các hàm array ở
[chương 06](06-mang.md), `switch`/`match` ở [chương 07](07-toan-tu-dieu-khien.md).

### 13.5 Bẫy bảo mật: magic hash

Hai chuỗi dạng `"0e"` theo sau toàn chữ số là **numeric string** (ký hiệu khoa học) có giá trị 0, nên
bằng nhau theo `==` dù khác nhau hoàn toàn. Một số input cho ra hash MD5 đúng dạng đó:

```php
<?php
declare(strict_types=1);

$a = md5('240610708');
$b = md5('QNKCDZO');
echo $a, "\n";               // in ra: 0e462097431906509019562988736854
echo $b, "\n";               // in ra: 0e830400451993494058024219903391
var_dump($a == $b);          // in ra: bool(true)   cả hai là "0 × 10^..." = 0
var_dump($a === $b);         // in ra: bool(false)
var_dump(hash_equals($a, $b)); // in ra: bool(false)
```

Code so mật khẩu hay token kiểu `md5($input) == $storedHash` bị qua mặt bằng cách này, **kể cả trên
PHP 8**, vì hai vế đều là numeric string và luật so hai numeric string không đổi. Cách đúng:

- So chuỗi bí mật (token, chữ ký HMAC) bằng `hash_equals($known, $userInput)`: so chính xác từng byte
  **và** chạy trong thời gian không phụ thuộc vị trí byte sai đầu tiên, chống *timing attack* (đoán
  dần token bằng cách đo thời gian phản hồi). `===` so đúng nhưng có thể dừng ngay ở byte khác nhau
  đầu tiên, nên thời gian so để lộ thông tin.
- Mật khẩu thì không tự hash bằng MD5; dùng `password_hash()` và `password_verify()`.

Chi tiết ở [chương 17](17-bao-mat.md).

### 13.6 So sánh float, NAN và object với bool

Ba trường hợp cuối, đã gặp ở các mục trước, gom lại cho đủ:

- **Float**: không so bằng `==` hay `===` (mục 4.4).
- **NAN**: không bằng bất cứ thứ gì kể cả chính nó, trừ khi so lỏng với `true` (mục 4.7).
- **Object không so được với nhau (enum, `CurlHandle`...) so lỏng với bool**: từ PHP 8.5 luôn tính như
  `(bool) $object`, mà các object này luôn truthy. Trước 8.5 kết quả phụ thuộc cách viết: so với literal
  `true` thì như `(bool)`, so với một **biến** bool thì luôn ra `false`:

  ```php
  <?php
  declare(strict_types=1);

  enum Status { case Active; }

  $t = true;
  var_dump(Status::Active == true);   // in ra: bool(true)  ở cả 8.4 và 8.5
  var_dump(Status::Active == $t);     // PHP 8.4: bool(false)   PHP 8.5: bool(true)
  ```

### 13.7 Thói quen nên có

- Mặc định dùng `===` và `!==`. Chỉ dùng `==` khi bạn **cố ý** muốn type juggling và biết luật.
- Truyền `true` cho tham số strict của `in_array`, `array_search`, `array_keys`.
- Dùng `match` thay cho `switch` khi so giá trị.
- Kết quả kiểu `int|false` thì so `=== false` (mục 2.3).
- Chuẩn hoá kiểu ở **ranh giới** (input từ request, dữ liệu từ database) càng sớm càng tốt, để phần
  còn lại của code làm việc với kiểu đúng.

Đối chiếu: JavaScript cũng có `==` lỏng và `===` chặt, với bẫy tương tự (`0 == ""` là `true` trong
JS, trong PHP 8 là `false`). Java không có so sánh lỏng giữa hai kiểu khác nhau; bẫy của Java là `==`
trên object so **reference** (`new String("a") == new String("a")` là `false`), phải dùng `equals()`.
Go không cho so hai kiểu khác nhau, lỗi ngay lúc biên dịch.

## 14. strict_types: chế độ ép kiểu và chế độ chặt

### 14.1 Hai chế độ kiểm tra kiểu scalar

Khi một giá trị đi qua "cửa" có khai báo kiểu **scalar** (`int`, `float`, `string`, `bool`), PHP có
hai cách xử lý:

- *Coercive mode* (chế độ ép kiểu, mặc định): nếu giá trị sai kiểu nhưng đổi được một cách "rõ ràng"
  sang kiểu khai báo, PHP tự đổi. Ví dụ chuỗi `"5"` vào tham số `int` thành `5`.
- *Strict mode* (chế độ chặt): chỉ nhận đúng kiểu, sai là `TypeError`. Ngoại lệ duy nhất: `int` được
  nhận ở chỗ khai báo `float` (mục 14.4).

Bảng dưới chạy thật trên PHP 8.5, với các hàm `fi(int $x)`, `ff(float $x)`, `fs(string $x)`,
`fb(bool $x)`:

| Lời gọi | Coercive mode | Strict mode |
|---|---|---|
| `fi(5)` | `5` | `5` |
| `fi("5")` | `5` | `TypeError` |
| `fi(" 5 ")` | `5` (khoảng trắng hai đầu hợp lệ từ 8.0) | `TypeError` |
| `fi("1e3")` | `1000` | `TypeError` |
| `fi("5abc")` | `TypeError` (PHP 7: `5` kèm Notice) | `TypeError` |
| `fi("")` | `TypeError` | `TypeError` |
| `fi(5.0)` | `5` | `TypeError` |
| `fi(5.5)` | `5` kèm `Deprecated: Implicit conversion from float 5.5 to int loses precision` (8.1+) | `TypeError` |
| `fi(true)` | `1` | `TypeError` |
| `fi(null)` | `TypeError` (hàm tự viết không bao giờ ép `null`) | `TypeError` |
| `ff(5)` | `5.0` | `5.0` (int vào float: được phép) |
| `ff("1.5")` | `1.5` | `TypeError` |
| `fs(5)` | `"5"` | `TypeError` |
| `fs(true)` | `"1"` | `TypeError` |
| `fb(1)` | `true` | `TypeError` |
| `fb("0")` | `false` | `TypeError` |

Coercive mode **không** dễ dãi như ép kiểu `(int)`: tham số `int` chỉ nhận chuỗi là numeric string
(mục 12.2), nên `"5abc"` và `""` bị từ chối, trong khi `(int) "5abc"` cho `5` và `(int) ""` cho `0`.

### 14.2 Bật strict mode

Đặt `declare(strict_types=1);` làm **câu lệnh đầu tiên** của file:

```php
<?php
declare(strict_types=1);

// phần còn lại của file
```

PHP rất khắt khe về vị trí (đã chạy thử):

| Viết sai | Lỗi |
|---|---|
| Có câu lệnh khác trước `declare` (kể cả `namespace`) | `Fatal error: strict_types declaration must be the very first statement in the script` |
| Có HTML/văn bản trước thẻ `<?php` | lỗi như trên (văn bản đó cũng được tính là output, tức là một câu lệnh) |
| `declare(strict_types=1) { ... }` | `Fatal error: strict_types declaration must not use block mode` |

Comment trước `declare` thì được. `namespace` phải đứng **sau** `declare`.

Strict mode có hiệu lực **theo từng file**: chỉ file có dòng `declare` này mới chạy chặt. Một file
strict `require` một file không strict thì file kia vẫn chạy chế độ ép kiểu, và ngược lại.

### 14.3 Áp dụng ở đâu: theo file của câu lệnh

Đây là điểm hay bị hỏi nhất, và dễ hiểu sai nhất. Strict mode được quyết định bởi **file chứa câu
lệnh đang truyền giá trị qua cửa**, không phải file định nghĩa hàm:

| Cửa | Chế độ được quyết định bởi |
|---|---|
| Tham số khi gọi hàm (kể cả hàm có sẵn như `strlen`) | file chứa **lời gọi** |
| Giá trị trả về | file chứa **định nghĩa hàm** (nơi có câu `return`) |
| Gán property có kiểu | file chứa **câu lệnh gán** |

Ví dụ với ba file:

```php
<?php
// lib_loose.php: KHÔNG có declare(strict_types=1)
function twice(int $x): int { return $x * 2; }
function asInt(): int { return "5"; }    // return sai kiểu, nhưng file này không strict
```

```php
<?php
declare(strict_types=1);
// lib_strict.php: CÓ strict
function triple(int $x): int { return $x * 3; }
function asIntStrict(): int { return "5"; }   // return sai kiểu trong file strict
```

```php
<?php
declare(strict_types=1);
// app.php: file gọi, CÓ strict
require __DIR__ . '/lib_loose.php';
require __DIR__ . '/lib_strict.php';

try {
    twice("5");
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: twice(): Argument #1 ($x) must be of type int, string given, called in .../app.php on line ...
}

var_dump(asInt());   // in ra: int(5)   return được kiểm theo lib_loose.php (không strict): "5" bị ép thành 5

try {
    asIntStrict();
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";   // in ra: asIntStrict(): Return value must be of type int, string returned
}

try {
    strlen(123);     // hàm có sẵn cũng bị kiểm chặt khi gọi từ file strict
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";   // in ra: strlen(): Argument #1 ($string) must be of type string, int given
}
```

Nếu đổi `app.php` thành **không** strict thì `twice("5")` và `triple("5")` đều chạy (ra `10` và
`15`), `strlen(123)` ra `3`, nhưng `asIntStrict()` vẫn ném `TypeError` vì return của nó nằm trong file
strict.

Lý do thiết kế: strict mode là lựa chọn của **người viết câu lệnh**. Người gọi hàm nói "code của tôi
cam kết truyền đúng kiểu"; người viết hàm nói "hàm của tôi cam kết trả đúng kiểu". Người viết thư viện
không áp được lựa chọn của mình lên code của người dùng thư viện, và ngược lại.

Cùng logic cho property: lệnh gán `$box->n = "7";` (property `int $n`) bị `TypeError` nếu câu gán
nằm trong file strict, và được ép thành `7` nếu câu gán nằm trong file không strict, bất kể class được
định nghĩa ở file nào.

### 14.4 Ngoại lệ duy nhất: int vào chỗ float

Kể cả ở strict mode, giá trị `int` được nhận ở chỗ khai báo `float`, và được đổi thành float. RFC gốc
gọi đây là *widening* (mở rộng, mượn khái niệm "widening primitive conversion" của Java) và ghi rõ
không có kiểm tra tràn hay mất chính xác: số nguyên lớn hơn 2⁵³ có thể bị làm tròn (mục 4.6).

```php
<?php
declare(strict_types=1);

function half(float $x): float
{
    return $x / 2;
}

var_dump(half(5));     // in ra: float(2.5)   int 5 được nhận, đổi thành 5.0
// half("5");          // TypeError: chuỗi thì không
```

### 14.5 Không áp dụng ở đâu

Manual nói ngắn gọn: strict typing **chỉ được định nghĩa cho khai báo kiểu scalar**. Mọi type juggling
khác vẫn chạy y như cũ trong file strict:

| Vẫn type juggling bình thường | Ví dụ trong file strict |
|---|---|
| Toán tử số học, bitwise | `"5" + 1` ra `6` |
| So sánh lỏng | `"abc" == 0` ra `false` (luật PHP 8), `null == 0` ra `true` |
| Điều kiện | `if ("0")` không chạy nhánh |
| Ép kiểu tường minh | `(int) "12abc"` ra `12` |
| Ngữ cảnh chuỗi | `echo 1.5;`, `"x = $x"` |
| Key của array | `$a["1"]` là key int `1` |
| `switch`, `in_array()` không strict | vẫn so bằng `==` |

⚠️ Thêm một chỗ ít người biết: **hàm do hàm có sẵn gọi lại** (callback của `array_map`, `usort`,
`array_filter`...) không chịu ảnh hưởng của `strict_types`. Manual: "Function calls from within
internal functions will not be affected by the strict_types declaration." Lời gọi callback xuất phát
từ mã C của `array_map`, không phải từ file của bạn, nên chạy theo chế độ ép kiểu:

```php
<?php
declare(strict_types=1);

$doubled = array_map(fn (int $x): int => $x * 2, ['1', '2']);
var_dump($doubled);   // in ra: array(2) { [0]=> int(2) [1]=> int(4) }   chuỗi bị ép thành int, không lỗi

var_dump(array_map('strlen', [123, 4567]));   // in ra: array(2) { [0]=> int(3) [1]=> int(4) }
// trong khi gọi trực tiếp strlen(123) ở file này là TypeError
```

Hệ quả thực tế: đừng tin rằng file có `strict_types` thì mọi tham số `int` trong closure đều đã được
kiểm chặt. Một array chuỗi (đọc từ file CSV chẳng hạn) đi qua `array_map` vẫn bị ép lặng lẽ.

### 14.6 null vào hàm có sẵn

Hàm **tự viết** chưa bao giờ ép `null` vào tham số scalar không nullable (luôn `TypeError`). Hàm **có
sẵn** thì khác: ở coercive mode, PHP từng âm thầm đổi `null` thành `""`, `0`, `0.0` hoặc `false`. Từ
PHP 8.1 việc này bị Deprecated (RFC dự kiến thành `TypeError` ở bản major tiếp theo); ở strict mode
thì đã là `TypeError`:

```php
<?php
// file KHÔNG strict
var_dump(strlen(null));
// Deprecated: strlen(): Passing null to parameter #1 ($string) of type string is deprecated
// in ra: int(0)
```

```php
<?php
declare(strict_types=1);

var_dump(strlen(null));
// Fatal error: Uncaught TypeError: strlen(): Argument #1 ($string) must be of type string, null given
```

Đây là một trong những cảnh báo hay gặp khi nâng dự án từ 7.4 lên 8.x, thường do giá trị `null` từ
cột database cho phép NULL hoặc từ tham số request không được gửi lên. Sửa ở gốc: quyết định rõ `null` nghĩa là gì
(`$name ?? ''`), đừng tắt cảnh báo.

### 14.7 Có nên bật strict_types không?

Lợi ích:

- Lỗi kiểu lộ ra ngay tại dòng gọi sai, thay vì một giá trị bị ép lặng lẽ chạy tiếp (ví dụ `"5abc"`
  từ PHP 7, `5.5` bị cắt thành `5`).
- Code nói rõ ý: chỗ nào cần đổi kiểu thì phải viết ra (`(int) $id`, `filter_var(...)`).
- Hành vi gần với Java/Go, dễ suy luận hơn.

Cái giá:

- Phải đổi kiểu tường minh ở **ranh giới**: dữ liệu từ request, từ file là chuỗi; dữ liệu từ
  database có kiểu tuỳ driver và cấu hình.
- Không bảo vệ được những chỗ ở mục 14.5.

Thói quen phổ biến cho code mới: bật `declare(strict_types=1);` ở **mọi file**, đổi và kiểm tra kiểu
một lần ở ranh giới (controller, lớp đọc dữ liệu), rồi để phần lõi làm việc với kiểu đúng. Kết hợp
công cụ phân tích tĩnh ([chương 21](21-chat-luong-code.md)) để bắt lỗi kiểu trước khi chạy. Chi tiết
về tham số hàm (mặc định, named arguments, variadic) ở [chương 08](08-ham.md).

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| `if (strpos($s, 'a'))` | Tìm thấy ở vị trí `0` thì `0` là falsy, bị coi như không thấy | So `!== false`, hoặc dùng `str_contains()` (mục 2.3) |
| Coi `"0.0"`, `" "`, `"false"`, `[0]` là falsy | Chuỗi chỉ falsy khi là `""` hoặc `"0"`; array chỉ falsy khi rỗng | Thuộc bảng falsy (mục 2.2), kiểm tra cụ thể thay vì `if ($x)` |
| `0.1 + 0.2 == 0.3`, dùng float cho tiền | Float nhị phân không biểu diễn đúng 0.1 | So bằng epsilon; tiền dùng int đơn vị nhỏ nhất hoặc BCMath (mục 4.4, 4.8) |
| Tin vào số `echo` in ra khi debug float | `echo` làm tròn còn 14 chữ số (`precision`) | Dùng `var_dump` hoặc `printf('%.20f')` (mục 4.3) |
| Không để ý int tràn sang float | Vượt `PHP_INT_MAX` không báo lỗi, chỉ mất chính xác | Giữ ID lớn dạng chuỗi, `JSON_BIGINT_AS_STRING`, GMP/BCMath (mục 3.3, 3.5) |
| Viết `-9223372036854775808` hay `0123` | Literal thứ nhất thành float; literal thứ hai là hệ 8 (= 83) | Dùng `PHP_INT_MIN`; viết hệ 8 bằng `0o`, số có 0 đầu thì để dạng chuỗi (mục 3.1, 3.3) |
| `(int) $_GET['id']` để "kiểm tra" input | Cast không bao giờ lỗi: `"abc"` thành `0` lặng lẽ | `filter_var($v, FILTER_VALIDATE_INT)` trả `int` hoặc `false` (mục 12.3) |
| `gettype($x) === 'float'` | `gettype` trả `"double"` | `is_float($x)` hoặc `get_debug_type($x)` (mục 1.4) |
| `in_array($v, $list)`, `switch` với dữ liệu lẫn kiểu | So lỏng `==` | Tham số strict `true`; dùng `match` (mục 13.4) |
| `md5($input) == $hash` | Magic hash `"0e..."`: hai numeric string bằng 0 | `hash_equals()`, `password_verify()` (mục 13.5) |
| Nâng 7.4 lên 8.x mà không rà `==` | `0 == "abc"` đổi từ `true` sang `false` không báo gì | Tìm các phép so số với chuỗi, chuyển sang `===` (mục 13.3) |
| Nghĩ `strict_types` chặn mọi type juggling | Nó chỉ áp cho khai báo kiểu scalar; không áp cho toán tử, `==`, callback của hàm có sẵn | Nhớ bảng mục 14.5; tự đổi kiểu ở ranh giới |
| Nghĩ strict mode theo file **định nghĩa** hàm | Tham số theo file **gọi**, return theo file định nghĩa, property theo file gán | Mục 14.3 |
| `function f(Foo $x = null)` | Nullable ngầm, Deprecated từ 8.4 | Viết `?Foo $x = null` (mục 11.4) |
| Truyền `null` vào hàm có sẵn (`strlen(null)`) | Deprecated từ 8.1, `TypeError` ở strict mode | Xử lý null tường minh: `$s ?? ''` (mục 14.6) |
| `public callable $fn;` | `callable` không dùng được cho property | Khai báo `Closure` (mục 10.1) |
| `is_resource($ch)` sau `curl_init()` trên PHP 8 | `curl_init()` trả object `CurlHandle` | Kiểm tra `=== false` (mục 9) |

## Tóm tắt chương

- PHP là ngôn ngữ kiểu động: biến không có kiểu, **giá trị** mới có kiểu. Engine lưu nhãn kiểu cùng
  giá trị trong zval.
- Các kiểu: scalar (`bool`, `int`, `float`, `string`), `array`, `object`, `null`, `resource`, cộng
  `callable` và `iterable` mô tả khả năng. Xem kiểu bằng `var_dump`, `get_debug_type`, kiểm tra bằng
  `is_*`.
- `int` là số nguyên có dấu 64 bit (trên bản 64 bit); vượt giới hạn thì thành `float`, không báo lỗi.
  `float` là IEEE 754 double, khoảng 15 chữ số có nghĩa: không so bằng, không dùng cho tiền.
- Falsy: `false`, `0`, `0.0`, `-0.0`, `""`, `"0"`, `[]`, `null` (cộng vài object nội bộ như GMP mang
  giá trị 0). Mọi thứ khác là truthy.
- Khai báo kiểu có ở tham số, return, property, hằng class; PHP kiểm tra lúc chạy, sai thì `TypeError`.
  Ghép kiểu bằng `?T`, `A|B`, `A&B`, `(A&B)|C`; kiểu đặc biệt `mixed`, `void`, `never`, `static`.
- Type juggling theo sáu ngữ cảnh. Numeric string (PHP 8) cho phép khoảng trắng hai đầu; trong phép
  tính, leading-numeric báo Warning, non-numeric ném `TypeError`. Cast tường minh không bao giờ báo lỗi.
- `===` so kiểu và giá trị; `==` đổi kiểu theo bảng luật. PHP 8 đổi phép so số với chuỗi không phải
  số: số được đổi thành chuỗi, nên `0 == "a"` là `false`. Magic hash vẫn còn ở PHP 8.
- `strict_types=1` chỉ áp cho khai báo kiểu scalar, theo file của câu lệnh (gọi, return, gán); int vào
  float vẫn được nhận; không áp cho toán tử, so sánh, cast, callback do hàm có sẵn gọi.
- Các mốc cần nhớ: 8.0 (union, mixed, so sánh mới, numeric string mới), 8.1 (never, intersection,
  Deprecated float lẻ sang int, null vào hàm có sẵn), 8.2 (DNF, `null`/`false`/`true` đứng riêng),
  8.3 (hằng có kiểu), 8.4 (nullable ngầm Deprecated), 8.5 (Warning khi ép float ngoài khoảng/NAN, bí
  danh cast cũ Deprecated).

## Câu hỏi tự kiểm tra

1. "Biến không có kiểu, giá trị mới có kiểu" nghĩa là gì? Engine biết kiểu của một giá trị bằng cách
   nào? (mục 1.2, 1.5)
2. Kể đủ các giá trị falsy. `"0.0"`, `" "`, `[0]`, `new stdClass()` là truthy hay falsy?
3. `PHP_INT_MAX + 1` cho ra gì? Vì sao `-9223372036854775808` viết trong code lại là float? (mục 3.3)
4. Vì sao `0.1 + 0.2 !== 0.3`, và vì sao `echo 0.1 + 0.2` vẫn in `0.3`? (mục 4.2, 4.3)
5. Khác nhau giữa `void` và `never`? Vì sao `?mixed` là lỗi còn `?string` thì không?
6. `?string $name`, `string $name = null` và `?string $name = null` khác nhau thế nào? PHP 8.4 nói gì
   về cách viết thứ hai? (mục 11.4)
7. Phân loại `"42"`, `"42 "`, `"42abc"`, `"1e3"`, `"0x1A"`, `""` thành numeric, leading-numeric hay
   non-numeric. `1 + "10 pigs"` và `1 + "pigs"` cho kết quả gì ở PHP 7.4 và PHP 8? (mục 12.2)
8. Dự đoán kết quả của `0 == "a"`, `"1" == "01"`, `null == 0`, `null == "0"`, `[0] == ["a"]` ở PHP 7.4
   và PHP 8, kèm tên luật đã dùng. (mục 13.2, 13.3)
9. File A có `strict_types=1` gọi hàm `f(int $x): int` định nghĩa trong file B không strict, truyền
   `"5"`. Chuyện gì xảy ra? Nếu `f` có `return "5";` thì sao? (mục 14.3)
10. Kể ít nhất ba chỗ mà `strict_types=1` không có tác dụng, và giải thích vì sao callback của
    `array_map` thuộc nhóm này. (mục 14.5)

## Bài tập

1. **Bảng kiểu của riêng bạn.** Viết `type_table.php` nhận một danh sách giá trị: `true`, `0`, `-0.0`,
   `"0"`, `""`, `"0.0"`, `" "`, `null`, `[]`, `[0]`, `"abc"`, `"12abc"`, `" 12 "`, `"1e3"`, `1.5`,
   `NAN`. Với mỗi giá trị in ra một dòng: `get_debug_type`, `(bool)`, `(int)`, `is_numeric`, và kết quả
   `== 0`, `== ""`, `== null`. Dự đoán từng ô **trước** khi chạy, đánh dấu những ô bạn đoán sai. Nếu
   chạy được cả PHP 8.4 và 8.5, so sánh hai output và giải thích dòng nào khác.

2. **Đọc số lượng từ input.** Viết hàm `parseQuantity(string $input): int` cho form đặt hàng: nhận
   `"5"`, `" 5 "`, `"12"`; từ chối (ném `InvalidArgumentException` với thông báo rõ ràng) `"5abc"`,
   `""`, `"5.5"`, `"-1"`, `"0"`, `"1e3"`, `"0x1A"`. Không dùng `(int)` để kiểm tra. Viết thêm một đoạn
   code duyệt qua tất cả input trên và in kết quả hoặc thông báo lỗi của từng cái.

3. **Tiền không dùng float.** Viết class `Money` lưu số tiền bằng `int` (đơn vị xu) với các method
   `fromString(string $amount): self` (nhận `"19.99"`, `"0.1"`, `"5"`), `add(Money $other): self`,
   `multiply(int $factor): self`, `format(): string` (trả `"19.99"`). Không được có giá trị float ở bất
   kỳ bước nào (gợi ý: tách phần nguyên và phần lẻ bằng xử lý chuỗi). Kiểm tra: cộng `"0.10"` mười lần
   phải ra `"1.00"`; `"19.99"` nhân 3 phải ra `"59.97"`. Làm lại bằng `bcadd`/`bcmul`, hoặc
   `BcMath\Number` nếu có PHP 8.4+.

4. **Thí nghiệm strict_types.** Dựng lại ba file của mục 14.3, thêm vào mỗi file thư viện một class có
   property `public int $n` và một hàm gán `$obj->n = "7"`. Trong `app.php` viết 8 đến 10 lời gọi khác
   nhau (truyền tham số, nhận return, gán property trực tiếp và qua hàm, gọi `array_map` với closure có
   tham số `int`, gọi `strlen(123)`). Ghi dự đoán cho từng lời gọi, chạy, rồi đổi `app.php` sang không
   strict và chạy lại. Viết ba câu tóm tắt quy tắc bằng lời của bạn.

## Đọc thêm

PHP manual (php.net):

- [Types: Introduction](https://www.php.net/manual/en/language.types.intro.php),
  [Type System](https://www.php.net/manual/en/language.types.type-system.php)
- Từng kiểu: [Booleans](https://www.php.net/manual/en/language.types.boolean.php),
  [Integers](https://www.php.net/manual/en/language.types.integer.php),
  [Floating point numbers](https://www.php.net/manual/en/language.types.float.php),
  [Numeric strings](https://www.php.net/manual/en/language.types.numeric-strings.php),
  [Strings](https://www.php.net/manual/en/language.types.string.php) (mục Converting to string),
  [Arrays](https://www.php.net/manual/en/language.types.array.php) (mục Converting to array),
  [Objects](https://www.php.net/manual/en/language.types.object.php),
  [NULL](https://www.php.net/manual/en/language.types.null.php),
  [Resources](https://www.php.net/manual/en/language.types.resource.php),
  [Callables](https://www.php.net/manual/en/language.types.callable.php),
  [Iterables](https://www.php.net/manual/en/language.types.iterable.php),
  [Mixed](https://www.php.net/manual/en/language.types.mixed.php),
  [Void](https://www.php.net/manual/en/language.types.void.php),
  [Never](https://www.php.net/manual/en/language.types.never.php),
  [Relative class types](https://www.php.net/manual/en/language.types.relative-class-types.php),
  [Singleton types](https://www.php.net/manual/en/language.types.singleton.php)
- [Type declarations](https://www.php.net/manual/en/language.types.declarations.php) (có mục Strict
  typing và bảng changelog theo phiên bản)
- [Type Juggling](https://www.php.net/manual/en/language.types.type-juggling.php),
  [Comparison Operators](https://www.php.net/manual/en/language.operators.comparison.php),
  [PHP type comparison tables](https://www.php.net/manual/en/types.comparisons.php)
- Hàm: [get_debug_type](https://www.php.net/manual/en/function.get-debug-type.php),
  [gettype](https://www.php.net/manual/en/function.gettype.php),
  [intval](https://www.php.net/manual/en/function.intval.php),
  [is_numeric](https://www.php.net/manual/en/function.is-numeric.php),
  [settype](https://www.php.net/manual/en/function.settype.php),
  [filter_var](https://www.php.net/manual/en/function.filter-var.php),
  [hash_equals](https://www.php.net/manual/en/function.hash-equals.php),
  [BcMath\Number](https://www.php.net/manual/en/class.bcmath-number.php)
- Thiết lập `precision`, `serialize_precision`: [php.ini core directives](https://www.php.net/manual/en/ini.core.php)

RFC (wiki.php.net), theo thứ tự phiên bản:

- 7.0: [Scalar Type Declarations](https://wiki.php.net/rfc/scalar_type_hints_v5) (nguồn gốc `strict_types`)
- 7.1: [Iterable](https://wiki.php.net/rfc/iterable)
- 8.0: [Union Types 2.0](https://wiki.php.net/rfc/union_types_v2),
  [Mixed Type v2](https://wiki.php.net/rfc/mixed_type_v2),
  [Static return type](https://wiki.php.net/rfc/static_return_type),
  [Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison),
  [Saner numeric strings](https://wiki.php.net/rfc/saner-numeric-strings),
  [Stricter type checks for arithmetic/bitwise operators](https://wiki.php.net/rfc/arithmetic_operator_type_checks),
  [Locale-independent float to string cast](https://wiki.php.net/rfc/locale_independent_float_to_string)
- 8.1: [noreturn type](https://wiki.php.net/rfc/noreturn_type) (RFC có vote chọn tên giữa `noreturn`
  và `never`; tên được chọn là `never`),
  [Pure intersection types](https://wiki.php.net/rfc/pure-intersection-types),
  [Deprecate implicit non-integer-compatible float to int conversions](https://wiki.php.net/rfc/implicit-float-int-deprecate),
  [Deprecate passing null to non-nullable arguments of internal functions](https://wiki.php.net/rfc/deprecate_null_to_scalar_internal_arg)
- 8.2: [Disjunctive Normal Form Types](https://wiki.php.net/rfc/dnf_types),
  [Allow null and false as stand-alone types](https://wiki.php.net/rfc/null-false-standalone-types),
  [Add true type](https://wiki.php.net/rfc/true-type)
- 8.3: [Typed class constants](https://wiki.php.net/rfc/typed_class_constants)
- 8.4: [Deprecate implicitly nullable parameter types](https://wiki.php.net/rfc/deprecate-implicitly-nullable-types)
- 8.5: [Warnings for PHP 8.5](https://wiki.php.net/rfc/warnings-php-8-5) (ép float ngoài khoảng, NAN),
  [Deprecations for PHP 8.5](https://wiki.php.net/rfc/deprecations_php_8_5) (bí danh cast, `null` làm key)

Khác:

- [php-src UPGRADING của PHP 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) (danh sách
  thay đổi chính thức; các bản trước nằm ở nhánh `PHP-8.x` tương ứng)
- [The Floating-Point Guide](https://floating-point-gui.de/): giải thích dễ hiểu vì sao số thực "cộng
  không ra" (manual PHP cũng dẫn tới trang này)
- Nikita Popov, [Internal value representation in PHP 7, part 1](https://www.npopov.com/2015/05/05/Internal-value-representation-in-PHP-7-part-1.html):
  zval từ bên trong (đọc sau khi học chương 19)
