# Ôn phỏng vấn Backend (senior, PHP)

Lộ trình ôn phỏng vấn backend tới mức senior, chia theo chủ đề. Ngôn ngữ chính là **PHP/Laravel**,
database chính là **MySQL 8.4**. Java, Go và Postgres dùng để đối chiếu.

Tư tưởng của bộ này: **học chắc kiến thức trước, câu hỏi chỉ để kiểm tra.** Khi đã hiểu tới
gốc thì bị hỏi kiểu gì cũng trả lời được. Học thuộc câu trả lời mẫu thì chỉ cần bị hỏi vặn thêm
một lớp là đơ.

## Cách dùng

Mỗi file chủ đề có hai phần:

1. **Lộ trình kiến thức** (phần chính). Chia 2–3 chặng: 🟢 Nền → 🟡 Làm chủ → 🔴 Senior. Mỗi
   module gồm:
   - **Học gì**: các ý chính và cạm bẫy.
   - **Đọc**: link tới tài liệu gốc (official docs, RFC, sách, paper, blog kỹ thuật). Mọi link
     đã được kiểm tra còn mở được.
   - **Nắm chắc khi**: tiêu chí tự kiểm tra. Đây là những việc bạn **làm được**, không phải chỉ
     "biết".
2. **Câu hỏi thường gặp** (bonus). Mỗi câu kèm hướng trả lời mong đợi: ý phải có, điểm cộng
   senior, red flag. Trả lời thành tiếng trước, rồi mới đối chiếu.

Cuối mỗi file có **bài tập tự làm**. Nộp bài để được review.

**Kiến thức:** folder [kien-thuc/](kien-thuc/README.md) chứa phần học. Chủ đề chính có
**giáo trình đầy đủ từ cơ bản tới nâng cao** (chương sách, ví dụ chạy được, bài tập):
[PHP và Laravel](kien-thuc/php/README.md) (30 chương); Database đang viết. Các chủ đề khác có bài
đọc tổng hợp theo module. Cách học: đọc plan (file ở đây) để biết module cần gì → đọc chương giáo
trình mà module trỏ tới → quay lại plan tick "Nắm chắc khi" và trả lời Phần 2.

**Mindmap:** mở [mindmap.html](mindmap.html) bằng trình duyệt. Mindmap toả tròn, đi sâu từng
tầng: tất cả → nhóm → file → module → nhóm kiến thức.
- Node đang xem nằm ở tâm, các nhánh con toả quanh. Bấm một nhánh để đi vào; bấm vào tâm, bấm
  breadcrumb phía trên hoặc nhấn Esc để lùi lại.
- Ở tầng file, màu chấm cho biết module thuộc chặng nào: xanh là nền, vàng là làm chủ, đỏ là senior.
- Bấm vào một module để mở panel "Vì sao cần học" và tick các tiêu chí "Nắm chắc khi". Trạng thái
  tick lưu trong trình duyệt.
- Ô tìm kiếm gõ không dấu cũng được; bấm vào kết quả để nhảy thẳng tới đó.

**Tài liệu tham khảo:** [references.md](references.md) tổng hợp mọi tài liệu trong bộ này: tài liệu
nền của từng chủ đề, danh sách sách, những nguồn được dẫn nhiều nhất, và chỉ mục đầy đủ theo module.

Mindmap và file tài liệu tham khảo đều được sinh tự động từ các file bài học. Sau khi sửa file bài
học, chạy lại:

```bash
python3 tools/build_mindmap.py
python3 tools/build_references.py
```

| Ký hiệu | Nghĩa |
|---|---|
| 🟢 🟡 🔴 | junior / mid / senior |
| ⚠️ | cạm bẫy hay bị hỏi vặn |
| `- [ ]` | tiêu chí "nắm chắc khi". Chỉ tick khi làm được mà không nhìn tài liệu |

---

## Mục lục

Cột **Ưu tiên** là mức độ hay bị hỏi với vị trí senior backend PHP: ★★★ gần như chắc chắn bị
hỏi, ★★ hay bị hỏi, ★ tuỳ JD.

### Nền tảng
| File | Nội dung | Ưu tiên |
|---|---|---|
| [01-os-linux.md](01-os-linux.md) | process/thread, bộ nhớ, I/O, signal, Linux để debug production | ★★ |
| [02-networking.md](02-networking.md) | TCP/UDP, DNS, HTTP/1.1/2/3, TLS, WebSocket, proxy, load balancer, Nginx | ★★ |
| [21-dsa.md](21-dsa.md) | cấu trúc dữ liệu, thuật toán, các pattern luyện bài | ★★ |

### Dữ liệu
| File | Nội dung | Ưu tiên |
|---|---|---|
| [03-database-sql.md](03-database-sql.md) | InnoDB, index, EXPLAIN, transaction, isolation, lock, schema, PDO/Laravel, migration online, replication, sharding | ★★★ |
| [04-nosql-search-storage.md](04-nosql-search-storage.md) | Redis, MongoDB, Cassandra/DynamoDB, Elasticsearch, OLAP, S3, vector DB | ★★ |
| [11-cache.md](11-cache.md) | cache pattern, invalidation, stampede, penetration, avalanche | ★★★ |
| [22-practical-data.md](22-practical-data.md) | thời gian/timezone, tiền, Unicode/tiếng Việt, file lớn, email, cổng thanh toán | ★★ |

### Ngôn ngữ và thiết kế code
| File | Nội dung | Ưu tiên |
|---|---|---|
| [05-php-laravel.md](05-php-laravel.md) | PHP engine, PHP-FPM, OPcache, ngôn ngữ tới 8.5, Laravel sâu | ★★★ **ngôn ngữ chính** |
| [08-oop-design.md](08-oop-design.md) | OOP, SOLID, design pattern, clean code, refactoring | ★★ |
| [06-java-spring.md](06-java-spring.md) | Java 25, JVM, concurrency, Spring Boot, JPA | ★ khi JD có Java |
| [07-go.md](07-go.md) | slice/map/interface, error, goroutine/channel, runtime, testing | ★ khi JD có Go |

### Giao tiếp giữa các hệ thống
| File | Nội dung | Ưu tiên |
|---|---|---|
| [09-api-design.md](09-api-design.md) | REST, status code, idempotency, versioning, webhook, GraphQL, gRPC | ★★★ |
| [10-security.md](10-security.md) | password, session/JWT, OAuth2, phân quyền, OWASP 2025, crypto, secret | ★★★ |
| [12-messaging.md](12-messaging.md) | queue, Laravel Queue, Kafka, RabbitMQ, SQS, outbox, event-driven, cron/batch | ★★ |

### Hệ thống quy mô lớn
| File | Nội dung | Ưu tiên |
|---|---|---|
| [13-concurrency.md](13-concurrency.md) | race condition, lock, deadlock, concurrency trong ứng dụng web | ★★★ |
| [14-distributed-systems.md](14-distributed-systems.md) | CAP, consistency, replication, consensus, saga, distributed lock, resilience | ★★★ |
| [15-architecture.md](15-architecture.md) | layered, hexagonal, DDD, monolith/microservices, multi-tenancy | ★★ |
| [16-system-design.md](16-system-design.md) | phương pháp, ước lượng, building block, các bài kinh điển | ★★★ |
| [17-performance.md](17-performance.md) | latency, percentile, profiling, load test, capacity | ★★ |

### Vận hành và chất lượng
| File | Nội dung | Ưu tiên |
|---|---|---|
| [18-reliability-observability.md](18-reliability-observability.md) | SLO, HA, DR, log/metric/trace, alert, incident, postmortem | ★★ |
| [19-devops-cloud.md](19-devops-cloud.md) | Docker, Kubernetes, CI/CD, deploy strategy, IaC, AWS | ★★ |
| [20-testing-quality.md](20-testing-quality.md) | testing, PHPUnit/Pest, code review, static analysis, tech debt, Git | ★★ |

### Làm việc cùng AI
| File | Nội dung | Ưu tiên |
|---|---|---|
| [26-ai-assisted-engineering.md](26-ai-assisted-engineering.md) | dùng AI coding assistant/agent trong công việc: giao việc, kiểm chứng, review, bảo mật, đưa vào team, đo hiệu quả | ★★★ |
| [23-ai-llm-backend.md](23-ai-llm-backend.md) | tích hợp LLM vào sản phẩm: gọi LLM API, RAG, vector search, MCP, prompt injection | ★ đọc qua; ôn sâu khi JD có AI/LLM |

### Ngoài kỹ thuật
| File | Nội dung | Ưu tiên |
|---|---|---|
| [24-senior-leadership.md](24-senior-leadership.md) | ra quyết định, ước lượng, giao hàng, tech debt, migration, mentor | ★★★ |
| [25-interview-skills.md](25-interview-skills.md) | các vòng phỏng vấn, CV, kho câu chuyện, AI trong phỏng vấn, deal lương | ★★★ |

---

## Lộ trình tổng: 10 tuần

Học theo **hai vòng**. Vòng 1 đi rộng: làm chặng 🟢🟡 của mọi file quan trọng, để sớm có
cái nhìn toàn cảnh và không bị hổng mảng nào. Vòng 2 đi sâu: làm chặng 🔴, nơi quyết định bạn có
được đánh giá là senior hay không.

Lý do không làm xong từng file rồi mới sang file khác: các chủ đề phụ thuộc lẫn nhau (cache cần
hiểu DB, system design cần hiểu mọi thứ). Học sâu một file khi chưa có nền của các file khác thì
chóng quên và khó liên kết.

Mỗi ngày khoảng 2 giờ. **DSA ([21](21-dsa.md)) làm song song mỗi ngày 30–45 phút** trong suốt 10 tuần.

### Vòng 1: đi rộng (chặng 🟢🟡), 6 tuần

| Tuần | Trọng tâm | File (chặng 1–2) | Vì sao ở vị trí này |
|---|---|---|---|
| 1 | Database | [03](03-database-sql.md) | Được hỏi nhiều nhất; cache, concurrency, system design đều dựa trên nó |
| 2 | Ngôn ngữ chính | [05](05-php-laravel.md), [08](08-oop-design.md) | Người phỏng vấn đào sâu nhất vào ngôn ngữ ghi trong CV |
| 3 | Cache, concurrency | [11](11-cache.md), [13](13-concurrency.md), [22](22-practical-data.md) | Cần nền DB; đây là nơi hay có câu hỏi tình huống |
| 4 | API, bảo mật | [09](09-api-design.md), [10](10-security.md) | Bài thiết kế nào cũng có API và phân quyền |
| 5 | Queue, mạng, hệ điều hành | [12](12-messaging.md), [02](02-networking.md), [01](01-os-linux.md) | Nền để hiểu hệ phân tán và debug production |
| 6 | NoSQL, hệ phân tán, kiến trúc | [04](04-nosql-search-storage.md), [14](14-distributed-systems.md), [15](15-architecture.md) | Chuẩn bị cho system design |

### Vòng 2: đi sâu (chặng 🔴) và luyện tổng hợp, 4 tuần

| Tuần | Trọng tâm | File | Ghi chú |
|---|---|---|---|
| 7 | Chặng 🔴 của DB, PHP, concurrency | [03](03-database-sql.md), [05](05-php-laravel.md), [13](13-concurrency.md), [11](11-cache.md) | Đây là các câu hỏi vặn của senior |
| 8 | System design, performance | [16](16-system-design.md), [17](17-performance.md), chặng 🔴 của [14](14-distributed-systems.md) | Mỗi ngày tự làm một bài design trên giấy trong 45 phút |
| 9 | Vận hành, vai trò senior, làm việc cùng AI | [18](18-reliability-observability.md), [19](19-devops-cloud.md), [20](20-testing-quality.md), [24](24-senior-leadership.md), [26](26-ai-assisted-engineering.md) | Chuẩn bị câu chuyện sự cố, quyết định kỹ thuật, và cách bạn dùng AI |
| 10 | Phỏng vấn | [25](25-interview-skills.md), mock interview, lấp các lỗ hổng còn 🟥🟨 | Làm Phần 2 (câu hỏi) của mọi file như một bài thi |

Chỉ ôn thêm khi JD yêu cầu: [06](06-java-spring.md) (Java), [07](07-go.md) (Go), [23](23-ai-llm-backend.md) (AI/LLM, còn không thì đọc qua).

Riêng [26](26-ai-assisted-engineering.md) (dùng AI khi làm việc) nên **thực hành suốt 10 tuần**: mỗi
tuần áp dụng một module vào công việc thật, để tới lúc phỏng vấn có sẵn câu chuyện cụ thể.

### Gấp: 2 tuần

Chỉ làm chặng 🟡 và Phần 2 của các file ★★★.

| Ngày | Việc |
|---|---|
| 1–3 | [03](03-database-sql.md): các module về index, EXPLAIN, isolation, lock, tầng PHP |
| 4–5 | [05](05-php-laravel.md) |
| 6 | [11](11-cache.md), [13](13-concurrency.md) |
| 7 | [09](09-api-design.md), [10](10-security.md) |
| 8–9 | [16](16-system-design.md) (phương pháp + 3 bài) và [14](14-distributed-systems.md) (các ý chính) |
| 10–11 | [25](25-interview-skills.md), [24](24-senior-leadership.md), [26](26-ai-assisted-engineering.md): CV, giới thiệu bản thân, 5 câu chuyện, cách bạn dùng AI |
| 12–13 | Mock interview bằng Phần 2 của các file trên, rồi ôn lại chỗ bị đơ |
| 14 | Nghỉ, đọc lại câu chuyện, ngủ sớm |

---

## Theo dõi tiến độ

Đánh dấu mỗi chặng: 🟥 chưa học · 🟨 đã đọc nhưng chưa tick hết "Nắm chắc khi" · 🟩 tick hết và
trả lời được Phần 2 thành tiếng.

| File | 🟢 Nền | 🟡 Làm chủ | 🔴 Senior |
|---|---|---|---|
| 01 OS/Linux | 🟥 | 🟥 | 🟥 |
| 02 Networking | 🟥 | 🟥 | 🟥 |
| 03 Database | 🟥 | 🟥 | 🟥 |
| 04 NoSQL/Search | 🟥 | 🟥 | 🟥 |
| 05 PHP/Laravel | 🟥 | 🟥 | 🟥 |
| 06 Java/Spring | 🟥 | 🟥 | 🟥 |
| 07 Go | 🟥 | 🟥 | 🟥 |
| 08 OOP/Design | 🟥 | 🟥 | 🟥 |
| 09 API | 🟥 | 🟥 | 🟥 |
| 10 Security | 🟥 | 🟥 | 🟥 |
| 11 Cache | 🟥 | 🟥 | 🟥 |
| 12 Messaging | 🟥 | 🟥 | 🟥 |
| 13 Concurrency | 🟥 | 🟥 | 🟥 |
| 14 Distributed | 🟥 | 🟥 | 🟥 |
| 15 Architecture | 🟥 | 🟥 | 🟥 |
| 16 System design | 🟥 | 🟥 | 🟥 |
| 17 Performance | 🟥 | 🟥 | 🟥 |
| 18 Reliability | 🟥 | 🟥 | 🟥 |
| 19 DevOps/Cloud | 🟥 | 🟥 | 🟥 |
| 20 Testing | 🟥 | 🟥 | 🟥 |
| 21 DSA | 🟥 | 🟥 | 🟥 |
| 22 Practical data | 🟥 | 🟥 | 🟥 |
| 23 AI/LLM | 🟥 | 🟥 | 🟥 |
| 24 Senior skills | 🟥 | 🟥 | 🟥 |
| 25 Interview skills | 🟥 | 🟥 | 🟥 |
| 26 AI trong công việc | 🟥 | 🟥 | 🟥 |

---

## Nguyên tắc ôn tập

- **Sâu một ngôn ngữ hơn rộng ba ngôn ngữ.** Trả lời hời hợt về PHP khi CV ghi PHP bị trừ điểm
  nặng hơn nhiều so với việc không biết Go.
- **Đọc tài liệu gốc.** Blog tóm tắt hay sai hoặc đã cũ. Khi blog và official docs mâu thuẫn,
  tin docs. Khi có thể, **tự chạy thử**: hai terminal `mysql` dạy isolation level tốt hơn mọi
  bài viết.
- **Luôn hỏi "tại sao" và "đánh đổi gì".** Câu trả lời điểm cao thường có dạng *"Tôi chọn A vì
  X, nhưng phải chấp nhận Y; nếu Z thay đổi thì tôi chuyển sang B."*
- **Nói to khi ôn.** Hiểu trong đầu khác với giải thích được thành lời. Tự giải thích cho một
  người tưởng tượng, hoặc ghi âm lại.
- **Gắn kiến thức với trải nghiệm thật.** "Index giúp query nhanh" là câu nhạt. "Query báo cáo
  mất 8 giây, tôi `EXPLAIN` ra full scan, thêm composite index `(status, created_at)` và xuống
  còn 40ms" là câu được nhớ.
- **Ôn theo JD, không ôn theo cảm hứng.** Dùng bảng bên dưới.

---

## Từ khoá trong JD → cần ôn gì

| JD có nhắc | Sẽ bị hỏi | Đọc |
|---|---|---|
| "hệ thống lớn", "high traffic", "hàng triệu người dùng" | cache, scale ngang, DB replication/sharding, queue, performance | 03, 11, 12, 16, 17 |
| "microservices" | giao tiếp giữa service, saga, outbox, distributed tracing, API gateway, và **khi nào không nên** dùng microservices | 12, 14, 15, 18 |
| "fintech", "thanh toán", "ví" | transaction, isolation, idempotency, ledger, đối soát, bảo mật, audit | 03, 09, 10, 13, 22 |
| "e-commerce" | tồn kho và race condition, flash sale, giỏ hàng, đơn hàng dạng state machine, search | 03, 04, 13, 16, 22 |
| "realtime", "chat", "notification" | WebSocket/SSE, pub/sub, scale kết nối, thứ tự message | 02, 12, 16 |
| "Kafka", "event-driven", "streaming" | partition, consumer group, delivery semantics, outbox, CDC | 12, 14 |
| "Kubernetes", "Docker", "cloud", "DevOps" | container, probes, deploy strategy, IaC, observability | 19, 18 |
| "SaaS", "B2B", "multi-tenant" | tenant isolation, phân quyền, noisy neighbor | 10, 15 |
| "data", "báo cáo", "analytics" | OLAP, ETL, SQL nâng cao (window function), xử lý file lớn | 03, 04, 22 |
| "AI", "LLM", "RAG" | gọi LLM API, streaming, vector search, MCP, prompt injection | 23 |
| "AI-first", "dùng Copilot/Cursor/Claude Code", hoặc gần như mọi JD năm 2026 | bạn dùng AI khi code thế nào, kiểm chứng ra sao, rủi ro dữ liệu, đo hiệu quả | 26 |
| "tech lead", "senior", "mentor" | ra quyết định, ước lượng, migration, dẫn dắt sự cố, mentor | 24, 18, 15 |
| "PHP/Laravel" | ngôn ngữ và framework, ôn **sâu nhất** | 05, 03 (module tầng PHP) |
| "Java/Spring", "Go" | ngôn ngữ tương ứng | 06, 07 |

---

## Bộ này sẽ lớn dần

Không lộ trình nào đầy đủ cho mọi công ty.

1. **Đối chiếu JD**: lấy 5–10 JD của những vị trí bạn nhắm tới, gạch từ khoá, dò bảng ở trên.
   Từ khoá nào chưa có thì thêm module vào file phù hợp.
2. **Sau mỗi buổi phỏng vấn**: ghi lại câu hỏi ngay. Câu nào chưa có trong Phần 2 thì thêm vào,
   kèm hướng trả lời. Câu nào bị đơ thì quay lại module tương ứng.
3. **Mock interview**: nhờ bạn bè hoặc Claude hỏi ngẫu nhiên từ Phần 2 của các file, kèm hỏi vặn
   thêm 2 lớp, rồi ghi lại chỗ bị đơ.

---

## Checklist ngày phỏng vấn

- [ ] Đọc lại JD và CV của chính mình
- [ ] Đọc lại các câu chuyện: dự án, sự cố, bất đồng
- [ ] Đọc lại danh sách câu hỏi ngược
- [ ] Tìm hiểu công ty: sản phẩm, tech stack (blog kỹ thuật, tin tuyển dụng)
- [ ] Online: test mic, camera, mạng, chia sẻ màn hình; tắt thông báo
- [ ] Offline: đi sớm 10–15 phút
- [ ] Chuẩn bị giấy bút, nước uống
- [ ] Sau khi xong: ghi lại câu hỏi ngay

---

Luyện DSA bằng code chạy được trong repo này: [`../dsa/`](../dsa/).
