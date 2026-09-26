# 02. Mạng: TCP, DNS, HTTP, TLS, proxy, load balancer

> [← Mục lục](README.md) · Trọng tâm: **mạng nhìn từ backend** (TCP, DNS, HTTP/1.1–3, TLS 1.3, Nginx + PHP-FPM, load balancer, timeout, mạng cloud/container), đối chiếu Java/Go/Node khi có ích.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn.

File gồm hai phần:

1. **Lộ trình kiến thức** (phần chính): ba chặng từ nền tới senior. Mỗi module có:
   - **Vì sao cần học**: module này dùng vào việc gì và hay bị hỏi thế nào.
   - **Học gì**: các khái niệm, giải thích bằng lời thường kèm ví dụ, và các cạm bẫy ⚠️. Đọc phần
     này để biết cần học gì, rồi học sâu qua tài liệu ở mục Đọc.
   - **Đọc**: tài liệu gốc.
   - **Nắm chắc khi**: tiêu chí tự kiểm tra. Chỉ tick ô khi làm được điều đó mà không cần nhìn
     tài liệu.
2. **Câu hỏi thường gặp** (bonus): mỗi câu kèm hướng trả lời mong đợi, gồm ý phải có, điểm
   cộng senior và red flag. Dùng để kiểm tra sau khi học, không dùng để học thuộc.

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [*High Performance Browser Networking*](https://hpbn.co/) (Ilya Grigorik) | Sách online miễn phí | TCP, TLS, HTTP/1.1, HTTP/2 dưới góc latency. Đọc các chương networking 101 và HTTP. Phần HTTP/3 chưa có |
| [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110) (HTTP Semantics), [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111) (Caching), [RFC 9112](https://www.rfc-editor.org/rfc/rfc9112) (HTTP/1.1) | RFC | Nguồn chuẩn cho method, status, header, cache. Tra cứu, không cần đọc hết |
| [MDN: HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP) | Docs | Giải thích HTTP dễ đọc nhất, có ví dụ, cập nhật theo trình duyệt |
| [Nginx docs](https://nginx.org/en/docs/) | Official docs | Proxy, upstream, FastCGI, rate limit, real IP. Mỗi directive ghi giá trị mặc định và phiên bản |
| [*Computer Networking: A Top-Down Approach*](https://gaia.cs.umass.edu/kurose_ross/) (Kurose, Ross) | Sách | Nền lý thuyết nếu chưa học mạng bài bản: chương 2 (application), 3 (transport) |
| [The Illustrated TLS 1.3 Connection](https://tls13.xargs.org/) | Tài liệu trực quan | Từng byte của một handshake TLS 1.3 thật |
| [PortSwigger Web Security Academy](https://portswigger.net/web-security) | Khoá học miễn phí | Request smuggling, các lỗi ở ranh giới proxy và app |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.5 | Hiểu TCP/UDP, DNS, HTTP, HTTPS ở mức dùng được; trả lời trôi câu "gõ URL rồi Enter" | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.8 | Cấu hình đúng Nginx, PHP-FPM, cache, timeout; đọc được 502/504 và sửa được | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.5 | TCP và DNS chuyên sâu, lỗ hổng ở ranh giới proxy, scale realtime, mạng cloud | 7–9 ngày |

Học theo thứ tự: chặng 2 cần mô hình TCP và HTTP của chặng 1; chặng 3 giải thích các sự cố
lác đác, khó tái hiện mà chặng 2 mới chỉ mô tả triệu chứng. Người phỏng vấn senior hay bắt đầu
bằng "gõ URL rồi Enter" rồi đào xuống đúng chỗ bạn nói lướt.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Tầng mạng, TCP và UDP

**Vì sao cần học:** Mọi request tới app Laravel của bạn đều đi qua TCP. Hiểu TCP là nền để
hiểu vì sao tái dùng kết nối quan trọng, vì sao đọc socket có thể nhận nửa message, và vì sao
gói lớn "biến mất" khi đi qua VPN. Câu "TCP khác UDP thế nào" và "vì sao handshake 3 bước"
gần như luôn có ở vòng đầu.

**Học gì**

*Mô hình tầng*
- Mạng được chia thành các tầng. Mỗi tầng chỉ lo một việc và dựa vào tầng bên dưới.
- Có hai cách chia hay gặp: mô hình TCP/IP (4 tầng, dùng trong thực tế) và mô hình OSI (7 tầng,
  hay gặp trong sách và phỏng vấn). Bảng dưới đặt hai mô hình cạnh nhau:

| TCP/IP | OSI | Việc | Ví dụ |
|---|---|---|---|
| Application | 7, 6, 5 | giao thức ứng dụng | HTTP, DNS, SMTP, TLS (thường xếp ở đây) |
| Transport | 4 | kết nối giữa process, port | TCP, UDP, QUIC (chạy trên UDP) |
| Internet | 3 | định tuyến giữa máy | IP, ICMP |
| Link | 2, 1 | truyền trong một mạng vật lý | Ethernet, Wi-Fi, ARP |

- *Port* là số (0–65535) dùng để phân biệt các process trên cùng một máy. IP đưa gói tới đúng
  máy, port đưa tới đúng chương trình. Ví dụ: Nginx nghe port 443, MySQL nghe port 3306.

*TCP*
- TCP là giao thức "có kết nối": hai bên phải bắt tay trước khi gửi dữ liệu. TCP đảm bảo:
  - Dữ liệu tới **đúng thứ tự**.
  - Gói bị mất thì **gửi lại**.
  - *Flow control*: bên gửi không gửi nhanh hơn bên nhận kịp xử lý.
  - *Congestion control*: bên gửi tự giảm tốc khi mạng ở giữa bị nghẽn (chi tiết ở module 3.1).
- ⚠️ TCP là *byte stream*, tức một dòng byte liên tục, **không có ranh giới message**.
  - Ví dụ: bên gửi gọi `write("hello")` rồi `write("world")`. Bên nhận có thể nhận `"hellowor"`
    trong lần `read()` đầu và `"ld"` ở lần sau.
  - Vì vậy app phải tự *đóng khung* (framing) message: ghi độ dài ở đầu (*length prefix*) hoặc
    dùng ký tự phân cách (*delimiter*, ví dụ HTTP/1.1 dùng dòng trống để kết thúc header).

*UDP*
- UDP không có kết nối, không đảm bảo thứ tự, không đảm bảo gói tới nơi. Gửi đi là xong.
- Dùng cho: DNS, VoIP, game, và QUIC (nền của HTTP/3).
- ⚠️ "UDP nhanh hơn TCP" không hẳn đúng. UDP nhanh vì không chờ gửi lại gói mất. Muốn tin cậy
  thì app phải tự làm phần đó, và lúc ấy nó không còn "nhẹ" nữa.

*3-way handshake*
- Mỗi byte TCP gửi đi được đánh một số thứ tự gọi là *sequence number* (seq). Bên nhận trả lời
  bằng *ack* = "tôi đã nhận tới byte này, gửi tiếp từ số này".
- Quy trình bắt tay:
  1. Client gửi `SYN(seq=x)`: "tôi muốn mở kết nối, số thứ tự ban đầu của tôi là x".
  2. Server gửi `SYN-ACK(seq=y, ack=x+1)`: "đã nhận x, số thứ tự ban đầu của tôi là y".
  3. Client gửi `ACK(ack=y+1)`: "đã nhận y". Từ đây hai bên gửi dữ liệu.
- Vì sao cần 3 bước: mỗi bên phải gửi sequence number ban đầu của mình **và** nhận được xác nhận
  cho nó. Nếu chỉ 2 bước, một gói SYN cũ bị lạc đường tới muộn có thể mở ra một "kết nối ma" mà
  client không hề muốn.
- Cái giá: mất 1 *RTT* (round-trip time, thời gian một gói đi rồi về) trước khi gửi được byte
  dữ liệu đầu tiên. Cộng thêm TLS (module 1.4) là thêm RTT nữa.
  - Ví dụ: server ở Singapore, RTT 40 ms. Kết nối mới + TLS tốn khoảng 80 ms trước khi request
    đầu tiên đi. Vì vậy **tái dùng kết nối** (keep-alive, pool, module 2.1) rất quan trọng.

*Địa chỉ IP, NAT, CIDR*
- *IP private* là các dải chỉ dùng trong mạng nội bộ, không đi thẳng ra Internet:
  `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`.
- *NAT* (Network Address Translation) là thiết bị đổi IP private thành một IP public khi gói đi
  ra Internet. Ví dụ: cả văn phòng 100 máy ra Internet chung một IP public.
- *CIDR* là cách viết một dải IP: số sau dấu `/` là số bit cố định ở đầu.
  - `/24` cố định 24 bit, còn 8 bit tự do, tức 256 địa chỉ.
  - `/16` còn 16 bit tự do, tức 65.536 địa chỉ.

*MTU*
- *MTU* (Maximum Transmission Unit) là kích thước gói lớn nhất một đường mạng chuyển được, thường
  là 1500 byte. Gói lớn hơn phải bị chia nhỏ (*fragmentation*), ở mức này chỉ cần biết tên.
- ⚠️ VPN và tunnel bọc thêm header nên MTU thực tế nhỏ hơn. Gói lớn có thể bị rơi âm thầm: kết
  nối mở được, request nhỏ chạy, nhưng response lớn thì treo.

**Đọc**
- HPBN: chương [Building Blocks of TCP](https://hpbn.co/building-blocks-of-tcp/) (handshake, slow start, head-of-line blocking)
- Kurose & Ross: chương 3, phần 3.5 (TCP)
- [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293) (TCP): mục 3.5 (connection establishment), tra cứu khi cần

**Nắm chắc khi**
- [ ] Vẽ được 3-way handshake kèm seq/ack và giải thích vì sao không phải 2 bước
- [ ] Bắt được handshake bằng `tcpdump -nn port 443` và chỉ ra từng gói
- [ ] Giải thích được vì sao đọc một lần `read()` trên socket TCP có thể nhận nửa message

#### 1.2 DNS cơ bản

**Vì sao cần học:** DNS là bước đầu tiên của mọi request, và "đổi DNS mà chưa có hiệu lực" là
tình huống ai cũng gặp khi migrate server, đổi CDN hay cấu hình email. Người phỏng vấn hay hỏi
quá trình phân giải và cách đổi IP mà không làm rơi request.

**Học gì**

*Quá trình phân giải*
- DNS đổi tên (`api.example.com`) thành IP. Có nhiều vai tham gia:
  - *Stub resolver*: phần nhỏ trong OS mà app gọi tới. Nó xem `/etc/hosts` trước, rồi hỏi
    server ghi trong `/etc/resolv.conf`.
  - *Recursive resolver*: server đi hỏi thay bạn, ví dụ của ISP, của cloud, hay `1.1.1.1`.
  - *Authoritative server*: server nắm dữ liệu gốc của một domain.
- Các bước khi cache trống:
  1. App hỏi stub resolver, stub resolver hỏi recursive resolver.
  2. Recursive resolver hỏi *root* server: "ai quản `.com`?".
  3. Hỏi *TLD* server của `.com`: "ai quản `example.com`?".
  4. Hỏi authoritative server của `example.com`: "IP của `api.example.com` là gì?".
  5. Kết quả được **cache theo TTL ở mọi tầng**, nên lần sau không phải đi lại từ đầu.
- DNS chạy trên UDP port 53, chuyển sang TCP khi response quá lớn.
- *DoH* (DNS over HTTPS) và *DoT* (DNS over TLS) mã hoá truy vấn để người ở giữa không đọc được.

*Các loại record*

| Record | Dùng cho |
|---|---|
| `A` / `AAAA` | tên → IPv4 / IPv6 |
| `CNAME` | bí danh của tên khác |
| `MX` | mail server |
| `TXT` | xác minh domain, SPF, DKIM, DMARC |
| `NS`, `SOA` | nameserver của zone; thông tin zone, gồm TTL cho negative caching |
| `SRV` | host + port cho service |
| `CAA` | CA nào được cấp cert cho domain |
| `PTR` | IP → tên (reverse DNS, quan trọng cho mail) |

- *Zone* là phần của cây tên mà một nhóm nameserver quản lý, ví dụ zone `example.com`.
- ⚠️ Không đặt `CNAME` ở *apex* (tên gốc `example.com`, không có tiền tố) cùng với record khác.
  Nếu cần trỏ apex tới CDN hay LB thì dùng `ALIAS`/`ANAME` hoặc alias record của Route 53.

*TTL và cách đổi DNS an toàn*
- *TTL* (time to live) là số giây một kết quả được phép nằm trong cache.
- ⚠️ Đổi DNS không có hiệu lực ngay: ai đã cache bản cũ sẽ dùng nó tới khi hết TTL.
- Quy trình migration không làm rơi request:
  1. Hạ TTL xuống thấp (ví dụ 60 giây), sớm hơn thời điểm đổi **ít nhất một TTL cũ**. Nếu TTL
     cũ là 1 ngày thì phải hạ trước 1 ngày.
  2. Đổi record sang IP mới.
  3. Giữ hệ thống cũ chạy thêm một thời gian cho những ai còn cache.
  4. Nâng TTL trở lại.

**Đọc**
- [Julia Evans: A DNS resolver in 80 lines of Go](https://jvns.ca/blog/2022/02/01/a-dns-resolver-in-80-lines-of-go/): hiểu phân giải đệ quy bằng cách viết một cái
- `man dig`; thử `dig +trace example.com`

**Nắm chắc khi**
- [ ] Chạy `dig +trace` cho một domain và giải thích từng bước
- [ ] Lập được kế hoạch đổi IP của `api.example.com` không làm rơi request, có mốc thời gian theo TTL

#### 1.3 HTTP cơ bản

**Vì sao cần học:** Mọi API bạn viết bằng Laravel đều là HTTP. Chọn sai method hay status làm
client retry sai, cấu hình cookie sai là mất session hoặc lộ session. Câu "safe khác idempotent
thế nào" và "401 khác 403 thế nào" rất hay bị hỏi.

**Học gì**

*Cấu trúc một request và response*
- Request gồm: method (`GET`, `POST`...), path, version, các header, rồi body.
- Response gồm: status code, các header, rồi body.

```http
POST /api/orders HTTP/1.1
Host: shop.example.com
Content-Type: application/json
Content-Length: 27

{"product_id": 42, "qty": 1}
```

*Safe và idempotent*
- Method *safe* là method không đổi state phía server: `GET`, `HEAD`, `OPTIONS`.
- Method *idempotent* là method gọi N lần cho cùng hiệu ứng như gọi 1 lần. Gồm mọi method safe,
  cộng `PUT` và `DELETE`.
  - Ví dụ: `DELETE /orders/5` gọi 3 lần thì đơn 5 vẫn chỉ bị xoá một lần.
- `POST` và `PATCH` không idempotent theo mặc định.
  - Ví dụ: `POST /orders` gọi 2 lần vì mạng chập chờn là ra 2 đơn. Đó là lý do có header
    `Idempotency-Key` ([09-api-design.md](09-api-design.md)).
- ⚠️ Safe kéo theo idempotent, nhưng không có chiều ngược lại. `DELETE` idempotent nhưng không
  safe, vì nó có đổi state.
- Vì sao quan trọng: proxy, thư viện HTTP và trình duyệt chỉ tự retry an toàn với method
  idempotent.

*Status code*
- `2xx`: thành công.
- `3xx`: chuyển hướng hoặc dùng cache.
  - `301` chuyển vĩnh viễn và được trình duyệt cache.
  - `302`, `307` chuyển tạm. `307` giữ nguyên method.
  - `308` chuyển vĩnh viễn và giữ nguyên method.
  - `304` "không đổi, dùng bản cache của bạn".
- `4xx`: lỗi phía client.
  - `401` chưa xác thực (chưa đăng nhập hoặc token sai). `403` đã biết bạn là ai nhưng không có
    quyền.
  - `409` xung đột state, `422` dữ liệu không hợp lệ, `429` gọi quá nhiều.
- `5xx`: lỗi phía server.

*Header quan trọng*
- Nhóm nội dung: `Host`, `Content-Type`, `Content-Length`, `Accept-Encoding`.
- Nhóm xác thực và state: `Authorization`, `Cookie`/`Set-Cookie`.
- Nhóm cache: `Cache-Control`, `ETag` (module 2.3).
- Nhóm điều hướng và vận hành: `Location`, `X-Forwarded-For`/`Forwarded` (module 2.5),
  `X-Request-Id`, `Retry-After`, `Idempotency-Key`.
- Security header: `Strict-Transport-Security`, `Content-Security-Policy`,
  `X-Content-Type-Options: nosniff` ([10-security.md](10-security.md)).

*Stateless và cookie*
- HTTP là *stateless*: mỗi request độc lập, server không tự nhớ request trước.
- App "nhớ" bạn đã đăng nhập bằng một trong hai cách:
  - Cookie chứa *session id*, còn dữ liệu session nằm ở server (Laravel: file, Redis, DB).
  - Token (ví dụ JWT) mà client gửi kèm mỗi request.
- Các thuộc tính của cookie:
  - `HttpOnly`: JavaScript không đọc được, giảm thiệt hại khi bị XSS.
  - `Secure`: chỉ gửi qua HTTPS.
  - `SameSite=Strict|Lax|None`: có gửi cookie khi request đến từ site khác không. Chrome mặc
    định coi là `Lax` nếu không khai. `None` bắt buộc đi kèm `Secure`.
  - `Domain`, `Path`: cookie được gửi tới host và đường dẫn nào.
  - `Expires`/`Max-Age`: hết hạn khi nào.
- ⚠️ `Domain=example.com` làm cookie bị gửi tới **mọi subdomain**, kể cả subdomain ít tin cậy
  như `blog.example.com` chạy WordPress của bên thứ ba.
- Thiết kế API chi tiết: [09-api-design.md](09-api-design.md).

**Đọc**
- MDN: [HTTP request methods](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods), [Idempotent](https://developer.mozilla.org/en-US/docs/Glossary/Idempotent), [Status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status), [Cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies)
- RFC 9110: mục [9.2.1 Safe Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.1) và [9.2.2 Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9.2.2)

**Nắm chắc khi**
- [ ] Xếp được 7 method vào bảng safe/idempotent và cho ví dụ vì sao retry `POST` nguy hiểm
- [ ] Viết được `Set-Cookie` cho session cookie của Laravel với đủ thuộc tính an toàn, giải thích từng cái
- [ ] Gọi được một API bằng `curl -v` và đọc hết request/response header

#### 1.4 HTTPS cơ bản

**Vì sao cần học:** Mọi app production đều chạy HTTPS, và lỗi cert (thiếu intermediate, hết
hạn) là nguyên nhân outage rất phổ biến. Người phỏng vấn hay hỏi "HTTPS bảo vệ được gì" và "vì
sao trình duyệt chạy mà `curl` báo lỗi cert".

**Học gì**

*HTTPS bảo vệ gì*
- HTTPS là HTTP chạy bên trong TLS. TLS cho ba thứ:
  - Mã hoá: người ở giữa không đọc được nội dung.
  - Toàn vẹn: người ở giữa không sửa được nội dung mà không bị phát hiện.
  - Xác thực server: bạn đang nói chuyện với đúng `example.com`, không phải kẻ giả mạo.
- Không che được:
  - IP đích.
  - Tên domain: *SNI* (tên host client gửi trong gói mở đầu, module 2.4) thường vẫn lộ.

*Handshake, ý chung*
1. Hai bên trao đổi khoá bằng thuật toán *ECDHE* để cùng tính ra một *khoá phiên* mà người
   nghe lén không tính được.
2. Server chứng minh danh tính bằng cert.
3. Từ đó dữ liệu được mã hoá bằng *mật mã đối xứng* (một khoá dùng cho cả mã hoá và giải mã,
   rất nhanh), ví dụ AES-GCM hoặc ChaCha20.

*Cert và chuỗi tin cậy*
- *Cert* (certificate) chứa: domain, public key, hạn dùng, và chữ ký của *CA* (Certificate
  Authority, tổ chức được tin để cấp cert).
- Chuỗi tin cậy có ba mắt:
  - *Leaf*: cert của chính site bạn.
  - *Intermediate*: cert của CA trung gian, dùng để ký leaf.
  - *Root*: cert gốc, có sẵn trong OS hoặc trình duyệt.
- Server phải gửi leaf **và** intermediate. Client tự dựng chuỗi tới root mà nó tin.
- ⚠️ Server quên gửi intermediate: trình duyệt có thể vẫn chạy (vì đã cache intermediate từ
  site khác), còn `curl`, app mobile, Java client thì lỗi. Kiểm tra bằng
  `openssl s_client -connect host:443 -showcerts`.
- *Self-signed cert* là cert tự ký, không có CA nào đứng sau. Dùng CA nội bộ thì phải phân phối
  root của CA đó tới mọi client.
- ⚠️ Cert hết hạn vẫn là nguyên nhân outage phổ biến, nhất là khi hạn cert ngày càng ngắn (xem
  module 2.4).

**Đọc**
- HPBN: chương [Transport Layer Security](https://hpbn.co/transport-layer-security-tls/) (chain of trust, session resumption)
- [The Illustrated TLS 1.3 Connection](https://tls13.xargs.org/): lướt để thấy handshake thật trông thế nào

**Nắm chắc khi**
- [ ] Dùng `openssl s_client` xem được chain của một site, chỉ ra leaf, intermediate, root
- [ ] Giải thích được với người không chuyên HTTPS chống được gì và không chống được gì

#### 1.5 Gõ URL rồi Enter

**Vì sao cần học:** Đây là câu phỏng vấn kinh điển nhất của mảng mạng. Nó không kiểm tra bạn
thuộc bao nhiêu chi tiết, mà kiểm tra bạn có bức tranh toàn cảnh không và đào sâu được phần
nào. Với backend engineer, phần được đào nhiều nhất là hạ tầng phía server.

**Học gì**

*Khung 10 bước (nói được trong 1–2 phút)*
1. Phân tích URL. Kiểm tra *HSTS* (danh sách site bắt buộc HTTPS, module 2.4) để ép dùng `https`.
2. Xem cache phía client: service worker, HTTP cache của trình duyệt.
3. DNS: cache trình duyệt → OS → recursive resolver → root → TLD → authoritative (module 1.2).
   - Tên có thể là `CNAME` trỏ tới CDN. *GeoDNS* trả về IP của edge gần người dùng nhất.
4. Mở kết nối:
   - Có sẵn kết nối tới host này thì dùng lại.
   - Không có thì TCP handshake, hoặc QUIC nếu trình duyệt đã biết server hỗ trợ qua header
     `Alt-Svc` hoặc DNS record `HTTPS`.
5. TLS: ClientHello mang SNI và *ALPN* (danh sách giao thức muốn dùng, ví dụ `h2`, `http/1.1`).
   Client kiểm tra chain, tên, hạn dùng, tình trạng thu hồi của cert.
6. Gửi request: method, path, `Host`, `Cookie`, `Accept-Encoding`.
7. Request đi qua hạ tầng: CDN edge (anycast, module 3.5) → WAF → load balancer → Nginx/ingress
   → app (worker PHP-FPM, goroutine, thread).
   - *CDN edge*: server cache của CDN đặt gần người dùng (module 2.7).
   - *WAF* (Web Application Firewall): lớp lọc chặn request độc hại như SQL injection.
   - *Ingress*: cổng nhận request HTTP từ ngoài vào cluster Kubernetes.
8. App xử lý: routing, middleware, business logic, cache, DB, gọi service khác. Ghi log, metric,
   trace.
9. Response đi ngược qua proxy, LB, CDN, và có thể được CDN cache lại.
10. Trình duyệt render:
    - Dựng DOM (từ HTML) và CSSOM (từ CSS).
    - JS chặn việc parse HTML, trừ khi có `async`/`defer`.
    - Tải thêm tài nguyên, rồi layout → paint → composite.

*Cách trả lời*
- Nói khung trước, rồi hỏi người phỏng vấn muốn đào sâu phần nào.
- Backend engineer nên chủ động đào sâu bước 7–8. Ví dụ với stack PHP: Nginx nhận request, chuyển
  qua FastCGI cho một worker PHP-FPM (module 2.6), Laravel chạy middleware, controller, query
  MySQL, trả JSON.
- ⚠️ Đừng nói lướt một bước mà mình không đào sâu được. Người phỏng vấn senior hay đào đúng chỗ
  bạn nói nhanh nhất.

**Đọc**
- MDN: [How browsers work](https://developer.mozilla.org/en-US/docs/Web/Performance/Guides/How_browsers_work)
- [everything curl: write-out](https://everything.curl.dev/usingcurl/verbose/writeout.html): đo từng giai đoạn bằng `curl -w`

**Nắm chắc khi**
- [ ] Nói được khung 10 bước trong 2 phút, rồi đào sâu được 5 phút vào bất kỳ bước nào trong 3–8
- [ ] Đo được thời gian DNS, TCP, TLS, TTFB bằng `curl -w` và giải thích lần gọi thứ hai khác lần đầu thế nào (bài tập 1)

---

### Chặng 2: Làm chủ 🟡

#### 2.1 TCP khi vận hành: đóng kết nối, keep-alive, pool

**Vì sao cần học:** Sự cố "server có hàng chục nghìn kết nối `TIME_WAIT`", "`CLOSE_WAIT` tăng
dần rồi hết fd", hay "gọi API ngoài chậm vì mỗi lần một handshake" đều nằm ở module này. Trong
PHP, cách bạn dùng Guzzle hay `Http` của Laravel quyết định có tái dùng kết nối hay không.

**Học gì**

*Đóng kết nối: 4-way close*
- TCP có hai chiều độc lập, mỗi chiều đóng riêng. Một bên có thể đã nói "tôi gửi xong" mà vẫn
  nhận tiếp được. Tình trạng này gọi là *half-close*.
- Vì vậy đóng kết nối cần 4 gói:
  1. Bên A gửi `FIN`: "tôi gửi xong".
  2. Bên B trả `ACK`.
  3. Khi B cũng xong, B gửi `FIN`.
  4. A trả `ACK`.

*TIME_WAIT và CLOSE_WAIT*
- `TIME_WAIT` nằm ở bên **đóng trước**, kéo dài 2×MSL (*Maximum Segment Lifetime*, thời gian
  sống tối đa của một gói). Linux cố định 60 giây. Nó tồn tại vì hai lý do:
  - Chặn gói trễ của kết nối cũ lẫn vào kết nối mới có cùng *4-tuple* (IP nguồn, port nguồn, IP
    đích, port đích).
  - Để còn gửi lại được `ACK` cuối nếu `ACK` đó bị mất.
- Server có nhiều `TIME_WAIT` khi chính server chủ động đóng, ví dụ vì client không dùng
  keep-alive.
- `CLOSE_WAIT` nằm ở bên **nhận `FIN`**: bên kia đã đóng, còn app mình chưa gọi `close()`.
- ⚠️ Nhiều `CLOSE_WAIT` là **bug trong app** (quên đóng kết nối, quên đọc hết body), không phải
  chuyện tuning kernel.
- ⚠️ Các tham số kernel hay bị khuyên bừa:
  - `tcp_tw_recycle` gây lỗi khi client đứng sau NAT, và đã bị bỏ khỏi kernel từ 4.12.
  - `tcp_tw_reuse` chỉ áp dụng cho kết nối **đi ra**, không giúp phía nhận kết nối.

*Hai khái niệm "keep-alive"*

| | HTTP keep-alive | TCP keepalive |
|---|---|---|
| Là gì | Dùng lại một kết nối TCP cho nhiều request HTTP | Gửi gói dò (*probe*) khi kết nối rảnh lâu |
| Mục đích | Tránh handshake TCP + TLS cho mỗi request | Phát hiện kết nối đã chết, giữ mapping của NAT không bị xoá |
| Cấu hình ở | Web server, HTTP client, proxy | Socket option `SO_KEEPALIVE`, sysctl `tcp_keepalive_time` |

*Connection pool*
- *Connection pool* là một kho kết nối đã mở sẵn, dùng xong trả lại kho thay vì đóng. HTTP client
  và DB driver đều dùng pool. Đây là hệ quả trực tiếp của HTTP keep-alive.
- ⚠️ Tạo HTTP client mới cho mỗi request là mất keep-alive. Hậu quả:
  - Tốn một lần handshake cho mỗi lần gọi.
  - Sinh rất nhiều `TIME_WAIT`, dễ dẫn tới hết port (module 3.1).
- Áp vào PHP:
  - Mỗi request của PHP-FPM chạy như một process sạch, nên Guzzle hay `Http` của Laravel **không
    giữ kết nối giữa các request**.
  - Trong một request mà gọi nhiều API tới cùng host thì dùng chung một client để còn tái dùng
    kết nối.

*Quan sát*
- `ss -tan state time-wait | wc -l`: đếm số kết nối đang `TIME_WAIT`.
- `ss -s`: tổng hợp số kết nối theo trạng thái.

**Đọc**
- Vincent Bernat: [Coping with the TCP TIME-WAIT state on busy Linux servers](https://vincent.bernat.ch/en/blog/2014-tcp-time-wait-state-linux)
- man: [tcp(7)](https://man7.org/linux/man-pages/man7/tcp.7.html) (mục `tcp_tw_reuse`, `tcp_keepalive_time`)
- Cloudflare: [This is strictly a violation of the TCP specification](https://blog.cloudflare.com/this-is-strictly-a-violation-of-the-tcp-specification/) (một sự cố thật về `CLOSE_WAIT`)

**Nắm chắc khi**
- [ ] Nói được bên nào có `TIME_WAIT`, bên nào có `CLOSE_WAIT`, và cái nào là bug
- [ ] Tái hiện được `CLOSE_WAIT` tích tụ bằng một client không đóng body, thấy nó trong `ss`
- [ ] Giải thích được vì sao hai khái niệm "keep-alive" khác nhau và cấu hình ở đâu

#### 2.2 HTTP/1.1, HTTP/2, HTTP/3 và gRPC

**Vì sao cần học:** Bạn cần biết HTTP/2 và HTTP/3 giải quyết gì để quyết định bật ở đâu, và
để không mang mẹo tối ưu cũ của HTTP/1.1 vào. Nếu công ty có service nội bộ dùng gRPC, bạn cần
biết vì sao PHP-FPM không làm server gRPC được và vì sao load balancer thường "cân bằng" sai.

**Học gì**

*Head-of-line blocking*
- *Head-of-line (HOL) blocking* là tình trạng một thứ ở đầu hàng bị chậm làm mọi thứ phía sau
  phải chờ, dù chúng không liên quan.
  - Ví dụ ở HTTP/1.1: trên một kết nối, request 2 phải chờ response 1 xong.
  - Ví dụ ở TCP: một gói bị mất thì mọi byte đến sau phải chờ gói đó được gửi lại, vì TCP giao
    dữ liệu đúng thứ tự.
- *Multiplex* nghĩa là chạy nhiều request song song trên cùng một kết nối, mỗi request là một
  *stream*.

*So sánh ba phiên bản*

| | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---|---|---|---|
| Transport | TCP | TCP (thực tế luôn có TLS) | QUIC trên UDP |
| Định dạng | text | binary frame | binary frame |
| Nhiều request | tuần tự trên một kết nối; trình duyệt mở ~6 kết nối/host | multiplex nhiều stream | multiplex, stream độc lập |
| Nén header | không | HPACK | QPACK |
| HOL blocking | ở tầng HTTP | hết ở HTTP, còn ở TCP | không còn ở transport |
| Handshake | TCP + TLS | TCP + TLS | gộp, 1-RTT, có 0-RTT |

- Hệ quả của dòng HOL: trên mạng hay mất gói, HTTP/2 dồn mọi thứ vào một kết nối TCP, nên một
  gói mất làm chậm **tất cả** stream. HTTP/1.1 với 6 kết nối thì chỉ chậm một.
- Mẹo thời HTTP/1.1 như *domain sharding* (chia tài nguyên ra nhiều domain để mở thêm kết nối) và
  gộp file JS/CSS thành một file lớn **phản tác dụng** với HTTP/2.
- QUIC nhận diện kết nối bằng *connection id* thay vì 4-tuple, nên kết nối sống được khi điện
  thoại đổi mạng từ Wi-Fi sang 4G.

*Cạm bẫy khi triển khai*
- ⚠️ Client nói HTTP/2 với CDN hay LB **không có nghĩa** LB nói HTTP/2 với backend. Phía sau
  thường vẫn là HTTP/1.1.
- ⚠️ HTTP/3 không chạy khi mạng chặn UDP (nhiều mạng công ty làm vậy). Trình duyệt tự lùi về
  HTTP/2.
- *HTTP/2 Rapid Reset* (CVE-2023-44487): kẻ tấn công mở rồi huỷ stream liên tục để làm server
  quá tải. Chỉ cần biết tên và hiểu vì sao server phải giới hạn số stream và tốc độ huỷ.

*gRPC (đại ý, chi tiết ở [09-api-design.md](09-api-design.md))*
- *gRPC* là cách gọi hàm từ xa (*RPC*) chạy trên HTTP/2.
- Payload là *protobuf*: định dạng binary, schema viết trong file `.proto`, từ đó sinh code
  client và server.
- Có 4 kiểu gọi: unary (một hỏi một đáp), server streaming, client streaming, bidirectional.
- *Deadline* được truyền qua các service trong chuỗi gọi. Status code riêng, ví dụ
  `DEADLINE_EXCEEDED`, `UNAVAILABLE`.
- ⚠️ Cần HTTP/2 từ đầu tới cuối, hoặc proxy hiểu gRPC. Qua LB L4 thì mọi request dồn vào một
  backend (module 2.7).
- ⚠️ Quy tắc sửa protobuf:
  - Không đổi số thứ tự của field.
  - Không tái dùng số của field đã xoá.
  - Thêm field mới thì vẫn tương thích ngược.
- PHP:
  - Làm client gRPC cần extension `grpc`.
  - Làm server gRPC bằng PHP-FPM thuần thì không được, vì FPM không nói HTTP/2 và không giữ
    stream dài. Cần RoadRunner hoặc một runtime chạy lâu.

**Đọc**
- HPBN: chương [HTTP/2](https://hpbn.co/http2/)
- [HTTP/3 explained](https://http3-explained.haxx.se/) (Daniel Stenberg, tác giả curl)
- gRPC: [Core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/); Protobuf: [Overview](https://protobuf.dev/overview/)
- Tra cứu: [RFC 9113](https://www.rfc-editor.org/rfc/rfc9113) (HTTP/2), [RFC 9114](https://www.rfc-editor.org/rfc/rfc9114) (HTTP/3), [RFC 9000](https://www.rfc-editor.org/rfc/rfc9000) (QUIC)

**Nắm chắc khi**
- [ ] Giải thích được HOL blocking ở cả ba phiên bản, và vì sao HTTP/2 trên mạng mất gói có thể tệ hơn HTTP/1.1
- [ ] Viết được một file `.proto` nhỏ và nói được thay đổi nào phá tương thích
- [ ] Xác định được site đang dùng phiên bản HTTP nào bằng `curl -v --http3` hoặc devtools

#### 2.3 HTTP caching, compression, range, CORS

**Vì sao cần học:** Header cache sai là nguyên nhân của hai loại sự cố: user không thấy bản
deploy mới, và tệ hơn là CDN trả dữ liệu của user A cho user B. CORS thì là lỗi mà dev frontend
hỏi backend nhiều nhất. Cả hai đều hay xuất hiện trong phỏng vấn.

**Học gì**

*Cache-Control*
- Header `Cache-Control` do server gửi, nói cho trình duyệt và CDN biết được cache response thế
  nào:
  - `max-age=N`: được dùng bản cache trong N giây.
  - `s-maxage=N`: giống `max-age` nhưng chỉ cho *shared cache* (cache dùng chung cho nhiều người,
    như CDN).
  - `public`: ai cache cũng được. `private`: chỉ trình duyệt của chính user được cache, CDN
    không được.
  - `immutable`: nội dung không bao giờ đổi, không cần hỏi lại.
  - `stale-while-revalidate=N`: được trả bản cũ trong N giây trong lúc lấy bản mới ở nền.
- ⚠️ Hai cái tên hay bị hiểu ngược:
  - `no-cache`: **được lưu**, nhưng phải hỏi lại server trước mỗi lần dùng.
  - `no-store`: **không được lưu**.

*Revalidate*
- *Revalidate* là hỏi server "bản tôi đang giữ còn đúng không" thay vì tải lại cả nội dung.
- Có hai cặp header:
  - Server gửi `ETag` (mã định danh phiên bản nội dung). Lần sau client gửi `If-None-Match`.
  - Server gửi `Last-Modified`. Lần sau client gửi `If-Modified-Since`.
- Nếu không đổi, server trả `304 Not Modified` **không có body**, tiết kiệm băng thông.

*Vary và cache key*
- `Vary` báo cho cache biết phải tách bản cache theo header nào của request. Ví dụ
  `Vary: Accept-Encoding` thì bản gzip và bản không nén được lưu riêng.
- ⚠️ Thiếu `Vary`:
  - CDN trả bản gzip cho client không hỗ trợ gzip.
  - Hoặc trả nội dung của user A cho user B.

*Chính sách cho từng loại*
- Static asset có hash trong tên (`app.3f9a1c.js`): `max-age` dài + `immutable`. Đổi nội dung
  thì hash đổi, tên file đổi, nên không lo bản cũ.
- HTML: `max-age` ngắn, hoặc bắt revalidate.

*Compression*
- Client gửi `Accept-Encoding: gzip, br, zstd`. Server chọn một, nén, và trả kèm
  `Content-Encoding`.
- Không nén lại ảnh hay video, vì chúng đã được nén sẵn.
- ⚠️ Nén một response vừa chứa bí mật (ví dụ CSRF token) vừa phản chiếu input người dùng có thể
  bị tấn công kiểu *BREACH*: kẻ tấn công đoán bí mật qua kích thước response sau nén.

*Range và chunked*
- Client gửi `Range: bytes=0-1023`, server trả `206 Partial Content` với đúng đoạn đó. Dùng cho
  tải tiếp file bị đứt, tua video.
- `Transfer-Encoding: chunked` (HTTP/1.1) dùng khi server chưa biết trước độ dài response: gửi
  từng khúc, mỗi khúc ghi độ dài. HTTP/2 và HTTP/3 dùng frame nên không cần chunked.

*CORS*
- *CORS* (Cross-Origin Resource Sharing) là cơ chế **của trình duyệt**: JS ở `app.example.com`
  muốn gọi API ở `api.other.com` thì trình duyệt hỏi server kia có cho phép không.
- Với request "không đơn giản" (ví dụ có header `Authorization`, body JSON), trình duyệt gửi trước
  một request `OPTIONS` gọi là *preflight*. Server trả lời bằng các header `Access-Control-Allow-*`.
- ⚠️ CORS **không bảo vệ server** khỏi request từ `curl` hay từ backend khác. Nó chỉ bảo vệ user
  khỏi JS của site lạ (chi tiết ở [10-security.md](10-security.md)).
- Chiến lược cache ở tầng ứng dụng (Redis...): [11-cache.md](11-cache.md).

**Đọc**
- MDN: [HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching) (đọc hết), [CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
- RFC 9111: mục [5.2 Cache-Control](https://www.rfc-editor.org/rfc/rfc9111#section-5.2)

**Nắm chắc khi**
- [ ] Thiết kế được header cache cho JS có hash, trang HTML, API công khai, API `/me` (bài tập 4)
- [ ] Giải thích được một sự cố "user thấy dữ liệu của người khác" sau khi bật CDN từ góc header
- [ ] Tái hiện được `304` bằng `curl` với `If-None-Match`

#### 2.4 TLS nâng cao

**Vì sao cần học:** Bạn không cần tự cài TLS, nhưng phải quyết định TLS kết thúc ở đâu, vì sao
Laravel sau load balancer sinh ra URL `http://`, và phải có quy trình gia hạn cert khi hạn cert
sắp chỉ còn 47 ngày. Phỏng vấn senior hay hỏi TLS 1.3 nhanh hơn ở đâu và 0-RTT nguy hiểm thế nào.

**Học gì**

*TLS 1.2 và TLS 1.3*
- TLS 1.2 cần 2 RTT để bắt tay xong.
- TLS 1.3 chỉ cần 1 RTT, vì client đoán trước thuật toán và gửi luôn phần khoá của mình (*key
  share*) ngay trong ClientHello. Ngoài ra TLS 1.3:
  - Bỏ các cipher yếu.
  - Bắt buộc forward secrecy (xem dưới).
  - Mã hoá phần lớn handshake.
- *Forward secrecy*: mỗi phiên dùng khoá tạm riêng, nên dù sau này private key của server bị lộ,
  kẻ đã ghi lại traffic cũ cũng không giải mã được.

*0-RTT*
- *0-RTT* là tính năng của TLS 1.3 khi client kết nối lại (*resumption*): client gửi dữ liệu
  ngay trong gói đầu tiên, không chờ bắt tay xong.
- ⚠️ Dữ liệu 0-RTT có thể bị kẻ ở giữa **gửi lại** (*replay*). Chỉ cho phép với request
  idempotent. Ví dụ: `GET /products` thì được, `POST /payments` thì không.

*Post-quantum*
- Máy tính lượng tử trong tương lai có thể phá thuật toán trao đổi khoá hiện nay. Rủi ro gọi là
  "thu bây giờ, giải mã sau": kẻ tấn công ghi traffic hôm nay để giải mã sau này.
- TLS 1.3 đã có trao đổi khoá lai `X25519MLKEM768`, bật mặc định ở các trình duyệt lớn và
  Cloudflare.
- ⚠️ ClientHello to hơn (key share khoảng 1 KB). Một số *middlebox* cũ (thiết bị mạng đứng giữa,
  như firewall) có thể làm hỏng kết nối.

*SNI, ECH, mTLS, HSTS*
- *SNI* (Server Name Indication): client gửi tên host ngay đầu handshake, để một IP phục vụ được
  nhiều domain với nhiều cert khác nhau. Tên này đi dạng rõ.
- *ECH* (Encrypted Client Hello) mã hoá phần này để giấu tên domain. Đã có ở Chrome, Firefox,
  Cloudflare.

- *mTLS* (mutual TLS): client cũng phải trình cert, nên server biết chắc client là ai. Dùng giữa
  các service (service mesh), kết nối B2B, thiết bị IoT.
- *HSTS* là header bắt trình duyệt chỉ dùng HTTPS với site này trong một khoảng thời gian:
  `Strict-Transport-Security: max-age=...; includeSubDomains`.
  - *Preload*: đưa domain vào danh sách cài sẵn trong trình duyệt, áp dụng từ lần truy cập đầu
    tiên.
  - ⚠️ Bật `includeSubDomains` hoặc preload khi còn subdomain chỉ chạy HTTP là subdomain đó không
    truy cập được nữa. Preload rất khó gỡ.

*Thu hồi cert*
- Cert bị lộ key phải được *thu hồi* (revoke) trước hạn. Có hai cơ chế:
  - *OCSP*: client hỏi CA "cert này còn hiệu lực không" mỗi lần.
  - *CRL*: CA công bố danh sách cert đã thu hồi.
- OCSP đang bị bỏ. Let's Encrypt đã tắt OCSP responder từ 8/2025, chỉ còn CRL.
- Trình duyệt dựa vào CRL do chính trình duyệt tổng hợp: CRLSets của Chrome, CRLite của Firefox.
- *OCSP stapling* (server tự đính kèm kết quả OCSP) chỉ còn ý nghĩa với CA còn chạy OCSP.

*Hạn cert ngắn dần*
- Theo ballot SC-081 của CA/Browser Forum, hạn tối đa của cert giảm dần:

| Từ | Hạn tối đa |
|---|---|
| Trước 15/3/2026 | 398 ngày |
| 15/3/2026 | 200 ngày |
| 3/2027 | 100 ngày |
| 3/2029 | 47 ngày |

- ⚠️ Hệ quả: gia hạn thủ công không còn khả thi. Bắt buộc tự động hoá và có alert trước khi hết
  hạn. Công cụ hay dùng:
  - *ACME*: giao thức tự động xin và gia hạn cert, Let's Encrypt dùng giao thức này.
  - cert-manager trên Kubernetes, ACM trên AWS.

*TLS termination*
- *TLS termination* là chỗ giải mã TLS. Có ba lựa chọn:

| Cách | Làm thế nào | Hợp khi |
|---|---|---|
| Terminate ở LB/CDN/ingress | Giải mã ở LB, phía sau đi HTTP thường | Muốn quản lý cert tập trung, LB cần đọc HTTP để route |
| Re-encrypt hoặc mTLS tới backend | LB giải mã rồi mã hoá lại khi gửi vào | Yêu cầu compliance, zero-trust |
| Passthrough | LB L4 chuyển nguyên byte, backend tự giải mã | LB không cần đọc HTTP |

- ⚠️ Terminate ở LB thì app thấy request là `http`.
  - App phải tin header `X-Forwarded-Proto` do proxy **tin cậy** gửi.
  - Không cấu hình thì bị redirect vòng lặp (app cứ redirect sang https) hoặc sinh URL `http://`.
  - Laravel: middleware `TrustProxies`.

**Đọc**
- [RFC 8446](https://www.rfc-editor.org/rfc/rfc8446) (TLS 1.3): mục 2 (protocol overview) và 8 (0-RTT and anti-replay)
- Cloudflare: [The state of the post-quantum Internet](https://blog.cloudflare.com/pq-2024/)
- Let's Encrypt: [Ending OCSP Support in 2025](https://letsencrypt.org/2024/12/05/ending-ocsp/), [OCSP Service Has Reached End of Life](https://letsencrypt.org/2025/08/06/ocsp-service-has-reached-end-of-life/)
- CA/B Forum: [Ballot SC-081v3](https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/) (bảng lộ trình rút ngắn hạn cert)
- MDN: [Strict-Transport-Security](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Strict-Transport-Security); [hstspreload.org](https://hstspreload.org/) (đọc điều kiện và cách gỡ)

**Nắm chắc khi**
- [ ] Vẽ được handshake TLS 1.2 và 1.3, chỉ ra chỗ tiết kiệm 1 RTT
- [ ] Giải thích được vì sao 0-RTT không an toàn cho `POST /payments`
- [ ] Kể được quy trình quản lý cert của hệ thống mình khi hạn cert còn 47 ngày: cấp, gia hạn, alert, ai chịu trách nhiệm

#### 2.5 Reverse proxy, Nginx, X-Forwarded-For

**Vì sao cần học:** Gần như mọi app Laravel đều có Nginx đứng trước. Cấu hình proxy quyết định
kết nối có được tái dùng không, upload lớn có bị chặn không, rate limit có chặn nhầm cả văn
phòng không, và log có ghi đúng IP người dùng không. "Lấy IP thật của client thế nào" là câu
hỏi hay gặp và hay trả lời sai.

**Học gì**

*Forward proxy và reverse proxy*
- *Forward proxy* đứng về phía client, đại diện client đi ra ngoài. Ví dụ: *egress proxy* mà
  mọi request ra Internet của công ty phải đi qua.
- *Reverse proxy* đứng về phía server, đại diện server nhận request. Nó làm được:
  - TLS termination, routing, cache, nén, rate limit.
  - Che backend: client không biết phía sau có bao nhiêu server.
- Ví dụ: Nginx, HAProxy, Envoy, Traefik.

*Keepalive tới upstream*
- *Upstream* là các server phía sau mà Nginx chuyển request tới.
- ⚠️ Nginx **trước 1.29.7** mặc định nói HTTP/1.0 và không giữ kết nối tới upstream.
  - Hậu quả: mỗi request một kết nối mới, sinh nhiều `TIME_WAIT`, dễ hết port (module 3.1).
  - Phải khai đủ ba dòng: `keepalive` trong `upstream`, `proxy_http_version 1.1`, và
    `proxy_set_header Connection ""`.
- Từ 1.29.7 (nhánh stable 1.30), mặc định đã là HTTP/1.1 và `keepalive 32`. Kiểm tra `nginx -v`
  trước khi kết luận.

*Timeout, buffering, giới hạn body*
- `proxy_connect_timeout` và `proxy_read_timeout` mặc định 60 giây.
  - Thường quá dài cho API bình thường.
  - Lại quá ngắn cho SSE/WebSocket (module 3.4).
- `proxy_buffering on` (mặc định): Nginx đọc nhanh toàn bộ response từ upstream để giải phóng
  upstream, rồi tự trả dần cho client chậm.
  - Tốt cho PHP: worker được giải phóng sớm.
  - Phải tắt cho SSE/streaming, hoặc app gửi header `X-Accel-Buffering: no`.
- `client_max_body_size` mặc định 1 MB. Upload lớn hơn bị trả `413`.

*Rate limit*
- `limit_req` giới hạn số request theo thuật toán *leaky bucket* (request chảy ra với tốc độ đều).
  `limit_conn` giới hạn số kết nối đồng thời.
- `burst=N` cho phép vượt tạm N request, xếp hàng chờ. Thêm `nodelay` thì các request trong
  burst được xử lý ngay thay vì bị giãn ra theo tốc độ.
- ⚠️ Rate limit theo IP:
  - Sau NAT hay CDN, nhiều người chung một IP, nên chặn nhầm cả văn phòng.
  - Sau CDN mà chưa cấu hình real IP (xem dưới) thì `$binary_remote_addr` là IP của CDN, tức mọi
    user chung một bucket.

*Reload không downtime*
1. `nginx -t` để kiểm tra cú pháp cấu hình.
2. `nginx -s reload`: master đọc cấu hình mới, tạo worker mới.
3. Worker cũ làm nốt các kết nối đang có rồi mới thoát.

*X-Forwarded-For và IP thật*
- Khi đi qua proxy, IP kết nối mà app thấy là IP của proxy. Header `X-Forwarded-For` (XFF) giữ
  lại dấu vết: mỗi proxy **nối IP nó thấy vào cuối** danh sách.
  - Ví dụ: `X-Forwarded-For: 203.0.113.7, 198.51.100.2` nghĩa là client `203.0.113.7` đi qua
    proxy `198.51.100.2` rồi mới tới proxy cuối cùng.
- ⚠️ Client **tự gửi được** XFF giả ngay từ đầu. Lấy IP thật theo cách này:
  1. Đọc danh sách từ **phải sang trái**.
  2. Bỏ qua các IP thuộc proxy mà mình tin (LB, CDN của mình).
  3. IP đầu tiên không thuộc danh sách tin cậy chính là client.
- Lấy phần tử **đầu tiên** là bị giả mạo được. Hậu quả: bypass rate limit, ghi log sai, bypass
  allowlist IP.
- Cấu hình:
  - Nginx: `set_real_ip_from` (dải IP tin cậy), `real_ip_header X-Forwarded-For`,
    `real_ip_recursive on`.
  - Laravel: `TrustProxies` chỉ tin dải IP của proxy đã biết.

*Cấu hình mẫu*

```nginx
upstream api {
    least_conn;
    server 10.0.1.10:8080 max_fails=3 fail_timeout=10s;
    server 10.0.1.11:8080 max_fails=3 fail_timeout=10s;
    keepalive 32;                          # bản < 1.29.7 phải khai báo
}
limit_req_zone $binary_remote_addr zone=perip:10m rate=10r/s;
server {
    listen 443 ssl;
    http2 on;
    location /api/ {
        limit_req zone=perip burst=20 nodelay;
        proxy_pass http://api;
        proxy_http_version 1.1;            # bản < 1.29.7 phải khai báo
        proxy_set_header Connection "";    # bản < 1.29.7 phải khai báo
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 2s;
        proxy_read_timeout 30s;
    }
}
```

**Đọc**
- Nginx: [ngx_http_proxy_module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html) (mục [`proxy_http_version`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_http_version), [`proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering), [`proxy_read_timeout`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout)), [upstream `keepalive`](https://nginx.org/en/docs/http/ngx_http_upstream_module.html#keepalive), [realip](https://nginx.org/en/docs/http/ngx_http_realip_module.html), [limit_req](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
- Nginx blog: [Rate Limiting with NGINX](https://blog.nginx.org/blog/rate-limiting-nginx) (giải thích `burst` và `nodelay` bằng hình)
- Laravel: [Configuring Trusted Proxies](https://laravel.com/docs/requests#configuring-trusted-proxies)
- [RFC 7239](https://www.rfc-editor.org/rfc/rfc7239) (header `Forwarded` chuẩn hoá)

**Nắm chắc khi**
- [ ] Viết được thuật toán lấy IP thật từ XFF với một danh sách proxy tin cậy, và chỉ ra cách tấn công nếu lấy phần tử đầu
- [ ] Giải thích được `burst=20 nodelay` khác `burst=20` thế nào với một đợt 30 request cùng lúc
- [ ] Nhìn một cấu hình Nginx và nói được nó có giữ kết nối tới upstream không, dựa vào phiên bản

#### 2.6 Tầng PHP: Nginx + PHP-FPM qua FastCGI

**Vì sao cần học:** Đây là module riêng cho người làm PHP. Phần lớn sự cố 502/504 của app
Laravel nằm ở ranh giới giữa Nginx và PHP-FPM. Biết đọc một dòng error log của Nginx là biết
ngay lỗi nằm ở FPM chết, hết worker hay request chạy quá lâu. Câu "chuỗi timeout đặt thế nào"
rất hay gặp.

**Học gì**

*FastCGI*
- *FastCGI* là giao thức binary giữa web server và process ứng dụng. Nginx đóng vai client,
  PHP-FPM đóng vai server.
- Nginx gửi sang FPM:
  1. Các biến CGI: `SCRIPT_FILENAME` (file PHP cần chạy), `REQUEST_METHOD`, `QUERY_STRING`, và
     mỗi header HTTP thành một biến `HTTP_*` (ví dụ `HTTP_USER_AGENT`).
  2. Rồi tới body.
- Nginx không chạy PHP. FPM không hiểu HTTP. Mỗi bên chỉ làm phần của mình.

*Kết nối Nginx tới FPM*
- Hai cách:
  - Unix socket `fastcgi_pass unix:/run/php/php-fpm.sock`: khi cùng máy, nhanh hơn chút.
  - TCP `127.0.0.1:9000`, hoặc tên service khi FPM chạy ở container khác.
- Mặc định Nginx mở kết nối mới tới FPM cho mỗi request. Muốn tái dùng thì bật
  `fastcgi_keep_conn on` và khai `keepalive` ở `upstream`.

*Cấu hình an toàn*
- `try_files $uri $uri/ /index.php?$query_string;`: file tĩnh có thật thì trả luôn, không thì đưa
  cho *front controller* `index.php` của Laravel.
- `fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;`
  - `$realpath_root` là đường dẫn đã giải symlink. Khi deploy bằng cách đổi symlink `current`,
    request mới dùng code mới, không lẫn code cũ (xem [01-os-linux.md](01-os-linux.md)).
- ⚠️ Không cho chạy PHP trong thư mục upload.
  - Chỉ chuyển cho FPM đúng `index.php`, hoặc file `.php` có thật.
  - Lỗi kinh điển: với `cgi.fix_pathinfo` bật, request `/uploads/avatar.jpg/x.php` làm FPM chạy
    `avatar.jpg` như code PHP. Kẻ tấn công chỉ cần upload một "ảnh" chứa code.

*Chuỗi timeout*
- Quy tắc: tầng ngoài phải có timeout lớn hơn tầng trong. Nếu không, tầng ngoài bỏ cuộc trong
  khi tầng trong vẫn đang làm.

| Tầng | Tham số | Mặc định |
|---|---|---|
| LB (ví dụ AWS ALB) | idle timeout | 60 giây |
| Nginx → FPM | `fastcgi_connect_timeout`, `fastcgi_read_timeout`, `fastcgi_send_timeout` | 60 giây |
| FPM | `request_terminate_timeout` (thời gian thật) | 0 (không giới hạn) |
| PHP | `max_execution_time` | 30 giây (CLI: 0) |
| App | timeout của HTTP client, DB, Redis | tuỳ thư viện, nhiều cái là vô hạn |

- ⚠️ Trên Linux, `max_execution_time` không tính thời gian chờ I/O (chờ DB, chờ API). Một
  request treo vì API ngoài không bị nó chặn. Chỉ `request_terminate_timeout` (tính theo đồng hồ
  thật) chặn được.
- ⚠️ Nếu `fastcgi_read_timeout` nhỏ hơn thời gian PHP thực chạy:
  1. Nginx hết kiên nhẫn, trả 504 cho client.
  2. Nhưng worker FPM vẫn chạy tiếp tới xong, vẫn chiếm một slot.
  3. Client retry thì lại chiếm thêm một worker nữa.

*Đọc lỗi trong error log của Nginx*

| Dòng log | Nghĩa | Client thấy |
|---|---|---|
| `connect() to unix:/run/php/php-fpm.sock failed (2: No such file or directory)` hoặc `(111: Connection refused)` | FPM chết hoặc sai đường dẫn socket | 502 |
| `(11: Resource temporarily unavailable)` | Hàng đợi (*backlog*) của FPM đầy vì hết worker rảnh | 502 |
| `upstream timed out (110) while reading response header` | Vượt `fastcgi_read_timeout` | 504 |
| `upstream prematurely closed connection` | Worker bị kill giữa chừng (`request_terminate_timeout`, segfault, OOM) | 502 |

*Upload*
- Cả ba giới hạn phải đủ lớn: `client_max_body_size` (Nginx), `upload_max_filesize` và
  `post_max_size` (PHP). Thiếu một cái là upload hỏng, và mỗi cái báo lỗi một kiểu khác nhau.

**Đọc**
- Nginx: [ngx_http_fastcgi_module](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html) (mục [`fastcgi_read_timeout`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_read_timeout), [`fastcgi_keep_conn`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_keep_conn)), wiki [PHP FastCGI Example](https://www.nginx.com/resources/wiki/start/topics/examples/phpfcgi/) (đọc phần cảnh báo bảo mật)
- Laravel: [Deployment: Nginx](https://laravel.com/docs/deployment#nginx) (cấu hình mẫu chính thức)
- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (`listen`, `listen.backlog`, `request_terminate_timeout`)
- [FastCGI Specification](https://fastcgi-archives.github.io/FastCGI_Specification.html): lướt mục 3 (protocol basics) để biết record trông thế nào
- Chi tiết process model của FPM: [01-os-linux.md](01-os-linux.md), runtime PHP: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Nhìn 4 dòng error log Nginx ở trên, nói ngay được mã lỗi client thấy và hướng sửa
- [ ] Đặt được bộ timeout cho ALB, Nginx, FPM, PHP, Guzzle của một API có endpoint export chạy 2 phút, giải thích thứ tự
- [ ] Viết được cấu hình Nginx cho Laravel không cho chạy PHP trong `storage/app/public` (bài tập 3)

#### 2.7 Load balancer, health check, CDN

**Vì sao cần học:** Khi app chạy nhiều server, load balancer quyết định request đi đâu, server
nào bị coi là chết, và deploy có làm rơi request không. Cấu hình health check sai có thể làm cả
cụm bị đánh dấu chết chỉ vì DB chậm. CDN cấu hình sai là lộ dữ liệu người dùng.

**Học gì**

*L4 và L7*
- *Load balancer* (LB) chia request cho nhiều backend. Có hai loại theo tầng mà nó nhìn thấy:

| | L4 | L7 |
|---|---|---|
| Nhìn thấy | IP, port, TCP/UDP | method, path, header, cookie |
| Làm được | chuyển kết nối, rất nhanh, protocol bất kỳ | route theo path/host, TLS termination, retry, rewrite, WAF |
| Ví dụ | AWS NLB, LVS, HAProxy mode tcp | AWS ALB, Nginx, Envoy, HAProxy mode http |
| Cân bằng theo | kết nối | request |

- ⚠️ gRPC hay HTTP/2 qua LB L4: một kết nối dài mang mọi request, mà L4 chỉ chia **kết nối**,
  nên mọi request dồn vào một backend. Cần LB L7, hoặc để client tự cân bằng.

*Thuật toán chia tải*
- *Round robin*: lần lượt từng server.
- *Weighted*: server mạnh nhận nhiều hơn theo trọng số.
- *Least connections*: gửi cho server đang có ít kết nối nhất. Hợp khi request dài ngắn khác nhau.
- *IP hash* hoặc *consistent hashing*: cùng một khoá (IP, user id) luôn tới cùng server.
- *Power of two choices*: chọn ngẫu nhiên 2 server, lấy cái ít tải hơn. Gần tốt bằng least
  connections mà không cần biết toàn bộ trạng thái.
- ⚠️ *Sticky session* (gắn user với một server cố định):
  - Làm lệch tải.
  - Mất session khi server đó chết.
  - Nên ưu tiên app stateless, session để ở Redis.

*Health check*
- *Active*: LB định kỳ gọi `/health` của từng backend.
- *Passive*: LB đếm lỗi của request thật, ví dụ `max_fails` của Nginx.
- ⚠️ Health check "sâu" (có kiểm tra DB): DB chậm là **mọi** backend cùng fail, cả cụm bị đánh
  dấu chết, kể cả những request không cần DB.
- Nên tách hai loại:
  - *Liveness*: process còn sống không. Fail thì restart.
  - *Readiness*: đã sẵn sàng nhận request chưa. Fail thì tạm ngừng gửi request tới.

*Connection draining*
- *Connection draining* (AWS gọi là *deregistration delay*) là quy trình gỡ một backend ra mà
  không làm rơi request:
  1. LB ngừng gửi request mới tới backend đó.
  2. Các request đang chạy được làm cho xong.
  3. Hết thời gian chờ thì backend mới bị gỡ hẳn.
- Phải phối hợp với *graceful shutdown* của app (app nhận tín hiệu tắt thì làm nốt việc rồi mới
  thoát).

*CDN*
- *CDN* là mạng server cache đặt gần người dùng. Lợi ích: nhanh hơn, giảm tải *origin* (server
  gốc của bạn), hấp thụ DDoS.
- Làm mới nội dung: *invalidation* theo path, hoặc dùng tên file có hash (module 2.3).
- ⚠️ CDN cache nhầm response cá nhân là sự cố lộ dữ liệu. Nguyên nhân hay gặp:
  - Response thiếu `Cache-Control: private`.
  - Cache key không bao gồm cookie.
- ⚠️ Nếu chỉ muốn truy cập qua CDN thì origin phải chặn truy cập trực tiếp, không thì kẻ tấn
  công bỏ qua CDN và WAF.

**Đọc**
- gRPC blog: [gRPC Load Balancing](https://grpc.io/blog/grpc-load-balancing/)
- Nginx: [HTTP Load Balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) (thuật toán, health check passive)
- AWS: [Application Load Balancer attributes](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html) (idle timeout, deregistration delay)
- Kubernetes: [Pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination) (vì sao cần `preStop`)

**Nắm chắc khi**
- [ ] Giải thích được vì sao 3 pod gRPC sau NLB có một pod 100% CPU, hai pod rảnh
- [ ] Thiết kế được endpoint `/health` và `/ready` cho app Laravel, nói cái nào kiểm tra DB và vì sao

#### 2.8 Timeout và mã lỗi giữa proxy và app

**Vì sao cần học:** Timeout đặt sai là cách phổ biến nhất để một dependency chậm kéo sập cả hệ
thống. 502, 504, 499 là ba mã bạn sẽ gặp khi trực sự cố, và mỗi mã chỉ về một nguyên nhân khác
nhau. Câu "đặt timeout và retry thế nào" gần như luôn có ở vòng system design.

**Học gì**

*Các loại timeout*
- *Connect timeout*: thời gian chờ mở kết nối (TCP + TLS). Nên ngắn, vài giây.
- *Read timeout*: thời gian chờ **giữa hai lần đọc** được dữ liệu.
- *Write timeout*: thời gian chờ gửi được dữ liệu đi.
- *Idle timeout*: kết nối rảnh bao lâu thì bị đóng.
- *Deadline tổng*: thời gian tối đa cho cả request.
- ⚠️ Read timeout **không phải** tổng thời gian. Server nhả từng byte một, mỗi byte cách nhau dưới
  read timeout, thì giữ được kết nối mãi. Cần thêm deadline tổng.

*Mặc định nguy hiểm*
- Nhiều HTTP client mặc định chờ vô hạn. Một dependency treo là mọi worker lần lượt kẹt ở đó, và
  app hết worker.
  - Go: `http.Client{}` không có timeout.
  - Guzzle: mặc định `timeout = 0`, tức vô hạn.
  - Laravel `Http`: mặc định 30 giây.

*Timeout budget*
- Tầng ngoài phải lớn hơn tầng trong: CDN > LB > Nginx > app > DB. Không thì tầng ngoài bỏ cuộc
  trong khi tầng trong vẫn làm, tốn tài nguyên vô ích.
- *Propagate deadline*: truyền thời gian còn lại xuống các lời gọi bên dưới, để tầng dưới không
  làm việc mà tầng trên đã bỏ. Ví dụ Go `context`, gRPC deadline.

*Retry*
- Chỉ retry request idempotent (module 1.3).
- Có *backoff* (chờ lâu dần giữa các lần) và *jitter* (cộng thêm một khoảng ngẫu nhiên để các
  client không retry cùng lúc).
- Có giới hạn số lần.
- ⚠️ Retry ở mọi tầng nhân số request theo cấp số nhân. Ví dụ 3 tầng, mỗi tầng gọi tối đa 3 lần,
  thì một request của user có thể thành 3 × 3 × 3 = 27 request tới DB.

*Mã lỗi ở proxy*

| Mã | Ý nghĩa ở proxy | Nguyên nhân hay gặp |
|---|---|---|
| `502 Bad Gateway` | upstream trả lỗi không hợp lệ, từ chối hoặc đóng kết nối | app crash, sai port, FPM chết, keep-alive race |
| `503 Service Unavailable` | không có upstream khả dụng / quá tải | mọi backend fail health check, rate limit, bảo trì |
| `504 Gateway Timeout` | upstream không trả lời kịp | query chậm, dependency treo, hết worker |
| `499` (Nginx) | client đóng kết nối trước khi có response | client timeout ngắn hơn server |

*Keep-alive race*
- ⚠️ Đây là nguyên nhân của 502 "lác đác, không tái hiện được". Chuỗi sự cố:
  1. App đóng kết nối rảnh sau 5 giây. LB giữ kết nối rảnh tới 60 giây.
  2. Một kết nối rảnh được 5 giây, app đóng nó.
  3. Đúng lúc đó LB chọn kết nối này để gửi request mới, trước khi kịp biết nó đã bị đóng.
  4. Request rơi vào kết nối vừa chết, LB trả 502.
- Quy tắc: idle timeout của app phải **lớn hơn** của LB phía trước.
- Ví dụ kinh điển: Node `server.keepAliveTimeout` mặc định 5 giây đặt sau ALB 60 giây.

**Đọc**
- AWS Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- Nginx: [`proxy_read_timeout`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout), [`client_max_body_size`](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size)
- Resilience chi tiết: [18-reliability-observability.md](18-reliability-observability.md)

**Nắm chắc khi**
- [ ] Tạo ra được lần lượt 502, 504, 499 với một app nhỏ sau Nginx, ghi lại cấu hình gây ra từng lỗi (bài tập 2)
- [ ] Giải thích được keep-alive race và chọn đúng idle timeout cho app sau ALB
- [ ] Tính được số request thực tế tới DB khi 3 tầng mỗi tầng retry 3 lần

---

### Chặng 3: Senior 🔴

#### 3.1 TCP chuyên sâu: hiệu năng, port exhaustion, SYN flood

**Vì sao cần học:** Các sự cố ở module này hiếm nhưng rất khó chẩn đoán nếu không biết cơ chế:
request chậm đúng 40 ms, lỗi `cannot assign requested address` khi gọi API nội bộ, client
connect timeout trong khi server vẫn "khoẻ". Phỏng vấn senior hay đưa một triệu chứng như vậy
rồi hỏi bạn đoán nguyên nhân.

**Học gì**

*Nagle và delayed ACK*
- *Nagle* là thuật toán gom các gói nhỏ: khi còn dữ liệu đã gửi mà chưa được ACK, TCP giữ lại
  gói nhỏ tiếp theo để gộp chung.
- *Delayed ACK*: bên nhận không ACK ngay, mà chờ một chút để gộp ACK với dữ liệu trả về.
- ⚠️ Hai cơ chế gặp nhau khi app theo mẫu write-write-read (gửi header, gửi body, rồi chờ đọc):
  1. Gói đầu đi, chưa được ACK.
  2. Nagle giữ gói thứ hai lại chờ ACK.
  3. Bên kia delayed ACK, chờ thêm dữ liệu.
  4. Hai bên chờ nhau, trễ cỡ vài chục ms.
- `TCP_NODELAY` tắt Nagle. Go bật sẵn option này.

*Flow control và congestion control*
- *Flow control*: bên nhận quảng bá *receive window*, tức "tôi còn nhận thêm được bao nhiêu byte".
  Bên gửi không được gửi vượt số đó.
- *Congestion control*: bên gửi tự đoán mạng chịu được bao nhiêu, qua *congestion window* (cwnd).
  - *Slow start*: kết nối mới bắt đầu với cwnd nhỏ, tăng theo cấp số nhân cho tới khi mất gói.
  - Linux mặc định dùng thuật toán CUBIC. *BBR* là thuật toán khác, dựa trên đo bandwidth và RTT
    thay vì chờ mất gói.
- Hệ quả:
  - Kết nối mới chưa đạt tốc độ tối đa ngay. Thêm một lý do để tái dùng kết nối.
  - *Bandwidth-delay product* (băng thông × RTT) là lượng dữ liệu "đang trên đường". Đường truyền
    nhanh mà xa thì BDP lớn, cần window lớn mới tận dụng hết.

*Port exhaustion phía client*
- Mỗi kết nối được xác định bởi *4-tuple* (IP nguồn, port nguồn, IP đích, port đích). Khi bạn gọi
  ra ngoài, OS chọn port nguồn trong dải *ephemeral port*, mặc định 32768–60999, khoảng 28 nghìn
  port.
- Phép tính:
  - Không keep-alive, mỗi kết nối để lại `TIME_WAIT` 60 giây, giữ port đó.
  - Tới **một đích** cố định, tối đa khoảng 28.000 / 60 ≈ 470 kết nối mới mỗi giây.
- Hay gặp ở:
  - App gọi API nội bộ mà không tái dùng kết nối.
  - Nginx gọi upstream không có keepalive (module 2.5).
  - NAT gateway, vì mọi máy phía sau dùng chung IP của nó (module 3.5).
- Triệu chứng: lỗi `cannot assign requested address` (`EADDRNOTAVAIL`).
- Cách xử lý:
  - Keep-alive hoặc pool. Đây là cách đúng nhất.
  - Thêm IP đích hoặc IP nguồn, vì mỗi cặp IP có dải port riêng.
  - Mở rộng `ip_local_port_range`.

*Hàng đợi khi accept*
- Kernel giữ hai hàng đợi cho mỗi socket đang nghe:
  - *SYN queue*: kết nối nửa mở, mới nhận SYN. Giới hạn bởi `tcp_max_syn_backlog`.
  - *Accept queue*: kết nối đã bắt tay xong, chờ app gọi `accept()`. Giới hạn bởi tham số backlog
    của `listen()` và `somaxconn` (mặc định 4096 từ kernel 5.4).
- ⚠️ Accept queue đầy (app nhận không kịp) thì kết nối mới bị drop. Client thấy connect timeout
  dù server vẫn "còn sống".
- Quan sát:
  - `ss -ltn`: với socket đang nghe, `Recv-Q` là số kết nối đang chờ trong accept queue, `Send-Q`
    là giới hạn.
  - `nstat`: bộ đếm `ListenOverflows` tăng là queue đã tràn.

*SYN flood*
- Kẻ tấn công gửi hàng loạt SYN (thường giả IP nguồn) và không bao giờ gửi ACK. SYN queue đầy,
  người dùng thật không kết nối được.
- *SYN cookies* (`net.ipv4.tcp_syncookies`) chống lại như sau:
  1. Server không lưu state gì cho SYN mới.
  2. Server mã hoá thông tin cần thiết vào chính sequence number của SYN-ACK.
  3. Chỉ khi ACK hợp lệ quay về (mang theo số đó + 1), server mới giải mã và dựng kết nối.
- Giới hạn: cookie mã hoá được ít TCP option hơn một handshake bình thường.
- Tấn công lớn được chặn ở tầng trên: CDN, anycast, dịch vụ chống DDoS của cloud.

**Đọc**
- HPBN: chương [Building Blocks of TCP](https://hpbn.co/building-blocks-of-tcp/) (flow control, slow start, BDP)
- Cloudflare: [SYN packet handling in the wild](https://blog.cloudflare.com/syn-packet-handling-in-the-wild/) (SYN queue, accept queue, SYN cookies, cách quan sát)
- [RFC 4987](https://www.rfc-editor.org/rfc/rfc4987): TCP SYN flooding attacks and common mitigations
- Kernel docs: [ip-sysctl](https://docs.kernel.org/networking/ip-sysctl.html) (`tcp_syncookies`, `ip_local_port_range`, `tcp_max_syn_backlog`, `somaxconn`)

**Nắm chắc khi**
- [ ] Tính được số kết nối mới/giây tối đa tới một đích không keep-alive, và giải thích ba cách nâng giới hạn
- [ ] Chỉ ra được trong `ss -ltn` dấu hiệu accept queue đầy
- [ ] Giải thích được SYN cookies hoạt động thế nào mà server không cần giữ state

#### 3.2 DNS chuyên sâu

**Vì sao cần học:** Nhiều sự cố "DNS đã đổi mà app vẫn gọi IP cũ" không nằm ở DNS server mà ở
các lớp cache trong app, trong JVM, trong connection pool. Trên Kubernetes, cấu hình DNS mặc
định còn nhân số truy vấn lên nhiều lần. Đây là chủ đề phân biệt người đã vận hành hệ thống thật.

**Học gì**

*Negative caching*
- *Negative caching*: kết quả "tên này không tồn tại" (*NXDOMAIN*) cũng được cache, theo thời
  gian ghi trong record `SOA` (RFC 2308).
- ⚠️ Chuỗi sự cố hay gặp khi tự động tạo subdomain cho khách hàng:
  1. Code gọi thử `shop123.example.com` trước khi record được tạo.
  2. Resolver nhớ "không có tên này".
  3. Record được tạo xong, nhưng resolver vẫn trả "không có" cho tới hết TTL của negative cache.

*DNS làm load balancing*
- Có thể chia tải bằng DNS:
  - Nhiều record `A` cho cùng tên.
  - GeoDNS: trả IP theo vị trí người hỏi.
  - Weighted: trả IP theo tỉ lệ.
  - Failover theo health check.
- Hạn chế:
  - Client cache kết quả, nên đổi không có hiệu lực ngay.
  - DNS không biết tải thật của server.
  - Chuyển đổi chậm theo TTL.
- Vì vậy DNS thường dùng ở tầng toàn cầu (chọn region), còn trong một region thì dùng LB.
- ⚠️ Nhiều resolver và client không tôn trọng TTL. Luôn chờ lâu hơn TTL trước khi tắt máy cũ.

*DNS cache trong app*

| Runtime | Hành vi cache |
|---|---|
| JVM | `networkaddress.cache.ttl` mặc định 30 giây, negative cache 10 giây |
| Go | Resolver thuần Go không cache |
| Node | `dns.lookup` gọi `getaddrinfo` trên threadpool, không cache |
| PHP, glibc | Phụ thuộc OS, không cache trừ khi máy có `nscd`, `systemd-resolved` hoặc dnsmasq |

- JVM: Security Manager đã bị vô hiệu vĩnh viễn từ JDK 24 (JEP 486), nên hành vi cũ "cache vĩnh
  viễn khi có security manager" không còn áp dụng.
- ⚠️ Không cache mà gọi nhiều thì DNS server thành *bottleneck ẩn*: mỗi request PHP gọi Redis
  bằng tên host là một truy vấn DNS.

*Kết nối cũ không phân giải lại*
- ⚠️ DNS chỉ được hỏi khi **mở** kết nối. Kết nối đã mở thì cứ trỏ vào IP cũ.
- Ví dụ: DB failover, record DNS của DB đổi sang máy mới. Nhưng connection pool (Java, Go, worker
  chạy lâu như Horizon, Octane) vẫn giữ kết nối tới máy cũ.
- Cách xử lý: giới hạn thời gian sống của mỗi kết nối trong pool (`maxLifetime`), để kết nối được
  mở lại định kỳ và phân giải lại.

*Kubernetes và ndots*
- File `resolv.conf` trong pod mặc định có `ndots:5` và nhiều `search` domain.
- `ndots:5` nghĩa là: tên có ít hơn 5 dấu chấm thì bị coi là "tên ngắn", và được thử ghép với từng
  search domain **trước** khi thử tên gốc.
- ⚠️ Ví dụ: `api.stripe.com` chỉ có 2 dấu chấm, nên bị thử `api.stripe.com.default.svc.cluster.local`,
  `api.stripe.com.svc.cluster.local`... rồi mới tới `api.stripe.com`. Mỗi lần thử có thể là cả
  truy vấn `A` lẫn `AAAA`.
- Cách xử lý:
  - Dùng *FQDN* (tên đầy đủ) có dấu chấm cuối: `api.stripe.com.`.
  - Hoặc hạ `ndots` qua `dnsConfig` của pod.

**Đọc**
- [RFC 2308](https://www.rfc-editor.org/rfc/rfc2308) (negative caching): mục 5
- [JEP 486: Permanently Disable the Security Manager](https://openjdk.org/jeps/486)
- Kubernetes: [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/), mục [Pod's DNS Config](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#pod-dns-config)

**Nắm chắc khi**
- [ ] Giải thích được vì sao sau khi DB failover, app vẫn lỗi 10 phút dù DNS đã đổi, kể đủ các lớp cache
- [ ] Đếm được số truy vấn DNS một pod gửi đi khi gọi `api.stripe.com` với `ndots:5` và 3 search domain

#### 3.3 HTTP request smuggling và desync

**Vì sao cần học:** Request smuggling là lỗ hổng ở ranh giới giữa các proxy, nên kiểm tra code
app không bao giờ thấy nó. Hiểu nó giúp bạn đánh giá rủi ro khi xếp chồng CDN, LB, Nginx và app
server của nhiều hãng. Đây là câu hỏi senior thiên về bảo mật.

**Học gì**

*Bản chất*
- Front-end (CDN, LB, Nginx) và back-end (app server) dùng chung một kết nối được tái dùng cho
  request của nhiều người.
- Nếu hai bên xác định **ranh giới request** khác nhau (request này kết thúc ở byte nào), thì:
  1. Kẻ tấn công gửi một request mơ hồ.
  2. Front-end nghĩ đó là một request trọn vẹn và chuyển hết đi.
  3. Back-end chỉ đọc một phần, phần dư nằm lại trên kết nối.
  4. Back-end hiểu phần dư là **đầu của request tiếp theo**, mà request tiếp theo là của người
     dùng khác.
- HTTP/1.1 có hai cách báo độ dài body:
  - `Content-Length` (CL): số byte.
  - `Transfer-Encoding: chunked` (TE): body chia khúc, khúc độ dài 0 là kết thúc.

*Các biến thể*
- `CL.TE`: front-end tin `Content-Length`, back-end tin `Transfer-Encoding: chunked`.
- `TE.CL`: ngược lại.
- `TE.TE`: cả hai hỗ trợ TE, nhưng một bên bị lừa bỏ qua `Transfer-Encoding` bằng header dị dạng
  (ví dụ viết sai chữ hoa, thêm khoảng trắng).
- HTTP/2 downgrade (`H2.CL`, `H2.TE`): front-end nói HTTP/2 với client rồi chuyển xuống HTTP/1.1
  cho back-end, và dịch sai độ dài.
- `CL.0`: back-end bỏ qua body hoàn toàn.

*Hậu quả*
- Vượt WAF hay kiểm soát truy cập đặt ở front-end, vì front-end không thấy request bị giấu.
- Đầu độc cache: response độc bị cache cho URL bình thường.
- Cướp request của người khác, kể cả cookie của họ.

*Phòng*
- Dùng HTTP/2 (hoặc cao hơn) tới tận back-end khi có thể. HTTP/2 có frame với độ dài rõ ràng.
- Front-end chuẩn hoá hoặc từ chối request mơ hồ: có cả `Content-Length` lẫn `Transfer-Encoding`,
  hoặc header dị dạng.
  - RFC 9112 coi request có cả hai header là dấu hiệu smuggling. Server được phép từ chối, và bắt
    buộc đóng kết nối sau khi trả lời.
- Giữ proxy và server được cập nhật. Không tự viết parser HTTP.
- Liên hệ PHP: Nginx trước PHP-FPM nói FastCGI (có độ dài rõ ràng trong từng record), nên ít bị
  hơn một chuỗi nhiều proxy HTTP/1.1 khác hãng.

**Đọc**
- PortSwigger: [HTTP request smuggling](https://portswigger.net/web-security/request-smuggling) (làm các lab cơ bản)
- PortSwigger Research: [HTTP/1.1 must die](https://portswigger.net/research/http1-must-die) (2025, vì sao vấn đề chưa hết)
- RFC 9112: mục [6.3 Message Body Length](https://www.rfc-editor.org/rfc/rfc9112#section-6.3)

**Nắm chắc khi**
- [ ] Viết được tay một request `CL.TE` và giải thích front-end và back-end mỗi bên thấy gì
- [ ] Nêu được 3 biện pháp phòng và cái nào bạn áp dụng được cho hệ thống hiện tại

#### 3.4 Realtime: SSE, WebSocket và scale

**Vì sao cần học:** Thông báo realtime, tiến trình job, stream câu trả lời từ LLM, chat đều cần
server đẩy dữ liệu xuống client. Với PHP, chọn sai cơ chế là cạn worker FPM. Câu "SSE hay
WebSocket" và "scale 1 triệu kết nối WebSocket thế nào" là câu system design phổ biến.

**Học gì**

*Bốn cơ chế*

| | Cơ chế | Hướng | Ưu | Nhược |
|---|---|---|---|---|
| Polling | hỏi mỗi N giây | client → server | đơn giản, stateless | trễ, tốn request rỗng |
| Long polling | server giữ request tới khi có dữ liệu | gần như server → client | chạy mọi nơi | giữ connection, phức tạp timeout |
| SSE | 1 response dài, `text/event-stream` | server → client | tự reconnect, `Last-Event-ID`, qua proxy dễ | một chiều, text; HTTP/1.1 giới hạn kết nối/host |
| WebSocket | nâng cấp HTTP (`101 Switching Protocols`) | hai chiều | độ trễ thấp | stateful, cấu hình proxy, tự làm reconnect/heartbeat |

- *SSE* (Server-Sent Events): một response HTTP không bao giờ kết thúc, server ghi thêm từng sự
  kiện. Khi mất kết nối, trình duyệt tự nối lại và gửi `Last-Event-ID` để server gửi tiếp từ sự
  kiện đó.
- *WebSocket*: bắt đầu bằng một request HTTP có header `Upgrade`, server trả `101`, từ đó kết nối
  thành kênh hai chiều riêng.

*Chọn cái nào*
- Thông báo, tiến trình job, stream token từ LLM: SSE thường đủ.
- Chat, game, soạn thảo chung (*collaborative editing*): WebSocket.
- Tần suất cập nhật thấp: polling vẫn ổn và đơn giản nhất.

*PHP-FPM và kết nối dài*
- ⚠️ Mỗi kết nối SSE hay WebSocket giữ một worker FPM **suốt đời kết nối**. 50 worker thì 50 user
  mở trang thông báo là hết worker cho mọi request khác.
- Cách làm: dùng dịch vụ riêng như Laravel Reverb, Soketi, Pusher, Mercure, hoặc một runtime chạy
  lâu. App Laravel chỉ publish sự kiện sang dịch vụ đó.

*Scale WebSocket*
- Mỗi kết nối gắn với một node. Muốn gửi cho user X thì phải biết X đang ở node nào. Hai cách:
  - Pub/sub (Redis, NATS, Kafka): publish một lần, mọi node nhận, node nào giữ X thì gửi.
  - Registry "user → node": tra rồi gửi thẳng tới node đó.
- Sticky session chỉ cần khi handshake nhiều bước, ví dụ Socket.IO lùi về long polling.
- ⚠️ LB và proxy có idle timeout, cắt kết nối rảnh. Gửi *heartbeat* (ping định kỳ) với chu kỳ ngắn
  hơn idle timeout.
- ⚠️ *Reconnect storm*: deploy hay restart một node làm hàng chục nghìn client nối lại cùng lúc.
  - Phía client: backoff + jitter.
  - Phía server: drain từng node một, từ từ.
- ⚠️ Giới hạn tài nguyên:
  - Mỗi kết nối tốn một fd và một ít RAM.
  - Đi qua proxy thì còn tốn port (module 3.1).
  - Autoscale theo **số kết nối**, không theo CPU, vì kết nối rảnh gần như không tốn CPU.
- Tin gửi đúng lúc client mất kết nối: pub/sub không lưu lại. Cần lưu tin và cho client lấy bù
  theo *offset* (vị trí tin cuối đã nhận).
- Nginx phải chuyển header `Upgrade`/`Connection` và tăng `proxy_read_timeout`.

**Đọc**
- MDN: [Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events), [WebSockets API](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- Nginx: [WebSocket proxying](https://nginx.org/en/docs/http/websocket.html)
- [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455) (WebSocket): mục 1.3 (opening handshake), 5.5.2 (ping/pong)
- Messaging và pub/sub: [12-messaging.md](12-messaging.md)

**Nắm chắc khi**
- [ ] Chọn được giữa SSE và WebSocket cho 3 tính năng cụ thể và bảo vệ được lựa chọn
- [ ] Thiết kế được hệ chat 1 triệu kết nối: số node, fan-out, heartbeat, reconnect storm, lấy bù tin
- [ ] Giải thích được vì sao endpoint SSE viết bằng Laravel trên FPM làm cạn worker

#### 3.5 Mạng cloud, container, anycast

**Vì sao cần học:** App chạy trên cloud và container thì mạng có thêm nhiều tầng ảo: VPC,
subnet, NAT, security group, Service của Kubernetes. Chọn sai từ đầu (ví dụ dải IP trùng) rất
khó sửa về sau, còn NAT gateway có thể âm thầm làm hoá đơn tăng vọt. Phỏng vấn hay yêu cầu vẽ
sơ đồ mạng cho một app đơn giản.

**Học gì**

*VPC và subnet*
- *VPC* (Virtual Private Cloud) là mạng riêng ảo của bạn trên cloud, chia thành nhiều *subnet*.
- *Subnet public*: có route ra *Internet Gateway*. Đặt LB, *bastion* (máy trung gian để SSH vào
  vùng private).
- *Subnet private*: không ra Internet trực tiếp. Đặt app, DB. Muốn gọi ra Internet thì đi qua
  *NAT gateway*.
- ⚠️ NAT gateway tính tiền theo GB. Gọi S3 qua NAT là tốn tiền vô ích. Dùng *VPC endpoint* để đi
  thẳng tới S3 trong mạng AWS.
- ⚠️ NAT gateway cũng có giới hạn port theo từng đích (port exhaustion, module 3.1).
- ⚠️ Chọn CIDR của VPC trùng mạng văn phòng hay VPC khác thì về sau không *peering* (nối hai VPC)
  hay VPN được.
- AWS giữ lại 5 địa chỉ trong mỗi subnet, nên `/24` chỉ dùng được 251 địa chỉ.

*Security group và NACL*

| | Security group | NACL |
|---|---|---|
| Gắn vào | *ENI* (card mạng ảo của máy) | Subnet |
| Stateful? | Có: cho chiều đi thì chiều về tự được phép | Không: phải mở cả hai chiều |
| Luật | Chỉ có allow | Có cả allow và deny |
| Tham chiếu | Tham chiếu được SG khác ("cho phép mọi máy thuộc SG app") | Chỉ theo dải IP |

*Container*
- Docker bridge: mỗi container có IP riêng trong một mạng ảo. *Publish port* (`-p 8080:80`) là NAT
  từ port của máy host vào container.
- Docker Compose: các container gọi nhau bằng **tên service**, ví dụ `mysql:3306`.
- ⚠️ `localhost` trong container là **chính container đó**, không phải máy host. App Laravel
  trong container đặt `DB_HOST=127.0.0.1` sẽ không thấy MySQL ở container khác.

*Kubernetes*
- Mỗi pod có một IP riêng, nhưng pod chết là IP đổi.
- *Service* cho một IP ảo ổn định và một tên DNS: `<service>.<namespace>.svc.cluster.local`.
  Trong cùng namespace chỉ cần gọi `<service>`.

*Service discovery*
- *Service discovery* là cách một service tìm ra địa chỉ của service khác.
  - *Client-side*: client hỏi registry rồi tự chọn instance. Ví dụ Consul, Eureka.
  - *Server-side*: client gọi một địa chỉ cố định, hạ tầng chọn giúp. Ví dụ K8s Service, ALB.
  - DNS là dạng đơn giản nhất.
- *Service mesh* (Istio, Linkerd) đặt proxy cạnh mỗi service để lo discovery, mTLS, retry,
  metric mà app không cần code.

*Anycast*
- *Anycast*: cùng một IP được quảng bá qua *BGP* (giao thức định tuyến giữa các mạng lớn) từ
  nhiều nơi. Người dùng được đưa tới điểm gần nhất theo BGP.
- Dùng cho DNS công cộng (`1.1.1.1`), CDN, chống DDoS (lưu lượng tấn công bị chia ra nhiều nơi).
- ⚠️ Route BGP đổi giữa chừng có thể đưa gói tới điểm khác, làm đứt kết nối TCP dài.
- Chi tiết cloud: [19-devops-cloud.md](19-devops-cloud.md).

**Đọc**
- AWS: [What is Amazon VPC?](https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html), [Infrastructure security](https://docs.aws.amazon.com/vpc/latest/userguide/infrastructure-security.html) (so sánh security group và NACL)
- Kubernetes: [Service](https://kubernetes.io/docs/concepts/services-networking/service/), [DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/#services)
- Cloudflare: [The Road to QUIC](https://blog.cloudflare.com/the-road-to-quic/) (có phần về anycast và vì sao QUIC hợp với edge)

**Nắm chắc khi**
- [ ] Vẽ được sơ đồ VPC cho app LB + 3 app server + MySQL + Redis, ghi rõ subnet, route, security group (bài tập 5)
- [ ] Viết được FQDN của Service `mysql` trong namespace `prod` và giải thích pod ở namespace khác gọi thế nào

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Gõ `https://example.com` rồi Enter, chuyện gì xảy ra?** (1.5)
- Ý phải có: khung URL → cache → DNS → TCP → TLS → request → hạ tầng → app → response → render
- Điểm cộng: tự chọn đào sâu phần backend (LB, Nginx, FPM, DB); nói được chỗ nào tái dùng kết nối
- Red flag: kể lan man một bước và bỏ sót DNS hoặc TLS

**2. TCP khác UDP thế nào? Cho ví dụ ứng dụng.** (1.1)
- Ý phải có: kết nối, thứ tự, gửi lại, flow/congestion control so với không; DNS, video, game, QUIC
- Điểm cộng: TCP là byte stream không có ranh giới message; QUIC tự làm tin cậy trên UDP

**3. Vì sao HTTP là stateless? Server "nhớ" người dùng đã đăng nhập bằng cách nào?** (1.3)
- Ý phải có: mỗi request độc lập; cookie session id (state ở server) hoặc token
- Điểm cộng: session ở Redis để app scale ngang; đánh đổi session và JWT

**4. `HttpOnly`, `Secure`, `SameSite` dùng để làm gì?** (1.3)
- Ý phải có: chống JS đọc cookie (XSS), chỉ gửi qua HTTPS, kiểm soát gửi cookie cross-site (CSRF)
- Điểm cộng: `SameSite=None` bắt buộc `Secure`; bẫy `Domain` gửi cookie tới mọi subdomain

**5. Method nào safe, method nào idempotent?** (1.3)
- Ý phải có: safe `GET`, `HEAD`, `OPTIONS` (và vì thế cũng idempotent); thêm `PUT`, `DELETE` là idempotent; `POST`, `PATCH` không
- Điểm cộng: idempotent nói về hiệu ứng phía server, không phải response giống nhau; `Idempotency-Key` cho `POST` thanh toán
- Red flag: "GET idempotent nhưng không safe"

**6. Reverse proxy là gì? Vì sao đặt Nginx trước PHP-FPM?** (2.5, 2.6)
- Ý phải có: đại diện server; TLS, static file, buffering client chậm, rate limit, che backend; FPM không nói HTTP
- Điểm cộng: `proxy_buffering`/buffer FastCGI giải phóng worker FPM sớm khi client chậm

### 🟡 Mid

**7. Vì sao handshake cần 3 bước? `TIME_WAIT` là gì, vì sao server có rất nhiều?** (1.1, 2.1)
- Ý phải có: trao đổi và xác nhận ISN hai chiều; `TIME_WAIT` ở bên đóng trước, 60 giây trên Linux; server nhiều khi server chủ động đóng
- Điểm cộng: `CLOSE_WAIT` mới là bug app; `tcp_tw_recycle` đã bị bỏ
- Red flag: "bật `tcp_tw_recycle` là hết"

**8. HTTP/2 cải thiện gì so với HTTP/1.1? Vì sao vẫn cần HTTP/3?** (2.2)
- Ý phải có: multiplex, binary, HPACK; HOL blocking vẫn còn ở TCP; QUIC gộp handshake, stream độc lập, connection migration
- Điểm cộng: LB nói HTTP/1.1 với backend; HTTP/3 lùi về HTTP/2 khi UDP bị chặn

**9. `no-cache` khác `no-store` thế nào? `ETag` hoạt động ra sao?** (2.3)
- Ý phải có: lưu nhưng revalidate so với không lưu; `If-None-Match` → `304`
- Điểm cộng: `private` cho dữ liệu cá nhân; `Vary`; `immutable` cho asset có hash

**10. 502 và 504 khác nhau thế nào? Điều tra mỗi loại ra sao?** (2.8, 2.6)
- Ý phải có: 502 upstream trả sai/đóng/từ chối; 504 upstream không trả kịp; đọc error log của Nginx để biết chính xác
- Điểm cộng: nói được các dòng log FastCGI tương ứng; keep-alive race gây 502 lác đác; 504 mà worker FPM vẫn chạy tiếp

**11. Load balancer L4 và L7 khác nhau thế nào? Khi nào chọn cái nào?** (2.7)
- Ý phải có: nhìn thấy gì, làm được gì, cân bằng theo kết nối hay request
- Điểm cộng: gRPC/HTTP/2 qua L4 dồn tải; L4 cho protocol không phải HTTP, TLS passthrough

**12. TLS 1.3 nhanh hơn TLS 1.2 ở đâu? 0-RTT có rủi ro gì?** (2.4)
- Ý phải có: 1 RTT nhờ gửi key share ngay; 0-RTT bị replay nên chỉ cho request idempotent
- Điểm cộng: forward secrecy bắt buộc; key exchange post-quantum `X25519MLKEM768` làm ClientHello to hơn

**13. Polling, SSE, WebSocket: chọn cái nào cho thông báo realtime?** (3.4)
- Ý phải có: SSE đủ cho một chiều server → client; WebSocket khi cần hai chiều độ trễ thấp
- Điểm cộng: SSE với PHP-FPM chiếm worker; proxy buffering; heartbeat so với idle timeout

**14. Upload file 20 MB bị `413`, sửa xong lại bị `504`.** (2.6, 2.8)
- Ý phải có: `client_max_body_size` và `upload_max_filesize`/`post_max_size`; 504 do timeout đọc giữa Nginx và FPM khi xử lý lâu
- Điểm cộng: presigned URL để client upload thẳng lên object storage; xử lý file trong queue

**15. Nginx trước PHP-FPM: đặt timeout các tầng thế nào?** (2.6)
- Ý phải có: tầng ngoài lớn hơn tầng trong; `fastcgi_read_timeout`, `request_terminate_timeout`, timeout HTTP client trong app
- Điểm cộng: `max_execution_time` không tính I/O trên Linux; việc dài đưa vào queue thay vì kéo timeout
- Red flag: đặt mọi timeout 300 giây cho "chắc"

### 🔴 Senior

**16. Service A gọi B qua HTTP, tải cao thì A báo `cannot assign requested address`.** (3.1)
- Ý phải có: hết ephemeral port; đếm `TIME_WAIT` bằng `ss`; A tạo client mới mỗi request hoặc không đóng body
- Điểm cộng: tính được giới hạn ~470 kết nối/giây/đích; Nginx cũ không keepalive tới upstream; NAT gateway cũng bị

**17. Có lỗi 502 lác đác, không theo quy luật, app không có log lỗi.** (2.8, 2.7)
- Ý phải có: keep-alive race (so idle timeout hai bên); pod tắt khi còn trong endpoint (thiếu `preStop`/draining); OOMKilled
- Điểm cộng: đối chiếu thời điểm 502 với deploy/restart và log LB; với FPM thì `upstream prematurely closed` khi worker bị kill

**18. Đổi IP server, cập nhật DNS xong nhưng một số client vẫn gọi IP cũ.** (3.2)
- Ý phải có: TTL chưa hạ trước; resolver/client không tôn trọng TTL; JVM và connection pool giữ IP cũ
- Điểm cộng: negative caching khi tạo tên mới; giữ server cũ, theo dõi traffic còn vào rồi mới tắt

**19. Lấy IP thật của client thế nào cho an toàn?** (2.5)
- Ý phải có: chỉ tin XFF khi request đến từ proxy đã biết; đọc từ phải sang trái bỏ proxy tin cậy
- Điểm cộng: cấu hình ở một chỗ (Nginx real_ip hoặc `TrustProxies`); hậu quả nếu sai: rate limit, audit log, allowlist bị vượt
- Red flag: lấy phần tử đầu tiên của XFF

**20. HTTP request smuggling là gì? Hệ thống của bạn có thể bị không?** (3.3)
- Ý phải có: front-end và back-end hiểu ranh giới request khác nhau (`CL.TE`, `TE.CL`, HTTP/2 downgrade); hậu quả vượt WAF, đầu độc cache, cướp request
- Điểm cộng: HTTP/2 tới back-end, từ chối request mơ hồ, cập nhật proxy; đánh giá được chuỗi proxy thật của hệ thống mình

**21. SYN flood là gì? Server tự bảo vệ thế nào?** (3.1)
- Ý phải có: làm đầy SYN queue bằng kết nối nửa mở; SYN cookies không lưu state; phân biệt với accept queue đầy do app `accept()` chậm
- Điểm cộng: tấn công lớn chặn ở CDN/anycast/dịch vụ DDoS; quan sát bằng `nstat`

**22. Sau khi chuyển sang CDN, một số người dùng thấy trang tài khoản của người khác.** (2.3, 2.7)
- Ý phải có: response cá nhân bị cache vì thiếu `private`/`no-store` hoặc cache key bỏ qua cookie; purge ngay, sửa header, không cache path động
- Điểm cộng: xử lý như sự cố lộ dữ liệu (báo cáo, đánh giá phạm vi); test header cache trong CI

**23. Scale hệ chat WebSocket lên 1 triệu kết nối.** (3.4)
- Ý phải có: số kết nối mỗi node (fd, RAM); pub/sub fan-out giữa node; heartbeat so với idle timeout
- Điểm cộng: reconnect storm khi deploy; lưu tin để lấy bù; autoscale theo số kết nối; tách gateway kết nối khỏi logic nghiệp vụ

**24. Sau khi DB failover, app Java vẫn lỗi kết nối 10 phút dù DNS đã đổi.** (3.2)
- Ý phải có: pool giữ kết nối cũ; JVM DNS cache; cần `maxLifetime`, validation khi mượn connection
- Điểm cộng: driver hỗ trợ failover; với PHP-FPM thì mỗi request kết nối mới nên ít bị, trừ persistent connection

**25. Hạn cert sắp xuống 47 ngày. Bạn chuẩn bị gì?** (2.4)
- Ý phải có: tự động hoá cấp và gia hạn (ACME, cert-manager, ACM); alert trước khi hết hạn; kiểm kê mọi nơi có cert (LB, CDN, mTLS nội bộ, app mobile pin cert)
- Điểm cộng: OCSP đã bị Let's Encrypt bỏ, không dựa vào stapling; certificate pinning thành rủi ro lớn hơn khi xoay cert thường xuyên

**26. SSE chạy ở local nhưng trên staging client chỉ nhận dữ liệu sau vài chục giây, hoặc bị ngắt mỗi 60 giây.** (2.5, 3.4)
- Ý phải có: proxy buffering giữ response; ngắt đều là idle/read timeout của proxy/LB; gửi heartbeat định kỳ
- Điểm cộng: nén response cũng gây buffer; `X-Accel-Buffering: no`

---

## Bài tập tự làm

1. **Đo độ trễ.** Dùng `curl -w` đo thời gian DNS, TCP, TLS, TTFB tới ba website ở các vị trí địa lý khác nhau. Giải thích vì sao các con số khác nhau, và lần gọi thứ hai khác lần đầu thế nào.
2. **Tái hiện mã lỗi.** Viết một server HTTP nhỏ (Go hoặc PHP) trả response chậm, đặt sau Nginx trong Docker Compose. Tạo ra được lần lượt 502, 504 và 499, ghi lại cấu hình gây ra từng lỗi. Làm thêm phiên bản với PHP-FPM và ghi lại dòng error log Nginx của từng trường hợp.
3. **Nginx cho Laravel.** Viết cấu hình gồm:
   - Static file, PHP-FPM qua FastCGI dùng `$realpath_root`
   - Upload tối đa 50 MB (kể cả cấu hình PHP tương ứng)
   - Rate limit cho `/login`
   - Real IP sau một LB có dải `10.0.0.0/16`
   - Không cho chạy PHP trong thư mục upload
   - Một endpoint SSE không bị buffer
4. **Header cache.** Thiết kế header cho: file JS có hash trong tên, trang HTML, API công khai danh sách sản phẩm, API `/me`. Giải thích từng lựa chọn.
5. **VPC.** Vẽ sơ đồ VPC cho app gồm LB, 3 app server, MySQL, Redis; ghi rõ subnet, route, security group rule, và đường đi ra Internet của app server.
6. **Port exhaustion.** Viết client gọi một server nội bộ không dùng keep-alive, tăng tốc độ tới khi gặp `cannot assign requested address`. Đếm `TIME_WAIT` lúc đó, rồi bật keep-alive và đo lại.

> Nộp bài vào đây để được review.
