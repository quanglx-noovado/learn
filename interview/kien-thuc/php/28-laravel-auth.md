# Chương 28. Xác thực và phân quyền trong Laravel

> [← Mục lục](README.md) · [← Chương 27: Database trong Laravel: migration, query builder, Eloquent](27-laravel-database-eloquent.md) · [Chương 29: Queue, event, scheduler, cache, mail và notification →](29-laravel-queue-event-schedule-cache.md)

**Bạn sẽ học được:**

- Phân biệt *xác thực* (authentication, "bạn là ai") với *phân quyền* (authorization, "bạn được làm
  gì"), và vì sao trộn hai việc này là nguồn gốc của nhiều lỗ hổng.
- Hai khái niệm lõi của hệ thống auth Laravel là *guard* và *provider*, file `config/auth.php`, và
  điều thực sự xảy ra bên trong khi gọi `Auth::attempt()`, `Auth::user()`, `Auth::logout()`, kể cả
  cookie "remember me".
- Cách Laravel băm mật khẩu, quy trình quên mật khẩu, xác minh email, và các *starter kit* dựng sẵn
  toàn bộ phần này.
- Xác thực cho API: Sanctum ở hai chế độ (cookie cho SPA, token cho mobile và script), và Passport
  (OAuth2) dùng khi nào.
- Phân quyền bằng *Gate* và *Policy*, các chỗ gọi kiểm tra quyền (controller, middleware `can`,
  Blade, Form Request, attribute), và cách ẩn dữ liệu theo quyền.
- Hai lỗ hổng phổ biến nhất ở tầng này: *mass assignment* và *IDOR*, cùng cách chặn.

**Cần biết trước:** [Chương 15](15-php-va-web.md) (HTTP, cookie, session, session fixation),
[Chương 17](17-bao-mat.md) (băm mật khẩu bằng `password_hash`, CSRF, `hash_equals`, HMAC),
[Chương 24](24-laravel-routing-controller-middleware.md) (route, middleware, route model binding),
[Chương 25](25-laravel-request-validation-response.md) (Form Request, validation),
[Chương 27](27-laravel-database-eloquent.md) (Eloquent model, relationship).

Một lưu ý về ví dụ: máy soạn giáo trình không chạy được Laravel. Các đoạn code Laravel trong chương
được viết theo tài liệu chính thức Laravel 13.x và mã nguồn `laravel/framework` nhánh 13.x (có ghi
nguồn ở cuối chương). Những đoạn PHP thuần (mô phỏng guard, băm mật khẩu, mô phỏng token) đều đã được
chạy thật và output ghi trong comment là output thật. Các file cấu hình mặc định (`config/auth.php`,
model `User`) được chép từ repo skeleton `laravel/laravel` nhánh 13.x, chỉ lược bớt comment.

## 1. Xác thực và phân quyền là hai việc khác nhau

### 1.1 Hai câu hỏi mà mọi request phải trả lời

Hãy hình dung một toà nhà văn phòng. Ở cửa có bảo vệ kiểm tra thẻ nhân viên: "anh là ai?". Vào
được bên trong rồi, không phải phòng nào anh cũng mở được: phòng kế toán chỉ cho người phòng kế
toán, phòng server chỉ cho đội IT. Hai việc này khác nhau:

| | Xác thực (*authentication*, viết tắt *authn*) | Phân quyền (*authorization*, viết tắt *authz*) |
|---|---|---|
| Câu hỏi | Bạn là ai? | Bạn có được làm việc này với thứ này không? |
| Đầu vào | Mật khẩu, cookie session, token, chữ ký... | User đã xác định + hành động + tài nguyên |
| Kết quả | Một user cụ thể, hoặc "khách" (*guest*) | Cho phép hoặc từ chối |
| Thất bại thì HTTP trả | `401 Unauthorized` (thực chất nghĩa là "chưa xác thực") | `403 Forbidden` (đã biết bạn là ai, nhưng không cho) |
| Trong Laravel | Guard, provider, `Auth`, Sanctum, Passport | Gate, Policy, `can`, `authorize` |

Thứ tự luôn là xác thực trước, phân quyền sau: không biết bạn là ai thì không thể quyết bạn được làm
gì. Một số quyết định phân quyền vẫn áp dụng cho khách (ví dụ "ai cũng được xem bài viết công khai"),
nên "chưa đăng nhập" không tự động có nghĩa là "cấm hết".

⚠️ Tên status `401 Unauthorized` là một sự đặt tên đáng tiếc của HTTP: nó dùng cho trường hợp
*chưa xác thực* (thiếu hoặc sai thông tin đăng nhập), còn "đã đăng nhập nhưng không đủ quyền" là
`403 Forbidden`. Laravel theo đúng quy ước này: middleware `auth` thất bại thì trả 401 (với request
muốn JSON) hoặc redirect về trang login; kiểm tra quyền thất bại thì trả 403.

### 1.2 Vì sao phải tách hai việc

Lỗi bảo mật kinh điển nhất ở tầng ứng dụng là: lập trình viên làm xác thực rất kỹ (đăng nhập, 2FA,
khoá tài khoản khi đoán sai mật khẩu nhiều lần), rồi quên phân quyền. Ví dụ:

```php
// routes/web.php
Route::get('/invoices/{invoice}', [InvoiceController::class, 'show'])->middleware('auth');

// InvoiceController
public function show(Invoice $invoice): View
{
    return view('invoices.show', ['invoice' => $invoice]);   // ⚠️ không hỏi: hoá đơn này có phải của user không?
}
```

Middleware `auth` chỉ đảm bảo "có ai đó đã đăng nhập". Bất kỳ user nào đăng nhập được cũng xem được
hoá đơn của mọi người bằng cách đổi số trên URL: `/invoices/1`, `/invoices/2`... Đây là lỗ hổng
*IDOR* (mục 13). Tách bạch hai khái niệm giúp bạn luôn tự hỏi hai câu cho mỗi route: "ai được vào?"
và "được làm gì với tài nguyên này?".

### 1.3 Bản đồ các thành phần trong Laravel

```
                         request
                            │
        ┌───────────────────▼────────────────────┐
        │ Middleware auth / auth:sanctum          │  XÁC THỰC
        │   └─ Guard (session | sanctum | ...)    │  "request này của user nào?"
        │        └─ Provider (eloquent | database)│  "lấy user đó ở đâu?"
        └───────────────────┬────────────────────┘
                            │  $request->user() đã có giá trị
        ┌───────────────────▼────────────────────┐
        │ Middleware can:..., Gate::authorize(),  │  PHÂN QUYỀN
        │ $user->can(), #[Authorize], Form Request│  "user này được làm X với Y?"
        │   └─ Gate (closure) | Policy (class)    │
        └───────────────────┬────────────────────┘
                            │
                       controller
                            │
        ┌───────────────────▼────────────────────┐
        │ #[Hidden], API Resource, query scope   │  ẨN DỮ LIỆU theo quyền
        └────────────────────────────────────────┘
```

Các phần còn lại của chương đi theo đúng bản đồ này: mục 2 tới 9 là xác thực, mục 10 tới 12 là
phân quyền, mục 13 là các lỗ hổng hay gặp khi ghép hai thứ lại.

## 2. Guard và provider

### 2.1 Hai câu hỏi tách biệt: "nhận diện thế nào" và "lấy user ở đâu"

Tài liệu Laravel mô tả lõi của hệ thống xác thực gồm hai loại thành phần:

- *Guard* quyết định cách xác định user cho mỗi request. Guard `session` có sẵn: đọc ID user lưu
  trong session (session lại được nhận diện nhờ cookie). Sanctum thêm guard `sanctum`: đọc session
  cookie hoặc Bearer token.
- *Provider* (đầy đủ là *user provider*) quyết định cách lấy user từ nơi lưu trữ. Có sẵn hai driver:
  `eloquent` (dùng một Eloquent model, mặc định `App\Models\User`) và `database` (dùng query builder,
  trả về object `GenericUser` thay vì model).

Tách như vậy để bạn thay một bên mà không đụng bên kia. Cùng một bảng `users` có thể được nhận diện
bằng session (trang web) và bằng token (API). Ngược lại, cùng cơ chế session có thể dùng cho hai
bảng user khác nhau (`users` cho khách hàng, `admins` cho nhân viên).

⚠️ Guard và provider không liên quan tới "vai trò" (*role*) hay "quyền" (*permission*). Tài liệu
Laravel nhấn mạnh điều này. Guard `admin` nghĩa là "nhận diện người đăng nhập vào khu admin, lấy từ
bảng admins", không phải "người này có quyền admin". Quyền thuộc về Gate và Policy.

### 2.2 File `config/auth.php`

Đây là nội dung `config/auth.php` trong skeleton Laravel 13 (đã bỏ comment):

```php
<?php

use App\Models\User;

return [
    'defaults' => [
        'guard' => env('AUTH_GUARD', 'web'),
        'passwords' => env('AUTH_PASSWORD_BROKER', 'users'),
    ],

    'guards' => [
        'web' => [
            'driver' => 'session',      // guard tên "web" dùng driver session
            'provider' => 'users',      // ... và lấy user qua provider tên "users"
        ],
    ],

    'providers' => [
        'users' => [
            'driver' => 'eloquent',
            'model' => env('AUTH_MODEL', User::class),
        ],

        // 'users' => [
        //     'driver' => 'database',
        //     'table' => 'users',
        // ],
    ],

    'passwords' => [
        'users' => [
            'provider' => 'users',
            'table' => env('AUTH_PASSWORD_RESET_TOKEN_TABLE', 'password_reset_tokens'),
            'expire' => 60,
            'throttle' => 60,
        ],
    ],

    'password_timeout' => env('AUTH_PASSWORD_TIMEOUT', 10800),
];
```

Đọc từng khối:

- `defaults.guard`: guard dùng khi bạn không nói rõ (gọi `Auth::user()` thay vì
  `Auth::guard('admin')->user()`). Mặc định `web`.
- `guards`: danh sách guard có tên. Mỗi guard = một driver (cách nhận diện) + một provider (nơi lấy
  user). Lưu ý không có guard `sanctum` ở đây: Sanctum tự đăng ký guard của nó khi được cài (mục 8).
- `providers`: danh sách provider có tên.
- `passwords`: cấu hình *password broker* cho chức năng quên mật khẩu (mục 5). `expire` là số phút
  token reset còn hiệu lực, `throttle` là số giây phải chờ giữa hai lần xin link.
- `password_timeout`: số giây (10800 = 3 giờ) mà một lần "xác nhận lại mật khẩu" còn hiệu lực
  (mục 3.8).

### 2.3 Model `User` và hợp đồng `Authenticatable`

Model `User` trong skeleton Laravel 13:

```php
<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail;
use Database\Factories\UserFactory;
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Attributes\Hidden;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

#[Fillable(['name', 'email', 'password'])]
#[Hidden(['password', 'remember_token'])]
class User extends Authenticatable
{
    /** @use HasFactory<UserFactory> */
    use HasFactory, Notifiable;

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
        ];
    }
}
```

Mấy điểm liên quan tới chương này:

- `User` kế thừa `Illuminate\Foundation\Auth\User` (đặt bí danh `Authenticatable`). Class cha đó là
  một Eloquent model đã cài sẵn interface `Illuminate\Contracts\Auth\Authenticatable` và vài trait
  khác (trong đó có `Authorizable` để gọi `$user->can(...)`, `CanResetPassword` cho quên mật khẩu,
  `MustVerifyEmail` trait cho xác minh email).
- `#[Fillable]` là whitelist cho mass assignment (mục 13.1). `#[Hidden]` giấu `password` và
  `remember_token` khi model bị chuyển thành array/JSON (mục 12).
- Cast `'password' => 'hashed'`: gán mật khẩu thô vào `$user->password` thì Eloquent tự băm trước
  khi lưu (mục 4.3).
- Dòng `MustVerifyEmail` đang bị comment: bật nó lên khi cần xác minh email (mục 6).

Interface `Authenticatable` là thứ guard cần ở một "user". Nó rất nhỏ:

```php
<?php

namespace Illuminate\Contracts\Auth;

interface Authenticatable
{
    public function getAuthIdentifierName();   // tên cột khoá chính, thường "id"
    public function getAuthIdentifier();       // giá trị khoá chính, ví dụ 42
    public function getAuthPasswordName();     // tên cột mật khẩu, thường "password"
    public function getAuthPassword();         // chuỗi hash mật khẩu
    public function getRememberToken();
    public function setRememberToken($value);
    public function getRememberTokenName();    // thường "remember_token"
}
```

Vì guard chỉ làm việc qua interface này, "user" có thể là bất kỳ class nào cài nó, không nhất thiết
là Eloquent model.

Bảng `users` trong migration mặc định:

```php
Schema::create('users', function (Blueprint $table) {
    $table->id();
    $table->string('name');
    $table->string('email')->unique();
    $table->timestamp('email_verified_at')->nullable();
    $table->string('password');
    $table->rememberToken();          // cột remember_token: VARCHAR(100) NULL
    $table->timestamps();
});
```

Tài liệu Laravel lưu ý: cột mật khẩu cần ít nhất 60 ký tự (độ dài hash bcrypt), cột
`remember_token` là chuỗi nullable 100 ký tự. Migration mặc định đã đáp ứng cả hai. Cùng file
migration này còn tạo bảng `password_reset_tokens` (mục 5) và `sessions` (khi session driver là
`database`, xem [Chương 15](15-php-va-web.md) về session).

### 2.4 Hợp đồng `UserProvider`

Provider cài interface `Illuminate\Contracts\Auth\UserProvider`:

```php
interface UserProvider
{
    public function retrieveById($identifier);
    public function retrieveByToken($identifier, $token);
    public function updateRememberToken(Authenticatable $user, $token);
    public function retrieveByCredentials(array $credentials);
    public function validateCredentials(Authenticatable $user, array $credentials);
    public function rehashPasswordIfRequired(Authenticatable $user, array $credentials, bool $force = false);
}
```

Ý nghĩa:

- `retrieveById`: tìm user theo khoá chính. Guard session gọi hàm này ở mỗi request.
- `retrieveByToken` và `updateRememberToken`: phục vụ "remember me" (mục 3.6).
- `retrieveByCredentials`: tìm user theo thông tin đăng nhập, ví dụ theo email. Tài liệu nhấn mạnh
  hàm này không được kiểm tra mật khẩu.
- `validateCredentials`: so mật khẩu người dùng gõ với hash đã lưu (thường bằng `Hash::check`).
- `rehashPasswordIfRequired`: băm lại mật khẩu nếu thuật toán hoặc cost đã đổi (mục 4.4).

Tách "tìm" khỏi "so mật khẩu" có lý do: logic tìm phụ thuộc nơi lưu trữ (SQL, MongoDB, LDAP...), còn
logic so mật khẩu thì giống nhau.

### 2.5 Tự dựng một guard thu nhỏ để hiểu cơ chế

Trước khi xem Laravel làm gì, hãy tự viết một phiên bản rất nhỏ bằng PHP thuần. Đoạn sau mô phỏng ý
tưởng guard + provider, không phải code của Laravel. Session được giả lập bằng một `ArrayObject` sống
qua nhiều "request".

```php
<?php
declare(strict_types=1);

// Mô phỏng thu nhỏ guard + provider của Laravel (KHÔNG phải code Laravel thật).

final class User
{
    public function __construct(
        public readonly int $id,
        public readonly string $email,
        public readonly string $passwordHash,
    ) {}
}

// Provider: biết lấy user TỪ ĐÂU (ở đây là một array, Laravel thì là Eloquent/DB).
interface UserProvider
{
    public function retrieveById(int $id): ?User;
    /** @param array<string, string> $credentials */
    public function retrieveByCredentials(array $credentials): ?User;
    /** @param array<string, string> $credentials */
    public function validateCredentials(User $user, array $credentials): bool;
}

final class ArrayUserProvider implements UserProvider
{
    /** @param list<User> $users */
    public function __construct(private array $users) {}

    public function retrieveById(int $id): ?User
    {
        foreach ($this->users as $u) {
            if ($u->id === $id) {
                return $u;
            }
        }
        return null;
    }

    public function retrieveByCredentials(array $credentials): ?User
    {
        // Laravel bỏ mọi key chứa "password" rồi tìm theo phần còn lại; ở đây chỉ tìm theo email cho gọn.
        foreach ($this->users as $u) {
            if ($u->email === ($credentials['email'] ?? null)) {
                return $u;
            }
        }
        return null;
    }

    public function validateCredentials(User $user, array $credentials): bool
    {
        return password_verify($credentials['password'] ?? '', $user->passwordHash);
    }
}

// Guard: biết XÁC ĐỊNH user của request NHƯ THẾ NÀO (ở đây: đọc id trong session).
final class SessionGuard
{
    private ?User $user = null;

    /** @param ArrayObject<string, mixed> $session */
    public function __construct(
        private string $name,
        private UserProvider $provider,
        private ArrayObject $session,
    ) {}

    private function key(): string
    {
        return 'login_' . $this->name;          // Laravel: 'login_web_' . sha1(SessionGuard::class)
    }

    /** @param array<string, string> $credentials */
    public function attempt(array $credentials): bool
    {
        $user = $this->provider->retrieveByCredentials($credentials);
        if ($user === null || !$this->provider->validateCredentials($user, $credentials)) {
            return false;
        }
        $this->session[$this->key()] = $user->id; // chỉ lưu ID, không lưu cả user
        $this->user = $user;
        return true;
    }

    public function user(): ?User
    {
        if ($this->user !== null) {
            return $this->user;                  // đã tra trong request này thì dùng lại
        }
        $id = $this->session[$this->key()] ?? null;
        return $this->user = is_int($id) ? $this->provider->retrieveById($id) : null;
    }

    public function logout(): void
    {
        unset($this->session[$this->key()]);
        $this->user = null;
    }
}

$provider = new ArrayUserProvider([
    new User(1, 'an@example.com', password_hash('mat-khau-an', PASSWORD_DEFAULT)),
]);
$session = new ArrayObject();   // "kho session" sống qua nhiều request

// Request 1: form đăng nhập
$guard = new SessionGuard('web', $provider, $session);
var_dump($guard->attempt(['email' => 'an@example.com', 'password' => 'sai']));        // in ra: bool(false)
var_dump($guard->attempt(['email' => 'an@example.com', 'password' => 'mat-khau-an'])); // in ra: bool(true)
print_r($session->getArrayCopy());
// in ra:
// Array
// (
//     [login_web] => 1
// )

// Request 2: guard MỚI (mỗi request PHP bắt đầu từ đầu), chỉ còn session
$guard2 = new SessionGuard('web', $provider, $session);
echo $guard2->user()?->email ?? 'khách', "\n";   // in ra: an@example.com

$guard2->logout();
// Request 3
$guard3 = new SessionGuard('web', $provider, $session);
echo $guard3->user()?->email ?? 'khách', "\n";   // in ra: khách
```

Ba ý cần rút ra, vì Laravel làm y như vậy ở quy mô lớn hơn:

1. Đăng nhập thành công chỉ để lại một thứ trong session: ID của user. Không lưu mật khẩu, không lưu
   cả object user.
2. Ở mỗi request sau, guard đọc ID từ session rồi nhờ provider tra lại user (một query
   `SELECT ... WHERE id = ?` với Eloquent). Kết quả được nhớ trong guard suốt request đó, nên gọi
   `Auth::user()` nhiều lần chỉ tốn một query.
3. Guard không biết dữ liệu nằm ở đâu, provider không biết request đến bằng cách nào. Đổi một bên
   không ảnh hưởng bên kia.

### 2.6 Nhiều guard trong một ứng dụng

Giả sử bạn muốn khu quản trị dùng bảng `admins` riêng. Thêm một provider và một guard:

```php
// config/auth.php (phần thêm)
'guards' => [
    'web' => ['driver' => 'session', 'provider' => 'users'],
    'admin' => ['driver' => 'session', 'provider' => 'admins'],
],

'providers' => [
    'users' => ['driver' => 'eloquent', 'model' => App\Models\User::class],
    'admins' => ['driver' => 'eloquent', 'model' => App\Models\Admin::class],
],
```

Rồi dùng tên guard ở những chỗ cần:

```php
// Đăng nhập vào guard admin
if (Auth::guard('admin')->attempt($credentials)) { /* ... */ }

// Bảo vệ route bằng guard admin
Route::middleware('auth:admin')->prefix('admin')->group(function (): void {
    // ...
});

// Lấy user theo guard cụ thể
$admin = Auth::guard('admin')->user();
```

Vì key trong session có chứa tên guard (`login_web_...` và `login_admin_...`), một trình duyệt có
thể đồng thời đăng nhập ở cả hai guard mà chúng không đè lên nhau.

Middleware `auth` nhận nhiều guard: `auth:web,admin` thử lần lượt từng guard, guard đầu tiên xác thực
được sẽ được đặt làm guard mặc định cho phần còn lại của request (mã nguồn gọi
`$this->auth->shouldUse($guard)`). Nhờ vậy, trong controller, `Auth::user()` và `$request->user()`
trả về đúng user của guard đã khớp.

⚠️ Nhiều guard là công cụ cho các loại người dùng thật sự khác nhau (bảng khác, cách đăng nhập khác).
Nếu chỉ là "user thường" và "user có quyền admin" trong cùng một bảng, đừng tạo guard mới: dùng một
cột vai trò và Gate/Policy (mục 10, 11).

### 2.7 Tự viết guard hoặc provider (biết là có)

Khi nhu cầu vượt ra ngoài những gì có sẵn, Laravel cho mở rộng trong `AppServiceProvider::boot()`:

- `Auth::extend('jwt', fn ($app, string $name, array $config) => new JwtGuard(...))`: đăng ký một
  driver guard mới tên `jwt`, trả về object cài `Illuminate\Contracts\Auth\Guard`.
- `Auth::viaRequest('custom-token', fn (Request $request) => User::where(...)->first())`: cách nhanh
  nhất để có một guard dựa trên request; closure trả user hoặc `null`.
- `Auth::provider('mongo', fn ($app, array $config) => new MongoUserProvider(...))`: đăng ký driver
  provider mới.

Sau khi đăng ký, khai báo tên driver đó trong `config/auth.php` như các driver có sẵn. Phần lớn ứng
dụng không bao giờ cần tự viết guard; với API, Sanctum (mục 8) thường đủ.

## 3. Đăng nhập bằng session: từ form tới từng request

### 3.1 Luồng tổng thể

Với ứng dụng web truyền thống (trình duyệt hiển thị HTML do Laravel render), cách xác thực mặc định
là session. Tài liệu Laravel tóm tắt: người dùng gửi username và mật khẩu qua form; nếu đúng, ứng
dụng lưu thông tin user vào session; trình duyệt nhận một cookie chứa *session ID*; ở các request
sau, ứng dụng dùng session ID đó để lấy dữ liệu session, thấy trong đó có thông tin đăng nhập, và coi
user là đã xác thực.

```
Trình duyệt                                   Laravel
    │  POST /login  email+password                │
    │────────────────────────────────────────────►│ Auth::attempt(): tìm user, so hash
    │                                             │ session: login_web_<sha1> = 42
    │                                             │ đổi session ID (chống fixation)
    │  302 → /dashboard                           │
    │  Set-Cookie: laravel_session=<ID mới>       │
    │◄────────────────────────────────────────────│
    │                                             │
    │  GET /dashboard                             │
    │  Cookie: laravel_session=<ID mới>           │
    │────────────────────────────────────────────►│ StartSession đọc session theo ID
    │                                             │ middleware auth: guard đọc 42 trong session
    │                                             │ provider: SELECT * FROM users WHERE id = 42
    │  200 HTML                                   │
    │◄────────────────────────────────────────────│
```

Session, cookie và session fixation ở mức PHP thuần đã có ở [Chương 15](15-php-va-web.md). Chương
này chỉ nói phần Laravel đặt lên trên.

### 3.2 Viết controller đăng nhập thủ công

Bạn không bắt buộc dùng starter kit (mục 7). Đây là controller đăng nhập tối thiểu theo tài liệu
Laravel, thêm chú thích:

```php
<?php
declare(strict_types=1);

namespace App\Http\Controllers;

use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;

final class LoginController extends Controller
{
    public function authenticate(Request $request): RedirectResponse
    {
        // 1. Validate: đảm bảo email và password là chuỗi, có mặt
        $credentials = $request->validate([
            'email' => ['required', 'email'],
            'password' => ['required'],
        ]);

        // 2. attempt(): tìm user theo các key KHÔNG chứa "password", rồi so mật khẩu với hash
        if (Auth::attempt($credentials, remember: $request->boolean('remember'))) {
            // 3. Đổi session ID sau khi đăng nhập
            $request->session()->regenerate();

            // 4. Quay lại trang user định vào trước khi bị bắt đăng nhập, mặc định /dashboard
            return redirect()->intended('dashboard');
        }

        // 5. Sai: báo lỗi chung chung, giữ lại email đã gõ
        return back()->withErrors([
            'email' => 'The provided credentials do not match our records.',
        ])->onlyInput('email');
    }
}
```

Từng bước, kèm lý do:

1. Validate trước. Không chỉ để báo lỗi đẹp: nếu bỏ qua, `email` có thể là một array (xem bẫy ở
   mục 3.3).
2. `Auth::attempt($credentials, $remember)` trả `true` nếu đăng nhập được. Không băm mật khẩu trước
   khi truyền vào: framework tự so mật khẩu thô với hash trong DB. Tham số thứ hai bật "remember me"
   (mục 3.6).
3. `regenerate()` đổi session ID để chống *session fixation* (kẻ tấn công cài sẵn một session ID cho
   nạn nhân, chờ nạn nhân đăng nhập rồi dùng chính ID đó). Đọc mã nguồn Laravel 13 sẽ thấy hàm
   `login()` của `SessionGuard` đã tự gọi `$this->session->regenerate(true)`; tài liệu vẫn hướng dẫn
   gọi thêm, và gọi thêm không có hại.
4. `redirect()->intended($fallback)`: khi middleware `auth` chặn một khách, nó redirect về trang login
   và lưu URL ban đầu vào session. `intended()` đọc URL đó để đưa user về đúng chỗ.
5. Thông báo lỗi giống nhau cho "email không tồn tại" và "sai mật khẩu". Nếu báo khác nhau, kẻ tấn
   công dò được email nào đã đăng ký (*user enumeration*).

Thêm điều kiện khi đăng nhập:

```php
// Chỉ cho user đang active đăng nhập: thêm cột vào mảng credentials
Auth::attempt(['email' => $email, 'password' => $password, 'active' => 1]);

// Điều kiện phức tạp: closure nhận query builder
Auth::attempt([
    'email' => $email,
    'password' => $password,
    fn (Builder $query) => $query->has('activeSubscription'),
]);

// Kiểm tra trên chính object user sau khi mật khẩu đã đúng
Auth::attemptWhen(
    ['email' => $email, 'password' => $password],
    fn (User $user): bool => $user->isNotBanned(),
);
```

### 3.3 Bên trong `Auth::attempt()`

Đọc `SessionGuard::attempt()` và `EloquentUserProvider` trong Laravel 13, trình tự là:

```
Auth::attempt($credentials, $remember)
 └─ Timebox (tối thiểu 200 ms nếu thất bại)
     1. phát event Attempting
     2. provider->retrieveByCredentials($credentials)
          - bỏ mọi key có chứa chữ "password"
          - mỗi key còn lại thành một điều kiện: where(key, value)
            (value là array → whereIn; value là closure → gọi closure với query)
          - ->first()
     3. user tìm thấy? provider->validateCredentials($user, $credentials)
          - Hash::check(mật khẩu thô, $user->getAuthPassword())
     4a. Đúng: phát event Validated
          - rehashPasswordIfRequired (nếu bật rehash_on_login, mục 4.4)
          - login($user, $remember):
              session[login_web_<sha1(SessionGuard)>] = id
              session->regenerate(true)
              session[password_hash_web] = HMAC(hash mật khẩu)
              nếu $remember: đặt remember_token, xếp hàng cookie remember_web_...
              phát event Login
          - trả true (thoát Timebox sớm)
     4b. Sai: phát event Failed, trả false (sau khi Timebox chờ đủ thời gian)
```

Vài chi tiết đáng chú ý:

- *Timebox*. Kiểm tra bcrypt tốn hàng chục tới hàng trăm mili giây, còn "email không tồn tại" thì trả
  lời gần như tức thì. Kẻ tấn công đo thời gian phản hồi sẽ biết email nào có trong hệ thống. Laravel
  bọc `attempt()` trong một `Timebox`: nếu thất bại, hàm không trả về trước một khoảng thời gian tối
  thiểu (mặc định 200000 micro giây, đọc từ config `auth.timebox_duration`). Thành công thì
  `returnEarly()` để user không phải chờ.
- Key session có dạng `login_<tên guard>_<sha1 của tên class guard>`, ví dụ
  `login_web_59ba36add...`. Chỉ ID user được lưu.
- ⚠️ Vì `retrieveByCredentials` biến array thành `whereIn`, truyền thẳng `$request->only('email',
  'password')` mà không validate là nguy hiểm: client gửi `email[]=a@x.com&email[]=b@x.com` thì câu
  query thành `WHERE email IN (...)`. Luôn validate `email` là chuỗi email trước.
- ⚠️ Cũng vì mọi key không chứa "password" đều thành điều kiện `where`, đừng bao giờ đưa nguyên
  `$request->all()` vào `attempt()`: client có thể chèn thêm cột tuỳ ý vào điều kiện tìm.

### 3.4 Lấy user hiện tại và kiểm tra đăng nhập

```php
use Illuminate\Support\Facades\Auth;

$user = Auth::user();          // User|null, theo guard mặc định
$id = Auth::id();              // khoá chính hoặc null
$loggedIn = Auth::check();     // bool
$isGuest = Auth::guest();      // bool, ngược của check()

// Trong controller: cùng kết quả, không cần facade
public function update(Request $request): RedirectResponse
{
    $user = $request->user();
    // ...
}

// Theo một guard cụ thể
$admin = Auth::guard('admin')->user();
```

Hàm helper `auth()` trả về cùng đối tượng như facade `Auth`: `auth()->user()`, `auth()->id()`.

Bên trong `SessionGuard::user()`:

1. Nếu request này đã logout thì trả `null`.
2. Nếu đã tra user trong request này rồi thì trả lại object cũ (không query lại).
3. Đọc ID trong session, gọi `provider->retrieveById($id)`.
4. Nếu chưa có user và request có cookie "remember me" hợp lệ, đăng nhập lại từ cookie (mục 3.6).

⚠️ "Không query lại trong cùng request" là đúng với PHP-FPM, nơi mỗi request dựng lại toàn bộ ứng
dụng. Với Octane (một worker phục vụ nhiều request), đừng lưu `Auth::user()` vào property của một
singleton: request sau sẽ thấy user của request trước. Octane được nói ở
[Chương 30](30-laravel-testing-octane-deploy.md).

### 3.5 Bảo vệ route: middleware `auth` và `guest`

```php
// Chỉ user đã đăng nhập (guard mặc định)
Route::get('/flights', [FlightController::class, 'index'])->middleware('auth');

// Chỉ admin đăng nhập qua guard admin
Route::get('/admin', [AdminController::class, 'index'])->middleware('auth:admin');

// Chỉ khách (đã đăng nhập thì bị đẩy đi chỗ khác), dùng cho trang login/register
Route::get('/login', [LoginController::class, 'show'])->middleware('guest');
```

`auth` là alias của `Illuminate\Auth\Middleware\Authenticate`. Khi không có guard nào xác thực được,
nó ném `AuthenticationException`. Exception handler của Laravel xử lý exception này như sau (đọc từ
`Illuminate\Foundation\Exceptions\Handler::unauthenticated()`):

- Request muốn JSON (ví dụ header `Accept: application/json`): trả `401` với body
  `{"message": "Unauthenticated."}`.
- Ngược lại: redirect về route tên `login` và ghi nhớ URL định vào (để `intended()` dùng).

Đổi đích redirect trong `bootstrap/app.php`:

```php
->withMiddleware(function (Middleware $middleware): void {
    $middleware->redirectGuestsTo('/login');            // khách bị auth chặn đi đâu
    $middleware->redirectUsersTo('/panel');             // user đã đăng nhập bị guest chặn đi đâu
})
```

⚠️ Nếu ứng dụng chỉ là API và không có route tên `login`, request không gửi `Accept: application/json`
sẽ làm Laravel cố redirect tới route không tồn tại và báo lỗi. Client API nên luôn gửi header này.

### 3.6 "Remember me" hoạt động thế nào

Session có thời hạn (`SESSION_LIFETIME`, xem [Chương 15](15-php-va-web.md)). "Remember me" giữ user
đăng nhập lâu hơn session bằng một cookie riêng. Khi gọi `Auth::attempt($credentials, true)` hoặc
`Auth::login($user, true)`, `SessionGuard` (Laravel 13) làm:

1. Nếu cột `remember_token` của user đang rỗng, sinh một chuỗi ngẫu nhiên 60 ký tự và lưu vào cột đó.
2. Tạo cookie tên `remember_<guard>_<sha1>` với giá trị
   `<id>|<remember_token>|<HMAC-SHA256 của hash mật khẩu, khoá là APP_KEY>`. Thời hạn mặc định của
   cookie là 576000 phút (400 ngày). Như mọi cookie khác trong group `web`, nó được middleware
   `EncryptCookies` mã hoá.

Ở request sau, nếu session không còn thông tin đăng nhập nhưng có cookie này, guard:

1. Tách cookie thành ba phần, tìm user theo ID, so `remember_token` bằng `hash_equals`.
2. So phần thứ ba với HMAC của hash mật khẩu hiện tại. Đổi mật khẩu thì hash đổi, cookie cũ hết tác
   dụng.
3. Nếu khớp: đăng nhập lại vào session, `Auth::viaRemember()` trả `true` trong request này.

Mô phỏng ý tưởng bằng PHP thuần (rút gọn: không mã hoá cookie, không có DB):

```php
<?php
declare(strict_types=1);

// Mô phỏng giá trị cookie "remember me" của Laravel (rút gọn, không mã hoá cookie).
const APP_KEY = 'base64:khoa-bi-mat-cua-ung-dung';

function hashPasswordForCookie(string $passwordHash): string
{
    return hash_hmac('sha256', $passwordHash, APP_KEY);   // HMAC của HASH mật khẩu, không phải mật khẩu
}

// Lúc đăng nhập có tích "remember me"
$userId = 42;
$rememberToken = bin2hex(random_bytes(30));                  // Laravel: Str::random(60), lưu ở cột remember_token
$passwordHash = password_hash('mat-khau-cu', PASSWORD_DEFAULT);

$cookie = $userId . '|' . $rememberToken . '|' . hashPasswordForCookie($passwordHash);
echo count(explode('|', $cookie)), " phần\n";                // in ra: 3 phần

// Request sau, session đã hết hạn: guard đọc cookie và kiểm tra
function userFromCookie(string $cookie, string $tokenInDb, string $passwordHashInDb): bool
{
    [$id, $token, $hash] = explode('|', $cookie, 3);
    return hash_equals($tokenInDb, $token)
        && hash_equals(hashPasswordForCookie($passwordHashInDb), $hash);
}

var_dump(userFromCookie($cookie, $rememberToken, $passwordHash));   // in ra: bool(true)

// User đổi mật khẩu ở thiết bị khác → hash trong DB đổi → cookie cũ hết tác dụng
$newHash = password_hash('mat-khau-moi', PASSWORD_DEFAULT);
var_dump(userFromCookie($cookie, $rememberToken, $newHash));        // in ra: bool(false)

// User bấm logout → Laravel đổi remember_token mới → cookie cũ cũng hết tác dụng
var_dump(userFromCookie($cookie, bin2hex(random_bytes(30)), $passwordHash)); // in ra: bool(false)
```

⚠️ Cạm bẫy với "remember me":

- Cột `remember_token` lưu token ở dạng thô (không băm). Ai đọc được bảng `users` và biết `APP_KEY`
  thì dựng được cookie. Giữ `APP_KEY` bí mật, đừng commit `.env`.
- Mọi thiết bị của một user dùng chung một `remember_token`. Logout ở một máy (`Auth::logout()`) sinh
  token mới, nên cookie "remember me" ở mọi máy khác cũng mất hiệu lực. Muốn chỉ logout máy hiện tại
  mà không đổi token, dùng `Auth::logoutCurrentDevice()`.
- Đổi `APP_KEY` làm mọi cookie mã hoá cũ (kể cả remember cookie và session cookie) không giải mã được.
  Laravel hỗ trợ `APP_PREVIOUS_KEYS` để xoay khoá dần; chi tiết ở tài liệu Encryption.

### 3.7 Đăng xuất

```php
public function logout(Request $request): RedirectResponse
{
    Auth::logout();                          // xoá ID khỏi session, xoá cookie remember, đổi remember_token

    $request->session()->invalidate();       // xoá sạch dữ liệu session, cấp session ID mới
    $request->session()->regenerateToken();  // đổi CSRF token

    return redirect('/');
}
```

Ba lệnh, ba việc khác nhau. `Auth::logout()` chỉ gỡ thông tin đăng nhập; nếu không `invalidate()`,
các dữ liệu khác trong session (giỏ hàng, flash message, dữ liệu tạm của user cũ) vẫn còn và người
dùng tiếp theo trên cùng máy có thể thấy. `regenerateToken()` để CSRF token của phiên cũ không dùng
lại được.

⚠️ Route logout phải là `POST` (có CSRF token), không phải `GET`. Nếu là `GET`, một thẻ
`<img src="https://app.vn/logout">` trên trang bất kỳ cũng đăng xuất được người dùng của bạn (lý do
"GET không đổi trạng thái" ở [Chương 17](17-bao-mat.md)). Starter kit của Laravel dùng `POST /logout`.

### 3.8 Đăng xuất các thiết bị khác và xác nhận lại mật khẩu

Đăng xuất mọi thiết bị khác, giữ thiết bị hiện tại (thường làm khi user đổi mật khẩu hoặc nghi bị lộ):

```php
// 1. Gắn middleware auth.session cho các route dùng session
Route::middleware(['auth', 'auth.session'])->group(function (): void {
    // ...
});

// 2. Trong action "đăng xuất thiết bị khác", yêu cầu user nhập mật khẩu hiện tại
Auth::logoutOtherDevices($request->input('current_password'));
```

Cơ chế (đọc từ mã nguồn): `logoutOtherDevices()` kiểm tra mật khẩu, rồi băm lại chính mật khẩu đó
(bcrypt sinh salt mới nên hash mới khác hash cũ dù mật khẩu không đổi) và lưu vào DB. Middleware
`auth.session` (`AuthenticateSession`) ở mỗi request so HMAC của hash mật khẩu đã lưu trong session
(`password_hash_web`) với hash hiện tại trong DB. Ở các thiết bị khác, hai giá trị không còn khớp nên
chúng bị logout. Thiết bị hiện tại được cập nhật giá trị mới nên vẫn đăng nhập.

⚠️ Thiếu middleware `auth.session` thì `logoutOtherDevices()` vẫn đổi hash trong DB nhưng session ở
máy khác không bị kiểm tra, nghĩa là chúng vẫn đăng nhập.

*Xác nhận lại mật khẩu* (*password confirmation*): với thao tác nhạy cảm (đổi email, xoá tài khoản,
xem mã khôi phục 2FA), bắt user gõ lại mật khẩu dù đang đăng nhập. Phòng trường hợp ai đó dùng máy
đang mở sẵn.

```php
// Trang hỏi mật khẩu, tên route phải là password.confirm
Route::get('/confirm-password', fn () => view('auth.confirm-password'))
    ->middleware('auth')->name('password.confirm');

Route::post('/confirm-password', function (Request $request) {
    if (! Hash::check($request->password, $request->user()->password)) {
        return back()->withErrors(['password' => ['The provided password does not match our records.']]);
    }
    $request->session()->passwordConfirmed();     // ghi thời điểm xác nhận vào session
    return redirect()->intended();
})->middleware(['auth', 'throttle:6,1']);

// Route nhạy cảm
Route::post('/settings/delete-account', [AccountController::class, 'destroy'])
    ->middleware(['auth', 'password.confirm']);
```

Middleware `password.confirm` đọc thời điểm xác nhận trong session (key
`auth.password_confirmed_at`). Nếu đã quá `password_timeout` giây (mặc định 10800, tức 3 giờ), nó
lưu URL đang định vào và redirect tới route `password.confirm`.

### 3.9 Chống dò mật khẩu: giới hạn số lần đăng nhập

Không có giới hạn, kẻ tấn công thử hàng triệu mật khẩu cho một email (*brute force*) hoặc thử một
mật khẩu phổ biến cho hàng triệu email (*credential stuffing*, dùng mật khẩu lộ từ trang khác). Các
starter kit của Laravel (qua Fortify) đã có rate limit cho login, theo tổ hợp email và IP. Tự làm thì
dùng `RateLimiter` (công cụ đầy đủ ở [Chương 24](24-laravel-routing-controller-middleware.md)):

```php
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Support\Facades\RateLimiter;

// AppServiceProvider::boot()
RateLimiter::for('login', function (Request $request): Limit {
    return Limit::perMinute(5)->by($request->string('email')->lower() . '|' . $request->ip());
});

// routes/web.php
Route::post('/login', [LoginController::class, 'authenticate'])->middleware('throttle:login');
```

⚠️ Chỉ giới hạn theo IP thì botnet (nhiều IP) vượt qua; chỉ giới hạn theo email thì kẻ xấu có thể cố
tình khoá tài khoản người khác. Ghép cả hai như trên là cách phổ biến. Khi vượt giới hạn, middleware
`throttle` trả `429 Too Many Requests`.

Event `Illuminate\Auth\Events\Lockout` được định nghĩa trong framework nhưng framework không tự phát
nó, kể cả trong middleware `throttle`. Fortify phát event này trong bước `EnsureLoginIsNotThrottled`,
và bước đó chỉ chạy khi config `fortify.limiters.login` để trống. Cấu hình của starter kit đặt
`'login' => 'login'`, nên route `POST /login` dùng middleware `throttle:login` và khi vượt giới hạn
không có event `Lockout`. Muốn nghe event này trong code tự viết thì tự gọi
`event(new Lockout($request))` ở chỗ phát hiện vượt giới hạn.

### 3.10 Các cách đăng nhập khác

| Hàm | Làm gì | Khi nào dùng |
|---|---|---|
| `Auth::login($user, $remember = false)` | Đăng nhập một object user có sẵn, không kiểm mật khẩu | Ngay sau khi đăng ký; sau khi đăng nhập qua Google (Socialite) |
| `Auth::loginUsingId(1, remember: true)` | Như trên, nhưng truyền khoá chính | Công cụ nội bộ, test |
| `Auth::once($credentials)` | Xác thực cho đúng request này, không dùng session/cookie, không phát event `Login` | API đơn giản không trạng thái |
| `Auth::validate($credentials)` | Chỉ kiểm thông tin đúng hay sai, không đăng nhập | Xác nhận mật khẩu trước thao tác |
| Middleware `auth.basic` | HTTP Basic Authentication: trình duyệt hiện hộp thoại hỏi username/password, mặc định dùng cột `email` | Trang nội bộ đơn giản |
| `Auth::onceBasic()` trong middleware tự viết | Basic auth không ghi session | API nội bộ |

⚠️ `Auth::login($user)` và `loginUsingId()` không kiểm tra gì cả. Đừng bao giờ gọi chúng với ID lấy từ
input của người dùng.

### 3.11 Event trong quá trình xác thực

Laravel phát các event sau (namespace `Illuminate\Auth\Events`), bạn có thể nghe để ghi log bảo
mật, gửi email cảnh báo đăng nhập lạ, khoá tài khoản...: `Registered`, `Attempting`,
`Authenticated`, `Login`, `Failed`, `Validated`, `Verified`, `Logout`, `CurrentDeviceLogout`,
`OtherDeviceLogout`, `Lockout`, `PasswordReset`, `PasswordResetLinkSent`. Cách viết listener ở
[Chương 29](29-laravel-queue-event-schedule-cache.md).

## 4. Băm mật khẩu trong Laravel

### 4.1 Nhắc lại ngắn

Mật khẩu không bao giờ được lưu dạng thô, cũng không được "mã hoá" (mã hoá thì giải mã được). Ta lưu
một *hash* tạo bởi thuật toán chậm có *salt* như bcrypt hoặc Argon2id. Lý do, cách dùng
`password_hash`, `password_verify`, `password_needs_rehash` ở mức PHP thuần đã có đủ ở
[Chương 17, mục 5](17-bao-mat.md). Laravel chỉ bọc các hàm đó lại sau facade `Hash`.

### 4.2 Facade `Hash` và cấu hình

```php
use Illuminate\Support\Facades\Hash;

$hashed = Hash::make('mat-khau');                    // bọc password_hash()
$ok = Hash::check('mat-khau', $hashed);              // bọc password_verify(), trả bool
$old = Hash::needsRehash($hashed);                   // bọc password_needs_rehash()

$hashed = Hash::make('mat-khau', ['rounds' => 12]);  // tự chỉnh cost bcrypt cho một lần gọi
```

Cấu hình nằm trong `config/hashing.php` (không có sẵn trong skeleton; tạo bằng
`php artisan config:publish hashing`). Bản trong framework Laravel 13, bỏ comment:

```php
return [
    'driver' => env('HASH_DRIVER', 'bcrypt'),          // bcrypt | argon | argon2id

    'bcrypt' => [
        'rounds' => env('BCRYPT_ROUNDS', 12),
        'verify' => env('HASH_VERIFY', true),
        'limit' => env('BCRYPT_LIMIT', null),
    ],

    'argon' => [
        'memory' => env('ARGON_MEMORY', 65536),
        'threads' => env('ARGON_THREADS', 1),
        'time' => env('ARGON_TIME', 4),
        'verify' => env('HASH_VERIFY', true),
    ],

    'rehash_on_login' => true,
];
```

- `driver`: mặc định `bcrypt`. Đổi bằng biến môi trường `HASH_DRIVER`.
- `rounds`: cost của bcrypt (mỗi lần tăng 1 thì thời gian băm gấp đôi). File `.env.example` của
  skeleton đặt `BCRYPT_ROUNDS=12`.
- `verify`: khi bật, `Hash::check()` kiểm tra hash có đúng thuật toán đang cấu hình không; sai thuật
  toán thì ném `RuntimeException` thay vì trả `false`. Lý do (theo tài liệu): chặn việc thao túng
  thuật toán, vì một hash "lạ" có thể là dấu hiệu bị tấn công. Khi đang chuyển từ thuật toán này sang
  thuật toán khác, đặt `HASH_VERIFY=false` để hai loại hash cùng tồn tại.
- `limit`: nếu đặt, `Hash::make()` ném exception khi chuỗi dài hơn số byte này (lý do ở bẫy 72 byte
  bên dưới). Mặc định `null`, tức không giới hạn.

Trong file test (`phpunit.xml` của skeleton), `BCRYPT_ROUNDS` được hạ xuống thấp để test chạy nhanh.
Đừng mang giá trị đó lên production.

### 4.3 Cast `hashed`: tự băm khi gán

Model `User` mặc định có cast `'password' => 'hashed'`. Đọc mã nguồn
(`HasAttributes::castAttributeAsHashedString`):

- Gán `null` thì giữ `null`.
- Gán một chuỗi chưa phải hash thì gọi `Hash::make()` trước khi lưu.
- Gán một chuỗi đã là hash (ví dụ bạn lỡ gọi `Hash::make()` trước) thì giữ nguyên, sau khi kiểm tra
  cấu hình của hash đó hợp lệ. Nhờ vậy không bị băm hai lần.

```php
$user->password = $request->validated('password');   // mật khẩu thô
$user->save();                                       // trong DB là $2y$12$...
```

⚠️ Cast chỉ chạy khi gán qua Eloquent model. Cập nhật bằng query builder
(`DB::table('users')->update(['password' => ...])`) hoặc mass update
(`User::where(...)->update([...])`) không đi qua cast, nên bạn phải tự `Hash::make()`.

### 4.4 Tự băm lại khi đăng nhập

Máy tính nhanh lên theo thời gian, nên cost cần tăng dần. Nhưng ta không thể băm lại mật khẩu cũ khi
không biết mật khẩu thô. Thời điểm duy nhất có mật khẩu thô là lúc user đăng nhập. Laravel tận dụng
đúng thời điểm đó: khi `rehash_on_login` là `true` (mặc định), `Auth::attempt()` sau khi xác nhận
mật khẩu đúng sẽ gọi `provider->rehashPasswordIfRequired()`. Hàm này dùng `Hash::needsRehash()`, nếu
cần thì băm lại và lưu (mục 3.3). Mô phỏng bằng PHP thuần:

```php
<?php
declare(strict_types=1);

// Mô phỏng "rehash khi đăng nhập": hash cũ cost 10, cấu hình hiện tại cost 12.
$stored = password_hash('correct horse', PASSWORD_BCRYPT, ['cost' => 10]);
echo substr($stored, 0, 7), "\n";                     // in ra: $2y$10$

$config = ['cost' => 12];
$input = 'correct horse';                             // user gõ khi đăng nhập

if (password_verify($input, $stored)) {
    // Chỉ lúc này ta mới có mật khẩu thô, nên chỉ lúc này mới băm lại được
    if (password_needs_rehash($stored, PASSWORD_BCRYPT, $config)) {
        $stored = password_hash($input, PASSWORD_BCRYPT, $config);
        echo "đã băm lại\n";                          // in ra: đã băm lại
    }
}
echo substr($stored, 0, 7), "\n";                     // in ra: $2y$12$

// Giới hạn 72 byte của bcrypt: phần sau byte thứ 72 bị bỏ qua
$a = str_repeat('x', 72) . 'AAA';
$b = str_repeat('x', 72) . 'BBB';
var_dump(password_verify($b, password_hash($a, PASSWORD_BCRYPT)));   // in ra: bool(true)
```

⚠️ Dòng cuối cho thấy bẫy 72 byte: bcrypt chỉ dùng 72 byte đầu của mật khẩu, nên hai mật khẩu chung
72 byte đầu được coi là một. Mật khẩu tiếng Việt có dấu tốn 2 tới 3 byte mỗi ký tự trong UTF-8, nên
72 byte có thể chỉ khoảng 24 tới 36 ký tự. Cách xử lý: đặt quy tắc validate độ dài tối đa (ví dụ
`max:72` tính theo ký tự chưa đủ chặt với chuỗi nhiều byte), đặt `BCRYPT_LIMIT`, hoặc dùng Argon2id
(không có giới hạn này).

### 4.5 Quy tắc độ mạnh mật khẩu

Validation rule `Illuminate\Validation\Rules\Password` (cú pháp validation ở
[Chương 25](25-laravel-request-validation-response.md)) giúp ép mật khẩu đủ mạnh:

```php
use Illuminate\Validation\Rules\Password;

$request->validate([
    'password' => ['required', 'confirmed', Password::min(12)->letters()->numbers()->uncompromised()],
]);

// Đặt quy tắc mặc định một lần trong AppServiceProvider::boot(), dùng lại bằng Password::defaults()
Password::defaults(fn () => $this->app->isProduction()
    ? Password::min(12)->uncompromised()
    : Password::min(8));
```

- `confirmed`: phải có field `password_confirmation` trùng giá trị.
- `uncompromised()`: kiểm tra mật khẩu có nằm trong các vụ lộ dữ liệu công khai không, qua dịch vụ
  Have I Been Pwned. Theo mã nguồn `NotPwnedVerifier`: Laravel tính SHA-1 của mật khẩu, chỉ gửi 5 ký
  tự hex đầu tới `https://api.pwnedpasswords.com/range/<5 ký tự>` (kèm header `Add-Padding: true`),
  nhận về danh sách phần đuôi các hash có cùng tiền tố rồi tự so ở server (kỹ thuật *k-anonymity*).
  Mật khẩu và hash đầy đủ không rời khỏi server. Cần kết nối mạng ra ngoài; nếu gọi API lỗi, rule này
  cho qua (coi như chưa bị lộ).

## 5. Quên mật khẩu (password reset)

### 5.1 Luồng nghiệp vụ

```
1. User bấm "Quên mật khẩu", nhập email           POST /forgot-password
2. Laravel tạo token ngẫu nhiên:
     - lưu HASH của token vào bảng password_reset_tokens (kèm email, created_at)
     - gửi link chứa token THÔ qua email
3. User mở email, bấm link                          GET  /reset-password/{token}?email=...
4. User nhập mật khẩu mới                           POST /reset-password (token, email, password)
5. Laravel kiểm tra: token khớp hash? còn hạn? → đổi mật khẩu, xoá token
```

Thành phần chịu trách nhiệm là *password broker*, truy cập qua facade `Password`. Broker dùng provider
cấu hình trong `config/auth.php`, khối `passwords` (mục 2.2), để tìm user.

### 5.2 Hai route xin link

```php
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Password;

Route::get('/forgot-password', fn () => view('auth.forgot-password'))
    ->middleware('guest')->name('password.request');

Route::post('/forgot-password', function (Request $request) {
    $request->validate(['email' => 'required|email']);

    $status = Password::sendResetLink($request->only('email'));

    return $status === Password::ResetLinkSent
        ? back()->with(['status' => __($status)])
        : back()->withErrors(['email' => __($status)]);
})->middleware('guest')->name('password.email');
```

`sendResetLink()` trả về một chuỗi trạng thái. Các giá trị (hằng trong
`Illuminate\Contracts\Auth\PasswordBroker`) là `passwords.sent`, `passwords.reset`, `passwords.user`
(không tìm thấy user), `passwords.token` (token sai hoặc hết hạn), `passwords.throttled` (xin link quá
nhanh). Chúng là key dịch trong file ngôn ngữ `lang/<locale>/passwords.php`.

⚠️ Đoạn code mẫu trên báo lỗi khác nhau cho "email không tồn tại" (`passwords.user`) và "đã gửi"
(`passwords.sent`), tức là để lộ email nào đã đăng ký. Nếu điều này quan trọng với ứng dụng của bạn,
trả cùng một thông báo trung tính cho mọi trường hợp ("Nếu email tồn tại, chúng tôi đã gửi link").

### 5.3 Hai route đặt mật khẩu mới

```php
use App\Models\User;
use Illuminate\Auth\Events\PasswordReset;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

Route::get('/reset-password/{token}', fn (string $token) => view('auth.reset-password', ['token' => $token]))
    ->middleware('guest')->name('password.reset');

Route::post('/reset-password', function (Request $request) {
    $request->validate([
        'token' => 'required',
        'email' => 'required|email',
        'password' => 'required|min:8|confirmed',
    ]);

    $status = Password::reset(
        $request->only('email', 'password', 'password_confirmation', 'token'),
        function (User $user, string $password): void {
            $user->forceFill(['password' => Hash::make($password)])
                ->setRememberToken(Str::random(60));     // vô hiệu mọi cookie "remember me" cũ
            $user->save();

            event(new PasswordReset($user));
        }
    );

    return $status === Password::PasswordReset
        ? redirect()->route('login')->with('status', __($status))
        : back()->withErrors(['email' => [__($status)]]);
})->middleware('guest')->name('password.update');
```

Closure chỉ được gọi khi token hợp lệ. Bên trong, ngoài đổi mật khẩu, mẫu của Laravel đổi luôn
`remember_token`: kẻ đã chiếm tài khoản bằng cookie "remember me" sẽ bị đá ra.

### 5.4 Bên trong: token được lưu thế nào

Đọc `DatabaseTokenRepository` của Laravel 13:

- Token thô = `hash_hmac('sha256', Str::random(40), <APP_KEY>)`, tức một chuỗi hex 64 ký tự.
- Trước khi tạo token mới cho một email, các token cũ của email đó bị xoá. Mỗi email chỉ có một token
  còn hiệu lực.
- Cột `token` trong DB lưu `Hash::make($token)` (bcrypt), không lưu token thô. Ai đọc trộm được bảng
  `password_reset_tokens` cũng không có link reset dùng được.
- Kiểm tra: tìm dòng theo email, kiểm `created_at + expire` chưa qua, rồi `Hash::check()`.
- `Password::reset()` cũng được bọc trong `Timebox`, giống `attempt()`.

Mô phỏng ý tưởng:

```php
<?php
declare(strict_types=1);

// Mô phỏng password reset token: gửi bản thô qua email, DB chỉ giữ hash.
$plainToken = hash_hmac('sha256', bin2hex(random_bytes(20)), 'APP_KEY');  // Laravel: hash_hmac('sha256', Str::random(40), key)
$row = [
    'email' => 'an@example.com',
    'token' => password_hash($plainToken, PASSWORD_BCRYPT),   // Laravel: Hash::make($token)
    'created_at' => time(),
];

echo strlen($plainToken), "\n";                                 // in ra: 64
echo substr($row['token'], 0, 4), "\n";                         // in ra: $2y$

$expireSeconds = 60 * 60;                                       // 'expire' => 60 (phút)
$isValid = fn (string $t, int $now): bool =>
    $now < $row['created_at'] + $expireSeconds && password_verify($t, $row['token']);

var_dump($isValid($plainToken, time()));                        // in ra: bool(true)
var_dump($isValid('doan-bua', time()));                         // in ra: bool(false)
var_dump($isValid($plainToken, time() + 3601));                 // in ra: bool(false)
```

Ngoài driver `database`, tài liệu Laravel 13 có driver `cache` (không cần bảng riêng, key là SHA-256
của email). Nên dùng một cache store riêng để `cache:clear` không xoá mất token đang chờ.

Token hết hạn vẫn nằm trong bảng; dọn bằng lệnh `php artisan auth:clear-resets`, có thể đặt lịch chạy
định kỳ (scheduler ở [Chương 29](29-laravel-queue-event-schedule-cache.md)).

### 5.5 Cạm bẫy: Host header và link reset

Link reset trong email được dựng từ URL của request hiện tại. Tài liệu Laravel cảnh báo: mặc định
Laravel trả lời mọi request bất kể header `Host`, và dùng `Host` để dựng URL tuyệt đối. Kẻ tấn công
gửi `POST /forgot-password` với email nạn nhân và `Host: evil.example`; nếu server chấp nhận, email
gửi cho nạn nhân chứa link tới `evil.example/reset-password/<token thật>`. Nạn nhân bấm vào là token
rơi vào tay kẻ tấn công (*password reset poisoning*).

Cách chặn: cấu hình web server (Nginx) chỉ chuyển request có hostname đúng vào ứng dụng, hoặc dùng
`$middleware->trustHosts(...)` trong `bootstrap/app.php`. Đặt `APP_URL` đúng cũng quan trọng cho các
link tạo ngoài request (như trong queue).

## 6. Xác minh email (email verification)

### 6.1 Để làm gì

Người đăng ký có thể gõ nhầm email, hoặc cố tình dùng email của người khác. Xác minh email bắt user
bấm một link gửi tới hộp thư để chứng minh họ sở hữu địa chỉ đó. Dữ liệu lưu ở cột
`users.email_verified_at`: `NULL` là chưa xác minh.

### 6.2 Bật tính năng

1. Cho model cài interface `MustVerifyEmail`:

   ```php
   use Illuminate\Contracts\Auth\MustVerifyEmail;

   class User extends Authenticatable implements MustVerifyEmail
   {
       use Notifiable;
       // ...
   }
   ```

2. Khi đăng ký thành công, phát event `Registered`. Laravel tự đăng ký listener
   `SendEmailVerificationNotification` cho event này, listener gửi email nếu user cài
   `MustVerifyEmail` và chưa xác minh. Starter kit đã phát event này; tự viết thì phải nhớ:

   ```php
   use Illuminate\Auth\Events\Registered;

   event(new Registered($user));
   ```

3. Khai báo ba route với đúng tên:

```php
use Illuminate\Foundation\Auth\EmailVerificationRequest;
use Illuminate\Http\Request;

// Trang nhắc "hãy kiểm tra hộp thư". Middleware verified redirect về route tên này.
Route::get('/email/verify', fn () => view('auth.verify-email'))
    ->middleware('auth')->name('verification.notice');

// Link trong email trỏ vào đây
Route::get('/email/verify/{id}/{hash}', function (EmailVerificationRequest $request) {
    $request->fulfill();          // đặt email_verified_at, phát event Verified
    return redirect('/home');
})->middleware(['auth', 'signed'])->name('verification.verify');

// Gửi lại email
Route::post('/email/verification-notification', function (Request $request) {
    $request->user()->sendEmailVerificationNotification();
    return back()->with('message', 'Verification link sent!');
})->middleware(['auth', 'throttle:6,1'])->name('verification.send');
```

4. Bảo vệ các route chỉ dành cho user đã xác minh bằng middleware `verified` (alias của
   `EnsureEmailIsVerified`), thường đi cùng `auth`:

   ```php
   Route::get('/billing', [BillingController::class, 'index'])->middleware(['auth', 'verified']);
   ```

### 6.3 Link xác minh an toàn nhờ đâu

Link trong email có dạng `/email/verify/{id}/{hash}?expires=...&signature=...`, sinh bởi
`URL::temporarySignedRoute()`. Theo mã nguồn notification `VerifyEmail`: `id` là khoá chính user,
`hash` là `sha1(email)`, link hết hạn sau `auth.verification.expire` phút (mặc định 60).

Có ba lớp kiểm tra:

| Lớp | Ai làm | Chặn được gì |
|---|---|---|
| Chữ ký (*signature*) | Middleware `signed` | Sửa bất kỳ phần nào của URL (đổi id, đổi hash, kéo dài `expires`) |
| Hạn dùng | Middleware `signed` (tham số `expires`) | Dùng link cũ |
| `id` khớp user đang đăng nhập, `hash` khớp `sha1(email)` hiện tại | `EmailVerificationRequest::authorize()` (dùng `hash_equals`) | Mở link của người khác khi đang đăng nhập tài khoản mình; dùng link cũ sau khi đã đổi email |

Chữ ký là HMAC-SHA256 của URL, khoá là `APP_KEY`. Không có khoá thì không làm giả được chữ ký. Mô
phỏng ý tưởng (Laravel chi tiết hơn, nhưng nguyên lý giống):

```php
<?php
declare(strict_types=1);

// Mô phỏng ý tưởng signed URL (Laravel: URL::temporarySignedRoute + middleware signed).
const APP_KEY = 'khoa-bi-mat-cua-ung-dung';

function signedUrl(string $path, array $params, int $expiresAt): string
{
    $params['expires'] = $expiresAt;
    ksort($params);
    $url = $path . '?' . http_build_query($params);
    return $url . '&signature=' . hash_hmac('sha256', $url, APP_KEY);
}

function hasValidSignature(string $fullUrl, int $now): bool
{
    $parts = parse_url($fullUrl);
    parse_str($parts['query'] ?? '', $q);
    $signature = (string) ($q['signature'] ?? '');
    unset($q['signature']);
    ksort($q);
    $original = $parts['path'] . '?' . http_build_query($q);
    return hash_equals(hash_hmac('sha256', $original, APP_KEY), $signature)
        && (int) ($q['expires'] ?? 0) > $now;
}

$now = 1_800_000_000;
$url = signedUrl('/email/verify/42/' . sha1('an@example.com'), [], $now + 3600);

var_dump(hasValidSignature($url, $now));                                  // in ra: bool(true)
var_dump(hasValidSignature(str_replace('/42/', '/43/', $url), $now));     // in ra: bool(false)  (sửa id)
var_dump(hasValidSignature($url, $now + 7200));                           // in ra: bool(false)  (hết hạn)
```

⚠️ Cạm bẫy:

- Quên phát `Registered` khi tự viết đăng ký: không ai nhận được email xác minh, và cũng không có lỗi
  nào báo.
- Gắn `verified` mà không gắn `auth`: middleware `verified` không có user để kiểm tra. Luôn dùng cặp
  `['auth', 'verified']`.
- Cho user đổi email mà không đặt lại `email_verified_at = null` và gửi lại link: user có thể đổi
  sang email chưa xác minh mà vẫn giữ trạng thái "đã xác minh".
- Link xác minh trong email cũng chịu bẫy Host header như link reset (mục 5.5).

## 7. Starter kit: không tự viết lại mọi thứ

### 7.1 Starter kit là gì

Mục 3 tới 6 cho thấy một hệ thống đăng nhập đầy đủ cần rất nhiều route, controller, view: login,
logout, register, quên mật khẩu, đặt lại mật khẩu, xác minh email, xác nhận mật khẩu, 2FA, rate
limit. *Starter kit* là bộ khung ứng dụng có sẵn tất cả những thứ đó. Code được sinh vào chính dự án
của bạn (không nằm trong `vendor/`), nên bạn sở hữu và sửa thoải mái.

Tạo dự án với starter kit bằng Laravel installer; lệnh sẽ hỏi bạn chọn kit nào:

```bash
# chạy ở thư mục muốn chứa dự án, cần PHP, Composer, Node.js
composer global require laravel/installer
laravel new my-app
cd my-app
npm install && npm run build
composer run dev
```

### 7.2 Các kit chính thức (Laravel 13)

| Kit | Frontend | Thư viện UI |
|---|---|---|
| React | Inertia + React 19 + TypeScript | shadcn/ui, Tailwind |
| Vue | Inertia + Vue (Composition API) + TypeScript | shadcn-vue, Tailwind |
| Svelte | Inertia + Svelte 5 + TypeScript | shadcn-svelte, Tailwind |
| Livewire | Livewire (UI viết bằng PHP + Blade) | Flux UI, Tailwind |

Mỗi kit có thêm biến thể dùng *WorkOS AuthKit* (dịch vụ bên ngoài) cho đăng nhập bằng Google,
Microsoft, GitHub, Apple, passkey, "magic link" qua email và SSO. Biến thể mặc định dùng hệ thống xác
thực có sẵn của Laravel.

Về backend, tài liệu Laravel 13 nói mọi starter kit dùng *Laravel Fortify* để xử lý xác thực. Fortify
là một thư viện xác thực *headless* (chỉ có route, controller, logic, không có giao diện). Nó đăng ký
các route như `/login`, `/logout`, `/register`, `/forgot-password`, `/reset-password`, `/email/verify`,
`/user/confirm-password`, `/two-factor-challenge` tuỳ theo tính năng bật trong `config/fortify.php`:

```php
use Laravel\Fortify\Features;

'features' => [
    Features::registration(),
    Features::resetPasswords(),
    Features::emailVerification(),
    Features::twoFactorAuthentication([
        'confirm' => true,
        'confirmPassword' => true,
    ]),
],
```

Logic tạo user và đặt lại mật khẩu nằm trong `app/Actions/Fortify/` (`CreateNewUser.php`,
`ResetUserPassword.php`, `PasswordValidationRules.php`) để bạn sửa. Rate limit login khai báo trong
`FortifyServiceProvider` bằng `RateLimiter::for('login', ...)`.

### 7.3 Lịch sử tên gọi để đọc code cũ

Bạn sẽ gặp nhiều dự án dùng các kit đời trước:

- *Laravel Breeze*: kit tối giản (Blade, hoặc Inertia React/Vue), controller xác thực sinh thẳng vào
  `app/Http/Controllers/Auth`.
- *Laravel Jetstream*: kit đầy đủ hơn (team, 2FA, API token), dựa trên Fortify.
- *laravel/ui*: thế hệ cũ hơn nữa, dùng Bootstrap.

Theo ghi chú phát hành Laravel 12: với các starter kit mới, Breeze và Jetstream không nhận thêm cập
nhật. Dự án đang chạy Breeze/Jetstream vẫn hoạt động bình thường vì code đã nằm trong dự án.

### 7.4 Có nên dùng starter kit

Tài liệu Laravel khuyên: kể cả khi không dùng starter kit cho dự án thật, cài thử một kit là cách tốt
để học cách Laravel làm xác thực, vì toàn bộ code nằm ngay trong dự án. Lợi ích thực tế khác: những
chi tiết dễ quên (rate limit, regenerate session, `intended`, thông báo lỗi trung tính, 2FA) đã được
làm sẵn và được nhiều người dùng kiểm chứng. Tự viết chỉ khi có lý do rõ ràng, và khi đó hãy đối
chiếu với code của kit.

## 8. Xác thực API với Sanctum

### 8.1 Vì sao API cần cách khác

Session dựa vào cookie, mà cookie là cơ chế của trình duyệt. Một app mobile, một script cron trên máy
khác, hay một hệ thống đối tác gọi API của bạn thì không có trình duyệt. Tài liệu Laravel mô tả: dịch
vụ từ xa gửi một *API token* kèm mỗi request; ứng dụng so token với bảng token hợp lệ và coi request
được thực hiện bởi user sở hữu token đó.

Token thường gửi trong header theo chuẩn *Bearer*:

```
GET /api/orders HTTP/1.1
Host: shop.example
Accept: application/json
Authorization: Bearer 7|Xk2...a9f
```

"Bearer" nghĩa là "người cầm": ai cầm token thì được coi là chủ token. Vì vậy token phải được đối
xử như mật khẩu: chỉ gửi qua HTTPS, không ghi vào log, không đặt trong URL.

### 8.2 Sanctum: một gói, hai chế độ

*Laravel Sanctum* là gói xác thực API được Laravel khuyên dùng cho phần lớn ứng dụng. Nó giải hai bài
toán tách biệt:

| | Chế độ API token | Chế độ SPA (cookie) |
|---|---|---|
| Dành cho | Mobile app, script, bên thứ ba, "API key" kiểu GitHub | SPA của chính bạn (React/Vue/Next.js...) gọi API Laravel |
| Mang danh tính bằng | Header `Authorization: Bearer <token>` | Session cookie như web thường |
| Lưu ở server | Bảng `personal_access_tokens` (hash SHA-256) | Session |
| CSRF | Không cần (trình duyệt không tự gửi header Authorization) | Có, bắt buộc |
| JavaScript đọc được thông tin xác thực? | Có nếu SPA giữ token trong JS (nên tránh) | Không: cookie session là `HttpOnly` |

Cài đặt (Laravel 11 trở lên không có sẵn `routes/api.php` và Sanctum):

```bash
# chạy ở thư mục gốc dự án
php artisan install:api
```

Lệnh này cài Sanctum, tạo `routes/api.php` và migration bảng `personal_access_tokens`.

Bảo vệ route bằng guard `sanctum`:

```php
// routes/api.php
Route::get('/user', fn (Request $request) => $request->user())->middleware('auth:sanctum');
```

Guard `sanctum` theo mã nguồn (`Laravel\Sanctum\Guard`) làm theo thứ tự:

1. Thử các guard trong `config('sanctum.guard')` (mặc định `['web']`). Nếu request có session đăng
   nhập hợp lệ thì dùng luôn user đó, gắn cho nó một `TransientToken`.
2. Nếu không, đọc Bearer token trong header, tìm trong bảng `personal_access_tokens`, kiểm tra hạn
   dùng, rồi trả user sở hữu token.

Nhờ thứ tự này, cùng một route `auth:sanctum` phục vụ được cả SPA (cookie) lẫn mobile (token).

### 8.3 Chế độ API token

Model `User` cần trait `HasApiTokens`:

```php
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;
}
```

Phát token cho app mobile: đổi email + mật khẩu + tên thiết bị lấy token.

```php
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\ValidationException;

Route::post('/sanctum/token', function (Request $request) {
    $request->validate([
        'email' => 'required|email',
        'password' => 'required',
        'device_name' => 'required',
    ]);

    $user = User::where('email', $request->email)->first();

    if (! $user || ! Hash::check($request->password, $user->password)) {
        throw ValidationException::withMessages([
            'email' => ['The provided credentials are incorrect.'],
        ]);
    }

    return $user->createToken($request->device_name)->plainTextToken;
});
```

⚠️ Route này là một form đăng nhập. Nó cần rate limit giống `/login` (mục 3.9), nếu không sẽ thành
cửa dò mật khẩu không giới hạn.

Bên trong `createToken()` (đọc mã nguồn Sanctum 4.x):

- Token thô = tiền tố tuỳ chọn (`SANCTUM_TOKEN_PREFIX`, mặc định rỗng) + 40 ký tự ngẫu nhiên + 8 ký tự
  checksum CRC32 của phần ngẫu nhiên.
- Bảng chỉ lưu `hash('sha256', token thô)`.
- Giá trị trả về cho client (`plainTextToken`) có dạng `<id dòng>|<token thô>`. Phần id giúp tìm đúng
  dòng bằng khoá chính, sau đó so hash bằng `hash_equals`.
- Token thô chỉ xem được đúng lúc tạo. Mất thì phát token mới.

Vì sao token dùng SHA-256 mà mật khẩu phải dùng bcrypt? Mật khẩu do người đặt, ngắn, dễ đoán, nên cần
thuật toán chậm để làm khó việc thử. Token là 40 ký tự ngẫu nhiên do máy sinh, không thể đoán bằng vét
cạn, nên một hash nhanh là đủ, và hash nhanh thì kiểm tra ở mỗi request không tốn CPU.

Mô phỏng:

```php
<?php
declare(strict_types=1);

// Mô phỏng cách Sanctum phát và kiểm tra personal access token (rút gọn).
/** @var array<int, array{token: string, abilities: list<string>}> $table  bảng personal_access_tokens */
$table = [];

function randomString(int $len): string
{
    $chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    $s = '';
    for ($i = 0; $i < $len; $i++) {
        $s .= $chars[random_int(0, strlen($chars) - 1)];
    }
    return $s;
}

/** @param list<string> $abilities */
function createToken(array &$table, array $abilities): string
{
    $entropy = randomString(40);
    $plain = $entropy . hash('crc32b', $entropy);       // 40 ký tự ngẫu nhiên + 8 ký tự checksum
    $id = count($table) + 1;
    $table[$id] = ['token' => hash('sha256', $plain), 'abilities' => $abilities];  // DB chỉ giữ SHA-256
    return $id . '|' . $plain;                           // trả cho client đúng MỘT lần
}

/** @return array{token: string, abilities: list<string>}|null */
function findToken(array $table, string $bearer): ?array
{
    [$id, $plain] = explode('|', $bearer, 2) + [1 => ''];
    $row = $table[(int) $id] ?? null;
    return ($row !== null && hash_equals($row['token'], hash('sha256', $plain))) ? $row : null;
}

function can(array $row, string $ability): bool
{
    return in_array('*', $row['abilities'], true) || in_array($ability, $row['abilities'], true);
}

$t = createToken($table, ['orders:read']);
echo strlen(explode('|', $t)[1]), "\n";                  // in ra: 48
echo strlen($table[1]['token']), "\n";                   // in ra: 64  (hex SHA-256)

$row = findToken($table, $t);
var_dump($row !== null);                                 // in ra: bool(true)
var_dump(can($row, 'orders:read'));                      // in ra: bool(true)
var_dump(can($row, 'orders:delete'));                    // in ra: bool(false)
var_dump(findToken($table, '1|doan-bua') === null);      // in ra: bool(true)
```

*Abilities* (khả năng của token) giống *scope* của OAuth: giới hạn token chỉ làm được một số việc.

```php
// Tạo token chỉ được đọc đơn hàng; tham số thứ 3 là thời điểm hết hạn riêng của token này
$token = $user->createToken('bao-cao', ['orders:read'], now()->addWeek())->plainTextToken;

// Kiểm trong code
if ($request->user()->tokenCan('orders:read')) { /* ... */ }

// Hoặc bằng middleware (phải tự đăng ký alias trong bootstrap/app.php)
$middleware->alias([
    'abilities' => \Laravel\Sanctum\Http\Middleware\CheckAbilities::class,      // phải có ĐỦ
    'ability' => \Laravel\Sanctum\Http\Middleware\CheckForAnyAbility::class,    // có MỘT là được
]);
Route::get('/orders', [OrderController::class, 'index'])
    ->middleware(['auth:sanctum', 'abilities:orders:read']);
```

Token mặc định khi không truyền abilities là `['*']`, nghĩa là làm được mọi thứ.

⚠️ Với request đến từ SPA qua cookie, `tokenCan()` luôn trả `true` (user được gắn `TransientToken`).
Tài liệu Sanctum giải thích: để bạn luôn gọi được `tokenCan()` trong policy mà không cần biết request
đến từ đâu. Hệ quả: ability của token không bao giờ là lớp phân quyền duy nhất. Policy vẫn phải kiểm
quyền của user, ví dụ:

```php
return $request->user()->id === $server->user_id
    && $request->user()->tokenCan('server:update');
```

Thu hồi và hết hạn:

```php
$user->tokens()->delete();                                   // thu hồi mọi token
$request->user()->currentAccessToken()->delete();            // thu hồi token đang dùng (logout trên mobile)
$user->tokens()->where('id', $tokenId)->delete();            // thu hồi một token cụ thể
```

- ⚠️ Mặc định token không bao giờ hết hạn (`'expiration' => null` trong `config/sanctum.php`). Đặt số
  phút ở đó, hoặc truyền thời điểm hết hạn khi tạo từng token.
- Token hết hạn vẫn nằm trong bảng; dọn bằng `php artisan sanctum:prune-expired --hours=24` đặt trong
  scheduler.
- Khi user đổi mật khẩu, token cũ không tự bị thu hồi. Nếu nghiệp vụ cần, tự xoá trong action đổi mật
  khẩu.

### 8.4 Chế độ SPA (cookie)

Tài liệu Sanctum nói rõ: không dùng API token cho SPA của chính bạn. Với SPA, Sanctum không dùng token
nào cả mà dùng session cookie của Laravel. Lợi ích: có CSRF protection, có session, và thông tin xác
thực không bị lộ qua XSS (JavaScript không đọc được cookie `HttpOnly`; ngược lại token để trong
`localStorage` thì bất kỳ script XSS nào cũng đọc được).

Điều kiện và cấu hình:

1. SPA và API phải chung *top-level domain*; được khác subdomain (`app.shop.vn` và `api.shop.vn`).
   Request nên gửi header `Accept: application/json` và `Referer` hoặc `Origin`.
2. Khai domain của SPA trong `stateful` ở `config/sanctum.php` (biến `SANCTUM_STATEFUL_DOMAINS`). Có
   cổng thì ghi cả cổng (`localhost:3000`). Chỉ request từ các domain này mới được xác thực bằng cookie.
3. Trong `bootstrap/app.php` gọi `$middleware->statefulApi();` để group `api` chạy được session cho
   các request từ SPA.
4. CORS: `supports_credentials` = `true` trong `config/cors.php` (publish bằng
   `php artisan config:publish cors`). Client bật `withCredentials` và `withXSRFToken` (Axios).
5. `config/session.php`: `'domain' => '.shop.vn'` để cookie dùng chung giữa các subdomain.

Luồng đăng nhập:

```
SPA (app.shop.vn)                                  Laravel (api.shop.vn)
  │ GET /sanctum/csrf-cookie                          │
  │──────────────────────────────────────────────────►│
  │ Set-Cookie: XSRF-TOKEN=...; laravel_session=...   │
  │◄──────────────────────────────────────────────────│
  │ POST /login  (header X-XSRF-TOKEN = giá trị cookie │
  │               XSRF-TOKEN đã URL-decode)            │
  │──────────────────────────────────────────────────►│ Auth::attempt() bằng guard web
  │ Set-Cookie: laravel_session=<ID mới>              │
  │◄──────────────────────────────────────────────────│
  │ GET /api/user  (cookie tự gửi kèm)                │
  │──────────────────────────────────────────────────►│ auth:sanctum → guard web → user
```

Route `/login` có thể tự viết (mục 3.2) hoặc dùng Fortify, nhưng phải dùng xác thực session chuẩn
(guard `web`). Khi session hết hạn, request sau nhận 401 hoặc 419 (CSRF token hết hạn); SPA cần đưa
user về trang đăng nhập.

⚠️ Lỗi cấu hình hay gặp với SPA mode: thiếu domain trong `stateful` (request bị coi như API token và
trả 401), quên cổng, CORS không bật credentials (trình duyệt không gửi cookie), `session.domain` sai
(cookie không dùng chung được giữa subdomain), SPA và API khác top-level domain (cookie không gửi được).

## 9. Passport và OAuth2: khi nào cần

### 9.1 OAuth2 giải bài toán gì

Hãy nghĩ tới nút "Đăng nhập bằng Google" hay "Cho phép ứng dụng X đọc lịch Google của bạn". Ứng dụng
X là bên thứ ba: nó không được biết mật khẩu Google của bạn, nhưng cần một quyền hạn chế để thay bạn
gọi API Google. *OAuth2* (RFC 6749) là chuẩn cho bài toán *uỷ quyền* (*delegated authorization*) này.
Các vai trò:

| Vai trò OAuth2 | Ví dụ |
|---|---|
| *Resource owner* | Bạn, chủ tài khoản |
| *Client* | Ứng dụng X muốn truy cập thay bạn |
| *Authorization server* | Máy chủ cấp token (Google) |
| *Resource server* | API chứa dữ liệu (Google Calendar API) |

Luồng phổ biến nhất là *authorization code* (kèm *PKCE* cho client không giữ được bí mật như SPA,
mobile): client chuyển bạn tới authorization server, bạn đăng nhập và bấm "Cho phép", server trả về một
mã tạm (*authorization code*), client đổi mã đó lấy *access token* (thường kèm *refresh token* để xin
access token mới khi hết hạn).

### 9.2 Passport

*Laravel Passport* biến ứng dụng Laravel của bạn thành một OAuth2 authorization server đầy đủ, xây
trên thư viện `league/oauth2-server`. Cài bằng `php artisan install:api --passport`; lệnh tạo bảng cho
client và token, và tạo khoá mã hoá để ký access token. Guard dùng driver `passport`, route bảo vệ bằng
`auth:api`.

Theo tài liệu Passport cho Laravel 13:

- Các grant được hỗ trợ: authorization code, authorization code với PKCE, device authorization (cho TV,
  máy chơi game: thiết bị hiện mã, user xác nhận trên điện thoại), client credentials (máy gọi máy, không
  có user), personal access token.
- Password grant và implicit grant phải tự bật (`Passport::enablePasswordGrant()`,
  `Passport::enableImplicitGrant()`), và tài liệu ghi rõ không còn khuyên dùng hai grant này.
- Access token mặc định sống một năm; chỉnh bằng `Passport::tokensExpireIn()`,
  `refreshTokensExpireIn()`, `personalAccessTokensExpireIn()`.

### 9.3 Chọn gì

| Tình huống | Chọn |
|---|---|
| Web truyền thống (Blade, Livewire, Inertia) | Session có sẵn (starter kit) |
| SPA của chính bạn, chung top-level domain | Sanctum SPA mode |
| Mobile app của chính bạn | Sanctum API token |
| Script, cron, đối tác cần "API key" | Sanctum API token với abilities |
| Bên thứ ba xin quyền truy cập thay user của bạn ("Đăng nhập bằng <ứng dụng của bạn>") | Passport (OAuth2) |
| MCP server cho AI client | Passport (tài liệu Laravel 13 nói MCP client thường xác thực bằng OAuth) |
| Bạn muốn user đăng nhập bằng Google/GitHub | Đây là bạn làm *client* OAuth, không phải server: dùng *Laravel Socialite*, không phải Passport |

Tài liệu Laravel khuyên ưu tiên Sanctum khi có thể; chỉ dùng Passport khi thực sự cần các tính năng
của chuẩn OAuth2.

⚠️ Sanctum không phải OAuth2 server: không có authorization code flow, không có refresh token, không
có khái niệm "ứng dụng bên thứ ba xin quyền thay user". Ngược lại, dùng Passport cho SPA của chính
mình là thêm độ phức tạp không cần thiết.

⚠️ Về JWT: nhiều bài hướng dẫn trên mạng dùng gói bên thứ ba để phát JWT cho API Laravel. JWT tự chứa
thông tin và không cần tra DB, nhưng đổi lại khó thu hồi trước hạn. Token của Sanctum tra DB ở mỗi
request nên thu hồi tức thì bằng cách xoá dòng. Với phần lớn ứng dụng, chi phí một query theo khoá
chính là không đáng kể so với lợi ích thu hồi được.

## 10. Phân quyền bằng Gate

### 10.1 Gate là gì

Từ mục này ta sang câu hỏi thứ hai: "user này được làm việc này không?". Laravel cung cấp hai công cụ:

- *Gate*: một closure có tên, trả lời một câu hỏi quyền. Hợp với quyền không gắn với model cụ thể, ví
  dụ "được vào trang quản trị", "được sửa cấu hình hệ thống".
- *Policy*: một class gom mọi quyền liên quan tới một model, ví dụ `PostPolicy` có `view`, `update`,
  `delete` cho `Post` (mục 11).

Tài liệu Laravel so sánh: gate giống route closure, policy giống controller. Ứng dụng thật thường dùng
cả hai, phần lớn là policy.

### 10.2 Định nghĩa và kiểm tra gate

Định nghĩa trong `AppServiceProvider::boot()`:

```php
use App\Models\Post;
use App\Models\User;
use Illuminate\Support\Facades\Gate;

public function boot(): void
{
    Gate::define('update-post', function (User $user, Post $post): bool {
        return $user->id === $post->user_id;
    });

    Gate::define('access-admin', fn (User $user): bool => $user->role === 'admin');
}
```

Tham số đầu luôn là user hiện tại; Laravel tự truyền, bạn không truyền. Các tham số sau là những gì
bạn đưa vào khi kiểm tra:

```php
if (Gate::allows('update-post', $post)) { /* được */ }
if (Gate::denies('update-post', $post)) { abort(403); }

Gate::authorize('update-post', $post);   // không được thì ném AuthorizationException → HTTP 403

Gate::any(['update-post', 'delete-post'], $post);   // có ít nhất một quyền
Gate::none(['update-post', 'delete-post'], $post);  // không có quyền nào

Gate::forUser($otherUser)->allows('update-post', $post);   // kiểm cho user khác user hiện tại

Gate::check('create-post', [$category, $pinned]);   // nhiều tham số: truyền array
```

### 10.3 Trả về lý do và đổi status code

Gate có thể trả object `Illuminate\Auth\Access\Response` thay cho bool để kèm thông báo:

```php
use Illuminate\Auth\Access\Response;

Gate::define('edit-settings', fn (User $user): Response => $user->isAdmin
    ? Response::allow()
    : Response::deny('You must be an administrator.'));

$response = Gate::inspect('edit-settings');      // lấy object Response đầy đủ
if (! $response->allowed()) {
    echo $response->message();
}

Gate::authorize('edit-settings');                // thông báo trên đi theo exception vào HTTP response
```

`Gate::allows()` vẫn chỉ trả bool. Muốn trả 404 thay vì 403 (giấu luôn việc tài nguyên tồn tại):
`Response::denyWithStatus(404)` hoặc gọn hơn `Response::denyAsNotFound()`.

### 10.4 `before` và `after`: chặn đầu và chặn cuối

`Gate::before()` chạy trước mọi kiểm tra. Mã nguồn `Gate::raw()` cho thấy thứ tự:

```
1. Chạy lần lượt các callback before. Callback nào trả giá trị KHÁC null → dùng làm kết quả, dừng.
2. Nếu vẫn null: chạy gate/policy tương ứng.
3. Chạy các callback after. Kết quả của after chỉ được dùng nếu bước 1-2 cho ra null.
```

Mẫu dùng phổ biến: cho super admin mọi quyền.

```php
Gate::before(function (User $user, string $ability): ?bool {
    return $user->isAdministrator() ? true : null;   // null: để gate/policy tự quyết
});
```

⚠️ Lỗi kinh điển: viết `return $user->isAdministrator();`. Với user thường, callback trả `false`,
mà `false` khác `null`, nên user thường bị từ chối mọi quyền, kể cả sửa bài của chính mình. Mô phỏng
thứ tự đánh giá để thấy tận mắt:

```php
<?php
declare(strict_types=1);

// Mô phỏng thu nhỏ thứ tự đánh giá của Gate Laravel (KHÔNG phải code Laravel thật).

final class User
{
    public function __construct(public readonly int $id, public readonly bool $isAdmin) {}
}

final class Post
{
    public function __construct(public readonly int $id, public readonly int $userId) {}
}

final class MiniGate
{
    /** @var array<string, Closure> */
    private array $abilities = [];
    /** @var list<Closure> */
    private array $before = [];

    public function define(string $ability, Closure $cb): void { $this->abilities[$ability] = $cb; }
    public function before(Closure $cb): void { $this->before[] = $cb; }

    public function allows(?User $user, string $ability, mixed ...$args): bool
    {
        if ($user === null) {
            return false;                          // Laravel: khách bị từ chối, trừ khi khai ?User
        }
        foreach ($this->before as $cb) {
            $result = $cb($user, $ability);
            if ($result !== null) {
                return (bool) $result;             // khác null là CHỐT luôn, không xét tiếp
            }
        }
        $cb = $this->abilities[$ability] ?? null;
        return $cb !== null && (bool) $cb($user, ...$args);   // ability không tồn tại → false
    }
}

$owner = new User(1, false);
$other = new User(2, false);
$admin = new User(3, true);
$post = new Post(10, 1);

// Cách ĐÚNG: before trả true hoặc null
$gate = new MiniGate();
$gate->define('update-post', fn (User $u, Post $p): bool => $u->id === $p->userId);
$gate->before(fn (User $u, string $ability): ?bool => $u->isAdmin ? true : null);

var_dump($gate->allows($owner, 'update-post', $post));   // in ra: bool(true)
var_dump($gate->allows($other, 'update-post', $post));   // in ra: bool(false)
var_dump($gate->allows($admin, 'update-post', $post));   // in ra: bool(true)
var_dump($gate->allows(null, 'update-post', $post));     // in ra: bool(false)

// Cách SAI: before trả bool cho mọi user
$bad = new MiniGate();
$bad->define('update-post', fn (User $u, Post $p): bool => $u->id === $p->userId);
$bad->before(fn (User $u, string $ability): bool => $u->isAdmin);

var_dump($bad->allows($owner, 'update-post', $post));    // in ra: bool(false)  ← chủ bài cũng bị chặn!
```

`Gate::after()` hữu ích để ghi log mọi quyết định phân quyền; nó chỉ đổi được kết quả khi gate hoặc
policy trả `null`.

Kiểm tra nhanh không cần định nghĩa gate: `Gate::allowIf(fn (User $u) => $u->isAdministrator())` và
`Gate::denyIf(fn (User $u) => $u->banned())`. Không được thì ném `AuthorizationException`. Lưu ý
dạng inline này không chạy callback `before`/`after`.

### 10.5 Khách (chưa đăng nhập)

Mặc định mọi gate và policy tự trả `false` khi không có user đăng nhập, closure của bạn không hề được
gọi. Muốn khách cũng được xét (ví dụ "ai cũng xem được bài đã xuất bản"), khai tham số user là
nullable:

```php
Gate::define('view-post', fn (?User $user, Post $post): bool =>
    $post->published || $user?->id === $post->user_id);
```

## 11. Phân quyền bằng Policy

### 11.1 Tạo policy

```bash
# chạy ở thư mục gốc dự án
php artisan make:policy PostPolicy --model=Post
```

Với `--model`, file sinh ra có sẵn các method `viewAny`, `view`, `create`, `update`, `delete`,
`restore`, `forceDelete`. Ví dụ hoàn chỉnh:

```php
<?php
declare(strict_types=1);

namespace App\Policies;

use App\Models\Post;
use App\Models\User;
use Illuminate\Auth\Access\Response;

final class PostPolicy
{
    // Chạy trước mọi method của policy này (khi method tương ứng tồn tại)
    public function before(User $user, string $ability): ?bool
    {
        return $user->isAdministrator() ? true : null;
    }

    // Danh sách: ai đăng nhập cũng xem được
    public function viewAny(User $user): bool
    {
        return true;
    }

    // Xem một bài: bài đã xuất bản, hoặc là tác giả. Khách cũng được xét nhờ ?User.
    public function view(?User $user, Post $post): bool
    {
        return $post->published || $user?->id === $post->user_id;
    }

    // Tạo: không có model cụ thể, chỉ nhận user
    public function create(User $user): bool
    {
        return $user->role === 'writer';
    }

    public function update(User $user, Post $post): Response
    {
        return $user->id === $post->user_id
            ? Response::allow()
            : Response::denyAsNotFound();   // trả 404: không cho người lạ biết bài tồn tại
    }

    public function delete(User $user, Post $post): bool
    {
        return $user->id === $post->user_id;
    }
}
```

Mấy quy tắc:

- Policy được resolve qua service container ([Chương 26](26-laravel-container-provider-facade.md)),
  nên constructor được inject dependency.
- `before()` trả `true` (cho hết), `false` (cấm hết), hoặc `null` (để method cụ thể quyết). ⚠️ Tài
  liệu cảnh báo: `before()` không được gọi nếu policy không có method trùng tên với ability đang kiểm
  tra. Mã nguồn `resolvePolicyCallback` trả `false` ngay khi method không tồn tại.
- Ví dụ của tài liệu Laravel so `$user->id === $post->user_id`. Phép `===` chỉ đúng khi hai bên cùng
  kiểu `int`. Nếu không chắc driver trả cột khoá ngoại về kiểu gì, khai cast `'user_id' => 'integer'`
  trong model `Post` để kiểu luôn rõ ràng (cast ở [Chương 27](27-laravel-database-eloquent.md)).

### 11.2 Laravel tìm policy cho model thế nào

Mặc định Laravel tự phát hiện (*policy discovery*) theo quy ước tên: model `App\Models\Post` ứng với
`App\Models\Policies\PostPolicy` hoặc `App\Policies\PostPolicy` (thư mục `Policies` nằm cùng cấp hoặc
cao hơn thư mục chứa model, tên là tên model + `Policy`). Không theo quy ước thì đăng ký tay:

```php
// AppServiceProvider::boot()
Gate::policy(Order::class, OrderPolicy::class);
```

hoặc dùng attribute trên model:

```php
use App\Policies\OrderPolicy;
use Illuminate\Database\Eloquent\Attributes\UsePolicy;

#[UsePolicy(OrderPolicy::class)]
class Order extends Model {}
```

Khi gọi `$user->can('update', $post)`: nếu model có policy, Laravel gọi `PostPolicy::update()`; nếu
không, Laravel tìm gate tên `update` định nghĩa bằng `Gate::define`.

### 11.3 Truyền model hay truyền tên class

- Hành động trên một bản ghi cụ thể: truyền object, `Gate::authorize('update', $post)`.
- Hành động không có bản ghi (`create`, `viewAny`): truyền tên class để Laravel biết dùng policy nào,
  `Gate::authorize('create', Post::class)`.
- Cần thêm ngữ cảnh: truyền array, phần tử đầu quyết định policy, phần còn lại thành tham số thêm:
  `Gate::authorize('update', [$post, $request->integer('category')])` gọi
  `PostPolicy::update(User $user, Post $post, int $category)`.

### 11.4 Role và permission: chọn mô hình

Laravel không có sẵn bảng role/permission. Policy chỉ là chỗ đặt logic; dữ liệu quyền đến từ đâu là
việc của bạn:

| Mô hình | Ví dụ code trong policy | Hợp với |
|---|---|---|
| Sở hữu (*ownership*) | `$user->id === $post->user_id` | Dữ liệu cá nhân: bài viết, đơn hàng |
| Cột role đơn giản | `$user->role === 'editor'` | Ít vai trò, cố định |
| RBAC (*role-based access control*): bảng roles, permissions, bảng nối | `$user->hasPermission('posts.publish')` | Nhiều vai trò, admin tự cấu hình |
| Theo tổ chức/tenant | `$user->current_team_id === $post->team_id` | SaaS nhiều khách hàng |

Thực tế thường kết hợp: "editor được sửa mọi bài trong team của mình, writer chỉ sửa bài của chính mình".
Nhiều dự án dùng gói cộng đồng (phổ biến nhất là `spatie/laravel-permission`) cho phần RBAC; gói đó
vẫn tích hợp với `can()` và policy của Laravel.

⚠️ Đừng rải `if ($user->role === 'admin')` khắp controller và view. Gom vào policy để có một chỗ duy
nhất cần sửa và cần test.

## 12. Gọi kiểm tra quyền ở đâu, và ẩn dữ liệu theo quyền

### 12.1 Các điểm gọi

| Chỗ gọi | Cú pháp | Không được thì |
|---|---|---|
| Middleware trên route | `->middleware('can:update,post')` hoặc `->can('update', 'post')` | 403 trước khi vào controller |
| Attribute trên method controller (Laravel 13) | `#[Authorize('update', 'post')]` | 403 (dựng middleware `can`) |
| Trong controller | `Gate::authorize('update', $post);` | Ném `AuthorizationException` → 403 |
| Trên user | `$request->user()->can('update', $post)` / `cannot(...)` | Trả bool, bạn tự xử lý |
| Form Request | method `authorize(): bool` | 403, `rules()` không chạy |
| Blade | `@can('update', $post) ... @endcan`, `@cannot`, `@canany` | Không hiện phần HTML đó |

Middleware `can` (alias của `Illuminate\Auth\Middleware\Authorize`):

```php
use App\Models\Post;

// "post" là TÊN THAM SỐ ROUTE; route model binding đã đổi nó thành object Post
Route::put('/posts/{post}', [PostController::class, 'update'])->middleware('can:update,post');
Route::put('/posts/{post}', [PostController::class, 'update'])->can('update', 'post');   // tương đương

// Hành động không có model: truyền tên class
Route::post('/posts', [PostController::class, 'store'])->can('create', Post::class);
```

Middleware `can` chạy sau `SubstituteBindings` (Laravel sắp thứ tự middleware theo độ ưu tiên, xem
[Chương 24](24-laravel-routing-controller-middleware.md)), nên nó nhận được model thật thay vì chuỗi
ID.

Attribute (Laravel 13, namespace `Illuminate\Routing\Attributes\Controllers`):

```php
use App\Models\Post;
use Illuminate\Http\RedirectResponse;
use Illuminate\Routing\Attributes\Controllers\Authorize;
use Illuminate\Routing\Attributes\Controllers\Middleware;

#[Middleware('auth')]
final class PostController
{
    #[Authorize('update', 'post')]
    public function update(Post $post): RedirectResponse
    {
        // tới được đây nghĩa là đã có quyền
    }
}
```

⚠️ Từ Laravel 11, class `App\Http\Controllers\Controller` trong skeleton là một abstract class rỗng,
không còn trait `AuthorizesRequests`. Code cũ gọi `$this->authorize('update', $post)` sẽ báo lỗi method
không tồn tại trên dự án mới. Dùng `Gate::authorize()`, hoặc tự thêm
`use Illuminate\Foundation\Auth\Access\AuthorizesRequests;` vào controller.

Form Request ([Chương 25](25-laravel-request-validation-response.md)):

```php
final class UpdatePostRequest extends FormRequest
{
    public function authorize(): bool
    {
        return $this->user()->can('update', $this->route('post'));
    }

    public function rules(): array
    {
        return ['title' => ['required', 'string', 'max:255']];
    }
}
```

Nên chọn một chỗ nhất quán cho cả dự án (thường là middleware/attribute hoặc `Gate::authorize()` đầu
mỗi action). Kiểm ở nhiều chỗ không sai, nhưng thiếu ở một chỗ thì là lỗ hổng, và tính nhất quán giúp
review dễ thấy chỗ thiếu.

### 12.2 Ẩn trong giao diện không phải là phân quyền

```blade
@can('update', $post)
    <a href="{{ route('posts.edit', $post) }}">Sửa</a>
@endcan
```

`@can` chỉ quyết định hiện hay không hiện nút. Kẻ tấn công không cần nút: họ gửi thẳng
`PUT /posts/10`. Server vẫn phải kiểm quyền ở route/controller. Tương tự với SPA: tài liệu Laravel có
mẫu gửi danh sách quyền xuống frontend Inertia qua middleware `HandleInertiaRequests::share()` để vẽ
giao diện, và nhấn mạnh phân quyền luôn phải xử lý ở server.

### 12.3 Ẩn thuộc tính khi trả JSON

Khi controller trả một model hoặc collection, Laravel tự chuyển thành JSON qua `toArray()`. Mọi cột đều
đi ra ngoài, trừ những cột bị ẩn:

```php
use Illuminate\Database\Eloquent\Attributes\Hidden;

#[Hidden(['password', 'remember_token', 'two_factor_secret'])]
class User extends Authenticatable {}
```

Ngược lại, `#[Visible([...])]` là whitelist: chỉ các cột liệt kê mới đi ra. Thay đổi tạm cho một
instance: `$user->makeVisible('email')`, `$user->makeHidden('phone')`, `mergeVisible`, `mergeHidden`,
`setVisible`, `setHidden` (tài liệu Eloquent Serialization).

⚠️ `$hidden` là danh sách đen: thêm cột nhạy cảm mới (ví dụ `api_secret`) mà quên thêm vào `#[Hidden]`
thì nó lộ ở mọi API trả nguyên model. Với API công khai, nên dùng *API Resource* (class quy định rõ
từng field trả ra) thay vì trả model trực tiếp.

### 12.4 Field theo quyền với API Resource

```php
<?php
declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

final class UserResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            // chỉ chủ tài khoản hoặc người có quyền mới thấy email
            'email' => $this->when($request->user()?->can('viewPrivate', $this->resource), $this->email),
            // nhiều field cùng một điều kiện
            $this->mergeWhen($request->user()?->isAdministrator() ?? false, [
                'last_login_ip' => $this->last_login_ip,
                'created_at' => $this->created_at,
            ]),
        ];
    }
}
```

Khi điều kiện của `when()` sai, key đó biến mất hẳn khỏi JSON (không phải `null`). Chi tiết API
Resource ở [Chương 25](25-laravel-request-validation-response.md).

### 12.5 Lọc bản ghi theo quyền ngay trong query

Policy trả lời "được làm gì với một bản ghi". Với danh sách, kiểm từng bản ghi sau khi đã lấy hết là
vừa chậm vừa sai phân trang. Cách đúng là đưa điều kiện quyền vào câu query:

```php
// ⚠️ Sai: lấy mọi đơn hàng rồi lọc trong PHP (chậm, và phân trang đếm sai)
$orders = Order::paginate(20)->filter(fn (Order $o): bool => $request->user()->can('view', $o));

// Đúng: chỉ lấy đơn của user hiện tại, đi qua relationship
$orders = $request->user()->orders()->latest()->paginate(20);

// Hoặc một local scope dùng lại nhiều nơi (scope ở Chương 27)
$orders = Order::query()->visibleTo($request->user())->paginate(20);
```

Đi qua relationship (`$request->user()->orders()`) cũng là cách gọn nhất để lấy một bản ghi mà vẫn
an toàn: `$request->user()->orders()->findOrFail($id)` trả 404 nếu đơn không thuộc user. Kỹ thuật này
dùng lại ở mục 13.2.

⚠️ *Global scope* (tự thêm điều kiện cho mọi query của model, [Chương 27](27-laravel-database-eloquent.md))
dựa trên `auth()->user()` nghe tiện, nhưng chạy sai trong queue worker hoặc lệnh Artisan (không có
user đăng nhập) và dễ quên khi cần bỏ scope. Dùng có cân nhắc.

## 13. Hai lỗ hổng hay gặp nhất: mass assignment và IDOR

### 13.1 Mass assignment: tự cấp quyền qua form

*Mass assignment* (gán hàng loạt) là gán nhiều thuộc tính một lần từ một array:
`User::create($data)`, `$user->fill($data)`, `$user->update($data)`. Cơ chế whitelist/blacklist của
Eloquent (`#[Fillable]`, `$fillable`, `$guarded`) đã có ở [Chương 27](27-laravel-database-eloquent.md).
Ở đây ta nhìn nó từ góc phân quyền: nếu bảng `users` có cột `role` hoặc `is_admin`, mass assignment
không lọc là con đường để user tự nâng quyền (*privilege escalation*).

```php
// ⚠️ Model: protected $guarded = [];   (tắt bảo vệ)
public function register(Request $request): RedirectResponse
{
    $user = User::create($request->all());   // client gửi thêm role=admin → thành admin
    Auth::login($user);
    return redirect('/dashboard');
}
```

Mô phỏng bằng PHP thuần:

```php
<?php
declare(strict_types=1);

// Mô phỏng mass assignment: fill() không lọc và fill() có whitelist (KHÔNG phải code Eloquent thật).

final class UserModel
{
    /** @var array<string, mixed> */
    public array $attributes = ['role' => 'member'];

    /** @param list<string> $fillable  rỗng = không lọc gì */
    public function __construct(private array $fillable = []) {}

    /** @param array<string, mixed> $input */
    public function fill(array $input): self
    {
        foreach ($input as $key => $value) {
            if ($this->fillable === [] || in_array($key, $this->fillable, true)) {
                $this->attributes[$key] = $value;
            }
            // Eloquent: key ngoài whitelist bị lặng lẽ bỏ qua
        }
        return $this;
    }
}

// Request đăng ký mà kẻ tấn công gửi thêm field role
$input = ['name' => 'Mallory', 'email' => 'm@example.com', 'role' => 'admin'];

$unsafe = (new UserModel())->fill($input);                              // giống $guarded = []
echo $unsafe->attributes['role'], "\n";                                 // in ra: admin

$safe = (new UserModel(['name', 'email', 'password']))->fill($input);   // giống #[Fillable([...])]
echo $safe->attributes['role'], "\n";                                   // in ra: member
```

Phòng thủ cần cả hai lớp:

1. Model khai whitelist (`#[Fillable([...])]` như model `User` mặc định). Cột quyền (`role`,
   `is_admin`, `team_id`, `balance`) không bao giờ nằm trong whitelist.
2. Controller chỉ đưa dữ liệu đã validate: `$request->validated()` hoặc `$request->safe()->only([...])`,
   không dùng `$request->all()`.

Khi thực sự cần đổi role (trang quản trị), làm tường minh, sau khi đã kiểm quyền:

```php
Gate::authorize('changeRole', $target);           // chỉ admin mới được
$target->forceFill(['role' => $request->validated('role')])->save();   // forceFill bỏ qua whitelist, cố ý
```

⚠️ Bẫy liên quan:

- `$guarded = ['is_admin']` (blacklist) mong manh: thêm cột `role` sau này mà quên cập nhật là thủng.
- Whitelist có field `user_id` hoặc `team_id`: client tự gán bài viết cho người khác, hoặc chuyển dữ
  liệu sang tenant khác. Gán các khoá sở hữu từ phía server: `$request->user()->posts()->create($data)`.
- Field ngoài whitelist bị bỏ qua không báo lỗi. Ở môi trường dev, bật
  `Model::preventSilentlyDiscardingAttributes($this->app->isLocal())` trong `AppServiceProvider` để
  phát hiện sớm.

### 13.2 IDOR: đoán ID là xem được dữ liệu người khác

*IDOR* (*Insecure Direct Object Reference*) là khi ứng dụng dùng một định danh do client gửi (ID trong
URL, trong body) để truy cập tài nguyên mà không kiểm tra người gửi có quyền với tài nguyên đó. Trong
danh sách OWASP Top 10 bản 2021, nhóm lỗi này thuộc mục đứng đầu *A01 Broken Access Control*.

Kịch bản:

| Bước | Alice (user 1) | Mallory (user 2, kẻ tấn công) | Kết quả |
|---|---|---|---|
| 1 | Mở `GET /invoices/1001`, thấy hoá đơn của mình | | Đúng |
| 2 | | Đăng nhập tài khoản của chính Mallory, mở `GET /invoices/1002` (hoá đơn của mình) | Đúng |
| 3 | | Sửa URL thành `GET /invoices/1001` | Route chỉ có `auth`, route model binding tìm thấy hoá đơn 1001 |
| 4 | | Viết script chạy 1 tới 100000 | Tải về toàn bộ hoá đơn của mọi khách hàng |

Điểm mấu chốt: route model binding (`Invoice $invoice`) chỉ đảm bảo bản ghi tồn tại (không thì 404),
không kiểm tra quyền. Middleware `auth` chỉ đảm bảo có người đăng nhập. Cả hai đều không trả lời "hoá
đơn này có phải của người đang hỏi không".

Ba cách chặn, có thể kết hợp:

```php
// Cách 1: policy + middleware can (hoặc #[Authorize], hoặc Gate::authorize trong controller)
Route::get('/invoices/{invoice}', [InvoiceController::class, 'show'])
    ->middleware(['auth', 'can:view,invoice']);

// InvoicePolicy
public function view(User $user, Invoice $invoice): bool
{
    return $user->id === $invoice->user_id;
}

// Cách 2: đi qua relationship của user hiện tại, không tìm trên toàn bảng
public function show(Request $request, int $id): View
{
    $invoice = $request->user()->invoices()->findOrFail($id);   // không phải của mình → 404
    return view('invoices.show', ['invoice' => $invoice]);
}

// Cách 3: scoped binding cho route lồng nhau: bản ghi con phải thuộc bản ghi cha
Route::get('/teams/{team}/projects/{project}', [ProjectController::class, 'show'])
    ->scopeBindings()
    ->middleware(['auth', 'can:view,team']);
```

Với cách 3, Laravel tìm `project` qua relationship `$team->projects()`, nên `/teams/1/projects/99`
trả 404 nếu project 99 không thuộc team 1. Nhưng scoped binding vẫn không kiểm user có thuộc team 1
không; vì vậy ví dụ vẫn cần `can:view,team`. Scoped binding là lớp phụ, policy là lớp chính.

⚠️ Những thứ không phải cách chặn IDOR:

- Dùng UUID hoặc ID khó đoán thay cho số tự tăng. Giảm khả năng dò hàng loạt, nhưng ID vẫn lộ qua
  link chia sẻ, log, header `Referer`, email. Đây là phòng thủ bổ sung, không thay kiểm quyền.
- Ẩn nút trong giao diện (mục 12.2).
- Kiểm quyền ở trang xem nhưng quên ở các action khác: `update`, `destroy`, endpoint tải file đính kèm,
  endpoint export CSV, endpoint API cho mobile. Mỗi action cần kiểm riêng.
- Lấy ID sở hữu từ input: `Order::where('user_id', $request->input('user_id'))`. Kẻ tấn công gửi
  user_id của người khác. ID sở hữu luôn lấy từ `$request->user()`.

### 13.3 Các lỗi khác ở tầng auth (tổng hợp)

| Lỗi | Hậu quả | Mục |
|---|---|---|
| Báo lỗi đăng nhập khác nhau cho "sai email" và "sai mật khẩu" | Dò được email đã đăng ký | 3.2 |
| Không rate limit `/login`, `/sanctum/token`, `/forgot-password` | Brute force, credential stuffing, spam email | 3.9 |
| Không regenerate session sau login | Session fixation | 3.2 |
| Logout bằng `GET` | Trang khác đăng xuất được user | 3.7 |
| Logout không `invalidate()` session | Dữ liệu phiên cũ còn lại | 3.7 |
| Không cấu hình trusted host | Link reset mật khẩu trỏ về domain kẻ tấn công | 5.5 |
| Token Sanctum không hết hạn, không thu hồi khi đổi mật khẩu | Token lộ dùng được mãi | 8.3 |
| Chỉ dựa vào `tokenCan()` để phân quyền | Request từ SPA luôn qua | 8.3 |
| `Gate::before` trả `false` cho user thường | Mọi user bị chặn mọi quyền | 10.4 |
| Trả nguyên model ra JSON | Lộ cột nhạy cảm mới thêm | 12.3 |

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Chỉ gắn `auth`, nghĩ là đủ bảo mật | `auth` là xác thực, không phải phân quyền | Mỗi route có tài nguyên cụ thể phải có policy/`can` |
| Đưa `$request->all()` vào `Auth::attempt()` | Mọi key không chứa "password" thành điều kiện `where`; array thành `whereIn` | Validate rồi chỉ truyền `email`, `password` |
| Băm mật khẩu trước khi gọi `Auth::attempt()` | `attempt` tự so mật khẩu thô với hash; băm trước thì không bao giờ khớp | Truyền mật khẩu thô |
| Cập nhật mật khẩu thô bằng `User::where(...)->update()` mà tưởng cast `hashed` sẽ băm | Mass update không qua cast, mật khẩu thô bị lưu thẳng vào DB | Hoặc tự băm và cập nhật qua query, hoặc gán qua model rồi `save()` |
| Dùng guard riêng cho "admin" trong cùng bảng users | Guard là cách nhận diện, không phải quyền | Cột role + Gate/Policy |
| `Gate::before(fn ($u) => $u->isAdmin())` | Trả `false` cho user thường, chốt kết quả | Trả `true` hoặc `null` |
| Policy có `before()` nhưng không có method của ability | `before()` không được gọi, kết quả `false` | Khai đủ method cho mọi ability |
| Gọi `$this->authorize()` trong dự án Laravel 11+ | Base `Controller` không còn trait `AuthorizesRequests` | `Gate::authorize()` hoặc thêm trait |
| `logoutOtherDevices()` nhưng không gắn `auth.session` | Session ở máy khác không bị kiểm tra | Gắn `auth.session` cho group route |
| Dùng API token của Sanctum cho SPA của mình, lưu trong `localStorage` | XSS đọc được token | Sanctum SPA mode (cookie HttpOnly) |
| Quên `Accept: application/json` ở client API | Lỗi xác thực bị biến thành redirect tới route `login` | Client luôn gửi header này |
| Ẩn nút bằng `@can` mà không kiểm ở server | Gửi request trực tiếp vẫn qua | Kiểm quyền ở route/controller |
| Lọc danh sách bằng `can()` sau khi đã `paginate()` | Chậm, phân trang sai, dễ lộ | Đưa điều kiện quyền vào query |

## Tóm tắt chương

- Xác thực trả lời "bạn là ai" (thất bại: 401 hoặc redirect login), phân quyền trả lời "bạn được làm
  gì" (thất bại: 403). Hai việc khác nhau, phải làm cả hai.
- Guard quyết định cách nhận diện user (session, sanctum...), provider quyết định lấy user từ đâu
  (eloquent, database). Cấu hình ở `config/auth.php`. Middleware `auth:<guard>` bảo vệ route.
- Đăng nhập session chỉ lưu ID user trong session; mỗi request guard tra lại user qua provider.
  `Auth::attempt()` được bọc Timebox, tự rehash mật khẩu khi cần, đổi session ID. "Remember me" là
  cookie `id|remember_token|HMAC(hash mật khẩu)`.
- Mật khẩu băm bằng bcrypt (mặc định, cost 12) qua facade `Hash` hoặc cast `hashed`; nhớ giới hạn 72
  byte của bcrypt. Token reset mật khẩu lưu dạng bcrypt hash, link xác minh email là signed URL.
- Starter kit (React, Vue, Svelte, Livewire, dùng Fortify ở backend) dựng sẵn toàn bộ luồng xác thực,
  kể cả rate limit và 2FA.
- Sanctum: SPA của bạn dùng session cookie (có CSRF, chống lộ qua XSS); mobile/script dùng Bearer token
  lưu SHA-256 trong DB, có abilities, mặc định không hết hạn. Passport chỉ khi cần OAuth2 thật sự.
- Gate cho quyền chung, Policy cho quyền theo model. `before` trả `true`/`null`, không trả `false` bừa.
  Kiểm quyền qua middleware `can`, `#[Authorize]`, `Gate::authorize()`, Form Request `authorize()`.
- Ẩn dữ liệu theo quyền bằng `#[Hidden]`/`#[Visible]`, API Resource `when`/`mergeWhen`, và lọc ngay
  trong query. Ẩn nút trên giao diện không phải phân quyền.
- Mass assignment: whitelist + `validated()`, khoá sở hữu gán từ server. IDOR: policy cho mọi action,
  hoặc truy vấn qua relationship của user hiện tại; UUID không thay được kiểm quyền.

## Câu hỏi tự kiểm tra

1. Một route chỉ gắn middleware `auth`. Hãy mô tả một cuộc tấn công có thể xảy ra, và nêu hai cách sửa
   khác nhau. (mục 1.2, 13.2)
2. Guard và provider khác nhau thế nào? Vì sao tạo guard `admin` để phân biệt "user thường" và "user có
   quyền admin" trong cùng bảng `users` là thiết kế sai? (mục 2.1, 2.6)
3. Sau khi `Auth::attempt()` thành công, trong session có gì? Ở request kế tiếp, Laravel lấy user ra như
   thế nào, và tốn bao nhiêu query nếu controller gọi `Auth::user()` năm lần? (mục 2.5, 3.3, 3.4)
4. Vì sao `Auth::attempt()` được bọc trong Timebox? Nếu không có nó, kẻ tấn công học được gì? (mục 3.3)
5. Cookie "remember me" chứa những gì? Giải thích vì sao đổi mật khẩu và logout đều làm cookie cũ mất
   hiệu lực. (mục 3.6)
6. Vì sao token của Sanctum chỉ cần SHA-256, còn mật khẩu và token reset mật khẩu thì dùng bcrypt? Lý lẽ
   này có áp dụng được cho token reset mật khẩu không? (mục 4, 5.4, 8.3)
7. Một SPA ở `app.shop.vn` gọi API ở `api.shop.vn`. Liệt kê các cấu hình cần có để Sanctum SPA mode hoạt
   động, và hậu quả nếu thiếu từng cái. (mục 8.4)
8. `Gate::before(fn (User $u) => $u->isAdmin())` sai ở đâu? Viết lại cho đúng. (mục 10.4)
9. Khi nào bạn chọn Passport thay vì Sanctum? Muốn cho user đăng nhập bằng tài khoản Google thì dùng gói
   nào? (mục 9.3)
10. Kể ba thứ thường bị nhầm là "cách chặn IDOR" nhưng không phải. (mục 13.2)

## Bài tập

1. Mở rộng mô phỏng guard ở mục 2.5: thêm chức năng "remember me" như mục 3.6 (cookie
   `id|token|HMAC`), thêm `logout()` sinh token mới, và một `TokenGuard` thứ hai đọc token từ một
   array giả lập header `Authorization`. Viết đoạn code chứng minh cùng một `ArrayUserProvider` dùng
   được cho cả hai guard. Chạy bằng `php file.php`.
2. Viết bằng PHP thuần một class `Gate` hỗ trợ: `define`, `policy(string $modelClass, object $policy)`,
   `before`, `after` (chỉ có tác dụng khi kết quả là `null`), `allows`, `authorize` (ném exception), và
   user `null` bị từ chối trừ khi tham số đầu của closure cho phép `null` (gợi ý: dùng
   `ReflectionFunction` để đọc kiểu tham số). Viết các ca kiểm thử bằng `assert()` hoặc `var_dump`
   cho: chủ bài, người lạ, admin, khách xem bài công khai, `before` trả `false`.
3. Trong một dự án Laravel 13 (tạo bằng starter kit bất kỳ), xây tính năng "đơn hàng" gồm: migration
   bảng `orders` (`user_id`, `total`, `status`), `OrderPolicy` (`viewAny`, `view`, `update`, `delete`;
   admin được mọi thứ qua `before`), route resource có kiểm quyền bằng một cách nhất quán, danh sách chỉ
   hiện đơn của user, `OrderResource` chỉ hiện `internal_note` cho admin. Sau đó tự đóng vai kẻ tấn công:
   đăng nhập user B và thử xem, sửa, xoá đơn của user A bằng `curl`; ghi lại status code nhận được.
4. Thêm vào dự án ở bài 3 một API cho mobile bằng Sanctum token: endpoint đổi email + mật khẩu lấy token
   (có rate limit), token có abilities `orders:read`, `orders:write`, hết hạn sau 30 ngày. Chứng minh
   bằng `curl` rằng token chỉ có `orders:read` không sửa được đơn, và token của user B không đọc được
   đơn của user A dù có `orders:read`.

## Đọc thêm

- Laravel 13.x: [Authentication](https://laravel.com/docs/13.x/authentication),
  [Authorization](https://laravel.com/docs/13.x/authorization),
  [Hashing](https://laravel.com/docs/13.x/hashing),
  [Resetting Passwords](https://laravel.com/docs/13.x/passwords),
  [Email Verification](https://laravel.com/docs/13.x/verification),
  [Starter Kits](https://laravel.com/docs/13.x/starter-kits),
  [Fortify](https://laravel.com/docs/13.x/fortify),
  [Sanctum](https://laravel.com/docs/13.x/sanctum),
  [Passport](https://laravel.com/docs/13.x/passport),
  [Eloquent Serialization](https://laravel.com/docs/13.x/eloquent-serialization),
  [Eloquent API Resources](https://laravel.com/docs/13.x/eloquent-resources),
  [Encryption](https://laravel.com/docs/13.x/encryption). Bản markdown gốc:
  [github.com/laravel/docs nhánh 13.x](https://github.com/laravel/docs/tree/13.x).
- Mã nguồn đã đọc khi viết chương (nhánh 13.x của
  [laravel/framework](https://github.com/laravel/framework/tree/13.x/src/Illuminate)):
  `Auth/SessionGuard.php`, `Auth/EloquentUserProvider.php`, `Auth/AuthManager.php`,
  `Auth/Middleware/Authenticate.php`, `Auth/Passwords/DatabaseTokenRepository.php`,
  `Auth/Passwords/PasswordBroker.php`, `Auth/Notifications/VerifyEmail.php`,
  `Auth/Access/Gate.php`, `Session/Middleware/AuthenticateSession.php`, `Hashing/BcryptHasher.php`,
  `Foundation/Auth/User.php`, `Foundation/Auth/EmailVerificationRequest.php`,
  `Foundation/Exceptions/Handler.php`. Skeleton
  [laravel/laravel 13.x](https://github.com/laravel/laravel/tree/13.x): `config/auth.php`,
  `app/Models/User.php`, migration tạo bảng users. [laravel/sanctum](https://github.com/laravel/sanctum):
  `src/Guard.php`, `src/HasApiTokens.php`, `src/PersonalAccessToken.php`, `config/sanctum.php`.
- Ghi chú phát hành Laravel 12 (starter kit mới, Breeze/Jetstream ngừng cập nhật):
  [laravel.com/docs/12.x/releases](https://laravel.com/docs/12.x/releases).
- PHP: [password_hash](https://www.php.net/manual/en/function.password-hash.php),
  [hash_hmac](https://www.php.net/manual/en/function.hash-hmac.php),
  [hash_equals](https://www.php.net/manual/en/function.hash-equals.php).
- [RFC 6749: The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749),
  [RFC 7636: PKCE](https://www.rfc-editor.org/rfc/rfc7636),
  [RFC 6750: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750).
- OWASP: [A01:2021 Broken Access Control](https://owasp.org/Top10/A01_2021-Broken_Access_Control/),
  [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html),
  [Mass Assignment Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html),
  [Insecure Direct Object Reference Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html).
