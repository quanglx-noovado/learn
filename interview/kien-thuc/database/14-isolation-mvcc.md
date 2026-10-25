# Chương 14. Isolation level và MVCC

> [← Mục lục](README.md) · [← Chương 13: Transaction và ACID](13-transaction-acid.md) · [Chương 15: Lock và deadlock →](15-lock-deadlock.md)

**Bạn sẽ học được:**

- Khi nhiều transaction chạy đồng thời thì có thể sai theo những kiểu nào: dirty read,
  non-repeatable read, phantom, read skew, lost update, write skew. Mỗi kiểu có một timeline hai
  session để bạn tự gõ lại.
- Bốn isolation level của chuẩn SQL, chúng hứa chặn gì, và vì sao MySQL mặc định `REPEATABLE READ`
  còn PostgreSQL mặc định `READ COMMITTED`.
- MVCC: InnoDB giữ nhiều phiên bản của một dòng bằng undo log, và dùng *read view* để quyết định mỗi
  câu đọc thấy phiên bản nào.
- Hai kiểu đọc của InnoDB: *consistent read* và *locking read*, và hệ quả kỳ lạ khi trộn chúng.
- Hành vi thật của InnoDB và PostgreSQL ở từng level (lost update lọt qua RR của MySQL, lỗi 40001
  của PostgreSQL, SSI), từ đó biết chọn level nào và chống lost update ra sao.

**Cần biết trước:** [Chương 13](13-transaction-acid.md) (transaction, `START TRANSACTION`,
`COMMIT`, `ROLLBACK`, autocommit, chữ I trong ACID). Biết `INDEX` ở mức
[chương 11](11-index.md) sẽ giúp đọc mục 6.4. Chi tiết về lock (record lock, gap lock, next-key
lock, deadlock) để dành cho [chương 15](15-lock-deadlock.md); chương này chỉ dùng chúng ở mức "có
khoá, phải chờ".

## 1. Dữ liệu mẫu của chương

Mọi ví dụ chạy trên MySQL 8.4, bảng InnoDB. Chỗ nào nói về PostgreSQL sẽ ghi rõ. Cách chạy MySQL bằng
Docker và cách mở hai session A, B giống hệt [chương 13 mục 1](13-transaction-acid.md#1-dữ-liệu-mẫu-của-chương):
mỗi cửa sổ `mysql` là một session.

Bảng `accounts` dùng lại từ chương 13 (tổng tiền luôn phải là 800), thêm hai bảng cho các ví dụ
tồn kho và lịch trực:

```sql
DROP DATABASE IF EXISTS ch14;      -- database riêng của chương
CREATE DATABASE ch14;
USE ch14;

-- Tài khoản: bất biến "tổng số dư = 800"
CREATE TABLE accounts (
  id      INT PRIMARY KEY,
  owner   VARCHAR(50)   NOT NULL,
  balance DECIMAL(12,2) NOT NULL
) ENGINE = InnoDB;

INSERT INTO accounts VALUES
  (1, 'An',   500.00),
  (2, 'Bình', 300.00),
  (3, 'Chi',    0.00);

-- Sản phẩm: cột price KHÔNG có index (cố ý, dùng ở mục 6.4)
CREATE TABLE products (
  id    INT PRIMARY KEY,
  name  VARCHAR(50) NOT NULL,
  price INT NOT NULL,
  stock INT NOT NULL
) ENGINE = InnoDB;

INSERT INTO products VALUES
  (1, 'Bàn phím', 100,  1),
  (2, 'Chuột',     50, 10);

-- Lịch trực: luật nghiệp vụ "mỗi ca luôn có ít nhất 1 bác sĩ trực"
CREATE TABLE doctors (
  id       INT PRIMARY KEY,
  name     VARCHAR(20) NOT NULL,
  shift_id INT NOT NULL,
  on_call  BOOLEAN NOT NULL,
  KEY idx_shift (shift_id)
) ENGINE = InnoDB;

INSERT INTO doctors VALUES
  (1, 'Alice', 1, TRUE),
  (2, 'Bob',   1, TRUE);
```

⚠️ **Trước mỗi timeline, chạy lại toàn bộ đoạn SQL trên** để dữ liệu về trạng thái ban đầu. Các
timeline đều giả định dữ liệu vừa được tạo lại, và cả hai session đang ở `USE ch14;`.

Cách đọc timeline: làm lần lượt theo cột "Bước", từ trên xuống. Ô trống nghĩa là session đó không làm
gì ở bước ấy. Nếu một session không ghi `START TRANSACTION`, nó đang ở chế độ autocommit: mỗi câu là
một transaction riêng và commit ngay (chương 13 mục 4).

## 2. Đặt và xem isolation level

Trước khi xem các hiện tượng, cần biết cách đổi level, vì nhiều timeline bên dưới bắt đầu bằng việc
đổi level của một session.

### 2.1 Trong MySQL

```sql
SELECT @@transaction_isolation;          -- level của session hiện tại
-- Kết quả mong đợi (mặc định):
-- +-------------------------+
-- | @@transaction_isolation |
-- +-------------------------+
-- | REPEATABLE-READ         |
-- +-------------------------+

SELECT @@GLOBAL.transaction_isolation;   -- level mặc định cho các session MỚI
```

Ba cách đổi, khác nhau ở phạm vi:

```sql
-- (1) Mọi transaction SAU NÀY của session hiện tại
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;

-- (2) Chỉ đúng MỘT transaction kế tiếp, xong quay về level của session
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;

-- (3) Mặc định cho các session tạo SAU câu lệnh này (cần quyền quản trị);
--     session đang mở, kể cả session chạy câu này, không bị ảnh hưởng
SET GLOBAL TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

Bốn giá trị hợp lệ trong câu `SET ... TRANSACTION ISOLATION LEVEL`: `READ UNCOMMITTED`,
`READ COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE`. Khi đọc biến `transaction_isolation` thì giá trị
có gạch nối: `READ-COMMITTED`, `REPEATABLE-READ`... Muốn đặt cho cả server từ lúc khởi động thì ghi
trong file cấu hình, mục `[mysqld]`: `transaction-isolation = READ-COMMITTED`.

⚠️ Cạm bẫy hay gặp khi tự thử nghiệm:

- `SET TRANSACTION ...` (không có `SESSION`) chỉ áp dụng cho **một** transaction kế tiếp. Nhiều người
  tưởng đã đổi cả session, chạy timeline thứ hai thì kết quả "sai".
- Không đổi được level giữa chừng: `SET TRANSACTION ...` khi đang có transaction mở sẽ báo lỗi
  `Transaction characteristics can't be changed while a transaction is in progress`. Đổi trước
  `START TRANSACTION`.
- Biến cũ `tx_isolation` đã bị bỏ từ MySQL 8.0; tài liệu, code cũ còn dùng thì đổi sang
  `transaction_isolation`.

### 2.2 Trong PostgreSQL

```sql
SHOW transaction_isolation;                     -- read committed (mặc định)
BEGIN ISOLATION LEVEL REPEATABLE READ;          -- đặt ngay khi mở transaction
-- hoặc: BEGIN; SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;  (phải trước câu truy vấn đầu tiên)
SET SESSION CHARACTERISTICS AS TRANSACTION ISOLATION LEVEL SERIALIZABLE;  -- cho cả session
```

Mặc định toàn server nằm ở tham số `default_transaction_isolation`.

## 3. Những gì có thể sai khi chạy đồng thời

### 3.1 Vì sao phải "cô lập"

Chương 13 (mục 8.3) nói chữ I trong ACID hứa: các transaction chạy đồng thời không giẫm lên nhau.
Mức lý tưởng có tên *serializable*: kết quả của một nhóm transaction chạy đồng thời phải **giống
như** khi chúng chạy lần lượt từng cái một, theo một thứ tự nào đó.

Cách dễ nhất để đạt điều đó là thật sự chạy lần lượt: một transaction xong mới tới transaction sau.
Nhưng một server có hàng trăm connection, phần lớn transaction không hề đụng nhau; bắt tất cả xếp
hàng thì quá chậm. Vì vậy database cho chạy xen kẽ, và đưa ra nhiều *mức cô lập* (isolation level):
mức càng thấp thì càng ít chờ, càng nhanh, nhưng càng để lọt nhiều kiểu sai.

Mỗi kết quả không thể có được bằng bất kỳ thứ tự chạy tuần tự nào gọi là một *anomaly* (hiện tượng
bất thường). Các mục 3.2 đến 3.7 lần lượt đi qua sáu anomaly hay gặp nhất. Mỗi mục có: định nghĩa,
timeline trên MySQL ở level mà nó xảy ra, và level nào chặn được nó.

Còn một anomaly nữa, *dirty write* (ghi đè lên dữ liệu chưa commit của người khác), nhưng nó bị
chặn ở **mọi** level của cả MySQL lẫn PostgreSQL: mọi câu ghi đều khoá dòng và giữ khoá tới lúc
commit hoặc rollback, nên người thứ hai muốn ghi cùng dòng phải chờ. Bạn đã thấy điều này ở chương
13 mục 3.4.

### 3.2 Dirty read: đọc dữ liệu chưa commit

**Là gì:** transaction A đọc được thay đổi mà transaction B **chưa commit**. Nếu sau đó B rollback,
A đã dùng một giá trị chưa từng tồn tại chính thức.

**Timeline** (session A ở `READ UNCOMMITTED`, level duy nhất của MySQL để lọt dirty read):

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 0 | `SET SESSION TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;` | | |
| 1 | | `START TRANSACTION;` | |
| 2 | | `UPDATE accounts SET balance = balance - 100 WHERE id = 1;` | B trừ An 100, chưa commit |
| 3 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy **400.00**: dirty read |
| 4 | | `ROLLBACK;` | B huỷ |
| 5 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy **500.00** |

Nếu ở bước 3 code của A đã dựa vào con số 400 (ví dụ từ chối một khoản rút 450), quyết định đó dựa
trên dữ liệu "ma". Chạy lại timeline với A ở level mặc định (bỏ bước 0): bước 3 trả về 500.00.

**Ai chặn:** mọi level từ `READ COMMITTED` trở lên. PostgreSQL chấp nhận cú pháp
`READ UNCOMMITTED` nhưng chạy y như `READ COMMITTED`, tức là PostgreSQL **không bao giờ** có dirty
read.

### 3.3 Non-repeatable read: đọc lại một dòng, ra giá trị khác

**Là gì:** trong cùng một transaction, A đọc một dòng hai lần; giữa hai lần, B sửa dòng đó và
commit; lần đọc sau của A ra giá trị khác lần đầu. Khác dirty read ở chỗ: giá trị mới **đã commit**,
nó là dữ liệu thật. Vấn đề là A không còn nhìn thấy một thế giới ổn định.

**Timeline** (A ở `READ COMMITTED`):

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 0 | `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;` | | |
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy 500.00 |
| 3 | | `UPDATE accounts SET balance = 450 WHERE id = 1;` | Autocommit: B commit ngay |
| 4 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy **450.00**: cùng câu, cùng transaction, khác kết quả |
| 5 | `COMMIT;` | | |

Chạy lại với A ở `REPEATABLE READ` (bỏ bước 0, hoặc đặt lại `SET SESSION TRANSACTION ISOLATION LEVEL
REPEATABLE READ;`): bước 4 vẫn ra 500.00. Muốn thấy 450 thì A phải commit rồi đọc trong transaction
mới. Lý do nằm ở MVCC (mục 5).

**Ai chặn:** `REPEATABLE READ` và `SERIALIZABLE`.

### 3.4 Phantom: tập dòng thoả điều kiện thay đổi

**Là gì:** A chạy một câu có điều kiện (`WHERE price >= 100`) hai lần; giữa hai lần, B **chèn**
(hoặc xoá) một dòng thoả điều kiện và commit; lần sau A thấy thêm (hoặc mất) dòng. Dòng mới xuất
hiện như "bóng ma", nên gọi là *phantom*. Khác non-repeatable read: không dòng nào bị sửa, mà
**thành viên** của tập kết quả thay đổi.

**Timeline** (A ở `READ COMMITTED`):

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 0 | `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;` | | |
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT id, price FROM products WHERE price >= 100;` | | 1 dòng: id 1 (100) |
| 3 | | `INSERT INTO products VALUES (3, 'Màn hình', 300, 5);` | B commit ngay |
| 4 | `SELECT id, price FROM products WHERE price >= 100;` | | **2 dòng**: id 1 (100), id 3 (300) |
| 5 | `COMMIT;` | | |

Ví dụ thực tế: báo cáo đếm đơn hàng hôm nay ra 10, rồi tính tổng tiền của "các đơn hôm nay" ra số
tiền của 11 đơn. Hai con số trong cùng một báo cáo không khớp nhau.

**Ai chặn:** theo chuẩn SQL chỉ `SERIALIZABLE` bắt buộc phải chặn. Thực tế, với `SELECT` thường,
`REPEATABLE READ` của cả MySQL lẫn PostgreSQL cũng chặn (chạy lại timeline ở RR: bước 4 vẫn 1 dòng).
Nhưng ở MySQL có ngoại lệ khi trộn với câu ghi hoặc locking read, xem mục 6.

### 3.5 Read skew: đọc hai dòng ở hai thời điểm

**Là gì:** A đọc hai dòng có liên quan với nhau, nhưng ở hai thời điểm khác nhau; giữa hai lần đọc,
B sửa cả hai dòng và commit. A ghép lại thấy một trạng thái **chưa từng tồn tại**. Đây là
non-repeatable read nhìn từ góc "nhiều dòng": A không đọc lại dòng nào cả mà vẫn sai.

**Timeline** (A ở `READ COMMITTED`; B chuyển 100 từ An sang Bình):

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 0 | `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;` | | |
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy An 500.00 |
| 3 | | `START TRANSACTION;` | |
| 4 | | `UPDATE accounts SET balance = balance - 100 WHERE id = 1;` | |
| 5 | | `UPDATE accounts SET balance = balance + 100 WHERE id = 2;` | |
| 6 | | `COMMIT;` | An 400, Bình 400 |
| 7 | `SELECT balance FROM accounts WHERE id = 2;` | | A thấy Bình **400.00** |
| 8 | `COMMIT;` | | A tính tổng An + Bình + Chi = 500 + 400 + 0 = **900** ≠ 800 |

Không có thời điểm nào tổng tiền là 900: trước khi chuyển là 500 + 300, sau khi chuyển là 400 + 400.
Nếu A là job đối soát cuối ngày, nó sẽ báo "thừa 100" một cách vô lý.

Ở `REPEATABLE READ`, bước 7 thấy 300.00 (snapshot từ bước 2), tổng đúng 800. Một cách khác không
phụ thuộc level: đọc tất cả bằng **một** câu lệnh (`SELECT SUM(balance) FROM accounts;`), vì ở mọi
level từ RC trở lên, một câu lệnh luôn đọc trên một snapshot nhất quán.

**Ai chặn:** `REPEATABLE READ` và `SERIALIZABLE` (với transaction chỉ đọc; mục 6 có ngoại lệ ở MySQL).

### 3.6 Lost update: cập nhật bị mất

**Là gì:** A và B cùng đọc một dòng, mỗi bên tính giá trị mới **ở ứng dụng** rồi ghi lại. Bên ghi
sau đè lên bên ghi trước, thay đổi của bên trước biến mất. Mẫu code gây ra nó có tên
*read-modify-write*: đọc, sửa trong bộ nhớ, ghi lại.

**Timeline** (cả hai ở `REPEATABLE READ`, level mặc định của MySQL; An có 500, A rút 30, B nạp 50,
đúng ra phải còn 520):

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy 500.00 |
| 3 | | `START TRANSACTION;` | |
| 4 | | `SELECT balance FROM accounts WHERE id = 1;` | B thấy 500.00 |
| 5 | App tính 500 - 30. `UPDATE accounts SET balance = 470 WHERE id = 1;` | | A giữ khoá dòng 1 |
| 6 | | App tính 500 + 50. `UPDATE accounts SET balance = 550 WHERE id = 1;` | **B chờ** khoá của A |
| 7 | `COMMIT;` | | B hết chờ, ghi 550, **không lỗi** |
| 8 | | `COMMIT;` | |
| 9 | `SELECT balance FROM accounts WHERE id = 1;` | | **550.00**. Khoản rút 30 biến mất |

Transaction không hề "hỏng": mỗi bên đều all-or-nothing, không ai đọc dữ liệu chưa commit. Lỗi nằm ở
chỗ giá trị B ghi được tính từ một lần đọc đã cũ. InnoDB chỉ bắt B chờ khoá rồi cho ghi; nó **không**
kiểm tra "dòng mình sắp ghi có bị ai sửa từ lúc mình đọc không".

Chương 13 mục 8.3 có cùng hiện tượng với tồn kho: hai request cùng thấy còn 1 món, cùng bán, ra hai
đơn hàng cho một món.

**Ai chặn:** ở MySQL chỉ có `SERIALIZABLE` (bằng deadlock, mục 7.3). Ở PostgreSQL thì `REPEATABLE
READ` đã chặn (bằng lỗi 40001, mục 7.1). Cách chống trong ứng dụng ở mục 9.

### 3.7 Write skew: mỗi bên ghi một dòng khác, gộp lại thì sai

**Là gì:** A và B cùng đọc **một tập** dữ liệu để kiểm tra một điều kiện, cả hai thấy điều kiện
đúng, rồi mỗi bên ghi một dòng **khác nhau**. Từng bên riêng lẻ không sai, nhưng gộp lại thì điều
kiện bị vi phạm. Vì không ai ghi đè dòng của ai, mọi cơ chế chỉ phát hiện xung đột trên **cùng một
dòng** đều bỏ sót.

Ví dụ kinh điển (sách *Designing Data-Intensive Applications*, DDIA): luật "mỗi ca luôn có ít nhất
một bác sĩ trực". Alice và Bob đang cùng trực ca 1, cùng bấm "xin nghỉ" gần như một lúc. Code nút này:
đếm số người đang trực, còn ít nhất 2 thì cho người bấm nghỉ.

**Timeline** (cả hai ở `REPEATABLE READ`):

| Bước | Session A (Alice) | Session B (Bob) | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT COUNT(*) FROM doctors WHERE shift_id = 1 AND on_call = TRUE;` | | A thấy 2 |
| 3 | | `START TRANSACTION;` | |
| 4 | | `SELECT COUNT(*) FROM doctors WHERE shift_id = 1 AND on_call = TRUE;` | B thấy 2 |
| 5 | App: 2 ≥ 2, cho nghỉ. `UPDATE doctors SET on_call = FALSE WHERE id = 1;` | | A khoá dòng 1 |
| 6 | | App: 2 ≥ 2, cho nghỉ. `UPDATE doctors SET on_call = FALSE WHERE id = 2;` | Không chờ: dòng 2 không ai khoá |
| 7 | `COMMIT;` | `COMMIT;` | Cả hai thành công. Ca 1 **không còn ai trực** |

Cấu trúc chung của write skew (theo DDIA): (1) một câu `SELECT` kiểm tra điều kiện; (2) app quyết
định dựa trên kết quả; (3) app ghi, và chính câu ghi làm thay đổi kết quả của bước 1. Các dạng khác
cùng cấu trúc: đặt phòng họp trùng giờ, hai người cùng đăng ký một username, rút tiền từ hai tài khoản
có hạn mức chung.

**Ai chặn:** chỉ `SERIALIZABLE`, ở cả MySQL lẫn PostgreSQL. `REPEATABLE READ` của PostgreSQL, dù
chặn được lost update, vẫn để lọt write skew.

### 3.8 Phân loại cho dễ nhớ

- **Chuyện của đọc:** dirty read (thấy cái chưa commit), non-repeatable read (một dòng đổi giá
  trị), phantom (tập dòng đổi thành viên), read skew (nhiều dòng đọc ở nhiều thời điểm).
- **Chuyện của đọc rồi quyết định ghi:** lost update (hai bên ghi **cùng** một dòng), write skew (hai
  bên ghi **khác** dòng).

Nhóm thứ hai nguy hiểm hơn vì nó làm **hỏng dữ liệu đã lưu**, còn nhóm thứ nhất thường chỉ làm sai
một lần đọc (trừ khi app ghi dựa trên lần đọc sai đó).

## 4. Bốn isolation level của chuẩn SQL

### 4.1 Định nghĩa theo chuẩn

Chuẩn SQL định nghĩa bốn level bằng cách nói level nào **cho phép** hiện tượng nào trong ba hiện
tượng dirty read, non-repeatable read, phantom:

| Level | Dirty read | Non-repeatable read | Phantom |
|---|---|---|---|
| `READ UNCOMMITTED` | Có thể xảy ra | Có thể xảy ra | Có thể xảy ra |
| `READ COMMITTED` | Không | Có thể xảy ra | Có thể xảy ra |
| `REPEATABLE READ` | Không | Không | Có thể xảy ra |
| `SERIALIZABLE` | Không | Không | Không |

Đọc bảng này cần hai lưu ý:

1. Chuẩn chỉ nói mức **tối thiểu** phải chặn. Một DB được phép chặn nhiều hơn. Ví dụ PostgreSQL ghi
   rõ trong tài liệu: phantom ở RR "allowed, but not in PG".
2. Bảng không nhắc tới lost update, read skew, write skew. Bài báo *A Critique of ANSI SQL Isolation
   Levels* (Berenson và cộng sự, 1995) đã chỉ ra rằng định nghĩa bằng ba hiện tượng này vừa mơ hồ vừa
   thiếu. Hệ quả thực tế: **cùng một tên level ở hai DB có thể đảm bảo những điều khác nhau**.
   `REPEATABLE READ` của MySQL và của PostgreSQL là ví dụ rõ nhất (mục 7).

Ngoài ra `SERIALIZABLE` theo chuẩn nghĩa là kết quả tương đương một thứ tự chạy tuần tự, tức chặn
**mọi** anomaly, kể cả write skew, chứ không chỉ ba hiện tượng trong bảng.

### 4.2 Mặc định của MySQL và PostgreSQL

| | MySQL (InnoDB) | PostgreSQL |
|---|---|---|
| Level mặc định | `REPEATABLE READ` | `READ COMMITTED` |
| Hỗ trợ `READ UNCOMMITTED` | Có, có dirty read thật | Chấp nhận cú pháp, chạy như `READ COMMITTED` |

Vì sao khác nhau? Tài liệu chính thức không giải thích lý do chọn mặc định. Cách giải thích hay được
nhắc tới là lịch sử replication: MySQL thời đầu chỉ có binlog dạng câu lệnh (*statement-based*),
replica chạy lại đúng câu SQL, và RR cùng gap lock giúp các câu ghi cho cùng kết quả trên replica.
Dấu vết còn lại đến giờ: MySQL chỉ cho dùng `READ COMMITTED` với binlog dạng row-based (mục 8.2).
Hãy coi đây là bối cảnh để nhớ, không phải lý do chính thức.

Hệ quả cho người chuyển giữa hai DB: code chạy đúng trên MySQL có thể thấy non-repeatable read khi
chuyển sang PostgreSQL, và ngược lại code dựa vào lỗi 40001 của PostgreSQL RR để chặn lost update sẽ
âm thầm mất dữ liệu trên MySQL RR.

## 5. MVCC: mỗi dòng có nhiều phiên bản

### 5.1 Vấn đề: đọc và ghi cùng một dòng

Ở timeline mục 3.3 (chạy ở RR), session B đã sửa An thành 450 và commit, vậy mà A vẫn đọc ra 500. Còn
ở chương 13 mục 3.4, B đọc dòng đang bị A sửa dở mà **không phải chờ**. Database lấy giá trị 500 ở
đâu ra, khi trên trang dữ liệu chỉ còn 450?

Có hai cách để giữ cô lập giữa người đọc và người ghi:

1. **Dùng khoá cho cả đọc:** người đọc lấy khoá chia sẻ, người ghi lấy khoá độc quyền, ai đến sau
   thì chờ. Đúng, nhưng một báo cáo quét cả bảng mất 10 phút sẽ chặn mọi câu `UPDATE` trong 10 phút.
2. **Giữ nhiều phiên bản:** người ghi tạo phiên bản mới, phiên bản cũ vẫn được giữ lại một thời gian;
   người đọc được chỉ định đọc phiên bản phù hợp với "thời điểm" của mình. Không ai phải chờ ai.

Cách thứ hai có tên *MVCC* (Multi-Version Concurrency Control, điều khiển đồng thời đa phiên bản).
InnoDB và PostgreSQL đều dùng MVCC. Khẩu quyết cần nhớ:

> **Đọc không chặn ghi, ghi không chặn đọc.** Chỉ có **ghi với ghi** trên cùng dòng là phải chờ nhau.

("Đọc" ở đây là `SELECT` thường. Locking read ở mục 6 là chuyện khác.)

### 5.2 Phiên bản dòng và undo log trong InnoDB

Theo tài liệu MySQL 8.4 (mục *InnoDB Multi-Versioning*), InnoDB thêm vào mỗi dòng mấy cột ẩn, trong
đó hai cột quan trọng cho MVCC:

- `DB_TRX_ID` (6 byte): id của transaction cuối cùng đã chèn hoặc sửa dòng. Xoá dòng được InnoDB coi
  là một kiểu sửa: đặt một bit đánh dấu "đã xoá".
- `DB_ROLL_PTR` (7 byte, *roll pointer*): trỏ tới một bản ghi trong *undo log*. Nếu dòng đã bị sửa,
  bản ghi undo đó chứa đủ thông tin để dựng lại nội dung dòng **trước khi** sửa.

Khi một câu `UPDATE` sửa dòng, InnoDB sửa **tại chỗ** trong clustered index, nhưng trước đó ghi giá
trị cũ vào undo log. Bản ghi undo lại có roll pointer trỏ tới phiên bản cũ hơn nữa. Kết quả là một
chuỗi phiên bản (*version chain*). Sau timeline mục 3.3, dòng An trông như sau (id transaction là
**số minh hoạ**):

```
Clustered index (bản mới nhất)                Undo log
┌─────────────────────────────────────┐       ┌──────────────────────────────┐
│ id=1 owner=An balance=450.00        │       │ id=1 balance=500.00          │
│ DB_TRX_ID=1205  DB_ROLL_PTR ────────┼──────►│ DB_TRX_ID=1100 (lúc INSERT)  │
└─────────────────────────────────────┘       └──────────────────────────────┘
   (do B, transaction 1205, ghi)                 (phiên bản trước khi B sửa)
```

Undo log vì thế phục vụ hai việc: **rollback** (chương 13, chữ A trong ACID) và **MVCC** (cho người
khác đọc bản cũ). Chi tiết cách lưu trữ undo, chuỗi phiên bản và secondary index nằm ở
[chương 16 mục 6](16-ben-trong-innodb.md#6-undo-log-mvcc-và-purge).

### 5.3 Read view: quyết định phiên bản nào được thấy

Một câu `SELECT` thường cần biết "từ góc nhìn của tôi, phiên bản nào là đúng?". InnoDB trả lời bằng
*read view* (tài liệu cũng gọi là *snapshot*, ảnh chụp, hay *timepoint*). Hiểu đơn giản, khi tạo read
view, InnoDB ghi lại danh sách các transaction **đang chạy dở** lúc đó. Từ đó, với mỗi phiên bản dòng
có `DB_TRX_ID = T`:

- `T` là chính transaction của mình: **thấy** (luôn thấy thay đổi của chính mình).
- `T` đã commit **trước** khi tạo read view: **thấy**.
- `T` còn đang chạy lúc tạo read view, hoặc bắt đầu **sau** đó: **không thấy**. InnoDB lần theo roll
  pointer xuống phiên bản cũ hơn và kiểm tra lại, cho tới khi gặp phiên bản thấy được. Nếu hết chuỗi
  mà không có, dòng coi như không tồn tại với read view này (đó là lý do dòng mới chèn bởi người khác
  không hiện ra).

Quy tắc chính xác theo con số id (so sánh với id nhỏ nhất đang chạy, id sẽ cấp tiếp theo) được trình
bày ở [chương 16 mục 6.2](16-ben-trong-innodb.md#62-version-chain-chuỗi-phiên-bản). Ở mức người dùng,
câu hỏi quan trọng hơn là **read view được tạo khi nào**, vì đó chính là khác biệt giữa các level:

| Level | Read view cho `SELECT` thường |
|---|---|
| `READ UNCOMMITTED` | Không dùng read view: đọc phiên bản mới nhất, kể cả chưa commit |
| `READ COMMITTED` | Tạo **mới cho mỗi câu lệnh** |
| `REPEATABLE READ` | Tạo ở **câu consistent read đầu tiên** của transaction, dùng tới cuối transaction |
| `SERIALIZABLE` | `SELECT` thường bị đổi thành locking read (mục 7.3), nên không dùng read view, trừ khi câu `SELECT` chạy lẻ ở chế độ autocommit (không nằm trong transaction mở) |

Đọc lại các timeline ở mục 3 với bảng này:

- Mục 3.3 ở RC: bước 4 là câu mới, read view mới, thấy bản 450 do B đã commit. Ở RR: dùng lại read
  view từ bước 2, lúc đó B chưa sửa, nên InnoDB lần theo undo và trả về 500.
- Mục 3.4: dòng id 3 do B chèn sau khi read view của A (ở RR) được tạo, nên không thấy.
- Mục 3.2: RU không dùng read view nên thấy bản 400 chưa commit.

### 5.4 Snapshot được chụp ở câu đọc đầu tiên, không phải ở START TRANSACTION

⚠️ Đây là điểm hay bị hỏi vặn. Ở RR, `START TRANSACTION` **chưa** tạo read view. Read view được tạo
ở câu consistent read đầu tiên.

| Bước | Session A (RR) | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | Chưa có read view |
| 2 | | `UPDATE accounts SET balance = 450 WHERE id = 1;` | B commit ngay |
| 3 | `SELECT balance FROM accounts WHERE id = 1;` | | A thấy **450.00**: read view tạo ở bước này, sau khi B đã commit |
| 4 | | `UPDATE accounts SET balance = 400 WHERE id = 1;` | |
| 5 | `SELECT balance FROM accounts WHERE id = 1;` | | Vẫn 450.00 |
| 6 | `COMMIT;` | | |

Muốn chụp ngay lúc mở transaction thì dùng `START TRANSACTION WITH CONSISTENT SNAPSHOT;` (chương 13
mục 3.5 đã giới thiệu cú pháp). Thay bước 1 bằng câu này: bước 3 sẽ ra 500.00. Tuỳ chọn này chỉ có
tác dụng ở RR. `mysqldump --single-transaction` dùng đúng cơ chế này để lấy bản backup nhất quán của
mọi bảng InnoDB mà không khoá ai.

PostgreSQL tương tự: snapshot của transaction RR được chụp ở câu lệnh đầu tiên (không tính các lệnh
điều khiển transaction), không phải ở `BEGIN`.

### 5.5 Cái giá của MVCC

Phiên bản cũ không thể giữ mãi. InnoDB chỉ dọn (*purge*) được bản ghi undo khi **không còn read view
nào** có thể cần đến nó. Hệ quả: một transaction RR mở rồi để đó hàng giờ (kể cả chỉ đọc) giữ lại
toàn bộ lịch sử thay đổi của mọi bảng từ thời điểm read view của nó; undo phình to và các câu đọc
khác phải lần qua chuỗi phiên bản dài hơn. Đây là một tác hại của transaction dài đã nêu ở
[chương 13 mục 9](13-transaction-acid.md#9-transaction-dài-và-tác-hại); cơ chế purge và chỉ số
*history list length* ở [chương 16 mục 6.5](16-ben-trong-innodb.md#65-history-list-length-và-sự-cố-transaction-quên-đóng).

### 5.6 Đối chiếu PostgreSQL

PostgreSQL cũng MVCC nhưng lưu phiên bản theo cách khác:

| | InnoDB | PostgreSQL |
|---|---|---|
| `UPDATE` | Sửa tại chỗ, bản cũ vào undo log | Ghi **một bản dòng mới** (tuple) ngay trong bảng, bản cũ vẫn nằm đó |
| Đánh dấu phiên bản | `DB_TRX_ID`, `DB_ROLL_PTR` | `xmin` (transaction tạo), `xmax` (transaction xoá/sửa) trên mỗi tuple |
| Dọn bản cũ | Purge (luồng nền) | `VACUUM` / autovacuum |
| Hệ quả hay gặp | Undo phình khi có transaction dài | Bảng và index phình (*bloat*) khi vacuum không theo kịp |

Ở mức người dùng, hai bên giống nhau: `SELECT` thường đọc snapshot, không chặn và không bị chặn bởi
người ghi.

## 6. Hành vi thực tế của InnoDB

### 6.1 Hai kiểu đọc: consistent read và locking read

Tới đây, mọi `SELECT` đều là *consistent read* (đọc nhất quán, còn gọi *nonlocking read*): đọc theo
read view, không lấy khoá, không chờ ai. Nhưng InnoDB còn một kiểu đọc thứ hai:

| | Consistent read | Locking read |
|---|---|---|
| Câu lệnh | `SELECT` thường | `SELECT ... FOR UPDATE`, `SELECT ... FOR SHARE`, và phần **tìm dòng** của `UPDATE`, `DELETE` |
| Đọc phiên bản nào | Phiên bản theo read view (có thể cũ) | Phiên bản **mới nhất đã commit** |
| Lấy khoá | Không | Có, khoá các dòng tìm được (ở RR còn khoá cả khoảng trống, chương 15) |
| Gặp dòng người khác đang khoá | Không chờ, đọc bản cũ từ undo | **Chờ** |

Vì sao `UPDATE` và `DELETE` phải đọc bản mới nhất? Vì không thể sửa một phiên bản cũ: muốn ghi thì
phải ghi lên bản hiện hành, và phải khoá nó để không ai ghi chồng. (`FOR SHARE` là cú pháp từ MySQL
8.0; cú pháp cũ `LOCK IN SHARE MODE` vẫn được hỗ trợ và có cùng ý nghĩa.)

Hai thế giới cùng tồn tại trong một transaction RR:

| Bước | Session A (RR) | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT balance FROM accounts WHERE id = 1;` | | 500.00 (tạo read view) |
| 3 | | `UPDATE accounts SET balance = 450 WHERE id = 1;` | B commit ngay |
| 4 | `SELECT balance FROM accounts WHERE id = 1;` | | 500.00: consistent read, theo read view |
| 5 | `SELECT balance FROM accounts WHERE id = 1 FOR SHARE;` | | **450.00**: locking read, bản mới nhất |
| 6 | `SELECT balance FROM accounts WHERE id = 1;` | | Lại **500.00** |
| 7 | `COMMIT;` | | |

Cùng một dòng, trong cùng một transaction, ba câu đọc liên tiếp ra 500, 450, 500. Bước 6 vẫn ra 500 vì
`FOR SHARE` chỉ khoá, không sửa dòng, nên phiên bản mới nhất vẫn mang id transaction của B, không thấy
được theo read view của A.

### 6.2 DML chạm vào dòng mà SELECT không thấy

Tài liệu MySQL viết rõ: snapshot áp dụng cho `SELECT`, **không nhất thiết** cho câu DML. Một `UPDATE`
hay `DELETE` trong transaction RR có thể tác động lên những dòng mà người khác vừa commit, dù chính
transaction đó không `SELECT` thấy chúng. Và một khi đã sửa, dòng đó trở nên **thấy được** với
transaction (vì giờ phiên bản mới nhất mang id của chính mình).

| Bước | Session A (RR) | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT id, price FROM products WHERE price >= 100;` | | 1 dòng: id 1 (100) |
| 3 | | `INSERT INTO products VALUES (3, 'Màn hình', 300, 5);` | B commit ngay (A không giữ khoá nào) |
| 4 | `SELECT id, price FROM products WHERE price >= 100;` | | Vẫn 1 dòng: không phantom |
| 5 | `UPDATE products SET price = price + 10 WHERE price >= 100;` | | `Rows matched: 2  Changed: 2`: `UPDATE` đọc bản mới nhất nên chạm cả id 3 |
| 6 | `SELECT id, price FROM products WHERE price >= 100;` | | **2 dòng**: id 1 (110), id 3 (310) |
| 7 | `COMMIT;` | | |

Bước 4 cho thấy RR chặn phantom với `SELECT` thường. Bước 5 và 6 cho thấy phantom "lọt vào" khi
transaction có ghi. Trường hợp ngược lại cũng xảy ra: `SELECT` thấy một dòng nhưng `UPDATE` thì không.

| Bước | Session A (RR) | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT balance FROM accounts WHERE id = 2;` | | 300.00 |
| 3 | | `UPDATE accounts SET balance = 350 WHERE id = 2;` | B commit ngay |
| 4 | `UPDATE accounts SET owner = 'Bình (VIP)' WHERE balance = 300;` | | `Rows matched: 0`: bản mới nhất là 350 |
| 5 | `SELECT id, owner, balance FROM accounts WHERE balance = 300;` | | Vẫn trả về dòng 2: `Bình`, 300.00 |
| 6 | `COMMIT;` | | |

Transaction A vừa "thấy" Bình có 300 (bước 5) vừa "không thấy" (bước 4). Đây là lý do tài liệu MySQL
**khuyên không trộn** câu có khoá (`UPDATE`, `INSERT`, `DELETE`, `SELECT ... FOR ...`) với `SELECT`
thường trong cùng một transaction RR: hai kiểu đọc nhìn hai trạng thái khác nhau của database. Cũng vì
những hành vi này mà RR của MySQL **không** phải *snapshot isolation* đúng nghĩa (như RR của
PostgreSQL, mục 7.1).

Hệ quả thực hành: nếu một transaction đọc rồi ghi dựa trên cái đã đọc, câu đọc đó nên là locking read
(`FOR UPDATE`) để nó nhìn cùng "thế giới" với câu ghi. Chương 15 đi sâu.

### 6.3 Lost update lọt qua RR

Nhìn lại timeline mục 3.6 với kiến thức mới: bước 2 và 4 là consistent read, cả hai thấy 500 từ read
view. Bước 5 và 6 là `UPDATE`, locking read: B phải chờ A, và khi A commit, B đọc bản mới nhất (470),
khoá nó, rồi ghi đè bằng giá trị **app đã tính sẵn** là 550. InnoDB không so sánh "bản mới nhất có
khác bản trong read view của B không"; nó cứ ghi. Đó là lý do lost update lọt qua RR của MySQL, và
cũng lọt qua RC.

Nếu B viết `UPDATE accounts SET balance = balance + 50 WHERE id = 1;` (phép tính nằm trong SQL) thì
sau khi chờ, B tính trên bản mới nhất 470, ra 520: đúng. Đây là ý tưởng của *atomic update* ở mục 9.

### 6.4 Phantom với locking read: RR dùng gap lock, RC thì không

Mục 3.4 nói về phantom của `SELECT` thường. Với locking read, read view không dính dáng gì (locking
read luôn đọc bản mới nhất), nên muốn chặn phantom thì phải **chặn người khác chèn**. InnoDB ở RR làm
điều đó bằng *next-key lock*: khoá bản ghi index cộng với "khe" (*gap*) trước nó, để không ai chèn
được dòng mới vào khoảng đã quét.

**Ở RR:**

| Bước | Session A (RR) | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` | | |
| 2 | `SELECT id, price FROM products WHERE price >= 100 FOR UPDATE;` | | 1 dòng: id 1 |
| 3 | | `INSERT INTO products VALUES (3, 'Màn hình', 300, 5);` | **B chờ** |
| 4 | `SELECT id, price FROM products WHERE price >= 100 FOR UPDATE;` | | Vẫn 1 dòng: không phantom |
| 5 | `COMMIT;` | | B hết chờ, chèn được id 3 |

Cột `price` không có index, nên câu `FOR UPDATE` ở bước 2 phải quét toàn bộ clustered index và khoá
**mọi** dòng cùng mọi khe. Kết quả là B không chèn được dòng nào, kể cả dòng có `price = 10`. Nếu có
index trên `price` thì InnoDB chỉ khoá vùng index đã quét. (Nếu A giữ khoá quá
`innodb_lock_wait_timeout`, mặc định 50 giây, B nhận lỗi `Lock wait timeout exceeded`.)

**Ở RC:** chạy lại với cả hai session đã `SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;`.
RC không dùng gap lock (trừ khi kiểm tra foreign key và kiểm tra trùng khoá), nên ở bước 3 B chèn được
**ngay**, và bước 4 của A ra **2 dòng**: phantom.

Gap lock, next-key lock, cách đọc khoá trong `performance_schema.data_locks` và deadlock do gap lock
là nội dung [chương 15](15-lock-deadlock.md).

### 6.5 Semi-consistent read ở READ COMMITTED

Ở RC, InnoDB có thêm hai tối ưu cho `UPDATE` và `DELETE` (theo tài liệu MySQL 8.4):

1. Sau khi đánh giá `WHERE`, InnoDB **nhả khoá** của những dòng **không khớp** điều kiện; chỉ giữ khoá
   dòng thực sự bị sửa hoặc xoá. Ở RR thì giữ khoá mọi dòng đã quét tới hết transaction.
2. Với `UPDATE`, nếu dòng đang bị người khác khoá, InnoDB làm *semi-consistent read*: trả về phiên bản
   **mới nhất đã commit** để MySQL kiểm tra `WHERE`. Nếu không khớp thì bỏ qua, không cần chờ. Nếu khớp
   (dòng phải sửa), MySQL đọc lại dòng và lần này InnoDB khoá nó hoặc chờ khoá.

Ví dụ lấy từ tài liệu MySQL (bảng không có index, chạy trong database `ch14`):

```sql
CREATE TABLE t (a INT NOT NULL, b INT) ENGINE = InnoDB;
INSERT INTO t VALUES (1,2),(2,3),(3,2),(4,3),(5,2);
```

| Bước | Session A | Session B | Kết quả ở RR | Kết quả ở RC (cả hai session) |
|---|---|---|---|---|
| 1 | `START TRANSACTION;` | | | |
| 2 | `UPDATE t SET b = 5 WHERE b = 3;` | | A khoá **cả 5 dòng** đã quét, sửa (2,3), (4,3) | A khoá 5 dòng, rồi nhả 3 dòng không khớp; giữ (2,·), (4,·) |
| 3 | | `UPDATE t SET b = 4 WHERE b = 2;` | **B chờ** ngay ở dòng (1,2) | B **không chờ**: sửa (1,2), (3,2), (5,2); dòng (2,3), (4,3) đang bị khoá thì đọc bản đã commit, thấy `b = 3` không khớp, bỏ qua |
| 4 | `COMMIT;` | | B hết chờ, chạy tiếp | |

Kết quả cuối cùng như nhau: `b` của dòng 1, 3, 5 là 4; của dòng 2, 4 là 5. Khác nhau ở chỗ RC ít
chờ hơn, nên ít deadlock hơn. Đây là một trong những lý do nhiều hệ thống MySQL lớn chủ động chuyển
sang RC (mục 8).

### 6.6 Bảng tổng hợp anomaly theo level của InnoDB

| Anomaly | RU | RC | RR (mặc định) | Serializable |
|---|---|---|---|---|
| Dirty read | Lọt | Chặn | Chặn | Chặn |
| Non-repeatable read, read skew | Lọt | Lọt | Chặn nếu chỉ dùng `SELECT` thường; lọt khi trộn câu có khoá (6.1, 6.2) | Chặn |
| Phantom, `SELECT` thường | Lọt | Lọt | Chặn; lọt khi trộn câu ghi (6.2) | Chặn |
| Phantom, locking read | Lọt | Lọt | Chặn (gap lock) | Chặn |
| Lost update (read-modify-write) | Lọt | Lọt | **Lọt** | Chặn (deadlock 1213) |
| Write skew | Lọt | Lọt | Lọt | Chặn (deadlock 1213) |

## 7. PostgreSQL REPEATABLE READ và SERIALIZABLE

### 7.1 PostgreSQL RR: snapshot isolation thật, và lỗi 40001

RR của PostgreSQL là *snapshot isolation*: **mọi** câu trong transaction, cả đọc lẫn ghi, dùng cùng một
snapshot. Khi một câu `UPDATE`, `DELETE` hay `SELECT ... FOR UPDATE` gặp một dòng đã bị transaction
khác sửa và commit **sau** khi snapshot được chụp, PostgreSQL không ghi đè mà huỷ transaction với lỗi
*serialization failure*, SQLSTATE `40001`.

Timeline lost update của mục 3.6, chạy trên PostgreSQL (bảng `accounts` cùng dữ liệu; khi tạo bảng
trên PostgreSQL, bỏ `ENGINE = InnoDB`, và với bảng `doctors` thì tạo index bằng câu `CREATE INDEX`
riêng thay cho dòng `KEY idx_shift (shift_id)`):

| Bước | Session A (PG) | Session B (PG) | Kết quả |
|---|---|---|---|
| 1 | `BEGIN ISOLATION LEVEL REPEATABLE READ;` | | |
| 2 | `SELECT balance FROM accounts WHERE id = 1;` | | 500.00 |
| 3 | | `BEGIN ISOLATION LEVEL REPEATABLE READ;` | |
| 4 | | `SELECT balance FROM accounts WHERE id = 1;` | 500.00 |
| 5 | `UPDATE accounts SET balance = 470 WHERE id = 1;` | | A khoá dòng 1 |
| 6 | | `UPDATE accounts SET balance = 550 WHERE id = 1;` | B chờ khoá của A |
| 7 | `COMMIT;` | | B nhận `ERROR: could not serialize access due to concurrent update` |
| 8 | | `ROLLBACK;` rồi chạy lại cả transaction | Lần chạy lại có snapshot mới, đọc 470, ghi 520: đúng |

So với MySQL RR: cùng các câu lệnh, MySQL lặng lẽ ghi 550; PostgreSQL từ chối và bắt app thử lại. Nếu
A ở bước 7 `ROLLBACK` thay vì `COMMIT`, B được ghi bình thường vì không có xung đột thật.

Những điều cần nhớ về PostgreSQL RR:

- Lỗi 40001 là **cơ chế hoạt động bình thường**, không phải sự cố. App dùng RR hoặc Serializable trên
  PostgreSQL bắt buộc phải bắt 40001 và chạy lại **cả transaction từ đầu** (kể cả các câu đọc, để có
  snapshot mới).
- Không có hiện tượng "SELECT thấy, UPDATE không thấy" như mục 6.2. Phantom cũng không xảy ra.
- Kể cả `UPDATE accounts SET balance = balance + 50 WHERE id = 1` (atomic update) cũng nhận 40001 nếu
  dòng đã bị sửa sau snapshot. Ở PostgreSQL RC thì không lỗi: sau khi chờ, PostgreSQL đánh giá lại
  `WHERE` trên phiên bản mới của dòng rồi ghi.
- Write skew **vẫn lọt**: chạy timeline mục 3.7 trên PostgreSQL RR, hai câu `UPDATE` sửa hai dòng
  khác nhau, không có xung đột trên cùng dòng, cả hai commit thành công.

### 7.2 PostgreSQL SERIALIZABLE: SSI

Từ PostgreSQL 9.1, `SERIALIZABLE` được hiện thực bằng *SSI* (Serializable Snapshot Isolation). Ý tưởng:

1. Chạy y như RR, **không thêm khoá chặn nào**: người đọc vẫn không chờ ai.
2. Ghi nhận mỗi transaction đã đọc những gì, bằng *predicate lock* (trong `pg_locks` có mode
   `SIReadLock`). Tên có chữ "lock" nhưng nó **không chặn ai**, chỉ để đánh dấu.
3. Khi phát hiện một mẫu phụ thuộc đọc-ghi giữa các transaction đồng thời có thể dẫn tới kết quả không
   tuần tự hoá được, PostgreSQL huỷ một transaction với lỗi 40001.

Timeline write skew (mục 3.7) trên PostgreSQL Serializable:

| Bước | Session A (Alice) | Session B (Bob) | Kết quả |
|---|---|---|---|
| 1 | `BEGIN ISOLATION LEVEL SERIALIZABLE;` | `BEGIN ISOLATION LEVEL SERIALIZABLE;` | |
| 2 | `SELECT COUNT(*) FROM doctors WHERE shift_id = 1 AND on_call;` | | 2 |
| 3 | | `SELECT COUNT(*) FROM doctors WHERE shift_id = 1 AND on_call;` | 2 |
| 4 | `UPDATE doctors SET on_call = FALSE WHERE id = 1;` | | Không chờ |
| 5 | | `UPDATE doctors SET on_call = FALSE WHERE id = 2;` | Không chờ |
| 6 | `COMMIT;` | | Thành công |
| 7 | | `COMMIT;` | `ERROR: could not serialize access due to read/write dependencies among transactions` |

B chạy lại sẽ đếm được 1 và từ chối cho nghỉ. Ràng buộc được giữ mà không cần viết logic khoá riêng
cho bài toán này. Cái giá: SSI có thể huỷ nhầm (*false positive*) cả những transaction thực ra không
gây anomaly, nên mọi transaction phải có retry. Tài liệu PostgreSQL khuyên thêm: khai báo `READ ONLY`
khi có thể, giữ transaction ngắn, tránh để connection ở trạng thái "idle in transaction".

### 7.3 MySQL SERIALIZABLE: biến SELECT thành locking read

InnoDB làm `SERIALIZABLE` theo hướng ngược lại: không phát hiện mà **ngăn bằng khoá**. Theo tài liệu
MySQL 8.4: level này giống `REPEATABLE READ`, nhưng khi **autocommit tắt** (ví dụ đang trong
`START TRANSACTION`), InnoDB ngầm đổi mọi `SELECT` thường thành `SELECT ... FOR SHARE` (cú pháp cũ:
`LOCK IN SHARE MODE`). Khi autocommit bật, một câu `SELECT` lẻ là một transaction chỉ đọc, chạy bằng
consistent read và không chặn ai.

Timeline lost update (mục 3.6), cả hai session ở MySQL Serializable:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 0 | `SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;` | `SET SESSION TRANSACTION ISOLATION LEVEL SERIALIZABLE;` | |
| 1 | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 1;` | | 500.00, A giữ khoá S (shared) dòng 1 |
| 2 | | `START TRANSACTION;` `SELECT balance FROM accounts WHERE id = 1;` | 500.00, B cũng giữ khoá S (S với S không xung đột) |
| 3 | `UPDATE accounts SET balance = 470 WHERE id = 1;` | | A cần khoá X, **chờ** khoá S của B |
| 4 | | `UPDATE accounts SET balance = 550 WHERE id = 1;` | B cần khoá X, chờ khoá S của A: vòng chờ, **deadlock** |
| 5 | | | InnoDB rollback một bên, bên đó nhận `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction`; bên còn lại chạy tiếp |

Bên nào bị rollback? Tài liệu MySQL chỉ nói InnoDB cố chọn transaction "nhỏ" (ít dòng đã chèn,
sửa, xoá) để rollback; ở đây hai bên ngang nhau nên đừng dựa vào việc bên nào thua. Lỗi deadlock
rollback **cả transaction** của bên thua, không chỉ câu lệnh vừa chạy.

Không còn lost update: bên bị rollback phải chạy lại và sẽ đọc giá trị mới. Write skew (mục 3.7) cũng
bị chặn theo cùng cách: hai câu đếm giữ khoá S trên dòng 1 và 2, mỗi bên muốn ghi một dòng thì chờ
khoá S của bên kia, ra deadlock. Và phantom bị chặn vì `SELECT` giờ là locking read có next-key lock
(mục 6.4).

Cái giá: đọc giờ **chặn** ghi, nhiều chờ khoá và deadlock hơn, nên `SERIALIZABLE` hiếm khi được dùng
làm mặc định trên MySQL. Để ý mã SQLSTATE: deadlock của MySQL mang `40001`, cùng mã với serialization
failure của PostgreSQL, nên một vòng retry bắt `40001` dùng được cho cả hai.

### 7.4 Bảng so sánh MySQL và PostgreSQL

| Anomaly | MySQL RC | MySQL RR (mặc định) | MySQL Serializable | PG RC (mặc định) | PG RR | PG Serializable |
|---|---|---|---|---|---|---|
| Dirty read | Chặn | Chặn | Chặn | Chặn | Chặn | Chặn |
| Non-repeatable read, read skew | Lọt | Chặn với `SELECT` thường (6.2) | Chặn | Lọt | Chặn | Chặn |
| Phantom | Lọt | Chặn với `SELECT` thường (6.2) | Chặn | Lọt | Chặn | Chặn |
| Lost update | Lọt | **Lọt** | Chặn (deadlock 1213) | Lọt | Chặn (lỗi 40001) | Chặn (lỗi 40001) |
| Write skew | Lọt | Lọt | Chặn (deadlock 1213) | Lọt | **Lọt** | Chặn (lỗi 40001) |
| Cách chặn | | Read view, gap lock | Khoá S cho mọi `SELECT` | | Snapshot + huỷ khi xung đột ghi | SSI: theo dõi phụ thuộc, huỷ |

Bảng này khớp với kết quả của dự án [Hermitage](https://github.com/ept/hermitage) (Martin Kleppmann),
nơi mỗi anomaly là một kịch bản nhiều session gõ tay, chạy trên từng DB và từng level. Hermitage xếp RR
của MySQL vào nhóm yếu hơn snapshot isolation, vì những hành vi ở mục 6.2.

## 8. Chọn isolation level

### 8.1 Nguyên tắc chung

- **Giữ mặc định** trừ khi có lý do cụ thể: MySQL RR, PostgreSQL RC. Nhưng phải biết mặc định đó để
  lọt anomaly nào (bảng mục 7.4), và chống chúng bằng cách viết câu ghi đúng (mục 9).
- **Isolation level không thay được thiết kế câu ghi.** Đổi từ RC lên RR trên MySQL không chống được
  lost update. Đừng "nâng level cho chắc" mà không biết level mới chặn thêm được gì.
- Có thể đặt level **theo từng transaction**: cả hệ thống ở mức mặc định, riêng vài nghiệp vụ đặc
  biệt dùng `SET TRANSACTION ISOLATION LEVEL ...` ngay trước `START TRANSACTION`.

### 8.2 Khi nào cân nhắc từng level trên MySQL

| Level | Khi nào dùng | Lưu ý |
|---|---|---|
| `READ UNCOMMITTED` | Gần như không bao giờ. Có thể cho một truy vấn ước lượng thô trên bảng đang ghi liên tục, chấp nhận số liệu sai | Có dirty read |
| `READ COMMITTED` | Hệ thống ghi nhiều, nhiều tranh chấp khoá, hay deadlock vì gap lock; muốn mỗi câu thấy dữ liệu mới nhất | Không gap lock nên phantom với locking read; binlog chỉ hỗ trợ dạng row-based (nếu `binlog_format = MIXED`, server tự ghi dạng row); transaction đọc nhiều câu cần nhất quán phải tự lo (đọc bằng một câu, hoặc chuyển riêng transaction đó sang RR) |
| `REPEATABLE READ` | Mặc định; báo cáo, đối soát, backup cần nhiều câu đọc nhất quán | Không trộn `SELECT` thường với câu có khoá khi logic phụ thuộc vào nhau (6.2); lost update vẫn lọt |
| `SERIALIZABLE` | Hiếm; một nghiệp vụ nhỏ, ít tranh chấp, cần chắc chắn mà khó viết khoá thủ công | Nhiều chờ khoá và deadlock; bắt buộc retry |

Với báo cáo trên MySQL, kết hợp hay dùng:

```sql
START TRANSACTION READ ONLY, WITH CONSISTENT SNAPSHOT;   -- RR: chụp ngay, không cần transaction id
SELECT SUM(balance) FROM accounts;
SELECT owner, balance FROM accounts ORDER BY balance DESC;
COMMIT;                                                   -- đóng sớm để purge dọn được undo (5.5)
```

### 8.3 Trên PostgreSQL

- RC (mặc định) cho đa số ứng dụng web, cộng với atomic update và `FOR UPDATE` khi cần.
- RR cho báo cáo nhiều câu cần nhất quán, hoặc khi muốn DB tự phát hiện lost update (đổi lại phải
  retry 40001).
- Serializable khi có nhiều ràng buộc kiểu write skew khó khoá thủ công, và team chấp nhận viết retry
  cho mọi transaction. Khác MySQL, đây là lựa chọn thực tế trên PostgreSQL vì SSI không chặn người đọc.

## 9. Chống lost update trong ứng dụng (giới thiệu)

Phần này chỉ giới thiệu để thấy bức tranh; cơ chế khoá, deadlock và cách viết đầy đủ ở
[chương 15](15-lock-deadlock.md).

### 9.1 Atomic update: để DB tính

Đưa phép tính và điều kiện vào **một** câu SQL, thay vì đọc lên app, tính, rồi ghi lại:

```sql
-- Rút 30 từ tài khoản An, chỉ khi đủ tiền
UPDATE accounts SET balance = balance - 30 WHERE id = 1 AND balance >= 30;
-- Query OK, 1 row affected   → rút được
-- Query OK, 0 rows affected  → không đủ tiền (hoặc không có tài khoản)
```

Trên MySQL, ở mọi level, nếu hai câu như vậy chạy cùng lúc thì câu sau chờ khoá, rồi tính trên phiên
bản mới nhất đã commit (vì `UPDATE` là locking read, mục 6.1). Không cần đổi level, không cần khoá thủ
công. Đây là lựa chọn đầu tiên khi logic gói gọn được trong một câu. (Trên PostgreSQL RR/Serializable,
câu sau nhận 40001 và cần retry, mục 7.1.)

### 9.2 SELECT ... FOR UPDATE: khoá trước khi đọc

Khi logic phức tạp phải tính ở app (kiểm tra hạn mức, đọc nhiều bảng), đổi câu đọc thành locking read:

```sql
START TRANSACTION;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;    -- đọc bản mới nhất VÀ khoá dòng
-- ... app tính toán dựa trên balance ...
UPDATE accounts SET balance = 470 WHERE id = 1;
COMMIT;
```

Session thứ hai chạy cùng đoạn này sẽ **chờ ngay ở câu `SELECT ... FOR UPDATE`**, nên khi nó đọc
được thì A đã commit và nó thấy giá trị mới. Vấn đề của mục 6.2 cũng biến mất vì câu đọc và câu ghi
cùng nhìn bản mới nhất. Cách này gọi là *pessimistic lock* (khoá bi quan).

⚠️ Đừng dùng `FOR SHARE` cho mẫu "đọc rồi ghi": hai bên cùng giữ khoá S, cùng xin nâng lên X, ra
deadlock (chính là timeline mục 7.3).

### 9.3 Optimistic lock: không khoá, kiểm tra lúc ghi

Thêm cột phiên bản; khi ghi, chỉ ghi nếu phiên bản chưa đổi kể từ lúc đọc:

```sql
ALTER TABLE accounts ADD COLUMN version INT NOT NULL DEFAULT 0;

SELECT balance, version FROM accounts WHERE id = 1;     -- giả sử: 500.00, version 0
-- app tính 500 - 30 = 470
UPDATE accounts SET balance = 470, version = version + 1
 WHERE id = 1 AND version = 0;
-- 1 row affected: thành công
-- 0 rows affected: có người đã ghi trước, đọc lại và thử lại (hoặc báo người dùng)
```

Không ai phải chờ ai trong lúc app tính toán, hợp với tương tác dài (người dùng mở form sửa trong vài
phút). Cái giá: app phải xử lý trường hợp 0 dòng.

### 9.4 Write skew cần gì hơn

Ba cách trên đều dựa vào xung đột trên **cùng một dòng**. Write skew ghi hai dòng khác nhau nên cần
thêm: khoá cả tập đã đọc bằng `FOR UPDATE` (ở timeline mục 3.7, đổi câu đếm thành
`SELECT id FROM doctors WHERE shift_id = 1 AND on_call = TRUE FOR UPDATE;`), đưa ràng buộc xuống DB
(`UNIQUE`, hoặc một dòng đại diện mà mọi transaction liên quan phải cùng cập nhật), hoặc dùng
`SERIALIZABLE` kèm retry. Chương 15 phân tích từng cách, kể cả trường hợp khó: điều kiện là "chưa có
dòng nào" thì không có dòng để khoá.

### 9.5 Retry

Dù chọn cách nào, app nên có retry cho lỗi `40001` (deadlock 1213 của MySQL, serialization failure
của PostgreSQL). Retry phải chạy lại **cả transaction từ câu đầu tiên**, và phần code được retry không
nên có tác dụng ra ngoài DB (gửi email, gọi API), như chương 13 mục 10 đã cảnh báo. Đối chiếu với
framework: `DB::transaction($callback, $attempts)` của Laravel nhận số lần thử, mặc định 1 (tức không
retry); Spring của Java dịch deadlock và serialization failure thành các lớp con của
`ConcurrencyFailureException` để code bắt và thử lại.

## 10. Đối chiếu MySQL và PostgreSQL

| Chủ đề | MySQL 8.4 (InnoDB) | PostgreSQL |
|---|---|---|
| Level mặc định | `REPEATABLE READ` | `READ COMMITTED` |
| `READ UNCOMMITTED` | Có dirty read | Chạy như RC |
| Xem level | `SELECT @@transaction_isolation;` | `SHOW transaction_isolation;` |
| Lưu phiên bản cũ | Undo log, sửa tại chỗ | Tuple mới trong bảng, `VACUUM` dọn |
| Snapshot RR chụp lúc | Câu consistent read đầu tiên | Câu lệnh đầu tiên của transaction |
| RR với câu ghi | Câu ghi đọc bản mới nhất, ghi đè lặng lẽ | Lỗi 40001 nếu dòng bị sửa sau snapshot |
| Phantom ở RR | Chặn với `SELECT` thường và locking read (gap lock); lọt khi trộn (6.2) | Chặn |
| Serializable | Đổi `SELECT` thành `FOR SHARE`, chặn bằng khoá, deadlock 1213 | SSI, không chặn đọc, huỷ bằng 40001 |
| Mã lỗi cần retry | 1213 (SQLSTATE 40001) | SQLSTATE 40001 (và 40P01 cho deadlock) |

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Tin rằng bọc transaction ở MySQL RR là chống được lost update | RR chỉ cô lập `SELECT` thường; `UPDATE` sau khi chờ khoá vẫn ghi đè bằng giá trị app tính từ snapshot cũ | Atomic update, `FOR UPDATE`, hoặc optimistic lock |
| Dùng `SET TRANSACTION ISOLATION LEVEL ...` rồi tưởng đã đổi cả session | Không có `SESSION` thì chỉ áp dụng cho một transaction kế tiếp | Dùng `SET SESSION ...`, kiểm tra `@@transaction_isolation` |
| Nghĩ snapshot RR chụp ở `START TRANSACTION` | Chụp ở câu consistent read đầu tiên | Dùng `START TRANSACTION WITH CONSISTENT SNAPSHOT` khi cần |
| Trộn `SELECT` thường và `UPDATE` trong một transaction RR rồi ra quyết định dựa trên `SELECT` | Hai kiểu đọc nhìn hai trạng thái khác nhau (6.2) | Đọc bằng `FOR UPDATE` nếu sắp ghi dựa trên kết quả |
| Dùng `SELECT ... FOR SHARE` rồi `UPDATE` để "khoá cho chắc" | Hai bên cùng giữ S, cùng xin X, deadlock | Dùng `FOR UPDATE` |
| Chạy PostgreSQL ở RR/Serializable mà không bắt lỗi 40001 | 40001 là hành vi bình thường ở các level này | Retry cả transaction |
| Chuyển MySQL sang RC mà vẫn để `binlog_format = STATEMENT` | RC chỉ hỗ trợ binlog dạng row-based | Giữ `ROW` (mặc định) |
| Mở transaction RR để đọc rồi để đó hàng giờ | Read view cũ giữ undo, purge không dọn được | Đóng transaction ngay khi đọc xong |
| Nghĩ `REPEATABLE READ` của MySQL và PostgreSQL giống nhau | Cùng tên, khác đảm bảo (7.4) | Tra bảng anomaly của đúng DB |

## Tóm tắt chương

- Chạy đồng thời có thể sinh anomaly: dirty read, non-repeatable read, phantom, read skew (chuyện của
  đọc); lost update, write skew (chuyện của đọc rồi ghi). Dirty write bị chặn ở mọi level.
- Chuẩn SQL có bốn level định nghĩa qua ba hiện tượng dirty read, non-repeatable read, phantom; định
  nghĩa này thiếu nên cùng tên level ở hai DB có thể khác nhau. MySQL mặc định RR, PostgreSQL mặc định RC.
- MVCC giữ nhiều phiên bản dòng: InnoDB ghi bản cũ vào undo log, nối bằng `DB_ROLL_PTR`; read view
  quyết định câu đọc thấy phiên bản nào. RC tạo read view mỗi câu lệnh; RR tạo ở câu consistent read
  đầu tiên. Đọc không chặn ghi, ghi không chặn đọc.
- InnoDB có consistent read (theo read view, không khoá) và locking read (`FOR UPDATE`, `FOR SHARE`,
  `UPDATE`, `DELETE`: bản mới nhất, có khoá). Trộn hai loại trong RR cho kết quả khó hiểu.
- Ở MySQL RR: lost update và write skew lọt; phantom với locking read bị chặn bằng gap lock. Ở RC: không
  gap lock, có semi-consistent read cho `UPDATE`, ít chờ khoá hơn.
- PostgreSQL RR là snapshot isolation, chặn lost update bằng lỗi 40001 nhưng lọt write skew;
  PostgreSQL Serializable dùng SSI. MySQL Serializable đổi `SELECT` thành `FOR SHARE` khi autocommit tắt.
- Chống lost update bằng atomic update, `SELECT ... FOR UPDATE`, hoặc optimistic lock; luôn có retry
  cho 40001. Chi tiết ở chương 15.

## Câu hỏi tự kiểm tra

1. Phân biệt dirty read, non-repeatable read và phantom bằng ví dụ trên bảng `accounts` hoặc
   `products`. (mục 3.2 đến 3.4)
2. Read skew khác non-repeatable read ở điểm nào? Vì sao một câu `SELECT SUM(...)` duy nhất không bị
   read skew ở RC? (mục 3.5)
3. Vì sao lost update vẫn xảy ra dù cả hai bên đều nằm trong transaction RR và không ai đọc dữ liệu
   chưa commit? (mục 3.6, 6.3)
4. Write skew khác lost update thế nào, và vì sao PostgreSQL RR chặn được cái này mà không chặn được
   cái kia? (mục 3.7, 7.1)
5. Hai cột ẩn nào của InnoDB làm MVCC hoạt động được? Một câu `SELECT` ở RR lấy giá trị cũ từ đâu?
   (mục 5.2, 5.3)
6. Snapshot ở RR được chụp lúc nào? Làm sao để chụp ngay khi mở transaction? (mục 5.4)
7. Trong một transaction RR, vì sao `SELECT` thường và `SELECT ... FOR SHARE` liên tiếp có thể ra hai
   giá trị khác nhau? (mục 6.1)
8. Giải thích vì sao `UPDATE` ở mục 6.2 báo `Rows matched: 2` trong khi `SELECT` ngay trước đó chỉ
   thấy 1 dòng.
9. Semi-consistent read là gì, xảy ra ở level nào, và lợi ích là gì? (mục 6.5)
10. MySQL Serializable và PostgreSQL Serializable cùng chặn write skew, nhưng bằng hai cách khác nhau
    như thế nào? Cách nào chặn người đọc? (mục 7.2, 7.3)
11. Một hệ thống MySQL hay bị deadlock do gap lock, đội định chuyển sang RC. Cần kiểm tra những gì
    trước? (mục 6.4, 8.2)

## Bài tập

1. **Chạy lại toàn bộ timeline mục 3** trên MySQL. Với mỗi anomaly, ghi lại level thấp nhất chặn được
   nó, rồi so với bảng mục 6.6. Chỗ nào kết quả khác bảng, giải thích vì sao (gợi ý: kiểm tra lại
   `@@transaction_isolation` của cả hai session).
2. **Snapshot ở đâu.** Viết một timeline hai session chứng minh rằng ở RR, nếu câu đầu tiên của
   transaction là `UPDATE` một dòng khác chứ không phải `SELECT`, thì read view vẫn chưa được tạo cho
   tới câu `SELECT` đầu tiên. Dự đoán kết quả trước khi chạy.
3. **Hai thế giới.** Dùng bảng `products`, viết một transaction RR mà trong đó `SELECT COUNT(*)` trả về
   một con số, còn `DELETE ... WHERE` cùng điều kiện báo xoá được số dòng khác. Giải thích bằng read
   view.
4. **Sửa lost update.** Viết lại timeline mục 3.6 theo ba cách ở mục 9.1, 9.2, 9.3. Với mỗi cách, chỉ
   ra ở bước nào session B phải chờ hoặc phải thử lại, và số dư cuối cùng.
5. **Write skew trên PostgreSQL** (nếu có PostgreSQL). Chạy timeline mục 3.7 ở RR và ở Serializable.
   Sau đó sửa nó ở RR bằng `FOR UPDATE` và so sánh hành vi với MySQL RR.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html),
  [Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html),
  [Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html),
  [InnoDB Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html),
  [Phantom Rows](https://dev.mysql.com/doc/refman/8.4/en/innodb-next-key-locking.html),
  [SET TRANSACTION Statement](https://dev.mysql.com/doc/refman/8.4/en/set-transaction.html).
- PostgreSQL Documentation:
  [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html),
  [Introduction to MVCC](https://www.postgresql.org/docs/current/mvcc-intro.html).
- Berenson và cộng sự (1995), *A Critique of ANSI SQL Isolation Levels*.
- Martin Kleppmann, *Designing Data-Intensive Applications*, chương 7 (Transactions); và dự án
  [Hermitage](https://github.com/ept/hermitage).
- Ports và Grittner (2012), *Serializable Snapshot Isolation in PostgreSQL*.
- Trong repo: [chương 13](13-transaction-acid.md) (transaction, ACID), [chương 15](15-lock-deadlock.md)
  (lock, deadlock), [chương 16 mục 6](16-ben-trong-innodb.md#6-undo-log-mvcc-và-purge) (undo log,
  purge bên trong InnoDB).
