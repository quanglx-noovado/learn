# Chương 20. Thay đổi schema an toàn

> [← Mục lục](README.md) · [← Chương 19: Database từ phía ứng dụng](19-database-tu-ung-dung.md)

**Bạn sẽ học được:**

- Migration là gì, vì sao schema phải được quản lý như code, và migration của Laravel chạy ra sao
  trên MySQL (không có transaction) so với PostgreSQL (có transaction).
- Online DDL của MySQL: ba thuật toán `INSTANT`, `INPLACE`, `COPY`, mệnh đề `LOCK`, và cách tra
  trước một câu `ALTER TABLE` có khoá ghi hay dựng lại bảng không.
- *Metadata lock*: vì sao một câu `ALTER` chỉ cần vài mili giây vẫn có thể làm cả ứng dụng treo, và
  cách phòng bằng `lock_wait_timeout` cùng retry.
- Cách hai công cụ gh-ost và pt-online-schema-change đổi schema bảng lớn mà không khoá bảng.
- Kỹ thuật *expand/contract*: đổi tên cột, đổi kiểu cột không downtime theo từng bước; backfill dữ
  liệu theo batch; thêm cột `NOT NULL` và thêm index trên bảng lớn.
- Phía PostgreSQL: `CREATE INDEX CONCURRENTLY`, ràng buộc `NOT VALID` rồi `VALIDATE CONSTRAINT`.

**Cần biết trước:** [Chương 04](04-ddl-constraint.md) (cú pháp `ALTER TABLE`, DDL tự commit),
[Chương 11](11-index.md) (index là gì), [Chương 13](13-transaction-acid.md) (transaction),
[Chương 15](15-lock-deadlock.md) (lock nói chung). Biết sơ qua replication
([Chương 22](22-replication-ha.md)) sẽ giúp hiểu phần replica lag, nhưng chương này giải thích đủ
để đọc trước.

## 1. Schema cũng thay đổi, và đó là lúc dễ gây sự cố

### 1.1 Vì sao schema phải thay đổi

Ở [chương 02](02-mo-hinh-quan-he-thiet-ke.md) bạn đã thiết kế schema cho một ứng dụng. Thiết kế đó
không đứng yên. Sản phẩm thêm tính năng thì cần cột mới, bảng mới; truy vấn chậm thì cần index mới;
dữ liệu lớn lên thì cột `INT` sắp tràn và phải đổi sang `BIGINT`; đặt tên cột sai từ đầu thì muốn đổi
tên. Một ứng dụng sống vài năm thường có hàng trăm lần thay đổi schema.

Trên máy của bạn, mỗi thay đổi chỉ là một câu `ALTER TABLE` chạy trong tích tắc vì bảng có vài chục
dòng. Trên production thì khác ở ba điểm:

1. **Bảng lớn.** Bảng có hàng chục triệu dòng, vài chục GB. Một thao tác phải đọc và ghi lại toàn bộ
   bảng có thể mất hàng giờ.
2. **Bảng đang được dùng.** Trong lúc đổi schema, người dùng vẫn đặt hàng, đăng nhập, đọc dữ liệu.
   Nếu thao tác chặn đọc hoặc ghi, đó là downtime.
3. **Code đang chạy phụ thuộc vào schema.** Code cũ đang chạy trên server biết tên cột cũ. Bạn đổi
   tên cột trong một giây, mọi request của code cũ lỗi ngay trong giây tiếp theo.

Chương này dạy cách thay đổi schema mà không gây ra ba loại sự cố trên. Trước hết, cần hiểu công cụ
mà mọi team dùng để quản lý thay đổi schema: migration.

### 1.2 Migration là gì

*Migration* (di trú schema) là một file code mô tả **một** thay đổi schema, có tên hoặc số thứ tự để
biết thứ tự chạy. Tập hợp các file migration chính là lịch sử của schema: từ database rỗng, chạy lần
lượt mọi migration sẽ ra đúng schema hiện tại.

Vì sao không chạy `ALTER TABLE` bằng tay trên production rồi thôi:

- **Đồng bộ nhiều môi trường.** Máy dev của mỗi người, máy CI, staging, production đều phải có cùng
  schema. Nếu thay đổi chỉ nằm trong đầu một người hoặc trong lịch sử terminal của họ, các môi trường
  sẽ lệch nhau và bug chỉ xuất hiện ở một nơi.
- **Review được.** Migration nằm trong git, đi cùng pull request với code dùng nó. Người review thấy
  "PR này thêm cột `orders.note` và thêm index trên `orders(user_id, created_at)`".
- **Biết cái gì đã chạy.** Công cụ migration ghi lại migration nào đã chạy trên database nào, nên chạy
  lại lệnh migrate chỉ chạy những cái mới.
- **Tự động hoá.** Deploy chạy migration như một bước của pipeline, không cần ai đăng nhập vào
  database.

Cơ chế chung của gần như mọi công cụ migration (Laravel, Rails, Flyway, Liquibase, golang-migrate...):

```
database/migrations/
  2026_01_10_000000_create_users_table.php      ┐
  2026_03_02_000000_add_phone_to_users.php      ├─ mỗi file một thay đổi, sắp theo tên
  2026_09_20_000000_add_index_orders_user.php   ┘

Bảng "migrations" trong database (do công cụ tự tạo):
+----+-------------------------------------------+-------+
| id | migration                                 | batch |
+----+-------------------------------------------+-------+
|  1 | 2026_01_10_000000_create_users_table      |     1 |
|  2 | 2026_03_02_000000_add_phone_to_users      |     2 |
+----+-------------------------------------------+-------+

Lệnh migrate:  file nào chưa có trong bảng migrations → chạy, rồi ghi tên vào bảng.
               Ở đây chỉ chạy 2026_09_20_..._add_index_orders_user (batch 3).
```

Mỗi migration thường có hai chiều: `up` (áp thay đổi) và `down` (hoàn tác). Chiều `down` hữu ích ở môi
trường dev; trên production, như bạn sẽ thấy ở mục 5, "rollback" thật sự thường là một migration mới
chứ không phải chạy `down`.

### 1.3 Migration trong Laravel

Một migration Laravel là một file PHP trả về một class kế thừa `Migration`:

```php
<?php
declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::table('users', function (Blueprint $table): void {
            $table->string('phone', 20)->nullable();
        });
    }

    public function down(): void
    {
        Schema::table('users', function (Blueprint $table): void {
            $table->dropColumn('phone');
        });
    }
};
```

Các lệnh artisan liên quan (chạy ở thư mục gốc của project Laravel):

| Lệnh | Tác dụng |
|---|---|
| `php artisan make:migration add_phone_to_users` | Tạo file migration mới, tên có tiền tố ngày giờ |
| `php artisan migrate` | Chạy mọi migration chưa chạy, cùng một số `batch` |
| `php artisan migrate --pretend` | In ra các câu SQL sẽ chạy, **không** chạy. Dùng để kiểm tra câu DDL thật trước khi lên production |
| `php artisan migrate --force` | Bỏ qua câu hỏi xác nhận khi môi trường là production (dùng trong script deploy) |
| `php artisan migrate --isolated` | Lấy một atomic lock qua cache driver trước khi chạy, để khi nhiều server cùng deploy thì chỉ một server chạy migration |
| `php artisan migrate:rollback` | Chạy `down` của batch gần nhất |
| `php artisan migrate:status` | Liệt kê migration nào đã chạy |

Builder `Schema` của Laravel chỉ là lớp vỏ: cuối cùng nó sinh câu DDL cho database cụ thể. Với
MySQL, migration ở trên sinh ra (xem bằng `--pretend`):

```sql
alter table `users` add `phone` varchar(20) null
```

Laravel 13 có thêm vài modifier riêng cho MySQL để gắn `ALGORITHM` và `LOCK` vào câu DDL (`->instant()`,
`->inplace()`, `->lock()`); mục 2.6 sẽ dùng chúng sau khi bạn hiểu `ALGORITHM` và `LOCK` là gì.

⚠️ **Migration trên MySQL không có tính nguyên tử.** Như [chương 04](04-ddl-constraint.md) đã nói, mỗi
câu DDL trong MySQL tự commit. Laravel chỉ bọc migration trong transaction khi schema grammar của
database hỗ trợ DDL trong transaction: grammar của PostgreSQL bật, grammar của MySQL tắt (thuộc tính
`$transactions` trong mã nguồn `Illuminate\Database\Schema\Grammars`). Hệ quả: một migration chứa hai
câu `ALTER`, câu thứ hai lỗi, thì câu thứ nhất đã có hiệu lực nhưng bảng `migrations` không ghi nhận
migration đó. Chạy lại thì câu thứ nhất lỗi "column already exists". Quy tắc thực hành: **mỗi
migration chỉ làm một thay đổi schema**, để lỗi ở đâu thì biết chính xác trạng thái ở đó.

Trên PostgreSQL thì ngược lại: migration mặc định chạy trong transaction, lỗi giữa chừng thì rollback
sạch. Nhưng có lệnh không được chạy trong transaction (mục 9), khi đó migration phải tắt transaction
bằng thuộc tính `public $withinTransaction = false;` của class `Migration`.

### 1.4 Bốn câu hỏi trước mọi thay đổi schema trên production

Từ đây tới hết chương, mọi kỹ thuật đều nhằm trả lời bốn câu hỏi. Hãy tập thói quen tự hỏi chúng mỗi
khi review một migration:

| # | Câu hỏi | Nếu bỏ qua thì | Mục |
|---|---|---|---|
| 1 | Câu DDL này có khoá ghi (hoặc khoá cả đọc) không, trong bao lâu? Có dựng lại cả bảng không? | Bảng bị khoá hàng giờ | 2 |
| 2 | Có transaction nào đang giữ bảng mà câu DDL phải chờ không? | Cả ứng dụng treo dù DDL rất nhẹ | 3 |
| 3 | Code đang chạy (bản cũ) và code sắp deploy (bản mới) có cùng chạy được trên schema mới không? | Lỗi hàng loạt trong lúc deploy | 5 |
| 4 | Replica có theo kịp không? Dữ liệu cũ có cần sửa (backfill) không? | Replica trễ hàng giờ, đọc dữ liệu cũ; bảng có dữ liệu sai | 2.7, 6 |

### 1.5 Dữ liệu mẫu cho chương

Các ví dụ SQL trong chương chạy trên MySQL 8.4. Nếu chưa có MySQL, xem cách chạy bằng Docker ở
[chương 01](01-database-la-gi.md):

```sh
# Chạy trên máy của bạn (terminal), cần Docker
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
docker exec -it my84 mysql -uroot -proot
```

Rồi tạo database và hai bảng nhỏ (gõ trong `mysql` client):

```sql
CREATE DATABASE IF NOT EXISTS lab20;
USE lab20;

CREATE TABLE users (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(50)  NOT NULL,          -- utf8mb4 (mặc định): tối đa 200 byte
  email      VARCHAR(100) NOT NULL,
  created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_users_email (email)
);

CREATE TABLE orders (
  id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  user_id    BIGINT UNSIGNED NOT NULL,
  amount     INT NOT NULL,                   -- tiền theo đồng, sẽ có lúc sắp tràn
  status     VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (name, email) VALUES
  ('An',   'an@example.com'),
  ('Bình', 'binh@example.com'),
  ('Chi',  'chi@example.com');

INSERT INTO orders (user_id, amount, status) VALUES
  (1, 150000, 'paid'), (1, 99000, 'pending'), (2, 2000000, 'paid'),
  (3, 45000, 'cancelled'), (3, 120000, 'paid');
```

Bảng `orders` cố ý chưa có khoá ngoại và index trên `user_id`; ta sẽ thêm chúng ở các mục sau. Để thấy
được hiện tượng "bảng lớn", mục 2.5 có cách nhân bảng lên vài trăm nghìn dòng.

## 2. Online DDL của MySQL

### 2.1 Ba cách MySQL thực hiện một câu ALTER TABLE

Khi bạn chạy `ALTER TABLE`, MySQL (với engine InnoDB) chọn một trong ba *algorithm* (thuật toán):

- **`COPY`**: tạo một bảng tạm có cấu trúc mới, copy **từng dòng** từ bảng cũ sang, rồi xoá bảng cũ và
  đổi tên bảng tạm thành tên cũ. Trong suốt quá trình, bảng cũ vẫn cho đọc nhưng **không cho ghi**
  (`INSERT`, `UPDATE`, `DELETE` phải chờ tới khi xong). Đây là cách cũ nhất, chậm nhất.
- **`INPLACE`**: InnoDB tự làm thay đổi bên trong engine, không đi qua bảng tạm ở tầng SQL. Tuỳ thao
  tác, nó có thể *dựng lại bảng* (*rebuild*: viết lại toàn bộ dữ liệu, ví dụ đổi một cột sang `NOT
  NULL`) hoặc không (ví dụ thêm một secondary index: chỉ đọc bảng để dựng cây index mới). Điểm mạnh:
  thường **cho phép đọc và ghi đồng thời** trong lúc chạy. Các thay đổi dữ liệu xảy ra song song được
  ghi tạm vào một *online log* rồi áp vào cuối.
- **`INSTANT`**: chỉ sửa *metadata* (định nghĩa bảng trong *data dictionary*), không đụng tới dữ liệu.
  Xong gần như ngay lập tức, bất kể bảng lớn cỡ nào.

Hình dung trên một bảng 50 GB:

```
COPY      [đọc từng dòng → ghi vào bảng tạm .................. hàng giờ] → đổi tên
          ghi của ứng dụng: BỊ CHẶN suốt thời gian này

INPLACE   [dựng index / rebuild trong InnoDB .................. hàng giờ] → áp online log
          ghi của ứng dụng: vẫn chạy (được ghi vào online log)

INSTANT   [sửa metadata] (mili giây)
```

Thuật ngữ *online DDL* chỉ chung khả năng đổi cấu trúc bảng mà vẫn cho đọc và ghi đồng thời, tức là
`INSTANT` và (phần lớn) `INPLACE`.

**MySQL chọn algorithm như thế nào.** Theo tài liệu `ALTER TABLE` của MySQL 8.4: nếu không ghi mệnh đề
`ALGORITHM`, MySQL dùng `INSTANT` khi thao tác hỗ trợ; nếu không thì dùng `INPLACE`; nếu `INPLACE`
cũng không được thì dùng `COPY`. Nghe thì tiện, nhưng đó chính là cái bẫy: bạn tưởng thao tác nhẹ,
MySQL lặng lẽ rơi xuống `COPY` và khoá ghi hàng giờ mà không báo trước.

Cách phòng là **ghi rõ algorithm mong muốn**. Khi có mệnh đề `ALGORITHM`, MySQL bắt buộc dùng đúng
algorithm đó hoặc báo lỗi ngay, trước khi đụng vào dữ liệu:

```sql
USE lab20;

-- Thêm cột: INSTANT làm được
ALTER TABLE orders ADD COLUMN note VARCHAR(255) NULL, ALGORITHM=INSTANT;
-- Query OK, 0 rows affected

-- Thêm index: không có INSTANT, nhưng INPLACE và cho ghi đồng thời
ALTER TABLE orders ADD INDEX idx_orders_user (user_id), ALGORITHM=INPLACE, LOCK=NONE;

-- Đổi kiểu cột: chỉ COPY làm được, nên câu dưới bị TỪ CHỐI ngay, bảng không đổi gì
ALTER TABLE orders MODIFY amount BIGINT NOT NULL, ALGORITHM=INPLACE;
-- ERROR ... ALGORITHM=INPLACE is not supported ... Try ALGORITHM=COPY.   (output minh hoạ)
```

Lỗi ở câu cuối là điều bạn muốn: nó báo cho bạn biết thao tác này nặng, cần kế hoạch khác (mục 4, 5),
thay vì âm thầm khoá bảng.

### 2.2 Mệnh đề LOCK

Mệnh đề `LOCK` quy định mức đồng thời **tối thiểu** bạn chấp nhận trong lúc `ALTER` chạy:

| `LOCK=` | Ý nghĩa (theo tài liệu MySQL 8.4) |
|---|---|
| `NONE` | Cho cả đọc và ghi đồng thời. Nếu thao tác không hỗ trợ, báo lỗi |
| `SHARED` | Cho đọc, chặn ghi |
| `DEFAULT` (hoặc không ghi) | Cho đồng thời nhiều nhất mà thao tác và algorithm hỗ trợ |
| `EXCLUSIVE` | Chặn cả đọc lẫn ghi |

Nếu bạn yêu cầu mức lỏng hơn mức thao tác cho phép (ví dụ `LOCK=NONE` cho thao tác bắt buộc chặn ghi),
câu lệnh thất bại ngay. Đây là lưới an toàn thứ hai, bên cạnh `ALGORITHM`.

Hai điểm cần nhớ:

- `LOCK` dùng cho thao tác `INPLACE` (và một số thao tác `COPY` để khoá chặt hơn). Với `INSTANT`, tài
  liệu MySQL nói chỉ `LOCK=DEFAULT` được phép; các giá trị khác không áp dụng. Vậy đừng viết
  `ALGORITHM=INSTANT, LOCK=NONE`.
- `COPY` luôn chặn ghi, tối thiểu là mức `LOCK=SHARED`.

### 2.3 Bảng tra: thao tác nào thuộc loại nào

Đây là phần quan trọng nhất của mục 2. Trích từ trang "Online DDL Operations" của tài liệu MySQL 8.4
(chỉ giữ thao tác hay gặp). "Dựng lại bảng" nói về trường hợp chạy bằng `INPLACE`.

| Thao tác | INSTANT | INPLACE | Dựng lại bảng | Cho ghi đồng thời | Ghi chú |
|---|---|---|---|---|---|
| Thêm cột | Có | Có | Không (nhưng INPLACE thì có) | Có | INSTANT là mặc định ở 8.4, thêm được ở mọi vị trí; xem giới hạn ở 2.4 |
| Xoá cột | Có | Có | Có (nếu INPLACE) | Có | |
| Đổi tên cột (giữ nguyên kiểu) | Có | Có | Không | Có | Cột được bảng khác tham chiếu bằng khoá ngoại: chỉ INPLACE |
| Đổi thứ tự cột (`FIRST`, `AFTER` với cột có sẵn) | Không | Có | Có | Có | |
| Đặt hoặc bỏ `DEFAULT` | Có | Có | Không | Có | Chỉ sửa metadata |
| Đổi kiểu dữ liệu (ví dụ `INT` sang `BIGINT`) | Không | Không | Có | **Không** | Chỉ COPY |
| Nới `VARCHAR` | Không | Có | Không | Có | Chỉ khi số byte lưu độ dài không đổi (2.4) |
| Thu nhỏ `VARCHAR` | Không | Không | Có | Không | Chỉ COPY |
| Đổi cột thành `NULL` | Không | Có | Có | Có | |
| Đổi cột thành `NOT NULL` | Không | Có | Có | Có | Cần strict SQL mode; lỗi nếu còn dòng NULL |
| Thêm giá trị vào **cuối** `ENUM`/`SET` | Có | Có | Không | Có | Khi kích thước lưu trữ không đổi; chèn vào giữa thì COPY |
| Thêm secondary index | Không | Có | Không | Có | |
| Xoá hoặc đổi tên index | Không | Có | Không | Có | Chỉ sửa metadata |
| Thêm `FULLTEXT` index | Không | Có | Có với index đầu tiên (nếu chưa có cột `FTS_DOC_ID`) | **Không** | |
| Thêm primary key | Không | Có | Có | Có | Tổ chức lại toàn bộ dữ liệu, rất đắt |
| Xoá primary key (không thêm cái mới) | Không | Không | Có | Không | Chỉ COPY |
| Thêm khoá ngoại | Không | Có | Không | Có | INPLACE chỉ khi `foreign_key_checks` tắt, nếu không thì chỉ COPY |
| Xoá khoá ngoại | Không | Có | Không | Có | |
| Thêm cột generated `VIRTUAL` | Có | Có | Không | Có | Bảng không partition |
| Thêm cột generated `STORED` | Không | Không | Có | Không | Chỉ COPY |
| Thêm cột `AUTO_INCREMENT` | Không | Có | Có | **Không** | Tối thiểu `LOCK=SHARED` |
| Chuyển charset (`CONVERT TO CHARACTER SET`) | Không | Có | Có nếu encoding khác | **Không** | |
| `OPTIMIZE TABLE`, `ALTER TABLE ... FORCE` | Không | Có | Có | Có | Không INPLACE được với bảng có FULLTEXT |
| Đổi tên bảng | Có | Có | Không | Có | Quyền GRANT riêng cho bảng không đi theo tên mới |

Cách đọc bảng: cột "Cho ghi đồng thời = Không" là thứ cần sợ trên bảng lớn, vì trong suốt thời gian
chạy ứng dụng không ghi được. Cột "Dựng lại bảng = Có" nghĩa là thời gian chạy tỉ lệ với kích thước
bảng (và tốn thêm đĩa), dù vẫn cho ghi.

### 2.4 Những chi tiết hay bị hỏi

**Ranh giới 255 byte của VARCHAR.** InnoDB lưu độ dài của mỗi giá trị `VARCHAR` bằng 1 byte nếu độ dài
tối đa của cột từ 0 tới 255 byte, và bằng 2 byte nếu từ 256 byte trở lên. Nới cột mà số byte độ dài
không đổi thì `INPLACE`, chỉ sửa metadata. Nới vượt ranh giới (từ dưới 256 lên từ 256 trở lên) thì
phải `COPY`. Ranh giới tính theo **byte**, không theo ký tự: với `utf8mb4` mỗi ký tự tính tối đa 4
byte, nên `VARCHAR(63)` là 252 byte còn `VARCHAR(64)` đã là 256 byte.

```sql
-- users.name là VARCHAR(50) utf8mb4 = 200 byte (1 byte độ dài)
ALTER TABLE users MODIFY name VARCHAR(60) NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- 240 byte, vẫn 1 byte độ dài: thành công

ALTER TABLE users MODIFY name VARCHAR(100) NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
-- 400 byte, cần 2 byte độ dài: bị từ chối, MySQL gợi ý ALGORITHM=COPY
```

⚠️ Lưu ý câu `MODIFY` phải ghi lại đầy đủ định nghĩa cột (ở đây là `NOT NULL`), nếu không thuộc tính bị
mất ([chương 04](04-ddl-constraint.md), mục 7.2).

**Giới hạn của INSTANT khi thêm hoặc xoá cột** (tài liệu MySQL 8.4):

- Mỗi câu `ALTER ... ALGORITHM=INSTANT` thêm hoặc xoá cột tạo ra một *row version* mới. Tối đa 64 row
  version (MySQL 9.1.0 nâng lên 255). Hết thì MySQL từ chối với lỗi 4092 `Maximum row versions
  reached ...`, và bạn phải dựng lại bảng bằng `INPLACE`/`COPY`; dựng lại thì bộ đếm về 0. Xem bộ đếm:

  ```sql
  SELECT NAME, TOTAL_ROW_VERSIONS
  FROM INFORMATION_SCHEMA.INNODB_TABLES
  WHERE NAME = 'lab20/orders';
  -- sau câu ADD COLUMN note ở mục 2.1, giá trị là 1
  ```

- Không dùng được với bảng `ROW_FORMAT=COMPRESSED`, bảng có `FULLTEXT` index, bảng tạm (bảng tạm chỉ hỗ
  trợ `COPY`), bảng trong data dictionary tablespace.
- Không gộp được với thao tác khác không hỗ trợ `INSTANT` trong cùng một câu `ALTER`.
- Nếu cột mới làm kích thước dòng tối đa vượt giới hạn, MySQL báo lỗi 4092 và gợi ý `INPLACE/COPY`.
- Không xoá được bằng `INSTANT` một cột đang có *functional index*.

**Đổi kiểu cột luôn là COPY**, kể cả nới `INT` lên `BIGINT`. Đây là lý do [chương 03](03-kieu-du-lieu.md)
khuyên chọn `BIGINT` cho khoá chính ngay từ đầu: đổi sau này trên bảng lớn là cả một dự án (mục 5.4).

**Một ngoại lệ nhẹ về charset**: tài liệu `ALTER TABLE` liệt kê việc đổi charset của **một cột** từ
`utf8mb3` sang `utf8mb4` là thao tác chỉ sửa metadata, với điều kiện cột là `CHAR`, `VARCHAR`, `TEXT`
hoặc `ENUM` và cột **không có index**. Còn `CONVERT TO CHARACTER SET` cho cả bảng thì dựng lại bảng và
chặn ghi.

### 2.5 Biết trước khi chạy

Ba thói quen để không bị bất ngờ:

1. **Luôn ghi `ALGORITHM` (và `LOCK` với INPLACE) trong migration chạy trên production.** Như mục 2.1:
   sai thì lỗi ngay, không khoá bảng.
2. **Đọc số "rows affected".** Tài liệu MySQL gợi ý: thao tác chỉ sửa metadata hoặc dựng index báo
   `0 rows affected`; thao tác copy dữ liệu báo số dòng khác 0. Trước khi chạy trên bảng lớn, hãy thử
   trên một bản sao nhỏ:

   ```sql
   CREATE TABLE orders_try LIKE orders;          -- cùng cấu trúc, rỗng
   INSERT INTO orders_try SELECT * FROM orders;  -- một ít dữ liệu
   ALTER TABLE orders_try MODIFY amount BIGINT NOT NULL;
   -- Query OK, 5 rows affected  (output minh hoạ) → khác 0: copy dữ liệu, cần kế hoạch riêng
   DROP TABLE orders_try;
   ```

3. **Đo trên dữ liệu đủ lớn.** Bảng 5 dòng không cho thấy gì về thời gian. Muốn cảm nhận, nhân bảng
   lên bằng cách tự chèn lại chính nó nhiều lần (mỗi lần gấp đôi):

   ```sql
   CREATE TABLE big_orders LIKE orders;
   INSERT INTO big_orders (user_id, amount, status) SELECT user_id, amount, status FROM orders;
   -- chạy câu dưới 16 lần: 5 × 2^16 = 327.680 dòng
   INSERT INTO big_orders (user_id, amount, status) SELECT user_id, amount, status FROM big_orders;

   ALTER TABLE big_orders ADD COLUMN x INT NULL, ALGORITHM=INSTANT;          -- gần như tức thì
   ALTER TABLE big_orders ADD INDEX idx_status (status), ALGORITHM=INPLACE, LOCK=NONE;  -- vài giây
   ALTER TABLE big_orders MODIFY amount BIGINT NOT NULL, ALGORITHM=COPY;     -- lâu nhất, chặn ghi
   ```

   So sánh thời gian ba câu (in sau mỗi câu trong `mysql` client) là bài học trực quan nhất của chương.

Khi một `ALTER` dài đang chạy, có thể theo dõi tiến độ qua Performance Schema (theo trang "Monitoring
ALTER TABLE Progress for InnoDB Tables Using Performance Schema"): bật instrument và consumer một lần,
rồi xem `WORK_COMPLETED` so với `WORK_ESTIMATED`:

```sql
UPDATE performance_schema.setup_instruments SET ENABLED = 'YES'
WHERE NAME LIKE 'stage/innodb/alter%';
UPDATE performance_schema.setup_consumers SET ENABLED = 'YES'
WHERE NAME LIKE '%stages%';

-- ở một session khác, trong lúc ALTER đang chạy:
SELECT EVENT_NAME, WORK_COMPLETED, WORK_ESTIMATED
FROM performance_schema.events_stages_current;
```

### 2.6 ALGORITHM và LOCK trong migration Laravel

Laravel 13 có modifier sinh sẵn mệnh đề cho MySQL (theo tài liệu Migrations và mã nguồn
`MySqlGrammar`):

```php
Schema::table('orders', function (Blueprint $table): void {
    // sinh: alter table `orders` add `note` varchar(255) null, algorithm=instant
    $table->string('note')->nullable()->instant();
});

Schema::table('orders', function (Blueprint $table): void {
    // sinh: ... add index ..., algorithm=inplace, lock=none
    $table->index('user_id')->inplace()->lock('none');
});
```

Các điểm cần biết:

- Tài liệu Laravel nói `->instant()` không dùng cùng `->after()`/`->first()` (cột instant chỉ nối vào
  cuối bảng). Thực tế MySQL 8.4 cho `INSTANT` thêm cột ở mọi vị trí (bảng 2.3), và grammar của Laravel
  vẫn sinh `after`; cứ theo tài liệu Laravel cho an toàn, và kiểm tra bằng `--pretend`.
- Tài liệu Laravel có ví dụ `->instant()->lock('none')`, nhưng tài liệu MySQL nói với `INSTANT` chỉ
  `LOCK=DEFAULT` được phép. Đừng gộp hai thứ này; chỉ dùng `->lock()` với `->inplace()` hoặc thao tác
  INPLACE.
- `->inplace()` cho khoá ngoại đòi `foreign_key_checks` tắt (đúng như bảng tra ở 2.3).
- Dùng `php artisan migrate --pretend` để đọc câu SQL thật trước khi deploy.
- Thao tác chưa có modifier thì viết thẳng SQL: `DB::statement('ALTER TABLE ... , ALGORITHM=INPLACE, LOCK=NONE')`.

### 2.7 Giới hạn của online DDL

"Online" không có nghĩa là miễn phí. Tài liệu MySQL liệt kê các giới hạn sau cho thao tác INPLACE trên
bảng lớn:

- **Online log có giới hạn.** Thay đổi dữ liệu xảy ra trong lúc `ALTER` chạy được ghi vào một file log
  tạm, tối đa `innodb_online_alter_log_max_size` (mặc định 134217728 byte, tức 128 MB). Bảng bị ghi quá
  nhiều làm log vượt giới hạn thì `ALTER` thất bại với lỗi `DB_ONLINE_LOG_TOO_BIG` và phải chạy lại từ
  đầu. Đặt lớn hơn thì cho phép nhiều DML hơn, nhưng giai đoạn cuối (khoá bảng để áp log) cũng dài hơn.
- **Tốn đĩa.** Thao tác dựng lại bảng có thể cần thêm dung lượng bằng cỡ bảng cộng index (file sort tạm
  trong `tmpdir` hoặc `innodb_tmpdir`, và file bảng trung gian tên bắt đầu bằng `#sql-ib` trong cùng thư
  mục với bảng). Hết đĩa thì `ALTER` thất bại.
- **Không tạm dừng, không điều tốc được.** Đã chạy là chạy hết, ăn I/O và CPU của server. Huỷ giữa
  chừng thì rollback cũng có thể tốn kém.
- **Lỗi có thể chỉ xuất hiện ở cuối.** Ví dụ đang tạo unique index mà ứng dụng chèn giá trị trùng, hoặc
  khi áp online log gặp lỗi trùng khoá tạm thời (`ERROR 1062 Duplicate entry`), thì `ALTER` bị huỷ sau
  khi đã chạy hàng giờ.
- ⚠️ **Replica lag.** Đây là giới hạn hay bị quên nhất. Câu DDL chỉ được chạy trên replica **sau khi**
  chạy xong trên primary, và các DML đã chạy song song trên primary chỉ được áp trên replica **sau khi**
  DDL trên replica xong. Một `ALTER` mất 2 giờ trên primary nghĩa là replica chạy lại nó thêm khoảng 2
  giờ, và trong lúc đó replica đứng lại ở quá khứ. Nếu ứng dụng đọc từ replica, người dùng thấy dữ liệu
  cũ hàng giờ ([chương 22](22-replication-ha.md)).

Vì giới hạn cuối cùng, trên hệ thống có replica phục vụ đọc, kể cả thao tác INPLACE trên bảng lớn
thường cũng được chạy bằng công cụ bên ngoài (mục 4). Nhưng trước hết, có một vấn đề còn hay gây sự cố
hơn: metadata lock.

## 3. Metadata lock và lock_wait_timeout

### 3.1 Metadata lock là gì

Giả sử một transaction đang đọc bảng `orders` theo từng bước, và giữa hai bước có người xoá cột
`amount`. Bước thứ hai sẽ gặp một bảng có cấu trúc khác bước thứ nhất. Để tránh chuyện đó, MySQL có
*metadata lock* (MDL): lock của tầng server (không phải của InnoDB) đặt trên **định nghĩa** của đối
tượng (bảng, view, stored procedure...), không phải trên dữ liệu.

Quy tắc, theo trang "Metadata Locking" của tài liệu MySQL 8.4:

- Mọi câu lệnh dùng tới bảng, **kể cả `SELECT` thường**, lấy một MDL dạng *shared* trên bảng đó.
- MDL được giữ **tới hết transaction**, không phải tới hết câu lệnh. Ở chế độ autocommit, mỗi câu là
  một transaction nên lock được nhả ngay sau câu đó. Nhưng trong `START TRANSACTION ... COMMIT`, lock
  được giữ tới `COMMIT`/`ROLLBACK`.
- DDL (`ALTER`, `DROP`, `RENAME`, `TRUNCATE`...) cần MDL *exclusive*, xung đột với mọi MDL shared.
- Khi nhiều yêu cầu cùng chờ một lock, **yêu cầu ghi (exclusive) được ưu tiên hơn yêu cầu đọc**. Một
  yêu cầu exclusive đang chờ sẽ khiến các yêu cầu shared đến sau nó phải xếp hàng sau nó. (Có ngoại lệ
  liên quan tới `max_write_lock_count`, nhưng giá trị mặc định của biến này rất lớn nên thực tế không
  xảy ra.)

Phân biệt với lock dòng của InnoDB ([chương 15](15-lock-deadlock.md)): lock dòng bảo vệ **dữ liệu** và
có timeout riêng là `innodb_lock_wait_timeout`; MDL bảo vệ **cấu trúc** và có timeout là
`lock_wait_timeout`. Hai biến khác nhau, dễ nhầm.

### 3.2 Ba pha của một câu ALTER online

Trang "Online DDL Performance and Concurrency" chia một thao tác online DDL thành ba pha:

```
Pha 1. Initialization   Lấy MDL "shared upgradable": vẫn cho mọi người đọc/ghi.
                        Server quyết định algorithm và mức đồng thời.
Pha 2. Execution        Có thể nâng lên MDL exclusive RẤT NGẮN lúc chuẩn bị (tuỳ thao tác).
                        Rồi dựng index / rebuild trong khi DML chạy song song.
Pha 3. Commit           Nâng lên MDL exclusive để thay định nghĩa bảng cũ bằng mới.
                        Khi đã lấy được, chỉ giữ rất ngắn.
```

Với `INSTANT`, tài liệu nói MDL exclusive có thể được lấy ngắn trong pha execution. Tóm lại: **mọi
câu `ALTER`, kể cả `INSTANT`, đều cần MDL exclusive ít nhất một khoảnh khắc.** Muốn lấy được nó, câu
`ALTER` phải chờ mọi transaction đang giữ MDL shared trên bảng kết thúc.

### 3.3 Sự cố kinh điển: ALTER vài mili giây làm cả ứng dụng treo

Ghép các quy tắc ở 3.1 và 3.2 lại, ta có kịch bản sau (tài liệu MySQL mô tả đúng kịch bản này). Bạn có
thể tái hiện bằng ba cửa sổ `mysql` client trên `lab20`:

| Bước | Session A | Session B (migration) | Session C (ứng dụng) | Kết quả |
|---|---|---|---|---|
| 1 | `START TRANSACTION;`<br>`SELECT * FROM users WHERE id = 1;` | | | A giữ MDL shared trên `users`, rồi không commit (ví dụ một console bỏ quên, một job báo cáo dài) |
| 2 | | `ALTER TABLE users ADD COLUMN nickname VARCHAR(30) NULL, ALGORITHM=INSTANT;` | | B xin MDL exclusive, phải chờ A. Trạng thái `Waiting for table metadata lock` |
| 3 | | | `SELECT * FROM users WHERE id = 2;` | C xin MDL shared, nhưng phải **xếp hàng sau B** vì B là yêu cầu exclusive đang chờ. C treo |
| 4 | | | (mọi request mới tới `users`) | Tất cả treo sau B. Connection pool cạn, PHP-FPM hết worker, health check fail: ứng dụng "sập" |
| 5 | `COMMIT;` | | | A nhả MDL |
| 6 | | `ALTER` chạy xong trong mili giây | | |
| 7 | | | các câu đang chờ chạy tiếp | Ứng dụng hồi lại |

Điểm then chốt: `ALTER` chưa làm gì nặng cả. Thủ phạm là **hàng đợi MDL**: một transaction cũ chặn
`ALTER`, và `ALTER` đang chờ chặn mọi người đến sau. Vì thế:

- Dù thao tác là `INSTANT`, sự cố vẫn xảy ra.
- Chạy migration lúc nửa đêm không chữa được nếu đúng lúc đó có một job dài đang mở transaction.
- Thủ phạm (session A) thường **không hiện câu lệnh nào** trong processlist: nó đang rảnh giữa
  transaction, `Command = Sleep`.

### 3.4 Tìm thủ phạm

```sql
-- 1. Thấy nhiều dòng State = 'Waiting for table metadata lock'
SHOW FULL PROCESSLIST;

-- 2. Ai đang giữ (GRANTED), ai đang chờ (PENDING) MDL trên bảng users
SELECT OBJECT_NAME, LOCK_TYPE, LOCK_DURATION, LOCK_STATUS, OWNER_THREAD_ID
FROM performance_schema.metadata_locks
WHERE OBJECT_SCHEMA = 'lab20' AND OBJECT_NAME = 'users';

-- 3. View gom sẵn của sys schema: ai chặn ai, kèm câu KILL gợi ý
SELECT * FROM sys.schema_table_lock_waits\G

-- 4. Transaction mở lâu (thủ phạm hay gặp nhất)
SELECT trx_id, trx_started, trx_mysql_thread_id, trx_query
FROM information_schema.innodb_trx
ORDER BY trx_started;
```

Ở bước 4, cột `trx_mysql_thread_id` là id hiện trong `SHOW PROCESSLIST`, dùng được cho `KILL <id>;`
nếu bạn chắc transaction đó có thể huỷ.

### 3.5 Phòng: lock_wait_timeout ngắn và thử lại

`lock_wait_timeout` là số giây tối đa một câu lệnh chờ để lấy MDL. **Mặc định 31536000 giây, tức một
năm**. Không đặt gì thì `ALTER` chờ gần như vô hạn, và cả ứng dụng chờ theo.

Cách phòng chuẩn là đặt nó ngắn **cho riêng session chạy migration**:

```sql
SET SESSION lock_wait_timeout = 5;
ALTER TABLE users ADD COLUMN nickname VARCHAR(30) NULL, ALGORITHM=INSTANT;
-- Nếu sau 5 giây chưa lấy được MDL: lỗi ER_LOCK_WAIT_TIMEOUT (1205),
-- ALTER rời hàng đợi, các query của ứng dụng đang xếp sau nó được chạy tiếp.
```

Ứng dụng chỉ bị chậm tối đa 5 giây thay vì treo vô hạn. Đổi lại migration có thể thất bại, nên cần
thử lại vài lần có nghỉ. Lưu ý từ tài liệu: timeout áp dụng **cho từng lần** lấy lock, một câu lệnh cần
nhiều lock có thể chờ lâu hơn tổng con số này.

Trong Laravel:

```php
<?php
declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\QueryException;
use Illuminate\Support\Facades\DB;

return new class extends Migration
{
    public function up(): void
    {
        DB::statement('SET SESSION lock_wait_timeout = 5');

        $attempts = 0;
        while (true) {
            try {
                DB::statement(
                    'ALTER TABLE users ADD COLUMN nickname VARCHAR(30) NULL, ALGORITHM=INSTANT'
                );
                return;
            } catch (QueryException $e) {
                $attempts++;
                // 1205 = lock wait timeout. Lỗi khác thì ném ra ngay.
                if (($e->errorInfo[1] ?? null) !== 1205 || $attempts >= 5) {
                    throw $e;
                }
                sleep(10);  // nghỉ cho transaction dài có cơ hội kết thúc
            }
        }
    }

    public function down(): void
    {
        DB::statement('ALTER TABLE users DROP COLUMN nickname, ALGORITHM=INSTANT');
    }
};
```

⚠️ `SET SESSION` có hiệu lực cho cả phần còn lại của connection đó. Trong `php artisan migrate`, mọi
migration sau dùng chung connection nên cũng nhận timeout 5 giây, thường là điều bạn muốn.

Ngoài timeout, ba thói quen khác:

1. Trước khi migrate, kiểm tra `information_schema.innodb_trx` xem có transaction nào mở quá vài phút,
   xử lý chúng trước.
2. Ở tầng ứng dụng, không để transaction mở lâu: không gọi API bên ngoài trong transaction, đặt
   timeout cho job báo cáo, không mở transaction rồi bỏ đó trong console production
   ([chương 19](19-database-tu-ung-dung.md)).
3. Các công cụ ở mục 4 cũng cần MDL exclusive ở bước cuối (và pt-online-schema-change cả ở bước tạo
   trigger), nên vấn đề này không biến mất khi dùng công cụ.

## 4. Công cụ đổi schema online: pt-online-schema-change và gh-ost

### 4.1 Ý tưởng chung: tự copy bảng, từng khúc nhỏ

Với thao tác phải `COPY` (đổi kiểu cột), hoặc thao tác `INPLACE` dài trên hệ thống có replica, ta cần
một cách đổi schema mà: không chặn ghi, tạm dừng được khi server quá tải, và không làm replica trễ hàng
giờ. Hai công cụ phổ biến cho MySQL làm cùng một ý tưởng:

```
1. Tạo bảng "bóng" rỗng có cấu trúc MỚI:            _orders_new
2. Copy dữ liệu cũ sang theo từng khúc nhỏ (vài nghìn dòng / khúc), có nghỉ, có điều tốc
3. Trong lúc copy, mọi thay đổi mới trên orders cũng được đồng bộ sang bảng bóng
4. Khi bảng bóng bắt kịp: đổi tên nguyên tử
       RENAME TABLE orders TO _orders_old, _orders_new TO orders
5. Giữ hoặc xoá bảng cũ
```

Mỗi khúc là một transaction ngắn, nên lock ít, binlog nhỏ, replica áp nhanh. Điểm khác nhau giữa hai
công cụ nằm ở bước 3: đồng bộ thay đổi mới bằng cách nào.

### 4.2 pt-online-schema-change: dùng trigger

`pt-online-schema-change` (gọi tắt pt-osc) thuộc Percona Toolkit. Theo tài liệu của nó:

1. Tạo bảng mới rỗng, chạy `ALTER` lên bảng mới (rỗng nên tức thì).
2. Tạo trigger trên bảng gốc cho `INSERT`, `UPDATE`, `DELETE`: mỗi khi ứng dụng ghi vào bảng gốc,
   trigger ghi tương ứng vào bảng mới, **trong cùng transaction** với câu lệnh của ứng dụng.
3. Copy dữ liệu cũ theo khúc. Kích thước khúc tự điều chỉnh để mỗi khúc chạy khoảng `--chunk-time`
   giây (mặc định 0.5). Sau mỗi khúc, công cụ:
   - tạm dừng nếu replica trễ hơn `--max-lag` (mặc định 1s);
   - tạm dừng nếu biến trạng thái vượt `--max-load` (mặc định `Threads_running=25`);
   - **huỷ** nếu vượt `--critical-load` (mặc định `Threads_running=50`).
4. `RENAME TABLE` nguyên tử để tráo hai bảng, rồi mặc định xoá bảng cũ (`--[no]drop-old-table`).

Ví dụ (chạy ở terminal của máy có Percona Toolkit và quyền vào MySQL):

```sh
pt-online-schema-change \
  --alter "MODIFY amount BIGINT NOT NULL" \
  D=shop,t=orders \
  --max-lag 2 --max-load Threads_running=25 --critical-load Threads_running=50 \
  --dry-run          # tạo và ALTER bảng mới, không tạo trigger, không copy, không tráo
# Đọc kỹ output, rồi thay --dry-run bằng --execute để chạy thật.
# Không có --execute thì công cụ chỉ kiểm tra an toàn rồi thoát.
```

Các yêu cầu và điểm cần nhớ:

- Gần như luôn cần bảng có `PRIMARY KEY` hoặc `UNIQUE` index để chia khúc.
- Bảng đã có trigger riêng: mặc định công cụ không chạy; bản mới có `--preserve-triggers`.
- Khoá ngoại là phần khó nhất. Sau khi tráo tên, các bảng con vẫn trỏ vào bảng cũ, nên phải chọn
  `--alter-foreign-keys-method`: `rebuild_constraints` (`ALTER` bảng con để trỏ lại, an toàn nhưng chậm
  nếu bảng con lớn), `drop_swap` (tắt kiểm tra khoá ngoại, xoá bảng gốc rồi đổi tên bảng mới: có một
  khoảnh khắc bảng không tồn tại và nếu đổi tên lỗi thì không quay lại được), hoặc `auto` để công cụ
  tự chọn.
- Công cụ tự đặt `lock_wait_timeout=60` và `innodb_lock_wait_timeout=1` cho session của nó (đổi bằng
  `--set-vars`) và thử lại khi gặp lock wait timeout. Tạo trigger và tráo bảng đều cần MDL exclusive,
  nên transaction dài vẫn là mối nguy.

Nhược điểm cố hữu của trigger: mỗi câu ghi của ứng dụng phải chạy thêm trigger trong chính transaction
của nó, nên ứng dụng chậm hơn trong suốt thời gian migration; và khi "tạm dừng", công cụ chỉ dừng được
phần copy, còn trigger vẫn phải chạy.

### 4.3 gh-ost: đọc binlog thay cho trigger

`gh-ost` do GitHub viết, không dùng trigger (*triggerless*). Nó giả làm một replica: kết nối vào MySQL,
đọc luồng *binlog* ở dạng `ROW` (mỗi dòng bị thay đổi là một event) và lọc ra các event của bảng đang
migrate. Các bước:

1. **Chuẩn bị.** Tạo bảng ghost `_orders_gho` giống `orders` rồi `ALTER` nó (rỗng nên tức thì), và một
   bảng changelog `_orders_ghc` để ghi trạng thái và heartbeat. Chọn một khoá duy nhất chung của hai
   bảng (thường là PK) để chia khúc.
2. **Copy và áp binlog song song.** Copy từng khúc theo khoá (mặc định `--chunk-size 1000` dòng, cho
   phép 10 tới 100000) bằng `INSERT IGNORE ... SELECT`, đồng thời áp các event binlog của `orders` lên
   bảng ghost. Copy dùng `INSERT IGNORE` nên không đè dòng mà binlog đã áp; event `INSERT` của binlog
   được áp bằng `REPLACE INTO`, event `UPDATE`/`DELETE` áp bằng câu tương ứng, nên binlog luôn đè bản
   copy cũ hơn. Kết quả cuối mỗi dòng là trạng thái mới nhất.
3. **Điều tốc** (*throttle*). Khi replica trễ quá `--max-lag-millis` (gh-ost tự đo lag bằng heartbeat
   ghi vào bảng changelog), hoặc tải vượt `--max-load`, gh-ost dừng **cả** copy lẫn áp binlog: primary
   không phải làm thêm gì cho migration. Vượt `--critical-load` thì huỷ.
4. **Hoãn cut-over.** Với `--postpone-cut-over-flag-file`, copy xong gh-ost vẫn áp binlog để bảng ghost
   luôn bắt kịp, nhưng không tráo bảng cho tới khi bạn xoá file đó. Bước rủi ro nhất xảy ra lúc bạn
   đang ngồi theo dõi.
5. **Cut-over.** Tráo bảng gốc và bảng ghost bằng một chuỗi `LOCK TABLES` và `RENAME` được thiết kế để
   nếu có sự cố giữa chừng thì bảng gốc vẫn nguyên vẹn. Thời gian giữ lock tối đa
   `--cut-over-lock-timeout-seconds` (mặc định 3), quá thì bỏ và thử lại sau. Ứng dụng chỉ bị chặn ghi
   vài giây.

```sh
# Chạy ở terminal của máy có gh-ost. Mặc định gh-ost kết nối vào replica để đọc binlog
# và tự tìm ra primary để ghi.
gh-ost --host=replica-1 --database=shop --table=orders \
  --alter="MODIFY amount BIGINT NOT NULL" \
  --max-lag-millis=1500 --max-load=Threads_running=25 --critical-load=Threads_running=200 \
  --postpone-cut-over-flag-file=/tmp/ghost.postpone \
  --assume-rbr --execute
# Bỏ --execute là chạy thử (noop), không đụng dữ liệu.
```

Khi đang chạy, gh-ost cho điều khiển qua unix socket (lệnh `status`, `throttle`, đổi `chunk-size`...),
xem tài liệu "interactive commands" của gh-ost.

Yêu cầu và giới hạn (theo tài liệu "Requirements and limitations"): cần binlog dạng `ROW` với row image
`FULL` (mặc định của MySQL 8.4); **không hỗ trợ khoá ngoại và trigger** trên bảng migrate (bản gh-ost
mới có thêm cờ `--include-triggers` để tạo lại trigger trên bảng mới; đọc tài liệu flag trước khi dựa vào
nó); hai bảng phải chung một `PRIMARY KEY` hoặc `UNIQUE KEY` không chứa NULL.

### 4.4 So sánh và cách chọn

| | Online DDL (INPLACE) | pt-online-schema-change | gh-ost |
|---|---|---|---|
| Đồng bộ thay đổi mới | Online log trong InnoDB | Trigger, trong transaction của ứng dụng | Đọc binlog, bất đồng bộ |
| Tạm dừng, điều tốc | Không | Chỉ dừng được phần copy | Dừng hẳn, đổi tham số khi đang chạy |
| Replica lag | Trễ bằng cả thời gian `ALTER` | Theo khúc, điều tốc theo lag | Theo khúc, điều tốc theo lag |
| Khoá ngoại | Được | Được, cần chọn cách xử lý | Không |
| Dung lượng đĩa thêm | Có nếu dựng lại bảng | Khoảng một bản sao bảng | Khoảng một bản sao bảng |
| Cần MDL exclusive | Đầu/cuối thao tác | Tạo/xoá trigger, tráo bảng | Cut-over |

Quy trình quyết định cho một thay đổi trên bảng lớn:

```
Tra bảng ở 2.3
 ├─ Có INSTANT?              → chạy trực tiếp, ALGORITHM=INSTANT + lock_wait_timeout ngắn
 ├─ INPLACE + LOCK=NONE, không dựng lại bảng, nhanh (vd. xoá index)?
 │                           → chạy trực tiếp
 ├─ INPLACE nhưng dài (dựng index, rebuild) trên bảng lớn có replica phục vụ đọc?
 │                           → gh-ost (hoặc pt-osc nếu có khoá ngoại)
 └─ Chỉ COPY?                → gh-ost / pt-osc, hoặc né bằng expand/contract (mục 5)
```

Nếu database chạy trên cloud (Amazon RDS, Google Cloud SQL, Azure...), tài liệu gh-ost có ghi chú và
flag riêng cho từng nền tảng; đọc chúng trước khi chạy.

## 5. Expand/contract: đổi schema mà code cũ và code mới cùng chạy được

### 5.1 Vấn đề không nằm ở database

Giả sử bạn muốn đổi tên cột `users.name` thành `users.full_name`. Tra bảng ở 2.3: đổi tên cột là
`INSTANT`. Vậy chỉ cần một migration:

```sql
ALTER TABLE users RENAME COLUMN name TO full_name, ALGORITHM=INSTANT;
```

Database xong trong mili giây. Nhưng hãy nhìn quá trình deploy thật: ứng dụng chạy trên nhiều server
(hoặc nhiều container), deploy lần lượt từng cái (*rolling deploy*), và migration chạy ở một thời điểm
nào đó trong quá trình đó:

```
thời gian ─────────────────────────────────────────────────────────►
server 1:  [code cũ: đọc/ghi "name"]──┐ deploy ┌─[code mới: "full_name"]
server 2:  [code cũ: đọc/ghi "name"]───────────┐ deploy ┌─[code mới]
migration:                         ▲ RENAME COLUMN name TO full_name
                                   │
         từ đây tới lúc server 2 deploy xong: mọi request vào server 2 lỗi
         "Unknown column 'name'"
```

Chạy migration trước hay sau deploy đều có một khoảng code và schema không khớp: chạy trước thì code
cũ lỗi, chạy sau thì code mới lỗi. Schema đổi nhanh không cứu được bạn khỏi lỗi **tương thích**. Ngoài
ra còn job trong queue được tạo bởi code cũ, cron, script báo cáo, service khác đọc chung database.

### 5.2 Ba pha: expand, migrate, contract

Kỹ thuật *expand/contract* (Martin Fowler gọi là *parallel change*) chia một thay đổi không tương thích
thành các bước, mỗi bước đều **tương thích với cả code trước và sau nó**:

1. **Expand** (mở rộng): thêm cái mới bên cạnh cái cũ. Cả hai cùng tồn tại.
2. **Migrate** (chuyển): chuyển dần mọi nơi dùng sang cái mới: code ghi, dữ liệu cũ, code đọc.
3. **Contract** (thu gọn): xoá cái cũ khi chắc chắn không còn ai dùng.

Nguyên tắc vận hành:

- **Mỗi bước là một lần deploy riêng**, và chỉ sang bước sau khi bước trước đã chạy ổn trên mọi server.
- Migration schema (thêm cột) và thay đổi code (ghi cột) tách ra, để mỗi lần deploy chỉ có một thứ
  thay đổi.
- Mỗi bước có cách lùi (rollback) rõ ràng. Bước xoá dữ liệu luôn đi cuối, và chỉ chạy khi chắc không
  cần lùi nữa.

Cái giá, như Fowler lưu ý: trong suốt quá trình có hai phiên bản cùng tồn tại, dễ nhầm; và nếu thiếu kỷ
luật làm nốt pha contract, hệ thống còn rối hơn lúc đầu (hai cột cùng nghĩa sống mãi).

### 5.3 Ví dụ: đổi tên users.name thành full_name, từng bước

Bối cảnh: bảng `users` lớn, đang nhận ghi liên tục, ứng dụng Laravel chạy trên nhiều server.

**Bước 1. Expand schema** (migration riêng, deploy trước mọi thay đổi code):

```php
<?php
declare(strict_types=1);

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        DB::statement('SET SESSION lock_wait_timeout = 5');

        Schema::table('users', function (Blueprint $table): void {
            // nullable: dòng cũ chưa có dữ liệu. instant(): thêm ", algorithm=instant"
            $table->string('full_name', 50)->nullable()->instant();
        });
    }

    public function down(): void
    {
        Schema::table('users', function (Blueprint $table): void {
            $table->dropColumn('full_name');
        });
    }
};
```

Code cũ không biết cột mới nên không bị ảnh hưởng. Lùi: xoá cột, không mất gì.

**Bước 2. Deploy code ghi cả hai cột, vẫn đọc cột cũ:**

```php
<?php
declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

final class User extends Model
{
    protected static function booted(): void
    {
        // Mọi lần save qua Eloquent đều ghi cả hai cột.
        static::saving(function (User $user): void {
            if ($user->isDirty('name')) {
                $user->full_name = $user->name;
            }
        });
    }
}
```

⚠️ Hook của Eloquent không chạy với `DB::table('users')->update(...)`, `User::query()->update(...)` hay
SQL viết tay (import, job hàng loạt). Phải tìm toàn bộ codebase những chỗ ghi `name` và sửa cả chúng.
Lùi: deploy lại code cũ, cột mới chỉ ngừng được cập nhật.

**Bước 3. Backfill**: sao `name` sang `full_name` cho các dòng cũ, theo batch (cách làm chi tiết ở mục
6). Xong thì kiểm tra:

```sql
SELECT COUNT(*) FROM users WHERE full_name IS NULL;                 -- phải là 0
SELECT COUNT(*) FROM users WHERE full_name <> name;                 -- phải là 0
```

**Bước 4. Deploy code đọc cột mới**, vẫn ghi cả hai. Có lỗi thì quay về code bước 2, vì cột cũ vẫn đầy
đủ và đúng.

**Bước 5. Deploy code chỉ dùng `full_name`**, bỏ `name` khỏi model, `$fillable`, query, validation.
Trước bước này, phải bảo đảm `INSERT` không ghi `name` vẫn thành công. Cột `name` đang `NOT NULL` và
không có default, nên với strict mode, `INSERT` thiếu nó sẽ lỗi (`Field 'name' doesn't have a default
value`). Cách rẻ nhất là cho nó một default, thao tác `INSTANT`:

```sql
ALTER TABLE users ALTER COLUMN name SET DEFAULT '', ALGORITHM=INSTANT;
```

(Đổi `name` thành nullable cũng được, nhưng đó là `INPLACE` có dựng lại bảng.) Từ bước này lùi về bước
4 không còn hoàn toàn an toàn: các dòng mới có `name` rỗng.

**Bước 6. Contract schema**, sau vài ngày chạy ổn:

```sql
SET SESSION lock_wait_timeout = 5;
-- Xoá cột cũ: INSTANT
ALTER TABLE users DROP COLUMN name, ALGORITHM=INSTANT;
-- Đặt NOT NULL cho cột mới: INPLACE, có dựng lại bảng.
-- Bảng nhỏ chạy trực tiếp; bảng lớn có replica thì dùng gh-ost với --alter="MODIFY full_name VARCHAR(50) NOT NULL"
ALTER TABLE users MODIFY full_name VARCHAR(50) NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
```

Tóm tắt dưới dạng bảng:

| Bước | Deploy gì | Schema sau bước | Code đọc | Code ghi | Lùi được không |
|---|---|---|---|---|---|
| 1 | Migration thêm cột | `name`, `full_name` (NULL) | `name` | `name` | Có, xoá cột |
| 2 | Code | như trên | `name` | cả hai | Có |
| 3 | Lệnh backfill | `full_name` đầy đủ | `name` | cả hai | Có |
| 4 | Code | như trên | `full_name` | cả hai | Có, về bước 2 |
| 5 | Migration default + code | `name` có default `''` | `full_name` | `full_name` | Có rủi ro: dòng mới thiếu `name` |
| 6 | Migration | chỉ `full_name` NOT NULL | `full_name` | `full_name` | Không (dữ liệu cột cũ đã mất) |

### 5.4 Cùng kỹ thuật cho đổi kiểu cột

Đổi `orders.amount` từ `INT` sang `BIGINT` là `COPY` (khoá ghi). Ngoài cách chạy gh-ost trên chính cột
đó, có thể làm expand/contract: thêm `amount_minor BIGINT NULL` (INSTANT), ghi cả hai, backfill, chuyển
đọc, ngừng ghi cột cũ, xoá cột cũ. Không có bước nào khoá ghi lâu.

⚠️ Trong lúc các bước chạy (có thể nhiều ngày), code vẫn ghi vào cột `INT` cũ, nên giá trị vượt
2.147.483.647 vẫn chưa ghi được. Kế hoạch phải bắt đầu khi còn cách ngưỡng xa, không phải khi đã chạm
ngưỡng.

### 5.5 Các bẫy khác của expand/contract

- ⚠️ Xoá cột khi còn code đọc hoặc ghi nó: lỗi ngay trong lúc deploy. Có ORM cache danh sách cột lúc
  khởi động (ví dụ ActiveRecord của Rails phải khai báo bỏ qua cột trước khi xoá). Eloquent của Laravel
  không bắt khai báo danh sách cột như vậy (đọc bằng `select *`), nhưng code tham chiếu tên cột trực tiếp
  (`$fillable`, query, validation) thì vẫn lỗi.
- ⚠️ Migration huỷ dữ liệu (`dropColumn`, `drop`) nên ở một lần deploy riêng, sau khi đã chắc không cần
  lùi, và có backup ([chương 21](21-backup-restore.md)).
- ⚠️ Với Laravel, `->change()` phải ghi lại **mọi** modifier muốn giữ (`nullable`, `default`,
  `unsigned`, `comment`), thiếu cái nào mất cái đó (tài liệu Laravel nói rõ điều này). Và `->change()`
  đổi kiểu cột thì vẫn là `COPY`.
- Tên cột cũ còn sống ngoài database: dữ liệu trong cache, job đã nằm trong queue, API response mà
  client đang dựa vào. Rà cả những nơi đó trước bước contract.

## 6. Backfill dữ liệu theo batch

### 6.1 Vì sao không chạy một câu UPDATE cho cả bảng

*Backfill* là điền dữ liệu cho các dòng **đã có** sau khi thêm cột mới (bước 3 của mục 5.3). Cách ngây
thơ:

```sql
UPDATE users SET full_name = name WHERE full_name IS NULL;
```

Trên bảng vài chục triệu dòng, câu này là một transaction khổng lồ:

- **Lock**: InnoDB giữ lock trên mọi dòng đã sửa tới khi câu lệnh commit. Request nào của ứng dụng
  muốn sửa một user trong lúc đó đều phải chờ, có thể tới `innodb_lock_wait_timeout` rồi lỗi.
- **Undo log**: InnoDB phải giữ bản cũ của mọi dòng để có thể rollback. Câu lệnh lỗi ở dòng cuối thì
  rollback toàn bộ, và rollback cũng lâu cỡ thời gian đã chạy ([chương 16](16-ben-trong-innodb.md)).
- **Replica lag**: với binlog dạng `ROW`, cả transaction được ghi vào binlog khi commit, và replica phải
  áp toàn bộ nó. Replica trễ đúng bằng khoảng thời gian áp transaction khổng lồ đó.
- **Không dừng được**: muốn dừng giữa chừng thì phải kill, và kill thì rollback.

Giải pháp: chia thành nhiều câu `UPDATE` nhỏ, mỗi câu một transaction ngắn, có nghỉ giữa các câu.

### 6.2 Chia batch theo khoảng khoá chính

Cách đầu tiên người mới hay nghĩ tới là lặp một câu `UPDATE ... LIMIT` cho tới khi không còn dòng nào:

```sql
-- Chạy được, nhưng chậm dần: lặp lại tới khi "0 rows affected"
UPDATE users SET full_name = name WHERE full_name IS NULL LIMIT 1000;
```

Cột `full_name` không có index, nên mỗi lần chạy MySQL phải quét bảng từ đầu, bỏ qua mọi dòng đã điền
rồi mới tìm thấy 1000 dòng còn `NULL`. Batch càng về sau càng phải quét nhiều, và vì quét qua nhiều
dòng nên cũng khoá nhiều hơn cần thiết ([chương 15](15-lock-deadlock.md): InnoDB khoá các entry index
đã quét). Còn phân trang kiểu `LIMIT ... OFFSET` (khi đọc lên PHP để xử lý) thì vừa chậm dần vừa có thể
bỏ sót hoặc trùng dòng khi dữ liệu thay đổi trong lúc chạy.

Cách đúng: duyệt theo **khoảng khoá chính** `(from, to]`. Mỗi batch dùng index của PK để nhảy thẳng tới
đoạn cần sửa, chi phí mỗi batch gần như không đổi, và dừng ở đâu thì biết đã làm tới đâu để chạy tiếp.

Script dưới đây chạy được ngay, không cần MySQL (mặc định dùng SQLite trong bộ nhớ chỉ để bạn thấy
vòng lặp; SQLite không phải bằng chứng cho hành vi lock của MySQL). Với MySQL `lab20` ở mục 1.5, cần
thêm cột `full_name` trước (`ALTER TABLE users ADD COLUMN full_name VARCHAR(50) NULL, ALGORITHM=INSTANT;`)
rồi truyền DSN như dòng chú thích:

```php
<?php
declare(strict_types=1);

// backfill.php: sao users.name sang users.full_name theo batch.
// Chạy thử không cần MySQL:  php backfill.php            (dùng SQLite trong bộ nhớ, tự tạo dữ liệu)
// Chạy với MySQL lab20:       DSN='mysql:host=<host>;dbname=lab20' DB_USER=root DB_PASS=root php backfill.php

function backfill(PDO $pdo, int $batchSize, int $pauseMicros): int
{
    $maxId = (int) $pdo->query('SELECT COALESCE(MAX(id), 0) FROM users')->fetchColumn();
    $update = $pdo->prepare(
        'UPDATE users SET full_name = name
         WHERE id > :from AND id <= :to AND full_name IS NULL'
    );

    $total = 0;
    for ($from = 0; $from < $maxId; $from += $batchSize) {
        // Mỗi batch là một câu UPDATE ngắn (autocommit): lock ít dòng, transaction ngắn.
        $update->execute(['from' => $from, 'to' => $from + $batchSize]);
        $total += $update->rowCount();
        echo "batch ({$from}, " . ($from + $batchSize) . "]: {$update->rowCount()} dòng\n";
        usleep($pauseMicros); // nghỉ giữa các batch; thực tế: kiểm tra replica lag ở đây
    }

    return $total;
}

$dsn = getenv('DSN') ?: 'sqlite::memory:';
$pdo = new PDO($dsn, getenv('DB_USER') ?: null, getenv('DB_PASS') ?: null, [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);

if ($dsn === 'sqlite::memory:') {
    $pdo->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, full_name TEXT NULL)');
    $insert = $pdo->prepare('INSERT INTO users (id, name, full_name) VALUES (?, ?, ?)');
    foreach ([1, 2, 3, 5, 8, 9, 10, 12] as $id) {      // id có "lỗ" như dữ liệu thật
        // dòng 9 đã được code mới (bước 2) ghi full_name, backfill không được đè
        $insert->execute([$id, "user{$id}", $id === 9 ? 'Đã có' : null]);
    }
}

$done = backfill($pdo, batchSize: 5, pauseMicros: 100_000);
echo "Tổng cộng: {$done} dòng\n";
echo 'Còn NULL: ' . $pdo->query('SELECT COUNT(*) FROM users WHERE full_name IS NULL')->fetchColumn() . "\n";
echo 'Dòng 9: ' . $pdo->query('SELECT full_name FROM users WHERE id = 9')->fetchColumn() . "\n";
```

Output khi chạy `php backfill.php` (đã chạy thật với PHP 8.5 và 8.4):

```
batch (0, 5]: 4 dòng
batch (5, 10]: 2 dòng
batch (10, 15]: 1 dòng
Tổng cộng: 7 dòng
Còn NULL: 0
Dòng 9: Đã có
```

Đọc kỹ ba chi tiết trong câu `UPDATE`:

1. `id > :from AND id <= :to`: khoảng theo PK, không phụ thuộc id liên tục. Khoảng `(5, 10]` chỉ có 3
   id thật (8, 9, 10) vì id có "lỗ"; không sao cả.
2. `AND full_name IS NULL`: không đè lên dòng mà code mới (bước 2) đã ghi. Dòng 9 giữ giá trị `Đã có`.
   Nhờ điều kiện này, chạy lại script nhiều lần cũng an toàn (*idempotent*).
3. `SET full_name = name`: giá trị lấy ngay trong câu `UPDATE`, không đọc lên PHP rồi ghi xuống. Nếu đọc
   lên rồi mới ghi, giữa hai bước đó ứng dụng có thể đổi `name`, và backfill sẽ ghi một giá trị cũ.

Chọn kích thước batch: đủ nhỏ để mỗi câu chạy trong khoảng vài trăm mili giây trên production (thường
vài trăm tới vài nghìn dòng), đo thực tế rồi chỉnh. Đây cũng chính là ý tưởng `--chunk-time` của
pt-online-schema-change.

### 6.3 Điều tốc theo replica lag

Nghỉ một khoảng cố định chưa đủ: khi primary bận, replica có thể vẫn tụt lại. Cách tốt hơn là sau mỗi
batch, hỏi replica đang trễ bao nhiêu và chỉ chạy tiếp khi trễ dưới ngưỡng:

```php
// Kết nối thẳng vào replica, user cần quyền REPLICATION CLIENT.
function replicaLagSeconds(PDO $replica): ?int
{
    $row = $replica->query('SHOW REPLICA STATUS')->fetch(PDO::FETCH_ASSOC);
    if ($row === false || $row['Seconds_Behind_Source'] === null) {
        return null;   // không phải replica, hoặc replication đang dừng: coi là nguy hiểm
    }
    return (int) $row['Seconds_Behind_Source'];
}

// trong vòng lặp, thay cho usleep():
while (($lag = replicaLagSeconds($replica)) === null || $lag > 2) {
    echo "replica lag = " . var_export($lag, true) . ", tạm dừng\n";
    sleep(1);
}
```

`Seconds_Behind_Source` có độ chính xác hạn chế; hệ thống lớn thường dùng bảng heartbeat (gh-ost tự
làm điều này). Chi tiết ở [chương 22](22-replication-ha.md).

### 6.4 Backfill trong Laravel

Backfill nên là một **artisan command** (hoặc job) riêng, không đặt trong migration: nó có thể chạy
hàng giờ, cần dừng và chạy tiếp được, còn migration chạy trong lúc deploy và nên xong nhanh.

```php
<?php
declare(strict_types=1);

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Illuminate\Support\Facades\DB;

final class BackfillUserFullName extends Command
{
    protected $signature = 'users:backfill-full-name {--batch=1000} {--from=0}';

    public function handle(): int
    {
        $batch = (int) $this->option('batch');
        $from = (int) $this->option('from');            // chạy tiếp từ chỗ đã dừng
        $maxId = (int) DB::table('users')->max('id');

        for (; $from < $maxId; $from += $batch) {
            $n = DB::update(
                'UPDATE users SET full_name = name
                 WHERE id > ? AND id <= ? AND full_name IS NULL',
                [$from, $from + $batch],
            );
            $this->line("({$from}, " . ($from + $batch) . "]: {$n}");
            usleep(100_000);                             // hoặc chờ replica lag như 6.3
        }

        return self::SUCCESS;
    }
}
```

Laravel còn có `chunkById()` và `lazyById()` để duyệt theo PK. Chúng hữu ích khi mỗi dòng cần xử lý
bằng PHP (gọi hàm, tính toán phức tạp); khi phép biến đổi viết được bằng SQL thì một câu `UPDATE` theo
khoảng như trên nhanh hơn nhiều vì không kéo dữ liệu về PHP.

⚠️ `$maxId` lấy một lần ở đầu. Dòng mới chèn sau đó có id lớn hơn nhưng đã được code bước 2 ghi
`full_name`, nên không cần backfill. Đó là lý do phải deploy bước 2 **trước** khi backfill.

## 7. Thêm cột NOT NULL vào bảng lớn

Yêu cầu hay gặp: thêm cột bắt buộc có giá trị, ví dụ `orders.currency` không được để trống. Có hai tình
huống, tuỳ vào giá trị cho các dòng **cũ**.

### 7.1 Mọi dòng cũ nhận cùng một giá trị: NOT NULL DEFAULT, INSTANT

Nếu mọi đơn hàng cũ đều là tiền đồng, chỉ cần:

```sql
SET SESSION lock_wait_timeout = 5;
ALTER TABLE orders ADD COLUMN currency CHAR(3) NOT NULL DEFAULT 'VND', ALGORITHM=INSTANT;

SELECT id, currency FROM orders;   -- mọi dòng cũ: 'VND'
```

Thao tác `INSTANT` không viết lại dòng cũ nào. Giá trị default được lưu trong data dictionary (tài liệu
nhắc tới các cột `INNODB_COLUMNS.DEFAULT_VALUE`, `HAS_DEFAULT` cho cột thêm kiểu instant), và khi đọc một
dòng cũ chưa có cột này, InnoDB trả về giá trị đó. Trong Laravel:
`$table->char('currency', 3)->default('VND')->instant();`.

⚠️ Không ghi `DEFAULT` khi thêm cột `NOT NULL` vào bảng đã có dữ liệu: như [chương 04](04-ddl-constraint.md)
đã nói, MySQL điền giá trị ngầm định của kiểu (`0`, chuỗi rỗng) cho dòng cũ mà không báo gì, còn với
`DATE`/`DATETIME` thì câu lệnh lỗi do SQL mode mặc định. Luôn ghi `DEFAULT` rõ ràng.

⚠️ Default chỉ đúng khi nó thật sự đúng nghiệp vụ cho dòng cũ. Nếu có đơn cũ bằng USD, `DEFAULT 'VND'`
âm thầm làm sai dữ liệu. Khi đó dùng 7.2.

### 7.2 Giá trị cho dòng cũ phải tính từ dữ liệu khác: ba bước

```
1. ADD COLUMN ... NULL                 (INSTANT)            code cũ không bị ảnh hưởng
2. Deploy code ghi cột mới cho mọi dòng mới/sửa
3. Backfill dòng cũ theo batch (mục 6), kiểm tra không còn NULL
4. MODIFY ... NOT NULL                 (INPLACE, dựng lại bảng, LOCK=NONE được)
```

```sql
-- Bước 4: chỉ thành công nếu không còn dòng NULL, và cần strict SQL mode (mặc định đã bật)
SELECT COUNT(*) FROM orders WHERE currency IS NULL;      -- phải là 0
ALTER TABLE orders MODIFY currency CHAR(3) NOT NULL, ALGORITHM=INPLACE, LOCK=NONE;
```

Bước 4 dựng lại bảng, nên trên bảng lớn có replica thì chạy bằng gh-ost (`--alter="MODIFY currency
CHAR(3) NOT NULL"`). Một số team chấp nhận bỏ qua bước 4 và để ràng buộc ở tầng ứng dụng, nhưng khi đó
database không còn bảo vệ dữ liệu; thường đáng để làm cho đủ.

## 8. Thêm index trên bảng lớn

### 8.1 ADD INDEX với INPLACE

Thêm secondary index là `INPLACE`, không dựng lại bảng, cho đọc và ghi đồng thời (bảng 2.3):

```sql
SET SESSION lock_wait_timeout = 5;
ALTER TABLE orders ADD INDEX idx_orders_user_created (user_id, created_at),
  ALGORITHM=INPLACE, LOCK=NONE;
```

Laravel: `$table->index(['user_id', 'created_at'])->inplace()->lock('none');`.

Những gì vẫn xảy ra trên bảng lớn (theo tài liệu online DDL):

- Câu lệnh phải đọc toàn bộ bảng và sắp xếp để dựng cây index: tốn I/O, CPU, và file sort tạm (cần đủ
  chỗ ở `tmpdir`/`innodb_tmpdir`).
- Tài liệu ghi: `CREATE INDEX` chỉ kết thúc sau khi mọi transaction đang truy cập bảng hoàn tất. Đây
  lại là chuyện MDL ở mục 3.
- Ghi đồng thời trong lúc dựng index đi vào online log; ghi quá nhiều thì vượt
  `innodb_online_alter_log_max_size` và thất bại (2.7).
- Replica dựng lại index đó sau khi primary xong, trễ tương ứng (2.7). Vì vậy trên bảng lớn có replica
  phục vụ đọc, thêm index thường cũng chạy bằng gh-ost (`--alter="ADD INDEX idx_orders_user_created
  (user_id, created_at)"`).

### 8.2 Unique index: kiểm tra trùng trước

Thêm `UNIQUE` index thì MySQL phải kiểm tra không có giá trị trùng. Có trùng thì câu lệnh thất bại, có
khi sau khi đã chạy rất lâu. Và nếu ứng dụng chèn giá trị trùng **trong lúc** index đang được dựng, tài
liệu MySQL nói thao tác chỉ thất bại ở cuối, khi áp các thay đổi đồng thời; thay đổi của DML thắng, còn
`ALTER` coi như bị rollback. Vậy nên:

```sql
-- 1. Tìm trùng trước
SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1;
-- 2. Dọn dữ liệu trùng, và sửa code để không sinh thêm trùng
-- 3. Rồi mới thêm unique
ALTER TABLE users ADD UNIQUE INDEX uq_users_phone (phone), ALGORITHM=INPLACE, LOCK=NONE;
```

(Câu cuối là ví dụ mẫu; bảng `users` của `lab20` chỉ có cột `phone` nếu bạn đã chạy migration ở 1.3.)

### 8.3 Xoá index an toàn: cho nó "vô hình" trước

Xoá index chỉ sửa metadata, rất nhanh. Cái nguy là xoá nhầm một index đang được truy vấn quan trọng
dùng, và thêm lại thì mất hàng giờ. MySQL 8 có *invisible index*: index vẫn được duy trì khi ghi,
nhưng optimizer không dùng nó. Đổi visibility là thao tác chỉ sửa metadata.

Trong `lab20`, sau mục 8.1 bảng `orders` có cả `idx_orders_user (user_id)` (thêm ở 2.1) và
`idx_orders_user_created (user_id, created_at)`. Index đầu là thừa: mọi truy vấn lọc theo `user_id` đều
dùng được tiền tố trái của index sau ([chương 11](11-index.md)). Đây là ứng viên xoá điển hình:

```sql
ALTER TABLE orders ALTER INDEX idx_orders_user INVISIBLE;
-- Theo dõi vài ngày: truy vấn nào chậm đi? Có thì bật lại ngay, tức thì:
ALTER TABLE orders ALTER INDEX idx_orders_user VISIBLE;
-- Không có vấn đề gì thì mới xoá:
ALTER TABLE orders DROP INDEX idx_orders_user, ALGORITHM=INPLACE, LOCK=NONE;
```

Primary key không thể đặt invisible. Chi tiết về invisible index ở [chương 11](11-index.md).

### 8.4 Thêm khoá ngoại trên bảng lớn

Bảng 2.3 nói: thêm khoá ngoại chỉ `INPLACE` được khi `foreign_key_checks` tắt, nếu không thì `COPY`
(khoá ghi). Nhưng tắt `foreign_key_checks` nghĩa là MySQL **không kiểm tra dữ liệu đang có**. Vì vậy
quy trình là: tự kiểm tra trước, rồi mới tắt kiểm tra để thêm nhanh.

```sql
-- 1. Tìm dòng "mồ côi": order trỏ tới user không tồn tại
SELECT o.id, o.user_id
FROM orders o LEFT JOIN users u ON u.id = o.user_id
WHERE u.id IS NULL;
-- 2. Dọn chúng. Sau đó, chỉ trong session này:
SET SESSION foreign_key_checks = 0;
ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id),
  ALGORITHM=INPLACE, LOCK=NONE;
SET SESSION foreign_key_checks = 1;
```

⚠️ Giữa bước 1 và bước 2, ứng dụng vẫn có thể ghi dòng mồ côi mới (nếu code có bug); những dòng đó sẽ
không bị phát hiện. Chạy lại truy vấn bước 1 sau khi thêm xong để chắc chắn. Lưu ý thêm: gh-ost không
hỗ trợ bảng có khoá ngoại, nên bảng đã có khoá ngoại thì công cụ ngoài chỉ còn pt-osc.

## 9. Đối chiếu PostgreSQL

Phần này để bạn thấy cùng bài toán được giải thế nào ở database khác; so sánh đầy đủ hai hệ ở
[chương 25](25-postgres-doi-chieu.md). Các câu lệnh dưới đây là **PostgreSQL**, không chạy trên MySQL.

### 9.1 Mô hình lock khác, cùng một cái bẫy

Postgres không có khái niệm `ALGORITHM` hay `LOCK=`. Mỗi dạng `ALTER TABLE` lấy một mức lock bảng cố
định, và theo tài liệu, mặc định là `ACCESS EXCLUSIVE` trừ khi ghi chú khác. `ACCESS EXCLUSIVE` xung đột
với mọi mức lock khác, kể cả `ACCESS SHARE` mà `SELECT` thường lấy. Các yêu cầu lock cũng xếp hàng, nên
sự cố ở mục 3.3 xảy ra y hệt: một transaction dài chặn `ALTER`, `ALTER` đang chờ chặn mọi query đến sau.

Cách phòng tương đương `lock_wait_timeout`:

```sql
-- PostgreSQL
SET lock_timeout = '5s';
ALTER TABLE users ADD COLUMN nickname text;
```

Điểm Postgres hơn MySQL: **DDL chạy được trong transaction** và rollback được. Migration nhiều câu lỗi
giữa chừng thì không để lại schema dở dang (mục 1.3).

Một số thao tác nhanh tương tự `INSTANT` của MySQL, theo tài liệu `ALTER TABLE`:

- Thêm cột không có default, hoặc có default *non-volatile* (giá trị cố định như `'VND'`, `0`): chỉ sửa
  metadata, không viết lại bảng. Default *volatile* (như `clock_timestamp()`), cột generated `STORED`,
  cột identity thì viết lại cả bảng và index.
- Đổi kiểu cột thường viết lại bảng; ngoại lệ là khi kiểu cũ *binary coercible* sang kiểu mới và không
  dùng `USING` đổi nội dung (ví dụ `varchar` sang `text`).

### 9.2 CREATE INDEX CONCURRENTLY

`CREATE INDEX` thường của Postgres cho đọc nhưng **chặn ghi** trong suốt thời gian dựng index. Tuỳ chọn
`CONCURRENTLY` dựng index mà không chặn `INSERT`, `UPDATE`, `DELETE`:

```sql
-- PostgreSQL
CREATE INDEX CONCURRENTLY idx_orders_user_created ON orders (user_id, created_at);
```

Cái giá, theo tài liệu "Building Indexes Concurrently":

- Postgres phải quét bảng **hai lần** và chờ mọi transaction có thể dùng hoặc sửa bảng kết thúc, nên
  tổng công việc nhiều hơn và lâu hơn đáng kể so với cách thường.
- **Không chạy được trong transaction block.** Migration Laravel trên Postgres mặc định bọc transaction,
  nên migration dùng `->online()` (Laravel sinh `CONCURRENTLY`) phải tắt transaction:

  ```php
  return new class extends Migration
  {
      public $withinTransaction = false;   // bắt buộc cho CREATE INDEX CONCURRENTLY

      public function up(): void
      {
          Schema::table('orders', function (Blueprint $table): void {
              $table->index(['user_id', 'created_at'])->online();
          });
      }
  };
  ```

- Nếu lỗi giữa chừng (deadlock, trùng giá trị khi tạo unique index), câu lệnh thất bại nhưng **để lại
  một index đánh dấu `INVALID`**. Index này không được dùng để truy vấn nhưng **vẫn tốn chi phí cập nhật
  khi ghi**. Cách xử lý được khuyến nghị: `DROP INDEX` nó rồi chạy lại `CREATE INDEX CONCURRENTLY` (hoặc
  `REINDEX INDEX CONCURRENTLY`). Với unique index, phần kiểm tra trùng đã có hiệu lực với các transaction
  khác từ lần quét thứ hai, và index invalid để lại vẫn tiếp tục chặn trùng.
- Mỗi bảng chỉ chạy được một lần dựng index concurrently tại một thời điểm, và không hỗ trợ trực tiếp
  trên bảng partition (phải dựng trên từng partition).

### 9.3 Ràng buộc NOT VALID rồi VALIDATE

Thêm khoá ngoại hoặc `CHECK` trên bảng lớn bình thường phải quét toàn bộ bảng để kiểm tra dữ liệu cũ, và
trong lúc đó các thay đổi khác bị chặn. Postgres cho tách làm hai bước:

```sql
-- PostgreSQL
-- Bước 1: thêm ràng buộc, KHÔNG kiểm tra dòng cũ. Nhanh. Dòng mới/sửa từ giờ phải thoả ràng buộc.
ALTER TABLE orders ADD CONSTRAINT fk_orders_user
  FOREIGN KEY (user_id) REFERENCES users (id) NOT VALID;

-- Bước 2 (lúc khác): quét và kiểm tra dòng cũ.
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_user;
```

Tài liệu giải thích vì sao bước 2 nhẹ: các transaction khác đã tự kiểm tra ràng buộc cho dòng chúng
ghi, nên việc kiểm tra chỉ cần lock `SHARE UPDATE EXCLUSIVE` (không chặn đọc ghi thông thường), cộng
thêm `ROW SHARE` trên bảng được tham chiếu nếu là khoá ngoại. Một lợi ích nữa: nếu bảng đang có dữ liệu
vi phạm, bước 1 vẫn chặn được vi phạm mới, còn dữ liệu cũ thì dọn từ từ tới khi `VALIDATE` thành công.

So với MySQL ở mục 8.4: MySQL không có `NOT VALID`, cách nhanh duy nhất là tắt `foreign_key_checks`, tức
bỏ hẳn bước kiểm tra dòng cũ.

`NOT VALID` áp dụng cho khoá ngoại, `CHECK`, và từ PostgreSQL 18 cả ràng buộc `NOT NULL` (bản tài liệu
17 chỉ liệt kê khoá ngoại và `CHECK`). Với `SET NOT NULL`, tài liệu nói Postgres bỏ qua bước quét bảng
nếu đã có một `CHECK` hợp lệ chứng minh cột không có NULL. Từ đó có cách thêm `NOT NULL` trên bảng lớn
cho các bản trước 18:

```sql
-- PostgreSQL
ALTER TABLE orders ADD CONSTRAINT chk_currency_nn CHECK (currency IS NOT NULL) NOT VALID;
ALTER TABLE orders VALIDATE CONSTRAINT chk_currency_nn;          -- quét, không chặn ghi
ALTER TABLE orders ALTER COLUMN currency SET NOT NULL;           -- ACCESS EXCLUSIVE nhưng không quét
ALTER TABLE orders DROP CONSTRAINT chk_currency_nn;
```

Với PostgreSQL 18 có thể viết thẳng:
`ALTER TABLE orders ADD CONSTRAINT nn_currency NOT NULL currency NOT VALID;` rồi
`VALIDATE CONSTRAINT nn_currency`.

## 10. Quy trình tổng hợp cho một thay đổi schema trên production

Gom mọi thứ của chương thành một checklist để dùng khi viết hoặc review migration:

1. **Thay đổi có tương thích với code đang chạy không?** Thêm cột nullable, thêm bảng, thêm index: tương
   thích. Đổi tên, đổi kiểu, xoá, thêm `NOT NULL` không default: không tương thích, phải chia
   expand/contract (mục 5), mỗi bước một lần deploy.
2. **Tra bảng online DDL (2.3).** Ghi rõ `ALGORITHM` (và `LOCK` với INPLACE) để MySQL báo lỗi thay vì âm
   thầm `COPY`. Kiểm tra câu SQL thật bằng `php artisan migrate --pretend`.
3. **Ước lượng kích thước bảng và replica.** Thao tác dài (dựng lại bảng, dựng index, `COPY`) trên bảng
   lớn có replica phục vụ đọc thì dùng gh-ost hoặc pt-osc (mục 4).
4. **Chuẩn bị cho MDL.** `SET SESSION lock_wait_timeout` ngắn, có retry; kiểm tra transaction dài trước
   khi chạy (mục 3).
5. **Dữ liệu cũ.** Cần backfill thì làm bằng command riêng, theo khoảng PK, có điều tốc (mục 6). Thêm
   unique hoặc khoá ngoại thì kiểm tra dữ liệu vi phạm trước (8.2, 8.4).
6. **Đường lùi.** Mỗi bước có cách lùi; bước xoá dữ liệu đi cuối, tách riêng, có backup.
7. **Theo dõi khi chạy.** Processlist, `performance_schema.metadata_locks`, tiến độ `ALTER` (2.5),
   replica lag, lỗi ứng dụng.

## Lỗi thường gặp

| Lỗi | Vì sao nguy hiểm | Cách tránh |
|---|---|---|
| Chạy `ALTER` không ghi `ALGORITHM` trên bảng lớn | MySQL có thể lặng lẽ chọn `COPY`, chặn ghi hàng giờ | Luôn ghi `ALGORITHM=INSTANT` hoặc `INPLACE, LOCK=NONE`; sai thì lỗi ngay |
| Nghĩ `INSTANT` thì không thể gây sự cố | Mọi `ALTER` đều cần MDL exclusive; một transaction dài làm cả hàng đợi treo | `SET SESSION lock_wait_timeout` ngắn + retry; kiểm tra `innodb_trx` trước |
| Nhầm `innodb_lock_wait_timeout` với `lock_wait_timeout` | Biến đầu cho lock dòng, không ảnh hưởng chờ MDL | Đặt `lock_wait_timeout` cho session chạy DDL |
| Nới `VARCHAR` qua ranh giới 255 byte và tưởng là INPLACE | Phải `COPY`, chặn ghi | Tính theo byte (utf8mb4 × 4); ghi `ALGORITHM=INPLACE` để kiểm |
| Đổi `INT` sang `BIGINT` trực tiếp trên bảng lớn | Đổi kiểu luôn là `COPY` | gh-ost/pt-osc, hoặc expand/contract với cột mới |
| Đổi tên hoặc xoá cột trong cùng lần deploy code | Code cũ đang chạy lỗi `Unknown column` | Expand/contract, mỗi bước một lần deploy |
| Gộp nhiều thay đổi schema vào một migration MySQL | DDL tự commit; lỗi giữa chừng để lại schema dở dang | Một migration, một thay đổi |
| Backfill bằng một câu `UPDATE` cho cả bảng | Transaction khổng lồ: lock nhiều, undo lớn, replica trễ | Batch theo khoảng PK, nghỉ và điều tốc theo replica lag |
| Backfill đọc giá trị lên PHP rồi ghi xuống | Có thể ghi đè giá trị mới hơn do ứng dụng vừa ghi | Tính ngay trong câu `UPDATE`, thêm điều kiện `IS NULL` |
| Thêm `NOT NULL` không có `DEFAULT` | Dòng cũ nhận giá trị ngầm định (0, '') mà không báo; cột ngày giờ thì lỗi | Ghi `DEFAULT` rõ ràng, hoặc nullable → backfill → `NOT NULL` |
| Thêm unique index khi chưa dọn trùng | Thất bại sau khi chạy rất lâu | `GROUP BY ... HAVING COUNT(*) > 1` trước |
| Tắt `foreign_key_checks` để thêm khoá ngoại nhanh mà không kiểm tra dữ liệu | Dữ liệu mồ côi đang có không bị phát hiện | Truy vấn `LEFT JOIN ... IS NULL` trước và sau |
| Postgres: `CREATE INDEX CONCURRENTLY` trong migration có transaction | Lỗi "cannot run inside a transaction block" | `public $withinTransaction = false;` |
| Postgres: bỏ mặc index `INVALID` sau khi `CONCURRENTLY` lỗi | Vẫn tốn chi phí ghi, không được dùng để đọc | `DROP INDEX` rồi tạo lại |

## Tóm tắt chương

- Migration là thay đổi schema dưới dạng code có thứ tự, review được, chạy tự động. Trên MySQL, DDL tự
  commit nên migration không nguyên tử: mỗi migration chỉ nên làm một thay đổi.
- MySQL có ba algorithm: `INSTANT` (chỉ sửa metadata), `INPLACE` (trong InnoDB, thường cho ghi đồng
  thời, có thể dựng lại bảng), `COPY` (copy từng dòng, chặn ghi). Không ghi `ALGORITHM` thì MySQL thử lần
  lượt INSTANT, INPLACE, COPY.
- Thêm, xoá, đổi tên cột và đặt default: INSTANT. Thêm index: INPLACE, cho ghi. Đổi kiểu cột: chỉ COPY.
  Tra bảng "Online DDL Operations" trước mọi thay đổi trên bảng lớn.
- Online DDL vẫn có giới hạn: online log có hạn, tốn đĩa, không tạm dừng được, và replica chỉ bắt đầu
  chạy DDL sau khi primary xong nên trễ tương ứng.
- Mọi `ALTER` đều cần MDL exclusive một khoảnh khắc. Transaction dài chặn `ALTER`, `ALTER` đang chờ chặn
  mọi query sau. `lock_wait_timeout` mặc định một năm: đặt ngắn và retry.
- gh-ost (đọc binlog) và pt-osc (trigger) tự copy bảng theo khúc, điều tốc theo replica lag, rồi đổi tên
  nguyên tử. gh-ost không hỗ trợ khoá ngoại; pt-osc thêm tải vào mỗi câu ghi của ứng dụng.
- Expand/contract: thêm cái mới, ghi cả hai, backfill, chuyển đọc, ngừng ghi cái cũ, xoá cái cũ. Mỗi
  bước một lần deploy, có đường lùi.
- Backfill theo khoảng PK, mỗi batch một transaction ngắn, idempotent (`IS NULL`), tính giá trị ngay
  trong `UPDATE`, nghỉ theo replica lag.
- Postgres: `lock_timeout`, DDL trong transaction, `CREATE INDEX CONCURRENTLY` (không chạy trong
  transaction, lỗi thì để lại index `INVALID`), và `NOT VALID` + `VALIDATE CONSTRAINT`.

## Câu hỏi tự kiểm tra

1. Vì sao migration nên được lưu trong git thay vì chạy `ALTER TABLE` bằng tay trên production? Bảng
   `migrations` dùng để làm gì? (1.2)
2. Một migration Laravel trên MySQL gồm hai câu `ALTER`, câu thứ hai lỗi. Database và bảng `migrations`
   ở trạng thái nào? Trên PostgreSQL thì sao? (1.3)
3. Phân biệt `INSTANT`, `INPLACE`, `COPY`. Vì sao nên ghi rõ `ALGORITHM` dù MySQL tự chọn được? (2.1)
4. Cột `title VARCHAR(60)` charset utf8mb4. Nới lên `VARCHAR(63)` và lên `VARCHAR(70)`, mỗi trường hợp
   là INPLACE hay COPY? Vì sao? (2.4)
5. Mô tả từng bước vì sao một câu `ALTER ... ALGORITHM=INSTANT` có thể làm toàn bộ ứng dụng treo. Bạn
   tìm thủ phạm bằng những truy vấn nào? (3.3, 3.4)
6. Một `ALTER` INPLACE mất 90 phút trên primary. Điều gì xảy ra với replica, và vì sao đó là lý do dùng
   gh-ost dù thao tác vốn "online"? (2.7, 4.3)
7. So sánh cách pt-osc và gh-ost đồng bộ thay đổi mới sang bảng bóng. Khi nào bắt buộc phải dùng pt-osc
   thay vì gh-ost? (4.2, 4.3, 4.4)
8. Vì sao đổi tên cột bằng `RENAME COLUMN` (INSTANT) vẫn gây lỗi khi deploy? Liệt kê các bước
   expand/contract và cách lùi ở mỗi bước. (5.1, 5.3)
9. Trong script backfill, điều kiện `full_name IS NULL` và việc dùng `SET full_name = name` thay vì đọc
   lên PHP giải quyết những vấn đề gì? (6.2)
10. Ở Postgres, vì sao `VALIDATE CONSTRAINT` không chặn ghi trong khi thêm khoá ngoại thông thường thì
    chặn? (9.3)

## Bài tập

1. **Đo ba algorithm.** Trên `lab20`, dựng bảng `big_orders` khoảng 300 nghìn dòng như mục 2.5. Chạy và
   ghi lại thời gian cùng số "rows affected" của: thêm cột `INSTANT`, thêm index `INPLACE`, xoá cột bằng
   `ALGORITHM=INPLACE`, đổi `amount` sang `BIGINT`. Với mỗi câu, thử thêm `LOCK=NONE` và ghi lại câu nào
   bị từ chối. Đối chiếu kết quả với bảng 2.3.
2. **Tái hiện sự cố MDL.** Dùng ba session như bảng ở mục 3.3. Trong lúc treo, chạy các truy vấn ở 3.4
   và chỉ ra session nào là thủ phạm. Sau đó làm lại với `SET SESSION lock_wait_timeout = 3` ở session
   migration và mô tả khác biệt.
3. **Kế hoạch expand/contract.** Bảng `orders` 80 triệu dòng có cột `status VARCHAR(20)` chứa các giá trị
   chữ. Nhóm muốn chuyển sang cột `status_code TINYINT UNSIGNED NOT NULL` theo một bảng ánh xạ. Viết kế
   hoạch từng bước: mỗi bước deploy gì (migration hay code), câu DDL kèm `ALGORITHM`, cách backfill, cách
   kiểm tra, và cách lùi.
4. **Backfill có tiếp tục được.** Sửa script `backfill.php` ở mục 6.2 để: in tiến độ phần trăm theo id,
   ghi id đã xử lý xong vào một file sau mỗi batch, và khi chạy lại thì đọc file đó để tiếp tục thay vì
   bắt đầu từ 0. Chạy thử bằng SQLite (mặc định của script), dừng giữa chừng bằng Ctrl+C rồi chạy lại.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [InnoDB and Online DDL](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl.html),
  [Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html)
  (bảng tra quan trọng nhất của chương),
  [Online DDL Performance and Concurrency](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-performance.html),
  [Online DDL Space Requirements](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-space-requirements.html),
  [Online DDL Failure Conditions](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-failure-conditions.html),
  [Online DDL Limitations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-limitations.html),
  [ALTER TABLE Statement](https://dev.mysql.com/doc/refman/8.4/en/alter-table.html),
  [Metadata Locking](https://dev.mysql.com/doc/refman/8.4/en/metadata-locking.html),
  [Monitoring ALTER TABLE Progress](https://dev.mysql.com/doc/refman/8.4/en/monitor-alter-table-performance-schema.html),
  biến [`lock_wait_timeout`](https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html#sysvar_lock_wait_timeout)
  và [`innodb_online_alter_log_max_size`](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html#sysvar_innodb_online_alter_log_max_size).
- [gh-ost](https://github.com/github/gh-ost): README, thư mục `doc/` (đặc biệt "Requirements and
  limitations", "Command line flags", "Cut-over", "Why triggerless").
- [pt-online-schema-change](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html)
  (Percona Toolkit).
- Laravel 13: [Database: Migrations](https://laravel.com/docs/13.x/migrations) (các mục Instant Column
  Operations, DDL Locking, Online Index Creation, Running Migrations).
- PostgreSQL 18: [ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html) (phần Notes),
  [CREATE INDEX: Building Indexes Concurrently](https://www.postgresql.org/docs/18/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY),
  [Explicit Locking](https://www.postgresql.org/docs/18/explicit-locking.html).
- Martin Fowler, [ParallelChange](https://martinfowler.com/bliki/ParallelChange.html) (expand/contract).
