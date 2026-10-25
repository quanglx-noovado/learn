# Chương 19. Database từ phía ứng dụng

> [← Mục lục](README.md) · [← Chương 18: Người dùng, phân quyền và bảo mật](18-user-quyen-bao-mat.md) · [Chương 20: Thay đổi schema an toàn →](20-thay-doi-schema-migration.md)

**Bạn sẽ học được:**

- Một câu SQL đi từ code ứng dụng tới MySQL qua những tầng nào, *connection* thật sự là gì và vì sao
  mở connection tốn kém.
- *Connection pool*: cơ chế, cách chọn kích thước pool (và vì sao pool to quá lại chậm hơn), vì sao
  PHP-FPM không có pool, khi nào cần proxy pool như ProxySQL, PgBouncer.
- *Prepared statement* nhìn từ phía server: server lưu gì, sống bao lâu, giới hạn gì.
- Viết transaction đúng từ ứng dụng: ranh giới, xử lý lỗi, *retry* khi deadlock hoặc serialization
  failure, và những gì không được đặt trong transaction.
- ORM (*Active Record* và *Data Mapper*), bài toán *N+1* và *eager loading*, đọc tập dữ liệu lớn theo
  lô hoặc theo luồng.
- Tách đọc/ghi (*read/write splitting*), vấn đề *read-your-writes*, và bản đồ các loại *timeout*.

**Cần biết trước:** [Chương 05](05-select-co-ban.md) (`SELECT`, `LIMIT`, `ORDER BY`),
[Chương 07](07-join.md) (JOIN), [Chương 11](11-index.md) (index), [Chương 13](13-transaction-acid.md)
(transaction), [Chương 14](14-isolation-mvcc.md) (isolation, MVCC), [Chương 15](15-lock-deadlock.md)
(lock, deadlock). Ví dụ PHP dùng PDO và Laravel; nếu chưa quen, đọc giáo trình PHP
[chương 16: PHP làm việc với database](../php/16-php-va-database.md) và
[chương 27: Database trong Laravel](../php/27-laravel-database-eloquent.md). Chương này nói từ phía
database: cùng các chủ đề đó nhưng trả lời câu hỏi "database thấy gì, chịu gì".

## 1. Bức tranh chung: một query đi từ ứng dụng tới database

### 1.1 Database là một server riêng

Từ chương 01 tới giờ, bạn gõ SQL trực tiếp vào client `mysql`. Trong thực tế, người gõ SQL là
*ứng dụng* (web app, queue worker, cron job), và giữa dòng code của bạn với MySQL có nhiều tầng:

```
 Code ứng dụng          $orders = Order::where('user_id', 7)->get();
      |                  (ORM / query builder sinh SQL có placeholder + danh sách giá trị)
      v
 Thư viện truy cập DB    PDO (PHP), JDBC (Java), database/sql (Go)
      |                  API chung cho mọi loại database
      v
 Driver                  pdo_mysql + mysqlnd, MySQL Connector/J, go-sql-driver/mysql
      |                  biết nói "giao thức MySQL"
      v
 Mạng                    TCP (hoặc Unix socket nếu cùng máy), có thể bọc TLS
      |
      v
 MySQL server            một thread phục vụ connection này: parse, tối ưu, thực thi, trả kết quả
```

Mỗi tầng có những mặc định riêng, và phần lớn sự cố "database chậm" trong thực tế không nằm ở câu SQL
mà nằm ở cách ứng dụng dùng database: mở quá nhiều connection, giữ transaction quá lâu, chạy hàng
trăm query nhỏ thay vì một query, đọc một triệu dòng vào RAM, không đặt timeout. Chương này đi qua
từng chuyện đó.

### 1.2 Round-trip: đơn vị chi phí bị quên nhiều nhất

Mỗi lần ứng dụng gửi một câu lệnh và chờ kết quả là một *round-trip* (một lượt đi và về qua mạng).
Ngay cả khi MySQL xử lý câu lệnh trong 0,05 ms (tra một dòng theo primary key, dữ liệu đã trong
buffer pool), ứng dụng vẫn phải trả thêm thời gian mạng hai chiều và thời gian driver đóng gói, giải
mã. Trong cùng một data center, thời gian mạng hai chiều thường cỡ vài trăm micro giây; qua vùng
(region) khác có thể lên hàng chục mili giây.

Ví dụ minh hoạ (số tròn để dễ tính, không phải số đo):

```
Giả sử mỗi round-trip tốn 0,5 ms (mạng + driver), mỗi query chạy trên server 0,1 ms.

  1 query lấy 500 dòng:        1 × (0,5 + 0,1)   ≈ 0,6 ms   (+ thời gian truyền 500 dòng)
  500 query, mỗi query 1 dòng: 500 × (0,5 + 0,1) ≈ 300 ms
```

Không query nào trong 500 query kia chậm: từng câu đều nhanh, không lên slow query log. Nhưng cộng lại
thì trang web chậm thấy rõ. Đây là gốc rễ của bài toán N+1 (mục 7), và là lý do bạn nên quen nghĩ theo
"request này tốn bao nhiêu round-trip" chứ không chỉ "query này chạy bao lâu".

### 1.3 Ai chịu trách nhiệm việc gì

| Việc | Database lo | Ứng dụng phải lo |
|---|---|---|
| Đúng dữ liệu khi nhiều người cùng ghi | Lock, MVCC, phát hiện deadlock (chương 13-15) | Chọn ranh giới transaction, retry khi bị huỷ |
| Số connection | Giới hạn bằng `max_connections`, từ chối khi vượt | Không mở quá giới hạn, dùng pool |
| Tốc độ một query | Optimizer, index (chương 11, 12) | Viết query dùng được index, không gửi query thừa |
| Chống SQL injection | Prepared statement tách code khỏi dữ liệu | Luôn dùng placeholder, không ghép chuỗi |
| Thời gian chờ tối đa | Một số timeout phía server (mục 10) | Đặt timeout ở client, quyết định làm gì khi hết giờ |
| Dữ liệu mới nhất khi có replica | Replication (chương 22) | Biết khi nào phải đọc từ primary (mục 9) |

### 1.4 Dữ liệu mẫu của chương

Các ví dụ SQL chạy trên MySQL 8.4. Nếu chưa có MySQL, chạy bằng Docker:

```bash
# Chạy trên máy của bạn (terminal thường)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi vài giây cho server khởi động xong, rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Rồi dán đoạn SQL sau vào client `mysql`:

```sql
DROP DATABASE IF EXISTS ch19;      -- database riêng của chương này
CREATE DATABASE ch19;
USE ch19;

-- Tài khoản: dùng cho ví dụ transaction, retry, deadlock (mục 5)
CREATE TABLE accounts (
  id      INT PRIMARY KEY,
  owner   VARCHAR(50) NOT NULL,
  balance DECIMAL(12,2) NOT NULL
);
INSERT INTO accounts VALUES (1, 'An', 1000.00), (2, 'Bình', 500.00);

-- Người dùng và bài viết: dùng cho N+1, eager loading (mục 6, 7)
CREATE TABLE users (
  id   INT PRIMARY KEY,
  name VARCHAR(50) NOT NULL
);
CREATE TABLE posts (
  id      INT PRIMARY KEY,
  user_id INT NOT NULL,
  title   VARCHAR(100) NOT NULL,
  INDEX idx_posts_user (user_id)
);
INSERT INTO users VALUES (1, 'An'), (2, 'Bình'), (3, 'Chi');
INSERT INTO posts VALUES
  (1, 1, 'Học SQL'), (2, 2, 'Học PHP'), (3, 1, 'Index là gì'),
  (4, 3, 'Deadlock'), (5, 2, 'Connection pool');

-- Đơn hàng: 100.000 dòng để thử đọc theo lô (mục 8)
SET SESSION cte_max_recursion_depth = 100000;   -- mặc định 1000, phải nới để sinh 100.000 dòng
CREATE TABLE orders (
  id      BIGINT PRIMARY KEY,
  user_id INT NOT NULL,
  status  VARCHAR(10) NOT NULL,
  total   DECIMAL(12,2) NOT NULL,
  INDEX idx_orders_status_id (status, id)
);
INSERT INTO orders (id, user_id, status, total)
WITH RECURSIVE seq (n) AS (
  SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 100000
)
SELECT n, 1 + n % 3, IF(n % 4 = 0, 'pending', 'paid'), (n % 1000) + 0.50 FROM seq;
```

Kiểm tra nhanh:

```sql
SELECT status, COUNT(*) FROM orders GROUP BY status ORDER BY status;
-- Kết quả mong đợi:
-- +---------+----------+
-- | status  | COUNT(*) |
-- +---------+----------+
-- | paid    |    75000 |
-- | pending |    25000 |
-- +---------+----------+
```

(`n % 4 = 0` đúng với 25.000 số trong 1..100.000, nên có 25.000 đơn `pending`.)

Ví dụ PHP trong chương là đoạn minh hoạ cách dùng với MySQL thật; chúng cần một MySQL server và
extension `pdo_mysql`. Cách dựng môi trường PHP + MySQL bằng Docker có ở
[giáo trình PHP, chương 16, mục 1.4](../php/16-php-va-database.md).

## 2. Driver và kết nối

### 2.1 Driver là gì

*Driver* là thư viện biết nói *giao thức mạng* (wire protocol) của một loại database cụ thể: đóng
câu SQL thành gói tin, gửi đi, đọc gói tin trả về và đổi thành giá trị của ngôn ngữ (int, string,
mảng...). MySQL và PostgreSQL có giao thức khác nhau, nên mỗi bên cần driver riêng.

Phía trên driver thường có một lớp API chung để code không phụ thuộc database:

| Ngôn ngữ | API chung | Driver MySQL | Driver PostgreSQL |
|---|---|---|---|
| PHP | PDO | `pdo_mysql` (chạy trên thư viện client `mysqlnd`) | `pdo_pgsql` |
| Java | JDBC | MySQL Connector/J | PgJDBC |
| Go | `database/sql` | `github.com/go-sql-driver/mysql` | `pgx` (có adapter cho `database/sql`) |

Bạn ít khi gọi driver trực tiếp, nhưng nhiều hành vi quan trọng là do driver quyết định: chế độ
prepared statement (mục 4), kéo toàn bộ kết quả về RAM hay đọc dần (mục 8), timeout (mục 10), có tự
kết nối lại hay không.

### 2.2 Connection là gì

*Connection* (kết nối) là một phiên làm việc giữa một client và server. Khi ứng dụng mở connection
tới MySQL, những việc sau xảy ra (đơn giản hoá):

```
Client                                           MySQL server
  |  ---- TCP SYN / SYN-ACK / ACK (bắt tay TCP) ---->|
  |  <--------------- gói "handshake" -------------- |  server gửi phiên bản, plugin xác thực, chuỗi ngẫu nhiên
  |  ---- (nếu dùng TLS) bắt tay TLS --------------> |
  |  ---- user, dữ liệu xác thực, database mặc định ->|
  |  <---------------------- OK -------------------- |  server gắn connection với một thread riêng
  |  ---- SET ... (driver/ORM cấu hình session) ----> |  ví dụ charset, sql_mode, time_zone
  |  ---- câu SQL đầu tiên của bạn ----------------> |
```

Trước khi câu SQL đầu tiên của bạn chạy, đã mất vài round-trip mạng, công xác thực mật khẩu (plugin
mặc định của MySQL 8.4 là `caching_sha2_password`), và nếu bật TLS thì thêm bắt tay TLS. Trong cùng
data center, tổng chi phí này thường ở mức mili giây; với một request web chỉ chạy vài query nhỏ, mở
connection có thể tốn hơn chính các query.

Phía server, MySQL dùng mô hình *thread per connection*: tài liệu MySQL 8.4 (mục Connection
Interfaces) ghi mỗi client connection được gắn với một thread riêng, lo xác thực và xử lý mọi câu
lệnh của connection đó. Có bao nhiêu client đang kết nối thì có bấy nhiêu thread. Để đỡ chi phí tạo
thread, MySQL giữ một *thread cache* (`thread_cache_size`, mặc định tự tính lúc khởi động): connection
đóng thì thread quay về cache, connection mới lấy lại dùng.

PostgreSQL còn nặng hơn: mỗi connection là một *process* hệ điều hành riêng (backend process). Đây là
lý do proxy pool như PgBouncer gần như là tiêu chuẩn với Postgres (mục 3.6).

### 2.3 Session state: connection mang theo trạng thái

Connection không chỉ là một đường ống. Nó mang theo *trạng thái phiên* (session state), tức những
thứ chỉ tồn tại trong connection đó:

- Biến hệ thống cấp session: `SET SESSION sql_mode = ...`, `time_zone`, `transaction_isolation`,
  charset (`SET NAMES`).
- Biến người dùng: `SET @x = 1`.
- Transaction đang mở và các lock nó giữ, lock bảng (`LOCK TABLES`), lock tên (`GET_LOCK()`).
- Bảng tạm (`CREATE TEMPORARY TABLE`), prepared statement đã tạo (mục 4).
- Kết quả `LAST_INSERT_ID()`.

Ví dụ thấy được trong client `mysql`, mở hai cửa sổ (hai connection):

```sql
-- Connection A
SET @gio = 'A đặt';
SELECT @gio;                       -- 'A đặt'

-- Connection B
SELECT @gio;                       -- NULL: B không thấy biến của A
```

Điều này rất quan trọng khi connection được dùng lại cho nhiều việc khác nhau (pool, persistent
connection, proxy): trạng thái của người dùng trước có thể rò sang người sau. MySQL có lệnh giao thức
*reset connection* (hàm C API `mysql_reset_connection()`): theo tài liệu C API 8.4, nó rollback
transaction đang mở và reset autocommit, nhả lock bảng và lock `GET_LOCK()`, xoá bảng tạm, đưa biến
session về giá trị global, xoá biến người dùng, giải phóng prepared statement, đặt `LAST_INSERT_ID()`
về 0. Nó làm việc đó mà không đóng connection và không xác thực lại, nên rẻ hơn mở connection mới.
Một số pool và proxy dùng cơ chế này khi trả connection về pool; không phải pool nào cũng làm, cần
đọc tài liệu của pool bạn dùng.

### 2.4 Giới hạn số connection: `max_connections`

Vì mỗi connection tốn một thread và bộ nhớ (stack của thread, các buffer cấp phát theo session khi
query cần như sort buffer, join buffer), server phải giới hạn số connection đồng thời:

- MySQL: `max_connections`, mặc định **151**. Thực tế MySQL cho phép `max_connections + 1`: slot thừa
  để dành cho tài khoản có quyền `CONNECTION_ADMIN`, để quản trị viên vẫn vào được chẩn đoán khi
  connection thường đã đầy. Vượt giới hạn, client nhận lỗi 1040 `Too many connections`.
- PostgreSQL: `max_connections`, tài liệu ghi mặc định thường là 100, chỉ đổi được khi khởi động lại
  server; một phần slot được giữ cho superuser (`superuser_reserved_connections`).

Theo dõi trên MySQL:

```sql
SHOW GLOBAL STATUS LIKE 'Threads_connected';      -- số connection đang mở
SHOW GLOBAL STATUS LIKE 'Threads_running';        -- số connection đang thực sự chạy câu lệnh
SHOW GLOBAL STATUS LIKE 'Max_used_connections';   -- đỉnh cao nhất từ lúc khởi động
SHOW GLOBAL STATUS LIKE 'Connection_errors_max_connections';  -- số lần từ chối vì đầy
SHOW PROCESSLIST;                                  -- từng connection: user, host, đang làm gì, bao lâu
```

Một hệ thống khoẻ thường có `Threads_connected` vài trăm nhưng `Threads_running` chỉ vài chục: phần
lớn connection đang rảnh (chờ ứng dụng gửi câu tiếp theo). Khi `Threads_running` tăng vọt, server
đang quá tải hoặc có nhiều câu đang chờ lock.

⚠️ Tăng `max_connections` thật lớn không phải cách chữa. Tài liệu MySQL ghi tăng giá trị này làm tăng
số file descriptor cần dùng, và mỗi connection tốn RAM; nhiều connection cùng *chạy* một lúc còn làm
server chậm đi vì tranh CPU, lock nội bộ (mục 3.3). Cách chữa đúng là giảm số connection ứng dụng mở
ra, hoặc gom chúng qua pool.

## 3. Connection pool

### 3.1 Pool là gì, vì sao cần

*Connection pool* (bể kết nối) là một tập connection được mở sẵn và dùng chung. Khi code cần chạy
query, nó *mượn* một connection rảnh trong pool, chạy xong thì *trả lại* chứ không đóng. Người mượn
sau dùng tiếp connection đó.

```
  Request 1 ─┐                          ┌── conn #1 ──┐
  Request 2 ─┼──▶  [ Pool: 3 connection ] ┼── conn #2 ──┼──▶ MySQL
  Request 3 ─┤      mượn ─ dùng ─ trả    └── conn #3 ──┘
  Request 4 ─┘  (chờ tới khi có conn rảnh, hoặc hết thời gian chờ thì báo lỗi)
```

Pool giải quyết hai việc:

1. Bỏ chi phí mở connection cho mỗi lần dùng (mục 2.2).
2. Giới hạn số connection tới database: dù có 1.000 request đồng thời, database chỉ thấy đúng số
   connection của pool. Request dư phải xếp hàng ở phía ứng dụng, chỗ rẻ hơn nhiều so với xếp hàng
   trong database.

Các tham số thường gặp của một pool:

| Tham số | Ý nghĩa | Ví dụ tên thật |
|---|---|---|
| Kích thước tối đa | Số connection nhiều nhất pool được mở | HikariCP `maximumPoolSize` (mặc định 10); Go `SetMaxOpenConns` (mặc định không giới hạn) |
| Số connection rảnh giữ lại | Giữ sẵn bao nhiêu connection lúc vắng | HikariCP `minimumIdle`; Go `SetMaxIdleConns` (mặc định 2) |
| Thời gian chờ mượn | Chờ connection rảnh tối đa bao lâu rồi báo lỗi | HikariCP `connectionTimeout` (mặc định 30 giây) |
| Tuổi thọ tối đa | Đóng và mở lại connection sau một thời gian | HikariCP `maxLifetime` (mặc định 30 phút); Go `SetConnMaxLifetime` (mặc định không giới hạn) |
| Thời gian rảnh tối đa | Đóng connection rảnh quá lâu | HikariCP `idleTimeout` (mặc định 10 phút); Go `SetConnMaxIdleTime` |

⚠️ Tuổi thọ tối đa của pool phải **ngắn hơn** mọi giới hạn phía server và hạ tầng (ví dụ
`wait_timeout` của MySQL, timeout của load balancer, firewall). Tài liệu HikariCP khuyến nghị
`maxLifetime` ngắn hơn vài giây so với giới hạn đó. Nếu ngược lại, server đã đóng connection mà pool
vẫn tưởng còn sống, người mượn tiếp theo nhận lỗi "MySQL server has gone away" hoặc "Lost connection".

⚠️ Go: `SetMaxOpenConns` mặc định là không giới hạn. Tài liệu Go ghi `sql.DB` sẽ mở connection mới bất
cứ khi nào mọi connection hiện có đang bận. Một đợt traffic đột biến có thể mở hàng trăm connection
và chạm `max_connections`. Luôn đặt giới hạn này trong production.

### 3.2 Định luật Little: cần bao nhiêu connection

Số connection *thực sự bận* cùng lúc được tính bằng *định luật Little* (Little's law):

```
số connection bận trung bình = số lần mượn mỗi giây × thời gian giữ connection mỗi lần
```

Ví dụ: ứng dụng chạy 2.000 transaction mỗi giây, mỗi transaction giữ connection 5 ms:

```
2.000 × 0,005 = 10 connection bận trung bình
```

Pool 15-20 connection đã đủ, có dư cho dao động. Nếu một bug làm mỗi transaction giữ connection
500 ms (ví dụ gọi API bên ngoài trong lúc transaction đang mở), cùng tải đó cần 1.000 connection: pool
cạn, request xếp hàng, timeout dây chuyền. Bài học: muốn ít connection, hãy **giữ connection ngắn**,
không phải mở pool to ra.

### 3.3 Pool to hơn không nhanh hơn

Trực giác bảo "nhiều connection thì xử lý được nhiều việc song song hơn". Sai, vì database có tài
nguyên hữu hạn: số lõi CPU, băng thông đĩa, các lock nội bộ. Khi số câu lệnh chạy đồng thời vượt
quá khả năng đó, chúng chỉ tranh nhau: hệ điều hành chuyển ngữ cảnh liên tục, các câu tranh mutex và
lock của InnoDB, cache CPU bị xáo trộn. Thông lượng (số câu xong mỗi giây) đứng yên hoặc giảm, còn
thời gian của từng câu tăng.

Bài "About Pool Sizing" của HikariCP trích một công thức do cộng đồng PostgreSQL đưa ra làm **điểm
xuất phát**:

```
số connection ≈ (số lõi CPU × 2) + effective_spindle_count
```

`effective_spindle_count` là số đĩa quay "hiệu dụng": bằng 0 nếu dữ liệu nóng nằm gọn trong RAM. Ví dụ
máy database 8 lõi, dữ liệu nằm trong buffer pool: khoảng 16-17 connection *đang chạy* là vùng hiệu quả.
Bài viết cũng nhấn mạnh: đây chỉ là điểm bắt đầu, phải đo bằng tải thử thực tế; SSD ít chặn I/O hơn
nên càng không cần nhiều connection hơn.

Ý chính cần nhớ: một pool nhỏ, luôn bận, với ứng dụng xếp hàng chờ ở phía trước, thường cho thông
lượng tốt hơn một pool khổng lồ.

⚠️ Con số trên là tổng số connection *đang chạy* trên database, cộng từ mọi instance ứng dụng. 20
instance mỗi instance pool 20 là 400 connection tiềm năng, dù mỗi pool trông có vẻ nhỏ:

```
tổng connection tối đa = số instance × pool mỗi instance  (+ cron, worker, công cụ admin)
                       phải < max_connections, và nên xa hơn một khoảng dự phòng
```

⚠️ *Pool deadlock*: nếu một luồng xử lý giữ một connection rồi cố mượn thêm connection thứ hai (ví dụ
mở transaction rồi gọi một hàm dùng connection khác), khi pool cạn mọi luồng đều giữ một và chờ thêm
một, không ai trả. Tránh bằng cách mỗi đơn vị công việc chỉ dùng một connection.

### 3.4 PHP-FPM không có pool

Java và Go chạy một process sống lâu, nên pool nằm trong process đó và được mọi thread/goroutine dùng
chung. PHP-FPM khác: mỗi *worker* là một process riêng, xử lý một request tại một thời điểm, và
connection mở trong request bị đóng khi request kết thúc (giáo trình PHP,
[chương 16, mục 10.1](../php/16-php-va-database.md)). Không có pool dùng chung giữa các worker.

Hệ quả:

```
tổng connection tối đa ≈ số máy web × pm.max_children × số connection mỗi request
                         + queue worker + cron + công cụ admin, monitoring

Ví dụ: 4 máy × 50 children × 1 + 10 queue worker + 5 khác = 215  >  151 (mặc định max_connections)
```

- Mỗi request mở connection mới: trả chi phí mở connection mỗi request (mục 2.2).
- Số connection tỉ lệ với số worker đang bận, không tỉ lệ với số query. Autoscale thêm máy web là thêm
  connection; database có thể hết connection trước khi app kịp chậm.
- Nếu app tách đọc/ghi (mục 9), một request có thể mở hai connection.

Các lựa chọn:

| Cách | Ý tưởng | Lưu ý |
|---|---|---|
| Giới hạn `pm.max_children` theo `max_connections` | Tính ngược từ giới hạn của DB | Đơn giản, nhưng giới hạn luôn cả khả năng phục vụ request không cần DB |
| Persistent connection (`PDO::ATTR_PERSISTENT`) | Worker giữ connection qua các request | Trạng thái session rò sang request sau; worker rảnh vẫn giữ connection. Chi tiết: [PHP chương 16, mục 10.2](../php/16-php-va-database.md) |
| Runtime sống lâu (Laravel Octane trên Swoole, RoadRunner, FrankenPHP) | App boot một lần, connection sống qua nhiều request | Cùng rủi ro rò trạng thái; mỗi worker vẫn giữ connection riêng, không phải pool dùng chung |
| Proxy pool (ProxySQL, PgBouncer) | Một tiến trình đứng giữa app và DB, gom nhiều connection client vào ít connection server | Cách phổ biến nhất khi số worker lớn; mục 3.5, 3.6 |

### 3.5 Proxy pool cho MySQL: ProxySQL

*ProxySQL* là một proxy nói giao thức MySQL. Ứng dụng kết nối tới ProxySQL như tới một MySQL bình
thường; ProxySQL giữ một pool connection tới MySQL thật phía sau. Tính năng chính:

- *Multiplexing*: nhiều connection phía client dùng chung một connection phía backend, mỗi câu lệnh
  có thể đi trên một connection backend khác nhau. 1.000 connection PHP có thể chỉ cần vài chục
  connection thật tới MySQL.
- Định tuyến câu lệnh theo luật (query rules): ví dụ `SELECT` sang replica, còn lại sang primary
  (mục 9).
- Theo dõi sức khoẻ backend, chuyển hướng khi một server bị đánh dấu offline.

Multiplexing chỉ an toàn khi connection không mang trạng thái riêng. Tài liệu ProxySQL liệt kê các
trường hợp nó **tắt** multiplexing cho connection đó (gắn client với một backend cố định):

- Đang có transaction: tắt cho tới khi commit hoặc rollback.
- `LOCK TABLES`: tắt cho tới `UNLOCK TABLES`.
- Dùng `GET_LOCK()`, câu có biến `@...`, `SQL_CALC_FOUND_ROWS`, `CREATE TEMPORARY TABLE`, hoặc lệnh
  SQL `PREPARE` (prepared statement dạng text): tắt luôn, **không bật lại** trên connection đó.

Nghĩa là ứng dụng dùng nhiều biến session hay bảng tạm sẽ mất phần lớn lợi ích của multiplexing. Tài
liệu cũng cảnh báo về `LAST_INSERT_ID()`: nếu câu lấy id chạy trên một backend khác với câu `INSERT`,
kết quả sai; ProxySQL có tham số trì hoãn multiplexing sau câu có auto increment để giảm rủi ro này.
Driver thường lấy id vừa sinh từ gói OK trả về của chính câu `INSERT`, nên `lastInsertId()` của PDO
không phải gửi thêm câu `SELECT LAST_INSERT_ID()`.

### 3.6 Proxy pool cho PostgreSQL: PgBouncer

Với Postgres, mỗi connection là một process, nên thêm connection còn đắt hơn MySQL. *PgBouncer* là
proxy pool nhẹ, có ba chế độ (`pool_mode`):

| Chế độ | Connection server được trả về pool khi | Tương thích |
|---|---|---|
| `session` (mặc định) | Client ngắt kết nối | Mọi tính năng Postgres; nhưng chỉ đỡ chi phí mở connection, không giảm số connection đang giữ |
| `transaction` | Transaction kết thúc | Phổ biến nhất; làm hỏng các tính năng dựa vào session |
| `statement` | Mỗi câu lệnh xong | Cấm transaction nhiều câu |

Ở chế độ `transaction`, bảng tương thích trong tài liệu PgBouncer ghi các tính năng **không** dùng
được: `SET`/`RESET` (thiết lập session), `LISTEN`, cursor `WITH HOLD`, lệnh SQL `PREPARE`/`DEALLOCATE`,
bảng tạm kiểu giữ qua transaction, advisory lock cấp session. Prepared statement ở mức giao thức thì
dùng được từ khi bật `max_prepared_statements` khác 0 (PgBouncer theo dõi và chuẩn bị lại statement
trên connection server mà client đang được gán).

Quy tắc chung cho mọi proxy pool kiểu transaction: **coi như mỗi transaction chạy trên một connection
khác nhau**. Mọi thiết lập cần cho câu lệnh phải nằm trong chính transaction đó (Postgres có
`SET LOCAL`, chỉ có hiệu lực tới hết transaction).

### 3.7 Đối chiếu Java, Go, PHP

| | Java (HikariCP) | Go (`database/sql`) | PHP-FPM (PDO) |
|---|---|---|---|
| Pool nằm ở đâu | Trong process JVM | Trong `sql.DB` của process | Không có; mỗi request một connection |
| Mặc định kích thước | 10 | Không giới hạn mở; giữ 2 rảnh | 1 connection mỗi worker đang bận |
| Mượn/trả | `getConnection()` / `close()` trả về pool | Tự động mỗi `Query`/`Exec`; `Tx` giữ một connection tới khi commit/rollback | Mở khi `new PDO`, đóng cuối request |
| Giảm connection khi nhiều instance | Giảm pool mỗi instance, hoặc proxy | Như Java | Proxy pool |

⚠️ Go: `*sql.Rows` chưa `Close()` (hoặc chưa đọc hết) thì connection chưa được trả về pool. Quên
`defer rows.Close()` là cách phổ biến nhất làm cạn pool trong Go. Java tương tự với `Connection`,
`ResultSet` không đóng (dùng try-with-resources).

## 4. Prepared statement nhìn từ phía server

### 4.1 Nhắc lại: prepared statement là gì

*Prepared statement* tách câu SQL thành hai phần: khuôn câu lệnh có chỗ trống (`?`) và các giá trị
gửi riêng. Hai lợi ích, theo tài liệu MySQL 8.4 (mục Prepared Statements):

1. Bớt chi phí parse khi cùng một khuôn câu chạy nhiều lần với giá trị khác nhau.
2. Chống *SQL injection*: giá trị không bao giờ trở thành một phần cú pháp SQL, nên chuỗi
   `' OR 1=1 --` chỉ là dữ liệu.

Cách dùng từ PHP (prepare, bind, execute, emulated và native prepare) đã có ở giáo trình PHP,
[chương 16, mục 3.3-3.5](../php/16-php-va-database.md). Mục này nhìn từ phía MySQL.

### 4.2 Hai cách gửi câu lệnh: text protocol và binary protocol

```
Không prepare (text protocol, COM_QUERY):
  client ── "SELECT * FROM users WHERE id = 7" ──▶ server: parse, tối ưu, chạy

Native prepare (binary protocol):
  client ── COM_STMT_PREPARE "SELECT * FROM users WHERE id = ?" ──▶ server: parse, tạo statement, trả id
  client ── COM_STMT_EXECUTE (id, giá trị 7 dạng nhị phân)        ──▶ server: chạy
  client ── COM_STMT_EXECUTE (id, giá trị 9)                      ──▶ server: chạy
  client ── COM_STMT_CLOSE (id)                                   ──▶ server: giải phóng
```

*Emulated prepare* (mặc định của `pdo_mysql` thuần) thực chất dùng text protocol: driver tự escape
giá trị rồi ghép thành câu SQL hoàn chỉnh. Server không hề biết có prepared statement. Laravel đặt
`PDO::ATTR_EMULATE_PREPARES => false` nên dùng native prepare.

Bạn cũng có thể thử prepared statement bằng chính SQL trong client `mysql` (giao diện này kém hiệu quả
hơn binary protocol, tài liệu MySQL khuyên dùng để thử nghiệm và gỡ lỗi):

```sql
USE ch19;
PREPARE lay_bai FROM 'SELECT id, title FROM posts WHERE user_id = ? ORDER BY id';
SET @u = 1;
EXECUTE lay_bai USING @u;
-- +----+-------------+
-- | id | title       |
-- +----+-------------+
-- |  1 | Học SQL     |
-- |  3 | Index là gì |
-- +----+-------------+
SET @u = 2;
EXECUTE lay_bai USING @u;          -- trả bài 2 'Học PHP' và 5 'Connection pool'
DEALLOCATE PREPARE lay_bai;
```

### 4.3 Server lưu gì, sống bao lâu

Theo tài liệu MySQL 8.4 (Caching of Prepared Statements and Stored Programs):

- Khi prepare, server chuyển câu lệnh thành một cấu trúc nội bộ và giữ lại để các lần execute sau
  dùng tiếp.
- Cache này **thuộc về session**. Session khác không dùng được; session kết thúc thì mọi prepared
  statement của nó bị huỷ. Đây là lý do proxy pool phải xử lý prepared statement đặc biệt (mục 3.5,
  3.6).
- Nếu bảng mà statement dùng bị đổi metadata (DDL như `ALTER TABLE`, `TRUNCATE`, hoặc bảng bị đẩy ra
  khỏi table definition cache), server tự *reprepare* ở lần execute tiếp theo. Ví dụ tài liệu nêu:
  `SELECT *` đã được mở rộng thành danh sách cột lúc prepare, thêm cột thì phải prepare lại mới đúng.
  Số lần reprepare đếm ở biến trạng thái `Com_stmt_reprepare`.
- Tổng số prepared statement trên toàn server (cộng mọi session) bị giới hạn bởi
  `max_prepared_stmt_count`, mặc định **16382**. Đặt 0 là tắt prepared statement.

⚠️ Rò prepared statement: nếu code prepare liên tục mà không đóng statement, trên connection sống lâu
(persistent connection, pool, worker chạy lâu), số statement tăng dần tới khi chạm
`max_prepared_stmt_count`. Lúc đó **mọi** session trên server đều không prepare được nữa, kể cả các
ứng dụng không có lỗi. Theo dõi:

```sql
SHOW GLOBAL STATUS LIKE 'Prepared_stmt_count';                 -- số statement đang tồn tại
SHOW GLOBAL STATUS WHERE Variable_name IN ('Com_stmt_prepare', 'Com_stmt_close');
-- Com_stmt_prepare tăng đều mà Com_stmt_close đứng yên là dấu hiệu rò
```

Trong PHP, statement được đóng khi object `PDOStatement` bị huỷ (hết tham chiếu); vấn đề thường xuất
hiện khi code giữ statement trong mảng cache không giới hạn.

### 4.4 Prepared statement và kế hoạch thực thi

MySQL và PostgreSQL khác nhau ở chỗ này:

- MySQL: tài liệu chỉ nêu lợi ích là bớt chi phí parse và chuyển đổi câu lệnh. Kiểu của tham số được
  xác định một lần lúc prepare (tài liệu PREPARE Statement có cả bảng quy tắc suy kiểu).
- PostgreSQL: một prepared statement có thể chạy bằng *custom plan* (lập kế hoạch mới theo giá trị
  tham số mỗi lần) hoặc *generic plan* (một kế hoạch dùng cho mọi giá trị). Tài liệu PostgreSQL 18 ghi
  quy tắc mặc định (`plan_cache_mode = auto`): năm lần execute đầu dùng custom plan, sau đó lập thử
  generic plan và dùng nó nếu chi phí ước tính không cao hơn nhiều so với trung bình custom plan.

⚠️ Bẫy của generic plan ở Postgres: với dữ liệu lệch (ví dụ 99% đơn hàng là `paid`, 1% là
`pending`), kế hoạch tốt cho `status = 'pending'` (dùng index) khác hẳn kế hoạch tốt cho
`status = 'paid'` (quét bảng). Một generic plan phải chọn một trong hai, nên có thể chậm cho một số giá
trị. Triệu chứng: "query chạy tay thì nhanh, chạy từ app thì chậm, và chỉ chậm từ lần thứ sáu". Có thể
đặt `plan_cache_mode = force_custom_plan` cho session hoặc cho riêng câu đó, và xem kế hoạch bằng
`EXPLAIN EXECUTE ten(gia_tri)`.

### 4.5 Placeholder không thay được mọi thứ

Placeholder chỉ đứng thay cho **giá trị**. Không dùng được cho:

- Tên bảng, tên cột, từ khoá: `ORDER BY ?` không sắp xếp theo cột có tên đó mà sắp theo một hằng số
  (mọi dòng bằng nhau). Riêng PDO với emulated prepare mà bind số nguyên thì câu thành `ORDER BY 2`,
  tức sắp theo *vị trí* cột thứ hai, cũng không phải điều bạn muốn. Tên cột, hướng sắp xếp lấy từ input
  phải kiểm bằng *whitelist* (danh sách cho phép) trong code.
- Một danh sách có độ dài thay đổi: `WHERE id IN (?)` chỉ nhận một giá trị. Phải sinh đủ số dấu `?`
  theo số phần tử (ORM làm việc này cho bạn). Danh sách rất dài sinh câu SQL rất dài; giao thức native
  prepare của MySQL giới hạn 65.535 placeholder mỗi câu, nên mảng hàng chục nghìn id nên chia lô
  (mục 8) hoặc ghi vào bảng tạm rồi JOIN.

`LIMIT ?` thì dùng được với prepared statement (tài liệu MySQL ghi rõ). Riêng PDO với emulated prepare
có bẫy: giá trị bind mặc định dạng chuỗi nên thành `LIMIT '10'` và lỗi cú pháp; dùng
`bindValue(..., PDO::PARAM_INT)` hoặc native prepare.

## 5. Transaction từ phía ứng dụng

Chương 13-15 giải thích transaction, isolation, lock từ phía database. Mục này trả lời câu hỏi của
người viết ứng dụng: đặt `BEGIN`/`COMMIT` ở đâu, xử lý lỗi thế nào, và khi nào được chạy lại.

### 5.1 Ranh giới transaction thuộc về ứng dụng

Database không biết "một thao tác nghiệp vụ" gồm những câu nào; chỉ ứng dụng biết. Chuyển tiền gồm
trừ tài khoản A, cộng tài khoản B, ghi sổ: ba câu này phải nằm trong **một** transaction. Nếu không
mở transaction, MySQL chạy ở chế độ *autocommit*: mỗi câu là một transaction riêng, commit ngay, và
lỗi ở câu thứ hai để lại dữ liệu nửa vời.

```php
<?php
declare(strict_types=1);

// Cần MySQL thật và bảng accounts ở mục 1.4. $pdo tạo như giáo trình PHP chương 16, mục 2.5.
function chuyenTien(PDO $pdo, int $tu, int $den, string $soTien): void
{
    $pdo->beginTransaction();
    try {
        $tru = $pdo->prepare('UPDATE accounts SET balance = balance - ? WHERE id = ? AND balance >= ?');
        $tru->execute([$soTien, $tu, $soTien]);
        if ($tru->rowCount() !== 1) {
            throw new DomainException('Không đủ số dư hoặc không có tài khoản');
        }
        $cong = $pdo->prepare('UPDATE accounts SET balance = balance + ? WHERE id = ?');
        $cong->execute([$soTien, $den]);
        if ($cong->rowCount() !== 1) {
            throw new DomainException('Không có tài khoản nhận');
        }
        $pdo->commit();
    } catch (Throwable $e) {
        if ($pdo->inTransaction()) {
            $pdo->rollBack();
        }
        throw $e;
    }
}
```

Hai chi tiết trong ví dụ:

- `UPDATE ... SET balance = balance - ? WHERE ... AND balance >= ?` đưa phép kiểm tra vào chính câu
  SQL, nên không có khoảng hở giữa "đọc số dư" và "ghi số dư" (lost update, chương 14).
- ⚠️ `rowCount()` của MySQL mặc định đếm số dòng **thực sự thay đổi**, không phải số dòng khớp `WHERE`.
  `UPDATE ... SET x = 5` trên dòng đã có `x = 5` trả 0. Ở ví dụ trên giá trị luôn đổi (số tiền
  khác 0) nên không sao; nhưng đừng dùng `rowCount() === 0` để kết luận "không tìm thấy dòng" khi giá
  trị mới có thể trùng giá trị cũ. (`pdo_mysql` có tuỳ chọn `MYSQL_ATTR_FOUND_ROWS` để đếm dòng khớp.)

### 5.2 Giữ transaction ngắn

Một transaction đang mở giữ lock trên các dòng đã ghi (và đã `SELECT ... FOR UPDATE`) cho tới khi kết
thúc, giữ một connection (mục 3.2), và với InnoDB còn giữ một *read view* khiến undo log cũ chưa được
dọn (chương 16). Transaction càng dài thì càng nhiều request khác phải chờ, càng dễ deadlock.

Những thứ **không** được đặt bên trong transaction:

| Việc | Vì sao |
|---|---|
| Gọi API bên ngoài (cổng thanh toán, gửi email, HTTP tới service khác) | Có thể mất hàng giây; lock và connection bị giữ suốt thời gian đó. Rollback không thu hồi được email đã gửi |
| Chờ người dùng (mở transaction ở request này, commit ở request sau) | Không làm được với PHP-FPM, và không bao giờ nên làm. Dùng optimistic lock với cột version (chương 15) |
| Xử lý nặng ở ứng dụng (resize ảnh, sinh PDF) | Tính xong rồi mới mở transaction để ghi |
| Đọc hàng triệu dòng để xử lý dần | Giữ read view rất lâu; chia lô, mỗi lô một transaction (mục 8) |

Mẫu đúng: chuẩn bị mọi thứ ở ngoài, mở transaction, chạy vài câu SQL, commit, rồi mới làm tác dụng
phụ bên ngoài (gửi email, đẩy job vào queue). Laravel có `DB::afterCommit()` và
`dispatch(...)->afterCommit()` cho đúng mục đích này; bug "dispatch job bên trong transaction" có
timeline đầy đủ ở giáo trình PHP, [chương 27, mục 11.3](../php/27-laravel-database-eloquent.md).

### 5.3 Lỗi trong transaction: cái gì bị rollback?

Không phải lỗi nào cũng rollback cả transaction. Tài liệu MySQL 8.4 (InnoDB Error Handling) ghi:

| Lỗi | Mã MySQL / SQLSTATE | InnoDB rollback gì |
|---|---|---|
| Deadlock | 1213 / `40001` | **Cả transaction** |
| Lock wait timeout | 1205 / `HY000` | Chỉ **câu lệnh** đang chờ (trừ khi bật `innodb_rollback_on_timeout`) |
| Trùng khoá (duplicate key) | 1062 / `23000` | Chỉ câu lệnh |
| Phần lớn lỗi khác (phát hiện ở tầng SQL) | | Chỉ câu lệnh |

⚠️ Điều nguy hiểm ở dòng thứ hai: sau lock wait timeout, transaction **vẫn mở**, các câu trước đó
vẫn còn hiệu lực, và tài liệu ghi rõ lock không được nhả khi chỉ rollback một câu. Nếu code bắt lỗi rồi
chạy tiếp và commit, bạn commit một transaction thiếu một câu. Quy tắc an toàn cho ứng dụng: **gặp bất
kỳ lỗi nào trong transaction thì rollback cả transaction**, rồi quyết định có chạy lại hay không. Mẫu
`try { ... commit } catch { rollBack; throw }` ở mục 5.1 làm đúng điều này.

PostgreSQL đơn giản hơn: một câu lỗi làm cả transaction rơi vào trạng thái hỏng, mọi câu sau đó bị từ
chối với lỗi "current transaction is aborted, commands ignored until end of transaction block" cho
tới khi `ROLLBACK` (hoặc rollback về một savepoint).

### 5.4 Retry: lỗi nào được chạy lại

Tài liệu MySQL nói deadlock và lock wait timeout là chuyện **bình thường** trên server bận, ứng dụng
phải sẵn sàng chạy lại. Ở PostgreSQL với mức `REPEATABLE READ` và `SERIALIZABLE`, lỗi
*serialization failure* (`40001`) là một phần thiết kế: database huỷ transaction thay vì để xảy ra
anomaly, và ứng dụng *bắt buộc* phải retry (chương 14).

| Lỗi | Retry được? | Ghi chú |
|---|---|---|
| MySQL deadlock (1213, `40001`) | Có, chạy lại cả transaction | Transaction đã bị rollback hết |
| MySQL lock wait timeout (1205) | Có thể, sau khi rollback cả transaction | Có thể là dấu hiệu một transaction khác giữ lock quá lâu; retry mãi không giải quyết gốc |
| Postgres serialization failure (`40001`), deadlock (`40P01`) | Có, chạy lại cả transaction | |
| Mất kết nối (2006, 2013) giữa transaction | Cẩn thận (mục 5.6) | Nếu mất trước `COMMIT`: transaction đã bị huỷ, chạy lại được. Nếu mất **trong lúc** `COMMIT`: không biết đã commit hay chưa |
| Duplicate key, vi phạm ràng buộc, lỗi cú pháp | Không | Chạy lại vẫn lỗi y như cũ |

Ba quy tắc khi retry:

1. **Chạy lại cả transaction từ câu đầu tiên**, kể cả các câu `SELECT`. Lần chạy mới phải đọc lại dữ
   liệu mới nhất; dùng lại giá trị đã đọc ở lần trước là tự tạo ra lost update.
2. **Chỉ retry ở transaction ngoài cùng.** Deadlock huỷ cả transaction, savepoint bên trong cũng mất.
   Laravel làm đúng như vậy: ở transaction lồng nhau, nó không retry mà ném lỗi ra lớp ngoài.
3. **Giới hạn số lần và chờ ngắt quãng có ngẫu nhiên** (*backoff* với *jitter*). Hai transaction vừa
   deadlock nhau mà retry ngay cùng lúc thì dễ đụng nhau lần nữa; chờ một khoảng ngẫu nhiên tăng dần
   làm chúng lệch nhau.

```php
<?php
declare(strict_types=1);

/**
 * Chạy $viec trong transaction, chạy lại khi gặp lỗi tranh chấp tạm thời.
 * Cần MySQL thật; minh hoạ cách phân loại lỗi, không phải thư viện hoàn chỉnh.
 *
 * @template T
 * @param callable(PDO): T $viec   chỉ được thao tác database, không gửi email/gọi API
 * @return T
 */
function trongTransactionCoRetry(PDO $pdo, callable $viec, int $soLanToiDa = 3): mixed
{
    for ($lan = 1; ; $lan++) {
        $pdo->beginTransaction();
        try {
            $ketQua = $viec($pdo);
            $pdo->commit();
            return $ketQua;
        } catch (PDOException $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();                       // luôn rollback cả transaction (mục 5.3)
            }
            $maMySql = $e->errorInfo[1] ?? null;        // 1213 deadlock, 1205 lock wait timeout
            $coTheThuLai = $maMySql === 1213 || $maMySql === 1205;
            if (!$coTheThuLai || $lan >= $soLanToiDa) {
                throw $e;
            }
            // backoff tăng dần + jitter: lần 1 chờ 10-50 ms, lần 2 chờ 20-100 ms...
            usleep(random_int(10_000, 50_000) * $lan);
        } catch (Throwable $e) {
            if ($pdo->inTransaction()) {
                $pdo->rollBack();
            }
            throw $e;                                   // lỗi nghiệp vụ, lỗi khác: không retry
        }
    }
}
```

Laravel có sẵn: `DB::transaction(fn () => ..., attempts: 3)`. Tham số số lần thử mặc định là 1 (không
retry). Laravel coi là lỗi tranh chấp và chạy lại khi exception mang SQLSTATE `40001` hoặc thông điệp
chứa các cụm như "Deadlock found", "Lock wait timeout exceeded" (giáo trình PHP,
[chương 27, mục 11.2](../php/27-laravel-database-eloquent.md)).

⚠️ Code trong closure có thể chạy nhiều lần, nên phải *chạy lại được an toàn*: mọi tác dụng phụ ngoài
database (gửi email, gọi API, ghi file, tăng counter Redis) đặt sau commit, nếu không mỗi lần retry
lại làm thêm một lần.

### 5.5 Giảm số lần phải retry

Retry là lưới an toàn, không phải thiết kế. Giảm deadlock từ phía ứng dụng (chi tiết ở chương 15):

- Truy cập các dòng theo **cùng một thứ tự** ở mọi nơi trong code. Ví dụ chuyển tiền: luôn khoá tài
  khoản có id nhỏ hơn trước, bất kể chiều chuyển.
- Giữ transaction ngắn (mục 5.2), ít dòng.
- Có index phù hợp cho `UPDATE`/`DELETE`/`SELECT ... FOR UPDATE`, để InnoDB khoá ít bản ghi index hơn.
- Ưu tiên câu `UPDATE` atomic có điều kiện thay cho đọc-tính-ghi ở ứng dụng.

### 5.6 Mất kết nối lúc commit: kết quả không xác định

Tình huống ít người nghĩ tới:

| Bước | Ứng dụng | MySQL | Kết quả |
|---|---|---|---|
| 1 | `BEGIN`; `INSERT INTO payments ...` | Ghi vào transaction | |
| 2 | Gửi `COMMIT` | Commit thành công, chuẩn bị gửi OK | |
| 3 | | Mạng đứt trước khi gói OK tới client | |
| 4 | Nhận lỗi "Lost connection" | | Ứng dụng không biết đã commit hay chưa |
| 5 | Retry cả transaction | Ghi thêm một payment | **Thanh toán hai lần** |

Driver không thể biết đáp án, vì câu trả lời bị mất trên đường. Cách xử lý là thiết kế để chạy lại
không gây hại (*idempotency*): mỗi thao tác mang một khoá duy nhất do client sinh (ví dụ
`idempotency_key` có `UNIQUE` index). Lần chạy lại gặp lỗi trùng khoá nghĩa là lần trước đã thành
công. Hoặc trước khi chạy lại, đọc lại trạng thái để kiểm tra.

## 6. ORM: Active Record và Data Mapper

### 6.1 ORM là gì, vì sao dùng

Ứng dụng nghĩ bằng object (`$user->name`, `$order->items`), database nghĩ bằng bảng và dòng. Phần
code chuyển qua lại giữa hai thế giới là việc lặp đi lặp lại: viết `SELECT`, đổ từng cột vào thuộc
tính, sinh `INSERT`/`UPDATE` từ object. *ORM* (Object-Relational Mapping) là thư viện làm hộ việc đó.

ORM giúp: ít code lặp, câu SQL đơn giản sinh tự động và luôn dùng placeholder, quan hệ giữa các bảng
thành thuộc tính dễ dùng. Cái giá: SQL thật bị che khuất. Một dòng `$post->author->name` trông như
đọc thuộc tính nhưng có thể là một query (mục 7). Người dùng ORM giỏi là người luôn biết dòng code của
mình sinh ra SQL gì.

### 6.2 Hai kiểu thiết kế

**Active Record**: mỗi object vừa chứa dữ liệu của một dòng vừa tự biết lưu chính nó.

```php
// Eloquent (Laravel): object Post biết bảng của nó và tự lưu
$post = Post::find(5);          // SELECT * FROM posts WHERE id = 5 LIMIT 1
$post->title = 'Tiêu đề mới';
$post->save();                  // UPDATE posts SET title = ?, updated_at = ? WHERE id = ?
                                // (chỉ cột đã đổi; updated_at do model bật timestamps mặc định)
```

**Data Mapper**: object nghiệp vụ (entity) chỉ chứa dữ liệu và logic, không biết gì về database. Một
lớp riêng (mapper, *entity manager*) lo việc đọc và ghi.

```php
// Doctrine ORM: entity không có save(); EntityManager theo dõi và ghi
$post = $entityManager->find(Post::class, 5);
$post->setTitle('Tiêu đề mới');
$entityManager->flush();        // tính các thay đổi, sinh UPDATE, chạy trong một transaction
```

| | Active Record | Data Mapper |
|---|---|---|
| Ví dụ | Eloquent (Laravel), Rails ActiveRecord | Doctrine (PHP), Hibernate/JPA (Java) |
| Object biết database | Có (`save()`, `delete()`, query ngay trên class) | Không |
| Khi nào ghi xuống DB | Mỗi lần gọi `save()` | Khi `flush()`/commit, gom mọi thay đổi |
| Dễ bắt đầu | Rất dễ | Phải học thêm khái niệm |
| Test logic nghiệp vụ không cần DB | Khó hơn | Dễ hơn |
| Hợp với | CRUD, schema gần giống object | Domain phức tạp, object khác xa bảng |

Data Mapper thường đi kèm hai khái niệm:

- *Unit of Work*: theo dõi mọi object đã đọc, tạo, sửa, xoá trong một phiên làm việc; khi `flush()`
  thì sinh và chạy toàn bộ câu SQL cần thiết.
- *Identity Map*: trong một phiên, đọc cùng một dòng hai lần trả về **cùng một object**, không query
  lần hai.

Go thường đi đường khác: nhiều dự án viết SQL tay với `database/sql` hoặc sinh code Go từ file SQL
(sqlc); cũng có ORM như GORM, nhưng không có một ORM "mặc định" gắn với framework như Eloquent với
Laravel.

### 6.3 ORM hay viết SQL tay

Không phải chọn một. Thực tế tốt:

- CRUD và truy vấn đơn giản: dùng ORM.
- Báo cáo, window function (chương 10), CTE (chương 9), thao tác hàng loạt (`UPDATE ... WHERE id IN`,
  `INSERT ... ON DUPLICATE KEY UPDATE`): viết SQL (qua query builder hoặc raw), **vẫn dùng binding**.
- Luôn bật công cụ xem SQL sinh ra khi phát triển (Laravel: `toSql()`, `DB::listen`, Debugbar,
  Telescope; giáo trình PHP chương 27, mục 4.8 và 9.5).

Các mẫu "ORM sinh SQL tệ" hay gặp:

| Viết | SQL thực tế | Nên viết |
|---|---|---|
| `Order::where(...)->get()->count()` | `SELECT *` kéo hết về rồi đếm trong PHP | `->count()`: `SELECT COUNT(*)` |
| `if (Order::where(...)->count() > 0)` | Đếm mọi dòng khớp | `->exists()` |
| Vòng lặp `Model::find($id)->update([...])` | 2N query | Một `UPDATE ... WHERE id IN (...)` hoặc upsert |
| Vòng lặp `Model::create([...])` | N câu `INSERT` | `insert([...])` nhiều dòng một câu (bỏ qua event, timestamps) |
| `paginate()` ở trang rất sâu | `LIMIT 15 OFFSET 500000` | Keyset pagination: `cursorPaginate()` |

## 7. N+1 và eager loading

### 7.1 N+1 nhìn từ database

*N+1* là mẫu truy cập: 1 query lấy danh sách N phần tử, rồi thêm N query, mỗi query lấy dữ liệu liên
quan của một phần tử. Với dữ liệu mẫu, trang "danh sách bài viết kèm tên tác giả" viết kiểu lazy
loading (ví dụ Eloquent `Post::all()` rồi `$post->author->name` trong vòng lặp) gửi tới MySQL:

```sql
SELECT * FROM posts;                              -- 1 query: 5 bài
SELECT * FROM users WHERE id = 1 LIMIT 1;         -- bài 1
SELECT * FROM users WHERE id = 2 LIMIT 1;         -- bài 2
SELECT * FROM users WHERE id = 1 LIMIT 1;         -- bài 3 (lại user 1)
SELECT * FROM users WHERE id = 3 LIMIT 1;         -- bài 4
SELECT * FROM users WHERE id = 2 LIMIT 1;         -- bài 5
```

6 query cho 5 bài. Mỗi câu chỉ tra primary key, cực nhanh, **không bao giờ lên slow query log**.
Nhưng như mục 1.2, 500 bài là 501 round-trip. Muốn thấy N+1 phải đếm số query mỗi request, hoặc nhìn
câu có cùng *digest* (dạng chuẩn hoá, thay hằng số bằng `?`) chạy rất nhiều lần:

```sql
-- Câu nào được chạy nhiều lần nhất (performance_schema, chương 12, 24)
SELECT DIGEST_TEXT, COUNT_STAR, ROUND(SUM_TIMER_WAIT / 1e12, 3) AS tong_giay
FROM performance_schema.events_statements_summary_by_digest
ORDER BY COUNT_STAR DESC
LIMIT 5;
-- Một câu kiểu "SELECT * FROM `users` WHERE `id` = ? LIMIT ?" có COUNT_STAR khổng lồ
-- so với số request là dấu hiệu N+1.
```

(`SUM_TIMER_WAIT` tính bằng picosecond, chia 10^12 ra giây.)

### 7.2 Ba cách lấy dữ liệu liên quan

**Cách 1: lazy loading (N+1)**, như trên. Chấp nhận được khi N rất nhỏ và cố định.

**Cách 2: eager loading bằng `IN`** (cách Eloquent `with()`, Doctrine, Hibernate batch fetch dùng):

```sql
SELECT * FROM posts;
SELECT * FROM users WHERE id IN (1, 2, 3);        -- id lấy từ cột user_id của các bài, đã bỏ trùng
-- ứng dụng tự ghép: bài nào user_id = bao nhiêu thì gắn user tương ứng
```

Luôn là 2 query, dù có 5 hay 5.000 bài.

**Cách 3: JOIN** trong một query:

```sql
SELECT p.id, p.title, u.name AS author
FROM posts p
JOIN users u ON u.id = p.user_id
ORDER BY p.id;
-- +----+-----------------+--------+
-- | id | title           | author |
-- +----+-----------------+--------+
-- |  1 | Học SQL         | An     |
-- |  2 | Học PHP         | Bình   |
-- |  3 | Index là gì     | An     |
-- |  4 | Deadlock        | Chi    |
-- |  5 | Connection pool | Bình   |
-- +----+-----------------+--------+
```

| | `IN` (2 query) | JOIN (1 query) |
|---|---|---|
| Round-trip | 2 | 1 |
| Dữ liệu lặp | Không: mỗi user gửi một lần | Cột của user lặp lại ở mỗi bài của user đó |
| Quan hệ một-nhiều (bài kèm comment) | Gọn | Mỗi bài nhân lên theo số comment; JOIN hai quan hệ một-nhiều cùng lúc sinh tích Descartes (bài × comment × tag) |
| Lọc, sắp xếp theo cột bảng kia | Không làm được trong query thứ hai | Làm được |

Vì vậy ORM thường dùng `IN` để nạp quan hệ, còn JOIN khi cần lọc/sắp theo bảng liên quan. Cách
Eloquent làm (`with`, `load`, `withCount`, `preventLazyLoading`) có ở giáo trình PHP,
[chương 27, mục 9](../php/27-laravel-database-eloquent.md).

### 7.3 Eager loading cũng có giá

- Kéo quá nhiều: `with('comments')` cho 1.000 bài, mỗi bài 500 comment là 500.000 dòng vào RAM
  ứng dụng, dù trang chỉ hiện 5 comment mới nhất. Cần đếm thì dùng `COUNT` (Eloquent `withCount`),
  cần vài dòng thì giới hạn ngay trong query.
- `IN` rất dài: nạp quan hệ cho hàng chục nghìn phần tử sinh câu `IN` với hàng chục nghìn giá trị. Kết
  hợp với đọc theo lô (mục 8).
- Index: query `WHERE user_id IN (...)` cần index trên cột khoá ngoại (`idx_posts_user` ở dữ liệu
  mẫu). MySQL không tự tạo index cho cột khoá ngoại nếu bạn không khai báo `FOREIGN KEY`; nếu có
  `FOREIGN KEY` thì InnoDB yêu cầu và tự tạo index khi chưa có (chương 04).

## 8. Đọc và ghi tập dữ liệu lớn

### 8.1 Vấn đề

Export 2 triệu đơn hàng ra CSV, gửi email cho mọi user, cập nhật trạng thái hàng loạt: viết ngây thơ
thì là một `SELECT` lấy hết rồi lặp. Có ba thứ có thể vỡ:

1. RAM ứng dụng: mặc định driver MySQL của PHP (mysqlnd) dùng *buffered query*, kéo **toàn bộ** kết
   quả về bộ nhớ process trước khi bạn đọc dòng đầu tiên. ORM còn tạo một object cho mỗi dòng.
2. Database: một câu lệnh chạy vài phút giữ một snapshot (read view) suốt thời gian đó; InnoDB không
   dọn được các phiên bản cũ mà snapshot còn có thể cần (chương 14, 16).
3. Một transaction ghi khổng lồ: khoá hàng triệu dòng, sinh undo log lớn, rollback (nếu lỗi) rất lâu,
   và replica phải áp dụng cả khối một lúc nên bị trễ (chương 22).

Hai hướng giải: đọc theo **luồng** (một query, nhận dòng dần dần) hoặc theo **lô** (nhiều query nhỏ).

### 8.2 Đọc theo luồng: unbuffered query

Với *unbuffered query*, server gửi dòng dần khi ứng dụng đọc, ứng dụng chỉ giữ dòng hiện tại. Giới hạn
(chi tiết PHP ở giáo trình PHP, [chương 16, mục 9](../php/16-php-va-database.md)):

- Trong lúc chưa đọc hết, connection đó **không chạy được câu nào khác** (lỗi 2014 "Commands out of
  sync" / "Cannot execute queries while other unbuffered queries are active"); thường phải mở connection
  riêng cho việc export.
- Câu lệnh vẫn đang chạy trên server suốt thời gian ứng dụng xử lý, nên vấn đề số 2 ở trên vẫn còn.
  Ứng dụng xử lý chậm (ghi file, gọi API cho từng dòng) thì câu lệnh sống càng lâu.

PostgreSQL có *cursor* phía server: `DECLARE c CURSOR FOR SELECT ...` trong một transaction, rồi
`FETCH 1000 FROM c` nhiều lần. Ở MySQL, câu lệnh `DECLARE ... CURSOR` chỉ dùng được bên trong stored
program, không gõ được như một câu SQL thường từ client. Server-side cursor vẫn tồn tại ở mức giao
thức: tài liệu MySQL 8.4 (Restrictions on Server-Side Cursors) ghi C API cài đặt nó qua
`mysql_stmt_attr_set()` trên prepared statement, và một số driver dùng cơ chế này (ví dụ Connector/J
với tuỳ chọn `useCursorFetch`).

### 8.3 Đọc theo lô: OFFSET và keyset

Cách thứ hai: chia thành nhiều query, mỗi query lấy 1.000 dòng.

```sql
-- Cách 1: OFFSET (tránh với tập lớn)
SELECT id, total FROM orders WHERE status = 'pending' ORDER BY id LIMIT 1000 OFFSET 0;
SELECT id, total FROM orders WHERE status = 'pending' ORDER BY id LIMIT 1000 OFFSET 1000;
SELECT id, total FROM orders WHERE status = 'pending' ORDER BY id LIMIT 1000 OFFSET 2000;
...
```

Hai vấn đề:

- Chậm dần: `OFFSET 24000` bắt MySQL đọc rồi bỏ 24.000 dòng đầu. Tổng công việc tăng theo bình phương
  số lô.
- Sai khi dữ liệu thay đổi giữa các lô. Nếu mỗi lô đổi `status` của các đơn vừa đọc từ `pending` sang
  `paid`, tập `pending` co lại: lô 2 dùng `OFFSET 1000` trên tập mới bỏ qua 1.000 đơn chưa xử lý. Kết
  quả: chỉ xử lý được khoảng một nửa (timeline đầy đủ với Laravel `chunk()` ở giáo trình PHP,
  [chương 27, mục 10.2](../php/27-laravel-database-eloquent.md)).

```sql
-- Cách 2: keyset (seek): nhớ id cuối của lô trước
SELECT id, total FROM orders WHERE status = 'pending' AND id > 0     ORDER BY id LIMIT 1000;
-- ứng dụng ghi nhớ id lớn nhất vừa nhận, ví dụ 4000
SELECT id, total FROM orders WHERE status = 'pending' AND id > 4000  ORDER BY id LIMIT 1000;
-- id cuối lô 2 là 8000 ...
-- dừng khi một lô trả về ít hơn 1000 dòng (hoặc 0 dòng)
```

Với dữ liệu mẫu, đơn `pending` là các id chia hết cho 4 (4, 8, ..., 100000), nên lô 1 có id 4..4000,
lô 2 có id 4004..8000, và cần 25 lô cho 25.000 đơn.

Keyset nhanh đều ở mọi lô vì index `(status, id)` cho phép MySQL nhảy thẳng tới `status = 'pending'
AND id > 4000` rồi đọc tiếp 1.000 entry theo thứ tự (chương 11). Và nó đúng ngay cả khi lô trước đã
sửa dữ liệu: điều kiện `id > ?` không phụ thuộc vào số dòng còn lại. Laravel gọi cách này là
`chunkById()` và `lazyById()`.

⚠️ Keyset cần một cột (hoặc tổ hợp cột) **duy nhất và có thứ tự**, thường là primary key. Sắp theo cột
không duy nhất như `created_at` thì phải dùng cặp `(created_at, id)`, nếu không các dòng cùng
`created_at` ở ranh giới lô bị lặp hoặc sót.

### 8.4 Ghi theo lô

Cập nhật hoặc xoá hàng loạt cũng nên chia nhỏ: mỗi lô là một transaction ngắn, giữ ít lock, replica
theo kịp giữa các lô.

```sql
-- Chạy lặp lại câu này cho tới khi số dòng bị ảnh hưởng là 0
UPDATE orders
SET status = 'expired'
WHERE status = 'pending' AND id <= 50000
ORDER BY id
LIMIT 1000;
-- MySQL cho phép ORDER BY ... LIMIT trong UPDATE/DELETE một bảng.
-- Với dữ liệu mẫu: có 12.500 đơn pending có id <= 50000, nên 13 lần (12 lần 1.000 dòng, lần thứ 13
-- là 500 dòng); lần thứ 14 trả 0 dòng thì dừng.
```

Câu này tự "trôi" vì dòng đã sửa không còn khớp `status = 'pending'`. Giữa các lô có thể nghỉ vài
chục mili giây để giảm tải. Với insert hàng loạt, gửi nhiều dòng trong một câu
`INSERT ... VALUES (...), (...), ...` và gom vài trăm tới vài nghìn dòng mỗi transaction thay vì một
dòng một transaction (mỗi commit phải ghi redo log xuống đĩa, chương 16).

| Kích thước lô | Ưu | Nhược |
|---|---|---|
| Quá nhỏ (1-10 dòng) | Lock rất ngắn | Quá nhiều round-trip và commit |
| Vừa (vài trăm tới vài nghìn) | Cân bằng | Cần đo với hệ thống thật |
| Quá lớn (hàng trăm nghìn) | Ít round-trip | Lock lâu, undo lớn, replica trễ, RAM ứng dụng |

## 9. Tách đọc và ghi (read/write splitting)

### 9.1 Vì sao tách

Phần lớn ứng dụng web đọc nhiều hơn ghi rất nhiều. Một cách mở rộng phổ biến là *replication*
(chương 22): một server *primary* nhận mọi câu ghi, các server *replica* nhận lại thay đổi từ primary
và phục vụ câu đọc. Ứng dụng cần biết gửi câu nào đi đâu:

```
                 ghi (INSERT/UPDATE/DELETE, transaction)
  Ứng dụng ───────────────────────────────────────────────▶ Primary
     │                                                        │  replication (thường bất đồng bộ)
     │  đọc (SELECT)                                          ▼
     └───────────────────────────────────────────────▶ Replica 1, Replica 2
```

Việc định tuyến có thể nằm ở ứng dụng (Laravel cấu hình `read`/`write` cho một connection; Java hay
dùng hai DataSource) hoặc ở proxy (ProxySQL với query rules).

### 9.2 Replication lag và các anomaly

Replication MySQL mặc định là *bất đồng bộ*: primary commit xong là trả lời client, replica nhận và
áp dụng thay đổi sau đó. Khoảng trễ đó là *replication lag*, bình thường vài mili giây, lúc có
transaction lớn hoặc replica quá tải có thể lên hàng phút. Hai loại sai lệch người dùng thấy được:

**Không đọc thấy chính dữ liệu mình vừa ghi** (vi phạm *read-your-writes*):

| Bước | Người dùng | Primary | Replica | Kết quả |
|---|---|---|---|---|
| 1 | Đổi tên thành "An Nguyễn", bấm Lưu | `UPDATE users SET name = 'An Nguyễn'`, commit | Vẫn là "An" (chưa nhận) | |
| 2 | Bị redirect về trang hồ sơ | | `SELECT name ...` trả "An" | Người dùng thấy tên cũ, tưởng lưu lỗi, bấm lưu lần nữa |
| 3 | | | Nhận và áp dụng thay đổi | Lần tải sau mới thấy tên mới |

**Đọc lùi thời gian** (vi phạm *monotonic reads*): hai lần tải trang liên tiếp rơi vào hai replica có
độ trễ khác nhau; lần đầu thấy comment mới, lần sau comment biến mất.

### 9.3 Các cách đảm bảo read-your-writes

| Cách | Ý tưởng | Giới hạn |
|---|---|---|
| Transaction luôn đi primary | Mọi câu trong transaction, kể cả `SELECT`, dùng connection ghi | Laravel làm sẵn; nếu không, `SELECT ... FOR UPDATE` lên replica là sai hoàn toàn |
| *Sticky* trong request | Sau câu ghi đầu tiên, mọi câu đọc còn lại của request đi primary | Laravel `'sticky' => true`. Chỉ trong một request: request sau redirect, queue job, request ở máy khác không biết |
| Đọc primary trong một khoảng sau khi ghi | Lưu "user này vừa ghi lúc T" vào session/cookie; trong vài giây sau T, đọc của user đó đi primary | Phải tự làm; chọn khoảng thời gian lớn hơn lag thường gặp |
| Đọc quan trọng luôn đi primary | Trang thanh toán, kiểm tra số dư, bước ngay sau khi ghi | Primary gánh thêm tải; cần kỷ luật trong code |
| Chờ replica bắt kịp bằng GTID | Sau khi ghi, lấy GTID của transaction; trước khi đọc trên replica, chờ replica đã áp dụng GTID đó | Chính xác nhất nhưng phức tạp nhất |

Cách GTID trên MySQL (khi replication dùng GTID, chương 22): mỗi transaction đã commit có một mã định
danh toàn cục. Client có thể nhận GTID của transaction mình vừa commit nếu bật
`session_track_gtids = OWN_GTID` (mặc định `OFF`; driver phải hỗ trợ đọc thông tin này), rồi trên
replica:

```sql
-- Chờ tối đa 1 giây cho tới khi replica đã áp dụng transaction có GTID này
SELECT WAIT_FOR_EXECUTED_GTID_SET('3E11FA47-71CA-11E1-9E33-C80AA9429562:23', 1);
-- Trả 0: đã bắt kịp, đọc trên replica an toàn
-- Trả 1: hết thời gian chờ; nên chuyển sang đọc primary
```

(Mã GTID ở trên lấy theo dạng ví dụ trong tài liệu MySQL, không phải giá trị thật trên máy bạn.)

⚠️ Queue job hay bị lag cắn: request ghi đơn hàng rồi dispatch job, job chạy ngay và đọc từ replica
chưa nhận đơn, báo "không tìm thấy". Job cần dữ liệu vừa ghi thì đọc từ primary (Laravel:
`->useWritePdo()` trên query, hoặc dùng connection ghi).

⚠️ Đừng dùng replica cho kiểm tra trước khi ghi ("email này đã tồn tại chưa?" rồi `INSERT`): replica
có thể chưa thấy dòng vừa thêm. Ràng buộc duy nhất phải dựa vào `UNIQUE` index trên primary.

## 10. Timeout

### 10.1 Vì sao phải có timeout

Không có timeout, một sự cố nhỏ lan thành sự cố lớn. Ví dụ: một câu query bị khoá chờ lock 50 giây;
mỗi request web chờ theo; PHP-FPM hết worker rảnh; Nginx trả 502 cho mọi trang, kể cả trang không
đụng tới bảng bị khoá. Timeout giúp *thất bại nhanh*: bỏ cuộc sớm, nhả tài nguyên, trả lỗi rõ ràng.

### 10.2 Bản đồ các timeout

Mỗi tầng có timeout riêng, đo những thứ khác nhau:

| Timeout | Ở đâu | Đo cái gì | Mặc định |
|---|---|---|---|
| Chờ mượn connection từ pool | Pool (HikariCP `connectionTimeout`) | Thời gian chờ có connection rảnh | 30 giây (HikariCP) |
| Kết nối | Client (PDO `ATTR_TIMEOUT` với MySQL), server `connect_timeout` | Thời gian bắt tay, xác thực | Server: `connect_timeout` 10 giây |
| Đọc kết quả | Client: `mysqlnd.net_read_timeout` (PHP) | Chờ dữ liệu từ server trên socket | 86400 giây (1 ngày) |
| Thời gian chạy câu `SELECT` | Server MySQL: `max_execution_time` (ms) hoặc hint `MAX_EXECUTION_TIME(N)` | Thời gian thực thi một `SELECT` chỉ đọc | 0 = không giới hạn |
| Thời gian chạy mọi câu | PostgreSQL `statement_timeout` | Từ lúc câu tới server tới khi xong | 0 = không giới hạn |
| Chờ row lock | MySQL `innodb_lock_wait_timeout` (giây); Postgres `lock_timeout` | Thời gian chờ một lock dòng | MySQL 50 giây; Postgres 0 = không giới hạn |
| Chờ metadata lock | MySQL `lock_wait_timeout` (giây) | Chờ lock cấp bảng/DDL | 31536000 (1 năm) |
| Connection rảnh | MySQL `wait_timeout` (giây) | Connection không gửi gì | 28800 (8 giờ) |
| Rảnh giữa transaction | Postgres `idle_in_transaction_session_timeout` | Session đang mở transaction mà không gửi câu nào | 0 = không giới hạn |
| Cả transaction | Postgres `transaction_timeout` (có từ PostgreSQL 17) | Tổng thời gian một transaction | 0 = không giới hạn |

Các con số mặc định ở trên lấy từ tài liệu MySQL 8.4, PostgreSQL 18, PHP manual và HikariCP README.
Nhìn vào cột mặc định, điểm chung là: **gần như mọi thứ mặc định là chờ rất lâu hoặc chờ mãi**. Đặt
timeout là việc của bạn.

### 10.3 Timeout truy vấn trên MySQL

```sql
-- Giới hạn cho cả session: mọi SELECT chỉ đọc chạy quá 2 giây bị ngắt
SET SESSION max_execution_time = 2000;

-- Hoặc cho riêng một câu bằng optimizer hint
SELECT /*+ MAX_EXECUTION_TIME(1000) */ user_id, SUM(total)
FROM orders
GROUP BY user_id;
-- Quá 1 giây: câu bị ngắt và client nhận lỗi 3024 (ER_QUERY_TIMEOUT):
-- "Query execution was interrupted, maximum statement execution time exceeded"
```

⚠️ Theo tài liệu MySQL 8.4, `max_execution_time` chỉ áp dụng cho `SELECT` chỉ đọc, và bị bỏ qua với
`SELECT` bên trong stored program. `UPDATE`, `DELETE`, `INSERT ... SELECT` không bị giới hạn bởi biến
này. Với câu ghi, giới hạn chủ yếu đến từ `innodb_lock_wait_timeout` (khi chờ lock) và timeout phía
client.

Giảm `innodb_lock_wait_timeout` cho ứng dụng tương tác (tài liệu MySQL cũng gợi ý điều này cho hệ
OLTP) để request không treo 50 giây. Biến này đặt được ở cấp session:

```sql
SET SESSION innodb_lock_wait_timeout = 5;    -- chờ lock tối đa 5 giây trong session này
```

Nhớ mục 5.3: hết thời gian chờ lock chỉ rollback câu đang chờ, transaction vẫn mở.

⚠️ `lock_wait_timeout` (metadata lock) mặc định một năm là bẫy lớn khi chạy migration: `ALTER TABLE`
chờ metadata lock sau một transaction dài, và mọi câu mới trên bảng đó xếp hàng sau `ALTER`. Chương 20
nói cách đặt timeout ngắn cho migration.

### 10.4 Client bỏ cuộc không có nghĩa server dừng

Khi timeout phía client hết hạn (ví dụ ứng dụng hết thời gian đọc socket rồi đóng connection), câu
lệnh **có thể vẫn đang chạy trên server** cho tới khi server phát hiện client đã đi. Ứng dụng retry
thì server chạy thêm một bản nữa của cùng câu nặng; vài lần như vậy là server quá tải vì chính các
câu đã bị bỏ rơi.

Vì vậy với câu đọc nặng, nên đặt giới hạn **ở phía server** (`max_execution_time` trên MySQL,
`statement_timeout` trên Postgres): server tự dừng câu lệnh và nhả tài nguyên. Muốn dừng tay một câu
đang chạy:

```sql
SHOW PROCESSLIST;           -- tìm Id của connection đang chạy câu nặng
KILL QUERY 1234;            -- dừng câu đang chạy, giữ connection
KILL 1234;                  -- (KILL CONNECTION) dừng câu và đóng luôn connection
-- Không có quyền CONNECTION_ADMIN thì chỉ KILL được thread của chính mình
```

### 10.5 Timeout ở PHP

- ⚠️ `max_execution_time` của PHP (và `set_time_limit()`) **không tính** thời gian chờ database trên
  Linux: tài liệu PHP ghi thời gian cho system call, stream, database query không được tính (trừ
  Windows). Script chờ một query 5 phút vẫn không bị `max_execution_time = 30` cắt.
- PHP-FPM có `request_terminate_timeout` giết worker theo thời gian thực (giáo trình PHP, chương 18);
  worker bị giết giữa chừng thì connection đóng, transaction đang mở bị server rollback, còn câu lệnh
  đang chạy trên server có thể chạy tiếp như mục 10.4.
- `mysqlnd.net_read_timeout` mặc định một ngày, tức là trên thực tế PHP chờ server rất lâu.
- `PDO::ATTR_TIMEOUT`: tài liệu PDO ghi ý nghĩa tuỳ driver. Với `pdo_mysql`, mã nguồn PHP
  (`ext/pdo_mysql/mysql_driver.c`) truyền giá trị này vào `MYSQL_OPT_CONNECT_TIMEOUT`, tức là timeout
  **kết nối** (mặc định 30 giây), không giới hạn thời gian chạy query.

### 10.6 Ngân sách thời gian

Đặt timeout theo *ngân sách* từ ngoài vào trong: tầng trong phải hết giờ trước tầng ngoài, nếu không
tầng ngoài đã bỏ cuộc mà tầng trong vẫn làm.

```
Load balancer / Nginx timeout                   30 s
  └─ PHP-FPM request_terminate_timeout          25 s
       └─ tổng thời gian query trong request    nên < vài giây
            ├─ max_execution_time (SELECT)       2-5 s cho request web
            └─ innodb_lock_wait_timeout          vài giây cho request web
Queue worker / báo cáo: ngân sách riêng, dài hơn, dùng connection hoặc session riêng
```

(Các con số là ví dụ minh hoạ cho một ứng dụng web điển hình, không phải khuyến nghị chung.)

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Tăng `max_connections` mỗi khi gặp "Too many connections" | Nhiều connection cùng chạy làm server chậm hơn; gốc là ứng dụng mở quá nhiều hoặc giữ quá lâu | Tính tổng connection từ mọi instance; giữ connection ngắn; dùng pool/proxy |
| Pool rất to "cho chắc" | Thông lượng không tăng, độ trễ tăng vì tranh tài nguyên (mục 3.3) | Bắt đầu nhỏ (cỡ 2 × số lõi của DB cho tổng connection đang chạy), đo rồi chỉnh |
| Go không đặt `SetMaxOpenConns` | Mặc định không giới hạn, spike mở hàng trăm connection | Luôn đặt giới hạn và `SetConnMaxLifetime` |
| Tuổi thọ connection trong pool dài hơn `wait_timeout` hoặc timeout của hạ tầng | Pool đưa ra connection đã bị server/firewall đóng | `maxLifetime` ngắn hơn các giới hạn đó vài giây |
| Dùng biến session, bảng tạm, `SET` sau proxy pool kiểu transaction | Câu sau có thể chạy trên connection khác | Coi mỗi transaction là một connection mới; với ProxySQL biết các điều kiện tắt multiplexing |
| Gọi API, gửi email trong transaction | Giữ lock và connection lâu; retry làm gửi lặp | Tác dụng phụ đặt sau commit (`afterCommit`) |
| Bắt lỗi lock wait timeout rồi commit tiếp | Chỉ câu lỗi bị rollback, transaction thiếu một câu vẫn commit được | Lỗi gì trong transaction cũng rollback cả transaction |
| Retry chỉ câu lệnh lỗi thay vì cả transaction | Deadlock đã huỷ toàn bộ; dữ liệu đọc trước đó đã cũ | Retry từ `BEGIN`, ở transaction ngoài cùng, có giới hạn và jitter |
| Retry mù khi mất kết nối lúc `COMMIT` | Có thể đã commit, chạy lại là ghi hai lần | Idempotency key với `UNIQUE`, hoặc kiểm tra trạng thái trước khi chạy lại |
| Lazy loading quan hệ trong vòng lặp | N+1 round-trip, không lên slow log | Eager loading, đếm số query mỗi request |
| Đọc hàng triệu dòng bằng một `SELECT` buffered | Hết RAM ứng dụng | Keyset theo lô hoặc unbuffered trên connection riêng |
| Chia lô bằng `OFFSET` khi đang sửa dữ liệu | Bỏ sót dòng, chậm dần | Keyset (`id > ?`) |
| Đọc từ replica ngay sau khi ghi | Replication lag: thấy dữ liệu cũ | Sticky, đọc primary sau khi ghi, GTID wait |
| Tin `max_execution_time` của PHP giới hạn thời gian query | Trên Linux nó không tính thời gian chờ DB | Timeout phía server (`max_execution_time` MySQL, `statement_timeout` Postgres) |
| Prepare liên tục không đóng trên connection sống lâu | Chạm `max_prepared_stmt_count`, cả server không prepare được | Đóng statement, giới hạn cache statement, theo dõi `Prepared_stmt_count` |

## Tóm tắt chương

- Mỗi query tốn ít nhất một round-trip; nhiều query nhỏ có thể chậm hơn một query lớn dù từng câu đều
  nhanh.
- Connection là phiên có trạng thái (biến session, transaction, lock, bảng tạm, prepared statement),
  mở tốn nhiều round-trip; MySQL dùng một thread mỗi connection, Postgres một process mỗi connection.
- Pool tái dùng connection và giới hạn số connection; số connection cần ≈ tần suất × thời gian giữ
  (định luật Little). Pool nhỏ, bận thường nhanh hơn pool to.
- PHP-FPM không có pool: connection tỉ lệ với số worker. Proxy (ProxySQL, PgBouncer) gom connection,
  đổi lại phải tránh các tính năng gắn với session.
- Prepared statement sống trong session, bị giới hạn bởi `max_prepared_stmt_count`; Postgres có thể
  chuyển sang generic plan sau năm lần execute.
- Lỗi trong transaction: deadlock rollback cả transaction, lock wait timeout chỉ rollback câu lệnh; ứng
  dụng nên luôn rollback cả transaction rồi mới quyết định retry.
- Retry cả transaction, ở lớp ngoài cùng, có giới hạn và jitter, không có tác dụng phụ bên ngoài; mất
  kết nối lúc commit cần idempotency.
- ORM: Active Record (Eloquent) và Data Mapper (Doctrine, Hibernate); N+1 sửa bằng eager loading
  (`IN`) hoặc JOIN.
- Tập lớn: đọc theo keyset hoặc theo luồng, ghi theo lô nhỏ, mỗi lô một transaction ngắn.
- Read/write splitting gặp replication lag; đảm bảo read-your-writes bằng sticky, đọc primary sau khi
  ghi, hoặc chờ GTID. Mặc định của hầu hết timeout là rất dài: tự đặt, và ưu tiên timeout phía server.

## Câu hỏi tự kiểm tra

1. Vì sao một trang chạy 300 query, mỗi query 0,2 ms trên server, vẫn có thể chậm? (mục 1.2)
2. Liệt kê năm thứ thuộc trạng thái session của một connection MySQL. Vì sao chúng gây rắc rối khi
   connection được tái dùng? (mục 2.3)
3. Ứng dụng xử lý 1.500 transaction/giây, mỗi transaction giữ connection 8 ms. Cần khoảng bao nhiêu
   connection bận? Nếu thêm một lời gọi API 200 ms vào trong transaction thì sao? (mục 3.2)
4. Vì sao tăng kích thước pool từ 50 lên 500 có thể làm hệ thống chậm đi? (mục 3.3)
5. ProxySQL tắt multiplexing trong những trường hợp nào? Vì sao không thể tránh việc đó? (mục 3.5)
6. Sau lỗi 1205 lock wait timeout, transaction đang ở trạng thái nào? Nếu code chỉ log lỗi rồi
   `commit()` thì chuyện gì xảy ra? (mục 5.3)
7. Vì sao retry phải chạy lại cả transaction, kể cả các câu `SELECT`? Vì sao chỉ ở transaction ngoài
   cùng? (mục 5.4)
8. So sánh nạp quan hệ bằng `IN` và bằng JOIN khi lấy 100 bài viết kèm toàn bộ comment và tag.
   (mục 7.2)
9. Vì sao chia lô bằng `OFFSET` vừa chậm dần vừa có thể sai? (mục 8.3)
10. `'sticky' => true` của Laravel bảo vệ được tình huống nào và không bảo vệ được tình huống nào?
    (mục 9.3)

## Bài tập

1. **Đo round-trip.** Viết script PHP (PDO, MySQL thật, dữ liệu mẫu mục 1.4) lấy 1.000 đơn hàng đầu
   tiên theo hai cách: (a) 1.000 câu `SELECT ... WHERE id = ?`, (b) một câu `WHERE id BETWEEN 1 AND
   1000`. Đo thời gian bằng `hrtime(true)` và giải thích chênh lệch. Lặp lại khi MySQL chạy trên một
   máy khác (hoặc container khác) để thấy ảnh hưởng của mạng.
2. **Tái hiện deadlock và retry.** Mở hai client `mysql`, làm deadlock trên bảng `accounts` (A khoá
   dòng 1 rồi dòng 2, B khoá dòng 2 rồi dòng 1). Ghi lại thông báo lỗi và kiểm tra transaction bị huỷ
   đã mất những thay đổi nào. Sau đó viết hàm chuyển tiền PHP dùng mẫu retry ở mục 5.4 và sửa để luôn
   khoá tài khoản id nhỏ trước; giải thích vì sao deadlock biến mất.
3. **Lock wait timeout không rollback cả transaction.** Trong client A: `BEGIN; UPDATE accounts SET
   balance = balance + 1 WHERE id = 2;` (giữ nguyên). Trong client B: `SET SESSION
   innodb_lock_wait_timeout = 3; BEGIN; UPDATE accounts SET balance = balance - 10 WHERE id = 1;
   UPDATE accounts SET balance = balance + 10 WHERE id = 2;`. Sau lỗi timeout ở B, chạy `SELECT * FROM
   accounts` trong B rồi `COMMIT`. Quan sát dữ liệu cuối cùng và giải thích bằng mục 5.3.
4. **Xử lý theo lô.** Viết script chuyển mọi đơn `pending` sang `paid` theo lô 1.000 dòng bằng cả hai
   cách OFFSET và keyset (mục 8.3). Đếm số đơn còn `pending` sau mỗi cách (nhớ chạy lại dữ liệu mẫu
   giữa hai lần thử) và giải thích kết quả.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [Connection Interfaces](https://dev.mysql.com/doc/refman/8.4/en/connection-interfaces.html),
  [Server System Variables](https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html)
  (`max_connections`, `wait_timeout`, `connect_timeout`, `max_execution_time`, `lock_wait_timeout`,
  `max_prepared_stmt_count`, `session_track_gtids`),
  [InnoDB Startup Options and System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html)
  (`innodb_lock_wait_timeout`, `innodb_rollback_on_timeout`),
  [InnoDB Error Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-error-handling.html),
  [Prepared Statements](https://dev.mysql.com/doc/refman/8.4/en/sql-prepared-statements.html),
  [PREPARE Statement](https://dev.mysql.com/doc/refman/8.4/en/prepare.html),
  [Caching of Prepared Statements and Stored Programs](https://dev.mysql.com/doc/refman/8.4/en/statement-caching.html),
  [KILL Statement](https://dev.mysql.com/doc/refman/8.4/en/kill.html),
  [Functions Used with GTIDs](https://dev.mysql.com/doc/refman/8.4/en/gtid-functions.html).
- MySQL 8.4 C API: [mysql_reset_connection()](https://dev.mysql.com/doc/c-api/8.4/en/mysql-reset-connection.html).
- PostgreSQL 18: [Connections and Authentication](https://www.postgresql.org/docs/18/runtime-config-connection.html),
  [Client Connection Defaults](https://www.postgresql.org/docs/18/runtime-config-client.html)
  (`statement_timeout`, `lock_timeout`, `idle_in_transaction_session_timeout`, `transaction_timeout`),
  [PREPARE](https://www.postgresql.org/docs/18/sql-prepare.html) (custom và generic plan).
- PgBouncer: [Features](https://www.pgbouncer.org/features.html) (bảng tương thích theo pool mode),
  [Configuration](https://www.pgbouncer.org/config.html) (`pool_mode`, `max_prepared_statements`).
- ProxySQL: [Multiplexing](https://proxysql.com/documentation/multiplexing/).
- HikariCP: [About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing),
  [README](https://github.com/brettwooldridge/HikariCP) (các tham số và giá trị mặc định).
- Go: [Managing connections](https://go.dev/doc/database/manage-connections).
- PHP manual: [Persistent Database Connections](https://www.php.net/manual/en/features.persistent-connections.php),
  [PDO::setAttribute](https://www.php.net/manual/en/pdo.setattribute.php),
  [mysqlnd configuration](https://www.php.net/manual/en/mysqlnd.config.php),
  [set_time_limit](https://www.php.net/manual/en/function.set-time-limit.php).
- Martin Fowler, *Patterns of Enterprise Application Architecture*: các mẫu Active Record, Data Mapper,
  Unit of Work, Identity Map.
- Giáo trình PHP trong repo: [chương 16](../php/16-php-va-database.md),
  [chương 27](../php/27-laravel-database-eloquent.md).
