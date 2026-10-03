# Chương 22. Tổng hợp PHP 8.0 tới 8.5

> [← Mục lục](README.md) · [← Chương 21: Chất lượng code: test, phân tích tĩnh, chuẩn code](21-chat-luong-code.md) · [Chương 23: Laravel: giới thiệu và cấu trúc dự án →](23-laravel-gioi-thieu.md)

**Bạn sẽ học được:**

- Một bản PHP mới mang theo ba loại thay đổi (tính năng mới, deprecation, thay đổi phá vỡ tương
  thích) và cách đọc tài liệu gốc của từng bản: `UPGRADING`, migration guide, RFC.
- Từng bản 8.0, 8.1, 8.2, 8.3, 8.4, 8.5 thêm gì, đánh dấu deprecated gì và làm hỏng gì; mỗi tính năng
  kèm link tới chương đã giải thích chi tiết.
- Những thay đổi "âm thầm đổi kết quả" nguy hiểm nhất khi nâng từ PHP 7 lên 8.
- Quy trình nâng cấp một dự án lên bản PHP mới một cách an toàn: test, PHPStan, Rector, CI chạy nhiều
  phiên bản, đọc log deprecation, triển khai từng bước.

**Cần biết trước:** chương này là chương tổng hợp, nó điểm lại tính năng đã học ở các chương trước
thay vì dạy lại. Nên đọc trước [Chương 01](01-php-la-gi.md) (mục 2: phiên bản và vòng đời),
[Chương 04](04-kieu-du-lieu.md), [Chương 08](08-ham.md), [Chương 09](09-oop-co-ban.md),
[Chương 10](10-oop-nang-cao.md), [Chương 12](12-loi-exception.md) và
[Chương 21](21-chat-luong-code.md) (test, PHPStan, Rector). Nếu chưa đọc, bạn vẫn đọc được chương này
như một bản đồ, rồi theo link quay lại chương gốc khi cần.

Cách đọc chương này: mục 1 giải thích cách một bản PHP thay đổi và cách đọc tài liệu của nó. Mục 2
tới 7 đi qua từng bản, mỗi bản có ba phần giống nhau: tính năng chính, deprecation, thay đổi phá vỡ
tương thích. Mục 8 gom tất cả vào vài bảng tra cứu nhanh. Mục 9 là quy trình nâng cấp. Mọi ví dụ PHP
trong chương đã chạy thật trên đúng bản PHP được ghi (8.5, 8.4, 8.3... tuỳ ví dụ); output ghi trong
comment `// in ra: ...`. Mọi mục trong danh sách thay đổi đã được đối chiếu với file `UPGRADING` của
php-src và RFC tương ứng (link ở cuối mỗi mục và trong phần Đọc thêm).

## 1. Một bản PHP mới thay đổi những gì

### 1.1 Vì sao cần một chương tổng hợp

Các chương trước dạy ngôn ngữ theo chủ đề: kiểu dữ liệu, hàm, OOP, exception... Trong mỗi chủ đề có
ghi "tính năng này có từ PHP 8.1", "cái kia deprecated từ 8.4". Khi làm việc thật, bạn lại hay gặp câu
hỏi theo chiều ngược lại:

- Dự án đang chạy PHP 8.1, công ty muốn lên 8.4. Những gì có thể hỏng? Có gì mới đáng dùng?
- Một thư viện ghi "yêu cầu PHP 8.2". Nghĩa là nó dùng tính năng gì mà 8.1 không có?
- Phỏng vấn: "PHP 8.0 có gì mới?", "Kể vài thay đổi của 8.4?".
- Đọc code cũ thấy `${var}` trong chuỗi, `utf8_encode()`, `$obj->prop` không khai báo... cái nào còn
  dùng được, cái nào đang phát deprecation, cái nào sẽ lỗi ở bản tới?

Chương này trả lời các câu đó bằng cách xếp lại kiến thức theo trục thời gian. Nó không giải thích lại
từng tính năng từ đầu (đã có ở chương gốc, có link), mà tập trung vào: bản nào thêm gì, bản nào bỏ gì,
và làm sao đi từ bản cũ sang bản mới mà không làm hỏng production.

### 1.2 Ba loại thay đổi trong một bản minor

Nhắc lại từ [Chương 01, mục 2.1](01-php-la-gi.md#21-đọc-số-phiên-bản): PHP đánh số
`major.minor.patch`. Bản patch (8.4.25 lên 8.4.26) chỉ sửa lỗi. Bản minor (8.4 lên 8.5) và major (7.4
lên 8.0) mới mang thay đổi đáng kể, chia làm ba loại:

| Loại | Nghĩa | Code cũ của bạn bị ảnh hưởng thế nào | Ví dụ |
|---|---|---|---|
| Tính năng mới (*new feature*) | Cú pháp, hàm, class mới | Không ảnh hưởng. Chỉ là code mới viết được thêm | `enum` (8.1), `array_find()` (8.4) |
| Deprecation | Tính năng cũ vẫn chạy nhưng bị đánh dấu "sẽ xoá"; PHP phát thông báo mức `E_DEPRECATED` (hoặc chỉ ghi trong tài liệu) | Vẫn chạy đúng như cũ, chỉ thêm dòng thông báo trong log | Dynamic property (8.2) |
| Thay đổi phá vỡ tương thích (*backward incompatible change*, viết tắt *BC break*) | Hành vi cũ bị đổi hoặc bị xoá | Có thể ném `Error`, báo lỗi biên dịch, hoặc tệ nhất là trả kết quả khác mà không báo gì | `0 == "a"` thành `false` (8.0) |

*Tương thích ngược* (*backward compatibility*) nghĩa là code viết cho bản cũ vẫn chạy đúng trên bản
mới. Một thay đổi "phá vỡ tương thích ngược" là thay đổi làm code cũ chạy sai hoặc không chạy.

Chính sách phát hành của PHP muốn BC break ở bản minor phải "ồn ào": ném exception hoặc báo lỗi, chứ
không lặng lẽ đổi kết quả. Bản major (như 8.0) thì được phép thay đổi lớn hơn, và chính bản 8.0 có vài
thay đổi lặng lẽ đổi kết quả (mục 2.4). Đó là lý do nâng từ 7.4 lên 8.0 khó hơn hẳn các lần nâng minor
sau đó.

### 1.3 Vòng đời của một deprecation

Một tính năng thường không bị xoá đột ngột. Đường đi điển hình:

```
  bản N            bản N+1 ... (các bản minor tiếp theo)        bản major tiếp theo
  ┌──────────┐     ┌──────────────────────────────────┐         ┌──────────────┐
  │ đánh dấu │ ──► │ vẫn chạy, vẫn phát E_DEPRECATED  │  ─────► │ bị xoá hẳn:  │
  │deprecated│     │ (thời gian để bạn sửa code)      │         │ Error / lỗi  │
  └──────────┘     └──────────────────────────────────┘         └──────────────┘

  Ví dụ thật: hàm each()   deprecated ở 7.2   →   bị xoá ở 8.0
              ${var} trong chuỗi  deprecated ở 8.2  →  dự kiến xoá ở 9.0
```

Hầu hết deprecation trong dòng 8.x được ghi trong RFC là "xoá ở PHP 9.0". Bản 8.0, vì là bản major,
đã xoá hàng loạt thứ bị deprecated trong dòng 7.x (mục 2.4). Bài học: thấy `E_DEPRECATED` trong log là thấy một lỗi tương lai đã được báo trước. Sửa
lúc nó còn là deprecation thì rẻ; đợi tới khi nó thành `Error` thì phải sửa gấp.

⚠️ `E_DEPRECATED` mặc định thường không hiện trên production (cấu hình `error_reporting` của
`php.ini-production` loại nó ra). Vì vậy rất nhiều dự án "không biết" mình đang dùng tính năng
deprecated. Mục 9 bàn cách bật nó lên ở môi trường dev, test và CI. Cách cấu hình mức lỗi nằm ở
[Chương 12, mục 8](12-loi-exception.md#8-warning-notice-deprecated-lỗi-không-phải-exception).

### 1.4 Đọc tài liệu gốc của một bản PHP

Có ba nguồn chính, từ "đầy đủ nhất" tới "dễ đọc nhất":

| Nguồn | Ở đâu | Dùng khi |
|---|---|---|
| File `UPGRADING` | Trong mã nguồn php-src, mỗi nhánh một file, ví dụ `https://github.com/php/php-src/blob/PHP-8.4/UPGRADING` | Muốn danh sách đầy đủ, chính xác nhất. Viết cho người bảo trì code PHP; được chia theo mục: "Backward Incompatible Changes", "New Features", "Deprecated Functionality", "Changed Functions", "New Functions"... |
| Migration guide trong manual | `https://www.php.net/manual/en/migration84.php` (đổi số cho bản khác) | Bản dễ đọc của `UPGRADING`, chia thành các trang: tính năng mới, BC break, deprecated... |
| RFC | `https://wiki.php.net/rfc/...` | Muốn biết vì sao một tính năng được thêm, các trường hợp biên, và kết quả bỏ phiếu. Mỗi thay đổi lớn đều có một RFC |

Ngoài ra trang giới thiệu `https://www.php.net/releases/8.4/en.php` (đổi số) tóm tắt các điểm nổi bật
bằng ví dụ "trước/sau", hợp để đọc lướt.

⚠️ Nói về phiên bản theo trí nhớ rất dễ sai một số (8.1 hay 8.2? deprecated hay đã xoá?). Quy tắc khi
làm việc thật: mọi câu "tính năng X có từ bản Y" phải được kiểm bằng `UPGRADING` hoặc manual (mục
"Changelog" ở cuối mỗi trang hàm ghi rõ bản nào đổi gì), hoặc chạy thử trên đúng bản đó.

### 1.5 Tóm tắt dòng 8.x trong một hình

```
 2020-11     2021-11     2022-12     2023-11     2024-11     2025-11
 ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐     ┌─────┐
 │ 8.0 │ ──► │ 8.1 │ ──► │ 8.2 │ ──► │ 8.3 │ ──► │ 8.4 │ ──► │ 8.5 │
 └─────┘     └─────┘     └─────┘     └─────┘     └─────┘     └─────┘
  major       enum        readonly    typed       property    pipe |>
  JIT         readonly    class       class       hooks       clone with
  union type  property    DNF type    const       asymmetric  URI ext
  named args  never       dynamic     #[Override] visibility  #[NoDiscard]
  match       fibers      property    json_       lazy object array_first
  nullsafe ?-> first-class deprecated validate()  array_find  array_last
  attributes  callable                            new MyClass()->m()
  ctor promotion
```

Ngày ra bản x.y.0: 8.0 ngày 26/11/2020, 8.1 ngày 25/11/2021, 8.2 ngày 08/12/2022, 8.3 ngày 23/11/2023,
8.4 ngày 21/11/2024, 8.5 ngày 20/11/2025. Tình trạng hỗ trợ của từng nhánh tại 10/2026 đã có trong
[Chương 01, mục 2.3](01-php-la-gi.md#23-vòng-đời-4-năm-2-năm-active-2-năm-security): 8.0 và 8.1 đã EOL,
8.2 và 8.3 chỉ còn vá bảo mật, 8.4 và 8.5 còn active.

## 2. PHP 8.0 (26/11/2020): bản major

PHP 8.0 là bản major đầu tiên sau PHP 7.0 (2015). Nó vừa thêm rất nhiều cú pháp mới, vừa dọn dẹp những
hành vi "kỳ quặc" tích tụ từ thời PHP 5. Phần lớn code hiện đại bạn đọc hôm nay (Laravel, Symfony)
dùng tính năng của bản này ở gần như mọi file.

### 2.1 Tính năng chính

| Tính năng | Trông như thế nào | Học ở đâu |
|---|---|---|
| Union type | `int\|float $total` | [Chương 04, mục 11.5](04-kieu-du-lieu.md) |
| Kiểu `mixed`, kiểu trả về `static` | `function get(): mixed`, `function create(): static` | [Chương 08, mục 3.2 và 3.5](08-ham.md) |
| Named arguments | `new Order(id: 7, total: 99.5)` | [Chương 08, mục 6](08-ham.md) |
| Biểu thức `match` | `match ($x) { 1, 2 => 'a', default => 'b' }` | [Chương 07, mục 15](07-toan-tu-dieu-khien.md) |
| Toán tử nullsafe | `$order->customer?->email` | [Chương 07, mục 9.1](07-toan-tu-dieu-khien.md) |
| Constructor property promotion | `public function __construct(public int $id) {}` | [Chương 09, mục 4.2](09-oop-co-ban.md) |
| Attributes | `#[Route('/orders')]` | [Chương 10, mục 9](10-oop-nang-cao.md) |
| `throw` là biểu thức | `$x ?? throw new LogicException()` | [Chương 12, mục 5](12-loi-exception.md) |
| `catch` không cần biến | `catch (LogicException) { ... }` | [Chương 12, mục 2.6](12-loi-exception.md) |
| Interface `Stringable` (tự gắn cho class có `__toString`) | `function log(Stringable\|string $m)` | [Chương 10, mục 1.4](10-oop-nang-cao.md) |
| `WeakMap` | Cache gắn với object, không giữ object sống | [Chương 10, mục 12](10-oop-nang-cao.md) |
| `$object::class` | Giống `get_class($object)` | [Chương 09, mục 1.5](09-oop-co-ban.md) |
| Dấu phẩy cuối trong danh sách tham số | `function f(int $a, int $b,) {}` | [Chương 08](08-ham.md) |
| Class `ValueError` | Hàm có sẵn ném khi giá trị đúng kiểu nhưng sai miền | [Chương 12, mục 4.2](12-loi-exception.md) |
| Hàm mới: `str_contains`, `str_starts_with`, `str_ends_with` | `str_contains($s, 'abc')` | [Chương 05, mục 4.2](05-chuoi.md) |
| Hàm mới: `fdiv`, `get_debug_type`, `get_resource_id`, `preg_last_error_msg` | `fdiv(1, 0)` cho `INF` | [Chương 07, mục 2.2](07-toan-tu-dieu-khien.md), [Chương 04, mục 1.4](04-kieu-du-lieu.md) |
| Sắp xếp ổn định (*stable sort*) | Phần tử bằng nhau giữ thứ tự ban đầu | [Chương 06, mục 8.4](06-mang.md) |
| JIT compiler trong OPcache | Cấu hình `opcache.jit*` | [Chương 02, mục 3.5](02-php-chay-nhu-the-nao.md) |

Một file gom nhiều tính năng của 8.0 (chạy được từ PHP 8.0 trở lên):

```php
<?php
declare(strict_types=1);

#[Attribute]
final class Route
{
    public function __construct(public string $path) {}
}

final class Order
{
    // constructor property promotion (8.0)
    public function __construct(
        public int $id,
        public int|float $total,      // union type (8.0)
        public ?Customer $customer = null,
    ) {}

    #[Route('/orders')]               // attribute (8.0)
    public function show(): static    // kiểu trả về static (8.0)
    {
        return $this;
    }
}

final class Customer
{
    public function __construct(public ?string $email = null) {}
}

$order = new Order(id: 7, total: 99.5);           // named arguments (8.0)

echo $order->customer?->email ?? 'không có email', "\n"; // in ra: không có email

$label = match (true) {                            // match (8.0)
    $order->total >= 100 => 'lớn',
    $order->total >= 50  => 'vừa',
    default              => 'nhỏ',
};
echo $label, "\n";                                 // in ra: vừa

echo $order::class, "\n";                          // in ra: Order
var_dump(str_contains('hello world', 'world'));    // in ra: bool(true)
echo get_debug_type($order->total), "\n";          // in ra: float

$attr = (new ReflectionMethod(Order::class, 'show'))->getAttributes()[0];
echo $attr->newInstance()->path, "\n";             // in ra: /orders

try {
    $x = $order->customer ?? throw new LogicException('thiếu khách'); // throw là biểu thức
} catch (LogicException) {                         // catch không cần biến
    echo "đã bắt LogicException\n";                // in ra: đã bắt LogicException
}
```

Về JIT: *JIT* (just-in-time compiler) dịch opcode thành mã máy lúc chạy. Nó giúp nhiều cho code nặng
tính toán (xử lý ảnh, thuật toán số), còn ứng dụng web điển hình (phần lớn thời gian chờ database,
mạng) thường không nhanh lên đáng kể. Đừng bật JIT với kỳ vọng Laravel nhanh gấp đôi; hãy đo
([Chương 20](20-hieu-nang.md)).

### 2.2 Thay đổi lặng lẽ đổi kết quả: nguy hiểm nhất

Đây là nhóm thay đổi đáng sợ nhất khi nâng từ 7.4 lên 8.0: code vẫn chạy, không báo lỗi gì, nhưng
cho kết quả khác. Test là cách duy nhất bắt được chúng.

```php
<?php
declare(strict_types=1);

// 1. So sánh lỏng giữa số và chuỗi không phải số
var_dump(0 == 'foo');                       // in ra: bool(false)  (PHP 7.4: bool(true))
var_dump(0 == '');                          // in ra: bool(false)  (PHP 7.4: bool(true))
var_dump(42 == '42foo');                    // in ra: bool(false)  (PHP 7.4: bool(true))
var_dump(in_array(0, ['foo', 'bar']));      // in ra: bool(false)  (PHP 7.4: bool(true))

// 2. Thứ tự ưu tiên của toán tử nối chuỗi so với + và -
$a = 1;
$b = 2;
echo 'Tổng: ' . $a + $b, "\n";              // in ra: Tổng: 3
                                            // (PHP 7.4: Warning "A non-numeric value", in ra 2)

// 3. switch cũng so sánh lỏng nên cũng đổi nhánh
switch (0) {
    case 'abc':
        echo "nhánh abc\n";
        break;
    default:
        echo "nhánh default\n";             // in ra: nhánh default  (PHP 7.4: nhánh abc)
}
```

Output ở comment đã chạy thật trên PHP 8.0 và PHP 7.4.

Giải thích:

1. RFC [Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison):
   khi so sánh lỏng một số với một chuỗi, nếu chuỗi là *numeric string* (chuỗi số như `"42"`,
   `" 42"`, `"1e3"`) thì vẫn so như số; nếu không, PHP 8 đổi số thành chuỗi rồi so hai chuỗi. Áp dụng
   cho mọi chỗ so lỏng: `==`, `!=`, `<`, `>`, `<=>`, `switch`, `in_array()`/`array_search()` không
   strict, `sort()` với cờ mặc định. Chi tiết ở [Chương 04, mục 13.3](04-kieu-du-lieu.md).
2. RFC [Change the precedence of the concatenation operator](https://wiki.php.net/rfc/concatenation_precedence):
   từ 8.0, `+` và `-` được tính trước `.`. Ở 7.4, `'Tổng: ' . $a + $b` bị hiểu là
   `('Tổng: ' . $a) + $b`, tức `'Tổng: 1' + 2`. Xem [Chương 07, mục 7.2](07-toan-tu-dieu-khien.md).
3. Thêm vài thay đổi lặng lẽ khác cần biết (theo `UPGRADING` 8.0):
   - Sắp xếp giờ ổn định, nên thứ tự các phần tử "bằng nhau" sau khi sort có thể khác trước.
   - Callback so sánh trả `bool` (`fn($a, $b) => $a > $b`) cho `usort` giờ phát deprecation; hãy dùng
     `<=>`.
   - Ép float sang string không còn phụ thuộc locale (trước đây với `setlocale(LC_ALL, 'de_DE')`,
     `(string) 3.14` có thể ra `"3,14"`).
   - `var_dump()` in float theo `serialize_precision`, nên in đầy đủ chữ số hơn (ví dụ
     `float(0.30000000000000004)` thay vì `float(0.3)`).
   - Chuỗi số có khoảng trắng ở cuối (`"42 "`) giờ được coi là numeric string, giống khoảng trắng ở đầu
     (RFC [Saner numeric strings](https://wiki.php.net/rfc/saner-numeric-strings)).

### 2.3 Warning và notice thành Error: lỗi "ồn ào" hơn

Nhóm này không âm thầm. Code cũ sẽ ném lỗi ngay, nên dễ phát hiện hơn, nhưng có thể làm sập một trang
từng chạy "được" (với vài dòng warning trong log).

Hàm có sẵn ném `TypeError` và `ValueError` (RFC
[Consistent type errors for internal functions](https://wiki.php.net/rfc/consistent_type_errors)).
Trước 8.0, truyền sai kiểu vào hàm có sẵn (trong chế độ không strict) chỉ phát warning và trả `null`:

```php
<?php
// File này cố ý KHÔNG bật strict_types để thấy khác biệt giữa hai bản.
try {
    var_dump(strlen([]));
} catch (TypeError $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
}
try {
    var_dump(array_chunk([1, 2], 0));
} catch (ValueError $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
}

// PHP 8.5 in ra:
// TypeError: strlen(): Argument #1 ($string) must be of type string, array given
// ValueError: array_chunk(): Argument #2 ($length) must be greater than 0
//
// PHP 7.4 in ra:
// Warning: strlen() expects parameter 1 to be string, array given in ... on line 4
// NULL
// Warning: array_chunk(): Size parameter expected to be greater than 0 in ... on line 9
// NULL
```

(Tên tham số trong thông báo có thể khác giữa các bản 8.x; ví dụ PHP 8.0 ghi `$str`, 8.5 ghi
`$string`.)

RFC [Reclassifying engine warnings](https://wiki.php.net/rfc/engine_warnings) nâng mức của nhiều thông
báo:

| Hành động | PHP 7.4 | PHP 8.0 |
|---|---|---|
| Đọc biến chưa định nghĩa | Notice | Warning |
| Đọc key mảng không tồn tại | Notice | Warning |
| Đọc property chưa định nghĩa | Notice | Warning |
| Ép mảng thành chuỗi (`"$arr"`) | Notice | Warning |
| Ghi property lên `null`, `false`, chuỗi rỗng (trước đây tự tạo `stdClass`) | Warning | `Error` |
| Ghi phần tử mảng lên một giá trị scalar | Warning | `Error` |
| Dùng mảng hoặc object làm key mảng | Warning | `TypeError` |
| Unpack (`...`) một giá trị không phải array/Traversable | Warning | `Error` |

Thêm vài thay đổi cùng tinh thần:

- Toán tử số học và bitwise (`+ - * / ** % << >> & | ^ ~ ++ --`) ném `TypeError` khi một toán hạng là
  array, resource hoặc object (trừ `array + array` vẫn là gộp mảng).
- Phép toán số học với chuỗi không phải số (`'abc' * 2`) ném `TypeError`; chuỗi "bắt đầu bằng số"
  như `'5 apples'` vẫn chạy nhưng phát warning "A non-numeric value encountered".
- Truy cập hằng chưa định nghĩa ném `Error` (trước đây chỉ warning và coi tên hằng là chuỗi).
- `assert()` mặc định ném `AssertionError` khi điều kiện sai.
- Override method sai chữ ký (vi phạm LSP) luôn là fatal error.
- Magic method có khai báo kiểu thì kiểu phải khớp chữ ký chuẩn (ví dụ `__get(string $name): mixed`).
- `@` không còn tắt được fatal error. Error handler cũ kiểm tra `error_reporting() == 0` để biết lỗi bị
  `@` che phải đổi sang `!(error_reporting() & $errno)`. Xem
  [Chương 07, mục 10.2](07-toan-tu-dieu-khien.md).
- `error_reporting` mặc định (khi không có `php.ini`) là `E_ALL`; trước đây loại `E_NOTICE` và
  `E_DEPRECATED`. `display_startup_errors` bật mặc định.
- PDO mặc định ở chế độ ném exception (`PDO::ERRMODE_EXCEPTION`), trước đây im lặng. Xem
  [Chương 16, mục 2.4](16-php-va-database.md).

### 2.4 Cú pháp và hàm đã bị xoá

PHP 8.0 xoá hẳn những thứ đã deprecated trong dòng 7.x. Gặp chúng trên 8.0 là lỗi ngay:

| Đã bị xoá | Dùng thay bằng |
|---|---|
| Constructor kiểu PHP 4 (method trùng tên class) | `__construct()` |
| Gọi method không static theo kiểu static (`Foo::bar()` khi `bar` không static) | Tạo object rồi gọi |
| `each()` | `foreach` |
| `create_function()` | Closure `function () {}` hoặc `fn` |
| Hàm `__autoload()` | `spl_autoload_register()` ([Chương 11, mục 6](11-namespace-composer.md)) |
| Ép kiểu `(real)` và `(unset)` | `(float)`, gán `null` |
| `define('X', 1, true)`: hằng không phân biệt hoa thường | Hằng thường |
| Truy cập offset bằng ngoặc nhọn `$str{0}` | `$str[0]` |
| Ternary lồng không có ngoặc `$a ? $b : $c ? $d : $e` | Thêm ngoặc ([Chương 07, mục 8.3](07-toan-tu-dieu-khien.md)) |
| `track_errors` và biến `$php_errormsg` | `error_get_last()` |
| Tham số `$errcontext` của error handler | Bỏ tham số đó |
| `money_format()`, `hebrevc()`, `convert_cyr_string()`, `ezmlm_hash()`, `restore_include_path()`, `get_magic_quotes_gpc()`, `get_magic_quotes_runtime()`, `fgetss()` | Tuỳ hàm (ví dụ `NumberFormatter` thay `money_format`) |
| `implode($pieces, $glue)` (đảo thứ tự tham số) | `implode($glue, $pieces)` |
| `parse_str($str)` không có tham số kết quả | `parse_str($str, $result)` |
| `array_key_exists()` với object | `isset()` hoặc `property_exists()` |
| `mbstring.func_overload` | Gọi thẳng hàm `mb_*` |
| Extension `xmlrpc` (chuyển sang PECL) | Thư viện khác |

### 2.5 Resource thành object

Nhiều extension đổi giá trị trả về từ *resource* sang object của một class "đục" (*opaque*, không có
method): `curl_init()` trả `CurlHandle`, các hàm GD trả `GdImage`, OpenSSL trả `OpenSSLCertificate`...
Code kiểm tra `is_resource($ch)` sẽ thành `false` dù tạo thành công. Cách sửa: kiểm tra `=== false`.
Các hàm `curl_close()`, `imagedestroy()` không còn tác dụng; object tự giải phóng khi không còn ai
tham chiếu. Xem [Chương 04, mục 9](04-kieu-du-lieu.md).

### 2.6 Deprecation của 8.0

| Deprecated | Vì sao | Thay bằng |
|---|---|---|
| Tham số bắt buộc đứng sau tham số tuỳ chọn: `function f($a = [], $b)` | Giá trị mặc định của `$a` không bao giờ dùng được | Bỏ giá trị mặc định hoặc đổi thứ tự ([Chương 08, mục 5.5](08-ham.md)) |
| `ReflectionParameter::getClass()`, `isArray()`, `isCallable()` | Không mô tả được union type | `ReflectionParameter::getType()` |
| `libxml_disable_entity_loader()` | Từ libxml 2.9.0 (bản tối thiểu PHP 8.0 yêu cầu), external entity đã tắt mặc định | Bỏ lời gọi |
| API thủ tục của extension zip (`zip_open()`...) | Có API hướng đối tượng | `ZipArchive` |

Ngoại lệ của dòng đầu: tham số dạng `Type $param = null` hoặc `?Type $param = null` đứng trước tham số
bắt buộc vẫn được phép ở 8.0, vì code cũ dùng nó để giả lập nullable. Lối thoát này bị thu hẹp dần:
8.1 deprecated dạng `?Type $param = null` đứng trước tham số bắt buộc, còn 8.4 deprecated mọi kiểu
"nullable ngầm" `Type $param = null` (mục 6.3). Đã chạy thử trên 8.0, 8.1, 8.3, 8.4:

```php
<?php
error_reporting(E_ALL);
function f1(int $a = null, $b) {}   // 8.0-8.3: im lặng; 8.4: Deprecated "Implicitly marking parameter $a as nullable..."
function f2(?int $a = null, $b) {}  // 8.0: im lặng; từ 8.1: Deprecated "Optional parameter $a declared before required parameter $b..."
function f3($a = [], $b) {}         // từ 8.0: Deprecated (8.0: "Required parameter $b follows optional parameter $a")
```

Nguồn: [UPGRADING 8.0](https://github.com/php/php-src/blob/PHP-8.0/UPGRADING),
[Migration 7.4 → 8.0](https://www.php.net/manual/en/migration80.php).

## 3. PHP 8.1 (25/11/2021)

PHP 8.1 là bản minor "giàu tính năng" nhất của dòng 8: enum, readonly, fiber. Về tương thích, điểm
đáng chú ý nhất là hàng loạt deprecation mới (truyền `null` vào hàm có sẵn), thứ làm log của nhiều dự
án cũ đầy ắp dòng `Deprecated` sau khi nâng cấp.

### 3.1 Tính năng chính

| Tính năng | Trông như thế nào | Học ở đâu |
|---|---|---|
| Enum (pure và backed) | `enum Status: string { case Paid = 'paid'; }` | [Chương 10, mục 3](10-oop-nang-cao.md) |
| Readonly property | `public readonly int $id` | [Chương 10, mục 4.2](10-oop-nang-cao.md) |
| Kiểu trả về `never` | `function fail(): never { throw ...; }` | [Chương 08, mục 3.4](08-ham.md) |
| Pure intersection type | `Countable&Iterator $x` (chưa kết hợp được với union) | [Chương 04, mục 11.6](04-kieu-du-lieu.md) |
| First-class callable syntax | `$f = strtoupper(...);` | [Chương 08, mục 12.3](08-ham.md) |
| `new` trong giá trị khởi tạo | `private Clock $clock = new Clock()` trong tham số; cũng dùng được cho biến static, hằng toàn cục, đối số attribute | [Chương 09, mục 4.3](09-oop-co-ban.md) |
| Fiber | `new Fiber(fn () => Fiber::suspend(1))` | [Chương 13, mục 10](13-generator-iterator-spl.md) |
| Hằng class `final` | `final public const VERSION = 2;` | [Chương 09, mục 7.2](09-oop-co-ban.md) |
| Unpack mảng có key chuỗi | `[...$a, ...$b]` với key chuỗi | [Chương 06, mục 6.3](06-mang.md) |
| Tiền tố `0o` cho số hệ 8 | `0o17` bằng `15` | [Chương 04, mục 3.1](04-kieu-du-lieu.md) |
| Named argument sau unpack | `foo(...$args, named: 1)` | [Chương 08, mục 7](08-ham.md) |
| Hàm mới `array_is_list()` | `array_is_list([1, 2])` cho `true` | [Chương 06, mục 3.1](06-mang.md) |
| Hàm mới `fsync()`, `fdatasync()` | Ép hệ điều hành ghi bộ đệm xuống đĩa | [Chương 14](14-file-json-thoi-gian.md) |
| `$_FILES` có thêm key `full_path` | Đường dẫn đầy đủ khi upload cả thư mục | [Chương 15](15-php-va-web.md) |

```php
<?php
declare(strict_types=1);

enum Status: string                               // enum (8.1)
{
    case Paid = 'paid';
    case Pending = 'pending';

    public function label(): string
    {
        return match ($this) {
            Status::Paid    => 'Đã thanh toán',
            Status::Pending => 'Chờ thanh toán',
        };
    }
}

final class Clock
{
    public function now(): string
    {
        return '2026-10-03';
    }
}

final class Invoice
{
    public function __construct(
        public readonly int $id,                  // readonly property (8.1)
        public readonly Status $status,
        private Clock $clock = new Clock(),       // new trong giá trị mặc định (8.1)
    ) {}

    public function issuedAt(): string
    {
        return $this->clock->now();
    }
}

function fail(string $msg): never                 // kiểu trả về never (8.1)
{
    throw new RuntimeException($msg);
}

$inv = new Invoice(1, Status::from('paid'));
echo $inv->status->label(), "\n";                 // in ra: Đã thanh toán
echo $inv->issuedAt(), "\n";                      // in ra: 2026-10-03

try {
    $inv->id = 2;
} catch (Error $e) {
    echo $e->getMessage(), "\n";                  // in ra: Cannot modify readonly property Invoice::$id
}

$upper = strtoupper(...);                         // first-class callable (8.1)
echo $upper('php'), "\n";                         // in ra: PHP

var_dump(array_is_list([10, 20]));                // in ra: bool(true)
var_dump(array_is_list([1 => 10]));               // in ra: bool(false)
echo 0o17, "\n";                                  // in ra: 15
var_dump([...['a' => 1], ...['b' => 2]]);         // in ra: array(2) { ["a"]=> int(1) ["b"]=> int(2) }
```

(Dòng cuối, `var_dump` in mảng trên nhiều dòng; ở đây viết gọn trên một dòng.)

### 3.2 Thay đổi phá vỡ tương thích

| Thay đổi | Ảnh hưởng thực tế | Cách xử lý |
|---|---|---|
| `htmlspecialchars()`, `htmlentities()` và các hàm decode tương ứng mặc định dùng `ENT_QUOTES \| ENT_SUBSTITUTE` thay vì `ENT_COMPAT` | Dấu nháy đơn `'` giờ thành `&#039;`; UTF-8 hỏng được thay bằng ký tự thay thế thay vì trả chuỗi rỗng. An toàn hơn, nhưng snapshot test so HTML có thể lệch | Cập nhật test. Xem [Chương 17, mục 3.2](17-bao-mat.md) |
| PDO MySQL (với emulated prepare) và PDO SQLite trả số nguyên, số thực đúng kiểu `int`/`float` thay vì chuỗi | Code so sánh `=== '1'` với giá trị từ database thành `false` | So với `int`, hoặc bật `PDO::ATTR_STRINGIFY_FETCHES` để có lại hành vi cũ. Xem [Chương 16, mục 5.1](16-php-va-database.md) |
| MySQLi mặc định ném exception (`MYSQLI_REPORT_ERROR \| MYSQLI_REPORT_STRICT`) | Code kiểm tra `if (!$result)` sau query lỗi không còn chạy tới | Bắt `mysqli_sql_exception`, hoặc `mysqli_report(MYSQLI_REPORT_OFF)` nếu buộc phải giữ cách cũ |
| Method của class có sẵn (ví dụ `Iterator::current()`, `ArrayAccess::offsetGet()`, `JsonSerializable::jsonSerialize()`) có kiểu trả về "dự kiến"; class con ghi đè mà không khai báo kiểu tương thích sẽ phát deprecation | Rất nhiều thư viện cũ phát `Deprecated: Return type of X::current() should either be compatible with...` | Thêm kiểu trả về; thư viện cần chạy cả trên PHP cũ thì gắn `#[\ReturnTypeWillChange]`. Xem [Chương 13, mục 2.4](13-generator-iterator-spl.md) |
| Ghi vào toàn bộ `$GLOBALS` (ví dụ `array_pop($GLOBALS)`, `$GLOBALS = []`) bị cấm; đọc ghi từng phần tử `$GLOBALS['x']` vẫn được | Hiếm gặp | Ghi từng phần tử. Xem [Chương 03, mục 4.3](03-cu-phap-bien-hang.md) |
| Method có biến `static` được kế thừa (không override) giờ dùng chung biến `static` với method của class cha | Bộ đếm, cache trong biến `static` của class cha và class con không còn tách riêng | Xem lại code dùng `static $x` trong method của class có class con |
| Thêm nhiều resource thành object: `finfo`, `FTP\Connection`, `IMAP\Connection`, `LDAP\Connection`, `PgSql\Connection`... | `is_resource()` thành `false` | Kiểm tra `=== false` |

### 3.3 Deprecation của 8.1

Đây là bản có deprecation ảnh hưởng nhiều code cũ nhất. Chạy thử trên 8.0 và 8.1:

```php
<?php
// File KHÔNG bật strict_types: đây là kiểu code cũ hay gặp
error_reporting(E_ALL);

$name = null;
echo strlen($name), "\n";        // truyền null vào tham số string của hàm có sẵn

$arr = [];
$arr[1.5] = 'a';                 // float có phần lẻ làm key mảng

$x = false;
$x[] = 'b';                      // biến false tự thành mảng

echo htmlspecialchars("It's"), "\n";
```

```
PHP 8.0:
0
It's

PHP 8.1:
Deprecated: strlen(): Passing null to parameter #1 ($string) of type string is deprecated in ... on line 6
0
Deprecated: Implicit conversion from float 1.5 to int loses precision in ... on line 9
Deprecated: Automatic conversion of false to array is deprecated in ... on line 12
It&#039;s
```

Danh sách deprecation quan trọng của 8.1:

| Deprecated | Thay bằng |
|---|---|
| Truyền `null` vào tham số không nullable của hàm có sẵn (`strlen(null)`, `str_replace('a', 'b', null)`, `trim(null)`...) | Ép kiểu hoặc dùng `?? ''` trước khi gọi. Hàm tự viết vốn đã không nhận `null` (ném `TypeError`), 8.1 làm hàm có sẵn nhất quán theo |
| Đổi float sang int ngầm mà mất phần lẻ (key mảng `1.5`, truyền `1.5` vào tham số `int` ở chế độ không strict, toán tử `%`, `<<`...) | `(int)`, `intdiv()`, `round()` tường minh |
| Biến `false` tự thành mảng khi ghi `$x[] = ...` (*autovivification* trên `false`) | Khởi tạo `$x = []`. Lưu ý `null` và biến chưa định nghĩa vẫn tự thành mảng, không bị deprecated |
| Implement `Serializable` mà không có `__serialize()`/`__unserialize()` | Viết `__serialize()`/`__unserialize()` ([Chương 10, mục 11](10-oop-nang-cao.md)) |
| Gọi static method hoặc truy cập static property trực tiếp trên trait (`MyTrait::foo()`) | Gọi qua class dùng trait |
| `return` theo tham chiếu từ hàm `void` | Bỏ `&` |
| Truyền giá trị không phải chuỗi vào `ctype_*()` | `ctype_digit(chr($cp))` hoặc truyền chuỗi |
| `strftime()`, `gmstrftime()`, `strptime()` | `date()`/`DateTimeInterface::format()`, hoặc `IntlDateFormatter` khi cần định dạng theo ngôn ngữ; thay `strptime()` bằng `date_parse_from_format()` |
| `date_sunrise()`, `date_sunset()` | `date_sun_info()` |
| Filter `FILTER_SANITIZE_STRING`, `FILTER_SANITIZE_STRIPPED` | `htmlspecialchars()` khi xuất ra; validate rõ ràng khi nhận vào |
| `key()`, `current()`, `next()`, `prev()`, `reset()`, `end()` trên object | Ép `(array)` hoặc dùng `ArrayIterator` |
| `mhash*()` | `hash*()` |
| `PDO::FETCH_SERIALIZE`, `mysqli::init()`, `odbc_result_all()`, ini `auto_detect_line_endings`, `filter.default` | Xem `UPGRADING` 8.1 |
| Tham số `?Type $x = null` đứng trước tham số bắt buộc (mục 2.6) | Đổi thứ tự tham số |

⚠️ Deprecation "Passing null to parameter" là nguồn log nhiều nhất khi nâng lên 8.1. Nó thường đến từ
dữ liệu: cột database `NULL`, `$_GET['q']` không có, giá trị config trống. Sửa bằng cách xử lý
`null` ở biên (nơi dữ liệu đi vào), không phải rải `(string)` khắp nơi. Khai báo kiểu đầy đủ và bật
`strict_types` giúp PHPStan tìm ra những chỗ này trước khi chạy (mục 9).

Nguồn: [UPGRADING 8.1](https://github.com/php/php-src/blob/PHP-8.1/UPGRADING),
[RFC Deprecations for PHP 8.1](https://wiki.php.net/rfc/deprecations_php_8_1),
[RFC Deprecate passing null to non-nullable arguments of internal functions](https://wiki.php.net/rfc/deprecate_null_to_scalar_internal_arg).

## 4. PHP 8.2 (08/12/2022)

PHP 8.2 tiếp tục hoàn thiện hệ thống kiểu (DNF type, `true`/`false`/`null` đứng riêng) và
immutability (`readonly class`). Deprecation nổi tiếng nhất của bản này là dynamic property.

### 4.1 Tính năng chính

| Tính năng | Trông như thế nào | Học ở đâu |
|---|---|---|
| `readonly class`: mọi property đều readonly | `readonly class Point { ... }` | [Chương 10, mục 4.4](10-oop-nang-cao.md) |
| DNF type (*Disjoint Normal Form*): kết hợp intersection và union | `(HasId&HasName)\|null` | [Chương 04, mục 11.6](04-kieu-du-lieu.md) |
| `null`, `false` đứng riêng làm kiểu; thêm kiểu `true` | `function f(): true` | [Chương 04, mục 11.3](04-kieu-du-lieu.md) |
| Hằng trong trait | `trait T { public const X = 1; }` (chỉ truy cập qua class dùng trait) | [Chương 09, mục 11.5](09-oop-co-ban.md) |
| Đọc property của enum (`->value`, `->name`) trong biểu thức hằng | `const D = self::Small->value;` | [Chương 10, mục 3.5](10-oop-nang-cao.md) |
| Attribute `#[\SensitiveParameter]`: giấu giá trị tham số trong stack trace | `function login(#[\SensitiveParameter] string $pw)` | [Chương 12, mục 2.8](12-loi-exception.md) |
| Extension Random: `Random\Randomizer` và các engine | `new Random\Randomizer()` | [Chương 17, mục 6.2](17-bao-mat.md) |
| Hàm mới `memory_reset_peak_usage()`, `ini_parse_quantity()`, `mysqli_execute_query()` | | [Chương 20, mục 3.4](20-hieu-nang.md) |
| `iterator_to_array()`, `iterator_count()` nhận cả array (`iterable`) | `iterator_to_array([1, 2])` | [Chương 13, mục 3.4](13-generator-iterator-spl.md) |
| Modifier `n` của PCRE: nhóm `(...)` không đặt tên thì không bắt | `preg_match('/(a)(?<b>b)/n', ...)` | [Chương 05, mục 7](05-chuoi.md) |

```php
<?php
declare(strict_types=1);

readonly class Point                              // readonly class (8.2)
{
    public function __construct(public int $x, public int $y) {}
}

trait HasVersion
{
    public const VERSION = '1.0';                 // hằng trong trait (8.2)
}

final class Api
{
    use HasVersion;
}

enum Size: string
{
    case Small = 's';
    const DEFAULT = self::Small->value;           // ->value của enum trong biểu thức hằng (8.2)
}

interface HasId {}
interface HasName {}

// DNF type (8.2): (A&B)|null
function show((HasId&HasName)|null $x): string
{
    return $x === null ? 'null' : 'object';
}

function alwaysTrue(): true                       // kiểu true đứng riêng (8.2)
{
    return true;
}

function login(string $user, #[\SensitiveParameter] string $password): void // (8.2)
{
    throw new RuntimeException('sai mật khẩu');
}

$p = new Point(1, 2);
echo $p->x + $p->y, "\n";                                  // in ra: 3
echo Api::VERSION, ' ', Size::DEFAULT, ' ', show(null), "\n"; // in ra: 1.0 s null
var_dump(alwaysTrue());                                    // in ra: bool(true)

try {
    login('an', 'hunter2');
} catch (RuntimeException $e) {
    echo $e->getTraceAsString(), "\n";
    // in ra: #0 /đường/dẫn/v82.php(50): login('an', Object(SensitiveParameterValue))
    //        #1 {main}
}

$r = new Random\Randomizer(new Random\Engine\Mt19937(42)); // extension Random (8.2)
echo $r->getInt(1, 100), "\n";                             // in ra: 43 (cùng seed thì cùng kết quả)
```

Để ý dòng trace: mật khẩu `hunter2` không xuất hiện, thay bằng `Object(SensitiveParameterValue)`. Đây
là lý do nên gắn attribute này cho mọi tham số mật khẩu, token, khoá bí mật: stack trace hay được ghi
vào log hoặc gửi sang dịch vụ theo dõi lỗi.

### 4.2 Thay đổi phá vỡ tương thích

| Thay đổi | Ảnh hưởng | Cách xử lý |
|---|---|---|
| `strtolower()`, `strtoupper()`, `stripos()`, `ucfirst()`, `ucwords()`, `str_ireplace()`... không còn phụ thuộc locale; chỉ đổi hoa thường các chữ ASCII | Code từng dựa vào `setlocale()` để `strtolower()` đổi được chữ có dấu trong bảng mã 1 byte (Latin-1...) sẽ không đổi nữa | Dùng `mb_strtolower()` cho văn bản Unicode ([Chương 05, mục 4.6](05-chuoi.md)) |
| `str_split('')` trả `[]` thay vì `['']` | Code đếm `count(str_split($s))` với chuỗi rỗng ra 0 thay vì 1 | Kiểm tra lại các chỗ xử lý chuỗi rỗng |
| `ksort()`, `krsort()` với `SORT_REGULAR` so key dạng chuỗi số theo luật so sánh của PHP 8 | Thứ tự key trộn số và chữ có thể khác | Hiếm gặp; thêm test nếu dựa vào thứ tự đó |
| mysqli không còn build được với libmysql (chỉ mysqlnd) | Chỉ ảnh hưởng người tự build PHP | |

### 4.3 Deprecation của 8.2

```php
<?php
declare(strict_types=1);
error_reporting(E_ALL);

class User
{
    public string $name = 'An';
}

$u = new User();
$u->age = 30;                       // dynamic property

$name = 'An';
echo "Xin chào ${name}\n";          // cú pháp ${} trong chuỗi

echo utf8_decode('é') === "\xE9" ? "latin1\n" : "khác\n";
```

```
PHP 8.1:
Xin chào An
latin1

PHP 8.2:
Deprecated: Using ${var} in strings is deprecated, use {$var} instead in ... on line 14
Deprecated: Creation of dynamic property User::$age is deprecated in ... on line 11
Xin chào An
Deprecated: Function utf8_decode() is deprecated in ... on line 16
latin1
```

Để ý thứ tự: thông báo về `${}` hiện ra trước thông báo của dòng 11. Lý do: `${}` bị phát hiện lúc
biên dịch file, trước khi dòng nào chạy; còn dynamic property chỉ bị phát hiện lúc chạy tới dòng 11.

| Deprecated | Thay bằng |
|---|---|
| Tạo *dynamic property* (property chưa khai báo) trên object của class thường | Khai báo property (cách tốt nhất); gắn `#[\AllowDynamicProperties]` cho class nếu buộc phải giữ; dùng `WeakMap` nếu muốn gắn dữ liệu vào object của class không phải của bạn. `stdClass` và class có `__get`/`__set` không bị ảnh hưởng. Xem [Chương 09, mục 2.5](09-oop-co-ban.md) |
| Chèn biến bằng `"${var}"` và `"${expr}"` | `"$var"`, `"{$var}"`; dạng biến động `"${expr}"` viết thành `"{${expr}}"`. Xem [Chương 05, mục 2.4](05-chuoi.md) |
| `utf8_encode()`, `utf8_decode()` (tên gây hiểu lầm: chỉ chuyển giữa ISO-8859-1 và UTF-8) | `mb_convert_encoding()`. Xem [Chương 05, mục 5.4](05-chuoi.md) |
| Callable dạng chuỗi/mảng dùng `self`, `parent`, `static` (`"self::method"`, `["static", "method"]`, `"parent::method"`...) và `["Foo", "Bar::method"]` | `self::method(...)` (first-class callable), `[self::class, 'method']`, `static::class`. Callable `"A::method"` và `["A", "method"]` vẫn bình thường. Xem [Chương 08, mục 12](08-ham.md) |
| Các "encoding" `QPrint`, `Base64`, `Uuencode`, `HTML-ENTITIES` trong hàm `mb_*` | `base64_encode()`, `quoted_printable_encode()`, `htmlentities()`... |

⚠️ Dynamic property là deprecation hay gặp thứ hai (sau "Passing null" của 8.1). Nó thường nằm ở code
cũ kiểu `$this->foo = ...` trong constructor mà quên khai báo `public $foo;`, hoặc code gắn thêm dữ
liệu vào object của thư viện. Theo RFC [Deprecate dynamic properties](https://wiki.php.net/rfc/deprecate_dynamic_properties),
ở PHP 9 việc này dự kiến ném `Error`.

Nguồn: [UPGRADING 8.2](https://github.com/php/php-src/blob/PHP-8.2/UPGRADING),
[Migration 8.1 → 8.2](https://www.php.net/manual/en/migration82.php).

## 5. PHP 8.3 (23/11/2023)

PHP 8.3 là bản "nhỏ mà tiện": không có tính năng lớn như enum hay property hooks, nhưng có vài công cụ
dùng hằng ngày (`#[\Override]`, hằng có kiểu, `json_validate()`). Đây cũng là bản PHP tối thiểu của
Laravel 13.

### 5.1 Tính năng chính

| Tính năng | Trông như thế nào | Học ở đâu |
|---|---|---|
| Hằng class có kiểu | `const string DEFAULT = 'draft';` | [Chương 09, mục 7.3](09-oop-co-ban.md) |
| Attribute `#[\Override]`: báo lỗi nếu method không thực sự ghi đè method nào | `#[\Override] public function title()` | [Chương 10, mục 9.4](10-oop-nang-cao.md) |
| Lấy hằng class theo tên động | `Post::{$name}` | [Chương 09, mục 7.4](09-oop-co-ban.md) |
| Khởi tạo lại property readonly trong `__clone()` | `$this->at = new DateTimeImmutable()` trong `__clone` | [Chương 10, mục 4](10-oop-nang-cao.md) |
| `readonly` cho anonymous class | `new readonly class { ... }` | [Chương 10, mục 4.4](10-oop-nang-cao.md) |
| Giá trị khởi tạo của biến `static` là biểu thức tuỳ ý | `static $x = compute();` | [Chương 08, mục 9.3](08-ham.md) |
| Hàm `json_validate()`: kiểm tra JSON hợp lệ mà không dựng giá trị | `json_validate($s)` | [Chương 14, mục 7](14-file-json-thoi-gian.md) |
| Hàm `mb_str_pad()`, `str_increment()`, `str_decrement()` | `mb_str_pad('Hà', 5, '*')` | [Chương 05](05-chuoi.md), [Chương 07, mục 2.6](07-toan-tu-dieu-khien.md) |
| `Random\Randomizer::getBytesFromString()`, `getFloat()`, `nextFloat()` | Sinh mã ngẫu nhiên từ một bảng ký tự | [Chương 17, mục 6.2](17-bao-mat.md) |
| Exception riêng của extension Date: `DateMalformedStringException`, `DateInvalidTimeZoneException`... thay cho warning và `Exception` chung | `catch (DateMalformedStringException $e)` | [Chương 14](14-file-json-thoi-gian.md) |
| `php -l` lint được nhiều file một lúc | `php -l a.php b.php` | [Chương 01, mục 4.6](01-php-la-gi.md) |
| Phát hiện tràn stack: ini `zend.max_allowed_stack_size` | Đệ quy quá sâu ném `Error` thay vì làm process crash | [Chương 08, mục 13.3](08-ham.md) |

```php
<?php
declare(strict_types=1);

interface HasStatus
{
    const string DEFAULT = 'draft';               // hằng có kiểu (8.3)
}

class Post implements HasStatus
{
    public function __construct(public readonly DateTimeImmutable $at) {}

    public function __clone()
    {
        $this->at = new DateTimeImmutable('2026-01-01'); // khởi tạo lại readonly trong __clone (8.3)
    }

    public function title(): string
    {
        return 'Bài viết';
    }
}

final class News extends Post
{
    #[\Override]                                  // #[\Override] (8.3)
    public function title(): string
    {
        return 'Tin tức';
    }
}

$name = 'DEFAULT';
echo Post::{$name}, "\n";                         // in ra: draft

$post = new News(new DateTimeImmutable('2025-05-05'));
$copy = clone $post;
echo $copy->at->format('Y-m-d'), ' ', $copy->title(), "\n"; // in ra: 2026-01-01 Tin tức

var_dump(json_validate('{"a": 1}'));              // in ra: bool(true)
var_dump(json_validate('{a: 1}'));                // in ra: bool(false)
echo mb_str_pad('Hà', 5, '*'), "|\n";             // in ra: Hà***|
echo str_increment('Az'), "\n";                   // in ra: Ba

try {
    new DateTimeImmutable('không phải ngày');
} catch (DateMalformedStringException $e) {
    echo get_class($e), "\n";                     // in ra: DateMalformedStringException
}
```

`#[\Override]` đáng dùng nhất trong nhóm này. Nó bắt lỗi gõ nhầm tên method hoặc lỗi khi class cha đổi
tên method mà class con không biết:

```php
<?php
declare(strict_types=1);

class Base
{
    public function titel(): string { return 'gõ nhầm tên'; }
}

final class Child extends Base
{
    #[\Override]
    public function title(): string { return 'x'; }
}
// PHP 8.3 in ra:
// Fatal error: Child::title() has #[\Override] attribute, but no matching parent method exists in ... on line 12
// PHP 8.2: không báo gì (attribute lạ chỉ là metadata, không ai kiểm tra)
```

Để ý dòng cuối: trên PHP 8.2, `#[\Override]` không gây lỗi, vì attribute chỉ được kiểm tra khi có
code đọc nó. Bạn có thể thêm `#[\Override]` vào code vẫn phải chạy trên 8.2; nó chỉ có tác dụng từ 8.3.

### 5.2 Thay đổi phá vỡ tương thích

| Thay đổi | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Gán key âm `n` vào mảng rỗng: key tự động tiếp theo là `n+1` thay vì `0` | Xem bảng dưới | Đừng dựa vào key tự động sau key âm |
| `range()` chặt hơn: ném `TypeError` với object/array, `ValueError` khi `$step` âm cho dãy tăng; phát warning với chuỗi rỗng, chuỗi nhiều byte... `range('5', 'z')` giờ cho dãy ký tự | Code gọi `range()` với tham số "lạ" | Truyền số hoặc ký tự đơn rõ ràng |
| Trait có static property: class dùng trait có ô nhớ static riêng, kể cả khi class cha đã khai báo static property đó | Static property chia sẻ qua trait giữa cha và con có thể tách ra | Xem [Chương 09, mục 11.5](09-oop-co-ban.md) |
| `unserialize()`: các `E_NOTICE` thành `E_WARNING`; thêm warning khi còn dữ liệu thừa sau chuỗi serialize | Log nhiều warning hơn | Sửa dữ liệu serialize hỏng |
| `array_sum()`, `array_product()` phát warning khi phần tử không đổi được sang số (trước đây mảng và object bị bỏ qua lặng lẽ) | Log có warning mới | Lọc mảng trước khi tính |
| `SQLite3` ném `SQLite3Exception` thay vì `Exception` | Chỉ ảnh hưởng nếu so tên class chính xác | |
| Đệ quy quá sâu có thể ném `Error` sớm hơn (giới hạn stack mới) | Chương trình vốn "sát nút" tràn stack | Đổi đệ quy thành vòng lặp |

Chuyện key âm, chạy thử trên nhiều bản:

```php
<?php
$a = [];
$a[-5] = 'x';
$a[] = 'y';
echo implode(',', array_keys($a)), "\n";

$b = [-5 => 'x'];
$b[] = 'y';
echo implode(',', array_keys($b)), "\n";
```

| Bản | Dòng 1 (mảng rỗng rồi gán `[-5]`) | Dòng 2 (literal `[-5 => 'x']`) |
|---|---|---|
| 7.4 | `-5,0` | `-5,0` |
| 8.0 tới 8.2 | `-5,0` | `-5,-4` |
| 8.3 trở đi | `-5,-4` | `-5,-4` |

Thay đổi này đi qua hai bước: 8.0 sửa cho literal mảng (RFC
[Arrays starting with a negative index](https://wiki.php.net/rfc/negative_array_index)), 8.3 sửa nốt
trường hợp gán vào mảng rỗng.

### 5.3 Deprecation của 8.3

```php
<?php
declare(strict_types=1);
error_reporting(E_ALL);

$s = '';
$s++;
var_dump($s);

$code = 'Az';
$code++;                       // chuỗi chữ-số: 8.3, 8.4 chưa có thông báo (8.5 có, mục 7.3)
var_dump($code);

class A
{
    public function name(): string
    {
        return get_class();    // gọi không đối số
    }
}
echo (new A())->name(), "\n";
```

```
PHP 8.2:
string(1) "1"
string(2) "Ba"
A

PHP 8.3:
Deprecated: Increment on non-alphanumeric string is deprecated in ... on line 6
string(1) "1"
string(2) "Ba"
Deprecated: Calling get_class() without arguments is deprecated in ... on line 17
A
```

| Deprecated | Thay bằng |
|---|---|
| `++` trên chuỗi rỗng hoặc chuỗi không phải chữ-số; `--` trên chuỗi rỗng hoặc không phải số. (`++` trên chuỗi chữ-số như `'Az'` ở 8.3 chỉ bị "soft deprecated": tài liệu khuyên tránh nhưng chưa phát thông báo; từ 8.5 nó cũng phát deprecation, mục 7.3) | `str_increment()`, `str_decrement()` cho chuỗi; ép sang số trước khi tăng. Xem [Chương 07, mục 2.6](07-toan-tu-dieu-khien.md) |
| `get_class()`, `get_parent_class()` không đối số | `self::class`, `static::class`, `get_class($this)` |
| `assert_options()` và các hằng `ASSERT_ACTIVE`, `ASSERT_BAIL`, `ASSERT_CALLBACK`, `ASSERT_EXCEPTION`, `ASSERT_WARNING` | Cấu hình `zend.assertions` trong ini |
| Biến thể `MT_RAND_PHP` của Mt19937 | `MT_RAND_MT19937` (mặc định) |
| `ReflectionProperty::setValue()` với một tham số | Truyền `null` làm tham số đầu cho static property |
| `ldap_connect()` với host và port riêng, `mb_strimwidth()` với `$width` âm, `SQLite3::enableExceptions(false)`, `NumberFormatter::TYPE_CURRENCY` | Xem `UPGRADING` 8.3 |

Ngoài ra, 8.3 phát warning (chưa phải deprecation) khi `++`/`--` trên `bool` và `--` trên `null`, vì
hành vi các trường hợp này dự kiến thay đổi ở bản major sau (hiện tại chúng không làm gì).

Nguồn: [UPGRADING 8.3](https://github.com/php/php-src/blob/PHP-8.3/UPGRADING),
[Migration 8.2 → 8.3](https://www.php.net/manual/en/migration83.php),
[RFC Path to Saner Increment/Decrement operators](https://wiki.php.net/rfc/saner-inc-dec-operators).

## 6. PHP 8.4 (21/11/2024)

PHP 8.4 là bản thay đổi cách viết class nhiều nhất kể từ 8.0: property hooks và asymmetric
visibility làm phần lớn getter/setter viết tay trở nên thừa. Tại 10/2026 đây vẫn là bản phổ biến trên
production.

### 6.1 Tính năng chính

| Tính năng | Trông như thế nào | Học ở đâu |
|---|---|---|
| Property hooks: gắn logic `get`/`set` vào property | `public string $email { set(string $v) { ... } }` | [Chương 10, mục 5](10-oop-nang-cao.md) |
| Asymmetric visibility: quyền đọc và quyền ghi khác nhau | `public private(set) int $count` | [Chương 10, mục 6](10-oop-nang-cao.md) |
| Property trong interface (kèm hook) | `interface HasName { public string $name { get; } }` | [Chương 09, mục 10.5](09-oop-co-ban.md) |
| Lazy objects (ghost và proxy) qua Reflection | `$r->newLazyGhost(fn ($o) => ...)` | [Chương 10, mục 10](10-oop-nang-cao.md) |
| `new` không cần bọc ngoặc khi gọi tiếp | `new User()->login()` | [Chương 09, mục 1.4](09-oop-co-ban.md) |
| Attribute `#[\Deprecated]` cho hàm, method, hằng class của bạn | `#[\Deprecated(message: '...', since: '2.0')]` | [Chương 10, mục 9.4](10-oop-nang-cao.md) |
| `array_find()`, `array_find_key()`, `array_any()`, `array_all()` | `array_find($xs, fn ($x) => $x > 5)` | [Chương 06, mục 7.4](06-mang.md) |
| `mb_trim()`, `mb_ltrim()`, `mb_rtrim()`, `mb_ucfirst()`, `mb_lcfirst()` | `mb_ucfirst('đà nẵng')` | [Chương 05, mục 5.3](05-chuoi.md) |
| `request_parse_body()`: đọc body `multipart/form-data` của `PUT`/`PATCH` | | [Chương 15, mục 2.6](15-php-va-web.md) |
| Class con của PDO theo driver (`Pdo\Mysql`, `Pdo\Sqlite`...) và `PDO::connect()` | `PDO::connect('sqlite::memory:')` | [Chương 16, mục 2.2](16-php-va-database.md) |
| `Dom\HTMLDocument`: parser HTML5 đúng chuẩn | `Dom\HTMLDocument::createFromString($html)` | |
| `BcMath\Number`: số thập phân chính xác, dùng được với toán tử `+ - * /` | `new BcMath\Number('0.1') + new BcMath\Number('0.2')` | [Chương 04, mục 4.8](04-kieu-du-lieu.md) |
| Enum `RoundingMode` và 4 chế độ làm tròn mới cho `round()` | `round(2.5, 0, RoundingMode::HalfEven)` | [Chương 14, mục 9.4](14-file-json-thoi-gian.md) |
| `DateTime[Immutable]::createFromTimestamp()`, `getMicrosecond()`, `setMicrosecond()` | | [Chương 14](14-file-json-thoi-gian.md) |
| `http_get_last_response_headers()` thay biến ma thuật `$http_response_header` | | [Chương 14, mục 4.5](14-file-json-thoi-gian.md) |

```php
<?php
declare(strict_types=1);

final class User
{
    public private(set) int $loginCount = 0;      // asymmetric visibility (8.4)

    public string $email {                        // property hook (8.4)
        set(string $value) {
            $this->email = strtolower(trim($value));
        }
    }

    public string $domain {                       // virtual property: chỉ có get
        get => substr($this->email, strpos($this->email, '@') + 1);
    }

    public function __construct(string $email)
    {
        $this->email = $email;
    }

    public function login(): static
    {
        $this->loginCount++;
        return $this;
    }

    #[\Deprecated(message: 'dùng login()', since: '2.0')] // #[\Deprecated] (8.4)
    public function signIn(): void
    {
        $this->login();
    }
}

$u = new User('  An@Example.COM ');
echo $u->email, ' ', $u->domain, "\n";            // in ra: an@example.com example.com

echo new User('b@x.vn')->login()->loginCount, "\n"; // in ra: 1   (new không cần ngoặc, 8.4)

try {
    $u->loginCount = 99;
} catch (Error $e) {
    echo $e->getMessage(), "\n";
    // in ra: Cannot modify private(set) property User::$loginCount from global scope
}

$nums = [3, 8, 11, 20];
var_dump(array_find($nums, fn (int $n): bool => $n > 5));   // in ra: int(8)
var_dump(array_any($nums, fn (int $n): bool => $n > 15));   // in ra: bool(true)
var_dump(array_all($nums, fn (int $n): bool => $n > 0));    // in ra: bool(true)
echo mb_ucfirst('đà nẵng'), '|', mb_trim('  xin chào  '), "|\n"; // in ra: Đà nẵng|xin chào|
echo round(2.5, 0, RoundingMode::HalfEven), "\n";            // in ra: 2
echo password_get_info(password_hash('x', PASSWORD_BCRYPT))['options']['cost'], "\n"; // in ra: 12
```

Dòng cuối dẫn sang một thay đổi đáng chú ý ở mục 6.2: cost mặc định của bcrypt.

### 6.2 Thay đổi phá vỡ tương thích

| Thay đổi | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Cost mặc định của `PASSWORD_BCRYPT` (cũng là `PASSWORD_DEFAULT`) tăng từ 10 lên 12 (RFC [bcrypt cost 2023](https://wiki.php.net/rfc/bcrypt_cost_2023)) | Hash mật khẩu chậm hơn khoảng 4 lần (mỗi đơn vị cost gấp đôi thời gian). `password_needs_rehash($hashCũ, PASSWORD_DEFAULT)` trả `true` cho hash cost 10 cũ, nên code rehash khi đăng nhập sẽ dần nâng cấp mọi hash | Đây là hành vi mong muốn. Kiểm tra server chịu được tải đăng nhập với cost 12; xem [Chương 17, mục 5.4](17-bao-mat.md) |
| `exit()`/`die()` thành hàm thật: truyền được như callable, chịu ảnh hưởng `strict_types`, đối số sai kiểu có thể ném `TypeError` | Code `exit($mảng)` hoặc `exit(1.5)`... hiếm gặp | Truyền `int` hoặc `string` |
| Bỏ mức lỗi `E_STRICT`; hằng `E_STRICT` bị deprecated | Code dùng `E_STRICT` trong `error_reporting()` phát deprecation | Bỏ `E_STRICT` khỏi biểu thức |
| Cấu hình JIT mặc định đổi thành `opcache.jit=disable`, `opcache.jit_buffer_size=64M` (trước đây `tracing` và `0`) | Ai bật JIT chỉ bằng cách đặt `opcache.jit_buffer_size` sẽ thấy JIT không bật nữa | Đặt `opcache.jit=tracing` (hoặc chế độ khác) tường minh. Xem [Chương 18](18-fpm-nginx-opcache.md) |
| `round()` được viết lại: sửa vài lỗi làm tròn, ném `ValueError` khi `$mode` không hợp lệ | Vài kết quả biên khác trước (ví dụ `round(0.49999999999999994)` giờ là `0.0`) | Thêm test cho chỗ làm tròn tiền |
| PCRE2 nâng lên 10.44: `{,3}` giờ là quantifier (0 tới 3 lần) chứ không phải chữ thường | Regex có `{,n}` đổi nghĩa | Escape `\{` nếu muốn khớp ký tự `{` |
| Extension `imap`, `oci8`, `pdo_oci`, `pspell` bị tách khỏi mã nguồn PHP, chuyển sang PECL | Server cần `imap_open()` phải cài extension từ PECL | Cài từ PECL hoặc dùng thư viện thay thế |
| Thêm resource thành object: `Dba\Connection`, `Odbc\Connection`, `Odbc\Result` | `is_resource()` thành `false` | Kiểm tra `=== false` |
| Hằng của nhiều class có sẵn (Date, Intl, PDO, Reflection, SPL...) có kiểu; `GMP` thành `final` | Class con override các hằng đó với kiểu khác, hoặc kế thừa `GMP`, sẽ lỗi | Hiếm gặp |
| Thêm nhiều `ValueError`/`TypeError` cho đối số sai (`str_getcsv()` với separator nhiều byte, option `allowed_classes` của `unserialize()`...) | Code truyền giá trị sai từng "chạy được" giờ ném lỗi | Sửa đối số |

### 6.3 Deprecation của 8.4

```php
<?php
declare(strict_types=1);
error_reporting(E_ALL);

#[\Deprecated(message: 'dùng newName()', since: '2.0')]
function oldName(): void {}

oldName();

function find(int $id, string $name = null): void {}   // nullable ngầm

echo 0 ** -1, "\n";                                       // 0 mũ số âm

$f = fopen('php://memory', 'w+');
fputcsv($f, ['a', 'b']);                                  // không truyền $escape

trigger_error('lỗi nặng', E_USER_ERROR);
```

```
PHP 8.3:
INF
Fatal error: lỗi nặng in ... on line 17

PHP 8.4:
Deprecated: find(): Implicitly marking parameter $name as nullable is deprecated, the explicit nullable type must be used instead in ... on line 10
Deprecated: Function oldName() is deprecated since 2.0, dùng newName() in ... on line 8
Deprecated: Power of base 0 and negative exponent is deprecated in ... on line 12
INF
Deprecated: fputcsv(): the $escape parameter must be provided as its default value will change in ... on line 15
Deprecated: Passing E_USER_ERROR to trigger_error() is deprecated since 8.4, throw an exception or call exit with a string message instead in ... on line 17
Fatal error: lỗi nặng in ... on line 17
```

Thông báo của dòng 10 hiện đầu tiên vì nó được phát lúc biên dịch file (khai báo hàm), các thông báo
còn lại phát lúc chạy.

| Deprecated | Thay bằng |
|---|---|
| *Implicitly nullable type*: tham số có kiểu không nullable nhưng giá trị mặc định `null` (`string $name = null`) | Viết rõ `?string $name = null` (hoặc `string\|null`). Rector sửa tự động được. Xem [Chương 08, mục 3.6](08-ham.md) |
| `trigger_error(..., E_USER_ERROR)` | Ném exception, hoặc `exit('thông báo')` |
| `0 ** -1` (0 mũ số âm) | Hàm mới `fpow()` (theo IEEE 754) nếu thật sự muốn `INF` |
| Không truyền tham số `$escape` cho `fputcsv()`, `fgetcsv()`, `str_getcsv()` và các method CSV của `SplFileObject` | Truyền tường minh, thường là `escape: ''` để theo đúng RFC 4180. Xem [Chương 14, mục 5.3](14-file-json-thoi-gian.md) |
| Dùng `_` làm tên class | Đặt tên khác |
| Hằng `E_STRICT` | Bỏ đi |
| `lcg_value()` | `Random\Randomizer::getFloat()` |
| `mysqli_ping()`, `mysqli_kill()`, `mysqli_refresh()` | Lệnh SQL `KILL`, `FLUSH`; tự kết nối lại khi mất kết nối |
| Đổi ini `session.sid_length`, `session.sid_bits_per_character`; đổi ini `session.use_only_cookies`, `session.use_trans_sid`... và hằng `SID` | Giữ mặc định; session chỉ qua cookie. Xem [Chương 15](15-php-va-web.md) |
| `DatePeriod::__construct()` với chuỗi ISO 8601 | `DatePeriod::createFromISO8601String()` |
| `stream_context_set_option()` với 2 đối số | `stream_context_set_options()` |
| `unserialize()` chuỗi dùng tag `S` hoa; `xml_set_object()`; `ReflectionMethod::__construct()` với 1 đối số; `session_set_save_handler()` với hơn 2 đối số | Xem `UPGRADING` 8.4 |

Nguồn: [UPGRADING 8.4](https://github.com/php/php-src/blob/PHP-8.4/UPGRADING),
[Migration 8.3 → 8.4](https://www.php.net/manual/en/migration84.php),
[RFC Deprecations for PHP 8.4](https://wiki.php.net/rfc/deprecations_php_8_4).

## 7. PHP 8.5 (20/11/2025)

PHP 8.5 là bản mới nhất đã phát hành chính thức tại 10/2026 và là bản chuẩn của giáo trình này. Điểm
nhấn là pipe operator, `clone` có tham số, extension URI, và một đợt deprecation lớn (RFC
[Deprecations for PHP 8.5](https://wiki.php.net/rfc/deprecations_php_8_5)) dọn nhiều cú pháp và hàm
cũ.

### 7.1 Tính năng chính

| Tính năng | Trông như thế nào | Học ở đâu |
|---|---|---|
| Pipe operator `\|>` | `$s \|> trim(...) \|> strtolower(...)` | [Chương 07, mục 11](07-toan-tu-dieu-khien.md) |
| `clone()` nhận mảng property mới ("clone with"), kể cả property readonly | `clone($this, ['amount' => 250])` | [Chương 10, mục 7](10-oop-nang-cao.md) |
| Attribute `#[\NoDiscard]` và ép kiểu `(void)` | `#[\NoDiscard] function save(): bool` | [Chương 08, mục 15](08-ham.md) |
| `array_first()`, `array_last()` | `array_first([3, 5, 7])` cho `3` | [Chương 06, mục 7.2](06-mang.md) |
| Extension URI (luôn bật): `Uri\Rfc3986\Uri`, `Uri\WhatWg\Url` | `new Uri\Rfc3986\Uri('https://...')` | |
| Closure và first-class callable trong biểu thức hằng (giá trị mặc định, attribute, hằng) | `function f(Closure $c = static function () { return 1; })` | [Chương 08, mục 5.4](08-ham.md) |
| Fatal error kèm backtrace (ini `fatal_error_backtraces`) | "Maximum execution time exceeded" giờ có stack trace | [Chương 12](12-loi-exception.md) |
| `get_error_handler()`, `get_exception_handler()` | Lấy handler hiện tại | [Chương 12](12-loi-exception.md) |
| Cờ `FILTER_THROW_ON_FAILURE` cho `filter_var()` | Ném `Filter\FilterFailedException` khi validate thất bại | [Chương 12, mục 4](12-loi-exception.md) |
| Constructor promotion cho property `final`; `#[\Override]` cho property; asymmetric visibility cho static property; `#[\Deprecated]` cho hằng toàn cục khai báo bằng `const` | `public function __construct(final public int $id)` | [Chương 10, mục 9.4](10-oop-nang-cao.md) |
| `Closure::getCurrent()` | Closure ẩn danh gọi đệ quy chính nó | [Chương 08](08-ham.md) |
| `curl_share_init_persistent()`: chia sẻ kết nối cURL giữa các request | | |
| OPcache luôn được build sẵn và luôn được nạp | Không còn `zend_extension=opcache.so`; vẫn bật tắt bằng `opcache.enable` | [Chương 02, mục 3.5](02-php-chay-nhu-the-nao.md) |
| ini `max_memory_limit`: trần của `memory_limit` | Chặn code tự `ini_set('memory_limit', '-1')` vượt trần | [Chương 19, mục 9.3](19-ben-trong-engine.md) |

```php
<?php
declare(strict_types=1);

final readonly class Money
{
    public function __construct(public int $amount, public string $currency) {}

    public function withAmount(int $amount): self
    {
        return clone($this, ['amount' => $amount]); // clone with (8.5)
    }
}

#[\NoDiscard('kết quả cho biết có lưu thành công không')]   // #[\NoDiscard] (8.5)
function save(Money $m): bool
{
    return true;
}

$slug = '  Xin Chào PHP 8.5  '
    |> trim(...)                                   // pipe |> (8.5)
    |> strtolower(...)
    |> (fn (string $s): string => str_replace(' ', '-', $s));
echo $slug, "\n";                                  // in ra: xin-chào-php-8.5

$m = new Money(100, 'VND')->withAmount(250);
echo $m->amount, ' ', $m->currency, "\n";          // in ra: 250 VND

echo array_first([3, 5, 7]), ' ', array_last([3, 5, 7]), "\n"; // in ra: 3 7
var_dump(array_first([]));                         // in ra: NULL

$uri = new Uri\Rfc3986\Uri('https://example.com:8080/a/b?x=1#top'); // extension URI (8.5)
echo $uri->getHost(), ' ', $uri->getPort(), ' ', $uri->getPath(), "\n"; // in ra: example.com 8080 /a/b

(void) save($m);                                   // (void): cố ý bỏ giá trị trả về, không cảnh báo
save($m);                                          // bỏ quên giá trị trả về
// in ra: Warning: The return value of function save() should either be used or intentionally
//        ignored by casting it as (void), kết quả cho biết có lưu thành công không in ... on line 36
```

Hai điểm cần để ý trong ví dụ:

- `strtolower()` chỉ đổi chữ ASCII (mục 4.2), nên `'Chào'` thành `'chào'` là nhờ chữ `C` là ASCII; chữ
  có dấu viết hoa như `'À'` sẽ không đổi. Văn bản tiếng Việt cần `mb_strtolower()`.
- Vế phải của `|>` là arrow function phải bọc trong ngoặc; lý do nằm ở
  [Chương 07, mục 11.2](07-toan-tu-dieu-khien.md).

### 7.2 Thay đổi phá vỡ tương thích

Bản 8.5 thêm nhiều warning mới cho các thao tác trước đây im lặng cho kết quả vô nghĩa (RFC
[Warnings for PHP 8.5](https://wiki.php.net/rfc/warnings-php-8-5)):

```php
<?php
declare(strict_types=1);
error_reporting(E_ALL);

var_dump((int) 1e20);               // float quá lớn để thành int

[$a, $b] = 42;                      // phân rã một giá trị không phải mảng
var_dump($a);

var_dump((int) NAN);
```

```
PHP 8.4:
int(7766279631452241920)
NULL
int(0)

PHP 8.5:
Warning: The float 1.0E+20 is not representable as an int, cast occurred in ... on line 5
int(7766279631452241920)
Warning: Cannot use int as array in ... on line 7
Warning: Cannot use int as array in ... on line 7
NULL
Warning: The float NAN is not representable as an int, cast occurred in ... on line 10
int(0)
```

Con số `7766279631452241920` ở dòng đầu là kết quả vô nghĩa: manual ghi rằng ép float nằm ngoài phạm
vi `int` cho kết quả không xác định. (Trên máy 64-bit, php-src lấy phần dư của giá trị khi chia cho
2^64, nên `1e20` ra đúng số này.) 8.5 không đổi kết quả, chỉ bắt đầu cảnh báo. Warning ở dòng 7 in
hai lần vì có hai biến `$a`, `$b` cần phân rã.

| Thay đổi | Ảnh hưởng | Cách xử lý |
|---|---|---|
| Warning khi ép float không biểu diễn được thành int (quá lớn, `NAN`, `INF`), và khi ép `NAN` sang kiểu khác | Log có warning mới; thường lộ ra bug thật | Kiểm tra phạm vi trước khi ép. Xem [Chương 04, mục 4.5 và 4.7](04-kieu-du-lieu.md) |
| Warning khi phân rã `[...] = ` / `list()` một giá trị không phải mảng (trừ `null`) | Như trên | Kiểm tra kiểu trước khi phân rã |
| So sánh lỏng object "không so được" (enum, `CurlHandle`...) với bool luôn theo `(bool) $object` | Trước đây `$enum == $biếnTrue` luôn `false` nếu vế bool không phải literal | Dùng `===` |
| `#[\Attribute]` gắn vào abstract class, enum, interface, trait báo lỗi lúc biên dịch (trước đây chỉ lỗi khi `newInstance()`) | Code khai báo attribute sai chỗ | Sửa khai báo, hoặc dùng `#[\DelayedTargetValidation]` |
| Bỏ ini `disable_classes` | Cấu hình hardening dựa vào nó mất tác dụng | Dùng biện pháp khác (`disable_functions` vẫn còn) |
| Không dùng được `array`, `callable` làm tên alias trong `class_alias()` | Hiếm gặp | |
| Giá trị các hằng `PDO::FETCH_GROUP`, `FETCH_UNIQUE`, `FETCH_CLASSTYPE`, `FETCH_PROPS_LATE`, `FETCH_SERIALIZE` thay đổi; `FETCH_PROPS_LATE` dùng sai mode hoặc `FETCH_INTO` trong `fetchAll()` ném `ValueError` | Code lưu giá trị số của các hằng này (thay vì dùng tên hằng) sẽ sai | Luôn dùng tên hằng |
| Gọi lại constructor của `mysqli` trên object đã tạo ném `Error` | Hiếm gặp | |
| `ArrayObject` không nhận enum | Hiếm gặp | |
| `zend_extension=opcache.so` trong ini phát warning (OPcache đã có sẵn) | Image Docker cũ có dòng này | Xoá dòng nạp opcache |

### 7.3 Deprecation của 8.5

```php
<?php
declare(strict_types=1);
error_reporting(E_ALL);

$n = (integer) '5';                 // tên ép kiểu không chuẩn

switch ($n) {
    case 5;                         // case kết thúc bằng ; thay vì :
        echo "năm\n";
}

$map = ['' => 'rỗng'];
echo $map[null], "\n";              // null làm key mảng

echo chr(300) === chr(44) ? "chr bọc vòng\n" : "khác\n";  // chr ngoài 0..255

$code = 'A9';
$code++;                            // tăng chuỗi không phải số
echo $code, "\n";
```

```
PHP 8.4:
năm
rỗng
chr bọc vòng
B0

PHP 8.5:
Deprecated: Non-canonical cast (integer) is deprecated, use the (int) cast instead in ... on line 5
Deprecated: Case statements followed by a semicolon (;) are deprecated, use a colon (:) instead in ... on line 8
năm
Deprecated: Using null as an array offset is deprecated, use an empty string instead in ... on line 13
rỗng
Deprecated: chr(): Providing a value not in-between 0 and 255 is deprecated, this is because a byte value must be in the [0, 255] interval. The value used will be constrained using % 256 in ... on line 15
chr bọc vòng
Deprecated: Increment on non-numeric string is deprecated, use str_increment() instead in ... on line 18
B0
```

| Deprecated | Thay bằng |
|---|---|
| Tên ép kiểu không chuẩn `(boolean)`, `(integer)`, `(double)`, `(binary)` | `(bool)`, `(int)`, `(float)`, `(string)` |
| `case X;` (dấu chấm phẩy sau `case`) | `case X:` |
| Toán tử backtick `` `ls` `` (alias của `shell_exec()`) | `shell_exec()`, hoặc tốt hơn `proc_open()` với mảng đối số. Xem [Chương 07, mục 10.4](07-toan-tu-dieu-khien.md) |
| `null` làm key mảng (`$a[null]`) và trong `array_key_exists(null, ...)` | Chuỗi rỗng `''` |
| `++` trên chuỗi không phải số (`'A9'`, `'Az'`): giai đoạn tiếp theo của RFC saner inc/dec (mục 5.3) | `str_increment()` |
| `chr()` với số ngoài 0..255; `ord()` với chuỗi không đúng một byte | Tự `% 256` nếu đó là ý định; truyền đúng một byte |
| Biến ma thuật `$http_response_header` | `http_get_last_response_headers()` (8.4). Xem [Chương 14, mục 4.5](14-file-json-thoi-gian.md) |
| `curl_close()`, `curl_share_close()`, `finfo_close()`, `imagedestroy()`, `xml_parser_free()` (vô tác dụng từ khi resource thành object) | Bỏ lời gọi; gán `null` cho biến nếu muốn giải phóng sớm |
| `__debugInfo()` trả `null` | Trả `[]` |
| Khai báo lại một hằng đã có (`define()` hai lần) | Kiểm tra `defined()` trước |
| Các thao tác bind closure vốn đã phát warning (bind instance vào static closure, unbind `$this` khỏi closure dùng `$this`...) | Sửa logic bind. Xem [Chương 08, mục 12.5](08-ham.md) |
| Hằng và method riêng của từng driver nằm trên class `PDO` (`PDO::MYSQL_ATTR_INIT_COMMAND`, `PDO::MYSQL_ATTR_SSL_CA`, `PDO::sqliteCreateFunction()`...) | Dùng trên class con: `Pdo\Mysql::ATTR_INIT_COMMAND`, `Pdo\Mysql::ATTR_SSL_CA`, `Pdo\Sqlite::createFunction()`. Xem [Chương 16](16-php-va-database.md) |
| DSN `uri:` của PDO | Ghi DSN trực tiếp |
| `setAccessible()` của Reflection (vô tác dụng từ 8.1) | Bỏ lời gọi |
| `SplObjectStorage::contains()`, `attach()`, `detach()` | `offsetExists()`, `offsetSet()`, `offsetUnset()` |
| `ArrayObject`/`ArrayIterator` bọc object | Bọc mảng |
| Hằng `DATE_RFC7231` và `DateTimeInterface::RFC7231` | Định dạng tường minh |
| `$_SERVER['argc']`/`['argv']` lấy từ query string khi không phải CLI | Đặt `register_argc_argv=0`; đọc `$_GET` |
| `__sleep()`, `__wakeup()`: chỉ "soft deprecated" (tài liệu khuyên tránh, chưa phát thông báo) | `__serialize()`, `__unserialize()`. Xem [Chương 10, mục 11.2](10-oop-nang-cao.md) |
| `mysqli_execute()`, `socket_set_timeout()`, `readdir()`/`closedir()` không đối số, ini `report_memleaks`, `intl.error_level` | Xem `UPGRADING` 8.5 |

⚠️ Hằng `PDO::MYSQL_ATTR_*` xuất hiện trong file `config/database.php` mặc định của Laravel các bản
cũ (tuỳ chọn SSL của kết nối MySQL). Trên PHP 8.5 chúng phát deprecation. File cấu hình của Laravel 13
đã chuyển sang `Pdo\Mysql::ATTR_SSL_CA`; dự án tạo từ bản cũ cần tự sửa file cấu hình của mình theo,
thay vì tự tắt thông báo.

Nguồn: [UPGRADING 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING),
[Migration 8.4 → 8.5](https://www.php.net/manual/en/migration85.php).

## 8. Bảng tra cứu nhanh

Các bảng dưới gom lại mục 2 tới 7. Dùng khi cần trả lời nhanh "cái này có từ bản nào".

### 8.1 Hệ thống kiểu qua từng bản

| Bản | Thêm gì vào hệ thống kiểu |
|---|---|
| 7.4 (nhắc lại) | Typed property |
| 8.0 | Union type `A\|B`, `mixed`, kiểu trả về `static` |
| 8.1 | `never`, pure intersection type `A&B`, enum (là một kiểu), `readonly` property |
| 8.2 | DNF type `(A&B)\|null`, `null`/`false` đứng riêng, `true`, `readonly class` |
| 8.3 | Hằng class có kiểu |
| 8.4 | Property hooks, asymmetric visibility, property trong interface |
| 8.5 | `Closure` là subtype chính thức của `callable`; `final` cho property được promote |

### 8.2 Cú pháp và toán tử

| Cú pháp | Bản |
|---|---|
| Named arguments, nullsafe `?->`, `match`, attributes `#[...]`, constructor promotion, `throw` là biểu thức, `catch` không biến, `$obj::class` | 8.0 |
| `enum`, first-class callable `f(...)`, `new` trong giá trị khởi tạo, `0o17`, unpack mảng key chuỗi | 8.1 |
| Hằng trong trait, `->value` của enum trong biểu thức hằng | 8.2 |
| `C::{$name}`, `#[\Override]`, readonly anonymous class | 8.3 |
| `new X()->m()` không ngoặc, `public private(set)`, hooks `{ get; set; }`, `#[\Deprecated]` | 8.4 |
| Pipe `\|>`, `clone($obj, [...])`, `(void)`, `#[\NoDiscard]`, closure trong biểu thức hằng | 8.5 |

### 8.3 Hàm mới hay dùng

| Hàm | Bản |
|---|---|
| `str_contains`, `str_starts_with`, `str_ends_with`, `fdiv`, `get_debug_type`, `get_resource_id`, `preg_last_error_msg` | 8.0 |
| `array_is_list`, `fsync`, `fdatasync` | 8.1 |
| `memory_reset_peak_usage`, `ini_parse_quantity`, `mysqli_execute_query`, `Random\Randomizer` | 8.2 |
| `json_validate`, `mb_str_pad`, `str_increment`, `str_decrement` | 8.3 |
| `array_find`, `array_find_key`, `array_any`, `array_all`, `mb_trim`, `mb_ltrim`, `mb_rtrim`, `mb_ucfirst`, `mb_lcfirst`, `request_parse_body`, `http_get_last_response_headers`, `fpow`, `bcround`/`bcfloor`/`bcceil` | 8.4 |
| `array_first`, `array_last`, `get_error_handler`, `get_exception_handler`, `curl_multi_get_handles`, `grapheme_levenshtein` | 8.5 |

### 8.4 Deprecation đáng nhớ nhất của mỗi bản

Nếu chỉ nhớ được một dòng cho mỗi bản, hãy nhớ dòng này. Đây là những thông báo bạn sẽ thấy nhiều nhất
trong log khi nâng cấp một dự án cũ.

| Bản | Deprecation hay gặp nhất | Sửa |
|---|---|---|
| 8.0 | Tham số bắt buộc đứng sau tham số tuỳ chọn | Đổi thứ tự |
| 8.1 | `Passing null to parameter #1 ... of type string is deprecated` | Xử lý `null` ở biên |
| 8.1 | `Return type of X::current() should either be compatible with ...` | Thêm kiểu trả về |
| 8.1 | `Implicit conversion from float ... to int loses precision` | Ép kiểu tường minh |
| 8.2 | `Creation of dynamic property ... is deprecated` | Khai báo property |
| 8.2 | `Using ${var} in strings is deprecated` | `{$var}` |
| 8.3 | `Increment on non-alphanumeric string`, `get_class() without arguments` | `str_increment()`, `static::class` |
| 8.4 | `Implicitly marking parameter $x as nullable is deprecated` | `?Type $x = null` |
| 8.4 | `fputcsv(): the $escape parameter must be provided` | Truyền `escape: ''` |
| 8.5 | `Non-canonical cast (integer)`, `Using null as an array offset`, `curl_close()`, `PDO::MYSQL_ATTR_*` | Xem mục 7.3 |

### 8.5 Những thay đổi lặng lẽ đổi kết quả

Đây là danh sách "không có thông báo gì, chỉ có kết quả khác". Chỉ test bắt được chúng.

| Bản | Thay đổi |
|---|---|
| 8.0 | `0 == 'foo'` thành `false` (và mọi so sánh lỏng số với chuỗi không phải số, kể cả `switch`, `in_array`) |
| 8.0 | `'a' . $x + $y` tính `+` trước `.` |
| 8.0 | Sort ổn định |
| 8.0 | Ép float sang string không phụ thuộc locale |
| 8.0 | Literal `[-5 => 'x']` rồi `[] = ...` cho key `-4` thay vì `0` |
| 8.1 | `htmlspecialchars()` mặc định escape cả `'` |
| 8.1 | PDO MySQL (emulated prepare) và PDO SQLite trả `int`/`float` thay vì string |
| 8.1 | Biến `static` trong method kế thừa dùng chung với class cha |
| 8.2 | `strtolower()` và họ hàng chỉ đổi chữ ASCII, bỏ qua locale |
| 8.2 | `str_split('')` trả `[]` |
| 8.3 | Mảng rỗng gán `[-5]` rồi `[] = ...` cho key `-4` thay vì `0` |
| 8.4 | Cost bcrypt mặc định 12; `password_needs_rehash()` trả `true` cho hash cost 10 |
| 8.4 | `round()` sửa vài kết quả biên |

## 9. Nâng cấp phiên bản PHP một cách an toàn

Phần này là quy trình làm thật trên một dự án (ví dụ một ứng dụng Laravel đang chạy 8.2, muốn lên
8.4 hoặc 8.5). Ý tưởng chung: để máy móc tìm lỗi trước khi người dùng tìm thấy, và đổi từng bước nhỏ
có thể quay lại được.

### 9.1 Toàn cảnh quy trình

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 0. Chuẩn bị: test đủ tin cậy, CI chạy được, đọc UPGRADING           │
 └──────────────────────────────┬──────────────────────────────────────┘
                                ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 1. Sửa deprecation trên bản HIỆN TẠI (log, test với E_ALL)          │
 └──────────────────────────────┬──────────────────────────────────────┘
                                ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 2. Dependency: composer why-not php X.Y, nâng thư viện/framework    │
 └──────────────────────────────┬──────────────────────────────────────┘
                                ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 3. Phân tích tĩnh: PHPStan với phpVersion mới; Rector sửa tự động   │
 └──────────────────────────────┬──────────────────────────────────────┘
                                ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 4. CI chạy test trên CẢ bản cũ và bản mới (matrix)                  │
 └──────────────────────────────┬──────────────────────────────────────┘
                                ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 5. Môi trường: Docker image, extension, php.ini, OPcache/JIT        │
 └──────────────────────────────┬──────────────────────────────────────┘
                                ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 6. Staging → canary một phần traffic → toàn bộ; theo dõi log, lỗi,  │
 │    latency; có đường lùi                                            │
 └──────────────────────────────┬──────────────────────────────────────┘
                                ▼
 ┌─────────────────────────────────────────────────────────────────────┐
 │ 7. Sau khi ổn định: nâng "php" trong composer.json, dùng tính năng  │
 │    mới, dọn code tương thích ngược                                  │
 └─────────────────────────────────────────────────────────────────────┘
```

Một nguyên tắc xuyên suốt: đi từng bản minor một nếu khoảng cách xa (8.1 lên 8.2, rồi 8.3...) hoặc ít
nhất đọc `UPGRADING` của mọi bản nằm giữa. Nhảy thẳng 8.1 lên 8.5 vẫn làm được nếu test tốt, nhưng khi
có lỗi sẽ khó biết lỗi đến từ bản nào.

### 9.2 Bước 0 và 1: test và deprecation trên bản hiện tại

Test là lưới an toàn duy nhất bắt được thay đổi lặng lẽ (mục 8.5). Trước khi nâng cấp, hãy chắc rằng
các luồng quan trọng (đăng nhập, thanh toán, tính tiền, xuất báo cáo) có test. Cách viết test nằm ở
[Chương 21](21-chat-luong-code.md).

Deprecation thì nên sửa ngay trên bản đang chạy, vì cảnh báo hôm nay là lỗi của bản sau:

- Môi trường dev, test và CI: `error_reporting = E_ALL` (bao gồm `E_DEPRECATED`) và
  `display_errors = On` ở dev. Với PHPUnit, cấu hình để lần chạy test kết thúc với mã lỗi khi có test phát
  deprecation (thuộc tính `failOnDeprecation="true"` trong `phpunit.xml`, có từ PHPUnit 10.1).
- Production: đừng hiện lỗi ra màn hình (`display_errors = Off`), nhưng có thể ghi deprecation vào log
  một thời gian để biết code nào thực sự chạy tới chỗ deprecated. Cách cấu hình log ở
  [Chương 12, mục 9](12-loi-exception.md).
- Laravel có kênh log riêng cho deprecation (`LOG_DEPRECATIONS_CHANNEL` trong `.env`, mặc định gửi vào
  kênh `null` tức bỏ đi); đổi sang một kênh thật khi chuẩn bị nâng cấp. Chi tiết ở Chương 23 trở đi.

Bạn cũng có thể chạy thử test suite trên bản mới ngay từ đầu (Docker, mục 9.5) chỉ để xem danh sách
deprecation và lỗi, trước khi sửa gì.

### 9.3 Bước 2: dependency

Code của bạn chỉ là một phần; thư viện trong `vendor/` cũng phải hỗ trợ bản PHP mới.

```bash
# Chạy trong thư mục dự án (máy dev)
composer why-not php 8.5          # gói nào đang chặn PHP 8.5? (alias của "composer prohibits")
composer outdated --direct        # gói phụ thuộc trực tiếp nào có bản mới hơn
composer check-platform-reqs      # PHP và extension trên máy này có đáp ứng composer.lock không
```

Một số điểm cần biết:

- Ràng buộc `"php": "^8.2"` trong `require` của `composer.json` nói "dự án chạy được trên 8.2 trở
  lên (dưới 9.0)". Nó không chứng minh code chạy được trên 8.5; nó chỉ là lời hứa.
- `config.platform.php` (ví dụ `"config": {"platform": {"php": "8.2.0"}}`) bảo Composer giả vờ đang
  chạy PHP 8.2 khi chọn phiên bản gói. Dùng khi máy dev chạy bản mới hơn production, để không cài nhầm
  gói đòi PHP cao hơn production. Khi nâng production, nhớ nâng cả giá trị này.
- Framework thường có bảng hỗ trợ PHP riêng. Ví dụ Laravel 13 hỗ trợ PHP 8.3 tới 8.5
  ([Chương 01, mục 2.4](01-php-la-gi.md)). Nâng PHP đôi khi kéo theo phải nâng framework trước.

### 9.4 Bước 3: phân tích tĩnh với PHPStan và Rector

*Phân tích tĩnh* (*static analysis*) là đọc code mà không chạy nó, để tìm lỗi. Hai công cụ chính (giới
thiệu ở [Chương 21](21-chat-luong-code.md)):

PHPStan có tham số `phpVersion` để phân tích code "như thể" chạy trên một bản PHP cụ thể. Theo tài
liệu PHPStan, nếu không đặt, nó tự suy ra từ `config.platform.php` của `composer.json`, và nếu vẫn
không có thì dùng bản PHP đang chạy PHPStan. Từ PHPStan 2.0 có thể đặt một khoảng:

```neon
# phpstan.neon (thư mục gốc dự án)
parameters:
    level: 6
    paths:
        - app
        - tests
    phpVersion:
        min: 80200   # bản thấp nhất còn phải hỗ trợ
        max: 80500   # bản cao nhất sẽ chạy
```

Gói `phpstan/phpstan-deprecation-rules` báo khi code gọi tới class, method, hàm được đánh dấu
deprecated. Khai báo kiểu đầy đủ cũng giúp PHPStan tìm ra những chỗ có thể truyền `null` vào hàm có sẵn
(deprecation lớn nhất của 8.1).

Rector là công cụ *tự sửa code* (*automated refactoring*): nó đọc code thành cây cú pháp, áp các
"rule" biến đổi, rồi ghi lại file. Với nâng cấp PHP, Rector có các bộ rule theo phiên bản (*PHP set*).
Ví dụ rule thêm `?` cho tham số nullable ngầm (deprecation của 8.4), đổi `strpos(...) !== false` thành
`str_contains()`, thêm `#[\Override]`... Theo tài liệu Rector, phiên bản PHP mục tiêu được lấy từ
`require.php` trong `composer.json` (hoặc đặt bằng `withPhpVersion()`).

```php
<?php
// rector.php (thư mục gốc dự án)
declare(strict_types=1);

use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/app', __DIR__ . '/tests'])
    ->withPhpSets();          // áp mọi PHP set tới bản trong composer.json
```

```bash
# Chạy trong thư mục dự án
composer require rector/rector --dev
vendor/bin/rector --dry-run       # chỉ in diff, chưa sửa
vendor/bin/rector                 # sửa thật
```

⚠️ Rector sửa hàng loạt file. Quy tắc an toàn:

- Luôn chạy `--dry-run` trước, đọc diff.
- Chạy trên một nhánh git sạch, commit riêng thay đổi của Rector, để review và revert dễ.
- Với code base lớn, tài liệu Rector khuyên bắt đầu từ `withPhpLevel(0)` rồi tăng dần `withPhpLevel(1)`,
  `withPhpLevel(2)`... mỗi lần một ít rule, thay vì bật tất cả cùng lúc.
- Rector chỉ đổi cú pháp; nó không biết logic nghiệp vụ. Thay đổi lặng lẽ (mục 8.5) vẫn phải nhờ test.
- Sau Rector, chạy lại code style (PHP CS Fixer, Pint) và test.

### 9.5 Bước 4: CI chạy nhiều phiên bản

Trong giai đoạn chuyển, cho CI chạy test trên cả bản cũ (đang ở production) và bản mới. Ví dụ với
GitHub Actions và action `shivammathur/setup-php`:

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        php: ['8.2', '8.4', '8.5']
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}
          coverage: none
      - run: composer install --no-interaction --prefer-dist
      - run: vendor/bin/phpunit
```

Chạy thử trên máy mà không cần cài nhiều bản PHP: dùng Docker image chính thức, mỗi bản một tag:

```bash
# Chạy trong thư mục dự án; mount code vào container rồi chạy test bằng PHP 8.5
docker run --rm -v "$PWD":/app -w /app php:8.5-cli vendor/bin/phpunit
# đổi thành php:8.4-cli để so sánh
```

(Image `php:*-cli` gốc chỉ có một số extension mặc định; dự án cần thêm extension như `pdo_mysql`,
`intl` thì phải tự build image với `docker-php-ext-install`.)

### 9.6 Bước 5: môi trường chạy

Code chạy được trên bản mới chưa đủ; môi trường cũng phải sẵn sàng:

| Hạng mục | Kiểm tra gì |
|---|---|
| Extension | Mọi extension đang dùng (`php -m` trên server cũ) có bản cho PHP mới không. Extension PECL (redis, imagick, swoole...) thường ra bản hỗ trợ muộn hơn PHP vài tuần. Extension bị tách khỏi core (mục 6.2: imap, oci8...) phải cài riêng |
| `php.ini` | Directive bị bỏ (`disable_classes` ở 8.5, `track_errors` ở 8.0...) hoặc đổi mặc định (JIT ở 8.4). Dòng `zend_extension=opcache.so` thừa ở 8.5 |
| OPcache, JIT | Sau khi nâng bản, cache cũ không dùng lại được: deploy mới sẽ biên dịch lại từ đầu; nếu dùng preload thì kiểm tra file preload chạy được trên bản mới. Xem [Chương 18](18-fpm-nginx-opcache.md) |
| PHP-FPM | Cấu hình pool chuyển sang thư mục của bản mới (ví dụ `/etc/php/8.5/fpm/pool.d/` trên Debian/Ubuntu) |
| Công cụ quanh code | Phiên bản Composer, PHPUnit, PHPStan, Xdebug phải hỗ trợ PHP mới |
| Hiệu năng | Đo trước và sau (latency p95, RAM mỗi worker) để chắc bản mới không chậm hơn. Xem [Chương 20](20-hieu-nang.md) |

### 9.7 Bước 6 và 7: triển khai và dọn dẹp

- Triển khai lên staging với dữ liệu gần thật, chạy các luồng chính bằng tay hoặc test end-to-end.
- Lên production từng phần nếu hạ tầng cho phép: một server, một pod, hoặc một phần trăm traffic
  (*canary*). Theo dõi log lỗi, số lỗi 500, latency. Giữ sẵn image/bản cũ để quay lại nhanh.
- Chạy cả các tiến trình không phải web: queue worker, cron, lệnh CLI. Chúng hay bị quên vì không ai
  "mở trang" để thấy lỗi.
- Khi ổn định, nâng `"php"` trong `composer.json` lên bản mới (ví dụ `"^8.4"`) để chính thức được dùng
  tính năng mới, bỏ code chỉ để tương thích bản cũ (`#[\ReturnTypeWillChange]`, nhánh
  `if (PHP_VERSION_ID < ...)`), và cập nhật `phpVersion` của PHPStan, `config.platform.php`.

### 9.8 Đối chiếu với Java và Go

| Khía cạnh | PHP | Java | Go |
|---|---|---|---|
| Nhịp phát hành | Mỗi năm một bản minor (cuối năm, thường tháng 11) | 6 tháng một bản; bản LTS định kỳ | 6 tháng một bản (tháng 2 và tháng 8) |
| Tương thích ngược | Bản minor có thể có BC break nhỏ và deprecation; bản major (8.0) đổi nhiều | Rất coi trọng tương thích; API bị xoá sau thời gian deprecated dài | Cam kết Go 1 compatibility: code Go 1 hợp lệ tiếp tục biên dịch được; các thay đổi hành vi được kiểm soát bằng dòng `go` trong `go.mod` và `GODEBUG` |
| Phát hiện vấn đề | Lúc chạy (deprecation là thông báo runtime, trừ vài cái lúc biên dịch file) + công cụ tĩnh | Phần lớn lúc biên dịch (`@Deprecated` cho cảnh báo của compiler) | Lúc biên dịch, `go vet` |

Khác biệt cốt lõi: PHP là ngôn ngữ thông dịch, nhiều vấn đề chỉ lộ ra khi dòng code đó thực sự chạy.
Vì vậy với PHP, test và phân tích tĩnh quan trọng hơn hẳn so với ngôn ngữ có compiler kiểm tra kiểu.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Nâng PHP trên production trước, sửa lỗi sau | Thay đổi lặng lẽ và lỗi của queue/cron chỉ lộ ra khi người dùng gặp | Theo quy trình mục 9: test, CI nhiều bản, staging, canary |
| Tắt `E_DEPRECATED` cho "sạch log" rồi quên luôn | Deprecation hôm nay là `Error` ở bản major sau | Tắt hiển thị trên production thì được, nhưng dev/test/CI phải thấy và sửa (mục 9.2) |
| Tin rằng `"php": "^8.2"` trong `composer.json` nghĩa là code chạy được trên 8.5 | Đó chỉ là ràng buộc khi cài gói, không kiểm tra code | Chạy test thật trên 8.5 (mục 9.5) |
| `is_resource($ch)` sau `curl_init()` | Từ 8.0 trả object `CurlHandle` | Kiểm tra `=== false` (mục 2.5) |
| So sánh giá trị từ PDO MySQL bằng `=== '1'` sau khi lên 8.1 | Từ 8.1 số trả về là `int` | So với `1`, hoặc chuẩn hoá kiểu ở tầng repository (mục 3.2) |
| Rải `(string)` khắp nơi để hết "Passing null to parameter" | Che lỗi dữ liệu thay vì xử lý; `null` thành chuỗi rỗng có thể sai nghiệp vụ | Quyết định ý nghĩa của `null` ở biên (input, database) (mục 3.3) |
| Gắn `#[\AllowDynamicProperties]` cho mọi class | Tắt thông báo nhưng giữ nguyên thiết kế mong manh | Khai báo property; chỉ dùng attribute cho code cũ chưa sửa kịp (mục 4.3) |
| Chạy Rector trên toàn bộ dự án rồi commit không đọc diff | Rule có thể đổi hành vi ở trường hợp biên; diff quá lớn không review được | `--dry-run`, tăng dần level, commit riêng (mục 9.4) |
| Quên queue worker và cron khi nâng cấp | Chúng chạy bằng PHP CLI, có thể khác bản với FPM, không có ai "mở trang" để thấy lỗi | Kiểm tra `php -v` của CLI và FPM; theo dõi log worker (mục 9.7) |
| Nói "tính năng X có từ PHP Y" theo trí nhớ | Rất dễ nhầm một bản | Kiểm `UPGRADING`, mục Changelog của manual, hoặc chạy thử (mục 1.4) |

## Tóm tắt chương

- Một bản PHP mới mang ba loại thay đổi: tính năng mới (không ảnh hưởng code cũ), deprecation (vẫn
  chạy, phát `E_DEPRECATED`, thường sẽ bị xoá ở bản major sau) và thay đổi phá vỡ tương thích.
- Nguồn chính xác nhất là file `UPGRADING` của php-src cho từng nhánh; migration guide của manual là
  bản dễ đọc; RFC giải thích lý do.
- 8.0 (major): union type, named arguments, `match`, nullsafe, attributes, constructor promotion, JIT;
  đồng thời đổi so sánh số với chuỗi, ưu tiên của `.`, biến nhiều warning thành `Error`, xoá cú pháp
  cũ.
- 8.1: enum, readonly property, `never`, intersection type, first-class callable, fiber; deprecation
  lớn nhất là truyền `null` vào hàm có sẵn.
- 8.2: `readonly class`, DNF type, `true`/`null`/`false` làm kiểu, extension Random; deprecated
  dynamic property và `"${var}"`.
- 8.3: hằng có kiểu, `#[\Override]`, `json_validate()`, exception riêng cho Date; deprecated `++` trên
  chuỗi lạ và `get_class()` không đối số.
- 8.4: property hooks, asymmetric visibility, lazy objects, `new X()->m()`, `array_find`/`any`/`all`,
  bcrypt cost 12; deprecated nullable ngầm và `$escape` mặc định của hàm CSV.
- 8.5: pipe `|>`, `clone()` có tham số, `#[\NoDiscard]`, `array_first`/`array_last`, extension URI,
  OPcache luôn có sẵn; deprecated cast `(integer)`, backtick, `null` làm key mảng, `curl_close()`,
  hằng `PDO::MYSQL_ATTR_*`.
- Thay đổi lặng lẽ đổi kết quả chỉ bắt được bằng test; deprecation nên sửa trên bản hiện tại trước khi
  nâng.
- Quy trình nâng cấp: test, sửa deprecation, dependency (`composer why-not`), PHPStan với
  `phpVersion`, Rector với PHP set, CI nhiều bản, kiểm tra môi trường, staging và canary, cuối cùng nâng
  `composer.json` và dọn code tương thích ngược.

## Câu hỏi tự kiểm tra

1. Deprecation khác thay đổi phá vỡ tương thích ở điểm nào? Vì sao chính sách của PHP muốn BC break ở
   bản minor phải "ồn ào"? (mục 1.2)
2. Trên PHP 7.4 và PHP 8.0, `in_array(0, ['a', 'b'])` trả gì? Giải thích bằng luật so sánh mới.
   (mục 2.2)
3. Vì sao `echo 'Tổng: ' . $a + $b;` cho kết quả khác nhau giữa 7.4 và 8.0?
4. Một dự án vừa lên PHP 8.1, log đầy dòng `Passing null to parameter #1 ($string) of type string is
   deprecated`. Những nguồn dữ liệu nào hay sinh ra `null` này, và nên sửa ở đâu? (mục 3.3)
5. Có ba cách xử lý thông báo "Creation of dynamic property": kể ra và cho biết khi nào dùng cách nào.
   (mục 4.3)
6. `#[\Override]` đặt trong code chạy trên PHP 8.2 thì chuyện gì xảy ra? Trên 8.3 thì sao? (mục 5.1)
7. Sau khi lên PHP 8.4, `password_needs_rehash()` bắt đầu trả `true` cho mọi user cũ. Đây là lỗi hay
   hành vi mong muốn? Cần lưu ý gì về hạ tầng? (mục 6.2)
8. Kể năm thay đổi "lặng lẽ đổi kết quả" trong dòng 8.x mà không có thông báo nào. (mục 8.5)
9. Vì sao nên sửa deprecation trên bản PHP đang chạy, trước khi nâng cấp? Cấu hình gì để thấy được
   chúng trong test? (mục 9.2)
10. Rector và PHPStan khác nhau thế nào về vai trò trong một lần nâng cấp? Vì sao không thể chỉ dựa vào
    hai công cụ này? (mục 9.4)

## Bài tập

1. Bảng tương thích của riêng bạn. Viết một script PHP `kiem-tra.php` (có `declare(strict_types=1);`)
   in ra kết quả của ít nhất 8 biểu thức đã thay đổi hành vi trong dòng 8.x (ví dụ `0 == 'foo'`,
   `str_split('')`, `htmlspecialchars("'")`, key tự động sau key âm...). Chạy nó bằng Docker trên ba
   bản `php:8.0-cli`, `php:8.2-cli`, `php:8.5-cli`
   (`docker run --rm -v "$PWD":/app -w /app php:8.5-cli php kiem-tra.php`) và lập bảng so sánh. Thêm
   `error_reporting(E_ALL);` để thấy cả deprecation.
2. Săn deprecation. Lấy một đoạn code PHP cũ (của bạn, hoặc tự viết theo phong cách PHP 7: dynamic
   property, `"${var}"`, tham số `string $x = null`, `utf8_encode()`, `strftime()`, callable
   `"self::method"`...). Chạy nó trên PHP 8.5 với `E_ALL`, ghi lại từng thông báo, rồi sửa từng chỗ
   bằng tay theo bảng trong chương cho tới khi không còn thông báo nào.
3. Rector thử nghiệm. Tạo một dự án Composer nhỏ với `"php": "^8.4"` trong `composer.json`, một thư
   mục `src/` chứa vài file viết kiểu cũ (có `strpos(...) !== false`, tham số nullable ngầm, class có
   method ghi đè không có `#[\Override]`...). Cài Rector, cấu hình `withPhpSets()`, chạy `--dry-run`,
   đọc diff và giải thích từng thay đổi Rector đề xuất thuộc bản PHP nào.
4. Kế hoạch nâng cấp. Giả sử bạn phụ trách một ứng dụng Laravel chạy PHP 8.2 (sắp hết hỗ trợ bảo mật
   cuối 2026) với 3 queue worker, 10 cron job và extension `redis`, `imagick`, `intl`. Viết một kế hoạch
   nâng lên 8.5 dạng checklist theo các bước của mục 9, ghi rõ với mỗi bước: làm gì, công cụ gì, tiêu
   chí "xong", và cách quay lại nếu hỏng.

## Đọc thêm

- File `UPGRADING` của từng nhánh trong php-src:
  [8.0](https://github.com/php/php-src/blob/PHP-8.0/UPGRADING),
  [8.1](https://github.com/php/php-src/blob/PHP-8.1/UPGRADING),
  [8.2](https://github.com/php/php-src/blob/PHP-8.2/UPGRADING),
  [8.3](https://github.com/php/php-src/blob/PHP-8.3/UPGRADING),
  [8.4](https://github.com/php/php-src/blob/PHP-8.4/UPGRADING),
  [8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING).
- Migration guide trong manual: [Appendices, Migrating from PHP 7.4.x to PHP 8.0.x](https://www.php.net/manual/en/migration80.php)
  và các trang tương ứng `migration81.php` tới `migration85.php`.
- Trang giới thiệu bản phát hành: [php.net/releases/8.0](https://www.php.net/releases/8.0/en.php) tới
  [php.net/releases/8.5](https://www.php.net/releases/8.5/en.php).
- RFC đã dẫn trong chương:
  [Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison),
  [Consistent type errors for internal functions](https://wiki.php.net/rfc/consistent_type_errors),
  [Reclassifying engine warnings](https://wiki.php.net/rfc/engine_warnings),
  [Deprecate passing null to non-nullable arguments of internal functions](https://wiki.php.net/rfc/deprecate_null_to_scalar_internal_arg),
  [Deprecate dynamic properties](https://wiki.php.net/rfc/deprecate_dynamic_properties),
  [Path to Saner Increment/Decrement operators](https://wiki.php.net/rfc/saner-inc-dec-operators),
  [Deprecate implicitly nullable parameter types](https://wiki.php.net/rfc/deprecate-implicitly-nullable-types),
  [Deprecations for PHP 8.1](https://wiki.php.net/rfc/deprecations_php_8_1),
  [8.4](https://wiki.php.net/rfc/deprecations_php_8_4),
  [8.5](https://wiki.php.net/rfc/deprecations_php_8_5),
  [Warnings for PHP 8.5](https://wiki.php.net/rfc/warnings-php-8-5).
- [Supported Versions](https://www.php.net/supported-versions.php) và
  [chính sách phát hành của PHP](https://github.com/php/policies/blob/main/release-process.rst).
- Tài liệu Rector: [getrector.com/documentation](https://getrector.com/documentation/) (mục cấu hình
  và "PHP Version").
- Tài liệu PHPStan: [Config Reference, mục phpVersion](https://phpstan.org/config-reference) và
  [phpstan-deprecation-rules](https://github.com/phpstan/phpstan-deprecation-rules).
- Composer: [lệnh `prohibits` (why-not)](https://getcomposer.org/doc/03-cli.md#prohibits-why-not) và
  [`config.platform`](https://getcomposer.org/doc/06-config.md#platform).
