# Chương 18. Người dùng, phân quyền và bảo mật

> [← Mục lục](README.md) · [← Chương 17: View, stored procedure, function, trigger, event](17-view-procedure-trigger.md) · [Chương 19: Database từ phía ứng dụng →](19-database-tu-ung-dung.md)

**Bạn sẽ học được:**

- MySQL quyết định "ai được vào, được làm gì" theo hai bước: xác thực kết nối, rồi kiểm tra quyền
  cho từng câu lệnh.
- Account trong MySQL là cặp `'user'@'host'`, cách server chọn account khi nhiều dòng cùng khớp,
  và cách tạo, sửa, khoá, xoá account.
- *Authentication plugin*: vì sao MySQL 8.4 dùng `caching_sha2_password` mặc định, vì sao
  `mysql_native_password` bị tắt, và chuyện gì xảy ra với ứng dụng PHP khi nâng cấp.
- `GRANT`, `REVOKE`, các cấp quyền (toàn server, database, bảng, cột, routine), *role*, và cách
  thiết kế quyền tối thiểu cho ứng dụng, migration, báo cáo, sao lưu.
- Mã hoá đường truyền bằng TLS, mã hoá dữ liệu khi lưu (ở mức khái niệm), SQL injection nhìn từ
  phía database, quyền cho sao lưu, và audit.

**Cần biết trước:** [Chương 01](01-database-la-gi.md) (cài MySQL, client `mysql`),
[Chương 04](04-ddl-constraint.md) (tạo database và bảng), [Chương 05](05-select-co-ban.md)
(`SELECT`, `INSERT`, `UPDATE`, `DELETE`). Mục về routine và view có nhắc tới
[Chương 17](17-view-procedure-trigger.md).

Mọi câu SQL trong chương chạy trên MySQL 8.4. Bạn cần đăng nhập bằng một account có quyền quản trị
(ví dụ `root`) để tạo user và cấp quyền. Nếu chạy MySQL bằng Docker như ở chương 01:

```bash
# Chạy trên máy của bạn (terminal), không phải trong mysql client
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
docker exec -it my84 mysql -uroot -proot
```

⚠️ Chỉ thực hành trên một server MySQL riêng để học. Các lệnh trong chương tạo và xoá user, đổi
cấu hình bảo mật; đừng chạy trên database công ty hay database thật của bạn.

## 1. Bảo mật database: bức tranh tổng thể

### 1.1 Database cần bảo vệ khỏi cái gì

Database thường là nơi giữ thứ quý nhất của một hệ thống: thông tin khách hàng, đơn hàng, mật khẩu
(đã băm), số dư tài khoản. Khi nói "bảo mật database", ta muốn ba điều, thường gọi tắt là *CIA*:

| Mục tiêu | Nghĩa | Ví dụ khi bị phá |
|---|---|---|
| *Confidentiality* (bí mật) | Chỉ người được phép mới đọc được dữ liệu | Lộ bảng `users` kèm email, số điện thoại |
| *Integrity* (toàn vẹn) | Chỉ người được phép mới sửa được, và sửa đúng cách | Kẻ tấn công đổi giá sản phẩm, xoá đơn hàng |
| *Availability* (sẵn sàng) | Người được phép luôn dùng được | Ai đó `DROP TABLE`, hoặc mở hàng nghìn kết nối làm server nghẽn |

Mối đe doạ đến từ nhiều phía, không chỉ "hacker ở ngoài":

- Kẻ tấn công lợi dụng lỗ hổng của ứng dụng (phổ biến nhất là SQL injection, mục 9) để chạy câu
  lệnh tuỳ ý bằng chính account của ứng dụng.
- Mật khẩu database bị lộ: commit nhầm file `.env` lên Git, log in ra chuỗi kết nối, máy dev bị
  nhiễm mã độc.
- Người nghe lén trên đường mạng giữa ứng dụng và database (mục 7).
- Người có quyền truy cập ổ đĩa, file backup hoặc snapshot (mục 8, mục 10).
- Người trong nội bộ dùng quyền quá rộng, cố ý hoặc vô tình (chạy nhầm `DELETE` không có `WHERE`
  trên production).

### 1.2 Phòng thủ nhiều lớp

Không có một biện pháp nào chặn được mọi thứ. Cách làm chuẩn là *defense in depth* (phòng thủ
nhiều lớp): mỗi lớp chặn một số kiểu tấn công, và khi một lớp thủng thì lớp sau vẫn giới hạn thiệt
hại.

```
   Kẻ tấn công / người dùng
            │
            ▼
 ┌─────────────────────────────┐
 │ 1. Mạng                     │  firewall, MySQL không mở ra Internet, chỉ nhận từ app server
 ├─────────────────────────────┤
 │ 2. Đường truyền             │  TLS: không nghe lén, không giả mạo server         (mục 7)
 ├─────────────────────────────┤
 │ 3. Xác thực (authentication)│  account 'user'@'host', mật khẩu, plugin           (mục 2, 3)
 ├─────────────────────────────┤
 │ 4. Phân quyền (authorization)│ GRANT tối thiểu, role                             (mục 4, 5, 6)
 ├─────────────────────────────┤
 │ 5. Ứng dụng                 │  prepared statement, không ghép chuỗi SQL         (mục 9)
 ├─────────────────────────────┤
 │ 6. Dữ liệu khi lưu          │  mã hoá file, mã hoá cột nhạy cảm, băm mật khẩu   (mục 8)
 ├─────────────────────────────┤
 │ 7. Sao lưu                  │  backup được bảo vệ như chính database            (mục 10)
 ├─────────────────────────────┤
 │ 8. Ghi vết (audit)          │  biết ai đã làm gì, khi nào                        (mục 11)
 └─────────────────────────────┘
```

Ví dụ cho thấy vì sao cần nhiều lớp: giả sử ứng dụng có lỗ SQL injection (lớp 5 thủng). Nếu account
của ứng dụng chỉ có `SELECT, INSERT, UPDATE, DELETE` trên đúng database của nó (lớp 4 làm tốt), kẻ
tấn công vẫn đọc được dữ liệu của app, nhưng không `DROP DATABASE` được, không đọc được database
khác, không tạo được user mới để quay lại sau, không ghi file ra ổ đĩa server. Thiệt hại vẫn lớn,
nhưng nhỏ hơn rất nhiều so với khi app dùng `root`.

### 1.3 Hai giai đoạn kiểm soát truy cập của MySQL

*Access control* (kiểm soát truy cập) của MySQL chia thành hai giai đoạn rõ ràng. Hiểu hai giai
đoạn này giúp đọc đúng thông báo lỗi.

```
 Client                                 MySQL server
   │  kết nối: user = app, từ host 10.0.0.5, mật khẩu ...
   │──────────────────────────────────────►│
   │                                       │  Giai đoạn 1: CONNECTION VERIFICATION
   │                                       │  - Có dòng nào trong mysql.user khớp (User, Host)?
   │                                       │  - Thông tin xác thực đúng chưa (theo plugin)?
   │                                       │  - Account có bị khoá (ACCOUNT LOCK) không?
   │◄─────────── OK hoặc ERROR 1045 ───────│
   │
   │  SELECT * FROM shop.orders
   │──────────────────────────────────────►│
   │                                       │  Giai đoạn 2: REQUEST VERIFICATION (mỗi câu lệnh)
   │                                       │  - Account có quyền SELECT trên shop.orders không?
   │                                       │    (xét quyền toàn cục, database, bảng, cột)
   │◄──── kết quả hoặc ERROR 1142 ─────────│
```

- Giai đoạn 1 (*connection verification*): server tìm account khớp với tên user và host của client,
  kiểm tra mật khẩu (hoặc thông tin xác thực khác) bằng *authentication plugin* của account đó, rồi
  kiểm tra account có bị khoá không. Sai một trong các điều đó thì kết nối bị từ chối hẳn, lỗi
  thường gặp là `ERROR 1045 (28000): Access denied for user ...`.
- Giai đoạn 2 (*request verification*): sau khi đã vào, với mỗi câu lệnh, server kiểm tra account
  có đủ quyền cho thao tác đó trên đối tượng đó không. Thiếu quyền thì câu lệnh bị từ chối nhưng
  kết nối vẫn còn, ví dụ `ERROR 1142 (42000): INSERT command denied to user 'u'@'localhost' for
  table 't'`.

Hai khái niệm hay bị lẫn:

- *Authentication* (xác thực): "bạn là ai?". Trả lời bằng mật khẩu, chứng chỉ, v.v. Mục 2 và 3.
- *Authorization* (phân quyền): "bạn được làm gì?". Trả lời bằng các quyền (*privilege*) đã cấp.
  Mục 4 tới 6.

Dữ liệu cho cả hai giai đoạn nằm trong các bảng của schema hệ thống `mysql`, gọi chung là *grant
tables*: `mysql.user` (mỗi account một dòng, kèm plugin, chuỗi xác thực, trạng thái khoá và các
quyền toàn cục), `mysql.db` (quyền cấp database), `mysql.tables_priv`, `mysql.columns_priv`,
`mysql.procs_priv` (quyền cấp bảng, cột, routine), và vài bảng khác cho role, quyền động. Bạn không
sửa các bảng này trực tiếp; luôn dùng `CREATE USER`, `GRANT`, `REVOKE`... (mục 4.6 giải thích vì sao).

⚠️ Cột `authentication_string` trong `mysql.user` chứa mật khẩu đã băm. Tài liệu MySQL nhấn mạnh:
với server, chuỗi đã băm này chính là "mật khẩu thật", đừng bao giờ cho account không phải quản
trị quyền đọc các bảng trong schema `mysql`.

## 2. Account: `'user'@'host'`

### 2.1 Account gồm tên user và host

Trong nhiều hệ thống, "user" chỉ là một cái tên. Trong MySQL, một *account* gồm hai phần: tên user
và host (máy) mà client kết nối từ đó, viết là `'user_name'@'host_name'`.

```sql
CREATE USER 'app'@'10.0.0.5'  IDENTIFIED BY 'mat-khau-1';
CREATE USER 'app'@'localhost' IDENTIFIED BY 'mat-khau-2';
```

Hai câu trên tạo ra hai account khác nhau hoàn toàn, chỉ tình cờ cùng tên `app`. Mỗi account có mật
khẩu riêng, quyền riêng. Khi `app` kết nối từ máy `10.0.0.5`, server dùng account thứ nhất; khi
kết nối ngay trên máy chủ database, server dùng account thứ hai.

Vì sao thiết kế như vậy? Để giới hạn không chỉ "ai" mà còn "từ đâu". Account `'app'@'10.0.0.5'`
dù bị lộ mật khẩu, kẻ tấn công vẫn phải kết nối từ đúng máy `10.0.0.5` mới dùng được.

Quy tắc viết tên account:

- Phần `@'host'` có thể bỏ; `'app'` tương đương `'app'@'%'` (mọi host).
- Trích dẫn tên user và host riêng biệt: viết `'app'@'localhost'`, không viết `'app@localhost'`.
  Cách viết sau bị hiểu thành user tên `app@localhost` ở host `'%'` (và cách hiểu này đã bị đánh
  dấu *deprecated*).
- Có thể dùng dấu nháy đơn, nháy kép hoặc backtick. Bắt buộc phải có nháy khi tên chứa ký tự đặc
  biệt như `-`, `.`, `%`.
- So khớp tên user phân biệt hoa thường; so khớp host không phân biệt hoa thường.
- Tên user tối đa 32 ký tự, host tối đa 255 ký tự.

### 2.2 Các dạng giá trị host

| Host | Ý nghĩa |
|---|---|
| `'localhost'` | Kết nối cục bộ trên chính máy chạy MySQL. Kết nối qua Unix socket file (và named pipe, shared memory trên Windows) được coi là kết nối cục bộ và khớp `localhost` |
| `'127.0.0.1'`, `'::1'` | Địa chỉ loopback IPv4, IPv6 (kết nối TCP tới chính máy) |
| `'10.0.0.5'` | Đúng một địa chỉ IP |
| `'db-client.example.com'` | Đúng một tên máy (server so với tên mà DNS trả về) |
| `'10.0.0.0/255.255.255.0'` | Mọi IP trong dải 10.0.0.0 tới 10.0.0.255 (IP kèm netmask, chỉ cho IPv4) |
| `'10.0.0.0/24'` | Cùng dải trên, viết kiểu CIDR |
| `'10.0.0.%'`, `'%.example.com'` | Ký tự đại diện giống `LIKE`: `%` là chuỗi bất kỳ, `_` là một ký tự |
| `'%'` | Mọi host |

⚠️ Trong MySQL 8.4, việc dùng `%` và `_` làm ký tự đại diện trong phần host đã bị đánh dấu
deprecated (có thể bị bỏ ở phiên bản sau). Với dải mạng, ưu tiên dạng netmask hoặc CIDR. `'%'` vẫn
được dùng rất phổ biến (đặc biệt với Docker, Kubernetes, nơi IP của client thay đổi liên tục), nhưng
hãy biết rằng đó là "mở cho mọi nơi", và lúc đó lớp mạng (firewall, security group) phải gánh việc
giới hạn nguồn kết nối.

⚠️ Server so khớp host dưới dạng chuỗi với kết quả mà DNS trả về (trừ dạng netmask). Nếu DNS trả về
`host1` thay vì `host1.example.com` thì account `'u'@'host1.example.com'` không khớp. Để tránh rắc
rối này, nhiều nơi dùng IP thay cho tên máy.

### 2.3 Khi nhiều account cùng khớp: server chọn account nào

Một kết nối có thể khớp nhiều dòng trong `mysql.user`. Ví dụ `fred` kết nối từ `h1.example.net`
khớp cả `'fred'@'h1.example.net'`, `'fred'@'%.example.net'` và `'fred'@'%'`. Server giải quyết như
sau:

1. Khi nạp bảng `mysql.user` vào bộ nhớ, server sắp xếp các dòng theo độ cụ thể của host: host là
   IP hoặc tên máy cụ thể đứng đầu, host có ký tự đại diện đứng sau, `'%'` gần cuối (chuỗi rỗng `''`
   cũng nghĩa là mọi host nhưng xếp sau `'%'`).
2. Các dòng cùng host thì user cụ thể đứng trước user rỗng (*anonymous user*, account có tên user là
   chuỗi rỗng, khớp mọi tên).
3. Khi client kết nối, server duyệt danh sách đã sắp xếp và dùng dòng khớp đầu tiên.

Điểm hay gây bất ngờ: server không ưu tiên "các dòng có đúng tên user của tôi". Nó ưu tiên host cụ
thể trước. Ví dụ từ tài liệu MySQL, bảng `mysql.user` có:

```
+----------------+---------+
| Host           | User    |
+----------------+---------+
| %              | jeffrey |
| h1.example.net |         |      <- anonymous user
+----------------+---------+
```

Sau khi sắp xếp, dòng `h1.example.net` (host cụ thể) đứng trước dòng `%`. Khi `jeffrey` kết nối từ
`h1.example.net`, dòng đầu tiên khớp là anonymous user, nên jeffrey được xác thực thành anonymous
user (phải dùng mật khẩu của anonymous user, và nhận quyền của anonymous user), dù anh ta đã gõ tên
`jeffrey`.

Cách kiểm tra mình đang thực sự là account nào:

```sql
SELECT USER(), CURRENT_USER();
```

- `USER()`: tên user và host mà client đưa ra khi kết nối (bạn "xưng" là ai).
- `CURRENT_USER()`: account mà server đã chọn để xác thực và kiểm tra quyền (server "coi" bạn là ai).

Nếu `CURRENT_USER()` trả về `@localhost` (phần user rỗng) thì bạn đang bị coi là anonymous user.
Quy tắc thực hành: khi kết nối được nhưng quyền "không như mong đợi", việc đầu tiên là chạy
`SELECT CURRENT_USER();`.

⚠️ Một số bản cài MySQL cũ tạo sẵn anonymous user. Liệt kê và xoá chúng:

```sql
SELECT Host, User FROM mysql.user WHERE User = '';
DROP USER ''@'localhost';   -- nếu có
```

### 2.4 `localhost` khác `127.0.0.1`

Trên Linux/macOS, client `mysql` (và PHP PDO) hiểu host `localhost` là "kết nối qua Unix socket
file", còn `127.0.0.1` là "kết nối TCP". Hai đường kết nối này có thể khớp hai account khác nhau:

```bash
# Chạy trên chính máy MySQL
mysql -u app -p -h localhost     # Unix socket: khớp 'app'@'localhost'
mysql -u app -p -h 127.0.0.1     # TCP tới loopback: xem giải thích bên dưới
```

Với kết nối TCP, server so khớp IP của client (`127.0.0.1`), và nếu bật phân giải tên máy (mặc định
bật, tắt bằng `skip_name_resolve`) thì so cả tên máy mà DNS trả về cho IP đó, thường là `localhost`.
Vì vậy kết nối qua `127.0.0.1` khớp account nào phụ thuộc cấu hình phân giải tên và những account
đang có. Đừng đoán: chạy `SELECT CURRENT_USER();` sau khi kết nối.

Với Docker, chuyện còn rõ hơn: container ứng dụng kết nối tới container MySQL qua mạng Docker, từ
một IP kiểu `172.18.0.3`. Account `'app'@'localhost'` không bao giờ khớp kết nối đó; bạn cần host
khớp với IP của container ứng dụng (dải mạng Docker, hoặc `'%'` kèm giới hạn ở lớp mạng).

### 2.5 Tạo, sửa, đổi tên, xoá account

Tạo account:

```sql
-- Dạng đơn giản nhất: dùng authentication plugin mặc định (caching_sha2_password ở 8.4)
CREATE USER 'report'@'10.0.0.0/24' IDENTIFIED BY 'mat-khau-dai-va-kho-doan';

-- Không báo lỗi nếu đã tồn tại (chỉ cảnh báo)
CREATE USER IF NOT EXISTS 'report'@'10.0.0.0/24' IDENTIFIED BY 'mat-khau-dai-va-kho-doan';

-- Để MySQL tự sinh mật khẩu ngẫu nhiên và trả về trong kết quả (một lần duy nhất)
CREATE USER 'tmp_audit'@'localhost' IDENTIFIED BY RANDOM PASSWORD;
```

Câu `IDENTIFIED BY RANDOM PASSWORD` trả về một result set có các cột `user`, `host`,
`generated password`, `auth_factor`. Mật khẩu sinh ra mặc định dài 20 ký tự (biến hệ thống
`generated_random_password_length`, nhận giá trị từ 5 tới 255). Server chỉ lưu bản đã băm, nên đây
là lần duy nhất bạn thấy mật khẩu đó.

Account mới tạo không có quyền gì cả (ngoài việc đăng nhập được). Quyền được cấp riêng bằng `GRANT`
(mục 4). Các thuộc tính không ghi trong `CREATE USER` nhận giá trị mặc định: plugin mặc định, không
yêu cầu TLS, không giới hạn tài nguyên, chính sách mật khẩu theo mặc định toàn server, không bật
theo dõi đăng nhập sai, account không bị khoá.

Sửa account dùng `ALTER USER`:

```sql
-- Đổi mật khẩu
ALTER USER 'report'@'10.0.0.0/24' IDENTIFIED BY 'mat-khau-moi';

-- Tự đổi mật khẩu của chính mình
ALTER USER USER() IDENTIFIED BY 'mat-khau-moi';

-- Khoá / mở khoá account
ALTER USER 'report'@'10.0.0.0/24' ACCOUNT LOCK;
ALTER USER 'report'@'10.0.0.0/24' ACCOUNT UNLOCK;
```

Đổi tên và xoá:

```sql
RENAME USER 'report'@'10.0.0.0/24' TO 'bi_report'@'10.0.0.0/24';
DROP USER IF EXISTS 'tmp_audit'@'localhost';
```

Xem lại account:

```sql
SELECT User, Host, plugin, account_locked FROM mysql.user;   -- cần quyền đọc schema mysql
SHOW CREATE USER 'report'@'10.0.0.0/24';                     -- toàn bộ thuộc tính của account
```

⚠️ Những chi tiết hay làm người mới bất ngờ:

- `DROP USER` không ngắt các session đang mở của user đó. Tài liệu MySQL ghi rõ: session đang mở vẫn
  tiếp tục, lần đăng nhập sau mới thất bại. Muốn đá user ra ngay, tìm session trong
  `SHOW PROCESSLIST` (hoặc `performance_schema.processlist`) rồi `KILL <id>`.
- Tương tự, khoá account (`ACCOUNT LOCK`) được kiểm tra ở giai đoạn kết nối, nên chỉ chặn các kết
  nối mới; kết nối đang mở cần `KILL` riêng.
- `DROP USER` không xoá database, bảng hay view, procedure mà user đó tạo. Nếu account đang là
  `DEFINER` của một stored object (view, procedure, trigger, event, xem
  [chương 17](17-view-procedure-trigger.md)), `DROP USER` mặc định báo lỗi để tránh tạo ra object
  "mồ côi".
- `CREATE USER ... IDENTIFIED BY 'mat-khau'` có thể bị ghi lại ở dạng chữ rõ trong file lịch sử của
  client (`~/.mysql_history`) hoặc trong log của server trong một số điều kiện. Đừng để file lịch sử
  và log ở nơi người khác đọc được.

### 2.6 Chính sách mật khẩu và khoá tạm khi đăng nhập sai

MySQL có sẵn nhiều tuỳ chọn quản lý mật khẩu, khai báo trong `CREATE USER` hoặc `ALTER USER`:

```sql
CREATE USER 'nv_an'@'10.0.0.0/24'
  IDENTIFIED BY 'mat-khau-tam'
  PASSWORD EXPIRE                    -- bắt đổi mật khẩu ngay lần đăng nhập đầu
  PASSWORD HISTORY 5                 -- không được dùng lại 5 mật khẩu gần nhất
  FAILED_LOGIN_ATTEMPTS 3            -- sai mật khẩu 3 lần liên tiếp ...
  PASSWORD_LOCK_TIME 2;              -- ... thì khoá tạm 2 ngày
```

| Tuỳ chọn | Ý nghĩa |
|---|---|
| `PASSWORD EXPIRE` | Đánh dấu mật khẩu hết hạn ngay; lần đăng nhập sau phải đổi mật khẩu |
| `PASSWORD EXPIRE INTERVAL N DAY` | Mật khẩu hết hạn sau N ngày. Mặc định toàn server là `default_password_lifetime`, giá trị mặc định 0 (không tự hết hạn) |
| `PASSWORD EXPIRE NEVER` | Không bao giờ hết hạn |
| `PASSWORD HISTORY N`, `PASSWORD REUSE INTERVAL N DAY` | Cấm dùng lại mật khẩu cũ (theo số lần hoặc theo số ngày) |
| `PASSWORD REQUIRE CURRENT` | Khi tự đổi mật khẩu, phải nhập mật khẩu hiện tại |
| `FAILED_LOGIN_ATTEMPTS N` + `PASSWORD_LOCK_TIME {N \| UNBOUNDED}` | Sai mật khẩu N lần liên tiếp thì khoá tạm N ngày (hoặc tới khi được mở khoá). Cả hai phải khác 0 thì mới có tác dụng |

Khi mật khẩu đã hết hạn, client vẫn kết nối được nhưng ở chế độ hạn chế: mọi câu lệnh đều báo lỗi
cho tới khi đổi mật khẩu:

```
mysql> SELECT 1;
ERROR 1820 (HY000): You must reset your password using ALTER USER statement before executing this statement.
mysql> ALTER USER USER() IDENTIFIED BY 'mat-khau-moi';
Query OK, 0 rows affected
```

Khi bị khoá do đăng nhập sai, client nhận lỗi dạng:

```
ERROR 3957 (HY000): Access denied for user 'nv_an'@'10.0.0.7'. Account is blocked for 2 day(s) (2 day(s) remaining) due to 3 consecutive failed logins.
```

(Output minh hoạ: câu chữ theo thông báo lỗi của MySQL 8.4, các con số và địa chỉ là ví dụ.)

Quản trị viên mở khoá bằng `ALTER USER ... ACCOUNT UNLOCK`.

⚠️ Các tuỳ chọn này hợp cho account của con người. Với account mà ứng dụng dùng, cẩn thận:

- `PASSWORD EXPIRE INTERVAL` trên account của app có nghĩa là một ngày đẹp trời app không chạy được
  câu lệnh nào nữa vì mật khẩu hết hạn. Account dịch vụ thường đặt `PASSWORD EXPIRE NEVER` và thay
  mật khẩu chủ động theo quy trình.
- `FAILED_LOGIN_ATTEMPTS` trên account của app: một lần deploy sai mật khẩu, vài worker thử kết nối
  lại là account bị khoá, kéo theo cả các instance đang chạy đúng cũng không mở được kết nối mới.
  Kẻ tấn công cũng có thể cố tình gõ sai để khoá account của app (một kiểu tấn công từ chối dịch vụ).

### 2.7 Đổi mật khẩu account ứng dụng không downtime: dual password

Bài toán: ứng dụng có 20 instance cùng dùng account `app`. Nếu đổi mật khẩu trên MySQL trước, các
instance chưa cập nhật cấu hình sẽ không kết nối được. Nếu cập nhật app trước, app dùng mật khẩu mới
khi MySQL chưa biết mật khẩu đó.

MySQL hỗ trợ *dual password*: một account có mật khẩu chính (*primary*) và mật khẩu phụ
(*secondary*), đăng nhập bằng cái nào cũng được.

```sql
-- Bước 1: đặt mật khẩu mới làm primary, giữ mật khẩu hiện tại làm secondary
ALTER USER 'app'@'10.0.0.0/24' IDENTIFIED BY 'mat-khau-B' RETAIN CURRENT PASSWORD;

-- Bước 2: (ngoài MySQL) lần lượt cập nhật cấu hình từng instance sang mat-khau-B.
--         Trong lúc này, instance cũ dùng mat-khau-A vẫn đăng nhập được.

-- Bước 3: khi mọi instance đã dùng mật khẩu mới, bỏ mật khẩu cũ
ALTER USER 'app'@'10.0.0.0/24' DISCARD OLD PASSWORD;
```

### 2.8 Giới hạn tài nguyên theo account

Có thể giới hạn mỗi account bằng mệnh đề `WITH`:

```sql
ALTER USER 'report'@'10.0.0.0/24'
  WITH MAX_USER_CONNECTIONS 10       -- tối đa 10 kết nối đồng thời
       MAX_QUERIES_PER_HOUR 5000;    -- tối đa 5000 câu lệnh mỗi giờ
```

Các tuỳ chọn: `MAX_QUERIES_PER_HOUR`, `MAX_UPDATES_PER_HOUR`, `MAX_CONNECTIONS_PER_HOUR`,
`MAX_USER_CONNECTIONS`. Với ba giới hạn theo giờ, giá trị 0 (mặc định) nghĩa là không giới hạn.
Với `MAX_USER_CONNECTIONS`, giá trị 0 nghĩa là "dùng biến toàn cục `max_user_connections`", và nếu
biến đó cũng bằng 0 thì account không bị giới hạn. `MAX_USER_CONNECTIONS` đặc
biệt hữu ích: một công cụ báo cáo viết tệ mở hàng trăm kết nối sẽ chạm giới hạn của chính nó thay vì
chiếm hết `max_connections` của cả server và làm ứng dụng chính không kết nối được.

## 3. Authentication plugin: mật khẩu được kiểm tra như thế nào

### 3.1 Authentication plugin là gì

MySQL không gắn cứng một cách kiểm tra mật khẩu. Mỗi account có một *authentication plugin* (lưu ở
cột `plugin` của `mysql.user`), là đoạn code quyết định: mật khẩu được băm thế nào khi lưu, và khi
client kết nối thì hai bên trao đổi gì để chứng minh client biết mật khẩu. Thiết kế này gọi là
*pluggable authentication*; nhờ nó MySQL có thể thêm cách xác thực mới (LDAP, Kerberos... ở bản
Enterprise) mà không đổi giao thức chung.

Hai plugin bạn sẽ gặp nhiều nhất:

| | `mysql_native_password` | `caching_sha2_password` |
|---|---|---|
| Thuật toán | Băm dựa trên SHA-1 (cách cũ, có từ trước khi có pluggable authentication) | SHA-256 |
| Tình trạng | Deprecated từ 8.0.34, tắt mặc định ở 8.4, bị gỡ bỏ từ 9.0 | Plugin mặc định của 8.4 |
| Cần kết nối bảo mật? | Không | Lần xác thực "đầy đủ" cần TLS, socket, hoặc trao đổi khoá RSA (mục 3.3) |

Plugin mặc định khi `CREATE USER ... IDENTIFIED BY` không ghi `WITH` được quyết định bởi biến hệ
thống `authentication_policy`. Giá trị mặc định của biến này ở 8.4 là `*,,`, trong đó `*` ở vị trí
đầu nghĩa là dùng `caching_sha2_password`.

### 3.2 Vì sao 8.4 tắt `mysql_native_password`

`mysql_native_password` dùng SHA-1, một hàm băm cũ và nhanh. Hàm băm càng nhanh thì kẻ lấy được
chuỗi băm càng dễ thử hàng loạt mật khẩu để dò ngược. `caching_sha2_password` dùng SHA-256 với
nhiều vòng băm (số vòng chỉnh bằng `caching_sha2_password_digest_rounds`), làm việc dò chậm hơn
nhiều.

Trong MySQL 8.4, plugin phía server `mysql_native_password` vẫn được biên dịch sẵn nhưng tắt. Hệ quả
khi nó tắt:

- Account đang dùng `mysql_native_password` không đăng nhập được (lỗi `ERROR 1045 ... Access denied`,
  server ghi lý do vào error log).
- Tạo hoặc sửa account với `IDENTIFIED WITH mysql_native_password` báo lỗi.

Muốn bật lại tạm thời (ví dụ trong lúc chuyển đổi), khởi động server với
`--mysql-native-password=ON`, hoặc thêm vào file cấu hình:

```ini
# my.cnf, phần [mysqld]
[mysqld]
mysql_native_password=ON
```

Đây chỉ nên là giải pháp tạm. Từ MySQL 9.0 plugin này bị gỡ hẳn, nên mọi account cần chuyển sang
`caching_sha2_password` trước khi lên 9.x.

### 3.3 `caching_sha2_password` hoạt động thế nào

Tên plugin có chữ "caching" vì server giữ một *cache* trong bộ nhớ gồm các cặp (account, chuỗi băm
mật khẩu) của những client đã xác thực thành công. Có hai đường xác thực:

```
Client kết nối
     │
     ▼
Account đã có trong cache?
     │
     ├── CÓ  → "fast authentication": trao đổi kiểu challenge-response,
     │         không gửi mật khẩu, không cần kết nối bảo mật. Nhanh.
     │
     └── CHƯA → "full authentication": server cần nhận được mật khẩu để
               kiểm tra với mysql.user. Mật khẩu chỉ được gửi khi:
                 • kết nối đã an toàn (TCP có TLS, Unix socket, shared memory)
                   → gửi thẳng, kênh đã bảo vệ;
                 • hoặc kết nối không mã hoá nhưng client có khoá công khai RSA
                   của server → mã hoá mật khẩu bằng RSA rồi gửi.
               Thành công → thêm account vào cache.
```

Cache bị xoá (toàn bộ hoặc theo account) khi: tạo account, đổi mật khẩu, `RENAME USER`, đổi plugin,
`DROP USER`, chạy `FLUSH PRIVILEGES` (xoá cả cache), và khi server tắt (cache không tồn tại qua lần
khởi động lại). Sau những sự kiện đó, lần kết nối đầu tiên của account lại phải đi đường "full".

Đây là nguồn của một lỗi rất hay gặp. Client kết nối TCP không TLS, không có khoá RSA, và account
chưa có trong cache:

```
ERROR 2061 (HY000): Authentication plugin 'caching_sha2_password' reported error:
Authentication requires secure connection.
```

Lỗi kiểu này thường xuất hiện "ngẫu nhiên": app chạy tốt nhiều ngày (vì account đã nằm trong cache
nhờ một kết nối nào đó qua socket hoặc TLS), rồi sau khi MySQL khởi động lại thì app không kết nối
được nữa (cache trống, kết nối đầu phải đi đường full nhưng không có kênh an toàn).

Cách xử lý, theo thứ tự nên chọn:

1. Dùng TLS cho kết nối (mục 7). Đây là cách đúng, vì đằng nào dữ liệu truyền qua mạng cũng nên mã
   hoá.
2. Cho client một bản sao khoá công khai RSA của server (client `mysql` có tuỳ chọn
   `--server-public-key-path=file`).
3. Cho client tự xin khoá công khai từ server (`--get-server-public-key` với client `mysql`). Tiện
   nhưng kém an toàn hơn cách 2, vì kẻ đứng giữa có thể đưa khoá giả; tài liệu MySQL coi cách này
   chấp nhận được trong mạng tin cậy.

### 3.4 Ứng dụng PHP và `caching_sha2_password`

PHP kết nối MySQL qua *mysqlnd* (MySQL Native Driver, dùng chung cho PDO_MySQL và mysqli). mysqlnd
hỗ trợ đầy đủ `caching_sha2_password` từ PHP 7.4.4 (theo tài liệu PDO_MYSQL trên php.net), nên với PHP 8.x bạn không cần làm
gì đặc biệt về mặt plugin. Những trục trặc thường gặp khi nâng MySQL lên 8.4:

- Account của app được tạo từ thời MySQL 5.7 hoặc 8.0 với `mysql_native_password`: sau khi lên 8.4
  app báo `Access denied`. Kiểm tra bằng `SELECT User, Host, plugin FROM mysql.user;`.
- Kết nối TCP không TLS: gặp lỗi "Authentication requires secure connection" như mục 3.3 sau mỗi
  lần MySQL khởi động lại hoặc đổi mật khẩu.
- Thư viện, công cụ cũ (client GUI đời cũ, driver của ngôn ngữ khác) chưa hỗ trợ plugin mới.

Chuyển một account sang plugin mới:

```sql
ALTER USER 'app'@'10.0.0.0/24' IDENTIFIED WITH caching_sha2_password BY 'mat-khau-hien-tai';
```

⚠️ Chuỗi băm cũ của `mysql_native_password` không chuyển đổi được sang dạng của
`caching_sha2_password` (băm là một chiều). Bạn phải biết mật khẩu dạng rõ để đặt lại, hoặc đặt mật
khẩu mới và cập nhật cấu hình app (dùng dual password ở mục 2.7 để không downtime). Vì vậy nên rà
và chuyển các account sang plugin mới khi còn ở 8.0, trước khi nâng cấp.

## 4. Quyền (privilege), `GRANT` và `REVOKE`

### 4.1 Dữ liệu mẫu cho mục 4 tới 6

Chạy bằng account quản trị (ví dụ `root`):

```sql
CREATE DATABASE shop;
USE shop;

CREATE TABLE customers (
  id        INT PRIMARY KEY AUTO_INCREMENT,
  name      VARCHAR(100) NOT NULL,
  email     VARCHAR(200) NOT NULL,
  phone     VARCHAR(20)
);

CREATE TABLE orders (
  id          INT PRIMARY KEY AUTO_INCREMENT,
  customer_id INT NOT NULL,
  total       DECIMAL(12,2) NOT NULL,
  created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id)
);

INSERT INTO customers (name, email, phone) VALUES
  ('An',   'an@example.com',   '0901000001'),
  ('Binh', 'binh@example.com', '0901000002');

INSERT INTO orders (customer_id, total) VALUES (1, 150000), (1, 70000), (2, 300000);

CREATE DATABASE hr;
CREATE TABLE hr.salaries (employee VARCHAR(100), amount DECIMAL(12,2));
INSERT INTO hr.salaries VALUES ('An', 20000000);

-- Một account để thử (host '%' cho dễ thực hành; thực tế nên giới hạn host)
CREATE USER 'lab'@'%' IDENTIFIED BY 'lab-pass-123';
```

Mở một terminal thứ hai, đăng nhập bằng `lab` để thấy tác dụng của từng lệnh:

```bash
# Nếu chạy Docker như đầu chương: chạy trên máy của bạn
docker exec -it my84 mysql -ulab -plab-pass-123
```

### 4.2 Account mới không có quyền gì

```sql
-- Session của lab
SHOW GRANTS;
-- +---------------------------------+
-- | Grants for lab@%                |
-- +---------------------------------+
-- | GRANT USAGE ON *.* TO `lab`@`%` |
-- +---------------------------------+

SELECT * FROM shop.orders;
-- ERROR 1142 (42000): SELECT command denied to user 'lab'@'localhost' for table 'orders'
```

`USAGE` nghĩa là "không có quyền nào", chỉ được đăng nhập. (Output trên là minh hoạ theo định
dạng của MySQL 8.4. Trong thông báo lỗi, phần host là host
thực tế của kết nối; ví dụ trên giả định bạn chạy client ngay trong container nên host là
`localhost`.)

### 4.3 Các cấp của quyền

Quyền trong MySQL được cấp ở nhiều cấp (*privilege level*), xác định bằng mệnh đề `ON`:

| Cấp | Cú pháp `ON` | Lưu ở | Ví dụ |
|---|---|---|---|
| Toàn cục (*global*) | `*.*` | `mysql.user` (và `mysql.global_grants` cho quyền động) | `GRANT PROCESS ON *.* TO ...` |
| Database | `shop.*` | `mysql.db` | `GRANT SELECT ON shop.* TO ...` |
| Bảng | `shop.orders` | `mysql.tables_priv` | `GRANT INSERT ON shop.orders TO ...` |
| Cột | `SELECT (col, ...)` + `ON shop.customers` | `mysql.columns_priv` | `GRANT SELECT (id, name) ON shop.customers TO ...` |
| Routine | `PROCEDURE shop.p` / `FUNCTION shop.f` | `mysql.procs_priv` | `GRANT EXECUTE ON PROCEDURE shop.p TO ...` |

Một số quyền chỉ có nghĩa ở cấp toàn cục vì chúng là quyền quản trị cả server: `CREATE USER`,
`FILE`, `PROCESS`, `RELOAD`, `REPLICATION CLIENT`, `REPLICATION SLAVE`, `SHOW DATABASES`,
`SHUTDOWN`, `SUPER`, `CREATE TABLESPACE`, `CREATE ROLE`, `DROP ROLE`, và mọi quyền động (mục 4.8).

Ở cấp cột chỉ có bốn quyền: `SELECT`, `INSERT`, `UPDATE`, `REFERENCES`.

Quyền được cộng dồn theo kiểu OR qua các cấp: quyền ở cấp cao áp dụng cho mọi thứ bên dưới, và
không có cách "từ chối" ở cấp thấp bằng việc không cấp. Ví dụ `GRANT SELECT ON *.*` cho phép đọc
mọi bảng của mọi database (kể cả `mysql`), dù bạn không cấp gì ở cấp database hay bảng.

```
Câu lệnh: SELECT name FROM shop.customers

Server kiểm tra lần lượt, chỉ cần MỘT cấp cho phép là đủ:
  có SELECT ở *.* ?                 → cho phép
  không → có SELECT ở shop.* ?      → cho phép
  không → có SELECT ở shop.customers ? → cho phép
  không → có SELECT trên cột name ? → cho phép
  không → ERROR 1142 / 1143
```

### 4.4 Các quyền thường dùng

| Quyền | Cho phép |
|---|---|
| `SELECT`, `INSERT`, `UPDATE`, `DELETE` | Đọc, thêm, sửa, xoá dòng |
| `CREATE`, `DROP` | Tạo, xoá database và bảng (`DROP` cũng cho `TRUNCATE TABLE`) |
| `ALTER` | `ALTER TABLE` |
| `INDEX` | Tạo, xoá index |
| `REFERENCES` | Tạo foreign key |
| `CREATE VIEW`, `SHOW VIEW` | Tạo view, xem định nghĩa view |
| `CREATE ROUTINE`, `ALTER ROUTINE`, `EXECUTE` | Tạo, sửa/xoá, chạy stored procedure và function |
| `TRIGGER` | Tạo, xoá trigger (quyền cấp trên bảng) |
| `EVENT` | Tạo event cho Event Scheduler |
| `CREATE TEMPORARY TABLES` | `CREATE TEMPORARY TABLE` |
| `LOCK TABLES` | `LOCK TABLES` trên bảng mà mình có `SELECT` |
| `PROCESS` | Xem câu lệnh của mọi session (`SHOW PROCESSLIST`) |
| `FILE` | Đọc, ghi file trên máy chủ database (`LOAD DATA INFILE`, `SELECT ... INTO OUTFILE`, `LOAD_FILE()`) |
| `CREATE USER` | Tạo, xoá, đổi tên account |
| `GRANT OPTION` | Cấp lại cho người khác các quyền mình đang có |
| `ALL [PRIVILEGES]` | Mọi quyền có ở cấp được chỉ định, trừ `GRANT OPTION` và `PROXY` |

`ALL` phụ thuộc cấp: `GRANT ALL ON shop.*` chỉ cấp các quyền có ở cấp database, nên không bao gồm
quyền chỉ có ở cấp toàn cục như `FILE`.

### 4.5 `GRANT`: cấp quyền

Cú pháp cơ bản:

```sql
GRANT danh_sách_quyền ON cấp TO account [, account] [WITH GRANT OPTION];
```

Thử lần lượt (chạy bằng root, rồi thử lại bằng session `lab`):

```sql
-- 1. Đọc mọi bảng trong shop
GRANT SELECT ON shop.* TO 'lab'@'%';

-- 2. Được thêm đơn hàng, chỉ trên bảng orders
GRANT INSERT ON shop.orders TO 'lab'@'%';

-- 3. Được sửa duy nhất cột phone của customers
GRANT UPDATE (phone) ON shop.customers TO 'lab'@'%';
```

Trong session `lab` (đăng nhập lại nếu cần, xem mục 4.7):

```sql
SELECT COUNT(*) FROM shop.orders;               -- 3
INSERT INTO shop.orders (customer_id, total) VALUES (2, 10000);   -- OK
UPDATE shop.customers SET phone = '0999' WHERE id = 1;            -- OK
UPDATE shop.customers SET email = 'x@y.z' WHERE id = 1;
-- ERROR 1143 (42000): UPDATE command denied to user 'lab'@'...' for column 'email' in table 'customers'
DELETE FROM shop.orders WHERE id = 4;
-- ERROR 1142 (42000): DELETE command denied to user 'lab'@'...' for table 'orders'
SELECT * FROM hr.salaries;
-- ERROR 1142 (42000): SELECT command denied to user 'lab'@'...' for table 'salaries'
```

(Output minh hoạ: câu chữ theo thông báo lỗi của MySQL 8.4, phần host `'...'` tuỳ kết nối thực tế.)
Lỗi 1142 là thiếu quyền ở cấp bảng, lỗi 1143 là thiếu quyền ở cấp cột.

Vài điểm cần biết về `GRANT`:

- Không trộn quyền và role trong cùng một câu `GRANT`. Có `ON` là cấp quyền; không có `ON` là cấp
  role (mục 6).
- Để cấp một quyền, bạn phải có chính quyền đó và có `GRANT OPTION`.
- `GRANT` không tạo account. Từ MySQL 8.0, phải `CREATE USER` trước; `GRANT ... IDENTIFIED BY`
  kiểu MySQL 5.x không còn hợp lệ.
- Có thể cấp quyền trên database hoặc bảng chưa tồn tại (cố ý, để chuẩn bị trước).
- ⚠️ `DROP DATABASE` hay `DROP TABLE` không tự thu hồi quyền đã cấp. Nếu sau này tạo lại database
  cùng tên, các quyền cũ tự áp dụng lại. (Riêng quyền cấp routine thì bị thu hồi khi xoá routine.)
- ⚠️ Ở cấp database, `_` và `%` trong tên database được hiểu là ký tự đại diện (hành vi này đã bị
  deprecated). `GRANT SELECT ON my_db.*` về lý thuyết cũng khớp database tên `myXdb`. Muốn khớp đúng
  tên, viết `` GRANT SELECT ON `my\_db`.* ``.

`WITH GRANT OPTION` cho phép account cấp lại quyền cho người khác. ⚠️ Nó áp dụng cho mọi quyền
account có ở cấp đó, kể cả quyền được cấp thêm sau này: cấp `SELECT ON shop.* WITH GRANT OPTION`
cho một account đang có `INSERT ON shop.*` thì account đó cấp được cả `INSERT` cho người khác. Hai
account khác quyền nhau mà cùng có `GRANT OPTION` có thể cấp chéo để gộp quyền. Gần như không bao
giờ cần cấp `GRANT OPTION` cho account ứng dụng.

### 4.6 `REVOKE`: thu hồi quyền

```sql
REVOKE INSERT ON shop.orders FROM 'lab'@'%';
REVOKE UPDATE (phone) ON shop.customers FROM 'lab'@'%';

-- Thu hồi mọi quyền (toàn cục, database, bảng, cột, routine), không thu hồi role
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'lab'@'%';
```

⚠️ `REVOKE` phải khớp đúng cấp đã `GRANT`. Quyền cấp ở `shop.*` nằm ở bảng `mysql.db`; câu
`REVOKE SELECT ON shop.orders` tìm ở cấp bảng (`mysql.tables_priv`), không thấy gì nên báo lỗi:

```sql
GRANT SELECT ON shop.* TO 'lab'@'%';
REVOKE SELECT ON shop.orders FROM 'lab'@'%';
-- ERROR 1147 (42000): There is no such grant defined for user 'lab' on host '%' on table 'orders'
```

Bạn không thể "cấp cả database rồi trừ đi một bảng" theo cách đó. Muốn `lab` đọc mọi bảng trừ một
bảng, hoặc cấp `SELECT` từng bảng, hoặc tách bảng nhạy cảm ra database riêng (cách thường gặp và dễ
quản lý nhất).

MySQL có tính năng *partial revokes* (biến `partial_revokes`, mặc định tắt) cho phép trừ một
database khỏi quyền toàn cục, ví dụ cấp `SELECT ON *.*` rồi `REVOKE SELECT ON hr.*`. Tính năng này
chỉ áp dụng cho trường hợp quyền toàn cục trừ đi cấp database, không áp dụng cho database trừ đi bảng.

Thêm hai biến thể hữu ích khi viết script: `REVOKE IF EXISTS ...` (thiếu quyền thì chỉ cảnh báo) và
`REVOKE ... IGNORE UNKNOWN USER` (account không tồn tại thì chỉ cảnh báo).

### 4.7 Xem quyền và thời điểm quyền có hiệu lực

```sql
SHOW GRANTS;                              -- quyền của chính mình
SHOW GRANTS FOR 'lab'@'%';                -- quyền của account khác (cần SELECT trên schema mysql)
SHOW CREATE USER 'lab'@'%';               -- thuộc tính không phải quyền: plugin, TLS, khoá...
```

Output của `SHOW GRANTS` là chính các câu `GRANT` cần chạy để tạo lại tập quyền đó, nên rất tiện để
sao chép quyền sang server khác. ⚠️ Từ 8.4, ở cấp toàn cục `SHOW GRANTS` không còn in
`ALL PRIVILEGES` mà liệt kê từng quyền, script nào đọc output này cần tính tới điều đó.

Khi bạn dùng `GRANT`, `REVOKE`, `ALTER USER`... server cập nhật bảng quyền trong bộ nhớ ngay. Với các
session đang mở, tài liệu MySQL mô tả:

| Loại thay đổi | Session đang mở thấy khi nào |
|---|---|
| Quyền cấp bảng, cột | Ngay câu lệnh tiếp theo |
| Quyền cấp database | Lần tới session chạy `USE db_name` |
| Quyền toàn cục tĩnh (static), mật khẩu | Chỉ áp dụng cho kết nối mới |
| Quyền toàn cục động (dynamic) | Ngay lập tức |

Nghĩa là khi thu hồi quyền của một account đang bị lạm dụng, kết nối cũ có thể vẫn giữ một phần quyền
cũ; muốn chắc chắn, `KILL` các kết nối của account đó.

⚠️ Không cần `FLUSH PRIVILEGES` sau `GRANT`/`REVOKE`/`CREATE USER`. `FLUSH PRIVILEGES` chỉ cần khi
ai đó sửa thẳng các bảng `mysql.*` bằng `INSERT`/`UPDATE`/`DELETE` (không nên làm): khi đó server
không biết có thay đổi cho tới khi được bảo nạp lại hoặc khởi động lại. Thêm nữa, `FLUSH PRIVILEGES`
xoá toàn bộ cache của `caching_sha2_password` (mục 3.3).

### 4.8 Quyền tĩnh, quyền động, và vì sao tránh `SUPER`

Các quyền ở bảng mục 4.4 là *static privilege* (quyền tĩnh), có sẵn trong server. Từ MySQL 8.0 có
thêm *dynamic privilege* (quyền động): do server hoặc component/plugin đăng ký lúc chạy, luôn ở cấp
toàn cục. Chúng chia nhỏ quyền `SUPER` khổng lồ ngày trước thành nhiều quyền hẹp, ví dụ:

| Quyền động | Cho phép |
|---|---|
| `SYSTEM_VARIABLES_ADMIN` | Đổi, persist biến hệ thống toàn cục |
| `CONNECTION_ADMIN` | Quản lý kết nối (giới hạn, `KILL` session của user khác...) |
| `BINLOG_ADMIN` | Điều khiển binary log |
| `REPLICATION_SLAVE_ADMIN` | Điều khiển replication |
| `BACKUP_ADMIN` | Quản trị sao lưu (ví dụ `LOCK INSTANCE FOR BACKUP`) |
| `ROLE_ADMIN` | Cấp, thu hồi role |
| `ENCRYPTION_KEY_ADMIN` | Xoay khoá mã hoá InnoDB |
| `AUDIT_ADMIN` | Cấu hình audit log (bản Enterprise) |
| `SYSTEM_USER` | Đánh dấu account hệ thống; account thường không sửa hay kill được account có quyền này |

`SUPER` vẫn tồn tại nhưng deprecated. Cấp đúng quyền động cần thiết thay vì `SUPER`.

### 4.9 Những quyền nguy hiểm

Tài liệu MySQL đặc biệt cảnh báo các quyền sau, không cấp cho account không phải quản trị:

- `FILE`: đọc vào bảng mọi file mà tiến trình MySQL đọc được trên máy chủ (kể cả file trong data
  directory), rồi `SELECT` ra; hoặc ghi file ra ổ đĩa bằng `SELECT ... INTO OUTFILE`. Biến
  `secure_file_priv` giới hạn các thao tác này trong một thư mục (gói DEB/RPM mặc định là
  `/var/lib/mysql-files`), giá trị rỗng là không giới hạn (không an toàn), `NULL` là cấm hẳn.
- `PROCESS`: xem nội dung câu lệnh đang chạy của mọi session, kể cả câu đặt hoặc đổi mật khẩu.
- `SUPER`, `SHUTDOWN`: kill session của người khác, đổi cách server chạy, tắt server.
- `GRANT OPTION`: như mục 4.5.
- `ALTER` ở cấp toàn cục hoặc trên schema `mysql`: có thể đổi tên bảng để phá hệ thống quyền.
- Bất kỳ quyền ghi nào (`INSERT`, `UPDATE`, `DROP`) trên schema `mysql`: ai sửa được
  `mysql.user.authentication_string` thì đặt được mật khẩu cho account bất kỳ, kể cả root.

Đây là lý do `GRANT ALL ON *.*` cho account ứng dụng là sai nghiêm trọng: nó bao gồm tất cả những
quyền trên.

## 5. Role: nhóm quyền có tên

### 5.1 Vì sao cần role

Giả sử công ty có 15 nhân viên phân tích dữ liệu, ai cũng cần `SELECT` trên 8 bảng báo cáo. Cấp từng
quyền cho từng người là 120 câu `GRANT`; khi thêm bảng thứ 9 lại thêm 15 câu nữa, và rất dễ sót.

*Role* là một tập quyền có tên. Bạn cấp quyền cho role một lần, rồi cấp role cho người. Thêm bảng
mới thì chỉ cần cấp cho role; mọi người có role đó tự có quyền mới. MySQL hỗ trợ role từ 8.0.

### 5.2 Tạo role và cấp cho account

```sql
-- Tạo role (tên role có dạng giống account, host mặc định là '%')
CREATE ROLE 'shop_read', 'shop_write';

-- Cấp quyền cho role: cú pháp giống cấp cho account
GRANT SELECT ON shop.* TO 'shop_read';
GRANT INSERT, UPDATE, DELETE ON shop.* TO 'shop_write';

-- Cấp role cho account: GRANT không có ON
CREATE USER 'analyst1'@'%' IDENTIFIED BY 'analyst-pass-1';
CREATE USER 'backend'@'%'  IDENTIFIED BY 'backend-pass-1';
GRANT 'shop_read' TO 'analyst1'@'%';
GRANT 'shop_read', 'shop_write' TO 'backend'@'%';
```

Role khi mới tạo bị khoá và không có mật khẩu, nên không dùng để đăng nhập được. Về bản chất MySQL
lưu role giống account (cũng nằm trong `mysql.user`), chỉ khác là bị khoá.

### 5.3 Bẫy lớn nhất: role được cấp nhưng chưa được kích hoạt

Đăng nhập bằng `analyst1` và thử:

```sql
SELECT * FROM shop.orders;
-- ERROR 1142 (42000): SELECT command denied to user 'analyst1'@'...' for table 'orders'

SELECT CURRENT_ROLE();
-- +----------------+
-- | CURRENT_ROLE() |
-- +----------------+
-- | NONE           |
-- +----------------+
```

Quyền cấp thẳng cho account thì luôn có hiệu lực. Còn role thì phải *active* (được kích hoạt) trong
session mới có tác dụng, và mặc định việc cấp role không làm nó tự kích hoạt. Ba cách kích hoạt:

```sql
-- Cách 1 (khuyên dùng): đặt default role, tự kích hoạt mỗi lần account đăng nhập
SET DEFAULT ROLE 'shop_read' TO 'analyst1'@'%';
SET DEFAULT ROLE ALL TO 'backend'@'%';       -- mọi role đã được cấp


-- Cách 2: trong session, tự bật/tắt role
SET ROLE 'shop_read';
SET ROLE ALL;
SET ROLE NONE;
SET ROLE DEFAULT;

-- Cách 3: bật biến toàn cục, mọi role đã cấp tự kích hoạt khi đăng nhập (mặc định OFF)
SET PERSIST activate_all_roles_on_login = ON;
```

Sau khi đặt default role, `analyst1` đăng nhập lại:

```sql
SELECT CURRENT_ROLE();
-- +-----------------+
-- | CURRENT_ROLE()  |
-- +-----------------+
-- | `shop_read`@`%` |
-- +-----------------+
SELECT COUNT(*) FROM shop.orders;   -- chạy được
```

`SET DEFAULT ROLE` lưu cấu hình cho các lần đăng nhập sau; session đang mở không đổi (dùng
`SET ROLE DEFAULT` để áp dụng ngay trong session).

`SET ROLE` cũng có ích theo chiều ngược lại: một account có quyền đọc và ghi đều đến từ role (như
`backend`) có thể
`SET ROLE 'shop_read'` để tự giới hạn mình chỉ đọc khi làm việc thủ công trên production, tránh lỡ
tay sửa dữ liệu. Lưu ý điều này chỉ tác dụng với quyền đến từ role; quyền cấp thẳng cho account
thì luôn có hiệu lực, `SET ROLE` không tắt được.

### 5.4 Xem quyền của role, thu hồi và xoá role

```sql
SHOW GRANTS FOR 'backend'@'%';
-- +---------------------------------------------------------+
-- | Grants for backend@%                                    |
-- +---------------------------------------------------------+
-- | GRANT USAGE ON *.* TO `backend`@`%`                     |
-- | GRANT `shop_read`@`%`,`shop_write`@`%` TO `backend`@`%` |
-- +---------------------------------------------------------+

-- Thêm USING để "mở" role ra thành quyền cụ thể
SHOW GRANTS FOR 'backend'@'%' USING 'shop_read', 'shop_write';
-- ... GRANT SELECT, INSERT, UPDATE, DELETE ON `shop`.* TO `backend`@`%` ...

REVOKE 'shop_write' FROM 'backend'@'%';     -- thu hồi role khỏi account
REVOKE DELETE ON shop.* FROM 'shop_write';  -- bớt quyền của role: mọi account có role bị ảnh hưởng
DROP ROLE 'shop_write';                     -- xoá role: tự thu hồi khỏi mọi account
```

### 5.5 Role và stored object

View, procedure, function... chạy với quyền của ai phụ thuộc thuộc tính `SQL SECURITY` của chúng
(xem [chương 17](17-view-procedure-trigger.md)):

- `SQL SECURITY INVOKER`: chạy với quyền và các role đang active trong session của người gọi.
- `SQL SECURITY DEFINER` (mặc định): chạy với quyền của account ghi ở `DEFINER`, cùng với các
  default role của account đó (hoặc mọi role đã cấp nếu `activate_all_roles_on_login` bật).

Một hệ quả dễ bị quên: nếu quyền của `DEFINER` chỉ đến từ role mà role đó không phải default role,
view hoặc procedure chạy theo kiểu `DEFINER` sẽ báo lỗi thiếu quyền.

### 5.6 Mandatory role

Biến `mandatory_roles` liệt kê các role coi như được cấp cho mọi account (vẫn cần được kích hoạt như
role thường). Role trong danh sách này không `REVOKE` hay `DROP` được. Dùng khi muốn mọi account
đều có một quyền tối thiểu chung; ít khi cần cho ứng dụng web thông thường.

## 6. Thiết kế quyền tối thiểu trong thực tế

### 6.1 Nguyên tắc quyền tối thiểu

*Principle of least privilege* (nguyên tắc quyền tối thiểu): mỗi account chỉ có đúng những quyền nó
cần để làm việc của nó, trên đúng những đối tượng nó cần, từ đúng những nơi nó cần kết nối. Không
hơn.

Lý do không phải vì "không tin đồng nghiệp", mà để giới hạn *blast radius* (phạm vi thiệt hại) khi có
sự cố: mật khẩu bị lộ, ứng dụng có lỗ SQL injection, script chạy nhầm môi trường, người gõ nhầm
lệnh. Một account chỉ đọc bị lộ thì dữ liệu bị lộ; một account `root` bị lộ thì mất cả server.

### 6.2 Tách account theo vai trò

Một hệ thống web điển hình (ví dụ ứng dụng Laravel dùng database `shop`) nên có ít nhất các account
sau, mỗi cái một mật khẩu riêng:

| Account | Dùng bởi | Quyền gợi ý | Không được có |
|---|---|---|---|
| `shop_app` | Ứng dụng khi chạy (web, queue worker) | `SELECT, INSERT, UPDATE, DELETE` trên `shop.*` (thêm `CREATE TEMPORARY TABLES`, `EXECUTE` nếu thực sự dùng) | `CREATE`, `DROP`, `ALTER`, `FILE`, `PROCESS`, `SUPER`, `GRANT OPTION`, quyền trên database khác |
| `shop_migrate` | Bước chạy migration khi deploy | Thêm `CREATE, ALTER, DROP, INDEX, REFERENCES` (và `CREATE VIEW`, `TRIGGER`, `CREATE ROUTINE`... nếu migration có tạo chúng) trên `shop.*` | Quyền toàn cục, quyền trên database khác |
| `shop_readonly` | Báo cáo, BI, dev tra cứu production | `SELECT` trên `shop.*`, hoặc chỉ các bảng/cột cần thiết | Quyền ghi; quyền đọc bảng nhạy cảm nếu không cần |
| `backup` | Công cụ sao lưu | Xem mục 10 | Quyền ghi dữ liệu |
| Account cá nhân của DBA | Con người quản trị | Theo nhu cầu, có thể rộng | Dùng chung giữa nhiều người |

```sql
-- Ứng dụng: chỉ thao tác dữ liệu, từ dải mạng của app server
CREATE USER 'shop_app'@'10.0.1.0/24' IDENTIFIED BY '...';
GRANT SELECT, INSERT, UPDATE, DELETE ON shop.* TO 'shop_app'@'10.0.1.0/24';

-- Migration: thêm quyền đổi cấu trúc, chỉ từ máy CI/CD
CREATE USER 'shop_migrate'@'10.0.9.10' IDENTIFIED BY '...';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP, INDEX, REFERENCES
  ON shop.* TO 'shop_migrate'@'10.0.9.10';

-- Chỉ đọc cho báo cáo, giới hạn số kết nối
CREATE USER 'shop_readonly'@'10.0.2.0/24' IDENTIFIED BY '...'
  WITH MAX_USER_CONNECTIONS 5;
GRANT SELECT ON shop.* TO 'shop_readonly'@'10.0.2.0/24';
```

Vài điều cần biết khi tách quyền như vậy:

- `SELECT ... FOR UPDATE` (dùng trong khoá dòng, queue dạng database với `SKIP LOCKED`) cần `SELECT`
  cộng thêm ít nhất một trong `UPDATE`, `DELETE`, `LOCK TABLES`. Account chỉ đọc không chạy được câu
  này; `SELECT ... FOR SHARE` chỉ cần `SELECT`.
- `TRUNCATE TABLE` cần quyền `DROP`, không phải `DELETE`. Nếu test hoặc job dọn dẹp dùng `TRUNCATE`
  thì account ứng dụng sẽ không chạy được; đó thường là dấu hiệu nên dùng `DELETE` hoặc chạy việc đó
  bằng account khác.
- Trong Laravel, tách account migration bằng cách cấu hình một connection riêng (ví dụ biến môi
  trường khác khi chạy `php artisan migrate` trong pipeline deploy). Cách cụ thể thuộc
  [chương 19](19-database-tu-ung-dung.md) và [chương 20](20-thay-doi-schema-migration.md).

⚠️ Thực tế nhiều đội vẫn cho app dùng một account có đủ quyền DDL vì "migration chạy trong app". Đó
là đánh đổi tiện lợi lấy rủi ro: lỗ SQL injection lúc đó có thể `DROP TABLE`. Ít nhất, đừng bao giờ
dùng `root` hay account có quyền toàn cục cho app.

### 6.3 Hạn chế theo cột và theo dòng

Quyền cấp cột giúp giấu cột nhạy cảm:

```sql
-- Nhân viên chăm sóc khách hàng xem tên và email, không xem số điện thoại
CREATE USER 'cs_staff'@'10.0.3.0/24' IDENTIFIED BY '...';
GRANT SELECT (id, name, email) ON shop.customers TO 'cs_staff'@'10.0.3.0/24';
```

Với account này, `SELECT * FROM shop.customers` bị từ chối (vì `*` bao gồm cột `phone`; lỗi trả về
là 1142 ở cấp bảng chứ không phải 1143, vì server cố ý không nêu tên cột mà account không được
thấy), còn
`SELECT id, name FROM shop.customers` chạy được. Tài liệu MySQL lưu ý: chỉ cần một account có quyền
cấp bảng, cột hoặc routine, server phải kiểm tra các quyền chi tiết đó cho mọi account, làm chậm đi
một chút. Thường không đáng kể, nhưng nên biết.

MySQL không có tính năng *row-level security* (giới hạn theo dòng) như PostgreSQL. Cách thay thế là
view với `SQL SECURITY DEFINER`: tạo view chỉ lộ ra các dòng/cột được phép, cấp `SELECT` trên view
chứ không trên bảng gốc (xem [chương 17](17-view-procedure-trigger.md)).

```sql
-- Chạy bằng admin
CREATE SQL SECURITY DEFINER VIEW shop.v_big_orders AS
  SELECT id, customer_id, total FROM shop.orders WHERE total >= 100000;

CREATE USER 'sales'@'10.0.3.0/24' IDENTIFIED BY '...';
GRANT SELECT ON shop.v_big_orders TO 'sales'@'10.0.3.0/24';
-- sales: SELECT * FROM shop.v_big_orders   -> chạy được (2 dòng: 150000 và 300000)
-- sales: SELECT * FROM shop.orders         -> ERROR 1142
```

### 6.4 Bảo vệ account `root` và các account quản trị

- Không dùng `root` cho ứng dụng hay công cụ. Mỗi người quản trị có account riêng để biết ai làm gì.
- Giới hạn host của account quản trị (ví dụ chỉ `localhost`, hoặc chỉ từ máy bastion).
- Không mở cổng MySQL ra Internet; chỉ cho phép từ app server và máy quản trị ở lớp mạng.
- Không cho account nào ngoài quản trị quyền trên schema `mysql`.
- Định kỳ rà soát: liệt kê account, plugin, host; tìm account có quyền toàn cục.

```sql
-- Account nào có quyền toàn cục đáng chú ý?
SELECT User, Host, Super_priv, File_priv, Process_priv, Grant_priv, Create_user_priv
FROM mysql.user
WHERE Super_priv = 'Y' OR File_priv = 'Y' OR Process_priv = 'Y'
   OR Grant_priv = 'Y' OR Create_user_priv = 'Y';

-- Account nào có quyền động (cấp toàn cục)?
SELECT * FROM mysql.global_grants;
```

## 7. Mã hoá đường truyền: TLS

### 7.1 Vì sao cần

Mặc định, giao thức MySQL qua TCP không mã hoá. Ai đứng được trên đường mạng giữa app server và
database (cùng mạng nội bộ, router bị chiếm, mạng của nhà cung cấp cloud giữa hai vùng) có thể đọc
toàn bộ câu SQL và kết quả: email, số điện thoại, token... và có thể sửa dữ liệu trên đường đi.

*TLS* (Transport Layer Security, hậu duệ của SSL; MySQL vẫn dùng chữ "SSL" trong tên tuỳ chọn) giải
quyết hai việc:

1. Mã hoá: người nghe lén chỉ thấy dữ liệu vô nghĩa.
2. Xác thực server: client kiểm tra chứng chỉ (*certificate*) của server để chắc mình đang nói chuyện
   với đúng server, không phải kẻ mạo danh đứng giữa (*man-in-the-middle*).

Điểm 2 hay bị bỏ qua: mã hoá mà không kiểm tra chứng chỉ thì kẻ đứng giữa vẫn có thể tự xưng là
server, nhận kết nối mã hoá từ client, giải mã, rồi chuyển tiếp.

### 7.2 Phía server

MySQL 8.4 (bản dựng với OpenSSL, như bản chính thức và image Docker) tự sinh chứng chỉ tự ký
(*self-signed*) khi khởi động nếu chưa có (biến `auto_generate_certs`, mặc định `ON`), và tự bật hỗ
trợ TLS nếu tìm thấy `ca.pem`, `server-cert.pem`, `server-key.pem` hợp lệ trong data directory. Vậy
nên trên một bản cài mới, TLS thường đã sẵn sàng.

Với production, bạn thường dùng chứng chỉ do CA của tổ chức (hoặc của nhà cung cấp cloud) cấp:

```ini
# my.cnf
[mysqld]
ssl_ca=ca.pem
ssl_cert=server-cert.pem
ssl_key=server-key.pem
require_secure_transport=ON     # từ chối mọi kết nối không an toàn
```

Các biến liên quan:

| Biến | Ý nghĩa | Mặc định 8.4 |
|---|---|---|
| `ssl_ca`, `ssl_cert`, `ssl_key` | File CA, chứng chỉ và khoá riêng của server (định dạng PEM) | Tự dò trong data directory |
| `require_secure_transport` | `ON`: chỉ chấp nhận TCP có TLS, Unix socket, shared memory; kết nối khác bị từ chối với lỗi `ER_SECURE_TRANSPORT_REQUIRED` | `OFF` |
| `tls_version` | Các phiên bản TLS được phép | `TLSv1.2,TLSv1.3` |

`require_secure_transport` có thể bật lúc chạy: `SET PERSIST require_secure_transport = ON;`.

Muốn bắt buộc TLS cho riêng một account thay vì cả server, dùng mệnh đề `REQUIRE`:

```sql
ALTER USER 'shop_app'@'10.0.1.0/24' REQUIRE SSL;    -- phải kết nối qua TLS
ALTER USER 'partner'@'203.0.113.7' REQUIRE X509;    -- phải có thêm chứng chỉ client hợp lệ
ALTER USER 'shop_app'@'10.0.1.0/24' REQUIRE NONE;   -- bỏ yêu cầu
```

`REQUIRE X509` là dạng *mutual TLS*: client cũng phải trình chứng chỉ do CA mà server tin cấp, thêm
một lớp xác thực ngoài mật khẩu. Ngoài ra còn `REQUIRE ISSUER '...'`, `SUBJECT '...'`,
`CIPHER '...'` để ràng buộc chặt hơn.

### 7.3 Phía client `mysql`: `--ssl-mode`

| `--ssl-mode` | Hành vi |
|---|---|
| `DISABLED` | Không mã hoá |
| `PREFERRED` (mặc định) | Thử TLS, không được thì lùi về kết nối không mã hoá |
| `REQUIRED` | Bắt buộc TLS, không thì thất bại. Không kiểm tra chứng chỉ server |
| `VERIFY_CA` | Bắt buộc TLS và kiểm tra chứng chỉ server do CA tin cậy cấp (cần `--ssl-ca`) |
| `VERIFY_IDENTITY` | Như `VERIFY_CA` và kiểm tra tên host trong chứng chỉ khớp tên host đang kết nối |

Tài liệu MySQL khuyên dùng `VERIFY_CA` hoặc `VERIFY_IDENTITY` để chống man-in-the-middle; chúng không
phải mặc định chỉ vì cần phân phối file CA tới mọi client. ⚠️ `VERIFY_IDENTITY` không dùng được với
chứng chỉ tự ký mà server tự sinh, vì chứng chỉ đó không chứa tên server.

```bash
# Chạy trên máy client; ca.pem là chứng chỉ CA của server
mysql -h db.internal -u shop_app -p --ssl-mode=VERIFY_IDENTITY --ssl-ca=ca.pem
```

Kiểm tra kết nối hiện tại có mã hoá không:

```sql
SHOW SESSION STATUS LIKE 'Ssl_cipher';
-- Giá trị rỗng: không mã hoá. Có giá trị (tên cipher): đang dùng TLS.
SHOW SESSION STATUS LIKE 'Ssl_version';
-- Ví dụ: TLSv1.3
```

### 7.4 Phía PHP (PDO)

Với PDO MySQL, TLS được bật bằng các thuộc tính khi tạo kết nối. PHP 8.4 thêm lớp `Pdo\Mysql` chứa
các hằng số riêng của driver MySQL; PHP 8.5 đánh dấu deprecated các hằng cũ dạng
`PDO::MYSQL_ATTR_*` và thay bằng `Pdo\Mysql::ATTR_*`:

| Hằng cũ (mọi bản PHP 8.x; deprecated từ 8.5) | Hằng mới (PHP 8.4+) |
|---|---|
| `PDO::MYSQL_ATTR_SSL_CA` | `Pdo\Mysql::ATTR_SSL_CA` |
| `PDO::MYSQL_ATTR_SSL_CERT`, `PDO::MYSQL_ATTR_SSL_KEY` | `Pdo\Mysql::ATTR_SSL_CERT`, `Pdo\Mysql::ATTR_SSL_KEY` |
| `PDO::MYSQL_ATTR_SSL_VERIFY_SERVER_CERT` | `Pdo\Mysql::ATTR_SSL_VERIFY_SERVER_CERT` |
| `PDO::MYSQL_ATTR_SERVER_PUBLIC_KEY` | `Pdo\Mysql::ATTR_SERVER_PUBLIC_KEY` |

```php
<?php
declare(strict_types=1);

// Kết nối PDO có TLS và kiểm tra chứng chỉ server (PHP 8.4+).
// Cần một MySQL server thật để chạy; đường dẫn ca.pem là ví dụ.
$pdo = new PDO(
    'mysql:host=db.internal;port=3306;dbname=shop;charset=utf8mb4',
    'shop_app',
    (string) getenv('DB_PASSWORD'),
    [
        PDO::ATTR_ERRMODE                     => PDO::ERRMODE_EXCEPTION,
        Pdo\Mysql::ATTR_SSL_CA                => '/etc/ssl/mysql/ca.pem',
        Pdo\Mysql::ATTR_SSL_VERIFY_SERVER_CERT => true,
    ],
);

$cipher = $pdo->query("SHOW SESSION STATUS LIKE 'Ssl_cipher'")->fetch(PDO::FETCH_NUM);
echo $cipher[1] === '' ? "KHÔNG mã hoá\n" : "TLS: {$cipher[1]}\n";
```

Trong Laravel 13, file `config/database.php` mặc định đã có sẵn chỗ cho CA ở connection `mysql`:

```php
'options' => extension_loaded('pdo_mysql') ? array_filter([
    Mysql::ATTR_SSL_CA => env('MYSQL_ATTR_SSL_CA'),
]) : [],
```

Nghĩa là chỉ cần đặt biến môi trường `MYSQL_ATTR_SSL_CA` trỏ tới file CA. ⚠️ Cũng trong file đó,
`'username' => env('DB_USERNAME', 'root')`: nếu quên đặt `DB_USERNAME`, app sẽ thử đăng nhập bằng
`root`. Luôn đặt rõ account ứng dụng.

⚠️ Đừng dựa vào việc "client tự chọn TLS nếu server hỗ trợ" như client `mysql` với `PREFERRED`:
cách mỗi driver xử lý mặc định khác nhau. Cách chắc chắn là khai báo tuỳ chọn TLS ở phía app, bật
`require_secure_transport` (hoặc `REQUIRE SSL` cho account) ở phía server, rồi kiểm tra `Ssl_cipher`
như trên.

Nhắc lại liên hệ với mục 3.3: khi kết nối đã có TLS, `caching_sha2_password` không cần cặp khoá RSA,
và lỗi "Authentication requires secure connection" biến mất.

## 8. Mã hoá dữ liệu khi lưu (khái niệm)

### 8.1 Dữ liệu nằm trên đĩa ở dạng nào

TLS bảo vệ dữ liệu khi đang truyền. Còn dữ liệu nằm yên trên đĩa (*data at rest*): file `.ibd` của
từng bảng, redo log, undo log, binary log, file backup. Mặc định các file này không mã hoá. Ai lấy
được file (ổ đĩa cũ bị thải mà chưa xoá, snapshot cloud bị chia sẻ nhầm, file backup trên storage để
public) có thể đọc dữ liệu mà không cần mật khẩu MySQL nào, vì họ không đi qua MySQL.

Có ba tầng mã hoá, bảo vệ trước các mối đe doạ khác nhau:

| Tầng | Ví dụ | Chống được | Không chống được |
|---|---|---|---|
| Ổ đĩa / hệ điều hành | Mã hoá volume của cloud, LUKS | Mất ổ đĩa vật lý, snapshot bị lộ (tuỳ cấu hình khoá) | Ai đọc được file khi hệ điều hành đang chạy; ai có quyền SQL |
| Database (*TDE*, Transparent Data Encryption) | InnoDB data-at-rest encryption | Lấy trộm file dữ liệu, file log | Ai có quyền SQL: MySQL giải mã trong suốt cho mọi câu lệnh hợp lệ |
| Ứng dụng | App mã hoá cột trước khi `INSERT` | Cả người có quyền SQL đọc toàn bảng, kể cả DBA, và SQL injection đọc được cột đó | Kẻ chiếm được app server (có khoá); mất khả năng tìm kiếm, sắp xếp, index trên cột mã hoá |

Chữ "transparent" (trong suốt) là then chốt: TDE mã hoá khi ghi xuống đĩa và giải mã khi đọc lên,
ứng dụng không thấy khác gì. Vì vậy TDE không giúp gì trước SQL injection hay account bị lộ.

### 8.2 InnoDB data-at-rest encryption

InnoDB hỗ trợ mã hoá tablespace file-per-table, general tablespace, tablespace hệ thống `mysql`,
redo log và undo log. Binary log và relay log được mã hoá riêng qua biến `binlog_encryption` (mặc định
`OFF`).

Cơ chế khoá hai tầng:

```
 Keyring (component_keyring_file, hoặc KMS/Vault ở bản Enterprise)
        │ giữ
        ▼
   Master key ──── mã hoá ───► Tablespace key (lưu, đã mã hoá, trong header của file .ibd)
                                     │
                                     └── mã hoá ───► dữ liệu các trang của tablespace (AES)
```

- Mỗi tablespace có khoá riêng, được mã hoá bằng master key và cất trong header của chính file đó.
- Master key nằm ngoài data directory, trong *keyring*. Bản Community có `component_keyring_file`
  (lưu khoá trong một file trên máy chủ); bản Enterprise có thêm các kết nối tới hệ thống quản lý
  khoá (KMS, HashiCorp Vault...). Tài liệu MySQL lưu ý keyring dạng file không phải giải pháp đáp
  ứng các chuẩn tuân thủ như PCI.
- *Master key rotation* (xoay khoá): `ALTER INSTANCE ROTATE INNODB MASTER KEY;` sinh master key mới
  và chỉ mã hoá lại các tablespace key (nhỏ), không phải mã hoá lại toàn bộ dữ liệu.

Khi keyring đã cấu hình, mã hoá một bảng chỉ là:

```sql
CREATE TABLE shop.payment_tokens (id INT PRIMARY KEY, token VARBINARY(255)) ENCRYPTION = 'Y';
ALTER TABLE shop.customers ENCRYPTION = 'Y';
```

Biến `default_table_encryption` đặt mặc định mã hoá cho schema và tablespace tạo mới.
`innodb_redo_log_encrypt` và `innodb_undo_log_encrypt` (mặc định tắt) bật mã hoá redo/undo log.

⚠️ Mất keyring là mất dữ liệu: không có master key thì không giải mã được tablespace key, kể cả từ
backup. Sao lưu keyring tách biệt với backup dữ liệu (để kẻ lấy được backup không có luôn khoá),
nhưng phải chắc chắn khôi phục được.

Trên dịch vụ managed (Amazon RDS, Cloud SQL...), mã hoá khi lưu thường được bật ở tầng lưu trữ bằng
một tuỳ chọn khi tạo instance, và khoá do KMS của cloud quản lý.

### 8.3 Mã hoá ở tầng ứng dụng và băm mật khẩu

Với vài cột cực nhạy cảm (số CCCD, token của bên thứ ba), mã hoá ở tầng ứng dụng bảo vệ được cả
khi kẻ tấn công đọc được bảng bằng SQL. Laravel có sẵn cast `encrypted` cho Eloquent (dùng khoá
`APP_KEY`). Đổi lại, cột mã hoá không tìm kiếm, sắp xếp hay đánh index theo giá trị gốc được.

MySQL có hàm `AES_ENCRYPT()`/`AES_DECRYPT()`, nhưng khi gọi chúng trong SQL, khoá nằm ngay trong
câu lệnh, có thể lọt vào general log, slow log, binary log (với định dạng statement), hoặc
`SHOW PROCESSLIST` của người có quyền `PROCESS`. Vì vậy mã hoá trong app thường an toàn hơn mã hoá
bằng hàm SQL.

Mật khẩu người dùng của ứng dụng thì không mã hoá mà *băm* (hash) bằng thuật toán chậm có salt như
bcrypt hoặc Argon2 (`password_hash()` trong PHP, `Hash::make()` trong Laravel). Mã hoá thì giải mã
ngược được nếu có khoá; băm thì không, và app không bao giờ cần biết lại mật khẩu gốc. Đừng dùng
`MD5()`, `SHA1()`, `SHA2()` của MySQL để lưu mật khẩu: chúng quá nhanh và không có salt tự động.

## 9. SQL injection nhìn từ phía database

### 9.1 Chuyện gì xảy ra

*SQL injection* xảy ra khi dữ liệu người dùng nhập được ghép thẳng vào chuỗi SQL, làm thay đổi cấu
trúc câu lệnh. Đoạn PHP sau chỉ in ra câu SQL sẽ được gửi đi (không kết nối database):

```php
<?php
declare(strict_types=1);

// Mô phỏng code ghép chuỗi: chỉ in ra câu SQL sẽ gửi tới MySQL, không kết nối DB.
function buildQuery(string $email): string
{
    return "SELECT id, name FROM customers WHERE email = '" . $email . "'";
}

echo buildQuery('an@example.com'), "\n";
// in ra: SELECT id, name FROM customers WHERE email = 'an@example.com'
echo buildQuery("x' OR '1'='1"), "\n";
// in ra: SELECT id, name FROM customers WHERE email = 'x' OR '1'='1'
echo buildQuery("x' UNION SELECT User, authentication_string FROM mysql.user -- "), "\n";
// in ra: SELECT id, name FROM customers WHERE email = 'x' UNION SELECT User, authentication_string FROM mysql.user -- '
```

Câu thứ hai trả về mọi khách hàng. Câu thứ ba cố đọc bảng account của MySQL; `-- ` (hai gạch ngang
và một khoảng trắng) biến phần còn lại thành comment.

Phía MySQL không có cách nào phân biệt câu đó là "do lập trình viên viết" hay "do kẻ tấn công chèn":
nó chỉ nhận một chuỗi SQL hợp lệ từ một account hợp lệ. Vì vậy cách chữa gốc nằm ở ứng dụng:
*prepared statement* với tham số (placeholder `?` hoặc `:ten`), trong đó cấu trúc câu lệnh và dữ liệu
được tách riêng, dữ liệu không bao giờ được hiểu là SQL. Chi tiết cách dùng PDO, chế độ emulated
prepares, và những chỗ không bind được tham số (tên bảng, tên cột, `ORDER BY`, danh sách `IN`) được
trình bày ở [chương 19](19-database-tu-ung-dung.md).

### 9.2 Quyền quyết định thiệt hại

Điều chương này muốn nhấn mạnh: khi lớp ứng dụng đã thủng, quyền của account là lớp phòng thủ còn
lại. Cùng một lỗ injection, thiệt hại rất khác nhau:

| Kẻ tấn công muốn | Cần quyền | Account app tối thiểu (`SELECT, INSERT, UPDATE, DELETE` trên `shop.*`) |
|---|---|---|
| Đọc dữ liệu của app | `SELECT` trên `shop` | Làm được. Đây là thiệt hại không tránh khỏi |
| Sửa, xoá dữ liệu của app | `UPDATE`, `DELETE` | Làm được |
| Đọc database khác (`hr.salaries`) | `SELECT` trên database đó | Không |
| Đọc `mysql.user` lấy chuỗi băm mật khẩu | `SELECT` trên schema `mysql` | Không |
| Liệt kê bảng, cột qua `information_schema` | Không cần quyền riêng, nhưng chỉ thấy đối tượng mình có quyền | Chỉ thấy bảng của `shop` |
| `DROP TABLE`, `ALTER TABLE` | `DROP`, `ALTER` | Không |
| Đọc file hệ thống bằng `LOAD_FILE('/etc/passwd')`, ghi webshell bằng `SELECT ... INTO OUTFILE` | `FILE` (và `secure_file_priv` cho phép) | Không |
| Tạo account mới để quay lại sau | `CREATE USER` hoặc quyền ghi trên `mysql` | Không |
| Xem câu lệnh (kèm dữ liệu) của session khác | `PROCESS` | Không |

Một số điểm khác từ phía database:

- *Stacked queries* (nhiều câu lệnh cách nhau bởi `;` trong một lần gửi, ví dụ
  `x'; DROP TABLE orders; -- `) chỉ chạy được khi driver bật chế độ nhiều câu lệnh. PDO MySQL có
  thuộc tính `Pdo\Mysql::ATTR_MULTI_STATEMENTS` (PHP 8.4+, tên cũ `PDO::MYSQL_ATTR_MULTI_STATEMENTS`)
  để tắt chế độ này; đặt `false` là một lớp phòng thủ thêm. Không có stacked queries thì kẻ tấn công
  vẫn khai thác được bằng `UNION`, điều kiện boolean, hoặc theo thời gian (`SLEEP()`), nên đây không
  thay thế được prepared statement.
- Dynamic SQL trong stored procedure (`PREPARE stmt FROM CONCAT(...)`) cũng bị injection nếu ghép
  tham số vào chuỗi. Trong procedure, dùng `PREPARE ... FROM 'SELECT ... WHERE id = ?'` rồi
  `EXECUTE stmt USING @bien` (xem [chương 17](17-view-procedure-trigger.md)).
- Đừng hiển thị thông báo lỗi SQL thô cho người dùng cuối: chúng tiết lộ tên bảng, cột, phiên bản và
  giúp kẻ tấn công dò cấu trúc.
- `MAX_USER_CONNECTIONS`, `MAX_QUERIES_PER_HOUR` (mục 2.8) có thể làm chậm việc dò dữ liệu tự động,
  nhưng cẩn thận đừng đặt quá thấp làm nghẽn chính ứng dụng.

## 10. Sao lưu và quyền

Cách sao lưu, khôi phục chi tiết thuộc [chương 21](21-backup-restore.md). Ở đây chỉ nói về khía cạnh
bảo mật.

### 10.1 Account riêng cho sao lưu

Công cụ sao lưu cần đọc mọi thứ, nhưng không cần ghi. Đừng dùng `root`. Với `mysqldump`, tài liệu
MySQL 8.4 liệt kê quyền tối thiểu: `SELECT` cho bảng được dump, `SHOW VIEW` cho view, `TRIGGER` cho
trigger, `LOCK TABLES` nếu không dùng `--single-transaction`, `PROCESS` nếu không dùng
`--no-tablespaces`, và `RELOAD` hoặc `FLUSH_TABLES` khi dùng `--single-transaction` cùng GTID. Một
số tuỳ chọn khác cần thêm quyền riêng (ví dụ dump event cần `EVENT`).

```sql
CREATE USER 'backup'@'localhost' IDENTIFIED BY '...';
GRANT SELECT, SHOW VIEW, TRIGGER, EVENT ON shop.* TO 'backup'@'localhost';
-- Thêm tuỳ theo cách chạy:
-- GRANT LOCK TABLES ON shop.* TO 'backup'@'localhost';   -- nếu không dùng --single-transaction
-- GRANT PROCESS ON *.* TO 'backup'@'localhost';          -- nếu không dùng --no-tablespaces
```

Công cụ sao lưu vật lý (MySQL Enterprise Backup, Percona XtraBackup) cần các quyền khác như
`BACKUP_ADMIN` (cho `LOCK INSTANCE FOR BACKUP`); làm theo tài liệu của công cụ.

Đọc mật khẩu từ file cấu hình có quyền hạn chế thay vì ghi trên dòng lệnh (`-p'mat-khau'` lộ trong
danh sách tiến trình của hệ điều hành và lịch sử shell):

```ini
# ~/.my.cnf của user hệ điều hành chạy backup, chmod 600
[mysqldump]
user=backup
password=...
```

### 10.2 Backup là bản sao toàn bộ dữ liệu

- File dump chứa mọi dữ liệu ở dạng chữ rõ, kể cả cột email, số điện thoại, và nếu dump schema
  `mysql` thì có cả chuỗi băm mật khẩu của các account. Ai lấy được file backup là có toàn bộ
  database mà không cần qua bất kỳ lớp `GRANT` nào.
- Mã hoá file backup (ví dụ bằng công cụ mã hoá trước khi đẩy lên storage, hoặc mã hoá phía server
  của storage), giới hạn quyền truy cập nơi lưu, và ghi log ai tải backup.
- Khôi phục backup cũng là một thao tác cần quyền lớn: để chạy lại file dump bạn cần quyền thực
  hiện mọi câu lệnh trong đó (`CREATE`, `INSERT`, và `ALTER` nếu dump có `ALTER DATABASE`).
- Bản dump production đem về máy dev hoặc môi trường test là một nguồn rò rỉ dữ liệu phổ biến. Nếu
  cần dữ liệu thật cho test, ẩn danh hoá (*anonymize*) trước.
- Nếu dùng TDE (mục 8.2): backup vật lý của tablespace mã hoá cần keyring để khôi phục; còn
  `mysqldump` đọc qua SQL nên file dump ra là chữ rõ, không được TDE bảo vệ.

## 11. Audit: ai đã làm gì, khi nào (khái niệm)

### 11.1 Vì sao cần audit

Phân quyền trả lời "ai được làm gì". *Audit* (kiểm toán, ghi vết) trả lời "ai đã thực sự làm gì": ai
đăng nhập lúc mấy giờ, từ đâu, đã chạy những câu lệnh nào trên bảng nào. Cần audit để:

- Điều tra sự cố: dữ liệu bị xoá lúc nào, bởi account nào.
- Phát hiện bất thường: account báo cáo đột nhiên đọc bảng lương, đăng nhập sai liên tục.
- Đáp ứng yêu cầu tuân thủ (PCI DSS, các quy định bảo vệ dữ liệu cá nhân) thường đòi hỏi lưu vết
  truy cập dữ liệu nhạy cảm.

Audit chỉ có ý nghĩa khi mỗi người, mỗi dịch vụ có account riêng. Nếu cả đội dùng chung một account
`admin`, log chỉ cho biết "admin đã xoá bảng".

### 11.2 Các lựa chọn với MySQL

| Cách | Ghi được gì | Ghi chú |
|---|---|---|
| MySQL Enterprise Audit (plugin `audit_log`) | Kết nối, ngắt kết nối, câu lệnh, bảng được truy cập; có bộ lọc theo account, loại sự kiện | Chỉ có trong bản Enterprise (thương mại). Mặc định ghi file `audit.log` trong data directory, định dạng XML |
| Plugin audit của các bản phân phối khác | Tương tự | Percona Server và MariaDB có plugin audit riêng; kiểm tra tài liệu của bản bạn dùng |
| General query log (`general_log`) | Mọi câu lệnh mọi session nhận được | Có sẵn ở mọi bản nhưng rất nặng và không có bộ lọc; chỉ hợp để gỡ lỗi ngắn hạn, không phải audit lâu dài |
| Binary log | Mọi thay đổi dữ liệu (không có `SELECT`) | Mục đích chính là replication và khôi phục theo thời điểm (chương 21, 22); không ghi việc đọc |
| Audit ở tầng ứng dụng | Hành động nghiệp vụ: "nhân viên X sửa đơn hàng Y" | Thường hữu ích nhất cho nghiệp vụ, vì database chỉ thấy account `shop_app` chung |
| Dịch vụ managed | Tuỳ nhà cung cấp (ví dụ Amazon RDS cho MySQL hỗ trợ plugin audit trong option group) | Xem tài liệu cloud |

Với PostgreSQL, công cụ tương ứng phổ biến là extension `pgaudit` (đối chiếu ở
[chương 25](25-postgres-doi-chieu.md)).

### 11.3 Nguyên tắc với log audit

- Log audit phải nằm ngoài tầm sửa của người bị audit: đẩy sang hệ thống log tập trung, account
  quản trị database không xoá được.
- Log có thể chứa dữ liệu nhạy cảm (giá trị trong câu lệnh). Bảo vệ nó như bảo vệ dữ liệu.
- Ghi quá nhiều thì không ai đọc và tốn tài nguyên; ghi theo bộ lọc: đăng nhập thất bại, thao tác
  của account quản trị, truy cập bảng nhạy cảm, mọi DDL và thay đổi quyền.
- Đặt cảnh báo cho các sự kiện quan trọng (`GRANT`, `CREATE USER`, đăng nhập `root` từ host lạ)
  thay vì chỉ lưu để đó.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| App dùng `root` hoặc account có `ALL ON *.*` | Tiện lúc đầu, quên đổi | Account riêng cho app chỉ có `SELECT, INSERT, UPDATE, DELETE` trên database của nó (mục 6.2) |
| Đăng nhập được nhưng quyền "lạ", hoặc `Access denied` dù mật khẩu đúng | Kết nối khớp một account khác (anonymous user, host cụ thể hơn, `localhost` khác `127.0.0.1`) | `SELECT CURRENT_USER();`, xoá anonymous user, tạo account đúng host (mục 2.3, 2.4) |
| Account `'app'@'localhost'` không kết nối được từ container khác | Kết nối qua mạng Docker đến từ IP của container, không phải `localhost` | Host theo dải mạng của app, hoặc `'%'` kèm firewall |
| Sau khi nâng lên 8.4, app báo `Access denied` | Account dùng `mysql_native_password`, plugin này tắt mặc định | Chuyển sang `caching_sha2_password` trước khi nâng cấp (mục 3.4) |
| "Authentication requires secure connection" xuất hiện sau khi MySQL khởi động lại | Cache của `caching_sha2_password` trống, kết nối TCP không TLS, không có khoá RSA | Dùng TLS cho kết nối (mục 3.3, 7) |
| Đã `GRANT` role nhưng vẫn bị từ chối | Role chưa được kích hoạt, `CURRENT_ROLE()` là `NONE` | `SET DEFAULT ROLE` cho account (mục 5.3) |
| `REVOKE SELECT ON shop.orders` báo lỗi 1147 dù account đọc được `orders` | Quyền được cấp ở cấp database (`shop.*`), `REVOKE` phải khớp đúng cấp | Thu hồi ở đúng cấp; tách bảng nhạy cảm ra database riêng (mục 4.6) |
| Thu hồi quyền hoặc khoá account nhưng session cũ vẫn chạy | `DROP USER`, `ACCOUNT LOCK` chỉ chặn kết nối mới; quyền toàn cục tĩnh chỉ áp dụng cho kết nối mới | `KILL` các kết nối của account (mục 2.5, 4.7) |
| Chạy `FLUSH PRIVILEGES` sau mỗi `GRANT` "cho chắc" | Thói quen từ thời sửa thẳng bảng `mysql.*` | Không cần; nó còn xoá cache xác thực của mọi account (mục 4.7) |
| Đặt `PASSWORD EXPIRE INTERVAL` hoặc `FAILED_LOGIN_ATTEMPTS` cho account của app | Áp chính sách dành cho người lên account dịch vụ | App: `PASSWORD EXPIRE NEVER`, đổi mật khẩu chủ động bằng dual password (mục 2.6, 2.7) |
| Tin rằng bật TDE là chống được SQL injection | TDE chỉ bảo vệ file trên đĩa, giải mã trong suốt cho mọi câu SQL hợp lệ | Prepared statement + quyền tối thiểu; mã hoá ở tầng app cho cột cực nhạy cảm (mục 8) |
| TLS "đang bật" nhưng thực ra không kiểm tra chứng chỉ server | Dùng `REQUIRED`/mặc định thay vì `VERIFY_CA`/`VERIFY_IDENTITY` | Phân phối CA cho client, bật kiểm tra chứng chỉ (mục 7.3, 7.4) |
| File backup để ở nơi nhiều người đọc được | Coi backup là "file phụ" | Mã hoá backup, giới hạn truy cập, account backup chỉ đọc (mục 10) |
| Cấp `GRANT ... ON my_db.*` và vô tình khớp database khác | `_` là ký tự đại diện ở cấp database | Viết `` `my\_db`.* `` (mục 4.5) |

## Tóm tắt chương

- MySQL kiểm soát truy cập theo hai giai đoạn: xác thực kết nối (account, plugin, trạng thái khoá),
  rồi kiểm tra quyền cho từng câu lệnh.
- Account là cặp `'user'@'host'`; server dùng dòng khớp đầu tiên sau khi sắp xếp theo độ cụ thể của
  host. `CURRENT_USER()` cho biết server thực sự coi bạn là account nào.
- MySQL 8.4 dùng `caching_sha2_password` mặc định; `mysql_native_password` tắt mặc định và bị gỡ ở 9.0.
  Lần xác thực đầy đủ của `caching_sha2_password` cần TLS, socket, hoặc khoá RSA.
- Quyền cấp ở các mức toàn cục, database, bảng, cột, routine, cộng dồn theo kiểu OR. `REVOKE` phải
  khớp đúng cấp đã cấp. `GRANT`/`REVOKE` có hiệu lực ngay, không cần `FLUSH PRIVILEGES`.
- Role gom quyền thành nhóm có tên; role phải được kích hoạt (default role) mới có tác dụng.
- Quyền tối thiểu: tách account cho app, migration, báo cáo, backup; không cấp `FILE`, `PROCESS`,
  `SUPER`, `GRANT OPTION`, quyền trên schema `mysql` cho account không phải quản trị.
- TLS mã hoá đường truyền; chỉ chống được man-in-the-middle khi client kiểm tra chứng chỉ server.
- Mã hoá khi lưu (TDE) bảo vệ file trên đĩa, không bảo vệ trước người có quyền SQL. Mật khẩu người
  dùng của app phải băm bằng bcrypt/Argon2 ở tầng app.
- SQL injection chữa ở ứng dụng bằng prepared statement; quyền tối thiểu quyết định thiệt hại khi lỗ
  hổng vẫn xảy ra.
- Backup là bản sao toàn bộ dữ liệu, cần bảo vệ như database; audit cần account riêng cho từng người
  và log nằm ngoài tầm sửa của người bị audit.

## Câu hỏi tự kiểm tra

1. `ERROR 1045` và `ERROR 1142` khác nhau thế nào về giai đoạn kiểm soát truy cập? (mục 1.3)
2. Bảng `mysql.user` có hai account `'jeffrey'@'%'` và `''@'localhost'`. Jeffrey kết nối qua Unix
   socket trên máy chủ. Server dùng account nào, và làm
   sao để kiểm chứng? (mục 2.3)
3. Vì sao một app chạy ổn nhiều ngày lại đột nhiên gặp lỗi "Authentication requires secure
   connection" ngay sau khi MySQL khởi động lại? Nêu hai cách sửa. (mục 3.3)
4. Account `u` được `GRANT SELECT ON shop.*`. Sau đó admin chạy `REVOKE SELECT ON shop.orders FROM u`.
   Kết quả là gì và vì sao? Muốn `u` đọc mọi bảng trừ `orders` thì làm thế nào? (mục 4.6)
5. Admin thu hồi một quyền toàn cục tĩnh (ví dụ `PROCESS`) của account đang có kết nối mở. Kết nối
   đó còn dùng được quyền này không? Còn quyền cấp bảng thì sao? (mục 4.7)
6. Đã `GRANT 'shop_read' TO 'analyst1'@'%'`, nhưng analyst1 vẫn bị từ chối `SELECT`. Vì sao, và sửa
   bằng lệnh gì? (mục 5.3)
7. Liệt kê các account bạn sẽ tạo cho một ứng dụng Laravel có migration chạy trong pipeline deploy và
   một công cụ BI, kèm quyền của từng account. (mục 6.2)
8. `--ssl-mode=REQUIRED` khác `--ssl-mode=VERIFY_IDENTITY` ở điểm nào về an ninh? (mục 7.3)
9. Bật InnoDB data-at-rest encryption có giúp gì khi ứng dụng bị SQL injection không? Vì sao? (mục 8.1)
10. Với account app chỉ có `SELECT, INSERT, UPDATE, DELETE` trên `shop.*`, một lỗ SQL injection có
    thể đọc file `/etc/passwd` của máy chủ database không? Cần quyền gì để làm được? (mục 9.2)

## Bài tập

Làm trên MySQL 8.4 riêng để học (ví dụ container Docker ở đầu chương), dùng dữ liệu mẫu mục 4.1.

1. **Thí nghiệm khớp account.** Tạo hai account `'demo'@'localhost'` và `'demo'@'%'` với hai mật
   khẩu khác nhau, cấp cho mỗi cái một quyền khác nhau (ví dụ `SELECT` trên `shop.orders` cho cái
   thứ nhất, `SELECT` trên `shop.customers` cho cái thứ hai). Kết nối lần lượt bằng
   `mysql -h localhost` và `mysql -h 127.0.0.1` (bên trong container), mỗi lần chạy
   `SELECT USER(), CURRENT_USER();` và thử đọc hai bảng. Ghi lại kết quả và giải thích theo quy tắc
   sắp xếp ở mục 2.3. Kết thúc bằng việc xoá cả hai account.

2. **Thiết kế quyền cho `shop`.** Viết một file SQL tạo đủ các account và role sau, rồi kiểm chứng
   bằng cách đăng nhập từng account và chạy thử các câu lệnh được phép và bị cấm (ghi lại mã lỗi):
   - role `shop_read` (đọc `shop`), `shop_write` (ghi dữ liệu `shop`), `shop_ddl` (đổi cấu trúc
     `shop`);
   - account `shop_app` (dùng `shop_read` + `shop_write`), `shop_migrate` (cả ba role),
     `shop_bi` (chỉ `shop_read`, tối đa 3 kết nối đồng thời);
   - account `cs_staff` chỉ được đọc cột `id`, `name`, `email` của `customers` và không đọc được
     `orders`;
   - đặt default role đúng cho từng account. Kiểm tra bằng `SHOW GRANTS ... USING ...` và
     `CURRENT_ROLE()`.

3. **TLS.** Trong container, kiểm tra server có hỗ trợ TLS không (xem `SHOW VARIABLES LIKE 'ssl%'` và
   error log khi khởi động), kết nối bằng `--ssl-mode=DISABLED` và `--ssl-mode=REQUIRED`, mỗi lần xem
   `SHOW SESSION STATUS LIKE 'Ssl_cipher'`. Sau đó đặt `REQUIRE SSL` cho account `shop_app` và chứng
   minh kết nối không TLS bị từ chối. Thử thêm: tạo account mới, kết nối lần đầu bằng
   `--ssl-mode=DISABLED` qua TCP và giải thích lỗi nhận được (mục 3.3).

4. **Rà soát bảo mật.** Viết một bộ câu truy vấn (chạy bằng admin) để trả lời: account nào có host
   `'%'`; account nào còn dùng plugin khác `caching_sha2_password`; account nào có quyền toàn cục
   nguy hiểm (mục 4.9); account nào có quyền trên schema `mysql`; có anonymous user không. Chạy trên
   server thực hành và viết vài dòng nhận xét cho từng phát hiện.

## Đọc thêm

- MySQL 8.4 Reference Manual, [Access Control and Account Management](https://dev.mysql.com/doc/refman/8.4/en/access-control.html),
  đặc biệt [Specifying Account Names](https://dev.mysql.com/doc/refman/8.4/en/account-names.html),
  [Connection Verification](https://dev.mysql.com/doc/refman/8.4/en/connection-access.html),
  [When Privilege Changes Take Effect](https://dev.mysql.com/doc/refman/8.4/en/privilege-changes.html).
- [CREATE USER](https://dev.mysql.com/doc/refman/8.4/en/create-user.html),
  [DROP USER](https://dev.mysql.com/doc/refman/8.4/en/drop-user.html),
  [GRANT](https://dev.mysql.com/doc/refman/8.4/en/grant.html),
  [REVOKE](https://dev.mysql.com/doc/refman/8.4/en/revoke.html),
  [SHOW GRANTS](https://dev.mysql.com/doc/refman/8.4/en/show-grants.html).
- [Privileges Provided by MySQL](https://dev.mysql.com/doc/refman/8.4/en/privileges-provided.html)
  (bảng quyền tĩnh/động và mục Privilege-Granting Guidelines).
- [Using Roles](https://dev.mysql.com/doc/refman/8.4/en/roles.html),
  [Privilege Restriction Using Partial Revokes](https://dev.mysql.com/doc/refman/8.4/en/partial-revokes.html).
- [Password Management](https://dev.mysql.com/doc/refman/8.4/en/password-management.html),
  [Account Locking](https://dev.mysql.com/doc/refman/8.4/en/account-locking.html),
  [Setting Account Resource Limits](https://dev.mysql.com/doc/refman/8.4/en/user-resources.html).
- [Caching SHA-2 Pluggable Authentication](https://dev.mysql.com/doc/refman/8.4/en/caching-sha2-pluggable-authentication.html),
  [Native Pluggable Authentication](https://dev.mysql.com/doc/refman/8.4/en/native-pluggable-authentication.html).
- [Using Encrypted Connections](https://dev.mysql.com/doc/refman/8.4/en/using-encrypted-connections.html).
- [InnoDB Data-at-Rest Encryption](https://dev.mysql.com/doc/refman/8.4/en/innodb-data-encryption.html).
- [mysqldump](https://dev.mysql.com/doc/refman/8.4/en/mysqldump.html) (mục quyền cần thiết),
  biến [`secure_file_priv`](https://dev.mysql.com/doc/refman/8.4/en/server-system-variables.html#sysvar_secure_file_priv).
- [MySQL Enterprise Audit](https://dev.mysql.com/doc/refman/8.4/en/audit-log.html).
- PHP: [php-src UPGRADING 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) (hằng
  `PDO::MYSQL_ATTR_*` deprecated, thay bằng `Pdo\Mysql::ATTR_*`).
- Laravel 13: [`config/database.php` của laravel/laravel](https://github.com/laravel/laravel/blob/13.x/config/database.php).
- OWASP: [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).
