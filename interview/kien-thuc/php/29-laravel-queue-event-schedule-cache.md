# Chương 29. Queue, event, scheduler, cache, mail và notification

> [← Mục lục](README.md) · [← Chương 28: Xác thực và phân quyền trong Laravel](28-laravel-auth.md) · [Chương 30: Laravel: kiểm thử, Octane và triển khai →](30-laravel-testing-octane-deploy.md)

**Bạn sẽ học được:**

- Vì sao web app cần *xử lý nền* (background processing), và một hàng đợi (*queue*) hoạt động thế nào
  bên dưới: payload, reserve, attempt, retry, failed job. Bạn sẽ tự dựng một queue tí hon bằng PHP thuần
  để thấy tận mắt.
- Viết, dispatch và chạy job trong Laravel; cấu hình worker cho đúng (`tries`, `backoff`, `timeout`,
  `retry_after`) và tránh các lỗi làm job chạy hai lần hoặc "thất bại oan".
- Điều phối job: unique job, job middleware (`WithoutOverlapping`, `RateLimited`), chain, batch; quản lý
  worker trên production bằng Supervisor và Horizon.
- Tách code bằng event và listener (đồng bộ và qua queue), và các bẫy liên quan tới transaction.
- Chạy việc định kỳ bằng scheduler (`schedule:run`, `withoutOverlapping`, `onOneServer`).
- Dùng cache đúng cách (`remember`, atomic lock, tag, `flexible`, `memo`), gửi mail và notification ở mức
  cơ bản, và hiểu broadcasting (Reverb) là gì.

**Cần biết trước:** [Chương 16: PHP làm việc với database](16-php-va-database.md) (PDO, transaction),
[Chương 18: PHP-FPM, Nginx và OPcache](18-fpm-nginx-opcache.md) (mô hình mỗi request một lần chạy),
[Chương 23](23-laravel-gioi-thieu.md) tới [Chương 27](27-laravel-database-eloquent.md) (cấu trúc project,
artisan, service container, facade, Eloquent).

Cách chạy ví dụ: các ví dụ đánh dấu "PHP thuần" chạy được bằng một lệnh, không cần Laravel:

```bash
# chạy trong thư mục chứa file
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

Các ví dụ PHP thuần trong chương đã được chạy thử trên PHP 8.5. Các đoạn code Laravel cần một project
Laravel 13 (tạo như ở [Chương 23](23-laravel-gioi-thieu.md)); hành vi Laravel mô tả trong chương được
đối chiếu với tài liệu Laravel 13.x và mã nguồn `laravel/framework` nhánh 13.x.

## 1. Vì sao cần xử lý nền

### 1.1 Vấn đề: có những việc không nên làm trong request

Nhớ lại [Chương 18](18-fpm-nginx-opcache.md): với PHP-FPM, mỗi HTTP request chiếm trọn một FPM worker từ
lúc bắt đầu tới lúc trả response. Người dùng thì đứng chờ trước màn hình suốt thời gian đó.

Thử hình dung chức năng "đăng ký tài khoản". Sau khi lưu user vào database, app còn phải:

1. Gửi email chào mừng (nói chuyện với SMTP server, có thể mất 1 đến 3 giây, có lúc treo).
2. Tạo ảnh đại diện mặc định (xử lý ảnh, tốn CPU).
3. Đồng bộ khách hàng mới sang CRM của bộ phận bán hàng (gọi HTTP API bên ngoài, có lúc trả lỗi 503).

Nếu làm cả ba ngay trong request:

- Người dùng chờ lâu, dù họ chỉ cần biết "đăng ký thành công".
- Một dịch vụ ngoài lỗi (CRM sập) làm cả request lỗi, dù user đã được lưu rồi.
- FPM worker bị chiếm lâu, nên khi đông người, worker cạn và request khác phải xếp hàng (lỗi 502/504
  ở Chương 18).
- Không có cách nào tự động thử lại khi dịch vụ ngoài lỗi tạm thời.

Nhận xét then chốt: ba việc trên **không cần xong ngay** để trả lời người dùng. Chúng chỉ cần chắc chắn
được làm, sớm thôi. Đó là dấu hiệu của việc nên đưa ra *xử lý nền* (background processing): request
chỉ ghi lại "cần làm việc X" rồi trả response ngay, còn một process khác làm X sau.

### 1.2 Ý tưởng hàng đợi: producer, queue, worker

*Queue* (hàng đợi) là một danh sách việc cần làm, vào trước ra trước (FIFO, first in first out), được
lưu ở một nơi mà nhiều process cùng đọc ghi được: một bảng database, Redis, Amazon SQS...

Ba vai trò:

- *Producer* (bên sinh việc): code trong request web. Nó đóng gói việc cần làm thành một *job* rồi đẩy
  vào queue. Thao tác này rất nhanh (một câu INSERT hay một lệnh Redis).
- *Queue backend*: nơi cất job chờ xử lý.
- *Worker* (bên xử lý, còn gọi là *consumer*): một process PHP chạy liên tục ở nền, lấy job ra và chạy.

```
  Trình duyệt                Web (PHP-FPM)                Queue backend           Worker (CLI, chạy mãi)
  -----------                -------------                -------------           ----------------------
  POST /register  ------->   lưu user vào DB
                             đẩy job "gửi email"  ------> [job1]
                             đẩy job "đồng bộ CRM" -----> [job1][job2]
  <------- 201 Created       (xong, ~50 ms)
                                                                          <------ lấy job1, gửi email
                                                                          <------ lấy job2, gọi CRM
                                                                                   lỗi 503? thử lại sau
```

Lợi ích:

- Response nhanh, vì request chỉ còn làm phần bắt buộc.
- Cô lập lỗi: CRM sập thì job đồng bộ lỗi và được thử lại, không ảnh hưởng người dùng.
- Tự động thử lại (*retry*) với khoảng chờ tăng dần.
- San tải: 10.000 email cần gửi thì xếp hàng trong queue, worker gửi dần với tốc độ vừa sức, không làm
  sập SMTP server.
- Mở rộng độc lập: thêm worker khi queue dài, không cần thêm web server.

Cái giá phải trả:

- Thêm thành phần cần vận hành (backend, worker, công cụ theo dõi).
- Kết quả không có ngay: không thể trả về cho người dùng "email đã gửi thành công" trong cùng response.
- Job có thể chạy **nhiều hơn một lần** (mục 3.7 giải thích vì sao), nên code trong job phải được viết
  cẩn thận.

⚠️ Đừng đưa vào queue những việc mà response **phụ thuộc** vào kết quả (kiểm tra mật khẩu, tính tổng
tiền hiển thị ngay). Queue dành cho việc "làm sau cũng được".

### 1.3 Tự dựng một queue tí hon bằng PHP thuần

Cách tốt nhất để hiểu queue của Laravel là tự viết một bản đơn giản. Ví dụ sau dùng SQLite trong bộ
nhớ làm backend, mô phỏng khá sát driver `database` của Laravel (sẽ gặp lại ở mục 2): bảng `jobs` có cột
`payload`, `attempts`, `reserved_at`, `available_at`, và bảng `failed_jobs` cho job hết lượt thử.

```php
<?php
declare(strict_types=1);

// PHP thuần. Một "queue" tối giản đặt trên bảng SQLite, mô phỏng driver `database` của Laravel.
// Chỉ để hiểu cơ chế: payload, reserve, attempts, retry, failed_jobs.

interface Job
{
    public function handle(): void;
}

final class SendWelcomeEmail implements Job
{
    public function __construct(public string $email) {}

    public function handle(): void
    {
        echo "  gửi email chào mừng tới {$this->email}\n";
    }
}

final class CallFlakyApi implements Job
{
    public function __construct(public int $orderId) {}

    public function handle(): void
    {
        throw new RuntimeException("API đối tác trả 503 cho đơn {$this->orderId}");
    }
}

final class MiniQueue
{
    public function __construct(private PDO $db)
    {
        $db->exec('CREATE TABLE jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            queue TEXT NOT NULL,
            payload TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0,
            reserved_at INTEGER NULL,
            available_at INTEGER NOT NULL
        )');
        $db->exec('CREATE TABLE failed_jobs (id INTEGER PRIMARY KEY, payload TEXT, exception TEXT)');
    }

    // Phía web: biến object job thành chuỗi rồi INSERT. Không chạy gì cả.
    public function push(Job $job, string $queue = 'default', int $delay = 0): void
    {
        $payload = json_encode([
            'displayName' => $job::class,
            'maxTries' => 3,
            'command' => serialize($job),
        ], JSON_THROW_ON_ERROR);

        $stmt = $this->db->prepare(
            'INSERT INTO jobs (queue, payload, available_at) VALUES (?, ?, ?)'
        );
        $stmt->execute([$queue, $payload, time() + $delay]);
    }

    // Phía worker: lấy job sẵn sàng sớm nhất, đánh dấu reserved và tăng attempts.
    // (MySQL 8 dùng SELECT ... FOR UPDATE SKIP LOCKED để nhiều worker không lấy trùng.)
    /** @return array{id:int, attempts:int, payload:string}|null */
    public function pop(string $queue = 'default'): ?array
    {
        $this->db->beginTransaction();
        $stmt = $this->db->prepare(
            'SELECT id, attempts, payload FROM jobs
             WHERE queue = ? AND reserved_at IS NULL AND available_at <= ?
             ORDER BY id LIMIT 1'
        );
        $stmt->execute([$queue, time()]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);
        if ($row === false) {
            $this->db->commit();
            return null;
        }
        $attempts = (int) $row['attempts'] + 1;
        $this->db->prepare('UPDATE jobs SET reserved_at = ?, attempts = ? WHERE id = ?')
            ->execute([time(), $attempts, $row['id']]);
        $this->db->commit();

        return ['id' => (int) $row['id'], 'attempts' => $attempts, 'payload' => $row['payload']];
    }

    public function delete(int $id): void
    {
        $this->db->prepare('DELETE FROM jobs WHERE id = ?')->execute([$id]);
    }

    // Trả job về hàng đợi, cho phép lấy lại sau $delay giây.
    public function release(int $id, int $delay): void
    {
        $this->db->prepare('UPDATE jobs SET reserved_at = NULL, available_at = ? WHERE id = ?')
            ->execute([time() + $delay, $id]);
    }

    public function fail(array $record, Throwable $e): void
    {
        $this->db->prepare('INSERT INTO failed_jobs (payload, exception) VALUES (?, ?)')
            ->execute([$record['payload'], $e->getMessage()]);
        $this->delete($record['id']);
    }

    public function count(string $table): int
    {
        return (int) $this->db->query("SELECT COUNT(*) FROM {$table}")->fetchColumn();
    }
}

// Vòng lặp worker: lấy, giải nén, chạy, rồi xoá / thử lại / ghi failed.
function work(MiniQueue $queue): void
{
    while (($record = $queue->pop()) !== null) {
        $payload = json_decode($record['payload'], true, flags: JSON_THROW_ON_ERROR);
        /** @var Job $job */
        $job = unserialize($payload['command']);
        echo "attempt {$record['attempts']} của {$payload['displayName']}\n";

        try {
            $job->handle();
            $queue->delete($record['id']);          // thành công: xoá khỏi hàng đợi
        } catch (Throwable $e) {
            echo "  lỗi: {$e->getMessage()}\n";
            if ($record['attempts'] >= $payload['maxTries']) {
                $queue->fail($record, $e);          // hết lượt: chuyển sang failed_jobs
                echo "  -> hết lượt, ghi vào failed_jobs\n";
            } else {
                $queue->release($record['id'], 0); // còn lượt: trả về hàng đợi (backoff = 0)
            }
        }
    }
}

$queue = new MiniQueue(new PDO('sqlite::memory:', options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]));

// "Request web": chỉ đẩy job rồi trả response ngay
$queue->push(new SendWelcomeEmail('an@example.com'));
$queue->push(new CallFlakyApi(42));
echo "đang chờ: {$queue->count('jobs')} job\n";

// "Worker" (process khác, chạy nền)
work($queue);

echo "còn lại: {$queue->count('jobs')} job, thất bại: {$queue->count('failed_jobs')} job\n";

// in ra:
// đang chờ: 2 job
// attempt 1 của SendWelcomeEmail
//   gửi email chào mừng tới an@example.com
// attempt 1 của CallFlakyApi
//   lỗi: API đối tác trả 503 cho đơn 42
// attempt 2 của CallFlakyApi
//   lỗi: API đối tác trả 503 cho đơn 42
// attempt 3 của CallFlakyApi
//   lỗi: API đối tác trả 503 cho đơn 42
//   -> hết lượt, ghi vào failed_jobs
// còn lại: 0 job, thất bại: 1 job
```

Những điều rút ra từ ví dụ, và cũng là xương sống của queue trong Laravel:

1. *Payload*: job là một object PHP, nhưng queue chỉ cất được chuỗi. Producer `serialize()` object (xem
   lại serialize ở [Chương 14](14-file-json-thoi-gian.md)), bọc trong JSON kèm thông tin phụ (tên class,
   số lần thử tối đa). Worker `unserialize()` để dựng lại object. Vì vậy mọi thứ đặt vào property của
   job phải serialize được: không truyền closure, PDO, resource (file handle, socket) vào job.
2. *Reserve*: worker đánh dấu job "đang được xử lý" (`reserved_at`) để worker khác không lấy trùng. Với
   nhiều worker chạy song song trên MySQL, Laravel dùng `SELECT ... FOR UPDATE SKIP LOCKED`
   (cơ chế khoá dòng ở [Lock và deadlock](../database/15-lock-deadlock.md) của bộ giáo trình database); ví dụ trên chỉ có một worker
   nên không cần.
3. *Attempt* (lần thử): mỗi lần worker lấy job ra là `attempts` tăng 1, **ngay lúc lấy ra**, trước khi
   chạy. Điểm này quan trọng ở mục 3.
4. *Ba kết cục* của một lần chạy: thành công thì xoá job; lỗi mà còn lượt thì *release* (trả job về
   hàng đợi, có thể kèm thời gian chờ); lỗi mà hết lượt thì chuyển sang `failed_jobs` để con người xem.
5. Producer và worker là **hai process khác nhau**, có thể ở hai máy khác nhau. Chúng chỉ nói chuyện
   với nhau qua backend.

⚠️ Ví dụ trên thiếu một mảnh quan trọng: nếu worker **chết giữa chừng** (server mất điện, process bị
kill) thì job nằm mãi ở trạng thái reserved. Laravel giải quyết bằng `retry_after`: job reserved quá
N giây mà chưa bị xoá thì coi như worker đã chết, cho hiện lại. Mục 3.5 nói kỹ, vì đây là nguồn gốc của
nhiều lỗi khó.

### 1.4 Laravel thêm gì so với bản tự dựng

Queue của Laravel làm đúng những việc trên, cộng thêm rất nhiều thứ bạn không muốn tự viết:

| Bản tự dựng | Laravel |
|---|---|
| Một backend SQLite | Nhiều backend (*driver*) cùng một API: `database`, `redis`, `sqs`, `beanstalkd`... |
| `maxTries` cứng | `tries`, `backoff` tăng dần, `retryUntil`, `maxExceptions`, `timeout` khai báo trên từng job |
| Vòng `while` | Lệnh `php artisan queue:work`: xử lý tín hiệu dừng, giới hạn bộ nhớ, restart khi deploy |
| Không | Tự cứu job của worker chết (`retry_after`) |
| Không | Serialize model thông minh (chỉ lưu id, worker query lại) |
| Không | Unique job, rate limit, chống chạy chồng, chuỗi job (chain), lô job (batch) |
| Không | Dashboard theo dõi (Horizon), lệnh quản lý job lỗi (`queue:failed`, `queue:retry`) |

Phần còn lại của chương đi lần lượt qua từng thứ, rồi tới các thành phần khác thường đi chung với queue:
event, scheduler, cache, mail, notification, broadcasting.

## 2. Queue trong Laravel: cấu hình, job và dispatch

### 2.1 Connection và queue: hai khái niệm dễ lẫn

Mọi cấu hình queue nằm trong `config/queue.php`. Có hai khái niệm phải tách bạch ngay từ đầu:

- *Connection*: một backend cụ thể cộng cách nối tới nó. Ví dụ connection `redis` trỏ tới Redis server,
  connection `database` trỏ tới bảng `jobs`. Mỗi connection dùng một *driver*.
- *Queue*: tên một hàng đợi **bên trong** một connection. Một connection có thể chứa nhiều queue
  (`default`, `emails`, `high`...). Mỗi connection có khai báo `queue` mặc định: job không chỉ định queue
  thì vào đó.

```
config/queue.php
  default: env('QUEUE_CONNECTION', 'database')     <- connection dùng khi không chỉ định
  connections:
    database  (driver database, bảng jobs)          <- connection
      ├── queue "default"                           <- các queue bên trong
      └── queue "emails"
    redis     (driver redis)
      ├── queue "default"
      └── queue "high"
```

Trích phần cấu hình `database` và `redis` trong `config/queue.php` của project Laravel 13 mới tạo:

```php
'default' => env('QUEUE_CONNECTION', 'database'),

'connections' => [
    'sync' => [
        'driver' => 'sync',
    ],

    'database' => [
        'driver' => 'database',
        'connection' => env('DB_QUEUE_CONNECTION'),
        'table' => env('DB_QUEUE_TABLE', 'jobs'),
        'queue' => env('DB_QUEUE', 'default'),
        'retry_after' => (int) env('DB_QUEUE_RETRY_AFTER', 90),
        'after_commit' => false,
    ],

    'redis' => [
        'driver' => 'redis',
        'connection' => env('REDIS_QUEUE_CONNECTION', 'default'),
        'queue' => env('REDIS_QUEUE', 'default'),
        'retry_after' => (int) env('REDIS_QUEUE_RETRY_AFTER', 90),
        'block_for' => null,
        'after_commit' => false,
    ],
    // ... beanstalkd, sqs, deferred, background, failover
],
```

Các driver chính:

| Driver | Job nằm ở đâu | Dùng khi |
|---|---|---|
| `sync` | Không nằm đâu cả: chạy ngay trong process hiện tại | Dev, test. Không có xử lý nền thật |
| `database` | Bảng `jobs` của database | Mặc định của app mới. Không cần thêm hạ tầng; tải lớn thì bảng `jobs` thành điểm nóng |
| `redis` | Các key trong Redis (LIST, sorted set) | Production phổ biến nhất; bắt buộc nếu dùng Horizon |
| `sqs` | Amazon SQS | Hạ tầng AWS, không muốn tự vận hành Redis |
| `beanstalkd` | Beanstalkd server | Ít gặp |
| `null` | Bỏ job đi | Tắt queue hoàn toàn |
| `deferred` | Chạy trong cùng process, sau khi đã gửi response | Việc nhỏ, không cần worker |
| `background` | Chạy trong một process PHP riêng được sinh ra, sau khi gửi response | Như trên, nhưng giải phóng FPM worker sớm hơn |
| `failover` | Danh sách connection: đẩy vào cái đầu, lỗi thì thử cái tiếp | Dự phòng khi backend chính sập |

Driver `redis` cần extension phpredis hoặc package `predis/predis`; `sqs` cần `aws/aws-sdk-php`.

⚠️ Hai bẫy cấu hình hay gặp:

- `QUEUE_CONNECTION=sync` lọt lên production (copy `.env` của dev) thì mọi job chạy ngay trong request:
  không lỗi gì, chỉ là chậm, và người ta tưởng queue đang chạy. Lệnh `php artisan about` in ra driver
  queue đang dùng; nên kiểm tra sau khi deploy.
- `deferred` và `background` không đi qua backend nào và không có worker riêng: job chạy trong (hoặc cạnh)
  process web sau khi gửi response. Process chết giữa chừng là việc mất, không có `retry_after` nào cứu lại.
  Chỉ dùng cho việc mất cũng không sao (ghi thống kê, xoá cache).

### 2.2 Chuẩn bị driver database

Project Laravel mới đã có sẵn migration `0001_01_01_000002_create_jobs_table.php` tạo ba bảng: `jobs`
(job đang chờ), `job_batches` (dùng cho batch ở mục 4.4) và `failed_jobs` (job đã thất bại). Nếu project
thiếu migration này:

```bash
# chạy ở thư mục gốc project
php artisan make:queue-table
php artisan migrate
```

Bảng `jobs` có các cột giống hệt bản tự dựng ở mục 1.3: `id`, `queue`, `payload`, `attempts`,
`reserved_at`, `available_at`, `created_at`. Bạn có thể mở database ra xem từng job nằm đó sau khi
dispatch, rất tiện để học.

Cách driver `database` lấy job (đọc từ `DatabaseQueue::pop` trong mã nguồn 13.x):

1. Mở transaction.
2. `SELECT` dòng đầu tiên (theo `id` tăng dần) của queue cần lấy, thoả **một trong hai**: chưa ai giữ
   (`reserved_at IS NULL`) và đã tới giờ (`available_at <= now`); hoặc đã bị giữ quá `retry_after` giây
   (worker giữ nó có lẽ đã chết). Câu `SELECT` có kèm `FOR UPDATE SKIP LOCKED` trên MySQL 8.0.1+,
   MariaDB 10.6+, PostgreSQL 9.5+: dòng đang bị worker khác khoá thì bỏ qua, lấy dòng kế tiếp, thay vì
   đứng chờ.
3. `UPDATE` dòng đó: `reserved_at = now`, `attempts = attempts + 1`.
4. Commit.

Khi job chạy xong, worker `DELETE` dòng đó.

### 2.3 Viết job đầu tiên

```bash
# chạy ở thư mục gốc project
php artisan make:job SendWelcomeEmail
```

Lệnh tạo file `app/Jobs/SendWelcomeEmail.php`. Sửa lại như sau:

```php
<?php
declare(strict_types=1);

namespace App\Jobs;

use App\Mail\WelcomeMail;
use App\Models\User;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Mail;

final class SendWelcomeEmail implements ShouldQueue
{
    use Queueable;

    public function __construct(
        public User $user,
    ) {}

    public function handle(): void
    {
        Mail::to($this->user)->send(new WelcomeMail($this->user));
    }
}
```

Giải thích từng phần:

- `implements ShouldQueue`: interface đánh dấu (không có method nào). Nó báo cho Laravel "class này phải
  được đẩy vào queue". Thiếu nó, `dispatch()` sẽ chạy job **ngay lập tức** trong request, không báo lỗi
  gì. Đây là lỗi rất hay gặp khi tự viết job bằng tay thay vì dùng `make:job`.
- `use Queueable`: trait `Illuminate\Foundation\Queue\Queueable` gom bốn trait: `Dispatchable` (cho
  method tĩnh `dispatch()`), `InteractsWithQueue` (cho `$this->release()`, `$this->fail()`,
  `$this->attempts()`), `Queueable` của Bus (cho `onQueue()`, `delay()`...) và `SerializesModels`
  (mục 2.5).
- Constructor nhận dữ liệu job cần. Dữ liệu này được serialize vào payload.
- `handle()`: việc thật sự. Method này được gọi qua service container, nên có thể type-hint dependency
  làm tham số (`handle(AudioProcessor $processor)`), container tự inject
  ([Chương 26](26-laravel-container-provider-facade.md)).

⚠️ Chỉ đưa vào constructor những thứ serialize được: model, scalar, mảng, enum, object thường. Không đưa
closure, kết nối PDO, file handle, hay object client HTTP đang giữ socket. Dữ liệu nhị phân (nội dung
ảnh) phải `base64_encode` trước, vì payload là JSON và JSON không chứa được byte tuỳ ý (docs nêu rõ).

### 2.4 Dispatch: đẩy job vào queue

```php
use App\Jobs\SendWelcomeEmail;

// Cơ bản: connection mặc định, queue mặc định của connection đó
SendWelcomeEmail::dispatch($user);

// Có điều kiện
SendWelcomeEmail::dispatchIf($user->wantsEmail(), $user);
SendWelcomeEmail::dispatchUnless($user->isBot(), $user);

// Chỉ cho worker lấy sau 10 phút
SendWelcomeEmail::dispatch($user)->delay(now()->addMinutes(10));

// Chọn queue và connection
SendWelcomeEmail::dispatch($user)->onQueue('emails');
SendWelcomeEmail::dispatch($user)->onConnection('redis')->onQueue('emails');

// Chạy ngay trong process hiện tại, không qua queue
SendWelcomeEmail::dispatchSync($user);

// Hàm helper tương đương
dispatch(new SendWelcomeEmail($user));
```

Các tham số truyền vào `dispatch()` được chuyển thẳng cho constructor của job.

Cũng có thể đặt queue/connection mặc định ngay trong constructor của job (`$this->onQueue('emails');`),
hoặc khai báo tập trung trong `boot()` của một service provider bằng `Queue::route()` (docs 13.x):

```php
use App\Jobs\ProcessPodcast;
use Illuminate\Support\Facades\Queue;

Queue::route(ProcessPodcast::class, connection: 'redis', queue: 'podcasts');
```

`route()` nhận cả interface, trait hay class cha: mọi job khớp đều đi theo. Job tự khai queue/connection
thì ghi đè route.

⚠️ Một chi tiết bên trong gây bất ngờ: `SendWelcomeEmail::dispatch($user)` **chưa** đẩy job ngay. Nó trả
về một object `PendingDispatch`, và việc đẩy thật diễn ra trong **destructor** (`__destruct`) của object
đó (mã nguồn `Foundation/Bus/PendingDispatch.php`). Nhờ vậy bạn nối được `->delay()->onQueue()` sau
`dispatch()`. Bình thường object bị huỷ ngay cuối câu lệnh nên bạn không nhận ra. Nhưng nếu gán vào biến
(`$pending = SendWelcomeEmail::dispatch($user);`) thì job chỉ được đẩy khi biến đó bị huỷ, tức muộn hơn
bạn nghĩ. Đừng giữ kết quả của `dispatch()` trong biến.

Một job cần dispatch hàng loạt (hàng nghìn user) mà không cần theo dõi chung thì dùng `Bus::bulk()`:
Laravel gom theo connection/queue rồi đẩy mỗi nhóm một lần.

```php
use App\Jobs\ProcessUser;
use Illuminate\Support\Facades\Bus;

Bus::bulk($users->map(fn (User $u): ProcessUser => new ProcessUser($u)));
```

### 2.5 Model trong job: SerializesModels

Khi job có property là Eloquent model, trait `SerializesModels` không serialize toàn bộ model (mọi cột,
mọi quan hệ đã nạp). Nó thay model bằng một object `ModelIdentifier` nhỏ chứa tên class, khoá chính,
tên các quan hệ đã nạp và tên connection database. Khi worker unserialize job, model được **query lại**
từ database.

Ví dụ PHP thuần sau mô phỏng đúng ý tưởng đó bằng `__serialize`/`__unserialize` (hai magic method ở
[Chương 10](10-oop-nang-cao.md)):

```php
<?php
declare(strict_types=1);

// PHP thuần: mô phỏng ý tưởng của trait SerializesModels.
// "Database" là một mảng tĩnh; Order là một "model" tí hon.

final class FakeDb
{
    /** @var array<int, array{status: string, total: int}> */
    public static array $orders = [];
}

final class Order
{
    public function __construct(public int $id, public string $status, public int $total) {}

    public static function find(int $id): ?self
    {
        $row = FakeDb::$orders[$id] ?? null;
        return $row === null ? null : new self($id, $row['status'], $row['total']);
    }
}

// Thứ thật sự được ghi vào payload thay cho cả model
final class ModelIdentifier
{
    public function __construct(public string $class, public int $id) {}
}

final class ShipOrder
{
    public function __construct(public Order $order) {}

    /** @return array<string, mixed> */
    public function __serialize(): array
    {
        // Chỉ lưu class + id, bỏ toàn bộ dữ liệu của model
        return ['order' => new ModelIdentifier(Order::class, $this->order->id)];
    }

    /** @param array<string, mixed> $data */
    public function __unserialize(array $data): void
    {
        $order = Order::find($data['order']->id);   // query lại lúc worker chạy
        if ($order === null) {
            throw new RuntimeException('ModelNotFound: order ' . $data['order']->id);
        }
        $this->order = $order;
    }
}

FakeDb::$orders[7] = ['status' => 'paid', 'total' => 500_000];

$payload = serialize(new ShipOrder(Order::find(7)));   // lúc dispatch
echo $payload, "\n";
// in ra: O:9:"ShipOrder":1:{s:5:"order";O:15:"ModelIdentifier":2:{s:5:"class";s:5:"Order";s:2:"id";i:7;}}

FakeDb::$orders[7]['status'] = 'cancelled';             // dữ liệu đổi trước khi worker chạy

$job = unserialize($payload);                           // lúc worker chạy
echo $job->order->status, "\n";
// in ra: cancelled

unset(FakeDb::$orders[7]);                              // model bị xoá
try {
    unserialize($payload);
} catch (RuntimeException $e) {
    echo $e->getMessage(), "\n";
}
// in ra: ModelNotFound: order 7
```

Hệ quả thực tế trong Laravel:

- Payload nhỏ, và job luôn thấy dữ liệu **mới nhất lúc chạy**, không phải lúc dispatch. Nếu cần giá trị
  tại thời điểm dispatch (giá lúc đặt hàng, trạng thái lúc bấm nút), truyền giá trị đó dạng scalar vào
  constructor.
- Mã nguồn 13.x query lại model bằng `useWritePdo()`: nếu app có read replica, worker vẫn đọc từ primary,
  nên không dính độ trễ replica khi khôi phục model (truy vấn khác bạn tự viết trong `handle()` thì vẫn có
  thể đi vào replica).
- Model bị xoá trước khi job chạy thì job ném `ModelNotFoundException` (và thất bại) trước cả khi vào
  `handle()`. Nếu muốn job âm thầm bị bỏ trong trường hợp đó, gắn attribute `#[DeleteWhenMissingModels]`
  lên class job (hoặc property kiểu cũ `public $deleteWhenMissingModels = true;`).
- Quan hệ đã nạp được nạp lại **toàn bộ**: ràng buộc lúc eager load (`with(['comments' => fn ($q) =>
  $q->where('approved', true)])`) bị mất. Muốn không mang quan hệ theo, dùng `$model->withoutRelations()`,
  hoặc attribute `#[WithoutRelations]` trên tham số constructor hay trên cả class.
- Job nhận một Eloquent collection: các model được query lại bằng **một** câu (theo danh sách id). Từ
  Laravel 13, quan hệ đã eager load của các model trong collection **cũng được nạp lại**: mã nguồn 13.x
  (`restoreCollection` trong `SerializesAndRestoresModelIdentifiers`) gọi `loadMissing()` với danh sách
  tên quan hệ, tức eager load mỗi quan hệ bằng một query cho cả collection. Danh sách đó chỉ gồm những
  quan hệ đã nạp trên **mọi** model của collection (phần giao), và ràng buộc lúc eager load cũng bị mất như
  với một model. Upgrade guide 13.x ghi đúng thay đổi này ("Collection Model Serialization Restores
  Eager-Loaded Relations"); trang Queues của docs 13.x vẫn còn câu cũ từ các bản trước ("will not have
  their relationships restored"), đừng dựa vào câu đó. Ở Laravel 12 trở về trước, quan hệ của phần tử
  trong collection không được nạp lại, nên truy cập quan hệ trong job dễ thành N+1
  ([Chương 27](27-laravel-database-eloquent.md)).

Payload thật mà Laravel ghi vào cột `payload` là JSON có dạng sau (output minh hoạ, giá trị `uuid` và chuỗi
`command` rút gọn; tên khoá lấy từ `Queue::createObjectPayload` trong mã nguồn 13.x):

```json
{
  "uuid": "9f1c...",
  "displayName": "App\\Jobs\\SendWelcomeEmail",
  "job": "Illuminate\\Queue\\CallQueuedHandler@call",
  "maxTries": null,
  "maxExceptions": null,
  "failOnTimeout": false,
  "countCrashesAsExceptions": false,
  "backoff": null,
  "timeout": null,
  "retryUntil": null,
  "deleteWhenMissingModels": false,
  "data": {
    "commandName": "App\\Jobs\\SendWelcomeEmail",
    "command": "O:25:\"App\\Jobs\\SendWelcomeEmail\":1:{s:4:\"user\";O:45:\"Illuminate\\Contracts\\Database\\ModelIdentifier\":5:{...}}",
    "batchId": null
  },
  "createdAt": 1790000000
}
```

(Driver `redis` thêm hai khoá `id` và `attempts` vào payload, vì Redis không có cột riêng cho chúng.)

Để ý: cấu hình `tries`, `backoff`, `timeout` của job được chụp lại **lúc dispatch** và ghi vào payload.
Sửa `#[Tries(5)]` trong code rồi deploy thì các job đã nằm trong queue từ trước vẫn mang giá trị cũ.

### 2.6 Dispatch trong transaction: afterCommit

Đây là lỗi kinh điển. Code đặt hàng:

```php
DB::transaction(function () use ($data): void {
    $order = Order::create($data);
    SendOrderConfirmation::dispatch($order);   // job đi vào queue NGAY
    $order->items()->createMany($data['items']);
});
```

Job được đẩy vào queue ngay khi gọi `dispatch()`, trong khi transaction **chưa commit**. Worker rảnh có
thể lấy job trong vài mili giây:

| Bước | Request (trong transaction) | Worker | Kết quả |
|---|---|---|---|
| 1 | `INSERT orders` (chưa commit) | | Dòng mới chỉ thấy được bên trong transaction của request |
| 2 | `dispatch()`: job vào Redis ngay | | |
| 3 | `INSERT order_items`... | Lấy job, unserialize: `SELECT * FROM orders WHERE id = ?` | Không thấy dòng chưa commit (xem [Transaction và ACID](../database/13-transaction-acid.md)): `ModelNotFoundException`, job thất bại |
| 4 | Commit | | Đơn hàng có thật, nhưng job gửi email đã thất bại |

Kịch bản ngược lại cũng tệ: transaction **rollback** (bước `INSERT order_items` lỗi) nhưng job đã nằm trong
queue. Nếu job chỉ mang dữ liệu scalar (email, mã đơn) thay vì model, nó chạy thành công và khách nhận
email xác nhận cho một đơn hàng không tồn tại.

Vấn đề xuất hiện khi job được ghi ra một nơi **nằm ngoài** transaction: Redis, SQS, hay một connection
database khác. (Nếu dùng driver `database` trên đúng connection đang mở transaction thì câu INSERT vào
bảng `jobs` cũng thuộc transaction đó, nên job chỉ hiện ra khi commit. Đừng dựa vào sự tình cờ này: đổi
sang Redis là lỗi lộ ra.)

Cách sửa:

```php
// Cho một job
SendOrderConfirmation::dispatch($order)->afterCommit();

// Cho cả connection: config/queue.php
'redis' => [
    // ...
    'after_commit' => true,
],
// khi đó job nào cần đẩy ngay thì dùng ->beforeCommit()
```

Với `afterCommit`, Laravel giữ job lại tới khi **mọi** transaction đang mở commit xong mới đẩy; transaction
rollback thì job bị bỏ. Không có transaction nào đang mở thì job được đẩy ngay như bình thường. Docs ghi
rằng `after_commit => true` cũng áp cho queued listener, mailable, notification và broadcast event.

⚠️ `afterCommit` vẫn để hở một khe nhỏ: transaction commit xong, process chết trước khi kịp đẩy job thì
job mất. Hệ thống cần đảm bảo tuyệt đối (thanh toán) dùng *transactional outbox*: ghi "việc cần làm" vào
một bảng trong **cùng** transaction, rồi một process khác đọc bảng đó và đẩy vào queue.

## 3. Worker: chạy job và xử lý lỗi

### 3.1 `queue:work` và `queue:listen`

Job nằm trong queue sẽ không tự chạy. Cần ít nhất một worker:

```bash
# chạy ở thư mục gốc project; process này chạy mãi tới khi bị dừng (Ctrl+C)
php artisan queue:work

# chỉ định connection và các queue cần xử lý
php artisan queue:work redis --queue=emails

# in thêm id job, connection, queue cho mỗi job
php artisan queue:work -v
```

Điểm khác biệt quan trọng nhất với code web: `queue:work` boot framework **một lần**, rồi lặp mãi để xử
lý hết job này tới job khác trong **cùng một process**. Trái với mô hình FPM "mỗi request khởi động sạch"
ở [Chương 18](18-fpm-nginx-opcache.md), hệ quả là:

- Nhanh, vì không phải boot lại cho mỗi job.
- Code đã nạp vào bộ nhớ không đổi: sửa code rồi deploy mà không restart worker thì worker vẫn chạy code
  cũ (mục 3.8).
- Trạng thái tĩnh (`static` property, singleton giữ dữ liệu) **không được reset** giữa các job. Job trước
  để lại gì, job sau thấy nấy. Bộ nhớ rò rỉ tích dần.

`php artisan queue:listen` thì boot lại framework cho **mỗi** job: không cần restart khi sửa code, nhưng
chậm hơn nhiều. Chỉ dùng khi phát triển ở máy cá nhân.

Muốn xử lý song song, chạy **nhiều process** `queue:work`. Một process chỉ xử lý một job tại một thời
điểm (PHP không có thread trong worker như Java).

Các tuỳ chọn của `queue:work` (giá trị mặc định đọc từ chữ ký lệnh trong `Queue/Console/WorkCommand.php`
13.x):

| Tuỳ chọn | Mặc định | Ý nghĩa |
|---|---|---|
| `--queue=high,default` | Queue mặc định của connection | Danh sách queue, theo thứ tự ưu tiên |
| `--tries` | 1 | Số attempt tối đa cho job không tự khai báo; `0` là không giới hạn |
| `--backoff` | 0 | Số giây chờ trước khi thử lại job vừa ném exception |
| `--timeout` | 60 | Số giây tối đa cho một job |
| `--sleep` | 3 | Số giây nghỉ khi queue trống, trước khi hỏi lại |
| `--memory` | 128 | MB; worker dùng quá thì thoát sau job hiện tại |
| `--max-jobs` | 0 (tắt) | Xử lý N job rồi thoát |
| `--max-time` | 0 (tắt) | Chạy N giây rồi thoát |
| `--stop-when-empty` | tắt | Hết job thì thoát (hợp với container chạy theo lô) |
| `--once` | tắt | Chỉ xử lý một job rồi thoát |
| `--force` | tắt | Vẫn chạy khi app đang ở maintenance mode (mặc định worker không lấy job lúc đó) |

`--max-jobs`, `--max-time`, `--memory` khiến worker tự thoát định kỳ, để process manager khởi động lại
một process sạch, giải phóng bộ nhớ đã rò. Đây là cách phòng thủ đơn giản cho bản chất "process sống lâu"
của worker.

Về *thứ tự ưu tiên* `--queue=high,default,low`: worker luôn hỏi `high` trước, chỉ khi `high` trống mới
hỏi `default`, rồi mới tới `low`. ⚠️ Đây là ưu tiên tuyệt đối (*strict priority*): nếu `high` lúc nào cũng
có job thì `low` không bao giờ được chạy (*starvation*). Muốn chắc chắn `low` vẫn tiến triển, cấp cho nó
worker riêng.

### 3.2 Vòng đời của một attempt

Mỗi vòng lặp của worker (đọc từ `Queue/Worker.php` 13.x, đơn giản hoá):

```
vòng lặp daemon
 ├─ 1. queue đang bị pause? app maintenance? -> nghỉ, quay lại
 ├─ 2. pop(): lấy một job, attempts++ ngay lúc lấy, đánh dấu reserved
 │      không có job -> sleep(--sleep) rồi quay lại
 ├─ 3. hẹn giờ: pcntl_alarm(timeout)  (mục 3.4)
 ├─ 4. attempts đã vượt tries (hoặc quá retryUntil)? -> đánh dấu failed, không chạy
 ├─ 5. unserialize payload -> chạy job middleware -> handle()
 │      ├─ OK            -> xoá job khỏi queue
 │      ├─ release(N)    -> trả về queue, hiện lại sau N giây
 │      └─ exception     -> còn lượt: release với backoff; hết lượt: failed
 ├─ 6. huỷ hẹn giờ
 └─ 7. kiểm tra: có lệnh restart? vượt --memory? --max-jobs? --max-time? -> thoát
        (exit code 0; riêng vượt --memory là exit code 12)
```

Khái niệm *attempt* hay bị hiểu sai. Theo docs, một attempt bị "tiêu" khi:

- job ném exception chưa được bắt;
- job tự gọi `$this->release()`;
- job middleware như `WithoutOverlapping` hay `RateLimited` không lấy được lock và release job;
- job bị timeout;
- job chạy xong không lỗi.

Nói cách khác, attempt là "một lần được lấy ra khỏi queue", **không** phải "một lần `handle()` chạy lỗi".
Và vì `attempts` tăng ngay lúc lấy ra (bước 2), worker chết giữa chừng thì lần lấy sau đã là attempt 2.

⚠️ Mặc định Laravel chỉ thử **một** lần (`--tries=1`). Job dùng `RateLimited` hay `WithoutOverlapping`
mà để mặc định thì: lần đầu bị release vì vượt rate limit, lần lấy sau attempts = 2 > 1, job thất bại dù
`handle()` **chưa từng chạy**. Docs nhắc chính trường hợp này.

### 3.3 Thử lại: tries, backoff, retryUntil, maxExceptions

Từ Laravel 13, cách viết được docs dùng là *attribute* PHP đặt trên class job (attribute ở
[Chương 10](10-oop-nang-cao.md)). Cách cũ bằng property (`public $tries = 5;`) và bằng method
(`public function tries(): int`) vẫn dùng được; method hợp khi cần tính giá trị động.

```php
<?php
declare(strict_types=1);

namespace App\Jobs;

use App\Models\Order;
use App\Services\ErpClient;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\Attributes\Backoff;
use Illuminate\Queue\Attributes\MaxExceptions;
use Illuminate\Queue\Attributes\Timeout;
use Illuminate\Queue\Attributes\Tries;
use Throwable;

#[Tries(10)]                 // tối đa 10 attempt (tính cả lần bị release vì rate limit)
#[MaxExceptions(3)]          // nhưng chỉ chịu tối đa 3 lần ném exception thật
#[Backoff([10, 60, 300])]    // sau exception: chờ 10s, rồi 60s, rồi 300s cho mọi lần sau
#[Timeout(120)]              // một attempt chạy quá 120s thì bị kill
final class SyncOrderToErp implements ShouldQueue
{
    use Queueable;

    public function __construct(public Order $order) {}

    public function handle(ErpClient $erp): void
    {
        $erp->push($this->order);
    }

    public function failed(?Throwable $exception): void
    {
        // Gọi khi job thất bại hẳn: báo cho đội vận hành, hoàn tác phần đã làm...
    }
}
```

- *Tries*: số attempt tối đa. Giá trị trên job thắng `--tries` của worker. Hết lượt thì job thất bại.
  Ngoại lệ truyền vào `failed()` tuỳ cách hết lượt (docs): attempt cuối ném exception thì `failed()` nhận
  chính exception đó; job bị lấy ra khi số attempt đã vượt giới hạn (sau release, sau khi worker chết) thì
  nhận `MaxAttemptsExceededException`; hết lượt vì timeout thì nhận `TimeoutExceededException`.
- *Backoff*: số giây chờ trước khi thử lại, **chỉ** áp dụng khi job ném exception (`release(N)` thì tự
  chọn N). Mảng `[10, 60, 300]` nghĩa là lần thử lại thứ nhất chờ 10 giây, thứ hai 60 giây, từ thứ ba trở
  đi 300 giây (docs: hết phần tử thì dùng mãi phần tử cuối). Khoảng chờ tăng dần cho dịch vụ ngoài thời
  gian hồi phục, thay vì dội liên tục vào nó.
- *retryUntil()*: thay vì đếm số lần, cho phép thử bao nhiêu lần cũng được **tới một thời điểm**. Có cả
  `retryUntil` và `Tries` thì `retryUntil` được ưu tiên.

  ```php
  public function retryUntil(): \DateTimeInterface
  {
      return now()->addMinutes(30);
  }
  ```

- *MaxExceptions*: chỉ đếm những lần job ném exception, không đếm những lần bị release. Cặp
  `#[Tries(25)] #[MaxExceptions(3)]` nghĩa là "được release chờ rate limit nhiều lần, nhưng lỗi thật 3 lần
  là thôi".
- Dừng thử lại sớm khi biết chắc lỗi là vĩnh viễn (dữ liệu sai, user bị thu hồi quyền): gọi
  `$this->fail($e)` trong `handle()`, hoặc khai báo `$exceptions->dontRetry([...])` trong
  `bootstrap/app.php`, hoặc dùng job middleware `FailOnException([...])`. Thử lại một lỗi vĩnh viễn chỉ phí
  tài nguyên và làm chậm queue.

Tự trả job về queue trong `handle()`:

```php
public function handle(): void
{
    if (! $this->partnerIsAvailable()) {
        $this->release(30);   // thử lại sau 30 giây; vẫn tốn một attempt
        return;
    }
    // ...
}
```

### 3.4 Timeout hoạt động thế nào

Timeout chặn một job treo (chờ một API không bao giờ trả lời) giữ worker mãi mãi. Bên trong (đọc từ
`Worker::registerTimeoutHandler` 13.x):

1. Trước khi chạy job, worker đăng ký hàm xử lý cho tín hiệu `SIGALRM`, rồi gọi `pcntl_alarm($timeout)`:
   nhờ hệ điều hành gửi `SIGALRM` cho chính process sau `$timeout` giây.
2. Job xong sớm thì alarm bị huỷ.
3. Hết giờ mà job chưa xong: hàm xử lý chạy. Nó đánh dấu job thất bại nếu đây là attempt cuối (hoặc job
   có `#[FailOnTimeout]`), bắn event `JobTimedOut`, rồi **giết chính process worker** bằng
   `posix_kill(getmypid(), SIGKILL)` (không có extension `posix` thì gọi `exit()`).

Hệ quả cần nhớ:

- ⚠️ Cần extension `pcntl` (chỉ có trên Linux/macOS, bản CLI). Không có `pcntl` thì timeout không có tác
  dụng. Docs cũng ghi `--timeout` không có tác dụng khi chạy với `--once`.
- Timeout không "huỷ job": nó giết **cả worker**. Phải có process manager (mục 3.8) để khởi động lại.
- Job bị giết **không** được trả về queue ngay. Nó vẫn đang ở trạng thái reserved, và chỉ hiện lại khi
  quá `retry_after` (mục 3.5). Khi đó nó được lấy lại như một attempt mới.
- `SIGKILL` không bắt được, nên khối `finally` trong job **không chạy**: lock bạn tự lấy trong job sẽ không
  được nhả. Nhớ điều này khi đọc về `WithoutOverlapping` ở mục 4.2.
- Một số thao tác I/O chặn (socket, HTTP) có thể không bị ngắt đúng giờ. Docs khuyên luôn đặt timeout
  riêng cho chính thao tác đó, ví dụ `Http::timeout(10)->connectTimeout(3)->get(...)`.
- Mặc định job timeout thì tốn một attempt và được thử lại nếu còn lượt. Thêm `#[FailOnTimeout]` để thất
  bại luôn, không thử lại.

### 3.5 retry_after và timeout: hai con số phải đi cùng nhau

Nhắc lại vấn đề còn bỏ ngỏ ở mục 1.3: worker chết giữa chừng (máy sập, bị OOM killer giết) thì job nằm
mãi ở trạng thái reserved. Laravel xử lý bằng `retry_after` khai báo cho từng connection trong
`config/queue.php` (mặc định 90 giây trong project mới). Ý nghĩa: job đã được lấy ra quá `retry_after`
giây mà chưa bị xoá hay release thì queue coi như worker đã chết, cho job hiện lại để worker khác lấy.
(SQS là ngoại lệ: không có `retry_after`, thay bằng *visibility timeout* cấu hình bên AWS.)

Hai con số rất dễ lẫn:

| | `retry_after` | `timeout` |
|---|---|---|
| Đặt ở đâu | `config/queue.php`, từng connection | `--timeout` của worker (mặc định 60) hoặc `#[Timeout]` trên job |
| Ai thực thi | Phía **queue**: job reserved quá N giây thì cho hiện lại | Phía **worker**: job chạy quá N giây thì worker tự kill |
| Mục đích | Cứu job của worker đã chết | Không để job treo giữ worker mãi |

Queue không biết worker còn sống hay không. Nó chỉ biết "job này được lấy ra lúc T". Vì vậy nếu một job
**chạy bình thường** nhưng lâu hơn `retry_after`, queue sẽ tưởng worker đã chết và giao job cho worker khác,
trong khi worker đầu vẫn đang chạy.

Tình huống: `retry_after = 90`, job gửi email rồi gọi API, tổng cộng mất 120 giây, `#[Timeout(150)]`,
`#[Tries(3)]`, hai worker A và B, driver `redis` (với Redis, mỗi lần job được lấy lại là một bản ghi reserved
mới, nên lệnh xoá của worker cũ không chạm được bản của worker mới).

| Giây | Worker A | Worker B | Trạng thái job |
|---|---|---|---|
| 0 | Lấy job, attempts = 1, bắt đầu chạy | Rảnh | Reserved, "hết hạn" ở giây 90 |
| 5 | Gửi email lần 1 | | |
| 90 | Vẫn đang gọi API | Thấy job reserved đã quá hạn: lấy job, attempts = 2, bắt đầu chạy | Reserved lại, hết hạn ở giây 180 |
| 95 | | Gửi email **lần 2** | |
| 120 | Xong, xoá job (bản ghi đã bị B lấy lại, nên xoá không còn tác dụng gì) | Vẫn chạy | |
| 180 | Rảnh, thấy job quá hạn: lấy, attempts = 3, chạy | Vẫn chạy | Reserved, hết hạn ở giây 270 |
| 185 | Gửi email **lần 3** | | |
| 210 | | Xong | |
| 270 | | Thấy job quá hạn: lấy, attempts = 4 > 3, đánh dấu **failed** | Ghi vào `failed_jobs` |

Email được gửi ba lần, và cuối cùng job còn nằm trong `failed_jobs` dù mọi lần chạy đều thành công. Log
không có exception nào từ `handle()`. Đây là loại lỗi rất khó chẩn đoán nếu không biết cơ chế.

Với driver `database`, diễn biến chi tiết khác một chút: worker xoá job theo `id` của dòng trong bảng `jobs`, nên ở
giây 120 A xoá luôn dòng mà B đang giữ, và job không bị lấy lần thứ ba. Nhưng job vẫn đã chạy **hai lần** song
song (email gửi hai lần). Kết luận không đổi: chạy chồng là do `timeout` ≥ `retry_after`, driver nào cũng vậy.

Biến thể với mặc định `tries = 1`: ở giây 90, B lấy job ra với attempts = 2 > 1, nên đánh dấu job thất bại
ngay (gọi `failed()` với `MaxAttemptsExceededException`) trong khi A vẫn đang chạy và sẽ thành công. Nếu
`failed()` làm việc bù trừ (hoàn tiền, huỷ đơn) thì hậu quả còn nặng hơn.

Quy tắc đúng (docs: `timeout` phải ngắn hơn `retry_after` "ít nhất vài giây"):

```
timeout của job dài nhất  <  retry_after của connection      (cách nhau vài giây trở lên)
timeout của job dài nhất  <  stopwaitsecs của Supervisor      (mục 3.8)
SQS: timeout              <  visibility timeout của queue
```

Với cấu hình đúng, ví dụ `#[Timeout(150)]` và `retry_after = 180`, một job treo diễn ra thế này: giây 150
worker tự kill; giây 180 job hiện lại, một worker khác lấy với attempts = 2. Không lúc nào có hai worker cùng
chạy một job.

⚠️ Đừng tăng `retry_after` cho mọi job chỉ vì có một loại job dài (import file lớn). `retry_after` lớn nghĩa
là job của worker chết thật phải chờ lâu mới được cứu. Hãy tạo một connection riêng (cùng Redis, khác tên)
với `retry_after` lớn và đưa loại job dài vào đó.

### 3.6 Job thất bại

Job thất bại khi hết attempt, hết `retryUntil`, quá `MaxExceptions`, timeout với `FailOnTimeout`, hoặc tự
gọi `$this->fail()`. Khi đó:

1. Worker ghi job vào bảng `failed_jobs` (có `uuid`, connection, queue, payload, nội dung exception,
   thời điểm). Chỉ job chạy qua worker mới được ghi; job `dispatchSync` hay driver `sync` ném exception
   thẳng ra cho code gọi.
2. Method `failed(?Throwable $exception)` của job (nếu có) được gọi.

⚠️ `failed()` chạy trên một **instance mới** của job (docs nêu rõ): property bạn gán trong `handle()` đã mất.

Các lệnh quản lý:

| Lệnh | Việc |
|---|---|
| `php artisan queue:failed` | Liệt kê job lỗi: id, connection, queue, thời điểm |
| `php artisan queue:retry <uuid> [<uuid>...]` | Đẩy lại các job đó vào queue |
| `php artisan queue:retry --queue=emails` | Đẩy lại mọi job lỗi của một queue |
| `php artisan queue:retry all` | Đẩy lại tất cả |
| `php artisan queue:forget <uuid>` | Xoá một job lỗi |
| `php artisan queue:flush` | Xoá mọi job lỗi (`--hours=48`: chỉ xoá bản ghi cũ hơn 48 giờ) |
| `php artisan queue:prune-failed` | Xoá bản ghi cũ hơn 24 giờ (mặc định), nên chạy theo lịch |

Thói quen tốt: theo dõi số dòng `failed_jobs` (hoặc lắng nghe event `JobFailed`) và cảnh báo khi tăng.
Job thất bại mà không ai biết thì cũng như việc không bao giờ được làm.

### 3.7 Idempotent: vì sao job phải chạy lại được an toàn

*Idempotent* (lũy đẳng): chạy một lần hay nhiều lần đều cho cùng một kết quả. "Đặt trạng thái đơn thành
`paid`" là idempotent; "cộng 100.000 vào số dư" thì không.

Job **phải** được viết idempotent, vì có nhiều đường khiến nó chạy lại mà không cấu hình nào chặn hết:

1. Retry sau exception, kể cả khi exception xảy ra **sau** bước có tác dụng phụ (đã trừ tiền xong mới lỗi
   lúc ghi log).
2. `retry_after` ngắn hơn thời gian chạy (mục 3.5).
3. Worker bị kill sau khi làm xong việc nhưng **trước khi** kịp xoá job khỏi queue.
4. Nhiều broker (như SQS) chỉ đảm bảo *at-least-once delivery*: giao ít nhất một lần, có thể nhiều hơn.
5. Người vận hành chạy `queue:retry all` sau sự cố, kể cả với job thật ra đã làm xong một nửa.

Các kỹ thuật thường dùng:

```php
public function handle(PaymentGateway $gateway): void
{
    // 1. Kiểm tra trạng thái trước khi làm
    if ($this->order->fresh()->status === OrderStatus::Paid) {
        return;
    }

    // 2. Idempotency key gửi cho đối tác: cổng thanh toán nhận cùng key hai lần thì trả kết quả lần trước
    $charge = $gateway->charge(
        $this->order->total,
        idempotencyKey: 'order-charge-' . $this->order->id,
    );

    // 3. UPDATE có điều kiện: chỉ một lần chuyển trạng thái thành công
    Order::whereKey($this->order->id)
        ->where('status', OrderStatus::Pending)
        ->update(['status' => OrderStatus::Paid, 'charge_id' => $charge->id]);
}
```

Thêm một kỹ thuật nữa: unique index trong database. Ví dụ bảng `sent_emails (order_id, type)` có UNIQUE;
job INSERT trước khi gửi, INSERT bị trùng thì biết đã gửi rồi và bỏ qua.

### 3.8 Chạy worker trên production: Supervisor, restart, tín hiệu

Worker phải chạy liên tục, và tự sống lại khi thoát (do timeout, `--max-time`, vượt `--memory`, hay lệnh
restart). Trên Linux, công cụ phổ biến là *Supervisor* (một chương trình quản lý process, không liên quan
tới "supervisor" của Horizon ở mục 5). Ví dụ cấu hình theo docs:

```ini
; /etc/supervisor/conf.d/laravel-worker.conf
[program:laravel-worker]
process_name=%(program_name)s_%(process_num)02d
command=php /var/www/app/artisan queue:work redis --sleep=3 --tries=3 --max-time=3600
autostart=true
autorestart=true          ; worker thoát vì bất kỳ lý do gì thì chạy lại
stopasgroup=true
killasgroup=true
user=www-data
numprocs=8                ; 8 worker song song
redirect_stderr=true
stdout_logfile=/var/www/app/storage/logs/worker.log
stopwaitsecs=3600         ; khi dừng: chờ tối đa 3600 giây cho worker tự thoát, quá thì SIGKILL
```

```bash
# chạy trên server, với quyền root
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start "laravel-worker:*"
```

⚠️ `stopwaitsecs`: khi dừng hoặc restart chương trình, Supervisor gửi `SIGTERM`, chờ `stopwaitsecs` giây,
quá hạn thì `SIGKILL`. Mặc định của Supervisor chỉ là 10 giây. Job chạy 2 phút gặp deploy sẽ bị giết giữa
chừng mỗi lần deploy. Docs yêu cầu `stopwaitsecs` lớn hơn thời gian chạy của job dài nhất. Trên
Kubernetes, tương đương là `terminationGracePeriodSeconds` của pod.

*Restart khi deploy.* Worker giữ code cũ trong bộ nhớ, nên sau mỗi lần deploy phải restart:

```bash
# chạy ở thư mục gốc project, trong script deploy
php artisan queue:restart
```

Lệnh này **không** giết worker. Cơ chế:

1. Ghi thời điểm hiện tại vào **cache**, key `illuminate:queue:restart`.
2. Mỗi worker đọc key này lúc khởi động, và sau mỗi vòng lặp đọc lại để so sánh.
3. Thấy giá trị đổi, worker thoát êm **sau khi làm xong job hiện tại** (exit code 0).
4. Supervisor thấy process thoát thì khởi động lại; process mới nạp code mới.

⚠️ Hai điều kiện để cơ chế này hoạt động: có process manager (không có thì `queue:restart` chỉ làm worker
tắt hẳn), và cache phải **dùng chung** giữa mọi server chạy worker (Redis, database). Cache `file` thì mỗi
server một bản, lệnh chạy ở server A không báo được cho worker ở server B.

*Tín hiệu dừng.* Worker nhận `SIGTERM`, `SIGINT` hoặc `SIGQUIT` thì làm xong job hiện tại rồi thoát. Job dài
(import hàng triệu dòng) muốn phản ứng sớm, ví dụ lưu tiến độ rồi dừng, thì `implements Interruptible` và
viết method `interrupted(int $signal)` (docs 13.x).

⚠️ Với Redis, `block_for => 0` làm worker chặn vô thời hạn để chờ job, và docs cảnh báo khi đó tín hiệu như
`SIGTERM` không được xử lý cho tới khi có job tiếp theo.

Tạm dừng lấy job mà không dừng worker (khi bảo trì một hệ thống phía sau):
`php artisan queue:pause redis:default` và `php artisan queue:continue redis:default`.

Đối chiếu với ngôn ngữ khác: Java (Spring) và Go thường dùng broker như RabbitMQ, Kafka, với consumer là
thread hoặc goroutine trong một process sống lâu; một message treo thường được xử lý bằng *ack timeout*
của broker. Mô hình "mỗi worker là một process PHP, tự kill khi timeout, queue tự cứu job sau
`retry_after`" là đặc thù của PHP. Tương đương của `retry_after` bên các broker khác là visibility timeout
(SQS) hay consumer ack timeout (RabbitMQ).

## 4. Điều phối job: unique, middleware, chain, batch

### 4.1 Unique job: không cho job trùng nằm trong queue

Tình huống: mỗi lần sản phẩm được sửa, app dispatch job cập nhật chỉ mục tìm kiếm. Người quản trị sửa một
sản phẩm 20 lần trong một phút, sinh ra 20 job làm cùng một việc. Chỉ cần một là đủ.

```php
<?php
declare(strict_types=1);

namespace App\Jobs;

use App\Models\Product;
use Illuminate\Contracts\Queue\ShouldBeUnique;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Queue\Attributes\UniqueFor;

#[UniqueFor(3600)]   // khoá "duy nhất" tự hết hạn sau 1 giờ nếu job chưa xong
final class UpdateSearchIndex implements ShouldQueue, ShouldBeUnique
{
    use Queueable;

    public function __construct(public Product $product) {}

    // Hai job có cùng uniqueId (và cùng class) bị coi là trùng
    public function uniqueId(): string
    {
        return (string) $this->product->id;
    }

    public function handle(): void
    {
        // ...
    }
}
```

Bên dưới (đọc từ `Bus/UniqueLock.php` 13.x):

1. Lúc dispatch, Laravel xin một *cache lock* (mục 8.4) với key `laravel_unique_job:<tên class>:<uniqueId>`,
   thời hạn bằng `uniqueFor` giây.
2. Xin không được (đã có job cùng key đang chờ hoặc đang chạy) thì job **lặng lẽ không được dispatch**:
   không exception, không log.
3. Lock được nhả khi job chạy xong hoặc thất bại hẳn. Nếu dùng `ShouldBeUniqueUntilProcessing` thay cho
   `ShouldBeUnique`, lock được nhả ngay **khi job bắt đầu chạy**: trong lúc job đang chạy đã dispatch được
   bản mới.

⚠️ Cạm bẫy:

- Không đặt `uniqueFor` thì lock không có thời hạn. Nếu job "biến mất" mà lock không được nhả (ai đó xoá tay
  dữ liệu trong Redis), mọi job cùng key sẽ không bao giờ dispatch được nữa.
- Lock nằm trong cache, nên cache phải hỗ trợ lock và phải **dùng chung** giữa mọi server dispatch job. Docs
  liệt kê driver hỗ trợ lock: `memcached`, `redis`, `dynamodb`, `database`, `file`, `array` (hai cái cuối chỉ
  có nghĩa trong một máy). Muốn dùng store khác store mặc định, định nghĩa method `uniqueVia()`.
- Ràng buộc unique **không** áp dụng cho job nằm trong batch (docs).

### 4.2 Job middleware

*Job middleware* bọc quanh `handle()`, giống middleware HTTP ở [Chương 24](24-laravel-routing-controller-middleware.md):
nhận job và một closure `$next`, quyết định có cho job chạy tiếp hay không. Khai báo bằng method
`middleware()` trên job:

```php
use Illuminate\Queue\Middleware\RateLimited;
use Illuminate\Queue\Middleware\WithoutOverlapping;

public function middleware(): array
{
    return [
        new RateLimited('backups'),
        (new WithoutOverlapping($this->user->id))->releaseAfter(60)->expireAfter(180),
    ];
}
```

Các middleware có sẵn:

| Middleware | Làm gì | Tuỳ chọn |
|---|---|---|
| `RateLimited('tên')` | Dùng rate limiter đã khai báo bằng `RateLimiter::for('tên', ...)`; vượt hạn mức thì release job với độ trễ phù hợp | `releaseAfter(N)`, `dontRelease()` (bỏ job thay vì thử lại); bản tối ưu cho Redis: `RateLimitedWithRedis` |
| `WithoutOverlapping($key)` | Lấy cache lock theo key; không lấy được (đang có job cùng class, cùng key chạy) thì release job | `releaseAfter(N)`, `expireAfter(N)`, `dontRelease()`, `shared()` (dùng chung key giữa nhiều class job) |
| `ThrottlesExceptions($n, $giây)` | Job ném exception liên tiếp quá ngưỡng thì hoãn các lần thử tiếp theo một khoảng thời gian | Hợp với dịch vụ ngoài đang sập |
| `Skip::when(...)`, `Skip::unless(...)` | Bỏ job theo điều kiện | |
| `FailOnException([...])` | Gặp loại exception này thì thất bại luôn, không thử lại | |
| `SkipIfBatchCancelled` | Bỏ qua nếu batch chứa job đã bị huỷ (mục 4.4) | |

Ví dụ định nghĩa rate limiter cho job (trong `boot()` của `AppServiceProvider`, theo docs):

```php
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Support\Facades\RateLimiter;

RateLimiter::for('backups', function (object $job): Limit {
    return $job->user->vipCustomer()
        ? Limit::none()
        : Limit::perHour(1)->by($job->user->id);
});
```

⚠️ Hai bẫy lớn, docs đều nhắc:

1. **Release vẫn tiêu attempt.** Với mặc định `tries = 1`, job bị `RateLimited` hay `WithoutOverlapping`
   release một lần là thất bại ở lần lấy sau, dù `handle()` chưa chạy lần nào (mục 3.2). Dùng `retryUntil()`
   cộng `MaxExceptions`, hoặc tăng `Tries`.
2. **`WithoutOverlapping` không có `expireAfter` thì lock không hết hạn.** Trong mã nguồn 13.x thời hạn mặc
   định là 0 (không hết hạn) và lock được nhả ở khối `finally`. Worker bị kill vì timeout (`SIGKILL`, mục 3.4)
   thì `finally` không chạy, lock nằm đó mãi, mọi job cùng key bị release liên tục rồi thất bại. Luôn đặt
   `expireAfter` lớn hơn timeout của job một chút.

Ba công cụ trông giống nhau nhưng trả lời ba câu hỏi khác nhau:

| | Chặn lúc | Job trùng bị | Câu hỏi |
|---|---|---|---|
| `ShouldBeUnique` | Dispatch | Không được đưa vào queue | "Đã có việc này trong queue chưa?" |
| `WithoutOverlapping` | Chạy | Release lại (tốn attempt) hoặc xoá | "Có ai đang làm việc này không?" |
| `RateLimited` | Chạy | Release lại với độ trễ | "Đã làm quá nhiều trong khoảng thời gian này chưa?" |

⚠️ Không cái nào thay được việc viết job idempotent (mục 3.7). Unique chỉ chặn lúc dispatch; kịch bản
`retry_after` ở mục 3.5 vẫn làm job chạy hai lần.

### 4.3 Chain: chạy tuần tự

*Chain* (chuỗi) là danh sách job chạy lần lượt: job sau chỉ bắt đầu khi job trước **thành công**. Một job
thất bại (sau khi hết lượt thử) thì các job sau không chạy.

```php
use App\Jobs\OptimizePodcast;
use App\Jobs\ProcessPodcast;
use App\Jobs\ReleasePodcast;
use Illuminate\Support\Facades\Bus;

Bus::chain([
    new ProcessPodcast($podcast),
    new OptimizePodcast($podcast),
    new ReleasePodcast($podcast),
])->onConnection('redis')->onQueue('podcasts')
  ->catch(function (Throwable $e): void {
      // một job trong chuỗi đã thất bại
  })
  ->dispatch();
```

- Chuỗi không nằm ở đâu riêng: danh sách job còn lại được serialize **bên trong payload** của job đang
  chạy. Job xong thì dispatch job kế tiếp. Trong một job có thể chèn thêm bằng `$this->prependToChain(...)`
  (chạy ngay sau job hiện tại) hoặc `$this->appendToChain(...)` (chạy cuối chuỗi).
- ⚠️ `$this->delete()` trong job **không** dừng chuỗi (docs); chỉ job thất bại mới dừng.
- ⚠️ Callback (`catch`) được serialize và chạy về sau trong worker, nên không dùng `$this` trong đó.

### 4.4 Batch: chạy song song và theo dõi tiến độ

*Batch* (lô) là một nhóm job chạy song song (nếu có nhiều worker), có tiến độ chung và callback khi cả lô
kết thúc. Ví dụ điển hình: chia file CSV một triệu dòng thành 100 job, mỗi job 10.000 dòng, hiện thanh tiến
độ cho người dùng.

Cần bảng `job_batches` (có sẵn trong migration mặc định; nếu thiếu: `php artisan make:queue-batches-table`)
và job phải dùng trait `Illuminate\Bus\Batchable`:

```php
<?php
declare(strict_types=1);

namespace App\Jobs;

use Illuminate\Bus\Batchable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;

final class ImportCsv implements ShouldQueue
{
    use Batchable, Queueable;

    public function __construct(public string $path, public int $from, public int $to) {}

    public function handle(): void
    {
        if ($this->batch()->cancelled()) {
            return;   // hoặc gắn middleware SkipIfBatchCancelled
        }
        // nhập các dòng từ $from tới $to
    }
}
```

```php
use App\Jobs\ImportCsv;
use Illuminate\Bus\Batch;
use Illuminate\Support\Facades\Bus;

$batch = Bus::batch([
    new ImportCsv($path, 1, 10_000),
    new ImportCsv($path, 10_001, 20_000),
    // ...
])->progress(function (Batch $batch): void {
    // một job vừa thành công
})->then(function (Batch $batch): void {
    // mọi job đều thành công
})->catch(function (Batch $batch, Throwable $e): void {
    // job thất bại ĐẦU TIÊN (chỉ gọi một lần)
})->finally(function (Batch $batch): void {
    // lô đã kết thúc, dù thành công hay không
})->name('Import khách hàng')->onQueue('imports')->dispatch();

return $batch->id;   // lưu lại để hỏi tiến độ sau: Bus::findBatch($id)
```

- Đối tượng `Batch` có `totalJobs`, `pendingJobs`, `failedJobs`, `processedJobs()`, `progress()` (0 tới 100),
  `finished()`, `cancel()`. Trả `Bus::findBatch($id)` từ một route là ra JSON cho thanh tiến độ.
- Mặc định, một job thất bại thì lô bị đánh dấu **cancelled**. Các job còn lại vẫn được worker lấy ra,
  nên phải tự kiểm tra `cancelled()` (hoặc dùng `SkipIfBatchCancelled`) để bỏ qua. Gọi `->allowFailures()`
  nếu muốn lô tiếp tục dù có job lỗi.
- `php artisan queue:retry-batch <id>` thử lại các job lỗi của một lô.
- Chain và batch lồng nhau được: một phần tử của chain có thể là một batch, và ngược lại.
- ⚠️ Mọi job trong lô phải cùng connection và queue (docs).
- ⚠️ Docs ghi job trong batch được bọc trong database transaction, nên đừng chạy câu lệnh gây *implicit
  commit* (như `ALTER TABLE`, `CREATE TABLE`) trong job của batch.
- ⚠️ Bảng `job_batches` phình rất nhanh. Lên lịch `queue:prune-batches` hằng ngày (mặc định xoá lô đã kết
  thúc quá 24 giờ; thêm `--unfinished=72`, `--cancelled=72` để xoá cả lô dở dang hay bị huỷ).

## 5. Horizon: quản lý worker cho Redis

### 5.1 Horizon là gì

Tự chạy nhiều `queue:work` qua Supervisor thì được, nhưng bạn không thấy được queue nào đang dồn, job nào
chậm, job nào lỗi nhiều. *Laravel Horizon* là package chính thức giải quyết việc đó cho queue **Redis**
(chỉ Redis, và docs ghi chưa hỗ trợ Redis Cluster):

- Một dashboard web tại `/horizon`: job đang chờ, đã xong, thất bại, thời gian chạy, throughput.
- Cấu hình worker **bằng code** trong `config/horizon.php` (được version control), thay cho nhiều file
  Supervisor.
- Tự co giãn số worker theo tải.

```bash
# chạy ở thư mục gốc project
composer require laravel/horizon
php artisan horizon:install

# chạy Horizon (một process, nó tự sinh và quản lý các worker con)
php artisan horizon
```

Trên production vẫn cần Supervisor, nhưng chỉ để giữ **một** chương trình `php artisan horizon` luôn chạy.
Deploy thì chạy `php artisan horizon:terminate`: Horizon làm xong job đang chạy rồi thoát, Supervisor khởi
động lại với code mới.

⚠️ Ngoài môi trường `local`, dashboard bị chặn bởi gate `viewHorizon` trong
`app/Providers/HorizonServiceProvider.php`. Nhớ sửa gate cho đúng người được xem
([Chương 28](28-laravel-auth.md)), đừng mở cho mọi người.

### 5.2 Cấu hình supervisor và chiến lược cân bằng

Trong Horizon, *supervisor* là một **nhóm worker cùng cấu hình** (không phải chương trình Supervisor của
Linux). Mỗi môi trường (`production`, `local`...) có một hoặc nhiều supervisor:

```php
// config/horizon.php
'environments' => [
    'production' => [
        'supervisor-default' => [
            'connection'          => 'redis',
            'queue'               => ['default', 'notifications'],
            'balance'             => 'auto',
            'autoScalingStrategy' => 'time',
            'minProcesses'        => 1,     // tối thiểu mỗi queue
            'maxProcesses'        => 10,    // tổng tối đa
            'balanceMaxShift'     => 1,     // mỗi lần thêm/bớt tối đa 1 process
            'balanceCooldown'     => 3,     // mỗi 3 giây
            'tries'               => 3,
            'timeout'             => 150,   // phải nhỏ hơn retry_after của connection redis
        ],
        'supervisor-images' => [            // queue nặng: tách riêng, giới hạn số process
            'connection'   => 'redis',
            'queue'        => ['images'],
            'balance'      => 'auto',
            'minProcesses' => 1,
            'maxProcesses' => 1,
        ],
    ],
],
```

Ba chiến lược `balance`:

| `balance` | Số process | Thứ tự queue |
|---|---|---|
| `auto` (mặc định) | Co giãn giữa `minProcesses` và `maxProcesses` theo tải từng queue; `autoScalingStrategy` là `time` (ước lượng thời gian xả queue), `size` (số job), hoặc `log` | **Không** ưu tiên theo thứ tự khai báo |
| `simple` | Cố định `processes`, chia đều cho các queue | |
| `false` | Vẫn co giãn tổng số | Ưu tiên tuyệt đối theo thứ tự, như `--queue=a,b` |

⚠️ Với `auto`, viết `'queue' => ['high', 'default']` **không** làm `high` được ưu tiên (docs nói rõ). Cần ưu
tiên thì tách supervisor riêng, hoặc dùng `balance => false`.

⚠️ Khi `auto` thu nhỏ số process, Horizon coi worker đang chạy quá `timeout` của supervisor là treo và giết
nó. Docs yêu cầu: `timeout` của supervisor lớn hơn timeout của mọi job, và vẫn nhỏ hơn `retry_after` vài giây.

### 5.3 Tag, metrics, cảnh báo

- *Tag*: Horizon tự gắn tag cho job theo các model trong property, dạng `App\Models\Video:1`. Trên dashboard
  bạn lọc được mọi job liên quan tới một đơn hàng hay một user. Tự đặt tag bằng method `tags(): array`.
- *Metrics*: biểu đồ thời gian chờ và throughput cần lên lịch `horizon:snapshot` mỗi năm phút
  (`Schedule::command('horizon:snapshot')->everyFiveMinutes();`, xem mục 7).
- *Cảnh báo*: cấu hình `waits` trong `config/horizon.php` đặt ngưỡng "chờ quá lâu" cho từng
  `connection:queue` (không khai báo thì 60 giây), và `Horizon::routeMailNotificationsTo(...)` (hoặc Slack,
  SMS) để nhận thông báo.
- Job lỗi xoá bằng `php artisan horizon:forget <id>` thay vì `queue:forget`.

## 6. Event và listener

### 6.1 Event là gì, vì sao cần

Quay lại chức năng đặt hàng. Sau khi lưu đơn, nhiều việc cần xảy ra: gửi email xác nhận, cộng điểm thưởng,
báo kho chuẩn bị hàng, đẩy dữ liệu sang CRM. Nếu viết hết vào controller, controller biết quá nhiều thứ
không phải việc của nó; mỗi lần thêm một việc mới lại phải sửa nó.

*Event* (sự kiện) là một cách tách: code đặt hàng chỉ thông báo "đã có đơn mới" (bắn event `OrderPlaced`).
Những phần khác của app đăng ký làm *listener* (bên lắng nghe) cho event đó và tự làm việc của mình. Đây là
*observer pattern* quen thuộc trong thiết kế hướng đối tượng. Một event có thể có nhiều listener, và các
listener không phụ thuộc nhau.

Bản PHP thuần tối giản để thấy cơ chế:

```php
<?php
declare(strict_types=1);

// PHP thuần: một event dispatcher tí hon, cùng ý tưởng với Illuminate\Events\Dispatcher.

final class OrderPlaced
{
    public function __construct(public int $orderId, public int $total) {}
}

final class EventDispatcher
{
    /** @var array<class-string, list<callable(object): mixed>> */
    private array $listeners = [];

    /** @param class-string $event */
    public function listen(string $event, callable $listener): void
    {
        $this->listeners[$event][] = $listener;
    }

    public function dispatch(object $event): void
    {
        foreach ($this->listeners[$event::class] ?? [] as $listener) {
            // Listener trả về false thì dừng, các listener sau không được gọi
            if ($listener($event) === false) {
                break;
            }
        }
    }
}

$events = new EventDispatcher();

$events->listen(OrderPlaced::class, function (OrderPlaced $e): void {
    echo "Gửi email xác nhận đơn {$e->orderId}\n";
});
$events->listen(OrderPlaced::class, function (OrderPlaced $e): void {
    echo "Cộng điểm thưởng: " . intdiv($e->total, 10_000) . " điểm\n";
});
$events->listen(OrderPlaced::class, function (OrderPlaced $e): void {
    throw new RuntimeException('CRM không phản hồi');
});

// Code đặt hàng chỉ biết "đã có đơn mới", không biết ai đang lắng nghe
try {
    echo "Lưu đơn hàng 42\n";
    $events->dispatch(new OrderPlaced(42, 350_000));
    echo "Trả response 201\n";
} catch (RuntimeException $e) {
    echo "Request lỗi 500: {$e->getMessage()}\n";
}

// in ra:
// Lưu đơn hàng 42
// Gửi email xác nhận đơn 42
// Cộng điểm thưởng: 35 điểm
// Request lỗi 500: CRM không phản hồi
```

Ví dụ cho thấy điểm quan trọng nhất về listener **đồng bộ**: chúng chạy ngay trong request, tuần tự, trong
cùng process. Listener chậm thì request chậm; listener ném exception thì exception lan ra và request lỗi,
dù việc chính (lưu đơn) đã xong. Event giúp tách code, **không** tự làm cho việc chạy nền. Muốn chạy nền phải
cho listener đi qua queue (mục 6.3).

⚠️ Event cũng có mặt trái: luồng xử lý bị phân tán. Đọc controller không còn thấy hết những gì xảy ra khi
đặt hàng. Dùng event khi thật sự có nhiều bên độc lập quan tâm; một việc duy nhất, gắn chặt với nghiệp vụ
thì gọi thẳng service cho dễ đọc.

### 6.2 Event và listener trong Laravel

```bash
# chạy ở thư mục gốc project
php artisan make:event OrderPlaced
php artisan make:listener SendOrderConfirmation --event=OrderPlaced
```

Event là một class chứa dữ liệu, không có logic:

```php
<?php
declare(strict_types=1);

namespace App\Events;

use App\Models\Order;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

final class OrderPlaced
{
    use Dispatchable, SerializesModels;

    public function __construct(public Order $order) {}
}
```

Listener có method `handle` nhận event:

```php
<?php
declare(strict_types=1);

namespace App\Listeners;

use App\Events\OrderPlaced;

final class AwardLoyaltyPoints
{
    public function handle(OrderPlaced $event): void
    {
        $event->order->customer->increment('points', intdiv($event->order->total, 10_000));
    }
}
```

Bắn event:

```php
OrderPlaced::dispatch($order);              // hoặc event(new OrderPlaced($order));
OrderPlaced::dispatchIf($order->isPaid(), $order);
```

*Đăng ký listener*: Laravel tự tìm (*event discovery*). Nó quét thư mục `app/Listeners`, method nào tên bắt
đầu bằng `handle` hoặc là `__invoke` thì được đăng ký cho event được type-hint ở tham số (union type
`OrderPlaced|OrderCancelled` cho nhiều event). Thư mục khác thì khai trong `bootstrap/app.php`:
`->withEvents(discover: [__DIR__.'/../app/Domain/*/Listeners'])`. Có thể đăng ký tay trong `boot()` của
`AppServiceProvider`: `Event::listen(OrderPlaced::class, AwardLoyaltyPoints::class);`.

- `php artisan event:list` liệt kê mọi event và listener đang đăng ký. Nên chạy khi không hiểu vì sao một
  listener không chạy hoặc chạy hai lần.
- Trên production, cache danh sách bằng `php artisan optimize` hoặc `event:cache` (xoá: `event:clear`) để
  khỏi quét thư mục mỗi request.
- Listener được tạo qua service container, nên constructor có thể nhận dependency.
- Listener trả về `false` thì các listener sau của cùng event không được gọi (như bản tự dựng ở trên).

### 6.3 Queued listener

Thêm `implements ShouldQueue` vào listener là đủ để nó chạy trong worker thay vì trong request:

```php
<?php
declare(strict_types=1);

namespace App\Listeners;

use App\Events\OrderPlaced;
use App\Services\CrmClient;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\Attributes\Queue;
use Illuminate\Queue\Attributes\Tries;
use Illuminate\Queue\InteractsWithQueue;

#[Queue('listeners')]
#[Tries(5)]
final class SyncOrderToCrm implements ShouldQueue
{
    use InteractsWithQueue;   // cho $this->release(), $this->attempts()...

    // Dependency nhận qua constructor (listener được tạo bằng service container)
    public function __construct(private CrmClient $crm) {}

    public function handle(OrderPlaced $event): void
    {
        $this->crm->upsertOrder($event->order);
    }

    // Chỉ đưa vào queue khi đơn đủ lớn
    public function shouldQueue(OrderPlaced $event): bool
    {
        return $event->order->total >= 5_000_000;
    }
}
```

Khi event được bắn, mỗi queued listener được đóng gói thành **một job riêng** (class
`Illuminate\Events\CallQueuedListener` bọc listener và event) rồi đẩy vào queue. Mọi thứ ở mục 2 tới 4 áp
dụng nguyên vẹn: event được serialize (nên event dùng `SerializesModels`), có tries, backoff, timeout,
middleware, `failed()`, unique (`ShouldBeUnique`)... Khai báo connection/queue/delay bằng attribute
`#[Connection]`, `#[Queue]`, `#[Delay]` hoặc method `viaConnection()`, `viaQueue()`, `withDelay()`.

Một event có ba listener queued thì sinh ra ba job; một listener lỗi không ảnh hưởng hai listener kia.

### 6.4 Event và transaction

Vấn đề ở mục 2.6 xuất hiện lại y hệt với event: bắn event trong transaction, queued listener có thể chạy
trước khi commit, không thấy dữ liệu; transaction rollback thì listener vẫn chạy cho dữ liệu không tồn tại.
Laravel có ba interface đặt ở ba chỗ khác nhau:

| Interface | Gắn vào | Tác dụng |
|---|---|---|
| `ShouldDispatchAfterCommit` | Event | Cả event chỉ được bắn sau khi transaction commit; rollback thì bỏ event |
| `ShouldQueueAfterCommit` | Queued listener | Job của listener chỉ được đẩy vào queue sau commit |
| `ShouldHandleEventsAfterCommit` | Listener (kể cả đồng bộ), observer | Listener chỉ được gọi sau commit |

Không có transaction nào đang mở thì cả ba chạy ngay như bình thường. Đặt `'after_commit' => true` cho
connection queue cũng áp cho queued listener (mục 2.6).

Một công cụ liên quan trong docs 13.x: `Event::defer(fn)` gom mọi event bắn bên trong closure lại, chỉ bắn
sau khi closure chạy xong; closure ném exception thì không bắn event nào. Hữu ích khi tạo một bản ghi cùng
các bản ghi con và muốn listener thấy đủ cả.

⚠️ Model event của Eloquent (`created`, `updated`... ở [Chương 27](27-laravel-database-eloquent.md)) cũng là
event; observer xử lý chúng chạy đồng bộ, trong transaction nếu có. Gửi email hay gọi API từ observer mà
không có `ShouldHandleEventsAfterCommit` là đang gửi cho dữ liệu có thể bị rollback.

## 7. Task scheduling: chạy việc định kỳ

### 7.1 Cron và vì sao Laravel có scheduler riêng

Nhiều việc phải chạy theo lịch: gửi báo cáo 8 giờ sáng mỗi ngày, xoá session hết hạn mỗi giờ, đối soát
thanh toán lúc 2 giờ đêm. Trên Linux, công cụ truyền thống là *cron*: một daemon đọc bảng lịch (*crontab*),
mỗi dòng gồm năm trường thời gian và một lệnh.

```
┌───────── phút (0-59)
│ ┌─────── giờ (0-23)
│ │ ┌───── ngày trong tháng (1-31)
│ │ │ ┌─── tháng (1-12)
│ │ │ │ ┌─ thứ trong tuần (0-6, 0 là Chủ nhật)
│ │ │ │ │
0 8 * * *   php /var/www/app/artisan report:daily      <- 8:00 mỗi ngày
```

Viết từng dòng cron cho từng việc có nhược điểm: lịch nằm trên server chứ không nằm trong mã nguồn (không
review được, không version control), thêm việc mới phải SSH vào sửa, nhiều server thì phải sửa đồng bộ.

*Scheduler* của Laravel đảo ngược: lịch được khai báo **trong code**, và server chỉ cần **một** dòng cron
gọi Laravel mỗi phút:

```bash
# thêm bằng `crontab -e` trên server (user chạy app, ví dụ www-data)
* * * * * cd /var/www/app && php artisan schedule:run >> /dev/null 2>&1
```

Mỗi phút, cron khởi động một process `schedule:run`. Process đó:

1. Boot app, nạp danh sách task đã khai báo.
2. Với từng task, so biểu thức lịch của task với thời điểm hiện tại, rồi áp các điều kiện lọc (`when`,
   `skip`, `environments`, maintenance mode, lock của `withoutOverlapping`/`onOneServer`).
3. Chạy các task đến giờ **tuần tự** theo thứ tự khai báo (trừ task có `runInBackground()`).
4. Thoát. Nếu có task chạy dưới một phút (`everyTenSeconds()`...), process ở lại tới hết phút để gọi
   chúng.

Trên máy dev không cần cron: chạy `php artisan schedule:work` (gọi scheduler mỗi phút, chạy ở foreground).
`php artisan schedule:list` liệt kê mọi task và lần chạy kế tiếp.

### 7.2 Khai báo task

Task thường được khai báo trong `routes/console.php`:

```php
<?php
declare(strict_types=1);

// routes/console.php
use App\Jobs\Heartbeat;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schedule;

// Lệnh artisan
Schedule::command('report:generate')->dailyAt('08:00');

// Đẩy một job vào queue (task chỉ dispatch, worker mới chạy)
Schedule::job(new Heartbeat())->everyFiveMinutes();

// Closure
Schedule::call(fn (): int => DB::table('recent_users')->delete())
    ->name('purge-recent-users')
    ->daily();

// Lệnh shell
Schedule::exec('node /var/www/scripts/sitemap.js')->weekly();

// Kết hợp ràng buộc: mỗi giờ, ngày thường, từ 8:00 tới 17:00
Schedule::command('inventory:sync')
    ->weekdays()
    ->hourly()
    ->between('8:00', '17:00');

// Dọn dẹp định kỳ cho queue (mục 3.6, 4.4)
Schedule::command('queue:prune-failed --hours=168')->daily();
Schedule::command('queue:prune-batches --hours=48')->daily();
```

Một số phương thức tần suất (danh sách đầy đủ ở docs): `everyMinute()`, `everyFiveMinutes()`, `hourly()`,
`hourlyAt(17)`, `daily()` (nửa đêm), `dailyAt('13:00')`, `twiceDaily(1, 13)`, `weekly()` (Chủ nhật 00:00),
`weeklyOn(1, '8:00')`, `monthly()`, `lastDayOfMonth('15:00')`, `cron('*/5 * * * *')` cho biểu thức tuỳ ý.
Điều kiện: `weekdays()`, `mondays()`, `between()`, `unlessBetween()`, `when(fn)`, `skip(fn)`,
`environments(['production'])`.

⚠️ Mặc định giờ của task theo `timezone` của app (thường là `UTC`). "8 giờ sáng giờ Việt Nam" cần
`->timezone('Asia/Ho_Chi_Minh')`, hoặc đặt `schedule_timezone` trong `config/app.php`. Docs cảnh báo múi giờ
có *daylight saving time*: lúc đổi giờ task có thể chạy hai lần hoặc không chạy. Việt Nam không đổi giờ,
nhưng nếu đặt theo `America/New_York` thì phải nhớ điều này.

### 7.3 withoutOverlapping: không cho lượt mới chồng lên lượt cũ

Mặc định, task vẫn được chạy dù lượt trước của chính nó chưa xong. Task `emails:send` chạy mỗi phút, có
hôm mất 3 phút, thì sẽ có ba bản chạy cùng lúc, gửi trùng email.

```php
Schedule::command('emails:send')
    ->everyMinute()
    ->withoutOverlapping(10);   // lock hết hạn sau 10 phút (mặc định 24 giờ)
```

Cơ chế: trước khi chạy, scheduler lấy một cache lock mang tên task (`Event::mutexName()`: chuỗi
`framework/schedule-` cộng `sha1` của biểu thức lịch và lệnh); lấy được thì chạy, xong thì nhả. Lấy không
được thì lượt này bỏ qua.

⚠️ Process chết đột ngột (`kill -9`, OOM killer, container bị giết cứng) không kịp nhả lock. Lock nằm đó tới
khi hết hạn; với mặc định 24 giờ, task không chạy suốt một ngày mà không có lỗi nào được báo. Cách phòng:
đặt thời hạn sát với thời gian chạy tối đa (`withoutOverlapping(10)`), và khi lock kẹt thì chạy
`php artisan schedule:clear-cache`.

### 7.4 onOneServer: nhiều server, mỗi lượt chỉ chạy một lần

Bẫy kinh điển khi scale: app chạy trên 3 server, server nào cũng có dòng cron `schedule:run` (vì cùng một
image hay cùng script cài đặt). Đến 17:00 thứ Sáu, cả ba cùng thấy `report:generate` tới giờ, và báo cáo được
gửi ba lần. Tệ hơn với task trừ tiền.

| Bước | Server A | Server B | Server C | Kết quả |
|---|---|---|---|---|
| 1 | 17:00 cron gọi `schedule:run` | 17:00 cron gọi `schedule:run` | 17:00 cron gọi `schedule:run` | Cả ba thấy task tới giờ |
| 2 | Không có `onOneServer`: chạy | Chạy | Chạy | 3 báo cáo |
| 2' | Có `onOneServer`: lấy được lock, chạy | Lấy lock thất bại, bỏ qua | Lấy lock thất bại, bỏ qua | 1 báo cáo |

```php
Schedule::command('report:generate')
    ->fridays()->at('17:00')
    ->onOneServer();

// Closure (và job có tham số khác nhau) phải có name() để dùng onOneServer
Schedule::call(fn (): int => DB::table('recent_users')->delete())
    ->name('purge-recent-users')
    ->daily()
    ->onOneServer();
```

Cơ chế (đọc trong `Console/Scheduling/CacheSchedulingMutex.php` 13.x): tên lock là tên mutex của task ghép
với giờ phút của lượt chạy (định dạng `Hi`, ví dụ `1700`), thời hạn 3600 giây, lấy bằng cache lock (hoặc
`Cache::add`, cũng nguyên tử). Server nào lấy được trước thì chạy. Lock **không** được nhả sau khi chạy
xong: nó chỉ phục vụ đúng lượt 17:00 đó và tự hết hạn.

Điều kiện bắt buộc (docs): cache mặc định (hoặc store chọn bằng `Schedule::useCache('redis')`) phải là
`database`, `memcached`, `dynamodb` hoặc `redis`, và mọi server nối tới **cùng một** cache server. Ví dụ PHP
thuần sau cho thấy vì sao:

```php
<?php
declare(strict_types=1);

// PHP thuần: vì sao onOneServer() cần một cache DÙNG CHUNG.
// Store là một bảng SQLite; add() chỉ ghi khi key chưa có (nguyên tử nhờ PRIMARY KEY).

final class Store
{
    private PDO $db;

    public function __construct()
    {
        $this->db = new PDO('sqlite::memory:', options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
        $this->db->exec('CREATE TABLE cache (k TEXT PRIMARY KEY, expires_at INTEGER)');
    }

    public function add(string $key, int $ttl): bool
    {
        $stmt = $this->db->prepare('INSERT OR IGNORE INTO cache (k, expires_at) VALUES (?, ?)');
        $stmt->execute([$key, time() + $ttl]);
        return $stmt->rowCount() === 1;   // 1 dòng được chèn = mình là người đầu tiên
    }
}

function runSchedule(string $server, Store $store, string $minute): void
{
    // Tên lock = tên task + giờ phút của lượt chạy (giống CacheSchedulingMutex)
    $lock = 'schedule-report:generate' . $minute;
    echo $store->add($lock, 3600)
        ? "{$server}: chạy report:generate\n"
        : "{$server}: bỏ qua (server khác đã nhận lượt {$minute})\n";
}

echo "== Cache dùng chung (Redis/DB) ==\n";
$shared = new Store();
foreach (['A', 'B', 'C'] as $server) {
    runSchedule($server, $shared, '1700');
}

echo "== Cache file: mỗi server một store riêng ==\n";
foreach (['A', 'B', 'C'] as $server) {
    runSchedule($server, new Store(), '1700');
}

// in ra:
// == Cache dùng chung (Redis/DB) ==
// A: chạy report:generate
// B: bỏ qua (server khác đã nhận lượt 1700)
// C: bỏ qua (server khác đã nhận lượt 1700)
// == Cache file: mỗi server một store riêng ==
// A: chạy report:generate
// B: chạy report:generate
// C: chạy report:generate
```

Phân biệt hai công cụ:

| | `onOneServer()` | `withoutOverlapping()` |
|---|---|---|
| Chặn | Nhiều server cùng chạy **một lượt** | Lượt mới chồng lên lượt cũ đang chạy |
| Tên lock | Tên task + giờ phút của lượt | Tên task |
| Thời hạn lock | 3600 giây, không nhả chủ động | Mặc định 24 giờ, nhả khi task xong |

Một cách khác thay cho `onOneServer`: chỉ đặt cron trên **một** instance (một container "scheduler" riêng).
Đơn giản hơn, nhưng instance đó chết thì không task nào chạy.

### 7.5 Các chi tiết khác

- `runInBackground()`: mặc định task cùng phút chạy tuần tự, task dài làm task sau trễ. `runInBackground()`
  chạy task thành process con riêng; chỉ dùng được với `command` và `exec`.
- Maintenance mode: task không chạy, trừ khi có `->evenInMaintenanceMode()`.
- `php artisan schedule:pause` / `schedule:continue` tạm dừng mọi task mà không cần deploy.
- Task dưới một phút làm `schedule:run` sống cả phút, tức vẫn chạy code cũ ngay sau deploy. Docs khuyên thêm
  `php artisan schedule:interrupt` vào script deploy, và để task dưới một phút chỉ dispatch job hoặc chạy nền.
- Output và hook: `->sendOutputTo($file)`, `->emailOutputOnFailure(...)`, `->onSuccess(fn)`, `->onFailure(fn)`,
  `->pingOnFailure($url)` (báo cho dịch vụ giám sát cron). Task thất bại âm thầm là chuyện thường gặp; hãy
  cho nó một cách để kêu cứu.
- ⚠️ Task chạy trong process `schedule:run`, không phải worker. Việc nặng nên để task chỉ `Schedule::job(...)`,
  phần nặng chạy trong worker với đủ retry, timeout của queue.

## 8. Cache

### 8.1 Cache là gì, cache-aside

*Cache* là nơi lưu tạm kết quả của một việc tốn kém (query nặng, gọi API, tính toán) để lần sau lấy lại nhanh
thay vì làm lại. Kho cache thường là bộ nhớ (Redis, Memcached): đọc mất cỡ dưới một mili giây, so với hàng chục
hay hàng trăm mili giây của một query phức tạp.

Mẫu dùng phổ biến nhất là *cache-aside*:

```
đọc:  có trong cache? ── có ──> trả luôn                      (cache hit)
                      └─ không ─> query DB -> ghi vào cache -> trả   (cache miss)
ghi:  cập nhật DB -> xoá (hoặc cập nhật) key cache liên quan
```

Mỗi giá trị trong cache có *TTL* (time to live): sau thời gian đó tự hết hạn. TTL là cách đơn giản nhất để giới
hạn độ "cũ" của dữ liệu.

Câu khó nhất của cache không phải "lưu thế nào" mà là "khi nào dữ liệu trong cache trở nên sai" (*cache
invalidation*). Lý thuyết đầy đủ (các chiến lược ghi, eviction, nhất quán) nằm ở tài liệu
[Cache](../11-cache.md); mục này tập trung vào API của Laravel và các bẫy.

### 8.2 Cấu hình và API cơ bản

`config/cache.php` khai báo các *store*; `CACHE_STORE` chọn store mặc định. Project Laravel 13 mới dùng
`database` (bảng `cache`, tạo bởi migration mặc định `0001_01_01_000001_create_cache_table.php`).

| Driver | Ghi chú |
|---|---|
| `database` | Mặc định của app mới; không cần cài thêm |
| `redis` | Phổ biến nhất trên production; cần phpredis hoặc `predis/predis` |
| `memcached` | Cần extension Memcached |
| `file` | `storage/framework/cache/data`; mỗi server một bản |
| `array` | Chỉ trong process hiện tại, mất khi process kết thúc; dùng cho test |
| `dynamodb`, `storage` (filesystem disk), `failover`, `null` | Ít gặp hơn |

```php
use Illuminate\Support\Facades\Cache;

Cache::put('rate:usd', 25_400, 600);        // lưu 600 giây; không truyền TTL là lưu vô hạn
Cache::put('rate:usd', 25_400, now()->addMinutes(10));

$rate = Cache::get('rate:usd');            // không có thì null
$rate = Cache::get('rate:usd', 25_000);    // không có thì giá trị mặc định

Cache::has('rate:usd');                    // false cả khi key có nhưng giá trị là null
Cache::add('lock:x', 1, 60);               // chỉ ghi nếu key CHƯA có; trả true/false; nguyên tử
Cache::increment('views:42');              // tăng số nguyên
Cache::forget('rate:usd');                 // xoá một key
$v = Cache::pull('otp:42');                // đọc rồi xoá
Cache::touch('session:abc', 3600);         // gia hạn TTL mà không đọc/ghi lại giá trị
Cache::forever('settings', $settings);     // không hết hạn (phải tự forget)

Cache::store('redis')->get('k');           // dùng một store cụ thể thay cho mặc định
```

`remember` gói đúng mẫu cache-aside:

```php
$users = Cache::remember('users:active', 600, function () {
    return User::where('active', true)->get();
});
```

Có trong cache thì trả luôn; không có thì gọi closure, lưu kết quả với TTL 600 giây, rồi trả.

⚠️ Bẫy của `remember`:

- Closure trả về `null` thì lần sau vẫn bị coi là miss (mã nguồn: `if (! is_null($value)) return ...`), nên
  query chạy **mỗi lần**. Muốn cache kết quả "không có", lưu một giá trị đại diện khác `null` (`false`, mảng
  rỗng).
- Key phải chứa **mọi thứ** làm kết quả khác đi. `Cache::remember('products', ...)` cho danh sách sản phẩm có
  phân trang và lọc theo ngôn ngữ là sai: trang 2 nhận kết quả của trang 1. Key đúng kiểu
  `"products:{$locale}:page:{$page}"`.
- Dữ liệu riêng của user (giỏ hàng, quyền) mà key không có user id thì user này thấy dữ liệu của user khác:
  vừa là bug vừa là lỗ hổng bảo mật.

⚠️ `Cache::flush()` xoá **toàn bộ** store, không tôn trọng `prefix` (docs). Redis dùng chung với app khác hay
chung với queue mà flush là xoá luôn dữ liệu của họ. Nên tách Redis database (hoặc connection) cho cache và
cho queue.

⚠️ Laravel 13 thêm tuỳ chọn `'serializable_classes' => false` trong `config/cache.php` của app mới: mặc định
cache **không** unserialize object PHP nào, để chặn tấn công *gadget chain* nếu `APP_KEY` bị lộ (unserialize
không an toàn ở [Chương 17](17-bao-mat.md)). App cố ý cache object (model, DTO) phải liệt kê class được phép
trong tuỳ chọn này, hoặc chuyển sang cache mảng (upgrade guide 13.x).

### 8.3 Tag và memo

*Tag* gắn nhãn cho nhiều key để xoá cả nhóm:

```php
Cache::tags(['people', 'artists'])->put('John', $john, 600);
Cache::tags(['people', 'authors'])->put('Anne', $anne, 600);

$john = Cache::tags(['people', 'artists'])->get('John');   // phải truyền đúng danh sách tag lúc ghi

Cache::tags('authors')->flush();   // xoá Anne, giữ John
```

⚠️ Docs: tag không hỗ trợ ở driver `file`, `dynamodb`, `database`, `storage`. Thực tế là Redis hoặc Memcached.

*Memo*: `Cache::memo()` bọc một store và nhớ giá trị đã đọc **trong phạm vi một request hoặc một job**:

```php
Cache::memo()->get('settings');   // gọi xuống store (Redis)
Cache::memo()->get('settings');   // lấy từ bộ nhớ của process, không gọi Redis
Cache::memo()->put('settings', $new);   // thao tác ghi: xoá bản nhớ rồi ghi xuống store
```

Hữu ích khi cùng một key được đọc hàng chục lần trong một request (cấu hình, feature flag).

### 8.4 Atomic lock

Cache của Laravel còn cung cấp *atomic lock* (khoá phân tán): đảm bảo tại một thời điểm chỉ một process, trên
bất kỳ server nào, được làm một việc. Unique job (mục 4.1), `WithoutOverlapping` (mục 4.2) và `onOneServer`
(mục 7.4) đều xây trên nó.

```php
<?php
declare(strict_types=1);

use Illuminate\Contracts\Cache\LockTimeoutException;
use Illuminate\Support\Facades\Cache;

$lock = Cache::lock('invoice:42', 10);   // lock tự hết hạn sau 10 giây

if ($lock->get()) {                      // thử lấy ngay, không chờ
    try {
        // phần chỉ một process được làm tại một thời điểm
    } finally {
        $lock->release();
    }
}

// Chờ tối đa 5 giây để lấy lock; quá thì ném LockTimeoutException
try {
    Cache::lock('invoice:42', 10)->block(5, function (): void {
        // lấy được lock; tự nhả sau khi closure chạy xong
    });
} catch (LockTimeoutException) {
    // không lấy được lock
}
```

Bên trong, với Redis (đọc từ `Cache/RedisLock.php` 13.x): lấy lock là lệnh `SET <tên> <owner> EX <giây> NX`,
tức "chỉ ghi nếu chưa có, kèm thời hạn", một thao tác nguyên tử. `<owner>` là một chuỗi ngẫu nhiên riêng của
mỗi object lock. Nhả lock chạy một Lua script "nếu giá trị đang là owner của tôi thì mới xoá".

Vì sao cần owner? Ví dụ PHP thuần sau mô phỏng tình huống lock hết hạn trong khi người giữ vẫn đang chạy:

```php
<?php
declare(strict_types=1);

// PHP thuần: mô phỏng cache lock kiểu Redis (SET key owner EX ttl NX) với đồng hồ giả.
// Mục tiêu: thấy vì sao release() phải kiểm tra owner token.

final class FakeRedis
{
    public int $now = 0;                                   // đồng hồ giả, tính bằng giây
    /** @var array<string, array{value: string, expires: int}> */
    private array $data = [];

    // SET key value EX ttl NX: chỉ ghi khi key chưa có (hoặc đã hết hạn)
    public function setNx(string $key, string $value, int $ttl): bool
    {
        if (isset($this->data[$key]) && $this->data[$key]['expires'] > $this->now) {
            return false;
        }
        $this->data[$key] = ['value' => $value, 'expires' => $this->now + $ttl];
        return true;
    }

    public function get(string $key): ?string
    {
        $item = $this->data[$key] ?? null;
        return ($item !== null && $item['expires'] > $this->now) ? $item['value'] : null;
    }

    public function del(string $key): void
    {
        unset($this->data[$key]);
    }
}

final class Lock
{
    public function __construct(
        private FakeRedis $redis,
        private string $name,
        private int $seconds,
        private string $owner,                             // token ngẫu nhiên riêng của mỗi lock
    ) {}

    public function get(): bool
    {
        return $this->redis->setNx($this->name, $this->owner, $this->seconds);
    }

    // Laravel làm bước "so owner rồi xoá" trong một Lua script để nó nguyên tử
    public function release(): bool
    {
        if ($this->redis->get($this->name) !== $this->owner) {
            return false;                                  // không phải lock của mình: không xoá
        }
        $this->redis->del($this->name);
        return true;
    }
}

$redis = new FakeRedis();
$a = new Lock($redis, 'invoice:42', 10, 'token-A');
$b = new Lock($redis, 'invoice:42', 10, 'token-B');

var_dump($a->get());          // t=0: A lấy lock 10 giây
// in ra: bool(true)
var_dump($b->get());          // t=0: B thử, thất bại
// in ra: bool(false)

$redis->now = 12;             // A chạy chậm 12 giây, lock đã tự hết hạn ở t=10
var_dump($b->get());          // t=12: B lấy được lock
// in ra: bool(true)

var_dump($a->release());      // A xong việc, gọi release(): bị từ chối vì lock giờ là của B
// in ra: bool(false)
var_dump($redis->get('invoice:42'));
// in ra: string(7) "token-B"
```

Nếu không có owner, A sẽ xoá mất lock của B, và một process C bất kỳ lại vào được: ba bên cùng làm việc lẽ ra
chỉ một bên được làm.

Ví dụ cũng cho thấy giới hạn của mọi lock có thời hạn:

- ⚠️ TTL của lock phải **dài hơn** thời gian làm việc. Ở trên, từ giây thứ 10 tới 12, cả A và B cùng ở trong
  vùng "chỉ một process". Việc dài thì lấy lock ngắn rồi gọi `$lock->refresh()` định kỳ để gia hạn.
- Lock không thời hạn (`Cache::lock('k')` với 0 giây) thì không bị hết hạn sớm, nhưng process chết là lock
  kẹt mãi (cùng bẫy với `WithoutOverlapping` ở mục 4.2).
- Lấy lock trong request rồi nhả trong job: truyền `$lock->owner()` cho job, trong job gọi
  `Cache::restoreLock('invoice:42', $owner)->release()`. `forceRelease()` bỏ qua owner (chỉ dùng khi cứu hộ).
- Lock nằm trong cache, nên phải dùng **cùng** cache server giữa mọi server. Driver hỗ trợ: `memcached`,
  `redis`, `dynamodb`, `database`, `file`, `array` (hai cái cuối chỉ có nghĩa trong một máy).
- Giới hạn số process chạy **đồng thời** (không phải loại trừ hẳn): `Cache::funnel('k')->limit(3)->...`.

### 8.5 Cache stampede và `flexible`

*Cache stampede* (còn gọi *dog-pile*): một key nóng (trang chủ, bảng xếp hạng) hết hạn, hàng trăm request
cùng lúc thấy "miss", cùng chạy query nặng, database quá tải đúng lúc cao điểm.

| Bước | Request 1 | Request 2 | Request 3...100 | Database |
|---|---|---|---|---|
| t | `remember`: miss | `remember`: miss | miss | |
| t + 1 ms | Chạy query nặng | Chạy query nặng | Chạy query nặng | 100 query nặng cùng lúc |
| t + 2 s | Ghi cache | Ghi đè cache | Ghi đè cache | Hồi phục (nếu chưa sập) |

`remember` **không** chống được: nó chỉ là "get, nếu null thì tính rồi put", không có gì phối hợp giữa các
request.

`Cache::flexible($key, [$fresh, $stale], $callback)` áp dụng *stale-while-revalidate*: trả bản cũ trong lúc làm
mới ở nền. Đọc `Repository::flexible` 13.x:

1. Đọc cùng lúc giá trị và một key phụ chứa thời điểm tạo. Cả hai được lưu với TTL bằng số thứ hai (`$stale`).
2. Chưa có giá trị: tính **ngay** trong request, lưu, trả về (lúc cache lạnh vẫn có thể stampede).
3. Tuổi giá trị nhỏ hơn `$fresh`: trả luôn.
4. Tuổi nằm giữa `$fresh` và `$stale`: trả **bản cũ ngay**, và đăng ký một hàm `defer` chạy sau khi response đã
   gửi đi. Hàm đó lấy một cache lock, kiểm tra chưa ai làm mới, rồi mới tính lại. Nhờ lock, chỉ một request
   thực sự chạy query.

```php
$stats = Cache::flexible('dashboard:stats', [300, 600], function (): array {
    return DashboardStats::compute();   // query nặng
});
// 0 tới 300 giây: trả bản trong cache
// 300 tới 600 giây: trả bản cũ ngay, một request làm mới sau khi gửi response
// sau 600 giây (không ai đọc trong khoảng stale): hết hạn hẳn, request kế tiếp tính đồng bộ
```

Các cách chống stampede khác: bọc phần tính bằng `Cache::lock` (một process tính, số còn lại chờ rồi đọc lại);
cộng *jitter* ngẫu nhiên vào TTL để nhiều key không cùng hết hạn một lúc; làm ấm cache bằng task định kỳ (mục 7)
trước khi key hết hạn.

## 9. Mail và notification

### 9.1 Gửi mail

Laravel gửi mail qua component Symfony Mailer, với nhiều *transport*: SMTP, Amazon SES, Postmark, Resend,
Mailgun, `sendmail`... Cấu hình nằm trong `config/mail.php`; `MAIL_MAILER` chọn mailer mặc định. Project mới
dùng mailer `log`: mail không được gửi thật mà được ghi vào file log, rất tiện khi phát triển. Một lựa chọn
khác cho dev là SMTP tới một hộp thư giả (Mailpit, Mailtrap) để xem mail như trong trình đọc mail thật.

Mỗi loại email là một class *mailable*:

```bash
# chạy ở thư mục gốc project
php artisan make:mail OrderShipped
```

```php
<?php
declare(strict_types=1);

namespace App\Mail;

use App\Models\Order;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Mail\Mailable;
use Illuminate\Mail\Mailables\Content;
use Illuminate\Mail\Mailables\Envelope;
use Illuminate\Queue\SerializesModels;

final class OrderShipped extends Mailable implements ShouldQueue   // ShouldQueue: luôn gửi qua queue
{
    use Queueable, SerializesModels;

    public function __construct(public Order $order) {}

    // Tiêu đề, người gửi, reply-to
    public function envelope(): Envelope
    {
        return new Envelope(subject: "Đơn hàng #{$this->order->id} đã được giao cho đơn vị vận chuyển");
    }

    // Nội dung: một view Blade; property public ($order) tự có trong view
    public function content(): Content
    {
        return new Content(view: 'mail.orders.shipped');
    }
}
```

```blade
{{-- resources/views/mail/orders/shipped.blade.php --}}
<p>Xin chào {{ $order->customer->name }},</p>
<p>Đơn hàng của bạn trị giá {{ number_format($order->total) }} đ đang trên đường giao.</p>
```

Gửi:

```php
use App\Mail\OrderShipped;
use Illuminate\Support\Facades\Mail;

Mail::to($order->customer)->send(new OrderShipped($order));      // object có thuộc tính email, name
Mail::to('an@example.com')->cc($manager)->bcc($audit)->send(new OrderShipped($order));

Mail::to($user)->queue(new OrderShipped($order));                // đẩy vào queue
Mail::to($user)->later(now()->addMinutes(10), new OrderShipped($order));
```

- Mailable `implements ShouldQueue` thì gọi `send()` cũng đi qua queue. Không có `ShouldQueue` thì `send()` gửi
  **ngay trong request**: chậm, và SMTP lỗi là request lỗi. Trên production, mail gần như luôn nên đi qua queue.
- Mail qua queue là một job như mọi job khác: có retry, timeout, failed_jobs; mailable dùng
  `SerializesModels` nên model bị query lại lúc gửi (mục 2.5). Chọn queue bằng `onQueue('emails')` hoặc
  attribute `#[Queue('emails')]`; cần đợi transaction thì `->afterCommit()` (mục 2.6).
- ⚠️ Gửi cho nhiều người trong vòng lặp: `to()` **cộng dồn** người nhận vào mailable, nên tạo mailable mới
  cho từng người (docs):

  ```php
  foreach ($recipients as $email) {
      Mail::to($email)->send(new Newsletter($issue));   // new mỗi vòng, không dùng lại một object
  }
  ```

- ⚠️ Mail đã gửi thì không thu hồi được. Job gửi mail chạy lại (mục 3.7) là khách nhận hai email. Với mail
  quan trọng, ghi lại "đã gửi" vào database (unique index) trước hoặc sau khi gửi.
- Trên môi trường dev/staging, `Mail::alwaysTo('dev@example.com')` (trong `boot()` của provider) chuyển mọi
  mail về một địa chỉ, tránh gửi nhầm cho khách thật.

### 9.2 Notification: một thông báo, nhiều kênh

*Notification* là một thông báo ngắn gửi cho người dùng qua một hoặc nhiều *kênh* (*channel*): mail, database
(hiện trong chuông thông báo của web), broadcast (đẩy real-time, mục 10), SMS, Slack... Khác mailable ở chỗ:
mailable mô tả **một email**, notification mô tả **một sự kiện cần báo**, rồi tự quyết định báo qua đâu.

```bash
php artisan make:notification InvoicePaid
php artisan make:notifications-table   # bảng notifications cho kênh database
php artisan migrate
```

```php
<?php
declare(strict_types=1);

namespace App\Notifications;

use App\Models\Invoice;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Notifications\Messages\MailMessage;
use Illuminate\Notifications\Notification;

final class InvoicePaid extends Notification implements ShouldQueue
{
    use Queueable;

    public function __construct(public Invoice $invoice) {}

    // Gửi qua kênh nào; $notifiable là đối tượng nhận (thường là User)
    /** @return list<string> */
    public function via(object $notifiable): array
    {
        return $notifiable->wants_email ? ['mail', 'database'] : ['database'];
    }

    public function toMail(object $notifiable): MailMessage
    {
        return (new MailMessage())
            ->subject('Hoá đơn đã được thanh toán')
            ->line("Hoá đơn #{$this->invoice->id} đã được thanh toán.")
            ->action('Xem hoá đơn', url("/invoices/{$this->invoice->id}"));
    }

    // Dữ liệu lưu vào bảng notifications (cột data, dạng JSON)
    /** @return array<string, mixed> */
    public function toArray(object $notifiable): array
    {
        return ['invoice_id' => $this->invoice->id, 'amount' => $this->invoice->amount];
    }
}
```

Gửi:

```php
use App\Notifications\InvoicePaid;
use Illuminate\Support\Facades\Notification;

$user->notify(new InvoicePaid($invoice));            // model User dùng trait Notifiable (có sẵn)
Notification::send($admins, new InvoicePaid($invoice));

// Gửi cho địa chỉ không phải user trong DB (on-demand)
Notification::route('mail', 'ops@example.com')->notify(new InvoicePaid($invoice));

// Đọc thông báo kênh database
foreach ($user->unreadNotifications as $n) {
    echo $n->data['invoice_id'];
}
$user->unreadNotifications->markAsRead();
```

⚠️ Notification `ShouldQueue`: docs ghi rằng mỗi cặp (người nhận, kênh) thành **một job riêng**. Ba người nhận
× hai kênh = sáu job. Gửi cho 10.000 user qua 2 kênh là 20.000 job: tính trước tải cho queue, và tách queue
riêng cho notification để không làm nghẽn job nghiệp vụ.

Notification còn có `shouldSend($notifiable, $channel)` để bỏ gửi vào phút chót, `middleware()` như job, và
cùng các attribute `#[Tries]`, `#[Timeout]`... Chi tiết từng kênh xem docs Notifications.

## 10. Broadcasting và Reverb (khái niệm)

### 10.1 Vấn đề: server muốn báo cho trình duyệt

HTTP là mô hình "client hỏi, server trả lời". Server không tự gửi được gì cho trình duyệt nếu trình duyệt không
hỏi. Vậy làm sao hiện "Đơn hàng của bạn vừa được giao" ngay khi job ở mục 3 chạy xong, không cần người dùng tải
lại trang?

- *Polling*: trình duyệt hỏi server mỗi vài giây. Đơn giản, nhưng tốn request vô ích và vẫn trễ.
- *WebSocket*: trình duyệt mở một kết nối hai chiều, giữ mở lâu dài; server đẩy tin xuống bất kỳ lúc nào.

Một PHP-FPM worker không thể giữ hàng nghìn kết nối mở lâu dài ([Chương 18](18-fpm-nginx-opcache.md): mỗi
worker một request). Vì vậy cần một *WebSocket server* riêng chạy song song với app.

### 10.2 Broadcasting trong Laravel

*Broadcasting* của Laravel cho phép "phát" một event phía server xuống trình duyệt qua WebSocket server:

```
Laravel (web hoặc worker)                     WebSocket server                     Trình duyệt
-------------------------                     ----------------                     -----------
OrderShipped::dispatch($order)                                                     Laravel Echo (JS)
  event implements ShouldBroadcast                                                 đã subscribe
  -> job broadcast vào queue                                                       private-orders.42
Worker chạy job  ---- HTTP API ------------>  Reverb / Pusher / Ably  --- push --->  nhận event, cập nhật UI
```

- Bật bằng `php artisan install:broadcasting` (app mới chưa bật sẵn). Lệnh tạo `config/broadcasting.php` và
  `routes/channels.php`, và hỏi chọn driver: *Reverb* (WebSocket server viết bằng PHP của chính Laravel, tự
  host), Pusher Channels, Ably (hai dịch vụ bên ngoài), hoặc Mercure.
- Event `implements ShouldBroadcast` và có method `broadcastOn()` trả về channel. Mặc định việc phát đi
  **qua queue** (cần worker chạy); `ShouldBroadcastNow` thì phát ngay (đồng bộ).
- Phía trình duyệt dùng thư viện JavaScript *Laravel Echo* để subscribe channel và nghe event.

Ba loại channel:

| Loại | Ai được nghe | Dùng cho |
|---|---|---|
| `Channel` (public) | Bất kỳ ai | Tỉ số trận đấu, thông báo chung |
| `PrivateChannel` | User đã đăng nhập và được callback phân quyền cho phép | Đơn hàng của tôi, tin nhắn riêng |
| `PresenceChannel` | Như private, và biết thêm danh sách ai đang trong channel | "Đang online", "đang gõ..." |

```php
<?php
declare(strict_types=1);

namespace App\Events;

use App\Models\Order;
use Illuminate\Broadcasting\PrivateChannel;
use Illuminate\Contracts\Broadcasting\ShouldBroadcast;
use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

final class OrderStatusUpdated implements ShouldBroadcast
{
    use Dispatchable, SerializesModels;

    public function __construct(public Order $order) {}

    public function broadcastOn(): PrivateChannel
    {
        return new PrivateChannel('orders.' . $this->order->id);
    }
}
```

```php
// routes/channels.php: ai được nghe channel private "orders.{id}"
use App\Models\Order;
use App\Models\User;
use Illuminate\Support\Facades\Broadcast;

Broadcast::channel('orders.{order}', function (User $user, Order $order): bool {
    return $user->id === $order->user_id;
});
```

⚠️ Mặc định mọi property **public** của event được gửi xuống trình duyệt. Event mang cả model `Order` thì mọi cột
không bị ẩn của model (xem `$hidden` ở [Chương 27](27-laravel-database-eloquent.md)) đều lộ ra phía client.
Kiểm soát dữ liệu gửi đi bằng method `broadcastWith()`, và luôn phân quyền channel private cẩn thận như phân quyền
một API ([Chương 28](28-laravel-auth.md)).

`broadcast(new OrderStatusUpdated($order))->toOthers()` bỏ qua chính người vừa thao tác (họ đã cập nhật giao diện
từ response rồi). Docs yêu cầu event dùng trait `Illuminate\Broadcasting\InteractsWithSockets` thì mới gọi được
`toOthers()`; event ở ví dụ trên chưa có trait này, và trong mã nguồn 13.x thiếu trait thì `toOthers()` lặng lẽ không
có tác dụng.

### 10.3 Reverb trên production

Reverb chạy bằng `php artisan reverb:start` (mặc định lắng nghe `0.0.0.0:8080`). Đây lại là một **process sống
lâu** như queue worker, với cùng hệ quả:

- Cần process manager (Supervisor) giữ nó chạy; deploy xong chạy `php artisan reverb:restart`.
- Thường đặt sau Nginx làm reverse proxy (có header `Upgrade` cho WebSocket).
- Mỗi kết nối WebSocket là một file descriptor đang mở: phải nâng giới hạn `ulimit -n` của hệ điều hành. Docs
  ghi event loop mặc định dựa trên `stream_select` thường bị giới hạn 1.024 file mở, muốn hơn khoảng 1.000 kết
  nối đồng thời thì cài extension `uv` (Reverb tự chuyển sang).
- Scale ngang nhiều máy Reverb: bật `REVERB_SCALING_ENABLED=true`, các máy dùng Redis pub/sub chung để chuyển
  tin cho nhau, đặt sau load balancer.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Job "chạy" nhưng thật ra chạy ngay trong request | Thiếu `implements ShouldQueue`, hoặc `QUEUE_CONNECTION=sync` trên production | Tạo job bằng `make:job`; kiểm tra `php artisan about` sau deploy |
| Job không bao giờ chạy | Không có worker, hoặc worker nghe sai connection/queue (`--queue`) | Chạy worker qua Supervisor/Horizon; `--queue` liệt kê đủ các queue đang dùng |
| Worker chạy code cũ sau deploy | `queue:work` nạp code một lần | `queue:restart` (hoặc `horizon:terminate`) trong script deploy; cache dùng chung |
| Job chạy hai, ba lần; hoặc nằm trong `failed_jobs` dù đã chạy thành công | `timeout` ≥ `retry_after` | `timeout` nhỏ hơn `retry_after` vài giây; job dài tách connection riêng |
| Job thất bại dù `handle()` chưa từng chạy | Bị release bởi `RateLimited`/`WithoutOverlapping` với `tries = 1` | Tăng `Tries`, hoặc `retryUntil()` cộng `MaxExceptions` |
| Mọi job cùng key bị release mãi rồi thất bại | Lock của `WithoutOverlapping` không có `expireAfter`, worker bị SIGKILL nên lock kẹt | Luôn đặt `expireAfter` lớn hơn timeout của job |
| `ModelNotFoundException` trong job, hoặc job chạy cho dữ liệu đã rollback | Dispatch trong transaction | `->afterCommit()`, `after_commit => true`, các interface `...AfterCommit` |
| Job gửi email/trừ tiền hai lần | Job không idempotent, mà job thì luôn có thể chạy lại | Kiểm tra trạng thái, idempotency key, unique constraint |
| Job dùng giá trị "lúc dispatch" nhưng nhận giá trị mới | `SerializesModels` query lại model lúc chạy | Truyền giá trị scalar cần giữ nguyên vào constructor |
| Thêm server thì task định kỳ chạy N lần | Mỗi server một dòng cron | `onOneServer()` với cache dùng chung, hoặc chỉ một instance chạy cron |
| Task định kỳ ngừng chạy cả ngày, không báo lỗi | Lock `withoutOverlapping` kẹt sau khi process bị kill, mặc định 24 giờ | `withoutOverlapping(N phút)`; `schedule:clear-cache`; `pingOnFailure`/giám sát |
| Unique job, `onOneServer`, `queue:restart` không có tác dụng trên nhiều server | Cache là `file` hoặc `array`, mỗi máy một bản | Dùng Redis/database làm cache chung |
| Listener làm request chậm hoặc lỗi 500 | Listener đồng bộ chạy trong request | `implements ShouldQueue` cho listener chậm hoặc gọi dịch vụ ngoài |
| Người dùng thấy dữ liệu của người khác từ cache | Key cache thiếu user id/tham số | Key chứa mọi thứ làm kết quả khác đi |
| Query vẫn chạy mỗi request dù đã `remember` | Closure trả `null`, `remember` coi `null` là miss | Cache một giá trị khác `null` cho trường hợp "không có" |
| `Cache::flush()` xoá mất job/dữ liệu của app khác | `flush` bỏ qua prefix, xoá cả store | Tách Redis database cho cache; xoá theo key hoặc tag |
| DB quá tải mỗi khi key nóng hết hạn | Cache stampede; `remember` không phối hợp giữa request | `Cache::flexible`, lock, jitter TTL, làm ấm cache |
| Lỗi khi đọc object từ cache sau khi lên Laravel 13 | `serializable_classes => false` chặn unserialize object | Liệt kê class được phép hoặc cache mảng |
| Gửi email trong vòng lặp, người sau nhận cả email của người trước | `to()` cộng dồn người nhận vào cùng một mailable | Tạo mailable mới cho mỗi người nhận |
| Dữ liệu nhạy cảm lộ ra trình duyệt qua broadcast | Mọi property public của event được gửi đi | `broadcastWith()` chỉ trả trường cần thiết; phân quyền channel |

## Tóm tắt chương

- Queue tách việc "làm sau cũng được" khỏi request: producer serialize job vào backend, worker (process riêng)
  lấy ra, chạy, rồi xoá, release hoặc chuyển sang `failed_jobs`. Connection là backend, queue là tên hàng đợi bên
  trong connection.
- Attempt là một lần job được lấy ra, tăng ngay lúc lấy; release, timeout và chạy xong đều tiêu attempt. Mặc định
  `tries = 1`, `timeout = 60`, `retry_after = 90` (project mới).
- Timeout do worker thực thi bằng `SIGALRM` rồi tự `SIGKILL` (cần `pcntl`, `finally` không chạy); `retry_after` do
  queue thực thi để cứu job của worker chết. Luôn giữ `timeout` < `retry_after`, nếu không job chạy chồng nhiều lần.
- Job phải idempotent; unique job (chặn lúc dispatch), `WithoutOverlapping` (chặn lúc chạy), `RateLimited` không
  thay được điều đó. Dispatch trong transaction cần `afterCommit`.
- `queue:work` là process sống lâu: phải có Supervisor (với `stopwaitsecs` đủ lớn), restart khi deploy bằng
  `queue:restart` qua cache dùng chung. Horizon quản lý worker cho Redis; `balance => auto` không ưu tiên theo thứ
  tự queue.
- Event tách code; listener đồng bộ chạy trong request, listener `ShouldQueue` thành job riêng. Ba interface
  `ShouldDispatchAfterCommit`, `ShouldQueueAfterCommit`, `ShouldHandleEventsAfterCommit` xử lý chuyện transaction.
- Scheduler: một dòng cron gọi `schedule:run` mỗi phút; `withoutOverlapping` chặn lượt chồng lượt,
  `onOneServer` chặn nhiều server cùng chạy một lượt; cả hai cần cache lock dùng chung.
- Cache: `remember` là cache-aside, không chống stampede; `flexible` trả bản cũ và làm mới ở nền có lock; atomic
  lock dùng owner token để không nhả nhầm lock của người khác; TTL lock phải dài hơn việc cần làm.
- Mail và notification nên đi qua queue; notification queued tạo một job cho mỗi cặp người nhận và kênh.
- Broadcasting đẩy event xuống trình duyệt qua WebSocket server (Reverb, Pusher...); Reverb cũng là process sống
  lâu cần quản lý như worker.

## Câu hỏi tự kiểm tra

1. Phân biệt connection và queue trong `config/queue.php`. Lệnh `php artisan queue:work redis --queue=high,low`
   xử lý những job nào, theo thứ tự nào, và rủi ro gì với queue `low`? (mục 2.1, 3.1)
2. Vì sao gán `$p = SendWelcomeEmail::dispatch($user);` có thể làm job được đẩy muộn hơn dự kiến? (mục 2.4)
3. "Attempt" là gì? Kể bốn tình huống tiêu một attempt mà `handle()` không ném exception. (mục 3.2)
4. Giải thích bằng timeline vì sao `#[Timeout(150)]` với `retry_after = 90` có thể làm email gửi ba lần và job
   vẫn nằm trong `failed_jobs`. Sửa cấu hình thế nào? (mục 3.5)
5. Timeout của worker hoạt động thế nào ở mức process? Vì sao lock lấy trong job có thể không bao giờ được nhả
   khi job bị timeout? (mục 3.4, 4.2)
6. So sánh `ShouldBeUnique`, `WithoutOverlapping` và `RateLimited`: mỗi cái chặn ở thời điểm nào và job trùng
   bị xử lý ra sao? Vì sao không cái nào thay được job idempotent?
7. Dispatch job (hoặc bắn event có queued listener) trong `DB::transaction` có thể gây lỗi gì? Nêu các cách sửa
   ở mức job, connection, event và listener. (mục 2.6, 6.4)
8. Một app chạy trên 4 server, mỗi server có cron `schedule:run`, cache store là `file`. Task gửi báo cáo có
   `onOneServer()`. Báo cáo được gửi mấy lần, vì sao? (mục 7.4)
9. Vì sao `Cache::remember` không chống được cache stampede, còn `Cache::flexible` thì giảm được? `flexible` còn
   để hở trường hợp nào? (mục 8.5)
10. Atomic lock của Laravel dùng owner token để làm gì? Điều gì xảy ra khi TTL của lock ngắn hơn thời gian làm
    việc? (mục 8.4)

## Bài tập

1. **Mở rộng queue tí hon (PHP thuần).** Lấy ví dụ ở mục 1.3 và thêm: (a) backoff dạng mảng `[1, 5, 10]` giống
   `#[Backoff]` (dùng đồng hồ giả thay cho `time()` để không phải chờ thật); (b) `retry_after`: `pop()` lấy cả
   job đã reserved quá N giây; (c) mô phỏng một worker "chết" giữa chừng (lấy job nhưng không xoá) và chứng minh
   job được worker thứ hai lấy lại với `attempts = 2`. In ra timeline giống bảng ở mục 3.5.
2. **Tái hiện lỗi `timeout` ≥ `retry_after` (PHP thuần).** Với hàng đợi ở bài 1 và đồng hồ giả, cho một job "chạy"
   120 giây, `retry_after = 90`, hai worker luân phiên. Đếm số lần job chạy và kiểm tra job có rơi vào
   `failed_jobs` không khi `maxTries = 3`. Sau đó đổi cấu hình theo quy tắc ở mục 3.5 và cho thấy kết quả khác đi.
3. **Cache stampede (PHP thuần).** Viết một store giả có đồng hồ giả và một hàm `remember()`. Mô phỏng 50
   "request" cùng đến lúc key vừa hết hạn và đếm số lần query nặng chạy. Sau đó cài một bản `flexible()` đơn giản
   (lưu kèm thời điểm tạo, trả bản cũ trong khoảng stale, chỉ một request được làm mới nhờ lock kiểu mục 8.4) và
   so sánh số lần query.
4. **Laravel (cần một project Laravel 13).** Dùng driver `database`: tạo job `GenerateReport` có
   `#[Tries(3)]`, `#[Backoff([5, 15])]`, ném exception ở hai attempt đầu và thành công ở attempt thứ ba (dựa vào
   `$this->attempts()`). Dispatch nó, mở bảng `jobs` xem cột `attempts`, `available_at` thay đổi sau mỗi lần thử
   (chạy `php artisan queue:work --once` từng lần). Thêm một listener queued cho event `ReportGenerated` và một task
   `Schedule::job(new GenerateReport())->everyMinute()->withoutOverlapping(5)`; dùng `schedule:work` và
   `event:list` để quan sát.

## Đọc thêm

- [Laravel 13.x: Queues](https://laravel.com/docs/13.x/queues) (Connections vs. Queues, Unique Jobs, Job
  Middleware, Jobs & Database Transactions, Job Chaining, Job Batching, Max Attempts / Timeout, Running the Queue
  Worker, Supervisor Configuration, Dealing With Failed Jobs)
- [Laravel 13.x: Horizon](https://laravel.com/docs/13.x/horizon) (Balancing Strategies, Job Timeout, Deploying
  Horizon, Metrics)
- [Laravel 13.x: Events](https://laravel.com/docs/13.x/events) (Event Discovery, Queued Event Listeners,
  Dispatching Events After Database Transactions, Deferring Events)
- [Laravel 13.x: Task Scheduling](https://laravel.com/docs/13.x/scheduling) (Preventing Task Overlaps, Running
  Tasks on One Server, Sub-Minute Scheduled Tasks)
- [Laravel 13.x: Cache](https://laravel.com/docs/13.x/cache) (Stale While Revalidate, Cache Memoization, Cache
  Tags, Atomic Locks)
- [Laravel 13.x: Mail](https://laravel.com/docs/13.x/mail) và
  [Notifications](https://laravel.com/docs/13.x/notifications)
- [Laravel 13.x: Broadcasting](https://laravel.com/docs/13.x/broadcasting) và
  [Reverb](https://laravel.com/docs/13.x/reverb)
- [Laravel 13.x: Upgrade Guide](https://laravel.com/docs/13.x/upgrade) (Cache `serializable_classes`, Collection
  Model Serialization Restores Eager-Loaded Relations)
- Mã nguồn [`laravel/framework` nhánh 13.x](https://github.com/laravel/framework/tree/13.x/src/Illuminate):
  `Queue/Worker.php`, `Queue/WorkerOptions.php`, `Queue/Console/WorkCommand.php`, `Queue/Queue.php`
  (`createObjectPayload`), `Queue/DatabaseQueue.php`, `Queue/SerializesAndRestoresModelIdentifiers.php`,
  `Queue/Middleware/WithoutOverlapping.php`, `Bus/UniqueLock.php`, `Foundation/Bus/PendingDispatch.php`,
  `Events/Dispatcher.php`, `Events/CallQueuedListener.php`, `Console/Scheduling/CacheSchedulingMutex.php`,
  `Console/Scheduling/Event.php`, `Cache/Repository.php` (`remember`, `flexible`), `Cache/RedisLock.php`
- [laravel/laravel 13.x](https://github.com/laravel/laravel/tree/13.x): `config/queue.php`, `config/cache.php`,
  `database/migrations/0001_01_01_000002_create_jobs_table.php`
- [Supervisor: cấu hình `[program:x]`](http://supervisord.org/configuration.html#program-x-section-settings)
  (`autorestart`, `stopwaitsecs`)
- Tài liệu liên quan trong repo: [Cache](../11-cache.md), [Messaging](../../12-messaging.md) (delivery semantics,
  outbox)
