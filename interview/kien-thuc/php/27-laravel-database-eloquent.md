# Chương 27. Database trong Laravel: migration, query builder, Eloquent

> [← Mục lục](README.md) · [← Chương 26: Service container, provider, facade và vòng đời request](26-laravel-container-provider-facade.md) · [Chương 28: Xác thực và phân quyền trong Laravel →](28-laravel-auth.md)

**Bạn sẽ học được:**

- Laravel nói chuyện với database qua ba tầng (SQL thô qua facade `DB`, *query builder*, *Eloquent
  ORM*), mỗi tầng hợp với việc gì, và cấu hình connection trong `config/database.php`.
- Quản lý schema bằng *migration*: tạo bảng, thêm cột, index, khoá ngoại, chạy và rollback, cùng
  những cái bẫy riêng của MySQL (DDL không nằm trong transaction, khoá bảng khi `ALTER`).
- Sinh dữ liệu mẫu bằng *seeder* và *factory*.
- Eloquent từ đầu: model và quy ước đặt tên, đọc ghi, *mass assignment*, cast, accessor, mutator,
  scope, soft delete, model event, observer.
- Relationship (1-1, 1-n, n-n, has-many-through, polymorphic), *eager loading* và bài toán N+1, cách
  bắt N+1 bằng `preventLazyLoading`.
- Làm việc với dữ liệu lớn và đồng thời: `chunk`/`lazy`/`cursor`, transaction và retry khi deadlock,
  phân trang offset và cursor, `upsert`, raw query an toàn.

**Cần biết trước:** [Chương 16](16-php-va-database.md) (PDO, prepared statement, transaction ở mức
PHP thuần) là nền bắt buộc: mọi thứ trong chương này cuối cùng đều gọi PDO. [Chương 23](23-laravel-gioi-thieu.md)
(cấu trúc dự án, `.env`, `config()`, Artisan) và [Chương 26](26-laravel-container-provider-facade.md)
(facade, service provider) để hiểu `DB::...` và `AppServiceProvider::boot()` là gì. Về SQL: nên đọc
giáo trình [Database](../database/README.md), ít nhất các chương
[04 (DDL, constraint)](../database/04-ddl-constraint.md), [05 (SELECT)](../database/05-select-co-ban.md)
và [07 (JOIN)](../database/07-join.md). Chương này không dạy lại SQL; nó dạy cách Laravel sinh SQL và
những gì Laravel làm thêm quanh câu SQL đó.

Một lưu ý về ví dụ: máy soạn giáo trình không chạy được Laravel hay MySQL. Đoạn cấu hình và đoạn mã
trích từ framework được chép từ repo chính thức nhánh `13.x` (`laravel/laravel`, `laravel/framework`,
`laravel/docs`). Câu SQL mà Laravel sinh ra được ghi theo mã nguồn grammar của framework; chỗ nào là
output minh hoạ thì ghi rõ. Đoạn PHP thuần (không cần Laravel) đã được chạy thật trên PHP 8.5.

Dự án mẫu xuyên suốt chương: một blog nhỏ có `users`, `posts`, `comments`, `tags`. Mỗi mục thêm dần
bảng và model cho dự án đó.

## 1. Laravel nói chuyện với database thế nào

### 1.1 Ba tầng: SQL thô, query builder, Eloquent

Ở [Chương 16](16-php-va-database.md) bạn đã viết PDO tay: mở kết nối, `prepare`, `execute`, `fetch`.
Laravel không thay PDO; nó bọc PDO thêm ba tầng tiện dụng, tầng sau dựng trên tầng trước:

```
  Code của bạn
      │
      ├── Eloquent ORM        Post::where('published', true)->with('author')->get()
      │      │                (trả về object model, có event, cast, relationship)
      │      ▼
      ├── Query builder       DB::table('posts')->where('published', true)->get()
      │      │                (dựng câu SQL bằng method, trả về stdClass)
      │      ▼
      ├── Connection (DB)     DB::select('select * from posts where published = ?', [1])
      │      │                (gửi SQL thô kèm binding, ghi log, đo thời gian, quản lý transaction)
      │      ▼
      └── PDO  ──────────────► MySQL / PostgreSQL / SQLite / SQL Server / MariaDB
```

- *Connection* (lớp `Illuminate\Database\Connection`, gọi qua facade `DB`): nhận câu SQL bạn viết
  sẵn cùng mảng giá trị, chuẩn bị bằng PDO, chạy, trả kết quả. Mọi tầng trên đều đi qua đây.
- *Query builder* (lớp `Illuminate\Database\Query\Builder`): bạn gọi method (`where`, `join`,
  `orderBy`...), builder ghép thành câu SQL đúng cú pháp của từng database nhờ một *grammar* riêng cho
  mỗi loại (MySQL dùng backtick quanh tên cột, PostgreSQL dùng nháy kép...).
- *Eloquent* (lớp `Illuminate\Database\Eloquent\Model` và `Eloquent\Builder`): mỗi bảng có một class
  *model*, mỗi dòng trở thành một object. Eloquent dùng query builder để sinh SQL, rồi dựng object từ
  kết quả (gọi là *hydrate*), và thêm nhiều hành vi: event, cast, relationship, soft delete.

Theo tài liệu 13.x, Laravel hỗ trợ chính thức năm hệ: MariaDB 10.3+, MySQL 5.7+, PostgreSQL 10.0+,
SQLite 3.26.0+, SQL Server 2017+. MongoDB có package riêng do MongoDB duy trì.

Vì sao cần ba tầng thay vì một? Vì mỗi tầng có giá khác nhau:

| | SQL thô (`DB::select`) | Query builder | Eloquent |
|---|---|---|---|
| Viết | Chuỗi SQL | Method nối nhau | Method trên model |
| Kết quả | mảng `stdClass` | `Collection` các `stdClass` | `Collection` các model |
| Đổi database (MySQL sang PostgreSQL) | Phải sửa SQL | Grammar lo phần lớn | Grammar lo phần lớn |
| Event, cast, relationship | Không | Không | Có |
| Chi phí mỗi dòng | Thấp nhất | Thấp | Cao hơn (dựng object, cast, giữ bản gốc để so thay đổi) |
| Hợp với | Báo cáo phức tạp, window function, CTE | Thao tác hàng loạt, truy vấn động | Nghiệp vụ theo từng bản ghi |

Trong một dự án thật cả ba cùng tồn tại. Mục 4 (query builder) và mục 5 trở đi (Eloquent) đi vào
từng tầng.

### 1.2 Cấu hình connection: `.env` và `config/database.php`

Toàn bộ cấu hình database nằm ở `config/database.php`. Giá trị cụ thể (host, mật khẩu) lấy từ biến môi
trường trong `.env` qua hàm `env()` (cơ chế `.env` và `config()` ở [Chương 23](23-laravel-gioi-thieu.md)).

Skeleton Laravel 13 mặc định dùng SQLite cho dễ bắt đầu. File `.env.example` của skeleton:

```ini
DB_CONNECTION=sqlite
# DB_HOST=127.0.0.1
# DB_PORT=3306
# DB_DATABASE=laravel
# DB_USERNAME=root
# DB_PASSWORD=
```

Chuyển sang MySQL thì bỏ comment và sửa giá trị:

```ini
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=blog
DB_USERNAME=blog
DB_PASSWORD=secret
```

Phần connection `mysql` trong `config/database.php` của skeleton 13.x (chép nguyên văn):

```php
'default' => env('DB_CONNECTION', 'sqlite'),

'connections' => [
    // ... sqlite ...
    'mysql' => [
        'driver' => 'mysql',
        'url' => env('DB_URL'),
        'host' => env('DB_HOST', '127.0.0.1'),
        'port' => env('DB_PORT', '3306'),
        'database' => env('DB_DATABASE', 'laravel'),
        'username' => env('DB_USERNAME', 'root'),
        'password' => env('DB_PASSWORD', ''),
        'unix_socket' => env('DB_SOCKET', ''),
        'charset' => env('DB_CHARSET', 'utf8mb4'),
        'collation' => env('DB_COLLATION', 'utf8mb4_unicode_ci'),
        'prefix' => '',
        'prefix_indexes' => true,
        'strict' => true,
        'engine' => null,
        'options' => extension_loaded('pdo_mysql') ? array_filter([
            Mysql::ATTR_SSL_CA => env('MYSQL_ATTR_SSL_CA'),
        ]) : [],
    ],
    // ... mariadb, pgsql, sqlsrv ...
],
```

Các khoá đáng chú ý:

- `default`: connection dùng khi bạn không chỉ định. Một app có thể khai nhiều connection (ví dụ
  `mysql` cho nghiệp vụ và `analytics` cho kho báo cáo) rồi chọn bằng `DB::connection('analytics')`.
- `url` / `DB_URL`: nhiều nhà cung cấp managed database đưa một chuỗi duy nhất dạng
  `mysql://user:pass@host:port/database?options`. Có `url` thì Laravel tách thông tin từ chuỗi đó.
- `charset` = `utf8mb4`: bảng mã đủ 4 byte của MySQL, chứa được emoji. Lý do không dùng `utf8` (thực
  chất là `utf8mb3`, tối đa 3 byte) nằm ở [Database chương 03](../database/03-kieu-du-lieu.md).
- `prefix`: tiền tố tự thêm vào tên bảng, ít dùng.
- `strict`: quyết định `sql_mode` mà Laravel đặt cho session ngay khi kết nối. Đọc `MySqlConnector`
  13.x:
  - `strict => true` với MySQL từ 8.0.11: `SET SESSION sql_mode='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'`.
  - `strict => false`: chỉ `NO_ENGINE_SUBSTITUTION`, tức tắt strict mode.
  - Có khoá `modes` (mảng) thì dùng đúng danh sách đó; không có khoá `strict` thì để nguyên
    `sql_mode` của server.
- `options`: mảng attribute truyền vào constructor PDO.

⚠️ Đặt `strict => false` để "chữa" lỗi là che bug. Không có `STRICT_TRANS_TABLES`, MySQL lặng lẽ cắt
chuỗi dài hơn cột, đổi giá trị sai kiểu thành 0, và chỉ báo warning mà Laravel không hiển thị. Không
có `ONLY_FULL_GROUP_BY`, câu `GROUP BY` thiếu cột trả về giá trị tuỳ ý. Lỗi thường gặp nhất khi mới
chuyển sang MySQL 8 là `GROUP BY` bị từ chối vì `ONLY_FULL_GROUP_BY`; cách đúng là sửa câu query
([Database chương 08](../database/08-group-by-aggregate.md)), không phải tắt strict.

Ngoài ra, mọi connection Laravel mở đều dùng một bộ attribute PDO mặc định (mảng `$options` trong
`Connectors/Connector.php` 13.x): `ATTR_ERRMODE => ERRMODE_EXCEPTION` (lỗi SQL thành exception),
`ATTR_EMULATE_PREPARES => false` (prepare thật trên server), `ATTR_STRINGIFY_FETCHES => false`,
`ATTR_CASE => CASE_NATURAL`, `ATTR_ORACLE_NULLS => NULL_NATURAL`. Ý nghĩa từng attribute đã học ở
[Chương 16, mục 2.4](16-php-va-database.md). Hệ quả cần nhớ: bạn không bao giờ phải tự kiểm tra
`false` sau mỗi câu query như PDO ở chế độ silent; lỗi luôn là `Illuminate\Database\QueryException`
(bọc `PDOException`, kèm câu SQL và binding).

### 1.3 Connection mở khi nào, sống bao lâu

Laravel mở connection *lazy*: đăng ký cấu hình lúc boot, nhưng chỉ thật sự gọi `new PDO(...)` khi có
câu query đầu tiên. Request không đụng database thì không tốn kết nối.

Dưới PHP-FPM, mỗi worker xử lý một request một lúc và connection đóng khi request kết thúc (trừ khi bật
persistent connection). Không có *connection pool* dùng chung như Java hay Go. Hệ quả: số connection
tới MySQL xấp xỉ số worker đang chạy, cộng queue worker và cron. Công thức ước lượng và chuyện
`max_connections` ở [Database chương 19](../database/19-database-tu-ung-dung.md); vòng đời worker ở
[Chương 18](18-fpm-nginx-opcache.md). Với Octane (process sống lâu), connection sống qua nhiều request,
xem [Chương 30](30-laravel-testing-octane-deploy.md).

### 1.4 Read/write connection và `sticky`

Hệ thống lớn thường có một máy *primary* nhận ghi và vài máy *replica* sao chép từ primary để chia tải
đọc ([Database chương 22](../database/22-replication-ha.md)). Laravel cho khai hai nhóm host trong cùng
một connection:

```php
'mysql' => [
    'driver' => 'mysql',
    'read' => [
        'host' => ['10.0.0.11', '10.0.0.12'],   // replica
    ],
    'write' => [
        'host' => ['10.0.0.10'],                // primary
    ],
    'sticky' => true,
    // database, username, password, charset... dùng chung cho cả read và write
],
```

- Câu `SELECT` đi connection read, câu ghi (`INSERT`, `UPDATE`, `DELETE`, statement) đi connection
  write. Áp dụng cho cả SQL thô, query builder và Eloquent.
- Nhiều host trong mảng thì mỗi request chọn ngẫu nhiên một host.
- Trong transaction, mọi câu đều chạy trên connection write. Muốn ép một câu đọc đi primary:
  `->useWritePdo()` (hoặc `lockForUpdate()`, vì khoá dòng chỉ có nghĩa trên primary).
- `sticky => true`: trong cùng một request, sau khi đã có câu ghi, mọi câu đọc tiếp theo dùng
  connection write. Mục đích: đọc thấy ngay thứ mình vừa ghi, dù replica chưa kịp nhận.

⚠️ `sticky` chỉ có tác dụng trong một request. Người dùng sửa hồ sơ, trang redirect sang request mới,
request đó đọc replica đang trễ vài trăm mili giây và thấy dữ liệu cũ. Queue job chạy ngay sau khi ghi
cũng có thể đọc replica chưa cập nhật. Muốn "đọc thấy thứ mình vừa ghi" xuyên request thì phải tự làm
(ví dụ đánh dấu trong session và đọc primary vài giây sau đó).

### 1.5 Chạy SQL thô qua facade `DB`

Tầng thấp nhất. Facade `DB` có một method cho mỗi loại câu lệnh:

```php
use Illuminate\Support\Facades\DB;

// SELECT: luôn trả mảng các stdClass
$users = DB::select('select id, name from users where active = ?', [1]);
foreach ($users as $user) {
    echo $user->name;
}

// Binding có tên
$rows = DB::select('select * from users where id = :id', ['id' => 1]);

// Một giá trị đơn
$total = DB::scalar('select count(*) from users');

// INSERT: trả bool
DB::insert('insert into users (name, email) values (?, ?)', ['An', 'an@example.com']);

// UPDATE, DELETE: trả số dòng bị ảnh hưởng
$affected = DB::update('update users set active = 0 where last_login_at < ?', ['2025-01-01']);
$deleted  = DB::delete('delete from sessions where last_activity < ?', [1700000000]);

// Câu không trả gì (DDL...)
DB::statement('drop table if exists tmp_import');

// Connection khác
$rows = DB::connection('analytics')->select('select ...');

// PDO gốc khi thật sự cần
$pdo = DB::connection()->getPdo();
```

Mảng thứ hai là *binding*: giá trị được gửi tách khỏi câu SQL qua prepared statement, nên không bị SQL
injection ([Chương 16, mục 3.3](16-php-va-database.md)).

⚠️ `DB::unprepared($sql)` gửi câu SQL không qua prepare và không nhận binding. Tài liệu Laravel cảnh
báo: không bao giờ đưa giá trị do người dùng kiểm soát vào đây.

⚠️ *Implicit commit*: trong MySQL, các câu DDL như `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`,
`TRUNCATE` tự commit transaction đang mở. Chạy chúng bằng `DB::statement()` hay `DB::unprepared()`
bên trong `DB::transaction()` thì transaction bị commit ngầm, Laravel không biết, và bộ đếm cấp
transaction của Laravel lệch với thực tế (tài liệu Laravel, mục *Implicit Commits*). Danh sách đầy đủ
các câu gây implicit commit ở [Database chương 13](../database/13-transaction-acid.md).

### 1.6 Công cụ Artisan để nhìn vào database

```bash
# Chạy ở thư mục gốc dự án Laravel
php artisan db                 # mở client dòng lệnh (mysql, psql...) với thông tin từ config
php artisan db:show            # tổng quan: loại DB, kích thước, số connection đang mở, danh sách bảng
php artisan db:show --counts   # kèm số dòng mỗi bảng (chậm trên DB lớn)
php artisan db:table users     # cột, kiểu, index, khoá ngoại của một bảng
php artisan db:monitor --databases=mysql --max=100   # bắn event DatabaseBusy khi quá 100 connection
```

Trong code, facade `Schema` cho đọc cấu trúc: `Schema::getColumns('users')`,
`Schema::getIndexes('users')`, `Schema::getForeignKeys('users')`, `Schema::hasColumn('users', 'email')`.

## 2. Migration: quản lý schema bằng code

### 2.1 Migration là gì, vì sao cần

Hình dung đội ba người. Bạn thêm cột `status` vào bảng `posts` trên máy mình bằng một câu `ALTER TABLE`
gõ tay. Đồng nghiệp kéo code về, chạy app, lỗi "Unknown column 'status'". Họ phải hỏi bạn đã sửa gì
trong database. Lên production lại phải nhớ chạy đúng câu đó, đúng thứ tự với các thay đổi khác.

*Migration* giải quyết việc này: mỗi thay đổi schema là một file PHP nằm trong git, có thứ tự rõ ràng.
Tài liệu Laravel gọi migration là "version control cho database". Ai kéo code về chỉ cần chạy
`php artisan migrate`, Laravel tự biết file nào đã chạy, file nào chưa, và chạy phần còn thiếu.

Laravel biết "đã chạy hay chưa" nhờ một bảng tên `migrations` mà nó tự tạo trong database của bạn:

```
migrations
+----+-------------------------------------------+-------+
| id | migration                                 | batch |
+----+-------------------------------------------+-------+
|  1 | 0001_01_01_000000_create_users_table      |     1 |
|  2 | 0001_01_01_000001_create_cache_table      |     1 |
|  3 | 0001_01_01_000002_create_jobs_table       |     1 |
|  4 | 2026_10_03_081500_create_posts_table      |     2 |
+----+-------------------------------------------+-------+
(output minh hoạ)
```

- Cột `migration`: tên file (bỏ đuôi `.php`). File có trong thư mục mà không có dòng ở đây là
  "pending", sẽ chạy ở lần `migrate` tới.
- Cột `batch`: số thứ tự của lần chạy `migrate`. Mọi file chạy trong cùng một lệnh `migrate` có cùng
  batch. `migrate:rollback` mặc định lùi lại nguyên batch cuối cùng.
- Thứ tự chạy theo tên file, mà tên file bắt đầu bằng thời điểm tạo, nên file cũ chạy trước.

Ba file `0001_01_01_...` ở trên là migration có sẵn trong skeleton Laravel 13 (tạo bảng `users`,
`password_reset_tokens`, `sessions`, `cache`, `jobs`...). Tiền tố `0001_01_01` bảo đảm chúng luôn chạy
trước migration của bạn.

### 2.2 Tạo một migration

```bash
# Chạy ở thư mục gốc dự án
php artisan make:migration create_posts_table
# Tạo file database/migrations/2026_10_03_081500_create_posts_table.php (phần thời gian là lúc bạn chạy lệnh)
```

Laravel đoán tên bảng từ tên migration: `create_posts_table` thì sinh sẵn khung `Schema::create('posts', ...)`;
`add_status_to_posts_table` thì sinh khung `Schema::table('posts', ...)`. Đoán không được thì bạn tự
điền.

Một file migration là một *anonymous class* (class không tên, [Chương 10](10-oop-nang-cao.md)) kế thừa
`Migration`, có hai method:

```php
<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    // Chạy khi migrate: áp thay đổi
    public function up(): void
    {
        Schema::create('posts', function (Blueprint $table) {
            $table->id();                                         // BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('title');                              // VARCHAR(255)
            $table->string('slug')->unique();
            $table->text('body');
            $table->boolean('published')->default(false);         // TINYINT(1) trên MySQL
            $table->timestamp('published_at')->nullable();
            $table->timestamps();                                 // created_at, updated_at (nullable)
            $table->index(['published', 'published_at']);
        });
    }

    // Chạy khi rollback: hoàn tác đúng những gì up() đã làm
    public function down(): void
    {
        Schema::dropIfExists('posts');
    }
};
```

Vì sao là anonymous class? Trước Laravel 8.37, mỗi migration là một class có tên (`CreatePostsTable`).
Hai migration trùng tên class (rất dễ xảy ra trong dự án lâu năm, ví dụ hai lần "add_status_to_posts")
làm PHP báo lỗi khai báo class trùng. Class không tên thì không bao giờ trùng.

`Schema::create` nhận tên bảng và một closure. Closure nhận object `Blueprint`, bạn gọi method trên nó
để mô tả cột. Laravel gom mô tả lại, đưa cho grammar của MySQL dịch thành câu SQL. Muốn xem SQL mà
không chạy thật: `php artisan migrate --pretend`. Với migration trên, MySQL nhận đại ý:

```sql
-- output minh hoạ, rút gọn
create table `posts` (`id` bigint unsigned not null auto_increment primary key,
  `user_id` bigint unsigned not null, `title` varchar(255) not null, `slug` varchar(255) not null,
  `body` text not null, `published` tinyint(1) not null default '0',
  `published_at` timestamp null, `created_at` timestamp null, `updated_at` timestamp null)
  default character set utf8mb4 collate 'utf8mb4_unicode_ci';
alter table `posts` add constraint `posts_user_id_foreign` foreign key (`user_id`)
  references `users` (`id`) on delete cascade;
alter table `posts` add index `posts_published_published_at_index`(`published`, `published_at`);
alter table `posts` add unique `posts_slug_unique`(`slug`);
```

Để ý: Laravel không thêm `NOT NULL` hay `NULL` theo ý bạn đoán; mặc định mọi cột là `NOT NULL`, trừ
khi gọi `->nullable()`. Riêng `timestamps()` tạo hai cột nullable (đọc từ `Blueprint::timestamps()`
13.x).

### 2.3 Chạy, xem trạng thái, rollback

```bash
php artisan migrate                    # chạy mọi migration pending, chung một batch mới
php artisan migrate:status             # bảng: migration nào Ran, batch mấy, cái nào Pending
php artisan migrate --pretend          # in SQL, không chạy
php artisan migrate --step             # mỗi file một batch riêng, để rollback từng file

php artisan migrate:rollback           # gọi down() của mọi file trong batch cuối, theo thứ tự ngược
php artisan migrate:rollback --step=2  # lùi 2 file gần nhất
php artisan migrate:rollback --batch=3 # lùi đúng batch 3
php artisan migrate:reset              # lùi tất cả

php artisan migrate:refresh            # reset rồi migrate lại (gọi down() của mọi file)
php artisan migrate:fresh              # DROP mọi bảng rồi migrate từ đầu (KHÔNG gọi down())
php artisan migrate:fresh --seed       # như trên rồi chạy seeder (mục 3)
```

Khác nhau giữa `refresh` và `fresh`: `refresh` tin vào các `down()` của bạn; `down()` viết sai là
lỗi giữa chừng. `fresh` không quan tâm `down()`, xoá sạch bảng rồi dựng lại, nên nhanh và chắc hơn ở
máy dev. Cả hai đều xoá dữ liệu.

⚠️ `migrate:fresh` xoá **mọi** bảng của connection, kể cả bảng không do migration tạo, bất kể prefix
(tài liệu Laravel cảnh báo). Không bao giờ chạy trên database dùng chung với ứng dụng khác.

Trên production:

- Các lệnh có thể làm mất dữ liệu sẽ hỏi xác nhận khi `APP_ENV=production`. Script deploy không có
  người gõ "yes", nên dùng `php artisan migrate --force`.
- Deploy song song lên nhiều server cùng lúc thì hai server có thể cùng chạy migrate. Dùng
  `php artisan migrate --isolated`: Laravel lấy một *atomic lock* qua cache driver mặc định (cần là
  `memcached`, `redis`, `dynamodb`, `database`, `file` hoặc `array`, và mọi server dùng chung một máy
  cache); server không lấy được lock thì bỏ qua và vẫn thoát với mã thành công.
- Trong thực tế, rollback trên production hiếm khi là `migrate:rollback`: `down()` xoá cột là xoá dữ
  liệu đã ghi vào cột đó từ lúc deploy. Cách an toàn hơn là viết một migration mới để "tiến lên" về
  trạng thái mong muốn.

### 2.4 Kiểu cột thường dùng

| Method | MySQL nhận | Ghi chú |
|---|---|---|
| `id()` | `BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY` | Alias của `bigIncrements('id')` |
| `foreignId('user_id')` | `BIGINT UNSIGNED` | Khớp kiểu với `id()` của bảng kia |
| `string('name', 100)` | `VARCHAR(100)` | Không truyền độ dài thì 255 (`Builder::$defaultStringLength`) |
| `text`, `mediumText`, `longText` | `TEXT`... | Không đặt `default` được trên MySQL (trừ biểu thức), không index trọn cột |
| `integer`, `bigInteger`, `unsignedInteger`... | `INT`, `BIGINT`... | |
| `decimal('amount', total: 12, places: 2)` | `DECIMAL(12, 2)` | Dùng cho tiền, không dùng `float` |
| `boolean('active')` | `TINYINT(1)` | |
| `date`, `dateTime`, `timestamp` | `DATE`, `DATETIME`, `TIMESTAMP` | Khác nhau về múi giờ và phạm vi: [Database chương 03](../database/03-kieu-du-lieu.md) |
| `timestamps()` | `created_at`, `updated_at` nullable | Eloquent tự điền (mục 5) |
| `softDeletes()` | `deleted_at TIMESTAMP NULL` | Cho soft delete (mục 7) |
| `json('options')` | `JSON` | SQLite tạo `TEXT` |
| `enum('status', ['draft', 'published'])` | `ENUM(...)` | Thêm giá trị mới là `ALTER TABLE` |
| `uuid('uuid')`, `ulid('ulid')` | `CHAR(36)`, `CHAR(26)` | |
| `morphs('commentable')` | `commentable_type VARCHAR` + `commentable_id BIGINT UNSIGNED` + index | Cho polymorphic (mục 8) |
| `rememberToken()` | `remember_token VARCHAR(100) NULL` | Dùng cho đăng nhập "nhớ tôi" |

Chọn kiểu nào (vì sao không `float` cho tiền, `TIMESTAMP` hay `DATETIME`, vì sao `ENUM` khó đổi) là
chuyện của thiết kế dữ liệu, đã viết kỹ ở [Database chương 03](../database/03-kieu-du-lieu.md). Ở đây
chỉ cần biết method nào ra kiểu nào.

### 2.5 Column modifier

*Modifier* là method nối sau định nghĩa cột để thêm thuộc tính:

```php
$table->string('nickname')->nullable();                  // cho phép NULL
$table->integer('views')->unsigned()->default(0);        // không âm, mặc định 0
$table->string('note')->comment('Ghi chú nội bộ');       // comment cột (MySQL, MariaDB, PostgreSQL)
$table->string('middle_name')->after('first_name');      // vị trí cột (MySQL, MariaDB)
$table->timestamp('seen_at')->useCurrent();              // DEFAULT CURRENT_TIMESTAMP
$table->timestamp('changed_at')->useCurrent()->useCurrentOnUpdate();   // ON UPDATE CURRENT_TIMESTAMP (MySQL)
$table->json('tags')->default(new Expression('(JSON_ARRAY())'));       // default là biểu thức SQL
$table->string('full_name')->virtualAs("concat(first_name, ' ', last_name)");   // generated column
$table->string('secret')->invisible();                   // không hiện trong SELECT * (MySQL, MariaDB)
```

`default()` nhận giá trị thường thì Laravel bọc trong nháy; nhận `Illuminate\Database\Query\Expression`
thì để nguyên, dùng cho hàm của database.

### 2.6 Sửa bảng có sẵn: thêm, đổi, đổi tên, xoá cột

```php
// php artisan make:migration add_status_to_posts_table
public function up(): void
{
    Schema::table('posts', function (Blueprint $table) {
        $table->string('status', 20)->default('draft')->after('slug');
    });
}

public function down(): void
{
    Schema::table('posts', function (Blueprint $table) {
        $table->dropColumn('status');
    });
}
```

Đổi kiểu hoặc thuộc tính của cột có sẵn bằng `->change()`:

```php
Schema::table('users', function (Blueprint $table) {
    $table->string('name', 50)->change();            // VARCHAR(255) -> VARCHAR(50)
});
```

⚠️ Bẫy lớn nhất của `change()`: bạn phải viết **đầy đủ** trạng thái mới của cột. Thuộc tính nào không
viết lại thì bị bỏ. Cột cũ là `integer('votes')->unsigned()->default(1)->comment('...')`, bạn viết
`$table->integer('votes')->nullable()->change()` thì cột mới mất `unsigned`, mất default, mất comment.
Đúng là:

```php
$table->integer('votes')->unsigned()->default(1)->comment('my comment')->nullable()->change();
```

`change()` không đụng tới index của cột; muốn thêm hay bỏ index thì nói rõ (`->unique()`,
`->unique(false)`).

Đổi tên và xoá:

```php
$table->renameColumn('from', 'to');
$table->dropColumn('votes');
$table->dropColumn(['votes', 'avatar']);
$table->dropTimestamps();            // created_at, updated_at
$table->dropSoftDeletes();           // deleted_at
Schema::rename('posts', 'articles'); // đổi tên bảng
Schema::dropIfExists('posts');
```

⚠️ Thay đổi cột trên bảng đang có traffic không vô hại: xoá hay đổi tên cột mà code đang chạy vẫn đọc cột
đó là lỗi ngay khi migration xong và trước khi code mới lên. Quy trình *expand/contract* (thêm cái mới,
chuyển code, rồi mới bỏ cái cũ qua nhiều lần deploy) ở [Database chương 20](../database/20-thay-doi-schema-migration.md).

### 2.7 Index

```php
$table->string('email')->unique();                 // unique index ngay trên định nghĩa cột
$table->unique('email');                           // hoặc khai báo riêng
$table->index(['account_id', 'created_at']);       // composite index, thứ tự cột quan trọng
$table->unique(['post_id', 'tag_id']);             // unique nhiều cột
$table->fullText('body');                          // FULLTEXT (MySQL, MariaDB, PostgreSQL)
$table->primary(['post_id', 'tag_id']);            // khoá chính nhiều cột
$table->unique('email', 'users_email_uq');         // tự đặt tên index
```

Tên index mặc định ghép từ tên bảng, tên cột và loại: `users_email_unique`,
`posts_published_published_at_index`. Xoá index cần tên đó:

```php
$table->dropUnique('users_email_unique');
$table->dropIndex(['state']);     // truyền mảng cột: Laravel tự dựng tên theo quy ước, ở đây là '<bảng>_state_index'
```

Kiểm tra trong code: `Schema::hasIndex('users', ['email'], 'unique')`.

Chọn index nào, thứ tự cột trong composite index, vì sao index không được dùng: [Database chương 11](../database/11-index.md).

### 2.8 Khoá ngoại

*Khoá ngoại* (*foreign key*) là ràng buộc ở database: giá trị `posts.user_id` phải tồn tại trong
`users.id` ([Database chương 04](../database/04-ddl-constraint.md)). Cách viết dài:

```php
$table->unsignedBigInteger('user_id');
$table->foreign('user_id')->references('id')->on('users');
```

Cách viết ngắn theo quy ước, dùng hằng ngày:

```php
$table->foreignId('user_id')->constrained();
// constrained() suy ra bảng 'users' và cột 'id' từ tên cột 'user_id'

$table->foreignId('author_id')->constrained(table: 'users');   // tên cột không theo quy ước
$table->foreignId('category_id')->nullable()->constrained()->nullOnDelete();
// modifier của cột (nullable...) phải gọi TRƯỚC constrained()
```

Hành động khi dòng cha bị xoá hoặc đổi khoá:

| Method | SQL | Ý nghĩa |
|---|---|---|
| `cascadeOnDelete()` | `ON DELETE CASCADE` | Xoá user thì xoá luôn post |
| `restrictOnDelete()` | `ON DELETE RESTRICT` | Còn post thì không cho xoá user |
| `nullOnDelete()` | `ON DELETE SET NULL` | Xoá user thì `user_id` thành NULL (cột phải nullable) |
| `noActionOnDelete()` | `ON DELETE NO ACTION` | Như restrict trên InnoDB |
| `cascadeOnUpdate()`... | `ON UPDATE ...` | Tương tự cho khi đổi khoá cha |

Xoá khoá ngoại: `$table->dropForeign('posts_user_id_foreign')` hoặc `$table->dropForeign(['user_id'])`
(tên mặc định là `<bảng>_<cột>_foreign`). Tạm tắt kiểm tra (ví dụ khi nạp dữ liệu lệch thứ tự):
`Schema::withoutForeignKeyConstraints(function () { ... })`.

⚠️ Hai điểm hay gây nhầm:

- `ON DELETE CASCADE` của database xoá dòng con bằng chính MySQL; Eloquent không biết, nên **không có
  model event** nào cho các comment bị xoá theo (mục 7.4).
- Soft delete (mục 7.3) không phải `DELETE`, nên cascade của khoá ngoại không chạy: xoá mềm post thì
  comment vẫn còn nguyên.

### 2.9 Migration trên MySQL không có tính nguyên tử

Đọc `Migrator::runMigration()` 13.x: Laravel chỉ bọc migration trong transaction khi grammar báo
database hỗ trợ *transactional DDL* (`supportsSchemaTransactions()`). Trong 13.x, grammar của PostgreSQL
và SQL Server bật cờ này; grammar MySQL tắt. Lý do nằm ở MySQL: mỗi câu DDL tự commit (mục 1.5), nên không có cách nào
gói nhiều câu `ALTER` thành một khối "hoặc tất cả, hoặc không".

Hệ quả, với một migration có ba thay đổi:

```php
public function up(): void
{
    Schema::table('posts', function (Blueprint $table) {
        $table->string('status', 20)->default('draft');   // câu 1: thành công, có hiệu lực ngay
        $table->index('statsu');                          // câu 2: gõ nhầm tên cột, lỗi
        $table->string('subtitle')->nullable();           // câu 3: không bao giờ chạy
    });
}
```

| Bước | Điều xảy ra | Trạng thái |
|---|---|---|
| 1 | `ALTER TABLE posts ADD status ...` | Cột `status` đã có trong bảng |
| 2 | `ALTER TABLE posts ADD INDEX (statsu)` lỗi, exception | Laravel dừng |
| 3 | Laravel không ghi dòng vào bảng `migrations` (chỉ ghi khi `up()` chạy xong) | Migration vẫn là "Pending" |
| 4 | Bạn sửa lỗi gõ, chạy lại `migrate` | Câu 1 chạy lại: lỗi "Duplicate column name 'status'" |

Bạn phải tự dọn (xoá cột `status` bằng tay hoặc bọc bằng `Schema::hasColumn`) rồi mới chạy lại được.
Cách phòng: mỗi migration chỉ làm một việc nhỏ, chạy thử bằng `--pretend` và trên bản sao dữ liệu thật
trước khi lên production.

Thêm một hệ quả: trên MySQL, bảng `migrations` và thay đổi schema không đồng bộ tuyệt đối. Process chết
đúng lúc giữa câu `ALTER` và lúc ghi bảng `migrations` thì schema đã đổi mà Laravel tưởng chưa.

### 2.10 `ALTER TABLE` trên bảng lớn: instant, inplace, lock

Trên bảng vài chục triệu dòng, `ALTER TABLE` có thể phải chép lại cả bảng (*table rebuild*), mất hàng
chục phút và chặn ghi. MySQL có ba *algorithm* cho DDL:

| Algorithm | Làm gì | Ví dụ thao tác hỗ trợ (theo bảng Online DDL của MySQL 8.4) |
|---|---|---|
| `INSTANT` | Chỉ sửa metadata trong data dictionary, không đụng dữ liệu | Thêm cột, xoá cột, đổi tên cột, đặt/bỏ default |
| `INPLACE` | Làm trong engine, không chép sang bảng mới theo kiểu COPY; nhiều thao tác cho ghi đồng thời | Tạo secondary index, nới `VARCHAR` |
| `COPY` | Tạo bảng mới, chép từng dòng, đổi tên | Đổi kiểu dữ liệu cột |

Theo MySQL 8.4 Reference Manual, `INSTANT` là algorithm mặc định cho thao tác thêm cột, và từ 8.0.29
có thể thêm cột ở bất kỳ vị trí nào bằng `INSTANT`. Nó có giới hạn: không dùng được với bảng
`ROW_FORMAT=COMPRESSED`, bảng có `FULLTEXT` index, và số cột nội bộ tối đa 1022.

Laravel 13 cho bạn nói rõ algorithm và mức lock mong muốn (chỉ MySQL). Grammar MySQL 13.x nối thêm
`, algorithm=instant`, `, algorithm=inplace`, `, lock=...` vào câu `ALTER`:

```php
$table->string('nickname')->nullable()->instant();      // alter table ... add ..., algorithm=instant
$table->string('nickname')->nullable()->instant()->lock('none');
$table->index('email')->inplace()->lock('none');        // tạo index, cho đọc ghi đồng thời
```

Mức lock: `none` (cho đọc và ghi đồng thời), `shared` (cho đọc, chặn ghi), `exclusive` (chặn hết),
`default` (MySQL tự chọn). Lợi ích của việc ghi rõ: nếu thao tác không làm được theo cách bạn yêu cầu,
MySQL **báo lỗi ngay** thay vì lặng lẽ chuyển sang cách nặng hơn và khoá bảng. Một migration tưởng là
nhẹ mà thành `COPY` trên bảng 50 triệu dòng là sự cố production.

⚠️ Tài liệu Laravel 13.x ghi `instant()` không kết hợp được với `after()`/`first()`, với lý do thêm cột
`INSTANT` chỉ nối được vào cuối bảng. Lý do đó là hành vi của MySQL trước 8.0.29; MySQL 8.4 cho thêm cột
`INSTANT` ở mọi vị trí, và grammar 13.x không chặn việc kết hợp. Cách an toàn: không kết hợp, theo tài
liệu Laravel. Với khoá ngoại, `inplace()` đòi phải tắt `foreign_key_checks`.

⚠️ Ngay cả `INSTANT` cũng cần một *metadata lock* (MDL) độc quyền trong chốc lát. Theo MySQL manual: nếu
có một transaction đang mở (dù chỉ vừa `SELECT` trên bảng đó) thì `ALTER` phải chờ; và trong lúc
`ALTER` chờ, **mọi câu query mới** trên bảng đó xếp hàng sau nó.

| Bước | Session A (worker quên commit) | Session B (migrate) | Session C (request web) | Kết quả |
|---|---|---|---|---|
| 1 | `BEGIN; SELECT * FROM posts ...` | | | A giữ shared MDL trên `posts` |
| 2 | (chưa commit, đang gọi API chậm) | `ALTER TABLE posts ADD ..., ALGORITHM=INSTANT` | | B chờ exclusive MDL: "Waiting for table metadata lock" |
| 3 | | (vẫn chờ) | `SELECT * FROM posts WHERE id = 1` | C bị chặn sau B, dù chỉ là SELECT |
| 4 | | | Hàng trăm request khác | Toàn bộ request đụng `posts` treo, cạn PHP-FPM worker |
| 5 | `COMMIT` | `ALTER` xong trong vài ms | Các query chạy tiếp | Hệ thống hồi lại |

Cách phòng: chạy migration lúc ít traffic, đặt `lock_wait_timeout` ngắn cho session chạy migration để
`ALTER` bỏ cuộc thay vì làm tắc cả hệ thống, và tránh transaction dài trong app. Với thao tác bắt buộc
`COPY` trên bảng lớn, dùng công cụ online schema change (gh-ost, pt-online-schema-change). Chi tiết ở
[Database chương 20](../database/20-thay-doi-schema-migration.md) và [chương 15](../database/15-lock-deadlock.md).

### 2.11 Gom migration: `schema:dump`

Dự án vài năm có hàng trăm file migration; chạy lại từ đầu (trong CI, máy dev mới) rất chậm.

```bash
php artisan schema:dump            # ghi schema hiện tại ra database/schema/mysql-schema.sql
php artisan schema:dump --prune    # đồng thời xoá các file migration cũ
```

Lần sau `migrate` trên database trống, Laravel chạy file SQL đó trước, rồi chạy các migration mới hơn
chưa nằm trong dump. Tính năng này dùng client dòng lệnh của database (`mysqldump`...), chỉ có cho
MariaDB, MySQL, PostgreSQL, SQLite. Nhớ commit file schema vào git.

## 3. Seeder và factory: dữ liệu mẫu

### 3.1 Seeder

Migration tạo **cấu trúc**; bảng sinh ra còn trống. Muốn có dữ liệu để chạy thử (một tài khoản admin,
danh sách tỉnh thành, vài trăm bài viết giả) thì dùng *seeder*: một class có method `run()` chèn dữ
liệu.

```bash
php artisan make:seeder CategorySeeder      # tạo database/seeders/CategorySeeder.php
php artisan db:seed                         # chạy Database\Seeders\DatabaseSeeder
php artisan db:seed --class=CategorySeeder  # chạy một seeder cụ thể
php artisan migrate:fresh --seed            # dựng lại DB từ đầu rồi seed
```

`DatabaseSeeder` là điểm vào, gọi các seeder khác bằng `$this->call([...])`:

```php
<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Console\Seeds\WithoutModelEvents;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class DatabaseSeeder extends Seeder
{
    use WithoutModelEvents;     // có sẵn trong skeleton 13.x: tắt model event trong lúc seed

    public function run(): void
    {
        // Dữ liệu cố định: chèn thẳng bằng query builder
        DB::table('categories')->insert([
            ['name' => 'PHP', 'slug' => 'php'],
            ['name' => 'Database', 'slug' => 'database'],
        ]);

        // Dữ liệu giả: dùng factory (mục 3.2)
        User::factory()->count(10)->create();

        $this->call([
            PostSeeder::class,
        ]);
    }
}
```

`WithoutModelEvents` làm model không bắn event trong suốt quá trình seed (kể cả các seeder gọi qua
`call`). Lý do skeleton bật sẵn: observer gửi email chào mừng hay gọi API ngoài (mục 7.4) không nên chạy
khi bạn tạo 10 user giả. Trên production, `db:seed` hỏi xác nhận; script dùng `--force`.

Phân biệt hai loại dữ liệu seed:

- Dữ liệu tham chiếu mà app cần để chạy (danh mục quyền, cấu hình mặc định): phải giống nhau ở mọi môi
  trường. Nhiều đội đưa loại này vào migration hoặc viết seeder *idempotent* (chạy nhiều lần không sinh
  trùng, ví dụ dùng `upsert` ở mục 12) để chạy được an toàn trên production.
- Dữ liệu giả cho dev và test: chỉ chạy ở máy dev, CI.

### 3.2 Factory

*Factory* là "khuôn" sinh model với dữ liệu ngẫu nhiên hợp lý. Skeleton có sẵn `UserFactory`:

```php
<?php

namespace Database\Factories;

use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Str;

/**
 * @extends Factory<User>
 */
class UserFactory extends Factory
{
    protected static ?string $password;

    // Giá trị mặc định cho mỗi model sinh ra
    public function definition(): array
    {
        return [
            'name' => fake()->name(),
            'email' => fake()->unique()->safeEmail(),
            'email_verified_at' => now(),
            'password' => static::$password ??= Hash::make('password'),   // hash một lần, dùng lại
            'remember_token' => Str::random(10),
        ];
    }

    // Một "state": biến thể của dữ liệu mặc định
    public function unverified(): static
    {
        return $this->state(fn (array $attributes) => [
            'email_verified_at' => null,
        ]);
    }
}
```

`fake()` trả object của thư viện Faker (sinh tên, email, đoạn văn ngẫu nhiên). Dòng
`static::$password ??= Hash::make('password')` có lý do: hash bcrypt cố ý chậm, tạo 1.000 user mà hash
1.000 lần thì seed rất lâu; ở đây chỉ hash lần đầu.

Model dùng được factory nhờ trait `HasFactory`; Laravel tìm class `Database\Factories\<TênModel>Factory`
theo quy ước (khác quy ước thì khai `#[UseFactory(...)]` trên model).

```php
$user  = User::factory()->make();                          // tạo object, CHƯA lưu DB
$user  = User::factory()->create();                        // tạo và lưu (gọi save())
$users = User::factory()->count(3)->unverified()->create();
$user  = User::factory()->create(['name' => 'An']);        // ghi đè một vài field

// Luân phiên giá trị
User::factory()->count(10)->sequence(['role' => 'admin'], ['role' => 'member'])->create();
// 5 admin, 5 member xen kẽ

// Kèm quan hệ (cần relationship đã khai báo trên model, mục 8)
User::factory()->has(Post::factory()->count(3))->create();   // 1 user, 3 post của user đó
User::factory()->hasPosts(3)->create();                      // cách viết tắt (magic method)
Post::factory()->count(3)->for($user)->create();             // 3 post thuộc user có sẵn
```

Factory tự tắt bảo vệ mass assignment (mục 5.5) khi tạo model, nên `definition()` gán được mọi cột.

⚠️ Faker (`fakerphp/faker`) nằm trong `require-dev` của skeleton. Server production cài bằng
`composer install --no-dev` thì không có Faker; seeder gọi factory chạy trên production sẽ lỗi. Đây là
thêm một lý do tách dữ liệu tham chiếu (không dùng factory) khỏi dữ liệu giả.

Factory dùng nhiều nhất trong test, xem [Chương 30](30-laravel-testing-octane-deploy.md).

## 4. Query builder

### 4.1 Builder là gì

`DB::table('posts')` trả về một object `Illuminate\Database\Query\Builder`. Mỗi method như `where`,
`orderBy` chỉ **ghi nhớ** một mảnh của câu SQL vào object rồi trả lại chính object đó (nên nối được
liên tiếp, gọi là *fluent interface*). Chỉ khi gọi một method "kết thúc" như `get()`, `first()`,
`count()`, `update()`, builder mới ghép các mảnh thành SQL, gửi qua connection và trả kết quả.

Để thấy cơ chế, đây là một builder đồ chơi bằng PHP thuần (không phải code Laravel, chỉ mô phỏng ý
tưởng). Chạy được bằng `php toy.php`:

```php
<?php
declare(strict_types=1);

// Một query builder đồ chơi: chỉ để thấy builder gom điều kiện và binding thế nào.
final class ToyBuilder
{
    /** @var list<array{bool: string, sql: string}> */
    private array $wheres = [];
    /** @var list<mixed> */
    private array $bindings = [];

    public function __construct(private readonly string $table) {}

    public function where(string|Closure $column, mixed $value = null, string $bool = 'and'): self
    {
        if ($column instanceof Closure) {
            // Nhóm: chạy closure trên builder con, bọc kết quả trong ngoặc
            $nested = new self($this->table);
            $column($nested);
            $this->wheres[] = ['bool' => $bool, 'sql' => '(' . $nested->compileWheres() . ')'];
            array_push($this->bindings, ...$nested->bindings);
            return $this;
        }
        $this->wheres[] = ['bool' => $bool, 'sql' => "`$column` = ?"];
        $this->bindings[] = $value;   // giá trị KHÔNG nằm trong chuỗi SQL
        return $this;
    }

    public function orWhere(string|Closure $column, mixed $value = null): self
    {
        return $this->where($column, $value, 'or');
    }

    private function compileWheres(): string
    {
        $sql = '';
        foreach ($this->wheres as $i => $w) {
            $sql .= ($i === 0 ? '' : " {$w['bool']} ") . $w['sql'];
        }
        return $sql;
    }

    public function toSql(): string
    {
        return "select * from `{$this->table}` where " . $this->compileWheres();
    }

    /** @return list<mixed> */
    public function getBindings(): array
    {
        return $this->bindings;
    }
}

$q1 = (new ToyBuilder('posts'))
    ->where('user_id', 7)
    ->where('status', 'draft')
    ->orWhere('status', 'review');
echo $q1->toSql(), PHP_EOL;
// in ra: select * from `posts` where `user_id` = ? and `status` = ? or `status` = ?
echo json_encode($q1->getBindings()), PHP_EOL;
// in ra: [7,"draft","review"]

$q2 = (new ToyBuilder('posts'))
    ->where('user_id', 7)
    ->where(fn (ToyBuilder $q) => $q->where('status', 'draft')->orWhere('status', 'review'));
echo $q2->toSql(), PHP_EOL;
// in ra: select * from `posts` where `user_id` = ? and (`status` = ? or `status` = ?)
echo json_encode($q2->getBindings()), PHP_EOL;
// in ra: [7,"draft","review"]
```

Hai điều rút ra, đúng với builder thật của Laravel:

1. Giá trị không bao giờ được ghép vào chuỗi SQL; chúng nằm trong mảng binding và đi qua prepared
   statement. Đó là lý do query builder an toàn với SQL injection **cho giá trị**.
2. Thứ tự gọi method tạo ra đúng thứ tự trong SQL, và SQL ưu tiên `AND` trước `OR`. Câu `$q1` nghĩa là
   `(user_id = 7 AND status = 'draft') OR status = 'review'`: nó trả về bài `review` của **mọi** user.
   Muốn "bài của user 7, đang draft hoặc review" thì phải nhóm bằng closure như `$q2`. Tài liệu
   Laravel khuyên luôn nhóm `orWhere`.

### 4.2 Đọc dữ liệu

```php
use Illuminate\Support\Facades\DB;

$posts = DB::table('posts')->get();                     // Collection các stdClass
$post  = DB::table('posts')->where('slug', 'hello')->first();   // stdClass hoặc null
$post  = DB::table('posts')->where('slug', 'hello')->firstOrFail();
// không có thì ném RecordNotFoundException; không bắt thì Laravel trả 404
$post  = DB::table('posts')->find(3);                   // theo cột id
$title = DB::table('posts')->where('id', 3)->value('title');    // một giá trị
$titles = DB::table('posts')->pluck('title');           // Collection các title
$titles = DB::table('posts')->pluck('title', 'id');     // [id => title]

$count = DB::table('posts')->where('published', true)->count();
$max   = DB::table('orders')->max('total');             // min, avg, sum tương tự
$has   = DB::table('posts')->where('user_id', 7)->exists();     // SELECT EXISTS(...)
```

`get()` trả về `Illuminate\Support\Collection`: một object bọc mảng, có hàng trăm method tiện dụng
(`map`, `filter`, `groupBy`, `sum`...). Nhưng nhớ: đó là xử lý trong RAM của PHP, sau khi dữ liệu đã
về. `->get()->count()` kéo mọi dòng về rồi đếm; `->count()` để MySQL đếm và chỉ trả một số.

### 4.3 Điều kiện `where`

```php
DB::table('posts')
    ->select('id', 'title', 'created_at')               // thay vì select *
    ->where('user_id', 7)                               // toán tử mặc định là =
    ->where('views', '>=', 100)                         // toán tử tường minh
    ->whereIn('status', ['draft', 'review'])
    ->whereNotIn('id', [1, 2])
    ->whereNull('deleted_at')                           // IS NULL (không viết where('x', null) khi muốn rõ ý)
    ->whereBetween('created_at', ['2026-01-01', '2026-06-30'])
    ->whereDate('created_at', '2026-10-03')             // bọc cột trong DATE(): không dùng được index thường
    ->whereLike('title', '%laravel%')                   // LIKE
    ->whereColumn('updated_at', '>', 'created_at')      // so hai cột với nhau
    ->orderBy('created_at', 'desc')                     // hoặc ->latest() / ->oldest() theo created_at
    ->limit(20)->offset(40)
    ->get();
```

Một số dạng còn lại: `orWhere...`, `whereNot`, `whereAny`/`whereAll` (nhiều cột cùng điều kiện),
`whereJsonContains` cho cột JSON, `whereExists`, `whereFullText`. Danh sách đầy đủ ở tài liệu Query
Builder.

⚠️ `whereDate('created_at', ...)` sinh `date(created_at) = ?`. Bọc cột trong hàm làm MySQL không dùng
được index B-tree thường trên cột đó ([Database chương 11](../database/11-index.md)). Với bảng lớn, viết
thành khoảng: `->where('created_at', '>=', '2026-10-03')->where('created_at', '<', '2026-10-04')`.

### 4.4 Điều kiện động với `when`

Form tìm kiếm có nhiều ô lọc, ô nào trống thì không lọc:

```php
$posts = DB::table('posts')
    ->when($request->input('status'), function (Builder $query, string $status) {
        $query->where('status', $status);
    })
    ->when($request->input('q'), fn (Builder $query, string $q) => $query->whereLike('title', "%{$q}%"))
    ->get();
```

`when($value, $callback)` chỉ chạy callback khi `$value` là truthy. ⚠️ Truthy theo nghĩa của PHP:
chuỗi `'0'`, số `0`, chuỗi rỗng đều là falsy ([Chương 04](04-kieu-du-lieu.md)), nên lọc
`category_id = 0` hay `rating = '0'` bằng `when($request->input('rating'), ...)` sẽ lặng lẽ bị bỏ qua:

```php
<?php
declare(strict_types=1);

foreach (['5', '0', '', null] as $role) {
    echo var_export($role, true), ' => ', ($role ? 'áp điều kiện' : 'BỎ QUA điều kiện'), PHP_EOL;
}
// in ra:
// '5' => áp điều kiện
// '0' => BỎ QUA điều kiện
// '' => BỎ QUA điều kiện
// NULL => BỎ QUA điều kiện
```

Khi `0` là giá trị hợp lệ, dùng điều kiện tường minh: `->when($request->filled('rating'), fn ($q) => $q->where('rating', $request->integer('rating')))`.

### 4.5 Join, group by

```php
// Số bài đã đăng của mỗi tác giả, chỉ tác giả có từ 5 bài
$rows = DB::table('users')
    ->join('posts', 'posts.user_id', '=', 'users.id')           // INNER JOIN
    ->where('posts.published', true)
    ->groupBy('users.id', 'users.name')
    ->having('post_count', '>=', 5)
    ->select('users.id', 'users.name', DB::raw('count(*) as post_count'))
    ->orderByDesc('post_count')
    ->get();

DB::table('users')->leftJoin('posts', 'posts.user_id', '=', 'users.id');   // LEFT JOIN
```

Ý nghĩa của từng loại join, `GROUP BY`, `HAVING` đã ở [Database chương 07](../database/07-join.md) và
[chương 08](../database/08-group-by-aggregate.md). Với `strict => true` (mục 1.2), `ONLY_FULL_GROUP_BY`
đang bật: cột nào trong `SELECT` mà không nằm trong `GROUP BY` và không phải hàm tổng hợp thì MySQL từ
chối (trừ khi phụ thuộc hàm vào khoá chính đã group).

### 4.6 Ghi dữ liệu

```php
DB::table('tags')->insert(['name' => 'php']);
DB::table('tags')->insert([['name' => 'go'], ['name' => 'java']]);     // nhiều dòng, một câu INSERT
$id = DB::table('tags')->insertGetId(['name' => 'sql']);              // trả id vừa tạo
DB::table('tags')->insertOrIgnore([['id' => 1, 'name' => 'php']]);    // INSERT IGNORE trên MySQL

$affected = DB::table('posts')->where('id', 3)->update(['title' => 'Mới']);   // số dòng bị ảnh hưởng
DB::table('posts')->where('id', 3)->increment('views');                // views = views + 1, nguyên tử
DB::table('accounts')->where('id', 1)->decrement('balance', 50);
DB::table('posts')->updateOrInsert(['slug' => 'hello'], ['title' => 'Hello']);

$deleted = DB::table('posts')->where('published', false)->delete();
```

⚠️ `insertOrIgnore` dùng `INSERT IGNORE` của MySQL. Tài liệu Laravel cảnh báo: nó không chỉ bỏ qua lỗi
trùng khoá mà còn có thể bỏ qua lỗi khác, và bỏ qua strict mode (giá trị sai kiểu bị ép thành giá trị
mặc định thay vì báo lỗi).

⚠️ `increment('views')` sinh `update ... set views = views + 1`, cộng ngay trong MySQL nên an toàn khi
nhiều request cùng tăng. Viết `$post->views + 1` trong PHP rồi `update` là *lost update*: hai request
cùng đọc 10, cùng ghi 11 ([Database chương 14](../database/14-isolation-mvcc.md)).

⚠️ `update()` và `delete()` không có `where` áp lên **toàn bộ bảng**. Builder không cảnh báo gì.

### 4.7 Khoá dòng: `lockForUpdate`, `sharedLock`

```php
DB::transaction(function () {
    $from = DB::table('accounts')->where('id', 1)->lockForUpdate()->first();   // SELECT ... FOR UPDATE
    $to   = DB::table('accounts')->where('id', 2)->lockForUpdate()->first();
    if ($from->balance < 100) {
        throw new RuntimeException('Không đủ số dư');
    }
    DB::table('accounts')->where('id', 1)->decrement('balance', 100);
    DB::table('accounts')->where('id', 2)->increment('balance', 100);
});
```

`lockForUpdate()` thêm `for update`, `sharedLock()` thêm `lock in share mode` (grammar MySQL 13.x vẫn
sinh cú pháp cũ này; MySQL 8 hiểu nó như `FOR SHARE`). Khoá chỉ giữ tới hết transaction, nên ngoài transaction (autocommit) chúng gần như
vô nghĩa. Như mục 1.4, gọi lock cũng ép query chạy trên connection write. Khoá dòng, thứ tự khoá để
tránh deadlock: [Database chương 15](../database/15-lock-deadlock.md); transaction trong Laravel: mục 11.

### 4.8 Xem SQL mà builder sinh ra

```php
$q = DB::table('posts')->where('user_id', 7)->where('views', '>', 100);
$q->toSql();         // "select * from `posts` where `user_id` = ? and `views` > ?"
$q->getBindings();   // [7, 100]
$q->toRawSql();      // binding đã được ghép vào, để copy sang EXPLAIN
$q->dump();          // in SQL và binding, chạy tiếp
$q->dd();            // in rồi dừng
$q->ddRawSql();      // in SQL đã ghép binding rồi dừng
```

`toRawSql()` chỉ để đọc và debug; đừng chạy chuỗi đó như câu SQL thật (đó chính là ghép chuỗi). Để theo
dõi mọi query của một request, dùng `DB::listen` (mục 9.5).

## 5. Eloquent cơ bản

### 5.1 ORM và Active Record

*ORM* (*Object-Relational Mapping*) là lớp ánh xạ giữa bảng trong database và object trong code: bạn
làm việc với `$post->title`, ORM lo câu SQL. Eloquent theo mẫu *Active Record* (Martin Fowler đặt tên):
mỗi object vừa mang dữ liệu của một dòng, vừa tự biết lưu và xoá chính nó (`$post->save()`,
`$post->delete()`). Mẫu đối lập là *Data Mapper* (Doctrine của PHP, Hibernate/JPA của Java): entity là
object thuần không biết gì về database, một lớp riêng (`EntityManager`) lo việc lưu. Active Record viết
CRUD rất nhanh; đổi lại model gắn chặt với database, khó test logic tách khỏi DB.

Để hiểu Eloquent làm gì bên dưới, đây là một model đồ chơi bằng PHP thuần mô phỏng ba ý chính: dữ liệu
nằm trong một mảng `$attributes`, đọc ghi qua magic method `__get`/`__set` ([Chương 10](10-oop-nang-cao.md)),
và model giữ thêm bản `$original` để biết cột nào đã đổi (*dirty*) mà chỉ `UPDATE` đúng các cột đó.

```php
<?php
declare(strict_types=1);

// Mô phỏng cách một model Active Record giữ dữ liệu: KHÔNG phải code Laravel.
class ToyModel
{
    /** @var array<string, mixed> giá trị hiện tại */
    protected array $attributes = [];
    /** @var array<string, mixed> giá trị lúc đọc từ DB */
    protected array $original = [];
    public bool $exists = false;

    /** Dựng model từ một dòng DB (hydrate) */
    public static function hydrateRow(array $row): static
    {
        $m = new static();
        $m->attributes = $row;
        $m->original = $row;
        $m->exists = true;
        return $m;
    }

    public function __get(string $key): mixed
    {
        return $this->attributes[$key] ?? null;
    }

    public function __set(string $key, mixed $value): void
    {
        $this->attributes[$key] = $value;
    }

    /** @return array<string, mixed> các cột đã đổi so với bản gốc */
    public function getDirty(): array
    {
        $dirty = [];
        foreach ($this->attributes as $k => $v) {
            if (!array_key_exists($k, $this->original) || $this->original[$k] !== $v) {
                $dirty[$k] = $v;
            }
        }
        return $dirty;
    }

    public function save(): string
    {
        if (!$this->exists) {
            return 'INSERT ' . json_encode($this->attributes);
        }
        $dirty = $this->getDirty();
        if ($dirty === []) {
            return 'không có gì đổi: bỏ qua UPDATE';
        }
        $this->original = $this->attributes;   // đồng bộ lại sau khi lưu
        return 'UPDATE posts SET ' . implode(', ', array_map(fn ($k) => "$k = ?", array_keys($dirty)))
            . ' WHERE id = ? ' . json_encode([...array_values($dirty), $this->attributes["id"]], JSON_UNESCAPED_UNICODE);
    }
}

$post = ToyModel::hydrateRow(['id' => 3, 'title' => 'Cũ', 'views' => 10, 'options' => ['theme' => 'light']]);
echo $post->save(), PHP_EOL;
// in ra: không có gì đổi: bỏ qua UPDATE

$post->title = 'Mới';
echo json_encode($post->getDirty(), JSON_UNESCAPED_UNICODE), PHP_EOL;
// in ra: {"title":"Mới"}
echo $post->save(), PHP_EOL;
// in ra: UPDATE posts SET title = ? WHERE id = ? ["Mới",3]
echo $post->save(), PHP_EOL;
// in ra: không có gì đổi: bỏ qua UPDATE

// Sửa một phần tử của mảng qua __get: __get trả về BẢN SAO
$post->options['theme'] = 'dark';
// in ra: Notice: Indirect modification of overloaded property ToyModel::$options has no effect in ...
echo json_encode($post->options), PHP_EOL;
// in ra: {"theme":"light"}
```

(Đã chạy trên PHP 8.4 và 8.5, cùng kết quả.)

Model thật của Laravel phức tạp hơn nhiều (cast, accessor, relationship, event), nhưng ba hành vi trên
là có thật và giải thích nhiều điều về sau:

- `save()` trên model không thay đổi gì thì không gửi `UPDATE` (đọc `Model::save()` 13.x: chỉ gọi
  `performUpdate` khi `isDirty()`).
- `UPDATE` chỉ chứa cột dirty, không ghi đè cả dòng.
- Thuộc tính của model là "ảo" (đi qua `__get`), nên `$post->options['theme'] = 'dark'` không sửa được
  mảng bên trong. Mục 6.1 quay lại chuyện này với cast `array`.

### 5.2 Tạo model và quy ước

```bash
php artisan make:model Post                 # app/Models/Post.php
php artisan make:model Post -mfs            # kèm migration, factory, seeder
php artisan model:show Post                 # xem cột, cast, relationship của model (đọc cả từ DB)
```

```php
<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Post extends Model
{
    use HasFactory;
}
```

Model rỗng như vậy đã dùng được vì Eloquent dựa vào quy ước:

| Quy ước | Mặc định | Đổi bằng (Laravel 13) |
|---|---|---|
| Tên bảng | snake_case số nhiều của tên class: `Post` thành `posts`, `AirTrafficController` thành `air_traffic_controllers` | `#[Table('my_posts')]` |
| Khoá chính | cột `id`, số nguyên tự tăng | `#[Table(key: 'post_id')]`; khoá chuỗi: `#[Table(key: 'uuid', keyType: 'string', incrementing: false)]` |
| Timestamps | có `created_at`, `updated_at`, Eloquent tự điền | `#[WithoutTimestamps]` hoặc `#[Table(timestamps: false)]`; đổi tên cột bằng hằng `CREATED_AT`, `UPDATED_AT` |
| Connection | connection `default` | `#[Connection('analytics')]` |
| Khoá ngoại khi khai relationship | snake_case tên model + `_id`: `user_id` | Truyền tham số khi khai relationship |

Laravel 13 cho cấu hình model bằng *PHP attribute* (`#[...]`, [Chương 10](10-oop-nang-cao.md)). Cách
cũ bằng property (`protected $table = 'my_posts';`, `public $timestamps = false;`,
`protected $primaryKey = 'post_id';`) vẫn chạy, và bạn sẽ gặp nó trong hầu hết code viết trước Laravel
13.

Eloquent không hỗ trợ khoá chính nhiều cột (*composite primary key*). Bảng nối kiểu `post_tag` dùng
qua relationship (mục 8.4) thì không cần model riêng; còn nếu cần model, thêm cột `id` và một unique
index trên cặp cột.

Muốn khoá chính là UUID thay vì số tự tăng: `use HasUuids;` trên model (mặc định sinh UUIDv7, có thứ tự
theo thời gian nên chèn vào index B-tree đỡ phân mảnh hơn UUIDv4) hoặc `use HasUlids;`. Đánh đổi giữa
số tự tăng và UUID làm khoá chính trong InnoDB: [Database chương 16](../database/16-ben-trong-innodb.md).

### 5.3 Đọc

Model đóng vai một query builder: mọi method của mục 4 dùng được, chỉ khác là kết quả thành model.

```php
use App\Models\Post;

$posts = Post::all();                                        // mọi dòng: cẩn thận với bảng lớn
$posts = Post::where('published', true)->latest()->limit(10)->get();   // Eloquent\Collection các Post
$post  = Post::find(3);                                      // Post hoặc null
$post  = Post::findOrFail(3);                                // không có: ModelNotFoundException, thành 404
$post  = Post::where('slug', 'hello')->first();
$post  = Post::firstWhere('slug', 'hello');
$posts = Post::find([1, 2, 3]);                              // nhiều khoá: Collection
$count = Post::where('published', true)->count();            // số, không phải model

$post->refresh();                                            // đọc lại từ DB, ghi đè thay đổi chưa lưu
$copy = $post->fresh();                                      // object mới đọc từ DB, $post giữ nguyên
```

`Post::where(...)` là gọi static nhưng `Model` không có method static `where`. Nó đi qua magic method
`__callStatic` của `Model`, tạo một instance rồi chuyển tiếp lời gọi sang `Eloquent\Builder` (cùng ý
tưởng với facade ở [Chương 26](26-laravel-container-provider-facade.md)).

### 5.4 Tạo, sửa, xoá

```php
// Tạo: gán từng thuộc tính rồi save()
$post = new Post();
$post->user_id = $user->id;
$post->title = 'Xin chào';
$post->slug = 'xin-chao';
$post->body = '...';
$post->save();               // INSERT; created_at, updated_at tự điền; $post->id có giá trị
$post->wasRecentlyCreated;   // true

// Tạo một dòng lệnh (cần khai mass assignment, mục 5.5)
$post = Post::create(['title' => 'Xin chào', 'slug' => 'xin-chao', 'body' => '...', 'user_id' => 1]);

// Sửa
$post = Post::findOrFail(3);
$post->title = 'Tiêu đề mới';
$post->save();               // UPDATE posts SET title = ?, updated_at = ? WHERE id = ?

$post->update(['title' => 'Khác']);   // fill + save
$post->increment('views');            // UPDATE ... SET views = views + 1 (cộng trong SQL)

// Xoá
$post->delete();             // DELETE ... WHERE id = ?
Post::destroy([4, 5, 6]);    // nạp từng model rồi delete() từng cái
```

Theo dõi thay đổi:

```php
$post = Post::find(1);         // title = 'A'
$post->title = 'B';
$post->isDirty('title');       // true: đã đổi, chưa lưu
$post->getOriginal('title');   // 'A'
$post->save();
$post->isDirty();              // false
$post->wasChanged('title');    // true: lần save vừa rồi có đổi title
$post->getChanges();           // ['title' => 'B', 'updated_at' => ...] (những gì lần save vừa rồi ghi)
```

Tìm hoặc tạo:

```php
// Tìm theo mảng thứ nhất; không có thì tạo với (mảng 1 + mảng 2)
$tag = Tag::firstOrCreate(['slug' => 'php'], ['name' => 'PHP']);
$tag = Tag::firstOrNew(['slug' => 'php']);          // không có thì trả model CHƯA lưu
$user = User::updateOrCreate(['email' => $email], ['name' => $name]);
```

⚠️ Đọc mã nguồn `Eloquent\Builder` 13.x: `firstOrCreate` chạy `SELECT` trước; không thấy thì gọi
`createOrFirst`, tức là `INSERT`, và nếu `INSERT` gặp lỗi trùng unique (`UniqueConstraintViolationException`)
thì `SELECT` lại trên connection write. Nhờ vậy hai request đồng thời cùng tạo một tag không làm request
thứ hai lỗi. Nhưng điều đó **chỉ đúng khi cột tìm kiếm có unique index**. Không có unique index thì hai
request cùng thấy "chưa có" và cùng `INSERT`: bạn có hai dòng trùng. Ràng buộc duy nhất phải nằm ở
database, không phải ở logic PHP.

### 5.5 Mass assignment: `#[Fillable]`, `$guarded`

*Mass assignment* (gán hàng loạt) là gán nhiều thuộc tính một lần từ một mảng: `Post::create($data)`,
`$post->fill($data)`, `$post->update($data)`. Nguy hiểm vì mảng đó thường đến từ request:

```php
// Bảng users có cột is_admin. Giả sử model tắt hết bảo vệ.
public function register(Request $request)
{
    return User::create($request->all());   // client gửi thêm is_admin=1: tự thành admin
}
```

Vì vậy mặc định Eloquent chặn hết: property `$guarded` mặc định là `['*']` (đọc từ `GuardsAttributes`
13.x), và gọi `create()` trên model chưa khai gì sẽ ném `MassAssignmentException`. Bạn phải khai rõ:

```php
use Illuminate\Database\Eloquent\Attributes\Fillable;
use Illuminate\Database\Eloquent\Attributes\Hidden;

#[Fillable(['title', 'slug', 'body'])]          // whitelist: chỉ ba cột này được gán hàng loạt
#[Hidden(['internal_note'])]                    // ẩn khi chuyển sang mảng/JSON
class Post extends Model {}

// Cú pháp property, tương đương, gặp trong code cũ:
//   protected $fillable = ['title', 'slug', 'body'];
//   protected $guarded = ['is_admin'];         // blacklist: mọi cột trừ is_admin
//   protected $guarded = [];                   // TẮT bảo vệ hoàn toàn (tương đương #[Unguarded])
```

Skeleton 13.x khai `User` bằng đúng cách này: `#[Fillable(['name', 'email', 'password'])]` và
`#[Hidden(['password', 'remember_token'])]`.

Cách Eloquent quyết định một key có được gán không (`GuardsAttributes::isFillable()` 13.x):

1. Đang ở chế độ unguarded (`Model::unguard()`, factory dùng chế độ này): được.
2. Key nằm trong fillable: được.
3. Key nằm trong guarded (hoặc guarded là `['*']`): không.
4. Còn lại: chỉ được khi danh sách fillable **rỗng** (tức bạn đang dùng kiểu blacklist), và key không
   chứa dấu chấm, không bắt đầu bằng `_`.

Key không được phép thì sao? Đọc `Model::fill()` 13.x: nếu model đang "chặn hoàn toàn" (fillable rỗng
và guarded là `['*']`) thì ném `MassAssignmentException`. Còn nếu đã có whitelist, key ngoài whitelist bị
**lặng lẽ bỏ qua**. Bỏ qua lặng lẽ là nguồn bug: thêm cột `subtitle` vào form, quên thêm vào fillable,
dữ liệu không bao giờ được lưu và không ai báo lỗi. Ở môi trường dev, bật
`Model::preventSilentlyDiscardingAttributes(! $this->app->isProduction())` trong
`AppServiceProvider::boot()` để biến việc bỏ qua thành exception.

Phòng thủ đúng cần hai lớp:

- Model khai whitelist (`#[Fillable]`). Blacklist (`$guarded = ['is_admin']`) mong manh: sau này thêm
  cột `role` mà quên cập nhật blacklist là thủng.
- Controller chỉ đưa dữ liệu đã validate: `Post::create($request->validated())`, không bao giờ
  `$request->all()` ([Chương 25](25-laravel-request-validation-response.md)).

Gán từng thuộc tính (`$post->is_featured = true`) không bị mass assignment chặn: đó là cách đúng cho
các cột nhạy cảm do code quyết định, không do người dùng gửi lên.

## 6. Cast, accessor, mutator

Database chỉ có vài kiểu đơn giản: số, chuỗi, ngày giờ, JSON dạng chuỗi. Trong PHP bạn muốn làm việc với
`bool`, mảng, enum, object ngày giờ. *Cast* là khai báo "cột này, khi đọc ra thì đổi sang kiểu X, khi
ghi vào thì đổi ngược lại". *Accessor* và *mutator* là phiên bản tự viết của việc đó.

### 6.1 Cast

Từ Laravel 11, khai cast trong method `casts()` (property `protected $casts = [...]` vẫn chạy):

```php
<?php

namespace App\Models;

use App\Enums\PostStatus;
use Illuminate\Database\Eloquent\Casts\AsArrayObject;
use Illuminate\Database\Eloquent\Model;

class Post extends Model
{
    protected function casts(): array
    {
        return [
            'published'    => 'boolean',              // 0/1 trong DB, false/true trong PHP
            'published_at' => 'datetime',             // chuỗi trong DB, Carbon trong PHP
            'options'      => 'array',                // cột JSON <-> mảng PHP
            'settings'     => AsArrayObject::class,   // như array nhưng sửa từng key được
            'price'        => 'decimal:2',            // trả về STRING "1234.50"
            'status'       => PostStatus::class,      // backed enum (Chương 10)
            'secret_note'  => 'encrypted',            // mã hoá bằng APP_KEY khi lưu
        ];
    }
}

$post->published;                     // true (bool), không phải 1
$post->published_at->diffForHumans(); // "3 days ago": Carbon có sẵn method
$post->status === PostStatus::Draft;  // so sánh enum
$post->options = ['theme' => 'dark']; // lưu thành chuỗi JSON
```

`User` của skeleton dùng `'password' => 'hashed'`: gán mật khẩu thô thì Eloquent tự hash trước khi lưu.

Cạm bẫy theo từng loại cast:

- ⚠️ `array`: như model đồ chơi ở mục 5.1, `$post->options['theme'] = 'dark'` không có tác dụng và PHP
  báo *Indirect modification of overloaded property*. Thuộc tính đi qua `__get`, trả về bản sao của
  mảng. Phải lấy ra, sửa, gán lại (`$o = $post->options; $o['theme'] = 'dark'; $post->options = $o;`),
  hoặc dùng cast `AsArrayObject`/`AsCollection` (trả object, sửa trực tiếp được).
- ⚠️ `decimal:2` trả **chuỗi** (đọc `HasAttributes::asDecimal()` 13.x: dùng `BigDecimal` rồi ép
  `string`). Đó là cố ý: `float` không biểu diễn chính xác `0.1`. Tính tiền bằng bcmath hoặc lưu số
  nguyên theo đơn vị nhỏ nhất ([Chương 16, mục 5.2](16-php-va-database.md)). Đừng cast tiền sang
  `float`.
- ⚠️ `encrypted`: chuỗi mã hoá dài hơn dữ liệu gốc và không đoán trước độ dài, cột nên là `TEXT`; không
  `WHERE` hay index được; đổi `APP_KEY` mà không cấu hình key cũ là mất khả năng đọc.
- Giá trị `null` không được cast. Theo tài liệu Laravel, không đặt cast trùng tên một relationship và
  không cast khoá chính.
- Cast enum: gán giá trị không có trong enum thì PHP ném `ValueError` ngay lúc gán, lỗi sớm thay vì lưu
  rác.

### 6.2 Accessor và mutator

*Accessor* biến đổi giá trị khi **đọc**, *mutator* biến đổi khi **ghi**. Viết bằng một method
`protected` trả về `Attribute`; tên method là camelCase của tên thuộc tính:

```php
use Illuminate\Database\Eloquent\Casts\Attribute;

class User extends Model
{
    // Thuộc tính email: chuẩn hoá trước khi lưu
    protected function email(): Attribute
    {
        return Attribute::make(
            set: fn (string $value): string => mb_strtolower(trim($value)),
        );
    }

    // Thuộc tính "ảo" full_name, tính từ hai cột (không có cột full_name trong DB)
    protected function fullName(): Attribute
    {
        return Attribute::make(
            get: fn (mixed $value, array $attributes): string =>
                $attributes['first_name'] . ' ' . $attributes['last_name'],
        );
    }
}

$user->email = '  An@Example.COM ';   // lưu: "an@example.com"
echo $user->full_name;                // method fullName() ứng với thuộc tính full_name
```

Cú pháp cũ (vẫn chạy, gặp nhiều trong code cũ): `getFullNameAttribute()` và
`setEmailAttribute($value)`.

Thuộc tính ảo không tự xuất hiện khi chuyển model sang mảng/JSON (`toArray()`, trả model từ controller).
Muốn có thì khai `#[Appends(['full_name'])]` (hoặc property `$appends`). Ngược lại `#[Hidden([...])]`
giấu cột khỏi JSON.

⚠️ Accessor đọc relationship cộng với `$appends` là N+1 khó thấy nhất:

```php
#[Appends(['city_name'])]
class User extends Model
{
    protected function cityName(): Attribute
    {
        return Attribute::make(get: fn (): string => $this->city->name);   // lazy load city
    }
}

return User::paginate(100);
// Serialize 100 user: 100 câu SELECT * FROM cities, dù controller không có vòng lặp nào
```

Sửa: eager load (`User::with('city')->paginate(100)`, mục 9), hoặc bỏ khỏi `$appends` và chỉ thêm ở
endpoint cần (`$users->append('city_name')`).

## 7. Scope, soft delete, event và observer

### 7.1 Local scope

*Local scope* đóng gói một điều kiện hay dùng thành method gọi được trên query:

```php
use Illuminate\Database\Eloquent\Attributes\Scope;
use Illuminate\Database\Eloquent\Builder;

class Post extends Model
{
    #[Scope]
    protected function published(Builder $query): void
    {
        $query->where('published', true)->whereNotNull('published_at');
    }

    #[Scope]
    protected function byAuthor(Builder $query, int $userId): void   // scope có tham số
    {
        $query->where('user_id', $userId);
    }
}

$posts = Post::published()->byAuthor(7)->latest()->get();
```

Cú pháp cũ: `public function scopePublished(Builder $query)`, gọi là `Post::published()` (bỏ chữ
`scope`).

⚠️ Ghép scope bằng `or`: `Post::published()->orWhere(...)` gặp đúng vấn đề `AND`/`OR` ở mục 4.1. Nhóm
lại bằng closure: `Post::where(fn ($q) => $q->published())->orWhere(fn ($q) => $q->byAuthor(7))`.

### 7.2 Global scope

*Global scope* tự thêm điều kiện vào **mọi** query Eloquent của model. Ví dụ thực tế là ứng dụng nhiều
khách hàng (*multi-tenant*) dùng chung bảng:

```php
<?php

namespace App\Models\Scopes;

use Illuminate\Database\Eloquent\Builder;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Scope;

class TenantScope implements Scope
{
    public function apply(Builder $builder, Model $model): void
    {
        $builder->where($model->qualifyColumn('tenant_id'), app('tenant')->id);
    }
}

// Gắn: #[ScopedBy([TenantScope::class])] trên class model
// Bỏ cho một query: Invoice::withoutGlobalScope(TenantScope::class)->get();
// Bỏ tất cả:        Invoice::withoutGlobalScopes()->get();
```

⚠️ Global scope làm query "thiếu dữ liệu" mà người đọc code không thấy nguyên nhân: viết
`Invoice::sum('total')` cho báo cáo toàn hệ thống mà ra số của một tenant. Và scope **chỉ áp cho
Eloquent** của model đó: `DB::table('invoices')`, raw SQL, hay join sang bảng `invoices` từ model khác
đều không có điều kiện. Với dữ liệu phân tách khách hàng, lọt scope là lộ dữ liệu; cần thêm test tự
động.

### 7.3 Soft delete

*Soft delete* (xoá mềm): thay vì `DELETE`, ghi thời điểm xoá vào cột `deleted_at`, dòng vẫn còn trong
bảng. Dùng khi cần khôi phục hoặc giữ lịch sử.

```php
// Migration: $table->softDeletes();   // deleted_at TIMESTAMP NULL

use Illuminate\Database\Eloquent\SoftDeletes;

class Post extends Model
{
    use SoftDeletes;
}

$post->delete();                     // UPDATE posts SET deleted_at = ?, updated_at = ? WHERE id = ?
Post::all();                         // tự thêm WHERE deleted_at IS NULL
Post::withTrashed()->find($id);      // gồm cả bản đã xoá mềm
Post::onlyTrashed()->get();          // chỉ bản đã xoá
$post->trashed();                    // bool
$post->restore();                    // deleted_at = NULL
$post->forceDelete();                // DELETE thật
```

Trait `SoftDeletes` hoạt động bằng một global scope (`SoftDeletingScope`) tự thêm
`WHERE deleted_at IS NULL`. Vì thế nó có đúng các giới hạn của global scope:

- ⚠️ `DB::table('posts')`, raw SQL, join từ bảng khác, công cụ BI đọc thẳng DB đều thấy dòng đã xoá.
- ⚠️ Unique index: `users.email` unique thì người dùng đã xoá mềm chặn người khác đăng ký lại email đó.
  Thêm `deleted_at` vào unique index cũng không giải quyết vì MySQL coi các `NULL` là khác nhau. Cách
  xử lý (generated column, partial index ở PostgreSQL): [Database chương 20](../database/20-thay-doi-schema-migration.md)
  và [chương 04](../database/04-ddl-constraint.md).
- ⚠️ Không có cascade: xoá mềm post thì comment vẫn hiện; phải tự xoá mềm con (trong event `deleting`).
- `Post::where(...)->delete()` (mass delete) trên model có `SoftDeletes` vẫn là xoá mềm (thành
  `UPDATE`), nhưng không bắn event (mục 7.4).
- Xoá mềm không phải xoá dữ liệu. Yêu cầu pháp lý "xoá dữ liệu cá nhân" cần xoá thật; trait `Prunable`
  kèm lệnh `model:prune` chạy theo lịch giúp xoá hẳn bản ghi cũ.

### 7.4 Model event

Eloquent bắn *event* tại các mốc trong vòng đời model: `retrieved`, `creating`/`created`,
`updating`/`updated`, `saving`/`saved`, `deleting`/`deleted`, `restoring`/`restored`, `trashed`,
`forceDeleting`/`forceDeleted`, `replicating`. Đuôi `-ing` chạy **trước** khi ghi DB (trả `false` để
huỷ thao tác); đuôi `-ed` chạy sau.

Thứ tự khi `save()` model đã tồn tại (đọc `Model::save()` 13.x):

```
save()
 ├─ saving          luôn bắn
 ├─ isDirty()? không -> bỏ qua UPDATE, updating/updated KHÔNG bắn
 │   có ↓
 ├─ updating
 ├─ UPDATE ... SET <chỉ cột dirty> WHERE id = ?
 ├─ updated
 └─ saved
```

Model mới: `saving` → `creating` → `INSERT` → `created` → `saved`.

Đăng ký nhanh bằng closure trong method `booted()` của model:

```php
class Post extends Model
{
    protected static function booted(): void
    {
        static::creating(function (Post $post): void {
            $post->slug ??= Str::slug($post->title);
        });
    }
}
```

Nhiều event cho một model thì gom vào một *observer*:

```bash
php artisan make:observer PostObserver --model=Post
```

```php
<?php

namespace App\Observers;

use App\Models\Post;
use Illuminate\Support\Facades\Cache;

class PostObserver
{
    public function saved(Post $post): void
    {
        Cache::forget("post:{$post->id}");
    }

    public function updated(Post $post): void
    {
        if ($post->wasChanged('status')) {
            // trạng thái vừa đổi: getOriginal('status') là giá trị cũ
        }
    }

    public function deleted(Post $post): void
    {
        Cache::forget("post:{$post->id}");
    }
}

// Gắn observer: #[ObservedBy([PostObserver::class])] trên class Post
```

⚠️ Điểm quan trọng nhất của chương về event: thao tác **hàng loạt** qua query không dựng model nên
không bắn event, không chạy observer, không áp cast hay mutator. Tài liệu Laravel giải thích: các model
"không bao giờ thực sự được lấy ra".

```php
$post = Post::findOrFail($id);
$post->update(['status' => 'published']);        // SELECT rồi UPDATE: saving, updating, updated, saved

Post::where('id', $id)->update(['status' => 'published']);   // một câu UPDATE: KHÔNG event nào
Post::where('user_id', 7)->delete();                          // một câu DELETE: không deleting/deleted
Post::insert([...]);                                          // không event, không timestamps
Post::destroy([1, 2, 3]);                                     // CÓ event: nạp từng model rồi delete()
```

Khoá ngoại `ON DELETE CASCADE` (mục 2.8) cũng xoá ở tầng MySQL, Eloquent không biết, không có event.

Mass update nhanh (một câu cho 10.000 dòng) nhưng mất event; nạp từng model có event nhưng chậm. Nếu
logic trong observer là bắt buộc (ghi audit, xoá cache), code hàng loạt phải tự làm phần đó.

Tắt event có chủ đích: `$post->saveQuietly()`, `deleteQuietly()`, hoặc
`Post::withoutEvents(fn () => ...)`; seeder dùng trait `WithoutModelEvents` (mục 3.1).

⚠️ Observer và transaction: handler chạy ngay khi event bắn, tức là **trước** khi transaction bao ngoài
commit. Observer gửi email trong `created` rồi transaction rollback là email cho một bản ghi không tồn
tại. Cho observer `implements ShouldHandleEventsAfterCommit` để nó chờ commit (không có transaction thì
chạy ngay). Chuyện tương tự với queue job ở mục 11.3.

⚠️ Observer giấu logic: người đọc controller không thấy email được gửi. Seeder, import, factory trong
test đều kích hoạt observer. Quy tắc thực dụng: dùng observer cho việc kỹ thuật gắn với dữ liệu (xoá
cache, cập nhật search index, audit); luồng nghiệp vụ quan trọng viết tường minh trong service hoặc
action. Event và listener ở mức ứng dụng: [Chương 29](29-laravel-queue-event-schedule-cache.md).

## 8. Relationship

### 8.1 Relationship là gì

Bảng liên kết với nhau qua khoá ngoại ([Database chương 02](../database/02-mo-hinh-quan-he-thiet-ke.md)).
Trong Eloquent, bạn khai báo liên kết đó một lần, dưới dạng method trả về một object *relation*, rồi
dùng như thuộc tính:

```php
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class User extends Model
{
    public function posts(): HasMany
    {
        return $this->hasMany(Post::class);       // posts.user_id = users.id
    }
}

class Post extends Model
{
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);     // posts.user_id -> users.id
    }
}
```

Hai cách dùng, khác nhau quan trọng:

```php
$user->posts;          // THUỘC TÍNH: chạy query (nếu chưa chạy), trả Collection, lưu lại cho lần sau
$user->posts;          // lần hai: không query nữa, dùng kết quả đã lưu

$user->posts()                    // METHOD: trả object HasMany (một query builder), CHƯA chạy gì
    ->where('published', true)
    ->latest()
    ->get();                      // giờ mới chạy, đại ý: SELECT * FROM posts WHERE user_id = ? AND published = ? ORDER BY created_at DESC
$user->posts()->count();          // SELECT COUNT(*) ..., không nạp model nào
```

Việc chạy query lúc bạn truy cập thuộc tính lần đầu gọi là *lazy loading*. Nó tiện nhưng là nguồn của
bài toán N+1 (mục 9).

### 8.2 Một-một và một-nhiều

```php
// Một-một: mỗi user có một profile (bảng profiles có user_id)
class User extends Model
{
    public function profile(): HasOne
    {
        return $this->hasOne(Profile::class);
    }
}
class Profile extends Model
{
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}

// Một-nhiều: một post có nhiều comment (bảng comments có post_id)
class Post extends Model
{
    public function comments(): HasMany
    {
        return $this->hasMany(Comment::class);
    }
}
class Comment extends Model
{
    public function post(): BelongsTo
    {
        return $this->belongsTo(Post::class);
    }
}
```

Cách nhớ: bảng nào **chứa** cột khoá ngoại thì model đó dùng `belongsTo`. Bên kia dùng `hasOne` hoặc
`hasMany`.

Khoá được đoán theo quy ước:

- `hasMany(Comment::class)` trên `Post`: khoá ngoại là `post_id` (snake_case tên model cha + `_id`),
  khoá cục bộ là `id`.
- `belongsTo(Post::class)` trên `Comment`: khoá ngoại lấy từ **tên method** + `_id`. Method tên
  `post()` thì cột `post_id`; method tên `author()` thì Eloquent tìm cột `author_id`.
- Tên khác quy ước: truyền tường minh, `belongsTo(User::class, 'author_id')`,
  `hasMany(Comment::class, 'article_id', 'id')`.

Khi quan hệ có thể rỗng, `$post->user` trả `null`, và `$post->user->name` lỗi. Có thể trả "model rỗng"
thay vì `null` (mẫu *Null Object*): `->withDefault(['name' => 'Ẩn danh'])` trên `belongsTo`/`hasOne`.

Tạo bản ghi qua relationship (Eloquent tự điền khoá ngoại):

```php
$post->comments()->create(['body' => 'Hay quá']);          // comments.post_id = $post->id
$post->comments()->createMany([['body' => 'A'], ['body' => 'B']]);
$comment->post()->associate($otherPost);                    // đặt comments.post_id
$comment->save();
```

Các biến thể một-một đáng biết: `latestOfMany()`, `oldestOfMany()`, `ofMany('price', 'max')` lấy
một bản ghi "mới nhất / lớn nhất" trong quan hệ một-nhiều (ví dụ `latestOrder()`).

### 8.3 Has-many-through: đi xuyên một bảng

Bảng `countries` → `users` (có `country_id`) → `posts` (có `user_id`). Bảng `posts` không có
`country_id`, nhưng muốn lấy mọi bài viết của một nước:

```php
use Illuminate\Database\Eloquent\Relations\HasManyThrough;

class Country extends Model
{
    public function posts(): HasManyThrough
    {
        return $this->hasManyThrough(Post::class, User::class);
        // khoá mặc định: users.country_id, posts.user_id
        // nếu User đã có posts() và Country đã có users(), viết gọn:
        // return $this->through('users')->has('posts');
    }
}

// $country->posts sinh một query JOIN qua bảng trung gian, đại ý (output minh hoạ):
// select posts.*, users.country_id as laravel_through_key from posts
//   inner join users on users.id = posts.user_id
//   where users.country_id = ?
```

`hasOneThrough` tương tự nhưng trả một model.

### 8.4 Nhiều-nhiều và bảng pivot

Một post có nhiều tag, một tag gắn với nhiều post. Cần bảng thứ ba, *pivot table*, chứa hai khoá ngoại.
Quy ước tên: tên hai model số ít, xếp theo **thứ tự bảng chữ cái**, nối bằng `_`: `Post` và `Tag` thành
`post_tag`; `Role` và `User` thành `role_user` (không phải `user_role`).

```php
// Migration
Schema::create('post_tag', function (Blueprint $table) {
    $table->foreignId('post_id')->constrained()->cascadeOnDelete();
    $table->foreignId('tag_id')->constrained()->cascadeOnDelete();
    $table->timestamps();
    $table->primary(['post_id', 'tag_id']);      // chặn gắn trùng
});

// Model
use Illuminate\Database\Eloquent\Relations\BelongsToMany;

class Post extends Model
{
    public function tags(): BelongsToMany
    {
        return $this->belongsToMany(Tag::class)
            ->withTimestamps()                   // điền created_at/updated_at của pivot
            ->withPivot('added_by');             // cột thêm trên pivot phải khai mới đọc được
    }
}
class Tag extends Model
{
    public function posts(): BelongsToMany
    {
        return $this->belongsToMany(Post::class);
    }
}

foreach ($post->tags as $tag) {
    echo $tag->name, ' ', $tag->pivot->created_at;   // dữ liệu bảng nối nằm ở ->pivot
}
```

Ghi lên bảng pivot:

| Method | Làm gì | Ghi chú |
|---|---|---|
| `attach($id, [...])` | INSERT một dòng pivot | Gọi hai lần là hai dòng trùng nếu không có unique/primary trên cặp cột |
| `detach($id)` / `detach()` | DELETE dòng pivot (không truyền id là xoá hết) | Hai model ở hai đầu vẫn còn |
| `sync([1, 2, 3])` | Đưa pivot về đúng tập này: thêm cái thiếu, **xoá cái không có trong mảng** | Truyền nhầm mảng rỗng là xoá sạch |
| `syncWithoutDetaching([...])` | Chỉ thêm, không xoá | |
| `toggle([...])` | Có thì bỏ, chưa có thì thêm | |

⚠️ Mặc định các thao tác pivot đi qua query builder, không có model event. Cần event cho pivot thì khai
model pivot riêng bằng `->using(PostTag::class)` (class kế thừa `Pivot`).

### 8.5 Polymorphic: một bảng con, nhiều loại cha

Comment có thể thuộc về post hoặc video. Thay vì hai bảng comment, dùng một bảng với cặp cột "loại cha"
và "id cha":

```php
// Migration: $table->morphs('commentable');
//   tạo commentable_type VARCHAR, commentable_id BIGINT UNSIGNED, và index (type, id)

use Illuminate\Database\Eloquent\Relations\MorphMany;
use Illuminate\Database\Eloquent\Relations\MorphTo;

class Comment extends Model
{
    public function commentable(): MorphTo
    {
        return $this->morphTo();      // đọc commentable_type để biết phải query bảng nào
    }
}
class Post extends Model
{
    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }
}
class Video extends Model
{
    public function comments(): MorphMany
    {
        return $this->morphMany(Comment::class, 'commentable');
    }
}

$post->comments()->create(['body' => '...']);   // commentable_type, commentable_id tự điền
$comment->commentable;                          // Post hoặc Video
```

Có thêm `morphOne` (một-một), `morphToMany`/`morphedByMany` (nhiều-nhiều, ví dụ tag dùng chung cho post
và video qua bảng `taggables`).

Mặc định cột `commentable_type` lưu tên class đầy đủ, ví dụ `App\Models\Post`. Nên khai *morph map*
trong `AppServiceProvider::boot()`:

```php
use Illuminate\Database\Eloquent\Relations\Relation;

Relation::enforceMorphMap([
    'post'  => Post::class,
    'video' => Video::class,
]);
// commentable_type lưu 'post' thay vì 'App\Models\Post'
```

- ⚠️ Không có morph map: đổi namespace hay đổi tên class là dữ liệu cũ trỏ vào class không tồn tại.
  `enforceMorphMap` (khác `morphMap`) còn ném exception khi gặp model chưa khai alias. Thêm morph map
  vào app đang chạy thì phải cập nhật các giá trị type cũ trong DB.
- ⚠️ `commentable_id` trỏ tới nhiều bảng tuỳ giá trị cột khác, nên **không đặt được khoá ngoại**: không
  có cascade, comment mồ côi khi xoá post, sai type không ai chặn. Đó là lý do một số đội tránh
  polymorphic và dùng bảng riêng hoặc nhiều cột khoá ngoại nullable.

### 8.6 Lọc theo quan hệ: `has`, `whereHas`, `withCount`

```php
Post::has('comments')->get();                                 // post có ít nhất 1 comment
Post::has('comments', '>=', 5)->get();
Post::doesntHave('comments')->get();
Post::whereHas('comments', fn ($q) => $q->where('flagged', true))->get();   // WHERE EXISTS (subquery)
Post::whereRelation('comments', 'flagged', true)->get();      // viết tắt của dòng trên

Post::withCount('comments')->get();      // thêm $post->comments_count bằng subquery COUNT, không nạp comment
Post::withSum('orderItems', 'price')->get();   // $post->order_items_sum_price
Post::withExists('likes')->get();        // $post->likes_exists (bool)
```

⚠️ `whereHas` chỉ **lọc** post, không nạp comment. Viết `whereHas(...)` rồi lặp `$post->comments` là lazy
load (N+1) và nhận **mọi** comment, không chỉ comment bị flag. Muốn vừa lọc vừa nạp đúng phần đó:
`Post::withWhereHas('comments', fn ($q) => $q->where('flagged', true))->get()`.

`whereHas` sinh `WHERE EXISTS (SELECT * FROM comments WHERE comments.post_id = posts.id AND ...)`. Cần
index trên `comments.post_id` (khoá ngoại tạo bằng `constrained()` trên MySQL đã có index, vì InnoDB đòi
index cho cột khoá ngoại).

## 9. Eager loading và bài toán N+1

### 9.1 N+1 là gì

```php
$posts = Post::all();                 // 1 query: SELECT * FROM posts
foreach ($posts as $post) {
    echo $post->user->name;           // mỗi vòng 1 query: SELECT * FROM users WHERE id = ? LIMIT 1
}
```

50 bài viết là 1 + 50 = 51 query: đó là *N+1*. Mỗi query chỉ vài mili giây nên **không bao giờ lên
slow query log**, nhưng mỗi query là một lượt đi về mạng tới MySQL; 500 bài là 501 lượt, cộng lại vài
trăm mili giây tới vài giây. Muốn thấy N+1 phải đếm **số query mỗi request**, không phải nhìn từng
query.

*Eager loading* nạp quan hệ cho cả tập trong một query:

```php
$posts = Post::with('user')->get();
// Query 1: select * from posts
// Query 2: select * from users where users.id in (1, 2, 3, 4, 5)
// Eloquent ghép user vào từng post trong PHP
foreach ($posts as $post) {
    echo $post->user->name;           // không query thêm
}
```

Mô phỏng hai cách bằng PDO và SQLite trong RAM để tự đếm (PHP thuần, chạy được không cần Laravel hay
MySQL):

```php
<?php
declare(strict_types=1);

// Mô phỏng N+1 và eager loading bằng PDO + SQLite trong RAM (không cần MySQL).
$pdo = new PDO('sqlite::memory:', options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)');
$pdo->exec('CREATE TABLE posts (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, title TEXT NOT NULL)');
for ($u = 1; $u <= 5; $u++) {
    $pdo->exec("INSERT INTO users (id, name) VALUES ($u, 'User $u')");
}
for ($p = 1; $p <= 50; $p++) {
    $uid = ($p % 5) + 1;
    $pdo->exec("INSERT INTO posts (id, user_id, title) VALUES ($p, $uid, 'Post $p')");
}

$queries = 0;
$run = function (string $sql, array $params = []) use ($pdo, &$queries): array {
    $queries++;
    $stmt = $pdo->prepare($sql);
    $stmt->execute($params);
    return $stmt->fetchAll(PDO::FETCH_ASSOC);
};

// Cách 1: lazy loading trong vòng lặp (giống $post->user trong foreach)
$queries = 0;
$posts = $run('SELECT * FROM posts');
foreach ($posts as $post) {
    $user = $run('SELECT * FROM users WHERE id = ? LIMIT 1', [$post['user_id']])[0];
}
echo "Lazy: $queries query", PHP_EOL;

// Cách 2: eager loading (giống Post::with('user')->get())
$queries = 0;
$posts = $run('SELECT * FROM posts');
$ids = array_values(array_unique(array_column($posts, 'user_id')));
$placeholders = implode(', ', array_fill(0, count($ids), '?'));
$users = array_column($run("SELECT * FROM users WHERE id IN ($placeholders)", $ids), null, 'id');
foreach ($posts as $post) {
    $user = $users[$post['user_id']];   // ghép trong PHP, không query thêm
}
echo "Eager: $queries query, IN có ", count($ids), " id", PHP_EOL;
// in ra:
// Lazy: 51 query
// Eager: 2 query, IN có 5 id
```

Để ý: eager loading không dùng `JOIN`. Nó chạy một query riêng cho mỗi quan hệ với `WHERE ... IN (...)`
rồi ghép bằng PHP. Số query cố định theo **số quan hệ**, không theo số dòng.

### 9.2 Các dạng eager loading

```php
Post::with('user')->get();
Post::with(['user', 'tags'])->get();                    // nhiều quan hệ: mỗi quan hệ một query
Post::with('comments.user')->get();                     // lồng: comment và tác giả của comment
Post::with('user:id,name')->get();                      // chỉ lấy vài cột (phải có khoá id để ghép)
Post::with(['comments' => fn ($q) => $q->where('approved', true)->latest()])->get();   // có điều kiện

$posts = Post::all();
$posts->load('user');                                   // "lazy eager": đã có collection rồi mới nạp
$posts->loadMissing('user');                            // chỉ nạp nếu chưa nạp
$posts->loadCount('comments');
```

⚠️ Eager loading có giá riêng: `with('comments')` trên 1.000 bài, mỗi bài 500 comment, là kéo 500.000
model vào RAM, dù trang chỉ hiện số comment. Cần đếm thì `withCount`, cần tổng thì `withSum` (mục 8.6).

⚠️ `with(['comments' => fn ($q) => $q->latest()->limit(5)])`: muốn "5 comment mới nhất của mỗi post".
Trong Laravel 13, `limit` đặt trên relation được chuyển thành *group limit* (đọc `HasOneOrMany` và
`Query\Grammars\Grammar::compileGroupLimit()` 13.x: dùng window function `row_number()` theo từng khoá
cha), nên đúng là 5 comment cho mỗi post. Cơ chế này có từ Laravel 11; trước đó (tài liệu Laravel 10.x
ghi rõ không được dùng `limit`/`take` khi ràng buộc eager load), limit áp cho **cả** query `IN (...)`,
tức 5 comment tổng cộng. Gặp code cũ cần kiểm tra phiên bản.

### 9.3 N+1 hay trốn ở đâu

1. View Blade hoặc API Resource đọc quan hệ: `{{ $post->user->name }}` trong vòng `@foreach`, hay
   `'author' => $this->user->name` trong `JsonResource`. Controller không có vòng lặp nhưng view có.
2. Accessor và `$appends` đọc quan hệ (mục 6.2): mỗi lần serialize model là một query.
3. Policy trong vòng lặp: `@can('update', $post)` với policy đọc `$post->team->owner_id`
   ([Chương 28](28-laravel-auth.md)).
4. Queue job nhận model: job chỉ lưu id, lúc chạy đọc lại từ DB, quan hệ đã nạp trước đó không đi theo
   ([Chương 29](29-laravel-queue-event-schedule-cache.md)).

### 9.4 Bắt N+1 bằng `preventLazyLoading` và strict mode

Đừng chờ production chậm mới biết. Trong `AppServiceProvider::boot()`:

```php
use Illuminate\Database\Eloquent\Model;

public function boot(): void
{
    // Bật kiểm tra ở mọi môi trường: mặc định lazy load là ném LazyLoadingViolationException
    Model::preventLazyLoading();

    // Production: không ném, chỉ ghi log để thấy chỗ còn sót
    if ($this->app->isProduction()) {
        Model::handleLazyLoadingViolationUsing(function (Model $model, string $relation): void {
            logger()->warning('lazy load', ['model' => $model::class, 'relation' => $relation]);
        });
    }
}
```

Đọc `HasAttributes::handleLazyLoadingViolation()` 13.x: handler chỉ được gọi khi `preventLazyLoading` đang
bật, và khi đã đăng ký handler thì Laravel gọi handler **thay cho** việc ném exception. Vì thế không viết
`preventLazyLoading(! $this->app->isProduction())` kèm một handler đăng ký vô điều kiện: production không
bao giờ ghi log (kiểm tra đang tắt), còn máy dev chỉ ghi log mà không ném. Chỉ muốn ném ở dev, không cần
gì ở production thì dùng dòng có trong tài liệu Laravel: `Model::preventLazyLoading(! $this->app->isProduction());`.

`Model::shouldBeStrict(bool)` bật cùng lúc ba kiểm tra (đọc `Model::shouldBeStrict()` 13.x):

| Method | Chặn gì | Không bật thì |
|---|---|---|
| `preventLazyLoading()` | Truy cập quan hệ chưa nạp: ném `LazyLoadingViolationException` | Âm thầm thêm query |
| `preventSilentlyDiscardingAttributes()` | Mass assignment key ngoài fillable: ném `MassAssignmentException` | Key bị bỏ qua lặng lẽ (mục 5.5) |
| `preventAccessingMissingAttributes()` | Đọc thuộc tính không có trong kết quả (ví dụ quên `select` cột): ném `MissingAttributeException` | Trả `null`, không phân biệt được "cột NULL" với "không select" |

Chi tiết đọc từ mã nguồn: `preventLazyLoading` chỉ áp cho model được dựng từ kết quả có **nhiều hơn một
dòng** (`Eloquent\Builder::hydrate()` 13.x chỉ gán cờ khi `count($items) > 1`). `User::find(1)->posts`
không bị chặn, vì một model đơn lẻ không gây N+1.

⚠️ Bật strict mode trên dự án cũ, lỗi gặp nhiều nhất thường không phải N+1 mà là
`MassAssignmentException`: rất nhiều `update($request->all())` đang lặng lẽ vứt field. Đó là bug có sẵn,
strict mode chỉ làm nó lộ ra.

*Automatic eager loading* (có từ Laravel 12.x, có trong 13): `Model::automaticallyEagerLoadRelationships()`
trong `boot()`. Khi bạn truy cập một quan hệ chưa nạp trên model thuộc một collection, Laravel nạp quan
hệ đó cho **cả collection** một lần. Nó giảm số query nhưng không giảm lượng dữ liệu kéo về; với endpoint
quan trọng vẫn nên `with` có chủ đích.

Đối chiếu: Hibernate/JPA của Java có đúng vấn đề này với quan hệ `LAZY`, sửa bằng `JOIN FETCH` hoặc
`@EntityGraph`. Go thường viết SQL tay (`database/sql`, sqlc) nên N+1 ít ẩn hơn, nhưng vẫn gặp khi gọi
query trong vòng lặp.

### 9.5 Quan sát query

```php
use Illuminate\Database\Events\QueryExecuted;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

// AppServiceProvider::boot()
DB::listen(function (QueryExecuted $query): void {
    if ($query->time > 100) {                                  // mili giây
        Log::warning('slow query', ['sql' => $query->toRawSql(), 'ms' => $query->time]);
    }
});

// Tổng thời gian query của một request vượt 500 ms: bắt được N+1 dù từng query đều nhanh
DB::whenQueryingForLongerThan(500, function ($connection, QueryExecuted $event): void {
    Log::warning('request tốn nhiều thời gian query');
});
```

Ở máy dev, Laravel Debugbar hoặc Telescope hiện số query mỗi request và đánh dấu query lặp lại; dấu hiệu
N+1 là cùng một câu SQL lặp hàng chục lần chỉ khác tham số. Đừng ghi binding ra log chung nếu chứa dữ
liệu nhạy cảm. Trong test có thể khoá số query của một endpoint để N+1 mới làm đỏ CI
([Chương 30](30-laravel-testing-octane-deploy.md)).

## 10. Xử lý tập dữ liệu lớn: chunk, lazy, cursor

### 10.1 Vì sao không `get()` tất cả

`Invoice::where('status', 'pending')->get()` trên 2 triệu dòng tạo 2 triệu object model trong RAM và
chắc chắn vượt `memory_limit` ([Chương 20](20-hieu-nang.md)). Lệnh Artisan hay queue job xử lý dữ liệu
lớn phải chia nhỏ:

| Cách | SQL sinh ra | RAM giữ cùng lúc | Khi nào dùng |
|---|---|---|---|
| `get()` | 1 query, lấy hết | Toàn bộ | Tập nhỏ, có giới hạn rõ |
| `chunk(1000, fn)` | `ORDER BY id LIMIT 1000 OFFSET 0`, rồi `OFFSET 1000`... | 1 chunk | Chỉ đọc, không sửa cột trong điều kiện lọc |
| `chunkById(1000, fn)` | `WHERE ... AND id > :last ORDER BY id LIMIT 1000` | 1 chunk | Mặc định nên dùng, nhất là khi callback sửa dữ liệu |
| `lazy()` / `lazyById()` | Như `chunk` / `chunkById` (mặc định 1000 dòng mỗi lần) | 1 chunk | Muốn viết dạng chuỗi `->filter()->each()` trên `LazyCollection` |
| `cursor()` | 1 query duy nhất | 1 model, nhưng PDO vẫn giữ toàn bộ raw row | Chỉ đọc, không cần eager load |

```php
Invoice::where('status', 'pending')->chunkById(1000, function (Collection $invoices): void {
    foreach ($invoices as $invoice) {
        // xử lý từng hoá đơn
    }
});

foreach (Invoice::where('status', 'pending')->lazyById(1000) as $invoice) {
    // trông như vòng lặp thường, bên dưới vẫn chia từng 1000 dòng
}

foreach (Invoice::where('year', 2025)->cursor() as $invoice) {
    // một query, model được dựng dần (generator, Chương 13)
}
```

Eloquent `chunk` tự thêm `ORDER BY` khoá chính nếu bạn chưa có; query builder thuần (`DB::table`) thì
bắt buộc tự `orderBy`, thiếu là ném exception (đọc `enforceOrderBy()` 13.x). Không có thứ tự ổn định thì
`LIMIT/OFFSET` có thể trả dòng lặp hoặc sót.

### 10.2 Bẫy `chunk()` khi callback sửa cột đang lọc

```php
// SAI: chỉ xử lý được 2/3
Invoice::where('status', 'pending')->chunk(1000, function (Collection $invoices): void {
    foreach ($invoices as $invoice) {
        $invoice->update(['status' => 'sent']);
    }
});
```

Với 3.000 hoá đơn pending:

| Lượt | Câu SQL | Tập "pending" lúc đó | Lấy được | Sau callback |
|---|---|---|---|---|
| 1 | `... LIMIT 1000 OFFSET 0` | 1..3000 | 1..1000 | Còn 1001..3000 pending |
| 2 | `... LIMIT 1000 OFFSET 1000` | 1001..3000 | 2001..3000 (bỏ qua 1001..2000) | Còn 1001..2000 pending |
| 3 | `... LIMIT 1000 OFFSET 2000` | 1001..2000 (1.000 dòng) | Rỗng: dừng | 1.000 hoá đơn bị bỏ sót |

`chunkById` không bị vì không đếm vị trí mà nhớ id cuối cùng (`WHERE id > 1000`); đây là *keyset
pagination*. Nó còn nhanh hơn trên bảng lớn: `OFFSET 1000000` bắt MySQL đọc rồi vứt một triệu dòng, còn
`id > ?` nhảy thẳng tới vị trí trong index.

Mô phỏng cả hai bằng PDO và SQLite trong RAM:

```php
<?php
declare(strict_types=1);

// Mô phỏng chunk() (LIMIT/OFFSET) và chunkById() (keyset) khi callback sửa cột đang lọc.
function freshDb(): PDO
{
    $pdo = new PDO('sqlite::memory:', options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
    $pdo->exec("CREATE TABLE invoices (id INTEGER PRIMARY KEY, status TEXT NOT NULL)");
    $ins = $pdo->prepare("INSERT INTO invoices (id, status) VALUES (?, 'pending')");
    for ($i = 1; $i <= 3000; $i++) {
        $ins->execute([$i]);
    }
    return $pdo;
}

function markSent(PDO $pdo, array $ids): void
{
    $in = implode(',', array_fill(0, count($ids), '?'));
    $pdo->prepare("UPDATE invoices SET status = 'sent' WHERE id IN ($in)")->execute($ids);
}

// Kiểu chunk(): trang thứ n = OFFSET n*1000
$pdo = freshDb();
$page = 0;
while (true) {
    $stmt = $pdo->prepare("SELECT id FROM invoices WHERE status = 'pending' ORDER BY id LIMIT 1000 OFFSET ?");
    $stmt->execute([$page * 1000]);
    $ids = $stmt->fetchAll(PDO::FETCH_COLUMN);
    if ($ids === []) {
        break;
    }
    markSent($pdo, $ids);
    $page++;
}
echo 'chunk: còn pending = ', $pdo->query("SELECT COUNT(*) FROM invoices WHERE status = 'pending'")->fetchColumn(), PHP_EOL;

// Kiểu chunkById(): nhớ id cuối cùng
$pdo = freshDb();
$lastId = 0;
while (true) {
    $stmt = $pdo->prepare("SELECT id FROM invoices WHERE status = 'pending' AND id > ? ORDER BY id LIMIT 1000");
    $stmt->execute([$lastId]);
    $ids = $stmt->fetchAll(PDO::FETCH_COLUMN);
    if ($ids === []) {
        break;
    }
    markSent($pdo, $ids);
    $lastId = (int) end($ids);
}
echo 'chunkById: còn pending = ', $pdo->query("SELECT COUNT(*) FROM invoices WHERE status = 'pending'")->fetchColumn(), PHP_EOL;
// in ra:
// chunk: còn pending = 1000
// chunkById: còn pending = 0
```

Phiên bản đúng và nhanh hơn trong Laravel: một `UPDATE` cho mỗi chunk thay vì một `UPDATE` cho mỗi dòng.

```php
Invoice::where('status', 'pending')->chunkById(1000, function (Collection $invoices): void {
    Invoice::whereKey($invoices->modelKeys())->update(['status' => 'sent']);   // nhớ: không có model event
});
```

Các bẫy nhỏ hơn (đều có trong tài liệu Laravel):

- `chunkById` tự thêm `where id > ?`. Điều kiện của bạn có `orWhere` không nhóm thì thành
  `a OR b AND id > ?`, sai logic, có thể lặp vô hạn. Luôn nhóm:
  `->where(fn ($q) => $q->where('credits', 1)->orWhere('credits', 2))->chunkById(...)`.
- Callback sửa khoá chính hoặc khoá ngoại nằm trong điều kiện thì vẫn có thể bỏ sót.
- `cursor()` không eager load được (chỉ giữ một model), và theo tài liệu Laravel, PDO vẫn buffer toàn bộ
  kết quả thô nên với tập rất lớn vẫn hết RAM ([Chương 16](16-php-va-database.md) nói về buffered query
  của PDO MySQL). Khi đó dùng `lazyById()`.
- Script chạy lâu: nếu có bật query log (`DB::enableQueryLog()`) thì tắt, vì log giữ mọi câu SQL trong
  RAM.

## 11. Transaction

### 11.1 `DB::transaction`

Nhắc lại từ [Chương 16, mục 6](16-php-va-database.md): *transaction* gom nhiều câu thành một khối
"hoặc tất cả, hoặc không". Laravel bọc việc `beginTransaction`/`commit`/`rollBack` trong một closure:

```php
use Illuminate\Support\Facades\DB;

$order = DB::transaction(function () use ($cart): Order {
    $order = Order::create(['user_id' => $cart->userId, 'total' => $cart->total]);
    $order->items()->createMany($cart->items);
    $affected = Product::whereKey($cart->productId)->where('stock', '>', 0)->decrement('stock');
    if ($affected === 0) {
        throw new OutOfStockException();     // ném exception: rollback toàn bộ
    }
    return $order;                           // giá trị trả về của closure là giá trị của transaction()
}, attempts: 3);
```

- Closure chạy xong không lỗi: `COMMIT`. Closure ném exception: `ROLLBACK` rồi ném lại exception.
- Transaction áp dụng cho mọi thứ đi qua connection đó: SQL thô, query builder, Eloquent.
- Cách thủ công: `DB::beginTransaction()`, `DB::commit()`, `DB::rollBack()`. Ít dùng vì dễ quên rollback
  ở một nhánh lỗi.
- Connection khác: `DB::connection('analytics')->transaction(...)`. Transaction không trải qua hai
  connection.

### 11.2 Bên dưới: lồng nhau và retry

Đọc `Concerns/ManagesTransactions.php` 13.x:

1. Gọi `transaction()` khi chưa có transaction: gửi `BEGIN` (qua PDO). Gọi lồng bên trong một
   transaction đang mở: tạo `SAVEPOINT trans2`, `trans3`... Rollback lớp trong chỉ quay về savepoint
   (`ROLLBACK TO SAVEPOINT`), lớp ngoài vẫn tiếp tục được.
2. Tham số `attempts` (mặc định 1): nếu exception là *lỗi đồng thời* và còn lượt, Laravel rollback rồi
   chạy lại **toàn bộ closure** từ đầu. "Lỗi đồng thời" theo `ConcurrencyErrorDetector` 13.x: SQLSTATE
   `40001`, hoặc message chứa "Deadlock found when trying to get lock", "Lock wait timeout exceeded; try
   restarting transaction", và vài message tương tự của database khác. Nghĩa là cả lock wait timeout cũng
   được retry, không chỉ deadlock.
3. Nếu lỗi đồng thời xảy ra ở transaction **lồng** (cấp > 1): không retry ở lớp trong mà ném
   `DeadlockException` ra ngoài. Lý do (comment trong mã nguồn): khi deadlock, MySQL rollback **cả**
   transaction, savepoint của lớp trong cũng mất, chỉ lớp ngoài cùng mới retry được.

⚠️ Vì closure có thể chạy lại, đừng đặt trong đó việc không thu hồi được: gửi email, gọi API thanh toán,
ghi file, đẩy message. Retry là làm thêm lần nữa, còn rollback DB không thu hồi được chúng. Chỉ để thao
tác DB bên trong.

⚠️ Như mục 1.5 và 2.9: câu DDL trong transaction trên MySQL gây implicit commit.

Deadlock là gì, vì sao xảy ra, cách giảm (khoá theo cùng thứ tự, transaction ngắn, index đúng):
[Database chương 15](../database/15-lock-deadlock.md). Isolation level mặc định của InnoDB
(`REPEATABLE READ`) và các hiện tượng như lost update: [chương 14](../database/14-isolation-mvcc.md).

### 11.3 Bug kinh điển: dispatch job bên trong transaction

```php
DB::transaction(function () use ($data): void {
    $order = Order::create($data);
    SendOrderConfirmation::dispatch($order);   // job vào queue (Redis) NGAY, trước COMMIT
    // ... thêm vài query tốn 200ms
});
```

| Bước | Request web | Queue worker | Kết quả |
|---|---|---|---|
| 1 | `BEGIN`; `INSERT INTO orders` (id 42) | | Dòng 42 chưa commit, session khác không thấy |
| 2 | `dispatch()`: đẩy job `{order_id: 42}` vào Redis | | Job đã nằm trong queue |
| 3 | Đang chạy tiếp các query khác | Lấy job, `SELECT * FROM orders WHERE id = 42` | Không thấy dòng: `ModelNotFoundException`, job lỗi |
| 4 | `COMMIT` | | Đơn có trong DB nhưng email không được gửi |
| 4' | (nhánh khác) query sau lỗi, `ROLLBACK` | Job chạy | Email xác nhận cho một đơn không tồn tại |

Sửa: `SendOrderConfirmation::dispatch($order)->afterCommit();` (job chờ transaction ngoài cùng commit; bị
rollback thì job bị bỏ), hoặc bật `'after_commit' => true` cho queue connection để áp cho mọi job. Event,
listener, mail, notification có cơ chế tương tự. Chi tiết và *outbox pattern* cho trường hợp cần chắc
chắn tuyệt đối: [Chương 29](29-laravel-queue-event-schedule-cache.md).

Cũng có `DB::afterCommit(fn () => ...)` để chạy một callback bất kỳ sau khi transaction ngoài cùng commit.

### 11.4 Khoá dòng trên model

```php
DB::transaction(function () use ($id): void {
    $account = Account::whereKey($id)->lockForUpdate()->firstOrFail();   // SELECT ... FOR UPDATE
    $account->balance = bcsub($account->balance, '100.00', 2);
    $account->save();
});

$post->refreshForUpdate();    // đọc lại model với FOR UPDATE (trong transaction)
```

Pessimistic lock (khoá trước) và optimistic lock (cột `version`, `UPDATE ... WHERE version = ?` rồi kiểm
tra số dòng bị ảnh hưởng): so sánh và khi nào dùng cái nào ở [Database chương 15](../database/15-lock-deadlock.md).

## 12. Upsert, thao tác hàng loạt và raw query

### 12.1 Upsert

*Upsert* = insert nếu chưa có, update nếu đã có, trong **một câu SQL**:

```php
Product::upsert(
    [
        ['sku' => 'A1', 'name' => 'Áo', 'price' => 100],
        ['sku' => 'B2', 'name' => 'Quần', 'price' => 200],
    ],
    uniqueBy: ['sku'],              // cột xác định "đã có"
    update: ['name', 'price'],      // cột cần cập nhật khi đã có
);
// MySQL: insert into products (...) values (...), (...)
//        on duplicate key update name = values(name), price = values(price)
// (output minh hoạ, rút gọn: Eloquent còn thêm created_at, updated_at vào values
//  và updated_at = values(updated_at) vào phần update)
```

Grammar MySQL 13.x mặc định sinh dạng `values(cột)`; MySQL từ 8.0.20 đánh dấu cách viết này là
deprecated (vẫn chạy). Connection có tuỳ chọn `use_upsert_alias` để Laravel sinh dạng alias
(`insert ... as laravel_upsert_alias on duplicate key update price = laravel_upsert_alias.price`).

So với vòng lặp `updateOrCreate` (mỗi dòng ít nhất 2 query, có race condition nếu thiếu unique index),
`upsert` là một câu, nguyên tử, dùng cho đồng bộ dữ liệu, import, seeder idempotent.

⚠️ Hai cảnh báo trong tài liệu Laravel:

- Cột trong `uniqueBy` phải có primary hoặc unique index (trừ SQL Server).
- Driver MySQL và MariaDB **bỏ qua** tham số `uniqueBy`, luôn dùng **mọi** primary và unique index của
  bảng (đó là bản chất của `ON DUPLICATE KEY UPDATE`). Bảng có hai unique index (`sku` và `barcode`) thì
  một dòng có thể "trùng" theo `barcode` và update nhầm sản phẩm khác.

`upsert` tự điền `created_at`/`updated_at` nhưng không bắn model event, không qua mutator (mục 7.4).

### 12.2 Thao tác hàng loạt và "ORM sinh SQL tệ"

| Viết | SQL thực tế | Nên viết |
|---|---|---|
| `Order::where(...)->get()->count()` | `SELECT *`, kéo hết về PHP rồi đếm | `->count()`: `SELECT COUNT(*)` |
| `->get()->sum('total')` | Như trên | `->sum('total')` |
| `if (Order::where(...)->count() > 0)` | Đếm hết các dòng khớp | `->exists()` |
| Vòng lặp `Model::find($id)->update([...])` | 2N query | Một `whereIn(...)->update([...])` hoặc `upsert` |
| Vòng lặp `Model::create([...])` | N câu `INSERT`, N lần event | `Model::insert([...])` theo lô (không event, không timestamps) |
| `->orderBy('id')->paginate()` ở trang 5000 | `LIMIT 15 OFFSET 74985` | `cursorPaginate()` (mục 13) |

⚠️ `whereIn('id', $ids)` với hàng chục nghìn giá trị sinh hàng chục nghìn placeholder; prepared statement
của MySQL giới hạn 65.535 placeholder mỗi câu. Chia lô (`collect($ids)->chunk(1000)`), hoặc với mảng số
nguyên lớn dùng `whereIntegerInRaw` (Laravel ép từng phần tử về `int` rồi viết thẳng vào SQL).

### 12.3 Raw query và an toàn

Có lúc builder không đủ (window function, CTE, báo cáo phức tạp). Dùng SQL thô, nhưng **giá trị vẫn
bind**:

```php
// ĐÚNG: binding
$rows = DB::select(
    'select user_id, sum(total) as s from orders where created_at >= ? group by user_id',
    [$from],
);
$posts = Post::whereRaw('lower(title) like ?', ["%{$q}%"])->get();
$posts = Post::selectRaw('*, views / greatest(datediff(now(), created_at), 1) as hot')->orderByDesc('hot')->get();

// SAI: ghép chuỗi, SQL injection
$rows = DB::select("select * from orders where status = '$status'");
$posts = Post::whereRaw("title = '$title'")->get();
```

Các method nhận chuỗi SQL thô: `DB::raw`, `selectRaw`, `whereRaw`, `havingRaw`, `orderByRaw`,
`groupByRaw`, `DB::statement`, `DB::unprepared`. Mỗi cái đều có tham số mảng binding (trừ `DB::raw` và
`unprepared`); hãy dùng nó.

⚠️ Binding chỉ bảo vệ **giá trị**. Tên cột, tên bảng, hướng sắp xếp không bind được (tài liệu Laravel:
"PDO does not support binding column names"). Cho người dùng chọn cột sắp xếp thì phải whitelist:

```php
// SAI: ?sort=... đi thẳng vào SQL
Post::orderBy($request->input('sort'))->get();

// ĐÚNG
$sort = in_array($request->input('sort'), ['title', 'created_at', 'views'], true)
    ? $request->input('sort')
    : 'created_at';
$dir = $request->input('dir') === 'asc' ? 'asc' : 'desc';
Post::orderBy($sort, $dir)->get();
```

SQL injection và các lớp phòng thủ khác: [Chương 17](17-bao-mat.md).

## 13. Phân trang: offset và cursor

### 13.1 `paginate` và `simplePaginate`

```php
// Controller
$posts = Post::published()->latest()->paginate(15);      // trang hiện tại lấy từ ?page=
return view('posts.index', ['posts' => $posts]);         // Blade: {{ $posts->links() }}
return $posts;                                            // hoặc trả JSON: data, current_page, last_page, total, links...
```

`paginate(15)` chạy **hai** query: một `COUNT(*)` để biết tổng số trang, một `LIMIT 15 OFFSET (page-1)*15`
để lấy dữ liệu. `simplePaginate(15)` bỏ query đếm, chỉ cho "Trước/Sau" (lấy dư một dòng để biết còn
trang sau không). Trên bảng lớn có điều kiện phức tạp, `COUNT(*)` có thể chậm hơn cả query lấy dữ liệu.

Hai trang danh sách trên cùng màn hình: đặt tên tham số khác, `paginate(15, ['*'], 'comments_page')`.

### 13.2 Vấn đề của offset

1. Chậm khi trang sâu: `LIMIT 15 OFFSET 150000` bắt MySQL đọc và bỏ 150.000 dòng rồi mới trả 15 dòng.
   Trang càng sâu càng chậm, dù có index ([Database chương 12](../database/12-explain-toi-uu-query.md)).
2. Lệch khi dữ liệu thay đổi: người dùng đang xem trang 1 (bài 1..15 theo mới nhất), có 3 bài mới đăng,
   bấm trang 2 (`OFFSET 15`) thì thấy lại 3 bài cuối của trang 1. Ngược lại, có bài bị xoá thì bỏ sót.

### 13.3 `cursorPaginate`

Thay vì "bỏ qua N dòng", *cursor pagination* nhớ giá trị của dòng cuối cùng và hỏi "các dòng sau giá trị
này":

```sql
-- Offset, trang 2 (theo tài liệu Laravel)
select * from users order by id asc limit 15 offset 15;
-- Cursor, trang 2
select * from users where id > 15 order by id asc limit 15;
```

```php
$posts = Post::orderByDesc('created_at')->orderByDesc('id')->cursorPaginate(15);
// URL trang sau: /posts?cursor=eyJ...
```

Cursor trong URL không phải số trang mà là giá trị các cột sắp xếp của dòng cuối, mã hoá base64 (đọc
`Illuminate\Pagination\Cursor::encode()` 13.x: `json_encode` rồi `base64_encode` kiểu URL-safe). Giải mã
cursor mẫu trong tài liệu Laravel:

```php
<?php
declare(strict_types=1);

// Cursor trong URL của cursorPaginate chỉ là JSON mã hoá base64 (theo ví dụ trong tài liệu Laravel)
$cursor = 'eyJpZCI6MTUsIl9wb2ludHNUb05leHRJdGVtcyI6dHJ1ZX0';
$json = base64_decode(strtr($cursor, '-_', '+/'), true);
var_dump($json);
var_dump(json_decode((string) $json, true, flags: JSON_THROW_ON_ERROR));
// in ra:
// string(35) "{"id":15,"_pointsToNextItems":true}"
// array(2) {
//   ["id"]=>
//   int(15)
//   ["_pointsToNextItems"]=>
//   bool(true)
// }
```

Cursor không được mã hoá hay ký: người dùng
sửa được nó. Laravel đưa các giá trị đó vào query qua binding nên không gây injection, nhưng đừng đặt dữ
liệu nhạy cảm làm cột sắp xếp.

Giới hạn theo tài liệu Laravel:

- Query phải có `orderBy`, và các cột sắp xếp phải thuộc bảng đang phân trang.
- Thứ tự phải dựa trên ít nhất một cột **unique** hoặc tổ hợp cột unique (vì thế ví dụ trên thêm `id`
  sau `created_at`: nhiều bài có cùng `created_at`). Cột có giá trị `NULL` không được hỗ trợ.
- Chỉ có "Trước/Sau", không nhảy tới trang số 37 được.

Hợp với: danh sách dài kiểu cuộn vô hạn, API cho mobile, bảng lớn ghi liên tục. Cần index khớp thứ tự
sắp xếp, ví dụ `index(['created_at', 'id'])`, để `WHERE` của cursor nhảy thẳng vào index. Kỹ thuật này
(*keyset pagination*) ở mức SQL: [Database chương 12](../database/12-explain-toi-uu-query.md).

| | `paginate` | `simplePaginate` | `cursorPaginate` |
|---|---|---|---|
| Query | `COUNT` + `LIMIT/OFFSET` | `LIMIT/OFFSET` | `WHERE (cột sắp xếp) > giá trị` + `LIMIT` |
| Tổng số trang, nhảy trang | Có | Không | Không |
| Trang sâu | Chậm dần | Chậm dần | Ổn định nếu có index |
| Dữ liệu đổi giữa chừng | Có thể lặp/sót | Có thể lặp/sót | Không lặp/sót theo thứ tự đã chọn |

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Đặt `strict => false` để hết lỗi `GROUP BY` | Tắt cả `STRICT_TRANS_TABLES`: dữ liệu sai bị cắt hoặc ép âm thầm | Sửa câu query; giữ `strict => true` |
| Migration lỗi giữa chừng, chạy lại báo "column already exists" | MySQL không có transactional DDL, câu trước đã có hiệu lực | Mỗi migration một thay đổi nhỏ, thử `--pretend` và trên bản sao dữ liệu |
| `->change()` làm mất `default`, `unsigned`, comment | `change()` thay cả định nghĩa cột | Viết lại đầy đủ mọi modifier cần giữ |
| `ALTER` nhẹ mà làm treo cả hệ thống | Chờ metadata lock sau một transaction dài, chặn mọi query sau nó | Chạy lúc ít traffic, `lock_wait_timeout` ngắn, tránh transaction dài; ghi rõ `instant()`/`lock('none')` để lỗi sớm |
| `orWhere` trả dữ liệu của người khác | `a AND b OR c` | Luôn nhóm `orWhere` trong closure |
| `when($request->input('x'), ...)` bỏ qua giá trị `0` | `'0'` là falsy | `when($request->filled('x'), ...)` |
| `User::create($request->all())` | Mass assignment: client gửi thêm `is_admin` | `#[Fillable]` whitelist + `$request->validated()` |
| Field mới không được lưu, không lỗi | Key ngoài fillable bị bỏ qua lặng lẽ | Thêm vào fillable; bật `preventSilentlyDiscardingAttributes` ở dev |
| Observer không chạy khi update hàng loạt | `Model::where()->update()` không dựng model, không event | Nạp từng model nếu cần event, hoặc tự làm phần việc của observer |
| `$model->options['k'] = v` không có tác dụng | Thuộc tính đi qua `__get`, trả bản sao | Gán lại cả mảng, hoặc cast `AsArrayObject` |
| Trang danh sách 100 dòng chạy 101+ query | N+1: lazy load trong vòng lặp, view, accessor `$appends` | `with`, `withCount`; bật `preventLazyLoading` ở dev |
| `chunk()` bỏ sót bản ghi | `OFFSET` trên tập đang bị callback sửa | `chunkById()` / `lazyById()` |
| Hai dòng trùng dù dùng `firstOrCreate` | Không có unique index, hai request cùng `INSERT` | Unique index ở DB |
| Job lỗi "model not found" hoặc gửi email cho đơn bị rollback | Dispatch trong transaction, trước `COMMIT` | `afterCommit()` / `after_commit => true` |
| Gửi email hai lần khi deadlock | `DB::transaction(..., attempts)` chạy lại cả closure | Chỉ thao tác DB trong closure |
| `upsert` cập nhật nhầm dòng | MySQL bỏ qua `uniqueBy`, dùng mọi unique index | Biết rõ mọi unique index của bảng |
| `orderBy($request->input('sort'))` | Tên cột không bind được: injection | Whitelist tên cột và hướng sắp xếp |
| Trang sâu rất chậm | `OFFSET` lớn | `cursorPaginate` với index khớp thứ tự |

## Tóm tắt chương

- Laravel có ba tầng trên PDO: SQL thô qua `DB`, query builder, Eloquent. Mọi connection đặt
  `ERRMODE_EXCEPTION`, native prepare; `strict => true` đặt `sql_mode` chặt cho MySQL.
- Migration là lịch sử schema nằm trong git; bảng `migrations` ghi file nào đã chạy theo batch. Trên
  MySQL, migration không nguyên tử, và `ALTER` có thể khoá bảng hoặc kẹt metadata lock; Laravel 13 cho
  ghi rõ `instant()`, `inplace()`, `lock()`.
- Seeder chèn dữ liệu, factory sinh model giả (Faker nằm ở `require-dev`).
- Query builder gom điều kiện và binding; binding chỉ bảo vệ giá trị, không bảo vệ tên cột. Nhóm
  `orWhere`, coi chừng `when` với `'0'`.
- Model Eloquent giữ `attributes` và `original`, `save()` chỉ `UPDATE` cột dirty và bỏ qua khi không có
  gì đổi. Mặc định chặn mass assignment; khai `#[Fillable]` và chỉ truyền dữ liệu đã validate.
- Cast, accessor, mutator biến đổi dữ liệu khi đọc ghi; `decimal` trả chuỗi; cast `array` không sửa tại
  chỗ được.
- Global scope và soft delete chỉ áp cho Eloquent; thao tác hàng loạt, cascade của khoá ngoại không bắn
  model event.
- Relationship: `belongsTo` ở bảng chứa khoá ngoại; pivot đặt tên theo thứ tự chữ cái; polymorphic không
  có khoá ngoại, nên dùng `enforceMorphMap`.
- N+1 không lên slow log; sửa bằng `with`/`withCount`, bắt bằng `preventLazyLoading`/`shouldBeStrict`.
- Dữ liệu lớn: `chunkById`/`lazyById`. Transaction: `DB::transaction(fn, attempts)` chạy lại cả closure
  khi deadlock hoặc lock wait timeout; dispatch job thì `afterCommit`. Phân trang sâu: `cursorPaginate`.

## Câu hỏi tự kiểm tra

1. Ba tầng làm việc với database trong Laravel là gì? Khi nào bạn chọn query builder thay vì Eloquent?
   (mục 1.1)
2. Laravel biết migration nào đã chạy bằng cách nào? `migrate:rollback` lùi lại những gì? (mục 2.1, 2.3)
3. Vì sao trên MySQL một migration lỗi giữa chừng để lại database ở trạng thái nửa vời, còn trên
   PostgreSQL thì không? (mục 2.9)
4. Một câu `ALTER TABLE ... ALGORITHM=INSTANT` lẽ ra mất vài mili giây lại làm mọi request treo. Giải
   thích chuỗi sự kiện. (mục 2.10)
5. `Post::where('user_id', 7)->where('status', 'draft')->orWhere('status', 'review')->get()` trả về
   những gì? Sửa thế nào? (mục 4.1)
6. Model đã khai `#[Fillable(['title'])]`. Gọi `$post->update(['title' => 'A', 'is_featured' => true])`
   thì chuyện gì xảy ra với `is_featured`? Nếu model không khai gì cả thì sao? (mục 5.5)
7. Liệt kê ba cách thay đổi dữ liệu không bắn model event. (mục 7.4, 2.8, 12.1)
8. Vì sao N+1 không xuất hiện trong slow query log? Kể ba chỗ N+1 hay trốn ngoài vòng `foreach` trong
   controller. (mục 9.1, 9.3)
9. `DB::transaction($fn, attempts: 3)` retry trong những trường hợp nào, và vì sao ở transaction lồng thì
   không retry? (mục 11.2)
10. So sánh `paginate`, `simplePaginate`, `cursorPaginate` về số query, khả năng nhảy trang và hiệu năng
    ở trang sâu. Cursor pagination đòi hỏi gì ở thứ tự sắp xếp? (mục 13)

## Bài tập

1. **Mô phỏng N+1 và eager loading bằng PHP thuần.** Mở rộng file ở mục 9.1 (PDO + SQLite trong RAM,
   chạy bằng `php file.php`): thêm bảng `comments` (mỗi post 0 đến 10 comment). Viết hai hàm in ra
   "tiêu đề post, tên tác giả, số comment" cho mọi post: một hàm theo kiểu lazy (truy vấn trong vòng lặp),
   một hàm theo kiểu eager (một query cho mỗi bảng, ghép bằng PHP). Đếm và in số query của mỗi cách. Sau
   đó viết phiên bản thứ ba dùng `COUNT` bằng một query `GROUP BY` thay vì nạp comment (giống
   `withCount`).
2. **Thiết kế migration và model cho blog.** Trong một dự án Laravel 13 (skeleton mặc định dùng SQLite,
   tạo bằng `laravel new blog` hoặc `composer create-project laravel/laravel blog`), viết migration cho
   `posts`, `comments`, `tags`, `post_tag` với khoá ngoại, unique index, và index phục vụ truy vấn
   "bài đã đăng mới nhất". Viết model với `#[Fillable]`, cast, relationship đầy đủ hai chiều, một local
   scope `published`. Viết factory và seeder tạo 20 user, mỗi user 0 đến 5 bài, mỗi bài vài tag. Chạy
   `php artisan migrate:fresh --seed` thành công.
3. **Săn N+1.** Trên dự án bài 2, viết route trả JSON danh sách bài kèm tên tác giả, tên tag và số
   comment. Bật `Model::preventLazyLoading()` và `DB::listen` để đếm query; sửa cho tới khi số query
   không phụ thuộc số bài viết. Ghi lại số query trước và sau.
4. **Chuyển trạng thái hàng loạt an toàn.** Viết một lệnh Artisan chuyển mọi bài `draft` cũ hơn 30 ngày
   sang `archived`, xử lý theo lô 500 dòng, không bỏ sót (thử với 2.000 bài bằng factory), và giải thích
   trong comment vì sao bạn chọn `chunkById` hay `lazyById`, có cần model event hay không.

## Đọc thêm

- Laravel 13.x: [Database: Getting Started](https://laravel.com/docs/13.x/database) ·
  [Migrations](https://laravel.com/docs/13.x/migrations) · [Seeding](https://laravel.com/docs/13.x/seeding) ·
  [Query Builder](https://laravel.com/docs/13.x/queries) · [Pagination](https://laravel.com/docs/13.x/pagination) ·
  [Eloquent](https://laravel.com/docs/13.x/eloquent) ·
  [Relationships](https://laravel.com/docs/13.x/eloquent-relationships) ·
  [Mutators & Casting](https://laravel.com/docs/13.x/eloquent-mutators) ·
  [Factories](https://laravel.com/docs/13.x/eloquent-factories) (nguồn markdown: github.com/laravel/docs nhánh 13.x)
- Mã nguồn `laravel/framework` nhánh 13.x, thư mục `src/Illuminate/Database`: `Connectors/MySqlConnector.php`,
  `Connectors/Connector.php`, `Connection.php`, `Concerns/ManagesTransactions.php`,
  `ConcurrencyErrorDetector.php`, `Migrations/Migrator.php`, `Schema/Blueprint.php`,
  `Schema/Grammars/MySqlGrammar.php`, `Query/Builder.php`, `Query/Grammars/MySqlGrammar.php`,
  `Eloquent/Model.php`, `Eloquent/Builder.php`, `Eloquent/Concerns/GuardsAttributes.php`,
  `Eloquent/Concerns/HasAttributes.php`, `Eloquent/SoftDeletes.php`; `src/Illuminate/Pagination/Cursor.php`.
- Skeleton `laravel/laravel` nhánh 13.x: `config/database.php`, `.env.example`, `database/`, `app/Models/User.php`.
- MySQL 8.4 Reference Manual: [Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html),
  [Online DDL Performance and Concurrency](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-performance.html),
  [Statements That Cause an Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html),
  [Server SQL Modes](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html).
- Martin Fowler: [Active Record](https://martinfowler.com/eaaCatalog/activeRecord.html),
  [Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html).
- [Use The Index, Luke: Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)
  (vì sao keyset pagination nhanh hơn offset).
- Giáo trình [Database](../database/README.md), đặc biệt chương 11, 12, 14, 15, 19, 20.
