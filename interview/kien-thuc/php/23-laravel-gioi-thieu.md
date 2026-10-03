# Chương 23. Laravel: giới thiệu và cấu trúc dự án

> [← Mục lục](README.md) · [← Chương 22: Tổng hợp PHP 8.0 tới 8.5](22-phien-ban-moi.md) · [Chương 24: Routing, controller và middleware →](24-laravel-routing-controller-middleware.md)

**Bạn sẽ học được:**

- Framework là gì, khác thư viện ở đâu, và vì sao gần như mọi dự án PHP thương mại đều dùng một
  framework thay vì viết tay từ `$_GET`, `$_POST`.
- Laravel là gì, chính sách phiên bản và hỗ trợ của nó (mỗi năm một bản lớn, sửa lỗi 18 tháng, vá bảo
  mật 2 năm) và cách đọc bảng hỗ trợ để chọn phiên bản.
- Cách tạo một dự án Laravel 13 bằng `laravel new` hoặc `composer create-project`, và những gì xảy ra
  ngay sau lệnh đó.
- Cấu trúc thư mục của một dự án Laravel 11 trở lên: mỗi thư mục chứa gì, request đi qua những file nào
  (`public/index.php`, `bootstrap/app.php`, `routes/web.php`...).
- Hệ thống cấu hình: file `.env`, hàm `env()`, hàm `config()`, và cái bẫy kinh điển khi chạy
  `php artisan config:cache`.
- Artisan (công cụ dòng lệnh của Laravel) với các lệnh dùng hằng ngày, và bản đồ hệ sinh thái:
  Sail, Herd, Forge, Vapor, Cloud, Octane, Horizon, Telescope, Pulse, Boost.

**Cần biết trước:** [Chương 11](11-namespace-composer.md) (namespace, autoload PSR-4, Composer) là
quan trọng nhất, vì Laravel dựng hoàn toàn trên Composer. Nên đọc [Chương 15](15-php-va-web.md)
(PHP xử lý HTTP thế nào) và [Chương 18](18-fpm-nginx-opcache.md) (PHP-FPM, Nginx, document root) để
hiểu vì sao Laravel có thư mục `public/`. Cú pháp PHP hiện đại (closure, arrow function, named
argument, attribute) ở [Chương 08](08-ham.md) và [Chương 10](10-oop-nang-cao.md).

Cách đọc chương này: đây là chương "nhìn toàn cảnh". Nó cho bạn bản đồ của một dự án Laravel để các
chương sau (24 tới 30) đi sâu từng phần. Những gì thuộc chương sau chỉ được nhắc một câu kèm link.

Một lưu ý về ví dụ: máy dùng để soạn giáo trình không cài được Laravel, nên các file Laravel trong
chương (như `bootstrap/app.php`, `.env.example`) được chép nguyên văn từ repo chính thức
[laravel/laravel nhánh 13.x](https://github.com/laravel/laravel/tree/13.x), còn hành vi được đối chiếu
với mã nguồn [laravel/framework nhánh 13.x](https://github.com/laravel/framework/tree/13.x) và tài liệu
chính thức. Các ví dụ PHP thuần (mô phỏng cơ chế) đã chạy thật trên PHP 8.5; output ghi trong comment
`// in ra: ...`. Output của lệnh `php artisan ...` được ghi là "output minh hoạ" khi không chép từ tài
liệu.

## 1. Framework là gì và vì sao cần

### 1.1 Viết ứng dụng web "tay không" thì phải lo những gì

Ở [Chương 15](15-php-va-web.md) bạn đã viết PHP xử lý HTTP trực tiếp: đọc `$_GET`, `$_POST`,
`$_SERVER['REQUEST_URI']`, gọi `header()`, `setcookie()`, `session_start()`. Với một trang đơn giản
thì đủ. Nhưng hãy liệt kê những việc mà một ứng dụng web thật (một trang bán hàng, một API cho app
di động) phải làm cho gần như mọi request:

| Việc | Viết tay nghĩa là |
|---|---|
| Định tuyến (*routing*): URL nào chạy code nào | Tự phân tích `REQUEST_URI`, tự viết bảng `if/switch` hoặc regex |
| Đọc và kiểm tra dữ liệu vào (*validation*) | Tự viết từng điều kiện, tự gom thông báo lỗi |
| Chống CSRF, XSS, SQL injection | Tự sinh token, tự escape, tự dùng prepared statement ở mọi chỗ ([Chương 17](17-bao-mat.md)) |
| Kết nối database, migration (thay đổi schema có phiên bản) | Tự viết lớp bọc PDO, tự quản lý file SQL thay đổi schema |
| Đăng nhập, phân quyền, quên mật khẩu | Tự băm mật khẩu, tự quản lý session, tự sinh link reset |
| Gửi email, hàng đợi (*queue*) việc chạy nền, lịch chạy định kỳ | Tự viết worker, tự cấu hình cron |
| Cấu hình khác nhau giữa máy dev và server | Tự nghĩ cách đọc file cấu hình theo môi trường |
| Xử lý lỗi, ghi log | Tự đăng ký `set_exception_handler`, tự định dạng log |
| Test tự động | Tự dựng request giả, tự dọn database sau mỗi test |

Mỗi dòng trong bảng là vài trăm tới vài nghìn dòng code, và mỗi dòng đều có cách làm sai gây lỗ hổng
bảo mật. Nếu mỗi dự án tự viết lại toàn bộ, ta tốn thời gian vào những thứ không phải nghiệp vụ, và
mỗi dự án có một kiểu tổ chức riêng nên người mới vào phải học lại từ đầu.

### 1.2 Thư viện (library) và framework khác nhau thế nào

Cả hai đều là "code người khác viết sẵn". Khác biệt nằm ở chỗ ai gọi ai.

- *Library* (thư viện): bạn gọi nó. Ví dụ bạn gọi `json_encode()`, hoặc gọi một thư viện gửi email
  khi cần. Luồng chương trình do bạn điều khiển.
- *Framework*: nó gọi bạn. Framework điều khiển luồng chính (nhận request, chọn code cần chạy, trả
  response); bạn chỉ "đăng ký" các mảnh code của mình vào những chỗ nó chừa sẵn. Nguyên lý này có tên
  *inversion of control* (đảo ngược điều khiển), hay được tóm bằng câu "Don't call us, we'll call you".

Ví dụ sau dựng một "framework" tí hon trong 20 dòng để bạn thấy cảm giác "framework gọi mình". Đây
chỉ là mô phỏng để học, Laravel thật phức tạp hơn rất nhiều.

```php
<?php
declare(strict_types=1);

// ===== Phần "framework" (bạn KHÔNG viết, chỉ dùng) =====
final class MiniApp
{
    /** @var array<string, callable(array<string, string>): string> */
    private array $routes = [];

    public function get(string $path, callable $handler): void
    {
        $this->routes['GET ' . $path] = $handler;
    }

    /** @param array<string, string> $query */
    public function handle(string $method, string $path, array $query): string
    {
        $key = $method . ' ' . $path;
        if (!array_key_exists($key, $this->routes)) {
            return '404 Not Found';
        }
        // Framework gọi code của bạn, không phải bạn gọi framework.
        return '200 ' . ($this->routes[$key])($query);
    }
}

// ===== Phần "ứng dụng" (bạn viết) =====
$app = new MiniApp();
$app->get('/hello', fn (array $q): string => 'Xin chào ' . ($q['name'] ?? 'khách'));

// Giả lập hai request đi vào
echo $app->handle('GET', '/hello', ['name' => 'An']), "\n";   // in ra: 200 Xin chào An
echo $app->handle('GET', '/khong-co', []), "\n";              // in ra: 404 Not Found
```

Bạn không bao giờ tự gọi closure `fn (array $q) ...`. Bạn chỉ đăng ký nó với `$app->get(...)`, và
`handle()` của framework quyết định khi nào gọi nó. Trong Laravel, file `routes/web.php` làm đúng việc
đăng ký này: `Route::get('/', function () { ... });`. Phần "framework" ở trên trong Laravel là hàng
trăm nghìn dòng code nằm trong `vendor/laravel/framework`.

### 1.3 Framework cho bạn ba thứ

1. **Code có sẵn và đã được kiểm chứng** cho các việc lặp lại ở bảng 1.1. Hàng nghìn dự án dùng
   chung nên lỗi được phát hiện và vá nhanh hơn code tự viết.
2. **Một cấu trúc chung** (*convention*, quy ước): controller để ở đâu, model đặt tên thế nào, cấu
   hình nằm ở đâu. Người đã biết Laravel mở một dự án Laravel lạ vẫn biết tìm gì ở đâu. Laravel theo
   triết lý *convention over configuration*: làm theo quy ước thì gần như không phải cấu hình gì.
3. **Một hệ sinh thái**: package, tài liệu, công cụ deploy, cộng đồng hỏi đáp.

Cái giá phải trả:

- Phải học framework (chính là các chương 23 tới 30).
- Framework làm nhiều việc "ngầm" (*magic*), nên khi có lỗi bạn cần hiểu nó chạy bên trong thế nào.
  Đây là lý do giáo trình này dạy PHP thuần trước (chương 1 tới 22) rồi mới tới Laravel.
- Mỗi request phải nạp và khởi động framework, tốn thời gian hơn một file PHP trơn. OPcache
  ([Chương 18](18-fpm-nginx-opcache.md)) và các lệnh cache của Laravel (mục 7.1 chương này) bù lại phần
  lớn chi phí đó.
- Bị ràng buộc vào lịch phát hành của framework: phải nâng cấp theo khi bản cũ hết hỗ trợ (mục 2).

### 1.4 MVC: mô hình tổ chức mà Laravel dùng

Hầu hết web framework (Laravel, Symfony, Rails, Django, Spring MVC) tổ chức code theo *MVC*
(Model, View, Controller):

```
   Request (GET /posts/5)
        │
        ▼
   ┌──────────┐   "URL này do ai xử lý?"
   │  Router  │ ─────────────────────────┐
   └──────────┘                          ▼
                                  ┌──────────────┐  hỏi dữ liệu   ┌─────────┐      ┌──────────┐
                                  │  Controller  │ ─────────────▶ │  Model  │ ───▶ │ Database │
                                  │ (điều phối)  │ ◀───────────── │(dữ liệu)│ ◀─── │          │
                                  └──────────────┘   trả object   └─────────┘      └──────────┘
                                         │ đưa dữ liệu cho view
                                         ▼
                                  ┌──────────────┐
                                  │     View     │  (HTML, hoặc JSON nếu là API)
                                  └──────────────┘
                                         │
                                         ▼
                                     Response
```

- *Model*: đại diện dữ liệu và quy tắc nghiệp vụ gắn với dữ liệu. Trong Laravel là các class
  *Eloquent* trong `app/Models` (mỗi model ứng với một bảng, xem [Chương 27](27-laravel-database-eloquent.md)).
- *View*: phần trình bày. Trong Laravel là file *Blade* (`.blade.php`) trong `resources/views`, hoặc
  JSON trả về cho API ([Chương 25](25-laravel-request-validation-response.md)).
- *Controller*: nhận request, gọi model, chọn view. Trong Laravel nằm ở `app/Http/Controllers`
  ([Chương 24](24-laravel-routing-controller-middleware.md)).

⚠️ MVC chỉ là điểm khởi đầu. Nhồi hết nghiệp vụ vào controller (*fat controller*) hoặc vào model
(*fat model*) đều làm code khó test và khó đọc khi dự án lớn. Các dự án lớn thường thêm lớp service,
action, job... Laravel không cấm, vì như tài liệu viết, nó "gần như không ràng buộc class nào phải đặt
ở đâu, miễn là Composer autoload được" (mục 4).

### 1.5 Vì sao Laravel

Laravel là một web framework PHP mã nguồn mở (giấy phép MIT), do Taylor Otwell tạo ra và phát hành bản
đầu năm 2011. Ở thời điểm viết (10/2026), bản lớn mới nhất là Laravel 13 (phát hành 17/3/2026).

Lý do Laravel được chọn nhiều:

- **Đủ đồ**: routing, validation, ORM (Eloquent), migration, queue, scheduler, cache, mail,
  notification, auth, test... đều có sẵn và cùng một phong cách. Tài liệu gọi đây là framework
  "progressive": người mới dùng được ngay, người có kinh nghiệm có sẵn dependency injection, queue,
  test.
- **Cú pháp gọn**, đọc như tiếng Anh: `User::where('active', true)->orderBy('name')->get()`.
- **Tài liệu tốt** và cộng đồng lớn; nhiều package bên thứ ba.
- **Hệ sinh thái first-party** (do chính đội Laravel làm): công cụ dev local, server, deploy, giám sát
  queue, debug (mục 8).
- **Đứng trên vai Symfony**: Laravel dùng nhiều component của Symfony, một framework PHP lâu đời khác.
  Ví dụ lớp `Illuminate\Http\Request` kế thừa `Request` của `symfony/http-foundation`, và Artisan dựng
  trên `symfony/console` (bạn sẽ thấy `Symfony\Component\Console\Input\ArgvInput` trong file `artisan`
  ở mục 4.3).

So sánh nhanh với lựa chọn khác trong PHP (định tính, không phải xếp hạng):

| | Laravel | Symfony | Không framework / micro-framework (Slim...) |
|---|---|---|---|
| Triết lý | Convention over configuration, "đủ đồ" | Linh hoạt, cấu hình tường minh, từng component độc lập | Chỉ routing + middleware, còn lại tự chọn |
| Tốc độ bắt đầu | Nhanh | Trung bình | Nhanh với dự án nhỏ, chậm dần khi lớn |
| Truy cập DB mặc định | Eloquent (*Active Record*) | Doctrine (*Data Mapper*) | Tự chọn |
| Hợp với | Đa số web app, API, startup tới doanh nghiệp | Hệ thống lớn, cần kiểm soát chi tiết | Service rất nhỏ, học cơ chế |

*Active Record* và *Data Mapper* là hai cách ánh xạ bảng sang object; [Chương 27](27-laravel-database-eloquent.md)
giải thích.

⚠️ Đừng chọn framework vì "nhanh nhất trong benchmark". Phần lớn thời gian của một request web nằm ở
database và mạng; chênh lệch tốc độ khởi động framework thường nhỏ so với một câu query thiếu index.

## 2. Phiên bản, vòng đời phát hành và chính sách hỗ trợ

### 2.1 Laravel đánh số phiên bản thế nào

Laravel (và các package first-party của nó) theo *Semantic Versioning* (semver): số phiên bản có dạng
`MAJOR.MINOR.PATCH`, ví dụ `13.17.0`.

- `MAJOR` (13): tăng khi có thay đổi phá vỡ tương thích (*breaking change*). Laravel ra một bản lớn
  mỗi năm, khoảng quý 1.
- `MINOR` (17): thêm tính năng, không phá vỡ code cũ.
- `PATCH` (0): sửa lỗi.

Tài liệu chính thức viết: bản minor và patch có thể ra "thường xuyên tới mức hằng tuần" và "không bao
giờ được chứa breaking change". Vì vậy `composer.json` của dự án luôn khai báo ràng buộc kiểu caret,
ví dụ `"laravel/framework": "^13.0"`, nghĩa là chấp nhận mọi bản từ `13.0.0` tới dưới `14.0.0`
(ký hiệu `^` đã giải thích ở [Chương 11](11-namespace-composer.md)). Chạy `composer update` sẽ lấy bản
13.x mới nhất nhưng không bao giờ tự nhảy lên 14.

⚠️ Một ngoại lệ ít người biết: *named argument* ([Chương 08](08-ham.md)) không nằm trong cam kết
tương thích của Laravel. Đội Laravel có thể đổi tên tham số của một method trong bản minor. Nếu bạn
gọi `$x->method(foo: 1)` vào method của framework và tham số `foo` bị đổi tên, code hỏng dù chỉ nâng
bản minor. Gọi method của framework bằng tham số theo vị trí là an toàn hơn.

### 2.2 Chính sách hỗ trợ

Với mọi bản lớn, Laravel sửa lỗi (*bug fixes*) trong 18 tháng và vá bảo mật (*security fixes*) trong
2 năm kể từ ngày phát hành. Laravel không còn bản LTS (hỗ trợ dài hạn) riêng; bản nào cũng theo cùng
một chính sách. Bảng dưới chép từ trang Release Notes của tài liệu 13.x:

| Phiên bản | PHP hỗ trợ | Phát hành | Hết sửa lỗi | Hết vá bảo mật |
|---|---|---|---|---|
| 10 | 8.1 - 8.3 | 14/02/2023 | 06/08/2024 | 04/02/2025 |
| 11 | 8.2 - 8.4 | 12/03/2024 | 03/09/2025 | 12/03/2026 |
| 12 | 8.2 - 8.5 | 24/02/2025 | 13/08/2026 | 24/02/2027 |
| 13 | 8.3 - 8.5 | 17/03/2026 | Quý 3/2027 | 17/03/2028 |

Với các package first-party đi kèm (Horizon, Sanctum, Telescope...), chỉ bản lớn mới nhất được sửa
lỗi.

Đoạn code sau tính trạng thái hỗ trợ của từng bản tại một ngày cho trước, để bạn tập đọc bảng (và ôn
`DateTimeImmutable` ở [Chương 14](14-file-json-thoi-gian.md)):

```php
<?php
declare(strict_types=1);

// Dữ liệu chép từ bảng Support Policy (laravel.com/docs/13.x/releases).
// Laravel 13 chỉ ghi "Q3 2027" cho mốc sửa lỗi nên để null (chưa có ngày cụ thể).
$versions = [
    10 => ['php' => '8.1 - 8.3', 'bugs' => '2024-08-06', 'security' => '2025-02-04'],
    11 => ['php' => '8.2 - 8.4', 'bugs' => '2025-09-03', 'security' => '2026-03-12'],
    12 => ['php' => '8.2 - 8.5', 'bugs' => '2026-08-13', 'security' => '2027-02-24'],
    13 => ['php' => '8.3 - 8.5', 'bugs' => null,         'security' => '2028-03-17'],
];

function status(?string $bugs, string $security, DateTimeImmutable $today): string
{
    if ($today > new DateTimeImmutable($security)) {
        return 'hết hỗ trợ (end of life)';
    }
    if ($bugs !== null && $today > new DateTimeImmutable($bugs)) {
        return 'chỉ còn vá bảo mật';
    }
    return 'còn sửa lỗi và vá bảo mật';
}

$today = new DateTimeImmutable('2026-10-01');
foreach ($versions as $major => $v) {
    printf("Laravel %d (PHP %s): %s\n", $major, $v['php'], status($v['bugs'], $v['security'], $today));
}
// in ra:
// Laravel 10 (PHP 8.1 - 8.3): hết hỗ trợ (end of life)
// Laravel 11 (PHP 8.2 - 8.4): hết hỗ trợ (end of life)
// Laravel 12 (PHP 8.2 - 8.5): chỉ còn vá bảo mật
// Laravel 13 (PHP 8.3 - 8.5): còn sửa lỗi và vá bảo mật
```

Ý nghĩa thực tế ở thời điểm 10/2026:

- Dự án mới: dùng Laravel 13 (cần PHP 8.3 trở lên; nên dùng PHP 8.4 hoặc 8.5).
- Dự án đang chạy Laravel 12: vẫn an toàn về bảo mật tới 24/02/2027, nhưng nên lên 13 sớm.
- Dự án Laravel 11 hoặc cũ hơn: đã hết vá bảo mật. Một lỗ hổng mới phát hiện sẽ không được vá cho bản
  đó; đây là rủi ro thật, không chỉ là "cũ".

⚠️ Phiên bản Laravel và phiên bản PHP ràng buộc lẫn nhau. Laravel 10 chỉ hỗ trợ tới PHP 8.3, nên dự
án Laravel 10 muốn lên PHP 8.4 thì phải nâng Laravel trước. Ngược lại Laravel 13 đòi PHP 8.3 trở lên,
nên server còn PHP 8.2 phải nâng PHP trước. Vòng đời của PHP xem ở [Chương 01](01-php-la-gi.md). Hai
việc nâng cấp này thường phải lên kế hoạch cùng nhau.

### 2.3 Nâng cấp giữa các bản lớn

Mỗi bản lớn có một *Upgrade Guide* trên laravel.com liệt kê từng breaking change, xếp theo mức ảnh
hưởng (high, medium, low). Ví dụ hướng dẫn 12.x lên 13.0 ước lượng 10 phút cho một ứng dụng điển hình,
với ba mục ảnh hưởng cao: cập nhật dependency trong `composer.json` (`laravel/framework` lên `^13.0`,
`phpunit/phpunit` lên `^12.0`...), cập nhật Laravel installer, và thay đổi ở middleware chống giả mạo
request (`PreventRequestForgery`). Ngoài cách tự làm theo hướng dẫn, có dịch vụ cộng đồng
[Laravel Shift](https://laravelshift.com) và Laravel Boost (mục 8) hỗ trợ nâng cấp tự động.

Quy trình an toàn (chi tiết ở [Chương 22](22-phien-ban-moi.md) mục 9 cho PHP, áp dụng tương tự):
có test tốt, đọc kỹ phần high impact, chạy test và phân tích tĩnh, deploy lên staging trước. Một lời
khuyên thực tế (không phải quy định của Laravel): nếu cách nhiều bản lớn, hãy nâng lần lượt từng bản
(11 → 12 → 13), vì mỗi Upgrade Guide chỉ viết cho bước nhảy từ bản liền trước.

## 3. Cài đặt và tạo dự án đầu tiên

### 3.1 Cần gì trên máy

Theo tài liệu 13.x, để tạo và chạy một dự án Laravel trên máy dev bạn cần:

- PHP 8.3 trở lên, kèm các extension (danh sách lấy từ mục Server Requirements của tài liệu
  Deployment): Ctype, cURL, DOM, Fileinfo, Filter, Hash, Mbstring, OpenSSL,
  PCRE, PDO, Session, Tokenizer, XML. Đa số bản PHP cài qua trình quản lý gói đã có sẵn phần lớn.
  Kiểm tra bằng `php -v` và `php -m` (liệt kê extension đã nạp).
- Composer ([Chương 11](11-namespace-composer.md)).
- Laravel installer (lệnh `laravel`), không bắt buộc nhưng tiện.
- Node.js và npm (hoặc Bun) để build CSS/JS phía frontend bằng Vite. Nếu chỉ làm API thuần thì có
  thể chưa cần: khi tạo dự án, installer hỏi có chạy `npm install` và build không, hoặc bỏ qua hẳn
  bằng tuỳ chọn `--no-node`.

Tài liệu đưa ra cách cài nhanh cả PHP, Composer và Laravel installer bằng một lệnh qua trang
`php.new`. Trên macOS (chạy trong Terminal):

```shell
/bin/bash -c "$(curl -fsSL https://php.new/install/mac/8.5)"
```

(Linux thay `mac` bằng `linux`; Windows có lệnh PowerShell riêng trong tài liệu.) Sau đó mở lại
terminal. Nếu đã có PHP và Composer, chỉ cần cài installer:

```shell
composer global require laravel/installer
```

⚠️ Lệnh `composer global require` cài vào thư mục "global" của Composer (thường là
`~/.composer/vendor/bin` hoặc `~/.config/composer/vendor/bin`). Nếu gõ `laravel` báo "command not
found", nghĩa là thư mục `vendor/bin` đó chưa có trong biến môi trường `PATH`. Xem đường dẫn thật bằng
`composer global config bin-dir --absolute`.

⚠️ Đừng chạy `curl ... | bash` một cách mù quáng với URL bất kỳ: lệnh đó chạy code tải từ Internet
với quyền của bạn. Chỉ làm với nguồn bạn tin (ở đây là trang được tài liệu chính thức chỉ tới).

Không muốn cài PHP lên máy? Có hai lựa chọn: Laravel Herd (ứng dụng đồ hoạ cho macOS/Windows, cài sẵn
PHP, Nginx, Composer, Node) và Laravel Sail (chạy mọi thứ trong Docker). Cả hai giới thiệu ở mục 8.

### 3.2 Tạo dự án: `laravel new` và `composer create-project`

Có hai lệnh, kết quả cơ bản giống nhau:

```shell
# Cách 1: Laravel installer (hỏi tương tác: starter kit, database, Pest hay PHPUnit...)
laravel new example-app

# Cách 2: chỉ dùng Composer (không hỏi gì, tạo dự án trắng)
composer create-project laravel/laravel example-app
```

Chúng liên quan thế nào? Đọc mã nguồn installer ([laravel/installer](https://github.com/laravel/installer))
sẽ thấy: khi bạn không chọn starter kit, `laravel new` thực chất chạy
`composer create-project laravel/laravel ...` bên dưới (với `--no-scripts`, rồi tự chạy các bước khởi
tạo tương đương ở mục 3.3); khi chọn starter kit, nó `create-project` từ package của starter kit đó.
Sau đó installer làm thêm các bước tuỳ chọn: đổi database, cài Pest, khởi tạo git, cài Laravel Boost,
chạy `npm install`. Một số tuỳ chọn hữu ích của installer:

| Tuỳ chọn | Ý nghĩa |
|---|---|
| `--database=mysql` | Chọn database (`mysql`, `mariadb`, `pgsql`, `sqlite`, `sqlsrv`) thay vì hỏi |
| `--react`, `--vue`, `--svelte`, `--livewire` | Dùng starter kit tương ứng (có sẵn đăng ký, đăng nhập) |
| `--pest`, `--phpunit` | Chọn framework test |
| `--git` | Khởi tạo git repository |
| `--no-node` | Bỏ qua cài và build npm |
| `--boost`, `--no-boost` | Cài hoặc bỏ qua Laravel Boost |

*Starter kit* là bộ khung có sẵn route, controller, view cho đăng ký, đăng nhập, quên mật khẩu, dùng
Laravel Fortify phía backend và React, Vue, Svelte (qua Inertia) hoặc Livewire phía frontend. Không bắt
buộc dùng; người học nên tạo một dự án trắng trước để nhìn rõ cấu trúc gốc.

`laravel/laravel` là gì? Đó là package *skeleton* (bộ khung ứng dụng) trên Packagist, có
`"type": "project"`. Nó gần như không chứa logic; nó chỉ chứa cấu trúc thư mục, file cấu hình, và khai
báo phụ thuộc vào `laravel/framework`, nơi chứa toàn bộ code của framework. Đây là điểm người mới hay
nhầm:

```
laravel/laravel   (skeleton, copy MỘT LẦN vào dự án của bạn, từ đó là code của bạn)
   └─ composer.json: "require": { "laravel/framework": "^13.17", ... }
                                        │
                                        ▼
laravel/framework (thư viện, nằm trong vendor/, cập nhật bằng composer update)
```

Hệ quả: khi Laravel ra bản 13.20, `composer update` cập nhật `vendor/laravel/framework` nhưng không
động tới các file skeleton đã copy vào dự án (như `config/app.php`). Đó là lý do khi nâng bản lớn, đôi
khi bạn phải tự sửa file trong `config/` hay `bootstrap/` theo Upgrade Guide.

### 3.3 Chuyện gì xảy ra ngay sau lệnh tạo dự án

`composer create-project` chạy các *script* khai báo trong `composer.json` của skeleton. Trích từ
skeleton 13.x:

```json
"post-root-package-install": [
    "@php -r \"file_exists('.env') || copy('.env.example', '.env');\""
],
"post-create-project-cmd": [
    "@php artisan key:generate --ansi",
    "@php -r \"file_exists('database/database.sqlite') || touch('database/database.sqlite');\"",
    "@php artisan migrate --graceful --ansi"
],
```

Đọc từng dòng:

1. Copy `.env.example` thành `.env` nếu chưa có (file cấu hình theo môi trường, mục 5).
2. `php artisan key:generate`: sinh khoá mã hoá ngẫu nhiên và ghi vào dòng `APP_KEY=` trong `.env`.
3. Tạo file rỗng `database/database.sqlite`, vì mặc định dự án mới dùng SQLite (`DB_CONNECTION=sqlite`).
4. `php artisan migrate`: tạo các bảng mặc định (`users`, `cache`, `jobs`...) trong file SQLite đó.

Nhờ vậy dự án mới chạy được ngay mà không cần cài MySQL. Khi chuyển sang MySQL bạn sửa các biến `DB_*`
trong `.env`, tự tạo database rồi chạy lại `php artisan migrate` (mục 5.2).

### 3.4 Chạy thử

Trong thư mục dự án:

```shell
cd example-app
npm install && npm run build   # build CSS/JS một lần
composer run dev               # chạy các tiến trình dev
```

Mở `http://localhost:8000`, bạn sẽ thấy trang chào mừng của Laravel. Trong skeleton 13.x, script
`dev` trong `composer.json` gọi lệnh `php artisan dev`; theo tài liệu Artisan 13.x, lệnh này chạy đồng
thời trong một cửa sổ terminal: server dev của PHP, một queue worker, xem log trực tiếp (Laravel Pail)
và Vite (build lại CSS/JS khi bạn sửa).

Nếu chỉ cần web server, dùng:

```shell
php artisan serve              # mặc định 127.0.0.1:8000
```

`php artisan serve` dùng web server tích hợp của PHP (`php -S`, đã gặp ở [Chương 01](01-php-la-gi.md)),
trỏ document root vào thư mục `public/`.

⚠️ `php artisan serve` chỉ dành cho dev. Server tích hợp của PHP không được thiết kế cho production;
production dùng Nginx + PHP-FPM ([Chương 18](18-fpm-nginx-opcache.md)), hoặc Octane (mục 8).

Thử sửa route đầu tiên. Mở `routes/web.php` (nội dung nguyên bản):

```php
<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return view('welcome');
});
```

Thêm vào cuối file:

```php
Route::get('/xin-chao/{ten}', function (string $ten) {
    return "Xin chào {$ten}";
});
```

Truy cập `http://localhost:8000/xin-chao/An`, trình duyệt hiện `Xin chào An`. Không cần khởi động lại
server: mỗi request PHP đọc lại code (xem [Chương 02](02-php-chay-nhu-the-nao.md)). Routing chi tiết ở
[Chương 24](24-laravel-routing-controller-middleware.md).

⚠️ Ví dụ trên trả chuỗi có dữ liệu người dùng mà không escape, chỉ để minh hoạ. Trong view thật bạn dùng
Blade `{{ $ten }}`, vốn tự escape HTML ([Chương 25](25-laravel-request-validation-response.md)).

## 4. Cấu trúc thư mục của một dự án Laravel

### 4.1 Toàn cảnh

Dưới đây là cây thư mục của skeleton `laravel/laravel` nhánh 13.x (đã bỏ bớt file phụ như
`.editorconfig`, `.gitattributes`, `.github/`, các file `.gitignore` con), cộng thêm `vendor/`,
`node_modules/` và `.env` sinh ra sau khi cài:

```
example-app/
├── app/                      ← code của bạn (namespace App\)
│   ├── Http/
│   │   └── Controllers/
│   │       └── Controller.php
│   ├── Models/
│   │   └── User.php
│   └── Providers/
│       └── AppServiceProvider.php
├── bootstrap/
│   ├── app.php               ← cấu hình và khởi tạo ứng dụng (routing, middleware, exception)
│   ├── providers.php         ← danh sách service provider của bạn
│   └── cache/                ← file cache do framework sinh (config, route, services...)
├── config/                   ← file cấu hình: app.php, auth.php, cache.php, database.php,
│                               filesystems.php, logging.php, mail.php, queue.php,
│                               services.php, session.php
├── database/
│   ├── factories/UserFactory.php
│   ├── migrations/           ← 3 migration mặc định (users, cache, jobs)
│   ├── seeders/DatabaseSeeder.php
│   └── database.sqlite       ← sinh ra khi cài (mục 3.3)
├── public/                   ← DOCUMENT ROOT: thư mục duy nhất web server được phép phục vụ
│   ├── index.php             ← cửa vào của MỌI request HTTP
│   ├── .htaccess, favicon.ico, robots.txt
│   └── build/                ← CSS/JS do Vite build ra
├── resources/
│   ├── css/app.css, js/app.js   ← asset nguồn (chưa build)
│   └── views/welcome.blade.php  ← view Blade
├── routes/
│   ├── web.php               ← route web
│   └── console.php           ← lệnh Artisan dạng closure và lịch chạy (schedule)
├── storage/
│   ├── app/{private,public}/ ← file ứng dụng lưu (upload...)
│   ├── framework/{cache,sessions,views,testing}/
│   └── logs/                 ← laravel.log
├── tests/
│   ├── Feature/ExampleTest.php
│   ├── Unit/ExampleTest.php
│   └── TestCase.php
├── vendor/                   ← dependency Composer (KHÔNG commit)
├── node_modules/             ← dependency npm (KHÔNG commit)
├── .env                      ← cấu hình theo môi trường (KHÔNG commit)
├── .env.example              ← mẫu .env (CÓ commit)
├── artisan                   ← cửa vào của mọi lệnh CLI
├── composer.json, composer.lock
├── package.json, vite.config.js
└── phpunit.xml
```

Hai file "cửa vào" (*entry point*) đáng nhớ nhất: `public/index.php` cho HTTP và `artisan` cho dòng
lệnh. Cả hai đều nạp autoloader của Composer rồi lấy đối tượng ứng dụng từ `bootstrap/app.php`.

Tài liệu nhấn mạnh: cấu trúc mặc định chỉ là điểm khởi đầu tốt, Laravel "gần như không ràng buộc
class nào phải nằm ở đâu, miễn là Composer autoload được". Bạn có thể thêm `app/Services`,
`app/Actions`, `app/Enums`... tuỳ ý.

### 4.2 Các thư mục ở gốc

**`app/`** chứa gần như toàn bộ class của bạn. Nó ứng với namespace `App\` qua autoload PSR-4 khai
báo trong `composer.json`:

```json
"autoload": {
    "psr-4": {
        "App\\": "app/",
        "Database\\Factories\\": "database/factories/",
        "Database\\Seeders\\": "database/seeders/"
    }
},
```

Nên class `App\Http\Controllers\PostController` phải nằm ở `app/Http/Controllers/PostController.php`
(quy tắc PSR-4, [Chương 11](11-namespace-composer.md)). Chi tiết từng thư mục con ở mục 4.6.

**`bootstrap/`** chứa `app.php` (khởi tạo ứng dụng, mục 4.4), `providers.php` (danh sách service
provider) và thư mục `cache/`, nơi framework ghi các file tối ưu hiệu năng như cache cấu hình
(`bootstrap/cache/config.php`), cache route, cache danh sách service và package.

**`config/`** chứa các file cấu hình, mỗi file trả về một mảng PHP (mục 5). Skeleton 13.x có sẵn 10
file. Một số file ít khi phải sửa (như `cors.php`, `view.php`) không được đặt sẵn; khi cần sửa, bạn
"publish" chúng ra bằng `php artisan config:publish`.

**`database/`** chứa *migration* (file PHP mô tả thay đổi schema theo thứ tự thời gian), *factory*
(sinh dữ liệu giả cho test), *seeder* (đổ dữ liệu mẫu), và có thể chứa file SQLite. Chi tiết ở
[Chương 27](27-laravel-database-eloquent.md).

**`public/`** là *document root*: thư mục mà web server (Nginx, Apache) được cấu hình để phục vụ ra
Internet. Nó chứa `index.php` và file tĩnh (ảnh, CSS, JS đã build). Mọi request không trỏ tới file tĩnh
có thật đều được web server chuyển cho `public/index.php` (file `.htaccess` làm việc này với Apache;
với Nginx là dòng `try_files`, xem [Chương 18](18-fpm-nginx-opcache.md)).

**`resources/`** chứa view Blade và asset chưa build (CSS, JS nguồn), có thể có file dịch.

**`routes/`** chứa định nghĩa route:

- `web.php`: route cho trình duyệt. Tài liệu mô tả: các route này nằm trong *middleware group* `web`,
  có session, chống CSRF, mã hoá cookie.
- `console.php`: lệnh Artisan viết bằng closure và lịch chạy định kỳ ([Chương 29](29-laravel-queue-event-schedule-cache.md)).
- `api.php` (không có sẵn): route API *stateless* (không session), thường xác thực bằng token. Tạo
  bằng `php artisan install:api`, lệnh này cài thêm Laravel Sanctum.
- `channels.php` (không có sẵn): kênh broadcast realtime, tạo bằng `php artisan install:broadcasting`.

**`storage/`** chứa mọi thứ framework và ứng dụng ghi ra lúc chạy:

- `storage/logs/`: log (mặc định `laravel.log`).
- `storage/framework/`: view Blade đã biên dịch, session dạng file, cache dạng file.
- `storage/app/`: file ứng dụng lưu, chia `private/` và `public/`. Muốn file trong
  `storage/app/public` truy cập được từ web (ví dụ ảnh đại diện), chạy `php artisan storage:link` để
  tạo symlink `public/storage` → `storage/app/public`.

**`tests/`** chứa test Pest hoặc PHPUnit, chia `Feature/` (test qua HTTP, nhiều thành phần) và `Unit/`
([Chương 30](30-laravel-testing-octane-deploy.md)).

**`vendor/`** là dependency do Composer cài, trong đó có `vendor/laravel/framework`.

⚠️ Hai thư mục `storage/` và `bootstrap/cache/` phải ghi được bởi user chạy PHP (ví dụ `www-data` của
PHP-FPM). Đây là nguyên nhân số một của lỗi "trang trắng" hoặc "Permission denied ... laravel.log"
khi deploy lần đầu: tiến trình PHP không ghi được log, không ghi được view đã biên dịch.

⚠️ Đừng bao giờ cấu hình web server phục vụ thư mục gốc của dự án thay cho `public/`, và đừng chuyển
`index.php` ra gốc. Tài liệu cảnh báo rõ điều này sẽ phơi các file nhạy cảm ra Internet: ai cũng có
thể tải `.env` (mật khẩu database, `APP_KEY`), `composer.json`, `storage/logs/laravel.log`. Cũng không
nên phục vụ Laravel từ một thư mục con của document root (kiểu `example.com/myapp/public`); hãy cho
mỗi ứng dụng một document root trỏ thẳng vào `public/`.

### 4.3 Hai cửa vào: `public/index.php` và `artisan`

Nội dung nguyên bản `public/index.php` (skeleton 13.x):

```php
<?php

use Illuminate\Foundation\Application;
use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

// Determine if the application is in maintenance mode...
if (file_exists($maintenance = __DIR__.'/../storage/framework/maintenance.php')) {
    require $maintenance;
}

// Register the Composer autoloader...
require __DIR__.'/../vendor/autoload.php';

// Bootstrap Laravel and handle the request...
/** @var Application $app */
$app = require_once __DIR__.'/../bootstrap/app.php';

$app->handleRequest(Request::capture());
```

Đọc từng bước:

1. Ghi lại thời điểm bắt đầu (`LARAVEL_START`), dùng để đo thời gian xử lý.
2. Nếu đang ở chế độ bảo trì (có file `storage/framework/maintenance.php`, do `php artisan down`
   tạo ra), nạp file đó. Nó có thể trả trang 503 ngay mà chưa cần khởi động framework (mục 7.4).
3. Nạp autoloader của Composer. Từ đây mọi class trong `vendor/` và `app/` tự nạp khi dùng.
4. Lấy đối tượng ứng dụng (`Application`) từ `bootstrap/app.php`.
5. `Request::capture()` gom `$_GET`, `$_POST`, `$_COOKIE`, `$_FILES`, `$_SERVER` thành một object
   `Request`; `handleRequest()` đưa nó qua HTTP kernel, middleware, router, controller, rồi gửi response
   về trình duyệt.

File `artisan` ở gốc dự án có cấu trúc gần như y hệt, chỉ khác dòng cuối:

```php
#!/usr/bin/env php
<?php

use Illuminate\Foundation\Application;
use Symfony\Component\Console\Input\ArgvInput;

define('LARAVEL_START', microtime(true));

// Register the Composer autoloader...
require __DIR__.'/vendor/autoload.php';

// Bootstrap Laravel and handle the command...
/** @var Application $app */
$app = require_once __DIR__.'/bootstrap/app.php';

$status = $app->handleCommand(new ArgvInput);

exit($status);
```

`ArgvInput` đọc tham số dòng lệnh (`$argv`), `handleCommand()` chạy lệnh qua *console kernel* và trả
về *exit code* (0 là thành công). Dòng đầu `#!/usr/bin/env php` (*shebang*) cho phép chạy `./artisan`
trực tiếp trên Linux/macOS, nhưng cách thông dụng là `php artisan ...`.

Luồng tổng quát:

```
 Trình duyệt ──HTTP──▶ Nginx ──FastCGI──▶ PHP-FPM ──▶ public/index.php ─┐
                                                                       ├─▶ vendor/autoload.php
 Terminal ──"php artisan migrate"──▶ artisan ──────────────────────────┤
                                                                       └─▶ bootstrap/app.php
                                                                              │ tạo Application
                                                       ┌──────────────────────┴───────────────┐
                                                       ▼                                      ▼
                                          handleRequest(Request)                handleCommand(ArgvInput)
                                          HTTP kernel → middleware              Console kernel → lệnh
                                          → router → controller → Response      → exit code
```

Vòng đời một request ở mức chi tiết (bootstrapper, service provider `register`/`boot`, middleware)
là nội dung của [Chương 26](26-laravel-container-provider-facade.md).

### 4.4 `bootstrap/app.php`: trung tâm cấu hình ứng dụng

Từ Laravel 11, `bootstrap/app.php` là nơi bạn cấu hình các hành vi cấp ứng dụng bằng code: route,
middleware, xử lý exception. Nội dung nguyên bản (skeleton 13.x):

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
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        //
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(
            fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
        );
    })->create();
```

Đây là kiểu *fluent interface* (method chaining): mỗi method `with...()` trả về chính builder để gọi
tiếp, `create()` cuối cùng trả về đối tượng `Application`. File này `return` giá trị đó, nên ở
`index.php` mới viết được `$app = require_once .../bootstrap/app.php` (`require` trả về giá trị
`return` của file, [Chương 11](11-namespace-composer.md)).

- `Application::configure(basePath: ...)`: tạo ứng dụng với thư mục gốc là cha của `bootstrap/`
  (`dirname(__DIR__)`). Bên trong nó cũng đăng ký sẵn kernel, event, command, và nạp danh sách
  provider từ `bootstrap/providers.php`.
- `withRouting(...)`: khai báo file route web, file lệnh console, và *health route* `/up`. Theo tài liệu
  deploy, `/up` trả HTTP 200 nếu ứng dụng khởi động không có exception, ngược lại trả 500; dùng cho
  uptime monitor, load balancer hay Kubernetes. Khi thêm `routes/api.php` bằng `install:api`, dòng
  `api: __DIR__.'/../routes/api.php'` được thêm vào đây.
- `withMiddleware(...)`: tuỳ chỉnh middleware toàn cục và middleware group
  ([Chương 24](24-laravel-routing-controller-middleware.md)).
- `withExceptions(...)`: tuỳ chỉnh cách báo cáo và hiển thị exception. Skeleton 13.x cấu hình sẵn: trả
  lỗi dạng JSON khi URL bắt đầu bằng `api/` hoặc khi client yêu cầu JSON (header `Accept`).

File `bootstrap/providers.php` liệt kê service provider của ứng dụng:

```php
<?php

use App\Providers\AppServiceProvider;

return [
    AppServiceProvider::class,
];
```

*Service provider* là class "khởi động" một phần của ứng dụng: đăng ký service vào container, cấu hình
thứ cần cấu hình lúc khởi động. Dự án mới chỉ có `AppServiceProvider` với hai method rỗng `register()`
và `boot()`. Khi bạn tạo provider mới bằng `php artisan make:provider`, Laravel tự thêm nó vào mảng
này. Container và provider là chủ đề của [Chương 26](26-laravel-container-provider-facade.md).

### 4.5 Laravel 11 đã đổi cấu trúc thế nào (để đọc được dự án cũ)

Ngoài kia rất nhiều dự án tạo từ Laravel 10 trở về trước. Laravel 11 giới thiệu cấu trúc tinh gọn cho
dự án **mới**, và nói rõ là không bắt buộc dự án cũ phải đổi. Nên một dự án đã nâng lên Laravel 13 vẫn
có thể mang cấu trúc kiểu cũ. Bảng đối chiếu:

| Việc | Laravel 10 trở về trước | Laravel 11 trở đi |
|---|---|---|
| Middleware toàn cục và group | `app/Http/Kernel.php` | `withMiddleware()` trong `bootstrap/app.php` |
| Middleware mặc định (CSRF, trim string...) | 9 file trong `app/Http/Middleware/` | Nằm trong framework, tuỳ chỉnh qua `bootstrap/app.php` |
| Lịch chạy định kỳ (schedule) | `app/Console/Kernel.php` | `routes/console.php` (facade `Schedule`) |
| Xử lý exception | `app/Exceptions/Handler.php` | `withExceptions()` trong `bootstrap/app.php` |
| Service provider mặc định | 5 provider (App, Auth, Broadcast, Event, Route) | Chỉ `AppServiceProvider` |
| Đăng ký provider | Mảng `providers` trong `config/app.php` | `bootstrap/providers.php` |
| `routes/api.php`, `routes/channels.php` | Có sẵn | Tạo khi cần (`install:api`, `install:broadcasting`) |
| Database mặc định | MySQL | SQLite |

⚠️ Khi đọc tutorial hoặc câu trả lời trên mạng, xem nó viết cho bản nào. Hướng dẫn "thêm middleware vào
`app/Http/Kernel.php`" là của Laravel 10; trên dự án mới, file đó không tồn tại.

### 4.6 Bên trong `app/`

Dự án mới chỉ có `app/Http`, `app/Models`, `app/Providers`. Các thư mục khác tự xuất hiện khi bạn
chạy lệnh `make:` tương ứng. Tài liệu ví dụ: `app/Console` chưa tồn tại cho tới khi bạn chạy
`make:command`.

| Thư mục | Chứa gì | Lệnh tạo | Học ở |
|---|---|---|---|
| `Http/Controllers` | Controller | `make:controller` | [Ch. 24](24-laravel-routing-controller-middleware.md) |
| `Http/Middleware` | Middleware của bạn | `make:middleware` | [Ch. 24](24-laravel-routing-controller-middleware.md) |
| `Http/Requests` | Form request (validation) | `make:request` | [Ch. 25](25-laravel-request-validation-response.md) |
| `Models` | Model Eloquent | `make:model` | [Ch. 27](27-laravel-database-eloquent.md) |
| `Providers` | Service provider | `make:provider` | [Ch. 26](26-laravel-container-provider-facade.md) |
| `Console/Commands` | Lệnh Artisan dạng class | `make:command` | mục 7.5 |
| `Policies` | Quy tắc phân quyền | `make:policy` | [Ch. 28](28-laravel-auth.md) |
| `Jobs` | Job đưa vào queue | `make:job` | [Ch. 29](29-laravel-queue-event-schedule-cache.md) |
| `Events`, `Listeners` | Sự kiện và bộ xử lý | `make:event`, `make:listener` | [Ch. 29](29-laravel-queue-event-schedule-cache.md) |
| `Mail`, `Notifications` | Email, thông báo | `make:mail`, `make:notification` | [Ch. 29](29-laravel-queue-event-schedule-cache.md) |
| `Exceptions` | Exception tự định nghĩa | `make:exception` | [Ch. 12](12-loi-exception.md) |
| `Rules` | Quy tắc validation tự viết | `make:rule` | [Ch. 25](25-laravel-request-validation-response.md) |
| `Broadcasting` | Kênh broadcast | `make:channel` | |

Tài liệu có một nhận xét đáng nhớ: `Http` và `Console` là hai "cổng" để ra lệnh cho ứng dụng (qua
HTTP và qua dòng lệnh), chúng không nên chứa logic nghiệp vụ. Controller và command nên mỏng: nhận
input, gọi tới phần nghiệp vụ, trả kết quả. Nhờ vậy cùng một nghiệp vụ (ví dụ "tạo đơn hàng") có thể
được gọi từ controller, từ command, từ job mà không lặp code.

## 5. Cấu hình: `.env`, `env()`, `config()` và `config:cache`

### 5.1 Vì sao cấu hình phải tách khỏi code

Cùng một code chạy ở nhiều nơi: máy dev của bạn, máy đồng nghiệp, server staging, server production.
Mỗi nơi có database khác, mật khẩu khác, mức log khác, có nơi bật debug có nơi không. Nếu ghi cứng
`'password' => 'secret123'` vào code thì:

- muốn đổi phải sửa code và deploy lại;
- mật khẩu production nằm trong git, ai đọc được repo là có mật khẩu.

Giải pháp phổ biến (được nhóm nguyên tắc *Twelve-Factor App* khuyến nghị): code giữ nguyên, phần khác
nhau giữa các môi trường lấy từ *biến môi trường* (*environment variable*) của hệ điều hành. Laravel
hiện thực điều này qua hai tầng:

```
 .env  (KHÔNG commit)          config/*.php  (CÓ commit)               Code của bạn
 ┌──────────────────────┐      ┌─────────────────────────────────┐      ┌──────────────────────────┐
 │ DB_HOST=10.0.0.5     │─────▶│ 'host' => env('DB_HOST',        │─────▶│ config('database.        │
 │ DB_PASSWORD=s3cr3t   │ env()│            '127.0.0.1'),        │config│   connections.mysql.host')│
 │ APP_DEBUG=false      │      │ 'debug' => (bool) env('APP_DEBUG│  ()  │                          │
 └──────────────────────┘      │            ', false),           │      └──────────────────────────┘
   biến môi trường thật         └─────────────────────────────────┘
   của server cũng vào đây       chỉ ở ĐÂY mới gọi env()                 ở mọi chỗ khác dùng config()
```

Quy tắc vàng, học thuộc ngay từ đầu: **`env()` chỉ gọi trong các file `config/*.php`. Mọi nơi khác
dùng `config()`**. Mục 5.5 giải thích vì sao.

### 5.2 File `.env`

`.env` là file văn bản ở gốc dự án, mỗi dòng một cặp `TÊN=giá_trị`. Laravel dùng thư viện
[vlucas/phpdotenv](https://github.com/vlucas/phpdotenv) để đọc nó. Trích `.env.example` của skeleton
13.x:

```ini
APP_NAME=Laravel
APP_ENV=local
APP_KEY=
APP_DEBUG=true
APP_URL=http://localhost:8000

LOG_CHANNEL=stack
LOG_LEVEL=debug

DB_CONNECTION=sqlite
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_DATABASE=laravel
# DB_USERNAME=root
# DB_PASSWORD=

SESSION_DRIVER=database
QUEUE_CONNECTION=database
CACHE_STORE=database

MAIL_MAILER=log
MAIL_FROM_ADDRESS="hello@example.com"
MAIL_FROM_NAME="${APP_NAME}"
```

Vài điểm cú pháp:

- Dòng bắt đầu bằng `#` là comment.
- Giá trị có khoảng trắng phải đặt trong nháy kép: `APP_NAME="My Application"`.
- `"${APP_NAME}"` tham chiếu tới biến khác đã khai báo trước đó, nên `MAIL_FROM_NAME` sẽ là `Laravel`.
- Nếu `.env` sai cú pháp, Laravel dừng ngay và in `The environment file is invalid!` kèm thông báo lỗi.

Để dùng MySQL thay SQLite, sửa thành (giá trị lấy từ tài liệu cài đặt):

```ini
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=laravel
DB_USERNAME=root
DB_PASSWORD=
```

rồi tự tạo database `laravel` trong MySQL và chạy `php artisan migrate`.

Hai file, hai vai trò:

| | `.env` | `.env.example` |
|---|---|---|
| Chứa | Giá trị thật của máy này (mật khẩu thật) | Danh sách biến cần có, giá trị mẫu hoặc rỗng |
| Commit vào git | Không (skeleton đã có `.env` trong `.gitignore`) | Có |
| Ai tạo | Copy từ `.env.example` khi cài, rồi sửa | Đội dự án duy trì |

⚠️ Thêm một biến mới vào `.env` của bạn thì nhớ thêm nó (với giá trị rỗng hoặc mẫu) vào `.env.example`.
Nếu không, đồng nghiệp pull code về sẽ chạy thiếu biến và gặp lỗi khó hiểu.

⚠️ Biến môi trường thật của hệ điều hành (đặt qua Docker, systemd, PHP-FPM `env[...]`, nền tảng
hosting) được ưu tiên hơn giá trị trong `.env`. Tài liệu ghi: mọi biến trong `.env` đều có thể bị ghi
đè bởi biến môi trường bên ngoài. Bên trong, Laravel tạo kho biến môi trường của phpdotenv ở chế độ
*immutable*: biến đã tồn tại thì `.env` không ghi đè. Khi "sửa `.env` mà không thấy tác dụng", hãy kiểm
tra xem server có đặt biến cùng tên không (và kiểm tra config cache, mục 5.5).

### 5.3 Hàm `env()` và kiểu dữ liệu

`env('TÊN', mặc_định)` đọc một biến môi trường; tham số thứ hai là giá trị trả về khi biến không tồn
tại. Vì file `.env` là văn bản, mọi giá trị đọc ra là chuỗi, trừ vài từ khoá đặc biệt được tài liệu
quy định:

| Giá trị trong `.env` | `env()` trả về |
|---|---|
| `true` hoặc `(true)` | `true` (bool) |
| `false` hoặc `(false)` | `false` (bool) |
| `empty` hoặc `(empty)` | `''` (chuỗi rỗng) |
| `null` hoặc `(null)` | `null` |

Ví dụ sau chép lại (rút gọn) logic chuyển đổi trong `Illuminate\Support\Env` của Laravel 13.x để bạn
chạy thử bằng PHP thuần:

```php
<?php
declare(strict_types=1);

// Mô phỏng cách env() của Laravel chuyển chuỗi trong .env thành giá trị PHP.
// Logic chép lại từ Illuminate\Support\Env::getOption() (laravel/framework 13.x), rút gọn.
function convertEnvValue(string $value): string|bool|null
{
    switch (strtolower($value)) {
        case 'true':
        case '(true)':
            return true;
        case 'false':
        case '(false)':
            return false;
        case 'empty':
        case '(empty)':
            return '';
        case 'null':
        case '(null)':
            return null;
    }
    // Bỏ cặp nháy bao ngoài nếu còn sót
    if (preg_match('/\A([\'"])(.*)\1\z/', $value, $m) === 1) {
        return $m[2];
    }
    return $value;
}

foreach (['true', 'FALSE', '(null)', 'empty', '0', '1', '3306', 'My App'] as $raw) {
    echo str_pad("'$raw'", 10), ' => ', var_export(convertEnvValue($raw), true), "\n";
}
// in ra:
// 'true'     => true
// 'FALSE'    => false
// '(null)'   => NULL
// 'empty'    => ''
// '0'        => '0'
// '1'        => '1'
// '3306'     => '3306'
// 'My App'   => 'My App'

echo "---\n";
// Vì sao config/app.php viết (bool) env('APP_DEBUG', false)?
var_dump((bool) convertEnvValue('0'));      // APP_DEBUG=0  → in ra: bool(false)
var_dump((bool) convertEnvValue('1'));      // APP_DEBUG=1  → in ra: bool(true)
var_dump(convertEnvValue('3306') === 3306); // in ra: bool(false), DB_PORT luôn là string
```

Rút ra:

- Từ khoá không phân biệt hoa thường (`FALSE` cũng thành `false`), vì code dùng `strtolower`.
- Số vẫn là chuỗi: `DB_PORT=3306` cho ra `'3306'`. Với `strict_types=1`, truyền nó vào tham số `int`
  sẽ lỗi; cần ép kiểu `(int)` hoặc dùng accessor có kiểu (mục 5.4).
- Đó là lý do `config/app.php` viết `'debug' => (bool) env('APP_DEBUG', false)`: để `APP_DEBUG=1` hay
  `APP_DEBUG=0` cũng cho ra bool đúng.

### 5.4 Thư mục `config/` và hàm `config()`

Mỗi file trong `config/` trả về một mảng PHP. Trích `config/app.php` của skeleton 13.x (bỏ comment):

```php
<?php

return [
    'name' => env('APP_NAME', 'Laravel'),
    'env' => env('APP_ENV', 'production'),
    'debug' => (bool) env('APP_DEBUG', false),
    'url' => env('APP_URL', 'http://localhost'),
    'timezone' => 'UTC',
    'locale' => env('APP_LOCALE', 'en'),
    'fallback_locale' => env('APP_FALLBACK_LOCALE', 'en'),
    'faker_locale' => env('APP_FAKER_LOCALE', 'en_US'),
    'cipher' => 'AES-256-CBC',
    'key' => env('APP_KEY'),
    'previous_keys' => [
        ...array_filter(
            explode(',', (string) env('APP_PREVIOUS_KEYS', ''))
        ),
    ],
    'maintenance' => [
        'driver' => env('APP_MAINTENANCE_DRIVER', 'file'),
        'store' => env('APP_MAINTENANCE_STORE', 'database'),
    ],
];
```

Để ý các giá trị mặc định là giá trị an toàn cho production: thiếu `APP_ENV` thì coi là
`production`, thiếu `APP_DEBUG` thì `false`. Thiếu biến thì ứng dụng nghiêng về phía an toàn chứ không
lộ thông tin.

Đọc cấu hình ở bất kỳ đâu bằng hàm `config()` hoặc facade `Config`, với cú pháp *dot notation*: phần
đầu là tên file, các phần sau là khoá lồng nhau.

```php
use Illuminate\Support\Facades\Config;

$tz = config('app.timezone');                       // 'UTC'
$tz = Config::get('app.timezone');                  // cùng kết quả
$tz = config('app.timezone', 'Asia/Ho_Chi_Minh');   // mặc định nếu khoá không tồn tại
$host = config('database.connections.mysql.host');  // file database.php, khoá lồng 3 tầng

// Đặt giá trị lúc chạy (chỉ có tác dụng trong request/tiến trình hiện tại, không ghi ra file)
config(['app.timezone' => 'Asia/Ho_Chi_Minh']);
Config::set('app.timezone', 'Asia/Ho_Chi_Minh');
```

Hỗ trợ phân tích tĩnh, facade `Config` có các method lấy giá trị có kiểu; nếu giá trị không đúng kiểu
sẽ ném exception thay vì âm thầm trả sai kiểu:

```php
Config::string('app.name');
Config::integer('queue.connections.redis.retry_after');
Config::boolean('app.debug');
Config::array('app.previous_keys');
// còn có Config::float(), Config::collection()
```

Muốn thêm cấu hình riêng, tạo file mới, ví dụ `config/payment.php`:

```php
<?php

return [
    'provider' => env('PAYMENT_PROVIDER', 'stripe'),
    'key' => env('PAYMENT_KEY'),
    'timeout_seconds' => (int) env('PAYMENT_TIMEOUT', 10),
];
```

rồi đọc bằng `config('payment.key')`. Laravel tự nạp mọi file trong `config/`.

Hai lệnh để xem cấu hình đang có hiệu lực (rất hữu ích khi debug "sao config không như mình nghĩ"):

```shell
php artisan about                    # tổng quan: phiên bản, môi trường, driver cache/queue/session...
php artisan about --only=environment # chỉ một phần
php artisan config:show database     # toàn bộ giá trị của config/database.php sau khi đã đọc env
```

### 5.5 `config:cache` và cái bẫy kinh điển

Mỗi request, Laravel phải đọc file `.env`, rồi `require` từng file trong `config/` (mỗi file gọi
`env()` nhiều lần). Lệnh sau gộp tất cả thành một file duy nhất:

```shell
php artisan config:cache      # tạo bootstrap/cache/config.php
php artisan config:clear      # xoá file cache đó
```

Đọc mã nguồn `ConfigCacheCommand` (13.x) sẽ thấy các bước chính: xoá cache cũ, nạp cấu hình mới
(lúc này `.env` được đọc và mọi `env()` được tính ra giá trị), ghi ra file
`'<?php return '.var_export($config, true).';'`, rồi `require` thử file vừa ghi để chắc nó nạp được
(nếu lỗi thì xoá file và báo lỗi). File cache là một mảng PHP thuần, không còn lời gọi
`env()` nào, OPcache giữ nó trong bộ nhớ nên nạp rất nhanh.

Chỗ quan trọng nằm ở đây. Khi file cache tồn tại, Laravel **không đọc `.env` nữa**. Mã nguồn
`LoadEnvironmentVariables::bootstrap()` mở đầu bằng:

```php
if ($app->configurationIsCached()) {
    return;
}
```

Hệ quả, như tài liệu cảnh báo: sau `config:cache`, hàm `env()` chỉ còn trả về biến môi trường thật của
hệ thống; biến chỉ khai báo trong `.env` sẽ ra `null` (hoặc giá trị mặc định bạn truyền). Code gọi
`env()` trực tiếp trong controller, service... chạy đúng ở máy dev rồi hỏng trên production.

Mô phỏng bằng PHP thuần (đơn giản hoá, không phải code Laravel thật):

```php
<?php
declare(strict_types=1);

// MÔ PHỎNG cơ chế config:cache của Laravel (đơn giản hoá, không phải code Laravel thật).

const DOTENV_FILE = ['APP_NAME' => 'Shop', 'PAYMENT_KEY' => 'sk_test_123']; // nội dung file .env
$cachePath = __DIR__ . '/demo-config-cache.php';                             // ~ bootstrap/cache/config.php
@unlink($cachePath);

/** @var array<string, string> Kho biến môi trường của tiến trình hiện tại */
$envRepo = [];
/** @var array<string, mixed> */
$config = [];

function env(string $key, mixed $default = null): mixed
{
    return $GLOBALS['envRepo'][$key] ?? $default;
}

/** Tương đương thư mục config/: mỗi "file" là một mảng, giá trị lấy từ env() */
function readConfigFiles(): array
{
    return [
        'app'      => ['name' => env('APP_NAME', 'Laravel')],
        'services' => ['payment' => ['key' => env('PAYMENT_KEY')]],
    ];
}

function config(string $key, mixed $default = null): mixed
{
    $value = $GLOBALS['config'];
    foreach (explode('.', $key) as $segment) {          // "dot notation": services.payment.key
        if (!is_array($value) || !array_key_exists($segment, $value)) {
            return $default;
        }
        $value = $value[$segment];
    }
    return $value;
}

/** Mỗi request/lệnh là một tiến trình mới: kho env bắt đầu rỗng (server không đặt biến nào) */
function bootstrap(string $cachePath): void
{
    $GLOBALS['envRepo'] = [];
    if (is_file($cachePath)) {
        $GLOBALS['config'] = require $cachePath;   // có cache: KHÔNG đọc .env
        return;
    }
    $GLOBALS['envRepo'] = DOTENV_FILE;             // không cache: nạp .env
    $GLOBALS['config'] = readConfigFiles();
}

function handleRequest(string $label): void
{
    printf("%s: config() = %s | env() = %s\n", $label,
        var_export(config('services.payment.key'), true),
        var_export(env('PAYMENT_KEY'), true));
}

bootstrap($cachePath);
handleRequest('Request 1 (chưa cache)');

// php artisan config:cache: nạp .env, đọc mọi file config, ghi ra MỘT file PHP
bootstrap($cachePath);
file_put_contents($cachePath, '<?php return ' . var_export($GLOBALS['config'], true) . ';' . PHP_EOL);
echo "--- đã chạy config:cache ---\n";

bootstrap($cachePath);
handleRequest('Request 2 (đã cache) ');

unlink($cachePath);
// in ra:
// Request 1 (chưa cache): config() = 'sk_test_123' | env() = 'sk_test_123'
// --- đã chạy config:cache ---
// Request 2 (đã cache) : config() = 'sk_test_123' | env() = NULL
```

`config()` vẫn đúng vì giá trị đã được "đóng băng" vào file cache. `env()` gọi lúc chạy thì không còn
`.env` để đọc. Diễn biến thực tế thường như sau:

| Bước | Máy dev | Server production | Kết quả |
|---|---|---|---|
| 1 | Viết `Http::withToken(env('PAYMENT_KEY'))` trong service | | Chạy đúng ở dev (dev không cache config) |
| 2 | | Deploy, script deploy chạy `php artisan config:cache` | `.env` không còn được đọc lúc request |
| 3 | | Request gọi service, `env('PAYMENT_KEY')` trả `null` | Gọi API thanh toán không có token, lỗi 401 |
| 4 | Thử lại ở dev, không tái hiện được | | Mất nhiều giờ debug |

Cách đúng: khai báo trong `config/services.php` (hoặc file config riêng)
`'payment' => ['key' => env('PAYMENT_KEY')]`, còn code dùng `config('services.payment.key')`.

Các hệ quả khác của config cache:

- Sửa `.env` trên server sau khi đã cache sẽ không có tác dụng cho tới khi chạy lại
  `php artisan config:cache` (hoặc `config:clear`).
- Giá trị trong config phải "xuất ra được" bằng `var_export`. Nếu bạn đặt một closure hay object không
  serialize được vào file config, `config:cache` báo lỗi `LogicException`, thường kèm tên khoá gây lỗi:
  `Your configuration files could not be serialized because the value at "..." is non-serializable.`
- Tài liệu khuyên: chạy `config:cache` khi deploy production, không chạy ở máy dev (vì bạn sửa cấu hình
  liên tục). Nếu lỡ chạy ở dev và thấy sửa `.env` không ăn, chạy `php artisan config:clear`.

### 5.6 Môi trường: `APP_ENV`, `APP_DEBUG`, `APP_KEY`

**`APP_ENV`** cho biết ứng dụng đang chạy ở môi trường nào. Giá trị là chuỗi tuỳ bạn đặt, thông dụng
là `local`, `testing`, `staging`, `production`. Kiểm tra trong code:

```php
use Illuminate\Support\Facades\App;

$environment = App::environment();             // ví dụ 'local'

if (App::environment('local')) {
    // đang ở local
}
if (App::environment(['local', 'staging'])) {
    // local HOẶC staging
}
```

Laravel còn hỗ trợ file `.env` theo môi trường: nếu biến `APP_ENV` được đặt từ bên ngoài (biến môi
trường thật), hoặc lệnh Artisan có tham số `--env=staging`, Laravel thử nạp `.env.staging` (tức
`.env.[APP_ENV]`); không có file đó thì nạp `.env` như thường.

**`APP_DEBUG`** quyết định lỗi được hiển thị chi tiết thế nào. `true`: trang lỗi có stack trace, đoạn
code, thông tin request và môi trường. `false`: trang lỗi chung chung "500 Server Error".

⚠️ `APP_DEBUG=true` trên production là một lỗ hổng bảo mật nghiêm trọng. Tài liệu cảnh báo bằng chữ in
đậm: bạn có nguy cơ phơi các giá trị cấu hình nhạy cảm cho người dùng cuối. Chỉ cần một exception là
kẻ tấn công thấy được đường dẫn file, câu query, có khi cả thông tin kết nối. Đây là lỗi cấu hình hay
gặp khi copy `.env` từ máy dev lên server.

**`APP_KEY`** là khoá mã hoá của ứng dụng, sinh bằng `php artisan key:generate` (bộ sinh số ngẫu nhiên
an toàn của PHP) và lưu dạng `base64:...` trong `.env`. Laravel dùng nó cho dịch vụ mã hoá (facade
`Crypt`, cipher mặc định `AES-256-CBC`, kèm MAC chống sửa đổi). Theo tài liệu, mọi cookie, kể cả cookie
session, đều được Laravel mã hoá bằng khoá này.

⚠️ Đổi `APP_KEY` (hoặc mỗi server một khoá khác nhau sau load balancer) thì:

- mọi người dùng đang đăng nhập bị đăng xuất, vì cookie cũ không giải mã được;
- dữ liệu bạn đã mã hoá bằng `Crypt` và lưu vào database không giải mã được nữa.

Muốn xoay khoá an toàn, đưa khoá cũ vào `APP_PREVIOUS_KEYS` (danh sách ngăn cách bằng dấu phẩy):
Laravel luôn mã hoá bằng khoá hiện tại, nhưng khi giải mã sẽ thử khoá hiện tại rồi lần lượt các khoá cũ.

⚠️ Một hiểu lầm thường gặp: `APP_KEY` không dùng để băm mật khẩu người dùng. Mật khẩu được băm bằng
bcrypt/Argon2 ([Chương 17](17-bao-mat.md)), không phụ thuộc `APP_KEY`; đổi khoá không làm hỏng mật khẩu
đã lưu. Cái hỏng là cookie, session và dữ liệu mã hoá bằng `Crypt`.

### 5.7 Mã hoá file `.env` để commit

Đôi khi đội muốn lưu cấu hình production trong git (để có lịch sử thay đổi). Laravel cho phép mã hoá
file `.env`:

```shell
php artisan env:encrypt                 # tạo .env.encrypted, in ra khoá giải mã (cất vào password manager)
php artisan env:encrypt --env=staging   # mã hoá .env.staging
php artisan env:encrypt --readable      # giữ tên biến đọc được, chỉ mã hoá giá trị (dễ review diff)
php artisan env:decrypt                 # giải mã ra .env, khoá lấy từ biến LARAVEL_ENV_ENCRYPTION_KEY
php artisan env:decrypt --key=...       # hoặc truyền khoá trực tiếp
```

File `.env.encrypted` commit được; khoá giải mã thì không bao giờ commit, mà đặt làm biến môi trường
trên server deploy.

## 6. Artisan: công cụ dòng lệnh của Laravel

### 6.1 Artisan là gì

*Artisan* là giao diện dòng lệnh (CLI) đi kèm Laravel, chính là file `artisan` ở gốc dự án (mục 4.3).
Mọi lệnh có dạng `php artisan <tên-lệnh> [tham số] [--tuỳ-chọn]`, chạy trong thư mục gốc dự án. Artisan
dùng để: sinh code mẫu, chạy migration, xem route, xoá và tạo cache, chạy queue worker, bật chế độ bảo
trì, chạy test, và chạy các lệnh do chính bạn viết.

Về bản chất Artisan làm việc giống ví dụ mô phỏng dưới đây: một file cửa vào, tra tên lệnh trong bảng
lệnh đã đăng ký, gọi phần xử lý, trả *exit code*. Exit code là con số tiến trình trả cho hệ điều hành
khi kết thúc: `0` là thành công, khác `0` là lỗi. Script deploy và CI dựa vào nó để biết bước nào hỏng.

```php
<?php
declare(strict_types=1);

// MÔ PHỎNG ý tưởng của Artisan: một file cửa vào, tra tên lệnh trong bảng, gọi handler, trả exit code.
// (Artisan thật dựng trên symfony/console, phức tạp hơn nhiều.)

/** @var array<string, array{description: string, handler: callable(list<string>): int}> */
$commands = [
    'inspire' => [
        'description' => 'Display an inspiring quote',
        'handler' => function (array $args): int {
            echo "Simplicity is the ultimate sophistication.\n";
            return 0;
        },
    ],
    'greet' => [
        'description' => 'Chào một người',
        'handler' => function (array $args): int {
            if ($args === []) {
                echo "Thiếu tham số {name}\n";
                return 1;                                   // exit code khác 0 = thất bại
            }
            echo "Xin chào {$args[0]}\n";
            return 0;
        },
    ],
];

function run(array $commands, array $argv): int
{
    $name = $argv[1] ?? 'list';
    if ($name === 'list') {
        foreach ($commands as $cmd => $def) {
            printf("  %-10s %s\n", $cmd, $def['description']);
        }
        return 0;
    }
    if (!isset($commands[$name])) {
        echo "Command \"$name\" is not defined.\n";
        return 1;
    }
    return ($commands[$name]['handler'])(array_slice($argv, 2));
}

// Giả lập: php artisan / php artisan greet An / php artisan greet / php artisan foo
foreach ([['artisan'], ['artisan', 'greet', 'An'], ['artisan', 'greet'], ['artisan', 'foo']] as $argv) {
    echo '$ php ', implode(' ', $argv), "\n";
    $status = run($commands, $argv);
    echo "(exit code: $status)\n";
}
// in ra:
// $ php artisan
//   inspire    Display an inspiring quote
//   greet      Chào một người
// (exit code: 0)
// $ php artisan greet An
// Xin chào An
// (exit code: 0)
// $ php artisan greet
// Thiếu tham số {name}
// (exit code: 1)
// $ php artisan foo
// Command "foo" is not defined.
// (exit code: 1)
```

Hai lệnh để tự tra cứu, nhớ hai lệnh này là đủ để tự học phần còn lại:

```shell
php artisan list          # liệt kê mọi lệnh (gõ "php artisan" không tham số cũng ra danh sách)
php artisan list make     # chỉ các lệnh trong nhóm make:
php artisan help migrate  # tham số và tuỳ chọn của một lệnh
php artisan migrate --help  # cách viết khác, cùng kết quả
```

Danh sách lệnh không cố định: package cài thêm (Horizon, Sanctum...) và chính bạn có thể đăng ký lệnh
mới.

### 6.2 Nhóm `make:`: sinh code mẫu

Các lệnh `make:` tạo file class từ *stub* (file mẫu), đặt đúng thư mục, đúng namespace. Dùng chúng
thay vì tự tạo file tay để không sai namespace hay quên kế thừa class cha.

```shell
php artisan make:controller PostController            # app/Http/Controllers/PostController.php
php artisan make:controller PostController --resource # kèm sẵn 7 method CRUD (index, create, store...)
php artisan make:model Post                           # app/Models/Post.php
php artisan make:model Post -mfsc                     # model + migration + factory + seeder + controller
php artisan make:migration create_posts_table         # database/migrations/<thời gian>_create_posts_table.php
php artisan make:request StorePostRequest             # app/Http/Requests/StorePostRequest.php
php artisan make:middleware EnsureUserIsAdmin         # app/Http/Middleware/EnsureUserIsAdmin.php
php artisan make:command SendReport                   # app/Console/Commands/SendReport.php
php artisan make:job ProcessPodcast                   # app/Jobs/ProcessPodcast.php
php artisan make:test PostTest                        # tests/Feature/PostTest.php (--unit để vào tests/Unit)
```

Với `make:model`, các tuỳ chọn viết tắt (theo tài liệu Eloquent 13.x): `-m` migration, `-f` factory,
`-s` seeder, `-c` controller, `-a` (`--all`) sinh đủ mọi thứ liên quan. Ghép được: `-mfsc`.

### 6.3 Lệnh làm việc với database

```shell
php artisan migrate                 # chạy các migration chưa chạy
php artisan migrate:status          # migration nào đã chạy, nào chưa
php artisan migrate:rollback        # hoàn tác "batch" migration gần nhất
php artisan migrate:fresh --seed    # XOÁ HẾT bảng, chạy lại mọi migration, rồi seed dữ liệu mẫu
php artisan db:seed                 # chạy seeder (mặc định Database\Seeders\DatabaseSeeder)
php artisan db:show                 # thông tin database: loại, phiên bản, danh sách bảng
php artisan db                      # mở CLI của database (mysql, psql, sqlite3) theo cấu hình hiện tại
```

⚠️ `migrate:fresh` xoá mọi bảng trong database của kết nối mặc định. Chỉ dùng ở dev. Để bảo vệ bạn,
các lệnh migration có thể gây mất dữ liệu sẽ hỏi xác nhận khi chạy trên môi trường production; script
deploy dùng `php artisan migrate --force` để bỏ qua câu hỏi (vì không có ai ngồi gõ "yes"). Hiểu rõ:
`--force` là "tôi biết mình đang chạy trên production", không phải "chạy cho bằng được".

Chi tiết migration và seeder ở [Chương 27](27-laravel-database-eloquent.md).

### 6.4 Lệnh xem và gỡ lỗi

```shell
php artisan about                 # tổng quan ứng dụng (phiên bản Laravel, PHP, môi trường, driver...)
php artisan route:list            # mọi route: method, URI, tên, controller
php artisan route:list -v         # thêm cột middleware
php artisan route:list --path=api # chỉ route có URI chứa "api"
php artisan route:list --except-vendor   # bỏ route do package đăng ký
php artisan config:show app       # giá trị thực tế của config/app.php
php artisan model:show User       # cột, quan hệ, cast của một model
php artisan tinker                # REPL: gõ code PHP chạy trong ngữ cảnh ứng dụng
```

*Tinker* là *REPL* (Read-Eval-Print Loop, vòng "đọc lệnh, chạy, in kết quả") dựng trên thư viện PsySH,
có sẵn trong mọi dự án (package `laravel/tinker` trong `composer.json`). Khác `php -a`
([Chương 01](01-php-la-gi.md)) ở chỗ ứng dụng đã được khởi động: dùng được model, config, facade ngay.
Một phiên Tinker trông như sau (output minh hoạ, chi tiết hiển thị tuỳ phiên bản):

```
$ php artisan tinker
> config('app.timezone')
= "UTC"

> App\Models\User::count()
= 0

> App\Models\User::factory()->create(['name' => 'An'])
= App\Models\User {#6123
    name: "An",
    email: "...",
    ...
  }
```

⚠️ Tinker chạy thật trên database mà `.env` đang trỏ tới. Mở Tinker trên server production và gõ nhầm
`User::truncate()` là mất dữ liệu thật. Coi Tinker trên production như mở client SQL với quyền ghi.

⚠️ Tài liệu lưu ý: trong Tinker, hàm `dispatch()` dựa vào cơ chế thu gom rác để đưa job vào queue nên
có thể không chạy như mong đợi; dùng `Bus::dispatch(...)` hoặc `Queue::push(...)`.

### 6.5 Bảng tra nhanh lệnh hằng ngày

| Khi muốn | Lệnh |
|---|---|
| Chạy server dev | `php artisan serve` hoặc `composer run dev` |
| Sinh khoá ứng dụng | `php artisan key:generate` |
| Tạo symlink `public/storage` | `php artisan storage:link` |
| Thêm file route API | `php artisan install:api` |
| Chạy test | `php artisan test` |
| Chạy queue worker | `php artisan queue:work` ([Ch. 29](29-laravel-queue-event-schedule-cache.md)) |
| Chạy scheduler | `php artisan schedule:run` hoặc `schedule:work` ([Ch. 29](29-laravel-queue-event-schedule-cache.md)) |
| Xoá cache ứng dụng | `php artisan cache:clear` |
| Bật / tắt bảo trì | `php artisan down` / `php artisan up` (mục 7.4) |

## 7. Artisan nâng cao: cache khi deploy, bảo trì, tự viết lệnh

### 7.1 Nhóm lệnh tối ưu khi deploy

Mục 5.5 đã nói về `config:cache`. Laravel có thêm vài loại cache cùng ý tưởng "tính trước một lần lúc
deploy, request nào cũng dùng lại":

| Lệnh | Làm gì | Xoá bằng |
|---|---|---|
| `config:cache` | Gộp mọi file `config/` thành `bootstrap/cache/config.php`, ngừng đọc `.env` | `config:clear` |
| `route:cache` | Gộp đăng ký route thành một file cache, đăng ký route nhanh hơn khi có hàng trăm route | `route:clear` |
| `event:cache` | Lưu ánh xạ event → listener đã tự phát hiện, khỏi quét thư mục mỗi request | `event:clear` |
| `view:cache` | Biên dịch trước mọi view Blade, khỏi biên dịch lúc request đầu | `view:clear` |
| `optimize` | Chạy cả bốn lệnh trên | `optimize:clear` |

Đọc mã nguồn `OptimizeCommand` (13.x) thấy đúng danh sách: `config:cache`, `event:cache`,
`route:cache`, `view:cache`. Còn `OptimizeClearCommand` chạy `config:clear`, `cache:clear`,
`clear-compiled`, `event:clear`, `route:clear`, `view:clear`.

⚠️ `optimize:clear` không chỉ xoá các file cache ở trên mà còn chạy `cache:clear`, tức xoá mọi khoá
trong cache store mặc định của ứng dụng (tài liệu deploy ghi rõ). Nếu store đó là Redis dùng chung với
dữ liệu bạn không muốn mất (ví dụ khoá rate limit, khoá lock), chạy `optimize:clear` trên production sẽ
xoá luôn.

⚠️ Sau `route:cache`, thêm route mới mà không cache lại thì route mới "không tồn tại" (404). Tài liệu
khuyên chỉ chạy `route:cache` trong quy trình deploy. Quy tắc chung cho cả nhóm: ở máy dev không cache
gì; ở production, script deploy luôn chạy lại các lệnh cache sau khi kéo code mới.

Một script deploy tối giản (minh hoạ, chạy trên server, trong thư mục dự án; deploy đầy đủ ở
[Chương 30](30-laravel-testing-octane-deploy.md)):

```shell
composer install --no-dev --optimize-autoloader   # không cài package dev, autoload dạng classmap
php artisan migrate --force                       # cập nhật schema
php artisan optimize                              # config, event, route, view cache
php artisan reload                                # cho queue worker, Octane, Reverb... dừng để chạy lại với code mới
```

Lệnh `reload` theo tài liệu deploy 13.x sẽ dừng các dịch vụ chạy lâu (queue worker, Reverb, Octane);
bạn cần một trình giám sát tiến trình (như Supervisor) để tự khởi động lại chúng.

### 7.2 Vì sao cache lại giúp nhanh

Nhắc lại từ [Chương 02](02-php-chay-nhu-the-nao.md) và [Chương 18](18-fpm-nginx-opcache.md): với
PHP-FPM, mỗi request bắt đầu từ đầu, không có gì sống sót từ request trước ngoài những gì OPcache giữ
(bytecode). Không có config cache, mỗi request phải: mở và phân tích `.env`, `require` khoảng chục file
config, gọi `env()` hàng trăm lần. Có cache: `require` một file PHP chỉ `return` một mảng hằng, mà
bytecode của nó đã nằm sẵn trong OPcache. Route cũng vậy: thay vì chạy lại mọi lời gọi
`Route::get(...)` để dựng bảng route, Laravel nạp bảng đã dựng sẵn.

Với Laravel Octane (mục 8), ứng dụng được khởi động một lần và giữ trong bộ nhớ qua nhiều request, nên
phần lớn chi phí khởi động biến mất theo cách khác.

### 7.3 `php artisan dev`, `serve` và Pail

Lệnh `dev` (từ `composer run dev`) đã nói ở mục 3.4. Thành phần xem log là *Laravel Pail* (package
`laravel/pail` trong `require-dev` của skeleton), có thể chạy riêng bằng `php artisan pail` để xem log
ứng dụng theo thời gian thực ngay trong terminal.

### 7.4 Chế độ bảo trì

Khi cần tạm dừng ứng dụng (nâng cấp lớn, sửa dữ liệu), bật chế độ bảo trì:

```shell
php artisan down                         # mọi request nhận trang 503
php artisan down --retry=60              # đặt header Retry-After: 60
php artisan down --refresh=15            # header Refresh: trình duyệt tự tải lại sau 15 giây
php artisan down --secret="mot-chuoi-bi-mat"   # truy cập https://site/mot-chuoi-bi-mat để nhận cookie vượt bảo trì
php artisan down --with-secret           # để Laravel tự sinh secret và in ra
php artisan down --render="errors::503"  # render sẵn trang bảo trì, trả về trước khi framework khởi động
php artisan up                           # tắt bảo trì
```

Cơ chế: theo tài liệu, khi ứng dụng ở chế độ bảo trì, một middleware mặc định ném `HttpException` mã
503 cho mọi request. Với driver mặc định (`file`), trạng thái bảo trì là file `storage/framework/down`.
Lệnh `down` còn ghi thêm file `storage/framework/maintenance.php`, chính là file mà `public/index.php`
kiểm tra ngay dòng đầu (mục 4.3). Tuỳ chọn `--render` giúp trả trang 503 ngay ở bước đó, kể cả khi
`vendor/` đang được cập nhật dở; không có `--render` thì file này để framework tự xử lý.

⚠️ Với driver `file`, phải chạy `php artisan down` trên từng server. Ứng dụng chạy nhiều server sau load
balancer nên dùng driver `cache` (đặt `APP_MAINTENANCE_DRIVER=cache` và `APP_MAINTENANCE_STORE` trỏ tới
một cache store mà mọi server dùng chung), khi đó chạy `down` trên một server là đủ.

⚠️ Trong lúc bảo trì, queue worker không xử lý job; job được xử lý tiếp khi ứng dụng `up`.

Chế độ bảo trì gây downtime vài giây tới vài phút. Hệ thống cần không gián đoạn thường dùng cách
*zero-downtime deployment* (chuẩn bị bản mới ở thư mục riêng rồi đổi symlink), xem
[Chương 30](30-laravel-testing-octane-deploy.md).

### 7.5 Tự viết lệnh Artisan

Có hai cách, giống route có thể là closure hoặc controller.

**Cách 1: closure trong `routes/console.php`.** Skeleton 13.x có sẵn lệnh `inspire`:

```php
<?php

use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');
```

`$this` trong closure là đối tượng command (closure được bind vào command), nên gọi được `comment()`,
`info()`, `error()`... `purpose()` đặt mô tả hiện trong `php artisan list`.

**Cách 2: class trong `app/Console/Commands`.** Chạy `php artisan make:command SendReport`. Từ Laravel
13, file sinh ra dùng *attribute* `#[Signature]` và `#[Description]` để khai báo tên lệnh và mô tả
(attribute đã học ở [Chương 10](10-oop-nang-cao.md)). Ví dụ hoàn chỉnh (viết theo mẫu trong tài liệu
Artisan 13.x):

```php
<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Attributes\Description;
use Illuminate\Console\Attributes\Signature;
use Illuminate\Console\Command;

#[Signature('report:users {--active : Chỉ đếm user đang hoạt động}')]
#[Description('In số lượng user')]
class SendReport extends Command
{
    public function handle(): int
    {
        $query = User::query();

        if ($this->option('active')) {
            $query->whereNotNull('email_verified_at');
        }

        $count = $query->count();

        if ($count === 0) {
            $this->error('Chưa có user nào.');
            return self::FAILURE;   // = 1
        }

        $this->info("Có {$count} user.");
        return self::SUCCESS;       // = 0
    }
}
```

Chạy `php artisan report:users --active`. Cú pháp *signature* giống route:

| Signature | Ý nghĩa |
|---|---|
| `{user}` | Tham số bắt buộc |
| `{user?}` | Tham số tuỳ chọn |
| `{user=foo}` | Tham số có giá trị mặc định |
| `{user*}` | Nhiều giá trị (mảng) |
| `{--queue}` | Công tắc: có thì `true`, không thì `false` |
| `{--queue=}` | Tuỳ chọn nhận giá trị, không truyền thì `null` |
| `{--queue=default}` | Tuỳ chọn có mặc định |
| `{--Q\|queue=}` | Có tên viết tắt `-Q` |
| `{user : Mô tả}` | Thêm mô tả hiện trong `help` |

Trong dự án cũ (và trong nhiều ví dụ của tài liệu) bạn sẽ thấy cách viết bằng thuộc tính
`protected $signature = 'mail:send {user}';` và `protected $description = '...';`; hai cách tương
đương. Lệnh trong `app/Console/Commands` được Laravel tự phát hiện và đăng ký, không cần khai báo ở đâu
khác.

Theo tài liệu: `handle()` không trả gì và chạy xong bình thường thì exit code là `0`; có thể trả số
nguyên để tự đặt exit code, hoặc gọi `$this->fail('...')` để dừng ngay với exit code `1`. Hằng
`self::SUCCESS`, `self::FAILURE` đến từ class `Command` của Symfony Console.

⚠️ Giữ command mỏng. Tài liệu khuyên để command gọi tới service làm phần việc nặng, giống controller
(mục 4.6). Logic nằm trong service thì vừa gọi được từ command, vừa từ controller, vừa test riêng được.

⚠️ Lệnh chạy theo lịch hoặc chạy lâu có thể bị chạy chồng (cron gọi lần mới khi lần cũ chưa xong). Laravel
có interface `Isolatable` thêm tuỳ chọn `--isolated` để chỉ cho một tiến trình của lệnh chạy cùng lúc
(dùng atomic lock qua cache). Scheduler có cơ chế tương tự, xem [Chương 29](29-laravel-queue-event-schedule-cache.md).

## 8. Hệ sinh thái Laravel

Ngoài framework, đội Laravel duy trì nhiều công cụ và dịch vụ *first-party*. Người mới hay bị ngợp vì
toàn tên riêng. Mục này chỉ giới thiệu từng thứ là gì và dùng khi nào; các chương sau đi sâu những
thứ quan trọng cho backend.

### 8.1 Bản đồ theo giai đoạn

```
  PHÁT TRIỂN (máy dev)           CHẠY (runtime)              DEPLOY / HẠ TẦNG          QUAN SÁT
  ┌────────────────────┐        ┌───────────────────┐       ┌──────────────────┐      ┌───────────────┐
  │ Herd  (app native) │        │ Octane (app server│       │ Forge (quản lý   │      │ Telescope     │
  │ Sail  (Docker)     │        │   giữ app trong   │       │   VPS của bạn)   │      │  (debug, dev) │
  │ Boost (cho AI agent│        │   bộ nhớ)         │       │ Cloud (nền tảng  │      │ Pulse (số liệu│
  │   viết code)       │        │ Horizon (queue    │       │   managed)       │      │  hiệu năng)   │
  │ Pail  (xem log)    │        │   Redis+dashboard)│       │ Vapor (serverless│      │ Horizon       │
  └────────────────────┘        └───────────────────┘       │   trên AWS)      │      │  (dashboard   │
                                                            └──────────────────┘      │   queue)      │
                                                                                      └───────────────┘
```

| Tên | Là gì | Dạng | Dùng khi |
|---|---|---|---|
| Herd | Môi trường dev native cho macOS và Windows: cài sẵn PHP, Nginx, Composer, Node; ứng dụng trong thư mục "parked" (mặc định `~/Herd`) tự có tên miền `<tên-thư-mục>.test` | Ứng dụng desktop (bản Pro trả phí thêm MySQL, Postgres, Redis...) | Muốn dev nhanh trên máy, không dùng Docker |
| Sail | CLI nhẹ bao quanh môi trường Docker mặc định của Laravel: file `compose.yaml` + script `sail` | Package Composer (`laravel/sail`, dev) | Muốn môi trường giống nhau giữa các máy, có sẵn MySQL, Redis trong container |
| Boost | Cung cấp cho AI agent (Claude Code, Cursor...) hướng dẫn, công cụ MCP và tài liệu đúng phiên bản package của dự án | Package Composer (dev) | Dùng AI hỗ trợ viết code Laravel |
| Octane | Chạy ứng dụng trên application server (FrankenPHP, Swoole, Open Swoole, RoadRunner): khởi động ứng dụng một lần, giữ trong bộ nhớ, phục vụ nhiều request | Package Composer | Cần thông lượng cao, độ trễ thấp |
| Horizon | Dashboard và cấu hình bằng code cho queue chạy trên Redis: theo dõi throughput, thời gian chạy, job lỗi | Package Composer | Dùng queue Redis ở production |
| Telescope | Công cụ debug: ghi lại request, exception, log, query, job, mail, cache, lệnh dump... | Package Composer | Dev và debug local |
| Pulse | Dashboard số liệu hiệu năng và sử dụng: request chậm, job chậm, user hoạt động nhiều | Package Composer | Theo dõi production ở mức tổng quan |
| Forge | Dịch vụ quản lý VPS: tạo server trên DigitalOcean, AWS... và cài sẵn Nginx, MySQL, Redis..., deploy ứng dụng | Dịch vụ web trả phí | Muốn tự sở hữu server nhưng không tự cấu hình từng thứ |
| Cloud | Nền tảng deploy managed, tự co giãn: compute, database, cache, object storage | Dịch vụ web trả phí | Không muốn quản lý server |
| Vapor | Nền tảng deploy *serverless* chạy Laravel trên AWS Lambda | Dịch vụ web trả phí | Dự án cũ đang chạy trên Vapor; trang vapor.laravel.com ghi Vapor không còn nhận đăng ký mới (10/2026) |

### 8.2 Môi trường dev: Herd và Sail

Herd (mục 3.1) hợp người muốn "cài là chạy". Tạo dự án trong `~/Herd`:

```shell
cd ~/Herd
laravel new my-app
cd my-app
herd open        # mở http://my-app.test trong trình duyệt
```

Sail hợp đội muốn mọi người chạy cùng phiên bản PHP, MySQL, Redis bằng Docker (chạy trong thư mục dự
án):

```shell
composer require laravel/sail --dev
php artisan sail:install          # sinh compose.yaml, sửa .env để trỏ tới các container
./vendor/bin/sail up              # khởi động container
./vendor/bin/sail artisan migrate # mọi lệnh artisan/composer/php chạy qua sail, tức chạy TRONG container
```

⚠️ Khi dùng Sail, chạy `php artisan migrate` trực tiếp trên máy host thường lỗi kết nối: `.env` ghi
`DB_HOST=mysql` (tên service trong Docker), tên này chỉ phân giải được bên trong mạng Docker. Hãy chạy
qua `./vendor/bin/sail artisan ...`.

### 8.3 Octane: khác biệt căn bản so với PHP-FPM

Với PHP-FPM, mỗi request khởi động lại toàn bộ framework rồi vứt bỏ (mô hình *shared-nothing*,
[Chương 02](02-php-chay-nhu-the-nao.md)). Octane khởi động ứng dụng một lần rồi giữ trong bộ nhớ, đưa
request liên tiếp vào cùng một tiến trình worker. Nhanh hơn, nhưng đổi lại một loạt cạm bẫy mới: biến
`static`, singleton trong container, dữ liệu tích luỹ trong mảng... sống qua nhiều request, có thể rò
dữ liệu của user này sang user khác hoặc rò bộ nhớ. Đây là chủ đề của
[Chương 30](30-laravel-testing-octane-deploy.md); ở đây chỉ cần nhớ: code chạy đúng trên FPM chưa chắc
đúng trên Octane.

### 8.4 Quan sát: Telescope, Pulse, Horizon

- Telescope ghi lại gần như mọi thứ xảy ra trong từng request, rất tiện để thấy "request này chạy
  những query nào". Tài liệu mô tả nó là bạn đồng hành cho môi trường dev local; có thể cài chỉ ở dev
  (`composer require laravel/telescope --dev`).
- Pulse cho số liệu tổng hợp (endpoint chậm, job chậm, query chậm), dùng được ở production: tài
  liệu hướng dẫn cấp quyền xem dashboard cho môi trường production và cách giảm ảnh hưởng hiệu năng
  với ứng dụng lưu lượng lớn.
- Horizon là dashboard và bộ quản lý worker cho queue Redis ([Chương 29](29-laravel-queue-event-schedule-cache.md)).
  Theo tài liệu, Horizon bắt buộc queue chạy trên Redis.

⚠️ Dashboard Telescope nằm ở `/telescope`. Mặc định chỉ vào được khi môi trường là `local`; môi trường
khác được kiểm soát bởi một gate trong `TelescopeServiceProvider`. Tài liệu cảnh báo: nếu production
mà quên đặt `APP_ENV=production`, dashboard Telescope sẽ công khai cho mọi người, kèm toàn bộ request,
query, dữ liệu đã ghi lại. Một lý do nữa để kiểm tra `APP_ENV` và `APP_DEBUG` ở mỗi lần deploy.

### 8.5 Deploy: Forge, Cloud, Vapor, hay tự làm

| Cách | Bạn quản lý | Hợp với |
|---|---|---|
| Tự dựng server (Nginx + PHP-FPM, [Ch. 18](18-fpm-nginx-opcache.md)) | Mọi thứ | Muốn kiểm soát toàn bộ, có người làm vận hành |
| Forge | Server là của bạn (VPS), Forge cài đặt và deploy giúp | Đội nhỏ muốn VPS giá rẻ mà không tự cấu hình tay |
| Cloud | Gần như không quản lý hạ tầng | Muốn tập trung vào code, chấp nhận chi phí nền tảng |
| Vapor | Không quản lý server, nhưng phải hiểu ràng buộc của serverless (AWS Lambda) | Chỉ còn cho dự án đã dùng Vapor (không nhận đăng ký mới) |
| Docker/Kubernetes tự dựng | Image, orchestration | Tổ chức đã chuẩn hoá trên container |

Không có lựa chọn nào bắt buộc; Laravel chạy ở bất cứ đâu có PHP. Health route `/up` (mục 4.4) và
lệnh `optimize`, `reload` (mục 7.1) dùng được với mọi cách.

### 8.6 Package first-party khác bạn sẽ gặp

Chỉ để nhận mặt tên, chi tiết ở các chương sau: Sanctum (xác thực API bằng token, SPA) và Fortify
(backend xác thực cho starter kit) ở [Chương 28](28-laravel-auth.md); Reverb (WebSocket server cho
realtime); Scout (tìm kiếm full-text); Socialite (đăng nhập bằng Google, GitHub...); Cashier (thanh toán
thuê bao); Pint (định dạng code, có sẵn trong `require-dev` của skeleton, xem
[Chương 21](21-chat-luong-code.md)); Pennant (feature flag); Prompts (giao diện nhập liệu đẹp cho lệnh
CLI, chính installer dùng nó).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Gọi `env()` trong controller, service, view | Sau `config:cache`, `.env` không được đọc; `env()` trả `null` trên production | Chỉ gọi `env()` trong `config/*.php`, mọi nơi khác dùng `config()` (mục 5.5) |
| Sửa `.env` trên server mà không thấy thay đổi | Config đang được cache, hoặc biến môi trường thật của server ghi đè | Chạy lại `config:cache` hoặc `config:clear`; kiểm tra biến môi trường của tiến trình PHP (mục 5.2) |
| `APP_DEBUG=true` trên production | Copy `.env` từ dev | Mặc định `false`; checklist deploy kiểm tra `APP_ENV=production`, `APP_DEBUG=false` (mục 5.6) |
| Commit `.env` vào git | Quên `.gitignore` hoặc `git add -f` | Chỉ commit `.env.example`; muốn lưu cấu hình thì dùng `env:encrypt` (mục 5.7) |
| Document root trỏ vào gốc dự án | Cấu hình Nginx/Apache sai, hoặc hosting chia sẻ chỉ cho một thư mục | Document root luôn là `public/`; không chuyển `index.php` ra ngoài (mục 4.2) |
| "Permission denied" với `storage/logs/laravel.log`, trang trắng | User của PHP-FPM không ghi được `storage/`, `bootstrap/cache/` | Cấp quyền ghi hai thư mục này cho user chạy PHP (mục 4.2) |
| Đổi `APP_KEY` làm mọi người bị đăng xuất, dữ liệu `Crypt` không giải mã được | Cookie và dữ liệu mã hoá phụ thuộc khoá | Không đổi khoá tuỳ tiện; xoay khoá bằng `APP_PREVIOUS_KEYS`; mọi server dùng chung một khoá (mục 5.6) |
| Route mới trả 404 trên production | `route:cache` cũ còn đó | Script deploy luôn chạy lại `optimize` sau khi kéo code (mục 7.1) |
| `optimize:clear` trên production làm mất dữ liệu cache | Lệnh này chạy cả `cache:clear` | Hiểu lệnh xoá những gì; dùng `config:clear`, `route:clear`... riêng lẻ khi cần (mục 7.1) |
| Làm theo tutorial Laravel 10 trên dự án mới ("sửa `app/Http/Kernel.php`") | Laravel 11 đổi cấu trúc | Xem tutorial viết cho bản nào; dùng `bootstrap/app.php` (mục 4.5) |
| Nghĩ `composer update` sẽ cập nhật file trong `config/`, `bootstrap/` | Đó là file skeleton đã copy, không thuộc `vendor/` | Khi nâng bản lớn, đọc Upgrade Guide và tự sửa (mục 3.2) |
| Chạy `migrate:fresh` hay Tinker trên nhầm database | `.env` đang trỏ tới database thật | Kiểm tra `php artisan about` trước lệnh nguy hiểm; không dùng `migrate:fresh` ngoài dev (mục 6.3, 6.4) |
| So sánh `env('DB_PORT') === 3306` ra `false` | Giá trị từ `.env` là chuỗi | Ép kiểu trong file config (`(int) env(...)`) hoặc dùng `Config::integer()` (mục 5.3, 5.4) |
| Dùng Laravel 11 hoặc cũ hơn ở thời điểm 10/2026 | Đã hết vá bảo mật | Lên kế hoạch nâng cấp theo bảng hỗ trợ (mục 2.2) |

## Tóm tắt chương

- Framework đảo ngược điều khiển: nó nhận request và gọi code bạn đăng ký. Laravel là framework PHP
  theo hướng "convention over configuration", đủ đồ, dựng trên nhiều component Symfony.
- Laravel theo semver, mỗi năm một bản lớn; mọi bản lớn được sửa lỗi 18 tháng, vá bảo mật 2 năm.
  Laravel 13 (17/3/2026) cần PHP 8.3 tới 8.5. Phiên bản Laravel và PHP phải nâng cấp cùng kế hoạch.
- Tạo dự án bằng `laravel new` hoặc `composer create-project laravel/laravel`. `laravel/laravel` là
  skeleton copy một lần; code framework nằm ở `vendor/laravel/framework`. Dự án mới dùng SQLite, có sẵn
  `.env` và `APP_KEY`.
- Cửa vào: `public/index.php` (HTTP) và `artisan` (CLI), cả hai nạp `vendor/autoload.php` rồi
  `bootstrap/app.php`. Document root phải là `public/`. `storage/` và `bootstrap/cache/` phải ghi được.
- Từ Laravel 11, `bootstrap/app.php` cấu hình routing, middleware, exception; provider liệt kê ở
  `bootstrap/providers.php`; không còn `Http/Kernel.php`, `Console/Kernel.php`.
- Cấu hình hai tầng: `.env` (không commit) → `config/*.php` qua `env()` → code qua `config()`. Sau
  `config:cache`, `.env` không được đọc nữa, nên chỉ gọi `env()` trong file config.
- `APP_DEBUG=false` trên production; `APP_KEY` mã hoá cookie, session và dữ liệu `Crypt`, không dùng để
  băm mật khẩu; xoay khoá bằng `APP_PREVIOUS_KEYS`.
- Artisan: `list`, `help`, `make:*`, `migrate*`, `route:list`, `tinker`, `about`; khi deploy chạy
  `migrate --force`, `optimize`, `reload`; bảo trì bằng `down`/`up`; lệnh riêng viết bằng closure trong
  `routes/console.php` hoặc class với `#[Signature]`.
- Hệ sinh thái: Herd, Sail (dev); Octane, Horizon (runtime); Forge, Cloud, Vapor (deploy); Telescope,
  Pulse (quan sát); Boost (AI agent).

## Câu hỏi tự kiểm tra

1. Thư viện và framework khác nhau ở điểm nào? Trong `routes/web.php`, ai gọi closure bạn truyền vào
   `Route::get()`? (mục 1.2)
2. Một dự án đang chạy Laravel 12 trên PHP 8.2. Ở thời điểm 10/2026 nó còn được hỗ trợ ở mức nào, và
   muốn lên Laravel 13 thì phải làm gì với PHP trước? (mục 2.2)
3. `laravel/laravel` và `laravel/framework` khác nhau thế nào? Vì sao `composer update` không sửa
   `config/app.php`? (mục 3.2)
4. Kể lần lượt các bước `public/index.php` thực hiện khi nhận một request. Vì sao nó kiểm tra file
   `maintenance.php` trước cả khi nạp autoloader? (mục 4.3, 7.4)
5. Vì sao document root phải là `public/` mà không phải thư mục gốc dự án? Kẻ tấn công lấy được gì nếu
   cấu hình sai? (mục 4.2)
6. Giải thích chính xác vì sao `env('PAYMENT_KEY')` gọi trong một service chạy đúng ở máy dev nhưng
   trả `null` trên production. Sửa thế nào? (mục 5.5)
7. Với `.env` có `APP_DEBUG=0`, `FEATURE_X=False`, `DB_PORT=3306`, `env()` trả về giá trị và kiểu gì
   cho từng biến? (mục 5.3)
8. Đổi `APP_KEY` ảnh hưởng tới những gì và không ảnh hưởng tới gì? Làm sao xoay khoá mà không đăng xuất
   người dùng? (mục 5.6)
9. `php artisan optimize` chạy những lệnh nào? `optimize:clear` khác gì ngoài việc xoá các cache đó?
   (mục 7.1)
10. Ứng dụng chạy trên 3 server sau load balancer. Chạy `php artisan down` trên một server thì chuyện
    gì xảy ra với driver bảo trì mặc định, và cấu hình gì để một lệnh là đủ? (mục 7.4)

## Bài tập

1. **Mini config loader.** Viết bằng PHP thuần (không dùng Laravel) một chương trình gồm: hàm đọc file
   `.env` (bỏ dòng trống và comment `#`, tách `TÊN=giá_trị`, bỏ nháy kép bao ngoài, chuyển `true`,
   `false`, `null`, `empty` như bảng mục 5.3); một thư mục `config/` gồm hai file trả về mảng và gọi
   `env()`; hàm `config('file.khoa.con', $default)` hỗ trợ dot notation; lệnh `cache` ghi toàn bộ cấu
   hình ra một file bằng `var_export`, và khi file cache tồn tại thì không đọc `.env` nữa. Viết vài
   dòng kiểm tra in ra kết quả trước và sau khi cache, chứng minh lại cái bẫy ở mục 5.5.
2. **Đọc cấu trúc dự án.** Tạo một dự án Laravel 13 trắng (bằng Herd, Sail hoặc PHP cài sẵn). Với mỗi
   thư mục và file ở mục 4.1, ghi một câu "nó chứa gì" bằng lời của bạn. Chạy `php artisan about` và
   `php artisan route:list`, giải thích từng route xuất hiện (gợi ý: có route `/up` dù bạn không viết).
3. **Lệnh Artisan đầu tiên.** Trong dự án ở bài 2, viết lệnh `app:check-env` (class, dùng
   `#[Signature]`) kiểm tra ba điều: `APP_KEY` không rỗng, nếu môi trường là `production` thì
   `app.debug` phải là `false`, và `storage/logs` ghi được. Lệnh in từng mục OK/FAIL và trả exit code
   `1` nếu có mục FAIL. Chỉ đọc cấu hình bằng `config()` và `App::environment()`, không gọi `env()`.
   Chạy thử sau khi `config:cache` để chắc chắn lệnh vẫn đúng.
4. **Bảng hỗ trợ.** Mở rộng ví dụ mục 2.2: nhận vào một phiên bản Laravel và một phiên bản PHP, in ra
   cặp này có nằm trong dải PHP được hỗ trợ không, trạng thái hỗ trợ ở ngày hôm nay, và số ngày còn lại
   tới khi hết vá bảo mật.

## Đọc thêm

- Laravel 13.x, Installation: https://laravel.com/docs/13.x/installation
- Laravel 13.x, Release Notes (versioning, support policy): https://laravel.com/docs/13.x/releases
- Laravel 13.x, Upgrade Guide: https://laravel.com/docs/13.x/upgrade
- Laravel 13.x, Directory Structure: https://laravel.com/docs/13.x/structure
- Laravel 13.x, Configuration: https://laravel.com/docs/13.x/configuration
- Laravel 13.x, Request Lifecycle: https://laravel.com/docs/13.x/lifecycle
- Laravel 13.x, Artisan Console: https://laravel.com/docs/13.x/artisan
- Laravel 13.x, Deployment (server requirements, optimize, health route, Forge, Cloud): https://laravel.com/docs/13.x/deployment
- Laravel 13.x, Encryption (APP_KEY, key rotation): https://laravel.com/docs/13.x/encryption
- Laravel 13.x, Starter Kits: https://laravel.com/docs/13.x/starter-kits
- Laravel 13.x, Sail, Octane, Horizon, Telescope, Pulse, Boost: https://laravel.com/docs/13.x/sail ,
  https://laravel.com/docs/13.x/octane , https://laravel.com/docs/13.x/horizon ,
  https://laravel.com/docs/13.x/telescope , https://laravel.com/docs/13.x/pulse ,
  https://laravel.com/docs/13.x/boost
- Laravel 11.x Release Notes, phần "Streamlined Application Structure": https://laravel.com/docs/11.x/releases
- Skeleton `laravel/laravel` nhánh 13.x: https://github.com/laravel/laravel/tree/13.x
- Mã nguồn `laravel/framework` nhánh 13.x, đặc biệt `src/Illuminate/Support/Env.php`,
  `src/Illuminate/Foundation/Bootstrap/LoadEnvironmentVariables.php`,
  `src/Illuminate/Foundation/Console/ConfigCacheCommand.php`, `OptimizeCommand.php`:
  https://github.com/laravel/framework/tree/13.x
- Laravel installer: https://github.com/laravel/installer
- vlucas/phpdotenv: https://github.com/vlucas/phpdotenv
- The Twelve-Factor App, mục Config: https://12factor.net/config
