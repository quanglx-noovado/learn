# Chương 18. PHP-FPM, Nginx và OPcache trên production

> [← Mục lục](README.md) · [← Chương 17: Bảo mật ứng dụng PHP](17-bao-mat.md) · [Chương 19: Bên trong Zend Engine →](19-ben-trong-engine.md)

**Bạn sẽ học được:**

- PHP-FPM tổ chức process ra sao (master, pool, worker), ba chế độ `pm` khác nhau thế nào, và cách
  tính `pm.max_children` theo RAM thật (RSS, PSS) thay vì đoán.
- Các timeout ở FPM và Nginx, slow log, status page: công cụ để biết worker đang kẹt ở đâu, và đọc
  lỗi 502/504 thành nguyên nhân cụ thể.
- Cấu hình Nginx cho PHP từng dòng: `fastcgi_pass`, `SCRIPT_FILENAME`, `$realpath_root`, và vì sao
  chỉ nên cho chạy đúng một file `index.php`.
- Cấu hình OPcache cho production, đọc `opcache_get_status()`, xoá cache đúng cách khi deploy; preloading
  và JIT ở mức vận hành: bật thế nào, khi nào nên, cái giá là gì.
- Deploy không downtime bằng symlink, và những cái bẫy khiến "deploy xong vẫn chạy code cũ".
- Chạy PHP-FPM trong Docker/Kubernetes: image chính thức, dừng êm bằng `SIGQUIT`, log ra stdout.

**Cần biết trước:** [Chương 02](02-php-chay-nhu-the-nao.md) (SAPI, vòng đời process và request,
OPcache ở mức khái niệm, đường đi của một request qua Nginx và FPM),
[chương 15](15-php-va-web.md) (HTTP, header, `$_SERVER`). Biết dùng terminal Linux cơ bản (`ps`,
`curl`, `kill`).

Chương này nói về *vận hành*: cấu hình, đo đạc, xử lý sự cố. Phần lớn ví dụ là file cấu hình và lệnh
shell chạy trên server Linux hoặc trong container, không phải script PHP chạy một mình. Mục 1.3 dựng
sẵn một phòng thí nghiệm bằng Docker để bạn tự thử mọi thứ trong chương.

## 1. Từ máy dev tới production: bức tranh tổng thể

### 1.1 Vì sao không chạy `php -S` trên production

Ở [chương 01](01-php-la-gi.md) bạn đã chạy web bằng `php -S localhost:8000`. Tiện, nhưng php.net ghi
rõ trong cảnh báo của built-in web server:

- nó được thiết kế để hỗ trợ phát triển, "không nhằm làm một web server đầy đủ tính năng" và "không
  được dùng trên mạng công khai";
- nó chạy **một process đơn luồng**, nên một request bị treo (chờ API ngoài chẳng hạn) làm mọi request
  khác đứng theo. Từ PHP 7.4 có biến môi trường `PHP_CLI_SERVER_WORKERS` để fork nhiều worker, nhưng
  mục đích chỉ là để test code cần nhiều request đồng thời.

Một server production cần nhiều thứ hơn thế: phục vụ hàng trăm request cùng lúc, trả file tĩnh (ảnh,
CSS, JS) thật nhanh mà không đụng tới PHP, TLS (HTTPS), nén gzip, giới hạn kích thước upload, tự thay
process chết, khởi động lại mà không rớt request, đo được đang bận tới đâu. Không chương trình nào làm
hết; người ta ghép ba mảnh lại.

### 1.2 Ba mảnh ghép: Nginx, PHP-FPM, OPcache

```
 Trình duyệt / app mobile
        │  HTTPS
        ▼
┌─────────────────────────┐
│ Nginx                   │  TLS, gzip, file tĩnh, giới hạn body, timeout phía client.
│                         │  Gặp request cần PHP thì chuyển tiếp (fastcgi_pass).
└───────────┬─────────────┘
            │  FastCGI qua unix socket hoặc TCP          (mục 7)
            ▼
┌─────────────────────────────────────────────────────┐
│ PHP-FPM                                             │
│   master process: đọc cấu hình, quản lý worker      │  (mục 2 tới 6)
│   worker 1  worker 2  ...  worker N                 │
│       │         │              │                    │
│       └────┬────┴──────────────┘                    │
│            ▼                                        │
│   OPcache (shared memory): opcode đã biên dịch,     │  (mục 8 tới 10)
│   dùng chung cho mọi worker                         │
└─────────────────────────────────────────────────────┘
            │
            ▼
      MySQL, Redis, API ngoài...
```

- *Nginx* (đọc là "engine-x") là web server: nhận kết nối HTTP(S) từ client, tự trả file tĩnh, và
  chuyển các request cần chạy PHP sang PHP-FPM. Nginx không biết chạy PHP.
- *PHP-FPM* (FastCGI Process Manager) là SAPI `fpm-fcgi` mà bạn đã gặp ở
  [chương 02](02-php-chay-nhu-the-nao.md#4-sapi-cầu-nối-giữa-php-và-thế-giới-bên-ngoài): một chương
  trình giữ sẵn một nhóm process PHP (*worker*), nhận request từ Nginx qua giao thức *FastCGI*, chạy
  script, trả output về.
- *OPcache* là extension nằm **bên trong** mỗi process PHP-FPM. Nó giữ opcode đã biên dịch trong vùng
  bộ nhớ dùng chung (*shared memory*) để các worker khỏi phải parse và biên dịch lại file ở mỗi request.

Vì sao tách Nginx và PHP-FPM thành hai chương trình? Vì hai việc có tính chất rất khác nhau:

| | Nginx | PHP-FPM worker |
|---|---|---|
| Việc chính | Chuyển byte: đọc request, gửi file, giữ kết nối chậm | Chạy code ứng dụng: tính toán, gọi DB |
| Mô hình | Vài process, mỗi process một *event loop* giữ hàng nghìn kết nối | Mỗi worker xử lý **một** request tại một thời điểm |
| Chi phí một kết nối đang chờ | Rất nhỏ | Nguyên một process PHP (với app dùng framework thường vài chục MB) |

Hệ quả thực tế: một client mạng chậm (điện thoại 3G tải response 2 MB) chỉ chiếm một kết nối rẻ của
Nginx. Nginx nhận trọn response từ PHP-FPM vào buffer rồi tự gửi dần cho client, còn worker PHP được
giải phóng ngay để phục vụ request khác (mục 7.5 nói về buffer).

⚠️ Ba mảnh này có ba bộ cấu hình riêng, ở ba nơi khác nhau: `nginx.conf` (và các file nó `include`),
`php-fpm.conf` cùng các file pool, và `php.ini` (nơi đặt `opcache.*`, `memory_limit`...). Rất nhiều sự
cố production đến từ việc sửa đúng giá trị nhưng sai file, hoặc sửa xong quên reload đúng chương trình.

### 1.3 Phòng thí nghiệm: Nginx và PHP-FPM bằng Docker Compose

Để tự thử mọi thứ trong chương mà không cài gì vào máy, dựng một thư mục như sau (chỉ cần Docker và
Docker Compose):

```
fpm-lab/
├── compose.yaml
├── nginx.conf
└── public/
    └── index.php
```

`compose.yaml`:

```yaml
services:
  php:
    image: php:8.5-fpm              # image chính thức, có sẵn PHP-FPM (mục 12)
    volumes:
      - ./public:/var/www/html/public
  nginx:
    image: nginx:stable
    ports:
      - "8080:80"
    volumes:
      - ./public:/var/www/html/public:ro
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - php
```

`nginx.conf` (ý nghĩa từng dòng ở mục 7):

```nginx
server {
    listen 80;
    root /var/www/html/public;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ ^/index\.php(/|$) {
        fastcgi_pass php:9000;     # "php" là tên service trong compose.yaml
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
    }
}
```

`public/index.php`:

```php
<?php
declare(strict_types=1);

header('Content-Type: text/plain; charset=utf-8');

$opcache = function_exists('opcache_get_status') ? opcache_get_status(false) : false;

echo 'SAPI            : ', PHP_SAPI, "\n";
echo 'PHP             : ', PHP_VERSION, "\n";
echo 'PID của worker  : ', getmypid(), "\n";
echo 'SCRIPT_FILENAME : ', $_SERVER['SCRIPT_FILENAME'] ?? '-', "\n";
echo 'REQUEST_URI     : ', $_SERVER['REQUEST_URI'] ?? '-', "\n";
echo 'OPcache         : ', $opcache === false ? 'tắt' : 'bật', "\n";
```

Chạy (trong thư mục `fpm-lab/`):

```bash
docker compose up -d
curl -s http://localhost:8080/san-pham/42
```

Output minh hoạ (PID và bản vá PHP trên máy bạn sẽ khác):

```
SAPI            : fpm-fcgi
PHP             : 8.5.x
PID của worker  : 8
SCRIPT_FILENAME : /var/www/html/public/index.php
REQUEST_URI     : /san-pham/42
OPcache         : bật
```

Đọc output:

- `SAPI` là `fpm-fcgi`: script đang chạy dưới PHP-FPM, không phải CLI.
- URL `/san-pham/42` không ứng với file nào, nên `try_files` chuyển nó về `/index.php`, còn
  `REQUEST_URI` vẫn giữ URL gốc. Đây là mô hình *front controller* mà Laravel dùng: mọi request đi
  qua một file `public/index.php`, router của framework đọc `REQUEST_URI` để biết gọi controller nào.
- Gọi `curl` vài lần, `PID của worker` có thể đổi qua lại giữa vài giá trị: mỗi request được một
  worker đang rảnh nhận, không cố định worker nào.

Xem các process trong container PHP:

```bash
docker compose top php
```

Bạn sẽ thấy một dòng `php-fpm: master process (/usr/local/etc/php-fpm.conf)` và vài dòng
`php-fpm: pool www`: đó là master và các worker, chủ đề của mục 2. Dọn dẹp khi xong:
`docker compose down`.

⚠️ Đây là cấu hình để học. Image `php:8.5-fpm` chưa có `php.ini` (bạn phải tự chọn bản production,
mục 12.2) và để FPM nghe TCP cổng 9000 trên mọi địa chỉ trong mạng nội bộ của Docker; không publish
cổng 9000 ra máy host (mục 2.4 giải thích vì sao).

## 2. PHP-FPM: master, pool, worker

### 2.1 FPM là gì, cấu hình nằm ở đâu

Theo php.net, *FPM* (FastCGI Process Manager) là bản cài đặt FastCGI chính của PHP, với các tính năng
"chủ yếu hữu ích cho site tải cao": quản lý process có dừng/khởi động êm, nhiều *pool* với user và cấu
hình riêng, slow log, `fastcgi_finish_request()`, status page... Bạn đã thấy vòng lặp của một worker
FPM ở [chương 02, mục 5.3](02-php-chay-nhu-the-nao.md#53-php-fpm-một-process-nhiều-request); chương
này nhìn từ phía người vận hành.

FPM dùng cú pháp giống `php.ini` và tách cấu hình thành hai tầng:

- `php-fpm.conf`: phần `[global]`, các thiết lập của cả chương trình (file log, pid, cách xử lý tín
  hiệu...). Cuối file thường có dòng `include=.../php-fpm.d/*.conf` để nạp các file pool.
- File pool, mỗi file một hoặc nhiều đoạn `[ten_pool]`: user chạy, địa chỉ nghe, số worker, timeout...
  File mặc định tên `www.conf`, định nghĩa pool `www`.

Ngoài ra, mỗi worker vẫn đọc `php.ini` như mọi SAPI khác (nơi đặt `memory_limit`, `opcache.*`...).

| Môi trường | File FPM | `php.ini` cho FPM | Tên chương trình / service |
|---|---|---|---|
| Debian/Ubuntu (gói `php8.4-fpm`) | `/etc/php/8.4/fpm/php-fpm.conf`, `/etc/php/8.4/fpm/pool.d/*.conf` | `/etc/php/8.4/fpm/php.ini` | `php-fpm8.4`, service `php8.4-fpm` |
| Image Docker chính thức `php:*-fpm` | `/usr/local/etc/php-fpm.conf`, `/usr/local/etc/php-fpm.d/*.conf` | `/usr/local/etc/php/php.ini` (phải tự tạo, mục 12) | `php-fpm` |

⚠️ Trên Debian/Ubuntu, CLI và FPM đọc **hai file `php.ini` khác nhau** (`/etc/php/8.4/cli/php.ini` và
`/etc/php/8.4/fpm/php.ini`). Lệnh `php -i` hay `php -r 'echo ini_get("memory_limit");'` trên terminal
cho bạn cấu hình của CLI, không phải của web. Muốn biết FPM thật sự đang dùng giá trị nào, gọi
`phpinfo()` hoặc `ini_get()` từ một trang chạy dưới FPM (đặt sau xác thực, đừng để public).

Kiểm tra cú pháp cấu hình trước khi áp dụng (man page `php-fpm.8`: `-t` kiểm tra rồi thoát, `-tt` in
thêm toàn bộ cấu hình đã nạp):

```bash
# Trên server Debian/Ubuntu
sudo php-fpm8.4 -t
# Trong container image chính thức
php-fpm -t
```

Output minh hoạ khi cấu hình đúng:

```
[03-Oct-2026 10:15:02] NOTICE: configuration file /etc/php/8.4/fpm/php-fpm.conf test is successful
```

Vài quy ước cú pháp hay gặp trong file FPM:

- Giá trị thời gian nhận đơn vị `s`, `m`, `h`, `d` (ví dụ `30s`, `5m`); không ghi đơn vị là giây.
- Biến `$pool` được thay bằng tên pool, tiện cho đường dẫn log: `slowlog = /var/log/php-fpm/$pool.slow.log`.
- Dùng được biến môi trường: `listen = /run/php/${POOL_NAME}.sock`; từ PHP 8.3 có thêm giá trị mặc định
  dạng `${USER_NAME:-www-data}` (ví dụ trên trang cấu hình FPM của php.net).

### 2.2 Master và worker

Trên một server đang chạy, lệnh `ps` cho thấy cấu trúc này (output minh hoạ):

```bash
ps -eo user,pid,ppid,rss,cmd | grep php-fpm
```

```
USER       PID  PPID   RSS CMD
root       812     1 30124 php-fpm: master process (/etc/php/8.4/fpm/php-fpm.conf)
www-data   901   812 61240 php-fpm: pool www
www-data   902   812 58876 php-fpm: pool www
www-data   903   812 63012 php-fpm: pool www
```

- *Master process* (một process duy nhất, thường chạy bằng `root`): đọc cấu hình, mở socket để nghe,
  khởi động các extension (giai đoạn MINIT, trong đó OPcache tạo vùng shared memory), rồi `fork()` ra
  các worker. Sau đó master chỉ quản lý: theo dõi worker sống hay chết, tạo thêm hoặc giết bớt theo
  chế độ `pm` (mục 3), giết worker chạy quá giờ (mục 5), xử lý tín hiệu reload/stop (mục 6). Master
  **không bao giờ chạy code PHP của bạn**.
- *Worker process*: con của master (cột `PPID` là 812). Ngay sau khi fork, nếu master chạy bằng root,
  worker đổi sang `user`/`group` của pool (ở đây `www-data`), nên code PHP không chạy bằng quyền root.
  Mỗi worker lặp: chờ một kết nối, chạy request, dọn sạch, chờ tiếp.

Tên `php-fpm: master process (...)` và `php-fpm: pool www` là do FPM tự đặt lại tên process; nhờ đó
bạn lọc được worker của từng pool bằng `pgrep -f 'php-fpm: pool www'`.

⚠️ Nếu FPM không chạy bằng root (ví dụ container chạy với `--user 1000`), các directive `user`,
`group`, `chroot` của pool bị bỏ qua (FPM ghi `NOTICE` vào log); mọi worker chạy bằng chính user đó.

### 2.3 Pool

*Pool* là một nhóm worker dùng chung một bộ cấu hình. Một master có thể quản lý nhiều pool, mỗi pool
có: socket nghe riêng, user chạy riêng, chế độ `pm` và số worker riêng, timeout riêng, giá trị
`php.ini` riêng.

```ini
; /etc/php/8.4/fpm/pool.d/www.conf
[www]
user = www-data
group = www-data
listen = /run/php/php8.4-fpm.sock
listen.owner = www-data
listen.group = www-data
listen.mode = 0660

pm = dynamic
pm.max_children = 20
pm.start_servers = 4
pm.min_spare_servers = 2
pm.max_spare_servers = 6
```

Vì sao lại muốn nhiều pool? Ví dụ một app có API cho mobile (request nhanh, nhiều) và trang quản trị
có báo cáo xuất Excel (chậm, nặng RAM). Nếu dùng chung một pool, vài admin bấm xuất báo cáo cùng lúc có
thể giữ hết worker, và API của cả nghìn người dùng phải xếp hàng. Tách pool thì mỗi loại traffic có
"làn" riêng:

```ini
; /etc/php/8.4/fpm/pool.d/api.conf
[api]
user = www-data
group = www-data
listen = /run/php/api.sock
listen.owner = www-data
listen.group = www-data
pm = static
pm.max_children = 30
request_terminate_timeout = 30s

; /etc/php/8.4/fpm/pool.d/admin.conf
[admin]
user = www-data
group = www-data
listen = /run/php/admin.sock
listen.owner = www-data
listen.group = www-data
pm = ondemand
pm.max_children = 4
request_terminate_timeout = 300s
php_admin_value[memory_limit] = 512M
```

Rồi cho Nginx gửi `/admin` sang socket của pool `admin`, phần còn lại sang `api` (cú pháp `location` ở
mục 7). Admin có chậm tới đâu cũng chỉ chiếm tối đa 4 worker của chính nó.

⚠️ php.net ghi rõ: pool **không phải là cơ chế bảo mật**, vì chúng không tách biệt hoàn toàn; ví dụ
mọi pool của cùng một master dùng chung một OPcache. Muốn cô lập thật hai khách hàng (hai site của hai
chủ khác nhau) thì chạy hai master FPM riêng, tốt hơn nữa là hai container riêng.

### 2.4 `listen`: unix socket hay TCP

`listen` là địa chỉ pool nhận kết nối FastCGI. Các dạng hợp lệ (theo `www.conf`):

| Giá trị | Nghĩa |
|---|---|
| `127.0.0.1:9000` | TCP, chỉ trên địa chỉ IPv4 đó (đây là giá trị trong file `www.conf` mẫu) |
| `[::1]:9000` | TCP, trên địa chỉ IPv6 đó |
| `9000` | TCP, trên **mọi** địa chỉ của máy |
| `/run/php/php8.4-fpm.sock` | *Unix domain socket*: một "file đặc biệt" trên đĩa, chỉ process cùng máy kết nối được |

So sánh:

| | Unix socket | TCP |
|---|---|---|
| Nginx và FPM ở hai máy / hai container không chung filesystem | Không dùng được | Dùng được |
| Ai được kết nối | Quyền trên file socket: `listen.owner`, `listen.group`, `listen.mode` (mặc định `0660`) | Địa chỉ IP: `listen.allowed_clients` (mặc định không đặt, tức nhận mọi IP) |
| Chi phí | Không đi qua TCP/IP stack, nhẹ hơn | Có thêm chi phí TCP |
| Status page đo được `listen queue` | Không (mục 5.4) | Có |

⚠️ Lỗi kinh điển với unix socket: Nginx chạy bằng user `nginx` hoặc `www-data`, còn file socket thuộc
user khác với mode `0660`, Nginx không có quyền ghi vào socket. Kết quả là 502, và error log của Nginx có
`connect() to unix:/run/php/php8.4-fpm.sock failed (13: Permission denied)`. Sửa bằng `listen.owner`,
`listen.group` khớp với user của Nginx.

⚠️ **Đừng bao giờ để cổng FastCGI lộ ra mạng không tin cậy.** Trang FPM của php.net cảnh báo: client
nào mở được kết nối FastCGI thì điều khiển được cấu hình dùng cho request đó, kể cả
`auto_prepend_file`, nên **chạy được code tuỳ ý**. Cơ chế là FPM nhận hai tham số FastCGI đặc biệt
`PHP_VALUE` và `PHP_ADMIN_VALUE` để đặt giá trị ini cho từng request (php.net có ví dụ đặt từ Nginx:
`fastcgi_param PHP_VALUE "pcre.backtrack_limit=424242";`). Kẻ tấn công nói thẳng FastCGI với cổng 9000
có thể gửi `PHP_VALUE` trỏ `auto_prepend_file` tới một file chứa code của hắn. Quy tắc:

- Nginx và FPM cùng máy: dùng unix socket.
- Bắt buộc dùng TCP: nghe trên địa chỉ nội bộ (`127.0.0.1:9000`, IP mạng riêng), đặt
  `listen.allowed_clients`, chặn bằng firewall.
- Docker: không publish cổng 9000 ra host (`ports: - "9000:9000"` là sai); container cùng network đã
  nói chuyện được với nhau.

`listen.backlog` là độ dài tối đa của hàng đợi kết nối chờ ở socket (mục 2.5). Trên Linux, từ PHP 8.2
giá trị mặc định là `-1` (NEWS của PHP 8.2.0: "Changed default for listen.backlog on Linux to -1"),
nghĩa là để kernel dùng mức tối đa nó cho phép, chính là `net.core.somaxconn`. Trước 8.2 mặc định là
`511`. Trang cấu hình trên php.net (lúc viết chương này) vẫn ghi 511 cho Linux; mã nguồn FPM mới là
căn cứ.

### 2.5 Mỗi worker một request, phần còn lại xếp hàng

Đây là sự thật quan trọng nhất về FPM: **một worker chỉ xử lý một request tại một thời điểm**. php.net
mô tả `pm.max_children` là giới hạn "số request được phục vụ đồng thời". Vậy chuyện gì xảy ra với request
tới khi mọi worker đều bận?

FPM không tự giữ hàng đợi. Socket mà master mở là một *listening socket* của kernel; kết nối mới tới
được kernel xếp vào *listen queue* (hàng đợi kết nối) của socket đó. Worker nào rảnh thì gọi `accept()`
để lấy kết nối đầu hàng. Hàng đợi dài tối đa `listen.backlog` (bị chặn trên bởi `net.core.somaxconn`).

Ví dụ pool có 2 worker, ba request tới gần như cùng lúc, mỗi request mất 1 giây:

| Thời điểm | Worker 1 | Worker 2 | Listen queue | Ghi chú |
|---|---|---|---|---|
| 0,00 s | Nhận request A | Nhận request B | trống | |
| 0,01 s | Chạy A | Chạy B | C | C đã kết nối xong nhưng chưa ai `accept()` |
| 1,00 s | Xong A, `accept()` lấy C | Xong B, chờ | trống | C bắt đầu chạy sau 1 giây xếp hàng |
| 2,00 s | Xong C | Chờ | trống | Người gửi C thấy 2 giây thay vì 1 |

Ba hệ quả:

1. Thời gian người dùng thấy = thời gian **chờ trong hàng** + thời gian chạy. Khi pool bão hoà, latency
   tăng vọt dù code không chậm đi.
2. Hàng đợi đầy thì kết nối mới không vào được nữa. Với unix socket, kernel từ chối ngay: Nginx nhận
   lỗi `EAGAIN` và trả 502; error log của Nginx có
   `connect() to unix:... failed (11: Resource temporarily unavailable)`. Với TCP, Linux mặc định
   không từ chối mà bỏ qua gói kết nối để phía client gửi lại, nên Nginx chờ và có thể hết
   `fastcgi_connect_timeout` (504).
3. Nginx cũng có giới hạn chờ riêng (`fastcgi_connect_timeout`, `fastcgi_read_timeout`, mục 7.6). Request
   nằm hàng quá lâu có thể bị Nginx bỏ cuộc trước khi tới lượt.

### 2.6 Cấu hình riêng cho pool và biến môi trường

Mỗi pool có thể ghi đè giá trị `php.ini` cho riêng worker của nó (ví dụ trên trang cấu hình FPM):

```ini
php_value[max_execution_time] = 60      ; code đổi lại được bằng ini_set()
php_flag[display_errors] = off
php_admin_value[memory_limit] = 256M    ; code KHÔNG đổi được bằng ini_set()
php_admin_flag[log_errors] = on
php_admin_value[error_log] = /var/log/php-fpm/$pool.error.log
```

- `php_value` / `php_flag`: đặt giá trị khởi đầu, code PHP vẫn `ini_set()` đè được.
- `php_admin_value` / `php_admin_flag`: code không đè được bằng `ini_set()`. Dùng cho thứ bạn muốn ép
  cứng (giới hạn bộ nhớ, đường dẫn log).
- Riêng `disable_functions` đặt ở pool không thay mà **nối thêm** vào giá trị trong `php.ini`.

*Biến môi trường.* Mặc định `clear_env = yes`: FPM xoá sạch biến môi trường trước khi khởi động worker,
chỉ giữ những biến khai báo bằng `env[...]` trong pool. Lý do: không để biến môi trường tuỳ ý của
server lọt vào code PHP.

```ini
env[APP_ENV] = production
env[DB_HOST] = $DB_HOST     ; lấy giá trị từ môi trường của master lúc khởi động
```

⚠️ Hệ quả hay gặp: bạn `export DB_HOST=...` trong systemd unit hoặc truyền `-e DB_HOST=...` cho
container, nhưng `getenv('DB_HOST')` trong code trả `false`. Nguyên nhân là `clear_env = yes`. Hai cách
sửa: liệt kê từng biến bằng `env[...]`, hoặc đặt `clear_env = no`. Image Docker chính thức đặt sẵn
`clear_env = no` (trong file `docker.conf`), nên trong container chuẩn bạn ít gặp lỗi này; trên VM cài
bằng gói thì hay gặp.

## 3. Process manager: `static`, `dynamic`, `ondemand`

*Process manager* (directive `pm`, bắt buộc phải có trong mỗi pool) là chiến lược master dùng để quyết
định giữ bao nhiêu worker. Cả ba chế độ đều bị chặn trên bởi `pm.max_children`.

### 3.1 `static`: số worker cố định

```ini
pm = static
pm.max_children = 30
```

Master fork đủ 30 worker ngay khi khởi động và giữ nguyên con số đó. Worker nào chết (bị kill, hết
`pm.max_requests`) thì master fork worker mới thay.

- Ưu: không bao giờ phải chờ fork khi traffic tăng đột ngột; bộ nhớ dùng gần như cố định, dễ dự đoán.
- Nhược: lúc vắng khách vẫn giữ đủ 30 process trong RAM.
- Hợp với: server hoặc container chỉ chạy một app, nơi RAM đã dành riêng cho PHP.

### 3.2 `dynamic`: co giãn theo số worker rảnh

```ini
pm = dynamic
pm.max_children = 20
pm.start_servers = 4
pm.min_spare_servers = 2
pm.max_spare_servers = 6
pm.max_spawn_rate = 32     ; có từ PHP 8.1, mặc định 32
```

`dynamic` không nhìn số request, nó nhìn số worker **rảnh** (*spare*, *idle*): luôn cố giữ số worker
rảnh trong khoảng `min_spare_servers` tới `max_spare_servers`, để request mới tới có sẵn worker nhận.

Thuật toán, đọc từ hàm `fpm_pctl_perform_idle_server_maintenance()` trong
`sapi/fpm/fpm/fpm_process_ctl.c`. Master chạy vòng kiểm tra này **mỗi giây một lần** cho mỗi pool:

1. Đếm worker rảnh (`idle`) và đang bận (`active`).
2. Nếu `idle > max_spare_servers`: gửi `SIGQUIT` cho **một** worker rảnh (worker được khởi động sớm
   nhất trong số đang rảnh), rồi dừng, chờ giây sau. Vì mỗi giây chỉ bớt một, sau đợt cao điểm số worker
   giảm từ từ.
3. Nếu `idle < min_spare_servers`:
   - Đã đủ `max_children`: không fork được nữa, ghi cảnh báo
     `[pool www] server reached pm.max_children setting (20), consider raising it`
     và tăng bộ đếm `max children reached` trên status page.
   - Chưa đủ: fork thêm `min(tốc độ hiện tại, min_spare_servers - idle)` worker (không vượt
     `max_children`). "Tốc độ hiện tại" bắt đầu từ 1 và **gấp đôi** sau mỗi giây liên tiếp còn thiếu
     (1, 2, 4, 8...), tối đa `pm.max_spawn_rate`. Khi tốc độ chạm từ 8 trở lên, log có dòng
     `seems busy (you may need to increase pm.start_servers, or pm.min/max_spare_servers)`.
4. Mỗi khi không còn thiếu, tốc độ quay về 1.

`pm.start_servers` là số worker tạo lúc khởi động; bỏ trống thì FPM tự đặt `(min_spare + max_spare) / 2`.
FPM từ chối khởi động nếu cấu hình mâu thuẫn, ví dụ `start_servers` nhỏ hơn `min_spare_servers` hoặc
lớn hơn `max_spare_servers`, hay `min_spare`/`max_spare` lớn hơn `max_children`.

Chi tiết ở bước 3 có một hệ quả ít người để ý: số worker fork mỗi giây bị chặn bởi
`min_spare_servers - idle`. Khi traffic tăng vọt, worker mới vừa fork xong đã bị request trong hàng
đợi lấy mất, `idle` vẫn là 0, nên mỗi giây chỉ fork thêm được tối đa `min_spare_servers` worker, dù
tốc độ đã gấp đôi lên bao nhiêu. Minh hoạ theo thuật toán trên, với cấu hình ở đầu mục và 15 request
dài chạy đồng thời từ giây 0:

| Giây | Worker trước khi kiểm tra | Rảnh | Fork thêm | Ghi chú |
|---|---|---|---|---|
| 0 | 4 | 0 | | 4 request đang chạy, 11 request chờ trong listen queue |
| 1 | 4 | 0 | min(1, 2 - 0) = 1 | tốc độ lên 2 |
| 2 | 5 | 0 | min(2, 2) = 2 | tốc độ lên 4 |
| 3 | 7 | 0 | min(4, 2) = 2 | tốc độ lên 8 |
| 4 | 9 | 0 | 2 | log "seems busy" |
| 5 | 11 | 0 | 2 | |
| 6 | 13 | 0 | 2 | Sau lần fork này, 15 request đều có worker |
| 7 | 15 | 0 | 2 | Cả 15 worker đều bận, vẫn thiếu worker rảnh |
| 8 | 17 | 2 | 0 | Đủ 2 worker rảnh, dừng fork |

Request cuối cùng phải xếp hàng khoảng 6 giây chỉ để chờ có worker. Muốn hấp thụ đột biến nhanh hơn:
tăng `min_spare_servers` (giữ sẵn nhiều worker rảnh hơn), tăng `start_servers`, hoặc chuyển sang
`static`.

### 3.3 `ondemand`: chỉ fork khi có request

```ini
pm = ondemand
pm.max_children = 10
pm.process_idle_timeout = 10s   ; mặc định 10s
```

Lúc khởi động không có worker nào. Master theo dõi socket của pool; có kết nối mới mà không có worker
rảnh thì fork một worker (nếu chưa đủ `max_children`; đã đủ thì log
`server reached max_children setting (10), consider raising it`). Mỗi giây, master xét một worker
đang rảnh (worker được khởi động sớm nhất trong số đang rảnh): nếu nó đã không làm gì quá
`process_idle_timeout` thì bị giết.

- Ưu: gần như không tốn RAM khi không có traffic.
- Nhược: request đầu tiên sau lúc vắng phải chờ fork; traffic dao động thì fork/kill liên tục.
- Chỉ dùng được khi `events.mechanism` là `epoll` (Linux) hoặc `kqueue` (BSD); trên Linux đây là mặc
  định tự chọn.
- Hợp với: nhiều pool ít traffic trên một máy (trang quản trị nội bộ, shared hosting).

### 3.4 Chọn chế độ nào

| | `static` | `dynamic` | `ondemand` |
|---|---|---|---|
| Worker lúc khởi động | `max_children` | `start_servers` | 0 |
| Lúc vắng | Giữ nguyên | Giảm dần (một worker mỗi giây) về khoảng `max_spare` | Giảm về 0 sau `process_idle_timeout` |
| Lúc đột biến | Có sẵn, không chờ | Fork dần, mỗi giây tối đa `min_spare - idle` | Fork theo từng kết nối |
| Bộ nhớ | Cố định, dễ dự đoán | Dao động | Thấp nhất khi rảnh |
| `max children reached` trên status page | Luôn 0 (không có ý nghĩa) | Có | Có |
| Hợp với | Server/container dành riêng | VM chạy nhiều dịch vụ, mặc định | Nhiều pool ít traffic |

Mặc định trong file `www.conf` mẫu của PHP là `pm = dynamic` với `pm.max_children = 5`,
`start_servers = 2`, `min_spare_servers = 1`, `max_spare_servers = 3`. Chính file đó ghi chú các giá trị
này dành cho "server không nhiều tài nguyên". ⚠️ Năm worker nghĩa là chỉ năm request PHP chạy cùng lúc;
gần như mọi server production phải chỉnh lại (mục 4).

### 3.5 `pm.max_requests`: thay worker định kỳ

```ini
pm.max_requests = 1000
```

Worker tự thoát sau khi phục vụ đủ 1000 request, master fork worker mới thay. Mặc định là `0` (không
bao giờ thay). ⚠️ File `www.conf` mẫu có dòng `;pm.max_requests = 500` nhưng bị comment, đừng nhầm 500 là
mặc định.

Vì sao cần, khi mô hình share-nothing đã dọn sạch mọi thứ sau mỗi request
([chương 02, mục 7](02-php-chay-nhu-the-nao.md#7-share-nothing-mỗi-request-bắt-đầu-từ-trang-trắng))?
Vì share-nothing chỉ dọn bộ nhớ mà Zend Engine cấp cho request. Thư viện C bên dưới extension
(ImageMagick, driver, ...) có thể rò rỉ bộ nhớ của riêng nó, cộng dồn theo từng request mà PHP không
dọn được. php.net nói đúng mục đích này: "hữu ích để tránh rò rỉ bộ nhớ trong thư viện bên thứ ba".
Dấu hiệu cần bật: RSS của worker tăng đều theo thời gian chạy (đo ở mục 4.3).

- Cái giá: mỗi lần thay là một lần fork, và worker mới phải "làm nóng" lại các cache riêng của process
  (ví dụ realpath cache). Nhỏ so với rủi ro hết RAM.
- Đặt quá thấp (vài chục) thì fork liên tục, phí CPU.
- ⚠️ Với `pm = static`, mọi worker khởi động cùng lúc nên cũng chạm mốc N gần cùng lúc. Thường không
  sao vì thay rất nhanh, nhưng nếu thấy latency nhảy lên theo chu kỳ đều đặn, hãy nghĩ tới chuyện này.

## 4. Tính `pm.max_children` theo RAM

### 4.1 Nguyên tắc

`pm.max_children` là số worker **tối đa có thể chạy cùng lúc**. Câu hỏi đúng không phải "bao nhiêu thì
nhanh" mà là: khi cả `max_children` worker cùng bận ở mức dùng RAM cao, máy có còn đủ RAM không?

- Đặt quá cao: lúc cao điểm mọi worker cùng phình, máy hết RAM, bắt đầu *swap* (đẩy trang bộ nhớ xuống
  đĩa, chậm hơn RAM hàng trăm lần), rồi *OOM killer* của Linux giết process để cứu máy, có khi giết
  nhầm MySQL hay Redis chạy cùng máy. Máy swap thì chậm toàn bộ, tệ hơn nhiều so với vài request phải
  xếp hàng.
- Đặt quá thấp: request xếp hàng ở listen queue, latency tăng, rồi 502/504 khi hàng đợi đầy (mục 2.5), trong
  khi RAM vẫn còn thừa.

Công thức khởi đầu:

```
pm.max_children ≈ (RAM dành cho các worker) / (RAM mỗi worker thật sự dùng lúc tải cao)

RAM dành cho các worker = tổng RAM
                        - hệ điều hành và các agent
                        - Nginx, Redis, MySQL... nếu chạy chung máy
                        - shared memory của OPcache (đếm MỘT lần)
                        - phần dự phòng
```

⚠️ **Đừng chia cho `memory_limit`.** `memory_limit` (mặc định `128M`) là **trần** mà một request được
phép dùng, không phải mức dùng thật. Worker Laravel điển hình dùng ít hơn nhiều. Chia cho 128 MB sẽ ra
con số thấp hơn cần thiết vài lần. Ngược lại, cũng nhớ rằng về lý thuyết nhiều request có thể cùng
chạm trần một lúc, nên luôn chừa dự phòng.

### 4.2 RSS, PSS, USS: đo "RAM của một process" thế nào cho đúng

Đo bộ nhớ của worker PHP-FPM khó hơn tưởng, vì các worker **dùng chung** rất nhiều trang bộ nhớ:

- Vùng shared memory của OPcache (mặc định 128 MB, `opcache.memory_consumption`): mọi worker cùng đọc.
- Mã máy của binary PHP và các thư viện `.so`: nạp một lần, mọi process dùng chung.
- Các trang được kế thừa từ master lúc `fork()`. Linux dùng *copy-on-write*: sau khi fork, cha và con
  dùng chung trang nhớ; chỉ khi một bên **ghi** vào trang nào thì trang đó mới được sao ra thành bản
  riêng.

Ba thước đo:

| Thước đo | Định nghĩa | Cộng cho mọi worker thì ra |
|---|---|---|
| *RSS* (Resident Set Size) | Mọi trang RAM process đang dùng, **kể cả trang dùng chung** | Lớn hơn RAM thật, vì trang dùng chung bị đếm lặp ở từng worker |
| *PSS* (Proportional Set Size) | Trang riêng tính đủ; trang dùng chung bởi N process thì mỗi process tính 1/N | Xấp xỉ RAM thật cả nhóm đang dùng |
| *USS* (Unique Set Size) | Chỉ các trang **riêng** của process | Phần RAM tăng thêm khi thêm một worker |

Ví dụ minh hoạ: 50 worker, mỗi worker RSS 90 MB, trong đó 60 MB là trang dùng chung (OPcache, mã máy,
trang chưa bị ghi sau fork) và 30 MB là riêng.

```
Cộng RSS:              50 × 90 MB             = 4500 MB   (sai, đếm 60 MB dùng chung 50 lần)
RAM thật xấp xỉ:       60 MB + 50 × 30 MB     = 1560 MB
Cộng PSS:              50 × (30 + 60/50) MB   = 1560 MB   (khớp)
Thêm worker thứ 51:    tốn thêm USS           ≈   30 MB
```

Chia RAM theo RSS cho ra `max_children` thấp hơn cần thiết gần 3 lần trong ví dụ này. Đó là cách tính
**an toàn** (thừa RAM), nhưng lãng phí.

### 4.3 Đo trên server thật

`ps` cho RSS (cột `RSS`, đơn vị KB):

```bash
# RSS trung bình các worker của pool www (MB)
ps --no-headers -o rss -p "$(pgrep -d, -f 'php-fpm: pool www')" \
  | awk '{s+=$1; n++} END {printf "RSS trung bình %.1f MB, %d worker\n", s/n/1024, n}'
```

PSS và USS đọc từ `/proc/<pid>/smaps_rollup` (có từ Linux 4.14). Chạy bằng root, vì worker thuộc user
khác:

```bash
for pid in $(pgrep -f 'php-fpm: pool www'); do
  awk -v pid="$pid" '
    /^Rss:/           { rss = $2 }
    /^Pss:/           { pss = $2 }
    /^Private_Clean:/ { uss += $2 }
    /^Private_Dirty:/ { uss += $2 }
    END { printf "%7d  RSS %4d MB  PSS %4d MB  USS %4d MB\n", pid, rss/1024, pss/1024, uss/1024 }
  ' "/proc/$pid/smaps_rollup"
done
```

Output minh hoạ:

```
    901  RSS   92 MB  PSS   41 MB  USS   33 MB
    902  RSS   88 MB  PSS   38 MB  USS   30 MB
    903  RSS  141 MB  PSS   90 MB  USS   82 MB
```

Công cụ `smem` (nếu cài) in sẵn ba cột USS, PSS, RSS.

Đo cho đúng:

- Đo **lúc tải thật** (giờ cao điểm, hoặc chạy load test giống production), sau khi worker đã phục vụ
  nhiều request. Worker vừa fork có USS rất nhỏ vì chưa ghi vào trang nào; đo lúc đó sẽ ra con số đẹp
  một cách giả tạo.
- Nhìn cả phân bố, không chỉ trung bình: worker 903 ở trên (82 MB riêng) có thể vừa chạy một request xuất
  báo cáo. Tìm endpoint nặng bằng access log của FPM với `%M` (đỉnh bộ nhớ của request, mục 5.5) hoặc
  trường `last request memory` trên status page (mục 5.4).
- Đo lại sau mỗi đợt thay đổi lớn (nâng PHP, thêm package, đổi cách xử lý ảnh).

### 4.4 Ví dụ tính

Server 8 GB chạy Nginx, PHP-FPM, Redis; MySQL ở máy khác.

```
Tổng RAM                                         8192 MB
- Hệ điều hành, sshd, agent giám sát             -800 MB
- Nginx                                          -100 MB
- Redis (maxmemory 1 GB cộng overhead)           -1300 MB
- OPcache shared memory (memory_consumption=256)  -256 MB
- Dự phòng                                       -700 MB
= RAM dành cho các worker                        5036 MB

Đo được: USS trung bình lúc cao điểm  45 MB
         request xuất báo cáo nặng nhất  150 MB, ước tính tối đa 5 request như vậy cùng lúc

Chừa cho request nặng:   5 × 150 MB  =  750 MB
Còn lại:                 5036 - 750  = 4286 MB
4286 / 45 ≈ 95  ->  pm.max_children = 95
```

Không có gì đảm bảo chỉ 5 request nặng chạy cùng lúc. Nếu báo cáo nặng hay bị bấm đồng loạt, cách tốt
hơn là tách endpoint đó sang pool riêng với `max_children` nhỏ và `memory_limit` riêng (mục 2.3), để
con số của pool chính khỏi phải đoán.

⚠️ Nhiều pool trên một máy: **tổng** `max_children` của mọi pool mới là con số phải khớp với RAM.

### 4.5 Kiểm tra chéo: CPU, nhu cầu thật, connection DB

RAM chỉ là một trần. Trước khi chốt, kiểm thêm ba trần khác.

*CPU.* Thêm worker chỉ có ích khi worker phần lớn thời gian **chờ** I/O (MySQL, Redis, API ngoài). Nếu
request chủ yếu tính toán (resize ảnh, sinh PDF bằng PHP thuần), worker nhiều hơn số core CPU chỉ làm
chúng giành CPU của nhau, request nào cũng chậm đi.

*Nhu cầu thật*, theo *định luật Little*: số request đang xử lý trung bình = số request mỗi giây × thời
gian xử lý trung bình. Ví dụ 200 request/giây, mỗi request 0,25 giây thì trung bình 200 × 0,25 = 50
worker bận. `max_children = 95` cho bạn gần gấp đôi chỗ trống để đỡ đột biến; nếu con số này chỉ ngang
mức trung bình thì mỗi đợt tăng nhẹ là xếp hàng.

*Connection tới database.* Mỗi worker đang chạy request có thể giữ một connection MySQL. 95 worker × 4
server web = 380 connection có thể mở cùng lúc, chưa kể queue worker, cron. `max_connections` mặc định
của MySQL 8.4 là 151. Vượt trần thì request mới nhận lỗi "Too many connections". Các lựa chọn: giảm
worker, tăng `max_connections` của MySQL (mỗi connection cũng tốn RAM phía MySQL), hoặc đặt một proxy gom
connection (như ProxySQL) ở giữa. Connection và persistent connection nhìn từ phía PHP ở
[chương 16](16-php-va-database.md).

⚠️ Tăng `max_children` khi DB đang là nút thắt là đổ thêm dầu vào lửa: thêm worker nghĩa là thêm query
đồng thời dồn vào một DB vốn đã chậm. Mục 7.9 đi qua cách chẩn đoán trước khi tăng.

## 5. Timeout, slow log, status page và log

### 5.1 Bốn giới hạn, bốn chiếc đồng hồ khác nhau

Một request PHP chạy dưới Nginx và FPM bị canh bởi nhiều giới hạn, mỗi cái ở một tầng và đo một thứ
khác nhau:

| Giới hạn | Đặt ở | Mặc định | Đo cái gì | Vượt thì |
|---|---|---|---|---|
| `memory_limit` | `php.ini` hoặc pool | `128M` | Bộ nhớ mà Zend Engine cấp cho request | Fatal error "Allowed memory size of ... bytes exhausted", request chết, worker vẫn sống |
| `max_execution_time` | `php.ini` | `30` (CLI mặc định `0`) | Thời gian thực thi của script (xem ⚠️ dưới) | Fatal error "Maximum execution time of 30 seconds exceeded" |
| `request_terminate_timeout` | pool FPM | `0` (tắt) | Thời gian **thực** tính từ lúc worker nhận request | Master giết worker bằng `SIGTERM`; Nginx trả 502 |
| `fastcgi_read_timeout` | Nginx | `60s` | Khoảng thời gian giữa hai lần đọc được dữ liệu từ FPM | Nginx trả 504 cho client; worker **vẫn chạy tiếp** |

⚠️ `max_execution_time` không phải thời gian thực. Theo php.net (trang `set_time_limit`), nó chỉ tính
thời gian thực thi của chính script; thời gian nằm trong system call, thao tác stream, query database...
không được tính, trừ trên Windows. Trang cấu hình nói rõ hơn: mặc định PHP dùng `setitimer(ITIMER_PROF)`,
tức đo **thời gian CPU**. Ngoại lệ: bản build có `--enable-zend-max-execution-timers` (mặc định cho bản
ZTS, tức bản thread-safe, từ PHP 8.3) đo thời gian thực, nên thời gian ngủ và chờ I/O cũng được tính.
PHP-FPM thông thường dùng bản NTS (không thread-safe), nên trên Linux:

```php
<?php
declare(strict_types=1);

set_time_limit(2);

sleep(5);                          // không bị cắt: process nằm chờ trong system call, không tốn CPU
echo "vẫn sống sau 5 giây\n";

$end = microtime(true) + 3;
while (microtime(true) < $end) {   // vòng lặp đốt CPU
}
// Fatal error: Maximum execution time of 2 seconds exceeded
```

(Hành vi trên là của bản NTS trên Linux theo tài liệu php.net. Môi trường khác, ví dụ bản ZTS hay
WebAssembly, có thể cắt ngay ở `sleep(5)` vì đo thời gian thực.)

Hệ quả: một request đứng chờ API ngoài 10 phút có thể không bao giờ chạm `max_execution_time = 30`.
Chặn theo thời gian thực phải dùng tầng khác: timeout của chính lời gọi ra ngoài (HTTP client, PDO,
Redis), rồi tới `request_terminate_timeout` (mục 5.2) làm lưới an toàn cuối.

### 5.2 `request_terminate_timeout`: lưới an toàn cuối cùng

```ini
; trong pool
request_terminate_timeout = 60s
```

php.net mô tả: thời gian phục vụ một request mà quá nó thì worker bị giết; nên dùng khi
`max_execution_time` "vì lý do nào đó" không dừng được script (chính là trường hợp chờ I/O ở trên).

Khi xảy ra, log của FPM có hai dòng như sau (output minh hoạ, định dạng lấy theo mã nguồn FPM):

```
WARNING: [pool www] child 4182, script '/var/www/app/public/index.php' (request: "POST /index.php") execution timed out (60.004163 sec), terminating
WARNING: [pool www] child 4182 exited on signal 15 (SIGTERM) after 812.301722 seconds from start
```

Nginx thấy kết nối tới FPM bị đóng giữa chừng nên trả **502** (không phải 504), error log của Nginx
thường có `upstream prematurely closed connection while reading response header from upstream`.

⚠️ Worker bị giết từ bên ngoài nên **không có gì của PHP chạy tiếp**: không khối `finally`, không
exception handler, không `register_shutdown_function()`, không dòng log nào của Laravel. Transaction
MySQL đang dở sẽ được MySQL tự rollback khi connection đóng, nhưng những gì đã xảy ra bên ngoài (đã gọi
API thanh toán, đã ghi file) thì không quay lại được. Vì vậy đây là lưới an toàn, không phải cơ chế
timeout chính; cơ chế chính là timeout của từng lời gọi ra ngoài, nơi code còn bắt được lỗi và xử lý.

Hai chi tiết đọc từ mã nguồn FPM:

- Master không canh từng mili giây. Nó kiểm tra định kỳ với chu kỳ khoảng một phần ba timeout nhỏ nhất
  (và không dưới 130 ms). Với `request_terminate_timeout = 30s`, kiểm tra mỗi khoảng 10 giây, nên worker
  có thể bị giết ở đâu đó giữa giây thứ 30 và 40.
- `request_terminate_timeout_track_finished` (từ PHP 7.3, mặc định `no`): mặc định timeout **không áp
  dụng** sau khi code gọi `fastcgi_finish_request()` hoặc khi đang chạy shutdown function. Bật `yes` để
  áp dụng cả trong những lúc đó.

`fastcgi_finish_request()` (chỉ có trong FPM) gửi xong response cho client rồi để script chạy tiếp:

```php
<?php
declare(strict_types=1);

echo json_encode(['status' => 'ok']);
fastcgi_finish_request();   // client nhận response ngay tại đây

// Phần dưới vẫn chạy trong worker này, client không phải chờ
file_put_contents('/tmp/audit.log', date('c') . " xong\n", FILE_APPEND);
```

⚠️ Client thấy nhanh, nhưng **worker vẫn bận** tới khi script chạy xong. Lạm dụng nó là âm thầm giảm số
worker rảnh. Việc nặng (gửi email, gọi đối tác, sinh PDF) nên đưa vào queue
([chương 29](29-laravel-queue-event-schedule-cache.md)).

### 5.3 Slow log: chụp call stack của request chậm

```ini
; trong pool
request_slowlog_timeout = 5s                    ; 0 là tắt (mặc định)
slowlog = /var/log/php-fpm/$pool.slow.log       ; bắt buộc khi đặt request_slowlog_timeout
request_slowlog_trace_depth = 20                ; mặc định 20 frame
```

Khi một request chạy quá 5 giây, master tạm dừng worker đó bằng `ptrace` (cơ chế debug của Linux cho
phép một process đọc bộ nhớ process khác), đọc call stack PHP đang chạy, ghi vào file, rồi cho worker
chạy tiếp. Worker **không bị giết**. Log chính của FPM có thêm dòng
`[pool www] child 4182, script '...' (request: "...") executing too slow (5.012345 sec), logging`.

Một bản ghi trong file slow log (output minh hoạ, định dạng theo mã nguồn `fpm_php_trace.c`):

```
[03-Oct-2026 10:15:02]  [pool www] pid 4182
script_filename = /var/www/app/public/index.php
[0x00007f3a1c2150a0] curl_exec() /var/www/app/vendor/guzzlehttp/guzzle/src/Handler/CurlHandler.php:44
[0x00007f3a1c214f80] __invoke() /var/www/app/vendor/guzzlehttp/guzzle/src/Handler/Proxy.php:28
...
[0x00007f3a1c213e10] charge() /var/www/app/app/Services/PaymentGateway.php:87
[0x00007f3a1c213c90] store() /var/www/app/app/Http/Controllers/OrderController.php:41
```

Cách đọc:

- Mỗi dòng là một frame: tên hàm, rồi file:dòng nơi hàm đó được gọi. Dòng **đầu** là chỗ worker đang
  đứng lúc bị chụp; đọc xuống là đi ra các hàm gọi nó.
- Slow log chỉ in tên hàm, không in tên class.
- Dò xuống tới dòng đầu tiên thuộc code của bạn (`app/...`) để biết điểm xuất phát: ở đây
  `PaymentGateway::charge()` đang chờ `curl_exec()`, tức chậm vì chờ API ngoài, không phải vì code
  PHP. Nếu dòng đầu là `execute()` (của `PDOStatement`), nút thắt ở database; `session_start()` hay
  `flock()` thường là chờ lock.
- Slow log chỉ là một tấm ảnh chụp tại giây thứ 5. Nó trả lời "đang chờ cái gì", không trả lời "cả
  request tốn thời gian vào đâu"; câu sau cần profiler ([chương 20](20-hieu-nang.md)).

⚠️ Trong container, `ptrace` thường bị chặn vì thiếu capability `SYS_PTRACE` (master chạy root, worker
chạy user khác). Khi đó slow log không có stack nào, còn log chính của FPM có dòng lỗi dạng
`failed to ptrace(ATTACH) child 4182: Operation not permitted (1)`. Docker: `cap_add: [SYS_PTRACE]`;
Kubernetes: `securityContext.capabilities.add: ["SYS_PTRACE"]`. Cân nhắc trước khi cấp, vì capability
này cũng mở thêm quyền cho kẻ đã chiếm được container.

### 5.4 Status page và ping

Bật trong pool:

```ini
pm.status_path = /fpm-status
ping.path = /fpm-ping            ; trả "pong" (đổi được bằng ping.response)
```

Rồi cho Nginx chuyển đúng hai đường dẫn đó vào FPM, chỉ cho IP nội bộ. php.net cảnh báo trang này lộ
URL của request và thông tin tài nguyên:

```nginx
location ~ ^/(fpm-status|fpm-ping)$ {
    allow 127.0.0.1;
    deny all;
    fastcgi_pass unix:/run/php/php8.4-fpm.sock;
    include fastcgi_params;      # có SCRIPT_NAME, FPM so nó với pm.status_path / ping.path
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;   # bắt buộc phải có, xem dưới
}
```

Đọc mã nguồn `fpm_main.c`: request không có `SCRIPT_FILENAME` thì FPM không xét tới đường dẫn status
mà trả luôn `File not found.`. Vì vậy vẫn phải gửi tham số này, dù file `/fpm-status` không hề tồn tại
trên đĩa (trỏ tới file không tồn tại cũng được).

```bash
curl -s 'http://127.0.0.1/fpm-status'
```

Output minh hoạ (pool nghe bằng TCP; cột bên phải là chú thích, không có trong output):

```
pool:                 www
process manager:      dynamic
start time:           03/Oct/2026:08:00:01 +0700
start since:          8100
accepted conn:        190460       tổng số kết nối đã nhận
listen queue:         0            số request ĐANG chờ worker rảnh
max listen queue:     12           đỉnh của listen queue từ lúc start
listen queue len:     4096         kích thước tối đa của hàng đợi
idle processes:       4
active processes:     11
total processes:      15
max active processes: 20           đỉnh số worker bận cùng lúc
max children reached: 3            số đợt muốn fork thêm mà đã chạm pm.max_children
slow requests:        27           số request vượt request_slowlog_timeout
memory peak:          94371840     đỉnh bộ nhớ của một request, tính bằng byte (có từ PHP 8.4)
```

Thêm tham số vào URL để đổi định dạng: `?json`, `?xml`, `?html`, `?openmetrics` (từ PHP 8.1, cho
Prometheus); thêm `full` (`?json&full`) để xem từng worker: `pid`, `state` (Idle, Running...),
`requests` đã phục vụ, `request duration` (micro giây), `request uri`, `last request cpu`,
`last request memory`.

Đọc theo thời gian, không đọc một lần:

| Tín hiệu kéo dài | Nghĩa |
|---|---|
| `listen queue` > 0 | Request đang xếp hàng: mọi worker đều bận |
| `idle processes` về 0, `active` bằng tổng | Pool bão hoà |
| `max children reached` tăng | Master đã nhiều lần muốn fork thêm mà không được |
| `slow requests` tăng vọt | Có thứ gì đó phía sau (DB, API) đang chậm; mở slow log |

Mấy cái bẫy khi đọc status page:

- ⚠️ `max children reached` chỉ hoạt động với `pm = dynamic` và `ondemand` (ghi chú trong `www.conf`).
  Với `static` nó luôn là 0 dù pool đã bão hoà.
- ⚠️ Trên Linux, FPM đọc độ dài hàng đợi qua `TCP_INFO` của socket, nên chỉ đo được khi pool nghe bằng
  **TCP**. Pool nghe unix socket thì `listen queue`, `max listen queue`, `listen queue len` không được
  cập nhật (đứng ở 0), bạn sẽ tưởng không bao giờ có hàng đợi. Khi đó nhìn `active processes` so với
  tổng, và error log của Nginx (lỗi `11: Resource temporarily unavailable` là hàng đợi đã đầy).
- ⚠️ `request uri` của từng worker là đường dẫn **sau** khi web server xử lý. php.net ghi chú: với front
  controller (mọi request đi qua `index.php` như Laravel) nó có thể luôn là `/index.php`. Muốn biết URL
  gốc, dùng access log của FPM với `%{REQUEST_URI}e` (mục 5.5).
- ⚠️ Khi pool bão hoà, chính request tới status page cũng phải xếp hàng sau các request khác. Directive
  `pm.status_listen` (từ PHP 8.0) tạo một pool ẩn nghe ở địa chỉ riêng chỉ để phục vụ status, nên vẫn
  đọc được status lúc pool chính kẹt cứng.
- Mọi số liệu là của riêng pool đó và bị reset khi FPM restart.

Ping (`/fpm-ping` trả `pong`, mã 200) là health check rẻ cho load balancer hay Kubernetes. Nó chỉ chứng
minh FPM còn nhận và trả lời được request, không chứng minh app khoẻ (DB có thể đang chết).

Đọc status thẳng qua socket FastCGI, không cần Nginx, bằng công cụ `cgi-fcgi` (gói `libfcgi-bin` trên
Debian/Ubuntu):

```bash
SCRIPT_NAME=/fpm-status SCRIPT_FILENAME=/fpm-status QUERY_STRING=full REQUEST_METHOD=GET \
  cgi-fcgi -bind -connect /run/php/php8.4-fpm.sock
```

### 5.5 Log của FPM và của PHP

Có ba dòng log khác nhau, đừng lẫn:

| Log | Cấu hình | Chứa gì |
|---|---|---|
| Log của FPM | `error_log` trong `[global]` của `php-fpm.conf` | Sự kiện của master: khởi động, reload, worker chết, `reached pm.max_children`, timeout, slow |
| Log lỗi của PHP | `error_log`, `log_errors` trong `php.ini` (hoặc `php_admin_value[error_log]` trong pool) | Warning, fatal error, exception không bắt từ code của bạn |
| Access log của FPM | `access.log`, `access.format` trong pool (mặc định tắt) | Mỗi request một dòng, có thời gian, CPU, bộ nhớ |

Nếu `php.ini` không đặt `error_log`, lỗi PHP dưới FPM được gửi về web server qua kênh stderr của
FastCGI (khi `fastcgi.logging` bật, mặc định là bật), nên bạn thấy chúng trong error log của Nginx với
dòng dạng `FastCGI sent in stderr: "PHP message: PHP Warning: ..."`. Đặt `error_log` riêng cho PHP thì dễ
tìm hơn.

Access log của FPM bổ sung cho access log của Nginx ở chỗ nó biết những thứ chỉ PHP biết. Một định dạng
hữu ích (các placeholder lấy từ tài liệu `access.format`):

```ini
access.log = /var/log/php-fpm/$pool.access.log
access.format = "%{%Y-%m-%dT%H:%M:%S%z}t %m %{REQUEST_URI}e %s %{milli}d ms %{mega}M MB %C%% cpu"
```

- `%{REQUEST_URI}e`: URL gốc client gọi (với Laravel, `%r` thường chỉ là `/index.php`).
- `%{milli}d`: thời gian xử lý; `%{mega}M`: đỉnh bộ nhớ PHP của request; `%C`: phần trăm CPU.
- ⚠️ Con số bộ nhớ ở đây (và `last request memory`, `memory peak` trên status page) là đỉnh bộ nhớ do
  bộ cấp phát của Zend Engine cấp cho request, giống `memory_get_peak_usage(true)`. Nó không gồm bộ nhớ
  mà thư viện C tự cấp riêng, cũng không gồm phần dùng chung như OPcache. Dùng nó để **so sánh** các
  endpoint với nhau; RAM thật của worker vẫn phải đo bằng PSS/USS (mục 4.3).

Dòng log minh hoạ:

```
2026-10-03T10:15:02+0700 POST /orders 201 182.442 ms 18 MB 34.21% cpu
```

Đây là nguồn dữ liệu tốt nhất để tìm endpoint ăn nhiều RAM (đầu vào cho mục 4) hay endpoint chậm vì
chờ (thời gian lớn mà CPU thấp).

`catch_workers_output` (mặc định `no`): những gì worker ghi ra stdout/stderr của chính nó (không phải
output gửi cho client) bị bỏ vào `/dev/null` theo đặc tả FastCGI; bật `yes` để chuyển vào log của FPM.
Container cần bật cái này để log đi ra stdout của container (mục 12.5).

## 6. Điều khiển FPM: signal, reload, restart

### 6.1 Bốn tín hiệu master hiểu

*Signal* (tín hiệu) là cách Unix "gõ cửa" một process: lệnh `kill -<TÊN> <pid>` gửi tín hiệu, process
quyết định làm gì khi nhận. Theo man page `php-fpm.8`, master FPM phản ứng như sau:

| Signal | Hành vi |
|---|---|
| `SIGINT`, `SIGTERM` | Dừng **ngay** (immediate termination) |
| `SIGQUIT` | Dừng **êm** (graceful stop) |
| `SIGUSR1` | Mở lại file log (dùng sau khi logrotate đổi tên file) |
| `SIGUSR2` | Reload êm: thay toàn bộ worker, đọc lại cấu hình (và cả binary) |

```bash
# Chạy trên server, pid lấy từ file pid của FPM (đường dẫn tuỳ cấu hình "pid")
sudo kill -USR2 "$(cat /run/php/php8.4-fpm.pid)"    # reload êm
sudo kill -QUIT "$(cat /run/php/php8.4-fpm.pid)"    # dừng êm
```

Với systemd, unit mẫu trong php-src khai báo `ExecReload=/bin/kill -USR2 $MAINPID`, nên
`systemctl reload php8.4-fpm` chính là gửi `SIGUSR2`. Còn `systemctl stop` (và `restart`, vốn là stop
rồi start) dùng tín hiệu dừng mặc định của systemd là `SIGTERM`, tức dừng **ngay**.

### 6.2 Bên trong một lần reload

Đọc từ `fpm_process_ctl.c` và `fpm_signals.c`, đây là chuyện xảy ra khi master nhận `SIGUSR2`:

1. Master chuyển sang trạng thái "reloading" và ngừng fork worker mới.
2. Master gửi `SIGQUIT` cho **mọi** worker. Worker nhận `SIGQUIT` thì đóng bản sao socket nghe của mình
   (không nhận request mới nữa), chạy **nốt** request đang dở rồi thoát. Worker đang rảnh thoát ngay.
3. Master chờ tối đa `process_control_timeout` giây (directive trong `[global]`). Hết giờ mà còn worker
   sống thì gửi `SIGTERM` (worker chết ngay, request dở bị cắt); một giây sau còn sống nữa thì `SIGKILL`.
4. Khi worker cuối cùng thoát, master `exec()` lại chính chương trình `php-fpm` (cùng PID), đọc lại
   cấu hình và `php.ini`, khởi động lại extension. OPcache tạo vùng shared memory **mới**, nên cache
   trống.
5. Socket nghe được giữ nguyên qua lần `exec()` (FPM truyền file descriptor qua biến môi trường
   `FPM_SOCKETS`), nên trong lúc reload kết nối mới không bị từ chối mà nằm chờ trong listen queue.
6. Master fork worker mới theo cấu hình mới; chúng nhận các kết nối đang chờ.

Timeline với `process_control_timeout = 30s`, lúc nhận tín hiệu worker A đang chạy dở một request còn
khoảng 8 giây nữa mới xong:

| Bước | Master | Worker A (đang bận) | Worker B (đang rảnh) | Request mới tới |
|---|---|---|---|---|
| 0 s | Nhận `SIGUSR2`, gửi `SIGQUIT` cho A, B | Chạy tiếp request | Thoát ngay | |
| 0 tới 8 s | Chờ worker thoát (tối đa 30 s) | Chạy nốt | | Nằm trong listen queue, không ai nhận |
| 8 s | A thoát: `exec()` lại, đọc cấu hình mới | Thoát sau khi trả xong response | | Vẫn chờ |
| ngay sau đó | Fork worker mới (OPcache trống) | | | Được worker mới nhận |

Rút ra:

- Reload êm **không làm rớt** request đang chạy, miễn là chúng xong trước `process_control_timeout`.
- Nhưng reload **không phải không có giá**: trong lúc chờ worker chậm nhất, không có worker nào nhận
  request mới, nên latency nhảy lên trong vài giây. Ngay sau đó OPcache trống, các request đầu tiên phải
  biên dịch lại file (mục 8.6). Reload lúc thấp điểm nếu được.

### 6.3 `process_control_timeout`: mặc định 0 là cái bẫy

```ini
; php-fpm.conf
[global]
process_control_timeout = 30s
```

Mặc định là `0`. Theo bước 3 ở trên, với 0 master gửi `SIGQUIT` rồi gần như ngay lập tức gửi `SIGTERM`:
request đang dở bị cắt dù bạn đã dùng reload "êm". Đặt giá trị này bằng khoảng thời gian dài nhất bạn
chấp nhận chờ một request chạy nốt (thường bằng hoặc hơi lớn hơn `request_terminate_timeout`).

So sánh các cách "khởi động lại":

| Thao tác | Request đang chạy | Request mới trong lúc đó | OPcache |
|---|---|---|---|
| `systemctl reload` (`SIGUSR2`), `process_control_timeout` đủ lớn | Chạy nốt | Chờ trong listen queue, không lỗi | Trống, nạp lại dần |
| `systemctl reload` với `process_control_timeout = 0` | Bị cắt (`SIGTERM`) | Chờ trong listen queue | Trống |
| `systemctl restart` (`SIGTERM` rồi start) | Bị cắt | Socket đóng (unix socket bị xoá) cho tới khi master mới chạy: Nginx trả 502 | Trống |

Kiểm tra cấu hình trước khi reload (`php-fpm8.4 -t`, mục 2.1). Nếu file cấu hình mới sai cú pháp,
master đã `exec()` lại sẽ không khởi động được và bạn mất cả FPM.

### 6.4 `emergency_restart_threshold`: tự reload khi worker chết hàng loạt

```ini
[global]
emergency_restart_threshold = 10
emergency_restart_interval = 1m
```

Nếu có 10 worker thoát vì `SIGSEGV` hoặc `SIGBUS` (lỗi truy cập bộ nhớ, thường do bug trong extension C)
trong vòng 1 phút, FPM tự reload. php.net nêu lý do: để chống chọi với trường hợp shared memory của
opcode cache bị hỏng ngoài ý muốn. Mặc định cả hai là `0` (tắt). Log FPM khi kích hoạt:
`failed processes threshold (10 in 60 sec) is reached, initiating reload`.

Đây là băng cứu thương, không phải cách chữa. Worker segfault là bug thật (thường ở extension hoặc
JIT) cần tìm ra bằng core dump.

## 7. Nginx và FastCGI

### 7.1 FastCGI: Nginx và FPM nói gì với nhau

*FastCGI* là giao thức nhị phân để web server chuyển request cho một chương trình khác xử lý, qua một
kết nối (unix socket hoặc TCP) mà chương trình đó giữ mở và dùng lại cho nhiều request. Nó ra đời để
thay *CGI* đời đầu, nơi mỗi request web phải khởi động hẳn một process mới.

Một request đi qua FastCGI là một chuỗi *record* (gói tin có kiểu):

```
Nginx ──> FPM   BEGIN_REQUEST
Nginx ──> FPM   PARAMS   SCRIPT_FILENAME=/var/www/app/public/index.php
                         REQUEST_METHOD=POST  QUERY_STRING=page=2
                         REQUEST_URI=/orders?page=2  CONTENT_TYPE=...  CONTENT_LENGTH=...
                         HTTP_HOST=shop.example.com  HTTP_COOKIE=...   (mỗi header HTTP thành HTTP_*)
Nginx ──> FPM   PARAMS   (rỗng: hết tham số)
Nginx ──> FPM   STDIN    body của request (dữ liệu form, JSON...)
Nginx ──> FPM   STDIN    (rỗng: hết body)
FPM   ──> Nginx STDOUT   "Status: 201 Created\r\nContent-Type: application/json\r\n\r\n{...}"
FPM   ──> Nginx STDERR   (nếu có thông báo lỗi gửi về web server)
FPM   ──> Nginx END_REQUEST
```

Phía PHP, các `PARAMS` trở thành `$_SERVER` (cùng `$_GET` dựng từ `QUERY_STRING`), `STDIN` là thứ bạn
đọc qua `php://input` và `$_POST` ([chương 15](15-php-va-web.md)). Mọi thứ `echo` ra đi về qua `STDOUT`.
Nginx dịch ngược lại thành một HTTP response cho client.

Hệ quả quan trọng: **PHP chỉ biết những gì Nginx gửi sang trong `PARAMS`**. File nào được chạy, URL gốc
là gì, client dùng HTTPS hay không, IP client là gì: tất cả do cấu hình `fastcgi_param` của Nginx quyết
định.

### 7.2 Cấu hình server cho Laravel, từng dòng

Tài liệu deployment của Laravel 13 đưa cấu hình Nginx khởi điểm sau (giữ nguyên, chỉ thêm chú thích
tiếng Việt):

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name example.com;
    root /srv/example.com/public;              # chỉ thư mục public/ được phục vụ

    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";

    index index.php;

    charset utf-8;

    location / {
        try_files $uri $uri/ /index.php?$query_string;   # file tĩnh có thật thì trả luôn, không thì vào Laravel
    }

    location = /favicon.ico { access_log off; log_not_found off; }
    location = /robots.txt  { access_log off; log_not_found off; }

    error_page 404 /index.php;

    location ~ ^/index\.php(/|$) {                       # CHỈ index.php được chạy bằng PHP
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;  # đổi theo phiên bản PHP của bạn
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_buffer_size 32k;
        fastcgi_buffers 8 32k;
        fastcgi_busy_buffers_size 64k;
        fastcgi_hide_header X-Powered-By;              # không lộ phiên bản PHP
    }

    location ~ /\.(?!well-known).* {
        deny all;                                       # chặn .env, .git... (trừ .well-known)
    }
}
```

Đi qua các phần chính:

- `root .../public`: docs Laravel nhấn mạnh mọi request phải vào `public/index.php` và **không bao giờ**
  đưa `index.php` ra thư mục gốc dự án, vì làm vậy sẽ lộ các file cấu hình nhạy cảm (`.env`,
  `composer.json`, `storage/`...) ra Internet.
- `try_files $uri $uri/ /index.php?$query_string`: Nginx thử lần lượt: có file đúng tên không (ảnh,
  CSS, JS trong `public/`), có thư mục không; không có thì chuyển nội bộ (*internal redirect*) sang
  `/index.php`, giữ nguyên query string. Đây là chỗ hiện thực mô hình front controller.
- `location ~ ^/index\.php(/|$)`: regex chỉ khớp đúng `/index.php` (hoặc `/index.php/...`). Một file
  `.php` nào khác lọt vào `public/` cũng **không** được thực thi; mục 7.4 giải thích vì sao điều này
  quan trọng.
- `fastcgi_pass`: địa chỉ của pool FPM, dạng `unix:/đường/dẫn.sock` hoặc `host:port`
  (`127.0.0.1:9000`, hay `php:9000` trong Docker Compose). Theo tài liệu Nginx, nếu tên miền phân giải
  ra nhiều địa chỉ, Nginx dùng lần lượt kiểu round-robin; muốn cân bằng tải nhiều server FPM thì khai báo
  một khối `upstream`.
- `fastcgi_hide_header X-Powered-By`: PHP mặc định gửi header `X-Powered-By: PHP/8.x.y` (do
  `expose_php`); ẩn nó đi để khỏi lộ phiên bản cho kẻ dò lỗ hổng.
- Buffer: mục 7.5.

Sau khi sửa cấu hình Nginx: `sudo nginx -t` (kiểm tra cú pháp) rồi `sudo systemctl reload nginx`. Reload
của Nginx cũng êm: process cũ phục vụ nốt kết nối đang có, process mới nhận kết nối mới.

### 7.3 `fastcgi_params`, `SCRIPT_FILENAME` và bẫy kế thừa

`include fastcgi_params;` nạp file `fastcgi_params` đi kèm Nginx, chứa các dòng như:

```nginx
fastcgi_param  QUERY_STRING       $query_string;
fastcgi_param  REQUEST_METHOD     $request_method;
fastcgi_param  CONTENT_TYPE       $content_type;
fastcgi_param  CONTENT_LENGTH     $content_length;
fastcgi_param  SCRIPT_NAME        $fastcgi_script_name;
fastcgi_param  REQUEST_URI        $request_uri;
fastcgi_param  DOCUMENT_ROOT      $document_root;
fastcgi_param  HTTPS              $https if_not_empty;
fastcgi_param  REMOTE_ADDR        $remote_addr;
...
```

Header HTTP của client không nằm trong file này; Nginx tự gửi chúng thành tham số `HTTP_*`.

Điểm đáng chú ý: **`fastcgi_params` không có `SCRIPT_FILENAME`**, tham số quan trọng nhất cho PHP biết
chạy file nào. Bạn phải tự đặt (như cấu hình Laravel ở trên). Nginx còn kèm file `fastcgi.conf`, giống
hệt `fastcgi_params` nhưng có thêm dòng
`fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;`. Dùng một trong hai cách, đừng trộn:
`fastcgi_params` cộng `SCRIPT_FILENAME` tự đặt, hoặc `fastcgi.conf` và không đặt lại.

Thiếu `SCRIPT_FILENAME` hoặc đặt sai đường dẫn, FPM không tìm thấy file và trả về trang trắng với dòng
`File not found.` (mã 404, do chính FPM sinh ra, không phải Nginx). Nếu đã đặt `cgi.fix_pathinfo=0`
(mục 7.4), đường dẫn sai cho dòng `No input file specified.` thay vì `File not found.`, cùng mã 404. Nguyên nhân hay gặp nhất là Nginx và
FPM nhìn thấy cây thư mục khác nhau: Nginx thấy `/srv/app/public`, còn container FPM mount code ở
`/var/www/html/public`. Đường dẫn trong `SCRIPT_FILENAME` phải đúng **từ góc nhìn của FPM**.

⚠️ Bẫy kế thừa: tài liệu Nginx ghi rõ các directive `fastcgi_param` được kế thừa từ cấp cấu hình bên
ngoài "khi và chỉ khi" cấp hiện tại **không có** `fastcgi_param` nào. Ví dụ đặt
`fastcgi_param APP_REGION sg;` ở cấp `server` rồi trong `location` có `include fastcgi_params;` cộng
`SCRIPT_FILENAME`: `APP_REGION` sẽ **không** tới được PHP, vì `location` đã có `fastcgi_param` của riêng
nó. Đặt mọi `fastcgi_param` ở cùng một cấp.

### 7.4 Chỉ cho chạy `index.php`: bài học `cgi.fix_pathinfo`

Nhiều hướng dẫn cũ dùng `location ~ \.php$` (chạy mọi file `.php`). Xem chuyện gì có thể xảy ra:

1. App cho người dùng upload ảnh đại diện vào `public/uploads/`. Kẻ tấn công upload file `avatar.jpg`,
   nội dung thật ra là code PHP.
2. Hắn gọi `/uploads/avatar.jpg/x.php`. URL kết thúc bằng `.php` nên khớp `location ~ \.php$`, Nginx gửi
   `SCRIPT_FILENAME=/var/www/app/public/uploads/avatar.jpg/x.php`.
3. File đó không tồn tại. Nhưng `cgi.fix_pathinfo` (mặc định `1`) bảo PHP thử bỏ dần các phần cuối của
   đường dẫn để tìm file có thật, và nó tìm ra `.../uploads/avatar.jpg`.
4. Nếu không có lớp bảo vệ nào khác, `avatar.jpg` được **chạy như code PHP**.

Các lớp bảo vệ, nên có nhiều lớp cùng lúc:

| Lớp | Cách làm | Chặn ở đâu |
|---|---|---|
| Nginx chỉ chuyển đúng một file | `location ~ ^/index\.php(/|$)` như cấu hình Laravel | URL `/uploads/avatar.jpg/x.php` không khớp, rơi về `location /` và vào router của Laravel (404) |
| Nginx kiểm tra file có thật | Trong `location` của PHP thêm `try_files $uri =404;` (khi không dùng `PATH_INFO`) | Nginx trả 404 trước khi tới FPM |
| FPM chỉ chạy đuôi cho phép | `security.limit_extensions` (mặc định `.php .phar` theo mã nguồn FPM) | FPM trả 403 với dòng `Access denied.` vì `avatar.jpg` không có đuôi `.php` |
| PHP không "sửa" đường dẫn | `cgi.fix_pathinfo=0` trong `php.ini` (trang cài Nginx trên php.net khuyên làm) | PHP không lần ngược ra `avatar.jpg` |
| Không để file upload nằm trong `public/` có quyền thực thi | Lưu upload ngoài web root ([chương 17](17-bao-mat.md)) | Không có gì để chạy |

### 7.5 Buffer và giới hạn kích thước

*Buffer response.* Mặc định `fastcgi_buffering on`: Nginx đọc response từ FPM nhanh nhất có thể vào bộ
nhớ đệm (`fastcgi_buffer_size` cho phần đầu chứa header, `fastcgi_buffers` cho phần thân); không đủ chỗ
thì ghi phần thừa ra file tạm trên đĩa (tối đa `fastcgi_max_temp_file_size`, mặc định `1024m`). Nhờ vậy
worker PHP xong việc là được giải phóng, dù client tải chậm (mục 1.2). Tắt buffering (hoặc gửi header
`X-Accel-Buffering: no` từ PHP) chỉ khi bạn cần đẩy dữ liệu tới client ngay, như server-sent events; khi
đó worker bị giữ suốt thời gian client nhận.

*Header quá lớn.* `fastcgi_buffer_size` mặc định bằng một trang bộ nhớ (4K hoặc 8K tuỳ nền tảng). Theo
tài liệu Nginx, phần đầu response vượt quá buffer này bị coi là response không hợp lệ: Nginx trả **502**
và error log có `upstream sent too big header while reading response header from upstream`. App nhiều
cookie hoặc header lớn hay gặp lỗi này; đó là lý do cấu hình Laravel ở trên tăng lên `32k`.

*Body request quá lớn.* `client_max_body_size` của Nginx mặc định `1m`; request có body lớn hơn bị Nginx
trả **413** (Request Entity Too Large) và không bao giờ tới PHP. Muốn cho upload 20 MB phải nâng cả ba
tầng: `client_max_body_size` ở Nginx, `upload_max_filesize` và `post_max_size` ở PHP
([chương 15](15-php-va-web.md)).

### 7.6 Timeout phía Nginx

| Directive | Mặc định | Đo gì | Hết giờ thì |
|---|---|---|---|
| `fastcgi_connect_timeout` | `60s` (tài liệu: thường không thể vượt quá 75 giây) | Thời gian thiết lập kết nối tới FPM | 504 |
| `fastcgi_send_timeout` | `60s` | Khoảng giữa hai lần **ghi** thành công sang FPM | Đóng kết nối |
| `fastcgi_read_timeout` | `60s` | Khoảng giữa hai lần **đọc** được dữ liệu từ FPM | 504 |

⚠️ `fastcgi_read_timeout` **không** phải tổng thời gian của request. Tài liệu Nginx: timeout chỉ áp dụng
giữa hai lần đọc liên tiếp. Một script cứ vài giây lại đẩy hẳn một ít output sang Nginx (`flush()`, kèm
`ob_flush()` nếu đang bật `output_buffering`) có thể chạy lâu hơn
60 giây mà không bị 504. Ngược lại, script im lặng xử lý 61 giây rồi mới trả response thì bị 504.

⚠️ Khi Nginx trả 504, nó chỉ **bỏ cuộc phía mình**: worker PHP không biết gì và vẫn chạy tiếp tới khi
xong (hoặc tới `request_terminate_timeout`). Worker đó vẫn bị chiếm trong lúc người dùng đã thấy lỗi và
có khi bấm F5 gửi thêm request mới.

### 7.7 502 và 504: đọc lỗi thành nguyên nhân

| Client thấy | Dòng error log Nginx hay gặp (rút gọn) | Nguyên nhân thường gặp |
|---|---|---|
| 502 | `connect() to unix:... failed (2: No such file or directory)` | FPM không chạy, hoặc sai đường dẫn socket |
| 502 | `connect() to unix:... failed (13: Permission denied)` | User của Nginx không có quyền trên file socket (mục 2.4) |
| 502 | `connect() to 127.0.0.1:9000 failed (111: Connection refused)` | Không có gì nghe ở cổng đó |
| 502 | `connect() to unix:... failed (11: Resource temporarily unavailable)` | Listen queue đầy: hết worker quá lâu (mục 2.5) |
| 502 | `upstream prematurely closed connection while reading response header from upstream` | Worker chết giữa request: bị `request_terminate_timeout` giết, bị OOM killer giết, segfault |
| 502 | `upstream sent too big header` | Header response vượt `fastcgi_buffer_size` (mục 7.5) |
| 504 | `upstream timed out (110: Connection timed out) while reading response header from upstream` | Script chạy quá `fastcgi_read_timeout` mà chưa trả gì |
| 404 trang trắng `File not found.` (hoặc `No input file specified.`) | (FPM trả, không phải Nginx) | `SCRIPT_FILENAME` thiếu hoặc sai (mục 7.3) |

Quy tắc nhớ nhanh: **502** là Nginx không nói chuyện được với FPM, hoặc FPM trả về thứ không dùng được
(kết nối bị từ chối, bị đóng giữa chừng, header hỏng). **504** là Nginx đã gửi request nhưng chờ quá lâu
mà không nhận được gì.

### 7.8 Chuỗi timeout: tầng trong phải hết giờ trước

Mỗi tầng có đồng hồ riêng. Muốn lỗi được xử lý gọn, đồng hồ của tầng **trong cùng** phải điểm trước:

```
Client → Load balancer → Nginx ──FastCGI──> FPM worker → code PHP → HTTP client / DB
           idle timeout    fastcgi_read_timeout   request_terminate_timeout   timeout của từng lời gọi
           (ví dụ 60s)  >     (ví dụ 55s)      >        (ví dụ 50s)        >   (ví dụ 5–10s)
```

Vì sao thứ tự này:

1. Timeout của HTTP client hay của query hết trước: code PHP nhận exception, ghi log, trả response có
   nghĩa (ví dụ 503 kèm thông báo), worker rảnh ngay.
2. Nếu `request_terminate_timeout` hết trước: worker bị giết, mất log, Nginx trả 502 (mục 5.2).
3. Nếu Nginx hoặc load balancer hết giờ trước FPM: client nhận 504 nhưng worker vẫn chạy và chiếm chỗ,
   client thử lại, gửi thêm request vào một pool đã đầy. Đây là vòng xoáy biến một sự cố nhỏ thành sập.

Đừng giả định giá trị mặc định của từng tầng; kiểm tra trong hệ thống thật. Ví dụ Guzzle dùng trực
tiếp thì mặc định `timeout` là 0, tức chờ vô hạn; HTTP client của Laravel 13 (lớp `PendingRequest`) đặt
sẵn `timeout` 30 giây và `connect_timeout` 10 giây. 30 giây vẫn là quá lâu cho phần lớn API, nên đặt
`Http::timeout(...)` theo từng đối tác.

### 7.9 Tình huống: 502/504 lúc cao điểm mà CPU không cao

Tình huống kinh điển: 20 giờ tối, Nginx trả 502 và 504 hàng loạt, CPU của server web chỉ 30%.

1. **Xác nhận pool bão hoà.** Status page: `active processes` bằng tổng, `idle processes` gần 0; với
   pool TCP thì `listen queue` > 0. Log FPM có `server reached pm.max_children setting` (với `dynamic`).
   Error log Nginx có `(11: Resource temporarily unavailable)` hoặc `upstream timed out`.
2. **CPU thấp mà hết worker** nghĩa là các worker không bận tính toán mà đang **chờ**: DB chậm, API ngoài
   treo, chờ lock (session file, `SELECT ... FOR UPDATE`), Redis quá tải.
3. **Tìm xem chúng chờ gì.** Slow log (dòng đầu của mỗi stack, mục 5.3), access log của FPM (endpoint
   nào thời gian lớn mà CPU nhỏ, mục 5.5), APM nếu có. Đối chiếu phía sau: slow query log và danh sách
   query đang chạy của MySQL.
4. **Sửa đúng nguyên nhân**, theo thứ tự ưu tiên: đặt timeout ngắn cho lời gọi ra ngoài; sửa query chậm;
   đưa việc chậm vào queue; tách endpoint chậm sang pool riêng (mục 2.3).
5. **Tăng `pm.max_children` sau cùng**, và chỉ khi còn RAM (mục 4) **và** phía sau chịu được thêm tải.
   Thêm worker khi DB đang là nút thắt chỉ dồn thêm query vào DB.

## 8. OPcache trên production

### 8.1 Nhắc lại và kiểm tra OPcache có thật sự bật cho FPM

Ở [chương 02, mục 3](02-php-chay-nhu-the-nao.md#3-opcache-biên-dịch-một-lần-dùng-lại-nhiều-lần) bạn đã
biết: OPcache lưu opcode đã biên dịch vào shared memory, mọi worker của cùng một master FPM dùng chung
một cache, và cache của CLI là chuyện riêng của CLI. Mục này nói chuyện cấu hình và vận hành.

- Từ PHP 8.5, theo UPGRADING của php-src, OPcache luôn được build vào binary và luôn được nạp; không còn
  file `opcache.so`, dòng `zend_extension=opcache.so` trong `php.ini` sẽ sinh warning. Bật hay tắt vẫn do
  `opcache.enable` (mặc định `1`) và `opcache.enable_cli` (mặc định `0`) quyết định.
- Với 8.4 trở về trước, OPcache là extension riêng phải được nạp bằng `zend_extension`. Gói của
  distro thường bật sẵn; với Docker, Dockerfile hiện tại của image chính thức bản 8.4 có dòng
  `docker-php-ext-enable opcache`. Đừng dựa vào trí nhớ: kiểm tra.

Kiểm tra **từ bên trong FPM**, không phải từ terminal: gọi `opcache_get_status()` qua HTTP (mục 8.5).
`php -m` trên terminal chỉ cho biết extension có được nạp ở CLI hay không.

### 8.2 Ba vùng nhớ, ba giới hạn

| Directive | Mặc định | Ý nghĩa |
|---|---|---|
| `opcache.memory_consumption` | `128` (MB) | Dung lượng shared memory cho opcode. Tối thiểu 8. Khi bật JIT, segment còn chứa thêm `jit_buffer_size` |
| `opcache.interned_strings_buffer` | `8` (MB) | Vùng chứa *interned string*: chuỗi dùng chung như tên class, tên hàm, chuỗi literal. Tối đa 32767 trên máy 64-bit (từ 8.4; trước đó 4095) |
| `opcache.max_accelerated_files` | `10000` | Số key tối đa trong bảng băm của cache. Giá trị thật là số nguyên tố đầu tiên ≥ giá trị đặt, trong dãy {223, 463, 983, 1979, 3907, 7963, 16229, 32531, 65407, 130987, 262237, 524521, 1048793}; 10000 thành 16229. Tối thiểu 200, tối đa 1000000 |

Cả ba đều là `INI_SYSTEM`: chỉ đặt được trong `php.ini` (hoặc file `.ini` trong `conf.d/`), đổi xong
phải reload FPM.

Chọn giá trị:

- `max_accelerated_files`: đếm số file PHP của app **kể cả `vendor/`** (`find /var/www/app -name '*.php' | wc -l`)
  rồi đặt cao hơn rõ rệt. Một file có thể chiếm nhiều hơn một key (đường dẫn qua symlink và đường dẫn
  thật là hai key, mục 11.4).
- `memory_consumption` và `interned_strings_buffer`: bắt đầu từ mặc định hoặc gấp đôi, chạy thật, rồi
  đọc `opcache_get_status()` (mục 8.5) để chỉnh. Không có con số đúng cho mọi app.

### 8.3 OPcache biết file đã đổi bằng cách nào

| Directive | Mặc định | Ý nghĩa |
|---|---|---|
| `opcache.validate_timestamps` | `1` | Có kiểm tra file trên đĩa đã đổi hay không |
| `opcache.revalidate_freq` | `2` (giây) | Mỗi script được kiểm tra tối đa một lần trong N giây; `0` là kiểm tra ở mọi lần nạp |
| `opcache.file_update_protection` | `2` (giây) | Không cache file có thời điểm sửa (mtime) mới hơn N giây, để tránh cache file đang ghi dở |

Cách kiểm tra: OPcache gọi `stat()` lấy *mtime* (thời điểm sửa đổi cuối) của file và so với mtime lúc
cache. Khác thì biên dịch lại. Thí nghiệm sau chạy thật được trên CLI (bật OPcache cho CLI bằng `-d`):

```php
<?php
declare(strict_types=1);

// revalidate.php
$file = __DIR__ . '/greeting.php';

file_put_contents($file, "<?php return 'phiên bản 1';");
touch($file, time() - 100);   // mtime lùi về quá khứ để khỏi vướng file_update_protection
echo include $file, "\n";

file_put_contents($file, "<?php return 'phiên bản 2';");
touch($file, time() - 50);    // mtime mới hơn lần trước 50 giây
echo include $file, "\n";

var_dump(opcache_invalidate($file));   // bỏ riêng file này khỏi cache
echo include $file, "\n";
```

```bash
php -d opcache.enable_cli=1 -d opcache.validate_timestamps=0 revalidate.php
# phiên bản 1
# phiên bản 1          <- file trên đĩa đã đổi, nhưng không ai kiểm tra
# bool(true)
# phiên bản 2          <- chỉ sau khi invalidate

php -d opcache.enable_cli=1 -d opcache.validate_timestamps=1 -d opcache.revalidate_freq=0 revalidate.php
# phiên bản 1
# phiên bản 2          <- kiểm tra ở mọi lần nạp, thấy mtime đổi
# bool(true)
# phiên bản 2

php -d opcache.enable_cli=1 revalidate.php           # mặc định: validate_timestamps=1, revalidate_freq=2
# phiên bản 1
# phiên bản 1          <- chưa quá 2 giây kể từ lần kiểm trước
# bool(true)
# phiên bản 2
```

Production thường đặt `opcache.validate_timestamps=0`: code chỉ đổi khi deploy, nên bỏ hẳn việc `stat()`
file ở mỗi request. Cái giá: theo php.net, khi đó thay đổi trên đĩa chỉ có hiệu lực sau khi gọi
`opcache_reset()`, `opcache_invalidate()` hoặc khởi động lại server. Quy trình deploy **bắt buộc** phải
có bước xoá cache (mục 8.6, mục 11).

Môi trường dev thì ngược lại: `validate_timestamps=1`, `revalidate_freq=0` để sửa code là thấy ngay.

### 8.4 Wasted memory, cache đầy và restart

Shared memory của OPcache chỉ cấp phát thêm, không dồn lại. Khi một file được biên dịch lại (vì đổi
mtime, vì `opcache_invalidate()`), bản cũ bị đánh dấu bỏ và phần nhớ của nó thành *wasted memory*
(bộ nhớ phí), không dùng lại được cho tới lần restart cache.

Đọc mã nguồn `ext/opcache/ZendAccelerator.c`, chuyện xảy ra khi hết chỗ (hết `memory_consumption`, hoặc
bảng băm đã đủ `max_accelerated_files` key):

1. OPcache đánh dấu cache đầy (`cache_full = true` trong `opcache_get_status()`).
2. Nếu tỉ lệ wasted ≥ `opcache.max_wasted_percentage` (mặc định 5): lên lịch *restart*, tức xoá sạch
   cache làm lại từ đầu. Bộ đếm `oom_restarts` (hết bộ nhớ) hoặc `hash_restarts` (hết key) tăng.
3. Nếu chưa tới ngưỡng: **không restart**. Từ đó mọi file chưa có trong cache bị biên dịch lại ở **mỗi
   request**, như thể không có OPcache cho những file đó. App không lỗi gì, chỉ chậm dần và CPU tăng.

Restart cũng không xảy ra ngay. Khi đã lên lịch, OPcache tạm ngưng dùng cache (request mới biên dịch file
như không có OPcache) và chờ tới lúc không còn request nào đang dùng cache mới xoá. php.net mô tả
`opcache.force_restart_timeout` (mặc định 180 giây): chờ quá chừng đó mà vẫn có process giữ cache thì
OPcache cho rằng có gì đó hỏng và **giết các process đang giữ** để restart được. Trên server bận, một
lần restart cache là một đợt CPU tăng vọt.

Interned strings cũng có thể đầy riêng: khi đó chuỗi mới không vào được vùng dùng chung, mỗi worker phải
giữ bản riêng, tốn RAM hơn.

### 8.5 Đọc `opcache_get_status()`

Script dưới đây phải được gọi **qua HTTP** (để chạy trong FPM), đặt sau xác thực hoặc chỉ cho IP nội bộ:

```php
<?php
declare(strict_types=1);

// opcache-health.php
$s = opcache_get_status(false);    // false: không kèm danh sách từng script cho nhẹ
if ($s === false) {
    exit("OPcache tắt cho process này (hoặc bị opcache.restrict_api chặn)\n");
}

$mem   = $s['memory_usage'];
$stat  = $s['opcache_statistics'];
$istr  = $s['interned_strings_usage'];
$total = $mem['used_memory'] + $mem['free_memory'] + $mem['wasted_memory'];

printf("bộ nhớ    : %.1f%% đã dùng, %.1f%% wasted\n",
    100 * $mem['used_memory'] / $total, $mem['current_wasted_percentage']);
printf("key       : %d / %d\n", $stat['num_cached_keys'], $stat['max_cached_keys']);
printf("interned  : %.1f%% đã dùng\n", 100 * $istr['used_memory'] / $istr['buffer_size']);
printf("hit rate  : %.2f%%\n", $stat['opcache_hit_rate']);
printf("cache_full=%s  oom_restarts=%d  hash_restarts=%d  manual_restarts=%d\n",
    var_export($s['cache_full'], true),
    $stat['oom_restarts'], $stat['hash_restarts'], $stat['manual_restarts']);
```

Chạy file này bằng `php opcache-health.php` trên terminal in ra
`OPcache tắt cho process này (hoặc bị opcache.restrict_api chặn)`: CLI mặc định không bật OPcache, và kể
cả có bật thì đó cũng là cache của chính lệnh CLI, không phải của FPM. Gọi qua web trên một server
khoẻ, output trông như sau (output minh hoạ):

```
bộ nhớ    : 61.3% đã dùng, 0.4% wasted
key       : 9120 / 32531
interned  : 72.5% đã dùng
hit rate  : 99.97%
cache_full=false  oom_restarts=0  hash_restarts=0  manual_restarts=0
```

Cách đọc:

| Thấy | Nghĩa | Làm gì |
|---|---|---|
| `cache_full=true`, hoặc bộ nhớ đã dùng gần 100% | Hết chỗ cho opcode | Tăng `memory_consumption` |
| `key` sát trần | Sắp hết key | Tăng `max_accelerated_files` |
| `interned` gần 100% | Vùng interned string sắp đầy | Tăng `interned_strings_buffer` |
| `oom_restarts`, `hash_restarts` tăng dần theo ngày | Cache bị xoá sạch định kỳ vì hết chỗ | Tăng các giới hạn trên; kiểm tra quy trình deploy có xoá cache không |
| `hit rate` thấp ở trạng thái ổn định | Có gì đó làm miss liên tục | Xem cache có đầy không, có file sinh ra liên tục không |

Thêm `start_time` và `last_restart_time` trong `opcache_statistics`: so với giờ deploy để biết cache đã
được làm mới sau deploy chưa.

### 8.6 Xoá cache đúng cách

| Cách | Phạm vi | Ghi chú |
|---|---|---|
| Reload FPM (`systemctl reload`, `SIGUSR2`) | Toàn bộ, kèm realpath cache của mọi worker | Cách sạch nhất: worker mới là process mới, shared memory tạo mới (mục 6.2) |
| `opcache_reset()` **gọi bên trong FPM** | Toàn bộ opcode cache trong RAM | php.net: chỉ reset cache trong bộ nhớ, không reset file cache; trả `false` nếu OPcache tắt hoặc đang có restart chờ. Thực chất là lên lịch restart (mục 8.4) |
| `opcache_invalidate($file, $force)` | Một file | Mặc định chỉ bỏ khi mtime file mới hơn bản cache; `$force = true` thì bỏ bất kể |

⚠️ Bẫy kinh điển: chạy `php -r 'opcache_reset();'` trong script deploy. Lệnh đó chạy trong một process
CLI riêng, với cache riêng (mà mặc định còn tắt). Cache của FPM **không hề bị đụng tới**. Muốn reset cache
FPM mà không reload thì lời gọi phải chạy trong FPM: qua một URL nội bộ có bảo vệ, hoặc qua công cụ nói
chuyện thẳng với socket FastCGI (ví dụ dự án mã nguồn mở `cachetool`).

`opcache.restrict_api` (mặc định rỗng, tức không hạn chế) giới hạn chỉ script nằm dưới một đường dẫn
nhất định mới được gọi các hàm API của OPcache; gọi từ chỗ khác sẽ nhận warning
"API is restricted by "restrict_api" configuration directive". Nên đặt, để code bị chèn không gọi được
`opcache_reset()` liên tục làm sập hiệu năng.

### 8.7 Các directive khác nên biết

| Directive | Mặc định | Khi nào quan tâm |
|---|---|---|
| `opcache.save_comments` | `1` | Tắt đi thì mất docblock trong cache; php.net cảnh báo làm hỏng thư viện đọc annotation từ comment (Doctrine, PHPUnit...). Giữ mặc định |
| `opcache.enable_file_override` | `0` | Bật thì `file_exists()`, `is_file()`, `is_readable()` hỏi cache trước; php.net: có rủi ro trả dữ liệu cũ khi `validate_timestamps=0` |
| `opcache.file_cache` | rỗng (tắt) | Thư mục làm cache cấp hai trên đĩa: có ích khi SHM đầy, khi server vừa khởi động, khi SHM bị reset |
| `opcache.file_cache_read_only` | (mới ở 8.5) | Dùng thư mục file cache dựng sẵn trên filesystem chỉ đọc, ví dụ container read-only. UPGRADING khuyên đi kèm `validate_timestamps=0`, `enable_file_override=1`, `file_cache_consistency_checks=0`; cache tạo bởi build PHP khác, đường dẫn khác hay cấu hình khác có thể bị bỏ qua |
| `opcache.blacklist_filename` | rỗng | File liệt kê các script không được cache |
| `opcache.huge_code_pages` | `0` | Chép đoạn mã máy của binary PHP vào huge page; cần cấu hình OS. Không ảnh hưởng vùng SHM của opcode |
| `opcache.validate_permission`, `opcache.validate_root` | `0` | Cho môi trường nhiều user / chroot dùng chung một cache (shared hosting) |

### 8.8 Cấu hình mẫu

Production (code chỉ đổi khi deploy, deploy luôn có bước reload FPM):

```ini
; /etc/php/8.4/fpm/conf.d/99-opcache.ini  (Docker: $PHP_INI_DIR/conf.d/opcache.ini)
opcache.enable=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=32531
opcache.validate_timestamps=0
opcache.restrict_api=/var/www/ops/   ; chỉ script trong thư mục này gọi được API OPcache
```

Dev:

```ini
opcache.enable=1
opcache.validate_timestamps=1
opcache.revalidate_freq=0
```

Các con số ở bản production là điểm xuất phát; giá trị đúng cho app của bạn đến từ việc đọc
`opcache_get_status()` sau vài ngày chạy thật.

## 9. Preloading

### 9.1 Preloading giải quyết phần việc nào còn lại

Có OPcache rồi, mỗi request vẫn còn một ít việc lặp lại với từng class: autoloader của Composer được gọi
để tìm file, OPcache tra cache (và `stat()` file nếu `validate_timestamps=1`), rồi class trong cache
được nạp vào bảng class của request. *Preloading* (có từ PHP 7.4) làm các việc đó **một lần lúc server
khởi động**: theo php.net, mọi hàm, class, interface, trait (nhưng **không** gồm hằng số) trong các file
được preload sẽ có sẵn cho mọi request mà không cần `include`, cho tới khi server tắt.

Đổi lại, php.net nói thẳng: bạn đánh đổi lấy mức bộ nhớ nền cao hơn, và muốn bỏ code đã preload thì
**phải khởi động lại process PHP**. Vì thế php.net kết luận preloading chỉ thực tế cho production, không
cho môi trường dev.

### 9.2 Viết preload script

```ini
; php.ini của FPM
opcache.preload=/var/www/app/preload.php
opcache.preload_user=www-data     ; khi master FPM chạy bằng root
```

`preload.php` là một file PHP bình thường, chạy một lần khi FPM khởi động. Mọi file được nó `include`,
`require` hoặc truyền cho `opcache_compile_file()` sẽ được nạp vào bộ nhớ bền. Thí nghiệm nhỏ, chạy được
bằng CLI:

```
pre/
├── preload.php
├── app.php
└── src/
    ├── Money.php       final class Money
    └── Discount.php    final class Discount extends BasePolicy   (BasePolicy không có ở đâu cả)
```

```php
<?php
declare(strict_types=1);

// src/Money.php
final class Money
{
    public function __construct(public readonly int $cents) {}

    public function format(): string
    {
        return number_format($this->cents / 100, 2) . ' USD';
    }
}
```

```php
<?php
declare(strict_types=1);

// preload.php: chạy MỘT lần lúc server khởi động
foreach (glob(__DIR__ . '/src/*.php') as $file) {
    opcache_compile_file($file);   // chỉ biên dịch, không chạy code của file
}
```

```php
<?php
declare(strict_types=1);

// app.php: không có require, không có autoloader
echo (new Money(123450))->format(), "\n";
var_dump(class_exists('Discount', false));
```

```bash
php -d opcache.enable_cli=1 -d opcache.preload="$PWD/preload.php" app.php
```

Output:

```
Warning: Can't preload unlinked class Discount: Unknown parent BasePolicy in .../src/Discount.php on line 4
1,234.50 USD
bool(false)
```

- `Money` dùng được dù `app.php` không `require` gì: class đã nằm sẵn trong bộ nhớ.
- `Discount` kế thừa một class không tồn tại lúc preload, nên không được preload: chỉ có **warning**,
  không fatal. Class được preload phải *liên kết* được đầy đủ (class cha, interface, trait có mặt).

`include` và `opcache_compile_file()` khác nhau (php.net):

| | `include` / `require` | `opcache_compile_file()` |
|---|---|---|
| Chạy code trong file | Có | Không, chỉ biên dịch |
| Thứ tự nạp | Class cha phải được nạp trước class con | Thứ tự nào cũng được |
| Khai báo có điều kiện (hàm trong `if`) | Được hỗ trợ | Không |

⚠️ `opcache_compile_file()` không gọi autoloader. Class cha, interface, trait nằm trong `vendor/` mà
script không nạp thì class con không được preload (warning như trên). Cách thường dùng là `require`
autoloader của Composer ở đầu preload script rồi dùng `require_once` hay `class_exists()` để kéo cả cây
phụ thuộc vào.

### 9.3 Giới hạn và cái bẫy khi deploy

- Hằng số toàn cục (`define()`, `const` ở cấp file) không được preload.
- Không hỗ trợ Windows. Với CLI gần như vô nghĩa vì không có process sống qua nhiều request (php.net
  nêu ngoại lệ: preload thư viện FFI).
- `opcache.preload_user`: preload bằng root bị cấm mặc định vì lý do bảo mật; directive này chỉ định
  user chạy preload khi server khởi động bằng root. Từ PHP 8.3 không cần đặt nó khi chạy bằng root ở
  SAPI CLI hoặc phpdbg.
- ⚠️ Code đã preload ở lại tới khi process PHP tắt. Đọc mã nguồn OPcache: khi cache restart (kể cả do
  `opcache_reset()`), phần preload được giữ lại. Sửa file nguồn không có tác dụng, reset cache không có tác
  dụng. Deploy code mới phải **restart hoặc reload FPM** để master chạy lại preload từ đầu. Quy trình deploy
  chỉ reset OPcache sẽ chạy code mới lẫn với class cũ đã preload: loại bug rất khó lần ra.

### 9.4 Có nên dùng

RFC Preloading đo được mức tăng khoảng 30% và 50% trên các app mẫu dựng trên Zend Framework (loại app
mà chi phí nạp class chiếm phần lớn thời gian). App thật có query database và gọi mạng thì phần trăm
nhỏ hơn nhiều. Symfony có sinh sẵn file preload; Laravel không sinh, bạn phải tự viết hoặc dùng package
bên thứ ba. Lời khuyên thực dụng: chỉ bật khi đã đo (profiler cho thấy thời gian nạp class đáng kể) và
quy trình deploy đã chắc chắn có bước reload FPM.

## 10. JIT ở mức vận hành

### 10.1 JIT là gì, trong một đoạn

*JIT* (Just-In-Time compiler, có từ PHP 8.0) là một phần của OPcache. Nó dịch opcode của những đoạn code
chạy nhiều ("nóng") thành **mã máy** của CPU, để chạy thẳng thay vì để Zend VM thông dịch từng opcode.
Mã máy được giữ trong một vùng của shared memory OPcache (`opcache.jit_buffer_size`), dùng chung cho
mọi worker. Cách JIT tracing hoạt động bên trong nằm ở [chương 19](19-ben-trong-engine.md); đo hiệu năng
ở [chương 20](20-hieu-nang.md). Mục này chỉ trả lời: bật thế nào, kiểm tra ra sao, có nên bật không.

### 10.2 Bật JIT: PHP 8.4 đã đổi công tắc

UPGRADING của PHP 8.4 ghi: giá trị mặc định đổi từ `opcache.jit=tracing`, `opcache.jit_buffer_size=0`
sang `opcache.jit=disable`, `opcache.jit_buffer_size=64M`. JIT **vẫn tắt mặc định** như cũ, chỉ có công
tắc là đổi chỗ:

| | PHP 8.0 tới 8.3 | PHP 8.4 trở đi |
|---|---|---|
| `opcache.jit` mặc định | `tracing` | `disable` |
| `opcache.jit_buffer_size` mặc định | `0` | `64M` |
| Cách bật | Đặt `jit_buffer_size` khác 0 | Đặt `opcache.jit` thành `tracing` (hoặc `function`) |

⚠️ Mang cấu hình cũ chỉ có `opcache.jit_buffer_size=128M` lên 8.4: JIT vẫn tắt, không có cảnh báo gì.
Cấu hình rõ ràng cho cả hai thời kỳ:

```ini
opcache.enable=1
opcache.jit=tracing
opcache.jit_buffer_size=64M
```

Các giá trị của `opcache.jit` (php.net): `disable` (tắt hẳn, không bật lại được lúc chạy), `off` (tắt
nhưng bật lại được lúc chạy), `tracing` hoặc `on` (php.net: "khuyến nghị cho hầu hết người dùng"),
`function`. Còn có dạng số bốn chữ số CRTO cho người dùng nâng cao; `tracing` tương ứng 1254, `function`
tương ứng 1205.

Thêm hai điểm vận hành:

- Theo php.net, khi bật JIT thì segment shared memory có tổng dung lượng bằng `memory_consumption` cộng
  `jit_buffer_size`. Tính RAM (mục 4) phải cộng cả phần này.
- Từ 8.4, nếu JIT được bật mà khởi tạo thất bại, PHP dừng với fatal error lúc khởi động (trước đó chạy
  tiếp không JIT). Kiểm tra cấu hình trên môi trường staging trước.

### 10.3 Kiểm tra JIT có thật sự chạy

Trong một trang chạy dưới FPM:

```php
<?php
declare(strict_types=1);

$jit = opcache_get_status(false)['jit'] ?? null;
var_dump($jit === null ? 'không có thông tin JIT' : [
    'enabled'     => $jit['enabled'],
    'on'          => $jit['on'],
    'buffer_size' => $jit['buffer_size'],
    'buffer_free' => $jit['buffer_free'],
]);
```

`on` là `true` nghĩa là JIT đang hoạt động. `buffer_free` gần 0 nghĩa là vùng nhớ JIT đã đầy, code nóng
mới không được dịch nữa. (Bản PHP không build kèm JIT, ví dụ một số bản trên nền tảng lạ, sẽ không có
khoá `jit`.)

⚠️ Extension ghi đè hàm thực thi của engine làm JIT tự tắt, với warning lúc khởi động:
`JIT is incompatible with third party extensions that override zend_execute_ex(). JIT disabled.` Xdebug
là ví dụ hay gặp. Đo hiệu năng JIT trên máy có Xdebug là đo sai.

### 10.4 Khi nào JIT đáng bật

JIT chỉ tăng tốc phần thời gian CPU chạy **code PHP**. Một request Laravel điển hình phần lớn thời gian
là chờ MySQL, Redis, API; phần CPU còn lại phần nhiều nằm trong hàm viết bằng C sẵn có (`json_encode`,
`preg_*`, PDO) vốn đã là mã máy. RFC JIT tự đo: benchmark tính toán thuần (Mandelbrot) nhanh hơn nhiều
lần, còn WordPress gần như không đổi. Với app web thông thường, đừng kỳ vọng JIT làm request nhanh rõ.

Quy trình hợp lý:

1. Dùng profiler xác định request có thật sự tốn CPU cho code PHP không
   ([chương 20](20-hieu-nang.md)).
2. Benchmark cùng tải, cùng máy, hai cấu hình: JIT `disable` và `tracing`; so latency p95/p99 và CPU, không
   chỉ số request mỗi giây.
3. Chỉ bật trên production khi thấy lợi rõ.

JIT là một tầng phức tạp và từng có bug riêng (kết quả sai, crash) khó điều tra hơn nhiều so với VM.
Không đo được lợi ích thì không có lý do mang rủi ro đó lên production. Workload hưởng lợi thật thường là
xử lý tính toán nặng bằng PHP thuần: parser, thuật toán, xử lý dữ liệu số trong worker CLI.

## 11. Deploy không downtime bằng symlink

### 11.1 Vấn đề của việc ghi đè code đang chạy

Cách deploy ngây thơ nhất là `git pull` (hoặc `rsync`) thẳng vào thư mục đang phục vụ. Trong vài giây
đó, đĩa chứa một nửa code cũ một nửa code mới:

- Một request đang chạy có thể `require` một file đã là bản mới từ một file vẫn là bản cũ: gọi hàm
  không tồn tại, sai số tham số, fatal error.
- Với `validate_timestamps=1`, OPcache có thể cache một file đang được ghi dở (đó là lý do tồn tại
  `file_update_protection`).
- `composer install` chạy giữa chừng thì `vendor/` có lúc thiếu file.
- Muốn rollback thì phải deploy lại bản cũ, cũng chậm và cũng dở dang như vậy.

### 11.2 Cấu trúc releases, shared, current

Cách mà Capistrano, Deployer, Envoyer... đều dùng: mỗi lần deploy là một thư mục mới, chuẩn bị xong xuôi
rồi mới chuyển sang bằng một thao tác đổi symlink.

```
/var/www/app/
├── current  ->  releases/20261003_1015      Nginx: root /var/www/app/current/public
├── releases/
│   ├── 20261002_1730/                        bản trước, giữ lại để rollback
│   └── 20261003_1015/                        bản mới
└── shared/
    ├── .env                                  symlink vào từng release
    └── storage/                              log, file upload...; symlink vào từng release
```

*Symlink* (symbolic link) là một file đặc biệt chỉ chứa đường dẫn tới file/thư mục khác. Đổi `current`
trỏ sang release mới là đổi toàn bộ code trong một bước, không có lúc nào lẫn lộn trên đĩa. Rollback là
đổi `current` về thư mục cũ.

### 11.3 Đổi symlink nguyên tử

```bash
# Chạy trên server, trong /var/www/app
ln -s releases/20261003_1015 current.tmp
mv -T current.tmp current
```

`mv -T` (GNU coreutils) đổi tên `current.tmp` đè lên `current` bằng system call `rename()`, vốn là thao
tác *nguyên tử* (atomic) trên cùng một filesystem: mọi process nhìn thấy hoặc symlink cũ, hoặc symlink
mới, không bao giờ thấy "không có gì". ⚠️ Đừng mặc định `ln -sfn` an toàn trong mọi môi trường: một số bản
`ln` thực hiện bằng cách xoá link cũ rồi tạo link mới, để lộ một khoảnh khắc `current` không tồn tại
(Nginx trả 404). Tạo link tạm rồi `mv -T` là cách tường minh.

### 11.4 Cái bẫy: đổi symlink xong vẫn chạy code cũ

Chỉ đổi symlink thì rất có thể web **vẫn chạy code cũ**. Có hai cache dính vào chuyện này.

*Realpath cache.* Mỗi process PHP có một cache riêng (không nằm trong shared memory) nhớ "đường dẫn này,
sau khi giải hết symlink, `.` và `..`, thì là file thật nào", để khỏi gọi `lstat()` lặp lại cho từng thành
phần đường dẫn ở mỗi lần `require`. Mặc định `realpath_cache_size = 4096K`, `realpath_cache_ttl = 120`
(giây). Một worker đã giải `/var/www/app/current` thành `releases/20261002_1730` có thể tiếp tục dùng kết
quả đó tới 120 giây.

*Key của OPcache.* Nginx gửi `SCRIPT_FILENAME=/var/www/app/current/public/index.php`. OPcache lưu script
theo đường dẫn, và cũng nhớ đường dẫn được đưa vào (qua symlink) như một key trỏ tới bản đã biên dịch.
Với `validate_timestamps=0`, không có gì kiểm tra lại: key `.../current/public/index.php` tiếp tục trỏ
vào bản biên dịch của release cũ **mãi mãi**, cho tới khi cache bị xoá. Với `validate_timestamps=1`, tới
lượt kiểm tra OPcache mới phát hiện, nhưng việc giải đường dẫn lại đi qua realpath cache của từng worker,
nên trong một khoảng các worker khác nhau có thể trả về code khác nhau.

Điểm tốt: một khi `index.php` đã được giải thành release cũ, mọi `require __DIR__ . '/../vendor/autoload.php'`
phía sau dùng đường dẫn thật của chính release đó (vì `__DIR__` là đường dẫn thật), nên **một** request
không bao giờ trộn file của hai release. Cái trộn là giữa các worker, hoặc giữa trước và sau.

### 11.5 Hai cách xử lý (thường dùng cả hai)

1. **Reload FPM sau khi đổi symlink** (mục 6). Worker mới là process mới: realpath cache trống, OPcache
   trống. Nhớ đặt `process_control_timeout` khác 0 để request đang dở được chạy nốt.
2. **Để Nginx tự giải symlink** bằng `$realpath_root` thay cho `$document_root`. Theo tài liệu Nginx,
   `$realpath_root` là đường dẫn tuyệt đối ứng với `root` của request "với mọi symbolic link đã được giải
   thành đường dẫn thật". Nginx gửi cho FPM
   `SCRIPT_FILENAME=/var/www/app/releases/20261003_1015/public/index.php`: một đường dẫn mới hẳn, nên là
   một key OPcache mới, được biên dịch từ code mới ngay cả khi chưa reload.

```nginx
location ~ ^/index\.php(/|$) {
    fastcgi_pass unix:/run/php/php8.4-fpm.sock;
    fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;   # đường dẫn thật của release
    include fastcgi_params;
}
```

Lưu ý `fastcgi_params` vẫn gửi `DOCUMENT_ROOT` bằng `$document_root` (đường dẫn qua symlink). Với
Laravel điều đó không ảnh hưởng, chỉ `SCRIPT_FILENAME` quyết định file nào được chạy.

⚠️ Chỉ dùng `$realpath_root` mà không bao giờ reload: bản biên dịch của các release cũ vẫn nằm trong
shared memory thành rác. Sau vài chục lần deploy, cache đầy (mục 8.4). Vẫn nên reload FPM mỗi lần deploy.

⚠️ Đã bật preloading (mục 9) thì bắt buộc reload/restart FPM, `$realpath_root` không cứu được class cũ
đã preload.

### 11.6 Script deploy tối thiểu

Script dưới đây chạy trên server web, cho một app Laravel, gói lại các bước của mục này. Các lệnh
`artisan` (cache cấu hình, migrate, khởi động lại queue worker) thuộc về
[chương 30](30-laravel-testing-octane-deploy.md); ở đây chỉ cần hiểu chúng chạy **trước** khi đổi symlink.

```bash
#!/usr/bin/env bash
set -euo pipefail
APP=/var/www/app
REL=$APP/releases/$(date +%Y%m%d_%H%M%S)

git clone --depth 1 --branch main git@github.com:acme/shop.git "$REL"
cd "$REL"
ln -s "$APP/shared/.env" .env
rm -rf storage && ln -s "$APP/shared/storage" storage

composer install --no-dev --optimize-autoloader --no-interaction
php artisan optimize                 # chương 30
php artisan migrate --force          # chương 30: migration phải tương thích với code cũ

ln -s "$REL" "$APP/current.tmp" && mv -T "$APP/current.tmp" "$APP/current"   # đổi symlink nguyên tử
sudo php-fpm8.4 -t                   # kiểm tra cấu hình trước khi reload
sudo systemctl reload php8.4-fpm     # xoá OPcache + realpath cache của mọi worker

# giữ lại 5 release gần nhất
ls -1dt "$APP"/releases/* | tail -n +6 | xargs -r rm -rf
```

Rollback: trỏ `current` về release trước bằng đúng hai lệnh `ln -s` + `mv -T`, rồi reload FPM.

⚠️ Process PHP sống lâu (queue worker, Horizon, Octane, scheduler) không phải FPM: chúng đã nạp code cũ
vào bộ nhớ và **không** bị reload FPM ảnh hưởng. Phải khởi động lại chúng riêng
([chương 29](29-laravel-queue-event-schedule-cache.md), [chương 30](30-laravel-testing-octane-deploy.md)).

### 11.7 Checklist "deploy xong mà vẫn chạy code cũ"

| Nghi phạm | Kiểm tra |
|---|---|
| OPcache chưa được xoá (`validate_timestamps=0`, quên reload FPM, hoặc chạy `opcache_reset()` từ CLI) | `opcache_get_status()` gọi qua HTTP: `start_time` / `last_restart_time` có sau giờ deploy không |
| Symlink + key OPcache / realpath cache vẫn trỏ release cũ | `readlink -f /var/www/app/current`; so với `$_SERVER['SCRIPT_FILENAME']` và `__DIR__` in ra từ app |
| Class cũ đã preload | Có đặt `opcache.preload` không; FPM đã restart chưa |
| Queue worker, Horizon, Octane chưa khởi động lại | Thời điểm khởi động process: `ps -o lstart= -p <pid>` |
| Load balancer còn gửi tới server chưa deploy; CDN/trình duyệt cache asset cũ | Header phản hồi cho biết server nào trả; hash trong tên file asset |

## 12. Docker cho PHP-FPM

### 12.1 Image chính thức `php:*-fpm` có gì

Image `php` chính thức trên Docker Hub có các biến thể `cli`, `fpm`, `apache`, `zts`, trên nền Debian
(ví dụ `php:8.5-fpm`) hoặc Alpine (`php:8.5-fpm-alpine`). Đọc Dockerfile của biến thể `fpm`:

- `PHP_INI_DIR=/usr/local/etc/php`; file pool ở `/usr/local/etc/php-fpm.d/`.
- **Không có `php.ini`**: image chỉ chép sẵn hai file mẫu `php.ini-development` và `php.ini-production`
  vào `$PHP_INI_DIR`. Tài liệu của image "đặc biệt khuyến nghị" dùng bản production cho production.
  Không chọn bản nào thì PHP chạy với giá trị mặc định dựng sẵn trong binary.
- File `php-fpm.d/docker.conf` đặt sẵn: `error_log = /proc/self/fd/2` (global), `access.log =
  /proc/self/fd/2`, `clear_env = no`, `catch_workers_output = yes`, `decorate_workers_output = no`,
  `listen = 9000`.
- File `php-fpm.d/zz-docker.conf` đặt `daemonize = no`: FPM chạy foreground làm process chính của container.
- `STOPSIGNAL SIGQUIT`, `EXPOSE 9000`, `CMD ["php-fpm"]`.
- Script `docker-php-ext-install`, `docker-php-ext-enable`, `docker-php-ext-configure` để cài extension.

### 12.2 Dockerfile production

```dockerfile
# Giai đoạn 1: cài dependency PHP bằng Composer (không mang Composer vào image cuối)
FROM composer:2 AS vendor
WORKDIR /app
COPY composer.json composer.lock ./
RUN composer install --no-dev --no-scripts --no-autoloader --no-interaction
COPY . .
RUN composer dump-autoload --optimize --no-dev   # với Laravel, script artisan chạy sau bước này: xem chương 30

# Giai đoạn 2: image chạy thật
FROM php:8.5-fpm
RUN docker-php-ext-install pdo_mysql \
 && mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

COPY docker/php/opcache.ini "$PHP_INI_DIR/conf.d/opcache.ini"
COPY docker/php/zz-pool.conf /usr/local/etc/php-fpm.d/zz-pool.conf

WORKDIR /var/www/html
COPY --from=vendor --chown=www-data:www-data /app /var/www/html
```

`docker/php/opcache.ini`: như cấu hình production ở mục 8.8, với `opcache.validate_timestamps=0`. Trong
container, code nằm trong image và không bao giờ đổi trong suốt đời container; deploy là chạy container
mới từ image mới, OPcache tự bắt đầu trống. Không cần reload, không có bẫy symlink của mục 11.

`docker/php/zz-pool.conf` (tên bắt đầu bằng `zz-` để được đọc **sau** `www.conf` và `docker.conf`, nên
ghi đè được chúng; các file trong `php-fpm.d/` được nạp theo thứ tự tên):

```ini
[global]
process_control_timeout = 30s

[www]
pm = static
pm.max_children = 20
pm.max_requests = 1000
request_terminate_timeout = 30s
pm.status_path = /fpm-status
ping.path = /fpm-ping
```

Vì sao `pm = static` trong container: container (pod) đã được cấp một lượng RAM cố định, nên giữ số worker
cố định cho bộ nhớ dễ dự đoán và không phải fork lúc tải tăng. Muốn tăng sức chịu tải thì tăng **số
container**, không tăng số worker. `pm.max_children` tính từ memory limit của container theo mục 4.

⚠️ Trong container, bộ nhớ được tính theo *cgroup*: mỗi trang chỉ bị tính một lần cho cả container, gần
với tổng PSS (cộng thêm page cache). Vượt memory limit thì OOM killer của cgroup giết một process trong
container, thường là worker đang lớn nhất; Nginx thấy worker chết giữa chừng và trả 502.

### 12.3 Nginx ở đâu

| Cách bố trí | Kết nối | Ghi chú |
|---|---|---|
| Hai container trong cùng một Docker network (như lab mục 1.3) | TCP `php:9000` | Nginx cần thấy file tĩnh trong `public/`: mount chung volume hoặc build image Nginx có sẵn `public/` |
| Hai container trong cùng một pod Kubernetes (sidecar) | TCP `127.0.0.1:9000`, hoặc unix socket trong volume `emptyDir` dùng chung | Cách hay gặp trên Kubernetes |
| Một container chạy cả Nginx và FPM (dưới supervisord...) | Unix socket | Đơn giản nhưng phá nguyên tắc một process chính mỗi container; dừng êm khó hơn |

Nhắc lại mục 2.4: không bao giờ publish cổng 9000 ra ngoài.

### 12.4 Dừng êm: `SIGQUIT`, `process_control_timeout`, Kubernetes

Docker và Kubernetes dừng container bằng cách gửi tín hiệu dừng cho process chính, chờ một khoảng, rồi
`SIGKILL`. Tín hiệu mặc định là `SIGTERM`, mà với master FPM `SIGTERM` nghĩa là **dừng ngay** (mục 6.1).
Image chính thức sửa chuyện này bằng `STOPSIGNAL SIGQUIT` (comment trong Dockerfile: "dừng process một
cách êm"). Image tự build từ base khác phải tự khai báo.

Để dừng êm thật sự trên Kubernetes, ba con số phải khớp nhau:

```
preStop (ví dụ sleep 5)  +  process_control_timeout (30s)  <  terminationGracePeriodSeconds (mặc định 30s → đặt 45s)
```

1. Khi pod bị xoá (rolling update), Kubernetes gỡ pod khỏi danh sách endpoint của Service và đồng thời bắt
   đầu dừng container. Hai việc diễn ra song song, nên trong vài giây đầu vẫn có request được gửi tới.
   Một `preStop` hook kiểu `sleep 5` giữ FPM tiếp tục phục vụ trong lúc đó.
2. Sau `preStop`, FPM nhận `SIGQUIT`, worker chạy nốt request đang dở, chờ tối đa
   `process_control_timeout`.
3. Tất cả phải xong trước `terminationGracePeriodSeconds`, nếu không kubelet `SIGKILL` cả container.

Health check: readiness probe nên gọi `ping.path` của FPM (qua Nginx, hoặc `cgi-fcgi` như mục 5.4), không
gọi một route nặng của app.

### 12.5 Log ra stdout/stderr

Container nên ghi log ra stdout/stderr để Docker hay Kubernetes thu thập. Image chính thức đã làm sẵn:
log của FPM và access log ghi vào `/proc/self/fd/2` (stderr của master). Comment trong Dockerfile giải
thích vì sao không dùng stdout: php-fpm đóng STDOUT lúc khởi động. `catch_workers_output = yes` đưa
những gì worker ghi ra stderr về log của master.

Cho lỗi PHP: đặt `error_log` trỏ tới stderr (ví dụ `php_admin_value[error_log] = /proc/self/fd/2` trong
pool) hoặc để Laravel ghi log qua channel `stderr`, thay vì ghi file trong container (file mất khi
container bị xoá).

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Để `pm.max_children = 5` của file mẫu trên production | Chỉ 5 request PHP chạy cùng lúc, còn lại xếp hàng | Tính theo RAM và đo thật (mục 4) |
| Chia RAM cho `memory_limit` để ra `max_children` | `memory_limit` là trần, không phải mức dùng | Đo USS/PSS lúc tải thật (mục 4.2, 4.3) |
| Tăng `max_children` khi 502/504 mà DB đang chậm | Thêm worker là thêm query dồn vào DB | Chẩn đoán worker đang chờ gì trước (mục 7.9) |
| Tin `max_execution_time` sẽ chặn request treo vì chờ API | Trên Linux (bản NTS) nó đo thời gian CPU | Timeout cho từng lời gọi ra ngoài + `request_terminate_timeout` (mục 5.1, 5.2) |
| `fastcgi_read_timeout` nhỏ hơn timeout phía PHP | Nginx trả 504 trong khi worker vẫn chạy, client thử lại làm pool đầy thêm | Chuỗi timeout tầng trong hết trước (mục 7.8) |
| Reload FPM với `process_control_timeout = 0` | `SIGQUIT` gần như lập tức thành `SIGTERM`, request dở bị cắt | Đặt `process_control_timeout` (mục 6.3) |
| `systemctl restart php-fpm` khi deploy | Dừng ngay, socket biến mất, Nginx 502 | Dùng `reload` (mục 6.3) |
| `php -r 'opcache_reset();'` trong script deploy | Reset cache của CLI, không phải của FPM | Reload FPM, hoặc gọi reset bên trong FPM (mục 8.6) |
| `validate_timestamps=0` mà quy trình deploy không xoá cache | Web chạy code cũ vô thời hạn | Reload FPM mỗi lần deploy (mục 8.3, 11.5) |
| Đổi symlink `current` rồi thôi | Key OPcache và realpath cache còn trỏ release cũ | `$realpath_root` + reload FPM (mục 11.4, 11.5) |
| `location ~ \.php$` chạy mọi file PHP | File upload giả ảnh có thể bị thực thi | Chỉ cho chạy `index.php`, giữ `security.limit_extensions` (mục 7.4) |
| Publish cổng 9000 của FPM ra ngoài | Ai nói được FastCGI là chạy được code tuỳ ý | Unix socket, hoặc TCP nội bộ + `listen.allowed_clients` (mục 2.4) |
| Mang `opcache.jit_buffer_size=128M` lên PHP 8.4 và tưởng JIT đang chạy | Từ 8.4 phải đặt `opcache.jit` | Đặt `opcache.jit=tracing`, kiểm tra `opcache_get_status()['jit']['on']` (mục 10) |
| Container FPM tự build dừng bằng `SIGTERM` | FPM dừng ngay, rớt request khi rolling update | `STOPSIGNAL SIGQUIT`, `preStop`, grace period đủ dài (mục 12.4) |
| `getenv()` trả `false` dù đã export biến môi trường | `clear_env = yes` | `env[...]` hoặc `clear_env = no` (mục 2.6) |
| Nhìn `listen queue = 0` trên pool unix socket và kết luận không có hàng đợi | Trên Linux FPM chỉ đo được với TCP | Nhìn `active`/`idle` và error log của Nginx (mục 5.4) |

## Tóm tắt chương

- Production ghép ba mảnh: Nginx (kết nối, file tĩnh, buffer), PHP-FPM (master quản lý, worker chạy
  code, mỗi worker một request), OPcache (opcode trong shared memory dùng chung các worker).
- Số request PHP đồng thời của một pool bằng số worker. Request dư xếp hàng trong listen queue của
  kernel; hàng đầy thì Nginx báo lỗi (502 với unix socket).
- `static` cho server/container dành riêng, `dynamic` co giãn theo số worker rảnh (fork mỗi giây tối đa
  `min_spare - idle`), `ondemand` cho pool ít traffic. `pm.max_requests` chống rò rỉ trong thư viện C.
- `pm.max_children` tính từ RAM còn lại chia cho bộ nhớ thật mỗi worker (USS/PSS, không phải RSS hay
  `memory_limit`), rồi kiểm chéo CPU, định luật Little và số connection DB.
- `max_execution_time` trên Linux đo CPU; `request_terminate_timeout` giết worker theo thời gian thực;
  `fastcgi_read_timeout` làm Nginx trả 504 nhưng worker vẫn chạy. Tầng trong cùng phải hết giờ trước.
- Slow log cho biết request chậm đang chờ gì; status page cho biết pool bão hoà chưa; access log của FPM
  cho biết endpoint nào tốn thời gian, CPU, bộ nhớ.
- `SIGUSR2` reload êm, `SIGQUIT` dừng êm, `SIGTERM` dừng ngay; `process_control_timeout` mặc định 0 làm
  reload cắt request dở.
- Nginx: chỉ chuyển `index.php` cho FPM, tự đặt `SCRIPT_FILENAME` (dùng `$realpath_root`), hiểu
  502 là không nói chuyện được với FPM và 504 là chờ quá lâu.
- OPcache production: `validate_timestamps=0`, đủ `memory_consumption`, `max_accelerated_files`,
  `interned_strings_buffer`; theo dõi `cache_full` và số lần restart; xoá cache bằng reload FPM.
  Preloading cần restart khi deploy; JIT từ 8.4 bật bằng `opcache.jit` và chỉ đáng bật khi đo thấy lợi.
- Deploy không downtime: release mới trong thư mục riêng, đổi symlink nguyên tử, `$realpath_root`, reload
  FPM. Trong container: image bất biến, `pm = static`, dừng bằng `SIGQUIT`, log ra stderr.

## Câu hỏi tự kiểm tra

1. Master process của FPM làm những việc gì và không làm việc gì? Vì sao code PHP không chạy bằng quyền
   root dù master chạy bằng root?
2. Pool có 10 worker, mỗi request mất 200 ms. Nếu 80 request tới cùng lúc, request cuối chờ khoảng bao
   lâu? Nó chờ ở đâu? (mục 2.5)
3. Với `pm = dynamic`, `min_spare_servers = 2`, vì sao pool tăng worker rất chậm khi traffic tăng vọt,
   dù `pm.max_spawn_rate = 32`? (mục 3.2)
4. Vì sao cộng RSS của mọi worker lại ra con số lớn hơn RAM thật đang dùng? PSS và USS khác nhau ra sao?
5. Một request chờ API ngoài 2 phút mà không bị `max_execution_time = 30` cắt. Giải thích, và nêu hai
   tầng nên dùng để chặn nó.
6. Nginx trả 504, nhưng log của API đối tác cho thấy request từ server bạn vẫn tới thêm 40 giây sau đó.
   Chuyện gì đang xảy ra ở worker?
7. Mô tả từng bước điều xảy ra khi master FPM nhận `SIGUSR2`. Trong lúc đó request mới tới thì sao?
   (mục 6.2)
8. Vì sao `location ~ \.php$` nguy hiểm hơn `location ~ ^/index\.php(/|$)`? Kể ba lớp bảo vệ khác.
9. Cache OPcache đã đầy nhưng `oom_restarts` vẫn là 0. App sẽ hành xử thế nào? (mục 8.4)
10. Sau khi đổi symlink `current` và chưa reload FPM, vì sao `$realpath_root` giúp code mới chạy ngay,
    và vì sao vẫn nên reload? (mục 11.4, 11.5)

## Bài tập

1. **Lab đo pool.** Dựng lab ở mục 1.3. Thêm file `public/slow.php` gọi `sleep(3)`, đổi Nginx cho phép
   chạy file này, đặt pool `pm = static`, `pm.max_children = 2` (file cấu hình riêng trong
   `/usr/local/etc/php-fpm.d/`). Bắn 6 request song song (`for i in $(seq 6); do curl -s -o /dev/null
   -w '%{time_total}\n' localhost:8080/slow.php & done; wait`). Giải thích thời gian từng request. Đổi
   sang 6 worker và đo lại.
2. **Status page và slow log.** Trong lab, bật `pm.status_path`, `request_slowlog_timeout = 1s`, cấu hình
   Nginx cho `/fpm-status` chỉ nhận từ mạng nội bộ của Docker. Vừa chạy bài 1 vừa đọc `?json&full`. Slow
   log có ghi được không? Nếu gặp lỗi `ptrace`, sửa bằng `cap_add` và giải thích vì sao.
3. **Trang sức khoẻ OPcache.** Viết `public/ops/opcache.php` in các chỉ số ở mục 8.5 dưới dạng JSON, chỉ
   trả lời khi header `X-Ops-Token` khớp một biến môi trường (nhớ `clear_env`). Bật
   `opcache.validate_timestamps=0`, sửa một file PHP, chứng minh bằng output rằng code cũ vẫn chạy, rồi
   đưa ra hai cách làm code mới có hiệu lực.
4. **Deploy bằng symlink.** Trên lab, mô phỏng hai release (`releases/v1`, `releases/v2`, mỗi bản
   `index.php` in số phiên bản), `current` là symlink, Nginx `root` trỏ qua `current`. Đổi symlink bằng
   `mv -T`, gọi `curl` liên tục, ghi lại phiên bản trả về trong hai trường hợp: `SCRIPT_FILENAME` dùng
   `$document_root` và dùng `$realpath_root` (với `validate_timestamps=0`). Giải thích kết quả.

## Đọc thêm

- [PHP Manual: FastCGI Process Manager (FPM)](https://www.php.net/manual/en/install.fpm.php) và
  [FPM Configuration](https://www.php.net/manual/en/install.fpm.configuration.php)
- [PHP Manual: FPM Status Page](https://www.php.net/manual/en/fpm.status.php)
- [php-src: `www.conf.in`](https://github.com/php/php-src/blob/PHP-8.5/sapi/fpm/www.conf.in),
  [`php-fpm.conf.in`](https://github.com/php/php-src/blob/PHP-8.5/sapi/fpm/php-fpm.conf.in),
  [`php-fpm.8.in`](https://github.com/php/php-src/blob/PHP-8.5/sapi/fpm/php-fpm.8.in) (signal),
  [`fpm_process_ctl.c`](https://github.com/php/php-src/blob/PHP-8.5/sapi/fpm/fpm/fpm_process_ctl.c),
  [`fpm_sockets.c`](https://github.com/php/php-src/blob/PHP-8.5/sapi/fpm/fpm/fpm_sockets.c)
- [PHP Manual: `set_time_limit`](https://www.php.net/manual/en/function.set-time-limit.php),
  [`max_execution_time`](https://www.php.net/manual/en/info.configuration.php),
  [`fastcgi_finish_request`](https://www.php.net/manual/en/function.fastcgi-finish-request.php)
- [PHP Manual: Built-in web server](https://www.php.net/manual/en/features.commandline.webserver.php),
  [Nginx trên Unix](https://www.php.net/manual/en/install.unix.nginx.php)
- [PHP Manual: OPcache runtime configuration](https://www.php.net/manual/en/opcache.configuration.php),
  [Preloading](https://www.php.net/manual/en/opcache.preloading.php),
  [`opcache_reset`](https://www.php.net/manual/en/function.opcache-reset.php),
  [`opcache_invalidate`](https://www.php.net/manual/en/function.opcache-invalidate.php),
  [`opcache_get_status`](https://www.php.net/manual/en/function.opcache-get-status.php)
- [php-src: `ext/opcache/ZendAccelerator.c`](https://github.com/php/php-src/blob/PHP-8.5/ext/opcache/ZendAccelerator.c)
- php-src UPGRADING [8.4](https://github.com/php/php-src/blob/PHP-8.4/UPGRADING) (JIT),
  [8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) (OPcache bắt buộc, `file_cache_read_only`)
- [RFC: Preloading](https://wiki.php.net/rfc/preload), [RFC: JIT](https://wiki.php.net/rfc/jit)
- [Nginx: ngx_http_fastcgi_module](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html),
  [ngx_http_core_module](https://nginx.org/en/docs/http/ngx_http_core_module.html) (`try_files`,
  `$realpath_root`, `client_max_body_size`)
- [Laravel 13: Deployment](https://laravel.com/docs/13.x/deployment)
- [docker-library/php](https://github.com/docker-library/php) (Dockerfile của image chính thức) và
  [tài liệu image `php`](https://hub.docker.com/_/php)
