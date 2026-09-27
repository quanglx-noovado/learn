# 11. Cache

> [← Mục lục](README.md) · **[📖 Bài đọc kiến thức](kien-thuc/11-cache.md)** · Trọng tâm: cache ứng dụng bằng **Redis/Valkey** trong stack **PHP/Laravel**: pattern đọc/ghi, invalidation và race condition, stampede/penetration/avalanche, eviction, multi-level cache, đo lường. Đối chiếu Spring và Go.
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
| [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala) (Nishtala và cộng sự, NSDI 2013) | Paper | Bài đọc quan trọng nhất về cache ở quy mô lớn: lease, invalidation qua commit log, nhiều region. Đọc mục 3 (in a cluster) trước |
| [AWS: Database Caching Strategies Using Redis](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/welcome.html) và [Caching best practices](https://aws.amazon.com/caching/best-practices/) | Whitepaper | Cache-aside, write-through, TTL, thundering herd, viết ngắn gọn |
| [Redis docs](https://redis.io/docs/latest/) | Official docs | Eviction, TTL, client-side caching. Phần lớn áp dụng cho [Valkey](https://valkey.io/) |
| [Laravel Cache](https://laravel.com/docs/cache) | Official docs | `remember`, `flexible`, lock, tag, memo, failover |
| [RFC 9111: HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111) và [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching) | RFC + guide | Tầng cache HTTP (browser, CDN, proxy). MDN dễ đọc hơn, RFC để tra |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.5 (replication lag, nguồn gốc nhiều race khi nạp cache), ch.11 (CDC, giữ các hệ thống đồng bộ) (số chương theo bản 1) |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.3 | Biết các tầng cache, dùng cache-aside và TTL đúng, hiểu LRU/LFU | 2–3 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.7 | Vẽ được race khi invalidate, phòng được stampede/penetration/avalanche, vận hành cache trong Laravel không gây sự cố | 7–9 ngày |
| **3. Senior** 🔴 | 3.1–3.3 | Thiết kế cache nhiều tầng, nhất quán ở quy mô lớn, hệ thống sống sót khi cache sập | 5–7 ngày |

Học theo thứ tự: race condition ở chặng 2 chỉ có nghĩa khi đã hiểu cache-aside ở chặng 1, và
chặng 3 là các lời giải công nghiệp (lease, CDC, L1 + L2) cho chính các race đó. Chi tiết về
bản thân Redis (kiểu dữ liệu, persistence, Cluster) nằm ở
[04-nosql-search-storage.md](04-nosql-search-storage.md).

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Các tầng cache

**Vì sao cần học:** Bug "sửa rồi mà người dùng vẫn thấy cũ" thường không nằm ở Redis mà ở một tầng
cache khác: trình duyệt, CDN, hay Nginx. Biết đủ các tầng thì mới debug được. Câu hỏi hay gặp: "kể
các tầng cache", "`no-cache` khác `no-store` thế nào".

**Học gì**

*Cache là gì*
- *Cache* là một bản sao dữ liệu đặt ở chỗ đọc nhanh hơn hoặc gần người dùng hơn nguồn gốc. Đọc từ
  cache thay vì nguồn gọi là *hit*. Không có trong cache, phải đọc nguồn, gọi là *miss*.
- Cái giá của mọi cache: bản sao có thể **cũ** (*stale*) so với nguồn.

*Các tầng, từ gần user tới gần dữ liệu*

| Tầng | Ví dụ | Đặc điểm | Xoá thế nào |
|---|---|---|---|
| Browser | HTTP cache, Service Worker | Nằm trên máy người dùng | Server không xoá được. Asset dùng tên file có hash (`app.3f9a.js`) để đổi file là đổi URL |
| CDN | CloudFront, Cloudflare | Máy chủ đặt gần người dùng, cache theo URL + header `Vary` | Purge API, hoặc chờ TTL |
| Reverse proxy | Nginx `proxy_cache`, Varnish | Đứng trước app server | Purge hoặc chờ TTL |
| App in-process | Map trong memory, Caffeine, APCu | Nhanh nhất, nhưng mỗi instance một bản | Riêng từng instance |
| Distributed | Redis, Memcached | Dùng chung giữa các instance, đi qua mạng | `DEL`, versioned key (module 2.2) |
| DB | InnoDB buffer pool, OS page cache | "Cache miễn phí" có sẵn | DB tự quản lý |

- *In-process* nghĩa là nằm trong bộ nhớ của chính process app. *Distributed* nghĩa là một hệ thống
  cache riêng mà mọi instance app cùng gọi tới.
- ⚠️ CDN cache nhầm response có dữ liệu cá nhân là lộ dữ liệu: người sau thấy trang của người trước.
- Tầng DB thường bị quên: thêm RAM cho DB để dữ liệu nóng nằm hết trong buffer pool đôi khi là đủ,
  không cần thêm Redis.

*Debug "sửa rồi mà không thấy đổi"*
- Mỗi tầng thêm một nơi dữ liệu có thể cũ.
- Đi lần lượt từng tầng từ ngoài vào: trình duyệt, CDN, proxy, cache trong app, Redis, rồi tới
  replica DB.

*HTTP caching*
- Header `Cache-Control` báo cho browser, CDN và proxy cách cache một response:
  - `private`: chỉ browser của người đó được lưu. `public`: shared cache (CDN, proxy) cũng được lưu,
    kể cả khi request có header `Authorization` (response có `max-age` thì shared cache đã lưu được,
    `public` cần nhất trong trường hợp có `Authorization`).
  - `max-age=N`: được dùng lại trong N giây. `s-maxage=N`: như `max-age` nhưng chỉ cho cache dùng
    chung (CDN, proxy).
  - `no-cache`, `no-store`: xem cạm bẫy ngay dưới.
  - `stale-while-revalidate=N`: hết hạn rồi vẫn được trả bản cũ thêm N giây, trong khi làm mới ở
    nền. Ý tưởng này quay lại ở module 2.3.
- *Revalidate* là hỏi lại server "bản tôi đang có còn đúng không":
  - `ETag` là mã phiên bản của response. `Last-Modified` là thời điểm sửa cuối.
  - Browser gửi lại mã đó. Server trả `304 Not Modified` (không gửi lại nội dung) nếu chưa đổi.
- `Vary`: liệt kê các header request làm response khác nhau (ví dụ `Accept-Language`), để cache lưu
  riêng từng biến thể.
- ⚠️ `no-cache` nghĩa là "được lưu, nhưng phải revalidate trước mỗi lần dùng". `no-store` mới là
  "không được lưu".
- Chi tiết HTTP: [02-networking.md](02-networking.md).

**Đọc**
- MDN: [HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching) (đọc hết), [Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control)
- [RFC 5861](https://www.rfc-editor.org/rfc/rfc5861): `stale-while-revalidate` và `stale-if-error`, nguồn gốc của pattern SWR ở module 2.3
- Laravel: [Cache-Control middleware](https://laravel.com/docs/responses#cache-control-middleware) (`cache.headers`)

**Nắm chắc khi**
- [ ] Liệt kê được mọi tầng cache giữa trình duyệt và MySQL trong hệ thống mình đang làm, và cách xoá từng tầng
- [ ] Chọn được header `Cache-Control` cho 3 loại response: asset có hash, trang sản phẩm công khai, trang "đơn hàng của tôi"

#### 1.2 Cache-aside và TTL

**Vì sao cần học:** Cache-aside là pattern dùng trong phần lớn code cache thực tế, và
`Cache::remember` của Laravel chính là nó. Câu "cache-aside hoạt động thế nào" gần như luôn có ở vòng
junior, rồi bị đào tiếp vào TTL và race.

**Học gì**

*Cache-aside*
- *Cache-aside* (còn gọi *lazy loading*): app tự quản lý cache, cache chỉ là chỗ để đồ.
- Luồng đọc:
  1. Đọc cache.
  2. Hit thì trả luôn.
  3. Miss thì đọc DB.
  4. Ghi kết quả vào cache kèm TTL.
  5. Trả kết quả.
- Luồng ghi:
  1. Ghi DB.
  2. **Xoá** key cache tương ứng. Lần đọc sau sẽ miss và nạp bản mới. (Vì sao xoá chứ không cập
     nhật: module 2.2.)
- Trong Laravel:

  ```php
  $user = Cache::remember("user:{$id}:v1", 600, fn () => User::find($id));
  ```

| Ưu | Nhược |
|---|---|
| Đơn giản | Lần đầu đọc một key luôn miss |
| Chỉ cache thứ thật sự được đọc | Có cửa sổ thời gian dữ liệu cũ |
| Redis chết thì app vẫn chạy, chỉ chậm hơn | Logic cache rải khắp code |

*TTL*
- *TTL* (time to live) là thời gian sống của một mục cache. Hết TTL thì mục đó bị coi là miss.
- TTL là **lưới an toàn cuối**: dù code quên xoá cache ở đâu đó, dữ liệu cũng chỉ cũ tối đa bằng TTL.
- Chọn TTL theo câu hỏi nghiệp vụ "chấp nhận dữ liệu cũ bao lâu", không theo cảm tính:
  - Cấu hình hệ thống: vài phút.
  - Giá sản phẩm: ngắn.
  - Tồn kho lúc thanh toán: không đọc cache, đọc thẳng DB.

*Jitter*
- *Jitter* là cộng thêm một khoảng ngẫu nhiên vào TTL:
  `ttl = base + random(0, base * 0.1)`.
- Mục đích: các key được tạo cùng lúc (ví dụ ngay sau deploy) không hết hạn cùng lúc, nên không dồn
  hàng loạt miss vào DB trong một giây (avalanche, module 2.3).

*Bẫy giá trị `null`*
- ⚠️ `Cache::remember` với callback trả `null`: khi đọc lại, `get` trả `null` và không phân biệt
  được với miss. Kết quả là bản ghi không tồn tại thì lần nào cũng xuống DB.
  - Kẻ xấu lợi dụng điều này bằng cách gọi liên tục id không tồn tại. Đây là *penetration*, cách
    phòng ở module 2.3.

**Đọc**
- AWS: [Caching best practices](https://aws.amazon.com/caching/best-practices/) (mục lazy caching, write-through, TTL)
- Laravel: [Retrieve & Store](https://laravel.com/docs/cache#retrieve-store)

**Nắm chắc khi**
- [ ] Viết được cache-aside bằng Redis thuần (không dùng `remember`) và chỉ ra chỗ race có thể xảy ra
- [ ] Chọn và bảo vệ được TTL cho 5 loại dữ liệu trên một trang sản phẩm

#### 1.3 Eviction cơ bản

**Vì sao cần học:** Cache luôn có giới hạn bộ nhớ, nên phải chọn bỏ gì khi đầy. Redis bắt bạn chọn
`maxmemory-policy`, và câu "LRU khác LFU thế nào" là câu lý thuyết cache hay gặp nhất. Chọn sai
policy làm hit ratio giảm mà không ai biết vì sao.

**Học gì**

*Eviction khác expiration*
- *Eviction* là bỏ bớt mục cache vì **đầy bộ nhớ**.
- *Expiration* là mục cache hết hạn vì **hết TTL**.
- Hai việc độc lập: một key còn TTL dài vẫn có thể bị evict khi bộ nhớ đầy.

*Các policy*

| Policy | Bỏ mục nào | Hợp khi | Điểm yếu |
|---|---|---|---|
| LRU (least recently used) | Lâu nhất chưa được dùng | Truy cập cục bộ theo thời gian: thứ vừa dùng dễ được dùng lại | ⚠️ Một lần quét lớn (job đọc toàn bộ sản phẩm một lần) đẩy hết key nóng ra |
| LFU (least frequently used) | Ít được dùng nhất | Tập key nóng ổn định lâu dài | Cần cơ chế giảm dần (*decay*), không thì key từng nóng giữ chỗ mãi |
| FIFO | Vào trước ra trước | Đơn giản | Không quan tâm key có nóng không |
| TTL | Sắp hết hạn nhất | Khi TTL phản ánh độ quan trọng | Phụ thuộc cách đặt TTL |
| Random | Ngẫu nhiên | Rẻ, không cần theo dõi gì | Có thể bỏ nhầm key nóng |

- Ví dụ LRU bị quét lớn phá: cache 1000 mục đang giữ 1000 sản phẩm hot. Một job export đọc lần lượt
  100.000 sản phẩm qua cache. Sau job, cache chỉ còn 1000 sản phẩm cuối của job, toàn thứ không ai
  xem.

*W-TinyLFU*
- Caffeine (thư viện cache của Java) dùng *W-TinyLFU*: kết hợp tần suất (như LFU) và độ mới (như
  LRU). Hit ratio thường tốt hơn LRU thuần trên dữ liệu thật.

**Đọc**
- Redis: [Key eviction](https://redis.io/docs/latest/develop/reference/eviction/) (mục approximated LRU và LFU)
- Caffeine: [Efficiency](https://github.com/ben-manes/caffeine/wiki/Efficiency) (biểu đồ hit ratio của các policy trên trace thật)

**Nắm chắc khi**
- [ ] Cho một chuỗi truy cập 10 key và dung lượng 3, mô phỏng được LRU và LFU bằng tay
- [ ] Nói được một workload mà LRU tệ và LFU tốt, và ngược lại

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Pattern đọc/ghi

**Vì sao cần học:** Ngoài cache-aside còn bốn pattern khác, mỗi cái đổi độ nhất quán lấy tốc độ theo
một cách. Người phỏng vấn mid hay hỏi "write-through khác write-behind thế nào" và "khi nào dám dùng
write-behind", vì đó là chỗ có thể mất dữ liệu.

**Học gì**

*Read-through*
- *Read-through*: app chỉ hỏi cache. Khi miss, **cache tự gọi** hàm nạp dữ liệu (*loader*) rồi lưu
  lại.
  - Ví dụ: Caffeine `LoadingCache` trong Java.
- Khác cache-aside ở chỗ logic nạp nằm tập trung trong cache, không rải trong code gọi.

*Write-through*
- *Write-through*: app ghi vào cache, và cache ghi **đồng bộ** xuống DB trước khi báo xong.
- Cache luôn mới. Cái giá: mỗi lần ghi chậm hơn (ghi hai nơi), và cache đầy cả dữ liệu lạnh (được
  ghi nhưng không ai đọc).

*Write-behind*
- *Write-behind* (còn gọi *write-back*): app ghi vào cache rồi trả về ngay. Cache ghi xuống DB
  **sau**, theo lô.
- Rất nhanh, và gom được nhiều lần ghi thành một. Hợp cho counter, view count.
- ⚠️ Cache sập trước khi flush là **mất dữ liệu** chưa được ghi xuống DB.
  - Giới hạn lượng có thể mất bằng chu kỳ flush: flush mỗi 10 giây thì mất tối đa khoảng 10 giây ghi.

*Refresh-ahead*
- *Refresh-ahead*: tự làm mới key sắp hết hạn **trước khi** nó hết hạn.
- Key nóng không bao giờ miss. Cái giá: tốn công làm mới cả những key không còn ai đọc.

*So sánh*

| Pattern | Độ nhất quán | Tốc độ đọc | Tốc độ ghi | Rủi ro chính |
|---|---|---|---|---|
| Cache-aside | Có cửa sổ cũ, giới hạn bằng TTL | Miss lần đầu | Nhanh (ghi DB, xoá key) | Race khi ghi đồng thời (module 2.2) |
| Read-through | Như cache-aside | Miss lần đầu | Như cache-aside | Như cache-aside |
| Write-through | Cao | Nhanh | Chậm hơn | Cache đầy dữ liệu lạnh |
| Write-behind | DB bị trễ so với cache | Nhanh | Rất nhanh | Mất dữ liệu chưa flush |
| Refresh-ahead | Tốt với key nóng | Không miss với key nóng | Không ảnh hưởng | Làm mới thừa |

**Đọc**
- AWS whitepaper: [Database Caching Strategies Using Redis](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/welcome.html) (phần caching patterns)

**Nắm chắc khi**
- [ ] Vẽ được bảng so sánh 5 pattern theo 4 tiêu chí mà không nhìn tài liệu
- [ ] Nêu được một use case thật cho write-behind và cách giới hạn lượng dữ liệu có thể mất

#### 2.2 Invalidation và race condition

**Vì sao cần học:** Đây là phần bị hỏi vặn nhiều nhất về cache. "Update DB rồi xoá cache hay ngược
lại" có vẻ đơn giản, nhưng cả hai cách đều có race, và người phỏng vấn muốn bạn vẽ được timeline.
Bug thật hay gặp trong Laravel là xoá cache bên trong transaction.

**Học gì**

*Invalidation là gì*
- *Invalidation* là làm cho mục cache cũ không còn được dùng khi dữ liệu gốc đổi.
- *Race condition* ở đây là khi hai request chạy đan xen theo một thứ tự xấu và để lại giá trị cũ
  trong cache.

*Hai cách invalidate*
- **Explicit delete**: ghi DB xong thì xoá key.
  - ⚠️ Phần khó nhất là **biết hết key nào liên quan**. Sửa một sản phẩm thì phải xoá cả key chi
    tiết, các key danh sách chứa nó, trang chủ, kết quả search có nó.
- **Versioned key**: nhét số version vào tên key, ví dụ `product:123:v{version}` hoặc
  `catalog:v{n}:...`.
  - Tăng version thì code đọc key mới, mọi key cũ thành rác và tự hết hạn dần theo TTL.
  - Invalidate cả một nhóm chỉ bằng một lệnh `INCR` trên số version.

*Xoá cache rồi update DB*
- ⚠️ Cửa sổ lỗi rộng:
  1. A xoá cache.
  2. B đọc, miss, đọc DB được giá trị **cũ** (A chưa update).
  3. B ghi giá trị cũ vào cache.
  4. A update DB.
  5. Cache giữ giá trị cũ tới hết TTL.
- Bước 2 chỉ cần xảy ra trong lúc A đang update, việc rất dễ xảy ra.

*Update DB rồi xoá cache (cách thường dùng)*
- ⚠️ Vẫn sai được:
  1. Cache đang trống (vừa hết hạn).
  2. B đọc, miss, đọc DB được giá trị cũ.
  3. A update DB.
  4. A xoá cache (đang trống, không có gì để xoá).
  5. B ghi giá trị cũ vào cache, **sau** khi A đã xoá.
- Điều kiện để lỗi xảy ra: B phải đọc DB trước A ghi, và ghi cache sau A xoá. Tức là lần ghi cache
  của B chậm hơn cả một lần update DB. Xác suất thấp hơn nhiều, nhưng vẫn có, nên luôn có TTL.

*Các lỗi hay gặp khác*
- Xoá cache thất bại (Redis timeout): retry, hoặc đẩy lệnh xoá qua queue hay CDC (module 3.2).
- ⚠️ Xoá cache **trong** transaction, trước khi commit:
  1. Code xoá cache, transaction chưa commit.
  2. Request khác miss, đọc DB, vẫn thấy giá trị cũ (vì chưa commit).
  3. Request đó nạp giá trị cũ vào cache.
  4. Transaction commit, nhưng cache đã cũ.
  - Sửa: xoá **sau** commit. Laravel `DB::afterCommit(...)`, Spring
    `@TransactionalEventListener(phase = AFTER_COMMIT)`.
- ⚠️ Nạp cache từ replica đang lag: replica chưa nhận được thay đổi, nên giá trị cũ vào cache ngay
  sau khi xoá.
  - Sửa: nạp cache từ primary, hoặc delayed double delete.

*Delayed double delete*
- Các bước:
  1. Xoá cache.
  2. Update DB.
  3. Chờ một khoảng lớn hơn thời gian một lần đọc DB + ghi cache, hoặc lớn hơn replica lag.
  4. Xoá cache lần nữa, để dọn giá trị cũ lỡ được nạp trong lúc đó.
- Khoảng chờ là **đoán**, không phải đảm bảo.
- Làm lần xoá thứ hai bất đồng bộ (job queue có delay), không `sleep` trong request.

*Vì sao xoá thay vì set*
- ⚠️ Nếu ghi DB xong thì **set** giá trị mới vào cache, hai lần ghi đồng thời có thể lệch:
  1. A ghi DB = 1.
  2. B ghi DB = 2.
  3. B set cache = 2.
  4. A set cache = 1 (A chậm hơn).
  5. DB là 2, cache là 1.
- Xoá thì không có thứ tự nào để sai: lần đọc sau luôn lấy từ DB.
- Ngoại lệ:
  - Counter dùng `INCR`: phép cộng không phụ thuộc thứ tự.
  - Set kèm version và chỉ ghi nếu version mới hơn bản đang có.
- Muốn nhất quán mạnh thì cache không phải công cụ đúng. Luồng cần chính xác (thanh toán, trừ tồn
  kho) đọc thẳng DB.

**Đọc**
- Scaling Memcache at Facebook: mục 3.2.1 (leases) và 4.1 (invalidation qua commit log)
- DDIA ch.5, mục *Problems with Replication Lag*
- Laravel: [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions) (cùng vấn đề "chạy trước khi commit")

**Nắm chắc khi**
- [ ] Vẽ được timeline race cho cả hai thứ tự (xoá trước, update trước) và chỉ ra điều kiện để lỗi xảy ra
- [ ] Vẽ được timeline "set thay vì xoá" làm cache lệch với DB
- [ ] Giải thích được bug xoá cache trong transaction và sửa được trong code Laravel

#### 2.3 Stampede, penetration, avalanche

**Vì sao cần học:** Ba sự cố này là cách cache làm sập DB. Chúng hay xảy ra đúng lúc tải cao nhất
(flash sale, sau deploy), và câu "phân biệt stampede, penetration, avalanche" gần như chắc chắn gặp
ở vòng mid.

**Học gì**

*Phân biệt ba sự cố*

| Sự cố | Chuyện gì xảy ra | Dấu hiệu |
|---|---|---|
| Stampede (thundering herd) | **Một** key nóng hết hạn, hàng nghìn request cùng miss, cùng chạy một query nặng | Một query giống hệt nhau tăng vọt đúng lúc key hết hạn |
| Penetration | Query key **không tồn tại**, lần nào cũng xuống DB | Nhiều query tìm id không có kết quả |
| Avalanche | **Nhiều** key cùng hết hạn, hoặc cả cụm Redis sập | Hit ratio tụt mạnh trên diện rộng |

*Chống stampede*
- **Mutex** (khoá loại trừ):
  1. Request đầu tiên thấy miss thì lấy lock: `SET key:lock <token> NX PX 5000`.
  2. Request lấy được lock đọc DB và nạp lại cache.
  3. Các request khác chờ ngắn rồi đọc lại cache, hoặc trả giá trị cũ nếu còn.
  - ⚠️ Lock phải có hạn (`PX`). Người giữ lock chết thì lock tự hết hạn và người khác lấy được.
- **Request coalescing** (gom request) trong một process: nhiều request cùng key trong cùng process
  chỉ chạy loader một lần, các request còn lại chờ và dùng chung kết quả.
  - Ví dụ: Go `singleflight`, Caffeine tự gom load cùng key, Spring `@Cacheable(sync = true)`.
- **Stale-while-revalidate** (SWR): mỗi mục có hai hạn.
  - Hạn mềm: quá hạn này thì vẫn trả giá trị cũ, và một request làm mới ở background.
  - Hạn cứng: quá hạn này thì mới thật sự miss.
- **Probabilistic early expiration** (thuật toán *XFetch*): mỗi request tự quyết định làm mới sớm
  với xác suất tăng dần khi gần hết hạn. Không cần lock.
  - Công thức: làm mới nếu `now - delta * beta * ln(rand()) >= expiry`, trong đó `delta` là thời gian
    tính lại giá trị, `beta` là hệ số (thường 1), `rand()` là số ngẫu nhiên trong (0, 1).
  - Vì `ln(rand())` luôn âm, vế trái lớn hơn `now` một lượng ngẫu nhiên. Càng gần `expiry`, càng dễ
    vượt ngưỡng.
- **Key cực nóng**: không để hết hạn, dùng job làm mới chủ động theo chu kỳ.

*Chống penetration*
- Cache một *null marker* (giá trị đặc biệt nghĩa là "không tồn tại") với TTL ngắn.
  - ⚠️ Nhớ xoá marker khi bản ghi đó được tạo, không thì bản ghi mới bị báo "không tồn tại" tới hết
    TTL.
- *Bloom filter* chứa mọi id hợp lệ, kiểm tra trước khi xuống DB. Bloom filter là cấu trúc dữ liệu
  rất gọn trả lời "chắc chắn không có" hoặc "có thể có":
  - Có *false positive* (báo có mà thật ra không có).
  - Không có *false negative* (không bao giờ báo không có khi thật ra có).
  - Không xoá được phần tử.
  - Chi tiết: [21-dsa.md](21-dsa.md).
- Validate input sớm (id sai định dạng thì trả lỗi ngay), và rate limit.

*Chống avalanche*
- Nguyên nhân thường gặp: nhiều key được nạp cùng lúc sau deploy với TTL cố định, hoặc cả cụm Redis
  sập.
- Cách phòng:
  - Jitter cho TTL (module 1.2).
  - Redis HA (module 3.3).
  - Circuit breaker và rate limit bảo vệ DB. *Circuit breaker* là cơ chế tạm ngừng gọi một phụ thuộc
    đang lỗi, để không dồn thêm tải vào nó.
  - L1 cache làm đệm (module 3.1).
  - Degrade tính năng phụ: tạm tắt gợi ý, bộ đếm, để dành DB cho luồng chính.
- ⚠️ Cold start sau khi Redis restart mà không có persistence: cache trống hoàn toàn. Warm-up dần,
  không bật 100% traffic ngay.

**Đọc**
- Vattani, Chierichetti, Lowenstein: [Optimal Probabilistic Cache Stampede Prevention](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf) (VLDB 2015): paper gốc của XFetch, đọc mục 1–3
- Go: [singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight)
- Scaling Memcache at Facebook: mục 3.2.1, phần lease dùng để chống thundering herd

**Nắm chắc khi**
- [ ] Viết được pseudo-code `getWithCache` có SWR và lock phân tán, xử lý người giữ lock chết (bài tập 2)
- [ ] Phân biệt được stampede, penetration, avalanche bằng triệu chứng trên dashboard (key nào, DB query nào tăng)
- [ ] Giải thích được vì sao Bloom filter không có false negative

#### 2.4 Hot key, big key và Redis làm cache

**Vì sao cần học:** Khi Redis là cache chính, hot key và big key là hai nguyên nhân phổ biến nhất làm
Redis chậm hoặc một node quá tải. Chọn sai `maxmemory-policy` thì session và queue bị xoá âm thầm.
Câu hỏi hay gặp: "trang chủ flash sale làm một node Redis 100% CPU, xử lý thế nào".

**Học gì**

*Hot key*
- *Hot key* là một key bị đọc quá nhiều, ví dụ sản phẩm đang flash sale, cấu hình toàn cục.
- Trong Redis Cluster, mỗi key chỉ nằm trên một node, nên mọi request tới key đó dồn vào **một**
  node dù cụm có nhiều node.
- Cách xử lý:
  - L1 cache trong app với TTL rất ngắn (vài giây), để phần lớn request không tới Redis.
  - Nhân bản key: lưu N bản `product:1#1`..`product:1#N`, mỗi lần đọc chọn ngẫu nhiên một bản, ghi
    thì cập nhật tất cả. Các bản nằm ở slot khác nhau nên rải ra nhiều node.
  - Đọc từ replica.
- Phát hiện: `redis-cli --hotkeys` (cần `maxmemory-policy` là LFU, vì Redis chỉ đếm tần suất khi
  dùng LFU), và metric phía client.

*Big key*
- *Big key*: value vài MB, hoặc hash/list/set có hàng triệu phần tử.
- Tác hại:
  - Đọc hoặc xoá key đó chặn mọi lệnh khác, vì Redis chạy lệnh trên một thread
    ([04-nosql-search-storage.md](04-nosql-search-storage.md) module 2.1).
  - Tốn băng thông mạng.
  - Bộ nhớ lệch giữa các node trong cluster.
- Cách xử lý:
  - Chia nhỏ, nén.
  - Chỉ lấy phần cần: `HGET` thay `HGETALL`, duyệt dần bằng `HSCAN`.
  - Xoá bằng `UNLINK` (giải phóng bộ nhớ ở thread nền) thay `DEL`.
- Phát hiện: `redis-cli --bigkeys` (đếm theo số phần tử), `redis-cli --memkeys` và `MEMORY USAGE`
  (đo theo byte).

*`maxmemory-policy`*
- Quyết định Redis bỏ key nào khi đầy bộ nhớ:
  - `noeviction` (mặc định của Redis tự cài; ElastiCache mặc định `volatile-lru`): không bỏ gì, lệnh
    ghi báo lỗi khi đầy.
  - `allkeys-lru`, `allkeys-lfu`: bỏ trong mọi key.
  - `volatile-*`: chỉ bỏ trong các key có TTL; `volatile-ttl` bỏ key sắp hết hạn nhất.
  - Redis 8.6 thêm `allkeys-lrm` và `volatile-lrm`.
  - `allkeys-random`: bỏ ngẫu nhiên.
- LRU/LFU của Redis là xấp xỉ: chỉ lấy mẫu một số key rồi bỏ key tệ nhất trong mẫu.
- ⚠️ Vừa làm cache vừa lưu session/queue với policy `allkeys-*` thì dữ liệu quan trọng cũng bị evict.
  Tách instance: instance cache dùng `allkeys-lru`/`allkeys-lfu`, instance dữ liệu dùng
  `noeviction`.

*TTL theo field của hash*
- `HEXPIRE`/`HPEXPIRE`/`HTTL` (Redis 7.4+, Valkey 9.0+) đặt TTL cho từng field trong một hash.
- Nhờ vậy gom được nhiều mục cache nhỏ của một user vào một hash mà mỗi mục hết hạn riêng. Trước đây
  phải tách thành nhiều key.

*Redis hay Valkey*
- 2024 Redis đổi license sang RSALv2/SSPLv1, Linux Foundation lập Valkey (fork giữ license BSD).
  Redis 8 (2025) thêm lựa chọn AGPLv3.
- Với vai trò cache, API hai bên gần như giống nhau. Chọn theo dịch vụ managed có sẵn và tính năng
  cần ([04-nosql-search-storage.md](04-nosql-search-storage.md) module 3.2).

**Đọc**
- Redis: [Key eviction](https://redis.io/docs/latest/develop/reference/eviction/) (mục chọn policy), [HEXPIRE](https://redis.io/docs/latest/commands/hexpire/), [Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/)
- Valkey: [Introducing Hash Field Expirations](https://valkey.io/blog/hash-fields-expiration/)
- License: [Redis licenses](https://redis.io/legal/licenses/)

**Nắm chắc khi**
- [ ] Đề xuất được 2 cách xử lý hot key "trang chủ flash sale" và nói cái giá độ cũ của mỗi cách
- [ ] Chọn được `maxmemory-policy` cho instance cache và instance session, giải thích vì sao không dùng chung

#### 2.5 Vận hành cache

**Vì sao cần học:** Phần lớn sự cố cache không đến từ thuật toán mà từ vận hành: deploy xong đọc
cache lỗi, key thiếu `tenant_id` làm lộ dữ liệu, gọi Redis hàng trăm lần mỗi request. Senior được
kỳ vọng biết đo cache, và biết khi nào **không** cache.

**Học gì**

*Serialization và version*
- *Serialization* là biến object thành chuỗi byte để lưu vào cache, và ngược lại khi đọc.

| Cách | Ưu | Nhược |
|---|---|---|
| JSON | Đọc được bằng mắt, mọi ngôn ngữ đọc được | To hơn |
| igbinary, msgpack | Nhỏ hơn, nhanh hơn | Không đọc bằng mắt được |
| Native (PHP `serialize`, Java serialization) | Tiện, lưu nguyên object | Gắn chặt với class |

- ⚠️ Native serialization gắn với class: đổi class là không đọc được cache cũ. Ngoài ra còn rủi ro
  bảo mật khi deserialize dữ liệu không tin cậy.
- Nén value lớn khi băng thông mạng là nút thắt.
- Đổi cấu trúc object thì đổi version trong key: `user:123:v1` thành `user:123:v2`.
  - Deploy mới chỉ đọc key `v2`, không vấp phải format cũ.
  - Rollback về code cũ thì code cũ đọc `v1`, vẫn chạy.

*Đặt tên key*
- Mẫu: `{app}:{env}:{entity}:{id}:{version}`.
- Key phải chứa **mọi thứ** làm kết quả khác nhau: tenant, locale, quyền, tham số query.
  - ⚠️ Thiếu `tenant_id` hay `user_id` trong key là lộ dữ liệu chéo: người này thấy dữ liệu người
    kia.
- Input dài (câu search) thì băm: `search:{sha1(query)}`.
- Không dùng `KEYS *` để tìm và xoá theo prefix. Thay bằng versioned key hoặc tag.

*Cache danh sách và số đếm*
- Cache danh sách: cache **danh sách id** (TTL ngắn, hoặc versioned theo nhóm), rồi lấy chi tiết
  từng object theo id bằng `MGET`.
  - Vì sao: sửa một sản phẩm chỉ cần xoá key của sản phẩm đó, không phải xoá mọi danh sách chứa nó.
- Số đếm: `INCR`/`HINCRBY` trên Redis, đồng bộ định kỳ với DB.

*Cache là một cuộc gọi mạng*
- Timeout ngắn, ngắn hơn DB nhiều. Redis chậm thì coi như miss, đừng để request treo theo.
- ⚠️ N+1 với cache: vòng lặp gọi Redis hàng trăm lần mỗi request, mỗi lần một round-trip. Dùng `MGET`
  hoặc pipeline.

*Warming và tag*
- *Cache warming*: nạp trước key nóng sau deploy, sau restart, hoặc trước sự kiện lớn. Chạy từ từ để
  không tự tạo tải đột biến lên DB.
- *Cache tag*: gắn tag cho các mục cache để invalidate cả nhóm theo tag.
  - ⚠️ Không phải driver nào cũng hỗ trợ (module 2.7).

*Đo lường*
- *Hit ratio* (tỉ lệ hit trên tổng số lần đọc), cả tổng và theo từng nhóm key.
  - Hit ratio thấp thường do key quá cụ thể (mỗi key chỉ được đọc một lần) hoặc TTL quá ngắn.
- Latency p50/p99, số kết nối, số timeout, memory, số key bị evict, số key hết hạn.
- Mục tiêu thật là giảm tải và latency của DB, không phải có hit ratio đẹp.
- Có feature flag tắt cache theo từng tính năng.
  - ⚠️ Cache làm bug khó tái hiện: tắt được cache là có thêm một công cụ debug.

*Khi nào không cache*
- ⚠️ Không cache khi:
  - Dữ liệu cần chính xác tuyệt đối lúc đọc.
  - Ghi nhiều hơn đọc.
  - Query vốn đã nhanh. Nếu chậm vì thiếu index thì sửa index trước.
  - Cá nhân hoá cao, số tổ hợp key bùng nổ, hit ratio sẽ rất thấp.
  - Cache chỉ là "băng dán" che một thiết kế chậm.

**Đọc**
- Redis: [Pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/)
- AWS: [Caching best practices](https://aws.amazon.com/caching/best-practices/) (mục evictions, the thundering herd, cache (almost) everything)
- Hiệu năng nói chung, đo trước khi cache: [17-performance.md](17-performance.md)

**Nắm chắc khi**
- [ ] Thiết kế được key naming cho một app multi-tenant, đa ngôn ngữ, và chỉ ra key nào dễ lộ dữ liệu
- [ ] Đề xuất được bộ metric và cảnh báo cho cache của hệ thống mình
- [ ] Nêu được 3 chỗ trong dự án mà bạn quyết định **không** cache, kèm lý do

#### 2.6 Cài LRU `O(1)`

**Vì sao cần học:** "Cài LRU cache với `get`/`put` O(1)" (LeetCode 146) là bài live coding kinh điển.
Nó kiểm tra bạn có kết hợp được hai cấu trúc dữ liệu để bù điểm yếu của nhau không.

**Học gì**

*Ý tưởng*
- Cần hai thao tác đều O(1):
  - Tìm một key: hash map làm được.
  - Biết key nào lâu nhất chưa dùng, và đổi thứ tự khi một key vừa được dùng: linked list làm được.
- Kết hợp: hash map từ key tới node, node nằm trong một *doubly linked list* (danh sách liên kết hai
  chiều, mỗi node trỏ cả node trước và node sau).
  - Đầu danh sách là mục mới dùng nhất, cuối là mục lâu nhất chưa dùng.

*Hai thao tác*
- `get(key)`:
  1. Tra map. Không có thì trả miss.
  2. Có thì chuyển node lên đầu danh sách, rồi trả giá trị.
- `put(key, value)`:
  1. Key đã có: cập nhật giá trị, chuyển node lên đầu.
  2. Key chưa có: tạo node, thêm vào đầu, thêm vào map.
  3. Vượt dung lượng: bỏ node ở cuối danh sách, và xoá key của nó khỏi map.

*Chi tiết cài đặt*
- Cần danh sách **hai chiều** để gỡ một node ở giữa trong O(1): biết node trước nó mà không phải
  duyệt từ đầu.
- Node lưu cả key, để khi evict node cuối thì biết key nào cần xoá khỏi map.
- Dùng *sentinel* head và tail: hai node giả luôn nằm ở hai đầu, để thêm và gỡ node không phải xử lý
  riêng trường hợp danh sách rỗng hay node ở biên.
- ⚠️ Đa luồng thì `get` cũng là thao tác **ghi**, vì nó đổi thứ tự danh sách. Nên `get` cũng phải
  lock.

*Đối chiếu Java/Go/PHP*
- Java: `LinkedHashMap(capacity, 0.75f, true)` (tham số `true` là sắp theo thứ tự truy cập) và
  override `removeEldestEntry`.
- Go: `map` kết hợp `container/list`.
- PHP: không có sẵn, phải tự cài.
  - Lưu ý mảng PHP giữ thứ tự chèn. Có thể `unset` rồi gán lại một phần tử để "chuyển nó xuống
    cuối", và phần tử đầu mảng là mục lâu nhất chưa dùng.

**Đọc**
- LeetCode 146 *LRU Cache* (luyện viết không cần IDE)
- Thuật toán và cấu trúc dữ liệu liên quan: [21-dsa.md](21-dsa.md)

**Nắm chắc khi**
- [ ] Viết được LRU `O(1)` trong 15 phút, có test cho các trường hợp biên (dung lượng 1, put trùng key)
- [ ] Bổ sung được TTL cho từng key mà `get` vẫn `O(1)` (bài tập 3)

#### 2.7 Cache trong PHP/Laravel

**Vì sao cần học:** Module riêng cho người làm PHP. Người phỏng vấn hay hỏi xoáy vào việc PHP-FPM
không giữ gì giữa các request, nên "cache trong RAM của app" kiểu Java không áp dụng thẳng được. Họ
cũng hay hỏi các API cache của Laravel và những lệnh artisan có thể gây sự cố production.

**Học gì**

*Mô hình PHP-FPM và cache trong process*
- PHP-FPM không có biến nào sống qua request: mỗi request bắt đầu sạch
  ([01-os-linux.md](01-os-linux.md) module 1.1). Nên "L1 in-process" kiểu Java không tồn tại.
- Ba thứ hay bị nhầm với nhau:

| | APCu | OPcache | Octane cache |
|---|---|---|---|
| Cache gì | Dữ liệu key-value | **Bytecode** đã biên dịch của file PHP | Dữ liệu key-value |
| Nằm ở đâu | Shared memory của một máy, dùng chung giữa các worker FPM cùng pool | Shared memory của một máy | Bộ nhớ của process Octane sống lâu |
| Có thay Redis được không | Không khi có nhiều server | Không liên quan, không phải cache dữ liệu | Không khi có nhiều server |

- APCu:
  - ⚠️ Mỗi server một bản riêng, không invalidate chéo được giữa các server.
  - ⚠️ Restart FPM là mất hết. CLI (artisan, cron) có vùng nhớ riêng, không thấy dữ liệu của FPM.
- OPcache:
  - ⚠️ Nhầm OPcache với cache dữ liệu là red flag.
  - `opcache.validate_timestamps=0` trên production thì PHP không kiểm tra file đổi, nên deploy phải
    reset OPcache.
- Octane (chạy bằng Swoole, RoadRunner hoặc FrankenPHP): process sống lâu qua nhiều request.
  [Octane cache](https://laravel.com/docs/octane#the-octane-cache) là bảng dùng chung giữa các worker
  **chỉ khi chạy Swoole**; với server khác, store `octane` lặng lẽ rơi về mảng riêng của từng worker.
  - ⚠️ Biến static và singleton sống qua request, nên có thể rò dữ liệu của request trước sang request
    sau.

*Laravel Cache API*
- `Cache::remember`, `rememberForever`: cache-aside (module 1.2).
- `Cache::memo()` và helper `once()`: *memoize* (nhớ kết quả) trong phạm vi một request hoặc một job,
  để gọi nhiều lần cũng chỉ tính một lần.
- `Cache::flexible($key, [$fresh, $stale], $fn)` (Laravel 11.23+): stale-while-revalidate (module 2.3).
  - Trong khoảng `$fresh`: trả giá trị như thường.
  - Trong khoảng `$stale`: trả giá trị cũ, và làm mới **sau khi gửi response** (deferred).
  - Có lock để chỉ một request làm mới.
- `Cache::lock($name, $seconds)`: atomic lock, dùng chống stampede và chống chạy trùng.
  - `block()` chờ lock trong một thời gian có hạn.
  - *Owner token* và `restoreLock` cho phép nhả lock từ process khác, ví dụ request lấy lock rồi job
    nhả.
- Cache tags: không hỗ trợ với driver `file`, `dynamodb`, `database`, `storage`.
  - ⚠️ Tag trên Redis lưu thêm một tập key cho mỗi tag, tốn memory, và flush một tag lớn có thể chậm.
- Failover driver: tự chuyển sang store dự phòng khi store chính lỗi.

*Redis client*
- phpredis (extension C, mặc định, nhanh) và Predis (thuần PHP).
- phpredis có serializer và compression riêng.
  - ⚠️ Đổi serializer là đọc lỗi toàn bộ cache cũ.

*Các cạm bẫy của Laravel*
- ⚠️ `php artisan cache:clear` flush **cả DB Redis** mà cache store đang dùng.
  - Dùng chung DB đó với queue thì mất job. Dùng chung với session thì mọi người bị đăng xuất.
  - Sửa: tách connection hoặc DB Redis cho cache, queue, session. Skeleton Laravel 13 đã tách sẵn
    (cache ở DB 1, còn lại ở DB 0), nhưng ⚠️ `cache:clear --locks` vẫn flush DB 0.
- ⚠️ Laravel 13 mặc định `serializable_classes => false` trong `config/cache.php`: cache một object
  (kể cả model) thì lần đọc sau nhận `__PHP_Incomplete_Class`. Cache mảng hoặc khai báo class được phép.
- ⚠️ Cache nguyên model Eloquent: serialize cả các relation đã load, và đổi class là lỗi khi đọc lại.
  Cache mảng hoặc DTO đơn giản thì an toàn hơn.

*Đối chiếu Java/Go*
- Spring: `@Cacheable`/`@CacheEvict`, `@Cacheable(sync = true)` để gom load cùng key.
  - ⚠️ *Self-invocation*: method trong cùng class gọi nhau thì không đi qua proxy của Spring, nên cache
    không chạy.
- Go: `singleflight` (gom request), `ristretto` (thư viện cache trong process).
- Cả ba chỉ chống stampede trong **một process**. Nhiều instance vẫn cần lock phân tán hoặc SWR.

**Đọc**
- Laravel: [Cache](https://laravel.com/docs/cache) (các mục [Stale While Revalidate](https://laravel.com/docs/cache#swr), [Cache Memoization](https://laravel.com/docs/cache#cache-memoization), [Cache Tags](https://laravel.com/docs/cache#cache-tags), [Atomic Locks](https://laravel.com/docs/cache#atomic-locks), [Managing Locks Across Processes](https://laravel.com/docs/cache#managing-locks-across-processes), [Cache Failover](https://laravel.com/docs/cache#cache-failover)), helper [`once()`](https://laravel.com/docs/helpers#method-once)
- PHP: [APCu](https://www.php.net/manual/en/book.apcu.php), [OPcache](https://www.php.net/manual/en/book.opcache.php)
- [phpredis](https://github.com/phpredis/phpredis) (mục serializer, compression, persistent connection), [Predis](https://github.com/predis/predis)
- Spring: [Cache Abstraction](https://docs.spring.io/spring-framework/reference/integration/cache.html) (đối chiếu)
- Runtime PHP-FPM và Octane: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Giải thích được vì sao APCu không thay được Redis khi có 10 server, và khi nào APCu vẫn hợp lý
- [ ] Dùng `Cache::flexible` và `Cache::lock` sửa được một endpoint bị stampede, nói rõ khác nhau giữa hai cách
- [ ] Chỉ ra được cấu hình Laravel để `cache:clear` không đụng tới queue và session

---

### Chặng 3: Senior 🔴

#### 3.1 Multi-level cache (L1 + L2)

**Vì sao cần học:** Khi Redis thành nút thắt (hot key, round-trip quá nhiều), bước tiếp theo là thêm
một tầng cache ngay trong app. Cái khó là giữ các bản sao trên 20 instance không lệch nhau quá lâu.
Người phỏng vấn senior muốn nghe bạn nói được "độ cũ tối đa là bao nhiêu" và vì sao.

**Học gì**

*Hai tầng cache*
- *L1* là cache in-process, nằm trong bộ nhớ của từng instance app. *L2* là cache distributed dùng
  chung (Redis).
- Luồng đọc:
  1. Đọc L1. Hit thì trả luôn, không tốn round-trip mạng.
  2. Miss thì đọc L2 (Redis). Hit thì nạp vào L1 rồi trả.
  3. Miss tiếp thì đọc DB, nạp vào L2 và L1.
- L1 bớt round-trip và chắn hot key (request không còn dồn vào một node Redis). L2 dùng chung giữa
  mọi instance.

*Vấn đề: mỗi instance một bản L1*
- Ghi ở instance A thì A xoá được L1 của mình và L2. Nhưng L1 ở instance B vẫn giữ bản cũ, B không
  biết có thay đổi.

*Cách xử lý*
- **TTL của L1 rất ngắn** (vài giây): giới hạn độ cũ tối đa bằng TTL đó.
- **Broadcast invalidation**: instance ghi phát một message "key X đã đổi" qua Redis Pub/Sub hoặc
  message bus, mọi instance nhận thì xoá X khỏi L1 của mình.
  - ⚠️ Pub/Sub không bền: instance mất kết nối đúng lúc đó sẽ bỏ lỡ message và giữ bản cũ. Vì vậy
    vẫn cần TTL.
- **Redis client-side caching** (tính năng *tracking*): Redis ghi nhớ client nào đã đọc key nào, và
  gửi thông báo cho client đó khi key bị đổi. Client library phải hỗ trợ tính năng này.

*Chọn gì cho L1*
- Chỉ đưa vào L1 dữ liệu nhỏ, ít đổi (cấu hình, danh mục, feature flag).
- Để ý memory của từng instance, ví dụ JVM heap: L1 phình to là app bị OOM.
- PHP-FPM không có L1 in-process thật sự (module 2.7): L1 thường là APCu, hoặc Octane cache nếu chạy
  Octane.

**Đọc**
- Redis: [Client-side caching reference](https://redis.io/docs/latest/develop/reference/client-side-caching/) (mục tracking, broadcasting mode, và phần race giữa đọc và invalidation)
- Redis: [Pub/Sub](https://redis.io/docs/latest/develop/pubsub/) (mục delivery semantics)

**Nắm chắc khi**
- [ ] Thiết kế được L1 + L2 cho 20 instance, nói được độ cũ tối đa trong trường hợp xấu nhất
- [ ] So sánh được Pub/Sub, Streams, Kafka để broadcast invalidation (bài tập 5)

#### 3.2 Nhất quán cache ở quy mô lớn: lease, CDC

**Vì sao cần học:** Module này là các lời giải công nghiệp cho chính những race ở module 2.2 và
stampede ở module 2.3, lấy từ paper memcache của Facebook. Câu "lease giải quyết vấn đề gì" là câu
phân loại senior rất rõ: người chưa đọc thường nhầm lease với distributed lock.

**Học gì**

*Lease*
- *Lease* (Facebook memcache, NSDI 2013) là một token cache cấp cho client khi client gặp miss, cho
  phép client đó ghi lại giá trị cho key.
- Cách hoạt động:
  1. Client đọc key, miss. Cache cấp cho client một **lease token**.
  2. Client đọc DB.
  3. Client `set` giá trị kèm token. Cache chỉ nhận nếu token còn hiệu lực.
- Giải race "ghi cache sau khi đã xoá" ở module 2.2:
  1. B miss, nhận token, đọc DB được giá trị cũ.
  2. A update DB rồi xoá key. Lệnh xoá làm **token của B mất hiệu lực**.
  3. B `set` giá trị cũ kèm token cũ, cache từ chối.
- Giải stampede:
  - Cache chỉ cấp token cho mỗi key với tần suất giới hạn (paper dùng khoảng 10 giây một lần).
  - Client khác trong lúc đó nhận "chờ rồi thử lại". Khi thử lại, thường giá trị đã được client giữ
    token nạp xong.
- Khác distributed lock: lease không bắt ai chờ để được làm việc, mà chỉ quyết định **ai được ghi**
  vào cache và từ chối ghi đã lỗi thời.
- Redis không có lease sẵn. Mô phỏng bằng Lua:
  - Khi miss: ghi một token vào key phụ.
  - Khi `set`: so token, chỉ ghi nếu khớp.
  - Khi xoá: `DEL` cả key lẫn token.

*Invalidation qua commit log*
- Facebook đọc commit log của MySQL để phát lệnh xoá cache (hệ thống tên *mcsqueal*), thay vì để code
  nghiệp vụ tự xoá.
- Ngày nay cách này gọi là CDC: Debezium, Canal đọc binlog của MySQL rồi phát lệnh xoá.

| | Xoá trong code | Xoá qua CDC |
|---|---|---|
| Độ trễ | Ngay sau ghi | Thêm độ trễ của pipeline CDC |
| Độ phủ | Chỉ các đường ghi có gọi xoá | Mọi thay đổi, kể cả sửa tay, script |
| Thời điểm | Dễ lỡ xoá trước commit | Chỉ thấy thay đổi đã commit |
| Độ phức tạp | Logic xoá rải trong code | Thêm hạ tầng; map từ dòng thay đổi sang key cache không phải lúc nào cũng dễ |

*Đo độ nhất quán*
- Đo thay vì đoán. Meta đo tỉ lệ cache lệch với DB và đẩy lên mức rất nhiều số 9, bằng cách lấy mẫu
  so sánh cache với DB và truy vết từng ca lệch.

*Nhiều region*
- Region phụ đọc replica DB đang lag, nên dễ nạp giá trị cũ vào cache.
- Paper dùng *remote marker*: đánh dấu key vừa bị ghi, để request ở region phụ biết phải đọc từ
  region chính thay vì replica local.

**Đọc**
- [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala): đọc mục 3.2.1 (leases), 4 (in a region), 5 (across regions)
- Meta Engineering: [Cache made consistent](https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/) (2022)
- DDIA ch.11, mục *Change Data Capture*

**Nắm chắc khi**
- [ ] Vẽ lại được race "update DB rồi xoá cache" và chỉ ra chính xác bước nào lease chặn được
- [ ] Viết được Lua mô phỏng lease trên Redis: cấp token khi miss, `set` có điều kiện, xoá huỷ token
- [ ] So sánh được xoá cache trong code và xoá qua CDC theo 4 tiêu chí: độ trễ, độ phủ, độ phức tạp, điểm lỗi

#### 3.3 Khi cache trở thành phụ thuộc bắt buộc

**Vì sao cần học:** Hệ thống chạy lâu với hit ratio 95% thì DB đã được sizing cho 5% tải. Redis sập
là DB nhận gấp 20 lần tải và sập theo. Senior phải trả lời được "cache chết thì sao" bằng số liệu, và
thiết kế để hệ thống sống sót.

**Học gì**

*Câu hỏi thật*
- Cache sập thì hệ thống có chịu nổi không?
- Nếu không, cache đã là *phụ thuộc bắt buộc*. Khi đó nó phải được vận hành như một DB: HA, giám
  sát, capacity plan.

*Redis HA*
- Replica + Sentinel, hoặc Cluster ([04-nosql-search-storage.md](04-nosql-search-storage.md)
  module 3.2).
- Failover async có thể mất ghi. Với cache thì thường chấp nhận được, vì nguồn sự thật nằm ở DB.

*Hành vi khi Redis chậm hoặc chết*
- Timeout ngắn: Redis chậm thì bỏ qua, không để request treo theo.
- Circuit breaker: lỗi liên tục thì tạm ngừng gọi Redis một lúc.
- Coi như miss, nhưng có rate limit xuống DB để không dồn toàn bộ tải vào DB.
- Failover sang store phụ (Laravel failover driver) hoặc L1.

*Đo, không đoán*
- DB chịu được bao nhiêu phần trăm tải khi mất cache? Đo bằng load test, không đoán.
- Ví dụ: hit ratio 95% nghĩa là DB chỉ thấy 5% số lần đọc. Mất cache thì DB thấy 100%, tức gấp 20 lần.

*Phục hồi sau sự cố*
- Warm-up dần sau sự cố, tránh cả cụm cùng nạp lại một lúc.
- Postmortem: hỏi vì sao DB không chịu nổi một lượt miss. Sửa gốc (query, index), không chỉ tăng TTL
  ([18-reliability-observability.md](18-reliability-observability.md)).

**Đọc**
- Scaling Memcache at Facebook: mục 3.3 (gutter pool: nhóm máy dự phòng nhận tải khi máy cache chết)
- Redis: [Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/), [Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)

**Nắm chắc khi**
- [ ] Mô tả được từng bước hệ thống của mình phản ứng khi Redis mất hoàn toàn trong 10 phút
- [ ] Đề xuất được bài load test chứng minh DB sống sót với hit ratio giảm từ 95% xuống 0%

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Cache-aside hoạt động thế nào?** (1.2)
- Ý phải có: đọc cache, miss thì đọc DB rồi ghi cache kèm TTL; ghi thì ghi DB rồi xoá key
- Điểm cộng: nói luôn nhược điểm (miss lần đầu, cửa sổ cũ, race)

**2. TTL dùng để làm gì? Vì sao thêm jitter?** (1.2)
- Ý phải có: lưới an toàn giới hạn độ cũ; jitter để key không hết hạn cùng lúc
- Điểm cộng: chọn TTL theo mức chấp nhận cũ của nghiệp vụ, không theo cảm tính

**3. LRU và LFU khác nhau thế nào?** (1.3)
- Ý phải có: lâu nhất chưa dùng so với ít dùng nhất; workload mỗi cái hợp
- Điểm cộng: LRU bị quét lớn phá; LFU cần decay; W-TinyLFU

**4. Kể các tầng cache từ trình duyệt tới DB.** (1.1)
- Ý phải có: browser, CDN, reverse proxy, in-process, distributed, DB buffer pool
- Điểm cộng: mỗi tầng xoá thế nào; `no-cache` khác `no-store`
- Red flag: chỉ biết Redis

**5. OPcache và APCu khác nhau thế nào?** (2.7)
- Ý phải có: OPcache cache bytecode, APCu cache dữ liệu trong shared memory của một máy
- Red flag: coi OPcache là nơi cache kết quả query

### 🟡 Mid

**6. Update DB rồi xoá cache, hay xoá cache rồi update DB? Vẽ race.** (2.2)
- Ý phải có: vẽ được cả hai timeline; update rồi xoá có cửa sổ hẹp hơn; vẫn cần TTL
- Điểm cộng: xoá sau commit; replica lag; delayed double delete và vì sao nó chỉ là xác suất
- Red flag: "update rồi xoá là đúng tuyệt đối"

**7. Vì sao nên xoá cache thay vì cập nhật cache khi ghi?** (2.2)
- Ý phải có: hai lần ghi đồng thời set theo thứ tự ngược; giá trị cache thường tổng hợp từ nhiều bảng
- Điểm cộng: ngoại lệ counter `INCR` hoặc set kèm version

**8. Stampede, penetration, avalanche khác nhau thế nào? Phòng từng cái?** (2.3)
- Ý phải có: một key nóng hết hạn / key không tồn tại / nhiều key hoặc cả cụm cùng mất; mỗi cái 2–3 cách phòng
- Điểm cộng: XFetch; Bloom filter không có false negative; cold start sau restart

**9. Cài LRU cache với `get`/`put` đều `O(1)`.** (2.6)
- Ý phải có: hash map + doubly linked list, sentinel, node giữ key
- Điểm cộng: lock khi đa luồng; `LinkedHashMap` access order

**10. Hot key và big key trong Redis xử lý ra sao?** (2.4)
- Ý phải có: hot key: L1, nhân bản key, replica; big key: chia nhỏ, `HSCAN`, `UNLINK`
- Điểm cộng: `--hotkeys` cần LFU; big key làm migrate slot treo

**11. Write-through và write-behind khác nhau thế nào? Khi nào dùng write-behind?** (2.1)
- Ý phải có: đồng bộ so với theo lô; write-behind mất dữ liệu khi sập
- Điểm cộng: dùng cho counter/view count, giới hạn lượng có thể mất bằng chu kỳ flush

**12. `Cache::flexible` và `Cache::lock` khác nhau thế nào khi chống stampede?** (2.7)
- Ý phải có: `flexible` trả giá trị cũ và làm mới sau response; `lock` để một request rebuild, người khác chờ hoặc trả cũ
- Điểm cộng: `flexible` vẫn miss khi quá hạn stale; lock phải có hạn và nhả đúng chủ; cả hai cần store hỗ trợ lock

**13. Cache danh sách sản phẩm theo danh mục, invalidate thế nào khi một sản phẩm đổi?** (2.5)
- Ý phải có: cache danh sách id + cache từng object; versioned key hoặc tag cho nhóm
- Điểm cộng: tag không có ở mọi driver và tốn memory; TTL ngắn cho danh sách

**14. Vì sao `php artisan cache:clear` có thể làm sự cố production?** (2.7)
- Ý phải có: flush cả DB Redis của store, dùng chung với queue/session là mất job, đăng xuất; tất cả key cùng miss
- Điểm cộng: tách connection/DB; xoá theo tag hoặc version thay vì flush

### 🔴 Senior

**15. Lease trong paper memcache của Facebook giải quyết vấn đề gì?** (3.2)
- Ý phải có: race set giá trị cũ sau khi đã xoá (token bị huỷ khi xoá) và thundering herd (giới hạn tần suất cấp token)
- Điểm cộng: mô phỏng lease trên Redis bằng Lua; invalidation qua commit log
- Red flag: nhầm lease với distributed lock thông thường

**16. Thiết kế multi-level cache L1 + L2 cho 20 instance, giữ nhất quán thế nào?** (3.1)
- Ý phải có: TTL L1 ngắn, broadcast invalidation, chỉ dữ liệu nhỏ ít đổi
- Điểm cộng: Pub/Sub không bền nên TTL vẫn cần; client-side caching; PHP-FPM dùng APCu hoặc Octane cache

**17. Dùng CDC để invalidate cache: ưu nhược so với xoá trong code?** (3.2)
- Ý phải có: bắt mọi thay đổi, chỉ sau commit, tách khỏi code; đổi lại độ trễ và hạ tầng
- Điểm cộng: map từ dòng sang key; kết hợp cả hai

**18. Trang chủ có key cache hết hạn đúng giờ cao điểm và DB sập.** (2.3, 3.3)
- Ý phải có: stampede, có thể kèm avalanche; lock rebuild, SWR, job làm mới, jitter
- Điểm cộng: kiểm tra DB có chịu được một lượt miss; postmortem vì sao
- Red flag: "tăng TTL lên 1 ngày"

**19. Admin sửa giá, 10 phút sau một số người vẫn thấy giá cũ.** (2.2, 3.1)
- Ý phải có: đi từng tầng: CDN, L1 từng instance, Redis, replica lag
- Điểm cộng: xoá chạy sau commit không, lỗi xoá có bị nuốt không; versioned key hoặc CDC

**20. Bot gọi `/products/{id}` với id ngẫu nhiên, DB CPU 100%.** (2.3)
- Ý phải có: penetration; cache null TTL ngắn, Bloom filter, validate id, rate limit
- Điểm cộng: id không đoán được (public id) giảm bề mặt tấn công

**21. Sau khi bật cache danh sách đơn hàng, một khách thấy đơn của khách khác.** (2.5)
- Ý phải có: key thiếu `user_id`/`tenant_id`, hoặc CDN cache response thiếu `Cache-Control: private`
- Điểm cộng: xử lý như sự cố lộ dữ liệu: xoá cache, rà mọi key, thông báo theo quy định ([10-security.md](10-security.md))

**22. Redis memory tăng đều, latency thỉnh thoảng vọt vài trăm ms.** (2.4)
- Ý phải có: key không TTL, big key, lệnh chặn (`KEYS`, `HGETALL` lớn, `DEL` big key)
- Điểm cộng: `maxmemory` + policy, `UNLINK`, fork RDB, `HEXPIRE` thay vì hash không bao giờ hết hạn

**23. Deploy đổi class `UserDto`, log đầy lỗi deserialize từ cache.** (2.5)
- Ý phải có: format cache cũ; version trong key, JSON thay native, đọc lỗi thì coi là miss
- Điểm cộng: rollback cũng phải đọc được; đổi serializer phpredis cũng gây lỗi tương tự

**24. Redis cache sập hoàn toàn, hệ thống của bạn phản ứng thế nào?** (3.3)
- Ý phải có: timeout ngắn, circuit breaker, coi như miss có rate limit, DB chịu được bao nhiêu
- Điểm cộng: failover store, gutter pool, warm-up dần, load test chứng minh
- Red flag: "có replica rồi nên không sập"

**25. Khi nào bạn quyết định không dùng cache?** (2.5)
- Ý phải có: cần chính xác tuyệt đối, ghi nhiều hơn đọc, query vốn nhanh, tổ hợp key bùng nổ
- Điểm cộng: đo trước; cache che thiết kế chậm là nợ kỹ thuật

---

## Bài tập tự làm

1. Vẽ timeline cho kịch bản: DB có một replica lag 500 ms, app đọc từ replica khi cache miss, dùng "update DB rồi xoá cache". Chỉ ra dữ liệu cũ vào cache thế nào và đề xuất hai cách sửa kèm cái giá.
2. Viết pseudo-code cho hàm `getWithCache(key, loader, ttl)` có chống stampede bằng stale-while-revalidate và lock phân tán, xử lý trường hợp người giữ lock chết. Sau đó so sánh với cách `Cache::flexible` của Laravel làm.
3. Cài LRU cache `O(1)` bằng ngôn ngữ bạn chọn (Go, Java hoặc PHP), sau đó bổ sung TTL cho từng key.
4. Chọn một màn hình trong dự án của bạn, liệt kê dữ liệu trên đó, quyết định cache hay không cho từng phần, TTL, key naming, và cách invalidate.
5. So sánh bằng bảng: Redis Pub/Sub, Redis Streams, Kafka dùng để broadcast invalidation cho L1 cache.
6. Viết Lua script mô phỏng lease của Facebook trên Redis (cấp token khi miss, `set` chỉ thành công nếu token còn, `DEL` huỷ token). Viết kịch bản hai client chứng minh nó chặn được race ở bài tập 1.

> Nộp bài vào đây để được review.
