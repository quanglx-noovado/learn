# 17. Performance và scalability

> [← Mục lục](README.md) · Trọng tâm: **đo trước, sửa sau**: latency/percentile, các định luật, profiling (PHP, Go, Java), nguyên nhân chậm theo tầng, load testing, capacity planning và autoscaling cho stack **PHP-FPM / Laravel + MySQL**.
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
| [*Systems Performance*, 2nd ed.](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) (Brendan Gregg, 2020) | Sách | Phương pháp luận (USE, workload characterization), công cụ quan sát, profiling |
| [Brendan Gregg: Performance Methodologies](https://www.brendangregg.com/methodology.html) | Blog | Tóm tắt các phương pháp và anti-pattern ("streetlight", "random change") |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.1: latency, percentile, tail latency amplification, cách mô tả tải |
| [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/) (Dean, Barroso, 2013) | Paper | Tail latency khi fan-out, hedged request. Ngắn, đọc hết |
| [Google SRE Book](https://sre.google/sre-book/handling-overload/) | Sách online miễn phí | Chương *Handling Overload* và *Addressing Cascading Failures* |
| [Grafana k6 docs](https://grafana.com/docs/k6/latest/) | Official docs | Load testing, executor, threshold, open/closed model |
| [PHP-FPM](https://www.php.net/manual/en/install.fpm.configuration.php) và [OPcache](https://www.php.net/manual/en/opcache.configuration.php) configuration | Official docs | Tuning tầng PHP |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Nói đúng ngôn ngữ đo lường, có quy trình tối ưu, sửa được các lỗi chậm phổ biến | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.6 | Dùng định luật để tính, profile được PHP và một ngôn ngữ khác, tune PHP-FPM, chạy load test đúng | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.5 | Tail latency, giới hạn của scale, load test không tự lừa mình, capacity và autoscaling | 7–9 ngày |

Học theo thứ tự: chặng 2 dùng từ vựng percentile và quy trình của chặng 1; chặng 3 giải thích
vì sao các kết quả đo ở chặng 2 có thể sai hoặc không scale. Câu hỏi performance ở vòng senior
gần như luôn là tình huống ("p99 3 giây", "autoscale làm sập DB"); người phỏng vấn chấm quy
trình và con số, không chấm danh sách mẹo.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Latency, throughput, percentile

**Vì sao cần học:** Mọi cuộc nói chuyện về hiệu năng, từ SLO tới báo cáo load test, đều dùng các
từ latency, throughput, p99. Dùng sai (nói "trung bình 60 ms" khi người dùng đang chờ 5 giây, hay
lấy trung bình p99 của nhiều server) là red flag ngay trong phỏng vấn. Câu mở đầu hay gặp: "p99
nghĩa là gì, vì sao không dùng trung bình".

**Học gì**

*Ba khái niệm đo*
- *Latency*: thời gian để xử lý **một** request, từ lúc gửi tới lúc nhận xong response.
- *Throughput*: số request hệ thống xử lý được mỗi giây, viết là RPS (requests per second) hoặc
  QPS (queries per second).
- *Bandwidth*: dung lượng tối đa của đường truyền, ví dụ 1 Gbps. Là trần, không phải lượng đang
  dùng.
- Latency và throughput không tỉ lệ nghịch đơn giản:
  - *Batching* (gom nhiều việc làm một lần) tăng throughput nhưng làm từng việc phải chờ lâu hơn,
    tức tăng latency.
  - Song song hoá tăng throughput, nhưng không làm nhanh hơn một việc buộc phải chạy tuần tự.
- ⚠️ Luôn nói latency **tại mức tải nào**. "p99 = 100 ms" không có nghĩa gì nếu không kèm RPS, vì
  ở 10 RPS và ở 1.000 RPS cùng một hệ thống cho hai con số khác hẳn.

*Percentile*
- *Percentile*: xếp mọi request theo latency từ nhanh tới chậm. p99 là giá trị mà 99% request
  nhanh hơn nó. p50 (còn gọi *median*) là request ở giữa.
- Vì sao không dùng trung bình: trung bình che mất *đuôi* (nhóm request chậm nhất).
  - Ví dụ: 99 request 10 ms và 1 request 5 giây có trung bình khoảng 60 ms. Con số 60 ms không
    mô tả ai cả: 99 người thấy 10 ms, 1 người thấy 5 giây.
- Nên nhìn:
  - p50: trải nghiệm điển hình.
  - p95, p99: phần đuôi.
  - p99.9 và max: cho hệ nhạy cảm, ví dụ thanh toán.
- ⚠️ Không lấy trung bình của các percentile. Trung bình p99 của 10 server **không phải** p99 của
  cả hệ thống.
  - Cách đúng: mỗi server ghi *histogram* (đếm số request rơi vào từng khoảng latency), gộp các
    histogram lại rồi mới tính percentile.

*Latency gồm cả thời gian chờ*
- Latency người dùng thấy gồm cả thời gian **chờ trong hàng đợi**, không chỉ thời gian xử lý.
- Ví dụ: request chỉ cần 50 ms để chạy, nhưng phải đợi 2 giây trong `listen.backlog` của PHP-FPM
  vì hết worker, hoặc đợi lấy connection từ pool. Người dùng thấy 2,05 giây.
- ⚠️ Log trong app thường chỉ đo phần xử lý, nên trông vẫn đẹp trong khi người dùng đang chờ lâu.

**Đọc**
- DDIA ch.1: mục *Describing Performance*
- Brendan Gregg: [Latency heat maps](https://www.brendangregg.com/HeatMaps/latency.html) (vì sao phân phối quan trọng hơn một con số)

**Nắm chắc khi**
- [ ] Giải thích được vì sao trung bình p99 của nhiều server là con số sai và cách tính đúng
- [ ] Viết được SLO dạng "p99 < 300 ms ở 500 RPS" cho một endpoint mình đang làm, kèm lý do chọn con số

#### 1.2 Quy trình tối ưu: đo trước, sửa sau

**Vì sao cần học:** Sai lầm tốn thời gian nhất khi tối ưu là sửa chỗ mình đoán là chậm thay vì chỗ
thật sự chậm. Người phỏng vấn senior thường hỏi "kể một lần bạn tối ưu hiệu năng" và chấm quy
trình: có mục tiêu không, có đo trước sau không, có biết thời gian nằm ở đâu không.

**Học gì**

*Quy trình 6 bước*
1. Đặt mục tiêu bằng số, ví dụ "p99 < 300 ms ở 500 RPS". Tối ưu không có đích là vô tận.
2. Đo *baseline* (số liệu hiện tại) trong điều kiện lặp lại được: cùng dữ liệu, cùng tải.
3. Tìm *nút thắt* (bottleneck, chỗ giới hạn toàn bộ tốc độ). Công cụ APM hoặc trace cho biết thời
   gian nằm ở đâu: DB, API ngoài, CPU của app, hay chờ hàng đợi.
4. Sửa **một** thứ mỗi lần. Sửa ba thứ cùng lúc thì không biết cái nào có tác dụng.
5. Đo lại trong cùng điều kiện. Giữ thay đổi nếu cải thiện có ý nghĩa.
6. Theo dõi *regression* (hiệu năng xấu đi trở lại) trên production.

*Anti-pattern*
- ⚠️ Tối ưu theo cảm giác: một tuần tối ưu vòng lặp PHP trong khi 90% thời gian nằm ở một query
  thiếu index.
- ⚠️ *Streetlight*: chỉ nhìn chỗ có sẵn công cụ, như người tìm chìa khoá dưới cột đèn vì chỗ đó
  sáng, dù chìa rơi ở chỗ khác.
- ⚠️ *Random change*: đổi cấu hình lung tung cho tới khi thấy nhanh hơn, không hiểu vì sao.

*Công cụ để thấy thời gian nằm ở đâu*
- *APM* (Application Performance Monitoring): công cụ gắn vào app, tự đo từng request. Cho biết theo
  từng endpoint: throughput, percentile, tỉ lệ lỗi, và thời gian chia ra DB, HTTP, cache.
  - Ví dụ: New Relic, Datadog, Elastic APM, Tideways, OpenTelemetry + Tempo/Jaeger.
- *Trace*: bản ghi một request đi qua hệ thống, gồm nhiều *span*. Mỗi span là một đoạn việc có giờ
  bắt đầu và kết thúc, ví dụ một query hay một lời gọi HTTP. Nhìn trace là thấy span nào dài nhất.
- Công cụ của Laravel:
  - Dev: Telescope, Debugbar.
  - Production: Pulse (dashboard tự host), Nightwatch (dịch vụ giám sát chính thức).

**Đọc**
- Brendan Gregg: [Performance Methodologies](https://www.brendangregg.com/methodology.html) (đọc phần anti-methodologies trước)
- [OpenTelemetry docs](https://opentelemetry.io/docs/): mục *Concepts* (trace, span, metric)
- Laravel: [Pulse](https://laravel.com/docs/pulse), [Telescope](https://laravel.com/docs/telescope)
- Observability chi tiết: [18-reliability-observability.md](18-reliability-observability.md)

**Nắm chắc khi**
- [ ] Kể được một lần tối ưu thật theo đủ 6 bước, có số trước và sau
- [ ] Mở một trace của request chậm và chỉ ra span nào chiếm nhiều thời gian nhất

#### 1.3 Nguyên nhân chậm thường gặp: DB và cache

**Vì sao cần học:** Phần lớn "app chậm" ở backend là do vài nguyên nhân lặp đi lặp lại, và đa số
nằm ở DB. Biết thứ tự hay gặp giúp bạn tìm đúng chỗ nhanh, và nhận ra ngay các mẫu như N+1 khi
nhìn trace. Phỏng vấn hay hỏi "endpoint chậm, bạn nghi gì đầu tiên".

**Học gì**

*Thứ tự nguyên nhân hay gặp ở backend*
1. Query DB: N+1, thiếu index, lấy thừa dữ liệu.
2. Gọi API ngoài tuần tự, không đặt timeout.
3. Làm việc nặng ngay trong request thay vì đẩy vào queue.
4. Không cache dữ liệu đọc nhiều.
5. Serialize, deserialize dữ liệu lớn (module 2.4).
6. Lock contention: nhiều request tranh nhau một khoá (module 3.2).

*DB*
- Chi tiết ở [03-database-sql.md](03-database-sql.md). Phần này chỉ điểm qua các lỗi hay gặp nhất.
- *N+1*: lấy danh sách bằng 1 query, rồi với mỗi dòng lại chạy thêm 1 query để lấy dữ liệu liên
  quan. 100 đơn hàng là 101 query.

```php
// N+1: 1 query lấy orders, rồi mỗi vòng lặp thêm 1 query lấy customer
foreach (Order::all() as $order) {
    echo $order->customer->name;
}
// Sửa: eager loading, tổng cộng 2 query
foreach (Order::with('customer')->get() as $order) {
    echo $order->customer->name;
}
```

- Sửa N+1 bằng *eager loading* (nạp trước dữ liệu liên quan): Laravel `with()`, JPA `JOIN FETCH`
  hoặc `@EntityGraph`. Hoặc tự gom thành `WHERE id IN (...)`.
- Index: đọc `EXPLAIN`, đặt *composite index* (index nhiều cột) đúng thứ tự, dùng *covering index*
  (index chứa đủ cột query cần).
  - ⚠️ `WHERE DATE(created_at) = ...` làm mất index, vì DB phải tính hàm trên mọi dòng. Viết thành
    khoảng `created_at >= ... AND created_at < ...`.
- Lấy thừa: `SELECT *`, kéo về cột TEXT/JSON lớn mà không dùng.
- ⚠️ `OFFSET 100000` bắt DB duyệt qua 100.000 dòng rồi bỏ đi. Dùng *keyset pagination*: nhớ id cuối
  của trang trước và query `WHERE id > ?`.
- `COUNT(*)` trên bảng lớn ở mỗi request: cache lại, hoặc dùng số xấp xỉ.
- Transaction dài giữ lock lâu, làm request khác phải chờ.
- Insert hay update từng dòng một: gom thành batch.

*Cache*
- Chi tiết ở [11-cache.md](11-cache.md).
- Cache dữ liệu đọc nhiều, ít đổi. Đo *hit rate* (tỉ lệ lần đọc tìm thấy trong cache).
- ⚠️ *Cache stampede*: một key nóng hết hạn, hàng trăm request cùng lúc thấy cache trống và cùng
  chạy query nặng vào DB.
- ⚠️ Cache không có TTL (thời gian sống) thì dữ liệu cũ mãi và bộ nhớ đầy dần.
- ⚠️ Cache che mất nút thắt thật: khi cache lạnh (sau restart, deploy) hệ thống sập lại.

**Đọc**
- Laravel: [Eager Loading](https://laravel.com/docs/eloquent-relationships#eager-loading), [Preventing Lazy Loading](https://laravel.com/docs/eloquent-relationships#preventing-lazy-loading)
- Use The Index, Luke: [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)

**Nắm chắc khi**
- [ ] Viết một endpoint N+1, đo số query và thời gian với 1.000 bản ghi, sửa và đo lại (bài tập 1)
- [ ] Nhìn một trace có 200 query giống nhau, nói được ngay đó là gì và sửa ở đâu

#### 1.4 Scale cơ bản

**Vì sao cần học:** "Thêm server" là câu trả lời đầu tiên ai cũng nghĩ tới, nhưng app Laravel chỉ
chạy được trên nhiều server khi không giữ state trên máy. Module này giúp bạn biết khi nào nên mua
máy to hơn, khi nào thêm máy, và những chỗ nào trong app sẽ vỡ khi thêm máy.

**Học gì**

*Hai cách scale*

| | Vertical (máy to hơn) | Horizontal (thêm máy) |
|---|---|---|
| Sửa code | Không | Cần app stateless |
| Tốc độ triển khai | Nhanh | Cần load balancer, deploy nhiều máy |
| Giới hạn | Có trần, càng to càng đắt | Gần như không trần cho app |
| Điểm yếu | Vẫn là SPOF | Phức tạp vận hành hơn |

- *SPOF* (single point of failure): một chỗ hỏng là cả hệ thống ngừng.
- *Stateless*: app không giữ dữ liệu nào trên máy mà request sau cần tới. Request nào tới máy nào
  cũng được. Muốn vậy:
  - Session ra Redis hoặc DB.
  - File upload ra S3 hoặc storage dùng chung.
  - Không dùng cache local cho dữ liệu cần nhất quán giữa các máy.
- Thêm một *load balancer* đứng trước để chia request cho các máy.
- Cách thường làm: scale dọc DB trước (dễ, không đổi code), scale ngang app (dễ vì app stateless).

*PHP-FPM khi thêm server*
- PHP-FPM gần như stateless sẵn nhờ share-nothing. ⚠️ Các chỗ hay vỡ khi thêm server:
  - Session driver `file`: user đăng nhập ở máy A, request sau vào máy B thì bị đăng xuất.
  - Upload vào disk local: file chỉ có trên một máy.
  - Cache driver `file`: mỗi máy một cache riêng, xoá cache ở máy này không xoá ở máy kia.
  - Cron chạy trên mọi máy: job chạy N lần.

**Đọc**
- Laravel: [Deployment](https://laravel.com/docs/deployment) (các bước optimize), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server)
- System design tổng thể: [16-system-design.md](16-system-design.md)

**Nắm chắc khi**
- [ ] Liệt kê được mọi chỗ trong một app Laravel thật cần sửa trước khi chạy trên 3 server
- [ ] Nói được khi nào scale dọc DB vẫn là lựa chọn đúng dù "không scale được mãi"

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Little's law, Amdahl, queueing

**Vì sao cần học:** Ba công thức này cho phép tính trước thay vì đoán: cần bao nhiêu worker, thêm
máy được lợi bao nhiêu, vì sao hệ thống ở 90% tải lại chậm hẳn. Phỏng vấn senior thường cho con số
("1.000 RPS, 200 ms, cần bao nhiêu connection?") và chờ bạn áp Little's law ngay.

**Học gì**

*Little's law*
- Công thức `L = λ × W`:
  - `L`: số request đang được xử lý đồng thời.
  - `λ` (lambda): throughput, số request mỗi giây.
  - `W`: latency trung bình, tính bằng giây.
- Ví dụ: 1.000 RPS × 200 ms (0,2 giây) = 200 request đồng thời. Cần ít nhất khoảng 200 *slot*
  (chỗ xử lý): PHP-FPM worker, thread, hoặc DB connection nếu mỗi request giữ connection suốt thời
  gian chạy.
- ⚠️ Dependency chậm đi là cần nhiều slot hơn:
  1. Một API ngoài chậm từ 200 ms lên 2 giây, RPS vẫn vậy.
  2. `L` tăng từ 200 lên 2.000 request đồng thời.
  3. Pool 200 slot cạn, request mới phải xếp hàng.
  4. Hệ thống sập dù CPU vẫn rảnh.
- Áp vào PHP-FPM: `pm.max_children` là trần của `L`. Đảo công thức: `λ tối đa = L / W`.
  - Ví dụ: tổng 200 worker, latency 500 ms thì throughput tối đa khoảng 400 RPS, bất kể CPU còn
    bao nhiêu.

*Amdahl's law*
- Công thức `Speedup = 1 / ((1 − p) + p / N)`:
  - `p`: tỉ lệ công việc song song hoá được.
  - `N`: số máy, số core, hay số worker.
- Ví dụ: p = 90%, thì dù N vô hạn cũng chỉ nhanh được 10 lần, vì 10% tuần tự còn lại vẫn phải chạy
  một mình.
- Hệ quả: tối ưu phần tuần tự (một lock chung, một bước ghi DB chung) quan trọng hơn thêm máy.

*Utilization và hàng đợi*
- *Utilization* (ρ, rho): tỉ lệ thời gian tài nguyên bận.
- Khi utilization tiến gần 100%, hàng đợi và latency tăng **phi tuyến**, không tăng đều.
  - Mô hình hàng đợi cơ bản: thời gian chờ tỉ lệ với `ρ / (1 − ρ)`.
  - ρ = 50% cho hệ số 1. ρ = 90% cho hệ số 9. ρ = 95% cho hệ số 19.
- Vì vậy luôn giữ *headroom* (khoảng dư), đừng để hệ thống chạy thường xuyên ở 90–100%.

**Đọc**
- Marc Brooker: [Little's Law](https://brooker.co.za/blog/2018/06/20/littles-law.html) (ngắn, có ví dụ hệ thống thật)
- Mor Harchol-Balter: [*Performance Modeling and Design of Computer Systems*](https://www.cs.cmu.edu/~harchol/PerformanceModeling/book.html), chương 6 (Little's law) và các chương M/M/1 nếu muốn đi sâu

**Nắm chắc khi**
- [ ] Tính được số DB connection tối thiểu cho bài tập 3, cả khi DB chậm gấp 5
- [ ] Từ `pm.max_children` và p50 latency, tính được throughput tối đa của một server PHP-FPM
- [ ] Vẽ được đồ thị latency theo utilization và giải thích vì sao chạy ở 95% nguy hiểm

#### 2.2 Profiling, flame graph, công cụ theo ngôn ngữ

**Vì sao cần học:** APM cho biết endpoint nào chậm, còn profiler cho biết **dòng code nào** chậm.
Biết đọc flame graph và biết profiler nào thấy được gì giúp bạn không mất công tối ưu nhầm chỗ. Câu
hay gặp: "request 2 giây mà profile chỉ thấy 50 ms, phần còn lại ở đâu".

**Học gì**

*Các loại profile*
- *CPU profile*: hàm nào tốn CPU nhất. Có hai cách lấy:

| | Sampling profiler | Instrumenting profiler |
|---|---|---|
| Cách làm | Chụp stack định kỳ (ví dụ 100 lần/giây), đếm hàm nào hay xuất hiện | Chèn đo vào mọi lời gọi hàm |
| Độ chính xác | Xấp xỉ, đủ để tìm hàm nóng | Chính xác số lần gọi |
| Overhead | Thấp, chạy được trên production | Cao, làm chậm nhiều |

- *Memory profile*: ai cấp phát nhiều, ai đang giữ bộ nhớ. Lấy bằng heap dump hoặc allocation
  profile.
- *Off-CPU / I/O*: thời gian chờ disk, mạng, lock.
  - ⚠️ CPU profile **không** thấy thời gian này, vì lúc chờ thì process không chạy trên CPU. Cần
    tracing hoặc off-CPU profile.
- *Lock/mutex profile*: thread hoặc goroutine chờ lock bao lâu.

*Đọc flame graph*
- *Flame graph*: hình gộp mọi stack đã chụp. Mỗi ô chữ nhật là một hàm, ô ở trên là hàm được gọi
  bởi ô ở dưới.
- Trục y là độ sâu stack.
- ⚠️ Trục x **không phải thời gian**. Các ô sắp theo tên hàm. **Độ rộng** của ô là tỉ lệ số mẫu có
  hàm đó, tức tỉ lệ CPU.
- Cách đọc:
  1. Tìm các ô rộng.
  2. Đặc biệt chú ý "cao nguyên": ô rộng nằm ở đỉnh, không có gì phía trên. Đó là hàm tự tiêu CPU.
  3. Ô rộng ở dưới nhưng phía trên chia thành nhiều ô nhỏ: chi phí nằm ở các hàm con.
- ⚠️ Flame graph CPU không cho thấy request chậm vì chờ DB.
- *Continuous profiling*: profile liên tục trên production với overhead thấp, so sánh được trước và
  sau deploy. Ví dụ Pyroscope, Datadog, Tideways.

*Công cụ theo ngôn ngữ*

| | PHP | Java | Go |
|---|---|---|---|
| CPU profile | SPX, Blackfire, Tideways, Xdebug (dev) | JFR, async-profiler | `pprof` (`net/http/pprof`, `go test -cpuprofile`) |
| Memory | Blackfire, SPX, `memory_get_peak_usage()` | heap dump (`jcmd`), Eclipse MAT, JFR | `pprof` heap/allocs |
| Lock | ít liên quan (mỗi request một process); lock nằm ở DB/Redis | JFR, thread dump (`jstack`) | `pprof` mutex, block |
| Benchmark | PHPBench | JMH | `testing.B` |

*Đối chiếu PHP với Java/Go*
- PHP-FPM không chia sẻ bộ nhớ giữa các request, nên lock contention trong app hiếm. Đổi lại, số
  process giới hạn concurrency.
- Java và Go chia sẻ bộ nhớ giữa các request, nên có contention và có GC chạy trên toàn bộ heap
  chung.

**Đọc**
- Brendan Gregg: [Flame Graphs](https://www.brendangregg.com/flamegraphs.html), [Off-CPU Analysis](https://www.brendangregg.com/offcpuanalysis.html)
- Go: [Diagnostics](https://go.dev/doc/diagnostics), [net/http/pprof](https://pkg.go.dev/net/http/pprof)
- Java: [async-profiler](https://github.com/async-profiler/async-profiler) README, [JMH](https://github.com/openjdk/jmh)
- [Grafana Pyroscope](https://github.com/grafana/pyroscope) (continuous profiling mã nguồn mở)

**Nắm chắc khi**
- [ ] Lấy được CPU profile của một chương trình Go hoặc Java nhỏ có hàm nóng, vẽ flame graph và chỉ ra hàm tốn nhất (bài tập 4)
- [ ] Nhìn một flame graph lạ, trong 1 phút nói được 2 chỗ đáng xem
- [ ] Giải thích được vì sao request 2 giây chỉ có 50 ms trên CPU profile, và dùng công cụ gì tìm 1,95 giây còn lại

#### 2.3 Tầng PHP: profiling, OPcache/JIT, tuning PHP-FPM

**Vì sao cần học:** Module riêng cho người làm PHP. Phần lớn "PHP chậm" là do cấu hình runtime
hoặc chờ I/O, không phải do ngôn ngữ. Biết profile một request Laravel, đọc trạng thái OPcache và
chọn cấu hình `pm` là những việc sẽ làm thật, và là câu hỏi gần như chắc chắn gặp khi phỏng vấn
vị trí PHP senior.

**Học gì**

*Profiling PHP*

| Công cụ | Loại | Dùng ở đâu | Ghi chú |
|---|---|---|---|
| Xdebug profiler (`xdebug.mode=profile`) | Instrumenting | Chỉ dev | Ghi file cachegrind, xem bằng KCachegrind/QCachegrind. ⚠️ Overhead rất lớn, làm sai lệch tỉ lệ thời gian |
| SPX | Mã nguồn mở, overhead thấp | Dev, staging | Có web UI (flat profile, timeline, flame graph), bật theo từng request |
| xhprof | Mã nguồn mở | Dev, staging | Extension gốc của Facebook, bản fork đang được duy trì trên PECL, cần công cụ riêng để xem kết quả |
| Blackfire | Thương mại | Cả production | Profile theo yêu cầu an toàn, so sánh hai profile, viết assertion hiệu năng trong CI |
| Tideways | Thương mại | Production | APM + profiler + trace cho PHP |

- ⚠️ Đừng để Xdebug bật trên production. Kiểm tra bằng `php -m` trong image.

*OPcache*
- Không có OPcache thì mỗi request PHP phải đọc và biên dịch lại mọi file PHP thành opcode (lệnh
  cho máy ảo của PHP).
- Các thông số chính:
  - `memory_consumption`: bộ nhớ chứa opcode, mặc định 128 MB.
  - `interned_strings_buffer`: bộ nhớ cho các chuỗi dùng chung (tên class, tên hàm...).
  - `max_accelerated_files`: số file tối đa được cache. Phải lớn hơn số file trong `vendor/`.
- Production đặt `validate_timestamps=0`: không `stat` file mỗi request để xem file có đổi không.
  Đổi lại phải reload FPM khi deploy.
- Theo dõi bằng `opcache_get_status()`: hit rate, bộ nhớ trống, `wasted_memory` (bộ nhớ của code
  cũ không còn dùng), số lần restart.
  - ⚠️ Hết bộ nhớ hoặc hết slot thì OPcache tự restart hoặc ngừng cache file mới. Hiệu năng rơi âm
    thầm, không có lỗi nào.
- *Preloading* (PHP 7.4+): nạp sẵn các class vào shared memory ngay khi FPM khởi động. Lợi ích nhỏ
  với app Laravel thông thường, phải đo mới biết.

*JIT (PHP 8.0+)*
- *JIT* (just-in-time compiler): biên dịch các đoạn opcode chạy nhiều ra mã máy.
- Có lợi cho việc CPU-bound: tính toán, xử lý ảnh, parser.
- Gần như không giúp request web, vì request web chủ yếu chờ DB và HTTP.
- Từ PHP 8.4, mặc định `opcache.jit=disable` và `opcache.jit_buffer_size=64M`. Bật bằng
  `opcache.jit=tracing`.
- ⚠️ Bật JIT mà không đo là nhận thêm rủi ro (bug của JIT, extension không tương thích) để đổi lấy
  lợi ích có thể bằng 0.

*Laravel và Composer*
- `php artisan optimize`: cache config, route, view, event, để không phải đọc lại ở mỗi request.
- `composer install --no-dev --optimize-autoloader`: bỏ package dev, tạo sẵn bản đồ class để
  autoload nhanh. Có thể thêm `--classmap-authoritative` (chỉ tìm class trong bản đồ, không dò file
  system).
- ⚠️ Sau `config:cache`, gọi `env()` ở ngoài file config sẽ trả về `null`. Chỉ đọc `env()` trong
  `config/*.php`, còn code thì dùng `config()`.

*Tuning PHP-FPM*

| `pm` | Cách chạy | Hợp với | Cái giá |
|---|---|---|---|
| `static` | Luôn giữ đúng `max_children` worker | Server chỉ chạy FPM, tải ổn định | Giữ RAM kể cả lúc rảnh |
| `dynamic` | Giữ số worker rảnh trong khoảng `min_spare_servers` tới `max_spare_servers`, khởi động với `start_servers` | Tải dao động | Tốn thời gian fork khi tải tăng. `pm.max_spawn_rate` giới hạn tốc độ fork |
| `ondemand` | Chỉ fork khi có request, tắt worker rảnh sau `process_idle_timeout` | Nhiều pool ít tải, tiết kiệm RAM | Request đầu tiên chịu độ trễ fork |

- Tính `max_children` theo hai cách rồi lấy số nhỏ hơn:
  - Theo RAM: RAM dành cho FPM chia cho PSS mỗi worker ([01-os-linux.md](01-os-linux.md), module 2.6).
  - Theo Little's law (module 2.1): số request đồng thời cần có.
  - ⚠️ Khi tính tổng kết nối DB, nhớ nhân với số server.
- `pm.max_requests`: thay worker sau N request để chặn leak.
- `pm.status_path`: `listen queue` > 0 kéo dài, hoặc `max children reached` tăng, là thiếu worker
  hoặc worker bị chiếm bởi request chậm.
- `slowlog` + `request_slowlog_timeout`: in stack trace của request chạy quá N giây.
- Tách pool riêng cho endpoint chậm (export, webhook), để chúng không chiếm worker của API chính.

*Xử lý việc chậm*
- Gọi HTTP song song bằng `Http::pool()` hoặc Guzzle async (module 2.4).
- Đẩy việc nặng vào queue.
- Octane khi bootstrap framework chính là nút thắt. Đo trước, và nhớ rủi ro rò state giữa request.

**Đọc**
- Profiler: [Xdebug Profiling](https://xdebug.org/docs/profiler), [SPX](https://github.com/NoiseByNorthwest/php-spx), [xhprof (PECL)](https://pecl.php.net/package/xhprof), [Blackfire docs](https://docs.blackfire.io/), [Tideways](https://tideways.com/)
- PHP: [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) (mục [`opcache.jit`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.jit), [`memory_consumption`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.memory-consumption), [`validate_timestamps`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps)), [Preloading](https://www.php.net/manual/en/opcache.preloading.php), [RFC: JIT](https://wiki.php.net/rfc/jit) (phần benchmark cho thấy khi nào có lợi)
- PHP-FPM: [configuration](https://www.php.net/manual/en/install.fpm.configuration.php), mục [`pm`](https://www.php.net/manual/en/install.fpm.configuration.php#pm), [`pm.max_children`](https://www.php.net/manual/en/install.fpm.configuration.php#pm.max-children), `pm.status_path`, `slowlog`
- Laravel: [Optimizing configuration loading](https://laravel.com/docs/deployment#optimizing-configuration-loading), [Concurrent Requests](https://laravel.com/docs/http-client#concurrent-requests), [Octane](https://laravel.com/docs/octane)
- [PHPBench](https://phpbench.readthedocs.io/)
- Runtime PHP chi tiết: [05-php-laravel.md](05-php-laravel.md); process model FPM ở mức OS: [01-os-linux.md](01-os-linux.md)

**Nắm chắc khi**
- [ ] Profile được một request Laravel bằng SPX hoặc Xdebug, chỉ ra 3 hàm/khối tốn nhất và phần nào là bootstrap framework
- [ ] Đọc được `opcache_get_status()` của production và nói OPcache có đang đủ bộ nhớ, đủ slot không
- [ ] Chọn được `pm` và tính được `max_children` cho một server cụ thể, bảo vệ được bằng cả RAM và Little's law
- [ ] Đo được JIT bật/tắt trên một endpoint I/O-bound và một script CPU-bound, giải thích kết quả

#### 2.4 Checklist tầng network, app code, serialization

**Vì sao cần học:** Sau DB, thời gian của một request thường nằm ở mạng (gọi API tuần tự, không
tái dùng kết nối), ở code có độ phức tạp ẩn, và ở việc chuyển đổi dữ liệu lớn. Đây là checklist để
rà một endpoint chậm khi DB đã ổn, và hay được hỏi dưới dạng "export 1 triệu dòng thế nào".

**Học gì**

*Network*
- Gọi song song các I/O **độc lập** (không cái nào cần kết quả của cái kia):
  - Laravel `Http::pool()`, Go `errgroup`, Java `CompletableFuture` hoặc virtual thread.
  - Ví dụ: gọi 3 API mỗi cái 300 ms. Tuần tự là 900 ms, song song là khoảng 300 ms.
- Đặt timeout cho mọi lời gọi ra ngoài, cả connect timeout và read timeout. Chi tiết ở
  [02-networking.md](02-networking.md).
- Tái dùng kết nối: keep-alive, HTTP/2, dùng lại HTTP client.
  - ⚠️ Tạo client mới mỗi request nghĩa là mỗi lần gọi phải làm lại TCP handshake và TLS handshake,
    tốn thêm vài chục tới vài trăm ms.
- Giảm dữ liệu gửi đi: nén response (gzip, brotli), phân trang, chỉ trả field cần thiết.
- Giảm số *round trip* (lượt đi về qua mạng): batch API, Redis pipeline (gửi nhiều lệnh một lượt).

*App code*
- ⚠️ O(n²) ẩn: `in_array` bên trong vòng lặp duyệt lại cả mảng mỗi lần. Đổi sang tra theo key
  (`isset($map[$id])`) là O(1).
- Việc nặng như gửi email, resize ảnh, tạo báo cáo: đẩy vào queue + worker
  ([12-messaging.md](12-messaging.md)).
- Tính lại cùng một thứ nhiều lần trong một request: *memoize* (lưu kết quả lần đầu, lần sau dùng
  lại).
- Log quá nhiều, hoặc log đồng bộ ra một disk chậm.
- ⚠️ Regex *catastrophic backtracking*: một số regex với input xấu phải thử lại theo cấp số nhân, một
  request có thể ăn CPU hàng giây.

*Serialization*
- *Serialization*: chuyển dữ liệu trong bộ nhớ thành chuỗi byte để gửi đi hoặc lưu, ví dụ JSON.
- `json_encode`/`json_decode` object lớn tốn CPU và RAM. Với dữ liệu lớn, *stream* (ghi dần từng
  phần) thay vì dựng cả mảng trong RAM rồi mới encode.
- Protobuf, MessagePack nhỏ và nhanh hơn JSON, hợp cho giao tiếp nội bộ giữa các service.
- ORM *hydrate* (tạo object model cho từng dòng) hàng nghìn model rất tốn.
  - Báo cáo nên dùng query builder trả mảng, hoặc `cursor()`/`lazy()` để xử lý từng phần thay vì
    nạp hết.

**Đọc**
- Laravel: [Chunking Results](https://laravel.com/docs/eloquent#chunking-results), [Chunking Using Lazy Collections](https://laravel.com/docs/eloquent#chunking-using-lazy-collections)
- AWS Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

**Nắm chắc khi**
- [ ] Viết lại một endpoint gọi 3 API tuần tự thành song song bằng `Http::pool()` và đo latency trước/sau
- [ ] Thiết kế được luồng export 1 triệu dòng không làm treo server (câu 13)

#### 2.5 Connection pool

**Vì sao cần học:** Connection pool là nơi hai sự cố hay gặp nhất xảy ra: pool cạn làm request chờ
dù DB không chậm, và tổng số kết nối vượt giới hạn của DB khi scale app. Với PHP-FPM, cách tính
khác Java/Go vì không có pool trong process. Phỏng vấn hay hỏi "pool size bao nhiêu là đủ".

**Học gì**

*Pool là gì, vì sao cần*
- *Connection pool*: một nhóm kết nối (tới DB hoặc tới một HTTP service) được mở sẵn và cho mượn
  lại. Request mượn một kết nối, dùng xong trả lại cho request sau.
- Lợi ích: tránh chi phí mở kết nối mới mỗi request (TCP, TLS, xác thực).
- ⚠️ Pool càng lớn không phải càng tốt:
  - DB có giới hạn số kết nối (`max_connections`).
  - Quá nhiều kết nối cùng chạy thì chúng tranh nhau CPU và lock của DB, tổng throughput giảm.

*Tính tổng kết nối*
- Công thức: `số instance × pool size ≤ max_connections của DB`, sau khi trừ phần dự phòng cho
  admin, replica, job.
- ⚠️ Autoscale làm vỡ công thức này:
  1. App có 10 instance × pool 20 = 200 kết nối. Ổn.
  2. Autoscale lên 50 instance × pool 20 = 1.000 kết nối.
  3. DB từ chối kết nối mới.
  - Sửa: đặt một *connection pooler* đứng giữa app và DB, gom nhiều kết nối của app thành ít kết
    nối tới DB. Ví dụ ProxySQL (MySQL), RDS Proxy (AWS), PgBouncer (Postgres).

*Pool cạn*
- ⚠️ Khi mọi kết nối đều đang được mượn, request mới phải chờ. Latency tăng trong khi từng query vẫn
  nhanh, nên nhìn slow query log không thấy gì.
- Metric cần có: số kết nối đang dùng, và thời gian chờ để lấy được kết nối.

*PHP-FPM không có pool trong process*
- Mỗi worker giữ kết nối riêng của nó: mở mới mỗi request, hoặc giữ lại giữa các request nếu dùng
  *persistent connection*.
- Tổng kết nối = số server × `max_children` + queue worker + cron.
- Ví dụ: 4 server × 50 worker + 20 queue worker = 220 kết nối lúc cao điểm.

**Đọc**
- [HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing) (áp dụng được cho mọi DB, không chỉ Java)
- Tầng PHP và DB: module 2.7 của [03-database-sql.md](03-database-sql.md)

**Nắm chắc khi**
- [ ] Tính được tổng connection tối đa của hệ thống mình đang làm và so với `max_connections`
- [ ] Giải thích được vì sao pool nhỏ hơn đôi khi cho throughput cao hơn

#### 2.6 Load testing

**Vì sao cần học:** Load test là cách duy nhất biết hệ thống chịu được bao nhiêu trước khi người
dùng thật cho bạn biết. Nhưng load test làm sai rất dễ cho kết quả đẹp mà vô nghĩa. Người phỏng
vấn hay hỏi "bạn load test thế nào" để xem bạn có biết các bẫy đó không.

**Học gì**

*Các loại test*

| Loại | Mục đích | Hình dạng tải |
|---|---|---|
| Load test | Có đạt mục tiêu ở tải dự kiến không | Tăng dần tới mức dự kiến, giữ |
| Stress test | Tìm điểm gãy, xem hỏng thế nào (có graceful không) | Tăng tới khi lỗi |
| Soak test | Lỗi lộ ra theo thời gian: leak, pool rò, đĩa đầy | Tải vừa, nhiều giờ |
| Spike test | Đỉnh đột ngột (flash sale, push notification) | Nhảy vọt trong vài giây |

*Công cụ*
- k6: viết script bằng JavaScript/TypeScript, dễ đưa vào CI.
- Gatling: SDK Java, Kotlin, Scala và JavaScript/TypeScript. Report tốt.
- JMeter: có GUI, nhiều plugin, nặng.
- wrk/wrk2: dòng lệnh, benchmark HTTP rất nhẹ. wrk2 gửi request theo tốc độ cố định (*arrival
  rate*, module 3.3).
- Locust: viết bằng Python. `hey`, `vegeta`: dòng lệnh nhẹ.

*Thiết kế bài test*
- Môi trường giống production: cỡ máy, dữ liệu cỡ thật.
  - ⚠️ DB chỉ có 1.000 dòng thì mọi query đều nhanh.
- Kịch bản giống thật: tỉ lệ các endpoint, *think time* (thời gian người dùng dừng giữa hai thao
  tác), dữ liệu đa dạng.
  - ⚠️ Mọi request dùng cùng một id thì cache hit 100%, kết quả ảo.
- *Warm-up* (chạy nóng máy) trước khi đo, để OPcache, JIT của Java và cache đã đầy.
- Máy sinh tải không được là nút thắt. Theo dõi CPU của máy chạy k6.
- ⚠️ Không load test vào hệ thống dùng chung hoặc dịch vụ thật của bên thứ ba (thanh toán, SMS).
  Dùng mock hoặc sandbox.
- Định nghĩa pass/fail trước khi chạy bằng *threshold*, ví dụ p99 < 300 ms và tỉ lệ lỗi < 0,1%.

*Đọc kết quả*
- Nhìn đồng thời:
  - RPS đạt được, percentile, tỉ lệ lỗi.
  - Tài nguyên server: CPU, RAM, số DB connection, `listen queue` của FPM, độ dài queue.
- Tìm *điểm gãy* (knee): chỗ RPS ngừng tăng dù tải tăng, và latency tăng vọt. Tài nguyên nào bão
  hoà ngay tại điểm đó chính là nút thắt.
- Lỗi tăng theo tải thường là: timeout, pool cạn, 502/503 từ load balancer.

**Đọc**
- k6: [Load test types](https://grafana.com/docs/k6/latest/testing-guides/test-types/), [Thresholds](https://grafana.com/docs/k6/latest/using-k6/thresholds/), [Executors](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/)
- Gatling: [Create your first JavaScript-based simulation](https://docs.gatling.io/tutorials/test-as-code/javascript/running-your-first-simulation/)
- [wrk2](https://github.com/giltene/wrk2) README (đọc phần về constant throughput)

**Nắm chắc khi**
- [ ] Viết được script k6 open model có threshold p99 và tỉ lệ lỗi (bài tập 2)
- [ ] Chạy một stress test lên app Laravel, tìm được điểm gãy và chỉ ra tài nguyên bão hoà (FPM worker, CPU, hay DB)
- [ ] Liệt kê được 5 lý do một load test đẹp nhưng production vẫn chậm

---

### Chặng 3: Senior 🔴

#### 3.1 Tail latency, fan-out, USL

**Vì sao cần học:** Khi một request gọi tới nhiều service hoặc nhiều shard, phần đuôi latency của
từng service cộng dồn thành trải nghiệm chậm của người dùng. USL giải thích vì sao thêm node đôi
khi làm hệ thống chậm đi. Đây là kiến thức phân biệt senior với mid trong câu hỏi system design.

**Học gì**

*Fan-out và tail latency*
- *Fan-out*: một request gọi song song tới N backend và phải chờ **cái chậm nhất** trả về.
- Xác suất ít nhất một backend rơi vào nhóm 1% chậm nhất là `1 − 0,99^N`:
  - N = 1: 1%.
  - N = 100: khoảng 63%.
- Hệ quả: khi fan-out lớn, p99 của backend gần như thành p50 của trải nghiệm người dùng.

*Cách giảm tail*
- *Hedged request*: gửi request, nếu sau một ngưỡng (ví dụ p95) chưa có kết quả thì gửi thêm một
  request dự phòng tới bản sao khác, lấy kết quả nào về trước.
  - ⚠️ Chỉ dùng cho request idempotent, và phải giới hạn tỉ lệ request dự phòng. Không thì chính nó
    nhân tải lên và làm hệ thống chậm thêm.
- Timeout chặt.
- Giảm fan-out.
- Cô lập việc nặng khỏi đường phục vụ request: GC, *compaction* (gom dọn dữ liệu của storage
  engine), backup.

*USL: vì sao thêm node lại chậm đi*
- *USL* (Universal Scalability Law, Neil Gunther) mô tả throughput theo số node N:
  `C(N) = N / (1 + α(N − 1) + βN(N − 1))`
  - `α` (*contention*): chờ tài nguyên chung, giống phần tuần tự của Amdahl.
  - `β` (*coherency*): chi phí để các node đồng bộ với nhau, tăng theo N².
- Khi β > 0, throughput có **đỉnh** rồi **giảm** khi thêm node. Nguồn của β: lock phân tán, cache
  invalidation, *gossip* (các node liên tục trao đổi trạng thái với nhau).
- Cách dùng: đo throughput ở vài mức N, fit ra α và β, rồi dự đoán điểm N tối ưu.

*Metastable failure*
- *Metastable failure*: hệ thống bị đẩy vào trạng thái quá tải **tự duy trì**, và không tự hồi phục
  dù tải gốc đã giảm.
- Ví dụ:
  1. Một đợt tải ngắn làm request timeout.
  2. Client retry, tải tăng gấp đôi (*retry storm*).
  3. Hệ thống càng chậm, càng nhiều timeout, càng nhiều retry.
  4. Tải gốc đã về bình thường nhưng retry vẫn giữ hệ thống quá tải.
- Nguyên nhân khác: cache lạnh sau restart làm DB quá tải, DB chậm làm cache không kịp đầy lại.

**Đọc**
- [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/): đọc hết
- Neil Gunther: [How to Quantify Scalability](http://www.perfdynamics.com/Manifesto/USLscalability.html)
- Marc Brooker: [Metastability and Distributed Systems](https://brooker.co.za/blog/2021/05/24/metastable.html)

**Nắm chắc khi**
- [ ] Tính được xác suất một request chạm đuôi khi fan-out 10, 50, 100 backend
- [ ] Giải thích được bằng USL vì sao thêm node làm hệ thống chậm đi, cho một ví dụ thật
- [ ] Thiết kế được hedged request có giới hạn cho một lời gọi đọc

#### 3.2 GC và lock contention

**Vì sao cần học:** Hai nguyên nhân phổ biến của p99 có đỉnh bất thường mà profile CPU thông thường
khó thấy là GC và tranh chấp lock. Với PHP, lock gần như luôn nằm ở tầng dưới (MySQL, Redis,
session file), còn Java/Go thì cả trong app. Câu hỏi hay gặp: "thêm CPU mà throughput không tăng,
vì sao".

**Học gì**

*GC*
- Triệu chứng: p99 có các đỉnh định kỳ, CPU cao dù traffic không đổi.
- Giảm lượng cấp phát bộ nhớ:
  - Tái dùng buffer, ví dụ Go `sync.Pool`.
  - Tránh tạo object tạm trong vòng lặp nóng.
- Java: G1 là GC mặc định. ZGC (bản generational) cho pause rất thấp. Đặt heap hợp lý và đọc GC log.
- Go: chỉnh bằng `GOGC` (GC chạy khi heap tăng bao nhiêu %) và `GOMEMLIMIT` (ngưỡng bộ nhớ).
- PHP: dùng *refcount* (đếm tham chiếu, về 0 thì giải phóng ngay) cộng *cycle collector* (dọn các
  object tham chiếu vòng lẫn nhau).
  - Ít quan trọng với FPM vì process reset sau mỗi request.
  - Queue worker hoặc Octane xử lý tập dữ liệu lớn có thể tốn thời gian ở `gc_collect_cycles`.
- Chi tiết: [06-java-spring.md](06-java-spring.md), [07-go.md](07-go.md).

*Lock contention*
- *Lock contention*: nhiều thread hoặc request cùng muốn một khoá, chỉ một cái được giữ, còn lại
  phải chờ.
- Triệu chứng:
  - Thêm CPU hay thêm thread không tăng throughput.
  - CPU thấp nhưng latency cao.
  - Thread dump (Java) có nhiều thread ở trạng thái `BLOCKED`.
- Nguồn hay gặp:
  - Mutex toàn cục, `synchronized` bọc quanh I/O.
  - **Hàng DB nóng**: mọi request cùng cập nhật một dòng, ví dụ counter hay số dư.
  - Lock bên trong pool.
- Với PHP, contention gần như luôn ở tầng dưới:
  - Row lock của MySQL.
  - Redis lock.
  - File lock của session driver `file`: hai request cùng session phải chạy lần lượt.

*Cách giảm contention*
- Thu nhỏ *critical section* (đoạn code chạy khi đang giữ lock).
- Không giữ lock trong lúc gọi I/O.
- *Sharded counter*: chia một counter thành N dòng, mỗi lần tăng ngẫu nhiên một dòng, khi đọc thì
  cộng lại. Tranh chấp giảm N lần.
- Dùng thao tác *atomic*, hoặc gom nhiều lần ghi thành một.
- Xem thêm [13-concurrency.md](13-concurrency.md).

**Đọc**
- Go: [A Guide to the Go Garbage Collector](https://go.dev/doc/gc-guide)
- Cloudflare: [The story of one latency spike](https://blog.cloudflare.com/the-story-of-one-latency-spike/) (điều tra một đỉnh p99 tới tận kernel)
- MySQL lock: module 2.6 và 3.2 của [03-database-sql.md](03-database-sql.md)

**Nắm chắc khi**
- [ ] Phân biệt được đỉnh p99 do GC và do lock bằng dữ liệu (GC log, thread dump, profile)
- [ ] Thiết kế được sharded counter cho "lượt xem bài viết" 10.000 lượt/giây trên MySQL

#### 3.3 Load test không tự lừa mình: open/closed model, coordinated omission

**Vì sao cần học:** Phần lớn công cụ load test mặc định đo sai theo cách làm kết quả đẹp hơn thực
tế, đôi khi đẹp hơn hàng chục lần ở p99. Biết open/closed model và coordinated omission là dấu hiệu
rõ của người đã load test nghiêm túc. Câu hỏi hay gặp: "load test p99 200 ms mà production 3 giây,
vì sao".

**Học gì**

*Closed model và open model*

| | Closed model | Open model |
|---|---|---|
| Cách sinh tải | Số *virtual user* (VU, người dùng giả lập) cố định. Mỗi VU gửi request tiếp theo sau khi nhận response | Request đến với tốc độ cố định, bất kể hệ nhanh hay chậm |
| Khi hệ thống chậm | Tải tự giảm, vì VU đang chờ response | Tải vẫn giữ nguyên, request dồn lại |
| Giống thực tế | Hệ có số client cố định (ví dụ job nội bộ) | Traffic Internet thật |
| k6 executor | `constant-vus`, `ramping-vus` | `constant-arrival-rate`, `ramping-arrival-rate` |

*Coordinated omission*
- *Coordinated omission*: lỗi đo khiến percentile đẹp hơn thực tế. Xảy ra trong closed model:
  1. Server khựng 2 giây.
  2. Mọi VU đều đang chờ response, nên công cụ **không gửi** các request lẽ ra phải gửi trong 2
     giây đó.
  3. Công cụ chỉ ghi nhận vài request chậm (những cái đang chờ), còn hàng trăm request "lẽ ra bị
     chậm" không bao giờ tồn tại trong số liệu.
  4. Kết quả: percentile đẹp hơn thực tế rất nhiều.
- Thực tế người dùng thật vẫn tới trong 2 giây đó, và ai cũng bị chậm.
- Cách tránh:
  - Dùng open model.
  - Dùng công cụ đo latency từ thời điểm request **lẽ ra** được gửi, không phải lúc thật sự gửi:
    wrk2, hoặc HdrHistogram có hiệu chỉnh.
- ⚠️ Open model cần đủ VU dự phòng (`preAllocatedVUs`/`maxVUs` trong k6). Thiếu VU thì k6 báo
  *dropped iterations* (lượt không gửi được). Bản thân đó là tín hiệu hệ thống không theo kịp tải.

**Đọc**
- k6: [Open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)
- Gil Tene: ["How NOT to Measure Latency"](https://www.youtube.com/watch?v=lJ8ydIuPFeU) (video, bài nói gốc về coordinated omission)
- [HdrHistogram](https://github.com/HdrHistogram/HdrHistogram) README

**Nắm chắc khi**
- [ ] Chạy cùng một endpoint có pause ngẫu nhiên bằng closed và open model, so p99 và giải thích chênh lệch
- [ ] Giải thích được coordinated omission cho người chưa biết trong 2 phút

#### 3.4 Scale nâng cao: precompute và đánh đổi

**Vì sao cần học:** Khi query và index đã tối ưu mà vẫn chậm, phải chọn giữa cache, queue, replica,
sharding, precompute, mỗi cái có cái giá riêng. Người phỏng vấn senior chấm việc bạn chọn theo
thứ tự hợp lý và nói được cái giá, không phải kể tên kỹ thuật.

**Học gì**

*Bảng kỹ thuật và cái giá*

| Kỹ thuật | Giải quyết | Cái giá |
|---|---|---|
| Tối ưu query/index | Đa số vấn đề DB | Thời gian phân tích |
| Cache | Đọc lặp lại | Stale, invalidation |
| CDN | File tĩnh, người dùng xa | Invalidation, chi phí |
| Async (queue) | Việc chậm trong request, đỉnh tải | Eventual consistency, vận hành queue |
| Read replica | Đọc nhiều | Replication lag |
| Sharding | Ghi hoặc dữ liệu vượt một node | Query xuyên shard, rebalance, phức tạp lớn |
| Precompute / materialized view | Query tổng hợp nặng lặp lại | Dữ liệu trễ, công đồng bộ |

- Giải thích các từ trong bảng:
  - *Stale*: dữ liệu trong cache đã cũ so với DB. *Invalidation*: xoá hoặc cập nhật cache khi dữ
    liệu gốc đổi.
  - *CDN*: mạng máy chủ đặt gần người dùng, giữ bản sao file tĩnh.
  - *Eventual consistency*: dữ liệu sẽ đúng sau một lúc, không đúng ngay lập tức.
  - *Replication lag*: độ trễ để thay đổi trên DB chính tới được replica. Vừa ghi xong đọc từ
    replica có thể chưa thấy.
  - *Sharding*: chia dữ liệu ra nhiều DB theo một khoá, ví dụ theo `user_id`. *Rebalance*: chuyển dữ
    liệu giữa các shard khi thêm shard.

*Precompute*
- *Precompute*: tính trước lúc ghi hoặc theo lịch, thay vì tính lúc đọc. Ví dụ:
  - Bảng tổng hợp doanh thu theo ngày, job cập nhật mỗi đêm.
  - Counter cập nhật ngay khi có sự kiện, thay vì `COUNT(*)` khi đọc.
  - Feed đã *fan-out* sẵn: khi một người đăng bài, ghi bài vào feed của từng follower.
- *Materialized view*: một view mà kết quả được lưu lại như một bảng.
  - PostgreSQL có sẵn, làm mới bằng `REFRESH MATERIALIZED VIEW`. Thêm `CONCURRENTLY` (cần unique
    index) để không khoá người đọc trong lúc làm mới.
  - MySQL không có sẵn. Tự làm bằng bảng tổng hợp, cập nhật qua job, trigger, hoặc *CDC* (đọc
    binlog để bắt thay đổi).
- Cái giá:
  - Dữ liệu trễ so với nguồn.
  - Tốn thêm storage.
  - Logic cập nhật phải đúng, và phải chạy lại được khi cần sửa sai (ví dụ đơn bị hoàn).
- Thứ tự áp dụng cho DB: xem module 3.6 của [03-database-sql.md](03-database-sql.md).

**Đọc**
- PostgreSQL: [REFRESH MATERIALIZED VIEW](https://www.postgresql.org/docs/current/sql-refreshmaterializedview.html)
- DDIA ch.1 (ví dụ Twitter home timeline: fan-out lúc ghi hay lúc đọc) và ch.11 (derived data)

**Nắm chắc khi**
- [ ] Thiết kế được bảng tổng hợp doanh thu theo ngày cho MySQL: cập nhật thế nào, sửa sai thế nào khi đơn bị hoàn
- [ ] Với dashboard chạy query 8 giây, nêu được 3 phương án theo thứ tự và cái giá của mỗi cái

#### 3.5 Capacity planning, autoscaling, load shedding

**Vì sao cần học:** Flash sale, chiến dịch marketing, mùa cao điểm: đều cần trả lời "cần bao nhiêu
máy" trước khi sự kiện xảy ra. Autoscaling nghe như giải pháp tự động, nhưng làm sai thì chính nó
đánh sập DB. Đây là chủ đề hay gặp ở vòng system design senior, dưới dạng "chuẩn bị cho flash sale
gấp 10 lần tải thường".

**Học gì**

*Capacity planning*
- *Capacity planning*: tính trước cần bao nhiêu tài nguyên cho tải dự kiến. Các bước:
  1. Load test để biết một instance chịu được X RPS mà vẫn đạt p99 mục tiêu.
  2. Tải dự kiến Y RPS thì cần `Y / X` instance.
  3. Cộng *headroom*: thường giữ utilization ở 50–70%, không chạy sát 100% (module 2.1).
  4. Tính cho trường hợp hỏng: N+1 (mất một máy vẫn chịu được), hoặc mất một *AZ* (availability
     zone, một trung tâm dữ liệu). Chạy 3 AZ mà mất một thì 2 AZ còn lại phải chịu 100% tải.
- Dự báo theo xu hướng tăng trưởng, cộng các sự kiện đã biết (khuyến mãi, mùa cao điểm).
- Kiểm tra các nút thắt dùng chung, không scale theo app: DB, cache, queue, quota API của bên thứ
  ba, giới hạn tài khoản của cloud provider.

*Autoscaling*
- *Autoscaling*: tự thêm hoặc bớt instance theo một metric. Các metric hay dùng:
  - CPU, RPS.
  - Độ dài queue, hoặc *consumer lag* (số message chưa xử lý), dùng cho worker. Trên Kubernetes có
    KEDA.
  - Theo lịch, cho tải biết trước.
- ⚠️ **Scale chậm hơn spike**:
  1. Metric phải vượt ngưỡng một lúc mới được phát hiện.
  2. Khởi động máy hoặc pod mới.
  3. Warm-up (OPcache, cache, kết nối).
  - Tổng có thể mất vài phút, trong khi spike tính bằng giây đã làm sập trước. Chữa bằng: scale
    trước theo lịch, giữ headroom, rate limit, load shedding.
- ⚠️ **DB không scale theo**: autoscale app từ 10 lên 50 instance là gấp 5 lần kết nối và query vào
  cùng một DB. Autoscale app có thể chính là thứ đánh sập DB (module 2.5).
- ⚠️ Scale theo CPU khi nút thắt là I/O: CPU thấp nên không scale, dù latency đang tăng.
  - PHP-FPM chờ API ngoài là ví dụ điển hình. Scale theo số worker bận hoặc `listen queue` đúng hơn.
- ⚠️ *Flapping*: scale lên rồi xuống liên tục. Cần *cooldown* (thời gian chờ giữa hai lần scale), và
  ngưỡng scale lên khác ngưỡng scale xuống.
- Đặt max replicas để một bug không làm hoá đơn cloud bùng nổ.
- Scale xuống phải graceful: drain connection, làm xong job ([01-os-linux.md](01-os-linux.md), module 2.3).

*Load shedding*
- *Load shedding*: khi quá tải, chủ động từ chối sớm một phần request (trả 503 hoặc 429), ưu tiên
  giữ request quan trọng.
- Vì sao tốt hơn: không shedding thì mọi request cùng chậm rồi cùng timeout, số request thành công
  gần bằng 0. Shedding thì phần được nhận vẫn thành công.
- ⚠️ Với PHP-FPM, request đã vào `listen queue` thì vẫn chiếm chỗ và vẫn phải chờ. Từ chối sớm ở
  Nginx hoặc load balancer (`limit_req`, `limit_conn`) rẻ hơn nhiều.

**Đọc**
- Kubernetes: [Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) (mục *stabilization window*, *scaling policies*), [KEDA](https://keda.sh/)
- Google SRE: [Handling Overload](https://sre.google/sre-book/handling-overload/), [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/), Workbook [Managing Load](https://sre.google/workbook/managing-load/)
- AWS Builders' Library: [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)

**Nắm chắc khi**
- [ ] Viết được kế hoạch capacity cho flash sale (bài tập 5) có số instance, headroom, nút thắt chung, kế hoạch dự phòng
- [ ] Chọn được metric autoscale đúng cho API Laravel chờ I/O và cho queue worker
- [ ] Giải thích được vì sao load shedding làm hệ thống phục vụ **nhiều** request thành công hơn

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Latency và throughput khác nhau thế nào?** (1.1)
- Ý phải có: thời gian một request so với số request mỗi giây; không tỉ lệ nghịch đơn giản
- Điểm cộng: latency phải kèm mức tải; Little's law nối hai đại lượng

**2. Vì sao nhìn p99 thay vì trung bình?** (1.1)
- Ý phải có: trung bình che đuôi; người dùng nặng thường rơi vào đuôi
- Điểm cộng: không lấy trung bình của percentile; fan-out làm đuôi thành trải nghiệm phổ biến
- Red flag: "trung bình 200 ms là ổn"

**3. N+1 query là gì, sửa thế nào?** (1.3)
- Ý phải có: 1 query danh sách + N query quan hệ; eager loading hoặc `IN`
- Điểm cộng: `preventLazyLoading()` ở dev; vì sao N+1 không hiện trên slow log

**4. API chậm, bạn làm gì đầu tiên?** (1.2)
- Ý phải có: đặt mục tiêu bằng số, đo baseline, dùng trace/APM tìm thời gian nằm ở đâu, sửa nút thắt lớn nhất, đo lại
- Red flag: "thêm cache" hoặc "nâng cấp server" trước khi đo

**5. Scale dọc và scale ngang, khi nào dùng cái nào?** (1.4)
- Ý phải có: máy to hơn so với thêm máy; ngang cần stateless và LB; dọc có trần và SPOF
- Điểm cộng: DB thường scale dọc trước; kể được chỗ app Laravel không stateless (session file, upload local)

### 🟡 Mid

**6. Little's law là gì? Dùng để tính số connection thế nào?** (2.1)
- Ý phải có: `L = λ × W`; ví dụ số: 1.000 RPS × 200 ms = 200 đồng thời
- Điểm cộng: dependency chậm lên làm `L` tăng tuyến tính và cạn pool; áp dụng cho `pm.max_children`

**7. Flame graph đọc thế nào?** (2.2)
- Ý phải có: y là stack, x không phải thời gian, độ rộng là tỉ lệ mẫu; tìm cao nguyên rộng
- Điểm cộng: không thấy thời gian chờ I/O; off-CPU profile

**8. Profile một app PHP thế nào? Dùng công cụ gì ở dev, ở production?** (2.3)
- Ý phải có: Xdebug profiler ở dev (overhead lớn); SPX, Blackfire, Tideways, xhprof cho môi trường gần production; APM cho bức tranh tổng
- Điểm cộng: tách thời gian bootstrap framework khỏi logic; so hai profile trước/sau
- Red flag: bật Xdebug trên production để "xem cho nhanh"

**9. OPcache làm gì? JIT có làm app Laravel nhanh hơn không?** (2.3)
- Ý phải có: cache bytecode trong shared memory, bỏ compile mỗi request; JIT chỉ giúp CPU-bound, request web chủ yếu chờ I/O nên lợi ích nhỏ
- Điểm cộng: PHP 8.4 tắt JIT mặc định; `validate_timestamps=0` và reload khi deploy; theo dõi hit rate, wasted memory

**10. Chọn `pm` và `pm.max_children` cho PHP-FPM thế nào?** (2.3)
- Ý phải có: static/dynamic/ondemand và khi nào dùng; `max_children` theo RAM (PSS mỗi worker) và theo Little's law
- Điểm cộng: `pm.status_path` và slowlog để kiểm chứng; tách pool cho endpoint chậm; nhân với số server khi tính kết nối DB
- Red flag: đặt `max_children` thật lớn "cho chắc"

**11. Load test, stress test, soak test, spike test khác nhau thế nào?** (2.6)
- Ý phải có: mục đích và hình dạng tải của từng loại
- Điểm cộng: soak test bắt leak và pool rò; spike test kiểm tra autoscale và load shedding

**12. Chọn kích thước connection pool thế nào?** (2.5)
- Ý phải có: tổng pool của mọi instance ≤ `max_connections` trừ dự phòng; lớn quá làm DB chậm vì tranh chấp
- Điểm cộng: metric thời gian chờ lấy connection; pooler ngoài (ProxySQL, RDS Proxy) khi app autoscale

**13. Xuất báo cáo 1 triệu dòng mà không làm treo server.** (2.4)
- Ý phải có: không làm trong request HTTP; queue + worker; đọc theo lô bằng keyset/cursor (`cursor()`/`lazy()`), ghi file stream (CSV); xong thì gửi link (object storage + presigned URL)
- Điểm cộng: đọc từ replica; giới hạn số job export đồng thời; job idempotent, có tiến độ

### 🔴 Senior

**14. API p99 là 3 giây nhưng trung bình chỉ 200 ms. Điều tra thế nào?** (1.1, 2.2, 3.2)
- Ý phải có: xem trace của request chậm, tìm điểm chung (endpoint, tenant lớn, tham số, instance, thời điểm); đỉnh định kỳ (cron, backup, GC) hay ngẫu nhiên
- Điểm cộng: nghi phạm theo tầng: query với dữ liệu lớn, API ngoài timeout dài, chờ pool/FPM `listen queue`, lock DB, GC, cold cache

**15. Vì sao tail latency quan trọng hơn khi fan-out?** (3.1)
- Ý phải có: phải chờ cái chậm nhất; 1 − 0,99^N; N = 100 → 63%
- Điểm cộng: hedged request có giới hạn; giảm fan-out; cô lập việc nặng

**16. Amdahl's law và USL nói gì? Vì sao thêm máy có thể chậm hơn?** (2.1, 3.1)
- Ý phải có: phần tuần tự đặt trần; USL thêm chi phí đồng bộ β làm throughput có đỉnh rồi giảm
- Điểm cộng: ví dụ thật (lock phân tán, cache invalidation, một dòng DB nóng); tìm nút thắt chung trước khi thêm máy
- Red flag: "thêm máy là tăng tuyến tính"

**17. Coordinated omission là gì?** (3.3)
- Ý phải có: closed model ngừng gửi khi server khựng nên bỏ sót request chậm; percentile đẹp giả
- Điểm cộng: open model, wrk2, HdrHistogram; dropped iterations của k6 là tín hiệu

**18. Load test đạt 5.000 RPS với p99 80 ms, lên production 1.000 RPS đã chậm.** (2.6, 3.3)
- Ý phải có: so dữ liệu (cỡ DB, độ đa dạng), kịch bản (tỉ lệ endpoint, đọc/ghi), cache hit ảo, dependency được mock
- Điểm cộng: coordinated omission và closed model; máy sinh tải bão hoà; warm-up

**19. Autoscaling có những cạm bẫy gì?** (3.5)
- Ý phải có: scale chậm hơn spike; DB và dependency không scale theo; connection nhân lên; metric sai (CPU khi nút thắt là I/O)
- Điểm cộng: flapping, max replicas, scale xuống graceful; scale theo lịch và headroom cho sự kiện biết trước
- Red flag: "bật HPA là xong"

**20. Sau khi bật autoscaling, giờ cao điểm DB báo "too many connections".** (2.5, 3.5)
- Ý phải có: phép nhân instance × pool (với PHP: server × `max_children`); đặt max replicas; giảm pool mỗi instance; thêm pooler
- Điểm cộng: hỏi ngược vì sao cần nhiều instance: nếu request chậm vì DB chậm thì scale app chỉ làm DB tệ hơn

**21. Memory của service tăng dần sau mỗi lần deploy tới khi bị OOM kill.** (3.2)
- Ý phải có: phân biệt leak thật và cache tăng tới ngưỡng; heap dump/profile ở hai thời điểm và so sánh
- Điểm cộng: nghi phạm theo ngôn ngữ (static/global trong queue worker và Octane, listener, goroutine leak); `--max-jobs`/`--max-time` chỉ là giảm thiệt hại

**22. CPU 100% trên mọi instance, traffic không tăng.** (2.2, 3.1)
- Ý phải có: có deploy gần đây thì rollback trước; lấy CPU profile/flame graph; thread dump nhiều lần
- Điểm cộng: nghi phạm: vòng lặp vô hạn, regex backtracking với input mới, GC liên tục, retry storm, cache hết hạn đồng loạt; metastable failure

**23. Bạn làm capacity planning cho đợt khuyến mãi thế nào?** (3.5)
- Ý phải có: dự báo tải đỉnh từ dữ liệu cũ và kế hoạch marketing; load test tìm X RPS mỗi instance; headroom và mất một AZ; nút thắt chung
- Điểm cộng: scale trước theo lịch; load shedding và hàng đợi ảo cho luồng mua; kiểm tra quota bên thứ ba; kế hoạch rollback và người trực

**24. Hệ thống quá tải, bạn chọn từ chối bớt request hay để mọi request chậm?** (3.5)
- Ý phải có: load shedding sớm (429/503) giữ được throughput hữu ích; để hàng đợi dài thì mọi request cùng timeout
- Điểm cộng: ưu tiên request quan trọng (thanh toán hơn gợi ý sản phẩm); từ chối ở Nginx/LB rẻ hơn ở PHP-FPM; client phải retry có backoff

---

## Bài tập tự làm

1. **N+1.** Viết một endpoint có N+1 query (Laravel hoặc ngôn ngữ bạn dùng), đo số query và thời gian với 1.000 bản ghi, rồi sửa và đo lại.
2. **k6 open model.** Viết script k6 cho một API với executor `constant-arrival-rate`, threshold p99 và tỉ lệ lỗi. Chạy thêm bản `constant-vus` trên cùng endpoint và giải thích vì sao hai kết quả khác nhau.
3. **Little's law.** Một service nhận 800 RPS, mỗi request gọi DB 3 lần, mỗi lần 20 ms, và giữ connection trong suốt request 150 ms.
   - Tính số DB connection tối thiểu, và tính lại khi DB chậm gấp 5.
   - Nếu đây là PHP-FPM trên 4 server, mỗi server cần tối thiểu bao nhiêu worker?
4. **Profiling.** Lấy CPU profile của một chương trình Go hoặc Java nhỏ có một hàm nóng, vẽ flame graph và chỉ ra hàm tốn nhất. Làm tương tự với một request Laravel bằng SPX hoặc Xdebug.
5. **Capacity.** Viết kế hoạch capacity cho một đợt flash sale: dự kiến tải, số instance, headroom, các nút thắt chung (DB, Redis, cổng thanh toán) và kế hoạch dự phòng.
6. **Tuning PHP-FPM.** Trên một server có app Laravel:
   - Đo PSS mỗi worker dưới tải, tính `max_children` theo RAM và theo Little's law.
   - Chạy stress test với `pm = static` và `pm = dynamic`, ghi lại p99, `listen queue` và `max children reached`.
   - Đọc `opcache_get_status()` trước và sau test, nói OPcache có đủ cấu hình không.

> Nộp bài vào đây để được review.
