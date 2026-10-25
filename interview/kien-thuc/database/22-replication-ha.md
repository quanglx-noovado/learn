# Chương 22. Replication và high availability

> [← Mục lục](README.md) · [← Chương 21: Sao lưu và khôi phục](21-backup-restore.md) · [Chương 23: Partitioning, sharding và mở rộng →](23-partition-sharding-scale.md)

**Bạn sẽ học được:**

- Replication là gì, giải quyết ba bài toán nào (đọc nhiều, sẵn sàng cao, sao lưu/báo cáo), và nó
  **không** giải quyết bài toán nào.
- Replication dựa trên binary log của MySQL: *source* và *replica*, bộ thuật ngữ mới của MySQL 8.4
  (các lệnh `MASTER`/`SLAVE` cũ đã bị xoá), lệnh `CHANGE REPLICATION SOURCE TO` và `START REPLICA`.
- Bên trong: thread *binlog dump* trên source, thread *receiver* (I/O) và *applier* (SQL) trên replica,
  *relay log*, *multi-threaded applier*, và GTID.
- Ba mức đồng bộ: asynchronous, semisynchronous (`AFTER_SYNC` khác `AFTER_COMMIT` ra sao), và Group
  Replication.
- Replication lag: vì sao có, đo bằng gì (`Seconds_Behind_Source`, `performance_schema`, heartbeat),
  và vấn đề *read-your-writes* khi đọc từ replica.
- Failover: chuyển replica lên làm source, *split brain*, *fencing*; công cụ (InnoDB Cluster, MySQL
  Router, Orchestrator, RDS/Aurora).
- Ứng dụng chịu failover thế nào: retry, reconnect, cấu hình `read`/`write`/`sticky` của Laravel.
- Đối chiếu ngắn với streaming replication của PostgreSQL.

**Cần biết trước:** [Chương 13](13-transaction-acid.md) (transaction, commit),
[Chương 16](16-ben-trong-innodb.md) (redo log, binary log, two-phase commit giữa chúng),
[Chương 18](18-user-quyen-bao-mat.md) (tạo user, cấp quyền),
[Chương 19](19-database-tu-ung-dung.md) (kết nối từ ứng dụng, connection pool),
[Chương 21](21-backup-restore.md) (backup và binlog dùng cho point-in-time recovery).

## 1. Replication là gì và để làm gì

### 1.1 Một server là một điểm chết

Đến giờ, mọi ví dụ trong giáo trình chạy trên **một** MySQL server. Ứng dụng thật chạy trên một
server sẽ gặp ba giới hạn:

1. **Server hỏng là ứng dụng dừng.** Ổ đĩa hỏng, kernel panic, máy ảo bị nhà cung cấp cloud thu hồi,
   hay đơn giản là bạn cần khởi động lại để vá bảo mật. Trong thời gian đó không ai đọc hay ghi được.
   Đây gọi là *single point of failure* (điểm hỏng duy nhất).
2. **Đọc nhiều hơn một máy chịu nổi.** Ứng dụng web điển hình đọc nhiều hơn ghi rất nhiều (xem trang
   sản phẩm nhiều hơn đặt hàng). Đến lúc CPU của một server không đủ cho mọi câu `SELECT`.
3. **Việc nặng làm phiền việc chính.** Chạy báo cáo cuối tháng, chạy backup, chạy truy vấn phân tích
   ngay trên server đang phục vụ người dùng làm mọi người chậm theo.

### 1.2 Định nghĩa

**Replication** (nhân bản) là cơ chế giữ một hoặc nhiều bản sao của database trên các server khác,
và **tự động cập nhật** các bản sao đó khi dữ liệu gốc thay đổi.

- Server nhận ghi từ ứng dụng gọi là **source** (trước đây gọi là *master*, PostgreSQL gọi là
  *primary*).
- Server giữ bản sao và nhận thay đổi từ source gọi là **replica** (trước đây gọi là *slave*,
  PostgreSQL gọi là *standby*).

```
               ghi + đọc
   Ứng dụng ───────────────▶ source
       │                       │  gửi thay đổi (binary log)
       │ chỉ đọc               ├──────────────▶ replica 1
       └──────────────────────▶│
                               └──────────────▶ replica 2
```

### 1.3 Replication giúp gì, và không giúp gì

| Mục đích | Replication giúp thế nào |
|---|---|
| Sẵn sàng cao (*high availability*, HA) | Source hỏng thì đưa một replica lên làm source mới (*failover*). |
| Mở rộng đọc (*read scaling*) | Chia các câu `SELECT` sang nhiều replica. |
| Tách việc nặng | Backup, báo cáo, ETL chạy trên một replica riêng. |
| Gần người dùng | Đặt replica ở vùng địa lý khác để đọc nhanh hơn. |

Replication **không** thay thế backup. Nếu ai đó chạy `DELETE FROM orders;` trên source, câu lệnh đó
được nhân bản sang mọi replica trong vài mili giây. Mọi bản sao đều mất dữ liệu cùng lúc. Chỉ backup
(Chương 21) mới cho phép quay lại thời điểm trước lỗi. (Có một ngoại lệ một phần: *delayed replica*,
xem mục 3.6.)

Replication cũng **không** giúp mở rộng ghi. Mọi câu `INSERT`/`UPDATE` vẫn phải chạy trên source, rồi
**chạy lại** trên từng replica. Ghi nhiều quá một server chịu nổi là bài toán của Chương 23 (sharding).

### 1.4 High availability đo bằng gì

Hai con số hay gặp khi nói về HA:

- **RPO** (*Recovery Point Objective*): khi có sự cố, chấp nhận **mất tối đa bao nhiêu dữ liệu**
  (tính theo thời gian). RPO = 0 nghĩa là không được mất transaction nào đã báo commit thành công.
- **RTO** (*Recovery Time Objective*): chấp nhận **dừng dịch vụ bao lâu** đến khi phục vụ lại.

Hai con số này quyết định bạn chọn cơ chế nào trong chương: async replication có RPO lớn hơn 0
(mục 4.1), semisync `AFTER_SYNC` và Group Replication hướng đến RPO = 0 (mục 4.2, 4.3); failover thủ
công có RTO tính bằng phút đến giờ, failover tự động có RTO tính bằng giây đến vài chục giây (mục 7, 8).

Người ta cũng hay nói "ba số 9", "bốn số 9": 99,9% thời gian sẵn sàng trong năm tương đương khoảng
8,76 giờ dừng mỗi năm; 99,99% tương đương khoảng 52,6 phút. (Tính tay: 365 × 24 = 8760 giờ;
8760 × 0,001 = 8,76 giờ; 8760 × 60 × 0,0001 = 52,56 phút.)

## 2. Binary log replication của MySQL

### 2.1 Ý tưởng: ghi lại mọi thay đổi rồi phát lại

Ở Chương 16 bạn đã gặp **binary log** (binlog): file mà MySQL ghi lại mọi thay đổi dữ liệu theo thứ
tự commit. Ở Chương 21, binlog được dùng cho point-in-time recovery: phục hồi backup rồi "phát lại"
binlog đến thời điểm mong muốn.

Replication của MySQL dùng đúng ý tưởng đó, chỉ là làm **liên tục**: replica kết nối đến source, đọc
binlog của source khi nó vừa được ghi, rồi phát lại trên dữ liệu của mình. Nếu replica bắt đầu từ một
bản sao giống hệt source tại một thời điểm, và phát lại đúng mọi thay đổi theo đúng thứ tự kể từ thời
điểm đó, thì nó sẽ luôn giống source (chậm hơn một chút).

Hai điều kiện trong câu trên là nền tảng của mọi sự cố replication:

1. **Điểm bắt đầu phải khớp.** Replica phải biết chính xác nó bắt đầu từ vị trí nào trong binlog của
   source. Sai vị trí là thiếu hoặc lặp thay đổi.
2. **Phát lại phải cho cùng kết quả.** Nếu một câu lệnh chạy trên replica cho kết quả khác trên source
   (ví dụ `UPDATE ... LIMIT 1` không có `ORDER BY`), dữ liệu lệch nhau âm thầm.

### 2.2 Thuật ngữ mới trong MySQL 8.4

Trong loạt bản 8.0 về sau, MySQL lần lượt thêm tên mới (`SOURCE`, `REPLICA`) cho các lệnh và biến
replication, giữ tên cũ (`MASTER`, `SLAVE`) ở dạng deprecated. **MySQL 8.4 xoá hẳn các lệnh cũ**: gõ
`START SLAVE` trên 8.4 là lỗi cú pháp. Đây là điểm bạn sẽ gặp ngay khi đọc tài liệu hay blog cũ.

| Lệnh cũ (đã bị xoá trong 8.4) | Lệnh dùng trên 8.4 |
|---|---|
| `CHANGE MASTER TO` | `CHANGE REPLICATION SOURCE TO` |
| `START SLAVE` / `STOP SLAVE` | `START REPLICA` / `STOP REPLICA` |
| `SHOW SLAVE STATUS` | `SHOW REPLICA STATUS` |
| `RESET SLAVE` | `RESET REPLICA` |
| `SHOW SLAVE HOSTS` | `SHOW REPLICAS` |
| `SHOW MASTER STATUS` | `SHOW BINARY LOG STATUS` |
| `SHOW MASTER LOGS` | `SHOW BINARY LOGS` |
| `PURGE MASTER LOGS` | `PURGE BINARY LOGS` |
| `RESET MASTER` | `RESET BINARY LOGS AND GTIDS` |

Các tuỳ chọn trong `CHANGE REPLICATION SOURCE TO` cũng đổi tên theo: `MASTER_HOST` thành
`SOURCE_HOST`, `MASTER_AUTO_POSITION` thành `SOURCE_AUTO_POSITION`, `GET_MASTER_PUBLIC_KEY` thành
`GET_SOURCE_PUBLIC_KEY`, v.v. Cột trong `SHOW REPLICA STATUS` cũng vậy: `Seconds_Behind_Master` thành
`Seconds_Behind_Source`.

Vài chỗ vẫn còn tên cũ, đừng ngạc nhiên:

- Tên **quyền** vẫn là `REPLICATION SLAVE` (quyền cho user mà replica dùng để kết nối) và
  `REPLICATION_SLAVE_ADMIN`.
- Plugin semisync kiểu cũ (`rpl_semi_sync_master`/`rpl_semi_sync_slave`) vẫn còn trong 8.4 nhưng
  deprecated; dùng bản mới `rpl_semi_sync_source`/`rpl_semi_sync_replica` (mục 4.2).
- Một số bảng hệ thống như `mysql.slave_master_info` vẫn mang tên cũ.

Giáo trình này dùng *source*/*replica* xuyên suốt.

### 2.3 Ba thread làm nên replication

```
         SOURCE                                   REPLICA
 ┌──────────────────────┐              ┌────────────────────────────────────┐
 │ client COMMIT        │              │                                    │
 │      │               │              │  receiver thread (I/O)             │
 │      ▼               │   TCP        │      │  ghi                        │
 │  binary log ──▶ binlog dump thread ─┼──────┘──▶ relay log                │
 │                      │              │              │  đọc                │
 └──────────────────────┘              │              ▼                     │
                                       │  applier thread(s) (SQL)           │
                                       │      │  chạy lại transaction       │
                                       │      ▼                             │
                                       │  dữ liệu của replica (InnoDB)      │
                                       └────────────────────────────────────┘
```

1. **Binlog dump thread** (trên source). Mỗi replica kết nối vào thì source tạo một thread để gửi nội
   dung binlog cho replica đó. Trong `SHOW PROCESSLIST` của source, nó hiện với `Command` là
   `Binlog Dump` (hoặc `Binlog Dump GTID` khi replica dùng GTID auto-positioning).
2. **Receiver thread**, còn gọi là *I/O thread* (trên replica). Tạo ra khi chạy `START REPLICA`. Nó
   kết nối đến source, nhận các event mà binlog dump thread gửi, và **chép nguyên** vào file trên đĩa
   của replica gọi là **relay log**. Thread này không chạy câu SQL nào.
3. **Applier thread**, còn gọi là *SQL thread* (trên replica). Đọc relay log và thực thi các
   transaction trong đó lên dữ liệu của replica.

Vì sao tách receiver và applier? Vì nhận dữ liệu qua mạng thường nhanh, còn chạy lại transaction có thể
chậm. Tách ra thì replica vẫn tiếp tục kéo binlog về đĩa của mình kể cả khi applier đang tụt lại. Nếu
source chết lúc đó, những gì đã nằm trong relay log vẫn còn để áp dụng nốt.

**Relay log** có định dạng giống binlog. Applier áp dụng xong một file relay log thì MySQL tự xoá file
đó (mặc định `relay_log_purge = ON`). Vị trí đã nhận và đã áp dụng được lưu trong *replication
metadata repositories* (mặc định là bảng InnoDB trong schema `mysql`), nhờ vậy replica crash rồi khởi
động lại vẫn biết tiếp tục từ đâu.

### 2.4 Multi-threaded applier

Trên source, hàng trăm session ghi song song. Nếu replica chỉ có **một** applier thread chạy lại từng
transaction một, replica không bao giờ theo kịp source bận rộn. Vì vậy MySQL có **multi-threaded
applier** (còn gọi là *multithreaded replica*, MTR):

- Một **coordinator thread** đọc relay log tuần tự và phân transaction cho các **worker thread**.
- Số worker do biến `replica_parallel_workers` quy định. **Mặc định là 4** trong MySQL 8.4,
  tức replica mặc định đã chạy đa luồng. Đặt bằng 0 bị deprecated; muốn một luồng thì đặt 1.
- Coordinator quyết định hai transaction có được chạy song song hay không dựa trên thông tin
  phụ thuộc mà source ghi vào binlog (chính sách `LOGICAL_CLOCK`, là mặc định; biến
  `replica_parallel_type` chọn chính sách này đã deprecated). Nói đơn giản: hai transaction đã
  commit đồng thời trên source mà không đụng cùng dòng thì có thể chạy song song trên replica.
- `replica_preserve_commit_order` **mặc định ON**: dù chạy song song, các transaction được *commit*
  trên replica theo đúng thứ tự trong relay log. Nhờ vậy người đọc replica không thấy trạng thái mà
  source chưa từng có (ví dụ thấy transaction sau mà chưa thấy transaction trước).

```sql
-- Trên replica: xem cấu hình applier
SELECT @@replica_parallel_workers, @@replica_preserve_commit_order;
```

```
+----------------------------+---------------------------------+
| @@replica_parallel_workers | @@replica_preserve_commit_order |
+----------------------------+---------------------------------+
|                          4 |                               1 |
+----------------------------+---------------------------------+
```

(output minh hoạ với giá trị mặc định của 8.4)

### 2.5 binlog_format: ghi câu lệnh hay ghi dòng

Binlog có thể ghi thay đổi theo hai cách chính:

- **STATEMENT** (*statement-based replication*, SBR): ghi nguyên câu SQL, replica chạy lại câu đó.
- **ROW** (*row-based replication*, RBR): ghi **giá trị của từng dòng** bị thay đổi (ảnh trước và sau),
  replica áp dụng trực tiếp lên dòng đó.
- **MIXED**: mặc định ghi statement, tự chuyển sang row với câu lệnh "không an toàn".

Mặc định của `binlog_format` là **`ROW`**, và trong MySQL 8.4 bản thân biến `binlog_format` đã
**deprecated**: manual khuyên mọi hệ thống replication mới chỉ dùng ROW, các định dạng khác có thể bị
bỏ trong tương lai.

Vì sao ROW thắng? Xét dữ liệu mẫu:

```sql
CREATE TABLE tickets (
  id         INT PRIMARY KEY AUTO_INCREMENT,
  status     VARCHAR(10) NOT NULL,
  created_at DATETIME NOT NULL
);
INSERT INTO tickets (status, created_at) VALUES
  ('open', '2026-10-01 08:00:00'),
  ('open', '2026-10-02 09:00:00'),
  ('open', '2026-10-03 10:00:00');

UPDATE tickets SET status = 'closed' LIMIT 1;   -- không ORDER BY
```

Với STATEMENT, replica chạy lại `UPDATE ... LIMIT 1`. "Dòng đầu tiên" mà câu này chọn phụ thuộc vào
thứ tự quét, thứ tự này **không được SQL đảm bảo**. Source có thể đóng ticket 1, replica đóng ticket 2.
Hai bên lệch nhau và không ai báo lỗi. Các hàm như `UUID()`, `SYSDATE()`, `RAND()` không seed cũng
gây vấn đề tương tự. Với ROW, binlog ghi "dòng id = 1 đổi status từ open thành closed", replica áp
dụng đúng dòng đó, không cần suy luận lại.

Cái giá của ROW: một câu `UPDATE` chạm 1 triệu dòng tạo ra 1 triệu dòng thay đổi trong binlog (với
`binlog_row_image = FULL`, mặc định, là cả ảnh trước và ảnh sau đầy đủ cột). Binlog to hơn, và replica
phải áp dụng 1 triệu thay đổi. Đây là một lý do để chia việc lớn thành batch nhỏ (Chương 20, mục 6).

**Cạm bẫy của ROW: bảng không có primary key.** Khi áp dụng thay đổi một dòng, replica phải **tìm**
dòng đó. Có primary key thì tìm bằng index, rất nhanh. Không có primary key (và không có unique index
phù hợp) thì replica có thể phải quét cả bảng cho **mỗi** dòng thay đổi: xoá 10.000 dòng trên bảng
1 triệu dòng có thể thành 10.000 lần quét toàn bảng. Replica tụt lag hàng giờ vì một câu `DELETE`. Mọi
bảng nên có primary key (Chương 04); Group Replication còn bắt buộc điều này.

### 2.6 GTID: định danh toàn cục cho mỗi transaction

Cách cổ điển để replica biết "bắt đầu từ đâu" là **toạ độ binlog**: tên file và vị trí byte, ví dụ
`binlog.000042`, vị trí `1573`. Cách này có một điểm yếu lớn khi failover: toạ độ chỉ có nghĩa trên
**một** server. Replica B muốn chuyển sang lấy dữ liệu từ replica C (vừa lên làm source) thì phải tự
tìm xem "vị trí 1573 trong `binlog.000042` của source cũ" tương ứng với vị trí nào trong binlog của C.
Làm tay việc này dưới áp lực sự cố là nguồn gốc của rất nhiều lần mất hoặc lặp dữ liệu.

**GTID** (*Global Transaction Identifier*) giải quyết bằng cách gắn cho mỗi transaction một định danh
duy nhất toàn hệ thống, dạng:

```
source_uuid:transaction_id
3E11FA47-71CA-11E1-9E33-C80AA9429562:23
```

- `source_uuid` là `server_uuid` của server nơi transaction được commit lần đầu.
- `transaction_id` là số thứ tự tăng dần trên server đó.

Định danh đi theo transaction qua mọi replica. Mỗi server ghi nhớ **tập** GTID đã thực thi trong biến
`gtid_executed`, viết gọn dạng khoảng, ví dụ `3E11...9562:1-1000`. Khi replica kết nối với
`SOURCE_AUTO_POSITION = 1`, nó gửi tập GTID mình đã có, source tự tính phần còn thiếu và gửi đúng phần
đó. Không ai phải nhớ tên file hay vị trí byte nữa, và đổi source khi failover chỉ là một lệnh
`CHANGE REPLICATION SOURCE TO` trỏ sang host mới.

GTID cũng chặn việc áp dụng một transaction hai lần: nếu GTID đã có trong `gtid_executed`, replica
bỏ qua.

Trong MySQL 8.4, `gtid_mode` mặc định vẫn là **OFF**. Muốn dùng GTID phải bật cả hai biến
`gtid_mode = ON` và `enforce_gtid_consistency = ON` (biến thứ hai từ chối các câu lệnh không thể ghi
log an toàn thành một transaction có GTID). Với hệ thống mới, gần như luôn nên bật GTID; InnoDB Cluster
và Group Replication bắt buộc GTID.

### 2.7 Thiết lập một cặp source/replica (lab)

Phần này dựng hai MySQL 8.4 trên cùng một máy ở cổng **3307** (source) và **3308** (replica), để không
đụng vào MySQL nào đang chạy ở cổng 3306. Bạn cần binary `mysqld` và `mysql` của MySQL 8.4.

**Bước 1. Khởi tạo hai data directory.**

```bash
mkdir -p ~/rpl-lab
mysqld --no-defaults --initialize-insecure --datadir=$HOME/rpl-lab/src
mysqld --no-defaults --initialize-insecure --datadir=$HOME/rpl-lab/rep
```

`--initialize-insecure` tạo user `root@localhost` không mật khẩu; chỉ dùng cho lab.

**Bước 2. Chạy source.** Mỗi server trong một topology replication phải có `server_id` khác nhau.

```bash
mysqld --no-defaults --datadir=$HOME/rpl-lab/src \
  --port=3307 --socket=$HOME/rpl-lab/src.sock --mysqlx=OFF \
  --server-id=1 --log-bin=binlog \
  --gtid-mode=ON --enforce-gtid-consistency=ON &
```

Binary log mặc định đã bật trong 8.x; `--log-bin=binlog` chỉ đặt tên file cho rõ.

**Bước 3. Chạy replica.**

```bash
mysqld --no-defaults --datadir=$HOME/rpl-lab/rep \
  --port=3308 --socket=$HOME/rpl-lab/rep.sock --mysqlx=OFF \
  --server-id=2 --log-bin=binlog \
  --gtid-mode=ON --enforce-gtid-consistency=ON \
  --super-read-only=ON &
```

`super_read_only = ON` cấm mọi câu ghi từ client, kể cả user có quyền cao; chỉ applier thread được
ghi. Đây là hàng rào chống việc ai đó (hoặc ứng dụng cấu hình sai) ghi nhầm vào replica làm dữ liệu
lệch.

**Bước 4. Tạo user replication trên source.**

```sql
-- mysql -uroot -S ~/rpl-lab/src.sock
CREATE USER 'repl'@'127.0.0.1' IDENTIFIED BY 'repl-pass-2026';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'127.0.0.1';
```

**Bước 5. Trỏ replica vào source và khởi động.**

```sql
-- mysql -uroot -S ~/rpl-lab/rep.sock
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST = '127.0.0.1',
  SOURCE_PORT = 3307,
  SOURCE_USER = 'repl',
  SOURCE_PASSWORD = 'repl-pass-2026',
  SOURCE_AUTO_POSITION = 1,
  GET_SOURCE_PUBLIC_KEY = 1;

START REPLICA;
```

Vì sao có `GET_SOURCE_PUBLIC_KEY = 1`? User `repl` dùng plugin xác thực mặc định
`caching_sha2_password`. Khi kết nối không mã hoá (lab này không bật `SOURCE_SSL`), replica cần public
key RSA của source để gửi mật khẩu an toàn; source chỉ gửi key khi được yêu cầu. Thiếu tuỳ chọn này,
receiver thread báo lỗi xác thực. Trên production nên dùng `SOURCE_SSL = 1` để mã hoá cả luồng dữ
liệu replication.

Lab này bắt đầu khi source còn trống, nên replica không cần bản sao ban đầu. Với source đã có dữ
liệu, trước tiên phải đưa một bản sao nhất quán sang replica: dùng backup vật lý (Chương 21) hoặc
*clone plugin* (`CLONE INSTANCE FROM ...`), rồi mới `CHANGE REPLICATION SOURCE TO`.

**Bước 6. Thử.**

```sql
-- Trên source (3307)
CREATE DATABASE shop;
CREATE TABLE shop.orders (
  id     BIGINT PRIMARY KEY AUTO_INCREMENT,
  amount DECIMAL(10,2) NOT NULL
);
INSERT INTO shop.orders (amount) VALUES (100.00), (250.50);

-- Trên replica (3308)
SELECT * FROM shop.orders;
```

```
+----+--------+
| id | amount |
+----+--------+
|  1 | 100.00 |
|  2 | 250.50 |
+----+--------+
```

Thử ghi trên replica:

```sql
-- Trên replica (3308)
INSERT INTO shop.orders (amount) VALUES (1.00);
```

```
ERROR 1290 (HY000): The MySQL server is running with the --super-read-only option
so it cannot execute this statement
```

(output minh hoạ)

**Dọn lab:** `mysqladmin -uroot -S ~/rpl-lab/rep.sock shutdown`, tương tự cho `src.sock`, rồi xoá
thư mục `~/rpl-lab`.

### 2.8 Đọc SHOW REPLICA STATUS

`SHOW REPLICA STATUS\G` là lệnh bạn sẽ chạy nhiều nhất khi vận hành replica. Các cột quan trọng:

```
             Replica_IO_State: Waiting for source to send event
                  Source_Host: 127.0.0.1
                  Source_Port: 3307
           Replica_IO_Running: Yes
          Replica_SQL_Running: Yes
                Last_IO_Error:
               Last_SQL_Error:
        Seconds_Behind_Source: 0
           Retrieved_Gtid_Set: 5a1c...e0f1:1-5
            Executed_Gtid_Set: 5a1c...e0f1:1-5,
                               9b7d...2a33:1-2
                Auto_Position: 1
```

(output minh hoạ, đã lược bớt cột)

| Cột | Ý nghĩa |
|---|---|
| `Replica_IO_Running` | Receiver thread: `Yes`, `No`, hoặc `Connecting` (đang cố kết nối). |
| `Replica_SQL_Running` | Applier thread có chạy không. |
| `Last_IO_Error`, `Last_SQL_Error` | Lỗi gần nhất của từng thread. Applier dừng vì lỗi thì đọc ở đây. |
| `Seconds_Behind_Source` | Ước lượng độ trễ, xem mục 5.2. |
| `Retrieved_Gtid_Set` | Các GTID receiver đã nhận về relay log. |
| `Executed_Gtid_Set` | Các GTID đã thực thi trên replica (bằng `gtid_executed`). |

Trong ví dụ, `Executed_Gtid_Set` có thêm một UUID thứ hai `9b7d...:1-2`: đó là hai transaction được
commit **trực tiếp trên replica** (ví dụ ai đó tạo user hay sửa dữ liệu ngay trên replica khi chưa bật
`super_read_only`). GTID "lạ" kiểu này gọi là *errant transaction*. Nó vô hại cho đến khi replica này
được đưa lên làm source: khi đó các replica khác sẽ cố kéo những transaction lạ đó về, có thể lỗi hoặc
làm lệch dữ liệu. Công cụ failover tốt đều kiểm tra errant transaction trước khi promote.

Hai thread hiện `Yes` cả hai và lỗi trống là trạng thái khoẻ. Một mẫu lỗi hay gặp:
`Replica_SQL_Running: No` với `Last_SQL_Error` dạng "Duplicate entry ... for key 'PRIMARY'" (applier
cố `INSERT` một dòng đã tồn tại, thường vì ai đó đã ghi tay vào replica). Đừng vội "skip lỗi cho chạy
tiếp": dữ liệu đã lệch, và skip chỉ che giấu điều đó. Hướng đúng là tìm nguyên nhân, và nếu không chắc
dữ liệu khớp thì dựng lại replica từ bản sao mới.

Bảng tương đương trong `performance_schema` (dễ truy vấn bằng SQL hơn):

```sql
SELECT CHANNEL_NAME, SERVICE_STATE, LAST_ERROR_MESSAGE,
       LAST_HEARTBEAT_TIMESTAMP
FROM performance_schema.replication_connection_status;

SELECT WORKER_ID, SERVICE_STATE, LAST_ERROR_MESSAGE
FROM performance_schema.replication_applier_status_by_worker;
```

Trên source, `SHOW REPLICAS` liệt kê các replica đang kết nối, `SHOW BINARY LOG STATUS` cho file binlog
hiện tại và `Executed_Gtid_Set` của source.

### 2.9 Topology thường gặp

- **Một source, nhiều replica** (hình sao): phổ biến nhất.
- **Chuỗi** (*chain*): source → replica A → replica B. A phải bật `log_replica_updates` (mặc định
  **ON**) để ghi lại những gì nó áp dụng vào binlog của chính nó, nhờ vậy B mới đọc được. Dùng để giảm
  tải cho source khi có rất nhiều replica, đổi lại B trễ hơn.
- **Multi-source**: một replica nhận từ nhiều source qua nhiều *channel* (gom dữ liệu để phân tích).
- **Source-source** (hai server ghi lẫn nhau, *circular*): kỹ thuật cũ, dễ xung đột khi cả hai cùng
  nhận ghi. Nếu cần nhiều nơi ghi, dùng Group Replication thay vì tự ghép.

## 3. Những chi tiết vận hành cần biết

### 3.1 Giữ binlog đủ lâu

Source tự xoá binlog cũ sau `binlog_expire_logs_seconds` giây (mặc định **2592000**, tức 30 ngày).
Nếu một replica tắt lâu hơn thời gian đó, khi bật lại nó cần những binlog đã bị xoá và receiver thread
báo lỗi; lúc đó chỉ còn cách dựng lại replica. Ngược lại, giữ binlog quá lâu tốn đĩa. Hãy đặt giá trị
này dài hơn khoảng thời gian dài nhất bạn tưởng tượng một replica có thể ngừng (và dài hơn chu kỳ
backup nếu dùng binlog cho point-in-time recovery).

### 3.2 sync_binlog và innodb_flush_log_at_trx_commit

Để source crash mà không mất transaction đã báo commit và binlog khớp với dữ liệu InnoDB, cần
`sync_binlog = 1` (mặc định) và `innodb_flush_log_at_trx_commit = 1` (mặc định), như đã học ở
Chương 16. Đặt giá trị khác để "nhanh hơn" thì khi source crash, binlog có thể thiếu transaction mà
InnoDB đã có (hoặc ngược lại), và replica lệch với source vĩnh viễn.

### 3.3 Replica cũng cần được bảo vệ khỏi crash

Replica nên bật `relay_log_recovery = ON`: khi khởi động lại sau crash, nó bỏ relay log có thể hỏng
và tải lại từ source kể từ vị trí đã áp dụng. Với GTID auto-positioning, việc tìm lại vị trí là tự động.

### 3.4 Kết nối và heartbeat

Nếu source không có gì mới để gửi, kết nối replication im lặng. Làm sao replica phân biệt "source
rảnh" với "mạng đã đứt"? Bằng **heartbeat**: source gửi tín hiệu định kỳ khi không có event.

- `replica_net_timeout` (mặc định **60** giây): quá thời gian này không nhận được dữ liệu hay
  heartbeat, replica coi kết nối đã chết và kết nối lại.
- `SOURCE_HEARTBEAT_PERIOD` (tuỳ chọn của `CHANGE REPLICATION SOURCE TO`): khoảng gửi heartbeat, mặc
  định bằng **một nửa** `replica_net_timeout`.
- `SOURCE_CONNECT_RETRY` (mặc định 60 giây) và `SOURCE_RETRY_COUNT` (mặc định 10 lần): khoảng cách
  và số lần thử kết nối lại.

Thời điểm heartbeat cuối nằm ở cột `LAST_HEARTBEAT_TIMESTAMP` của
`performance_schema.replication_connection_status`. Lưu ý: đây là heartbeat **của giao thức
replication**, chỉ cho biết kết nối còn sống. Nó khác với kỹ thuật "bảng heartbeat" để đo lag ở mục
5.4.

### 3.5 Lọc replication

Có thể chỉ nhân bản một phần (`REPLICATE_DO_DB`, `REPLICATE_IGNORE_TABLE`... qua lệnh
`CHANGE REPLICATION FILTER`). Dùng cẩn thận: replica lọc dữ liệu thì không còn là bản sao đầy đủ, không
dùng để failover được.

### 3.6 Delayed replica

`CHANGE REPLICATION SOURCE TO SOURCE_DELAY = 3600;` làm replica cố ý áp dụng chậm 1 giờ (mặc định 0).
Nếu có người chạy nhầm `DROP TABLE` trên source, bạn có 1 giờ để dừng applier trên delayed replica
(`STOP REPLICA SQL_THREAD;`) trước khi câu lệnh độc hại được áp dụng, rồi lấy dữ liệu ra. Đây là lưới
an toàn bổ sung, không thay được backup.

## 4. Ba mức đồng bộ: async, semi-sync, Group Replication

Câu hỏi trung tâm của mục này: **khi ứng dụng nhận "COMMIT thành công", transaction đó đã nằm trên
bao nhiêu server?** Câu trả lời quyết định bạn có mất dữ liệu khi source chết hay không.

### 4.1 Asynchronous (mặc định)

Replication mặc định của MySQL là **asynchronous** (bất đồng bộ). Source ghi transaction vào binlog,
commit, trả kết quả cho client. Việc replica có kéo về hay chưa, source **không biết và không chờ**.

Timeline khi source chết đúng lúc xấu:

| Thời điểm | Client | Source | Replica |
|---|---|---|---|
| t1 | `COMMIT` đơn hàng #501 | ghi binlog, commit InnoDB | chưa nhận |
| t2 | nhận "OK", báo người dùng đặt hàng thành công | | chưa nhận |
| t3 | | **crash, đĩa hỏng** | chưa nhận |
| t4 | | | được promote lên làm source mới |
| t5 | người dùng tra đơn #501: **không tồn tại** | | |

Transaction đã báo thành công nhưng mất. RPO của async lớn hơn 0, cụ thể là lượng transaction chưa kịp
sang replica tại thời điểm sự cố (thường là mili giây đến vài giây, nhưng lúc replica đang lag nặng
có thể nhiều hơn nhiều).

Ưu điểm của async: commit trên source không phải chờ mạng, nhanh nhất, và replica ở xa (khác vùng địa
lý) hay chậm cũng không ảnh hưởng source.

### 4.2 Semisynchronous

**Semisynchronous replication** (semi-sync) chen vào giữa: source chỉ trả "OK" cho client sau khi
**ít nhất một replica xác nhận đã nhận** transaction. "Nhận" ở đây nghĩa là replica đã ghi các event
của transaction vào relay log **và flush xuống đĩa**; replica **chưa cần áp dụng** nó.

Semi-sync được cài bằng plugin, phải bật ở **cả hai** phía:

```sql
-- Trên source
INSTALL PLUGIN rpl_semi_sync_source SONAME 'semisync_source.so';
SET GLOBAL rpl_semi_sync_source_enabled = 1;

-- Trên mỗi replica
INSTALL PLUGIN rpl_semi_sync_replica SONAME 'semisync_replica.so';
SET GLOBAL rpl_semi_sync_replica_enabled = 1;
STOP REPLICA IO_THREAD;     -- bật lúc đang chạy thì phải khởi động lại receiver
START REPLICA IO_THREAD;    -- để nó đăng ký lại với source ở chế độ semi-sync
```

Muốn giữ sau khi restart thì ghi các biến `rpl_semi_sync_source_enabled=1` /
`rpl_semi_sync_replica_enabled=1` vào file cấu hình (plugin cũng phải được nạp lúc khởi động). Chỉ một
phía bật thì replication vẫn là async.

Các biến chính (trên source):

| Biến | Mặc định | Ý nghĩa |
|---|---|---|
| `rpl_semi_sync_source_timeout` | 10000 (ms) | Chờ xác nhận tối đa bao lâu. Quá thời gian thì **tự quay về async**. |
| `rpl_semi_sync_source_wait_for_replica_count` | 1 | Cần bao nhiêu replica xác nhận. |
| `rpl_semi_sync_source_wait_point` | `AFTER_SYNC` | Chờ xác nhận ở thời điểm nào (xem dưới). |

**Cạm bẫy lớn nhất: tự quay về async.** Nếu không replica nào xác nhận trong 10 giây (replica chết, mạng
đứt), source không đứng chờ mãi mà chuyển sang async và commit tiếp. Ứng dụng chỉ thấy các commit chậm
đúng 10 giây một lần rồi chạy bình thường. Từ lúc đó, bạn **không còn** đảm bảo RPO = 0 mà không hay biết.
Hãy giám sát biến trạng thái `Rpl_semi_sync_source_status` (ON là đang semi-sync, OFF là đã rơi về
async) và `Rpl_semi_sync_source_no_tx` (số commit không được replica xác nhận):

```sql
SHOW GLOBAL STATUS LIKE 'Rpl_semi_sync_source_status';
```

Khi replica theo kịp trở lại, source tự quay về semi-sync. Có hệ thống đặt timeout rất lớn để "thà dừng
ghi còn hơn mất dữ liệu"; đó là đánh đổi RTO lấy RPO, phải là quyết định có chủ đích.

**Chi phí:** mỗi commit chậm thêm ít nhất một vòng mạng (*round-trip*) đến replica. Trong cùng
datacenter là dưới một mili giây; giữa hai vùng địa lý xa nhau có thể vài chục mili giây cho **mỗi**
commit. Semi-sync hợp với replica ở gần.

#### AFTER_SYNC và AFTER_COMMIT

Biến `rpl_semi_sync_source_wait_point` quyết định source chờ xác nhận **trước hay sau** khi commit vào
InnoDB. Commit của source gồm: (1) ghi binlog và sync xuống đĩa, (2) commit vào storage engine (từ đây
session khác thấy dữ liệu), (3) trả kết quả cho client.

- **`AFTER_SYNC`** (mặc định, còn gọi là *lossless semi-sync*): chờ xác nhận **giữa (1) và (2)**.
- **`AFTER_COMMIT`**: chờ xác nhận **giữa (2) và (3)**.

Khác biệt nằm ở chỗ: với `AFTER_COMMIT`, transaction đã commit trong InnoDB, **các session khác đã đọc
thấy**, trong khi replica có thể chưa nhận. Timeline:

| Thời điểm | Session A (người ghi) | Session B (người đọc khác) | Source | Replica |
|---|---|---|---|---|
| t1 | `COMMIT` đơn #502 | | ghi + sync binlog | |
| t2 | đang chờ | | commit InnoDB (`AFTER_COMMIT`) | chưa nhận |
| t3 | đang chờ | `SELECT` thấy đơn #502, gửi email xác nhận | | chưa nhận |
| t4 | | | **crash** | chưa nhận |
| t5 | nhận lỗi mất kết nối | | | promote lên source |
| t6 | | đơn #502 **không tồn tại** nhưng email đã gửi | | |

Session A không bao giờ nhận "OK" nên không hứa gì với người dùng. Nhưng session B đã **thấy** và hành
động dựa trên dữ liệu mà sau failover biến mất (*phantom read* xuyên failover). Với `AFTER_SYNC`, ở t2
source chưa commit vào InnoDB nên B không thể thấy đơn #502 trước khi replica nhận; mọi client thấy
transaction cùng lúc, sau khi replica đã có nó. Vì vậy `AFTER_SYNC` là mặc định và là lựa chọn đúng
trong gần như mọi trường hợp.

Một hệ quả mà manual nhấn mạnh: sau khi source semi-sync crash và đã failover, **không đưa source cũ
quay lại làm source**, manual nói nên loại bỏ nó. Nó có thể chứa transaction đã ghi binlog (bước 1) mà
chưa replica nào xác nhận, tức là những transaction mà cụm mới không có. Muốn dùng lại máy đó thì dựng
lại nó như một replica mới từ bản sao của cụm hiện tại.

### 4.3 Group Replication (khái niệm)

**Group Replication** (GR) là một cơ chế khác hẳn: một nhóm server (tối đa **9** thành viên) giao tiếp
qua một giao thức đồng thuận (*consensus*, họ hàng của Paxos). Một transaction chỉ commit khi **đa số**
thành viên (*majority*) đã đồng ý về thứ tự của nó.

Quy trình commit trong GR, đơn giản hoá:

1. Transaction chạy trên một thành viên đến lúc commit.
2. Thay đổi (*write set*: các dòng bị đụng) được gửi tới cả nhóm, nhóm thống nhất thứ tự toàn cục.
3. Mỗi thành viên chạy bước **certification**: kiểm tra transaction này có đụng cùng dòng với một
   transaction khác đã được xếp trước mà nó chưa thấy hay không. Có xung đột thì transaction bị
   rollback (người commit trước thắng). Vì mọi thành viên nhận cùng thứ tự và cùng luật, tất cả ra cùng
   kết luận mà không cần hỏi nhau thêm.
4. Thành viên gốc commit và trả kết quả; các thành viên khác áp dụng transaction một cách bất đồng bộ.

Hai chế độ:

- **Single-primary** (mặc định, `group_replication_single_primary_mode = ON`): chỉ một thành viên nhận
  ghi, các thành viên khác `super_read_only`. Primary chết thì nhóm **tự bầu** primary mới.
- **Multi-primary**: mọi thành viên nhận ghi. Ghi đồng thời cùng dòng ở hai nơi sẽ có transaction bị
  rollback ở bước certification, nên ứng dụng phải chịu được lỗi này. Ít dùng hơn.

Điều GR đem lại so với async/semi-sync:

- **Không mất transaction đã commit** khi một thành viên chết, vì đa số đã có nó.
- **Failover tự động** có sẵn, không cần công cụ ngoài để bầu primary.
- **Bảo vệ khỏi split brain bằng quorum** (mục 7.3): phần mạng chỉ còn thiểu số thành viên không commit
  được gì.

Cái giá: nhóm 3 thành viên chịu được 1 thành viên chết, nhóm 5 chịu được 2 (đa số của 3 là 2, của 5 là
3). Mất đa số thì cả nhóm dừng ghi. Mọi commit phải đi một vòng đồng thuận; transaction rất lớn bị
giới hạn kích thước; mọi bảng phải là InnoDB và có primary key; GTID phải bật.

**Đọc dữ liệu cũ trên thành viên phụ.** Thành viên phụ áp dụng transaction bất đồng bộ, nên đọc từ đó
vẫn có thể thấy dữ liệu cũ, giống replica thường. Biến `group_replication_consistency` (mặc định
`BEFORE_ON_PRIMARY_FAILOVER`) điều chỉnh mức đảm bảo; các giá trị mạnh hơn như `BEFORE`, `AFTER` cho
đọc nhất quán đổi lại độ trễ cao hơn.

Trong thực tế bạn ít khi tự cấu hình GR bằng tay mà dùng **InnoDB Cluster** (mục 8.1), vốn dựng GR bên
dưới.

### 4.4 So sánh

| | Async | Semi-sync `AFTER_SYNC` | Group Replication |
|---|---|---|---|
| Commit chờ gì | Không chờ ai | Ít nhất N replica nhận (ghi relay log) | Đa số thành viên đồng thuận |
| Mất dữ liệu khi source chết | Có thể | Không, trừ khi đã rơi về async | Không, khi còn đa số |
| Độ trễ commit thêm | 0 | 1 round-trip | 1 vòng đồng thuận |
| Replica ở xa | Tốt | Kém (chậm mọi commit) | Kém |
| Failover tự động | Cần công cụ ngoài | Cần công cụ ngoài | Có sẵn |
| Replica đọc có thể cũ | Có | Có (nhận chưa phải đã áp dụng) | Có (tuỳ `group_replication_consistency`) |

Dòng cuối là điểm hay bị hiểu sai: **semi-sync không làm replica "luôn mới"**. Nó chỉ đảm bảo dữ liệu
đã nằm trong relay log của replica, applier vẫn có thể đang tụt lại phía sau.

## 5. Replication lag

### 5.1 Lag là gì, vì sao có

**Replication lag** là khoảng thời gian từ lúc transaction commit trên source đến lúc nó được áp dụng
trên replica. Lag luôn lớn hơn 0 (ít nhất là thời gian mạng và thời gian áp dụng), thường vài mili giây.
Vấn đề là khi nó lên đến vài giây, vài phút hay vài giờ.

Nguyên nhân thường gặp:

1. **Transaction lớn.** Source mất 5 phút cho một `UPDATE` 10 triệu dòng; replica cũng sẽ mất cỡ đó
   **sau khi** nhận xong, và trong lúc áp dụng nó, các transaction phía sau phải chờ. Thêm vào đó, với
   ROW format, một transaction lớn tạo binlog lớn phải truyền qua mạng.
2. **DDL dài.** Một `ALTER TABLE` mất 1 giờ trên source sẽ chạy lại 1 giờ trên replica, và (với cách
   áp dụng có thứ tự) replica trễ ít nhất 1 giờ. Đây là lý do gh-ost/pt-online-schema-change có tuỳ
   chọn điều tốc theo lag (Chương 20, mục 4 và 6.3).
3. **Bảng không có primary key** với ROW format (mục 2.5).
4. **Replica yếu hơn source** hoặc đang bận phục vụ truy vấn đọc nặng, backup.
5. **Song song hoá kém.** Source có 200 session ghi song song, replica chỉ có vài worker, hoặc tải
   ghi dồn vào cùng vài dòng nóng nên không chạy song song được.
6. **Mạng chậm** giữa hai vùng địa lý.

### 5.2 Seconds_Behind_Source và vì sao không nên tin hoàn toàn

Cột `Seconds_Behind_Source` của `SHOW REPLICA STATUS` là chỉ số lag đầu tiên mọi người nhìn. Cách nó
được tính: khi applier đang xử lý một event, giá trị bằng **thời gian hiện tại trên replica trừ timestamp
ghi trong event lúc commit trên source** (MySQL bù độ lệch đồng hồ đo được khi receiver khởi động).
Khi applier không có gì để làm, giá trị là 0.

Những trường hợp nó đánh lừa bạn:

- **Nó đo khoảng cách giữa applier và receiver, không phải giữa applier và source.** Nếu mạng chậm và
  receiver tụt lại phía sau source, applier áp dụng hết những gì receiver kéo về rồi ngồi chờ, nên giá
  trị là **0** dù replica đang thiếu nhiều phút dữ liệu. Manual nói rõ cột này chỉ có ích trên mạng nhanh.
- **NULL** nghĩa là "không biết": applier không chạy, hoặc applier đã hết relay log và receiver không
  chạy. NULL **không** phải là 0. Hệ thống giám sát coi NULL là ổn là một lỗi kinh điển.
- **Nhảy vọt với transaction lớn:** đang 0, bắt đầu áp dụng một transaction đã commit 5 phút trước thì
  lập tức thành 300, rồi về 0 khi xong. Nó không cho biết còn bao lâu nữa mới xong.
- **Lệch đồng hồ** (NTP chỉnh giờ sau khi receiver đã khởi động) làm số sai.
- Với multi-threaded applier, giá trị dựa trên vị trí đã áp dụng xong liên tục, nên có thể không phản
  ánh transaction mới nhất mà worker nào đó đã commit.

### 5.3 Đo lag bằng performance_schema

Từ 8.0, mỗi transaction mang theo hai timestamp: *original commit timestamp* (lúc commit trên source
gốc) và *immediate commit timestamp* (lúc commit trên server ngay phía trên). `performance_schema` cho
biết các mốc thời gian của từng giai đoạn:

```sql
-- Trên replica: transaction gần nhất mà mỗi worker đã áp dụng xong,
-- và mất bao lâu từ lúc commit trên source đến lúc áp dụng xong
SELECT WORKER_ID,
       LAST_APPLIED_TRANSACTION,
       TIMESTAMPDIFF(MICROSECOND,
           LAST_APPLIED_TRANSACTION_ORIGINAL_COMMIT_TIMESTAMP,
           LAST_APPLIED_TRANSACTION_END_APPLY_TIMESTAMP) / 1000000 AS lag_giay
FROM performance_schema.replication_applier_status_by_worker;
```

```
+-----------+---------------------------------------------+----------+
| WORKER_ID | LAST_APPLIED_TRANSACTION                    | lag_giay |
+-----------+---------------------------------------------+----------+
|         1 | 5a1c...e0f1:10234                           |   0.0042 |
|         2 | 5a1c...e0f1:10233                           |   0.0039 |
|         3 | 5a1c...e0f1:10231                           |   0.0051 |
|         4 | 5a1c...e0f1:10235                           |   0.0040 |
+-----------+---------------------------------------------+----------+
```

(output minh hoạ)

Con số này là "lag của transaction gần nhất đã áp dụng", không phải "bây giờ replica cũ bao nhiêu". Nếu
replica đang kẹt ở một transaction lớn, xem thêm các cột `APPLYING_TRANSACTION_*` (transaction đang áp
dụng và thời điểm bắt đầu). Tương tự, `replication_connection_status` có
`LAST_QUEUED_TRANSACTION_*` cho giai đoạn receiver nhận về relay log; so sánh hai giai đoạn giúp biết lag
nằm ở mạng (receiver) hay ở áp dụng (applier).

### 5.4 Bảng heartbeat: đo lag từ đầu đến cuối

Cách đo đáng tin nhất là tự tạo "nhịp tim": một tiến trình ghi thời gian hiện tại vào source mỗi giây,
và trên replica so sánh giá trị đó với đồng hồ hiện tại.

```sql
-- Trên source
CREATE TABLE ops.heartbeat (
  id INT PRIMARY KEY,
  ts TIMESTAMP(6) NOT NULL
);
INSERT INTO ops.heartbeat VALUES (1, NOW(6));

-- Một job chạy mỗi giây trên source:
UPDATE ops.heartbeat SET ts = NOW(6) WHERE id = 1;

-- Trên replica:
SELECT TIMESTAMPDIFF(MICROSECOND, ts, NOW(6)) / 1000000 AS lag_giay
FROM ops.heartbeat WHERE id = 1;
```

Giá trị đọc được trên replica đo đúng thứ bạn quan tâm: "dữ liệu trên replica cũ bao nhiêu giây so với
source", bao gồm cả mạng, relay log, applier. Nếu replica kẹt hoàn toàn, con số cứ tăng dần thay vì về
0 hay NULL. Sai số khoảng 1 giây do chu kỳ ghi, và cần đồng hồ hai máy đồng bộ (NTP). Công cụ
`pt-heartbeat` của Percona Toolkit làm đúng việc này. Lưu ý `NOW(6)` trong `UPDATE` được ghi vào binlog
dạng ROW là giá trị cụ thể, nên replica nhận đúng timestamp của source.

### 5.5 Giảm lag

- Chia transaction lớn thành batch nhỏ (Chương 20, mục 6), điều tốc theo lag.
- Mọi bảng có primary key.
- Đủ `replica_parallel_workers` cho tải ghi; replica phần cứng không yếu hơn source.
- Không chạy truy vấn đọc quá nặng trên replica dùng cho failover; tách replica báo cáo riêng.
- Đổi schema bảng lớn bằng công cụ online có điều tốc.

## 6. Read replica và read-your-writes

### 6.1 Chia đọc ghi

Mô hình phổ biến: mọi câu ghi đi vào source, câu đọc chia ra các replica. Với ứng dụng 90% đọc, thêm
replica gần như tăng tuyến tính khả năng đọc.

Cái giá: **đọc từ replica là đọc dữ liệu có thể cũ** (*stale read*). Đa số trang (danh sách sản phẩm,
bài viết) chấp nhận được dữ liệu cũ vài trăm mili giây. Nhưng có một tình huống người dùng thấy ngay.

### 6.2 Vấn đề read-your-writes

| Thời điểm | Người dùng | Ứng dụng | Source | Replica |
|---|---|---|---|---|
| t1 | bấm "Lưu" tên mới "Lan" | `UPDATE users SET name='Lan'` → source | name = Lan | name = Mai |
| t2 | trang chuyển hướng về hồ sơ | `SELECT name` → replica | | name = Mai (lag) |
| t3 | thấy **"Mai"**, nghĩ lưu thất bại, bấm lưu lại | | | |
| t4 | | | | name = Lan |

**Read-your-writes consistency** (đọc được thứ mình vừa ghi) là đảm bảo rằng sau khi một người ghi,
**chính người đó** đọc lại sẽ thấy giá trị mới. Người khác thấy chậm một chút thì thường không sao.

### 6.3 Các cách giải

1. **Đọc từ source ngay sau khi ghi.** Đơn giản nhất. Trong cùng request: sau khi ghi thì mọi lần đọc
   tiếp đi vào source (Laravel `sticky`, mục 9.3). Qua các request: ghi nhớ trong session "user này vừa
   ghi lúc T", trong vài giây sau T thì đọc từ source.
2. **Đọc các dữ liệu "của tôi" từ source.** Trang hồ sơ, giỏ hàng, lịch sử đơn của chính người dùng đọc
   từ source; trang công khai đọc từ replica.
3. **Chờ replica theo kịp bằng GTID.** Sau khi ghi, lấy GTID của transaction vừa commit; trước khi đọc
   từ replica, bảo replica chờ đến khi đã áp dụng GTID đó:

   ```sql
   -- Trên source, sau COMMIT: lấy GTID của transaction vừa xong.
   -- Cách 1: bật session_track_gtids = OWN_GTID để server trả GTID về
   --         cùng gói OK (driver phải hỗ trợ đọc).
   -- Cách 2: đọc @@GLOBAL.gtid_executed (tập GTID đã thực thi, gồm cả
   --         transaction vừa commit).
   SELECT @@GLOBAL.gtid_executed;

   -- Trên replica, trước khi đọc: chờ tối đa 1 giây
   SELECT WAIT_FOR_EXECUTED_GTID_SET('5a1c...e0f1:1-10240', 1);
   -- 0: đã áp dụng xong, đọc an toàn; 1: hết thời gian chờ
   ```

   Hết thời gian chờ thì ứng dụng chuyển sang đọc source. Cách này chính xác nhất nhưng phức tạp, ít khi
   tự làm tay. Một số proxy (ví dụ ProxySQL) có tính năng dựa trên ý tưởng này.
4. **Cập nhật giao diện từ dữ liệu vừa ghi**, không đọc lại từ database. Ví dụ API trả luôn đối tượng
   sau khi cập nhật.

### 6.4 Monotonic read

Một vấn đề họ hàng: nếu mỗi request chọn ngẫu nhiên một replica, người dùng có thể thấy bình luận mới ở
lần tải trang thứ nhất (replica A đã theo kịp) rồi lần thứ hai bình luận biến mất (replica B đang lag).
Dữ liệu "đi lùi". Cách giải: gắn một người dùng với một replica cố định (theo hash của user id), hoặc
dùng cách chờ GTID ở trên.

### 6.5 Transaction và replica

Một transaction chỉ nên chạy trên **một** server. Nếu ứng dụng mở transaction, ghi vào source, rồi đọc
trong cùng transaction lại đi sang replica, phần đọc không thấy phần ghi chưa commit, và mọi đảm bảo
isolation (Chương 14) mất ý nghĩa. Các framework đúng đắn (Laravel cũng vậy) dùng kết nối ghi cho mọi
câu trong transaction.

## 7. Failover

### 7.1 Failover là gì

**Failover** là đưa một replica lên làm source mới khi source hỏng. Phân biệt với **switchover** (chuyển
có kế hoạch, ví dụ để bảo trì source): switchover cho phép dừng ghi một cách gọn gàng, chờ replica theo
kịp hoàn toàn rồi mới đổi, nên không mất dữ liệu.

Các bước của một failover (dù làm tay hay công cụ làm):

1. **Phát hiện** source hỏng. Khó hơn tưởng: source không trả lời ping có thể chỉ là mạng giữa công cụ
   giám sát và source bị đứt, source vẫn sống và vẫn nhận ghi từ ứng dụng.
2. **Chọn** replica tốt nhất: replica có nhiều dữ liệu nhất (tập GTID lớn nhất), không có errant
   transaction, cấu hình phù hợp.
3. **Cho replica đó áp dụng hết** relay log đã nhận.
4. **Promote:** dừng replication trên nó, tắt `super_read_only`/`read_only`.

   ```sql
   STOP REPLICA;
   RESET REPLICA ALL;         -- xoá cấu hình kết nối tới source cũ
   SET GLOBAL super_read_only = OFF;
   SET GLOBAL read_only = OFF;
   ```

5. **Trỏ các replica còn lại** sang source mới. Với GTID, chỉ cần:

   ```sql
   STOP REPLICA;
   CHANGE REPLICATION SOURCE TO SOURCE_HOST = 'db-new-source', SOURCE_PORT = 3306,
     SOURCE_AUTO_POSITION = 1;
   START REPLICA;
   ```

6. **Chuyển ứng dụng** sang source mới: đổi DNS, đổi địa chỉ IP ảo (VIP), cập nhật cấu hình proxy.
7. **Xử lý source cũ** khi nó sống lại: không cho nó nhận ghi, dựng lại làm replica.

Lưu ý: `RESET REPLICA ALL` trên 8.4; `RESET SLAVE ALL` của tài liệu cũ là lỗi cú pháp.

### 7.2 Split brain

**Split brain** (não chia đôi) là tình huống **hai server cùng nghĩ mình là source và cùng nhận ghi**.

| Thời điểm | Ứng dụng nhóm 1 | Source cũ A | Công cụ failover | Replica B |
|---|---|---|---|---|
| t1 | | mạng giữa A và công cụ/B bị đứt | thấy A "chết" | |
| t2 | vẫn kết nối tới A, đặt hàng, trừ kho | **vẫn sống**, nhận ghi | promote B | lên làm source |
| t3 | | nhận ghi | | ứng dụng nhóm 2 ghi vào B |
| t4 | mạng phục hồi: A và B có hai lịch sử khác nhau | | | |

Hai bên đều có transaction mà bên kia không có, có thể cùng cấp một `id` auto-increment cho hai đơn hàng
khác nhau, cùng bán món hàng cuối cùng trong kho. Không có cách tự động nào gộp lại cho đúng; phải đối
soát bằng tay. Split brain thường tệ hơn nhiều so với vài phút downtime.

### 7.3 Phòng split brain: quorum và fencing

1. **Quorum.** Chỉ cho phép một bên hoạt động khi nó nhìn thấy **đa số** các thành viên. Mạng chia đôi
   thì tối đa một bên có đa số. Đây là cách Group Replication làm: phần thiểu số không commit được. Vì
   vậy cụm nên có số lẻ thành viên (3, 5): cụm 2 thành viên chia đôi thì không bên nào có đa số. Công cụ
   giám sát cũng nên chạy từ nhiều vị trí và cần đồng thuận trước khi kết luận source chết.
2. **Fencing** (rào lại). Trước khi (hoặc ngay khi) promote source mới, **chủ động đảm bảo source cũ
   không thể nhận ghi nữa**, dù nó còn sống hay không:
   - Đặt `super_read_only = ON` trên source cũ nếu còn kết nối được.
   - Thu hồi địa chỉ IP ảo khỏi máy source cũ, hoặc cập nhật proxy để không gửi ghi tới nó nữa.
   - Mạnh nhất: tắt hẳn máy source cũ qua API của cloud hay quản lý nguồn điện (kỹ thuật được gọi vui là
     STONITH, *shoot the other node in the head*).
3. **Source tự rào.** Source mất liên lạc với đa số thì tự chuyển read-only (GR làm điều này với thành
   viên thiểu số).

Nguyên tắc: không bao giờ được có hai server ghi được cùng lúc. Nếu phải chọn giữa "có thể có hai source"
và "có thể không có source nào trong vài phút", hệ thống tiền bạc nên chọn vế sau.

### 7.4 Mất dữ liệu khi failover async

Với async, replica được promote có thể thiếu vài transaction cuối của source cũ (mục 4.1). Khi source cũ
sống lại, những transaction đó vẫn nằm trong binlog của nó. Có thể trích ra bằng `mysqlbinlog` (dựa trên
GTID mà cụm mới không có) để xem xét áp dụng lại bằng tay; nhưng có thể chúng đã xung đột với ghi mới
trên source mới. Đây là lý do hệ thống cần RPO = 0 dùng semi-sync `AFTER_SYNC` hoặc GR.

## 8. Công cụ

Không ai nên làm failover tay lúc 3 giờ sáng. Các công cụ dưới đây tự động hoá phát hiện, chọn, promote
và chuyển hướng ứng dụng.

### 8.1 InnoDB Cluster và MySQL Router

**InnoDB Cluster** là giải pháp HA chính thức của MySQL, gồm ba phần:

- **Group Replication** làm nền (thường 3 thành viên, single-primary).
- **MySQL Shell** (`mysqlsh`) với AdminAPI để dựng và quản lý cụm bằng vài lệnh
  (`dba.createCluster()`, `cluster.addInstance()`, `cluster.status()`...).
- **MySQL Router**: một proxy nhẹ đặt cạnh ứng dụng. Router đọc metadata của cụm và biết ai là primary.
  Theo mặc định khi bootstrap, cổng **6446** dành cho kết nối đọc-ghi (luôn tới primary) và **6447** cho
  kết nối chỉ đọc (chia cho các thành viên phụ); 6448/6449 là các cổng tương ứng cho X Protocol.
  Primary đổi thì Router tự chuyển kết nối mới sang primary mới; ứng dụng chỉ cần biết địa chỉ Router.

Ngoài ra còn **InnoDB ReplicaSet** (async replication thường được quản lý bằng MySQL Shell, failover thủ
công qua một lệnh) và **InnoDB ClusterSet** (nhiều InnoDB Cluster ở nhiều vùng, nối với nhau bằng async
replication để dự phòng thảm hoạ).

### 8.2 Orchestrator

**Orchestrator** là công cụ mã nguồn mở (do Shlomi Noach viết, từng được dùng ở GitHub) quản lý topology async/
semi-sync replication: tự khám phá topology, vẽ sơ đồ, phát hiện source chết (dựa trên việc **cả các
replica** cũng mất kết nối tới source, giảm báo động giả), chọn replica tốt nhất, sắp xếp lại topology,
gọi hook để bạn tự thực hiện fencing và đổi DNS/proxy. Có chế độ chạy nhiều node với đồng thuận Raft để
bản thân công cụ không là điểm hỏng duy nhất. Lưu ý: repo gốc `openark/orchestrator` đã được
**archive** (đầu năm 2025, không còn bảo trì); README của nó hướng người dùng sang bản fork của Percona
(`percona/orchestrator`). Trước khi chọn, hãy kiểm tra tình trạng bảo trì của bản fork. Công cụ cũ hơn cùng loại: MHA. Thường đi kèm proxy như **ProxySQL** hoặc HAProxy để định
tuyến đọc/ghi.

### 8.3 Dịch vụ managed: RDS và Aurora

Trên cloud, nhà cung cấp lo phần lớn những việc trên:

- **Amazon RDS for MySQL Multi-AZ**: một bản standby ở vùng sẵn sàng (*Availability Zone*) khác, dữ liệu
  được sao chép **đồng bộ** sang standby; standby này không phục vụ đọc (với kiểu triển khai Multi-AZ
  một standby). Khi primary hỏng, RDS tự failover và **đổi bản ghi DNS** của endpoint sang máy mới.
  Read replica của RDS là một tính năng riêng, dùng async replication của MySQL.
- **Amazon Aurora MySQL**: kiến trúc khác hẳn. Các instance dùng chung một tầng lưu trữ phân tán (dữ liệu
  được giữ nhiều bản sao trải trên 3 Availability Zone), replica đọc cùng dữ liệu đó thay vì phát lại binlog, nên lag
  thường rất thấp. Một cluster có tối đa 15 Aurora Replica; failover đưa một replica lên làm writer. Aurora
  cung cấp *cluster endpoint* (luôn trỏ writer) và *reader endpoint* (chia đọc cho các replica).

Điểm chung cần biết khi dùng managed: failover **đổi DNS**, nên ứng dụng phải không cache DNS quá lâu
và phải kết nối lại (mục 9). Một sự cố quen thuộc là sau failover, kết nối cũ trong pool vẫn trỏ tới
máy cũ, giờ đã thành replica read-only, và mọi câu ghi lỗi "running with the --read-only option".

## 9. Ứng dụng chịu failover thế nào

Dù công cụ tốt đến đâu, trong lúc failover luôn có một khoảng (vài giây đến vài chục giây) ứng dụng
không ghi được. Ứng dụng viết đúng thì người dùng chỉ thấy chậm một chút; viết sai thì lỗi kéo dài đến
khi có người restart server ứng dụng.

### 9.1 Những lỗi ứng dụng sẽ thấy

- Kết nối bị đóng giữa chừng: "MySQL server has gone away", "Lost connection to MySQL server during
  query".
- Không kết nối được: "Connection refused", timeout.
- Kết nối được nhưng vào nhầm máy cũ, nay đã read-only: lỗi 1290 "...running with the --read-only option
  so it cannot execute this statement" (hoặc `--super-read-only`).
- Transaction đang chạy dở bị mất: bạn **không biết** nó đã commit hay chưa nếu lỗi xảy ra đúng lúc
  `COMMIT`.

### 9.2 Retry và reconnect đúng cách

1. **Reconnect:** khi gặp lỗi mất kết nối, bỏ kết nối cũ, mở kết nối mới (lúc đó DNS/Router đã trỏ tới
   source mới). Connection pool phải loại kết nối hỏng thay vì trả lại cho request sau.
2. **Retry ở mức transaction, không phải mức câu lệnh.** Nếu kết nối mất giữa transaction, mọi câu trước
   đó trong transaction đã bị rollback. Chạy lại riêng câu bị lỗi trên kết nối mới là sai (nửa transaction).
   Phải chạy lại **cả transaction** từ đầu.
3. **Chỉ retry thao tác idempotent hoặc đã kiểm tra.** Lỗi đúng lúc `COMMIT` thì transaction có thể đã
   commit. Retry một câu "trừ 100.000đ khỏi tài khoản" có thể trừ hai lần. Cách an toàn: dùng khoá
   idempotency (một `request_id` có ràng buộc `UNIQUE`, Chương 19), hoặc kiểm tra trạng thái trước khi
   chạy lại.
4. **Backoff:** chờ tăng dần giữa các lần thử (ví dụ 100 ms, 200 ms, 400 ms...) có giới hạn số lần, để
   hàng nghìn tiến trình không cùng lúc dội vào source mới vừa lên.
5. **DNS TTL ngắn và không cache vĩnh viễn** ở tầng ứng dụng/runtime, để thấy địa chỉ mới.
6. **Timeout kết nối ngắn** để không treo hàng chục giây chờ một máy đã chết.

### 9.3 Laravel: read/write connection và sticky

Laravel hỗ trợ sẵn tách đọc ghi trong `config/database.php`:

```php
'mysql' => [
    'driver' => 'mysql',
    'read' => [
        'host' => [
            env('DB_READ_HOST_1', '10.0.0.11'),
            env('DB_READ_HOST_2', '10.0.0.12'),
        ],
    ],
    'write' => [
        'host' => [
            env('DB_WRITE_HOST', '10.0.0.10'),
        ],
    ],
    'sticky' => true,
    'port' => env('DB_PORT', '3306'),
    'database' => env('DB_DATABASE', 'shop'),
    'username' => env('DB_USERNAME', 'app'),
    'password' => env('DB_PASSWORD', ''),
    // ... các khoá còn lại như cấu hình mysql thông thường
],
```

Cách nó hoạt động:

- Câu `SELECT` dùng kết nối **read**; `INSERT`/`UPDATE`/`DELETE` dùng kết nối **write**. Các khoá khác
  (user, password, database...) dùng chung, chỉ ghi đè những gì đặt trong `read`/`write`.
- Có nhiều host trong mảng thì Laravel chọn **ngẫu nhiên một host cho mỗi request**.
- **`sticky => true`**: nếu trong request hiện tại đã có thao tác ghi, mọi lần đọc tiếp theo **trong
  cùng request** dùng kết nối write. Đây là cách giải read-your-writes số 1 ở mục 6.3, trong phạm vi một
  request.
- Bên trong transaction (`DB::transaction(...)`), mọi câu dùng kết nối write.
- Ép một truy vấn đọc từ write: `DB::table('users')->useWritePdo()->get()`, hoặc cho cả một đoạn code:
  `DB::connection()->usingWritePdo(fn ($c) => ...)` (có trong tài liệu Laravel 13).

`sticky` không giúp qua **request sau**: lưu xong rồi redirect sang trang hồ sơ là một request mới, đọc lại
từ replica, đúng tình huống ở mục 6.2. Laravel 13 có middleware
`Illuminate\Foundation\Http\Middleware\PreventStaleDatabaseReads`: nó ghi vào session thời điểm người
dùng vừa ghi, và trong **2 giây** (mặc định, đổi bằng `PreventStaleDatabaseReads::for(5)`) sau đó các lần
đọc trên kết nối mặc định của người dùng đó đi vào write. Middleware phải chạy sau `StartSession`. Nếu
replica của bạn có lúc lag hơn khoảng thời gian này, người dùng vẫn có thể thấy dữ liệu cũ; chọn con số
dựa trên lag đo được ở mục 5, không đoán.

**Reconnect trong Laravel.** Khi một câu lệnh lỗi và thông điệp lỗi khớp danh sách "mất kết nối" của
Laravel (gồm "server has gone away", "Lost connection", "Connection refused", và cả
"running with the --read-only option so it cannot execute this statement" để bắt trường hợp failover
kiểu Aurora), Laravel tự kết nối lại và **chạy lại câu đó một lần**, nhưng **chỉ khi không ở trong
transaction**. Trong transaction thì exception được ném ra, đúng với nguyên tắc ở mục 9.2: phần retry
transaction là việc của bạn. `DB::transaction($callback, $attempts)` có tham số số lần thử, nhưng nó
chỉ thử lại khi gặp deadlock/lỗi đồng thời (Chương 15), không phải khi mất kết nối.

Với worker chạy lâu (queue worker, Octane), một kết nối đã trỏ tới source cũ có thể tồn tại rất lâu.
Hãy đảm bảo worker được khởi động lại sau failover, hoặc dựa vào cơ chế reconnect ở trên.

### 9.4 Kiểm tra bằng diễn tập

Cách duy nhất biết ứng dụng chịu failover thế nào là **làm thử**: trên môi trường staging, chạy tải giả
lập rồi failover (hoặc switchover) cụm database, quan sát lỗi, thời gian phục hồi, và có transaction nào
bị ghi hai lần hay mất không. Nhiều dịch vụ managed có thao tác "failover" chủ động để diễn tập.

## 10. Đối chiếu PostgreSQL: streaming replication

PostgreSQL 18 nhân bản theo cách khác về bản chất:

| | MySQL | PostgreSQL |
|---|---|---|
| Nhân bản cái gì | Binlog: thay đổi **logic** (dòng/câu lệnh) | WAL: thay đổi **vật lý** (byte trên trang dữ liệu) |
| Tên gọi | source / replica | primary / standby |
| Replica khác phiên bản, khác schema | Được (trong giới hạn) | Không: standby là bản sao từng byte, cùng phiên bản chính |
| Đồng bộ | async; semi-sync (plugin); GR | async; sync qua `synchronous_standby_names` và `synchronous_commit` |
| Theo dõi | `SHOW REPLICA STATUS`, `performance_schema` | `pg_stat_replication` (có sẵn `write_lag`, `flush_lag`, `replay_lag`) |
| Promote | `STOP REPLICA`, tắt read-only | `pg_promote()` hoặc `pg_ctl promote` |
| Giữ log cho replica | `binlog_expire_logs_seconds` | *replication slot* (giữ WAL đến khi standby nhận, cẩn thận đầy đĩa) |

Vài điểm đáng chú ý:

- **Physical streaming replication**: standby nhận luồng WAL từ primary qua kết nối được cấu hình bằng
  `primary_conninfo` và file `standby.signal` trong data directory; `pg_basebackup -R` vừa sao chép dữ
  liệu ban đầu vừa ghi sẵn cấu hình này. Standby phục vụ đọc khi `hot_standby = on` (mặc định).
- **Sync replication** của PostgreSQL chỉnh được theo từng transaction bằng `synchronous_commit`:
  `remote_write`, `on` (standby đã flush WAL, gần giống semi-sync `AFTER_SYNC`), `remote_apply` (standby
  đã **áp dụng**, nghĩa là đọc trên standby sẽ thấy, giải luôn read-your-writes nhưng chậm nhất).
- **Logical replication** (`CREATE PUBLICATION` / `CREATE SUBSCRIPTION`) là cơ chế riêng nhân bản thay
  đổi theo dòng, gần với tinh thần binlog ROW của MySQL, dùng cho nâng cấp phiên bản hoặc nhân bản một
  phần.
- PostgreSQL lõi không có failover tự động; dùng công cụ như Patroni (dựa trên etcd/Consul để có quorum),
  hoặc dịch vụ managed. Các khái niệm split brain, fencing, read-your-writes ở trên áp dụng y nguyên.

## Lỗi thường gặp

1. **Dùng lệnh cũ trên 8.4.** `START SLAVE`, `SHOW SLAVE STATUS`, `CHANGE MASTER TO`, `RESET MASTER`
   đều là lỗi cú pháp. Dùng bảng ở mục 2.2.
2. **Coi replication là backup.** `DELETE` nhầm được nhân bản ngay lập tức.
3. **Ghi vào replica.** Do quên `super_read_only` hoặc ứng dụng cấu hình nhầm host. Kết quả là errant
   transaction, lỗi duplicate key làm applier dừng, dữ liệu lệch âm thầm.
4. **Skip lỗi applier cho "chạy tiếp"** mà không tìm nguyên nhân, che giấu dữ liệu đã lệch.
5. **Tin `Seconds_Behind_Source = 0`** và coi `NULL` là ổn. Dùng bảng heartbeat để đo thật.
6. **Bảng không có primary key** làm replica (ROW format) chậm hàng giờ.
7. **Một transaction khổng lồ** (xoá hàng triệu dòng một lần, `ALTER` dài) làm lag tăng vọt.
8. **Nghĩ semi-sync làm replica luôn mới**, hoặc không giám sát việc semi-sync âm thầm rơi về async sau
   timeout.
9. **Đưa source cũ quay lại làm source** sau failover mà không kiểm tra những transaction chỉ nó có.
10. **Failover không fencing**, dẫn tới split brain.
11. **Đọc từ replica ngay sau khi ghi** mà không có chiến lược read-your-writes.
12. **Retry nửa transaction** sau khi mất kết nối, hoặc retry thao tác không idempotent khi lỗi xảy ra
    đúng lúc `COMMIT`.
13. **Cache DNS hoặc giữ kết nối pool cũ** sau failover, ghi mãi vào máy đã thành read-only.
14. **Binlog hết hạn** trước khi replica tắt lâu kịp bật lại.

## Tóm tắt chương

- Replication giữ bản sao database trên server khác, cập nhật liên tục. Dùng cho HA, mở rộng đọc, tách
  việc nặng. Không thay backup, không mở rộng ghi.
- MySQL replication phát lại binary log: binlog dump thread (source) gửi, receiver thread (replica) ghi
  vào relay log, applier thread(s) áp dụng. Multi-threaded applier mặc định 4 worker, giữ thứ tự commit.
- MySQL 8.4 chỉ còn bộ lệnh `SOURCE`/`REPLICA`: `CHANGE REPLICATION SOURCE TO`, `START REPLICA`,
  `SHOW REPLICA STATUS`, `SHOW BINARY LOG STATUS`, `RESET BINARY LOGS AND GTIDS`.
- `binlog_format = ROW` (mặc định, biến đã deprecated) an toàn hơn STATEMENT; cần primary key ở mọi bảng.
- GTID định danh mỗi transaction toàn hệ thống; `SOURCE_AUTO_POSITION = 1` làm failover đơn giản.
  `gtid_mode` mặc định OFF, cần bật cùng `enforce_gtid_consistency`.
- Async có thể mất transaction đã commit khi failover. Semi-sync chờ ít nhất một replica nhận;
  `AFTER_SYNC` (mặc định) không để client khác thấy dữ liệu chưa sang replica; quá
  `rpl_semi_sync_source_timeout` (10 giây) thì rơi về async. Group Replication dùng đồng thuận đa số,
  tối đa 9 thành viên, failover tự động.
- Lag có nhiều nguyên nhân (transaction lớn, DDL, thiếu primary key, applier không song song đủ).
  `Seconds_Behind_Source` có nhiều điểm mù; `performance_schema` và bảng heartbeat chính xác hơn.
- Đọc từ replica cần chiến lược read-your-writes: sticky, đọc source trong vài giây sau khi ghi, chờ GTID.
- Failover: phát hiện, chọn, promote, trỏ lại, chuyển ứng dụng, rào source cũ. Split brain phòng bằng
  quorum và fencing.
- Ứng dụng: reconnect, retry cả transaction với backoff, idempotency, DNS TTL ngắn. Laravel có
  `read`/`write`/`sticky`, `PreventStaleDatabaseReads`, và tự reconnect một lần ngoài transaction.
- PostgreSQL nhân bản WAL vật lý; `synchronous_commit = remote_apply` cho đọc nhất quán trên standby.

## Câu hỏi tự kiểm tra

1. Vì sao replication không thay thế được backup? Nêu một tình huống cụ thể.
2. Kể tên ba thread tham gia replication và vai trò của từng thread. Vì sao MySQL tách receiver khỏi
   applier?
3. Relay log là gì? Nó khác binlog của source ở điểm nào?
4. Trên MySQL 8.4, lệnh tương ứng với `SHOW MASTER STATUS` và `RESET SLAVE ALL` là gì?
5. Cho một ví dụ câu lệnh cho kết quả khác nhau trên source và replica nếu dùng `binlog_format =
   STATEMENT`. ROW format giải quyết thế nào, và cái giá là gì?
6. Vì sao bảng không có primary key làm replica lag với ROW format?
7. GTID gồm những phần nào? GTID giúp failover dễ hơn toạ độ binlog ra sao?
8. Errant transaction là gì, vì sao nó nguy hiểm khi failover?
9. Semi-sync đảm bảo điều gì và **không** đảm bảo điều gì? "Replica đã nhận" có nghĩa là gì?
10. Mô tả một tình huống mà `AFTER_COMMIT` làm client thấy dữ liệu rồi dữ liệu đó biến mất sau failover,
    còn `AFTER_SYNC` thì không.
11. Chuyện gì xảy ra khi không replica nào xác nhận trong `rpl_semi_sync_source_timeout`? Bạn giám sát
    điều đó bằng gì?
12. Vì sao `Seconds_Behind_Source` có thể bằng 0 trong khi replica đang thiếu dữ liệu vài phút?
    `NULL` nghĩa là gì?
13. Group Replication 5 thành viên chịu được bao nhiêu thành viên chết mà vẫn ghi được? Vì sao nên dùng
    số lẻ?
14. Split brain là gì? Kể hai biện pháp fencing.
15. `sticky => true` trong Laravel giải quyết read-your-writes trong phạm vi nào và không giải quyết
    trường hợp nào?
16. Vì sao không được retry riêng câu lệnh bị lỗi mất kết nối nằm giữa transaction?
17. Streaming replication của PostgreSQL khác binlog replication của MySQL ở điểm cơ bản nào?

## Bài tập

1. **Dựng lab.** Làm theo mục 2.7 với hai instance ở cổng 3307/3308. Sau khi chạy được, tạo một bảng
   có 100.000 dòng trên source, xác nhận số dòng trên replica khớp. Chạy `SHOW PROCESSLIST` trên cả hai
   server và chỉ ra binlog dump thread, receiver thread, coordinator và các worker thread.
2. **Gây lỗi và đọc lỗi.** Trên replica, tạm tắt `super_read_only` rồi `INSERT` một dòng với `id` mà
   source sẽ dùng tiếp theo. Sau đó `INSERT` trên source. Quan sát `Replica_SQL_Running` và
   `Last_SQL_Error`, xem `Executed_Gtid_Set` của replica có UUID lạ nào. Ghi lại cách bạn sẽ xử lý
   đúng (không skip mù). Cuối cùng dựng lại replica cho sạch.
3. **Đo lag.** Tạo bảng heartbeat ở mục 5.4 và một script (shell hoặc PHP) cập nhật mỗi giây. Trên
   source chạy một `UPDATE` chạm toàn bộ bảng 100.000 dòng ở bài 1 (thêm vài cột để nó nặng). Ghi lại
   song song ba con số theo thời gian: `Seconds_Behind_Source`, lag tính từ
   `replication_applier_status_by_worker`, lag theo bảng heartbeat. Giải thích chỗ chúng khác nhau.
4. **Semi-sync.** Bật semi-sync trên lab. Đặt `rpl_semi_sync_source_timeout = 3000`. Dừng replica
   (`STOP REPLICA IO_THREAD`) rồi commit trên source: đo thời gian commit, theo dõi
   `Rpl_semi_sync_source_status` và `Rpl_semi_sync_source_no_tx`. Bật lại receiver và quan sát trạng
   thái quay về.
5. **Thiết kế.** Một ứng dụng thương mại điện tử dùng Laravel, một source và hai replica async. Viết một
   trang mô tả: trang nào đọc replica, trang nào đọc source; cấu hình `read`/`write`/`sticky`; có dùng
   `PreventStaleDatabaseReads` không và với thời gian bao lâu (dựa trên gì); chiến lược retry khi
   failover cho thao tác "đặt hàng" để không tạo đơn trùng.
6. **Failover tay.** Thêm instance thứ ba (cổng 3309) làm replica thứ hai của source 3307. Tắt source
   đột ngột (`kill -9` tiến trình `mysqld` cổng 3307). Promote 3308 theo mục 7.1 và trỏ 3309 sang 3308.
   Liệt kê các bước bạn đã làm để đảm bảo khi 3307 bật lại nó không nhận ghi.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [Replication](https://dev.mysql.com/doc/refman/8.4/en/replication.html),
  [Replication Threads](https://dev.mysql.com/doc/refman/8.4/en/replication-threads.html),
  [Replication with Global Transaction Identifiers](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids.html),
  [Setting Up Replication Using GTIDs](https://dev.mysql.com/doc/refman/8.4/en/replication-gtids-howto.html),
  [CHANGE REPLICATION SOURCE TO](https://dev.mysql.com/doc/refman/8.4/en/change-replication-source-to.html),
  [SHOW REPLICA STATUS](https://dev.mysql.com/doc/refman/8.4/en/show-replica-status.html),
  [Semisynchronous Replication](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html),
  [Configuring Semisynchronous Replication](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync-interface.html),
  [Replica Server Options and Variables](https://dev.mysql.com/doc/refman/8.4/en/replication-options-replica.html),
  [Binary Logging Options and Variables](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html),
  [Switching Sources During Failover](https://dev.mysql.com/doc/refman/8.4/en/replication-solutions-switch.html),
  [Group Replication](https://dev.mysql.com/doc/refman/8.4/en/group-replication.html),
  [What Is New in MySQL 8.4](https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html)
  (danh sách lệnh replication đã bị xoá).
- [MySQL Shell: InnoDB Cluster](https://dev.mysql.com/doc/mysql-shell/8.4/en/mysql-innodb-cluster.html),
  [MySQL Router](https://dev.mysql.com/doc/mysql-router/8.4/en/).
- Laravel 13: [Database: Getting Started, Read and Write Connections](https://laravel.com/docs/13.x/database#read-and-write-connections).
- PostgreSQL 18: [High Availability, Load Balancing, and Replication](https://www.postgresql.org/docs/18/high-availability.html),
  [Streaming Replication](https://www.postgresql.org/docs/18/warm-standby.html#STREAMING-REPLICATION),
  [Synchronous Replication](https://www.postgresql.org/docs/18/warm-standby.html#SYNCHRONOUS-REPLICATION).
- [Orchestrator](https://github.com/openark/orchestrator) (đã archive; fork: [percona/orchestrator](https://github.com/percona/orchestrator)), [ProxySQL](https://proxysql.com/documentation/),
  [pt-heartbeat](https://docs.percona.com/percona-toolkit/pt-heartbeat.html).
- Martin Kleppmann, *Designing Data-Intensive Applications*, chương 5 "Replication" (read-your-writes,
  monotonic reads, split brain).
