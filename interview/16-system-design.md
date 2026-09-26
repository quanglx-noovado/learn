# 16. System design

> [← Mục lục](README.md) · Trọng tâm: **phương pháp làm bài 45–60 phút**, ước lượng back-of-envelope (kể cả ước lượng số server PHP-FPM), building blocks, availability, và ý then chốt của các bài kinh điển.
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

Với các bài kinh điển (chặng 2–3), **Học gì** chỉ ghi ý then chốt người chấm tìm; lời giải
đầy đủ nằm trong nguồn ở mục **Đọc**. Hãy tự làm bài trước rồi mới đọc.

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| *System Design Interview*, vol 1 và vol 2 (Alex Xu; vol 2 viết cùng Sahn Lam) | Sách | Phương pháp và gần như mọi bài kinh điển trong file này. Một phần vol 1 đọc được trên [ByteByteGo](https://bytebytego.com/) |
| [System Design Primer](https://github.com/donnemartin/system-design-primer) | Repo GitHub miễn phí | Building blocks, bảng con số, danh sách bài đọc thêm |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Lý thuyết phía sau: replication, partitioning, stream. Khi người chấm hỏi "vì sao" |
| [Google SRE Book](https://sre.google/sre-book/table-of-contents/) | Sách online miễn phí | Availability, SLO, overload, cascading failure |
| [Amazon Builders' Library](https://aws.amazon.com/builders-library/) | Blog kỹ thuật | Kinh nghiệm vận hành thật: multi-AZ, shuffle sharding, load shedding |
| Blog kỹ thuật công ty (Discord, Slack, Dropbox, Stripe, Shopify...) | Blog | Bài gốc của từng bài kinh điển, dẫn ở từng module |

Đọc kèm các file nền: [11-cache.md](11-cache.md), [12-messaging.md](12-messaging.md),
[14-distributed-systems.md](14-distributed-systems.md), [03-database-sql.md](03-database-sql.md).

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Làm bài đúng quy trình, ước lượng nhanh, biết building block nào dùng khi nào, tính availability | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.7 | Tự làm trọn vẹn 7 bài hay gặp nhất ở mức mid, có deep dive | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.8 | Bài có tiền và tranh chấp (ví, flash sale), hạ tầng (KV store, scheduler, metrics), bài có dữ liệu lớn | 10–12 ngày |

Mỗi bài kinh điển: tự làm 45 phút trên giấy theo quy trình ở 1.1, rồi mới đọc nguồn và so.
Chỉ đọc lời giải mà không tự làm thì gần như không có tác dụng khi vào phòng phỏng vấn.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Phương pháp làm bài 45–60 phút

**Vì sao cần học:** Vòng system design không chấm đáp án đúng, vì đề nào cũng có nhiều đáp án. Người
chấm chấm **cách bạn đi tới** thiết kế: có hỏi rõ đề không, có ước lượng không, có nói được vì
sao chọn cái này mà không chọn cái kia không. Không có quy trình thì rất dễ sa vào vẽ hộp 30 phút
rồi hết giờ mà chưa đi qua được một luồng nào.

**Học gì**

*Bảy bước và thời gian*
- Bảng dưới cho bài 45 phút. Bài 60 phút thì giãn phần deep dive.

  | Bước | Thời gian | Làm gì |
  |---|---|---|
  | 1. Requirement | 5–8 phút | Functional 3–5 tính năng, **chốt phạm vi** (cái gì không làm). Non-functional: quy mô, latency, consistency, availability, tỉ lệ đọc/ghi |
  | 2. Ước lượng | 3–5 phút | QPS đọc/ghi, peak, storage vài năm. Chỉ tính con số ảnh hưởng thiết kế |
  | 3. API | 3–5 phút | 3–5 endpoint, phân trang, idempotency key cho ghi quan trọng |
  | 4. Data model | 5 phút | Bảng chính, khoá, index, loại DB và vì sao |
  | 5. Kiến trúc tổng | 10 phút | Sơ đồ hộp, **đi qua luồng đọc và luồng ghi** |
  | 6. Deep dive | 10–15 phút | 2–3 điểm then chốt: nút thắt, consistency, hot key, failure |
  | 7. Tổng kết | 2–3 phút | Trade-off đã chọn, điểm yếu còn lại, hướng mở rộng |

- Giải nghĩa các từ trong bảng:
  - *Functional requirement*: hệ thống làm được gì, ví dụ "rút gọn URL", "xem thống kê click".
  - *Non-functional requirement*: hệ thống phải tốt tới mức nào: chịu bao nhiêu người, nhanh bao
    nhiêu, được phép sai lệch hay chết bao lâu.
  - *QPS* (*queries per second*): số request mỗi giây. *Peak* là mức cao nhất trong ngày.
  - *Idempotency key*: một mã client gửi kèm request ghi. Server thấy mã đã xử lý rồi thì trả lại
    kết quả cũ thay vì làm lần hai. Nhờ vậy retry không tạo đơn hay trừ tiền hai lần.
  - *Deep dive*: đào sâu vào vài điểm khó nhất của bài.
  - *Hot key*: một key bị truy cập nhiều bất thường, dồn tải lên một node duy nhất.

*Hỏi gì ở bước requirement*
- Ai dùng, bao nhiêu người dùng mỗi ngày (*DAU*, *daily active users*), ở những vùng địa lý nào.
- Tỉ lệ đọc so với ghi.
- Chỗ nào cần *consistency* mạnh (mọi người luôn thấy dữ liệu mới nhất, ví dụ tiền, tồn kho), chỗ
  nào chấp nhận eventual (dữ liệu trễ vài giây vẫn được, ví dụ feed, số like).
- *p99* mục tiêu, tức mức latency mà 99% request phải nhanh hơn.
- Giữ dữ liệu bao lâu.
- Compliance: xoá dữ liệu cá nhân theo yêu cầu, *data residency* (dữ liệu phải nằm ở một quốc gia
  nhất định).

*Người chấm đánh giá gì*
- Làm rõ được một đề bài mơ hồ.
- Có thiết kế chạy được end-to-end trước, rồi mới tối ưu.
- Biết **vì sao** không dùng phương án khác.
- Nói được trade-off, *failure mode* (hệ thống hỏng theo kiểu nào) và cách vận hành.
- Dẫn dắt được buổi nói chuyện, và biết nhận gợi ý của người chấm.
- Riêng senior: tự nhận ra điểm then chốt của bài. Ví dụ bài thanh toán thì then chốt là
  idempotency và ledger (sổ cái ghi mọi biến động tiền, module 3.1), không phải chọn framework.

*Lỗi hay gặp*
- ⚠️ Chọn Kafka hay Cassandra trước khi biết quy mô.
- ⚠️ Không hỏi requirement.
- ⚠️ Nói "dùng Redis" mà không nói mất gì khi Redis chết.
- ⚠️ Vẽ nhiều hộp nhưng không đi qua luồng nào.
- ⚠️ Microservices cho hệ 100 QPS.
- ⚠️ Tính toán mất 15 phút.
- ⚠️ Im lặng suy nghĩ lâu. Hãy nghĩ thành tiếng.

**Đọc**
- Alex Xu vol 1, ch.3 *A Framework for System Design Interviews* ([bản online](https://bytebytego.com/courses/system-design-interview/a-framework-for-system-design-interviews))
- [Hello Interview: System Design in a Hurry](https://www.hellointerview.com/learn/system-design/in-a-hurry/introduction): góc nhìn của người chấm

**Nắm chắc khi**
- [ ] Làm được một bài 45 phút đúng bảy bước, ghi giờ từng bước, không bước nào lố quá 50%
- [ ] Liệt kê được 6 câu hỏi requirement cho một đề bất kỳ trong 1 phút

#### 1.2 Ước lượng back-of-envelope

**Vì sao cần học:** Ước lượng là thứ biến "hệ này cần cache không, cần shard không" từ cảm tính
thành con số. Trong phỏng vấn, người chấm muốn thấy bạn tính nhanh và biết con số nào làm đổi
thiết kế. Ngoài công việc, câu "cần bao nhiêu server PHP-FPM cho đợt khuyến mãi" dùng đúng các
công thức ở đây.

**Học gì**

*Các con số cần thuộc*
- Lũy thừa 2 và đơn vị:

  | Lũy thừa 2 | Xấp xỉ | Đơn vị |
  |---|---|---|
  | 2^10 | 10^3 | KB |
  | 2^20 | 10^6 | MB |
  | 2^30 | 10^9 | GB |
  | 2^40 | 10^12 | TB |
  | 2^50 | 10^15 | PB |

- Kích thước thường gặp:
  - `int64` hay timestamp: 8 byte.
  - UUID: 16 byte khi lưu nhị phân, 36 ký tự khi lưu dạng chuỗi.
  - Ký tự tiếng Việt có dấu trong UTF-8: thường 2–3 byte.
- Độ trễ, tính theo bậc độ lớn:

  | Thao tác | Độ trễ gần đúng |
  |---|---|
  | Đọc L1 cache | ~1 ns |
  | Đọc RAM | ~100 ns |
  | Đọc ngẫu nhiên SSD | ~16–100 µs |
  | Round trip trong cùng datacenter | ~0,5 ms |
  | Seek HDD | ~2–10 ms |
  | Round trip xuyên lục địa | ~150 ms |

  - *Round trip* là thời gian gửi một gói tin đi và nhận trả lời về.
  - Đọc RAM nhanh hơn một round trip trong datacenter khoảng **5.000 lần** (100 ns so với 0,5 ms).
  - Round trip xuyên lục địa chậm hơn trong datacenter khoảng 300 lần.
  - Hệ quả: một request gọi mạng tuần tự 10 lần là thấy chậm ngay.

*QPS, storage, bandwidth*
- Mẹo: 1 ngày ≈ 86.400 giây ≈ 10^5 giây. Nên **1 triệu request/ngày ≈ 12 QPS**.
- Công thức: QPS = DAU × số request mỗi user / 86.400.
- Peak thường gấp 2–10 lần trung bình. Flash sale có thể gấp hàng trăm lần.
- **Storage** = số bản ghi mỗi ngày × kích thước mỗi bản ghi × số ngày lưu × số bản sao × hệ số
  cho index và overhead.
- **Bandwidth** = QPS × kích thước response. Tính riêng chiều đọc và chiều ghi.

*Số server theo QPS*
- Công thức: số server = peak QPS / (QPS một server chịu được × mức tải mục tiêu) + dự phòng.
  - Mức tải mục tiêu thường 60–70%, để còn chỗ cho đột biến.
  - Dự phòng *N+1*: thêm một máy, để một máy chết hay đang bảo trì thì vẫn đủ.
- QPS một server lấy từ **load test**, không đoán. Con số trong sách chỉ là bậc độ lớn.

*Riêng PHP-FPM*
- Mỗi worker PHP-FPM xử lý một request tại một thời điểm. Theo *Little's law* (số việc đang xử lý
  = tốc độ đến × thời gian xử lý mỗi việc), suy ra:
  - QPS một server ≈ **số worker / latency trung bình**.
  - Ví dụ: 50 worker, latency 100 ms → khoảng 500 QPS.
- Số worker bị chặn bởi RAM:
  - `pm.max_children` ≈ RAM dành cho FPM / *RSS* mỗi worker.
  - RSS (*resident set size*) là lượng RAM thật một process đang chiếm. Phải đo thật, thường vài
    chục MB.
- Và bị chặn bởi CPU:
  - Ví dụ: mỗi request tốn 20 ms CPU, máy 8 core → trần khoảng 400 QPS, dù có bao nhiêu worker.
  - Thêm worker quá trần CPU chỉ làm latency tăng, vì các worker phải xếp hàng chờ CPU.
- ⚠️ Tổng số worker cũng là tổng số connection tới DB, vì mỗi worker giữ một connection. Nên số
  server × `max_children` phải nhỏ hơn `max_connections` của MySQL
  ([03-database-sql.md](03-database-sql.md) module 2.7).
- Ví dụ tính số server: peak 5.000 QPS, mỗi server 400 QPS, chạy ở 70%:
  1. Mỗi server gánh an toàn 400 × 0,7 = 280 QPS.
  2. 5.000 / 280 ≈ 18 server.
  3. Cộng 1 dự phòng: 19 server.

*Cache*
- Theo quy tắc 80/20 (khoảng 20% dữ liệu nhận 80% lượt đọc), cache khoảng 20% dữ liệu nóng của một
  ngày.

*Ví dụ mẫu: URL shortener*
- Đề: 100 triệu URL mới mỗi tháng, tỉ lệ đọc:ghi = 100:1, lưu 5 năm.
- Các bước:
  1. Ghi: 10^8 / (30 × 10^5) ≈ 40 QPS. Peak ×5 ≈ 200.
  2. Đọc: 4.000 QPS. Peak ≈ 20.000.
  3. Số URL sau 5 năm: 10^8 × 12 × 5 = 6 × 10^9.
  4. Storage: 6 × 10^9 × ~500 byte ≈ 3 TB, chưa tính replica.
  5. Cache: 4.000 × 10^5 = 4 × 10^8 lượt đọc/ngày. 20% × 4 × 10^8 × 500 byte ≈ 40 GB, vừa một cụm
     Redis nhỏ.
- Kết luận: đọc cao, ghi thấp nên cache là trọng tâm. 3 TB chưa cần shard.
- ⚠️ Làm tròn mạnh tay và nói rõ giả định. Mục tiêu là đúng bậc độ lớn, không phải đúng từng số.

**Đọc**
- Alex Xu vol 1, ch.2 *Back-of-the-envelope Estimation* ([bản online](https://bytebytego.com/courses/system-design-interview/back-of-the-envelope-estimation))
- [Latency Numbers Every Programmer Should Know (interactive)](https://colin-scott.github.io/personal_website/research/interactive_latency.html): con số theo năm
- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (`pm`, `pm.max_children`)
- Little's law: module 2.4 của [13-concurrency.md](13-concurrency.md)

**Nắm chắc khi**
- [ ] Ước lượng xong QPS, storage, cache của URL shortener trong 4 phút không cần giấy nháp dài
- [ ] Tính được số server PHP-FPM cho một hệ 3.000 QPS peak khi biết latency, RSS mỗi worker, RAM và số core, và kiểm tra lại với `max_connections`
- [ ] Nói được con số ước lượng nào làm thay đổi thiết kế, con số nào không

#### 1.3 Building blocks và scale từ một server

**Vì sao cần học:** Mọi bài system design đều được ráp từ cùng một bộ khối: load balancer, cache,
DB, queue, object storage. Biết khối nào dùng khi nào, và khi nào **không** nên dùng, là nền của
mọi bài phía sau. Câu "hệ thống một server, traffic tăng 10 lần thì làm gì" là câu mở màn rất phổ
biến.

**Học gì**

*Scale dọc và scale ngang*

| | Scale dọc | Scale ngang |
|---|---|---|
| Làm gì | Máy to hơn: thêm CPU, RAM | Thêm nhiều máy chạy song song |
| Độ phức tạp | Đơn giản, không đổi code | Cần app **stateless** |
| Giới hạn | Có trần: không có máy nào to vô hạn | Gần như không có trần |
| Rủi ro | Vẫn là *SPOF* (*single point of failure*, một chỗ chết là cả hệ thống chết) | Một máy chết, các máy khác gánh |

- *Stateless* nghĩa là không giữ trạng thái quan trọng trên máy app:
  - Session ra Redis.
  - File ra S3.
  - Không để cache local chứa dữ liệu quan trọng.

*Building block và khi nào dùng*

  | Block | Dùng khi | Xem |
  |---|---|---|
  | Load balancer | chia tải, health check, TLS termination. L4 nhanh, L7 route theo path/header. Round robin, least connections, consistent hashing. ⚠️ Sticky session cản scale và failover | [02](02-networking.md) |
  | API gateway | một điểm vào: auth, rate limit, routing, logging | [09](09-api-design.md) |
  | Cache (Redis/Memcached), CDN | đọc nhiều, chịu được stale; file tĩnh, người dùng xa | [11](11-cache.md) |
  | SQL DB | quan hệ, transaction, constraint. **Mặc định nên chọn** | [03](03-database-sql.md) |
  | NoSQL | ghi rất lớn, truy cập theo key biết trước | [04](04-nosql-search-storage.md) |
  | Read replica, sharding | đọc nhiều (⚠️ lag); dữ liệu hoặc ghi vượt một node | [03](03-database-sql.md) |
  | Queue / log (Kafka, RabbitMQ, SQS) | tách việc chậm, làm mượt đỉnh, fan-out sự kiện | [12](12-messaging.md) |
  | Object storage (S3) | file, ảnh, video, backup. ⚠️ Không lưu upload trên đĩa app server | [04](04-nosql-search-storage.md) |
  | Search (Elasticsearch/OpenSearch) | full-text, filter nhiều chiều; không làm nguồn dữ liệu gốc | [04](04-nosql-search-storage.md) |
  | Stream processing (Flink, Kafka Streams) | tổng hợp real-time, window, gian lận | [12](12-messaging.md) |
  | 🔴 Consistent hashing | thêm/bớt node chỉ dời ~1/N key; virtual node để chia đều | [14](14-distributed-systems.md) |
  | 🔴 Bloom filter | "chắc chắn không có" rất rẻ; có false positive, không false negative; bản chuẩn không xoá được | [21](21-dsa.md) |
  | 🔴 Geo index | tìm điểm gần nhất (module 3.6) | |

- Giải nghĩa các từ trong bảng:
  - *Health check*: load balancer định kỳ gọi thử từng máy, máy không trả lời thì ngừng gửi
    request tới.
  - *TLS termination*: giải mã HTTPS ngay ở load balancer, phía sau đi HTTP thường.
  - *L4* chia tải theo kết nối TCP, không nhìn nội dung. *L7* đọc được HTTP nên route được theo
    path, header.
  - *Round robin* chia lần lượt. *Least connections* chọn máy đang ít kết nối nhất.
  - *Sticky session*: một user luôn được gửi về cùng một máy. Là cách chữa cháy cho app chưa
    stateless, và làm mất cân bằng tải khi scale hay khi một máy chết.
  - *CDN*: mạng máy chủ đặt gần người dùng, giữ bản sao file tĩnh.
  - *Stale*: dữ liệu cũ hơn bản gốc một chút.
  - *Read replica*: bản sao của DB chỉ để đọc. *Lag* là độ trễ giữa lúc ghi vào primary và lúc
    replica thấy.
  - *Sharding*: chia dữ liệu ra nhiều DB, mỗi DB giữ một phần.
  - *Fan-out*: một sự kiện được gửi tới nhiều nơi nhận.
  - *Consistent hashing*: cách gán key vào node sao cho thêm hay bớt một node chỉ phải dời khoảng
    1/N số key. *Virtual node*: mỗi node thật đứng ở nhiều vị trí để chia tải đều hơn.
  - *Bloom filter*: cấu trúc rất gọn để hỏi "phần tử này có trong tập không". Trả lời "không" thì
    chắc chắn không có. Trả lời "có" thì có thể sai (*false positive*).

*Bài "một server, traffic tăng 10 lần"* 🟢
- Làm theo thứ tự, mỗi bước kèm "đo gì để biết cần bước tiếp":
  1. Đo nút thắt: CPU app, DB hay mạng. Kiểm tra đã có *APM* (công cụ đo hiệu năng từng request,
     như New Relic, Datadog) chưa.
  2. Tách DB ra máy riêng. Tối ưu query và index, thường là bước rẻ và lợi nhất.
  3. Cache cho dữ liệu đọc nhiều. CDN cho file tĩnh.
  4. App stateless, đặt load balancer trước nhiều instance.
  5. Việc chậm đưa vào queue, worker xử lý nền.
  6. Read replica, tách đường đọc và đường ghi.
  7. Ghi vượt một node: partition hoặc shard, hoặc chuyển một phần dữ liệu sang store phù hợp hơn.
  8. Suốt quá trình: monitoring, alert, load test, loại bỏ SPOF.

**Đọc**
- Alex Xu vol 1, ch.1 *Scale from Zero to Millions of Users* ([bản online](https://bytebytego.com/courses/system-design-interview/scale-from-zero-to-millions-of-users))
- System Design Primer: các mục *Load balancer*, *Cache*, *Database*, *Asynchronism*
- Laravel: [Session drivers](https://laravel.com/docs/session), [File Storage](https://laravel.com/docs/filesystem) (để app stateless)

**Nắm chắc khi**
- [ ] Trả lời được bài "traffic tăng 10 lần" theo 8 bước, mỗi bước nói được chỉ số nào cho thấy cần bước đó
- [ ] Với mỗi block trong bảng, nói được một trường hợp **không** nên dùng

#### 1.4 Availability

**Vì sao cần học:** Con số "99,9%" xuất hiện trong mọi SLA và mọi cuộc bàn về kiến trúc, nhưng ít
người đổi được nó ra số phút downtime hay biết mỗi số 9 thêm vào tốn gì. Câu hỏi hay gặp: "99,9%
là bao nhiêu phút mỗi tháng" (junior) và "cần 99,99% thì bạn thay đổi gì" (senior).

**Học gì**

*Bảng số 9*
- *Availability* là tỉ lệ thời gian hệ thống phục vụ được.

  | Availability | Downtime/năm | Downtime/tháng (30 ngày) |
  |---|---|---|
  | 99% | ~3,65 ngày | ~7,2 giờ |
  | 99,9% | ~8,76 giờ | ~43,2 phút |
  | 99,99% | ~52,6 phút | ~4,3 phút |
  | 99,999% | ~5,26 phút | ~26 giây |

- Mỗi số 9 thêm vào đắt hơn nhiều:
  - *Failover* (chuyển sang bản dự phòng) phải tự động, vì con người không phản ứng kịp trong 4
    phút.
  - Phải chạy multi-AZ (xem dưới).
  - Deploy phải an toàn, vì phần lớn sự cố đến từ thay đổi.

*Tính availability của nhiều thành phần*
- Nối tiếp (A gọi B gọi C, một cái chết là cả chuỗi chết): **nhân** các availability.
  - Ví dụ: 3 thành phần 99,9% → 0,999³ ≈ 99,7%.
- Song song dự phòng (hai bản, còn một bản sống là được): 1 − (xác suất cả hai cùng chết).
  - Ví dụ: hai bản 99% → 1 − 0,01² = 99,99%.
  - ⚠️ Chỉ đúng khi hai bản hỏng thật sự độc lập. Thực tế thường không: cùng một bản deploy lỗi,
    cùng một nguồn điện, cùng một config.

*SPOF và redundancy*
- SPOF hay bị bỏ quên:
  - DB primary.
  - Một load balancer duy nhất.
  - Một Redis duy nhất.
  - Một server chạy cron.
  - Một nhà cung cấp DNS.
  - Một người duy nhất biết cách deploy.
- *Redundancy* là có thêm bản dự phòng:
  - N+1: thêm một bản.
  - N+2: thêm hai bản, để vẫn an toàn khi một máy đang bảo trì và một máy khác chết.

*Active-passive và active-active*

| | Active-passive | Active-active |
|---|---|---|
| Cách chạy | Một bản phục vụ, một bản chờ | Cả hai cùng phục vụ |
| Failover | Chậm hơn, phải promote bản chờ | Nhanh, bản kia đang chạy sẵn |
| Tài nguyên | Bản chờ lãng phí lúc bình thường | Dùng hết, nhưng mỗi bản phải chịu được **toàn bộ tải** khi bản kia chết |
| ⚠️ Rủi ro | *Split brain* khi promote: cả hai bản cùng tưởng mình là chính và cùng nhận ghi | Ghi ở nhiều nơi thì xung đột dữ liệu |

*AZ và region*
- *AZ* (*Availability Zone*) là một hoặc vài datacenter độc lập về điện và mạng trong cùng một
  vùng. *Region* là một vùng địa lý gồm nhiều AZ, ví dụ Singapore.
- **Multi-AZ là mặc định cho production.** Các AZ gần nhau nên replication đồng bộ được, tức ghi
  xong ở cả hai nơi mới báo thành công.
- Multi-region:
  - Lợi: chống mất cả một vùng, và gần người dùng hơn.
  - Giá: các region xa nhau nên replication phải bất đồng bộ. Vì vậy *RPO* (lượng dữ liệu có thể
    mất khi sự cố) lớn hơn 0.
  - Mô hình phổ biến: đọc ở mọi region, ghi về một region chính. Hoặc mỗi user có một "home
    region" để ghi.
- *Static stability*: khi một AZ chết, các AZ còn lại **đã có sẵn** đủ công suất. Không phụ thuộc
  vào việc autoscaling kịp tạo thêm máy lúc sự cố.

**Đọc**
- Google SRE: [Embracing Risk](https://sre.google/sre-book/embracing-risk/), [Availability Table](https://sre.google/sre-book/availability-table/)
- Amazon Builders' Library: [Static stability using Availability Zones](https://aws.amazon.com/builders-library/static-stability-using-availability-zones/)
- [18-reliability-observability.md](18-reliability-observability.md) (SLO, RPO/RTO, DR)

**Nắm chắc khi**
- [ ] Tính được availability của một chuỗi LB → app → Redis → MySQL với số liệu tự giả định, và chỉ ra chỗ nên thêm dự phòng
- [ ] Liệt kê được mọi SPOF trong hệ thống mình đang làm

---

### Chặng 2: Làm chủ 🟡

#### 2.1 URL shortener

**Vì sao cần học:** URL shortener là bài nhập môn kinh điển, gần như chắc gặp ở vòng mid. Bài nhỏ
nhưng có đủ các ý người chấm muốn thấy: ước lượng dẫn tới quyết định, cách sinh mã không trùng,
và hiểu hệ quả của một chi tiết HTTP (`301` hay `302`).

**Học gì**

*Ước lượng, API và data model*
- Ước lượng dẫn tới kết luận: đọc gấp 100 lần ghi → **cache là trọng tâm**. 3 TB chưa cần shard
  (module 1.2).
- API:
  - `POST /urls`: tạo mã rút gọn.
  - `GET /{code}`: chuyển hướng tới URL gốc.
- Data model: `urls(code PK, long_url, user_id, created_at, expire_at)`.

*Độ dài mã*
- *Base62* là cách viết số bằng 62 ký tự: `0-9`, `a-z`, `A-Z`.
- Mã 7 ký tự cho 62^7 ≈ 3,5 × 10^12 mã, dư nhiều cho 6 × 10^9 URL trong 5 năm.

*Sinh mã (deep dive chính)*

| Cách | Làm thế nào | Ưu | Nhược |
|---|---|---|---|
| ID tăng dần → base62 | ID tự tăng của DB hoặc Snowflake (module 3.3), đổi sang base62 | Không bao giờ trùng | Đoán được mã kế tiếp |
| Hash URL | Hash URL gốc, lấy 7 ký tự đầu | Cùng URL ra cùng mã | Có thể trùng, phải thử lại |
| Random | Sinh 7 ký tự ngẫu nhiên | Không đoán được | Phải kiểm tra trùng |
| Key service | Một service sinh sẵn các lô mã chưa dùng, phát cho app server | Nhanh lúc tạo | Thêm một thành phần phải vận hành |

- ⚠️ Kiểm tra trùng bằng `INSERT` với unique constraint rồi bắt lỗi, không "SELECT xem có chưa
  rồi INSERT". Hai request cùng lúc có thể cùng thấy "chưa có".

*Redirect: 301 hay 302*

| | `301` | `302` / `307` |
|---|---|---|
| Nghĩa | Chuyển vĩnh viễn | Chuyển tạm thời |
| Browser cache | Có, lần sau browser tự chuyển không hỏi server | Không, lần nào cũng hỏi server |
| Tải lên server | Giảm | Không giảm |
| Thống kê click | **Mất**, vì server không thấy các lần sau | Thống kê được |

*Đường redirect phải nhẹ*
- Click event đi qua queue bất đồng bộ. Không ghi DB ngay trong đường redirect.
- Cache cả kết quả "mã không tồn tại", để kẻ dò mã không đánh thẳng xuống DB.

*Hỏi tiếp hay gặp*
- Custom alias (người dùng tự chọn mã).
- Chặn URL độc hại.
- Dọn URL hết hạn.
- Rate limit việc tạo URL.

**Đọc**
- Alex Xu vol 1, ch.8 *Design a URL Shortener* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-url-shortener))

**Nắm chắc khi**
- [ ] Làm trọn bài trong 45 phút và bảo vệ được cách sinh mã đã chọn
- [ ] Trả lời được "traffic đọc tăng 100 lần" mà không phải vẽ lại từ đầu (câu 21)

#### 2.2 Rate limiter

**Vì sao cần học:** Rate limiter vừa là bài phỏng vấn phổ biến vừa là thứ bạn cấu hình thật trong
Laravel (`throttle`). Bài này kiểm tra bạn có hiểu race condition trên Redis không, và biết đánh
đổi giữa độ chính xác và bộ nhớ của từng thuật toán.

**Học gì**

*Các thuật toán*
- *Rate limiter* giới hạn số request một client được gửi trong một khoảng thời gian, ví dụ 100
  request mỗi phút cho mỗi API key.

| Thuật toán | Cách hoạt động | Ưu | ⚠️ Nhược |
|---|---|---|---|
| Token bucket | Xô chứa tối đa N token, được nạp đều đặn. Mỗi request lấy một token, hết token thì bị từ chối | Cho phép burst (dồn nhiều request một lúc) tới N. Phổ biến nhất | Phải lưu hai giá trị: số token và lần nạp cuối |
| Leaky bucket | Request vào hàng đợi, được xử lý ra với tốc độ đều | Output đều | Burst phải chờ |
| Fixed window | Đếm theo từng cửa sổ cố định, ví dụ từng phút tròn | Đơn giản, rẻ | Ở ranh giới hai cửa sổ có thể lọt gấp đôi limit |
| Sliding window log | Lưu thời điểm của từng request, đếm trong 60 giây gần nhất | Chính xác | Tốn bộ nhớ |
| Sliding window counter | Ước lượng từ bộ đếm cửa sổ hiện tại và cửa sổ trước, có trọng số | Xấp xỉ tốt, rẻ | Không chính xác tuyệt đối |

- Ví dụ bẫy fixed window: limit 100/phút.
  1. 100 request lúc 00:59.
  2. 100 request lúc 01:00, đã sang cửa sổ mới nên bộ đếm về 0.
  3. Kết quả: 200 request lọt qua trong khoảng 2 giây.

*Đặt ở đâu*
- Ở gateway hoặc edge, ở middleware của app, hoặc cả hai.
- Rate limit ở phía client không tin được, vì client tự sửa được.

*Counter trong Redis phải atomic*
- ⚠️ `GET` rồi `SET` từ app là race condition: hai request cùng đọc 99, cùng ghi 100, cả hai đều
  lọt.
- Cách đúng:
  - Fixed window: `INCR` rồi `EXPIRE`. `INCR` là atomic.
  - Token bucket: viết bằng Lua script. Redis chạy trọn một script mà không xen lệnh khác vào.

*Response khi bị chặn*
- Trả `429 Too Many Requests` kèm header `Retry-After` (bao lâu nữa thì thử lại).
- Header `RateLimit` và `RateLimit-Policy` theo draft của IETF, chưa thành RFC. Nhiều nơi vẫn dùng
  `X-RateLimit-*`.

*Deep dive*
- Redis chết thì làm gì:
  - *Fail-open*: cho qua hết, có thể kèm limit local trên từng máy.
  - *Fail-closed*: chặn hết.
- Mỗi request tốn thêm một round trip tới Redis.
- Multi-region: chia quota giữa các region thế nào.
- Hot key: một API key rất lớn dồn toàn bộ counter lên một node Redis.

*Góc Laravel*
- Định nghĩa bằng `RateLimiter::for()`, gắn middleware `throttle`. Counter lưu trong cache driver.

**Đọc**
- Alex Xu vol 1, ch.4 *Design a Rate Limiter* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-rate-limiter))
- Stripe: [Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters); Cloudflare: [How we built rate limiting capable of scaling to millions of domains](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/) (sliding window counter)
- IETF: [RateLimit header fields draft](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/)
- Laravel: [Rate Limiting](https://laravel.com/docs/rate-limiting), [Route rate limiting](https://laravel.com/docs/routing#rate-limiting)

**Nắm chắc khi**
- [ ] Viết được Lua token bucket cho Redis (bài tập 3)
- [ ] Vẽ được ví dụ fixed window cho qua gấp đôi limit trong 2 giây quanh ranh giới

#### 2.3 Notification system

**Vì sao cần học:** Hệ nào cũng gửi email, SMS, push, và ở PHP đây là việc chạy queue nhiều nhất.
Hai sự cố hay gặp là gửi trùng cho khách và OTP đến chậm vì bị kẹt sau một campaign marketing.
Bài này kiểm tra bạn thiết kế queue, retry và chống trùng có bài bản không.

**Học gì**

*Yêu cầu*
- Kênh: email, SMS, push (qua APNs của Apple và FCM của Google), in-app.
- Gửi ngay và gửi theo lịch.
- Template cho nội dung.
- *Preference* của người dùng: tắt từng kênh, giờ yên lặng theo timezone của họ.

*Vì sao queue là bắt buộc*
- 10 triệu push mỗi ngày ≈ 120 mỗi giây trung bình, nghe nhỏ.
- Nhưng một campaign dồn hàng triệu tin trong vài phút. Không có queue thì app và provider đều
  quá tải.
- Queue riêng cho từng kênh: provider SMS chậm không chặn email.

*Chống gửi trùng*
- Queue thường là *at-least-once*: mỗi message được giao ít nhất một lần, có thể nhiều hơn.
- ⚠️ Vì vậy cần *idempotency key*, ví dụ `event_id + user_id + channel`, và kiểm tra bằng một
  trong hai cách:
  - Unique constraint trong DB.
  - Redis `SET NX` có TTL (chỉ set được nếu key chưa tồn tại).

*Ưu tiên*
- ⚠️ OTP và thông báo giao dịch đi queue riêng. Campaign không được làm chậm OTP.

*Retry, DLQ, rate limit*
- Retry có *backoff*: lần sau chờ lâu hơn lần trước.
- *DLQ* (*dead letter queue*) cho lỗi vĩnh viễn. Ví dụ token push hết hạn thì xoá token, không
  retry mãi.
- Rate limit theo user (không spam một người) và theo quota của provider.

*Góc Laravel*
- Notification hỗ trợ nhiều channel.
- Implement `ShouldQueue` để gửi qua queue.
- Tách queue theo kênh.

**Đọc**
- Alex Xu vol 1, ch.10 *Design a Notification System*
- Laravel: [Notifications](https://laravel.com/docs/notifications) (mục queueing notifications)

**Nắm chắc khi**
- [ ] Vẽ được luồng từ service nghiệp vụ tới provider, chỉ ra chỗ dedup và chỗ ưu tiên OTP
- [ ] Nói được chuyện gì xảy ra khi worker gửi xong nhưng chết trước khi ghi "đã gửi"

#### 2.4 News feed

**Vì sao cần học:** News feed là bài kinh điển để nói về đánh đổi giữa chi phí ghi và chi phí
đọc. Câu hỏi then chốt luôn là "người có 10 triệu follower đăng bài thì sao". Ý tưởng "cache chỉ
lưu id" dùng lại được ở rất nhiều hệ khác.

**Học gì**

*Ước lượng*
- 100 triệu DAU × 10 lần mở feed → 10^9 / 10^5 = 10.000 QPS đọc.
- 0,1 bài/người/ngày → khoảng 100 QPS ghi.

*Fan-out on write và fan-out on read*

| | Fan-out on write (push) | Fan-out on read (pull) |
|---|---|---|
| Cách làm | Khi A đăng bài, ghi id bài vào feed của từng follower | Khi B mở feed, đi lấy bài mới của mọi người B follow rồi trộn |
| Đọc | Rất nhanh, feed có sẵn | Chậm, phải merge nhiều nguồn |
| Ghi | Đắt: ⚠️ người nổi tiếng 10 triệu follower = 10 triệu lần ghi | Rẻ, chỉ ghi một bài |

- **Hybrid**:
  - Người thường: push.
  - Người nổi tiếng: pull, rồi merge vào lúc đọc.
  - Không push cho user đã lâu không hoạt động.

*Feed cache chỉ lưu id*
- Feed cache chỉ lưu **post id**. Nội dung được *hydrate* (lấy nội dung đầy đủ theo id) từ post
  cache lúc đọc.
- Lợi: sửa hay xoá bài không phải sửa hàng triệu feed.
- Xoá bài thì lọc bỏ lúc đọc.

*Phân trang*
- Dùng *cursor pagination* ("cho tôi 20 bài cũ hơn bài id X"), không dùng offset. Offset vừa chậm
  ở trang sâu, vừa bị lặp hoặc sót bài khi có bài mới chen vào.

*Hỏi tiếp hay gặp*
- Ranking (sắp theo độ liên quan thay vì thời gian).
- Counter like xấp xỉ.
- Media qua object storage và CDN.
- Feed real-time.

**Đọc**
- Alex Xu vol 1, ch.11 *Design a News Feed System* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-news-feed-system))
- Facebook: [TAO: The power of the graph](https://engineering.fb.com/2013/06/25/core-infra/tao-the-power-of-the-graph/) (lưu và cache đồ thị xã hội)

**Nắm chắc khi**
- [ ] Tính được số lần ghi khi một người 10 triệu follower đăng bài theo push, và thiết kế ngưỡng hybrid
- [ ] Giải thích được vì sao feed cache chỉ nên lưu id

#### 2.5 Chat / messenger

**Vì sao cần học:** Chat là bài về kết nối lâu dài (*stateful*), thứ tự tin nhắn và giao tin tin
cậy, khác hẳn kiểu request/response quen thuộc của PHP. Với dev PHP, bài này còn kiểm tra bạn có
biết giới hạn của PHP-FPM và cách Laravel làm real-time không.

**Học gì**

*Ước lượng*
- 50 triệu DAU × 40 tin → 2 × 10^9 tin/ngày ≈ 20.000 tin/giây.
- 100 byte/tin → 200 GB/ngày. Storage ghi nhiều, cần scale ngang.

*Kết nối*
- *WebSocket* là kết nối hai chiều giữ mở lâu giữa client và server. Server đẩy tin xuống được
  bất kỳ lúc nào.
- Hệ quả: chat server là stateful, không hoàn toàn stateless, vì nó giữ kết nối của những user cụ
  thể.
- *Session registry*: bảng `user_id → chat server đang giữ kết nối` trong Redis.
- Chuyển tin giữa các chat server qua *pub/sub* (một bên publish, các bên đã subscribe đều nhận).

*Lưu trữ*
- Partition theo `conversation_id`, trong mỗi partition sắp theo `message_id`.
- Chọn store: Cassandra hoặc ScyllaDB, hoặc SQL shard theo conversation.

*Thứ tự và giao tin tin cậy*
- ⚠️ Không dựa vào đồng hồ của client để sắp thứ tự. Dùng sequence tăng dần theo từng conversation,
  hoặc id có chứa thời gian do server sinh.
- Giao tin tin cậy:
  1. Client gắn `client_msg_id` cho mỗi tin, để server bỏ tin trùng khi client retry.
  2. Server lưu tin xong mới gửi *ack* (xác nhận đã nhận) cho người gửi.
  3. Người nhận giữ `last_seen_message_id`. Khi reconnect thì xin mọi tin sau id đó.

*Nhóm và presence*
- Nhóm nhỏ: fan-out tin tới từng thành viên. Kênh rất lớn: thành viên tự kéo về.
- *Presence* (đang online hay không) dùng heartbeat: client gửi tín hiệu định kỳ, lâu không thấy
  thì coi là offline.
- ⚠️ Không broadcast thay đổi presence cho mọi bạn bè. Một người có 1.000 bạn online/offline liên
  tục sẽ sinh bão message.

*Vận hành*
- Một user có nhiều thiết bị.
- Deploy phải *drain* kết nối: ngừng nhận kết nối mới, chờ hoặc chuyển dần kết nối cũ.
- Có E2E encryption (mã hoá đầu cuối) thì server không đọc được nội dung, nên không search phía
  server được.

*Góc PHP*
- PHP-FPM không giữ được WebSocket, vì mỗi worker xử lý xong một request là trả về.
- Dùng Laravel Reverb hoặc một server WebSocket riêng. Code PHP chỉ publish sự kiện.

**Đọc**
- Alex Xu vol 1, ch.12 *Design a Chat System* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-chat-system))
- Discord: [How Discord Stores Trillions of Messages](https://discord.com/blog/how-discord-stores-trillions-of-messages) (Cassandra sang ScyllaDB, partition theo channel và bucket thời gian)
- Slack: [Real-time Messaging](https://slack.engineering/real-time-messaging/)
- Laravel: [Broadcasting](https://laravel.com/docs/broadcasting), [Reverb](https://laravel.com/docs/reverb)

**Nắm chắc khi**
- [ ] Vẽ được đường đi một tin từ A (server 1) tới B (server 2) và tới B khi offline
- [ ] Xử lý được tình huống một chat server chết làm 50.000 kết nối rớt cùng lúc (câu 25)

#### 2.6 Đặt vé / đặt phòng

**Vì sao cần học:** Double booking là lỗi tiền thật và khách thật: hai người cùng mua một ghế.
Bài này kiểm tra bạn có viết được thao tác "kiểm tra và giữ" nguyên tử ngay trong DB không, thay
vì kiểm tra ở app rồi mới ghi. Đây cũng là nền của flash sale (module 3.2).

**Học gì**

*Hai kiểu tồn kho*
- Chỗ cụ thể: mỗi ghế một dòng, ví dụ ghế G12 của suất chiếu 20h.
- Theo số lượng: một dòng đếm cho mỗi loại phòng mỗi ngày, ví dụ "phòng Deluxe ngày 01/05 còn 3".

*Không double booking*
- Dùng một câu *conditional update* (UPDATE có điều kiện) nguyên tử, rồi kiểm tra *affected rows*
  (số dòng thật sự bị sửa):

  ```sql
  UPDATE seats SET status = 'HELD', hold_id = ?, hold_until = NOW() + INTERVAL 10 MINUTE
  WHERE show_id = ? AND seat_no = ?
    AND (status = 'AVAILABLE' OR (status = 'HELD' AND hold_until < NOW()));

  UPDATE room_inventory SET reserved = reserved + 1
  WHERE room_type_id = ? AND date = ? AND reserved < total;
  ```

  - Affected rows = 1: giữ được.
  - Affected rows = 0: đã có người khác giữ, báo hết.
- ⚠️ *Check-then-act* ở app (SELECT thấy còn, rồi UPDATE) là race: hai request cùng thấy còn.
- Đặt nhiều đêm hoặc nhiều ghế: làm trong một transaction, và khoá theo một thứ tự cố định (ví dụ
  theo ngày tăng dần) để tránh deadlock.

*Giữ chỗ tạm*
- Trạng thái đi theo `AVAILABLE → HELD → BOOKED`.
- Hạn giữ được kiểm tra ngay trong `WHERE` (`hold_until < NOW()`). Vì vậy tính đúng không phụ thuộc
  vào job dọn hold hết hạn. Job dọn chỉ để dữ liệu gọn.
- ⚠️ Thanh toán về **sau** khi hold đã hết hạn và ghế đã bán cho người khác. Hai cách xử lý:
  - Quy trình hoàn tiền tự động.
  - Gia hạn hold khi người dùng đã vào bước thanh toán.

*Lúc mở bán*
- *Waiting room*: xếp hàng người dùng trước khi cho vào trang chọn ghế.
- Cache sơ đồ ghế để hiển thị: có thể hơi cũ, nhưng lệnh ghi luôn kiểm tra ở DB.
- Rate limit.

*Hỏi tiếp hay gặp*
- Overbooking có chủ đích (khách sạn bán vượt vì biết có tỉ lệ huỷ).
- Đồng bộ tồn kho với OTA (các sàn đặt phòng như Booking, Agoda).
- Huỷ và hoàn tiền.

**Đọc**
- Alex Xu vol 2, ch.7 *Hotel Reservation System* ([bản online](https://bytebytego.com/courses/system-design-interview/hotel-reservation-system))
- Module 1.4 của [13-concurrency.md](13-concurrency.md), module 2.6 của [03-database-sql.md](03-database-sql.md)

**Nắm chắc khi**
- [ ] Viết được câu UPDATE giữ ghế và giải thích vì sao không cần job dọn hold để đảm bảo đúng
- [ ] Mô tả được luồng xử lý thanh toán về muộn (bài tập 5)

#### 2.7 Leaderboard

**Vì sao cần học:** Leaderboard là bài ngắn để kiểm tra bạn có biết dùng đúng cấu trúc dữ liệu của
Redis không. Sorted set còn dùng cho rất nhiều việc khác như xếp hạng bài viết hay hàng đợi có
độ ưu tiên.

**Học gì**

*Redis sorted set*
- *Sorted set* là tập các phần tử, mỗi phần tử có một điểm (*score*), luôn được giữ sắp theo điểm.
- Các lệnh cần nhớ:
  - Cập nhật điểm: `ZADD` (đặt điểm), `ZINCRBY` (cộng điểm).
  - Top 10: `ZRANGE key 0 9 REV WITHSCORES`.
  - Hạng của một user: `ZREVRANK`.
  - Các thao tác này là O(log N).
- ⚠️ `ZREVRANGE` đã deprecated từ Redis 6.2. Thay bằng `ZRANGE ... REV`.

*Hạng bằng nhau*
- Mã hoá cả điểm và thời điểm đạt điểm vào cùng một score, để ai đạt trước xếp trên.

*Theo kỳ*
- Leaderboard theo tuần hay tháng: mỗi kỳ một key, đặt TTL sau khi kỳ kết thúc.

*Nguồn sự thật*
- DB là nguồn sự thật. Redis mất thì dựng lại được từ DB.

*Quy mô rất lớn*
- Chia theo khoảng điểm hoặc shard.
- Hạng chính xác cho nhóm top. Phần còn lại chỉ cần *percentile* xấp xỉ ("bạn nằm trong top 15%").
- ⚠️ Lấy top-N khi dữ liệu nằm ở nhiều shard: lấy top-N của **từng** shard rồi merge lại.

**Đọc**
- Alex Xu vol 2, ch.10 *Real-time Gaming Leaderboard* ([bản online](https://bytebytego.com/courses/system-design-interview/real-time-gaming-leaderboard))
- Redis: [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/), [ZRANGE](https://redis.io/docs/latest/commands/zrange/)

**Nắm chắc khi**
- [ ] Viết được các lệnh Redis cho: cộng điểm, top 10, hạng của một user, leaderboard theo tuần
- [ ] Thiết kế được cách phá hoà bằng thời điểm trong một score kiểu double

---

### Chặng 3: Senior 🔴

#### 3.1 Thanh toán / ví điện tử

**Vì sao cần học:** Bài có tiền là nơi người chấm senior soi kỹ nhất, vì sai một chút là mất tiền
thật hoặc trừ tiền khách hai lần. Điểm then chốt không nằm ở chọn công nghệ mà ở ledger,
idempotency và cách xử lý khi không biết giao dịch thành công hay chưa. Red flag kinh điển: chỉ
có một cột `balance` và `UPDATE`.

**Học gì**

*Nguyên tắc và ledger bút toán kép*
- Đúng quan trọng hơn nhanh.
- Tiền lưu bằng số nguyên theo đơn vị nhỏ nhất, hoặc `DECIMAL`. ⚠️ Không dùng `float`
  ([22-practical-data.md](22-practical-data.md)).
- *Ledger* là sổ cái ghi mọi biến động tiền. *Bút toán kép* (*double-entry*) nghĩa là:
  - Mỗi giao dịch có ít nhất hai *entry* (dòng ghi): một bên ghi nợ (*debit*), một bên ghi có
    (*credit*).
  - Tổng debit luôn bằng tổng credit.
  - Ví dụ: A chuyển 100.000đ cho B thì có một entry −100.000 ở ví A và một entry +100.000 ở ví B.
- Entry là **append-only**: chỉ thêm, không sửa, không xoá. Ghi sai thì thêm một entry đảo ngược.
- Cột `balance` chỉ là cache của ledger, tính lại được từ các entry.

*Chuyển tiền nội bộ*
- Một transaction DB gồm:
  1. Tạo một dòng trong bảng `transactions`.
  2. Ghi hai entry.
  3. Cập nhật balance có điều kiện `balance >= amount`. Hoặc dùng `SELECT ... FOR UPDATE` khoá hai
     ví theo thứ tự id tăng dần để tránh deadlock.

*Idempotency ở mọi tầng*
- Client gửi header `Idempotency-Key`.
- Server lưu key với unique constraint, và trạng thái `PROCESSING` để request trùng đến trong lúc
  đang xử lý không chạy song song.
- Truyền key đó sang *PSP* (*payment service provider*, bên xử lý thanh toán như Stripe, VNPay).

*Luồng với PSP*
- Trạng thái: `CREATED → PENDING → SUCCEEDED/FAILED`, và có thêm `UNKNOWN`.
- ⚠️ Timeout khi gọi PSP **không phải là thất bại**. Tiền có thể đã bị trừ ở phía PSP. Cách xử lý:
  1. Đặt giao dịch về `UNKNOWN`. Không tạo giao dịch mới.
  2. Query trạng thái ở PSP bằng cùng mã giao dịch, hoặc chờ webhook.

*Webhook*
- *Webhook* là PSP gọi ngược vào server của bạn để báo kết quả.
- Xác thực chữ ký, để chắc là PSP gọi chứ không phải kẻ giả mạo.
- Xử lý idempotent: webhook có thể đến nhiều lần và sai thứ tự.
- Trả 2xx thật nhanh rồi xử lý qua queue.
- Event "đã thanh toán" gửi đi qua outbox (ghi event trong cùng transaction với dữ liệu,
  [12-messaging.md](12-messaging.md)).

*Reconciliation*
- *Reconciliation* (đối soát) chạy hằng ngày: so dữ liệu của mình với file của PSP và sao kê ngân
  hàng.
- Lệch thì tạo case để người xử lý. Không âm thầm sửa số dư.
- Kiểm tra tổng các entry bằng 0 theo từng loại tiền.

*Hot account*
- *Hot account*: một ví nhận rất nhiều giao dịch cùng lúc, ví dụ ví của merchant lớn. Mọi giao
  dịch tranh nhau khoá một dòng balance.
- Cách xử lý:
  - Chia thành nhiều sub-account.
  - Gom nhiều giao dịch rồi ghi một lần.
  - Cập nhật balance bất đồng bộ từ ledger.

**Đọc**
- Alex Xu vol 2, ch.11 *Payment System* và ch.12 *Digital Wallet*
- Stripe: [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency)
- Modern Treasury: [Accounting for Developers, Part I](https://www.moderntreasury.com/journal/accounting-for-developers-part-i) (bút toán kép cho developer)
- [Brandur: Idempotency Keys](https://brandur.org/idempotency-keys)

**Nắm chắc khi**
- [ ] Thiết kế được schema ledger và câu SQL kiểm tra ledger cân bằng (bài tập 4)
- [ ] Kể được từng bước xử lý khi gọi PSP bị timeout, tới lúc tiền được xác nhận hoặc hoàn

#### 3.2 Flash sale

**Vì sao cần học:** Flash sale là bài gộp của rate limit, cache, queue và chống oversell dưới tải
cực đỉnh. Các sàn thương mại điện tử ở Việt Nam chạy flash sale thường xuyên, và sự cố "bán vượt
số lượng" là câu hỏi tình huống rất hay gặp.

**Học gì**

*Mục tiêu: từ chối rẻ*
- Traffic tăng hàng trăm lần trong vài giây, nhưng chỉ 1.000 đơn thành công. Tuyệt đại đa số
  request sẽ bị từ chối.
- Vì vậy mục tiêu là **từ chối càng rẻ và càng sớm càng tốt**, trước khi request chạm tới DB.

*Các tầng lọc*
1. Client: nút bị disable tới đúng giờ, captcha.
2. CDN: phục vụ trang tĩnh.
3. Gateway: rate limit, chặn bot.
4. Waiting room: xếp hàng người dùng.
5. Flash sale service.

*Trừ kho*
1. Trừ kho nguyên tử trong Redis bằng Lua script: kiểm tra `stock > 0` và user chưa mua, rồi
   `DECR`.
2. Thành công thì đẩy vào queue.
3. Worker tạo đơn trong DB.

*DB vẫn là nguồn sự thật*
- Worker ghi đơn bằng conditional update (module 2.6).
- Hai trường hợp lệch:
  - Redis thấp hơn thật: bán thiếu. Chấp nhận được.
  - Redis cao hơn thật: DB chặn, không oversell.
- Người dùng không thanh toán trong hạn: trả kho ở cả Redis và DB.

*Cô lập và chuẩn bị*
- Chạy flash sale trên cluster hoặc pool riêng, để luồng mua hàng thường không chết theo.
- Scale **trước** giờ mở bán. Autoscaling không kịp một đỉnh tính bằng giây.
- Load test ở quy mô thật.
- Hot key tồn kho: chia tồn kho thành nhiều bucket nằm trên nhiều node Redis.

**Đọc**
- Shopify: [Surviving Flashes of High-Write Traffic Using Scriptable Load Balancers](https://shopify.engineering/surviving-flashes-of-high-write-traffic-using-scriptable-load-balancers-part-i)
- Module 3.4 của [13-concurrency.md](13-concurrency.md)

**Nắm chắc khi**
- [ ] Vẽ được các tầng lọc và ước lượng số request còn lại sau mỗi tầng cho 1 triệu người
- [ ] Điều tra được sự cố "bán 1.012 trên 1.000" (câu 24)

#### 3.3 Distributed ID generator và key-value store

**Vì sao cần học:** Hai bài hạ tầng này hay xuất hiện ở vòng senior vì chúng buộc bạn nói về các
khái niệm của hệ phân tán: phân vùng, replication, quorum, xung đột. Snowflake và UUIDv7 cũng là
lựa chọn thật khi thiết kế primary key cho hệ nhiều service.

**Học gì**

*Distributed ID*

| Cách | Mô tả | ⚠️ Lưu ý |
|---|---|---|
| Auto-increment | DB cấp id tăng dần | Một DB là SPOF và nút thắt ghi |
| Nhiều DB bước nhảy khác nhau | DB 1 cấp 1, 3, 5...; DB 2 cấp 2, 4, 6... | Khó thêm DB |
| UUIDv4 | 128 bit ngẫu nhiên | Phân mảnh B+tree khi làm primary key |
| UUIDv7 | 128 bit, phần đầu là thời gian | Tăng dần nên insert tốt |
| Snowflake | 64 bit: `1 \| 41 bit ms \| 10 bit machine \| 12 bit sequence` | Phụ thuộc đồng hồ |
| Segment allocation | Service lấy từ DB một khoảng id (ví dụ 1.000 id) rồi cấp dần | Id không liên tục khi service khởi động lại |

- Snowflake:
  - 41 bit ms đủ dùng khoảng 69 năm.
  - 12 bit sequence cho 4.096 id mỗi ms mỗi máy.
  - 10 bit machine cho 1.024 máy.
  - ⚠️ Đồng hồ chạy lùi (ví dụ sau khi đồng bộ NTP) có thể sinh id trùng. Phải phát hiện và chờ
    hoặc từ chối.
  - Machine id gán bằng config, hoặc xin từ ZooKeeper, etcd hay DB.
- Chi tiết ở module 2.7 của [14](14-distributed-systems.md).

*Key-value store (hướng Dynamo/Cassandra)*
- Partition:
  - Dùng consistent hashing kèm virtual node (module 1.3).
  - Mỗi key lưu ở N node kế tiếp nhau trên vòng hash, rải qua các AZ.
- *Quorum*: ghi thành công khi W node xác nhận, đọc khi hỏi R node.
  - `W + R > N` thì tập node đọc và tập node ghi luôn giao nhau, nên đọc thấy bản ghi mới nhất
    trong điều kiện bình thường.
  - W=1, R=1: nhanh nhưng chỉ eventual.
- Xử lý xung đột khi hai bản ghi cùng lúc:
  - *LWW* (*last write wins*): bản có timestamp mới hơn thắng. Đơn giản, nhưng có thể mất ghi.
  - *Vector clock*: theo dõi phiên bản theo từng node, phát hiện được hai bản xung đột để app tự
    gộp.
- Xử lý node lỗi:
  - Node tạm chết: *hinted handoff*, node khác giữ hộ dữ liệu rồi trả lại khi node sống lại.
  - Lệch lâu: *anti-entropy* bằng *Merkle tree* (cây hash để so nhanh hai node lệch nhau ở đâu).
  - *Read repair*: lúc đọc thấy node nào cũ thì sửa luôn.
- Membership (node nào đang sống) lan truyền bằng *gossip*: mỗi node định kỳ trao đổi thông tin
  với vài node ngẫu nhiên.
- Storage engine *LSM*, theo thứ tự ghi:
  1. Ghi vào *WAL* (log ghi trước, để không mất khi crash).
  2. Ghi vào *memtable* trong RAM.
  3. Memtable đầy thì flush ra file *SSTable* đã sắp xếp, bất biến.
  4. Ở chế độ nền, *compaction* gộp các SSTable lại.

  Mỗi SSTable có một bloom filter, để đường đọc bỏ qua được các file chắc chắn không chứa key.

*Hỏi tiếp hay gặp*
- Thêm node thì dữ liệu di chuyển thế nào.
- TTL.
- Range query: consistent hashing phá thứ tự của key, nên quét một khoảng key rất khó.

**Đọc**
- Alex Xu vol 1, ch.7 *Design a Unique ID Generator*, ch.5 *Consistent Hashing* ([bản online](https://bytebytego.com/courses/system-design-interview/design-consistent-hashing)), ch.6 *Design a Key-Value Store* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-key-value-store))
- [Dynamo paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- DDIA ch.3 (LSM-tree)

**Nắm chắc khi**
- [ ] Vẽ được đường ghi và đường đọc của KV store với N=3, W=2, R=2, có một node chết
- [ ] Giải thích được vai trò bloom filter trong đường đọc của LSM

#### 3.4 Web crawler và search autocomplete

**Vì sao cần học:** Crawler và autocomplete là hai bài có cấu trúc dữ liệu riêng (hàng đợi theo
host, trie) và phần xử lý offline. Autocomplete còn có góc riêng cho tiếng Việt: người dùng gõ
không dấu nhưng vẫn phải ra kết quả có dấu.

**Học gì**

*Web crawler*
- Luồng chính, theo vòng:
  1. *Seed*: danh sách URL khởi đầu.
  2. *URL frontier*: hàng đợi các URL sẽ tải.
  3. Fetcher tải trang. DNS có cache, vì tra DNS cho từng URL rất chậm.
  4. Lưu nội dung vào object storage.
  5. Parser tách link từ trang.
  6. Lọc link.
  7. Đưa link mới vào lại frontier.
- Frontier gồm hai phần:
  - Hàng đợi ưu tiên: trang quan trọng tải trước.
  - Hàng đợi theo từng host, để đảm bảo *politeness*: tôn trọng `robots.txt` và crawl-delay, không
    dội request vào một website.
- Dedup:
  - URL: chuẩn hoá URL, rồi kiểm tra bằng bloom filter.
  - Nội dung trùng hệt: so hash.
  - Nội dung gần trùng: SimHash hoặc MinHash.
- ⚠️ *Crawler trap*: các trang sinh URL vô tận, như lịch có nút "tháng sau" mãi mãi, hoặc session
  id trong URL. Cách chặn: giới hạn độ sâu, độ dài URL, số trang mỗi host.
- Chia việc theo hash của host, để mỗi host chỉ do một worker phụ trách. Nhờ vậy dễ giữ
  politeness.

*Search autocomplete*
- *Trie* là cây mà mỗi node là một ký tự, đi từ gốc xuống là ghép thành prefix.
- Mỗi node lưu sẵn top-k gợi ý của cây con bên dưới. Truy vấn chỉ cần đi xuống theo prefix, nên
  O(độ dài prefix).
- Offline, theo từng bước:
  1. Thu log truy vấn.
  2. Tổng hợp tần suất, có trọng số cho độ mới.
  3. Build trie.
  4. Phát hành snapshot.
- Online: server giữ trie chỉ đọc trong bộ nhớ.
- Scale:
  - Shard theo prefix. ⚠️ Phân bố lệch: prefix "a" nhiều hơn "x" rất nhiều.
  - Cache prefix phổ biến ở CDN và browser.
  - Client *debounce*: chờ người dùng ngừng gõ một chút rồi mới gửi.
- Tiếng Việt: chuẩn hoá bỏ dấu khi index ([22-practical-data.md](22-practical-data.md)).

**Đọc**
- Alex Xu vol 1, ch.9 *Design a Web Crawler* ([bản online](https://bytebytego.com/courses/system-design-interview/design-a-web-crawler)) và ch.13 *Design a Search Autocomplete System*

**Nắm chắc khi**
- [ ] Thiết kế được frontier đảm bảo mỗi host tối đa 1 request/giây với 1.000 worker
- [ ] Giải thích được vì sao lưu top-k ở mỗi node trie, và cái giá khi cập nhật

#### 3.5 File storage (Drive/Dropbox) và video streaming

**Vì sao cần học:** Upload và phục vụ file lớn là việc dev PHP gặp thường xuyên, và cách làm sai
phổ biến là cho file đi xuyên qua app server. Bài Dropbox kiểm tra bạn tách metadata khỏi dữ liệu,
chia chunk và đồng bộ. Bài video chủ yếu kiểm tra bạn biết pipeline và chỗ tốn tiền.

**Học gì**

*File storage: tách block và metadata*
- Nội dung file chia thành các *block* lưu ở object storage.
- *Metadata* (tên file, thư mục, phiên bản, danh sách block) lưu ở SQL, cần consistency mạnh.

*Chunking*
- Chia file thành các chunk vài MB. Lợi:
  - Upload song song.
  - Upload tiếp khi bị ngắt (*resume*).
  - *Delta sync*: sửa file thì chỉ upload lại chunk bị đổi.
- *Content-defined chunking*: ranh giới chunk được chọn theo nội dung chứ không theo vị trí cố
  định. Chèn thêm dữ liệu vào giữa file thì chỉ vài chunk quanh chỗ chèn bị đổi. Với chunk cố
  định, mọi chunk phía sau đều lệch.

*Dedup*
- Dedup bằng hash nội dung: hai chunk cùng hash chỉ lưu một bản.
- ⚠️ Dedup chéo giữa các user làm lộ thông tin: upload xong ngay lập tức nghĩa là "file này đã có
  người khác lưu".

*Upload thẳng lên object storage*
- Dùng *pre-signed URL*: server ký một URL có hạn, client upload thẳng lên S3 bằng URL đó. File
  không đi qua app server.
- Laravel có `temporaryUploadUrl`.

*Sync*
- Mỗi client giữ con trỏ phiên bản, tức "tôi đã đồng bộ tới phiên bản nào".
- Server báo thay đổi bằng long polling hoặc WebSocket.
- Xung đột: tạo một "bản xung đột" riêng. Không tự merge file nhị phân.
- Mỗi version là một danh sách block. Block không còn version nào tham chiếu thì được *garbage
  collect* (dọn đi).

*Video (đại ý)*
- Pipeline, theo từng bước:
  1. Upload *resumable* (tiếp được khi bị ngắt).
  2. Đưa vào queue.
  3. *Transcode* ra nhiều bitrate, cắt thành các segment ngắn.
  4. Tạo manifest theo chuẩn **HLS** hoặc **DASH** (file liệt kê các segment và các mức chất lượng).
  5. Phân phối qua CDN.
- Player dùng *adaptive bitrate*: tự đổi chất lượng theo tốc độ mạng.
- Chi phí chủ yếu là băng thông CDN và storage. Video ít người xem không cần transcode mọi độ phân
  giải.
- Live streaming là bài khác hẳn.

**Đọc**
- Alex Xu vol 1, ch.15 *Design Google Drive* và ch.14 *Design YouTube* ([bản online](https://bytebytego.com/courses/system-design-interview/design-youtube))
- Dropbox: [Streaming File Synchronization](https://dropbox.tech/infrastructure/streaming-file-synchronization), [Rewriting the heart of our sync engine](https://dropbox.tech/infrastructure/rewriting-the-heart-of-our-sync-engine)
- AWS: [Uploading objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html); Laravel: [Temporary Upload URLs](https://laravel.com/docs/filesystem#temporary-upload-urls)
- [RFC 8216](https://www.rfc-editor.org/rfc/rfc8216) (HLS): lướt mục 4 để biết manifest trông thế nào

**Nắm chắc khi**
- [ ] Vẽ được luồng sửa 1 byte giữa file 1 GB và chỉ ra bao nhiêu dữ liệu phải upload lại với chunk cố định so với content-defined
- [ ] Thiết kế được luồng upload file 5 GB từ app Laravel mà app server không chạm vào nội dung

#### 3.6 Ride-hailing / nearby search

**Vì sao cần học:** Grab, Be, các app giao đồ ăn đều dựa trên bài toán "tìm điểm gần nhất". Bài
này kiểm tra hai thứ: xử lý lượng ghi vị trí rất lớn, và hiểu geo index hoạt động ra sao, nhất là
bẫy ranh giới ô của geohash.

**Học gì**

*Ước lượng và lưu vị trí*
- 1 triệu tài xế cập nhật vị trí mỗi 4 giây → 250.000 ghi/giây.
- Vị trí chỉ có giá trị trong thời gian ngắn, nên giữ trong bộ nhớ. Không ghi mọi điểm vào DB chính.

*Geo index*

| Cách | Ý tưởng | Hợp khi |
|---|---|---|
| Geohash | Mã hoá toạ độ thành chuỗi. Hai điểm có prefix chung dài thì gần nhau | Đơn giản, dùng index chuỗi thường được |
| Quadtree | Chia bản đồ thành 4 ô, ô nào quá nhiều điểm thì chia tiếp | Mật độ không đều (phố đông, ngoại ô thưa) |
| H3 | Lưới lục giác của Uber | Cần khoảng cách tới các ô lân cận đều nhau |
| Redis GEO | `GEOADD`, `GEOSEARCH`, bên trong là sorted set + geohash | Quy mô vừa, muốn có ngay |

- Geohash độ dài 6 là một ô khoảng 1,2 km × 0,6 km.
- ⚠️ Hai điểm sát nhau nhưng nằm hai bên ranh giới ô sẽ có prefix khác nhau. Vì vậy phải tìm cả 8
  ô lân cận, không chỉ ô chứa điểm.

*Ghép chuyến và lưu lộ trình*
- Shard theo vùng hoặc thành phố.
- Ghép chuyến phải tránh gán một tài xế cho hai khách: giữ tài xế có TTL, giống giữ ghế ở bài đặt
  vé (module 2.6).
- Lộ trình ghi bất đồng bộ qua stream.

*Hỏi tiếp hay gặp*
- *Surge pricing*: tăng giá khi cầu vượt cung.
- ETA theo bản đồ đường thật, không theo đường chim bay.

**Đọc**
- Alex Xu vol 2, ch.1 *Proximity Service* và ch.2 *Nearby Friends*
- [H3](https://h3geo.org/) (docs, mục introduction)
- Redis: [GEOSEARCH](https://redis.io/docs/latest/commands/geosearch/)

**Nắm chắc khi**
- [ ] Giải thích được bằng hình vì sao phải tìm 8 ô lân cận khi dùng geohash
- [ ] Chọn được geohash hay quadtree cho một app giao đồ ăn một thành phố và bảo vệ lựa chọn

#### 3.7 Distributed job scheduler

**Vì sao cần học:** Mọi app Laravel đều có scheduler và queue. Khi scale từ 1 lên 2 instance, bug
"cron chạy hai lần" xuất hiện gần như chắc chắn. Bài này kiểm tra bạn hiểu lease, idempotency và
vì sao exactly-once là ảo tưởng.

**Học gì**

*Yêu cầu*
- Có cả cron (chạy lặp) và job chạy một lần tại thời điểm T.
- Hàng triệu job.
- Không mất job.
- Không chạy trùng, hoặc chạy trùng cũng vô hại.
- Retry.
- Lưu lịch sử.

*Bản cơ bản trên DB*
- Bảng: `jobs(id, type, payload, run_at, status, attempts, locked_by, locked_until)`.
- Worker lấy job bằng `FOR UPDATE SKIP LOCKED` (Postgres, MySQL 8.0+): khoá các dòng đang rảnh,
  bỏ qua dòng worker khác đang khoá, nên nhiều worker không tranh nhau.
- `locked_until` là một *lease* (quyền giữ có thời hạn). Worker chết giữa chừng thì lease hết hạn
  và job được worker khác lấy lại.

*Cron chạy trùng*
- ⚠️ Cron cài trên mọi instance thì job chạy N lần.
- Cách sửa: chỉ một trigger duy nhất sinh bản chạy vào bảng `jobs`, chọn bằng *leader election*
  (các instance bầu ra một instance làm việc đó) hoặc bằng lock.
- Laravel: `onOneServer()` và `withoutOverlapping()`.

*At-least-once và idempotency*
- Hệ thống kiểu này là at-least-once, nên job phải idempotent.
- *Exactly-once* (chạy đúng một lần) là ảo tưởng. Chuỗi sự cố:
  1. Worker làm xong việc, ví dụ đã gửi email.
  2. Worker chết trước khi kịp ghi trạng thái "xong".
  3. Lease hết hạn, worker khác chạy lại job. Email đi lần hai.

*Retry và job dài*
- Retry có backoff, giới hạn số lần. Hết lần thì chuyển `FAILED` và alert.
- Job chạy lâu:
  - *Heartbeat*: định kỳ gia hạn lease để không bị lấy mất.
  - *Checkpoint*: lưu tiến độ để chạy lại thì tiếp từ chỗ dở.

*Quy mô lớn*
- Partition bảng `jobs` theo thời gian hoặc theo hash.
- *Timing wheel* hoặc delay queue để kích hoạt job đúng giờ mà không quét bảng.
- Dùng công cụ có sẵn: Temporal, hoặc Kubernetes CronJob cho việc đơn giản.

*Hỏi tiếp hay gặp*
- DAG phụ thuộc (job B chỉ chạy khi A xong, kiểu Airflow).
- Múi giờ và DST (giờ mùa hè làm một giờ bị lặp hoặc bị mất).
- Chia công bằng giữa các tenant.

**Đọc**
- Module 2.6 của [03-database-sql.md](03-database-sql.md) (`SKIP LOCKED`), module 3.6 của [14-distributed-systems.md](14-distributed-systems.md) (leader election)
- Laravel: [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server), [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps)

**Nắm chắc khi**
- [ ] Viết được query lấy job và luồng xử lý worker chết giữa chừng
- [ ] Sửa được sự cố "báo cáo gửi hai lần từ khi scale lên 2 instance" bằng hai lớp chặn (câu 26)

#### 3.8 Metrics / logging system

**Vì sao cần học:** Metrics và log là thứ bạn dùng hằng ngày để vận hành, và thiết kế sai (label
`user_id`, log không lọc thông tin cá nhân) gây tốn tiền hoặc sự cố thật. Bài này kiểm tra bạn hiểu
workload ghi rất nhiều, bài toán cardinality và đánh đổi chi phí giữa các hệ lưu log.

**Học gì**

*Metrics*
- Thu thập: agent đẩy lên, hoặc Prometheus định kỳ kéo (*pull*) từ app.
- Lưu trong *TSDB* (*time series database*), mỗi điểm dữ liệu là `(metric, labels, timestamp,
  value)`.
- Đặc điểm: ghi rất nhiều, đọc theo khoảng thời gian.
- Nén theo thời gian: Gorilla dùng delta-of-delta cho timestamp và XOR cho giá trị, vì các điểm
  liên tiếp thường rất giống nhau.
- *Downsampling*: giữ độ phân giải cao cho dữ liệu mới, gộp thô dần cho dữ liệu cũ. Ví dụ 10 giây
  trong 2 tuần, 5 phút trong 1 năm.
- ⚠️ *Cardinality*: mỗi tổ hợp giá trị label là một *time series* riêng. Label không giới hạn giá
  trị như `user_id` hay URL đầy đủ làm số time series bùng nổ.
  - Ví dụ: thêm label `user_id` cho 1 triệu user thì mỗi metric thành 1 triệu time series.

*Logging*
- Pipeline, theo từng bước:
  1. App ghi log ra stdout.
  2. Agent thu gom: **Grafana Alloy**, Fluent Bit hoặc Vector.
  3. Buffer: Kafka.
  4. Xử lý: parse, lọc *PII* (thông tin định danh cá nhân như số điện thoại, email), sampling.
  5. Lưu để tìm kiếm.
  6. Chuyển sang object storage để lưu lâu dài.
- ⚠️ Promtail đã EOL từ 2/3/2026. Grafana khuyên chuyển sang Alloy.
- Kafka làm buffer để khi hệ lưu trữ chậm thì log không bị mất và app không bị nghẽn.
- Retention chia nóng, ấm, lạnh: dữ liệu càng cũ càng nằm ở chỗ rẻ hơn và chậm hơn.
- Chọn nơi lưu:

| | Elasticsearch / OpenSearch | Loki |
|---|---|---|
| Index gì | Full-text, mọi nội dung | Chỉ label |
| Chi phí | Đắt | Rẻ hơn |
| Query | Nhanh, linh hoạt | Chậm hơn khi tìm trong nội dung |

*Alerting*
- Rule engine đánh giá các rule định kỳ.
- Gom nhóm alert liên quan, để một sự cố không bắn 500 alert.
- Định tuyến tới người trực (*on-call*).

**Đọc**
- Alex Xu vol 2, ch.5 *Metrics Monitoring and Alerting System*
- Facebook: [Gorilla: A Fast, Scalable, In-Memory Time Series Database](https://www.vldb.org/pvldb/vol8/p1816-teller.pdf) (mục 4 về nén)
- Prometheus: [Overview](https://prometheus.io/docs/introduction/overview/), [Do not overuse labels](https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels)
- Grafana: [Loki overview](https://grafana.com/docs/loki/latest/get-started/overview/), [Migrate from Promtail to Alloy](https://grafana.com/docs/alloy/latest/set-up/migrate/from-promtail/)
- [18-reliability-observability.md](18-reliability-observability.md)

**Nắm chắc khi**
- [ ] Tính được số time series khi thêm label `user_id` cho 1 triệu user và giải thích vì sao không được
- [ ] Vẽ được pipeline log từ app Laravel trên Kubernetes tới Loki, chỉ ra chỗ lọc PII

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Với câu
"Thiết kế X", các ý dưới đây là **điểm then chốt người chấm tìm**, không phải lời giải đầy đủ.

### 🟢 Junior

**1. Scale dọc và scale ngang khác nhau thế nào? Vì sao scale ngang cần stateless?** (1.3)
- Ý phải có: máy to hơn so với thêm máy; state (session, file, cache local) phải ra ngoài
- Điểm cộng: Laravel session Redis, file S3; sticky session là cách chữa cháy

**2. 99,9% availability là bao nhiêu phút downtime mỗi tháng?** (1.4)
- Ý phải có: ~43 phút/tháng, ~8,8 giờ/năm
- Điểm cộng: nhân availability của chuỗi phụ thuộc

**3. Hệ thống chạy trên một server, traffic tăng 10 lần. Làm gì theo từng bước?** (1.3)
- Ý phải có: đo trước; tách DB, tối ưu query; cache/CDN; stateless + LB; queue; replica
- Red flag: "chuyển sang microservices" hoặc "dùng Kubernetes" ngay bước đầu

**4. Vì sao không lưu file upload trên ổ đĩa app server?** (1.3)
- Ý phải có: không scale ngang được, mất khi server chết; dùng object storage
- Điểm cộng: pre-signed URL để upload thẳng

**5. 1 triệu request mỗi ngày là bao nhiêu QPS?** (1.2)
- Ý phải có: ~12 QPS trung bình, dùng 10^5 giây/ngày; peak gấp vài lần

### 🟡 Mid

**6. Thiết kế URL shortener cho 100 triệu URL mới mỗi tháng.** (2.1)
- Ý phải có: ước lượng dẫn tới cache là trọng tâm; base62 độ dài 7; so các cách sinh mã; unique constraint khi insert
- Điểm cộng: `301` so với `302` ảnh hưởng thống kê; click event qua queue; cache "không tồn tại"
- Red flag: không ước lượng mà shard ngay

**7. Thiết kế rate limiter cho API gateway.** (2.2)
- Ý phải có: chọn thuật toán theo burst và bộ nhớ; counter atomic trong Redis (Lua); `429` + `Retry-After`
- Điểm cộng: fail-open hay fail-closed; latency thêm vào; multi-region
- Red flag: `GET` rồi `SET` từ app

**8. Fan-out on write và fan-out on read khác nhau thế nào? Xử lý người nổi tiếng ra sao?** (2.4)
- Ý phải có: đánh đổi chi phí ghi và đọc; hybrid theo ngưỡng follower
- Điểm cộng: feed chỉ lưu id; bỏ qua user không hoạt động

**9. Thiết kế notification đa kênh không gửi trùng.** (2.3)
- Ý phải có: queue theo kênh; idempotency key với unique; retry + DLQ
- Điểm cộng: queue ưu tiên cho OTP; rate limit theo provider; giờ yên lặng theo timezone

**10. Thiết kế chat 1-1 và nhóm.** (2.5)
- Ý phải có: WebSocket, session registry, lưu trước rồi ack, thứ tự theo sequence của conversation
- Điểm cộng: `client_msg_id`; đồng bộ khi reconnect; presence không broadcast; FPM không giữ WebSocket
- Red flag: sắp tin theo timestamp của client

**11. Thiết kế đặt phòng khách sạn không bị double booking.** (2.6)
- Ý phải có: conditional update + affected rows, hoặc unique constraint; hold có hạn kiểm tra trong `WHERE`
- Điểm cộng: nhiều đêm trong một transaction khoá theo thứ tự; thanh toán về muộn; overbooking có chủ đích
- Red flag: "kiểm tra còn phòng rồi insert"

**12. Thiết kế leaderboard cho game 10 triệu người chơi.** (2.7)
- Ý phải có: Redis sorted set, `ZINCRBY`, `ZRANGE ... REV`, `ZREVRANK`; DB là nguồn sự thật
- Điểm cộng: phá hoà bằng thời điểm; key theo kỳ; biết `ZREVRANGE` đã deprecated

**13. Active-passive và active-active khác nhau thế nào?** (1.4)
- Ý phải có: bản chờ và failover so với cả hai cùng phục vụ; active-active mỗi bản phải chịu toàn tải
- Điểm cộng: split brain khi promote; xung đột ghi khi active-active nhiều region

**14. Một server PHP-FPM chịu được bao nhiêu request/giây? Cần bao nhiêu server cho 3.000 QPS?** (1.2)
- Ý phải có: QPS ≈ số worker / latency trung bình; worker bị chặn bởi RAM (RSS mỗi worker) và CPU; số server = peak / (QPS một server × 60–70%) + dự phòng
- Điểm cộng: tổng worker ≤ `max_connections` của DB; latency tăng khi DB chậm làm QPS mỗi server giảm theo; con số thật lấy từ load test
- Red flag: "tăng `pm.max_children` lên 500 là được"

### 🔴 Senior

**15. Thiết kế ví điện tử.** (3.1)
- Ý phải có: ledger bút toán kép append-only; idempotency ở mọi tầng; timeout PSP không phải thất bại; reconciliation
- Điểm cộng: hot account; webhook idempotent sai thứ tự; tiền không dùng float
- Red flag: chỉ có một cột `balance` và `UPDATE`

**16. Thiết kế flash sale 1.000 sản phẩm cho 1 triệu người.** (3.2)
- Ý phải có: từ chối rẻ ở nhiều tầng; trừ nguyên tử trong Redis; queue tạo đơn; DB chốt chặn cuối
- Điểm cộng: cô lập hạ tầng; scale trước; chia bucket hot key; đối soát Redis và DB

**17. Snowflake ID gồm những phần nào? Đồng hồ chạy lùi thì sao?** (3.3)
- Ý phải có: 41 bit ms, 10 bit machine, 12 bit sequence; phát hiện lùi và chờ hoặc từ chối
- Điểm cộng: cấp machine id cho pod; UUIDv7 khi không cần 64 bit

**18. Thiết kế key-value store phân tán.** (3.3)
- Ý phải có: consistent hashing + vnode; replication N; quorum; xử lý xung đột; hinted handoff, anti-entropy; LSM
- Điểm cộng: `W + R > N` vẫn không linearizable; bloom filter trong đường đọc

**19. Thiết kế Dropbox.** (3.5)
- Ý phải có: tách block và metadata; chunking + dedup theo hash; pre-signed URL; sync bằng con trỏ phiên bản; bản xung đột
- Điểm cộng: content-defined chunking; rủi ro dedup chéo user; GC block

**20. Tìm tài xế gần nhất: geohash hay quadtree?** (3.6)
- Ý phải có: 250.000 ghi/giây giữ trong bộ nhớ; geohash cần 8 ô lân cận; quadtree hợp mật độ lệch
- Điểm cộng: H3; Redis GEO cho quy mô vừa; giữ tài xế có TTL khi ghép chuyến

**21. Tình huống: giữa bài URL shortener, người phỏng vấn nói "traffic đọc tăng 100 lần".** (2.1, 1.2)
- Ý phải có: ước lượng lại; cache hit rate và dung lượng; CDN cache redirect
- Điểm cộng: hot key → cache in-process trước Redis; thundering herd khi cache chết ([11-cache.md](11-cache.md))

**22. Tình huống: người phỏng vấn nói "Thiết kế Instagram" rồi im lặng.** (1.1)
- Ý phải có: chốt phạm vi (đăng ảnh, follow, feed), hỏi DAU và tỉ lệ đọc/ghi, nói thành tiếng giả định
- Điểm cộng: chọn deep dive vào feed (fan-out) và lưu ảnh (object storage + CDN)
- Red flag: bắt đầu vẽ ngay story, DM, search

**23. Tình huống: bài ví điện tử, "gọi PSP bị timeout, giờ làm gì?"** (3.1)
- Ý phải có: trạng thái `UNKNOWN`, không tạo giao dịch mới; query với cùng mã giao dịch; chờ webhook
- Điểm cộng: job quét `PENDING`/`UNKNOWN` quá lâu; reconciliation cuối ngày; không cộng/trừ tiền khi chưa chắc

**24. Tình huống: sau flash sale, phát hiện bán 1.012 trên 1.000 sản phẩm.** (3.2)
- Ý phải có: tìm check-then-act, trừ kho không nguyên tử, retry tạo đơn trùng
- Điểm cộng: DB chốt chặn cuối; idempotency khi tạo đơn; liên hệ khách, hoàn tiền, postmortem

**25. Tình huống: một chat server chết, 50.000 kết nối rớt cùng lúc.** (2.5)
- Ý phải có: reconnect có backoff + jitter; tin không mất vì lưu trước khi ack; đồng bộ theo `last_seen_message_id`
- Điểm cộng: session registry hết hạn; tin trong lúc đó đi đường push

**26. Tình huống: job gửi báo cáo chạy hai lần mỗi sáng từ khi scale lên 2 instance.** (3.7)
- Ý phải có: cron chạy trên mọi instance; `onOneServer()`/lock/leader election hoặc tách scheduler ra một process
- Điểm cộng: làm job idempotent (ghi dấu "đã gửi báo cáo ngày X") để trùng cũng vô hại

**27. Cần 99,99%. Bạn thay đổi gì?** (1.4)
- Ý phải có: 52 phút/năm nên failover phải tự động; tính availability chuỗi phụ thuộc; multi-AZ
- Điểm cộng: deploy an toàn (canary) vì phần lớn sự cố đến từ thay đổi; static stability
- Red flag: "thêm server"

**28. Chọn SQL hay NoSQL cho dự án mới?** (1.3)
- Ý phải có: bắt đầu từ pattern truy cập và yêu cầu consistency; SQL là mặc định tới khi có lý do cụ thể
- Red flag: "NoSQL vì scale" mà không nói quy mô

---

## Bài tập tự làm

1. **Tự chấm một bài.** Làm bài URL shortener trong 45 phút theo đúng bảy bước ở module 1.1,
   ghi ra giấy, sau đó tự chấm theo mục "Người chấm đánh giá".
2. **Ước lượng chat.** Ứng dụng chat 20 triệu DAU: QPS gửi tin, storage mỗi năm, số kết nối
   WebSocket đồng thời, số chat server cần nếu mỗi server giữ được một số kết nối bạn tự giả định.
3. **Token bucket.** Viết Lua script token bucket cho Redis (tham số: capacity, refill rate),
   kèm giải thích vì sao phải chạy nguyên tử.
4. **Ledger.** Thiết kế schema ledger cho ví điện tử hỗ trợ nạp, chuyển, refund; viết câu SQL
   kiểm tra ledger cân bằng.
5. **Đặt vé.** Thiết kế hệ thống đặt vé xem phim cho một buổi mở bán 50.000 người: vẽ sơ đồ,
   viết câu UPDATE giữ ghế, mô tả xử lý thanh toán về muộn.
6. **Sizing PHP-FPM.** Với app Laravel bạn đang làm (hoặc tự giả định): đo RSS trung bình mỗi
   worker và latency p50/p95, tính `pm.max_children` cho máy 8 GB RAM 4 core, số server cho
   peak 2.000 QPS, và tổng connection tới MySQL. Nêu rõ giả định nào ảnh hưởng kết quả nhiều nhất.

> Nộp bài vào đây để được review.
