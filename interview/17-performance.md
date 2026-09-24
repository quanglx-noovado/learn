# 17. Performance và scalability

> [← Mục lục](README.md) · Phạm vi: đo lường hiệu năng (latency, throughput, percentile, các định luật), quy trình tối ưu và profiling, nguyên nhân chậm theo từng tầng, các cách scale, load testing, capacity planning và autoscaling.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Khái niệm và định luật**
- [ ] 🟢 Latency vs throughput; bandwidth
- [ ] 🟢 Percentile p50/p95/p99 và vì sao không nhìn trung bình
- [ ] 🟡 Tail latency và fan-out
- [ ] 🟡 Little's law
- [ ] 🟡 Amdahl's law
- [ ] 🔴 Universal Scalability Law (USL)
- [ ] 🟡 Utilization và queueing: vì sao latency tăng vọt khi gần 100%

**Quy trình tối ưu**
- [ ] 🟢 Đo trước (baseline), tìm nút thắt, tối ưu, đo lại
- [ ] 🟡 Profiling: CPU, memory, I/O, lock
- [ ] 🟡 Flame graph: cách đọc
- [ ] 🟡 APM
- [ ] 🟡 Công cụ theo ngôn ngữ: Xdebug/Blackfire (PHP), `pprof` (Go), JFR/async-profiler (Java)

**Nguyên nhân chậm và checklist theo tầng**
- [ ] 🟢 Sáu nguyên nhân chậm thường gặp theo thứ tự
- [ ] 🟢 DB: N+1, index, lấy thừa, phân trang
- [ ] 🟢 Cache
- [ ] 🟡 Network: gọi song song, timeout, keep-alive, nén
- [ ] 🟡 App code: thuật toán, việc nặng trong request
- [ ] 🟡 Serialization
- [ ] 🔴 GC
- [ ] 🔴 Lock contention
- [ ] 🟡 Connection pool

**Scale**
- [ ] 🟢 Vertical vs horizontal; stateless
- [ ] 🟡 Read replica, sharding, cache, async, CDN
- [ ] 🔴 Precompute, materialized view, denormalize

**Load testing**
- [ ] 🟡 Các loại: load, stress, soak, spike
- [ ] 🟡 Công cụ: k6, JMeter, wrk, Gatling
- [ ] 🟡 Thiết kế bài test và đọc kết quả
- [ ] 🔴 Open vs closed model; coordinated omission

**Capacity và autoscaling**
- [ ] 🔴 Capacity planning, headroom
- [ ] 🟡 Autoscaling và cạm bẫy (scale chậm hơn spike, DB không scale theo)

## Chi tiết

### Khái niệm và định luật

- [ ] **Latency vs throughput** 🟢
  - Latency: thời gian một request (ms). Throughput: số request xử lý được mỗi đơn vị thời gian (RPS/QPS). Bandwidth: dung lượng đường truyền tối đa
  - Không tỉ lệ nghịch đơn giản: batching tăng throughput nhưng tăng latency; song song hoá tăng throughput nhưng không giảm latency của một việc tuần tự
  - Luôn nói latency **tại mức tải nào**. "p99 = 100 ms" không có nghĩa nếu không kèm RPS
- [ ] **Percentile** 🟢
  - p99 = 99% request nhanh hơn giá trị này. Trung bình che mất đuôi: 99 request 10 ms và 1 request 5 giây có trung bình ~60 ms
  - ⚠️ Không lấy trung bình của các percentile (trung bình p99 của 10 server không phải p99 toàn hệ thống). Phải tính từ histogram gộp
  - Nhìn p50 (trải nghiệm điển hình), p95/p99 (đuôi), p99.9 và max (cho hệ thống nhạy cảm)
- [ ] **Tail latency và fan-out** 🟡
  - Một request người dùng gọi N backend song song phải chờ **cái chậm nhất**. Xác suất ít nhất một backend rơi vào 1% chậm nhất = 1 − 0,99^N. N = 100 → khoảng 63%
  - Nghĩa là p99 của backend trở thành gần như p50 của trải nghiệm người dùng khi fan-out lớn
  - Giảm tail: hedged request (gửi request dự phòng sau một ngưỡng, lấy kết quả về trước), timeout chặt, giảm fan-out, cô lập việc nặng khỏi đường phục vụ (GC, compaction, backup)
- [ ] **Little's law** 🟡: `L = λ × W` — số request đang xử lý đồng thời = throughput × latency
  - Ví dụ: 1.000 RPS, latency 200 ms → 200 request đồng thời → cần ít nhất ~200 worker/connection (PHP-FPM process, thread, DB connection nếu mỗi request giữ một connection suốt)
  - Hệ quả: latency của dependency tăng từ 200 ms lên 2 giây ở cùng RPS → cần 2.000 slot → pool cạn → hệ thống sập dù CPU rảnh
- [ ] **Amdahl's law** 🟡: `Speedup = 1 / ((1 − p) + p / N)`, p là phần song song hoá được, N là số bộ xử lý
  - p = 90% thì dù N vô hạn, tăng tốc tối đa 10 lần. Phần tuần tự quyết định trần
  - Hệ quả thực tế: tối ưu phần tuần tự (một lock chung, một bước ghi DB chung) quan trọng hơn thêm máy
- [ ] **Universal Scalability Law (USL)** 🔴: `C(N) = N / (1 + α(N − 1) + βN(N − 1))`
  - α: contention (chờ tài nguyên chung, giống Amdahl). β: coherency (chi phí đồng bộ giữa các node, tăng theo N²)
  - Khi β > 0, throughput có **đỉnh** rồi **giảm** khi thêm node. Giải thích vì sao thêm máy có lúc làm chậm hơn (lock phân tán, cache invalidation, gossip)
  - Dùng: đo throughput ở vài mức N, fit α, β để dự đoán điểm tối ưu
- [ ] **Utilization và queueing** 🟡
  - Khi utilization tiến gần 100%, hàng đợi và latency tăng phi tuyến (theo mô hình hàng đợi cơ bản, thời gian chờ tỉ lệ với ρ/(1 − ρ))
  - Hệ quả: đừng chạy tài nguyên ở 90–100% thường xuyên; giữ headroom

### Quy trình tối ưu

- [ ] **Đo trước, sửa sau**
  1. Xác định mục tiêu bằng số (p99 < 300 ms ở 500 RPS) — tối ưu không có đích là vô tận
  2. Đo **baseline** trong điều kiện lặp lại được
  3. Tìm nút thắt: APM/trace cho biết thời gian nằm ở đâu (DB, API ngoài, CPU app)
  4. Sửa **một** thứ tại một thời điểm
  5. Đo lại cùng điều kiện; giữ thay đổi nếu cải thiện có ý nghĩa
  6. Theo dõi trên production (regression)
  - ⚠️ Tối ưu theo cảm giác: dành một tuần tối ưu vòng lặp PHP trong khi 90% thời gian nằm ở một query thiếu index
- [ ] **Profiling** 🟡
  - CPU profile: hàm nào tốn CPU (sampling profiler: chụp stack định kỳ, overhead thấp, dùng được trên production)
  - Memory profile: ai cấp phát nhiều, ai giữ bộ nhớ (heap dump, allocation profile)
  - I/O / off-CPU: thời gian chờ đĩa, mạng, lock — CPU profile **không** thấy thời gian này; cần tracing hoặc off-CPU profile
  - Lock/mutex profile: goroutine/thread chờ lock bao lâu
- [ ] **Flame graph** 🟡
  - Trục y: độ sâu stack (hàm gọi ở dưới, hàm được gọi ở trên). Trục x: **không phải thời gian**; các frame sắp theo tên, **độ rộng** = tỉ lệ số mẫu chứa frame đó
  - Đọc: tìm frame **rộng**, đặc biệt "cao nguyên" phẳng ở đỉnh (hàm tự tiêu CPU chứ không phải gọi hàm khác)
  - Frame rộng ở dưới nhưng chia nhỏ ở trên → chi phí nằm ở các hàm con
  - ⚠️ Flame graph CPU không cho thấy thời gian chờ I/O; request chậm vì DB sẽ không hiện ra rõ
- [ ] **APM** 🟡: New Relic, Datadog, Elastic APM, hoặc OpenTelemetry + Tempo/Jaeger. Cho biết theo từng endpoint: throughput, latency percentile, lỗi, và breakdown (bao nhiêu ms ở DB, HTTP ngoài, cache)
- [ ] **Công cụ theo ngôn ngữ**

  | | PHP | Java | Go |
  |---|---|---|---|
  | CPU profile | Xdebug (dev), Blackfire, Tideways, SPX | JFR, async-profiler | `pprof` (`net/http/pprof`, `go test -cpuprofile`) |
  | Memory | Blackfire, `memory_get_peak_usage()` | Heap dump (`jcmd`), Eclipse MAT, JFR | `pprof` heap/allocs |
  | Lock | — (thường không liên quan, mỗi request một process) | JFR, thread dump (`jstack`) | `pprof` mutex, block profile |
  | Benchmark | PHPBench | JMH | `testing.B` |

  - **Đối chiếu:** PHP-FPM mỗi request một process, không chia sẻ bộ nhớ nên lock contention hiếm, nhưng số process giới hạn concurrency; Java/Go chia sẻ bộ nhớ giữa thread/goroutine nên có contention và GC toàn cục

### Nguyên nhân chậm thường gặp

Theo thứ tự hay gặp ở backend:
1. Query DB: N+1, thiếu index, lấy thừa dữ liệu
2. Gọi API bên ngoài tuần tự, không có timeout
3. Làm việc nặng trong request thay vì đẩy vào queue
4. Không cache dữ liệu đọc nhiều
5. Serialize/deserialize dữ liệu lớn
6. Lock contention

### Checklist tối ưu theo tầng

- [ ] **DB** 🟢 — chi tiết ở [03-database-sql.md](03-database-sql.md)
  - N+1: một query lấy danh sách + N query lấy quan hệ → eager loading (`with()` trong Eloquent, `JOIN FETCH`/`@EntityGraph` trong JPA), hoặc gom `WHERE id IN (...)`
  - Index: đọc `EXPLAIN`; composite index đúng thứ tự; covering index; ⚠️ hàm trên cột (`WHERE DATE(created_at) = ...`) làm mất index
  - Lấy thừa: `SELECT *`, lấy cả cột TEXT/JSON lớn không dùng
  - Phân trang: ⚠️ `OFFSET 100000` phải duyệt qua 100.000 dòng → keyset/cursor pagination (`WHERE id > ? ORDER BY id LIMIT 20`)
  - `COUNT(*)` trên bảng lớn mỗi request → cache hoặc số xấp xỉ
  - Transaction dài giữ lock; slow query log; batch insert/update thay vì từng dòng
- [ ] **Cache** 🟢 — chi tiết ở [11-cache.md](11-cache.md)
  - Cache dữ liệu đọc nhiều, ít đổi; đo hit rate
  - ⚠️ Cache stampede khi key nóng hết hạn; cache vô hạn không TTL; cache làm che nút thắt thật
- [ ] **Network** 🟡
  - Gọi song song các I/O **độc lập** với nhau (Go goroutine + `errgroup`, Java `CompletableFuture`/virtual thread, PHP `Http::pool()` của Laravel hoặc Guzzle async)
  - Timeout cho mọi lời gọi ra ngoài (connect timeout và read timeout)
  - Keep-alive, HTTP/2, tái sử dụng HTTP client (⚠️ tạo client mới mỗi request = TCP + TLS handshake mỗi lần)
  - Nén response (gzip, brotli), phân trang, chỉ trả về field cần thiết
  - Giảm round trip: batch API, gom nhiều lệnh Redis bằng pipeline
- [ ] **App code** 🟡
  - Thuật toán: O(n²) ẩn trong vòng lặp lồng (`in_array` trong vòng lặp → dùng map/set)
  - Việc nặng (gửi email, resize ảnh, gọi API chậm, xuất báo cáo) → queue + worker
  - Tính lại cùng một thứ nhiều lần trong một request → memoize
  - Logging quá nhiều, log đồng bộ ra đĩa chậm
  - Regex phức tạp (⚠️ catastrophic backtracking với input xấu)
- [ ] **Serialization** 🟡
  - JSON encode/decode object lớn tốn CPU và bộ nhớ. Giảm payload, stream thay vì dựng cả mảng trong bộ nhớ
  - Protobuf/MessagePack nhỏ và nhanh hơn JSON cho giao tiếp nội bộ
  - ORM hydrate hàng nghìn entity rất tốn; với báo cáo dùng query thô trả mảng
- [ ] **GC** 🔴
  - Triệu chứng: p99 có đỉnh định kỳ, CPU cao dù traffic không đổi
  - Giảm cấp phát: tái sử dụng buffer (`sync.Pool` trong Go), tránh tạo object tạm trong vòng lặp nóng
  - Java: chọn GC phù hợp (G1 mặc định; ZGC/Shenandoah cho pause thấp), đặt heap hợp lý; theo dõi GC log. Go: `GOGC`, `GOMEMLIMIT`. PHP: GC vòng tham chiếu, ít quan trọng vì process tái tạo theo request
  - Chi tiết ở [06-java-spring.md](06-java-spring.md), [07-go.md](07-go.md)
- [ ] **Lock contention** 🔴
  - Triệu chứng: thêm CPU/thread không tăng throughput; CPU thấp nhưng latency cao; thread dump nhiều thread `BLOCKED`
  - Nguồn: mutex toàn cục trong app, synchronized quanh I/O, **hàng DB nóng** (mọi request cập nhật một dòng counter/balance), lock trong connection pool
  - Giảm: thu nhỏ critical section, không giữ lock khi gọi I/O, sharded counter, lock-free/atomic, gom ghi (batch) — xem [13-concurrency.md](13-concurrency.md)
- [ ] **Connection pool** 🟡
  - Pool cho DB và HTTP client: tránh chi phí mở kết nối mỗi request
  - Kích thước: không phải càng lớn càng tốt. DB có giới hạn kết nối và hiệu quả giảm khi quá nhiều kết nối đồng thời tranh CPU/lock. Tính: `số instance × pool size ≤ max_connections của DB` (trừ phần dự phòng)
  - ⚠️ Autoscale app từ 10 lên 50 instance × pool 20 = 1.000 kết nối → DB từ chối. Dùng connection pooler (PgBouncer, ProxySQL, RDS Proxy)
  - ⚠️ Pool cạn: request chờ lấy connection → latency tăng mà query không chậm. Metric cần theo dõi: số connection đang dùng, thời gian chờ lấy connection
  - PHP-FPM không có pool bền giữa request theo mặc định; mỗi process giữ kết nối riêng (persistent connection) → số process × số server là số kết nối

### Scale

- [ ] **Vertical vs horizontal** 🟢
  - Vertical: máy to hơn. Không đổi code, nhanh; có trần, đắt dần, vẫn là SPOF
  - Horizontal: thêm máy. Cần app **stateless** (session ra Redis, file ra S3, không cache local cần nhất quán); cần load balancer
  - Thường: scale dọc DB trước (dễ), scale ngang app (dễ vì stateless)
- [ ] **Các kỹ thuật** 🟡 (theo thứ tự thường áp dụng)

  | Kỹ thuật | Giải quyết | Cái giá |
  |---|---|---|
  | Tối ưu query/index | Đa số vấn đề DB | Thời gian phân tích |
  | Cache | Đọc lặp lại | Stale, invalidation |
  | CDN | File tĩnh, người dùng xa | Invalidation, chi phí |
  | Async (queue) | Việc chậm trong request, đỉnh tải | Eventual consistency, vận hành queue |
  | Read replica | Đọc nhiều | Replication lag |
  | Sharding | Ghi hoặc dữ liệu vượt một node | Query xuyên shard, rebalance, phức tạp lớn |
  | Precompute / materialized view | Query tổng hợp nặng lặp lại | Dữ liệu trễ, công đồng bộ |

- [ ] **Precompute** 🔴
  - Tính trước lúc ghi hoặc theo lịch, thay vì lúc đọc: bảng tổng hợp theo ngày, counter được cập nhật khi có sự kiện, feed đã fan-out
  - Materialized view (PostgreSQL có `REFRESH MATERIALIZED VIEW`, có `CONCURRENTLY` nếu có unique index; MySQL không có sẵn, dùng bảng tổng hợp tự cập nhật)
  - Đánh đổi: dữ liệu trễ, tốn storage, logic cập nhật phải đúng

### Load testing

- [ ] **Các loại** 🟡

  | Loại | Mục đích | Hình dạng tải |
  |---|---|---|
  | Load test | Hệ thống có đạt mục tiêu ở tải dự kiến không | Tăng dần tới mức dự kiến, giữ |
  | Stress test | Tìm điểm gãy, xem hệ thống hỏng thế nào (có graceful không) | Tăng dần tới khi lỗi |
  | Soak (endurance) test | Lỗi chỉ lộ ra theo thời gian: memory leak, pool rò, đĩa đầy | Tải vừa, kéo dài nhiều giờ |
  | Spike test | Đỉnh đột ngột (flash sale, push notification) | Nhảy vọt trong vài giây |

- [ ] **Công cụ** 🟡: k6 (script JavaScript, dễ đưa vào CI), JMeter (GUI, nhiều plugin, nặng), Gatling (Scala/Java/Kotlin DSL, report tốt), wrk/wrk2 (dòng lệnh, benchmark HTTP đơn giản, rất nhẹ), Locust (Python)
- [ ] **Thiết kế bài test** 🟡
  - Môi trường giống production (cỡ máy, dữ liệu DB cỡ thật — ⚠️ DB 1.000 dòng thì mọi query đều nhanh)
  - Kịch bản giống hành vi thật: tỉ lệ endpoint, think time, dữ liệu đa dạng (⚠️ mọi request cùng một id → cache hit 100%, kết quả ảo)
  - Warm-up trước khi đo (JIT của Java, cache)
  - Máy sinh tải không được là nút thắt (theo dõi CPU của máy chạy k6)
  - ⚠️ Không load test vào hệ thống dùng chung hoặc dịch vụ bên thứ ba thật (cổng thanh toán, SMS); dùng mock/sandbox
  - Định nghĩa pass/fail trước (threshold): p99 < 300 ms, lỗi < 0,1%
- [ ] **Đọc kết quả** 🟡
  - Nhìn đồng thời: RPS đạt được, latency percentile, tỉ lệ lỗi, và tài nguyên phía server (CPU, memory, DB connection, queue depth)
  - Điểm gãy (knee): RPS ngừng tăng trong khi latency tăng vọt → đã chạm nút thắt. Tìm tài nguyên nào bão hoà ở điểm đó
  - Lỗi tăng khi tải tăng: timeout, pool cạn, 502/503 từ LB
- [ ] **Open vs closed model** 🔴
  - Closed model: số virtual user cố định, mỗi user gửi request tiếp theo sau khi nhận response. Hệ thống chậm → tải tự giảm
  - Open model: request đến với tốc độ cố định bất kể hệ thống nhanh hay chậm — giống traffic Internet thật
  - k6: executor `constant-arrival-rate`/`ramping-arrival-rate` là open model; `constant-vus` là closed
- [ ] **Coordinated omission** 🔴
  - Trong closed model, khi server khựng 2 giây, công cụ **không gửi** các request lẽ ra phải gửi trong 2 giây đó, nên chỉ ghi nhận vài request chậm. Kết quả: percentile đẹp hơn thực tế rất nhiều
  - Người dùng thật vẫn tới trong 2 giây đó và đều bị chậm
  - Cách tránh: dùng open model (arrival rate cố định), công cụ đo từ thời điểm request **lẽ ra** được gửi (wrk2, HdrHistogram có hiệu chỉnh)

### Capacity planning và autoscaling

- [ ] **Capacity planning** 🔴
  - Từ load test: một instance chịu X RPS ở p99 mục tiêu. Tải dự kiến Y RPS → cần Y/X instance + headroom (thường nhắm giữ utilization quanh 50–70% để chịu đỉnh và mất một AZ)
  - Tính cả N+1 hoặc mất một AZ: 3 AZ, mất một thì 2 AZ còn lại phải chịu 100%
  - Dự báo tăng trưởng theo xu hướng + sự kiện đã biết (khuyến mãi, mùa cao điểm)
  - Nhìn nút thắt chung: DB, cache, queue, quota API bên thứ ba, giới hạn của cloud provider
- [ ] **Autoscaling** 🟡
  - Scale theo CPU, RPS, queue depth/consumer lag (cho worker), hoặc lịch (biết trước giờ cao điểm)
  - ⚠️ **Scale chậm hơn spike**: phát hiện metric (vài chục giây) + khởi động máy/pod + warm-up app có thể mất vài phút. Spike tính bằng giây đã làm sập trước khi instance mới lên. Cách chữa: scale trước theo lịch, giữ headroom, rate limit/load shedding
  - ⚠️ **DB không scale theo**: thêm 50 instance app → gấp 5 lần kết nối và query vào cùng một DB. Autoscale app có thể chính là thứ đánh sập DB
  - ⚠️ Scale theo CPU khi nút thắt là I/O: CPU thấp nên không scale dù latency tăng
  - ⚠️ Flapping: scale lên xuống liên tục → cần cooldown, ngưỡng lên và xuống khác nhau
  - Giới hạn tối đa (max replicas) để một bug không làm hoá đơn cloud bùng nổ
  - Scale xuống phải graceful: drain connection, hoàn thành job đang làm
- [ ] **Load shedding** 🔴: khi quá tải, chủ động từ chối sớm (503/429) một phần request, ưu tiên request quan trọng, thay vì để mọi request cùng chậm rồi cùng timeout

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| API chậm, bạn làm gì? | "Thêm cache" | Đặt mục tiêu bằng số, đo baseline, dùng trace để biết thời gian nằm ở đâu, sửa nút thắt lớn nhất, đo lại. Cache chỉ khi dữ liệu hợp để cache |
| p99 cao nhưng trung bình thấp | "Server yếu, nâng cấp" | Phân tích theo endpoint/tham số (khách hàng dữ liệu lớn?), GC pause, pool chờ, lock, dependency chậm, cold cache; nói fan-out làm tail tệ hơn |
| Load test cho kết quả tốt | "p99 50 ms, ổn" | Hỏi: dữ liệu cỡ thật chưa, open hay closed model, có coordinated omission không, máy sinh tải có bão hoà không, kịch bản có đa dạng không |
| Autoscaling giải quyết traffic tăng? | "Bật HPA là xong" | Nói thời gian phản ứng vs spike, DB và dependency không scale theo, connection pool nhân lên, scale theo metric sai, cần headroom và load shedding |
| Thêm server có nhanh hơn không? | "Có, tuyến tính" | Amdahl/USL: phần tuần tự và chi phí đồng bộ giới hạn; có lúc thêm node làm chậm hơn; tìm nút thắt chung trước |

## Tình huống

1. **Xuất báo cáo 1 triệu dòng mà không làm treo server.**
   - Gợi ý: không làm trong request HTTP; đẩy vào queue, worker xử lý, xong thì thông báo/gửi link tải (object storage + pre-signed URL)
   - Đọc DB theo lô bằng cursor/keyset (không `OFFSET`), hoặc stream (`cursor()`/`lazy()` trong Laravel, `Stream` trong JPA với fetch size, `rows.Next()` trong Go)
   - Ghi file dạng stream (CSV), không dựng cả mảng trong bộ nhớ; đọc từ read replica để không ảnh hưởng primary
   - Giới hạn số job export đồng thời; theo dõi tiến độ; job idempotent để retry được

2. **API p99 là 3 giây nhưng trung bình chỉ 200 ms.**
   - Gợi ý: xem trace của các request chậm, tìm điểm chung (endpoint, tenant lớn, tham số, instance cụ thể, thời điểm)
   - Nghi phạm: query chậm với dữ liệu lớn, API ngoài chậm/timeout dài, GC pause, chờ connection pool, lock DB, cold start/cache miss
   - Đối chiếu metric theo thời gian: đỉnh định kỳ (cron, backup, GC) hay ngẫu nhiên

3. **Memory của service tăng dần sau mỗi lần deploy, tới khi bị OOM kill.**
   - Gợi ý: phân biệt leak thật và cache/heap tăng tới ngưỡng rồi ổn định
   - Lấy heap dump/heap profile ở hai thời điểm và so sánh (Java: `jcmd` + MAT; Go: `pprof` heap; PHP: worker dài hạn như Octane/queue worker hay giữ static/global)
   - Nghi phạm: cache in-memory không giới hạn, listener đăng ký không gỡ, goroutine leak (kiểm tra số goroutine), connection không đóng
   - Giảm thiệt hại tạm thời: restart định kỳ worker (`--max-jobs`/`--max-time` của Laravel queue) — nhưng vẫn phải tìm root cause

4. **CPU 100% trên toàn bộ instance, traffic không tăng.**
   - Gợi ý: có deploy gần đây không → rollback trước
   - Lấy CPU profile/flame graph trên một instance; thread dump (Java) nhiều lần để xem thread nào luôn chạy
   - Nghi phạm: vòng lặp vô hạn, regex backtracking với input mới, GC liên tục do gần hết heap, retry storm (client retry dồn dập), cache hết hạn đồng loạt khiến tính lại

5. **Sau khi bật autoscaling, giờ cao điểm DB báo "too many connections".**
   - Gợi ý: Little's law và phép nhân `instance × pool size`; đặt max replicas; giảm pool mỗi instance; thêm PgBouncer/ProxySQL/RDS Proxy
   - Xem lại vì sao cần nhiều instance: có phải request chậm vì DB chậm, và scale app chỉ làm DB tệ hơn

6. **Load test đạt 5.000 RPS với p99 80 ms, lên production 1.000 RPS đã chậm.**
   - Gợi ý: so dữ liệu (cỡ DB, độ đa dạng), kịch bản (tỉ lệ endpoint, ghi vs đọc), cache hit ảo, dependency được mock trong test
   - Kiểm tra coordinated omission và closed model

## ❓ Câu hỏi hay gặp

🟢
- Latency và throughput khác nhau thế nào?
- Vì sao dùng p99 thay vì trung bình?
- N+1 query là gì, sửa thế nào?
- Làm thế nào để xuất file báo cáo 1 triệu dòng mà không làm treo server?

🟡
- API của bạn p99 là 3 giây nhưng trung bình chỉ 200 ms. Bạn điều tra thế nào?
- Little's law là gì? Dùng nó để tính số connection thế nào?
- Flame graph đọc thế nào?
- Load test, stress test, soak test, spike test khác nhau thế nào?
- Chọn kích thước connection pool thế nào?
- Scale dọc và scale ngang, khi nào dùng cái nào?

🔴
- Vì sao tail latency quan trọng hơn khi fan-out?
- Amdahl's law và USL nói gì? Vì sao thêm máy có thể làm chậm hơn?
- Coordinated omission là gì?
- Autoscaling có những cạm bẫy gì?
- Bạn làm capacity planning cho một đợt khuyến mãi thế nào?

## Bài tập tự làm

1. Viết một endpoint có N+1 query (ngôn ngữ bạn dùng), đo số query và thời gian với 1.000 bản ghi, rồi sửa và đo lại.
2. Viết script k6 cho một API với executor open model (`constant-arrival-rate`), threshold p99 và tỉ lệ lỗi. Giải thích vì sao chọn open model.
3. Dùng Little's law: một service nhận 800 RPS, mỗi request gọi DB 3 lần, mỗi lần 20 ms và giữ connection trong suốt request 150 ms. Tính số DB connection tối thiểu, và tính lại khi DB chậm gấp 5.
4. Lấy CPU profile của một chương trình Go hoặc Java nhỏ có một hàm nóng, vẽ flame graph và chỉ ra hàm tốn nhất.
5. Viết kế hoạch capacity cho một đợt flash sale: dự kiến tải, số instance, headroom, các nút thắt chung và kế hoạch dự phòng.

> Nộp bài vào đây để được review.
