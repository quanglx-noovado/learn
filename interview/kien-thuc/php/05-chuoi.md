# Chương 05. Chuỗi (string)

> [← Mục lục](README.md) · [← Chương 04: Kiểu dữ liệu và hệ thống kiểu](04-kieu-du-lieu.md) · [Chương 06: Mảng (array) →](06-mang.md)

**Bạn sẽ học được:**

- String trong PHP thật ra là một dãy byte, và vì sao chi tiết đó gây ra gần như mọi lỗi với tiếng Việt.
- Bốn cách viết chuỗi (nháy đơn, nháy kép, heredoc, nowdoc), cách escape và chèn biến vào chuỗi.
- Nhóm hàm string dùng hằng ngày và các bẫy kinh điển của chúng (`strpos` trả về `0`, `trim` với
  tham số thứ hai, `str_replace` thay dây chuyền...).
- Xử lý UTF-8 cho đúng: khi nào bắt buộc dùng `mb_*`, khi nào hàm thường vẫn an toàn, chuẩn hoá
  Unicode bằng `Normalizer`.
- So sánh và sắp xếp chuỗi: `===`, họ `strcmp`, so sánh "tự nhiên", sắp xếp tiếng Việt bằng `Collator`.
- Viết regex PCRE cơ bản với `preg_match`, `preg_replace` và tránh các bẫy về `$`, modifier `u`,
  lỗi bị nuốt im lặng và ReDoS.

**Cần biết trước:** [Chương 03](03-cu-phap-bien-hang.md) (biến, `echo`, `var_dump`) và
[Chương 04](04-kieu-du-lieu.md) (các kiểu dữ liệu, `strict_types`).

**Cách chạy ví dụ.** Mỗi ví dụ đầy đủ là một file `.php`. Lưu lại rồi chạy `php ten-file.php`. Không
cài PHP thì dùng Docker, chạy ở thư mục chứa file:

```bash
# Chạy tại thư mục chứa file ví dụ
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

Image `php:8.5-cli` chính thức đã có sẵn extension `mbstring` nhưng không có `intl`. Các ví dụ có
dòng `// Cần extension intl` (ở mục 3.4, 5.5, 5.6 và 6.4) cần `intl`; với Docker, cài thêm trong
container như sau (PHP cài qua Homebrew trên macOS đã có sẵn cả hai):

```bash
# Chạy tại thư mục chứa file ví dụ; cài intl rồi chạy file
docker run --rm -v "$PWD":/app -w /app php:8.5-cli bash -c \
  "apt-get update -qq && apt-get install -y -qq libicu-dev > /dev/null \
   && docker-php-ext-install intl > /dev/null && php ten-file.php"
```

## 1. String là gì

### 1.1 Chuỗi là một dãy byte

Một *string* (chuỗi) là một đoạn dữ liệu dạng văn bản: tên người dùng, nội dung email, một dòng
log, một câu SQL, cả nội dung một file ảnh. Trong PHP, định nghĩa chính xác là:

> String là một dãy **byte**. PHP không biết các byte đó biểu diễn chữ gì.

Manual của PHP nói thẳng: một ký tự (character) trong string là một byte, nên PHP "không có hỗ trợ
Unicode gốc" (*native Unicode support*). Bên trong, mỗi string là một vùng nhớ gồm các byte cộng với
một số nguyên ghi độ dài. PHP không lưu kèm thông tin "các byte này là UTF-8 hay mã nào khác".

Hệ quả đầu tiên thấy ngay:

```php
<?php
declare(strict_types=1);

$a = 'Hi';
$b = 'Việt';

echo strlen($a), "\n";   // in ra: 2
echo strlen($b), "\n";   // in ra: 6   (không phải 4!)
echo bin2hex($a), "\n";  // in ra: 4869
echo bin2hex($b), "\n";  // in ra: 5669e1bb8774
```

`strlen()` trả về số byte, không phải số chữ. `bin2hex()` in từng byte dưới dạng hai chữ số hex,
rất tiện để "nhìn" vào bên trong một chuỗi. Chữ `ệ` chiếm 3 byte vì file mã nguồn được lưu bằng
UTF-8, và trong UTF-8 chữ `ệ` được mã hoá thành 3 byte `E1 BB 87`:

```
'Việt' trong bộ nhớ (file nguồn lưu bằng UTF-8):

 byte  :  56    69    E1    BB    87    74
 chữ   :  V     i     └──── ệ ────┘     t
 offset:  0     1     2     3     4     5        strlen = 6
```

Mục 5 sẽ giải thích kỹ UTF-8. Lúc này chỉ cần nhớ: với PHP, `'Việt'` là 6 byte. Chuỗi literal trong
code mang đúng mã hoá (*encoding*) của file nguồn; file lưu UTF-8 thì chuỗi là UTF-8. Ngày nay hầu
hết dự án lưu file UTF-8, nên bạn cứ giả định như vậy, nhưng hiểu rằng đó là quy ước của người viết
code, không phải điều PHP bảo đảm.

Vì string chỉ là byte, PHP không có kiểu `byte` hay `char` riêng. Dữ liệu nhị phân (nội dung file
ảnh, dữ liệu đọc từ socket, kết quả hàm băm dạng raw) cũng là string. String của PHP là *binary-safe*:
byte có giá trị 0 (`"\0"`, gọi là NUL byte) nằm ở đâu cũng được, không cắt ngang chuỗi như trong C.

```php
<?php
declare(strict_types=1);

$bin = "a\0b";               // a, byte 0, b
echo strlen($bin), "\n";     // in ra: 3
echo bin2hex($bin), "\n";    // in ra: 610062
```

⚠️ Manual có lưu ý một số ít hàm "không binary-safe": chúng chuyển chuỗi xuống thư viện C và thư viện
đó bỏ qua phần sau NUL byte. Các hàm cơ bản như `strlen`, `substr`, `strpos`, `strcmp` làm việc trên
toàn bộ các byte. Khi dùng một hàm lạ với dữ liệu nhị phân, đọc manual xem có ghi chú binary-safe không.

Về độ dài tối đa: manual ghi trên bản PHP 32-bit một string dài tối đa 2GB (2147483647 byte). Trên
máy 64-bit phổ biến hiện nay, giới hạn thực tế là bộ nhớ mà tiến trình được dùng (`memory_limit`).

**Đối chiếu với ngôn ngữ khác.** Go giống PHP ở chỗ string là dãy byte: `len("Việt")` trong Go cũng
là 6. Java thì khác: `String` là dãy các đơn vị UTF-16 (`char`), `"Việt".length()` trả về 4. Cùng một chữ, ba
ngôn ngữ, hai đáp án. Khi chuyển qua lại giữa các ngôn ngữ, luôn hỏi "hàm độ dài này đếm cái gì?".

### 1.2 Truy cập từng byte bằng offset

Có thể đọc và sửa từng byte bằng cú pháp giống mảng `$s[i]`, với *offset* (vị trí) bắt đầu từ 0.
Từ PHP 7.1, offset âm được đếm từ cuối chuỗi: `-1` là byte cuối.

```php
<?php
declare(strict_types=1);

$s = 'hello';
echo $s[0], $s[-1], "\n";   // in ra: ho
$s[0] = 'J';
echo $s, "\n";              // in ra: Jello

$t = 'ab';
$t[5] = 'x';                // ghi quá độ dài: PHP đệm bằng dấu cách
var_dump($t);               // in ra: string(6) "ab   x"

$v = 'Việt';
echo bin2hex($v[2]), "\n";  // in ra: e1   (một byte lẻ, KHÔNG phải chữ "ệ")
```

Những điều cần biết về offset:

- Kết quả của `$s[i]` là một string dài 1 byte. PHP không có kiểu ký tự riêng.
- Đọc offset không tồn tại (`$s[10]` với chuỗi 5 byte) sinh Warning `Uninitialized string offset 10`
  và trả về chuỗi rỗng. Kiểm tra trước bằng `isset($s[10])` (trả về `false`, không cảnh báo).
- Gán chuỗi dài hơn 1 byte vào một offset (`$u[1] = 'XYZ'`) chỉ lấy byte đầu, kèm Warning
  `Only the first byte will be assigned to the string offset`. Gán chuỗi rỗng ném `Error`.
- Cú pháp cũ `$s{0}` đã bị xoá từ PHP 8.0, gặp trong code cũ thì đổi thành `$s[0]`.

⚠️ `$s[i]` làm việc với byte, nên với chuỗi UTF-8 có dấu thì `$v[2]` chỉ lấy được một mảnh của chữ
`ệ`. In mảnh đó ra màn hình sẽ thấy ký tự lỗi `�`. Muốn lấy "chữ thứ i" của chuỗi tiếng Việt, dùng
`mb_substr($v, $i, 1)` (mục 5.3).

### 1.3 Đổi giá trị khác thành string

Chương 04 đã nói về ép kiểu nói chung. Với string, cần nhớ các quy tắc sau (ép bằng `(string)` hoặc
`strval()`, hoặc tự động khi `echo`, khi nối chuỗi):

```php
<?php
declare(strict_types=1);

var_dump((string) true);    // in ra: string(1) "1"
var_dump((string) false);   // in ra: string(0) ""
var_dump((string) null);    // in ra: string(0) ""
var_dump((string) 42);      // in ra: string(2) "42"
var_dump((string) 1.0);     // in ra: string(1) "1"
var_dump((string) 1e20);    // in ra: string(7) "1.0E+20"
var_dump((string) [1, 2]);  // Warning: Array to string conversion, rồi in ra: string(5) "Array"
```

- `false` và `null` đều thành chuỗi rỗng, nên `echo false;` không in gì cả. Debug giá trị bool thì
  dùng `var_dump`, đừng dùng `echo`.
- Từ PHP 8.0, số thực luôn dùng dấu chấm `.` làm dấu thập phân khi đổi sang string, không phụ thuộc
  locale nữa (trước 8.0 thì phụ thuộc `setlocale`).
- Object muốn đổi được sang string phải có method `__toString()` (chương 10).
- Với `declare(strict_types=1)`, gọi `strlen(42)` ném `TypeError`
  (`strlen(): Argument #1 ($string) must be of type string, int given`). Chế độ strict không tự đổi
  số thành chuỗi khi truyền vào hàm, nhưng `echo 42` và `'a' . 42` vẫn chạy bình thường.

## 2. Viết chuỗi trong code: bốn cú pháp

Một *string literal* là chuỗi viết thẳng trong code. PHP có bốn cách viết:

| Cú pháp | Ví dụ | Escape (`\n`, `\t`...) | Chèn biến (`$x`) |
|---|---|---|---|
| Nháy đơn | `'Xin chào'` | Chỉ `\'` và `\\` | Không |
| Nháy kép | `"Xin chào $ten"` | Có | Có |
| Heredoc | `<<<TXT ... TXT` | Có | Có |
| Nowdoc | `<<<'TXT' ... TXT` | Không | Không |

### 2.1 Nháy đơn: viết sao ra vậy

Trong chuỗi nháy đơn, gần như mọi thứ được giữ nguyên. Chỉ có hai *escape sequence* (chuỗi thoát,
tức là cách viết đặc biệt bắt đầu bằng `\`): `\'` cho dấu nháy đơn và `\\` cho một dấu gạch ngược.
Mọi dấu `\` khác được giữ nguyên.

```php
<?php
declare(strict_types=1);

$name = 'Lan';
echo 'Xin chào $name\n', "\n";        // in ra: Xin chào $name\n   (không chèn biến, \n giữ nguyên)
echo 'It\'s a \\ and \n', "\n";       // in ra: It's a \ and \n
echo strlen('\n'), ' ', strlen("\n"); // in ra: 2 1
echo "\n";
echo 'C:\new\table', "\n";            // in ra: C:\new\table
```

`'\n'` là hai byte: dấu `\` và chữ `n`. `"\n"` là một byte xuống dòng. Đây là nguồn bug phổ biến khi
mới học: viết `'Dòng 1\nDòng 2'` rồi thắc mắc vì sao không xuống dòng.

### 2.2 Nháy kép: escape sequence

Trong chuỗi nháy kép, PHP hiểu các escape sequence sau (theo manual):

| Viết | Ý nghĩa |
|---|---|
| `\n` | xuống dòng (LF, byte 0x0A) |
| `\r` | về đầu dòng (CR, 0x0D) |
| `\t` | tab ngang (0x09) |
| `\v` | tab dọc (0x0B) |
| `\e` | escape (ESC, 0x1B), dùng cho mã màu terminal |
| `\f` | form feed (0x0C) |
| `\\` | dấu `\` |
| `\$` | dấu `$` (để không bị hiểu là biến) |
| `\"` | dấu nháy kép |
| `\101` | byte viết bằng hệ bát phân, 1 tới 3 chữ số (`"\101" === "A"`) |
| `\x41` | byte viết bằng hệ hex, 1 tới 2 chữ số (`"\x41" === "A"`) |
| `\u{1EC7}` | ký tự Unicode theo *code point*, được ghi vào chuỗi dưới dạng các byte UTF-8 |

Escape một ký tự không có trong bảng (ví dụ `"\q"`) thì dấu `\` được giữ nguyên.

```php
<?php
declare(strict_types=1);

$name = 'Lan';
echo "Xin chào $name\n";                    // in ra: Xin chào Lan (rồi xuống dòng)
echo "Đô la: \$name, nháy: \", lạ: \q\n";  // in ra: Đô la: $name, nháy: ", lạ: \q
var_dump("\x41" === 'A', "\u{41}" === 'A'); // in ra: bool(true), xuống dòng, bool(true)
var_dump(bin2hex("\u{1EC7}"));              // in ra: string(6) "e1bb87"   (chữ ệ)
echo "C:\new\table", "\n";                  // in ra: "C:", xuống dòng, "ew", TAB, "able"
```

⚠️ Dòng cuối là cái bẫy với đường dẫn Windows: trong nháy kép, `\n` và `\t` bị hiểu thành xuống dòng
và tab. Viết đường dẫn bằng nháy đơn, hoặc dùng `/` (PHP trên Windows chấp nhận cả `/`).

`\u{...}` rất hữu ích khi cần ghi rõ một ký tự khó gõ hoặc vô hình, ví dụ khoảng trắng không ngắt
dòng `"\u{00A0}"` hay dấu kết hợp `"\u{0301}"` (mục 5).

### 2.3 Chèn biến vào chuỗi (interpolation): cú pháp đơn giản

*String interpolation* là việc PHP thay tên biến trong chuỗi nháy kép (và heredoc) bằng giá trị của
nó. Cú pháp đơn giản: gặp dấu `$`, PHP đọc tiếp các ký tự hợp lệ cho tên biến và thay vào.

```php
<?php
declare(strict_types=1);

final class User
{
    public string $name = 'Lan';
    public ?User $boss = null;
}

$user = new User();
$user->boss = new User();
$user->boss->name = 'Minh';
$order = ['id' => 42, 'items' => ['bút', 'vở']];
$list = ['a', 'b', 'c'];
$price = 1500;

echo "Tên: $user->name\n";      // in ra: Tên: Lan          (một cấp thuộc tính)
echo "Phần tử: $list[1]\n";     // in ra: Phần tử: b        (một cấp chỉ số)
echo "Đơn: $order[id]\n";       // in ra: Đơn: 42           (key KHÔNG có nháy)
echo "Giá: $priceVND\n";        // Warning: Undefined variable $priceVND, in ra: Giá:
echo "Sếp: $user->boss->name\n"; // Error: Object of class User could not be converted to string
```

Cú pháp đơn giản chỉ đi được một bước: một chỉ số mảng hoặc một thuộc tính. Hai dòng cuối là hai
bẫy hay gặp:

- `$priceVND`: PHP "tham lam" đọc hết các chữ cái hợp lệ, nên tưởng bạn muốn biến `$priceVND`.
- `$user->boss->name`: PHP chỉ lấy `$user->boss` (một object), cố đổi nó thành chuỗi thì lỗi, phần
  `->name` còn lại được coi là chữ thường.

Nếu sau `$` không tạo được tên biến hợp lệ thì `$` được giữ nguyên: `"100$ USD"` in ra `100$ USD`.

### 2.4 Cú pháp ngoặc nhọn `{$...}`

Khi cần nhiều hơn một bước, hoặc cần tách tên biến khỏi chữ phía sau, bọc biểu thức trong `{$` và `}`.
Bên trong viết y như viết ngoài chuỗi:

```php
<?php
declare(strict_types=1);

final class User
{
    public string $name = 'Lan';
    public ?User $boss = null;

    public function greet(): string
    {
        return 'Chào ' . $this->name;
    }
}

const KEY = 'id';
$user = new User();
$user->boss = new User();
$user->boss->name = 'Minh';
$order = ['id' => 42, 'items' => ['bút', 'vở']];
$price = 1500;
$name = 'lan';
$upper = strtoupper(...);   // closure từ hàm có sẵn (chương 08)

echo "{$price}VND\n";              // in ra: 1500VND
echo "{$order['id']}\n";           // in ra: 42           (key CÓ nháy, chỉ được trong {})
echo "{$order[KEY]}\n";            // in ra: 42           (dùng hằng làm key)
echo "{$order['items'][0]}\n";     // in ra: bút          (nhiều chiều)
echo "{$user->boss->name}\n";      // in ra: Minh         (nhiều cấp)
echo "{$user->greet()}\n";         // in ra: Chào Lan     (gọi method)
echo "{strtoupper($name)}\n";      // in ra: {strtoupper(lan)}   (KHÔNG gọi được hàm)
echo "{$upper($name)}\n";          // in ra: LAN          (gọi closure trong biến thì được)
echo "{ $price}\n";                // in ra: { 1500}      (có dấu cách sau { thì không nhận)
echo "{{$price}}\n";               // in ra: {1500}
```

Quy tắc: PHP chỉ nhận cú pháp này khi `$` đứng ngay sau `{`. Vì vậy `"{strtoupper($name)}"`
không gọi hàm: sau `{` là chữ `s` chứ không phải `$`, nên `{` được in ra như chữ thường, còn `$name`
vẫn được chèn theo cú pháp đơn giản.

Lời khuyên thực tế: dùng `{$...}` cho mọi trường hợp trừ biến đơn giản. Khi biểu thức bắt đầu phức
tạp (gọi hàm, tính toán), tính ra biến trước hoặc dùng `sprintf` (mục 3.3) sẽ dễ đọc hơn.

⚠️ Cú pháp `"${price}"` (dấu `$` đứng ngoài ngoặc) đã deprecated từ PHP 8.2; RFC tương ứng dự
kiến xoá hẳn ở PHP 9.0. PHP 8.2 trở lên sinh thông báo
`Deprecated: Using ${var} in strings is deprecated, use {$var} instead`. Gặp trong code cũ thì đổi
`${price}` thành `{$price}`.

### 2.5 Heredoc: chuỗi nhiều dòng có chèn biến

Khi chuỗi dài nhiều dòng (nội dung email, template, câu SQL dài), nháy kép trở nên khó đọc. *Heredoc*
cho phép viết một khối văn bản: mở bằng `<<<` cộng một tên (*identifier*) tự chọn rồi xuống dòng,
đóng bằng chính tên đó. Bên trong heredoc hoạt động y như chuỗi nháy kép (escape và chèn biến), chỉ
khác là không cần escape dấu nháy kép.

```php
<?php
declare(strict_types=1);

function emailBody(string $name, int $total): string
{
    return <<<TXT
        Chào $name,
          Đơn hàng của bạn: {$total} đồng.
        Cảm ơn!
        TXT;
}

echo emailBody('Lan', 250000), "\n";
// in ra:
// Chào Lan,
//   Đơn hàng của bạn: 250000 đồng.
// Cảm ơn!
```

Từ PHP 7.3 (*flexible heredoc*), dòng đóng có thể thụt lề. PHP lấy độ thụt lề của dòng đóng (ở đây 8
dấu cách) và xoá đúng chừng đó khoảng trắng ở đầu mọi dòng trong thân. Dòng nào thụt sâu hơn thì
giữ phần dư (dòng "Đơn hàng" còn 2 dấu cách). Nhờ vậy heredoc có thể thụt lề theo code xung quanh.

Các quy tắc cần nhớ:

- Không có dòng nào trong thân được thụt ít hơn dòng đóng, nếu không sẽ gặp lỗi kiểu
  `Parse error: Invalid body indentation level (expecting an indentation level of at least 4)`
  (4 là số dấu cách thụt của dòng đóng trong trường hợp đó).
- Không trộn tab và dấu cách khi thụt lề (cũng là ParseError).
- Ký tự xuống dòng ngay trước dòng đóng không thuộc chuỗi: chuỗi trên kết thúc bằng `Cảm ơn!`,
  không có `\n` ở cuối.
- Sau tên đóng có thể viết tiếp biểu thức (từ 7.3), ví dụ `[<<<A ... A, 'hai']`.
- Tên mở có thể đặt trong nháy kép: `<<<"TXT"` tương đương `<<<TXT`.

⚠️ Bẫy chọn tên: nếu trong thân có một dòng bắt đầu bằng đúng tên đóng rồi theo sau là ký tự
không thể là một phần tên (dấu cách, dấu chấm...), PHP coi đó là dòng đóng; phần còn lại của dòng bị
hiểu như code PHP và thường gây lỗi cú pháp:

```php
<?php
$s = <<<SQL
SELECT 1
SQL là ngôn ngữ truy vấn
SQL;
// Parse error: syntax error, unexpected identifier "là"
```

Quy tắc an toàn: chọn tên không xuất hiện trong nội dung, ví dụ `TXT`, `HTML`, `EOT`.

### 2.6 Nowdoc: heredoc không xử lý gì

*Nowdoc* là với heredoc như nháy đơn là với nháy kép: không chèn biến, không escape, viết sao ra vậy.
Cú pháp giống heredoc nhưng tên mở đặt trong nháy đơn: `<<<'SQL'`. Các quy tắc về thụt lề và
dòng đóng giống heredoc.

```php
<?php
declare(strict_types=1);

$sql = <<<'SQL'
    SELECT * FROM users WHERE name = $name AND note LIKE '%\n%'
    SQL;
echo $sql, "\n";
// in ra: SELECT * FROM users WHERE name = $name AND note LIKE '%\n%'
```

Nowdoc hợp với: đoạn code mẫu, đoạn văn bản có nhiều `$` hay `\` (regex dài, script shell), template
mà bạn không muốn PHP đụng vào.

⚠️ Đừng hiểu nhầm ví dụ trên là cách viết SQL an toàn. Nowdoc chỉ giữ nguyên chữ `$name`; giá trị
thật của người dùng phải đi qua *prepared statement* (chương 16), không bao giờ nối thẳng vào SQL.

### 2.7 Chọn cú pháp nào

- Chuỗi cố định, không có biến: nháy đơn. Người đọc biết ngay "không có gì đặc biệt bên trong".
- Có biến hoặc cần `\n`, `\t`: nháy kép, dùng `{$...}` cho mọi thứ phức tạp hơn một biến.
- Văn bản nhiều dòng có biến: heredoc. Nhiều dòng không có biến, hoặc có nhiều `$` và `\`: nowdoc.
- Định dạng số, căn lề, nhiều giá trị: `sprintf` (mục 3.3).

Về tốc độ: bạn có thể đọc thấy lời khuyên "nháy đơn nhanh hơn nháy kép". Việc xử lý escape và tách
biến diễn ra ở bước biên dịch file thành opcode (chương 02). Chuỗi nháy kép không chứa biến, như
`"hi\n"`, được tokenizer xếp cùng loại token `T_CONSTANT_ENCAPSED_STRING` với chuỗi nháy đơn, tức là
cũng thành một hằng chuỗi. Khác biệt không đáng để ý; hãy chọn theo tính dễ đọc.

## 3. Nối và định dạng chuỗi

### 3.1 Toán tử `.` và `.=`

PHP dùng dấu chấm `.` để nối (*concatenate*) hai chuỗi, và `.=` để nối thêm vào cuối một biến. Dấu
`+` luôn là phép cộng số, không bao giờ nối chuỗi:

```php
<?php
declare(strict_types=1);

echo '1' . '2', "\n";   // in ra: 12
echo '1' + '2', "\n";   // in ra: 3   (hai numeric string được cộng như số)

$s = 'a';
$s .= 'b';
$s .= 'c';
echo $s, "\n";          // in ra: abc

$a = 1;
$b = 2;
echo 'Tổng: ' . $a + $b, "\n";    // in ra: Tổng: 3   (PHP 8)
echo 'Tổng: ' . ($a + $b), "\n";  // in ra: Tổng: 3   (rõ ràng, nên viết thế này)
```

**Đối chiếu.** Java, JavaScript và Go dùng `+` để nối chuỗi. PHP tách riêng hai việc: `.` là nối, `+`
là cộng. Nhờ vậy `'1' + '2'` trong PHP là `3`, còn trong JavaScript là `"12"`.

⚠️ Thứ tự ưu tiên: từ PHP 8.0 (RFC *Change the precedence of the concatenation operator*), `+` và `-`
được tính trước `.`, nên dòng `'Tổng: ' . $a + $b` cho `Tổng: 3`. Ở PHP 7, ba toán tử này ngang hàng
và tính từ trái sang phải: PHP 7 tính `('Tổng: 1') + 2` và in `2` (từ PHP 7.1 kèm Warning
`A non-numeric value encountered`; PHP 7.4 còn báo Deprecated về thay đổi này). Code chạy trên nhiều phiên bản, hoặc đơn giản là để người đọc khỏi phải nhớ: luôn đặt
ngoặc quanh phép tính khi nối với chuỗi. Bảng thứ tự ưu tiên đầy đủ ở chương 07.

### 3.2 Dựng chuỗi dài: `.=` hay `implode`

Hai cách hay dùng để ghép nhiều mảnh thành một chuỗi:

```php
<?php
declare(strict_types=1);

$items = ['bút', 'vở', 'thước'];

// Cách 1: nối dần bằng .=
$text = '';
foreach ($items as $i => $item) {
    $text .= ($i + 1) . '. ' . $item . "\n";
}
echo $text;
// in ra:
// 1. bút
// 2. vở
// 3. thước

// Cách 2: gom các mảnh vào mảng rồi ghép một lần bằng implode
$parts = [];
foreach ($items as $i => $item) {
    $parts[] = ($i + 1) . '. ' . $item;
}
echo implode(', ', $parts), "\n";   // in ra: 1. bút, 2. vở, 3. thước
```

Cách 2 tiện khi cần dấu phân cách giữa các phần tử (không bị thừa dấu phẩy ở cuối).

**Đối chiếu với Java.** `String` của Java là bất biến (*immutable*), nên `s += x` trong vòng lặp tạo
chuỗi mới mỗi lần, và người ta dùng `StringBuilder`. PHP không có `StringBuilder` và không cần: khi
chuỗi bên trái không bị biến nào khác dùng chung, `$s .= $x` có thể nới rộng ngay vùng nhớ của chính
chuỗi đó (mã nguồn PHP ghi chú rõ trường hợp "`$x .= ...;` may happen in-place"). Cơ chế dùng chung và
sao chép khi ghi (*copy-on-write*) được giải thích ở chương 19.

### 3.3 `sprintf` và `printf`: định dạng theo mẫu

Khi chuỗi có nhiều giá trị cần định dạng (số chữ số thập phân, căn lề, đệm số 0), nối bằng `.` rất
rối. `sprintf()` nhận một *chuỗi định dạng* (format string) chứa các chỗ trống bắt đầu bằng `%`, rồi
điền lần lượt các tham số vào:

```php
<?php
declare(strict_types=1);

echo sprintf('Đơn #%d của %s: %.2f USD', 42, 'Lan', 19.5), "\n";
// in ra: Đơn #42 của Lan: 19.50 USD
```

Mỗi chỗ trống có dạng `%[argnum$][flags][width][.precision]specifier`. Các phần trong ngoặc vuông là
tuỳ chọn. Phần bắt buộc là *specifier*, chữ cái cuối cùng cho biết kiểu hiển thị:

| Specifier | Ý nghĩa | Ví dụ | Kết quả |
|---|---|---|---|
| `s` | chuỗi | `sprintf('%s', 'abc')` | `abc` |
| `d` | số nguyên có dấu | `sprintf('%d', 42)` | `42` |
| `f` | số thực, theo locale | `sprintf('%.2f', 3.14159)` | `3.14` |
| `F` | số thực, không theo locale | `sprintf('%.2F', 3.14159)` | `3.14` |
| `x` / `X` | hex chữ thường / hoa | `sprintf('%x', 255)` | `ff` |
| `b` | nhị phân | `sprintf('%b', 5)` | `101` |
| `e` | dạng khoa học | `sprintf('%e', 12345.678)` | `1.234568e+4` |
| `%` | dấu `%` | `sprintf('Tăng 15%%')` | `Tăng 15%` |

Các phần tuỳ chọn:

- *width* (độ rộng tối thiểu): `%5d` đệm trái cho đủ 5 vị trí.
- *flags*: `-` căn trái, `0` đệm bằng số 0, `+` luôn in dấu của số, `'x` đệm bằng ký tự `x` tuỳ chọn.
- *precision* (sau dấu chấm): với `f`, `e` là số chữ số sau dấu thập phân (mặc định 6); với `s` là độ
  dài tối đa được lấy từ chuỗi.
- *argnum* (`%2$s`): lấy tham số thứ 2, dùng được một tham số nhiều lần.

```php
<?php
declare(strict_types=1);

echo sprintf('[%5d] [%-5d] [%05d]', 42, 42, 42), "\n";
// in ra: [   42] [42   ] [00042]
echo sprintf('[%8.3f] [%08.3f] [%+d] [%+d]', 3.14159, 3.14159, 5, -5), "\n";
// in ra: [   3.142] [0003.142] [+5] [-5]
echo sprintf("[%10s] [%-10s] [%'*10s]", 'abc', 'abc', 'abc'), "\n";
// in ra: [       abc] [abc       ] [*******abc]
echo sprintf('%x %X %o %b', 255, 255, 8, 5), "\n";
// in ra: ff FF 10 101
echo sprintf('%2$s, %1$s! %2$s', 'Lan', 'Chào'), "\n";
// in ra: Chào, Lan! Chào
echo sprintf('[%.3s]', 'abcdef'), "\n";
// in ra: [abc]

$n = printf("%s=%d\n", 'x', 10);   // printf in thẳng ra: x=10
var_dump($n);                      // in ra: int(5)   (printf trả về số byte đã in)
echo vsprintf('%s-%s', ['a', 'b']), "\n";   // in ra: a-b   (tham số truyền bằng mảng)
```

Họ hàm này gồm: `sprintf` trả về chuỗi, `printf` in ra và trả về số byte đã in, `vsprintf`/`vprintf`
nhận tham số dạng mảng, `fprintf` ghi vào file hoặc stream.

Các bẫy của `sprintf`:

```php
<?php
declare(strict_types=1);

echo sprintf('%d', 3.99), "\n";      // in ra: 3     (cắt phần thập phân, KHÔNG làm tròn)
echo sprintf('%d', '12abc'), "\n";   // in ra: 12    (lấy phần số ở đầu, không cảnh báo gì)

try {
    echo sprintf('%s và %s', 'a');   // thiếu một tham số
} catch (ArgumentCountError $e) {
    echo $e->getMessage(), "\n";     // in ra: 3 arguments are required, 2 given
}

echo sprintf('[%-6s|]', 'Viet'), "\n";      // in ra: [Viet  |]
echo sprintf('[%-6s|]', 'Việt'), "\n";      // in ra: [Việt|]   (không đệm: 'Việt' đã đủ 6 byte)
echo bin2hex(sprintf('%.3s', 'Việt')), "\n"; // in ra: 5669e1   (cắt giữa chữ ệ, chuỗi hỏng)
```

- `%d` ép tham số về số nguyên một cách lặng lẽ: `sprintf` nhận tham số kiểu `mixed`, nên
  `strict_types` không giúp được. Kiểm tra dữ liệu trước khi định dạng.
- Thiếu tham số: từ PHP 8.0 ném `ArgumentCountError` (PHP 7 trả về `false` kèm Warning).
- Width và precision của `%s` đếm byte. Bảng chữ tiếng Việt căn bằng `%-20s` sẽ bị lệch, và
  `%.3s` có thể cắt đôi một chữ. Dùng `mb_str_pad` hoặc `mb_strimwidth` (mục 5.3) cho văn bản có dấu.
  Manual của `sprintf` cũng cảnh báo điều này với các bộ ký tự nhiều byte.
- `%f` phụ thuộc locale (nếu chương trình đã gọi `setlocale`), `%F` thì không. Khi ghi số ra file,
  CSV hay giao thức mà bên kia cần dấu chấm, dùng `%F` cho chắc.
- Không dùng `sprintf` để ghép giá trị người dùng vào câu SQL. Đó vẫn là nối chuỗi và vẫn bị SQL
  injection; dùng prepared statement (chương 16, 17).

### 3.4 `number_format`: hiển thị số có phân cách hàng nghìn

```
number_format(float $num, int $decimals = 0,
              ?string $decimal_separator = ".", ?string $thousands_separator = ","): string
```

Hàm làm tròn `$num` tới `$decimals` chữ số thập phân theo quy tắc *round half up* (từ .5 trở lên làm
tròn ra xa số 0), rồi chèn dấu phân cách hàng nghìn:

```php
<?php
declare(strict_types=1);

echo number_format(1234567.891), "\n";                  // in ra: 1,234,568
echo number_format(1234567.891, 2), "\n";               // in ra: 1,234,567.89
echo number_format(1234567.891, 2, ',', '.'), "\n";     // in ra: 1.234.567,89   (kiểu Việt Nam)
echo number_format(1234567, 0, ',', '.') . ' ₫', "\n";  // in ra: 1.234.567 ₫
echo number_format(2.5), ' ', number_format(-2.5), "\n"; // in ra: 3 -3
echo number_format(1234.5678, -2), "\n";                // in ra: 1,200   (PHP 8.3+)

$s = number_format(1234.5, 2);
var_dump($s);        // in ra: string(8) "1,234.50"
var_dump($s + 1);    // Warning: A non-numeric value encountered, rồi in ra: int(2)
```

- Người Việt viết `1.234.567,89` (chấm phân cách hàng nghìn, phẩy thập phân), ngược với kiểu Mỹ. Truyền
  đủ 4 tham số để có định dạng này.
- Từ PHP 8.3, `$decimals` âm làm tròn phần nguyên (`-2` là tới hàng trăm). Trước 8.3, giá trị âm bị
  coi như `0`.
- Từ PHP 8.0 được gọi với 3 tham số (trước đó chỉ nhận 1, 2 hoặc 4 tham số).

⚠️ Kết quả của `number_format` là chuỗi để hiển thị. Đừng đưa nó vào tính toán tiếp: `"1,234.50"`
không phải numeric string, PHP chỉ đọc được chữ số `1` ở đầu nên `$s + 1` ra `2` kèm Warning. Định dạng
ở bước cuối cùng, ngay trước khi in. Còn bản thân việc tính tiền bằng số thực (`float`) đã có sai số;
chương 14 bàn cách tính tiền đúng (số nguyên đơn vị nhỏ nhất, hoặc `bcmath`).

Nếu cần định dạng theo đúng quy ước của từng nước (dấu phân cách, ký hiệu tiền tệ, vị trí ký hiệu),
extension `intl` có class `NumberFormatter`:

```php
<?php
declare(strict_types=1);

// Cần extension intl
$fmt = new NumberFormatter('vi_VN', NumberFormatter::CURRENCY);
$s = $fmt->formatCurrency(1234567, 'VND');
echo $s, "\n";                  // in ra: 1.234.567 ₫   (khoảng trắng ở giữa không phải dấu cách thường)
echo bin2hex($s), "\n";         // in ra: 312e3233342e353637c2a0e282ab
var_dump($s === '1.234.567 ₫'); // in ra: bool(false)
```

Kết quả trên chạy với ICU 74 (thư viện mà `intl` dựa vào); phiên bản ICU khác có thể cho chuỗi hơi
khác. Điểm đáng chú ý là dòng cuối: khoảng trắng giữa số và `₫` là byte `c2a0`, tức ký tự *no-break
space* U+00A0, không phải dấu cách thường. Hai chuỗi nhìn giống hệt nhau nhưng `===` trả về `false`.
Đây là loại bug khiến test so sánh chuỗi thất bại mà mắt không nhìn ra; `bin2hex` là công cụ để bắt nó.

## 4. Các hàm string dùng hằng ngày

Trang String Functions của manual liệt kê hơn một trăm hàm. Mục này đi qua nhóm hàm bạn sẽ gặp hằng ngày, kèm cạm bẫy của
từng hàm. Lưu ý chung: các hàm trong mục này làm việc trên byte. Với chuỗi chỉ có ký tự ASCII
(chữ không dấu, số, ký hiệu cơ bản) thì byte và chữ trùng nhau. Mục 5 sẽ nói khi nào cần bản `mb_*`.

### 4.1 Độ dài và cắt chuỗi: `strlen`, `substr`

`strlen($s)` trả về số byte. `substr(string $string, int $offset, ?int $length = null)` lấy một đoạn
con: bắt đầu ở `$offset`, dài tối đa `$length` byte.

```php
<?php
declare(strict_types=1);

$s = 'abcdef';
var_dump(substr($s, 1, 3));   // in ra: string(3) "bcd"    (từ vị trí 1, lấy 3 byte)
var_dump(substr($s, 2));      // in ra: string(4) "cdef"   (bỏ $length: lấy tới hết)
var_dump(substr($s, -2));     // in ra: string(2) "ef"     ($offset âm: đếm từ cuối)
var_dump(substr($s, 0, -1));  // in ra: string(5) "abcde"  ($length âm: bỏ bớt ở cuối)
var_dump(substr($s, 10));     // in ra: string(0) ""       (vượt quá độ dài)
```

- `$offset` âm đếm từ cuối; `$length` âm nghĩa là "bỏ đi chừng đó byte ở cuối".
- Từ PHP 8.0, các trường hợp "không lấy được gì" trả về chuỗi rỗng `""`. PHP 7 trả về `false` ở một
  số trường hợp, nên code cũ hay có `if (substr(...) === false)`.

### 4.2 Tìm kiếm: `str_contains`, `str_starts_with`, `str_ends_with`, `strpos`

Từ PHP 8.0 có ba hàm trả lời câu hỏi có/không, nên dùng chúng khi chỉ cần biết "có hay không":

```php
<?php
declare(strict_types=1);

$email = 'lan@example.com';
var_dump(str_contains($email, '@'));        // in ra: bool(true)
var_dump(str_starts_with($email, 'lan'));   // in ra: bool(true)
var_dump(str_ends_with($email, '.com'));    // in ra: bool(true)
var_dump(str_contains('Hello', 'hello'));   // in ra: bool(false)  (phân biệt hoa thường)
var_dump(str_contains($email, ''));         // in ra: bool(true)   (chuỗi rỗng luôn "có mặt")
```

Khi cần vị trí, dùng `strpos(string $haystack, string $needle, int $offset = 0): int|false`. Hàm
trả về vị trí byte đầu tiên tìm thấy, hoặc `false` nếu không thấy. Họ hàng: `stripos` (không phân
biệt hoa thường), `strrpos` (tìm từ cuối), `strripos`.

```php
<?php
declare(strict_types=1);

$email = 'lan@example.com';
var_dump(strpos($email, '@'));       // in ra: int(3)
var_dump(strpos($email, 'z'));       // in ra: bool(false)
var_dump(strrpos('a.b.c', '.'));     // in ra: int(3)   (lần xuất hiện cuối)
var_dump(strpos($email, 'lan'));     // in ra: int(0)   (tìm thấy ở ngay đầu chuỗi)

// BẪY: vị trí 0 bị coi là "falsy" trong if
if (strpos($email, 'lan')) {
    echo "tìm thấy\n";
} else {
    echo "không thấy\n";             // in ra: không thấy   (SAI!)
}

// Đúng: so sánh chặt với false
if (strpos($email, 'lan') !== false) {
    echo "tìm thấy\n";               // in ra: tìm thấy
}

// Dùng vị trí để cắt chuỗi
$at = strpos($email, '@');
echo substr($email, 0, $at), ' | ', substr($email, $at + 1), "\n";   // in ra: lan | example.com
```

⚠️ Đây là bẫy kinh điển nhất của PHP: `strpos` trả về `0` khi tìm thấy ở đầu chuỗi, và `0` bị `if`
coi là sai. Manual có hẳn một khung Warning ở trang `strpos`: luôn dùng `=== false` hoặc `!== false`. Chỉ
cần biết có hay không thì dùng `str_contains`, khỏi lo bẫy này.

Vài chi tiết khác:

- `$offset` lớn hơn độ dài chuỗi thì ném `ValueError` (`Argument #3 ($offset) must be contained in
  argument #1 ($haystack)`).
- `strstr($email, '@')` trả về phần từ `@` tới hết (`@example.com`); thêm tham số `true` để lấy phần
  trước (`lan`).
- `substr_count('a,b,,c', ',')` đếm số lần xuất hiện (ở đây là `3`).

### 4.3 Thay thế: `str_replace`, `str_ireplace`, `strtr`

`str_replace($search, $replace, $subject, &$count)` thay mọi chỗ xuất hiện của `$search` bằng
`$replace`. Tham số thứ tư (tuỳ chọn) nhận số lần đã thay.

```php
<?php
declare(strict_types=1);

echo str_replace('mèo', 'chó', 'mèo đen, mèo trắng', $count), " ($count)\n";
// in ra: chó đen, chó trắng (2)

// Truyền mảng: thay từng cặp theo thứ tự
echo str_replace(['{name}', '{total}'], ['Lan', '250.000'], 'Chào {name}, tổng {total} đ'), "\n";
// in ra: Chào Lan, tổng 250.000 đ

echo str_ireplace('PHP', 'Go', 'php và Php'), "\n";   // in ra: Go và Go   (không phân biệt hoa thường)
```

⚠️ Khi truyền mảng, `str_replace` xử lý lần lượt từ phần tử đầu tới cuối, và mỗi bước làm việc trên
kết quả của bước trước. Vì vậy có thể thay dây chuyền ngoài ý muốn:

```php
<?php
declare(strict_types=1);

// Muốn: A -> B và B -> C, cùng lúc
echo str_replace(['A', 'B'], ['B', 'C'], 'AB'), "\n";   // in ra: CC   (A thành B, rồi mọi B thành C)
echo strtr('AB', ['A' => 'B', 'B' => 'C']), "\n";       // in ra: BC   (đúng ý)
```

`strtr($string, array $replace_pairs)` khác ở hai điểm: thử key dài nhất trước, và phần đã thay
thì không bị tìm lại. Vì vậy `strtr` hợp với việc điền template (`['{name}' => 'Lan']`) hoặc
hoán đổi qua lại. Ví dụ trong manual: `strtr("hi all, I said hello", ["h" => "-", "hello" => "hi",
"hi" => "hello"])` cho `hello all, I said hi`.

⚠️ `str_ireplace` và `stripos` chỉ "không phân biệt hoa thường" với chữ ASCII.
`str_ireplace('VIỆT', 'X', 'việt Việt VIỆT')` cho `việt Việt X`: chữ `ệ` và `Ệ` là hai dãy byte khác
nhau, hàm không biết chúng là một chữ. Với tiếng Việt, dùng `mb_stripos` hoặc chuyển cả hai về chữ
thường bằng `mb_strtolower` trước khi so (mục 5.3).

### 4.4 Tách và ghép: `explode`, `implode`, `str_split`

`explode(string $separator, string $string, int $limit = PHP_INT_MAX): array` cắt chuỗi tại mỗi chỗ
có `$separator`. `implode(string $separator, array $array): string` làm ngược lại.

```php
<?php
declare(strict_types=1);

var_dump(explode(',', 'a,b,,c'));     // ["a", "b", "", "c"]   (giữ phần tử rỗng ở giữa)
var_dump(explode(',', ''));           // [""]   một phần tử rỗng, KHÔNG phải mảng rỗng
var_dump(explode(',', 'a,b,c', 2));   // ["a", "b,c"]   ($limit dương: tối đa 2 phần, phần cuối giữ phần còn lại)
var_dump(explode(',', 'a,b,c', -1));  // ["a", "b"]     ($limit âm: bỏ 1 phần ở cuối)

echo implode(', ', ['a', 'b', 'c']), "\n";        // in ra: a, b, c
echo implode(', ', []), "|\n";                    // in ra: |   (mảng rỗng cho chuỗi rỗng)
echo implode(',', [1, 2.5, true, null]), "\n";    // in ra: 1,2.5,1,   (true thành "1", null thành "")

try {
    explode('', 'abc');
} catch (ValueError $e) {
    echo $e->getMessage(), "\n";   // in ra: explode(): Argument #1 ($separator) must not be empty
}                                  // (PHP 8.3 trở về trước ghi "cannot be empty")
```

(Để gọn, comment ở bốn dòng `var_dump` đầu ghi kết quả theo cú pháp mảng thay vì output đầy đủ của
`var_dump`.)

⚠️ `explode(',', '')` trả về `[""]` (mảng một phần tử), nên `count(explode(',', $tags))` với
`$tags` rỗng ra `1` chứ không phải `0`. Kiểm tra chuỗi rỗng trước khi tách.

Lịch sử phiên bản: từ PHP 8.0, `explode` với separator rỗng ném `ValueError` (trước đó trả `false`),
và `implode` không còn nhận thứ tự tham số cũ `implode($array, $separator)`.

`str_split($s, $length = 1)` cắt thành các mảnh dài `$length` byte: `str_split('abcde', 2)` cho
`["ab", "cd", "e"]`. Với chuỗi có dấu, `str_split('Việt')` cắt chữ `ệ` thành ba byte rời; dùng
`mb_str_split` (mục 5.3). Từ PHP 8.2, `str_split('')` trả về mảng rỗng (trước đó là `[""]`).

### 4.5 Cắt khoảng trắng: `trim`, `ltrim`, `rtrim`

`trim()` bỏ ký tự thừa ở hai đầu chuỗi; `ltrim()` chỉ đầu trái, `rtrim()` chỉ cuối phải. Đây là
bước quen thuộc khi xử lý dữ liệu người dùng nhập (form, file CSV). Mặc định, `trim` bỏ 6 ký tự: dấu
cách `" "`, `"\t"`, `"\n"`, `"\r"`, `"\0"` và `"\v"`.

```php
<?php
declare(strict_types=1);

var_dump(trim("  \t xin chào \n"));   // in ra: string(9) "xin chào"
var_dump(ltrim('  abc  '));          // in ra: string(5) "abc  "
var_dump(rtrim('  abc  '));          // in ra: string(5) "  abc"

// Tham số thứ hai: TẬP HỢP ký tự cần bỏ, không phải một chuỗi con
var_dump(trim('0012300', '0'));              // in ra: string(3) "123"
var_dump(trim('[abc]', '[]'));               // in ra: string(3) "abc"
var_dump(trim("\x01\x02abc\x1F", "\x00..\x1F")); // in ra: string(3) "abc"   (dùng .. cho một dải)
var_dump(rtrim('graph.php', '.php'));        // in ra: string(3) "gra"   (BẪY!)

// NBSP (U+00A0) không nằm trong danh sách mặc định
var_dump(bin2hex(trim("\u{00A0}abc\u{00A0}")));   // in ra: string(14) "c2a0616263c2a0"
```

⚠️ `rtrim('graph.php', '.php')` không phải "bỏ đuôi `.php`". Tham số thứ hai là một **tập ký tự**
`{., p, h}`; `rtrim` bỏ mọi ký tự thuộc tập đó ở cuối cho tới khi gặp ký tự khác, nên ăn luôn `ph`
của chữ `graph`. Muốn bỏ một hậu tố, kiểm tra rồi cắt:

```php
<?php
declare(strict_types=1);

$file = 'graph.php';
if (str_ends_with($file, '.php')) {
    $file = substr($file, 0, -strlen('.php'));
}
echo $file, "\n";   // in ra: graph
```

(Với đường dẫn file cụ thể, `basename('graph.php', '.php')` cũng cho `graph`.)

⚠️ `trim` không bỏ các khoảng trắng Unicode như *no-break space* (U+00A0, hay gặp khi copy từ web
hoặc Word) và khoảng trắng toàn khổ U+3000. Dữ liệu trông như có dấu cách thừa mà `trim` không xoá
được thì nghi ngay tới chúng. PHP 8.4 có `mb_trim` xử lý được (mục 5.3).

### 4.6 Chữ hoa, chữ thường

| Hàm | Việc | Ví dụ |
|---|---|---|
| `strtolower` | về chữ thường | `strtolower('ABC')` → `abc` |
| `strtoupper` | về chữ hoa | `strtoupper('abc')` → `ABC` |
| `ucfirst` | viết hoa chữ đầu chuỗi | `ucfirst('hello world')` → `Hello world` |
| `lcfirst` | viết thường chữ đầu chuỗi | `lcfirst('Hello')` → `hello` |
| `ucwords` | viết hoa chữ đầu mỗi từ | `ucwords('nguyễn văn an')` → `Nguyễn Văn An` |

Từ PHP 8.2, các hàm này không phụ thuộc locale nữa và chỉ đổi chữ ASCII `A`-`Z`/`a`-`z`. Byte của
chữ có dấu được giữ nguyên:

```php
<?php
declare(strict_types=1);

var_dump(strtolower('XIN CHÀO VIỆT NAM'));  // in ra: string(20) "xin chÀo viỆt nam"
var_dump(ucfirst('élan'));                  // in ra: string(5) "élan"   (é không đổi)
var_dump(ucwords('đặng thị ánh'));          // in ra: string(18) "đặng Thị ánh"
var_dump(mb_strtolower('XIN CHÀO VIỆT NAM')); // in ra: string(20) "xin chào việt nam"
```

`ucwords('nguyễn văn an')` trông đúng chỉ vì chữ cái đầu mỗi từ tình cờ là ASCII. Gặp tên bắt đầu bằng
`đ`, `á`, `ơ`... thì sai. Với tiếng Việt, luôn dùng bản `mb_*` (mục 5.3).

### 4.7 Lặp, đệm, đảo: `str_repeat`, `str_pad`, `strrev`

```php
<?php
declare(strict_types=1);

var_dump(str_repeat('=-', 5));                  // in ra: string(10) "=-=-=-=-=-"
var_dump(str_pad('42', 5, '0', STR_PAD_LEFT));  // in ra: string(5) "00042"
var_dump(str_pad('ab', 6, '*', STR_PAD_BOTH));  // in ra: string(6) "**ab**"
var_dump(str_pad('abc', 6));                    // in ra: string(6) "abc   "  (mặc định đệm dấu cách bên phải)
var_dump(str_pad('abcdef', 3));                 // in ra: string(6) "abcdef"  (đã đủ dài thì giữ nguyên, không cắt)
var_dump(strrev('abc'));                        // in ra: string(3) "cba"
var_dump(bin2hex(strrev('ệ')));                 // in ra: string(6) "87bbe1"  (đảo byte: chữ ệ bị phá hỏng)
```

`str_pad` đếm byte (giống `sprintf`), nên căn cột với chữ có dấu sẽ lệch. `strrev` đảo byte, với
UTF-8 thì cho ra chuỗi hỏng. PHP không có `mb_strrev`; muốn đảo chuỗi Unicode, tách bằng
`mb_str_split`, đảo mảng bằng `array_reverse`, rồi `implode`.

Hai hàm liên quan tới HTML là `htmlspecialchars` (escape khi in ra HTML) và `strip_tags`; chúng thuộc
về chủ đề bảo mật và được bàn ở chương 17.

## 5. Multibyte, UTF-8 và tiếng Việt

Mục này trả lời câu hỏi mở đầu chương: vì sao `strlen('Việt')` là 6 trong khi mắt ta thấy 4 chữ, và
phải làm gì để xử lý tiếng Việt cho đúng.

### 5.1 Ký tự, code point và encoding

Ba khái niệm cần tách bạch:

- *Unicode* là một bảng đánh số cho gần như mọi ký tự của mọi chữ viết. Mỗi ký tự có một số gọi là
  *code point*, viết dạng `U+` cộng số hex: `A` là U+0041, `ệ` là U+1EC7, `₫` là U+20AB, `😀` là U+1F600.
- *Encoding* (bảng mã, cách mã hoá) là quy tắc biến code point thành byte để lưu và truyền đi.
  Một code point, nhiều cách biểu diễn.
- *UTF-8* là encoding phổ biến nhất hiện nay: web, JSON, MySQL `utf8mb4`, file mã nguồn PHP đều dùng.

UTF-8 dùng từ 1 tới 4 byte cho mỗi code point. Code point càng lớn thì càng nhiều byte:

| Khoảng code point | Số byte | Ví dụ | Byte UTF-8 (hex) |
|---|---|---|---|
| U+0000 tới U+007F (ASCII) | 1 | `A` (U+0041) | `41` |
| U+0080 tới U+07FF | 2 | `à` (U+00E0), `đ` (U+0111), `ư` (U+01B0) | `c3a0`, `c491`, `c6b0` |
| U+0800 tới U+FFFF | 3 | `ệ` (U+1EC7), `₫` (U+20AB) | `e1bb87`, `e282ab` |
| U+10000 tới U+10FFFF | 4 | `😀` (U+1F600) | `f09f9880` |

Tiếng Việt trộn cả ba loại đầu: chữ không dấu 1 byte, phần lớn chữ một dấu (`à`, `á`, `đ`, `ơ`, `ư`,
`ă`...) 2 byte, chữ hai dấu và một số chữ khác (`ệ`, `ễ`, `ọ`, `ở`...) 3 byte. Vì thế không có công thức
nào đổi số byte ra số chữ: `'Nguyễn'` là 8 byte cho 6 chữ, `'Học PHP ở Việt Nam'` là 24 byte cho 18 chữ.

Bạn có thể tự kiểm bảng trên bằng `mb_ord()` (code point của một ký tự) và `bin2hex()`:

```php
<?php
declare(strict_types=1);

foreach (['A', 'đ', 'ệ', '😀'] as $c) {
    printf("%s U+%04X %d byte: %s\n", $c, mb_ord($c), strlen($c), bin2hex($c));
}
// in ra:
// A U+0041 1 byte: 41
// đ U+0111 2 byte: c491
// ệ U+1EC7 3 byte: e1bb87
// 😀 U+1F600 4 byte: f09f9880
```

Cấu trúc byte của UTF-8 có một tính chất rất quan trọng cho phần sau:

```
1 byte : 0xxxxxxx                              (ASCII, 00..7F)
2 byte : 110xxxxx 10xxxxxx
3 byte : 1110xxxx 10xxxxxx 10xxxxxx
4 byte : 11110xxx 10xxxxxx 10xxxxxx 10xxxxxx
         └ byte đầu ┘ └──── byte tiếp theo, luôn dạng 10xxxxxx ────┘
```

Byte đầu của mỗi ký tự và các byte tiếp theo có dạng khác nhau, và byte ASCII không bao giờ xuất hiện
bên trong một ký tự nhiều byte. Nhờ thiết kế này, tìm một chuỗi UTF-8 hợp lệ bên trong một chuỗi UTF-8
hợp lệ bằng cách so từng byte không thể khớp nhầm vào giữa một ký tự.

### 5.2 Khi nào hàm byte làm hỏng dữ liệu, khi nào vẫn an toàn

Hàm byte **sai** khi nó cần biết "một chữ dài bao nhiêu byte": đếm, cắt theo vị trí, đảo, đệm, đổi
hoa thường. Ví dụ hay gặp nhất là cắt đoạn trích (excerpt) cho tiêu đề:

```php
<?php
declare(strict_types=1);

$title = 'Học PHP ở Việt Nam';
echo strlen($title), ' ', mb_strlen($title), "\n";   // in ra: 24 18

$cut = substr($title, 0, 12);                  // cắt 12 BYTE: rơi vào giữa chữ "ở"
var_dump(mb_check_encoding($cut, 'UTF-8'));    // in ra: bool(false)   (không còn là UTF-8 hợp lệ)
var_dump(json_encode(['title' => $cut]));      // in ra: bool(false)
echo json_last_error_msg(), "\n";              // in ra: Malformed UTF-8 characters, possibly incorrectly encoded

var_dump(mb_substr($title, 0, 12));            // in ra: string(16) "Học PHP ở Vi"   (12 KÝ TỰ)
```

Một chuỗi bị cắt hỏng sẽ gây lỗi ở nơi khác, xa chỗ gây ra nó: `json_encode` trả `false` (API trả về
rỗng), trình duyệt hiện ký tự `�`, MySQL có thể từ chối ghi với lỗi `Incorrect string value`. Rất khó
lần ngược ra một dòng `substr` ở tận đâu đó. Tương tự, kiểm tra "tên tối đa 50 ký tự" bằng `strlen`
sẽ chặn nhầm tên tiếng Việt ngắn hơn 50 chữ (cột `VARCHAR(50)` của MySQL đếm theo ký tự, không theo byte).

Hàm byte vẫn **an toàn** khi chỉ tìm, thay, tách theo một chuỗi UTF-8 hợp lệ: `str_contains`,
`str_starts_with`, `str_ends_with`, `strpos`, `str_replace`, `explode`. Nhờ tính chất UTF-8 ở mục 5.1,
`explode(', ', 'Hà Nội, Đà Nẵng')` hay `str_replace('Sài Gòn', 'TP.HCM', $s)` cho kết quả đúng.

⚠️ Nhưng vị trí mà `strpos` trả về là vị trí byte. Đừng trộn vị trí byte với hàm đếm theo ký tự:

```php
<?php
declare(strict_types=1);

$s = 'Việt Nam';
var_dump(strpos($s, 'Nam'), mb_strpos($s, 'Nam'));  // in ra: int(7) int(5)   (byte 7, ký tự thứ 5)
var_dump(mb_substr($s, strpos($s, 'Nam')));         // in ra: string(1) "m"     (SAI: trộn byte với ký tự)
var_dump(substr($s, strpos($s, 'Nam')));            // in ra: string(3) "Nam"   (byte đi với byte)
var_dump(mb_substr($s, mb_strpos($s, 'Nam')));      // in ra: string(3) "Nam"   (ký tự đi với ký tự)
```

(`var_dump` với nhiều tham số in mỗi giá trị trên một dòng; comment ghi gộp cho gọn.)

### 5.3 Extension mbstring

*mbstring* (multibyte string) là extension cung cấp các hàm `mb_*` làm việc theo ký tự thay vì
byte. Về cài đặt: manual ghi mbstring là extension "non-default", nghĩa là tự biên dịch PHP từ mã nguồn
thì phải bật bằng `--enable-mbstring`. Image Docker chính thức và PHP của Homebrew đã bật sẵn; trên
Debian/Ubuntu, mbstring thường là một gói riêng (dạng `php8.x-mbstring`) phải cài thêm. Laravel liệt kê
mbstring trong yêu cầu bắt buộc của server. Kiểm tra bằng `php -m | grep mbstring`.

Bảng đối chiếu hàm byte và hàm theo ký tự:

| Hàm byte | Bản theo ký tự | Ghi chú |
|---|---|---|
| `strlen` | `mb_strlen` | |
| `substr` | `mb_substr` | |
| `strpos`, `stripos`, `strrpos` | `mb_strpos`, `mb_stripos`, `mb_strrpos` | `mb_stripos` không phân biệt hoa thường cả với chữ có dấu |
| `strtolower`, `strtoupper` | `mb_strtolower`, `mb_strtoupper` | |
| `ucwords` | `mb_convert_case($s, MB_CASE_TITLE)` | |
| `ucfirst`, `lcfirst` | `mb_ucfirst`, `mb_lcfirst` | từ PHP 8.4 |
| `str_split` | `mb_str_split` | từ PHP 7.4 |
| `str_pad` | `mb_str_pad` | từ PHP 8.3 |
| `trim`, `ltrim`, `rtrim` | `mb_trim`, `mb_ltrim`, `mb_rtrim` | từ PHP 8.4, mặc định bỏ cả khoảng trắng Unicode |
| `substr_count` | `mb_substr_count` | |
| `strrev` | (không có) | tự làm bằng `mb_str_split` + `array_reverse` + `implode` |

```php
<?php
declare(strict_types=1);

$s = 'Việt Nam';
var_dump(mb_strlen($s));                               // in ra: int(8)
var_dump(mb_substr($s, 0, 3));                         // in ra: string(5) "Việ"
var_dump(mb_substr($s, -3));                           // in ra: string(3) "Nam"
var_dump(mb_strtoupper('đặng thị ánh'));               // in ra: string(18) "ĐẶNG THỊ ÁNH"
var_dump(mb_convert_case('đặng thị ánh', MB_CASE_TITLE)); // in ra: string(18) "Đặng Thị Ánh"
var_dump(mb_stripos('Học PHP ở VIỆT NAM', 'việt'));    // in ra: int(10)
var_dump(mb_str_split('Việt'));                        // ["V", "i", "ệ", "t"]
var_dump(mb_str_pad('Việt', 6, '.'));                  // in ra: string(8) "Việt.."     (PHP 8.3+)
var_dump(mb_trim("\u{00A0} abc \u{3000}"));            // in ra: string(3) "abc"        (PHP 8.4+)
var_dump(mb_ucfirst('đặng'));                          // in ra: string(7) "Đặng"       (PHP 8.4+)
var_dump(mb_strimwidth('Xin chào Việt Nam', 0, 10, '...')); // in ra: string(11) "Xin chà..."
```

Vài điều cần biết khi dùng `mb_*`:

- Gần như mọi hàm `mb_*` có tham số cuối `$encoding`. Bỏ trống thì dùng `mb_internal_encoding()`, mặc
  định lấy từ ini `default_charset`, mà giá trị mặc định của `default_charset` là `"UTF-8"`. Cấu hình
  chuẩn thì không cần truyền; thư viện viết cho người khác dùng thì truyền `'UTF-8'` cho chắc.
- `mb_strimwidth` cắt theo độ rộng hiển thị (chữ Hán, Nhật tính 2 cột), hợp để rút gọn tiêu đề
  hiển thị. Laravel `Str::limit()` dùng chính `mb_strwidth`/`mb_strimwidth`, còn `Str::length()` gọi
  `mb_strlen`.
- UTF-8 có độ dài thay đổi, nên muốn tới ký tự thứ `n` thì phải đi qua `n` ký tự trước đó. Gọi
  `mb_substr($s, $i, 1)` trong vòng lặp qua một chuỗi dài vì thế chậm dần theo `$i`; cần duyệt từng
  ký tự thì gọi `mb_str_split($s)` một lần rồi `foreach`.

### 5.4 Kiểm tra và chuyển encoding

Dữ liệu từ bên ngoài (form, file người dùng upload, API của bên thứ ba, file CSV xuất từ phần mềm cũ)
không chắc là UTF-8 hợp lệ. Nguyên tắc: **kiểm tra ở biên hệ thống**, ngay khi dữ liệu đi vào, rồi
bên trong ứng dụng chỉ làm việc với UTF-8 hợp lệ.

```php
<?php
declare(strict_types=1);

$input = "Vi\xE1";                              // UTF-8 hỏng (mất 2 byte cuối của chữ ệ)
var_dump(mb_check_encoding($input, 'UTF-8'));   // in ra: bool(false)
var_dump(mb_check_encoding('Việt', 'UTF-8'));   // in ra: bool(true)
var_dump(mb_scrub($input));                     // in ra: string(3) "Vi?"   (thay byte hỏng bằng ?)

$latin1 = "caf\xE9";                            // "café" ở bảng mã ISO-8859-1: é là 1 byte E9
var_dump(mb_check_encoding($latin1, 'UTF-8'));  // in ra: bool(false)
$utf8 = mb_convert_encoding($latin1, 'UTF-8', 'ISO-8859-1');
var_dump($utf8, bin2hex($utf8));                // in ra: string(5) "café" và string(10) "636166c3a9"
```

- `mb_check_encoding($s, 'UTF-8')`: chuỗi có phải UTF-8 hợp lệ không. Dữ liệu không hợp lệ thì từ chối
  (báo lỗi cho người dùng) hoặc làm sạch bằng `mb_scrub`, tuỳ nghiệp vụ.
- `mb_convert_encoding($s, $to, $from)`: chuyển giữa các bảng mã. Phải biết chắc bảng mã nguồn;
  đoán sai thì ra chữ lỗi (*mojibake*) mà không có thông báo nào. `iconv($from, $to, $s)` là lựa chọn
  khác, dùng thư viện iconv của hệ thống.
- `utf8_encode()` và `utf8_decode()` đã deprecated từ PHP 8.2. Tên gây hiểu nhầm: chúng chỉ chuyển
  giữa ISO-8859-1 và UTF-8, không "sửa" được chuỗi bảng mã khác. Code cũ dùng chúng thì thay bằng
  `mb_convert_encoding`.
- Excel trên Windows hay thêm *BOM* (3 byte `\xEF\xBB\xBF`) vào đầu file UTF-8. Khi đọc file, kiểm tra
  bằng `str_starts_with($line, "\xEF\xBB\xBF")` rồi cắt bỏ; chương 14 nói thêm về đọc CSV.

### 5.5 Grapheme: "chữ" mà người dùng nhìn thấy

`mb_strlen` đếm code point. Nhưng một "chữ" trên màn hình có thể gồm nhiều code point. Unicode gọi
đơn vị mà người đọc cảm nhận là một chữ là *grapheme cluster*. Hai ví dụ:

- Emoji gia đình 👨‍👩‍👧 gồm 5 code point: ba emoji người nối bằng hai ký tự vô hình *zero width joiner*
  (U+200D). Hiển thị là một hình.
- Chữ `ệ` có thể được viết bằng 3 code point: chữ `e` cộng hai *dấu kết hợp* (combining mark) là dấu
  nặng U+0323 và dấu mũ U+0302 (xem mục 5.6).

Extension `intl` có các hàm `grapheme_*` đếm và cắt theo grapheme:

```php
<?php
declare(strict_types=1);

// Cần extension intl
$family = "\u{1F468}\u{200D}\u{1F469}\u{200D}\u{1F467}";   // 👨‍👩‍👧
var_dump(strlen($family), mb_strlen($family), grapheme_strlen($family));
// in ra: int(18), int(5), int(1)   (byte, code point, grapheme)

$nfd = "Vi\u{0065}\u{0323}\u{0302}t";                       // "Việt" viết bằng dấu kết hợp
var_dump(mb_strlen($nfd), grapheme_strlen($nfd));           // in ra: int(6), int(4)
var_dump(mb_substr($nfd, 0, 3));                            // in ra: string(3) "Vie"    (mất dấu!)
var_dump(grapheme_substr($nfd, 0, 3));                      // in ra: string(7) "Việ"    (vẫn ở dạng tách dấu)
```

Với văn bản tiếng Việt thông thường (đã chuẩn hoá NFC, mục 5.6) và không có emoji, `mb_*` là đủ. Khi
giới hạn độ dài hoặc cắt chuỗi do người dùng nhập tự do (tên hiển thị, bio, bình luận có emoji), dùng
`grapheme_*` để không cắt đôi một emoji hay tách dấu khỏi chữ.

### 5.6 Chuẩn hoá Unicode với `Normalizer`

Unicode cho phép cùng một chữ được viết bằng nhiều dãy code point khác nhau. Chữ `ệ`:

```
Dạng dựng sẵn (NFC):  ệ = U+1EC7                       → 3 byte: e1 bb 87
Dạng tách dấu (NFD):  ệ = U+0065  U+0323     U+0302    → 5 byte: 65 cc a3 cc 82
                          (e)    (dấu nặng) (dấu mũ)
```

Hai dạng hiển thị giống hệt nhau, nhưng là hai dãy byte khác nhau, nên `===`, `strpos`, `str_replace`
và key của array đều coi chúng là khác nhau (trong database thì tuỳ collation của cột). Unicode định nghĩa các
*dạng chuẩn* (*normalization form*), trong đó hai dạng hay dùng:

- *NFC* (Canonical Composition): ghép thành ký tự dựng sẵn khi có thể. Đây là dạng phổ biến trên web
  và là dạng nên dùng để lưu trữ.
- *NFD* (Canonical Decomposition): tách hết thành chữ gốc cộng dấu kết hợp, các dấu được xếp theo một
  thứ tự chuẩn (vì vậy dấu nặng U+0323 đứng trước dấu mũ U+0302).

Văn bản dạng tách dấu có thể đến từ nhiều nguồn: tên file tạo trên macOS (hệ thống file HFS+ cũ lưu
tên file ở dạng tách dấu), bộ gõ được cấu hình bảng mã tổ hợp, nội dung copy từ PDF. Bạn không kiểm
soát được nguồn, nên hãy chuẩn hoá ở biên hệ thống. Class `Normalizer` của extension `intl` làm việc này:

```php
<?php
declare(strict_types=1);

// Cần extension intl
$nfc = "Vi\u{1EC7}t";                    // ệ dựng sẵn
$nfd = "Vi\u{0065}\u{0323}\u{0302}t";    // e + dấu nặng + dấu mũ

echo $nfc, ' ', $nfd, "\n";              // in ra: Việt Việt   (nhìn giống hệt)
var_dump($nfc === $nfd);                 // in ra: bool(false)
var_dump(strlen($nfc), strlen($nfd));    // in ra: int(6), int(8)
var_dump(str_contains($nfd, 'ệ'));       // in ra: bool(false)  ('ệ' gõ trong file này là NFC)

var_dump(Normalizer::isNormalized($nfd, Normalizer::FORM_C));  // in ra: bool(false)
$fixed = Normalizer::normalize($nfd, Normalizer::FORM_C);
var_dump($fixed === $nfc);               // in ra: bool(true)

var_dump(Normalizer::normalize("Vi\xE1")); // in ra: bool(false)   (đầu vào không phải UTF-8 hợp lệ)
```

- `Normalizer::normalize($s, $form)` trả về chuỗi đã chuẩn hoá, hoặc `false` nếu lỗi (ví dụ đầu vào
  không phải UTF-8 hợp lệ). Bỏ trống `$form` thì mặc định là `Normalizer::FORM_C`. Có dạng hàm thường
  `normalizer_normalize()`.
- Thứ tự hợp lý khi nhận dữ liệu: kiểm tra UTF-8 hợp lệ → chuẩn hoá NFC → `trim` → validate → lưu.
- Ngoài NFC/NFD còn NFKC/NFKD (*compatibility*), gộp cả những ký tự "tương đương về nghĩa": chữ toàn
  khổ `ｈｅｌｌｏ` thành `hello`, `①` thành `1`. Hữu ích khi chuẩn hoá username hay từ khoá tìm kiếm,
  nhưng làm mất thông tin, nên đừng áp lên nội dung bài viết.

## 6. So sánh và sắp xếp chuỗi

### 6.1 `===` và `==` với chuỗi

`$a === $b` với hai string nghĩa là: cùng độ dài và giống nhau từng byte. Đây là cách so sánh
chuỗi nên dùng mặc định.

`==` có một bẫy riêng với chuỗi: nếu cả hai đều là *numeric string* (chuỗi trông như số), PHP so
sánh chúng như số:

```php
<?php
declare(strict_types=1);

var_dump('1e3' == '1000');    // in ra: bool(true)    (1e3 là 1000 viết kiểu khoa học)
var_dump('10' == '010');      // in ra: bool(true)
var_dump('0.0' == '0');       // in ra: bool(true)
var_dump('abc' == 'ABC');     // in ra: bool(false)
var_dump('1e3' === '1000');   // in ra: bool(false)   (khác byte)
```

Mã đơn hàng `'010'` và `'10'`, hay hai mã băm mật khẩu cùng dạng `'0e...'`, có thể bị `==` coi là bằng
nhau. Quy tắc đầy đủ về so sánh lỏng nằm ở chương 04; với chuỗi, cứ dùng `===`. Khi so sánh chuỗi bí
mật (token, chữ ký), dùng `hash_equals()` để tránh *timing attack* (chương 17).

### 6.2 Họ `strcmp`: so sánh thứ tự

Khi cần biết chuỗi nào "đứng trước" (để sắp xếp), dùng `strcmp($a, $b)`. Kết quả là số âm nếu
`$a` đứng trước, `0` nếu bằng nhau, số dương nếu `$a` đứng sau.

```php
<?php
declare(strict_types=1);

var_dump(strcmp('a', 'b') < 0);              // in ra: bool(true)   ('a' đứng trước 'b')
var_dump(strcmp('b', 'a') > 0);              // in ra: bool(true)
var_dump(strcmp('a', 'a'));                  // in ra: int(0)
var_dump(strcmp('Z', 'a') < 0);              // in ra: bool(true)   ('Z' là byte 0x5A, 'a' là 0x61)
var_dump(strcasecmp('HELLO', 'hello'));      // in ra: int(0)       (không phân biệt hoa thường, chỉ ASCII)
var_dump(strcasecmp('VIỆT', 'việt') === 0);  // in ra: bool(false)  (Ệ và ệ không được coi là một)
var_dump(strncmp('abcd', 'abxy', 2));        // in ra: int(0)       (chỉ so 2 byte đầu)
```

- Chỉ dựa vào dấu của kết quả, không dựa vào giá trị cụ thể. Manual ghi rõ không có ý nghĩa nào
  khác ngoài dấu. Trên thực tế, khi hai chuỗi khác nhau ở một byte nào đó, `strcmp` trả nguyên kết quả
  của hàm `memcmp` trong thư viện C, nên độ lớn có thể khác nhau giữa các nền tảng (máy thử của chương
  này cho `strcmp('Z', 'a')` là `-7`). Từ PHP 8.2, giá trị trả về khi hai chuỗi khác độ dài cũng đã
  thay đổi. Vì vậy các ví dụ ở đây chỉ in dấu của kết quả.
- Họ hàng: `strcasecmp` (không phân biệt hoa thường), `strncmp`/`strncasecmp` (chỉ so `n` byte đầu),
  `substr_compare`.
- `strcmp` so byte: mọi chữ hoa ASCII (0x41 tới 0x5A) đứng trước mọi chữ thường (0x61 tới 0x7A),
  nên `'Zoe'` đứng trước `'an'`.

⚠️ Toán tử `<`, `>`, `<=>` với hai chuỗi numeric sẽ so như số, khác với `strcmp`:

```php
<?php
declare(strict_types=1);

var_dump('10' <=> '9');            // in ra: int(1)       (so như số: 10 > 9)
var_dump(strcmp('10', '9') < 0);   // in ra: bool(true)   (so byte: '1' < '9')

$n = ['10', '9', '2', '1'];
sort($n);                      // mặc định SORT_REGULAR: numeric string so như số
echo implode(',', $n), "\n";   // in ra: 1,2,9,10
sort($n, SORT_STRING);         // ép so như chuỗi
echo implode(',', $n), "\n";   // in ra: 1,10,2,9
```

Một mảng mã sản phẩm như `['10', '9', 'A1']` có lúc so như số, lúc so như chuỗi; thứ tự kết quả rất
khó đoán. Khi sắp xếp chuỗi, hãy nói rõ ý định: `SORT_STRING`, hoặc `usort($arr, strcmp(...))`. Chi
tiết các hàm sắp xếp mảng ở chương 06.

### 6.3 So sánh "tự nhiên"

Con người đọc `img2` trước `img10`, nhưng so byte thì `'img10' < 'img2'` (vì `'1' < '2'`). So sánh tự
nhiên (*natural order*) coi dãy chữ số là một con số:

```php
<?php
declare(strict_types=1);

$files = ['img12.png', 'img10.png', 'img2.png', 'img1.png'];
sort($files);
echo implode(', ', $files), "\n";   // in ra: img1.png, img10.png, img12.png, img2.png
sort($files, SORT_NATURAL);
echo implode(', ', $files), "\n";   // in ra: img1.png, img2.png, img10.png, img12.png

var_dump(strnatcmp('img2', 'img10') < 0);  // in ra: bool(true)    (tự nhiên: 2 < 10)
var_dump(strcmp('img2', 'img10') < 0);     // in ra: bool(false)   (theo byte: '2' > '1')
```

Các công cụ: `strnatcmp`, `strnatcasecmp`, `natsort`, `natcasesort`, cờ `SORT_NATURAL` (kết hợp
`SORT_FLAG_CASE` để không phân biệt hoa thường).

### 6.4 Sắp xếp tiếng Việt: locale và `Collator`

Sắp xếp theo byte cho kết quả sai với tiếng Việt, vì byte đầu của `Á` (0xC3) và `Đ` (0xC4) lớn hơn mọi
chữ ASCII:

```php
<?php
declare(strict_types=1);

$names = ['Bình', 'An', 'Đức', 'Ánh', 'Dung', 'Zoe'];
sort($names);
echo implode(', ', $names), "\n";   // in ra: An, Bình, Dung, Zoe, Ánh, Đức
```

Thứ tự đúng theo bảng chữ cái tiếng Việt (a, ă, â, b, c, d, đ, e, ê...) phụ thuộc ngôn ngữ, gọi là
*collation* (quy tắc đối chiếu). Có hai cách tiếp cận trong PHP.

**Cách cũ: `setlocale` + `strcoll`.** `setlocale(LC_COLLATE, 'vi_VN.UTF-8')` rồi so bằng `strcoll`
(hoặc `sort($arr, SORT_LOCALE_STRING)`). Cách này mong manh:

- Locale phải được cài trên hệ điều hành của server. Image Docker gọn nhẹ thường không có
  `vi_VN.UTF-8`; `setlocale` trả về `false` và bạn có thể không để ý.
- Locale là trạng thái của cả tiến trình. Manual cảnh báo: trên server đa luồng, một script có thể
  bị đổi locale giữa chừng vì script khác chạy cùng tiến trình gọi `setlocale`.
- Từ PHP 8.0, locale lúc khởi động là `"C"`, không thừa hưởng từ biến môi trường nữa (từ PHP 8.1,
  riêng `LC_CTYPE` được đặt là `"C.UTF-8"` nếu hệ thống có; `LC_COLLATE` vẫn là `"C"`); muốn locale
  khác phải gọi `setlocale` tường minh.

**Cách nên dùng: `Collator` của extension intl.** `Collator` dùng dữ liệu collation của thư viện ICU,
không phụ thuộc locale của hệ điều hành:

```php
<?php
declare(strict_types=1);

// Cần extension intl
$names = ['Bình', 'An', 'Đức', 'Ánh', 'Dung', 'Zoe', 'Ơn', 'Ông'];
$vi = new Collator('vi_VN');
$vi->sort($names);
echo implode(', ', $names), "\n";   // in ra: An, Ánh, Bình, Dung, Đức, Ông, Ơn, Zoe

var_dump($vi->compare('Dung', 'Đức'));   // in ra: int(-1)   (d đứng trước đ)

// Dùng làm hàm so sánh cho usort
$people = ['Đức', 'Dung', 'An'];
usort($people, $vi->compare(...));
echo implode(', ', $people), "\n";  // in ra: An, Dung, Đức

// Locale khác thì thứ tự khác: tiếng Anh coi Đ gần như D
$en = ['Dung', 'Đức'];
(new Collator('en_US'))->sort($en);
echo implode(', ', $en), "\n";      // in ra: Đức, Dung

// Không phân biệt hoa thường: hạ "độ mạnh" (strength) xuống SECONDARY
$ci = new Collator('vi_VN');
$ci->setStrength(Collator::SECONDARY);
var_dump($ci->compare('Việt', 'VIỆT'));  // in ra: int(0)
var_dump($ci->compare('Việt', 'viet'));  // in ra: int(1)   (ê và e vẫn khác nhau)
```

Kết quả trên chạy với ICU 74; quy tắc collation đến từ dữ liệu đi kèm ICU, nên bản ICU khác có thể cho
kết quả khác ở vài trường hợp biên. Vài điều đáng chú ý:

- `Collator::sort()` sắp xếp mảng tại chỗ (truyền tham chiếu), giống `sort()`.
- *Strength* quyết định khác biệt nào được tính: mặc định (TERTIARY) tính cả dấu và hoa thường,
  SECONDARY bỏ qua hoa thường, PRIMARY bỏ qua thêm cả dấu. Thế nào là "dấu" do quy tắc của từng ngôn
  ngữ quyết định. Với `vi_VN` ở mức PRIMARY, dấu thanh bị bỏ qua (`'Ánh'` bằng `'anh'`, `'Việt'` bằng
  `'Viết'`), nhưng `ê` và `e`, `đ` và `d` là các chữ cái khác nhau trong bảng chữ cái tiếng Việt,
  nên `'Việt'` vẫn khác `'viet'`.
- `$c->setAttribute(Collator::NUMERIC_COLLATION, Collator::ON)` bật so sánh số kiểu tự nhiên
  (`img2` trước `img10`).

Database cũng có collation cho cột chuỗi (MySQL `utf8mb4_0900_ai_ci`...). Khi `ORDER BY` trong SQL
và `sort` trong PHP cho hai thứ tự khác nhau, nguyên nhân thường là hai bên dùng hai quy tắc collation
khác nhau.

## 7. Biểu thức chính quy (regex) với PCRE

### 7.1 Regex là gì, khi nào nên dùng

*Regular expression* (regex, biểu thức chính quy) là một ngôn ngữ nhỏ để mô tả mẫu của chuỗi:
"bắt đầu bằng `DH-`, tiếp theo 4 chữ số, một dấu gạch, rồi một hoặc nhiều chữ số". Với một mẫu, ta có
thể kiểm tra chuỗi có khớp không, rút ra các phần khớp, hoặc thay thế chúng.

PHP dùng thư viện *PCRE* (Perl Compatible Regular Expressions), cụ thể là PCRE2 từ PHP 7.3, qua họ
hàm `preg_*`. Hằng `PCRE_VERSION` cho biết phiên bản thư viện đang dùng.

Regex mạnh nhưng khó đọc và có bẫy riêng. Trước khi viết regex, hỏi xem đã có công cụ chuyên dụng chưa:

| Việc | Nên dùng | Thay vì |
|---|---|---|
| Chuỗi có chứa / bắt đầu / kết thúc bằng X | `str_contains`, `str_starts_with`, `str_ends_with` | `preg_match` (manual cũng khuyên vậy) |
| Kiểm tra email | `filter_var($s, FILTER_VALIDATE_EMAIL)` | regex tự viết |
| Tách URL | `parse_url` | regex |
| Đọc HTML/XML | DOM parser (`DOMDocument`...) | regex |
| Mẫu có cấu trúc: mã đơn, số điện thoại, ngày giờ trong log | regex | |

### 7.2 Viết pattern trong PHP: delimiter, cú pháp cơ bản, modifier

Pattern trong PHP là một chuỗi gồm ba phần: *delimiter* (ký tự mở), nội dung, delimiter đóng, rồi
các *modifier* (cờ) tuỳ chọn:

```
'/^DH-\d{4}-\d+$/u'
 │└─── mẫu ────┘│└ modifier
 └─ delimiter ──┘
```

- Delimiter có thể là bất kỳ ký tự một byte nào không phải chữ, số, `\`, NUL hay khoảng trắng. Hay
  dùng `/`, `#`, `~`. Cũng dùng được cặp ngoặc `()`, `{}`, `[]`, `<>`. Nếu mẫu chứa nhiều `/` (như URL),
  chọn `#` cho đỡ phải escape: `'#https?://#'` thay vì `'/https?:\/\//'`.
- Luôn viết pattern bằng nháy đơn. Trong nháy kép, PHP xử lý escape trước khi PCRE nhìn thấy
  pattern (`"\\d"`, `"\$"`...), rất dễ rối.

Cú pháp cơ bản đủ dùng cho phần lớn công việc:

| Ký hiệu | Khớp với |
|---|---|
| `abc` | đúng chuỗi `abc` |
| `.` | một ký tự bất kỳ trừ xuống dòng |
| `\d`, `\w`, `\s` | chữ số; chữ, số hoặc `_`; khoảng trắng |
| `\D`, `\W`, `\S` | phủ định của ba loại trên |
| `[abc]`, `[a-z]`, `[^0-9]` | một ký tự trong tập; trong dải; không thuộc tập |
| `^`, `$` | đầu chuỗi, cuối chuỗi (xem bẫy ở 7.6) |
| `\A`, `\z` | đầu chuỗi, cuối chuỗi tuyệt đối |
| `\b` | ranh giới từ |
| `*`, `+`, `?` | lặp 0 lần trở lên; 1 lần trở lên; 0 hoặc 1 lần |
| `{n}`, `{n,m}` | lặp đúng `n` lần; từ `n` tới `m` lần |
| `*?`, `+?` | như `*`, `+` nhưng lấy ít nhất có thể (*lazy*) |
| `(...)` | nhóm, đồng thời *capture* (lưu lại phần khớp) |
| `(?<ten>...)` | nhóm có tên |
| `a\|b` | `a` hoặc `b` |
| `\.`, `\(`, `\\` | ký tự đặc biệt được hiểu theo nghĩa đen |

Modifier hay dùng (theo manual):

| Modifier | Tác dụng |
|---|---|
| `i` | không phân biệt hoa thường |
| `m` | `^` và `$` khớp ở đầu và cuối mỗi dòng |
| `s` | `.` khớp cả ký tự xuống dòng |
| `x` | bỏ qua khoảng trắng và cho phép comment `#` trong pattern, giúp viết regex dài dễ đọc |
| `u` | pattern và chuỗi được xử lý như UTF-8 (mục 7.5) |
| `D` | `$` chỉ khớp ở cuối chuỗi tuyệt đối |

### 7.3 `preg_match` và `preg_match_all`: tìm và rút trích

`preg_match($pattern, $subject, &$matches = null, $flags = 0, $offset = 0): int|false` tìm lần khớp
đầu tiên. Trả về `1` nếu khớp, `0` nếu không, `false` nếu có lỗi. Nếu truyền `$matches`, PHP ghi
vào đó: `$matches[0]` là toàn bộ phần khớp, `$matches[1]` là nhóm thứ nhất, và cứ thế.

```php
<?php
declare(strict_types=1);

$text = 'Mã đơn: DH-2024-0042, khách: Lan';

if (preg_match('/DH-(\d{4})-(\d+)/', $text, $m) === 1) {
    echo $m[0], ' | ', $m[1], ' | ', $m[2], "\n";   // in ra: DH-2024-0042 | 2024 | 0042
}

// Nhóm có tên: dễ đọc hơn đếm số thứ tự
if (preg_match('/DH-(?<year>\d{4})-(?<seq>\d+)/', $text, $m) === 1) {
    echo $m['year'], ' ', $m['seq'], "\n";          // in ra: 2024 0042
}

var_dump(preg_match('/XYZ/', $text));               // in ra: int(0)
```

Với nhóm có tên, `$matches` chứa cả key tên (`'year'`) lẫn key số (`1`).

`preg_match_all` tìm mọi lần khớp và trả về số lần khớp. Mặc định (`PREG_PATTERN_ORDER`)
`$matches[1]` là mảng mọi giá trị của nhóm 1; cờ `PREG_SET_ORDER` gom theo từng lần khớp, thường tiện
hơn khi duyệt:

```php
<?php
declare(strict_types=1);

$log = 'GET /a 200; POST /b 500; GET /c 404';

$n = preg_match_all('/(GET|POST) (\S+) (\d{3})/', $log, $all);
echo $n, ': ', implode(', ', $all[2]), "\n";   // in ra: 3: /a, /b, /c

preg_match_all('/(GET|POST) (\S+) (\d{3})/', $log, $sets, PREG_SET_ORDER);
foreach ($sets as [$full, $method, $path, $code]) {
    echo "$method $path => $code\n";
}
// in ra:
// GET /a => 200
// POST /b => 500
// GET /c => 404
```

⚠️ Cờ `PREG_OFFSET_CAPTURE` trả kèm vị trí của mỗi phần khớp. Vị trí đó luôn tính bằng byte, kể cả
khi có modifier `u`. Muốn dùng với chuỗi tiếng Việt thì cắt bằng `substr`, không phải `mb_substr`
(nhớ lại mục 5.2).

### 7.4 `preg_replace`, `preg_replace_callback`, `preg_split`, `preg_quote`

```php
<?php
declare(strict_types=1);

// Gộp mọi cụm khoảng trắng (cách, tab, xuống dòng) thành một dấu cách
echo trim(preg_replace('/\s+/', ' ', "  Xin   chào\t\nbạn  ")), "\n";   // in ra: Xin chào bạn

// Tham chiếu ngược $1, $2... tới các nhóm
echo preg_replace('/(\d{4})-(\d{2})-(\d{2})/', '$3/$2/$1', 'Ngày 2026-10-03'), "\n";
// in ra: Ngày 03/10/2026

// BẪY: '$1000' bị hiểu là nhóm số 10 (không tồn tại) rồi tới "00"
echo preg_replace('/(\d+)/', '$1000', 'Giá 15'), "\n";     // in ra: Giá 00
echo preg_replace('/(\d+)/', '${1}000', 'Giá 15'), "\n";   // in ra: Giá 15000

// Phần thay thế cần tính toán: dùng callback
echo preg_replace_callback(
    '/\d+/',
    fn (array $m): string => (string) ((int) $m[0] * 2),
    'a1 b20 c300',
), "\n";                                                   // in ra: a2 b40 c600

// Tách theo nhiều loại dấu phân cách cùng lúc
print_r(preg_split('/[\s,;]+/', 'php, mysql;  redis   go', -1, PREG_SPLIT_NO_EMPTY));
// in ra: Array ( [0] => php [1] => mysql [2] => redis [3] => go )   (print_r in nhiều dòng)
```

Khi phải đưa một chuỗi do người dùng nhập vào pattern (ví dụ tìm kiếm từ khoá), luôn escape bằng
`preg_quote($s, $delimiter)`. Nếu không, các ký tự `.`, `*`, `?`, `(`... trong từ khoá sẽ được hiểu là cú
pháp regex: kết quả sai, pattern lỗi, hoặc tệ hơn là một pattern chạy rất chậm (mục 7.6).

```php
<?php
declare(strict_types=1);

echo preg_quote('a.b*c?'), "\n";         // in ra: a\.b\*c\?
echo preg_quote('1/2', '/'), "\n";       // in ra: 1\/2   (truyền delimiter để nó cũng được escape)

$keyword = 'a.b';
var_dump(preg_match('/' . preg_quote($keyword, '/') . '/', 'axb'));  // in ra: int(0)   (đúng)
var_dump(preg_match('/' . $keyword . '/', 'axb'));                   // in ra: int(1)   (sai: . khớp mọi ký tự)
```

### 7.5 Regex và UTF-8: modifier `u`

Không có modifier `u`, PCRE làm việc trên byte, giống các hàm string ở mục 4:

```php
<?php
declare(strict_types=1);

var_dump(preg_match_all('/./', 'Việt'));          // in ra: int(6)   (6 byte)
var_dump(preg_match_all('/./u', 'Việt'));         // in ra: int(4)   (4 ký tự)
var_dump(preg_match('/^\w+$/', 'Việt'));          // in ra: int(0)   (\w không nhận byte của chữ ệ)
var_dump(preg_match('/^\w+$/u', 'Việt'));         // in ra: int(1)
var_dump(preg_match('/việt/i', 'VIỆT'));          // in ra: int(0)
var_dump(preg_match('/việt/iu', 'VIỆT'));         // in ra: int(1)
var_dump(preg_match('/^\p{Lu}/u', 'Đức'));        // in ra: int(1)   (\p{Lu}: chữ cái viết hoa)
var_dump(preg_match('/^\d+$/u', '٣٤'));           // in ra: int(1)   (BẪY: chữ số Ả Rập cũng là \d)
var_dump(preg_match('/^[0-9]+$/u', '٣٤'));        // in ra: int(0)
```

Quy tắc: **chuỗi có thể chứa tiếng Việt thì thêm `u`**. Với `u`:

- `.` khớp một ký tự (code point), không phải một byte; `[à-ỹ]` hiểu đúng là dải ký tự.
- Khi gặp `u`, PHP bật cả hai tuỳ chọn `PCRE2_UTF` và `PCRE2_UCP` của PCRE2, nên `\w`, `\d`, `\s` hiểu
  theo Unicode: `\w` nhận chữ có dấu, còn `i` coi `ệ` và `Ệ` là một. Mặt trái: `\d` nhận cả chữ số của
  các hệ chữ viết khác. Khi kiểm tra "chỉ gồm chữ số 0 tới 9" (mã OTP, số tiền), viết rõ `[0-9]`.
- Có thêm các lớp ký tự Unicode: `\p{L}` (mọi chữ cái), `\p{Lu}` (chữ hoa), `\p{Mn}` (dấu kết hợp),
  và `\X` (một grapheme cluster, mục 5.5).
- Chuỗi không phải UTF-8 hợp lệ làm hàm trả về `false` (lỗi), không phải `0`. Manual ghi: "An invalid
  subject will cause the preg_* function to match nothing".

### 7.6 Cạm bẫy của regex

**1. Không phân biệt `false` (lỗi) với `0` (không khớp).** `preg_match` trả `false` khi pattern sai cú
pháp, chuỗi không phải UTF-8 hợp lệ (với `u`), hoặc vượt giới hạn backtracking. Viết
`if (preg_match(...))` thì lỗi bị nuốt im lặng như "không khớp". Với bộ lọc kiểu "chặn nếu khớp", đó
là lỗ hổng:

```php
<?php
declare(strict_types=1);

function hasLink(string $comment): bool
{
    return (bool) preg_match('#https?://#u', $comment);   // BẪY: false (lỗi) thành "không có link"
}

function hasLinkSafe(string $comment): bool
{
    $r = preg_match('#https?://#u', $comment);
    if ($r === false) {
        throw new RuntimeException('Regex lỗi: ' . preg_last_error_msg());
    }
    return $r === 1;
}

$spam = "Mua ngay http://spam.example \xFF";   // kẻ gửi spam chèn một byte không hợp lệ
var_dump(hasLink($spam));                      // in ra: bool(false)   (bộ lọc bị vượt qua!)
try {
    hasLinkSafe($spam);
} catch (RuntimeException $e) {
    echo $e->getMessage(), "\n";   // in ra: Regex lỗi: Malformed UTF-8 characters, possibly incorrectly encoded
}
```

So kết quả bằng `=== 1`, xử lý `false` riêng. `preg_last_error()` trả mã lỗi (so với các hằng
`PREG_BAD_UTF8_ERROR`, `PREG_BACKTRACK_LIMIT_ERROR`...), `preg_last_error_msg()` (từ PHP 8.0) trả
thông báo dễ đọc. Pattern sai cú pháp còn sinh Warning, ví dụ pattern `'/(abc/'` (thiếu ngoặc đóng) cho
`preg_match(): Compilation failed: missing closing parenthesis at offset 4`.

**2. `$` khớp cả trước ký tự xuống dòng cuối cùng.** Manual ghi rõ: không có modifier `D`, `$` khớp ở
cuối chuỗi hoặc ngay trước `\n` cuối chuỗi:

```php
<?php
declare(strict_types=1);

var_dump(preg_match('/^\d+$/', "123\n"));    // in ra: int(1)   (chuỗi có "\n" vẫn lọt qua!)
var_dump(preg_match('/^\d+\z/', "123\n"));   // in ra: int(0)
var_dump(preg_match('/^\d+$/D', "123\n"));   // in ra: int(0)
```

Một ID "đã kiểm tra là toàn chữ số" nhưng mang theo `\n` có thể gây lỗi khi đưa vào header HTTP, tên
file, dòng log. Khi validate toàn bộ chuỗi, dùng `\A...\z` hoặc thêm `D`.

**3. Quên neo `^`/`$`.** `preg_match('/\d{4}/', 'abc1234xyz')` trả `1` vì regex tìm ở bất kỳ đâu.
Kiểm tra "cả chuỗi là 4 chữ số" phải viết `'/\A[0-9]{4}\z/'`.

**4. Tham lam (greedy) và lười (lazy).** `*` và `+` mặc định lấy nhiều nhất có thể:

```php
<?php
declare(strict_types=1);

$html = '<b>một</b> và <b>hai</b>';
preg_match('/<b>(.*)<\/b>/', $html, $greedy);
preg_match('/<b>(.*?)<\/b>/', $html, $lazy);
var_dump($greedy[1]);   // in ra: string(20) "một</b> và <b>hai"
var_dump($lazy[1]);     // in ra: string(5) "một"
```

(Ví dụ chỉ để minh hoạ greedy/lazy; đọc HTML thật thì dùng DOM parser.)

**5. Catastrophic backtracking và ReDoS.** Khi một lần thử khớp thất bại, PCRE quay lui (*backtrack*)
để thử cách chia khác. Với pattern có lượng từ lồng nhau như `(a+)+`, số cách chia tăng theo hàm mũ với
độ dài chuỗi. Kẻ tấn công gửi một chuỗi được chọn kỹ để máy chủ tốn CPU vô ích, gọi là *ReDoS*
(Regular expression Denial of Service).

```php
<?php
declare(strict_types=1);

$input = str_repeat('a', 30) . 'b';
var_dump(preg_match('/^(a+)+$/', $input));        // in ra: bool(false)
echo preg_last_error_msg(), "\n";                 // in ra: Backtrack limit exhausted
var_dump(preg_match('/^a+$/', $input));           // in ra: int(0)   (cùng ý nghĩa, không lồng: trả lời ngay)
```

PHP đặt giới hạn qua ini `pcre.backtrack_limit` (mặc định `1000000`) và `pcre.recursion_limit` (mặc
định `100000`). Vượt giới hạn thì hàm trả về `false` thay vì chạy mãi, nhưng máy chủ vẫn đã tốn CPU tới
lúc chạm giới hạn, và bạn lại quay về bẫy số 1 (lỗi bị coi là "không khớp"). Output ở trên lấy từ một
bản PHP không bật JIT của PCRE. Với `pcre.jit` bật (mặc định), PHP vẫn áp cùng giới hạn
`pcre.backtrack_limit` cho JIT (thử pattern trên bằng PCRE2 có JIT cũng dừng vì vượt giới hạn), nên vẫn
nhận `false` và `Backtrack limit exhausted`; chỉ thời gian chạy tới lúc dừng là khác. Cách phòng:

- Tránh lượng từ lồng nhau và các nhánh chồng lấn nhau (`(a|a)*`, `(\w+\s?)+`...).
- Giới hạn độ dài đầu vào trước khi chạy regex.
- Không đưa chuỗi người dùng thẳng vào pattern: dùng `preg_quote`.
- Luôn kiểm tra kết quả `false`.

**6. Regex phức tạp không ai đọc nổi.** Dùng nhóm có tên, modifier `x` để xuống dòng và chú thích, hoặc
tách thành nhiều bước đơn giản. Viết test cho regex với cả trường hợp khớp lẫn không khớp.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| `if (strpos($s, 'abc'))` bỏ sót khi `abc` ở đầu chuỗi | `strpos` trả `0`, `if` coi `0` là sai | `str_contains`, hoặc so `!== false` (4.2) |
| Đếm, cắt, đệm, đảo chuỗi tiếng Việt bằng `strlen`, `substr`, `str_pad`, `strrev` | Các hàm này làm việc trên byte | Dùng `mb_*` tương ứng (5.3) |
| Cắt chuỗi bằng `substr` rồi `json_encode` trả `false` | Cắt giữa một ký tự nhiều byte, UTF-8 bị hỏng | `mb_substr`, `mb_strimwidth`; kiểm `mb_check_encoding` (5.2) |
| Trộn vị trí của `strpos` với `mb_substr` | Một bên tính byte, một bên tính ký tự | Byte đi với byte, ký tự đi với ký tự (5.2) |
| `'Dòng 1\nDòng 2'` không xuống dòng | Nháy đơn không xử lý `\n` | Nháy kép hoặc `PHP_EOL` (2.1) |
| `"$user->boss->name"` lỗi hoặc in sai | Cú pháp đơn giản chỉ đi một bước | `"{$user->boss->name}"` (2.3, 2.4) |
| `"${var}"` sinh Deprecated | Deprecated từ PHP 8.2 | `"{$var}"` (2.4) |
| `rtrim($file, '.php')` cắt mất chữ | Tham số thứ hai là tập ký tự, không phải chuỗi con | `str_ends_with` + `substr` (4.5) |
| `str_replace` với mảng thay dây chuyền | Các cặp được áp dụng tuần tự lên kết quả | `strtr` với mảng (4.3) |
| `count(explode(',', ''))` bằng 1 | `explode` trả `[""]` với chuỗi rỗng | Kiểm tra chuỗi rỗng trước (4.4) |
| `strtolower`, `ucfirst`, `stripos`, `str_ireplace` "không ăn" chữ có dấu | Từ PHP 8.2 chỉ đổi chữ ASCII | `mb_strtolower`, `mb_convert_case`, `mb_stripos` (4.6) |
| `trim` không xoá được "dấu cách" | Đó là NBSP U+00A0 hoặc khoảng trắng Unicode khác | Soi bằng `bin2hex`; `mb_trim` (8.4+) (4.5) |
| Hai chuỗi nhìn giống hệt nhau nhưng `===` là `false` | NFC và NFD, hoặc NBSP thay cho dấu cách | `Normalizer::normalize`, soi bằng `bin2hex` (5.6, 3.4) |
| Lấy kết quả `number_format` đi tính tiếp | Đó là chuỗi hiển thị, không phải numeric string | Chỉ định dạng ở bước in ra (3.4) |
| So sánh mã, token bằng `==` | Hai numeric string được so như số | `===`; chuỗi bí mật dùng `hash_equals` (6.1) |
| `sort()` tên tiếng Việt cho thứ tự sai | So theo byte | `Collator('vi_VN')` (6.4) |
| `if (preg_match(...))` cho qua dữ liệu xấu | Lỗi (`false`) bị coi như "không khớp" | So `=== 1`, xử lý `false` riêng (7.6) |
| `/^\d+$/` cho qua `"123\n"` hoặc `"٣٤"` | `$` khớp trước `\n` cuối; `\d` với `u` nhận chữ số Unicode | `/\A[0-9]+\z/` (7.5, 7.6) |
| Regex trên tiếng Việt cho kết quả lạ | Thiếu modifier `u`, PCRE làm việc trên byte | Thêm `u` (7.5) |
| `preg_replace(..., '$1000', ...)` ra kết quả lạ | `$10` được hiểu là nhóm số 10 | `'${1}000'` (7.4) |
| Nối từ khoá người dùng vào pattern | Ký tự đặc biệt thành cú pháp regex | `preg_quote($s, $delimiter)` (7.4) |

## Tóm tắt chương

- String trong PHP là dãy byte có kèm độ dài, binary-safe, không mang thông tin encoding. `strlen`
  đếm byte; chuỗi literal mang encoding của file nguồn, thường là UTF-8.
- Bốn cú pháp: nháy đơn (gần như nguyên văn), nháy kép (escape và chèn biến), heredoc (nháy kép nhiều
  dòng), nowdoc (nháy đơn nhiều dòng). Dùng `{$...}` cho mọi biểu thức phức tạp hơn một biến; `${var}`
  đã deprecated từ 8.2.
- Nối bằng `.`, `+` luôn là phép cộng. Từ PHP 8, `+`/`-` được tính trước `.`; vẫn nên đặt ngoặc.
  `sprintf` cho định dạng phức tạp, `number_format` để hiển thị số, kết quả chỉ để in.
- Bẫy kinh điển: `strpos` trả `0`, `trim` nhận tập ký tự, `str_replace` thay dây chuyền,
  `explode(',', '')` cho `[""]`.
- UTF-8 dùng 1 tới 4 byte cho một code point; tiếng Việt trộn 1, 2, 3 byte. Hàm đếm, cắt, đổi hoa
  thường phải dùng `mb_*`; hàm tìm, thay, tách theo chuỗi UTF-8 hợp lệ vẫn an toàn nhưng trả vị trí byte.
- Kiểm tra UTF-8 hợp lệ và chuẩn hoá NFC ở biên hệ thống (`mb_check_encoding`, `Normalizer`); dùng
  `grapheme_*` khi cần đúng "chữ" người dùng nhìn thấy.
- So sánh bằng `===`; `strcmp` chỉ dựa vào dấu của kết quả; numeric string bị so như số với `==`, `<`,
  `<=>` và `sort` mặc định. Sắp xếp tiếng Việt dùng `Collator`, không dùng `sort` hay `setlocale`.
- Regex: pattern nháy đơn, thêm `u` cho tiếng Việt, so kết quả `=== 1` và xử lý `false`, validate bằng
  `\A...\z`, escape input bằng `preg_quote`, tránh lượng từ lồng nhau để không bị ReDoS.

## Câu hỏi tự kiểm tra

1. Vì sao `strlen('Việt')` là 6 nhưng `mb_strlen('Việt')` là 4? `'Nguyễn'` dài bao nhiêu byte? Giải
   thích bằng cách nhìn output của `bin2hex`. (mục 1.1, 5.1)
2. `echo 'A\tB';` và `echo "A\tB";` in ra gì? Khi nào bạn chọn heredoc, khi nào nowdoc?
3. Dòng `echo "Sếp: $user->boss->name";` gặp lỗi gì và vì sao? Viết lại cho đúng. (mục 2.3)
4. Vì sao `if (strpos($email, 'admin'))` là bug? Viết lại theo hai cách khác nhau.
5. `rtrim('graph.php', '.php')` trả về gì? Vì sao? Viết cách bỏ đuôi `.php` đúng.
6. Những hàm byte nào vẫn cho kết quả đúng với chuỗi UTF-8 hợp lệ, và tính chất nào của UTF-8 làm điều
   đó đúng? Có bẫy gì khi dùng vị trí mà `strpos` trả về? (mục 5.1, 5.2)
7. Hai chuỗi `'Việt'` hiển thị giống hệt nhau nhưng `===` trả về `false`. Nêu ít nhất hai nguyên nhân
   có thể và cách bạn kiểm tra. (mục 3.4, 5.6)
8. Vì sao `sort()` xếp `'Ánh'` và `'Đức'` sau `'Zoe'`? Vì sao `Collator` đáng tin hơn
   `setlocale` + `strcoll` trên server? (mục 6.4)
9. `preg_match` trả về những giá trị nào? Vì sao `return (bool) preg_match(...)` nguy hiểm trong một bộ
   lọc chặn nội dung xấu? (mục 7.6)
10. Bạn validate mã OTP 6 chữ số bằng `'/^\d{6}$/u'`. Pattern này có những lỗ hổng nào? Viết lại cho
    chặt. (mục 7.5, 7.6)

## Bài tập

Mỗi bài là một file PHP chạy được bằng `php ten-file.php`. Tự in kết quả các trường hợp thử và đối
chiếu với kết quả mong đợi ghi trong đề.

**Bài 1. Đoạn trích an toàn.** Viết hàm
`excerpt(string $text, int $maxChars, string $suffix = '...'): string`:

- Nếu `$text` không dài quá `$maxChars` ký tự thì trả về nguyên văn.
- Nếu dài hơn, cắt sao cho kết quả (tính cả `$suffix`) không quá `$maxChars` ký tự, không cắt ngang
  một từ (lùi về dấu cách gần nhất), bỏ khoảng trắng thừa ở cuối, rồi thêm `$suffix`.
- Kết quả luôn là UTF-8 hợp lệ (tự kiểm bằng `mb_check_encoding`).

Thử với `'Học PHP ở Việt Nam thật là vui'` và `$maxChars` lần lượt là 10, 15, 100; với chuỗi rỗng;
với một từ dài hơn `$maxChars`. Ghi lại bạn đã chọn xử lý trường hợp cuối thế nào và vì sao.

**Bài 2. Slug tiếng Việt** (cần extension `intl`). Viết hàm `slugify(string $title): string` biến
tiêu đề thành đoạn URL: `'Học PHP ở Việt Nam!'` thành `'hoc-php-o-viet-nam'`,
`'  Đặng   Thị Ánh  '` thành `'dang-thi-anh'`. Yêu cầu: chuẩn hoá Unicode trước, bỏ dấu, xử lý riêng
chữ `đ`/`Đ` (vì sao `đ` không tách được thành `d` + dấu?), chữ thường, mọi cụm ký tự không phải
`a-z0-9` thành một dấu `-`, không có `-` ở hai đầu. Thử thêm với một chuỗi được viết ở dạng NFD (dựng
bằng `"\u{...}"`) và kiểm tra kết quả giống dạng NFC.

**Bài 3. Đọc log bằng regex.** Cho mảng các dòng log dạng
`2026-10-03 12:00:01 [ERROR] user=42 msg="Không kết nối được DB"`. Viết code:

- Dùng `preg_match` với nhóm có tên để rút `date`, `time`, `level`, `user`, `msg`.
- Đếm số dòng theo `level`, in ra theo thứ tự giảm dần.
- Dòng không khớp mẫu thì đưa vào danh sách "không đọc được"; dòng làm `preg_match` trả `false` (dùng
  pattern có modifier `u` và thử chèn một dòng chứa byte `"\xFF"`) thì in thông báo từ
  `preg_last_error_msg()`. Ba trường hợp khớp,
  không khớp, lỗi phải được xử lý tách biệt.

**Bài 4. Danh bạ tiếng Việt** (cần extension `intl`). Cho mảng họ tên đầy đủ, ví dụ
`['Nguyễn Văn An', 'Trần Thị Ánh', 'Lê Đức', 'Phạm Dung', 'Đỗ Bình', 'nguyễn văn an']`. Sắp xếp theo
tên (từ cuối cùng) rồi tới họ và tên đệm, theo thứ tự chữ cái tiếng Việt. Coi hai tên chỉ khác
nhau về hoa thường là trùng nhau và chỉ giữ một. In kết quả của `sort()` thường và của cách làm của bạn
cạnh nhau, giải thích chỗ khác nhau.

## Đọc thêm

- PHP Manual, [Strings](https://www.php.net/manual/en/language.types.string.php): cú pháp literal,
  interpolation, offset, chi tiết kiểu string và encoding.
- PHP Manual, [String Functions](https://www.php.net/manual/en/ref.strings.php), và các trang
  [sprintf](https://www.php.net/manual/en/function.sprintf.php),
  [number_format](https://www.php.net/manual/en/function.number-format.php),
  [trim](https://www.php.net/manual/en/function.trim.php),
  [strpos](https://www.php.net/manual/en/function.strpos.php),
  [strtr](https://www.php.net/manual/en/function.strtr.php),
  [explode](https://www.php.net/manual/en/function.explode.php).
- PHP Manual, [Multibyte String (mbstring)](https://www.php.net/manual/en/book.mbstring.php) và
  [mb_trim](https://www.php.net/manual/en/function.mb-trim.php).
- PHP Manual, [intl](https://www.php.net/manual/en/book.intl.php): [Normalizer](https://www.php.net/manual/en/class.normalizer.php),
  [Collator](https://www.php.net/manual/en/class.collator.php),
  [Collator::setStrength](https://www.php.net/manual/en/collator.setstrength.php).
- PHP Manual, [PCRE](https://www.php.net/manual/en/book.pcre.php):
  [pattern syntax](https://www.php.net/manual/en/reference.pcre.pattern.syntax.php),
  [modifiers](https://www.php.net/manual/en/reference.pcre.pattern.modifiers.php),
  [delimiters](https://www.php.net/manual/en/regexp.reference.delimiters.php),
  [preg_match](https://www.php.net/manual/en/function.preg-match.php),
  [runtime configuration](https://www.php.net/manual/en/pcre.configuration.php).
- RFC của PHP: [Change the precedence of the concatenation operator](https://wiki.php.net/rfc/concatenation_precedence),
  [Deprecate ${} string interpolation](https://wiki.php.net/rfc/deprecate_dollar_brace_string_interpolation),
  [Locale-independent case conversion](https://wiki.php.net/rfc/strtolower-ascii),
  [PCRE2 migration](https://wiki.php.net/rfc/pcre2-migration).
- [php-src UPGRADING của PHP 8.0](https://github.com/php/php-src/blob/PHP-8.0/UPGRADING) (mục về locale
  mặc định `"C"`, float sang string không phụ thuộc locale).
- [RFC 3629: UTF-8](https://www.rfc-editor.org/rfc/rfc3629) và
  [Unicode Standard Annex #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/).
- Laravel 13, [Deployment: Server Requirements](https://laravel.com/docs/13.x/deployment) (mbstring là
  extension bắt buộc).
