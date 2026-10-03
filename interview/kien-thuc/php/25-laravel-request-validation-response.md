# Chương 25. Request, validation, response và view

> [← Mục lục](README.md) · [← Chương 24: Routing, controller và middleware](24-laravel-routing-controller-middleware.md) · [Chương 26: Service container, provider, facade và vòng đời request →](26-laravel-container-provider-facade.md)

**Bạn sẽ học được:**

- Đọc mọi thứ client gửi lên qua object `Illuminate\Http\Request`: input từ form, query string, JSON,
  file upload, header, cookie; hiểu input được gộp từ đâu và bị chuẩn hoá ra sao.
- Kiểm tra dữ liệu đầu vào (*validation*) bằng `validate()`, các rule có sẵn, rule tự viết và Form
  Request; hiểu chuyện gì xảy ra khi dữ liệu sai (redirect kèm lỗi hay JSON 422).
- Trả về đủ loại response: JSON, redirect, download, stream, kèm header và cookie; biến model thành
  JSON có kiểm soát bằng API Resource.
- Viết view bằng Blade ở mức cơ bản: layout, component, và vì sao `{{ }}` an toàn còn `{!! !!}` thì
  nguy hiểm.
- Dùng session và flash data trong Laravel; cấu hình cách exception biến thành trang lỗi hoặc JSON
  lỗi trong `bootstrap/app.php`.

**Cần biết trước:** [Chương 15: PHP và HTTP](15-php-va-web.md) (request, response, header, cookie,
session, upload ở mức PHP thuần), [Chương 12: Lỗi và exception](12-loi-exception.md),
[Chương 17: Bảo mật](17-bao-mat.md) (XSS, CSRF), [Chương 23](23-laravel-gioi-thieu.md) và
[Chương 24](24-laravel-routing-controller-middleware.md) (cấu trúc project, route, controller,
middleware).

Cách chạy ví dụ: các đoạn code Laravel trong chương này cần một project Laravel 13 (tạo như ở
[Chương 23](23-laravel-gioi-thieu.md)), đặt route vào `routes/web.php` hoặc `routes/api.php`, chạy
`php artisan serve` rồi gọi thử bằng trình duyệt hoặc `curl`. Vài ví dụ PHP thuần (đánh dấu "PHP
thuần") minh hoạ cơ chế bên dưới, chạy được bằng `php ten-file.php` hoặc Docker:

```bash
# chạy trong thư mục chứa file
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

Các ví dụ PHP thuần đã chạy thử trên PHP 8.5. Hành vi Laravel trong chương đối chiếu với tài liệu
Laravel 13.x và mã nguồn `laravel/framework` nhánh 13.x.

## 1. Request object: cửa sổ nhìn vào HTTP request

### 1.1 Vì sao cần một object Request

Ở [Chương 15](15-php-va-web.md) bạn đã thấy PHP thuần đưa dữ liệu request vào các biến toàn cục
(*superglobal*): `$_GET`, `$_POST`, `$_FILES`, `$_COOKIE`, `$_SERVER`. Cách đó có vài vấn đề:

- Dữ liệu nằm rải rác ở năm, sáu biến khác nhau. Muốn biết header `Accept` phải tra
  `$_SERVER['HTTP_ACCEPT']`.
- Body JSON không tự vào `$_POST`; phải tự đọc `php://input` rồi `json_decode`.
- Biến toàn cục ai cũng sửa được, khó test (muốn giả lập một request phải gán đè `$_GET`...).

Laravel gói tất cả vào một object duy nhất: `Illuminate\Http\Request`. Class này kế thừa
(*extends*) `Symfony\Component\HttpFoundation\Request` của Symfony, rồi thêm rất nhiều method tiện
dụng. Trong `public/index.php` của project Laravel 13 có dòng:

```php
$app->handleRequest(Request::capture());
```

`Request::capture()` dựng object từ các superglobal (qua `SymfonyRequest::createFromGlobals()`), và
từ đó trở đi mọi phần của framework (middleware, controller, validation) làm việc với object này
thay vì đụng thẳng vào `$_GET`, `$_POST`.

```
  $_GET  $_POST  $_FILES  $_COOKIE  $_SERVER  php://input
     \      |       |        |         |         /
      \_____|_______|________|_________|________/
                         |
                Request::capture()
                         |
                         v
         Illuminate\Http\Request  ($request)
          ├─ query    : tham số trên URL (?page=2)
          ├─ request  : body dạng form (POST)
          ├─ json()   : body JSON (decode từ php://input)
          ├─ files    : file upload
          ├─ cookies
          ├─ headers
          └─ server   : biến môi trường của request
```

### 1.2 Lấy object Request ở đâu

Cách chuẩn: khai báo tham số kiểu `Request` trong route closure hoặc method controller. Service
container của Laravel (sẽ học ở [Chương 26](26-laravel-container-provider-facade.md)) nhìn type-hint
và tự truyền đúng object request hiện tại vào. Kỹ thuật này gọi là *dependency injection*.

```php
<?php
declare(strict_types=1);

namespace App\Http\Controllers;

use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

final class UserController extends Controller
{
    // Route::put('/users/{id}', [UserController::class, 'update']);
    public function update(Request $request, string $id): RedirectResponse
    {
        $name = $request->input('name');
        // ... cập nhật user $id
        return redirect('/users');
    }
}
```

Tham số route (`{id}`) được liệt kê sau các tham số được inject. Ngoài ra còn helper `request()`
trả về cùng object đó, dùng được ở bất cứ đâu; nhưng trong controller nên dùng type-hint vì nhìn chữ
ký method là biết nó phụ thuộc vào request.

### 1.3 Đường dẫn, URL, method, host

Giả sử request tới `http://localhost:8000/admin/users?page=2`:

```php
$request->path();          // "admin/users"  (không có dấu / đầu, không có query string)
$request->url();           // "http://localhost:8000/admin/users"
$request->fullUrl();       // "http://localhost:8000/admin/users?page=2"
$request->is('admin/*');   // true, '*' là ký tự đại diện
$request->routeIs('admin.*'); // so với TÊN route (đặt bằng ->name(...)), không phải đường dẫn
$request->method();        // "GET"
$request->isMethod('post');// false

$request->host();              // "localhost"
$request->httpHost();          // "localhost:8000"
$request->schemeAndHttpHost(); // "http://localhost:8000"
```

`fullUrlWithQuery(['type' => 'phone'])` trả URL hiện tại với query string được gộp thêm,
`fullUrlWithoutQuery(['type'])` bỏ bớt một tham số. Hai hàm này hay dùng khi dựng link lọc, sắp xếp.

⚠️ `method()` trả method "đã xét override". Form HTML chỉ gửi được GET và POST, nên Laravel cho phép
giả method bằng field ẩn `_method` (Blade có `@method('PUT')`, xem mục 8). `Request::capture()` bật
sẵn cơ chế này (`enableHttpMethodParameterOverride()`); method gốc trên đường truyền vẫn lấy được
bằng `getRealMethod()`.

### 1.4 Header, bearer token, IP

```php
$request->header('X-Request-Id');            // null nếu không có
$request->header('X-Request-Id', 'none');    // giá trị mặc định
$request->hasHeader('X-Request-Id');         // bool
$request->bearerToken();                     // phần sau "Bearer " trong header Authorization
$request->ip();                              // IP client
$request->ips();                             // mọi IP (kể cả qua proxy), IP gốc ở cuối mảng
```

Tên header không phân biệt hoa thường (`x-request-id` cũng được), giống chuẩn HTTP.

`bearerToken()` lấy token từ header `Authorization: Bearer abc123`, trả `"abc123"`. Khi không có
header, tài liệu ghi là trả chuỗi rỗng, còn mã nguồn 13.x thì không `return` gì (tức `null`). Đừng
so sánh `=== ''`; kiểm bằng `if (! $token)` cho chắc.

⚠️ Mọi header đều do client gửi, nghĩa là giả được; IP lấy qua proxy cũng đến từ header. Tài liệu
Laravel nói rõ: coi IP là input không tin cậy, chỉ dùng cho mục đích thông tin. Khi app đứng sau load balancer hoặc reverse proxy,
`ip()` trả IP của proxy, trừ khi bạn khai báo proxy đáng tin bằng `$middleware->trustProxies(at:
[...])` trong `bootstrap/app.php`. Khi đó Laravel mới chịu đọc header `X-Forwarded-For`. Đặt `at:
'*'` (tin mọi proxy) chỉ an toàn khi app không thể bị gọi trực tiếp từ Internet mà bỏ qua proxy; nếu
không, kẻ tấn công tự gửi `X-Forwarded-For` giả để đổi IP, vượt rate limit theo IP.

### 1.5 Content negotiation: client muốn nhận gì

Header `Accept` cho biết client muốn nhận kiểu dữ liệu nào. Laravel có:

```php
$request->accepts(['text/html', 'application/json']); // true nếu chấp nhận ít nhất một kiểu
$request->prefers(['text/html', 'application/json']); // kiểu được ưa thích nhất, hoặc null
$request->wantsJson();   // kiểu ĐẦU TIÊN trong Accept chứa "/json" hoặc "+json"
$request->expectsJson(); // "có vẻ" muốn JSON
$request->isJson();      // BODY gửi lên là JSON (xét Content-Type, không xét Accept)
```

`expectsJson()` rất quan trọng vì Laravel dùng nó để quyết định trả lỗi validation và lỗi exception
dạng HTML hay JSON (mục 3, mục 10). Mã nguồn của nó:

```php
return ($this->ajax() && ! $this->pjax() && $this->acceptsAnyContentType()) || $this->wantsJson();
```

Nghĩa là `true` khi: request có header `X-Requested-With: XMLHttpRequest` (AJAX kiểu cũ) và chấp nhận
mọi kiểu, hoặc header `Accept` bắt đầu bằng kiểu JSON.

⚠️ Phân biệt `isJson()` và `wantsJson()`: một cái nói về dữ liệu *gửi lên* (`Content-Type`), một
cái nói về dữ liệu *muốn nhận* (`Accept`). Client gọi API bằng `curl -d '{"a":1}' -H 'Content-Type:
application/json'` mà quên `-H 'Accept: application/json'` thì `wantsJson()` là `false`. Đây là
nguồn gốc của lỗi kinh điển "API validation sai mà lại nhận về redirect 302 sang trang chủ" (xem
mục 3.3).

## 2. Lấy input và file

### 2.1 `input()`, `query()`, `post()`, `json()`: dữ liệu đến từ đâu

```php
$name  = $request->input('name');            // tìm ở body VÀ query string
$name  = $request->input('name', 'Sally');   // mặc định khi không có key
$page  = $request->query('page');            // CHỈ query string
$email = $request->post('email');            // CHỈ body (form; request JSON thì là body JSON)
$city  = $request->json('address.city');     // CHỈ body JSON
$all   = $request->all();                    // mọi input + file, dạng mảng
```

Cái hay của `input()` là bạn không cần biết client gửi form hay JSON. Mã nguồn 13.x:

```php
// Illuminate\Http\Concerns\InteractsWithInput
public function input($key = null, $default = null)
{
    return data_get($this->getInputSource()->all() + $this->query->all(), $key, $default);
}

// Illuminate\Http\Request
protected function getInputSource()
{
    if ($this->isJson()) {
        return $this->json();          // Content-Type chứa /json hoặc +json
    }
    return in_array($this->getRealMethod(), ['GET', 'HEAD']) ? $this->query : $this->request;
}
```

Đọc kỹ sẽ thấy hai điều:

1. Body JSON chỉ được đọc khi header `Content-Type` là JSON. Client gửi JSON mà khai `Content-Type:
   text/plain` thì `input()` không thấy gì.
2. Body và query được gộp bằng toán tử `+` của mảng. Với `+`, khi trùng key thì phần tử của mảng bên
   **trái** được giữ. Vậy body thắng query.

Kiểm chứng toán tử `+` (PHP thuần):

```php
<?php
declare(strict_types=1);

$body  = ['name' => 'An', 'page' => '2'];
$query = ['page' => '1', 'sort' => 'desc'];
var_dump($body + $query);
// in ra (rút gọn, var_dump thật in mỗi giá trị trên một dòng riêng):
// array(3) {
//   ["name"]=> string(2) "An"
//   ["page"]=> string(1) "2"     <- của body, query "1" bị bỏ
//   ["sort"]=> string(4) "desc"
// }
```

Dấu chấm (*dot notation*) đi vào mảng lồng nhau: `input('products.0.name')` lấy tên sản phẩm đầu
tiên, `input('products.*.name')` lấy mảng tên của mọi sản phẩm.

### 2.2 Lấy input đã ép kiểu

Mọi giá trị từ form và query string đến dưới dạng **chuỗi** (hoặc mảng chuỗi). Với `strict_types=1`,
truyền `"20"` vào hàm nhận `int` sẽ ném `TypeError`. Laravel có các hàm lấy kèm ép kiểu:

| Method | Trả về | Ghi chú |
|---|---|---|
| `string('name')` | `Stringable` | Chuỗi kiểu fluent: `->trim()->lower()` |
| `integer('per_page')` | `int` | Ép bằng `(int)`, thiếu key thì trả mặc định (0) |
| `float('price')` | `float` | Ép bằng `(float)` |
| `boolean('archived')` | `bool` | Dùng `filter_var(..., FILTER_VALIDATE_BOOLEAN)` |
| `array('tags')` | `array` | Luôn trả mảng, thiếu key thì `[]` |
| `date('birthday')` | Carbon hoặc `null` | Sai định dạng thì ném `InvalidArgumentException` |
| `enum('status', Status::class)` | enum hoặc `null` | Giá trị không khớp case nào cũng trả `null` |

⚠️ `integer()` và `boolean()` không *kiểm tra*, chúng chỉ *ép*. `integer()` là `(int)` nên rất dễ
dãi; `boolean()` coi mọi thứ lạ là `false` (PHP thuần, mô phỏng đúng cách hai hàm này làm):

```php
<?php
declare(strict_types=1);

foreach (['12', '12abc', 'abc', '1e3'] as $s) {
    echo var_export($s, true), ' => ', (int) $s, PHP_EOL;
}
// in ra:
// '12' => 12
// '12abc' => 12
// 'abc' => 0
// '1e3' => 1000

foreach (['1', 'true', 'on', 'yes', '0', 'off', 'no', '', 'abc', '2'] as $s) {
    echo var_export($s, true), ' => ', var_export(filter_var($s, FILTER_VALIDATE_BOOLEAN), true), PHP_EOL;
}
// in ra: '1', 'true', 'on', 'yes' => true; '0', 'off', 'no', '', 'abc', '2' => false
```

Vậy `?per_page=abc` cho ra `0`, và `?per_page=999999` cho ra `999999`. Muốn từ chối giá trị rác hoặc
giới hạn khoảng, phải validate (mục 3) trước, rồi mới ép kiểu.

### 2.3 Có mặt, có giá trị, vắng mặt

Ba khái niệm khác nhau, hay bị lẫn:

| Method | `true` khi | `?name=An` | `?name=` (sau middleware, thành `null`) | không có `name` |
|---|---|---|---|---|
| `has('name')` | key có trong input | true | true | false |
| `filled('name')` | có key và không phải chuỗi rỗng | true | false | false |
| `missing('name')` | key không có | false | false | true |

Ngoài ra có `hasAny([...])`, `anyFilled([...])`, `isNotFilled(...)`, và dạng callback
`whenHas('name', fn ($v) => ...)`, `whenFilled(...)`, `whenMissing(...)`.

Cột giữa cần giải thích: Laravel mặc định có hai global middleware chuẩn hoá input.

- `TrimStrings`: cắt khoảng trắng đầu cuối mọi field chuỗi, trừ các field `password`,
  `password_confirmation`, `current_password` (mật khẩu có dấu cách ở đầu là mật khẩu khác).
- `ConvertEmptyStringsToNull`: chuỗi rỗng thành `null`.

Hệ quả: form gửi `name=   ` thì trong controller `input('name')` là `null`, không phải `"   "`. Đây
là lý do bạn sẽ hay thấy rule `nullable` (mục 3.4). Có thể tắt hai middleware này cho cả app bằng
`$middleware->remove([...])`, hoặc bỏ qua cho một số request bằng
`$middleware->trimStrings(except: [fn (Request $r) => $r->is('admin/*')])` trong `bootstrap/app.php`.

### 2.4 Lấy một phần input, thêm input

```php
$credentials = $request->only(['email', 'password']);  // chỉ các key này (key vắng mặt thì không có)
$data        = $request->except(['credit_card']);      // mọi thứ trừ key này

$request->merge(['votes' => 0]);           // ghi đè vào input
$request->mergeIfMissing(['votes' => 0]);  // chỉ thêm khi chưa có
```

Input cũng đọc được như thuộc tính: `$request->name`. Cách này tìm trong input trước, không có thì
tìm trong tham số route. Tiện nhưng mơ hồ (không rõ lấy từ đâu); trong code nghiêm túc nên dùng
`input()` hoặc `route()`.

⚠️ `except()` là danh sách đen: thêm cột mới vào bảng, quên thêm vào `except` là lọt. Khi đưa input
vào model, dùng dữ liệu đã validate (`$request->validated()`, mục 3.6), không dùng `all()` hay
`except()`.

### 2.5 File upload

```php
if ($request->hasFile('avatar') && $request->file('avatar')->isValid()) {
    $file = $request->file('avatar');   // Illuminate\Http\UploadedFile

    $file->getClientOriginalName();      // tên file client gửi: KHÔNG tin được
    $file->getClientOriginalExtension(); // đuôi theo tên client gửi: KHÔNG tin được
    $file->extension();                  // đuôi đoán từ NỘI DUNG file (MIME)
    $file->getSize();                    // byte
    $file->path();                       // đường dẫn file tạm trên server

    $path = $file->store('avatars');         // lưu vào disk mặc định, tên ngẫu nhiên, trả đường dẫn
    $path = $file->store('avatars', 's3');   // lưu vào disk "s3"
    $path = $file->storeAs('avatars', 'u42.jpg'); // tự đặt tên
}
```

`UploadedFile` kế thừa `SplFileInfo` của PHP. Nhớ lại [Chương 15](15-php-va-web.md): PHP lưu file
upload vào thư mục tạm và xoá khi request kết thúc, nên phải `store()` thì file mới còn.
`isValid()` kiểm tra upload thành công (không vướng lỗi kiểu vượt `upload_max_filesize`).

⚠️ Đừng dùng tên gốc client gửi làm tên file trên server (có thể chứa `../`, hoặc `shell.php`). Để
`store()` tự sinh tên, hoặc tự sinh tên rồi dùng `extension()` (đoán từ nội dung). Kiểm tra loại file
và kích thước bằng rule validation `file`, `image`, `mimes`, `max` (mục 3.4). Chi tiết lỗ hổng upload
xem [Chương 17](17-bao-mat.md).

### 2.6 Cookie trong request

```php
$value = $request->cookie('theme');
```

Mặc định mọi cookie do Laravel tạo đều được **mã hoá và ký** (middleware `EncryptCookies` trong
nhóm `web`). Client sửa giá trị cookie thì Laravel coi cookie đó không hợp lệ. Hệ quả: cookie do
JavaScript phía trình duyệt tự đặt (không mã hoá) sẽ không đọc được qua `$request->cookie()` trong
route `web`, trừ khi bạn khai báo nó trong danh sách loại trừ của `EncryptCookies`
(`$middleware->encryptCookies(except: ['ten_cookie'])`).

## 3. Validation cơ bản

### 3.1 Validation là gì, vì sao bắt buộc

*Validation* (kiểm tra hợp lệ) là bước kiểm xem dữ liệu client gửi lên có đúng thứ bạn mong đợi không
trước khi dùng: có đủ field bắt buộc chưa, email có đúng dạng không, số lượng có phải số nguyên dương
không, chuỗi có quá dài không.

Nguyên tắc nền: **mọi input đều không tin được**. Kiểm tra bằng JavaScript ở trình duyệt chỉ giúp
người dùng thấy lỗi sớm; kẻ tấn công gửi request bằng `curl` là bỏ qua hết. Validation phía server là
bắt buộc. Không validate thì hậu quả từ nhẹ tới nặng: lỗi 500 vì kiểu sai, dữ liệu rác trong DB, cột
`varchar(255)` bị cắt hoặc báo lỗi, tới lỗ hổng bảo mật.

### 3.2 `$request->validate()`

Cách nhanh nhất: gọi `validate()` trên request, truyền mảng *rule* (quy tắc) cho từng field.

```php
<?php
declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Post;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;

final class PostController extends Controller
{
    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'title'      => ['required', 'string', 'max:255'],
            'body'       => ['required', 'string'],
            'publish_at' => ['nullable', 'date'],
        ]);

        // Tới được dòng này nghĩa là dữ liệu hợp lệ.
        // $validated CHỈ chứa các key có trong rules: title, body, publish_at (nếu có gửi)
        $post = Post::create($validated);

        return redirect()->route('posts.show', $post);
    }
}
```

Rule viết được hai kiểu: mảng `['required', 'string', 'max:255']` hoặc chuỗi nối bằng `|`:
`'required|string|max:255'`. Nên dùng mảng: thêm được object rule (mục 4), và không vướng chuyện
tham số chứa ký tự `|` (ví dụ `regex`).

Kết quả của `validate()`:

- Hợp lệ: trả về mảng dữ liệu **đã validate** (chỉ các key có rule), code chạy tiếp.
- Không hợp lệ: ném `Illuminate\Validation\ValidationException`. Bạn **không** cần bắt nó; exception
  handler của Laravel (mục 10) tự biến nó thành response phù hợp. Dòng code sau `validate()` không
  bao giờ chạy.

Field lồng nhau dùng dấu chấm: `'author.name' => ['required']` kiểm `author[name]` trong form hoặc
`{"author": {"name": ...}}` trong JSON.

### 3.3 Khi validation thất bại: redirect hay 422

Đây là chỗ người mới hay bối rối nhất. Cùng một `ValidationException`, Laravel trả hai kiểu response
khác nhau tuỳ request "có vẻ muốn JSON" hay không. Đoạn mã quyết định nằm trong
`Illuminate\Foundation\Exceptions\Handler` (rút gọn từ mã nguồn 13.x):

```php
protected function convertValidationExceptionToResponse(ValidationException $e, $request)
{
    if ($e->response) {
        return $e->response;
    }
    return $this->shouldReturnJson($request, $e)
        ? $this->invalidJson($request, $e)   // JSON, status 422
        : $this->invalid($request, $e);      // redirect về trang trước
}

protected function invalid($request, ValidationException $exception)
{
    return redirect($exception->redirectTo ?? url()->previous())
        ->withInput(Arr::except($request->input(), $this->dontFlash))
        ->withErrors($exception->errors(), $request->input('_error_bag', $exception->errorBag));
}
```

`shouldReturnJson()` mặc định gọi `$request->expectsJson()` (mục 1.5). Project Laravel 13 mới tạo còn
cấu hình thêm trong `bootstrap/app.php`:

```php
->withExceptions(function (Exceptions $exceptions): void {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
    );
})
```

nghĩa là mọi URL bắt đầu bằng `api/` luôn nhận lỗi dạng JSON, kể cả khi client quên header `Accept`.

**Nhánh 1: request thường từ form HTML** (trình duyệt submit form):

```
 Trình duyệt              Laravel
    | POST /posts  (title="")  |
    |------------------------->|  validate() ném ValidationException
    |                          |  Handler::invalid():
    |                          |   - flash input cũ (trừ password...) vào session
    |                          |   - flash lỗi vào session (error bag "default")
    |  302 Location: /posts/create
    |<-------------------------|
    | GET /posts/create        |
    |------------------------->|  ShareErrorsFromSession đưa lỗi vào biến $errors của view
    |  200 HTML form + lỗi     |  old('title') trả lại giá trị đã nhập
    |<-------------------------|
```

Ba điều cần nhớ:

1. Lỗi và input cũ đi qua **session**, dạng *flash* (chỉ sống tới request kế tiếp, mục 9). Vì vậy
   cơ chế này chỉ chạy trong route có middleware nhóm `web` (có session).
2. Các field `password`, `password_confirmation`, `current_password` không bao giờ được flash lại
   (danh sách `$dontFlash` trong Handler), để mật khẩu không nằm trong session. Thêm field khác bằng
   `$exceptions->dontFlash([...])`.
3. "Trang trước" là `url()->previous()`: lấy header `Referer` nếu có, không có thì lấy URL trước đó
   Laravel lưu trong session, không có nữa thì về `/`. Form Request đổi được đích bằng attribute `#[RedirectTo('/...')]` (mục 5).

**Nhánh 2: request mong JSON** (SPA, mobile app, `Accept: application/json`): trả status `422
Unprocessable Content` (tên cũ *Unprocessable Entity*), body có dạng:

```json
{
    "message": "The title field is required. (and 1 more error)",
    "errors": {
        "title": ["The title field is required."],
        "author.name": ["The author.name field is required."]
    }
}
```

- `errors` là object: key là tên field (field lồng nhau viết theo dấu chấm, phần tử mảng theo chỉ số
  như `items.0.qty`), value là **mảng** thông báo (một field có thể sai nhiều rule).
- `message` là thông báo đầu tiên, kèm "(and N more error/errors)" khi có nhiều lỗi.

Vì sao là 422 mà không phải 400? `400 Bad Request` nghĩa là server không hiểu request (JSON hỏng cú
pháp...). `422` nghĩa là server hiểu cú pháp nhưng nội dung không xử lý được, đúng với "dữ liệu sai
quy tắc nghiệp vụ". Client frontend dựa vào 422 để biết "hiện lỗi dưới từng ô input".

⚠️ Lỗi kinh điển: gọi API bằng Postman hoặc `curl` mà không gửi `Accept: application/json`, với route
không nằm dưới `api/`. Validation sai, client nhận `302` về trang trước (thường là `/` vì không có
`Referer`), rồi nhận HTML trang chủ với status 200. Trông như "validation không chạy". Cách sửa: client
luôn gửi `Accept: application/json`; phía server có thể dùng `shouldRenderJsonWhen` như trên. (Với
route `POST` trong nhóm `web`, request từ `curl` không có CSRF token thường bị chặn sớm hơn bằng lỗi
419, chưa tới bước validation; xem mục 8.5.)

### 3.4 Các rule hay dùng

Bảng dưới là phần nhỏ trong hơn trăm rule có sẵn (danh sách đầy đủ ở tài liệu Validation, mục
Available Validation Rules).

| Nhóm | Rule | Ý nghĩa |
|---|---|---|
| Có mặt | `required` | Phải có và không "rỗng" (`null`, chuỗi rỗng, mảng rỗng, file không có đường dẫn) |
| | `nullable` | Cho phép giá trị `null` |
| | `sometimes` | Chỉ kiểm field này khi nó **có mặt** trong input |
| | `filled` | Nếu có mặt thì không được rỗng |
| | `required_if:type,company` | Bắt buộc khi field `type` bằng `company` (còn `required_with`, `required_without`...) |
| | `prohibited` | Không được có (hoặc phải rỗng) |
| Kiểu | `string`, `integer`, `numeric`, `boolean`, `array`, `date` | Đúng kiểu |
| Chuỗi | `email`, `url`, `uuid`, `alpha_dash`, `regex:/^[A-Z]+$/`, `starts_with:foo` | Đúng định dạng |
| Kích thước | `min:3`, `max:255`, `between:1,10`, `size:12` | Xem ⚠️ ngay dưới bảng |
| Giá trị | `in:draft,published`, `not_in:...`, `Rule::enum(Status::class)` | Thuộc tập cho phép |
| So sánh | `confirmed`, `same:field`, `different:field`, `gt:field`, `after:today` | So với field khác hoặc mốc |
| Mảng | `array:name,email`, `distinct`, `items.*.qty` | Kiểm khoá, phần tử |
| File | `file`, `image`, `mimes:jpg,png`, `extensions:pdf`, `max:2048` | Đúng loại, kích thước (KB) |
| Database | `unique:users,email`, `exists:teams,id` | Có hoặc chưa có trong bảng |
| Điều khiển | `bail` | Dừng kiểm field này ở rule sai đầu tiên |

⚠️ `min`, `max`, `size`, `between` đo theo **kiểu** của field:

- Chuỗi: số ký tự. `max:255` là tối đa 255 ký tự.
- Số: giá trị, nhưng **chỉ khi field có rule `numeric` hoặc `integer`** (hoặc `decimal`).
- Mảng: số phần tử.
- File: kích thước theo **kilobyte**. `max:2048` là 2 MB.

Vậy `'age' => ['max:150']` không có `integer`: client gửi `"200"` (chuỗi 3 ký tự) vẫn qua, vì Laravel
đo độ dài chuỗi. Viết đúng: `['integer', 'min:0', 'max:150']`.

⚠️ `integer` dùng `FILTER_VALIDATE_INT` nên chấp nhận cả chuỗi `"42"` (giá trị trong `validated()` vẫn
là chuỗi `"42"`, validation không đổi kiểu). Muốn chỉ nhận đúng kiểu `int` của JSON thì dùng
`integer:strict`. Tương tự có `numeric:strict`, `boolean:strict`. Rule `boolean` thường nhận `true`,
`false`, `1`, `0`, `"1"`, `"0"`; chuỗi `"true"`, `"on"` không hợp lệ với rule này (dù
`$request->boolean()` coi chúng là `true`). Checkbox HTML gửi `"on"` nên với checkbox hay dùng rule
`accepted` hoặc đặt `value="1"` cho input.

⚠️ `image` mặc định không nhận SVG (SVG chứa được JavaScript, nguy cơ XSS); muốn nhận phải ghi
`image:allow_svg`. `mimes` và `File::types([...])` kiểm MIME bằng cách **đọc nội dung file**, không
tin đuôi file client đặt.

### 3.5 `required`, `nullable`, `sometimes`: rule nào chạy khi nào

Bộ validator của Laravel có một luật ngầm quan trọng (theo `Validator::isValidatable()` trong mã
nguồn 13.x): một rule thường (`string`, `date`, `email`, `unique`, rule tự viết...) **không chạy** khi
field vắng mặt hoặc là chuỗi rỗng. Chỉ các rule "ngầm định bắt buộc" (*implicit*) như `required`,
`required_if`, `accepted`, `present` mới chạy trong trường hợp đó. Còn khi field **có mặt với giá trị
`null`**, mọi rule đều chạy, trừ khi có `nullable`.

Kết hợp với `ConvertEmptyStringsToNull` (ô input để trống thành `null`), ta có bảng kết quả cho field
`publish_at`:

| Input | `['date']` | `['nullable', 'date']` | `['required', 'date']` | `['sometimes', 'required', 'date']` |
|---|---|---|---|---|
| không gửi key | qua (không kiểm) | qua | **sai**: required | qua (bỏ qua cả field) |
| `publish_at=` (thành `null`) | **sai**: must be a valid date | qua | **sai**: required | **sai**: required |
| `publish_at=abc` | sai | sai | sai | sai |
| `publish_at=2026-10-03` | qua | qua | qua | qua |

Cách chọn:

- Field bắt buộc: `required` + rule kiểu.
- Field tuỳ chọn trong form (form luôn gửi key, có thể rỗng): `nullable` + rule kiểu.
- API `PATCH` cập nhật một phần (client chỉ gửi field muốn đổi): `sometimes` + `required` + rule
  kiểu. Gửi thì phải hợp lệ, không gửi thì giữ nguyên.

⚠️ Cột 1 là cái bẫy: chỉ ghi `['date']` không có nghĩa là "bắt buộc là ngày". Không gửi key là lọt.

### 3.6 Lấy dữ liệu đã validate

```php
$data = $request->validate([...]);            // mảng đã validate
$data = $validator->validated();              // với validator tạo tay
$data = $request->validated();                // với Form Request (mục 5)
$data = $request->safe()->only(['name', 'email']);
$data = $request->safe()->except(['avatar']);
$data = $request->safe()->merge(['user_id' => $request->user()->id]);
```

`validated()` chỉ chứa các key có trong rules. Đây là lớp bảo vệ quan trọng: client gửi thêm
`is_admin=1` mà rules không có `is_admin` thì nó không lọt vào `$data`.

⚠️ Ngoại lệ: rule `array` không kèm danh sách khoá. `'meta' => ['array']` làm `validated()` trả **toàn
bộ** mảng `meta` với mọi khoá con client gửi, kể cả khoá không được validate. Tài liệu Laravel khuyên
luôn liệt kê khoá cho phép: `'meta' => ['array:color,size']`.

### 3.7 Validator tạo tay

Khi cần validate dữ liệu không đến từ request (dòng CSV import, payload webhook đã giải mã...), hoặc
muốn tự xử lý khi sai thay vì để Laravel redirect:

```php
use Illuminate\Support\Facades\Validator;

$validator = Validator::make($row, [
    'email' => ['required', 'email'],
    'qty'   => ['required', 'integer', 'min:1'],
]);

if ($validator->fails()) {
    // $validator->errors() là MessageBag
    logger()->warning('Dòng CSV lỗi', $validator->errors()->toArray());
    return;
}

$data = $validator->validated();
```

Gọi `$validator->validate()` thì quay về hành vi tự động (ném `ValidationException`). Tham số thứ 3
và 4 của `make()` là thông báo tự đặt và tên field hiển thị (mục 3.8).

Tự ném lỗi validation từ chỗ bất kỳ (ví dụ trong service, khi kiểm tra cần gọi API ngoài):

```php
use Illuminate\Validation\ValidationException;

throw ValidationException::withMessages([
    'coupon' => ['Mã giảm giá đã hết hạn.'],
]);
```

Response sinh ra giống hệt lỗi validation thường (redirect kèm lỗi hoặc JSON 422).

### 3.8 Thông báo lỗi, tên field, error bag

**MessageBag.** Lỗi được gom trong object `Illuminate\Support\MessageBag`:

```php
$errors = $validator->errors();
$errors->first('email');      // thông báo đầu tiên của field email
$errors->get('email');        // mảng mọi thông báo của email
$errors->get('items.*');      // thông báo của mọi phần tử mảng items
$errors->all();               // mảng phẳng mọi thông báo
$errors->has('email');        // có lỗi không
```

**Đổi thông báo.** Thông báo mặc định viết bằng tiếng Anh, nằm trong file ngôn ngữ của framework,
dạng `'required' => 'The :attribute field is required.'`. `:attribute` được thay bằng tên field (dấu
gạch dưới thành khoảng trắng: `team_name` thành `team name`). Có ba tầng tuỳ chỉnh:

```php
$request->validate(
    ['email' => ['required', 'email'], 'qty' => ['required', 'integer', 'min:1']],
    [   // thông báo: "field.rule" hoặc chỉ "rule"
        'email.required' => 'Vui lòng nhập email.',
        'min'            => ':attribute phải ít nhất :min.',
    ],
    [   // tên hiển thị của field
        'qty' => 'Số lượng',
    ],
);
```

Muốn đổi cho cả app (ví dụ dịch sang tiếng Việt): chạy `php artisan lang:publish` để tạo thư mục
`lang/` (skeleton mặc định không có), rồi tạo `lang/vi/validation.php` và đặt `APP_LOCALE=vi`.

**Error bag có tên.** Một trang có hai form (đăng nhập và đăng ký) cùng có field `email`. Nếu lỗi của
cả hai cùng vào bag `default`, lỗi form này hiện dưới form kia. Đặt tên bag để tách:

```php
$request->validateWithBag('login', ['email' => ['required', 'email']]);
// hoặc: return back()->withErrors($validator, 'login');
```

```blade
{{ $errors->login->first('email') }}
@error('email', 'login') <span>{{ $message }}</span> @enderror
```

Biến `$errors` có mặt trong **mọi** view của route `web` nhờ middleware `ShareErrorsFromSession`, kể cả
khi không có lỗi (lúc đó là bag rỗng), nên view không cần kiểm `isset($errors)`.

## 4. Rule nâng cao và rule tự viết

### 4.1 Rule dạng object: `Rule::...`

Ngoài chuỗi, Laravel có lớp `Illuminate\Validation\Rule` để dựng rule bằng code, đỡ phải nối chuỗi và
an toàn hơn:

```php
use App\Enums\OrderStatus;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Rules\File;

$request->validate([
    'status'  => ['required', Rule::enum(OrderStatus::class)],            // backed enum
    'role'    => ['required', Rule::in(['admin', 'editor', 'viewer'])],
    'email'   => ['required', 'email', Rule::unique('users')->ignore($user)],
    'team_id' => ['required', Rule::exists('teams', 'id')->where('active', 1)],
    'avatar'  => ['nullable', File::image()->max('2mb')],
]);
```

`Rule::unique('users')->ignore($user)` dùng khi **cập nhật**: email phải không trùng với ai, trừ chính
record đang sửa (nếu không, user bấm "Lưu" mà không đổi email cũng báo "email đã tồn tại").

⚠️ Tài liệu Laravel cảnh báo: không bao giờ truyền input của người dùng vào `ignore()`. Chỉ truyền id
do hệ thống sinh, tốt nhất là truyền cả model (`ignore($user)`). Truyền input vào là mở đường cho SQL
injection.

### 4.2 Mảng và phần tử mảng

Đơn hàng có nhiều dòng hàng:

```json
{
  "customer_note": "Giao giờ hành chính",
  "items": [
    {"product_id": 10, "qty": 2},
    {"product_id": 11, "qty": 0}
  ]
}
```

```php
$data = $request->validate([
    'customer_note'    => ['nullable', 'string', 'max:500'],
    'items'            => ['required', 'array', 'min:1', 'max:50'],
    'items.*.product_id' => ['required', 'integer', 'distinct', 'exists:products,id'],
    'items.*.qty'      => ['required', 'integer', 'min:1', 'max:100'],
]);
```

`*` nghĩa là "mọi phần tử". Lỗi được báo theo chỉ số cụ thể: dòng thứ hai sai thì key lỗi là
`items.1.qty`. `distinct` đảm bảo các `product_id` không lặp. Trong thông báo tự đặt có thể dùng
`:index` (đếm từ 0) và `:position` (đếm từ 1): `'items.*.qty.min' => 'Dòng #:position: số lượng phải
ít nhất :min.'`.

⚠️ Giới hạn số phần tử (`max:50`). Không giới hạn thì client gửi mảng mười nghìn phần tử, mỗi phần tử
một câu `exists` vào DB.

### 4.3 Rule điều kiện

```php
$request->validate([
    'type'         => ['required', Rule::in(['personal', 'company'])],
    'company_name' => ['required_if:type,company', 'nullable', 'string', 'max:255'],
    'tax_code'     => ['exclude_unless:type,company', 'required', 'string'],
]);
```

- `required_if:type,company`: bắt buộc khi `type` là `company`.
- `exclude_unless:type,company`: nếu `type` không phải `company` thì **bỏ hẳn** field này: không
  kiểm, và không có trong `validated()`. Khác với `required_if` (field vẫn được kiểm các rule còn lại và
  vẫn vào `validated()`).
- Điều kiện phức tạp hơn: `Rule::requiredIf(fn () => ...)`, hoặc `$validator->sometimes('reason',
  'required', fn ($input) => $input->games >= 100)`.

### 4.4 Rule tự viết bằng closure

Dùng một lần, viết ngay trong mảng rules. Closure nhận tên field, giá trị, và hàm `$fail` để báo lỗi:

```php
use Closure;

$request->validate([
    'username' => [
        'required', 'string', 'max:30',
        function (string $attribute, mixed $value, Closure $fail): void {
            // không có 'bail' thì closure vẫn chạy dù rule 'string' đã sai, nên tự kiểm kiểu
            if (is_string($value) && in_array(strtolower($value), ['admin', 'root', 'support'], true)) {
                $fail("The {$attribute} is reserved.");
            }
        },
    ],
]);
```

### 4.5 Rule object: class implement `ValidationRule`

Dùng lại nhiều chỗ thì tạo class: `php artisan make:rule VietnamesePhone`, Laravel sinh file trong
`app/Rules/`:

```php
<?php
declare(strict_types=1);

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

final class VietnamesePhone implements ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if (!is_string($value) || preg_match('/^0\d{9}$/', $value) !== 1) {
            $fail('The :attribute must be a 10-digit phone number starting with 0.');
        }
    }
}
```

```php
$request->validate(['phone' => ['required', new VietnamesePhone()]]);
```

Cơ chế bên trong rất đơn giản: validator gọi `validate()` của rule cho từng field, truyền một closure
`$fail`; gọi `$fail(...)` là thêm một thông báo lỗi vào MessageBag của field đó. Mô phỏng bằng PHP
thuần:

```php
<?php
declare(strict_types=1);

interface ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void;
}

final class VietnamesePhone implements ValidationRule
{
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if (!is_string($value) || preg_match('/^0\d{9}$/', $value) !== 1) {
            $fail("Trường {$attribute} phải là số điện thoại 10 chữ số bắt đầu bằng 0.");
        }
    }
}

/** @param array<string, list<ValidationRule>> $rules
 *  @return array<string, list<string>> */
function runRules(array $data, array $rules): array
{
    $errors = [];
    foreach ($rules as $field => $fieldRules) {
        foreach ($fieldRules as $rule) {
            $rule->validate($field, $data[$field] ?? null, function (string $message) use (&$errors, $field): void {
                $errors[$field][] = $message;
            });
        }
    }
    return $errors;
}

print_r(runRules(['phone' => '0912345678'], ['phone' => [new VietnamesePhone()]]));
// in ra (print_r thật xuống dòng, ở đây viết gọn trên một dòng): Array ( )
print_r(runRules(['phone' => '+84 912'], ['phone' => [new VietnamesePhone()]]));
// in ra: Array ( [phone] => Array ( [0] => Trường phone phải là số điện thoại 10 chữ số bắt đầu bằng 0. ) )
```

Rule cần đọc field khác thì implement thêm `Illuminate\Contracts\Validation\DataAwareRule` (Laravel
gọi `setData(array $data)` trước khi validate). Thông báo có thể là key dịch:
`$fail('validation.phone')->translate()`.

⚠️ Như mục 3.5: rule tự viết **không chạy** khi field vắng mặt hoặc là chuỗi rỗng. Đừng trông chờ rule
tự viết bắt lỗi "thiếu field"; ghép thêm `required`. Nếu thật sự cần rule chạy cả khi rỗng, tạo rule
*implicit* bằng `php artisan make:rule TenRule --implicit`.

### 4.6 Kiểm tra cần nhiều field: `after`

Có những ràng buộc không thuộc về một field riêng lẻ: "ngày kết thúc sau ngày bắt đầu" (cái này có
rule `after:start_date`), "tổng tiền các dòng không vượt hạn mức của khách hàng", "slot đặt lịch còn
trống". Dùng hook `after`, chạy sau khi các rule thường đã chạy:

```php
use Illuminate\Validation\Validator as ValidatorInstance;

$validator = Validator::make($request->all(), $rules);

$validator->after(function (ValidatorInstance $v): void {
    if ($v->errors()->isNotEmpty()) {
        return; // dữ liệu cơ bản đã sai thì khỏi kiểm tiếp
    }
    if (! $this->slots->isAvailable($v->getData()['slot_id'])) {
        $v->errors()->add('slot_id', 'Khung giờ đã có người đặt.');
    }
});

$validator->validate();
```

### 4.7 Giới hạn của validation: race condition

Rule `unique` và `exists` chỉ là một câu `SELECT` chạy **trước** khi bạn ghi dữ liệu. Giữa lúc kiểm và
lúc ghi, request khác có thể chen vào. Hai người đăng ký cùng email cùng lúc:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | Validate: `SELECT count(*) FROM users WHERE email='an@x.vn'` | | 0, qua |
| 2 | | Validate cùng câu đó | 0, qua (A chưa insert) |
| 3 | `INSERT INTO users ... 'an@x.vn'` | | Thành công |
| 4 | | `INSERT INTO users ... 'an@x.vn'` | Không có unique index: hai tài khoản trùng email. Có unique index: MySQL báo lỗi 1062 Duplicate entry |

Validation ở tầng ứng dụng chỉ để trả thông báo đẹp cho trường hợp thường gặp. Hàng rào thật là ràng
buộc trong database: unique index (`$table->string('email')->unique()` trong migration, xem
[Chương 27](27-laravel-database-eloquent.md)) và foreign key cho `exists`. Lỗi trùng ở bước 4 bắn ra
`Illuminate\Database\UniqueConstraintViolationException`; bắt nó và đổi thành lỗi validation để client
vẫn nhận 422 thay vì 500:

```php
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Validation\ValidationException;

try {
    $user = User::create($data);
} catch (UniqueConstraintViolationException) {
    throw ValidationException::withMessages(['email' => ['The email has already been taken.']]);
}
```

## 5. Form Request

### 5.1 Vì sao tách validation ra class riêng

Controller có `validate([...])` dài hai mươi dòng, cộng kiểm quyền, cộng chuẩn hoá input, thì method
`store()` thành nồi lẩu. *Form Request* là một class kế thừa `Illuminate\Foundation\Http\FormRequest`
(mà `FormRequest` lại kế thừa `Request`), gom ba việc: chuẩn hoá input, kiểm quyền, kiểm dữ liệu.

```bash
# chạy ở thư mục gốc project Laravel
php artisan make:request StorePostRequest     # tạo app/Http/Requests/StorePostRequest.php
```

⚠️ File sinh ra có `authorize()` trả `false`. Quên sửa thì mọi request bị 403. Nếu kiểm quyền ở nơi
khác (policy, middleware), sửa thành `return true;` hoặc xoá hẳn method (không có `authorize()` thì
Laravel coi là được phép).

### 5.2 Một Form Request đầy đủ

```php
<?php
declare(strict_types=1);

namespace App\Http\Requests;

use App\Enums\PostStatus;
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Support\Str;
use Illuminate\Validation\Rule;
use Illuminate\Validation\Validator;

final class UpdatePostRequest extends FormRequest
{
    // 1. Chạy ĐẦU TIÊN: chuẩn hoá input trước khi kiểm
    protected function prepareForValidation(): void
    {
        if ($this->filled('title') && ! $this->filled('slug')) {
            $this->merge(['slug' => Str::slug((string) $this->input('title'))]);
        }
    }

    // 2. Kiểm quyền. false => 403, controller không chạy
    public function authorize(): bool
    {
        // {post} trong route đã được route model binding đổi thành model Post
        return $this->user()?->can('update', $this->route('post')) ?? false;
    }

    // 3. Rules
    /** @return array<string, mixed> */
    public function rules(): array
    {
        return [
            'title'  => ['sometimes', 'required', 'string', 'max:255'],
            'slug'   => ['sometimes', 'required', 'alpha_dash', 'max:255',
                         Rule::unique('posts')->ignore($this->route('post'))],
            'status' => ['sometimes', 'required', Rule::enum(PostStatus::class)],
            'tags'   => ['sometimes', 'array', 'max:10'],
            'tags.*' => ['string', 'max:30'],
        ];
    }

    // 4. Kiểm tra liên field, chạy sau rules
    /** @return list<callable> */
    public function after(): array
    {
        return [
            function (Validator $validator): void {
                if ($this->input('status') === PostStatus::Published->value
                    && $this->route('post')->body === '') {
                    $validator->errors()->add('status', 'Không thể publish bài viết rỗng.');
                }
            },
        ];
    }

    /** @return array<string, string> */
    public function messages(): array
    {
        return ['title.required' => 'Tiêu đề không được để trống.'];
    }

    /** @return array<string, string> */
    public function attributes(): array
    {
        return ['tags.*' => 'tag'];
    }
}
```

Dùng trong controller: chỉ cần type-hint, không gọi gì thêm.

```php
public function update(UpdatePostRequest $request, Post $post): RedirectResponse
{
    $post->update($request->validated());   // tới đây là đã qua authorize và rules
    return to_route('posts.show', $post)->with('status', 'Đã lưu.');
}
```

### 5.3 Thứ tự chạy bên trong

Khi container khởi tạo một object implement `ValidatesWhenResolved` (Form Request là một), nó gọi
`validateResolved()`. Mã nguồn trong `Illuminate\Validation\ValidatesWhenResolvedTrait` (13.x, bỏ phần
Precognition):

```php
public function validateResolved()
{
    $this->prepareForValidation();

    if (! $this->passesAuthorization()) {
        $this->failedAuthorization();      // ném AuthorizationException => 403
    }

    $instance = $this->getValidatorInstance();   // dựng validator từ rules(), messages(), attributes(), after()

    if ($instance->fails()) {
        $this->failedValidation($instance);       // ném ValidationException => redirect hoặc 422
    }

    $this->passedValidation();
}
```

```
 Request đến
   │
   ├─ middleware (auth, SubstituteBindings: {post} -> model Post, ...)
   │
   ├─ Resolve tham số controller: gặp UpdatePostRequest
   │     1. prepareForValidation()
   │     2. authorize()            ── false ──> 403
   │     3. rules() + after()      ── sai ────> 302 về trang trước / 422 JSON
   │     4. passedValidation()
   │
   └─ Controller::update() chạy với dữ liệu đã sạch
```

Hệ quả cần nhớ:

- `prepareForValidation()` chạy **trước cả** `authorize()`. Đừng làm việc tốn kém hay có tác dụng phụ ở
  đó; người không có quyền cũng chạy tới đây.
- Form Request chạy **sau** middleware (vì nó là tham số của controller), nên trong `authorize()` đã có
  user đăng nhập và model đã được binding.
- Lỗi validation của Form Request giống hệt `validate()`: redirect kèm lỗi, hoặc 422 JSON.

### 5.4 Tuỳ chỉnh hành vi bằng attribute và method

Laravel 13 cho cấu hình Form Request bằng PHP attribute đặt trên class:

| Attribute | Tác dụng |
|---|---|
| `#[StopOnFirstFailure]` | Dừng toàn bộ validation ở lỗi đầu tiên (khác `bail` chỉ dừng một field) |
| `#[RedirectTo('/dashboard')]`, `#[RedirectToRoute('dashboard')]` | Sai thì redirect tới đây thay vì trang trước |
| `#[ErrorBag('login')]` | Lỗi vào error bag tên `login` |
| `#[FailOnUnknownFields]` | Field gửi lên mà không có trong `rules()` làm validation thất bại |

Các attribute nằm trong namespace `Illuminate\Foundation\Http\Attributes`.

`#[FailOnUnknownFields]` cũng bật được cho mọi Form Request bằng `FormRequest::failOnUnknownFields();`
trong `AppServiceProvider::boot()`, và tắt riêng một class bằng `#[FailOnUnknownFields(false)]`. Theo mã
nguồn 13.x, nó chỉ xét field trong body (form hoặc JSON), không xét query string, và chấp nhận field
`xxx_confirmation` khi có rule cho `xxx`. Đây là lớp chặn thêm, không thay cho việc chỉ dùng
`validated()` và khai báo `$fillable` trên model.

Muốn thay hẳn cách xử lý khi sai, override `failedValidation()` hoặc `failedAuthorization()`. Ví dụ API
muốn trả 403 kèm JSON riêng thay vì exception mặc định:

```php
use Illuminate\Http\Exceptions\HttpResponseException;

protected function failedAuthorization(): void
{
    throw new HttpResponseException(response()->json(['message' => 'Bạn không có quyền sửa bài này.'], 403));
}
```

`HttpResponseException` mang sẵn một response; Handler trả thẳng response đó.

### 5.5 `validated()` khác `all()` ở đâu

Form Request **là** một Request, nên vẫn có `all()`, `input()`. Nhưng:

| Lấy bằng | Chứa gì |
|---|---|
| `$request->all()` / `input()` | Mọi thứ client gửi (kể cả `is_admin=1` lén thêm vào), cộng phần bạn `merge()` |
| `$request->validated()` | Chỉ các key có trong `rules()` và đã qua kiểm |
| `$request->safe()` | Như `validated()` nhưng là object `ValidatedInput` có `only()`, `except()`, `merge()` |

⚠️ `Post::create($request->all())` trong controller dùng Form Request là bỏ phí cả lớp bảo vệ. Luôn dùng
`validated()` hoặc `safe()`. Bàn thêm về *mass assignment* ở [Chương 27](27-laravel-database-eloquent.md).

## 6. Response

### 6.1 Controller trả gì thì client nhận gì

Ở PHP thuần, bạn `echo` nội dung và gọi `header()` (xem [Chương 15](15-php-va-web.md)). Trong Laravel,
route hoặc controller **trả về** (`return`) một giá trị, và router chuyển giá trị đó thành object
response. Hàm làm việc này là `Router::toResponse()`; tóm tắt theo mã nguồn 13.x:

| Controller trả về | Thành response |
|---|---|
| Object implement `Responsable` (ví dụ API Resource) | Gọi `->toResponse($request)` của nó |
| Model Eloquent **vừa được tạo** trong request này (`wasRecentlyCreated`) | JSON, status **201** |
| Mảng, Collection, model, object `Arrayable`/`Jsonable`/`JsonSerializable` | JSON, status 200 |
| Chuỗi (hoặc object `Stringable`) | HTML, status 200, `Content-Type: text/html` |
| Object response sẵn (`Response`, `JsonResponse`, `RedirectResponse`...) | Giữ nguyên |

```php
Route::get('/hello', fn () => 'Hello World');          // 200 text/html
Route::get('/numbers', fn () => [1, 2, 3]);            // 200 application/json: [1,2,3]
Route::get('/users/{user}', fn (User $user) => $user); // JSON của model (ẩn các cột trong $hidden)
```

Mọi object response của Laravel kế thừa `Symfony\Component\HttpFoundation\Response`. Response được
tạo xong thì còn đi ngược qua các middleware (chúng có thể thêm header, cookie) rồi mới được gửi
(`$response->send()`), như đã thấy ở [Chương 24](24-laravel-routing-controller-middleware.md).

### 6.2 `response()`: status, header, cookie

```php
return response('Created', 201)
    ->header('Content-Type', 'text/plain')
    ->withHeaders(['X-Request-Id' => $requestId, 'Cache-Control' => 'no-store'])
    ->cookie('theme', 'dark', 60 * 24 * 30);   // tên, giá trị, số PHÚT sống

return response()->noContent();                 // 204, body rỗng: hợp cho DELETE thành công
```

Cookie đầy đủ tham số giống `setcookie()` của PHP: `->cookie($name, $value, $minutes, $path, $domain,
$secure, $httpOnly)`. Xoá cookie: `->withoutCookie('theme')`. Khi chưa có object response trong tay (ví
dụ đang trong service), "xếp hàng" cookie để Laravel gắn vào response sau:
`Cookie::queue('theme', 'dark', 60)`.

⚠️ Tham số thời gian của cookie Laravel tính bằng **phút**, còn `setcookie()` của PHP nhận **timestamp
hết hạn**. Đừng truyền `time() + 3600`.

### 6.3 JSON

```php
return response()->json(['id' => $order->id, 'status' => 'paid'], 201);
return response()->json($data, 200, [], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
```

`response()->json()` gọi `json_encode` với tham số `$options` (mặc định `0`) và đặt `Content-Type:
application/json`. Với `0`, ký tự ngoài ASCII bị viết thành `\uXXXX`. Đây là JSON hợp lệ, client parse
ra đúng chữ, chỉ khó đọc khi xem log (PHP thuần):

```php
<?php
declare(strict_types=1);

$data = ['message' => 'Đã lưu', 'url' => 'https://x.vn/a'];
echo json_encode($data), PHP_EOL;
// in ra: {"message":"\u0110\u00e3 l\u01b0u","url":"https:\/\/x.vn\/a"}
echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES), PHP_EOL;
// in ra: {"message":"Đã lưu","url":"https://x.vn/a"}
```

⚠️ Dữ liệu không encode được (chuỗi không phải UTF-8 hợp lệ, `NAN`, `INF`) làm `JsonResponse` ném
`InvalidArgumentException` với thông báo của `json_last_error_msg()`, thành lỗi 500. Hay gặp khi đọc
dữ liệu cũ lưu bằng charset `latin1`.

### 6.4 Redirect

Redirect là response status 3xx kèm header `Location`; trình duyệt tự gửi request mới tới URL đó.

```php
return redirect('/dashboard');                         // URL
return redirect()->route('posts.show', $post);         // route có tên, model tự lấy khoá
return to_route('posts.show', $post);                  // helper viết tắt của dòng trên
return redirect()->action([PostController::class, 'index']);
return back();                                         // về trang trước (cần session: nhóm web)
return redirect()->away('https://example.com');        // ra domain ngoài
```

Mặc định status là `302 Found`.

Kèm dữ liệu sang request sau (đi qua session flash, mục 9):

```php
return to_route('posts.index')->with('status', 'Đã xoá bài viết.');  // flash một giá trị
return back()->withInput()->withErrors(['email' => 'Sai thông tin đăng nhập.']);
```

*Post/Redirect/Get (PRG)*: sau khi form POST thành công, luôn trả redirect chứ không trả HTML trực
tiếp. Nếu trả HTML, người dùng bấm F5 thì trình duyệt hỏi "gửi lại form?" và có thể tạo đơn hàng hai
lần. Sau redirect, trang đang hiển thị là kết quả của một GET, F5 vô hại.

⚠️ *Open redirect*: `redirect($request->input('next'))` cho phép kẻ xấu tạo link
`https://app-cua-ban.vn/login?next=https://trang-gia-mao.vn` để lừa người dùng. Chỉ redirect tới URL
nội bộ: kiểm tra `next` bắt đầu bằng `/` và không bắt đầu bằng `//`, hoặc dùng danh sách trắng. Cơ chế
có sẵn `redirect()->intended()` lấy URL đã lưu trong session (không lấy từ input), xem
[Chương 28](28-laravel-auth.md).

### 6.5 View

```php
return view('posts.show', ['post' => $post]);                 // resources/views/posts/show.blade.php
return response()->view('errors.maintenance', [], 503);        // view kèm status khác 200
```

Blade ở mục 8.

### 6.6 File: download, hiển thị, stream

```php
// Bắt tải về: header Content-Disposition: attachment; filename="bao-cao.pdf"
return response()->download(storage_path('app/reports/42.pdf'), 'bao-cao.pdf');

// Hiển thị ngay trong trình duyệt (ảnh, PDF)
return response()->file(storage_path('app/reports/42.pdf'));

// Nội dung sinh ra lúc chạy, không cần ghi ra đĩa trước
return response()->streamDownload(function (): void {
    $out = fopen('php://output', 'w');
    fputcsv($out, ['id', 'email'], escape: '');
    foreach (User::query()->select(['id', 'email'])->lazy() as $user) {
        fputcsv($out, [$user->id, $user->email], escape: '');
    }
    fclose($out);
}, 'users.csv', ['Content-Type' => 'text/csv']);
```

`download()` và `file()` dùng `BinaryFileResponse` của Symfony: đọc file và gửi dần, không nạp cả file
vào bộ nhớ.

`streamDownload()` và `stream()` nhận một closure; closure chỉ chạy **khi response được gửi**, ghi thẳng
ra output. Kết hợp với `lazy()` (đọc DB theo từng lô) thì xuất được file CSV triệu dòng mà bộ nhớ gần
như không tăng. So với cách gom hết vào một chuỗi rồi `return`: cách đó cần bộ nhớ bằng cả file.

Biến thể khác: `response()->stream($callback)` (stream nội dung tuỳ ý, ví dụ trả từng phần câu trả lời
của AI), `response()->streamJson(['users' => User::cursor()])` (JSON sinh dần), và
`response()->eventStream(...)` (Server-Sent Events). Tài liệu Laravel nhắc khi stream qua Nginx thì
nên gửi header `X-Accel-Buffering: no` để Nginx không gom output lại (ví dụ trong tài liệu gửi kèm
header này; với `stream()` mà closure là Generator, Laravel tự thêm).

⚠️ Đường dẫn file trong `download()` / `file()` mà lấy từ input (`storage_path('app/'.$request->input('f'))`)
là lỗ hổng *path traversal*: `f=../../.env` tải được file cấu hình. Chỉ dùng đường dẫn lưu trong DB
hoặc kiểm `realpath()` nằm trong thư mục cho phép (xem [Chương 17](17-bao-mat.md)).

⚠️ Khi stream, exception xảy ra bên trong closure thì header (kể cả status 200) **đã gửi đi rồi**,
không thể đổi thành trang lỗi 500 được nữa. Client nhận một file bị cắt cụt. Kiểm tra quyền, kiểm tra
dữ liệu đầu vào trước khi bắt đầu stream.

## 7. API Resource: biến model thành JSON có kiểm soát

### 7.1 Vấn đề khi trả thẳng model

`return $user;` tiện, nhưng JSON trả ra phụ thuộc vào **cấu trúc bảng**:

- Thêm cột `two_factor_secret` vào bảng mà quên đưa vào `$hidden` là lộ ra API.
- Đổi tên cột `fullname` thành `name` là mọi app mobile đang dùng API gãy.
- Muốn trả field tính toán (`avatar_url`), field tuỳ quyền (chỉ admin thấy `email`), quan hệ lồng nhau
  có điều kiện... thì không có chỗ đặt.

*API Resource* là một lớp biến đổi (*transformation layer*) giữa model và JSON: bạn khai báo rõ ràng
từng field trả ra. Hợp đồng API (*API contract*) tách khỏi schema DB.

### 7.2 Viết resource

```bash
php artisan make:resource UserResource     # app/Http/Resources/UserResource.php
```

```php
<?php
declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin \App\Models\User */
final class UserResource extends JsonResource
{
    /** @return array<string, mixed> */
    public function toArray(Request $request): array
    {
        return [
            'id'          => $this->id,
            'name'        => $this->name,
            'avatar_url'  => $this->avatar_path ? asset('storage/'.$this->avatar_path) : null,
            // chỉ admin mới thấy email; điều kiện sai thì KEY bị bỏ hẳn khỏi JSON
            'email'       => $this->when($request->user()?->isAdmin() === true, $this->email),
            // chỉ có khi controller đã eager load quan hệ posts
            'posts'       => PostResource::collection($this->whenLoaded('posts')),
            // chỉ có khi controller đã gọi withCount('posts') / loadCount('posts')
            'posts_count' => $this->whenCounted('posts'),
            'created_at'  => $this->created_at,
        ];
    }
}
```

`$this->id` đọc được vì resource chuyển (*proxy*) mọi truy cập thuộc tính và method xuống model bên
trong (`$this->resource`). Dòng `@mixin` giúp IDE và PHPStan hiểu điều đó.

Dùng trong controller:

```php
public function show(User $user): UserResource
{
    return new UserResource($user->loadCount('posts'));
}

public function index(): AnonymousResourceCollection
{
    return UserResource::collection(User::with('posts')->paginate(20));
}
```

(`AnonymousResourceCollection` nằm ở `Illuminate\Http\Resources\Json`.) Laravel 13 còn có cách viết
ngắn `$user->toResource()` và `User::paginate()->toResourceCollection()`, tự tìm class
`UserResource` theo quy ước tên.

### 7.3 Hình dạng JSON: `data`, phân trang, meta

Resource ngoài cùng được bọc trong key `data`:

```json
{
    "data": {
        "id": 1,
        "name": "An",
        "avatar_url": null,
        "posts_count": 3,
        "created_at": "..."
    }
}
```

Collection được phân trang có thêm `links` và `meta` do Laravel tự sinh (trích từ tài liệu Laravel):

```json
{
    "data": [ { "id": 1, "name": "..." }, { "id": 2, "name": "..." } ],
    "links": {
        "first": "http://example.com/users?page=1",
        "last": "http://example.com/users?page=1",
        "prev": null,
        "next": null
    },
    "meta": {
        "current_page": 1, "from": 1, "last_page": 1,
        "path": "http://example.com/users", "per_page": 15, "to": 10, "total": 10
    }
}
```

- Bỏ lớp `data` cho resource đơn: `JsonResource::withoutWrapping()` trong `AppServiceProvider::boot()`.
  Response phân trang thì vẫn luôn có `data` (vì cần chỗ cho `links`, `meta`).
- Thêm meta cấp ngoài cùng: method `with(Request $request): array` trong resource, hoặc
  `->additional(['meta' => [...]])` khi tạo.
- Đổi status hoặc header: `(new UserResource($user))->response()->setStatusCode(202)->header('X-A',
  'b')`, hoặc định nghĩa method `withResponse()` trong resource.
- Resource bọc một model vừa tạo trong request (`wasRecentlyCreated`) tự trả **201** thay vì 200 (theo
  `ResourceResponse::calculateStatus()`).

Laravel 13 còn có `JsonApiResource` (`make:resource PostResource --json-api`) sinh JSON theo đặc tả
[JSON:API](https://jsonapi.org/) (`type`, `id`, `attributes`, `relationships`, header `Content-Type:
application/vnd.api+json`). Chỉ cần khi team chọn theo chuẩn đó.

### 7.4 Cạm bẫy N+1 trong resource

```php
// Trong PostResource::toArray()
'author' => new UserResource($this->author),   // ⚠️ truy cập quan hệ chưa load
```

Trả 50 bài viết thì có 1 query lấy bài viết + 50 query lấy tác giả, gọi là *N+1 query*. Resource làm
lỗi này khó thấy vì truy vấn nằm rải rác trong `toArray()`.

Cách đúng: controller quyết định load gì (`Post::with('author')->paginate()`), resource chỉ hiển thị
cái đã load bằng `whenLoaded('author')`:

```php
'author' => new UserResource($this->whenLoaded('author')),
```

Quan hệ chưa load thì key `author` bị bỏ khỏi JSON, không phát sinh query. Chi tiết về eager loading và
cách phát hiện N+1 (`Model::preventLazyLoading()`) ở [Chương 27](27-laravel-database-eloquent.md).


## 8. Blade cơ bản

### 8.1 Blade là gì, chạy thế nào

*Blade* là *template engine* (bộ dựng HTML từ khuôn mẫu) của Laravel. File view đặt trong
`resources/views/`, đuôi `.blade.php`. `view('posts.show', [...])` tìm file
`resources/views/posts/show.blade.php` (dấu chấm thay cho dấu `/`).

Blade không phải trình thông dịch riêng: nó **biên dịch** (*compile*) file `.blade.php` thành file PHP
thuần, lưu vào `storage/framework/views/`, rồi `include` file PHP đó. Theo tài liệu Laravel, lần render
sau Blade chỉ biên dịch lại khi file gốc mới hơn bản đã biên dịch; trên production có thể biên dịch
trước tất cả bằng `php artisan view:cache` lúc deploy. Vì là PHP thuần sau biên dịch, OPcache cache
được, và Blade gần như không tốn thêm chi phí lúc chạy.

```
resources/views/hello.blade.php        storage/framework/views/<hash>.php
┌──────────────────────────────┐        ┌──────────────────────────────────────┐
│ <p>Xin chào {{ $name }}</p>  │ ─────> │ <p>Xin chào <?php echo e($name); ?></p>│
│ @if ($admin) ... @endif      │compile │ <?php if($admin): ?> ... <?php endif; ?>│
└──────────────────────────────┘        └──────────────────────────────────────┘
```

(Phần bên phải là minh hoạ đã rút gọn; mã biên dịch thật dài hơn một chút.)

### 8.2 `{{ }}` và `{!! !!}`: escaping và XSS

Đây là điều quan trọng nhất của Blade. Mã nguồn `CompilesEchos` cho thấy:

- `{{ $x }}` được biên dịch thành `<?php echo e($x); ?>`.
- `{!! $x !!}` được biên dịch thành `<?php echo $x; ?>`, in **nguyên văn**.

Helper `e()` (trong `Illuminate/Support/helpers.php`) về cơ bản là:

```php
htmlspecialchars($value ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8', $doubleEncode /* mặc định true */);
```

Nó đổi `<`, `>`, `&`, `"`, `'` thành *HTML entity*, nên dữ liệu người dùng nhập được hiển thị như chữ,
không bị trình duyệt hiểu thành thẻ HTML. Mô phỏng bằng PHP thuần:

```php
<?php
declare(strict_types=1);

// Bản rút gọn của helper e() mà Blade dùng cho {{ }}
function e(?string $value): string
{
    return htmlspecialchars($value ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

$name = '<script>alert("xss")</script>';
echo '<p>' . e($name) . '</p>', PHP_EOL;   // như {{ $name }}
// in ra: <p>&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;</p>
echo '<p>' . $name . '</p>', PHP_EOL;      // như {!! $name !!}
// in ra: <p><script>alert("xss")</script></p>   <- trình duyệt CHẠY script này

$title = "Tom's \"book\" & more";
echo '<input value="' . e($title) . '">', PHP_EOL;
// in ra: <input value="Tom&#039;s &quot;book&quot; &amp; more">

$url = 'javascript:alert(1)';
echo '<a href="' . e($url) . '">link</a>', PHP_EOL;
// in ra: <a href="javascript:alert(1)">link</a>   <- escape KHÔNG cứu được trường hợp này

echo e('&amp;'), PHP_EOL;
// in ra: &amp;amp;   (double encode: entity có sẵn bị mã hoá lần nữa)
```

Rút ra:

- Luôn dùng `{{ }}` cho dữ liệu có thể đến từ người dùng. `{!! !!}` chỉ dành cho HTML **bạn tin
  tuyệt đối** (HTML do chính code sinh ra, hoặc HTML người dùng nhập **đã qua** bộ lọc kiểu HTML
  Purifier).
- `ENT_QUOTES` làm cả dấu nháy đơn được mã hoá, nên `{{ }}` an toàn khi nằm trong giá trị thuộc tính
  HTML có bao nháy (`value="{{ $x }}"`).
- Escape HTML không giúp gì cho ngữ cảnh URL: `href="{{ $url }}"` với `$url = 'javascript:...'` vẫn là
  XSS khi người dùng bấm link. Kiểm scheme (`http`, `https`) khi validate (rule `url:http,https`).
- ⚠️ `e()` trả nguyên văn object implement `Htmlable` (ví dụ `Illuminate\Support\HtmlString`). Bọc input
  người dùng trong `new HtmlString(...)` là tự tắt escaping.
- ⚠️ Dữ liệu đưa vào JavaScript cần escape kiểu khác. Đừng viết `var name = '{{ $name }}';` hay
  `{!! json_encode($data) !!}` trong thẻ `<script>`. Dùng `{{ Js::from($data) }}`: theo tài liệu
  Laravel, nó sinh JSON đã escape đúng để nhúng vào HTML.

Chi tiết về XSS và các ngữ cảnh escape xem [Chương 17](17-bao-mat.md).

### 8.3 Directive điều khiển

```blade
@if ($posts->isEmpty())
    <p>Chưa có bài viết.</p>
@elseif ($posts->count() === 1)
    <p>Có một bài viết.</p>
@else
    <p>Có {{ $posts->count() }} bài viết.</p>
@endif

@forelse ($posts as $post)
    <li @class(['first' => $loop->first])>
        {{ $loop->iteration }}. {{ $post->title }}
    </li>
@empty
    <li>Danh sách trống.</li>   {{-- chạy khi $posts rỗng --}}
@endforelse

@auth  <a href="/logout">Đăng xuất</a>  @endauth
@guest <a href="/login">Đăng nhập</a>   @endguest

@include('partials.flash')       {{-- chèn view con, dùng chung biến của view cha --}}
```

`@forelse` giống `@foreach` nhưng có thêm nhánh `@empty` khi mảng rỗng. Trong vòng lặp có biến `$loop` với `index` (từ 0), `iteration` (từ 1),
`first`, `last`, `count`, `parent` (vòng lặp ngoài). `{{-- ... --}}` là comment Blade, không xuất ra
HTML (khác `<!-- -->` vẫn gửi xuống trình duyệt).

### 8.4 Layout bằng component

Mọi trang có chung `<head>`, menu, footer. Cách hiện đại là viết layout thành một *component*:

```blade
{{-- resources/views/components/layout.blade.php --}}
<!doctype html>
<html lang="vi">
<head>
    <meta charset="utf-8">
    <meta name="csrf-token" content="{{ csrf_token() }}">
    <title>{{ $title ?? 'Blog' }}</title>
</head>
<body>
    @include('partials.flash')
    <main>
        {{ $slot }}
    </main>
</body>
</html>
```

```blade
{{-- resources/views/posts/index.blade.php --}}
<x-layout>
    <x-slot:title>Danh sách bài viết</x-slot>

    @foreach ($posts as $post)
        <x-post-card :post="$post" class="mb-4" />
    @endforeach
</x-layout>
```

- `<x-layout>` tìm `resources/views/components/layout.blade.php`. Nội dung đặt giữa thẻ mở và đóng đi
  vào biến `$slot`; `<x-slot:title>` đi vào biến `$title` (*named slot*).
- `:post="$post"` (có dấu `:`) truyền **biểu thức PHP**; `class="mb-4"` (không có `:`) truyền chuỗi.

Component ẩn danh (*anonymous component*, chỉ có file view, không có class):

```blade
{{-- resources/views/components/post-card.blade.php --}}
@props(['post'])

<article {{ $attributes->merge(['class' => 'card']) }}>
    <h2>{{ $post->title }}</h2>
</article>
```

`@props` khai báo đâu là dữ liệu; các thuộc tính còn lại (như `class="mb-4"`) vào `$attributes` và được
gộp: kết quả là `class="card mb-4"`. Component có logic phức tạp thì tạo class bằng
`php artisan make:component`.

Cách cũ hơn, vẫn gặp nhiều trong project lâu năm, là *template inheritance*: layout có
`@yield('content')`, trang con viết `@extends('layouts.app')` và `@section('content') ... @endsection`.
Hai cách đều được hỗ trợ.

### 8.5 Form: `@csrf`, `@method`, `old()`, `@error`

```blade
<form method="POST" action="{{ route('posts.update', $post) }}">
    @csrf
    @method('PUT')

    <label for="title">Tiêu đề</label>
    <input id="title" name="title"
           value="{{ old('title', $post->title) }}"
           class="@error('title') is-invalid @enderror">
    @error('title')
        <div class="error">{{ $message }}</div>
    @enderror

    <button>Lưu</button>
</form>
```

- `@csrf` sinh `<input type="hidden" name="_token" value="...">`. Laravel 13 chống CSRF bằng middleware
  `PreventRequestForgery` trong nhóm `web`: trước tiên xem header `Sec-Fetch-Site` mà trình duyệt hiện
  đại gửi (chỉ qua HTTPS); không kết luận được thì so token. Token sai thì trả **419** (Page Expired).
  Nguyên lý CSRF ở [Chương 17](17-bao-mat.md).
- `@method('PUT')` sinh field ẩn `_method=PUT` (mục 1.3).
- `old('title', $post->title)`: nếu vừa bị trả về vì lỗi validation thì hiện giá trị người dùng đã gõ
  (flash trong session), không thì hiện giá trị hiện tại.
- `@error('title')` chỉ in khi field có lỗi, biến `$message` là thông báo đầu tiên.

## 9. Session và flash data trong Laravel

### 9.1 Session của Laravel khác session PHP thuần

HTTP không có trạng thái (*stateless*): mỗi request độc lập. *Session* là chỗ lưu dữ liệu của một
người dùng xuyên qua nhiều request, nhận diện bằng một *session ID* nằm trong cookie (xem
[Chương 15](15-php-va-web.md)).

Laravel **không** dùng `session_start()` và `$_SESSION` của PHP. Middleware `StartSession` (nhóm `web`)
tự làm toàn bộ:

```
 Request ──> StartSession: đọc session ID từ cookie, load dữ liệu từ driver vào bộ nhớ
                │
                ├─> controller đọc/ghi session (chỉ thay đổi trong bộ nhớ)
                │
           <── StartSession: lưu URL hiện tại, gắn cookie session vào response,
                             "lão hoá" flash data, GHI TOÀN BỘ session xuống driver
```

Cấu hình trong `config/session.php` và `.env`. Với project Laravel 13 mới:

| Biến `.env` | Mặc định | Ý nghĩa |
|---|---|---|
| `SESSION_DRIVER` | `database` | Nơi lưu: `file`, `cookie`, `database`, `redis`, `memcached`, `dynamodb`, `array` |
| `SESSION_LIFETIME` | `120` | Số phút không hoạt động trước khi hết hạn |
| `SESSION_ENCRYPT` | `false` | Mã hoá dữ liệu session khi lưu |
| `SESSION_HTTP_ONLY` | `true` | JavaScript không đọc được cookie session |
| `SESSION_SAME_SITE` | `lax` | Thuộc tính `SameSite` của cookie |

Driver `database` cần bảng `sessions` (có sẵn trong migration mặc định). Khi chạy nhiều server sau load
balancer, driver phải là nơi lưu dùng chung (`database`, `redis`), không phải `file` trên từng máy.
Driver `array` không lưu gì, chỉ dùng khi test. Route trong `routes/api.php` không có `StartSession`,
nên không có session.

### 9.2 Đọc, ghi, xoá

```php
$request->session()->put('cart_id', 42);
session(['locale' => 'vi']);                    // helper, mảng = ghi

$id = $request->session()->get('cart_id');
$lc = session('locale', 'en');                   // helper, chuỗi = đọc, kèm mặc định

$request->session()->has('cart_id');             // có và khác null
$request->session()->exists('cart_id');          // có (kể cả null)
$request->session()->pull('cart_id');            // đọc rồi xoá
$request->session()->push('recent.ids', 7);      // thêm vào mảng
$request->session()->increment('views');
$request->session()->forget('cart_id');
$request->session()->flush();                    // xoá hết dữ liệu

$request->session()->regenerate();               // đổi session ID, giữ dữ liệu
$request->session()->invalidate();               // đổi ID và xoá hết dữ liệu
```

`regenerate()` sau khi đăng nhập chống *session fixation* (kẻ tấn công cài trước một session ID cho
nạn nhân); starter kit của Laravel tự làm việc này. `invalidate()` dùng khi đăng xuất. Chi tiết ở
[Chương 28](28-laravel-auth.md).

### 9.3 Flash data: sống đúng một request kế tiếp

*Flash data* là dữ liệu chỉ tồn tại tới **hết request kế tiếp**. Dùng cho thông báo kiểu "Đã lưu!" sau
redirect, và chính là cách lỗi validation cùng input cũ đi từ request POST sang request GET (mục 3.3).

```php
$request->session()->flash('status', 'Đã lưu!');
return to_route('posts.index');
// hoặc gọn: return to_route('posts.index')->with('status', 'Đã lưu!');
```

```blade
{{-- resources/views/partials/flash.blade.php --}}
@if (session('status'))
    <div class="alert">{{ session('status') }}</div>
@endif
```

Cơ chế bên trong (`Illuminate\Session\Store`): session có hai danh sách key, `_flash.new` và
`_flash.old`. `flash()` ghi giá trị và thêm key vào `_flash.new`. Cuối **mỗi** request, khi lưu session,
`ageFlashData()` xoá các key trong `_flash.old`, rồi chuyển `_flash.new` thành `_flash.old`. Mô phỏng
bằng PHP thuần:

```php
<?php
declare(strict_types=1);

final class FakeSession
{
    /** @var array<string, mixed> */
    private array $data = ['_flash' => ['old' => [], 'new' => []]];

    public function put(string $key, mixed $value): void { $this->data[$key] = $value; }
    public function get(string $key): mixed { return $this->data[$key] ?? null; }

    public function flash(string $key, mixed $value): void
    {
        $this->put($key, $value);
        $this->data['_flash']['new'][] = $key;
    }

    // Gọi ở cuối mỗi request, ngay trước khi ghi session xuống storage
    public function ageFlashData(): void
    {
        foreach ($this->data['_flash']['old'] as $key) {
            unset($this->data[$key]);                                   // xoá flash của lần trước
        }
        $this->data['_flash']['old'] = $this->data['_flash']['new'];   // flash mới thành "cũ"
        $this->data['_flash']['new'] = [];
    }
}

$s = new FakeSession();

// Request 1: POST /posts -> lưu xong, flash rồi redirect
$s->flash('status', 'Đã lưu!');
echo 'R1 trong request: ', var_export($s->get('status'), true), PHP_EOL;
$s->ageFlashData();

// Request 2: GET /posts (trang đích của redirect)
echo 'R2 trong request: ', var_export($s->get('status'), true), PHP_EOL;
$s->ageFlashData();

// Request 3: người dùng F5
echo 'R3 trong request: ', var_export($s->get('status'), true), PHP_EOL;
// in ra:
// R1 trong request: 'Đã lưu!'
// R2 trong request: 'Đã lưu!'
// R3 trong request: NULL
```

Biến thể:

- `reflash()`: giữ **mọi** flash thêm một request nữa; `keep(['status'])`: chỉ giữ vài key.
- `now('status', '...')`: chỉ sống trong request hiện tại (đưa thẳng key vào `_flash.old`). Dùng khi trả
  view trực tiếp, không redirect.

⚠️ "Request kế tiếp" là request kế tiếp **cùng session**, bất kể là request nào. Nếu giữa redirect và
trang đích có một request AJAX khác (polling thông báo, một tab khác) chạy trước, request đó "tiêu" mất
flash và trang đích không hiện thông báo.

⚠️ `flash()` rồi trả view trực tiếp (không redirect): giá trị đọc được ngay trong request này nên
thông báo hiện ở trang hiện tại, rồi **hiện thêm lần nữa** ở trang kế tiếp người dùng mở (vì key vẫn
nằm trong `_flash.new`). Hoặc redirect, hoặc dùng `now()`.

### 9.4 Request đồng thời ghi đè session

Mặc định Laravel cho các request cùng session chạy song song, và mỗi request ghi lại **toàn bộ** dữ liệu
session lúc kết thúc. Hai request ghi hai key khác nhau vẫn có thể mất dữ liệu (*lost update*):

| Bước | Request A (`POST /cart/add`) | Request B (`POST /profile/theme`) | Session trong storage |
|---|---|---|---|
| 1 | Đọc session: `{cart: [1]}` | | `{cart: [1]}` |
| 2 | | Đọc session: `{cart: [1]}` | `{cart: [1]}` |
| 3 | Ghi trong bộ nhớ: `cart = [1, 2]` | Ghi trong bộ nhớ: `theme = dark` | `{cart: [1]}` |
| 4 | Kết thúc, lưu `{cart: [1,2]}` | | `{cart: [1,2]}` |
| 5 | | Kết thúc, lưu `{cart: [1], theme: dark}` | `{cart: [1], theme: dark}`: món 2 mất |

Laravel có *session blocking*: thêm `->block()` vào route (`Route::post(...)->block($lockSeconds = 10,
$waitSeconds = 10)`), các request cùng session tới những route có `block()` sẽ xếp hàng chờ khoá. Cần
cache driver hỗ trợ *atomic lock* (`redis`, `memcached`, `database`, `file`...) và không dùng được với
session driver `cookie`. Chờ quá thời gian thì ném `LockTimeoutException`. Dữ liệu quan trọng (giỏ hàng
thật) nên lưu vào DB với transaction thay vì session.

## 10. Exception và trang lỗi

### 10.1 Exception đi đâu khi không ai bắt

Mọi exception ném ra từ middleware, controller, view mà không bị bắt đều tới *exception handler*
(`Illuminate\Foundation\Exceptions\Handler`). Handler làm hai việc độc lập:

```
              throw $e
                 │
                 v
        ┌──────────────────┐
        │ Exception Handler │
        └──────────────────┘
          │              │
       report($e)     render($request, $e)
          │              │
   ghi log / gửi Sentry  biến thành HTTP response:
   (trừ loại "không cần  HTML (trang lỗi) hoặc JSON
    report")
```

- *Report*: ghi lại cho lập trình viên (log, Sentry, Flare...). Một số loại mặc định **không** report vì
  là lỗi "bình thường" của người dùng, không phải bug: theo `$internalDontReport` trong mã nguồn 13.x gồm
  `ValidationException`, `AuthenticationException`, `AuthorizationException`, `HttpException`,
  `ModelNotFoundException`, `TokenMismatchException`, `HttpResponseException`...
- *Render*: đổi thành response cho client.

Theo `prepareException()` và `render()` trong mã nguồn, trước khi render một số exception được đổi sang
HTTP exception tương ứng, một số khác (`AuthenticationException`, `ValidationException`) có nhánh xử lý
riêng:

| Exception | Status |
|---|---|
| `ModelNotFoundException` (`findOrFail`, route model binding không thấy) | 404 |
| `AuthorizationException` (`authorize()` false, policy từ chối) | 403 |
| `TokenMismatchException` (CSRF sai) | 419 |
| `AuthenticationException` (chưa đăng nhập) | 401 JSON, hoặc redirect tới trang login |
| `ValidationException` | 422 JSON, hoặc redirect kèm lỗi (mục 3.3) |
| `HttpException` (từ `abort()`) | status bạn chọn |
| Mọi exception khác | 500 |

### 10.2 `abort()` và HTTP exception

```php
abort(404);                                    // NotFoundHttpException
abort(403, 'Bạn không phải chủ bài viết.');    // HttpException kèm thông báo
abort_if($post->is_locked, 423);
abort_unless($user->isAdmin(), 403);
```

`abort()` ném exception, nên code phía sau không chạy, giống `return` nhưng dùng được ở bất cứ tầng nào.

### 10.3 `APP_DEBUG` và nội dung lỗi

- Response HTML: `APP_DEBUG=true` hiện trang lỗi chi tiết (stack trace, đoạn code, request). `false` thì
  hiện trang lỗi chung.
- Response JSON (`convertExceptionToArray()` trong mã nguồn): debug bật thì có `message`, `exception`,
  `file`, `line`, `trace`; debug tắt thì chỉ có `message`, và với lỗi không phải HTTP exception thì
  `message` luôn là `"Server Error"` (không lộ thông điệp nội bộ như lỗi SQL).

⚠️ Production luôn `APP_DEBUG=false`. Tài liệu Laravel cảnh báo bật debug trên production có nguy cơ lộ
giá trị cấu hình nhạy cảm cho người dùng.

### 10.4 Trang lỗi tuỳ biến

Tạo view `resources/views/errors/404.blade.php` là mọi lỗi 404 dùng trang này. Theo
`getHttpExceptionView()` trong mã nguồn, Laravel tìm view `errors::<status>`, không có thì tìm view dự
phòng theo nhóm `4xx` / `5xx` (`errors/4xx.blade.php`, `errors/5xx.blade.php`). Trong view có biến
`$exception`. Tài liệu Laravel lưu ý trang dự phòng không áp dụng cho `401, 402, 403, 404, 419, 429, 500,
503` vì Laravel đã có trang riêng cho các mã này; muốn đổi thì tạo từng file. Lấy bản mẫu của framework
để sửa: `php artisan vendor:publish --tag=laravel-errors`.

```blade
{{-- resources/views/errors/404.blade.php --}}
<x-layout>
    <x-slot:title>Không tìm thấy</x-slot>
    <h1>Trang bạn tìm không tồn tại</h1>
</x-layout>
```

⚠️ Trang lỗi nên đơn giản. Nếu trang lỗi tự nó ném exception (ví dụ truy vấn DB khi DB đang sập), mã
nguồn (`renderHttpException()`) cho thấy: khi debug tắt, Laravel report lỗi đó rồi rơi về trang lỗi
HTML tối giản do `HtmlErrorRenderer` của Symfony sinh; khi debug bật, exception đó được ném tiếp.

### 10.5 Cấu hình trong `bootstrap/app.php`

Từ Laravel 11, project mới không còn file `app/Exceptions/Handler.php`; cấu hình nằm trong
`withExceptions()`:

```php
use App\Exceptions\InsufficientStockException;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Http\Request;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

->withExceptions(function (Exceptions $exceptions): void {
    // Khi nào trả JSON (mặc định của skeleton 13.x)
    $exceptions->shouldRenderJsonWhen(
        fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
    );

    // Không ghi log loại exception này
    $exceptions->dontReport([InsufficientStockException::class]);

    // Đổi response của một loại exception. Loại được suy ra từ type-hint tham số đầu.
    $exceptions->render(function (InsufficientStockException $e, Request $request) {
        return response()->json(['message' => $e->getMessage()], 409);
    });

    // Closure không trả gì (null) thì Laravel dùng cách render mặc định
    $exceptions->render(function (NotFoundHttpException $e, Request $request) {
        if ($request->is('api/*')) {
            return response()->json(['message' => 'Không tìm thấy.'], 404);
        }
    });

    // Thêm ngữ cảnh vào mọi log exception
    $exceptions->context(fn (): array => ['app_region' => 'ap-southeast-1']);
})
```

Exception tự định nghĩa có thể tự mang method `render(Request $request)` và `report()`; handler gọi
chúng trước tiên (xem thứ tự trong `Handler::render()`). Cách này gom logic về một chỗ:

```php
<?php
declare(strict_types=1);

namespace App\Exceptions;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use RuntimeException;

final class InsufficientStockException extends RuntimeException
{
    public function __construct(public readonly int $productId, public readonly int $available)
    {
        parent::__construct("Sản phẩm {$productId} chỉ còn {$available}.");
    }

    public function render(Request $request): JsonResponse
    {
        return response()->json([
            'message'   => $this->getMessage(),
            'available' => $this->available,
        ], 409);
    }
}
```

Helper `report($e)` ghi log một exception đã bắt mà **vẫn chạy tiếp** request: dùng khi bạn xử lý được
lỗi (trả giá trị dự phòng) nhưng muốn để lại dấu vết. Báo cáo lỗi, log level, throttle báo cáo xem tài
liệu Error Handling; nguyên lý exception trong PHP xem [Chương 12](12-loi-exception.md).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Gọi API, validation sai mà nhận 302 rồi HTML trang chủ | Request không "expectsJson" (thiếu `Accept: application/json`), route không nằm dưới `api/` | Client gửi `Accept: application/json`; server cấu hình `shouldRenderJsonWhen` |
| Gửi JSON mà `input()` rỗng | Thiếu `Content-Type: application/json` | Client đặt đúng `Content-Type` |
| Field tuỳ chọn bỏ trống báo "must be a valid date" | `ConvertEmptyStringsToNull` đổi `""` thành `null`, rule vẫn chạy với `null` | Thêm `nullable` |
| `['date']` tưởng là bắt buộc | Rule thường không chạy khi field vắng mặt | Thêm `required` |
| `max:150` cho tuổi nhưng `"200"` vẫn qua | Thiếu `integer`/`numeric` nên đo độ dài chuỗi | `['integer', 'min:0', 'max:150']` |
| `Model::create($request->all())` | `all()` chứa cả field không validate (`is_admin`) | Dùng `validated()` / `safe()` |
| `'meta' => 'array'` làm lọt khoá lạ | `validated()` trả cả mảng con | `array:key1,key2` |
| Form Request mới tạo luôn trả 403 | Stub sinh `authorize()` trả `false` | Sửa thành logic thật hoặc `true` |
| Hai user đăng ký cùng email dù có rule `unique` | Race condition giữa SELECT và INSERT | Unique index trong DB, bắt `UniqueConstraintViolationException` |
| `{!! $comment->body !!}` | Tắt escaping, XSS | `{{ }}`, hoặc lọc HTML trước khi dùng `{!! !!}` |
| `var x = '{{ $x }}'` trong `<script>` | Escape HTML không đúng cho ngữ cảnh JS | `{{ Js::from($x) }}` |
| Thông báo flash bị mất, hoặc hiện hai lần | Flash sống tới hết request kế tiếp cùng session, bất kể request nào | Flash rồi redirect; trả view trực tiếp thì dùng `now()` |
| Form POST bị 419 | Thiếu `@csrf` hoặc session hết hạn | `@csrf` trong mọi form; xử lý 419 thân thiện |
| Trả model thẳng ra API lộ cột mới | JSON phụ thuộc schema | API Resource liệt kê rõ field |
| Resource gây N+1 | Truy cập quan hệ chưa load trong `toArray()` | Eager load ở controller + `whenLoaded()` |
| `download(storage_path($request->input('f')))` | Path traversal | Chỉ dùng đường dẫn lưu trong DB / kiểm `realpath()` |
| Production lộ stack trace | `APP_DEBUG=true` | `APP_DEBUG=false` |

## Tóm tắt chương

- `Illuminate\Http\Request` gói mọi dữ liệu request. `input()` gộp body và query (body thắng), đọc JSON
  khi `Content-Type` là JSON. Các hàm `integer()`, `boolean()` chỉ ép kiểu, không kiểm tra.
- `TrimStrings` và `ConvertEmptyStringsToNull` làm ô trống thành `null`; vì vậy field tuỳ chọn cần
  `nullable`.
- Validation sai ném `ValidationException`. Handler trả redirect kèm lỗi và input cũ qua session flash,
  hoặc JSON 422 `{message, errors}` khi request mong JSON (`expectsJson()`, hoặc `api/*` theo skeleton 13).
- Rule thường không chạy khi field vắng mặt hoặc là chuỗi rỗng; `required`, `nullable`, `sometimes`
  quyết định field bắt buộc, cho phép null, hay chỉ kiểm khi có mặt. `min`/`max` đo theo kiểu dữ liệu.
- Rule tự viết bằng closure hoặc class `ValidationRule` (gọi `$fail`). `unique`/`exists` không thay được
  ràng buộc trong DB.
- Form Request chạy `prepareForValidation` → `authorize` (403) → rules + `after` (422/redirect) →
  `passedValidation`, trước khi vào controller. Luôn lấy dữ liệu bằng `validated()`.
- Controller trả chuỗi thành HTML, mảng/model thành JSON (model vừa tạo thành 201). `response()` cho
  status, header, cookie (phút), JSON, download, stream; redirect sau POST (PRG).
- API Resource tách hợp đồng API khỏi schema DB; bọc `data`, phân trang có `links`/`meta`; dùng
  `whenLoaded` tránh N+1.
- Blade biên dịch ra PHP; `{{ }}` qua `htmlspecialchars` (an toàn cho HTML), `{!! !!}` in nguyên văn.
- Session Laravel tự quản (không dùng `$_SESSION`), ghi toàn bộ lúc cuối request; flash sống tới hết
  request kế tiếp. Exception được report và render theo cấu hình trong `withExceptions()`.

## Câu hỏi tự kiểm tra

1. Client gửi `POST /orders?page=1` với body form `page=2`. `$request->input('page')` và
   `$request->query('page')` trả gì? Vì sao? (mục 2.1)
2. Cùng một lỗi validation, khi nào Laravel trả 302, khi nào trả 422? Liệt kê những gì quyết định điều
   đó trong project Laravel 13 mới tạo. (mục 1.5, 3.3)
3. Với rule `['email']`, request không gửi key `email` thì sao? Gửi `email=` thì sao? Giải thích bằng cơ
   chế của validator và middleware. (mục 2.3, 3.5)
4. `'qty' => ['max:10']` và `'qty' => ['integer', 'max:10']` khác nhau thế nào khi client gửi `"25"`?
5. Trong Form Request, `prepareForValidation()` chạy trước hay sau `authorize()`? Hệ quả thực tế là gì?
   (mục 5.3)
6. Vì sao đã có rule `unique:users,email` mà vẫn cần unique index? Vẽ timeline hai request. (mục 4.7)
7. `{{ $x }}` biên dịch thành gì? Nêu hai trường hợp `{{ }}` không đủ để chống XSS. (mục 8.2)
8. Flash data bị xoá vào thời điểm nào? Vì sao một request AJAX chen giữa làm mất thông báo? (mục 9.3)
9. `ModelNotFoundException` biến thành status nào, và có bị ghi log không? (mục 10.1)
10. Khi nào nên trả API Resource thay vì trả thẳng model? `whenLoaded()` giải quyết vấn đề gì? (mục 7)

## Bài tập

1. **Form đăng ký sự kiện (web).** Trong một project Laravel 13, làm trang `GET /events/{event}/register`
   có form (họ tên, email, số điện thoại, số vé 1–5, ghi chú tuỳ chọn) và route `POST` xử lý. Dùng Form
   Request với rule tự viết kiểm số điện thoại Việt Nam, hiện lỗi bằng `@error`, giữ lại input bằng
   `old()`, thành công thì redirect kèm flash "Đăng ký thành công". Thử: bỏ trống ghi chú, nhập số vé
   `"abc"`, nhập `<script>` vào họ tên rồi xem trang hiển thị lại.
2. **API tạo đơn hàng.** Viết `POST /api/orders` nhận JSON có mảng `items` (`product_id`, `qty`), giới hạn
   tối đa 20 dòng, không trùng sản phẩm, kiểm tra tồn kho trong `after()`. Trả `OrderResource` với status
   201. Gọi bằng `curl` trong ba trường hợp: thiếu `Accept`, sai dữ liệu, đúng dữ liệu; ghi lại status
   và body mỗi lần.
3. **Validator mini bằng PHP thuần.** Không dùng Laravel, viết một hàm `validate(array $data, array
   $rules): array` hỗ trợ `required`, `nullable`, `integer`, `max:N` (đo theo kiểu như Laravel) và rule
   object có callback `$fail`, tuân theo luật "rule thường không chạy khi field vắng mặt hoặc chuỗi
   rỗng". Viết đủ ví dụ để tái hiện bảng ở mục 3.5 và in kết quả.
4. **Xuất CSV lớn.** Viết route `GET /admin/users/export` stream file CSV toàn bộ user bằng
   `streamDownload` + `lazy()`. Đo bộ nhớ đỉnh (`memory_get_peak_usage(true)` ghi vào log ở cuối
   closure) với 10.000 và 100.000 user (tạo bằng factory), so với cách gom cả file vào một chuỗi.

## Đọc thêm

- [Laravel 13.x: HTTP Requests](https://laravel.com/docs/13.x/requests)
- [Laravel 13.x: Validation](https://laravel.com/docs/13.x/validation)
- [Laravel 13.x: HTTP Responses](https://laravel.com/docs/13.x/responses)
- [Laravel 13.x: Eloquent API Resources](https://laravel.com/docs/13.x/eloquent-resources)
- [Laravel 13.x: Blade Templates](https://laravel.com/docs/13.x/blade) và [Views](https://laravel.com/docs/13.x/views)
- [Laravel 13.x: HTTP Session](https://laravel.com/docs/13.x/session)
- [Laravel 13.x: CSRF Protection](https://laravel.com/docs/13.x/csrf)
- [Laravel 13.x: Error Handling](https://laravel.com/docs/13.x/errors)
- Mã nguồn `laravel/framework` nhánh 13.x: [`Http/Request.php`, `Http/Concerns/InteractsWithInput.php`](https://github.com/laravel/framework/tree/13.x/src/Illuminate/Http),
  [`Foundation/Http/FormRequest.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Http/FormRequest.php),
  [`Validation/Validator.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Validation/Validator.php),
  [`Foundation/Exceptions/Handler.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Exceptions/Handler.php),
  [`Session/Store.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Session/Store.php)
- [PHP: htmlspecialchars](https://www.php.net/manual/en/function.htmlspecialchars.php) ·
  [PHP: json_encode](https://www.php.net/manual/en/function.json-encode.php)
- [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) (mục 15.5.21: 422 Unprocessable Content)
- [OWASP: Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
