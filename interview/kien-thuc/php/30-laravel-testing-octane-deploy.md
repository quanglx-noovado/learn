# Chương 30. Laravel: kiểm thử, Octane và triển khai

> [← Mục lục](README.md) · [← Chương 29: Queue, event, scheduler, cache, mail và notification](29-laravel-queue-event-schedule-cache.md) · (chương cuối)

**Bạn sẽ học được:**

- Viết *feature test* cho ứng dụng Laravel: gửi request giả lập, kiểm response, JSON, validation,
  đăng nhập.
- Giữ database sạch giữa các test bằng `RefreshDatabase`, và hiểu nó làm gì bên trong (transaction
  bọc quanh mỗi test).
- Dùng các *fake* của Laravel (`Queue`, `Bus`, `Event`, `Mail`, `Http`, thời gian) để test mà không gửi
  mail thật, không gọi API thật; viết cùng test đó bằng Pest.
- Hiểu Laravel Octane: vì sao nhanh hơn PHP-FPM, ba server FrankenPHP, RoadRunner, Swoole, và loại lỗi
  mới mà nó mang tới (rò trạng thái giữa các request).
- Triển khai lên production: `optimize`, migration an toàn, queue worker với Supervisor,
  `php artisan reload`, zero-downtime deploy, health check.
- Biết các công cụ quan sát hệ thống (*observability*): log, Telescope, Pulse, Nightwatch.

**Cần biết trước:** [Chương 21: Chất lượng code](21-chat-luong-code.md) (PHPUnit, Pest, test double),
[Chương 18: PHP-FPM, Nginx và OPcache](18-fpm-nginx-opcache.md) (mô hình FPM, deploy bằng symlink),
[Chương 26: Service container](26-laravel-container-provider-facade.md) (singleton, scoped, facade),
[Chương 27: Database trong Laravel](27-laravel-database-eloquent.md) (migration, factory, transaction),
[Chương 29: Queue, event...](29-laravel-queue-event-schedule-cache.md) (job, event, mail, worker).

**Về các ví dụ trong chương.** Có hai loại:

- Ví dụ **PHP thuần** (mô phỏng cơ chế bên trong) là file hoàn chỉnh, đã chạy thật trên PHP 8.5, output
  ghi trong comment. Chạy bằng `php ten-file.php`, hoặc không cần cài:
  `docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php`.
- Ví dụ **Laravel** (test, config) cần một project Laravel 13 (tạo bằng `laravel new demo` hoặc
  `composer create-project laravel/laravel demo`, xem [Chương 23](23-laravel-gioi-thieu.md)). Các ví dụ
  này viết theo tài liệu chính thức Laravel 13.x; khi ghi output thì đó là output minh hoạ.

---

## 1. Kiểm thử ứng dụng Laravel: bức tranh chung

### 1.1 Nhắc lại: test là gì, vì sao Laravel cần loại test riêng

*Test tự động* (*automated test*) là code kiểm tra code: chạy một đoạn chương trình với input cụ thể
rồi tự so kết quả với mong đợi. Chương 21 đã dạy phần nền chung cho mọi project PHP: PHPUnit,
assertion, data provider, Pest, test double (stub, mock, fake), và các loại test (unit, integration,
feature, end-to-end). Chương này chỉ bàn phần **riêng của Laravel**.

Vì sao cần phần riêng? Một tính năng web điển hình đi qua rất nhiều tầng:

```
 request HTTP
     │
     ▼
 routing ─► middleware (auth, CSRF, throttle) ─► controller ─► validation ─► model ─► database
                                                     │
                                                     ├─► dispatch job vào queue
                                                     ├─► bắn event
                                                     ├─► gửi mail
                                                     └─► gọi API bên ngoài (cổng thanh toán)
```

Unit test thuần (gọi thẳng một hàm) không bắt được lỗi ở chỗ các tầng ghép với nhau: quên middleware
`auth`, sai tên route, validation thiếu rule, quên dispatch job. Laravel cung cấp công cụ để:

1. Gửi một request HTTP **giả lập** vào ứng dụng và kiểm response (mục 2).
2. Cho mỗi test một database sạch (mục 3).
3. Thay những thứ "chạm ra thế giới bên ngoài" (queue, mail, API, đồng hồ) bằng đồ giả để test nhanh,
   ổn định và kiểm được "đã gửi chưa" (mục 4).

### 1.2 Thư mục `tests/`: Unit và Feature

Một project Laravel mới có sẵn:

```
tests/
├── TestCase.php            # class cha cho feature test (kế thừa TestCase của Laravel)
├── Feature/
│   └── ExampleTest.php     # test có khởi động ứng dụng
└── Unit/
    └── ExampleTest.php     # test KHÔNG khởi động ứng dụng
phpunit.xml                 # cấu hình PHPUnit (và Pest dùng chung)
```

Hai loại khác nhau ở chỗ **có khởi động (*boot*) ứng dụng Laravel hay không**:

| | `tests/Unit` | `tests/Feature` |
|---|---|---|
| Kế thừa | `PHPUnit\Framework\TestCase` | `Tests\TestCase` (kế thừa `Illuminate\Foundation\Testing\TestCase`) |
| Khởi động app | Không | Có, **lại từ đầu cho mỗi method test** |
| Dùng được DB, facade, `config()`, route | Không | Có |
| Tốc độ | Rất nhanh | Chậm hơn (phải boot app) |
| Dùng cho | Logic thuần: tính giá, parse chuỗi, value object | Một tính năng qua nhiều tầng |

Tài liệu Laravel khuyên: phần lớn test nên là feature test, vì chúng cho nhiều tự tin nhất rằng hệ
thống chạy đúng như một tổng thể.

File `tests/TestCase.php` của skeleton Laravel 13.x chỉ có:

```php
<?php

namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;

abstract class TestCase extends BaseTestCase
{
    //
}
```

Mọi tiện ích (`$this->get()`, `actingAs()`, `assertDatabaseHas()`...) đến từ class cha của Laravel.

⚠️ Nếu bạn tự viết `setUp()` hoặc `tearDown()` trong test class, phải gọi `parent::setUp()` ở **đầu**
`setUp()` và `parent::tearDown()` ở **cuối** `tearDown()`. Quên `parent::setUp()` thì ứng dụng không
được boot (`$this->app` là `null`), và lỗi hiện ra rất khó hiểu, thường ở dòng gọi facade hoặc
`$this->get()` chứ không ở chỗ bạn quên.

Laravel 13.x còn có attribute `#[UnitTest]` (namespace `Illuminate\Foundation\Testing\Attributes`) đặt
lên một method trong feature test để method đó **không** boot ứng dụng, khi bạn muốn để test thuần cạnh
các test cùng chủ đề.

### 1.3 `phpunit.xml` và môi trường `testing`

Khi chạy test, Laravel tự đặt môi trường là `testing` nhờ các biến khai báo trong `phpunit.xml`. Đây là
phần `<php>` của `phpunit.xml` trong skeleton Laravel 13.x:

```xml
<php>
    <env name="APP_ENV" value="testing"/>
    <env name="APP_MAINTENANCE_DRIVER" value="file"/>
    <env name="BCRYPT_ROUNDS" value="4"/>
    <env name="BROADCAST_CONNECTION" value="null"/>
    <env name="CACHE_STORE" value="array"/>
    <env name="DB_CONNECTION" value="sqlite"/>
    <env name="DB_DATABASE" value=":memory:"/>
    <env name="DB_URL" value=""/>
    <env name="MAIL_MAILER" value="array"/>
    <env name="QUEUE_CONNECTION" value="sync"/>
    <env name="SESSION_DRIVER" value="array"/>
    <env name="PULSE_ENABLED" value="false"/>
    <env name="TELESCOPE_ENABLED" value="false"/>
    <env name="NIGHTWATCH_ENABLED" value="false"/>
</php>
```

Đọc từng dòng để hiểu "môi trường test" khác production thế nào:

| Biến | Giá trị | Ý nghĩa |
|---|---|---|
| `BCRYPT_ROUNDS` | `4` | Băm mật khẩu với cost thấp nhất cho nhanh. Test tạo nhiều user, bcrypt cost cao làm bộ test chậm hẳn |
| `CACHE_STORE`, `SESSION_DRIVER` | `array` | Cache và session chỉ nằm trong bộ nhớ, mất khi test kết thúc |
| `DB_CONNECTION`, `DB_DATABASE` | `sqlite`, `:memory:` | Database SQLite trong RAM, không cần server |
| `MAIL_MAILER` | `array` | Mail không gửi đi đâu, chỉ giữ trong bộ nhớ |
| `QUEUE_CONNECTION` | `sync` | Job được chạy **ngay lập tức, đồng bộ** khi dispatch, không vào hàng đợi |
| `PULSE_ENABLED`, `TELESCOPE_ENABLED`, `NIGHTWATCH_ENABLED` | `false` | Tắt công cụ giám sát (mục 8) trong test |

⚠️ Hai hệ quả hay gây bất ngờ:

- `QUEUE_CONNECTION=sync` nghĩa là nếu bạn không fake queue, job **chạy thật** ngay trong test (gọi API,
  gửi mail...). Đó là lý do mục 4 quan trọng.
- `DB_CONNECTION=sqlite` nghĩa là test chạy trên **SQLite** trong khi production thường là MySQL. Hai
  engine khác nhau ở nhiều chỗ (mục 3.7).

Bạn có thể thêm biến khác vào `phpunit.xml`, hoặc tạo file `.env.testing` ở gốc project: file này được
dùng **thay cho** `.env` khi chạy test (và khi chạy lệnh Artisan với `--env=testing`).

⚠️ Nếu từng chạy `php artisan config:cache` ở máy dev, config đã cache sẽ thắng mọi biến trong
`phpunit.xml`, và test có thể chạy vào **database thật của bạn**. Tài liệu Laravel nhắc: xoá config cache
bằng `php artisan config:clear` trước khi chạy test. Script `composer test` của skeleton làm sẵn việc
này (`config:clear` rồi `artisan test`).

### 1.4 Tạo và chạy test

```bash
# Chạy trong thư mục gốc project Laravel
php artisan make:test OrderTest          # tạo tests/Feature/OrderTest.php
php artisan make:test PriceTest --unit   # tạo tests/Unit/PriceTest.php

php artisan test                         # chạy toàn bộ, output dễ đọc
./vendor/bin/phpunit                     # hoặc gọi thẳng PHPUnit
./vendor/bin/pest                        # hoặc Pest, nếu project dùng Pest

php artisan test --filter=OrderTest      # chỉ chạy test khớp tên
php artisan test --testsuite=Feature --stop-on-failure
```

`php artisan test` nhận mọi tham số của PHPUnit/Pest. Thêm vài tham số riêng hữu ích:

| Lệnh | Tác dụng |
|---|---|
| `php artisan test --parallel` | Chạy song song nhiều process (cần `composer require brianium/paratest --dev`). Mặc định số process bằng số nhân CPU; đổi bằng `--processes=4` |
| `php artisan test --coverage` | Báo cáo độ phủ code (cần Xdebug hoặc PCOV) |
| `php artisan test --coverage --min=80` | Cho fail nếu độ phủ dưới 80% |
| `php artisan test --profile` | Liệt kê 10 test chậm nhất |

Khi chạy song song, Laravel tự tạo một database test riêng cho mỗi process, thêm hậu tố là "token" của
process (ví dụ `your_db_test_1`, `your_db_test_2`), nên các process không giẫm lên dữ liệu của nhau.

---

## 2. HTTP test: gửi request giả lập vào ứng dụng

### 2.1 Request "giả" nhưng đi qua đúng mọi tầng

Trong feature test, `$this->get('/')`, `$this->post(...)`... **không** mở kết nối mạng và không cần web
server. Laravel dựng một object `Request` trong bộ nhớ rồi đưa thẳng cho HTTP kernel, giống hệt cách
`public/index.php` làm với request thật:

```
   test method                       cùng một process PHP
 ┌──────────────┐   Request object   ┌──────────────────────────────────────────────┐
 │ $this->post( │ ─────────────────► │ HTTP Kernel ─► middleware ─► route ─► controller │
 │  '/orders',  │                    │                                    │          │
 │  [...])      │ ◄───────────────── │ ◄──────────── Response ◄─────────────┘          │
 └──────────────┘   TestResponse     └──────────────────────────────────────────────┘
        │
        ▼
  $response->assertStatus(201) ...
```

Kết quả trả về là `Illuminate\Testing\TestResponse`: bọc response thật và thêm hàng chục method
`assert...`. Vì đi qua đúng kernel, test bắt được lỗi ở routing, middleware, validation, phân quyền.

Hai điều cần biết ngay:

- Middleware chống CSRF ([Chương 17](17-bao-mat.md)) **tự động tắt** khi chạy test, nên `post()` không
  cần token.
- Tài liệu Laravel khuyên mỗi test chỉ gửi **một** request; gửi nhiều request trong một method test có
  thể cho kết quả bất ngờ. Tài liệu không nói lý do; đọc mã nguồn (`MakesHttpRequests::call()`) thì
  thấy một nguyên nhân: mọi request trong cùng một method test đều đi qua cùng một instance ứng dụng
  (`$this->app`, tạo trong `setUp()`), nên object đã resolve và trạng thái request trước để lại vẫn
  còn, khác với production nơi mỗi request PHP-FPM bắt đầu từ trạng thái mới.

### 2.2 Ví dụ đầu tiên: tạo đơn hàng

Giả sử ứng dụng có bảng `orders` (cột `user_id`, `product`, `quantity`) và model `Order`, cùng route và
controller sau:

```php
// routes/web.php
use App\Http\Controllers\OrderController;
use Illuminate\Support\Facades\Route;

Route::post('/orders', [OrderController::class, 'store'])->middleware('auth');
```

```php
// app/Http/Controllers/OrderController.php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Order;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

final class OrderController extends Controller
{
    public function store(Request $request): JsonResponse
    {
        $data = $request->validate([
            'product'  => ['required', 'string', 'max:100'],
            'quantity' => ['required', 'integer', 'min:1'],
        ]);

        $order = Order::create([
            ...$data,
            'user_id' => $request->user()->id,
        ]);

        return response()->json(['id' => $order->id, 'product' => $order->product], 201);
    }
}
```

Test (tạo bằng `php artisan make:test OrderTest`):

```php
// tests/Feature/OrderTest.php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

final class OrderTest extends TestCase
{
    use RefreshDatabase;   // database sạch cho mỗi test (mục 3)

    public function test_khach_chua_dang_nhap_khong_tao_duoc_don(): void
    {
        $response = $this->postJson('/orders', ['product' => 'Bút', 'quantity' => 2]);

        $response->assertUnauthorized();          // 401
        $this->assertDatabaseCount('orders', 0);
    }

    public function test_user_tao_duoc_don(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)
            ->postJson('/orders', ['product' => 'Bút', 'quantity' => 2]);

        $response->assertCreated()                // 201
            ->assertJsonPath('product', 'Bút');

        $this->assertDatabaseHas('orders', [
            'user_id'  => $user->id,
            'product'  => 'Bút',
            'quantity' => 2,
        ]);
    }

    public function test_so_luong_phai_duong(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)
            ->postJson('/orders', ['product' => 'Bút', 'quantity' => 0]);

        $response->assertUnprocessable()          // 422
            ->assertInvalid(['quantity']);
        $this->assertDatabaseCount('orders', 0);
    }
}
```

Chạy `php artisan test --filter=OrderTest`. Output minh hoạ:

```
   PASS  Tests\Feature\OrderTest
  ✓ khach chua dang nhap khong tao duoc don
  ✓ user tao duoc don
  ✓ so luong phai duong

  Tests:    3 passed
```

Vài điểm đáng chú ý:

- Mỗi test theo khuôn *Arrange, Act, Assert* ([Chương 21](21-chat-luong-code.md)): chuẩn bị dữ liệu
  (factory), gửi đúng một request, rồi kiểm response **và** tác dụng phụ (dòng trong database).
- Test thứ nhất dùng `postJson` chứ không phải `post`. Với `post` (request kiểu form), khi chưa đăng
  nhập Laravel sẽ **redirect** về route tên `login` thay vì trả 401, vì nó quyết định dạng lỗi theo việc
  request có "mong đợi JSON" hay không ([Chương 25](25-laravel-request-validation-response.md)).
- Ví dụ giả định model `Order` đã khai báo `$fillable` cho ba cột trên
  ([Chương 27](27-laravel-database-eloquent.md)).
- Kiểm cả trường hợp **thất bại** (chưa đăng nhập, dữ liệu sai). Lỗi bảo mật thường nằm ở đây.

### 2.3 Gửi kèm header, cookie, session, đăng nhập

```php
$this->withHeaders(['X-Request-Id' => 'abc'])->get('/');
$this->withCookie('color', 'blue')->get('/');
$this->withSession(['banned' => false])->get('/');

$this->actingAs($user)->get('/dashboard');          // đăng nhập user này cho request
$this->actingAs($user, 'api')->getJson('/api/me');  // chỉ định guard; guard đó thành mặc định trong test
$this->actingAsGuest()->get('/dashboard');          // chắc chắn là khách
```

`actingAs()` không đi qua form login. Nó đặt user vào guard ([Chương 28](28-laravel-auth.md)), nên test
nhanh và không phụ thuộc trang login. Muốn test chính luồng login thì gửi `post('/login', [...])` thật.

Các assertion về đăng nhập: `$this->assertAuthenticated()`, `$this->assertGuest()`,
`$this->assertAuthenticatedAs($user)`.

Khi một test đỏ mà không hiểu vì sao, in response ra xem:

```php
$response->dump();          // in body, test chạy tiếp
$response->dumpHeaders();
$response->dumpSession();
$response->dd();            // in rồi dừng hẳn
```

### 2.4 Kiểm JSON

Với API, `getJson`, `postJson`, `putJson`, `patchJson`, `deleteJson` gửi body JSON và header
`Accept: application/json`. Các assertion chính:

| Assertion | Pass khi |
|---|---|
| `assertJson([...])` | Mảng truyền vào **có mặt** trong JSON (JSON được phép có thêm key khác) |
| `assertExactJson([...])` | JSON **đúng bằng** mảng truyền vào |
| `assertJsonPath('team.owner.name', 'Darian')` | Giá trị tại đường dẫn (dấu chấm) bằng giá trị cho trước |
| `assertJsonCount(3, 'data')` | Mảng tại `data` có 3 phần tử |
| `assertJsonStructure(['id', 'name'])` | Có đủ các key (không quan tâm giá trị) |
| `assertJsonMissingPath('password')` | Không có key đó |

⚠️ `assertJson()` chỉ kiểm "có chứa", nên một API vô tình trả thêm `password` hay `api_token` vẫn pass.
Laravel có cách viết chặt hơn: truyền closure, dùng `AssertableJson`:

```php
use Illuminate\Testing\Fluent\AssertableJson;

$this->getJson('/users/1')
    ->assertJson(fn (AssertableJson $json) =>
        $json->where('id', 1)
            ->where('name', 'Victoria Faith')
            ->missing('password')
            ->etc()
    );
```

Ở cách viết này, nếu **không** gọi `etc()` thì test fail khi JSON có key nào bạn chưa kiểm. Thiết kế đó
cố ý: buộc bạn hoặc kiểm từng key, hoặc ghi rõ "cho phép có thêm" bằng `etc()`, để tránh lộ dữ liệu nhạy
cảm. Lưu ý `etc()` chỉ có tác dụng ở **đúng cấp lồng** nơi nó được gọi, không kiểm các object lồng bên
trong.

Với danh sách: `$json->has(3)->first(fn (AssertableJson $json) => ...)` kiểm phần tử đầu,
`->each(fn (AssertableJson $json) => $json->whereType('id', 'integer')->etc())` kiểm mọi phần tử.

### 2.5 Kiểm validation

```php
$response->assertValid();                      // không có lỗi validation nào
$response->assertValid(['name', 'email']);     // hai field này không lỗi
$response->assertInvalid(['email']);           // field email có lỗi
$response->assertInvalid([
    'email' => 'valid email address',          // chỉ cần một phần câu báo lỗi
]);
$response->assertOnlyInvalid(['name', 'email']); // chỉ đúng hai field này lỗi
```

`assertValid`/`assertInvalid` dùng được cho cả hai kiểu Laravel báo lỗi validation: JSON (status 422,
với request JSON) và *flash* vào session rồi redirect (với form HTML). Nhờ vậy bạn không cần nhớ
`assertJsonValidationErrors` hay `assertSessionHasErrors` cho từng trường hợp.

### 2.6 Khi ứng dụng ném exception

Mặc định, exception trong request được exception handler chuyển thành response (ví dụ 500). Trong test,
điều này đôi khi che mất nguyên nhân: bạn chỉ thấy "mong 201, nhận 500". Hai công cụ:

```php
// 1) Tắt xử lý exception: exception bay thẳng ra test, kèm stack trace đầy đủ
$response = $this->withoutExceptionHandling()->get('/');

// 2) Fake exception handler, rồi kiểm exception nào đã được report
use Illuminate\Support\Facades\Exceptions;

Exceptions::fake();
$this->get('/order/1');
Exceptions::assertReported(InvalidOrderException::class);
Exceptions::assertNothingReported();   // hoặc: không có exception nào
```

Kiểm một đoạn code (không phải request) có ném exception không:

```php
$this->assertThrows(fn () => (new ProcessOrder)->execute(), OrderInvalid::class);
```

---

## 3. Database trong test

### 3.1 Vấn đề: test làm bẩn dữ liệu của nhau

Test A tạo user `a@example.com`. Test B cũng tạo user `a@example.com` và gặp lỗi UNIQUE, nhưng chỉ khi
chạy sau A. Chạy riêng B thì xanh. Đây là kiểu *flaky test* kinh điển
([Chương 21](21-chat-luong-code.md)): kết quả phụ thuộc thứ tự chạy, vì các test **dùng chung trạng
thái** là database.

Nguyên tắc: mỗi test phải bắt đầu từ một database đã biết trước (thường là rỗng, có đủ bảng), và không
để lại gì cho test sau. Có ba cách làm, từ chậm tới nhanh:

| Cách | Làm gì sau/trước mỗi test | Tốc độ |
|---|---|---|
| Chạy lại toàn bộ migration | Xoá mọi bảng rồi tạo lại | Chậm nhất |
| Truncate | Xoá sạch dữ liệu mọi bảng, giữ cấu trúc | Trung bình |
| Transaction rồi rollback | Mở transaction trước test, rollback sau test | Nhanh nhất |

### 3.2 Ý tưởng transaction rollback, tự làm bằng PHP thuần

Transaction ([Chương 16](16-php-va-database.md)) có tính chất: mọi thay đổi bên trong nó biến mất khi
`ROLLBACK`. Vậy chỉ cần tạo bảng **một lần**, rồi bọc mỗi test trong một transaction và luôn rollback
ở cuối. File sau chạy được với PHP có `pdo_sqlite` (bản Docker chính thức có sẵn):

```php
<?php
declare(strict_types=1);

// Mô phỏng ý tưởng của RefreshDatabase: migrate một lần, mỗi test chạy trong transaction rồi rollback.
$pdo = new PDO('sqlite::memory:');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

// "migrate" một lần cho cả bộ test
$pdo->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE)');

function countUsers(PDO $pdo): int
{
    return (int) $pdo->query('SELECT COUNT(*) FROM users')->fetchColumn();
}

/** @param callable(PDO): void $test */
function runTest(PDO $pdo, string $name, callable $test): void
{
    $pdo->beginTransaction();          // setUp: mở transaction bao quanh test
    try {
        $test($pdo);
        echo "PASS {$name}\n";
    } catch (Throwable $e) {
        echo "FAIL {$name}: {$e->getMessage()}\n";
    } finally {
        $pdo->rollBack();              // tearDown: vứt mọi thay đổi của test
    }
}

runTest($pdo, 'tạo user', function (PDO $pdo): void {
    $pdo->exec("INSERT INTO users (email) VALUES ('a@example.com')");
    if (countUsers($pdo) !== 1) {
        throw new RuntimeException('phải có 1 user');
    }
});

// Test sau dùng lại đúng email đó: không bị UNIQUE chặn vì test trước đã rollback
runTest($pdo, 'tạo user cùng email ở test khác', function (PDO $pdo): void {
    $pdo->exec("INSERT INTO users (email) VALUES ('a@example.com')");
    if (countUsers($pdo) !== 1) {
        throw new RuntimeException('phải có 1 user');
    }
});

echo 'Sau cả bộ test, bảng có ' . countUsers($pdo) . " dòng\n";

// in ra:
// PASS tạo user
// PASS tạo user cùng email ở test khác
// Sau cả bộ test, bảng có 0 dòng
```

Cách này nhanh vì rollback chỉ vứt bỏ những gì test vừa làm, không phải tạo lại bảng. Đó chính là thứ
trait `RefreshDatabase` của Laravel làm, cộng thêm vài chi tiết.

### 3.3 `RefreshDatabase` làm gì bên trong

Dùng trait:

```php
use Illuminate\Foundation\Testing\RefreshDatabase;

final class OrderTest extends TestCase
{
    use RefreshDatabase;
    // ...
}
```

Đọc mã nguồn `Illuminate\Foundation\Testing\RefreshDatabase` (Laravel 13.x), mỗi test đi qua các bước:

```
 test đầu tiên trong process                         các test sau
 ─────────────────────────────                       ─────────────────────────
 RefreshDatabaseState::$migrated === false?          $migrated === true
   └─ có: chạy `migrate:fresh` (xoá mọi bảng,          └─ bỏ qua migrate
          chạy lại mọi migration), đặt $migrated = true
 beginDatabaseTransaction():                         beginDatabaseTransaction()
   mở transaction trên connection mặc định             ...
 ── chạy test ──                                     ── chạy test ──
 khi app bị huỷ cuối test: rollBack(), disconnect()  rollBack(), disconnect()
```

Chi tiết đáng biết:

- `$migrated` là **thuộc tính static**, nên `migrate:fresh` chỉ chạy một lần cho mỗi process test, không
  phải mỗi test. Với SQLite `:memory:` (mặc định trong `phpunit.xml`), database chỉ sống trong một
  connection PDO, nên trait giữ lại object PDO đó trong `RefreshDatabaseState::$inMemoryConnections` và
  gắn lại cho mỗi test.
- Khi kết thúc test, nếu connection **không còn ở trong transaction** (nghĩa là có gì đó đã commit ngoài
  ý muốn), trait đặt `$migrated = false` để test sau migrate lại từ đầu.
- Mặc định chỉ connection mặc định được bọc transaction. Nếu ứng dụng dùng nhiều connection, khai báo
  thuộc tính `protected array $connectionsToTransact = ['mysql', 'reporting'];` trong test class.
- Code ứng dụng gọi `DB::transaction(...)` bên trong test vẫn chạy bình thường: Laravel biến transaction
  lồng thành *savepoint* ([Chương 16](16-php-va-database.md)), và rollback cuối test vẫn xoá
  hết.
- Callback "sau khi commit" (`DB::afterCommit()`, job/listener đánh dấu after commit, xem
  [Chương 29](29-laravel-queue-event-schedule-cache.md)) vẫn chạy trong test: Laravel thay transaction
  manager bằng một bản riêng cho test, coi transaction bọc ngoài của test là "không tính". Callback chạy
  khi transaction của chính ứng dụng commit, hoặc chạy ngay nếu ứng dụng không mở transaction nào.

### 3.4 Các trait khác và khi nào dùng

| Trait | Cách làm | Khi nào dùng |
|---|---|---|
| `RefreshDatabase` | Migrate một lần mỗi process, transaction và rollback mỗi test | Mặc định cho gần như mọi feature test |
| `LazilyRefreshDatabase` | Như trên, nhưng hoãn việc refresh (migrate nếu cần, mở transaction) tới lúc test **thật sự** chạy query đầu tiên | Bộ test có nhiều test không dùng DB |
| `DatabaseMigrations` | Chạy lại migration cho mỗi test | Khi transaction không dùng được (xem dưới); chậm |
| `DatabaseTruncation` | Truncate các bảng | Như trên |
| `DatabaseTransactions` | Chỉ bọc transaction, **không** migrate | Khi schema đã được dựng sẵn bằng cách khác |

Khi nào transaction rollback **không** đủ? Khi dữ liệu phải được nhìn thấy từ **một connection khác**.
Transaction chưa commit thì connection khác không thấy. Ví dụ điển hình: test bằng trình duyệt thật
(Laravel Dusk), nơi trình duyệt gửi request tới một process web server khác. Khi đó dùng
`DatabaseMigrations` hoặc `DatabaseTruncation`. Tài liệu Laravel ghi rõ hai trait này chậm hơn đáng kể
so với `RefreshDatabase`.

### 3.5 Tạo dữ liệu: factory và seeder

*Factory* ([Chương 27](27-laravel-database-eloquent.md)) sinh model với dữ liệu giả hợp lệ, để mỗi test
chỉ ghi ra những gì nó quan tâm:

```php
$user  = User::factory()->create();                         // lưu vào DB
$users = User::factory()->count(3)->create();               // 3 user
$admin = User::factory()->create(['role' => 'admin']);      // ghi đè một cột
$draft = User::factory()->make();                           // tạo object, KHÔNG lưu
```

Cần dữ liệu nền (danh mục, trạng thái đơn hàng...) thì chạy seeder:

```php
$this->seed();                          // chạy DatabaseSeeder
$this->seed(OrderStatusSeeder::class);  // chạy một seeder cụ thể
```

Hoặc gắn attribute `#[Seed]` lên class `TestCase` gốc để Laravel tự chạy `DatabaseSeeder` trước mỗi
test dùng `RefreshDatabase`; `#[Seeder(OrderStatusSeeder::class)]` để chọn seeder cụ thể (cả hai nằm
trong namespace `Illuminate\Foundation\Testing\Attributes`).

### 3.6 Assertion về database

```php
$this->assertDatabaseHas('users', ['email' => 'sally@example.com']);
$this->assertDatabaseMissing('users', ['email' => 'sally@example.com']);
$this->assertDatabaseCount('users', 5);
$this->assertDatabaseEmpty('users');
$this->assertModelExists($user);
$this->assertModelMissing($user);
$this->assertSoftDeleted($user);

$this->expectsDatabaseQueryCount(5);   // gọi ĐẦU test: fail nếu số query khác đúng 5
```

`expectsDatabaseQueryCount` là cách rẻ để khoá lại lỗi N+1 ([Chương 27](27-laravel-database-eloquent.md)):
nếu ai đó bỏ eager loading, số query tăng và test đỏ.

### 3.7 Cạm bẫy về database trong test

⚠️ **SQLite trong test, MySQL trên production.** Mặc định của skeleton rất tiện (không cần server),
nhưng SQLite và MySQL khác nhau về kiểu dữ liệu, hàm SQL, cách so sánh chuỗi, hành vi khi dữ liệu vượt
giới hạn cột, cú pháp JSON... Một câu query chạy đúng trên SQLite có thể sai hoặc lỗi trên MySQL, và
ngược lại. Với ứng dụng dùng tính năng riêng của MySQL (full-text, hàm JSON, lock), hãy chạy test trên
**cùng engine và cùng phiên bản** với production: dựng MySQL 8.4 bằng Docker trong CI và sửa
`DB_CONNECTION`, `DB_DATABASE`... trong `phpunit.xml` hoặc `.env.testing`.

⚠️ **DDL trong MySQL tự commit.** Trong MySQL, các lệnh như `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`,
`TRUNCATE TABLE` gây *implicit commit*: commit luôn transaction đang mở. Một test (hoặc code ứng dụng)
chạy DDL sẽ làm transaction bọc ngoài của `RefreshDatabase` bị commit, dữ liệu của test đó **ở lại**
database. Trait phát hiện được (connection không còn trong transaction) và migrate lại ở test sau, nhưng
nếu bạn thấy dữ liệu lạ còn sót, hãy nghĩ tới nguyên nhân này.

⚠️ **Dữ liệu tạo ngoài transaction.** Test class không dùng `RefreshDatabase` (hoặc dữ liệu ghi qua
connection không nằm trong `$connectionsToTransact`) sẽ để lại dữ liệu thật. Tài liệu Laravel nhắc:
bản ghi do test không dùng trait này tạo ra vẫn có thể còn trong database.

⚠️ **Không bao giờ chạy test vào database thật.** Kiểm tra `phpunit.xml`/`.env.testing` trỏ tới database
riêng cho test, và nhớ `config:clear` (mục 1.3). `migrate:fresh` của `RefreshDatabase` **xoá mọi bảng**.

---

## 4. Fake: thay thế thế giới bên ngoài

### 4.1 Vì sao cần fake

Tính năng "đặt hàng" thường kéo theo: gửi mail xác nhận, đẩy job xuất hoá đơn vào queue, bắn event cho
module kho, gọi API cổng thanh toán. Trong test, bạn **không** muốn:

- gửi mail thật tới khách hàng thật;
- gọi API thật (chậm, tốn tiền, lúc được lúc không, làm test flaky);
- chạy job nặng ngay trong test (nhớ `QUEUE_CONNECTION=sync`, mục 1.3);
- phụ thuộc giờ hiện tại ("đơn quá 7 ngày thì huỷ").

Nhưng bạn **có** muốn kiểm: "mail xác nhận đã được gửi tới đúng người chưa?", "job đã được đẩy vào queue
chưa?". *Fake* ([Chương 21](21-chat-luong-code.md) phân biệt stub, mock, fake, spy) là bản cài đặt thay
thế, hoạt động thật nhưng đơn giản: thay vì gửi, nó **ghi lại** những gì được yêu cầu gửi, rồi cho bạn
assert trên bản ghi đó.

### 4.2 Bên trong: facade tráo object trong container

Vì sao `Mail::fake()` chỉ một dòng mà mọi chỗ trong ứng dụng gọi `Mail::to(...)->send(...)` đều bị chặn?
Vì facade ([Chương 26](26-laravel-container-provider-facade.md)) không chứa logic: mỗi lần gọi method
tĩnh, nó hỏi container lấy object thật rồi chuyển lời gọi sang. `fake()` chỉ việc **đặt một object
khác vào container** dưới cùng tên. Mô phỏng bằng PHP thuần:

```php
<?php
declare(strict_types=1);

// Mô phỏng cơ chế Mail::fake(): facade tra "mailer" trong container; fake() thay nó bằng bản ghi nhớ.
interface Mailer
{
    public function send(string $to, string $subject): void;
}

final class SmtpMailer implements Mailer
{
    public function send(string $to, string $subject): void
    {
        throw new RuntimeException('Không được gửi mail thật trong test!');
    }
}

final class MailFake implements Mailer
{
    /** @var list<array{to: string, subject: string}> */
    private array $sent = [];

    public function send(string $to, string $subject): void
    {
        $this->sent[] = ['to' => $to, 'subject' => $subject];   // chỉ ghi lại, không gửi
    }

    public function assertSent(string $subject, int $times = 1): void
    {
        $count = count(array_filter($this->sent, fn (array $m): bool => $m['subject'] === $subject));
        if ($count !== $times) {
            throw new RuntimeException("Mong {$times} mail '{$subject}', thực tế {$count}");
        }
        echo "OK: đã 'gửi' {$count} mail '{$subject}'\n";
    }
}

/** Container tối giản: id => object */
final class Container
{
    /** @var array<string, object> */
    private static array $instances = [];

    public static function set(string $id, object $o): void { self::$instances[$id] = $o; }
    public static function get(string $id): object { return self::$instances[$id]; }
}

/** "Facade": hàm tĩnh, nhưng mỗi lần gọi đều hỏi container lấy object thật */
final class Mail
{
    public static function send(string $to, string $subject): void
    {
        $mailer = Container::get('mailer');
        assert($mailer instanceof Mailer);
        $mailer->send($to, $subject);
    }

    public static function fake(): MailFake
    {
        $fake = new MailFake();
        Container::set('mailer', $fake);   // tráo object trong container
        return $fake;
    }
}

// Code ứng dụng: không hề biết mình đang bị test
function placeOrder(string $email): void
{
    // ... lưu đơn hàng ...
    Mail::send($email, 'Xác nhận đơn hàng');
}

Container::set('mailer', new SmtpMailer());   // cấu hình "production"

$fake = Mail::fake();                          // trong test
placeOrder('an@example.com');
$fake->assertSent('Xác nhận đơn hàng');

// in ra:
// OK: đã 'gửi' 1 mail 'Xác nhận đơn hàng'
```

Laravel làm đúng ý tưởng đó (trong mã nguồn, `Mail::fake()` tạo một `MailFake` bọc mail manager thật rồi
gọi `Facade::swap()`, hàm này ghi object giả vào cả bộ nhớ đệm của facade lẫn container). Hệ quả quan trọng: **phải gọi `fake()` trước** khi code ứng dụng
chạy. Gọi sau thì những gì đã xảy ra đã đi qua object thật.

### 4.3 Queue và Bus

```php
use App\Jobs\ShipOrder;
use Illuminate\Support\Facades\Queue;

Queue::fake();

// ... gọi code dispatch job ...

Queue::assertPushed(ShipOrder::class);               // đã đẩy ít nhất một lần
Queue::assertPushedOnce(ShipOrder::class);
Queue::assertPushedTimes(ShipOrder::class, 2);
Queue::assertPushedOn('emails', ShipOrder::class);   // đúng tên queue
Queue::assertNotPushed(AnotherJob::class);
Queue::assertNothingPushed();
Queue::assertCount(3);                               // tổng số job

// Kiểm dữ liệu bên trong job bằng closure: pass nếu có ít nhất một job thoả
Queue::assertPushed(fn (ShipOrder $job) => $job->order->id === $order->id);
```

Chỉ fake một số job, để job khác chạy bình thường: `Queue::fake([ShipOrder::class])`; fake tất cả trừ
vài job: `Queue::fake()->except([ShipOrder::class])`.

Chain và batch ([Chương 29](29-laravel-queue-event-schedule-cache.md)) dùng `Bus::fake()` với
`Bus::assertChained([...])`, `Bus::assertBatched(fn (PendingBatch $batch) => ...)`.

Chiến lược test job: **tách làm hai**. Test chỗ dispatch chỉ kiểm "đã đẩy đúng job với đúng dữ liệu"
(dùng fake). Test chính job đó riêng: tạo instance và gọi `handle()` trực tiếp. Muốn kiểm job tự
`release()` hay `fail()`, dùng `$job->withFakeQueueInteractions()` rồi `assertReleased()`,
`assertFailed()`...

### 4.4 Event

```php
use Illuminate\Support\Facades\Event;

Event::fake();

// ... code bắn event ...

Event::assertDispatched(OrderShipped::class);
Event::assertDispatched(OrderShipped::class, 2);       // đúng 2 lần
Event::assertDispatchedOnce(OrderShipped::class);
Event::assertNotDispatched(OrderFailedToShip::class);
Event::assertNothingDispatched();
Event::assertListening(OrderShipped::class, SendShipmentNotification::class); // listener đã đăng ký
```

Sau `Event::fake()`, **không listener nào chạy**. Cạm bẫy theo tài liệu Laravel: nếu factory của bạn dựa
vào event của model (ví dụ sinh UUID trong event `creating`), hãy gọi `Event::fake()` **sau** khi đã
tạo dữ liệu bằng factory, hoặc chỉ fake vài event: `Event::fake([OrderCreated::class])`. Muốn fake trong
một đoạn rồi trả lại bình thường: `Event::fakeFor(function () { ... })`.

### 4.5 Mail, notification, file

```php
use Illuminate\Support\Facades\Mail;

Mail::fake();

// ... code gửi mail ...

Mail::assertSent(OrderShipped::class);
Mail::assertSent(OrderShipped::class, 'example@laravel.com');   // gửi tới địa chỉ này
Mail::assertSent(OrderShipped::class, fn (OrderShipped $mail) => $mail->hasTo($user->email));
Mail::assertNotSent(AnotherMailable::class);
Mail::assertNothingSent();

// Mailable được đưa vào queue (->queue() hoặc implements ShouldQueue):
Mail::assertQueued(OrderShipped::class);
Mail::assertNothingOutgoing();   // không gửi, cũng không queue
```

⚠️ `assertSent` và `assertQueued` khác nhau: mail đi qua queue thì `assertSent` báo **không** gửi. Không
chắc thì dùng `assertNothingOutgoing`/`assertNotOutgoing` (gộp cả hai), hoặc kiểm đúng loại.

Nội dung mail (tiêu đề, người nhận, chữ trong HTML) nên test **riêng**, trên chính object mailable:
`$mailable->assertHasSubject('Invoice Paid')`, `$mailable->assertSeeInHtml($user->email)`. Tài liệu
Laravel khuyên tách hai việc "nội dung mail đúng" và "mail đã được gửi".

Tương tự có `Notification::fake()` (assert bằng `Notification::assertSentTo($user, ...)`) và
`Storage::fake('s3')` (thay một disk bằng thư mục tạm).

### 4.6 HTTP client gọi ra ngoài

Ứng dụng gọi API bằng HTTP client của Laravel (`Http::post(...)`) thì fake bằng `Http::fake()`:

```php
use Illuminate\Http\Client\Request;
use Illuminate\Support\Facades\Http;

Http::preventStrayRequests();   // request nào KHÔNG khớp fake thì ném exception, không gọi thật

Http::fake([
    'api.payment.test/charges' => Http::response(['id' => 'ch_1', 'status' => 'paid'], 200),
    'api.payment.test/*'       => Http::response(['error' => 'not_found'], 404),
]);

// ... code gọi cổng thanh toán ...

Http::assertSent(fn (Request $request) =>
    $request->url() === 'https://api.payment.test/charges'
    && $request['amount'] === 50000
);
Http::assertSentCount(1);
```

Thêm các tình huống khó tái hiện với API thật:

```php
Http::fake(['api.payment.test/*' => Http::failedConnection()]);   // mất kết nối
Http::fake(['api.payment.test/*' => Http::sequence()
    ->push(['status' => 'pending'], 200)                           // lần gọi 1
    ->push(['status' => 'paid'], 200)                              // lần gọi 2
    ->pushStatus(500)]);                                           // lần gọi 3
```

⚠️ Mặc định, URL **không** khớp mẫu nào trong `Http::fake([...])` sẽ được gọi **thật**. Vì vậy nên bật
`Http::preventStrayRequests()` (có thể bật cho cả bộ test trong `setUp()` của `TestCase` gốc). Lưu ý
fake này chỉ chặn HTTP client của Laravel; thư viện tự gọi Guzzle/cURL riêng (SDK của bên thứ ba) không
bị chặn, cần thay cả SDK đó bằng đồ giả qua container (mục 4.8).

### 4.7 Thời gian

Code phụ thuộc "bây giờ" (hết hạn, khoá sau 7 ngày) dùng các helper du hành thời gian của test case
Laravel. Bên dưới chúng gọi `Carbon::setTestNow()`, nên tác động lên `now()` và `Carbon::now()`:

```php
$this->travel(5)->days();                       // tiến 5 ngày
$this->travel(-5)->hours();                     // lùi 5 giờ
$this->travelTo(now()->minus(hours: 6));        // tới một thời điểm cụ thể
$this->travelBack();                            // về hiện tại

$this->freezeTime(function ($time) {            // đóng băng thời gian trong closure
    // ...
});

// Ví dụ
$thread = Thread::factory()->create();
$this->travel(1)->week();
$this->assertTrue($thread->isLockedByInactivity());
```

⚠️ Chỉ có tác dụng với code lấy giờ qua Carbon/`now()`. Code gọi `time()` hay `new DateTimeImmutable()`
của PHP thuần thì không bị ảnh hưởng. Đó là một lý do để luôn lấy giờ qua `now()` (hoặc inject một
"clock", [Chương 21](21-chat-luong-code.md)).

### 4.8 Mock một class của bạn

Với class tự viết được container tiêm vào (ví dụ `PaymentGateway`), thay nó bằng mock:

```php
use App\Services\PaymentGateway;
use Mockery\MockInterface;

$this->mock(PaymentGateway::class, function (MockInterface $mock) {
    $mock->expects('charge')->with(50000)->andReturn('ch_1');
});

$this->postJson('/checkout', [...])->assertOk();
```

`$this->mock()` tạo mock bằng Mockery và đăng ký nó vào container (*instance binding*), nên mọi chỗ
resolve `PaymentGateway` đều nhận mock. Có thêm `partialMock()` (chỉ giả vài method) và `spy()` (ghi
lại mọi lời gọi để assert sau).

⚠️ Mock chỉ tác dụng khi class được lấy **từ container** (type-hint trong constructor/method, `app()`,
`resolve()`). Code tự `new PaymentGateway()` thì mock không chen vào được.

⚠️ Tài liệu Laravel dặn: **đừng mock facade `Request`**, hãy truyền input qua `get()`/`post()`; đừng mock
`Config`, hãy gọi `Config::set(...)` hoặc `config([...])` trong test.

### 4.9 Ghép lại: một test đặt hàng đầy đủ

```php
// tests/Feature/CheckoutTest.php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Jobs\GenerateInvoice;
use App\Mail\OrderConfirmed;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Queue;
use Tests\TestCase;

final class CheckoutTest extends TestCase
{
    use RefreshDatabase;

    public function test_dat_hang_thanh_cong(): void
    {
        // Arrange
        Queue::fake();
        Mail::fake();
        Http::preventStrayRequests();
        Http::fake(['api.payment.test/*' => Http::response(['status' => 'paid'], 200)]);
        $user = User::factory()->create();

        // Act
        $response = $this->actingAs($user)->postJson('/checkout', ['product' => 'Bút', 'quantity' => 2]);

        // Assert
        $response->assertCreated();
        $this->assertDatabaseHas('orders', ['user_id' => $user->id, 'status' => 'paid']);
        Queue::assertPushed(GenerateInvoice::class);
        Mail::assertQueued(OrderConfirmed::class, fn (OrderConfirmed $m) => $m->hasTo($user->email));
        Http::assertSentCount(1);
    }

    public function test_thanh_toan_loi_thi_khong_tao_don(): void
    {
        Queue::fake();
        Http::fake(['api.payment.test/*' => Http::response(['error' => 'declined'], 402)]);
        $user = User::factory()->create();

        $this->actingAs($user)
            ->postJson('/checkout', ['product' => 'Bút', 'quantity' => 2])
            ->assertStatus(402);

        $this->assertDatabaseCount('orders', 0);
        Queue::assertNothingPushed();
    }
}
```

(Ví dụ minh hoạ cách ghép các công cụ; route `/checkout`, model, job, mailable là của ứng dụng giả định.)

---

## 5. Viết test Laravel bằng Pest

[Chương 21](21-chat-luong-code.md) đã giới thiệu Pest: framework test chạy trên nền PHPUnit, cú pháp
dạng hàm. Khi tạo project, trình cài Laravel cho chọn Pest hoặc PHPUnit; tài liệu Laravel viết mọi ví
dụ test chính cho cả hai. Phần riêng của Laravel nằm ở file cấu hình `tests/Pest.php`:

```php
<?php
// tests/Pest.php
use Illuminate\Foundation\Testing\RefreshDatabase;

pest()->extend(Tests\TestCase::class)   // $this trong test thuộc thư mục Feature là Tests\TestCase
    ->use(RefreshDatabase::class)       // gắn trait cho mọi test trong thư mục đó
    ->in('Feature');
```

`extend()` quyết định `$this` trong closure test là object gì. Nhờ dòng trên, `$this->postJson()`,
`$this->actingAs()`... dùng được y như test class PHPUnit. Muốn gắn trait cho riêng một file thì gọi
`pest()->use(RefreshDatabase::class);` ở đầu file đó, không có `->in()`.

Test đơn hàng ở mục 2.2 viết bằng Pest:

```php
<?php
// tests/Feature/OrderTest.php
use App\Models\Order;
use App\Models\User;

test('khách chưa đăng nhập không tạo được đơn', function () {
    $this->postJson('/orders', ['product' => 'Bút', 'quantity' => 2])
        ->assertUnauthorized();

    expect(Order::count())->toBe(0);
});

it('cho user tạo đơn', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->postJson('/orders', ['product' => 'Bút', 'quantity' => 2])
        ->assertCreated()
        ->assertJsonPath('product', 'Bút');

    $this->assertDatabaseHas('orders', ['user_id' => $user->id, 'quantity' => 2]);
});

it('từ chối số lượng không dương', function (int $quantity) {
    $this->actingAs(User::factory()->create())
        ->postJson('/orders', ['product' => 'Bút', 'quantity' => $quantity])
        ->assertInvalid(['quantity']);
})->with([0, -1]);
```

Các assertion HTTP, database, fake ở mục 2 tới 4 dùng nguyên vẹn; Pest chỉ thêm cú pháp `expect(...)`
và dataset `->with(...)` (tương đương data provider của PHPUnit).

---

## 6. Laravel Octane: giữ ứng dụng sống trong bộ nhớ

### 6.1 Chi phí ẩn của mô hình PHP-FPM

Nhắc lại [Chương 2](02-php-chay-nhu-the-nao.md) và [Chương 18](18-fpm-nginx-opcache.md): với PHP-FPM,
mỗi request là một vòng đời trọn vẹn, *share-nothing*. Với một ứng dụng Laravel, mỗi request phải làm
lại từ đầu:

```
 request 1:  nạp autoload ─► tạo Application ─► register mọi provider ─► boot mọi provider
             ─► nạp config, route ─► middleware ─► controller ─► response ─► VỨT HẾT
 request 2:  nạp autoload ─► tạo Application ─► register ─► boot ─► ... ─► VỨT HẾT
 request 3:  ...
```

OPcache đã bỏ được bước biên dịch file PHP, và `php artisan optimize` (mục 7.2) đã bỏ bớt việc đọc
nhiều file config/route. Nhưng việc **tạo object** (container, hàng chục service provider, router,
connection DB...) vẫn lặp lại cho mỗi request. Với endpoint nhẹ (trả vài dòng JSON), phần khởi động này
có thể chiếm phần lớn thời gian xử lý.

Bù lại, mô hình này có một ưu điểm cực lớn: **request trước không thể làm hỏng request sau**. Biến
static, singleton, mảng toàn cục đều bị vứt bỏ khi request kết thúc. Code PHP xưa nay được viết với giả
định ngầm đó.

### 6.2 Ý tưởng của Octane

*Laravel Octane* là package chính thức chạy ứng dụng Laravel trên một *application server* sống lâu.
Theo tài liệu: Octane **boot ứng dụng một lần, giữ nó trong bộ nhớ**, rồi đưa lần lượt các request vào.

```
 worker process (sống lâu, xử lý hàng trăm request)
 ┌───────────────────────────────────────────────────────────────────────┐
 │ khởi động: autoload ─► Application ─► register ─► boot  (MỘT lần)      │
 │                                                                       │
 │ request 1 ─► [clone app] ─► middleware ─► controller ─► response ─► dọn │
 │ request 2 ─► [clone app] ─► middleware ─► controller ─► response ─► dọn │
 │ request 3 ─► ...                                                      │
 └───────────────────────────────────────────────────────────────────────┘
```

Nhanh hơn vì bỏ được toàn bộ phần khởi động lặp lại. Cái giá: giả định "mọi thứ được vứt bỏ sau
request" **không còn đúng**. Thứ gì sống ở cấp process (biến static, object tạo lúc boot) sẽ sống qua
nhiều request, của nhiều user khác nhau.

### 6.3 Thấy tận mắt: mô phỏng một worker sống lâu

File PHP thuần sau mô phỏng đúng cách Octane làm (boot một lần, clone ứng dụng cho mỗi request) và hai
lỗi kinh điển:

```php
<?php
declare(strict_types=1);

// Mô phỏng một worker kiểu Octane: khởi động app MỘT lần, rồi phục vụ nhiều request trong cùng process.

final class Request
{
    public function __construct(public readonly string $user) {}
}

final class App
{
    /** @var array<string, object> các singleton đã tạo */
    public array $instances = [];
    /** @var array<string, Closure(App): object> */
    public array $singletons = [];

    public function singleton(string $id, Closure $factory): void { $this->singletons[$id] = $factory; }

    public function make(string $id): object
    {
        return $this->instances[$id] ??= ($this->singletons[$id])($this);
    }
}

// Service giữ request trong constructor: an toàn với FPM, nguy hiểm với worker sống lâu
final class Greeter
{
    public function __construct(private Request $request) {}
    public function hello(): string { return "Xin chào {$this->request->user}"; }
}

final class Stats
{
    /** @var list<string> */
    public static array $seen = [];       // static: sống suốt đời process
}

// ---- Boot một lần ----
$base = new App();
$base->singleton(Greeter::class, fn (App $app): Greeter => new Greeter($app->make(Request::class)));
$base->instances[Request::class] = new Request('(boot)');
$base->make(Greeter::class);  // lỡ resolve lúc boot (ví dụ trong boot() của provider)

// ---- Vòng lặp request ----
foreach (['an', 'binh', 'chi'] as $user) {
    $sandbox = clone $base;                          // Octane clone app cho mỗi request
    $sandbox->instances[Request::class] = new Request($user);

    Stats::$seen[] = $user;                          // rò bộ nhớ: mảng static cứ lớn dần
    echo str_pad($user, 5) . '| ' . $sandbox->make(Greeter::class)->hello()
        . ' | Stats::$seen có ' . count(Stats::$seen) . " phần tử\n";
    unset($sandbox);                                 // hết request, bỏ sandbox
}

// in ra:
// an   | Xin chào (boot) | Stats::$seen có 1 phần tử
// binh | Xin chào (boot) | Stats::$seen có 2 phần tử
// chi  | Xin chào (boot) | Stats::$seen có 3 phần tử
```

Hai lỗi lộ ra:

1. **Trạng thái cũ (*stale state*).** `Greeter` là singleton được tạo lúc boot, giữ object `Request`
   của lúc đó. `clone $base` chỉ sao chép mảng `$instances` (các phần tử vẫn trỏ tới **cùng** object
   `Greeter`), nên mọi request đều thấy request cũ. Trong ứng dụng thật, đây là lỗi "user B thấy dữ liệu
   của user A": header, input, user đăng nhập đều sai.
2. **Rò bộ nhớ (*memory leak*).** `Stats::$seen` là static, sống suốt đời process. Với FPM nó bị xoá sau
   mỗi request; ở đây nó lớn mãi.

Với PHP-FPM, cả hai đoạn code trên đều **vô hại**, vì mỗi request là một vòng đời mới. Đó là lý do lỗi
Octane thường chỉ lộ ra sau khi chuyển hạ tầng, khi worker phục vụ liên tiếp request của nhiều user
khác nhau.

Sửa lỗi 1 theo cách tài liệu Octane gợi ý: đừng giữ object `Request`, hãy giữ một **closure lấy request
hiện tại**. Đổi `Greeter` và chỗ đăng ký (phần còn lại giữ nguyên, bỏ dòng `Stats`):

```php
/** Trỏ tới app đang phục vụ request hiện tại (vai trò của Container::getInstance() trong Laravel) */
final class Current
{
    public static App $app;
}

final class Greeter
{
    /** @param Closure(): Request $request */
    public function __construct(private Closure $request) {}
    public function hello(): string { return "Xin chào " . ($this->request)()->user; }
}

$base->singleton(Greeter::class, fn (App $app): Greeter => new Greeter(fn (): Request => Current::$app->make(Request::class)));
// ... trong vòng lặp, sau khi tạo sandbox: Current::$app = $sandbox;
// (và trước khi resolve lúc boot: Current::$app = $base;)

// in ra:
// an   | Xin chào an
// binh | Xin chào binh
// chi  | Xin chào chi
```

### 6.4 Ba application server: FrankenPHP, RoadRunner, Swoole

Octane không tự làm server. Nó chạy trên một trong các server sau (tài liệu Octane 13.x liệt kê
FrankenPHP, Open Swoole, Swoole, RoadRunner):

| | FrankenPHP | RoadRunner | Swoole / Open Swoole |
|---|---|---|---|
| Là gì | Application server viết bằng Go, xây trên web server Caddy, nhúng PHP vào bên trong | Application server viết bằng Go; chạy các process PHP worker riêng và chuyển request cho chúng | Extension PHP (viết bằng C/C++) biến PHP thành server có event loop |
| Cài | Octane tự tải binary khi chọn FrankenPHP; có image Docker chính thức | Octane đề nghị tải binary `rr` lần đầu chạy | `pecl install swoole` (hoặc `openswoole`) |
| Ghi chú | Tài liệu nêu: hỗ trợ early hints, nén Brotli và Zstandard; cấu hình thêm bằng Caddyfile | Cần thêm package Composer `spiral/roadrunner-http`, `spiral/roadrunner-cli` (`octane:install` đề nghị cài khi chọn RoadRunner) | Tính năng riêng chỉ Swoole có (mục 6.9) |

Mặc định trong `config/octane.php`, server là `env('OCTANE_SERVER', 'roadrunner')`; lệnh
`php artisan octane:install` hỏi bạn chọn server. Cả ba đều được Octane hỗ trợ chính thức; khác biệt
lớn nhất khi chọn là cách cài đặt và việc bạn có cần các tính năng chỉ Swoole có hay không.

### 6.5 Cài đặt và các tham số quan trọng

```bash
# Chạy trong thư mục project
composer require laravel/octane
php artisan octane:install            # tạo config/octane.php, chọn server

php artisan octane:start              # mặc định cổng 8000
php artisan octane:start --watch      # dev: tự restart khi file đổi (cần Node và chokidar)
php artisan octane:start --workers=4 --max-requests=250
php artisan octane:reload             # nạp lại worker một cách êm (sau deploy)
php artisan octane:status
php artisan octane:stop
```

| Tham số | Mặc định (theo tài liệu) | Ý nghĩa |
|---|---|---|
| `--workers` | Một worker cho mỗi nhân CPU | Số request xử lý song song. Mỗi worker một request tại một thời điểm, giống worker FPM |
| `--max-requests` | 500 | Worker tự khởi động lại êm sau ngần ấy request, để chặn rò bộ nhớ tích luỹ |
| `max_execution_time` (trong `config/octane.php`) | 30 giây | Request chạy quá thời gian này bị dừng; `0` là không giới hạn. Đổi xong phải restart server |

⚠️ Vì code đã nằm sẵn trong bộ nhớ, **sửa file không có tác dụng** cho tới khi worker được nạp lại. Ở máy
dev dùng `--watch`; trên production phải `octane:reload` (hoặc `php artisan reload`, mục 7.4) sau mỗi
lần deploy. Quên bước này là "deploy xong mà vẫn chạy code cũ".

### 6.6 Octane tự dọn những gì

Đọc mã nguồn `Laravel\Octane\Worker` (Octane 2.x), mỗi request được xử lý như sau:

```
 boot:   $app = tạo và bootstrap Application (một lần); resolve trước các service trong 'warm'
 mỗi request:
   $sandbox = clone $app                 ◄── bản sao nông của container
   bắn event RequestReceived            ◄── các listener "chuẩn bị cho request mới"
   $sandbox->make(Kernel)->handle($request)
   gửi response, terminate
   OperationTerminated: quên scoped instance, quên các binding liệt kê trong 'flush' (trên $app gốc)
   $sandbox->flush(); quay về $app gốc
```

Hệ quả của bản sao nông: singleton resolve lần đầu **trong** request được lưu vào mảng instance của
`$sandbox`, nên bị bỏ cùng `$sandbox` sau request. Singleton sống qua nhiều request là singleton đã
có sẵn trong `$app` gốc: resolve lúc boot (ví dụ trong `boot()` của provider) hoặc nằm trong danh sách
`warm`. Vì vậy tài liệu Octane mô tả lỗi giữ request/container cũ kèm điều kiện "nếu service được
resolve trong quá trình boot".

Danh sách listener mặc định trong `config/octane.php` cho thấy Octane đã lo sẵn cho phần của framework:
gắn application/request mới cho authorization gate, cache, database, session, router, view, validator, mail, queue...;
xoá trạng thái session, xác thực, locale, cookie đang chờ, cache `array`, log context... Tài liệu tóm
lại: Octane tự reset trạng thái của framework giữa các request, nhưng **không phải lúc nào cũng biết cách
reset trạng thái do code của bạn tạo ra**.

Hai cấu hình liên quan:

```php
// config/octane.php
'warm'  => [...Octane::defaultServicesToWarm()],   // resolve sẵn lúc boot worker, dùng chung mọi request
'flush' => [
    // các binding bạn muốn bị quên sau mỗi request
],
```

Binding kiểu `scoped` ([Chương 26](26-laravel-container-provider-facade.md)) sinh ra đúng cho tình
huống này: hoạt động như singleton trong **một** request (hoặc một job), và được Octane xoá sau mỗi
request (listener `FlushTemporaryContainerInstances` gọi `forgetScopedInstances()`).

### 6.7 Rò trạng thái: các dạng thường gặp và cách sửa

Các dạng "singleton giữ..." dưới đây gây lỗi khi singleton đó đã nằm trong app gốc (resolve lúc boot
hoặc trong `warm`, mục 6.6); singleton resolve lần đầu trong request thì bị bỏ cùng sandbox.

| Dạng lỗi | Ví dụ | Hậu quả | Cách sửa |
|---|---|---|---|
| Singleton giữ `Request` | `singleton(Service::class, fn ($app) => new Service($app['request']))` | Header, input, user sai: thấy dữ liệu của request cũ | Truyền dữ liệu cần thiết qua tham số method lúc gọi (cách tài liệu khuyên nhất); hoặc giữ closure `fn () => $app['request']`; hoặc đổi sang `bind`/`scoped` |
| Singleton giữ cả container | `new Service($app)` | Container cũ, thiếu binding đăng ký sau | Dùng `fn () => Container::getInstance()`; hàm `app()` luôn trả container hiện tại |
| Singleton giữ config repository | `new Service($app->make('config'))` | Không thấy giá trị config đổi giữa các request | Closure lấy config, hoặc dùng hàm `config()` |
| Biến static tích luỹ | `Service::$data[] = ...` trong controller | Rò bộ nhớ | Không dùng static làm kho dữ liệu theo request |
| Singleton tự viết có thuộc tính thay đổi theo request | `CurrentTenant` là singleton đã resolve lúc boot, set tenant trong middleware | Request sau thấy tenant của request trước nếu không set lại | Đăng ký `scoped`, hoặc thêm vào mảng `flush` |

Những thứ **an toàn** theo tài liệu Octane: type-hint `Illuminate\Http\Request` trong method controller
và closure route; dùng các helper `request()`, `app()`, `config()` (luôn trả object của request hiện
tại).

Nguyên tắc tổng quát: object sống lâu hơn một request (singleton tạo lúc boot, static) **không được
giữ dữ liệu của một request cụ thể**.

### 6.8 Rò bộ nhớ và `--max-requests`

Trong FPM, rò bộ nhớ tự hết khi request kết thúc. Trong Octane, mỗi request rò một ít thì worker phình
dần. Tài liệu khuyên theo dõi bộ nhớ của ứng dụng khi phát triển. `--max-requests` (mặc định 500) là lưới
an toàn: worker được thay mới định kỳ, giống `pm.max_requests` của FPM
([Chương 18](18-fpm-nginx-opcache.md)). Nó không thay được việc sửa lỗi rò: nếu một request rò lớn, 500
request vẫn đủ làm process vượt giới hạn bộ nhớ.

### 6.9 Tính năng chỉ có khi dùng Swoole

Theo tài liệu, các tính năng sau **yêu cầu Swoole** (Open Swoole cũng có):

- `Octane::concurrently([fn () => ..., fn () => ...])`: chạy nhiều tác vụ song song trên các *task
  worker* (process riêng, số lượng đặt bằng `--task-workers`), không quá 1024 tác vụ một lần.
- `Octane::tick('ten', fn () => ...)->seconds(10)`: chạy định kỳ trong server.
- Cache driver `octane` (dựa trên Swoole table): dữ liệu dùng chung giữa các worker trên **cùng một
  server**, mất khi server restart.
- Swoole table tự định nghĩa (`Octane::table(...)`), cột chỉ có kiểu `string`, `int`, `float`.

### 6.10 Chạy Octane trên production

Octane là một process sống lâu, cần một *process monitor* như Supervisor giữ cho nó luôn chạy (cấu hình
mẫu theo tài liệu Octane):

```ini
; /etc/supervisor/conf.d/octane.conf
[program:octane]
process_name=%(program_name)s_%(process_num)02d
command=php /home/forge/example.com/artisan octane:start --server=frankenphp --host=127.0.0.1 --port=8000
autostart=true
autorestart=true
user=forge
redirect_stderr=true
stdout_logfile=/home/forge/example.com/storage/logs/octane.log
stopwaitsecs=3600
```

Tài liệu khuyên đặt Octane **sau** một web server như Nginx: Nginx phục vụ file tĩnh, lo chứng chỉ SSL,
và *reverse proxy* (`proxy_pass http://127.0.0.1:8000`) các request còn lại vào Octane. Khác với FPM
(Nginx nói FastCGI), ở đây Nginx nói HTTP với Octane. Khi phục vụ qua HTTPS, đặt `OCTANE_HTTPS=true` để
Laravel sinh link `https://`.

### 6.11 Có nên dùng Octane

| Nên cân nhắc khi | Không nên (chưa nên) khi |
|---|---|
| Đã làm hết các bước rẻ ([Chương 20](20-hieu-nang.md)): `optimize`, OPcache, sửa query chậm | Thời gian request chủ yếu nằm ở database hay API bên ngoài: Octane không làm query nhanh hơn |
| Endpoint nhẹ, lưu lượng cao, phần khởi động framework chiếm tỷ lệ lớn | Codebase cũ, nhiều package lạ, nhiều static/singleton giữ trạng thái chưa ai rà |
| Team hiểu và kiểm được rủi ro rò trạng thái | Không có tải kiểm thử (load test) để bắt lỗi chỉ lộ ra khi nhiều request liên tiếp |

Chuyển sang Octane là một thay đổi về **mô hình chạy**, không chỉ là đổi cấu hình. Cách làm an toàn:
rà các binding singleton và biến static của ứng dụng lẫn package, chạy song song với FPM một thời gian,
load test với nhiều user khác nhau và kiểm dữ liệu trả về không lẫn giữa user.

---

## 7. Triển khai lên production

*Triển khai* (*deploy*) là đưa một phiên bản code mới lên server đang phục vụ người dùng. Phần hạ tầng
chung (Nginx, PHP-FPM, OPcache, deploy bằng symlink, Docker) đã ở [Chương 18](18-fpm-nginx-opcache.md);
phần tối ưu khởi động (`optimize`, autoloader) ở [Chương 20](20-hieu-nang.md). Mục này ghép chúng lại
thành quy trình cho một ứng dụng Laravel, cộng những phần riêng: migration, queue worker, reload, health
check.

### 7.1 Cấu hình bắt buộc cho production

| Mục | Giá trị đúng | Vì sao |
|---|---|---|
| `APP_ENV` | `production` | Nhiều hành vi dựa vào môi trường (ví dụ lệnh nguy hiểm hỏi xác nhận, mục 7.3) |
| `APP_DEBUG` | `false` | Tài liệu cảnh báo: để `true` trên production có nguy cơ lộ giá trị cấu hình nhạy cảm cho người dùng cuối (trang lỗi chi tiết) |
| `APP_KEY` | Đã đặt, giữ bí mật, không đổi tuỳ tiện | Dùng để mã hoá cookie, session, dữ liệu `encrypt()` ([Chương 23](23-laravel-gioi-thieu.md)) |
| Document root của web server | Thư mục `public/` | Tài liệu dặn không bao giờ chuyển `index.php` ra gốc project, vì sẽ lộ file cấu hình ra Internet |
| Quyền ghi | `storage/` và `bootstrap/cache/` ghi được bởi user chạy PHP | Laravel ghi log, cache, session, view đã biên dịch, file cache cấu hình vào đây |
| Phiên bản PHP | Laravel 13 yêu cầu PHP >= 8.3 cùng các extension trong trang Deployment (ctype, curl, dom, fileinfo, filter, hash, mbstring, openssl, pcre, pdo, session, tokenizer, xml) | Thiếu extension thì lỗi ngay lúc chạy |

### 7.2 Bước build: dependency và cache khởi động

```bash
# Chạy trong thư mục của bản release mới (trên server, hoặc trong bước build image/CI)
composer install --no-dev --optimize-autoloader --no-interaction
npm ci && npm run build            # nếu có frontend build bằng Vite
php artisan optimize               # config:cache, event:cache, route:cache, view:cache
```

Chi tiết từng lệnh cache, file sinh ra, và lý do `optimize:clear` nguy hiểm trên production (xoá luôn
dữ liệu trong cache store mặc định) ở [Chương 20, mục 7](20-hieu-nang.md). Hai cạm bẫy phải nhớ:

- ⚠️ Sau `config:cache`, file `.env` không được nạp nữa, `env('X')` ngoài thư mục `config/` trả `null`.
  Chỉ gọi `env()` trong file config, mọi nơi khác dùng `config()`.
- ⚠️ Các lệnh cache phải nằm **trong script deploy**, chạy mỗi lần deploy. Chạy tay thì sớm muộn sẽ quên,
  và route mới báo 404, config mới không có hiệu lực.

### 7.3 Migration trên production

```bash
php artisan migrate --force
```

Trên production, Laravel **hỏi xác nhận** trước các lệnh migration vì chúng có thể làm mất dữ liệu.
Script deploy chạy không có người trả lời, nên cần `--force` để bỏ bước hỏi. Đừng bao giờ chạy
`migrate:fresh` hay `migrate:refresh` trên production: chúng xoá bảng.

Vấn đề thật sự khó là **thứ tự**. Trong một lần deploy không downtime, luôn có một khoảng thời gian mà
code cũ và schema mới (hoặc code mới và schema cũ) cùng tồn tại:

- Chạy migration **trước** khi đổi code: code cũ đang phục vụ request phải chạy được trên schema mới.
- Chạy migration **sau** khi đổi code: code mới phải chạy được trên schema cũ trong vài giây đó.
- Có nhiều server, hoặc queue worker chưa kịp restart: code cũ và mới chạy **cùng lúc** trên cùng
  database.

Lời giải phổ biến là kỹ thuật *expand/contract* (mở rộng rồi thu hẹp): mỗi lần deploy chỉ thay đổi
schema theo cách **tương thích ngược** với code đang chạy. Ví dụ đổi tên cột `name` thành `full_name`
trên bảng `users`. Làm `renameColumn` trong một lần deploy sẽ khiến code cũ (đọc `name`) lỗi ngay khi
migration chạy xong. Thay vào đó, chia làm ba lần deploy:

| Bước | Migration | Code | Code cũ còn chạy có lỗi không |
|---|---|---|---|
| Deploy 1 (expand) | Thêm cột `full_name` cho phép NULL | Ghi vào **cả** `name` và `full_name`; vẫn đọc `name` | Không: code cũ không biết cột mới, cột mới cho phép NULL |
| Giữa 1 và 2 | Job/command chép dữ liệu `name` sang `full_name` cho dòng cũ (chia lô) | | Không |
| Deploy 2 | (không) | Đọc `full_name`; vẫn ghi cả hai cột | Không: code của deploy 1 vẫn đọc `name` và được ghi đủ |
| Deploy 3 (contract) | Xoá cột `name` | Chỉ dùng `full_name` | Không: không còn code nào đọc `name` |

Quy tắc rút ra: thêm thì dễ (thêm cột cho phép NULL hoặc có default, thêm bảng), xoá và đổi tên phải
làm sau cùng, khi chắc chắn không còn code nào dùng. Một lợi ích nữa: muốn *rollback* code (đổi symlink
về bản trước) thì code cũ vẫn chạy được trên schema hiện tại. Đổi symlink **không** rollback được
migration.

⚠️ `ALTER TABLE` trên bảng lớn có thể chạy lâu và tốn tài nguyên, tuỳ loại thay đổi và thuật toán DDL mà
MySQL chọn. Với bảng lớn, thử trên bản sao dữ liệu thật trước, và tìm hiểu online DDL trong tài liệu
MySQL 8.4 hoặc công cụ như `gh-ost`, `pt-online-schema-change`.

### 7.4 Process sống lâu: queue worker và `php artisan reload`

Queue worker (`php artisan queue:work`, [Chương 29](29-laravel-queue-event-schedule-cache.md)) cũng là
process sống lâu như Octane: nó boot ứng dụng một lần rồi xử lý job liên tục. Hệ quả cho deploy:
**worker không thấy code mới cho tới khi được khởi động lại**.

Trên production, worker được giữ chạy bởi Supervisor. Cấu hình mẫu theo tài liệu Laravel:

```ini
; /etc/supervisor/conf.d/laravel-worker.conf
[program:laravel-worker]
process_name=%(program_name)s_%(process_num)02d
command=php /home/forge/app.com/artisan queue:work --sleep=3 --tries=3 --max-time=3600
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
user=forge
numprocs=8
redirect_stderr=true
stdout_logfile=/home/forge/app.com/worker.log
stopwaitsecs=3600
```

```bash
# Chạy trên server sau khi tạo/sửa file cấu hình
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start "laravel-worker:*"
```

- `numprocs=8`: Supervisor chạy và trông 8 process worker, chết process nào thì bật lại process đó.
- `stopwaitsecs`: số giây Supervisor chờ process dừng êm trước khi giết hẳn. ⚠️ Tài liệu dặn giá trị
  này phải **lớn hơn thời gian chạy của job dài nhất**, nếu không job bị giết giữa chừng.
- `--max-time=3600`: worker tự thoát sau một giờ (Supervisor bật lại), một cách giới hạn rò bộ nhớ.

**Khởi động lại worker một cách êm.** Đừng `kill` worker giữa lúc đang chạy job. Dùng:

```bash
php artisan queue:restart
```

Cơ chế (đọc mã nguồn `RestartCommand` và `Queue\Worker` của Laravel 13.x): lệnh này ghi thời điểm hiện
tại vào cache với key `illuminate:queue:restart`. Mỗi worker nhớ giá trị đó lúc khởi động, và cuối mỗi
vòng lặp (sau khi xử lý một job, hoặc sau khi ngủ vì queue rỗng) lại đọc lại; thấy giá trị khác thì
**thoát sau khi xong job hiện tại**. Supervisor thấy process thoát
và bật process mới, process mới nạp code mới.

```
 deploy ──► queue:restart ──► cache['illuminate:queue:restart'] = T2
                                         │
 worker (nhớ T1) ── job 41 ── đọc cache: T2 ≠ T1 ──► xong job 41, exit
                                                          │
 Supervisor ◄─────────────────────────────────────────────┘ bật worker mới (code mới, nhớ T2)
```

⚠️ Vì tín hiệu đi qua cache, cache store mặc định phải **dùng chung** giữa nơi chạy lệnh và mọi worker
(Redis, database...). Với cache `file` trên nhiều server, hoặc cache `array`, worker không bao giờ
nhận được tín hiệu. Tài liệu Laravel cũng nhắc phải cấu hình cache đúng trước khi dùng tính năng này.

**`php artisan reload`: một lệnh cho mọi process sống lâu.** Đọc mã nguồn `ReloadCommand`
(Laravel 13.x), lệnh này chạy:

| Key | Lệnh mặc định | Ai đăng ký |
|---|---|---|
| `queue` | `queue:restart` | Framework |
| `schedule` | `schedule:interrupt` | Framework (ngắt lần `schedule:run` đang chạy, liên quan tới tác vụ chạy dưới một phút) |
| `octane` | `octane:reload` | Package Octane, nếu cài |
| `queue` (ghi đè) | `horizon:terminate` | Package Horizon, nếu cài: thay `queue:restart` bằng lệnh của Horizon |
| `reverb` | `reverb:restart` | Package Reverb, nếu cài |
| `pulse` | `pulse:restart` | Package Pulse, nếu cài |

Có thể bỏ bớt bằng `php artisan reload --except=schedule`. Lưu ý tài liệu: `reload` chỉ **kết thúc** các
service; bạn phải có process monitor (Supervisor, systemd, Kubernetes...) để bật chúng lại.

⚠️ Job đang nằm trong queue lúc deploy được *serialize* bởi code **cũ** nhưng sẽ được chạy bởi code
**mới**. Đổi constructor hay thuộc tính của một class job đang có hàng nghìn job chờ có thể làm các job
đó lỗi. Với thay đổi lớn, tạo class job mới (ví dụ `SendInvoiceV2`), giữ class cũ cho tới khi queue cạn.

### 7.5 Deploy không downtime: thứ tự các bước

[Chương 18, mục 11](18-fpm-nginx-opcache.md) đã giải thích cấu trúc `releases/`, `shared/`, `current`
và việc đổi symlink nguyên tử. Với Laravel, thứ tự bước trong script là:

```
 /var/www/app/
 ├── releases/
 │   ├── 20261001_0900/
 │   └── 20261003_1400/        ◄── bản mới đang chuẩn bị
 ├── shared/
 │   ├── .env                  ◄── dùng chung, symlink vào từng release
 │   └── storage/              ◄── log, file upload, session file... dùng chung
 └── current -> releases/20261001_0900    (Nginx/FPM trỏ vào current/public)
```

```bash
#!/usr/bin/env bash
# deploy.sh: chạy trên server. Bản phác thảo để hiểu thứ tự, chưa xử lý lỗi đầy đủ.
set -euo pipefail
APP=/var/www/app
NEW=$APP/releases/$(date +%Y%m%d_%H%M%S)

# 1. Lấy code vào thư mục release mới (ở đây: giải nén artifact do CI build)
mkdir -p "$NEW" && tar -xzf /tmp/build.tar.gz -C "$NEW"

# 2. Nối phần dùng chung
ln -s $APP/shared/.env "$NEW/.env"
rm -rf "$NEW/storage" && ln -s $APP/shared/storage "$NEW/storage"

# 3. Dependency và cache khởi động, chạy TRONG thư mục release mới
cd "$NEW"
composer install --no-dev --optimize-autoloader --no-interaction
php artisan optimize

# 4. Migration tương thích ngược (mục 7.3)
php artisan migrate --force

# 5. Đổi symlink nguyên tử
ln -sfn "$NEW" $APP/current.tmp && mv -T $APP/current.tmp $APP/current

# 6. Cho process đang chạy nạp code mới
sudo systemctl reload php8.4-fpm      # hoặc reset OPcache; tên service tuỳ bản cài (Chương 18)
php artisan reload                    # queue worker, scheduler, Octane, Horizon...

# 7. Kiểm tra nhanh, rồi dọn bớt release cũ (giữ vài bản để rollback)
curl -fsS https://example.com/up > /dev/null
ls -1dt $APP/releases/* | tail -n +6 | xargs -r rm -rf
```

Những điểm hay sai:

- ⚠️ `php artisan optimize` phải chạy bằng `artisan` của **release mới**, trước khi đổi symlink. File
  config cache chứa đường dẫn tuyệt đối và giá trị của đúng release đó; chạy nhầm trong `current` (lúc
  vẫn trỏ bản cũ) là cache cho bản cũ.
- ⚠️ Quên bước 6: FPM với `opcache.validate_timestamps=0` vẫn chạy code cũ
  ([Chương 18, mục 11.4](18-fpm-nginx-opcache.md)); worker và Octane chạy code cũ cho tới khi restart.
- ⚠️ `storage/` không dùng chung giữa các release thì mỗi lần deploy mất log, file upload, session file.
- Rollback nhanh = trỏ symlink về release trước + bước 6. Nhưng migration đã chạy thì không quay lại,
  nên mới cần expand/contract.

Dùng Docker/Kubernetes thì ý tưởng giữ nguyên, chỉ đổi hình thức. Cách làm phổ biến (khuyến nghị
vận hành chung, không phải quy định trong tài liệu Laravel): bước 1 tới 3 nằm trong lúc build image
(trừ `config:cache` nếu config lấy từ biến môi trường lúc chạy container: khi đó nên chạy `optimize`
lúc container khởi động), migration chạy bằng một job riêng trước khi rollout, và "đổi symlink" là
rolling update của orchestrator.

### 7.6 Health check

*Health check* là một URL để hệ thống bên ngoài (load balancer, Kubernetes, dịch vụ uptime) hỏi "ứng dụng
còn sống không?". Laravel có sẵn route `/up`, khai báo trong `bootstrap/app.php` của skeleton:

```php
->withRouting(
    web: __DIR__.'/../routes/web.php',
    commands: __DIR__.'/../routes/console.php',
    health: '/up',
)
```

Theo tài liệu: `/up` trả **200** nếu ứng dụng boot được mà không có exception, ngược lại trả **500**. Nó
**không** tự kiểm database hay Redis. Muốn kiểm thêm, nghe event
`Illuminate\Foundation\Events\DiagnosingHealth` (được bắn khi có request vào route health) và ném
exception nếu phát hiện vấn đề:

```php
// app/Providers/AppServiceProvider.php, trong boot()
use Illuminate\Foundation\Events\DiagnosingHealth;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Event;

Event::listen(function (DiagnosingHealth $event): void {
    DB::select('SELECT 1');   // lỗi kết nối sẽ ném exception, /up trả 500
});
```

⚠️ Cân nhắc kỹ việc đưa database vào health check (phần này là khuyến nghị vận hành chung, tài liệu
Laravel không bàn). Trong Kubernetes, nếu *liveness probe* (probe quyết
định có restart container không) kiểm cả database, thì khi database chậm, **mọi** container bị restart
cùng lúc, biến sự cố nhỏ thành sập toàn bộ. Cách phổ biến: liveness chỉ kiểm process còn trả lời (như
`/up` mặc định); *readiness probe* (quyết định có gửi traffic vào không) mới kiểm phụ thuộc.

### 7.7 Chế độ bảo trì

Khi bắt buộc phải dừng (migration không thể tương thích ngược), dùng `php artisan down` / `php artisan up`
([Chương 23](23-laravel-gioi-thieu.md)). Hai điểm liên quan tới deploy theo tài liệu:

- Mặc định trạng thái bảo trì lưu bằng **file**, nên phải chạy `down` trên **từng** server. Đặt
  `APP_MAINTENANCE_DRIVER=cache` cùng một cache store dùng chung để chỉ cần chạy trên một server.
- `php artisan down --render="errors::503"` render sẵn trang bảo trì, trả về từ rất sớm trong vòng đời
  request, trước khi phần lớn framework được nạp, nên vẫn hoạt động khi dependency đang được cập nhật.

---

## 8. Quan sát hệ thống trên production

### 8.1 Observability là gì

Code đã lên production thì bạn không còn debugger, không `dd()` được. Câu hỏi "vì sao đơn hàng của khách
X lỗi lúc 14:03?" hay "endpoint nào đang chậm?" chỉ trả lời được nếu hệ thống **tự ghi lại** đủ thông
tin. Khả năng hiểu hệ thống từ dữ liệu nó phát ra gọi là *observability*. Ba loại dữ liệu chính:

| Loại | Là gì | Trả lời câu hỏi |
|---|---|---|
| *Log* | Dòng sự kiện có thời gian, mức độ, ngữ cảnh | "Chuyện gì đã xảy ra với request này?" |
| *Metric* | Con số đo theo thời gian (số request, p95 latency, độ dài queue) | "Hệ thống đang khoẻ không, xu hướng ra sao?" |
| *Trace* | Hành trình của một request qua các thành phần (query, job, API), có thời gian từng đoạn | "Request này chậm ở đâu?" |

### 8.2 Log trong Laravel

Laravel ghi log qua thư viện Monolog, cấu hình trong `config/logging.php` theo *channel* (kênh, mỗi kênh
là một đích ghi log):

```php
use Illuminate\Support\Facades\Log;

Log::info('Đặt hàng thành công', ['order_id' => $order->id, 'amount' => $order->amount]);
Log::warning('Thanh toán chậm', ['ms' => $elapsed]);
Log::error('Cổng thanh toán lỗi', ['status' => $response->status()]);
Log::channel('slack')->critical('Hết tiền trong ví hoàn tiền!');
```

Tám mức độ theo RFC 5424, từ nặng tới nhẹ: `emergency`, `alert`, `critical`, `error`, `warning`,
`notice`, `info`, `debug`. Mỗi channel có `level` tối thiểu; log nhẹ hơn mức đó bị bỏ qua.

Cấu hình mặc định của skeleton (`.env.example` Laravel 13.x):

```ini
LOG_CHANNEL=stack
LOG_STACK=single
LOG_LEVEL=debug
```

`stack` là channel gộp: ghi cùng lúc vào các channel liệt kê trong `LOG_STACK` (mặc định chỉ `single`,
tức một file `storage/logs/laravel.log`). Các driver hay dùng:

| Channel | Ghi vào | Ghi chú |
|---|---|---|
| `single` | Một file | File lớn mãi, cần logrotate |
| `daily` | Mỗi ngày một file | Giữ số file theo `LOG_DAILY_DAYS` (mặc định trong config skeleton là 14) |
| `stderr` | Luồng stderr | Hợp với Docker/Kubernetes: nền tảng tự gom log từ stdout/stderr ([Chương 18](18-fpm-nginx-opcache.md)) |
| `slack` | Webhook Slack | Config skeleton đặt `level` là `env('LOG_LEVEL', 'critical')`: chỉ từ mức `critical` khi không đặt `LOG_LEVEL` (`.env.example` đặt `debug`) |
| `syslog`, `papertrail` | Syslog, dịch vụ ngoài | |

Production nên đặt `LOG_LEVEL` cao hơn `debug` (thường `info` hoặc `warning`) để không ngập log.

⚠️ Đừng ghi dữ liệu nhạy cảm vào log: mật khẩu, token, số thẻ, toàn bộ request body. Log thường được
nhiều người và nhiều hệ thống đọc hơn database.

**Context: gắn thông tin chung vào mọi dòng log.** Một dòng log "Thanh toán lỗi" vô dụng nếu không biết
của request nào. Facade `Context` lưu thông tin trong suốt request, tự **gắn vào mọi log** và tự **đi theo
job** được dispatch từ request đó:

```php
// app/Http/Middleware/AddContext.php (theo ví dụ trong tài liệu Laravel)
use Illuminate\Support\Facades\Context;
use Illuminate\Support\Str;

public function handle(Request $request, Closure $next): Response
{
    Context::add('url', $request->url());
    Context::add('trace_id', Str::uuid()->toString());

    return $next($request);
}
```

Mọi `Log::...` trong request có thêm `url` và `trace_id`; job dispatch trong request mang theo context
đó (Laravel "dehydrate" context vào payload job và "hydrate" lại khi job chạy), nên log của job cũng có
cùng `trace_id`. Tìm theo `trace_id` là thấy cả chuỗi sự kiện từ request tới job.

Ở máy dev, `php artisan pail` (package `laravel/pail`, có sẵn trong `require-dev` của skeleton) hiện log
trực tiếp trên terminal, có lọc.

### 8.3 Telescope: kính hiển vi cho môi trường dev

*Laravel Telescope* ghi lại **từng** sự kiện trong ứng dụng: request, exception, log, query database,
job, mail, notification, thao tác cache, tác vụ lịch, `dump()`..., và hiện trên giao diện web `/telescope`.
Rất tiện để thấy một request chạy những query nào (bắt N+1), job nào được dispatch.

```bash
composer require laravel/telescope --dev
php artisan telescope:install
php artisan migrate
```

⚠️ Cài với `--dev` thì theo tài liệu Telescope, sau `telescope:install` phải xoá đăng ký
`TelescopeServiceProvider` khỏi `bootstrap/providers.php` và đăng ký nó trong `register()` của
`AppServiceProvider`, chỉ khi môi trường là `local`. Nếu không, server chạy
`composer install --no-dev` sẽ lỗi vì không tìm thấy class của Telescope.

Tài liệu Telescope mô tả nó là "người bạn đồng hành của môi trường phát triển local". Nếu bật ở môi trường
khác local:

- Dashboard mặc định chỉ mở ở môi trường `local`; ở môi trường khác, quyền xem do gate `viewTelescope`
  (định nghĩa sẵn trong `app/Providers/TelescopeServiceProvider.php`) quyết định, hãy sửa gate này cho chặt.
- Dữ liệu ghi vào bảng `telescope_entries` và **phình rất nhanh**: phải lên lịch `telescope:prune`
  hằng ngày (mặc định xoá bản ghi cũ hơn 24 giờ; `--hours=48` để giữ lâu hơn).
- Ghi mọi sự kiện tốn tài nguyên; với lưu lượng lớn, Pulse hoặc Nightwatch hợp hơn.

### 8.4 Pulse: dashboard sức khoẻ cho production

*Laravel Pulse* không ghi từng sự kiện mà **tổng hợp** số liệu, nên nhẹ hơn và hợp với production.
Dashboard `/pulse` cho thấy: request chậm, query chậm, job chậm, request gọi ra ngoài chậm, exception,
user hoạt động nhiều nhất, tài nguyên server (CPU, RAM, ổ đĩa).

```bash
composer require laravel/pulse
php artisan vendor:publish --provider="Laravel\Pulse\PulseServiceProvider"
php artisan migrate
```

Những điểm vận hành theo tài liệu Pulse:

- Lưu trữ cần MySQL, MariaDB hoặc PostgreSQL (dùng engine khác thì phải có thêm một database loại này
  riêng cho Pulse).
- Dashboard mặc định chỉ mở ở môi trường `local`; production phải định nghĩa gate `viewPulse`.
- Card "Servers" cần chạy `php artisan pulse:check` trên **mỗi** server (process sống lâu, chạy dưới
  Supervisor, và cần `pulse:restart` khi deploy; `php artisan reload` đã gồm lệnh này).
- Lưu lượng lớn: bật *sampling* (chỉ ghi một phần, ví dụ 10% request, dashboard nhân ngược lại và đánh
  dấu `~`), hoặc dùng Redis ingest kèm process `pulse:work`.

### 8.5 Nightwatch

*Laravel Nightwatch* là nền tảng giám sát ứng dụng **dạng dịch vụ** (hosted) do chính đội Laravel làm.
Bạn cài package `laravel/nightwatch` vào ứng dụng; package thu thập số liệu và gửi về Nightwatch thông
qua một agent chạy bằng `php artisan nightwatch:agent` (process sống lâu, chạy dưới process monitor). Dữ
liệu được lưu và phân tích phía Nightwatch, nên ứng dụng không phải chứa thêm bảng giám sát. Chi tiết
gói dịch vụ và cấu hình xem tài liệu tại nightwatch.laravel.com.

### 8.6 Chọn công cụ nào

| | Log (`Log`, `Context`) | Telescope | Pulse | Nightwatch |
|---|---|---|---|---|
| Môi trường chính | Mọi nơi | Local, staging | Production | Production |
| Ghi | Sự kiện bạn chủ động ghi | Mọi sự kiện, chi tiết | Số liệu tổng hợp | Số liệu và sự kiện, gửi ra dịch vụ ngoài |
| Lưu ở đâu | File, stderr, dịch vụ log | Database của app | Database (MySQL/MariaDB/PostgreSQL) | Hạ tầng của Nightwatch |
| Trả lời tốt | "Chuyện gì xảy ra với request X" | "Request này chạy những query nào" | "Endpoint/query/job nào đang chậm" | Giám sát toàn diện, cảnh báo |

Chúng bổ sung cho nhau: log luôn cần; Telescope khi phát triển; Pulse hoặc Nightwatch (hoặc một APM
khác như các dịch vụ thương mại, [Chương 20](20-hieu-nang.md)) trên production.

---

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Test chạy vào database dev/thật và xoá sạch bảng | Đã `config:cache` ở máy dev, config cache thắng `phpunit.xml`; `RefreshDatabase` chạy `migrate:fresh` | `php artisan config:clear` trước khi test (script `composer test` đã làm); database test riêng |
| Test xanh/đỏ tuỳ thứ tự chạy | Dữ liệu còn lại từ test trước | `RefreshDatabase` cho mọi feature test có dùng DB |
| Test xanh trên SQLite, production lỗi trên MySQL | Hai engine khác nhau | Chạy test trên MySQL cùng phiên bản trong CI |
| Test gửi mail thật, gọi API thật | `QUEUE_CONNECTION=sync` chạy job ngay; HTTP không fake | `Mail::fake()`, `Queue::fake()`, `Http::fake()` + `Http::preventStrayRequests()` |
| Gọi `fake()` sau khi code đã chạy | Fake chỉ chặn được lời gọi xảy ra sau khi tráo | Fake ở đầu test (phần Arrange) |
| `Event::fake()` làm factory hỏng (UUID null...) | Listener của model event không chạy | Fake sau khi tạo dữ liệu, hoặc chỉ fake event cần thiết |
| `assertSent` báo không gửi dù code có gửi | Mailable đi qua queue | `assertQueued` hoặc `assertNotOutgoing` |
| `assertJson` pass dù API lộ `password` | `assertJson` chỉ kiểm "có chứa" | `AssertableJson` không gọi `etc()`, hoặc `assertJsonMissingPath` |
| Octane: user B thấy dữ liệu của user A | Singleton/static giữ request, user, tenant | Không giữ dữ liệu theo request trong object sống lâu; dùng `scoped`, closure, tham số method |
| Octane: RAM worker tăng dần | Mảng static tích luỹ | Sửa chỗ rò; `--max-requests` chỉ là lưới an toàn |
| Deploy xong vẫn chạy code cũ | Octane, queue worker, FPM+OPcache chưa nạp lại | `php artisan reload` + reload FPM trong script deploy |
| `queue:restart` không có tác dụng | Cache không dùng chung (`file` nhiều server, `array`) | Cache store dùng chung như Redis |
| Job bị giết giữa chừng khi deploy | `stopwaitsecs` nhỏ hơn thời gian job dài nhất | Đặt `stopwaitsecs` lớn hơn job dài nhất |
| Code cũ lỗi ngay khi migration chạy | Migration đổi tên/xoá cột đang được dùng | Expand/contract qua nhiều lần deploy |
| `env()` trả `null` trên production | `config:cache` đã chạy, `.env` không được nạp | Chỉ gọi `env()` trong `config/*.php` |
| `APP_DEBUG=true` trên production | Quên đổi `.env` | Kiểm trong checklist deploy |
| Bảng `telescope_entries` làm đầy ổ đĩa | Không prune | `telescope:prune` theo lịch, hoặc không bật Telescope trên production |
| Toàn bộ pod bị restart khi DB chậm | Liveness probe kiểm cả database | Liveness nhẹ, kiểm phụ thuộc ở readiness |

## Tóm tắt chương

- Feature test gửi request giả lập qua đúng kernel, middleware, controller; kiểm status, JSON,
  validation (`assertInvalid`), đăng nhập (`actingAs`), và tác dụng phụ trong database.
- `phpunit.xml` đặt môi trường `testing`: SQLite in-memory, cache/session/mail `array`, queue `sync`,
  bcrypt rẻ. Nhớ `config:clear`, và cân nhắc chạy test trên đúng MySQL của production.
- `RefreshDatabase` chạy `migrate:fresh` một lần mỗi process, rồi bọc mỗi test trong transaction và
  rollback. Khi cần dữ liệu thấy được từ connection khác, dùng `DatabaseMigrations`/`DatabaseTruncation`.
- Fake (`Queue`, `Bus`, `Event`, `Mail`, `Notification`, `Http`, `Storage`, thời gian) hoạt động bằng cách
  tráo object trong container qua facade; gọi fake trước khi code chạy, và bật `preventStrayRequests`.
- Octane boot ứng dụng một lần rồi clone nó cho mỗi request, nên nhanh hơn FPM nhưng mọi thứ sống ở cấp
  process (static, singleton tạo lúc boot) có thể rò sang request sau. Dùng `scoped`, closure, helper
  `request()`/`config()`, và `--max-requests`.
- Deploy: `composer install --no-dev -o`, `optimize` trong release mới, `migrate --force` với migration
  tương thích ngược (expand/contract), đổi symlink, reload FPM và `php artisan reload`.
- Queue worker cần Supervisor; `queue:restart` gửi tín hiệu qua cache để worker thoát êm sau job hiện tại.
- `/up` chỉ kiểm ứng dụng boot được; thêm kiểm tra bằng event `DiagnosingHealth`, cẩn thận với liveness.
- Observability: log có `Context` (trace id đi theo cả job), Telescope cho dev, Pulse hoặc Nightwatch cho
  production.

## Câu hỏi tự kiểm tra

1. Khác nhau giữa test trong `tests/Unit` và `tests/Feature` của Laravel là gì? Vì sao tài liệu Laravel
   khuyên viết phần lớn là feature test? (mục 1.2)
2. Vì sao test có thể vô tình chạy vào database thật dù `phpunit.xml` đã đặt `DB_CONNECTION=sqlite`?
   (mục 1.3)
3. Mô tả từng bước `RefreshDatabase` làm cho test đầu tiên và các test sau trong một process. Điều gì xảy
   ra nếu một test chạy `ALTER TABLE` trên MySQL? (mục 3.3, 3.7)
4. Vì sao `Mail::fake()` chặn được mọi lời gọi `Mail::to()->send()` ở khắp ứng dụng mà không phải sửa
   code ứng dụng? Vì sao `$this->mock(PaymentGateway::class)` không có tác dụng với code tự
   `new PaymentGateway()`? (mục 4.2, 4.8)
5. `assertJson(['id' => 1])` và `assertJson(fn (AssertableJson $json) => $json->where('id', 1))` khác
   nhau thế nào khi response có thêm key `password`? (mục 2.4)
6. Giải thích vì sao một singleton nhận `Request` trong constructor chạy đúng trên PHP-FPM nhưng sai trên
   Octane. Nêu ba cách sửa. (mục 6.3, 6.7)
7. Liệt kê những process sống lâu trong một ứng dụng Laravel điển hình, và cách mỗi process nhận code mới
   sau deploy. (mục 6.5, 7.4)
8. `queue:restart` hoạt động thế nào? Vì sao nó không có tác dụng khi cache driver là `array`? (mục 7.4)
9. Bạn cần đổi tên cột `price` thành `unit_price` trên bảng có ứng dụng đang chạy, không được downtime.
   Lên kế hoạch các lần deploy. (mục 7.3)
10. Route `/up` kiểm tra những gì? Có nên cho liveness probe kiểm kết nối database không? (mục 7.6)

## Bài tập

1. **Feature test cho CRUD.** Trong một project Laravel 13 mới, tạo bảng `notes` (`user_id`, `title`,
   `body`) và các route tạo, xem, sửa, xoá note (chỉ chủ sở hữu được sửa/xoá). Viết feature test (PHPUnit
   hoặc Pest) cho: khách bị từ chối, chủ sở hữu thao tác thành công, người khác nhận 403, validation sai
   trả lỗi đúng field. Dùng `RefreshDatabase` và factory. Chạy `php artisan test --profile` và ghi lại
   test nào chậm nhất.
2. **Fake toàn bộ thế giới bên ngoài.** Thêm vào bài 1: khi tạo note, gọi một API giả
   `https://api.moderation.test/check` để kiểm nội dung, rồi dispatch job `IndexNote` và gửi mail cho chủ
   sở hữu. Viết test cho ba trường hợp: API trả "ok", API trả "rejected" (không lưu note, không dispatch
   job), API mất kết nối. Bật `Http::preventStrayRequests()` cho cả bộ test trong `TestCase` gốc.
3. **Săn rò trạng thái.** Mở rộng file mô phỏng ở mục 6.3: thêm một singleton `CurrentTenant` (resolve lúc boot như
   `Greeter`) được middleware đặt tenant theo header của request. Viết vòng lặp ba request với ba tenant khác nhau, trong
   đó request thứ ba **không** gửi header. Cho thấy lỗi xảy ra, rồi sửa bằng hai cách: mô phỏng binding
   `scoped` (xoá instance sau mỗi request) và mô phỏng danh sách `flush`. Chạy cả hai bản, ghi output.
4. **Script deploy.** Viết `deploy.sh` cho một server thật hoặc máy ảo (hoặc một container Docker có
   Nginx + PHP-FPM theo [Chương 18](18-fpm-nginx-opcache.md)): release theo thư mục, `shared/` cho `.env`
   và `storage/`, `optimize` trong release mới, `migrate --force`, đổi symlink nguyên tử, reload FPM,
   `php artisan reload`, kiểm `/up`, giữ 5 release gần nhất, và một lệnh `rollback.sh`. Thêm một
   listener `DiagnosingHealth` kiểm database. Thử deploy trong lúc chạy vòng lặp `curl` liên tục để chứng
   minh không có request nào lỗi.

## Đọc thêm

- Laravel 13.x, Testing: Getting Started: https://laravel.com/docs/13.x/testing
- Laravel 13.x, HTTP Tests: https://laravel.com/docs/13.x/http-tests
- Laravel 13.x, Database Testing: https://laravel.com/docs/13.x/database-testing
- Laravel 13.x, Mocking: https://laravel.com/docs/13.x/mocking
- Laravel 13.x, phần Testing trong các trang Queues, Events, Mail, HTTP Client:
  https://laravel.com/docs/13.x/queues#testing, https://laravel.com/docs/13.x/events#testing,
  https://laravel.com/docs/13.x/mail#testing-mailables, https://laravel.com/docs/13.x/http-client#testing
- Mã nguồn `Illuminate\Foundation\Testing\RefreshDatabase` và `DatabaseTransactionsManager`:
  https://github.com/laravel/framework/tree/13.x/src/Illuminate/Foundation/Testing
- Skeleton Laravel 13.x (`phpunit.xml`, `composer.json`, `config/logging.php`):
  https://github.com/laravel/laravel/tree/13.x
- Pest, Configuring Tests: https://pestphp.com/docs/configuring-tests
- Laravel 13.x, Octane: https://laravel.com/docs/13.x/octane
- Mã nguồn Octane (`Worker.php`, `ApplicationGateway.php`, `config/octane.php`):
  https://github.com/laravel/octane/tree/2.x
- FrankenPHP: https://frankenphp.dev/docs/laravel/ ; RoadRunner: https://roadrunner.dev ; Swoole:
  https://github.com/swoole/swoole-src
- Laravel 13.x, Deployment: https://laravel.com/docs/13.x/deployment
- Laravel 13.x, Queues (Supervisor Configuration, Queue Workers and Deployment):
  https://laravel.com/docs/13.x/queues#supervisor-configuration
- Mã nguồn `ReloadCommand`, `Queue\Console\RestartCommand`, `Queue\Worker`:
  https://github.com/laravel/framework/tree/13.x/src/Illuminate
- Laravel 13.x, Migrations (Forcing Migrations to Run in Production):
  https://laravel.com/docs/13.x/migrations#forcing-migrations-to-run-in-production
- Laravel 13.x, Configuration (Maintenance Mode): https://laravel.com/docs/13.x/configuration#maintenance-mode
- Laravel 13.x, Logging và Context: https://laravel.com/docs/13.x/logging, https://laravel.com/docs/13.x/context
- Laravel 13.x, Telescope và Pulse: https://laravel.com/docs/13.x/telescope, https://laravel.com/docs/13.x/pulse
- Laravel Nightwatch: https://nightwatch.laravel.com/docs
- MySQL 8.4 Reference Manual, Statements That Cause an Implicit Commit:
  https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html
- MySQL 8.4 Reference Manual, Online DDL Operations: https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html
