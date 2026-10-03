# Chương 01. PHP là gì và chạy chương trình đầu tiên

> [← Mục lục](README.md) · [Chương 02: PHP chạy như thế nào →](02-php-chay-nhu-the-nao.md)

**Bạn sẽ học được:**

- PHP là gì, ra đời thế nào, dùng để làm gì và vì sao tài liệu PHP trên mạng "mỗi nơi một kiểu".
- Cách đọc số phiên bản (8.4.26 nghĩa là gì), lịch phát hành hằng năm và vòng đời hỗ trợ 4 năm; chọn
  bản nào cho dự án mới.
- Cài PHP bằng Homebrew, Docker, gói của Linux hoặc bản tải từ php.net, rồi kiểm tra cài đặt.
- Chạy script bằng dòng lệnh, thử nhanh bằng REPL `php -a`, dựng web server thử nghiệm bằng `php -S`.
- Cấu trúc một file PHP chuẩn và vì sao nên bỏ thẻ đóng `?>`.
- `php.ini` là gì, tìm nó bằng `php --ini`, đổi cấu hình theo nhiều cách; extension là gì và xem bằng
  `php -m`.

**Cần biết trước:** không cần gì. Chỉ cần biết mở terminal (Terminal trên macOS, PowerShell hoặc WSL
trên Windows) và gõ lệnh.

Cách đọc chương này: mục 1 và 2 là kiến thức nền (đọc để hiểu), từ mục 3 trở đi là thực hành, hãy mở
terminal và gõ theo. Các file ví dụ PHP trong chương đều đã chạy thật trên PHP 8.5 (và 8.4 khi so
sánh); output ghi trong comment `// in ra: ...` hoặc trong khối output ngay sau. Riêng phiên REPL (mục
5) và log của web server (mục 6) được ghi rõ là minh hoạ.

## 1. PHP là gì

### 1.1 Một định nghĩa bằng lời thường

Tài liệu chính thức (PHP Manual) định nghĩa:

> PHP (recursive acronym for PHP: Hypertext Preprocessor) is a widely-used open source
> general-purpose scripting language that is especially suited for web development and can be
> embedded into HTML.

Tách từng phần ra cho dễ hiểu:

| Cụm từ | Nghĩa |
|---|---|
| *recursive acronym* (từ viết tắt đệ quy) | PHP là viết tắt của "PHP: Hypertext Preprocessor". Chữ P đầu tiên lại chính là "PHP". Ban đầu PHP viết tắt cho "Personal Home Page" (xem mục 1.4) |
| *open source* (mã nguồn mở) | Miễn phí, ai cũng xem được mã nguồn. Bản thân PHP được viết bằng ngôn ngữ C, mã nguồn ở [github.com/php/php-src](https://github.com/php/php-src) |
| *general-purpose* (đa dụng) | Không chỉ làm web: viết script dòng lệnh, công cụ xử lý file, chương trình chạy nền đều được |
| *scripting language* (ngôn ngữ kịch bản) | Bạn viết mã nguồn ra file `.php` rồi đưa thẳng file đó cho chương trình `php` chạy. Không có bước "build ra file thực thi" riêng như C hay Go |
| *especially suited for web development* | Có sẵn những thứ web cần: đọc dữ liệu request (`$_GET`, `$_POST`, cookie), gửi header, session, sinh HTML hoặc JSON, mà không phải cài thư viện ngoài |
| *embedded into HTML* | Mã PHP có thể viết xen vào giữa một file HTML |

Về chữ "scripting": đừng hiểu là PHP đọc từng dòng rồi chạy từng dòng. Khi bạn chạy một file, PHP
dịch (compile) toàn bộ file sang một dạng lệnh trung gian gọi là *opcode*, rồi mới thực thi các opcode
đó. Bước dịch này diễn ra trong bộ nhớ, mỗi lần chạy, và bạn không thấy nó. Chi tiết ở
[Chương 02](02-php-chay-nhu-the-nao.md).

Khi nói "PHP" người ta có thể đang nói tới ba thứ khác nhau, nên tách bạch ngay từ đầu:

- Ngôn ngữ PHP: cú pháp, quy tắc (`$bien`, `function`, `class`...).
- *Trình thông dịch* (interpreter) PHP: chương trình tên `php` (hoặc `php-fpm`) bạn cài vào máy, đọc
  file `.php` và chạy nó. Lõi của trình thông dịch tên là *Zend Engine* (xem
  [Chương 19](19-ben-trong-engine.md)).
- Thư viện chuẩn và *extension*: hàng nghìn hàm, class có sẵn như `strlen()`, `json_encode()`, `PDO`.
  Phần lớn nằm trong các extension (mục 9).

### 1.2 Ví dụ: PHP nhúng trong HTML

Cách dễ hình dung nhất về PHP là một trang HTML có "lỗ hổng" để PHP điền nội dung vào. Tạo file
`trang.php`:

```php
<!DOCTYPE html>
<html>
    <body>
        <h1>Đơn hàng</h1>
        <p>Hôm nay có <?php echo 2 + 3; ?> đơn hàng mới.</p>
        <p>Tổng: <?= number_format(1250000) ?> đồng</p>
    </body>
</html>
```

Mọi thứ nằm ngoài cặp thẻ `<?php ... ?>` được PHP chép nguyên ra output. Mã nằm trong cặp thẻ được
chạy, và cái nó in ra (bằng `echo`) thay vào đúng chỗ đó. `<?= ... ?>` là cách viết tắt của
`<?php echo ...; ?>`. Chạy file này, output là:

```html
<!DOCTYPE html>
<html>
    <body>
        <h1>Đơn hàng</h1>
        <p>Hôm nay có 5 đơn hàng mới.</p>
        <p>Tổng: 1,250,000 đồng</p>
    </body>
</html>
```

Điểm mấu chốt: mã PHP chạy trên *server* (máy chủ), không chạy trên trình duyệt. Trình duyệt chỉ nhận
được HTML kết quả, không bao giờ thấy dòng `<?php echo 2 + 3; ?>`. Đây là khác biệt cơ bản với
JavaScript chạy trong trình duyệt (client-side):

```
  Trình duyệt                    Server
  ───────────                    ──────────────────────────────────────────
  GET /trang.php  ───────────►   Web server nhận request
                                    │
                                    ▼
                                 PHP đọc trang.php, chạy phần trong <?php ?>
                                    │   (2 + 3 = 5, number_format(...))
                                    ▼
  Nhận HTML thuần ◄───────────   HTML kết quả: "...có 5 đơn hàng mới..."
  (không có mã PHP)
```

Vì mã chạy trên server, PHP được phép làm những việc trình duyệt không được làm: đọc database, đọc
file trên server, giữ bí mật mật khẩu kết nối database. Người dùng không thể xem hay sửa mã đó.

Kiểu "HTML có xen PHP" là cách PHP được dùng từ những ngày đầu. Ứng dụng hiện đại thường tách riêng:
file PHP thuần chứa logic, còn HTML nằm trong *template* (Laravel dùng Blade, xem
[Chương 25](25-laravel-request-validation-response.md)), hoặc server chỉ trả JSON cho một ứng dụng
front-end riêng. Nhưng cơ chế bên dưới vẫn là cái bạn vừa thấy.

### 1.3 PHP dùng để làm gì

Manual chia việc dùng PHP thành hai mảng chính.

1. *Server-side scripting* (lập trình phía server). Đây là mảng chính: website, trang quản trị, REST
   API trả JSON cho app mobile hoặc front-end. Cần ba thứ: trình thông dịch PHP, một web server (Nginx,
   Apache...) và một trình duyệt hoặc client gọi tới. Cả ba có thể chạy trên máy bạn để học.
2. *Command line scripting* (script dòng lệnh). Chạy PHP không cần web server hay trình duyệt, chỉ
   cần trình thông dịch. Dùng cho script chạy định kỳ bằng cron, công cụ xử lý dữ liệu, import file
   CSV, và các tiến trình chạy nền (ví dụ *queue worker* của Laravel, xem
   [Chương 29](29-laravel-queue-event-schedule-cache.md)).

PHP không chỉ sinh ra HTML: nó có thể xuất JSON, XML, ảnh, file PDF, gửi email, và làm việc với rất
nhiều loại database (MySQL, PostgreSQL, SQLite...) qua lớp trừu tượng PDO (xem
[Chương 16](16-php-va-database.md)). PHP chạy trên Linux, macOS, Windows và nhiều hệ Unix khác, đi
cùng hầu hết web server phổ biến.

Một vài phần mềm nổi tiếng viết bằng PHP, để bạn hình dung hệ sinh thái:

| Loại | Ví dụ |
|---|---|
| Framework web | Laravel (trọng tâm của giáo trình này, từ [Chương 23](23-laravel-gioi-thieu.md)), Symfony |
| CMS (hệ quản trị nội dung) | WordPress, Drupal |
| Công cụ cho lập trình viên PHP | Composer (trình quản lý thư viện, xem [Chương 11](11-namespace-composer.md)), PHPUnit (kiểm thử), PHPStan (phân tích tĩnh) |

Composer, PHPUnit, PHPStan đều là chương trình PHP chạy bằng dòng lệnh. Nghĩa là ngay cả khi chỉ làm
web, bạn vẫn dùng PHP CLI hằng ngày.

### 1.4 Lịch sử ngắn

Biết lịch sử giúp bạn hiểu vì sao có những thứ "kỳ lạ" trong PHP, và vì sao tài liệu trên mạng mỗi
nơi một kiểu. Bảng dưới tóm tắt từ trang [History of PHP](https://www.php.net/manual/en/history.php.php)
của manual:

| Thời điểm | Mốc | Điều đáng nhớ |
|---|---|---|
| 1994 | Rasmus Lerdorf viết "Personal Home Page Tools" | Một bộ chương trình CGI viết bằng C để theo dõi lượt xem trang CV online của chính ông. Chưa phải ngôn ngữ |
| 1995 | Công bố mã nguồn (tháng 6), rồi viết lại | Đã có biến kiểu Perl, tự đọc dữ liệu form, nhúng trong HTML |
| 1996 đến 1997 | PHP/FI 2.0 | Hỗ trợ database (mSQL, Postgres95...), cookie, hàm do người dùng định nghĩa. Vẫn chủ yếu do một người phát triển |
| 06/1998 | PHP 3.0 | Andi Gutmans và Zeev Suraski viết lại toàn bộ parser. Đổi tên thành "PHP: Hypertext Preprocessor". Thế mạnh lớn là dễ mở rộng: hàng chục lập trình viên góp thêm module cho database, giao thức, API |
| 05/2000 | PHP 4.0 | Chạy trên *Zend Engine* (Zend ghép từ tên Zeev và Andi). Nhanh hơn nhiều, có session, output buffering |
| 07/2004 | PHP 5 | Zend Engine 2 với mô hình object mới, nền móng cho cách viết class bạn sẽ học ở [Chương 09](09-oop-co-ban.md) |
| (không có) | PHP 6 | Kế hoạch hỗ trợ Unicode tận lõi bị bỏ dở. Các tính năng khác của nó chuyển sang PHP 5.3 (namespace) và 5.4 (trait, cú pháp mảng ngắn `[]`). Vì vậy sau 5 là 7 |
| 2015 | PHP 7.0 | Zend Engine 3: nhanh tới khoảng gấp đôi PHP 5.6, tốn ít bộ nhớ hơn, toán tử `??`, anonymous class. Dòng 7.x thêm dần kiểu dữ liệu, tới 7.4 có typed property |
| 2020 | PHP 8.0 | Named arguments, union types, attributes, `match`, nullsafe `?->`, trình biên dịch JIT |
| 2021 đến 2023 | 8.1, 8.2, 8.3 | 8.1: enum, readonly property, fiber. 8.2: readonly class, DNF type. 8.3: typed class constant |
| 11/2024 | 8.4 | Property hooks, asymmetric visibility |
| 11/2025 | 8.5 | Toán tử pipe `\|>`, "clone with", extension URI |

Bạn chưa cần hiểu các tính năng trong cột cuối; chúng được giải thích dần trong các chương sau và tổng
hợp ở [Chương 22](22-phien-ban-moi.md). Điều cần rút ra từ bảng:

- PHP lớn lên dần từ một bộ công cụ cá nhân, qua nhiều lần viết lại, chứ không được thiết kế trọn
  vẹn ngay từ đầu, và mỗi bản mới cố giữ cho code cũ chạy được. Vì vậy bạn sẽ gặp những điểm thiếu
  nhất quán còn sót lại: tên hàm lúc có gạch dưới lúc không (`str_replace` nhưng `strlen`), thứ tự
  tham số lúc thế này lúc thế khác (`strpos($haystack, $needle)` nhưng
  `in_array($needle, $haystack)`). FAQ của manual đưa ra quy tắc nhớ: hàm mảng xếp "needle, haystack",
  hàm chuỗi ngược lại "haystack, needle"; từ PHP 8.0 có thêm named arguments nên thứ tự bớt quan trọng.
  Không chắc thì tra manual, đừng đoán.
- PHP 7 và PHP 8 thay đổi rất nhiều. Nhiều lời chê PHP bạn nghe được bắt nguồn từ thời PHP 4, 5, và
  nhiều điểm trong đó đã được sửa. Ví dụ, ở PHP 8.0 kết quả của `0 == "a"` đổi từ `true` thành
  `false` (xem [Chương 04](04-kieu-du-lieu.md)).
- Tài liệu cũ trên mạng rất nhiều. Nếu một bài hướng dẫn dùng `mysql_connect()`, nó đã lỗi thời hơn
  10 năm: extension `mysql` bị đánh dấu deprecated từ PHP 5.5.0 và bị xoá hẳn ở PHP 7.0.0. Code đó
  không chạy trên PHP hiện đại.

⚠️ Khi tra cứu trên mạng, luôn để ý bài viết dành cho bản PHP nào. Nguồn đáng tin nhất là manual tại
[php.net/manual](https://www.php.net/manual/en/): mỗi trang hàm ghi các bản PHP có hàm đó (ví dụ
"PHP 4, PHP 5, PHP 7, PHP 8"), và nhiều trang có mục "Changelog" liệt kê thay đổi theo phiên bản.

Ngôn ngữ PHP ngày nay được phát triển công khai. Mỗi thay đổi đáng kể được đề xuất bằng một *RFC*
(Request for Comments) đăng trên [wiki.php.net/rfc](https://wiki.php.net/rfc), thảo luận trên mailing
list `internals@lists.php.net`, rồi đưa ra bỏ phiếu. Người được bỏ phiếu là những người có tài khoản
php.net đã đóng góp mã cho PHP, cùng một số đại diện cộng đồng (ví dụ người dẫn dắt các framework lớn).
Phiếu chính của một RFC chỉ được chấp nhận khi số phiếu "Yes" ít nhất gấp đôi số phiếu "No" (đa số
2/3, phiếu "Abstain" không tính). Khi muốn biết vì sao một tính năng được thiết kế như vậy, đọc RFC
của nó là cách nhanh nhất.

## 2. Phiên bản và vòng đời hỗ trợ

Trước khi cài, bạn cần biết nên cài bản nào. Muốn chọn đúng thì phải đọc được số phiên bản và hiểu
mỗi bản được hỗ trợ tới bao giờ.

### 2.1 Đọc số phiên bản

PHP đánh số theo dạng `major.minor.patch`. Ví dụ `8.4.26`:

```
  8   .   4   .   26
  │       │       └── patch: bản vá thứ 26 của nhánh 8.4
  │       └────────── minor: bản tính năng thứ 4 của dòng 8
  └────────────────── major: dòng lớn
```

Tập hợp mọi bản `8.4.x` gọi là *nhánh* (branch) 8.4. Chính sách phát hành của PHP
([release-process](https://github.com/php/policies/blob/main/release-process.rst)) quy định mỗi bậc
được phép thay đổi những gì:

| Bậc | Ví dụ | Chứa gì | Có thể làm hỏng code đang chạy? |
|---|---|---|---|
| Patch | 8.4.25 → 8.4.26 | Sửa lỗi và vá bảo mật. Không được thêm tính năng | Không: API mà code PHP của bạn dùng phải giữ nguyên |
| Minor | 8.4 → 8.5 | Tính năng mới, đánh dấu deprecated, đôi khi bỏ hẳn một thứ đã deprecated | Có thể. Nhưng chính sách quy định thay đổi phá vỡ nên "lộ ra" (ném exception hoặc báo lỗi) thay vì âm thầm đổi kết quả (ngoại lệ được xét từng trường hợp), và code hợp lệ vẫn nên parse được |
| Major | 8.x → 9.0 | Thay đổi lớn | Có. Các thay đổi lớn nên được báo trước bằng deprecation ở dòng major trước đó |

*Deprecated* (bị phản đối) nghĩa là tính năng vẫn chạy nhưng PHP phát cảnh báo `E_DEPRECATED`, báo
rằng nó sẽ bị xoá ở một bản sau. Ví dụ đã thấy ở mục 1.4: extension `mysql` deprecated ở 5.5.0, bị
xoá ở 7.0.0. Khi thấy cảnh báo deprecated trong log, hãy sửa sớm, đừng đợi tới lúc nâng cấp mới phát
hiện. Cách bật, tắt các loại cảnh báo nằm ở [Chương 12](12-loi-exception.md).

Hệ quả thực tế: nâng patch (8.4.25 lên 8.4.26) nên làm thường xuyên, gần như không rủi ro. Nâng minor
(8.4 lên 8.5) là một việc cần kế hoạch: đọc hướng dẫn chuyển đổi (*migration guide*) trong manual, chạy
test, xử lý deprecation. [Chương 22](22-phien-ban-moi.md) bàn kỹ chuyện nâng cấp.

### 2.2 Mỗi năm một bản minor

PHP ra một bản minor mỗi năm. Quy trình bắt đầu vào thứ Ba đầu tiên của tháng 7, kéo dài khoảng 20
tuần qua các bản thử nghiệm *alpha*, *beta*, *RC* (release candidate), rồi ra bản chính thức `x.y.0`
(gọi là *GA*, general availability), thường vào cuối tháng 11:

| Nhánh | Ngày ra bản x.y.0 |
|---|---|
| 8.2 | 08/12/2022 |
| 8.3 | 23/11/2023 |
| 8.4 | 21/11/2024 |
| 8.5 | 20/11/2025 |

Tại thời điểm viết (đầu 10/2026), PHP 8.6 đang ở giai đoạn RC; lịch trên
[wiki.php.net/todo/php86](https://wiki.php.net/todo/php86) dự kiến GA ngày 19/11/2026 (lịch có thể
đổi). Bản RC dùng để thử, không dùng cho production.

Sau GA, mỗi nhánh còn được hỗ trợ ra bản patch định kỳ (mục 2.3).

### 2.3 Vòng đời 4 năm: 2 năm active, 2 năm security

Mỗi nhánh được hỗ trợ tổng cộng 4 năm, chia hai giai đoạn
([Supported Versions](https://www.php.net/supported-versions.php)):

1. *Active support* (hỗ trợ đầy đủ), 2 năm: sửa lỗi thường và lỗi bảo mật. Bản patch ra đều đặn, khoảng
   4 tuần một lần.
2. *Security support* (chỉ vá bảo mật), 2 năm tiếp theo: chỉ sửa lỗi bảo mật nghiêm trọng (và vài loại
   lỗi đặc biệt như crash). Bản patch chỉ ra khi cần, có khi không có bản nào.

Hết 4 năm, nhánh tới *end of life* (EOL): không còn bản vá nào nữa, kể cả khi có lỗ hổng bảo mật mới.
Các mốc kết thúc được làm tròn về ngày 31/12 của năm tương ứng.

Bảng nhánh còn được hỗ trợ (theo php.net, xem ngày 03/10/2026; bản mới nhất ra ngày 24/09/2026):

| Nhánh | Hết active support | Hết security support | Trạng thái 10/2026 | Bản mới nhất |
|---|---|---|---|---|
| 8.5 | 31/12/2027 | 31/12/2029 | Active | 8.5.11 |
| 8.4 | 31/12/2026 | 31/12/2028 | Active, sắp chuyển sang security | 8.4.26 |
| 8.3 | 31/12/2025 | 31/12/2027 | Chỉ vá bảo mật | 8.3.35 |
| 8.2 | 31/12/2024 | 31/12/2026 | Chỉ vá bảo mật, EOL cuối năm nay | 8.2.34 |

Một số nhánh đã EOL ([Unsupported Branches](https://www.php.net/eol.php)):

| Nhánh | Ngày EOL | Bản cuối cùng |
|---|---|---|
| 8.1 | 31/12/2025 | 8.1.34 |
| 8.0 | 26/11/2023 | 8.0.30 |
| 7.4 | 28/11/2022 | 7.4.33 |

Vẽ ra thành trục thời gian:

```
       2023  2024  2025  2026  2027  2028  2029  2030
8.2    ████████████░░░░░░░░░░░░|
8.3         █████████████░░░░░░░░░░░░|
8.4               █████████████░░░░░░░░░░░░|
8.5                     █████████████░░░░░░░░░░░░|
                             ▲ hôm nay (10/2026)

█ active support: sửa lỗi + vá bảo mật, ra bản đều đặn
░ security support: chỉ vá lỗi bảo mật nghiêm trọng, ra bản khi cần
| end of life (31/12)
```

Vì sao 8.0 EOL ngày 26/11 còn 8.1 EOL ngày 31/12? Trước năm 2024, mỗi nhánh chỉ có 2 năm active cộng 1
năm security, và ngày hết hạn tính đúng ngày kỷ niệm phát hành (8.0 ra 26/11/2020, EOL 26/11/2023).
RFC [Release cycle update](https://wiki.php.net/rfc/release_cycle_update) (2024) kéo dài phần security
thêm 1 năm và làm tròn mọi mốc về 31/12. Thay đổi áp dụng ngay cho các nhánh từ 8.2 trở đi, và 8.1
cũng được thêm một năm vá bảo mật. Nếu đọc tài liệu cũ ghi "mỗi bản được hỗ trợ 3 năm", đó là quy tắc
cũ.

### 2.4 Chọn bản nào

Quy tắc đơn giản:

- Dự án mới: chọn bản minor mới nhất đã ra chính thức, hoặc bản ngay trước nó nếu thư viện bạn cần
  chưa hỗ trợ bản mới nhất. Tại 10/2026 là 8.5 hoặc 8.4. Giáo trình này dùng 8.5 làm chuẩn và ghi chú
  khi 8.4 khác.
- Laravel 13 (ra 17/03/2026) yêu cầu tối thiểu PHP 8.3 và hỗ trợ 8.3 tới 8.5
  ([Laravel release notes](https://laravel.com/docs/13.x/releases)).
- Đang chạy nhánh đã EOL (8.1 trở về trước): lên kế hoạch nâng cấp. Lỗ hổng bảo mật mới phát hiện sẽ
  không được vá trên nhánh đó.
- Máy dev và server production nên cùng một bản minor. Nếu máy bạn chạy 8.5 còn server chạy 8.4, code
  dùng tính năng của 8.5 sẽ chạy tốt ở máy bạn rồi hỏng trên server. Khai báo `"php": "^8.4"` trong
  `composer.json` chỉ giúp `composer install` từ chối chạy trên bản thấp hơn 8.4 (xem
  [Chương 11](11-namespace-composer.md)); nó không phát hiện được code của bạn đang dùng cú pháp của
  8.5. Cách chắc chắn là dev bằng đúng bản của production (Docker giúp việc này, mục 3.3) và chạy test
  trên bản đó.

⚠️ PHP cài từ kho gói của bản phân phối Linux (Ubuntu, Debian...) do chính bản phân phối đóng gói.
Trang tải về của php.net ghi rõ các bản đó chứa bản vá riêng do bên đóng gói thêm vào, mà dự án PHP
không kiểm soát. Số phiên bản cũng có thể khác bản mới nhất trên php.net. Đừng đoán, hãy kiểm tra bằng
`php -v` (mục 3.6).

### 2.5 Kiểm tra phiên bản bên trong code

PHP có sẵn các hằng số (constant) cho biết bản đang chạy:

```php
<?php
declare(strict_types=1);

echo PHP_VERSION, "\n";            // in ra: 8.5.10     (chuỗi, tuỳ máy bạn)
echo PHP_MAJOR_VERSION, "\n";      // in ra: 8
echo PHP_MINOR_VERSION, "\n";      // in ra: 5
echo PHP_RELEASE_VERSION, "\n";    // in ra: 10
echo PHP_VERSION_ID, "\n";         // in ra: 80510      (số nguyên = major*10000 + minor*100 + patch)

var_dump(PHP_VERSION_ID >= 80400);                     // in ra: bool(true)
var_dump(version_compare(PHP_VERSION, '8.4.0', '>=')); // in ra: bool(true)
var_dump(version_compare('8.4.10', '8.4.9', '>'));     // in ra: bool(true)
var_dump('8.4.10' > '8.4.9');                          // in ra: bool(false)  ⚠️ sai!
```

Output trên là khi chạy bằng PHP 8.5.10; máy bạn sẽ in số khác. Dòng cuối là cạm bẫy: `'8.4.10'`
và `'8.4.9'` không phải chuỗi số (có hai dấu chấm), nên `>` so sánh chúng như chuỗi ký tự, từng ký tự
một: tới vị trí thứ năm, `'1'` nhỏ hơn `'9'`, nên kết quả là `false`. Muốn so phiên bản, dùng
`version_compare()` hoặc so `PHP_VERSION_ID` (là số nguyên).

## 3. Cài đặt PHP

Mục tiêu của mục này: gõ `php -v` trong terminal và thấy số phiên bản. Chọn một cách cài hợp với máy
bạn, không cần làm hết.

### 3.1 Chọn cách cài

Trang [Downloads & Installation Instructions](https://www.php.net/downloads.php) của php.net có sẵn
lệnh cài cho từng hệ điều hành. Tóm tắt các lựa chọn:

| Cách | Hợp với | Ưu điểm | Nhược điểm |
|---|---|---|---|
| Docker, image `php` | Mọi hệ điều hành có Docker | Không cài gì vào máy; đổi bản PHP bằng đổi tag; giống môi trường server | Lệnh dài hơn; cần hiểu chút về Docker |
| Homebrew | macOS | Có lệnh `php` dùng trực tiếp | Mỗi lúc chỉ một bản được "link" làm mặc định |
| Gói của bản phân phối (`apt`, `dnf`) | Linux, WSL | Có sẵn, cập nhật cùng hệ thống | Bản PHP do bản phân phối chọn, có thể cũ hơn |
| Bản build từ windows.php.net, hoặc `winget` | Windows | Bản build chính thức cho Windows | Phải tự thêm vào PATH, tự tạo `php.ini` |
| php.new hoặc Laravel Herd | Người học Laravel | Cài luôn Composer và Laravel installer | Công cụ của Laravel, không phải của dự án PHP |

macOS từng có sẵn PHP, nhưng theo manual, PHP không còn đi kèm từ macOS 12 (Monterey). Trên Mac đời
mới bạn phải tự cài.

### 3.2 macOS: Homebrew

[Homebrew](https://brew.sh) là trình quản lý gói phổ biến nhất trên macOS. Lệnh dưới lấy từ trang tải
của php.net, chạy trong Terminal:

```sh
# Cài Homebrew (bỏ qua nếu đã có)
curl -o- https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh | bash

# Cài và link PHP 8.5 (hiện php@8.5 là tên khác của formula "php", formula luôn theo bản mới nhất)
brew install php@8.5
brew link --force --overwrite php@8.5

php -v
```

Muốn dùng bản cũ hơn, cài formula có số phiên bản. Các formula này là *keg-only*: Homebrew cài nhưng
không tự đưa vào PATH, nên phải link thủ công:

```sh
brew install php@8.4
brew unlink php                          # bỏ link bản đang dùng
brew link --force --overwrite php@8.4    # đưa 8.4 thành lệnh "php" mặc định
php -v                                   # kiểm tra: phải thấy 8.4.x
```

Vài điều cần biết về PHP của Homebrew:

- File cấu hình nằm ở `$(brew --prefix)/etc/php/8.5/` (gồm `php.ini` và cấu hình PHP-FPM). Lệnh
  `brew --prefix` in ra thư mục cài Homebrew, mặc định là `/opt/homebrew` trên Mac dùng chip Apple.
- Formula cài kèm PHP-FPM; `brew services start php` chạy nó nền như một dịch vụ. Bạn chưa cần tới
  PHP-FPM ở chương này (xem [Chương 18](18-fpm-nginx-opcache.md)).
- php.net còn giới thiệu tap của bên thứ ba `shivammathur/php` (`brew install shivammathur/php/php@8.5`),
  tiện khi cần nhiều bản PHP khác nhau.

### 3.3 Docker: chạy PHP không cần cài

Nếu máy đã có Docker (Docker Desktop trên macOS, Windows), đây là cách sạch nhất: PHP nằm trong
container, xoá đi là máy sạch, muốn thử bản khác chỉ cần đổi tag. Image `php` trên Docker Hub là một
*Docker Official Image* (do cộng đồng Docker duy trì tại github.com/docker-library/php), và trang tải
của php.net cũng hướng dẫn dùng nó.

```sh
# Mở REPL tương tác của PHP 8.5 (mục 5)
docker run --rm -it php:8.5-cli php -a

# Chạy file hello.php trong thư mục hiện tại
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php hello.php

# Chạy cùng file đó bằng PHP 8.4: chỉ đổi tag
docker run --rm -v "$PWD":/app -w /app php:8.4-cli php hello.php
```

Giải thích các tham số:

| Tham số | Ý nghĩa |
|---|---|
| `--rm` | Xoá container khi chạy xong, không để rác |
| `-it` | `-i` giữ stdin mở, `-t` cấp một terminal. Bắt buộc khi cần gõ phím vào chương trình (REPL) |
| `-v "$PWD":/app` | Gắn (mount) thư mục hiện tại của máy bạn vào `/app` trong container, để PHP đọc được file của bạn |
| `-w /app` | Đặt thư mục làm việc trong container là `/app` |
| `php:8.5-cli` | Tên image `php`, tag `8.5-cli` |
| `php hello.php` | Lệnh chạy bên trong container |

Image `php:8.5-cli` có lệnh mặc định là `php -a`, nên `docker run --rm -it php:8.5-cli` (không ghi
lệnh) cũng mở REPL. Các lệnh trên viết cho shell kiểu Unix (Terminal macOS, Linux, WSL); trên
PowerShell cách viết đường dẫn ở `-v` có thể khác.

Tag của image cho biết bản PHP và *biến thể* (variant):

| Tag (ví dụ) | Chứa gì | Dùng khi |
|---|---|---|
| `php:8.5-cli` | PHP CLI | Chạy script, học, chạy công cụ dòng lệnh |
| `php:8.5-fpm` | PHP-FPM (cần Nginx hoặc web server khác đứng trước) | Chạy ứng dụng web trên production ([Chương 18](18-fpm-nginx-opcache.md)) |
| `php:8.5-apache` | Apache kèm PHP dạng module | Ứng dụng web đơn giản, một container |
| `php:8.5-zts` | Bản build thread-safe (ZTS) | Trường hợp đặc biệt cần chạy PHP đa luồng |
| `php:8.5-cli-alpine`, `php:8.5-fpm-alpine` | Như trên nhưng nền Alpine Linux | Cần image nhỏ; Alpine dùng thư viện C musl thay vì glibc nên đôi khi gặp lỗi tương thích |

Mọi biến thể đều có lệnh `php` CLI. Mặc định image dựa trên Debian; tag có đuôi `-trixie`,
`-bookworm` chỉ rõ bản Debian. Tag `8.5` luôn trỏ tới bản 8.5.x mới nhất; muốn cố định tuyệt đối
thì ghi đủ, ví dụ `8.5.11-cli`.

⚠️ Đừng dùng tag `latest` (hoặc không ghi tag) trong dự án thật: tag này tự nhảy sang bản minor mới
khi bản đó ra mắt, và code của bạn có thể đổi hành vi mà không ai sửa gì.

⚠️ Image `php` không có file `php.ini`, chỉ có hai file mẫu `php.ini-development` và
`php.ini-production` trong `/usr/local/etc/php/`. Image cũng không có sẵn mọi extension (ví dụ chưa
có `pdo_mysql`); cách thêm extension ở mục 9.4.

### 3.4 Linux và WSL: gói của bản phân phối

Trên Debian, Ubuntu (kể cả Ubuntu chạy trong WSL của Windows):

```sh
sudo apt update
sudo apt install -y php-cli      # chỉ cài PHP dòng lệnh
php -v
```

⚠️ Trang php.net ghi lệnh `sudo apt install -y php`. Hãy biết gói `php` của Debian chỉ trỏ tới gói
của bản mặc định (ví dụ `php8.4`), và gói đó là gói tổng (*metapackage*) đòi một trong ba thứ: module
PHP cho Apache, PHP-FPM hoặc PHP-CGI. Nếu máy chưa có cái nào, apt chọn cái đầu tiên là module cho
Apache, và với cấu hình mặc định apt cài luôn cả Apache.
Nếu chỉ cần dòng lệnh, cài `php-cli` như trên.

Fedora: `sudo dnf install -y php`.

Bản PHP cài theo cách này là bản mặc định của bản phân phối. Muốn bản mới hơn, trang php.net hướng dẫn
thêm kho của bên thứ ba (`ppa:ondrej/php` trên Ubuntu, `packages.sury.org` trên Debian) rồi cài
`php8.5`. php.net cảnh báo rõ: các bản này do bên thứ ba build, có bản vá mà dự án PHP không kiểm soát,
và nhà cung cấp này thêm một bản vá gửi dữ liệu thống kê (telemetry) vào module Apache 2 và PHP-FPM.
Hãy đọc cảnh báo đó trước khi dùng cho production.

Trên Debian, Ubuntu, mỗi SAPI có thư mục cấu hình riêng: `/etc/php/8.4/cli/php.ini` cho dòng lệnh,
`/etc/php/8.4/fpm/php.ini` cho PHP-FPM (số `8.4` đổi theo bản đang cài). Điều này quan trọng ở mục 8.

### 3.5 Windows

Có ba hướng, xếp từ dễ tới khó:

1. Dùng WSL (Ubuntu chạy trong Windows) rồi cài như mục 3.4, hoặc dùng Docker Desktop như mục 3.3.
   Môi trường giống server Linux nhất.
2. `winget install PHP.PHP.8.5` (lệnh trên trang php.net, cài bản thread-safe), hoặc dùng Scoop,
   Chocolatey, hoặc lệnh PowerShell một dòng trên trang tải của php.net.
3. Tự cài bản build chính thức từ [windows.php.net/download](https://windows.php.net/download/):
   - Chọn bản `x64`. Manual ghi PHP trên Windows chỉ có bản x86 (32-bit) và x64, chưa chạy trên
     Windows on ARM.
   - Chọn *Non Thread Safe* (NTS) nếu chỉ chạy dòng lệnh hoặc chạy sau FastCGI (như IIS); chọn *Thread
     Safe* (TS) nếu nạp PHP làm module của Apache. Đây là hướng dẫn trên chính trang tải bản Windows
     của php.net.
   - Cần Microsoft Visual C++ Redistributable (bản x64 cho PHP x64).
   - Giải nén vào một thư mục, ví dụ `C:\php`, thêm thư mục đó vào biến môi trường `PATH`, rồi chép
     `php.ini-development` thành `php.ini` trong cùng thư mục.

Người học Laravel còn có thể dùng [php.new](https://php.new) (cài PHP, Composer và Laravel installer
bằng một lệnh, có cho macOS, Windows, Linux) hoặc [Laravel Herd](https://herd.laravel.com) (ứng dụng có
giao diện cho macOS, Windows, kèm PHP và Nginx). Cả hai được giới thiệu trong
[tài liệu cài đặt của Laravel](https://laravel.com/docs/13.x/installation).

### 3.6 Kiểm tra cài đặt

Mở terminal mới (để PATH được nạp lại) và gõ:

```sh
php -v
```

Ví dụ output trên một máy chạy PHP 8.5.10:

```
PHP 8.5.10 (cli) (built: Aug 27 2026 21:50:54) (NTS)
Copyright (c) The PHP Group
Zend Engine v4.5.10, Copyright (c) Zend Technologies
    with Zend OPcache v8.5.10, Copyright (c), by Zend Technologies
```

Đọc từng phần:

| Phần | Ý nghĩa |
|---|---|
| `PHP 8.5.10` | Phiên bản |
| `(cli)` | PHP đang chạy ở chế độ dòng lệnh. Tên kỹ thuật là *SAPI* (Server API) `cli`; PHP-FPM là một SAPI khác. Xem [Chương 02](02-php-chay-nhu-the-nao.md) |
| `(built: ...)` | Thời điểm bản PHP này được biên dịch |
| `(NTS)` | Bản build *Non Thread Safe*. Bản thread-safe ghi `ZTS` (Zend Thread Safety) |
| `Zend Engine v4.5.10` | Phiên bản lõi Zend Engine đi kèm |
| `with Zend OPcache ...` | Extension OPcache đang được nạp. Từ PHP 8.5, OPcache luôn được build sẵn trong PHP |

Tuỳ cách cài, có thể có thêm dòng `Built by ...` cho biết ai đóng gói bản PHP đó.

⚠️ Một máy có thể có nhiều bản PHP cùng lúc (Homebrew, Herd, bản cài tay...). Lệnh `php` bạn gõ là bản
nào phụ thuộc thứ tự thư mục trong PATH. Kiểm tra:

```sh
which php       # macOS, Linux: đường dẫn của lệnh php sẽ chạy
which -a php    # liệt kê mọi lệnh php tìm thấy trong PATH, theo thứ tự ưu tiên
where php       # Windows (cmd)
```

Nếu `php -v` báo một bản còn editor của bạn (VS Code, PhpStorm) hoặc Composer báo bản khác, nguyên nhân
thường là chúng đang dùng hai file `php` khác nhau.

Không muốn cài gì mà chỉ muốn thử một đoạn code? Trang [3v4l.org](https://3v4l.org) chạy đoạn code
trên rất nhiều phiên bản PHP cùng lúc, rất tiện để xem một hành vi thay đổi qua các bản.

## 4. Chạy chương trình đầu tiên bằng dòng lệnh

PHP có thể chạy trong web server hoặc chạy thẳng từ terminal. Cách thứ hai đơn giản hơn nhiều để bắt
đầu: không cần web server, không cần trình duyệt. Chế độ này gọi là *CLI* (Command Line Interface).

### 4.1 Hello world

Tạo một thư mục học tập và file `hello.php` trong đó:

```php
<?php
declare(strict_types=1);

echo "Xin chào, PHP!\n";
```

Chạy (trong terminal, ở đúng thư mục chứa file):

```sh
php hello.php
# in ra: Xin chào, PHP!
```

Dùng Docker thì: `docker run --rm -v "$PWD":/app -w /app php:8.5-cli php hello.php`.

Giải thích từng dòng:

- `<?php` là *thẻ mở* (opening tag): từ đây trở đi là mã PHP. Mục 7 nói kỹ về cấu trúc file.
- `declare(strict_types=1);` bật chế độ kiểm tra kiểu chặt cho file này. Giáo trình luôn bật nó; ý
  nghĩa chi tiết ở [Chương 04](04-kieu-du-lieu.md).
- `echo` in một giá trị ra output. `"\n"` là ký tự xuống dòng. Mỗi câu lệnh kết thúc bằng dấu `;`.

Khi bạn gõ `php hello.php`, chương trình `php` đọc file, dịch sang opcode, chạy, in kết quả ra
terminal, rồi thoát. Lần chạy sau bắt đầu lại từ đầu, không nhớ gì của lần trước. Chuyện gì diễn ra bên
trong ở [Chương 02](02-php-chay-nhu-the-nao.md).

### 4.2 Ba cách đưa code cho PHP

Manual liệt kê ba cách, không kết hợp được với nhau:

```sh
# 1. Chạy một file (có hay không có -f đều được; file không bắt buộc đuôi .php)
php hello.php
php -f hello.php

# 2. Chạy code viết thẳng trên dòng lệnh với -r (KHÔNG có thẻ <?php)
php -r 'echo 2 ** 10, PHP_EOL;'
# in ra: 1024

# 3. Đưa code qua standard input (stdin)
echo '<?php echo "chạy từ stdin\n";' | php
# in ra: chạy từ stdin
```

`PHP_EOL` là hằng số chứa ký tự xuống dòng của hệ điều hành đang chạy (`"\n"` trên Linux, macOS).

⚠️ Với `-r`, luôn bọc code trong nháy đơn `'...'`. Trong nháy kép, shell (bash, zsh) tự thay `$ten`
bằng biến của shell trước khi PHP nhìn thấy:

```sh
php -r "\$x = 5; echo \$x;"    # chạy được nhưng phải escape từng dấu $, dễ sai
php -r "$x = 5; echo $x;"      # shell biến $x thành rỗng, PHP nhận " = 5; echo ;" → Parse error
php -r '$x = 5; echo $x;'      # đúng: nháy đơn, shell không đụng vào
```

### 4.3 Đối số dòng lệnh: `$argv` và `$argc`

Script CLI nhận đối số (argument) giống mọi lệnh khác. PHP đặt chúng vào hai biến có sẵn:

- `$argv`: mảng các đối số. Phần tử `[0]` luôn là tên script như lúc được gọi.
- `$argc`: số phần tử của `$argv` (tính cả tên script).

File `args.php`:

```php
<?php
declare(strict_types=1);

echo 'Số phần tử $argc: ', $argc, "\n";
var_dump($argv);
```

```sh
php args.php An 30 --vip
```

Output:

```
Số phần tử $argc: 4
array(4) {
  [0]=>
  string(8) "args.php"
  [1]=>
  string(2) "An"
  [2]=>
  string(2) "30"
  [3]=>
  string(5) "--vip"
}
```

Ba điều cần để ý:

1. Mọi đối số đều là chuỗi: `"30"` là `string(2) "30"`, không phải số. Muốn dùng như số phải tự chuyển
   và kiểm tra (xem [Chương 04](04-kieu-du-lieu.md)).
2. Mọi thứ đứng sau tên file được chuyển nguyên cho script, kể cả thứ trông như tùy chọn của PHP
   (`--vip`, `-h`).
3. Khi chạy bằng `-r`, `$argv[0]` là chuỗi `"Standard input code"`, và muốn truyền đối số bắt đầu bằng
   `-` thì phải đặt `--` trước, nếu không PHP tưởng đó là tùy chọn của chính nó:
   `php -r 'var_dump($argv);' -- -h`.

Script thật thường cần tùy chọn kiểu `--limit=10`. PHP có hàm `getopt()` cho việc này, còn các
framework có sẵn bộ khung viết lệnh CLI (Laravel có Artisan, xem [Chương 23](23-laravel-gioi-thieu.md)).

### 4.4 Nhập, xuất và mã thoát

Một chương trình dòng lệnh làm việc với ba *luồng* (stream) chuẩn của hệ điều hành:

```
             ┌──────────────────────┐
 bàn phím ──►│ STDIN       script   │──► STDOUT ──► màn hình (hoặc file, nếu chuyển hướng >)
 hoặc pipe   │             PHP      │──► STDERR ──► màn hình (thông báo lỗi, chuyển hướng bằng 2>)
             └──────────┬───────────┘
                        └──► mã thoát (exit code): 0 = thành công, khác 0 = thất bại
```

PHP CLI có sẵn ba hằng số `STDIN`, `STDOUT`, `STDERR` là các luồng đã mở sẵn. `echo` ghi vào STDOUT.
Thông báo lỗi nên ghi vào STDERR để người dùng chuyển hướng output mà vẫn thấy lỗi.

File `chao.php`:

```php
#!/usr/bin/env php
<?php
declare(strict_types=1);

// Đọc tên từ đối số dòng lệnh; nếu không có thì hỏi qua bàn phím (STDIN)
$ten = $argv[1] ?? null;

if ($ten === null) {
    echo 'Bạn tên gì? ';
    $dong = fgets(STDIN);               // đọc một dòng, false nếu hết input
    $ten = $dong === false ? '' : trim($dong);
}

if ($ten === '') {
    fwrite(STDERR, "Lỗi: chưa nhập tên\n");   // thông báo lỗi ghi ra STDERR
    exit(1);                                 // mã thoát khác 0 = thất bại
}

echo "Xin chào, {$ten}!\n";
```

`$argv[1] ?? null` nghĩa là "lấy `$argv[1]`, nếu không tồn tại thì lấy `null`" (toán tử `??` ở
[Chương 07](07-toan-tu-dieu-khien.md)). Chạy thử:

```sh
php chao.php An
# in ra: Xin chào, An!

echo "Bình" | php chao.php
# in ra: Bạn tên gì? Xin chào, Bình!

php chao.php < /dev/null       # stdin rỗng: fgets trả về false
# màn hình hiện: Bạn tên gì? Lỗi: chưa nhập tên   (phần "Lỗi..." đi qua STDERR)
echo $?                        # xem mã thoát của lệnh vừa chạy
# in ra: 1

php chao.php < /dev/null 2>/dev/null   # bỏ STDERR đi: chỉ còn "Bạn tên gì?"
```

Mã thoát (exit code) là con số chương trình trả về cho hệ điều hành khi kết thúc. Shell, hệ thống CI,
Docker, Supervisor đều nhìn con số này để biết lệnh thành công hay thất bại; `cmd1 && cmd2` chỉ chạy
`cmd2` khi `cmd1` trả về 0. Quy tắc của PHP theo manual hàm `exit()`:

| Cách kết thúc | Mã thoát |
|---|---|
| Chạy hết script, không lỗi | 0 |
| `exit(0)` hoặc `exit()` | 0 |
| `exit(1)` ... `exit(254)` | Đúng số đó. Manual khuyên dùng 0 tới 254 |
| Fatal error, exception không được bắt, lỗi cú pháp | 255 (PHP giữ số này cho riêng mình) |
| `exit("thông báo")` | In chuỗi ra rồi thoát với mã 0 |

⚠️ Dòng cuối là cái bẫy: `exit("Không kết nối được database")` in ra thông báo nhưng trả về 0, nên
CI hay script gọi nó tưởng là thành công. Khi báo lỗi, ghi thông báo ra STDERR rồi `exit(1)` như ví dụ
trên.

### 4.5 Biến script thành một lệnh: dòng shebang

Dòng đầu tiên `#!/usr/bin/env php` của `chao.php` gọi là *shebang*. Trên macOS, Linux, nó cho hệ điều
hành biết dùng chương trình nào để chạy file. Khi đó bạn chạy script như một lệnh bình thường:

```sh
chmod +x chao.php     # cấp quyền thực thi (làm một lần)
./chao.php An
# in ra: Xin chào, An!
```

`/usr/bin/env php` nghĩa là "tìm lệnh `php` trong PATH", nên script chạy được dù PHP cài ở đâu. PHP CLI
bỏ qua dòng đầu nếu nó bắt đầu bằng `#!`, nên dòng này không bị in ra. Chạy `php chao.php` vẫn bình
thường. Composer, Artisan của Laravel đều là script PHP có shebang.

### 4.6 Các tùy chọn hay dùng của lệnh `php`

`php -h` in toàn bộ danh sách. Những tùy chọn bạn sẽ dùng thường xuyên:

| Tùy chọn | Làm gì | Chi tiết |
|---|---|---|
| `-v` | In phiên bản | Mục 3.6 |
| `-r '<code>'` | Chạy code trên dòng lệnh | Mục 4.2 |
| `-l file.php` | Kiểm tra cú pháp (lint), không chạy | Ngay dưới |
| `-a` | Mở REPL tương tác | Mục 5 |
| `-S host:port` | Chạy web server dựng sẵn | Mục 6 |
| `-i` | In toàn bộ thông tin cấu hình (như `phpinfo()`) | Mục 8 |
| `--ini` | In đường dẫn các file `php.ini` đang dùng | Mục 8 |
| `--ini=diff` | In các cấu hình khác giá trị mặc định (từ PHP 8.5) | Mục 8 |
| `-d key=value` | Đặt một cấu hình cho lần chạy này | Mục 8 |
| `-c path` | Dùng file `php.ini` (hoặc thư mục chứa nó) chỉ định | Mục 8 |
| `-n` | Không đọc file `php.ini` nào | Mục 8 |
| `-m` | Liệt kê extension đang nạp | Mục 9 |
| `--rf <hàm>`, `--rc <class>`, `--re <extension>`, `--ri <extension>` | Xem thông tin hàm, class, extension | Ngay dưới |

`php -l` (lint) kiểm tra lỗi cú pháp mà không chạy code, hay dùng trong CI hoặc git hook:

```sh
php -l hello.php
# in ra: No syntax errors detected in hello.php
```

Với file `loi.php` quên dấu `;` ở dòng 4:

```php
<?php
declare(strict_types=1);

echo "thiếu dấu chấm phẩy"
echo "dòng sau\n";
```

```
$ php -l loi.php

Parse error: syntax error, unexpected token "echo", expecting "," or ";" in loi.php on line 5
Errors parsing loi.php
```

Mã thoát khi lint thất bại là 255. Để ý PHP báo lỗi ở dòng 5, dòng chứa token "bất ngờ", chứ không phải
dòng 4 nơi thật sự thiếu `;`. Khi gặp lỗi cú pháp, hãy nhìn cả dòng ngay trước dòng được báo.

Nếu cấu hình bật `log_errors` mà không đặt `error_log` (file `php.ini-development` mà Homebrew dùng
làm `php.ini` có bật `log_errors`), bạn sẽ thấy thông báo lỗi hai lần: một dòng `PHP Parse error: ...`
ghi vào STDERR (bản "log") và một dòng `Parse error: ...` ghi vào STDOUT (bản "display"). Không phải
hai lỗi khác nhau. Các chỉ thị này được giải thích ở [Chương 12](12-loi-exception.md).

⚠️ `php -l` chỉ bắt lỗi cú pháp. Gọi một hàm không tồn tại vẫn qua lint ("No syntax errors detected")
và chỉ lộ ra khi chạy (`Fatal error: Uncaught Error: Call to undefined function ...`). Những lỗi kiểu
này cần công cụ phân tích tĩnh như PHPStan ([Chương 21](21-chat-luong-code.md)). Từ PHP 8.3, `-l` nhận
nhiều file một lần.

`--rf` cho xem nhanh chữ ký của một hàm có sẵn mà không cần mở manual:

```
$ php --rf str_contains
Function [ <internal:standard> function str_contains ] {

  - Parameters [2] {
    Parameter #0 [ <required> string $haystack ]
    Parameter #1 [ <required> string $needle ]
  }
  - Return [ bool ]
}
```

### 4.7 CLI khác chạy trên web ở chỗ nào

Cùng một ngôn ngữ, nhưng PHP CLI có vài khác biệt quan trọng so với PHP chạy sau web server (manual,
trang [Differences from other SAPIs](https://www.php.net/manual/en/features.commandline.differences.php)):

| Điểm | CLI | Trên web (ví dụ PHP-FPM) |
|---|---|---|
| `max_execution_time` | Luôn là `0` (không giới hạn) | Mặc định 30 giây |
| `html_errors` | `false`: thông báo lỗi là text thuần | Theo `php.ini` |
| `implicit_flush` | `true`: `echo` hiện ra ngay | Theo `php.ini` |
| `$argv`, `$argc` | Luôn có. Tới PHP 8.4 là nhờ CLI ép `register_argc_argv` thành `true`; từ 8.5 CLI tự tạo hai biến này mà không cần chỉ thị đó (`ini_get('register_argc_argv')` trả `"0"`) | Theo `register_argc_argv` trong `php.ini` |
| HTTP header | Không gửi header nào | Gửi header HTTP trước nội dung |
| Thư mục làm việc | Thư mục nơi bạn gõ lệnh, không đổi sang thư mục của script | Tùy SAPI |
| `PHP_SAPI` / `php_sapi_name()` | `"cli"` | Ví dụ `"fpm-fcgi"` với PHP-FPM, `"cli-server"` với `php -S` |

Ba chỉ thị đầu bảng bị CLI ép cứng sau khi đọc `php.ini`, nên ghi `max_execution_time = 5` vào `php.ini`
không có tác dụng với CLI (đã thử: `ini_get('max_execution_time')` vẫn trả `"0"`); đổi lúc chạy bằng
`-d max_execution_time=5` hoặc `ini_set()` thì được.

⚠️ Đường dẫn tương đối trong CLI tính từ thư mục làm việc, không phải thư mục chứa script. Với cấu trúc
`proj/scripts/where.php`:

```php
<?php
declare(strict_types=1);

echo getcwd(), "\n";   // thư mục làm việc hiện tại
echo __DIR__, "\n";    // thư mục chứa file này
```

```sh
cd proj && php scripts/where.php
# in ra: /.../proj
#        /.../proj/scripts
```

Nếu script đọc `file_get_contents('data.csv')`, file được tìm trong `proj/`, không phải
`proj/scripts/`. Muốn đường dẫn ổn định, ghép từ `__DIR__`: `__DIR__ . '/data.csv'` (`__DIR__` là
*magic constant*, xem [Chương 03](03-cu-phap-bien-hang.md)).

Khác biệt sâu hơn giữa các SAPI và vòng đời một request trên web là nội dung của
[Chương 02](02-php-chay-nhu-the-nao.md).

## 5. Thử nhanh với REPL: `php -a`

### 5.1 REPL là gì

*REPL* (Read-Eval-Print Loop) là chế độ gõ từng dòng code và thấy kết quả ngay, không cần tạo file.
PHP gọi nó là *interactive shell*, mở bằng `php -a`:

```
$ php -a
Interactive shell

php > echo 5 + 8;
13
php > $gia = 120000;
php > $soLuong = 3;
php > echo $gia * $soLuong;
360000
php > var_dump(intdiv(7, 2));
int(3)
php > function tang(int $n): int
php > {
php {     return $n + 1;
php { }
php > echo tang(41);
42
php > exit
```

(Phiên trên là minh hoạ, dựng theo manual và mã nguồn của shell; các phép tính là kết quả đúng của PHP.)

Những điều cần biết khi dùng:

- Mỗi câu lệnh phải kết thúc bằng `;`. Nếu quên, shell không báo lỗi mà im lặng chờ bạn gõ tiếp (dấu
  nhắc vẫn là `php >`). Gõ `;` ở dòng tiếp theo là xong.
- Shell không tự in giá trị của biểu thức. Gõ `5 + 8;` sẽ không thấy gì; phải `echo` hoặc `var_dump()`.
- Khi đang ở trong khối `{ ... }` chưa đóng, dấu nhắc đổi thành `php {`; trong ngoặc `(` chưa đóng
  là `php (`. Nhìn dấu nhắc để biết shell đang chờ gì.
- Biến và hàm đã khai báo còn sống tới khi thoát shell. Thoát bằng `exit`, `quit` hoặc Ctrl+D.
- Phím Tab gợi ý tên hàm, hằng, class, biến; phím mũi tên lên, xuống gọi lại lệnh cũ. Lịch sử lưu ở
  `~/.php_history`; từ PHP 8.4 đổi được đường dẫn bằng biến môi trường `PHP_HISTFILE`.
- Đổi cấu hình ngay trong shell bằng cú pháp `#tên=giá trị`, ví dụ `#cli.prompt=>>> ` đổi dấu nhắc.

### 5.2 Khi `php -a` không chạy

Shell tương tác cần extension `readline`. Từ PHP 8.1, nếu bản PHP của bạn không có `readline`, lệnh
`php -a` dừng ngay với thông báo:

```
Interactive shell (-a) requires the readline extension.
```

(Trước 8.1, PHP rơi vào một "interactive mode" khác: đọc cả đoạn code từ bàn phím tới khi bấm Ctrl+D
rồi mới chạy, dễ làm người mới tưởng bị treo.) Bản PHP của Homebrew, của Debian/Ubuntu (gói
`php8.x-readline` được cài kèm `php8.x-cli`) và image Docker `php` đều có `readline`. Với Docker nhớ
có `-it`, nếu không bạn không gõ được gì vào shell.

### 5.3 REPL tốt hơn: PsySH và Tinker

`php -a` khá thô. *PsySH* là một REPL viết bằng PHP, cài qua Composer, tự in giá trị biểu thức, có
lệnh xem tài liệu và mã nguồn. Laravel có sẵn `php artisan tinker`, chính là PsySH đã nạp sẵn ứng dụng
Laravel của bạn ([tài liệu Artisan](https://laravel.com/docs/13.x/artisan#tinker)). Bạn sẽ dùng Tinker
rất nhiều từ phần Laravel.

Lời khuyên: REPL để thử nhanh một hàm hay một phép so sánh. Hễ đoạn thử dài hơn vài dòng, viết ra file
rồi chạy `php file.php`: sửa dễ hơn, chạy lại được, và không mất khi thoát shell.

## 6. Web server dựng sẵn: `php -S`

Muốn xem PHP trả trang web cho trình duyệt mà chưa muốn cài Nginx hay Apache, dùng web server có sẵn
trong PHP CLI.

### 6.1 Trang web PHP đầu tiên

Tạo thư mục `web/` và file `web/index.php`:

```php
<?php
declare(strict_types=1);

$ten = $_GET['ten'] ?? 'bạn';   // đọc tham số ?ten=... trên URL, không có thì dùng 'bạn'
$ten = is_string($ten) ? $ten : 'bạn';   // ?ten[]=x sẽ gửi lên một mảng: loại bỏ
$gio = date('H:i');
?>
<!DOCTYPE html>
<html lang="vi">
<head><meta charset="utf-8"><title>Trang PHP đầu tiên</title></head>
<body>
    <h1>Xin chào, <?= htmlspecialchars($ten) ?>!</h1>
    <p>Bây giờ là <?= $gio ?> theo đồng hồ của PHP.</p>
    <p>SAPI: <?= PHP_SAPI ?></p>
</body>
</html>
```

Chạy server trong thư mục `web/`:

```sh
cd web
php -S localhost:8000
```

Mở trình duyệt tới `http://localhost:8000/?ten=An`. Trang hiện "Xin chào, An!", giờ hiện tại và dòng
"SAPI: cli-server". Terminal chạy server in log của từng request, đại loại như sau (output minh hoạ:
thời gian, số cổng phía trình duyệt sẽ khác):

```
[Sat Oct  3 14:05:12 2026] PHP 8.5.11 Development Server (http://localhost:8000) started
[Sat Oct  3 14:05:20 2026] [::1]:51234 Accepted
[Sat Oct  3 14:05:20 2026] [::1]:51234 [200]: GET /?ten=An
[Sat Oct  3 14:05:20 2026] [::1]:51234 Closing
```

Bấm Ctrl+C để tắt server. Vài điểm đáng chú ý trong ví dụ:

- `$_GET` chứa tham số trên URL. Đây là một *superglobal*; dữ liệu request được bàn kỹ ở
  [Chương 15](15-php-va-web.md).
- `htmlspecialchars()` biến các ký tự đặc biệt của HTML (`<`, `>`, `"`...) thành dạng an toàn. Thử
  bỏ nó đi rồi mở `?ten=<b>An</b>`: chữ An bị in đậm, tức là người dùng đã chèn được HTML vào trang
  của bạn. Đó là mầm mống của lỗi bảo mật XSS ([Chương 17](17-bao-mat.md)). Tập thói quen escape mọi
  dữ liệu người dùng khi in ra HTML ngay từ bây giờ.
- Giờ hiện ra rất có thể lệch 7 tiếng so với giờ Việt Nam. Lý do: cấu hình `date.timezone` mặc định là
  `"UTC"`. Mục 8 chỉ cách sửa.
- Dòng `?>` ngay trước `<!DOCTYPE html>` đóng chế độ PHP; từ đó trở đi là HTML được chép nguyên ra
  output (mục 1.2).

Nếu chạy trong Docker, phải mở cổng và cho server nghe trên mọi địa chỉ của container:

```sh
docker run --rm -it -p 8000:8000 -v "$PWD":/app -w /app php:8.5-cli php -S 0.0.0.0:8000
```

⚠️ `localhost` bên trong container là chính container, nên `php -S localhost:8000` trong container thì
trình duyệt trên máy bạn không vào được. Phải dùng `0.0.0.0` và `-p 8000:8000`.

### 6.2 Document root, file index và router script

*Document root* là thư mục gốc mà server lấy file để trả về. Mặc định là thư mục bạn đứng khi gõ lệnh;
đổi bằng `-t`. Ứng dụng Laravel đặt điểm vào ở thư mục `public/`, nên sẽ chạy kiểu
`php -S localhost:8000 -t public`.

Server xử lý một URL như sau (theo manual):

```
GET /duong/dan
   │
   ├── có router script? ──có──► chạy router.php
   │                              ├── router trả về false ──► xử lý tiếp như khi không có router
   │                              └── ngược lại ────────────► output của router là response
   │
   └── không có router:
         ├── URL trỏ tới file có thật ──► file .php thì chạy, file khác thì gửi nguyên
         ├── URL là thư mục / không chỉ ra file ──► tìm index.php hoặc index.html,
         │        không thấy thì tìm tiếp ở thư mục cha, tới document root
         └── không tìm được gì ──► 404
```

*Router script* là file PHP truyền vào cuối lệnh. Nó chạy ở đầu mọi request, nên dùng để thử ý tưởng
"một file nhận mọi request" (*front controller*), đúng cách các framework làm:

```php
<?php
// router.php: chạy cho MỌI request khi khởi động bằng: php -S localhost:8000 router.php
declare(strict_types=1);

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

// Ảnh, CSS, JS: trả false để server tự gửi file tĩnh như bình thường
if (is_string($path) && preg_match('/\.(?:png|jpe?g|gif|css|js)$/', $path) === 1) {
    return false;
}

// Mọi đường dẫn khác: router tự trả lời bằng JSON
header('Content-Type: application/json');
echo json_encode([
    'method' => $_SERVER['REQUEST_METHOD'],
    'path'   => $path,
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), "\n";
```

```sh
php -S localhost:8000 router.php
# Ở terminal khác (để URL trong nháy đơn: zsh coi dấu ? là ký tự đại diện của tên file):
curl 'http://localhost:8000/api/don-hang?trang=2'
# in ra: {"method":"GET","path":"/api/don-hang"}
```

`php artisan serve` của Laravel chính là chạy `php -S` với một router script của Laravel.

### 6.3 Giới hạn: chỉ dùng khi phát triển

Manual cảnh báo rõ: server này để hỗ trợ phát triển và thử nghiệm, không phải web server đầy đủ, và
không được dùng trên mạng công cộng.

- Mặc định chỉ có một process đơn luồng: một request chậm (ví dụ `sleep(10)`) làm mọi request khác phải
  chờ. Từ PHP 7.4 có thể chạy nhiều worker bằng biến môi trường `PHP_CLI_SERVER_WORKERS` (không hỗ trợ
  trên Windows); manual ghi đây là tính năng thử nghiệm, không dành cho production.
- `php -S 0.0.0.0:8000` cho máy khác trong mạng truy cập vào. Chỉ làm vậy trong mạng tin cậy.
- Trên production, PHP chạy bằng PHP-FPM sau Nginx ([Chương 18](18-fpm-nginx-opcache.md)). Code của bạn
  muốn biết mình đang chạy dưới server dựng sẵn thì kiểm tra `PHP_SAPI === 'cli-server'`.

## 7. Cấu trúc một file PHP

Mục này trả lời: một file `.php` "chuẩn" trông thế nào, và vì sao lại như vậy. Chi tiết về thẻ PHP,
comment, câu lệnh nằm ở [Chương 03](03-cu-phap-bien-hang.md); ở đây chỉ nói những gì quyết định hình
dạng của cả file.

### 7.1 Hai kiểu file

| Kiểu | Nội dung | Ví dụ |
|---|---|---|
| File PHP thuần | Chỉ có code PHP: class, hàm, script | Gần như mọi file trong một dự án Laravel |
| File template (view) | HTML là chính, xen các đoạn `<?php ... ?>` hoặc `<?= ... ?>` để điền dữ liệu | `trang.php` ở mục 1.2, `web/index.php` ở mục 6.1 |

Hai kiểu tuân theo quy tắc hơi khác nhau, như các mục dưới đây cho thấy.

### 7.2 Khung chuẩn của một file PHP thuần

Ví dụ `tinh-tien.php`, sắp xếp đúng thứ tự mà chuẩn PSR-12 quy định:

```php
<?php

declare(strict_types=1);

namespace HocPhp\Chuong01;

use InvalidArgumentException;

function tongTien(int $donGia, int $soLuong): int
{
    if ($soLuong < 0) {
        throw new InvalidArgumentException('Số lượng không được âm');
    }

    return $donGia * $soLuong;
}

echo tongTien(120000, 3), "\n";   // in ra: 360000
```

Đọc từ trên xuống:

```
<?php                           ← thẻ mở, đứng riêng ở dòng 1

declare(strict_types=1);        ← câu lệnh ĐẦU TIÊN của file (mục 7.4)

namespace HocPhp\Chuong01;      ← "họ" của các tên khai báo trong file (Chương 11)

use InvalidArgumentException;   ← nhập tên từ namespace khác

function ... / class ...        ← phần code chính
...
                                ← hết file: KHÔNG có ?> (mục 7.3), kết thúc bằng một ký tự xuống dòng
```

Mỗi khối cách nhau một dòng trống. Bạn chưa cần hiểu `namespace`, `use`, `throw`; chúng có chương riêng.
Điều cần nhớ bây giờ là thứ tự: thẻ mở, `declare`, `namespace`, `use`, rồi tới code.

Chuẩn PSR-1 còn khuyên một file hoặc chỉ *khai báo* (class, hàm, hằng), hoặc chỉ *làm việc có tác dụng
phụ* (in output, đổi cấu hình...), không làm cả hai. File ví dụ trên vừa khai báo hàm vừa `echo` để
gọn cho bài học; trong dự án thật, hàm nằm một file, đoạn gọi hàm nằm file khác.

### 7.3 Thẻ đóng `?>` và vì sao file PHP thuần nên bỏ nó

Ba sự thật về thẻ, theo manual:

1. Sau `<?php` phải có một khoảng trắng (dấu cách, tab hoặc xuống dòng). Viết dính như `<?phpecho`
   thì PHP không nhận ra thẻ mở: tùy cấu hình `short_open_tag`, bạn gặp lỗi cú pháp hoặc cả đoạn bị in
   ra như văn bản thường.
2. Thẻ đóng `?>` tự ngầm có một dấu `;`, và nó "nuốt" luôn một ký tự xuống dòng đứng ngay sau nó.
3. Mọi thứ nằm ngoài cặp thẻ, kể cả một dấu cách hay một dòng trống, đều được in ra output.

Thử điểm 2 với file `nl2.php`:

```php
<?php echo "Xin"; ?>
chào
<?php echo "các"; ?>
bạn
```

Output:

```
Xinchào
cácbạn
```

Ký tự xuống dòng ngay sau mỗi `?>` biến mất, nên "Xin" dính liền "chào". Cơ chế này giúp template
không bị thừa dòng trống, nhưng kết hợp với điểm 3 nó sinh ra một lỗi kinh điển. Xem hai file:

```php
<?php
// config.php: file chỉ có code PHP nhưng lỡ có thẻ đóng và dòng trống phía sau
$cauHinh = ['debug' => true];
?>

```

```php
<?php
declare(strict_types=1);

require __DIR__ . '/config.php';

header('Content-Type: application/json');   // gửi header SAU khi đã lỡ có output
echo json_encode($cauHinh), "\n";
```

`config.php` kết thúc bằng `?>`, một ký tự xuống dòng (bị nuốt), rồi thêm một dòng trống (không bị
nuốt). Dòng trống đó là output. Chạy `php main.php`:

```


Warning: Cannot modify header information - headers already sent by (output started at /…/config.php:5) in /…/main.php on line 6
{"debug":true}
```

(Dòng trống thứ nhất là output của `config.php`; dòng thứ hai do PHP tự thêm trước thông báo lỗi.)

Vì sao lại lỗi? Trong một HTTP response, header (như `Content-Type`) phải đi trước nội dung. Khi output
đầu tiên thật sự được gửi đi, PHP gửi header kèm theo, và từ đó `header()` không đổi được gì nữa. CLI
luôn tắt bộ đệm output (`output_buffering`), nên dòng trống của `config.php` được gửi ngay và ta thấy
warning. Thông báo chỉ đúng chỗ gây ra: `output started at .../config.php:5`.

Trên web, nếu `php.ini` bật `output_buffering` (cả hai file mẫu `php.ini-development` và
`php.ini-production` đặt 4096 byte), output nhỏ được giữ lại trong bộ đệm nên có thể không thấy
warning. Nhưng dòng trống vẫn nằm trong response: JSON bị kèm ký tự thừa, file tải về bị hỏng. Lỗi
lúc có lúc không tùy cấu hình nên rất khó tìm.

Cách phòng đơn giản và triệt để: file chỉ chứa code PHP thì không viết `?>` ở cuối. Manual khuyên vậy,
PSR-12 bắt buộc vậy. Thẻ đóng chỉ dùng trong file template, nơi bạn thật sự muốn quay về HTML.

Về các kiểu thẻ khác: `<?=` (in giá trị) luôn dùng được. Thẻ ngắn `<?` (không có chữ `php`) phụ thuộc
cấu hình `short_open_tag`, mà cả `php.ini-development` lẫn `php.ini-production` đều tắt, nên đừng dùng.
PSR-1 chỉ cho phép `<?php` và `<?=`.

### 7.4 `declare(strict_types=1)` phải là câu lệnh đầu tiên

`declare(strict_types=1);` bật chế độ kiểu chặt cho các lời gọi hàm viết trong file đó: truyền chuỗi
`"5"` vào tham số kiểu `int` sẽ bị từ chối thay vì âm thầm đổi thành số. Toàn bộ quy tắc ở
[Chương 04](04-kieu-du-lieu.md). Ở đây chỉ cần biết luật đặt chỗ: nó phải là câu lệnh đầu tiên của file.
Kết quả thử thật trên PHP 8.5:

| Thứ đứng trước `declare(strict_types=1)` | Kết quả |
|---|---|
| Chỉ có `<?php`, dòng trống, comment | Chạy bình thường |
| Một câu lệnh, ví dụ `$a = 1;` | Fatal error |
| HTML trước thẻ `<?php` (ví dụ `<html>`) | Fatal error |
| Một dấu cách trước `<?php` | Fatal error |
| BOM (mục 7.5) trước `<?php` | Fatal error |

Thông báo lỗi:

```
Fatal error: strict_types declaration must be the very first statement in the script in /…/c2.php on line 3
```

Từ PHP 8.5, fatal error còn kèm thêm vài dòng `Stack trace:` phía dưới (PHP 8.4 thì không); đây là
tính năng mới của 8.5, xem [Chương 12](12-loi-exception.md).

Ba trường hợp cuối cùng một gốc: thứ gì nằm ngoài thẻ PHP cũng là output, và output là một "câu lệnh"
in ra, nên `declare` không còn đứng đầu. Với file template, PSR-12 quy định viết `declare` ngay ở dòng
đầu, trong một cặp thẻ riêng:

```php
<?php declare(strict_types=1) ?>
<ul>
<?php foreach (['Sách', 'Bút'] as $sp): ?>
    <li><?= $sp ?></li>
<?php endforeach ?>
</ul>
```

Output (các dòng chỉ chứa thẻ PHP không để lại dòng trống, nhờ điểm 2 ở mục 7.3):

```html
<ul>
    <li>Sách</li>
    <li>Bút</li>
</ul>
```

### 7.5 Mã hoá: UTF-8 không BOM, xuống dòng kiểu LF

File PHP nên lưu dạng UTF-8. Có một biến thể cần tránh: "UTF-8 with BOM". *BOM* (byte order mark) là
3 byte `EF BB BF` mà một số trình soạn thảo chèn vào đầu file. Với PHP, 3 byte đó nằm trước `<?php`,
tức là output. Hậu quả:

- File có `declare(strict_types=1)`: Fatal error như bảng trên (đã thử).
- File không có `declare`: 3 byte BOM bị in ra đầu output (đã thử), đủ để gây lỗi "headers already sent"
  hoặc làm hỏng JSON.

Kiểm tra 3 byte đầu của file (macOS, Linux):

```sh
head -c 3 file.php | od -An -tx1
# File có BOM in ra:  ef bb bf
# File bình thường in ra 3c 3f 70  (tức "<?p")
```

Sửa: trong editor chọn lưu lại dạng "UTF-8" (không phải "UTF-8 with BOM"). PSR-1 quy định code PHP chỉ
dùng UTF-8 không BOM; PSR-12 quy định xuống dòng kiểu Unix (LF, không phải CRLF của Windows) và file kết
thúc bằng đúng một ký tự xuống dòng.

### 7.6 Tên file và đuôi `.php`

Khi chạy bằng CLI, PHP không quan tâm đuôi file. Nhưng web server chỉ chuyển cho PHP những file được cấu
hình (thường là `*.php`); file có đuôi khác bị gửi nguyên văn cho trình duyệt. Một file
`config.inc` hay `backup.php.bak` nằm trong document root có thể làm lộ toàn bộ mã nguồn và mật khẩu
database. Vì vậy: mọi file PHP dùng đuôi `.php`, và chỉ để trong document root những gì được phép truy
cập công khai (lý do Laravel chỉ public thư mục `public/`).

## 8. `php.ini`: cấu hình của PHP

### 8.1 `php.ini` là gì, được đọc khi nào

`php.ini` là file văn bản chứa các *chỉ thị cấu hình* (directive) quyết định cách PHP hoạt động: được
dùng bao nhiêu bộ nhớ, có hiện lỗi ra màn hình không, múi giờ nào, cho upload file lớn tới đâu, nạp
extension nào... Không có `php.ini` thì PHP dùng giá trị mặc định có sẵn trong mã nguồn (trường hợp của
image Docker `php`).

Theo manual, `php.ini` được đọc khi PHP khởi động:

- PHP CLI: đọc lại mỗi lần bạn gõ `php ...`. Sửa xong chạy lại lệnh là có hiệu lực.
- PHP chạy dạng module của web server (Apache `mod_php`): đọc một lần khi web server khởi động.
- PHP-FPM cũng đọc khi khởi động process, nên sửa xong phải reload hoặc restart PHP-FPM thì mới có hiệu
  lực ([Chương 18](18-fpm-nginx-opcache.md)).

⚠️ Mỗi SAPI có thể dùng một `php.ini` riêng. Trên Debian, Ubuntu là `/etc/php/8.4/cli/php.ini` cho
dòng lệnh và `/etc/php/8.4/fpm/php.ini` cho PHP-FPM. Sửa file của CLI rồi thắc mắc vì sao trang web
không đổi là lỗi rất phổ biến. Ngoài ra, nếu tồn tại file `php-cli.ini` (dạng `php-<SAPI>.ini`) thì
PHP CLI dùng nó thay cho `php.ini`.

### 8.2 Tìm `php.ini` đang dùng: `php --ini`

Đừng đoán vị trí, hãy hỏi PHP:

```sh
php --ini
```

Ví dụ trong image Docker `php:8.5-cli` (output minh hoạ, dựng từ Dockerfile của image: không có
`php.ini`, chỉ có file ini do `docker-php-ext-enable sodium` tạo):

```
Configuration File (php.ini) Path: "/usr/local/etc/php"
Loaded Configuration File:         (none)
Scan for additional .ini files in: "/usr/local/etc/php/conf.d"
Additional .ini files parsed:      /usr/local/etc/php/conf.d/docker-php-ext-sodium.ini
```

| Dòng | Ý nghĩa |
|---|---|
| `Configuration File (php.ini) Path` | Thư mục PHP được biên dịch để tìm `php.ini` |
| `Loaded Configuration File` | File `php.ini` thật sự đã nạp. `(none)` nghĩa là không có, PHP đang chạy bằng giá trị mặc định |
| `Scan for additional .ini files in` | Thư mục chứa các file `.ini` phụ, thường tên `conf.d` |
| `Additional .ini files parsed` | Các file phụ đã đọc, mỗi file một dòng, ngăn bằng dấu phẩy |

PHP 8.5 in đường dẫn trong dấu nháy kép như trên; PHP 8.4 trở về trước in không có dấu nháy (đã thử
trên cả hai bản).

Thứ tự đọc: `php.ini` trước, sau đó các file trong thư mục `conf.d` theo thứ tự bảng chữ cái của tên
file. Chỉ thị nào được đặt nhiều lần thì giá trị đọc sau cùng thắng. Vì vậy các bản đóng gói hay đặt
tên file kiểu `10-opcache.ini`, `20-mbstring.ini`: con số ở đầu quyết định thứ tự. Đã thử: `php.ini`
đặt `memory_limit = 96M`, file `conf.d/20-memory.ini` đặt `256M`, kết quả cuối là `256M`.

Vị trí `php.ini` theo cách cài:

| Cách cài | File `php.ini` (CLI) | Thư mục `conf.d` |
|---|---|---|
| Homebrew | `$(brew --prefix)/etc/php/8.5/php.ini` | `$(brew --prefix)/etc/php/8.5/conf.d` |
| Debian, Ubuntu | `/etc/php/8.4/cli/php.ini` | `/etc/php/8.4/cli/conf.d` |
| Docker `php` | Không có sẵn; đặt vào `/usr/local/etc/php/php.ini` | `/usr/local/etc/php/conf.d` |
| Windows (zip) | `php.ini` trong thư mục chứa `php.exe` (bạn tự tạo) | |

Ngoài ra có thể chỉ định file khác bằng tùy chọn `-c` hoặc biến môi trường `PHPRC`, và đổi thư mục quét
bằng biến môi trường `PHP_INI_SCAN_DIR`. Trong code, `php_ini_loaded_file()` trả về đường dẫn
`php.ini` đã nạp (hoặc `false`), `php_ini_scanned_files()` trả về danh sách file phụ.

### 8.3 Cú pháp

`php.ini` là file dạng INI rất đơn giản:

```ini
; Dòng bắt đầu bằng dấu chấm phẩy là comment
[PHP]
memory_limit = 256M
display_errors = On
error_reporting = E_ALL & ~E_DEPRECATED
date.timezone = "Asia/Ho_Chi_Minh"
extension = pdo_mysql
upload_max_filesize = ${UPLOAD_MAX:-20M}
```

Quy tắc chính (theo phần chú thích đầu file `php.ini` mẫu và manual):

- Mỗi dòng dạng `tên = giá_trị`. Tên phân biệt hoa thường.
- Tiêu đề mục như `[PHP]` bị bỏ qua (trừ `[PATH=...]`, `[HOST=...]` chỉ có tác dụng với CGI/FastCGI).
- Giá trị bật/tắt: `On`, `True`, `Yes`, `1` là bật; `Off`, `False`, `No`, `0` là tắt.
- Có thể dùng hằng số của PHP và phép toán bit: `E_ALL & ~E_DEPRECATED`.
- Kích thước viết tắt bằng `K`, `M`, `G` (không phân biệt hoa thường): `1M` là 1048576 byte, `1K` là
  1024 byte. Giá trị số bị ép về số nguyên, nên `0.5M` thành 0.
- `${TEN_BIEN}` lấy giá trị từ biến môi trường. Từ PHP 8.3 có thể ghi giá trị dự phòng
  `${TEN_BIEN:-giá trị}` khi biến không tồn tại.

⚠️ PHP không kiểm tra tên chỉ thị. Gõ sai `memory_limt = 512M` thì PHP lặng lẽ bỏ qua và dùng giá trị
mặc định, không có cảnh báo nào (đã thử: `ini_get('memory_limt')` trả `false`, `memory_limit` không
đổi). Sau khi sửa cấu hình, luôn kiểm tra lại giá trị thật (mục 8.4, 8.6).

⚠️ Cú pháp `${TEN_BIEN:-giá trị}` chỉ có từ 8.3. Đã thử trên PHP 8.2: dòng
`memory_limit = ${PHP_MEM:-256M}` không hiểu được, PHP báo `Warning: Failed to set memory limit to 0
bytes` và giữ giá trị mặc định 128M.

### 8.4 Bốn cách đổi cấu hình, bốn phạm vi khác nhau

| Cách | Phạm vi ảnh hưởng | Ghi chú |
|---|---|---|
| Sửa `php.ini` hoặc thêm file trong `conf.d` | Mọi script chạy bằng SAPI dùng file đó | Web server/PHP-FPM cần reload |
| `php -d tên=giá_trị` | Chỉ một lần chạy CLI đó | Tiện để thử: `php -d memory_limit=512M script.php` |
| `ini_set('tên', 'giá trị')` trong code | Chỉ script/request hiện tại, kết thúc thì trả lại như cũ | Chỉ với chỉ thị cho phép đổi lúc chạy |
| `.user.ini` trong thư mục của ứng dụng | Script trong thư mục đó và thư mục con | Chỉ với CGI/FastCGI (gồm PHP-FPM), được đọc lại theo chu kỳ (mặc định 300 giây) |

Không phải chỉ thị nào cũng đổi được ở mọi nơi. Manual ghi cho mỗi chỉ thị một *chế độ* (mode):

| Chế độ | Đặt được ở đâu |
|---|---|
| `INI_ALL` | Mọi nơi, kể cả `ini_set()` |
| `INI_USER` | Trong script (`ini_set()`), `.user.ini` |
| `INI_PERDIR` | `php.ini`, `.htaccess`, `httpd.conf`, `.user.ini` (không dùng được `ini_set()`) |
| `INI_SYSTEM` | Chỉ `php.ini` hoặc `httpd.conf` |

Thử trong code (`ini.php`, chạy không có `php.ini`):

```php
<?php
declare(strict_types=1);

var_dump(ini_get('memory_limit'));                 // in ra: string(4) "128M"
var_dump(ini_set('memory_limit', '256M'));         // in ra: string(4) "128M"  (trả về giá trị CŨ)
var_dump(ini_get('memory_limit'));                 // in ra: string(4) "256M"
var_dump(ini_set('upload_max_filesize', '20M'));   // in ra: bool(false)  (INI_PERDIR: không đổi được lúc chạy)
var_dump(ini_get('upload_max_filesize'));          // in ra: string(2) "2M"
var_dump(ini_set('khong_ton_tai', '1'));           // in ra: bool(false)  (tên sai, không có cảnh báo)
var_dump(php_ini_loaded_file());                   // in ra: bool(false)  (không có php.ini)
```

Vài điều rút ra:

- `ini_get()` luôn trả về chuỗi (hoặc `false` nếu chỉ thị không tồn tại). Giá trị bật thường đọc ra là
  `"1"`, còn `Off` trong file ini đọc ra là chuỗi rỗng `""` (đã thử với `display_errors = Off`).
- `ini_set()` thất bại thì trả `false` mà không báo lỗi. Nếu việc đổi cấu hình là quan trọng, hãy kiểm
  tra giá trị trả về.
- Với CLI, các chỉ thị bị ép cứng ở mục 4.7 không đổi được bằng `php.ini`, còn `-d` thì được.

### 8.5 Những chỉ thị nên biết ngay

Bảng dưới lấy từ mã nguồn PHP 8.5 (giá trị mặc định khi không có `php.ini`) và phần "Quick Reference" ở
đầu hai file `php.ini` mẫu:

| Chỉ thị | Mặc định | `php.ini-development` | `php.ini-production` | Ý nghĩa |
|---|---|---|---|---|
| `display_errors` | `1` | `On` | `Off` | Hiện lỗi ra output. Production phải tắt vì lỗi có thể lộ đường dẫn, câu SQL ([Chương 12](12-loi-exception.md)) |
| `error_reporting` | `E_ALL` | `E_ALL` | `E_ALL & ~E_DEPRECATED` | Loại lỗi nào được ghi nhận |
| `log_errors` | `0` | `On` | `On` | Ghi lỗi vào log |
| `memory_limit` | `128M` | `128M` | `128M` | Bộ nhớ tối đa một script được dùng |
| `max_execution_time` | `30` | `30` | `30` | Thời gian chạy tối đa (giây). CLI luôn là 0 |
| `date.timezone` | `"UTC"` | (để trống, tức UTC) | (để trống, tức UTC) | Múi giờ mặc định cho các hàm ngày giờ |
| `upload_max_filesize` | `2M` | `2M` | `2M` | Cỡ tối đa một file upload ([Chương 15](15-php-va-web.md)) |
| `post_max_size` | `8M` | `8M` | `8M` | Cỡ tối đa toàn bộ dữ liệu POST |
| `short_open_tag` | `On` | `Off` | `Off` | Có nhận thẻ ngắn `<?` không (mục 7.3) |
| `output_buffering` | `Off` | `4096` | `4096` | Bộ đệm output (mục 7.3). CLI luôn tắt |

Bài thực hành: sửa giờ lệch ở mục 6.1. Kiểm tra múi giờ hiện tại:

```sh
php -r 'echo date_default_timezone_get(), PHP_EOL;'
# in ra: UTC          (khi chưa cấu hình)
```

Ba cách sửa, theo phạm vi từ hẹp tới rộng:

```sh
# 1. Chỉ cho một lần chạy
php -d date.timezone=Asia/Ho_Chi_Minh -r 'echo date_default_timezone_get(), PHP_EOL;'
# in ra: Asia/Ho_Chi_Minh

# 2. Trong code: date_default_timezone_set('Asia/Ho_Chi_Minh');  (chỉ script đó)

# 3. Cho mọi script: thêm vào php.ini (hoặc một file trong conf.d) dòng
#    date.timezone = Asia/Ho_Chi_Minh
#    rồi chạy lại lệnh kiểm tra ở trên; với PHP-FPM thì reload FPM.
```

⚠️ Đặt `date.timezone` bằng chuỗi rỗng hoặc tên sai: từ PHP 8.2, PHP phát cảnh báo
`Invalid date.timezone value '...', using 'UTC' instead` lúc khởi động (đã thử).

### 8.6 `php.ini-development` và `php.ini-production`

Mã nguồn PHP có sẵn hai file mẫu, và phần chú thích đầu file giải thích:

- `php.ini-production` đặt bảo mật, hiệu năng và thói quen tốt lên hàng đầu. Nên dùng cho production
  và cả môi trường test.
- `php.ini-development` gần giống bản production nhưng hiện lỗi chi tiết hơn nhiều. Chỉ dùng khi phát
  triển, vì lỗi hiện cho người dùng có thể làm lộ thông tin.

Mỗi cách cài xử lý khác nhau: Homebrew chép `php.ini-development` thành `php.ini` (và để
`php.ini-production` bên cạnh); image Docker không có `php.ini`, tài liệu của image khuyên dùng bản
production cho môi trường production:

```dockerfile
FROM php:8.5-fpm
# Dùng cấu hình production mặc định
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"
```

Ba cách xem cấu hình thật đang có hiệu lực:

1. `php -i` in toàn bộ (giống trang `phpinfo()`); lọc bằng `grep`:
   `php -i | grep -i timezone`.
2. `php -r 'var_dump(ini_get("memory_limit"));'` cho một chỉ thị.
3. Từ PHP 8.5: `php --ini=diff` chỉ in các chỉ thị khác giá trị mặc định. Ví dụ với một `php.ini` đặt
   `display_errors = Off`, một file `conf.d` đặt `date.timezone` và một file đặt `memory_limit = 256M`
   (output thật, đã bỏ hai dòng về chứng chỉ SSL do môi trường chạy thử tự đặt):

```
Non-default INI settings:
date.timezone: "UTC" -> "Asia/Ho_Chi_Minh"
display_errors: "1" -> ""
html_errors: "1" -> "0"
implicit_flush: "0" -> "1"
max_execution_time: "30" -> "0"
memory_limit: "128M" -> "256M"
```

Ba dòng `html_errors`, `implicit_flush`, `max_execution_time` là các giá trị CLI tự ép (mục 4.7), không
đến từ file nào.

⚠️ Đừng để một trang chứa `phpinfo()` trên server thật. Nó in ra phiên bản PHP, đường dẫn, extension,
biến môi trường (có thể gồm mật khẩu) cho bất kỳ ai mở trang. Nếu buộc phải xem cấu hình của PHP-FPM
qua trình duyệt, tạo trang tạm ở máy dev, xem xong xoá ngay.

## 9. Extension

### 9.1 Extension là gì

Phần lớn hàm và class bạn dùng trong PHP không nằm trong "lõi" ngôn ngữ mà nằm trong các *extension*:
những module (thường viết bằng C) gắn thêm hàm, class, hằng số vào PHP. Ví dụ:

| Extension | Cung cấp | Dùng khi |
|---|---|---|
| `mbstring` | Các hàm `mb_*` xử lý chuỗi nhiều byte | Đếm, cắt chuỗi tiếng Việt đúng ký tự ([Chương 05](05-chuoi.md)) |
| `pdo_mysql` | Driver MySQL cho PDO | Kết nối MySQL ([Chương 16](16-php-va-database.md)) |
| `intl` | `NumberFormatter`, `Collator`... | Định dạng tiền, sắp xếp theo ngôn ngữ |
| `curl` | Các hàm `curl_*` | Gọi HTTP API khác |
| `opcache` | Cache opcode | Tăng tốc mọi ứng dụng ([Chương 02](02-php-chay-nhu-the-nao.md), [Chương 18](18-fpm-nginx-opcache.md)) |
| `redis`, `xdebug` | Client Redis; debug và đo coverage | Cài thêm từ bên ngoài (mục 9.4) |

Vì sao không gộp hết vào lõi? Nhiều extension phụ thuộc thư viện C bên ngoài (`curl` cần libcurl,
`intl` cần ICU, `openssl` cần OpenSSL). Tách thành extension giúp mỗi máy chỉ cần build và nạp những gì
nó dùng, và bên thứ ba có thể viết thêm extension mà không phải sửa PHP.

Hình dung:

```
code PHP của bạn
      │  gọi mb_strlen(), new PDO(...), json_encode()...
      ▼
chương trình php
  ├── Zend Engine (dịch và chạy code)
  ├── phần lõi luôn có: Core, standard, date, pcre, SPL, Reflection, json, hash, random...
  │                     (từ PHP 8.5 có cả opcache)
  └── extension được nạp theo cấu hình: mbstring, pdo_mysql, curl, intl...
                                         (hàm của extension nào chưa nạp thì "không tồn tại")
```

### 9.2 Các nhóm extension

Manual chia extension thành bốn nhóm
([Extension List/Categorization, mục Membership](https://www.php.net/manual/en/extensions.membership.php)):

| Nhóm | Là gì | Ví dụ |
|---|---|---|
| Core | Thật ra là một phần của lõi PHP, không thể bỏ ra khi build | Date/Time, PCRE, SPL, Reflection, JSON, Hash, Random |
| Bundled | Đi kèm mã nguồn PHP | BC Math, Ctype, Fileinfo, Multibyte String (`mbstring`), PDO, PCNTL |
| External | Đi kèm mã nguồn PHP nhưng cần thư viện ngoài để build | cURL, OpenSSL, Sodium, Zip, MySQLi, MySQL PDO Driver (`pdo_mysql`), Readline |
| PECL | Phát hành riêng trên kho PECL | APCu, Igbinary, Memcached, MongoDB, ImageMagick |

⚠️ "Bundled" hay "External" nghĩa là có sẵn trong mã nguồn PHP, không có nghĩa là bản PHP của bạn
đã bật nó. Có hay không tùy người build: image Docker `php` không có `pdo_mysql`, gói Debian tách mỗi extension thành một
gói riêng. Luôn kiểm tra (mục 9.3).

Có một loại đặc biệt gọi là *Zend extension*, can thiệp sâu vào engine (OPcache, Xdebug). Chúng được nạp
bằng chỉ thị `zend_extension=` thay vì `extension=`, và hiện ở mục `[Zend Modules]` trong output của
`php -m`. Riêng OPcache từ PHP 8.5 luôn được build và nạp sẵn, không cần dòng `zend_extension=` nữa.

### 9.3 Xem extension nào đang có

```sh
php -m
```

Output có dạng (rút gọn, danh sách thật tùy cách cài):

```
[PHP Modules]
bcmath
Core
ctype
curl
date
...
mbstring
...
PDO
pdo_mysql
pdo_sqlite
...
Zend OPcache
zip
zlib

[Zend Modules]
Zend OPcache
```

Các lệnh hữu ích khác:

```sh
php -m | grep -i mbstring    # có mbstring không?
php --ri mbstring            # cấu hình của extension mbstring
php --re json                # mọi hằng, hàm, class mà extension json cung cấp
```

Trong code, kiểm tra bằng `extension_loaded()`, hoặc kiểm tra thẳng thứ mình cần bằng `function_exists()`,
`class_exists()`. File `ext.php`:

```php
<?php
declare(strict_types=1);

// Kiểm tra extension trước khi dùng
foreach (['mbstring', 'pdo_mysql', 'intl'] as $ext) {
    echo $ext, ': ', extension_loaded($ext) ? 'có' : 'KHÔNG có', "\n";
}

// Hàm, class của một extension chỉ tồn tại khi extension được nạp
var_dump(function_exists('mb_strlen'));      // mbstring
var_dump(class_exists('NumberFormatter'));   // intl

echo mb_strlen('Việt Nam'), ' ', strlen('Việt Nam'), "\n";
print_r(PDO::getAvailableDrivers());
```

Output trên môi trường chạy thử (có `mbstring`, `pdo_mysql`, `pdo_sqlite`, không có `intl`; máy bạn có
thể khác):

```
mbstring: có
pdo_mysql: có
intl: KHÔNG có
bool(true)
bool(false)
8 10
Array
(
    [0] => mysql
    [1] => sqlite
)
```

`mb_strlen('Việt Nam')` đếm 8 ký tự, còn `strlen()` đếm 10 byte vì chữ `ệ` chiếm 3 byte trong UTF-8.
Đây là lý do mọi dự án xử lý tiếng Việt cần `mbstring` ([Chương 05](05-chuoi.md)).
`PDO::getAvailableDrivers()` liệt kê các driver database mà PDO đang có.

Thiếu extension thì lỗi trông như thế nào (đã thử trên bản PHP không có `intl`, không có `pdo_pgsql`):

| Bạn dùng | Thông báo |
|---|---|
| Hàm của extension chưa nạp, ví dụ `numfmt_create()` | `Fatal error: Uncaught Error: Call to undefined function numfmt_create()` |
| Class của extension chưa nạp, ví dụ `new NumberFormatter(...)` | `Fatal error: Uncaught Error: Class "NumberFormatter" not found` |
| PDO với driver chưa nạp, ví dụ `new PDO('pgsql:...')` | `PDOException: could not find driver` |

Gặp các thông báo này với một hàm có thật trong manual, hãy nghĩ ngay tới extension chưa được bật,
không phải lỗi gõ sai.

⚠️ CLI và PHP-FPM có thể nạp extension khác nhau, vì chúng đọc `php.ini` và `conf.d` khác nhau
(mục 8.1). `php -m` trên terminal chỉ nói về CLI. Lệnh `artisan` chạy được mà trang web báo
`could not find driver` là triệu chứng điển hình.

### 9.4 Bật và cài thêm extension

Extension đã có file (`.so` trên Linux, macOS; `.dll` trên Windows) thì bật bằng một dòng trong
`php.ini` hoặc một file trong `conf.d`:

```ini
extension=pdo_mysql
```

Chỉ cần tên. Cú pháp cũ `extension=pdo_mysql.so` hay `extension=php_pdo_mysql.dll` vẫn được hỗ trợ vì
lý do tương thích, nhưng chú thích trong `php.ini` mẫu khuyên chuyển sang dạng chỉ có tên. PHP tìm file
trong thư mục `extension_dir`; cũng có thể ghi đường dẫn tuyệt đối tới file.

Cách cài thêm khác nhau theo cách cài PHP:

| Cách cài PHP | Cài, bật extension |
|---|---|
| Debian, Ubuntu | `sudo apt install php8.4-mbstring php8.4-mysql` (hoặc `php-mbstring`, `php-mysql` cho bản mặc định). Gói tự thêm file vào `conf.d`; bật, tắt bằng `phpenmod`, `phpdismod` |
| Docker `php` | Extension có trong mã nguồn PHP: `docker-php-ext-install pdo_mysql`. Extension PECL: `pecl install <tên>` rồi `docker-php-ext-enable <tên>` |
| Windows (zip) | File DLL nằm trong thư mục `ext`; bỏ dấu `;` trước dòng `extension=...` tương ứng trong `php.ini` và đặt `extension_dir` đúng |
| Homebrew | Formula `php` đã build sẵn nhiều extension; extension ngoài cài bằng `pecl` (đi kèm formula) hoặc PIE |

Ví dụ Dockerfile cho một ứng dụng cần MySQL và Redis:

```dockerfile
FROM php:8.5-cli
# pdo_mysql có trong mã nguồn PHP: build và bật bằng script có sẵn của image
RUN docker-php-ext-install pdo_mysql
# redis là extension PECL: tài liệu image khuyên ghi rõ phiên bản, dạng redis-<phiên bản>
RUN pecl install redis && docker-php-ext-enable redis
```

`docker-php-ext-enable` tạo file `/usr/local/etc/php/conf.d/docker-php-ext-<tên>.ini` chứa dòng
`extension=...` (hoặc `zend_extension=...` nếu là Zend extension).

Về PECL và PIE: *PECL* là kho và công cụ cài extension truyền thống của PHP. *PIE* (PHP Installer for
Extensions) là công cụ mới; README của PIE giới thiệu nó là trình cài extension chính thức, thay thế
PECL (mà README ghi là đã bị deprecated). PIE phát hành dạng file PHAR giống Composer, cài bằng lệnh
`pie install <vendor>/<package>`, cần PHP 8.1 trở lên để chạy. Khi cài extension mới, hãy xem trang của
extension đó hướng dẫn dùng công cụ nào.

Sau khi bật extension: chạy lại `php -m` để kiểm tra với CLI; với PHP-FPM phải reload FPM rồi mới kiểm
tra trên web.

Dự án dùng Composer nên khai báo extension cần thiết trong `composer.json`, ví dụ
`"require": {"ext-mbstring": "*", "ext-pdo_mysql": "*"}`. Khi đó `composer install` báo lỗi ngay trên
máy thiếu extension, thay vì để ứng dụng chết lúc chạy ([Chương 11](11-namespace-composer.md)).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Học theo bài hướng dẫn cũ dùng `mysql_connect()` | Extension `mysql` bị xoá từ PHP 7.0 | Kiểm tra bài viết dành cho bản nào; tra manual php.net (mục 1.4) |
| Cài và chạy production trên nhánh đã EOL | Không còn bản vá bảo mật | Theo dõi trang Supported Versions, lên kế hoạch nâng minor mỗi năm (mục 2.3) |
| So phiên bản bằng `'8.4.10' > '8.4.9'` | Chuỗi không phải số nên bị so từng ký tự | Dùng `version_compare()` hoặc `PHP_VERSION_ID` (mục 2.5) |
| `apt install php` rồi thấy máy có thêm Apache | Gói `php` của Debian kéo theo module Apache | Chỉ cần CLI thì cài `php-cli` (mục 3.4) |
| `php -v` một bản, editor hoặc Composer báo bản khác | Máy có nhiều PHP, PATH chọn bản khác | `which -a php`, sửa PATH hoặc link lại (mục 3.6) |
| `php -r "..."` báo Parse error khó hiểu | Shell thay `$bien` trong nháy kép | Dùng nháy đơn với `-r` (mục 4.2) |
| Script báo lỗi bằng `exit("Lỗi...")`, CI vẫn xanh | `exit` với chuỗi trả mã 0 | Ghi lỗi ra STDERR rồi `exit(1)` (mục 4.4) |
| Script CLI không tìm thấy file `data.csv` cạnh nó | Đường dẫn tương đối tính từ thư mục làm việc | Dùng `__DIR__ . '/data.csv'` (mục 4.7) |
| Đặt `max_execution_time` trong `php.ini` mà script CLI vẫn chạy mãi | CLI ép giá trị 0 sau khi đọc `php.ini` | Dùng `-d` hoặc `set_time_limit()`/`ini_set()` nếu thật sự cần (mục 4.7) |
| `php -a` "treo", gõ gì cũng không ra kết quả | Quên dấu `;`, shell đang chờ dòng tiếp; hoặc thiếu `-it` khi chạy Docker | Gõ `;`; dùng `docker run -it` (mục 5) |
| `php -S localhost:8000` trong Docker mà trình duyệt không vào được | `localhost` của container khác của máy bạn | `php -S 0.0.0.0:8000` và `-p 8000:8000` (mục 6.1) |
| Dùng `php -S` cho production | Server đơn luồng, không dành cho mạng công cộng | PHP-FPM sau Nginx (mục 6.3) |
| "headers already sent", JSON có dòng trống lạ | Khoảng trắng sau `?>` hoặc BOM đầu file thành output | Bỏ `?>` ở file PHP thuần, lưu UTF-8 không BOM (mục 7.3, 7.5) |
| Fatal error "strict_types declaration must be the very first statement" | Có output (HTML, dấu cách, BOM) hoặc câu lệnh trước `declare` | `<?php` ở byte đầu tiên, `declare` là lệnh đầu (mục 7.4) |
| Sửa `php.ini` mà không có tác dụng | Sửa nhầm file của SAPI khác, gõ sai tên chỉ thị, hoặc chưa reload PHP-FPM | `php --ini`, kiểm tra bằng `ini_get()` hoặc `--ini=diff`, reload FPM (mục 8) |
| Giờ lệch 7 tiếng | `date.timezone` mặc định UTC | Đặt `date.timezone` (mục 8.5) |
| Để trang `phpinfo()` trên server thật | Lộ cấu hình, đường dẫn, biến môi trường | Chỉ dùng ở máy dev, xoá ngay (mục 8.6) |
| `Call to undefined function mb_strlen()`, `could not find driver` | Extension chưa được nạp (có khi chỉ thiếu ở FPM) | `php -m`, cài/bật extension, khai báo `ext-*` trong `composer.json` (mục 9) |

## Tóm tắt chương

- PHP là ngôn ngữ kịch bản mã nguồn mở, đa dụng, mạnh nhất ở web phía server; chạy được cả trong web
  server lẫn dòng lệnh. Code chạy trên server, trình duyệt chỉ nhận kết quả.
- PHP ra đời năm 1994 từ bộ công cụ cá nhân của Rasmus Lerdorf; PHP 7 (2015) và 8 (2020) thay đổi lớn.
  Tài liệu cũ rất nhiều, luôn kiểm tra bài viết dành cho bản nào.
- Phiên bản dạng `major.minor.patch`; mỗi năm một bản minor vào cuối tháng 11; mỗi nhánh được hỗ trợ
  2 năm đầy đủ và 2 năm chỉ vá bảo mật, các mốc kết thúc vào 31/12. Tại 10/2026: 8.5 và 8.4 đang active,
  8.3 và 8.2 chỉ vá bảo mật, 8.1 trở về trước đã EOL.
- Cài bằng Homebrew, Docker (`php:8.5-cli`), gói Linux hoặc bản Windows; kiểm tra bằng `php -v` và
  `which -a php`.
- CLI: `php file.php`, `php -r '...'`, `$argv`/`$argc`, STDIN/STDOUT/STDERR, mã thoát (0 là thành công,
  255 khi fatal error, `exit("chuỗi")` trả 0), `php -l` để lint. CLI ép `max_execution_time = 0` và vài
  chỉ thị khác.
- `php -a` là REPL cơ bản (cần `readline`, mỗi lệnh kết thúc bằng `;`, không tự in giá trị); Tinker
  (PsySH) là REPL của Laravel. `php -S` là web server chỉ để phát triển, hỗ trợ router script.
- File PHP thuần: `<?php`, `declare(strict_types=1);` là lệnh đầu tiên, rồi `namespace`, `use`, code;
  không có `?>` ở cuối; lưu UTF-8 không BOM, xuống dòng LF.
- `php.ini` được đọc khi PHP khởi động; tìm bằng `php --ini`; mỗi SAPI có thể có file riêng; đổi cấu hình
  bằng `php.ini`/`conf.d`, `-d`, `ini_set()`, `.user.ini` với phạm vi khác nhau. Dùng
  `php.ini-development` khi dev, `php.ini-production` cho production.
- Extension bổ sung hàm và class (mbstring, pdo_mysql, intl...); xem bằng `php -m`, cài theo cách cài
  PHP (apt, `docker-php-ext-install`, PECL, PIE), và nhớ CLI với FPM có thể khác nhau.

## Câu hỏi tự kiểm tra

1. Vì sao người dùng mở trang `.php` trên trình duyệt không thấy được mã PHP? Điều này cho phép PHP làm
   những việc gì mà JavaScript trong trình duyệt không làm được? (mục 1.2)
2. Nâng từ 8.4.25 lên 8.4.26 và nâng từ 8.4 lên 8.5 khác nhau thế nào về rủi ro? Chính sách phát hành
   của PHP cho phép mỗi loại thay đổi những gì? (mục 2.1)
3. Ngày 15/06/2027, những nhánh PHP nào còn active support, nhánh nào chỉ còn vá bảo mật, nhánh nào đã
   EOL? (mục 2.3)
4. Một script CLI đọc file `config.json` bằng đường dẫn tương đối. Chạy `php bin/import.php` ở thư mục gốc
   dự án thì được, chạy trong thư mục `bin/` thì lỗi. Giải thích và sửa.
5. Viết lệnh shell chạy một script PHP, rồi chỉ chạy lệnh thứ hai khi script thành công. Script phải
   kết thúc thế nào khi gặp lỗi để lệnh thứ hai không chạy? (mục 4.4)
6. Vì sao `php -l` báo "No syntax errors detected" mà khi chạy file đó vẫn Fatal error? Công cụ nào bắt
   được loại lỗi đó trước khi chạy?
7. Bạn sửa `memory_limit` trong `php.ini` nhưng trang web vẫn báo hết bộ nhớ ở 128M, trong khi
   `php -r 'echo ini_get("memory_limit");'` in đúng giá trị mới. Nêu ít nhất hai nguyên nhân có thể và
   cách kiểm tra từng nguyên nhân. (mục 8.1, 8.2)
8. Giải thích từng bước vì sao một dòng trống sau `?>` trong file `config.php` lại làm `header()` ở file
   khác thất bại, và vì sao lỗi này lúc có lúc không. (mục 7.3)
9. `ini_set('upload_max_filesize', '20M')` trả về `false`. Vì sao, và phải đặt chỉ thị này ở đâu?
   (mục 8.4)
10. Lệnh `artisan` trên server chạy bình thường nhưng trang web báo `could not find driver`. Bạn kiểm
    tra những gì?

## Bài tập

1. **Cài đặt và kiểm tra.** Cài PHP 8.5 bằng một cách ở mục 3 (hoặc dùng Docker). Ghi lại output của
   `php -v`, `php --ini` và `php -m` vào một file `moi-truong.txt`. Nếu dùng Docker, chạy thêm các lệnh
   đó với `php:8.4-cli` và ghi ra các điểm khác nhau bạn thấy.
2. **Công cụ dòng lệnh đầu tiên.** Viết `tinh-tong.php` nhận một danh sách số qua đối số
   (`php tinh-tong.php 3 5 10`) hoặc, nếu không có đối số, đọc mỗi dòng một số từ STDIN
   (`printf "3\n5\n10\n" | php tinh-tong.php`). In tổng ra STDOUT. Nếu có giá trị không phải số nguyên,
   in thông báo ra STDERR, chỉ ra giá trị sai, và thoát với mã 2. Thêm dòng shebang và chạy được bằng
   `./tinh-tong.php`. Kiểm tra mã thoát bằng `echo $?` cho cả trường hợp đúng và sai.
3. **Web server dựng sẵn.** Trong thư mục `public/`, viết `router.php` cho `php -S` sao cho: file tĩnh có
   thật thì server tự trả về; `GET /` trả trang HTML có lời chào và giờ hiện tại theo múi giờ Việt Nam;
   `GET /api/thoi-gian` trả JSON gồm giờ hiện tại và tên múi giờ; đường dẫn khác trả mã 404 kèm JSON báo
   lỗi (gợi ý: `http_response_code()`). Đặt múi giờ bằng cấu hình, không viết cứng trong code, và ghi lại
   bạn đã chọn cách nào trong mục 8.4, vì sao.
4. **Kiểm tra cấu hình.** Viết `kiem-tra.php` in ra: phiên bản PHP, SAPI, file `php.ini` đã nạp (hoặc
   "không có"), các file ini phụ, giá trị của `memory_limit`, `max_execution_time`, `display_errors`,
   `date.timezone`, và với danh sách extension `['mbstring', 'intl', 'pdo_mysql', 'curl']` thì in có
   hay không. Chạy nó bằng CLI, rồi qua `php -S`, rồi với `php -n`, và giải thích những giá trị khác nhau
   giữa ba lần chạy.

## Đọc thêm

- PHP Manual, [What is PHP and what can it do?](https://www.php.net/manual/en/introduction.php) và
  [History of PHP](https://www.php.net/manual/en/history.php.php)
- [Supported Versions](https://www.php.net/supported-versions.php),
  [Unsupported Branches](https://www.php.net/eol.php) và chính sách
  [release-process](https://github.com/php/policies/blob/main/release-process.rst) của PHP
- RFC [Release cycle update](https://wiki.php.net/rfc/release_cycle_update) (2024) và quy trình RFC
  [feature-proposals](https://github.com/php/policies/blob/main/feature-proposals.rst)
- [Downloads & Installation Instructions](https://www.php.net/downloads.php) của php.net,
  [windows.php.net/download](https://windows.php.net/download/),
  [Installation on macOS](https://www.php.net/manual/en/install.macosx.php)
- Docker Official Image [php](https://hub.docker.com/_/php) (mục How to use, Image Variants, Configuration)
- PHP Manual, [Command line usage](https://www.php.net/manual/en/features.commandline.php): các trang
  Options, Differences from other SAPIs, I/O streams, Interactive shell, Built-in web server
- PHP Manual, [exit](https://www.php.net/manual/en/function.exit.php)
- PHP Manual, [PHP tags](https://www.php.net/manual/en/language.basic-syntax.phptags.php) và
  [Instruction separation](https://www.php.net/manual/en/language.basic-syntax.instruction-separation.php)
- [PSR-1](https://www.php-fig.org/psr/psr-1/) và [PSR-12](https://www.php-fig.org/psr/psr-12/)
- PHP Manual, [The configuration file](https://www.php.net/manual/en/configuration.file.php),
  [.user.ini files](https://www.php.net/manual/en/configuration.file.per-user.php),
  [Where a configuration setting may be set](https://www.php.net/manual/en/configuration.changes.modes.php),
  [ini_set](https://www.php.net/manual/en/function.ini-set.php)
- Hai file mẫu [php.ini-development](https://github.com/php/php-src/blob/master/php.ini-development) và
  [php.ini-production](https://github.com/php/php-src/blob/master/php.ini-production) (đọc phần Quick
  Reference ở đầu file)
- PHP Manual, [Extension List/Categorization: Membership](https://www.php.net/manual/en/extensions.membership.php);
  [PIE](https://github.com/php/pie)
- File `UPGRADING` của PHP 8.5 trong [php-src](https://github.com/php/php-src) (mục CLI, OPcache, INI)
- Laravel 13: [Installation](https://laravel.com/docs/13.x/installation),
  [Release notes](https://laravel.com/docs/13.x/releases), [Artisan, Tinker](https://laravel.com/docs/13.x/artisan#tinker)
