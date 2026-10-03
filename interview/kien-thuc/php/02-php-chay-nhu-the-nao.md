# Chương 02. PHP chạy như thế nào

> [← Mục lục](README.md) · [← Chương 01: PHP là gì và chạy chương trình đầu tiên](01-php-la-gi.md) · [Chương 03: Cú pháp cơ bản, biến và hằng →](03-cu-phap-bien-hang.md)

**Bạn sẽ học được:**

- Chuyện gì xảy ra từ lúc bạn gõ `php hello.php` tới lúc chữ hiện ra: lexer, parser, AST, compiler,
  opcode và Zend VM.
- Cách tự xem token và opcode của chính đoạn code bạn viết.
- OPcache là gì và vì sao nó làm PHP nhanh hơn rõ rệt mà không phải sửa dòng code nào.
- SAPI là gì; chạy PHP bằng CLI, bằng PHP-FPM và nhúng PHP vào chương trình khác (embed) khác nhau ra sao.
- Một HTTP request đi từ trình duyệt qua Nginx, PHP-FPM, script của bạn rồi quay về như thế nào.
- Mô hình *share-nothing*: vì sao biến không sống qua request, và PHP khác Node.js, Java, Go ở điểm này
  thế nào.

**Cần biết trước:** [Chương 01](01-php-la-gi.md) (đã cài PHP hoặc có Docker, đã chạy được một file
bằng lệnh `php`).

Cách chạy thử không cần cài PHP vào máy:

```bash
# Chạy ở thư mục chứa file .php của bạn
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php

# Hoặc mở chế độ tương tác (REPL)
docker run --rm -it php:8.5-cli php -a
```

## 1. Bức tranh lớn: "chạy" một file PHP nghĩa là gì

### 1.1 Máy tính không hiểu PHP

CPU chỉ biết chạy *mã máy* (machine code): các lệnh nhị phân rất đơn giản như "cộng hai thanh ghi",
"nhảy tới địa chỉ X". File `hello.php` của bạn chỉ là văn bản. Phải có một chương trình đứng giữa,
đọc văn bản đó và làm theo. Có hai cách kinh điển:

- *Compiler* (trình biên dịch): dịch toàn bộ chương trình sang mã máy trước khi chạy, ra một file
  chạy được. Ví dụ: `go build` biến code Go thành một file binary; lúc chạy không cần tới mã nguồn nữa.
- *Interpreter* (trình thông dịch): đọc chương trình và làm theo ngay lúc chạy, không sinh ra file
  mã máy nào.

Hầu hết ngôn ngữ hiện đại đi đường giữa: dịch mã nguồn sang một dạng trung gian gọn hơn (thường gọi là
*bytecode*), rồi một *máy ảo* (virtual machine, VM) chạy dạng trung gian đó. Máy ảo ở đây không phải
VirtualBox hay VMware; nó chỉ là một chương trình biết thực thi một bộ lệnh do chính nó định nghĩa.

PHP thuộc nhóm đi đường giữa:

1. Mỗi khi một file PHP được nạp, PHP biên dịch file đó sang *opcode* (tên gọi bytecode của PHP).
2. *Zend VM*, máy ảo nằm bên trong PHP, thực thi từng opcode.

Vì vậy câu "PHP là ngôn ngữ thông dịch" chỉ đúng một nửa. Chính xác hơn: PHP biên dịch sang opcode
ngay lúc chạy, opcode được máy ảo thông dịch; từ PHP 8.0 còn có thêm *JIT* (Just-In-Time compiler,
biên dịch phần code chạy nhiều sang mã máy ngay trong lúc chạy), nhưng JIT là tuỳ chọn và không bật
sẵn.

So sánh với các ngôn ngữ bạn có thể đã gặp:

| Ngôn ngữ | Dịch sang gì | Dịch lúc nào | Ai chạy kết quả | Kết quả dịch nằm ở đâu |
|---|---|---|---|---|
| Go | Mã máy | Trước khi chạy (`go build`) | CPU chạy trực tiếp | File binary trên đĩa |
| Java | Bytecode JVM | Trước khi chạy (`javac`); `java File.java` thì dịch trong bộ nhớ | JVM: thông dịch, rồi JIT phần chạy nhiều | File `.class`/`.jar` |
| PHP | Opcode | Lúc chạy, mỗi khi một file được nạp | Zend VM (JIT tuỳ chọn) | Chỉ trong RAM; OPcache giữ lại để dùng lần sau (mục 3) |
| Python (CPython) | Bytecode | Lúc chạy | Máy ảo của CPython | RAM; module được `import` còn được cache ra file `.pyc` |
| JavaScript (Node.js) | Bytecode, rồi mã máy cho phần chạy nhiều | Lúc chạy | Engine V8 | RAM |

Điểm khác biệt đáng nhớ của PHP: không có bước build. Bạn sửa file, chạy lại là thấy ngay. Cái giá
là việc biên dịch diễn ra lúc chạy, nên nếu không có cơ chế cache thì lần chạy nào cũng phải biên dịch
lại. Mục 3 nói về cơ chế cache đó (OPcache).

### 1.2 Bên trong chương trình `php` có gì

Chương trình `php` bạn đã chạy ở chương 01 không phải một khối duy nhất mà gồm nhiều lớp. Thư mục mã
nguồn của PHP (repo [php-src](https://github.com/php/php-src)) phản ánh đúng các lớp đó:

```
                          Thế giới bên ngoài
   terminal        Nginx (qua FastCGI)       Apache httpd        chương trình C khác
      │                    │                      │                       │
┌─────▼─────┐       ┌──────▼──────┐      ┌────────▼────────┐       ┌──────▼──────┐
│ SAPI cli  │       │ SAPI fpm    │      │ SAPI            │       │ SAPI embed  │  sapi/
│           │       │             │      │ apache2handler  │       │             │
└─────┬─────┘       └──────┬──────┘      └────────┬────────┘       └──────┬──────┘
      └────────────────────┴──────────┬───────────┴───────────────────────┘
                 ┌────────────────────▼───────────────────────┐
                 │ PHP core: đọc php.ini, vòng đời request,   │  main/
                 │ output, stream, dựng $_GET/$_POST/$_SERVER │
                 ├────────────────────────────────────────────┤
                 │ Zend Engine: lexer, parser, compiler,      │  Zend/
                 │ Zend VM, quản lý bộ nhớ, kiểu, object      │
                 ├────────────────────────────────────────────┤
                 │ Extension: standard, json, pdo, mbstring,  │  ext/
                 │ OPcache ...                                │
                 └────────────────────────────────────────────┘
```

(Cột bên phải là thư mục tương ứng trong php-src.)

- *Zend Engine*: lõi của ngôn ngữ. Nó biên dịch và chạy code, quản lý bộ nhớ, biến, object. Theo trang
  lịch sử PHP trên php.net, tên "Zend" ghép từ tên hai tác giả Zeev Suraski và Andi Gutmans; engine
  này ra mắt năm 1999 và PHP 4.0 (tháng 5/2000) là bản đầu tiên chạy trên nó. PHP 7.0 dùng Zend
  Engine 3.0; hàm `zend_version()` cho biết phiên bản engine bạn đang chạy.
- *Extension*: thư viện viết bằng C cắm vào engine để cung cấp hàm và class. `array_map()` nằm trong
  extension `standard`, `json_encode()` trong `json`, class `PDO` trong extension `PDO` (xem được bằng
  `(new ReflectionFunction('array_map'))->getExtensionName()`). Chương 01 đã giới thiệu lệnh `php -m`
  để liệt kê extension.
- *SAPI* (Server API): lớp nói chuyện với thế giới bên ngoài. Engine không biết "terminal" hay "HTTP
  request" là gì; SAPI cho engine biết lấy input ở đâu và gửi output đi đâu. Mục 4 nói kỹ.
- *PHP core* (thư mục `main/`): phần keo dính các lớp trên: đọc `php.ini`, điều khiển vòng đời khởi
  động và kết thúc, hệ thống output, stream, dựng các biến `$_GET`, `$_POST`, `$_SERVER`.

### 1.3 Hành trình của một file: nhìn toàn cảnh trước

Lấy file nhỏ nhất có thể:

```php
<?php
echo "Hello\n";
```

Từ lúc bạn gõ `php hello.php` tới lúc chữ `Hello` hiện ra, file này đi qua bốn chặng (dòng token
bỏ qua các token khoảng trắng, cây AST vẽ đơn giản hoá; dòng opcode là output thật, cách xem ở mục 2.5):

```
 hello.php (văn bản)
     │
     │ ① Lexer: cắt văn bản thành các "từ" (token)
     ▼
 T_OPEN_TAG   T_ECHO   T_CONSTANT_ENCAPSED_STRING   ';'
     │
     │ ② Parser: kiểm tra ngữ pháp, ghép token thành cây
     ▼
 AST:  statement list
        └── echo
             └── "Hello\n"
     │
     │ ③ Compiler: duyệt cây, sinh lệnh cho máy ảo
     ▼
 opcode:  0000 ECHO string("Hello\n")
          0001 RETURN int(1)
     │
     │ ④ Zend VM: chạy lần lượt từng opcode
     ▼
 "Hello" xuất hiện trên màn hình
```

Chặng ①②③ gọi chung là *biên dịch* (compile), chặng ④ là *thực thi* (execute). Hai hệ quả bạn sẽ gặp
lại nhiều lần trong chương:

1. **Cả file được biên dịch xong rồi mới chạy dòng đầu tiên.** Một lỗi cú pháp ở dòng cuối file làm cả
   file không chạy dòng nào (mục 2.3).
2. **Opcode không được ghi ra đĩa.** Nó nằm trong RAM của process và bị vứt đi khi xong việc. Lần chạy
   sau lại biên dịch từ đầu, trừ khi có OPcache giữ lại (mục 3).

Phần còn lại của chương đi lần lượt: mục 2 mổ xẻ từng chặng biên dịch và thực thi, mục 3 là OPcache,
mục 4 là SAPI, mục 5 là vòng đời của process và request, mục 6 là đường đi của một request web, mục 7
là mô hình share-nothing, mục 8 so sánh với Node.js, Java, Go.

## 2. Biên dịch và thực thi, từng chặng một

### 2.1 Lexer: cắt văn bản thành token

Khi đọc câu "Tôi ăn cơm.", mắt bạn tự tách ra ba từ và một dấu chấm trước khi hiểu nghĩa. *Lexer*
(còn gọi là *scanner* hay *tokenizer*) làm đúng việc đó với mã nguồn: nó đọc từng ký tự và gom lại
thành các *token*. Mỗi token là một "từ" có nghĩa với PHP: một từ khoá (`echo`, `function`), một tên
biến (`$total`), một con số (`2`), một chuỗi, một dấu (`=`, `;`), một comment...

Vì sao cần bước này? Vì quy tắc ngữ pháp được viết theo "từ", không theo ký tự. Bước sau (parser) chỉ
cần hỏi "token tiếp theo là gì" thay vì phải tự lo chuyện khoảng trắng, xuống dòng hay comment.

PHP cho bạn gọi thẳng lexer của nó từ code PHP, qua class `PhpToken` (có từ PHP 8.0, thuộc extension
`tokenizer` vốn bật sẵn):

```php
<?php
declare(strict_types=1);

$code = '<?php $total = $price * 2; // tính tổng';

foreach (PhpToken::tokenize($code) as $token) {
    printf("%-15s %s\n", $token->getTokenName(), var_export($token->text, true));
}
```

Output:

```
T_OPEN_TAG      '<?php '
T_VARIABLE      '$total'
T_WHITESPACE    ' '
=               '='
T_WHITESPACE    ' '
T_VARIABLE      '$price'
T_WHITESPACE    ' '
*               '*'
T_WHITESPACE    ' '
T_LNUMBER       '2'
;               ';'
T_WHITESPACE    ' '
T_COMMENT       '// tính tổng'
```

Đọc kết quả:

- Token có tên dạng `T_...`: `T_VARIABLE` là tên biến, `T_LNUMBER` là số nguyên viết trực tiếp
  (*literal*), `T_COMMENT` là comment, `T_WHITESPACE` là khoảng trắng.
- Token chỉ gồm một ký tự như `=`, `*`, `;` không có tên riêng; tên của nó chính là ký tự đó.
- Ngoài tên (`getTokenName()`) và nội dung (`$text`), mỗi `PhpToken` còn giữ số dòng (`$line`) và vị
  trí byte (`$pos`). Nhờ số dòng mà thông báo lỗi chỉ được "on line 7".
- Hàm cũ hơn `token_get_all()` cho cùng thông tin nhưng dưới dạng mảng lẫn chuỗi, khó dùng hơn.
  Các công cụ kiểm tra code style như PHP_CodeSniffer làm việc trên token.

Lexer chỉ cắt chữ, không hiểu nghĩa. Một đoạn code sai ngữ pháp vẫn được cắt thành token bình thường:

```php
<?php
declare(strict_types=1);

$tokens = PhpToken::tokenize('<?php $x = = ;');   // sai ngữ pháp: hai dấu = liền nhau
echo implode(' | ', array_map(fn (PhpToken $t): string => $t->getTokenName(), $tokens)), "\n";
// in ra: T_OPEN_TAG | T_VARIABLE | T_WHITESPACE | = | T_WHITESPACE | = | T_WHITESPACE | ;
```

Phát hiện "hai dấu `=` liền nhau là vô nghĩa" là việc của parser (mục 2.2).

*Văn bản ngoài thẻ PHP cũng là token.* PHP sinh ra như một ngôn ngữ chèn vào HTML, nên mọi thứ nằm
ngoài `<?php ... ?>` được lexer gói thành token `T_INLINE_HTML`. Với file `tpl.php`:

```php
<h1>Chào <?= $name ?></h1>
<?php $n = 1;
```

lexer cho ra (output thật, bỏ bớt các dòng cuối):

```
T_INLINE_HTML          '<h1>Chào '
T_OPEN_TAG_WITH_ECHO   '<?='
T_WHITESPACE           ' '
T_VARIABLE             '$name'
T_WHITESPACE           ' '
T_CLOSE_TAG            '?>'
T_INLINE_HTML          '</h1>
'
T_OPEN_TAG             '<?php '
...
```

Mục 2.4 sẽ cho thấy `T_INLINE_HTML` được biên dịch thành lệnh in ra nguyên văn. Đó là lý do một dấu
cách hay một dòng trống vô tình nằm trước `<?php` cũng bị gửi ra output (và gây lỗi "headers already
sent" ở [chương 15](15-php-va-web.md)).

Bên trong: lexer của PHP được mô tả trong file `Zend/zend_language_scanner.l` của php-src, rồi công cụ
*re2c* sinh ra mã C từ file đó lúc build PHP.

⚠️ Giá trị số của các hằng `T_*` (ví dụ `T_VARIABLE`) có thể đổi giữa các phiên bản PHP (php.net ghi
rõ điều này). Khi viết công cụ xử lý token, so sánh bằng tên hằng (`$t->is(T_VARIABLE)`), đừng so
với một con số cứng.

### 2.2 Parser và AST: ghép token thành cây

Có từ đúng chưa đủ, câu còn phải đúng ngữ pháp: "cơm ăn tôi" gồm toàn từ hợp lệ nhưng sai trật tự.
*Parser* (bộ phân tích cú pháp) nhận dòng token, đối chiếu với *grammar* (bộ quy tắc ngữ pháp) của
PHP, và dựng ra một cấu trúc dạng cây gọi là *AST* (Abstract Syntax Tree, cây cú pháp trừu tượng).

Lấy câu lệnh:

```php
$total = $price * 2 + 1;
```

AST của nó trông như sau (hình minh hoạ, tên nút lấy theo các loại nút `ZEND_AST_*` trong
`Zend/zend_ast.h`, đã bỏ tiền tố):

```
ASSIGN
├── VAR  "total"
└── BINARY_OP (+)
    ├── BINARY_OP (*)
    │   ├── VAR  "price"
    │   └── ZVAL 2
    └── ZVAL 1
```

- Mỗi nút là một cấu trúc ngữ pháp: phép gán (`ASSIGN`), phép toán hai ngôi (`BINARY_OP`), một biến
  (`VAR`), một giá trị hằng (`ZVAL`).
- Thứ tự ưu tiên toán tử nằm ở hình dạng cây: `*` nằm sâu hơn `+`, nên được tính trước. Viết
  `($price * 2) + 1` cho ra đúng cây này; dấu ngoặc đã làm xong nhiệm vụ và biến mất. Còn
  `$price * (2 + 1)` cho ra cây khác: nút `+` nằm dưới nút `*`.
- "Trừu tượng" nghĩa là cây chỉ giữ cái ảnh hưởng tới ý nghĩa. Khoảng trắng, comment, dấu ngoặc, dấu
  chấm phẩy đều không còn.

Nếu dòng token không khớp grammar, parser dừng và báo *syntax error* (lỗi cú pháp). Mục 2.3 xem kỹ
chuyện này.

Bên trong:

- Parser của PHP được sinh bởi công cụ *GNU Bison* từ file grammar `Zend/zend_language_parser.y`.
- Lexer và parser không chạy thành hai lượt riêng: parser cần token nào thì gọi lexer lấy token đó.
- AST chỉ là đồ dùng tạm: hàm `zend_compile()` trong php-src dựng AST, đưa cho compiler sinh opcode,
  rồi huỷ AST ngay.
- AST mới có từ PHP 7.0 (RFC *Abstract syntax tree* của Nikita Popov). Trước đó parser sinh opcode
  thẳng trong lúc đọc, một lượt duy nhất. RFC nêu rằng cách cũ khiến một số cú pháp gần như không làm
  được; ví dụ trước PHP 7, `yield` dùng trong biểu thức bắt buộc phải bọc ngoặc.

Bạn không xem được AST của engine bằng PHP thuần (cần extension `ast` cài thêm từ PECL). Các công cụ
phân tích tĩnh như PHPStan, Rector ([chương 21](21-chat-luong-code.md)) dùng thư viện
`nikic/php-parser`: một parser viết bằng PHP, tự dựng AST riêng theo cùng ý tưởng.

### 2.3 Lỗi cú pháp: cả file không chạy dòng nào

Vì cả file phải qua parser trước khi chạy, một lỗi cú pháp ở bất kỳ đâu làm cả file không chạy:

```php
<?php
declare(strict_types=1);

echo "Dòng 1\n";
echo "Dòng 2\n";
echo "Dòng 3\n"   // quên dấu chấm phẩy
echo "Dòng 4\n";
```

Output (đường dẫn file rút gọn):

```
Parse error: syntax error, unexpected token "echo", expecting "," or ";" in /app/syntax.php on line 7
```

(Image Docker ở trên không có php.ini nên `log_errors` giữ mặc định là tắt. Nếu php.ini của bạn bật
`log_errors` mà không đặt `error_log`, như hai file php.ini mẫu đi kèm PHP, CLI còn ghi bản log của
cùng lỗi ra stderr: một dòng bắt đầu bằng `PHP Parse error:`. File mẫu `php.ini-production` còn tắt
`display_errors`, khi đó bạn chỉ thấy dòng log này.)

Hai điều đáng chú ý:

1. Không có "Dòng 1", dù dòng 4 hoàn toàn đúng. Code chưa bao giờ được chạy.
2. ⚠️ Lỗi báo ở dòng 7, trong khi chỗ sai thật (thiếu `;`) ở dòng 6. Parser chỉ phát hiện sai khi
   gặp token không thể đứng ở đó (`echo` của dòng 7). Gặp lỗi cú pháp, luôn nhìn cả dòng báo lỗi lẫn
   dòng ngay phía trên.

So sánh với một lỗi chỉ lộ ra lúc chạy (gọi hàm không tồn tại):

```php
<?php
declare(strict_types=1);

echo "Dòng 1\n";
khongTonTai();
echo "Dòng 3\n";
```

Output (đường dẫn rút gọn):

```
Dòng 1

Fatal error: Uncaught Error: Call to undefined function khongTonTai() in /app/runtime.php:5
Stack trace:
#0 {main}
  thrown in /app/runtime.php on line 5
```

File này đúng ngữ pháp nên biên dịch xong, "Dòng 1" chạy và in ra. Chỉ khi VM chạy tới dòng 5 và tìm
hàm `khongTonTai` mới biết là không có. Biên dịch không kiểm tra hàm có tồn tại hay không, vì hàm có
thể được khai báo ở file khác và nạp vào sau.

Kiểm tra cú pháp mà không chạy: `php -l file.php` (*lint*). Theo php.net, thành công thì in
`No syntax errors detected in <file>`; thất bại thì in lỗi parser kèm `Errors parsing <file>` và trả
mã thoát báo lỗi, nên dùng được trong CI. Cũng theo php.net, `-l` không tìm được lỗi chỉ lộ ra
khi chạy, như gọi hàm không tồn tại ở ví dụ trên.

*Lỗi cú pháp trong file được include.* Mỗi file được biên dịch riêng (mục 2.7). Nếu file được nạp bằng
`require`/`include` có lỗi cú pháp, PHP ném ra exception `ParseError` (từ PHP 7) tại chỗ `require`, và
file gọi có thể bắt nó. File `hong.php`, lỗi cú pháp ở dòng 3:

```php
<?php
echo "Bạn sẽ không thấy dòng này\n";
$x = ;
```

File `main.php` cùng thư mục:

```php
<?php
declare(strict_types=1);

echo "Bắt đầu main.php\n";
try {
    require __DIR__ . '/hong.php';
} catch (ParseError $e) {
    echo 'Bắt được ParseError: ', $e->getMessage(), ' (dòng ', $e->getLine(), ")\n";
}
echo "main.php vẫn chạy tiếp\n";
```

Chạy `php main.php`, output:

```
Bắt đầu main.php
Bắt được ParseError: syntax error, unexpected token ";" (dòng 3)
main.php vẫn chạy tiếp
```

`main.php` đã biên dịch thành công và đang chạy; chỉ `hong.php` hỏng, và dòng `echo` của `hong.php`
không chạy vì chính file đó không biên dịch được. Exception là chủ đề của
[chương 12](12-loi-exception.md); ở đây chỉ cần thấy ranh giới biên dịch là từng file.

### 2.4 Compiler: từ AST sinh opcode

*Compiler* duyệt AST và sinh ra *opcode*: các lệnh nhỏ, đơn giản mà máy ảo hiểu được. Mỗi opcode
làm một việc rất cụ thể: gán, cộng, in ra, gọi hàm, nhảy tới lệnh khác...

Với file `price.php`:

```php
<?php
$price = 5;
$total = $price * 2 + 1;
echo $total;
```

opcode sinh ra là (output thật, cách tự xem ở mục 2.5):

```
0000 ASSIGN CV0($price) int(5)
0001 T3 = MUL CV0($price) int(2)
0002 T4 = ADD T3 int(1)
0003 ASSIGN CV1($total) T4
0004 ECHO CV1($total)
0005 RETURN int(1)
```

Đặt cạnh cây AST ở mục 2.2, bạn thấy compiler đi từ lá lên gốc: nút `*` nằm sâu nhất nên được sinh
lệnh trước (`MUL`), rồi tới `+` (`ADD`), cuối cùng là phép gán (`ASSIGN`). Cách đọc một dòng opcode:

```
 0001   T3 =   MUL   CV0($price)   int(2)
  │      │      │        │            │
  │      │      │        │            └─ toán hạng 2: hằng số 2 (CONST)
  │      │      │        └─ toán hạng 1: biến $price (CV)
  │      │      └─ tên lệnh
  │      └─ nơi ghi kết quả: ô tạm số 3
  └─ số thứ tự lệnh
```

Các loại toán hạng bạn sẽ gặp:

| Ký hiệu | Tên trong php-src | Ý nghĩa |
|---|---|---|
| `int(5)`, `string("...")` | CONST | Giá trị hằng, biết ngay lúc biên dịch |
| `CV0($price)` | CV (compiled variable) | Biến có tên trong code. Compiler đánh số sẵn mọi biến của hàm, nên lúc chạy truy cập theo số thứ tự chứ không phải tra theo tên |
| `T3` | TMP_VAR | Ô tạm do compiler tạo cho kết quả trung gian, như `$price * 2` |
| `V2` | VAR | Cũng là ô tạm, dùng cho kết quả có thể là reference, như giá trị trả về của lời gọi hàm |

Tất cả opcode của một "đơn vị code" được gom vào một *op_array*: một op_array cho phần code nằm ngoài
mọi hàm của file (trong output gọi là `$_main`), và một op_array riêng cho mỗi hàm, mỗi method.
Ngoài danh sách lệnh, op_array còn giữ bảng hằng, tên các biến CV, số dòng tương ứng của từng lệnh
(để báo lỗi đúng dòng)...

Vài điều compiler làm sẵn mà bạn nên biết:

- *Tự tính biểu thức hằng* (*constant folding*). `$a = 1 + 2;` được biên dịch thẳng thành
  `ASSIGN CV0($a) int(3)`: phép cộng hai hằng số được compiler tính luôn, lúc chạy không còn phép
  cộng nào.
- *HTML ngoài thẻ PHP thành lệnh in.* File

  ```php
  <?php $name = 'An'; ?>
  <h1>Chào <?= $name ?></h1>
  ```

  biên dịch thành (output thật):

  ```
  0000 ASSIGN CV0($name) string("An")
  0001 ECHO string("<h1>Ch\xC3\xA0o ")
  0002 ECHO CV0($name)
  0003 ECHO string("</h1>\n")
  0004 RETURN int(1)
  ```

  Phần HTML trở thành `ECHO` một chuỗi hằng (chữ `à` hiện thành `\xC3\xA0` là hai byte UTF-8 của nó,
  [chương 05](05-chuoi.md)). Để ý: ký tự xuống dòng ngay sau `?>` ở dòng 1 không có trong output; PHP
  nuốt đúng một dấu xuống dòng nằm ngay sau thẻ đóng.
- *`RETURN int(1)` ở cuối `$_main`.* Compiler luôn thêm lệnh này. Đó là lý do `include 'file.php'`
  trả về `1` khi file đó không tự `return` gì (php.net ghi rõ hành vi này ở trang `include`).
- *Hàm khai báo ở cấp cao nhất được đăng ký ngay lúc biên dịch.* Vì vậy gọi hàm trước dòng khai báo
  vẫn chạy:

  ```php
  <?php
  declare(strict_types=1);

  echo binhPhuong(4), "\n"; // in ra: 16, dù hàm khai báo ở bên dưới

  function binhPhuong(int $x): int
  {
      return $x * $x;
  }
  ```

  Nhưng hàm khai báo có điều kiện (trong `if`, hoặc trong thân hàm khác) chỉ tồn tại khi VM chạy
  tới chỗ khai báo. php.net mô tả đúng như vậy: hàm không cần định nghĩa trước khi dùng, trừ khi được
  định nghĩa có điều kiện.

  ```php
  <?php
  declare(strict_types=1);

  var_dump(function_exists('sau'));         // in ra: bool(true), dù khai báo ở cuối file
  var_dump(function_exists('coDieuKien'));  // in ra: bool(false), chưa chạy tới if

  if (true) {
      function coDieuKien(): string { return 'có'; }
  }
  var_dump(function_exists('coDieuKien'));  // in ra: bool(true)

  function sau(): void {}
  ```

  Nhìn opcode sẽ thấy vì sao: hàm `sau` không sinh ra lệnh nào trong `$_main` (nó đã được đăng ký lúc
  biên dịch), còn `coDieuKien` sinh ra một lệnh `DECLARE_FUNCTION string("codieukien")` nằm sau lệnh
  nhảy của `if`, chỉ có tác dụng khi VM chạy qua nó. Tên hàm bị đổi về chữ thường vì tên hàm trong PHP
  không phân biệt hoa thường (với chữ A tới Z). Class có quy tắc riêng phức tạp hơn, xem
  [chương 09](09-oop-co-ban.md).

Sau khi sinh xong opcode, một lượt hoàn thiện (hàm `pass_two()` trong php-src) gắn mỗi lệnh với
*handler* của nó: hàm C sẽ thực thi lệnh đó (mục 2.6).

### 2.5 Tự xem opcode của bạn

Cách dễ nhất không cần cài thêm gì là nhờ OPcache in opcode ra (OPcache là gì: mục 3). Tạo file
`add.php`:

```php
<?php
declare(strict_types=1);

function add(int $x, int $y): int
{
    return $x + $y;
}

$a = 2;
echo add($a, 3), "\n";
```

Rồi chạy, ở thư mục chứa file:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php \
  -d opcache.enable_cli=1 \
  -d opcache.file_update_protection=0 \
  -d opcache.opt_debug_level=0x10000 \
  add.php
```

- `opcache.enable_cli=1`: CLI mặc định không bật OPcache (mục 3.4), phải bật thì mới có gì để in.
- `opcache.opt_debug_level=0x10000`: in opcode trước khi optimizer của OPcache xử lý; `0x20000` là
  sau khi tối ưu. Opcode được in ra *stderr*, nên chuyển hướng output nhớ dùng `2>`.
- `opcache.file_update_protection=0`: mặc định OPcache không cache file vừa sửa chưa quá 2 giây (để
  tránh cache file đang ghi dở). Không có dòng này, chạy ngay sau khi lưu file sẽ không thấy gì in ra.
- Từ PHP 8.5, OPcache luôn được build sẵn trong PHP. Với bản cũ hơn, nếu `php -m` không liệt kê
  `Zend OPcache` thì thêm `-d zend_extension=opcache`.

Output (đường dẫn file rút gọn; con số `128` ở dòng `INIT_FCALL` là trên máy 64-bit):

```
$_main:
     ; (lines=8, args=0, vars=1, tmps=2)
     ; (before optimizer)
     ; /app/add.php:1-11
     ; return  [] RANGE[0..0]
0000 ASSIGN CV0($a) int(2)
0001 INIT_FCALL 2 128 string("add")
0002 SEND_VAR CV0($a) 1
0003 SEND_VAL int(3) 2
0004 V2 = DO_UCALL
0005 ECHO V2
0006 ECHO string("\n")
0007 RETURN int(1)

add:
     ; (lines=7, args=2, vars=2, tmps=1)
     ; (before optimizer)
     ; /app/add.php:4-7
     ; return  [] RANGE[0..0]
0000 CV0($x) = RECV 1
0001 CV1($y) = RECV 2
0002 T2 = ADD CV0($x) CV1($y)
0003 VERIFY_RETURN_TYPE T2
0004 RETURN T2
0005 VERIFY_RETURN_TYPE
0006 RETURN null
LIVE RANGES:
     2: 0003 - 0004 (tmp/var)
5
```

Opcode được in lúc biên dịch, trước khi script chạy, nên số `5` của `echo` hiện ra sau cùng.
Có hai op_array: `$_main` và `add`. Dòng `; (lines=8, args=0, vars=1, tmps=2)` cho biết op_array có 8
lệnh, 0 tham số, 1 biến CV, 2 ô tạm. Hai lệnh cuối của `add` (`VERIFY_RETURN_TYPE` rồi `RETURN null`)
là lệnh `return` ngầm mà compiler luôn thêm vào cuối hàm phòng khi code chạy hết thân hàm mà không gặp
`return`; ở đây không bao giờ chạy tới. Chạy lại với `0x20000` sẽ thấy optimizer xoá hai lệnh thừa đó.

Ngoài cách này còn có trình gỡ lỗi `phpdbg` đi kèm PHP (tuỳ chọn `-p` in opcode rồi thoát) và
extension VLD. [Chương 19](19-ben-trong-engine.md) dùng chúng kỹ hơn.

### 2.6 Zend VM: chạy opcode

*Zend VM* là phần của Zend Engine thực thi opcode. Về ý tưởng, nó là một vòng lặp rất đơn giản
(giả mã, không phải code thật):

```
opline = lệnh đầu tiên của op_array
lặp mãi:
    handler = handler gắn với opline       // ví dụ handler của ADD
    gọi handler                            // handler làm việc của nó, rồi chỉnh opline:
                                           //   thường là lệnh kế tiếp, lệnh nhảy thì tới đích
    nếu vừa RETURN khỏi code cấp cao nhất: dừng
```

Trong php-src, vòng lặp đó là hàm `execute_ex()`, với thân chính là `while (1) { ... }`. Mỗi opcode
có handler viết bằng C. Handler được viết một lần trong `Zend/zend_vm_def.h`, rồi script
`Zend/zend_vm_gen.php` sinh ra nhiều phiên bản *chuyên biệt hoá* theo loại toán hạng vào file
`Zend/zend_vm_execute.h`. Ví dụ `ECHO` có `ZEND_ECHO_SPEC_CONST_HANDLER`,
`ZEND_ECHO_SPEC_TMPVAR_HANDLER`, `ZEND_ECHO_SPEC_CV_HANDLER`: bản dành cho hằng không phải kiểm tra
"toán hạng có phải biến không", nên chạy nhanh hơn. PHP 8.5 có hơn 200 loại opcode (danh sách ở
`Zend/zend_vm_opcodes.h`).

Theo dõi VM chạy `add.php` từng bước:

| Bước | Lệnh đang chạy | VM làm gì |
|---|---|---|
| 1 | `ASSIGN CV0($a) int(2)` | Ghi 2 vào ô của `$a` |
| 2 | `INIT_FCALL 2 128 string("add")` | Tìm hàm `add`, cấp một *call frame* mới trên stack của VM. `2` là số đối số, `128` là số byte frame cần (trên máy 64-bit) |
| 3 | `SEND_VAR CV0($a) 1` | Đặt giá trị của `$a` vào chỗ đối số thứ 1 của frame mới |
| 4 | `SEND_VAL int(3) 2` | Đặt 3 vào chỗ đối số thứ 2 |
| 5 | `V2 = DO_UCALL` | Chuyển sang chạy op_array của `add` (U = user function, hàm viết bằng PHP); kết quả sẽ về ô `V2` |
| 6 | `CV0($x) = RECV 1` (trong `add`) | Nhận đối số 1 vào `$x` và kiểm tra kiểu `int` ([chương 08](08-ham.md)) |
| 7 | `CV1($y) = RECV 2` | Tương tự cho `$y` |
| 8 | `T2 = ADD CV0($x) CV1($y)` | Cộng, ghi 5 vào ô tạm `T2` |
| 9 | `VERIFY_RETURN_TYPE T2` | Kiểm tra giá trị trả về đúng kiểu `int` đã khai báo |
| 10 | `RETURN T2` | Đưa 5 về ô `V2` của `$_main`, bỏ frame của `add`, quay lại lệnh 0005 |
| 11 | `ECHO V2` | In `5` |
| 12 | `ECHO string("\n")` | In xuống dòng |
| 13 | `RETURN int(1)` | Kết thúc script |

Một *call frame* (trong php-src là struct `zend_execute_data`) là vùng nhớ riêng của một lần gọi hàm:
chứa đối số, các biến CV, các ô tạm, và con trỏ quay về frame của bên gọi. Gọi hàm PHP từ PHP
(`DO_UCALL`) không làm C gọi đệ quy một `execute_ex()` mới: handler chỉ chuyển "frame hiện tại" sang
frame mới và vòng lặp chạy tiếp. Với hàm viết sẵn bằng C như `var_dump`, compiler sinh lệnh
`DO_ICALL` (I = internal function), handler gọi thẳng hàm C đó. Một số hàm rất hay dùng còn được
compiler thay hẳn bằng opcode riêng, không có lời gọi hàm nào: trên PHP 8.5, `strlen($s)` biên dịch
thành lệnh `STRLEN`, `count($a)` thành lệnh `COUNT`.

Từ đây bạn hiểu vì sao trong PHP, kiểu của tham số và giá trị trả về được kiểm tra lúc chạy (lệnh
`RECV`, `VERIFY_RETURN_TYPE`), khác với Go hay Java kiểm tra lúc biên dịch: compiler của PHP biên dịch
từng file riêng lẻ, không biết trước file khác sẽ truyền vào giá trị gì.

Mỗi opcode tốn một vòng "lấy lệnh, gọi handler". Với code tính toán nặng, phần tốn kém này đáng kể;
*JIT* (từ PHP 8.0) giải quyết bằng cách dịch opcode của đoạn code chạy nhiều sang mã máy để CPU chạy
trực tiếp. Trang phát hành PHP 8.0 trên php.net ghi: tracing JIT nhanh hơn khoảng 3 lần trên
benchmark tổng hợp, nhưng hiệu năng của ứng dụng điển hình thì ngang PHP 7.4. RFC JIT cũng nói rõ
lợi ích lớn nằm ở các tác vụ nặng CPU ngoài web, còn web app điển hình thì không đáng kể.
[Chương 19](19-ben-trong-engine.md) và [chương 20](20-hieu-nang.md) nói kỹ.

### 2.7 Biên dịch theo từng file, vào lúc file được nạp

PHP không biên dịch "cả dự án" một lần. Đơn vị biên dịch là một file, và file chỉ được biên dịch
khi được nạp: file bạn chạy trực tiếp, hoặc file được `include`/`require`, hoặc file được autoloader
nạp khi cần một class ([chương 11](11-namespace-composer.md)). File `lazy.php`, đặt cùng thư mục với
`hong.php` của mục 2.3:

```php
<?php
declare(strict_types=1);

$canBaoCao = false;
if ($canBaoCao) {
    require __DIR__ . '/hong.php';   // file lỗi cú pháp ở mục 2.3, nhưng dòng này không bao giờ chạy
}

require __DIR__ . '/helper.php';     // helper.php chỉ được biên dịch khi VM chạy tới đây
echo chao('An'), "\n";

foreach (get_included_files() as $file) {
    echo basename($file), "\n";
}
```

với `helper.php`:

```php
<?php
declare(strict_types=1);

function chao(string $ten): string
{
    return "Chào {$ten}";
}
```

Output:

```
Chào An
lazy.php
helper.php
```

`hong.php` chưa bao giờ được nạp nên chưa bao giờ được biên dịch, và lỗi cú pháp của nó không ảnh
hưởng gì. `require` là một lệnh chạy lúc runtime như mọi lệnh khác (opcode của nó là
`INCLUDE_OR_EVAL`): khi VM chạy tới, nó gọi compiler cho file mới, rồi chạy op_array vừa sinh ra.

Hệ quả quan trọng cho phần sau: một request vào ứng dụng Laravel nạp hàng trăm file (framework,
thư viện trong `vendor/`, code của bạn). Nếu mỗi request đều đọc đĩa, lexer, parse, compile lại toàn
bộ số file đó, rất nhiều CPU bị đốt cho cùng một việc lặp đi lặp lại trên code không hề đổi. Đó là
bài toán OPcache giải quyết.

## 3. OPcache: biên dịch một lần, dùng lại nhiều lần

Mục này chỉ nói OPcache ở mức khái niệm. Cấu hình và vận hành OPcache trên production nằm ở
[chương 18](18-fpm-nginx-opcache.md).

### 3.1 OPcache là gì

Theo php.net: *OPcache* cải thiện hiệu năng PHP bằng cách lưu bytecode (opcode) đã biên dịch sẵn
vào *shared memory*, nhờ đó PHP không phải nạp và parse lại script ở mỗi request. OPcache là một
extension đi kèm PHP từ bản 5.5.

*Shared memory* (bộ nhớ dùng chung) là một vùng RAM mà nhiều process cùng nhìn thấy. Thông thường mỗi
process có vùng nhớ riêng, process này không đọc được biến của process kia; shared memory là ngoại lệ
được hệ điều hành hỗ trợ.

```
Không có OPcache, request nào cũng làm lại từ đầu:

  request 1:  đọc file ─> lexer ─> parser ─> compiler ─> Zend VM chạy
  request 2:  đọc file ─> lexer ─> parser ─> compiler ─> Zend VM chạy
  request 3:  đọc file ─> lexer ─> parser ─> compiler ─> Zend VM chạy

Có OPcache:

  request 1:  tra cache: chưa có ─> lexer ─> parser ─> compiler ─> optimizer
                                    ─> LƯU op_array vào shared memory ─> Zend VM chạy
  request 2:  tra cache: có rồi ───────────────────────────────────────> Zend VM chạy
  request 3:  tra cache: có rồi ───────────────────────────────────────> Zend VM chạy
```

Cách OPcache "chen" vào: trong Zend Engine, việc biên dịch một file đi qua một con trỏ hàm tên
`zend_compile_file`. Khi khởi động, OPcache thay con trỏ đó bằng hàm của chính nó (trong php-src là
`persistent_compile_file` ở `ext/opcache/ZendAccelerator.c`). Từ đó mọi lần nạp file đều hỏi OPcache
trước; chỉ khi cache chưa có, OPcache mới gọi compiler gốc rồi lưu kết quả lại. Code của bạn không
phải sửa gì.

Với PHP-FPM (mục 6), các worker process là con của cùng một master process và dùng chung một vùng
shared memory của OPcache. File được worker A biên dịch xong thì worker B dùng lại được ngay.

### 3.2 Thấy cache hoạt động bằng mắt

Hàm `opcache_get_status()` trả về thống kê của cache, trong đó `misses` là số lần phải biên dịch (cache
chưa có) và `hits` là số lần dùng lại được. Tạo hai file:

```php
<?php
// config.php
return ['app' => 'demo', 'debug' => false];
```

```php
<?php
// opcache_demo.php
declare(strict_types=1);

$status = opcache_get_status(false);
if ($status === false) {
    exit("OPcache đang tắt cho process này\n");
}

for ($i = 1; $i <= 3; $i++) {
    $config = include __DIR__ . '/config.php';
    $stats = opcache_get_status(false)['opcache_statistics'];
    echo "Lần {$i}: misses = {$stats['misses']}, hits = {$stats['hits']}\n";
}
```

Chạy `php opcache_demo.php` thường sẽ in `OPcache đang tắt cho process này` (lý do ở mục 3.4). Bật
OPcache cho CLI:

```bash
php -d opcache.enable_cli=1 -d opcache.file_update_protection=0 opcache_demo.php
```

Output:

```
Lần 1: misses = 2, hits = 0
Lần 2: misses = 2, hits = 1
Lần 3: misses = 2, hits = 2
```

Hai lần miss ban đầu là `opcache_demo.php` và `config.php` lần đầu được biên dịch. Lần include thứ 2
và thứ 3, `config.php` lấy thẳng từ cache. Trên server web, cùng cơ chế đó áp dụng cho mọi file của
ứng dụng, qua hàng triệu request.

⚠️ Bỏ `-d opcache.file_update_protection=0` và chạy ngay sau khi vừa lưu file, bạn sẽ thấy `misses`
tăng đều 2, 3, 4 và `hits` đứng ở 0: OPcache mặc định không cache file mới sửa chưa quá 2 giây (để
tránh cache một file đang ghi dở), nên lần nào cũng biên dịch lại.

### 3.3 Sửa code rồi thì OPcache biết bằng cách nào

OPcache dùng đường dẫn file làm khoá. Nếu bạn sửa file, cache phải biết để biên dịch lại. Hai ini
quyết định chuyện này (giá trị mặc định theo php.net):

| Directive | Mặc định | Ý nghĩa |
|---|---|---|
| `opcache.validate_timestamps` | 1 (bật) | Có kiểm tra file đã bị sửa hay không |
| `opcache.revalidate_freq` | 2 (giây) | Kiểm tra mỗi file tối đa một lần trong N giây; 0 là kiểm tra ở mọi request |

Với mặc định, sau khi sửa file có thể mất tới khoảng 2 giây cache mới nhận ra. Trên production, người ta
thường tắt hẳn `validate_timestamps` để bỏ luôn việc kiểm tra file, vì code chỉ đổi khi deploy. Khi đó,
theo php.net, thay đổi trên đĩa chỉ có hiệu lực sau khi gọi `opcache_reset()`, `opcache_invalidate()`
hoặc khởi động lại server; trong thực tế là reload PHP-FPM sau mỗi lần deploy.

⚠️ Lỗi kinh điển: "đã deploy code mới mà web vẫn chạy code cũ". Thủ phạm thường là OPcache với
`validate_timestamps=0` mà quy trình deploy quên reload FPM. Cách deploy đúng ở
[chương 18](18-fpm-nginx-opcache.md).

### 3.4 OPcache và CLI

`opcache.enable` mặc định là 1, nhưng `opcache.enable_cli` mặc định là 0: chạy bằng lệnh `php`
thì OPcache tắt. php.net không ghi lý do của giá trị mặc định này, nhưng nhìn vòng đời process (mục 5)
sẽ thấy vì sao bật cho CLI thường ít lợi: mỗi lần chạy `php script.php` là một process mới; shared
memory của OPcache sinh ra cùng process đó và mất khi process thoát. Lần chạy sau không có gì để dùng
lại, mà lần này còn tốn thêm công tối ưu và lưu vào cache.

⚠️ Vì CLI và FPM là các process khác nhau với cache khác nhau:

- `php -r 'opcache_reset();'` gõ trong terminal không xoá cache của FPM.
- `php -r 'var_dump(opcache_get_status());'` cho bạn trạng thái OPcache của chính lệnh CLI đó (thường là
  `false`), không phải của server web.

(OPcache còn có thể lưu opcode ra đĩa bằng `opcache.file_cache`, làm cache cấp hai; chi tiết ở
chương 18.)

### 3.5 Không chỉ cache: optimizer, preloading, JIT

Trước khi lưu op_array vào cache, OPcache cho nó chạy qua *optimizer*: một chuỗi bước tối ưu opcode.
Với hàm:

```php
function secondsPerDay(): int
{
    $hours = 24;
    return $hours * 60 * 60;
}
```

opcode của hàm trước khi tối ưu (`opt_debug_level=0x10000`, output thật):

```
0000 ASSIGN CV0($hours) int(24)
0001 T2 = MUL CV0($hours) int(60)
0002 T3 = MUL T2 int(60)
0003 VERIFY_RETURN_TYPE T3
0004 RETURN T3
0005 VERIFY_RETURN_TYPE
0006 RETURN null
```

và sau khi tối ưu (`0x20000`, output thật):

```
0000 T0 = QM_ASSIGN int(86400)
0001 RETURN T0
```

Optimizer nhận ra `$hours` luôn là 24, tính sẵn `24 * 60 * 60 = 86400`, bỏ biến, bỏ phép kiểm tra kiểu
thừa (86400 chắc chắn là `int`) và bỏ lệnh return ngầm không bao giờ chạy tới. Việc tối ưu chỉ tốn một
lần lúc biên dịch, còn lợi ích có ở mọi lần chạy sau đó.

Hai tính năng lớn khác cũng nằm trong OPcache, bạn sẽ gặp lại sau:

- *Preloading* (PHP 7.4+): nạp sẵn một nhóm file vào bộ nhớ ngay khi server khởi động.
  [Chương 18](18-fpm-nginx-opcache.md).
- *JIT* (PHP 8.0+): dịch opcode sang mã máy (mục 2.6). [Chương 19](19-ben-trong-engine.md),
  [chương 20](20-hieu-nang.md).

Từ PHP 8.5, theo UPGRADING của php-src, OPcache luôn được build vào binary PHP và luôn được nạp; hai
ini `opcache.enable` và `opcache.enable_cli` vẫn có hiệu lực như cũ. Trước 8.5, OPcache là một
extension riêng (`opcache.so`) có thể thiếu hoặc quên bật.

## 4. SAPI: cầu nối giữa PHP và thế giới bên ngoài

### 4.1 SAPI là gì, vì sao cần

Zend Engine biết biên dịch và chạy code, nhưng không biết mình đang chạy ở đâu. Cùng một lệnh
`echo "Hello";`:

- chạy trong terminal thì chữ phải ra màn hình;
- chạy sau Nginx thì chữ phải thành phần thân của một HTTP response, gửi kèm header HTTP;
- chạy trong một chương trình khác nhúng PHP vào thì chữ phải được trả cho chương trình đó.

Tương tự, `$_GET`, `$_POST`, cookie, biến môi trường đến từ đâu, log lỗi ghi vào đâu, đều tuỳ môi
trường. *SAPI* (Server Application Programming Interface) là lớp chuyển đổi trả lời những câu hỏi đó.
README của SAPI embed trong php-src gọi SAPI là "điểm vào" (entry point) của Zend Engine.

Trong php-src, mỗi SAPI điền một struct `sapi_module_struct` gồm tên SAPI và các hàm callback. Vài
callback tiêu biểu (trong `main/SAPI.h`):

| Callback | Engine gọi khi cần... |
|---|---|
| `ub_write` | Ghi output ra ngoài. CLI ghi ra stdout; FPM đóng gói thành bản tin FastCGI gửi về Nginx |
| `send_headers` | Gửi header HTTP. CLI không có header để gửi |
| `read_post` | Đọc body của request (dữ liệu POST) |
| `read_cookies` | Lấy chuỗi cookie của request |
| `getenv` | Đọc biến môi trường |
| `log_message` | Ghi một dòng log lỗi |

Nhờ lớp này, một engine duy nhất chạy được trong nhiều môi trường khác nhau, và code PHP của bạn gần
như không phải biết mình đang chạy dưới SAPI nào.

### 4.2 Các SAPI thường gặp

Tên SAPI lấy được bằng hằng `PHP_SAPI` hoặc hàm `php_sapi_name()` (php.net: hai cách cho cùng giá
trị).

| `PHP_SAPI` | Chạy thế nào | Dùng khi nào |
|---|---|---|
| `cli` | Lệnh `php` trong terminal | Script, cron job, `composer`, `php artisan`, queue worker |
| `cli-server` | Lệnh `php -S localhost:8000` ([chương 01](01-php-la-gi.md)) | Chỉ để phát triển trên máy mình, không dùng cho production |
| `fpm-fcgi` | Chương trình PHP-FPM, nhận request từ web server qua giao thức FastCGI | Chạy ứng dụng web trên production; php.net xếp FPM (cùng PHP chạy như module của Apache) vào cách phổ biến nhất (mục 6) |
| `apache2handler` | Module `mod_php` nạp PHP vào chính process của Apache httpd | Cách cũ, vẫn gặp ở hosting truyền thống |
| `cgi-fcgi` | Chương trình `php-cgi` | Hiếm gặp |
| `embed` | Thư viện `libphp` để nhúng PHP vào chương trình C khác | Xây công cụ hoặc server riêng |
| `phpdbg` | Trình gỡ lỗi `phpdbg` | Debug, xem opcode |
| `litespeed` | Web server LiteSpeed | Hosting dùng LiteSpeed |

Ngoài các SAPI có sẵn trong php-src, dự án khác có thể tự viết SAPI. Ví dụ *FrankenPHP*, một app server
viết bằng Go (xây trên web server Caddy), có SAPI riêng tên `frankenphp`; tài liệu của FrankenPHP
hướng dẫn build PHP với `--enable-embed` để có `libphp` cho nó nhúng vào.

### 4.3 Cùng một file, khác SAPI

```php
<?php
declare(strict_types=1);

echo 'SAPI: ', PHP_SAPI, "\n";                         // giống hệt php_sapi_name()
echo 'PHP ', PHP_VERSION, ', Zend Engine ', zend_version(), "\n";
echo 'max_execution_time = ', ini_get('max_execution_time'), "\n";
echo 'Có hằng STDIN không? ', defined('STDIN') ? 'có' : 'không', "\n";
```

Chạy bằng `php sapi.php` (PHP 8.5.10; số phiên bản tuỳ máy bạn):

```
SAPI: cli
PHP 8.5.10, Zend Engine 4.5.10
max_execution_time = 0
Có hằng STDIN không? có
```

Đặt đúng file đó sau PHP-FPM và mở bằng trình duyệt, bạn sẽ thấy `SAPI: fpm-fcgi`, không có hằng
`STDIN`, và `max_execution_time` là giá trị trong php.ini của FPM (php.ini mẫu đi kèm PHP đặt 30 giây).
Những khác biệt chính của CLI so với SAPI web, theo trang "Differences from other SAPIs" của php.net:

- Không gửi header HTTP nào ra output.
- Lỗi in dạng văn bản thường (`html_errors` bị ép về tắt).
- `max_execution_time` bị ép về 0, tức không giới hạn thời gian chạy (script CLI hay chạy lâu).
  Các giá trị bị ép này không đổi được bằng php.ini, chỉ đổi được lúc chạy.
- Có sẵn hằng `STDIN`, `STDOUT`, `STDERR` và biến `$argc`, `$argv` chứa tham số dòng lệnh.
- Không tự đổi thư mục làm việc sang thư mục chứa script.

⚠️ Mỗi SAPI có thể đọc một file php.ini khác nhau. Trên Debian/Ubuntu cài PHP từ gói của hệ điều hành,
CLI đọc `/etc/php/<phiên bản>/cli/php.ini` còn FPM đọc `/etc/php/<phiên bản>/fpm/php.ini`. Hệ quả:

- `php --ini`, `php -m`, `php -i` gõ trong terminal cho biết cấu hình của CLI, không phải của
  server web. Muốn biết FPM đang dùng gì, xem `phpinfo()` chạy qua web (nhớ xoá trang đó sau khi xem).
- Sửa `memory_limit` trong ini của CLI rồi thắc mắc vì sao web không đổi: bạn đã sửa nhầm file.
- php.net cho biết php.ini chỉ được đọc khi PHP khởi động. CLI khởi động lại mỗi lần chạy lệnh nên
  đọc lại mỗi lần; với PHP-FPM, sửa php.ini xong phải reload FPM thì mới có hiệu lực.

### 4.4 Embed: nhúng PHP vào chương trình khác

SAPI `embed` biến PHP thành một thư viện (`libphp`) mà chương trình C (hoặc ngôn ngữ nào gọi được C) có
thể khởi động engine, chạy code PHP, rồi tắt engine. README của SAPI này trong php-src có ví dụ
chương trình C ngắn: macro `PHP_EMBED_START_BLOCK` khởi động engine và mở một request,
`PHP_EMBED_END_BLOCK` đóng request và tắt engine. Theo README, embed không được bật mặc định; phải build
PHP với `./configure --enable-embed`.

Bạn hiếm khi tự viết code C như vậy. Điều cần nhớ là: "PHP" không nhất thiết là chương trình `php`
hay PHP-FPM; nó có thể là một thư viện nằm bên trong một server khác, như FrankenPHP. Mục 8.3 sẽ cho
thấy điều này mở ra cách chạy PHP hoàn toàn khác.

## 5. Vòng đời: khởi động process, phục vụ request, dọn dẹp

### 5.1 Hai tầng vòng đời: process và request

PHP phân biệt rõ hai thứ:

- *Process*: chương trình đang chạy trong hệ điều hành (chương trình `php`, một worker của PHP-FPM...).
- *Request*: một lần chạy script để phục vụ một yêu cầu. Với CLI, request là "chạy file này một
  lần"; với web, request là một HTTP request.

Một process có thể phục vụ một hoặc rất nhiều request nối tiếp nhau. Các hàm tương ứng nằm trong
`main/main.c` của php-src; PHP Internals Book đặt tên các giai đoạn theo tên *hook* mà mỗi extension
có thể đăng ký (hook là hàm được engine gọi vào đúng thời điểm đó):

```
process khởi động
 └─ php_module_startup()    MINIT     1 lần mỗi process: đọc php.ini, khởi động từng extension
     │                                (đăng ký hàm, class, ini; OPcache cấp phát shared memory...)
     │
     ├─ php_request_startup()     RINIT      đầu mỗi request: chuẩn bị output, dựng $_GET, $_POST...
     │    php_execute_script()               biên dịch (hoặc lấy từ OPcache) và chạy script (mục 2, 3)
     ├─ php_request_shutdown()    RSHUTDOWN  cuối mỗi request: dọn SẠCH mọi thứ thuộc về request
     │
     ├─ ... request tiếp theo (nếu SAPI còn phục vụ tiếp) ...
     │
 └─ php_module_shutdown()   MSHUTDOWN 1 lần, khi process sắp thoát
```

### 5.2 CLI: một process, một request

`php script.php` tạo một process mới, chạy MINIT, phục vụ đúng một request là chạy file đó, rồi
MSHUTDOWN và thoát. Lần chạy sau là process mới tinh, khởi động lại từ đầu (kể cả đọc lại php.ini).

⚠️ Một script CLI chạy lâu, ví dụ queue worker `php artisan queue:work` của Laravel, vẫn chỉ là **một
request rất dài**: process không bao giờ tới RSHUTDOWN chừng nào vòng lặp xử lý job còn chạy. Biến
static, singleton, kết nối DB sống qua mọi job mà worker xử lý. Điều này khác hẳn web và là nguồn của
nhiều bug; [chương 29](29-laravel-queue-event-schedule-cache.md) nói kỹ.

### 5.3 PHP-FPM: một process, nhiều request

PHP-FPM gồm một *master process* và nhiều *worker process*:

1. Master khởi động, chạy MINIT (đọc php.ini, khởi động extension, OPcache tạo shared memory).
2. Master dùng `fork()` để nhân bản chính nó thành các worker. Worker thừa hưởng mọi thứ đã khởi động,
   nên không phải MINIT lại.
3. Mỗi worker chạy một vòng lặp: chờ request, RINIT, chạy script, RSHUTDOWN, rồi chờ request tiếp.
4. Master không chạy code PHP của bạn; nó chỉ quản lý worker: tạo thêm, giết bớt, thay worker chết.

Vòng lặp của worker trong `sapi/fpm/fpm/fpm_main.c`, rút gọn (bỏ phần xử lý lỗi và chi tiết):

```c
/* Worker đến được đây sau khi master fork ra */
while (fcgi_accept_request(request) >= 0) {   /* chờ web server gửi một request tới */
    php_request_startup();                    /* RINIT */
    php_execute_script(&file_handle);         /* chạy file PHP được yêu cầu */
    php_request_shutdown((void *) 0);         /* RSHUTDOWN: dọn sạch request */

    requests++;
    if (max_requests && requests == max_requests) {
        break;                                /* pm.max_requests: worker tự thoát, master thay worker mới */
    }
}
```

Nhìn vòng lặp này là hiểu mô hình share-nothing ở mục 7: cùng một worker phục vụ hàng nghìn request,
nhưng giữa hai request luôn có một lần `php_request_shutdown()` xoá sạch dấu vết.

### 5.4 Cuối request, PHP dọn những gì và theo thứ tự nào

Hàm `php_request_shutdown()` trong `main/main.c` (PHP 8.5) có chú thích đánh số từng bước. Những bước
liên quan trực tiếp tới code của bạn, theo đúng thứ tự:

1. Gọi các hàm đã đăng ký bằng `register_shutdown_function()`.
2. Gọi `__destruct()` của các object còn sống.
3. Đẩy hết output buffer ra ngoài.
4. Gọi RSHUTDOWN của từng extension.
5. Huỷ các superglobal (`$_GET`, `$_POST`, `$_SERVER`...).
6. Tắt compiler và executor của request; trả các ini đã đổi bằng `ini_set()` về giá trị gốc.
7. Giải phóng toàn bộ bộ nhớ của request.

Kiểm chứng thứ tự của bước 1 và 2:

```php
<?php
declare(strict_types=1);

final class KetNoi
{
    public function __destruct()
    {
        echo "3. __destruct: đóng kết nối\n";
    }
}

register_shutdown_function(function (): void {
    echo "2. shutdown function\n";
});

$ketNoi = new KetNoi();
echo "1. dòng cuối của script\n";
```

Output:

```
1. dòng cuối của script
2. shutdown function
3. __destruct: đóng kết nối
```

Bộ nhớ của request được cấp qua *Zend Memory Manager*, bộ cấp phát riêng của PHP. Vì mọi thứ thuộc về
request đều đi qua nó, cuối request PHP có thể thu hồi tất cả một lượt, kể cả những gì code quên giải
phóng. Theo PHP Internals Book, đó chính là thiết kế *share-nothing*: request sau không được nhớ gì
của request trước.

## 6. Một request web đi qua những đâu

### 6.1 Các nhân vật

Trang "Persistent Database Connections" của php.net xếp PHP-FPM, cùng với PHP chạy như module của
Apache, vào cách phổ biến nhất để web server chạy PHP. Mô hình rất hay gặp là Nginx đứng trước,
PHP-FPM đứng sau:

```
 Trình duyệt
     │  HTTP: GET /hello.php?name=An
     ▼
┌──────────────────┐   Tự trả file tĩnh (ảnh, CSS, JS).
│      Nginx       │   Gặp file .php thì chuyển cho PHP-FPM.
└────────┬─────────┘
         │  FastCGI, qua unix socket (vd /run/php/php-fpm.sock) hoặc TCP (vd 127.0.0.1:9000)
         ▼
┌───────────────────────────────────────────────┐
│ PHP-FPM                                       │
│   master ── quản lý, không chạy code của bạn  │
│   worker 1 (đang bận)                         │
│   worker 2 (rảnh) ◄── nhận request này        │
│   worker 3 (đang bận)                         │
└───────────────────────────────────────────────┘
```

- *Nginx* là web server: nhận kết nối HTTP từ trình duyệt, tự trả các file tĩnh. Nginx không chạy
  được PHP.
- *FastCGI* là giao thức để web server chuyển request cho một chương trình khác xử lý. Nginx gửi sang
  các tham số (đường dẫn file PHP cần chạy, method, query string, các header HTTP...) cùng body của
  request; chương trình bên kia gửi ngược lại output.
- *PHP-FPM* (FastCGI Process Manager) là SAPI `fpm-fcgi` đã gặp ở mục 4: nó nói FastCGI với Nginx và
  quản lý một nhóm worker.

Cấu hình Nginx tối thiểu theo hướng dẫn cài đặt trên php.net:

```nginx
location ~* \.php$ {
    fastcgi_index   index.php;
    fastcgi_pass    127.0.0.1:9000;
    include         fastcgi_params;
    fastcgi_param   SCRIPT_FILENAME    $document_root$fastcgi_script_name;
    fastcgi_param   SCRIPT_NAME        $fastcgi_script_name;
}
```

`fastcgi_pass` chỉ nơi PHP-FPM đang lắng nghe. `SCRIPT_FILENAME` là tham số quan trọng nhất: nó nói
cho FPM biết file PHP nào trên đĩa cần chạy. Cấu hình production đầy đủ, timeout và lỗi 502/504 ở
[chương 18](18-fpm-nginx-opcache.md).

### 6.2 Timeline của một request

Giả sử file `/var/www/html/hello.php`:

```php
<?php
declare(strict_types=1);

$name = $_GET['name'] ?? 'bạn';
echo 'Chào ' . htmlspecialchars($name);
```

| Bước | Trình duyệt | Nginx | PHP-FPM worker | Ghi chú |
|---|---|---|---|---|
| 1 | Gửi `GET /hello.php?name=An` | Nhận request, khớp `location ~* \.php$` | Đang chờ ở `fcgi_accept_request()` | |
| 2 | Chờ | Mở kết nối tới FPM, gửi tham số FastCGI (`SCRIPT_FILENAME=/var/www/html/hello.php`, `QUERY_STRING=name=An`...) | Một worker rảnh nhận kết nối | Nếu mọi worker đều bận, request phải xếp hàng |
| 3 | Chờ | Chờ | RINIT: các superglobal được dựng từ dữ liệu FastCGI, ví dụ `$_GET['name']` là `'An'` | Biến của bạn luôn bắt đầu từ trống |
| 4 | Chờ | Chờ | Lấy `hello.php` từ OPcache (hoặc biên dịch nếu chưa có), Zend VM chạy | Mục 2, 3 |
| 5 | Chờ | Nhận output từng phần | `echo` đi qua SAPI (`ub_write`), đóng gói thành bản tin FastCGI gửi về Nginx | Header HTTP gửi trước body |
| 6 | Nhận response `Chào An` | Gửi response HTTP cho trình duyệt | Script hết; RSHUTDOWN dọn sạch request (mục 5.4) | |
| 7 | | | Quay lại chờ request tiếp theo | Request sau có thể rơi vào worker khác |

Ba điều rút ra từ timeline:

1. **Mỗi worker chỉ xử lý một request tại một thời điểm.** Từ bước 2 tới bước 6, worker đó bận hoàn
   toàn. Số request PHP chạy song song tối đa bằng số worker (`pm.max_children`); request thứ
   `max_children + 1` phải chờ. Đây là con số quan trọng nhất khi tính sức chịu tải
   ([chương 18](18-fpm-nginx-opcache.md)).
2. **Không có gì đi từ request này sang request kia qua bộ nhớ PHP.** Request sau, dù cùng trình duyệt,
   có thể rơi vào worker khác; dù rơi đúng worker cũ thì bộ nhớ request cũng đã bị dọn.
3. Superglobal được dựng mới cho từng request từ dữ liệu FastCGI mà Nginx gửi sang. HTTP, header,
   cookie, session là chủ đề của [chương 15](15-php-va-web.md).

Muốn thử nhanh vòng đời này mà không cài Nginx: built-in web server `php -S localhost:8000`
([chương 01](01-php-la-gi.md)) cũng phục vụ mỗi HTTP request bằng một request PHP riêng (SAPI
`cli-server`), có RINIT và RSHUTDOWN như FPM. Khác biệt: theo php.net, mặc định nó chỉ chạy một
process đơn luồng, nên một request bị treo sẽ làm cả server đứng (từ PHP 7.4, biến môi trường
`PHP_CLI_SERVER_WORKERS` cho phép chạy nhiều worker, trừ trên Windows); php.net cũng cảnh báo nó chỉ
để hỗ trợ phát triển, không được dùng trên mạng công khai.

## 7. Share-nothing: mỗi request bắt đầu từ trang trắng

### 7.1 Định nghĩa và thí nghiệm

*Share-nothing* (không chia sẻ gì): không có gì trong bộ nhớ PHP của request này còn sống sang request
sau. Hết request, mọi biến global, biến `static`, thuộc tính static của class, object, kết nối database
thông thường, file đang mở đều bị huỷ. Request sau, dù rơi đúng vào worker cũ, bắt đầu từ trống.

File `counter.php`:

```php
<?php
declare(strict_types=1);

final class Counter
{
    private static int $hits = 0;

    public static function hit(): int
    {
        return ++self::$hits;
    }
}

echo 'Lần gọi thứ: ', Counter::hit(), "\n";
```

Chạy `php counter.php` hai lần, lần nào cũng in `Lần gọi thứ: 1`: mỗi lần là một process mới. Thú vị
hơn: chạy `php -S localhost:8000` trong thư mục đó rồi gọi `curl localhost:8000/counter.php` nhiều lần.
Built-in server là một process duy nhất sống suốt thời gian bạn thử, vậy mà kết quả vẫn luôn là
`1`: giữa hai request luôn có RSHUTDOWN (mục 5.4) xoá sạch thuộc tính static. Dưới PHP-FPM cũng y như
vậy.

Đừng nhầm "không sống qua request" với "không sống qua lời gọi hàm". Trong cùng một request, static
vẫn giữ giá trị giữa các lần gọi:

```php
<?php
declare(strict_types=1);

final class Counter
{
    private static int $hits = 0;

    public static function hit(): int
    {
        return ++self::$hits;
    }
}

// Ba lần gọi trong CÙNG một request
echo Counter::hit(), ' ', Counter::hit(), ' ', Counter::hit(), "\n";   // in ra: 1 2 3
```

### 7.2 Cái gì mất, cái gì còn

Mất khi hết request (nằm trong bộ nhớ của request):

- Mọi biến, object, mảng; biến `static` trong hàm; thuộc tính static của class.
- Hàm, class, hằng do code của bạn khai báo: request sau phải khai báo lại (nạp lại file, hoặc lấy từ
  OPcache nên rất nhanh).
- Kết nối database thường, file handle, output buffer, header đã đặt.
- Thay đổi cấu hình bằng `ini_set()` (được trả về giá trị gốc, mục 5.4).

Còn sống qua request: chỉ những thứ do extension viết bằng C giữ ở vùng nhớ nằm ngoài bộ nhớ của
request:

| Thứ còn sống | Ai giữ | Phạm vi |
|---|---|---|
| Opcode đã biên dịch | OPcache, trong shared memory | Mọi worker của cùng một master FPM |
| Dữ liệu cache do code tự lưu | Extension APCu, trong shared memory | Mọi worker của cùng một master FPM; không chia sẻ sang máy khác |
| Persistent connection (vd `PDO::ATTR_PERSISTENT`) | Extension database, trong bộ nhớ của từng process | Riêng từng worker |

Code PHP thuần không tự giữ được gì. Dữ liệu cần sống lâu hơn một request phải được lưu ra ngoài:
session (file, Redis), cache (Redis, Memcached), database, file. Đó là lý do ứng dụng PHP gần như luôn
đi kèm một database và một kho cache.

⚠️ Persistent connection không phải là "pool kết nối dùng chung" như ở Java hay Go. Theo php.net, mỗi
worker có bộ kết nối riêng, bạn không chọn được mình nhận kết nối nào, và trạng thái mà request trước
bỏ dở có thể dính sang request sau dùng lại kết nối đó: database đang chọn, table lock, transaction
chưa commit, bảng tạm (temporary table). php.net cũng nhắc rằng persistent connection thường làm tăng
tổng số kết nối đang mở tới database.

### 7.3 Ưu điểm và cái giá

| Ưu điểm | Vì sao |
|---|---|
| Cô lập lỗi | Một request lỗi, rò bộ nhớ hay để lại rác không ảnh hưởng request khác; cuối request mọi thứ bị dọn |
| Dễ suy luận | Hai request đang chạy song song ở hai worker không dùng chung biến nào, nên không có *race condition* (hai luồng cùng sửa một dữ liệu) trong bộ nhớ PHP |
| Dễ mở rộng ngang | State nằm ngoài (DB, Redis), thêm máy chủ là thêm sức chịu tải |
| Deploy đơn giản | Không có state trong RAM cần giữ lại; request tiếp theo đã chạy code mới (khi cache được làm mới đúng cách, mục 3.3) |

| Cái giá | Cách giảm |
|---|---|
| Mỗi request phải *bootstrap* (khởi động ứng dụng) lại: nạp autoloader, đọc config, dựng service container, đăng ký route... | OPcache bỏ được phần biên dịch nhưng không bỏ được phần chạy code bootstrap. Laravel có `php artisan optimize` để cache config, route ([chương 30](30-laravel-testing-octane-deploy.md)) |
| Không có cache trong RAM hay pool kết nối dùng chung giữa các request | Redis, APCu; với database thì dùng proxy pool bên ngoài nếu cần |
| Mỗi worker phục vụ một request một lúc, mỗi worker tốn RAM riêng | Tính `pm.max_children` theo RAM ([chương 18](18-fpm-nginx-opcache.md)) |
| Không chạy được việc nền sống lâu trong request web | Đưa sang queue worker ([chương 29](29-laravel-queue-event-schedule-cache.md)) |

## 8. So sánh với Node.js, Java, Go: process sống lâu

### 8.1 Mô hình process sống lâu

Node.js, Java (Spring Boot, Tomcat) và Go (`net/http`) đi theo hướng ngược lại: **một process khởi động
một lần, rồi phục vụ mọi request trong suốt đời nó**, thường là nhiều request cùng lúc. Biến ở cấp
module, package, hay field static sống suốt đời process và được mọi request dùng chung.

Cùng một bộ đếm, viết bằng ba ngôn ngữ đó:

```javascript
// counter.js: chạy bằng `node counter.js`
const http = require('node:http');

let hits = 0; // biến cấp module: sống suốt đời process, mọi request dùng chung

http.createServer((req, res) => {
  hits++;
  res.end(`hits = ${hits}\n`);
}).listen(3000);
```

```go
// main.go: chạy bằng `go run main.go`
package main

import (
	"fmt"
	"net/http"
	"sync/atomic"
)

// Biến cấp package: sống suốt đời process, mọi goroutine dùng chung.
var hits atomic.Int64

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		n := hits.Add(1) // atomic vì nhiều request có thể chạy song song
		fmt.Fprintf(w, "hits = %d\n", n)
	})
	http.ListenAndServe(":8080", nil)
}
```

```java
// Counter.java: chạy bằng `java Counter.java` (JDK 11+)
import com.sun.net.httpserver.HttpServer;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicLong;

public class Counter {
    // Field static: sống suốt đời JVM, mọi request dùng chung.
    static final AtomicLong hits = new AtomicLong();

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8081), 0);
        server.createContext("/", exchange -> {
            byte[] body = ("hits = " + hits.incrementAndGet() + "\n").getBytes(StandardCharsets.UTF_8);
            exchange.sendResponseHeaders(200, body.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(body);
            }
        });
        server.start();
    }
}
```

Gọi `curl` ba lần vào bất kỳ server nào ở trên (cổng 3000, 8080 hoặc 8081), kết quả là:

```
hits = 1
hits = 2
hits = 3
```

trong khi `counter.php` dưới PHP-FPM luôn in `1`. Để ý bản Go dùng kiểu *atomic*: `net/http` phục vụ
mỗi kết nối bằng một goroutine riêng, các request chạy song song thật, nếu hai request cùng tăng một
biến thường thì có thể mất một lần tăng (race condition). Bản Java dùng `AtomicLong` để an toàn khi
có nhiều thread: `HttpServer` ở đây chưa gọi `setExecutor()` nên theo tài liệu JDK mọi request được
xử lý trên một thread duy nhất, nhưng server Java thực tế (Tomcat, hoặc `HttpServer` có executor nhiều
thread) chạy nhiều request cùng lúc trên nhiều thread. Node.js chạy JavaScript trên một luồng duy
nhất (*event loop*) nên `hits++` không bị chen ngang, nhưng biến vẫn dùng chung giữa mọi request.

### 8.2 Hai mô hình đặt cạnh nhau

| Tiêu chí | PHP-FPM (share-nothing) | Node.js | Go `net/http` | Java (Spring Boot / Tomcat) |
|---|---|---|---|---|
| Ai phục vụ request | Nhiều worker process, mỗi worker một request một lúc | Một process, một luồng chạy JS với event loop, I/O bất đồng bộ | Một process; mỗi kết nối được một goroutine riêng phục vụ | Một JVM, mỗi request một thread trong thread pool |
| Khởi động ứng dụng | Lặp lại ở mỗi request | Một lần lúc start | Một lần lúc start | Một lần lúc start |
| Biến toàn cục giữa các request | Không còn | Dùng chung | Dùng chung, phải đồng bộ | Dùng chung, phải thread-safe |
| Rò rỉ dữ liệu giữa hai user | Rất khó xảy ra | Dễ, nếu lưu dữ liệu request vào biến module | Dễ, nếu lưu vào biến package | Dễ, nếu lưu vào singleton |
| Memory leak | Rò trong bộ nhớ request bị dọn cuối mỗi request | Tích tụ tới khi process khởi động lại | Tích tụ | Tích tụ |
| Kết nối database | Mỗi worker tự mở (hoặc persistent riêng từng worker) | Pool dùng chung trong process | Pool dùng chung (`database/sql`) | Pool dùng chung |

Không mô hình nào "thắng" tuyệt đối. Share-nothing đổi hiệu năng boot lấy sự đơn giản và an toàn;
process sống lâu đổi sự an toàn lấy tốc độ, và đòi lập trình viên kỷ luật hơn với state dùng chung.

### 8.3 PHP cũng có thể chạy kiểu sống lâu

PHP cũng chạy được theo mô hình của Node hay Go: khởi động ứng dụng một lần rồi phục vụ nhiều request
trong cùng bộ nhớ. Vài cách phổ biến: *worker mode* của FrankenPHP (nhúng PHP qua SAPI riêng, mục 4),
extension Swoole, RoadRunner (server viết bằng Go, giữ các process PHP chạy lâu làm worker). *Laravel
Octane* là lớp tích hợp Laravel với các server đó ([chương 30](30-laravel-testing-octane-deploy.md)).

Tài liệu worker mode của FrankenPHP mô tả đúng cái giá phải trả: biến `static` trong hàm, thuộc tính
static của class, biến global của worker script và mọi dữ liệu lưu trong bộ nhớ ngoài phần xử lý
request đều sống qua các request. Tài liệu đó dùng chính ví dụ bộ đếm `static`: mỗi request trên
cùng một worker in ra 1, 2, 3... như Node. Code viết cho FPM vô tư lưu dữ liệu của user hiện tại vào
biến static, khi chuyển sang mô hình sống lâu sẽ rò dữ liệu của user này sang user khác. Hiểu
share-nothing là điều kiện để hiểu vì sao.

## Lỗi thường gặp

| Lỗi | Vì sao xảy ra | Cách tránh |
|---|---|---|
| Sửa đúng dòng báo lỗi cú pháp mà không hết lỗi | Parser chỉ phát hiện sai khi gặp token không hợp lệ, thường là ở dòng ngay sau chỗ sai thật (mục 2.3) | Xem cả dòng báo lỗi và dòng phía trên; chạy `php -l` |
| Tin rằng `php -l` qua là code không lỗi | `-l` chỉ kiểm tra cú pháp, không phát hiện lỗi chỉ lộ ra khi chạy như gọi hàm không tồn tại | Thêm phân tích tĩnh và test ([chương 21](21-chat-luong-code.md)) |
| Có khoảng trắng, dòng trống, BOM trước `<?php` hoặc sau `?>` cuối file | Phần đó là `T_INLINE_HTML`, được biên dịch thành lệnh in ra, gây lỗi "headers already sent" | Bỏ thẻ đóng `?>` ở file chỉ chứa PHP ([chương 15](15-php-va-web.md)) |
| Lưu dữ liệu vào biến static, biến global để request sau dùng | Share-nothing: RSHUTDOWN xoá hết bộ nhớ của request (mục 7) | Lưu ra ngoài: session, cache, database |
| Sửa php.ini mà web không đổi | Sửa nhầm ini của CLI; hoặc sửa đúng ini của FPM nhưng chưa reload, vì FPM chỉ đọc php.ini lúc khởi động (mục 4.3) | Xem `phpinfo()` qua web để biết FPM dùng file nào; reload FPM sau khi sửa |
| Deploy xong web vẫn chạy code cũ | OPcache với `validate_timestamps=0` không bao giờ kiểm tra file trên đĩa (mục 3.3) | Reload PHP-FPM trong quy trình deploy ([chương 18](18-fpm-nginx-opcache.md)) |
| Gọi `opcache_reset()` hoặc `opcache_get_status()` trong terminal để quản lý cache của web | CLI là process khác với cache khác (mục 3.4) | Thao tác bên trong FPM, hoặc reload FPM |
| Bật `opcache.opt_debug_level` mà không thấy opcode in ra | CLI chưa bật OPcache, hoặc file vừa sửa chưa quá 2 giây nên không được cache, hoặc đang nhìn stdout trong khi dump đi ra stderr (mục 2.5) | Thêm `-d opcache.enable_cli=1 -d opcache.file_update_protection=0`, xem stderr |
| Code chạy tốt trên FPM, rò dữ liệu giữa user khi chuyển sang Octane, FrankenPHP worker hoặc trong queue worker | Process sống lâu (hoặc một request CLI rất dài) giữ static và singleton qua nhiều request, nhiều job (mục 5.2, 8.3) | Không giữ dữ liệu theo request trong static, singleton ([chương 29](29-laravel-queue-event-schedule-cache.md), [chương 30](30-laravel-testing-octane-deploy.md)) |
| Coi persistent connection là pool dùng chung | Mỗi worker có kết nối riêng; transaction, lock bỏ dở có thể dính sang request sau (mục 7.2) | Chỉ dùng khi hiểu rõ; luôn kết thúc transaction, nhả lock |

## Tóm tắt chương

- PHP biên dịch mã nguồn sang opcode ngay lúc chạy, rồi Zend VM thông dịch opcode; JIT (từ PHP 8.0) là
  tuỳ chọn và không bật sẵn.
- Hành trình một file: lexer cắt thành token, parser dựng AST và bắt lỗi cú pháp, compiler sinh opcode
  vào op_array (một cho code ngoài hàm, một cho mỗi hàm), Zend VM chạy từng opcode qua handler của nó.
- Đơn vị biên dịch là một file, biên dịch khi file được nạp. Lỗi cú pháp làm cả file không chạy dòng
  nào; lỗi như gọi hàm không tồn tại chỉ lộ ra khi VM chạy tới.
- OPcache lưu op_array đã tối ưu vào shared memory để request sau bỏ qua lexer, parser, compiler. Mặc
  định bật cho web, tắt cho CLI; từ PHP 8.5 luôn được build sẵn trong PHP.
- SAPI là lớp nối engine với môi trường: `cli`, `cli-server`, `fpm-fcgi`, `apache2handler`, `embed`...
  Mỗi SAPI có thể có php.ini và hành vi riêng.
- Vòng đời: MINIT một lần mỗi process; RINIT, chạy script, RSHUTDOWN cho mỗi request. CLI là một
  process một request; mỗi worker FPM phục vụ nhiều request nối tiếp, mỗi lúc một request.
- Request web: trình duyệt, Nginx, FastCGI, worker FPM rảnh, RINIT, chạy script, output về Nginx,
  RSHUTDOWN, worker chờ request tiếp.
- Share-nothing: hết request mọi biến, static, object, kết nối thường đều bị huỷ; chỉ thứ do extension
  giữ ngoài bộ nhớ request (OPcache, APCu, persistent connection) còn lại. Đổi lại là bootstrap mỗi
  request.
- Node.js, Go, Java giữ một process sống lâu, state dùng chung giữa các request. PHP cũng chạy được kiểu
  đó (FrankenPHP worker, Swoole, RoadRunner, Octane) và khi ấy chịu đúng rủi ro rò state như họ.

## Câu hỏi tự kiểm tra

1. Vì sao câu "PHP là ngôn ngữ thông dịch" chỉ đúng một nửa? So sánh với Go và Java.
2. Đoạn `$x = = 1;` bị phát hiện sai ở bước lexer hay parser? Vì sao? (gợi ý: mục 2.1, 2.2)
3. Một file có lỗi cú pháp ở dòng cuối và một file gọi hàm không tồn tại ở dòng cuối. File nào in được
   các dòng phía trên, file nào không? Giải thích bằng ranh giới biên dịch và thực thi.
4. Đọc dòng `T4 = ADD T3 int(1)`: từng phần nghĩa là gì? `CV`, `TMP_VAR`, `CONST` khác nhau thế nào?
   (gợi ý: mục 2.4)
5. Vì sao gọi được hàm trước dòng khai báo của nó, nhưng không gọi được một hàm khai báo trong `if`
   trước khi `if` đó chạy? Lệnh opcode nào tạo ra khác biệt?
6. OPcache bỏ được những bước nào khi chạy một file, và bước nào nó không bỏ được? Vì sao bật
   OPcache cho lệnh `php script.php` thường ít lợi? (gợi ý: mục 3.1, 3.4)
7. SAPI là gì? Vì sao `php -m` hay `php --ini` gõ trong terminal có thể cho thông tin sai về server
   web của bạn?
8. Trong PHP-FPM, MINIT chạy ở process nào và bao nhiêu lần? Vì sao worker không phải MINIT lại?
   (gợi ý: mục 5.3)
9. Queue worker `php artisan queue:work` có "share-nothing giữa các job" không? Vì sao?
10. Kể những thứ sống qua request trong PHP-FPM và ai giữ chúng. Vì sao code PHP thuần không tự giữ
    được gì qua request?

## Bài tập

1. **Thống kê token.** Viết `token_stats.php` nhận đường dẫn một file PHP từ `$argv[1]`, dùng
   `PhpToken::tokenize()` để đếm mỗi loại token xuất hiện bao nhiêu lần, bỏ qua token mà
   `isIgnorable()` trả về `true`, in kết quả sắp xếp giảm dần theo số lần. Chạy trên chính file đó và
   trên một file có HTML lẫn PHP. Câu hỏi phụ: những token nào bị coi là "ignorable", và vì sao parser
   bỏ qua được chúng?
2. **Quan sát compiler và optimizer.** Viết ba phiên bản của phép tính số giây trong một tuần: (a) biểu
   thức hằng `7 * 24 * 60 * 60` ở code ngoài hàm; (b) trong một hàm, dùng biến trung gian như
   `secondsPerDay()` ở mục 3.5; (c) số ngày đọc từ `$argv[1]`. Dump opcode của cả ba với
   `opt_debug_level=0x10000` và `0x20000`. Ghi lại: phép tính nào compiler tự tính, phép tính nào
   chỉ optimizer tính được, phép tính nào không ai tính trước được, và giải thích vì sao.
3. **Bộ đếm lượt xem.** Viết `visit.php` đếm số lượt truy cập trang, chạy bằng `php -S localhost:8000`
   và gọi bằng `curl` nhiều lần. Phiên bản 1 dùng thuộc tính static (quan sát và giải thích kết quả).
   Phiên bản 2 lưu số đếm vào file `counter.txt` sao cho đúng ngay cả khi nhiều request chạy cùng lúc
   (tìm hiểu `flock()`, [chương 14](14-file-json-thoi-gian.md)). So sánh với các server Node, Go,
   Java ở mục 8.1: cách nào đúng khi chạy nhiều worker, nhiều máy?
4. **Cùng file, khác SAPI.** Viết `whoami.php` in ra `PHP_SAPI`, `php_ini_loaded_file()`,
   `ini_get('max_execution_time')`, `ini_get('memory_limit')` và `getcwd()`. Chạy bằng `php whoami.php`
   từ một thư mục khác thư mục chứa file, rồi chạy qua `php -S`. Giải thích từng khác biệt dựa trên
   mục 4.

## Đọc thêm

- php.net: [OPcache](https://www.php.net/manual/en/book.opcache.php),
  [Cấu hình OPcache](https://www.php.net/manual/en/opcache.configuration.php),
  [PhpToken](https://www.php.net/manual/en/class.phptoken.php),
  [List of Parser Tokens](https://www.php.net/manual/en/tokens.php),
  [User-defined functions](https://www.php.net/manual/en/functions.user-defined.php),
  [include](https://www.php.net/manual/en/function.include.php),
  [ParseError](https://www.php.net/manual/en/class.parseerror.php)
- php.net, phần dòng lệnh và SAPI:
  [Differences from other SAPIs](https://www.php.net/manual/en/features.commandline.differences.php),
  [Command line options](https://www.php.net/manual/en/features.commandline.options.php) (`-l`),
  [Built-in web server](https://www.php.net/manual/en/features.commandline.webserver.php),
  [php_sapi_name()](https://www.php.net/manual/en/function.php-sapi-name.php),
  [The configuration file](https://www.php.net/manual/en/configuration.file.php),
  [Nginx và PHP-FPM](https://www.php.net/manual/en/install.unix.nginx.php),
  [Persistent Database Connections](https://www.php.net/manual/en/features.persistent-connections.php)
- php.net: [History of PHP](https://www.php.net/manual/en/history.php.php),
  [PHP 8.0 release](https://www.php.net/releases/8.0/en.php) (phần JIT)
- RFC: [Abstract syntax tree](https://wiki.php.net/rfc/abstract_syntax_tree),
  [JIT](https://wiki.php.net/rfc/jit),
  [Make OPcache a non-optional part of PHP](https://wiki.php.net/rfc/make_opcache_required)
- PHP Internals Book: [Learning the PHP lifecycle](https://www.phpinternalsbook.com/php7/extensions_design/php_lifecycle.html)
- Mã nguồn [php-src](https://github.com/php/php-src) (nhánh PHP-8.5): `Zend/zend_language_scanner.l`,
  `Zend/zend_language_parser.y`, `Zend/zend_compile.c`, `Zend/zend_vm_def.h`,
  `main/main.c` (`php_request_shutdown()`), `sapi/fpm/fpm/fpm_main.c`, `sapi/embed/README.md`,
  `UPGRADING`
- FrankenPHP: [Worker mode](https://frankenphp.dev/docs/worker/)
