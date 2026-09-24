# 16. System design

> [← Mục lục](README.md) · Phạm vi: phương pháp làm bài system design 45–60 phút, ước lượng back-of-envelope, building blocks, availability, và các bài kinh điển (URL shortener, rate limiter, feed, chat, đặt vé, thanh toán, flash sale, ID, KV store, crawler, autocomplete, file storage, video, nearby search, leaderboard, job scheduler, metrics/logging).
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

🟡 mid trở lên bắt buộc; junior có thể bị hỏi bản đơn giản (URL shortener, rate limiter, "hệ thống chạy một server, traffic tăng 10 lần").

## Bản đồ nhanh

**Phương pháp**
- [ ] Các bước làm bài và phân bổ thời gian
- [ ] Hỏi functional và non-functional requirement trước khi vẽ
- [ ] Những gì người chấm đánh giá
- [ ] ⚠️ Lỗi hay gặp: nhảy vào chi tiết sớm, không hỏi requirement, không nói trade-off, vẽ hộp không giải thích luồng dữ liệu

**Ước lượng**
- [ ] 🟢 Bảng lũy thừa 2 và đơn vị dữ liệu
- [ ] 🟢 Con số độ trễ nên nhớ
- [ ] 🟢 QPS từ DAU; 1 triệu request/ngày ≈ 12 QPS; peak factor
- [ ] 🟡 Ước lượng storage, bandwidth, số máy, bộ nhớ cache

**Building blocks**
- [ ] 🟢 Scale dọc vs scale ngang; stateless
- [ ] 🟢 Load balancer (thuật toán, health check, sticky session)
- [ ] 🟡 API gateway, cache, CDN, object storage
- [ ] 🟡 SQL vs NoSQL, replication, sharding
- [ ] 🟡 Queue, search engine, rate limiter
- [ ] 🔴 ID generator, consistent hashing, bloom filter, geo index

**Availability**
- [ ] 🟢 Bảng số 9 ra downtime/năm
- [ ] 🟡 SPOF, redundancy, active-passive vs active-active
- [ ] 🔴 Multi-AZ, multi-region; availability của chuỗi phụ thuộc

**Bài kinh điển (viết sâu)**
- [ ] 🟢 URL shortener
- [ ] 🟡 Rate limiter
- [ ] 🟡 Notification system
- [ ] 🟡 News feed
- [ ] 🟡 Chat / messenger
- [ ] 🟡 Đặt vé / đặt phòng (double booking, giữ chỗ tạm)
- [ ] 🔴 Thanh toán / ví điện tử (ledger, idempotency, reconciliation)
- [ ] 🔴 Flash sale

**Bài kinh điển (viết gọn)**
- [ ] 🔴 Distributed ID generator
- [ ] 🔴 Key-value store
- [ ] 🔴 Web crawler
- [ ] 🔴 Search autocomplete
- [ ] 🔴 File storage (Drive/Dropbox)
- [ ] 🔴 Video streaming (đại ý)
- [ ] 🔴 Ride-hailing / nearby search
- [ ] 🟡 Leaderboard
- [ ] 🔴 Distributed job scheduler
- [ ] 🔴 Metrics / logging system
- [ ] 🟢 "Một server, traffic tăng 10 lần, làm gì?"

## Chi tiết

### Phương pháp làm bài 45–60 phút

- [ ] **Các bước và thời gian** (bài 45 phút; bài 60 phút giãn phần deep dive)

  | Bước | Thời gian | Làm gì |
  |---|---|---|
  | 1. Làm rõ requirement | 5–8 phút | Functional: 3–5 tính năng chính, **chốt phạm vi** (cái gì không làm). Non-functional: quy mô, latency, consistency, availability, đọc/ghi nhiều hơn |
  | 2. Ước lượng | 3–5 phút | QPS đọc/ghi, peak, storage vài năm, bandwidth. Chỉ tính những con số ảnh hưởng tới thiết kế |
  | 3. API | 3–5 phút | 3–5 endpoint chính, tham số, response; phân trang, idempotency key nếu có ghi quan trọng |
  | 4. Data model | 5 phút | Bảng/collection chính, khoá, index, chọn loại DB và vì sao |
  | 5. Kiến trúc tổng | 10 phút | Sơ đồ hộp, **đi qua luồng đọc và luồng ghi** từ client tới storage |
  | 6. Deep dive | 10–15 phút | 2–3 điểm then chốt (thường người phỏng vấn chọn): nút thắt, consistency, hot key, failure |
  | 7. Tổng kết | 2–3 phút | Trade-off đã chọn, điểm yếu còn lại, mở rộng nếu có thêm thời gian |

- [ ] **Câu hỏi requirement nên hỏi**
  - Ai dùng, bao nhiêu DAU, phân bố địa lý?
  - Tỉ lệ đọc/ghi? Kích thước dữ liệu mỗi bản ghi?
  - Cần consistency mạnh ở đâu (tiền, tồn kho) và eventual ở đâu (feed, lượt like)?
  - Latency mục tiêu (p99)? Availability mục tiêu?
  - Dữ liệu giữ bao lâu? Có yêu cầu compliance (xoá dữ liệu cá nhân, data residency)?
- [ ] **Người chấm đánh giá gì**
  - Làm rõ bài toán mơ hồ, chốt phạm vi hợp lý
  - Thiết kế chạy được end-to-end trước, rồi mới tối ưu
  - Biết building block nào dùng khi nào, và **vì sao** không dùng cái khác
  - Nói trade-off, failure mode, cách vận hành (monitoring, deploy, migration)
  - Giao tiếp: dẫn dắt, nhận gợi ý, sửa thiết kế khi có thông tin mới
  - Ở level senior: nhận ra điểm then chốt của bài mà không cần gợi ý (ví dụ bài thanh toán thì là idempotency và ledger, không phải chọn framework)
- [ ] **Lỗi hay gặp** ⚠️
  - Nhảy vào chọn Kafka, Cassandra trước khi biết quy mô
  - Không hỏi requirement, tự giả định rồi thiết kế sai bài
  - Không nói trade-off: "dùng Redis" mà không nói mất gì khi Redis chết
  - Vẽ nhiều hộp nhưng không đi qua luồng một request
  - Over-engineering cho quy mô nhỏ (microservices cho 100 QPS)
  - Ước lượng quá chi tiết, mất 15 phút tính toán
  - Im lặng suy nghĩ lâu; nên nghĩ thành tiếng

### Ước lượng back-of-envelope

- [ ] **Lũy thừa 2 và đơn vị**

  | Lũy thừa | Xấp xỉ | Đơn vị |
  |---|---|---|
  | 2^10 | 1 nghìn (10^3) | 1 KB |
  | 2^20 | 1 triệu (10^6) | 1 MB |
  | 2^30 | 1 tỉ (10^9) | 1 GB |
  | 2^40 | 1 nghìn tỉ (10^12) | 1 TB |
  | 2^50 | 10^15 | 1 PB |

  - Kích thước quen thuộc: `int64`/timestamp 8 byte, UUID 16 byte (36 ký tự dạng chuỗi), một ký tự ASCII 1 byte, ký tự tiếng Việt có dấu trong UTF-8 thường 2–3 byte
- [ ] **Con số độ trễ nên nhớ** (bậc độ lớn)

  | Thao tác | Độ trễ gần đúng |
  |---|---|
  | Đọc L1 cache | ~1 ns |
  | Đọc RAM | ~100 ns |
  | Đọc ngẫu nhiên từ SSD | ~16–100 µs |
  | Round trip trong cùng datacenter | ~0,5 ms |
  | Seek ổ đĩa quay (HDD) | ~2–10 ms |
  | Round trip xuyên lục địa | ~150 ms |

  - Hệ quả: RAM nhanh hơn mạng ~1000 lần, mạng trong DC nhanh hơn round trip xuyên lục địa ~300 lần. Gọi mạng tuần tự 10 lần trong một request là thấy ngay
- [ ] **QPS từ DAU**
  - 1 ngày ≈ 86.400 giây ≈ 10^5 giây, nên **1 triệu request/ngày ≈ 12 QPS** trung bình
  - QPS trung bình = DAU × số request mỗi user mỗi ngày / 86.400
  - Peak thường gấp 2–10 lần trung bình (tuỳ sản phẩm; flash sale có thể gấp hàng trăm lần)
- [ ] **Storage** = số bản ghi mỗi ngày × kích thước × số ngày lưu × số bản sao (replication) × hệ số index/overhead
- [ ] **Bandwidth** = QPS × kích thước response. Ghi và đọc tính riêng
- [ ] **Ví dụ tính mẫu**: URL shortener, 100 triệu URL mới mỗi tháng, đọc:ghi = 100:1, lưu 5 năm
  - Ghi: 10^8 / (30 × 10^5) ≈ 40 QPS; peak ×5 ≈ 200 QPS
  - Đọc: 40 × 100 = 4.000 QPS; peak ≈ 20.000 QPS
  - Số URL sau 5 năm: 10^8 × 12 × 5 = 6 × 10^9
  - Storage: 6 × 10^9 × ~500 byte ≈ 3 TB (chưa tính replica)
  - Cache 20% URL nóng của một ngày: đọc mỗi ngày 4.000 × 10^5 = 4 × 10^8 request; 20% × 4 × 10^8 × 500 byte ≈ 40 GB → vừa một cụm Redis nhỏ
  - Kết luận ảnh hưởng thiết kế: ghi thấp, đọc cao → cache là trọng tâm; 3 TB vẫn nằm được trên vài node DB, sharding chưa cấp bách
- [ ] ⚠️ Làm tròn mạnh tay, nói rõ giả định. Mục tiêu là bậc độ lớn, không phải con số chính xác

### Building blocks

- [ ] **Scale dọc vs scale ngang** 🟢: dọc (máy to hơn) đơn giản nhưng có trần và là SPOF; ngang (thêm máy) cần service **stateless** (session, file, cache local chuyển ra ngoài)

| Block | Dùng khi | Chi tiết |
|---|---|---|
| Load balancer | Chia tải nhiều instance, health check, TLS termination. L4 (TCP) nhanh, L7 (HTTP) route theo path/header. Thuật toán: round robin, least connections, consistent hashing. ⚠️ Sticky session cản scale và failover; nên đưa session ra Redis | [02](02-networking.md) |
| API gateway | Một điểm vào: auth, rate limit, routing, logging cho nhiều service | [09](09-api-design.md) |
| Cache (Redis/Memcached) | Đọc nhiều, dữ liệu chịu được stale, cần latency thấp | [11](11-cache.md) |
| CDN | File tĩnh, ảnh, video, response công khai; người dùng xa server | [11](11-cache.md), [02](02-networking.md) |
| SQL DB | Quan hệ, transaction, constraint, query linh hoạt. Mặc định nên chọn | [03](03-database-sql.md) |
| NoSQL | Ghi rất lớn, schema linh hoạt, truy cập theo key đã biết trước (wide-column, document, KV) | [04](04-nosql-search-storage.md) |
| Read replica | Đọc nhiều hơn ghi; ⚠️ replication lag, read-your-writes | [03](03-database-sql.md) |
| Sharding | Dữ liệu hoặc lượng ghi vượt một node; chọn shard key theo pattern truy cập | [03](03-database-sql.md) |
| Queue / log (Kafka, RabbitMQ, SQS) | Tách việc chậm, làm mượt đỉnh tải, fan-out sự kiện | [12](12-messaging.md) |
| Object storage (S3) | File, ảnh, video, backup. ⚠️ Không lưu file upload trên đĩa app server | [04](04-nosql-search-storage.md) |
| Search (Elasticsearch/OpenSearch) | Full-text, filter nhiều chiều, faceting; không làm nguồn dữ liệu gốc | [04](04-nosql-search-storage.md) |
| Rate limiter | Chống lạm dụng, bảo vệ backend, công bằng giữa tenant | bài bên dưới |
| ID generator | Cần ID duy nhất toàn cục, sinh phân tán, có thứ tự thời gian | bài bên dưới |
| Consistent hashing | Chia key cho node sao cho thêm/bớt node chỉ dời ít key (cache cluster, KV store, sharding) | [14](14-distributed-systems.md) |
| Bloom filter | Kiểm tra "chắc chắn không có" rất rẻ: tránh đọc đĩa, URL đã crawl, username đã tồn tại. Có false positive, không có false negative | [21](21-dsa.md) |
| Geo index (geohash, quadtree, H3) | Tìm điểm gần nhất | bài nearby search |
| Stream processing (Flink, Kafka Streams) | Tổng hợp real-time: đếm, window, phát hiện gian lận | [12](12-messaging.md) |

- [ ] **Consistent hashing** 🔴 (tóm tắt): đặt node và key lên một vòng hash; key thuộc node đầu tiên theo chiều kim đồng hồ. Thêm/bớt node chỉ dời khoảng 1/N số key. **Virtual node** (mỗi node vật lý nhiều điểm trên vòng) để chia đều và chia theo năng lực máy
- [ ] **Bloom filter** 🔴 (tóm tắt): mảng bit + k hàm hash. Thêm: bật k bit. Kiểm tra: cả k bit bật → "có thể có"; một bit tắt → "chắc chắn không". Bloom filter chuẩn không xoá được (counting bloom filter thì xoá được)

### Availability

- [ ] **Bảng số 9**

  | Availability | Downtime/năm | Downtime/tháng (30 ngày) |
  |---|---|---|
  | 99% | ~3,65 ngày | ~7,2 giờ |
  | 99,9% | ~8,76 giờ | ~43,2 phút |
  | 99,99% | ~52,6 phút | ~4,3 phút |
  | 99,999% | ~5,26 phút | ~26 giây |

  - Mỗi số 9 thêm vào đắt hơn nhiều: cần tự động failover (con người không phản ứng kịp trong 4 phút), multi-AZ/region, deploy an toàn
- [ ] **Chuỗi phụ thuộc**: gọi nối tiếp thì nhân availability (3 thành phần 99,9% → ~99,7%). Chạy song song dự phòng thì tăng: hai bản độc lập 99% → 1 − 0,01² = 99,99% (nếu lỗi thật sự độc lập — ⚠️ thường không)
- [ ] **SPOF** 🟡: tìm từng thành phần mà chết là cả hệ thống chết: một DB primary, một LB, một Redis, một cron server, một nhà cung cấp DNS, một người duy nhất biết deploy
- [ ] **Redundancy**: N+1 (dư một), N+2 (dư hai để vẫn an toàn khi đang bảo trì một máy)
- [ ] **Active-passive vs active-active** 🟡

  | | Active-passive | Active-active |
  |---|---|---|
  | Cách chạy | Một bản phục vụ, một bản chờ | Cả hai cùng phục vụ |
  | Failover | Chậm hơn (phát hiện + promote), có thể mất dữ liệu chưa sao chép | Nhanh, traffic chuyển sang bản còn lại |
  | Tài nguyên | Bản chờ lãng phí | Dùng hết, nhưng mỗi bản phải chịu được toàn bộ tải khi bản kia chết |
  | Khó ở | Split-brain khi promote | Ghi ở nhiều nơi: xung đột, consistency |

- [ ] **Multi-AZ, multi-region** 🔴
  - Multi-AZ: chống mất một datacenter; latency giữa AZ thấp nên replication đồng bộ được. Đây là mức mặc định cho production
  - Multi-region: chống mất cả vùng, phục vụ người dùng gần hơn; latency giữa region cao nên replication thường bất đồng bộ → RPO > 0, xung đột ghi
  - Cách phổ biến: đọc ở mọi region, ghi về một region chính; hoặc chia user theo "home region"
  - Chi tiết HA/DR ở [18-reliability-observability.md](18-reliability-observability.md)

### Bài 1: URL shortener 🟢

- **Requirement**
  - Functional: tạo mã ngắn cho URL dài, redirect, (tuỳ chọn) custom alias, hết hạn, thống kê click
  - Non-functional: redirect latency thấp (p99 vài chục ms), availability cao, mã không đoán được (tuỳ yêu cầu)
- **Ước lượng**: xem ví dụ tính mẫu ở trên (40 QPS ghi, 4.000 QPS đọc, 6 tỉ URL, 3 TB)
- **API**
  - `POST /urls {long_url, custom_alias?, expire_at?}` → `{code, short_url}`
  - `GET /{code}` → `301`/`302` + header `Location`
- **Data model**: `urls(code PK, long_url, user_id, created_at, expire_at)`. Truy cập chủ yếu theo `code` → KV hoặc SQL đều được
- **Độ dài mã**: base62 (a-z, A-Z, 0-9). 62^7 ≈ 3,5 × 10^12, dư cho 6 × 10^9
- **Sinh mã** (điểm deep dive chính)

  | Cách | Ưu | Nhược |
  |---|---|---|
  | ID tự tăng/Snowflake → base62 | Không trùng, không cần kiểm tra | Đoán được mã kế tiếp (lộ số lượng, bị cào); cần sinh ID phân tán |
  | Hash (MD5/SHA) URL, lấy 7 ký tự | Cùng URL ra cùng mã (dedup tự nhiên) | Trùng (collision) → phải kiểm tra và thử lại |
  | Random 7 ký tự | Không đoán được | Kiểm tra trùng; tỉ lệ trùng tăng khi đầy |
  | Pre-generate (key service phát sẵn lô mã) | Nhanh, không trùng | Thêm một service; mất lô mã khi server chết (chấp nhận được) |

  - Kiểm tra trùng an toàn: `INSERT` với unique constraint trên `code`, lỗi thì sinh lại. ⚠️ Đừng "SELECT xem có chưa rồi INSERT" (race condition)
- **Redirect `301` vs `302`**
  - `301` (permanent): browser cache, lần sau không gọi lại server → giảm tải nhưng **mất thống kê click**
  - `302` (temporary) hoặc `307`: mọi click qua server → thống kê được, tải cao hơn
- **Kiến trúc**

  ```
  client ─► CDN/LB ─► API (stateless) ─► Redis cache (code → long_url)
                                     └─► DB (sharded theo code nếu cần)
                         └─► Kafka (click event) ─► analytics store
  ```
- **Deep dive**
  - Cache: cache-aside, TTL; URL nóng nằm trong Redis; cache cả kết quả "không tồn tại" ngắn hạn để chống dò mã
  - Thống kê: ghi click event vào queue bất đồng bộ, không ghi DB trong đường redirect
  - Sharding theo `code` (hash) khi cần
- **Trade-off**: mã đoán được vs đơn giản; `301` vs thống kê; consistency (URL vừa tạo phải redirect được ngay → đọc từ primary hoặc ghi cache khi tạo)
- **Hỏi tiếp**: custom alias trùng? URL độc hại (kiểm tra với danh sách đen)? Xoá URL hết hạn (job dọn dẹp, hoặc TTL của DB)? Rate limit tạo URL?

### Bài 2: Rate limiter 🟡

- **Requirement**: giới hạn theo user/API key/IP/endpoint; phân tán (nhiều instance gateway); latency thêm vào rất nhỏ; trả `429 Too Many Requests`; quy tắc cấu hình được
- **Thuật toán**

  | Thuật toán | Cách làm | Ưu | Nhược |
  |---|---|---|---|
  | Token bucket | Xô chứa tối đa B token, nạp r token/giây; mỗi request lấy 1 token | Cho phép burst tới B, bộ nhớ nhỏ, phổ biến nhất | Hai tham số cần chỉnh |
  | Leaky bucket | Request vào hàng đợi, xử lý với tốc độ cố định | Output đều | Burst bị xếp hàng/làm chậm |
  | Fixed window | Đếm trong từng cửa sổ (mỗi phút) | Đơn giản nhất | ⚠️ Burst gấp đôi ở ranh giới cửa sổ (cuối phút này + đầu phút sau) |
  | Sliding window log | Lưu timestamp mọi request, đếm trong cửa sổ trượt | Chính xác | Tốn bộ nhớ theo số request |
  | Sliding window counter | Ước lượng: `đếm_hiện_tại + đếm_trước × (phần cửa sổ trước còn nằm trong cửa sổ trượt)` | Gần đúng, rẻ | Xấp xỉ |

- **Nơi đặt**: API gateway/edge (chặn sớm), middleware trong service, hoặc cả hai. Rate limit ở client (SDK) chỉ là lịch sự, không tin được
- **Lưu counter**: Redis, dùng thao tác nguyên tử. ⚠️ `GET` rồi `SET` từ app là race condition; dùng `INCR` + `EXPIRE` (fixed window) hoặc Lua script (token bucket) để đọc-sửa-ghi trong một bước

  ```lua
  -- fixed window: KEYS[1] = "rl:{user}:{minute}", ARGV[1] = limit, ARGV[2] = ttl
  local n = redis.call('INCR', KEYS[1])
  if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[2]) end
  if n > tonumber(ARGV[1]) then return 0 end
  return 1
  ```
- **Response**: `429` + `Retry-After`; thường kèm header báo limit/remaining (`X-RateLimit-*` hoặc theo draft chuẩn `RateLimit-*`)
- **Deep dive**
  - Redis chết thì sao: fail-open (cho qua, ưu tiên availability) hay fail-closed (chặn, ưu tiên bảo vệ). Thường fail-open kèm limit local trong bộ nhớ mỗi instance
  - Latency: mỗi request thêm một round trip Redis (~0,5 ms trong DC). Giảm bằng local counter đồng bộ định kỳ (đổi lấy độ chính xác)
  - Multi-region: counter theo region (mỗi region một phần quota) hay đồng bộ toàn cục (chậm)
  - Hot key: một API key lớn dồn vào một Redis node
- **Trade-off**: chính xác vs rẻ; toàn cục vs cục bộ; fail-open vs fail-closed
- **Hỏi tiếp**: limit nhiều tầng (per second và per day)? Ưu tiên khách trả tiền? Rate limit theo chi phí request (tính token cho request nặng)? Chống DDoS là việc của tầng khác (WAF, CDN)

### Bài 3: Notification system 🟡

- **Requirement**: gửi email, SMS, push (iOS/Android), in-app; gửi ngay và theo lịch; template; tuỳ chọn của người dùng (tắt kênh, giờ yên lặng); không gửi trùng; theo dõi trạng thái gửi
- **Ước lượng**: ví dụ 10 triệu push/ngày ≈ 120/giây trung bình, nhưng campaign marketing có thể dồn hàng triệu trong vài phút → queue là bắt buộc
- **Kiến trúc**

  ```
  service nghiệp vụ ─► Notification API ─► kiểm tra preference, rate limit, render template
                                        └─► queue theo kênh: [email] [sms] [push]
                                              │       │       │
                                         worker   worker   worker ─► SES/SendGrid, Twilio, APNs/FCM
                                              └─► log trạng thái (sent, delivered, failed)
  ```
- **Deep dive**
  - Queue riêng từng kênh: một provider SMS chậm không chặn email; scale worker riêng
  - Retry có backoff khi provider lỗi tạm; DLQ khi lỗi vĩnh viễn (token push hết hạn → xoá token)
  - **Chống gửi trùng**: at-least-once nên phải có idempotency key (`event_id + user_id + channel`), lưu đã gửi trong bảng có unique constraint hoặc Redis `SET NX` với TTL
  - Ưu tiên: OTP/giao dịch đi queue ưu tiên cao, marketing đi queue thấp; ⚠️ campaign không được làm chậm OTP
  - Rate limit theo user (không spam) và theo provider (quota của nhà cung cấp)
  - Theo lịch và múi giờ: lưu thời điểm UTC, tính giờ yên lặng theo timezone của user
- **Trade-off**: độ tin cậy (at-least-once + dedup) vs đơn giản; gửi đồng bộ trong request (không nên) vs qua queue
- **Hỏi tiếp**: theo dõi mở email/click? Gộp nhiều thông báo (digest)? Fallback kênh (push thất bại thì SMS)? Opt-out theo luật?

### Bài 4: News feed 🟡

- **Requirement**: đăng bài; xem feed gồm bài của người mình follow, sắp theo thời gian (hoặc ranking); feed load nhanh (p99 < vài trăm ms); đọc nhiều hơn ghi rất nhiều
- **Ước lượng**: 100 triệu DAU, mỗi người mở feed 10 lần/ngày → 10^9/10^5 = 10.000 QPS đọc; mỗi người đăng 0,1 bài/ngày → ~100 QPS ghi
- **API**: `POST /posts`, `GET /feed?cursor=...&limit=20` (cursor pagination, không dùng offset)
- **Data model**: `posts(id, author_id, content, created_at)`, `follows(follower_id, followee_id)`, feed cache: Redis list/sorted set `feed:{user_id}` chứa post id
- **Fan-out** (điểm deep dive chính)

  | | Fan-out on write (push) | Fan-out on read (pull) |
  |---|---|---|
  | Cách làm | Đăng bài → ghi post id vào feed của mọi follower | Mở feed → lấy bài mới của từng người mình follow rồi merge |
  | Đọc | Rất nhanh (đọc sẵn một list) | Chậm, fan-out nhiều query |
  | Ghi | Đắt với người có nhiều follower | Rẻ |
  | ⚠️ Vấn đề | Người nổi tiếng 10 triệu follower = 10 triệu lần ghi mỗi bài | Người follow 2.000 tài khoản = 2.000 nguồn để merge |

  - **Hybrid**: người bình thường dùng push; người nổi tiếng (follower vượt ngưỡng) dùng pull. Khi đọc feed: lấy feed đã push + merge bài mới của các tài khoản nổi tiếng mình follow
  - Không push cho user không hoạt động lâu ngày (tiết kiệm ghi); dựng lại feed khi họ quay lại
- **Kiến trúc**: Post service ghi DB → phát event `PostCreated` → fan-out worker đọc danh sách follower, ghi vào Redis feed (giữ N bài gần nhất) → Feed service đọc list id, hydrate nội dung từ post cache
- **Deep dive**
  - Feed cache chỉ lưu id; nội dung bài lấy từ cache riêng (sửa/xoá bài không cần sửa hàng triệu feed)
  - Xoá bài: lọc khi đọc (bài đã xoá thì bỏ qua) thay vì xoá khỏi mọi feed
  - Ranking: thêm tầng tính điểm (tương tác, độ mới); đổi feed từ thời gian sang thứ tự theo điểm
- **Hỏi tiếp**: like/comment count (counter xấp xỉ, gom ghi)? Media (object storage + CDN)? Feed real-time (push qua WebSocket/SSE)?

### Bài 5: Chat / messenger 🟡

- **Requirement**: chat 1-1 và nhóm; gửi nhận real-time; lịch sử tin nhắn; trạng thái đã gửi/đã nhận/đã đọc; online presence; nhiều thiết bị; thông báo khi offline
- **Ước lượng**: 50 triệu DAU, 40 tin/người/ngày → 2 × 10^9 tin/ngày ≈ 20.000 tin/giây; 100 byte/tin → 200 GB/ngày → cần storage ghi nhiều, scale ngang
- **Kết nối**: WebSocket (hai chiều, giữ kết nối lâu). Long polling là phương án dự phòng. Kết nối stateful → chat server không hoàn toàn stateless
- **Kiến trúc**

  ```
  client ═WebSocket═ chat server A ─┐                 ┌─ chat server B ═ người nhận
                                     ├─► message store │
                                     └─► pub/sub / routing (user → server nào) ─┘
                                     └─► push service (APNs/FCM) nếu người nhận offline
  ```
  - Session registry: `user_id → chat server` (Redis). Server A nhận tin, lưu, tra registry, chuyển sang server B qua pub/sub hoặc gọi nội bộ
- **Data model**: `messages(conversation_id, message_id, sender_id, content, created_at)`, partition key `conversation_id`, sắp theo `message_id`. Wide-column (Cassandra/ScyllaDB) hoặc SQL sharded theo `conversation_id`
- **Deep dive**
  - **Thứ tự tin nhắn**: không dựa vào đồng hồ client. Dùng id tăng dần trong phạm vi conversation (sequence per conversation, hoặc Snowflake-like id có thời gian)
  - **Giao tin tin cậy**: client gửi kèm `client_msg_id` (idempotency, retry không tạo tin trùng); server ack sau khi lưu; người nhận ack "đã nhận"; client lưu `last_seen_message_id` để đồng bộ lại khi reconnect
  - **Nhóm**: nhóm nhỏ fan-out tới từng thành viên; nhóm rất lớn/kênh thì người nhận kéo (giống feed)
  - **Presence**: heartbeat định kỳ; hết hạn heartbeat → offline. ⚠️ Broadcast thay đổi presence cho mọi bạn bè tốn kém; chỉ gửi cho người đang mở cuộc trò chuyện hoặc lấy khi cần
  - Nhiều thiết bị: mỗi thiết bị một kết nối và con trỏ đồng bộ riêng
- **Trade-off**: WebSocket stateful khó scale/deploy (drain kết nối khi deploy); lưu tin vĩnh viễn vs chi phí; end-to-end encryption thì server không đọc được nội dung (không search phía server)
- **Hỏi tiếp**: gửi file/ảnh? Search lịch sử? Tin nhắn tự huỷ? Chat server chết thì client reconnect tới server khác và đồng bộ thế nào?

### Bài 6: Đặt vé / đặt phòng 🟡

- **Requirement**: xem chỗ còn trống; chọn chỗ; **giữ chỗ tạm** trong N phút để thanh toán; xác nhận; **không bao giờ double booking**; chịu được đợt mở bán
- **Hai kiểu tồn kho**
  - Chỗ cụ thể (ghế A12 suất 19h): mỗi ghế một hàng
  - Số lượng (phòng Deluxe ngày 1/10 còn 5): một hàng đếm theo (loại phòng, ngày)
- **Data model**

  ```sql
  -- chỗ cụ thể
  seats(show_id, seat_no, status, hold_id, hold_until, booking_id,
        PRIMARY KEY (show_id, seat_no))
  -- theo số lượng
  room_inventory(room_type_id, date, total, reserved, PRIMARY KEY (room_type_id, date))
  ```
- **Chống double booking** (điểm deep dive chính)
  - Conditional update nguyên tử, kiểm tra số dòng bị ảnh hưởng:

  ```sql
  UPDATE seats SET status = 'HELD', hold_id = ?, hold_until = NOW() + INTERVAL 10 MINUTE
  WHERE show_id = ? AND seat_no = ?
    AND (status = 'AVAILABLE' OR (status = 'HELD' AND hold_until < NOW()));
  -- affected rows = 0 → ghế đã bị người khác giữ

  UPDATE room_inventory SET reserved = reserved + 1
  WHERE room_type_id = ? AND date = ? AND reserved < total;
  ```
  - Đặt nhiều đêm/nhiều ghế: làm trong một transaction, khoá theo thứ tự cố định (sắp theo ngày/số ghế) để tránh deadlock; một dòng thất bại thì rollback cả
  - Các cách khác: `SELECT ... FOR UPDATE` (pessimistic), optimistic locking với `version`, unique constraint trên `(show_id, seat_no)` ở bảng booking. ⚠️ Kiểm tra ở app rồi mới ghi (check-then-act) là race condition
- **Giữ chỗ tạm**
  - Trạng thái: `AVAILABLE → HELD (hold_until) → BOOKED`, hoặc `HELD → AVAILABLE` khi hết hạn/huỷ
  - Hết hạn: kiểm tra `hold_until` ngay trong điều kiện UPDATE (như trên) nên không phụ thuộc job dọn dẹp chạy đúng giờ; job dọn dẹp chỉ để hiển thị cho đúng
  - ⚠️ Thanh toán thành công **sau** khi hold hết hạn và ghế đã bán cho người khác → cần quy trình hoàn tiền; hoặc gia hạn hold khi người dùng đã vào bước thanh toán
- **Mở bán (tải đột biến)**: waiting room/virtual queue, cache sơ đồ ghế (hiển thị có thể hơi cũ, ghi luôn kiểm tra ở DB), rate limit
- **Trade-off**: pessimistic lock đơn giản nhưng giảm throughput trên hàng nóng; Redis giữ chỗ nhanh nhưng phải đối chiếu với DB là nguồn sự thật
- **Hỏi tiếp**: overbooking có chủ đích (khách sạn, hãng bay)? Đồng bộ tồn kho với OTA (Booking, Agoda) — lệch tồn kho giữa các kênh? Hoàn/huỷ?

### Bài 7: Thanh toán / ví điện tử 🔴

- **Requirement**: nạp tiền, chuyển tiền giữa ví, thanh toán cho merchant qua cổng thanh toán (PSP); số dư luôn đúng; không trừ tiền hai lần; audit được; đối soát với ngân hàng/PSP
- **Non-functional**: correctness quan trọng hơn latency; consistency mạnh cho số dư; mọi thay đổi có lịch sử
- **Nguyên tắc**
  - Tiền lưu bằng số nguyên theo đơn vị nhỏ nhất (VND không có phần lẻ; USD lưu cent) hoặc `DECIMAL`. ⚠️ Không dùng `float` — xem [22-practical-data.md](22-practical-data.md)
  - **Ledger theo bút toán kép (double-entry)**: mỗi giao dịch sinh ít nhất hai entry, tổng debit = tổng credit. Không bao giờ chỉ `UPDATE balance` mà không có lịch sử
  - Entry là **append-only**; sửa sai bằng entry đảo (reversal), không sửa/xoá entry cũ
- **Data model**

  ```sql
  accounts(id, owner_id, currency, balance, version)       -- balance là cache của ledger
  transactions(id, idempotency_key UNIQUE, type, status, created_at)
  ledger_entries(id, transaction_id, account_id, direction, amount, created_at)
  -- chuyển 100.000 từ A sang B: entry debit A 100.000, entry credit B 100.000
  ```
- **Chuyển tiền nội bộ**: một transaction DB: insert `transactions`, insert hai entry, cập nhật balance hai tài khoản với điều kiện `balance >= amount` (hoặc khoá `FOR UPDATE` theo thứ tự id để tránh deadlock)
- **Idempotency** (deep dive 1)
  - Client gửi `Idempotency-Key`; server lưu key kèm kết quả; request lặp lại trả lại kết quả cũ, không xử lý lần hai
  - Unique constraint trên key; xử lý trường hợp request thứ hai tới khi request đầu còn đang chạy (trạng thái `PROCESSING`, trả 409 hoặc chờ)
  - Gọi PSP cũng truyền idempotency key của mình (các PSP lớn đều hỗ trợ)
- **Luồng với PSP** (deep dive 2)
  - Trạng thái: `CREATED → PENDING → SUCCEEDED / FAILED`, có thể `UNKNOWN` khi timeout
  - ⚠️ Timeout khi gọi PSP **không có nghĩa là thất bại**. Không tự retry tạo giao dịch mới; hỏi lại trạng thái (query API) hoặc chờ webhook
  - Webhook: xác thực chữ ký, xử lý idempotent (webhook đến nhiều lần, sai thứ tự), trả 2xx nhanh rồi xử lý qua queue
  - Outbox để phát event "đã thanh toán" nhất quán với ghi DB
- **Reconciliation** (deep dive 3)
  - Hằng ngày đối chiếu ledger nội bộ với file/báo cáo của PSP và sao kê ngân hàng: khớp theo mã giao dịch, số tiền, trạng thái
  - Các loại lệch: có ở PSP mà không có ở mình (webhook mất), ngược lại, lệch số tiền/trạng thái
  - Lệch thì tạo case xử lý (tự động hoặc thủ công), không tự sửa số dư im lặng
  - Kiểm tra nội bộ: tổng mọi entry = 0 theo từng currency; balance = tổng entry của tài khoản
- **Trade-off**: consistency mạnh (SQL, transaction) hơn là scale; hot account (ví merchant lớn nhận hàng nghìn giao dịch/giây) → tách sub-account, gom ghi, hoặc cập nhật balance bất đồng bộ từ ledger
- **Hỏi tiếp**: refund và partial refund? Đa tiền tệ, tỷ giá? Chống gian lận? Giữ tiền (authorization/capture)? Audit và phân quyền truy cập?

### Bài 8: Flash sale 🔴

- **Requirement**: 1.000 sản phẩm giá sốc, mở lúc 12:00, hàng triệu người vào cùng lúc; **không bán vượt tồn kho (oversell)**; hệ thống khác (mua hàng thường) không bị ảnh hưởng; công bằng, chống bot
- **Đặc điểm**: traffic tăng hàng trăm lần trong vài giây, nhưng số đơn thành công rất nhỏ (1.000). Mục tiêu là **từ chối rẻ** càng sớm càng tốt
- **Kiến trúc theo tầng lọc**

  ```
  client (nút mua disable tới giờ, captcha) ─► CDN (trang tĩnh, đồng hồ đếm ngược)
     ─► gateway (rate limit theo user/IP, chặn bot) ─► waiting room (tuỳ chọn)
     ─► flash sale service: trừ tồn kho trong Redis (Lua, nguyên tử)
            └─ thành công ─► queue ─► order worker tạo đơn trong DB, giữ chỗ chờ thanh toán
            └─ hết hàng   ─► trả "hết hàng" ngay
  ```
- **Deep dive**
  - Trừ kho nguyên tử trong Redis: Lua script kiểm tra `stock > 0` và user chưa mua (set các user đã mua), rồi `DECR`. Nhanh hơn nhiều so với khoá hàng trong DB
  - DB vẫn là nguồn sự thật: order worker ghi đơn với conditional update trên tồn kho DB; Redis chỉ là bộ lọc trước
  - Mất đồng bộ Redis–DB: Redis chết/mất dữ liệu → khôi phục từ DB; tồn kho Redis thấp hơn thật thì bán thiếu (chấp nhận được), cao hơn thì DB chặn oversell
  - Không thanh toán trong hạn → trả hàng về kho (cộng lại Redis và DB)
  - Cô lập: flash sale chạy trên hạ tầng/cluster riêng hoặc ít nhất pool riêng, để mua hàng thường không chết theo
  - Chuẩn bị trước: warm cache, scale trước (autoscaling không kịp đỉnh tính bằng giây), load test ở quy mô thật
- **Trade-off**: công bằng (queue theo thứ tự) vs đơn giản (ai nhanh người đó được); UX (chờ trong waiting room) vs tải
- **Hỏi tiếp**: một hot key tồn kho làm nghẽn một Redis node → chia tồn kho thành nhiều key (bucket) trên nhiều node? Chống một người dùng nhiều tài khoản?

### Bài 9: Distributed ID generator 🔴

- **Requirement**: duy nhất toàn cục, sinh ở nhiều máy không phối hợp, nhanh; thường cần sắp theo thời gian (tốt cho B-tree index); 64 bit nếu được
- **Các phương án**

  | Cách | Ưu | Nhược |
  |---|---|---|
  | Auto-increment một DB | Đơn giản, gọn | SPOF, giới hạn throughput, lộ số lượng |
  | Nhiều DB, mỗi cái bước nhảy khác (offset + step) | Hết SPOF | Khó thêm node, thứ tự không toàn cục |
  | UUID v4 | Sinh ở đâu cũng được | 128 bit, ngẫu nhiên → ⚠️ chèn vào B-tree clustered index gây phân mảnh |
  | UUID v7 (RFC 9562) | 128 bit nhưng có timestamp ở đầu → sắp theo thời gian | Vẫn 128 bit, lộ thời điểm tạo |
  | Snowflake | 64 bit, sắp theo thời gian, phân tán | Cần gán worker id, phụ thuộc đồng hồ |
  | Segment/range allocation | Mỗi server xin một dải id (1.000 số) từ DB rồi phát trong bộ nhớ | Mất dải khi crash, có khoảng trống |

- **Snowflake**: `1 bit dấu | 41 bit timestamp ms | 10 bit machine id | 12 bit sequence`
  - 41 bit ms ≈ 69 năm kể từ epoch tuỳ chọn; 12 bit sequence = 4.096 id mỗi ms mỗi máy; 10 bit = 1.024 máy
  - ⚠️ Đồng hồ chạy lùi (NTP chỉnh) → có thể sinh trùng. Xử lý: phát hiện và chờ tới khi đồng hồ vượt timestamp cuối, hoặc từ chối sinh
  - Gán machine id: config, hoặc xin từ ZooKeeper/etcd/DB khi khởi động
- **Hỏi tiếp**: id có cần không đoán được (id công khai trên URL)? Có cần sắp chặt chẽ toàn cục (thường không; "gần đúng theo thời gian" là đủ)?

### Bài 10: Key-value store 🔴

- **Requirement**: `put(key, value)`, `get(key)`; dữ liệu lớn hơn một máy; availability cao; latency thấp; consistency chỉnh được
- **Thành phần** (theo hướng Dynamo/Cassandra)
  - **Partition**: consistent hashing với virtual node
  - **Replication**: mỗi key lưu ở N node kế tiếp trên vòng (thường N = 3, rải qua các AZ)
  - **Quorum**: ghi thành công khi W node xác nhận, đọc từ R node. `W + R > N` thì đọc chắc chắn chạm ít nhất một bản mới nhất (ví dụ N=3, W=2, R=2). W=1, R=1 nhanh nhưng eventual
  - **Xung đột**: last-write-wins theo timestamp (đơn giản, có thể mất ghi) hoặc vector clock (phát hiện xung đột, client giải quyết)
  - **Node tạm chết**: hinted handoff (node khác nhận hộ rồi trả lại); **node lệch lâu**: anti-entropy bằng Merkle tree; read repair khi đọc thấy bản cũ
  - **Membership, phát hiện lỗi**: gossip protocol
  - **Storage engine**: LSM-tree — ghi vào WAL + memtable, flush thành SSTable bất biến, compaction gộp file; mỗi SSTable có bloom filter để bỏ qua file chắc chắn không chứa key
- **Trade-off**: CAP/PACELC — chọn availability (AP) hay consistency (CP) khi partition; chi tiết ở [14-distributed-systems.md](14-distributed-systems.md)
- **Hỏi tiếp**: thêm node thì dữ liệu di chuyển thế nào? TTL? Range query (consistent hashing phá thứ tự key)?

### Bài 11: Web crawler 🔴

- **Requirement**: crawl hàng tỉ trang, lịch sự với website (politeness), tránh trùng, recrawl trang thay đổi, chịu lỗi
- **Luồng**: seed URL → **URL frontier** → fetcher (DNS resolver có cache) → lưu nội dung (object storage) → parser trích link → lọc (đã thấy chưa, robots.txt, domain được phép) → đưa lại frontier
- **Deep dive**
  - URL frontier: hàng đợi ưu tiên (trang quan trọng/thay đổi nhiều crawl trước) + hàng đợi theo host để đảm bảo politeness (mỗi host một tốc độ, tôn trọng `robots.txt` và crawl-delay)
  - Dedup URL: chuẩn hoá URL (bỏ fragment, sắp query param...) + bloom filter hoặc set phân tán
  - Dedup nội dung: hash nội dung (trùng hệt), SimHash/MinHash (gần trùng)
  - ⚠️ Crawler trap: URL sinh vô hạn (lịch vô tận, session id trong URL) → giới hạn độ sâu, độ dài URL, số trang mỗi host
  - Phân tán: chia theo hash của host để một host chỉ do một worker phụ trách (dễ giữ politeness)
- **Hỏi tiếp**: render JavaScript (headless browser, tốn gấp nhiều lần)? Recrawl theo tần suất thay đổi?

### Bài 12: Search autocomplete 🔴

- **Requirement**: gõ prefix → trả top 5–10 gợi ý phổ biến nhất trong vài chục ms; cập nhật độ phổ biến theo ngày/giờ; lọc từ khoá xấu
- **Cấu trúc**: **trie**; mỗi node lưu sẵn **top-k** từ khoá của cây con, nên truy vấn là O(độ dài prefix) thay vì duyệt cả cây con
- **Hai đường**
  - Offline: log truy vấn → job tổng hợp (theo ngày/giờ, có trọng số độ mới) → build trie mới → phát hành snapshot cho các server phục vụ
  - Online: server giữ trie trong bộ nhớ, chỉ đọc; thay snapshot nguyên khối khi có bản mới
- **Deep dive**: shard theo prefix (chú ý phân bố lệch: prefix "a" nhiều hơn "x" rất nhiều); cache kết quả prefix phổ biến ở CDN/browser; client debounce (chờ người dùng ngừng gõ vài chục ms) để giảm request
- **Trade-off**: độ tươi (trending real-time cần luồng stream riêng) vs đơn giản (build theo lô)
- **Hỏi tiếp**: cá nhân hoá? Sửa lỗi chính tả? Tiếng Việt có dấu/không dấu (chuẩn hoá bỏ dấu khi index) — xem [22-practical-data.md](22-practical-data.md)

### Bài 13: File storage (Google Drive / Dropbox) 🔴

- **Requirement**: upload/download file lớn, đồng bộ nhiều thiết bị, lịch sử phiên bản, chia sẻ; tiết kiệm băng thông và dung lượng
- **Tách hai loại dữ liệu**: nội dung (block) trên object storage; metadata (file, folder, version, danh sách chunk, quyền) trên SQL — cần consistency mạnh
- **Deep dive**
  - **Chunking**: chia file thành block (vài MB). Upload song song, resume khi mất mạng, chỉ upload lại block thay đổi (delta sync). Chunk kích thước cố định đơn giản; content-defined chunking (rolling hash) giữ được ranh giới khi chèn dữ liệu vào giữa file
  - **Dedup**: định danh block bằng hash nội dung (SHA-256); block đã có thì không upload lại. ⚠️ Dedup chéo người dùng lộ thông tin "file này đã tồn tại" — cân nhắc chỉ dedup trong phạm vi một user
  - Upload thẳng lên object storage bằng pre-signed URL, không đi qua app server
  - **Sync**: client giữ con trỏ phiên bản; server thông báo thay đổi (long polling/WebSocket); client kéo danh sách thay đổi rồi tải block thiếu
  - **Xung đột**: hai thiết bị sửa cùng file offline → không tự merge file nhị phân; tạo "bản xung đột" để người dùng chọn
  - Version: mỗi version là một danh sách block; block không còn version nào tham chiếu thì dọn (garbage collection)
- **Hỏi tiếp**: chia sẻ và phân quyền? File rất nóng (link công khai) → CDN? Mã hoá phía client?

### Bài 14: Video streaming 🔴 (đại ý)

- Upload: resumable/multipart lên object storage bằng pre-signed URL
- Xử lý: queue → transcode sang nhiều độ phân giải/bitrate, cắt thành segment vài giây, tạo manifest **HLS/DASH**, thumbnail. Việc này tốn CPU/GPU, chạy song song theo segment
- Phát: CDN phục vụ segment; player dùng **adaptive bitrate** (chọn chất lượng theo băng thông hiện tại)
- Metadata (tiêu đề, trạng thái xử lý, lượt xem) trong DB; lượt xem đếm bất đồng bộ
- Chi phí chủ yếu là băng thông CDN và storage; video ít người xem có thể không cần transcode mọi độ phân giải
- Hỏi tiếp: live streaming (độ trễ thấp, khác hẳn VOD)? DRM? Resume vị trí xem?

### Bài 15: Ride-hailing / nearby search 🔴

- **Requirement**: tài xế gửi vị trí vài giây một lần; khách tìm tài xế gần trong bán kính; ghép chuyến; theo dõi chuyến real-time
- **Ước lượng**: 1 triệu tài xế online, cập nhật mỗi 4 giây → 250.000 ghi/giây. Ghi rất nhiều, dữ liệu vị trí sống ngắn → giữ trong bộ nhớ, không ghi mọi điểm vào DB chính
- **Geo index**

  | Cách | Ý tưởng | Ghi chú |
  |---|---|---|
  | Geohash | Mã hoá lat/long thành chuỗi; prefix chung = gần nhau. Độ dài 6 ≈ ô khoảng 1,2 km × 0,6 km | ⚠️ Hai điểm sát nhau nhưng ở hai bên ranh giới ô có prefix khác → phải tìm cả 8 ô lân cận |
  | Quadtree | Chia ô thành 4 khi quá nhiều điểm | Hợp mật độ không đều (thành phố vs nông thôn); cập nhật động phức tạp hơn |
  | H3 (lục giác) | Lưới lục giác phân cấp | Khoảng cách tới các ô lân cận đều nhau |
  | Redis GEO | `GEOADD`, `GEOSEARCH` (bên trong dùng sorted set + geohash) | Tiện cho quy mô vừa |

- **Deep dive**: shard vị trí theo vùng/thành phố; ghép chuyến phải tránh gán một tài xế cho hai khách (khoá/giữ chỗ tài xế có TTL, giống bài đặt vé); lịch sử lộ trình ghi bất đồng bộ qua stream để tính cước/audit
- **Hỏi tiếp**: surge pricing? ETA (định tuyến trên bản đồ, không phải khoảng cách đường chim bay)?

### Bài 16: Leaderboard 🟡

- **Redis sorted set**: `ZADD` (hoặc `ZINCRBY`) cập nhật điểm, `ZREVRANGE 0 9` lấy top 10, `ZREVRANK` lấy hạng của một user — các thao tác O(log N)
- Hạng bằng nhau: mã hoá điểm kèm thời điểm (ai đạt trước xếp trên) vào score
- Leaderboard theo tuần/tháng: mỗi kỳ một key, TTL sau khi hết kỳ
- DB là nguồn sự thật cho điểm; Redis dựng lại được từ DB
- Quy mô rất lớn (hàng trăm triệu user): chia theo khoảng điểm/shard; hạng chính xác cho top, hạng xấp xỉ (percentile) cho phần còn lại
- ⚠️ Top-N ở nhiều shard: lấy top-N mỗi shard rồi merge

### Bài 17: Distributed job scheduler 🔴

- **Requirement**: chạy job theo lịch (cron) và job một lần tại thời điểm T; hàng triệu job; không mất job; không chạy trùng (hoặc chạy trùng vô hại); retry; xem lịch sử
- **Thiết kế cơ bản trên DB**

  ```sql
  jobs(id, type, payload, run_at, status, attempts, locked_by, locked_until)
  -- worker lấy job, nhiều worker không giành nhau:
  SELECT * FROM jobs WHERE status = 'PENDING' AND run_at <= NOW()
  ORDER BY run_at LIMIT 100 FOR UPDATE SKIP LOCKED;
  ```
  - `SKIP LOCKED` có ở PostgreSQL và MySQL 8. Worker đánh dấu `locked_until` (lease); worker chết thì lease hết hạn và job được lấy lại
- **Deep dive**
  - Cron: một "trigger" (chỉ một instance, dùng leader election hoặc lock phân tán) sinh bản chạy cụ thể vào bảng `jobs`; worker pool thực thi. ⚠️ Chạy cron trên mọi instance app = job chạy N lần
  - Đảm bảo at-least-once → job phải idempotent; exactly-once là ảo tưởng khi worker có thể chết sau khi làm xong nhưng trước khi ghi trạng thái
  - Retry có backoff, giới hạn số lần, chuyển `FAILED` + alert
  - Quy mô lớn: partition bảng job theo thời gian/hash; hoặc dùng timing wheel/delay queue; hoặc công cụ có sẵn (Temporal, Quartz cluster, Kubernetes CronJob cho việc đơn giản)
  - Job chạy lâu: heartbeat gia hạn lease, checkpoint tiến độ để resume
- **Hỏi tiếp**: phụ thuộc giữa job (DAG, kiểu Airflow)? Múi giờ và DST cho cron? Ưu tiên/fair share giữa tenant?

### Bài 18: Metrics / logging system 🔴

- **Metrics**: agent trên mỗi máy thu (hoặc Prometheus pull) → TSDB. Dữ liệu dạng `(metric, labels, timestamp, value)`; ghi rất nhiều, đọc theo khoảng thời gian
  - Nén theo thời gian, downsampling (giữ dữ liệu 10 giây trong 2 tuần, dữ liệu 5 phút trong 1 năm)
  - ⚠️ Cardinality: label có giá trị không giới hạn (user_id, URL đầy đủ) làm số time series bùng nổ
- **Logging**: app ghi stdout → agent (Fluent Bit, Vector, Promtail) → buffer (Kafka) → xử lý (parse, lọc PII, sampling) → lưu (Elasticsearch/OpenSearch: index full-text, đắt; Loki: chỉ index label, rẻ hơn, query chậm hơn) → object storage cho lưu lâu
  - Kafka làm buffer để hệ lưu trữ chậm/chết không làm mất log hoặc làm nghẽn app
  - Retention theo tầng nóng/ấm/lạnh để kiểm soát chi phí
- **Alerting**: rule engine đánh giá định kỳ, gom nhóm, định tuyến tới on-call
- Chi tiết khái niệm ở [18-reliability-observability.md](18-reliability-observability.md)

### Bài 19: "Một server, traffic tăng 10 lần" 🟢

Trả lời theo từng bước, mỗi bước kèm "đo cái gì để biết cần bước tiếp":
1. Đo: nút thắt là CPU app, DB, hay mạng? Có APM chưa?
2. Tách DB ra máy riêng; tối ưu query và index (thường là cải thiện lớn nhất, rẻ nhất)
3. Thêm cache (Redis) cho dữ liệu đọc nhiều; CDN cho file tĩnh
4. Làm app stateless (session ra Redis, file ra S3), thêm load balancer và nhiều instance
5. Đẩy việc chậm vào queue + worker
6. Read replica cho DB; tách đọc/ghi
7. Khi ghi vượt một node: partition/sharding, hoặc tách một phần dữ liệu sang store phù hợp
8. Suốt quá trình: monitoring, alert, load test, loại bỏ SPOF (LB dự phòng, DB có standby)

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Thiết kế URL shortener | Vẽ ngay API + DB + cache | Hỏi quy mô, tỉ lệ đọc/ghi, có cần thống kê không; ước lượng để thấy cache là trọng tâm và sharding chưa cần; so các cách sinh mã; nói `301`/`302` ảnh hưởng thống kê |
| Rate limiter | "Dùng Redis đếm" | So thuật toán theo burst và bộ nhớ; nói thao tác nguyên tử (Lua); Redis chết thì fail-open hay fail-closed; latency thêm vào; multi-region |
| Đặt vé chống double booking | "Kiểm tra còn chỗ rồi insert" | Conditional update/unique constraint, không check-then-act; hold có hạn kiểm tra ngay trong câu UPDATE; thanh toán về muộn sau khi hold hết hạn thì hoàn tiền |
| Thanh toán | "Trừ balance trong transaction" | Ledger kép append-only, idempotency key ở mọi tầng, timeout ≠ thất bại, webhook idempotent, reconciliation hằng ngày, hot account |
| Cần 99,99% | "Thêm server" | 99,99% ≈ 52 phút/năm nên failover phải tự động; tính availability của chuỗi phụ thuộc; multi-AZ; deploy an toàn (canary) vì phần lớn sự cố đến từ thay đổi |
| Chọn DB | "NoSQL vì scale" | Bắt đầu bằng pattern truy cập và yêu cầu consistency; SQL là mặc định cho tới khi có lý do cụ thể; nói rõ mất gì khi đổi |

## Tình huống

1. **Người phỏng vấn nói "Thiết kế Instagram" rồi im lặng.**
   - Gợi ý: đừng thiết kế cả Instagram. Chốt phạm vi: đăng ảnh, follow, xem feed; bỏ qua story, DM, search
   - Hỏi DAU, tỉ lệ đọc/ghi, yêu cầu latency; nói thành tiếng các giả định
   - Deep dive vào feed (fan-out) và lưu ảnh (object storage + CDN)

2. **Đang giữa bài URL shortener, người phỏng vấn nói "giờ traffic đọc tăng 100 lần".**
   - Gợi ý: ước lượng lại; cache hit rate và dung lượng cache; CDN cache redirect (nếu dùng `301` hoặc cache ngắn với `302`)
   - Hot key: vài URL viral → cache local trong app (in-process) trước Redis
   - DB đọc: replica; nói chuyện gì xảy ra khi cache cluster chết (thundering herd) — xem [11-cache.md](11-cache.md)

3. **Bài ví điện tử: "Gọi PSP bị timeout, giờ làm gì?"**
   - Gợi ý: trạng thái `UNKNOWN`, không tạo giao dịch mới; query trạng thái với cùng mã giao dịch; chờ webhook
   - Job định kỳ quét các giao dịch `UNKNOWN`/`PENDING` quá lâu để hỏi lại
   - Reconciliation cuối ngày bắt các trường hợp còn sót; không cộng/trừ tiền cho tới khi biết chắc

4. **Flash sale: sau đợt bán, phát hiện bán 1.012 sản phẩm trong khi chỉ có 1.000.**
   - Gợi ý: tìm chỗ check-then-act (đọc tồn kho rồi mới trừ), cache tồn kho không nguyên tử, retry tạo đơn trùng
   - Sửa: trừ kho nguyên tử (Lua/conditional update), DB là chốt chặn cuối, idempotency khi tạo đơn
   - Xử lý hậu quả: liên hệ khách, hoàn tiền, và postmortem

5. **Thiết kế chat: một chat server chết, 50.000 kết nối rớt cùng lúc.**
   - Gợi ý: client reconnect có backoff + jitter để không dội vào server còn lại
   - Tin nhắn không mất vì đã lưu trước khi ack; client đồng bộ theo `last_seen_message_id`
   - Session registry phải hết hạn/cập nhật; tin gửi trong lúc đó đi đường push

6. **Scheduler: job gửi báo cáo chạy hai lần mỗi sáng từ khi scale app lên 2 instance.**
   - Gợi ý: cron chạy trên mọi instance; dùng lock phân tán/leader election, hoặc tách cron ra một process duy nhất, hoặc bảng job với `SKIP LOCKED`
   - Và làm job idempotent (ghi dấu "đã gửi báo cáo ngày X") để trùng cũng vô hại

## ❓ Câu hỏi hay gặp

🟢
- Scale dọc và scale ngang khác nhau thế nào? Vì sao scale ngang cần stateless?
- 99,9% availability là bao nhiêu phút downtime mỗi tháng?
- Hệ thống của bạn đang chạy trên một server. Traffic tăng gấp 10 lần, bạn làm gì theo từng bước?
- Vì sao không lưu file upload trên ổ đĩa của app server?

🟡
- Thiết kế URL shortener phục vụ 100 triệu URL mới mỗi tháng.
- Thiết kế rate limiter cho API gateway.
- Fan-out on write và fan-out on read khác nhau thế nào? Xử lý người nổi tiếng ra sao?
- Thiết kế hệ thống notification đa kênh không gửi trùng.
- Thiết kế đặt phòng khách sạn không bị double booking.
- Active-passive và active-active khác nhau thế nào?

🔴
- Thiết kế ví điện tử: ledger, idempotency, reconciliation.
- Thiết kế flash sale 1.000 sản phẩm cho 1 triệu người.
- Snowflake ID gồm những phần nào? Đồng hồ chạy lùi thì sao?
- Thiết kế key-value store phân tán: partition, replication, quorum.
- Thiết kế Dropbox: chunking, dedup, sync, xung đột.
- Tìm tài xế gần nhất: geohash hay quadtree?
- Thiết kế job scheduler phân tán không chạy trùng.

## Bài tập tự làm

1. Tự làm bài URL shortener trong 45 phút theo đúng các bước và phân bổ thời gian, ghi ra giấy, sau đó tự chấm theo mục "Người chấm đánh giá gì".
2. Ước lượng cho một ứng dụng chat 20 triệu DAU: QPS gửi tin, storage mỗi năm, số kết nối WebSocket đồng thời, số chat server cần nếu mỗi server giữ được một số kết nối bạn tự giả định.
3. Viết Lua script token bucket cho Redis (tham số: capacity, refill rate), kèm giải thích vì sao phải chạy nguyên tử.
4. Thiết kế schema ledger cho ví điện tử hỗ trợ nạp, chuyển, refund; viết câu SQL kiểm tra ledger cân bằng.
5. Thiết kế hệ thống đặt vé xem phim cho một buổi mở bán 50.000 người: vẽ sơ đồ, viết câu UPDATE giữ ghế, mô tả xử lý thanh toán về muộn.

> Nộp bài vào đây để được review.
