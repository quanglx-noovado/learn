# Chương 21. Sao lưu và khôi phục

> [← Mục lục](README.md) · [← Chương 20: Thay đổi schema an toàn](20-thay-doi-schema-migration.md) · [Chương 22: Replication và high availability →](22-replication-ha.md)

**Bạn sẽ học được:**

- Vì sao database nào cũng cần backup, và vì sao có replica rồi vẫn phải có backup.
- Hai chỉ số dùng để thiết kế chiến lược backup: RPO và RTO.
- Logical backup: `mysqldump --single-transaction` hoạt động thế nào bên trong, các công cụ dump song
  song (mydumper/myloader, MySQL Shell dump utilities), và chuyện `mysqlpump` đã bị bỏ ở MySQL 8.4.
- Physical backup: Percona XtraBackup (backup, prepare, restore, incremental), MySQL Enterprise Backup,
  snapshot đĩa.
- Binary log là gì, đọc nó bằng `mysqlbinlog`, và khôi phục về một thời điểm (point-in-time recovery,
  PITR) từng bước, theo position và theo GTID.
- Xử lý sự cố kinh điển "`DELETE` quên `WHERE`" từ phút đầu tiên đến khi dữ liệu trở lại.
- Lưu trữ, giữ bản (retention), mã hoá backup, và vì sao phải tập restore định kỳ.
- Đối chiếu PostgreSQL: `pg_dump`, `pg_basebackup`, WAL archiving và PITR.

**Cần biết trước:** [Chương 04](04-ddl-constraint.md) (DDL), [Chương 13](13-transaction-acid.md)
(transaction, durability), [Chương 14](14-isolation-mvcc.md) (MVCC, consistent read),
[Chương 16](16-ben-trong-innodb.md) (redo log, crash recovery, binlog),
[Chương 18](18-user-quyen-bao-mat.md) (tạo user, cấp quyền). Replication sẽ học kỹ ở
[Chương 22](22-replication-ha.md); chương này chỉ cần biết replica là một server chép lại mọi thay đổi
từ server chính.

> Quy ước: mọi lệnh shell trong chương chạy trên Linux/macOS, MySQL 8.4. Output của `mysqlbinlog`,
> `xtrabackup` và các công cụ khác là **output minh hoạ** (tự dựng cho dễ đọc, số position, thời gian,
> UUID là ví dụ). Kết quả SQL được tính tay từ dữ liệu mẫu ở mục 1.5.

## 1. Vì sao cần backup

### 1.1 Những cách dữ liệu bị mất

Ở [chương 13](13-transaction-acid.md) bạn học chữ D trong ACID: transaction đã commit thì không mất
khi server sập. Nhưng durability chỉ bảo vệ trước **một** loại sự cố: mất điện, process chết. Còn rất
nhiều cách khác làm mất dữ liệu:

| Loại sự cố | Ví dụ | Durability có cứu không? |
|---|---|---|
| Hỏng phần cứng | Đĩa chết, cả máy chủ cháy | Không: file dữ liệu mất cùng đĩa |
| Lỗi con người | `DELETE FROM orders;` quên `WHERE`, `DROP TABLE` nhầm database | Không: database "trung thành" thực hiện đúng lệnh |
| Lỗi phần mềm | Bug ứng dụng ghi đè giá sai cho cả nghìn sản phẩm; migration lỗi | Không |
| Tấn công | Ransomware mã hoá ổ đĩa; kẻ tấn công lấy được quyền và xoá dữ liệu | Không |
| Hỏng dữ liệu | Lỗi firmware, bit hỏng âm thầm trong file `.ibd` | Có thể không |
| Mất cả vùng | Sự cố trung tâm dữ liệu, mất cả region cloud | Không |

Điểm chung: trong các sự cố trên, database **vẫn hoạt động đúng thiết kế**. Nó không biết lệnh
`DELETE` kia là nhầm. Thứ duy nhất cứu được là một bản sao dữ liệu **từ trước sự cố**, cộng với nhật ký
thay đổi để đi từ bản sao đó tới gần thời điểm sự cố nhất có thể. Đó chính là backup và binary log.

### 1.2 Replica không phải backup

Câu hỏi phỏng vấn rất hay gặp: "Hệ thống đã có replica rồi, cần backup làm gì?"

Replica (chương 22) là một server khác liên tục chép lại mọi thay đổi từ server chính (source). Nó bảo
vệ tốt trước **hỏng phần cứng**: server chính chết thì chuyển sang replica. Nhưng hãy xem điều gì xảy ra
với một lệnh nhầm:

| Thời điểm | Source | Replica |
|---|---|---|
| 14:32:07.000 | `DELETE FROM orders;` chạy xong, commit | |
| 14:32:07.050 | | Nhận sự kiện từ binlog của source |
| 14:32:07.080 | | Thực hiện đúng lệnh xoá, `orders` rỗng |

Replica sao chép **cả lỗi**. Vài chục mili giây sau, mọi bản sao đều mất dữ liệu như nhau. Cùng lý do,
RAID (nhiều đĩa chép nhau) cũng không phải backup: RAID chép cả lệnh xoá.

Định nghĩa thực dụng: **backup là một bản sao dữ liệu ở một thời điểm trong quá khứ, nằm ở chỗ mà sự
cố hiện tại không với tới được, và đã được chứng minh là restore được.** Replica vi phạm vế đầu (nó luôn
ở "hiện tại"); bản backup để cùng đĩa với database vi phạm vế giữa; bản backup chưa bao giờ thử restore
vi phạm vế cuối.

> **Delayed replica.** MySQL cho phép một replica cố ý chạy chậm, ví dụ
> `CHANGE REPLICATION SOURCE TO SOURCE_DELAY = 3600;` (chậm 3600 giây). Nếu phát hiện lệnh nhầm trong
> vòng một giờ, bạn dừng replica đó lại trước khi nó kịp áp lệnh nhầm và lấy dữ liệu ra. Đây là một
> lớp bảo vệ bổ sung tiện lợi, **không** thay được backup: phát hiện muộn hơn độ trễ thì vô dụng, và nó
> vẫn nằm cùng hệ thống với source (ransomware, xoá nhầm cả cụm vẫn với tới).

### 1.3 RPO và RTO

Trước khi chọn công cụ, phải trả lời hai câu hỏi kinh doanh. Hai câu này có tên riêng, rất hay gặp khi
phỏng vấn:

- **RPO (Recovery Point Objective)**: được phép mất tối đa bao nhiêu dữ liệu, đo bằng **thời gian**.
  RPO = 1 giờ nghĩa là sau sự cố, chấp nhận mất tối đa những thay đổi trong 1 giờ cuối.
- **RTO (Recovery Time Objective)**: được phép ngừng dịch vụ tối đa bao lâu, tính từ lúc sự cố đến lúc
  hệ thống chạy lại.

```
           dữ liệu bị mất (RPO)          hệ thống ngừng (RTO)
   ◄──────────────────────────────►◄───────────────────────────►
───┼───────────────────────────────┼────────────────────────────┼──── thời gian
 bản backup                     sự cố                    chạy lại bình thường
 gần nhất có thể dùng
```

Hai con số này quyết định chiến lược:

| Chiến lược | RPO đạt được | RTO điển hình |
|---|---|---|
| Chỉ `mysqldump` mỗi đêm | Tới 24 giờ | Dài: phải chạy lại toàn bộ câu `INSERT` và dựng lại mọi index |
| Dump mỗi đêm + binlog chép ra ngoài mỗi 5 phút | Khoảng 5 phút | Dài như trên, cộng thời gian áp binlog |
| Physical backup + binlog stream liên tục (mục 6.4) | Gần 0 (vài giây) | Ngắn hơn: copy file là xong phần lớn |
| Thêm replica để failover (chương 22) | Gần 0 cho hỏng phần cứng | Vài giây đến vài phút cho hỏng phần cứng |

Chú ý dòng cuối: replica làm RTO rất nhỏ **cho hỏng phần cứng**, nhưng với lỗi con người thì vẫn phải
quay về backup. Một hệ thống nghiêm túc cần cả hai.

RPO và RTO không phải con số kỹ thuật tự đặt; chúng là thoả thuận với phía kinh doanh. RPO càng nhỏ,
RTO càng ngắn thì càng tốn tiền (nhiều máy, nhiều dung lượng, nhiều công vận hành). Kỹ sư cần trình bày
được "muốn RPO 5 phút thì phải làm gì và tốn bao nhiêu".

### 1.4 Ba thuộc tính phải hỏi về mọi phương pháp backup

1. **Nhất quán (consistent)**: bản backup có phản ánh đúng **một thời điểm** không? Nếu bảng `orders`
   được chép lúc 02:00:00 còn `order_items` được chép lúc 02:10:00, bạn có thể restore ra `order_items`
   trỏ tới đơn hàng không tồn tại.
2. **Nóng hay lạnh (hot/cold)**: có phải dừng server, hay chặn ghi, trong lúc backup không?
3. **Có biết vị trí binlog không**: bản backup có ghi lại "tôi tương ứng với binlog file nào, position
   nào (hoặc GTID set nào)" không? Thiếu thông tin này thì không làm được PITR (mục 7).

### 1.5 Dữ liệu mẫu cho chương

Chương này dùng một database `shop` nhỏ. Tạo trên một MySQL 8.4 **thử nghiệm của riêng bạn** (máy cá
nhân, container), đừng thử các lệnh restore trên server thật.

```sql
CREATE DATABASE shop;
USE shop;

CREATE TABLE orders (
  id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  customer    VARCHAR(50)   NOT NULL,
  total       DECIMAL(10,2) NOT NULL,
  created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE = InnoDB;

INSERT INTO orders (customer, total, created_at) VALUES
  ('An',   120.00, '2026-10-24 09:00:00'),
  ('Binh',  75.50, '2026-10-24 09:30:00'),
  ('Chi',  210.00, '2026-10-24 10:15:00');
```

Câu chuyện xuyên suốt chương (giờ là giờ địa phương của server):

| Giờ | Sự kiện | `orders` sau sự kiện |
|---|---|---|
| 02:00 | Backup đầy đủ hằng đêm (3 dòng trên được tạo hôm trước) | id 1, 2, 3 |
| 11:05 | `INSERT` đơn của Dung, 99.00 | id 1..4 |
| 13:20 | `INSERT` đơn của Em, 45.00 | id 1..5 |
| 14:32:07 | Ai đó chạy `DELETE FROM orders;` (quên `WHERE id = 2`) | rỗng |
| 14:40 | Ứng dụng vẫn chạy, `INSERT` đơn của Giang, 60.00 | id 6 |

Mục tiêu cuối chương (mục 8): đưa `orders` về trạng thái có đủ id 1, 2, 3, 4, 5 **và** 6, tức là
"như thể lệnh `DELETE` chưa từng chạy". Chú ý id 6 chứ không phải id 1: `AUTO_INCREMENT` không lùi lại
sau `DELETE`.

## 2. Bức tranh tổng quát: các loại backup

### 2.1 Logical và physical

| | Logical backup | Physical backup |
|---|---|---|
| Lưu cái gì | Câu lệnh SQL (`CREATE TABLE`, `INSERT`) hoặc file dữ liệu dạng text (CSV/TSV) | Bản sao các file trên đĩa của InnoDB (`.ibd`, redo log, undo...) |
| Công cụ MySQL | `mysqldump`, mydumper, MySQL Shell `util.dump*` | Percona XtraBackup, MySQL Enterprise Backup, snapshot đĩa |
| Tốc độ backup | Chậm hơn: phải đọc từng dòng qua SQL | Nhanh: copy file |
| Tốc độ restore | Chậm: chạy lại từng `INSERT`, dựng lại mọi index | Nhanh: copy file về, khởi động |
| Kích thước | Thường nhỏ hơn (không chứa index, chỗ trống trong page) | Bằng kích thước file dữ liệu |
| Khôi phục một bảng | Dễ: lấy đoạn SQL của bảng đó | Khó hơn |
| Chuyển sang version/hệ điều hành khác | Dễ: SQL là SQL | Phải cùng hoặc tương thích version |
| Phát hiện hỏng page | Có (đọc từng dòng sẽ gặp lỗi) | Có thể chép nguyên page hỏng |

Quy tắc ngón tay: database nhỏ (vài GB, dump và restore trong vài phút) thì logical là đủ và đơn giản.
Database lớn (hàng trăm GB trở lên) thì physical là bắt buộc nếu muốn RTO chấp nhận được, và vẫn nên giữ
thêm logical backup định kỳ để có thể lấy lẻ một bảng.

### 2.2 Full, incremental, differential

- **Full**: chép toàn bộ.
- **Incremental**: chỉ chép phần thay đổi so với **lần backup gần nhất** (full hoặc incremental).
  Restore = full + lần lượt từng incremental theo thứ tự.
- **Differential**: chép phần thay đổi so với **lần full gần nhất**. Restore = full + differential mới
  nhất.

Với MySQL, binlog thực chất là một dạng incremental liên tục ở mức transaction. Vì vậy chiến lược phổ
biến là "full định kỳ + binlog", có thể thêm incremental của XtraBackup để rút ngắn đoạn binlog phải áp.

## 3. mysqldump

### 3.1 Lệnh cơ bản

`mysqldump` kết nối vào server như một client bình thường, đọc cấu trúc và dữ liệu, rồi in ra một file
SQL. Restore bằng cách cho client `mysql` chạy file đó.

```bash
mysqldump --user=backup --password \
  --single-transaction \
  --source-data=2 \
  --routines --events \
  --databases shop > shop-2026-10-25.sql
```

Phần đầu file kết quả (output minh hoạ, đã rút gọn):

```sql
-- MySQL dump 10.13  Distrib 8.4.x, for Linux (x86_64)
--
-- Position to start replication or point-in-time recovery from
--
-- CHANGE REPLICATION SOURCE TO SOURCE_LOG_FILE='binlog.000042', SOURCE_LOG_POS=157;

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `shop` ...;
USE `shop`;
DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` ( ... ) ENGINE=InnoDB ...;
LOCK TABLES `orders` WRITE;
INSERT INTO `orders` VALUES (1,'An',120.00,'2026-10-24 09:00:00'),(2,'Binh',75.50,...),(3,'Chi',210.00,...);
UNLOCK TABLES;
```

Giải thích từng tuỳ chọn (theo MySQL 8.4 Reference Manual, trang mysqldump):

| Tuỳ chọn | Ý nghĩa |
|---|---|
| `--single-transaction` | Đặt isolation `REPEATABLE READ` và gửi `START TRANSACTION` trước khi dump, để có ảnh nhất quán **mà không chặn ứng dụng**. Chỉ nhất quán với bảng transactional như InnoDB. Mục 3.2. |
| `--source-data=2` | Ghi vị trí binlog tương ứng với bản dump dưới dạng câu `CHANGE REPLICATION SOURCE TO` **nằm trong comment** (giá trị `2`). Giá trị `1` thì câu đó không bị comment và sẽ được thực thi khi nạp lại. Cần binlog đang bật và quyền `RELOAD`. `--master-data` là alias cũ đã deprecated. |
| `--routines` | Dump stored procedure và function. Cần quyền `SELECT` toàn cục. |
| `--events` | Dump event của Event Scheduler. |
| `--triggers` | Dump trigger. **Bật sẵn mặc định**; tắt bằng `--skip-triggers`. |
| `--databases shop` | Dump database `shop`, có kèm `CREATE DATABASE` và `USE`. |
| `--all-databases` | Như `--databases` với mọi database. |

Một thay đổi hay bị bỏ qua: ở MySQL 5.7 trở về trước, `--all-databases` tự kéo theo routine và event vì
chúng nằm trong bảng `mysql.proc`, `mysql.event`. Từ MySQL 8.0 (data dictionary) các bảng đó không còn
được dùng, định nghĩa nằm trong data dictionary và **không** được dump, nên manual yêu cầu ghi rõ:

```bash
mysqldump --all-databases --routines --events > all_databases.sql
```

Còn `--opt` (bật sẵn) là gói gồm `--add-drop-table --add-locks --create-options --disable-keys
--extended-insert --lock-tables --quick --set-charset`. Trong đó:

- `--quick`: đọc và ghi ra **từng dòng** thay vì nạp cả bảng vào bộ nhớ. Nhờ có nó, dump bảng lớn không
  làm `mysqldump` hết RAM.
- `--extended-insert`: gộp nhiều dòng vào một câu `INSERT ... VALUES (...),(...)`, restore nhanh hơn
  nhiều so với mỗi dòng một câu.
- `--lock-tables`: khoá bảng khi dump. Nhưng `--single-transaction` và `--lock-tables` loại trừ nhau
  (manual giải thích: `LOCK TABLES` làm commit ngầm transaction đang mở); khi bạn dùng
  `--single-transaction`, khoá bảng không được dùng nữa.

Tuỳ chọn nên thêm khi bảng có cột nhị phân: `--hex-blob` ghi các cột `BINARY`, `VARBINARY`, `BLOB`,
`BIT`... dưới dạng hex (`'abc'` thành `0x616263`), tránh hỏng dữ liệu khi file bị xử lý như text.

### 3.2 Bên trong --single-transaction

Đây là câu hỏi phỏng vấn: "`mysqldump` chạy 30 phút trên bảng đang được ghi liên tục, sao bản dump vẫn
nhất quán?"

Câu trả lời là MVCC ([chương 14](14-isolation-mvcc.md)). Ở `REPEATABLE READ`, consistent read của InnoDB
đọc theo một **snapshot** cố định: bình thường snapshot tạo ra ở lần đọc đầu tiên của transaction, còn
`START TRANSACTION WITH CONSISTENT SNAPSHOT` (câu `mysqldump` dùng) tạo snapshot ngay lúc bắt đầu
transaction. Mọi `SELECT` sau đó của `mysqldump`
trong cùng transaction đều thấy dữ liệu **như ở thời điểm snapshot**, bất kể session khác ghi gì. Phiên
bản cũ của dòng được dựng lại từ undo log.

| Thời gian | Session `mysqldump` | Session ứng dụng |
|---|---|---|
| T1 | `SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;` `START TRANSACTION /*!40100 WITH CONSISTENT SNAPSHOT */;` | |
| T2 | Đọc `customers` (theo snapshot T1) | |
| T3 | | `INSERT INTO orders ...` (id 4), commit |
| T4 | Đọc `orders`: **không** thấy id 4 | |
| T5 | Kết thúc, file dump ứng với đúng thời điểm T1 | |

Ứng dụng không bị chặn vì consistent read không đặt lock lên dòng.

Muốn biết snapshot ứng với binlog position nào (để làm PITR), `mysqldump` cần lấy vị trí đó **cùng lúc**
mở snapshot. Vì vậy khi có `--source-data`, nó lấy global read lock (`FLUSH TABLES WITH READ LOCK`) trong
một khoảnh khắc ngắn ở đầu: khoá, mở transaction, đọc vị trí binlog bằng `SHOW BINARY LOG STATUS`, mở
khoá. Manual ghi: với `--single-transaction`, global read lock chỉ giữ "trong thời gian ngắn ở đầu bản
dump".

**Cạm bẫy của khoảnh khắc ngắn đó.** `FLUSH TABLES WITH READ LOCK` phải chờ mọi câu lệnh đang chạy trên
các bảng xong. Nếu lúc đó có một câu `SELECT` báo cáo chạy 20 phút, `FLUSH TABLES WITH READ LOCK` chờ
20 phút, và trong lúc chờ nó chặn mọi câu ghi mới. Hiện tượng y như metadata lock ở
[chương 20](20-thay-doi-schema-migration.md): một câu chạy lâu cộng một câu xin khoá làm cả ứng dụng
đứng. Hãy chạy backup trên replica, hoặc vào giờ không có truy vấn dài.

**Cạm bẫy thứ hai: DDL trong lúc dump.** Consistent read không được cô lập với DDL. Manual liệt kê: trong
lúc dump bằng `--single-transaction`, không connection nào khác được chạy `ALTER TABLE`,
`CREATE TABLE`, `DROP TABLE`, `RENAME TABLE`, `TRUNCATE TABLE`, nếu không thì `SELECT` của `mysqldump`
có thể lấy sai nội dung hoặc lỗi. Nghĩa là: đừng để cửa sổ migration trùng cửa sổ backup.

**Cạm bẫy thứ ba: bảng không phải InnoDB.** Bảng `MyISAM` hay `MEMORY` không có MVCC; chúng vẫn có
thể thay đổi trong lúc dump và bản dump của chúng không nhất quán.

### 3.3 Quyền cho user backup

Không dùng `root` để backup. Theo manual, `mysqldump` cần ít nhất: `SELECT` trên bảng được dump,
`SHOW VIEW` cho view, `TRIGGER` cho trigger, `LOCK TABLES` nếu **không** dùng `--single-transaction`,
`PROCESS` nếu không dùng `--no-tablespaces`, và `RELOAD` hoặc `FLUSH_TABLES` khi dùng
`--single-transaction` trên server bật GTID. `--source-data` cần `RELOAD`; `--events` cần `EVENT`;
`--routines` cần `SELECT` toàn cục. Câu `SHOW BINARY LOG STATUS` cần thêm `REPLICATION CLIENT`.

```sql
CREATE USER 'backup'@'localhost' IDENTIFIED BY 'mat-khau-dai-va-ngau-nhien';
GRANT SELECT, SHOW VIEW, TRIGGER, EVENT, PROCESS, RELOAD, REPLICATION CLIENT
  ON *.* TO 'backup'@'localhost';
```

Đừng ghi mật khẩu vào dòng lệnh (lộ qua `ps`, lịch sử shell). Dùng option file có quyền `600`, hoặc
`mysql_config_editor set --login-path=backup ...` rồi chạy `mysqldump --login-path=backup ...`.

### 3.4 Nén và kiểm tra lỗi khi dùng pipe

```bash
set -o pipefail
mysqldump --login-path=backup --single-transaction --source-data=2 \
  --routines --events --databases shop | gzip > shop-2026-10-25.sql.gz
```

Vì sao `set -o pipefail`? Mặc định, exit code của một pipeline là exit code của lệnh **cuối** (`gzip`).
Nếu `mysqldump` lỗi giữa chừng (mất kết nối, thiếu quyền), `gzip` vẫn thành công, script cron báo "OK",
và bạn có một file backup cụt mà không hề biết. Đây là nguyên nhân kinh điển của "có backup mà không
restore được". Ngoài exit code, hãy kiểm tra dòng cuối của file: `mysqldump` ghi
`-- Dump completed on ...` khi kết thúc bình thường (khi không tắt comment).

### 3.5 Restore

```bash
# Dump có --databases: file đã chứa CREATE DATABASE và USE
mysql --login-path=admin < shop-2026-10-25.sql
# Hoặc từ file nén
gunzip < shop-2026-10-25.sql.gz | mysql --login-path=admin
```

Sau khi restore, kiểm tra trên server thử nghiệm:

```sql
SELECT id, customer, total FROM shop.orders ORDER BY id;
```

Kết quả (từ dữ liệu mẫu, bản backup 02:00):

| id | customer | total |
|---|---|---|
| 1 | An | 120.00 |
| 2 | Binh | 75.50 |
| 3 | Chi | 210.00 |

Những điều cần biết về restore từ dump:

- **Chậm.** Server phải phân tích và chạy lại mọi câu `INSERT`, cập nhật mọi secondary index, ghi redo
  log, ghi binlog. Restore thường lâu hơn dump nhiều lần. Với database vài trăm GB, có thể mất hàng giờ
  đến cả ngày: đây là lý do RTO của logical backup kém.
- **Ghi binlog.** Restore vào một server có binlog bật thì mọi `INSERT` của restore cũng vào binlog, và
  nếu server đó có replica thì replica cũng nhận. Đôi khi đó là điều bạn muốn, đôi khi không. Khi không
  muốn, có thể tắt binlog cho riêng session restore (`SET sql_log_bin = 0;`; đây là biến session bị hạn chế, cần quyền `SESSION_VARIABLES_ADMIN`, hoặc
  `SYSTEM_VARIABLES_ADMIN`/`SUPER` vốn bao hàm nó; không đặt được giữa một transaction), nhưng
  hiểu rõ hậu quả: replica sẽ lệch với source.
- **Lấy một database từ file `--all-databases`:** client `mysql` có `--one-database`
  (`mysql --one-database shop < all.sql`: chỉ chạy các câu khi database mặc định là `shop`). Manual gọi nó
  là "thô sơ": việc lọc chỉ dựa vào câu `USE`, nội dung câu lệnh không được xét, nên một câu ghi rõ
  `db_khac.bang` mà nằm sau `USE shop` vẫn chạy. Kiểm tra kết quả cẩn thận; dễ hơn là ngay từ đầu dump mỗi
  database ra một file riêng.
- **GTID.** Trên server bật GTID, `mysqldump` mặc định (`--set-gtid-purged=AUTO`) ghi thêm câu
  `SET @@GLOBAL.gtid_purged=...` vào file. Câu này hữu ích khi dựng một replica mới, nhưng có thể gây lỗi
  khi nạp vào server đã có GTID của riêng nó (ví dụ chép một database sang staging). Khi đó dump với
  `--set-gtid-purged=OFF` (không ghi câu đó) hoặc `COMMENTED` (ghi nhưng comment lại).

### 3.6 mysqlpump đã bị bỏ

MySQL 5.7 và 8.0 có thêm công cụ `mysqlpump` (dump song song). Nó bị deprecated từ 8.0.34 và **đã bị gỡ
bỏ ở MySQL 8.4**, cùng hai công cụ phụ `lz4_decompress`, `zlib_decompress`. Manual 8.4 hướng dẫn dùng
`mysqldump` hoặc MySQL Shell dump utilities thay thế. Nếu gặp script cũ gọi `mysqlpump`, nó sẽ không chạy
với gói MySQL 8.4.

### 3.7 Giới hạn của mysqldump

Manual 8.4 nói thẳng: `mysqldump` "không phải giải pháp nhanh hay có khả năng mở rộng để backup lượng dữ
liệu lớn". Nó dump **một luồng**, restore cũng một luồng (một kết nối `mysql` chạy tuần tự). Manual gợi ý
MySQL Shell dump utilities (song song, nén, hiển thị tiến độ) và physical backup cho dữ liệu lớn.

## 4. Dump song song: mydumper/myloader và MySQL Shell

### 4.1 Ý tưởng

Logical backup chậm chủ yếu vì làm tuần tự. Các công cụ mới chia việc cho nhiều thread, mỗi thread có
kết nối riêng, cùng dump từng phần (từng bảng, từng khúc khoảng khoá chính của bảng lớn). Để vẫn nhất
quán, chúng phải làm sao cho **mọi thread cùng nhìn một snapshot**: khoá toàn cục trong khoảnh khắc ngắn,
cho từng thread mở transaction `WITH CONSISTENT SNAPSHOT`, rồi nhả khoá.

Output không còn là một file SQL mà là **một thư mục** nhiều file: file DDL cho từng bảng, file dữ liệu
cho từng khúc, file metadata. Restore cũng song song: nhiều thread nạp nhiều file cùng lúc.

### 4.2 mydumper và myloader

mydumper/myloader là công cụ mã nguồn mở bên thứ ba (không thuộc gói MySQL), cài riêng.

```bash
# Dump database shop, 4 thread, nén, chia bảng thành khúc 100000 dòng
mydumper --host=127.0.0.1 --user=backup --ask-password \
  --database=shop --outputdir=/backup/shop-2026-10-25 \
  --threads=4 --rows=100000 --compress

# Restore song song
myloader --host=127.0.0.1 --user=admin --ask-password \
  --directory=/backup/shop-2026-10-25 --threads=4
```

Theo tài liệu mydumper: `--threads` mặc định 4 (`0` nghĩa là bằng số CPU), `--rows` chia bảng thành khúc
theo số dòng, `--regex` lọc theo mẫu `db.table`. Với myloader, `--database` cho phép nạp vào database có
tên khác, `--drop-table` quyết định làm gì khi bảng đã tồn tại (mặc định `FAIL`, tức báo lỗi). Thư mục
dump có file metadata ghi vị trí binlog/GTID lúc bắt đầu snapshot, dùng cho PITR.

### 4.3 MySQL Shell dump utilities

MySQL Shell (`mysqlsh`) là client chính thức thế hệ mới của Oracle, có sẵn các hàm dump/load trong
module `util` (gõ ở chế độ JavaScript của shell):

```js
// Dump toàn bộ instance, chỉ một số schema, hoặc một số bảng
util.dumpInstance("/backup/inst-2026-10-25")
util.dumpSchemas(["shop"], "/backup/shop-2026-10-25", {threads: 8})
util.dumpTables("shop", ["orders"], "/backup/orders-2026-10-25")

// Nạp lại
util.loadDump("/backup/shop-2026-10-25", {threads: 8})
```

Những mặc định đáng nhớ (theo tài liệu MySQL Shell):

- `threads` mặc định **4**, mỗi thread một kết nối.
- `compression` mặc định **`zstd`** (mức 1). Dữ liệu được chia khúc, lưu dạng `.tsv.zst`.
- `consistent` mặc định **`true`**: đặt `FLUSH TABLES WITH READ LOCK` (nếu user có `RELOAD`) hoặc
  `LOCK TABLES`, cho mọi thread mở transaction `REPEATABLE READ` `WITH CONSISTENT SNAPSHOT`, sau đó khoá
  instance bằng `LOCK INSTANCE FOR BACKUP` (chặn DDL, không chặn DML; cần quyền `BACKUP_ADMIN`) và nhả
  global read lock. Như vậy, so với `mysqldump`, nó còn tự bảo vệ trước DDL trong lúc dump. Nếu user không
  có `BACKUP_ADMIN`, công cụ làm thêm một bước kiểm tra nhất quán thay cho khoá đó.
- Thư mục đích phải rỗng hoặc chưa tồn tại.
- Chỉ đảm bảo nhất quán với bảng InnoDB.
- `dryRun: true` để xem sẽ dump gì mà không dump thật.

Với `util.loadDump`:

- Dùng `LOAD DATA LOCAL INFILE`, nên server đích phải bật `local_infile = ON` trong lúc nạp.
- `threads` mặc định 4.
- `deferTableIndexes` mặc định `fulltext`: hoãn tạo full-text index tới sau khi nạp dữ liệu; đặt `all`
  để hoãn mọi secondary index (thường nhanh hơn: dựng index một lần sau cùng rẻ hơn cập nhật từng dòng).
- Tiến độ được ghi vào một file trạng thái (`load-progress...json`, tên kèm UUID của server đích) trong
  thư mục dump; bị ngắt giữa chừng thì
  chạy lại lệnh, nó **tiếp tục** từ chỗ dừng.
- `loadUsers` mặc định `false`: **không** nạp user. Muốn nạp tài khoản phải bật `loadUsers: true`.
- `skipBinlog: true` để không ghi binlog cho các session nạp (mặc định `false`).

## 5. Physical backup

### 5.1 Vấn đề của việc copy file khi server đang chạy

Cách "physical" thô sơ nhất là dừng MySQL rồi `cp -a /var/lib/mysql /backup/` (cold backup). Nhất quán
tuyệt đối, nhưng phải dừng server: không chấp nhận được với hệ thống chạy 24/7.

Copy khi server đang chạy thì sao? Copy một file `.ibd` 50 GB mất vài phút. Trong lúc đó InnoDB vẫn ghi
page vào file. Kết quả: page đầu file là bản lúc 02:00, page cuối file là bản lúc 02:05, có page bị chép
giữa lúc đang ghi dở. Đó là một mớ không nhất quán.

Ý tưởng của hot physical backup giải quyết bằng chính cơ chế crash recovery bạn học ở
[chương 16](16-ben-trong-innodb.md):

1. Bắt đầu theo dõi **redo log** từ một vị trí (LSN) trước khi copy.
2. Copy các file dữ liệu (chấp nhận chúng không nhất quán).
3. Trong suốt lúc copy, chép thêm mọi bản ghi redo log mới phát sinh.
4. Khi restore, **áp redo log** lên các file đã copy, y như InnoDB làm khi khởi động lại sau crash. Kết
   quả: dữ liệu nhất quán tại thời điểm cuối của quá trình copy.

Bước 4 được gọi là **prepare**.

### 5.2 Percona XtraBackup 8.4

XtraBackup là công cụ mã nguồn mở của Percona. Bản 8.4 theo tài liệu chỉ hỗ trợ MySQL 8.4 và Percona
Server for MySQL 8.4; không hỗ trợ server 8.0 hay 9.x. Nói chung, hãy dùng dòng XtraBackup khớp với dòng
MySQL bạn chạy.

**Bước 1: backup.**

```bash
xtrabackup --backup --target-dir=/data/backups/full-2026-10-25 \
  --user=backup --password=...
```

- Thư mục đích chưa tồn tại thì được tạo; nếu đã có file, xtrabackup báo lỗi (`file exists`), không ghi
  đè.
- Thành công khi dòng cuối là `completed OK!` và exit code `0`. Script tự động phải kiểm tra cả hai.
- Thư mục đích chứa bản sao file dữ liệu và các file metadata như `xtrabackup_checkpoints`,
  `xtrabackup_info`, `xtrabackup_logfile`, `xtrabackup_binlog_info`. File cuối ghi vị trí binlog (và
  GTID) ứng với bản backup, ví dụ (minh hoạ):

```
binlog.000042	157	3e11fa47-71ca-11e1-9e33-c80aa9429562:1-1234
```

- Bảng InnoDB được copy nóng; theo tài liệu, khi copy dữ liệu **không phải** InnoDB thì có khoá. Database
  toàn InnoDB thì gần như không ảnh hưởng ứng dụng, chỉ tốn I/O.

**Bước 2: prepare.**

```bash
xtrabackup --prepare --target-dir=/data/backups/full-2026-10-25
```

Đây là bước áp redo log như mục 5.1. Tài liệu Percona ghi: file dữ liệu chưa nhất quán cho tới khi được
prepare; transaction chưa commit tại thời điểm cuối sẽ bị rollback. Nếu thiếu bước này InnoDB sẽ phát hiện
dữ liệu không nhất quán và từ chối khởi động. Thành công khi thấy `completed OK!`. Có thể prepare ngay sau
khi backup (để biết sớm bản backup dùng được) hoặc lúc restore.

**Bước 3: restore.**

```bash
sudo systemctl stop mysqld                 # server phải dừng
# datadir phải rỗng: chuyển datadir cũ sang chỗ khác, KHÔNG xoá vội
sudo mv /var/lib/mysql /var/lib/mysql.broken
sudo mkdir /var/lib/mysql
sudo xtrabackup --copy-back --target-dir=/data/backups/full-2026-10-25
sudo chown -R mysql:mysql /var/lib/mysql
sudo systemctl start mysqld
```

`--copy-back` sao chép (giữ lại thư mục backup); `--move-back` di chuyển (thư mục backup bị làm rỗng,
nhanh hơn nhưng mất bản backup). Có thể dùng `rsync` thay thế. Quên `chown` là lỗi rất hay gặp: file
thuộc `root`, MySQL không đọc được, không khởi động.

Vì sao **đổi tên** datadir cũ thay vì xoá? Vì nếu bản backup hoá ra hỏng, datadir cũ là thứ duy nhất còn
lại. Nguyên tắc chung của mọi thao tác khôi phục: không phá huỷ gì cho tới khi chắc chắn bản mới tốt.

### 5.3 Incremental với XtraBackup

XtraBackup ghi lại LSN của mỗi bản backup (file `xtrabackup_checkpoints`). Bản incremental chỉ chép những
page có LSN mới hơn LSN của bản trước.

```bash
# Chủ nhật: full
xtrabackup --backup --target-dir=/data/backups/base
# Thứ hai: incremental so với base
xtrabackup --backup --target-dir=/data/backups/inc1 --incremental-basedir=/data/backups/base
# Thứ ba: incremental so với inc1
xtrabackup --backup --target-dir=/data/backups/inc2 --incremental-basedir=/data/backups/inc1
```

Prepare phải theo đúng thứ tự, và đây là chỗ dễ sai nhất:

```bash
xtrabackup --prepare --apply-log-only --target-dir=/data/backups/base
xtrabackup --prepare --apply-log-only --target-dir=/data/backups/base \
  --incremental-dir=/data/backups/inc1
# Bản cuối cùng: KHÔNG có --apply-log-only
xtrabackup --prepare --target-dir=/data/backups/base \
  --incremental-dir=/data/backups/inc2
```

`--apply-log-only` nghĩa là "chỉ áp redo, **chưa** rollback transaction dở dang", vì transaction dở dang
ở bản trước có thể được hoàn tất ở bản incremental sau. Tài liệu cảnh báo: nếu không dùng
`--apply-log-only` ở các bước giữa để ngăn pha rollback, các bản incremental sau trở nên vô dụng. Kết quả
cuối nằm trong `base`. Không prepare cùng một `--incremental-dir` hai lần.

### 5.4 Nén và mã hoá trong XtraBackup

```bash
xtrabackup --backup --compress --compress-threads=4 \
  --encrypt=AES256 --encrypt-key-file=/etc/mysql/backup.key \
  --target-dir=/data/backups/full-2026-10-25
```

- `--compress` mặc định dùng thuật toán **ZSTD** (mức 1); `--compress=lz4` để dùng lz4.
- `--encrypt=AES256` mã hoá; khoá truyền bằng `--encrypt-key` hoặc `--encrypt-key-file` (loại trừ nhau).
  Tạo file khoá bằng `echo -n` để không dính ký tự xuống dòng (khoá sai kích thước sẽ không dùng được).
- Restore phải giải mã (`--decrypt`) và giải nén (`--decompress`) trước khi prepare. File mã hoá gốc
  không tự bị xoá.
- Truyền khoá qua `--encrypt-key` trên dòng lệnh làm khoá lộ qua `ps` và lịch sử shell; ưu tiên file khoá
  với quyền `600`.

### 5.5 MySQL Enterprise Backup

MySQL Enterprise Backup (lệnh `mysqlbackup`) là công cụ physical backup **thương mại** của Oracle, đi kèm
MySQL Enterprise Edition. Cùng nguyên lý với XtraBackup: hot backup InnoDB, incremental, nén, mã hoá, và
lưu vị trí binlog trong bản backup để làm PITR. Bạn chỉ gặp nó ở công ty mua bản Enterprise; khi phỏng
vấn chỉ cần biết nó tồn tại và tương đương XtraBackup về ý tưởng.

### 5.6 Snapshot đĩa

Trên cloud (EBS snapshot của AWS, persistent disk snapshot của GCP) hoặc với LVM/ZFS, có thể chụp
**snapshot** cả ổ đĩa gần như tức thời.

- Nếu **toàn bộ** datadir (file dữ liệu, redo log, undo, binlog) nằm trên **một** volume và snapshot là
  nguyên tử, snapshot tương đương "rút điện server đúng lúc đó": InnoDB sẽ crash recovery khi khởi động từ
  snapshot. Gọi là *crash-consistent*.
- Nếu dữ liệu trải trên nhiều volume, các snapshot không cùng thời điểm, không còn nhất quán. Cách an toàn
  hơn: giữ `FLUSH TABLES WITH READ LOCK` trong vài giây lúc chụp (để có cả vị trí binlog chắc chắn), chụp,
  rồi `UNLOCK TABLES`; hoặc dùng tính năng snapshot nhóm nhiều volume cùng lúc của nhà cung cấp.
- Snapshot cùng tài khoản cloud, cùng region **không** an toàn trước việc mất tài khoản hay xoá nhầm cả
  tài khoản: phải chép sang tài khoản/region khác.
- Ưu điểm lớn: restore rất nhanh (tạo volume từ snapshot). Nhiều dịch vụ managed (Amazon RDS, Cloud SQL)
  kết hợp snapshot tự động với binlog để cung cấp sẵn PITR.

## 6. Binary log: nhật ký của mọi thay đổi

### 6.1 Binlog là gì, và nó khác redo log thế nào

Ở [chương 16](16-ben-trong-innodb.md) bạn đã gặp hai loại log. Nhắc lại sự khác nhau, vì đây là nền tảng
của PITR:

| | Redo log | Binary log (binlog) |
|---|---|---|
| Thuộc tầng | InnoDB (storage engine) | Server (tầng SQL), mọi engine |
| Ghi gì | Thay đổi vật lý trên page | Thay đổi logic: dòng nào bị insert/update/delete (hoặc câu lệnh) |
| Dùng để | Crash recovery | Replication và point-in-time recovery |
| Vòng đời | Ghi vòng tròn, bị ghi đè khi checkpoint xong | Nhiều file nối tiếp `binlog.000001`, `binlog.000002`..., giữ tới khi hết hạn hoặc bị purge |

Vì binlog được giữ lâu và ghi theo thứ tự commit, nó cho phép "phát lại" mọi transaction từ một vị trí
bất kỳ. Backup cho bạn trạng thái lúc 02:00; binlog cho bạn mọi thứ xảy ra sau 02:00.

Các mặc định quan trọng ở MySQL 8.4 (theo manual, trang Binary Logging Options and Variables):

- Binlog **bật sẵn** (`log_bin = ON`), trừ khi khởi tạo datadir thủ công bằng `--initialize`. Tắt bằng
  `--skip-log-bin`.
- `binlog_format` mặc định `ROW`. Biến này đã deprecated; manual khuyên chỉ dùng row-based cho hệ thống
  mới.
- `binlog_row_image` mặc định `full`: ghi đủ mọi cột của ảnh trước và ảnh sau. Điều này **cực kỳ quan
  trọng** cho xử lý sự cố: một sự kiện `DELETE` ở format ROW chứa toàn bộ nội dung các dòng bị xoá.
- `binlog_expire_logs_seconds` mặc định `2592000` giây = 30 ngày; quá hạn thì file binlog tự bị xoá.
  Biến cũ `expire_logs_days` đã bị gỡ ở 8.4.

Các lệnh xem binlog trên server (8.4 đã gỡ các tên cũ `SHOW MASTER STATUS`, `SHOW MASTER LOGS`,
`PURGE MASTER LOGS`, `RESET MASTER`):

```sql
SHOW BINARY LOGS;            -- danh sách file binlog và kích thước
SHOW BINARY LOG STATUS;      -- file hiện tại, position hiện tại, GTID đã thực thi
FLUSH BINARY LOGS;           -- đóng file hiện tại, mở file mới
```

### 6.2 Cấu trúc của binlog: event, position, GTID

Binlog là chuỗi **event**. Một transaction là một nhóm event. Mỗi event nằm ở một **position**: số byte
tính từ đầu file. Position không phải số thứ tự event.

Nếu bật GTID (`gtid_mode = ON`; mặc định là `OFF`), mỗi transaction còn có một định danh toàn cục
**GTID** dạng `source_uuid:số_thứ_tự`, ví dụ `3e11fa47-71ca-11e1-9e33-c80aa9429562:23` là transaction thứ
23 commit trên server có UUID đó. Một tập GTID viết gọn thành khoảng: `3e11...:1-1234`.

Hai tính chất GTID cần cho PITR:

- Server ghi nhớ mọi GTID đã thực thi trong `gtid_executed`.
- Manual: một transaction có GTID đã được commit trên server thì mọi lần thực thi sau với **cùng GTID**
  bị server **bỏ qua**, không báo lỗi. Tính chất này tiện (phát lại thừa không gây trùng) nhưng cũng là
  bẫy (mục 7.4).

### 6.3 Đọc binlog bằng mysqlbinlog

`mysqlbinlog` chuyển binlog thành text. Output của nó có thể đưa thẳng vào client `mysql` để thực thi lại.

```bash
# Xem, giải mã sự kiện ROW thành giả-SQL dạng comment để đọc
mysqlbinlog --base64-output=DECODE-ROWS --verbose /var/lib/mysql/binlog.000042 | less
```

Một transaction `DELETE` trong output trông thế này (output minh hoạ, rút gọn, server không bật GTID):

```
# at 2310
#261025 14:32:07 server id 1  end_log_pos 2389 CRC32 0x5a1c...   Anonymous_GTID  last_committed=8 sequence_number=9 rbr_only=yes
SET @@SESSION.GTID_NEXT= 'ANONYMOUS'/*!*/;
# at 2389
#261025 14:32:07 server id 1  end_log_pos 2468 CRC32 0x...   Query   thread_id=57  exec_time=0  error_code=0
BEGIN
# at 2468
#261025 14:32:07 server id 1  end_log_pos 2530 CRC32 0x...   Table_map: `shop`.`orders` mapped to number 92
# at 2530
#261025 14:32:07 server id 1  end_log_pos 2760 CRC32 0x...   Delete_rows: table id 92 flags: STMT_END_F
### DELETE FROM `shop`.`orders`
### WHERE
###   @1=1
###   @2='An'
###   @3=120.00
###   @4='2026-10-24 09:00:00'
### DELETE FROM `shop`.`orders`
### WHERE
###   @1=2
###   ...
# at 2760
#261025 14:32:07 server id 1  end_log_pos 2791 CRC32 0x...   Xid = 9123
COMMIT/*!*/;
# at 2791
```

Cách đọc:

- `# at 2310`: event này **bắt đầu** ở position 2310.
- `end_log_pos 2389`: event kết thúc, event tiếp theo bắt đầu ở 2389.
- `#261025 14:32:07`: ngày giờ (yymmdd) của event.
- Transaction gồm: event GTID (ở đây `Anonymous_GTID` vì không bật GTID), `BEGIN`, `Table_map`,
  `Delete_rows`, và `Xid` (commit). Nó **bắt đầu ở 2310** và **kết thúc ở 2791**.
- Ở format ROW, binlog không chứa câu SQL gốc (`DELETE FROM orders`), mà chứa từng dòng bị xoá
  (`@1`, `@2`... là cột thứ 1, 2... theo thứ tự trong bảng). Muốn binlog lưu kèm câu gốc dạng comment,
  bật `binlog_rows_query_log_events` và đọc bằng `-vv`.

Lưu ý `--base64-output=DECODE-ROWS` chỉ dùng để **đọc**. Manual ghi rõ: muốn thực thi lại output thì phải
để mặc định (`AUTO`), vì chỉ khi đó các event ROW được in dưới dạng câu `BINLOG '...'` thực thi được.

Các tuỳ chọn lọc dùng trong PITR (theo manual 8.4):

| Tuỳ chọn | Ý nghĩa chính xác |
|---|---|
| `--start-position=N` | Bắt đầu từ event **bắt đầu tại** N (bao gồm). N phải là vị trí bắt đầu của một event. Áp cho file **đầu tiên** trên dòng lệnh. |
| `--stop-position=N` | Dừng, **loại trừ** event bắt đầu tại N trở đi. Áp cho file **cuối cùng** trên dòng lệnh. |
| `--start-datetime="..."` | Từ event đầu tiên có thời gian **≥** giá trị. |
| `--stop-datetime="..."` | Dừng ở event đầu tiên có thời gian **≥** giá trị (event đó không được in). |
| `--include-gtids=SET` | Chỉ in các transaction có GTID trong tập. |
| `--exclude-gtids=SET` | Bỏ các transaction có GTID trong tập. |
| `--database=db` | Lọc theo database; ý nghĩa khác nhau giữa format STATEMENT và ROW, nên cẩn thận. |

Hai chi tiết về thời gian dễ gây sai:

1. Giá trị datetime được hiểu theo **múi giờ địa phương của máy chạy `mysqlbinlog`**, không phải múi giờ
   của server. Chạy trên laptop ở múi giờ khác là lệch vài giờ.
2. Thời gian của event có độ phân giải giây; trong cùng một giây có thể có nhiều transaction. Manual khuyên
   chỉ dùng `--start-datetime`/`--stop-datetime` để **tìm** vị trí, còn khi áp thật thì dùng
   `--start-position`/`--stop-position`, vì lọc theo thời gian có nguy cơ bỏ sót event cao hơn.

### 6.4 Giữ binlog an toàn

Binlog chỉ hữu ích nếu nó còn và nằm ngoài vùng sự cố:

- **Binlog phải phủ từ bản full cũ nhất bạn muốn dùng.** Giữ full 7 ngày mà binlog chỉ giữ 3 ngày thì từ
  bản full của 5 ngày trước bạn không thể đi tiếp. Hạn 30 ngày mặc định áp cho file trên server; bản chép
  ra ngoài có retention riêng.
- **Chép binlog ra ngoài server.** Đĩa server chết thì binlog chết theo. Cách đơn giản: định kỳ
  `FLUSH BINARY LOGS` rồi chép các file đã đóng lên kho lưu trữ. Khoảng thời gian giữa hai lần chép chính
  là RPO của bạn.
- **Stream binlog liên tục** bằng chính `mysqlbinlog`, từ một máy khác:

```bash
mysqlbinlog --read-from-remote-server --host=db1.internal --user=binlog_reader --password \
  --raw --stop-never binlog.000042
```

`--read-from-remote-server` đọc binlog qua mạng (cần quyền `REPLICATION SLAVE`); `--raw` ghi nguyên dạng
nhị phân, mỗi file nguồn thành một file cùng tên ở thư mục hiện tại; `--stop-never` giữ kết nối và tiếp
tục nhận event mới như một replica. Đây là cách đưa RPO xuống vài giây. Cần một tiến trình giám sát để tự
khởi động lại nó khi mất kết nối.

## 7. Point-in-time recovery từng bước

### 7.1 Ý tưởng

```
 bản full 02:00            binlog
 ┌──────────┐   ──────────────────────────────────────────────►
 │ id 1,2,3 │   INSERT 4 │ INSERT 5 │ DELETE (nhầm) │ INSERT 6
 └──────────┘            ▲          ▲               ▲
          position của bản backup   |  dừng trước    tiếp tục sau
                                      lệnh nhầm      lệnh nhầm
```

PITR = **restore bản full** + **phát lại binlog** từ vị trí của bản full tới ngay trước thời điểm mong
muốn. Tuỳ chọn: bỏ qua sự kiện xấu rồi phát lại tiếp phần sau.

Ba thông tin bạn phải có:

1. Bản full và **vị trí binlog của nó** (comment `CHANGE REPLICATION SOURCE TO` trong file `mysqldump`
   có `--source-data=2`, hoặc file `xtrabackup_binlog_info`).
2. Toàn bộ file binlog từ vị trí đó tới hiện tại.
3. Vị trí (position hoặc GTID) của sự kiện xấu.

### 7.2 Theo position (server không bật GTID)

Quy trình dưới đây theo đúng cấu trúc của manual 8.4 (mục "Point-in-Time Recovery Using Event
Positions"), áp vào câu chuyện mẫu. Giả sử bản dump 02:00 ghi
`SOURCE_LOG_FILE='binlog.000042', SOURCE_LOG_POS=157`, và mọi sự kiện trong ngày đều nằm trong
`binlog.000042`.

**Bước 1: restore bản full** vào server khôi phục (mục 8.2 bàn nên restore vào đâu):

```bash
mysql --login-path=admin < shop-2026-10-25.sql
```

**Bước 2: tìm position của sự kiện xấu.** Dùng thời gian để khoanh vùng, rồi đọc position:

```bash
mysqlbinlog --start-datetime="2026-10-25 14:30:00" --stop-datetime="2026-10-25 14:35:00" \
  --base64-output=DECODE-ROWS --verbose /backup/binlog/binlog.000042 \
  | grep -n -B 12 -A 3 'DELETE FROM `shop`.`orders`' | less
```

Từ output ở mục 6.3: transaction xoá bắt đầu ở `# at 2310` và kết thúc ở `end_log_pos 2791`.

**Bước 3: phát lại từ vị trí backup đến ngay trước sự kiện xấu:**

```bash
mysqlbinlog --start-position=157 --stop-position=2310 /backup/binlog/binlog.000042 \
  | mysql --login-path=admin
```

`--stop-position=2310` loại trừ event bắt đầu tại 2310, tức toàn bộ transaction `DELETE` không chạy.
Kiểm tra:

```sql
SELECT id, customer, total FROM shop.orders ORDER BY id;
```

| id | customer | total |
|---|---|---|
| 1 | An | 120.00 |
| 2 | Binh | 75.50 |
| 3 | Chi | 210.00 |
| 4 | Dung | 99.00 |
| 5 | Em | 45.00 |

Đây là trạng thái lúc 14:32:06.

**Bước 4 (tuỳ chọn): phát lại phần sau sự kiện xấu**, bắt đầu từ position kết thúc của nó:

```bash
mysqlbinlog --start-position=2791 /backup/binlog/binlog.000042 | mysql --login-path=admin
```

Kết quả có thêm dòng `6 | Giang | 60.00`. Trạng thái giờ là "như thể lệnh `DELETE` chưa từng chạy".

**Khi binlog trải trên nhiều file**, đưa tất cả vào **một** lệnh `mysqlbinlog` và **một** kết nối
`mysql`:

```bash
mysqlbinlog --start-position=157 binlog.000042 binlog.000043 binlog.000044 \
  | mysql --login-path=admin
```

Manual cảnh báo cách chạy từng file một với nhiều tiến trình `mysql` riêng (`mysqlbinlog binlog.000042 |
mysql`, rồi `mysqlbinlog binlog.000043 | mysql`) là nguy hiểm: nếu file đầu có `CREATE TEMPORARY TABLE`
còn file sau dùng bảng tạm đó, tiến trình `mysql` đầu kết thúc thì bảng tạm mất, file sau báo
"unknown table". Nhớ thêm: `--start-position` áp cho file đầu, `--stop-position` áp cho file cuối.

Một cách an toàn hơn nữa là ghi ra file trước, **đọc lại**, rồi mới chạy:

```bash
mysqlbinlog --start-position=157 --stop-position=2310 binlog.000042 > /tmp/replay.sql
mysql --login-path=admin -e "source /tmp/replay.sql"
```

### 7.3 Theo GTID

Khi server bật GTID, có thể làm theo position như trên, nhưng GTID cho cách diễn đạt gọn hơn. Giả sử
(minh hoạ) UUID server là `3e11fa47-...-c80aa9429562` (viết tắt `UUID`), bản backup có
`gtid_purged = UUID:1-1200`, và trong binlog transaction xoá có GTID `UUID:1235`.

Tìm GTID của transaction xoá: trong output `mysqlbinlog`, mỗi transaction bắt đầu bằng dòng
`SET @@SESSION.GTID_NEXT= 'UUID:1235'`. Sau đó:

```bash
# Phát lại mọi thứ trong binlog, trừ đúng transaction xoá
mysqlbinlog --exclude-gtids='3e11fa47-71ca-11e1-9e33-c80aa9429562:1235' \
  binlog.000041 binlog.000042 | mysql --login-path=admin
```

Vì sao có thể đưa cả file cũ `binlog.000041` (chứa các transaction trước bản backup)? Vì bản restore đã
có `gtid_executed` chứa `UUID:1-1200` (do câu `SET @@GLOBAL.gtid_purged` trong dump hoặc trong quy trình
restore của XtraBackup), và server tự bỏ qua transaction có GTID đã thực thi. Bạn không cần tính chính xác
position bắt đầu. Muốn dừng trước sự kiện xấu mà không phát lại phần sau, có thể dùng
`--include-gtids='UUID:1201-1234'`.

### 7.4 Bẫy của GTID khi khôi phục

- **Phát lại lên chính server gốc thì không có gì xảy ra.** Server gốc đã thực thi `UUID:1-1240`; mọi
  transaction trong binlog đều bị bỏ qua lặng lẽ. Người làm tưởng đã áp xong, thực ra không có gì được áp.
  PITR luôn làm trên một instance được restore từ backup.
- **`--skip-gtids`** xoá GTID khỏi output để thực thi như transaction mới. Manual khuyên không dùng trong
  production hay khôi phục, trừ trường hợp hiếm khi GTID thực sự gây vấn đề đã biết.
- **Nạp dump vào server đã có GTID khác**: câu `SET @@GLOBAL.gtid_purged` trong dump có thể lỗi. Xem
  `--set-gtid-purged` ở mục 3.5.

## 8. Sự cố: DELETE quên WHERE

Đây là kịch bản thực tế nhất của chương, và cũng là câu hỏi phỏng vấn "kể lại cách bạn xử lý". Lúc
14:32:07, một người chạy trực tiếp trên production:

```sql
DELETE FROM orders;            -- định viết: DELETE FROM orders WHERE id = 2;
```

`Query OK, 5 rows affected`. Autocommit đang bật, không có `ROLLBACK` nào cứu được.

### 8.1 Mười phút đầu: cầm máu, giữ bằng chứng

1. **Bình tĩnh và báo động.** Báo cho trưởng nhóm/người trực. Ghi lại **giờ chính xác** và câu lệnh. Một
   người điều phối, một người thao tác, không ai tự ý "sửa nhanh".
2. **Đánh giá phạm vi.** Bảng nào, bao nhiêu dòng, ứng dụng đang làm gì với bảng đó. Đơn hàng mới vẫn đang
   được ghi vào (id 6 lúc 14:40)?
3. **Quyết định có dừng ghi không.** Dừng ứng dụng (chế độ bảo trì) làm bài toán đơn giản hơn (không có
   dữ liệu mới xen vào), nhưng gây downtime. Nếu chỉ một bảng bị ảnh hưởng và ứng dụng vẫn chạy tạm được,
   thường chọn **không dừng** và dùng cách khôi phục từng phần (mục 8.3).
4. **Bảo vệ binlog.** Đây là bằng chứng quan trọng nhất. Chạy `FLUSH BINARY LOGS;` để đóng file hiện tại,
   chép **ngay** các file binlog từ trước bản backup gần nhất đến hiện tại sang nơi an toàn. Đảm bảo không
   có job nào `PURGE BINARY LOGS` trong lúc này.
5. **Xác định bản backup** sẽ dùng: bản full gần nhất **trước** 14:32:07 (bản 02:00), và kiểm tra nó tồn
   tại, đọc được, có vị trí binlog.
6. **Không làm thêm thao tác ghi tay** lên bảng bị hỏng (ví dụ tự gõ lại vài đơn hàng từ trí nhớ). Mọi
   thao tác thêm làm việc khôi phục khó hơn.

### 8.2 Hai hướng khôi phục

| | A. PITR toàn bộ instance | B. Khôi phục một phần (restore sang chỗ khác rồi chép ngược) |
|---|---|---|
| Cách làm | Restore bản full lên server chính, phát lại binlog, bỏ sự kiện xấu, tiếp tục | Dựng instance tạm, restore + phát lại binlog **tới ngay trước** sự kiện xấu, lấy các dòng bị xoá, chèn lại vào production |
| Downtime | Có, suốt quá trình | Không (production vẫn chạy) |
| Dữ liệu ghi sau sự cố | Phải phát lại phần binlog sau; với hệ đang chạy thì rất khó khớp | Giữ nguyên, vì production không bị đụng tới |
| Hợp với | Hỏng diện rộng (`DROP DATABASE`, nhiều bảng) | Hỏng giới hạn trong một hoặc vài bảng |

Thực tế với sự cố một bảng, hướng **B** gần như luôn được chọn. Hướng A giống mục 7.2 đầy đủ.

### 8.3 Hướng B từng bước

**Bước 1: dựng instance tạm** cùng version MySQL 8.4, trên máy khác (hoặc cổng khác), không phải
production.

**Bước 2: restore bản full 02:00** vào instance tạm (dump: `mysql < file`; XtraBackup: copy-back như mục
5.2).

**Bước 3: phát lại binlog tới ngay trước sự kiện xấu** (đã tìm được position 2310 như mục 7.2 bước 2):

```bash
mysqlbinlog --start-position=157 --stop-position=2310 /backup/binlog/binlog.000042 \
  | mysql --login-path=admin --host=restore-tmp
```

Instance tạm giờ có `orders` ở trạng thái 14:32:06: id 1 đến 5.

**Bước 4: so sánh và quyết định dòng nào cần trả lại.** Production lúc này chỉ có id 6. Các dòng cần
khôi phục là các dòng có ở instance tạm mà không có ở production: id 1 đến 5. Nhưng còn câu hỏi nghiệp vụ:
người gõ lệnh **định** xoá id 2. Có trả id 2 lại không? Đây là quyết định của người phụ trách dữ liệu, không
phải của người thao tác. Giả sử quyết định trả lại cả 5 dòng rồi làm lại thao tác xoá đúng sau.

**Bước 5: xuất các dòng từ instance tạm** dưới dạng SQL:

```bash
mysqldump --login-path=admin --host=restore-tmp \
  --no-create-info --skip-add-drop-table --single-transaction --hex-blob \
  --skip-add-locks --skip-disable-keys --set-gtid-purged=OFF \
  --where="id BETWEEN 1 AND 5" shop orders > orders-restore.sql
```

`--login-path` phải đứng **trước** mọi tuỳ chọn khác (manual: các tuỳ chọn ảnh hưởng tới việc đọc option
file phải ghi đầu tiên). `--no-create-info` để không có `CREATE TABLE`/`DROP TABLE` (tuyệt đối không muốn
`DROP TABLE` trên production). `--where` giới hạn dòng. Ba tuỳ chọn `--skip-...`/`--set-gtid-purged=OFF`
giải thích ở bước 6. **Đọc file trước khi chạy.**

**Bước 6: nạp vào production trong transaction và kiểm tra:**

```sql
START TRANSACTION;
SOURCE orders-restore.sql;       -- lệnh của client mysql
SELECT COUNT(*) FROM shop.orders;   -- kỳ vọng 6
SELECT id, customer FROM shop.orders ORDER BY id;
-- Nếu đúng:
COMMIT;
-- Nếu sai: ROLLBACK;
```

Lưu ý: mặc định (`--opt`) file dump có `LOCK TABLES ... WRITE` và `/*!40000 ALTER TABLE ... DISABLE KEYS */`
quanh `INSERT`. Cả `LOCK TABLES` lẫn `ALTER TABLE` đều làm commit ngầm transaction đang mở, nên `ROLLBACK`
sẽ không cứu được gì. Vì thế ở bước 5 dùng `--skip-add-locks --skip-disable-keys`. Ngoài ra, nếu instance
tạm bật GTID, mặc định file dump sẽ chứa `SET @@SESSION.SQL_LOG_BIN= 0` (các dòng chèn lại **không** vào
binlog, replica của production không nhận) và `SET @@GLOBAL.gtid_purged=...` (lỗi trên production);
`--set-gtid-purged=OFF` bỏ cả hai. Đây là lý do của quy tắc "đọc file trước khi chạy".

Nếu id có thể đụng nhau (ví dụ production đã cấp lại id đó, hiếm với `AUTO_INCREMENT` nhưng có thể với khoá
tự sinh khác), phải xử lý xung đột từng dòng, không dùng `REPLACE` mù quáng.

**Bước 7: kiểm tra liên quan.** Bảng con (`order_items`, thanh toán) có bị xoá theo qua
`ON DELETE CASCADE` không? Nếu có, binlog ROW cũng chứa các dòng bị xoá ở bảng con, phải khôi phục cả
chúng. Cache, search index, dữ liệu đã đồng bộ sang hệ thống khác có cần làm lại không?

**Bước 8: viết postmortem** (không đổ lỗi cá nhân) và sửa nguyên nhân gốc (mục 8.4).

> **Cách khác: đọc trực tiếp từ binlog.** Vì `binlog_row_image=full`, sự kiện `Delete_rows` chứa đầy đủ
> nội dung 5 dòng. Về nguyên tắc có thể dựng lại câu `INSERT` từ output `mysqlbinlog -v` mà không cần
> restore backup; có một số công cụ bên thứ ba tự động hoá việc "đảo ngược" sự kiện ROW (thường gọi là
> flashback). Cách này nhanh với vài dòng, nhưng phải tự chuyển đổi kiểu dữ liệu cẩn thận; với lượng lớn,
> hướng B an toàn hơn vì dữ liệu đi qua chính MySQL.

### 8.4 Phòng ngừa

- **Không ai gõ SQL ghi tay trên production** nếu không có quy trình: viết câu lệnh, cho người khác xem,
  chạy `SELECT COUNT(*)` với cùng `WHERE` trước, chạy trong `START TRANSACTION`, kiểm tra số dòng bị ảnh
  hưởng rồi mới `COMMIT`.
- Bật chế độ an toàn của client: `mysql --safe-updates` (biến `sql_safe_updates`) từ chối `UPDATE`,
  `DELETE` nếu `WHERE` không dùng cột khoá và cũng không có `LIMIT`.
- Tài khoản dùng hằng ngày chỉ có quyền đọc ([chương 18](18-user-quyen-bao-mat.md)); quyền ghi cấp tạm
  thời khi cần.
- Delayed replica (mục 1.2) cho phép lấy dữ liệu nhanh hơn restore nếu phát hiện kịp.
- Và quan trọng nhất: **đã từng tập** quy trình 8.1 đến 8.3 trước khi sự cố thật xảy ra (mục 10).

## 9. Lưu trữ, giữ bản và mã hoá

### 9.1 Quy tắc 3-2-1

Một quy tắc kinh nghiệm phổ biến: **3** bản sao dữ liệu, trên **2** loại phương tiện lưu trữ khác nhau,
trong đó **1** bản ở nơi khác (khác trung tâm dữ liệu, khác region). Nhiều nơi thêm: ít nhất một bản
**không thể sửa/xoá** trong một khoảng thời gian (immutable, ví dụ object storage có khoá đối tượng),
để chống trường hợp kẻ tấn công có quyền quản trị xoá luôn backup.

Các chỗ để backup **không** được tính là "nơi khác":

- Cùng đĩa, cùng máy với database.
- Cùng tài khoản cloud mà tài khoản chạy database có quyền xoá.
- Một thư mục mount qua mạng mà server database ghi và xoá được tuỳ ý.

### 9.2 Retention: giữ bao lâu, giữ bao nhiêu

Retention là chính sách giữ bản backup bao lâu. Một mẫu thường gặp (kiểu "ông-cha-con"):

| Loại | Giữ |
|---|---|
| Full hằng ngày | 7 bản gần nhất |
| Full hằng tuần | 4 bản |
| Full hằng tháng | 12 bản |
| Binlog | Phủ từ bản full **cũ nhất** muốn có PITR (ví dụ 7 ngày) |

Lý do giữ bản cũ: lỗi phần mềm làm hỏng dữ liệu âm thầm có thể chỉ được phát hiện sau vài tuần. Nếu chỉ
giữ 7 ngày, mọi bản backup đều đã chứa dữ liệu hỏng.

Chiều ngược lại: dữ liệu cá nhân có thể phải xoá theo yêu cầu pháp lý (quyền được xoá của người dùng).
Backup giữ quá lâu kéo theo dữ liệu đáng lẽ đã xoá. Chính sách retention phải được thống nhất với bộ phận
pháp lý, không chỉ là bài toán dung lượng.

### 9.3 Mã hoá

Backup chứa **toàn bộ** dữ liệu, kể cả email, mật khẩu đã hash, thông tin thanh toán. Một file backup bị
lộ tương đương cả database bị lộ. Vì thế:

- **Mã hoá khi truyền**: kết nối tới MySQL qua TLS; chép lên kho lưu trữ qua HTTPS/SSH.
- **Mã hoá khi lưu**: XtraBackup có `--encrypt` (mục 5.4); MySQL Shell và kho lưu trữ cloud có cơ chế mã
  hoá phía server; với `mysqldump` có thể mã hoá trong pipe (ví dụ qua `gpg` hay `openssl`) trước khi ghi
  ra đĩa.
- **Khoá phải để riêng với backup.** Khoá nằm cạnh file backup thì mã hoá vô nghĩa. Ngược lại, **mất khoá
  là mất backup**: khoá phải được lưu trữ, sao lưu và kiểm soát truy cập cẩn thận như chính dữ liệu (thường
  dùng một hệ thống quản lý khoá).
- Binlog cũng là dữ liệu. MySQL có biến `binlog_encryption` (mặc định `OFF`, cần cài keyring) để mã hoá
  file binlog và relay log trên đĩa. Khi bật, `mysqlbinlog` không đọc trực tiếp file đã mã hoá được, phải
  đọc qua server bằng `--read-from-remote-server`; hãy tính tới điều này trong quy trình PITR. Bản chép ra
  ngoài cũng cần mã hoá.
- Quyền đọc kho backup nên giới hạn chặt hơn cả quyền đọc database.

## 10. Kiểm tra restore định kỳ

### 10.1 Backup chưa restore thử thì chưa phải backup

Những lý do có thật khiến backup "chạy đều mỗi đêm" vẫn không restore được:

- Dump bị cắt cụt do lỗi giữa chừng, script không kiểm tra exit code (mục 3.4).
- Quên `--routines`/`--events`; restore xong ứng dụng gọi procedure không tồn tại.
- Thiếu tài khoản user, thiếu quyền, ứng dụng không đăng nhập được.
- Mất khoá giải mã, hoặc khoá đã bị xoay vòng mà bản backup cũ dùng khoá cũ.
- Binlog có lỗ hổng: một file bị purge trước khi được chép ra ngoài.
- Restore được, nhưng mất 20 giờ trong khi RTO cam kết là 2 giờ.
- Prepare XtraBackup chưa bao giờ chạy; bản backup hỏng mà không ai biết.

### 10.2 Quy trình kiểm tra tự động

Kiểm tra restore nên là một job **tự động, định kỳ** (ví dụ hằng tuần), không phải việc làm tay khi rảnh:

1. Lấy bản backup mới nhất **từ kho lưu trữ ngoài** (không phải từ máy database), như khi sự cố thật.
2. Giải mã, giải nén, prepare (nếu là XtraBackup).
3. Restore vào một instance MySQL dùng một lần (máy ảo, container).
4. Phát lại binlog tới một thời điểm xác định để kiểm tra cả chuỗi PITR.
5. Chạy kiểm tra:
   - Instance khởi động, `CHECK TABLE` trên các bảng quan trọng không báo lỗi.
   - Số dòng của các bảng chính nằm trong khoảng hợp lý so với production (ví dụ không ít hơn hôm qua).
   - Có đủ routine, trigger, event, user cần thiết.
   - Một vài truy vấn nghiệp vụ mẫu chạy được (đơn hàng gần nhất trước thời điểm backup có mặt).
6. **Đo thời gian** từng bước và so với RTO.
7. Huỷ instance, báo kết quả. Job thất bại thì báo động như sự cố.

Ngoài job tự động, nên định kỳ tập **diễn tập sự cố** có người tham gia: giả lập `DROP TABLE` trên môi
trường staging và để người trực làm theo runbook. Lần đầu tiên chạy runbook không nên là lúc production
đang cháy.

## 11. Đối chiếu PostgreSQL

Các khái niệm giống hệt, chỉ khác tên công cụ:

| MySQL 8.4 | PostgreSQL 18 |
|---|---|
| `mysqldump` | `pg_dump` (một database), `pg_dumpall` (cả cluster, gồm role và tablespace) |
| Restore bằng client `mysql` | `psql` cho dump dạng SQL; `pg_restore` cho dump dạng custom/directory |
| MySQL Shell / mydumper (song song) | `pg_dump -Fd -j N` và `pg_restore -j N` (directory format, nhiều job) |
| XtraBackup | `pg_basebackup` (công cụ chính thức, có sẵn) |
| Binary log | WAL (write-ahead log). Khác biệt: ở PostgreSQL, WAL vừa là log cho crash recovery vừa là log cho replication/PITR; MySQL tách redo log và binlog |
| Chép binlog ra ngoài | WAL archiving: `archive_mode`, `archive_command` / `archive_library` |
| `mysqlbinlog ... \| mysql` để PITR | Khởi động server ở chế độ recovery với `restore_command` và `recovery_target_time` |

**Logical:**

```bash
pg_dump -Fc -f shop.dump shop            # custom format, nén, chọn lọc được khi restore
pg_restore -d shop_restored -j 4 shop.dump
pg_dumpall --globals-only > globals.sql  # role, tablespace: pg_dump không chứa
```

`pg_dump` mặc định chạy trong một transaction có snapshot nhất quán, tương tự `--single-transaction`
của `mysqldump`. Cạm bẫy giống nhau: `pg_dump` một database không chứa role, phải dump role riêng.

**Physical và PITR:** cấu hình WAL archiving trong `postgresql.conf` (ví dụ từ tài liệu PostgreSQL):

```
wal_level = replica
archive_mode = on
archive_command = 'test ! -f /mnt/server/archivedir/%f && cp %p /mnt/server/archivedir/%f'
```

`archive_command` phải trả exit code 0 **khi và chỉ khi** thành công; `test ! -f` để không ghi đè file
đã có. Base backup:

```bash
pg_basebackup -D /path/to/backup -X stream
```

Khôi phục về một thời điểm: dừng server, đặt base backup vào data directory, đặt
`restore_command = 'cp /mnt/server/archivedir/%f %p'` và `recovery_target_time = '2026-10-25 14:32:06'`,
tạo file rỗng `recovery.signal` trong data directory, khởi động. Server tự lấy WAL từ kho và áp tới mốc
thời gian. Điểm khác so với MySQL: PostgreSQL tự làm phần "phát lại log", bạn chỉ khai báo đích; trong
MySQL bạn tự chạy `mysqlbinlog | mysql`.

Tài liệu PostgreSQL nhấn mạnh: `pg_dump` và `pg_dumpall` tạo backup logical, **không** dùng làm điểm bắt
đầu cho WAL replay được. Giống MySQL: muốn PITR thì bản full phải ghi nhận được vị trí log tương ứng.

Trong thực tế nhiều đội PostgreSQL dùng công cụ bên thứ ba (pgBackRest, Barman, WAL-G) để quản lý base
backup, WAL archive, retention và mã hoá, vai trò tương tự XtraBackup cộng script quản lý binlog bên MySQL.

## 12. Ghép lại: một chiến lược backup mẫu

Cho một database MySQL 8.4 khoảng 200 GB, RPO 5 phút, RTO 2 giờ, có một replica:

| Thành phần | Cách làm |
|---|---|
| Full physical | XtraBackup hằng đêm **trên replica** (không tải source), nén, mã hoá, đẩy lên object storage ở region khác |
| Incremental | XtraBackup incremental mỗi 6 giờ (rút ngắn đoạn binlog phải phát lại) |
| Binlog | `mysqlbinlog --read-from-remote-server --raw --stop-never` từ một máy riêng, đẩy file lên kho mỗi vài phút |
| Logical | MySQL Shell `util.dumpSchemas` hằng tuần, để lấy lẻ bảng và để có bản không phụ thuộc định dạng file InnoDB |
| Retention | Ngày 7, tuần 4, tháng 12; binlog 8 ngày |
| Kiểm tra | Job restore tự động hằng tuần, đo thời gian; diễn tập sự cố hằng quý |
| Bảo mật | User backup quyền tối thiểu; khoá trong hệ thống quản lý khoá; kho có bản immutable |

Lý luận khi phỏng vấn nên đi theo thứ tự: **RPO/RTO yêu cầu → chọn loại backup → binlog cho PITR → nơi lưu
và retention → mã hoá → kiểm tra restore**. Nói được thứ tự đó quan trọng hơn thuộc lòng tên tuỳ chọn.

## Lỗi thường gặp

1. **Coi replica (hoặc RAID) là backup.** Lệnh xoá nhầm được chép sang mọi bản sao trong vài mili giây.
2. **Không bao giờ thử restore.** Phát hiện backup hỏng đúng ngày cần nó.
3. **Pipeline nuốt lỗi**: `mysqldump | gzip` không có `set -o pipefail`, file cụt mà job vẫn báo thành
   công.
4. **Quên `--routines --events`** với `mysqldump`, nhất là với `--all-databases` từ 8.0 trở đi (không còn
   tự kéo theo như 5.7).
5. **Dump không có `--single-transaction`** trên InnoDB: hoặc khoá bảng chặn ứng dụng, hoặc (khi tắt khoá)
   dữ liệu không nhất quán giữa các bảng.
6. **Chạy migration (DDL) trùng giờ backup** với `mysqldump --single-transaction`: dump có thể sai hoặc lỗi.
7. **Backup không ghi vị trí binlog** (thiếu `--source-data`), hoặc binlog không được giữ đủ lâu / không
   được chép ra ngoài, nên không làm được PITR.
8. **Dùng `--stop-datetime` để áp binlog thật**: sai múi giờ của máy chạy `mysqlbinlog`, hoặc bỏ sót/thừa
   transaction trong cùng giây. Dùng thời gian để tìm, dùng position/GTID để áp.
9. **Phát lại nhiều file binlog bằng nhiều tiến trình `mysql` riêng**: mất bảng tạm giữa các file.
10. **Phát lại binlog GTID lên chính server gốc** và tưởng đã khôi phục: server bỏ qua toàn bộ GTID đã có.
11. **Quên prepare** bản XtraBackup, hoặc dùng `--apply-log-only` sai chỗ với incremental.
12. **Quên `chown -R mysql:mysql`** sau `--copy-back`; hoặc xoá datadir cũ trước khi chắc bản mới chạy được.
13. **Còn gọi `mysqlpump`** trong script khi lên 8.4: công cụ đã bị gỡ.
14. **Để backup cùng máy, cùng tài khoản** với database; hoặc để khoá giải mã cạnh file backup.
15. **Hoảng loạn khi sự cố**: gõ thêm lệnh ghi tay lên bảng hỏng, để binlog bị purge, restore đè lên
    production khi có thể khôi phục từng phần.

## Tóm tắt chương

- Durability chỉ chống crash. Lỗi con người, lỗi phần mềm, tấn công, mất đĩa cần **backup**: bản sao ở thời
  điểm quá khứ, nằm ngoài vùng sự cố, đã được thử restore. Replica và RAID không phải backup.
- **RPO** là lượng dữ liệu được phép mất, **RTO** là thời gian được phép ngừng; hai con số này quyết định
  chiến lược.
- **Logical backup** (`mysqldump`, mydumper, MySQL Shell) lưu SQL/dữ liệu text: linh hoạt, lấy lẻ bảng dễ,
  restore chậm. `mysqldump --single-transaction` dựa vào MVCC để có ảnh nhất quán mà không chặn ứng dụng;
  `--source-data=2` ghi vị trí binlog. `mysqlpump` đã bị gỡ ở 8.4.
- **Physical backup** (XtraBackup, MySQL Enterprise Backup, snapshot) chép file rồi dùng redo log để làm
  nhất quán (bước prepare): nhanh cả lúc backup lẫn restore, là lựa chọn cho database lớn.
- **Binlog** (mặc định bật, format ROW, hết hạn sau 30 ngày ở 8.4) ghi mọi thay đổi sau bản backup.
  **PITR** = restore bản full + `mysqlbinlog --start-position ... --stop-position ... | mysql`, hoặc lọc
  theo GTID (`--exclude-gtids`, `--include-gtids`).
- Sự cố `DELETE` quên `WHERE`: giữ binlog, xác định position của sự kiện xấu, thường restore sang instance
  tạm rồi chép ngược các dòng bị mất vào production.
- Lưu trữ theo 3-2-1, có bản immutable; retention có chủ đích; mã hoá với khoá để riêng; và **tự động kiểm
  tra restore** định kỳ, đo thời gian so với RTO.
- PostgreSQL: `pg_dump`/`pg_restore`, `pg_basebackup`, WAL archiving và `recovery_target_time`; cùng ý
  tưởng, khác công cụ.

## Câu hỏi tự kiểm tra

1. Nêu ba loại sự cố mà durability của InnoDB không bảo vệ được. Với mỗi loại, replica có giúp được
   không?
2. Phân biệt RPO và RTO. Một hệ thống chỉ có `mysqldump` mỗi 02:00 và không giữ binlog thì RPO tệ nhất là
   bao nhiêu?
3. Giải thích vì sao `mysqldump --single-transaction` cho bản dump nhất quán mà không chặn `INSERT` của
   ứng dụng. Điều đó chỉ đúng với loại bảng nào?
4. Vì sao `mysqldump` với `--source-data` vẫn cần global read lock trong một khoảnh khắc? Khoảnh khắc đó
   có thể biến thành vài phút trong trường hợp nào?
5. Trên MySQL 8.4, lệnh `mysqldump --all-databases > all.sql` thiếu những đối tượng nào, và vì sao ở
   MySQL 5.7 thì không thiếu?
6. Bước prepare của XtraBackup làm gì, và vì sao cần nó? Vì sao các bước prepare giữa của incremental
   phải có `--apply-log-only`?
7. Khác nhau giữa redo log và binlog là gì? Cái nào được dùng cho PITR?
8. `--stop-position=2310` có thực thi event bắt đầu ở position 2310 không? Còn `--stop-datetime` thì
   event có thời gian đúng bằng giá trị đó?
9. Vì sao manual khuyên không dùng `--start-datetime`/`--stop-datetime` để áp binlog thật?
10. Vì sao chạy `mysqlbinlog binlog.000042 | mysql` rồi `mysqlbinlog binlog.000043 | mysql` có thể lỗi?
11. Bạn phát lại binlog (server bật GTID) lên chính server gốc và không thấy dữ liệu thay đổi. Giải thích.
12. So sánh hai hướng xử lý `DELETE` quên `WHERE`: PITR toàn bộ instance và khôi phục một phần. Khi nào
    chọn hướng nào?
13. Nêu bốn lý do khiến một job backup "thành công mỗi đêm" vẫn không restore được.
14. Trong PostgreSQL, thành phần nào tương ứng với binlog của MySQL? Vì sao bản `pg_dump` không dùng làm
    điểm bắt đầu PITR được?

## Bài tập

1. **Dump và restore.** Trên MySQL 8.4 thử nghiệm, tạo database `shop` ở mục 1.5, thêm một stored
   procedure và một trigger bất kỳ. Dump bằng `mysqldump --single-transaction --source-data=2 --databases
   shop` **không** có `--routines`. Restore vào một instance khác (hoặc database tên khác) và liệt kê thứ gì
   bị thiếu. Làm lại với tuỳ chọn đúng.
2. **Thấy MVCC trong backup.** Tạo một bảng 1 triệu dòng. Mở hai terminal: một chạy `mysqldump
   --single-transaction` bảng đó, một liên tục `INSERT` trong lúc dump. So sánh số dòng trong file dump với
   số dòng trong bảng lúc dump bắt đầu và kết thúc. Giải thích.
3. **PITR theo position.** Dựng lại toàn bộ câu chuyện mẫu ở mục 1.5 trên instance thử nghiệm: backup,
   các `INSERT`, `DELETE FROM orders;`, `INSERT` sau sự cố. Sau đó khôi phục theo mục 7.2 sao cho kết quả có
   đủ id 1 đến 6. Ghi lại các position bạn tìm được và lệnh đã dùng.
4. **PITR theo GTID.** Làm lại bài 3 trên một instance bật `gtid_mode=ON` và `enforce_gtid_consistency=ON`,
   dùng `--exclude-gtids`. Thử cố tình phát lại lên chính instance gốc và quan sát chuyện gì xảy ra.
5. **Runbook.** Viết runbook một trang cho sự cố "`DROP TABLE` nhầm một bảng 50 GB trên production" với hệ
   thống có XtraBackup hằng đêm và binlog stream. Ghi rõ: ai làm gì, lệnh cụ thể, cách kiểm tra từng bước,
   ước lượng thời gian.
6. **Job kiểm tra restore.** Viết một shell script (dùng `set -euo pipefail`) lấy file dump mới nhất, khởi
   động một container MySQL 8.4 tạm, restore, so số dòng các bảng với một ngưỡng cho trước, in thời gian
   restore và trả exit code khác 0 nếu có gì sai.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [Backup and Recovery](https://dev.mysql.com/doc/refman/8.4/en/backup-and-recovery.html),
  [mysqldump](https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html),
  [mysqlbinlog](https://dev.mysql.com/doc/refman/8.4/en/mysqlbinlog.html),
  [Point-in-Time Recovery Using Event Positions](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery-positions.html),
  [Binary Logging Options and Variables](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html),
  [GTID Concepts](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids-concepts.html),
  [What Is New in MySQL 8.4](https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html) (phần các tính
  năng bị gỡ: `mysqlpump`, `expire_logs_days`, `SHOW MASTER STATUS`).
- MySQL Shell: [Instance Dump, Schema Dump, and Table Dump Utilities](https://dev.mysql.com/doc/mysql-shell/8.4/en/mysql-shell-utilities-dump-instance-schema.html),
  [Dump Loading Utility](https://dev.mysql.com/doc/mysql-shell/8.4/en/mysql-shell-utilities-load-dump.html).
- Percona XtraBackup 8.4: [tài liệu](https://docs.percona.com/percona-xtrabackup/8.4/) (các trang
  Create a full backup, Prepare a full backup, Restore a backup, Create/Prepare an incremental backup,
  Encrypt backups, Create a compressed backup).
- mydumper: [mydumper usage](https://mydumper.github.io/mydumper/docs/html/mydumper_usage.html),
  [myloader usage](https://mydumper.github.io/mydumper/docs/html/myloader_usage.html).
- PostgreSQL 18: [Backup and Restore](https://www.postgresql.org/docs/18/backup.html),
  [Continuous Archiving and Point-in-Time Recovery](https://www.postgresql.org/docs/18/continuous-archiving.html),
  [pg_dump](https://www.postgresql.org/docs/18/app-pgdump.html),
  [pg_basebackup](https://www.postgresql.org/docs/18/app-pgbasebackup.html).
