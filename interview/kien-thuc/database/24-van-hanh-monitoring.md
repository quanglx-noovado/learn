# Chương 24. Vận hành và giám sát

> [← Mục lục](README.md) · [← Chương 23: Partitioning, sharding và mở rộng](23-partition-sharding-scale.md) · [Chương 25: PostgreSQL: đối chiếu với MySQL →](25-postgres-doi-chieu.md)

**Bạn sẽ học được:**

- Cách đọc và đổi cấu hình MySQL (`SHOW VARIABLES`, `SET GLOBAL`, `SET PERSIST`, file `my.cnf`), và
  vì sao phải biết biến nào đổi được khi đang chạy.
- Năm nhóm cấu hình đáng chỉnh đầu tiên trên một server mới: `innodb_buffer_pool_size`,
  `innodb_dedicated_server`, `max_connections`, `innodb_redo_log_capacity`, slow query log, thời gian
  giữ binlog; cùng giá trị mặc định của MySQL 8.4.
- Các chỉ số sức khoẻ cần theo dõi: QPS, latency, connection và thread đang chạy, buffer pool hit
  ratio, replication lag, lock wait, history list length, dung lượng đĩa; cách tự tính chúng bằng SQL.
- Dùng `performance_schema` và schema `sys` để tìm câu query tốn thời gian nhất và thứ server đang
  chờ nhiều nhất; xem ai đang chạy gì và dừng một câu query bằng `KILL QUERY`.
- Đo dung lượng và tốc độ tăng trưởng của từng bảng.
- Nâng cấp từ MySQL 8.0 (hết extended support tháng 4/2026) lên 8.4 LTS: những thay đổi dễ làm vỡ ứng dụng.
- Một checklist từng bước khi có báo "database chậm".
- Bức tranh chung về công cụ giám sát (PMM, Prometheus với `mysqld_exporter`).

**Cần biết trước:** [Chương 12](12-explain-toi-uu-query.md) (EXPLAIN, slow query log, digest),
[Chương 15](15-lock-deadlock.md) (lock), [Chương 16](16-ben-trong-innodb.md) (buffer pool, redo log,
undo, history list length, binlog), [Chương 19](19-database-tu-ung-dung.md) (connection, pool, timeout).
Chương này **không giảng lại** cơ chế bên trong; khi cần sẽ dẫn link về đúng mục.

Cách chạy thử: các lệnh SQL chạy trên MySQL 8.4. Dựng nhanh bằng Docker (chạy ở terminal máy bạn):

```bash
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
docker exec -it my84 mysql -uroot -proot
```

Nhiều lệnh trong chương đọc biến toàn cục hoặc dữ liệu của mọi connection, nên cần quyền cao
(`PROCESS`, `SYSTEM_VARIABLES_ADMIN`, `CONNECTION_ADMIN`...). Trên máy thử, dùng `root` cho gọn. Trên
production, xem [Chương 18](18-user-quyen-bao-mat.md) để cấp quyền tối thiểu cho tài khoản giám sát.

---

## 1. Vận hành database là việc của ai

### 1.1 Từ "viết được query" tới "giữ cho DB sống"

Các chương trước dạy bạn viết query đúng và nhanh. Nhưng một database trên production còn phải:

- **Được cấu hình hợp với máy**: MySQL cài xong dùng giá trị mặc định rất khiêm tốn (buffer pool
  128 MB) để chạy được cả trên laptop. Trên server 64 GB RAM, để nguyên mặc định là lãng phí.
- **Được quan sát liên tục**: bạn cần biết DB đang "khoẻ" hay "mệt" *trước khi* người dùng phàn nàn.
- **Được xử lý khi có sự cố**: biết nhìn vào đâu, theo thứ tự nào, và can thiệp ra sao mà không làm
  tình hình tệ thêm.
- **Được nâng cấp đúng hạn**: phiên bản hết hỗ trợ không còn bản vá bảo mật.

Ở công ty lớn có DBA hoặc đội SRE lo phần này. Ở công ty nhỏ, hoặc khi dùng dịch vụ managed (Amazon
RDS, Cloud SQL...), backend developer thường là người phải đọc biểu đồ và trả lời câu "vì sao DB
chậm". Phỏng vấn backend vì thế hay hỏi: *"Bạn theo dõi những chỉ số gì của MySQL?"*, *"DB đột nhiên
chậm, bạn làm gì?"*.

### 1.2 Ba loại thông tin

Mọi thứ trong chương xoay quanh ba nguồn thông tin mà MySQL cung cấp:

| Loại | Trả lời câu hỏi | Xem bằng |
|---|---|---|
| **System variable** (biến cấu hình) | Server được *cấu hình* thế nào? | `SHOW VARIABLES`, `performance_schema.global_variables` |
| **Status variable** (biến trạng thái) | Từ lúc khởi động, server đã *làm* bao nhiêu việc? Hiện có bao nhiêu thứ? | `SHOW GLOBAL STATUS`, `performance_schema.global_status` |
| **Instrumentation** (đo đạc chi tiết) | Câu query nào, chờ cái gì, ai đang chạy gì? | `performance_schema`, `sys`, `information_schema` |

Phân biệt hai loại đầu là chỗ người mới hay lẫn: `max_connections` là *variable* (giới hạn bạn đặt),
còn `Threads_connected` là *status* (số connection đang mở thật). Tên status variable trong MySQL
viết hoa chữ cái đầu; system variable viết thường toàn bộ.

---

## 2. Cấu hình: đọc, đổi và lưu lại

### 2.1 Đọc giá trị hiện tại

```sql
-- Một biến
SELECT @@innodb_buffer_pool_size;
SHOW VARIABLES LIKE 'max_connections';

-- Nhiều biến theo mẫu tên
SHOW GLOBAL VARIABLES LIKE 'innodb_redo%';

-- Dạng bảng, lọc bằng SQL như bảng thường
SELECT VARIABLE_NAME, VARIABLE_VALUE
FROM performance_schema.global_variables
WHERE VARIABLE_NAME IN ('max_connections', 'long_query_time', 'slow_query_log');
```

Trên container mới, câu cuối trả về (giá trị mặc định 8.4):

| VARIABLE_NAME | VARIABLE_VALUE |
|---|---|
| long_query_time | 10.000000 |
| max_connections | 151 |
| slow_query_log | OFF |

Biết giá trị đang *có hiệu lực* là chưa đủ; còn phải biết nó **từ đâu ra** (mặc định, file cấu hình,
hay ai đó đã `SET`). Bảng `performance_schema.variables_info` trả lời điều này:

```sql
SELECT VARIABLE_NAME, VARIABLE_SOURCE, VARIABLE_PATH, SET_TIME, SET_USER
FROM performance_schema.variables_info
WHERE VARIABLE_NAME IN ('max_connections', 'innodb_buffer_pool_size');
-- VARIABLE_SOURCE = COMPILED     : đang dùng mặc định biên dịch sẵn
--                   GLOBAL / SERVER / EXPLICIT / EXTRA... : lấy từ file cấu hình
--                   COMMAND_LINE : lấy từ tham số dòng lệnh khi khởi động mysqld
--                   DYNAMIC      : ai đó đã SET lúc server đang chạy
--                   PERSISTED    : lấy từ mysqld-auto.cnf (SET PERSIST)
```

Khi nhận một server lạ, chạy câu trên với `WHERE VARIABLE_SOURCE <> 'COMPILED'` cho bạn danh sách
mọi thứ đã bị đổi khỏi mặc định: điểm khởi đầu rất tốt để hiểu server đó.

### 2.2 Global và session, dynamic và không dynamic

Hai tính chất của mỗi biến, tra trong manual ở mục của biến đó (dòng *Scope* và *Dynamic*):

- **Scope**: *global* (cả server), *session* (riêng một connection), hoặc cả hai. Biến có cả hai scope
  thì giá trị session được **sao chép từ global lúc connection mở**. Đổi global sau đó *không ảnh
  hưởng* các connection đã mở.
- **Dynamic**: đổi được khi server đang chạy (`SET GLOBAL`) hay phải sửa file rồi khởi động lại.

```sql
SET GLOBAL long_query_time = 1;    -- connection MỚI sẽ dùng 1 giây
SELECT @@SESSION.long_query_time;  -- connection hiện tại vẫn là 10.000000
SET SESSION long_query_time = 1;   -- muốn connection hiện tại đổi theo thì set riêng
```

⚠️ Cạm bẫy kinh điển: bật slow log với ngưỡng 1 giây bằng `SET GLOBAL`, rồi thắc mắc vì sao không thấy
query chậm của ứng dụng. Ứng dụng dùng connection pool, các connection đã mở từ trước vẫn giữ
`long_query_time = 10`. Phải chờ pool tạo connection mới (hoặc khởi động lại ứng dụng).

### 2.3 Ba cách đổi và chỗ lưu

| Cách | Có hiệu lực | Còn sau restart? | Ghi chú |
|---|---|---|---|
| `SET GLOBAL x = ...` | Ngay (với biến dynamic) | **Không** | Hay quên: restart xong mất cấu hình |
| `SET PERSIST x = ...` | Ngay, và ghi vào `mysqld-auto.cnf` | Có | File nằm trong data directory, dạng JSON |
| `SET PERSIST_ONLY x = ...` | Chỉ sau restart | Có | Dùng cho biến không dynamic |
| Sửa `my.cnf` (mục `[mysqld]`) | Sau restart | Có | Cách truyền thống, dễ quản lý bằng Git/Ansible |

```sql
SET PERSIST max_connections = 300;
-- Xem những gì đã persist
SELECT * FROM performance_schema.persisted_variables;
-- Bỏ một biến khỏi mysqld-auto.cnf (giá trị đang chạy không đổi)
RESET PERSIST max_connections;
```

Thứ tự đọc khi khởi động: các file option (`my.cnf`...) trước, `mysqld-auto.cnf` sau, nên **giá trị
persist thắng** giá trị trong `my.cnf`. Đây là nguồn của nhiều buổi chiều mất thời gian: sửa `my.cnf`
mà không thấy tác dụng, vì ai đó từng `SET PERSIST` cùng biến.

💡 Lời khuyên thực tế: chọn **một** nguồn sự thật. Nếu cấu hình được quản lý bằng file trong Git, dùng
`SET GLOBAL` để thử nhanh rồi ghi lại vào file; tránh trộn với `SET PERSIST`. Trên dịch vụ managed
(RDS, Cloud SQL) bạn không sửa được file, mà đổi qua *parameter group* hoặc *flags* của nhà cung cấp.

### 2.4 `innodb_buffer_pool_size`: biến quan trọng nhất

**Là gì.** Kích thước vùng RAM InnoDB dùng để cache page dữ liệu và index. Cơ chế (LRU midpoint, dirty
page, flush) đã giảng ở [Chương 16 mục 4](16-ben-trong-innodb.md#4-buffer-pool-bộ-nhớ-đệm-của-innodb).
Ở đây chỉ bàn chuyện **đặt bao nhiêu**.

**Mặc định 8.4:** 134217728 byte (128 MB). Dynamic: có.

**Vì sao quan trọng nhất.** Đọc từ RAM nhanh hơn đọc từ SSD vài bậc độ lớn. Nếu phần dữ liệu "nóng"
(được truy cập thường xuyên) nằm gọn trong buffer pool, phần lớn query không phải chạm đĩa. Nếu không,
mỗi query đều phải chờ I/O.

**Đặt bao nhiêu.**

- Manual MySQL viết: trên server chỉ chạy database, thường đặt tới khoảng 80% RAM. Phần còn lại cho
  hệ điều hành, bộ nhớ theo từng connection (sort buffer, join buffer, bảng tạm), và các cache khác.
- Không cần lớn hơn tổng dữ liệu + index (cộng thêm một ít dư). DB 5 GB trên máy 64 GB thì buffer
  pool 8 GB là đủ.
- Máy dùng chung (app và DB cùng một máy, môi trường dev) phải đặt thấp hơn nhiều.

```sql
-- Tổng dữ liệu + index của các bảng InnoDB, so với buffer pool hiện tại
SELECT ROUND(SUM(DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024) AS data_index_mb,
       @@innodb_buffer_pool_size / 1024 / 1024           AS pool_mb
FROM information_schema.TABLES
WHERE ENGINE = 'InnoDB';
```

**Đổi khi đang chạy.**

```sql
SET GLOBAL innodb_buffer_pool_size = 4 * 1024 * 1024 * 1024;  -- 4 GB
SHOW STATUS LIKE 'Innodb_buffer_pool_resize_status';           -- theo dõi tiến trình
```

InnoDB đổi kích thước theo từng khối `innodb_buffer_pool_chunk_size` (mặc định 128 MB), và tổng phải
là bội của `innodb_buffer_pool_chunk_size × innodb_buffer_pool_instances`; giá trị bạn đặt sẽ được
làm tròn lên cho khớp.

⚠️ **Cạm bẫy.**

- Đặt quá to làm máy hết RAM, hệ điều hành dùng swap hoặc OOM killer giết `mysqld`. Hệ quả tệ hơn
  nhiều so với buffer pool hơi nhỏ. Luôn chừa chỗ cho bộ nhớ theo connection: nhiều connection cùng
  sort lớn có thể ngốn vài GB.
- Trong container, "RAM của máy" là giới hạn của container (memory limit), không phải RAM của host.
- Đặt bằng `SET GLOBAL` rồi quên ghi vào file cấu hình: restart xong quay về 128 MB, DB chậm hẳn mà
  không ai hiểu vì sao.

### 2.5 `innodb_dedicated_server`: để InnoDB tự tính

**Là gì.** Mặc định `OFF`, không dynamic (chỉ đặt lúc khởi động). Khi bật, InnoDB tự tính hai biến
theo tài nguyên của máy. Ở MySQL 8.4 là `innodb_buffer_pool_size` và `innodb_redo_log_capacity`. (Ở
8.0 nó còn tự đặt `innodb_flush_method`; 8.4 bỏ việc này.)

Công thức theo manual 8.4:

| RAM phát hiện được | `innodb_buffer_pool_size` |
|---|---|
| Dưới 1 GB | 128 MB (mặc định) |
| 1 GB tới 4 GB | RAM × 0.5 |
| Trên 4 GB | RAM × 0.75 |

`innodb_redo_log_capacity` = (số logical processor / 2) GB, tối đa 16 GB. Ví dụ máy 8 vCPU, 32 GB RAM:
buffer pool = 32 × 0.75 = 24 GB, redo log capacity = 8 / 2 = 4 GB.

**Khi nào dùng.** Manual chỉ khuyên dùng khi MySQL chạy trên máy (VM, container) **dành riêng**, dùng
được toàn bộ tài nguyên. Không dùng khi MySQL chung máy với ứng dụng khác.

**Chi tiết dễ sai:**

- Nếu bạn đặt tường minh một biến (ví dụ `innodb_buffer_pool_size` trong `my.cnf`), giá trị tường minh
  thắng, kèm một warning lúc khởi động. Các biến khác vẫn được tự tính.
- Việc tự tính chỉ xảy ra lúc khởi động. Sau đó `SET GLOBAL x = DEFAULT` đưa biến về **mặc định ghi
  trong manual**, không phải về giá trị do `innodb_dedicated_server` tính.

### 2.6 `max_connections`

Đã bàn kỹ ở [Chương 19 mục 2.4](19-database-tu-ung-dung.md#24-giới-hạn-số-connection-max_connections)
từ phía ứng dụng. Tóm lại phía vận hành:

- Mặc định **151**, dynamic, khoảng 1 tới 100000.
- Giá trị hiệu lực thực tế còn bị giới hạn bởi `open_files_limit - 810` (theo manual): đặt
  `max_connections = 10000` mà giới hạn file của hệ điều hành thấp thì không đạt được.
- So sánh với `Max_used_connections` (status: số connection đồng thời cao nhất từ lúc khởi động) để
  biết bạn đã từng chạm trần bao giờ chưa:

```sql
SELECT @@max_connections AS gioi_han,
       (SELECT VARIABLE_VALUE FROM performance_schema.global_status
         WHERE VARIABLE_NAME = 'Max_used_connections')      AS cao_nhat,
       (SELECT VARIABLE_VALUE FROM performance_schema.global_status
         WHERE VARIABLE_NAME = 'Connection_errors_max_connections') AS so_lan_tu_choi;
```

⚠️ Tăng `max_connections` là chữa triệu chứng. Nếu connection đầy vì query chậm giữ connection lâu,
cho thêm connection chỉ làm nhiều query cùng tranh CPU, I/O và lock hơn. Xem
[Chương 19 mục 3.3](19-database-tu-ung-dung.md#33-pool-to-hơn-không-nhanh-hơn).

### 2.7 `innodb_redo_log_capacity`

**Là gì.** Tổng dung lượng đĩa dành cho các file redo log. Cơ chế redo và checkpoint ở
[Chương 16 mục 5](16-ben-trong-innodb.md#5-redo-log-write-ahead-log-và-crash-recovery).

**Mặc định 8.4:** 104857600 byte (100 MB). Dynamic: có. Biến này thay thế cặp biến cũ
`innodb_log_file_size` và `innodb_log_files_in_group` (đã deprecated; nếu `innodb_redo_log_capacity`
được đặt thì hai biến cũ bị bỏ qua).

**Vì sao cần chỉnh.** Redo log là một vòng tròn. Khi vòng gần đầy, InnoDB phải flush gấp dirty page
xuống đĩa để dời checkpoint, và lúc đó các câu ghi bị chậm lại. Với hệ thống ghi nhiều, 100 MB đầy
rất nhanh. Redo lớn hơn giúp ghi mượt hơn, đổi lại crash recovery có thể lâu hơn (phải replay nhiều
redo hơn).

**Cách ước lượng.** Một cách làm phổ biến: đo lượng redo sinh ra trong một khoảng thời gian lúc cao
điểm, rồi đặt capacity đủ chứa vài chục phút tới một giờ redo.

```sql
-- LSN tăng theo số byte redo đã sinh. Đo hai lần cách nhau 60 giây.
SELECT VARIABLE_VALUE INTO @lsn1 FROM performance_schema.global_status
 WHERE VARIABLE_NAME = 'Innodb_redo_log_current_lsn';
DO SLEEP(60);
SELECT VARIABLE_VALUE INTO @lsn2 FROM performance_schema.global_status
 WHERE VARIABLE_NAME = 'Innodb_redo_log_current_lsn';
SELECT ROUND((@lsn2 - @lsn1) / 1024 / 1024, 1) AS redo_mb_moi_phut;
```

Nếu ra 50 MB/phút, một giờ là 3000 MB, có thể đặt khoảng 3 tới 4 GB:

```sql
SET PERSIST innodb_redo_log_capacity = 4 * 1024 * 1024 * 1024;
SHOW STATUS LIKE 'Innodb_redo_log_capacity_resized';  -- dung lượng redo thực tế sau khi đổi
```

⚠️ Đây là "quy tắc ngón tay cái", không phải công thức chính thức. Trên máy thử không có tải, kết quả
gần 0 là bình thường.

### 2.8 Slow query log: `slow_query_log`, `long_query_time`

Cách đọc log và phân tích bằng `pt-query-digest` đã ở
[Chương 12 mục 7](12-explain-toi-uu-query.md#7-tìm-query-chậm-trên-server-thật). Phần vận hành:

| Biến | Mặc định 8.4 | Ý nghĩa |
|---|---|---|
| `slow_query_log` | `OFF` | Bật/tắt slow log |
| `long_query_time` | `10` (giây) | Câu chạy lâu hơn ngưỡng này bị ghi. Có phần lẻ tới micro giây |
| `slow_query_log_file` | `host_name-slow.log` trong data directory | Đường dẫn file |
| `log_output` | `FILE` | Ghi vào file, bảng `mysql.slow_log` (`TABLE`), hoặc cả hai |
| `log_queries_not_using_indexes` | `OFF` | Ghi cả câu không dùng index dù nhanh |
| `min_examined_row_limit` | `0` | Bỏ qua câu đọc ít hơn số dòng này |

```sql
SET PERSIST slow_query_log = ON;
SET PERSIST long_query_time = 1;    -- nhớ: chỉ connection mới nhận giá trị mới
```

Bao nhiêu là hợp lý? Ngưỡng 10 giây mặc định quá cao cho ứng dụng web, nơi một request vài trăm mili
giây đã là chậm. Đặt 0.5 tới 1 giây là điểm khởi đầu phổ biến. Đặt `0` ghi **mọi** câu: hữu ích khi
cần phân tích toàn bộ workload trong vài phút, nhưng file phình rất nhanh và tốn I/O; bật xong nhớ tắt.

⚠️ `log_queries_not_using_indexes = ON` trên hệ thống có nhiều bảng nhỏ sẽ làm log ngập câu vô hại
(quét toàn bảng 10 dòng là bình thường). Nếu bật, kèm `log_throttle_queries_not_using_indexes` để giới
hạn số dòng mỗi phút.

### 2.9 Binlog: giữ bao lâu

Binlog (xem [Chương 16 mục 9](16-ben-trong-innodb.md#9-binlog-và-internal-two-phase-commit)) được bật
mặc định từ 8.0 (`log_bin = ON`). Nếu không dọn, nó lấp đầy đĩa.

| Biến | Mặc định 8.4 | Ý nghĩa |
|---|---|---|
| `binlog_expire_logs_seconds` | `2592000` (30 ngày) | File binlog cũ hơn ngần này bị xoá tự động. `0` = không xoá tự động |
| `binlog_expire_logs_auto_purge` | `ON` | Tắt thì không tự xoá, dù đặt thời hạn |
| `max_binlog_size` | `1073741824` (1 GB) | Kích thước để chuyển sang file binlog mới |
| `sync_binlog` | `1` | Fsync binlog mỗi lần commit (độ bền) |

(`expire_logs_days` là biến cũ thời 5.7; không dùng trên 8.4.)

```sql
SHOW BINARY LOGS;                                  -- danh sách file và cột File_size
PURGE BINARY LOGS BEFORE NOW() - INTERVAL 3 DAY;   -- xoá tay các file cũ hơn 3 ngày
```

`SHOW BINARY LOGS` không phải bảng, không `SELECT SUM(...)` trên nó được. Cộng cột `File_size` bằng mắt
hoặc để script giám sát làm.

**Đặt bao lâu?** Cân hai nhu cầu:

- **Point-in-time recovery**: khôi phục = backup gần nhất + replay binlog từ thời điểm backup. Binlog
  phải giữ ít nhất **lâu hơn khoảng cách giữa hai lần backup** (thường thêm dư một chu kỳ).
- **Replica**: replica đang tụt lại (hoặc tạm tắt) cần những binlog nó chưa đọc. Nếu binlog bị xoá
  trước khi replica đọc tới, replica hỏng và phải dựng lại.

⚠️ Xoá file binlog bằng `rm` thay vì `PURGE BINARY LOGS` làm file index của binlog lệch với thực tế.
Luôn dùng lệnh SQL.

### 2.10 Các mặc định InnoDB đã đổi ở 8.4

Nếu bạn quen MySQL 8.0, nhớ rằng 8.4.0 đổi mặc định của nhiều biến InnoDB (manual có bảng đầy đủ ở
mục *What Is New in MySQL 8.4 since MySQL 8.0*). Một số đáng nhớ:

| Biến | 8.4 | 8.0 |
|---|---|---|
| `innodb_adaptive_hash_index` | `OFF` | `ON` |
| `innodb_change_buffering` | `none` | `all` |
| `innodb_io_capacity` | `10000` | `200` |
| `innodb_log_buffer_size` | 64 MB | 16 MB |
| `innodb_flush_method` (Linux) | `O_DIRECT` nếu hỗ trợ, nếu không `fsync` | `fsync` |
| `innodb_buffer_pool_instances` | Tự tính: 1 nếu pool ≤ 1 GB, lớn hơn thì theo kích thước pool và số CPU, trong khoảng 1 tới 64 | 8 (hoặc 1 nếu pool < 1 GB) |
| `innodb_purge_threads` | 1 nếu ≤ 16 logical processor, ngược lại 4 | 4 |

Hệ quả khi nâng cấp: nếu `my.cnf` cũ đặt tường minh các biến này (thường do copy từ blog cũ), server
8.4 vẫn dùng giá trị cũ của bạn chứ không hưởng mặc định mới. Rà lại file cấu hình là một bước của
nâng cấp (mục 7).

### 2.11 Bảng tổng hợp: cấu hình khởi điểm cho server mới

| Biến | Mặc định 8.4 | Hướng chỉnh |
|---|---|---|
| `innodb_buffer_pool_size` | 128 MB | Tới khoảng 80% RAM trên máy riêng; không cần lớn hơn nhiều so với dữ liệu + index |
| `innodb_dedicated_server` | `OFF` | `ON` nếu máy/container chỉ chạy MySQL và không muốn tự tính |
| `max_connections` | 151 | Theo tổng pool của mọi ứng dụng + dự phòng, không "càng to càng tốt" |
| `innodb_redo_log_capacity` | 100 MB | Đủ chứa khoảng một giờ redo lúc cao điểm |
| `slow_query_log` / `long_query_time` | `OFF` / 10 s | `ON` / 0.5 tới 1 s |
| `binlog_expire_logs_seconds` | 30 ngày | Lâu hơn chu kỳ backup, và đủ cho replica tụt lại |

---

## 3. Các chỉ số cần theo dõi

### 3.1 Counter và gauge

Status variable có hai loại, đọc khác nhau:

- **Counter** (bộ đếm cộng dồn): tăng mãi từ lúc khởi động. Ví dụ `Questions`, `Innodb_buffer_pool_reads`,
  `Slow_queries`. Giá trị tuyệt đối gần như vô nghĩa ("server đã chạy 4 tỉ câu"). Thứ cần là **tốc độ
  tăng**: lấy hiệu hai lần đọc chia cho khoảng thời gian.
- **Gauge** (giá trị tức thời): số đo ngay lúc này. Ví dụ `Threads_connected`, `Threads_running`,
  `Innodb_row_lock_current_waits`. Đọc thẳng được.

Counter về 0 khi server restart. Hệ thống giám sát (mục 9) tự xử lý chuyện này; khi tính tay, nhớ
kiểm `Uptime` để chắc không có restart giữa hai lần đọc.

### 3.2 Thông lượng: QPS

**Là gì.** *Queries per second*: số câu lệnh server nhận mỗi giây. Dùng counter `Questions` (câu do
client gửi; không đếm câu bên trong stored procedure). Counter `Queries` thì đếm cả câu bên trong
stored program.

```sql
SELECT VARIABLE_VALUE INTO @q1 FROM performance_schema.global_status
 WHERE VARIABLE_NAME = 'Questions';
DO SLEEP(10);
SELECT VARIABLE_VALUE INTO @q2 FROM performance_schema.global_status
 WHERE VARIABLE_NAME = 'Questions';
SELECT (@q2 - @q1) / 10 AS qps;
```

Ví dụ tính tay: lần đầu đọc được 1.000.000, mười giây sau 1.015.000. QPS = 15.000 / 10 = 1.500. (Trên
máy thử không có tải, kết quả chỉ khoảng 0.x tới vài câu/giây: chính các câu `SELECT` đo cũng được
đếm.)

Muốn biết tỉ lệ đọc/ghi, dùng các counter `Com_select`, `Com_insert`, `Com_update`, `Com_delete`
theo cùng cách.

**Đọc thế nào.** QPS tự nó không tốt cũng không xấu. Thứ đáng chú ý là **thay đổi đột ngột** so với
cùng giờ hôm trước: QPS tăng gấp đôi lúc nửa đêm có thể là một vòng lặp lỗi trong job, hoặc bot.

### 3.3 Độ trễ: latency

**Là gì.** Thời gian một câu query chạy. Đây là thứ người dùng cảm nhận, quan trọng hơn QPS.

**Vì sao phải nhìn percentile, không nhìn trung bình.** Giả sử 100 câu: 99 câu mất 2 ms, 1 câu mất
2000 ms. Trung bình = (99 × 2 + 2000) / 100 = 21.98 ms, nghe ổn. Nhưng 1% người dùng chờ 2 giây. Vì
thế người ta theo dõi *p95*, *p99*: mức mà 95%, 99% số câu nhanh hơn.

MySQL không có một con số "latency của server". Nguồn tốt nhất là bảng digest của performance_schema,
có sẵn cột percentile theo từng mẫu câu (digest đã giới thiệu ở
[Chương 12 mục 7.2](12-explain-toi-uu-query.md#72-performance_schema-thống-kê-theo-digest)):

```sql
SELECT LEFT(DIGEST_TEXT, 60)                   AS mau_cau,
       COUNT_STAR                              AS so_lan,
       FORMAT_PICO_TIME(AVG_TIMER_WAIT)        AS trung_binh,
       FORMAT_PICO_TIME(QUANTILE_95)           AS p95,
       FORMAT_PICO_TIME(QUANTILE_99)           AS p99
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME IS NOT NULL
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 5;
```

Thời gian trong performance_schema tính bằng **picosecond** (10⁻¹² giây). `FORMAT_PICO_TIME()` đổi
sang dạng dễ đọc (`1.25 ms`). Manual ghi rõ các cột `QUANTILE_*` là ước lượng *cao* tính từ histogram,
không phải giá trị chính xác.

⚠️ Bảng digest cộng dồn từ lúc khởi động (hoặc từ lần `TRUNCATE` gần nhất). Một câu chậm *hôm nay*
có thể bị pha loãng bởi hàng tháng chạy nhanh trước đó. Hệ thống giám sát chụp bảng này định kỳ và
tính chênh lệch; khi điều tra bằng tay, có thể `TRUNCATE TABLE
performance_schema.events_statements_summary_by_digest;` rồi đợi vài phút để có số liệu "tươi" (mất
lịch sử cũ, nên cân nhắc trên production).

Latency đo ở phía ứng dụng (thời gian từ lúc gửi tới lúc nhận đủ kết quả) còn gồm cả mạng và thời gian
chờ connection từ pool. Hai số đo bổ sung nhau: DB nói "tôi chạy câu này 5 ms", app nói "tôi chờ 800
ms" thì vấn đề nằm ngoài DB (pool cạn, mạng).

### 3.4 Connection và thread đang chạy

| Status | Loại | Ý nghĩa |
|---|---|---|
| `Threads_connected` | gauge | Số connection đang mở |
| `Threads_running` | gauge | Số thread **không ngủ**, tức đang thực sự làm việc |
| `Max_used_connections` | gauge (đỉnh) | Số connection đồng thời cao nhất từ lúc khởi động |
| `Aborted_connects` | counter | Số lần kết nối thất bại (sai mật khẩu, timeout bắt tay...) |
| `Connection_errors_max_connections` | counter | Số lần từ chối vì chạm `max_connections` |

```sql
SELECT VARIABLE_NAME, VARIABLE_VALUE
FROM performance_schema.global_status
WHERE VARIABLE_NAME IN ('Threads_connected', 'Threads_running',
                        'Max_used_connections', 'Aborted_connects',
                        'Connection_errors_max_connections', 'Uptime');
```

**`Threads_running` là chỉ số "độ căng" tốt nhất.** 500 connection mở mà phần lớn đang `Sleep` (chờ
ứng dụng gửi câu tiếp) là bình thường với pool. Nhưng `Threads_running` vượt xa số CPU core nghĩa là
các câu đang xếp hàng tranh nhau CPU, I/O hoặc lock; latency sẽ tăng theo. Khi DB "treo", con số này
thường vọt lên hàng trăm.

### 3.5 Buffer pool hit ratio

**Là gì.** Tỉ lệ yêu cầu đọc page được phục vụ từ RAM. Hai counter:

- `Innodb_buffer_pool_read_requests`: số yêu cầu đọc logic (đọc từ buffer pool).
- `Innodb_buffer_pool_reads`: số yêu cầu **không** có sẵn trong buffer pool, phải đọc từ đĩa.

```
hit ratio = 1 - Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests
```

```sql
SELECT ROUND(100 * (1 - r.v / q.v), 3) AS hit_ratio_pct
FROM (SELECT VARIABLE_VALUE AS v FROM performance_schema.global_status
       WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') r,
     (SELECT VARIABLE_VALUE AS v FROM performance_schema.global_status
       WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') q;
```

Ví dụ tính tay: read_requests = 50.000.000, reads = 250.000. Miss = 250.000 / 50.000.000 = 0.5%, hit
ratio = 99.5%.

**Đọc thế nào.** Workload OLTP có dữ liệu nóng vừa RAM thường ở mức trên 99%. Nhưng có hai điều cần
hiểu đúng:

- Đây là counter cộng dồn. Tỉ lệ tính từ lúc khởi động che mất sự cố mới; nên tính trên **chênh lệch**
  trong vài phút gần nhất, giống QPS.
- 99% nghe cao nhưng có thể vẫn tệ: 1% của 100.000 lần đọc/giây là 1.000 lần đọc đĩa/giây. Theo dõi
  thêm *tốc độ* của `Innodb_buffer_pool_reads` (số lần đọc đĩa mỗi giây) thì sát thực tế hơn.

Hit ratio tụt thường do: buffer pool quá nhỏ so với dữ liệu nóng, một câu báo cáo quét bảng lớn, hoặc
server vừa restart (buffer pool lạnh, xem
[Chương 16 mục 4.6](16-ben-trong-innodb.md#46-buffer-pool-lạnh-sau-restart)).

### 3.6 Replication lag

Replication sẽ được giảng ở chương riêng; ở đây chỉ cần biết đo ở đâu. Trên **replica**:

```sql
SHOW REPLICA STATUS\G
```

Các trường cần nhìn:

- `Replica_IO_Running` và `Replica_SQL_Running`: phải đều là `Yes`. Một trong hai là `No` nghĩa là
  replication đã dừng (xem `Last_IO_Error`, `Last_SQL_Error`).
- `Seconds_Behind_Source`: replica tụt sau source bao nhiêu giây. `NULL` khi luồng SQL không chạy (hoặc luồng SQL đã
  xử lý hết relay log mà luồng IO không chạy).

⚠️ `Seconds_Behind_Source` dựa trên timestamp của sự kiện trong binlog, nên có thể nhảy thất thường
(ví dụ một transaction lớn chạy 10 phút: lag nhảy từ 0 lên 600 rồi về 0). Nhiều đội đo chính xác hơn
bằng *heartbeat table*: source ghi thời gian hiện tại vào một bảng mỗi giây, replica so thời gian đó
với đồng hồ của nó (công cụ `pt-heartbeat` làm việc này).

Lag ảnh hưởng tới ứng dụng ra sao (đọc dữ liệu cũ sau khi ghi) đã ở
[Chương 19 mục 9.2](19-database-tu-ung-dung.md#92-replication-lag-và-các-anomaly).

### 3.7 Lock wait

Cơ chế lock ở [Chương 15](15-lock-deadlock.md). Chỉ số vận hành:

| Status | Loại | Ý nghĩa |
|---|---|---|
| `Innodb_row_lock_current_waits` | gauge | Số row lock đang bị chờ ngay lúc này |
| `Innodb_row_lock_waits` | counter | Tổng số lần phải chờ row lock |
| `Innodb_row_lock_time_avg` | (ms) | Thời gian chờ trung bình |

Khi `Innodb_row_lock_current_waits` tăng, tìm ai chặn ai bằng view `sys.innodb_lock_waits`:

```sql
SELECT wait_age_secs, locked_table_name,
       waiting_pid,  LEFT(waiting_query, 50)  AS dang_cho,
       blocking_pid, LEFT(blocking_query, 50) AS dang_chan,
       sql_kill_blocking_query
FROM sys.innodb_lock_waits;
```

Thử tái hiện với hai session trên một bảng nhỏ:

```sql
CREATE DATABASE IF NOT EXISTS ops;
USE ops;
CREATE TABLE tai_khoan (id INT PRIMARY KEY, so_du INT NOT NULL);
INSERT INTO tai_khoan VALUES (1, 100), (2, 200);
```

| Thời điểm | Session A | Session B | Session C (giám sát) |
|---|---|---|---|
| t1 | `START TRANSACTION;` `UPDATE ops.tai_khoan SET so_du = 90 WHERE id = 1;` | | |
| t2 | (không commit, đi uống cà phê) | `UPDATE ops.tai_khoan SET so_du = 80 WHERE id = 1;` (bị chặn) | |
| t3 | | (vẫn chờ) | `SELECT ... FROM sys.innodb_lock_waits;` thấy 1 dòng: `waiting_pid` là B, `blocking_pid` là A, `blocking_query` là `NULL` |
| t4 | | | `KILL <blocking_pid>;` (mục 5.3) |
| t5 | (connection bị đóng, transaction rollback) | UPDATE chạy xong | |

Ở t3, `blocking_query` của A là `NULL` vì A **không đang chạy câu nào**: nó chỉ đang giữ transaction
mở. Đây là hình dạng của sự cố "transaction quên đóng" rất hay gặp: không có câu chậm nào trong
processlist, nhưng mọi người đều chờ. Nếu không ai can thiệp, B sẽ bỏ cuộc sau
`innodb_lock_wait_timeout` (mặc định 50 giây) với lỗi 1205.

Để log mọi deadlock (không chỉ cái gần nhất trong `SHOW ENGINE INNODB STATUS`) vào error log, bật
`innodb_print_all_deadlocks` (mặc định `OFF`).

### 3.8 History list length

Giải thích đầy đủ ở [Chương 16 mục 6.5](16-ben-trong-innodb.md#65-history-list-length-và-sự-cố-transaction-quên-đóng).
Về vận hành, đây là chỉ số **phải có cảnh báo**:

```sql
SELECT `count` AS history_list_length
FROM information_schema.INNODB_METRICS
WHERE name = 'trx_rseg_history_len';    -- counter này bật sẵn mặc định
```

HLL tăng đều không giảm gần như luôn do một transaction (kể cả chỉ đọc) mở quá lâu. Tìm nó:

```sql
SELECT trx_mysql_thread_id AS pid,
       TIMESTAMPDIFF(SECOND, trx_started, NOW()) AS tuoi_giay,
       trx_state, LEFT(trx_query, 60) AS cau_hien_tai
FROM information_schema.INNODB_TRX
ORDER BY trx_started
LIMIT 5;
```

Cảnh báo nên có hai vế: HLL vượt một ngưỡng (đặt theo mức bình thường của hệ thống bạn, ví dụ vài
chục nghìn), **và** có transaction mở quá N phút.

### 3.9 Đĩa

MySQL không biết đĩa còn trống bao nhiêu; phải đo từ hệ điều hành (`df -h`) hoặc agent giám sát. Thứ
chiếm đĩa của MySQL:

| Thành phần | Xem bằng |
|---|---|
| Dữ liệu và index | `information_schema.TABLES` (mục 6) |
| Binlog | `SHOW BINARY LOGS` |
| Redo log | `innodb_redo_log_capacity` |
| Undo tablespace | `information_schema.FILES` (xem Chương 16 mục 6.6) |
| Bảng tạm trên đĩa, file sort | Không cố định; tăng vọt khi có câu sort/group lớn |
| Slow log, general log, error log | Kích thước file trên hệ điều hành |

⚠️ Hết đĩa với database là sự cố nặng: ghi bị treo hoặc lỗi, có khi phải dừng server để dọn. Cảnh báo
nên báo từ khi còn khoảng 20% trống, và dựa trên **tốc độ đầy** ("với tốc độ này, đĩa đầy sau 3 ngày")
chứ không chỉ phần trăm hiện tại.

Ngoài dung lượng, độ trễ I/O và số IOPS (đo ở hệ điều hành: `iostat`, hoặc metric của nhà cung cấp
cloud) cho biết đĩa có phải nút cổ chai không.

Một counter liên quan: `Created_tmp_disk_tables` (số bảng tạm nội bộ phải ghi xuống đĩa). Tốc độ tăng
cao thường do các câu `GROUP BY`/`ORDER BY`/`DISTINCT` trên tập lớn.

### 3.10 Bảng tóm tắt: theo dõi gì, cảnh báo khi nào

| Chỉ số | Nguồn | Gợi ý cảnh báo (tự hiệu chỉnh theo hệ thống) |
|---|---|---|
| QPS | `Questions` (tốc độ) | Lệch mạnh so với cùng giờ ngày/tuần trước |
| Latency p95/p99 | digest, hoặc đo ở app | Vượt mức cam kết (SLO) |
| `Threads_running` | status | Vượt xa số CPU core trong vài phút |
| `Threads_connected` | status | Trên khoảng 80% `max_connections` |
| Đọc đĩa buffer pool | `Innodb_buffer_pool_reads` (tốc độ) | Tăng mạnh so với nền |
| Replication | `SHOW REPLICA STATUS` | Thread dừng; lag vượt N giây |
| Lock wait | `Innodb_row_lock_current_waits`, `sys.innodb_lock_waits` | Có chờ lâu hơn vài giây |
| History list length | `INNODB_METRICS` | Tăng đều không giảm; transaction mở quá N phút |
| Đĩa | hệ điều hành | Dưới 20% trống, hoặc dự báo đầy trong vài ngày |
| Server sống | `Uptime` | `Uptime` nhỏ bất thường = vừa restart (có thể do crash) |

Các ngưỡng trong bảng là gợi ý khởi điểm, không có con số nào đúng cho mọi hệ thống. Cách làm đúng:
ghi nhận "mức bình thường" (baseline) trong vài tuần, rồi cảnh báo khi lệch khỏi baseline.

---

## 4. performance_schema và sys: nhìn vào bên trong server đang chạy

### 4.1 Hai schema này là gì

- **`performance_schema`**: một storage engine đặc biệt, ghi lại các sự kiện bên trong server (câu
  lệnh, giai đoạn xử lý, chờ I/O, chờ lock, bộ nhớ...) vào các bảng **chỉ nằm trong RAM**. Bật mặc
  định (`performance_schema = ON`, chỉ đổi được lúc khởi động). Các bảng của nó mất dữ liệu khi
  restart. Thời gian đo bằng picosecond.
- **`sys`**: một schema gồm các *view*, *function*, *procedure* viết sẵn trên `performance_schema` và
  `information_schema`, để người đọc không phải tự join hàng chục bảng thô. Hầu hết view có hai bản:
  bản thường (`sys.statement_analysis`) hiển thị số đã định dạng cho người đọc (`1.25 s`, `3.20 MiB`),
  và bản `x$` (`sys.x$statement_analysis`) giữ số thô để máy xử lý hoặc sắp xếp.

⚠️ Bản thường trả về *chuỗi* đã định dạng. `ORDER BY total_latency` trên bản thường sắp xếp theo chữ
(`"9.5 ms"` đứng sau `"10.2 s"`), sai. Muốn tự sắp xếp, lọc theo số, dùng bản `x$`. Đa số view đã có
thứ tự mặc định hợp lý (manual ghi rõ cho từng view), nên thường không cần `ORDER BY`.

**Chi phí.** Đo đạc tốn CPU và RAM. Vì thế không phải mọi *instrument* (điểm đo) và *consumer* (bảng
nhận dữ liệu) đều bật mặc định: phần được bật sẵn là phần có chi phí thấp và hữu ích nhất (câu lệnh,
I/O file và table, lock table...). Bật thêm (ví dụ các wait `wait/synch/%`) giúp chẩn đoán sâu hơn
nhưng tốn hơn; bật có chủ đích rồi tắt.

```sql
-- Instrument nào đang bật?
SELECT NAME, ENABLED, TIMED
FROM performance_schema.setup_instruments
WHERE NAME LIKE 'wait/io/file/innodb/%';
```

### 4.2 `sys.statement_analysis`: câu nào tốn nhất

Đây là view nên mở **đầu tiên** khi muốn biết server đang dành thời gian cho việc gì. Nó tổng hợp
bảng digest, mỗi dòng là một mẫu câu (đã thay giá trị cụ thể bằng `?`), mặc định sắp theo tổng thời
gian giảm dần.

```sql
SELECT query, db, exec_count, total_latency, avg_latency,
       rows_examined_avg, rows_sent_avg, full_scan, tmp_disk_tables
FROM sys.statement_analysis
LIMIT 5;
```

Output minh hoạ:

| query | db | exec_count | total_latency | avg_latency | rows_examined_avg | rows_sent_avg | full_scan | tmp_disk_tables |
|---|---|---|---|---|---|---|---|---|
| `SELECT * FROM orders WHERE customer_id = ? ...` | shop | 1840221 | 2.08 h | 4.07 ms | 52310 | 3 | * | 0 |
| `UPDATE products SET stock = stock - ? ...` | shop | 98211 | 21.30 min | 13.01 ms | 1 | 0 | | 0 |
| `SELECT ... GROUP BY DATE(created_at)` | shop | 288 | 9.12 min | 1.90 s | 2100000 | 30 | * | 288 |

Cách đọc:

- **Dòng 1** là ứng viên số một dù mỗi lần chỉ 4 ms: chạy gần 2 triệu lần, tổng 2 giờ. `rows_examined_avg`
  52310 mà `rows_sent_avg` chỉ 3: đọc hàng chục nghìn dòng để trả về 3, `full_scan` có dấu `*`. Gần
  như chắc chắn thiếu index trên `customer_id` (đem câu này đi `EXPLAIN` theo
  [Chương 12](12-explain-toi-uu-query.md)).
- **Dòng 2** đọc 1 dòng mà mất 13 ms: không phải vấn đề index, nghi chờ lock (sản phẩm "hot" bị nhiều
  người cùng mua). Xem cột `lock_latency`.
- **Dòng 3** chậm từng lần (1.9 s) nhưng ít chạy; là báo cáo, và mỗi lần đều tạo bảng tạm trên đĩa.

💡 Nguyên tắc ưu tiên: tối ưu theo **tổng thời gian** (`total_latency`), không theo thời gian từng
lần. Một câu 4 ms chạy triệu lần thường đáng sửa hơn một câu 2 giây chạy vài lần mỗi ngày.

Các view cùng họ, đều nên biết tên:

| View | Cho biết |
|---|---|
| `sys.statements_with_full_table_scans` | Câu quét toàn bảng |
| `sys.statements_with_runtimes_in_95th_percentile` | Câu nằm trong nhóm 5% chậm nhất |
| `sys.statements_with_temp_tables` | Câu tạo bảng tạm (nhất là trên đĩa) |
| `sys.statements_with_sorting` | Câu phải sort |
| `sys.statements_with_errors_or_warnings` | Câu hay lỗi hoặc có warning |

### 4.3 Server đang chờ cái gì: top waits

Một câu query chậm vì hai lý do: **làm nhiều việc** (đọc nhiều dòng) hoặc **chờ** (chờ đĩa, chờ lock,
chờ mutex). Các view *wait* trả lời câu thứ hai ở mức toàn server.

```sql
SELECT events, total, total_latency, avg_latency
FROM sys.waits_global_by_latency
LIMIT 5;
```

Output minh hoạ:

| events | total | total_latency | avg_latency |
|---|---|---|---|
| wait/io/file/innodb/innodb_data_file | 9182211 | 3.41 h | 1.34 ms |
| wait/io/table/sql/handler | 812339120 | 1.20 h | 5.31 us |
| wait/lock/table/sql/handler | 120992 | 6.02 min | 2.99 ms |
| wait/io/file/innodb/innodb_log_file | 2210831 | 4.11 min | 111.55 us |

Đọc tên sự kiện theo từng đoạn:

- `wait/io/file/innodb/innodb_data_file`: chờ đọc/ghi **file dữ liệu** InnoDB. Đứng đầu nghĩa là
  server chủ yếu chờ đĩa: buffer pool có thể quá nhỏ, hoặc có câu quét nhiều dữ liệu.
- `wait/io/file/innodb/innodb_log_file`: chờ ghi **redo log** (gắn với commit).
- `wait/io/table/sql/handler`: thời gian I/O ở mức *table* (đọc/ghi dòng qua storage engine), gồm cả
  đọc từ buffer pool; số lần lớn là bình thường.
- `wait/lock/table/sql/handler`: chờ lock ở mức table.

Không có con số "đúng" cho các wait này. Dùng chúng để **so sánh**: lúc bình thường thứ gì đứng đầu,
lúc sự cố thứ gì nhảy lên. Để biết bảng nào, file nào bị I/O nhiều nhất, xem tiếp
`sys.io_global_by_file_by_latency` và `sys.schema_table_statistics`.

### 4.4 Các view sys khác hay dùng khi vận hành

| View | Dùng khi |
|---|---|
| `sys.innodb_lock_waits` | Ai đang chặn ai (mục 3.7) |
| `sys.schema_table_lock_waits` | Ai đang chờ metadata lock (ví dụ ALTER bị treo, xem [Chương 20 mục 3](20-thay-doi-schema-migration.md#3-metadata-lock-và-lock_wait_timeout)) |
| `sys.schema_unused_indexes` | Index không được dùng từ lúc khởi động (ứng viên xoá) |
| `sys.schema_redundant_indexes` | Index thừa vì đã bị index khác bao trùm |
| `sys.schema_table_statistics` | Bảng nào bị đọc/ghi nhiều nhất, tốn bao nhiêu thời gian I/O |
| `sys.innodb_buffer_stats_by_table` | Bảng nào chiếm bao nhiêu buffer pool |
| `sys.memory_global_by_current_bytes` | Bộ nhớ server đang dùng cho việc gì |
| `sys.host_summary`, `sys.user_summary` | Tải chia theo host, theo user |

⚠️ `sys.schema_unused_indexes` chỉ đáng tin khi server đã chạy đủ lâu với workload đại diện (manual
nói rõ điều này). Server mới restart hôm qua chưa chạy báo cáo cuối tháng; xoá index "không dùng" lúc
đó có thể làm báo cáo cuối tháng chậm hàng giờ. Khi xoá, cho index *invisible* trước (xem
[Chương 20 mục 8.3](20-thay-doi-schema-migration.md#83-xoá-index-an-toàn-cho-nó-vô-hình-trước)).

⚠️ `sys.innodb_buffer_stats_by_table` quét toàn bộ buffer pool để đếm; trên buffer pool hàng chục
GB, chính nó có thể tốn đáng kể. Không chạy liên tục trên production.

---

## 5. Ai đang chạy gì: processlist và KILL

### 5.1 Ba cách xem danh sách thread

Mỗi connection tới MySQL là một thread. *Processlist* liệt kê chúng cùng việc đang làm.

```sql
SHOW FULL PROCESSLIST;                    -- cách quen thuộc
SELECT * FROM performance_schema.processlist;   -- dạng bảng, lọc được bằng SQL
SELECT * FROM sys.processlist;            -- thêm thông tin: latency, transaction, bộ nhớ...
```

Có quyền `PROCESS` thì thấy mọi thread; không có thì chỉ thấy thread của chính mình.

Khác biệt bên trong mà người vận hành nên biết: cách cài đặt mặc định của `SHOW PROCESSLIST` duyệt
các thread **trong khi giữ một mutex toàn cục**, tốn kém trên server bận. Bảng
`performance_schema.processlist` lấy dữ liệu từ Performance Schema, không cần mutex đó. Bật
`performance_schema_show_processlist` (mặc định `OFF`) thì chính `SHOW PROCESSLIST` cũng chuyển sang
dùng bảng này; nhưng ở 8.4 chính biến này cũng đã được đánh dấu deprecated. Manual 8.4 ghi bảng
`INFORMATION_SCHEMA.PROCESSLIST` và bản cài đặt `SHOW PROCESSLIST` dựa trên nó đã deprecated, khuyên
dùng bản của Performance Schema. Cách gọn nhất: truy vấn thẳng `performance_schema.processlist`.

### 5.2 Đọc processlist

```sql
SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, LEFT(INFO, 60) AS cau
FROM performance_schema.processlist
WHERE COMMAND <> 'Sleep'
ORDER BY TIME DESC;
```

Output minh hoạ:

| ID | USER | HOST | DB | COMMAND | TIME | STATE | cau |
|---|---|---|---|---|---|---|---|
| 812 | report | 10.0.2.15:51022 | shop | Query | 1834 | executing | `SELECT c.city, SUM(o.total) FROM orders o JOIN ...` |
| 905 | app | 10.0.1.7:40112 | shop | Query | 41 | updating | `UPDATE products SET stock = stock - 1 WHERE id = 77` |
| 906 | app | 10.0.1.8:40998 | shop | Query | 39 | updating | `UPDATE products SET stock = stock - 1 WHERE id = 77` |
| 5 | event_scheduler | localhost | NULL | Daemon | 99120 | Waiting on empty queue | NULL |

- `COMMAND`: `Query` (đang chạy câu lệnh), `Sleep` (connection rảnh, chờ client), `Daemon`
  (thread nền), `Binlog Dump` (replica đang kéo binlog)...
- `TIME`: số giây ở trạng thái hiện tại.
- `STATE`: giai đoạn đang làm (manual có danh sách *thread states*).
- `INFO`: câu lệnh đang chạy (`NULL` nếu không có).

Đọc ví dụ trên: một câu báo cáo chạy 30 phút (ID 812) và hai câu UPDATE cùng dòng `id = 77` đang
chờ nhau khoảng 40 giây. Bước tiếp theo là xem `sys.innodb_lock_waits` để biết ai chặn hai câu UPDATE.

⚠️ Một connection `Sleep` với `TIME` rất lớn không vô hại nếu nó **đang giữ transaction mở**
(ví dụ ở mục 3.7). Processlist không nói điều đó; phải join với `information_schema.INNODB_TRX`:

```sql
SELECT p.ID, p.USER, p.COMMAND, p.TIME AS idle_giay,
       t.trx_started, t.trx_rows_locked
FROM performance_schema.processlist p
JOIN information_schema.INNODB_TRX t ON t.trx_mysql_thread_id = p.ID
WHERE p.COMMAND = 'Sleep';
```

### 5.3 KILL QUERY và KILL CONNECTION

```sql
KILL QUERY 812;        -- dừng câu đang chạy, giữ connection
KILL CONNECTION 812;   -- dừng câu đang chạy (nếu có) rồi đóng connection
KILL 812;              -- giống KILL CONNECTION
```

`812` là ID trong processlist (giá trị của `CONNECTION_ID()` trong session đó). Không có quyền
`CONNECTION_ADMIN` thì chỉ kill được thread của chính mình.

Chọn cái nào:

- **`KILL QUERY`** khi một câu chạy quá lâu (báo cáo, câu bị lỗi logic). Connection còn sống, ứng dụng
  nhận lỗi cho câu đó và tiếp tục được.
- **`KILL CONNECTION`** khi thủ phạm là một connection đang **giữ transaction mở mà không chạy gì**
  (như session A ở mục 3.7). `KILL QUERY` không có tác dụng vì không có câu nào để dừng; phải đóng
  connection để transaction bị rollback và nhả lock.

Cơ chế bên trong và hệ quả:

- `KILL` chỉ **đặt cờ** cho thread rồi trả về ngay. Thread tự kiểm tra cờ ở những điểm nhất định (sau
  mỗi khối dòng đọc, sau mỗi dòng update/delete...), nên có độ trễ trước khi dừng hẳn.
- Kill một câu `UPDATE`/`DELETE` lớn trên InnoDB kéo theo **rollback**: InnoDB phải hoàn tác mọi
  dòng đã sửa bằng undo log. Câu đã chạy 30 phút có thể cần thời gian tương đương để rollback; trong
  lúc đó processlist hiện `Killed` và lock vẫn bị giữ. ⚠️ Đừng restart server vì "kill mãi không
  chết": sau restart, crash recovery vẫn phải rollback tiếp, và server còn không phục vụ được gì
  trong lúc đó.
- `KILL` không giải quyết nguyên nhân. Ghi lại câu bị kill (copy `INFO`) để sửa sau.

Ngăn từ đầu tốt hơn kill: `max_execution_time` (mili giây, mặc định `0` là không giới hạn) giới hạn
thời gian cho câu `SELECT` chỉ đọc; xem [Chương 19 mục 10.3](19-database-tu-ung-dung.md#103-timeout-truy-vấn-trên-mysql).

---

## 6. Dung lượng và tăng trưởng

### 6.1 Bảng nào to nhất

```sql
SELECT TABLE_SCHEMA, TABLE_NAME,
       TABLE_ROWS                                AS so_dong_uoc_luong,
       FORMAT_BYTES(DATA_LENGTH)                 AS du_lieu,
       FORMAT_BYTES(INDEX_LENGTH)                AS index_phu,
       FORMAT_BYTES(DATA_LENGTH + INDEX_LENGTH)  AS tong,
       FORMAT_BYTES(DATA_FREE)                   AS trong
FROM information_schema.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_SCHEMA NOT IN ('mysql', 'sys', 'performance_schema', 'information_schema')
ORDER BY DATA_LENGTH + INDEX_LENGTH DESC
LIMIT 10;
```

Output minh hoạ:

| TABLE_SCHEMA | TABLE_NAME | so_dong_uoc_luong | du_lieu | index_phu | tong | trong |
|---|---|---|---|---|---|---|
| shop | order_events | 48211930 | 9.83 GiB | 6.12 GiB | 15.95 GiB | 7.00 MiB |
| shop | orders | 5120344 | 1.51 GiB | 902.00 MiB | 2.39 GiB | 4.00 MiB |
| shop | customers | 401231 | 96.58 MiB | 61.11 MiB | 157.69 MiB | 4.00 MiB |

Ý nghĩa các cột với InnoDB (theo manual):

- `DATA_LENGTH`: dung lượng *xấp xỉ* cấp cho **clustered index** (tức chính dữ liệu, vì InnoDB lưu
  dữ liệu trong clustered index; xem [Chương 11](11-index.md)).
- `INDEX_LENGTH`: dung lượng xấp xỉ của các **secondary index**.
- `DATA_FREE`: dung lượng đã cấp nhưng đang trống trong tablespace.
- `TABLE_ROWS`: chỉ là **ước lượng** dùng cho optimizer; manual ghi có thể lệch tới 40% tới 50%. Cần
  số chính xác thì `SELECT COUNT(*)`.

`FORMAT_BYTES()` là hàm có sẵn của MySQL 8.4, đổi số byte sang dạng `KiB/MiB/GiB`.

⚠️ **Số liệu có thể cũ tới 24 giờ.** Các cột thống kê của `information_schema.TABLES` được cache;
`information_schema_stats_expiry` mặc định 86400 giây. Bảng vừa nạp 10 triệu dòng có thể vẫn hiện số
cũ. Muốn số mới: `ANALYZE TABLE ten_bang;` hoặc trong session đó
`SET SESSION information_schema_stats_expiry = 0;` trước khi truy vấn.

Kích thước file thật trên đĩa (file `.ibd` của từng bảng) xem ở `information_schema.INNODB_TABLESPACES`
(cột `FILE_SIZE`, `ALLOCATED_SIZE`) hoặc trực tiếp bằng `ls -lh` trong data directory.

### 6.2 Theo dõi tăng trưởng

Một con số kích thước chỉ cho biết "bây giờ". Để dự báo khi nào đầy đĩa, cần **chuỗi thời gian**. Nếu
chưa có hệ thống giám sát lưu số này, có thể tự chụp mỗi ngày:

```sql
CREATE TABLE ops.kich_thuoc_bang (
    ngay         DATE        NOT NULL,
    schema_name  VARCHAR(64) NOT NULL,
    table_name   VARCHAR(64) NOT NULL,
    tong_byte    BIGINT UNSIGNED NOT NULL,
    so_dong      BIGINT UNSIGNED NULL,
    PRIMARY KEY (ngay, schema_name, table_name)
);

-- Chạy mỗi ngày một lần (cron, hoặc EVENT ở Chương 17)
SET SESSION information_schema_stats_expiry = 0;
INSERT INTO ops.kich_thuoc_bang
SELECT CURDATE(), TABLE_SCHEMA, TABLE_NAME, DATA_LENGTH + INDEX_LENGTH, TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND TABLE_SCHEMA NOT IN ('mysql', 'sys', 'performance_schema', 'information_schema', 'ops');
```

Lưu ý: `SET SESSION information_schema_stats_expiry = 0` chỉ có tác dụng trong cùng session, nên phải
nằm cùng script với câu `INSERT`.

Tăng trưởng 7 ngày của từng bảng:

```sql
SELECT n.schema_name, n.table_name,
       FORMAT_BYTES(n.tong_byte)                          AS hom_nay,
       FORMAT_BYTES(n.tong_byte - c.tong_byte)            AS tang_7_ngay,
       FORMAT_BYTES((n.tong_byte - c.tong_byte) / 7)      AS tang_moi_ngay
FROM ops.kich_thuoc_bang n
JOIN ops.kich_thuoc_bang c
  ON c.schema_name = n.schema_name
 AND c.table_name  = n.table_name
 AND c.ngay        = n.ngay - INTERVAL 7 DAY
WHERE n.ngay = CURDATE()
ORDER BY n.tong_byte - c.tong_byte DESC;
```

Ví dụ tính tay: `order_events` hôm nay 15.95 GiB, 7 ngày trước 14.55 GiB, tăng 1.40 GiB, tức khoảng
0.2 GiB/ngày. Đĩa còn trống 40 GiB thì riêng bảng này cần khoảng 200 ngày mới lấp đầy; nhưng nhớ
cộng cả binlog (mỗi thay đổi đều được ghi vào binlog, giữ 30 ngày theo mặc định) và chỗ cho các thao
tác cần copy bảng.

⚠️ **Chừa chỗ cho thao tác bảo trì.** `ALTER TABLE` kiểu copy, `OPTIMIZE TABLE`, công cụ gh-ost/pt-osc
(Chương 20) tạo bản sao của bảng: cần thêm dung lượng xấp xỉ bằng kích thước bảng. Bảng 16 GiB trên đĩa
còn trống 10 GiB là không ALTER được.

Bảng to lên nhanh nhất thường là log, event, lịch sử: những bảng chỉ thêm mà không bao giờ xoá. Cách
xử lý (xoá theo batch, partition theo thời gian, đẩy sang kho lưu trữ rẻ hơn) ở
[Chương 23](23-partition-sharding-scale.md).

---

## 7. Nâng cấp phiên bản: từ 8.0 lên 8.4 LTS

### 7.1 Vì sao phải nâng cấp, và mô hình phát hành

Từ năm 2023, MySQL chia bản phát hành thành hai dòng (manual 8.4, mục *MySQL Releases: Innovation and
LTS*):

- **LTS (Long-Term Support)**: tính năng ổn định, chỉ nhận bản sửa lỗi; tính năng chỉ được thêm/bỏ ở
  bản đầu tiên của dòng (như 8.4.0). Hỗ trợ theo Oracle Lifetime Support Policy: 5 năm premier và 3
  năm extended. Dành cho production.
- **Innovation**: ra thường xuyên, có tính năng mới, mỗi bản được hỗ trợ ngắn. Hợp để thử nghiệm.

MySQL 8.0 đã hết hỗ trợ (hết extended support theo Oracle Lifetime Support Policy) vào tháng 4/2026:
không còn bản vá bảo mật. Chạy 8.0 sau mốc này là nợ kỹ thuật
có rủi ro bảo mật thật. Đích đến tự nhiên là **8.4 LTS**.

Lộ trình được hỗ trợ (bảng *Upgrade Paths* trong manual 8.4):

| Từ | Tới | Cách được hỗ trợ |
|---|---|---|
| 8.0.x | 8.4.x LTS | In-place, logical dump/load, replication |
| 8.4.x | 8.4.y (cùng dòng) | In-place, dump/load, replication, MySQL Clone |
| 5.7 | 8.4 | **Không trực tiếp**: phải lên 8.0 trước, rồi 8.0 lên 8.4 |

Chiều ngược lại (downgrade) từ 8.4 về 8.0 **không làm in-place được**: chỉ bằng dump/load hoặc
replication, và chỉ được hỗ trợ cho mục đích rollback khi chưa dùng tính năng mới nào. Nghĩa là kế
hoạch quay lui phải chuẩn bị *trước* khi nâng cấp.

### 7.2 Những thay đổi ở 8.4 dễ làm vỡ ứng dụng

**1. `mysql_native_password` không còn được bật mặc định.** Plugin xác thực cũ này (deprecated từ 8.0)
không được nạp mặc định ở 8.4.0. Account nào vẫn dùng nó sẽ **không đăng nhập được** sau nâng cấp.
Mặc định cho account mới là `caching_sha2_password` (theo `authentication_policy`; biến cũ
`default_authentication_plugin` đã bị **xoá** ở 8.4.0, để nó trong `my.cnf` làm server không khởi
động được).

```sql
-- Chạy trên 8.0 TRƯỚC khi nâng cấp: account nào còn dùng plugin cũ?
SELECT user, host, plugin
FROM mysql.user
WHERE plugin = 'mysql_native_password';
```

Cách xử lý đúng: chuyển account sang plugin mới, kiểm tra driver của ứng dụng hỗ trợ nó (driver hiện
đại như PDO/mysqlnd của PHP mới, Connector/J, go-sql-driver đều hỗ trợ):

```sql
ALTER USER 'app'@'10.0.%' IDENTIFIED WITH caching_sha2_password BY 'mat-khau-moi';
```

Cách tạm thời nếu chưa kịp: bật lại plugin cũ bằng `mysql_native_password=ON` trong mục `[mysqld]`
(hoặc `--mysql-native-password=ON`). Chỉ nên là cầu nối ngắn hạn.

Chi tiết về plugin xác thực ở [Chương 18](18-user-quyen-bao-mat.md).

**2. Thuật ngữ replication: các câu lệnh cũ bị xoá.** Ở 8.4, các câu dùng `MASTER`/`SLAVE` (đã
deprecated) giờ là **lỗi cú pháp**:

| Câu cũ (lỗi ở 8.4) | Câu mới |
|---|---|
| `SHOW SLAVE STATUS` | `SHOW REPLICA STATUS` |
| `START SLAVE` / `STOP SLAVE` | `START REPLICA` / `STOP REPLICA` |
| `RESET SLAVE` | `RESET REPLICA` |
| `SHOW SLAVE HOSTS` | `SHOW REPLICAS` |
| `CHANGE MASTER TO MASTER_HOST = ...` | `CHANGE REPLICATION SOURCE TO SOURCE_HOST = ...` |
| `SHOW MASTER STATUS` | `SHOW BINARY LOG STATUS` |
| `SHOW MASTER LOGS` | `SHOW BINARY LOGS` |
| `PURGE MASTER LOGS` | `PURGE BINARY LOGS` |
| `RESET MASTER` | `RESET BINARY LOGS AND GTIDS` |

Thứ hay vỡ không phải ứng dụng mà là **script vận hành và công cụ giám sát**: script backup chạy
`SHOW MASTER STATUS`, health check chạy `SHOW SLAVE STATUS`, exporter phiên bản cũ. Tên cột trong
output cũng đổi (`Seconds_Behind_Master` thành `Seconds_Behind_Source`), nên dashboard và cảnh báo
đọc tên cột cũ sẽ im lặng mất số liệu.

**3. Mặc định InnoDB đổi** (mục 2.10). Hiệu năng có thể khác đi dù bạn không đổi gì.

**4. Những thay đổi khác cần rà** (ghi trong mục *What Is New in MySQL 8.4 since MySQL 8.0* của manual):

- `AUTO_INCREMENT` trên cột `FLOAT`/`DOUBLE` bị bỏ hẳn; bảng nào còn dùng làm **nâng cấp thất bại**.
- Khoá ngoại tham chiếu tới cột không phải khoá unique/primary đầy đủ bị từ chối mặc định
  (`restrict_fk_on_non_standard_key = ON`).
- Nhiều biến và tuỳ chọn đã deprecated ở 8.0 bị xoá; còn trong file cấu hình thì server báo lỗi khi
  khởi động.

### 7.3 Quy trình nâng cấp an toàn

1. **Đọc** mục *Changes in MySQL 8.4* và *What Is New in MySQL 8.4 since MySQL 8.0*.
2. **Chạy Upgrade Checker** của MySQL Shell trên server 8.0: `util.checkForServerUpgrade()` liệt kê
   các vấn đề (plugin xác thực, biến bị xoá, schema không tương thích...). Manual khuyến nghị bước này.
3. **Sửa** những gì checker báo; rà `my.cnf` bỏ biến bị xoá, bỏ các mặc định cũ được đặt cứng.
4. **Dựng môi trường thử** chạy 8.4 với bản sao dữ liệu; chạy test của ứng dụng và đo hiệu năng các
   query quan trọng (optimizer có thể chọn plan khác).
5. **Nâng cấp qua replication** (cách ít downtime nhất): dựng replica 8.4 từ source 8.0, để nó chạy
   bắt kịp, chuyển dần traffic đọc sang, theo dõi; cuối cùng chuyển (failover) cho replica 8.4 làm
   source. Replica 8.0 cũ giữ lại một thời gian làm đường lui.
6. **Backup** ngay trước bước cuối, và kiểm tra backup khôi phục được.
7. **Theo dõi** sau nâng cấp: các chỉ số ở mục 3, so với baseline trước nâng cấp.

Nâng cấp in-place (thay binary, khởi động lại trên cùng data directory) đơn giản hơn nhưng có
downtime và đường lui khó hơn (không downgrade in-place được).

---

## 8. Checklist khi "database chậm"

Nhận tin nhắn "web chậm quá, chắc DB" lúc 2 giờ sáng. Đây là trình tự gợi ý: đi từ **rộng tới hẹp**,
từ thứ **rẻ và nhanh để kiểm** tới thứ tốn công. Ghi lại mọi thứ bạn thấy và làm (kèm giờ): sau sự cố
bạn sẽ cần nó.

**Bước 0. Xác nhận vấn đề nằm ở DB.** Latency phía ứng dụng tăng có thể do pool cạn, mạng, dịch vụ
khác. So latency DB (digest, mục 3.3) với latency app. Có thay đổi gì vừa xảy ra không: deploy mới,
migration, job mới, traffic tăng đột biến (marketing gửi email)? Phần lớn sự cố bắt nguồn từ một thay
đổi.

**Bước 1. Tài nguyên máy.** CPU, RAM (có swap không?), I/O (latency đĩa, IOPS chạm trần?), dung lượng
đĩa trống, mạng. Đĩa đầy hay máy swap thì mọi thứ khác là thứ yếu.

**Bước 2. Tổng quan server.**

```sql
SELECT VARIABLE_NAME, VARIABLE_VALUE FROM performance_schema.global_status
WHERE VARIABLE_NAME IN ('Uptime', 'Threads_connected', 'Threads_running',
                        'Innodb_row_lock_current_waits');
```

`Uptime` nhỏ: server vừa restart (crash? buffer pool lạnh?). `Threads_running` cao: có hàng đợi.
`Innodb_row_lock_current_waits` cao: nghi lock.

**Bước 3. Ai đang chạy gì.** Processlist, lọc bỏ `Sleep`, sắp theo `TIME` (mục 5.2). Tìm: câu chạy rất
lâu, nhiều câu giống nhau cùng chờ, trạng thái `Waiting for table metadata lock` (ALTER đang chặn,
[Chương 20 mục 3](20-thay-doi-schema-migration.md#3-metadata-lock-và-lock_wait_timeout)).

**Bước 4. Lock.** `sys.innodb_lock_waits` (mục 3.7). Nếu thủ phạm là transaction mở mà không chạy gì,
tìm nguồn của nó (host, user) trước khi kill.

**Bước 5. Transaction dài và history list length.** `INNODB_TRX` sắp theo `trx_started`, và HLL
(mục 3.8).

**Bước 6. Câu nào tốn nhất.** `sys.statement_analysis` (mục 4.2). Nếu có thể, `TRUNCATE` bảng digest
và đợi vài phút để thấy bức tranh *hiện tại* thay vì cộng dồn. Đối chiếu với slow log. Câu mới xuất
hiện, hoặc câu cũ bỗng chậm hơn (plan đổi, xem
[Chương 12 mục 5.6](12-explain-toi-uu-query.md#56-sự-cố-kinh-điển-query-đang-nhanh-bỗng-chậm)).

**Bước 7. Server chờ cái gì.** `sys.waits_global_by_latency` (mục 4.3), buffer pool reads/giây (mục
3.5).

**Bước 8. Replication** (nếu đọc từ replica): thread còn chạy không, lag bao nhiêu.

**Bước 9. Can thiệp, từ nhẹ tới nặng.**

| Mức | Hành động | Rủi ro |
|---|---|---|
| Nhẹ | Tạm dừng job/báo cáo nặng, bật cờ tắt tính năng nặng ở ứng dụng | Thấp |
| Vừa | `KILL QUERY` câu chạy lâu; `KILL` connection giữ lock | Rollback có thể lâu; ứng dụng nhận lỗi |
| Vừa | Thêm index còn thiếu (online DDL, Chương 20) | Tốn I/O lúc tạo, cần đĩa trống |
| Nặng | Failover sang replica, restart server | Downtime, buffer pool lạnh, crash recovery |

**Bước 10. Sau sự cố.** Tìm nguyên nhân gốc, sửa, và thêm cảnh báo để lần sau phát hiện sớm hơn.
Viết lại diễn biến (postmortem) không đổ lỗi.

⚠️ Hai việc **không nên** làm khi đang cháy: (1) restart server như phản xạ đầu tiên: mất hết bằng
chứng trong performance_schema và processlist, buffer pool lạnh làm mọi thứ chậm thêm một lúc, còn
transaction lớn vẫn phải rollback lúc khởi động; (2) đổi nhiều cấu hình cùng lúc: không biết cái nào
có tác dụng, cái nào làm tệ hơn.

---

## 9. Công cụ giám sát

### 9.1 Vì sao không chỉ dùng SQL tay

Mọi câu SQL ở mục 3 tới 6 chỉ cho một **ảnh chụp**. Để biết "bình thường là bao nhiêu", "từ mấy giờ
bắt đầu tăng", cần một hệ thống:

1. **Thu thập** chỉ số định kỳ (vài giây tới một phút một lần).
2. **Lưu** thành chuỗi thời gian (time series).
3. **Vẽ** biểu đồ (dashboard).
4. **Cảnh báo** khi chỉ số vượt ngưỡng hoặc lệch baseline.

Hệ thống này cũng tự xử lý những việc rắc rối khi tính tay: chuyển counter thành tốc độ, xử lý
counter về 0 khi restart.

### 9.2 Prometheus và `mysqld_exporter`

Mô hình phổ biến trong hệ sinh thái mã nguồn mở:

```
MySQL  <──SQL──  mysqld_exporter  <──HTTP /metrics──  Prometheus  ──>  Grafana (dashboard)
                                                           │
                                                           └──>  Alertmanager (gửi cảnh báo)
```

- **`mysqld_exporter`**: một tiến trình nhỏ, kết nối vào MySQL bằng một account chỉ có quyền đọc
  thông tin giám sát, chạy `SHOW GLOBAL STATUS`, `SHOW GLOBAL VARIABLES`, đọc performance_schema...,
  rồi phơi kết quả ra dạng text qua HTTP.
- **Prometheus**: định kỳ *kéo* (scrape) dữ liệu từ exporter, lưu chuỗi thời gian, đánh giá luật
  cảnh báo. Một counter như `Questions` trở thành metric; tốc độ được tính bằng hàm `rate()` của
  Prometheus.
- **Grafana**: vẽ dashboard từ dữ liệu Prometheus.
- Cùng mô hình có exporter cho máy (`node_exporter`: CPU, RAM, đĩa), nên chỉ số DB và chỉ số máy nằm
  chung một chỗ.

### 9.3 PMM (Percona Monitoring and Management)

PMM là bộ công cụ mã nguồn mở của Percona, đóng gói sẵn các thành phần thu thập, lưu trữ và dashboard
cho MySQL (và PostgreSQL, MongoDB). Điểm mạnh với MySQL là phần **Query Analytics**: tổng hợp query
từ slow log hoặc performance_schema thành danh sách "câu nào tốn nhất" theo thời gian, tức
`sys.statement_analysis` có thêm trục thời gian.

### 9.4 Dịch vụ managed

Amazon RDS/Aurora, Google Cloud SQL, Azure... có sẵn biểu đồ cơ bản (CPU, connection, IOPS, đĩa) và
công cụ phân tích query riêng của từng nhà cung cấp. Chúng tiện nhưng thường thiếu các chỉ số đặc thù
InnoDB như history list length; nhiều đội vẫn chạy thêm exporter hoặc PMM.

### 9.5 Giám sát cũng cần thiết kế

- Account giám sát chỉ cấp quyền cần thiết (`PROCESS`, `REPLICATION CLIENT`, `SELECT` trên
  performance_schema...), không dùng `root`.
- Cảnh báo nên dựa trên **triệu chứng người dùng thấy** (latency, lỗi) và **những thứ sắp hỏng**
  (đĩa sắp đầy, replication dừng, HLL tăng mãi), không cảnh báo mọi chỉ số. Cảnh báo kêu quá nhiều
  thì mọi người sẽ phớt lờ, kể cả cảnh báo thật.
- Bản thân việc thu thập tốn tài nguyên: scrape mỗi giây với hàng trăm bảng có thể tạo tải đáng kể.

---

## 10. Đối chiếu PostgreSQL

Chương 25 so sánh hai hệ chi tiết; ở đây chỉ đặt các công cụ vận hành tương ứng cạnh nhau.

| Việc | MySQL 8.4 | PostgreSQL |
|---|---|---|
| Cache dữ liệu | `innodb_buffer_pool_size` (mặc định 128 MB) | `shared_buffers` (mặc định 128 MB); PostgreSQL còn dựa nhiều vào page cache của hệ điều hành |
| Thống kê theo mẫu câu | `performance_schema` digest, `sys.statement_analysis` | Extension `pg_stat_statements` (phải nạp qua `shared_preload_libraries`) |
| Log câu chậm | `slow_query_log` + `long_query_time` | `log_min_duration_statement` |
| Ai đang chạy gì | `performance_schema.processlist` | View `pg_stat_activity` |
| Dừng câu đang chạy | `KILL QUERY id` | `SELECT pg_cancel_backend(pid)` |
| Đóng connection | `KILL CONNECTION id` | `SELECT pg_terminate_backend(pid)` |
| Transaction mở mà rảnh | Join processlist với `INNODB_TRX` | `pg_stat_activity.state = 'idle in transaction'`; có `idle_in_transaction_session_timeout` để tự cắt |
| Kích thước bảng | `information_schema.TABLES` | `pg_total_relation_size()`, `pg_size_pretty()` |
| Rác của MVCC | History list length | Dead tuple, bloat, theo dõi autovacuum (`pg_stat_user_tables`) |

Điểm khác về tư duy: ở PostgreSQL, ngoài các chỉ số chung, việc theo dõi **autovacuum** và **bloat**
là một mảng vận hành riêng (xem
[Chương 16 mục 11.2](16-ben-trong-innodb.md#112-vacuum-và-bloat)).

---

## Lỗi thường gặp

- **Để `innodb_buffer_pool_size` mặc định 128 MB trên production.** Mọi query phải đọc đĩa. Luôn chỉnh
  theo RAM của máy, hoặc bật `innodb_dedicated_server` trên máy dành riêng.
- **Đặt buffer pool bằng hoặc gần 100% RAM.** Máy swap hoặc `mysqld` bị OOM killer giết.
- **`SET GLOBAL` rồi quên lưu vào file cấu hình**, restart xong mất cấu hình. Hoặc ngược lại: sửa
  `my.cnf` mà không biết `mysqld-auto.cnf` (`SET PERSIST`) đang ghi đè.
- **Đổi biến global rồi tưởng connection đang mở cũng đổi theo** (ví dụ `long_query_time` với
  connection pool).
- **Nhìn latency trung bình thay vì p95/p99**, bỏ sót nhóm người dùng chờ lâu.
- **Đọc counter cộng dồn từ lúc khởi động** (hit ratio, digest) để kết luận về sự cố đang xảy ra.
- **Sắp xếp view `sys` bản thường theo cột latency**: sắp theo chuỗi, sai thứ tự. Dùng bản `x$`.
- **`KILL QUERY` một connection đang rảnh nhưng giữ transaction mở**: không có tác dụng. Phải `KILL`
  connection.
- **Restart server vì câu bị kill "mãi không chết"**: rollback vẫn phải chạy tiếp trong crash recovery.
- **Xoá index theo `sys.schema_unused_indexes` ngay sau restart**, khi workload chưa đủ đại diện.
- **Tin `TABLE_ROWS` là số dòng chính xác**, hoặc tin kích thước trong `information_schema.TABLES` là
  mới nhất (cache tới 24 giờ).
- **Xoá binlog bằng `rm`**, hoặc đặt thời gian giữ binlog ngắn hơn chu kỳ backup.
- **Nâng cấp lên 8.4 mà không kiểm account dùng `mysql_native_password`**, ứng dụng không đăng nhập
  được. Hoặc quên sửa script dùng `SHOW SLAVE STATUS`.

## Tóm tắt chương

- Ba nguồn thông tin: system variable (cấu hình), status variable (đã làm gì, đang có gì),
  instrumentation (`performance_schema`, `sys`, `information_schema`).
- Biến có scope (global/session) và có thể dynamic hoặc không. `SET GLOBAL` mất khi restart;
  `SET PERSIST` ghi vào `mysqld-auto.cnf` và thắng `my.cnf`. `performance_schema.variables_info` cho
  biết giá trị đến từ đâu.
- Mặc định 8.4 cần nhớ: buffer pool 128 MB, `max_connections` 151, `innodb_redo_log_capacity` 100 MB,
  slow log `OFF` với `long_query_time` 10 giây, binlog giữ 30 ngày, `innodb_dedicated_server` `OFF`.
- `innodb_dedicated_server` ở 8.4 tự tính buffer pool (theo RAM) và redo log capacity (theo số CPU,
  tối đa 16 GB).
- Chỉ số cốt lõi: QPS, latency p95/p99, `Threads_running`, buffer pool reads, replication lag, lock
  wait, history list length, đĩa. Counter phải tính theo tốc độ; gauge đọc thẳng.
- `sys.statement_analysis` cho biết câu nào tốn tổng thời gian nhất; `sys.waits_global_by_latency`
  cho biết server chờ gì; `sys.innodb_lock_waits` cho biết ai chặn ai.
- `KILL QUERY` dừng câu, giữ connection; `KILL` đóng connection và rollback transaction. Kill câu ghi
  lớn kéo theo rollback lâu.
- Kích thước bảng ở `information_schema.TABLES` là xấp xỉ và được cache; tăng trưởng cần chụp định kỳ.
- MySQL 8.0 hết extended support tháng 4/2026. Lên 8.4 LTS: kiểm `mysql_native_password`, đổi câu lệnh
  replication sang `SOURCE`/`REPLICA`, rà `my.cnf`, chạy Upgrade Checker, ưu tiên nâng cấp qua
  replication và chuẩn bị đường lui (không downgrade in-place được).
- Khi DB chậm: xác nhận và tìm thay đổi gần đây, rồi tài nguyên máy, tổng quan, processlist, lock,
  transaction dài, câu tốn nhất, wait; can thiệp từ nhẹ tới nặng; đừng restart theo phản xạ.

## Câu hỏi tự kiểm tra

1. Phân biệt system variable và status variable. `Max_used_connections` thuộc loại nào?
2. Vì sao sau `SET GLOBAL long_query_time = 1`, slow log vẫn không ghi các câu 3 giây của ứng dụng?
3. Bạn sửa `max_connections` trong `my.cnf`, restart, nhưng giá trị không đổi. Có những khả năng nào,
   và bạn kiểm tra bằng câu SQL nào?
4. Trên máy 16 GB RAM, 8 vCPU, chỉ chạy MySQL 8.4 với `innodb_dedicated_server = ON`, buffer pool và
   redo log capacity được đặt bao nhiêu?
5. Vì sao redo log quá nhỏ làm câu ghi chậm? Redo log lớn có nhược điểm gì?
6. `binlog_expire_logs_seconds` nên đặt dựa trên những yếu tố nào?
7. Counter và gauge khác nhau thế nào? Cho mỗi loại hai ví dụ.
8. Hit ratio 99% có chắc là tốt không? Nên nhìn thêm chỉ số nào?
9. Vì sao nên tối ưu theo `total_latency` thay vì `avg_latency`?
10. Một connection ở trạng thái `Sleep` 20 phút có thể gây hại gì? Làm sao phát hiện?
11. Khi nào dùng `KILL QUERY`, khi nào dùng `KILL CONNECTION`? Vì sao kill một câu `DELETE` lớn có thể
    không làm hệ thống nhẹ đi ngay?
12. Kể ba thay đổi của MySQL 8.4 có thể làm ứng dụng hoặc script vận hành vỡ sau nâng cấp từ 8.0.
13. Vì sao không nên restart server như bước đầu tiên khi DB chậm?

## Bài tập

1. **Kiểm kê cấu hình.** Trên container MySQL 8.4, liệt kê mọi biến có `VARIABLE_SOURCE` khác
   `COMPILED`. Sau đó `SET PERSIST` một biến, restart container, và chứng minh (bằng
   `variables_info` và `persisted_variables`) biến đó đến từ đâu. Cuối cùng xoá nó khỏi
   `mysqld-auto.cnf`.
2. **Tự đo QPS và hit ratio.** Viết một script (bash hoặc ngôn ngữ bạn chọn) đọc `Questions`,
   `Innodb_buffer_pool_reads`, `Innodb_buffer_pool_read_requests` mỗi 10 giây và in ra QPS và hit
   ratio **của khoảng 10 giây vừa qua** (không phải từ lúc khởi động). Tạo tải bằng cách chạy lặp một
   câu query trên một bảng vài trăm nghìn dòng, quan sát hai con số.
3. **Tái hiện và xử lý lock.** Làm lại timeline ở mục 3.7 với ba session. Ở session giám sát, tìm
   thủ phạm bằng `sys.innodb_lock_waits` và bằng join processlist với `INNODB_TRX`. Thử `KILL QUERY`
   rồi `KILL` connection thủ phạm; ghi lại kết quả của từng cách và giải thích.
4. **Câu tốn nhất.** Tạo một bảng 200.000 dòng không có index trên một cột lọc. `TRUNCATE` bảng digest,
   chạy một câu lọc theo cột đó 500 lần và một câu theo khoá chính 5.000 lần. Xem
   `sys.statement_analysis`: câu nào đứng đầu, `rows_examined_avg` bao nhiêu? Thêm index rồi lặp lại,
   so sánh.
5. **Theo dõi tăng trưởng.** Tạo bảng `ops.kich_thuoc_bang` như mục 6.2. Chụp lần 1, nạp thêm dữ liệu
   vào một bảng, chụp lần 2 (giả lập ngày khác bằng cách sửa cột `ngay`). Viết câu tính tăng trưởng.
   Thử chụp mà **không** đặt `information_schema_stats_expiry = 0` và giải thích kết quả.
6. **Chuẩn bị nâng cấp.** Trên một container MySQL 8.0, tạo một account dùng `mysql_native_password`
   và một script shell gọi `SHOW SLAVE STATUS`. Viết checklist nâng cấp lên 8.4 cho "hệ thống" này,
   gồm câu SQL phát hiện vấn đề và cách sửa từng mục. (Nếu có MySQL Shell, chạy thêm
   `util.checkForServerUpgrade()` và so với checklist của bạn.)
7. **Runbook.** Viết một runbook một trang cho đội của bạn: "DB chậm: làm gì trong 15 phút đầu", gồm
   các câu SQL cụ thể theo thứ tự, và tiêu chí để quyết định kill, failover hay chờ.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [Server System Variables](https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html) ·
  [Server Status Variables](https://dev.mysql.com/doc/refman/8.4/en/server-status-variables.html) ·
  [SET Syntax for Variable Assignment (SET PERSIST)](https://dev.mysql.com/doc/refman/8.4/en/set-variable.html) ·
  [Persisted System Variables](https://dev.mysql.com/doc/refman/8.4/en/persisted-system-variables.html) ·
  [Enabling Automatic Configuration for a Dedicated MySQL Server](https://dev.mysql.com/doc/refman/8.4/en/innodb-dedicated-server.html) ·
  [InnoDB Startup Options and System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html) ·
  [The Slow Query Log](https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html) ·
  [Binary Logging Options and Variables](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html) ·
  [MySQL Performance Schema](https://dev.mysql.com/doc/refman/8.4/en/performance-schema.html) ·
  [Statement Summary Tables](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-statement-summary-tables.html) ·
  [The processlist Table](https://dev.mysql.com/doc/refman/8.4/en/performance-schema-processlist-table.html) ·
  [MySQL sys Schema](https://dev.mysql.com/doc/refman/8.4/en/sys-schema.html) ·
  [KILL Statement](https://dev.mysql.com/doc/refman/8.4/en/kill.html) ·
  [The INFORMATION_SCHEMA TABLES Table](https://dev.mysql.com/doc/refman/8.4/en/information-schema-tables-table.html) ·
  [Checking Replication Status](https://dev.mysql.com/doc/refman/8.4/en/replication-administration-status.html)
- Nâng cấp:
  [MySQL Releases: Innovation and LTS](https://dev.mysql.com/doc/refman/8.4/en/mysql-releases.html) ·
  [What Is New in MySQL 8.4 since MySQL 8.0](https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html) ·
  [Upgrade Paths](https://dev.mysql.com/doc/refman/8.4/en/upgrade-paths.html) ·
  [Upgrade Best Practices](https://dev.mysql.com/doc/refman/8.4/en/upgrade-best-practices.html) ·
  [Changes in MySQL 8.4](https://dev.mysql.com/doc/refman/8.4/en/upgrading-from-previous-series.html) ·
  [Downgrading MySQL](https://dev.mysql.com/doc/refman/8.4/en/downgrading.html)
- Công cụ:
  [Prometheus mysqld_exporter](https://github.com/prometheus/mysqld_exporter) ·
  [Percona Monitoring and Management](https://docs.percona.com/percona-monitoring-and-management/) ·
  [Percona Toolkit (pt-heartbeat, pt-query-digest)](https://docs.percona.com/percona-toolkit/)
- PostgreSQL 18 docs:
  [The Cumulative Statistics System (pg_stat_activity)](https://www.postgresql.org/docs/18/monitoring-stats.html) ·
  [pg_stat_statements](https://www.postgresql.org/docs/18/pgstatstatements.html) ·
  [Server Signaling Functions](https://www.postgresql.org/docs/18/functions-admin.html)
- Google, *Site Reliability Engineering*, chương 6 "Monitoring Distributed Systems" (bốn tín hiệu
  vàng: latency, traffic, errors, saturation).
