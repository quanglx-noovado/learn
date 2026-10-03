# Chương 10. OOP nâng cao và các tính năng hiện đại

> [← Mục lục](README.md) · [← Chương 09: OOP cơ bản: class và object](09-oop-co-ban.md) · [Chương 11: Namespace, autoload và Composer →](11-namespace-composer.md)

**Bạn sẽ học được:**

- Magic method là gì, engine gọi chúng lúc nào, và cái giá phải trả khi dùng chúng (nền để đọc hiểu
  Eloquent và Facade của Laravel).
- `self::` khác `static::` thế nào (late static binding), vì sao `new static` có mặt khắp framework.
- Mô hình hoá dữ liệu chặt chẽ bằng enum, `readonly`, property hooks, asymmetric visibility và clone with.
- Đọc cấu trúc code lúc chạy bằng Reflection, tự định nghĩa và đọc attribute, hiểu lazy objects.
- Serialize object đúng cách, và vì sao `unserialize()` dữ liệu từ bên ngoài là lỗ hổng.
- Gắn dữ liệu vào object mà không giữ object sống, bằng `WeakMap` và `WeakReference`.

**Cần biết trước:** [Chương 09: OOP cơ bản](09-oop-co-ban.md) (class, property, visibility, kế thừa,
interface, trait, clone) và [Chương 08: Hàm](08-ham.md) (closure, callable, first-class callable).

Cách chạy ví dụ: lưu thành file `.php` rồi chạy `php ten-file.php`. Ví dụ viết cho PHP 8.5 và output
ghi trong comment là output trên 8.5; mỗi tính năng mới đều ghi rõ có từ bản nào, chạy trên bản cũ hơn
bản đó sẽ báo lỗi. Máy chưa cài PHP thì dùng Docker, chạy trong thư mục chứa file:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

## 1. Magic method

### 1.1 Magic method là gì

*Magic method* là method có tên bắt đầu bằng hai dấu gạch dưới `__` mà bạn không tự gọi: engine PHP
tự gọi nó khi một sự kiện đặc biệt xảy ra với object, ví dụ đọc một property không tồn tại, gọi một
method không tồn tại, dùng object như một chuỗi, gọi object như một hàm. Nhờ vậy class "can thiệp"
được vào hành vi mặc định của ngôn ngữ.

Bạn đã gặp ba magic method ở chương 09: `__construct`, `__destruct`, `__clone`. Phần còn lại:

| Magic method (chữ ký chuẩn) | Engine gọi khi | Mục |
|---|---|---|
| `__get(string $name): mixed` | Đọc property không truy cập được | 1.2 |
| `__set(string $name, mixed $value): void` | Ghi property không truy cập được | 1.2 |
| `__isset(string $name): bool` | `isset()`, `empty()`, `??` trên property không truy cập được | 1.2 |
| `__unset(string $name): void` | `unset()` trên property không truy cập được | 1.2 |
| `__call(string $name, array $arguments): mixed` | Gọi method không truy cập được trên object | 1.3 |
| `static __callStatic(string $name, array $arguments): mixed` | Như trên nhưng gọi kiểu static `Foo::bar()` | 1.3 |
| `__toString(): string` | Object bị dùng như chuỗi | 1.4 |
| `__invoke(...)` | Object bị gọi như hàm `$obj()` | 1.5 |
| `__debugInfo(): array` | `var_dump()`, `print_r()` cần biết in gì | 1.6 |
| `static __set_state(array $properties): object` | Chạy lại code mà `var_export()` sinh ra | 1.6 |
| `__serialize(): array`, `__unserialize(array $data): void` | `serialize()`, `unserialize()` | 11 |
| `__sleep(): array`, `__wakeup(): void` | Cách serialize cũ, *soft-deprecated* từ 8.5 | 11 |

"Không truy cập được" (*inaccessible*) nghĩa là property/method **không được khai báo**, hoặc có khai
báo nhưng **không nhìn thấy từ chỗ đang đứng** (ví dụ `private` mà truy cập từ ngoài class).

Quy tắc chung theo manual:

- Mọi tên method bắt đầu bằng `__` được PHP giữ riêng (*reserved*). Đừng đặt tên method của bạn kiểu
  đó, trừ khi bạn muốn dùng đúng magic method.
- Mọi magic method trừ `__construct`, `__destruct`, `__clone` phải là `public`. Khai báo `private`
  thì PHP phát `E_WARNING` ("must have public visibility").
- Nếu bạn khai báo kiểu cho tham số hoặc giá trị trả về thì phải khớp chữ ký chuẩn ở bảng trên. Sai
  là Fatal error ngay khi class được nạp (từ 8.0; trước đó PHP im lặng). Ví dụ `__get(int $name)`
  báo `Parameter #1 ($name) must be of type string when declared`, `__toString(): int` báo
  `Return type must be string when declared`.
- `__get`, `__set`, `__isset`, `__unset`, `__call` chỉ chạy với object, không được khai báo `static`
  (Fatal error "cannot be static"). Ngược lại `__callStatic` và `__set_state` bắt buộc `static`.
- Tham số của các magic method này không nhận *by reference*.

⚠️ Manual gọi nhóm `__get`/`__set`/`__call` là *overloading*, nhưng nghĩa khác hẳn overloading của
Java hay C# (nhiều method cùng tên, khác tham số). PHP không có overloading kiểu Java: một class không
thể có hai method cùng tên. "Overloading" của PHP là "tạo property/method động qua magic method".

### 1.2 `__get`, `__set`, `__isset`, `__unset`: property "ảo"

Bốn method này cho phép một class trả lời các thao tác trên property mà nó không khai báo. Ứng dụng
kinh điển là một "túi thuộc tính" (*attribute bag*): dữ liệu thật nằm trong một mảng private, bên ngoài
vẫn viết `$obj->ten` như property bình thường. Eloquent model của Laravel chính là một túi thuộc tính
như vậy: cột `name` trong DB được đọc bằng `$user->name` dù class `User` không khai báo `$name`.

Ví dụ in ra mỗi lần engine gọi magic method, để bạn thấy đúng thời điểm:

```php
<?php
declare(strict_types=1);

final class Settings
{
    /** @var array<string, mixed> */
    private array $data = [];

    public string $env = 'local';            // property khai báo, public

    public function __get(string $name): mixed
    {
        echo "  [__get $name]\n";
        return $this->data[$name] ?? null;
    }

    public function __set(string $name, mixed $value): void
    {
        echo "  [__set $name]\n";
        $this->data[$name] = $value;
    }

    public function __isset(string $name): bool
    {
        echo "  [__isset $name]\n";
        return isset($this->data[$name]);
    }

    public function __unset(string $name): void
    {
        echo "  [__unset $name]\n";
        unset($this->data[$name]);
    }
}

$s = new Settings();
$s->timezone = 'Asia/Ho_Chi_Minh';   // [__set timezone]
echo $s->timezone, "\n";             // [__get timezone]  rồi in Asia/Ho_Chi_Minh
var_dump(isset($s->timezone));       // [__isset timezone]  bool(true)
echo $s->locale ?? 'vi', "\n";       // [__isset locale]  rồi in vi
unset($s->timezone);                 // [__unset timezone]
var_dump(isset($s->timezone));       // [__isset timezone]  bool(false)
echo $s->env, "\n";                  // local   (property public đã khai báo: không gọi __get)
$s->data = ['x' => 1];               // [__set data]  (private nhìn từ ngoài = không truy cập được)
```

Những điều rút ra từ output:

- Magic chỉ là "lưới đỡ" cho truy cập **không thành**. `$s->env` là property public đã khai báo nên
  được đọc thẳng, `__get` không hề chạy. Đây là lý do Eloquent model không bao giờ khai báo
  `public $name;` cho cột DB: khai báo vào là chặn mất `__get`, và giá trị không còn đi qua cast,
  accessor của model.
- Property `private` nhìn từ ngoài cũng tính là không truy cập được: `$s->data = [...]` từ ngoài class
  đi vào `__set('data', ...)` chứ không báo lỗi. Bên trong class, `$this->data` vẫn truy cập thẳng.
- Biểu thức `$s->locale ?? 'vi'` gọi `__isset` trước. `__isset` trả `false` nên PHP lấy luôn `'vi'`,
  không gọi `__get`. Nếu `__isset` trả `true` thì PHP gọi tiếp `__get` để lấy giá trị. `empty()` cũng
  vậy: hỏi `__isset`, rồi gọi `__get` để xem giá trị có "rỗng" không.

⚠️ **Bẫy 1: có `__get` mà quên `__isset`.** Khi class không có `__isset`, PHP coi mọi property ảo là
"không tồn tại" trong `isset()` và `empty()`:

```php
<?php
declare(strict_types=1);

final class Bag
{
    /** @var array<string, mixed> */
    private array $data = ['name' => 'An', 'tags' => []];

    public function __get(string $k): mixed { return $this->data[$k] ?? null; }
    public function __set(string $k, mixed $v): void { $this->data[$k] = $v; }
}

$b = new Bag();
echo $b->name, "\n";              // An
var_dump(isset($b->name));        // bool(false)  <- không có __isset nên luôn false
var_dump(empty($b->name));        // bool(true)   <- luôn true
echo $b->name ?? 'khách', "\n";   // An           <- ?? không có __isset để hỏi, gọi thẳng __get
```

Hệ quả: code kiểu `if (isset($obj->name))` hay `if (!empty($obj->name))` luôn coi như property không có
giá trị, dù `__get` trả về giá trị thật. Viết `__get` thì viết luôn `__isset` cho khớp. Eloquent làm đúng điều này: `Model::__isset()` kiểm tra
attribute, nên `isset($user->name)` chạy như mong đợi.

⚠️ **Bẫy 2: sửa mảng lấy qua `__get` không có tác dụng** (*indirect modification*). `__get` trả về
một **bản copy** của giá trị, nên sửa trực tiếp lên kết quả là sửa bản copy:

```php
// tiếp tục với class Bag ở trên
$b->tags[] = 'php';    // Notice: Indirect modification of overloaded property Bag::$tags has no effect
var_dump(count($b->tags));   // int(0)

$tags = $b->tags;      // cách sửa: lấy ra, sửa, gán lại (đi qua __set)
$tags[] = 'php';
$b->tags = $tags;
var_dump(count($b->tags));   // int(1)
```

Cách thứ hai là cho `__get` trả về *reference* bằng cách khai báo `&__get`. Khi đó `$b->tags[] = ...`
sửa thẳng vào phần tử trong mảng `$data`:

```php
<?php
declare(strict_types=1);

final class RefBag
{
    /** @var array<string, mixed> */
    private array $data = ['tags' => []];

    public function &__get(string $k): mixed   // dấu & : trả về reference tới phần tử thật
    {
        return $this->data[$k];
    }
}

$r = new RefBag();
$r->tags[] = 'php';                          // không còn Notice
var_dump($r->tags);                          // array(1) { [0]=> string(3) "php" }
```

Laravel gặp đúng bẫy này với cột JSON được cast sang `array`: `$user->options['theme'] = 'dark'` không
lưu gì vào model, phải gán lại cả mảng (chi tiết ở [chương 27](27-laravel-database-eloquent.md)).

⚠️ **Bẫy 3: đọc lại chính property đó bên trong `__get`.** PHP có cơ chế chống đệ quy: bên trong
`__get('foo')`, đọc `$this->foo` (chưa khai báo) **không** gọi lại `__get` mà phát warning và trả
`null`:

```php
<?php
declare(strict_types=1);

final class Loop
{
    public function __get(string $k): mixed
    {
        return $this->$k;            // đọc lại chính property đang được hỏi
    }
}
var_dump((new Loop())->foo);         // Warning: Undefined property: Loop::$foo ... rồi NULL
```

Liên hệ *dynamic property*: gán vào property chưa khai báo (`$obj->foo = 1` khi class không có `foo`)
sẽ tạo property mới ngay trên object. Việc này bị deprecated từ PHP 8.2. Class có `__set`
không bị ảnh hưởng: phép gán đi vào `__set`, không tạo dynamic property nào. Đó là cách hợp lệ để có
"property tự do" ngoài `stdClass` và attribute `#[\AllowDynamicProperties]` (mục 9.4).

### 1.3 `__call` và `__callStatic`: method "ảo"

`__call($name, $arguments)` chạy khi gọi một method không truy cập được trên object;
`__callStatic($name, $arguments)` chạy khi gọi kiểu static `TenClass::method()`. `$name` là tên method
đã gọi (giữ nguyên hoa thường), `$arguments` là mảng tham số theo thứ tự.

Ví dụ: repository có các method `findByXxx` mà không phải viết từng method.

```php
<?php
declare(strict_types=1);

final class UserRepository
{
    /** @var list<array{id: int, email: string, city: string}> */
    private array $rows = [
        ['id' => 1, 'email' => 'an@example.com',   'city' => 'Hà Nội'],
        ['id' => 2, 'email' => 'binh@example.com', 'city' => 'Huế'],
        ['id' => 3, 'email' => 'chi@example.com',  'city' => 'Hà Nội'],
    ];

    /** @return list<array{id: int, email: string, city: string}> */
    public function __call(string $name, array $arguments): array
    {
        // Chỉ nhận tên dạng findByXxx với đúng 1 tham số; tên lạ thì báo lỗi rõ ràng
        if (!str_starts_with($name, 'findBy') || count($arguments) !== 1) {
            throw new BadMethodCallException("Method {$name} không tồn tại");
        }
        $column = strtolower(substr($name, 6));          // findByCity -> city
        return array_values(array_filter(
            $this->rows,
            fn(array $row): bool => ($row[$column] ?? null) === $arguments[0],
        ));
    }

    public static function __callStatic(string $name, array $arguments): mixed
    {
        // Gọi kiểu static: tạo instance rồi chuyển tiếp sang __call
        return (new self())->$name(...$arguments);
    }
}

$repo = new UserRepository();
echo count($repo->findByCity('Hà Nội')), "\n";              // 2
echo $repo->findByEmail('binh@example.com')[0]['id'], "\n"; // 2
echo count(UserRepository::findByCity('Huế')), "\n";        // 1   (đi qua __callStatic)
var_dump(method_exists($repo, 'findByCity'));               // bool(false)
var_dump(is_callable([$repo, 'findByCity']));               // bool(true)

try {
    $repo->delete(1);
} catch (BadMethodCallException $e) {
    echo $e->getMessage(), "\n";                            // Method delete không tồn tại
}
```

Mẫu "nhận lời gọi rồi chuyển sang object khác" gọi là *forwarding* (chuyển tiếp). Laravel dùng nó ở
khắp nơi, có hẳn trait `ForwardsCalls`. `User::where('active', 1)` không phải method static có thật:
nó đi qua `Model::__callStatic`, tạo một instance `User`, rồi `__call` chuyển lời gọi sang query
builder. Mục 2.5 tự dựng lại cơ chế này. Facade (`Cache::get('key')`) cũng là `__callStatic`:
`Facade::__callStatic` lấy object thật từ service container rồi gọi method trên object đó
([chương 26](26-laravel-container-provider-facade.md)).

⚠️ Những điểm hay vấp:

- `method_exists()` trả `false` cho method ảo, `is_callable()` trả `true` (vì class có `__call`). Code
  kiểm tra "object có method này không" cần chọn đúng hàm.
- `__call` nhận **mọi** tên. Không kiểm tra tên thì gõ sai `$repo->fndByCity(...)` cũng không lỗi.
  Luôn ném `BadMethodCallException` cho tên không hỗ trợ, như ví dụ trên.
- Gọi kiểu static **từ bên trong một method thường** (đang có `$this`) thì PHP gọi `__call` chứ không
  phải `__callStatic`:

```php
<?php
declare(strict_types=1);

class Demo
{
    public function __call(string $name, array $args): mixed
    {
        echo "__call($name)\n";
        return null;
    }

    public static function __callStatic(string $name, array $args): mixed
    {
        echo "__callStatic($name)\n";
        return null;
    }

    public function fromInstance(): void
    {
        self::missing();     // đang có $this -> __call, KHÔNG phải __callStatic
    }

    public static function fromStatic(): void
    {
        self::missing();     // không có $this -> __callStatic
    }

    private function secret(): void {}
}

(new Demo())->fromInstance();   // __call(missing)
Demo::fromStatic();             // __callStatic(missing)
Demo::missing();                // __callStatic(missing)
(new Demo())->secret();         // __call(secret)   method private gọi từ ngoài
```

### 1.4 `__toString` và interface `Stringable`

`__toString()` quyết định object trở thành chuỗi gì khi bị dùng như chuỗi: `echo`, nội suy trong chuỗi
`"...$obj..."`, nối chuỗi bằng `.`, ép kiểu `(string)`. Từ PHP 8.0, class nào có `__toString()` thì tự
động implement interface `Stringable`; manual vẫn khuyên viết `implements Stringable` cho rõ ý.

```php
<?php
declare(strict_types=1);

final class Money
{
    public function __construct(private int $amount, private string $currency) {}

    public function __toString(): string
    {
        return number_format($this->amount, 0, ',', '.') . ' ' . $this->currency;
    }
}

$m = new Money(1500000, 'VND');
echo $m, "\n";                          // 1.500.000 VND
echo "Tổng: $m\n";                      // Tổng: 1.500.000 VND
$label = 'Giá ' . $m;                   // nối chuỗi cũng gọi __toString
var_dump($m instanceof Stringable);     // bool(true)  dù không viết "implements Stringable"

function show(string $text): void { echo $text, "\n"; }
try {
    show($m);                           // strict_types=1: object không được nhận là string
} catch (TypeError $e) {
    echo get_class($e), "\n";           // TypeError
}

function show2(string|Stringable $text): void { echo $text, "\n"; }
show2($m);                              // 1.500.000 VND
show((string) $m);                      // 1.500.000 VND  (ép kiểu tường minh)
```

⚠️ Với `declare(strict_types=1)`, tham số kiểu `string` **không** nhận object có `__toString`. Muốn
nhận cả hai thì khai báo `string|Stringable` (manual khuyên đúng cách này), hoặc ép `(string)` ở chỗ
gọi. Không có strict_types thì PHP tự gọi `__toString` để chuyển đổi.

Từ PHP 7.4, `__toString()` được phép ném exception (trước đó là fatal error). Dù vậy, đừng nhét logic
có thể hỏng (query DB, gọi API) vào `__toString`: nó bị gọi ngầm ở những chỗ người đọc code không ngờ.

### 1.5 `__invoke`: object gọi được như hàm

Class có `__invoke()` thì object của nó là một *callable*: gọi được bằng `$obj(...)`, truyền được vào
mọi chỗ nhận callable (`usort`, `array_map`, tham số kiểu `callable`). Khác closure ở chỗ object này có
tên class, có constructor nhận cấu hình, có thể implement interface và được inject.

```php
<?php
declare(strict_types=1);

final class SortBy
{
    public function __construct(private string $key) {}

    /**
     * @param array<string, mixed> $a
     * @param array<string, mixed> $b
     */
    public function __invoke(array $a, array $b): int
    {
        return $a[$this->key] <=> $b[$this->key];
    }
}

$users = [
    ['name' => 'Chi',  'age' => 31],
    ['name' => 'An',   'age' => 25],
    ['name' => 'Bình', 'age' => 28],
];

usort($users, new SortBy('age'));                       // object dùng làm callback
echo implode(', ', array_column($users, 'name')), "\n"; // An, Bình, Chi

$byName = new SortBy('name');
var_dump(is_callable($byName));                         // bool(true)
echo $byName(['name' => 'A'], ['name' => 'B']), "\n";   // -1   gọi object như hàm
```

Laravel dùng `__invoke` cho *single action controller*: controller chỉ có một method `__invoke`, và
route trỏ thẳng vào tên class (`Route::post('/invoices', SendInvoiceController::class)`), chi tiết ở
[chương 24](24-laravel-routing-controller-middleware.md).

### 1.6 `__debugInfo` và `__set_state`

`__debugInfo()` trả về mảng mà `var_dump()` sẽ in thay cho các property thật. Không có method này thì
`var_dump()` in mọi property, kể cả `private`. Ứng dụng thường gặp: che bí mật khi debug.

```php
<?php
declare(strict_types=1);

final class DbConfig
{
    public function __construct(
        private string $host,
        private string $user,
        private string $password,
    ) {}

    /** @return array<string, string> */
    public function __debugInfo(): array
    {
        return ['host' => $this->host, 'user' => $this->user, 'password' => '***'];
    }
}

$c = new DbConfig('db.internal', 'app', 's3cr3t');
var_dump($c);
// object(DbConfig)#1 (3) {
//   ["host"]=>
//   string(11) "db.internal"
//   ["user"]=>
//   string(3) "app"
//   ["password"]=>
//   string(3) "***"
// }
print_r($c);      // cũng dùng __debugInfo: [password] => ***
echo "\n";
var_export($c);   // KHÔNG dùng __debugInfo: in ra 'password' => 's3cr3t'
```

⚠️ `__debugInfo` chỉ đổi cái mà `var_dump`/`print_r` hiển thị, không phải lớp bảo vệ dữ liệu.
`var_export()`, `serialize()`, ép `(array) $c` vẫn lộ giá trị thật. Muốn mật khẩu không lọt vào stack
trace của exception thì dùng attribute `#[\SensitiveParameter]` (mục 9.4). Từ PHP 8.5, `__debugInfo()`
trả `null` bị deprecated; muốn "không in gì" thì trả `[]`.

`__set_state(array $properties)` là method **static** dùng cho `var_export()`. Hàm này in ra **code
PHP** tạo lại giá trị; với object, code đó có dạng `\DbConfig::__set_state(array(...))` như output ở
trên. Chạy lại đoạn code đó (ví dụ file cache sinh bằng `var_export`) thì class phải có
`__set_state`, nếu không sẽ ném `Error`. Hiếm khi bạn cần viết method này.

### 1.7 Khi nào nên dùng magic

Magic method đổi sự tiện lợi lấy những thứ sau:

- **IDE và công cụ phân tích tĩnh "mù"**: PHPStan, Psalm, IDE không biết `$repo->findByCity()` hay
  `$user->name` có tồn tại không. Phải bù bằng PHPDoc (`@property`, `@method`) hoặc plugin (Larastan
  cho Laravel, [chương 21](21-chat-luong-code.md)).
- **Lỗi đánh máy không bị bắt**: `$user->nmae` không lỗi lúc viết code, chỉ ra kết quả sai lúc chạy.
- **Chậm hơn** truy cập trực tiếp: mỗi lần đi qua magic là thêm một lời gọi hàm. Không đáng kể với vài
  lần mỗi request, đáng kể trong vòng lặp hàng trăm nghìn lần.
- **Khó đọc**: người đọc phải biết class có magic mới hiểu dòng code chạy đi đâu.

```php
/**
 * PHPDoc giúp IDE và PHPStan "nhìn thấy" property/method ảo:
 *
 * @property string $timezone
 * @method list<array{id: int, email: string, city: string}> findByCity(string $city)
 */
final class UserRepository { /* ... */ }
```

Dùng magic khi nó thật sự là bản chất của class: proxy và decorator chuyển tiếp lời gọi, ORM kiểu
Active Record, DSL. Với "property có logic khi đọc/ghi", từ PHP 8.4 hãy dùng property hooks (mục 5)
thay cho `__get`/`__set`: IDE hiểu, có kiểu, không cần mảng ẩn.

## 2. Late static binding: `self::` và `static::`

### 2.1 Vấn đề: `self::` chốt cứng lúc viết code

Ở chương 09 bạn đã dùng `self::` để gọi method static và hằng của chính class. `self` luôn là **class
nơi method được định nghĩa**, cố định ngay từ khi viết code, bất kể sau này method được gọi qua class
con nào. Điều này gây khó khi viết class cha dùng chung cho nhiều class con: class cha muốn tạo "object
của class đang được dùng", nhưng `self` chỉ biết chính nó.

```php
<?php
declare(strict_types=1);

class Model
{
    public static function createSelf(): self     { return new self(); }
    public static function create(): static       { return new static(); }
    public static function tableSelf(): string    { return self::table(); }
    public static function tableStatic(): string  { return static::table(); }
    protected static function table(): string     { return 'models'; }

    public static function names(): string
    {
        return static::class . ' | ' . get_called_class() . ' | ' . self::class . ' | ' . __CLASS__;
    }
}

class User extends Model
{
    protected static function table(): string     { return 'users'; }
}

echo get_class(User::createSelf()), "\n";   // Model   <- self = class chứa dòng code
echo get_class(User::create()), "\n";       // User    <- static = class được gọi
echo User::tableSelf(), "\n";               // models
echo User::tableStatic(), "\n";             // users
echo Model::tableStatic(), "\n";            // models
echo User::names(), "\n";                   // User | User | Model | Model
```

### 2.2 `static::` là class được gọi lúc chạy

*Late static binding* (gắn static muộn) là cơ chế để `static::` trỏ tới **class được gọi lúc chạy**
thay vì class chứa dòng code. "Muộn" vì PHP chỉ biết đó là class nào khi code thật sự chạy. Trong ví
dụ trên, `User::create()` chạy code nằm trong `Model`, nhưng `static` là `User`, nên `new static()`
tạo ra `User`.

Các cách viết liên quan:

| Viết | Nghĩa | Ví dụ trên, gọi qua `User::` |
|---|---|---|
| `self::`, `self::class`, `__CLASS__` | Class nơi method được định nghĩa | `Model` |
| `static::`, `static::class`, `get_called_class()` | Class được gọi (lúc chạy) | `User` |
| `parent::` | Class cha của class chứa dòng code | |
| `new static()` | Tạo object của class được gọi | object `User` |
| Kiểu trả về `static` (8.0) | "Trả về object của đúng class được gọi" | |

Trong method thường (không static), "class được gọi" là class của object `$this`:

```php
<?php
declare(strict_types=1);

class Shape
{
    public function describe(): string
    {
        return static::class . ' có ' . static::sides() . ' cạnh';   // static = class của $this
    }
    public static function sides(): int { return 0; }
}
final class Triangle extends Shape
{
    public static function sides(): int { return 3; }
}
echo (new Triangle())->describe(), "\n";   // Triangle có 3 cạnh
```

Kiểu trả về `static` (từ PHP 8.0) là chỗ hay dùng nhất trong code hằng ngày: *named constructor*
(`public static function fromArray(array $data): static`) và fluent API ở class cha (`return $this;`
với kiểu `static` thì class con gọi nối tiếp vẫn giữ đúng kiểu con).

Từ khoá `static` trong PHP mang nhiều nghĩa, đừng lẫn:

| Chỗ xuất hiện | Nghĩa | Chương |
|---|---|---|
| `public static function`, `public static int $x` | Method/property thuộc class, không thuộc object | 09 |
| `static $count = 0;` trong thân hàm | Biến cục bộ giữ giá trị giữa các lần gọi | 08 |
| `static fn () => ...`, `static function () {}` | Closure không gắn `$this` | 08 |
| `static::`, `new static`, kiểu trả về `static` | Late static binding | 10 |

### 2.3 Forwarding call và non-forwarding call

Manual định nghĩa chính xác: `static` là class của lời gọi *không chuyển tiếp* (*non-forwarding call*)
gần nhất.

- Gọi bằng **tên class cụ thể** (`A::foo()`) là non-forwarding: `static` bị đặt lại thành class đó.
- Gọi qua `self::`, `parent::`, `static::` là *forwarding call* (gọi chuyển tiếp): thông tin "class được
  gọi" được giữ nguyên, truyền tiếp vào method được gọi.

```php
<?php
declare(strict_types=1);

class A
{
    public static function foo(): void { static::who(); }
    public static function who(): void { echo "A\n"; }
}

class B extends A
{
    public static function test(): void
    {
        A::foo();        // gọi bằng tên class: KHÔNG chuyển tiếp, static = A
        parent::foo();   // chuyển tiếp: static vẫn là C
        self::foo();     // chuyển tiếp: static vẫn là C
    }
    public static function who(): void { echo "B\n"; }
}

class C extends B
{
    public static function who(): void { echo "C\n"; }
}

C::test();
// A
// C
// C
```

Luồng của `C::test()`:

```
C::test()                     static = C   (non-forwarding: gọi bằng tên C)
 ├─ A::foo()                  static = A   (non-forwarding: gọi bằng tên A)
 │    └─ static::who()  →  A::who()  in "A"
 ├─ parent::foo()             static = C   (forwarding: giữ C)
 │    └─ static::who()  →  C::who()  in "C"
 └─ self::foo()               static = C   (forwarding: B không có foo, chạy A::foo, giữ C)
      └─ static::who()  →  C::who()  in "C"
```

### 2.4 Static property và late static binding

Static property khai báo ở class cha được **dùng chung** với class con, trừ khi class con khai báo lại
property cùng tên. `static::$x` chọn property theo class được gọi, nên lợi dụng được điều này để mỗi
class con có bộ đếm riêng:

```php
<?php
declare(strict_types=1);

abstract class Model
{
    protected static int $created = 0;

    public static function make(): static
    {
        static::$created++;
        return new static();
    }

    public static function createdCount(): int { return static::$created; }
}

final class Post extends Model
{
    protected static int $created = 0;     // khai báo lại: Post có biến đếm riêng
}

final class Comment extends Model {}       // không khai báo lại: dùng chung biến của Model

Post::make();
Post::make();
Comment::make();
echo Post::createdCount(), "\n";      // 2
echo Comment::createdCount(), "\n";   // 1
echo Model::createdCount(), "\n";     // 1   (Comment tăng chính biến của Model)
```

### 2.5 Ghép magic method với `new static`: Eloquent thu nhỏ

Đây là cơ chế đứng sau `User::where(...)` của Laravel, thu gọn còn vài chục dòng:

```php
<?php
declare(strict_types=1);

final class QueryBuilder
{
    /** @var list<string> */
    private array $wheres = [];

    public function __construct(private string $table) {}

    public function where(string $column, string $value): self
    {
        $this->wheres[] = "{$column} = '{$value}'";   // chỉ để minh hoạ, code thật phải dùng binding
        return $this;
    }

    public function toSql(): string
    {
        $sql = "select * from {$this->table}";
        return $this->wheres === [] ? $sql : $sql . ' where ' . implode(' and ', $this->wheres);
    }
}

abstract class Model
{
    abstract protected function table(): string;

    public function newQuery(): QueryBuilder
    {
        return new QueryBuilder($this->table());
    }

    // Gọi method không tồn tại trên object: chuyển tiếp sang QueryBuilder
    public function __call(string $method, array $args): mixed
    {
        return $this->newQuery()->$method(...$args);
    }

    // Gọi method không tồn tại kiểu static: tạo instance của ĐÚNG class con rồi gọi lại
    public static function __callStatic(string $method, array $args): mixed
    {
        return (new static())->$method(...$args);
    }
}

final class User extends Model
{
    protected function table(): string { return 'users'; }
}

final class Post extends Model
{
    protected function table(): string { return 'posts'; }
}

echo User::where('email', 'an@example.com')->where('active', '1')->toSql(), "\n";
// select * from users where email = 'an@example.com' and active = '1'
echo Post::where('status', 'draft')->toSql(), "\n";
// select * from posts where status = 'draft'
```

```
User::where('email', ...)
  └─ User không có static method where → Model::__callStatic('where', [...])
       └─ (new static())  tạo object User (static = User)
            └─ ->where(...) không có method where → Model::__call('where', [...])
                 └─ $this->newQuery() → QueryBuilder('users') → ->where(...)
```

Nếu `__callStatic` viết `new self()` thì sẽ lỗi ngay, vì `Model` là abstract; còn nếu `Model` không
abstract thì mọi query đều thành query trên bảng của `Model`. Eloquent thật làm đúng như trên:
`Model::__callStatic` viết `(new static)->$method(...$parameters)`, và `Model::query()` là
`(new static)->newQuery()`.

### 2.6 Bẫy của `new static()`

`new static()` gọi constructor của **class con**. Class con đổi chữ ký constructor (thêm tham số bắt
buộc, đổi kiểu) là `new static(...)` ở class cha vỡ, và chỉ vỡ lúc chạy:

```php
<?php
declare(strict_types=1);

class Model
{
    /** @param array<string, mixed> $attributes */
    public function __construct(protected array $attributes = []) {}

    /** @param array<string, mixed> $attributes */
    public static function make(array $attributes): static
    {
        return new static($attributes);      // gọi constructor của class CON
    }
}

class Invoice extends Model
{
    public function __construct(private string $number)   // đổi chữ ký constructor
    {
        parent::__construct([]);
    }
}

try {
    Invoice::make(['total' => 100]);
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // Invoice::__construct(): Argument #1 ($number) must be of type string, array given, called in ...
}
```

Cách phòng:

- Đánh dấu constructor của class cha là `final public function __construct(...)`. Class con nào cố
  khai báo constructor riêng sẽ bị Fatal error "Cannot override final method" ngay lúc nạp class,
  thay vì vỡ âm thầm lúc chạy.
- Hoặc đánh dấu class là `final` nếu không cần class con.
- Hoặc giữ quy ước như Eloquent: mọi model dùng chung constructor `__construct(array $attributes = [])`.
- PHPStan báo "Unsafe usage of new static()" cho những chỗ `new static()` có thể vỡ theo cách này,
  ngay cả khi chưa có class con nào đổi constructor.

## 3. Enum (PHP 8.1)

### 3.1 Enum giải quyết vấn đề gì

Một đơn hàng có vài trạng thái cố định: chờ thanh toán, đã thanh toán, đang giao, đã hoàn tiền. Trước
PHP 8.1, cách phổ biến là hằng số:

```php
final class Order
{
    public const STATUS_PENDING = 'pending';
    public const STATUS_PAID    = 'paid';

    public function setStatus(string $status): void { /* ... */ }
}

$order->setStatus('piad');      // gõ sai: không ai báo lỗi
$order->setStatus('banana');    // giá trị vô nghĩa: cũng không ai báo lỗi
```

Tham số kiểu `string` nhận **mọi** chuỗi. Muốn chặn giá trị sai phải tự viết code kiểm tra ở mọi nơi,
không có chỗ nào liệt kê "đây là toàn bộ giá trị hợp lệ", và không gắn được hành vi (nhãn hiển thị,
quy tắc chuyển trạng thái) vào từng giá trị.

*Enum* (enumeration, kiểu liệt kê) là một **kiểu mới** có tập giá trị cố định, được liệt kê sẵn. Hàm
khai báo tham số kiểu enum thì chỉ nhận đúng các giá trị đó; truyền gì khác là `TypeError`. Enum là
tính năng của PHP 8.1.

### 3.2 Pure enum

*Pure enum* (enum "thuần") là enum mà các *case* (giá trị) không gắn với giá trị vô hướng nào:

```php
<?php
declare(strict_types=1);

enum Suit
{
    case Hearts;
    case Diamonds;
    case Clubs;
    case Spades;
}

function color(Suit $s): string
{
    return match ($s) {
        Suit::Hearts, Suit::Diamonds => 'đỏ',
        Suit::Clubs, Suit::Spades    => 'đen',
    };
}

echo color(Suit::Hearts), "\n";               // đỏ
echo Suit::Spades->name, "\n";                // Spades
var_dump(Suit::Hearts === Suit::Hearts);      // bool(true)   mỗi case là một object duy nhất
var_dump(Suit::Hearts instanceof Suit);       // bool(true)
var_dump(Suit::Hearts === 'Hearts');          // bool(false)  case không phải chuỗi
var_dump(count(Suit::cases()));               // int(4)       theo thứ tự khai báo
var_dump(Suit::Hearts);                       // enum(Suit::Hearts)

try {
    color('Hearts');                          // truyền chuỗi vào chỗ cần Suit
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // color(): Argument #1 ($s) must be of type Suit, string given, called in ...
}
```

Cách hiểu bên trong: enum được PHP cài đặt như một class đặc biệt, mỗi case là **một object duy nhất**
(*singleton*) của class đó. `Suit::Hearts` ở mọi nơi trong chương trình là cùng một object, nên so sánh
bằng `===` là đủ và rất rẻ. Mỗi case có property chỉ đọc `name` (tên case, phân biệt hoa thường), và
`Suit::cases()` trả về mảng các case theo thứ tự khai báo.

`match` hợp với enum: liệt kê đủ mọi case thì khỏi cần `default`. Nếu sau này thêm case mới mà quên
cập nhật `match`, PHP ném `UnhandledMatchError` khi gặp case đó, và PHPStan báo trước được lúc phân
tích tĩnh. Đó là lý do nên tránh `default` trong `match` trên enum: `default` nuốt mất case mới.

### 3.3 Backed enum

Khi cần lưu enum vào DB, gửi qua JSON, đọc từ query string, ta cần một giá trị vô hướng tương ứng cho
mỗi case. *Backed enum* gắn mỗi case với một `int` hoặc một `string`:

```php
enum OrderStatus: string
{
    case Pending  = 'pending';
    case Paid     = 'paid';
}
```

Quy tắc:

- Kiểu gắn (*backing type*) chỉ là `int` hoặc `string`, một kiểu cho cả enum (không có `int|string`).
- Mọi case phải khai báo giá trị tường minh, không có tự đánh số; hai case không được trùng giá trị.
- Case có thêm property chỉ đọc `value`.
- Enum có `implements` thì viết sau backing type: `enum OrderStatus: string implements HasLabel`.

Backed enum tự có hai static method để đổi giá trị vô hướng thành case:

| Method | Không tìm thấy | Dùng khi |
|---|---|---|
| `from(int\|string $value): static` | Ném `ValueError` | Dữ liệu **phải** hợp lệ (đọc từ DB của chính mình); sai là lỗi thật, nên dừng |
| `tryFrom(int\|string $value): ?static` | Trả `null` | Dữ liệu không tin được (input người dùng); tự xử lý `null` |

Với `strict_types=1`, truyền `int` cho `from()` của enum gắn `string` (hoặc ngược lại) là `TypeError`.
Backed enum không được tự định nghĩa `from`, `tryFrom`, và không enum nào được tự định nghĩa `cases`
(Fatal error "Cannot redeclare ...").

### 3.4 Enum có method, static method, hằng, interface, trait

Enum không chỉ là danh sách tên: nó có method như class.

```php
<?php
declare(strict_types=1);

interface HasLabel
{
    public function label(): string;
}

trait EnumValues
{
    /** @return list<string> */
    public static function values(): array
    {
        return array_column(self::cases(), 'value');
    }
}

enum OrderStatus: string implements HasLabel
{
    use EnumValues;                                   // trait chỉ được chứa method, hằng

    case Pending  = 'pending';
    case Paid     = 'paid';
    case Shipped  = 'shipped';
    case Refunded = 'refunded';

    public const DEFAULT = self::Pending;             // hằng trỏ tới một case (alias)

    public function label(): string                   // method thường, $this là case hiện tại
    {
        return match ($this) {
            self::Pending  => 'Chờ thanh toán',
            self::Paid     => 'Đã thanh toán',
            self::Shipped  => 'Đang giao',
            self::Refunded => 'Đã hoàn tiền',
        };
    }

    public function canRefund(): bool
    {
        return $this === self::Paid || $this === self::Shipped;
    }

    public static function fromLabel(string $label): self   // static method: "constructor" phụ
    {
        foreach (self::cases() as $case) {
            if ($case->label() === $label) {
                return $case;
            }
        }
        throw new ValueError("Không có trạng thái '{$label}'");
    }
}

$s = OrderStatus::from('paid');                       // dữ liệu tin cậy (đọc từ DB của mình)
echo $s->name, ' | ', $s->value, ' | ', $s->label(), "\n";   // Paid | paid | Đã thanh toán
var_dump($s === OrderStatus::Paid);                   // bool(true)
var_dump(OrderStatus::tryFrom('banana'));             // NULL
echo (OrderStatus::tryFrom('banana') ?? OrderStatus::DEFAULT)->label(), "\n";   // Chờ thanh toán
var_dump(OrderStatus::Shipped->canRefund());          // bool(true)
echo OrderStatus::fromLabel('Đang giao')->value, "\n";   // shipped
echo implode(',', OrderStatus::values()), "\n";       // pending,paid,shipped,refunded
var_dump(OrderStatus::Paid instanceof BackedEnum);    // bool(true)
var_dump(OrderStatus::Paid instanceof HasLabel);      // bool(true)
echo json_encode(['status' => OrderStatus::Paid]), "\n";   // {"status":"paid"}

try {
    OrderStatus::from('banana');
} catch (ValueError $e) {
    echo $e->getMessage(), "\n";                      // "banana" is not a valid backing value for enum OrderStatus
}
```

- Method có thể `public`, `protected`, `private`; vì enum không kế thừa được nên `protected` và
  `private` thực chất như nhau.
- Mọi enum tự implement interface `UnitEnum` (có `cases()`); backed enum implement thêm `BackedEnum`
  (có `from()`, `tryFrom()`). Dùng hai interface này để type-hint code chung cho mọi enum, ví dụ hàm
  `function options(string $enumClass)` dựng danh sách lựa chọn cho form.
- Logic gắn với từng trạng thái (nhãn, màu, quyền chuyển trạng thái) nên nằm trong enum, thay vì rải
  `if ($status === 'paid')` khắp code.

### 3.5 Enum trong biểu thức hằng

Case là hằng của enum, nên dùng được trong *constant expression* (biểu thức hằng: loại biểu thức bị giới
hạn, không gọi hàm, dùng ở những chỗ cần giá trị cố định): giá trị hằng, giá trị mặc định của property
và tham số, tham số của attribute.

```php
final class Order
{
    public OrderStatus $status = OrderStatus::Pending;                   // 8.1: OK

    public function __construct(OrderStatus $initial = OrderStatus::Pending) { /* ... */ }
}

enum Status: string
{
    case Paid = 'paid';
    case Void = 'void';

    const LABELS = [self::Paid->value => 'Đã trả', self::Void->value => 'Đã huỷ'];   // 8.2+
}
```

Đọc `->value`, `->name` của case trong biểu thức hằng chỉ được từ PHP 8.2; trên 8.1 dòng `LABELS` báo
"Constant expression contains invalid operations". Lấy case theo tên động: `Suit::{$name}` (cú pháp có
từ 8.3), hoặc `constant(Suit::class . '::' . $name)` ở bản cũ hơn.

### 3.6 Enum khác object thường ở đâu

Enum là object (`gettype()` trả `"object"`), nhưng bị giới hạn để case luôn là singleton không có
trạng thái:

- **Không có state**: không khai báo property (cả static), chỉ có sẵn `name` và `value` chỉ đọc. Gán
  `$s->value = 'x'` ném `Error: Cannot modify readonly property`.
- Không có constructor/destructor, không `new` được (`Error: Cannot instantiate enum Suit`), không
  `clone` được.
- Không `extends` và không bị `extends`. Trait dùng trong enum không được có property.
- Magic method bị cấm, trừ `__call`, `__callStatic`, `__invoke`.
- ⚠️ **Không làm key mảng được**: `$map[Suit::Hearts] = 1` ném `TypeError`. Dùng `->value` (backed
  enum) làm key, hoặc dùng `WeakMap`/`SplObjectStorage` (mục 12) khi cần key là chính case.
- ⚠️ **Không có thứ tự**: `<`, `>` giữa hai case luôn trả `false`. Cần thứ tự (mức độ ưu tiên) thì viết
  method `rank(): int`, đừng dựa vào thứ tự khai báo hay giá trị `int`.
- `json_encode()` backed enum ra giá trị (`"paid"`); pure enum thì `json_encode()` thất bại (trả
  `false`, lỗi "Non-backed enums have no default serialization"; ném `JsonException` nếu dùng
  `JSON_THROW_ON_ERROR`).
- `serialize()` enum ra định dạng riêng `E:11:"Status:Paid";`, và `unserialize()` trả về **đúng
  singleton** đó, nên `unserialize(serialize(Status::Paid)) === Status::Paid` là `true`.

### 3.7 Enum trong dự án thật

- Lưu DB bằng `->value`, đọc lên bằng `from()`. Enum gắn `string` dễ đọc khi xem dữ liệu thô và khi
  debug hơn enum gắn `int`.
- Thêm case mới không làm hỏng dữ liệu cũ (nhưng phải cập nhật các `match` liệt kê case, xem 3.2). Đổi
  `value` của case cũ là thay đổi phá dữ liệu: các dòng cũ trong DB không còn `from()` được, phải kèm
  migration dữ liệu.
- Input từ người dùng dùng `tryFrom()` (hoặc validation) rồi trả lỗi 4xx, đừng để `from()` ném
  `ValueError` thành lỗi 500.
- Laravel hiểu enum ở nhiều chỗ: cast thuộc tính Eloquent sang enum, rule validation
  `Rule::enum(OrderStatus::class)`, route binding theo backed enum. Xem
  [chương 25](25-laravel-request-validation-response.md) và [chương 27](27-laravel-database-eloquent.md).

Đối chiếu: enum của PHP gần với enum của Java (mỗi hằng là một object singleton, có method, implement
interface), nhưng Java enum có field và constructor (mỗi hằng truyền giá trị riêng vào constructor), còn
case của PHP thì không có state. Go không có enum; người ta dùng `const` với `iota`, nên một biến kiểu
`Weekday` vẫn nhận được số bất kỳ.

## 4. `readonly`: property chỉ ghi một lần

### 4.1 Vì sao cần object không đổi

Hãy nghĩ tới một object `Money(100, 'VND')` được truyền qua năm hàm. Nếu bất kỳ hàm nào cũng sửa được
`$money->amount`, bạn phải đọc cả năm hàm mới chắc giá trị còn là 100. Object *bất biến* (*immutable*,
tạo xong không đổi nữa) loại bỏ lo lắng đó: muốn giá trị khác thì tạo object mới. Loại object này gọi
là *value object*: định danh bằng giá trị (hai `Money(100, 'VND')` là "bằng nhau"), không có vòng đời
riêng. Trước PHP 8.1, muốn bất biến phải khai báo `private` rồi viết getter cho từng property.

### 4.2 `readonly` property (PHP 8.1)

Property `readonly` chỉ được gán **đúng một lần**, sau đó mọi thay đổi đều ném `Error`, kể cả từ bên
trong class, kể cả gán lại đúng giá trị cũ.

```php
<?php
declare(strict_types=1);

final class Money
{
    public function __construct(
        public readonly int $amount,
        public readonly string $currency,
        public readonly array $tags = [],
    ) {}
}

$m = new Money(100, 'VND', ['sale']);
echo $m->amount, ' ', $m->currency, "\n";        // 100 VND   đọc thoải mái

$tries = [
    'gán lại'           => function () use ($m) { $m->amount = 200; },
    'gán giá trị cũ'    => function () use ($m) { $m->amount = 100; },
    'tăng ++'           => function () use ($m) { $m->amount++; },
    'thêm phần tử mảng' => function () use ($m) { $m->tags[] = 'hot'; },
    'unset'             => function () use ($m) { unset($m->amount); },
];
foreach ($tries as $label => $try) {
    try {
        $try();
    } catch (Error $e) {
        echo "$label: ", $e->getMessage(), "\n";
    }
}
// gán lại: Cannot modify readonly property Money::$amount
// gán giá trị cũ: Cannot modify readonly property Money::$amount
// tăng ++: Cannot modify readonly property Money::$amount
// thêm phần tử mảng: Cannot indirectly modify readonly property Money::$tags
// unset: Cannot unset readonly property Money::$amount
```

Quy tắc (theo manual):

1. **Bắt buộc có kiểu**: `public readonly $x;` là lỗi. Không muốn giới hạn kiểu thì dùng `mixed`.
2. **Không có giá trị mặc định** ở khai báo (`public readonly int $x = 1;` là Fatal error, vì như vậy
   nó chẳng khác gì hằng). Giá trị mặc định của *tham số* promoted như `$tags = []` ở trên thì được,
   vì đó là giá trị của tham số chứ không phải của property.
3. **Không có static readonly**.
4. **Chỉ khởi tạo được từ bên trong class**. Tới PHP 8.3 là "chỉ class khai báo property"; từ 8.4,
   readonly ngầm có quyền ghi `protected(set)` (mục 6) nên class con cũng khởi tạo được. Code bên
   ngoài thì không bao giờ:

```php
<?php
declare(strict_types=1);

final class Profile
{
    public readonly string $name;            // chưa khởi tạo
}
$p = new Profile();
try {
    $p->name = 'An';                         // khởi tạo từ ngoài class
} catch (Error $e) {
    echo $e->getMessage(), "\n";
    // 8.5: Cannot modify protected(set) readonly property Profile::$name from global scope
    // 8.1 tới 8.3: Cannot initialize readonly property Profile::$name from global scope
}
```

5. Không khởi tạo **qua reference**: truyền property readonly chưa khởi tạo vào hàm nhận tham số by
   reference (ví dụ `preg_match('/\d+/', $s, $this->matches)`) cũng ném `Error`. Gán vào biến tạm
   rồi gán cho property.

Trước khi được gán, property readonly ở trạng thái *uninitialized* (chưa khởi tạo) như mọi typed
property: đọc nó ném `Error: ... must not be accessed before initialization`.

### 4.3 Readonly là nông

⚠️ `readonly` khoá việc **gán lại property**, không khoá **nội dung object** mà property trỏ tới:

```php
<?php
declare(strict_types=1);

final class Order
{
    public function __construct(public readonly ArrayObject $lines) {}
}
$o = new Order(new ArrayObject());
$o->lines->append('A1');                     // CHẠY ĐƯỢC: readonly là nông
var_dump(count($o->lines));                  // int(1)
```

Mảng thì khác: mảng là giá trị (copy khi gán), nên `$m->tags[] = 'hot'` ở 4.2 bị chặn. Muốn một value
object bất biến thật thì mọi property kiểu object bên trong cũng phải bất biến: dùng
`DateTimeImmutable` thay cho `DateTime`, value object readonly thay cho object có setter.

### 4.4 `readonly class` (PHP 8.2)

Đánh dấu cả class là `readonly` thì **mọi property** được khai báo đều thành readonly, và class không
tạo được dynamic property:

```php
<?php
declare(strict_types=1);

final class Address                          // object có thể thay đổi
{
    public function __construct(public string $city) {}
}

final readonly class Customer               // 8.2: mọi property đều readonly
{
    public function __construct(
        public string $name,
        public Address $address,
    ) {}

    public function __clone(): void
    {
        // 8.3+: được gán lại property readonly bên trong __clone (để clone sâu)
        $this->address = clone $this->address;
    }
}

$a = new Customer('An', new Address('Huế'));
$b = clone $a;
$b->address->city = 'Đà Nẵng';
echo $a->address->city, ' / ', $b->address->city, "\n";   // Huế / Đà Nẵng
```

Quy tắc của readonly class:

- Mọi property phải có kiểu, không có static property (Fatal error "Static property ...::$x cannot be
  readonly").
- Không gắn được `#[\AllowDynamicProperties]`; gán property lạ ném
  `Error: Cannot create dynamic property`.
- Class con của readonly class cũng phải là readonly class ("Non-readonly class B cannot extend
  readonly class A").
- Từ PHP 8.3 có thêm *anonymous readonly class*: `new readonly class { ... }`.

Gán lại property readonly trong `__clone()` là tính năng của PHP 8.3. Trên 8.2, ví dụ trên ném
`Error: Cannot modify readonly property Customer::$address` ở dòng trong `__clone`. Còn thiếu một mảnh:
`__clone()` không nhận tham số, nên nó giúp clone sâu nhưng không giúp viết method `withCity('Hà Nội')`
trả bản sao có giá trị mới. Mảnh đó là clone with của PHP 8.5 (mục 7).

## 5. Property hooks (PHP 8.4)

### 5.1 Vấn đề: getter/setter viết tay

Giả sử `User` cần email luôn ở dạng chữ thường và phải có `@`. Trước 8.4 có hai lựa chọn, đều dở:

- Property `private` + cặp `getEmail()`/`setEmail()`: an toàn nhưng dài dòng, và mọi chỗ dùng phải gọi
  method. Nhiều team viết getter/setter cho **mọi** property "phòng khi sau này cần thêm logic", dù
  phần lớn chỉ là `return $this->x;`.
- Property `public`: gọn nhưng không chèn được kiểm tra. Muốn thêm kiểm tra sau này thì phải đổi thành
  method, sửa mọi chỗ đang dùng `$user->email`.
- (`__get`/`__set` ở mục 1 làm được, nhưng IDE không hiểu, không có kiểu, phải dùng mảng ẩn.)

*Property hooks* (manual: "còn gọi là *property accessors* ở ngôn ngữ khác", như C# hay Kotlin) cho
phép gắn logic `get`/`set` thẳng lên property. Bên ngoài vẫn đọc ghi `$user->email` như property
thường; khi nào cần thêm logic thì thêm hook, không phải sửa code gọi.

### 5.2 Cú pháp

```php
<?php
declare(strict_types=1);

final class User
{
    public string $email {
        set(string $value) {
            $value = strtolower(trim($value));
            if (!str_contains($value, '@')) {
                throw new InvalidArgumentException("Email không hợp lệ: $value");
            }
            $this->email = $value;           // $this->email trong hook = ô nhớ thật (backing value)
        }
    }

    public string $name {
        set => trim($value);                 // dạng ngắn: kết quả biểu thức được ghi vào ô nhớ
    }

    public string $domain {                  // virtual: không hook nào dùng $this->domain
        get => explode('@', $this->email, 2)[1];
    }

    public function __construct(string $name, string $email)
    {
        $this->name = $name;                 // đi qua set hook, kể cả trong constructor
        $this->email = $email;
    }
}

$u = new User('  An  ', ' An@Example.COM ');
var_dump($u->name);          // string(2) "An"
echo $u->email, "\n";        // an@example.com
echo $u->domain, "\n";       // example.com

try {
    $u->email = 'khong-hop-le';
} catch (InvalidArgumentException $e) {
    echo $e->getMessage(), "\n";             // Email không hợp lệ: khong-hop-le
}
try {
    $u->domain = 'php.net';
} catch (Error $e) {
    echo $e->getMessage(), "\n";             // Property User::$domain is read-only
}

var_dump($u);                // chỉ có email và name: virtual property không chiếm ô nhớ
// object(User)#1 (2) {
//   ["email"]=>
//   string(14) "an@example.com"
//   ["name"]=>
//   string(2) "An"
// }
echo json_encode($u), "\n";  // {"email":"an@example.com","name":"An","domain":"example.com"}
```

Đọc cú pháp:

- Property kết thúc bằng khối `{ ... }` thay cho dấu `;` nghĩa là có hook. Có hai hook: `get` (chạy khi
  đọc) và `set` (chạy khi ghi). Khai báo một hoặc cả hai.
- Trong `set`, giá trị được gán nằm trong biến `$value`. Có thể khai báo rõ `set(string $value)`, kiểu
  phải bằng hoặc rộng hơn kiểu property (property `string` có thể nhận `set(string|Stringable $value)`).
  Bỏ phần khai báo thì kiểu bằng kiểu property và tên mặc định là `$value`.
- Dạng ngắn `get => biểu thức;` trả về biểu thức. Dạng ngắn `set => biểu thức;` ghi **kết quả** của
  biểu thức vào ô nhớ (`set => trim($value);` tương đương `set { $this->name = trim($value); }`).
- Bên trong hook, `$this->email` (đúng tên property đó) là truy cập **thẳng vào ô nhớ**, không gọi lại
  hook, nên không có đệ quy vô hạn.
- Hook chạy trong scope của object: gọi được method `private`, đọc được property khác (và đọc property
  khác thì vẫn đi qua hook của property đó).

### 5.3 Backed property và virtual property

- *Backed property*: có ít nhất một hook dùng `$this->tenProperty`, hoặc không có hook nào. Property có
  ô nhớ thật. Hook nào không khai báo thì dùng hành vi đọc/ghi mặc định.
- *Virtual property*: không hook nào dùng `$this->tenProperty`. Không có ô nhớ, giống một cặp method
  trá hình. Hook nào không khai báo thì thao tác đó **không tồn tại**: `$domain` chỉ có `get` nên ghi
  vào là `Error: Property User::$domain is read-only`. Virtual property không được có giá trị mặc định.

Virtual property hợp với giá trị dẫn xuất: `fullName` ghép từ `firstName` và `lastName`, `area` tính
từ chiều dài và chiều rộng.

Hook ảnh hưởng tới việc in và serialize không đồng đều (bảng theo manual):

| Thao tác | Dùng giá trị thô (bỏ qua hook) | Đi qua `get`/`set` hook |
|---|---|---|
| `var_dump()`, `serialize()`, `unserialize()`, ép `(array)` | ✓ | |
| `var_export()`, `json_encode()`, `get_object_vars()` | | ✓ |
| `__serialize()`/`__unserialize()`, `JsonSerializable` | | Tuỳ code bạn viết (đọc/ghi property thì đi qua hook) |

Vì vậy `var_dump` ở trên không có `domain`, còn `json_encode` thì có.

### 5.4 Hook và kế thừa

Class con có thể thêm hook cho property của cha, hoặc ghi đè từng hook riêng lẻ. Muốn gọi lại hành vi
của cha thì dùng cú pháp `parent::$tenProperty::get()` / `parent::$tenProperty::set($value)`:

```php
<?php
declare(strict_types=1);

class Point
{
    public int $x = 0;                       // property thường, không hook
}

class PositivePoint extends Point
{
    public int $x = 0 {                      // class con thêm hook cho property của cha
        set {
            if ($value < 0) {
                throw new InvalidArgumentException('x phải >= 0');
            }
            parent::$x::set($value);         // gọi "hành vi ghi" của cha (ở đây là ghi mặc định)
        }
    }
}

abstract class Shape
{
    abstract public string $name { get; }    // abstract property: class con phải cung cấp get
}

final class Square extends Shape
{
    public string $name {
        get => 'hình vuông';
    }
}

$p = new PositivePoint();
$p->x = 5;
echo $p->x, "\n";                            // 5
try {
    $p->x = -1;
} catch (InvalidArgumentException $e) {
    echo $e->getMessage(), "\n";             // x phải >= 0
}
echo (new Square())->name, "\n";             // hình vuông
```

- Class con thêm hook thì giá trị mặc định của property ở class cha bị bỏ, phải khai báo lại (như
  `= 0` ở trên).
- Hook có thể `final` (class con không ghi đè được hook đó), cả property cũng có thể `final`.
- Abstract class và interface khai báo được property với yêu cầu `{ get; }`, `{ set; }` hoặc cả hai.
  Interface có property đã nói ở [chương 09](09-oop-co-ban.md); class thoả mãn yêu cầu `{ get; }`
  bằng property public thường, property có hook, hoặc property readonly.

### 5.5 Giới hạn và bẫy

⚠️ **Property mảng có `set` hook không sửa từng phần tử được.** Sửa `$obj->items[] = ...` là sửa tại
chỗ, đi vòng qua hook, nên PHP cấm:

```php
<?php
declare(strict_types=1);

final class Cart
{
    /** @var list<string> */
    public array $items = [] {
        set(array $value) {
            $this->items = array_values(array_unique($value));   // luôn khử trùng lặp
        }
    }
}

$c = new Cart();
try {
    $c->items[] = 'A1';                      // sửa một phần tử: đi vòng qua set hook
} catch (Error $e) {
    echo $e->getMessage(), "\n";             // Indirect modification of Cart::$items is not allowed
}
$c->items = [...$c->items, 'A1', 'A1'];      // gán cả mảng mới: đi qua set hook
var_dump($c->items);                         // array(1) { [0]=> string(2) "A1" }
```

Với collection cần thêm/bớt phần tử, method `add()`/`remove()` vẫn là thiết kế tốt hơn.

Các giới hạn khác (đều là lỗi lúc nạp class):

| Viết | Lỗi |
|---|---|
| `public readonly int $x { get => 1; }` | Hooked properties cannot be readonly |
| `public static int $x { get => 1; }` | Cannot declare hooks for static property |
| `public int $x = 5 { get => 1; }` (virtual có giá trị mặc định) | Cannot specify default value for virtual hooked property |
| Backed property có cả `&get` lẫn `set` | Get hook ... with set hook may not return by reference |

Muốn "đọc công khai, ghi có kiểm soát" mà không dùng được `readonly` thì kết hợp hook với asymmetric
visibility (mục 6), ví dụ `public private(set) string $email { set { ... } }`.

Khi nào dùng hook:

- Chuẩn hoá hoặc kiểm tra giá trị khi gán (`trim`, `strtolower`, ràng buộc miền giá trị).
- Giá trị dẫn xuất rẻ (virtual property).
- Thay cho getter/setter "phòng hờ": giờ cứ để property public, khi nào cần logic thì thêm hook.

Khi nào không:

- Logic nặng hoặc có tác dụng phụ (query DB, gọi API) trong `get`: người đọc `$order->total` nghĩ đó
  là phép đọc rẻ. Viết method `calculateTotal()` cho rõ chi phí.
- Cột của Eloquent model: Eloquent đọc cột qua `__get` (mục 1.2), khai báo property (dù có hook) sẽ
  chặn cơ chế đó. Eloquent có cơ chế accessor/mutator riêng ([chương 27](27-laravel-database-eloquent.md)).

## 6. Asymmetric visibility (PHP 8.4)

### 6.1 Quyền đọc và quyền ghi khác nhau

Rất nhiều property có nhu cầu "ai cũng đọc được, nhưng chỉ class này được ghi": trạng thái đơn hàng,
bộ đếm, lịch sử. `readonly` không hợp vì class cần ghi **nhiều lần**; `private` + getter thì dài dòng.
*Asymmetric visibility* (visibility bất đối xứng) cho phép khai báo quyền ghi riêng bằng
`private(set)` hoặc `protected(set)`:

```php
<?php
declare(strict_types=1);

final class Order
{
    public private(set) string $status = 'pending';   // ngoài đọc được, chỉ Order ghi
    private(set) int $version = 0;                      // viết tắt của public private(set)
    /** @var list<string> */
    public private(set) array $history = [];

    public function pay(): void
    {
        $this->status = 'paid';                         // bên trong class: ghi bao nhiêu lần cũng được
        $this->version++;
        $this->history[] = 'paid';
    }
}

$o = new Order();
$o->pay();
echo $o->status, ' v', $o->version, ' ', count($o->history), "\n";   // paid v1 1

$tries = [
    fn() => $o->status = 'refunded',                    // ghi từ ngoài
    fn() => $o->history[] = 'hack',                     // sửa phần tử mảng cũng cần quyền set
];
foreach ($tries as $try) {
    try {
        $try();
    } catch (Error $e) {
        echo $e->getMessage(), "\n";
    }
}
// Cannot modify private(set) property Order::$status from global scope
// Cannot indirectly modify private(set) property Order::$history from global scope
```

Cú pháp: `<quyền đọc> <quyền ghi>(set) <kiểu> $tên`. Quyền đọc là `public` thì được bỏ, nên
`private(set) int $version` giống hệt `public private(set) int $version`.

### 6.2 Quy tắc

- Chỉ dùng cho property **có kiểu** (không kiểu: "Property with asymmetric visibility ... must have type").
- Quyền ghi phải **bằng hoặc hẹp hơn** quyền đọc: `public protected(set)` được, `protected public(set)`
  là lỗi lúc nạp class.
- Property `private(set)` tự động là `final`: class con không khai báo lại được.
- Lấy reference tới property, hay sửa một phần tử của property mảng, đều tính là **ghi**, nên theo quyền
  set (như `$o->history[] = 'hack'` ở trên).
- Không có khoảng trắng trong ngoặc: `private( set )` là lỗi cú pháp.
- Static property chỉ dùng được asymmetric visibility từ PHP 8.5 (`public private(set) static int $calls = 0;`);
  trên 8.4 là lỗi "Static property may not have asymmetric visibility".
- Liên hệ `readonly`: từ 8.4, `readonly` ngầm là `protected(set)` (mục 4.2). Muốn class con không
  khởi tạo được thì ghi rõ `public private(set) readonly`.

⚠️ Giống `readonly`, giới hạn chỉ áp lên việc **gán lại** property. Nếu property chứa object, code bên
ngoài vẫn gọi method sửa object đó được.

### 6.3 Chọn công cụ nào

| Nhu cầu | Công cụ | Ví dụ |
|---|---|---|
| Tạo xong không bao giờ đổi | `readonly` (property hoặc class) | Value object: `Money`, `DateRange` |
| Ai cũng đọc, chỉ class ghi, ghi nhiều lần | `public private(set)` | Entity có trạng thái: `Order::$status` |
| Kiểm tra/biến đổi khi ghi, hoặc giá trị dẫn xuất | Property hook | `User::$email`, `Rectangle::$area` |
| Vừa giới hạn quyền ghi vừa kiểm tra khi ghi | `public private(set)` + `set` hook | `public private(set) string $email { set { ... } }` |
| Bản sao có vài giá trị khác của object bất biến | `readonly` + clone with | `$money->withAmount(200)` (mục 7) |

Đối chiếu: Java, Go không có cú pháp tương đương; Java dùng field `private` + getter (hoặc `record`
cho object bất biến), Go dùng field viết thường (chỉ package thấy) + method. C# có cú pháp gần nhất:
`public string Status { get; private set; }`.

## 7. Clone with (PHP 8.5)

### 7.1 Bài toán "wither"

Chương 09 đã nói `clone $obj` tạo bản sao nông và gọi `__clone()`. Với value object bất biến, ta thường
cần method kiểu `withAmount(200)` (gọi là *wither*): trả về **bản sao** với một vài giá trị khác, object
gốc giữ nguyên. Trước 8.5, property `readonly` trên bản clone đã được khởi tạo nên không gán lại được
(8.3 chỉ mở khoá bên trong `__clone()`, mà `__clone()` không nhận tham số), nên wither phải gọi lại
constructor và liệt kê **mọi** field:

```php
public function withAmount(int $amount): static
{
    return new static($amount, $this->currency /*, ...mọi field khác */);
}
```

Class có 8 field là wither nào cũng phải chép đủ 8 tham số, thêm field mới là sửa mọi wither.

### 7.2 `clone()` thành hàm nhận mảng giá trị mới

Từ PHP 8.5, `clone` dùng được như một hàm với tham số thứ hai là mảng `tên property => giá trị mới`:
`clone($object, ['amount' => 250])`. Chỉ property được nêu bị ghi đè, phần còn lại giữ giá trị đã
copy. Property `readonly` được "mở khoá" cho đúng lần gán này.

```php
<?php
declare(strict_types=1);

final readonly class Money
{
    public function __construct(
        public int $amount,
        public string $currency,
    ) {
        if ($amount < 0) {
            throw new InvalidArgumentException('amount phải >= 0');
        }
    }

    public function withAmount(int $amount): static
    {
        return clone($this, ['amount' => $amount]);    // 8.5: chỉ nêu property cần đổi
    }

    public function add(Money $other): static
    {
        return $this->withAmount($this->amount + $other->amount);
    }
}

$a = new Money(100, 'VND');
$b = $a->withAmount(250);
$c = $a->add($b);
echo $a->amount, ' ', $b->amount, ' ', $c->amount, ' ', $c->currency, "\n";   // 100 250 350 VND
var_dump($a === $b);                                   // bool(false)  object mới

try {
    clone($a, ['amount' => 1]);                        // từ ngoài class
} catch (Error $e) {
    echo $e->getMessage(), "\n";
    // Cannot modify protected(set) readonly property Money::$amount from global scope
}

$neg = $a->withAmount(-5);                             // ⚠️ clone with KHÔNG gọi constructor
echo $neg->amount, "\n";                               // -5   kiểm tra trong constructor bị bỏ qua
```

### 7.3 Cơ chế

Theo RFC *Clone with v2*, `clone($obj, $with)` làm lần lượt:

1. Tạo bản sao nông của object (như `clone $obj`).
2. Gọi `__clone()` trên bản sao nếu có. `__clone` chạy **trước** khi gán giá trị mới.
3. Gán từng cặp trong mảng theo thứ tự, **như một phép gán bình thường** từ chỗ gọi `clone()`: kiểm
   tra visibility, kiểm tra kiểu, chạy `set` hook, gọi `__set` nếu có; chỉ riêng trạng thái readonly
   được mở khoá. Lỗi ở key nào thì dừng tại key đó.

```php
<?php
declare(strict_types=1);

final class Draft
{
    public function __construct(
        public string $title,
        public int $revision = 1,
    ) {}

    public function __clone(): void
    {
        echo "  __clone: title = {$this->title}\n";   // chạy TRƯỚC khi gán giá trị mới
        $this->revision++;
    }
}

$d1 = new Draft('Bản nháp');
$d2 = clone($d1, ['title' => 'Bản sửa']);             //   __clone: title = Bản nháp
echo $d2->title, ' r', $d2->revision, "\n";           // Bản sửa r2

$copies = array_map(clone(...), [$d1, $d2]);          // clone dùng được như callable
echo count($copies), "\n";                            // 2   (trước đó in thêm hai dòng __clone)
```

Những điều cần nhớ:

- ⚠️ **Visibility vẫn áp dụng.** Code bên ngoài không dùng clone with để sửa property `private`,
  `protected` hay `readonly` được (readonly ngầm là `protected(set)`). Clone with không phải cửa sau
  để phá tính bất biến: chỉ class (hoặc class con, với `protected(set)`) mới tạo được bản sao đã sửa.
- ⚠️ **Không gọi constructor**, nên kiểm tra đặt trong constructor bị bỏ qua (`-5` ở ví dụ trên). Có ba
  cách: wither tự kiểm tra trước khi clone; đặt kiểm tra vào `set` hook (không dùng được với
  `readonly`, xem 5.5); hoặc dùng `new static(...)` khi cần chạy lại toàn bộ validation.
- ⚠️ Vẫn là bản sao **nông**: property kiểu object vẫn dùng chung giữa bản cũ và bản mới, trừ khi
  `__clone` clone sâu.
- Vì `clone` giờ là hàm, `clone(...)` tạo được closure để truyền vào `array_map`.

## 8. Reflection cơ bản

### 8.1 Reflection là gì, dùng để làm gì

*Reflection* là API cho phép chương trình **tự xem cấu trúc code của chính nó lúc chạy**: class có
những method nào, constructor cần tham số gì và kiểu gì, property nào là `private`, có attribute gì.
Thậm chí đọc/ghi được property `private` và gọi được method `private`.

Code nghiệp vụ hằng ngày hiếm khi cần Reflection. Nó là công cụ của **framework và thư viện**:

- DI container nhìn constructor để tự tạo dependency (*autowiring*): Laravel service container
  ([chương 26](26-laravel-container-provider-facade.md)).
- Đọc attribute để biết route, rule validation, cấu hình (mục 9).
- ORM, serializer đọc/ghi property không qua constructor; PHPUnit tìm method test.
- Tạo lazy object (mục 10).

### 8.2 Các class chính

| Class | Mô tả |
|---|---|
| `ReflectionClass` | Một class/interface/trait: tên, cha, interface, method, property, hằng, attribute, tạo instance |
| `ReflectionObject` | Như `ReflectionClass` nhưng tạo từ một object cụ thể |
| `ReflectionEnum` | Một enum: các case, backing type |
| `ReflectionMethod`, `ReflectionFunction` | Một method/hàm: tham số, kiểu trả về, visibility, gọi được |
| `ReflectionParameter` | Một tham số: tên, kiểu, giá trị mặc định, có phải variadic |
| `ReflectionProperty` | Một property: kiểu, visibility, readonly, đọc/ghi giá trị |
| `ReflectionNamedType` | Một kiểu đơn (`int`, `?string`, `User`) |
| `ReflectionUnionType`, `ReflectionIntersectionType` | Kiểu `int\|float`, `A&B` |
| `ReflectionAttribute` | Một attribute gắn trên phần tử (mục 9) |

### 8.3 Khám phá một class

```php
<?php
declare(strict_types=1);

final class Invoice
{
    private string $secret = 'không ai thấy';

    public function __construct(
        public readonly int $id,
        private ?string $note = null,
        protected int|float $total = 0,
    ) {}

    public function send(string $email, bool $copy = false): bool { return true; }
    private function sign(): string { return 'sig'; }
}

$rc = new ReflectionClass(Invoice::class);
echo $rc->getName(), ' final=', var_export($rc->isFinal(), true), "\n";   // Invoice final=true

foreach ($rc->getMethods() as $m) {
    $vis = $m->isPublic() ? 'public' : ($m->isProtected() ? 'protected' : 'private');
    echo "method {$vis} {$m->getName()}({$m->getNumberOfParameters()} tham số)\n";
}
// method public __construct(3 tham số)
// method public send(2 tham số)
// method private sign(0 tham số)

foreach ($rc->getConstructor()->getParameters() as $p) {
    $type = $p->getType();                    // ReflectionNamedType, ReflectionUnionType hoặc null
    echo '$', $p->getName(), ': ', $type, ' | nullable=', var_export($type?->allowsNull(), true);
    if ($p->isDefaultValueAvailable()) {
        echo ' | mặc định=', var_export($p->getDefaultValue(), true);
    }
    echo ' | ', get_class($type), "\n";
}
// $id: int | nullable=false | ReflectionNamedType
// $note: ?string | nullable=true | mặc định=NULL | ReflectionNamedType
// $total: int|float | nullable=false | mặc định=0 | ReflectionUnionType

$invoice = new Invoice(7);
$prop = $rc->getProperty('secret');
echo $prop->getValue($invoice), "\n";         // không ai thấy
```

Dòng cuối đọc được property `private` từ bên ngoài. Trước PHP 8.1 phải gọi `$prop->setAccessible(true)`
trước; từ 8.1 không cần nữa, và từ 8.5 gọi `setAccessible()` phát deprecation ("has no effect since
PHP 8.1").

### 8.4 Ứng dụng: container tự tạo dependency

Bài toán: `UserService` cần `Database` và `Mailer`, `Database` lại cần `Config`. Tự viết
`new UserService(new Database(new Config()), new Mailer())` ở mọi nơi rất mệt. Một *DI container*
(Dependency Injection container) đọc constructor bằng Reflection rồi tự tạo đệ quy:

```php
<?php
declare(strict_types=1);

final class Container
{
    /** @var array<class-string, object> */
    private array $instances = [];

    /**
     * @template T of object
     * @param class-string<T> $class
     * @return T
     */
    public function make(string $class): object
    {
        if (isset($this->instances[$class])) {
            return $this->instances[$class];          // mỗi class chỉ tạo một lần (singleton)
        }

        $rc = new ReflectionClass($class);            // class không tồn tại: ReflectionException
        if (!$rc->isInstantiable()) {
            throw new LogicException("{$class} không tạo được (interface/abstract?)");
        }

        $args = [];
        foreach ($rc->getConstructor()?->getParameters() ?? [] as $param) {
            $type = $param->getType();
            if ($type instanceof ReflectionNamedType && !$type->isBuiltin()) {
                $args[] = $this->make($type->getName());   // tham số là class: tạo đệ quy
            } elseif ($param->isDefaultValueAvailable()) {
                $args[] = $param->getDefaultValue();       // int, string... có mặc định
            } else {
                throw new LogicException("Không biết truyền gì cho \${$param->getName()} của {$class}");
            }
        }

        return $this->instances[$class] = $rc->newInstanceArgs($args);
    }
}

final class Config   { public function __construct(public string $dsn = 'sqlite::memory:') {} }
final class Database { public function __construct(public Config $config) {} }
final class Mailer   { public function __construct(public int $retries = 3) {} }
final class UserService
{
    public function __construct(public Database $db, public Mailer $mailer) {}
}

$c = new Container();
$service = $c->make(UserService::class);              // không cần tự new 4 object
echo $service->db->config->dsn, ' ', $service->mailer->retries, "\n";   // sqlite::memory: 3
var_dump($service->db === $c->make(Database::class)); // bool(true)

try {
    $c->make(Countable::class);
} catch (LogicException $e) {
    echo $e->getMessage(), "\n";                      // Countable không tạo được (interface/abstract?)
}
```

Container thật (Laravel) làm cùng ý tưởng, cộng thêm: binding interface sang class cụ thể, phát hiện
vòng phụ thuộc, scope (singleton, scoped), contextual binding. Chi tiết ở chương 26.

### 8.5 Lưu ý khi dùng Reflection

- ⚠️ `getType()` có thể trả `null` (tham số không khai báo kiểu), `ReflectionNamedType`, hoặc
  `ReflectionUnionType`/`ReflectionIntersectionType` (không có method `getName()`). Luôn kiểm tra
  `instanceof ReflectionNamedType` trước khi gọi `getName()`, như ví dụ container.
- ⚠️ Reflection phá đóng gói: đọc/ghi được `private`. Đó là quyền dành cho hạ tầng (framework, test,
  serializer); đừng dùng nó trong code nghiệp vụ để "lách" visibility.
- Reflection chậm hơn gọi trực tiếp. Thư viện dùng nhiều thường cache kết quả, hoặc sinh sẵn code lúc
  build (Symfony biên dịch container thành file PHP).
- `getMethods()`, `getProperties()` nhận bộ lọc, ví dụ `ReflectionMethod::IS_PUBLIC`.

## 9. Attributes

### 9.1 Attribute là gì

*Attribute* (PHP 8.0) là **metadata có cấu trúc** gắn lên class, method, hàm, tham số, property, hằng
class, và từ 8.5 cả hằng toàn cục. Viết dạng `#[Ten(tham số)]` ngay trước phần tử được gắn:

```php
#[Route('/users', method: 'POST')]
public function store(): void {}
```

Trước PHP 8, framework dùng *annotation* trong docblock (`/** @Route("/users") */`): chỉ là comment,
thư viện phải tự parse chuỗi, gõ sai không ai báo. Attribute là cú pháp thật của ngôn ngữ: tên được
resolve theo namespace như tên class, tham số là biểu thức PHP.

Điểm quan trọng nhất: **attribute tự nó không làm gì cả**. Nó chỉ là dữ liệu nằm cạnh code. Phải có
code khác đọc nó bằng Reflection rồi hành động (đăng ký route, kiểm tra quyền...). Ngoại lệ là vài
attribute có sẵn mà chính engine PHP đọc (mục 9.4).

Vì `#` mở đầu comment một dòng trong PHP 7, dòng `#[Route('/users')]` ở PHP 7 là comment và bị bỏ
qua. Nhờ vậy thư viện thêm attribute được mà vẫn chạy trên bản cũ (chỉ khi attribute nằm trọn trên một
dòng riêng).

### 9.2 Cú pháp và khai báo attribute class

- Một `#[...]` chứa được nhiều attribute cách nhau bởi dấu phẩy; cũng có thể viết nhiều `#[...]` liên tiếp.
- Tham số chỉ được là giá trị literal hoặc constant expression (hằng, enum case, mảng, phép toán hằng).
  Dùng được cả tham số theo vị trí lẫn *named argument*.
- Mỗi attribute nên tương ứng một class. Class đó được đánh dấu bằng attribute `#[Attribute]`, kèm
  bitmask chỉ nơi được phép gắn:

| Hằng | Gắn lên |
|---|---|
| `Attribute::TARGET_CLASS` | Class (gồm cả interface, trait, enum) |
| `Attribute::TARGET_FUNCTION`, `TARGET_METHOD` | Hàm, method |
| `Attribute::TARGET_PROPERTY`, `TARGET_PARAMETER` | Property, tham số |
| `Attribute::TARGET_CLASS_CONSTANT` | Hằng class (gồm cả enum case) |
| `Attribute::TARGET_CONSTANT` | Hằng toàn cục khai báo bằng `const` (8.5) |
| `Attribute::TARGET_ALL` | Mọi nơi (mặc định) |
| `Attribute::IS_REPEATABLE` | Cho phép gắn nhiều lần trên cùng một phần tử |

### 9.3 Đọc attribute bằng Reflection

Ví dụ: router tự đăng ký route từ attribute trên controller.

```php
<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_METHOD | Attribute::IS_REPEATABLE)]
final class Route
{
    public function __construct(
        public string $path,
        public string $method = 'GET',
    ) {}
}

#[Attribute(Attribute::TARGET_CLASS)]
final class Prefix
{
    public function __construct(public string $value) {}
}

#[Prefix('/users')]
final class UserController
{
    #[Route('')]
    public function index(): string { return 'danh sách user'; }

    #[Route('', method: 'POST')]                    // named argument
    public function store(): string { return 'tạo user'; }

    #[Route('/{id}'), Route('/{id}/profile')]       // hai attribute trong một #[...]
    public function show(): string { return 'xem user'; }

    public function helper(): void {}               // không có attribute: không phải route
}

/** @return list<array{string, string, string}> */
function routesOf(string $controller): array
{
    $rc = new ReflectionClass($controller);
    $prefix = '';
    foreach ($rc->getAttributes(Prefix::class) as $attr) {
        $prefix = $attr->newInstance()->value;      // lúc này mới chạy constructor của Prefix
    }

    $routes = [];
    foreach ($rc->getMethods(ReflectionMethod::IS_PUBLIC) as $m) {
        foreach ($m->getAttributes(Route::class) as $attr) {
            $route = $attr->newInstance();
            $routes[] = [$route->method, $prefix . $route->path, $m->getName()];
        }
    }
    return $routes;
}

foreach (routesOf(UserController::class) as [$method, $path, $action]) {
    echo str_pad($method, 5), $path, ' -> ', $action, "\n";
}
// GET  /users -> index
// POST /users -> store
// GET  /users/{id} -> show
// GET  /users/{id}/profile -> show

$attr = (new ReflectionMethod(UserController::class, 'store'))->getAttributes()[0];
echo $attr->getName(), "\n";                        // Route
var_dump($attr->getArguments());                    // array(2) { [0]=> string(0) "" ["method"]=> string(4) "POST" }
```

API cần nhớ:

- `getAttributes(?string $name = null, int $flags = 0)` có trên `ReflectionClass`, `ReflectionMethod`,
  `ReflectionFunction`, `ReflectionProperty`, `ReflectionParameter`, `ReflectionClassConstant`. Trả về
  mảng `ReflectionAttribute`. Truyền `$name` để lọc theo đúng tên; thêm cờ
  `ReflectionAttribute::IS_INSTANCEOF` để lấy cả attribute là class con hoặc implement interface đó.
- `ReflectionAttribute::getName()`, `getArguments()`: đọc tên và tham số **mà không tạo object**.
- `ReflectionAttribute::newInstance()`: tạo object attribute (chạy constructor của nó).

⚠️ Đọc metadata thì không kiểm tra gì. Class attribute không tồn tại, gắn sai target, gắn lặp lại một
attribute không `IS_REPEATABLE`, sai kiểu tham số: tất cả chỉ lộ ra khi gọi `newInstance()`:

```php
<?php
declare(strict_types=1);

#[Attribute(Attribute::TARGET_METHOD)]
final class Route { public function __construct(public string $path) {} }

#[Route('/sai-cho')]                 // Route chỉ cho phép đặt trên method
#[KhongTonTai]                       // class attribute không tồn tại
final class Demo {}

$attrs = (new ReflectionClass(Demo::class))->getAttributes();
echo count($attrs), "\n";            // 2   đọc metadata: chưa có lỗi gì
foreach ($attrs as $a) {
    try {
        $a->newInstance();
    } catch (Error $e) {
        echo $e->getMessage(), "\n";
    }
}
// Attribute "Route" cannot target class (allowed targets: method)
// Attribute class "KhongTonTai" not found
```

Framework thường đọc attribute một lần rồi cache kết quả (route cache, container cache), vì quét
Reflection mỗi request là lãng phí.

### 9.4 Attribute có sẵn của PHP

Các attribute này do engine tự đọc, nên có tác dụng ngay mà không cần code của bạn:

| Attribute | Từ bản | Tác dụng |
|---|---|---|
| `#[\Attribute]` | 8.0 | Đánh dấu một class là attribute class (9.2) |
| `#[\ReturnTypeWillChange]` | 8.1 | Tắt deprecation khi method ghi đè method của class built-in mà chưa khai báo kiểu trả về tương thích |
| `#[\AllowDynamicProperties]` | 8.2 | Cho phép class (và class con) tạo dynamic property không bị deprecation |
| `#[\SensitiveParameter]` | 8.2 | Che giá trị tham số trong stack trace |
| `#[\Override]` | 8.3 (property từ 8.5) | Khẳng định method/property đang ghi đè cha hoặc cài đặt interface |
| `#[\Deprecated]` | 8.4 (trait và hằng toàn cục từ 8.5) | Đánh dấu hàm/method/hằng của bạn là deprecated |
| `#[\NoDiscard]` | 8.5 | Cảnh báo khi giá trị trả về bị bỏ qua |
| `#[\DelayedTargetValidation]` | 8.5 | Hoãn lỗi "gắn sai chỗ" của attribute built-in từ lúc biên dịch tới lúc `newInstance()` |

`#[\Override]`: nếu cha (hoặc interface) không có method cùng tên, PHP báo lỗi ngay lúc nạp class. Nó
bắt đúng loại bug gõ sai tên hoặc cha đổi tên method mà con không biết, khiến method con thành method
mồ côi không ai gọi:

```php
<?php
declare(strict_types=1);

class BaseLogger
{
    public function format(string $msg): string { return $msg; }
}

final class JsonLogger extends BaseLogger
{
    #[\Override]
    public function fromat(string $msg): string    // gõ sai tên: tưởng ghi đè nhưng thật ra là method mới
    {
        return json_encode(['m' => $msg], JSON_THROW_ON_ERROR);
    }
}
// Fatal error: JsonLogger::fromat() has #[\Override] attribute, but no matching parent method exists
```

`#[\Deprecated]`: gọi tới phần tử bị đánh dấu thì phát `E_USER_DEPRECATED`, giống hàm built-in bị
deprecated. Thư viện dùng nó để báo người dùng chuyển sang API mới:

```php
<?php
declare(strict_types=1);

final class Mailer
{
    #[\Deprecated(message: 'dùng sendV2()', since: '3.0')]
    public function send(string $to): void { echo "send $to\n"; }

    public function sendV2(string $to): void { echo "sendV2 $to\n"; }
}

(new Mailer())->send('an@example.com');
// Deprecated: Method Mailer::send() is deprecated since 3.0, dùng sendV2() in ... on line 12
// send an@example.com
```

`#[\SensitiveParameter]`: stack trace của exception có thể chứa giá trị tham số, và trace thường được
ghi vào log hoặc gửi lên hệ thống theo dõi lỗi. Tham số gắn attribute này được thay bằng object
`SensitiveParameterValue`:

```php
<?php
declare(strict_types=1);

function login(string $user, #[\SensitiveParameter] string $password): never
{
    throw new RuntimeException('DB không kết nối được');
}

try {
    login('an', 'mat-khau-bi-mat');
} catch (RuntimeException $e) {
    echo $e->getTraceAsString(), "\n";
    // #0 /duong-dan/vidu.php(10): login('an', Object(SensitiveParameterValue))
    // #1 {main}
}
```

Output trên có tham số vì ini `zend.exception_ignore_args` đang tắt (giá trị mặc định khi không có
php.ini, và của `php.ini-development`). `php.ini-production` bật nó, khi đó trace không ghi tham số
nào. Đừng dựa vào cấu hình server: tham số nhạy cảm (mật khẩu, token, số thẻ) nên luôn được gắn
`#[\SensitiveParameter]`.

`#[\NoDiscard]` (8.5) dành cho hàm mà bỏ qua giá trị trả về gần như chắc chắn là bug: gọi mà không
dùng kết quả thì PHP phát warning, cố ý bỏ qua thì viết `(void) tenHam(...)`. Ví dụ và cách dùng ở
[chương 08](08-ham.md).

### 9.5 Attribute trong Laravel

Laravel dùng attribute ngày càng nhiều thay cho property cấu hình hay đăng ký trong service provider.
Hai ví dụ có trong Laravel 13:

```php
use Illuminate\Container\Attributes\Config;
use Illuminate\Database\Eloquent\Attributes\ObservedBy;

#[ObservedBy(UserObserver::class)]          // gắn observer cho model ngay trên class
class User extends Model {}

class ReportService
{
    public function __construct(
        #[Config('app.timezone')] private string $timezone,   // container inject giá trị config
    ) {}
}
```

Bên dưới vẫn là cơ chế ở mục 9.3: container và Eloquent đọc attribute bằng Reflection rồi hành động.
Chi tiết ở [chương 26](26-laravel-container-provider-facade.md) và [chương 27](27-laravel-database-eloquent.md).

## 10. Lazy objects (PHP 8.4)

### 10.1 Bài toán: tạo object tốn kém mà có khi không dùng tới

Một DI container tạo sẵn `ExchangeRates` cho controller, và constructor của nó gọi API lấy tỷ giá.
Nếu request này rốt cuộc không cần đổi tiền, lời gọi API đó là phí. Tương tự, ORM trả về entity
`Order` có quan hệ `customer`; nạp sẵn mọi `Customer` từ DB là lãng phí nếu không ai đọc tới.

*Lazy object* là object mà việc khởi tạo thật bị **hoãn tới lần đầu tiên có ai đọc hoặc ghi trạng
thái của nó**. Người dùng object không cần biết nó lazy: cứ dùng như object thường, engine tự khởi tạo
đúng lúc.

Trước 8.4, thư viện như Doctrine ORM, Symfony DI phải tự làm việc này trong PHP thuần (thư viện
`ocramius/proxy-manager`, `symfony/var-exporter`): sinh class proxy kế thừa class gốc, dựa vào magic
method. Cách đó phức tạp, tốn chi phí magic method, và không dùng được với class `final`. RFC *Lazy
Objects* đưa cơ chế này vào engine.

### 10.2 Ghost và proxy

Lazy object được tạo qua Reflection, với một hàm sẽ được gọi khi cần khởi tạo:

- *Lazy ghost* (`ReflectionClass::newLazyGhost($initializer)`): chính object đó được khởi tạo **tại
  chỗ**. Hàm initializer nhận object và tự điền trạng thái (thường là gọi `$obj->__construct(...)`).
  Khởi tạo xong, object không khác gì object chưa từng lazy.
- *Lazy proxy* (`ReflectionClass::newLazyProxy($factory)`): hàm factory **trả về một object thật**
  khác; từ đó mọi truy cập property trên proxy được chuyển sang object thật. Dùng khi việc tạo object
  thật do bên khác đảm nhận (ví dụ một factory có sẵn). Proxy và object thật là hai object khác nhau.

```php
<?php
declare(strict_types=1);

final class ExchangeRates
{
    /** @var array<string, float> */
    public array $rates;

    public function __construct(string $source)
    {
        echo "  [tải tỷ giá từ $source...]\n";       // giả lập việc tốn kém: gọi API, đọc file lớn
        $this->rates = ['USD' => 26000.0, 'EUR' => 30000.0];
    }

    public function name(): string { return 'tỷ giá'; }   // method không đụng tới state

    public function convert(float $amount, string $currency): float
    {
        return $amount * $this->rates[$currency];
    }
}

$rc = new ReflectionClass(ExchangeRates::class);

// Ghost: chính object này sẽ được khởi tạo tại chỗ khi cần
$rates = $rc->newLazyGhost(function (ExchangeRates $obj): void {
    $obj->__construct('api.example.com');
});

echo "đã tạo object\n";
var_dump($rc->isUninitializedLazyObject($rates));   // bool(true)
echo $rates->name(), "\n";                           // tỷ giá   (không đụng state: chưa khởi tạo)
var_dump($rc->isUninitializedLazyObject($rates));   // bool(true)
echo $rates->convert(2, 'USD'), "\n";                // [tải tỷ giá từ api.example.com...] rồi 52000
var_dump($rc->isUninitializedLazyObject($rates));   // bool(false)
var_dump($rates instanceof ExchangeRates);           // bool(true)   ghost giống hệt object thường

// Proxy: hàm factory trả về object thật, proxy chuyển mọi truy cập sang đó
$proxy = $rc->newLazyProxy(fn(ExchangeRates $p): ExchangeRates => new ExchangeRates('file.json'));
echo $proxy->convert(1, 'EUR'), "\n";                // [tải tỷ giá từ file.json...] rồi 30000
```

Lưu ý `ExchangeRates` là class `final`: lazy object của engine vẫn làm được, điều mà cách sinh class
proxy kế thừa trước đây không làm được.

### 10.3 Khi nào khởi tạo được kích hoạt

Theo manual, khởi tạo xảy ra trước các thao tác **quan sát hoặc thay đổi trạng thái**: đọc/ghi
property, `isset()`/`unset()` property, đọc/ghi qua `ReflectionProperty`, `get_object_vars()`, `foreach`
trên property, `serialize()`, `json_encode()`, `clone`.

Không kích hoạt:

- Gọi method mà method đó không đụng tới property (như `name()` ở trên).
- `var_dump()` (in ra dạng `lazy ghost object(...)` với property `uninitialized`), ép `(array)`,
  `get_mangled_object_vars()`.
- Các API Reflection dành riêng: `ReflectionProperty::skipLazyInitialization()`,
  `setRawValueWithoutLazyInitialization()` (đặt sẵn một property, ví dụ `id`, mà không khởi tạo cả
  object).

Các API khác trên `ReflectionClass`: `initializeLazyObject($obj)` (ép khởi tạo ngay),
`markLazyObjectAsInitialized($obj)`, `resetAsLazyGhost()`/`resetAsLazyProxy()` (biến object có sẵn
thành lazy), `isUninitializedLazyObject($obj)`.

⚠️ Giới hạn và bẫy:

- Chỉ class do người dùng định nghĩa và `stdClass`. Class built-in (và class con của chúng) thì không:
  `newLazyGhost` trên `ArrayObject` ném
  `Error: Cannot make instance of internal class lazy: ArrayObject is internal`.
- Nếu initializer ném exception, object được trả về trạng thái trước khi khởi tạo và vẫn lazy (không
  để lộ object khởi tạo dở). Tác dụng phụ ra bên ngoài (đã ghi log, đã gọi API) thì không hoàn tác.
- Với proxy, `$proxy === $realInstance` là `false`. Code dựa vào định danh object (`===`,
  `spl_object_id`, `WeakMap`) cần cẩn thận.
- Lỗi trong initializer (mất kết nối API, sai cấu hình) nổ ra **ở chỗ dùng object lần đầu**, có khi
  cách xa chỗ tạo, làm stack trace khó đọc hơn.

Đây là tính năng cho **tác giả framework/thư viện**. Code ứng dụng hiếm khi gọi `newLazyGhost` trực
tiếp; bạn hưởng lợi gián tiếp khi container hay ORM dùng nó.

## 11. Serialize, unserialize và rủi ro

### 11.1 Serialize là gì

*Serialize* là biến một giá trị trong bộ nhớ (kể cả object) thành **chuỗi** để lưu xuống file, cache,
DB hoặc gửi qua hàng đợi; *unserialize* là dựng lại giá trị từ chuỗi đó. PHP có định dạng riêng qua
cặp hàm `serialize()`/`unserialize()`. Bạn dùng nó gián tiếp hằng ngày: Laravel serialize giá trị khi
ghi vào cache, và serialize object job khi đẩy vào queue ([chương 29](29-laravel-queue-event-schedule-cache.md)).

```php
<?php
declare(strict_types=1);

final class Point
{
    public function __construct(
        public int $x,
        protected int $y,
        private string $label,
    ) {}
}

echo serialize(42), "\n";                              // i:42;
echo serialize('xin chào'), "\n";                      // s:9:"xin chào";   (9 là số BYTE, không phải ký tự)
echo serialize([1, 'a' => true, 'b' => null]), "\n";   // a:3:{i:0;i:1;s:1:"a";b:1;s:1:"b";N;}

$s = serialize(new Point(1, 2, 'A'));
echo str_replace("\0", '\0', $s), "\n";                // in \0 cho dễ thấy byte NUL
// O:5:"Point":3:{s:1:"x";i:1;s:4:"\0*\0y";i:2;s:12:"\0Point\0label";s:1:"A";}

$p = unserialize($s);
var_dump($p == new Point(1, 2, 'A'));                  // bool(true)
```

Đọc định dạng: `i` là int, `s:9:"..."` là chuỗi dài 9 byte, `a:3:{...}` là mảng 3 phần tử, `N` là
null, `O:5:"Point":3:{...}` là object class `Point` (tên dài 5) có 3 property. Property `protected`
được ghi với tiền tố `\0*\0`, `private` với `\0TênClass\0` (`\0` là byte NUL). Hai điều rút ra:

- Chuỗi serialize **ghi tên class**. `unserialize()` sẽ tạo object của đúng class đó, không gọi
  constructor, rồi gán property theo nội dung chuỗi. Đây là gốc của lỗ hổng ở 11.4.
- Chuỗi chứa byte NUL, nên khi lưu vào cột text hay gửi qua kênh không an toàn với nhị phân, người ta
  thường `base64_encode()` thêm một lớp.

### 11.2 Tự điều khiển: `__serialize()` và `__unserialize()`

Không phải mọi thứ serialize được. Kết nối DB, closure, file handle là trạng thái của tiến trình đang
chạy, không có ý nghĩa khi dựng lại ở nơi khác. Cặp magic method `__serialize()`/`__unserialize()`
(PHP 7.4) cho class tự quyết định lưu gì và dựng lại thế nào:

```php
<?php
declare(strict_types=1);

final class Repository
{
    private PDO $pdo;                                  // kết nối DB: không serialize được

    public function __construct(private string $dsn)
    {
        $this->connect();
    }

    private function connect(): void
    {
        echo "  [kết nối $this->dsn]\n";
        $this->pdo = new PDO($this->dsn);
    }

    public function count(): int
    {
        return (int) $this->pdo->query('SELECT 1')->fetchColumn();
    }

    /** @return array{dsn: string} */
    public function __serialize(): array
    {
        return ['dsn' => $this->dsn];                  // chỉ lưu thứ cần để dựng lại
    }

    /** @param array{dsn: string} $data */
    public function __unserialize(array $data): void   // KHÔNG có constructor nào được gọi
    {
        $this->dsn = $data['dsn'];
        $this->connect();                              // tự mở lại kết nối
    }
}

try {
    serialize(new PDO('sqlite::memory:'));
} catch (Exception $e) {
    echo $e->getMessage(), "\n";                       // Serialization of 'PDO' is not allowed
}
try {
    serialize(fn() => 1);
} catch (Exception $e) {
    echo $e->getMessage(), "\n";                       // Serialization of 'Closure' is not allowed
}

$repo = new Repository('sqlite::memory:');            //   [kết nối sqlite::memory:]
$data = serialize($repo);
echo $data, "\n";                                      // O:10:"Repository":1:{s:3:"dsn";s:15:"sqlite::memory:";}
$copy = unserialize($data);                            //   [kết nối sqlite::memory:]
echo $copy->count(), "\n";                             // 1
```

- `__serialize()` phải trả về **mảng**; mảng đó không cần khớp với property (manual: "không bắt buộc").
- `__unserialize(array $data)` nhận lại đúng mảng đó. Constructor **không** được gọi khi unserialize,
  nên mọi bước khởi tạo cần thiết phải nằm trong `__unserialize`.
- Class có `__serialize` thì `__sleep` bị bỏ qua; có `__unserialize` thì `__wakeup` bị bỏ qua.

### 11.3 Các cơ chế cũ

| Cơ chế | Tình trạng |
|---|---|
| `__sleep(): array` (trả về danh sách tên property cần lưu) + `__wakeup(): void` | *Soft-deprecated* từ 8.5: manual khuyên chuyển sang `__serialize`/`__unserialize`, nhưng chưa phát cảnh báo khi chạy. `__sleep` không trả được tên property `private` của class cha |
| Interface `Serializable` (method `serialize()`/`unserialize()`) | Deprecated từ 8.1 nếu class không có thêm `__serialize`/`__unserialize`: phát "S implements the Serializable interface, which is deprecated..." |

Code mới chỉ dùng `__serialize`/`__unserialize`. Thư viện cần chạy cả PHP cũ thì viết cả hai cặp.

Vài điều cần biết thêm:

- Enum serialize thành định dạng riêng `E:...` và `unserialize` trả về đúng singleton (mục 3.6).
- Property hook: `serialize()` dùng giá trị thô, bỏ qua hook; virtual property không được lưu (mục 5.3).
- Unserialize chuỗi hỏng: trả `false` kèm `E_WARNING` (từ 8.3 là warning thay vì notice); từ 8.3
  chuỗi thừa byte ở cuối cũng phát `E_WARNING`.

### 11.4 Rủi ro: object injection

⚠️ **Không bao giờ `unserialize()` dữ liệu mà người dùng sửa được** (cookie, tham số request, file
upload, dữ liệu từ hệ thống khác). Lý do nằm ở 11.1: chuỗi serialize quyết định class nào được tạo và
property mang giá trị gì. Kết hợp với magic method chạy tự động (`__wakeup`/`__unserialize` ngay khi
dựng, `__destruct` khi object bị huỷ, `__toString` khi bị dùng như chuỗi), kẻ tấn công điều khiển được
code có sẵn trong app chạy với dữ liệu của họ:

```php
<?php
declare(strict_types=1);

// Một class hoàn toàn vô hại có sẵn trong code (hoặc trong vendor/)
final class TempFile
{
    public function __construct(public string $path) {}

    public function __destruct()
    {
        echo "  [xoá file {$this->path}]\n";          // code thật sẽ là unlink($this->path)
    }
}

// App lưu giỏ hàng vào cookie bằng serialize(), rồi đọc lại bằng unserialize().
// Kẻ tấn công sửa cookie thành chuỗi này:
$cookie = 'O:8:"TempFile":1:{s:4:"path";s:13:"/var/www/.env";}';

echo "1) unserialize không giới hạn:\n";
$cart = unserialize($cookie);                         // tạo TempFile với path do kẻ tấn công chọn
unset($cart);                                         //   [xoá file /var/www/.env]

echo "2) allowed_classes => false:\n";
$cart = unserialize($cookie, ['allowed_classes' => false]);
echo get_class($cart), "\n";                          // __PHP_Incomplete_Class   (không có method nào chạy)
unset($cart);

echo "3) JSON: chỉ dựng lại mảng và giá trị vô hướng\n";
var_dump(json_decode('{"items":[1,2]}', true));       // array(1) { ["items"]=> array(2) {...} }
```

Lỗ hổng này gọi là *object injection* (OWASP xếp vào nhóm *insecure deserialization*). Trong thực tế,
kẻ tấn công nối nhiều class có sẵn trong `vendor/` thành một chuỗi gọi nhau (*POP chain*,
Property-Oriented Programming) để đi tới thao tác nguy hiểm như ghi file hay chạy lệnh; có công cụ
dựng sẵn chuỗi cho các thư viện phổ biến. Cách phòng:

1. Dữ liệu đi qua ranh giới tin cậy dùng **JSON** (`json_encode`/`json_decode`): JSON chỉ dựng lại mảng
   và giá trị vô hướng, không tạo object của class tuỳ ý.
2. Buộc phải unserialize thì truyền `allowed_classes` (`false` hoặc danh sách class được phép). Object
   của class không được phép thành `__PHP_Incomplete_Class`. Manual vẫn cảnh báo: đừng đưa input không
   tin cậy vào `unserialize()` **dù** đã đặt `allowed_classes`. Option này cũng không áp dụng cho enum.
3. Dữ liệu do chính bạn tạo nhưng phải đi qua tay người dùng (cookie): ký bằng HMAC (`hash_hmac`) và
   kiểm chữ ký bằng `hash_equals()` **trước** khi unserialize.
4. Option `max_depth` (7.4) giới hạn độ sâu lồng nhau để chống tràn stack.

Chi tiết tấn công và các lỗ hổng liên quan (lộ `APP_KEY` của Laravel, `phar://`) ở
[chương 17](17-bao-mat.md).

## 12. `WeakReference` và `WeakMap`

### 12.1 Nhắc lại: khi nào object được giải phóng

PHP đếm số chỗ đang giữ một object (*reference count*, refcount): mỗi biến, phần tử mảng, property
trỏ tới object làm refcount tăng 1. Khi refcount về 0, object được giải phóng ngay (và `__destruct`
chạy). Cơ chế chi tiết, kể cả cách dọn vòng tham chiếu, ở [chương 19](19-ben-trong-engine.md).

Hệ quả: một mảng cache chứa object cũng là một "chỗ giữ". Object nằm trong cache sẽ **không bao giờ**
được giải phóng chừng nào cache còn sống. Trong PHP-FPM, mỗi request dọn sạch bộ nhớ nên ít ai thấy;
trong process sống lâu (queue worker, Laravel Octane) thì cache kiểu đó phình mãi: *memory leak*.

*Weak reference* (tham chiếu yếu) là tham chiếu **không làm tăng refcount**: nó "nhớ" object mà không
giữ object sống.

### 12.2 `WeakReference` (7.4) và `WeakMap` (8.0)

- `WeakReference::create($obj)` tạo tham chiếu yếu; `->get()` trả object, hoặc `null` nếu object đã
  bị giải phóng.
- `WeakMap` là map có **key là object**, và key được giữ yếu. Khi object không còn ai giữ, mục tương ứng
  tự biến mất (value của mục đó cũng được thả). Dùng như mảng: `$map[$obj] = ...`, `isset()`,
  `unset()`, `count()`, `foreach`.

```php
<?php
declare(strict_types=1);

final class Order
{
    /** @param list<int> $prices */
    public function __construct(public array $prices) {}
}

// 1) WeakReference: "nhớ" một object mà không giữ nó sống
$order = new Order([100, 250]);
$ref = WeakReference::create($order);
var_dump($ref->get() === $order);     // bool(true)
unset($order);                        // biến cuối cùng giữ Order biến mất -> Order được giải phóng
var_dump($ref->get());                // NULL

// 2) WeakMap: cache theo object, mục tự biến mất khi object chết
final class TotalCache
{
    /** @var WeakMap<Order, int> */
    private WeakMap $map;

    public function __construct() { $this->map = new WeakMap(); }

    public function totalOf(Order $o): int
    {
        if (!isset($this->map[$o])) {
            echo "  [tính tổng]\n";
            $this->map[$o] = array_sum($o->prices);
        }
        return $this->map[$o];
    }

    public function size(): int { return count($this->map); }
}

$cache = new TotalCache();
$a = new Order([100, 250]);
echo $cache->totalOf($a), "\n";       //   [tính tổng]  rồi 350
echo $cache->totalOf($a), "\n";       // 350   (lấy từ cache)
echo $cache->size(), "\n";            // 1
unset($a);                            // không ai giữ Order nữa
echo $cache->size(), "\n";            // 0    mục tự biến mất

// 3) So sánh: SplObjectStorage giữ object sống
$storage = new SplObjectStorage();
$b = new Order([1]);
$storage[$b] = 1;
$ref2 = WeakReference::create($b);
unset($b);
var_dump($ref2->get() !== null);      // bool(true)  Order vẫn sống vì $storage còn giữ
echo count($storage), "\n";           // 1
```

### 12.3 Dùng khi nào, và vì sao cách "tự chế" sai

Ứng dụng điển hình:

- Cache dữ liệu **suy ra từ object** mà không kéo dài đời sống object (ví dụ trên).
- Gắn thêm dữ liệu vào object **của thư viện khác** mà bạn không sửa được class. Từ 8.2, gắn dynamic
  property bị deprecated, và UPGRADING của PHP 8.2 gợi ý đúng cách này: dùng `WeakMap` với key là object.
- Đăng ký listener/observer mà không giữ đối tượng sống mãi.

⚠️ Hai cách tự chế hay gặp đều sai:

- Mảng với key `spl_object_id($obj)`: mục không bao giờ tự mất nên cache phình mãi. Tệ hơn, manual ghi
  rõ id có thể được **tái dùng** cho object mới sau khi object cũ bị huỷ, nên object mới đọc nhầm kết
  quả của object cũ:

```php
<?php
declare(strict_types=1);

final class Order { public function __construct(public int $total) {} }

$cache = [];                                    // ⚠️ cache sai: key là spl_object_id
$x = new Order(100);
$cache[spl_object_id($x)] = $x->total * 2;
unset($x);                                      // Order bị giải phóng, mục trong $cache vẫn còn

$y = new Order(5);                              // object mới có thể nhận lại id cũ
var_dump(isset($cache[spl_object_id($y)]));     // bool(true)  <- đọc nhầm kết quả của object cũ
echo $cache[spl_object_id($y)], "\n";           // 200
```

- `SplObjectStorage` hoặc mảng chứa chính object: cache giữ object sống, không bao giờ được giải phóng.

Lưu ý thêm: nếu **value** trong `WeakMap` lại trỏ ngược về chính key, key bị giữ gián tiếp qua value.
Từ PHP 8.3, bộ dọn vòng tham chiếu xử lý được trường hợp này (UPGRADING 8.3: WeakMap có hành vi kiểu
*ephemeron*); ở bản cũ hơn các mục đó không bao giờ tự bị xoá.

Đối chiếu: Java có `WeakReference` và `WeakHashMap` cùng ý tưởng (key yếu); Go có package `weak`
(`weak.Pointer`, từ Go 1.24).

## 13. Nguyên tắc thiết kế: composition over inheritance

Chương này và chương 09 cho bạn rất nhiều công cụ: kế thừa, abstract class, interface, trait, magic,
`static::`. Một nguyên tắc giúp chọn đúng công cụ: *composition over inheritance* (ưu tiên kết hợp hơn
kế thừa).

- *Kế thừa* (`extends`) tạo quan hệ "là một" (*is-a*), và class con dính chặt vào chi tiết cài đặt của
  class cha: cha đổi một method protected là con có thể vỡ. Chuỗi kế thừa sâu khó đọc vì hành vi rải
  qua nhiều tầng (`static::` làm điều này khó lần theo hơn nữa).
- *Kết hợp* (*composition*): class **chứa** object khác (thường nhận qua constructor) và giao việc cho
  nó, quan hệ "có một" (*has-a*). Phụ thuộc vào **interface** thay vì class cụ thể thì thay được cài đặt
  (fake trong test, đổi driver) mà không sửa class dùng nó.

```php
<?php
declare(strict_types=1);

interface Notifier
{
    public function send(string $to, string $message): void;
}

final class EmailNotifier implements Notifier
{
    public function send(string $to, string $message): void { echo "email {$to}: {$message}\n"; }
}

final class FakeNotifier implements Notifier                  // dùng trong test
{
    /** @var list<string> */
    public private(set) array $sent = [];
    public function send(string $to, string $message): void { $this->sent[] = "{$to}: {$message}"; }
}

final class OrderService                                      // KHÔNG extends EmailNotifier
{
    public function __construct(private Notifier $notifier) {} // nhận dependency qua constructor

    public function place(string $customer): void
    {
        // ... lưu đơn hàng ...
        $this->notifier->send($customer, 'Đặt hàng thành công');
    }
}

(new OrderService(new EmailNotifier()))->place('an@example.com');   // email an@example.com: Đặt hàng thành công

$fake = new FakeNotifier();
(new OrderService($fake))->place('binh@example.com');
echo count($fake->sent), "\n";                                       // 1
```

Vài thói quen đi kèm:

- Đánh dấu class `final` mặc định; chỉ bỏ `final` khi thật sự thiết kế cho kế thừa. `final` cũng tránh
  luôn bẫy `new static` ở mục 2.6.
- Dùng kế thừa khi quan hệ "là một" thật sự đúng và ổn định, hoặc khi framework yêu cầu (model kế thừa
  `Model`, exception kế thừa `Exception`).
- Value object: `final readonly class` + clone with. Entity: `private(set)` + method thay đổi trạng thái.
- Magic method và Reflection là công cụ của hạ tầng; code nghiệp vụ nên tường minh để IDE và PHPStan
  kiểm tra được.

Container của Laravel tự inject `Notifier` vào `OrderService` khi bạn bind interface với cài đặt
([chương 26](26-laravel-container-provider-facade.md)). Kiểm thử bằng fake và công cụ phân tích tĩnh ở
[chương 21](21-chat-luong-code.md).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Viết `__get` mà quên `__isset`: `isset($o->x)` luôn `false`, `empty($o->x)` luôn `true` | Không có `__isset` thì PHP coi property ảo là không tồn tại | Luôn viết `__isset` đi cùng `__get` (1.2) |
| `$o->items[] = 1` trên property lấy qua `__get` hoặc property có `set` hook | `__get` trả bản copy; sửa tại chỗ thì đi vòng qua hook | Lấy ra, sửa, gán lại cả mảng; hoặc viết method `add()` (1.2, 5.5) |
| `__call` nhận mọi tên, gõ sai tên method không báo lỗi | Magic bắt cả lời gọi sai | Ném `BadMethodCallException` cho tên không hỗ trợ; khai báo `@method` (1.3, 1.7) |
| Hàm `string $s` không nhận object có `__toString` dưới `strict_types=1` | Strict mode không tự ép object thành string | Khai báo `string\|Stringable` hoặc ép `(string)` (1.4) |
| Class cha dùng `new self()` / `self::` nên class con nhận nhầm class cha | `self` là class nơi method được định nghĩa | Dùng `new static()`, `static::`, kiểu trả về `static` (2.1) |
| `new static()` vỡ khi class con đổi chữ ký constructor | Constructor của class con được gọi với tham số của cha | `final` constructor, `final` class, hoặc giữ chung chữ ký (2.6) |
| `Status::from($request->input('status'))` ném `ValueError` thành lỗi 500 | `from()` dành cho dữ liệu chắc chắn hợp lệ | `tryFrom()` + xử lý `null`, hoặc validation trước (3.3) |
| Dùng case enum làm key mảng | Enum là object, không làm key được | `->value`, hoặc `WeakMap`/`SplObjectStorage` (3.6) |
| `match` trên enum có `default` | `default` nuốt case mới thêm sau này | Liệt kê đủ case, để `UnhandledMatchError`/PHPStan báo thiếu (3.2) |
| Tin rằng `readonly` làm object bất biến hoàn toàn | `readonly` là nông, object bên trong vẫn sửa được | Property bên trong cũng phải bất biến (`DateTimeImmutable`, value object) (4.3) |
| Wither dùng clone with bỏ qua kiểm tra trong constructor | Clone with không gọi constructor | Wither tự kiểm tra, hoặc dùng `new static(...)` (7.3) |
| Khai báo property (kể cả có hook) cho cột của Eloquent model | Property khai báo chặn `__get` của model | Không khai báo; dùng cast/accessor của Eloquent (1.2, 5.5) |
| Tưởng attribute "tự chạy", hoặc lỗi attribute chỉ lộ ra trên production | Attribute chỉ là metadata; lỗi chỉ ném ở `newInstance()` | Có code đọc attribute và test cho code đó (9.3) |
| `unserialize()` dữ liệu từ cookie, request, hệ thống khác | Object injection: chuỗi quyết định class nào được tạo | Dùng JSON; bắt buộc thì `allowed_classes` + HMAC (11.4) |
| Cache theo `spl_object_id()` hoặc `SplObjectStorage` trong worker sống lâu | Mục không tự mất (leak); id bị tái dùng | `WeakMap` (12.3) |

## Tóm tắt chương

- Magic method là hook của engine: `__get`/`__set`/`__isset`/`__unset` cho property không truy cập
  được, `__call`/`__callStatic` cho method không truy cập được, `__toString`, `__invoke`, `__debugInfo`,
  `__serialize`/`__unserialize`. Chúng chỉ là lưới đỡ khi truy cập thông thường thất bại; cái giá là
  IDE/PHPStan mù, lỗi đánh máy không bị bắt, chậm hơn.
- `self` là class nơi method được định nghĩa, `static` là class được gọi lúc chạy (late static binding).
  Gọi bằng tên class là non-forwarding; `self::`, `parent::`, `static::` chuyển tiếp. `new static` là nền
  của `User::where()` trong Eloquent.
- Enum (8.1) là kiểu có tập giá trị cố định; mỗi case là singleton, so sánh bằng `===`. Backed enum gắn
  `int`/`string`, đổi bằng `from()` (ném lỗi) và `tryFrom()` (trả `null`). Enum có method, interface,
  hằng, nhưng không có state, không làm key mảng, không có thứ tự.
- `readonly` (8.1) cho property ghi một lần, readonly class (8.2) áp cho mọi property; readonly là nông.
  8.3 cho gán lại trong `__clone`, 8.4 đổi readonly thành `protected(set)` ngầm định.
- Property hooks (8.4) gắn logic `get`/`set` lên property; virtual property không có ô nhớ. Không dùng
  cùng `readonly`, không sửa từng phần tử mảng qua hook.
- Asymmetric visibility (8.4, static từ 8.5): `public private(set)` cho "ai cũng đọc, chỉ class ghi".
- Clone with (8.5): `clone($obj, ['prop' => $v])` chạy `__clone` trước rồi gán như phép gán thường, mở
  khoá readonly nhưng vẫn tôn trọng visibility; không gọi constructor.
- Reflection đọc cấu trúc code lúc chạy, là nền của DI container, attribute, lazy object. Attribute (8.0)
  là metadata, chỉ có tác dụng khi có code đọc nó; PHP có sẵn `#[\Override]`, `#[\Deprecated]`,
  `#[\SensitiveParameter]`, `#[\NoDiscard]`...
- Lazy objects (8.4): ghost khởi tạo tại chỗ, proxy chuyển tiếp sang object thật; khởi tạo khi trạng thái
  bị quan sát hoặc thay đổi.
- Không `unserialize()` dữ liệu không tin cậy; dùng `__serialize`/`__unserialize` cho class tự điều khiển.
  `WeakMap` cho cache theo object mà không giữ object sống. Ưu tiên composition và interface hơn kế thừa.

## Câu hỏi tự kiểm tra

1. Khi nào `__get` được gọi, khi nào không? Vì sao Eloquent model không khai báo property cho cột DB?
2. Class có `__get` nhưng không có `__isset`. `isset($o->name)`, `empty($o->name)` và `$o->name ?? 'x'`
   cho kết quả thế nào, magic method nào được gọi trong từng trường hợp? (mục 1.2)
3. Giải thích từng dòng output của `C::test()` ở mục 2.3 bằng khái niệm forwarding và non-forwarding call.
4. Khi nào chọn pure enum, khi nào backed enum? Với dữ liệu đọc từ DB của chính mình và với input của
   người dùng, nên dùng `from()` hay `tryFrom()`, vì sao?
5. Vì sao nói `readonly` là "nông"? Viết một ví dụ thay đổi được nội dung của một object mà mọi property
   đều `readonly`.
6. So sánh `readonly`, `public private(set)` và property có `set` hook. Bạn chọn gì cho `Order::$status`,
   `Money::$amount`, `User::$email`?
7. `clone($money, ['amount' => 1])` gọi từ bên ngoài class `Money` (property `public readonly`) có chạy
   không? Bên trong class thì sao? Clone with có chạy lại kiểm tra trong constructor không? (mục 7.3)
8. Vì sao `ReflectionClass::getAttributes()` không báo lỗi khi gắn một attribute không tồn tại, và lỗi
   sẽ lộ ra lúc nào? (mục 9.3)
9. Vì sao `unserialize()` một cookie do người dùng gửi lên là nguy hiểm, kể cả khi trong code của bạn
   không có class nào "nguy hiểm"? Kể các lớp phòng thủ theo thứ tự ưu tiên. (mục 11.4)
10. Cache với key `spl_object_id($obj)` sai ở những điểm nào? `WeakMap` giải quyết thế nào? (mục 12.3)

## Bài tập

1. **Túi cấu hình an toàn.** Viết class `Settings` lưu dữ liệu trong mảng private, dùng `__get`,
   `__set`, `__isset`, `__unset`. Chỉ cho phép các key nằm trong một whitelist (truyền qua constructor);
   key lạ thì ném exception. Viết script chứng minh `isset()`, `empty()`, `??` và `unset()` chạy đúng,
   và thêm PHPDoc `@property` cho các key. Sau đó viết lại bằng property hooks/asymmetric visibility và
   so sánh hai cách (IDE gợi ý được gì, lỗi đánh máy bị bắt ở đâu).
2. **Máy trạng thái đơn hàng bằng enum.** Viết `enum OrderStatus: string` với các case `pending`,
   `paid`, `shipped`, `delivered`, `cancelled`, `refunded`. Thêm method `canTransitionTo(self $next): bool`
   (ví dụ `pending → paid → shipped → delivered`, `pending → cancelled`, `paid → refunded`), method
   `label()` và static method `options(): array` trả `[value => label]` cho form. Viết class `Order`
   có `public private(set) OrderStatus $status` và method `transitionTo()` ném exception khi chuyển sai.
   In ra bảng mọi cặp (từ, tới) cùng kết quả.
3. **Value object `DateRange`.** Viết `final readonly class DateRange` với `start`, `end` kiểu
   `DateTimeImmutable`, ràng buộc `start <= end`. Viết `withEnd()`, `withStart()` dùng clone with (PHP
   8.5) mà vẫn giữ được ràng buộc, method `days(): int` và `overlaps(DateRange $other): bool`. Thử chứng
   minh object không thể bị sửa từ bên ngoài, và thử xem `withEnd()` có thể tạo ra khoảng ngày sai không.
4. **Validator bằng attribute.** Định nghĩa các attribute `#[Required]`, `#[Length(min: 3, max: 50)]`,
   `#[Email]` (target property). Viết hàm `validate(object $dto): array` dùng Reflection đọc attribute
   trên từng property và trả về danh sách lỗi dạng `['email' => ['Email không hợp lệ'], ...]`. Thêm
   cache metadata theo tên class để mỗi class chỉ phải quét Reflection một lần, rồi giải thích vì sao
   cache này dùng mảng thường (key là tên class) là được, không cần `WeakMap`.

## Đọc thêm

PHP manual:

- [Magic Methods](https://www.php.net/manual/en/language.oop5.magic.php) ·
  [Overloading](https://www.php.net/manual/en/language.oop5.overloading.php) ·
  [Late Static Bindings](https://www.php.net/manual/en/language.oop5.late-static-bindings.php)
- [Enumerations](https://www.php.net/manual/en/language.enumerations.php)
- [Readonly properties](https://www.php.net/manual/en/language.oop5.properties.php#language.oop5.properties.readonly-properties) ·
  [Readonly classes](https://www.php.net/manual/en/language.oop5.basic.php#language.oop5.basic.class.readonly) ·
  [Property Hooks](https://www.php.net/manual/en/language.oop5.property-hooks.php) ·
  [Asymmetric Property Visibility](https://www.php.net/manual/en/language.oop5.visibility.php#language.oop5.visibility-members-aviz) ·
  [Object Cloning](https://www.php.net/manual/en/language.oop5.cloning.php)
- [Reflection](https://www.php.net/manual/en/book.reflection.php) ·
  [Attributes](https://www.php.net/manual/en/language.attributes.php) ·
  [Predefined Attributes](https://www.php.net/manual/en/reserved.attributes.php) ·
  [Lazy Objects](https://www.php.net/manual/en/language.oop5.lazy-objects.php)
- [unserialize](https://www.php.net/manual/en/function.unserialize.php) ·
  [WeakMap](https://www.php.net/manual/en/class.weakmap.php) ·
  [WeakReference](https://www.php.net/manual/en/class.weakreference.php)

RFC (đọc phần Proposal để hiểu lý do thiết kế):

- [Enumerations](https://wiki.php.net/rfc/enumerations) ·
  [Readonly properties 2.0](https://wiki.php.net/rfc/readonly_properties_v2) ·
  [Readonly classes](https://wiki.php.net/rfc/readonly_classes) ·
  [Readonly amendments](https://wiki.php.net/rfc/readonly_amendments)
- [Property hooks](https://wiki.php.net/rfc/property-hooks) ·
  [Asymmetric visibility v2](https://wiki.php.net/rfc/asymmetric-visibility-v2) ·
  [Static asymmetric visibility](https://wiki.php.net/rfc/static-aviz) ·
  [Clone with v2](https://wiki.php.net/rfc/clone_with_v2) ·
  [Lazy objects](https://wiki.php.net/rfc/lazy-objects)
- [Attributes v2](https://wiki.php.net/rfc/attributes_v2) ·
  [#\[\Override\]](https://wiki.php.net/rfc/marking_overriden_methods) ·
  [#\[\Deprecated\]](https://wiki.php.net/rfc/deprecated_attribute) ·
  [#\[\SensitiveParameter\]](https://wiki.php.net/rfc/redact_parameters_in_back_traces) ·
  [#\[\NoDiscard\]](https://wiki.php.net/rfc/marking_return_value_as_important)
- [Custom object serialization](https://wiki.php.net/rfc/custom_object_serialization) ·
  [Weak maps](https://wiki.php.net/rfc/weak_maps) ·
  [Deprecate dynamic properties](https://wiki.php.net/rfc/deprecate_dynamic_properties)

Khác:

- php-src `UPGRADING` của từng bản 8.0 tới 8.5 (mốc phiên bản trong chương đối chiếu với các file này).
- PHPStan: [Solving "Unsafe usage of new static()"](https://phpstan.org/blog/solving-phpstan-error-unsafe-usage-of-new-static)
- Laravel 13: [Eloquent: Mutators & Casting](https://laravel.com/docs/13.x/eloquent-mutators) (enum
  casting, vì sao không sửa được phần tử của cột cast `array`), mã nguồn
  [`Illuminate/Database/Eloquent/Model.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Eloquent/Model.php)
  (`__get`, `__isset`, `__call`, `__callStatic`, `query()`).
