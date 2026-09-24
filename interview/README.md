# Ôn phỏng vấn Backend

Bộ checklist ôn phỏng vấn backend từ junior tới senior, chia theo chủ đề. Mục tiêu là
**không bỏ sót** chủ đề nào và **đủ sâu** để trả lời được các câu hỏi vặn.

## Cách dùng

Mỗi file có hai tầng:

1. **Bản đồ nhanh** (phần rộng): mỗi chủ đề con một dòng checkbox. Quét trong vài phút để
   biết mình còn thiếu gì.
2. **Chi tiết** (phần sâu): những ý phải nói được, trade-off, failure mode, cạm bẫy. Sau đó
   là **Senior trả lời khác gì**, **Tình huống**, **❓ Câu hỏi hay gặp** và **Bài tập tự làm**.

Ký hiệu dùng chung:

| Ký hiệu | Nghĩa |
|---|---|
| 🟢 | junior |
| 🟡 | mid |
| 🔴 | senior |
| (không nhãn) | level nào cũng cần |
| ⚠️ | cạm bẫy hay bị hỏi vặn |
| ❓ | câu hỏi tự kiểm tra |

Tick `[x]` một mục khi **giải thích được bằng lời của mình và trả lời được câu "tại sao?"
thêm 2 lớp nữa**. Chỉ đọc qua rồi thấy quen mắt thì chưa tính.

⚠️ Bộ này cố tình rất rộng. Junior nắm chắc các mục 🟢 và mục không nhãn là đủ; hãy dùng
các mục 🟡🔴 để biết mình còn thiếu gì, không phải để hoảng.

---

## Mục lục

Cột **Ưu tiên** là mức độ hay bị hỏi trong phỏng vấn backend nói chung: ★★★ gần như chắc
chắn bị hỏi, ★★ hay bị hỏi, ★ tuỳ JD và level.

### Nền tảng
| File | Nội dung | Ưu tiên |
|---|---|---|
| [01-os-linux.md](01-os-linux.md) | process/thread, bộ nhớ, I/O, signal, Linux để debug production | ★★ |
| [02-networking.md](02-networking.md) | TCP/UDP, DNS, HTTP/1.1/2/3, TLS, WebSocket, proxy, load balancer, Nginx | ★★ |
| [21-dsa.md](21-dsa.md) | cấu trúc dữ liệu, thuật toán, các pattern luyện bài | ★★ |

### Dữ liệu
| File | Nội dung | Ưu tiên |
|---|---|---|
| [03-database-sql.md](03-database-sql.md) | index, query optimizer, transaction, isolation, lock, schema, replication, sharding | ★★★ |
| [04-nosql-search-storage.md](04-nosql-search-storage.md) | Redis, MongoDB, Cassandra/DynamoDB, Elasticsearch, OLAP, S3, vector DB | ★★ |
| [11-cache.md](11-cache.md) | cache pattern, invalidation, stampede, penetration, avalanche | ★★★ |
| [22-practical-data.md](22-practical-data.md) | thời gian/timezone, tiền, Unicode/tiếng Việt, file lớn, email, cổng thanh toán | ★★ |

### Ngôn ngữ và thiết kế code
| File | Nội dung | Ưu tiên |
|---|---|---|
| [05-php-laravel.md](05-php-laravel.md) | PHP runtime, PHP-FPM, ngôn ngữ, Laravel sâu | ★★★ nếu làm PHP |
| [06-java-spring.md](06-java-spring.md) | Java, collections, JVM, concurrency, Spring, JPA | ★★★ nếu làm Java |
| [07-go.md](07-go.md) | slice/map/interface, error, goroutine/channel, runtime | ★★★ nếu làm Go |
| [08-oop-design.md](08-oop-design.md) | OOP, SOLID, design pattern, clean code, refactoring | ★★ |

### Giao tiếp giữa các hệ thống
| File | Nội dung | Ưu tiên |
|---|---|---|
| [09-api-design.md](09-api-design.md) | REST, status code, idempotency, versioning, webhook, GraphQL, gRPC | ★★★ |
| [10-security.md](10-security.md) | password, session/JWT, OAuth2, phân quyền, OWASP, crypto, secret | ★★★ |
| [12-messaging.md](12-messaging.md) | queue, Kafka, RabbitMQ, SQS, outbox, event-driven, cron/batch | ★★ |

### Hệ thống quy mô lớn
| File | Nội dung | Ưu tiên |
|---|---|---|
| [13-concurrency.md](13-concurrency.md) | race condition, lock, deadlock, concurrency trong ứng dụng web | ★★★ |
| [14-distributed-systems.md](14-distributed-systems.md) | CAP, consistency, replication, consensus, saga, distributed lock, resilience | ★★ (🔴 ★★★) |
| [15-architecture.md](15-architecture.md) | layered, hexagonal, DDD, monolith/microservices, multi-tenancy | ★★ |
| [16-system-design.md](16-system-design.md) | phương pháp, ước lượng, building block, các bài kinh điển | ★★ (🟡🔴 ★★★) |
| [17-performance.md](17-performance.md) | latency, percentile, profiling, load test, capacity | ★★ |

### Vận hành và chất lượng
| File | Nội dung | Ưu tiên |
|---|---|---|
| [18-reliability-observability.md](18-reliability-observability.md) | SLO, HA, DR, log/metric/trace, alert, incident, postmortem | ★★ |
| [19-devops-cloud.md](19-devops-cloud.md) | Docker, Kubernetes, CI/CD, deploy strategy, IaC, AWS | ★★ |
| [20-testing-quality.md](20-testing-quality.md) | testing, code review, static analysis, tech debt, Git | ★★ |

### Theo JD
| File | Nội dung | Ưu tiên |
|---|---|---|
| [23-ai-llm-backend.md](23-ai-llm-backend.md) | gọi LLM API, RAG, vector search, prompt injection | ★ (khi JD có AI/LLM) |

### Ngoài kỹ thuật
| File | Nội dung | Ưu tiên |
|---|---|---|
| [24-senior-leadership.md](24-senior-leadership.md) | ra quyết định, ước lượng, giao hàng, tech debt, migration, mentor | ★★★ với senior |
| [25-interview-skills.md](25-interview-skills.md) | các vòng phỏng vấn, CV, kho câu chuyện, tâm lý, deal lương | ★★★ |

---

## Nguyên tắc ôn tập

- **Sâu một ngôn ngữ hơn rộng ba ngôn ngữ.** Người phỏng vấn sẽ đào vào ngôn ngữ ghi
  trong CV. Trả lời hời hợt về ngôn ngữ chính bị trừ điểm nặng hơn nhiều so với việc không
  biết một ngôn ngữ phụ.
- **Luôn hỏi "tại sao" và "đánh đổi gì".** Backend là nghề của trade-off. Câu trả lời điểm
  cao thường có dạng *"Tôi chọn A vì X, nhưng phải chấp nhận Y; nếu Z thay đổi thì tôi
  chuyển sang B."*
- **Nói to khi ôn.** Hiểu trong đầu khác với giải thích được thành lời. Hãy tự giải thích
  cho một người tưởng tượng, hoặc ghi âm lại.
- **Gắn mọi kiến thức với trải nghiệm thật.** "Index giúp query nhanh" là câu nhạt. "Có lần
  query báo cáo mất 8 giây, tôi `EXPLAIN` ra full scan, thêm composite index
  `(status, created_at)` và xuống còn 40ms" là câu được nhớ.
- **Ôn theo JD, không ôn theo cảm hứng.** Dùng bảng bên dưới để biết JD đang ngầm hỏi gì.

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
| "AI", "LLM", "RAG" | gọi LLM API, streaming, vector search, prompt injection | 23 |
| "tech lead", "senior", "mentor" | ra quyết định, ước lượng, migration, dẫn dắt sự cố, mentor | 24, 18, 15 |
| "PHP/Laravel", "Java/Spring", "Go" | ngôn ngữ và framework tương ứng, ôn **sâu nhất** | 05, 06, 07 |

---

## Cách tìm chỗ mình còn thiếu

Không checklist nào đầy đủ cho mọi công ty. Bộ này nên lớn dần theo trải nghiệm thật của bạn.

1. **Tự đánh giá lần đầu**: quét phần "Bản đồ nhanh" của mọi file, đánh dấu mỗi mục 🟥 (chưa
   biết), 🟨 (biết mơ hồ) hoặc 🟩 (giải thích được). Ôn các mục 🟨 trước, vì chúng tiến bộ
   nhanh nhất.
2. **Đối chiếu JD**: lấy 5–10 JD của những vị trí bạn nhắm tới, gạch từ khoá, dò trong bảng ở
   trên. Từ khoá nào không có trong bộ này thì thêm vào file phù hợp.
3. **Sau mỗi buổi phỏng vấn**: ghi lại câu hỏi ngay, câu nào chưa có trong mục ❓ thì thêm vào.
4. **Mock interview**: nhờ bạn bè hoặc Claude hỏi ngẫu nhiên từ các mục ❓, ghi lại câu bị đơ.

---

## Lịch ôn gợi ý

**6 tuần**, mỗi ngày khoảng 1,5–2 giờ. Có ít thời gian hơn thì giữ thứ tự và cắt các mục 🟡🔴.

| Tuần | Trọng tâm | File | DSA mỗi ngày |
|---|---|---|---|
| 1 | Database, cache | 03, 11 | 2 bài easy (hash map, two pointers) |
| 2 | Ngôn ngữ chính, OOP | 05/06/07, 08 | 2 bài easy (stack, binary search) |
| 3 | API, bảo mật, mạng, dữ liệu thực tế | 09, 10, 02, 22 | 1–2 bài easy/medium (linked list, tree) |
| 4 | Queue, concurrency, hệ phân tán, NoSQL | 12, 13, 14, 04 | 1–2 bài medium (sliding window, heap) |
| 5 | Kiến trúc, system design, performance, vận hành | 15, 16, 17, 18, 19 | 1 bài medium (graph, interval) |
| 6 | Câu chuyện, kỹ năng phỏng vấn, mock, lấp lỗ hổng | 25, 24, các mục còn 🟨🟥 | ôn lại bài đã sai |

**2 tuần** (gấp):

| Ngày | Việc |
|---|---|
| 1–3 | 03 (database) và 11 (cache): chỉ phần Bản đồ nhanh + ❓ |
| 4–5 | Ngôn ngữ chính (05/06/07) |
| 6–7 | 09 (API), 10 (bảo mật), 13 (concurrency, phần ứng dụng web) |
| 8–9 | 12 (queue) và 16 (system design: 3 bài đầu) nếu là mid trở lên; nếu là junior thì làm DSA |
| 10–11 | 25: CV, giới thiệu bản thân, 4 câu chuyện |
| 12–13 | Mock interview, ôn lại chỗ bị đơ |
| 14 | Nghỉ, đọc lại câu chuyện, ngủ sớm |

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
