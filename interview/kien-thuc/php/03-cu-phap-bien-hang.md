# Chương 03. Cú pháp cơ bản, biến và hằng

> [← Mục lục](README.md) · [← Chương 02: PHP chạy như thế nào](02-php-chay-nhu-the-nao.md) · [Chương 04: Kiểu dữ liệu và hệ thống kiểu →](04-kieu-du-lieu.md)

**Bạn sẽ học được:**

- PHP nhận ra đâu là code trong một file như thế nào (thẻ mở, thẻ đóng), câu lệnh và comment viết ra sao.
- Sáu cách in dữ liệu: `echo`, `print`, `printf`, `var_dump`, `print_r`, `var_export`, và khi nào dùng cái nào.
- Biến: đặt tên, gán theo giá trị, gán theo tham chiếu (mức giới thiệu), *variable variables*.
- Phạm vi biến: biến cục bộ trong hàm, `global`, biến `static`, và nhóm *superglobals*.
- Hằng: `define` và `const` khác nhau ở đâu, hằng có sẵn, *magic constants* như `__DIR__`.
- Phân biệt chính xác `null`, `isset`, `unset`, `empty`, một nguồn bug rất phổ biến.

**Cần biết trước:** biết chạy một file PHP bằng dòng lệnh ([Chương 01](01-php-la-gi.md)). Hiểu mô hình
"mỗi request bắt đầu sạch" ở [Chương 02](02-php-chay-nhu-the-nao.md) sẽ giúp đọc mục 4 dễ hơn.

Ví dụ trong chương chạy được trên PHP 8.4 và 8.5; chỗ nào chỉ chạy trên một phiên bản sẽ ghi rõ.
Output ghi trong comment là kết quả chạy thật trên PHP 8.5, trong đó đường dẫn file ở các thông báo
lỗi được viết tắt thành `...`. Nếu máy chưa cài PHP, lưu ví dụ vào file `vidu.php` rồi chạy bằng
Docker từ chính thư mục chứa file:

```bash
# chạy ở thư mục chứa vidu.php
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php vidu.php
```

## 1. Thẻ PHP, câu lệnh và comment

### 1.1 Một file PHP có hai "chế độ"

File PHP là một file văn bản bình thường. Khi PHP đọc file, nó chia nội dung thành hai loại:

- Phần nằm ngoài cặp thẻ `<?php` ... `?>`: PHP không phân tích, cứ thế in nguyên ra output. Manual
  gọi đây là "escaping from HTML", vì ngày xưa phần này thường là HTML. Trong mã nguồn PHP nó có tên
  *inline HTML*.
- Phần nằm trong cặp thẻ: đây là code PHP, được dịch và chạy.

```
 file trang.php                         PHP xử lý
┌──────────────────────────────┐
│ <h1>Xin chào</h1>            │  ──►  in nguyên văn
│ <?php echo date('Y'); ?>     │  ──►  chạy code, in kết quả (ví dụ 2026)
│ <p>Hết</p>                   │  ──►  in nguyên văn
└──────────────────────────────┘
```

Nhờ cách này PHP có thể "nhúng" vào HTML để làm template. Đây là ví dụ một template nhỏ (đặt tên
`trang.php`, chạy `php trang.php`):

```php
<?php declare(strict_types=1);
$title = 'Việc cần làm';
$tasks = ['Học PHP', 'Ôn MySQL'];
?>
<h1><?= $title ?></h1>
<ul>
<?php foreach ($tasks as $task): ?>
    <li><?= $task ?></li>
<?php endforeach; ?>
</ul>
<p>Tổng: <?= count($tasks) ?> việc</p>
```

Output:

```
<h1>Việc cần làm</h1>
<ul>
    <li>Học PHP</li>
    <li>Ôn MySQL</li>
</ul>
<p>Tổng: 2 việc</p>
```

Vài điều đáng chú ý trong ví dụ:

- Dòng HTML nằm giữa `<?php foreach ...: ?>` và `<?php endforeach; ?>` được in mỗi vòng lặp một
  lần. PHP không chỉ "in nguyên văn" phần ngoài thẻ một cách mù quáng: phần đó nằm trong cấu trúc
  điều khiển nào thì tuân theo cấu trúc đó (lặp, hay bị bỏ qua nếu nằm trong nhánh `if` sai).
- `foreach (...):` và `endforeach;` là *cú pháp thay thế* (alternative syntax) của vòng lặp, rất hay
  gặp trong template. Chi tiết ở [Chương 07](07-toan-tu-dieu-khien.md).
- Output không có dòng trống ở đầu, dù dòng 4 của file là `?>` và có ký tự xuống dòng ngay sau nó.
  Lý do ở mục 1.3.

⚠️ Ví dụ trên in thẳng biến vào HTML để minh hoạ cú pháp. Trong ứng dụng thật, mọi dữ liệu đến từ
người dùng phải được escape (`htmlspecialchars($task)`), nếu không sẽ dính lỗ hổng XSS. Blade của
Laravel tự escape khi bạn viết `{{ $task }}`. Xem [Chương 17](17-bao-mat.md).

### 1.2 Các loại thẻ

| Thẻ | Ý nghĩa | Nên dùng? |
|---|---|---|
| `<?php` ... `?>` | Thẻ chuẩn, bật chế độ PHP | Luôn dùng |
| `<?=` ... `?>` | *Short echo tag*, viết tắt của `<?php echo` | Dùng trong template |
| `<?` ... `?>` | *Short open tag* | Không |

Quy tắc cần nhớ:

- Sau `<?php` phải có ít nhất một ký tự khoảng trắng (dấu cách, tab hoặc xuống dòng). Manual nói rõ
  thiếu khoảng trắng này sẽ gây lỗi cú pháp: `<?phpecho "x";` không được hiểu là `<?php echo "x";`.
  (Chạy thử: khi `short_open_tag` bật, dòng đó báo parse error; khi tắt, cả dòng bị in ra như văn
  bản thường.)
- `<?=` luôn dùng được, không phụ thuộc cấu hình nào. `<?= $title ?>` tương đương
  `<?php echo $title ?>`.
- `<?` chỉ hoạt động khi directive `short_open_tag` trong `php.ini` đang bật. Giá trị mặc định khi
  không có file `php.ini` là bật, nhưng cả hai file mẫu `php.ini-development` và `php.ini-production`
  đi kèm mã nguồn PHP đều đặt `short_open_tag = Off`. Vì code của bạn có thể chạy trên server tắt
  tuỳ chọn này, manual khuyên chỉ dùng `<?php ?>` và `<?= ?>`.

⚠️ Khi `short_open_tag` tắt, `<? echo 1; ?>` không báo lỗi: PHP coi nó là văn bản thường và in
nguyên chuỗi `<? echo 1; ?>` ra output, kể cả code bên trong. Đó là cách mã nguồn bị lộ ra trình duyệt.

### 1.3 Thẻ đóng `?>`: cái newline bị "nuốt" và vì sao nên bỏ thẻ đóng

Thẻ đóng có hai hành vi ngầm:

1. Nó ngầm định một dấu `;`. Câu lệnh cuối cùng trước `?>` không cần dấu chấm phẩy:
   `<?php echo "Xin chào" ?>` là hợp lệ.
2. Nếu ngay sau `?>` là một ký tự xuống dòng, PHP nuốt ký tự đó (chỉ một ký tự, không phải tất cả
   dòng trống). Đây là lý do template ở mục 1.1 không có dòng trống ở đầu.

Ví dụ (đặt trong file `newline.php`):

```php
<?php echo "A"; ?>
B
<?= "C" ?>

D
```

Output:

```
AB
C
D
```

Phân tích: newline sau `?>` ở dòng 1 bị nuốt nên `A` và `B` dính nhau. Sau `<?= "C" ?>` có hai
ký tự xuống dòng (một ở cuối dòng 3, một là dòng trống thứ 4): cái đầu bị nuốt, cái thứ hai được in.

Hành vi thứ hai chỉ "cứu" được đúng một ký tự xuống dòng. Vì vậy có một quy tắc quan trọng: **file
chỉ chứa code PHP thì không viết thẻ đóng `?>` ở cuối file**. Nếu có thẻ đóng mà sau nó vô tình dư một
dấu cách, hay hai dòng trống, phần thừa đó là inline HTML và sẽ thành output. Khi output đã được gửi đi, PHP không thể gửi thêm HTTP header nữa:
`header()` báo `Warning: Cannot modify header information - headers already sent by (output started
at ...)`, `session_start()` cũng thất bại tương tự. Lỗi này rất khó tìm vì kẻ gây ra chỉ là một ký tự
trắng ở cuối một file được `require`. (Nếu server bật *output buffering*, phần thừa nằm tạm trong
buffer nên lỗi có thể không lộ ra ngay, rồi xuất hiện khi buffer đầy hay khi đổi cấu hình. Chi tiết
về header và buffering ở [Chương 15](15-php-va-web.md).)

Chuẩn code PSR-2 và chuẩn thay thế nó là PSR-12 đều ghi cùng một câu: "The closing `?>` tag MUST be
omitted from files containing only PHP." (Hướng dẫn đóng góp của Laravel ghi framework theo PSR-2.)
Các file class, config, route của Laravel đều chỉ chứa PHP nên không có thẻ đóng.

### 1.4 Câu lệnh, khối lệnh và dấu chấm phẩy

Một *câu lệnh* (statement) là một chỉ thị cho PHP làm việc gì đó: gán biến, gọi hàm, in ra... Mỗi
câu lệnh kết thúc bằng dấu `;`. Nhiều câu lệnh gom trong cặp ngoặc nhọn `{ }` tạo thành một *khối
lệnh* (block), dùng cho thân hàm, thân `if`, thân vòng lặp.

```php
<?php declare(strict_types=1);

$price = 120000;                // câu lệnh gán
$qty = 3;
$total = $price
    * $qty;                     // một câu lệnh có thể trải trên nhiều dòng
if ($total > 300000) {          // khối lệnh của if
    echo "Miễn phí ship\n";
    echo "Tổng: $total\n";
}
// in ra:
// Miễn phí ship
// Tổng: 360000
```

PHP không quan tâm khoảng trắng và xuống dòng: chỉ dấu `;` mới kết thúc câu lệnh. Quên `;` là lỗi
*parse* (lỗi cú pháp), cả file không chạy được dòng nào:

```php
<?php
echo "a"
echo "b";
// Parse error: syntax error, unexpected token "echo", expecting "," or ";" in ... on line 3
```

Lỗi báo ở dòng 3 dù thiếu dấu ở dòng 2: parser chỉ phát hiện ra vấn đề khi gặp token tiếp theo. Gặp
"unexpected token" thì hãy nhìn cả dòng phía trên.

Đối chiếu: Java bắt buộc `;` giống PHP. Go thì để lexer tự chèn dấu `;` ở cuối dòng nên bạn hầu như
không gõ nó. JavaScript có cơ chế tự chèn (ASI). PHP không tự chèn `;` khi xuống dòng (chỉ có thẻ
đóng `?>` ngầm định một dấu `;`, mục 1.3).

Câu lệnh `declare(strict_types=1);` mà bạn thấy ở đầu mọi ví dụ bật chế độ kiểm tra kiểu chặt cho
file đó (ý nghĩa đầy đủ ở [Chương 04](04-kieu-du-lieu.md)). Nó phải là câu lệnh đầu tiên của
file. Comment đứng trước thì không sao, nhưng có bất kỳ câu lệnh nào đứng trước, kể cả một dòng HTML
nằm trước `<?php`, là lỗi:

```php
<?php
echo "a";
declare(strict_types=1);
// Fatal error: strict_types declaration must be the very first statement in the script in ... on line 3
```

(Từ PHP 8.5, fatal error kèm theo backtrace, nên bạn sẽ thấy thêm vài dòng `Stack trace:` phía sau;
ini mới `fatal_error_backtraces` điều khiển việc này, chi tiết ở [Chương 12](12-loi-exception.md).
Chương này lược bỏ phần đó.)

Chữ hoa, chữ thường: PHP phân biệt ở một số chỗ và không phân biệt ở chỗ khác. Bảng này cần thuộc:

| Thành phần | Phân biệt hoa thường? | Ví dụ |
|---|---|---|
| Tên biến | Có | `$ten` và `$Ten` là hai biến khác nhau |
| Tên hằng | Có | `MAX` và `max` khác nhau (mục 5.1) |
| `true`, `false`, `null` | Không | `TRUE`, `True`, `NULL` đều hợp lệ |
| Từ khoá (`if`, `echo`, `function`...) | Không | `IF`, `ECHO` vẫn chạy |
| Tên hàm | Không (với chữ cái ASCII) | `STRLEN('abc')` gọi `strlen` |
| Tên class | Không | `new DIEM()` tạo object của class `Diem` |

Không phân biệt không có nghĩa là nên viết lộn xộn. Hãy luôn gọi đúng như lúc khai báo. Với tên class
còn có lý do thực tế: autoloader (Chương 11) đổi tên class thành đường dẫn file, và trên Linux hệ
thống file phân biệt hoa thường. Code gọi `new diem()` chạy được trên macOS của bạn có thể không tìm
thấy file `Diem.php` trên server Linux.

### 1.5 Comment

*Comment* là phần chú thích để người đọc hiểu, PHP bỏ qua khi chạy. PHP có ba kiểu viết, mượn từ
C++, shell và C; docblock là một biến thể của kiểu C:

```php
<?php declare(strict_types=1);

// comment một dòng kiểu C++
# comment một dòng kiểu shell
/* comment
   nhiều dòng kiểu C */

/**
 * Tính tổng tiền đơn hàng.  <- docblock: bắt đầu bằng /** (hai dấu sao)
 *
 * @param list<int> $prices
 */
function total(array $prices): int
{
    return array_sum($prices);
}

echo total([100, 200]), "\n"; // in ra: 300
```

Loại cuối, bắt đầu bằng `/**`, gọi là *docblock* (hay *doc comment*). Với PHP nó vẫn là comment, nhưng
PHP giữ lại nội dung của nó để code khác đọc được qua Reflection (`getDocComment()`). IDE và công cụ
phân tích tĩnh như PHPStan đọc các thẻ `@param`, `@return`, `@var` trong docblock để biết những thông
tin mà kiểu khai báo của PHP chưa diễn đạt được, ví dụ `list<int>` là "mảng chỉ chứa int".

Ba cạm bẫy với comment:

⚠️ **Comment một dòng kết thúc ở cuối dòng hoặc ở `?>`, cái nào tới trước.** Thẻ đóng nằm trong
comment `//` vẫn có hiệu lực:

```php
<?php
// echo "?>"; echo "sau đó";
```

Output là `"; echo "sau đó";`: PHP coi `?>` trong comment là thẻ đóng, phần sau thành văn bản thường
và bị in ra. (Trong chuỗi thì khác: `$t = "?>";` vẫn là chuỗi bình thường.)

⚠️ **Comment `/* */` không lồng nhau được.** `/*` mở comment, và `*/` đầu tiên gặp được sẽ đóng
nó. Khi bạn "comment tạm" một khối code mà bên trong đã có `/* */`, phần còn lại lộ ra thành code:

```php
<?php
/*
   echo 'a'; /* comment có sẵn */
*/
// Parse error: syntax error, unexpected token "*", expecting end of file in ... on line 4
```

Muốn tắt tạm một khối code, dùng phím tắt comment từng dòng của editor (`//` đầu mỗi dòng).

⚠️ **`#[` không còn là comment từ PHP 8.0.** Từ 8.0, `#[...]` là cú pháp *attribute* (gắn siêu dữ
liệu vào class, hàm, tham số; học ở [Chương 10](10-oop-nang-cao.md)). Một dòng như
`#[TODO: sửa sau]` từng là comment ở PHP 7, giờ là lỗi:

```php
<?php
#[TODO: sửa sau]
echo "x";
// Parse error: syntax error, unexpected token ":", expecting "]" in ... on line 2
```

Viết `# [TODO]` (có dấu cách giữa `#` và `[`) hoặc dùng `//` thì không sao.

Comment tốt giải thích vì sao, không lặp lại code làm gì. `$i++; // tăng i` là comment vô
ích. `// Trừ 1 vì API đối tác đếm trang từ 1` là comment có giá trị.

## 2. In dữ liệu ra: echo, print, printf và ba công cụ debug

Chương trình nào cũng cần đưa kết quả ra ngoài: ra terminal khi chạy bằng CLI, hoặc vào nội dung
HTTP response khi chạy trên web. PHP có hai nhóm công cụ:

- In output cho người dùng: `echo`, `print`, `printf`.
- Cho lập trình viên nhìn vào bên trong một giá trị khi debug: `var_dump`, `print_r`, `var_export`.

### 2.1 echo và print

`echo` in ra một hoặc nhiều giá trị, không tự thêm dấu cách hay xuống dòng:

```php
<?php declare(strict_types=1);

$name = 'Lan';
echo "Xin chào ", $name, "\n";     // nhiều đối số, phân cách bằng dấu phẩy
echo "Xin chào " . $name . "\n";   // một đối số: chuỗi đã nối bằng dấu chấm
echo "Xin chào $name", PHP_EOL;    // biến đặt trong chuỗi nháy kép (Chương 05)
// cả ba dòng đều in ra: Xin chào Lan
```

`PHP_EOL` là hằng chứa ký tự xuống dòng của hệ điều hành đang chạy (`"\n"` trên Linux và macOS,
`"\r\n"` trên Windows). Khi in ra terminal, dùng `"\n"` hay `PHP_EOL` đều được.

`echo` không phải hàm mà là một *language construct* (cấu trúc ngôn ngữ, cùng loại với `if` hay
`return`). Điều này giải thích mấy hành vi lạ:

- Không cần ngoặc. `echo("một");` chạy được, nhưng cặp ngoặc ở đây thuộc về biểu thức `("một")`,
  không phải cú pháp gọi hàm. Vì vậy `echo("a", "b");` là lỗi parse (`unexpected token ","`).
- `echo` không trả về giá trị nên không đặt được vào giữa biểu thức: `$x = true ? echo "a" : 1;` là
  lỗi parse.
- Không gọi được qua biến: `$f = 'echo'; $f('x');` ném `Error: Call to undefined function echo()`.

`print` gần giống `echo`, khác ở hai điểm: chỉ nhận một đối số, và luôn trả về `1` nên dùng được
trong biểu thức:

```php
$r = print "print trả về 1\n";   // in ra: print trả về 1
var_dump($r);                    // in ra: int(1)
```

Thực tế gần như ai cũng dùng `echo`. Biết `print` để đọc hiểu code cũ.

⚠️ `echo` và `print` luôn đổi giá trị sang chuỗi, kể cả khi bật `strict_types` (manual ghi rõ
điều này). Cách đổi:

| Giá trị | `echo` in ra |
|---|---|
| `42` | `42` |
| `1.5` | `1.5` |
| `1.0` | `1` (mất phần `.0`) |
| `true` | `1` |
| `false` | chuỗi rỗng, tức không in gì |
| `null` | chuỗi rỗng, tức không in gì |
| `[1, 2]` | `Array`, kèm `Warning: Array to string conversion` |
| object không có method `__toString()` | ném `Error: Object of class P could not be converted to string` |

Nghĩa là nhìn output của `echo` bạn không phân biệt được `false`, `null` và `""`, cũng không phân
biệt được `1`, `1.0`, `"1"` và `true`. Khi debug, đừng dùng `echo`; dùng `var_dump` (mục 2.3).

⚠️ Khi in nhiều thứ, dùng dấu phẩy an toàn hơn dấu chấm. Nối chuỗi bằng `.` thì thứ tự ưu tiên toán
tử có thể làm bạn bất ngờ. Ví dụ lấy từ manual:

```php
echo 'Sum: ' . 1 + 2, "\n";   // PHP 8: Sum: 3. Theo manual, PHP trước 8.0 in ra 2
echo 'Sum: ', 1 + 2, "\n";    // Sum: 3 ở mọi phiên bản: mỗi đối số được tính riêng
```

Thứ tự ưu tiên toán tử được học kỹ ở [Chương 07](07-toan-tu-dieu-khien.md).

### 2.2 printf và sprintf: in có định dạng

Khi cần căn lề, cố định số chữ số thập phân, đệm số 0 phía trước..., dùng `printf`. Đối số đầu tiên
là *format string* (chuỗi mẫu); mỗi chỗ bắt đầu bằng `%` là một "ô trống", lần lượt được thay bằng
các đối số phía sau:

```php
<?php declare(strict_types=1);

printf("%s mua %d món, tổng %.2f\n", "Lan", 3, 359.5);
// in ra: Lan mua 3 món, tổng 359.50

$line = sprintf("%05d|%-6s|%6s|", 42, "ab", "ab");   // sprintf trả về chuỗi, không in
echo $line, "\n";
// in ra: 00042|ab    |    ab|
```

Cú pháp đầy đủ của một ô là `%[argnum$][flags][width][.precision]specifier`. Các dạng hay dùng:

| Mẫu | Ý nghĩa | Ví dụ | Kết quả |
|---|---|---|---|
| `%s` | chuỗi | `printf("%s", "abc")` | `abc` |
| `%d` | số nguyên | `printf("%d", 42)` | `42` |
| `%.2f` | số thực, 2 chữ số sau dấu chấm | `printf("%.2f", 3.14159)` | `3.14` |
| `%5d` | rộng tối thiểu 5 ký tự, căn phải | `printf("[%5d]", 42)` | `[   42]` |
| `%-5d` | rộng 5, căn trái | `printf("[%-5d]", 42)` | `[42   ]` |
| `%05d` | đệm số 0 bên trái | `printf("%05d", 42)` | `00042` |
| `%'*8s` | đệm bằng ký tự tự chọn (`*`) | `printf("%'*8s", "abc")` | `*****abc` |
| `%x`, `%b` | hệ 16, hệ 2 | `printf("%x %b", 255, 5)` | `ff 101` |
| `%%` | chính ký tự `%` | `printf("%d%%", 50)` | `50%` |
| `%2$s` | dùng đối số thứ 2 | `printf('%2$s %1$s', "a", "b")` | `b a` |

(Mẫu `%2$s` được viết trong nháy đơn vì trong nháy kép, `$s` sẽ bị hiểu là biến.)

`printf` trả về số byte đã in, không phải số ký tự: `printf("Việt\n")` trả về `7` vì chữ "ệ"
chiếm 3 byte trong UTF-8 (Chương 05 giải thích byte và ký tự). `sprintf` thì trả về chuỗi kết quả
thay vì in; trong code thật nó được dùng nhiều hơn `printf`, ví dụ để dựng nội dung log.

⚠️ Thiếu đối số là lỗi từ PHP 8.0: `printf("%s %s\n", "a")` ném
`ArgumentCountError: 3 arguments are required, 2 given` (con số đếm cả format string). Trước 8.0
chỉ có warning và hàm trả về `false`.

⚠️ Ngược lại, sai kiểu thì im lặng, kể cả với `strict_types`: `printf("[%d] [%d]", "12abc", "abc")`
in `[12] [0]` mà không có cảnh báo nào. Các đối số của `printf` có kiểu `mixed` nên `strict_types`
không chặn được; việc đổi `"12abc"` thành `12` xảy ra bên trong hàm. Dữ liệu từ người dùng phải được
kiểm tra trước khi đưa vào.

Định dạng tiền, số có dấu phân cách hàng nghìn (`number_format`) và các hàm chuỗi khác:
[Chương 05](05-chuoi.md).

### 2.3 var_dump, print_r, var_export: nhìn vào bên trong một giá trị

Ba hàm này cho lập trình viên biết một giá trị thật sự "trông như thế nào", đặc biệt hữu ích với
mảng và object. Cùng một dữ liệu, ba cách in:

```php
<?php declare(strict_types=1);

$data = ['id' => 7, 'price' => 1.0, 'name' => 'Việt', 'active' => true, 'deleted' => false, 'note' => null];
var_dump($data);
print_r($data);
var_export($data);
```

Output của `var_dump($data)`:

```
array(6) {
  ["id"]=>
  int(7)
  ["price"]=>
  float(1)
  ["name"]=>
  string(6) "Việt"
  ["active"]=>
  bool(true)
  ["deleted"]=>
  bool(false)
  ["note"]=>
  NULL
}
```

Output của `print_r($data)`:

```
Array
(
    [id] => 7
    [price] => 1
    [name] => Việt
    [active] => 1
    [deleted] => 
    [note] => 
)
```

Output của `var_export($data)`:

```
array (
  'id' => 7,
  'price' => 1.0,
  'name' => 'Việt',
  'active' => true,
  'deleted' => false,
  'note' => NULL,
)
```

Đọc kỹ ba output:

- `var_dump` ghi kiểu của từng giá trị: `int(7)`, `float(1)`, `bool(true)`, `NULL`. Với chuỗi nó
  ghi độ dài tính bằng byte: `string(6) "Việt"` (4 ký tự nhưng 6 byte). `array(6)` là mảng có 6 phần
  tử. `var_dump` nhận nhiều đối số một lúc: `var_dump($a, $b)`.
- `print_r` dễ đọc nhất nhưng mất thông tin kiểu: `true` thành `1`; `false` và `null` đều thành
  rỗng; `1.0` thành `1`. Nhìn `[deleted] =>` bạn không biết đó là `false`, `null` hay `""`.
- `var_export` in ra code PHP hợp lệ: copy output dán vào file `.php` là có lại đúng giá trị đó.

Với object, cả ba đều in mọi property kể cả `private` và `protected`. Ngoại lệ: nếu class định nghĩa
method `__debugInfo()` thì `var_dump` và `print_r` in mảng mà method đó trả về (dùng để giấu mật khẩu
chẳng hạn), còn `var_export` vẫn in property thật ([Chương 10](10-oop-nang-cao.md)):

```php
<?php declare(strict_types=1);

final class User
{
    public function __construct(
        public string $name,
        private ?string $email = null,
    ) {}
}

var_dump(new User('Lan'));
// in ra:
// object(User)#1 (2) {
//   ["name"]=>
//   string(3) "Lan"
//   ["email":"User":private]=>
//   NULL
// }
var_export(new User('Lan'));
// in ra:
// \User::__set_state(array(
//    'name' => 'Lan',
//    'email' => NULL,
// ))
```

Trong `object(User)#1 (2)`: `User` là tên class, `#1` là số hiệu (id) của object trong lần chạy này,
`(2)` là số property. Số hiệu `#1` hữu ích khi muốn biết hai biến có đang trỏ cùng một object hay
không (Chương 09). `var_export` sinh lời gọi `__set_state()`; muốn chạy lại được code đó thì class
phải tự định nghĩa method tĩnh `__set_state()`. Riêng `stdClass` được xuất thành
`(object) array(...)`. Từ PHP 8.2 tên class được xuất kèm dấu `\` ở đầu như trên.

So sánh nhanh:

| Tiêu chí | `var_dump` | `print_r` | `var_export` |
|---|---|---|---|
| Hiện kiểu dữ liệu | Có | Không | Gián tiếp, qua cú pháp PHP (`'a'`, `1.0`, `NULL`) |
| Phân biệt `true`, `false`, `null`, `""` | Có | Không | Có |
| Trả về chuỗi thay vì in | Không | Có: `print_r($x, true)` | Có: `var_export($x, true)` |
| Số thực | In đủ chữ số | Làm tròn (xem cạm bẫy dưới) | In đủ chữ số |
| Mảng hoặc object tự chứa chính nó | In `*RECURSION*` | In `*RECURSION*` | Warning `var_export does not handle circular references`, phần lặp thành `NULL` |
| Dùng khi | Debug, cần biết chính xác kiểu và giá trị | Xem nhanh cấu trúc mảng lớn | Sinh code PHP từ dữ liệu |

Tham số thứ hai `true` của `print_r` và `var_export` rất hay dùng để ghi log:
`error_log(print_r($payload, true));`.

Một ứng dụng thật của `var_export`: lệnh `php artisan config:cache` của Laravel gom toàn bộ config
thành một mảng rồi ghi ra file `bootstrap/cache/config.php` với nội dung
`'<?php return ' . var_export($config, true) . ';'`. Lần sau Laravel chỉ cần `require` một file
thay vì đọc hàng chục file config. Bạn có thể tự làm lại cơ chế đó:

```php
<?php declare(strict_types=1);

$config = ['app' => ['name' => 'Shop', 'debug' => false], 'rate' => 0.08];
$php = '<?php return ' . var_export($config, true) . ';' . PHP_EOL;
file_put_contents(__DIR__ . '/config.cache.php', $php);

$loaded = require __DIR__ . '/config.cache.php';   // require trả về giá trị của lệnh return trong file
var_dump($loaded === $config);                      // in ra: bool(true)
```

Hệ quả: config nào chứa closure (hàm ẩn danh) thì không cache được, vì `var_export` xuất closure
thành `\Closure::__set_state(array(...))` và khi chạy lại sẽ ném
`Error: Call to undefined method Closure::__set_state()`. Laravel bắt lỗi này, xoá file cache vừa
ghi và báo config không serialize được, kèm tên key gây lỗi.

⚠️ `echo` che giấu sai số của số thực:

```php
<?php declare(strict_types=1);

echo 0.1 + 0.2, "\n";    // in ra: 0.3
var_dump(0.1 + 0.2);     // in ra: float(0.30000000000000004)
```

`echo`, `print_r` và phép ép `(string)` đổi float sang chuỗi theo ini `precision` (mặc định 14 chữ số
có nghĩa) nên làm tròn mất phần lệch. `var_dump`, `var_export` và `json_encode` dùng ini
`serialize_precision` (mặc định `-1`: dùng thuật toán in ra chuỗi ngắn nhất mà khi đọc lại vẫn cho
đúng giá trị float đó), nên bạn thấy giá trị thật đang được lưu. Debug số thực thì dùng `var_dump`.
Vì sao `0.1 + 0.2` không bằng `0.3`: [Chương 04](04-kieu-du-lieu.md).

Laravel có sẵn hai helper `dump()` (in giá trị, dễ đọc hơn `var_dump`) và `dd()` ("dump and die":
in xong dừng script luôn); framework dùng thư viện Symfony VarDumper cho việc này.

⚠️ Đừng để `var_dump`, `print_r`, `dd` sót lại trong code đưa lên production: chúng in dữ liệu nội
bộ (có thể là mật khẩu, token) ra cho người dùng, làm hỏng response JSON, và tạo output trước khi
header được gửi. Muốn xem giá trị trên production thì ghi log.

## 3. Biến

### 3.1 Biến là gì

*Biến* (variable) là một cái tên gắn với một giá trị trong bộ nhớ, để bạn lưu giá trị rồi dùng lại
về sau. Trong PHP, tên biến luôn bắt đầu bằng dấu `$`.

```php
<?php declare(strict_types=1);

$x = 10;          // lần gán đầu tiên tạo ra biến $x
var_dump($x);     // in ra: int(10)
$x = 'mười';      // cùng biến, giờ chứa chuỗi
var_dump($x);     // in ra: string(7) "mười"
$x = [10];        // giờ chứa mảng
var_dump($x);     // in ra: array(1) { [0]=> int(10) }  (thực tế in trên nhiều dòng)
```

Hai điều khác hẳn Java và Go:

- **Không cần khai báo.** Không có `int x;` hay `var x int`. Biến ra đời ở lần gán đầu tiên.
- **Kiểu thuộc về giá trị, không thuộc về biến.** `$x` lúc chứa int, lúc chứa string đều hợp lệ.
  PHP là ngôn ngữ *dynamic typing*. Kiểu chỉ được kiểm tra ở những chỗ bạn khai báo kiểu: tham số
  hàm, giá trị trả về, property. Hệ thống kiểu được học ở [Chương 04](04-kieu-du-lieu.md).

### 3.2 Đặt tên biến

Quy tắc của manual: sau dấu `$` là một chữ cái hoặc dấu gạch dưới, tiếp theo là chữ cái, chữ số hoặc
gạch dưới bao nhiêu cũng được. "Chữ cái" ở đây gồm `a-z`, `A-Z` và mọi byte từ 128 tới 255. Viết thành
biểu thức chính quy: `^[a-zA-Z_\x80-\xff][a-zA-Z0-9_\x80-\xff]*$`.

```php
$userName = 'Lan';   // hợp lệ
$_tmp = 1;           // hợp lệ: bắt đầu bằng gạch dưới
$user2 = 'Minh';     // hợp lệ: chữ số không đứng đầu
$4site = 1;          // lỗi parse: bắt đầu bằng chữ số
$my-name = 1;        // lỗi parse: PHP đọc thành $my - name = 1
$this = 1;           // Fatal error: Cannot re-assign $this
```

- Tên biến phân biệt hoa thường: `$user` và `$User` là hai biến.
- `$this` là biến đặc biệt (object hiện tại bên trong method, Chương 09), không gán được.
- Vì byte 128-255 hợp lệ nên tên tiếng Việt UTF-8 như `$tên` chạy được. Nhưng manual lưu ý tên biến
  được so sánh theo byte, không theo ký tự hiển thị. Cùng là chữ "ä", nếu một chỗ gõ dạng dựng
  sẵn (một code point U+00E4) và chỗ khác gõ dạng tổ hợp (chữ `a` cộng dấu U+0308) thì đó là hai biến
  khác nhau dù nhìn y hệt. Hãy dùng tên tiếng Anh, chỉ gồm ký tự ASCII.

Về kiểu viết: chuẩn PSR-1 quy định tên method là `camelCase` nhưng cố ý không quy định kiểu tên
property, chỉ yêu cầu nhất quán; về tên biến thì PSR-1 không nói gì. Laravel và phần lớn code PHP
hiện đại dùng `camelCase` cho biến: `$orderTotal`, `$isPaid`. Đặt tên theo ý nghĩa (`$unpaidOrders`), tránh tên chung chung như
`$data`, `$tmp`, `$arr` cho biến sống lâu.

### 3.3 Đọc một biến chưa từng gán

```php
<?php declare(strict_types=1);

var_dump($chuaCo);
// Warning: Undefined variable $chuaCo in ... on line 3
// NULL
```

PHP 8 phát một *warning* (trước 8.0 là *notice*, mức nhẹ hơn), coi giá trị là `null`, rồi chạy
tiếp. Đây là điều nguy hiểm: một lỗi gõ sai tên biến (`$totl` thay vì `$total`) không làm chương
trình dừng mà khiến nó chạy tiếp với `null`. Laravel cài sẵn error handler biến mọi warning thành
`ErrorException`, nên trong ứng dụng Laravel lỗi này ném exception thay vì bị bỏ qua (cơ chế ở
[Chương 12](12-loi-exception.md)).

Một số thao tác ghi lên biến chưa có:

```php
<?php declare(strict_types=1);

$items[] = 'sách';   // KHÔNG có warning: PHP tự tạo mảng mới (manual gọi là autovivification)
$count++;            // Warning: Undefined variable $count, sau đó $count thành 1
$text .= 'a';        // Warning: Undefined variable $text, sau đó $text thành "a"
```

Thói quen tốt: luôn gán giá trị ban đầu trước khi dùng (`$count = 0;`, `$items = [];`). Code rõ ràng
hơn, và không phụ thuộc vào việc "biến chưa có thì là null". Manual cảnh báo riêng về việc dựa vào giá
trị mặc định này khi một file `include` file khác có biến trùng tên: biến bạn tưởng chưa có hoá ra đã
có giá trị từ file kia.

### 3.4 Gán theo giá trị

Mặc định, phép gán `=` copy giá trị: sau khi gán, hai biến độc lập, sửa biến này không ảnh hưởng
biến kia.

```php
<?php declare(strict_types=1);

$a = 10;
$b = $a;               // $b nhận một bản sao của 10
$b = 20;
echo $a, " ", $b, "\n";   // in ra: 10 20

$cart = ['sách'];
$copy = $cart;         // mảng cũng được gán theo giá trị
$copy[] = 'bút';
echo count($cart), " ", count($copy), "\n";   // in ra: 1 2  ($cart không bị ảnh hưởng)

$o1 = new stdClass();
$o1->name = 'Lan';
$o2 = $o1;             // object: thứ được copy là "handle" trỏ tới object, không phải object
$o2->name = 'Minh';
echo $o1->name, "\n";  // in ra: Minh  (cả hai biến dùng chung một object)
```

Hai chi tiết cần biết từ sớm, sẽ học kỹ ở chương sau:

- Copy một mảng lớn không tốn kém như bạn nghĩ. PHP dùng *copy-on-write*: `$copy = $cart` chỉ cho hai
  biến dùng chung dữ liệu, việc copy thật chỉ xảy ra khi một bên bị sửa
  ([Chương 06](06-mang.md), cơ chế bên trong ở [Chương 19](19-ben-trong-engine.md)).
- Object thì khác: giá trị nằm trong biến là một *handle* (mã định danh của object), nên copy biến
  chỉ copy handle. Đó là lý do `$o1` thấy thay đổi qua `$o2`. Muốn có object riêng phải `clone`
  ([Chương 09](09-oop-co-ban.md)). Lưu ý: đây vẫn là gán theo giá trị (giá trị là handle), không phải
  gán theo tham chiếu như mục dưới.

### 3.5 Gán theo tham chiếu (giới thiệu)

Viết `&` trước biến nguồn, `$b = &$a;`, thì không có bản sao nào: `$a` và `$b` thành **hai cái tên
cho cùng một ô chứa giá trị**. Gọi là *reference* (tham chiếu).

```
Gán theo giá trị: $b = $a;          Gán theo tham chiếu: $b = &$a;

  $a ──► [ 10 ]                       $a ──┐
  $b ──► [ 10 ]  (hai ô riêng)             ├──► [ 10 ]  (một ô, hai tên)
                                      $b ──┘
```

```php
<?php declare(strict_types=1);

$x = 1;
$y = &$x;              // $y và $x là hai tên của cùng một ô
$y = 2;
echo $x, " ", $y, "\n";   // in ra: 2 2
$x = 3;
echo $x, " ", $y, "\n";   // in ra: 3 3

unset($x);             // chỉ xoá TÊN $x, ô giá trị vẫn còn vì $y đang dùng
var_dump(isset($x), $y);  // in ra: bool(false) int(3)
```

Những điều manual nhấn mạnh:

- `$a` và `$b` ngang hàng: không phải `$b` "trỏ tới" `$a`, mà cả hai cùng trỏ vào một chỗ. Manual
  so sánh `unset` với lệnh `unlink` của Unix: xoá một tên (một hard link) không xoá dữ liệu khi còn
  tên khác.
- Reference không phải con trỏ (pointer) như trong C hay Go: không có phép lấy địa chỉ, không có
  `*p` để truy cập gián tiếp, và cũng không có số học con trỏ như C.
- Chỉ lấy tham chiếu được tới thứ có tên (biến, phần tử mảng, property). `$r = &(24 * 7);` là lỗi
  parse.
- Lấy tham chiếu tới biến chưa có thì biến đó được tạo ra với giá trị `null`, không có warning:
  sau `$p = &$chuaCo;` thì `$chuaCo` tồn tại và bằng `null`.

Bạn sẽ gặp lại reference ở ba chỗ: tham số truyền theo tham chiếu `function inc(int &$n)` và
`use (&$x)` của closure ([Chương 08](08-ham.md)), vòng `foreach ($items as &$item)` cùng cái bẫy kinh
điển của nó ([Chương 06](06-mang.md)), và cách `global`, `static` hoạt động (mục 4 của chương này).

⚠️ Reference là công cụ để chia sẻ một biến, không phải công cụ tăng tốc. Nhờ copy-on-write, gán
hay truyền mảng theo giá trị vốn không copy gì nếu không ai sửa. Thêm `&` "cho đỡ copy" không làm code
nhanh hơn, chỉ làm luồng dữ liệu khó theo dõi hơn ([Chương 19](19-ben-trong-engine.md)).

⚠️ Một phần tử mảng đang là reference thì vẫn được dùng chung sau khi copy mảng:

```php
<?php declare(strict_types=1);

$list = [1, 2];
$r = &$list[0];        // phần tử 0 giờ nằm trong một reference
$list2 = $list;        // tưởng là bản sao độc lập...
$list2[0] = 99;
var_dump($list[0]);    // in ra: int(99)  ...nhưng bản gốc cũng đổi
```

Đây là kiểu bug rất khó tìm, thường xuất hiện ngầm sau một vòng `foreach` theo tham chiếu. Quy tắc an
toàn: hạn chế dùng `&`, và khi dùng thì `unset()` biến tham chiếu ngay khi xong việc.

Đối chiếu: Go có con trỏ thật (`p := &x; *p = 2`), phải giải tham chiếu bằng `*`. Java không có cách
nào tạo tham chiếu tới một biến cục bộ. Reference của PHP giống "bí danh" (alias) hơn là con trỏ.

### 3.6 Variable variables: tên biến lấy từ một biến khác

*Variable variable* là khi tên của biến được lấy từ giá trị của một biến khác, viết bằng hai dấu `$`:

```php
<?php declare(strict_types=1);

$field = 'email';
$$field = 'lan@example.com';     // tương đương $email = 'lan@example.com';
echo $email, "\n";               // in ra: lan@example.com
echo ${'em' . 'ail'}, "\n";      // ngoặc nhọn: tên biến là kết quả của biểu thức. In ra: lan@example.com
```

Với mảng có chỗ mơ hồ: `$$a[1]` nghĩa là "biến có tên `$a[1]`" hay "phần tử `[1]` của biến `$$a`"?
PHP 7 trở đi đọc từ trái sang phải, tức hiểu là `${$a}[1]`. Muốn nghĩa còn lại phải viết `${$a[1]}`.
Đừng bắt người đọc phải nhớ quy tắc này: khi buộc phải dùng, luôn viết ngoặc nhọn.

```php
// tiếp ví dụ trên ($email đã có giá trị)
$names = ['email', 'phone'];
echo ${$names[0]}, "\n";   // biến có tên là giá trị $names[0], tức $email. In ra: lan@example.com
$arr = 'names';
echo ${$arr}[1], "\n";     // phần tử [1] của biến $names. In ra: phone
```

Cùng ý tưởng áp dụng cho property của object, và đây là chỗ nó thật sự hữu ích:

```php
<?php declare(strict_types=1);

$user = new stdClass();
$prop = 'name';
$user->$prop = 'Lan';                    // tương đương $user->name = 'Lan'

$data = json_decode('{"first-name":"Lan"}');
echo $data->{'first-name'}, "\n";        // in ra: Lan
```

JSON có key chứa dấu `-` thì không viết `$data->first-name` được (PHP hiểu là phép trừ), nên phải
dùng cú pháp `->{'...'}`.

Hai giới hạn (manual):

- Bên trong hàm hoặc method, variable variables không truy cập được superglobals: với
  `$n = '_SERVER';` thì `$$n` trong hàm là biến không tồn tại.
- `$this` là biến đặc biệt, manual ghi nó không tham chiếu động được. Chạy thử trên PHP 8.5 với
  `$name = 'this';`: trong method, gán `$$name = 1` ném `Error: Cannot re-assign $this`, còn đọc
  `$$name` vẫn trả về object hiện tại; ngoài class, đọc `$$name` cho warning `Undefined variable $this`.

⚠️ Hạn chế dùng variable variables cho biến thường. Code khó đọc, IDE và PHPStan không biết biến nào
được tạo ra, và nếu tên biến đến từ dữ liệu người dùng thì kẻ tấn công có thể ghi đè bất kỳ biến nào.
Gần như mọi trường hợp đều thay được bằng một mảng: `$data['email']` thay vì `$$field`.

Hai hàm có sẵn làm việc với "tên biến dạng chuỗi" mà bạn sẽ gặp trong Laravel:

```php
<?php declare(strict_types=1);

$title = 'Đơn hàng';
$total = 360000;
$vars = compact('title', 'total');   // ['title' => 'Đơn hàng', 'total' => 360000]
var_dump($vars);
compact('title', 'khongCo');         // Warning: compact(): Undefined variable $khongCo (từ PHP 8.0)

$isAdmin = false;
$input = ['name' => 'Lan', 'isAdmin' => true];   // giả sử đây là dữ liệu từ form
extract($input);                     // tạo biến $name và GHI ĐÈ $isAdmin
var_dump($name, $isAdmin);           // in ra: string(3) "Lan" bool(true)
```

- `compact()` gom các biến (theo tên) thành mảng. Rất hay gặp trong controller Laravel:
  `return view('orders.show', compact('order', 'items'));`.
- `extract()` làm ngược lại: biến mỗi key của mảng thành một biến. Ví dụ trên cho thấy vì sao manual
  cảnh báo **không dùng `extract()` với dữ liệu không tin cậy** như `$_GET`, `$_FILES`: người dùng gửi
  thêm `isAdmin=1` là ghi đè được biến quyền admin. Nếu buộc phải dùng, truyền cờ không ghi đè như
  `EXTR_SKIP`.

## 4. Phạm vi biến (scope)

### 4.1 Global scope và function scope

*Scope* (phạm vi) của một biến là vùng code mà ở đó tên biến có nghĩa. PHP chỉ có hai loại scope:

- *Global scope*: code nằm ngoài mọi hàm, ở cấp cao nhất của file.
- *Function scope*: thân của một hàm. Mỗi lần gọi hàm tạo ra một scope mới; biến trong đó (biến
  cục bộ, *local variable*) mất đi khi hàm trả về.

Điểm khiến người mới (và người từng viết JavaScript, Python, C) bất ngờ nhất: **hàm không nhìn thấy
biến ở bên ngoài**.

```php
<?php declare(strict_types=1);

$siteName = 'Shop';        // biến ở global scope

function showName(): void
{
    var_dump($siteName);   // đây là một biến cục bộ khác, chưa được gán
}
showName();
// Warning: Undefined variable $siteName in ... on line 7
// NULL
```

Manual giải thích: khác với C, nơi biến toàn cục tự động hiện diện trong hàm, PHP bắt bạn khai báo rõ
khi muốn dùng biến toàn cục, để tránh việc vô tình sửa nó. Muốn hàm dùng dữ liệu bên ngoài, cách đúng
là truyền qua tham số và nhận kết quả qua `return`. Hàm khi đó tự chứa, đọc chữ ký là biết nó
cần gì, và dễ test.

```
 global scope                          function scope của showName()
┌──────────────────────────┐           ┌──────────────────────────────┐
│ $siteName = 'Shop'       │           │ $siteName  (chưa gán → null) │
└──────────────────────────┘           └──────────────────────────────┘
      hai biến trùng tên nhưng nằm ở hai scope, không liên quan gì nhau
```

Closure (hàm ẩn danh) cũng tuân theo quy tắc này: muốn dùng biến bên ngoài phải ghi `use ($x)`. Riêng
arrow function `fn () => ...` tự động lấy (theo giá trị) các biến bên ngoài mà nó dùng. Chi tiết ở
[Chương 08](08-ham.md).

`include` và `require` không tạo scope mới: code trong file được include **kế thừa scope của dòng
include**. Include ở cấp file thì biến của file con là biến toàn cục; include bên trong một hàm thì
chúng là biến cục bộ của hàm đó:

```php
<?php declare(strict_types=1);
// file part.php chỉ có một dòng: <?php $fromInc = 'tạo trong part.php';

function withInclude(): void
{
    include __DIR__ . '/part.php';
    echo $fromInc, "\n";       // in ra: tạo trong part.php
}
withInclude();
var_dump(isset($fromInc));     // in ra: bool(false)  ($fromInc chỉ sống trong withInclude)
```

### 4.2 Khối lệnh không tạo scope

Trong Java và Go, biến khai báo trong `{ }` của `if` hay `for` chỉ sống trong khối đó (*block
scope*). PHP thì không: `if`, `for`, `foreach`, `while`, `switch`, `try` đều không tạo scope mới.
Biến tạo bên trong vẫn còn sau khi ra khỏi khối:

```php
<?php declare(strict_types=1);

foreach (['a', 'b', 'c'] as $letter) {
    $last = $letter;
}
echo $letter, " ", $last, "\n";   // in ra: c c   (biến vòng lặp vẫn còn, giữ giá trị cuối)

for ($i = 0; $i < 3; $i++) {}
echo $i, "\n";                     // in ra: 3

if (true) {
    $inIf = 'tạo trong if';
}
echo $inIf, "\n";                  // in ra: tạo trong if
```

⚠️ Hai hệ quả thực tế:

- Biến chỉ được gán trong một nhánh `if` sẽ "chưa có" nếu nhánh đó không chạy. Gán giá trị mặc định
  trước khối `if`.
- Tên biến vòng lặp sống tiếp sau vòng lặp. Đặc biệt nguy hiểm với `foreach` theo tham chiếu
  ([Chương 06](06-mang.md)).

### 4.3 Từ khoá global và mảng $GLOBALS

Khi thật sự cần dùng biến toàn cục trong hàm, có hai cách:

```php
<?php declare(strict_types=1);

$a = 1;
$b = 2;

function sumWithGlobal(): void
{
    global $a, $b;             // $a, $b trong hàm giờ gắn với biến toàn cục cùng tên
    $b = $a + $b;
}
sumWithGlobal();
echo $b, "\n";                 // in ra: 3

function sumWithGlobalsArray(): void
{
    $GLOBALS['b'] = $GLOBALS['a'] + $GLOBALS['b'];
}
sumWithGlobalsArray();
echo $b, "\n";                 // in ra: 4
```

- `global $x;` tạo một biến cục bộ `$x` là reference tới biến toàn cục `$x`. Manual mô tả nó như
  cách viết tắt của `$x = &$GLOBALS['x'];`. Nếu biến toàn cục chưa tồn tại, nó được tạo ở global scope
  với giá trị `null`.
- `$GLOBALS` là mảng có sẵn, key là tên biến toàn cục, value là giá trị. Nó là một *superglobal* (mục
  4.5) nên dùng được ở mọi nơi mà không cần khai báo.

Từ PHP 8.1, `$GLOBALS` bị giới hạn: đọc hoặc ghi từng phần tử (`$GLOBALS['x'] = 1`) vẫn được,
nhưng ghi lên cả mảng thì không. `$GLOBALS = [];` là lỗi biên dịch
(`$GLOBALS can only be modified using the $GLOBALS[$name] = $value syntax`), `array_pop($GLOBALS)`
ném `Error`. Đồng thời `$copy = $GLOBALS;` giờ là bản sao thật: sửa `$copy['a']` không còn làm đổi
biến `$a` như ở PHP 8.0 trở về trước.

⚠️ Một bẫy do `global` là reference (ví dụ trong manual): gán một reference khác cho biến đã khai
báo `global` chỉ đổi biến cục bộ, không đổi biến toàn cục.

```php
function setGlobalRef(): void
{
    global $obj;
    $new = new stdClass();
    $obj = &$new;       // $obj cục bộ giờ trỏ sang $new, mối nối với biến toàn cục bị cắt
}
setGlobalRef();
var_dump($obj);         // in ra: NULL
```

Vì sao nên tránh biến toàn cục:

- **Phụ thuộc ẩn.** Đọc chữ ký `function total(): int` bạn không biết hàm đọc `$taxRate` toàn cục.
- **Ai cũng sửa được.** Bất kỳ đoạn code nào cũng có thể đổi giá trị, bug xuất hiện ở chỗ cách xa
  nguyên nhân.
- **Khó test.** Muốn test hàm phải dựng lại đúng trạng thái toàn cục.

Code hiện đại truyền dữ liệu qua tham số, hoặc để *service container* của Laravel tiêm phụ thuộc vào
([Chương 26](26-laravel-container-provider-facade.md)).

### 4.4 Biến static trong hàm

Biến cục bộ bình thường mất đi khi hàm trả về. Biến khai báo bằng `static` thì **giữ giá trị giữa các
lần gọi**, nhưng vẫn chỉ nhìn thấy được bên trong hàm đó:

```php
<?php declare(strict_types=1);

function counter(): int
{
    static $count = 0;   // chỉ khởi tạo ở lần gọi đầu tiên
    $count++;
    return $count;
}
echo counter(), counter(), counter(), "\n";   // in ra: 123

function plain(): int
{
    $count = 0;          // biến thường: mỗi lần gọi lại bắt đầu từ 0
    $count++;
    return $count;
}
echo plain(), plain(), plain(), "\n";         // in ra: 111
```

Ứng dụng phổ biến nhất là *memoization*: tính một thứ tốn kém đúng một lần rồi nhớ kết quả. Từ PHP 8.3,
giá trị khởi tạo của biến static có thể là biểu thức bất kỳ, kể cả lời gọi hàm:

```php
<?php declare(strict_types=1);

function loadRates(): array
{
    echo "(đọc file tỷ giá)\n";
    return ['USD' => 25000];
}

function rate(string $code): int
{
    static $rates = loadRates();   // PHP 8.3+: chỉ gọi loadRates() ở lần đầu
    return $rates[$code];
}

echo rate('USD'), "\n";
echo rate('USD'), "\n";
// in ra:
// (đọc file tỷ giá)
// 25000
// 25000
```

Trên PHP 8.2 trở về trước, giá trị khởi tạo chỉ được là *biểu thức hằng* (số, chuỗi, phép tính trên
hằng...), và file trên báo
`Fatal error: Constant expression contains invalid operations`. Cách viết tương thích bản cũ:
`static $rates = null; $rates ??= loadRates();`. Cũng từ 8.3, khai báo `static` hai lần cùng một tên
trong một hàm là lỗi biên dịch (`Duplicate declaration of static variable $x`).

Vài chi tiết khác về biến static:

- Biến static trong method: từ PHP 8.1, nếu class con kế thừa method (không override) thì method
  của class con dùng chung biến static với method của class cha. Ví dụ `Foo::counter()` gọi 2 lần
  rồi `Bar::counter()` (với `Bar extends Foo`) trả về `3`; PHP 8.0 trả về `1` vì mỗi class có bản
  riêng.
- Biến static trong closure gắn với từng object closure. Mỗi lần tạo closure mới là một bộ biến
  static mới.
- `unset()` một biến static trong hàm chỉ xoá nó trong phần còn lại của lần gọi đó; lần gọi sau giá trị
  cũ quay lại (manual).
- Từ khoá `static` còn có nghĩa khác ở chỗ khác: property và method `static` của class, `static::`
  (late static binding), `static fn` (closure không gắn `$this`). Những nghĩa đó học ở Chương 08,
  09, 10; mục này chỉ nói về biến static trong hàm.

⚠️ Biến static và biến toàn cục sống bao lâu? Với PHP-FPM truyền thống, mỗi request bắt đầu sạch
([Chương 02](02-php-chay-nhu-the-nao.md)): biến static tạo ra trong request này không còn ở request
sau. Nhưng với runtime chạy lâu như Laravel Octane hay queue worker, ứng dụng được nạp một lần rồi
phục vụ nhiều request hoặc job, nên biến static và global **sống qua các request**. Một mảng static
mà mỗi request thêm phần tử sẽ phình mãi (docs của Octane gọi đây là memory leak, ví dụ trong docs là
một static property kiểu mảng), và dữ liệu của người dùng A có thể lọt sang request của người dùng B.
Xem [Chương 30](30-laravel-testing-octane-deploy.md).

### 4.5 Superglobals

*Superglobals* là các biến có sẵn, dùng được ở mọi scope (trong hàm, trong method) mà không cần
`global`. Manual liệt kê đúng chín biến:

| Biến | Chứa gì |
|---|---|
| `$GLOBALS` | Mọi biến ở global scope (mục 4.3) |
| `$_SERVER` | Thông tin server và request: method, URI, header, đường dẫn script... |
| `$_GET` | Tham số trên query string của URL (`?page=2`) |
| `$_POST` | Dữ liệu form gửi bằng POST |
| `$_FILES` | Thông tin file được upload |
| `$_COOKIE` | Cookie trình duyệt gửi lên |
| `$_SESSION` | Dữ liệu session, chỉ có sau khi gọi `session_start()` |
| `$_REQUEST` | Gộp dữ liệu từ GET, POST (và có thể cả cookie, tuỳ cấu hình) |
| `$_ENV` | Biến môi trường, có thể rỗng (xem dưới) |

Cách dùng từng biến, cấu trúc `$_FILES`, cơ chế session, cookie: [Chương 15](15-php-va-web.md).
Ở chương này chỉ cần nhớ mấy điểm:

- `$_ENV` có thể rỗng. Directive `variables_order` quyết định superglobal nào được nạp. Giá trị
  mặc định khi không có php.ini là `"EGPCS"`, nhưng cả hai file mẫu `php.ini-development` và
  `php.ini-production` đặt `"GPCS"`, thiếu chữ `E` (Environment), nên server dùng các file mẫu này có
  `$_ENV` rỗng. Chính chú thích trong php.ini gợi ý dùng `getenv()` để đọc biến môi trường.
- Tránh `$_REQUEST`: bạn không biết giá trị đến từ query string hay từ form, và thứ tự ưu tiên phụ thuộc
  directive `request_order`/`variables_order` của từng server.
- `$argv` và `$argc` (tham số dòng lệnh khi chạy CLI) không phải superglobal. Chúng chỉ có ở global
  scope; trong hàm `isset($argv)` là `false`, phải dùng `$_SERVER['argv']`.
- Như mục 3.6, superglobals không truy cập được qua variable variables bên trong hàm.

⚠️ Mọi thứ trong `$_GET`, `$_POST`, `$_COOKIE`, `$_FILES`, và phần lớn `$_SERVER` (header, URI) là
**dữ liệu do client gửi lên**, kẻ tấn công điều khiển được hoàn toàn. Luôn kiểm tra và escape
([Chương 17](17-bao-mat.md)). Trong Laravel bạn hầu như không đụng tới superglobals mà dùng object
`Request` ([Chương 25](25-laravel-request-validation-response.md)).

## 5. Hằng (constant)

### 5.1 Hằng là gì, vì sao cần

*Hằng* (constant) là một cái tên gắn với một giá trị không thay đổi được trong suốt lúc script
chạy. So với biến:

| | Biến | Hằng |
|---|---|---|
| Cú pháp | Có `$`: `$limit` | Không có `$`: `LIMIT` |
| Đổi giá trị | Gán lại thoải mái | Không bao giờ, kể cả `unset` cũng không được |
| Phạm vi | Theo scope (mục 4) | Dùng được ở mọi nơi, kể cả trong hàm, không cần `global` |
| Quy ước tên | `camelCase` | `UPPER_SNAKE_CASE` |

Vì sao cần hằng:

- Thay *magic number* bằng tên có nghĩa. `if ($count > MAX_ITEMS)` dễ hiểu hơn `if ($count > 50)`.
- Đổi một chỗ, cả chương trình đổi theo.
- Engine bảo đảm không ai vô tình gán đè. Gán `LIMIT = 20;` là lỗi parse ngay từ đầu.

Tên hằng theo cùng quy tắc với tên biến (chữ cái hoặc `_` đứng đầu, rồi chữ cái, chữ số, `_`) và
phân biệt hoa thường. Trước PHP 8.0, `define('X', 1, true)` tạo được hằng không phân biệt hoa
thường; PHP 8.0 bỏ khả năng này, nay truyền `true` ở tham số thứ ba chỉ nhận một warning và bị bỏ qua.

Đối chiếu: `const` của Go cũng là hằng lúc biên dịch nhưng chỉ cho kiểu cơ bản (số, chuỗi, bool).
Java không dùng từ khoá riêng cho hằng (`const` chỉ là từ khoá được giữ chỗ, không dùng được) mà dùng
field `static final`.

### 5.2 Hai cách định nghĩa: const và define()

```php
<?php declare(strict_types=1);

const MAX_ITEMS = 50;                            // const: định nghĩa lúc biên dịch
const STATUSES = ['draft', 'paid', 'shipped'];   // hằng có thể là mảng
const WELCOME = 'Xin chào, ' . 'bạn';            // biểu thức hằng: được phép
define('APP_ENV', getenv('APP_ENV') ?: 'local'); // define: lúc chạy, giá trị tuỳ ý

function canAdd(int $current): bool
{
    return $current < MAX_ITEMS;                 // dùng được trong hàm, không cần global
}

var_dump(canAdd(49));                            // bool(true)
echo STATUSES[1], "\n";                          // paid
echo WELCOME, "\n";                              // Xin chào, bạn
echo APP_ENV, "\n";                              // local (khi không đặt biến môi trường APP_ENV)
var_dump(defined('MAX_ITEMS'), defined('NOPE')); // bool(true) bool(false)
$name = 'MAX_' . 'ITEMS';
var_dump(constant($name));                       // int(50)
```

`defined('TÊN')` kiểm tra một hằng đã tồn tại chưa; `constant('TÊN')` đọc hằng khi tên nằm trong một
chuỗi (tên tính ra lúc chạy).

Khác biệt giữa hai cách:

| Tiêu chí | `const TÊN = ...;` | `define('TÊN', ...)` |
|---|---|---|
| Khi nào hằng được tạo | Lúc biên dịch file | Lúc chạy tới dòng đó (là một lời gọi hàm) |
| Viết ở đâu | Chỉ ở cấp cao nhất của file (và trong class, gọi là hằng class) | Ở bất cứ đâu: trong `if`, trong hàm |
| Tên | Cố định trong code | Là chuỗi, có thể tính ra lúc chạy |
| Giá trị | Phải là *biểu thức hằng* | Biểu thức bất kỳ, kể cả kết quả gọi hàm |
| Namespace | Thuộc namespace hiện tại | Luôn ở namespace toàn cục, trừ khi tên chuỗi ghi đủ namespace |
| Gắn attribute (8.5+) | Được, ví dụ `#[\Deprecated]` | Không |

Giải thích từng dòng:

- `const` nằm trong `if`, vòng lặp, `try` hay thân hàm là lỗi parse
  (`syntax error, unexpected token "const"`), vì hằng `const` phải có ngay lúc biên dịch, trước khi
  biết nhánh `if` nào chạy. Muốn định nghĩa có điều kiện thì dùng `define()`.
- *Biểu thức hằng* (constant expression) là biểu thức PHP tính được lúc biên dịch: số, chuỗi, mảng,
  hằng khác, phép toán trên chúng. Gọi hàm thì không: `const Z = strtoupper('a');` báo
  `Fatal error: Constant expression contains invalid operations`. Danh sách được nới dần qua các bản:
  từ 8.1 được dùng `new` (ví dụ `const ORIGIN = new ArrayObject([1]);`) và case của enum; từ 8.5 được
  dùng phép ép kiểu (`const PORT = (int) '8080';`), closure và first-class callable
  (`const UPPER = strtoupper(...);`).
- Về namespace (học ở [Chương 11](11-namespace-composer.md)): trong file có `namespace App;`,
  `const VERSION = '2.0';` tạo hằng `App\VERSION`, còn `define('BUILD', 42);` tạo hằng `\BUILD` ở
  namespace toàn cục. Manual ghi rõ `define()` coi tên là chuỗi thường, không gắn namespace hiện tại;
  muốn đặt vào namespace phải viết `define('App\REGION', 'vn')` hoặc `define(__NAMESPACE__ . '\REGION', 'vn')`.

Lời khuyên: dùng `const` cho hằng toàn cục bình thường (rõ ràng, công cụ phân tích tĩnh hiểu được,
đúng namespace). Chỉ dùng `define()` khi thật sự cần tên hay giá trị tính ra lúc chạy, hoặc cần định
nghĩa có điều kiện.

Ví dụ attribute trên hằng (chỉ chạy trên PHP 8.5; trên 8.4 dòng `#[...]` trước `const` là lỗi parse):

```php
<?php declare(strict_types=1);

#[\Deprecated(message: 'dùng MAX_UPLOAD_MB', since: '2.0')]
const MAX_UPLOAD = 10;

echo MAX_UPLOAD, "\n";
// Deprecated: Constant MAX_UPLOAD is deprecated since 2.0, dùng MAX_UPLOAD_MB in ... on line 6
// 10
```

⚠️ **Dùng hằng chưa định nghĩa là `Error` từ PHP 8.0.**

```php
<?php
echo UNKNOWN_CONST;
// Fatal error: Uncaught Error: Undefined constant "UNKNOWN_CONST" in ...
```

Theo manual, trước 8.0 PHP coi tên hằng không tồn tại là chuỗi cùng tên (in ra `UNKNOWN_CONST`) và chỉ
cảnh báo. Toán tử `??` cũng không cứu được: `echo UNKNOWN_CONST ?? 'x';` vẫn ném `Error`. Kiểm tra
bằng `defined()` trước khi dùng nếu không chắc hằng có tồn tại.

⚠️ **Định nghĩa lại một hằng không đổi được giá trị**, chỉ sinh warning:

```php
<?php declare(strict_types=1);

define('APP_NAME', 'Shop');
var_dump(define('APP_NAME', 'Other'));
// Warning: Constant APP_NAME already defined in ... on line 4             (PHP 8.4)
// Warning: Constant APP_NAME already defined, this will be an error in PHP 9 in ...   (PHP 8.5)
// bool(false)
echo APP_NAME, "\n";   // in ra: Shop
```

`const` khai báo lại cũng cho warning tương tự. PHP 8.5 chính thức *deprecate* việc định nghĩa lại
hằng: thông báo vẫn ở mức warning nhưng ghi rõ PHP 9 sẽ biến nó thành lỗi.

⚠️ Hằng chứa object (8.1+) chỉ bảo đảm không gán lại được tên hằng, không làm object bất biến:

```php
<?php declare(strict_types=1);

const ORIGIN = new ArrayObject([1]);
ORIGIN->append(2);        // vẫn sửa được nội dung object
var_dump(count(ORIGIN));  // in ra: int(2)
```

Trong code hướng đối tượng, phần lớn hằng bạn viết sẽ là hằng class:

```php
final class Order
{
    public const STATUS_PAID = 'paid';
}
echo Order::STATUS_PAID;   // paid
```

Hằng class có visibility (`public`, `protected`, `private`), có thể `final` (8.1) và khai báo kiểu
(8.3). Chúng được học ở [Chương 09](09-oop-co-ban.md). Khi một nhóm hằng biểu diễn tập giá trị
đóng (trạng thái đơn hàng chẳng hạn), *enum* thường là lựa chọn tốt hơn
([Chương 10](10-oop-nang-cao.md)).

### 5.3 Hằng có sẵn

PHP và các extension định nghĩa sẵn rất nhiều hằng. Những hằng của core hay dùng:

| Hằng | Ý nghĩa | Ví dụ giá trị |
|---|---|---|
| `PHP_VERSION` | Phiên bản PHP dạng chuỗi | `"8.5.10"` |
| `PHP_VERSION_ID` | Phiên bản dạng số nguyên, dễ so sánh | `80510` |
| `PHP_MAJOR_VERSION`, `PHP_MINOR_VERSION` | Số phiên bản chính, phụ | `8`, `5` |
| `PHP_OS_FAMILY` | Họ hệ điều hành: `'Windows'`, `'BSD'`, `'Darwin'`, `'Solaris'`, `'Linux'` hoặc `'Unknown'` | `"Linux"` |
| `PHP_SAPI` | SAPI đang chạy ([Chương 02](02-php-chay-nhu-the-nao.md)) | `"cli"`, `"fpm-fcgi"` |
| `PHP_EOL` | Ký tự xuống dòng của hệ điều hành | `"\n"` |
| `PHP_INT_MAX`, `PHP_INT_MIN` | Số nguyên lớn nhất, nhỏ nhất | `9223372036854775807` trên hệ 64 bit |
| `PHP_INT_SIZE` | Số byte của một int | `8` trên hệ 64 bit |
| `PHP_FLOAT_EPSILON` | Số dương nhỏ nhất `x` sao cho `1.0 + x != 1.0` | `2.220446049250313E-16` |
| `DIRECTORY_SEPARATOR` | Ký tự phân cách thư mục | `"/"` (Windows: `"\"`) |
| `E_ALL`, `E_WARNING`, ... | Các mức lỗi, dùng với `error_reporting` ([Chương 12](12-loi-exception.md)) | |

(Cột ví dụ chỉ để minh hoạ; giá trị thật tuỳ máy, hệ điều hành và phiên bản PHP.)

`PHP_VERSION_ID` được tính bằng `major * 10000 + minor * 100 + release`, nên so sánh phiên bản chỉ cần
so sánh số:

```php
if (PHP_VERSION_ID < 80300) {
    // code tương thích cho PHP 8.2 trở về trước
}
```

`true`, `false`, `null` cũng là hằng có sẵn, và là ngoại lệ không phân biệt hoa thường (mục 1.4).
Extension định nghĩa hằng của riêng nó, ví dụ `JSON_THROW_ON_ERROR` của extension JSON, hay hằng class
như `PDO::ATTR_ERRMODE`. Xem toàn bộ hằng do bạn tự định nghĩa bằng
`get_defined_constants(true)['user']`.

### 5.4 Magic constants

*Magic constants* (hằng "ma thuật") là các từ khoá mà PHP thay bằng thông tin về vị trí của chính
nó trong mã nguồn: file nào, dòng nào, trong hàm, class, namespace nào. Manual nhấn mạnh chúng
không phải hằng thật: `defined('__LINE__')` trả về `false`, và chúng không phân biệt hoa thường
(`__line__` vẫn chạy). Có chín magic constant:

| Tên | Giá trị |
|---|---|
| `__LINE__` | Số dòng hiện tại |
| `__FILE__` | Đường dẫn đầy đủ của file chứa nó (symlink đã được phân giải) |
| `__DIR__` | Thư mục của file đó, bằng `dirname(__FILE__)`; không có `/` ở cuối trừ khi là thư mục gốc |
| `__FUNCTION__` | Tên hàm (kèm namespace); trong method chỉ là tên method |
| `__CLASS__` | Tên class (kèm namespace); trong trait là tên class đang dùng trait |
| `__TRAIT__` | Tên trait (kèm namespace) |
| `__METHOD__` | `Class::method`; trong trait thì dùng tên trait thay cho tên class |
| `__PROPERTY__` | Tên property, chỉ dùng bên trong *property hook* (PHP 8.4+, Chương 10) |
| `__NAMESPACE__` | Tên namespace hiện tại |

Dùng ngoài ngữ cảnh phù hợp (ví dụ `__CLASS__` bên ngoài class) thì được thay bằng chuỗi rỗng. Gần họ
với nhóm này là cú pháp `TênClass::class`, cho ra tên class đầy đủ dạng chuỗi; từ PHP 8.0 dùng được
cả trên object: `$invoice::class`.

```php
<?php declare(strict_types=1);

namespace App\Billing;

trait Loggable
{
    public function where(): string
    {
        return __CLASS__ . ' | ' . __TRAIT__ . ' | ' . __METHOD__;
    }
}

final class Invoice
{
    use Loggable;

    public function method(): string
    {
        return __METHOD__ . ' | ' . __FUNCTION__;
    }
}

function helper(): string
{
    return __FUNCTION__;
}

echo __NAMESPACE__, "\n";             // App\Billing
echo helper(), "\n";                  // App\Billing\helper
echo (new Invoice())->method(), "\n"; // App\Billing\Invoice::method | method
echo (new Invoice())->where(), "\n";  // App\Billing\Invoice | App\Billing\Loggable | App\Billing\Loggable::where
echo Invoice::class, "\n";            // App\Billing\Invoice
var_dump(__CLASS__);                  // string(0) ""   (đang ở ngoài class)
```

Với closure, `__FUNCTION__` cho kết quả khác nhau giữa các phiên bản: PHP 8.3 trả về `{closure}` (kèm
namespace, ví dụ `App\Billing\{closure}`), từ PHP 8.4 trả về tên có cả vị trí, dạng
`{closure:/đường/dẫn/file.php:39}`. Đừng viết logic dựa vào chuỗi này.

Ứng dụng quan trọng nhất: **`__DIR__` để include file**. Đường dẫn tương đối bắt đầu bằng `./` hay
`../` được PHP tính từ *thư mục làm việc hiện tại* (current working directory, thư mục bạn đứng khi
gõ lệnh), không phải từ thư mục chứa file đang chạy. Giả sử có cấu trúc:

```
proj/
└── bin/
    ├── run.php
    └── config.php
```

```php
<?php declare(strict_types=1);
// proj/bin/run.php

$ok = require __DIR__ . '/config.php';   // luôn đúng: tính từ thư mục chứa run.php
$bad = require './config.php';           // tính từ thư mục bạn đứng khi chạy lệnh
```

Đứng ở `proj/bin` và chạy `php run.php` thì cả hai dòng đều chạy. Đứng ở `proj` và chạy
`php bin/run.php` thì dòng thứ hai thất bại:

```
Warning: require(./config.php): Failed to open stream: No such file or directory in .../bin/run.php on line 5
Fatal error: Uncaught Error: Failed opening required './config.php' (include_path='.:') in .../bin/run.php:5
```

(Phần `include_path='.:'` tuỳ cấu hình từng máy.) Đây là lỗi kinh điển của cron job: cron chạy script
từ một thư mục khác với lúc bạn thử bằng tay. Vì vậy hai file khởi động của Laravel đều nạp
autoloader qua `__DIR__`: `public/index.php` viết `require __DIR__.'/../vendor/autoload.php';`, file
`artisan` viết `require __DIR__.'/vendor/autoload.php';`.

## 6. null, isset, unset, empty

Bốn thứ này đều xoay quanh câu hỏi "biến này có giá trị không?", và nhầm lẫn giữa chúng là một trong
những nguồn bug phổ biến nhất của PHP, nhất là khi xử lý dữ liệu form.

### 6.1 null: "không có giá trị"

`null` là kiểu dữ liệu chỉ có đúng một giá trị, cũng tên là `null` (viết `NULL` hay `Null` đều
được). Một biến mang giá trị `null` trong ba trường hợp:

1. Được gán `null`: `$x = null;`
2. Chưa từng được gán (đọc nó sẽ có warning, mục 3.3).
3. Đã bị `unset()` (đọc nó cũng có warning).

Kiểm tra null bằng `$x === null` hoặc `is_null($x)`; hai cách cho cùng kết quả. Cả hai đều đọc biến
nên đều phát warning nếu biến chưa tồn tại. Code hiện đại hay dùng `=== null` hơn vì là toán tử, không
phải lời gọi hàm.

Đối chiếu: trong Java chỉ biến kiểu tham chiếu mới có thể là `null` (`int` thì không). Go không có
`null` cho kiểu giá trị: biến chưa gán nhận *zero value* (`0`, `""`, `false`), còn `nil` chỉ dành
cho con trỏ, map, slice, interface... Trong PHP biến nào cũng có thể chứa `null`. Muốn cấm `null`
thì khai báo kiểu: tham số `string $name` không nhận `null`, phải viết `?string $name` mới nhận
([Chương 04](04-kieu-du-lieu.md)).

### 6.2 isset: "có tồn tại và khác null không?"

`isset($x)` trả về `true` khi biến **tồn tại và khác `null`**. Nó là language construct (giống `echo`),
nên có một khả năng đặc biệt: không bao giờ phát warning khi biến, key hay property không tồn tại, dù
lồng sâu bao nhiêu tầng.

```php
<?php declare(strict_types=1);

$user = ['name' => 'Lan', 'phone' => null, 'address' => ['city' => 'Huế']];

var_dump(isset($user['name']));                  // bool(true)
var_dump(isset($user['phone']));                 // bool(false): key CÓ, nhưng giá trị là null
var_dump(array_key_exists('phone', $user));      // bool(true): chỉ hỏi key có tồn tại không
var_dump(isset($user['address']['city']));       // bool(true)
var_dump(isset($user['address']['zip']['x']));   // bool(false), không warning
var_dump(isset($khongCo['a']['b']));             // bool(false), không warning

$a = 'x';
$b = null;
var_dump(isset($a, $b));                         // bool(false): nhiều đối số thì TẤT CẢ phải "set"

echo $user['email'] ?? 'chưa có email', "\n";    // in ra: chưa có email
```

Dòng cuối dùng toán tử `??` (*null coalescing*): `$a ?? $b` trả về `$a` nếu `isset($a)`, ngược lại trả
về `$b`. Nó có cùng ngữ nghĩa với `isset` (không warning khi thiếu key) và là cách viết gọn nhất để lấy
giá trị mặc định. Chi tiết `??` và `??=` ở [Chương 07](07-toan-tu-dieu-khien.md).

⚠️ **`isset` coi "có nhưng bằng null" là "không có".** Với mảng có thể chứa `null` (dữ liệu JSON, dòng
từ database có cột NULL), muốn biết key có tồn tại hay không thì dùng `array_key_exists()`. Với object
thì tương tự là `property_exists()`. So sánh hai hàm này kỹ hơn ở [Chương 06](06-mang.md).

⚠️ **`isset` chỉ nhận biến** (kể cả phần tử mảng, property). Đưa biểu thức hay hằng vào là lỗi biên
dịch:

```php
<?php
var_dump(isset(trim(' ')));
// Fatal error: Cannot use isset() on the result of an expression (you can use "null !== expression" instead) in ...
```

Kiểm tra hằng thì dùng `defined('TÊN')` (mục 5.2).

⚠️ Với object có magic method `__get` (Chương 10), `isset($obj->prop)` gọi `__isset()` nếu class định
nghĩa nó; nếu class quên định nghĩa `__isset()` thì `isset` trả về `false` dù `$obj->prop` đọc ra giá
trị bình thường. Eloquent của Laravel có định nghĩa `__isset()` nên `isset($user->name)` hoạt động
đúng.

### 6.3 unset: xoá biến

`unset()` xoá một hoặc nhiều biến. Sau đó `isset()` trả về `false` và đọc biến sẽ có warning. `unset`
một biến không tồn tại thì không sao, không có warning.

```php
<?php declare(strict_types=1);

$a = 1; $b = 2;
unset($a, $b);                   // xoá nhiều biến một lúc
var_dump(isset($a));             // bool(false)
unset($khongCo);                 // không warning

$list = ['a', 'b', 'c'];
unset($list[1]);                 // xoá một phần tử: chỉ số KHÔNG được đánh lại
var_dump(array_keys($list));     // [0, 2]  (var_dump in dạng nhiều dòng)
$list[] = 'd';                   // phần tử mới nhận chỉ số 3: chỉ số nguyên lớn nhất từng dùng + 1
var_dump(array_values($list));   // ['a', 'c', 'd']: array_values đánh lại chỉ số từ 0
```

Hành vi của `unset` bên trong hàm phụ thuộc loại biến (manual):

| Bạn `unset` cái gì trong hàm | Kết quả |
|---|---|
| Biến khai báo bằng `global $x` | Chỉ xoá biến cục bộ (cắt reference), biến toàn cục còn nguyên. Muốn xoá thật: `unset($GLOBALS['x'])` |
| Tham số truyền theo tham chiếu `&$x` | Chỉ xoá tên cục bộ, biến của bên gọi còn nguyên |
| Biến `static` | Chỉ mất trong phần còn lại của lần gọi đó; lần gọi sau giá trị cũ quay lại |
| `$this` trong method | Lỗi: `Fatal error: Cannot unset $this` |

`unset($x)` và `$x = null` khác nhau ở chỗ nào? Cả hai đều làm `isset($x)` thành `false`, nhưng:

| | `$x = null;` | `unset($x);` |
|---|---|---|
| Biến còn tồn tại? | Còn, giá trị là `null` | Không |
| Đọc `$x` sau đó | `null`, không warning | `null`, có warning `Undefined variable` |
| `array_key_exists('x', get_defined_vars())` | `true` | `false` |
| Với phần tử mảng | Key còn, giá trị `null` | Key bị xoá khỏi mảng |

Về bộ nhớ: `unset` chỉ xoá cái tên. Giá trị được giải phóng khi không còn tên nào khác (biến khác,
phần tử mảng, reference) dùng nó. PHP theo dõi việc này bằng cơ chế đếm tham chiếu (*reference
counting*), học ở [Chương 19](19-ben-trong-engine.md). Trong script web ngắn bạn hiếm khi cần `unset`
để tiết kiệm bộ nhớ, vì cuối request mọi thứ được dọn sạch; nó có ích trong script chạy lâu xử lý dữ
liệu lớn.

Cú pháp ép kiểu `(unset) $x` (trả về `null`) đã bị xoá ở PHP 8.0: viết ra là
`Fatal error: The (unset) cast is no longer supported`.

### 6.4 empty: "có rỗng không?"

`empty($x)` trả về `true` nếu biến không tồn tại, hoặc giá trị của nó tương đương `false`. Manual
mô tả nó gần như cách viết gọn của `!isset($x) || $x == false`. Giống `isset`, nó không phát warning khi
biến không tồn tại. Khác `isset`, nó nhận được cả biểu thức: `empty(trim($s))` hợp lệ.

Các giá trị bị coi là `false` khi đổi sang bool (gọi là *falsy*), theo manual:

- `false`
- số nguyên `0`, số thực `0.0` và `-0.0`
- chuỗi rỗng `""` và chuỗi `"0"`
- mảng rỗng `[]`
- `null` (kể cả biến chưa gán)
- một số object nội bộ tự định nghĩa cách đổi sang bool, ví dụ object GMP biểu diễn số 0

Mọi giá trị khác là *truthy*, kể cả `" "` (một dấu cách), `"0.0"`, `"false"`, `"null"`, `[0]`.

⚠️ **Bẫy chuỗi `"0"`.** Dữ liệu form luôn là chuỗi, và `"0"` là một giá trị hợp lệ rất thường gặp:

```php
<?php declare(strict_types=1);

$input = ['quantity' => '0', 'note' => ' '];   // giả sử đây là $_POST

if (empty($input['quantity'])) {
    echo "Thiếu số lượng\n";      // in ra dòng này dù người dùng đã nhập 0
}
if (!empty($input['note'])) {
    echo "Có ghi chú\n";          // in ra dòng này dù ghi chú chỉ là một dấu cách
}
```

Cả hai kết luận đều sai với ý định: số lượng `0` bị coi là "thiếu", còn ghi chú toàn khoảng trắng lại
được coi là "có".

⚠️ **`empty` nuốt lỗi gõ sai tên.** `empty($usre)` (gõ nhầm `$user`) trả về `true` mà không có warning
nào, vì với `empty` "không tồn tại" là chuyện bình thường. Lỗi gõ sai biến thành một nhánh logic sai
chạy âm thầm.

Lời khuyên: viết điều kiện tường minh theo đúng ý bạn muốn kiểm tra, thay vì `empty`:

| Bạn muốn hỏi | Viết |
|---|---|
| Biến hoặc key có tồn tại và khác null? | `isset($x)`, hoặc `$x ?? $default` |
| Key có tồn tại không (kể cả khi giá trị null)? | `array_key_exists('k', $arr)` |
| Giá trị có phải null? | `$x === null` |
| Chuỗi rỗng? | `$s === ''` |
| Chuỗi trống hoặc toàn khoảng trắng? | `trim($s) === ''` |
| Mảng rỗng? | `$arr === []` hoặc `count($arr) === 0` |

Laravel có hai helper `blank()` và `filled()` sát với trực giác hơn khi xử lý input: theo mã nguồn
Laravel 13, `blank()` coi `null`, chuỗi rỗng hoặc toàn khoảng trắng, và collection/mảng rỗng là "trống",
còn số (kể cả `0`), chuỗi `"0"` và bool (kể cả `false`) không trống.

### 6.5 Bảng tổng hợp

Kết quả chạy thật trên PHP 8.5 (cột "chưa có" là biến chưa từng được gán):

| Giá trị của `$x` | `isset($x)` | `empty($x)` | `$x === null` | `(bool) $x` |
|---|---|---|---|---|
| chưa có | `false` | `true` | warning, `true` | warning, `false` |
| `null` | `false` | `true` | `true` | `false` |
| `false` | `true` | `true` | `false` | `false` |
| `0` | `true` | `true` | `false` | `false` |
| `0.0` | `true` | `true` | `false` | `false` |
| `"0"` | `true` | `true` | `false` | `false` |
| `""` | `true` | `true` | `false` | `false` |
| `" "` | `true` | `false` | `false` | `true` |
| `"0.0"` | `true` | `false` | `false` | `true` |
| `"false"` | `true` | `false` | `false` | `true` |
| `[]` | `true` | `true` | `false` | `false` |
| `[0]` | `true` | `false` | `false` | `true` |
| `"a"`, `1`, `true` | `true` | `false` | `false` | `true` |

Cách đọc bảng:

- `isset` chỉ quan tâm "tồn tại và khác `null`": `false`, `0`, `""` đều là "set".
- Với biến đã tồn tại, `empty($x)` luôn bằng `!(bool) $x`. Khác biệt duy nhất là với biến chưa có:
  `empty` im lặng, còn ép kiểu `(bool)` đọc biến nên có warning.
- `"0"` là chuỗi duy nhất khác chuỗi rỗng bị coi là falsy; `"0.0"` và `" "` thì không.

Vì sao `"0"` lại falsy và các quy tắc đổi kiểu khác: [Chương 04](04-kieu-du-lieu.md).

## Lỗi thường gặp

| Lỗi | Vì sao xảy ra | Cách tránh |
|---|---|---|
| Có `?>` ở cuối file chỉ chứa PHP, sau nó dư khoảng trắng | Phần thừa là inline HTML, thành output, làm hỏng `header()`, `session_start()` ("headers already sent") | Không viết thẻ đóng trong file thuần PHP (PSR-12) |
| Dùng short tag `<?` | Server tắt `short_open_tag` thì code bị in nguyên văn ra trình duyệt | Chỉ dùng `<?php` và `<?=` |
| Viết `?>` trong comment `//` | Comment một dòng kết thúc ở `?>`, phần sau bị in ra | Không đặt `?>` trong comment một dòng |
| Comment bằng `#[...]` trên PHP 8 | `#[` là cú pháp attribute | Dùng `//` hoặc `# [` có dấu cách |
| Debug bằng `echo` hoặc `print_r` | Không phân biệt `false`/`null`/`""`, làm tròn số thực | Dùng `var_dump` |
| Thiếu `;`, lỗi báo ở dòng sau | Parser chỉ phát hiện khi gặp token kế tiếp | Đọc cả dòng phía trên dòng báo lỗi |
| Hàm đọc biến toàn cục mà không truyền vào | Hàm có scope riêng, biến bên ngoài không nhìn thấy | Truyền qua tham số, trả kết quả qua `return` |
| Tưởng `if`, `for` tạo scope riêng | PHP chỉ có global scope và function scope | Khởi tạo biến trước khối lệnh, đặt tên rõ ràng |
| Biến static, global trên Octane hay queue worker | Process sống lâu, giá trị sống qua nhiều request | Không giữ trạng thái theo request trong static/global |
| `extract()` hoặc variable variables với dữ liệu người dùng | Người dùng chọn được tên biến, ghi đè biến quan trọng | Dùng mảng; nếu buộc dùng `extract` thì dùng `EXTR_SKIP` |
| `define('X', ...)` trong `namespace App;` | `define` không gắn namespace hiện tại, tạo `\X` | Dùng `const`, hoặc ghi đủ tên `'App\X'` |
| `require './file.php'` hoặc `'../file.php'` | Tính từ thư mục làm việc hiện tại, không phải thư mục của file | `require __DIR__ . '/file.php'` |
| `isset($arr['k'])` khi giá trị có thể là `null` | `isset` coi `null` là "không có" | `array_key_exists('k', $arr)` |
| `empty($input['qty'])` với input `"0"` | `"0"` là falsy | So sánh tường minh: `=== ''`, `trim() === ''`, `=== null` |
| Dùng `&` để "đỡ copy" mảng | Copy-on-write vốn không copy khi không sửa; reference làm luồng dữ liệu khó theo dõi | Chỉ dùng reference khi thật sự cần chia sẻ một biến |

## Tóm tắt chương

- PHP chỉ chạy code nằm giữa `<?php` và `?>`; phần ngoài thẻ được in nguyên văn. File chỉ chứa PHP
  không viết thẻ đóng. `<?=` là viết tắt của `<?php echo` và luôn dùng được.
- Câu lệnh kết thúc bằng `;`, PHP không tự chèn `;` khi xuống dòng. Tên biến và hằng phân biệt hoa thường; từ khoá,
  tên hàm, tên class thì không.
- `echo` để in cho người dùng (luôn đổi sang chuỗi, kể cả với `strict_types`); `printf`/`sprintf` để
  định dạng; `var_dump` để debug chính xác kiểu và giá trị; `print_r` để xem nhanh; `var_export` để
  sinh code PHP.
- Biến bắt đầu bằng `$`, ra đời ở lần gán đầu, kiểu thuộc về giá trị. Đọc biến chưa gán cho warning
  và `null`. Gán mặc định là theo giá trị; `$b = &$a` tạo hai tên cho cùng một ô (reference), không phải
  con trỏ.
- PHP chỉ có global scope và function scope; khối `if`, `for` không tạo scope. Hàm không thấy biến bên
  ngoài; truyền qua tham số thay vì dùng `global`. Biến `static` giữ giá trị giữa các lần gọi; từ 8.3
  được khởi tạo bằng biểu thức bất kỳ.
- Superglobals (`$_GET`, `$_POST`, `$_SERVER`...) dùng được ở mọi scope và chứa dữ liệu không tin cậy.
- Hằng không có `$`, không đổi được, thấy ở mọi nơi. `const` lúc biên dịch, ở cấp cao nhất, theo
  namespace; `define()` lúc chạy, ở đâu cũng được, mặc định ở namespace toàn cục. Dùng hằng chưa định
  nghĩa là `Error` từ PHP 8.0.
- Magic constants (`__DIR__`, `__FILE__`, `__LINE__`, `__CLASS__`...) cho biết vị trí trong mã nguồn.
  Luôn include bằng `__DIR__`.
- `isset`: tồn tại và khác `null`. `empty`: không tồn tại hoặc falsy, kể cả `"0"`. `unset`: xoá tên
  biến. Ưu tiên điều kiện tường minh (`=== null`, `=== ''`, `array_key_exists`) thay cho `empty`.

## Câu hỏi tự kiểm tra

1. Vì sao file chỉ chứa PHP không nên có thẻ đóng `?>`? Điều gì xảy ra với ký tự xuống dòng nằm ngay
   sau `?>`? (mục 1.3)
2. `echo` và `print` khác nhau ở đâu? Vì sao `echo("a");` chạy được mà `echo("a", "b");` lại lỗi?
   (mục 2.1)
3. Bạn cần biết một giá trị đang là `false`, `null` hay `""`. Dùng hàm nào, và vì sao không dùng
   `print_r`? (mục 2.3)
4. Vì sao `echo 0.1 + 0.2;` in ra `0.3` trong khi `var_dump(0.1 + 0.2)` in ra con số khác? (mục 2.3)
5. Sau `$b = &$a; unset($a);` thì `$b` còn giá trị không? Nếu thay `&` bằng phép gán thường thì có gì
   khác? (mục 3.4, 3.5)
6. Một hàm cần tỷ lệ thuế đang nằm trong biến toàn cục `$taxRate`. Nêu ba cách để hàm dùng được giá
   trị đó và cách bạn chọn cho code thật. (mục 4.1, 4.3)
7. Biến static trong một hàm sống bao lâu khi chạy trên PHP-FPM, và khi chạy trên Laravel Octane? Hệ
   quả với dữ liệu của người dùng? (mục 4.4)
8. Khi nào bắt buộc phải dùng `define()` thay vì `const`? Trong file có `namespace App;`, lệnh
   `define('X', 1)` tạo ra hằng tên đầy đủ là gì? (mục 5.2)
9. Vì sao nên viết `require __DIR__ . '/config.php'` thay vì `require './config.php'`? (mục 5.4)
10. Với `$data = ['a' => null, 'b' => '0']`, cho biết kết quả của `isset($data['a'])`,
    `array_key_exists('a', $data)`, `empty($data['b'])`, `isset($data['c'])`. (mục 6.2, 6.4)

## Bài tập

**Bài 1. Bảng soi giá trị.** Viết script `soi-gia-tri.php` duyệt danh sách giá trị
`[null, false, true, 0, 1.0, "0", "", " ", [], [0], "abc", 0.1 + 0.2]` và với mỗi giá trị in một
dòng, các cột căn thẳng bằng `printf`: kết quả `var_export($v, true)`, kết quả khi `echo` (đặt trong
ngoặc vuông để thấy chuỗi rỗng; riêng mảng thì ghi `Array`), `isset`, `empty`, `$v === null`. Chạy
xong, giải thích bằng lời từng dòng mà cột `echo` gây hiểu lầm.

**Bài 2. Bộ sinh mã đơn hàng.** Viết hàm `nextOrderCode(): string` trả về lần lượt `"DH0001"`,
`"DH0002"`, ... mỗi lần được gọi, dùng biến `static` và `sprintf`. Gọi ba lần và in kết quả. Sau đó
bổ sung khả năng đặt lại bộ đếm về 0 mà không dùng biến toàn cục (gợi ý: một hàm khác không nhìn
thấy biến static của `nextOrderCode`; hãy nghĩ cách để chính hàm đó nhận lệnh đặt lại). Cuối cùng, viết
vài câu trả lời: nếu hàm này chạy trong một ứng dụng PHP-FPM có nhiều request đồng thời thì mã đơn
hàng có bị trùng không? Còn trên Octane? Vậy trong hệ thống thật nên sinh mã ở đâu?

**Bài 3. Config cache tự làm.** Tạo thư mục `mini/` gồm `config/app.php` và `config/db.php` (mỗi file
chỉ có `return [...]`), một script `mini/build.php` gộp hai file thành mảng `['app' => ..., 'db' => ...]`
rồi ghi ra `mini/cache/config.php` bằng `var_export`, và một script `mini/show.php` nạp file cache rồi in
`db.host`. Yêu cầu: mọi đường dẫn dùng `__DIR__`, và cả hai script phải chạy đúng dù bạn đứng ở thư mục
nào (thử chạy từ thư mục cha và từ một thư mục khác hẳn). Sau đó thêm một closure vào `config/app.php`,
chạy lại hai script, mô tả lỗi gặp phải và giải thích nguyên nhân.

**Bài 4. Kiểm tra dữ liệu form không dùng empty.** Cho
`$form = ['name' => '  ', 'age' => '0', 'email' => null, 'note' => 'ok'];` (giả lập `$_POST`). Viết
hàm `describeField(array $form, string $key): string` trả về một trong bốn kết quả: `"không gửi"` (key
không có), `"null"`, `"trống"` (chuỗi rỗng hoặc toàn khoảng trắng), hoặc `"có giá trị: ..."`, và
không được dùng `empty()`. In kết quả cho các key `name`, `age`, `email`, `note`, `coupon`. Sau đó
viết một phiên bản chỉ dùng `empty()` và ghi lại những key mà hai phiên bản cho kết luận khác nhau.

## Đọc thêm

- PHP Manual, cú pháp cơ bản: [PHP tags](https://www.php.net/manual/en/language.basic-syntax.phptags.php) ·
  [Instruction separation](https://www.php.net/manual/en/language.basic-syntax.instruction-separation.php) ·
  [Comments](https://www.php.net/manual/en/language.basic-syntax.comments.php)
- PHP Manual, in dữ liệu: [echo](https://www.php.net/manual/en/function.echo.php) ·
  [print](https://www.php.net/manual/en/function.print.php) ·
  [printf](https://www.php.net/manual/en/function.printf.php) ·
  [var_dump](https://www.php.net/manual/en/function.var-dump.php) ·
  [print_r](https://www.php.net/manual/en/function.print-r.php) ·
  [var_export](https://www.php.net/manual/en/function.var-export.php)
- PHP Manual, biến: [Basics](https://www.php.net/manual/en/language.variables.basics.php) ·
  [Variable variables](https://www.php.net/manual/en/language.variables.variable.php) ·
  [Variable scope](https://www.php.net/manual/en/language.variables.scope.php) ·
  [Superglobals](https://www.php.net/manual/en/language.variables.superglobals.php) ·
  [$GLOBALS](https://www.php.net/manual/en/reserved.variables.globals.php) ·
  [What References Do](https://www.php.net/manual/en/language.references.whatdo.php)
- PHP Manual, hằng: [Constants](https://www.php.net/manual/en/language.constants.php) ·
  [Syntax](https://www.php.net/manual/en/language.constants.syntax.php) ·
  [define](https://www.php.net/manual/en/function.define.php) ·
  [Core predefined constants](https://www.php.net/manual/en/reserved.constants.php) ·
  [Magic constants](https://www.php.net/manual/en/language.constants.magic.php) ·
  [include](https://www.php.net/manual/en/function.include.php)
- PHP Manual, kiểm tra giá trị: [isset](https://www.php.net/manual/en/function.isset.php) ·
  [unset](https://www.php.net/manual/en/function.unset.php) ·
  [empty](https://www.php.net/manual/en/function.empty.php) ·
  [Booleans: converting to boolean](https://www.php.net/manual/en/language.types.boolean.php) ·
  [Type comparison tables](https://www.php.net/manual/en/types.comparisons.php)
- RFC: [Restrict $GLOBALS usage (8.1)](https://wiki.php.net/rfc/restrict_globals_usage) ·
  [Static variable inheritance (8.1)](https://wiki.php.net/rfc/static_variable_inheritance) ·
  [Arbitrary static variable initializers (8.3)](https://wiki.php.net/rfc/arbitrary_static_variable_initializers) ·
  [Attributes on constants (8.5)](https://wiki.php.net/rfc/attributes-on-constants) ·
  [Deprecations for PHP 8.5](https://wiki.php.net/rfc/deprecations_php_8_5) ·
  [Precise float value handling (7.1)](https://wiki.php.net/rfc/precise_float_value)
- php-src: [UPGRADING của PHP 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) (mỗi nhánh
  `PHP-8.x` có file UPGRADING tương ứng)
- Chuẩn code: [PSR-1](https://www.php-fig.org/psr/psr-1/) · [PSR-12](https://www.php-fig.org/psr/psr-12/)
- Laravel 13: [Helpers (`dd`, `dump`, `blank`, `filled`)](https://laravel.com/docs/13.x/helpers) ·
  [Octane: Managing Memory Leaks](https://laravel.com/docs/13.x/octane#managing-memory-leaks) ·
  [ConfigCacheCommand.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Console/ConfigCacheCommand.php)
