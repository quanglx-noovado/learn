# Chương 13. Transaction và ACID

> [← Mục lục](README.md) · [← Chương 12: EXPLAIN và tối ưu truy vấn](12-explain-toi-uu-query.md) · [Chương 14: Isolation level và MVCC →](14-isolation-mvcc.md)

**Bạn sẽ học được:**

- Transaction là gì, vì sao một ứng dụng có tiền, tồn kho, đơn hàng không thể sống thiếu nó.
- Dùng đúng `START TRANSACTION` / `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`, và hiểu chế độ
  *autocommit* của MySQL (cái mà nhiều người dùng hằng ngày mà không biết là có).
- Biết MySQL làm gì khi một câu lệnh trong transaction bị lỗi, câu lệnh nào tự commit ngầm, và cái gì
  không bao giờ rollback được.
- Hiểu bốn chữ ACID qua ví dụ chuyển tiền: mỗi chữ hứa gì, không hứa gì, và InnoDB thực hiện nó bằng
  cơ chế nào (redo log, `fsync`, undo log ở mức khái niệm).
- Nhận ra transaction dài, biết vì sao nó nguy hiểm, và vì sao không được gọi API bên ngoài khi đang
  giữ transaction.

**Cần biết trước:** [Chương 04](04-ddl-constraint.md) (bảng, `PRIMARY KEY`, `FOREIGN KEY`, `CHECK`),
[Chương 05](05-select-co-ban.md) (`INSERT`, `UPDATE`, `DELETE`, `SELECT`). Không cần biết gì về
concurrency: chương này giới thiệu từ đầu, chương 14 và 15 đi sâu.

## 1. Dữ liệu mẫu của chương

Mọi ví dụ chạy trên MySQL 8.4 (bảng InnoDB, engine mặc định). Chỗ nào nói về PostgreSQL sẽ ghi rõ.
Nếu chưa có MySQL, chạy bằng Docker:

```bash
# Chạy trên máy của bạn (terminal thường)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi vài giây cho server khởi động xong, rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Nhiều ví dụ trong chương cần **hai session** chạy song song (để thấy người khác nhìn thấy gì). Mở
thêm một terminal nữa và chạy lại lệnh `docker exec ...` ở trên: mỗi cửa sổ `mysql` là một session
(một connection) riêng. Trong chương, hai session này gọi là session A và session B.

Dán đoạn SQL sau vào client `mysql`:

```sql
DROP DATABASE IF EXISTS ch13;      -- database riêng của chương, xoá đi tạo lại cho sạch
CREATE DATABASE ch13;
USE ch13;

-- Tài khoản ngân hàng. Luật: số dư không bao giờ âm (khai báo bằng CHECK).
CREATE TABLE accounts (
  id      INT PRIMARY KEY,
  owner   VARCHAR(50)   NOT NULL,
  balance DECIMAL(12,2) NOT NULL,
  CONSTRAINT chk_balance_non_negative CHECK (balance >= 0)
) ENGINE = InnoDB;

INSERT INTO accounts VALUES
  (1, 'An',   500.00),
  (2, 'Bình', 300.00),
  (3, 'Chi',    0.00);           -- Chi có 0 đồng: cố ý, để thấy CHECK chặn số dư âm

-- Lịch sử chuyển tiền: mỗi lần chuyển ghi một dòng
CREATE TABLE transfers (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  from_id    INT           NOT NULL,
  to_id      INT           NOT NULL,
  amount     DECIMAL(12,2) NOT NULL,
  created_at DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_amount_positive CHECK (amount > 0),
  FOREIGN KEY (from_id) REFERENCES accounts (id),
  FOREIGN KEY (to_id)   REFERENCES accounts (id)
) ENGINE = InnoDB;
```

Kiểm tra:

```sql
SELECT * FROM accounts;
-- Kết quả mong đợi:
-- +----+-------+---------+
-- | id | owner | balance |
-- +----+-------+---------+
-- |  1 | An    |  500.00 |
-- |  2 | Bình  |  300.00 |
-- |  3 | Chi   |    0.00 |
-- +----+-------+---------+
```

Tổng tiền trong hệ thống lúc đầu là 500 + 300 + 0 = **800.00**. Hãy nhớ con số này: chuyển tiền giữa
các tài khoản thì tổng phải luôn là 800. Đây là một *bất biến* (invariant) của hệ thống, và nó sẽ là
thước đo xuyên suốt chương.

Mỗi khi muốn bắt đầu lại từ đầu, chạy lại toàn bộ đoạn SQL trên.

## 2. Vì sao cần transaction

### 2.1 Bài toán chuyển tiền

An chuyển 100 cho Bình. Ở mức SQL, việc này cần ít nhất hai câu lệnh:

```sql
UPDATE accounts SET balance = balance - 100 WHERE id = 1;   -- (1) trừ tiền An
UPDATE accounts SET balance = balance + 100 WHERE id = 2;   -- (2) cộng tiền Bình
INSERT INTO transfers (from_id, to_id, amount) VALUES (1, 2, 100);  -- (3) ghi lịch sử
```

Ba câu này, về mặt nghiệp vụ, là **một** việc. Nhưng database nhận chúng như ba câu riêng lẻ. Điều gì
xảy ra nếu có sự cố ở giữa?

```
Thời gian ─────────────────────────────────────────────────────────────►
   (1) trừ An 100        [X] server mất điện / app crash / mất mạng
   An: 500 → 400            (2) và (3) không bao giờ chạy
                         Kết quả: An mất 100, Bình không nhận được gì.
                         Tổng tiền: 400 + 300 + 0 = 700 ≠ 800. Tiền "bốc hơi".
```

Và kể cả không có sự cố, vẫn có vấn đề thứ hai: **người khác nhìn thấy trạng thái dở dang**. Giả sử
đúng lúc (1) đã chạy mà (2) chưa chạy, một báo cáo khác tính `SELECT SUM(balance) FROM accounts`. Nó
sẽ thấy 700, một con số chưa từng đúng ở bất kỳ thời điểm "thật" nào của nghiệp vụ.

Hai vấn đề này (làm dở dang, và bị nhìn thấy lúc dở dang) chính là lý do transaction ra đời.

### 2.2 Định nghĩa

*Transaction* (giao dịch) là một nhóm câu lệnh mà database đối xử như **một đơn vị công việc không
chia cắt**:

- Hoặc **tất cả** thay đổi trong nhóm cùng có hiệu lực: gọi là *commit* (xác nhận).
- Hoặc **không** thay đổi nào có hiệu lực, như thể nhóm lệnh chưa từng chạy: gọi là *rollback*
  (huỷ, quay lui).

Không có trạng thái thứ ba "làm được một nửa". Người ta hay gọi tính chất này là *all-or-nothing*.

Ngoài ra, khi transaction chưa commit, các session khác (ở mức cô lập mặc định) không nhìn thấy
những thay đổi dở dang của nó. Thay đổi chỉ "lộ ra" cho người khác vào đúng khoảnh khắc commit.

```
            START TRANSACTION
                   │
       ┌───────────┴───────────┐
       │  (1) trừ An 100        │   ← thay đổi tạm thời, chỉ session này thấy
       │  (2) cộng Bình 100     │
       │  (3) ghi transfers     │
       └───────────┬───────────┘
          ┌────────┴────────┐
        COMMIT           ROLLBACK
          │                 │
   cả 3 thay đổi      cả 3 thay đổi
   có hiệu lực,       biến mất, dữ liệu
   mọi người thấy     y như trước START
```

### 2.3 Transaction không chỉ dành cho ngân hàng

Ví dụ chuyển tiền là kinh điển vì dễ hình dung, nhưng trong một ứng dụng web bình thường, bạn gặp nhu
cầu "nhiều thay đổi phải đi cùng nhau" ở khắp nơi:

| Nghiệp vụ | Các thay đổi phải đi cùng nhau |
|---|---|
| Đặt hàng | Tạo `orders`, tạo nhiều `order_items`, trừ `products.stock` |
| Đăng ký tài khoản | Tạo `users`, tạo `profiles`, gán vai trò mặc định trong `role_user` |
| Hoàn tiền | Đổi trạng thái đơn, cộng lại tồn kho, ghi bút toán hoàn tiền |
| Xoá một bài viết | Xoá comment, xoá tag gắn kèm, xoá bài |

Nếu chỉ một phần chạy được, dữ liệu rơi vào trạng thái "mồ côi" hoặc mâu thuẫn: đơn hàng không có
dòng hàng nào, user không có profile, tồn kho đã trừ nhưng đơn không tồn tại.

## 3. Cú pháp: START TRANSACTION, COMMIT, ROLLBACK

### 3.1 Ba câu lệnh cơ bản

```sql
START TRANSACTION;   -- bắt đầu một transaction (BEGIN hoặc BEGIN WORK là bí danh)
...                  -- các câu INSERT / UPDATE / DELETE / SELECT
COMMIT;              -- xác nhận: mọi thay đổi có hiệu lực vĩnh viễn và người khác thấy được
-- hoặc
ROLLBACK;            -- huỷ: mọi thay đổi từ START TRANSACTION tới giờ bị bỏ
```

`BEGIN` và `BEGIN WORK` là bí danh của `START TRANSACTION`. Tài liệu MySQL khuyên dùng
`START TRANSACTION` vì đó là cú pháp chuẩn SQL và nó nhận thêm các tuỳ chọn (mục 3.5) mà `BEGIN`
không nhận. `COMMIT WORK` và `ROLLBACK WORK` cũng hợp lệ, chữ `WORK` không có tác dụng gì thêm.

### 3.2 Ví dụ commit: chuyển tiền thành công

Làm trong một session:

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
INSERT INTO transfers (from_id, to_id, amount) VALUES (1, 2, 100);
COMMIT;

SELECT id, balance FROM accounts;
-- Kết quả mong đợi:
-- | 1 | 400.00 |
-- | 2 | 400.00 |
-- | 3 |   0.00 |
-- Tổng: 800.00, bất biến được giữ.
```

### 3.3 Ví dụ rollback: đổi ý giữa chừng

Tiếp tục từ trạng thái trên (An 400, Bình 400):

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 50 WHERE id = 1;
SELECT balance FROM accounts WHERE id = 1;   -- 350.00: chính session này thấy thay đổi của mình
ROLLBACK;

SELECT balance FROM accounts WHERE id = 1;   -- 400.00: như chưa từng trừ
```

Lưu ý dòng thứ ba: bên trong transaction, **chính bạn** thấy thay đổi của mình ngay lập tức. Chỉ
người khác là chưa thấy.

### 3.4 Người khác thấy gì khi transaction chưa commit

Đây là thí nghiệm hai session. Dữ liệu đang là An 400, Bình 400. Làm lần lượt theo cột "Bước":

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | A mở transaction |
| 2 | `UPDATE accounts SET balance = balance - 100 WHERE id = 1;` | | A đã trừ An, chưa commit |
| 3 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy **300.00** |
| 4 | | `SELECT balance FROM accounts WHERE id = 1;` | B thấy **400.00**: thay đổi chưa commit của A bị giấu |
| 5 | | `SELECT SUM(balance) FROM accounts;` | B thấy **800.00**: không bao giờ thấy trạng thái dở dang |
| 6 | `UPDATE accounts SET balance = balance + 100 WHERE id = 2;` | | |
| 7 | `COMMIT;` | | Cả hai thay đổi có hiệu lực cùng một lúc |
| 8 | | `SELECT balance FROM accounts WHERE id IN (1, 2);` | B thấy **300.00** và **500.00** |

Ở bước 8, session B đang dùng autocommit (mục 4), nên mỗi câu `SELECT` của B là một transaction mới
và nhìn thấy dữ liệu đã commit mới nhất.

Tại sao B ở bước 4 không bị "chặn" (phải chờ) mà vẫn đọc được giá trị cũ 400? Vì InnoDB giữ lại bản
cũ của dòng trong *undo log* và cho B đọc bản đó. Cơ chế này tên là MVCC, và chuyện "B thấy gì, khi
nào" phụ thuộc vào *isolation level*. Cả hai là nội dung của [chương 14](14-isolation-mvcc.md). Ở
chương này chỉ cần nhớ: ở mức mặc định, người khác **không** thấy thay đổi chưa commit của bạn.

⚠️ Nếu ở bước 4, session B không `SELECT` mà cũng `UPDATE` đúng dòng `id = 1`, B sẽ phải **chờ** cho
tới khi A commit hoặc rollback, vì A đang giữ *lock* (khoá) trên dòng đó. Đọc thường thì không chờ,
ghi cùng dòng thì chờ. Lock là nội dung của [chương 15](15-lock-deadlock.md).

### 3.5 Các tuỳ chọn của START TRANSACTION

Cú pháp đầy đủ theo MySQL 8.4 Reference Manual:

```sql
START TRANSACTION [transaction_characteristic [, transaction_characteristic] ...]

transaction_characteristic: {
    WITH CONSISTENT SNAPSHOT
  | READ WRITE
  | READ ONLY
}
```

**`READ ONLY`**: khai báo transaction chỉ đọc. Mọi câu ghi vào bảng thường đều bị từ chối:

```sql
START TRANSACTION READ ONLY;
SELECT SUM(balance) FROM accounts;          -- được
UPDATE accounts SET balance = 0 WHERE id = 3;
-- ERROR 1792 (25006): Cannot execute statement in a READ ONLY transaction.
COMMIT;
```

Lỗi này không kết thúc transaction; transaction vẫn tiếp tục ở chế độ chỉ đọc. Bảng `TEMPORARY` của
riêng session thì vẫn được ghi. Lợi ích: InnoDB không cần cấp *transaction ID* cho transaction chỉ đọc,
giúp giảm chi phí nội bộ. Tài liệu cũng ghi InnoDB tự nhận ra transaction chỉ đọc trong nhiều trường
hợp (ví dụ một câu `SELECT` thường ở chế độ autocommit), `READ ONLY` là cách nói rõ cho chắc.

**`READ WRITE`**: ngược lại, cho phép ghi. Đây là mặc định, hiếm khi cần viết ra. Không được ghi cả
`READ ONLY` lẫn `READ WRITE` trong cùng một câu.

**`WITH CONSISTENT SNAPSHOT`**: chụp ngay "ảnh" dữ liệu để đọc nhất quán, thay vì chờ tới câu `SELECT`
đầu tiên. Chỉ có tác dụng ở isolation level `REPEATABLE READ`; ở mức khác thì bị bỏ qua kèm một
warning. Ý nghĩa của "ảnh" (snapshot) sẽ rõ ở [chương 14](14-isolation-mvcc.md).

Có thể ghép nhiều tuỳ chọn bằng dấu phẩy:

```sql
START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT;
```

### 3.6 BEGIN trong stored procedure không phải là bắt đầu transaction

⚠️ Trong *stored program* (stored procedure, function, trigger, event), từ khoá `BEGIN` mở một khối
lệnh `BEGIN ... END` chứ **không** bắt đầu transaction. Muốn bắt đầu transaction trong stored
procedure, phải viết `START TRANSACTION`. Đây là một lý do nữa để tập thói quen dùng
`START TRANSACTION` thay vì `BEGIN`. Stored program là nội dung của
[chương 17](17-view-procedure-trigger.md).

### 3.7 COMMIT AND CHAIN, RELEASE (biết để đọc hiểu)

Cú pháp đầy đủ của `COMMIT` và `ROLLBACK`:

```sql
COMMIT   [WORK] [AND [NO] CHAIN] [[NO] RELEASE]
ROLLBACK [WORK] [AND [NO] CHAIN] [[NO] RELEASE]
```

- `AND CHAIN`: kết thúc transaction hiện tại và **mở ngay** một transaction mới với cùng isolation
  level và cùng chế độ `READ ONLY`/`READ WRITE`.
- `RELEASE`: kết thúc transaction rồi **ngắt kết nối** session.
- Biến hệ thống `completion_type` (mặc định `NO_CHAIN`) có thể biến mọi `COMMIT`/`ROLLBACK` thành
  có `CHAIN` hoặc `RELEASE` mặc định; khi đó chữ `NO` dùng để tắt nó cho một câu.

Trong ứng dụng web thực tế, bạn gần như không bao giờ dùng hai tuỳ chọn này. Chỉ cần biết để không
bối rối khi đọc thấy.

### 3.8 Transaction không lồng nhau được

Gọi `START TRANSACTION` khi đang có transaction mở **không** tạo transaction con. MySQL tự commit
transaction đang mở rồi mới bắt đầu transaction mới:

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 10 WHERE id = 1;
START TRANSACTION;      -- ⚠️ commit ngầm cái UPDATE ở trên!
ROLLBACK;               -- chỉ huỷ transaction thứ hai (đang trống)
SELECT balance FROM accounts WHERE id = 1;   -- đã bị trừ 10, không lấy lại được
```

Tài liệu MySQL ghi thẳng: *Transactions cannot be nested*. Muốn có "điểm quay lui" bên trong một
transaction, dùng `SAVEPOINT` (mục 6). Các framework như Laravel giả lập "transaction lồng nhau" chính
bằng savepoint.

(Nếu bạn vừa chạy đoạn trên, chạy lại phần dữ liệu mẫu ở mục 1 để quay về trạng thái ban đầu trước
khi đọc tiếp.)

## 4. Autocommit: transaction mà bạn không biết mình đang dùng

### 4.1 Mỗi câu lệnh lẻ là một transaction

Với InnoDB, **mọi** câu lệnh đều chạy bên trong một transaction. Khi bạn không viết
`START TRANSACTION`, MySQL dùng chế độ *autocommit* (tự động commit): mỗi câu lệnh tự là một
transaction riêng, và được commit ngay khi chạy xong nếu không lỗi. Biến hệ thống `autocommit` mặc
định là `ON` cho mọi connection mới.

```sql
SELECT @@autocommit;   -- 1

UPDATE accounts SET balance = balance + 1 WHERE id = 3;   -- đã commit ngay khi câu này xong
ROLLBACK;                                                  -- không có tác dụng: không còn gì để huỷ
SELECT balance FROM accounts WHERE id = 3;                 -- 1.00
UPDATE accounts SET balance = balance - 1 WHERE id = 3;   -- trả lại 0.00 cho các ví dụ sau
```

`START TRANSACTION` tạm tắt autocommit cho tới khi gặp `COMMIT` hoặc `ROLLBACK`; sau đó autocommit
trở về như cũ.

### 4.2 Tính nguyên tử của một câu lệnh

Dù autocommit, một câu lệnh **ảnh hưởng nhiều dòng** vẫn là all-or-nothing: nếu lỗi ở dòng thứ ba thì
hai dòng đầu cũng được hoàn tác. Thử trừ 100 của mọi người cùng lúc (An 500, Bình 300, Chi 0):

```sql
UPDATE accounts SET balance = balance - 100;
-- ERROR 3819 (HY000): Check constraint 'chk_balance_non_negative' is violated.
SELECT id, balance FROM accounts;
-- | 1 | 500.00 |   ← An KHÔNG bị trừ, dù dòng của An hợp lệ
-- | 2 | 300.00 |
-- | 3 |   0.00 |
```

Tài liệu MySQL: ở chế độ autocommit, mỗi câu lệnh *atomic, as if it were surrounded by START
TRANSACTION and COMMIT*, và nếu có lỗi trong lúc chạy thì câu lệnh bị rollback. Điều này đúng với
bảng InnoDB; bảng không hỗ trợ transaction như MyISAM thì không (mục 7.3).

### 4.3 SET autocommit = 0

Cách thứ hai để làm nhiều câu trong một transaction: tắt autocommit cho cả session.

```sql
SET autocommit = 0;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
ROLLBACK;          -- kết thúc transaction này (ở đây huỷ để giữ dữ liệu mẫu);
                   -- một transaction mới tự bắt đầu ngay
SET autocommit = 1;
```

Khi `autocommit = 0`, session **luôn** có một transaction đang mở: `COMMIT`/`ROLLBACK` kết thúc
transaction cũ và transaction mới bắt đầu luôn. Một số điểm (đều theo tài liệu MySQL):

- `autocommit` là biến theo session, phải đặt cho từng connection.
- Đổi từ 0 sang 1 sẽ tự commit transaction đang mở.
- Session đang `autocommit = 0` mà kết thúc (ngắt kết nối) khi chưa commit thì MySQL **rollback**
  transaction cuối.

⚠️ Bẫy kinh điển: tắt autocommit, chạy một câu `SELECT` rồi quên `COMMIT`. Transaction vẫn mở, giữ một
snapshot cũ hàng giờ. Tài liệu MySQL nêu đúng tình huống này là ví dụ về transaction chạy dài làm
phình undo log (mục 9). Trong ứng dụng, cứ để autocommit mặc định và dùng `START TRANSACTION`
(hoặc `beginTransaction()` của thư viện) khi cần nhiều câu đi cùng nhau.

### 4.4 Làm sao biết đang có transaction mở

Trong client `mysql` không có dấu hiệu nào trên dấu nhắc. Hai cách xem:

```sql
SELECT @@autocommit;   -- 0 nghĩa là chắc chắn luôn có transaction mở

-- Các transaction InnoDB đang hoạt động trên server (mọi session)
SELECT trx_id, trx_state, trx_started, trx_mysql_thread_id, trx_rows_modified, trx_query
FROM information_schema.INNODB_TRX;
```

Lưu ý: transaction autocommit, không khoá, chỉ đọc (một `SELECT` thường) được InnoDB giữ ngoài một số
cấu trúc nội bộ, và cũng không hiện trong `SHOW ENGINE INNODB STATUS`.

## 5. Khi một câu lệnh trong transaction bị lỗi

### 5.1 MySQL chỉ rollback câu lệnh lỗi, không rollback cả transaction

Đây là điều nhiều người tưởng sai. Thử chuyển 600 từ An (chỉ có 500) sang Bình, nhưng làm theo thứ tự
"cộng trước, trừ sau":

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance + 600 WHERE id = 2;   -- OK, Bình: 900
UPDATE accounts SET balance = balance - 600 WHERE id = 1;   -- An: -100 → vi phạm CHECK
-- ERROR 3819 (HY000): Check constraint 'chk_balance_non_negative' is violated.

SELECT id, balance FROM accounts WHERE id IN (1, 2);
-- | 1 | 500.00 |
-- | 2 | 900.00 |   ← câu UPDATE đầu VẪN còn hiệu lực, transaction VẪN đang mở
```

Nếu lúc này bạn (hoặc code) lỡ gõ `COMMIT`, Bình được cộng 600 từ hư không và tổng tiền thành 1400.
Đúng phải là:

```sql
ROLLBACK;     -- ứng dụng thấy lỗi thì phải tự quyết định rollback cả khối
```

Theo tài liệu "InnoDB Error Handling", tuỳ loại lỗi mà InnoDB rollback một câu hay cả transaction:

| Lỗi | InnoDB rollback gì | Ứng dụng nên làm |
|---|---|---|
| Duplicate key (`ERROR 1062`), vi phạm `CHECK`, hầu hết lỗi khác | Chỉ câu lệnh lỗi | `ROLLBACK` cả transaction (hoặc xử lý rồi đi tiếp nếu có chủ đích) |
| Deadlock (`ERROR 1213`) | **Cả transaction** | Chạy lại toàn bộ transaction |
| Lock wait timeout (`ERROR 1205`, chờ quá `innodb_lock_wait_timeout`, mặc định 50 giây) | Chỉ câu lệnh đang chờ (mặc định) | Rollback/thử lại; nếu bật `innodb_rollback_on_timeout` (mặc định `OFF`) thì cả transaction đã bị rollback |
| Mất kết nối, client chết | Cả transaction (server rollback khi session kết thúc) | Kết nối lại, chạy lại nếu an toàn |

⚠️ Khi chỉ một câu bị rollback, *các lock mà câu đó đã lấy vẫn được giữ* cho tới khi transaction kết
thúc (tài liệu ghi: *Locks are not released in a rollback of a single SQL statement*). Thêm
một lý do để rollback sớm khi có lỗi.

### 5.2 Đối chiếu PostgreSQL

PostgreSQL làm ngược lại: một câu lỗi khiến cả transaction rơi vào trạng thái *aborted*; mọi câu sau
đó đều bị từ chối với lỗi `current transaction is aborted, commands ignored until end of transaction
block` cho tới khi bạn `ROLLBACK` (hoặc `ROLLBACK TO SAVEPOINT`). Postgres "ép" bạn xử lý lỗi;
MySQL thì để bạn tự nhớ. Code viết chung cho cả hai nên luôn rollback khi gặp lỗi.

## 6. SAVEPOINT: điểm quay lui bên trong transaction

### 6.1 Cú pháp và ví dụ

```sql
SAVEPOINT ten;                    -- đặt một điểm mốc tên "ten"
ROLLBACK [WORK] TO [SAVEPOINT] ten; -- huỷ các thay đổi sau mốc, transaction VẪN mở
RELEASE SAVEPOINT ten;            -- xoá mốc (không commit, không rollback gì)
```

Ví dụ: chuyển tiền từ An cho nhiều người; lần nào lỗi thì bỏ riêng lần đó, các lần khác giữ lại.

```sql
START TRANSACTION;

SAVEPOINT t1;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;   -- An 400
UPDATE accounts SET balance = balance + 100 WHERE id = 2;   -- Bình 400

SAVEPOINT t2;
UPDATE accounts SET balance = balance + 900 WHERE id = 3;   -- Chi 900
UPDATE accounts SET balance = balance - 900 WHERE id = 1;   -- An -500 → ERROR 3819
ROLLBACK TO SAVEPOINT t2;                                   -- bỏ lần chuyển thứ hai (cả phần cộng cho Chi)

COMMIT;
SELECT id, balance FROM accounts;
-- | 1 | 400.00 |
-- | 2 | 400.00 |
-- | 3 |   0.00 |   tổng vẫn 800.00
```

### 6.2 Quy tắc cần nhớ (theo tài liệu MySQL)

- Đặt savepoint trùng tên với savepoint đã có: cái cũ bị xoá, cái mới thay thế.
- `ROLLBACK TO` một savepoint sẽ xoá luôn các savepoint đặt **sau** nó.
- `ROLLBACK TO` tên không tồn tại: `ERROR 1305 (42000): SAVEPOINT ... does not exist`.
- `COMMIT` hoặc `ROLLBACK` (không kèm tên savepoint) xoá mọi savepoint của transaction.
- ⚠️ `ROLLBACK TO SAVEPOINT` hoàn tác thay đổi nhưng **không nhả row lock** đã lấy sau savepoint
  (trừ lock của dòng mới insert). Session khác chờ những dòng đó vẫn phải chờ tới khi transaction kết
  thúc.

### 6.3 Savepoint và "transaction lồng nhau" của framework

Laravel cho phép gọi `DB::transaction()` bên trong `DB::transaction()`. Bên dưới, chỉ lớp ngoài cùng
là `START TRANSACTION` thật; các lớp trong là savepoint (mã nguồn Laravel 13 đặt tên `trans2`,
`trans3`...). Lớp trong lỗi thì rollback về savepoint của nó. Chi tiết ở
[chương 19](19-database-tu-ung-dung.md).

## 7. Implicit commit và những thứ không rollback được

### 7.1 Câu lệnh tự commit ngầm

Một số câu lệnh *implicit commit* (commit ngầm): trước khi chạy, chúng kết thúc transaction đang mở
**như thể bạn đã gõ `COMMIT`**. Đa số còn commit thêm một lần sau khi chạy. Các nhóm chính theo tài
liệu MySQL 8.4:

| Nhóm | Ví dụ |
|---|---|
| DDL | `CREATE/ALTER/DROP TABLE`, `CREATE/DROP INDEX`, `RENAME TABLE`, `TRUNCATE TABLE`, `CREATE/DROP DATABASE`, `CREATE/DROP VIEW`, `CREATE/DROP PROCEDURE`, `CREATE/DROP TRIGGER` |
| Quản lý tài khoản | `CREATE USER`, `ALTER USER`, `DROP USER`, `GRANT`, `REVOKE`, `SET PASSWORD` |
| Điều khiển transaction, khoá | `START TRANSACTION`, `BEGIN`, `LOCK TABLES`, `UNLOCK TABLES` (khi có bảng đang bị `LOCK TABLES`), `SET autocommit = 1` (nếu đang là 0) |
| Quản trị | `ANALYZE TABLE`, `CHECK TABLE`, `OPTIMIZE TABLE`, `REPAIR TABLE`, `FLUSH`, `RESET` |
| Điều khiển replication | `START REPLICA`, `STOP REPLICA`, `RESET REPLICA`, `CHANGE REPLICATION SOURCE TO` |

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
CREATE TABLE audit_tmp (id INT);   -- ⚠️ commit ngầm: cái UPDATE ở trên đã được xác nhận
ROLLBACK;                          -- không lấy lại được 100 của An
```

Đây là bẫy thường gặp với migration hoặc code "tiện tay" tạo bảng trong lúc xử lý nghiệp vụ. Tài liệu
PDO cảnh báo: một số database, trong đó có MySQL, tự commit ngầm khi gặp DDL như `DROP TABLE` hay
`CREATE TABLE` bên trong transaction, và thư viện ở phía ứng dụng không hề biết điều đó.

Trường hợp đặc biệt: `CREATE TEMPORARY TABLE` và `DROP TEMPORARY TABLE` **không** commit ngầm, nhưng
cũng **không** rollback được: rollback transaction xong thì bảng tạm vẫn còn đó.

### 7.2 Atomic DDL không phải transactional DDL

Từ MySQL 8.0, nhờ data dictionary mới, một câu DDL trên InnoDB là *atomic*: hoặc xong trọn vẹn, hoặc
không để lại dấu vết dở dang (ví dụ không còn trạng thái "file bảng đã xoá mà metadata còn"). Nhưng
đó là atomic **trong phạm vi một câu**. Bạn vẫn không thể gom `ALTER TABLE` với `UPDATE` vào một
transaction rồi rollback cả hai.

PostgreSQL thì có *transactional DDL*: `CREATE TABLE`, `ALTER TABLE`... nằm trong transaction và
rollback được cùng dữ liệu (trừ một số lệnh như `CREATE INDEX CONCURRENTLY`). Hệ quả thực tế ở
[chương 20](20-thay-doi-schema-migration.md): migration lỗi giữa chừng trên MySQL có thể để schema ở
trạng thái nửa vời.

### 7.3 Bảng không hỗ trợ transaction

Transaction là tính năng của *storage engine*. InnoDB hỗ trợ, MyISAM thì không. Nếu một transaction
sửa cả bảng MyISAM: thay đổi trên bảng MyISAM có hiệu lực ngay, và `ROLLBACK` chỉ huỷ phần InnoDB,
kèm warning `ER_WARNING_NOT_COMPLETE_ROLLBACK` (một số bảng không transaction không rollback được).
Bài học: dùng InnoDB cho mọi bảng nghiệp vụ.

### 7.4 Những thứ rollback không trả lại

- Giá trị `AUTO_INCREMENT` đã cấp: rollback một `INSERT` thì id đó bị "tiêu" mất, id tiếp theo nhảy
  cóc. Đừng dùng id để đếm hay mong nó liên tục.
- Mọi việc **bên ngoài database**: email đã gửi, file đã ghi, API đã gọi, message đã đẩy vào queue.
  Mục 10 bàn kỹ.

## 8. ACID: bốn lời hứa của transaction

*ACID* là viết tắt của bốn tính chất: **A**tomicity, **C**onsistency, **I**solation,
**D**urability. Thuật ngữ do Theo Härder và Andreas Reuter đặt năm 1983. Martin Kleppmann
(*Designing Data-Intensive Applications*, chương 7) lưu ý mỗi hệ hiểu các chữ này hơi khác nhau, nên
hãy hiểu cơ chế và ví dụ thay vì học thuộc định nghĩa.

### 8.1 A: Atomicity (tính nguyên tử)

**Hứa gì**: các thay đổi trong một transaction hoặc cùng có hiệu lực, hoặc cùng bị huỷ. Không bao giờ
có chuyện An bị trừ 100 mà Bình không được cộng, dù lỗi đến từ đâu: lỗi logic, app gọi `ROLLBACK`,
mất kết nối, hay server sập giữa chừng.

**Không hứa gì**: "atomic" ở đây **không** nói về việc chạy đồng thời (đó là chữ I). Kleppmann gợi ý
nghĩ về chữ A như *abortability*: khả năng huỷ bỏ sạch sẽ, nhờ đó ứng dụng có thể thử lại cả khối mà
không lo dữ liệu dở dang.

**Cơ chế (khái niệm)**: trước khi sửa một dòng, InnoDB ghi lại thông tin để hoàn tác (bản cũ của dòng)
vào *undo log*. `ROLLBACK` là áp ngược undo log. Khi server khởi động lại sau sự cố, InnoDB cũng dùng
cơ chế này để rollback mọi transaction chưa commit lúc sập. Chi tiết ở
[chương 16](16-ben-trong-innodb.md).

### 8.2 C: Consistency (tính nhất quán)

**Hứa gì**: transaction đưa database từ một trạng thái hợp lệ sang một trạng thái hợp lệ khác, tức là
các *bất biến* luôn đúng. Ví dụ: số dư không âm, mỗi `transfers.from_id` trỏ tới tài khoản có thật,
tổng tiền luôn 800.

**Điểm mấu chốt**: database chỉ giữ được những bất biến bạn **đã khai báo** thành ràng buộc:
`PRIMARY KEY`, `UNIQUE`, `NOT NULL`, `FOREIGN KEY`, `CHECK`. Trong dữ liệu mẫu, "số dư không âm" là
`CHECK` nên DB tự chặn (mục 4.2, 5.1). Còn "tổng tiền luôn 800" không có ràng buộc nào diễn đạt được,
nên là trách nhiệm của code: nếu code cộng cho Bình 100 mà chỉ trừ An 10 rồi `COMMIT`, DB vui vẻ chấp
nhận. Vì thế Kleppmann cho rằng chữ C thuộc về ứng dụng nhiều hơn là về database: A, I, D là công cụ
DB đưa cho bạn để **bạn** giữ được C.

⚠️ `CHECK` chỉ thật sự được kiểm tra từ MySQL 8.0.16; các bản trước parse cú pháp rồi bỏ qua. Trên
MySQL 8.4 thì yên tâm dùng.

Thú vị: trang "MySQL and the ACID Model" trong tài liệu MySQL lại xếp vào chữ C các cơ chế bảo vệ dữ
liệu khỏi hỏng khi sập (doublewrite buffer, crash recovery). Một ví dụ cho nhận xét "mỗi hệ hiểu một
kiểu" ở trên.

### 8.3 I: Isolation (tính cô lập)

**Hứa gì**: các transaction chạy đồng thời không giẫm lên nhau. Mức lý tưởng là *serializable*: kết
quả giống như các transaction chạy lần lượt từng cái một. Ví dụ ở mục 3.4: báo cáo tổng tiền chạy đúng
lúc đang chuyển tiền vẫn thấy 800, không thấy trạng thái "đã trừ mà chưa cộng".

**Không hứa gì (ở mức mặc định)**: để nhanh, database mặc định dùng mức cô lập **yếu hơn**
serializable (MySQL: `REPEATABLE READ`, PostgreSQL: `READ COMMITTED`), và mức yếu để lọt một số hiện
tượng. Ví dụ nổi tiếng nhất là *lost update* (mất cập nhật). Tồn kho còn 1, hai request mua cùng lúc,
mỗi request đều nằm trong transaction:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | `START TRANSACTION;` | |
| 2 | `SELECT stock ... WHERE id = 1;` | | A thấy 1 |
| 3 | | `SELECT stock ... WHERE id = 1;` | B cũng thấy 1 |
| 4 | Code thấy còn hàng: `UPDATE ... SET stock = 0 WHERE id = 1;` | | A giữ lock dòng |
| 5 | | Code thấy còn hàng: `UPDATE ... SET stock = 0 WHERE id = 1;` | B chờ lock của A |
| 6 | `INSERT INTO orders ...; COMMIT;` | | B được chạy tiếp |
| 7 | | `INSERT INTO orders ...; COMMIT;` | Hai đơn hàng cho một món |

Transaction bảo đảm mỗi request "xong hết hoặc không gì cả", nhưng không bảo đảm dữ liệu đọc ở bước 2
còn đúng ở bước 4. Lỗi nằm ở mẫu *read-modify-write* (đọc, tính ở app, ghi lại). Cách sửa đơn giản
là để DB kiểm tra ngay lúc ghi:

```sql
UPDATE products SET stock = stock - 1 WHERE id = 1 AND stock > 0;
-- affected rows = 1: mua được; = 0: hết hàng
```

Các mức isolation, MVCC và các hiện tượng khác ở [chương 14](14-isolation-mvcc.md); `SELECT ... FOR
UPDATE`, lock, deadlock ở [chương 15](15-lock-deadlock.md).

### 8.4 D: Durability (tính bền vững)

**Hứa gì**: khi `COMMIT` đã báo thành công, dữ liệu không mất, kể cả nếu ngay sau đó server mất điện.

**Vấn đề**: ghi thẳng mọi trang dữ liệu bị sửa xuống đĩa ở mỗi lần commit thì rất chậm (các trang
16 KB nằm rải rác khắp file). Mặt khác, chỉ sửa trong RAM thì mất điện là mất.

**Cơ chế: write-ahead log** (WAL, ghi log trước). InnoDB làm như sau (mô tả ở mức khái niệm):

```
  Session                    RAM (buffer pool)          Đĩa
  ───────                    ─────────────────          ───
  UPDATE ...      ──►  sửa trang dữ liệu trong RAM
                       ("dirty page", chưa ghi đĩa)
                       ghi bản mô tả thay đổi
                       vào bộ đệm redo log
  COMMIT          ──►  ghi redo log ──────────────────► file redo log (ghi nối tiếp)
                                                         + fsync: buộc OS đẩy hẳn xuống thiết bị
  "OK" ◄── chỉ trả về sau khi fsync xong
  ...về sau, ở chế độ nền: trang dữ liệu bẩn ───────────► file dữ liệu (.ibd)

  Nếu sập trước khi trang dữ liệu kịp ghi: khởi động lại, InnoDB đọc redo log
  và áp lại các thay đổi (crash recovery), rồi rollback những transaction chưa commit.
```

- *Redo log*: nhật ký ghi lại "đã sửa gì", được ghi **nối tiếp vào cuối**, nên nhanh hơn nhiều so với
  ghi các trang rải rác.
- `fsync`: lời gọi hệ thống yêu cầu hệ điều hành đẩy dữ liệu từ bộ đệm của OS xuống thiết bị lưu trữ.
  Không có `fsync`, dữ liệu có thể mới nằm trong RAM của OS và mất khi mất điện.

Chi tiết (LSN, checkpoint, doublewrite, group commit) ở [chương 16](16-ben-trong-innodb.md).

**Durability là cấu hình được.** Biến `innodb_flush_log_at_trx_commit` (toàn cục, mặc định `1`):

| Giá trị | Mỗi lần commit | Rủi ro khi sập |
|---|---|---|
| `1` (mặc định) | Ghi redo log **và** flush xuống đĩa | Tài liệu: bắt buộc để tuân thủ ACID đầy đủ |
| `2` | Ghi redo log (vào OS), flush khoảng mỗi giây | Có thể mất các transaction chưa được flush |
| `0` | Không ghi lúc commit; ghi và flush khoảng mỗi giây | Có thể mất các transaction chưa được flush |

Với `0` và `2`, tài liệu nói "mỗi giây" không được bảo đảm 100%, nên lượng mất có thể khoảng một giây
giao dịch hoặc hơn. Tài liệu 8.4 chỉ ghi chung "có thể mất khi crash". Về nguyên lý, với `2` log đã
được ghi vào bộ đệm OS, nên nếu chỉ riêng tiến trình `mysqld` chết thì OS vẫn đẩy được phần đó xuống
đĩa; rủi ro mất dữ liệu chủ yếu đến từ mất điện hoặc OS sập. Với `0` thì kể cả chỉ `mysqld` chết cũng
có thể mất, vì log còn nằm trong bộ đệm của chính `mysqld`. Dù giá trị nào, crash recovery vẫn đảm
bảo mỗi transaction được áp trọn vẹn hoặc bị xoá trọn vẹn (atomicity giữ nguyên, chỉ durability giảm).

Khi bật binary log (dùng cho replication, backup, chương 21, 22), tài liệu khuyên cặp
`sync_binlog = 1` (mặc định) và `innodb_flush_log_at_trx_commit = 1` cho độ bền cao nhất.

⚠️ Không có durability tuyệt đối. Tài liệu MySQL cảnh báo: nhiều hệ điều hành và phần cứng "nói dối"
rằng đã flush xong; ổ đĩa có thể hỏng hẳn. Durability thật sự cần thêm replica và backup
([chương 21](21-backup-restore.md), [chương 22](22-replication-ha.md)).

### 8.5 Bảng tóm tắt ACID

| Chữ | Lời hứa | Cơ chế chính trong InnoDB | Ai chịu trách nhiệm | Đọc sâu |
|---|---|---|---|---|
| A | Tất cả hoặc không gì | Undo log, rollback, crash recovery | DB | Chương 16 |
| C | Bất biến luôn đúng | Ràng buộc (PK, FK, UNIQUE, CHECK, NOT NULL) | Chủ yếu ứng dụng, DB giữ phần đã khai báo | Chương 04 |
| I | Chạy đồng thời không giẫm nhau | MVCC, lock | DB, nhưng mức mặc định yếu hơn serializable | Chương 14, 15 |
| D | Đã commit thì không mất | Redo log + `fsync` (WAL) | DB + cấu hình + phần cứng + backup | Chương 16, 21 |

## 9. Transaction dài và tác hại

### 9.1 "Dài" nghĩa là gì

Độ dài của transaction là khoảng thời gian từ lúc nó bắt đầu tới lúc `COMMIT`/`ROLLBACK`, **không**
phải số câu lệnh. Một transaction chỉ có hai câu `UPDATE` nhưng ở giữa code ngồi chờ API 30 giây là
transaction dài. Transaction mở bằng `autocommit = 0` rồi quên commit có thể dài hàng giờ.

### 9.2 Tác hại

1. **Giữ lock lâu.** Dòng đã sửa bị khoá tới khi transaction kết thúc. Mọi request khác muốn sửa dòng
   đó phải xếp hàng; quá `innodb_lock_wait_timeout` (mặc định 50 giây) thì nhận
   `ERROR 1205 (HY000): Lock wait timeout exceeded; try restarting transaction`. Một dòng "nóng"
   (ví dụ số dư của một ví tổng) bị khoá lâu có thể làm nghẽn cả hệ thống.
2. **Undo log phình ra.** Để những transaction đang đọc snapshot cũ còn thấy dữ liệu cũ, InnoDB phải
   giữ các bản cũ trong undo log cho tới khi không ai cần. Một transaction mở lâu (kể cả chỉ đọc, ở
   `REPEATABLE READ`) ngăn tiến trình dọn dẹp (*purge*). Chỉ số theo dõi là `History list length`
   trong `SHOW ENGINE INNODB STATUS`; tài liệu MySQL nói bình thường nó thấp (thường dưới vài nghìn),
   và transaction chạy dài làm nó tăng. Hệ quả thường gặp: đọc chậm dần, undo tablespace to ra.
3. **Rollback cũng lâu.** Huỷ một transaction đã sửa hàng triệu dòng phải hoàn tác từng thay đổi. Tài
   liệu phần crash recovery ghi thời gian rollback một transaction dở dang có thể gấp ba bốn lần thời
   gian nó đã chạy, và không huỷ được việc rollback đang diễn ra. `KILL` một transaction khổng lồ không
   làm nó biến mất ngay.
4. **Replication trễ.** Mỗi transaction được ghi vào binary log thành một khối lúc commit. Một
   transaction khổng lồ khiến replica phải áp lại cả khối đó, gây trễ ([chương 22](22-replication-ha.md)).
5. **Chiếm connection.** Trong lúc transaction mở, connection đó không phục vụ việc khác, pool
   connection cạn nhanh khi tải cao.
6. **Dễ deadlock và xung đột hơn**, vì cửa sổ thời gian giữ lock rộng hơn. Tài liệu MySQL khuyên làm
   càng ít việc càng tốt giữa lần sửa dữ liệu đầu tiên và lúc commit.

### 9.3 Phát hiện

```sql
-- Các transaction đã mở hơn 60 giây
SELECT trx_id, trx_state, trx_started,
       TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS seconds_open,
       trx_mysql_thread_id, trx_rows_modified, trx_query
FROM information_schema.INNODB_TRX
WHERE trx_started < NOW() - INTERVAL 60 SECOND
ORDER BY trx_started;
```

`trx_query` là `NULL` nghĩa là transaction đang mở nhưng **không chạy câu nào**: dấu hiệu điển hình
của code quên commit hoặc đang chờ việc gì đó ngoài DB. `trx_mysql_thread_id` khớp với cột `Id`
trong `SHOW PROCESSLIST`, dùng để tìm ra connection (và ứng dụng) gây ra. Giám sát kỹ hơn ở
[chương 24](24-van-hanh-monitoring.md).

### 9.4 Cách tránh

- Chuẩn bị mọi thứ (validate input, tính toán, gọi dịch vụ ngoài) **trước** `START TRANSACTION`;
  bên trong chỉ còn các câu SQL cần đi cùng nhau.
- Thao tác hàng loạt (xoá/cập nhật hàng triệu dòng): chia thành nhiều batch nhỏ, mỗi batch một
  transaction ([chương 19](19-database-tu-ung-dung.md)).
- Đừng dùng `autocommit = 0` trong ứng dụng; luôn đóng transaction trong `finally`/`catch`.

## 10. Không gọi API ngoài trong transaction

### 10.1 Vấn đề

Đoạn code "tự nhiên" nhưng sai:

```
START TRANSACTION
  INSERT đơn hàng (trạng thái paid)
  trừ tồn kho
  gọi API cổng thanh toán (1–30 giây)     ← sai chỗ
  gửi email xác nhận                       ← sai chỗ
COMMIT
```

Ba lý do nó sai:

1. **Chậm**: transaction dài đúng bằng thời gian chờ mạng, kéo theo mọi tác hại ở mục 9 (dòng tồn kho
   bị khoá suốt thời gian gọi API).
2. **Không rollback được**: `ROLLBACK` không thu hồi được tiền đã trừ ở cổng thanh toán hay email đã
   gửi. Atomicity chỉ áp dụng cho dữ liệu trong database.
3. **Không nhất quán ở cả hai chiều**:

| Bước | Ứng dụng | Database | Thế giới bên ngoài | Kết quả |
|---|---|---|---|---|
| 1 | `START TRANSACTION`, insert đơn | Đơn chưa commit | | |
| 2 | Gọi API thanh toán: thành công | | Khách đã bị trừ tiền | |
| 3 | `COMMIT` lỗi (deadlock, mất kết nối, server sập) | Đơn bị rollback | Tiền vẫn bị trừ | Khách mất tiền, không có đơn |

Chiều ngược lại: commit thành công nhưng tiến trình chết trước khi gửi email, hoặc API timeout mà thật
ra phía bên kia đã xử lý xong.

### 10.2 Các mẫu đúng (giới thiệu)

- **Gọi bên ngoài trước hoặc sau transaction, không ở giữa.** Ví dụ: tạo đơn trạng thái `pending`
  (transaction ngắn) → gọi cổng thanh toán (ngoài transaction) → cập nhật `paid` (transaction ngắn).
  Mỗi bước để lại trạng thái rõ ràng để có thể đối soát hoặc thử lại.
- **Idempotency key**: gửi kèm một mã duy nhất cho mỗi yêu cầu thanh toán để gọi lại không bị trừ
  tiền hai lần.
- **Transactional outbox**: trong **cùng** transaction với dữ liệu nghiệp vụ, insert một dòng vào bảng
  `outbox` ("cần gửi email X"). Một worker riêng đọc bảng này và gửi sau. Như vậy "đơn được commit"
  và "yêu cầu gửi email được ghi nhận" là atomic với nhau.

Cách cài đặt các mẫu này trong PHP/Laravel ở [chương 19](19-database-tu-ung-dung.md).

## 11. Transaction từ ứng dụng (sơ lược)

Ứng dụng hiếm khi gửi chuỗi `START TRANSACTION` bằng tay; thư viện có hàm riêng. Với PDO:

```php
<?php
declare(strict_types=1);

// Chuyển tiền bằng PDO. $pdo phải bật PDO::ERRMODE_EXCEPTION (mặc định từ PHP 8.0).
function transfer(PDO $pdo, int $fromId, int $toId, string $amount): void
{
    $pdo->beginTransaction();          // tắt autocommit cho tới commit/rollBack
    try {
        $debit = $pdo->prepare('UPDATE accounts SET balance = balance - ? WHERE id = ?');
        $debit->execute([$amount, $fromId]);

        $credit = $pdo->prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?');
        $credit->execute([$amount, $toId]);

        $log = $pdo->prepare('INSERT INTO transfers (from_id, to_id, amount) VALUES (?, ?, ?)');
        $log->execute([$fromId, $toId, $amount]);

        $pdo->commit();
    } catch (Throwable $e) {
        // Nhớ mục 5.1: MySQL chỉ rollback câu lỗi, phần còn lại phải tự rollback
        if ($pdo->inTransaction()) {
            $pdo->rollBack();
        }
        throw $e;
    }
}
```

Một số điểm theo tài liệu PHP:

- `beginTransaction()` ném `PDOException` nếu đã có transaction đang mở; `commit()` ném nếu không có
  transaction nào.
- Script kết thúc hoặc connection đóng mà transaction chưa commit thì PDO tự rollback, **nhưng chỉ**
  với transaction mở bằng `beginTransaction()`, không phải bằng câu `START TRANSACTION` gửi tay.
- DDL bên trong transaction trên MySQL gây commit ngầm (mục 7.1).

Laravel: `DB::transaction(function () { ... })` tự commit khi closure chạy xong và tự rollback rồi ném
lại exception khi có lỗi; tham số `attempts` cho phép thử lại khi gặp deadlock. Xử lý retry, transaction
lồng nhau, `afterCommit`, outbox... ở [chương 19](19-database-tu-ung-dung.md).

## 12. Đối chiếu MySQL và PostgreSQL

| Điểm | MySQL 8.4 (InnoDB) | PostgreSQL 18 |
|---|---|---|
| Bắt đầu | `START TRANSACTION` / `BEGIN` | `BEGIN` / `START TRANSACTION` |
| Mặc định | Autocommit bật | Autocommit (mỗi câu ngoài khối `BEGIN` là một transaction) |
| Câu lỗi trong transaction | Chỉ câu đó bị rollback, transaction vẫn dùng tiếp | Cả transaction thành *aborted*, phải `ROLLBACK` |
| DDL trong transaction | Commit ngầm | Transactional, rollback được (trừ vài lệnh) |
| Savepoint | Có | Có |
| Isolation mặc định | `REPEATABLE READ` | `READ COMMITTED` |
| Nới durability | `innodb_flush_log_at_trx_commit` | `synchronous_commit` |

So sánh đầy đủ ở [chương 25](25-postgres-doi-chieu.md).

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Nghĩ rằng câu lỗi trong transaction làm MySQL tự rollback cả khối, nên vẫn `COMMIT` | MySQL chỉ rollback câu lỗi (trừ deadlock), các câu trước vẫn còn | Gặp lỗi thì `ROLLBACK` (trong `catch`) |
| `START TRANSACTION` lồng nhau để "tạo transaction con" | Câu thứ hai commit ngầm transaction đầu | Dùng `SAVEPOINT` |
| Chạy DDL (`CREATE TABLE`, `ALTER TABLE`, `TRUNCATE`) giữa transaction | Implicit commit, không rollback được | Tách DDL ra khỏi transaction nghiệp vụ |
| Bật `autocommit = 0` rồi quên commit | Transaction mở mãi, giữ lock và snapshot, phình undo log | Giữ autocommit mặc định, mở transaction tường minh |
| Gọi API, gửi email, upload file trong transaction | Transaction dài; tác dụng ngoài không rollback được | Làm trước/sau transaction, dùng outbox |
| Tin rằng "đã bọc transaction" là chống được bán quá tồn kho | Isolation mặc định không chặn lost update | Ghi có điều kiện (`WHERE stock > 0`), hoặc lock (chương 15) |
| Đặt `innodb_flush_log_at_trx_commit = 0/2` để "tăng tốc" mà không biết hệ quả | Có thể mất giao dịch đã báo commit khi sập | Giữ `1` cho dữ liệu quan trọng |
| Dùng bảng MyISAM cho dữ liệu nghiệp vụ | Không hỗ trợ transaction | Dùng InnoDB |
| Không kiểm tra `ROLLBACK TO SAVEPOINT` có nhả lock | Nó không nhả row lock | Kết thúc transaction sớm |

## Tóm tắt chương

- Transaction gom nhiều câu lệnh thành một đơn vị all-or-nothing: `COMMIT` hoặc `ROLLBACK`; thay đổi
  chưa commit không lộ ra cho người khác (ở mức mặc định).
- MySQL mặc định autocommit: mỗi câu lệnh lẻ là một transaction, và tự nó atomic.
- Dùng `START TRANSACTION` (không phải `BEGIN` trong stored program); transaction không lồng nhau,
  muốn điểm quay lui thì dùng `SAVEPOINT`.
- Câu lỗi trong transaction MySQL chỉ rollback câu đó (deadlock thì rollback cả transaction); ứng dụng
  phải tự `ROLLBACK`. PostgreSQL thì chuyển cả transaction sang trạng thái aborted.
- DDL, quản lý user, `LOCK TABLES`... gây implicit commit; bảng MyISAM, `AUTO_INCREMENT`, tác dụng bên
  ngoài DB không rollback được.
- A nhờ undo log; C phần lớn là việc của ứng dụng (DB chỉ giữ ràng buộc đã khai báo); I mặc định yếu
  hơn serializable; D nhờ redo log + `fsync` trước khi báo commit, cấu hình bằng
  `innodb_flush_log_at_trx_commit` (mặc định 1).
- Transaction dài giữ lock, cản purge, rollback lâu, gây trễ replication; phát hiện qua
  `information_schema.INNODB_TRX`.
- Không gọi API ngoài trong transaction; gọi trước/sau hoặc dùng outbox.

## Câu hỏi tự kiểm tra

1. Giải thích bằng ví dụ chuyển tiền hai vấn đề mà transaction giải quyết. (mục 2.1)
2. Ở chế độ autocommit, `UPDATE accounts SET balance = balance - 100` lỗi ở dòng thứ ba thì hai dòng
   đầu ra sao? Vì sao? (mục 4.2)
3. Trong transaction, câu thứ hai vi phạm `CHECK`. Nếu sau đó gọi `COMMIT`, câu thứ nhất có được
   lưu không? Deadlock thì khác thế nào? (mục 5.1)
4. Vì sao `START TRANSACTION` gọi hai lần không tạo transaction lồng nhau? Laravel làm "lồng nhau"
   bằng cách nào? (mục 3.8, 6.3)
5. Kể ba nhóm câu lệnh gây implicit commit. `CREATE TEMPORARY TABLE` có gây không, có rollback được
   không? (mục 7.1)
6. Tại sao nói chữ C trong ACID là trách nhiệm của ứng dụng nhiều hơn của DB? Cho một bất biến DB tự
   giữ được và một bất biến không. (mục 8.2)
7. Mô tả đường đi của một `COMMIT` tới đĩa. Vì sao ghi redo log nhanh hơn ghi trang dữ liệu? (mục 8.4)
8. So sánh ba giá trị của `innodb_flush_log_at_trx_commit`. Giá trị nào vẫn giữ atomicity? (mục 8.4)
9. Một transaction chỉ đọc nhưng mở 3 giờ có gây hại gì không? (mục 9.2)
10. Vì sao gọi API thanh toán trong transaction có thể khiến khách mất tiền mà không có đơn? (mục 10.1)

## Bài tập

1. **Thí nghiệm hai session.** Dùng dữ liệu mẫu, lặp lại timeline mục 3.4, sau đó thay bước 4 bằng
   `START TRANSACTION; UPDATE accounts SET balance = 0 WHERE id = 1;` ở session B. Ghi lại B có phải chờ không, chờ bao
   lâu thì lỗi (thử `SET SESSION innodb_lock_wait_timeout = 5;` trước), và sau lỗi transaction của B
   còn mở không (kiểm tra bằng `INNODB_TRX`).
2. **Implicit commit.** Viết một kịch bản SQL chứng minh `TRUNCATE TABLE` commit ngầm transaction đang
   mở, và một kịch bản chứng minh `CREATE TEMPORARY TABLE` thì không nhưng bảng tạm không bị rollback.
3. **Nhập dữ liệu với savepoint.** Có danh sách 5 lệnh chuyển tiền, trong đó 2 lệnh làm số dư âm. Viết
   một transaction (SQL thuần hoặc PHP + PDO) áp dụng các lệnh hợp lệ, bỏ qua lệnh lỗi bằng
   `SAVEPOINT`, cuối cùng kiểm tra tổng tiền vẫn bằng 800.
4. **Săn transaction dài.** Ở session A: `SET autocommit = 0; SELECT * FROM accounts;` rồi để yên. Ở
   session B, viết truy vấn trên `INNODB_TRX` tìm ra session A và cho biết dấu hiệu nào cho thấy nó
   "đang mở mà không làm gì". Sau đó dọn dẹp bằng `KILL`.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [START TRANSACTION, COMMIT, and ROLLBACK Statements](https://dev.mysql.com/doc/refman/8.4/en/commit.html),
  [Statements That Cannot Be Rolled Back](https://dev.mysql.com/doc/refman/8.4/en/cannot-roll-back.html),
  [Statements That Cause an Implicit Commit](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html),
  [SAVEPOINT, ROLLBACK TO SAVEPOINT, and RELEASE SAVEPOINT](https://dev.mysql.com/doc/refman/8.4/en/savepoint.html),
  [autocommit, Commit, and Rollback](https://dev.mysql.com/doc/refman/8.4/en/innodb-autocommit-commit-rollback.html),
  [InnoDB Error Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html),
  [MySQL and the ACID Model](https://dev.mysql.com/doc/refman/8.4/en/mysql-acid.html),
  [Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html),
  [InnoDB Startup Options and System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html)
  (`innodb_flush_log_at_trx_commit`, `innodb_lock_wait_timeout`, `innodb_rollback_on_timeout`),
  [Optimizing InnoDB Read-Only Transactions](https://dev.mysql.com/doc/refman/8.4/en/innodb-performance-ro-txn.html),
  [Purge Configuration](https://dev.mysql.com/doc/refman/8.4/en/innodb-purge-configuration.html),
  [InnoDB Recovery](https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html),
  [Atomic Data Definition Statement Support](https://dev.mysql.com/doc/refman/8.4/en/atomic-ddl.html),
  [CHECK Constraints](https://dev.mysql.com/doc/refman/8.4/en/create-table-check-constraints.html),
  [INNODB_TRX](https://dev.mysql.com/doc/refman/8.4/en/information-schema-innodb-trx-table.html).
- PHP Manual: [Transactions and auto-commit](https://www.php.net/manual/en/pdo.transactions.php),
  [PDO::beginTransaction](https://www.php.net/manual/en/pdo.begintransaction.php),
  [PDO::commit](https://www.php.net/manual/en/pdo.commit.php).
- Laravel 13: [Database Transactions](https://laravel.com/docs/13.x/database#database-transactions),
  mã nguồn [ManagesTransactions.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Concerns/ManagesTransactions.php).
- PostgreSQL 18: [Transactions (tutorial)](https://www.postgresql.org/docs/18/tutorial-transactions.html),
  [synchronous_commit](https://www.postgresql.org/docs/18/runtime-config-wal.html).
- Martin Kleppmann, *Designing Data-Intensive Applications*, chương 7 "Transactions", phần
  "The Meaning of ACID".
