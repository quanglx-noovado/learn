# Chương 24. Routing, controller và middleware

> [← Mục lục](README.md) · [← Chương 23: Laravel: giới thiệu và cấu trúc dự án](23-laravel-gioi-thieu.md) · [Chương 25: Request, validation, response và view →](25-laravel-request-validation-response.md)

**Bạn sẽ học được:**

- Routing là gì, router "tìm route" cho một request như thế nào, và cách khai báo route trong Laravel
  13: verb, tham số, ràng buộc bằng regex, tên route, group, prefix.
- Route model binding: vì sao viết `Post $post` trong tham số là đủ để có model, cơ chế bên dưới
  (middleware `SubstituteBindings`), các biến thể implicit, explicit, `{post:slug}`, `#[RouteKey]`,
  scoped binding, và lỗ hổng IDOR mà binding không tự chặn.
- Controller: controller thường, single action (`__invoke`), resource controller và bảy action
  chuẩn của nó.
- Middleware: khái niệm "củ hành", tự viết một pipeline bằng PHP thuần để thấy nó chạy thế nào, ba
  cấp đăng ký (global, group, route), before/after, tham số, thứ tự ưu tiên, terminable middleware.
- Ba middleware có sẵn quan trọng nhất (`PreventRequestForgery`, `auth`, `throttle`), rate limiting
  với `RateLimiter`, và route cache khi deploy.

**Cần biết trước:** [Chương 23](23-laravel-gioi-thieu.md) (cấu trúc dự án Laravel, `bootstrap/app.php`,
vòng đời request ở mức tổng quan). [Chương 15](15-php-va-web.md) (HTTP method, status code, session,
cookie). [Chương 09](09-oop-co-ban.md) và [Chương 10](10-oop-nang-cao.md) (class, interface,
attribute, closure). Biết sơ về [Chương 17](17-bao-mat.md) (CSRF) sẽ dễ đọc mục 7 hơn.

Cách đọc chương này: mục 1 tới 3 nói về route, mục 4 về route model binding, mục 5 về controller, mục
6 về middleware nói chung, mục 7 về các middleware có sẵn quan trọng, mục 8 về rate limiting, mục 9 về
route cache. Các ví dụ PHP thuần (không cần Laravel) đã chạy thật trên PHP 8.5 và có ghi output.
Các đoạn code Laravel lấy theo tài liệu và mã nguồn Laravel 13.x; để chạy chúng bạn cần một dự án
Laravel (tạo như ở Chương 23), rồi gọi bằng trình duyệt, `curl` hoặc `php artisan route:list`.

## 1. Routing là gì

### 1.1 Bài toán: một URL, ai xử lý?

Khi trình duyệt gửi `GET /users/42`, web server (Nginx) chuyển request cho PHP-FPM, và mọi request
của một ứng dụng Laravel đều đi vào cùng một file: `public/index.php` (xem
[Chương 18](18-fpm-nginx-opcache.md) và [Chương 23](23-laravel-gioi-thieu.md)). Như vậy ứng dụng phải
tự trả lời câu hỏi: với method `GET` và đường dẫn `/users/42`, đoạn code nào sẽ chạy?

*Routing* là bước trả lời câu hỏi đó. Một *route* là một quy tắc gồm:

- một hoặc nhiều *HTTP method* (còn gọi là *verb*): `GET`, `POST`, `PUT`, `PATCH`, `DELETE`...
- một mẫu *URI*, có thể chứa chỗ trống gọi là *tham số route* (*route parameter*), ví dụ
  `/users/{id}`;
- một *handler* (*action*): closure hoặc method của controller sẽ chạy khi route khớp.

Thành phần đi tìm route khớp với request gọi là *router*. Ở PHP thuần không có framework, người ta hay
viết `if ($_SERVER['REQUEST_URI'] === '/users') ...` hoặc tạo mỗi trang một file `.php`. Cách đó vỡ
ngay khi URL có phần thay đổi (`/users/42`, `/users/43`...) hoặc khi cùng một URL cần hành xử khác nhau
theo method (`GET /users/42` để xem, `PUT /users/42` để sửa). Router giải quyết cả hai.

### 1.2 Tự viết một router tối giản để hiểu ý tưởng

Trước khi dùng router của Laravel, hãy xem một router 40 dòng viết bằng PHP thuần. Nó không phải code
của Laravel, chỉ minh hoạ ba ý mà router Laravel cũng làm: đổi mẫu URI thành regex, duyệt route theo
thứ tự khai báo và lấy route đầu tiên khớp, phân biệt 404 (không URI nào khớp) với 405 (URI khớp
nhưng sai method).

```php
<?php
declare(strict_types=1);

// Router tối giản: chỉ để hiểu ý tưởng, KHÔNG phải code của Laravel.
final class MiniRouter
{
    /** @var list<array{methods: list<string>, regex: string, params: list<string>, handler: Closure}> */
    private array $routes = [];

    /** @param list<string> $methods */
    public function add(array $methods, string $uri, Closure $handler, array $where = []): void
    {
        $params = [];
        // Đổi '/users/{id}' thành regex '#^/users/(?P<id>[^/]+)$#'
        $regex = preg_replace_callback('/\{(\w+)\}/', function (array $m) use (&$params, $where): string {
            $params[] = $m[1];
            $pattern = $where[$m[1]] ?? '[^/]+';
            return '(?P<' . $m[1] . '>' . $pattern . ')';
        }, $uri);
        $this->routes[] = [
            'methods' => $methods,
            'regex' => '#^' . $regex . '$#',
            'params' => $params,
            'handler' => $handler,
        ];
    }

    public function dispatch(string $method, string $path): string
    {
        $allowed = [];
        foreach ($this->routes as $route) {                 // duyệt theo thứ tự khai báo
            if (preg_match($route['regex'], $path, $m) !== 1) {
                continue;                                    // URI không khớp
            }
            if (!in_array($method, $route['methods'], true)) {
                $allowed = [...$allowed, ...$route['methods']];
                continue;                                    // URI khớp nhưng sai verb
            }
            $args = array_map(fn (string $p): string => $m[$p], $route['params']);
            return ($route['handler'])(...$args);            // route ĐẦU TIÊN khớp thắng
        }
        return $allowed === []
            ? '404 Not Found'
            : '405 Method Not Allowed (Allow: ' . implode(', ', array_unique($allowed)) . ')';
    }
}

$router = new MiniRouter();
$router->add(['GET', 'HEAD'], '/users/{id}', fn (string $id): string => "Xem user $id", ['id' => '[0-9]+']);
$router->add(['PUT'], '/users/{id}', fn (string $id): string => "Sửa user $id", ['id' => '[0-9]+']);
$router->add(['GET', 'HEAD'], '/users/{name}', fn (string $name): string => "Tìm user tên $name");

echo $router->dispatch('GET', '/users/42'), "\n";     // in ra: Xem user 42
echo $router->dispatch('PUT', '/users/42'), "\n";     // in ra: Sửa user 42
echo $router->dispatch('GET', '/users/an'), "\n";     // in ra: Tìm user tên an
echo $router->dispatch('DELETE', '/users/42'), "\n";  // in ra: 405 Method Not Allowed (Allow: GET, HEAD, PUT)
echo $router->dispatch('GET', '/posts/1'), "\n";      // in ra: 404 Not Found
```

Những điều rút ra, và đều đúng với Laravel:

- Tham số route thực chất là một nhóm con trong regex. Mặc định nó khớp "mọi ký tự trừ `/`", nên
  `{id}` không bao giờ nuốt được cả `/users/42/edit`.
- Ràng buộc (`where`) thay regex mặc định bằng regex chặt hơn. Nhờ `[0-9]+`, `/users/an` không khớp
  route thứ nhất mà rơi xuống route thứ ba.
- Thứ tự khai báo quan trọng: route khớp đầu tiên thắng. Nếu bỏ ràng buộc `[0-9]+` ở route đầu thì
  `/users/an` sẽ vào "Xem user an".
- Giá trị tham số luôn là chuỗi (`"42"`, không phải `42`). Muốn có số nguyên hay model phải chuyển
  đổi thêm (mục 2.2 và mục 4).

Router thật của Laravel phức tạp hơn nhiều (biên dịch route bằng component Routing của Symfony, nhóm
route theo method để khỏi duyệt hết, hỗ trợ domain, cache...), nhưng mô hình trong đầu như trên là đủ
để đoán đúng hành vi trong hầu hết tình huống.

### 1.3 File route trong Laravel

Trong Laravel, route khai báo trong thư mục `routes/`. File nào được nạp là do `bootstrap/app.php` cấu
hình:

```php
<?php

use Illuminate\Foundation\Application;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )->create();
```

| File | Dùng cho | Middleware group | Prefix URI |
|---|---|---|---|
| `routes/web.php` | Trang web cho trình duyệt | `web` (cookie mã hoá, session, chống CSRF, model binding) | không |
| `routes/api.php` | API không trạng thái (*stateless*) | `api` (chỉ có model binding) | `/api` |
| `routes/console.php` | Lệnh Artisan dạng closure, lịch chạy (scheduler) | không áp dụng | không áp dụng |

- App mới tạo **không có** `routes/api.php`. Lệnh `php artisan install:api` cài Laravel Sanctum (gói
  xác thực bằng token, xem [Chương 28](28-laravel-auth.md)), tạo `routes/api.php` và đăng ký nó. Prefix
  `/api` đổi được bằng tham số `apiPrefix:` của `withRouting()`.
- `health: '/up'` tạo sẵn một route kiểm tra sức khoẻ ứng dụng, hay dùng cho load balancer.
- Muốn thêm file route riêng (ví dụ `routes/webhooks.php`), truyền closure `then:` cho `withRouting()`
  và đăng ký group trong đó (mục 3.3 nói về group):

```php
use Illuminate\Support\Facades\Route;

->withRouting(
    web: __DIR__.'/../routes/web.php',
    commands: __DIR__.'/../routes/console.php',
    health: '/up',
    then: function () {
        Route::middleware('api')
            ->prefix('webhooks')
            ->name('webhooks.')
            ->group(base_path('routes/webhooks.php'));
    },
)
```

`Route` ở đây là một *facade*: một lớp tĩnh "mặt tiền" chuyển lời gọi tới object router thật trong
service container. Chương 26 giải thích facade hoạt động ra sao; ở chương này bạn chỉ cần biết
`Route::get(...)` là đăng ký route vào router.

### 1.4 Khai báo route theo HTTP verb

Route đơn giản nhất nhận một URI và một closure:

```php
use Illuminate\Support\Facades\Route;

Route::get('/greeting', function () {
    return 'Hello World';
});
```

Router có một method cho mỗi verb thường dùng:

```php
Route::get($uri, $callback);
Route::post($uri, $callback);
Route::put($uri, $callback);
Route::patch($uri, $callback);
Route::delete($uri, $callback);
Route::options($uri, $callback);

Route::match(['get', 'post'], '/', function () { /* ... */ });  // nhiều verb
Route::any('/', function () { /* ... */ });                    // mọi verb
```

Vài điểm cần biết:

- `Route::get()` đăng ký cho cả `GET` và `HEAD` (trong mã nguồn router là
  `addRoute(['GET', 'HEAD'], ...)`). `HEAD` là "như `GET` nhưng chỉ lấy header", nên không cần khai báo
  riêng.
- Nếu URI khớp một route nhưng method không khớp route nào, Laravel trả 405 Method Not Allowed chứ
  không phải 404, giống router tối giản ở mục 1.2.
- Khi nhiều route dùng chung một URI, tài liệu Laravel khuyên khai báo các route `get`, `post`,
  `put`, `patch`, `delete`, `options` trước các route `any`, `match`, `redirect`, để request khớp
  đúng route.
- Closure route có thể type-hint dependency, ví dụ `function (Request $request)`. Laravel dùng service
  container để tự tạo và truyền vào (*dependency injection*, Chương 26).

⚠️ Route `GET` phải "an toàn": chỉ đọc, không thay đổi dữ liệu. Lý do kỹ thuật: middleware chống CSRF
bỏ qua `GET`, `HEAD`, `OPTIONS` (mục 7.1), và trình duyệt, crawler, tính năng prefetch có thể tự gọi
`GET`. Một route `GET /posts/{id}/delete` là một lỗ hổng: chỉ cần một thẻ `<img src=".../delete">` trên
trang khác là xoá được bài.

### 1.5 Route chuyển hướng, route trả view, giả lập method trong form

Hai lối tắt để khỏi viết closure:

```php
Route::redirect('/here', '/there');            // 302 mặc định
Route::redirect('/here', '/there', 301);       // tự chọn status
Route::permanentRedirect('/here', '/there');   // 301

Route::view('/welcome', 'welcome');                       // trả view resources/views/welcome.blade.php
Route::view('/welcome', 'welcome', ['name' => 'Taylor']); // kèm dữ liệu cho view
```

⚠️ Với route `redirect`, tên tham số `destination` và `status` bị Laravel giữ chỗ; với route `view`,
các tên `view`, `data`, `status`, `headers` bị giữ chỗ. Đừng đặt tham số route trùng các tên này.

*Form method spoofing*: form HTML chỉ gửi được `GET` và `POST`. Để gọi route `PUT`, `PATCH`, `DELETE`
từ form, gửi `POST` kèm field ẩn `_method`:

```blade
<form action="/example" method="POST">
    @method('PUT')   {{-- sinh <input type="hidden" name="_method" value="PUT"> --}}
    @csrf            {{-- sinh field _token chống CSRF, mục 7.1 --}}
</form>
```

Laravel đọc `_method` và coi request là `PUT` khi tìm route.

### 1.6 Xem danh sách route: `route:list`

Lệnh Artisan sau (chạy ở thư mục gốc dự án) in mọi route đã đăng ký:

```shell
php artisan route:list                  # method, URI, tên, action
php artisan route:list -v               # kèm middleware và tên middleware group
php artisan route:list -vv              # bung các middleware group ra từng middleware
php artisan route:list --path=api       # chỉ route có URI chứa "api"
php artisan route:list --except-vendor  # ẩn route do package bên thứ ba đăng ký
```

Đây là công cụ kiểm tra số một: muốn biết một route có thật sự được bảo vệ bởi `auth` không, đừng đọc
code rồi đoán, chạy `route:list -v` và nhìn.

## 2. Tham số route và ràng buộc

### 2.1 Tham số bắt buộc

Đặt tên tham số trong ngoặc nhọn. Tên chỉ gồm chữ cái và dấu gạch dưới:

```php
Route::get('/user/{id}', function (string $id) {
    return 'User '.$id;
});

Route::get('/posts/{post}/comments/{comment}', function (string $postId, string $commentId) {
    // ...
});
```

⚠️ Với tham số thường (không phải model binding), Laravel truyền giá trị vào closure hay controller
**theo thứ tự**, không theo tên. Ở ví dụ thứ hai, `$postId` nhận `{post}` vì nó đứng trước, chứ không
phải vì tên giống. Đổi chỗ hai tham số trong chữ ký hàm là đổi nghĩa mà không có lỗi nào báo.

Nếu cần cả dependency lẫn tham số route, đặt dependency trước, tham số route sau:

```php
use Illuminate\Http\Request;

Route::get('/user/{id}', function (Request $request, string $id) {
    return 'User '.$id;
});
```

Vì sao tài liệu Laravel viết `string $id`? Như đã thấy ở mục 1.2, giá trị lấy từ URL luôn là chuỗi.
Nếu bạn khai báo `int $id` thì sao? `declare(strict_types=1)` có hiệu lực theo **file gọi hàm**, không
theo file khai báo hàm (xem [Chương 04](04-kieu-du-lieu.md)). Controller của bạn được gọi từ code
của Laravel, mà các file routing của Laravel không khai báo `strict_types`, nên PHP dùng chế độ ép
kiểu mềm: `"42"` được đổi thành `42`, còn `"abc"` gây `TypeError` và người dùng nhận lỗi 500. Thí
nghiệm nhỏ mô phỏng điều đó:

```php
<?php
// strict_b.php: file của BẠN, có strict_types
declare(strict_types=1);
function show(int $id): string { return 'User ' . $id; }
```

```php
<?php
// strict_a.php: đóng vai "framework", KHÔNG có declare(strict_types=1)
require __DIR__ . '/strict_b.php';
echo show(...['42']), "\n";   // in ra: User 42
try {
    echo show(...['abc']), "\n";
} catch (TypeError $e) {
    echo get_class($e), "\n"; // in ra: TypeError
}
```

Kết luận thực tế: nhận `string`, hoặc nếu khai báo `int` thì phải kèm ràng buộc `whereNumber()` (mục
2.3) để chuỗi không phải số bị loại từ bước khớp route (404) thay vì nổ `TypeError` (500). Cách gọn
nhất thường là model binding (mục 4): nhận thẳng object.

### 2.2 Tham số tuỳ chọn

Thêm `?` sau tên tham số và **bắt buộc** cho biến một giá trị mặc định:

```php
Route::get('/user/{name?}', function (?string $name = null) {
    return $name;
});

Route::get('/user/{name?}', function (?string $name = 'John') {
    return $name;
});
```

Tài liệu Laravel yêu cầu luôn cho biến tương ứng một giá trị mặc định: khi URL không có phần đó, sẽ
không có giá trị nào để truyền vào, và giá trị mặc định là thứ hàm nhận được.

### 2.3 Ràng buộc bằng regex

`where()` giới hạn giá trị hợp lệ của tham số. Nếu không khớp, route coi như không khớp, và nếu
không route nào khác khớp thì kết quả là 404:

```php
Route::get('/user/{name}', function (string $name) {
    // ...
})->where('name', '[A-Za-z]+');

Route::get('/user/{id}', function (string $id) {
    // ...
})->where('id', '[0-9]+');

Route::get('/user/{id}/{name}', function (string $id, string $name) {
    // ...
})->where(['id' => '[0-9]+', 'name' => '[a-z]+']);
```

Các helper cho mẫu hay gặp:

| Helper | Ý nghĩa |
|---|---|
| `whereNumber('id')` | chỉ chữ số |
| `whereAlpha('name')` | chỉ chữ cái |
| `whereAlphaNumeric('name')` | chữ cái và chữ số |
| `whereUuid('id')` | UUID |
| `whereUlid('id')` | ULID |
| `whereIn('category', ['movie', 'song', 'painting'])` | một trong các giá trị cho trước (nhận cả `CategoryEnum::cases()`) |

Ràng buộc dùng chung cho mọi route có tham số cùng tên: khai báo trong `boot()` của
`App\Providers\AppServiceProvider`:

```php
use Illuminate\Support\Facades\Route;

public function boot(): void
{
    Route::pattern('id', '[0-9]+');   // từ giờ mọi {id} chỉ khớp chữ số
}
```

Ràng buộc có hai tác dụng: chặn input rác sớm (trước khi chạm tới controller hay database), và giúp
hai route có cùng "hình dạng" URI không giẫm lên nhau như ví dụ `/users/{id}` và `/users/{name}` ở mục
1.2.

⚠️ Ràng buộc route **không** thay cho validation. Nó chỉ quyết định route có khớp hay không. Kiểm tra
dữ liệu nghiệp vụ (độ dài, tồn tại trong DB, quyền...) vẫn là việc của validation
([Chương 25](25-laravel-request-validation-response.md)) và authorization ([Chương 28](28-laravel-auth.md)).

### 2.4 Cho phép dấu `/` trong tham số

Mặc định tham số nhận mọi ký tự trừ `/`. Muốn nhận cả `/` (ví dụ đường dẫn file), viết regex tường
minh:

```php
Route::get('/search/{search}', function (string $search) {
    return $search;
})->where('search', '.*');
```

Tài liệu Laravel lưu ý: dấu `/` đã mã hoá chỉ được hỗ trợ ở segment cuối cùng của route.

## 3. Tên route, route group và route dự phòng

### 3.1 Đặt tên route và sinh URL từ tên

Nếu trong view bạn viết cứng `href="/user/profile"`, đến ngày đổi URL thành `/me/profile` bạn phải
tìm và sửa mọi chỗ. *Named route* (route có tên) giải quyết việc đó: code tham chiếu tới **tên**, URL
được sinh ra từ định nghĩa route.

```php
Route::get('/user/profile', function () {
    // ...
})->name('profile');

Route::get('/user/profile', [UserProfileController::class, 'show'])->name('profile');
```

Dùng tên để sinh URL hoặc chuyển hướng:

```php
$url = route('profile');               // URL đầy đủ, ví dụ http://example.com/user/profile

return redirect()->route('profile');   // response chuyển hướng
return to_route('profile');            // cách viết ngắn hơn
```

Route có tham số: truyền mảng ở đối số thứ hai. Khoá nào không phải tham số route sẽ thành query
string:

```php
Route::get('/user/{id}/profile', function (string $id) {
    // ...
})->name('profile');

$url = route('profile', ['id' => 1, 'photos' => 'yes']);
// http://example.com/user/1/profile?photos=yes
```

Kiểm tra request hiện tại có đi vào route tên nào đó không (hay dùng trong middleware):
`$request->route()->named('profile')`. Facade `Route` cũng có `Route::currentRouteName()`.

⚠️ Tên route phải duy nhất. Trùng tên thì `route('x')` chỉ trỏ được tới một trong hai route, dễ sinh
link sai mà không có lỗi; còn lệnh `php artisan route:cache` (mục 9) sẽ dừng với `LogicException`
"Another route has already been assigned name [...]". Quy ước phổ biến là đặt tên theo dạng
`tài-nguyên.hành-động`: `posts.index`, `posts.show`, `admin.users.index`.

### 3.2 Route group: dùng chung thuộc tính

Một trang quản trị có thể có hàng chục route cùng cần đăng nhập, cùng prefix `/admin`, cùng tiền tố
tên `admin.`. Lặp lại ba thứ đó trên từng route vừa dài vừa dễ quên. *Route group* gom các route để
chúng dùng chung thuộc tính:

```php
use App\Http\Controllers\Admin\UserController;
use Illuminate\Support\Facades\Route;

Route::middleware(['auth'])
    ->prefix('admin')
    ->name('admin.')
    ->group(function () {
        Route::get('/users', [UserController::class, 'index'])->name('users.index');
        // URI: /admin/users   tên: admin.users.index   middleware: auth (+ group web)
    });
```

Các thuộc tính hay dùng cho group:

| Method | Tác dụng | Ví dụ |
|---|---|---|
| `middleware([...])` | Thêm middleware cho mọi route trong group, chạy theo thứ tự trong mảng | `Route::middleware(['first', 'second'])` |
| `prefix('admin')` | Thêm tiền tố vào URI | `/users` thành `/admin/users` |
| `name('admin.')` | Thêm tiền tố vào **tên**, nối nguyên văn | `users` thành `admin.users` |
| `controller(X::class)` | Mọi route trong group dùng chung controller, chỉ cần ghi tên method | `Route::get('/orders/{id}', 'show')` |
| `domain('{account}.example.com')` | Route theo subdomain, phần subdomain có thể là tham số | tham số `$account` đứng trước các tham số khác |
| `scopeBindings()` | Bật scoped binding cho cả group (mục 4.5) | |
| `withoutMiddleware([...])` | Gỡ middleware route khỏi cả group (mục 6.5) | |

⚠️ `name()` nối chuỗi nguyên văn, nên nhớ dấu chấm cuối: `name('admin.')` chứ không phải
`name('admin')`, nếu không bạn được tên `adminusers.index`.

Group lồng nhau: theo tài liệu Laravel, middleware và điều kiện `where` được **gộp** (con có cả của
cha), còn prefix và tên được **nối** (cha đứng trước). Dấu `/` giữa các prefix được thêm tự động.

```php
Route::prefix('admin')->name('admin.')->middleware('auth')->group(function () {
    Route::prefix('reports')->name('reports.')->middleware('can:view-reports')->group(function () {
        Route::get('/daily', fn () => 'daily')->name('daily');
        // URI: /admin/reports/daily
        // tên: admin.reports.daily
        // middleware (ngoài group web): auth, can:view-reports
    });
});
```

Ví dụ `controller()`:

```php
use App\Http\Controllers\OrderController;

Route::controller(OrderController::class)->group(function () {
    Route::get('/orders/{id}', 'show');   // OrderController::show
    Route::post('/orders', 'store');      // OrderController::store
});
```

Từ Laravel 13, route có domain tường minh được ưu tiên khớp trước route không có domain, bất kể thứ tự
đăng ký (theo hướng dẫn nâng cấp 13.x). Nếu ứng dụng cũ dựa vào thứ tự đăng ký giữa hai loại route
này, cần kiểm tra lại khi nâng cấp.

### 3.3 Route dự phòng (fallback)

`Route::fallback()` khai báo route chạy khi **không** route nào khác khớp. Nếu không khai báo,
Laravel tự render trang 404 qua exception handler. Fallback hữu ích khi muốn trang 404 riêng mà vẫn có
session, người dùng đăng nhập... vì khai báo trong `routes/web.php` thì nó chạy qua group `web`:

```php
Route::fallback(function () {
    return response()->view('errors.not-found', [], 404);
});
```

Trong mã nguồn router, khi duyệt danh sách route, route fallback bị "để dành" và chỉ được dùng nếu
duyệt hết mà không route thường nào khớp. Vì vậy vị trí khai báo fallback trong file không ảnh hưởng
kết quả, nhưng theo thói quen người ta vẫn đặt nó cuối file.

## 4. Route model binding

### 4.1 Vấn đề: lặp lại `findOrFail` ở mọi nơi

Gần như mọi route có `{id}` đều mở đầu bằng cùng một việc: lấy bản ghi từ DB, không có thì trả 404.

```php
use App\Models\Post;

Route::get('/posts/{id}', function (string $id) {
    $post = Post::findOrFail($id);   // không thấy thì ném ModelNotFoundException, Laravel đổi thành 404
    return view('posts.show', ['post' => $post]);
});
```

*Route model binding* là tính năng để Laravel làm việc đó thay bạn: bạn khai báo "tham số này là một
`Post`", Laravel lấy giá trị trong URL, tìm `Post` tương ứng và truyền object vào. (`Post` là một
*Eloquent model*, lớp đại diện cho một bảng; [Chương 27](27-laravel-database-eloquent.md) dạy Eloquent.
Ở đây chỉ cần biết `Post` tương ứng bảng `posts`, khoá chính `id`.)

### 4.2 Implicit binding: theo quy ước tên

Điều kiện: biến có type-hint là một Eloquent model **và** tên biến trùng tên segment trong URI.

```php
use App\Models\User;

Route::get('/users/{user}', function (User $user) {
    return $user->email;
});
```

`{user}` khớp `$user`, kiểu là `User`, nên Laravel chạy truy vấn tương đương
`select * from users where id = ? limit 1` với giá trị từ URL. Không có bản ghi thì trả 404. Cách này
hoạt động y hệt với method controller:

```php
use App\Http\Controllers\UserController;

Route::get('/users/{user}', [UserController::class, 'show']);

// trong UserController
public function show(User $user)
{
    return view('user.profile', ['user' => $user]);
}
```

⚠️ Tên phải khớp (mã nguồn chấp nhận thêm một biến thể: biến `$postComment` khớp segment
`{post_comment}`, tức dạng snake_case của tên biến). `Route::get('/users/{id}', fn (User $user) => ...)`
không bind: `$user` không trùng `{id}`, nên Laravel không lấy giá trị nào từ URL cho nó, và service
container sẽ tạo một object `User` mới, rỗng, chưa lưu DB. Khi controller nhận "model rỗng, không có
thuộc tính", kiểm tra tên segment và tên biến trước tiên.

### 4.3 Tìm theo cột khác: `{post:slug}`, `#[RouteKey]`, `getRouteKeyName()`

URL đẹp thường dùng *slug* (`/posts/hoc-laravel`) thay vì id. Chỉ định cột ngay trong segment:

```php
use App\Models\Post;

Route::get('/posts/{post:slug}', function (Post $post) {
    return $post;   // tìm where slug = 'hoc-laravel'
});
```

Nếu model **luôn** được tìm theo cột khác, khai báo một lần trên model. Laravel 13 có attribute
`RouteKey`:

```php
use Illuminate\Database\Eloquent\Attributes\RouteKey;
use Illuminate\Database\Eloquent\Model;

#[RouteKey('slug')]
class Post extends Model
{
    // ...
}
```

Bên trong, `Model::getRouteKeyName()` của Laravel 13 đọc attribute `RouteKey`, không có thì trả tên
khoá chính (`id`). Vì vậy cách cũ (vẫn chạy) là override method đó:

```php
class Post extends Model
{
    public function getRouteKeyName(): string
    {
        return 'slug';
    }
}
```

Một hệ quả dễ quên: route key cũng được dùng theo chiều ngược lại. Khi bạn viết
`route('posts.show', $post)` (truyền cả model), Laravel lấy `$post->getRouteKey()`, tức giá trị của cột
route key, để điền vào URL. Đổi route key sang `slug` là mọi link sinh từ model tự đổi theo.

⚠️ Cột dùng làm route key nên có index UNIQUE trong DB: mỗi request đều truy vấn theo cột đó, và hai
bản ghi trùng slug thì URL trỏ tới bản ghi nào là không xác định.

### 4.4 Bản ghi xoá mềm, enum, và tuỳ biến khi không tìm thấy

- *Soft delete* (xoá mềm, đánh dấu `deleted_at` thay vì xoá thật, Chương 27): implicit binding mặc
  định **không** trả bản ghi đã xoá mềm. Thêm `->withTrashed()` vào route nếu muốn lấy cả chúng.
- Không tìm thấy thì mặc định 404. Muốn làm khác (ví dụ chuyển hướng về trang danh sách), dùng
  `missing()`:

```php
use App\Http\Controllers\LocationsController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Redirect;

Route::get('/locations/{location:slug}', [LocationsController::class, 'show'])
    ->name('locations.view')
    ->missing(function (Request $request) {
        return Redirect::route('locations.index');
    });
```

- *Enum binding*: type-hint một *backed enum* kiểu string (enum có giá trị, [Chương 10](10-oop-nang-cao.md))
  thì route chỉ chạy khi segment là một giá trị hợp lệ của enum, ngược lại 404:

```php
namespace App\Enums;

enum Category: string
{
    case Fruits = 'fruits';
    case People = 'people';
}
```

```php
use App\Enums\Category;

Route::get('/categories/{category}', function (Category $category) {
    return $category->value;   // /categories/fruits -> "fruits"; /categories/cars -> 404
});
```

### 4.5 Scoped binding: route lồng nhau

Xét `/users/{user}/posts/{post}`. Implicit binding tìm `User` theo `{user}` và `Post` theo `{post}`
**độc lập** với nhau. Mặc định Laravel không kiểm tra post đó có thuộc user đó không, nên
`/users/1/posts/999` vẫn trả về post 999 dù nó của user 7.

*Scoped binding* bắt bản ghi con phải thuộc bản ghi cha:

```php
use App\Models\Post;
use App\Models\User;

Route::get('/users/{user}/posts/{post}', function (User $user, Post $post) {
    return $post;
})->scopeBindings();

// hoặc cho cả group
Route::scopeBindings()->group(function () {
    Route::get('/users/{user}/posts/{post}', function (User $user, Post $post) {
        return $post;
    });
});
```

Khi scope, Laravel tìm post thông qua relationship của user: nó đoán tên relationship là dạng số nhiều
của tên tham số (`posts`), tức tương đương `$user->posts()->where('id', ...)`. Model `User` phải có
method `posts()` (relationship `hasMany`, Chương 27).

Có một trường hợp Laravel **tự** scope mà không cần `scopeBindings()`: khi tham số con dùng custom key,
ví dụ `/users/{user}/posts/{post:slug}`. Muốn tắt hành vi tự động đó thì gọi `->withoutScopedBindings()`.

| URI | Có `scopeBindings()`? | Post có bị buộc thuộc user? |
|---|---|---|
| `/users/{user}/posts/{post}` | không | không |
| `/users/{user}/posts/{post}` | có | có |
| `/users/{user}/posts/{post:slug}` | không | có (tự động vì custom key) |
| `/users/{user}/posts/{post:slug}` + `withoutScopedBindings()` | | không |

### 4.6 Explicit binding: tự khai báo cách tìm

Khi quy ước không đủ, khai báo tường minh trong `boot()` của `AppServiceProvider`. Tài liệu Laravel
khuyên đặt ở đầu method `boot`.

```php
use App\Models\User;
use Illuminate\Support\Facades\Route;

public function boot(): void
{
    // Mọi tham số {user} đều là User, tìm theo route key như implicit binding
    Route::model('user', User::class);

    // Hoặc tự viết logic tìm: closure nhận chuỗi từ URL, trả về object
    Route::bind('user', function (string $value) {
        return User::where('name', $value)->firstOrFail();
    });
}
```

(Ví dụ trên chỉ để minh hoạ hai cách; thực tế chọn một cho mỗi tên tham số.)

Cách thứ ba là override `resolveRouteBinding()` trên model. Method này nhận giá trị từ URL (và tên cột
nếu route ghi `{post:slug}`) rồi trả về model hoặc `null`:

```php
public function resolveRouteBinding($value, $field = null)
{
    return $this->where('name', $value)->firstOrFail();
}
```

Với scoped binding, method tương ứng cho bản ghi con là `resolveChildRouteBinding()`.

### 4.7 Bên trong: ai làm binding và khi nào?

Binding không phải phép màu của router mà là việc của một **middleware**:
`Illuminate\Routing\Middleware\SubstituteBindings`, có sẵn trong cả group `web` và `api`. (Mục 6 dạy
middleware; tạm hiểu là một bước xử lý chạy trước controller.) Theo mã nguồn Laravel 13:

```
GET /users/42/posts/7
  │
  ▼
Router khớp route '/users/{user}/posts/{post}'
  → tham số: ['user' => '42', 'post' => '7']      (vẫn là chuỗi)
  │
  ▼
middleware ... (session, CSRF, ...)
  │
  ▼
SubstituteBindings::handle()
  1. substituteBindings():         với tham số có explicit binding (Route::model / Route::bind)
                                   → gọi binder, thay chuỗi bằng object
  2. substituteImplicitBindings(): với tham số còn lại, nếu handler có biến cùng tên
                                   type-hint model → resolveRouteBinding() (hoặc
                                   resolveChildRouteBinding() khi scoped)
     không tìm thấy → ModelNotFoundException
        → route có missing()? gọi closure đó : ném tiếp → exception handler trả 404
  │
  ▼
tham số: ['user' => User#42, 'post' => Post#7]
  │
  ▼
controller->show(User $user, Post $post)
```

Hai hệ quả quan trọng:

- Middleware nào chạy **trước** `SubstituteBindings` chỉ thấy chuỗi `'42'`, chưa thấy model. Laravel
  có một danh sách ưu tiên (mục 6.6) để những middleware cần model, như `Authorize` (alias `can`),
  luôn chạy sau `SubstituteBindings`.
- Mỗi tham số bind là một truy vấn DB. Route có ba tham số model là ba truy vấn, chạy trước cả khi
  controller bắt đầu.

### 4.8 ⚠️ Binding không phải kiểm tra quyền: IDOR

Binding chỉ trả lời "bản ghi này có tồn tại không", không trả lời "người đang đăng nhập có được xem
nó không". Route sau là lỗ hổng điển hình:

```php
Route::get('/orders/{order}', function (Order $order) {
    return $order;   // ai đăng nhập cũng xem được MỌI đơn, chỉ cần đổi số trên URL
})->middleware('auth');
```

Lỗi này gọi là *IDOR* (*Insecure Direct Object Reference*, tham chiếu trực tiếp tới object mà không
kiểm soát quyền): đổi `/orders/1001` thành `/orders/1002` là xem được đơn của người khác. `auth` chỉ
chứng minh "đã đăng nhập", không chứng minh "là chủ đơn". Scoped binding cũng không cứu được: nó đảm bảo
post thuộc `{user}` trên URL, nhưng `{user}` do chính người gửi request điền.

Cách sửa là kiểm tra quyền (authorization), ví dụ bằng middleware `can` gắn với một *policy*
(Chương 28 dạy policy):

```php
use App\Models\Order;

Route::get('/orders/{order}', function (Order $order) {
    return $order;
})->middleware(['auth', 'can:view,order']);   // gọi OrderPolicy::view($user, $order)
```

Ở đây `can:view,order` nghĩa là "kiểm tra ability `view` với tham số route tên `order`". Nhờ danh sách
ưu tiên, `can` chạy sau `SubstituteBindings` nên nhận được object `Order` thật chứ không phải chuỗi.

## 5. Controller

### 5.1 Vì sao cần controller

Closure trong file route tiện cho vài dòng, nhưng khi ứng dụng lớn lên, `routes/web.php` sẽ thành một
file nghìn dòng trộn lẫn khai báo URL với logic xử lý. *Controller* là class gom các handler liên quan
vào một chỗ: `UserController` xử lý xem, tạo, sửa, xoá user. File route chỉ còn là "bản đồ" URL tới
method.

Lợi ích cụ thể ngoài việc gọn file:

- Controller được tạo bằng service container, nên nhận dependency qua constructor (mục 5.3).
- Route trỏ tới controller là chuỗi tên class, dễ đọc trong `route:list`.
- Dễ gắn middleware theo từng action (mục 5.6).

Controller mặc định nằm ở `app/Http/Controllers`. Tạo bằng Artisan (chạy ở thư mục gốc dự án):

```shell
php artisan make:controller UserController
```

### 5.2 Controller cơ bản

```php
<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\View\View;

class UserController extends Controller
{
    public function show(string $id): View
    {
        return view('user.profile', [
            'user' => User::findOrFail($id),
        ]);
    }
}
```

```php
use App\Http\Controllers\UserController;

Route::get('/user/{id}', [UserController::class, 'show']);
```

Cú pháp `[UserController::class, 'show']` là một mảng hai phần tử: tên class và tên method (giống
*callable* dạng mảng ở [Chương 08](08-ham.md)). Laravel tạo instance controller qua container rồi gọi
method, truyền tham số route vào.

Controller **không bắt buộc** kế thừa class nào. Skeleton có sẵn `App\Http\Controllers\Controller` làm
class cha, tiện để đặt code dùng chung, nhưng đó chỉ là quy ước.

⚠️ Lỗi kinh điển khi mới học: "fat controller", nhồi truy vấn phức tạp, gọi API ngoài, tính toán
nghiệp vụ vào thẳng controller. Controller nên mỏng: nhận input đã kiểm tra, gọi tầng nghiệp vụ
(service, action class, model), trả response. Logic để trong controller không tái sử dụng được từ
command, job hay test đơn vị.

### 5.3 Dependency injection trong controller

Laravel tạo controller bằng *service container*, nên có thể khai báo dependency ở constructor hoặc
ở từng method; container tự tạo và truyền vào (cơ chế chi tiết ở Chương 26).

```php
<?php

namespace App\Http\Controllers;

use App\Repositories\UserRepository;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

class UserController extends Controller
{
    // Constructor injection: dùng cho mọi action
    public function __construct(
        protected UserRepository $users,
    ) {}

    // Method injection: Request chỉ cần cho action này
    // Tham số route {id} đặt SAU các dependency
    public function update(Request $request, string $id): RedirectResponse
    {
        // ...
        return redirect('/users');
    }
}
```

```php
Route::put('/user/{id}', [UserController::class, 'update']);
```

Quy tắc giống closure route (mục 2.1): dependency có type-hint class đứng trước, tham số route đứng
sau.

### 5.4 Single action controller

Khi một action đủ phức tạp để đứng riêng (ví dụ "cấp phát server mới"), dành cả class cho nó với một
method `__invoke` (magic method khiến object gọi được như hàm, [Chương 10](10-oop-nang-cao.md)):

```php
<?php

namespace App\Http\Controllers;

class ProvisionServer extends Controller
{
    public function __invoke()
    {
        // ...
    }
}
```

Route chỉ cần tên class, không cần tên method:

```php
use App\Http\Controllers\ProvisionServer;

Route::post('/server', ProvisionServer::class);
```

Tạo nhanh bằng `php artisan make:controller ProvisionServer --invokable`.

Nhiều đội ưu tiên single action controller vì mỗi class chỉ làm một việc, tên class nói luôn việc đó
(`PublishPost`, `CancelOrder`), và constructor chỉ chứa dependency mà action đó thật sự cần.

### 5.5 Resource controller

Rất nhiều tài nguyên có cùng bộ thao tác *CRUD* (Create, Read, Update, Delete: tạo, đọc, sửa, xoá).
Laravel chuẩn hoá bộ đó thành *resource route*: một dòng sinh ra bảy route.

```shell
php artisan make:controller PhotoController --resource
# thêm --model=Photo để method nhận sẵn Photo $photo (model binding)
# thêm --requests để sinh luôn Form Request cho store và update (Chương 25)
```

```php
use App\Http\Controllers\PhotoController;

Route::resource('photos', PhotoController::class);
```

Bảy route được sinh ra:

| Verb | URI | Action | Tên route | Làm gì |
|---|---|---|---|---|
| GET | `/photos` | index | photos.index | danh sách |
| GET | `/photos/create` | create | photos.create | form tạo mới |
| POST | `/photos` | store | photos.store | lưu bản ghi mới |
| GET | `/photos/{photo}` | show | photos.show | xem một bản ghi |
| GET | `/photos/{photo}/edit` | edit | photos.edit | form sửa |
| PUT/PATCH | `/photos/{photo}` | update | photos.update | lưu thay đổi |
| DELETE | `/photos/{photo}` | destroy | photos.destroy | xoá |

Để ý tên tham số `{photo}`: Laravel lấy dạng số ít của tên resource. Nhờ vậy method
`show(Photo $photo)` tự có model binding (mục 4.2). Muốn đổi tên tham số dùng `parameters()`:

```php
Route::resource('users', AdminUserController::class)->parameters([
    'users' => 'admin_user',
]);   // URI show: /users/{admin_user}
```

Các biến thể hay dùng:

```php
// Chỉ lấy một phần action
Route::resource('photos', PhotoController::class)->only(['index', 'show']);
Route::resource('photos', PhotoController::class)->except(['create', 'store', 'update', 'destroy']);

// API không cần form HTML: bỏ create và edit, còn 5 route
Route::apiResource('photos', PhotoController::class);
// tạo controller tương ứng: php artisan make:controller PhotoController --api

// Đăng ký nhiều resource một lúc
Route::resources([
    'photos' => PhotoController::class,
    'posts' => PostController::class,
]);

// Đổi tên route của một action
Route::resource('photos', PhotoController::class)->names(['create' => 'photos.build']);

// Không tìm thấy model thì chuyển hướng thay vì 404
Route::resource('photos', PhotoController::class)
    ->missing(fn (Request $request) => Redirect::route('photos.index'));

// Cho phép bản ghi xoá mềm ở show, edit, update
Route::resource('photos', PhotoController::class)->withTrashed();
```

*Nested resource*: tài nguyên con của tài nguyên cha, viết bằng dấu chấm:

```php
Route::resource('photos.comments', PhotoCommentController::class);
// URI dạng /photos/{photo}/comments/{comment}

Route::resource('photos.comments', PhotoCommentController::class)->scoped([
    'comment' => 'slug',
]);   // /photos/{photo}/comments/{comment:slug}, comment phải thuộc photo (mục 4.5)
```

*Shallow nesting*: khi id của con đã là duy nhất toàn bảng, không cần id cha trong URL của các action
thao tác trên một bản ghi con. `->shallow()` chỉ giữ id cha ở `index`, `create`, `store`:

| Verb | URI | Action | Tên route |
|---|---|---|---|
| GET | `/photos/{photo}/comments` | index | photos.comments.index |
| GET | `/photos/{photo}/comments/create` | create | photos.comments.create |
| POST | `/photos/{photo}/comments` | store | photos.comments.store |
| GET | `/comments/{comment}` | show | comments.show |
| GET | `/comments/{comment}/edit` | edit | comments.edit |
| PUT/PATCH | `/comments/{comment}` | update | comments.update |
| DELETE | `/comments/{comment}` | destroy | comments.destroy |

*Singleton resource*: tài nguyên chỉ có một bản ghi (hồ sơ của người dùng hiện tại) nên không có
`index`, `create`, `store` và URI không có id:

```php
Route::singleton('profile', ProfileController::class);
// GET /profile (show), GET /profile/edit (edit), PUT/PATCH /profile (update)
```

Thêm `->creatable()` để có cả `create`, `store`, `destroy`; `->destroyable()` để chỉ thêm `destroy`;
`Route::apiSingleton()` là bản không có `create` và `edit`.

⚠️ Thêm route ngoài bộ chuẩn: khai báo **trước** `Route::resource`. Nếu đặt sau, `GET /photos/popular`
sẽ khớp route `GET /photos/{photo}` trước (vì `popular` là một giá trị hợp lệ của `{photo}`), Laravel
tìm `Photo` có id `popular` và trả 404.

```php
Route::get('/photos/popular', [PhotoController::class, 'popular']);   // trước
Route::resource('photos', PhotoController::class);                     // sau
```

Tài liệu Laravel cũng nhắc: nếu thường xuyên cần thêm action ngoài bộ chuẩn, đó là dấu hiệu nên tách
controller nhỏ hơn.

### 5.6 Gắn middleware cho controller

Middleware (mục 6) có thể gắn ở file route như mọi route khác:

```php
Route::get('/profile', [UserController::class, 'show'])->middleware('auth');
```

Hoặc khai báo ngay trong controller. Cách thứ nhất: implement interface `HasMiddleware` và trả về danh
sách trong method tĩnh `middleware()`; `only` và `except` giới hạn theo action:

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Routing\Controllers\HasMiddleware;
use Illuminate\Routing\Controllers\Middleware;

class UserController implements HasMiddleware
{
    public static function middleware(): array
    {
        return [
            'auth',
            new Middleware('log', only: ['index']),
            new Middleware('subscribed', except: ['store']),
        ];
    }

    // ...
}
```

Cách thứ hai trong Laravel 13: dùng *attribute* PHP (cú pháp `#[...]`, [Chương 10](10-oop-nang-cao.md))
`Illuminate\Routing\Attributes\Controllers\Middleware`, đặt ở class hoặc ở từng method; middleware ở
method được gộp với middleware ở class:

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Routing\Attributes\Controllers\Middleware;

#[Middleware('auth')]
class UserController
{
    #[Middleware('log')]
    public function index()
    {
        // chạy qua: auth, log
    }
}
```

Attribute `WithoutMiddleware` gỡ bớt middleware route; attribute `Authorize` là lối tắt cho middleware
`can` (Chương 28).

Với resource route, gắn middleware theo action ở file route bằng `middlewareFor()` và
`withoutMiddlewareFor()`:

```php
Route::resource('users', UserController::class)
    ->middleware('auth')                     // mọi action
    ->middlewareFor(['update'], 'verified')  // chỉ update
    ->withoutMiddlewareFor('index', 'auth'); // index không cần đăng nhập
```

Nên chọn một chỗ khai báo cho cả dự án (file route, hoặc trong controller). Trộn hai chỗ khiến người
đọc phải mở nhiều file mới biết route có được bảo vệ không; khi nghi ngờ, dùng `route:list -v`.

## 6. Middleware

### 6.1 Middleware là gì

Có những việc cần làm cho **nhiều** route, và không thuộc về logic riêng của route nào: kiểm tra đã
đăng nhập chưa, chống CSRF, giới hạn số request, mở session, ghi log, thêm header bảo mật. Nhét chúng
vào từng controller thì lặp code và chắc chắn có ngày quên.

*Middleware* là một lớp xử lý đặt **giữa** request và controller. Mỗi middleware nhận request và có
ba lựa chọn:

1. Cho đi tiếp: gọi `$next($request)` để chuyển request vào lớp bên trong (middleware kế tiếp, cuối
   cùng là controller).
2. Chặn lại: trả một response ngay (chuyển hướng tới trang đăng nhập, 403, 429...) mà không gọi
   `$next`. Controller không bao giờ chạy. Hiện tượng này gọi là *short-circuit* (ngắt mạch).
3. Đi tiếp rồi sửa kết quả: gọi `$next($request)`, nhận response trả về, chỉnh nó (thêm header,
   nén...), rồi trả response đó ra ngoài.

Hình ảnh hay dùng là củ hành: controller ở lõi, mỗi middleware là một lớp vỏ. Request đi từ ngoài vào
qua từng lớp, response đi từ lõi ra qua đúng các lớp đó theo thứ tự ngược lại.

```
              ┌──────────────────── Log ────────────────────┐
              │        ┌─────────── Auth ───────────┐       │
              │        │      ┌── AddHeader ──┐      │       │
request ────► │ ─────► │ ───► │ ──► Controller│      │       │
              │        │      │        │      │      │       │
response ◄─── │ ◄───── │ ◄─── │ ◄──────┘      │      │       │
              │        │      └───────────────┘      │       │
              │        └─────────────────────────────┘       │
              └──────────────────────────────────────────────┘
```

### 6.2 Tự viết một pipeline để thấy nó chạy

Laravel nối middleware bằng class `Illuminate\Pipeline\Pipeline`. Lõi của nó là một lời gọi
`array_reduce` trên danh sách middleware **đã đảo ngược**, mỗi bước bọc closure hiện có vào trong một
closure mới. Đoạn PHP thuần dưới đây tái hiện đúng ý tưởng đó (request và response chỉ là mảng cho
gọn):

```php
<?php
declare(strict_types=1);

// Mô phỏng pipeline middleware của Laravel bằng PHP thuần.

interface Middleware
{
    /** @param Closure(array): array $next */
    public function handle(array $request, Closure $next): array;
}

final class LogMiddleware implements Middleware
{
    public function handle(array $request, Closure $next): array
    {
        echo "Log: vào {$request['path']}\n";            // TRƯỚC: chạy trên đường vào
        $response = $next($request);                      // đưa request vào lớp trong
        echo "Log: ra với status {$response['status']}\n"; // SAU: chạy trên đường ra
        return $response;
    }
}

final class AuthMiddleware implements Middleware
{
    public function handle(array $request, Closure $next): array
    {
        if ($request['user'] === null) {
            echo "Auth: chặn, không gọi \$next\n";
            return ['status' => 401, 'body' => 'Unauthenticated'];  // ngắt mạch
        }
        echo "Auth: cho qua\n";
        return $next($request);
    }
}

final class AddHeaderMiddleware implements Middleware
{
    public function handle(array $request, Closure $next): array
    {
        $response = $next($request);
        $response['headers']['X-Powered-By'] = 'pipeline';   // sửa response trên đường ra
        echo "AddHeader: thêm header\n";
        return $response;
    }
}

/**
 * Giống Illuminate\Pipeline\Pipeline::then(): gói các middleware lồng nhau
 * bằng array_reduce trên mảng ĐÃ ĐẢO NGƯỢC, lõi trong cùng là $destination.
 *
 * @param list<Middleware> $pipes
 * @param Closure(array): array $destination
 */
function runPipeline(array $pipes, array $request, Closure $destination): array
{
    $onion = array_reduce(
        array_reverse($pipes),
        fn (Closure $stack, Middleware $pipe): Closure
            => fn (array $req): array => $pipe->handle($req, $stack),
        $destination,
    );
    return $onion($request);
}

$controller = function (array $request): array {
    echo "Controller: xử lý\n";
    return ['status' => 200, 'body' => 'Hello ' . $request['user'], 'headers' => []];
};

$pipes = [new LogMiddleware(), new AuthMiddleware(), new AddHeaderMiddleware()];

echo "--- Có đăng nhập ---\n";
$res = runPipeline($pipes, ['path' => '/home', 'user' => 'an'], $controller);
echo json_encode($res), "\n";

echo "--- Chưa đăng nhập ---\n";
$res = runPipeline($pipes, ['path' => '/home', 'user' => null], $controller);
echo json_encode($res), "\n";
```

Output (đã chạy thật):

```
--- Có đăng nhập ---
Log: vào /home
Auth: cho qua
Controller: xử lý
AddHeader: thêm header
Log: ra với status 200
{"status":200,"body":"Hello an","headers":{"X-Powered-By":"pipeline"}}
--- Chưa đăng nhập ---
Log: vào /home
Auth: chặn, không gọi $next
Log: ra với status 401
{"status":401,"body":"Unauthenticated"}
```

Đọc kỹ output:

- Vì sao phải đảo ngược mảng? `array_reduce` bọc từ trong ra ngoài. Phần tử được xử lý **cuối cùng**
  thành lớp **ngoài cùng**. Đảo ngược trước khi reduce để `Log` (đứng đầu danh sách) thành lớp ngoài
  cùng, tức chạy đầu tiên trên đường vào.
- `$next` của mỗi middleware chính là closure của lớp bên trong nó. Gọi `$next` là "đi vào trong"; giá
  trị trả về của `$next` là response đã đi qua mọi lớp bên trong.
- Trường hợp chưa đăng nhập: `Auth` không gọi `$next`, nên `AddHeader` và controller không chạy, nhưng
  phần "SAU" của `Log` vẫn chạy vì `Log` bọc ngoài `Auth`. Lớp ngoài luôn thấy response cuối cùng,
  dù lớp trong chặn.

### 6.3 Viết middleware trong Laravel

Tạo bằng Artisan (file sinh ra ở `app/Http/Middleware`):

```shell
php artisan make:middleware EnsureTokenIsValid
```

```php
<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class EnsureTokenIsValid
{
    /**
     * @param  \Closure(\Illuminate\Http\Request): (\Symfony\Component\HttpFoundation\Response)  $next
     */
    public function handle(Request $request, Closure $next): Response
    {
        if ($request->input('token') !== 'my-secret-token') {
            return redirect('/home');     // chặn: không gọi $next
        }

        return $next($request);           // cho đi tiếp
    }
}
```

Chữ ký luôn là `handle(Request $request, Closure $next)` và phải trả về response. Middleware được
tạo qua service container, nên constructor có thể nhận dependency.

Before và after middleware chỉ khác nhau ở chỗ đặt code so với `$next`:

```php
// Làm việc TRƯỚC khi request vào ứng dụng
public function handle(Request $request, Closure $next): Response
{
    // ... ví dụ: kiểm tra, gắn thêm dữ liệu vào request
    return $next($request);
}

// Làm việc SAU khi ứng dụng đã tạo response
public function handle(Request $request, Closure $next): Response
{
    $response = $next($request);
    // ... ví dụ: thêm header
    return $response;
}
```

Ví dụ thực tế kết hợp cả hai: gắn một mã định danh cho mỗi request để lần theo log.

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

Một chi tiết quan trọng khi viết phần "SAU": trong Laravel, nếu controller (hay middleware bên trong)
ném exception, pipeline của Laravel (`Illuminate\Routing\Pipeline`) bắt nó, cho exception handler
`report` và `render` thành response (404, 500...), rồi trả response đó ra ngoài như bình thường. Vì vậy
phần "SAU" của middleware bên ngoài vẫn chạy và nhận được một response lỗi, chứ không nhận exception.

⚠️ Quên `return`: `$next($request);` mà không `return` thì `handle` trả `null`, vi phạm kiểu trả về
`Response` và thành `TypeError`. Khai báo kiểu trả về `: Response` giúp lỗi lộ ra ngay thay vì âm thầm.

### 6.4 Tham số cho middleware

Middleware nhận thêm tham số, đặt sau `$next`:

```php
public function handle(Request $request, Closure $next, string $role): Response
{
    if (! $request->user()->hasRole($role)) {
        abort(403);
    }

    return $next($request);
}
```

Khi gắn vào route, viết tên middleware, dấu hai chấm, rồi các tham số cách nhau dấu phẩy:

```php
use App\Http\Middleware\EnsureUserHasRole;

Route::put('/post/{id}', function (string $id) {
    // ...
})->middleware(EnsureUserHasRole::class.':editor');

Route::put('/post/{id}', function (string $id) {
    // ...
})->middleware(EnsureUserHasRole::class.':editor,publisher');   // hai tham số
```

Đây chính là cú pháp của `throttle:60,1`, `can:update,post`, `auth:sanctum` mà bạn sẽ gặp ở mục 7.
Tham số đến middleware luôn là **chuỗi**.

### 6.5 Ba cấp đăng ký: global, group, route

Middleware viết xong phải đăng ký thì mới chạy. Laravel 13 cấu hình trong `bootstrap/app.php`, qua
closure của `withMiddleware()`, nhận object `Illuminate\Foundation\Configuration\Middleware`.

| Cấp | Đăng ký | Chạy cho | Ghi chú |
|---|---|---|---|
| Global | `$middleware->append(X::class)`, `prepend(X::class)` | Mọi request, kể cả request không khớp route nào | Chạy trước khi router tìm route |
| Group | `$middleware->web(append: [...])`, `api(prepend: [...])`, `appendToGroup('ten', [...])` | Mọi route gắn group đó | `web` và `api` tự gắn cho `routes/web.php` và `routes/api.php` |
| Route | `->middleware(X::class)` hoặc alias `->middleware('auth')` trên route hay group | Route cụ thể | Có thể gỡ bằng `withoutMiddleware()` |

```php
use App\Http\Middleware\AddRequestId;
use App\Http\Middleware\EnsureUserIsSubscribed;
use Illuminate\Foundation\Configuration\Middleware;

->withMiddleware(function (Middleware $middleware): void {
    $middleware->append(AddRequestId::class);                 // global, cuối danh sách

    $middleware->web(append: [EnsureUserIsSubscribed::class]); // thêm vào group web

    $middleware->alias([                                       // đặt tên ngắn
        'subscribed' => EnsureUserIsSubscribed::class,
    ]);
})
```

Global middleware mặc định của Laravel 13 (theo `getGlobalMiddleware()` trong mã nguồn):

| Middleware | Việc |
|---|---|
| `ValidatePathEncoding` | Từ chối request có path, sau khi giải mã `%xx`, không phải UTF-8 hợp lệ |
| `InvokeDeferredCallbacks` | Chạy các callback hoãn (`defer()`) sau khi gửi response |
| `TrustHosts` (chỉ khi bật) | Chỉ chấp nhận header `Host` hợp lệ |
| `TrustProxies` | Tin header `X-Forwarded-*` từ proxy/load balancer đã cấu hình |
| `HandleCors` | Trả lời CORS |
| `PreventRequestsDuringMaintenance` | Trả 503 khi đang `php artisan down` |
| `ValidatePostSize` | Từ chối body vượt `post_max_size` |
| `TrimStrings` | Cắt khoảng trắng đầu cuối của input |
| `ConvertEmptyStringsToNull` | Chuỗi rỗng trong input thành `null` |

Middleware group mặc định:

| Group `web` | Group `api` |
|---|---|
| `EncryptCookies` | `SubstituteBindings` |
| `AddQueuedCookiesToResponse` | |
| `StartSession` | |
| `ShareErrorsFromSession` | |
| `PreventRequestForgery` (chống CSRF) | |
| `SubstituteBindings` (model binding) | |

⚠️ Group `api` mặc định **không** có `throttle`. Muốn giới hạn tần suất cho API phải tự bật (mục 8.2),
ví dụ `$middleware->throttleApi()` (thêm `throttle:api` vào group `api`) kèm định nghĩa limiter `api`.

⚠️ `ConvertEmptyStringsToNull` là global: field để trống trong form đến controller là `null` chứ không
phải `''`. Rule validation cho field tuỳ chọn cần `nullable` (Chương 25).

Alias có sẵn (một phần, theo tài liệu Laravel 13):

| Alias | Class |
|---|---|
| `auth` | `Illuminate\Auth\Middleware\Authenticate` |
| `auth.basic` | `Illuminate\Auth\Middleware\AuthenticateWithBasicAuth` |
| `can` | `Illuminate\Auth\Middleware\Authorize` |
| `guest` | `Illuminate\Auth\Middleware\RedirectIfAuthenticated` |
| `password.confirm` | `Illuminate\Auth\Middleware\RequirePassword` |
| `signed` | `Illuminate\Routing\Middleware\ValidateSignature` |
| `throttle` | `Illuminate\Routing\Middleware\ThrottleRequests` (hoặc bản Redis) |
| `verified` | `Illuminate\Auth\Middleware\EnsureEmailIsVerified` |

Gỡ middleware khỏi một route trong group bằng `withoutMiddleware()`:

```php
use App\Http\Middleware\EnsureTokenIsValid;

Route::middleware([EnsureTokenIsValid::class])->group(function () {
    Route::get('/', function () { /* có EnsureTokenIsValid */ });

    Route::get('/profile', function () { /* không có */ })
        ->withoutMiddleware([EnsureTokenIsValid::class]);
});
```

⚠️ `withoutMiddleware()` chỉ gỡ được middleware route (gồm cả middleware trong group), **không** gỡ được
global middleware.

### 6.6 Thứ tự chạy và danh sách ưu tiên

Toàn cảnh một request trong Laravel 13 (rút gọn từ `Foundation\Http\Kernel` và `Routing\Router`):

```
public/index.php
  └─ Kernel::handle()
       └─ Pipeline #1: GLOBAL middleware (TrustProxies, HandleCors, ..., TrimStrings, ...)
            └─ Router::dispatch()
                 ├─ tìm route khớp (không khớp → 404/405, vẫn bên trong global middleware)
                 └─ Pipeline #2: ROUTE middleware
                       = middleware của group (web/api) + của route/group trong file route
                         + của controller, bỏ những cái trong withoutMiddleware,
                         bỏ trùng, rồi SẮP LẠI theo danh sách ưu tiên
                       └─ controller / closure
  └─ gửi response
  └─ Kernel::terminate() → gọi terminate() của các middleware có method đó (mục 6.7)
```

Thứ tự mặc định là thứ tự đăng ký. Nhưng có những cặp middleware mà thứ tự sai sẽ hỏng: `StartSession`
phải chạy trước những gì đọc session; `SubstituteBindings` phải chạy trước `Authorize` (`can`) để
policy nhận model thật. Vì người dùng có thể gắn middleware theo thứ tự tuỳ ý, Laravel có một
*danh sách ưu tiên* (*middleware priority*): với những middleware nằm trong danh sách, router sắp lại
cho đúng thứ tự trong danh sách; middleware ngoài danh sách không bị dời (chỉ middleware trong danh
sách được chuyển chỗ, nên có thể nhảy qua chúng). Danh sách mặc định
trong `Illuminate\Foundation\Http\Kernel` của 13.x:

```
HandlePrecognitiveRequests
EncryptCookies
AddQueuedCookiesToResponse
StartSession
ShareErrorsFromSession
AuthenticatesRequests      (interface, khớp middleware auth)
ThrottleRequests
ThrottleRequestsWithRedis
AuthenticatesSessions
SubstituteBindings
Authorize                  (alias can)
```

Ví dụ: route khai báo `->middleware(['can:view,order', 'auth'])`, viết `can` trước `auth`. Nhờ danh
sách ưu tiên, khi chạy `auth` vẫn đứng trước `SubstituteBindings` và `can` đứng sau cùng. Lưu ý việc
sắp xếp này chỉ áp dụng cho route middleware (pipeline #2), global middleware chạy đúng thứ tự khai báo.

Hiếm khi cần, nhưng có thể chỉnh danh sách bằng `$middleware->priority([...])` (thay toàn bộ), hoặc
`prependToPriorityList(before: ..., prepend: ...)` và `appendToPriorityList(after: ..., append: ...)`
để chèn thêm.

### 6.7 Terminable middleware

Đôi khi muốn làm việc **sau khi** response đã gửi cho người dùng, để họ không phải chờ: ghi log chi
tiết, gửi số liệu đo đạc. Middleware có thêm method `terminate()` làm được việc đó:

```php
<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class TerminatingMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        return $next($request);
    }

    public function terminate(Request $request, Response $response): void
    {
        // chạy sau khi response đã gửi tới trình duyệt
    }
}
```

Cơ chế: `public/index.php` gọi `$app->handleRequest()`; hàm này lần lượt `handle()` request, `send()`
response, rồi gọi `Kernel::terminate()`. `terminate()` duyệt global
middleware và route middleware của request, middleware nào có `terminate()` thì gọi. Tài liệu Laravel
nói rõ `terminate` được gọi sau khi response đã tới trình duyệt khi web server dùng FastCGI (tức
PHP-FPM): PHP-FPM có hàm `fastcgi_finish_request()` để trả response cho client rồi tiếp tục chạy script
(xem [Chương 18](18-fpm-nginx-opcache.md)).

⚠️ Hai cạm bẫy:

- Laravel tạo **instance mới** của middleware từ container để gọi `terminate()`. Thuộc tính bạn gán
  trong `handle()` (ví dụ thời điểm bắt đầu) sẽ không còn. Muốn dùng chung một instance, đăng ký
  middleware là singleton: `$this->app->singleton(TerminatingMiddleware::class);` trong `register()`
  của `AppServiceProvider`.
- Người dùng không phải chờ, nhưng worker PHP-FPM vẫn bận cho tới khi `terminate()` xong. Việc nặng
  (gửi email, gọi API chậm) nên đẩy vào queue (Chương 29) chứ không phải `terminate()`.

## 7. Middleware có sẵn quan trọng

Mục này đi vào ba middleware bạn sẽ gặp hằng ngày. Lý thuyết tấn công CSRF ở
[Chương 17](17-bao-mat.md), cơ chế đăng nhập và guard ở [Chương 28](28-laravel-auth.md); ở đây tập
trung vào việc middleware làm gì với request.

### 7.1 `PreventRequestForgery`: chống CSRF

Nhắc lại ngắn: *CSRF* (*Cross-Site Request Forgery*) là khi một trang độc hại khiến trình duyệt của
nạn nhân gửi request tới ứng dụng của bạn. Trình duyệt tự đính kèm cookie session, nên request trông
như do chính người dùng gửi. Ví dụ trang độc hại tự submit một form `POST` tới
`https://your-app.com/user/email` để đổi email của nạn nhân.

Laravel 13 chống việc này bằng middleware `Illuminate\Foundation\Http\Middleware\PreventRequestForgery`,
có sẵn trong group `web`. (Đây là tên mới ở Laravel 13; Laravel 12 trở về trước gọi là
`VerifyCsrfToken`/`ValidateCsrfToken`. Hai tên cũ vẫn còn như alias deprecated, theo hướng dẫn nâng
cấp 13.x.)

Theo mã nguồn 13.x, method `handle()` cho request đi tiếp nếu **một** trong các điều kiện sau đúng, và
kiểm tra theo đúng thứ tự này:

```
1. Method là GET, HEAD hoặc OPTIONS          → "đọc", không kiểm tra
2. Đang chạy unit test                        → bỏ qua
3. URI nằm trong danh sách except             → bỏ qua
4. Header Sec-Fetch-Site = 'same-origin'      → hợp lệ (lớp 1: kiểm tra nguồn gốc)
   (hoặc 'same-site' nếu bật allowSameSite)
5. Token gửi lên khớp token trong session     → hợp lệ (lớp 2: token)
   (lấy từ field _token, hoặc header X-CSRF-TOKEN,
    hoặc header X-XSRF-TOKEN đã giải mã; so sánh bằng hash_equals)

Không điều kiện nào đúng → ném TokenMismatchException → response 419
```

- Lớp 1, `Sec-Fetch-Site`: trình duyệt hiện đại tự gắn header này, cho biết request xuất phát từ cùng
  origin, cùng site hay site khác, và JavaScript của trang độc hại không giả được nó. Tài liệu Laravel
  lưu ý trình duyệt chỉ gửi header này qua HTTPS; chạy HTTP thì lớp 1 không có tác dụng và middleware
  dựa vào lớp 2.
- Lớp 2, token: Laravel sinh một token ngẫu nhiên cho mỗi session. Trang độc hại ở domain khác không
  đọc được token này nên không đính kèm được. Trong form Blade, `@csrf` sinh field ẩn `_token`:

```blade
<form method="POST" action="/profile">
    @csrf
    {{-- tương đương: <input type="hidden" name="_token" value="{{ csrf_token() }}" /> --}}
</form>
```

- AJAX: đặt token vào thẻ `<meta name="csrf-token" content="{{ csrf_token() }}">` rồi gửi qua header
  `X-CSRF-TOKEN`. Ngoài ra Laravel gửi kèm cookie `XSRF-TOKEN` (đã mã hoá) trong response; các thư viện
  như Axios tự đọc cookie này và gửi lại qua header `X-XSRF-TOKEN`.

Cấu hình trong `bootstrap/app.php`:

```php
->withMiddleware(function (Middleware $middleware): void {
    // Loại trừ URI khỏi kiểm tra, ví dụ webhook của Stripe (Stripe không có token của bạn)
    $middleware->preventRequestForgery(except: [
        'stripe/*',
    ]);

    // Chấp nhận request từ subdomain cùng site
    // $middleware->preventRequestForgery(allowSameSite: true);

    // Chỉ dùng lớp 1, bỏ hẳn token; request không đạt nhận 403 thay vì 419
    // $middleware->preventRequestForgery(originOnly: true);
})
```

Với webhook, tài liệu khuyên cách tốt hơn `except` là đặt route **ngoài** group `web` (ví dụ file route
riêng với group `api` như mục 1.3), vì webhook không cần session lẫn cookie.

⚠️ Cạm bẫy:

- Route `GET` thay đổi dữ liệu không được bảo vệ, vì bước 1 bỏ qua mọi `GET` (nhắc lại mục 1.4).
- Lỗi 419 "Page Expired" khi submit form thường do: quên `@csrf`; session hết hạn (người dùng để tab
  mở lâu); session không lưu được (driver session lỗi, cookie bị chặn).
- Đừng dùng `except` với wildcard rộng như `'*'` để "chữa" lỗi 419: đó là tắt hẳn bảo vệ.
- Route trong `routes/api.php` không có middleware này (group `api` không có session). API xác thực
  bằng token trong header thì không bị CSRF theo cách trên; SPA dùng cookie thì xem Sanctum ở Chương 28.

### 7.2 `auth`: bắt buộc đăng nhập

Alias `auth` trỏ tới `Illuminate\Auth\Middleware\Authenticate`. Theo mã nguồn 13.x:

```php
Route::get('/dashboard', DashboardController::class)->middleware('auth');           // guard mặc định
Route::get('/api/user', fn (Request $r) => $r->user())->middleware('auth:sanctum');  // guard sanctum
```

- Tham số là tên *guard* (cách xác định người dùng: session, token...). Không truyền thì dùng guard mặc
  định. Truyền nhiều guard (`auth:web,sanctum`) thì guard đầu tiên xác thực được sẽ được dùng cho phần
  còn lại của request.
- Không guard nào xác thực được: middleware ném `AuthenticationException`. Exception handler đổi thành:
  JSON `{"message": "Unauthenticated."}` với status 401 nếu request muốn JSON (ví dụ có header
  `Accept: application/json`); ngược lại chuyển hướng tới trang đăng nhập. Mặc định của Laravel 13 là
  `route('login')`, đổi được bằng `$middleware->redirectGuestsTo('/dang-nhap')` trong `bootstrap/app.php`.
- Chuyển hướng dùng `redirect()->guest(...)`, nghĩa là URL đang định vào được nhớ trong session để sau
  khi đăng nhập quay lại đúng chỗ.

Alias ngược lại là `guest` (`RedirectIfAuthenticated`): dành cho trang đăng nhập, đăng ký; người đã
đăng nhập vào đó sẽ bị chuyển đi.

⚠️ Ứng dụng không có route tên `login` (ví dụ API thuần) mà request không gửi `Accept: application/json`
thì việc sinh URL `route('login')` sẽ ném `RouteNotFoundException` ("Route [login] not defined."),
người dùng nhận 500 thay vì 401. Client API nên luôn gửi
`Accept: application/json`.

### 7.3 `throttle`: giới hạn tần suất (giới thiệu)

Alias `throttle` trỏ tới `Illuminate\Routing\Middleware\ThrottleRequests`. Có hai cách dùng:

```php
// Cách 1: số cụ thể. throttle:{số request tối đa},{số phút của cửa sổ}
Route::post('/comments', [CommentController::class, 'store'])->middleware('throttle:60,1');

// Cách 2: tên của một rate limiter đã định nghĩa bằng RateLimiter::for() (mục 8)
Route::post('/login', [LoginController::class, 'store'])->middleware('throttle:login');
```

Vượt giới hạn thì Laravel trả 429 Too Many Requests. Mục 8 giải thích chi tiết, gồm cả cạm bẫy của
cách 1.

## 8. Rate limiting

### 8.1 Vì sao cần giới hạn tần suất

*Rate limiting* là giới hạn số lần một "chủ thể" (một user, một IP, một email...) được làm một việc
trong một khoảng thời gian. Lý do:

- Chống dò mật khẩu (*brute force*): không giới hạn thì kẻ tấn công thử hàng nghìn mật khẩu mỗi phút.
- Chống dò dữ liệu (*enumeration*): thử `/orders/1`, `/orders/2`... để tìm bản ghi tồn tại.
- Bảo vệ tài nguyên: một client lỗi gọi API liên tục có thể làm nghẽn cả hệ thống.
- Kiểm soát chi phí: gửi SMS, email, gọi API trả phí.

### 8.2 Định nghĩa rate limiter có tên

Định nghĩa trong `boot()` của `AppServiceProvider`. `RateLimiter::for()` nhận tên limiter và một
closure; closure nhận request và trả về một (hoặc nhiều) object `Illuminate\Cache\RateLimiting\Limit`:

```php
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;

public function boot(): void
{
    // 60 request/phút cho mỗi user; khách chưa đăng nhập thì tính theo IP
    RateLimiter::for('api', function (Request $request) {
        return Limit::perMinute(60)->by($request->user()?->id ?: $request->ip());
    });

    // Đăng nhập: tối đa 5 lần/phút cho mỗi cặp email + IP, và 500 lần/phút toàn hệ thống
    RateLimiter::for('login', function (Request $request) {
        return [
            Limit::perMinute(500),
            Limit::perMinute(5)->by($request->input('email').'|'.$request->ip()),
        ];
    });

    // Khách VIP không giới hạn, còn lại 10 lần/giờ
    RateLimiter::for('uploads', function (Request $request) {
        return $request->user()?->vipCustomer()
            ? Limit::none()
            : Limit::perHour(10)->by($request->user()?->id ?: $request->ip());
    });
}
```

Gắn vào route bằng `throttle:<tên>`:

```php
Route::middleware(['throttle:uploads'])->group(function () {
    Route::post('/audio', fn () => '...');
    Route::post('/video', fn () => '...');
});
```

Bật cho cả group `api` trong `bootstrap/app.php` (thêm `throttle:api` vào group, cần đã định nghĩa
limiter `api` như trên):

```php
->withMiddleware(function (Middleware $middleware): void {
    $middleware->throttleApi();
})
```

Các builder của `Limit` hay dùng: `perSecond()`, `perMinute()`, `perHour()`, `perDay()`, `none()`; nối
thêm `by($key)` để chia bộ đếm theo khoá, `response(fn (Request $r, array $headers) => ...)` để tự
định nghĩa response khi vượt giới hạn, `after(fn (Response $r) => bool)` để chỉ đếm những response thoả
điều kiện.

Ví dụ `after()` chống dò bản ghi: chỉ các response 404 bị đếm, request hợp lệ không tốn lượt:

```php
use Symfony\Component\HttpFoundation\Response;

RateLimiter::for('resource-not-found', function (Request $request) {
    return Limit::perMinute(10)
        ->by($request->user()?->id ?: $request->ip())
        ->after(function (Response $response) {
            return $response->getStatusCode() === 404;
        });
});
```

⚠️ Khi trả về nhiều `Limit` có cùng giá trị `by`, tài liệu Laravel yêu cầu thêm tiền tố để chúng không
dùng chung bộ đếm: `by('minute:'.$id)` và `by('day:'.$id)`. Lý do: khoá trong cache được ghép từ tên
limiter và giá trị `by`, bản thân nó không chứa độ dài cửa sổ. (Mã nguồn 13.x có thêm một lưới an toàn:
`RateLimiter::limiter()` phát hiện các `Limit` trùng khoá trong cùng một mảng và tự đổi khoá của chúng
sang dạng có kèm số lượt và `decay`. Dù vậy hãy làm theo tài liệu và tự thêm tiền tố, để khoá rõ ràng
và không phụ thuộc vào chi tiết cài đặt.)

### 8.3 Middleware `throttle` làm gì với mỗi request

Theo `ThrottleRequests::handleRequest()` trong 13.x:

```
1. Với từng Limit: nếu bộ đếm của khoá đã >= max và cửa sổ chưa hết
      → ném ThrottleRequestsException → response 429, kèm header
        Retry-After (số giây phải chờ), X-RateLimit-Reset, X-RateLimit-Limit, X-RateLimit-Remaining
2. Với từng Limit không có after(): tăng bộ đếm (hit)
3. Gọi $next($request) → controller chạy
4. Với từng Limit có after(): nếu callback trả true thì mới tăng bộ đếm
5. Thêm header X-RateLimit-Limit và X-RateLimit-Remaining vào response
```

Để ý bước 2 diễn ra **trước** khi controller chạy: request bị validation từ chối hay controller ném
lỗi vẫn tốn một lượt, trừ khi bạn dùng `after()`.

Khoá dùng để đếm được tạo như sau:

| Cách gắn | Khoá đếm |
|---|---|
| `throttle:60,1` | Theo user đang đăng nhập (id); chưa đăng nhập thì theo domain + IP. **Không** có tên route trong khoá |
| `throttle:ten_limiter` | Tên limiter + giá trị `by()`. Không gọi `by()` thì giá trị là chuỗi rỗng |

Từ bảng này ra hai cạm bẫy hay gặp:

- ⚠️ Gắn `throttle:60,1` lên hai route khác nhau thì hai route **dùng chung** một bộ đếm cho cùng một
  user/IP. Muốn đếm riêng, dùng limiter có tên khác nhau, hoặc tham số thứ ba (prefix) của `throttle`.
- ⚠️ Limiter có tên mà quên `->by(...)` thì **mọi người dùng chung một bộ đếm**: 60 request/phút cho cả
  hệ thống chứ không phải cho mỗi người. Đó là hành vi đúng cho limiter "global" (như `Limit::perMinute(500)`
  trong ví dụ `login`), nhưng là bug nếu bạn định giới hạn từng người.

### 8.4 Bên dưới: bộ đếm trong cache, cửa sổ cố định

`ThrottleRequests` dùng `Illuminate\Cache\RateLimiter`, lưu trạng thái trong **cache** của ứng dụng
(mặc định là cache store mặc định; đổi được bằng khoá `limiter` trong `config/cache.php`). Với mỗi khoá,
nó giữ hai mục trong cache:

- `khoá`: bộ đếm số lần;
- `khoá:timer`: thời điểm cửa sổ hết hạn, chỉ được tạo ở lần đếm **đầu tiên** (dùng `Cache::add`, chỉ
  ghi khi chưa tồn tại), sống đúng `decay` giây.

Đây là thuật toán *fixed window* (cửa sổ cố định): cửa sổ bắt đầu từ lần đếm đầu tiên và kéo dài
`decay` giây, hết cửa sổ thì bộ đếm về 0. Mô phỏng bằng PHP thuần với đồng hồ giả (chạy được, không cần
Laravel):

```php
<?php
declare(strict_types=1);

// Mô phỏng thuật toán của Illuminate\Cache\RateLimiter bằng PHP thuần:
// mỗi key có một bộ đếm và một "timer" sống $decay giây kể từ lần hit ĐẦU TIÊN.

final class FakeCache
{
    /** @var array<string, array{value: int, expires: int}> */
    private array $items = [];
    public int $now = 0;                                  // đồng hồ giả, đơn vị giây

    public function has(string $key): bool
    {
        return isset($this->items[$key]) && $this->items[$key]['expires'] > $this->now;
    }
    public function get(string $key): ?int
    {
        return $this->has($key) ? $this->items[$key]['value'] : null;
    }
    /** Chỉ ghi nếu key CHƯA tồn tại (giống Cache::add) */
    public function add(string $key, int $value, int $ttl): bool
    {
        if ($this->has($key)) {
            return false;
        }
        $this->items[$key] = ['value' => $value, 'expires' => $this->now + $ttl];
        return true;
    }
    public function increment(string $key): int
    {
        return ++$this->items[$key]['value'];
    }
    public function forget(string $key): void
    {
        unset($this->items[$key]);
    }
}

final class MiniRateLimiter
{
    public function __construct(private FakeCache $cache) {}

    public function tooManyAttempts(string $key, int $max): bool
    {
        if ((int) $this->cache->get($key) >= $max) {
            if ($this->cache->has($key . ':timer')) {
                return true;                                  // hết lượt, cửa sổ chưa hết hạn
            }
            $this->cache->forget($key);                       // cửa sổ đã hết: xoá bộ đếm cũ
        }
        return false;
    }

    public function hit(string $key, int $decay): int
    {
        $this->cache->add($key . ':timer', $this->cache->now + $decay, $decay);
        $this->cache->add($key, 0, $decay);
        return $this->cache->increment($key);
    }

    public function availableIn(string $key): int
    {
        return max(0, (int) $this->cache->get($key . ':timer') - $this->cache->now);
    }
}

$cache = new FakeCache();
$limiter = new MiniRateLimiter($cache);
$key = 'login:1.2.3.4';

foreach ([0, 10, 20, 30, 59, 60, 61] as $t) {
    $cache->now = $t;
    if ($limiter->tooManyAttempts($key, 3)) {
        echo "t={$t}s: 429, thử lại sau {$limiter->availableIn($key)}s\n";
        continue;
    }
    echo "t={$t}s: cho qua, lần thứ {$limiter->hit($key, 60)} trong cửa sổ\n";
}
```

Output (đã chạy thật):

```
t=0s: cho qua, lần thứ 1 trong cửa sổ
t=10s: cho qua, lần thứ 2 trong cửa sổ
t=20s: cho qua, lần thứ 3 trong cửa sổ
t=30s: 429, thử lại sau 30s
t=59s: 429, thử lại sau 1s
t=60s: cho qua, lần thứ 1 trong cửa sổ
t=61s: cho qua, lần thứ 2 trong cửa sổ
```

Hệ quả của fixed window: giới hạn "3 lần/60 giây" không có nghĩa là "không bao giờ quá 3 lần trong bất
kỳ 60 giây liên tiếp nào". Nếu request đầu tiên mở cửa sổ ở t=0, client gửi thêm 2 request ở t=58
(vẫn còn lượt) rồi 3 request ở t=60, 61, 62 (cửa sổ mới), thì trong khoảng 5 giây (t=58 tới 62) có 5
request lọt qua, gần gấp đôi giới hạn (chạy lại mô phỏng trên với các mốc này để tự kiểm tra). Với chống
brute force mức này thường chấp nhận được; cần chặt hơn thì phải tự cài thuật toán khác (sliding
window, token bucket), Laravel không có sẵn.

Những điều phải nhớ khi chạy production:

- ⚠️ Bộ đếm nằm trong cache. Nhiều server web mà mỗi server dùng cache riêng (driver `file`, `array`)
  thì mỗi server đếm riêng, giới hạn thực tế nhân lên theo số server. Dùng cache dùng chung: Redis,
  Memcached, hoặc `database`. Laravel còn có `$middleware->throttleWithRedis()` để đổi `throttle` sang
  `ThrottleRequestsWithRedis`: bộ đếm được kiểm tra và tăng bằng một Lua script chạy trên Redis
  (`Illuminate\Redis\Limiters\DurationLimiter`), nhưng thuật toán vẫn là cửa sổ cố định.
- ⚠️ Đếm theo IP sau load balancer: nếu chưa cấu hình `TrustProxies`, `$request->ip()` trả IP của load
  balancer, mọi người dùng chung một bộ đếm và cả hệ thống bị 429 cùng lúc. Cấu hình bằng
  `$middleware->trustProxies(at: [...])` với địa chỉ proxy của bạn. Ngược lại, tin mọi proxy
  (`at: '*'`) khi server nhận request trực tiếp từ Internet thì kẻ tấn công tự điền `X-Forwarded-For`
  để đổi IP tuỳ ý và né giới hạn.

### 8.5 Dùng `RateLimiter` trực tiếp, ngoài middleware

Không phải mọi thứ cần giới hạn đều là một route: gửi tin nhắn, gửi OTP, thử mã giảm giá. Facade
`RateLimiter` dùng trực tiếp được trong code:

```php
use Illuminate\Support\Facades\RateLimiter;

$executed = RateLimiter::attempt(
    'send-message:'.$user->id,
    $perMinute = 5,
    function () {
        // gửi tin nhắn...
    },
    // tham số thứ tư tuỳ chọn: decay (giây), mặc định 60
);

if (! $executed) {
    return 'Too many messages sent!';
}
```

`attempt()` trả `false` khi hết lượt; ngược lại chạy callback và trả kết quả của callback (hoặc `true`
nếu callback không trả gì). Các method khác:

| Method | Việc |
|---|---|
| `tooManyAttempts($key, $max)` | Đã hết lượt chưa |
| `increment($key, amount: 1)` / `hit($key, $decay)` | Tăng bộ đếm, trả về số đếm mới |
| `remaining($key, $max)` | Còn bao nhiêu lượt |
| `availableIn($key)` | Còn bao nhiêu giây thì có lượt lại |
| `clear($key)` | Xoá bộ đếm và timer (ví dụ sau khi đăng nhập thành công) |

⚠️ Race condition: `tooManyAttempts()` rồi mới `increment()` là hai bước tách rời; hai request đồng thời
có thể cùng thấy "còn lượt" rồi cùng đi tiếp. Tài liệu Laravel khuyên với endpoint có nhiều request đồng
thời, hãy dựa vào giá trị trả về của `increment()`, vì với cache store `redis`, `memcached`,
`database` phép tăng là nguyên tử (*atomic*), mỗi request nhận một số đếm khác nhau:

```php
if (RateLimiter::increment('send-message:'.$user->id) > 5) {
    return 'Too many attempts!';
}
// gửi tin nhắn...
```

| Bước | Request A | Request B | Kết quả với tooManyAttempts + increment |
|---|---|---|---|
| 1 | `tooManyAttempts()` thấy đếm = 4 < 5 | | A được đi tiếp |
| 2 | | `tooManyAttempts()` thấy đếm = 4 < 5 | B cũng được đi tiếp |
| 3 | `increment()` → 5 | | |
| 4 | | `increment()` → 6 | Lần thứ 6 đã lọt qua |

Dùng `increment()` làm điều kiện: A nhận 5 (đi tiếp), B nhận 6 (bị chặn), vì phép tăng nguyên tử
không cho hai request cùng nhận một giá trị.

## 9. Route cache

### 9.1 Vấn đề: đăng ký route ở mỗi request

PHP-FPM không giữ trạng thái giữa các request ([Chương 02](02-php-chay-nhu-the-nao.md)): mỗi request,
Laravel chạy lại `routes/web.php`, `routes/api.php`..., tạo lại hàng trăm object `Route`, gom group,
ghép prefix. Ứng dụng có vài trăm route thì việc này tốn thời gian đáng kể ở **mọi** request, trong khi
danh sách route không đổi giữa hai lần deploy.

### 9.2 `route:cache` và `route:clear`

Chạy ở thư mục gốc dự án, thường là một bước trong script deploy:

```shell
php artisan route:cache    # tạo file cache
php artisan route:clear    # xoá file cache
php artisan optimize       # gồm config:cache, event:cache, route:cache, view:cache
```

Theo mã nguồn 13.x, `route:cache` làm: xoá cache cũ, khởi động một bản ứng dụng mới để thu toàn bộ
route, chuẩn bị từng route để *serialize*, rồi ghi tất cả ra một file PHP: mặc định
`bootstrap/cache/routes-v7.php` (đổi được bằng biến môi trường `APP_ROUTES_CACHE`). Từ đó mỗi request,
nếu file này tồn tại, Laravel nạp nó thay vì chạy các file trong `routes/`. Route ở dạng đã biên dịch
sẵn nên không phải dựng lại.

Route dùng closure vẫn cache được: Laravel serialize closure bằng package `laravel/serializable-closure`.

### 9.3 Cạm bẫy khi dùng route cache

- ⚠️ Thêm hoặc sửa route mà quên chạy lại `route:cache` thì route mới không tồn tại (404), route cũ
  vẫn chạy như trước. Vì vậy tài liệu Laravel khuyên chỉ chạy `route:cache` lúc deploy, không chạy
  trên máy dev. Gặp "sửa route mà không ăn" ở local, thử `php artisan route:clear`.
- ⚠️ Khi có cache, các file trong `routes/` **không** được chạy. Code nào đặt trong file route mà
  không phải khai báo route (gọi `Route::bind`, `RateLimiter::for`, đăng ký gì đó...) sẽ biến mất trên
  production. Những thứ đó thuộc về `AppServiceProvider::boot()`, nơi luôn chạy.
- ⚠️ Hai route trùng tên: không có cache thì chỉ sinh link sai âm thầm (mục 3.1), có cache thì
  `route:cache` dừng với `LogicException`. Đây thật ra là điều tốt: lỗi lộ ra ở bước deploy. Chạy
  `route:cache` trong CI để bắt sớm.
- File cache là trạng thái của từng server. Deploy lên nhiều server thì mỗi server phải tự chạy
  `route:cache` (hoặc file được đóng gói sẵn trong artifact/image).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Route `GET` làm thay đổi dữ liệu (`GET /posts/1/delete`) | CSRF bỏ qua `GET`; crawler, prefetch, thẻ `<img>` đều gọi được | Thay đổi dữ liệu dùng `POST`/`PUT`/`PATCH`/`DELETE` (mục 1.4, 7.1) |
| Thêm route `/photos/popular` sau `Route::resource('photos', ...)` | `{photo}` khớp `popular` trước, binding không tìm thấy → 404 | Khai báo route bổ sung trước resource (mục 5.5) |
| Đổi chỗ tham số trong chữ ký hàm | Tham số route thường được truyền theo thứ tự, không theo tên | Giữ đúng thứ tự như URI; dependency đứng trước (mục 2.1) |
| Khai báo `int $id` không kèm ràng buộc | `"abc"` gây `TypeError` → 500 thay vì 404 | `string $id`, hoặc `int` + `whereNumber()` (mục 2.1) |
| Tên biến không trùng tên segment (`{id}` với `User $user`) | Implicit binding không áp dụng, container tạo `User` rỗng | Đặt tên trùng nhau (mục 4.2) |
| Tin rằng `auth` hoặc scoped binding đủ để bảo vệ bản ghi | Binding chỉ kiểm tra tồn tại, không kiểm tra quyền (IDOR) | Thêm `can:...`/policy (mục 4.8) |
| `name('admin')` thay vì `name('admin.')` | Tiền tố tên được nối nguyên văn | Nhớ dấu chấm cuối (mục 3.2) |
| Quên `return $next($request)` trong middleware | `handle()` trả `null` → `TypeError` | Khai báo kiểu trả về `Response` (mục 6.3) |
| Lưu trạng thái trong thuộc tính middleware để dùng ở `terminate()` | `terminate()` chạy trên instance mới | Đăng ký middleware singleton (mục 6.7) |
| Nghĩ group `api` đã có rate limit | Group `api` mặc định chỉ có `SubstituteBindings` | `throttleApi()` hoặc `throttle:...` (mục 6.5, 8.2) |
| Limiter có tên nhưng quên `by()` | Mọi người dùng chung một bộ đếm | Luôn `by(user id hoặc IP)` khi giới hạn từng người (mục 8.3) |
| Đếm theo IP sau load balancer mà chưa cấu hình `TrustProxies` | `$request->ip()` là IP của load balancer | `trustProxies(at: ...)` đúng địa chỉ proxy (mục 8.4) |
| Rate limit với cache `file` trên nhiều server | Mỗi server đếm riêng | Dùng Redis/Memcached/database (mục 8.4) |
| Sửa route trên production mà route mới 404 | Route cache cũ vẫn được dùng | Chạy lại `route:cache` mỗi lần deploy (mục 9.3) |
| Đặt `Route::bind`, `RateLimiter::for` trong file route | Có route cache thì file route không chạy | Đặt trong `AppServiceProvider::boot()` (mục 9.3) |

## Tóm tắt chương

- Router ghép method + URI với danh sách route theo thứ tự khai báo; route đầu tiên khớp thắng. URI
  khớp mà method không khớp là 405, không khớp gì là 404. `Route::get()` nhận cả `HEAD`.
- Tham số route luôn là chuỗi, khớp mọi ký tự trừ `/`; `where()`/`whereNumber()`... thu hẹp giá trị
  hợp lệ. Tham số thường được truyền theo thứ tự.
- Named route để sinh URL bằng `route()`, tên phải duy nhất. Group gom middleware, prefix, tên,
  controller; khi lồng nhau middleware được gộp, prefix và tên được nối.
- Route model binding do middleware `SubstituteBindings` thực hiện: explicit binding trước, implicit
  sau; không tìm thấy là 404 (hoặc `missing()`). Cột tìm đổi bằng `{post:slug}`, `#[RouteKey]` hoặc
  `getRouteKeyName()`. Scoped binding buộc con thuộc cha. Binding không thay cho kiểm tra quyền.
- Controller gom handler; single action dùng `__invoke`; `Route::resource` sinh bảy route CRUD,
  `apiResource` sinh năm.
- Middleware là các lớp bọc quanh controller, nối bằng pipeline (`array_reduce` trên danh sách đảo
  ngược). Ba cấp: global, group, route. Route middleware được sắp lại theo danh sách ưu tiên.
  `terminate()` chạy sau khi gửi response, trên instance mới.
- `PreventRequestForgery` (tên mới ở Laravel 13) kiểm tra `Sec-Fetch-Site` rồi tới token; thất bại
  là 419. `auth` ném `AuthenticationException` → 401 JSON hoặc chuyển hướng `login`.
- `throttle` dùng `RateLimiter` lưu bộ đếm trong cache, thuật toán cửa sổ cố định, trả 429 kèm
  `Retry-After`. Khoá đếm quyết định ai chung bộ đếm với ai.
- `route:cache` ghi toàn bộ route ra `bootstrap/cache/routes-v7.php`; chạy lúc deploy, chạy lại mỗi
  lần route đổi.

## Câu hỏi tự kiểm tra

1. Request `DELETE /users/42` tới ứng dụng chỉ có `GET /users/{id}` và `PUT /users/{id}`. Laravel trả
   status gì, vì sao không phải 404? (mục 1.2, 1.4)
2. Vì sao một route `GET` thay đổi dữ liệu là lỗ hổng, dù ứng dụng đã bật chống CSRF? (mục 1.4, 7.1)
3. Với `Route::get('/posts/{post}/comments/{comment}', fn (string $a, string $b) => ...)`, `$a` nhận
   giá trị nào? Nếu thay bằng `fn (Post $post, Comment $comment)` thì cơ chế truyền khác thế nào?
   (mục 2.1, 4.2)
4. `/users/{user}/posts/{post}` có tự kiểm tra post thuộc user không? Liệt kê hai cách bật kiểm tra
   đó, và giải thích vì sao bật rồi vẫn có thể bị IDOR. (mục 4.5, 4.8)
5. Middleware `can:view,order` cần nhận object `Order`. Điều gì đảm bảo nó chạy sau
   `SubstituteBindings`, kể cả khi bạn khai báo `can` trước? (mục 4.7, 6.6)
6. Trong pipeline, nếu middleware thứ hai trả response mà không gọi `$next`, những phần code nào còn
   chạy và những phần nào không? (mục 6.2)
7. Hai route cùng gắn `throttle:60,1`. Một user gọi route A 40 lần, rồi gọi route B. Còn bao nhiêu
   lượt cho route B, vì sao? (mục 8.3)
8. Giới hạn "5 lần/phút" của `throttle` có đảm bảo không bao giờ có hơn 5 request trong 60 giây liên
   tiếp không? (mục 8.4)
9. Vì sao `tooManyAttempts()` rồi `increment()` có thể để lọt request khi tải cao, và cách sửa? (mục 8.5)
10. Sau khi deploy có `route:cache`, explicit binding khai báo trong `routes/web.php` ngừng hoạt động.
    Giải thích. (mục 9.3)

## Bài tập

1. Mở rộng router tối giản ở mục 1.2: thêm tham số tuỳ chọn (`{name?}`), route có tên và hàm
   `url(string $name, array $params): string` sinh URL từ tên (tham số thừa thành query string như
   `route()` của Laravel). Viết vài lời gọi kiểm tra và ghi output mong đợi.
2. Mở rộng pipeline ở mục 6.2: cho middleware nhận tham số dạng chuỗi `'role:admin,editor'` (tách tên
   và tham số giống Laravel), thêm một middleware ném exception và một "exception handler" trong
   pipeline đổi exception thành response 500, sao cho phần "SAU" của `LogMiddleware` vẫn chạy.
3. Trong một dự án Laravel 13: tạo resource `orders` với scoped binding dưới `users`, gắn `auth` và
   một policy để chỉ chủ đơn xem được đơn. Dùng `php artisan route:list -v` để chứng minh mọi route đều
   có middleware đúng, và dùng `curl` thử đổi id để thấy 403/404.
4. Định nghĩa limiter `login` gồm hai giới hạn (theo email + IP và toàn hệ thống), chỉ đếm các lần đăng
   nhập thất bại bằng `after()`. Dùng `curl -i` gửi liên tục và ghi lại các header `X-RateLimit-*`,
   `Retry-After` bạn thấy.

## Đọc thêm

- Laravel 13.x, Routing: https://laravel.com/docs/13.x/routing
- Laravel 13.x, Controllers: https://laravel.com/docs/13.x/controllers
- Laravel 13.x, Middleware: https://laravel.com/docs/13.x/middleware
- Laravel 13.x, CSRF Protection: https://laravel.com/docs/13.x/csrf
- Laravel 13.x, Rate Limiting: https://laravel.com/docs/13.x/rate-limiting
- Laravel 13.x, Upgrade Guide (đổi tên `VerifyCsrfToken` thành `PreventRequestForgery`, ưu tiên domain
  route): https://laravel.com/docs/13.x/upgrade
- Mã nguồn laravel/framework nhánh 13.x, các file đã đọc khi viết chương:
  `src/Illuminate/Routing/{Router,Route,RouteCollection,AbstractRouteCollection,ImplicitRouteBinding,SortedMiddleware,Pipeline}.php`,
  `src/Illuminate/Routing/Middleware/{ThrottleRequests,SubstituteBindings}.php`,
  `src/Illuminate/Cache/RateLimiter.php`, `src/Illuminate/Foundation/Http/Kernel.php`,
  `src/Illuminate/Foundation/Http/Middleware/PreventRequestForgery.php`,
  `src/Illuminate/Foundation/Configuration/Middleware.php`, `src/Illuminate/Auth/Middleware/Authenticate.php`
  (https://github.com/laravel/framework/tree/13.x)
- OWASP, Cross-Site Request Forgery Prevention Cheat Sheet:
  https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
- MDN, `Sec-Fetch-Site`: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Sec-Fetch-Site
