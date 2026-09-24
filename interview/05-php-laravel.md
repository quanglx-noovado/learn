# 05. PHP và Laravel

> [← Mục lục](README.md) · Phạm vi: PHP runtime (Zend Engine, OPcache, PHP-FPM, GC), ngôn ngữ PHP 8.x, Composer/PSR, Laravel từ lifecycle tới queue/Octane, hiệu năng, vận hành và bảo mật đặc thù PHP.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

Nếu PHP/Laravel là ngôn ngữ chính trong CV, đây là file bị đào sâu nhất. Trả lời hời hợt ở
đây bị trừ điểm nặng hơn nhiều so với không biết Go hay Java.

## Bản đồ nhanh

**PHP runtime**
- [ ] 🟡 Zend Engine (source → AST → opcode), OPcache (shared memory, `validate_timestamps`, preload)
- [ ] 🔴 JIT (PHP 8): khi nào có lợi, khi nào gần như không
- [ ] PHP-FPM: master/worker, pool, share-nothing
- [ ] 🟡 `pm = static | dynamic | ondemand`, cách tính `pm.max_children`, `pm.max_requests`
- [ ] 🟡 Slow log, `request_terminate_timeout`, status page; lifecycle MINIT/RINIT/RSHUTDOWN
- [ ] `memory_limit`, `max_execution_time` (⚠️ không tính thời gian chờ I/O trên Linux)
- [ ] 🔴 zval, refcount, copy-on-write; 🟡 GC: refcount + cycle collector

**Ngôn ngữ**
- [ ] Type system, `declare(strict_types=1)` (theo file, theo phía gọi)
- [ ] ⚠️ Type juggling, `==` vs `===`, PHP 8 đổi so sánh chuỗi/số, `in_array` so lỏng
- [ ] 🟡 Array là ordered hash table, ép kiểu key; COW khi gán, object là handle, `clone` shallow
- [ ] ⚠️ Reference `&`, cạm bẫy `foreach` by reference
- [ ] Interface, abstract class, trait (xung đột, `insteadof`)
- [ ] 🟡 `self` vs `static` (late static binding); magic methods; closure, arrow fn, `static fn`
- [ ] 🟡 Generator, `yield from`, `send()`; Iterator/IteratorAggregate
- [ ] Exception hierarchy: `Throwable`, `Exception`, `Error`
- [ ] PHP 8.0–8.4: match, named args, nullsafe, promotion, enum, readonly, fibers, first-class callable, readonly class, typed class constants, property hooks
- [ ] 🟡 Attributes; deprecated dynamic property (8.2)

**Composer / PSR**
- [ ] PSR-4 autoload, `composer.lock`, semver (`^`, `~`); 🟡 `dump-autoload -o`, `--no-dev`
- [ ] Các PSR chính: 1/12, 3, 4, 6/16, 7/15/17/18, 11, 14

**Laravel**
- [ ] Request lifecycle: `index.php` → kernel → bootstrappers → provider → middleware → router → response → terminate
- [ ] Service container: `bind`/`singleton`/`scoped`/`instance`, contextual binding, auto-wiring qua reflection
- [ ] Provider `register()` vs `boot()`, 🟡 deferred provider; facade dưới nắp
- [ ] Middleware (global/group/route, terminable); route model binding; Form Request, `validated()`
- [ ] Eloquent: relationship, eager/lazy, N+1, `preventLazyLoading`, `shouldBeStrict`
- [ ] ⚠️ `chunk` / `chunkById` / `lazy` / `cursor` khác nhau
- [ ] Mass assignment, cast, accessor, scope, observer, soft delete; ⚠️ mass update không bắn event
- [ ] Query builder vs Eloquent; transaction, retry deadlock, ⚠️ `afterCommit`
- [ ] Queue: driver, worker, `tries`/`backoff`/`timeout`/`retryUntil`, ⚠️ `retry_after`
- [ ] Failed job, batching, chaining, unique job, job middleware (`RateLimited`, `WithoutOverlapping`)
- [ ] ⚠️ `SerializesModels`; Horizon, `queue:restart`, supervisor
- [ ] Scheduler (`onOneServer`, `withoutOverlapping`); cache (tags, atomic lock)
- [ ] Event/listener (queued), notification, 🟡 broadcasting
- [ ] Auth: guard, provider, Sanctum vs Passport, Gate/Policy
- [ ] ⚠️ `config:cache` và `env()` trả `null`
- [ ] 🔴 Octane, state leak giữa request
- [ ] Công cụ test (chỉ cần biết tên); 🟡 Laravel vs Symfony

**Hiệu năng / vận hành**
- [ ] 🟡 Profiling: Xdebug, Blackfire, Tideways, XHProf/SPX
- [ ] Đọc file lớn theo dòng, export CSV streaming
- [ ] 🔴 Long-running process (worker, daemon) và memory leak

**Bảo mật đặc thù PHP**
- [ ] ⚠️ `unserialize()` dữ liệu người dùng; `include` với input (LFI/RFI); file upload
- [ ] ⚠️ So sánh hash bằng `==` ("magic hash"), `hash_equals`, `password_hash`, `APP_KEY`

## Chi tiết

### PHP runtime

- [ ] 🟡 Zend Engine và opcode
  - Mỗi lần chạy file: lexer → parser ra AST → compiler ra opcode (op array) → Zend VM thực thi.
  - Không có OPcache thì **mỗi request** đều parse và compile lại toàn bộ file được include.
  - Xem opcode: extension VLD hoặc `opcache.opt_debug_level` (chỉ để học).

- [ ] 🟡 OPcache
  - Lưu opcode đã compile vào **shared memory** dùng chung cho mọi worker của FPM master.
  - `opcache.validate_timestamps=1` thì kiểm tra mtime file mỗi `revalidate_freq` giây.
    Production thường đặt `0` và **reload FPM khi deploy**.
  - ⚠️ Deploy kiểu symlink swap (`current -> releases/123`) mà không reload FPM: OPcache và
    realpath cache vẫn trỏ code cũ. Cách xử lý: reload FPM, hoặc Nginx dùng `$realpath_root`.
  - ⚠️ `opcache.memory_consumption` hoặc `max_accelerated_files` quá nhỏ: cache đầy, hit
    rate tụt, không có lỗi rõ ràng. Theo dõi bằng `opcache_get_status()`.
  - 🔴 Preload (PHP 7.4+): nạp sẵn class vào memory khi FPM khởi động. Đổi code phải restart.

- [ ] 🔴 JIT (PHP 8.0+)
  - Nằm trong OPcache, compile opcode nóng thành mã máy. Bật bằng `opcache.jit` và
    `opcache.jit_buffer_size` (giá trị mặc định đổi qua các bản, kiểm tra lại theo phiên bản).
  - Có lợi cho code **CPU-bound** (tính toán, xử lý ảnh bằng PHP thuần). Web app điển hình
    **I/O-bound** (chờ DB, Redis, HTTP) nên lợi ích nhỏ.
  - Câu trả lời senior: "đo trước khi bật; nút thắt thường là query chứ không phải CPU".

- [ ] PHP-FPM và share-nothing
  - Một master process quản lý nhiều pool; mỗi pool có nhiều worker process.
  - Mỗi worker xử lý **một request tại một thời điểm**. Song song = số worker.
  - Share-nothing: hết request thì biến, object, kết nối không persistent đều bị giải phóng.
    Hệ quả: memory leak trong code hiếm khi tích tụ; bug state giữa request gần như không có.
  - Trade-off: mỗi request phải boot lại framework (đọc config, đăng ký provider) → đây là lý
    do có `config:cache`, OPcache, và Octane.
  - Nginx nói chuyện với FPM qua FastCGI (unix socket hoặc TCP).

- [ ] 🟡 Process manager
  | `pm` | Hành vi | Khi nào dùng |
  |---|---|---|
  | `static` | Luôn giữ đúng `pm.max_children` worker | Server riêng cho app, tải ổn định, muốn latency đều |
  | `dynamic` | Giữ trong khoảng `min_spare`–`max_spare`, tối đa `max_children` | Mặc định phổ biến, nhiều pool trên một máy |
  | `ondemand` | Chỉ fork khi có request, kill sau `process_idle_timeout` | Pool ít traffic, shared hosting; fork lúc có request làm tăng latency |
  - Cách tính `pm.max_children`: `(RAM dành cho PHP) / (RSS trung bình mỗi worker)`.
    RAM dành cho PHP = RAM máy trừ OS, Nginx, các service khác. Đo RSS thật bằng `ps`
    lúc tải cao, không lấy `memory_limit` (đó là trần, không phải trung bình).
  - Ví dụ: còn 6 GB cho PHP, worker trung bình 60 MB → khoảng 100. Để dư biên.
  - ⚠️ Đặt quá cao: hết RAM, swap, OOM killer. Đặt quá thấp: request xếp hàng ở
    `listen.backlog`, Nginx trả 502/504, log FPM có "server reached pm.max_children".
  - ⚠️ Số worker còn bị giới hạn bởi **downstream**: 100 worker × 4 server = 400 kết nối DB tiềm năng.
  - `pm.max_requests`: worker tự khởi động lại sau N request, chặn leak từ extension/code.

- [ ] 🟡 Slow log và timeout
  - `request_slowlog_timeout` + `slowlog`: request chạy quá ngưỡng thì FPM ghi **stack trace**
    của worker. Công cụ rẻ nhất để tìm request chậm trên production.
  - `request_terminate_timeout`: FPM kill worker sau N giây, tính thời gian thực.
  - `pm.status_path`: xem active/idle process, listen queue, max children reached.

- [ ] 🟡 Request lifecycle mức engine
  - MINIT (một lần mỗi process) → RINIT (đầu request) → chạy script → RSHUTDOWN → MSHUTDOWN (process tắt).
    Vì vậy extension giữ được state giữa request (`PDO::ATTR_PERSISTENT`) dù userland share-nothing.

- [ ] `memory_limit`, `max_execution_time`
  - `memory_limit` là trần mỗi request/process; vượt thì Fatal error. CLI dùng file ini riêng.
  - ⚠️ Trên Linux, `max_execution_time` chỉ tính thời gian **chạy script**, không tính thời gian
    trong system call, stream, query DB. Một request chờ API ngoài 5 phút vẫn không bị cắt.
    Muốn chặn theo thời gian thực: `request_terminate_timeout`, timeout của HTTP client,
    `fastcgi_read_timeout` ở Nginx.
  - CLI mặc định `max_execution_time = 0` (không giới hạn).

- [ ] 🔴 zval, refcount, copy-on-write
  - zval (PHP 7+): struct nhỏ gồm value + type info. int, float, bool, null nằm **trực tiếp**
    trong zval, không refcount.
  - String, array, object là cấu trúc riêng có refcount (`zend_string`, `zend_array`, `zend_object`).
  - Copy-on-write: `$b = $a` (array) chỉ tăng refcount; khi ghi vào `$b` mới tách bản sao
    (separation). Vì vậy truyền array lớn vào hàm **không tốn** chừng nào hàm không sửa nó.
  - Interned string: literal và tên class/hàm được lưu một bản duy nhất, không refcount.
  - Object: biến giữ **handle**; `$b = $a` trỏ cùng object. Không phải COW.

- [ ] 🟡 Garbage collection
  - Chính: reference counting. Refcount về 0 thì giải phóng ngay, destructor chạy ngay.
  - Vấn đề: vòng tham chiếu (`$a->b = $b; $b->a = $a;`) không bao giờ về 0.
  - Cycle collector: khi refcount giảm mà chưa về 0, zval được đưa vào root buffer. Buffer đầy
    (ngưỡng mặc định 10.000 root, kiểm tra lại theo phiên bản) thì chạy thuật toán tìm vòng.
  - `gc_collect_cycles()`, `gc_status()`. Trong FPM thường không cần quan tâm; trong worker
    sống lâu thì có.
  - 🔴 `WeakMap` (8.0), `WeakReference` (7.4): cache gắn với object mà không giữ object sống.

> **Đối chiếu:** PHP-FPM song song bằng **process**, mỗi request một process sạch. Java dùng
> thread trong một JVM sống lâu, heap chung, GC tracing. Go dùng goroutine trong một process,
> GC tracing concurrent. PHP dùng refcount nên giải phóng tức thời, dễ đoán; đổi lại tốn chi phí
> tăng/giảm counter và cần cycle collector phụ.

### Ngôn ngữ

- [ ] Type system và `strict_types`
  - Kiểu: `int`, `float`, `string`, `bool`, `array`, `object`, `callable`, `iterable`, `mixed`,
    `null`, class/interface; union `A|B` (8.0), intersection `A&B` (8.1), DNF `(A&B)|null` (8.2),
    `never` (8.1), `static` return (8.0), `null`/`false`/`true` đứng riêng (8.2).
  - `declare(strict_types=1)` áp dụng **theo file**, và cho lời gọi **phát ra từ** file đó
    (cùng với return type của hàm khai báo trong file đó). File gọi không strict thì hàm
    của bạn vẫn nhận `"5"` và ép thành `5`.
  - Strict vẫn cho phép int → float. ⚠️ Strict không ảnh hưởng toán tử `==`.

- [ ] ⚠️ Type juggling và PHP 8
  - PHP 8 đổi so sánh số với chuỗi không phải số: so như chuỗi thay vì ép chuỗi thành số.
    | Biểu thức | PHP 7 | PHP 8 |
    |---|---|---|
    | `0 == "a"` | `true` | `false` |
    | `"1" == "01"` | `true` | `true` (cả hai là chuỗi số) |
    | `"10" == "1e1"` | `true` | `true` |
    | `100 == "1e2"` | `true` | `true` |
    | `null == false` | `true` | `true` |
    | `"abc" == 0` | `true` | `false` |
  - ⚠️ `in_array($x, $arr)`, `array_search`, `array_keys($a, $v)` mặc định so sánh lỏng.
    Luôn truyền `true` ở tham số strict.
  - `switch` so sánh lỏng; `match` so sánh chặt và ném `UnhandledMatchError` khi không khớp.

- [ ] 🟡 Array bên trong
  - Ordered hash table: mảng bucket giữ **thứ tự chèn** + bảng hash để tra cứu. Vừa là list vừa
    là map. Packed array (key 0..n liên tục) được tối ưu, không cần bảng hash đầy đủ.
  - ⚠️ Ép kiểu key: `"1"` → `1`, `true` → `1`, `null` → `""`, float bị cắt phần thập phân
    (deprecated từ 8.1). `"01"` vẫn là string.
  - `array_merge` đánh lại số cho key số; `+` giữ key vế trái.
  - Chi phí bộ nhớ mỗi phần tử lớn hơn nhiều so với mảng C/Java. Dữ liệu triệu dòng: dùng
    generator, `SplFixedArray`, hoặc đừng nạp hết.

- [ ] ⚠️ Reference `&` và `foreach` by reference
  ```php
  $a = [1, 2, 3];
  foreach ($a as &$v) {}      // $v giờ là reference tới $a[2]
  foreach ($a as $v) {}       // mỗi vòng ghi đè $a[2]
  // $a === [1, 2, 2]
  ```
  - Sửa: `unset($v);` ngay sau vòng lặp by reference, hoặc dùng `foreach ($a as $k => $x) $a[$k] = ...`.
  - Reference phá copy-on-write, thường **chậm hơn** chứ không nhanh hơn. Đừng dùng `&` để "tối ưu".
  - Object không cần `&` để sửa nội dung (hàm sửa property thì bên ngoài thấy; gán `$obj = new X`
    trong hàm thì không). `clone` là shallow copy; override `__clone()` để deep copy.

- [ ] Interface, abstract, trait
  - Interface: hợp đồng, có hằng; class implement nhiều interface.
  - Abstract class: có state, constructor, method có sẵn; chỉ kế thừa một.
  - Trait: copy-paste method vào class lúc compile. Xung đột tên: `A::hello insteadof B`,
    `B::hello as helloB`. Trait có thể có abstract method, static property (mỗi class dùng trait
    có bản riêng).
  - ⚠️ Trait không phải type: không `instanceof Trait` được. Lạm dụng trait = kế thừa ngầm khó lần.

- [ ] 🟡 Late static binding
  - `self::` gắn với class **nơi viết code**; `static::` gắn với class **được gọi lúc runtime**.
  - `new static()` trong base class trả về instance class con. Eloquent dùng nhiều (`User::query()`).

- [ ] Magic methods
  - `__construct/__destruct`, `__get/__set/__isset/__unset`, `__call/__callStatic`, `__toString`,
    `__invoke`, `__clone`, `__serialize/__unserialize`, `__sleep/__wakeup`, `__debugInfo`.
  - Eloquent dựa vào `__get`/`__set` (attribute), `__call`/`__callStatic` (chuyển sang query builder).
  - ⚠️ Magic làm IDE và static analysis (PHPStan/Larastan) mù; chậm hơn truy cập trực tiếp.

- [ ] Closure và arrow function
  - `function () use ($x)` bắt **giá trị** lúc định nghĩa; `use (&$x)` bắt reference.
  - `fn($y) => $x + $y` tự bắt biến ngoài theo giá trị, chỉ một biểu thức.
  - Closure trong class tự bind `$this`. `static function` / `static fn` không bind, tránh giữ
    object sống lâu (có ích trong Octane/worker).
  - `Closure::bind`, `Closure::fromCallable`, first-class callable `strlen(...)` (8.1).

- [ ] 🟡 Generator và iterator
  - Hàm có `yield` trả về `Generator`; chạy lười, chỉ giữ phần tử hiện tại trong RAM.
  - `yield $k => $v`, `yield from other()`, `$gen->send($x)`, `$gen->getReturn()`.
  - ⚠️ Generator chỉ duyệt một lần; `rewind` sau khi đã chạy sẽ ném exception.
  - Interface: `Traversable` (không implement trực tiếp), `Iterator`, `IteratorAggregate`,
    `ArrayAccess`, `Countable`. `LazyCollection` của Laravel bọc generator.

- [ ] Exception hierarchy
  ```text
  Throwable
  ├── Exception  (RuntimeException, LogicException, InvalidArgumentException, PDOException, JsonException...)
  └── Error      (TypeError → ArgumentCountError, ValueError (8.0), ArithmeticError → DivisionByZeroError,
                  CompileError → ParseError, UnhandledMatchError, ...)
  ```
  - PHP 7 biến nhiều fatal error thành `Error` bắt được. `catch (Exception $e)` **không** bắt `Error`.
  - `finally` luôn chạy; `return` trong `finally` đè return trong `try` (tránh).
  - Userland không implement `Throwable` trực tiếp, phải extends `Exception` hoặc `Error`.
  - `json_decode(..., flags: JSON_THROW_ON_ERROR)` thay cho kiểm tra `json_last_error()`.

- [ ] PHP 8.x features (chỉ liệt kê cái chắc chắn)
  | Bản | Tính năng |
  |---|---|
  | 8.0 | `match`, named arguments, nullsafe `?->`, constructor property promotion, union type, `mixed`, attributes, JIT, `throw` là biểu thức, `WeakMap`, `str_contains`/`str_starts_with`, `Stringable` |
  | 8.1 | `enum` (pure và backed), `readonly` property, Fibers, first-class callable `f(...)`, `never`, intersection type, `new` trong initializer |
  | 8.2 | `readonly` class, DNF type, `null`/`false`/`true` type, deprecated dynamic property, `#[SensitiveParameter]`, extension Random |
  | 8.3 | typed class constants, `#[\Override]`, `json_validate()`, dynamic class constant fetch |
  | 8.4 | property hooks, asymmetric visibility (`public private(set)`), `new Foo()->bar()` không cần ngoặc |
  - Enum: `enum Status: string { case Paid = 'paid'; }`, `Status::from()`, `tryFrom()`,
    `cases()`; có method, implement interface; không có state.
  - `readonly`: chỉ gán một lần trong scope của class; ⚠️ object bên trong vẫn sửa được (shallow).
  - Fibers: coroutine cấp thấp, dừng/tiếp tục stack. Không phải thread, không tự làm I/O
    non-blocking; thư viện như Revolt/AMPHP xây event loop trên đó.
  - ⚠️ Dynamic property (8.2): gán property chưa khai báo bị deprecated (trừ `stdClass` và class
    có `#[AllowDynamicProperties]`). Gặp nhiều khi nâng cấp code cũ.

- [ ] 🟡 Attributes: `#[Route('/users')]` là metadata đọc bằng Reflection (`getAttributes()`), thay
  docblock annotation. Không tự làm gì; phải có code đọc chúng.

> **Đối chiếu:** array PHP giữ thứ tự chèn; `HashMap` của Java và `map` của Go **không** giữ
> (Java cần `LinkedHashMap`). Generator PHP ~ `Iterator`/`Stream` lười của Java ~ iterator
> `iter.Seq` (Go 1.23) hoặc channel của Go. Exception PHP giống Java nhưng PHP không có checked
> exception. Enum PHP gần enum Java (có method) hơn là `iota` của Go.

### Composer và PSR

- [ ] PSR-4 và autoload
  - Map namespace prefix → thư mục: `"App\\": "app/"` thì `App\Models\User` → `app/Models/User.php`.
  - `spl_autoload_register`: Composer đăng ký một autoloader, chỉ `require` file khi class được dùng.
  - 🟡 `composer dump-autoload -o`: sinh classmap, bỏ bước kiểm tra filesystem.
    `--classmap-authoritative` (`-a`): class không có trong classmap thì coi như không tồn tại
    (nhanh nhất, ⚠️ class sinh lúc runtime sẽ không được tìm).
  - Deploy: `composer install --no-dev --optimize-autoloader`.

- [ ] `composer.lock` và semver
  - `composer.json` khai báo **ràng buộc**; `composer.lock` ghi **phiên bản chính xác** đã resolve.
  - `install` đọc lock (tái lập được); `update` resolve lại và ghi lock mới.
  - ⚠️ App phải commit lock. Library: lock không ảnh hưởng project dùng library.
  - | Ràng buộc | Nghĩa |
    |---|---|
    | `^1.2.3` | `>=1.2.3 <2.0.0` |
    | `^0.3.1` | `>=0.3.1 <0.4.0` (major 0 thì minor được coi là breaking) |
    | `~1.2` | `>=1.2 <2.0` |
    | `~1.2.3` | `>=1.2.3 <1.3.0` |
  - `composer audit` kiểm tra advisory bảo mật.

- [ ] Các PSR chính
  | PSR | Nội dung |
  |---|---|
  | PSR-1, PSR-12 (và PER Coding Style) | Code style |
  | PSR-3 | Logger interface (Monolog) |
  | PSR-4 | Autoload |
  | PSR-6, PSR-16 | Cache (đầy đủ / đơn giản) |
  | PSR-7, PSR-17 | HTTP message immutable và factory |
  | PSR-11 | Container interface |
  | PSR-14 | Event dispatcher |
  | PSR-15 | HTTP handler và middleware |
  | PSR-18 | HTTP client |
  - ⚠️ Laravel `Request` dựa trên Symfony HttpFoundation, **không** phải PSR-7 (mutable).
    Có bridge nếu cần.

### Laravel: lõi

- [ ] Request lifecycle
  ```text
  public/index.php → vendor/autoload.php → bootstrap/app.php (tạo Application = container)
  → HTTP Kernel::handle → bootstrappers (env, config, exception handler, facades,
    register providers, boot providers)
  → global middleware → Router tìm route → route/group middleware → controller
  → Response → gửi về client → terminate() (terminable middleware, callback terminating)
  ```
  - Laravel 11+: skeleton gọn, middleware/exception/routing cấu hình trong `bootstrap/app.php`,
    không còn `app/Http/Kernel.php` mặc định.
  - Terminable middleware chạy sau khi gửi response (với FPM nhờ `fastcgi_finish_request`),
    nhưng **vẫn giữ worker FPM**. Không thay được queue cho việc nặng.

- [ ] Service container
  - `bind`: mỗi lần resolve tạo mới. `singleton`: một instance cho **vòng đời app** (FPM = một
    request; Octane/queue worker = cả process). `scoped`: một instance mỗi request/job, được
    flush giữa các request Octane và giữa các job. `instance`: đăng ký object có sẵn.
  - Auto-wiring: container dùng `ReflectionClass` đọc constructor, đệ quy resolve từng tham số
    theo type hint. Class cụ thể không cần đăng ký.
  - ⚠️ Type hint là interface mà chưa bind → `BindingResolutionException`. Tham số scalar không
    có default cũng không resolve được.
  - Contextual binding:
    ```php
    $this->app->when(PhotoController::class)
        ->needs(Filesystem::class)
        ->give(fn () => Storage::disk('s3'));
    ```
  - Tagging (`tag`, `tagged`), `extend` (decorate service có sẵn), `resolving` callback.
  - ⚠️ `app()`/`resolve()` rải trong domain code = service locator; khó thấy dependency.

- [ ] Service provider
  - `register()`: chỉ bind vào container. Không dùng service khác ở đây vì chúng có thể chưa đăng ký.
  - `boot()`: chạy sau khi **mọi** provider đã register; đăng ký event, route, macro, observer.
  - 🟡 Deferred provider: implement `DeferrableProvider` + `provides()`; chỉ nạp khi một service
    trong `provides()` được resolve. Danh sách lưu ở `bootstrap/cache/services.php`.

- [ ] Facade dưới nắp
  ```text
  Cache::get('k')
  → Facade::__callStatic('get', ['k'])
  → static::getFacadeRoot() → app()->make(static::getFacadeAccessor())  // 'cache'
  → $instance->get('k')
  ```
  - Instance đã resolve được cache trong static property của Facade. Test được bằng
    `Cache::shouldReceive()` (Mockery) hoặc fake riêng (`Queue::fake()`) vì bên dưới là object trong container.
  - Tranh luận: facade giấu dependency. Chấp nhận trong controller, tránh trong domain logic quan trọng.
  - Real-time facade: `use Facades\App\Services\Payment;` biến class bất kỳ thành facade.

- [ ] Middleware
  - Global, group (`web`, `api`), route. Pipeline kiểu "hành tây": code trước `$next($request)`
    chạy trên đường vào, code sau chạy trên đường ra.
  - Thứ tự: global → group → route; middleware priority cho các cái cần thứ tự cố định (session
    trước auth). Tham số: `throttle:60,1`, `can:update,post`.

- [ ] Routing và route model binding
  - Implicit: `Route::get('/posts/{post}', ...)` + type hint `Post $post` → `findOrFail`.
    Đổi cột: `{post:slug}`.
  - Explicit: `Route::model()`, `Route::bind()`. Scoped binding: `/users/{user}/posts/{post}`
    với `scopeBindings()` đảm bảo post thuộc user.
  - ⚠️ Binding **không** thay authorization: tìm được post không có nghĩa user được xem (IDOR).

- [ ] Validation và Form Request
  - Form Request: `authorize()`, `rules()`, `prepareForValidation()`, `messages()`, `after()`.
  - ⚠️ Dùng `$request->validated()` hoặc `safe()->only()` khi tạo model, không dùng `$request->all()`.
  - Rule hay hỏi: `bail`, `sometimes`, `nullable`, `exists:table,col`, `Rule::unique()->ignore($id)`.
  - ⚠️ `unique` trong validation có race condition: hai request cùng lúc đều qua. Phải có
    **unique index** ở DB và bắt lỗi vi phạm.

### Laravel: Eloquent và database

- [ ] Relationship
  - `hasOne`, `hasMany`, `belongsTo`, `belongsToMany` (pivot, `withPivot`, `withTimestamps`),
    `hasOneThrough`, `hasManyThrough`, polymorphic `morphTo`/`morphMany`/`morphToMany`.
  - ⚠️ Polymorphic lưu tên class vào DB; đổi namespace là gãy. Dùng `Relation::enforceMorphMap()`.

- [ ] Eager vs lazy loading, N+1
  - `Post::all()` rồi `$post->author` trong vòng lặp: 1 + N query.
  - `with('author')`: 2 query (`WHERE id IN (...)`). `load()`/`loadMissing()` sau khi đã có
    collection. Constrained eager: `with(['comments' => fn ($q) => $q->latest()->limit(5)])`.
  - `withCount`, `withSum`, `withExists` thay vì nạp cả collection để đếm.
  - `Model::preventLazyLoading(! app()->isProduction())` ném exception khi lazy load.
    `Model::shouldBeStrict()` bật thêm chặn gán attribute không fillable âm thầm và truy cập
    attribute không tồn tại.
  - Phát hiện: Debugbar, Telescope, log query đếm số query mỗi request.

- [ ] ⚠️ Duyệt dữ liệu lớn
  | Method | Cơ chế | Bộ nhớ | Cạm bẫy |
  |---|---|---|---|
  | `chunk(1000)` | `LIMIT/OFFSET` từng trang | Một trang | Update/delete cột đang lọc → bỏ sót dòng; OFFSET lớn chậm |
  | `chunkById(1000)` | `WHERE id > last ORDER BY id LIMIT` | Một trang | Cần cột tăng dần có index |
  | `lazy()` / `lazyById()` | Như chunk nhưng trả `LazyCollection` | Một trang | Như trên |
  | `cursor()` | Một query, hydrate từng dòng | Model: một cái; kết quả thô vẫn buffer trong PDO | Không eager load được; MySQL buffered query vẫn giữ toàn bộ kết quả thô |
  - Vì sao `chunk` bỏ sót: trang 1 xử lý 1000 dòng `status=pending` và update thành `done`;
    trang 2 `OFFSET 1000` trên tập đã co lại, nhảy qua 1000 dòng chưa xử lý.

- [ ] Mass assignment
  - `$fillable` (whitelist) hoặc `$guarded` (blacklist). `$guarded = []` là tắt bảo vệ.
  - Tấn công: gửi thêm `is_admin=1` khi `User::create($request->all())`.
  - `forceFill()` bỏ qua bảo vệ, dùng có chủ đích.

- [ ] Cast, accessor/mutator, scope
  - Cast: `array`, `json`, `datetime`, `decimal:2`, `encrypted`, `hashed`, enum, custom
    `CastsAttributes`. Laravel 11+ khai báo qua method `casts()`.
  - Accessor/mutator: `Attribute::make(get: ..., set: ...)` (Laravel 9+); kiểu cũ `getXAttribute`.
    `$appends` đưa accessor vào JSON (⚠️ accessor chạy query trong `$appends` = N+1 ẩn).
  - Local scope `scopeActive($q)` → `->active()`. Global scope tự áp vào mọi query;
    `withoutGlobalScope()`. ⚠️ Global scope bất ngờ làm query "thiếu dữ liệu".
  - ⚠️ Cast `float` cho tiền: sai số. Dùng `decimal`, lưu số nguyên đơn vị nhỏ nhất, hoặc thư
    viện money. Xem [22-practical-data.md](22-practical-data.md).

- [ ] Observer và model event
  - `retrieved`, `creating/created`, `updating/updated`, `saving/saved`, `deleting/deleted`,
    `restoring/restored`, `forceDeleting/forceDeleted`.
  - ⚠️ `User::where(...)->update([...])`, `insert()`, `upsert()`, `delete()` trên query builder
    **không** hydrate model nên **không** bắn event, không chạy observer, không cập nhật cast.
  - `saveQuietly()`, `Model::withoutEvents()`.
  - ⚠️ Logic nghiệp vụ quan trọng giấu trong observer: khó lần theo, dễ gây side effect khi seed/import.

- [ ] Soft delete
  - `SoftDeletes` + cột `deleted_at`; global scope tự thêm `whereNull('deleted_at')`.
    `withTrashed()`, `onlyTrashed()`, `restore()`, `forceDelete()`.
  - ⚠️ Unique index (email) va chạm với bản ghi đã soft delete. Cách xử lý: unique trên
    `(email, deleted_at)` (lưu ý NULL trong unique index tuỳ DB), hoặc cột generated.
  - ⚠️ Raw query, join, báo cáo quên điều kiện `deleted_at`. Quan hệ không tự lọc bảng pivot.

- [ ] Query builder vs Eloquent
  - Query builder: nhanh hơn, trả `stdClass`, không event/cast/relationship. Hợp cho báo cáo,
    bulk update, import.
  - `upsert()`, `insertOrIgnore()`, `lockForUpdate()`, `sharedLock()`, `increment()` (atomic ở DB).
  - ⚠️ `whereRaw("name = '$name'")` là SQL injection; luôn truyền binding: `whereRaw('name = ?', [$name])`.
    ⚠️ Tên cột lấy từ input (sort by) phải whitelist, binding không bảo vệ identifier.

- [ ] Transaction
  - `DB::transaction(fn () => ..., attempts: 3)`: tự rollback khi có exception, retry khi deadlock.
    Lồng nhau dùng savepoint.
  - ⚠️ Dispatch job/gửi mail/gọi API trong transaction: job có thể chạy **trước khi commit**, đọc
    không thấy dữ liệu; hoặc transaction rollback nhưng mail đã gửi.
    Cách xử lý: `->afterCommit()` trên job, `after_commit => true` trong config queue,
    `DB::afterCommit()`, listener implement `ShouldHandleEventsAfterCommit`.
  - Đảm bảo mạnh hơn (DB commit và message không mất): outbox pattern, xem
    [12-messaging.md](12-messaging.md).
  - ⚠️ Transaction dài giữ lock; không gọi HTTP ngoài trong transaction.

### Laravel: queue

- [ ] Driver và worker
  - Driver: `sync` (chạy ngay, dev), `database`, `redis`, `sqs`, `beanstalkd`.
  - `queue:work`: process sống lâu, boot framework một lần. `queue:listen`: boot lại mỗi job
    (chậm, chỉ dev).
  - Ưu tiên: `--queue=high,default,low` (lấy hết high rồi mới tới default).
  - Tuỳ chọn worker: `--tries`, `--backoff`, `--timeout`, `--memory`, `--max-jobs`, `--max-time`, `--sleep`.

- [ ] Retry, timeout
  - Trên job: `$tries`, `$backoff` (mảng = backoff tăng dần), `$timeout`, `$maxExceptions`,
    `retryUntil()` (hạn theo thời gian, thay cho `tries`), `$failOnTimeout`.
  - ⚠️ `retry_after` (trong config connection) phải **lớn hơn** `timeout` của job dài nhất.
    Nếu không, job đang chạy bị coi là chết và worker khác nhận lại → chạy **hai lần song song**.
  - `timeout` cần extension `pcntl`; worker bị kill khi job vượt timeout.
  - ⚠️ Job phải **idempotent**: có thể chạy lại do retry, timeout, worker chết giữa chừng,
    SQS at-least-once. Dùng idempotency key, unique constraint, kiểm tra trạng thái trước khi làm.

- [ ] Failed job
  - Hết lượt thử → bảng `failed_jobs`, gọi `failed(Throwable $e)` trên job.
  - `queue:failed`, `queue:retry {id|all}`, `queue:forget`, `queue:flush`, `queue:prune-failed`.
  - Phân biệt lỗi tạm thời (timeout, 503 → retry) và lỗi vĩnh viễn (validation → `$this->fail()`
    ngay, không phí lượt).

- [ ] Batching, chaining
  - Chain: `Bus::chain([A, B, C])` chạy tuần tự; một job fail thì các job sau không chạy.
  - Batch: `Bus::batch([...])->then()->catch()->finally()->dispatch()`; bảng `job_batches`;
    job dùng trait `Batchable`, kiểm tra `$this->batch()->cancelled()`. `allowFailures()`.

- [ ] Unique job và job middleware
  - `ShouldBeUnique` + `uniqueId()` + `$uniqueFor`: không dispatch trùng khi job cũ chưa xong.
    `ShouldBeUniqueUntilProcessing`: mở khoá khi bắt đầu xử lý. Dựa vào cache lock, cần driver
    hỗ trợ lock.
  - `RateLimited('name')` dùng `RateLimiter::for()`; `WithoutOverlapping($key)` chặn hai job cùng
    key chạy đồng thời (`releaseAfter`, `expireAfter`); `ThrottlesExceptions` khi API ngoài lỗi liên tục.
  - ⚠️ Job bị middleware `release()` lại vẫn tính một **attempt**. Kết hợp `tries` nhỏ với rate
    limit thì job fail oan; dùng `retryUntil()`.

- [ ] ⚠️ `SerializesModels`
  - Job chỉ lưu class + id của model; khi chạy thì query lại. Model bị xoá trước đó →
    `ModelNotFoundException`. Dùng `$deleteWhenMissingModels = true` nếu chấp nhận bỏ qua.
  - Dữ liệu đã **thay đổi** giữa lúc dispatch và lúc chạy: job thấy bản mới nhất, không phải bản
    lúc dispatch. Cần snapshot thì truyền giá trị cụ thể.
  - Relationship đã load cũng được serialize và load lại; payload phình to.

- [ ] Horizon, restart, supervisor
  - Horizon: chỉ cho Redis; cấu hình supervisor theo code, balance (`simple`, `auto`, `false`),
    dashboard throughput/wait time/failed, tag. Deploy: `horizon:terminate`.
  - `queue:restart`: ghi timestamp vào **cache**; worker kiểm tra sau mỗi job và thoát êm.
    ⚠️ Cần cache dùng chung giữa các server; worker cần process manager (supervisor, systemd,
    k8s) để khởi động lại.
  - ⚠️ Worker là process sống lâu: sau deploy không restart thì vẫn chạy **code cũ**.
  - Supervisor: `numprocs`, `autorestart=true`, `stopwaitsecs` lớn hơn timeout job dài nhất
    (không thì job bị kill giữa chừng khi deploy).

### Laravel: các thành phần khác

- [ ] Scheduler
  - Một cron `* * * * * php artisan schedule:run`; Laravel 11+ khai báo trong `routes/console.php`.
  - ⚠️ Nhiều server cùng chạy cron → task chạy N lần. `->onOneServer()` dùng cache lock chung
    (Redis, Memcached, database, DynamoDB).
  - `->withoutOverlapping()`: không chạy lần mới khi lần cũ chưa xong; lock có hạn mặc định
    24 giờ (process chết giữa chừng thì task bị kẹt tới khi hết hạn, kiểm tra lại theo phiên bản).
  - `->runInBackground()` để task dài không chặn task khác cùng phút. Timezone của schedule.

- [ ] Cache
  - `Cache::remember($key, $ttl, fn)`, `rememberForever`, `forget`, `increment`.
  - Tag: `Cache::tags(['users'])->flush()`; ⚠️ không hỗ trợ ở driver `file`, `database`, `dynamodb`.
  - Atomic lock: `Cache::lock('order:1', 10)->block(5, fn () => ...)`; lock có owner, chỉ owner
    release được. Dùng chống chạy trùng, không thay lock DB cho tính đúng của dữ liệu.
  - Session (driver `file`, `database`, `redis`; ⚠️ `file` hỏng khi có nhiều server sau load balancer,
    trừ khi dùng sticky session). Rate limiting: `RateLimiter::for()` + middleware `throttle`.
  - ⚠️ `remember` không chống cache stampede: key hết hạn, nhiều request cùng tính lại. Xem
    [11-cache.md](11-cache.md).

- [ ] Event, listener, notification
  - Listener `implements ShouldQueue` thì chạy qua queue. Event discovery hoặc đăng ký tay.
  - Notification: `via()` chọn channel (mail, database, broadcast, Slack, SMS), `ShouldQueue`,
    on-demand `Notification::route('mail', ...)`.
  - ⚠️ Event đồng bộ + listener chậm = request chậm; listener lỗi làm hỏng request.

- [ ] 🟡 Broadcasting: `ShouldBroadcast` (qua queue) / `ShouldBroadcastNow`; driver Reverb (11+), Pusher,
  Ably; client Laravel Echo; private/presence channel xác thực qua `routes/channels.php`.

- [ ] Auth
  - Guard (cách xác thực: `session`, token) và provider (lấy user từ đâu: `eloquent`, `database`).
  - Sanctum: (1) SPA cùng domain gốc dùng cookie session + CSRF; (2) personal access token
    lưu **hash** trong DB, có abilities. Không phải OAuth2.
  - Passport: OAuth2 server đầy đủ (client, grant, refresh token). Chỉ dùng khi thật sự cần cho
    bên thứ ba đăng nhập bằng OAuth.
  - Gate (closure) cho quyền chung, Policy cho quyền theo model. `$this->authorize()`,
    middleware `can:`, `Gate::before()` cho super admin.
  - Chi tiết JWT/session/OAuth: [10-security.md](10-security.md).

- [ ] ⚠️ Config và route cache
  - `config:cache` gộp config vào một file PHP. Sau đó `.env` **không được đọc nữa**:
    `env()` gọi ngoài file config trả `null`. Quy tắc: chỉ gọi `env()` trong `config/*.php`.
  - `route:cache`, `view:cache`, `event:cache`, `optimize` (gom các lệnh trên).
  - Deploy: cache lại sau khi đổi config; `config:clear` khi debug.

- [ ] 🔴 Octane
  - Chạy trên Swoole, RoadRunner, hoặc FrankenPHP. App boot **một lần** mỗi worker, giữ trong
    memory, phục vụ nhiều request → bỏ chi phí boot.
  - State leak:
    - Singleton giữ `Request`, user, config lúc boot → request sau thấy dữ liệu request trước.
    - Static property, mảng cache static tăng mãi.
    - Inject container/request vào constructor singleton thì giữ bản cũ; nên inject closure
      resolver hoặc dùng `scoped`.
  - Octane tự reset một số service của framework; package bên thứ ba chưa chắc tương thích.
  - `--max-requests` để recycle worker. Hiệu quả nhất khi boot chiếm phần lớn thời gian request.

- [ ] Công cụ test (chỉ cần biết tên và vai trò)
  - PHPUnit, Pest; HTTP test (`$this->getJson()`), `RefreshDatabase` / `DatabaseTransactions`,
    model factory, fakes: `Queue::fake`, `Bus::fake`, `Event::fake`, `Mail::fake`,
    `Notification::fake`, `Http::fake`, `Storage::fake`; Mockery; Dusk (browser); Larastan.
  - ⚠️ Vận hành: test phải trỏ **DB riêng** (khai báo trong `phpunit.xml` / `.env.testing`).
    `RefreshDatabase` chạy migrate và xoá dữ liệu; trỏ nhầm DB dev dùng chung là mất dữ liệu thật.
  - Chiến lược test: [20-testing-quality.md](20-testing-quality.md).

- [ ] 🟡 Laravel vs Symfony
  | | Laravel | Symfony |
  |---|---|---|
  | Triết lý | Convention, dev nhanh, "magic" có chủ đích | Tường minh, cấu hình rõ, component tách rời |
  | ORM mặc định | Eloquent (Active Record) | Doctrine (Data Mapper, Unit of Work) |
  | Container | Resolve lúc runtime bằng reflection | Compile container thành PHP code, lỗi wiring lộ lúc build |
  | Truy cập service | Facade, helper, DI | DI, autowiring |
  | Quan hệ | Dùng nhiều Symfony component (HttpFoundation, Console, Mailer...) | |
  - Senior: chọn theo đội và domain. Domain phức tạp, nhiều invariant: Data Mapper dễ giữ domain
    sạch. CRUD/admin/startup: Laravel nhanh hơn.

### Hiệu năng và vận hành PHP

- [ ] 🟡 Profiling
  - Xdebug: debugger + profiler (cachegrind), overhead lớn, ⚠️ không bật trên production.
  - Blackfire, Tideways: profiler dùng được trên production (sampling/theo yêu cầu), call graph,
    so sánh trước/sau.
  - XHProf, SPX: nhẹ, mã nguồn mở. Laravel: Telescope, Debugbar (dev), Pulse (production).
  - APM (New Relic, Datadog...) cho bức tranh tổng; profiler để đào một endpoint.
  - Quy trình: đo → tìm nút thắt (thường là query, N+1, gọi API tuần tự) → sửa → đo lại.
    Xem [17-performance.md](17-performance.md).

- [ ] Xử lý file lớn
  - ⚠️ `file_get_contents()`/`file()` nạp cả file vào RAM.
  - Đọc theo dòng: `fopen` + `fgets`/`fgetcsv`, `SplFileObject`, bọc trong generator.
  ```php
  function rows(string $path): \Generator {
      $h = fopen($path, 'rb');
      try {
          while (($row = fgetcsv($h)) !== false) { yield $row; }
      } finally { fclose($h); }
  }
  ```
  - Import: đọc theo lô, insert theo batch (500–1000 dòng), mỗi lô một transaction ngắn, chạy
    trong queue job, lưu tiến độ để chạy tiếp khi fail.

- [ ] Export CSV streaming
  ```php
  return response()->streamDownload(function () {
      $out = fopen('php://output', 'wb');
      fputcsv($out, ['id', 'email']);
      User::query()->select('id', 'email')->lazyById(2000)
          ->each(fn ($u) => fputcsv($out, [$u->id, $u->email]));
      fclose($out);
  }, 'users.csv');
  ```
  - Bộ nhớ gần như hằng số. Cần kiểm tra output buffering, Nginx buffering
    (`X-Accel-Buffering: no`), timeout các tầng.
  - Export rất lớn hoặc lâu: chạy trong queue, ghi ra S3, gửi link. Không giữ worker FPM hàng phút.
  - ⚠️ Excel mở CSV UTF-8 tiếng Việt bị sai dấu (đoán nhầm encoding): thêm BOM `\xEF\xBB\xBF`. ⚠️ CSV injection:
    ô bắt đầu bằng `=`, `+`, `-`, `@`.

- [ ] 🔴 Long-running process và memory leak
  - Queue worker, daemon, Octane, consumer Kafka/RabbitMQ: mất lợi thế share-nothing.
  - Nguồn leak hay gặp: static array làm cache, listener/callback đăng ký lặp lại mỗi job,
    query log bật (`DB::enableQueryLog`), Telescope/Debugbar trong worker, vòng tham chiếu,
    collection lớn gán vào property của singleton.
  - Phòng: `--max-jobs`, `--max-time`, `--memory` để worker tự thoát và được restart; đo
    `memory_get_usage()` theo thời gian; `gc_collect_cycles()` khi cần.
  - ⚠️ Kết nối DB/Redis trong worker có thể bị server đóng (idle timeout, failover); cần reconnect.
  - Signal: xử lý `SIGTERM` để dừng êm (worker Laravel đã có, script tự viết thì phải tự làm).

### Bảo mật đặc thù PHP

- [ ] ⚠️ `unserialize()`
  - `unserialize()` dữ liệu người dùng → object injection: tạo object class bất kỳ, `__wakeup`/
    `__destruct` chạy, chuỗi gadget dẫn tới RCE (công cụ phpggc có sẵn gadget cho nhiều framework).
  - Dùng JSON. Bắt buộc dùng thì `unserialize($s, ['allowed_classes' => false])`.
  - ⚠️ `APP_KEY` lộ: kẻ tấn công giải mã/giả mạo cookie, dữ liệu encrypt. Laravel cũ từng có lỗ
    hổng RCE qua cookie serialize khi lộ key. Coi `APP_KEY` như secret cấp cao, xoay vòng khi lộ.
  - `phar://` stream wrapper từng cho phép deserialize qua các hàm file (đã thay đổi ở PHP 8.0).

- [ ] `include`/`require` với input
  - `include $_GET['page']` → Local File Inclusion (đọc `/etc/passwd`, include log đã bị chèn code),
    Remote File Inclusion nếu `allow_url_include=On`.
  - Whitelist tên file; không ghép path từ input; `open_basedir` như lớp phòng thủ phụ.

- [ ] File upload
  - Kiểm tra MIME theo **nội dung** (`finfo`, rule `mimes`/`mimetypes`), không tin extension và
    `Content-Type` client gửi.
  - Đặt tên file ngẫu nhiên, lưu ngoài webroot hoặc S3; ⚠️ Nginx chỉ cho chạy PHP ở `index.php`,
    không bao giờ chạy PHP trong thư mục upload.
  - Giới hạn `upload_max_filesize`, `post_max_size`, `client_max_body_size` (Nginx).
  - Ảnh: re-encode để bỏ payload; SVG chứa JavaScript (XSS).

- [ ] ⚠️ So sánh hash
  - `md5('240610708') == md5('QNKCDZO')` là `true`: cả hai hash dạng `0e...` là chuỗi số, so lỏng
    thành `0 == 0` (vẫn đúng ở PHP 8 vì cả hai là chuỗi số).
  - Dùng `hash_equals($known, $user)`: so chặt và **constant-time** (chống timing attack) cho token,
    chữ ký HMAC webhook.
  - Mật khẩu: `password_hash()` (bcrypt/argon2) và `password_verify()`, `password_needs_rehash()`.
    Không md5/sha1.
  - Random bảo mật: `random_bytes()`, `random_int()`, `Str::random()`; không `rand()`/`mt_rand()`/`uniqid()`.

- [ ] Khác: `APP_DEBUG=true`/`display_errors=On` trên production lộ stack trace và secret; Blade `{!! !!}`
  không escape; `extract()`, `$$var`, `eval`, `shell_exec` (dùng `escapeshellarg` hoặc Symfony Process
  với mảng tham số). OWASP tổng quát: [10-security.md](10-security.md).

### Đối chiếu với ngôn ngữ khác

| Khía cạnh | PHP/Laravel | Java/Spring | Go |
|---|---|---|---|
| Mô hình chạy | FPM: process/request, share-nothing | JVM sống lâu, thread pool (virtual thread từ 21) | Một process, goroutine mỗi request |
| State giữa request | Không có (trừ Octane/worker) | Có, singleton bean dùng chung | Có, biến package, struct server |
| Memory | Refcount + cycle collector | Tracing GC, chia thế hệ | Tracing GC concurrent, không chia thế hệ |
| Lỗi | Exception, không checked | Checked + unchecked | `error` là giá trị |
| DI | Container runtime, reflection | IoC container, bean, proxy | Truyền tay qua constructor, (Wire/Fx nếu cần) |
| ORM | Eloquent Active Record | JPA/Hibernate Data Mapper, Unit of Work | database/sql, sqlc, GORM |
| Job nền | Queue + worker process | `@Async`, executor, Spring Batch, consumer | goroutine + channel, worker riêng |
| Warm-up | OPcache; không JIT mặc định | JIT cần warm-up | Biên dịch sẵn, khởi động nhanh |

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Vì sao PHP ít bị memory leak? | "PHP tự giải phóng sau mỗi request." | Share-nothing của FPM che leak; leak vẫn xuất hiện ở worker, Octane, daemon. Nêu nguồn leak cụ thể, cách đo (`memory_get_usage` theo thời gian), cách chặn (`--max-jobs`, `pm.max_requests`). |
| Đặt `pm.max_children` bao nhiêu? | "Để 50 như mặc định trên mạng." | Đo RSS thật lúc tải cao, chia RAM còn lại, để biên; kiểm tra giới hạn downstream (connection DB); theo dõi status page và log "max_children reached"; `static` nếu server dành riêng. |
| N+1 xử lý thế nào? | "Dùng `with()`." | `with()` cộng bật `preventLazyLoading` ở non-production để chặn từ gốc, đếm query mỗi request trong APM, cẩn thận accessor trong `$appends` và serializer gây N+1 ẩn. |
| Job gửi email chạy trước khi commit | "Thêm `sleep`." | Hiểu vì sao (worker đọc DB trước khi commit), dùng `afterCommit`, bật `after_commit` global; nếu cần không mất message thì outbox. |
| Queue job bị chạy hai lần | "Lỗi của Laravel." | Kiểm tra `retry_after` < timeout, worker chết, SQS at-least-once; thiết kế job idempotent bằng unique key hoặc trạng thái; `WithoutOverlapping` nếu cần loại trừ. |
| Có nên dùng Octane? | "Có, nhanh hơn nhiều." | Đo xem boot chiếm bao nhiêu phần request; nếu nút thắt là DB thì lợi ích nhỏ; đánh giá rủi ro state leak, package không tương thích, cần review singleton/static trước khi bật. |

## Tình huống

1. **Sau deploy, một số request vẫn chạy code cũ.**
   - Gợi ý: OPcache với `validate_timestamps=0` chưa reload FPM; symlink deploy và realpath cache;
     queue worker chưa `queue:restart`; `config:cache` cũ; Horizon chưa terminate.
2. **Nginx trả 502/504 hàng loạt lúc cao điểm, CPU không cao.**
   - Gợi ý: FPM hết worker ("max_children reached"), worker bị chặn chờ DB/API ngoài; xem slow log;
     kiểm tra timeout HTTP client; tăng worker chỉ khi còn RAM và DB chịu được; chuyển việc chậm vào queue.
3. **Queue worker RAM tăng dần tới khi bị OOM kill sau vài giờ.**
   - Gợi ý: đo memory theo từng job; tìm static cache, listener đăng ký lặp, query log, Telescope;
     đặt `--max-jobs`/`--memory` làm lưới an toàn nhưng vẫn tìm gốc.
4. **Export báo cáo 2 triệu dòng làm timeout và hết RAM.**
   - Gợi ý: `lazyById`/cursor + streaming hoặc chạy nền ghi S3; chỉ select cột cần; index cột lọc;
     đọc từ replica; cẩn thận `chunk` khi dữ liệu thay đổi trong lúc export.
5. **Scheduler gửi báo cáo cho khách 3 lần mỗi sáng sau khi scale lên 3 server.**
   - Gợi ý: `onOneServer()` với cache lock chung, hoặc chạy scheduler trên một instance riêng;
     job gửi phải idempotent (lưu đã gửi ngày nào).
6. **Bật Octane xong thỉnh thoảng user A thấy dữ liệu của user B.**
   - Gợi ý: singleton/static giữ request hoặc user; tìm binding `singleton` nhận `Request` trong
     constructor; chuyển sang `scoped`; kiểm tra package bên thứ ba; rollback trước, điều tra sau.
7. **Webhook thanh toán bị xử lý hai lần, một lần xác thực chữ ký bị bypass.**
   - Gợi ý: so chữ ký bằng `hash_equals`, không `==`; idempotency theo transaction id của cổng
     thanh toán với unique index; trả 200 nhanh rồi xử lý trong queue.

## ❓ Câu hỏi hay gặp

🟢
- `==` và `===` khác nhau thế nào? Cho ví dụ đổi kết quả giữa PHP 7 và PHP 8.
- Interface, abstract class và trait khác nhau thế nào?
- `$fillable` và `$guarded` để làm gì?
- `register()` và `boot()` của service provider khác nhau thế nào?
- N+1 query là gì, xử lý trong Eloquent ra sao?
- Vì sao phải commit `composer.lock`?

🟡
- Vì sao PHP không có vấn đề memory leak kéo dài như Java? Khi nào thì PHP lại có?
- Service container resolve một class có dependency trong constructor thế nào?
- Facade hoạt động thế nào bên dưới? Test code dùng facade ra sao?
- `chunk`, `chunkById`, `lazy`, `cursor` khác nhau thế nào? Khi nào `chunk` bỏ sót dòng?
- Vì sao job dispatch trong transaction có thể lỗi? Sửa thế nào?
- `pm.max_children` tính thế nào? `static` và `dynamic` chọn khi nào?
- Sanctum và Passport khác nhau thế nào?
- Vì sao gọi `env()` trong code lại trả `null` trên production?

🔴
- Copy-on-write của array hoạt động thế nào? Reference `&` ảnh hưởng gì tới nó?
- `retry_after` và `timeout` liên quan thế nào? Sai thì hậu quả gì?
- Octane gây state leak thế nào? Review code nào trước khi bật?
- OPcache và JIT khác nhau thế nào? JIT có giúp web app không?
- Thiết kế import file CSV 5 triệu dòng có thể chạy tiếp khi lỗi giữa chừng.
- `unserialize()` dữ liệu người dùng nguy hiểm thế nào?

## Bài tập tự làm

1. Viết một đoạn PHP 10–15 dòng minh hoạ cạm bẫy `foreach` by reference, và một đoạn minh hoạ
   `in_array` so sánh lỏng. Dự đoán output trước, rồi mới chạy (`php file.php`).
2. Với một server 8 GB RAM chạy Nginx + PHP-FPM + Redis, viết ra các bước bạn sẽ làm để chọn
   `pm`, `pm.max_children`, `pm.max_requests`, kèm lý do. Không cần con số đúng, cần quy trình đúng.
3. Vẽ sơ đồ (ASCII) một request Laravel từ `public/index.php` tới khi terminable middleware chạy,
   ghi rõ service provider `register`/`boot` nằm ở bước nào.
4. Thiết kế một job gọi API đối tác bị giới hạn 60 request/phút, phải idempotent và không chạy
   trùng theo `order_id`. Liệt kê cấu hình `tries`/`backoff`/`retryUntil`/middleware bạn chọn và vì sao.
5. Liệt kê 5 chỗ trong một codebase Laravel bạn từng làm có thể gây state leak nếu bật Octane.

> Nộp bài vào đây để được review.
