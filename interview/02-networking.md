# 02. Mạng: TCP, DNS, HTTP, TLS, proxy, load balancer

> [← Mục lục](README.md) · Phạm vi: các tầng mạng, TCP/UDP, DNS, HTTP/1.1–3, TLS, realtime,
> Nginx và reverse proxy, load balancer, CDN, timeout, mạng trong cloud/container.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Tầng và TCP/UDP**
- [ ] 🟢 TCP/IP 4 tầng, OSI 7 tầng ở mức đại ý
- [ ] 🟢 TCP và UDP, ví dụ ứng dụng
- [ ] 🟢 3-way handshake, vì sao 3 bước
- [ ] 🟡 4-way close, `TIME_WAIT`, `CLOSE_WAIT`
- [ ] 🟡 Keep-alive (HTTP và TCP), connection pooling
- [ ] 🔴 Nagle, delayed ACK, `TCP_NODELAY`
- [ ] 🔴 Flow control (sliding window), congestion control (slow start, CUBIC, BBR)
- [ ] 🔴 Port exhaustion phía client, SYN backlog
- [ ] 🟡 MTU, fragmentation ở mức biết tên

**DNS**
- [ ] 🟢 Quá trình phân giải: stub, recursive resolver, root, TLD, authoritative
- [ ] 🟢 Record: `A`, `AAAA`, `CNAME`, `MX`, `TXT`, `NS`, `SOA`, `SRV`, `CAA`, `PTR`
- [ ] 🟢 TTL; ⚠️ đổi DNS không có hiệu lực ngay
- [ ] 🟡 Negative caching
- [ ] 🟡 DNS làm load balancing, GeoDNS, failover
- [ ] 🔴 DNS cache trong app/JVM, `ndots` trong Kubernetes
- [ ] 🟡 CNAME ở apex, ALIAS

**HTTP**
- [ ] 🟢 Cấu trúc request/response, method, status code
- [ ] 🟢 Header quan trọng
- [ ] 🟢 HTTP stateless; cookie và session
- [ ] 🟢 Cookie attributes: `HttpOnly`, `Secure`, `SameSite`, `Domain`, `Path`, `Expires`/`Max-Age`
- [ ] 🟡 HTTP/1.1, HTTP/2, HTTP/3/QUIC; head-of-line blocking
- [ ] 🟡 HTTP caching: `Cache-Control`, `ETag`, `Last-Modified`, `Vary`, `304`
- [ ] 🟡 Compression, range request, chunked transfer
- [ ] 🟡 CORS ở mức cơ chế (chi tiết ở [10-security.md](10-security.md))

**TLS**
- [ ] 🟢 HTTPS bảo vệ gì
- [ ] 🟡 TLS 1.2 và 1.3 handshake, 0-RTT
- [ ] 🟢 Certificate, CA, chain of trust, self-signed
- [ ] 🟡 SNI, mTLS, HSTS, OCSP stapling
- [ ] 🟡 TLS termination ở đâu

**Realtime**
- [ ] 🟢 Polling, long polling, SSE, WebSocket
- [ ] 🔴 Scale WebSocket qua nhiều node: sticky, pub/sub fan-out, reconnect storm

**Proxy, Nginx, load balancer, CDN**
- [ ] 🟢 Forward proxy và reverse proxy
- [ ] 🟡 Nginx: upstream, timeout, buffer, rate limit, keepalive tới upstream
- [ ] 🟡 Nginx + PHP-FPM (FastCGI)
- [ ] 🟡 `X-Forwarded-For`, trusted proxy
- [ ] 🟢 Load balancer L4 và L7
- [ ] 🟡 Thuật toán cân bằng tải, health check, connection draining
- [ ] 🟢 CDN
- [ ] 🔴 Anycast

**Timeout**
- [ ] 🟡 Connect, read, write, idle timeout; timeout budget
- [ ] 🟡 502, 503, 504, 499 giữa proxy và app

**Mạng cloud/container**
- [ ] 🟢 NAT, IP private/public, CIDR
- [ ] 🟡 VPC, subnet public/private, NAT gateway, security group vs NACL
- [ ] 🟡 Service discovery cơ bản

**Câu kinh điển**
- [ ] 🟢 Gõ URL rồi Enter: chuyện gì xảy ra

## Chi tiết

### Tầng mạng và TCP/UDP

- [ ] TCP/IP và OSI 🟢

| TCP/IP | OSI tương ứng | Việc | Ví dụ |
|---|---|---|---|
| Application | 7, 6, 5 | giao thức ứng dụng | HTTP, DNS, SMTP, TLS (thường xếp ở đây) |
| Transport | 4 | kết nối giữa process, port | TCP, UDP, QUIC (chạy trên UDP) |
| Internet | 3 | định tuyến giữa máy, IP | IP, ICMP |
| Link | 2, 1 | truyền trong một mạng vật lý | Ethernet, Wi-Fi, ARP |

- [ ] TCP và UDP 🟢
  - TCP: có kết nối, đảm bảo thứ tự, gửi lại gói mất, flow control, congestion control. Là
    byte stream, không có ranh giới message → app phải tự đóng khung (length prefix, delimiter)
  - UDP: không kết nối, không đảm bảo thứ tự hay tới nơi, ít overhead. Dùng cho DNS, VoIP,
    video, game, QUIC
  - ⚠️ "UDP nhanh hơn" không hẳn: nhanh vì không chờ gửi lại; muốn tin cậy thì app tự làm
- [ ] 3-way handshake 🟢
  - Client `SYN(seq=x)` → server `SYN-ACK(seq=y, ack=x+1)` → client `ACK(ack=y+1)`
  - Vì sao 3: hai bên đều phải gửi sequence number ban đầu của mình và nhận xác nhận. 2 bước thì
    server không biết client đã nhận seq của nó; SYN cũ lạc đường có thể mở kết nối ma
  - Chi phí: 1 RTT trước khi gửi dữ liệu → lý do connection reuse quan trọng
- [ ] 4-way close, `TIME_WAIT`, `CLOSE_WAIT` 🟡
  - Bên đóng trước gửi `FIN`, bên kia `ACK`, rồi gửi `FIN` của nó, bên đầu `ACK`. Bốn bước vì
    mỗi chiều đóng độc lập (half-close)
  - Bên đóng trước vào `TIME_WAIT`, chờ 2×MSL (Linux cố định 60 giây) để gói trễ không lẫn vào
    kết nối mới cùng 4-tuple, và để gửi lại ACK cuối nếu bị mất
  - Nhiều `TIME_WAIT` ở phía nào đóng trước. Server có nhiều khi client không dùng keep-alive
    hoặc server chủ động đóng
  - ⚠️ Nhiều `CLOSE_WAIT`: bên kia đã đóng mà app mình chưa `close()` → bug trong app (leak
    connection), không phải chuyện tuning kernel
  - ⚠️ `tcp_tw_recycle` gây lỗi sau NAT và đã bị bỏ khỏi kernel (4.12); `tcp_tw_reuse` chỉ áp
    dụng cho kết nối đi ra
- [ ] Keep-alive 🟡
  - HTTP keep-alive: tái dùng một kết nối TCP cho nhiều request, bỏ chi phí handshake TCP + TLS
  - TCP keepalive (`SO_KEEPALIVE`): gửi probe khi kết nối rảnh để phát hiện kết nối chết và giữ
    NAT/firewall không xoá mapping. Hai khái niệm khác nhau
  - Connection pool trong app (HTTP client, DB) là hệ quả trực tiếp. ⚠️ Tạo HTTP client mới mỗi
    request = mất keep-alive, tốn handshake, dễ port exhaustion
- [ ] Nagle và delayed ACK 🔴
  - Nagle gom các gói nhỏ khi còn dữ liệu chưa được ACK. Delayed ACK trì hoãn ACK để gộp.
    Hai cái gặp nhau với mô hình write-write-read → trễ cỡ vài chục ms (kiểm tra lại theo OS)
  - `TCP_NODELAY` tắt Nagle; nhiều runtime bật sẵn (Go mặc định bật `TCP_NODELAY`)
- [ ] Flow control và congestion control 🔴
  - Flow control: receiver quảng bá receive window để sender không gửi quá khả năng đọc
  - Congestion control: sender tự giới hạn theo ước lượng tắc nghẽn mạng. Slow start tăng
    congestion window theo cấp số nhân tới khi mất gói, sau đó tăng chậm. Linux mặc định CUBIC;
    BBR dựa trên đo bandwidth và RTT
  - Hệ quả thực tế: kết nối mới chưa đạt tốc độ tối đa ngay → thêm lý do tái dùng kết nối;
    bandwidth-delay product lớn (xuyên lục địa) cần window lớn
- [ ] Port exhaustion và backlog 🔴
  - Mỗi kết nối xác định bằng 4-tuple (src IP, src port, dst IP, dst port). Client gọi cùng một
    đích chỉ có dải ephemeral port (Linux mặc định 32768–60999, khoảng 28 nghìn port)
  - Không keep-alive + `TIME_WAIT` 60 giây → tối đa khoảng 470 kết nối mới/giây tới một đích
    trước khi hết port. Hay gặp: app gọi API nội bộ, proxy gọi upstream, NAT gateway
  - Cách xử lý: keep-alive/pool; thêm IP đích hoặc IP nguồn; mở rộng `ip_local_port_range`
  - SYN backlog và accept queue (`somaxconn`, backlog của `listen()`): đầy thì kết nối mới bị
    drop → client thấy connect timeout dù server "còn sống"

### DNS

- [ ] Quá trình phân giải 🟢
  - App → stub resolver của OS (đọc `/etc/hosts`, `/etc/resolv.conf`) → recursive resolver
    (của ISP, cloud, `8.8.8.8`, `1.1.1.1`) → hỏi root → TLD (`.com`) → authoritative server của
    domain → trả kết quả, cache theo TTL ở mọi tầng
  - Trình duyệt, OS có cache riêng. DNS dùng UDP 53, chuyển TCP khi response lớn; DoH/DoT mã hoá
- [ ] Record types 🟢

| Record | Dùng cho |
|---|---|
| `A` / `AAAA` | tên → IPv4 / IPv6 |
| `CNAME` | tên này là bí danh của tên khác |
| `MX` | mail server của domain |
| `TXT` | xác minh domain, SPF, DKIM, DMARC |
| `NS` | nameserver authoritative của zone |
| `SOA` | thông tin zone, gồm TTL cho negative caching |
| `SRV` | host + port cho service (dùng trong service discovery) |
| `CAA` | CA nào được phép cấp cert cho domain |
| `PTR` | IP → tên (reverse DNS, quan trọng cho mail server) |

  - ⚠️ Không đặt `CNAME` ở apex (`example.com`) cùng các record khác → nhà cung cấp DNS có
    `ALIAS`/`ANAME`, Route 53 có alias record
- [ ] TTL 🟢
  - Thời gian resolver được cache câu trả lời
  - ⚠️ Đổi IP không có hiệu lực ngay. Kế hoạch migration: hạ TTL xuống thấp trước ít nhất một
    TTL cũ, đổi record, giữ hệ thống cũ chạy thêm một thời gian, rồi nâng TTL lại
  - Một số resolver/client không tôn trọng TTL → luôn chờ lâu hơn TTL trước khi tắt máy cũ
- [ ] Negative caching 🟡
  - Câu trả lời "không tồn tại" (NXDOMAIN) cũng được cache, theo giá trị từ `SOA` (RFC 2308)
  - ⚠️ Truy vấn một tên trước khi tạo record → resolver nhớ "không có" một thời gian, tạo record
    xong vẫn lỗi. Hay gặp khi tự động tạo subdomain rồi gọi ngay
- [ ] DNS làm load balancing 🟡
  - Nhiều `A` record cho một tên (round robin), GeoDNS trả IP gần người dùng, weighted,
    failover theo health check (Route 53 routing policies)
  - Hạn chế: client cache, không biết tải thật, chuyển đổi chậm theo TTL. Thường dùng ở tầng
    toàn cầu, còn trong một region dùng load balancer
- [ ] DNS cache trong app 🔴
  - JVM cache kết quả DNS trong process: `networkaddress.cache.ttl` (mặc định 30 giây khi không
    có security manager; có security manager thì cache vĩnh viễn), negative cache mặc định 10
    giây (kiểm tra lại theo phiên bản JDK)
  - ⚠️ Kết nối đã mở không phân giải lại: pool connection sống lâu vẫn trỏ IP cũ sau khi DB
    failover hoặc LB đổi IP → cần giới hạn thời gian sống của connection
  - Go resolver thuần không cache trong process; Node `dns.lookup` gọi `getaddrinfo` trên
    threadpool, không cache; PHP phụ thuộc OS. glibc không cache, trừ khi có `nscd`,
    `systemd-resolved`, dnsmasq
  - Không cache + gọi nhiều → mỗi request một truy vấn DNS, DNS server là bottleneck ẩn
  - Kubernetes: `resolv.conf` có `ndots:5` và nhiều `search` domain → tên ngoài như
    `api.stripe.com` có thể bị thử với từng search domain trước → nhiều truy vấn thừa. Dùng FQDN
    có dấu chấm cuối hoặc hạ `ndots`

### HTTP

- [ ] Request/response và status code 🟢
  - Request: method, path, version, header, body. Response: status, header, body
  - Method: `GET`, `HEAD` (an toàn), `PUT`, `DELETE` (idempotent), `POST`, `PATCH` (không
    idempotent theo mặc định). Chi tiết thiết kế API: [09-api-design.md](09-api-design.md)
  - Status: `2xx` thành công, `3xx` chuyển hướng (`301` vĩnh viễn và được cache, `302`/`307`
    tạm, `304` dùng cache), `4xx` lỗi client, `5xx` lỗi server
- [ ] Header quan trọng 🟢
  - `Host`, `Content-Type`, `Content-Length`, `Accept`, `Accept-Encoding`, `Authorization`,
    `Cookie`/`Set-Cookie`, `Cache-Control`, `ETag`, `If-None-Match`, `Location`, `User-Agent`,
    `X-Forwarded-For`/`Forwarded`, `X-Request-Id` (correlation id), `Retry-After`,
    `Idempotency-Key`
  - Security header: `Strict-Transport-Security`, `Content-Security-Policy`, `nosniff`
- [ ] HTTP stateless, cookie và session 🟢
  - Server không nhớ request trước; "nhớ" đăng nhập nhờ client gửi lại thứ gì đó mỗi request:
    cookie chứa session id (state ở server: Redis, DB) hoặc token (JWT, state trong token)
- [ ] Cookie attributes 🟢
  - `HttpOnly`: JavaScript không đọc được (giảm thiệt hại XSS). `Secure`: chỉ gửi qua HTTPS
  - `SameSite=Strict|Lax|None`: kiểm soát gửi cookie trong request cross-site (chống CSRF).
    Chrome coi mặc định là `Lax`; `None` bắt buộc đi kèm `Secure`
  - `Domain`: không đặt thì chỉ host hiện tại; đặt `example.com` thì cả subdomain. `Path`
  - `Expires`/`Max-Age`: không có là session cookie, mất khi đóng trình duyệt
  - ⚠️ Cookie đặt `Domain=example.com` bị gửi tới mọi subdomain, kể cả subdomain ít tin cậy
- [ ] HTTP/1.1, HTTP/2, HTTP/3 🟡

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Transport | TCP | TCP (thực tế luôn có TLS) | QUIC trên UDP |
| Định dạng | text | binary frame | binary frame |
| Nhiều request | tuần tự trên một kết nối; trình duyệt mở ~6 kết nối/host | multiplex nhiều stream trên 1 kết nối | multiplex, stream độc lập |
| Nén header | không | HPACK | QPACK |
| HOL blocking | ở tầng HTTP | hết ở HTTP, còn ở TCP (mất 1 gói chặn mọi stream) | không còn ở transport |
| Handshake | TCP + TLS | TCP + TLS | gộp, 1-RTT, có 0-RTT |

  - Domain sharding, gộp file là mẹo thời HTTP/1.1, phản tác dụng với HTTP/2
  - QUIC: connection id giúp kết nối sống qua việc đổi mạng (Wi-Fi sang 4G)
  - ⚠️ HTTP/2 giữa client và CDN/LB không có nghĩa là LB nói HTTP/2 với backend; thường là
    HTTP/1.1 phía sau. gRPC cần HTTP/2 đầu cuối (hoặc proxy hiểu gRPC)
  - ⚠️ HTTP/3 bị chặn khi mạng chặn UDP; trình duyệt tự lùi về HTTP/2
- [ ] HTTP caching 🟡
  - `Cache-Control: max-age=N` (trình duyệt), `s-maxage` (shared cache như CDN), `public`,
    `private` (chỉ trình duyệt, không cho CDN cache), `immutable`
  - ⚠️ `no-cache` = được lưu nhưng phải revalidate trước khi dùng. `no-store` = không được lưu.
    Hai cái hay bị nhầm
  - Revalidate: server gửi `ETag` (hoặc `Last-Modified`); client gửi `If-None-Match`
    (`If-Modified-Since`); không đổi thì `304 Not Modified` không body
  - `Vary: Accept-Encoding, Accept-Language`: cache phải tách bản theo header này.
    ⚠️ Thiếu `Vary` → CDN trả bản gzip cho client không hỗ trợ, hoặc trả nội dung của user A
    cho user B nếu nội dung phụ thuộc `Cookie`/`Authorization`
  - Static asset có hash trong tên file → `max-age` dài + `immutable`; HTML → ngắn hoặc revalidate
  - Chi tiết chiến lược cache: [11-cache.md](11-cache.md)
- [ ] Compression, range, chunked 🟡
  - `Accept-Encoding: gzip, br` → server trả `Content-Encoding`. Nén text/JSON, không nén lại
    ảnh/video đã nén. ⚠️ Nén + dữ liệu bí mật phản chiếu input người dùng → rủi ro kiểu BREACH
  - Range request: `Range: bytes=0-1023` → `206 Partial Content`; dùng cho resume download,
    video seek, tải song song. Server báo hỗ trợ bằng `Accept-Ranges: bytes`
  - `Transfer-Encoding: chunked` (HTTP/1.1): gửi body khi chưa biết độ dài, dùng cho streaming.
    HTTP/2/3 không dùng chunked, dùng frame
  - ⚠️ Proxy buffer toàn bộ response → streaming/SSE không tới client ngay (Nginx
    `proxy_buffering`)

### TLS

- [ ] HTTPS bảo vệ gì 🟢
  - Mã hoá (người giữa không đọc được), toàn vẹn (không sửa được), xác thực server (đúng là
    `bank.com`). Không che được IP đích, và SNI thường lộ tên domain
- [ ] Handshake 🟡
  - Ý chung: dùng mật mã bất đối xứng/trao đổi khoá (ECDHE) để thống nhất khoá phiên, rồi mã hoá
    dữ liệu bằng mật mã đối xứng (AES-GCM, ChaCha20) vì nhanh hơn nhiều
  - TLS 1.2: 2 RTT. ClientHello → ServerHello + Certificate + key exchange → client key
    exchange + Finished → Finished
  - TLS 1.3: 1 RTT. Client gửi luôn key share trong ClientHello; bỏ các cipher yếu, bắt buộc
    forward secrecy; phần lớn handshake được mã hoá
  - 0-RTT (session resumption của 1.3): gửi dữ liệu ngay trong gói đầu. ⚠️ Dữ liệu 0-RTT có thể
    bị replay → chỉ cho request idempotent
  - Forward secrecy: lộ private key của server sau này không giải mã được traffic cũ đã ghi lại
- [ ] Certificate và chain of trust 🟢
  - Cert chứa domain, public key, hạn dùng, chữ ký của CA. Trình duyệt tin một tập root CA;
    server gửi leaf + intermediate, client dựng chuỗi tới root
  - ⚠️ Server quên gửi intermediate → trình duyệt có thể vẫn chạy (đã cache), nhưng `curl`,
    app mobile, Java client lỗi. Kiểm tra bằng `openssl s_client -connect host:443 -showcerts`
  - Self-signed không được root nào ký → cảnh báo. Nội bộ dùng CA riêng và phân phối root
  - Cert ngày càng có hạn ngắn → gia hạn tự động (ACME/Let's Encrypt, cert-manager, ACM).
    ⚠️ Cert hết hạn vẫn là nguyên nhân outage phổ biến → alert trước khi hết hạn
- [ ] SNI, mTLS, HSTS, OCSP 🟡
  - SNI: client gửi tên host trong ClientHello để một IP phục vụ nhiều cert. ECH (Encrypted
    Client Hello) đang được triển khai để giấu tên này
  - mTLS: client cũng trình cert → server xác thực client. Dùng giữa service (service mesh),
    API B2B, thiết bị IoT
  - HSTS: `Strict-Transport-Security: max-age=...; includeSubDomains` → trình duyệt chỉ dùng
    HTTPS cho domain. ⚠️ Bật `includeSubDomains`/preload khi còn subdomain chỉ chạy HTTP là
    subdomain đó chết; preload khó gỡ
  - OCSP stapling: server đính kèm trạng thái thu hồi cert, client không phải tự hỏi CA
- [ ] TLS termination ở đâu 🟡
  - Ở LB/CDN/ingress: tập trung quản lý cert, giảm tải backend, LB đọc được HTTP để route L7.
    Traffic từ LB tới backend là plaintext trong mạng nội bộ
  - Re-encrypt tới backend hoặc mTLS nội bộ khi yêu cầu compliance hoặc zero-trust
  - TLS passthrough (LB L4): backend giữ cert, LB không đọc được HTTP
  - ⚠️ Terminate ở LB thì app thấy request là `http` → phải tin `X-Forwarded-Proto` từ proxy
    tin cậy, nếu không redirect loop hoặc sinh URL `http://`

### Realtime

- [ ] Các lựa chọn 🟢

| | Cơ chế | Hướng | Ưu | Nhược |
|---|---|---|---|---|
| Polling | client hỏi mỗi N giây | client → server | đơn giản, stateless | trễ, tốn request rỗng |
| Long polling | server giữ request tới khi có dữ liệu hoặc timeout | gần như server → client | chạy mọi nơi | giữ connection, phức tạp timeout |
| SSE | 1 response HTTP dài, `text/event-stream` | server → client | tự reconnect, `Last-Event-ID`, qua proxy HTTP dễ | một chiều, text; HTTP/1.1 bị giới hạn số kết nối/host |
| WebSocket | nâng cấp HTTP (`101 Switching Protocols`) thành kênh hai chiều | hai chiều | độ trễ thấp, hai chiều | stateful, cần cấu hình proxy, tự làm reconnect/heartbeat |

  - Chọn: thông báo, feed, tiến trình job, stream token từ LLM → SSE thường đủ. Chat, game,
    collaborative editing → WebSocket. Tần suất thấp → polling vẫn ổn
- [ ] Scale WebSocket 🔴
  - Mỗi kết nối gắn với một node. Gửi tin cho user X phải biết X đang ở node nào → pub/sub
    (Redis Pub/Sub, NATS, Kafka): node nào nhận event thì publish, mọi node subscribe và đẩy
    cho client của mình; hoặc registry user → node
  - Sticky session chỉ cần khi handshake nhiều bước (Socket.IO fallback long polling); bản thân
    WebSocket đã dính một node suốt đời kết nối
  - ⚠️ LB/proxy idle timeout cắt kết nối rảnh → heartbeat ping/pong ngắn hơn idle timeout
  - ⚠️ Deploy/restart node → hàng chục nghìn client reconnect cùng lúc (thundering herd) →
    exponential backoff + jitter phía client, drain từ từ
  - ⚠️ Giới hạn: fd, RAM mỗi kết nối, port khi qua proxy; autoscale theo số kết nối chứ không
    theo CPU
  - Tin nhắn trong lúc mất kết nối: pub/sub không lưu → cần lưu và cho client lấy bù theo offset
  - Nginx phải chuyển header `Upgrade`/`Connection` và tăng `proxy_read_timeout`

### Proxy và Nginx

- [ ] Forward và reverse proxy 🟢
  - Forward proxy đứng phía client, đại diện client ra ngoài (proxy công ty, egress proxy)
  - Reverse proxy đứng phía server, đại diện server: TLS termination, routing, cache, nén,
    rate limit, che backend (Nginx, HAProxy, Envoy, Traefik)
- [ ] Nginx cấu hình mẫu 🟡

```nginx
upstream api {
    least_conn;
    server 10.0.1.10:8080 max_fails=3 fail_timeout=10s;
    server 10.0.1.11:8080 max_fails=3 fail_timeout=10s;
    keepalive 32;                          # số kết nối rảnh giữ lại mỗi worker
}
limit_req_zone $binary_remote_addr zone=perip:10m rate=10r/s;
server {
    listen 443 ssl;
    http2 on;
    location /api/ {
        limit_req zone=perip burst=20 nodelay;
        proxy_pass http://api;
        proxy_http_version 1.1;            # bắt buộc cho keepalive tới upstream
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 2s;
        proxy_read_timeout 30s;
    }
}
```

  - ⚠️ Mặc định Nginx nói HTTP/1.0 và không giữ kết nối tới upstream → mỗi request một kết nối
    mới, dễ `TIME_WAIT` và port exhaustion. Cần đủ ba dòng: `keepalive`, `proxy_http_version 1.1`,
    `Connection ""`
  - Timeout mặc định `proxy_connect_timeout`, `proxy_read_timeout` là 60 giây (kiểm tra lại):
    thường quá dài cho API, quá ngắn cho SSE/WebSocket
  - `proxy_buffering on` (mặc định): Nginx đọc nhanh response từ upstream để giải phóng upstream
    sớm, rồi tự trả chậm cho client chậm. Tắt cho SSE/streaming (hoặc app gửi
    `X-Accel-Buffering: no`)
  - `client_max_body_size` (mặc định 1 MB) → upload lớn bị `413`
  - `limit_req` (leaky bucket theo key), `limit_conn`; `burst` và `nodelay` quyết định có xếp
    hàng hay từ chối ngay. ⚠️ Rate limit theo IP sau NAT/CDN chặn nhầm cả văn phòng; sau CDN thì
    `$binary_remote_addr` là IP của CDN nếu chưa cấu hình real IP
  - Reload không downtime: `nginx -t` rồi `nginx -s reload` (SIGHUP); worker cũ làm nốt kết nối
- [ ] Nginx + PHP-FPM 🟡
  - Nginx phục vụ static, chuyển `.php` qua FastCGI (`fastcgi_pass unix:/run/php/php-fpm.sock`
    hoặc TCP `127.0.0.1:9000`)
  - Unix socket nhanh hơn chút trong cùng máy; TCP khi FPM ở container/máy khác
  - ⚠️ Phải chặn thực thi PHP trong thư mục upload, và cấu hình `try_files` đúng để không chuyển
    đường dẫn tuỳ ý cho FPM
  - Timeout phải khớp: `fastcgi_read_timeout` của Nginx, `request_terminate_timeout` của FPM,
    `max_execution_time` của PHP
- [ ] `X-Forwarded-For` và trusted proxy 🟡
  - Mỗi proxy nối IP nó thấy vào cuối: `XFF: client, proxy1, proxy2`
  - ⚠️ Client tự gửi được `X-Forwarded-For` giả. Lấy IP thật = đi từ phải sang trái, bỏ các IP
    thuộc proxy mình tin, IP đầu tiên không tin là client. Lấy phần tử đầu tiên là bị giả mạo
    được (bypass rate limit, ghi log sai, bypass allowlist IP)
  - Nginx: `set_real_ip_from <dải proxy>; real_ip_header X-Forwarded-For; real_ip_recursive on;`
  - Laravel `TrustProxies`, Spring `server.forward-headers-strategy`, Go tự xử lý: chỉ tin header
    khi request đến từ dải IP proxy đã biết

### Load balancer, CDN, anycast

- [ ] L4 và L7 🟢

| | L4 | L7 |
|---|---|---|
| Nhìn thấy | IP, port, TCP/UDP | method, path, header, cookie |
| Việc làm được | chuyển kết nối, rất nhanh, protocol bất kỳ | route theo path/host, TLS termination, retry, rewrite, WAF |
| Ví dụ | AWS NLB, LVS, HAProxy mode tcp | AWS ALB, Nginx, Envoy, HAProxy mode http |
| Cân bằng theo | kết nối | request (quan trọng với HTTP/2, gRPC) |

  - ⚠️ gRPC/HTTP/2 qua LB L4: một kết nối dài mang mọi request → dồn hết vào một backend. Cần LB
    L7 hoặc cân bằng phía client
- [ ] Thuật toán 🟡
  - Round robin, weighted round robin; least connections (hợp request thời gian khác nhau);
    IP hash / consistent hashing (dính session, cache locality); random, power of two choices
    (chọn ngẫu nhiên 2 rồi lấy cái ít tải hơn, rẻ mà hiệu quả)
  - ⚠️ Sticky session làm lệch tải và mất session khi node chết → ưu tiên app stateless, session
    ở Redis
- [ ] Health check và draining 🟡
  - Active (LB gọi `/health` định kỳ) và passive (đếm lỗi của request thật, như `max_fails`)
  - Health check nông (process sống) và sâu (kiểm tra DB). ⚠️ Health check sâu làm cả cụm bị
    đánh dấu chết khi DB chậm → không còn backend nào nhận request, kể cả request không cần DB
  - Connection draining (deregistration delay): khi gỡ backend, LB ngừng gửi request mới nhưng
    để request đang chạy xong. Phải phối hợp với graceful shutdown của app
- [ ] CDN 🟢
  - Mạng edge cache nội dung gần người dùng: giảm latency, giảm tải origin, hấp thụ DDoS
  - Cache static; cache cả API công khai với `s-maxage` ngắn; invalidation theo path hoặc dùng
    tên file có hash
  - ⚠️ Cache nhầm response có dữ liệu cá nhân (thiếu `private`, cache key không có cookie) →
    lộ dữ liệu người khác. Origin phải chặn truy cập trực tiếp nếu chỉ muốn đi qua CDN
- [ ] Anycast 🔴
  - Cùng một IP được quảng bá qua BGP từ nhiều địa điểm; định tuyến Internet tự đưa người dùng
    tới điểm gần (theo BGP) nhất
  - Dùng cho DNS công cộng (`1.1.1.1`, `8.8.8.8`), CDN, chống DDoS (traffic tấn công bị chia ra
    nhiều nơi), global load balancer của cloud
  - Hợp với UDP/kết nối ngắn; route BGP đổi giữa chừng có thể làm kết nối TCP dài bị đứt

### Timeout

- [ ] Các loại timeout 🟡
  - Connect timeout: thiết lập TCP (và TLS). Nên ngắn (vài trăm ms tới vài giây trong nội bộ)
  - Read timeout: chờ dữ liệu giữa hai lần đọc. ⚠️ Không phải tổng thời gian: server nhả từng byte
    chậm vẫn giữ được kết nối mãi → cần thêm tổng timeout/deadline cho request
  - Write timeout, idle timeout (kết nối keep-alive rảnh bao lâu thì đóng)
  - ⚠️ Mặc định nguy hiểm: `http.Client{}` của Go không có timeout; nhiều HTTP client mặc định
    chờ vô hạn → một dependency treo làm cạn thread/worker
  - Timeout budget: timeout tầng ngoài phải lớn hơn tầng trong (CDN > LB > Nginx > app > DB).
    Ngược lại thì tầng ngoài bỏ cuộc trong khi tầng trong vẫn làm, tốn tài nguyên vô ích.
    Propagate deadline qua service (Go `context`, gRPC deadline)
- [ ] Lỗi giữa proxy và app 🟡

| Mã | Ý nghĩa ở proxy | Nguyên nhân hay gặp |
|---|---|---|
| `502 Bad Gateway` | upstream trả lỗi không hợp lệ, từ chối hoặc đóng kết nối | app crash, sai port, FPM chết, keep-alive race |
| `503 Service Unavailable` | không có upstream khả dụng / quá tải | mọi backend fail health check, rate limit, bảo trì |
| `504 Gateway Timeout` | upstream không trả lời kịp | query chậm, dependency treo, hết worker |
| `499` (Nginx) | client đóng kết nối trước khi có response | client timeout ngắn hơn server |

  - ⚠️ Keep-alive race: app đóng kết nối rảnh sau 5 giây, LB giữ 60 giây → LB gửi request vào
    kết nối app vừa đóng → 502 lác đác. Quy tắc: idle timeout của app phải **lớn hơn** của LB
    phía trước. Ví dụ kinh điển: Node `server.keepAliveTimeout` mặc định 5 giây sau AWS ALB
    idle timeout mặc định 60 giây

### Mạng trong cloud và container

- [ ] NAT, IP, CIDR 🟢
  - IP private (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) không định tuyến trên Internet
  - NAT dịch private ↔ public; nhiều máy ra Internet chung một IP public
  - CIDR: `10.0.0.0/16` có 65.536 địa chỉ, `/24` có 256. AWS giữ lại 5 địa chỉ mỗi subnet
  - ⚠️ Chọn CIDR VPC trùng với mạng văn phòng/VPC khác → sau này không peering/VPN được
- [ ] VPC 🟡
  - Subnet public (route ra Internet Gateway) cho LB, bastion; subnet private cho app, DB
  - Private subnet ra Internet qua NAT gateway. ⚠️ NAT gateway tính tiền theo GB xử lý; gọi S3
    qua NAT tốn tiền vô ích → dùng VPC endpoint
  - Security group: stateful, gắn vào instance/ENI, chỉ có allow, tham chiếu được security group
    khác ("app SG được vào DB SG port 5432"). NACL: stateless, theo subnet, có allow và deny
  - Chi tiết cloud: [19-devops-cloud.md](19-devops-cloud.md)
- [ ] Mạng container 🟡
  - Docker bridge: container có IP riêng trong mạng ảo, publish port bằng NAT (`-p 8080:80`).
    Trong Docker Compose, service gọi nhau bằng tên service (DNS nội bộ)
  - ⚠️ `localhost` trong container là chính container, không phải máy host
  - Kubernetes: mỗi pod một IP, pod gọi nhau trực tiếp; Service có IP ảo ổn định và tên DNS
    `svc.namespace.svc.cluster.local`
- [ ] Service discovery 🟡
  - Client-side (client hỏi registry rồi tự chọn instance: Consul, Eureka) và server-side (gọi
    LB/Service, nó chọn giúp: Kubernetes Service, AWS ALB)
  - DNS là dạng service discovery đơn giản nhất; hạn chế là TTL và cache
  - Service mesh (Istio, Linkerd): sidecar lo discovery, mTLS, retry, metrics

### Gõ URL rồi Enter: đáp án đầy đủ

Gõ `https://shop.example.com/products?id=42` rồi Enter:

1. **Trình duyệt phân tích URL**: scheme, host, port (443 mặc định), path, query. Không phải URL
   thì chuyển thành tìm kiếm. Kiểm tra HSTS: domain trong danh sách thì ép `https`
2. **Cache phía client**: service worker, HTTP cache. Có bản còn hạn thì dùng luôn, không ra mạng
3. **DNS**: cache trình duyệt → cache OS / `/etc/hosts` → recursive resolver → root → TLD `.com`
   → authoritative của `example.com` → nhận `A`/`AAAA` (có thể qua CNAME tới CDN; GeoDNS trả IP
   edge gần nhất)
4. **Kết nối**: trình duyệt có kết nối sẵn tới host (keep-alive, HTTP/2 coalescing) thì dùng lại.
   Không thì TCP 3-way handshake (1 RTT). Nếu biết server hỗ trợ HTTP/3 (qua `Alt-Svc`) thì dùng
   QUIC, gộp transport và TLS
5. **TLS**: ClientHello có SNI `shop.example.com` và ALPN (`h2`, `http/1.1`); server gửi cert
   chain; trình duyệt kiểm tra chain tới root CA, tên domain, hạn dùng, trạng thái thu hồi; thống
   nhất khoá phiên (TLS 1.3: 1 RTT)
6. **Gửi HTTP request**: `GET /products?id=42`, `Host`, `Cookie`, `Accept-Encoding`,
   `User-Agent`...
7. **Phía hạ tầng**: có thể qua CDN edge (anycast; cache hit thì trả luôn) → WAF → load balancer
   (TLS termination, chọn backend theo thuật toán và health check) → reverse proxy Nginx/ingress
   → app (PHP-FPM worker, goroutine, thread). Proxy thêm `X-Forwarded-For`, `X-Request-Id`
8. **App xử lý**: routing, middleware (auth qua session/JWT, rate limit), business logic, đọc
   cache (Redis), query DB (connection pool), có thể gọi service khác; log, metric, trace
9. **Response**: status, header (`Content-Type`, `Cache-Control`, `Set-Cookie`,
   `Content-Encoding: br`), body; đi ngược qua proxy, LB, CDN (có thể được cache)
10. **Trình duyệt render**: giải nén, parse HTML → DOM; gặp CSS → CSSOM; JS có thể chặn parse
    (trừ `async`/`defer`); tải thêm tài nguyên (lặp lại từ bước 2–9 cho mỗi cái, nhưng tái dùng
    kết nối); layout → paint → composite
11. **Sau đó**: kết nối được giữ keep-alive cho request tiếp; JS gọi API qua `fetch`; có thể mở
    WebSocket/SSE

Mẹo khi trả lời: nói khung 10 bước trong 1–2 phút, rồi hỏi người phỏng vấn muốn đào sâu phần nào
(DNS, TLS, hạ tầng backend, hay render). Backend engineer nên đào sâu bước 7–8.

## Senior trả lời khác gì

**"Có lỗi 502 lác đác, không theo quy luật."**
- Mid: xem log app, có thể app crash.
- Senior: app không có lỗi tương ứng thì nghi keep-alive race giữa LB và app (so idle timeout
  hai bên), pod bị tắt khi còn trong endpoint (thiếu preStop/draining), hoặc OOMKilled. Đối
  chiếu thời điểm 502 với deploy, restart, và log của LB.

**"Đổi IP server, cập nhật DNS xong thì sao?"**
- Mid: chờ DNS cập nhật.
- Senior: đã hạ TTL trước đó chưa; resolver và client không tôn trọng TTL; JVM và connection
  pool giữ IP cũ; negative caching nếu tạo tên mới. Giữ server cũ chạy song song, theo dõi traffic
  còn vào đó rồi mới tắt.

**"Lấy IP người dùng thế nào?"**
- Mid: đọc `X-Forwarded-For`.
- Senior: header giả được; chỉ tin khi request tới từ proxy đã biết, đọc từ phải sang trái bỏ qua
  các proxy tin cậy. Cấu hình ở một chỗ (Nginx real_ip hoặc framework trusted proxy), và nói hậu
  quả nếu sai: rate limit, audit log, allowlist IP đều bị vượt.

**"Scale hệ thống chat WebSocket lên 1 triệu kết nối."**
- Mid: thêm server, dùng load balancer.
- Senior: tính số kết nối mỗi node (fd, RAM), pub/sub fan-out giữa node, heartbeat so với idle
  timeout, reconnect storm khi deploy, lưu tin để client lấy bù, autoscale theo số kết nối, tách
  gateway kết nối khỏi logic nghiệp vụ.

## Tình huống

1. **Service A gọi service B qua HTTP, khi tải cao A báo `cannot assign requested address`.**
   - Gợi ý:
     - Hết ephemeral port: đếm `TIME_WAIT` bằng `ss`
     - A có tạo HTTP client mới mỗi request không, có đọc hết và đóng body không
     - Bật keep-alive/pool, tăng số kết nối rảnh tối đa mỗi host

2. **Sau khi chuyển sang CDN, một số người dùng thấy trang tài khoản của người khác.**
   - Gợi ý:
     - Response cá nhân bị CDN cache: thiếu `Cache-Control: private`/`no-store`, hoặc CDN bỏ
       qua cookie trong cache key
     - Xử lý: purge ngay, sửa header, cấu hình CDN không cache path động
     - Báo cáo như sự cố lộ dữ liệu

3. **Upload file 20 MB bị lỗi `413`, sửa xong lại bị `504`.**
   - Gợi ý:
     - `413`: `client_max_body_size` của Nginx (và giới hạn của PHP `upload_max_filesize`,
       `post_max_size`)
     - `504`: timeout đọc/ghi giữa proxy và app khi xử lý lâu
     - Cách tốt hơn: presigned URL để client upload thẳng lên object storage

4. **Sau khi DB failover sang primary mới, app Java vẫn lỗi kết nối 10 phút dù DNS đã đổi.**
   - Gợi ý:
     - JVM DNS cache, connection pool giữ kết nối cũ không bị đóng
     - Giới hạn `maxLifetime` của pool, validation khi mượn connection, TTL DNS của JVM
     - Kiểm tra driver có hỗ trợ failover không

5. **SSE hoạt động ở local nhưng trên staging client chỉ nhận dữ liệu sau vài chục giây, hoặc bị
   ngắt mỗi 60 giây.**
   - Gợi ý:
     - Proxy buffering (Nginx, LB) giữ response → tắt buffering cho endpoint đó
     - Ngắt đều đặn → idle/read timeout của proxy/LB; gửi comment heartbeat định kỳ
     - Nén response có thể cũng gây buffer

## ❓ Câu hỏi hay gặp

🟢
- Điều gì xảy ra khi bạn gõ `https://example.com` rồi nhấn Enter?
- TCP khác UDP thế nào? Cho ví dụ ứng dụng dùng mỗi loại.
- Vì sao HTTP là stateless? Làm sao server "nhớ" được người dùng đã đăng nhập?
- `HttpOnly`, `Secure`, `SameSite` dùng để làm gì?
- Reverse proxy là gì? Vì sao đặt Nginx trước app?

🟡
- Vì sao handshake cần 3 bước? `TIME_WAIT` là gì, vì sao server có rất nhiều?
- HTTP/2 cải thiện gì so với HTTP/1.1? Vì sao vẫn cần HTTP/3?
- `no-cache` khác `no-store` thế nào? `ETag` hoạt động ra sao?
- 502 và 504 khác nhau thế nào? Bạn điều tra mỗi loại ra sao?
- Load balancer L4 và L7 khác nhau thế nào? Khi nào chọn cái nào?
- TLS handshake đại ý diễn ra thế nào? TLS 1.3 nhanh hơn 1.2 ở đâu?
- Polling, SSE, WebSocket: chọn cái nào cho thông báo realtime?

🔴
- Scale WebSocket qua nhiều node thế nào?
- Vì sao đổi DNS rồi mà một số client vẫn gọi IP cũ?
- Làm sao lấy IP thật của client một cách an toàn?
- Đặt timeout giữa các tầng CDN, LB, proxy, app, DB theo nguyên tắc nào?
- Port exhaustion là gì, xảy ra ở đâu, xử lý thế nào?
- Health check nên kiểm tra những gì? Health check sâu có rủi ro gì?

## Bài tập tự làm

1. Dùng `curl -w` đo thời gian DNS, TCP, TLS, TTFB tới ba website ở các vị trí địa lý khác nhau.
   Giải thích vì sao các con số khác nhau, và lần gọi thứ hai khác lần đầu thế nào.
2. Viết một server HTTP nhỏ bằng Go trả response chậm, đặt sau Nginx trong Docker Compose. Tạo ra
   được lần lượt 502, 504 và 499, ghi lại cấu hình gây ra từng lỗi.
3. Viết cấu hình Nginx cho một app Laravel: static file, PHP-FPM, upload tối đa 50 MB, rate limit
   cho `/login`, real IP sau một LB có dải `10.0.0.0/16`, và một endpoint SSE không bị buffer.
4. Thiết kế header cache cho: file JS có hash trong tên, trang HTML, API công khai danh sách sản
   phẩm, API `/me`. Giải thích từng lựa chọn.
5. Vẽ sơ đồ VPC cho một app gồm LB, 3 app server, PostgreSQL, Redis; ghi rõ subnet, route,
   security group rule, và đường đi ra Internet của app server.

> Nộp bài vào đây để được review.
