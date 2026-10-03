# Chương 07. Toán tử và cấu trúc điều khiển

> [← Mục lục](README.md) · [← Chương 06: Mảng (array)](06-mang.md) · [Chương 08: Hàm →](08-ham.md)

**Bạn sẽ học được:**

- Biểu thức, toán tử, thứ tự ưu tiên và tính kết hợp là gì, để đọc một biểu thức dài mà không phải đoán.
- Dùng đúng từng nhóm toán tử: số học, gán, so sánh, logic, bitwise, chuỗi, `??` và `??=`, nullsafe
  `?->`, ternary và elvis `?:`, `instanceof`, `@`, pipe `|>` (PHP 8.5).
- Nhận ra các bẫy kinh điển: `and` khác `&&`, `.` đứng cạnh `+`, ternary lồng nhau, `??` đứng sau
  `.`, `&` đứng cạnh `==`, `@` che mất lỗi.
- Rẽ nhánh bằng `if`, `switch`, `match`, và hiểu vì sao `match` an toàn hơn `switch`.
- Lặp bằng `while`, `do-while`, `for`, `foreach`; điều khiển vòng lặp bằng `break N`, `continue N`;
  biết `goto` và cú pháp thay thế (`endif`, `endforeach`...).

**Cần biết trước:** [Chương 03](03-cu-phap-bien-hang.md) (biến, `isset`, `empty`),
[Chương 04](04-kieu-du-lieu.md) (kiểu dữ liệu, type juggling, bảng so sánh `==`),
[Chương 06](06-mang.md) (mảng, cần cho phần `foreach`).

Mọi ví dụ là file PHP hoàn chỉnh, chạy bằng `php ten-file.php`. Không cài PHP thì chạy bằng Docker,
đứng ở thư mục chứa file:

```bash
# chạy ở thư mục chứa file .php
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

Output ghi trong comment (`// in ra: ...`) đã được chạy thật trên PHP 8.5; chỗ nào PHP 8.4 khác thì
ghi rõ.

## 1. Biểu thức, toán tử và cách PHP nhóm chúng

### 1.1 Biểu thức và câu lệnh

Manual PHP định nghĩa *biểu thức* (expression) ngắn gọn: "bất cứ thứ gì có giá trị". `5` là biểu
thức có giá trị 5. `$a` là biểu thức có giá trị là giá trị đang nằm trong `$a`. `foo()` là biểu thức
có giá trị là thứ hàm trả về. `$a > 3` là biểu thức có giá trị `true` hoặc `false`.

*Câu lệnh* (statement) là một đơn vị thực thi: một lệnh kết thúc bằng dấu `;`, hoặc một khối như
`if (...) { ... }`. Câu lệnh thường chứa biểu thức bên trong: `echo $a + 1;` là câu lệnh, `$a + 1`
là biểu thức nằm trong nó.

Phân biệt hai thứ này quan trọng vì chỉ biểu thức mới đặt được vào chỗ cần một giá trị (vế phải của
phép gán, tham số hàm, `return`...). Trong PHP, phép gán cũng là biểu thức: `$a = 5` vừa gán, vừa có
giá trị 5.

```php
<?php
declare(strict_types=1);

$a = 5;                  // câu lệnh; bản thân "$a = 5" là biểu thức có giá trị 5
$b = ($a = 7) + 1;       // dùng giá trị của phép gán ngay trong một biểu thức khác
var_dump($a, $b);        // in ra: int(7) int(8)

$label = $a > 5 ? 'lớn' : 'nhỏ';   // ternary là biểu thức nên gán được
echo $label, "\n";                  // in ra: lớn
```

Trong chương này, những thứ là biểu thức: mọi toán tử (kể cả gán, ternary, `??`, `|>`) và
`match`. Những thứ là câu lệnh: `if`, `switch`, `while`, `do-while`, `for`, `foreach`, `break`,
`continue`, `goto`. Viết `$x = if ($a) { 1 } else { 2 };` là lỗi cú pháp; muốn "if có giá trị" thì
dùng ternary hoặc `match`.

Đối chiếu: Java cũng vậy (`if` là câu lệnh, có toán tử `? :`, và từ Java 14 có *switch expression*
giống `match`). Go không có toán tử ba ngôi; muốn chọn giá trị theo điều kiện phải viết `if` đầy đủ.

### 1.2 Toán tử và toán hạng

*Toán tử* (operator) là ký hiệu nhận một hay nhiều giá trị rồi sinh ra một giá trị mới. Các giá trị
nó nhận gọi là *toán hạng* (operand). Trong `3 + 4`, `+` là toán tử, `3` và `4` là toán hạng, và cả
cụm `3 + 4` lại là một biểu thức có giá trị 7.

Manual chia toán tử theo số toán hạng:

| Loại | Số toán hạng | Ví dụ |
|---|---|---|
| *Unary* (một ngôi) | 1 | `!$a`, `-$a`, `++$a`, `~$a`, `@foo()` |
| *Binary* (hai ngôi) | 2 | `$a + $b`, `$a . $b`, `$a && $b`, phần lớn toán tử thuộc nhóm này |
| *Ternary* (ba ngôi) | 3 | `$cond ? $x : $y`, toán tử ba ngôi duy nhất |

Bản đồ các nhóm toán tử trong chương:

| Nhóm | Toán tử | Mục |
|---|---|---|
| Số học, tăng giảm | `+ - * / % **`, `++ --` | [2](#2-toán-tử-số-học-và-tăng-giảm) |
| Gán | `=`, `+=`, `.=`, `??=`... | [3](#3-toán-tử-gán) |
| So sánh | `== != <> === !== < > <= >= <=>` | [4](#4-toán-tử-so-sánh-và-spaceship) |
| Logic | `&& \|\| ! and or xor` | [5](#5-toán-tử-logic) |
| Bitwise | `& \| ^ ~ << >>` | [6](#6-toán-tử-bitwise) |
| Chuỗi | `.`, `.=` | [7](#7-toán-tử-chuỗi) |
| Điều kiện và null | `? :`, `?:`, `??`, `??=`, `?->` | [8](#8-ternary-elvis-và-null-coalescing), [9](#9-nullsafe---và-instanceof) |
| Kiểu | `instanceof` | [9](#9-nullsafe---và-instanceof) |
| Kiểm soát lỗi | `@` | [10](#10-toán-tử-kiểm-soát-lỗi--và-toán-tử-backtick) |
| Pipe (8.5) | `\|>` | [11](#11-pipe-operator--php-85) |

Toán tử mảng (`+` hợp hai mảng, `==` và `===` so mảng) thuộc [Chương 06](06-mang.md); ép kiểu
`(int)`, `(string)`... thuộc [Chương 04](04-kieu-du-lieu.md); `new` và `clone` thuộc
[Chương 09](09-oop-co-ban.md).

### 1.3 Thứ tự ưu tiên (precedence)

Khi một biểu thức có nhiều toán tử, PHP phải quyết định toán tử nào "dính" vào toán hạng chặt hơn.
Đó là *thứ tự ưu tiên* (precedence). Giống toán ở trường: nhân chia trước, cộng trừ sau.

```php
<?php
declare(strict_types=1);

var_dump(1 + 5 * 3);     // in ra: int(16), vì * ưu tiên cao hơn +
var_dump((1 + 5) * 3);   // in ra: int(18), ngoặc ép nhóm theo ý mình
```

PHP đọc `1 + 5 * 3` thành một cây, toán tử ưu tiên cao nằm sâu hơn nên được tính trước:

```
        +              (1 + 5) * 3 thì ngược lại:        *
       / \                                              / \
      1   *                                            +   3
         / \                                          / \
        5   3                                        1   5
```

### 1.4 Tính kết hợp (associativity)

Khi hai toán tử có cùng mức ưu tiên đứng cạnh nhau, *tính kết hợp* (associativity) quyết định
nhóm từ trái hay từ phải:

- *Kết hợp trái* (left-associative): `1 - 2 - 3` nhóm thành `(1 - 2) - 3`, ra `-4`. Phần lớn toán tử
  hai ngôi là kết hợp trái.
- *Kết hợp phải* (right-associative): `$a = $b = 3` nhóm thành `$a = ($b = 3)`. Lũy thừa `**` cũng
  kết hợp phải: `2 ** 3 ** 2` là `2 ** 9`.
- *Không kết hợp* (non-associative): không được đứng cạnh nhau. `1 < 2 > 1` là lỗi cú pháp. Muốn
  thì phải thêm ngoặc.

```php
<?php
declare(strict_types=1);

var_dump(1 - 2 - 3);     // in ra: int(-4)
$a = $b = 3;
var_dump($a, $b);        // in ra: int(3) int(3)
var_dump(2 ** 3 ** 2);   // in ra: int(512), tức 2 ** 9 chứ không phải 8 ** 2
var_dump(1 <= 1 == 1);   // in ra: bool(true), hợp lệ vì <= và == khác mức ưu tiên

// var_dump(1 < 2 > 1);  // Parse error: syntax error, unexpected token ">"
// var_dump(1 == 1 == 1);// Parse error: syntax error, unexpected token "=="
```

`1 <= 1 == 1` hợp lệ vì `<=` ưu tiên cao hơn `==`, nên PHP nhóm thành `(1 <= 1) == 1`, tức
`true == 1`, ra `true`. Hợp lệ không có nghĩa là nên viết: người đọc code phải dừng lại nghĩ.

Bảng ưu tiên đầy đủ nằm ở [mục 12](#12-bảng-thứ-tự-ưu-tiên-và-các-bẫy-ưu-tiên), sau khi bạn đã biết
từng toán tử.

### 1.5 Ưu tiên không quyết định thứ tự tính

Đây là điểm nhiều người hiểu sai. Ưu tiên và tính kết hợp chỉ quyết định cách nhóm (cây ở trên),
không quyết định toán hạng nào được tính trước. Manual nói rõ: PHP (trong trường hợp chung)
không quy định thứ tự tính, và code dựa vào một thứ tự cụ thể có thể đổi hành vi giữa các phiên bản.
Ví dụ trong manual:

```php
<?php
declare(strict_types=1);

$a = 1;
echo $a + $a++, "\n";    // manual: có thể in 2 hoặc 3 (PHP 8.4 và 8.5 khi chạy thử in 3)

$i = 1;
$array = [];
$array[$i] = $i++;       // manual: có thể gán vào key 1 hoặc key 2 (chạy thử: key 2)
```

⚠️ Quy tắc an toàn: trong một biểu thức, đừng vừa sửa một biến (`++`, `--`, gán) vừa đọc lại
chính biến đó. Tách thành hai câu lệnh. Ngoại lệ có chủ đích là các toán tử *ngắt mạch* (`&&`, `||`,
`??`, `?:`): chúng luôn tính vế trái trước rồi mới quyết định có tính vế phải hay không (mục 5.2,
mục 8).

## 2. Toán tử số học và tăng giảm

### 2.1 Các phép toán cơ bản

| Toán tử | Tên | Ví dụ | Kết quả |
|---|---|---|---|
| `+$a` | *Identity*: đổi `$a` sang int hoặc float | `+"12"` | `12` |
| `-$a` | *Negation*: đổi dấu | `-"3.5"` | `-3.5` |
| `$a + $b` | Cộng | `7 + 2` | `9` |
| `$a - $b` | Trừ | `7 - 2` | `5` |
| `$a * $b` | Nhân | `7 * 2` | `14` |
| `$a / $b` | Chia | `7 / 2` | `3.5` |
| `$a % $b` | Chia lấy dư (*modulo*) | `7 % 2` | `1` |
| `$a ** $b` | Lũy thừa (*exponentiation*) | `7 ** 2` | `49` |

```php
<?php
declare(strict_types=1);

var_dump(7 + 2, 7 - 2, 7 * 2);   // in ra: int(9) int(5) int(14)
var_dump(7 / 2);                 // in ra: float(3.5)
var_dump(7 % 2, 7 ** 2);         // in ra: int(1) int(49)
var_dump(+"12", -"3.5");         // in ra: int(12) float(-3.5)
```

### 2.2 Phép chia: `/`, `intdiv()`, `fdiv()`

Theo manual, `/` trả về float, trừ khi hai toán hạng đều là int (hoặc numeric string đổi ra int)
và số bị chia chia hết cho số chia; khi đó kết quả là int.

```php
<?php
declare(strict_types=1);

var_dump(10 / 5);          // in ra: int(2)
var_dump(10 / 4);          // in ra: float(2.5)
var_dump("10" / "5");      // in ra: int(2), numeric string được đổi sang số trước
var_dump(10.0 / 5);        // in ra: float(2), có một float thì kết quả là float
var_dump(intdiv(7, 2));    // in ra: int(3), chia lấy phần nguyên
var_dump(intdiv(-7, 2));   // in ra: int(-3), cắt phần lẻ về phía 0 chứ không làm tròn xuống
```

Đối chiếu: trong Java và Go, `7 / 2` với hai int là phép chia nguyên, ra `3`. PHP ra `3.5`. Dịch
thuật toán từ Java/Go sang PHP mà giữ nguyên `/` là một nguồn bug; cần chia nguyên thì dùng
`intdiv()`.

**Chia cho 0.** Từ PHP 8.0, `/` cho 0 ném `DivisionByZeroError` (một `Error`, xem
[Chương 12](12-loi-exception.md)). Trước 8.0, `/` cho 0 chỉ phát warning rồi trả `INF`, `-INF` hoặc
`NAN`; còn `%` và `intdiv()` thì đã ném `DivisionByZeroError` từ PHP 7. RFC *Reclassifying engine
warnings* đưa `/` về cùng hành vi với `%`. Ai thật sự cần kết quả theo chuẩn IEEE 754 (vô cực,
NaN) thì dùng `fdiv()` (8.0).

```php
<?php
declare(strict_types=1);

try {
    echo 1 / 0;
} catch (DivisionByZeroError $e) {
    echo $e->getMessage(), "\n";       // in ra: Division by zero
}
try {
    echo 1 % 0;
} catch (DivisionByZeroError $e) {
    echo $e->getMessage(), "\n";       // in ra: Modulo by zero
}
try {
    echo intdiv(PHP_INT_MIN, -1);      // kết quả vượt PHP_INT_MAX
} catch (ArithmeticError $e) {
    echo $e->getMessage(), "\n";       // in ra: Division of PHP_INT_MIN by -1 is not an integer
}
var_dump(fdiv(1, 0), fdiv(-1, 0), fdiv(0, 0)); // in ra: float(INF) float(-INF) float(NAN)
```

⚠️ `1.5 / 0.0` cũng ném `DivisionByZeroError`; chia cho float `0.0` không "an toàn" hơn chia cho
int `0`.

### 2.3 Chia lấy dư `%` và `fmod()`

Manual ghi hai luật cho `%`:

1. Hai toán hạng được đổi sang int trước khi tính. Float có phần lẻ bị cắt, và từ PHP 8.1 việc
   cắt mất phần lẻ này phát `Deprecated: Implicit conversion from float 7.9 to int loses precision`.
   Cần chia lấy dư cho số thực thì dùng `fmod()`.
2. Kết quả cùng dấu với số bị chia (vế trái).

```php
<?php
declare(strict_types=1);

var_dump(5 % 3, 5 % -3, -5 % 3, -5 % -3); // in ra: int(2) int(2) int(-2) int(-2)
var_dump(fmod(7.5, 2));                    // in ra: float(1.5)

$i = -1;
var_dump($i % 3);                          // in ra: int(-1), không phải 2
var_dump((($i % 3) + 3) % 3);              // in ra: int(2), "modulo toán học" luôn không âm

$x = -3;
var_dump($x % 2 === 1);                    // in ra: bool(false), dù -3 là số lẻ
var_dump($x % 2 !== 0);                    // in ra: bool(true), cách kiểm số lẻ đúng
```

⚠️ Kiểm số lẻ bằng `$n % 2 === 1` sai với số âm vì `-3 % 2` là `-1`. Viết `$n % 2 !== 0`. Tương tự,
xoay vòng chỉ số mảng bằng `$i % $n` với `$i` có thể âm thì phải dùng công thức `(($i % $n) + $n) % $n`.

### 2.4 Lũy thừa `**`

`**` có từ PHP 5.6, tương đương hàm `pow()`. Ba điều cần nhớ:

- Kết hợp phải: `2 ** 3 ** 2` là `2 ** 9` (mục 1.4).
- Ưu tiên cao hơn dấu trừ một ngôi: `-2 ** 2` là `-(2 ** 2)`, ra `-4`. Muốn bình phương số âm
  thì viết `(-2) ** 2`.
- Kết quả là int nếu cơ số và số mũ là int, số mũ không âm và kết quả còn vừa int; ngược lại là
  float.

```php
<?php
declare(strict_types=1);

var_dump(2 ** 10, pow(2, 10));  // in ra: int(1024) int(1024)
var_dump(-2 ** 2, (-2) ** 2);   // in ra: int(-4) int(4)
var_dump(2 ** -1, 2 ** 0.5);    // in ra: float(0.5) float(1.4142135623730951)
var_dump(2 ** 62);              // in ra: int(4611686018427387904)
var_dump(2 ** 63);              // in ra: float(9.223372036854776E+18), vượt PHP_INT_MAX
var_dump(0 ** -1);              // PHP 8.4+: Deprecated: Power of base 0 and negative exponent is deprecated
                                // rồi in ra: float(INF)
```

`0 ** -1` bị deprecated từ PHP 8.4 (RFC *Raising zero to the power of negative number*). Cùng RFC
thêm hàm `fpow()` tính theo IEEE 754 cho ai cần kết quả `INF` một cách có chủ đích.

### 2.5 Kiểu của kết quả và toán hạng không phải số

Toán tử số học làm việc với int và float. Gặp kiểu khác, PHP đổi kiểu theo luật *type juggling*
([Chương 04](04-kieu-du-lieu.md)), tóm tắt cho riêng số học:

| Toán hạng | Hành vi | Ví dụ | Kết quả |
|---|---|---|---|
| int với int | Kết quả int; tràn thì thành float | `PHP_INT_MAX + 1` | `float(9.223372036854776E+18)` |
| Có ít nhất một float | Kết quả float | `1 + 1.0` | `float(2)` |
| *Numeric string* (chuỗi số) | Đổi sang int hoặc float tuỳ hình dạng | `"10" + 5`, `"1.5" + 1`, `" 10 " + 1` | `15`, `2.5`, `11` |
| *Leading-numeric string* (bắt đầu bằng số) | Dùng phần số ở đầu, kèm `Warning: A non-numeric value encountered` | `"10 pigs" + 1` | `11` |
| Chuỗi không phải số | `TypeError` từ 8.0 | `"abc" + 1` | `Unsupported operand types: string + int` |
| `null`, `bool` | Đổi im lặng: `null` thành 0, `true` thành 1 | `null + 1`, `true + 1` | `1`, `2` |
| array, object, resource | `TypeError` từ 8.0 | `[1] + 1` | `Unsupported operand types: array + int` |

Ngoại lệ duy nhất của dòng cuối: `array + array` là phép hợp mảng, vẫn hợp lệ
([Chương 06](06-mang.md)). Các dòng `TypeError` đến từ hai RFC của PHP 8.0: *Stricter type checks
for arithmetic/bitwise operators* (array, object, resource) và *Saner numeric strings* (chuỗi không
phải số).

```php
<?php
declare(strict_types=1);   // strict_types KHÔNG ảnh hưởng toán tử

var_dump("5" * "4");       // in ra: int(20)
var_dump(PHP_INT_MAX + 1); // in ra: float(9.223372036854776E+18)
var_dump(0.1 + 0.2);       // in ra: float(0.30000000000000004)

try {
    var_dump(-"abc");
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";   // in ra: Unsupported operand types: string * int
}
```

Dòng cuối có một chi tiết thú vị: thông báo lỗi nói `string * int` dù code không có dấu `*`. Lý do
là compiler của PHP dịch `-$a` thành `$a * -1` và `+$a` thành `$a * 1` (hàm
`zend_compile_unary_pm` trong `Zend/zend_compile.c`).

⚠️ `strict_types=1` chỉ áp cho tham số, giá trị trả về và property có khai báo kiểu, không áp cho
toán tử. `"5" * "4"` vẫn ra `20` trong file strict.

⚠️ Float có sai số: `0.1 + 0.2 === 0.3` là `false`. Đừng dùng float cho tiền; dùng int theo đơn vị
nhỏ nhất (đồng, cent) hoặc bcmath. Chi tiết ở [Chương 04](04-kieu-du-lieu.md).

### 2.6 Tăng và giảm: `++` và `--`

`++` cộng 1, `--` trừ 1 vào biến. Mỗi toán tử có hai dạng, khác nhau ở giá trị của biểu thức:

| Dạng | Tên | Tác dụng |
|---|---|---|
| `++$a` | *Pre-increment* (tiền tố) | Tăng `$a` trước, rồi trả giá trị mới |
| `$a++` | *Post-increment* (hậu tố) | Trả giá trị cũ, rồi mới tăng `$a` |
| `--$a` | *Pre-decrement* | Giảm trước, trả giá trị mới |
| `$a--` | *Post-decrement* | Trả giá trị cũ, rồi mới giảm |

```php
<?php
declare(strict_types=1);

$a = 5;
echo $a++, ' ', $a, "\n";   // in ra: 5 6
$a = 5;
echo ++$a, ' ', $a, "\n";   // in ra: 6 6
```

Với int và float, `++`/`--` đơn giản. Với kiểu khác, hành vi có nhiều ngóc ngách (đã chạy thử trên
8.3, 8.4, 8.5):

| Giá trị ban đầu | Sau `++` | Sau `--` |
|---|---|---|
| `null` | `1` | Vẫn `null`, kèm Warning (từ 8.3) |
| `true` / `false` | Không đổi, kèm Warning (từ 8.3) | Không đổi, kèm Warning (từ 8.3) |
| `PHP_INT_MAX` | float | |
| `"9"` (numeric string) | `int(10)` | `int(8)` |
| `""` | `"1"`, kèm Deprecated (từ 8.3) | `int(-1)`, kèm Deprecated (từ 8.3) |
| `"a"`, `"Az"`, `"zz"` | `"b"`, `"Ba"`, `"aaa"` (kiểu Perl), Deprecated từ 8.5 | Không đổi, kèm Deprecated (từ 8.3) |

Dòng cuối là tính năng cũ "tăng chuỗi kiểu Perl": `"Az"++` thành `"Ba"`, `"zz"++` thành `"aaa"`.
RFC *Path to Saner Increment/Decrement operators* (8.3) thêm hàm `str_increment()` và
`str_decrement()` để thay, và từ 8.5 mọi phép `++` trên chuỗi không phải số đều phát
`Deprecated: Increment on non-numeric string is deprecated, use str_increment() instead`.

```php
<?php
declare(strict_types=1);

var_dump(str_increment('Az'), str_increment('zz')); // in ra: string(2) "Ba" string(3) "aaa"
var_dump(str_decrement('Ba'));                      // in ra: string(2) "Az"
```

⚠️ Thông điệp của warning với `bool` và `null` ("this will change in the next major version of
PHP") báo trước rằng hành vi sẽ đổi ở bản lớn sau. Đừng viết code dựa vào việc `$flag++` không làm gì.

Đối chiếu: Go coi `i++` là câu lệnh, không phải biểu thức, nên không viết được `x := i++` và không
bao giờ phải phân biệt tiền tố với hậu tố. Thói quen tốt trong PHP cũng vậy: dùng `$i++` như một câu
lệnh riêng, đừng nhét vào giữa biểu thức khác (nhớ mục 1.5).

## 3. Toán tử gán

### 3.1 `=` nghĩa là "nhận giá trị", không phải "bằng"

Manual nhắc: đừng đọc `=` là "bằng". `$a = 3` nghĩa là "`$a` nhận giá trị của biểu thức bên phải".
So sánh bằng là `==` hoặc `===` (mục 4).

Như mục 1.1 đã nói, phép gán là một biểu thức, và giá trị của nó là giá trị vừa gán. Vì `=` kết hợp
phải, `$a = $b = 0` gán `0` cho `$b` trước, rồi gán kết quả (cũng là `0`) cho `$a`.

```php
<?php
declare(strict_types=1);

$a = ($b = 4) + 5;   // ví dụ trong manual
var_dump($a, $b);    // in ra: int(9) int(4)
```

Gán thường là *gán theo giá trị* (assignment by value): bên phải được chép sang bên trái, sửa biến
này không ảnh hưởng biến kia. Với array, PHP dùng *copy-on-write* nên việc "chép" rẻ cho tới khi một
bên bị sửa ([Chương 06](06-mang.md), [Chương 19](19-ben-trong-engine.md)). Hai trường hợp khác:

- **Object**: biến object không chứa bản thân object mà chứa một *handle* (mã định danh) trỏ tới
  object. Gán chỉ chép handle, nên hai biến cùng trỏ một object. Muốn bản sao thật thì `clone`
  ([Chương 09](09-oop-co-ban.md)).
- **Gán tham chiếu** `$b = &$a`: hai tên cùng trỏ một vùng dữ liệu, sửa bên nào bên kia cũng thấy
  ([Chương 03](03-cu-phap-bien-hang.md)).

### 3.2 Gán kết hợp

Mọi toán tử hai ngôi số học, bitwise và chuỗi đều có dạng gán kết hợp: `$a op= $b` tương đương
`$a = $a op $b`.

| Nhóm | Toán tử |
|---|---|
| Số học | `+=` `-=` `*=` `/=` `%=` `**=` |
| Bitwise | `&=` `\|=` `^=` `<<=` `>>=` |
| Chuỗi | `.=` |
| Null coalescing | `??=` (PHP 7.4, mục 8.4) |

```php
<?php
declare(strict_types=1);

$n = 10;
$n += 5;            // 15
$n -= 3;            // 12
$n *= 2;            // 24
$n /= 4;            // 6 (chia hết nên vẫn là int)
var_dump($n);       // in ra: int(6)

$s = 'Hello';
$s .= ', PHP';
var_dump($s);       // in ra: string(10) "Hello, PHP"
```

⚠️ Gán kết hợp đọc biến trước khi ghi. Biến chưa khởi tạo sẽ phát warning:

```php
<?php
declare(strict_types=1);

$total += 10;       // Warning: Undefined variable $total
var_dump($total);   // in ra: int(10), null được coi là 0
```

Luôn khởi tạo biến cộng dồn (`$total = 0;`) trước vòng lặp.

### 3.3 Gán bên trong điều kiện

Vì phép gán có giá trị, có thể gán ngay trong điều kiện của `if`/`while`. Đây là mẫu chuẩn khi đọc
dần dữ liệu:

```php
<?php
declare(strict_types=1);

$queue = ['job1', 'job2'];
while (($job = array_shift($queue)) !== null) {   // gán rồi so kết quả của phép gán
    echo $job, "\n";                               // in ra: job1, rồi job2
}
```

Cặp ngoặc quanh `$job = array_shift($queue)` là bắt buộc: `!==` ưu tiên cao hơn `=`, thiếu ngoặc thì
PHP hiểu thành `$job = (array_shift($queue) !== null)` và `$job` nhận `true`/`false`.

⚠️ Bẫy kinh điển là gõ nhầm `=` thay cho `==`:

```php
<?php
declare(strict_types=1);

$x = 0;
if ($x = 5) {                         // GÁN 5 cho $x, giá trị biểu thức là 5, truthy
    echo "luôn vào đây, x = $x\n";    // in ra: luôn vào đây, x = 5
}
```

Code này chạy không báo lỗi gì. Một số người viết kiểu *Yoda* (`if (5 == $x)`) để gõ nhầm thành
`5 = $x` thì báo lỗi cú pháp. Cách hiện đại hơn là để công cụ kiểm tra code bắt lỗi này, ví dụ sniff
`Generic.CodeAnalysis.AssignmentInCondition` của PHP_CodeSniffer phát hiện phép gán nằm trong điều
kiện ([Chương 21](21-chat-luong-code.md)). Khi cố ý gán trong điều kiện như ví dụ `while` ở trên, bọc
phép gán trong ngoặc và so tường minh với giá trị cụ thể để người đọc biết đó là chủ đích.

### 3.4 Gán phân rã (destructuring)

`[$a, $b] = $mang` gán từng phần tử vào từng biến. Mẹo hay dùng là đổi chỗ hai biến không cần biến
tạm. Chi tiết (bỏ qua phần tử, dùng key, `list()`) ở [Chương 06](06-mang.md).

```php
<?php
declare(strict_types=1);

$p = 1;
$q = 2;
[$p, $q] = [$q, $p];
var_dump($p, $q);   // in ra: int(2) int(1)
```

## 4. Toán tử so sánh và spaceship

### 4.1 Bảng toán tử so sánh

| Toán tử | Tên | `true` khi |
|---|---|---|
| `$a == $b` | *Equal* | Bằng nhau sau khi đổi kiểu (type juggling) |
| `$a === $b` | *Identical* | Bằng nhau và cùng kiểu, không đổi kiểu gì |
| `$a != $b`, `$a <> $b` | *Not equal* | Khác nhau sau khi đổi kiểu (`<>` là tên khác của `!=`) |
| `$a !== $b` | *Not identical* | Khác giá trị hoặc khác kiểu |
| `$a < $b`, `$a > $b` | Nhỏ hơn, lớn hơn | |
| `$a <= $b`, `$a >= $b` | Nhỏ hơn hoặc bằng, lớn hơn hoặc bằng | |
| `$a <=> $b` | *Spaceship* | Trả về int âm, 0, hoặc dương (mục 4.4) |

Mọi toán tử trong bảng (trừ `<=>`) trả về `bool`.

### 4.2 `==` và `===`

`===` đơn giản: khác kiểu là khác, cùng kiểu thì so giá trị. `==` thì đổi hai vế về một kiểu chung
theo một bảng luật rồi mới so. Bảng luật đầy đủ và các ví dụ PHP 7 so với PHP 8 nằm ở
[Chương 04](04-kieu-du-lieu.md); ở đây chỉ nhắc những điểm phải thuộc:

- Hai vế là số, hoặc một vế là số và vế kia là *numeric string*, hoặc cả hai là numeric string: so
  như số. Vì vậy `"1" == "01"`, `"10" == "1e1"`, `100 == "1e2"` đều là `true`.
- Từ PHP 8.0 (RFC *Saner string to number comparisons*): số so với chuỗi không phải numeric
  string thì đổi số thành chuỗi rồi so hai chuỗi. `0 == "a"` thành `false` (PHP 7 là `true`).
- Có một vế là `bool`, hoặc một vế là `null` còn vế kia không phải string: đổi cả hai vế về bool.
  `null == false`, `null == 0`, `[] == false` đều là `true`. Riêng `null` so với string thì `null`
  được đổi thành `""` rồi so chuỗi: `null == ""` là `true`, `null == "0"` là `false`.

```php
<?php
declare(strict_types=1);   // không ảnh hưởng ==

var_dump(1 == 1.0, 1 === 1.0);     // in ra: bool(true) bool(false)
var_dump("1" == 1, "1" === 1);     // in ra: bool(true) bool(false)
var_dump("10" == "1e1");           // in ra: bool(true), hai numeric string so như số
var_dump(0 == "a");                // in ra: bool(false) ở PHP 8 (PHP 7: true)
var_dump(null == false, [] == false); // in ra: bool(true) bool(true)
var_dump("abc" == "ABC");          // in ra: bool(false), so chuỗi phân biệt hoa thường
```

Với array: `==` là cùng các cặp key/value (không cần cùng thứ tự), `===` thì thêm điều kiện cùng thứ
tự và cùng kiểu. Với object: `==` là cùng class và các property bằng nhau theo `==`; `===` là **cùng
một instance**.

```php
<?php
declare(strict_types=1);

var_dump([1, 2] == [1 => 2, 0 => 1]);   // in ra: bool(true)
var_dump([1, 2] === [1 => 2, 0 => 1]);  // in ra: bool(false), khác thứ tự

final class P { public function __construct(public int $x) {} }
$o1 = new P(1);
$o2 = new P(1);
$o3 = $o1;
var_dump($o1 == $o2, $o1 === $o2, $o1 === $o3); // in ra: bool(true) bool(false) bool(true)
```

Lời khuyên của chính manual: dùng `===` và `!==` trong hầu hết trường hợp. Chỉ dùng `==` khi bạn
thật sự muốn đổi kiểu và biết rõ luật.

⚠️ Một số chỗ so bằng `==` một cách ngầm: `in_array()` và `array_search()` khi không truyền tham số
`strict`, và `switch` (mục 14). Chi tiết ở [Chương 04](04-kieu-du-lieu.md) và
[Chương 06](06-mang.md).

### 4.3 So sánh thứ tự với chuỗi, null, bool, mảng

`<`, `>`, `<=`, `>=` dùng cùng bộ luật đổi kiểu với `==`. Manual liệt kê luật theo thứ tự ưu tiên, gặp
dòng nào khớp trước thì dùng dòng đó (rút gọn):

| Vế 1 | Vế 2 | Cách so |
|---|---|---|
| `null` hoặc string | string | Đổi `null` thành `""`, rồi so số (nếu cả hai là numeric string) hoặc so từng byte |
| `bool` hoặc `null` | bất kỳ | Đổi cả hai về bool, `false < true` |
| object | object | Khác class thì không so được; cùng class thì so từng property |
| string, int, float | string, int, float | So như số (với chuỗi: chỉ khi là numeric string, mục 4.2) |
| array | array | Ít phần tử hơn là nhỏ hơn; cùng số phần tử thì so từng key |
| object | bất kỳ | Object luôn lớn hơn |
| array | bất kỳ | Array luôn lớn hơn |

```php
<?php
declare(strict_types=1);

// Chuỗi với chuỗi: so từng byte (giống strcmp), không theo bảng chữ cái của ngôn ngữ nào
var_dump("apple" < "banana");   // in ra: bool(true)
var_dump("Zebra" < "apple");    // in ra: bool(true), byte 'Z' (90) nhỏ hơn byte 'a' (97)
var_dump("a" < "aa");           // in ra: bool(true)
var_dump("10" < "9");           // in ra: bool(false), hai numeric string so như số: 10 < 9 sai
var_dump("10" < "9a");          // in ra: bool(true), "9a" không phải số nên so từng byte: '1' < '9'
var_dump("Ăn" < "Bánh");        // in ra: bool(false), byte đầu của "Ă" trong UTF-8 lớn hơn 'B'

// null và bool: đổi cả hai về bool
var_dump(100 < true);           // in ra: bool(false), vì true < true sai
var_dump(null < -1);            // in ra: bool(true), vì false < true
var_dump(min(-100, -10, null, 10, 100)); // in ra: NULL (ví dụ trong manual)
```

⚠️ Sắp xếp chuỗi tiếng Việt bằng `<` hoặc `sort()` cho thứ tự theo byte UTF-8, không đúng thứ tự
chữ cái tiếng Việt. Cần đúng thì dùng `Collator` của extension intl ([Chương 05](05-chuoi.md)).

⚠️ Manual ghi rõ: kết quả so sánh hai giá trị *không so được* (incomparable), ví dụ hai object khác
class, hay hai array có key không khớp, là không xác định. Đừng viết code dựa vào nó. Còn khi so
một cấu trúc có chứa chính nó (array hay object tự tham chiếu), từ PHP 8.4 PHP ném `Error` thay vì
fatal error.

### 4.4 Spaceship `<=>`

`<=>` (PHP 7.0) gộp ba phép so sánh làm một. RFC định nghĩa: trả `0` nếu hai vế bằng nhau, `1` nếu vế
trái lớn hơn, `-1` nếu vế phải lớn hơn, theo đúng luật của `<`, `==`, `>`. Manual thì chỉ cam kết "số
nguyên nhỏ hơn, bằng, hoặc lớn hơn 0", nên khi dùng kết quả hãy so với 0 (`< 0`, `> 0`), đừng so
`=== -1`.

Công dụng chính: viết hàm so sánh cho `usort()`, `uasort()`, `uksort()`. Hàm so sánh phải trả số âm
nếu `$a` đứng trước `$b`, 0 nếu ngang nhau, số dương nếu `$a` đứng sau; đúng thứ `<=>` trả về.

```php
<?php
declare(strict_types=1);

var_dump(1 <=> 2, 2 <=> 2, 3 <=> 2);  // in ra: int(-1) int(0) int(1)
var_dump("a" <=> "b");                // in ra: int(-1)
var_dump([1, 2, 3] <=> [1, 2, 4]);    // in ra: int(-1), so từng phần tử
var_dump([1, 2] <=> [1, 2, 3]);       // in ra: int(-1), ít phần tử hơn là nhỏ hơn

$people = [
    ['name' => 'Chi',  'age' => 30],
    ['name' => 'An',   'age' => 25],
    ['name' => 'Bình', 'age' => 30],
];

// Tăng dần theo tuổi
usort($people, fn(array $a, array $b): int => $a['age'] <=> $b['age']);
echo implode(', ', array_column($people, 'name')), "\n";   // in ra: An, Chi, Bình

// Nhiều tiêu chí: tuổi GIẢM dần (đảo $a, $b), rồi tên TĂNG dần
usort($people, fn(array $a, array $b): int
    => [$b['age'], $a['name']] <=> [$a['age'], $b['name']]);
echo implode(', ', array_column($people, 'name')), "\n";   // in ra: Bình, Chi, An
```

Mẹo nhiều tiêu chí dựa trên luật so mảng: hai mảng cùng số phần tử thì so lần lượt từng phần tử,
gặp phần tử khác nhau đầu tiên là có kết quả. Muốn giảm dần ở tiêu chí nào thì đổi chỗ `$a` và `$b`
ở đúng vị trí đó.

Ở dòng in đầu, Chi và Bình cùng 30 tuổi nên giữ nguyên thứ tự ban đầu (Chi trước Bình). Đó là vì từ
PHP 8.0 các hàm sắp xếp là *stable* ([Chương 06](06-mang.md)).

### 4.5 So sánh số thực

Float lưu theo chuẩn IEEE 754 nên có sai số. Manual cảnh báo: đừng kiểm tra hai float có bằng nhau
không.

```php
<?php
declare(strict_types=1);

var_dump(0.1 + 0.2 == 0.3);                                   // in ra: bool(false)
var_dump(abs((0.1 + 0.2) - 0.3) < PHP_FLOAT_EPSILON);         // in ra: bool(true)
var_dump(NAN == NAN);                                         // in ra: bool(false), NAN không bằng gì cả
```

So bằng sai số chỉ là cách chữa cháy. Với tiền, dùng int theo đơn vị nhỏ nhất hoặc bcmath
([Chương 04](04-kieu-du-lieu.md)).

Đối chiếu: Java không có so sánh lỏng giữa hai kiểu khác nhau, nhưng có bẫy riêng: `==` với object so
*reference* (`new String("a") == new String("a")` là `false`), phải dùng `equals()`. Go không cho so
hai giá trị khác kiểu, lỗi ngay lúc compile. PHP gần JavaScript hơn: có cả `==` lỏng và `===` chặt.

## 5. Toán tử logic

### 5.1 Sáu toán tử logic

| Toán tử | Tên | `true` khi |
|---|---|---|
| `$a && $b`, `$a and $b` | Và (*and*) | Cả hai đều true |
| `$a \|\| $b`, `$a or $b` | Hoặc (*or*) | Ít nhất một vế true |
| `$a xor $b` | Hoặc loại trừ (*exclusive or*) | Đúng một vế true, không phải cả hai |
| `!$a` | Phủ định (*not*) | `$a` không true |

Toán hạng được đổi sang bool trước khi tính (luật *truthy/falsy*: `0`, `0.0`, `""`, `"0"`, `[]`,
`null` là false, xem [Chương 04](04-kieu-du-lieu.md)). Kết quả luôn là bool.

```php
<?php
declare(strict_types=1);

var_dump('a' || 'b');   // in ra: bool(true), không phải 'a'
var_dump(0 || 'b');     // in ra: bool(true)
var_dump('' && 'x');    // in ra: bool(false)
var_dump('a' ?: 'b');   // in ra: string(1) "a", muốn lấy giá trị thì dùng ?: (mục 8.2)
```

Đối chiếu: trong JavaScript và Python, `a || b` trả về một trong hai toán hạng nên hay dùng để lấy
giá trị mặc định (`name || 'khách'`). Trong PHP, `||` chỉ trả `true`/`false`; muốn giá trị mặc định
thì dùng `?:` hoặc `??` (mục 8).

### 5.2 Ngắt mạch (short-circuit evaluation)

`&&` và `||` (cùng `and`, `or`) tính vế trái trước. Nếu vế trái đã đủ quyết định kết quả thì
**vế phải không được tính**:

- `false && X`: chắc chắn false, bỏ qua X.
- `true || X`: chắc chắn true, bỏ qua X.

```php
<?php
declare(strict_types=1);

function loud(string $name, bool $v): bool
{
    echo "[$name]";
    return $v;
}

var_dump(loud('A', false) && loud('B', true));  // in ra: [A]bool(false), B không chạy
var_dump(loud('A', true) || loud('B', true));   // in ra: [A]bool(true), B không chạy
var_dump(loud('A', true) && loud('B', false));  // in ra: [A][B]bool(false)
```

Ngắt mạch là thứ làm cho mẫu "kiểm tra trước, dùng sau" an toàn:

```php
<?php
declare(strict_types=1);

$user = null;
// Nếu $user là null thì vế phải không chạy, nên không có lỗi "Call to a member function on null"
var_dump($user !== null && $user->isAdmin());   // in ra: bool(false)
```

⚠️ Đừng đặt việc **bắt buộc phải chạy** (ghi log, tăng bộ đếm, gửi mail) ở vế phải của `&&`/`||`:
nó sẽ bị bỏ qua lúc nào không hay. `xor` thì không ngắt mạch được, vì luôn cần biết cả hai vế.

### 5.3 `and`/`or` khác `&&`/`||` ở thứ tự ưu tiên

`and` và `or` cho cùng kết quả logic với `&&` và `||`. Khác biệt duy nhất, và là bẫy lớn: `and`, `or`,
`xor` có ưu tiên **thấp hơn cả phép gán `=`**, còn `&&`, `||` cao hơn `=`. Ví dụ trong manual:

```php
<?php
declare(strict_types=1);

$e = false || true;   // = ($e = (false || true))
$f = false or true;   // = (($f = false) or true): gán false cho $f trước!
var_dump($e, $f);     // in ra: bool(true) bool(false)

$g = true && false;   // = ($g = (true && false))
$h = true and false;  // = (($h = true) and false)
var_dump($g, $h);     // in ra: bool(false) bool(true)

$x = true xor true;   // = (($x = true) xor true)
var_dump($x);         // in ra: bool(true), dù true xor true là false
var_dump(true xor true); // in ra: bool(false)
```

Cây nhóm của `$f = false or true`:

```
           or                    ($f nhận false, sau đó kết quả của "or"
          /  \                    là true nhưng bị vứt đi)
       (=)    true
      /   \
    $f    false
```

Mẫu `$fh = fopen($path, 'r') or die('Không mở được file');` trong code PHP cũ chạy đúng **chính
nhờ** `or` thấp hơn `=`: gán trước, nếu giá trị gán là falsy thì chạy `die()`. Code hiện đại nên
viết tường minh bằng `if` và exception ([Chương 12](12-loi-exception.md)).

Quy tắc thực hành: luôn dùng `&&`, `||`, `!`. PHP-CS-Fixer có rule `logical_operators` tự đổi `and`/
`or` thành `&&`/`||` (rule này được đánh dấu *risky*, vì phải kiểm lại chỗ nào cố tình dùng ưu tiên
thấp). Cần `xor` thì luôn bọc ngoặc: `$ok = ($a xor $b);`.

### 5.4 `!` và thứ tự ưu tiên

`!` là toán tử một ngôi có ưu tiên cao hơn các phép so sánh. Vì vậy `!$a == $b` là `(!$a) == $b`,
không phải `!($a == $b)`:

```php
<?php
declare(strict_types=1);

$a = 1;
$b = 2;
var_dump(!$a == $b);     // in ra: bool(false), tức (!1) == 2, tức false == 2
var_dump(!($a == $b));   // in ra: bool(true), đúng ý "a không bằng b"
var_dump($a !== $b);     // in ra: bool(true), cách viết rõ nhất
```

Có một ngoại lệ dễ chịu: `!$obj instanceof Foo` được nhóm thành `!($obj instanceof Foo)` vì
`instanceof` ưu tiên cao hơn `!` (mục 9.2).

Đối chiếu: Java và Go chỉ có `&&`, `||`, `!` với cùng luật ngắt mạch, và chỉ chấp nhận toán hạng kiểu
`boolean`/`bool`; `if (1)` hay `"a" && x` là lỗi compile. PHP thì đổi mọi thứ sang bool, nên phải nhớ
luật truthy/falsy.

## 6. Toán tử bitwise

### 6.1 Làm việc trên từng bit

Một số int được lưu dưới dạng dãy bit (trên máy 64-bit là 64 bit). Toán tử *bitwise* thao tác trên
từng bit ở cùng vị trí của hai số. Viết số ở dạng nhị phân bằng tiền tố `0b` cho dễ nhìn
([Chương 04](04-kieu-du-lieu.md)).

| Toán tử | Tên | Bit kết quả bằng 1 khi |
|---|---|---|
| `$a & $b` | *And* | Bit đó bằng 1 ở cả hai số |
| `$a \| $b` | *Or* | Bit đó bằng 1 ở ít nhất một số |
| `$a ^ $b` | *Xor* | Bit đó bằng 1 ở đúng một số |
| `~$a` | *Not* | Đảo mọi bit của `$a` |
| `$a << $b` | Dịch trái | Dịch bit của `$a` sang trái `$b` vị trí (mỗi bước như nhân 2) |
| `$a >> $b` | Dịch phải | Dịch sang phải `$b` vị trí (mỗi bước như chia 2) |

```
    0101  (5)          0101  (5)          0101  (5)
  & 0011  (3)        | 0011  (3)        ^ 0011  (3)
  ------             ------             ------
    0001  (1)          0111  (7)          0110  (6)
```

```php
<?php
declare(strict_types=1);

var_dump(5 & 3, 5 | 3, 5 ^ 3);   // in ra: int(1) int(7) int(6)
var_dump(~5);                    // in ra: int(-6), đảo cả bit dấu (bù hai: ~x = -x - 1)
var_dump(1 << 3, 16 >> 2);       // in ra: int(8) int(4)
var_dump(-16 >> 2);              // in ra: int(-4), dịch phải giữ dấu
var_dump(1 << 63);               // in ra: int(-9223372036854775808), bit 1 rơi vào bit dấu
var_dump(1 << 64);               // in ra: int(0), mọi bit bị đẩy ra ngoài

try {
    var_dump(1 << -1);
} catch (ArithmeticError $e) {
    echo $e->getMessage(), "\n"; // in ra: Bit shift by negative number
}
```

Manual mô tả phép dịch của PHP là dịch *số học* (arithmetic shift): bit bị đẩy ra khỏi hai đầu thì
mất; dịch trái điền 0 vào bên phải và có thể làm đổi dấu; dịch phải chép bit dấu vào bên trái nên giữ
nguyên dấu. Cần thao tác bit trên số lớn hơn `PHP_INT_MAX` thì dùng extension gmp.

### 6.2 Ứng dụng: cờ (flags) và bitmask

Công dụng phổ biến nhất của bitwise trong PHP là *cờ* (flag): mỗi tùy chọn chiếm một bit, gộp nhiều
tùy chọn bằng `|`, kiểm tra bằng `&`. Chính PHP dùng kiểu này cho rất nhiều hằng số:

```php
<?php
declare(strict_types=1);

// Gộp hai tùy chọn của json_encode bằng |
echo json_encode(['tên' => 'Việt', 'url' => 'a/b'], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), "\n";
// in ra: {"tên":"Việt","url":"a/b"}

// Mọi mức lỗi trừ deprecated: bật hết rồi tắt một bit bằng & ~
error_reporting(E_ALL & ~E_DEPRECATED);
```

Tự định nghĩa cờ cho bài toán của mình (ví dụ quyền của một user, lưu gọn trong một cột int của DB):

```php
<?php
declare(strict_types=1);

const PERM_READ   = 1 << 0;   // 0b001 = 1
const PERM_WRITE  = 1 << 1;   // 0b010 = 2
const PERM_DELETE = 1 << 2;   // 0b100 = 4

$perms = PERM_READ | PERM_WRITE;          // bật hai cờ: 0b011
var_dump(($perms & PERM_WRITE) !== 0);    // in ra: bool(true), có quyền ghi
var_dump(($perms & PERM_DELETE) !== 0);   // in ra: bool(false), không có quyền xoá

$perms |= PERM_DELETE;                    // bật cờ:  0b111
$perms &= ~PERM_WRITE;                    // tắt cờ:  0b101
$perms ^= PERM_READ;                      // đảo cờ:  0b100
printf("%03b\n", $perms);                 // in ra: 100
```

Bốn thao tác cần thuộc: bật `|=`, tắt `&= ~`, đảo `^=`, kiểm tra `($x & FLAG) !== 0`.

Bitmask gọn và nhanh, nhưng khó đọc khi debug (nhìn số `5` không biết là quyền gì). Trong code nghiệp
vụ, một mảng enum hay vài cột bool thường dễ bảo trì hơn; bitmask hợp khi cần lưu gọn hoặc khi làm
việc với API vốn đã dùng cờ.

### 6.3 Cạm bẫy của bitwise

⚠️ **Ưu tiên của `&`, `|`, `^` thấp hơn `==`.** Đây là bẫy kinh điển kế thừa từ C:

```php
<?php
declare(strict_types=1);

const PERM_WRITE = 2;
$perms = 4;
var_dump(PERM_WRITE & $perms == PERM_WRITE);    // in ra: int(0)
// PHP hiểu là PERM_WRITE & ($perms == PERM_WRITE), tức 2 & false, tức 2 & 0
var_dump((PERM_WRITE & $perms) == PERM_WRITE);  // in ra: bool(false), đúng ý
```

Luôn bọc ngoặc quanh phép bitwise khi đứng cạnh phép so sánh. Manual trang Bitwise cũng nhắc điều
này.

⚠️ **Bitwise trên chuỗi.** Nếu cả hai toán hạng của `&`, `|`, `^` là string, PHP tính trên từng
byte và trả về string, không phải int. Chỉ cần một vế không phải string thì cả hai được đổi sang
int.

```php
<?php
declare(strict_types=1);

var_dump(2 ^ "3");       // in ra: int(1), "3" được đổi sang int
var_dump("AB" | "  ");   // in ra: string(2) "ab", OR từng byte với dấu cách (0x20)
```

Dữ liệu từ form hay query string luôn là string, nên `$_GET['flags'] & $_GET['mask']` sẽ cho ra một
chuỗi byte khó hiểu thay vì một số. Ép kiểu tường minh `(int)` trước khi làm bitwise.

⚠️ Float bị đổi sang int (cắt phần lẻ, kèm Deprecated nếu mất phần lẻ), chuỗi không phải số thì
`TypeError` (`Unsupported operand types: string & int`), giống luật của toán tử số học ở mục 2.5.

## 7. Toán tử chuỗi

### 7.1 Nối chuỗi `.` và `.=`

PHP có đúng hai toán tử chuỗi: `.` nối hai chuỗi thành chuỗi mới, `.=` nối thêm vào cuối biến. Khác
với JavaScript hay Java, PHP không dùng `+` để nối chuỗi; `+` luôn là phép cộng số.

```php
<?php
declare(strict_types=1);

$a = 'Hello ';
$b = $a . 'World!';
var_dump($b);            // in ra: string(12) "Hello World!"

$s = '';
foreach (['a', 'b', 'c'] as $p) {
    $s .= $p . ',';
}
var_dump($s);                          // in ra: string(6) "a,b,c,"
var_dump(implode(',', ['a', 'b', 'c'])); // in ra: string(5) "a,b,c", gọn hơn khi cần dấu phân cách
```

`.` đổi hai toán hạng sang string trước khi nối, theo luật đổi sang string của
[Chương 04](04-kieu-du-lieu.md): int và float thành chữ số, `true` thành `"1"`, `false` và `null`
thành `""`. Array thì thành `"Array"` kèm `Warning: Array to string conversion`; object không có
`__toString()` thì ném `Error`.

```php
<?php
declare(strict_types=1);   // không ảnh hưởng toán tử .

var_dump(1 . 2);           // in ra: string(2) "12" (cần dấu cách: 1.2 là số thực)
var_dump(true . '|', false . '|', null . '|'); // in ra: string(2) "1|" string(1) "|" string(1) "|"
```

Muốn chèn biến vào chuỗi mà không phải nối từng đoạn thì dùng *interpolation* (`"Xin chào {$name}"`),
`sprintf()`, heredoc ([Chương 05](05-chuoi.md)).

### 7.2 PHP 8 đổi ưu tiên của `.`

Trước PHP 8.0, `.`, `+` và `-` cùng mức ưu tiên và tính từ trái sang phải. RFC *Change the precedence
of the concatenation operator* (thực hiện ở 8.0) hạ `.` xuống dưới `+`, `-` và cả `<<`, `>>`.
Bây giờ phép cộng trừ luôn được tính trước phép nối:

```php
<?php
declare(strict_types=1);

$x = 4;
echo "x trừ một bằng " . $x - 1 . "\n";   // in ra: x trừ một bằng 3
echo "Tổng: " . 1 + 2, "\n";              // in ra: Tổng: 3
var_dump("5" . 4 + 1);                    // in ra: string(2) "55", tức "5" . (4 + 1)
```

Ở PHP 7, dòng đầu được nhóm thành `("x trừ một bằng " . $x) - 1`: lấy một chuỗi không phải số trừ đi
1, và manual ghi output của PHP 7 là `-1` cộng phần đuôi chuỗi. PHP 7.4 đã phát deprecation cho kiểu
viết dựa vào thứ tự này trước khi 8.0 đổi hẳn. Ở PHP 8, viết tường minh `("x trừ một bằng " . $x) - 1`
thì ném `TypeError: Unsupported operand types: string - int`.

Dù PHP 8 đã "đoán đúng ý" trong phần lớn trường hợp, hãy vẫn bọc ngoặc khi trộn toán số học với nối
chuỗi: `"Tổng: " . ($a + $b)`. Người đọc code không phải nhớ bản PHP nào đổi luật gì.

## 8. Ternary, elvis và null coalescing

Bốn toán tử trong mục này cùng giải một việc: chọn giá trị theo điều kiện ngay trong một biểu
thức, không cần viết `if` nhiều dòng.

| Toán tử | Đọc là | Lấy vế trái khi |
|---|---|---|
| `$c ? $a : $b` | Nếu `$c` thì `$a`, không thì `$b` | (chọn theo `$c` truthy) |
| `$a ?: $b` | `$a`, nếu falsy thì `$b` | `$a` truthy |
| `$a ?? $b` | `$a`, nếu không tồn tại hoặc null thì `$b` | `$a` tồn tại và khác `null` |
| `$a ??= $b` | Gán `$b` cho `$a` nếu `$a` không tồn tại hoặc null | |

### 8.1 Toán tử ba ngôi `? :`

`(expr1) ? (expr2) : (expr3)` có giá trị `expr2` nếu `expr1` truthy, ngược lại là `expr3`. Đây là
toán tử ba ngôi duy nhất của PHP nên thường được gọi tắt là "the ternary operator". Chỉ nhánh được
chọn mới được tính.

```php
<?php
declare(strict_types=1);

$age = 20;
echo $age >= 18 ? 'người lớn' : 'trẻ em', "\n";   // in ra: người lớn

// Tương đương với:
if ($age >= 18) {
    $label = 'người lớn';
} else {
    $label = 'trẻ em';
}

function loud(string $s): string { echo "[$s]"; return $s; }
echo true ? loud('A') : loud('B'), "\n";          // in ra: [A]A, loud('B') không chạy
```

Ternary hợp với lựa chọn ngắn, hai nhánh. Nhánh dài hoặc nhiều nhánh thì dùng `if` hoặc `match`
(mục 15) cho dễ đọc.

### 8.2 Elvis `?:`

Bỏ phần giữa của ternary ta được `$a ?: $b`, gọi vui là *elvis operator* (nghiêng đầu nhìn `?:` giống
kiểu tóc của Elvis Presley), manual gọi là *short ternary*. Nó có giá trị `$a` nếu `$a` truthy, ngược
lại là `$b`. Khác `$a ? $a : $b` ở chỗ `$a` chỉ được tính một lần.

Có thể xếp chuỗi: kết quả là giá trị truthy đầu tiên.

```php
<?php
declare(strict_types=1);

$input = '';
echo $input ?: 'khách', "\n";        // in ra: khách
var_dump(0 ?: 1 ?: 2 ?: 3);          // in ra: int(1)
var_dump(0 ?: 0 ?: 2 ?: 3);          // in ra: int(2)
```

⚠️ Elvis xét truthy/falsy, nên `0`, `"0"`, `""`, `[]` đều bị coi là "không có" và bị thay. Với số
lượng hay giá có thể bằng 0, `$qty ?: 1` biến 0 thành 1, một bug khó thấy.

⚠️ Elvis không chặn warning khi biến hay key không tồn tại: `$arr['k'] ?: 'x'` vẫn in
`Warning: Undefined array key "k"`. Đó là việc của `??`.

### 8.3 Ternary lồng nhau: PHP 8 bắt buộc có ngoặc

Trong hầu hết ngôn ngữ, ternary kết hợp phải: `a ? b : c ? d : e` là `a ? b : (c ? d : e)`. PHP đời
cũ lại kết hợp trái, nên đoạn code sau (rút gọn từ ví dụ trong RFC *Deprecate left-associative
ternary operator*):

```php
return $a == 1 ? 'one'
     : $a == 2 ? 'two'
     : 'other';
```

bị PHP 7 hiểu thành `(($a == 1 ? 'one' : $a == 2) ? 'two' : 'other')`, gần như chắc chắn không phải
ý người viết. RFC này cho PHP 7.4 phát deprecation, và từ PHP 8.0 ternary lồng không có ngoặc là
**lỗi compile**:

```php
<?php
$a = true ? 0 : true ? 1 : 2;
// Fatal error: Unparenthesized `a ? b : c ? d : e` is not supported.
// Use either `(a ? b : c) ? d : e` or `a ? b : (c ? d : e)`
```

Manual hiện ghi ternary là *non-associative*. Các trường hợp vẫn hợp lệ không cần ngoặc (theo RFC):

- Ghép toàn elvis: `1 ?: 2 ?: 3`, vì nhóm kiểu nào cũng ra cùng kết quả.
- Lồng vào phần giữa: `1 ? 2 ? 3 : 4 : 5`, vì không mơ hồ.

Lời khuyên: đừng lồng ternary. Nhiều nhánh thì dùng `match (true)` (mục 15.4) hoặc `if`/`elseif`.

### 8.4 Null coalescing `??`

`$a ?? $b` (PHP 7.0) có giá trị `$a` nếu `$a` **tồn tại và khác `null`**, ngược lại là `$b`. Điểm quý
nhất: giống `isset()`, nó **không phát warning** khi biến, key mảng hay property không tồn tại, kể cả
khi đào sâu nhiều tầng.

```php
<?php
declare(strict_types=1);

// Tương đương: $action = isset($_POST['action']) ? $_POST['action'] : 'default';
$action = $_POST['action'] ?? 'default';
echo $action, "\n";                                   // in ra: default

$data = ['user' => ['name' => 'An']];
var_dump($data['user']['email'] ?? 'không có');       // in ra: string(10) "không có"
var_dump($data['order']['id'] ?? 'không có');         // tầng 'order' cũng không có: vẫn không warning
var_dump($missing ?? 'mặc định');                     // biến chưa định nghĩa: không warning

$x = null;
$y = null;
$z = 3;
var_dump($x ?? $y ?? $z);                             // in ra: int(3), giá trị khác null đầu tiên
```

`??` kết hợp phải và ngắt mạch: vế phải chỉ được tính khi cần.

So sánh `?:` và `??` trên cùng một giá trị, đây là bảng nên thuộc:

| `$v` | `$v ?: 'khách'` | `$v ?? 'khách'` |
|---|---|---|
| `'An'` | `'An'` | `'An'` |
| `''` | `'khách'` | `''` |
| `'0'` | `'khách'` | `'0'` |
| `0` | `'khách'` | `0` |
| `false` | `'khách'` | `false` |
| `[]` | `'khách'` | `[]` |
| `null` | `'khách'` | `'khách'` |
| chưa định nghĩa | `'khách'` kèm Warning | `'khách'`, không warning |

Quy tắc chọn: "không có giá trị" nghĩa là `null` hoặc không tồn tại thì dùng `??`; "giá trị rỗng
cũng coi như không có" thì dùng `?:`, và nhớ rằng `0` cũng là rỗng.

Từ PHP 8.0, `throw` là biểu thức nên đặt được ở vế phải của `??` và `?:`
([Chương 12](12-loi-exception.md)):

```php
<?php
declare(strict_types=1);

function findName(int $id): ?string
{
    return $id === 1 ? 'An' : null;
}

$name = findName(1) ?? throw new RuntimeException('Không tìm thấy');
echo $name, "\n";      // in ra: An
// findName(2) ?? throw ... sẽ ném RuntimeException
```

### 8.5 Gán null coalescing `??=`

`$a ??= $b` (PHP 7.4) gán `$b` cho `$a` chỉ khi `$a` không tồn tại hoặc là `null`. Nếu `$a` đã
có giá trị thì không làm gì, và `$b` không được tính. Nó sinh ra để khỏi lặp lại vế trái dài:

```php
<?php
declare(strict_types=1);

$config = [];
// Thay cho: $config['db']['host'] = $config['db']['host'] ?? 'localhost';
$config['db']['host'] ??= 'localhost';
var_dump($config['db']['host']);    // in ra: string(9) "localhost"

function compute(): string { echo "[compute]"; return 'v'; }

$cache = ['a' => 'cached'];
$cache['a'] ??= compute();          // đã có giá trị: compute() KHÔNG chạy
$cache['b'] ??= compute();          // chưa có: compute() chạy, in [compute]
var_dump($cache['b']);              // in ra: string(1) "v"
```

Mẫu `$cache[$key] ??= tinhToanTon($key);` là cách viết *memoization* (nhớ kết quả) gọn nhất trong PHP.

### 8.6 Bẫy: `??` có ưu tiên rất thấp

`??` đứng dưới hầu hết toán tử khác: số học, `.`, so sánh, `&&`, `||`. Nó chỉ cao hơn ternary, phép
gán và vài toán tử ít gặp như `and`, `or`, `print`, `yield` (bảng ở mục 12).
Manual trang Comparison đưa ví dụ:

```php
<?php
declare(strict_types=1);

print 'Mr. ' . $name ?? 'Anonymous';   // Warning: Undefined variable $name, rồi in ra: Mr.
// PHP hiểu là ('Mr. ' . $name) ?? 'Anonymous': vế trái là phép nối, luôn khác null
echo "\n";
print 'Mr. ' . ($name ?? 'Anonymous'); // in ra: Mr. Anonymous
```

Bẫy tương tự với so sánh:

```php
<?php
declare(strict_types=1);

$count = 10;
var_dump($count ?? 0 > 5);     // in ra: int(10), vì là $count ?? (0 > 5)
var_dump(($count ?? 0) > 5);   // in ra: bool(true), đúng ý
```

Quy tắc: khi `??` nằm trong một biểu thức lớn hơn, **luôn bọc nó trong ngoặc**.

## 9. Nullsafe `?->` và `instanceof`

Hai toán tử này làm việc với object. Class, property và method được giải thích kỹ ở
[Chương 09](09-oop-co-ban.md); ở đây chỉ cần biết `$obj->prop` đọc property, `$obj->method()` gọi
method.

### 9.1 Nullsafe `?->` (PHP 8.0)

Vấn đề: một chuỗi truy cập như `$user->getAddress()->city` vỡ ngay khi một mắt xích là `null`. Trước
PHP 8 phải kiểm từng tầng:

```php
$city = null;
if ($user !== null) {
    $address = $user->getAddress();
    if ($address !== null) {
        $city = $address->city;
    }
}
```

`?->` thay cả khối đó: nếu vế trái là `null` thì **cả chuỗi phía sau bị bỏ qua** và biểu thức có giá
trị `null`; nếu khác `null` thì nó hành xử y hệt `->`.

```php
<?php
declare(strict_types=1);

final class Address
{
    public function __construct(public ?string $city) {}
}

final class User
{
    public function __construct(public ?Address $address) {}
    public function getAddress(): ?Address { return $this->address; }
}

function expensive(): string { echo "[expensive]"; return 'x'; }

$u1 = new User(new Address('Hà Nội'));
$u2 = new User(null);
$u3 = null;

var_dump($u1?->getAddress()?->city);   // in ra: string(9) "Hà Nội"
var_dump($u2?->getAddress()?->city);   // in ra: NULL
var_dump($u3?->getAddress()->city);    // in ra: NULL, ->city phía sau cũng bị bỏ qua
var_dump($u3?->foo(expensive()));      // in ra: NULL, expensive() không hề chạy
```

RFC *Nullsafe operator* gọi đây là *full short circuiting*: khi một mắt xích là `null`, toàn bộ phần
còn lại của chuỗi (truy cập property, gọi method, truy cập mảng `[]`, kể cả tham số của các lời
gọi trong chuỗi) đều không được tính. Vì vậy `$u3?->getAddress()->city` không lỗi dù `->city` không có
dấu `?`.

Giới hạn:

- `?->` chỉ xử lý giá trị `null`. Biến chưa định nghĩa vẫn phát `Warning: Undefined variable`, và
  vế trái là string hay int thì vẫn phát `Warning: Attempt to read property "..." on string`.
- Chỉ dùng để đọc. `$user?->name = 'x';` là lỗi compile `Can't use nullsafe operator in write
  context`; lấy reference `&$user?->name` cũng là lỗi compile.

**`?->` và `??` phối hợp thế nào.** `??` đã mang ngữ nghĩa `isset()` cho cả chuỗi property và
key mảng, nhưng không cứu được lời gọi method trên `null`:

```php
<?php
declare(strict_types=1);

final class User
{
    public ?User $manager = null;
    public function getName(): string { return 'An'; }
}

$u = null;
var_dump($u->manager ?? 'không có');           // in ra: string(10) "không có", không warning
var_dump($u?->getName() ?? 'khách');           // in ra: string(6) "khách"
try {
    var_dump($u->getName() ?? 'khách');        // ?? không bảo vệ lời gọi method
} catch (Error $e) {
    echo $e->getMessage(), "\n";               // in ra: Call to a member function getName() on null
}
```

Mẫu hay dùng: `$order?->customer?->getAddress()?->city ?? 'Chưa có địa chỉ'`: `?->` lo các mắt xích
null, `??` cho giá trị mặc định ở cuối.

⚠️ Đừng rải `?->` khắp nơi "cho chắc". Mỗi `?->` nói với người đọc rằng giá trị đó được phép
null. Nếu theo nghiệp vụ một đơn hàng luôn có khách hàng, viết `->` để code nổ sớm khi dữ liệu sai,
thay vì lặng lẽ trả `null` rồi sai ở chỗ khác.

### 9.2 `instanceof`

`$x instanceof T` trả `true` nếu `$x` là object của class `T`, của một class con của `T`, hoặc của
class cài đặt interface `T`.

```php
<?php
declare(strict_types=1);

interface Shape { public function area(): float; }

class Rect implements Shape
{
    public function __construct(protected float $w, protected float $h) {}
    public function area(): float { return $this->w * $this->h; }
}

final class Square extends Rect
{
    public function __construct(float $side) { parent::__construct($side, $side); }
}

$sq = new Square(2.0);
var_dump($sq instanceof Square);   // in ra: bool(true)
var_dump($sq instanceof Rect);     // in ra: bool(true), class cha
var_dump($sq instanceof Shape);    // in ra: bool(true), interface

$name = 'Rect';
var_dump($sq instanceof $name);    // in ra: bool(true), tên class trong biến string

var_dump(1 instanceof Rect, null instanceof Rect, 'Rect' instanceof Rect);
// in ra: bool(false) bool(false) bool(false), không phải object thì là false, không lỗi
var_dump($sq instanceof NoSuchClass); // in ra: bool(false), class không tồn tại cũng không lỗi

var_dump(!$sq instanceof Rect);    // in ra: bool(false), tức !($sq instanceof Rect)
```

Ghi chú:

- `instanceof` không ném lỗi khi vế trái không phải object, và cũng không kích hoạt autoload cho
  class ở vế phải (chạy thử với một autoloader in log: không có dòng log nào cho `NoSuchClass`).
- Tên class đặt trong biến string phải là tên đầy đủ kèm namespace; alias khai báo bằng `use`
  không áp dụng cho chuỗi ([Chương 11](11-namespace-composer.md)).
- Từ PHP 8.0 vế phải có thể là biểu thức bất kỳ trong ngoặc, cho ra string: `$x instanceof ($prefix . 'Shape')`.
- `!` có ưu tiên thấp hơn `instanceof`, nên `!$sq instanceof Rect` đúng ý "không phải Rect". Còn
  ép kiểu (`(int)`), `~`, `@`, dấu trừ một ngôi thì cao hơn: `(int) $x instanceof Foo` là
  `((int) $x) instanceof Foo` (ghi chú trong manual).

Các cách kiểm kiểu object khác:

| Cách viết | Ý nghĩa |
|---|---|
| `$x instanceof Rect` | Là Rect hoặc class con, hoặc cài đặt interface |
| `$x::class === Rect::class` hoặc `get_class($x) === Rect::class` | Đúng chính xác class Rect, class con không tính |
| `is_a($x, Rect::class)` | Như `instanceof`, dạng hàm; thêm tham số thứ ba `true` thì nhận cả chuỗi tên class |
| `is_subclass_of($x, Rect::class)` | Là class con của Rect, bản thân Rect không tính |

⚠️ Một chuỗi dài `if ($shape instanceof Rect) {...} elseif ($shape instanceof Circle) {...}` thường là
dấu hiệu nên dùng đa hình (mỗi class tự cài `area()`) thay vì rẽ nhánh theo kiểu
([Chương 10](10-oop-nang-cao.md)).

## 10. Toán tử kiểm soát lỗi `@` và toán tử backtick

### 10.1 `@` làm gì

Đặt `@` trước một biểu thức thì mọi thông báo lỗi (warning, notice, deprecated...) mà biểu thức đó
sinh ra sẽ không được hiển thị hay ghi log. Quy tắc của manual: thứ gì lấy được giá trị thì đặt `@`
trước được (biến, lời gọi hàm, `include`...); không đặt được trước định nghĩa hàm, class hay câu lệnh
như `if`, `foreach`.

```php
<?php
declare(strict_types=1);

$content = @file_get_contents('/khong/ton/tai.txt');   // không in Warning
var_dump($content);                                    // in ra: bool(false)
echo error_get_last()['message'], "\n";
// in ra: file_get_contents(/khong/ton/tai.txt): Failed to open stream: No such file or directory

$cache = [];
$v = @$cache['k'];                                     // không in "Undefined array key"
var_dump($v);                                          // in ra: NULL
```

Lỗi bị che vẫn còn đó: `error_get_last()` trả thông tin lỗi gần nhất (phải đọc ngay, vì lỗi sau sẽ
ghi đè).

### 10.2 Cơ chế bên trong và thay đổi ở PHP 8

`@` không "tắt lỗi" theo nghĩa phép màu. Compiler bọc biểu thức giữa hai opcode `BEGIN_SILENCE` và
`END_SILENCE`. `BEGIN_SILENCE` lưu giá trị `error_reporting` hiện tại, rồi tạm hạ nó xuống chỉ còn các
mức lỗi fatal; `END_SILENCE` khôi phục giá trị cũ (xem `Zend/zend_vm_def.h`). Hệ quả:

- **Error handler tự định nghĩa vẫn được gọi** (`set_error_handler`, [Chương 12](12-loi-exception.md)).
  Handler phải tự kiểm tra xem lỗi có đang bị `@` che không.
- **Từ PHP 8.0, `@` không che được lỗi fatal** (`E_ERROR`, `E_CORE_ERROR`, `E_COMPILE_ERROR`,
  `E_USER_ERROR`, `E_RECOVERABLE_ERROR`, `E_PARSE`). Trước 8.0, `@` trước lời gọi một hàm gõ sai tên
  có thể làm script chết không để lại một dòng thông báo nào.
- Trong handler, `error_reporting()` trước 8.0 trả `0` khi đang bị `@`; từ 8.0 trả đúng mặt nạ các mức
  fatal ở trên (giá trị `4437`). Handler cũ viết `if (error_reporting() == 0) return;` phải sửa thành
  kiểm tra theo bit như ví dụ dưới.
- `@` **không chặn exception**. `@intdiv(1, 0)` vẫn ném `DivisionByZeroError`.

```php
<?php
declare(strict_types=1);

set_error_handler(function (int $errno, string $errstr): bool {
    if (!(error_reporting() & $errno)) {
        return false;                  // lỗi đang bị @ che: không xử lý
    }
    echo "xử lý lỗi: $errstr\n";
    return true;
});

$x = @$undefined;      // handler được gọi nhưng thoát sớm, không in gì
$y = $undefined2;      // in ra: xử lý lỗi: Undefined variable $undefined2
restore_error_handler();

try {
    $r = @intdiv(1, 0);
} catch (DivisionByZeroError $e) {
    echo "@ không chặn exception: ", $e->getMessage(), "\n";
    // in ra: @ không chặn exception: Division by zero
}
```

### 10.3 Vì sao nên tránh `@`

- Nó giấu nguyên nhân. Khi có sự cố trên production, log trống trơn đúng chỗ cần thông tin nhất.
- Nó che mọi lỗi của biểu thức, không riêng lỗi bạn đã lường trước. Gõ nhầm `@$cahce[$key]` thay
  cho `@$cache[$key]` thì warning "Undefined variable" cũng bị che, biểu thức lặng lẽ trả `null`.
- Nó có chi phí: mỗi lần chạy phải đổi rồi khôi phục `error_reporting`.

Gần như luôn có cách viết tường minh hơn:

| Thay vì | Viết |
|---|---|
| `@$arr['k']` | `$arr['k'] ?? null` |
| `@$obj->prop` | `$obj?->prop` hoặc `$obj->prop ?? null` |
| `@file_get_contents($f)` | Kiểm tra `is_file($f)` trước, hoặc kiểm `=== false` và log `error_get_last()` |
| `@unlink($f)` khi file có thể đã bị xoá | Chấp nhận được nếu thật sự không quan tâm, nhưng nên kiểm kết quả |

Trường hợp `@` còn hợp lý: hàm có sẵn chỉ báo lỗi bằng warning và có *race condition* khiến kiểm tra
trước không đủ (file bị process khác xoá giữa `is_file()` và `fopen()`). Khi đó vẫn kiểm giá trị trả về
và tự ghi log.

### 10.4 Toán tử backtick (deprecated từ 8.5)

Chuỗi đặt giữa hai dấu backtick `` `ls -al` `` được chạy như lệnh shell và trả về output, giống hệt
hàm `shell_exec()`. Từ PHP 8.5 toán tử này bị deprecated:

```php
<?php
$o = `echo hi`;
// PHP 8.5: Deprecated: The backtick (`) operator is deprecated, use shell_exec() instead
```

Code mới gọi thẳng `shell_exec()`, hoặc tốt hơn là `proc_open()` để kiểm soát tham số và mã thoát.
Chạy lệnh shell với dữ liệu từ người dùng là lỗ hổng *command injection*: luôn escape bằng
`escapeshellarg()` ([Chương 17](17-bao-mat.md)).

## 11. Pipe operator `|>` (PHP 8.5)

### 11.1 Vấn đề: lời gọi hàm lồng nhau đọc ngược

Muốn biến một tiêu đề thành *slug* (chuỗi dùng trong URL), ta làm lần lượt: cắt khoảng trắng hai đầu,
bỏ dấu chấm, thay dấu cách bằng `-`, đổi về chữ thường. Viết bằng lời gọi lồng nhau thì phải đọc **từ
trong ra ngoài**, ngược với thứ tự các bước:

```php
$slug = strtolower(str_replace(' ', '-', str_replace('.', '', trim($title))));
```

Cách khác là dùng biến tạm cho từng bước, dài và đặt tên mệt. PHP 8.5 thêm *pipe operator* `|>`
(RFC *Pipe operator v3*): `$value |> $callable` truyền giá trị bên trái làm tham số duy nhất cho
callable bên phải, và có giá trị là kết quả của lời gọi đó.

```php
<?php
declare(strict_types=1);

var_dump("Hello World" |> strlen(...));   // in ra: int(11), giống strlen("Hello World")

$title = '  PHP 8.5 Released  ';
$slug = $title
    |> trim(...)
    |> (fn(string $s): string => str_replace(['.', ' '], ['', '-'], $s))
    |> strtolower(...);
var_dump($slug);                          // in ra: string(15) "php-85-released"
```

Đọc từ trên xuống đúng thứ tự xử lý. `strlen(...)` là cú pháp *first-class callable* (PHP 8.1): biến
một hàm thành giá trị callable mà chưa gọi nó ([Chương 08](08-ham.md)).

### 11.2 Vế phải nhận những gì

Vế phải là bất kỳ callable hợp lệ nào nhận được một tham số, hoặc một biểu thức cho ra callable như
vậy:

```php
<?php
declare(strict_types=1);

final class Str
{
    public static function exclaim(string $s): string { return $s . '!'; }
    public function __invoke(string $s): string { return "<$s>"; }
}

$upper = strtoupper(...);
var_dump('hello'
    |> $upper                 // biến chứa closure
    |> Str::exclaim(...)      // static method
    |> new Str()              // object có __invoke
    |> 'ucfirst');            // tên hàm dạng chuỗi
// in ra: string(8) "<HELLO!>"
```

Ràng buộc (manual và RFC):

- Callable phải chạy được với đúng một đối số. Hàm cần nhiều tham số bắt buộc thì lỗi như khi gọi
  thiếu đối số: `'a,b' |> explode(...)` ném `ArgumentCountError: explode() expects at least 2
  arguments, 1 given`. Bọc bằng arrow function để truyền thêm tham số, như `str_replace` ở trên.
- Không dùng được hàm nhận tham số theo reference: `$arr |> sort(...)` ném `Error: sort():
  Argument #1 ($array) could not be passed by reference`. Pipe được thiết kế cho luồng dữ liệu "vào
  một giá trị, ra một giá trị mới".
- Vế phải không phải callable thì ném `Error` (`Value of type int is not callable`,
  `Call to undefined function ...`).
- ⚠️ Arrow function ở vế phải **phải có ngoặc**. Thiếu ngoặc là lỗi compile `Arrow functions on the
  right hand side of |> must be parenthesized`. Lý do (mục *Errata* của RFC, 08/2025): không có ngoặc
  thì thân arrow function "nuốt" luôn phần `|> ...` phía sau.

### 11.3 Thứ tự ưu tiên và thứ tự tính

`|>` kết hợp trái và tính vế trái trước. Ưu tiên của nó được chọn cho các cách dùng thường gặp: **thấp
hơn** số học và nối chuỗi `.`, **cao hơn** so sánh và `??`.

```php
<?php
declare(strict_types=1);

var_dump('beep' |> strlen(...) == 4);                         // in ra: bool(true), so sánh kết quả cả chuỗi pipe
var_dump(5 + 2 |> (fn(int $x): int => $x * 10));              // in ra: int(70), tức (5 + 2) |> ...
var_dump('a' . 'b' |> strtoupper(...));                       // in ra: string(2) "AB", tức ('a' . 'b') |> ...

function findName(int $id): ?string { return $id === 1 ? 'An' : null; }
var_dump(2 |> findName(...) ?? 'khách');                      // in ra: string(6) "khách", ?? áp lên kết quả
```

Muốn chọn callable bằng ternary hay `??` thì phải bọc ngoặc vế phải:
`$x |> ($flag ? f(...) : g(...))`.

### 11.4 Bên trong: pipe được dịch thành lời gọi thường

RFC nói rõ pipe được xử lý hoàn toàn ở compiler: chuỗi pipe được dịch thành các lời gọi hàm tuần
tự, nên với `f(...)`, `Class::method(...)`, `$obj->method(...)` gần như không tốn thêm gì lúc chạy.
Có thể tự kiểm bằng cách bảo OPcache in opcode (chạy ở thư mục chứa file, cần PHP 8.5):

```bash
# chạy ở thư mục chứa pipe.php
php -d opcache.enable_cli=1 -d opcache.opt_debug_level=0x10000 pipe.php
```

```php
<?php
function f(string $s): string { return $s; }
$x = "a";
$r = $x |> trim(...) |> f(...);
echo $r;
```

Output minh hoạ (lấy từ bản build php-wasm của PHP 8.5, rút gọn, chỉ phần `$_main`; trên bản build
khác chi tiết có thể khác, ví dụ các con số `1 64` sau `INIT_FCALL`):

```
0000 ASSIGN CV0($x) string("a")
0001 T3 = QM_ASSIGN CV0($x)
0002 T4 = FRAMELESS_ICALL_1(trim) T3
0003 INIT_FCALL 1 64 string("f")
0004 SEND_VAL T4 1
0005 V5 = DO_UCALL
0006 ASSIGN CV1($r) V5
0007 ECHO CV1($r)
```

Không có closure nào được tạo cho `trim(...)` hay `f(...)`: compiler gọi thẳng `trim` rồi `f`, y như
viết `f(trim($x))`. Ngược lại, khi bước pipe là arrow function, opcode có thêm
`DECLARE_LAMBDA_FUNCTION` và `INIT_DYNAMIC_CALL`: mỗi lần chạy tạo một object `Closure` rồi gọi nó,
tốn hơn một chút (RFC thừa nhận chi phí này). Chi tiết về opcode ở [Chương 19](19-ben-trong-engine.md).

Đối chiếu: F#, Elixir, OCaml dùng `|>` với đúng ý nghĩa này (RFC nêu tên). Go và Java không có pipe;
Java hay dùng chuỗi method của Stream API (`list.stream().map(...).filter(...)`) cho cùng mục đích.

⚠️ Pipe là cú pháp mới của 8.5. Trên PHP 8.4 trở xuống, `|>` là lỗi cú pháp (`unexpected token ">"`),
nên thư viện cần chạy trên nhiều bản PHP chưa dùng được.

## 12. Bảng thứ tự ưu tiên và các bẫy ưu tiên

### 12.1 Bảng đầy đủ

Bảng dưới theo manual PHP (bản có pipe của 8.5), từ ưu tiên cao nhất xuống thấp nhất. Các
toán tử cùng dòng có cùng mức ưu tiên; khi đó cột kết hợp quyết định cách nhóm (mục 1.4).

| Mức | Kết hợp | Toán tử | Ghi chú |
|---|---|---|---|
| 1 | | `clone`, `new` | [Chương 09](09-oop-co-ban.md) |
| 2 | phải | `**` | Mục 2.4 |
| 3 | | `+` `-` (một ngôi), `++` `--`, `~`, ép kiểu `(int)` `(float)` `(string)` `(array)` `(object)` `(bool)`, `@` | |
| 4 | trái | `instanceof` | Mục 9.2 |
| 5 | | `!` | Mục 5.4 |
| 6 | trái | `*` `/` `%` | |
| 7 | trái | `+` `-` (hai ngôi) | |
| 8 | trái | `<<` `>>` | |
| 9 | trái | `.` | Từ 8.0 thấp hơn `+` `-` `<<` `>>` (mục 7.2) |
| 10 | trái | `\|>` | PHP 8.5 (mục 11) |
| 11 | không kết hợp | `<` `<=` `>` `>=` | |
| 12 | không kết hợp | `==` `!=` `===` `!==` `<>` `<=>` | |
| 13 | trái | `&` | Bitwise and (và dấu `&` của reference) |
| 14 | trái | `^` | |
| 15 | trái | `\|` | |
| 16 | trái | `&&` | |
| 17 | trái | `\|\|` | |
| 18 | phải | `??` | Mục 8.4 |
| 19 | không kết hợp | `? :` | Kết hợp trái trước 8.0 (mục 8.3) |
| 20 | phải | `=` `+=` `-=` `*=` `**=` `/=` `.=` `%=` `&=` `\|=` `^=` `<<=` `>>=` `??=` | |
| 21 | | `yield from` | Generator, [Chương 13](13-generator-iterator-spl.md) |
| 22 | | `=>` (yield có key) | |
| 23 | | `yield` | |
| 24 | | `print` | [Chương 03](03-cu-phap-bien-hang.md) |
| 25 | trái | `and` | Mục 5.3 |
| 26 | trái | `xor` | |
| 27 | trái | `or` | |

Bên dưới `or` manual còn liệt kê `include`/`require`, arrow function `fn` và `throw`.

Không cần học thuộc cả bảng. Nhớ vài mốc là đủ đọc hầu hết code:

```
  cao   **  >  một ngôi (-, ép kiểu, @)  >  instanceof  >  !  >  * / %  >  + -  >  .  >  |>
        >  so sánh  >  & ^ |  >  &&  >  ||  >  ??  >  ? :  >  =  >  and  xor  or   thấp
```

### 12.2 Các bẫy ưu tiên đã gặp trong chương

| Viết | PHP hiểu là | Ý thường muốn | Mục |
|---|---|---|---|
| `$f = false or true;` | `($f = false) or true` | `$f = (false \|\| true)` | 5.3 |
| `$x = true xor true;` | `($x = true) xor true` | `$x = (true xor true)` | 5.3 |
| `!$a == $b` | `(!$a) == $b` | `$a != $b` | 5.4 |
| `$flags & MASK == MASK` | `$flags & (MASK == MASK)` | `($flags & MASK) == MASK` | 6.3 |
| `'Mr. ' . $name ?? 'x'` | `('Mr. ' . $name) ?? 'x'` | `'Mr. ' . ($name ?? 'x')` | 8.6 |
| `$count ?? 0 > 5` | `$count ?? (0 > 5)` | `($count ?? 0) > 5` | 8.6 |
| `-2 ** 2` | `-(2 ** 2)`, ra `-4` | `(-2) ** 2` | 2.4 |
| `$job = array_shift($q) !== null` | `$job = (array_shift($q) !== null)` | `($job = array_shift($q)) !== null` | 3.3 |
| `"x: " . $a - 1` | PHP 8: `"x: " . ($a - 1)`; PHP 7: `("x: " . $a) - 1` | Viết ngoặc tường minh | 7.2 |
| `a ? b : c ? d : e` | Lỗi compile từ 8.0 | Thêm ngoặc hoặc dùng `match` | 8.3 |

Một trường hợp "trông như bẫy nhưng không phải": `if (!$user = findUser($id))`. Phép gán có ưu tiên
thấp hơn `!`, nhưng vế trái của phép gán bắt buộc là biến, nên PHP nhóm thành `!($user =
findUser($id))` (ghi chú trong manual). Hợp lệ, nhưng nhiều người đọc phải dừng lại nghĩ; viết
`if (($user = findUser($id)) === null)` rõ hơn.

Quy tắc thực hành: khi một biểu thức trộn **hai nhóm toán tử khác nhau** (số học với chuỗi, bitwise với
so sánh, `??` với bất cứ thứ gì), hãy thêm ngoặc dù không bắt buộc. Ngoặc không tốn gì lúc chạy, còn
người đọc thì đỡ phải tra bảng.

## 13. Rẽ nhánh với `if`, `elseif`, `else`

Từ đây chương chuyển sang *cấu trúc điều khiển* (control structures): các câu lệnh quyết định đoạn
code nào chạy, chạy bao nhiêu lần. Mặc định PHP chạy lần lượt từ trên xuống; cấu trúc điều khiển cho
phép rẽ nhánh và lặp.

### 13.1 `if`

```
if (biểu_thức)
    câu_lệnh
```

PHP tính `biểu_thức`, đổi kết quả sang bool theo luật truthy/falsy ([Chương 04](04-kieu-du-lieu.md)),
nếu là `true` thì chạy `câu_lệnh`. Muốn chạy nhiều câu lệnh thì gom vào một khối `{ ... }`.

```php
<?php
declare(strict_types=1);

$items = [];
if ($items) {                 // mảng rỗng là falsy
    echo "có hàng\n";
} else {
    echo "giỏ rỗng\n";        // in ra: giỏ rỗng
}

$s = "0";
if ($s) { echo "truthy\n"; } else { echo "falsy\n"; }      // in ra: falsy, "0" là falsy
$s2 = "0.0";
if ($s2) { echo "truthy\n"; } else { echo "falsy\n"; }     // in ra: truthy, "0.0" là truthy
```

⚠️ Điều kiện "ngầm" như `if ($items)` hay `if ($s)` gọn nhưng dễ sai với chuỗi `"0"` và số `0`. Khi
ý định là "khác null" hay "không rỗng", viết tường minh: `if ($x !== null)`, `if ($items !== [])`,
`if ($s !== '')`.

### 13.2 `else` và `elseif`

`else` chạy khi điều kiện của `if` (và mọi `elseif` trước nó) đều false. `elseif` thêm một điều kiện
nữa; PHP xét lần lượt từ trên xuống và chỉ chạy nhánh đầu tiên có điều kiện true.

```php
<?php
declare(strict_types=1);

function grade(int $score): string
{
    if ($score >= 90) {
        return 'A';
    } elseif ($score >= 80) {
        return 'B';               // 85 khớp ở đây; các nhánh sau không được xét
    } elseif ($score >= 65) {
        return 'C';
    } else {
        return 'F';
    }
}

echo grade(95), grade(85), grade(70), grade(10), "\n";   // in ra: ABCF
```

Thứ tự các nhánh quan trọng: nếu đặt `$score >= 65` lên đầu thì 95 cũng ra `'C'`.

`elseif` (một từ) và `else if` (hai từ) cho cùng kết quả khi dùng ngoặc nhọn. Về cú pháp chúng khác
nhau: `else if` thực chất là một `else` chứa một câu lệnh `if` mới. Khác biệt này lộ ra ở cú pháp thay
thế (mục 19): ở đó chỉ `elseif` hợp lệ. PSR-12 cũng khuyên dùng `elseif`.

### 13.3 Luôn dùng ngoặc nhọn

PHP cho phép bỏ `{}` khi thân chỉ có một câu lệnh, và đây là nguồn bug quen thuộc:

```php
<?php
declare(strict_types=1);

$isAdmin = false;
if ($isAdmin)
    echo "xoá dữ liệu\n";
    echo "ghi log\n";        // KHÔNG thuộc if, dù thụt lề như thể thuộc: luôn chạy
// in ra: ghi log
```

Bẫy thứ hai là *dangling else* (else lơ lửng). Ví dụ trong manual:

```php
<?php
declare(strict_types=1);

$a = false;
$b = true;
if ($a)
    if ($b)
        echo "b";
else
    echo "c";
// không in gì cả
```

Thụt lề gợi ý `else` thuộc `if ($a)`, nhưng PHP luôn ghép `else` với `if` gần nhất, tức `if ($b)`.
Vì `$a` false nên cả khối không chạy. Thụt lề không có ý nghĩa gì với PHP. Chuẩn code PSR-12 quy
định thân của mọi cấu trúc điều khiển phải nằm trong ngoặc nhọn, và PHP-CS-Fixer tự thêm được
([Chương 21](21-chat-luong-code.md)).

### 13.4 Guard clause: thoát sớm thay vì lồng sâu

`if` lồng nhiều tầng làm code trôi sang phải và khó theo dõi. Kỹ thuật *guard clause* xử lý các trường
hợp đặc biệt trước rồi `return` sớm, để luồng chính nằm ở mức thụt lề ngoài cùng:

```php
<?php
declare(strict_types=1);

// Lồng sâu
function shippingFeeNested(?array $order): int
{
    if ($order !== null) {
        if ($order['total'] < 500_000) {
            return 30_000;
        } else {
            return 0;
        }
    } else {
        return 0;
    }
}

// Guard clause
function shippingFee(?array $order): int
{
    if ($order === null) {
        return 0;
    }
    if ($order['total'] >= 500_000) {
        return 0;                   // miễn phí ship cho đơn từ 500k
    }
    return 30_000;
}

echo shippingFee(null), ' ', shippingFee(['total' => 600_000]), ' ', shippingFee(['total' => 100_000]), "\n";
// in ra: 0 0 30000
```

Trong vòng lặp, `continue` đóng vai trò tương tự `return` sớm (mục 18).

## 14. `switch`

### 14.1 Cú pháp và cách chạy

`switch` so một giá trị với nhiều giá trị khả dĩ, thay cho một dãy `if ($x == ...) elseif ($x ==
...)`:

```php
<?php
declare(strict_types=1);

$method = 'POST';
switch ($method) {
    case 'GET':
        echo "đọc dữ liệu\n";
        break;
    case 'POST':
        echo "tạo mới\n";          // in ra: tạo mới
        break;
    case 'PUT':
    case 'PATCH':                  // case rỗng: rơi xuống case dưới, PUT và PATCH dùng chung
        echo "cập nhật\n";
        break;
    default:
        echo "không hỗ trợ\n";
}
```

Manual mô tả cách `switch` chạy: lúc đầu không câu lệnh nào chạy; PHP tìm `case` đầu tiên có giá trị
khớp, bắt đầu chạy từ đó, và chạy tiếp cho tới cuối khối `switch` hoặc tới khi gặp `break`.
Quên `break` thì chạy tràn sang các case bên dưới, gọi là *fallthrough*:

```php
<?php
declare(strict_types=1);

$i = 1;
switch ($i) {
    case 0:
        echo "i equals 0\n";
    case 1:
        echo "i equals 1\n";     // khớp ở đây, rồi chạy tràn xuống
    case 2:
        echo "i equals 2\n";
}
// in ra:
// i equals 1
// i equals 2
```

Fallthrough đôi khi có chủ đích (như `PUT`/`PATCH` ở trên). Khi case có thân mà cố ý không
`break`, PSR-12 yêu cầu một comment như `// no break` để người đọc biết không phải quên.

Các luật khác (manual):

- `default` khớp mọi thứ chưa khớp case nào. Đặt ở đâu cũng được nhưng quy ước là cuối cùng. Hai
  `default` là lỗi compile (`Switch statements may only contain one default clause`).
- Không case nào khớp và không có `default`: không chạy gì cả.
- Biểu thức trong `switch (...)` chỉ được tính một lần; các biểu thức `case` được tính lần lượt từ
  trên xuống và dừng ở case khớp đầu tiên.
- Từ PHP 8.5, kết thúc `case` bằng dấu `;` thay vì `:` (`case 'a';`) bị deprecated.

### 14.2 `switch` so sánh lỏng

`switch` so bằng `==`, kể cả khi file bật `strict_types`. Mọi bẫy của `==` (mục 4.2) đều có mặt:

```php
<?php
declare(strict_types=1);   // không ảnh hưởng switch

function label(?int $status): string
{
    switch ($status) {
        case 0:
            return 'Đã huỷ';
        case 1:
            return 'Đang xử lý';
        default:
            return 'Chưa có trạng thái';
    }
}

echo label(1), "\n";      // in ra: Đang xử lý
echo label(null), "\n";   // in ra: Đã huỷ   <- null == 0 là true!
```

Đây là bug thật hay gặp: cột `status` nullable trong DB, đơn hàng chưa có trạng thái bị hiển thị là
"Đã huỷ". PHP 8 không sửa được trường hợp này vì `null == 0` vẫn đúng (luật đổi về bool).

Ví dụ trong manual cho thấy thay đổi của PHP 8 với chuỗi:

```php
<?php
declare(strict_types=1);

switch ("a") {
    case 0:
        echo "0";      // PHP 7 khớp ở đây vì "a" == 0
        break;
    case "a":
        echo "a";      // PHP 8 khớp ở đây
        break;
}
// PHP 8 in ra: a
```

Numeric string vẫn so như số: `switch ("1.0")` khớp `case "1":`.

### 14.3 `switch (true)`

Muốn mỗi nhánh là một điều kiện tuỳ ý (khoảng giá trị, nhiều biến), đặt `true` làm giá trị so sánh:

```php
<?php
declare(strict_types=1);

$score = 72;
switch (true) {
    case $score >= 90:
        echo "Giỏi\n";
        break;
    case $score >= 65:
        echo "Khá\n";           // in ra: Khá
        break;
    default:
        echo "Cần cố gắng\n";
}
```

Mỗi `case` được so `true == (điều kiện)`. Mẫu này chạy được nhưng `match (true)` (mục 15.4) hoặc
`if`/`elseif` thường rõ hơn.

### 14.4 `continue` bên trong `switch`

Manual ghi chú: với `continue`, PHP coi `switch` là một cấu trúc vòng lặp. Hệ quả: `continue` (không
kèm số) bên trong `switch` hành xử như `break`, chỉ thoát khỏi `switch` chứ không sang vòng lặp kế
tiếp. Vì gần như chắc chắn đây là nhầm lẫn, từ PHP 7.3 PHP phát warning:

```php
<?php
declare(strict_types=1);

foreach ([1, 2, 3] as $n) {
    switch ($n) {
        case 2:
            continue 2;     // sang vòng tiếp theo của foreach
    }
    echo $n, ' ';
}
echo "\n";                  // in ra: 1 3

// Nếu viết "continue;" thay cho "continue 2;", PHP báo:
// Warning: "continue" targeting switch is equivalent to "break". Did you mean to use "continue 2"?
```

Đối chiếu: Java có `switch` với fallthrough giống PHP (và từ Java 14 có dạng `case X ->` không
fallthrough). Go thì ngược lại: mặc định không fallthrough, muốn rơi xuống phải viết từ khoá
`fallthrough` tường minh, và `switch` của Go so bằng `==` có kiểm kiểu (không đổi kiểu).

## 15. `match` (PHP 8.0)

### 15.1 Cú pháp

`match` là biểu thức chọn giá trị theo phép so sánh `===`:

```php
<?php
declare(strict_types=1);

$code = 404;
$text = match ($code) {
    200, 201 => 'Thành công',          // nhiều giá trị một nhánh, ngăn cách bằng dấu phẩy
    404      => 'Không tìm thấy',
    500      => 'Lỗi máy chủ',
    default  => 'Mã khác',
};
echo $text, "\n";                       // in ra: Không tìm thấy
```

Mỗi nhánh (*arm*) có dạng `điều_kiện1, điều_kiện2 => biểu_thức_kết_quả`. Giống `switch`, các điều kiện
được tính lần lượt từ trên xuống và dừng ở nhánh khớp đầu tiên; chỉ biểu thức kết quả của nhánh đó
được tính. Dùng `match` như một câu lệnh độc lập (không gán) thì vẫn phải có dấu `;` sau `}`.

### 15.2 Khác `switch` ở đâu

RFC *Match expression v2* nêu bốn khác biệt, cũng là bốn lý do `match` an toàn hơn:

1. **So sánh chặt `===`**, bất kể `strict_types`. Không còn bẫy `null == 0`.
2. **Là biểu thức**, trả về giá trị: gán thẳng, `return` thẳng, không thể quên gán biến ở một nhánh.
3. **Không fallthrough**: mỗi nhánh tự kết thúc, không có `break`.
4. **Phải vét hết trường hợp** (*exhaustive*): không nhánh nào khớp thì ném `UnhandledMatchError`,
   thay vì lặng lẽ bỏ qua.

Viết lại hàm `label()` của mục 14.2 bằng `match`:

```php
<?php
declare(strict_types=1);

function label(?int $status): string
{
    return match ($status) {
        0    => 'Đã huỷ',
        1    => 'Đang xử lý',
        null => 'Chưa có trạng thái',
    };
}

echo label(1), "\n";      // in ra: Đang xử lý
echo label(null), "\n";   // in ra: Chưa có trạng thái

echo match ("1") { 1 => 'int', "1" => 'string' }, "\n";   // in ra: string, vì "1" !== 1

try {
    echo label(5);
} catch (\UnhandledMatchError $e) {
    echo $e->getMessage(), "\n";   // in ra: Unhandled match case 5
}
```

Thông báo của `UnhandledMatchError` kèm giá trị từ PHP 8.1 (`Unhandled match case 5`,
`Unhandled match case 'abc'`); PHP 8.0 chỉ ghi kiểu (`Unhandled match value of type int`). Với array
hay object, kể cả bản mới cũng chỉ ghi kiểu (`Unhandled match case of type stdClass`); riêng enum
thì từ PHP 8.4 ghi tên case (`Unhandled match case OrderStatus::Paid`).

| | `switch` | `match` |
|---|---|---|
| Loại | Câu lệnh | Biểu thức, có giá trị |
| So sánh | `==` (lỏng) | `===` (chặt) |
| Fallthrough | Có, phải nhớ `break` | Không |
| Nhiều giá trị một nhánh | Nhiều `case` liền nhau | `1, 2, 3 => ...` |
| Không khớp nhánh nào | Lặng lẽ bỏ qua | Ném `UnhandledMatchError` |
| Thân nhánh | Nhiều câu lệnh | Một biểu thức |

### 15.3 Thân nhánh chỉ là một biểu thức

Bên phải `=>` chỉ được đặt một biểu thức; viết khối `{ ... }` là lỗi cú pháp. Cần nhiều bước thì:

- Gọi một hàm hoặc method: `'pdf' => $this->exportPdf($data),`
- Dùng `throw` (là biểu thức từ PHP 8.0): `default => throw new InvalidArgumentException("...")`.
- Hoặc quay về `switch`/`if` nếu mỗi nhánh thật sự cần nhiều câu lệnh và không trả về giá trị.

```php
<?php
declare(strict_types=1);

function parseSize(string $unit): int
{
    return match (strtolower($unit)) {
        'kb'    => 1024,
        'mb'    => 1024 ** 2,
        'gb'    => 1024 ** 3,
        default => throw new InvalidArgumentException("Đơn vị lạ: {$unit}"),
    };
}

echo parseSize('MB'), "\n";            // in ra: 1048576
try {
    parseSize('tb');
} catch (InvalidArgumentException $e) {
    echo $e->getMessage(), "\n";       // in ra: Đơn vị lạ: tb
}
```

### 15.4 `match (true)` cho điều kiện tuỳ ý

Đặt `true` làm giá trị được so, mỗi nhánh là một điều kiện; nhánh đầu tiên có điều kiện đúng bằng
`true` (so `===`) thắng:

```php
<?php
declare(strict_types=1);

$age = 23;
$group = match (true) {
    $age >= 65 => 'cao tuổi',
    $age >= 25 => 'trưởng thành',
    $age >= 18 => 'thanh niên',
    default    => 'trẻ em',
};
echo $group, "\n";     // in ra: thanh niên
```

⚠️ Vì so `===` với `true`, điều kiện phải trả về bool thật. Một biểu thức trả int hay string
truthy (ví dụ `strpos($s, 'x')` trả `3`) sẽ không bao giờ khớp. Bọc thành so sánh tường minh
(`strpos(...) !== false`) hoặc dùng hàm trả bool (`str_contains`).

Thứ tự nhánh quan trọng như `elseif`: đặt `$age >= 18` lên đầu thì 70 tuổi cũng ra `'thanh niên'`.

### 15.5 `match` với enum

`match` và enum ([Chương 10](10-oop-nang-cao.md)) là cặp đôi tự nhiên: mỗi case của enum một nhánh,
không cần `default`. Thêm case mới vào enum mà quên sửa `match` thì `UnhandledMatchError` báo ngay
lúc chạy, và công cụ phân tích tĩnh như PHPStan còn báo sớm hơn, lúc phân tích code.

```php
<?php
declare(strict_types=1);

enum OrderStatus
{
    case Pending;
    case Paid;
    case Cancelled;
}

function badge(OrderStatus $s): string
{
    return match ($s) {
        OrderStatus::Pending   => 'Chờ thanh toán',
        OrderStatus::Paid      => 'Đã thanh toán',
        OrderStatus::Cancelled => 'Đã huỷ',
    };
}

echo badge(OrderStatus::Paid), "\n";   // in ra: Đã thanh toán
```

### 15.6 Bên trong: bảng nhảy (jump table)

Khi mọi điều kiện của `match` là hằng int hoặc string (và có từ 2 điều kiện), compiler sinh một
opcode `MATCH` mang theo một bảng băm từ giá trị sang vị trí cần nhảy tới, thay vì so lần lượt từng
nhánh (hàm `zend_compile_match` trong `Zend/zend_compile.c`). Output minh hoạ (rút gọn, lấy từ bản
build php-wasm của PHP 8.5) khi bảo OPcache in opcode của hàm có
`match ($code) { 200 => 'OK', 404 => 'Not Found', 500 => 'Server Error' }`:

```
0001 MATCH CV0($code) 200: 0003, 404: 0005, 500: 0007, default: 0002
0002 MATCH_ERROR CV0($code)
0003 T2 = QM_ASSIGN string("OK")
...
```

Tra bảng băm tốn gần như cùng thời gian dù có 3 hay 300 nhánh. `switch` cũng có tối ưu tương tự
(`SWITCH_LONG`, `SWITCH_STRING`) nhưng điều kiện chặt hơn: mọi `case` phải là hằng cùng một kiểu
(toàn int hoặc toàn string, và không có chuỗi dạng số), và phải đủ số nhánh: với int cần từ 5 nhánh
trở lên, tính cả `default` (hàm `should_use_jumptable`); nếu không thì `switch` được dịch thành
dãy phép so `==` rồi nhảy. Đây là chi tiết của engine, không phải lý do chính để chọn `match`: lý do
chính vẫn là `===` và tính vét hết.

### 15.7 Khi nào vẫn dùng `switch`

`match` thay được phần lớn `switch`. `switch` vẫn hợp khi mỗi nhánh là **nhiều câu lệnh có tác dụng
phụ** (in, ghi file, cập nhật nhiều biến) và không sinh ra một giá trị, hoặc khi cần fallthrough có
chủ đích. Còn lại, đặc biệt là khi "chọn một giá trị theo một giá trị", hãy dùng `match`.

Đối chiếu: *switch expression* của Java 14+ (`case X -> ...`) gần với `match`: là biểu thức, không
fallthrough, và với enum thì compiler bắt buộc vét hết case. Go không có biểu thức tương đương.

## 16. Vòng lặp `while`, `do-while` và `for`

*Vòng lặp* (loop) chạy lặp lại một khối lệnh. Mỗi lần chạy khối lệnh gọi là một *lần lặp* (iteration).
PHP có bốn loại: `while`, `do-while`, `for`, và `foreach` (mục 17).

### 16.1 `while`: kiểm tra trước, chạy sau

```
while (điều_kiện)
    câu_lệnh
```

Trước mỗi lần lặp, PHP kiểm tra điều kiện; còn true thì chạy thân, false thì thoát. Nếu ngay lần
đầu điều kiện đã false, thân không chạy lần nào. Manual nhấn mạnh: điều kiện chỉ được kiểm ở đầu
mỗi lần lặp, nên dù nó thành false giữa chừng, lần lặp hiện tại vẫn chạy hết.

```php
<?php
declare(strict_types=1);

$i = 1;
while ($i <= 5) {
    echo $i, ' ';
    $i++;                // quên dòng này là vòng lặp vô hạn
}
echo "\n";               // in ra: 1 2 3 4 5
```

`while` hợp khi không biết trước số lần lặp: đọc tới hết dữ liệu, thử lại tới khi thành công, xử
lý hàng đợi tới khi rỗng (ví dụ `array_shift` ở mục 3.3).

### 16.2 `do-while`: chạy trước, kiểm tra sau

`do { ... } while (điều_kiện);` kiểm tra điều kiện ở cuối mỗi lần lặp, nên thân luôn chạy **ít nhất
một lần**. Chú ý dấu `;` sau `while (...)`.

```php
<?php
declare(strict_types=1);

$n = 10;
while ($n > 100) {
    echo "không bao giờ chạy\n";
}
do {
    echo "do-while chạy ít nhất 1 lần, n = $n\n";   // in ra: do-while chạy ít nhất 1 lần, n = 10
} while ($n > 100);

// Mẫu thực tế: thử lại tối đa 5 lần
$attempt = 0;
do {
    $attempt++;
    $ok = $attempt >= 3;                 // giả lập: lần thứ 3 mới thành công
    echo "lần thử $attempt: ", $ok ? 'OK' : 'lỗi', "\n";
} while (!$ok && $attempt < 5);
// in ra:
// lần thử 1: lỗi
// lần thử 2: lỗi
// lần thử 3: OK
```

### 16.3 `for`: vòng lặp có bộ đếm

```
for (khởi_tạo; điều_kiện; bước_tiếp)
    câu_lệnh
```

Theo manual: `khởi_tạo` chạy một lần lúc đầu; `điều_kiện` được kiểm ở đầu mỗi lần lặp (true
thì chạy thân); `bước_tiếp` chạy ở cuối mỗi lần lặp.

```
 khởi_tạo ──► điều_kiện ──false──► thoát
                 │ true
                 ▼
               thân ──► bước_tiếp ──┐
                 ▲                   │
                 └──── điều_kiện ◄───┘
```

```php
<?php
declare(strict_types=1);

for ($i = 0; $i < 5; $i++) {
    echo $i, ' ';
}
echo "\n";                                      // in ra: 0 1 2 3 4

// Mỗi phần có thể chứa nhiều biểu thức, ngăn cách bằng dấu phẩy
for ($i = 0, $j = 10; $i < $j; $i += 3, $j -= 3) {
    echo "($i,$j) ";
}
echo "\n";                                      // in ra: (0,10) (3,7)

for ($i = 10; $i > 0; $i -= 3) {
    echo $i, ' ';
}
echo "\n";                                      // in ra: 10 7 4 1
echo "sau vòng for: i = $i\n";                  // in ra: sau vòng for: i = -2
```

Dòng cuối cho thấy một đặc điểm của PHP: biến tạo trong `for` (hay `foreach`) không biến mất khi
vòng lặp kết thúc. PHP không có *block scope*; phạm vi biến là cả hàm hoặc cả file
([Chương 03](03-cu-phap-bien-hang.md)). Java và Go thì khác: biến khai báo trong `for` chỉ sống trong
vòng lặp.

Phần nào của `for` cũng có thể để trống; `điều_kiện` trống nghĩa là luôn true, nên `for (;;)` là vòng
lặp vô hạn (thoát bằng `break`).

**Gọi hàm trong điều kiện.** `điều_kiện` và `bước_tiếp` chạy lại ở mỗi lần lặp, nên manual khuyên
đừng đặt lời gọi hàm tốn kém ở đó; tính trước một lần và lưu vào biến. Riêng `count()` trên array thì
manual ghi rõ là rẻ: kích thước được lưu sẵn cùng array, `count()` không phải đếm lại (trừ
`COUNT_RECURSIVE`). Cách viết quen thuộc:

```php
<?php
declare(strict_types=1);

$list = ['a', 'b', 'c'];
for ($i = 0, $n = count($list); $i < $n; $i++) {
    echo $list[$i];
}
echo "\n";                                      // in ra: abc
```

Với array, manual khuyên dùng `foreach` thay cho `for`: `for` theo chỉ số chỉ đúng khi array là list
(key 0..n-1 liên tục), xem [Chương 06](06-mang.md).

### 16.4 Vòng lặp vô hạn và các lỗi thường gặp

`while (true) { ... }` hay `for (;;) { ... }` là vòng lặp vô hạn có chủ đích, thoát bằng `break`
(mục 18). Hay gặp ở worker xử lý hàng đợi, vòng đọc socket. Còn vòng lặp vô hạn không chủ đích
thường do:

- Quên cập nhật biến điều kiện (`$i++`) trong `while`.
- Điều kiện dùng `!=` với số thực. Cộng `0.1` mười lần không ra đúng `1.0`:

```php
<?php
declare(strict_types=1);

$sum = 0.0;
for ($k = 0; $k < 10; $k++) {
    $sum += 0.1;
}
var_dump($sum, $sum == 1.0);   // in ra: float(0.9999999999999999) bool(false)
// Vì vậy "while ($x != 1.0) { $x += 0.1; }" chạy mãi mãi. Dùng bộ đếm int, hoặc so bằng < thay vì !=.
```

Trên web, script chạy vô hạn sẽ bị PHP dừng khi vượt `max_execution_time` (mặc định 30 giây theo
manual); trên CLI thì giới hạn mặc định là 0, tức không giới hạn ([Chương 18](18-fpm-nginx-opcache.md)).

Đối chiếu: Go chỉ có một từ khoá vòng lặp là `for`, dùng được theo cả ba kiểu (`for i := 0; i < n;
i++`, `for cond`, `for {}`). Java có đủ `while`, `do-while`, `for` và *enhanced for* (`for (T x :
list)`) tương ứng với `foreach`.

## 17. `foreach`

### 17.1 Hai dạng cơ bản

`foreach` là cách chính để duyệt array và object. Mỗi lần lặp, giá trị của phần tử hiện tại được gán
vào biến sau `as`; dạng thứ hai gán thêm key.

```php
<?php
declare(strict_types=1);

$prices = ['tao' => 30000, 'cam' => 25000];

foreach ($prices as $price) {
    echo $price, ' ';
}
echo "\n";                                      // in ra: 30000 25000

foreach ($prices as $name => $price) {
    echo "$name=$price ";
}
echo "\n";                                      // in ra: tao=30000 cam=25000
```

Thứ tự duyệt là thứ tự phần tử trong array (array PHP là *ordered map*, [Chương 06](06-mang.md)).
Hai hành vi quan trọng được giải thích kỹ ở [Chương 06](06-mang.md) và chỉ nhắc ở đây:

- `foreach` theo giá trị (mặc định) duyệt trên bản của array lúc bắt đầu vòng lặp; gán vào
  `$price` không sửa array, và thêm/xoá phần tử bên trong vòng lặp không đổi những gì được duyệt.
- `foreach ($arr as &$v)` theo tham chiếu sửa thẳng phần tử, nhưng để lại `$v` là reference tới
  phần tử cuối. Luôn `unset($v);` ngay sau vòng lặp, hoặc tránh hẳn kiểu này.

### 17.2 Phân rã phần tử ngay trong `foreach`

Khi mỗi phần tử là một array, có thể tách nó ra biến ngay ở chỗ `as`, bằng `[...]` (PHP 7.1+) hoặc
`list(...)`. Dạng có key rất hợp với dữ liệu kiểu "dòng" lấy từ DB hay JSON:

```php
<?php
declare(strict_types=1);

$rows = [
    [1, 'An'],
    [2, 'Bình'],
];
foreach ($rows as [$id, $name]) {
    echo "$id:$name ";
}
echo "\n";                                      // in ra: 1:An 2:Bình

$users = [
    ['id' => 1, 'name' => 'An',   'email' => 'an@example.com'],
    ['id' => 2, 'name' => 'Bình', 'email' => 'binh@example.com'],
];
foreach ($users as ['id' => $id, 'email' => $email]) {   // chỉ lấy hai key cần dùng
    echo "$id:$email ";
}
echo "\n";                                      // in ra: 1:an@example.com 2:binh@example.com
```

⚠️ Phần tử thiếu key cần lấy thì biến nhận `null` kèm `Warning: Undefined array key`. Phần tử không
phải array (ví dụ một số int) thì từ PHP 8.5 có thêm `Warning: Cannot use int as array`; PHP 8.4 lặng
lẽ gán `null`.

### 17.3 Duyệt object và generator

- `foreach` trên một object thường duyệt các property nhìn thấy được từ chỗ gọi (bên ngoài class
  thì chỉ property `public`).
- Object cài interface `Iterator` hoặc `IteratorAggregate`, và *generator* (hàm có `yield`), tự quyết
  định `foreach` nhận được gì. Đây là cách duyệt dữ liệu lớn mà không nạp hết vào bộ nhớ
  ([Chương 13](13-generator-iterator-spl.md)).

```php
<?php
declare(strict_types=1);

final class Point
{
    public int $x = 1;
    public int $y = 2;
    private int $secret = 3;
}

foreach (new Point() as $prop => $val) {
    echo "$prop=$val ";
}
echo "\n";                                      // in ra: x=1 y=2 (không thấy $secret)

function numbers(): Generator
{
    yield 10;
    yield 20;
}
foreach (numbers() as $n) {
    echo $n, ' ';
}
echo "\n";                                      // in ra: 10 20
```

### 17.4 `foreach` trên giá trị không duyệt được

`foreach` trên `null`, int, string... không ném exception mà chỉ phát warning rồi bỏ qua vòng lặp:

```php
<?php
declare(strict_types=1);

$data = null;                                   // ví dụ: hàm trả null khi không có kết quả
foreach ($data as $x) {
    echo "không chạy";
}
// Warning: foreach() argument must be of type array|object, null given
echo "sau foreach null\n";                      // in ra: sau foreach null
```

Manual cũng ghi chú: không dùng `@` để che lỗi của `foreach` được. Cách đúng là bảo đảm kiểu từ gốc:
khai báo kiểu trả về `array` (trả `[]` thay vì `null`), hoặc `foreach ($data ?? [] as $x)`.

Biến `$x`, `$k` của `foreach` cũng "sống sót" sau vòng lặp như biến của `for` (mục 16.3).

## 18. `break`, `continue` và `goto`

### 18.1 `break`: thoát khỏi vòng lặp

`break` kết thúc ngay cấu trúc `for`, `foreach`, `while`, `do-while` hoặc `switch` đang bao nó, chạy
tiếp từ câu lệnh sau cấu trúc đó.

```php
<?php
declare(strict_types=1);

foreach (['one', 'two', 'stop', 'three'] as $val) {
    if ($val === 'stop') {
        break;
    }
    echo $val, ' ';
}
echo "\n";                                      // in ra: one two

$i = 0;
while (true) {                                  // vô hạn có chủ đích
    $i++;
    if ($i > 3) {
        break;
    }
    echo "vòng $i\n";
}
// in ra: vòng 1, vòng 2, vòng 3 (mỗi dòng một vòng)
```

### 18.2 `continue`: bỏ qua phần còn lại của lần lặp

`continue` nhảy tới lần lặp kế tiếp (với `for` thì chạy `bước_tiếp` rồi kiểm điều kiện). Dùng như guard
clause trong vòng lặp:

```php
<?php
declare(strict_types=1);

foreach ([1, 2, 3, 4, 5, 6] as $n) {
    if ($n % 2 === 0) {
        continue;                               // bỏ qua số chẵn
    }
    echo $n, ' ';
}
echo "\n";                                      // in ra: 1 3 5
```

### 18.3 `break N` và `continue N`

Cả hai nhận một số nguyên dương cho biết tác động lên bao nhiêu tầng cấu trúc bao quanh (mặc định
là 1). Nhớ là `switch` cũng được tính là một tầng (mục 14.4).

```php
<?php
declare(strict_types=1);

$matrix = [
    [1, 2, 3],
    [4, -5, 6],
    [7, 8, 9],
];

// Tìm số âm đầu tiên, thấy là thoát cả hai vòng
$found = null;
foreach ($matrix as $r => $row) {
    foreach ($row as $c => $value) {
        if ($value < 0) {
            $found = [$r, $c];
            break 2;                            // thoát vòng trong VÀ vòng ngoài
        }
    }
}
echo json_encode($found), "\n";                 // in ra: [1,1]
```

`continue 2` tương tự: bỏ phần còn lại của vòng trong và của lần lặp hiện tại ở vòng ngoài, chuyển
sang lần lặp kế tiếp của vòng ngoài.

Luật:

- Số tầng phải là hằng số nguyên dương viết thẳng trong code. `break 0;` báo lỗi compile `'break'
  operator accepts only positive integers`; `break $n;` báo `'break' operator with non-integer operand
  is no longer supported` (PHP rất cũ từng cho phép, nay thì không).
- Số tầng lớn hơn số tầng thực có (`break 2` khi chỉ có một vòng): lỗi `Cannot 'break' 2 levels`.
- `break` nằm ngoài mọi vòng lặp và `switch`: lỗi `'break' not in the 'loop' or 'switch' context`.

⚠️ `break 3`, `continue 2` khó đọc vì người đọc phải đếm tầng. Khi vòng lặp lồng phức tạp, tách vòng
trong ra một hàm và dùng `return` thường rõ hơn.

### 18.4 `goto` (chỉ để biết)

`goto ten_nhan;` nhảy tới dòng có nhãn `ten_nhan:` trong cùng file và cùng ngữ cảnh. Manual nêu các giới
hạn: không nhảy ra khỏi hay vào trong một hàm/method, không nhảy vào vòng lặp hay `switch` (lỗi
`'goto' into loop or switch statement is disallowed`), nhưng được nhảy ra khỏi chúng. Ví dụ trong
manual:

```php
<?php
declare(strict_types=1);

for ($i = 0, $j = 50; $i < 100; $i++) {
    while ($j--) {
        if ($j === 17) {
            goto end;                           // thay cho break nhiều tầng
        }
    }
}
echo "i = $i";
end:
echo "j hit 17\n";                              // in ra: j hit 17
```

`goto` làm luồng chạy khó theo dõi và hầu như không xuất hiện trong code PHP hiện đại. Biết nó tồn tại
để đọc được code cũ; khi viết, dùng `break N`, `return` hoặc tách hàm.

## 19. Cú pháp thay thế (alternative syntax)

### 19.1 Dạng `:` ... `endif;`

PHP có cú pháp thứ hai cho `if`, `while`, `for`, `foreach`, `switch` (và `declare`): thay `{` bằng `:`
và thay `}` bằng `endif;`, `endwhile;`, `endfor;`, `endforeach;`, `endswitch;`.

```php
<?php
$i = 0;
while ($i < 3):
    echo $i;
    $i++;
endwhile;

for ($j = 0; $j < 3; $j++):
    echo $j;
endfor;

switch ($i):
    case 3:
        echo " ba";
        break;
endswitch;
echo "\n";
// in ra: 012012 ba
```

### 19.2 Dùng ở đâu: template HTML

Trong code thuần PHP, cú pháp ngoặc nhọn là chuẩn. Cú pháp thay thế toả sáng trong template, nơi
PHP xen giữa HTML ([Chương 03](03-cu-phap-bien-hang.md) nói về chế độ HTML và thẻ `<?php ?>`,
`<?= ?>`). Một `<?php } ?>` đứng lẻ loi giữa HTML rất khó biết đang đóng cái gì; `<?php endforeach; ?>`
thì tự nói lên điều đó.

```php
<?php
declare(strict_types=1);

$user = ['name' => 'An', 'isAdmin' => true];
$orders = [
    ['id' => 101, 'total' => 250000],
    ['id' => 102, 'total' => 90000],
];
?>
<h1>Xin chào, <?= htmlspecialchars($user['name']) ?></h1>
<?php if ($user['isAdmin']): ?>
<a href="/admin">Trang quản trị</a>
<?php endif; ?>
<ul>
<?php foreach ($orders as $order): ?>
    <li>Đơn #<?= $order['id'] ?>: <?= number_format($order['total']) ?>đ</li>
<?php endforeach; ?>
</ul>
<?php if (count($orders) === 0): ?>
<p>Chưa có đơn hàng.</p>
<?php elseif (count($orders) === 1): ?>
<p>Có 1 đơn hàng.</p>
<?php else: ?>
<p>Có <?= count($orders) ?> đơn hàng.</p>
<?php endif; ?>
```

Output:

```html
<h1>Xin chào, An</h1>
<a href="/admin">Trang quản trị</a>
<ul>
    <li>Đơn #101: 250,000đ</li>
    <li>Đơn #102: 90,000đ</li>
</ul>
<p>Có 2 đơn hàng.</p>
```

Blade của Laravel ([Chương 25](25-laravel-request-validation-response.md)) dịch template về PHP thuần
bằng đúng cú pháp này: trong mã nguồn laravel/framework, `@if(...)` được dịch thành `<?php if(...): ?>`
và `@endif` thành `<?php endif; ?>`; `@endforeach` cũng sinh ra `endforeach;`.

### 19.3 Luật và bẫy

- Không trộn hai kiểu trong cùng một khối: mở bằng `if (...):` mà đóng bằng `else { ... }` là lỗi
  cú pháp (`unexpected token "{", expecting ":"`).
- Trong cú pháp thay thế phải viết `elseif` liền; `else if (...):` là lỗi cú pháp (`unexpected token
  "if", expecting ":"`). Đây là chỗ duy nhất `elseif` và `else if` khác nhau (mục 13.2).
- Với `switch` dạng thay thế, mọi output (kể cả khoảng trắng) nằm giữa `switch (...):` và `case` đầu
  tiên là lỗi cú pháp. Manual khuyên viết `?>` của dòng `switch` và `<?php case ...` sát nhau.
- Luôn escape dữ liệu khi in ra HTML (`htmlspecialchars`), như dòng `<h1>` ở trên. In thẳng dữ liệu
  người dùng là lỗ hổng XSS ([Chương 17](17-bao-mat.md)).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| `$ok = $a and $b;` hay `$f = false or true;` cho kết quả sai | `and`, `or`, `xor` có ưu tiên thấp hơn `=`, nên phép gán chạy trước | Luôn dùng `&&`, `\|\|`; cần `xor` thì bọc ngoặc (mục 5.3) |
| `if ($x = 5)` luôn đúng | Gõ `=` (gán) thay cho `==`/`===` | Dùng `===`; bật công cụ kiểm tra như PHP_CodeSniffer (mục 3.3) |
| `switch` cho kết quả lạ với `null`, `0`, `""` | `switch` so bằng `==`: `null == 0` là `true` | Dùng `match` (so `===`) (mục 14.2, 15.2) |
| Quên `break` trong `switch` | Fallthrough: chạy tràn sang case dưới | Dùng `match`; fallthrough cố ý thì ghi `// no break` (mục 14.1) |
| `'Tổng: ' . $a ?? 0`, `$n ?? 0 > 5` sai ý | `??` có ưu tiên rất thấp | Bọc `??` trong ngoặc (mục 8.6) |
| `$qty ?: 1` biến số lượng 0 thành 1 | `?:` xét falsy, `0` là falsy | Dùng `??` khi chỉ muốn thay `null` (mục 8.4) |
| `$flags & MASK == MASK` cho kết quả sai | `&` có ưu tiên thấp hơn `==` | `($flags & MASK) === MASK` hoặc `($flags & MASK) !== 0` (mục 6.3) |
| `-2 ** 2` ra `-4` | `**` ưu tiên cao hơn dấu trừ một ngôi | `(-2) ** 2` (mục 2.4) |
| Kiểm số lẻ bằng `$n % 2 === 1` sai với số âm | `%` cho kết quả cùng dấu số bị chia: `-3 % 2` là `-1` | `$n % 2 !== 0` (mục 2.3) |
| Dịch `a / b` từ Java/Go ra kết quả có phần thập phân | Trong PHP `/` giữa hai int không chia hết trả float | `intdiv()` khi cần chia nguyên (mục 2.2) |
| `0.1 + 0.2 == 0.3` sai, `while ($x != 1.0)` chạy mãi | Sai số của float | Bộ đếm int, so bằng `<`, so với sai số, tiền dùng int/bcmath (mục 4.5, 16.4) |
| `@` làm mất dấu vết lỗi trên production | `@` che mọi diagnostic của biểu thức | Dùng `??`, `?->`, kiểm tra giá trị trả về và log (mục 10.3) |
| `a ? b : c ? d : e` báo Fatal error khi lên PHP 8 | Ternary lồng không ngoặc bị cấm từ 8.0 | Thêm ngoặc, hoặc dùng `match (true)`/`if` (mục 8.3) |
| `continue` trong `switch` bên trong vòng lặp không sang vòng tiếp | `continue` coi `switch` là một tầng, chạy như `break` | `continue 2` (mục 14.4) |
| `match (true)` không bao giờ khớp nhánh `strpos(...)` | `match` so `===` với `true`, mà `strpos` trả int | Điều kiện phải trả bool thật (mục 15.4) |
| `$x \|> fn($v) => ... \|> g(...)` báo Fatal error | Arrow function trong pipe phải có ngoặc | `\|> (fn($v) => ...)` (mục 11.2) |
| `$total += $x` báo `Undefined variable` | Gán kết hợp đọc biến trước khi ghi | Khởi tạo `$total = 0;` trước vòng lặp (mục 3.2) |
| `foreach` trên `null` in warning | Hàm trả `null` thay vì mảng rỗng | Khai báo kiểu trả về `array`, hoặc `$data ?? []` (mục 17.4) |
| Phần tử cuối mảng bị hỏng sau hai vòng `foreach` | `foreach` by reference để lại `$v` trỏ tới phần tử cuối | `unset($v)` sau vòng lặp, hoặc tránh by reference ([Chương 06](06-mang.md)) |

## Tóm tắt chương

- Biểu thức là thứ có giá trị; toán tử nhận toán hạng và sinh giá trị mới. Thứ tự ưu tiên và tính kết
  hợp chỉ quyết định cách nhóm, không quyết định thứ tự tính; đừng vừa sửa vừa đọc một biến trong
  cùng biểu thức.
- Số học: `/` trả float trừ khi chia hết, `intdiv()` chia nguyên, chia cho 0 ném `DivisionByZeroError`
  từ 8.0; `%` đổi về int và lấy dấu của số bị chia; `**` kết hợp phải và cao hơn dấu trừ một ngôi.
  Toán hạng là array, object, chuỗi không phải số thì `TypeError` từ 8.0; `strict_types` không ảnh
  hưởng toán tử.
- `++`/`--` trên `null`, bool, chuỗi có nhiều ngóc ngách; từ 8.5 tăng chuỗi không phải số bị deprecated,
  dùng `str_increment()`.
- So sánh: mặc định dùng `===`/`!==`. `==` đổi kiểu theo bảng luật (Chương 04), và nó ẩn trong
  `switch`, `in_array`. `<=>` trả âm/0/dương, dùng cho hàm sắp xếp, kể cả nhiều tiêu chí bằng mảng.
- Logic: `&&`, `||` ngắt mạch và luôn trả bool; `and`, `or`, `xor` thấp hơn `=` nên đừng dùng.
- `??` thay giá trị khi null hoặc không tồn tại và không phát warning; `?:` thay khi falsy;
  `??=` gán khi null; `?->` ngắt cả chuỗi khi gặp null nhưng chỉ dùng để đọc. `??` có ưu tiên rất
  thấp: bọc ngoặc.
- `@` chỉ hạ `error_reporting` tạm thời, không che được fatal error (từ 8.0), không chặn exception;
  tránh dùng. Toán tử backtick bị deprecated từ 8.5.
- Pipe `|>` (8.5) truyền giá trị trái làm tham số duy nhất cho callable phải, được compiler dịch thành
  lời gọi thường; arrow function trong pipe phải có ngoặc.
- `match` (8.0) là biểu thức, so `===`, không fallthrough, ném `UnhandledMatchError` khi không khớp:
  an toàn hơn `switch` trong hầu hết trường hợp. `match (true)` thay cho chuỗi `elseif` theo khoảng.
- Vòng lặp: `while` kiểm trước, `do-while` chạy ít nhất một lần, `for` cho bộ đếm, `foreach` cho array
  và object. `break N`/`continue N` tác động N tầng (tính cả `switch`). Biến vòng lặp còn sống sau vòng
  lặp. Cú pháp thay thế (`endif`, `endforeach`) dành cho template.

## Câu hỏi tự kiểm tra

1. Thứ tự ưu tiên và thứ tự tính khác nhau thế nào? Vì sao `echo $a + $a++;` không nên xuất hiện trong
   code thật? (mục 1.5)
2. Không chạy code, cho biết giá trị của `7 / 2`, `8 / 2`, `intdiv(-7, 2)`, `-7 % 3`, `-2 ** 2`,
   `2 ** 3 ** 2`.
3. Vì sao `$f = false or true;` để lại `$f` là `false`? Viết lại cho đúng ý. (mục 5.3)
4. Cho ba giá trị mà `$v ?: 'x'` và `$v ?? 'x'` cho kết quả khác nhau. Khi nào nên dùng cái nào?
5. Vì sao `print 'Mr. ' . $name ?? 'Anonymous';` vẫn in warning khi `$name` chưa định nghĩa? (mục 8.6)
6. Với `$order?->getCustomer()->getName(sendMail())`, nếu `$order` là `null` thì `sendMail()` có chạy
   không? Vì sao `$order->getCustomer() ?? null` không thay được `?->`? (mục 9.1)
7. Nêu bốn khác biệt giữa `switch` và `match`. Trường hợp nào vẫn nên dùng `switch`?
8. Trong một file có `declare(strict_types=1);`, `switch (null)` có khớp `case 0:` không? Còn
   `match (null)` với nhánh `0 =>`? Giải thích. (mục 14.2)
9. `continue` đặt trong `switch` nằm trong `foreach` sẽ làm gì? Muốn sang phần tử kế tiếp của
   `foreach` thì viết thế nào?
10. Pipe `|>` được dịch thành gì lúc compile? Vì sao `$x |> sort(...)` lỗi, và vì sao arrow function
    trong pipe phải có ngoặc? (mục 11)

## Bài tập

**Bài 1. Phân loại mã HTTP.** Viết `http_status.php` có hàm `classify(int $code): string` dùng
`match (true)`: 100-199 là `'informational'`, 200-299 `'success'`, 300-399 `'redirect'`, 400-499
`'client error'`, 500-599 `'server error'`; ngoài khoảng 100-599 thì ném `InvalidArgumentException`
(dùng `throw` trong nhánh `default`). Chạy thử với `[100, 204, 301, 404, 503]` và in mỗi mã một dòng,
rồi gọi với `99` và `600` trong `try/catch` để in thông báo lỗi. Sau đó viết lại hàm bằng `switch
(true)` và bằng `if/elseif`, so output ba bản phải giống hệt nhau.

**Bài 2. Quyền bằng bitmask.** Viết `permissions.php` định nghĩa 4 hằng `READ`, `WRITE`, `DELETE`,
`SHARE` bằng phép dịch bit, và các hàm `grant(int $mask, int $perm): int`, `revoke(...)`,
`toggle(...)`, `has(int $mask, int $perm): bool`, `describe(int $mask): string` (trả về chuỗi như
`"READ, SHARE"`, mask bằng 0 thì `"(không có quyền)"`). Viết kịch bản: bắt đầu từ 0, cấp READ và WRITE,
đảo SHARE hai lần, thu hồi WRITE, in `describe()` và `printf('%04b', ...)` sau mỗi bước. Kết quả cuối
cùng phải là `READ` với mask `0001`. Kiểm tra lại: `has()` của bạn có bị bẫy ưu tiên `&` với `==`
không?

**Bài 3. Săn bẫy ưu tiên.** Tạo `precedence.php`. Với từng biểu thức sau, viết dự đoán vào comment
trước, rồi mới `var_dump` để kiểm tra; với mỗi dự đoán sai, ghi lại bạn đã nhầm luật nào (dẫn mục
trong chương) và viết lại biểu thức bằng ngoặc cho rõ ý:

```php
$a = null;
$b = 0;
$r1 = true and false;
$r2 = !$b == 5;
$r3 = 'Kết quả: ' . 1 + 2;
$r4 = $a ?? 'x' . 'y';
$r5 = 6 & 3 == 2;
$r6 = $b ?: 10 ?: 20;
$r7 = 10 - 2 ** 2 ** 0 * 3;
$r8 = 'abc' |> strlen(...) > 2 ? 'dài' : 'ngắn';   // cần PHP 8.5
```

**Bài 4 (PHP 8.5). Chuẩn hoá số điện thoại bằng pipe.** Viết `phone.php` với hàm
`normalizePhone(string $raw): ?string` xây bằng một chuỗi pipe: cắt khoảng trắng hai đầu; bỏ mọi ký tự
khoảng trắng, dấu chấm, dấu gạch ngang; đổi tiền tố `+84` thành `0`; cuối cùng trả `null` nếu kết quả
không phải đúng 10 chữ số bắt đầu bằng `0` (gợi ý: `preg_match`, chương 05). Thử với
`' 0912.345.678 '`, `'+84 912 345 678'`, `'0912-345-67'`, `'abc'` và in kết quả bằng `var_dump`. Sau đó
viết lại cùng hàm không dùng pipe (lời gọi lồng nhau hoặc biến tạm) và so sánh: bản nào dễ đọc hơn,
bản nào dễ thêm một bước xử lý mới hơn?

## Đọc thêm

Manual PHP, phần toán tử:
[Operators](https://www.php.net/manual/en/language.operators.php) ·
[Operator Precedence](https://www.php.net/manual/en/language.operators.precedence.php) ·
[Arithmetic](https://www.php.net/manual/en/language.operators.arithmetic.php) ·
[Increment/Decrement](https://www.php.net/manual/en/language.operators.increment.php) ·
[Assignment](https://www.php.net/manual/en/language.operators.assignment.php) ·
[Bitwise](https://www.php.net/manual/en/language.operators.bitwise.php) ·
[Comparison](https://www.php.net/manual/en/language.operators.comparison.php) (gồm ternary và `??`) ·
[Error Control](https://www.php.net/manual/en/language.operators.errorcontrol.php) ·
[Execution](https://www.php.net/manual/en/language.operators.execution.php) ·
[Logical](https://www.php.net/manual/en/language.operators.logical.php) ·
[String](https://www.php.net/manual/en/language.operators.string.php) ·
[Type (instanceof)](https://www.php.net/manual/en/language.operators.type.php) ·
[Functional (pipe)](https://www.php.net/manual/en/language.operators.functional.php) ·
[Expressions](https://www.php.net/manual/en/language.expressions.php)

Manual PHP, phần cấu trúc điều khiển:
[if](https://www.php.net/manual/en/control-structures.if.php) ·
[else](https://www.php.net/manual/en/control-structures.else.php) ·
[elseif/else if](https://www.php.net/manual/en/control-structures.elseif.php) ·
[Alternative syntax](https://www.php.net/manual/en/control-structures.alternative-syntax.php) ·
[while](https://www.php.net/manual/en/control-structures.while.php) ·
[do-while](https://www.php.net/manual/en/control-structures.do.while.php) ·
[for](https://www.php.net/manual/en/control-structures.for.php) ·
[foreach](https://www.php.net/manual/en/control-structures.foreach.php) ·
[break](https://www.php.net/manual/en/control-structures.break.php) ·
[continue](https://www.php.net/manual/en/control-structures.continue.php) ·
[switch](https://www.php.net/manual/en/control-structures.switch.php) ·
[match](https://www.php.net/manual/en/control-structures.match.php) ·
[goto](https://www.php.net/manual/en/control-structures.goto.php)

RFC (đọc phần *Proposal*):
[Null Coalesce Operator](https://wiki.php.net/rfc/isset_ternary) ·
[Combined Comparison (Spaceship) Operator](https://wiki.php.net/rfc/combined-comparison-operator) ·
[Null Coalescing Assignment Operator](https://wiki.php.net/rfc/null_coalesce_equal_operator) ·
[Deprecate left-associative ternary operator](https://wiki.php.net/rfc/ternary_associativity) ·
[Change the precedence of the concatenation operator](https://wiki.php.net/rfc/concatenation_precedence) ·
[Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison) ·
[Saner numeric strings](https://wiki.php.net/rfc/saner-numeric-strings) ·
[Stricter type checks for arithmetic/bitwise operators](https://wiki.php.net/rfc/arithmetic_operator_type_checks) ·
[Reclassifying engine warnings](https://wiki.php.net/rfc/engine_warnings) ·
[Nullsafe operator](https://wiki.php.net/rfc/nullsafe_operator) ·
[Match expression v2](https://wiki.php.net/rfc/match_expression_v2) ·
[throw expression](https://wiki.php.net/rfc/throw_expression) ·
[Path to Saner Increment/Decrement operators](https://wiki.php.net/rfc/saner-inc-dec-operators) ·
[Raising zero to the power of negative number](https://wiki.php.net/rfc/raising_zero_to_power_of_negative_number) ·
[Pipe operator v3](https://wiki.php.net/rfc/pipe-operator-v3) ·
[Deprecations for PHP 8.5](https://wiki.php.net/rfc/deprecations_php_8_5)

Mã nguồn và chuẩn code:
[php-src: UPGRADING của PHP 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) ·
[php-src: zend_language_parser.y](https://github.com/php/php-src/blob/PHP-8.5/Zend/zend_language_parser.y)
(khai báo `%left`/`%right`/`%nonassoc` ở đầu file chính là bảng ưu tiên) ·
[php-src: zend_compile.c](https://github.com/php/php-src/blob/PHP-8.5/Zend/zend_compile.c)
(`zend_compile_match`, `zend_compile_unary_pm`) ·
[PSR-12: Extended Coding Style](https://www.php-fig.org/psr/psr-12/) (mục 5, cấu trúc điều khiển) ·
[PHP-CS-Fixer: rule logical_operators](https://cs.symfony.com/doc/rules/operator/logical_operators.html)
