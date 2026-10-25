# Chương 15. Lock và deadlock

> [← Mục lục](README.md) · [← Chương 14: Isolation level và MVCC](14-isolation-mvcc.md) · [Chương 16: Bên trong InnoDB →](16-ben-trong-innodb.md)

**Bạn sẽ học được:**

- Lock (khoá) là gì, hai loại cơ bản shared (S) và exclusive (X), khoá mức dòng và mức bảng.
- Dùng `SELECT ... FOR SHARE`, `SELECT ... FOR UPDATE`, `NOWAIT`, `SKIP LOCKED` đúng chỗ, và làm
  một hàng đợi job đơn giản bằng `SKIP LOCKED`.
- InnoDB thật sự khoá cái gì: record lock, gap lock, next-key lock, insert intention lock, intention
  lock (IS/IX), và vì sao một câu `UPDATE` có thể khoá những dòng không hề khớp `WHERE`.
- Khác biệt về lock giữa Read Committed và Repeatable Read.
- Chọn giữa pessimistic lock và optimistic lock (cột `version`).
- Deadlock xảy ra thế nào, InnoDB xử lý ra sao (lỗi 1213), khác gì lock wait timeout (lỗi 1205),
  đọc mục `LATEST DETECTED DEADLOCK`, giảm deadlock và retry trong ứng dụng PHP.
- Xem ai đang giữ lock, ai đang chờ bằng `performance_schema` và `sys`.

**Cần biết trước:** [Chương 11](11-index.md) (B+tree, clustered index, secondary index),
[Chương 13](13-transaction-acid.md) (transaction, autocommit, lỗi trong transaction),
[Chương 14](14-isolation-mvcc.md) (isolation level, consistent read, MVCC, phantom).

## 1. Dữ liệu mẫu của chương

Mọi ví dụ chạy trên MySQL 8.4, bảng InnoDB, isolation mặc định `REPEATABLE READ` (trừ chỗ ghi rõ).
Cách mở MySQL bằng Docker và mở hai session song song giống [chương 13, mục 1](13-transaction-acid.md#1-dữ-liệu-mẫu-của-chương):
mỗi cửa sổ `mysql` là một session; trong chương gọi là session A, B (đôi khi C).

```sql
DROP DATABASE IF EXISTS ch15;
CREATE DATABASE ch15;
USE ch15;

-- Tài khoản ngân hàng: dùng cho ví dụ khoá dòng và deadlock chuyển tiền
CREATE TABLE accounts (
  id      INT PRIMARY KEY,
  owner   VARCHAR(50)   NOT NULL,
  balance DECIMAL(12,2) NOT NULL
) ENGINE = InnoDB;

INSERT INTO accounts VALUES
  (1, 'An',   500.00),
  (2, 'Bình', 300.00),
  (3, 'Chi',    0.00);

-- Thành viên: id cách nhau 10 để có "khe" (gap) giữa các giá trị.
-- age có index KHÔNG unique, name KHÔNG có index: hai thứ này quyết định InnoDB khoá gì.
CREATE TABLE members (
  id   INT PRIMARY KEY,
  age  INT         NOT NULL,
  name VARCHAR(50) NOT NULL,
  INDEX idx_age (age)
) ENGINE = InnoDB;

INSERT INTO members VALUES
  (10, 20, 'An'),
  (20, 30, 'Bình'),
  (30, 40, 'Chi');

-- Hàng đợi job: dùng cho SKIP LOCKED
CREATE TABLE jobs (
  id         BIGINT AUTO_INCREMENT PRIMARY KEY,
  payload    VARCHAR(100) NOT NULL,
  status     ENUM('pending','running','done','failed') NOT NULL DEFAULT 'pending',
  run_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  attempts   INT          NOT NULL DEFAULT 0,
  locked_by  VARCHAR(64)  NULL,
  locked_at  DATETIME     NULL,
  INDEX idx_pick (status, run_at)
) ENGINE = InnoDB;

INSERT INTO jobs (payload) VALUES ('email 1'), ('email 2'), ('email 3'), ('email 4');
```

Kiểm tra:

```sql
SELECT * FROM members;
-- Kết quả mong đợi:
-- +----+-----+------+
-- | id | age | name |
-- +----+-----+------+
-- | 10 |  20 | An   |
-- | 20 |  30 | Bình |
-- | 30 |  40 | Chi  |
-- +----+-----+------+
```

Chạy lại toàn bộ đoạn trên mỗi khi muốn làm lại từ đầu. Trước mỗi timeline, nhớ `COMMIT` hoặc
`ROLLBACK` mọi transaction còn mở ở các session, nếu không lock cũ sẽ làm sai kết quả.

## 2. Lock là gì và vì sao cần

### 2.1 Bài toán

Chương 14 cho thấy MVCC giải quyết được xung đột *đọc với ghi*: người đọc xem một snapshot cũ, người
ghi tạo phiên bản mới, không ai chờ ai. Nhưng MVCC không giải quyết được xung đột *ghi với ghi*. Hai
transaction cùng sửa một dòng thì không thể cùng tạo hai "phiên bản mới nhất". Phải có một bên chờ
bên kia xong. Cơ chế bắt chờ đó là **lock**.

Lock là một "tấm biển" transaction đặt lên một đối tượng (dòng, khoảng index, bảng) để nói: "tôi đang
dùng cái này theo kiểu này, ai muốn dùng theo kiểu xung đột thì xếp hàng". Database tự đặt lock khi
bạn chạy `UPDATE`, `DELETE`, `INSERT`; bạn cũng có thể chủ động xin lock bằng locking read
(mục 3).

### 2.2 Shared lock và exclusive lock

Hai loại lock cơ bản (manual MySQL gọi là *shared and exclusive locks*):

- **Shared lock (S)**: quyền *đọc và giữ nguyên*. Nhiều transaction cùng giữ S trên một dòng được.
  Khi còn ai giữ S thì không ai sửa hay xoá được dòng đó.
- **Exclusive lock (X)**: quyền *sửa hoặc xoá*. Chỉ một transaction giữ X trên một dòng; ai xin S hay
  X trên dòng đó đều phải chờ.

Bảng tương thích (xin được ngay hay phải chờ):

| Mình xin ↓ / Người khác đang giữ → | Không ai giữ | S | X |
|---|---|---|---|
| S | Được | Được | Chờ |
| X | Được | Chờ | Chờ |

Ai lấy lock gì:

| Câu lệnh | Lock trên dòng |
|---|---|
| `SELECT ...` thường (consistent read) | **Không lock gì** (trừ Serializable, mục 5.4) |
| `SELECT ... FOR SHARE` | S |
| `SELECT ... FOR UPDATE` | X |
| `UPDATE`, `DELETE` | X |
| `INSERT` | X trên dòng mới chèn |

⚠️ Dòng đầu là điểm hay quên nhất: `SELECT` thường đọc snapshot qua undo log (chương 14), nên **không
bao giờ chờ lock dòng và không chặn ai**. Hệ quả: lock chỉ bảo vệ bạn khỏi những người *cũng xin
lock*. Một đoạn code khác đọc bằng `SELECT` thường rồi ghi đè thì lock của bạn không ngăn được nó.

### 2.3 Lock giữ tới hết transaction

InnoDB nhả row lock khi transaction `COMMIT` hoặc `ROLLBACK`, không nhả giữa chừng. Đây là cách làm
gọi là *two-phase locking* (2PL): pha 1 chỉ lấy thêm lock, pha 2 nhả tất cả một lúc ở cuối. Ba hệ quả:

1. Transaction càng dài, lock càng giữ lâu, người khác càng chờ lâu (chương 13, mục 9).
2. Ở chế độ autocommit, mỗi câu lệnh là một transaction, nên lock nhả ngay khi câu chạy xong.
3. ⚠️ `ROLLBACK TO SAVEPOINT` không nhả row lock đã lấy sau savepoint (chương 13, mục 6.2); một câu
   lệnh bị lỗi và bị rollback riêng cũng không nhả lock nó đã lấy.

### 2.4 Row lock và table lock

Lock có *độ mịn* (granularity) khác nhau:

| | Row lock (khoá dòng) | Table lock (khoá bảng) |
|---|---|---|
| Khoá gì | Một dòng (chính xác: một bản ghi index, mục 4) | Cả bảng |
| Song song | Cao: hai transaction sửa hai dòng khác nhau không chờ nhau | Thấp: mọi người ghi xếp hàng |
| Chi phí quản lý | Nhiều lock nhỏ, tốn bộ nhớ hơn | Một lock |
| Ví dụ | InnoDB khi `UPDATE ... WHERE id = 1` | `LOCK TABLES t WRITE`; engine MyISAM khoá cả bảng mỗi lần ghi |

InnoDB khoá mức dòng, đây là lý do lớn nhất nó thay MyISAM làm engine mặc định. Nhưng InnoDB vẫn
dùng lock mức bảng cho vài mục đích: intention lock (mục 4.7), `LOCK TABLES`, AUTO-INC (mục 7), và
tầng server còn có metadata lock (mục 7.3).

Thử ngay để thấy row lock:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `UPDATE accounts SET balance = balance - 10 WHERE id = 1;` | | A giữ X trên dòng id 1 |
| 2 | | `SELECT balance FROM accounts WHERE id = 1;` | Trả về **500.00** ngay, không chờ: consistent read đọc bản đã commit |
| 3 | | `UPDATE accounts SET balance = balance + 10 WHERE id = 2;` | Chạy ngay: dòng khác, không xung đột |
| 4 | | `UPDATE accounts SET balance = balance + 10 WHERE id = 1;` | **Chờ** A |
| 5 | `COMMIT;` | | Câu ở bước 4 của B chạy xong (1 dòng) |
| 6 | | `COMMIT;` | Dòng 1: 500 - 10 + 10 = 500.00; dòng 2: 310.00 |

## 3. Locking read: SELECT ... FOR SHARE và FOR UPDATE

### 3.1 Vì sao cần

Mẫu "đọc, tính ở ứng dụng, rồi ghi" (*read-modify-write*) bị lost update nếu đọc bằng `SELECT`
thường (chương 14): hai request cùng đọc tồn kho 1, cùng thấy còn hàng, cùng trừ. Muốn người thứ hai
phải chờ ngay từ lúc *đọc*, ta đọc bằng **locking read**: câu `SELECT` vừa đọc vừa xin lock trên các
dòng đọc được.

```sql
SELECT ... FOR SHARE;              -- xin S trên các dòng đọc được
SELECT ... LOCK IN SHARE MODE;     -- cú pháp cũ, tương đương FOR SHARE, vẫn chạy để tương thích
SELECT ... FOR UPDATE;             -- xin X trên các dòng đọc được
```

Manual MySQL ghi `FOR SHARE` thay thế `LOCK IN SHARE MODE` và chỉ `FOR SHARE` hỗ trợ thêm `OF`,
`NOWAIT`, `SKIP LOCKED`.

Một điểm khác quan trọng với `SELECT` thường: locking read **đọc phiên bản mới nhất đã commit**, không
đọc snapshot của transaction. Ở Repeatable Read, cùng một transaction có thể thấy hai kết quả khác
nhau giữa `SELECT` thường và `SELECT ... FOR UPDATE` (chương 14 đã minh hoạ). Lý do hợp lý: đã khoá để
sửa thì phải sửa trên dữ liệu thật hiện tại, không phải bản cũ.

### 3.2 FOR UPDATE: đọc để sửa

Ví dụ rút tiền, chặn hai lần rút cùng lúc làm số dư âm:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 2 FOR UPDATE;` | | A thấy 300.00, giữ X dòng 2 |
| 2 | | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 2 FOR UPDATE;` | **B chờ** A ngay ở câu đọc |
| 3 | App A: 300 ≥ 200, cho rút. `UPDATE accounts SET balance = 100.00 WHERE id = 2;` `COMMIT;` | | A nhả lock |
| 4 | | (câu ở bước 2 trả kết quả) | B thấy **100.00**, giá trị mới nhất |
| 5 | | App B: 100 < 200, từ chối. `ROLLBACK;` | Số dư không âm |

Nếu bước 1 và 2 dùng `SELECT` thường, cả hai cùng thấy 300 và cùng rút 200: số dư cuối sai.

⚠️ Locking read chỉ có tác dụng trong transaction. Với autocommit bật mà không có
`START TRANSACTION`, câu `SELECT ... FOR UPDATE` tự là một transaction và nhả lock ngay khi chạy xong,
tức là vô dụng. Trong Laravel, `lockForUpdate()` phải nằm trong `DB::transaction(...)`.

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

// Rút tiền kiểu pessimistic. Laravel: lockForUpdate() sinh "for update",
// sharedLock() sinh "lock in share mode" (với MySQL).
function withdraw(int $accountId, string $amount): void
{
    DB::transaction(function () use ($accountId, $amount): void {
        $acc = DB::table('accounts')->where('id', $accountId)->lockForUpdate()->first();
        if ($acc === null || bccomp($acc->balance, $amount, 2) < 0) {
            throw new RuntimeException('Không đủ số dư');   // ném ra: Laravel rollback
        }
        DB::table('accounts')->where('id', $accountId)
            ->update(['balance' => bcsub($acc->balance, $amount, 2)]);
    });
}
```

Với bài toán đơn giản như trên, một câu `UPDATE` có điều kiện còn tốt hơn (mục 8):
`UPDATE accounts SET balance = balance - 200 WHERE id = 2 AND balance >= 200;` rồi kiểm tra số dòng
bị ảnh hưởng. `FOR UPDATE` dành cho khi logic quá phức tạp để gói vào một câu SQL.

### 3.3 FOR SHARE: đọc để giữ nguyên

`FOR SHARE` dùng khi bạn cần *dòng không bị đổi hay xoá* trong lúc làm việc khác, nhưng không định
sửa chính nó. Ví dụ trong manual MySQL: trước khi chèn dòng con, khoá S dòng cha để không ai xoá cha
giữa chừng:

```sql
START TRANSACTION;
SELECT * FROM parent WHERE name = 'Jones' FOR SHARE;   -- ai muốn xoá/sửa cha phải chờ
INSERT INTO child (parent_id, ...) VALUES (...);
COMMIT;
```

Nhiều session cùng chèn con cho một cha thì cùng giữ S, không chặn nhau.

⚠️ **Không dùng `FOR SHARE` cho mẫu đọc rồi sửa chính dòng đó.** Manual MySQL nói rõ với ví dụ bộ đếm:
hai người cùng đọc bằng `FOR SHARE` thì ít nhất một người sẽ deadlock khi cập nhật. Timeline:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 1 FOR SHARE;` | | A giữ S dòng 1 |
| 2 | | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 1 FOR SHARE;` | B cũng giữ S (S tương thích S) |
| 3 | `UPDATE accounts SET balance = balance - 10 WHERE id = 1;` | | A xin X, chờ S của B |
| 4 | | `UPDATE accounts SET balance = balance - 10 WHERE id = 1;` | B xin X, chờ S của A: vòng chờ. InnoDB rollback một bên với `ERROR 1213` (mục 10) |

Đọc để sửa thì luôn `FOR UPDATE`.

### 3.4 Phạm vi của locking read: subquery, join, OF

- ⚠️ Locking read ở câu ngoài **không khoá** dòng mà subquery đọc. Ví dụ trong manual:
  `SELECT * FROM t1 WHERE c1 = (SELECT c1 FROM t2) FOR UPDATE;` chỉ khoá `t1`. Muốn khoá `t2` thì
  subquery cũng phải có `FOR UPDATE`.
- Với join, `FOR UPDATE` khoá dòng của mọi bảng tham gia. Muốn chỉ khoá một bảng:
  `SELECT ... FROM orders o JOIN customers c ON ... FOR UPDATE OF o;` (tên bảng phải viết đúng alias
  nếu có alias).
- Có thể trộn: `FOR UPDATE OF o FOR SHARE OF c`.

### 3.5 NOWAIT: không chờ, báo lỗi ngay

Mặc định, gặp dòng đang bị khoá thì locking read chờ (tới `innodb_lock_wait_timeout`, mục 9). Thêm
`NOWAIT` thì không chờ: dòng bị khoá là lỗi ngay. Hợp với giao diện kiểu "bản ghi đang có người xử lý,
thử lại sau" thay vì bắt người dùng nhìn vòng xoay.

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT * FROM accounts WHERE id = 1 FOR UPDATE;` | | A giữ X dòng 1 |
| 2 | | `START TRANSACTION;` `SELECT * FROM accounts WHERE id = 1 FOR UPDATE NOWAIT;` | Ngay lập tức: `ERROR 3572 (HY000): Statement aborted because lock(s) could not be acquired immediately and NOWAIT is set.` |
| 3 | | `SELECT * FROM accounts WHERE id = 2 FOR UPDATE NOWAIT;` | Trả về dòng 2: không ai khoá |

### 3.6 SKIP LOCKED: bỏ qua dòng đang bị khoá

`SKIP LOCKED` cũng không chờ, nhưng thay vì báo lỗi thì **loại các dòng đang bị khoá khỏi kết quả**.
Manual cảnh báo: kết quả là một view không nhất quán của dữ liệu, không hợp cho việc giao dịch thông
thường; chỉ dùng để tránh tranh chấp khi nhiều session cùng truy cập một bảng dạng hàng đợi.

Ghi nhớ về hai tuỳ chọn này (theo manual):

- `NOWAIT` và `SKIP LOCKED` chỉ áp dụng cho **row lock**; chờ metadata lock hay table lock thì vẫn chờ.
- Câu lệnh dùng chúng *không an toàn* với replication dạng statement-based.
- Có từ MySQL 8.0; PostgreSQL có từ 9.5.

**Hàng đợi job bằng `SKIP LOCKED`.** Nhiều worker cùng lấy job từ bảng `jobs`, mỗi job chỉ một
worker làm. Với `FOR UPDATE` thường, mọi worker cùng nhắm vào job cũ nhất và xếp hàng chờ nhau; với
`SKIP LOCKED`, mỗi worker lấy một nhóm job khác nhau.

| Bước | Worker A | Worker B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT id FROM jobs WHERE status = 'pending' AND run_at <= NOW() ORDER BY run_at LIMIT 2 FOR UPDATE SKIP LOCKED;` | | A nhận id 1, 2 (giữ X) |
| 2 | | `START TRANSACTION;` cùng câu `SELECT` | B **không chờ**, nhận id 3, 4 |
| 3 | `UPDATE jobs SET status = 'running', locked_by = 'A', locked_at = NOW(), attempts = attempts + 1 WHERE id IN (1, 2);` `COMMIT;` | | |
| 4 | | Tương tự với id 3, 4, `COMMIT;` | Hai worker chia việc, không job nào bị làm hai lần |

Bước 1 và 2 có thể ra kết quả hơi khác (ví dụ thứ tự các job cùng `run_at`); điểm chắc chắn là hai tập
id **rời nhau**. Index `idx_pick (status, run_at)` giúp câu lấy job chỉ quét và khoá vùng `pending`
cần thiết, không quét cả bảng (mục 6).

Worker viết bằng PDO:

```php
<?php
declare(strict_types=1);

/**
 * Nhận tối đa $limit job. Transaction chỉ bao phần "nhận", rất ngắn.
 * @return list<int> id các job đã nhận
 */
function claimJobs(PDO $pdo, string $workerId, int $limit = 10): array
{
    $pdo->beginTransaction();
    try {
        $stmt = $pdo->prepare(
            "SELECT id FROM jobs
              WHERE status = 'pending' AND run_at <= NOW()
              ORDER BY run_at LIMIT :lim
              FOR UPDATE SKIP LOCKED"
        );
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);   // LIMIT phải là số nguyên
        $stmt->execute();
        $ids = array_map('intval', $stmt->fetchAll(PDO::FETCH_COLUMN));

        if ($ids !== []) {
            $in = implode(',', array_fill(0, count($ids), '?'));
            $pdo->prepare(
                "UPDATE jobs SET status = 'running', locked_by = ?, locked_at = NOW(),
                        attempts = attempts + 1
                  WHERE id IN ($in)"
            )->execute([$workerId, ...$ids]);
        }
        $pdo->commit();
        return $ids;
    } catch (Throwable $e) {
        if ($pdo->inTransaction()) {
            $pdo->rollBack();
        }
        throw $e;
    }
}
// Xử lý từng job NGOÀI transaction; xong thì:
// UPDATE jobs SET status = 'done' WHERE id = ? AND locked_by = ?
```

Vì sao tách "nhận" và "xử lý": nếu giữ transaction suốt lúc xử lý (gửi email mất vài giây), lock và
connection bị giữ, transaction dài cản purge undo log (chương 16). Tách ra thì phải tự lo:

1. **Worker chết giữa chừng**: job kẹt ở `running`. Một tác vụ định kỳ trả job quá hạn về
   `pending` (`WHERE status = 'running' AND locked_at < NOW() - INTERVAL 15 MINUTE`). Ngưỡng phải lớn
   hơn thời gian chạy dài nhất của một job.
2. **Giới hạn số lần thử**: `attempts` vượt ngưỡng thì chuyển `failed`, tránh lặp vô hạn với job lỗi
   vĩnh viễn.
3. **Idempotent**: job có thể chạy hai lần (xong việc nhưng chết trước khi ghi `done`), nên xử lý phải
   cho cùng kết quả khi chạy lại.

Laravel queue driver `database` dùng đúng kỹ thuật này: với MySQL 8.0.1 trở lên nó lấy job bằng
`FOR UPDATE SKIP LOCKED`. Khi tải vượt sức database, chuyển sang Redis hoặc message broker.

## 4. InnoDB khoá cái gì: các loại lock

### 4.1 InnoDB khoá bản ghi index, không phải "dòng"

Nhắc lại chương 11: bảng InnoDB *là* clustered index (B+tree sắp theo primary key), mỗi secondary
index là một B+tree khác chứa `(giá trị cột, primary key)`. Khi nói "khoá dòng", InnoDB thật ra khoá
**bản ghi trong index** (index record) mà câu lệnh đi qua. Bảng không khai báo index nào thì InnoDB vẫn
có clustered index ẩn (`GEN_CLUST_INDEX`) và khoá trên đó.

Từ đó ra ba quy tắc nền (manual, mục *Locks Set by Different SQL Statements*):

1. Locking read, `UPDATE`, `DELETE` khoá **mọi bản ghi index mà quá trình tìm kiếm đi qua**, không chỉ
   bản ghi khớp `WHERE`. InnoDB không nhớ điều kiện `WHERE`, nó chỉ biết đã quét khoảng index nào.
2. Khoá bản ghi trong secondary index thì InnoDB khoá luôn bản ghi tương ứng trong clustered index.
3. Không có index phù hợp phải quét cả bảng thì mọi dòng bị khoá, chặn luôn mọi insert của người khác
   (mục 6).

Để chặn được *phantom* (dòng mới xuất hiện trong khoảng đã đọc, chương 14), InnoDB còn khoá cả
**khoảng trống giữa các bản ghi**. Dưới đây là bốn loại lock mức bản ghi, minh hoạ trên
`members.id` có các giá trị 10, 20, 30. Hãy hình dung trục số của index:

```
(-∞) ... 10 ... 20 ... 30 ... (supremum)
     khe     khe     khe     khe
```

*Supremum* là bản ghi giả luôn đứng sau giá trị lớn nhất của page; khoá nó nghĩa là khoá khoảng
"lớn hơn mọi giá trị hiện có".

### 4.2 Record lock

Khoá đúng **một bản ghi index**. Ví dụ `SELECT * FROM members WHERE id = 20 FOR UPDATE;` chỉ khoá
bản ghi id 20 trong PRIMARY: người khác không sửa, xoá, khoá được id 20, nhưng chèn id 15 hay 25 thoải
mái.

### 4.3 Gap lock

Khoá **khoảng trống giữa hai bản ghi** (không gồm chính các bản ghi). Ví dụ gap lock trên khoảng
(10, 20) chặn mọi insert id 11 tới 19.

Ba tính chất (manual, mục *Gap Locks*) giải thích hầu hết deadlock lạ ở mục 10:

- Gap lock **chỉ có tác dụng ngăn chặn** (manual: *purely inhibitive*): mục đích duy nhất là chặn
  transaction khác chèn vào khoảng.
- Gap lock của các transaction khác nhau **cùng tồn tại được**, không xung đột nhau, kể cả gap "S" với
  gap "X". Hai transaction có thể cùng giữ gap lock trên cùng một khoảng.
- Gap lock không cần khi tìm *một dòng* bằng unique index với điều kiện đầy đủ (ví dụ `id = 20` và dòng
  tồn tại). Nếu điều kiện chỉ gồm một phần cột của unique index nhiều cột thì vẫn có gap lock.

### 4.4 Next-key lock

**Record lock trên một bản ghi cộng gap lock trên khoảng ngay trước nó.** Với `members.id`, các
next-key lock có thể có là:

```
(-∞, 10]   (10, 20]   (20, 30]   (30, supremum]
```

Dấu `(` là không gồm, `]` là gồm. Ở Repeatable Read, InnoDB mặc định dùng next-key lock khi tìm kiếm
và quét index; đây là cách InnoDB chặn phantom cho locking read. Khoảng cuối khoá supremum, nên chặn
mọi insert id lớn hơn 30.

### 4.5 Insert intention lock

Trước khi chèn một dòng, `INSERT` đặt một loại gap lock đặc biệt gọi là **insert intention lock**: báo
"tôi sắp chèn vào vị trí này trong khoảng". Hai điều cần nhớ:

- Hai insert intention trong cùng khoảng **không chờ nhau** nếu chèn khác vị trí (manual: chèn 5 và 6
  vào khoảng giữa 4 và 7 không chặn nhau).
- Insert intention **phải chờ** nếu transaction khác đang giữ gap lock (hoặc next-key lock) trên
  khoảng đó. Đây chính là cách gap lock "chặn insert".

Sau khi chèn xong, dòng mới mang record lock X (không có gap lock), nên không chặn người khác chèn vào
khoảng trước nó.

### 4.6 Bảng tương thích của lock mức bản ghi

Tổng hợp: "người khác đang giữ" (cột) với "mình xin" (dòng), trên cùng bản ghi hoặc cùng khoảng.

| Mình xin ↓ / Đang giữ → | Record lock | Gap lock | Next-key lock | Insert intention |
|---|---|---|---|---|
| Record lock | Theo S/X | Được | Theo S/X | Được |
| Gap lock | Được | Được | Được | Được |
| Next-key lock | Theo S/X | Được | Theo S/X | Được |
| Insert intention | Được | **Chờ** | **Chờ** | Được |

"Theo S/X" nghĩa là áp bảng S/X ở mục 2.2 (S với S được, có X là chờ). Bảng này đọc theo ba câu:
gap không chặn gì ngoài insert; insert chỉ bị chặn bởi gap; phần "record" thì theo luật S/X.

### 4.7 Intention lock (IS, IX): lock mức bảng đi kèm

InnoDB cho phép row lock và table lock cùng tồn tại (*multiple granularity locking*). Vấn đề: câu
`LOCK TABLES t WRITE` muốn khoá cả bảng thì làm sao biết có ai đang khoá một dòng nào đó, mà không phải
duyệt từng dòng? Lời giải là **intention lock**, lock mức bảng nói trước "tôi sẽ khoá dòng kiểu gì":

- **IS** (intention shared): sắp khoá S một số dòng. Trước khi lấy S trên dòng, transaction phải có IS
  (hoặc mạnh hơn) trên bảng.
- **IX** (intention exclusive): sắp khoá X một số dòng. Trước khi lấy X trên dòng phải có IX trên bảng.

InnoDB tự lấy, bạn không cần làm gì. Bảng tương thích mức bảng (manual):

| | X | IX | S | IS |
|---|---|---|---|---|
| **X** | Xung đột | Xung đột | Xung đột | Xung đột |
| **IX** | Xung đột | Tương thích | Xung đột | Tương thích |
| **S** | Xung đột | Xung đột | Tương thích | Tương thích |
| **IS** | Xung đột | Tương thích | Tương thích | Tương thích |

Điểm mấu chốt: **IX với IX tương thích**, nên hàng nghìn transaction cùng sửa các dòng khác nhau của
một bảng không chặn nhau ở mức bảng. Intention lock chỉ chặn yêu cầu khoá *cả bảng* (như
`LOCK TABLES ... WRITE`). Trong `data_locks` bạn sẽ luôn thấy một dòng `LOCK_TYPE = TABLE`,
`LOCK_MODE = IX` (hoặc `IS`) đứng đầu.

### 4.8 Lock "ngầm" của dòng vừa insert

Chèn một dòng xong, nếu bạn xem `performance_schema.data_locks` ngay thì thường **không thấy** record
lock nào trên dòng đó, chỉ thấy `IX` mức bảng. Không phải dòng không được bảo vệ: InnoDB dùng *implicit
lock* (lock ngầm). Mỗi bản ghi lưu id của transaction đã ghi nó gần nhất (`DB_TRX_ID`, chương 16); nếu
transaction đó còn đang chạy thì bản ghi coi như đang bị khoá X. Chỉ khi có transaction khác đụng vào,
InnoDB mới đổi lock ngầm thành lock tường minh để bên kia xếp hàng chờ. Cách này tiết kiệm bộ nhớ cho
trường hợp phổ biến nhất (chèn mà không ai tranh chấp).

## 5. Mỗi câu lệnh khoá gì

### 5.1 Bảng tổng hợp (Repeatable Read)

Theo manual mục *Locks Set by Different SQL Statements in InnoDB*:

| Câu lệnh | Lock |
|---|---|
| `SELECT ...` thường | Không lock (consistent read); trừ Serializable |
| `SELECT ... FOR SHARE` / `FOR UPDATE` | S / X next-key lock trên mọi bản ghi index quét qua. Unique index với điều kiện tìm đúng một dòng: chỉ record lock |
| `UPDATE ... WHERE` / `DELETE ... WHERE` | X next-key lock trên mọi bản ghi quét qua. Unique index tìm đúng một dòng: chỉ record lock |
| `INSERT` | Insert intention trước khi chèn; sau đó X record lock (không gap) trên dòng mới |
| `INSERT` gặp trùng khoá (lỗi 1062) | **S lock** trên bản ghi bị trùng (nguồn của một kiểu deadlock, mục 10.4) |
| `INSERT ... ON DUPLICATE KEY UPDATE` gặp trùng | X record lock nếu trùng primary key; X next-key lock nếu trùng unique key khác |
| `REPLACE` gặp trùng | X next-key lock trên dòng bị thay |
| `INSERT INTO T SELECT ... FROM S` | X record lock trên dòng chèn vào `T`; S next-key lock trên dòng đọc từ `S` (ở Read Committed thì đọc `S` không lock) |
| Kiểm tra khoá ngoại khi insert/update/delete | S record lock trên bản ghi được kiểm tra (kể cả khi kiểm tra thất bại) |

⚠️ Dòng `INSERT INTO T SELECT ... FROM S` hay bị bỏ qua: câu "sao chép dữ liệu" này đặt S lock lên
các dòng nguồn, nên có thể chặn người đang ghi vào bảng nguồn. Manual giải thích lý do: binlog dạng
statement phải chạy lại được y hệt khi phục hồi.

### 5.2 Ví dụ trên bảng members

Cách xem lock của chính mình: trong session đang giữ transaction, chạy

```sql
SELECT INDEX_NAME, LOCK_TYPE, LOCK_MODE, LOCK_STATUS, LOCK_DATA
FROM performance_schema.data_locks
WHERE OBJECT_SCHEMA = 'ch15' AND OBJECT_NAME = 'members';
```

Cách đọc cột `LOCK_MODE` của InnoDB: manual liệt kê `S`, `X`, `IS`, `IX` có thể kèm `,GAP`; khi chạy
thật bạn còn gặp `,REC_NOT_GAP` và `,INSERT_INTENTION` (mã nguồn InnoDB ghép tên mode với các cờ
`GAP`, `REC_NOT_GAP`, `INSERT_INTENTION` thành chuỗi này).

| `LOCK_MODE` | Nghĩa |
|---|---|
| `X` hoặc `S` (không có gì thêm) | Next-key lock |
| `X,REC_NOT_GAP` | Record lock |
| `X,GAP` | Gap lock (khoảng ngay trước bản ghi ở `LOCK_DATA`) |
| `X,GAP,INSERT_INTENTION` | Insert intention, thường thấy ở trạng thái `WAITING` |
| `IX`, `IS` (`LOCK_TYPE = TABLE`) | Intention lock mức bảng |

`LOCK_DATA` của PRIMARY là giá trị primary key; của secondary index là `giá trị index, primary key`;
lock trên supremum hiện `supremum pseudo-record`.

Bốn trường hợp, mỗi trường hợp chạy trong một transaction mới rồi `ROLLBACK`. Output dưới đây là
**output minh hoạ** dựng theo quy tắc của manual, không chụp từ server thật; chi tiết có thể khác giữa
các bản 8.x, hãy tự chạy để kiểm tra.

**(a) Unique index, dòng tồn tại:**

```sql
START TRANSACTION;
SELECT * FROM members WHERE id = 20 FOR UPDATE;
-- output minh hoạ
-- INDEX_NAME | LOCK_TYPE | LOCK_MODE     | LOCK_DATA
-- NULL       | TABLE     | IX            | NULL
-- PRIMARY    | RECORD    | X,REC_NOT_GAP | 20
ROLLBACK;
```

Chỉ record lock: không ai sửa được id 20, nhưng chèn id 15, 25 vẫn được.

**(b) Unique index, dòng không tồn tại:**

```sql
START TRANSACTION;
SELECT * FROM members WHERE id = 15 FOR UPDATE;    -- rỗng
-- output minh hoạ
-- PRIMARY    | RECORD    | X,GAP         | 20         <- gap (10, 20)
ROLLBACK;
```

Không có dòng để khoá, InnoDB khoá khoảng chứa id 15, tức khe trước bản ghi 20. Người khác chèn id 11
tới 19 phải chờ; chèn id 25 thì được. Tương tự, `WHERE id = 35 FOR UPDATE` khoá khoảng sau 30
(`LOCK_DATA = supremum pseudo-record`), chặn mọi insert id lớn hơn 30.

**(c) Index không unique, điều kiện bằng:**

```sql
START TRANSACTION;
SELECT * FROM members WHERE age = 30 FOR UPDATE;
-- output minh hoạ
-- idx_age    | RECORD    | X             | 30, 20     <- next-key: khe trước (30,20) và chính nó
-- PRIMARY    | RECORD    | X,REC_NOT_GAP | 20         <- dòng khớp, khoá trên clustered index
-- idx_age    | RECORD    | X,GAP         | 40, 30     <- gap trước (40,30)
ROLLBACK;
```

Vì `idx_age` không unique, có thể có nhiều dòng `age = 30`, nên InnoDB quét tiếp tới bản ghi đầu tiên
lớn hơn 30 (là 40) mới biết dừng, và khoá khe trước nó. Kết quả: chèn dòng có `age` 25 hay 35 đều phải
chờ, dù không dòng nào có `age = 30`; chèn `age = 45` thì được; `UPDATE members SET name = 'x' WHERE id = 30`
(dòng `age = 40`) cũng được, vì bản ghi `(40, 30)` chỉ bị khoá khe trước nó, không khoá chính nó.

Chi tiết tinh hơn: secondary index sắp theo `(age, id)`, nên biên của khoảng có cả primary key. Ví dụ
khe trước `(30, 20)` bắt đầu sau `(20, 10)`: chèn `(age 20, id 15)` rơi vào khe đó nên chờ, còn chèn
`(age 20, id 5)` đứng trước `(20, 10)` nên không chờ. Đừng cố nhớ, hãy xem `data_locks`.

**(d) Không có index:**

```sql
START TRANSACTION;
SELECT * FROM members WHERE name = 'Bình' FOR UPDATE;
-- output minh hoạ
-- PRIMARY    | RECORD    | X             | supremum pseudo-record
-- PRIMARY    | RECORD    | X             | 10
-- PRIMARY    | RECORD    | X             | 20
-- PRIMARY    | RECORD    | X             | 30
ROLLBACK;
```

Không có index trên `name`, phải quét toàn bộ clustered index, nên next-key lock trên mọi bản ghi và
supremum: cả bảng bị khoá với người ghi (mục 6).

### 5.3 Read Committed khác gì

Đổi level cho session: `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;`. Theo manual (mục
*Transaction Isolation Levels*), ở Read Committed:

1. Locking read, `UPDATE`, `DELETE` **chỉ khoá bản ghi, không khoá khe**. Gap lock chỉ còn dùng cho
   kiểm tra khoá ngoại và kiểm tra trùng khoá. Vì vậy người khác chèn được vào khoảng, và phantom có
   thể xuất hiện.
2. Lock trên các dòng **không khớp `WHERE`** được nhả ngay sau khi MySQL đánh giá điều kiện.
3. `UPDATE` dùng *semi-consistent read*: gặp dòng đang bị khoá, InnoDB đọc bản đã commit mới nhất để
   xét `WHERE`; không khớp thì bỏ qua, không phải chờ; khớp thì mới đọc lại và chờ lock.

Chạy lại bốn trường hợp ở mục 5.2 với Read Committed:

| Trường hợp | Repeatable Read | Read Committed |
|---|---|---|
| (a) `id = 20` | Record lock 20 | Record lock 20 |
| (b) `id = 15` (không có) | Gap (10, 20) | **Không lock gì** |
| (c) `age = 30` | Next-key (…, 30], gap trước 40, record PK 20 | Record lock `idx_age` (30,20) và PK 20 |
| (d) `name = 'Bình'` | Mọi dòng và supremum | Quét mọi dòng nhưng nhả ngay dòng không khớp; còn lại record lock PK 20 |

Đánh đổi: Read Committed ít chờ và ít deadlock hơn hẳn (không có gap lock), đổi lại mất bảo vệ chống
phantom và non-repeatable read (chương 14). Nhiều hệ thống lớn chạy MySQL ở Read Committed vì lý do
này. ⚠️ Ở Read Committed, MySQL chỉ cho binlog dạng row-based (`binlog_format = ROW`, mặc định).

### 5.4 Serializable

Ở `SERIALIZABLE`, khi autocommit tắt (tức là trong `START TRANSACTION`), InnoDB ngầm biến mọi
`SELECT` thường thành `SELECT ... FOR SHARE`: tìm kiếm đặt S next-key lock lên các bản ghi đi qua.
Người đọc chặn người ghi và ngược lại, nên tranh chấp và deadlock tăng mạnh. Chương 14 đã bàn khi nào
dùng.

### 5.5 Quy trình trả lời "câu này khoá gì"

1. Xác định index mà câu lệnh dùng: `EXPLAIN` (chương 12). `type: ALL` là quét cả bảng.
2. Liệt kê các bản ghi index mà nó quét, kể cả bản ghi đầu tiên vượt ra ngoài điều kiện.
3. Unique index, điều kiện bằng trên đủ cột, dòng tồn tại: record lock; dòng không tồn tại: chỉ gap
   lock trên khe chứa giá trị đó. Còn lại (Repeatable Read): next-key lock trên các bản ghi quét được;
   riêng với điều kiện bằng trên index không unique, bản ghi đầu tiên vượt ra ngoài điều kiện chỉ bị
   gap lock (như trường hợp (c)).
4. Cộng record lock trên clustered index cho các dòng khớp.
5. Read Committed: bỏ hết phần gap, nhả lock của dòng không khớp.
6. Kiểm chứng bằng `performance_schema.data_locks`, đừng đoán.

## 6. UPDATE/DELETE trên cột không có index: khoá cả bảng

Đây là cái bẫy gây sự cố thật nhiều nhất. Manual ghi: nếu không có index phù hợp và MySQL phải quét cả
bảng, **mọi dòng của bảng bị khoá**, chặn mọi insert của người khác. Bảng `members` không có index trên
`name`:

| Bước | Session A | Session B | Kết quả (Repeatable Read) |
|---|---|---|---|
| 1 | `START TRANSACTION;` `UPDATE members SET age = age + 1 WHERE name = 'An';` | | 1 dòng đổi (id 10). Nhưng A giữ next-key lock trên **mọi** bản ghi PRIMARY và supremum |
| 2 | | `START TRANSACTION;` `UPDATE members SET age = 99 WHERE id = 30;` | **B chờ**, dù dòng id 30 không liên quan gì tới 'An' |
| 3 | | (hoặc) `INSERT INTO members VALUES (40, 50, 'Dũng');` | Cũng chờ: khe trước supremum bị khoá |
| 4 | `COMMIT;` | | B chạy được |

Cùng kịch bản ở Read Committed (chạy `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;` ở cả
hai session trước): A vẫn quét cả bảng, nhưng nhả lock của id 20, 30 ngay sau khi thấy không khớp, và
không có gap lock. Bước 2 và 3 của B chạy ngay.

Cách sửa đúng **không phải đổi isolation level** mà là thêm index cho cột trong `WHERE`:

```sql
ALTER TABLE members ADD INDEX idx_name (name);
```

Sau đó câu ở bước 1 chỉ khoá bản ghi `'An'` trong `idx_name` (cộng khe lân cận ở Repeatable Read) và
dòng id 10 trong PRIMARY. Thói quen tốt: trước khi đưa một câu `UPDATE`/`DELETE` lên production, chạy
`EXPLAIN UPDATE ...` (chương 12); thấy `type: ALL` là dấu hiệu nó sẽ khoá cả bảng.

⚠️ Các biến thể hay gặp của cùng cái bẫy:

- `UPDATE ... WHERE DATE(created_at) = '2026-10-01'`: bọc cột trong hàm làm index không dùng được
  (chương 11), quay về quét cả bảng.
- So sánh khác kiểu, ví dụ cột `VARCHAR` so với số (`WHERE phone = 912345678`), MySQL ép kiểu từng dòng
  nên không dùng index.
- `DELETE FROM logs WHERE created_at < ...` trên bảng lớn không có index `created_at`: khoá toàn bộ bảng
  trong suốt thời gian xoá. Có index rồi vẫn nên xoá theo lô nhỏ (`LIMIT 1000` lặp lại) để mỗi
  transaction ngắn.

## 7. Lock mức bảng và metadata lock

### 7.1 LOCK TABLES

`LOCK TABLES t READ` / `LOCK TABLES t WRITE` khoá cả bảng ở tầng server, tới khi `UNLOCK TABLES`. Với
InnoDB hầu như không cần dùng, row lock đã đủ. Vài điểm theo manual nếu gặp trong code cũ:

- `LOCK TABLES` gây commit ngầm transaction đang mở; không thể khoá thêm bảng giữa transaction.
- Khi `innodb_table_locks = 1` (mặc định), nó lấy thêm table lock trong InnoDB. Manual khuyên dùng với
  `autocommit = 0`, vì ở autocommit bật, table lock của InnoDB bị nhả ngay.
- InnoDB chỉ phát hiện được deadlock liên quan tới `LOCK TABLES` khi `innodb_table_locks = 1` và
  `autocommit = 0`; ngoài ra phải trông vào `innodb_lock_wait_timeout`.

### 7.2 AUTO-INC lock

Bảng có cột `AUTO_INCREMENT` cần cấp id duy nhất cho các insert chạy song song. Cách cấp do biến
`innodb_autoinc_lock_mode` quyết định; từ MySQL 8.0 mặc định là `2` (*interleaved*): không dùng lock
mức bảng, các câu insert cấp id xen kẽ nhau, nhanh nhất. Mode `0` và `1` dùng lock mức bảng đặc biệt
(`AUTO_INC` trong `data_locks`) cho cả câu (mode 0) hoặc cho các insert không biết trước số dòng như
`INSERT ... SELECT` (mode 1). Hệ quả cần nhớ: id có thể có lỗ (rollback không trả lại id đã cấp),
đừng dùng id để đếm dòng.

### 7.3 Metadata lock (MDL)

*Metadata lock* là lock của tầng MySQL server (không phải InnoDB) trên **định nghĩa** của bảng. Mọi
câu lệnh chạm vào bảng, kể cả `SELECT` thường, lấy MDL dạng shared và **giữ tới hết transaction**;
`ALTER TABLE`, `DROP`, `TRUNCATE` cần MDL exclusive. Kịch bản sự cố kinh điển: một transaction quên
commit giữ MDL shared, `ALTER TABLE` xếp hàng chờ exclusive, và mọi câu `SELECT` đến sau xếp hàng sau
`ALTER`, làm app treo. `NOWAIT`/`SKIP LOCKED` không giúp được vì chúng chỉ áp dụng cho row lock; thời
gian chờ MDL do `lock_wait_timeout` quyết định (khác `innodb_lock_wait_timeout`). Chi tiết, cách điều
tra và cách phòng ở [chương 20, mục 3](20-thay-doi-schema-migration.md#3-metadata-lock-và-lock_wait_timeout).

## 8. Pessimistic lock và optimistic lock

Có hai chiến lược đối lập để xử lý xung đột khi nhiều người sửa cùng dữ liệu:

- **Pessimistic lock** (bi quan): tin rằng xung đột sẽ xảy ra, nên **khoá trước khi đọc**
  (`SELECT ... FOR UPDATE`). Người đến sau chờ. Đây là những gì ta làm từ đầu chương.
- **Optimistic lock** (lạc quan): tin rằng xung đột hiếm, nên **không khoá gì khi đọc**; lúc ghi mới
  kiểm tra "từ lúc mình đọc, có ai sửa chưa". Có thì báo xung đột hoặc thử lại.

### 8.1 Cài optimistic lock bằng cột version

```sql
CREATE TABLE posts (
  id      INT PRIMARY KEY,
  body    TEXT NOT NULL,
  version INT  NOT NULL DEFAULT 1        -- tăng mỗi lần ghi
) ENGINE = InnoDB;
INSERT INTO posts (id, body) VALUES (1, 'Bản gốc');
```

Hai biên tập viên cùng mở form sửa bài 1:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `SELECT body, version FROM posts WHERE id = 1;` | | A thấy version 1. Không lock, không giữ transaction |
| 2 | | `SELECT body, version FROM posts WHERE id = 1;` | B cũng thấy version 1 |
| 3 | (người dùng A sửa 3 phút) | (người dùng B sửa 5 phút) | Không ai chờ ai, không connection nào bị giữ |
| 4 | `UPDATE posts SET body = 'Bản của A', version = version + 1 WHERE id = 1 AND version = 1;` | | 1 dòng bị ảnh hưởng, version thành 2 |
| 5 | | `UPDATE posts SET body = 'Bản của B', version = version + 1 WHERE id = 1 AND version = 1;` | **0 dòng**: điều kiện `version = 1` không còn đúng |
| 6 | | App báo "bài đã bị người khác sửa", cho B xem bản mới | Bản của A không bị đè |

Bước 5 đúng kể cả khi B đang ở trong transaction Repeatable Read đã đọc snapshot cũ, vì `UPDATE` luôn
xét `WHERE` trên bản mới nhất (locking read). Nếu A chưa commit ở bước 4 thì B chờ lock dòng, rồi vẫn
ra 0 dòng.

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

final class StaleWriteException extends RuntimeException {}

function savePost(int $id, string $body, int $versionDaDoc): void
{
    $affected = DB::table('posts')
        ->where('id', $id)
        ->where('version', $versionDaDoc)
        ->update(['body' => $body, 'version' => DB::raw('version + 1')]);

    if ($affected !== 1) {           // BẮT BUỘC kiểm tra, không thì optimistic lock vô nghĩa
        throw new StaleWriteException('Bài đã bị người khác sửa');
    }
}
```

Cạm bẫy:

- ⚠️ Quên kiểm tra số dòng bị ảnh hưởng là lỗi phổ biến nhất. Với MySQL, PDO mặc định trả số dòng *thật
  sự thay đổi* chứ không phải số dòng *khớp* `WHERE`; có `version = version + 1` thì dòng luôn thay đổi
  nên không sao.
- ⚠️ Dùng `updated_at` làm version là rủi ro: độ phân giải thời gian và đồng hồ lệch giữa các máy có thể
  cho hai lần ghi cùng giá trị. Dùng số nguyên.
- Mọi đường ghi vào bảng (job, script sửa dữ liệu, admin) đều phải tăng version.

Đối chiếu: JPA/Hibernate có sẵn `@Version` và ném `OptimisticLockException` khi 0 dòng; Eloquent không
có sẵn, phải tự viết điều kiện như trên.

### 8.2 Chọn cách nào

Còn một cách thứ ba thường tốt nhất: **một câu `UPDATE` atomic có điều kiện**, ví dụ trừ kho
`UPDATE products SET stock = stock - 1 WHERE id = ? AND stock >= 1`. Câu này cũng lấy X lock nhưng chỉ
trong vài mili giây của chính nó.

| Tiêu chí | `UPDATE` atomic có điều kiện | Pessimistic (`FOR UPDATE`) | Optimistic (`version`) |
|---|---|---|---|
| Logic | Diễn đạt được trong một câu SQL | Tuỳ ý, tính ở app | Tuỳ ý, tính ở app |
| Khoá | Trong một câu | Từ lúc đọc tới commit | Không khoá khi đọc |
| Tranh chấp cao (một sản phẩm flash sale) | Tốt nhất | Ổn, request xếp hàng | Tệ: đa số lần thử thất bại, tốn round-trip |
| Đọc và ghi cách nhau lâu (form sửa bài, qua nhiều request HTTP) | Không áp dụng | **Không được**: không thể giữ transaction qua nhiều request | Phù hợp nhất |
| Rủi ro | Quên kiểm tra affected rows | Lock wait, deadlock, transaction dài | Quên kiểm tra affected rows, đường ghi quên tăng version |

Quy tắc chọn: atomic trước; logic không gói được vào một câu thì pessimistic cho thao tác ngắn trong
một request; optimistic khi "đọc" và "ghi" cách nhau cả một lần tương tác của người dùng.

## 9. Chờ lock và innodb_lock_wait_timeout

Khi một câu phải chờ row lock, nó chờ tối đa `innodb_lock_wait_timeout` giây; **mặc định 50**. Biến
này đổi được cho từng session (`SET SESSION innodb_lock_wait_timeout = 5;`) và theo manual chỉ áp
dụng cho row lock của InnoDB, không áp dụng cho table lock của tầng server. Quá hạn thì nhận:

```
ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction
```

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `UPDATE accounts SET balance = balance - 10 WHERE id = 1;` | | A giữ X dòng 1 và "quên" commit |
| 2 | | `SET SESSION innodb_lock_wait_timeout = 5;` `START TRANSACTION;` `UPDATE accounts SET balance = balance + 100 WHERE id = 2;` | Câu này chạy ngay |
| 3 | | `UPDATE accounts SET balance = balance - 100 WHERE id = 1;` | Chờ A; sau 5 giây: `ERROR 1205` |
| 4 | | `SELECT balance FROM accounts WHERE id = 2;` | Thấy **400.00**: câu ở bước 2 vẫn còn, transaction B vẫn mở |
| 5 | | `ROLLBACK;` | Đúng cách xử lý |
| 6 | `ROLLBACK;` | | |

⚠️ Khác biệt lớn với deadlock: mặc định lock wait timeout **chỉ rollback câu lệnh đang chờ**, không
rollback cả transaction (biến `innodb_rollback_on_timeout` mặc định `OFF`; bật thì rollback cả
transaction, nhưng phải đặt lúc khởi động server). Nếu ở bước 5 app gọi `COMMIT`, tài khoản 2 được cộng
100 mà tài khoản 1 không bị trừ. Chương 13 mục 5.1 đã nói kỹ; quy tắc là **gặp 1205 thì `ROLLBACK` cả
transaction**.

50 giây là quá dài với request web: người dùng đã bỏ đi mà connection và PHP worker vẫn bị giữ. Nhiều
hệ thống đặt vài giây cho session của web app và giữ mặc định cho job chạy nền. Lock wait timeout xảy
ra thường xuyên là triệu chứng: có transaction giữ lock quá lâu. Tìm thủ phạm bằng mục 11 thay vì chỉ
tăng timeout.

## 10. Deadlock

### 10.1 Deadlock là gì: ví dụ chuyển tiền ngược chiều

*Deadlock* (khoá chết) là vòng chờ: A giữ thứ B cần, B giữ thứ A cần, không ai đi tiếp được và chờ bao
lâu cũng không tự gỡ. Kịch bản phổ biến nhất: hai transaction khoá cùng các dòng **theo thứ tự ngược
nhau**. A chuyển 100 từ tài khoản 1 sang 2, cùng lúc B chuyển 50 từ 2 sang 1:

| Bước | Session A (1 → 2) | Session B (2 → 1) | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `UPDATE accounts SET balance = balance - 100 WHERE id = 1;` | | A giữ X dòng 1 |
| 2 | | `START TRANSACTION;` `UPDATE accounts SET balance = balance - 50 WHERE id = 2;` | B giữ X dòng 2 |
| 3 | `UPDATE accounts SET balance = balance + 100 WHERE id = 2;` | | A chờ B (dòng 2) |
| 4 | | `UPDATE accounts SET balance = balance + 50 WHERE id = 1;` | B chờ A (dòng 1): vòng khép lại. InnoDB phát hiện ngay, chọn một bên làm *victim* (giả sử B): `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction` |
| 5 | (câu ở bước 3 chạy xong) | | Toàn bộ transaction B đã bị rollback, kể cả câu ở bước 2, nên lock dòng 2 được nhả |
| 6 | `COMMIT;` | App chạy lại cả transaction B | Lần chạy lại thành công. Cuối cùng: dòng 1 = 450.00, dòng 2 = 350.00, tổng vẫn 800.00 |

Bên nào bị chọn làm victim không đoán trước được; khi tự chạy, có thể là A.

### 10.2 InnoDB phát hiện và xử lý deadlock thế nào

1. **Phát hiện ngay**: mỗi khi một transaction phải chờ lock, InnoDB kiểm tra *wait-for graph* (đồ thị
   "ai chờ ai") xem có tạo thành vòng không. Bật bằng `innodb_deadlock_detect`, mặc định `ON`.
2. **Chọn victim**: manual ghi InnoDB cố chọn transaction **nhỏ** để rollback, kích thước đo bằng số
   dòng đã insert, update, delete. Mục đích: rollback rẻ nhất.
3. **Rollback cả transaction victim** và trả lỗi `1213` (SQLSTATE `40001`). Đây là điểm khác lỗi 1205:
   deadlock rollback **toàn bộ** transaction, lock wait timeout mặc định chỉ rollback **một câu**.
4. **Giới hạn**: nếu danh sách chờ vượt 200 transaction, hoặc thread kiểm tra phải xem hơn 1.000.000
   lock của các transaction trong danh sách, InnoDB coi luôn là deadlock và rollback transaction đang
   kiểm tra (log ghi `TOO DEEP OR LONG SEARCH IN THE LOCK TABLE WAITS-FOR GRAPH`).
5. **Tắt phát hiện**: trên hệ thống rất nhiều luồng cùng chờ một dòng nóng, chính việc duyệt đồ thị
   làm chậm. Manual cho phép tắt `innodb_deadlock_detect` và dựa vào `innodb_lock_wait_timeout`; khi đó
   deadlock thật phải chờ đủ timeout mới gỡ, nên chỉ làm khi đã đo đạc và đặt timeout ngắn.

Manual coi deadlock là chuyện bình thường của database có transaction, không phải lỗi nghiêm trọng,
miễn là không quá thường xuyên. Ứng dụng phải luôn sẵn sàng chạy lại transaction (mục 10.7).

### 10.3 Deadlock do gap lock: "kiểm tra chưa có thì tạo"

Không cần hai dòng ngược thứ tự. Mẫu code hay gặp: kiểm tra một id chưa tồn tại bằng `FOR UPDATE` "cho
chắc", rồi insert. Ở Repeatable Read, với `members` có id 10, 20, 30:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT * FROM members WHERE id = 15 FOR UPDATE;` | | Rỗng. A giữ gap lock (10, 20) |
| 2 | | `START TRANSACTION;` `SELECT * FROM members WHERE id = 15 FOR UPDATE;` | Rỗng. B **cũng** giữ gap lock (10, 20): gap lock không xung đột nhau |
| 3 | App A thấy chưa có: `INSERT INTO members VALUES (15, 25, 'Dũng');` | | Insert intention của A bị gap lock của B chặn: **A chờ B** |
| 4 | | App B thấy chưa có: `INSERT INTO members VALUES (15, 25, 'Dũng');` | B bị gap lock của A chặn: vòng chờ. Một bên nhận `ERROR 1213` (giả sử B) |
| 5 | (insert ở bước 3 chạy xong) `COMMIT;` | | A tạo được dòng 15. B chạy lại thì thấy dòng đã có |

Vì sao `FOR UPDATE` "khoá cho chắc" lại hại: nó không khoá được thứ chưa tồn tại, chỉ khoá được khoảng,
mà khoảng thì ai cũng khoá cùng lúc được. Nó không tạo ra loại trừ lẫn nhau như người viết mong.

Cách sửa, theo thứ tự nên thử:

1. **Để unique constraint làm việc**: bỏ `SELECT ... FOR UPDATE`, insert thẳng. Bên đến sau nhận lỗi
   `1062 Duplicate entry` (bắt lỗi rồi đọc lại), hoặc dùng một câu nguyên tử
   `INSERT ... ON DUPLICATE KEY UPDATE`. Lưu ý câu này vẫn lấy X lock trên dòng trùng (mục 5.1) nên vẫn
   có thể deadlock khi chạy rất dày, chỉ hiếm hơn nhiều.
2. **Read Committed** cho loại transaction này: không có gap lock ở bước 1, 2. B sẽ chờ ở bước 4 (kiểm
   tra trùng khoá) rồi nhận lỗi 1062 sau khi A commit, không deadlock.
3. **Khoá một dòng có thật**: ví dụ khoá dòng cha `users.id = ?` bằng `FOR UPDATE` để mọi request của
   cùng một user xếp hàng trên một record lock.

### 10.4 Deadlock do lỗi trùng khoá

Ví dụ trong manual, không có `SELECT` nào, chỉ có `INSERT`:

```sql
CREATE TABLE t1 (i INT, PRIMARY KEY (i)) ENGINE = InnoDB;
```

| Bước | Session A | Session B | Session C | Kết quả |
|---|---|---|---|---|
| 1 | `START TRANSACTION;` `INSERT INTO t1 VALUES (1);` | | | A giữ X trên bản ghi 1 |
| 2 | | `START TRANSACTION;` `INSERT INTO t1 VALUES (1);` | | B phát hiện trùng, xin **S lock** trên bản ghi 1, chờ A |
| 3 | | | `START TRANSACTION;` `INSERT INTO t1 VALUES (1);` | C cũng xin S, chờ A |
| 4 | `ROLLBACK;` | | | A nhả X. B và C **cùng được S** |
| 5 | | (cần X để chèn) | (cần X để chèn) | Mỗi bên chờ S của bên kia: deadlock, một bên nhận 1213, bên còn lại chèn được |

Manual mô tả thêm biến thể với `DELETE`: A xoá dòng đang tồn tại, B và C insert cùng khoá, A commit, và
B, C deadlock theo cùng cách. Bài học: S lock sinh ra khi gặp lỗi trùng khoá là nguồn deadlock ngầm của
các bảng có unique key bị insert dồn dập.

### 10.5 Đọc LATEST DETECTED DEADLOCK

Lệnh `SHOW ENGINE INNODB STATUS\G` in ra nhiều mục; mục `LATEST DETECTED DEADLOCK` mô tả **deadlock
gần nhất** (chỉ một). Output minh hoạ (dựng tay theo định dạng MySQL 8.x, đã lược bớt dòng) cho kịch
bản chuyển tiền ở mục 10.1:

```
------------------------
LATEST DETECTED DEADLOCK
------------------------
2026-10-25 09:12:44 140213774579264
*** (1) TRANSACTION:
TRANSACTION 4891, ACTIVE 12 sec starting index read
mysql tables in use 1, locked 1
LOCK WAIT 3 lock struct(s), heap size 1128, 2 row lock(s), undo log entries 1
MySQL thread id 12, OS thread handle 140213700000000, query id 87 localhost root updating
UPDATE accounts SET balance = balance + 100 WHERE id = 2

*** (1) HOLDS THE LOCK(S):
RECORD LOCKS space id 7 page no 4 n bits 72 index PRIMARY of table `ch15`.`accounts` trx id 4891 lock_mode X locks rec but not gap
Record lock, heap no 2 PHYSICAL RECORD: n_fields 5; compact format; info bits 0
 0: len 4; hex 80000001; asc     ;;
 ...

*** (1) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 7 page no 4 n bits 72 index PRIMARY of table `ch15`.`accounts` trx id 4891 lock_mode X locks rec but not gap waiting
Record lock, heap no 3 PHYSICAL RECORD: n_fields 5; compact format; info bits 0
 0: len 4; hex 80000002; asc     ;;
 ...

*** (2) TRANSACTION:
TRANSACTION 4892, ACTIVE 8 sec starting index read
mysql tables in use 1, locked 1
LOCK WAIT 3 lock struct(s), heap size 1128, 2 row lock(s), undo log entries 1
MySQL thread id 13, OS thread handle 140213700000001, query id 88 localhost root updating
UPDATE accounts SET balance = balance + 50 WHERE id = 1

*** (2) HOLDS THE LOCK(S):
RECORD LOCKS space id 7 page no 4 n bits 72 index PRIMARY of table `ch15`.`accounts` trx id 4892 lock_mode X locks rec but not gap
 0: len 4; hex 80000002; asc     ;;

*** (2) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS space id 7 page no 4 n bits 72 index PRIMARY of table `ch15`.`accounts` trx id 4892 lock_mode X locks rec but not gap waiting
 0: len 4; hex 80000001; asc     ;;

*** WE ROLL BACK TRANSACTION (2)
```

Đọc theo từng bước:

1. **Mỗi transaction**: `ACTIVE 12 sec` là đã mở bao lâu (lâu bất thường là dấu hiệu transaction ôm
   việc chậm); `2 row lock(s)` là số row lock đang giữ; `MySQL thread id 12` đối chiếu được với
   `SHOW PROCESSLIST` và log của app.
2. **Câu SQL** ngay dưới là câu đang chạy lúc deadlock.
3. **HOLDS THE LOCK(S)**: đang giữ gì, trên index nào của bảng nào. **WAITING FOR THIS LOCK**: đang
   chờ gì.
4. **Giải mã giá trị**: trường `0:` là cột đầu của index, ở đây PK kiểu `INT` (4 byte). InnoDB lưu số
   nguyên có dấu với bit dấu bị đảo, nên `80000001` là 1, `80000002` là 2. Gặp `supremum` là khoảng
   sau giá trị lớn nhất.
5. **Ghép vòng**: (1) giữ dòng 1, chờ dòng 2; (2) giữ dòng 2, chờ dòng 1. Đúng mẫu ngược thứ tự.
6. **WE ROLL BACK TRANSACTION (2)**: victim là (2), app của thread 13 nhận lỗi 1213.

Các chuỗi `lock_mode` hay gặp:

| Chuỗi trong log | Nghĩa |
|---|---|
| `lock_mode X locks rec but not gap` | Record lock X |
| `lock mode S locks rec but not gap` | Record lock S (từ `FOR SHARE`, kiểm tra khoá ngoại, lỗi trùng khoá) |
| `lock_mode X` (không có gì thêm) | Next-key lock X |
| `lock_mode X locks gap before rec` | Gap lock |
| `lock_mode X locks gap before rec insert intention waiting` | Insert đang chờ vì gap lock của người khác (mẫu ở mục 10.3) |

⚠️ Log chỉ in **câu đang chạy** của mỗi transaction, không in các câu trước đó. Lock ở mục HOLDS
thường do một câu chạy trước trong cùng transaction (ở trên là câu trừ tiền bước 1, log không hề nhắc).
Muốn biết đủ phải đối chiếu với code, hoặc xem `performance_schema.events_statements_history` của
thread đó.

Vì mục này chỉ giữ deadlock gần nhất, trên production nên bật:

```sql
SET PERSIST innodb_print_all_deadlocks = ON;   -- mặc định OFF; ghi mọi deadlock vào error log
```

Đếm số deadlock từ lúc khởi động:

```sql
SELECT NAME, COUNT FROM information_schema.INNODB_METRICS WHERE NAME = 'lock_deadlocks';
```

### 10.6 Giảm deadlock

Không loại bỏ được hoàn toàn, chỉ giảm tần suất. Các cách theo manual mục *How to Minimize and Handle
Deadlocks*, xếp theo hiệu quả thường gặp:

1. **Khoá theo một thứ tự cố định.** Ở mục 10.1, nếu cả hai luôn cập nhật tài khoản có id nhỏ trước
   (sắp xếp id trước khi chạy), B sẽ chờ ngay ở câu đầu tiên và không có vòng. Với đơn hàng nhiều sản
   phẩm: sort id sản phẩm trước khi trừ kho.
2. **Transaction ngắn và ít dòng**, commit ngay khi xong; không gọi API, không chờ người dùng khi đang
   giữ lock (chương 13 mục 10).
3. **Index đúng** cho `WHERE` của `UPDATE`, `DELETE`, `FOR UPDATE` để khoá ít bản ghi nhất (mục 6).
4. **Bớt locking read** khi không cần; dùng `UPDATE` atomic có điều kiện thay cho đọc rồi ghi.
5. **Read Committed** nếu chấp nhận được: không có gap lock nên không có deadlock kiểu mục 10.3.
6. Với `FOR SHARE` rồi sửa: đổi thành `FOR UPDATE` (mục 3.3).
7. Cách cuối cùng (manual có nêu): tuần tự hoá bằng lock mức bảng hoặc một dòng "semaphore" mà mọi
   transaction phải khoá trước, đổi lấy mất song song.

### 10.7 Retry trong ứng dụng

Quy tắc: gặp **1213** thì transaction đã bị rollback hết, chạy lại **cả transaction từ câu đầu tiên**
(đọc lại dữ liệu mới, không dùng lại giá trị cũ). Gặp **1205** thì tự `ROLLBACK` rồi mới quyết định
chạy lại. Giới hạn số lần, chờ ngắn ngẫu nhiên giữa các lần để hai bên không đụng nhau lần nữa.

Với PDO thuần:

```php
<?php
declare(strict_types=1);

/** Chạy $work trong transaction, thử lại khi deadlock (1213) hoặc lock wait timeout (1205). */
function withRetry(PDO $pdo, callable $work, int $maxAttempts = 3): mixed
{
    for ($attempt = 1; ; $attempt++) {
        $pdo->beginTransaction();
        try {
            $result = $work($pdo);
            $pdo->commit();
            return $result;
        } catch (Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();                    // luôn rollback cả transaction, kể cả với 1205
            }
            $code = $e instanceof PDOException ? (int) ($e->errorInfo[1] ?? 0) : 0;
            if (!in_array($code, [1213, 1205], true) || $attempt >= $maxAttempts) {
                throw $e;
            }
            usleep(random_int(10_000, 50_000) * $attempt);   // backoff tăng dần, có jitter
        }
    }
}

// Chuyển tiền: khoá theo thứ tự id tăng dần để giảm deadlock, retry để xử lý phần còn lại
function transfer(PDO $pdo, int $from, int $to, string $amount): void
{
    withRetry($pdo, function (PDO $pdo) use ($from, $to, $amount): void {
        $ids = [$from, $to];
        sort($ids);
        $lock = $pdo->prepare('SELECT id FROM accounts WHERE id IN (?, ?) ORDER BY id FOR UPDATE');
        $lock->execute($ids);
        $pdo->prepare('UPDATE accounts SET balance = balance - ? WHERE id = ?')->execute([$amount, $from]);
        $pdo->prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?')->execute([$amount, $to]);
    });
}
```

Với Laravel, tham số thứ hai của `DB::transaction` là số lần thử (mặc định 1, tức không retry):

```php
DB::transaction(function (): void {
    // ...
}, attempts: 3);
```

Laravel chạy lại closure khi lỗi được nhận là lỗi tranh chấp (SQLSTATE `40001` hoặc thông điệp như
"Deadlock found", "Lock wait timeout exceeded"), và chỉ retry ở transaction ngoài cùng. ⚠️ Closure có
thể chạy nhiều lần, nên mọi tác dụng phụ ngoài database (gửi email, gọi API) phải đặt sau commit. Phân
loại lỗi nào được retry, mất kết nối lúc commit: [chương 19, mục 5.4](19-database-tu-ung-dung.md#54-retry-lỗi-nào-được-chạy-lại).

## 11. Xem ai đang giữ lock, ai đang chờ

Khi app báo chậm hoặc lỗi 1205, cần trả lời: ai đang chờ, ai đang chặn, chặn bằng lock gì. MySQL 8.x
có ba nguồn (Performance Schema bật mặc định):

| Nguồn | Cho biết |
|---|---|
| `performance_schema.data_locks` | Mọi lock InnoDB đang giữ hoặc đang chờ (`LOCK_STATUS` là `GRANTED` hoặc `WAITING`) |
| `performance_schema.data_lock_waits` | Cặp "yêu cầu đang chờ" và "lock đang chặn nó" |
| `sys.innodb_lock_waits` | View gom sẵn hai bảng trên cùng `information_schema.INNODB_TRX`, kèm câu `KILL` gợi ý |

Tái hiện: chạy lại timeline ở mục 2.4 tới bước 4 (B đang chờ A), rồi mở session thứ ba:

```sql
SELECT wait_age, locked_table_schema, locked_table_name, locked_index, locked_type,
       waiting_pid, waiting_query, waiting_lock_mode,
       blocking_pid, blocking_query, blocking_lock_mode,
       sql_kill_blocking_connection
FROM sys.innodb_lock_waits\G
```

Output minh hoạ:

```
*************************** 1. row ***************************
                    wait_age: 00:00:07
         locked_table_schema: ch15
           locked_table_name: accounts
                locked_index: PRIMARY
                 locked_type: RECORD
                 waiting_pid: 13
               waiting_query: UPDATE accounts SET balance = balance + 10 WHERE id = 1
           waiting_lock_mode: X,REC_NOT_GAP
                blocking_pid: 12
              blocking_query: NULL
          blocking_lock_mode: X,REC_NOT_GAP
sql_kill_blocking_connection: KILL 12
```

⚠️ `blocking_query: NULL` là chuyện thường gặp: transaction chặn đang **rảnh** giữa hai câu (đã chạy
`UPDATE` rồi để đó, không commit), nên không có câu nào đang chạy. Trong `SHOW PROCESSLIST` nó hiện
`Command = Sleep`. Đây đúng là hình ảnh của "transaction quên commit".

Muốn xem chi tiết từng lock thì join trực tiếp:

```sql
SELECT w.REQUESTING_ENGINE_TRANSACTION_ID AS waiting_trx,
       w.BLOCKING_ENGINE_TRANSACTION_ID   AS blocking_trx,
       r.INDEX_NAME, r.LOCK_MODE AS waiting_mode, b.LOCK_MODE AS blocking_mode, r.LOCK_DATA
FROM performance_schema.data_lock_waits w
JOIN performance_schema.data_locks r ON r.ENGINE_LOCK_ID = w.REQUESTING_ENGINE_LOCK_ID
JOIN performance_schema.data_locks b ON b.ENGINE_LOCK_ID = w.BLOCKING_ENGINE_LOCK_ID;
```

Tìm transaction mở lâu (thủ phạm thường gặp nhất):

```sql
SELECT trx_id, trx_state, trx_started, trx_mysql_thread_id,
       trx_rows_locked, trx_rows_modified, trx_query
FROM information_schema.INNODB_TRX
ORDER BY trx_started
LIMIT 10;
```

Xử lý khẩn cấp: `KILL <thread id>` ngắt connection của transaction chặn; InnoDB rollback transaction
đó (rollback có thể mất thời gian nếu nó đã sửa nhiều dòng). Sau đó phải tìm trong code vì sao
transaction bị bỏ mở. Lưu ý `data_locks` có thể rất lớn khi có transaction khoá hàng triệu dòng; truy
vấn nó trên production nên có `WHERE` và `LIMIT`.

## 12. Đối chiếu PostgreSQL

| Khía cạnh | MySQL InnoDB | PostgreSQL |
|---|---|---|
| Locking read | `FOR SHARE`, `FOR UPDATE` | `FOR KEY SHARE`, `FOR SHARE`, `FOR NO KEY UPDATE`, `FOR UPDATE` (4 mức) |
| `UPDATE` khoá dòng | X | `FOR NO KEY UPDATE` nếu không sửa cột khoá, nên không chặn kiểm tra khoá ngoại (`FOR KEY SHARE`) của bảng con |
| `NOWAIT`, `SKIP LOCKED` | Có (8.0) | Có (9.5) |
| Gap lock, next-key lock | Có, ở Repeatable Read và Serializable | **Không có**. Repeatable Read chặn phantom bằng snapshot; Serializable dùng *predicate lock* (SIRead) chỉ để phát hiện xung đột, không gây chờ |
| Ghi đụng dòng đã bị transaction khác sửa và commit | Repeatable Read: chờ rồi ghi đè lên bản mới nhất | Repeatable Read/Serializable: lỗi `40001` (*could not serialize access*), app phải retry |
| Lưu row lock ở đâu | Cấu trúc lock trong bộ nhớ | Trên chính tuple (header), không giới hạn số dòng khoá |
| Phát hiện deadlock | Ngay khi bắt đầu chờ (`innodb_deadlock_detect`) | Sau khi đã chờ `deadlock_timeout` (mặc định 1 giây) |
| Lỗi deadlock | 1213, SQLSTATE `40001` | SQLSTATE `40P01` (`deadlock_detected`) |
| Thời gian chờ row lock | `innodb_lock_wait_timeout` mặc định 50 giây | `lock_timeout` mặc định 0 (chờ mãi) |
| Xem lock | `performance_schema.data_locks`, `sys.innodb_lock_waits` | `pg_locks`, hàm `pg_blocking_pids(pid)` |
| Khoá theo tên tuỳ ý | `GET_LOCK('ten', timeout)` | Advisory lock `pg_advisory_lock(key)` |

Hệ quả thực tế: mẫu "kiểm tra chưa có thì tạo" ở mục 10.3 không deadlock theo kiểu gap lock trên
Postgres, nhưng cũng không được bảo vệ: cả hai cùng thấy chưa có, một bên nhận lỗi trùng khoá ở
`INSERT`. Lời giải ở cả hai hệ giống nhau: dựa vào unique constraint và upsert
(`INSERT ... ON CONFLICT` ở Postgres). Lời khuyên giảm deadlock (thứ tự cố định, transaction ngắn,
retry) áp dụng y nguyên.

## Lỗi thường gặp

| Lỗi | Hậu quả | Cách đúng |
|---|---|---|
| `SELECT ... FOR UPDATE` ngoài transaction (autocommit) | Lock nhả ngay, không bảo vệ gì | Bọc trong `START TRANSACTION` / `DB::transaction` |
| Tin rằng lock chặn được `SELECT` thường | Code khác đọc snapshot rồi ghi đè, lost update vẫn xảy ra | Mọi đường đọc-để-ghi đều phải khoá, hoặc dùng `UPDATE` có điều kiện |
| `FOR SHARE` rồi `UPDATE` chính dòng đó | Deadlock khi hai request chạy cùng lúc | Đọc để sửa thì `FOR UPDATE` |
| `UPDATE`/`DELETE` theo cột không có index | Khoá cả bảng, mọi người ghi phải chờ | Thêm index; kiểm tra `EXPLAIN` trước |
| "Kiểm tra chưa có thì tạo" bằng `FOR UPDATE` | Deadlock do gap lock | Unique constraint + insert/upsert, bắt lỗi 1062 |
| Gặp 1205 rồi vẫn `COMMIT` | Commit nửa transaction | Luôn `ROLLBACK` cả transaction |
| Không retry khi gặp 1213 | Request lỗi ngẫu nhiên dưới tải | Retry cả transaction, giới hạn số lần, có backoff |
| Retry chỉ câu lệnh lỗi thay vì cả transaction | Các câu trước đã bị rollback, dữ liệu thiếu | Chạy lại từ đầu transaction |
| Tăng `innodb_lock_wait_timeout` để "hết lỗi" | Request treo lâu hơn, gốc vẫn còn | Tìm transaction giữ lock lâu (mục 11) |
| Khoá các dòng theo thứ tự tuỳ ý | Deadlock khi hai luồng đi ngược thứ tự | Sắp xếp id trước khi khoá |
| Optimistic lock mà không kiểm tra affected rows | Ghi đè im lặng | Luôn kiểm tra `=== 1` |
| Chỉ xem `LATEST DETECTED DEADLOCK` | Mất dấu các deadlock cũ | Bật `innodb_print_all_deadlocks` |

## Tóm tắt chương

- Lock giải quyết xung đột ghi với ghi; MVCC giải quyết đọc với ghi. `SELECT` thường không lock, không
  chờ; lock chỉ bảo vệ khỏi những người cũng lock.
- S tương thích S; X xung đột với mọi thứ. Row lock giữ tới hết transaction.
- Locking read: `FOR SHARE` (giữ nguyên), `FOR UPDATE` (để sửa), đọc bản mới nhất, phải nằm trong
  transaction. `NOWAIT` báo lỗi 3572 ngay; `SKIP LOCKED` bỏ qua dòng bị khoá, hợp cho hàng đợi job.
- InnoDB khoá bản ghi index đã quét: record lock, gap lock (chỉ chặn insert, không xung đột nhau),
  next-key lock (record + khe trước, mặc định ở Repeatable Read), insert intention (bị gap chặn).
  Intention lock IS/IX mức bảng tương thích nhau, chỉ chặn khoá cả bảng.
- Unique index tìm đúng một dòng có tồn tại: chỉ record lock. Không có index: khoá cả bảng.
- Read Committed bỏ gap lock và nhả lock dòng không khớp: ít chờ, ít deadlock, chấp nhận phantom.
- Atomic `UPDATE` có điều kiện trước; pessimistic cho logic phức tạp trong một request; optimistic
  (`version`) khi đọc và ghi cách nhau lâu.
- Deadlock: InnoDB phát hiện ngay, rollback cả transaction victim (1213). Lock wait timeout (1205, mặc
  định 50 giây) chỉ rollback một câu. Gặp cả hai: rollback, rồi retry cả transaction.
- Giảm deadlock: thứ tự khoá cố định, transaction ngắn, index đúng, Read Committed khi được.
- Chẩn đoán: `SHOW ENGINE INNODB STATUS` (deadlock gần nhất), `innodb_print_all_deadlocks`,
  `performance_schema.data_locks`, `data_lock_waits`, `sys.innodb_lock_waits`, `INNODB_TRX`.

## Câu hỏi tự kiểm tra

1. Vì sao MVCC không đủ để hai transaction cùng sửa một dòng một cách an toàn?
2. Session A đang giữ X trên dòng id 1. Session B chạy `SELECT * FROM accounts WHERE id = 1;` (không
   có `FOR ...`). B có chờ không? Nếu B chạy `... FOR SHARE` thì sao?
3. Một đoạn code gọi `SELECT ... FOR UPDATE` mà không mở transaction, chạy trên MySQL với autocommit
   mặc định. Lock được giữ bao lâu?
4. Khác nhau giữa `NOWAIT` và `SKIP LOCKED`? Vì sao `SKIP LOCKED` không hợp cho báo cáo tài chính?
5. Gap lock "chỉ có tác dụng ngăn chặn" nghĩa là gì? Hai transaction có thể cùng giữ gap lock trên một
   khoảng không?
6. Với `members` (id 10, 20, 30), ở Repeatable Read, `SELECT * FROM members WHERE id = 25 FOR UPDATE;`
   khoá gì? Session khác chèn id 22 thì sao, chèn id 35 thì sao?
7. Vì sao IX và IX tương thích? Nếu chúng xung đột thì hệ quả là gì?
8. Vì sao `UPDATE` theo cột không có index lại chặn cả `INSERT` của người khác ở Repeatable Read? Read
   Committed thay đổi điều đó thế nào?
9. Khi nào chọn optimistic lock thay vì `FOR UPDATE`? Khi nào ngược lại?
10. Phạm vi rollback của lỗi 1213 và 1205 khác nhau thế nào? Ứng dụng nên xử lý hai lỗi ra sao?
11. Trong log `LATEST DETECTED DEADLOCK`, vì sao không thấy câu lệnh đã lấy lock ở mục HOLDS?
12. Trong `sys.innodb_lock_waits`, `blocking_query` là `NULL` nói lên điều gì?
13. Vì sao mẫu "kiểm tra chưa có thì tạo" bằng `FOR UPDATE` deadlock trên MySQL Repeatable Read, mà
    trên PostgreSQL thì không deadlock kiểu đó?

## Bài tập

1. **Quan sát lock.** Với dữ liệu mẫu, ở Repeatable Read, lần lượt chạy (mỗi lần trong transaction
   mới) `SELECT ... FOR UPDATE` với các điều kiện `id = 20`, `id = 15`, `id = 35`, `age = 30`,
   `age BETWEEN 20 AND 30`, `name = 'Chi'`. Sau mỗi câu, ghi lại kết quả `performance_schema.data_locks`.
   Lặp lại ở Read Committed và lập bảng so sánh. Chỗ nào khác với output minh hoạ trong chương?
2. **Thử chèn.** Với `SELECT * FROM members WHERE age = 30 FOR UPDATE` đang giữ ở session A, ở session
   B thử chèn các dòng `(11, 20, 'x')`, `(5, 20, 'y')`, `(12, 35, 'z')`, `(13, 45, 'w')` với
   `innodb_lock_wait_timeout = 3`. Dòng nào chờ, dòng nào không? Giải thích bằng thứ tự `(age, id)`.
3. **Tái hiện deadlock.** Tái hiện ba deadlock ở mục 10.1, 10.3, 10.4. Sau mỗi lần, chép mục
   `LATEST DETECTED DEADLOCK`, chỉ ra mỗi transaction giữ gì, chờ gì, và giải mã giá trị hex.
4. **Hàng đợi job.** Viết script PHP (PDO) chạy worker lấy job bằng `FOR UPDATE SKIP LOCKED`, mở hai
   terminal chạy hai worker cùng lúc với 100 job, chứng minh không job nào bị xử lý hai lần. Thêm tác vụ
   trả job `running` quá 1 phút về `pending`.
5. **Sửa code.** Đoạn sau có ba vấn đề về lock. Chỉ ra và viết lại:

   ```php
   $pdo->query('SELECT stock FROM products WHERE sku = "A1" FOR SHARE');   // sku không có index
   $pdo->exec('UPDATE products SET stock = stock - 1 WHERE sku = "A1"');
   ```

6. **Optimistic lock.** Thêm cột `version` cho `accounts` và viết hàm PHP rút tiền kiểu optimistic,
   thử lại tối đa 5 lần. So sánh với phiên bản `FOR UPDATE` khi 20 request cùng rút một tài khoản.
7. **Điều tra.** Tạo tình huống session A giữ lock và bỏ đó, session B và C cùng chờ. Dùng
   `sys.innodb_lock_waits` và `INNODB_TRX` để tìm thủ phạm, rồi `KILL` nó. Ghi lại các bước.

## Đọc thêm

- [MySQL 8.4: InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)
- [MySQL 8.4: Locks Set by Different SQL Statements in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
- [MySQL 8.4: Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html)
- [MySQL 8.4: Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)
  (gồm *An InnoDB Deadlock Example*, *Deadlock Detection*, *How to Minimize and Handle Deadlocks*)
- [MySQL 8.4: The data_locks Table](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-data-locks-table.html)
- [MySQL 8.4: The innodb_lock_waits View (sys)](https://dev.mysql.com/doc/refman/8.4/en/sys-innodb-lock-waits.html)
- [PostgreSQL: Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)
- Bài đọc ôn phỏng vấn: [03-database-sql.md](../03-database-sql.md), module 2.6 và 3.2.
