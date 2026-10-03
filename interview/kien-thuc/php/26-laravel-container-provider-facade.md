# Chương 26. Service container, provider, facade và vòng đời request

> [← Mục lục](README.md) · [← Chương 25: Request, validation, response và view](25-laravel-request-validation-response.md) · [Chương 27: Database trong Laravel: migration, query builder, Eloquent →](27-laravel-database-eloquent.md)

**Bạn sẽ học được:**

- *Dependency injection* (DI) là gì, vì sao code "tự `new` mọi thứ" khó test và khó thay đổi.
- Service container của Laravel: `bind`, `singleton`, `scoped`, `instance`, cách nó tự tạo object bằng
  Reflection, contextual binding và các attribute như `#[Bind]`, `#[Config]`.
- Service provider: `register()` khác `boot()` ở đâu, deferred provider tiết kiệm được gì.
- Facade như `Cache::get()` thật ra là lời gọi gì (`__callStatic`, `getFacadeAccessor`,
  `$resolvedInstance`), real-time facade, và contract.
- Đi từng bước một request từ `public/index.php` tới `terminate()`, và điều gì thay đổi khi chạy
  Octane hoặc queue worker.

**Cần biết trước:** [Chương 09](09-oop-co-ban.md) và [Chương 10](10-oop-nang-cao.md) (interface,
magic method `__callStatic`, attribute, Reflection), [Chương 11](11-namespace-composer.md) (autoload),
[Chương 18](18-fpm-nginx-opcache.md) (PHP-FPM, mô hình share-nothing),
[Chương 23](23-laravel-gioi-thieu.md) và [Chương 24](24-laravel-routing-controller-middleware.md)
(cấu trúc dự án Laravel, route, middleware).

Mọi tên class, method trong chương này được đối chiếu với mã nguồn `laravel/framework` nhánh 13.x
(bản 13.34) và skeleton `laravel/laravel` nhánh 13.x. Các ví dụ dùng container "thật" được chạy bằng
chính file `Illuminate/Container/Container.php` của nhánh đó trên PHP 8.5.

## 1. Dependency injection là gì

### 1.1 Vấn đề: class tự tạo thứ nó cần

Một object hầu như không làm việc một mình. Service đăng ký tài khoản cần một thứ gửi mail; service
đặt hàng cần kết nối database, cổng thanh toán, đồng hồ để biết ngày giờ. Những thứ một class cần để
làm việc gọi là *dependency* (phụ thuộc) của class đó.

Cách viết tự nhiên nhất của người mới là để class tự tạo dependency:

```php
<?php
declare(strict_types=1);

// Cách 1: class tự tạo dependency của nó
final class SmtpMailer
{
    public function send(string $to, string $body): void
    {
        echo "[SMTP] gửi tới {$to}: {$body}", PHP_EOL;   // giả lập gửi mail thật
    }
}

final class TightRegistration
{
    private SmtpMailer $mailer;

    public function __construct()
    {
        $this->mailer = new SmtpMailer();   // tự new: bị "dính chặt" vào SmtpMailer
    }

    public function register(string $email): void
    {
        $this->mailer->send($email, 'Chào mừng!');
    }
}

(new TightRegistration())->register('an@example.com');
// in ra: [SMTP] gửi tới an@example.com: Chào mừng!
```

Chạy thì được, nhưng có ba vấn đề, và chúng lớn dần khi dự án lớn:

1. **Không test được mà không gửi mail thật.** Muốn viết test cho `register()`, bạn không có cách nào
   thay `SmtpMailer` bằng một bản giả, vì nó được `new` cứng bên trong constructor.
2. **Không đổi được cách làm.** Hôm sau công ty chuyển sang gửi mail qua API (Mailgun, SES): bạn phải
   sửa `TightRegistration`, và mọi class khác cũng đang `new SmtpMailer()`.
3. **Dependency bị giấu.** Nhìn chữ ký `__construct()` không tham số, người đọc không biết class này
   cần gửi mail. Phải đọc hết thân class mới biết.

Thuật ngữ cho tình trạng này là *tight coupling* (ghép chặt): class A biết quá cụ thể về class B.

### 1.2 Ý tưởng DI: nhận dependency từ bên ngoài

*Dependency injection* (tiêm phụ thuộc) chỉ là một ý rất đơn giản: **class không tự tạo dependency,
mà nhận nó từ bên ngoài**, thường qua tham số constructor. Kết hợp với việc khai báo kiểu là
*interface* thay vì class cụ thể, ta được:

```php
<?php
declare(strict_types=1);

interface Mailer
{
    public function send(string $to, string $body): void;
}

final class SmtpMailer implements Mailer
{
    public function send(string $to, string $body): void
    {
        echo "[SMTP] gửi tới {$to}: {$body}", PHP_EOL;
    }
}

// Bản giả cho test: không gửi gì, chỉ ghi nhớ
final class FakeMailer implements Mailer
{
    /** @var list<string> */
    public array $sent = [];

    public function send(string $to, string $body): void
    {
        $this->sent[] = $to;
    }
}

final class Registration
{
    // Dependency được "tiêm" vào qua constructor, kiểu là interface
    public function __construct(private Mailer $mailer) {}

    public function register(string $email): void
    {
        $this->mailer->send($email, 'Chào mừng!');
    }
}

// Code chạy thật: chọn SmtpMailer
(new Registration(new SmtpMailer()))->register('an@example.com');
// in ra: [SMTP] gửi tới an@example.com: Chào mừng!

// Code test: chọn FakeMailer, không có mail thật nào bị gửi
$fake = new FakeMailer();
(new Registration($fake))->register('binh@example.com');
var_dump($fake->sent);
// in ra:
// array(1) {
//   [0]=>
//   string(16) "binh@example.com"
// }
```

Ba vấn đề ở mục 1.1 biến mất: test truyền `FakeMailer`; đổi nhà cung cấp mail chỉ cần viết class
mới implement `Mailer`; và chữ ký constructor nói rõ "tôi cần một `Mailer`".

Có ba kiểu tiêm:

| Kiểu | Cách làm | Khi nào dùng |
|---|---|---|
| *Constructor injection* | Tham số `__construct()` | Mặc định. Dependency bắt buộc, object tạo ra là dùng được ngay |
| *Method injection* | Tham số của một method cụ thể | Dependency chỉ cần cho một hành động (Laravel dùng nhiều cho method của controller, `handle()` của job) |
| *Setter injection* | Method `setX()` gọi sau khi tạo | Dependency tuỳ chọn. Ít dùng, vì object có thể ở trạng thái "thiếu" giữa lúc tạo và lúc gọi setter |

Ý "phụ thuộc vào interface, không phụ thuộc vào class cụ thể" có tên riêng là *Dependency Inversion
Principle*, chữ D trong SOLID. DI là kỹ thuật, Dependency Inversion là nguyên tắc thiết kế; hai thứ hay
đi cùng nhau nhưng không phải một.

### 1.3 Ai sẽ `new`? Composition root và sự mệt mỏi của wiring bằng tay

DI không xoá việc `new`, nó dời việc `new` ra một chỗ. Chỗ đó (thường là đầu chương trình) gọi là
*composition root*: nơi lắp ráp toàn bộ đồ thị object. Với app nhỏ, lắp bằng tay là ổn:

```php
$pdo      = new PDO('mysql:host=db;dbname=shop', 'app', 'secret');
$orders   = new OrderRepository($pdo);
$gateway  = new StripeGateway(getenv('STRIPE_KEY'));
$mailer   = new SmtpMailer('smtp.example.com', 587);
$clock    = new SystemClock();
$service  = new CheckoutService($orders, $gateway, $mailer, $clock);
$controller = new CheckoutController($service);
```

Khi app có hàng trăm class, việc này thành gánh nặng: thêm một tham số vào constructor của
`OrderRepository` là phải tìm mọi chỗ `new OrderRepository(...)` để sửa; một số object nên chỉ tạo
một lần (kết nối DB), số khác nên tạo mới mỗi lần; và phải tạo đúng thứ tự (con trước, cha sau).

### 1.4 DI container: tự động hoá việc lắp ráp

*DI container* (còn gọi *IoC container*, *service container*) là một object chuyên làm việc lắp ráp
đó. Bạn nói với nó:

- "Ai cần `Mailer` thì đưa `SmtpMailer`" (đăng ký, *binding*).
- "`PDO` chỉ tạo một lần rồi dùng lại" (*singleton*).
- "Hãy tạo cho tôi một `CheckoutController`" (*resolve*).

Container đọc constructor của `CheckoutController`, thấy cần `CheckoutService`, đọc tiếp constructor
của `CheckoutService`, thấy cần bốn thứ, tạo từng thứ (đệ quy), rồi lắp lại. Bạn không còn viết dòng
`new` nào cho các class "bình thường".

Laravel gọi container của mình là *service container*. Trong một app Laravel, bạn gần như không bao
giờ gọi container trực tiếp: controller, middleware, job, listener, route closure đều được container
tạo, nên chỉ cần khai báo kiểu tham số là dependency tự tới.

```php
// Route closure: Laravel thấy tham số kiểu Registration và tự tạo nó (cùng Mailer bên trong)
Route::post('/register', function (Registration $registration) {
    $registration->register(request('email'));
    return response()->noContent();
});
```

### 1.5 DI khác service locator

Có một cách dùng container trông giống DI nhưng ngược tinh thần: *service locator*. Thay vì nhận
dependency qua constructor, class tự đi "xin" container:

```php
final class Registration
{
    public function register(string $email): void
    {
        app(Mailer::class)->send($email, 'Chào mừng!');   // tự đi lấy: service locator
    }
}
```

| | Dependency injection | Service locator |
|---|---|---|
| Dependency nằm ở đâu | Trong chữ ký constructor/method | Rải rác trong thân method |
| Đọc code có biết class cần gì không | Có, nhìn constructor là thấy | Không, phải đọc hết |
| Test | Truyền bản giả vào constructor | Phải dựng container, đăng ký bản giả vào đó |
| Class có biết container tồn tại không | Không | Có, bị phụ thuộc vào container |

⚠️ Cạm bẫy: rải `app(X::class)` hoặc `resolve(X::class)` khắp domain code. Hãy để class nhận
dependency qua constructor; chỉ gọi container ở "biên" của app (service provider, route closure,
factory). Facade (mục 6) về bản chất cũng là một dạng service locator, nên cũng cần cân nhắc như vậy.

## 2. Service container của Laravel: dùng cơ bản

### 2.1 Container ở đâu trong app

Trong Laravel, class `Illuminate\Foundation\Application` **kế thừa** `Illuminate\Container\Container`.
Nghĩa là "application" và "service container" là **cùng một object**. Bạn chạm vào nó qua nhiều cửa:

| Cách | Dùng ở đâu |
|---|---|
| `$this->app` | Trong service provider (mục 5) |
| `app()` (helper, không tham số) | Bất kỳ đâu; trả về `Container::getInstance()` |
| `app(X::class)`, `resolve(X::class)` | Resolve nhanh một service; `resolve()` chỉ gọi lại `app()` |
| Facade `App` | `App::make(...)`, `App::bind(...)` |
| Type hint `Illuminate\Contracts\Foundation\Application`, `Illuminate\Container\Container` hoặc `Psr\Container\ContainerInterface` | Container tự tiêm chính nó |

Ba thuật ngữ sẽ gặp suốt chương:

- *Abstract*: cái tên bạn dùng để xin, thường là tên interface hoặc class (`Mailer::class`), cũng có thể
  là một chuỗi tuỳ ý (`'cache'`, `'mailer.default'`).
- *Concrete*: công thức tạo ra object cho abstract đó: một tên class, hoặc một closure.
- *Resolve*: hành động "đưa abstract, nhận object". Hàm chính là `make()`.

### 2.2 Chuẩn bị để tự chạy ví dụ

Container của Laravel là một package độc lập (`illuminate/container`), dùng được cả ngoài Laravel.
Các ví dụ dưới đây chạy với file container thật của nhánh 13.x. Để tự chạy:

```bash
# Ở thư mục trống trên máy bạn (cần PHP >= 8.3 và Composer)
composer require illuminate/container
```

rồi trong mỗi file ví dụ thay dòng `require __DIR__ . '/boot.php';` bằng
`require __DIR__ . '/vendor/autoload.php';`. Riêng ví dụ facade ở mục 6.2 dùng class `Facade` nằm trong
package `illuminate/support`, nên cần `composer require illuminate/support` thêm. Trong một dự án Laravel có sẵn, bạn cũng có thể thử từng
dòng trong `php artisan tinker`, khi đó `app()` chính là container.

### 2.3 bind, singleton, instance

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';   // nạp illuminate/container (xem 2.2)

use Illuminate\Container\Container;

interface Mailer { public function name(): string; }
final class SmtpMailer implements Mailer { public function name(): string { return 'smtp'; } }
final class LogMailer implements Mailer { public function name(): string { return 'log'; } }

final class Counter
{
    public static int $created = 0;
    public function __construct() { self::$created++; }
}

$c = new Container();

// 1. bind: mỗi lần make tạo object mới
$c->bind(Mailer::class, SmtpMailer::class);
$m1 = $c->make(Mailer::class);
$m2 = $c->make(Mailer::class);
echo $m1->name(), ' ', var_export($m1 === $m2, true), PHP_EOL;       // smtp false

// 2. bind bằng closure: tự viết công thức tạo
$c->bind(Mailer::class, fn (Container $app): Mailer => new LogMailer());
echo $c->make(Mailer::class)->name(), PHP_EOL;                        // log

// 3. singleton: tạo một lần, các lần sau trả lại đúng object đó
$c->singleton(Counter::class);
$c->make(Counter::class);
$c->make(Counter::class);
echo Counter::$created, PHP_EOL;                                      // 1

// 4. instance: đưa một object có sẵn vào
$mine = new SmtpMailer();
$c->instance('mailer.default', $mine);
var_dump($c->make('mailer.default') === $mine);                       // bool(true)

// 5. bindIf: chỉ đăng ký nếu chưa ai đăng ký
$c->bindIf(Mailer::class, SmtpMailer::class);
echo $c->make(Mailer::class)->name(), PHP_EOL;                        // log (giữ binding cũ)

// 6. bound / has, và cú pháp mảng
var_dump($c->bound(Mailer::class), $c->has('khong-co'));             // bool(true) bool(false)
echo $c[Mailer::class]->name(), PHP_EOL;                              // log
```

Giải thích từng cách:

- `bind($abstract, $concrete)`: đăng ký công thức. `$concrete` là tên class hoặc closure. Closure nhận
  container làm tham số đầu, nên bên trong có thể `$app->make(...)` các dependency con. Bỏ trống
  `$concrete` thì concrete chính là abstract (`bind(Foo::class)`), hữu ích khi chỉ muốn đánh dấu
  singleton. Gọi `bind` lần nữa cho cùng abstract thì **ghi đè** binding cũ.
- `singleton($abstract, $concrete)`: giống `bind`, nhưng object tạo lần đầu được lưu lại, các lần sau
  trả lại đúng object đó. Dùng cho thứ đắt để tạo hoặc cần dùng chung: kết nối DB, HTTP client đã cấu
  hình, cache manager.
- `instance($abstract, $object)`: bạn đã có object rồi, đưa thẳng vào. Mọi lần resolve trả về object
  này. Laravel dùng nó để đưa request hiện tại vào container (`$app->instance('request', $request)`).
- `bindIf`, `singletonIf`, `scopedIf`: chỉ đăng ký khi abstract chưa được đăng ký, tức không ghi đè
  binding mà code khác đã đăng ký trước đó.
- `bound($abstract)` cho biết đã đăng ký chưa; `has()` là tên theo chuẩn PSR-11 (mục 2.6).
- Container implement `ArrayAccess`, nên `$c['x']` tương đương `$c->make('x')`. Code cũ của Laravel
  hay viết `$app['config']`.

Bạn cũng có thể bỏ hẳn tên abstract và để container đọc **kiểu trả về** của closure (docs Laravel
gọi đây là suy ra từ return type):

```php
use Illuminate\Contracts\Foundation\Application;

App::bind(function (Application $app): Transistor {
    return new Transistor($app->make(PodcastParser::class));
});   // đăng ký cho abstract Transistor::class
```

⚠️ Khi nào **không cần** bind: class cụ thể không phụ thuộc interface nào thì container tự tạo được
(mục 3), không cần đăng ký. Docs Laravel nói rõ: không cần bind class vào container nếu nó không phụ
thuộc interface. Chỉ bind khi (a) abstract là interface, (b) cần công thức đặc biệt (tham số
config, khởi tạo nhiều bước), hoặc (c) muốn singleton/scoped.

### 2.4 scoped: singleton trong phạm vi một request hoặc một job

`scoped()` giống `singleton()`: trong một request (hoặc một job queue), mọi lần resolve trả cùng một
object. Khác ở chỗ: khi request hoặc job kết thúc, framework gọi `forgetScopedInstances()` và object
bị bỏ, request sau nhận object mới.

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Container;

final class TenantContext
{
    public static int $created = 0;
    public ?string $tenant = null;
    public function __construct() { self::$created++; }
}
final class AppConfig
{
    public static int $created = 0;
    public function __construct() { self::$created++; }
}

$c = new Container();
$c->singleton(AppConfig::class);
$c->scoped(TenantContext::class);

// "Request" 1
$c->make(TenantContext::class)->tenant = 'acme';
$c->make(AppConfig::class);
echo $c->make(TenantContext::class)->tenant, PHP_EOL;     // acme (cùng object trong request)

// Hết request: framework gọi forgetScopedInstances()
$c->forgetScopedInstances();

// "Request" 2
var_dump($c->make(TenantContext::class)->tenant);          // NULL: object mới, sạch
$c->make(AppConfig::class);
echo TenantContext::$created, ' ', AppConfig::$created, PHP_EOL;   // 2 1
```

Ai gọi `forgetScopedInstances()`? Trên PHP-FPM thì không cần ai gọi: mỗi request là một lần chạy
script mới, container được tạo lại từ đầu (mô hình share-nothing, [Chương 18](18-fpm-nginx-opcache.md)).
Nó quan trọng khi **một process phục vụ nhiều request/job**:

- Queue worker: `QueueServiceProvider` truyền cho worker một callback reset; callback này gọi
  `$app->forgetScopedInstances()` và `Facade::clearResolvedInstances()` (cùng vài việc dọn dẹp khác)
  để mỗi job bắt đầu sạch.
- Laravel Octane (app server giữ app trong bộ nhớ, [Chương 30](30-laravel-testing-octane-deploy.md)):
  reset scoped instance giữa các request.

### 2.5 Bảng so sánh, và "singleton sống bao lâu"

| | `bind` | `singleton` | `scoped` | `instance` |
|---|---|---|---|---|
| Tạo khi nào | Mỗi lần resolve | Lần resolve đầu | Lần resolve đầu trong request/job | Bạn tạo sẵn |
| Lần sau nhận gì | Object mới | Cùng object | Cùng object (tới khi hết request/job) | Cùng object |
| Bên trong là | `bind(..., shared: false)` | `bind(..., shared: true)` | `singleton()` + ghi vào danh sách `$scopedInstances` | Ghi thẳng vào mảng `$instances` |

"Một lần" của singleton là một lần **trong vòng đời container**, mà vòng đời container phụ thuộc cách
app chạy:

| | PHP-FPM | Queue worker | Octane |
|---|---|---|---|
| Container sống bao lâu | Một request | Cả process: hàng nghìn job | Cả worker; mỗi request chạy trên một bản `clone` của application gốc đã boot |
| `bind` | Object mới mỗi lần | Object mới mỗi lần | Object mới mỗi lần |
| `singleton` | Thực chất là "một object mỗi request" | **Một object dùng chung cho mọi job** của process đó | Singleton đã tạo lúc boot (trong provider, hoặc nằm trong danh sách `warm` của `config/octane.php`) **dùng chung cho mọi request**; singleton tạo lần đầu trong một request chỉ nằm trong bản clone và bị bỏ khi request xong |
| `scoped` | Như singleton | Bị bỏ giữa các job | Bị bỏ giữa các request |

⚠️ Hệ quả: trên FPM, nhét dữ liệu của user hiện tại (tenant, user đăng nhập, locale) vào một
singleton có vẻ chạy đúng. Chuyển sang Octane hoặc đưa logic đó vào job queue, request của user B có
thể thấy dữ liệu của user A. State gắn với một request phải là `scoped` (hoặc truyền qua tham số
method), không phải `singleton`.

⚠️ Docs Octane cảnh báo thêm: đừng tiêm cả container hoặc request vào constructor của một singleton.
Nếu singleton đó được tạo trong lúc app boot, nó giữ container/request của lúc đó và dùng tiếp cho
các request sau. Cách sửa docs gợi ý: không dùng
singleton cho object đó, hoặc tiêm một closure `fn () => Container::getInstance()` để luôn lấy
container hiện tại, hoặc truyền request vào tham số method lúc gọi.

### 2.6 make, makeWith, get và lỗi khi resolve

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Container;

final class Report
{
    public function __construct(public int $year) {}
}

$c = new Container();

// makeWith: truyền tay tham số mà container không tự đoán được
echo $c->makeWith(Report::class, ['year' => 2025])->year, PHP_EOL;   // 2025

// Thiếu tham số primitive thì báo lỗi
try {
    $c->make(Report::class);
} catch (Throwable $e) {
    echo get_class($e), PHP_EOL, $e->getMessage(), PHP_EOL;
}

// make() với tham số trên một singleton: KHÔNG lưu và KHÔNG trả bản đã lưu
$c->singleton(Report::class, fn ($app, array $p) => new Report($p['year'] ?? 2000));
$a = $c->make(Report::class);
$b = $c->make(Report::class, ['year' => 1999]);
$d = $c->make(Report::class);
echo $a->year, ' ', $b->year, ' ', var_export($a === $d, true), PHP_EOL;   // 2000 1999 true

// PSR-11: get() ném NotFoundExceptionInterface khi id chưa đăng ký và không tạo được
try {
    $c->get('khong-co');
} catch (Psr\Container\NotFoundExceptionInterface $e) {
    echo get_class($e), PHP_EOL;
}

// in ra:
// 2025
// Illuminate\Contracts\Container\BindingResolutionException
// Unresolvable dependency resolving [Parameter #0 [ <required> int $year ]] in class Report
// 2000 1999 true
// Illuminate\Container\EntryNotFoundException
```

- `make($abstract, $parameters = [])` và `makeWith()` là một (`makeWith` gọi lại `make`). Mảng tham số
  map **theo tên tham số** constructor.
- ⚠️ Khi `make` kèm tham số, container coi đây là một lần build đặc biệt: không trả bản singleton đã
  lưu, và không lưu kết quả làm singleton. Ví dụ trên: `$b` là object riêng, `$a === $d` vẫn đúng.
- `get($id)` và `has($id)` là API của *PSR-11*, chuẩn interface container của PHP-FIG (nhóm
  soạn các chuẩn PSR dùng chung cho thư viện PHP). Container Laravel implement
  `Psr\Container\ContainerInterface`, nên thư viện viết theo PSR-11 dùng được với nó. Khác biệt: `get()`
  bọc lỗi "không tìm thấy" thành `EntryNotFoundException` (implement `NotFoundExceptionInterface`),
  còn `make()` ném thẳng `BindingResolutionException`.

## 3. Bên trong container: auto-resolve bằng Reflection

### 3.1 Container tự tạo được class chưa đăng ký

Laravel gọi khả năng này là *zero configuration resolution*; nhiều tài liệu khác gọi là *auto-wiring*.
Ví dụ với container thật:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Container;

interface Clock { public function today(): string; }
final class FixedClock implements Clock { public function today(): string { return '2026-10-03'; } }

final class OrderRepository {}                       // không constructor
final class Mailer { public function __construct(public string $from = 'no-reply@shop.test') {} }
final class CheckoutService
{
    public function __construct(
        public OrderRepository $orders,
        public Mailer $mailer,
        public Clock $clock,
    ) {}
}

$c = new Container();
$c->singleton(Clock::class, FixedClock::class);       // chỉ đăng ký đúng MỘT thứ: interface

$s = $c->make(CheckoutService::class);                // không đăng ký CheckoutService, repo, mailer
echo get_class($s->orders), ' ', $s->mailer->from, ' ', $s->clock->today(), PHP_EOL;
// in ra: OrderRepository no-reply@shop.test 2026-10-03

// Quên bind interface:
try {
    (new Container())->make(CheckoutService::class);
} catch (Illuminate\Contracts\Container\BindingResolutionException $e) {
    echo $e->getMessage(), PHP_EOL;
}
// in ra: Target [Clock] is not instantiable while building [CheckoutService].

// Class không tồn tại (gõ sai tên, quên use):
try {
    $c->make('App\Services\Paymnet');
} catch (Illuminate\Contracts\Container\BindingResolutionException $e) {
    echo $e->getMessage(), PHP_EOL;
}
// in ra: Target class [App\Services\Paymnet] does not exist.
```

Container làm được điều này nhờ *Reflection*: bộ API có sẵn của PHP cho phép đọc cấu trúc của class,
method, tham số **lúc chương trình đang chạy** ([Chương 10](10-oop-nang-cao.md)). Ba lời gọi là đủ để
hiểu container:

```php
$ref  = new ReflectionClass(CheckoutService::class);
$ctor = $ref->getConstructor();                 // ReflectionMethod, hoặc null nếu không có constructor
foreach ($ctor->getParameters() as $p) {        // từng ReflectionParameter
    echo $p->getName(), ': ', $p->getType(), PHP_EOL;
}
// in ra:
// orders: OrderRepository
// mailer: Mailer
// clock: Clock
```

Có tên kiểu của từng tham số, container chỉ việc `make()` đệ quy từng kiểu đó, rồi `new` class với
danh sách object vừa tạo.

### 3.2 Đường đi của `make()` trong mã nguồn

Đọc `Illuminate\Container\Container` (13.x), một lần `make(X)` đi qua các bước sau. Bạn không cần
thuộc tên hàm, nhưng nên hiểu thứ tự ưu tiên, vì nó giải thích hầu hết hành vi "lạ".

```text
make(X)
 └─ resolve(X)
     1. X là alias? đổi sang tên thật (getAlias)
     2. Bắn callback beforeResolving
     3. Có contextual binding cho class đang build không? (mục 4.1)
     4. Đã có trong $instances và không có tham số/contextual? → TRẢ LUÔN (đường tắt singleton)
     5. getConcrete(X):
          có trong $bindings → closure đã đăng ký
          không có → đọc attribute #[Bind] trên X (mục 4.3)
          không có nữa → concrete chính là X
     6. concrete === X hoặc là closure → build(concrete)
        ngược lại (interface → class) → make(concrete)  (đệ quy)
     7. Áp các extend() (mục 4.4)
     8. Shared (singleton/scoped) và không có tham số/contextual → lưu vào $instances
     9. Bắn callback resolving, afterResolving
```

`build($concrete)`:

```text
build(concrete)
 ├─ concrete là closure → gọi closure($container, $parameters), xong
 ├─ new ReflectionClass(concrete)        lỗi → "Target class [..] does not exist."
 ├─ !isInstantiable() (interface, abstract class, constructor private)
 │                                       → "Target [..] is not instantiable [while building [..]]."
 ├─ không có constructor → new concrete
 └─ có constructor → resolveDependencies(các tham số) → new concrete(...$args)
```

`resolveDependencies()` xử lý từng tham số theo thứ tự ưu tiên:

1. Có giá trị truyền tay qua `make(X, ['ten' => ...])` thì dùng.
2. Tham số có *contextual attribute* như `#[Config('app.timezone')]` thì để attribute quyết định
   (mục 4.2).
3. Kiểu là class/interface: `resolveClass()`. Nếu tham số **có giá trị mặc định** và kiểu đó **chưa
   được bind** (kể cả contextual) thì dùng giá trị mặc định; ngược lại `make()` đệ quy.
4. Kiểu là scalar (`string`, `int`...) hoặc không khai báo kiểu: `resolvePrimitive()` thử lần lượt:
   contextual binding `'$ten'` → giá trị mặc định → variadic thì `[]` → kiểu nullable thì `null` →
   còn lại ném "Unresolvable dependency resolving [...] in class ...".

Điểm 3 dễ gây bất ngờ:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Container;

final class Logger {}
final class Service
{
    // Logger là class cụ thể, container TỰ TẠO được, nhưng tham số có giá trị mặc định
    public function __construct(public ?Logger $logger = null, public string $env = 'prod') {}
}

$c = new Container();
var_dump($c->make(Service::class)->logger);          // NULL: dùng giá trị mặc định
echo $c->make(Service::class)->env, PHP_EOL;          // prod

$c->bind(Logger::class);                              // đăng ký tường minh
var_dump($c->make(Service::class)->logger instanceof Logger);   // bool(true)
```

### 3.3 Tự viết một container mini

Cách tốt nhất để hết thấy container là "phép thuật" là tự viết một cái. Bản dưới đây khoảng 70 dòng,
có `bind`, `singleton`, auto-resolve, và phát hiện vòng phụ thuộc:

```php
<?php
declare(strict_types=1);

final class MiniContainer
{
    /** @var array<string, array{factory: Closure, shared: bool}> */
    private array $bindings = [];
    /** @var array<string, object> */
    private array $instances = [];
    /** @var list<string> class đang build, để phát hiện vòng phụ thuộc */
    private array $buildStack = [];

    public function bind(string $abstract, Closure|string|null $concrete = null, bool $shared = false): void
    {
        $concrete ??= $abstract;
        $factory = $concrete instanceof Closure
            ? $concrete
            // như Container::getClosure(): trùng tên thì build, khác tên thì make (đi tiếp qua binding)
            : fn (self $c): object => $concrete === $abstract ? $c->build($concrete) : $c->make($concrete);
        $this->bindings[$abstract] = ['factory' => $factory, 'shared' => $shared];
        unset($this->instances[$abstract]);
    }

    public function singleton(string $abstract, Closure|string|null $concrete = null): void
    {
        $this->bind($abstract, $concrete, true);
    }

    public function make(string $abstract): object
    {
        if (isset($this->instances[$abstract])) {
            return $this->instances[$abstract];                  // đường tắt của singleton
        }
        $binding = $this->bindings[$abstract] ?? null;
        $object = $binding !== null ? ($binding['factory'])($this) : $this->build($abstract);
        if ($binding !== null && $binding['shared'] === true) {
            $this->instances[$abstract] = $object;
        }
        return $object;
    }

    private function build(string $class): object
    {
        if (in_array($class, $this->buildStack, true)) {
            throw new LogicException('Vòng phụ thuộc: ' . implode(' -> ', [...$this->buildStack, $class]));
        }
        $ref = new ReflectionClass($class);                      // ReflectionException nếu không tồn tại
        if (!$ref->isInstantiable()) {
            throw new LogicException('Target [' . $class . '] is not instantiable');
        }
        $ctor = $ref->getConstructor();
        if ($ctor === null) {
            return new $class();
        }
        $this->buildStack[] = $class;
        try {
            $args = [];
            foreach ($ctor->getParameters() as $param) {
                $type = $param->getType();
                if ($type instanceof ReflectionNamedType && !$type->isBuiltin()) {
                    $args[] = $this->make($type->getName());     // đệ quy
                } elseif ($param->isDefaultValueAvailable()) {
                    $args[] = $param->getDefaultValue();
                } else {
                    throw new LogicException('Unresolvable $' . $param->getName() . ' in ' . $class);
                }
            }
        } finally {
            array_pop($this->buildStack);
        }
        return new $class(...$args);
    }
}

interface Clock { public function today(): string; }
final class FixedClock implements Clock { public function today(): string { return '2026-09-27'; } }
final class Mailer { public function __construct(public string $from = 'no-reply@shop.test') {} }
final class OrderService { public function __construct(public Clock $clock, public Mailer $mailer) {} }
final class NeedsKey { public function __construct(public string $apiKey) {} }
final class A { public function __construct(public B $b) {} }
final class B { public function __construct(public A $a) {} }

$c = new MiniContainer();
$c->singleton(Clock::class, FixedClock::class);

$a = $c->make(OrderService::class);          // không đăng ký OrderService, Mailer: auto-wiring
$b = $c->make(OrderService::class);
var_dump($a === $b);                         // bool(false): OrderService không shared
var_dump($a->clock === $b->clock);           // bool(true): Clock là singleton
echo $a->clock->today(), ' ', $a->mailer->from, PHP_EOL;   // 2026-09-27 no-reply@shop.test

$tries = [
    fn () => (new MiniContainer())->make(OrderService::class),   // Clock chưa bind
    fn () => $c->make(NeedsKey::class),                         // string không default
    fn () => $c->make(A::class),                                // A cần B, B cần A
];
foreach ($tries as $try) {
    try { $try(); } catch (LogicException $e) { echo $e->getMessage(), PHP_EOL; }
}
// Target [Clock] is not instantiable
// Unresolvable $apiKey in NeedsKey
// Vòng phụ thuộc: A -> B -> A
```

So với container thật, bản mini thiếu: alias, contextual binding, attribute, `extend`, callback,
tham số truyền tay, scoped, deferred provider. Nhưng phần lõi `build()` + vòng lặp qua tham số
constructor đúng là ý tưởng của `Container::build()` và `resolveDependencies()`.

### 3.4 Cạm bẫy khi resolve

⚠️ Type hint là interface mà chưa bind (và interface không có attribute `#[Bind]`): lỗi
"Target [X] is not instantiable while building [Y]". Đọc phần "while building" để biết class nào đang
cần nó, rồi thêm binding trong service provider.

⚠️ Tham số scalar không có giá trị mặc định, không nullable, không có contextual binding: lỗi
"Unresolvable dependency resolving [Parameter #0 [ <required> string $apiKey ]] in class ...". Sửa
bằng contextual binding `'$apiKey'` (mục 4.1), attribute `#[Config]` (mục 4.2), hoặc bind cả class
bằng closure tự truyền tham số.

⚠️ Vòng phụ thuộc (A cần B, B cần A): container 13.x **không** kiểm tra vòng như bản mini ở trên
(`CircularDependencyException` chỉ xuất hiện trong docblock `@throws` và một nhánh `catch` của `get()`,
không chỗ nào ném nó). Đệ quy chạy cho tới khi cạn `memory_limit` hoặc tràn stack. Chạy thử với
container thật và `memory_limit` 32M cho kết quả như sau (output minh hoạ, chạy trên php-wasm; số byte
và số dòng trên máy bạn có thể khác):

```text
Fatal error: Allowed memory size of 33554432 bytes exhausted (tried to allocate 262144 bytes)
in .../Illuminate/Container/Container.php on line 1286
```

Gặp fatal error khó hiểu, stack trace toàn `resolveDependencies`/`build`/`resolve` lặp lại, hãy nghĩ
tới vòng phụ thuộc. Cách sửa là thiết kế lại (tách phần dùng chung ra class thứ ba), không phải "bẻ
vòng" bằng service locator.

⚠️ Reflection có chi phí, nhưng thường không phải nút thắt: container chỉ đọc constructor khi
**build**, và singleton chỉ build một lần. Nút thắt thật hay nằm ở việc tạo những object nặng mà
request không dùng tới (giải pháp: deferred provider, mục 5.4; hoặc tiêm closure/factory thay vì
object).

### 3.5 Gọi method với injection: `call()`

Container không chỉ tạo object, nó còn gọi được **method hoặc closure** và tự điền tham số theo kiểu:

```php
use Illuminate\Support\Facades\App;

final class PodcastStats
{
    public function generate(AppleMusic $apple, int $limit = 10): array { /* ... */ }
}

$stats = App::call([new PodcastStats(), 'generate']);                  // AppleMusic tự được tạo
$stats = App::call([new PodcastStats(), 'generate'], ['limit' => 5]);  // tham số truyền tay theo tên
$result = App::call(function (AppleMusic $apple) { /* ... */ });       // closure cũng được
```

Đây là cơ chế khiến method của controller, `handle()` của job, và `boot()` của service provider nhận
được dependency qua tham số (method injection).

## 4. Đăng ký nâng cao

### 4.1 Contextual binding: cùng interface, mỗi nơi một bản

Đôi khi hai class cùng cần một interface nhưng mỗi class cần một bản khác nhau: controller ảnh lưu ở
ổ local, controller video lưu lên S3. Binding thường (`bind(Filesystem::class, ...)`) áp cho mọi nơi;
*contextual binding* (binding theo ngữ cảnh) áp cho riêng class bạn chỉ định. Cú pháp đọc như câu
tiếng Anh: "when X needs Y, give Z".

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Container;

interface Filesystem { public function name(): string; }
final class LocalDisk implements Filesystem { public function name(): string { return 'local'; } }
final class S3Disk implements Filesystem { public function name(): string { return 's3'; } }

final class PhotoController  { public function __construct(public Filesystem $disk) {} }
final class VideoController  { public function __construct(public Filesystem $disk) {} }
final class UploadController { public function __construct(public Filesystem $disk) {} }

final class ReportMailer
{
    public function __construct(public Filesystem $disk, public string $timezone, public int $retries = 3) {}
}

$c = new Container();
$c->bind(Filesystem::class, LocalDisk::class);                 // mặc định cho mọi class

// Riêng Video và Upload nhận S3
$c->when([VideoController::class, UploadController::class])
    ->needs(Filesystem::class)
    ->give(S3Disk::class);

// Tham số primitive: tên biến có dấu $
$c->when(ReportMailer::class)->needs('$timezone')->give('Asia/Ho_Chi_Minh');
$c->when(ReportMailer::class)->needs('$retries')->give(fn () => 5);   // closure được gọi lúc build

echo $c->make(PhotoController::class)->disk->name(), PHP_EOL;    // local
echo $c->make(VideoController::class)->disk->name(), PHP_EOL;    // s3
echo $c->make(UploadController::class)->disk->name(), PHP_EOL;   // s3
$r = $c->make(ReportMailer::class);
echo $r->disk->name(), ' ', $r->timezone, ' ', $r->retries, PHP_EOL;   // local Asia/Ho_Chi_Minh 5
```

Những điều cần để ý:

- `give()` nhận tên class, closure, hoặc giá trị bất kỳ (cho tham số primitive).
- `needs('$ten')` khớp theo **tên biến** của tham số constructor. Đổi tên biến trong constructor là
  binding mất tác dụng một cách im lặng, và bạn nhận lỗi "Unresolvable dependency" (nếu tham số không
  có default) hoặc giá trị default (nếu có).
- Contextual binding được ưu tiên hơn giá trị mặc định: `$retries` có default 3 nhưng nhận 5.
- Có sẵn hai biến thể: `giveConfig('app.timezone')` lấy giá trị từ config, `giveTagged('reports')` lấy
  tất cả binding có tag (mục 4.4).
- Tham số *variadic* (`Filter ...$filters`) nhận mảng: `->needs(Filter::class)->give([NullFilter::class,
  ProfanityFilter::class])` hoặc closure trả về mảng object.

Bên trong, contextual binding được lưu trong mảng `$contextual[class đang build][abstract]`. Container
biết "class đang build" nhờ một ngăn xếp `$buildStack`: khi `build(VideoController)` bắt đầu, tên
class được đẩy vào stack; lúc resolve tham số `Filesystem`, container tra
`$contextual[end($buildStack)][Filesystem]`. Điều này cũng có nghĩa: contextual binding chỉ áp cho
**dependency trực tiếp** của class được chỉ định, không áp xuống các tầng sâu hơn.

### 4.2 Contextual attribute: khai báo ngay trên tham số

Phần lớn contextual binding trong thực tế là "cho tôi disk S3", "cho tôi giá trị config X". Laravel có
sẵn các *attribute* (cú pháp `#[...]`, [Chương 10](10-oop-nang-cao.md)) gắn trực tiếp lên tham số
constructor để làm việc đó mà không cần viết `when()->needs()->give()` trong provider. Tất cả nằm
trong namespace `Illuminate\Container\Attributes`:

| Attribute | Tiêm vào |
|---|---|
| `#[Config('app.timezone')]` | Giá trị config |
| `#[Storage('s3')]` | Disk filesystem |
| `#[Cache('redis')]` | Cache store |
| `#[DB('mysql')]` | Connection database |
| `#[Log('daily')]` | Kênh log |
| `#[Auth('web')]` | Guard xác thực |
| `#[Context('uuid')]` | Giá trị trong Context |
| `#[Give(DatabaseRepository::class)]` | Class cụ thể cho tham số kiểu interface |
| `#[Tag('reports')]` | Mọi binding có tag (tham số `iterable`) |
| `#[RouteParameter('photo')]` | Tham số route (bỏ tên thì lấy theo tên biến) |
| `#[RequestAttribute('organization')]` | Giá trị trong attribute bag của request |
| `#[CurrentUser]` | User đang đăng nhập |

Bạn tự viết được attribute loại này: implement interface `Illuminate\Contracts\Container\ContextualAttribute`
và định nghĩa static method `resolve()`; container gọi `resolve($attribute, $container, $parameter)`
và dùng giá trị trả về.

### 4.3 Binding bằng attribute trên class/interface

Container 13.x còn cho phép khai báo binding ngay trên interface hoặc class, thay cho dòng `bind()`
trong provider:

- `#[Bind(Concrete::class)]`: interface này dùng concrete nào. Lặp lại được, kèm tham số
  `environments` để chọn theo môi trường.
- `#[Singleton]`, `#[Scoped]`: đánh dấu kiểu chia sẻ.
- `#[BindWhen(Concrete::class, closure)]`: chỉ bind khi closure trả `true`. Docs ghi attribute này cần
  PHP 8.5: tham số của attribute phải là biểu thức hằng, và PHP chỉ cho phép closure trong biểu thức
  hằng từ 8.5 (RFC [Closures in constant expressions](https://wiki.php.net/rfc/closures_in_const_expr)).
  Theo RFC, closure đó phải là `static function (...) { ... }`, không có `use`; arrow function
  (`fn () => ...`) không được phép.

Ví dụ chạy với container thật, có cả contextual attribute có sẵn, tự viết, và `#[Give]`:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Attributes\Bind;
use Illuminate\Container\Attributes\Config;
use Illuminate\Container\Attributes\Give;
use Illuminate\Container\Attributes\Singleton;
use Illuminate\Container\Container;
use Illuminate\Contracts\Container\Container as ContainerContract;
use Illuminate\Contracts\Container\ContextualAttribute;

// --- Binding khai báo ngay trên interface ---
#[Bind(RedisPusher::class)]
#[Bind(FakePusher::class, environments: ['local', 'testing'])]
#[Singleton]
interface EventPusher { public function name(): string; }
final class RedisPusher implements EventPusher { public function name(): string { return 'redis'; } }
final class FakePusher implements EventPusher { public function name(): string { return 'fake'; } }

// --- Contextual attribute tự viết ---
#[Attribute(Attribute::TARGET_PARAMETER)]
final class Env implements ContextualAttribute
{
    public function __construct(public string $key, public ?string $default = null) {}

    public static function resolve(self $attribute, ContainerContract $container): ?string
    {
        $env = ['APP_NAME' => 'Shop'];                       // giả lập biến môi trường
        return $env[$attribute->key] ?? $attribute->default;
    }
}

final class ArrayConfig                                     // thay cho config repository của Laravel
{
    /** @param array<string, mixed> $items */
    public function __construct(private array $items) {}
    public function get(string $key, mixed $default = null): mixed { return $this->items[$key] ?? $default; }
}

interface UserRepository {}
final class DatabaseUserRepository implements UserRepository {}

final class Dashboard
{
    public function __construct(
        public EventPusher $pusher,
        #[Config('app.timezone')] public string $timezone,
        #[Env('APP_NAME')] public ?string $appName,
        #[Give(DatabaseUserRepository::class)] public UserRepository $users,
    ) {}
}

$c = new Container();
$c->instance('config', new ArrayConfig(['app.timezone' => 'UTC']));

$env = 'production';
$c->resolveEnvironmentUsing(fn (array|string $envs): bool => in_array($env, (array) $envs, true));

$d = $c->make(Dashboard::class);
echo $d->pusher->name(), ' ', $d->timezone, ' ', $d->appName, ' ', get_class($d->users), PHP_EOL;
// in ra: redis UTC Shop DatabaseUserRepository
var_dump($c->make(EventPusher::class) === $d->pusher);   // bool(true): #[Singleton]

$c2 = new Container();
$env = 'testing';
$c2->resolveEnvironmentUsing(fn (array|string $envs): bool => in_array($env, (array) $envs, true));
echo $c2->make(EventPusher::class)->name(), PHP_EOL;     // fake
```

Cách container xử lý `#[Bind]` (hàm `getConcreteBindingFromAttributes()`): ở lần đầu cần resolve một
abstract **chưa có binding**, container đọc attribute của nó bằng Reflection; tìm được concrete thì tự
gọi `bind`/`singleton`/`scoped` như thể bạn đã viết trong provider, và lần sau không đọc lại nữa.
`#[Bind]` không ghi `environments` thì áp cho mọi môi trường (`'*'`); bản có `environments` khớp môi
trường hiện tại được ưu tiên hơn bản `'*'`.

⚠️ `#[Bind]` cần container biết môi trường hiện tại. Trong app Laravel, bootstrapper
`LoadConfiguration` gọi `$app->resolveEnvironmentUsing(...)` khi nạp config; trước thời điểm đó (hoặc
với `new Container()` trần như ví dụ trên mà không gọi `resolveEnvironmentUsing`) container bỏ qua
`#[Bind]`. Đó là lý do ví dụ phải tự gọi hàm này.

⚠️ Binding tường minh trong provider luôn thắng attribute: `getConcrete()` chỉ đọc attribute khi
abstract chưa có trong `$bindings`. Đây là cách test ghi đè `#[Bind]`.

Nên dùng attribute hay provider? Attribute gọn, binding nằm cạnh interface nên dễ tìm. Provider gom mọi
cấu hình một chỗ, và là lựa chọn duy nhất khi interface nằm trong package bạn không sửa được, hoặc khi
công thức tạo cần logic (đọc config, chọn theo điều kiện phức tạp).

### 4.4 Tagging, extend, callback khi resolve

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Container;

interface Report { public function name(): string; }
final class CpuReport implements Report { public function name(): string { return 'cpu'; } }
final class MemoryReport implements Report { public function name(): string { return 'memory'; } }

final class ReportAggregator
{
    /** @var list<Report> */
    public array $reports;
    public function __construct(Report ...$reports) { $this->reports = $reports; }
}

interface Mailer { public function send(string $to): string; }
final class SmtpMailer implements Mailer { public function send(string $to): string { return "smtp:{$to}"; } }
final class LoggingMailer implements Mailer                      // decorator: bọc Mailer khác
{
    public function __construct(private Mailer $inner) {}
    public function send(string $to): string { return '[log] ' . $this->inner->send($to); }
}

$c = new Container();

// Tagging: gom nhiều binding vào một nhãn
$c->tag([CpuReport::class, MemoryReport::class], 'reports');
foreach ($c->tagged('reports') as $r) {                          // resolve lười, từng phần tử
    echo $r->name(), ' ';
}
echo PHP_EOL;                                                     // cpu memory

// Variadic: give một mảng tên class, hoặc giveTagged
$c->when(ReportAggregator::class)->needs(Report::class)->giveTagged('reports');
echo count($c->make(ReportAggregator::class)->reports), PHP_EOL;  // 2

// extend: sửa/bọc object mỗi khi nó được resolve
$c->bind(Mailer::class, SmtpMailer::class);
$c->extend(Mailer::class, fn (Mailer $m, Container $app): Mailer => new LoggingMailer($m));
echo $c->make(Mailer::class)->send('an'), PHP_EOL;               // [log] smtp:an

// resolving: callback chạy sau khi object được tạo
$c->resolving(CpuReport::class, function (CpuReport $r, Container $app): void {
    echo 'vừa tạo ', $r->name(), PHP_EOL;
});
$c->make(CpuReport::class);                                       // vừa tạo cpu
```

- *Tagging*: `tag([...], 'nhan')` rồi `tagged('nhan')` trả về một iterable (`RewindableGenerator`)
  resolve **lười** từng phần tử khi bạn duyệt tới. Hợp với kiểu "danh sách plugin": nhiều report, nhiều
  rule, nhiều handler cùng interface.
- `extend($abstract, fn ($service, $app) => ...)`: chạy sau khi object được build, trước khi lưu
  singleton; giá trị trả về thay cho object gốc. Dùng để bọc *decorator* (thêm log, cache, đo thời
  gian) quanh service của framework hoặc package mà không sửa code của họ. Nếu abstract đã là singleton
  đã tạo rồi, `extend` áp ngay lên instance đang lưu.
- `beforeResolving`, `resolving`, `afterResolving`: callback chạy quanh mỗi lần resolve (cho một
  abstract, hoặc cho mọi thứ nếu chỉ truyền closure). Chính Laravel dùng `afterResolving` cho HTTP
  Kernel để áp cấu hình middleware trong `bootstrap/app.php` (mục 8.3).
- `rebinding($abstract, fn ($app, $newInstance) => ...)`: chạy khi abstract được đăng ký lại hoặc bị
  ghi đè sau binding ban đầu (bind lại sau khi đã resolve, hoặc thay bằng `instance()`). Hữu ích cho object giữ tham chiếu tới một service có thể bị thay
  (test hay làm vậy).

## 5. Service provider

### 5.1 Provider là gì

Câu hỏi còn bỏ ngỏ từ mục 2: các dòng `bind`, `singleton`, `when()->needs()` viết ở đâu? Câu trả lời
là trong *service provider*: class kế thừa `Illuminate\Support\ServiceProvider`, nơi app (và mọi
package, kể cả chính framework) khai báo service với container và cấu hình những thứ cần có trước khi
request được xử lý. Docs Laravel gọi provider là "nơi trung tâm của mọi việc bootstrap ứng dụng":
mailer, queue, cache, database, routing của framework đều được dựng bởi provider.

Tạo provider:

```bash
# Chạy ở thư mục gốc dự án Laravel
php artisan make:provider RiakServiceProvider
```

Lệnh này tạo `app/Providers/RiakServiceProvider.php` và tự thêm class vào `bootstrap/providers.php`,
file liệt kê provider của app. Skeleton Laravel 13 chỉ có một provider:

```php
<?php

use App\Providers\AppServiceProvider;

return [
    AppServiceProvider::class,
];
```

Tạo provider bằng tay thì phải tự thêm vào mảng này, nếu không Laravel không biết tới nó.

### 5.2 Hai pha: `register()` và `boot()`

Mỗi provider có hai method chính, chạy ở hai pha tách biệt:

| | `register()` | `boot()` |
|---|---|---|
| Khi nào chạy | Pha 1: lần lượt từng provider | Pha 2: chỉ sau khi **mọi** provider đã `register()` xong |
| Nên làm gì | **Chỉ** đăng ký vào container: `bind`, `singleton`, `scoped`, `extend`, contextual binding | Mọi thứ còn lại: route, event listener, observer, macro, view composer, `Gate::define`, cấu hình model |
| Có được dùng service khác không | Không nên: provider khác có thể chưa register | Được: mọi binding đã có |
| Method injection | Không (không tham số) | Có: Laravel gọi `boot()` qua `$app->call([$provider, 'boot'])`, nên type hint tham số được resolve |

```php
<?php
declare(strict_types=1);

namespace App\Providers;

use App\Contracts\PaymentGateway;
use App\Services\StripeGateway;
use Illuminate\Contracts\Foundation\Application;
use Illuminate\Contracts\Routing\ResponseFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Support\ServiceProvider;

final class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        // Chỉ khai báo "công thức"
        $this->app->singleton(PaymentGateway::class, function (Application $app): PaymentGateway {
            return new StripeGateway((string) config('services.stripe.secret'));
        });
    }

    public function boot(ResponseFactory $response): void   // được inject
    {
        Model::preventLazyLoading(! $this->app->isProduction());
        $response->macro('ok', fn (mixed $data) => $response->json(['data' => $data]));
    }
}
```

Vì sao phải tách hai pha? Thử mô phỏng: hai provider, provider thứ nhất (vô tình) dùng service trong
`register()` mà binding của service đó lại do provider thứ hai đăng ký. Đoạn dưới đây là bản mô phỏng
tối giản (không phải code Laravel) dựng trên container thật:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';

use Illuminate\Container\Container;

// Mô phỏng tối giản cách Application chạy provider (không phải code Laravel)
abstract class Provider
{
    public function __construct(protected MiniApp $app) {}
    public function register(): void {}
}

final class MiniApp extends Container
{
    /** @var list<Provider> */
    private array $providers = [];

    /** @param list<class-string<Provider>> $classes */
    public function registerAll(array $classes): void
    {
        foreach ($classes as $class) {                 // Pha 1: register() lần lượt từng provider
            $p = new $class($this);
            echo "register ", $class, PHP_EOL;
            $p->register();
            $this->providers[] = $p;
        }
    }

    public function bootAll(): void
    {
        foreach ($this->providers as $p) {             // Pha 2: boot(), có method injection
            if (method_exists($p, 'boot')) {
                echo "boot ", $p::class, PHP_EOL;
                $this->call([$p, 'boot']);
            }
        }
    }
}

interface Mailer { public function send(string $to): void; }
final class LogMailer implements Mailer
{
    public function send(string $to): void { echo "  (mail tới {$to})", PHP_EOL; }
}
final class Reporter { public function __construct(public Mailer $mailer) {} }

final class ReportServiceProvider extends Provider
{
    public function register(): void
    {
        $this->app->singleton(Reporter::class);
        try {
            $this->app->make(Reporter::class);         // SAI: dùng service trong register()
        } catch (Throwable $e) {
            echo "  lỗi: ", $e->getMessage(), PHP_EOL;
        }
    }

    public function boot(Reporter $reporter): void     // ĐÚNG: dùng trong boot(), được inject
    {
        $reporter->mailer->send('admin@shop.test');
    }
}

final class MailServiceProvider extends Provider
{
    public function register(): void
    {
        $this->app->singleton(Mailer::class, LogMailer::class);
    }
}

$app = new MiniApp();
$app->registerAll([ReportServiceProvider::class, MailServiceProvider::class]);
$app->bootAll();

// in ra:
// register ReportServiceProvider
//   lỗi: Target [Mailer] is not instantiable while building [4, Reporter].
// register MailServiceProvider
// boot ReportServiceProvider
//   (mail tới admin@shop.test)
```

(Số `4` trong thông báo lỗi là id của closure mà `singleton()` tạo ra bọc quanh `Reporter`; container
đẩy id đó vào `$buildStack` khi gọi closure. Con số cụ thể có thể khác trên máy bạn.)

Trong `register()`, `Mailer` chưa có binding vì `MailServiceProvider` chưa chạy. Tới `boot()`, mọi
provider đã register nên `Reporter` resolve được. Thứ tự provider trong danh sách không còn quan
trọng, miễn là bạn chỉ **dùng** service trong `boot()`. Ngay cả khi không lỗi, resolve sớm trong
`register()` vẫn nguy hiểm: object được tạo khi chưa đủ cấu hình, các `extend()`/`resolving()` mà
provider phía sau đăng ký sẽ không áp lên nó, và nếu là singleton thì bản "thiếu" đó bị giữ lại.

⚠️ Docs Laravel nhấn mạnh: trong `register()` **không** đăng ký event listener, route hay bất kỳ chức
năng nào khác ngoài binding.

### 5.3 Thứ tự nạp và các tiện ích

Bootstrapper `RegisterProviders` (mục 8.4) gọi `Application::registerConfiguredProviders()`. Thứ tự
register là:

1. Provider của framework (tên bắt đầu `Illuminate\`), ví dụ `CacheServiceProvider`,
   `DatabaseServiceProvider`, `QueueServiceProvider`...
2. Provider của package, tự phát hiện (*package discovery*): package khai báo provider trong
   `extra.laravel.providers` của `composer.json`, Laravel gom lại và cache ở
   `bootstrap/cache/packages.php`. App muốn tắt phát hiện cho một package thì liệt kê tên package trong
   `extra.laravel.dont-discover` của `composer.json` của app.
3. Provider của app trong `bootstrap/providers.php`.

Ngoài ra, ngay trong constructor `Application` đã register sẵn bốn provider nền: Event, Log, Context,
Routing (`registerBaseServiceProviders()`).

Tiện ích:

- Thuộc tính `$bindings` và `$singletons`: provider chỉ có binding đơn giản có thể khai báo dạng mảng,
  `Application::register()` đọc hai thuộc tính này ngay sau khi gọi `register()`.

  ```php
  final class AppServiceProvider extends ServiceProvider
  {
      /** @var array<class-string, class-string> */
      public $bindings = [ServerProvider::class => DigitalOceanServerProvider::class];

      /** @var array<class-string, class-string> */
      public $singletons = [DowntimeNotifier::class => PingdomDowntimeNotifier::class];
  }
  ```

- `$app->register(SomeProvider::class)` gọi lúc app **đã boot** xong thì `boot()` của provider đó được
  gọi ngay.
- Provider có `booting(fn)` và `booted(fn)` để chạy callback ngay trước và sau `boot()` của chính nó.
  App cũng có `$app->booting(fn)` / `$app->booted(fn)`. Ví dụ: `withRouting()` trong
  `bootstrap/app.php` đăng ký một callback `booting` để register provider nạp file route.

### 5.4 Deferred provider: chỉ nạp khi cần

Một app có vài chục provider. Nếu provider nào cũng register mỗi request (trên FPM là mỗi request!),
ta tốn thời gian cho những service request đó không dùng tới. *Deferred provider* (provider trì hoãn)
giải quyết việc này: provider chỉ được nạp khi có ai resolve một trong các service nó cung cấp.

Điều kiện: provider **chỉ** đăng ký binding (không route, không listener), implement
`Illuminate\Contracts\Support\DeferrableProvider`, và khai báo `provides()`:

```php
<?php
declare(strict_types=1);

namespace App\Providers;

use App\Services\Riak\Connection;
use Illuminate\Contracts\Foundation\Application;
use Illuminate\Contracts\Support\DeferrableProvider;
use Illuminate\Support\ServiceProvider;

final class RiakServiceProvider extends ServiceProvider implements DeferrableProvider
{
    public function register(): void
    {
        $this->app->singleton(Connection::class, function (Application $app): Connection {
            return new Connection($app['config']['riak']);
        });
    }

    /** @return array<int, string> */
    public function provides(): array
    {
        return [Connection::class];
    }
}
```

Cơ chế trong mã nguồn (`Illuminate\Foundation\ProviderRepository`):

1. Laravel đọc *manifest* `bootstrap/cache/services.php`. Nếu chưa có, hoặc danh sách provider đã đổi,
   nó tạo từng provider, hỏi `isDeferred()` (tức `instanceof DeferrableProvider`), rồi ghi lại manifest
   gồm: `eager` (provider nạp mọi request), `deferred` (map `service => provider`), `when` (event kích
   hoạt nạp provider, từ method `when()`).
2. Mỗi request: chỉ `register()` provider `eager`; map `deferred` được đưa vào
   `$app->addDeferredServices()`.
3. Khi code `make(Connection::class)`, `Application::make()` thấy đây là deferred service chưa có
   instance, gọi `loadDeferredProvider()`: register provider đó, rồi boot nó (ngay nếu app đã boot,
   hoặc qua callback `booting` nếu chưa).

Chính framework dùng cơ chế này: `CacheServiceProvider` là deferred, `provides()` trả về `'cache'`,
`'cache.store'`, `'cache.psr6'`, `'memcached.connector'`, `RateLimiter::class`. Request không đụng tới
cache thì `CacheManager` không bao giờ được tạo.

⚠️ Deferred provider mà đặt việc vào `boot()` (đăng ký route, listener): nếu không ai resolve service
của nó thì `boot()` không bao giờ chạy, route/listener "biến mất" mà không báo lỗi.

⚠️ Thêm `provides()` thiếu một binding: resolve binding đó sẽ không kích hoạt nạp provider. Nếu
abstract là interface hoặc chuỗi, bạn nhận lỗi "not instantiable"/"does not exist" dù provider có
đăng ký; nếu là class cụ thể, container lặng lẽ tự build nó bằng auto-resolve, bỏ qua công thức của
bạn.

### 5.5 Provider trên Octane và queue worker

Trên FPM, cả hai pha chạy lại mỗi request. Trên Octane, docs ghi rõ: `register()` và `boot()` chỉ chạy
**một lần** khi worker khởi động, các request sau dùng lại cùng instance application. Queue worker
(`php artisan queue:work`) cũng boot app một lần rồi xử lý nhiều job. Hệ quả: đừng đặt trong
`boot()` những việc phụ thuộc request (đọc user hiện tại, header...), vì lúc đó chưa có request thật,
và kết quả sẽ bị dùng lại cho mọi request.

## 6. Facade

### 6.1 Facade là gì

Code Laravel đầy những lời gọi trông như static method:

```php
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Route;

Route::get('/cache', function () {
    return Cache::get('key');
});
```

`Cache` ở đây là một *facade*. Docs Laravel định nghĩa facade là "giao diện static" tới class có trong
service container, đóng vai *static proxy* (người đại diện): cú pháp gọn như static, nhưng lời gọi
thật được chuyển tới một **object** lấy từ container. Mọi facade của Laravel nằm trong namespace
`Illuminate\Support\Facades` và kế thừa class `Illuminate\Support\Facades\Facade`.

Vì sao không dùng static method thật? Static method thật gắn chặt vào một class (mục 1.1): không thay
được implementation, không mock được trong test. Facade giữ cú pháp tiện của static nhưng phía sau vẫn
là object trong container, nên đổi driver (cache `redis` hay `file`) hay thay bằng bản giả trong test
đều được.

### 6.2 Facade hoạt động bên dưới ra sao

Mở class `Illuminate\Support\Facades\Cache`, bạn sẽ không thấy method `get` nào. Phần quan trọng duy
nhất là:

```php
class Cache extends Facade
{
    protected static function getFacadeAccessor()
    {
        return 'cache';                     // tên binding trong container
    }
}
```

Mọi thứ còn lại nằm ở class cha `Facade` (13.x), gồm vài mảnh:

- `protected static $app`: container, được gán bởi `Facade::setFacadeApplication($app)`.
- `protected static $resolvedInstance`: mảng nhớ các object đã lấy, **key là accessor**. Đây là
  static property của class cha, nên mọi facade con dùng chung một mảng.
- `protected static $cached = true`: có nhớ object vào `$resolvedInstance` hay không.
- `__callStatic($method, $args)`: magic method PHP gọi khi bạn gọi một static method không tồn tại
  ([Chương 10](10-oop-nang-cao.md), mục 1.3).

`Cache::get('user:1')` đi như sau:

```text
Cache::get('user:1')
 │  PHP: Cache không có static method get → gọi Facade::__callStatic('get', ['user:1'])
 ├─ __callStatic: $instance = static::getFacadeRoot()
 │    └─ resolveFacadeInstance(static::getFacadeAccessor())    // accessor = 'cache'
 │         ├─ có static::$resolvedInstance['cache']? → trả luôn
 │         └─ chưa có → static::$app['cache']                   // ArrayAccess → make('cache')
 │                        và (vì $cached = true) lưu vào $resolvedInstance['cache']
 ├─ $instance rỗng → RuntimeException('A facade root has not been set.')
 └─ return $instance->get('user:1')                             // lời gọi thường trên object
```

Phần còn lại là chuyện của object thật. Với cache: `make('cache')` nạp `CacheServiceProvider`
(deferred, mục 5.4), provider này đăng ký singleton `'cache'` là `CacheManager`. `CacheManager` cũng
không có method `get`: magic method `__call()` của nó chuyển tiếp tới store mặc định (một
`Illuminate\Cache\Repository` bọc driver theo `config('cache.default')`), và `Repository::get()` mới
thật sự đọc Redis/file/database.

Chạy thử với **class `Facade` thật** của Laravel 13.x và container thật:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/boot.php';   // nạp illuminate/container + class Facade thật

use Illuminate\Container\Container;
use Illuminate\Support\Facades\Facade;

final class ArrayStore
{
    public static int $created = 0;
    /** @param array<string, mixed> $data */
    public function __construct(private array $data = []) { self::$created++; }
    public function get(string $key, mixed $default = null): mixed { return $this->data[$key] ?? $default; }
    public function put(string $key, mixed $value): void { $this->data[$key] = $value; }
}

// Một facade tự viết: chỉ cần nói "tên binding trong container là gì"
final class Store extends Facade
{
    protected static function getFacadeAccessor(): string
    {
        return 'store';
    }
}

// Chưa gắn container cho facade
try {
    Store::get('k');
} catch (RuntimeException $e) {
    echo $e->getMessage(), PHP_EOL;                    // A facade root has not been set.
}

$app = new Container();
$app->bind('store', fn (): ArrayStore => new ArrayStore());   // bind, KHÔNG phải singleton
Facade::setFacadeApplication($app);                    // việc bootstrapper RegisterFacades làm

Store::put('k', 42);                                   // = $app['store']->put('k', 42)
var_dump(Store::get('k'));                             // int(42)
echo ArrayStore::$created, PHP_EOL;                    // 1: facade đã nhớ instance
var_dump(Store::getFacadeRoot() === $app['store']);    // bool(false): container tạo bản mới

Store::swap(new ArrayStore(['k' => 'fake']));          // nền tảng của shouldReceive()/fake()
var_dump(Store::get('k'));                             // string(4) "fake"
var_dump($app['store']->get('k'));                     // string(4) "fake": swap ghi cả vào container

Facade::clearResolvedInstances();                      // việc làm giữa các request/job
```

Đọc kỹ dòng `bool(false)`: binding `'store'` là `bind` (mỗi lần resolve tạo object mới), nhưng facade
vẫn dùng **một** object vì đã nhớ trong `$resolvedInstance`. Nói cách khác, với facade, một binding
không shared vẫn hành xử gần như singleton cho tới khi `$resolvedInstance` bị xoá. Hầu hết service
mà facade trỏ tới là singleton nên chuyện này hiếm khi gây khác biệt, nhưng cần biết khi tự viết
facade.

Ai xoá `$resolvedInstance`? Bootstrapper `RegisterFacades` gọi `Facade::clearResolvedInstances()` rồi
`setFacadeApplication($app)` mỗi lần app bootstrap. Queue worker gọi `clearResolvedInstances()` giữa
các job (mục 2.4). `Kernel::sendRequestThroughRouter()` gọi `Request::clearResolvedInstance()` để
facade `Request` luôn trỏ tới request mới nhất.

### 6.3 Facade trong test

Vì facade chỉ là đường dẫn tới một object, thay object đó là thay được hành vi:

```php
use Illuminate\Support\Facades\Cache;

public function test_basic_example(): void
{
    Cache::shouldReceive('get')          // thay root bằng một Mockery mock
        ->with('key')
        ->andReturn('value');

    $this->get('/cache')->assertSee('value');
}
```

`shouldReceive()` tạo một mock (thư viện Mockery) rồi gọi `swap($mock)`. Như ví dụ ở 6.2 cho thấy,
`swap()` ghi object mới vào **cả** `$resolvedInstance` **và** container (`$app->instance(accessor, ...)`),
nên code nào lấy service qua container (helper `cache()`, constructor injection bằng contract) cũng
nhận bản mock. Các facade như `Queue::fake()`, `Mail::fake()`, `Event::fake()` dựa trên cùng cơ chế
`swap()`. Chi tiết viết test ở [Chương 30](30-laravel-testing-octane-deploy.md).

### 6.4 Alias: vì sao viết `Cache` không cần `use` trong Blade

Bạn có thể thấy code cũ hoặc view Blade dùng `\Cache::get()` mà không import namespace. Đó là
*alias*. Bootstrapper `RegisterFacades` tạo `Illuminate\Foundation\AliasLoader` từ danh sách alias
(`config('app.aliases')` cộng alias do package khai báo) và gọi `register()`: hàm này đăng ký một
autoloader bằng `spl_autoload_register(..., prepend: true)`, tức xếp **đầu** hàng đợi autoload
([Chương 11](11-namespace-composer.md)). Khi PHP gặp một class chưa biết tên `Cache`, autoloader này
tra bảng alias và gọi `class_alias(Illuminate\Support\Facades\Cache::class, 'Cache')`. Danh sách alias
mặc định nằm trong `Facade::defaultAliases()` (`App`, `Cache`, `DB`, `Route`, `Str`...).

### 6.5 Real-time facade

*Real-time facade* biến **bất kỳ class nào** thành facade mà không cần viết class facade: chỉ cần
thêm tiền tố `Facades\` vào namespace khi `use`.

```php
<?php
declare(strict_types=1);

namespace App\Models;

use Facades\App\Contracts\Publisher;      // thay vì use App\Contracts\Publisher;
use Illuminate\Database\Eloquent\Model;

class Podcast extends Model
{
    public function publish(): void       // không cần nhận Publisher qua tham số nữa
    {
        $this->update(['publishing' => now()]);
        Publisher::publish($this);        // resolve App\Contracts\Publisher từ container
    }
}

// Trong test:
// Publisher::shouldReceive('publish')->once()->with($podcast);
```

Bên dưới: class `Facades\App\Contracts\Publisher` không tồn tại ở đâu cả. Khi PHP cần nó, `AliasLoader`
thấy tên bắt đầu bằng `Facades\`, sinh một file từ stub `facade.stub`: một class kế thừa `Facade` với
`getFacadeAccessor()` trả về `'App\Contracts\Publisher'` (phần tên sau tiền tố). File được ghi vào
`storage/framework/cache/facade-<sha1 của tên>.php` (ghi qua file tạm rồi `rename` để tránh race), các
lần sau chỉ `require` lại.

⚠️ Real-time facade tiện nhưng giấu dependency y như service locator. Dùng ở chỗ code mỏng; với
domain service quan trọng, ưu tiên constructor injection.

### 6.6 Facade, helper hay DI?

Ba cách sau gọi cùng một object:

```php
Cache::get('k');                                    // facade
cache('k');                                         // helper: gọi get() trên chính object đó
public function __construct(private \Illuminate\Contracts\Cache\Repository $cache) {}   // DI
```

Docs Laravel nói facade và helper "không có khác biệt thực tế"; `Cache::shouldReceive()` vẫn bắt được
lời gọi qua `cache()`. Về test, facade cũng mock được như DI. Khác biệt nằm ở thiết kế:

| | Facade / helper | Constructor injection |
|---|---|---|
| Cú pháp | Ngắn, gọi ở đâu cũng được | Phải khai báo constructor |
| Nhìn chữ ký có biết class cần gì | Không | Có |
| Rủi ro | *Scope creep*: class dùng ngày càng nhiều facade mà không ai thấy nó phình | Constructor dài là tín hiệu trực quan "class làm quá nhiều" |
| Dùng ngoài Laravel (package đa framework) | Không | Được, nếu type hint contract (mục 7) |

Docs Laravel nêu rủi ro chính của facade chính là scope creep. Cách làm phổ biến: facade ở controller,
route, code "keo dán" mỏng; constructor injection cho domain service và class nhiều logic.

## 7. Contracts

### 7.1 Contract là gì

*Contract* trong Laravel là tên gọi cho bộ **interface** mô tả các service lõi của framework:
`Illuminate\Contracts\Cache\Repository` (đọc/ghi cache), `Illuminate\Contracts\Queue\Queue` (đẩy job),
`Illuminate\Contracts\Mail\Mailer` (gửi mail)... Mỗi contract có một implementation trong framework.
Toàn bộ contract nằm ở namespace `Illuminate\Contracts` và được phát hành thành package riêng
`illuminate/contracts`, nên một package có thể phụ thuộc vào interface của Laravel mà không cần kéo cả
framework.

Lấy implementation của contract: type hint interface đó ở bất kỳ class nào container tạo (controller,
listener, middleware, job, route closure):

```php
<?php
declare(strict_types=1);

namespace App\Listeners;

use App\Events\OrderWasPlaced;
use Illuminate\Contracts\Redis\Factory;

final class CacheOrderInformation
{
    public function __construct(private Factory $redis) {}

    public function handle(OrderWasPlaced $event): void
    {
        // $this->redis là RedisManager, cùng object mà facade Redis dùng
    }
}
```

### 7.2 Facade, contract và binding là cùng một object

Làm sao type hint `Illuminate\Contracts\Cache\Factory` lại ra đúng object mà facade `Cache` (accessor
`'cache'`) dùng? Nhờ *alias* của container. Constructor `Application` gọi
`registerCoreContainerAliases()`, đăng ký một bảng dạng:

```php
'cache'       => [\Illuminate\Cache\CacheManager::class, \Illuminate\Contracts\Cache\Factory::class],
'cache.store' => [\Illuminate\Cache\Repository::class, \Illuminate\Contracts\Cache\Repository::class,
                  \Psr\SimpleCache\CacheInterface::class],
'config'      => [\Illuminate\Config\Repository::class, \Illuminate\Contracts\Config\Repository::class],
'db'          => [\Illuminate\Database\DatabaseManager::class, \Illuminate\Database\ConnectionResolverInterface::class],
'log'         => [\Illuminate\Log\LogManager::class, \Psr\Log\LoggerInterface::class],
'app'         => [Application::class, \Illuminate\Contracts\Container\Container::class,
                  \Illuminate\Contracts\Foundation\Application::class, \Psr\Container\ContainerInterface::class],
// ... (trích một phần)
```

Mỗi tên bên phải là alias của key bên trái. Bước đầu tiên của `resolve()` là đổi alias sang tên thật
(mục 3.2), nên `make(Contracts\Cache\Factory::class)`, `make(CacheManager::class)`, `app('cache')` và
`Cache::...` đều về cùng binding `'cache'`, cùng một singleton.

| Facade | Accessor (key trong container) | Class thật | Contract tương ứng |
|---|---|---|---|
| `Cache` | `cache` | `Illuminate\Cache\CacheManager` | `Illuminate\Contracts\Cache\Factory` |
| `Cache::driver()` | `cache.store` | `Illuminate\Cache\Repository` | `Illuminate\Contracts\Cache\Repository` |
| `Config` | `config` | `Illuminate\Config\Repository` | `Illuminate\Contracts\Config\Repository` |
| `DB` | `db` | `Illuminate\Database\DatabaseManager` | (không có contract riêng trong bảng của docs) |
| `Log` | `log` | `Illuminate\Log\LogManager` | `Psr\Log\LoggerInterface` (alias) |
| `Route` | `router` | `Illuminate\Routing\Router` | `Illuminate\Contracts\Routing\Registrar` |
| `App` | `app` | `Illuminate\Foundation\Application` | `Illuminate\Contracts\Foundation\Application` |

### 7.3 Khi nào dùng contract

Docs Laravel khá thoải mái: dùng facade hay contract là chuyện khẩu vị của bạn và team, phần lớn app
dùng facade không vấn đề gì, và hai thứ có thể trộn trong cùng app. Contract có lợi rõ ở hai chỗ:

- Viết package dùng chung cho nhiều framework: phụ thuộc `illuminate/contracts` thay vì cả framework.
- Domain service muốn dependency lộ rõ trên constructor (mục 6.6), và muốn test bằng cách truyền
  implementation khác vào constructor mà không cần container.

Contract cũng chính là ví dụ "lập trình theo interface" ở mục 1.2, áp dụng ở quy mô framework: bạn phụ
thuộc `Contracts\Cache\Repository`, còn cache chạy bằng Redis hay file là chuyện cấu hình.

## 8. Vòng đời một request

Giờ ráp mọi mảnh lại: container, provider, facade xuất hiện ở đâu khi một request HTTP đi qua Laravel.
Mô tả dưới đây theo mã nguồn 13.x, trên PHP-FPM.

### 8.1 Toàn cảnh

```text
Nginx ──FastCGI──> PHP-FPM worker chạy public/index.php
  ├─ (1) maintenance.php? ─ vendor/autoload.php
  ├─ (2) bootstrap/app.php: Application::configure()->with...()->create()   [container ra đời]
  └─ (3) $app->handleRequest(Request::capture())
       ├─ make(HttpKernel)  → afterResolving: áp cấu hình withMiddleware
       ├─ (4) Kernel::handle($request)
       │    ├─ instance('request', $request)
       │    ├─ bootstrap: env → config → exceptions → facades
       │    │             → RegisterProviders (register() mọi provider eager)   [REGISTER]
       │    │             → BootProviders     (boot() mọi provider, nạp route)   [BOOT]
       │    ├─ (5) Pipeline qua global middleware
       │    │    └─ Router: tìm route → Pipeline qua middleware của route/group
       │    │         └─ container->make(Controller) → gọi method → chuẩn hoá thành Response
       │    └─ catch Throwable → report + render ; event RequestHandled
       ├─ (6) $response->send() → fastcgi_finish_request()   [client đã nhận đủ response]
       └─ (7) Kernel::terminate() → terminable middleware → $app->terminating callbacks
```

### 8.2 Bước 1: `public/index.php`

Nginx chuyển mọi request không phải file tĩnh tới `public/index.php` ([Chương 18](18-fpm-nginx-opcache.md)).
File này trong skeleton 13.x:

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

- `LARAVEL_START`: mốc thời gian để đo thời lượng request.
- `maintenance.php`: file do `php artisan down` tạo; được kiểm **trước** cả autoloader, để chế độ bảo
  trì tốn ít công nhất.
- `Request::capture()`: dựng object `Illuminate\Http\Request` từ các biến toàn cục `$_GET`, `$_POST`,
  `$_COOKIE`, `$_FILES`, `$_SERVER` ([Chương 15](15-php-va-web.md), [Chương 25](25-laravel-request-validation-response.md)).

### 8.3 Bước 2: `bootstrap/app.php` tạo container

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

`Application::configure()` làm `new Application($basePath)`. Ngoài việc ghi nhận base path,
constructor làm bốn việc:

1. `registerBaseBindings()`: `Container::setInstance($this)` (từ đây `app()` trả về object này), rồi
   `instance('app', $this)` và `instance(Container::class, $this)`.
2. `registerBaseServiceProviders()`: register bốn provider nền Event, Log, Context, Routing.
3. `registerCoreContainerAliases()`: bảng alias ở mục 7.2.
4. `registerLaravelCloudServices()`: hook riêng khi chạy trên Laravel Cloud.

Sau đó `configure()` gọi sẵn `withKernels()` (bind **singleton** `Contracts\Http\Kernel` →
`Foundation\Http\Kernel`, tương tự cho Console Kernel), `withEvents()`, `withCommands()`,
`withProviders()` (ghi nhớ đường dẫn `bootstrap/providers.php`).

⚠️ Thời điểm thực thi của các `with...()` dễ hiểu nhầm. Hầu hết chúng **không chạy ngay**, mà đăng ký
callback chạy sau:

- `withMiddleware(fn)`: đăng ký `afterResolving(HttpKernel::class, ...)`; closure của bạn chạy khi
  Kernel được resolve ở bước 3.
- `withRouting(...)`: đăng ký callback `booting` để register provider nạp file route; route được nạp
  trong pha boot.
- `create()` chỉ trả về `$this->app`.

### 8.4 Bước 3 và 4: `handleRequest()` và `Kernel::handle()`

`Application::handleRequest()` chỉ có ba dòng:

```php
$kernel = $this->make(HttpKernelContract::class);
$response = $kernel->handle($request)->send();
$kernel->terminate($request, $response);
```

`Kernel::handle()` gọi `sendRequestThroughRouter()`, hàm này:

1. `$this->app->instance('request', $request)`: đưa request vào container, rồi
   `Request::clearResolvedInstance()` để facade `Request` không giữ bản cũ.
2. `bootstrap()`: nếu app chưa bootstrap thì chạy lần lượt sáu *bootstrapper* trong
   `Kernel::$bootstrappers`:

   | Bootstrapper | Làm gì |
   |---|---|
   | `LoadEnvironmentVariables` | Đọc `.env` (bỏ qua nếu config đã được cache) |
   | `LoadConfiguration` | Nạp `config/*.php` hoặc file config đã cache; đặt môi trường (`resolveEnvironmentUsing`, mục 4.3) |
   | `HandleExceptions` | Đăng ký error handler, exception handler, shutdown handler |
   | `RegisterFacades` | `Facade::clearResolvedInstances()`, `Facade::setFacadeApplication($app)`, đăng ký `AliasLoader` |
   | `RegisterProviders` | `registerConfiguredProviders()`: `register()` mọi provider eager, ghi nhận deferred (mục 5.3, 5.4) |
   | `BootProviders` | `$app->boot()`: callback `booting`, `boot()` từng provider, callback `booted` |

   Trước và sau mỗi bootstrapper, app bắn event `bootstrapping: <Class>` và `bootstrapped: <Class>`.
3. Đẩy request qua `Pipeline` các *global middleware* rồi tới router.

Mọi `Throwable` văng ra trong quá trình đó được bắt ngay trong `handle()`: `reportException()` (ghi
log) rồi `renderException()` (biến thành response lỗi). Cuối `handle()` bắn event `RequestHandled`.

Thứ tự này giải thích nhiều điều: facade dùng được trong `boot()` của provider (vì `RegisterFacades`
chạy trước `RegisterProviders`), `config()` dùng được trong provider (vì `LoadConfiguration` chạy
trước), còn exception văng ra từ provider cũng được trang lỗi của Laravel xử lý (vì `HandleExceptions`
chạy trước nữa).

### 8.5 Bước 5: middleware, router, controller

Phần này đã học ở [Chương 24](24-laravel-routing-controller-middleware.md); ở đây chỉ nhìn từ góc độ
container:

- Global middleware mặc định trong 13.x gồm `ValidatePathEncoding`, `InvokeDeferredCallbacks`,
  `TrustHosts` (nếu bật), `TrustProxies`, `HandleCors`, `PreventRequestsDuringMaintenance`,
  `ValidatePostSize`, `TrimStrings`, `ConvertEmptyStringsToNull`.
- Middleware khai báo bằng tên class được **container tạo** lúc chạy, nên constructor của middleware
  nhận dependency được.
- Router tìm route khớp, chạy pipeline thứ hai qua middleware của group/route, rồi controller được tạo
  bằng `$container->make(ControllerClass)` (constructor injection), và tham số method được resolve
  (method injection, route model binding).
- Giá trị controller trả về (mảng, model, chuỗi, view...) được chuẩn hoá thành `Response`
  ([Chương 25](25-laravel-request-validation-response.md)), rồi đi ngược ra qua các middleware.

### 8.6 Bước 6 và 7: `send()` và `terminate()`

`send()` (của `Symfony\Component\HttpFoundation\Response`) gửi header và body, rồi nếu có hàm
`fastcgi_finish_request()` (luôn có trên PHP-FPM) thì gọi nó: kết nối với client được đóng, trình duyệt
nhận đủ response, **nhưng worker PHP vẫn chạy tiếp** phần sau.

`Kernel::terminate()` sau đó:

1. Bắn event `Terminating`.
2. Với từng middleware (global và của route) có method `terminate()`, gọi
   `terminate($request, $response)` (*terminable middleware*).
3. `$app->terminate()`: chạy các callback đăng ký bằng `$app->terminating(...)`.
4. Chạy các handler đăng ký bằng `whenRequestLifecycleIsLongerThan()` nếu request vượt ngưỡng thời
   gian.

Hàm `defer()` (namespace `Illuminate\Support`) cũng chạy ở giai đoạn này: closure được gom vào một
collection và được global middleware `InvokeDeferredCallbacks` gọi trong `terminate()` của nó, mặc định
chỉ khi status code < 400 (gọi `->always()` để chạy cả khi lỗi).

⚠️ `terminateMiddleware()` lấy middleware bằng `$this->app->make($name)`, tức một instance **mới**,
không phải instance đã chạy `handle()`. Muốn giữ state giữa `handle()` và `terminate()` thì đăng ký
middleware đó là singleton trong `register()` của provider.

⚠️ Sau `fastcgi_finish_request()` client đã xong nhưng worker FPM **vẫn bận** tới khi `terminate()`
chạy xong, không nhận request khác. Việc nặng hoặc cần retry đưa vào queue
([Chương 29](29-laravel-queue-event-schedule-cache.md)), đừng dồn vào terminate/defer.

Trên FPM, sau bước 7 script kết thúc: container, mọi singleton, mọi `$resolvedInstance` của facade bị
huỷ cùng process request. Request sau lặp lại từ bước 1. Đây là chi phí "boot lại mỗi request" mà
config cache, route cache, deferred provider và OPcache giúp giảm.

### 8.7 Console, queue worker và Octane khác gì

- **Artisan**: file `artisan` gọi `$app->handleCommand($input)`. Kernel console có danh sách
  bootstrapper riêng, nhưng cùng tinh thần: tạo container, register/boot provider, rồi chạy lệnh.
- **Queue worker** (`queue:work`): boot app **một lần**, sau đó xử lý job này tới job khác trong cùng
  process. Giữa các job, callback reset gọi `forgetScopedInstances()` và
  `Facade::clearResolvedInstances()`. Singleton thì **không** bị reset.
- **Octane**: boot app một lần mỗi worker, giữ trong bộ nhớ; mỗi request được xử lý trên application
  đã boot sẵn đó (`Laravel\Octane\Worker` tạo `$sandbox = clone $this->app` cho từng request rồi bỏ
  bản clone khi xong), bỏ qua bước 1, 2 và pha bootstrap. `register()`/`boot()` không chạy lại.
  Octane tự reset state của framework giữa các request, nhưng state do code của bạn tạo (singleton đã
  tạo lúc boot, static property) thì không.

| | PHP-FPM | Queue worker | Octane |
|---|---|---|---|
| Container tạo bao giờ | Mỗi request | Một lần mỗi process | Một lần mỗi worker |
| `register()`/`boot()` chạy | Mỗi request | Một lần | Một lần |
| Singleton của app sống | Một request | Suốt process | Tạo lúc boot: suốt worker; tạo trong request: hết request |
| Scoped bị reset | (Không cần) | Giữa các job | Giữa các request |
| Rủi ro chính | Chi phí boot lặp lại | Rò state giữa job | Rò state giữa request, giữ container/request cũ |

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| "Target [X] is not instantiable while building [Y]" | Type hint interface/abstract class mà chưa bind | Bind trong `register()` của provider, hoặc `#[Bind]` trên interface |
| "Unresolvable dependency resolving [Parameter #0 ...]" | Tham số scalar không default, không nullable, không contextual binding | `when()->needs('$ten')->give(...)`, `#[Config(...)]`, hoặc bind bằng closure |
| "Target class [X] does not exist." | Sai tên class, thiếu `use`, autoload chưa cập nhật | Kiểm tra namespace; `composer dump-autoload` |
| Fatal "Allowed memory size exhausted" khi resolve | Vòng phụ thuộc A → B → A, container không phát hiện | Tách phần dùng chung ra class thứ ba |
| Dữ liệu user này lọt sang user khác trên Octane/queue | Lưu state theo request trong `singleton` hoặc static property | Dùng `scoped`, hoặc truyền qua tham số method |
| Singleton giữ request/container cũ trên Octane | Tiêm `Request`/`Application` vào constructor singleton được tạo lúc boot | Tiêm closure `fn () => Container::getInstance()`, truyền request lúc gọi |
| Resolve service trong `register()` | Provider khác có thể chưa register; extend/resolving đăng ký sau không áp | Chỉ bind trong `register()`, dùng service trong `boot()` |
| Route/listener của deferred provider "biến mất" | `boot()` của deferred provider chỉ chạy khi có người resolve service của nó | Deferred provider chỉ chứa binding |
| Binding trong deferred provider không có tác dụng | Quên liệt kê trong `provides()` | `provides()` phải khớp mọi binding |
| `contextual needs('$ten')` không ăn | Đổi tên biến constructor | Ưu tiên attribute trên tham số; có test cho phần wiring |
| "A facade root has not been set." | Gọi facade khi chưa có app (unit test thuần, script ngoài Laravel) | Dùng test case của Laravel (boot app) hoặc DI |
| `terminate()` của middleware không thấy state từ `handle()` | Kernel `make()` một instance mới để gọi `terminate()` | Đăng ký middleware là singleton |
| Class phình to với hàng chục facade | Facade không làm lộ dependency (scope creep) | Constructor injection cho domain service |
| Rải `app(X::class)` khắp nơi | Service locator, dependency bị giấu | Nhận qua constructor; chỉ dùng `app()` ở biên |

## Tóm tắt chương

- DI: class nhận dependency từ bên ngoài (thường qua constructor, kiểu interface) thay vì tự `new`;
  dễ test, dễ thay. Container tự động hoá việc lắp ráp; service locator là cách dùng container ngược
  tinh thần DI.
- `Application` kế thừa `Container`: app và container là một object. `bind` tạo mới mỗi lần,
  `singleton` = `bind(..., shared: true)`, `scoped` = singleton bị xoá bởi `forgetScopedInstances()`
  giữa request (Octane) và job (queue), `instance` đưa object có sẵn vào.
- "Một lần" của singleton là một lần mỗi vòng đời container: một request trên FPM, cả process trên
  queue worker; trên Octane, singleton tạo lúc boot sống suốt worker, còn singleton tạo trong request
  nằm trong bản clone và bị bỏ khi request xong.
- Auto-resolve: `build()` dùng `ReflectionClass` đọc constructor, `resolveDependencies()` đệ quy
  `make()` theo kiểu tham số; scalar cần contextual binding, default hoặc nullable. Container không phát
  hiện vòng phụ thuộc.
- Contextual binding (`when()->needs()->give()`), contextual attribute (`#[Config]`, `#[Storage]`,
  `#[Give]`...), attribute trên interface (`#[Bind]`, `#[Singleton]`, `#[Scoped]`); tag, `extend`,
  callback `resolving`.
- Provider: `register()` chỉ bind, `boot()` chạy sau khi mọi provider đã register và được method
  injection. Deferred provider (`DeferrableProvider` + `provides()`) chỉ nạp khi service được resolve,
  nhờ manifest `bootstrap/cache/services.php`.
- Facade: `__callStatic` → `getFacadeRoot()` → `resolveFacadeInstance(getFacadeAccessor())` → nhớ
  trong `$resolvedInstance` dùng chung → gọi method trên object thật. `swap()`/`shouldReceive()` thay
  object đó; real-time facade sinh class từ stub khi `use Facades\...`.
- Contract là interface lõi của framework; nhờ alias của container, contract, class thật, key và
  facade trỏ cùng một binding.
- Vòng đời: `index.php` → `bootstrap/app.php` (container ra đời) → `handleRequest` → `Kernel::handle`:
  6 bootstrapper (env, config, exceptions, facades, register, boot) → middleware → router → controller
  → `send()` (`fastcgi_finish_request`) → `terminate()`.

## Câu hỏi tự kiểm tra

1. Nêu ba vấn đề của việc một class tự `new` dependency trong constructor. DI giải quyết từng vấn đề
   thế nào? (mục 1.1, 1.2)
2. DI và service locator khác nhau ở đâu? Facade gần với cái nào hơn? (mục 1.5, 6.6)
3. Trên PHP-FPM và trên Octane, `singleton` khác nhau thế nào về thời gian sống? Vì sao state theo
   user nên là `scoped`? (mục 2.5)
4. `make(Report::class, ['year' => 1999])` trên một singleton có trả về instance đã lưu không, và có lưu
   kết quả không? (mục 2.6)
5. Khi resolve một tham số kiểu class có giá trị mặc định `= null`, lúc nào container dùng `null`, lúc
   nào tự tạo object? (mục 3.2)
6. Vì sao contextual binding cho `VideoController` không ảnh hưởng tới một class mà `VideoController`
   phụ thuộc gián tiếp? (mục 4.1)
7. Vì sao không nên resolve service trong `register()`? Viết lại một ví dụ minh hoạ bằng lời. (mục 5.2)
8. Deferred provider được nạp vào lúc nào? Điều gì xảy ra nếu bạn đăng ký route trong `boot()` của nó?
   (mục 5.4)
9. Mô tả từng bước điều xảy ra khi gọi `Cache::get('k')`, từ `__callStatic` tới object thật. Vì sao
   facade vẫn dùng một object dù binding chỉ là `bind`? (mục 6.2)
10. Kể sáu bootstrapper theo thứ tự và giải thích vì sao facade dùng được trong `boot()` của provider.
    (mục 8.4)

## Bài tập

1. **Container mini nâng cấp.** Lấy container mini ở mục 3.3, thêm: (a) `instance()`; (b) `scoped()`
   kèm `forgetScopedInstances()`; (c) tham số truyền tay `make($abstract, array $parameters)` theo tên
   tham số; (d) contextual binding tối giản `when($class, $abstract, $concrete)` dùng `$buildStack`.
   Viết đoạn kiểm thử in kết quả cho từng tính năng, chạy bằng `php file.php`.
2. **Facade tự làm.** Không dùng Laravel, viết class `Facade` của riêng bạn (có `$resolvedInstance`,
   `swap()`, `clearResolvedInstances()`) trên container mini của bài 1, và hai facade `Clock`
   (`Clock::now()`) và `Mail` (`Mail::send()`). Chứng minh bằng output: (a) hai facade không lẫn
   instance của nhau; (b) `swap()` thay được `Clock` bằng đồng hồ cố định; (c) sau
   `clearResolvedInstances()` facade lấy lại object từ container.
3. **Provider hai pha.** Trong một dự án Laravel 13 (hoặc bằng mô phỏng như mục 5.2), viết
   `PaymentServiceProvider` bind interface `PaymentGateway` theo `config('services.payment.driver')`
   (`stripe` hoặc `fake`), và một `ReportServiceProvider` cần `PaymentGateway` trong `boot()`. Đổi
   thứ tự hai provider trong `bootstrap/providers.php` và giải thích vì sao kết quả không đổi. Sau đó
   biến `PaymentServiceProvider` thành deferred và kiểm tra nội dung `bootstrap/cache/services.php`.
4. **Truy vết vòng đời.** Trong một dự án Laravel 13, ghi log (kèm `microtime(true)`) từ: `register()`
   và `boot()` của một provider, một global middleware (trước và sau `$next`), controller, một
   terminable middleware, một callback `$app->terminating()` và một `defer()`. Ghi log thời điểm từng thứ chạy, gửi một request, và vẽ lại
   sơ đồ mục 8.1 theo log thực tế.

## Đọc thêm

- Laravel 13.x docs: [Service Container](https://laravel.com/docs/13.x/container),
  [Service Providers](https://laravel.com/docs/13.x/providers),
  [Facades](https://laravel.com/docs/13.x/facades),
  [Contracts](https://laravel.com/docs/13.x/contracts),
  [Request Lifecycle](https://laravel.com/docs/13.x/lifecycle),
  [Octane: Dependency Injection and Octane](https://laravel.com/docs/13.x/octane#dependency-injection-and-octane),
  [Package Discovery](https://laravel.com/docs/13.x/packages#package-discovery).
- Mã nguồn `laravel/framework` nhánh 13.x:
  [Container/Container.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Container/Container.php),
  [Foundation/Application.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Application.php),
  [Foundation/Http/Kernel.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Http/Kernel.php),
  [Foundation/ProviderRepository.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/ProviderRepository.php),
  [Support/Facades/Facade.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Support/Facades/Facade.php),
  [Foundation/AliasLoader.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/AliasLoader.php),
  [Foundation/Configuration/ApplicationBuilder.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Configuration/ApplicationBuilder.php).
- Skeleton [`laravel/laravel` 13.x](https://github.com/laravel/laravel/tree/13.x): `public/index.php`,
  `bootstrap/app.php`, `bootstrap/providers.php`.
- [PSR-11: Container interface](https://www.php-fig.org/psr/psr-11/).
- Martin Fowler, [Inversion of Control Containers and the Dependency Injection pattern](https://martinfowler.com/articles/injection.html)
  (bài gốc đặt tên "dependency injection" và so sánh với service locator).
- PHP manual: [Reflection](https://www.php.net/manual/en/book.reflection.php),
  [`__callStatic`](https://www.php.net/manual/en/language.oop5.overloading.php#object.callstatic).
