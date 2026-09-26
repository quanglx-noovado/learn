# 12. Messaging, event-driven, background job

> [← Mục lục](README.md) · Trọng tâm: **Laravel Queue** (Redis/SQS/database) cho stack PHP, cùng Kafka 4.x, RabbitMQ 4.x, SQS/SNS; các pattern outbox/inbox/CDC/CQRS/event sourcing; cron và batch.
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
| [Laravel docs: Queues](https://laravel.com/docs/queues) | Official docs | Nguồn chuẩn cho job, worker, retry, batching của stack PHP. **Đọc hết** |
| [Apache Kafka 4.3: Design](https://kafka.apache.org/43/design/design/) | Official docs | Chương thiết kế: persistence, consumer position, delivery semantics, replication, compaction |
| *Kafka: The Definitive Guide*, 2nd ed. (Shapira, Palino, Sivaram, Petty; O'Reilly 2021) | Sách | Producer, consumer, reliability, exactly-once, vận hành. Ra trước Kafka 4.0 nên phần ZooKeeper và rebalance đã cũ |
| [RabbitMQ docs](https://www.rabbitmq.com/docs) | Official docs | Exchange, ack, confirm, quorum queue, stream |
| [Amazon SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html) | Official docs | Visibility timeout, FIFO, DLQ, quota |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.11 stream processing (log-based broker, CDC, event sourcing), ch.12 phần end-to-end argument (số chương theo bản 1) |
| [Enterprise Integration Patterns](https://www.enterpriseintegrationpatterns.com/patterns/messaging/) (Hohpe, Woolf) | Sách + site | Tên gọi chuẩn của các pattern: claim check, DLQ, idempotent receiver, competing consumers |
| [microservices.io patterns](https://microservices.io/patterns/) (Chris Richardson) | Site | Outbox, idempotent consumer, saga, CQRS, event sourcing |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Hiểu vì sao cần queue, delivery semantics, idempotent consumer, retry/DLQ; dùng Laravel Queue đúng | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.9 | Dùng được Kafka, RabbitMQ, SQS và biết chọn; outbox; ordering và schema; Laravel Queue sâu; cron nhiều instance | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.6 | Hiểu Kafka bên trong, exactly-once và fencing, Kafka 4.x, vận hành; pattern event-driven; job dài và workflow | 8–10 ngày |

Học theo thứ tự: chặng 2 cần mô hình at-least-once + idempotent của chặng 1, vì mọi broker
đều quay về đó. Với người làm PHP, module 1.4 và 2.8 là nơi bị hỏi xoáy nhiều nhất; Kafka thì
chỉ cần học sâu (chặng 3) nếu JD có ghi.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Vì sao cần queue, các mô hình cơ bản

**Vì sao cần học:** Trong Laravel, gửi email, resize ảnh, gọi webhook hay xuất báo cáo đều nên
chạy ở background qua queue, để request của user trả về nhanh. Người phỏng vấn thường mở đầu
bằng "vì sao cần message queue", rồi hỏi tiếp "việc nào **không** nên đẩy vào queue" và "queue
khác topic thế nào". Module này cho bạn từ vựng chung để đọc các module sau.

**Học gì**

*Queue giải quyết việc gì*
- *Message queue* (hàng đợi message) là một hệ thống trung gian, gọi là *broker*. Bên gửi
  (*producer*) bỏ một *message* (gói dữ liệu mô tả việc cần làm hoặc chuyện đã xảy ra) vào broker.
  Bên nhận (*consumer*, trong Laravel gọi là *worker*) lấy ra và xử lý sau.
  - Ví dụ: controller tạo đơn hàng xong thì đẩy job "gửi email xác nhận" vào Redis và trả về
    ngay. Một process `queue:work` chạy riêng mới thực sự gửi email.
- Bốn lợi ích:
  - **Decouple** (tách rời): producer không cần biết ai xử lý, cũng không cần bên xử lý đang sống.
    Service email chết 5 phút thì message chỉ nằm chờ, không làm lỗi luồng đặt hàng.
  - **Làm mượt đỉnh tải** (*load leveling*): 10.000 request đổ vào trong một phút thì queue giữ
    lại, worker xử lý dần theo sức của nó thay vì làm sập DB.
  - **Đẩy việc chậm ra background**: user không phải chờ gửi email 2 giây.
  - **Retry khi lỗi tạm thời**: API bên thứ ba trả 503 thì thử lại sau, không mất việc.
- Cái giá:
  - Thêm một hệ thống phải vận hành và giám sát.
  - *Eventual consistency*: dữ liệu ở các nơi chỉ khớp nhau **sau một lúc**, không khớp ngay.
    Ví dụ: đơn đã tạo nhưng vài giây sau email mới đi, tồn kho mới trừ.
  - Debug khó, vì một luồng nghiệp vụ bị rải qua nhiều consumer và nhiều log khác nhau.
  - Phải lo message bị **trùng** và bị **sai thứ tự** (module 1.2, 2.7).
- ⚠️ Không phải việc gì cũng nên đẩy vào queue. Việc mà user cần kết quả ngay thì gọi đồng bộ.
  - Ví dụ: kiểm tra số dư trước khi thanh toán. Đẩy vào queue thì user không biết thanh toán
    được hay không.

*Queue và topic*
- **Queue** (còn gọi là *point-to-point*): mỗi message chỉ được **một** consumer xử lý. Nhiều
  worker cùng đọc một queue thì chia nhau việc.
  - Ví dụ: 10 worker Laravel cùng đọc queue `emails`, mỗi email chỉ gửi một lần.
- **Topic** (còn gọi là *pub/sub*, publish/subscribe): mỗi *subscriber* (bên đăng ký nhận) nhận
  **một bản riêng** của mọi message.
  - Ví dụ: event "đơn hàng đã tạo" được cả service email, service kho, service báo cáo nhận.
- Mỗi broker làm hai mô hình theo cách riêng:
  - Kafka gộp cả hai qua *consumer group*: trong một group thì chia việc như queue, giữa các
    group thì mỗi group nhận đủ như topic (module 2.1).
  - RabbitMQ dùng *fanout exchange* chép message tới nhiều queue (module 2.3).
  - AWS tách làm hai dịch vụ: SNS là topic, SQS là queue, ghép SNS + SQS để có fan-out (module 2.4).

*Push và pull*
- **Push**: broker chủ động đẩy message tới consumer. RabbitMQ và SNS theo kiểu này.
  - Cần *prefetch* hoặc *flow control* (giới hạn số message đẩy tới mà consumer chưa xử lý xong),
    không thì consumer chậm bị ngập.
- **Pull**: consumer tự hỏi broker "có gì mới không". Kafka và SQS theo kiểu này.
  - Có *backpressure* tự nhiên: consumer bận thì không hỏi, nên không bị ngập. Backpressure là
    cơ chế để bên nhận chậm "đẩy ngược" áp lực về bên gửi.
  - Dễ gom lô: mỗi lần hỏi lấy luôn nhiều message.

*Event, command, query*
- Ba loại message khác nhau ở ý định:
  - *Event*: thông báo một chuyện **đã xảy ra**.
  - *Command*: yêu cầu **hãy làm** một việc.
  - *Query*: hỏi **cho tôi biết** một thông tin.

  | | Event | Command | Query |
  |---|---|---|---|
  | Nghĩa | "đã xảy ra" | "hãy làm" | "cho tôi biết" |
  | Tên | quá khứ: `OrderPlaced` | mệnh lệnh: `SendInvoice` | `GetOrderStatus` |
  | Người nhận | 0..n, producer không biết là ai | đúng 1 handler | 1, cần trả lời |
  | Từ chối được? | không | được | không áp dụng |
  | Kênh hợp | topic/pub-sub | queue | thường gọi đồng bộ |

- ⚠️ "Event" trá hình command, ví dụ `OrderPlacedSoPleaseSendEmail`.
  - Tên như vậy ngầm nói producer biết và phụ thuộc vào một consumer cụ thể (service email). Đây
    là *coupling* (ràng buộc) ngầm, đúng thứ mà queue được dùng để tránh.
  - Sửa: phát event `OrderPlaced`, để service email tự quyết định có phản ứng hay không.

**Đọc**
- EIP: [Point-to-Point Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PointToPointChannel.html), [Publish-Subscribe Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/PublishSubscribeChannel.html), [Competing Consumers](https://www.enterpriseintegrationpatterns.com/patterns/messaging/CompetingConsumers.html)
- Martin Fowler: [What do you mean by "Event-Driven"?](https://martinfowler.com/articles/201701-event-driven.html)
- Kafka design: [Push vs. pull](https://kafka.apache.org/43/design/design/#push-vs-pull)

**Nắm chắc khi**
- [ ] Cho 5 tính năng, chỉ ra được cái nào nên qua queue, cái nào nên gọi đồng bộ, và vì sao
- [ ] Đặt tên đúng event hay command cho 5 message trong một luồng đặt hàng

#### 1.2 Delivery semantics và idempotent consumer

**Vì sao cần học:** Đây là ý quan trọng nhất của cả file: mọi broker trên thực tế đều có thể
giao **cùng một message hai lần**. Job trừ tiền hay gửi email mà không chịu được trùng thì sớm
muộn cũng charge khách hai lần. Câu "làm sao đảm bảo message không bị xử lý hai lần" gần như
chắc chắn gặp, và câu trả lời "SELECT kiểm tra trước" là red flag kinh điển.

**Học gì**

*Ack và ba mức đảm bảo giao*
- *Ack* (acknowledge) là tín hiệu consumer gửi cho broker: "tôi xử lý xong message này rồi, xoá
  đi hoặc đánh dấu đã đọc". Chưa ack thì broker coi như message chưa xong.
- *Delivery semantics* là mức đảm bảo mỗi message được xử lý bao nhiêu lần. Nó phụ thuộc vào
  **lúc nào ack** so với lúc xử lý:

  | Mức | Cách làm | Hậu quả khi consumer chết giữa chừng |
  |---|---|---|
  | *At-most-once* (nhiều nhất một lần) | Ack **trước** khi xử lý | Message đã ack nhưng chưa làm: **mất** |
  | *At-least-once* (ít nhất một lần) | Ack **sau** khi xử lý | Đã làm nhưng chưa ack: broker giao lại, **trùng** |
  | *Exactly-once* (đúng một lần) | Cần cơ chế đặc biệt | Chỉ đạt được trong phạm vi hẹp (xem dưới) |

- At-least-once là **mặc định thực tế** của gần như mọi hệ thống: thà trùng còn hơn mất.

*Vì sao không có exactly-once đầu cuối*
- Kịch bản:
  1. Consumer nhận message "gửi email cho đơn 42".
  2. Consumer gửi email xong.
  3. Consumer chết (bị kill khi deploy, hết RAM) **trước khi kịp ack**.
  4. Broker không biết việc đã làm hay chưa, nên giao lại cho consumer khác.
  5. Email được gửi lần hai.
- Broker không thể phân biệt "chết trước khi làm" và "chết sau khi làm nhưng trước khi ack".
- ⚠️ "Exactly-once" mà các broker quảng cáo chỉ đúng **trong phạm vi một hệ thống**:
  - Kafka đọc từ Kafka rồi ghi ra Kafka (module 3.2).
  - SQS FIFO chống trùng trong cửa sổ dedup 5 phút (module 2.4).
- Câu trả lời chuẩn khi phỏng vấn: **at-least-once + consumer idempotent = effectively-once**
  (hiệu quả như đúng một lần).

*Idempotent consumer*
- *Idempotent* nghĩa là làm một lần hay làm nhiều lần thì kết quả cuối vẫn như nhau.
  - `SET status = 'paid'` là idempotent: chạy 3 lần vẫn là `paid`.
  - `SET balance = balance + 100` không idempotent: chạy 3 lần cộng 300.
- *Idempotent consumer* là consumer nhận cùng một message nhiều lần mà hiệu lực chỉ như một lần.
- Các cách làm consumer idempotent:

  | Cách | Cơ chế | Hợp khi | Nhược điểm |
  |---|---|---|---|
  | Bảng `processed_messages` | `INSERT event_id` (unique) **trước**, cùng transaction với thay đổi nghiệp vụ | side effect nằm trong cùng DB | bảng phình, cần dọn |
  | Unique key nghiệp vụ | `UNIQUE(order_id)` trên bảng `invoices` | có khoá tự nhiên | không phải việc nào cũng có |
  | Upsert set giá trị tuyệt đối | `ON DUPLICATE KEY UPDATE status = 'paid'` | message mang trạng thái | không dùng cho cộng dồn (`+100`) |
  | Version/sequence | chỉ áp dụng khi `event.version > row.version` | cập nhật trạng thái có thứ tự | producer phải sinh version |

- Cách dùng bảng `processed_messages` theo đúng thứ tự:

  ```sql
  BEGIN;
  INSERT INTO processed_messages (event_id) VALUES (?);  -- trùng thì lỗi duplicate key: bỏ qua message
  UPDATE orders SET status = 'paid' WHERE id = ?;        -- thay đổi nghiệp vụ, cùng transaction
  COMMIT;
  -- chỉ ack message sau khi COMMIT thành công
  ```

*Các bẫy*
- ⚠️ **"Check rồi mới xử lý"** (`SELECT` xem đã xử lý chưa, chưa thì làm). Đây là lỗi
  *check-then-act* (kiểm tra rồi mới hành động, giữa hai bước có khe hở):
  1. Hai consumer nhận cùng một message song song.
  2. Cả hai cùng `SELECT`, cùng thấy "chưa có".
  3. Cả hai cùng xử lý.
  - Sửa: **INSERT `event_id` trước** (hoặc trong cùng transaction) để *unique constraint* (ràng
    buộc không trùng của DB) quyết định ai được làm. Bên INSERT sau sẽ nhận lỗi duplicate key.
- ⚠️ **Side effect ngoài DB** (email, API thanh toán) không nằm trong transaction của DB, nên
  rollback không thu hồi được:
  - API bên kia hỗ trợ thì truyền *idempotency key*: một mã duy nhất cho mỗi thao tác, gửi lại
    cùng mã thì bên kia trả kết quả cũ thay vì làm lại. Ví dụ Stripe header `Idempotency-Key`.
  - Email không có cơ chế này. Phải chọn một trong hai và nói rõ chọn bên nào:
    - Ghi "đã gửi" trước rồi mới gửi: nếu chết giữa chừng thì **có thể mất** email.
    - Gửi rồi mới ghi: nếu chết giữa chừng thì **có thể trùng** email.
- ⚠️ **Message id phải do producer sinh** và giữ nguyên qua mọi lần gửi lại.
  - Id do broker sinh (ví dụ SQS `MessageId`) sẽ khác nhau nếu producer gửi lại cùng nội dung,
    nên consumer không nhận ra là trùng.

**Đọc**
- microservices.io: [Idempotent Consumer](https://microservices.io/patterns/communication-style/idempotent-consumer.html)
- Kafka design: [Message Delivery Semantics](https://kafka.apache.org/43/design/design/#message-delivery-semantics)
- Stripe: [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency)
- DDIA ch.11: *Fault tolerance*, và ch.12: *The end-to-end argument for databases*

**Nắm chắc khi**
- [ ] Viết được đoạn SQL xử lý message idempotent, chỉ ra đúng thứ tự INSERT, UPDATE, COMMIT, ack
- [ ] Giải thích được vì sao `SELECT` kiểm tra trước rồi mới xử lý là sai khi có hai consumer
- [ ] Nói được với từng side effect (DB, API có idempotency key, email) thì đạt được mức đảm bảo nào

#### 1.3 Ack, retry, DLQ, poison message

**Vì sao cần học:** Job lỗi là chuyện hằng ngày: API đối tác timeout, dữ liệu sai định dạng,
deadlock. Cách bạn retry quyết định hệ thống tự lành hay tự đốt CPU, và message lỗi hẳn đi đâu.
Trong Laravel, `failed_jobs` chính là DLQ. Câu hỏi hay gặp: "DLQ là gì", "lỗi nào nên retry",
"message làm crash worker thì sao".

**Học gì**

*Ack và nack*
- Khi consumer ack, broker xử lý tuỳ loại:
  - RabbitMQ, SQS: **xoá** message khỏi queue.
  - Kafka: **tiến *offset***, tức ghi nhận vị trí đã đọc tới đâu. Message vẫn còn trong log
    (module 2.1).
- *Nack* hoặc *reject* là báo "tôi không xử lý được message này". Có hai lựa chọn:
  - *Requeue*: trả message về queue để thử lại.
  - Không requeue: bỏ message, hoặc đẩy sang DLQ (queue chứa message lỗi, xem dưới) nếu đã cấu hình.
- ⚠️ Nack + requeue **ngay lập tức** với lỗi cố định (ví dụ JSON hỏng) tạo vòng lặp nóng: message
  quay lại, lỗi, quay lại, lỗi... đốt CPU liên tục mà không bao giờ thành công.

*Retry đúng cách*
- Trước tiên phân loại lỗi:

  | Loại lỗi | Ví dụ | Xử lý |
  |---|---|---|
  | **Tạm thời** | timeout, HTTP 503, deadlock | Retry, vì lát nữa có thể thành công |
  | **Vĩnh viễn** | validation lỗi, HTTP 404, parse lỗi | Đẩy DLQ ngay, retry bao nhiêu lần cũng vẫn lỗi |

- Retry theo *exponential backoff + jitter*, có trần số lần:
  - *Exponential backoff*: khoảng chờ tăng theo cấp số nhân, ví dụ 1s, 2s, 4s, 8s. Cho hệ thống
    bên kia thời gian hồi phục.
  - *Jitter*: cộng thêm một khoảng ngẫu nhiên vào thời gian chờ. Không có jitter thì 1.000 job
    cùng lỗi lúc 10:00 sẽ cùng retry đúng 10:00:04, lại dồn một cú vào hệ thống vừa hồi phục.
  - Có trần: sau N lần thì dừng, đẩy vào DLQ.
- Retry ở đâu:

  | Cách | Cơ chế | Ưu | Nhược |
  |---|---|---|---|
  | Retry tại chỗ | `sleep` trong consumer rồi thử lại | Giữ thứ tự | **Chặn** cả queue hoặc partition trong lúc chờ |
  | Retry qua queue trễ | Đẩy message sang một queue có delay, lát nữa quay lại | Không chặn message khác | **Mất thứ tự** |

*DLQ*
- *DLQ* (dead letter queue) là queue chứa những message đã hết lượt retry hoặc lỗi vĩnh viễn, để
  người xem và xử lý sau.
- Một DLQ dùng được cần:
  - Alert ngay khi có message rơi vào.
  - Công cụ để xem message và **redrive**, tức đẩy message từ DLQ về queue gốc để chạy lại sau
    khi đã sửa bug.
  - Lưu kèm lỗi cuối cùng, số lần đã thử, và queue gốc.
- ⚠️ DLQ không ai nhìn thì chỉ là cách **mất message có tổ chức**.

*Poison message*
- *Poison message* là message luôn làm consumer lỗi, dù thử bao nhiêu lần.
- ⚠️ Nếu poison message làm **consumer crash** (OOM, segfault) chứ không chỉ ném exception:
  1. Consumer chết trước khi đoạn code đếm retry kịp chạy.
  2. Message không được ack, broker giao lại.
  3. Consumer mới nhận, lại crash. Vòng lặp không bao giờ dừng.
  - Sửa: đếm số lần giao **ở phía broker**, vì broker vẫn sống khi consumer chết. Ví dụ SQS
    `maxReceiveCount`, RabbitMQ quorum queue *delivery limit*.

**Đọc**
- EIP: [Dead Letter Channel](https://www.enterpriseintegrationpatterns.com/patterns/messaging/DeadLetterChannel.html)
- AWS: [Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

**Nắm chắc khi**
- [ ] Phân loại được 8 loại lỗi thường gặp thành retry được và không retry được
- [ ] Thiết kế được quy trình vận hành DLQ: ai nhận alert, xem ở đâu, redrive thế nào

#### 1.4 Laravel Queue cơ bản

**Vì sao cần học:** Với người làm PHP, đây là queue bạn dùng hằng ngày. Người phỏng vấn thích
hỏi vào chỗ Laravel "làm hộ" nhưng có bẫy: job chạy trước khi transaction commit, deploy xong
worker vẫn chạy code cũ, job fail ngay lần đầu vì mặc định chỉ thử 1 lần.

**Học gì**

*Connection, queue, job, worker*
- *Connection* là **nơi lưu** message: Redis, SQS, database, beanstalkd, hoặc `sync` (chạy ngay
  trong request, dùng khi test).
- *Queue* là **tên một hàng đợi** bên trong một connection. Một connection Redis có thể có nhiều
  queue như `default`, `emails`, `reports`.
  - ⚠️ Hai khái niệm này hay bị lẫn: `onConnection('sqs')` chọn nơi lưu, `onQueue('emails')` chọn
    hàng đợi.
- *Job* là một class implement `ShouldQueue`. Gọi `dispatch()` để đẩy vào queue.
  - `delay()` hẹn giờ chạy sau, `onQueue()` chọn queue.
- *Worker* là process chạy `php artisan queue:work`. Đây là **process chạy lâu**: nó không tắt
  sau mỗi job như request PHP-FPM, mà lặp mãi "lấy job, chạy, lấy job tiếp".

*Job lỗi*
- Bảng `failed_jobs` đóng vai DLQ (module 1.3). Các lệnh đi kèm:
  - `queue:failed` xem danh sách job lỗi.
  - `queue:retry` đẩy job lỗi về queue để chạy lại.
  - `queue:prune-failed` xoá job lỗi cũ.
- ⚠️ Nếu không cấu hình `tries`, mặc định job chỉ thử **1 lần**. Một lần API timeout là job vào
  `failed_jobs` luôn.

*SerializesModels*
- Khi job nhận một Eloquent model, trait `SerializesModels` chỉ lưu **id** của model vào payload.
  Lúc worker chạy job, nó lấy lại model từ DB bằng id đó.
  - Lợi: payload nhỏ, và job thấy dữ liệu mới nhất.
- ⚠️ Model đã bị xoá trước khi job chạy thì job lỗi `ModelNotFoundException`. Nếu chấp nhận bỏ
  job trong trường hợp này, đặt `deleteWhenMissingModels = true`.
- ⚠️ Relation đã load trên model cũng bị serialize theo, nên payload có thể to hơn bạn nghĩ.

*Dispatch trong transaction*
- ⚠️ Bug hay gặp:
  1. Code mở DB transaction, tạo đơn hàng, rồi `dispatch(new SendOrderEmail($order))`.
  2. Job vào Redis **ngay lập tức**, dù transaction chưa commit.
  3. Worker lấy job, query đơn hàng, nhưng đơn chưa commit nên không thấy.
  4. Hoặc transaction rollback, nhưng email vẫn được gửi cho một đơn không tồn tại.
- Sửa: bật `after_commit` trên connection, hoặc gọi `->afterCommit()` khi dispatch. Laravel sẽ
  giữ job lại tới khi transaction commit mới đẩy đi.

*Chạy worker trên production*
- *Supervisor* là chương trình giữ worker luôn sống: worker chết thì tự bật lại.
- ⚠️ Gọi `queue:restart` sau **mỗi lần deploy**. Worker là process chạy lâu, code đã nạp vào
  memory từ lúc khởi động, nên deploy code mới xong nó vẫn chạy code cũ cho tới khi restart.

**Đọc**
- Laravel: [Queues](https://laravel.com/docs/queues) phần *Introduction*, *Creating Jobs*, *Dispatching Jobs*, [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions), [Supervisor Configuration](https://laravel.com/docs/queues#supervisor-configuration), [Dealing With Failed Jobs](https://laravel.com/docs/queues#dealing-with-failed-jobs)

**Nắm chắc khi**
- [ ] Tái hiện được bug "job gửi email chạy trước khi đơn hàng được commit" và sửa bằng `afterCommit`
- [ ] Giải thích được vì sao deploy mà quên `queue:restart` thì worker chạy code cũ

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Kafka: mô hình, partition, producer

**Vì sao cần học:** Kafka là broker hay xuất hiện nhất trong JD backend, dùng cho event giữa
các service, CDC, log, analytics. Mô hình của nó khác hẳn queue kiểu Laravel/RabbitMQ: message
không mất đi khi đọc. Câu hỏi hay gặp: "Kafka đảm bảo thứ tự thế nào", "tăng partition thì
sao", "`acks=all` có chắc không mất dữ liệu không".

**Học gì**

*Kafka là một log*
- Kafka là một *distributed commit log*: một file nhật ký chỉ ghi nối vào cuối, được chia ra và
  chép sang nhiều máy.
  - Message được ghi nối tiếp và **không bị xoá khi đọc**. Đọc xong message vẫn còn đó cho người
    khác đọc.
  - Message chỉ bị xoá theo *retention*: theo thời gian (`retention.ms`, mặc định 7 ngày) hoặc
    theo dung lượng.
  - Vì message còn đó, consumer **tua lại** được: đặt lại vị trí đọc về quá khứ để xử lý lại.
- So với queue Laravel: job trong Redis bị xoá khi worker xong việc. Kafka thì giống một bảng log
  chỉ thêm, mỗi bên đọc tự nhớ mình đọc tới dòng nào.

*Các khái niệm*
- *Broker*: một server Kafka. Một *cluster* gồm nhiều broker.
- *Topic*: một luồng message cùng loại, ví dụ `orders`.
- *Partition*: topic được chia thành nhiều phần độc lập, nằm rải trên các broker. Đây là đơn vị
  để chia tải và để chạy song song.
- *Offset*: số thứ tự của message trong một partition, bắt đầu từ 0.
- *Consumer group*: một nhóm consumer cùng làm một việc. Kafka lưu offset riêng cho từng group.

  ```text
  topic: orders (3 partition)

  P0: [0][1][2][3][4][5]      ◄── group "email":   consumer A
  P1: [0][1][2][3]            ◄── group "email":   consumer B
  P2: [0][1][2][3][4]         ◄── group "email":   consumer B

  Group "inventory" đọc CÙNG topic với offset riêng: mỗi group nhận đủ mọi message.
  Trong một group, mỗi partition chỉ giao cho một consumer.
  ```

*Partition, key và thứ tự*
- Thứ tự chỉ được đảm bảo **trong một partition**. Hai message ở hai partition khác nhau có thể
  được xử lý theo thứ tự bất kỳ.
- Producer chọn partition cho message như sau:
  - Có *key* (ví dụ `order_id`): partition = `hash(key) % số_partition`. Mọi message cùng key
    luôn vào cùng partition, nên giữ được thứ tự theo key.
  - Không có key: dùng *sticky partitioner*, dồn một lô vào một partition rồi mới đổi sang
    partition khác, để gom lô hiệu quả.
- ⚠️ **Tăng số partition làm đổi mapping key → partition**, vì `% số_partition` đổi. Ví dụ đang
  12 partition, `order_id = 42` vào P6. Lên 24 partition, nó có thể vào P18. Message cũ của đơn 42
  nằm ở P6, message mới ở P18, hai consumer khác nhau xử lý, nên thứ tự theo key bị phá.
- ⚠️ **Không giảm được** số partition. Muốn ít hơn thì phải tạo topic mới.
- ⚠️ *Hot partition*: key bị lệch làm một partition quá tải trong khi các partition khác rảnh.
  - Ví dụ: key là `shop_id`, một shop lớn chiếm 80% đơn hàng.

*Consumer group và số partition*
- Trong một group, mỗi partition chỉ giao cho **một** consumer. Một consumer có thể nhận nhiều
  partition.
- Số consumer trong group vượt số partition thì **consumer thừa ngồi không**.
  - Ví dụ: 6 partition, 10 consumer thì 4 consumer không có việc.
- Vì vậy số partition là trần của độ song song. Nhưng ⚠️ quá nhiều partition làm tăng tải broker
  (nhiều file, nhiều metadata, bầu leader lâu hơn).

*Producer: acks*
- *Replica* là bản sao của partition trên broker khác. Mỗi partition có một *leader* (nhận ghi)
  và các *follower* (chép theo). *ISR* (in-sync replicas) là tập replica đang theo kịp leader
  (module 3.1).
- Cấu hình `acks` quyết định producer chờ gì trước khi coi là gửi thành công:

  | `acks` | Chờ gì | Rủi ro |
  |---|---|---|
  | `0` | không chờ | mất mà không biết |
  | `1` | leader ghi xong | leader chết trước khi replicate thì mất |
  | `all` (mặc định từ 3.0) | mọi replica trong ISR | chậm nhất, an toàn nhất |

- Bộ cấu hình an toàn phổ biến:
  - `replication.factor=3`: mỗi partition có 3 bản.
  - `min.insync.replicas=2`: phải có ít nhất 2 replica trong ISR thì mới nhận ghi.
  - `acks=all`.
  - Kết quả: chịu được một broker chết mà không mất dữ liệu và vẫn ghi được.
- ⚠️ Với `min.insync.replicas=1`, ISR có thể co lại chỉ còn leader, và khi đó "all" nghĩa là
  "chỉ leader". Leader chết là mất.

*Producer: idempotence, batching, callback*
- *Idempotent producer* (mặc định bật từ 3.0): mỗi producer có một *producer id*, mỗi message
  kèm một *sequence number*. Producer retry do mạng chập chờn thì broker nhận ra số thứ tự đã
  có và bỏ bản trùng.
- Batching và nén (`linger.ms`, `batch.size`, `compression.type`): producer chờ một chút để gom
  nhiều message thành một lô rồi nén. Đổi độ trễ lấy thông lượng.
  - `linger.ms` là thời gian tối đa chờ gom lô.
- ⚠️ Gửi bất đồng bộ (`send()` trả về ngay) thì **phải xử lý callback lỗi**. Không xử lý thì
  message gửi hỏng mà code không biết.

**Đọc**
- Kafka 4.3: [Introduction](https://kafka.apache.org/43/getting-started/introduction/), Design: [The Producer](https://kafka.apache.org/43/design/design/#the-producer), [Availability and Durability Guarantees](https://kafka.apache.org/43/design/design/#availability-and-durability-guarantees)
- [Producer configs](https://kafka.apache.org/43/configuration/producer-configs/): đọc `acks`, `enable.idempotence`, `linger.ms`, `delivery.timeout.ms`
- *Kafka: The Definitive Guide*: ch.3 (producer), ch.7 (reliable data delivery)
- Jay Kreps: *The Log: What every software engineer should know about real-time data's unifying abstraction* (LinkedIn Engineering, 2013; bản sách mở rộng *I Heart Logs*, O'Reilly 2014): bài gốc giải thích vì sao lại là log

**Nắm chắc khi**
- [ ] Vẽ được topic 3 partition với 2 consumer group và nói ai nhận message nào
- [ ] Chọn được key cho sự kiện đơn hàng và giải thích chuyện gì xảy ra khi tăng từ 12 lên 24 partition
- [ ] Nói được bộ cấu hình để chịu một broker chết mà không mất dữ liệu và vẫn ghi được

#### 2.2 Kafka: consumer, offset, rebalance

**Vì sao cần học:** Phần lớn bug Kafka ngoài thực tế nằm ở phía consumer: xử lý trùng, mất
message vì auto commit, group mới deploy bỏ qua dữ liệu cũ, rebalance liên tục. Câu "vì sao
consumer Kafka hay xử lý trùng, kể hai nguyên nhân" rất hay gặp, và "consumer lag" là metric
bạn sẽ bị hỏi khi nói về vận hành.

**Học gì**

*Vòng lặp consumer và commit*
- Consumer Kafka chạy một vòng lặp:
  1. `poll()` lấy một lô message.
  2. Xử lý lô đó.
  3. *Commit offset*: báo cho Kafka "group này đã xử lý tới đây".
- Commit **sau** khi xử lý là at-least-once: chết giữa bước 2 và 3 thì lần sau đọc lại lô đó.
- Commit là ghi offset của message **tiếp theo** cần đọc, không phải message cuối đã xử lý.
  - Ví dụ: xử lý xong offset 41 thì commit 42.
- Offset được lưu trong một topic nội bộ tên `__consumer_offsets` (loại *compacted*, xem cuối
  module). Mỗi group có một broker làm *group coordinator*, quản lý thành viên và offset của group.

*Các bẫy về offset*
- ⚠️ **Auto commit** (`enable.auto.commit=true`, là mặc định) commit **theo thời gian** (mỗi vài
  giây), không theo việc xử lý xong.
  - Nếu bạn đẩy message sang thread khác xử lý, auto commit có thể commit trước khi thread đó
    làm xong. Crash lúc này là **mất** message.
- ⚠️ `auto.offset.reset` quyết định group chưa có offset thì bắt đầu đọc từ đâu. Mặc định là
  `latest` (chỉ đọc message mới).
  - Hệ quả: một group mới deploy sẽ **bỏ qua toàn bộ message cũ** đang có trong topic. Muốn đọc
    từ đầu thì đặt `earliest`.
- ⚠️ Offset của group có hạn giữ (`offsets.retention.minutes`, mặc định 7 ngày). Group ngừng chạy
  lâu hơn thế thì offset bị xoá, và lúc chạy lại rơi về `auto.offset.reset`.
- Cách đạt effectively-once khi đích là DB: lưu offset **trong DB cùng transaction** với dữ liệu,
  và khi khởi động thì gọi `seek()` để nhảy tới offset đã lưu thay vì dùng offset của Kafka.

*Consumer lag*
- *Consumer lag* là khoảng cách giữa message mới nhất trong partition và offset group đã xử lý,
  tức "còn bao nhiêu message chưa xử lý". Đây là metric quan trọng nhất của consumer.
- ⚠️ Đo cả **lag theo thời gian** (message cũ nhất chưa xử lý đã chờ bao lâu). 10.000 message lag
  có thể là 1 giây hoặc 1 giờ, tuỳ tốc độ xử lý.

*Rebalance*
- *Rebalance* là lúc group chia lại partition giữa các consumer, xảy ra khi có consumer vào, ra,
  hoặc bị coi là chết.
- Kafka dùng hai cơ chế để phát hiện consumer có vấn đề:
  - Heartbeat và `session.timeout.ms`: consumer gửi tín hiệu "còn sống" định kỳ. Quá timeout không
    thấy thì coi là **process chết**.
  - `max.poll.interval.ms`: khoảng tối đa giữa hai lần `poll()`. Quá thì coi là **process sống
    nhưng kẹt**.
- ⚠️ Bẫy xử lý trùng kinh điển:
  1. Consumer xử lý một lô lâu hơn `max.poll.interval.ms` (mặc định 5 phút).
  2. Kafka đá consumer khỏi group và giao partition cho consumer khác.
  3. Consumer mới đọc từ offset đã commit, tức đọc lại chính lô đang xử lý.
  4. Lô bị xử lý **hai lần**.
  - Sửa: giảm `max.poll.records` (số message mỗi lần poll), hoặc xử lý nhanh hơn.
- *Static membership* (đặt `group.instance.id`): consumer có danh tính cố định, restart xong quay
  lại trong `session.timeout.ms` thì không gây rebalance. Hợp cho rolling deploy (module 3.3).

*Xử lý song song và retry*
- ⚠️ Xử lý song song các message **trong một partition** phá thứ tự và làm khó commit.
  - Ví dụ: offset 10, 11, 12 chạy song song, 12 xong trước. Không được commit 13, vì 10 và 11 chưa
    xong. Chỉ commit tới offset **liên tục thấp nhất** đã xong.
- Kafka không có sẵn retry có delay và DLQ. Phải tự dựng bằng các topic riêng:

  ```text
  orders ──lỗi──► orders.retry.1m ──lỗi──► orders.retry.10m ──lỗi──► orders.dlq
  ```

  - ⚠️ Retry topic làm **mất thứ tự**: message lỗi đi vòng qua topic khác, trong khi các message
    sau cùng key đã được xử lý. Cần thứ tự thì retry tại chỗ, hoặc chặn các message cùng key
    cho tới khi message lỗi xong.

*Log compaction*
- *Log compaction* là chế độ retention khác: thay vì xoá theo thời gian, Kafka giữ lại **message
  mới nhất của mỗi key** và xoá các bản cũ hơn cùng key.
  - Muốn xoá hẳn một key thì gửi *tombstone*: message có key đó và value `null`.
- Use case: `__consumer_offsets`, changelog của Kafka Streams, CDC snapshot, topic cấu hình.
- ⚠️ Các giới hạn:
  - Compaction chạy nền, nên tại một thời điểm vẫn có thể còn nhiều bản của cùng key.
  - Tombstone chỉ được giữ trong `delete.retention.ms`. Consumer đọc chậm hơn thế thì không thấy
    tombstone, nên không biết key đã bị xoá.
  - *Active segment* (file log đang được ghi, module 3.1) không bị compact.

**Đọc**
- Kafka design: [Consumer Position](https://kafka.apache.org/43/design/design/#consumer-position), [Static Membership](https://kafka.apache.org/43/design/design/#static-membership), [Log Compaction](https://kafka.apache.org/43/design/design/#log-compaction)
- [Consumer configs](https://kafka.apache.org/43/configuration/consumer-configs/): `enable.auto.commit`, `auto.offset.reset`, `max.poll.interval.ms`, `max.poll.records`, `group.protocol`
- *Kafka: The Definitive Guide*: ch.4 (consumer)
- Confluent: [Kafka Consumer Design](https://docs.confluent.io/kafka/design/consumer-design.html)

**Nắm chắc khi**
- [ ] Kể được 3 nguyên nhân khiến consumer Kafka xử lý trùng và cách sửa từng cái
- [ ] Giải thích được vì sao auto commit + xử lý bất đồng bộ có thể **mất** message
- [ ] Đọc được output `kafka-consumer-groups.sh --describe` và chỉ ra partition nào đang có vấn đề

#### 2.3 RabbitMQ

**Vì sao cần học:** RabbitMQ là task queue phổ biến khi cần định tuyến linh hoạt (theo loại
việc, theo vùng) và retry có delay. Nhiều hệ PHP dùng nó qua php-amqplib. Câu hỏi hay gặp:
"exchange là gì", "prefetch đặt bao nhiêu", "khi nào RabbitMQ mất message", và bài job dài bị
giao lại do consumer timeout.

**Học gì**

*Đường đi của một message*
- Producer không gửi thẳng vào queue, mà gửi vào một **exchange**:

  ```text
  producer ──► exchange ──binding──► queue ──► consumer
  ```

  - *Exchange*: bộ định tuyến, quyết định message đi tới queue nào.
  - *Binding*: luật nối exchange với queue, thường kèm một mẫu *routing key* (nhãn producer gắn
    vào message).
  - *Queue*: nơi message thật sự nằm chờ.
- Bốn loại exchange:

  | Loại | Định tuyến theo | Ví dụ |
  |---|---|---|
  | direct | routing key khớp chính xác | key `email` vào queue `emails` |
  | topic | mẫu có wildcard: `*` khớp đúng một từ, `#` khớp 0 hoặc nhiều từ | `order.*.vn` khớp `order.created.vn` |
  | fanout | bỏ qua key, chép tới **mọi** queue đã bind | pub/sub |
  | headers | giá trị trong header của message | ít dùng |

- *Default exchange*: "gửi vào queue X" thực ra là gửi qua exchange có tên rỗng với routing key `X`.

*Ack phía consumer*
- Ack thủ công bằng `basic.ack` sau khi xử lý xong.
- Connection đóng mà chưa ack (consumer chết) thì message quay lại queue, gắn cờ `redelivered`.
- `nack` hoặc `reject` với `requeue=false` thì message đi sang DLX (xem dưới).
- ⚠️ Quên ack: message nằm mãi ở trạng thái *unacked*, không ai khác nhận được, bộ nhớ broker tăng dần.
- ⚠️ *Consumer ack timeout* mặc định 30 phút: giữ message quá lâu chưa ack thì broker coi là có vấn đề.
  - Từ RabbitMQ 4.3, timeout này chỉ áp dụng cho quorum queue, và message quá hạn được trả lại
    queue thay vì đóng channel.
  - Hệ quả: job rất lâu (xử lý video 40 phút) dễ bị giao lại cho consumer khác.

*Prefetch*
- *Prefetch* (đặt bằng `basic.qos`) là số message tối đa broker giao cho một consumer mà chưa được ack.
  - Lớn: một consumer ôm hết message, consumer khác ngồi không.
  - Bằng 1: chia việc đều nhưng thông lượng thấp, vì mỗi lần chỉ nhận một message.
- Việc nặng và không đều (có job 1 phút, có job 40 phút): đặt prefetch nhỏ.

*Phía producer: confirm và mandatory*
- *Publisher confirms*: broker báo lại cho producer "đã nhận và lưu message". Không bật thì
  producer không biết message có tới hay không.
- `mandatory=true`: nếu message không route được tới queue nào, broker trả lại cho producer thay
  vì lặng lẽ bỏ đi.
- ⚠️ Chờ confirm **đồng bộ từng message** rất chậm. Nên confirm theo lô hoặc bất đồng bộ.

*DLX, TTL và delayed message*
- *DLX* (dead letter exchange) là exchange nhận các message bị "chết". Message bị dead-letter khi:
  - Bị reject không requeue.
  - Hết TTL.
  - Queue vượt `x-max-length`.
  - Vượt delivery limit.
- *TTL* (time to live) là thời gian sống tối đa, đặt theo queue hoặc theo từng message.
  - ⚠️ Classic queue chỉ xử lý TTL riêng của message khi message đó **tới đầu queue**. Message
    TTL ngắn nằm sau message TTL dài sẽ phải chờ.
- RabbitMQ không có delay sẵn trong queue thường. Ba cách làm delayed message:
  - TTL + DLX: mỗi mức trễ một queue. Message nằm ở queue "chờ 1 phút" không ai đọc, hết TTL thì
    dead-letter về queue chính.
  - Plugin *delayed message exchange*. Đọc kỹ giới hạn của plugin trước khi dùng.
  - Delayed retry của quorum queue (4.3).

*Độ bền và các loại queue*
- ⚠️ Muốn message sống qua lần restart broker thì cần **cả** hai: queue khai báo *durable* **và**
  message gửi với chế độ *persistent*. Thiếu một trong hai là mất.
- *Quorum queue*: queue được chép sang nhiều node, đồng thuận bằng thuật toán Raft.
  - Thay thế *classic mirrored queue*, loại này đã bị loại bỏ ở 4.0.
  - Delivery limit mặc định là 20 từ 4.0 (chống poison message, module 1.3).
  - Cần 3 hoặc 5 node.
- Classic queue từ 3.12 đã đẩy message xuống đĩa sớm, nên *lazy mode* cũ không còn tác dụng.
- *Streams*: một log kiểu Kafka nằm trong RabbitMQ, đọc lại được.
- *Single active consumer*: nhiều consumer đăng ký nhưng chỉ một consumer nhận message tại một
  thời điểm. Giữ được thứ tự mà vẫn có failover khi consumer đó chết.
- 4.3: *Khepri* là metadata store duy nhất (nơi lưu định nghĩa queue, exchange, user), thay Mnesia.

*Khi nào RabbitMQ mất message*
- ⚠️ Danh sách hay bị hỏi:
  1. Producer không bật confirm.
  2. Không đặt `mandatory`, message không route được bị bỏ.
  3. Queue không durable hoặc message không persistent.
  4. Consumer dùng auto-ack rồi crash.
  5. Hết TTL hoặc vượt max-length mà không có DLX.
  6. Classic queue trên một node, node đó hỏng đĩa.
  7. Ack trước khi xử lý xong.

**Đọc**
- RabbitMQ: [Tutorials](https://www.rabbitmq.com/tutorials) 1–5 (nếu chưa dùng bao giờ), [Exchanges](https://www.rabbitmq.com/docs/exchanges), [Consumer Acknowledgements and Publisher Confirms](https://www.rabbitmq.com/docs/confirms), [Consumer Prefetch](https://www.rabbitmq.com/docs/consumer-prefetch), [Delivery Acknowledgement Timeout](https://www.rabbitmq.com/docs/consumers#acknowledgement-timeout)
- [Dead Letter Exchanges](https://www.rabbitmq.com/docs/dlx), [TTL](https://www.rabbitmq.com/docs/ttl), [Quorum Queues](https://www.rabbitmq.com/docs/quorum-queues) (mục poison message handling), [Reliability Guide](https://www.rabbitmq.com/docs/reliability)
- [RabbitMQ 4.3 highlights](https://www.rabbitmq.com/blog/2026/04/23/rabbitmq-4.3-release)

**Nắm chắc khi**
- [ ] Liệt kê được 7 đường mất message trong RabbitMQ và cách chặn từng đường
- [ ] Chọn được prefetch cho job xử lý video 10–40 phút và giải thích
- [ ] Thiết kế được retry 1 phút, 10 phút, 1 giờ bằng TTL + DLX

#### 2.4 SQS và SNS

**Vì sao cần học:** Trên AWS, SQS là lựa chọn mặc định vì không phải vận hành gì, và Laravel
có sẵn driver SQS. Bug kinh điển là job chạy lâu hơn visibility timeout nên bị xử lý hai lần,
ví dụ gọi API thanh toán hai lần. Người phỏng vấn cũng hay hỏi các con số giới hạn và khác
biệt giữa Standard và FIFO.

**Học gì**

*Hai loại queue*

| | Standard | FIFO (tên kết thúc bằng `.fifo`) |
|---|---|---|
| Giao | At-least-once | Chống trùng trong cửa sổ dedup |
| Thứ tự | Best-effort, không đảm bảo | Đúng thứ tự trong từng message group |
| Thông lượng | Gần như không giới hạn | Có giới hạn, có chế độ high throughput (tra bảng quota theo region) |

- ⚠️ Standard queue có thể giao trùng **dù phía bạn không có lỗi gì**. Consumer bắt buộc phải
  idempotent.
- FIFO có hai khái niệm:
  - *Message group id*: message cùng group được giao đúng thứ tự, các group khác nhau chạy song
    song. Ví dụ dùng `order_id` làm group id.
  - *Deduplication id*: message cùng dedup id gửi trong **5 phút** chỉ được nhận một lần. Có thể để
    SQS tự tính từ nội dung (*content-based deduplication*).
  - ⚠️ Một message lỗi **chặn cả group** của nó cho tới khi xử lý xong hoặc vào DLQ.
- *Fair queues* (07/2025): gắn message group id trên **standard** queue. Mục đích khác hẳn FIFO:
  SQS dùng group id để giảm *noisy neighbor*, tức một tenant gửi quá nhiều message làm các tenant
  khác phải chờ.

*Visibility timeout*
- SQS không có ack kiểu RabbitMQ. Cơ chế của nó:
  1. Consumer nhận message. Message không bị xoá mà bị **ẩn** đi trong một khoảng gọi là
     *visibility timeout* (mặc định 30 giây, tối đa 12 giờ).
  2. Xử lý xong, consumer gọi `DeleteMessage`. Đây chính là "ack".
  3. Hết timeout mà chưa xoá, message **hiện lại** và consumer khác nhận được.
- ⚠️ Xử lý lâu hơn timeout thì consumer khác nhận **cùng message** trong khi consumer đầu vẫn
  đang chạy. Ví dụ worker gọi API 2 phút với timeout mặc định 30 giây.
  - Sửa: đặt timeout lớn hơn thời gian xử lý tối đa, hoặc gọi `ChangeMessageVisibility` định kỳ
    để gia hạn, giống một heartbeat.
- ⚠️ Timeout quá dài thì ngược lại: consumer crash làm message phải chờ rất lâu mới được thử lại.
- Không có nack. Muốn retry sớm thì đặt visibility của message về 0.

*Polling*
- *Long polling* (`WaitTimeSeconds`, tối đa 20 giây): nếu queue rỗng, SQS giữ request chờ tới khi
  có message hoặc hết thời gian. Ít request rỗng, rẻ hơn.
- *Short polling*: trả về ngay, và có thể trả **rỗng dù queue có message**, vì chỉ hỏi một phần
  server.

*DLQ*
- Cấu hình bằng *redrive policy*: message bị nhận quá `maxReceiveCount` lần thì chuyển sang DLQ.
  Vì SQS tự đếm, cách này bắt được cả poison message làm crash consumer (module 1.3).
- *DLQ redrive*: đẩy message từ DLQ về lại queue gốc.
- ⚠️ DLQ của một FIFO queue cũng phải là FIFO.

*Các con số cần nhớ*

| Giới hạn | Giá trị |
|---|---|
| Payload tối đa | **1 MiB** (nâng từ 256 KiB vào 08/2025) |
| Delay tối đa | 15 phút |
| Retention | Mặc định 4 ngày, tối đa 14 ngày |
| Số message mỗi lần nhận | Tối đa 10 |
| Dedup window của FIFO | 5 phút |

- Payload lớn hơn giới hạn: dùng *claim-check*, tức lưu payload lên S3 và message chỉ chứa đường
  dẫn (module 2.7).
  - AWS có sẵn Extended Client Library làm việc này. Laravel có overflow storage (module 2.8).

*Lambda và SNS*
- Lambda đọc SQS theo lô. Bật *partial batch response* để báo riêng message nào lỗi, không thì
  một message lỗi làm **cả lô** bị giao lại.
- *SNS fan-out*: SNS là dịch vụ pub/sub, gửi một bản tới nhiều SQS queue.
  - Mỗi service có một SQS riêng, nên có buffer, retry và DLQ riêng. Service này chậm không ảnh
    hưởng service kia.
  - *Filter policy*: mỗi subscriber chỉ nhận message khớp điều kiện.
  - *Raw message delivery*: gửi nguyên nội dung message, không bọc trong JSON của SNS.

**Đọc**
- SQS: [Visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html), [FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fifo-queues.html), [Fair queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fair-queues.html), [Dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html), [Message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html), [Short and long polling](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html)
- [SQS tăng payload lên 1 MiB](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib) (thông báo 08/2025)
- SNS: [Fanout to SQS](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html), [Message filtering](https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html)
- Lambda: [Handling errors for an SQS event source](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html) (partial batch response)

**Nắm chắc khi**
- [ ] Giải thích được bug "cùng một đơn bị gọi API hai lần" khi worker xử lý 2 phút với visibility timeout mặc định
- [ ] So sánh được message group id trên FIFO và trên fair queue standard: cùng tên, khác mục đích
- [ ] Nói đúng các giới hạn: payload, dedup window, delay, retention

#### 2.5 Redis, NATS, database làm queue, và chọn broker

**Vì sao cần học:** Không phải hệ thống nào cũng cần Kafka hay RabbitMQ. Laravel chạy queue
trên Redis hoặc ngay trên bảng MySQL, và với vài nghìn job mỗi ngày thì như vậy là đủ. Người
phỏng vấn muốn thấy bạn chọn broker theo nhu cầu, không theo độ nổi tiếng: "khi nào Kafka, khi
nào RabbitMQ, khi nào SQS", và red flag là "Kafka nhanh hơn nên chọn Kafka".

**Học gì**

*Redis làm queue: ba cách*
- **Redis List** (`LPUSH` để đẩy vào, `BRPOP` để lấy ra, chờ nếu rỗng):
  - ⚠️ `BRPOP` lấy message ra khỏi list ngay. Worker pop xong rồi crash là **mất** message.
  - *Reliable queue*: dùng `BLMOVE` chuyển message sang một list "processing" thay vì xoá hẳn.
    Xong việc mới xoá khỏi list processing. Cần thêm một tiến trình định kỳ thu hồi những việc
    nằm lâu trong list processing (worker đã chết).
- **Redis Pub/Sub**: *fire-and-forget* (gửi xong là quên, không lưu lại).
  - Subscriber đang offline lúc message được gửi thì **mất** message đó vĩnh viễn.
- **Redis Streams**: một cấu trúc log trong Redis, giống Kafka thu nhỏ.
  - `XADD` ghi message, `XREADGROUP` đọc theo consumer group, `XACK` ack.
  - *PEL* (pending entries list): danh sách message đã giao nhưng chưa ack của từng consumer.
  - `XAUTOCLAIM`: nhận lại các message nằm lâu trong PEL của consumer đã chết.
  - Giới hạn độ dài stream bằng `MAXLEN` (số message) hoặc `MINID` (id nhỏ nhất giữ lại).
  - ⚠️ Độ bền phụ thuộc vào cấu hình lưu đĩa của Redis (RDB/AOF) và replication **bất đồng bộ**.
    Khi failover sang replica, các message vừa ghi mà chưa kịp chép có thể mất.

*NATS*
- NATS core: định tuyến theo *subject* (tên kênh dạng `orders.created`), wildcard `*` (một phần)
  và `>` (mọi phần còn lại).
  - At-most-once: không lưu, subscriber offline là mất.
  - *Queue group*: các subscriber cùng group chia nhau message, như competing consumers.
- *JetStream* là lớp lưu trữ thêm vào NATS: persistence, ack, replay, dedup theo message id.

*Database làm queue*
- Dùng `SELECT ... FOR UPDATE SKIP LOCKED` (MySQL 8.0+, Postgres 9.5+). Laravel database driver
  dùng đúng cách này.
  - `FOR UPDATE` khoá các dòng job đã chọn.
  - `SKIP LOCKED` bỏ qua các dòng worker khác đang khoá, nên nhiều worker lấy job song song mà
    không chờ nhau và không lấy trùng.
- Ưu điểm:
  - Không thêm hạ tầng.
  - **Enqueue cùng transaction với dữ liệu**: tạo đơn và tạo job commit cùng nhau hoặc rollback
    cùng nhau. Đây sẵn là tính chất của outbox (module 2.6).
- Nhược điểm:
  - Worker phải polling liên tục, tốn tải DB.
  - Bảng *churn* (insert và delete liên tục). Trên Postgres gây *bloat*, bảng phình vì dòng chết
    chưa được dọn.
  - ⚠️ Phải có cơ chế thu hồi job ở trạng thái `running` của worker đã chết, không thì job đó
    treo mãi.

*Chọn broker*

| | Kafka | RabbitMQ | SQS | Redis Streams |
|---|---|---|---|---|
| Mô hình | log, giữ sau khi đọc | queue, xoá sau ack (có streams) | queue managed | log trong RAM |
| Đọc lại | tua offset | không (trừ streams) | không | theo id |
| Thứ tự | trong partition | trong queue, một consumer | FIFO theo group | trong stream |
| Retry có delay, DLQ | tự dựng | DLX, TTL, delivery limit | redrive, delay | tự dựng qua PEL |
| Định tuyến | topic + key | exchange linh hoạt | qua SNS filter | không |
| Vận hành | nặng (hoặc MSK, Confluent) | vừa | không phải vận hành | nhẹ nếu đã có Redis |
| Hợp với | event streaming, CDC, nhiều bên đọc | task queue, định tuyến phức tạp | task queue trên AWS | queue nhẹ |

- Cách nghĩ khi chọn:
  - Vài nghìn job mỗi ngày: bảng DB + `SKIP LOCKED` hoặc Redis mà Laravel đã có là đủ.
  - Cần nhiều bên đọc cùng một luồng event, đọc lại quá khứ, retention dài: Kafka.
  - Cần định tuyến phức tạp, retry có delay sẵn: RabbitMQ.
  - Đang trên AWS và muốn không phải vận hành: SQS.
  - Luôn hỏi thêm: đội có người vận hành được broker đó không.

**Đọc**
- Redis: [Streams](https://redis.io/docs/latest/develop/data-types/streams/), [BLMOVE: pattern reliable queue](https://redis.io/docs/latest/commands/blmove/)
- NATS: [JetStream](https://docs.nats.io/nats-concepts/jetstream)
- Brandur: [Postgres Job Queues & Failure By MVCC](https://brandur.org/postgres-queues)
- DB queue bằng `SKIP LOCKED`: module 2.6 của [03-database-sql.md](03-database-sql.md)

**Nắm chắc khi**
- [ ] Chọn được broker cho 4 bối cảnh (vài nghìn job/ngày; task queue trên AWS; CDC sang search; định tuyến theo vùng) và bảo vệ lựa chọn
- [ ] Giải thích được vì sao Redis Pub/Sub không dùng cho việc cần tin cậy, còn Streams thì tạm được

#### 2.6 Transactional outbox và inbox

**Vì sao cần học:** Luồng "tạo đơn xong thì phát event cho kho và email" có mặt ở mọi hệ
thống. Viết ngây thơ "lưu DB rồi publish" thì thỉnh thoảng mất event hoặc sinh event ma, và bug
này rất khó tái hiện. Transactional outbox là câu trả lời chuẩn, và câu "làm sao ghi DB và gửi
message luôn đi cùng nhau" là câu mid/senior rất hay gặp.

**Học gì**

*Dual write: vì sao mọi thứ tự đều sai*
- *Dual write* là ghi vào hai hệ thống khác nhau (DB và broker) trong cùng một thao tác, mà
  không có transaction chung nào bao cả hai.
- Ghi DB trước, publish sau:
  1. Transaction tạo đơn commit thành công.
  2. Publish lên broker lỗi (broker chết, mạng đứt, process bị kill).
  3. Đơn đã có nhưng **event bị mất**: kho không trừ, email không gửi.
- Publish trước, ghi DB sau:
  1. Publish event `OrderPlaced` thành công.
  2. Transaction DB rollback (lỗi validation, deadlock).
  3. Có **event ma**: kho trừ hàng, email gửi đi cho một đơn không tồn tại.
- Publish bên trong transaction trước khi commit cũng không cứu được: publish xong rồi commit
  lỗi thì vẫn ra event ma.

*Transactional outbox*
- Ý tưởng: không publish trực tiếp. Ghi event vào một bảng `outbox` **cùng transaction** với dữ
  liệu nghiệp vụ. Đơn và event commit cùng nhau hoặc cùng rollback.
- Một process riêng gọi là *relay* đọc bảng `outbox` và đẩy event lên broker.

  ```sql
  CREATE TABLE outbox (
    id             BIGINT AUTO_INCREMENT PRIMARY KEY,
    event_id       BINARY(16)   NOT NULL UNIQUE,  -- consumer dùng để dedup
    aggregate_type VARCHAR(50)  NOT NULL,
    aggregate_id   VARCHAR(64)  NOT NULL,         -- dùng làm key Kafka để giữ thứ tự
    event_type     VARCHAR(100) NOT NULL,
    payload        JSON         NOT NULL,
    created_at     DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    published_at   DATETIME(6)  NULL              -- NULL = chưa gửi
  );
  ```

  - *Aggregate* là thực thể nghiệp vụ mà event nói về, ví dụ một đơn hàng. `aggregate_id` là id
    của nó.

*Relay kiểu polling*
- Relay chạy vòng lặp:
  1. `SELECT ... WHERE published_at IS NULL ORDER BY id LIMIT n FOR UPDATE SKIP LOCKED`.
  2. Publish từng event lên broker.
  3. Cập nhật `published_at`.
- **Outbox luôn là at-least-once**: relay publish xong mà chết trước khi kịp cập nhật
  `published_at` thì lần sau gửi lại. Consumer vẫn phải idempotent, dùng `event_id` để dedup.
- ⚠️ **Poll theo `id > last_id` có thể bỏ sót event**:
  1. Transaction A lấy id 100, transaction B lấy id 101 (auto-increment cấp id lúc insert, không
     phải lúc commit).
  2. B commit trước. Relay đọc thấy 101, ghi nhớ `last_id = 101`.
  3. A commit sau. Dòng 100 giờ mới hiện ra, nhưng relay chỉ đọc `id > 101` nên bỏ qua mãi mãi.
  - Vì vậy dùng cờ `published_at IS NULL` như trên thay vì nhớ `last_id`.
- ⚠️ Nhiều relay chạy song song có thể **đảo thứ tự** event của cùng một aggregate: relay 1 lấy
  event 1, relay 2 lấy event 2, relay 2 publish trước.
  - Sửa: chia việc theo hash của `aggregate_id` (mỗi relay lo một phần), hoặc chỉ cho một relay
    active tại một thời điểm.

*Relay kiểu CDC*
- *CDC* (change data capture) là đọc log thay đổi của DB (binlog của MySQL, WAL của Postgres) để
  biết dòng nào vừa được thêm, sửa, xoá. *Debezium* là công cụ CDC phổ biến, chạy trên Kafka
  Connect.
- Dùng CDC làm relay: Debezium thấy dòng mới trong `outbox` thì đẩy lên Kafka.
  - Ưu: độ trễ thấp, đúng **thứ tự commit** (không dính bẫy id ở trên), có sẵn *outbox event
    router* để biến dòng outbox thành event.
  - Cái giá: phải vận hành Kafka Connect.
  - ⚠️ Postgres: CDC dùng một *replication slot* để giữ chỗ đọc WAL. Slot bị treo (connector chết)
    thì Postgres giữ lại toàn bộ WAL từ đó, làm **đầy đĩa**.

*Dọn outbox*
- Bảng outbox tăng mãi nếu không dọn. Hai cách:
  - Job xoá các dòng đã publish theo batch.
  - Partition bảng theo thời gian rồi drop partition cũ.

*Inbox*
- *Inbox* là outbox đặt ở phía consumer:
  1. Consumer nhận message, ghi vào bảng `inbox` (unique `event_id`), rồi ack ngay.
  2. Một process khác đọc `inbox` và xử lý.
- Unique `event_id` chặn trùng. Bản đơn giản nhất của inbox chính là bảng `processed_messages`
  ở module 1.2.

*Laravel*
- ⚠️ `afterCommit` (module 1.4) chỉ giải quyết "job chạy trước khi commit". Nó không giải quyết
  dual write: process chết ngay sau commit, trước khi đẩy job vào Redis, thì **vẫn mất job**.
- Muốn chắc chắn thì dùng outbox, hoặc dùng database queue driver **cùng connection** với dữ liệu
  để job được insert trong cùng transaction.

**Đọc**
- microservices.io: [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html), [Polling publisher](https://microservices.io/patterns/data/polling-publisher.html), [Transaction log tailing](https://microservices.io/patterns/data/transaction-log-tailing.html)
- Debezium: [Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)
- DDIA ch.11: *Change Data Capture*

**Nắm chắc khi**
- [ ] Giải thích được vì sao cả ba thứ tự dual write đều sai
- [ ] Viết được relay polling chạy 2 instance mà không đảo thứ tự của cùng aggregate (bài tập 1)
- [ ] Giải thích được bug "relay thỉnh thoảng bỏ sót event dù dòng vẫn trong bảng"

#### 2.7 Ordering, backpressure, kích thước, schema

**Vì sao cần học:** Khi hệ thống lớn dần, message bắt đầu tới sai thứ tự (cập nhật số dư cũ
đè số dư mới), queue dồn ứ vì consumer không theo kịp, và đổi format event làm vỡ service khác.
Ba chuyện này đều hay bị hỏi ở mức mid/senior, thường qua bài thiết kế "cập nhật số dư qua
Kafka mà giữ đúng thứ tự".

**Học gì**

*Thứ tự*
- Muốn **thứ tự toàn cục** (mọi message đúng thứ tự) thì cần một partition và một consumer. Như
  vậy là không scale được.
- Thực tế thường chỉ cần thứ tự **theo entity** (theo từng đơn, từng tài khoản). Mỗi broker có
  cách riêng:
  - Kafka: dùng entity id làm key.
  - SQS FIFO: dùng entity id làm message group id.
  - RabbitMQ: single active consumer.
- Cái giá:
  - Độ song song tối đa bằng số partition hoặc số group.
  - Một message lỗi **chặn cả nhóm** của nó (mọi message sau cùng key phải chờ).
- Cách thay thế: làm consumer **chịu được sai thứ tự**.
  - Dùng version: mỗi event mang số version, consumer bỏ event có version cũ hơn trạng thái
    hiện tại.
  - Hoặc event chỉ là tín hiệu "entity X vừa đổi", consumer gọi API đọc lại trạng thái mới nhất.

*Backpressure*
- Consumer chậm hơn producer thì queue dài dần. Hậu quả:
  - Độ trễ tăng: message mới phải chờ sau hàng nghìn message cũ.
  - Broker tốn đĩa và RAM.
  - RabbitMQ: khi chạm ngưỡng *memory alarm* hoặc *disk alarm*, broker **chặn mọi publisher** trên
    toàn broker, không chỉ queue bị dồn.
  - ⚠️ Kafka: message cũ bị retention xoá **trước khi kịp đọc**, tức mất dữ liệu lặng lẽ.
- Cách xử lý:
  - Scale thêm consumer.
  - Giới hạn tốc độ producer.
  - *Load shedding*: chủ động bỏ bớt việc ít quan trọng khi quá tải.
  - Alert theo *queue depth* (số message đang chờ) hoặc lag.

*Kích thước message*
- Broker được tối ưu cho message nhỏ.
  - Kafka mặc định khoảng 1 MB (`message.max.bytes`).
  - SQS tối đa 1 MiB.
- *Claim-check*: lưu payload lớn (file, ảnh, JSON lớn) lên S3, message chỉ chứa đường dẫn tới đó.
  - ⚠️ Nhớ quản lý vòng đời object trên S3: xoá quá sớm thì consumer không đọc được, không xoá
    thì tốn tiền mãi.

*Envelope*
- *Envelope* (phong bì) là phần khung chung bọc quanh mọi event, tách với dữ liệu nghiệp vụ:

  ```json
  {
    "event_id": "01J...",
    "event_type": "OrderPlaced",
    "version": 2,
    "occurred_at": "2026-09-25T03:00:00Z",
    "producer": "order-service",
    "correlation_id": "abc-123",
    "payload": { "order_id": 42, "total": 150000 }
  }
  ```

  - `correlation_id` hoặc `trace_id` dùng để nối các log của cùng một luồng nghiệp vụ qua nhiều
    service.

*Schema và versioning*
- Hai hướng tương thích:
  - *Backward compatible*: consumer **mới** đọc được message **cũ**.
  - *Forward compatible*: consumer **cũ** đọc được message **mới**.
- Thay đổi an toàn và nguy hiểm:
  - An toàn: thêm field optional có giá trị default.
  - Nguy hiểm (*breaking change*): xoá field, đổi kiểu, đổi nghĩa, đổi tên.
- Quy trình cho breaking change:
  1. Phát song song `v1` và `v2` (hoặc ra topic mới).
  2. Chuyển từng consumer sang `v2`.
  3. Khi không còn ai đọc `v1` thì mới ngừng phát `v1`.
- Consumer phải **bỏ qua field lạ** thay vì báo lỗi, để producer thêm field không làm vỡ ai.
- Avro hoặc Protobuf kèm *Schema Registry*: registry lưu các version của schema và kiểm tra tính
  tương thích **lúc produce**, chặn message sai trước khi vào topic.
- ⚠️ Message sống lâu hơn code. Replay Kafka từ 3 tháng trước thì consumer phải đọc được **mọi
  version** còn tồn tại trong topic.

**Đọc**
- EIP: [Claim Check](https://www.enterpriseintegrationpatterns.com/patterns/messaging/StoreInLibrary.html)
- Confluent: [Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)
- [CloudEvents spec](https://github.com/cloudevents/spec/blob/main/cloudevents/spec.md): tham khảo cách chuẩn hoá envelope
- RabbitMQ: [Memory and Disk Alarms](https://www.rabbitmq.com/docs/alarms)

**Nắm chắc khi**
- [ ] Thiết kế được cập nhật số dư qua Kafka giữ đúng thứ tự theo tài khoản, kể cả khi có lỗi
- [ ] Phân loại được 6 thay đổi schema thành an toàn và breaking, nêu quy trình cho loại breaking

#### 2.8 Tầng PHP: Laravel Queue sâu và consumer chạy lâu

**Vì sao cần học:** Đây là module riêng cho người làm PHP, và là nơi bị hỏi xoáy nhiều nhất.
Người phỏng vấn hay hỏi vào chỗ Laravel làm hộ và chỗ nó để lại cho bạn: `retry_after` với
`timeout` đặt sai làm job chạy hai lần song song, `ShouldBeUnique` bị hiểu nhầm là idempotency,
worker chạy lâu bị leak memory và mất connection DB. Bài "worker gọi API thanh toán, cùng một đơn
bị charge hai lần" gần như là câu chuẩn cho senior PHP.

**Học gì**

*Driver và Horizon*

| Driver | Khi nào dùng |
|---|---|
| Redis | Phổ biến nhất, dùng được Horizon |
| SQS | Trên AWS, không phải vận hành |
| database | Job được insert **cùng transaction** với dữ liệu |
| sync | Chạy ngay trong request, dùng khi test |
| `failover` | Khi connection chính lỗi lúc push job, thử connection tiếp theo trong danh sách |

- *Horizon* là dashboard và bộ quản lý worker cho Laravel, **chỉ dùng với Redis**.
  - Tự quản lý các *supervisor* (nhóm worker) theo cấu hình.
  - Balancing `auto` (tự dồn worker sang queue đang dài) hoặc `simple` (chia đều).
  - Metrics, tag để lọc job, notification khi queue chờ quá lâu.
  - ⚠️ Khi deploy dùng `horizon:terminate` thay cho `queue:restart`.

*Timeout và retry*
- Hai con số dễ lẫn:
  - `retry_after` (đặt trong config connection): job đã được lấy ra quá số giây này mà chưa xong
    thì queue **coi là treo và giao lại** cho worker khác. Với SQS, visibility timeout đóng vai
    này thay cho `retry_after`.
  - `timeout` của job, hoặc cờ `--timeout` của worker (mặc định 60 giây): job chạy quá số giây
    này thì **worker tự giết job và thoát**.
- ⚠️ `timeout` phải **ngắn hơn** `retry_after` vài giây. Nếu ngược lại:
  1. Job chạy tới giây thứ `retry_after` mà chưa xong, vẫn chưa bị giết vì chưa tới `timeout`.
  2. Queue giao lại job cho worker thứ hai.
  3. Hai worker cùng chạy **một job song song**. Nếu job gọi API thanh toán thì charge hai lần.
- Các thiết lập retry trên job:
  - `tries`: số lần thử tối đa.
  - `backoff`: thời gian chờ giữa các lần. Dùng mảng để tăng dần, ví dụ `[10, 60, 300]`.
  - `retryUntil`: thử lại tới một thời điểm, thay cho đếm số lần.
  - `maxExceptions`: số exception tối đa, tách với số lần `release()`.
  - `failOnTimeout`: timeout thì đánh dấu fail luôn, không thử lại.
- ⚠️ Mỗi lần `release()` (tự trả job về queue), và mỗi lần middleware `WithoutOverlapping` hoặc
  `RateLimited` trả job về, **đều tiêu một attempt**. Với `tries = 1` mặc định, job bị fail oan dù
  chưa từng chạy thật.

*Chống trùng và chồng*
- `ShouldBeUnique`: lấy lock **lúc dispatch**. Đã có một job cùng `uniqueId` đang chờ hoặc đang
  chạy thì lần dispatch sau bị bỏ qua.
  - Lock giữ tới khi job xử lý xong hoặc fail hết số lần thử.
  - `uniqueId` quy định thế nào là "cùng job", `uniqueFor` là thời gian tối đa giữ lock.
  - `ShouldBeUniqueUntilProcessing`: nhả lock ngay khi job **bắt đầu chạy**, nên trong lúc chạy
    vẫn dispatch được bản mới.
  - Cần cache driver hỗ trợ *atomic lock* (lock mà việc kiểm tra và lấy diễn ra trong một thao tác).
- Middleware `WithoutOverlapping($key)`: chặn **chạy song song**. Tại một thời điểm chỉ một job cùng
  key được chạy, job khác cùng key bị trả về queue.
  - `releaseAfter`: bao lâu sau thì thử lại. `expireAfter`: lock tự hết hạn sau bao lâu, phòng
    worker chết giữ lock mãi.
- `#[DebounceFor]`: dispatch nhiều lần trong một khoảng thời gian thì chỉ **bản cuối** chạy.
  - Ví dụ: user sửa hồ sơ 5 lần trong 10 giây, chỉ cần đồng bộ sang CRM một lần.
- ⚠️ Cả ba cơ chế đều dựa vào lock trong cache, và lock có thể hết hạn, bị mất khi Redis failover.
  Chúng giảm trùng nhưng **không thay** consumer idempotent (module 1.2).

*Chaining, batching và transaction*
- `Bus::chain([...])`: chạy các job **tuần tự**. Một job fail thì các job sau không chạy.
- `Bus::batch([...])`: chạy nhiều job song song và theo dõi chung cả nhóm.
  - Callback `->then()` (tất cả thành công), `->catch()` (có job lỗi đầu tiên), `->finally()`
    (xong hết, dù thành công hay lỗi).
  - `allowFailures()`: một job lỗi không làm huỷ cả batch.
  - Cần bảng `job_batches`.
  - ⚠️ Unique job không áp dụng trong batch.
- Transaction: `after_commit` trên connection, hoặc `->afterCommit()` khi dispatch (module 1.4).
- Áp dụng cho cả event listener, mail và notification được queue, không chỉ job.

*Payload*
- Payload của job là chuỗi PHP `serialize()`.
  - ⚠️ Ai ghi được vào Redis hoặc bảng `jobs` là chèn được object tuỳ ý, và worker sẽ
    `unserialize()` nó. Đây là lỗ hổng *object injection* (xem [10-security.md](10-security.md)).
  - Interface `ShouldBeEncrypted` mã hoá payload.
- *SQS overflow storage*: payload từ 1 MB trở lên được lưu vào cache store, SQS chỉ giữ con trỏ.
  Đây là claim-check có sẵn (module 2.7).
- SQS fair queue (module 2.4): gắn group bằng `onGroup()` hoặc `messageGroup()` trên job.

*Process chạy lâu và consumer tự viết*
- Áp dụng cho `queue:work` và cả consumer Kafka hay RabbitMQ bạn tự viết.
- Khác với PHP-FPM, worker **không boot lại framework** cho mỗi job. Các vấn đề:
  - ⚠️ Memory leak tích luỹ qua từng job.
  - ⚠️ Biến static và singleton trong container giữ state từ job trước sang job sau.
  - ⚠️ Connection DB chết: MySQL tự đóng connection nhàn rỗi quá `wait_timeout`, job tiếp theo gặp
    lỗi `MySQL server has gone away`.
- Cách chống: cho worker tự thoát định kỳ, Supervisor bật lại process mới sạch sẽ.

  ```bash
  php artisan queue:work --max-jobs=1000 --max-time=3600 --memory=256
  ```

  - `--max-jobs`: thoát sau 1.000 job. `--max-time`: thoát sau 3.600 giây. `--memory`: thoát khi
    vượt 256 MB.
- *Graceful shutdown* (dừng êm):
  1. Supervisor gửi SIGTERM khi deploy hoặc restart.
  2. Worker làm xong job hiện tại rồi mới thoát.
  3. Nếu quá `stopwaitsecs` (cấu hình của Supervisor) mà chưa thoát, Supervisor gửi SIGKILL giết
     ngay.
  - ⚠️ Vì vậy `stopwaitsecs` phải lớn hơn thời gian của job dài nhất.
- Consumer Kafka viết bằng PHP: dùng extension [php-rdkafka](https://github.com/arnaud-lb/php-rdkafka), là binding của
  thư viện C librdkafka.
  - Tự viết vòng lặp consume trong một artisan command, commit offset thủ công, xử lý rebalance
    callback.
  - Nhiều đội để một service Go hoặc Java lo consume Kafka, rồi đẩy việc sang Laravel queue.
- Consumer RabbitMQ viết bằng PHP: dùng [php-amqplib](https://github.com/php-amqplib/php-amqplib).
  - Đặt `basic_qos` (prefetch), ack thủ công, bật heartbeat.
  - ⚠️ PHP chỉ có một thread. Xử lý một job lâu thì thread đó bận, không gửi được heartbeat, nên
    broker tưởng consumer chết và đóng connection.

*Đối chiếu Java/Go*
- Spring: `@KafkaListener` với ack thủ công, `DefaultErrorHandler` +
  `DeadLetterPublishingRecoverer` để retry rồi đẩy DLQ. Xem [06-java-spring.md](06-java-spring.md).
- Go: thư viện `franz-go`, `confluent-kafka-go`, `amqp091-go`. Worker pool bằng goroutine, dùng
  `context` để dừng êm. Xem [07-go.md](07-go.md).
- Khác biệt gốc: Java và Go chạy nhiều luồng trong một process, nên một consumer vừa xử lý vừa
  gửi heartbeat được. PHP phải dựa vào nhiều process.

**Đọc**
- Laravel Queues:
  - [Job Expirations and Timeouts](https://laravel.com/docs/queues#job-expirations-and-timeouts) (`retry_after` và `--timeout`)
  - [Max Job Attempts and Timeout](https://laravel.com/docs/queues#max-job-attempts-and-timeout)
  - [Unique Jobs](https://laravel.com/docs/queues#unique-jobs), [Debounced Jobs](https://laravel.com/docs/queues#debounced-jobs), [Preventing Job Overlaps](https://laravel.com/docs/queues#preventing-job-overlaps)
  - [Job Chaining](https://laravel.com/docs/queues#job-chaining), [Job Batching](https://laravel.com/docs/queues#job-batching)
  - [Encrypted Jobs](https://laravel.com/docs/queues#encrypted-jobs), [SQS Overflow Storage](https://laravel.com/docs/queues#sqs-overflow-storage), [Queue Failover](https://laravel.com/docs/queues#queue-failover)
  - [Resource Considerations](https://laravel.com/docs/queues#resource-considerations), [Processing a Specified Number of Jobs](https://laravel.com/docs/queues#processing-a-specified-number-of-jobs), [Queue Workers and Deployment](https://laravel.com/docs/queues#queue-workers-and-deployment)
- Laravel: [Horizon](https://laravel.com/docs/horizon) (balancing strategies, deploying)
- [librdkafka CONFIGURATION.md](https://github.com/confluentinc/librdkafka/blob/master/CONFIGURATION.md): tên cấu hình dùng trong php-rdkafka
- Runtime PHP-FPM và CLI: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Giải thích được mối quan hệ `retry_after`, `timeout`, `tries`, `backoff` và đặt đúng giá trị cho job chạy tối đa 5 phút
- [ ] Chọn đúng giữa `ShouldBeUnique`, `WithoutOverlapping`, `DebounceFor` cho 3 tình huống cụ thể
- [ ] Liệt kê được 4 vấn đề của process PHP chạy lâu và cấu hình worker để tránh
- [ ] Liệt kê được mọi đường mất hoặc trùng job trong luồng dispatch → Redis → worker → API thanh toán (bài tập 2)

#### 2.9 Cron và scheduler nhiều instance

**Vì sao cần học:** Laravel Scheduler chạy qua một dòng crontab `schedule:run` mỗi phút. Khi
scale app từ 1 lên 3 server hay 3 pod mà không đổi gì, báo cáo ngày bị gửi 3 lần, tiền hoa hồng
bị tính 3 lần. Câu "chạy cron trên nhiều instance thế nào để không trùng" rất hay gặp, và red
flag là "dùng Redis lock là xong".

**Học gì**

*Vấn đề*
- Cron là trình hẹn giờ của Linux: đến giờ thì chạy lệnh. Mỗi server có crontab riêng.
- 3 instance, mỗi cái đều chạy cùng một crontab, thì job chạy **3 lần** mỗi lần tới giờ.

*Bốn cách chống*
- **Một instance riêng chạy scheduler**: chỉ một server có crontab, các server khác chỉ phục vụ
  web. Đơn giản, nhưng server đó chết thì không job nào chạy.
- **Lock trước khi chạy**: instance nào lấy được lock thì chạy, các instance khác bỏ qua.
  - Redis `SET key value NX PX 60000`: `NX` là chỉ set nếu key chưa có, `PX` là tự hết hạn sau
    số mili giây.
  - Hoặc một bảng lock trong DB.
- **Leader election** (bầu leader): các instance tự bầu ra một leader, chỉ leader chạy job.
  Ví dụ dùng *Lease* của Kubernetes.
- **Scheduler ngoài**: Kubernetes CronJob hoặc EventBridge Scheduler của AWS đến giờ thì đẩy việc
  vào queue, worker nào nhận thì làm.

*Laravel Scheduler*
- `onOneServer()`: dùng atomic lock trong cache để chỉ một server chạy task.
  - Cần cache driver database, memcached, dynamodb hoặc redis.
  - ⚠️ **Mọi server phải dùng chung** một cache. Mỗi server một Redis riêng thì ai cũng lấy được lock.
- `withoutOverlapping()`: chặn chạy chồng khi lần chạy trước chưa xong.
  - ⚠️ Lock mặc định hết hạn sau **24 giờ**. Process chết giữa chừng thì lock còn đó, và task bị
    bỏ qua **cả ngày**. Dọn bằng `schedule:clear-cache`.
- `runInBackground()`: chạy task ở process riêng, để task dài không chặn các task khác cùng phút.

*Các bẫy về lock*
- ⚠️ Lock TTL ngắn hơn thời gian chạy: lock hết hạn giữa chừng, instance khác lấy được và cũng chạy.
- ⚠️ Lock TTL quá dài: instance chết vẫn giữ lock, job không chạy tới khi lock hết hạn.
- ⚠️ Kubernetes CronJob chỉ đảm bảo "xấp xỉ một lần": có thể tạo hai job hoặc không tạo job nào.
  `concurrencyPolicy: Forbid` (không cho chạy chồng) cũng không thay được idempotency.

*Nguyên tắc*
- **Job phải idempotent**, lock chỉ để giảm lãng phí.
  - Ví dụ: job tính hoa hồng ngày ghi kèm unique `(user_id, date)`, chạy hai lần thì lần sau bị
    unique chặn.
- Thêm alert khi job **không** chạy (ví dụ job ghi thời điểm chạy cuối, quá hạn thì báo). Lỗi
  "không chạy" im lặng hơn lỗi "chạy trùng".
- ⚠️ Timezone và DST (giờ mùa hè) làm cron chạy lệch giờ, chạy hai lần hoặc bỏ lỡ một lần. Xem
  [22-practical-data.md](22-practical-data.md).

**Đọc**
- Laravel: [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server), [Background Tasks](https://laravel.com/docs/scheduling#background-tasks)
- Kubernetes: [CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/) (mục job creation và limitations)

**Nắm chắc khi**
- [ ] Giải thích được vì sao báo cáo ngày bị gửi hai lần sau khi scale từ 1 lên 3 pod, và 3 lớp sửa
- [ ] Nói được hệ quả của lock `withoutOverlapping` 24 giờ khi server bị kill giữa chừng

---

### Chặng 3: Senior 🔴

#### 3.1 Kafka bên trong: replication, lưu trữ, vì sao nhanh

**Vì sao cần học:** Ở vòng senior, người phỏng vấn không dừng ở "dùng Kafka thế nào" mà hỏi
"vì sao Kafka nhanh dù ghi xuống đĩa", "broker chết thì chuyện gì xảy ra", "nâng cluster lên
4.x cần làm gì". Hiểu cơ chế bên trong giúp bạn trả lời được các câu về độ bền và sự cố thay vì
chỉ đọc lại cấu hình.

**Học gì**

*Replication và ISR*
- Mỗi partition có một *leader* (nhận mọi lệnh ghi) và nhiều *follower* (liên tục chép
  dữ liệu từ leader).
- *ISR* (in-sync replicas) là tập các replica đang theo kịp leader. Follower tụt quá xa sẽ bị
  loại khỏi ISR.
- Leader chết thì Kafka chọn leader mới **trong ISR**, vì các replica này có đủ dữ liệu đã commit.
- *Unclean leader election* (mặc định tắt): nếu cả ISR đều chết, cho phép một replica tụt hậu
  lên làm leader.
  - Đổi lại: những message replica đó chưa kịp chép bị **mất**.
  - Tức là chọn giữa sẵn sàng (có leader ngay) và không mất dữ liệu (chờ replica trong ISR sống lại).
- Kafka 4.x có thêm *Eligible Leader Replicas* (ELR, KIP-966): theo dõi thêm những replica đủ an
  toàn để lên leader khi ISR co lại, nên chọn leader an toàn hơn.

*KRaft thay ZooKeeper*
- *Metadata* của cluster (có những topic nào, partition nào, leader là ai) trước đây lưu trong
  ZooKeeper, một hệ thống riêng phải vận hành song song.
- *KRaft*: metadata do một nhóm *controller* của chính Kafka quản lý, đồng thuận bằng thuật toán Raft.
- **Kafka 4.0 bỏ hẳn ZooKeeper.**
  - ⚠️ Cluster cũ còn ZooKeeper phải **chuyển sang KRaft khi đang ở 3.x** trước, rồi mới nâng lên
    4.x. Không nâng thẳng được.

*Lưu trữ trên đĩa*
- Mỗi partition là một thư mục trên đĩa của broker.
- Thư mục đó chia thành nhiều *segment* (đoạn log). Mỗi segment gồm ba file:
  - `.log`: chứa message.
  - `.index`: tra từ offset ra vị trí trong file `.log`.
  - `.timeindex`: tra từ thời gian ra offset.
- Chỉ segment mới nhất, gọi là *active segment*, được ghi thêm. Các segment cũ chỉ đọc.
- Index là *sparse* (thưa): không lưu mọi offset mà chỉ lưu cách quãng, tìm tới gần rồi đọc tuần
  tự một đoạn ngắn. Nhờ vậy index nhỏ, nằm gọn trong RAM.
- Retention và compaction làm **theo cả segment**: xoá hoặc gộp nguyên file.
  - ⚠️ Vì vậy message có thể sống lâu hơn `retention.ms` một chút: segment chỉ bị xoá khi message
    **mới nhất** trong nó đã quá hạn.

*Vì sao Kafka nhanh dù ghi xuống đĩa*
- **Sequential I/O, append-only**: chỉ ghi nối vào cuối file. Ghi tuần tự nhanh hơn ghi ngẫu nhiên
  rất nhiều, kể cả trên đĩa quay.
- **Page cache của OS** thay vì cache trong JVM heap: dữ liệu vừa ghi nằm sẵn trong RAM do hệ điều
  hành quản lý. Consumer đọc message mới thường đọc từ RAM, và không tốn GC của JVM.
- **Zero-copy** (syscall `sendfile`): dữ liệu đi thẳng từ page cache ra socket mạng, không phải chép
  qua bộ nhớ của ứng dụng.
  - ⚠️ Bật TLS thì **mất zero-copy**, vì dữ liệu phải được mã hoá trong ứng dụng trước khi gửi.
- **Batching và nén theo lô** ở mọi tầng: producer gửi lô, broker lưu nguyên lô, consumer nhận lô.
- **Broker không theo dõi ack từng message**, chỉ giữ một con số offset cho mỗi group mỗi partition.
- ⚠️ Kafka **không fsync** mỗi message theo mặc định (không ép dữ liệu xuống đĩa vật lý ngay). Độ bền
  đến từ **replication**: message đã nằm trên nhiều broker thì một máy mất điện cũng không mất.

*Tiered storage*
- *Tiered storage* (KIP-405, GA từ 3.9): segment cũ được đẩy lên object storage như S3, broker chỉ
  giữ phần dữ liệu nóng trên đĩa local.
- Lợi ích:
  - Retention dài rẻ hơn, vì object storage rẻ hơn đĩa của broker.
  - Broker nhẹ hơn khi phải thay thế, vì ít dữ liệu cần chép sang máy mới.

**Đọc**
- Kafka design: [Persistence](https://kafka.apache.org/43/design/design/#persistence), [Efficiency](https://kafka.apache.org/43/design/design/#efficiency), [Replication](https://kafka.apache.org/43/design/design/#replication), [Unclean leader election](https://kafka.apache.org/43/design/design/#unclean-leader-election-what-if-they-all-die)
- Kafka 4.3: [Implementation: Log](https://kafka.apache.org/43/implementation/log/), [KRaft](https://kafka.apache.org/43/operations/kraft/), [Tiered Storage](https://kafka.apache.org/43/operations/tiered-storage/), [ZooKeeper to KRaft migration](https://kafka.apache.org/43/getting-started/zk2kraft/)
- *Kafka: The Definitive Guide*: ch.6 (Kafka internals)

**Nắm chắc khi**
- [ ] Giải thích được trong 3 phút vì sao Kafka nhanh dù ghi xuống đĩa, kèm một chỗ tốc độ đó mất đi
- [ ] Nói được chuyện gì xảy ra với producer `acks=all` khi ISR co xuống dưới `min.insync.replicas`
- [ ] Nêu được việc phải làm trước khi nâng một cluster 3.x còn ZooKeeper lên 4.x

#### 3.2 Kafka exactly-once, transaction và zombie fencing

**Vì sao cần học:** "Kafka có exactly-once nên không lo trùng" là red flag kinh điển. Ở vòng
senior, bạn cần giải thích được exactly-once của Kafka thật sự làm gì, zombie fencing chặn
chuyện gì, và quan trọng nhất là vì sao nó **không** giúp gì khi consumer ghi vào MySQL hay gọi
API, tức đúng trường hợp của hầu hết app Laravel.

**Học gì**

*Idempotent producer chưa đủ*
- Idempotent producer (module 2.1) chỉ chống trùng do **producer retry**, và chỉ trong **một
  phiên** của producer. Producer restart là có producer id mới, broker không nhận ra bản trùng
  từ phiên cũ.
- Nó cũng không giải quyết được trùng ở phía consumer.

*Kafka transaction*
- Kafka transaction cho phép ghi vào nhiều partition và commit offset **nguyên tử**: tất cả có
  hiệu lực hoặc không cái nào có hiệu lực.
- Các bước trong code:
  1. Đặt `transactional.id`: một tên cố định cho producer, giữ nguyên qua các lần restart.
  2. `initTransactions()` một lần khi khởi động.
  3. `beginTransaction()`.
  4. Gửi message đầu ra.
  5. `sendOffsetsToTransaction()`: đưa offset của message đầu vào vào cùng transaction.
  6. `commitTransaction()`.
- Consumer ở phía sau đọc với `isolation.level=read_committed` để chỉ thấy message của transaction
  đã commit, bỏ qua message của transaction bị abort.
- Luồng *read-process-write*: đọc từ topic A, xử lý, ghi ra topic B, và commit offset của A, tất cả
  trong **cùng một transaction**. Crash giữa chừng thì cả ghi B lẫn commit offset đều bị huỷ, nên
  lần sau xử lý lại mà không ra trùng.

*Zombie fencing*
- *Zombie* là instance cũ bị coi là chết nhưng thật ra vẫn sống:
  1. Instance 1 bị GC pause dài hoặc mất mạng một lúc.
  2. Hệ thống coi nó đã chết, giao việc cho instance 2.
  3. Instance 1 tỉnh lại, không biết mình đã bị thay, tiếp tục ghi.
  4. Không có *fencing* (rào chặn) thì cả hai cùng ghi, ra trùng.
- Kafka chặn bằng *producer epoch* (số thế hệ):
  1. Instance 2 gọi `initTransactions` với **cùng `transactional.id`**.
  2. *Transaction coordinator* (broker phụ trách transaction của `transactional.id` đó) **tăng epoch** lên, và abort transaction còn dở của epoch cũ.
  3. Instance 1 ghi tiếp với epoch cũ thì bị broker từ chối, nhận `ProducerFencedException`.
- *EOS v2* (KIP-447): fencing dựa thêm vào metadata của consumer group, được truyền qua
  `sendOffsetsToTransaction`. Nhờ vậy không cần mỗi partition một `transactional.id` cố định như
  trước, số producer không tăng theo số partition.
- KIP-890 bổ sung phòng thủ phía server cho transaction treo và các lệnh ghi đến trễ.

*Giới hạn*
- ⚠️ Chỉ đúng khi **cả đầu vào và đầu ra đều là Kafka**.
  - Consumer ghi ra MySQL hay gọi API thì Kafka không kiểm soát được phía đó. Vẫn phải làm
    consumer idempotent (module 1.2), hoặc lưu offset trong DB cùng transaction (module 2.2).
- ⚠️ Consumer `read_committed` chỉ đọc tới *Last Stable Offset* (LSO): offset mà trước nó mọi
  transaction đã kết thúc. Một transaction treo không commit cũng không abort thì LSO đứng yên, và
  **consumer đứng lại** theo.

**Đọc**
- Kafka design: [Using Transactions](https://kafka.apache.org/43/design/design/#using-transactions), [Transaction protocol](https://kafka.apache.org/43/operations/transaction-protocol/)
- Confluent: [Transactions in Apache Kafka](https://www.confluent.io/blog/transactions-apache-kafka/) (mục zombie fencing), [Exactly-once Semantics are Possible](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)
- [KIP-447: Producer scalability for exactly once semantics](https://cwiki.apache.org/confluence/display/KAFKA/KIP-447%3A+Producer+scalability+for+exactly+once+semantics)

**Nắm chắc khi**
- [ ] Vẽ được kịch bản zombie producer và chỉ ra epoch chặn nó ở bước nào
- [ ] Giải thích được vì sao Kafka EOS không giúp gì khi consumer ghi vào MySQL, và thay bằng gì
- [ ] Nói được hệ quả của một transaction treo đối với consumer `read_committed`

#### 3.3 Kafka 4.x: consumer group protocol mới và share groups

**Vì sao cần học:** Rebalance là nguồn gây gián đoạn và xử lý trùng lớn nhất của consumer
Kafka, nhất là khi rolling deploy trên Kubernetes. Kafka 4.x đổi hẳn cách rebalance và thêm
share group, cho phép dùng Kafka như một task queue. Câu "rebalance hoạt động thế nào, Kafka 4.x
thay đổi gì" là câu senior, và red flag là vẫn mô tả ZooKeeper là thành phần bắt buộc.

**Học gì**

*Rebalance kiểu cũ (classic protocol)*
- Trong classic protocol, **client** tính assignment: một consumer được chọn làm leader của group
  và quyết định ai nhận partition nào. *Assignment* là bảng phân công partition cho consumer.
- Hai kiểu:

  | | Eager | Cooperative (`CooperativeStickyAssignor`) |
  |---|---|---|
  | Thu hồi | Mọi consumer trả **toàn bộ** partition rồi chia lại từ đầu | Chỉ thu hồi những partition cần chuyển |
  | Ai phải dừng | **Cả group** dừng trong lúc rebalance | Chỉ các partition bị chuyển |
  | Số vòng | Một vòng | Có thể hai vòng |

- ⚠️ Chuyển một group đang chạy từ eager sang cooperative phải rolling deploy **hai bước**: bước
  đầu khai báo cả hai assignor, bước sau mới bỏ eager. Đổi một lần thì các consumer cũ và mới
  không thống nhất được giao thức.

*Consumer group protocol mới (KIP-848)*
- **GA ở Kafka 4.0**, bật bằng `group.protocol=consumer`.
- Khác biệt chính:
  - **Broker** điều phối và tính assignment (*server-side assignor*), không phải client.
  - Không còn *barrier* đồng bộ toàn group (bước mọi consumer phải cùng dừng chờ nhau).
  - Rebalance tăng dần: consumer không liên quan tới partition đang chuyển thì **không phải dừng**.
  - Session timeout và heartbeat interval được cấu hình **phía broker**.
  - `partition.assignment.strategy` phía client không còn dùng.
- Kafka 4.3 đã log khuyến nghị chuyển khỏi classic protocol, vì classic sẽ bị deprecate.

*Static membership*
- Vẫn dùng được với protocol mới (module 2.2).
- Giải quyết rolling deploy trên Kubernetes: pod restart và quay lại trong session timeout thì
  giữ nguyên partition, không gây rebalance.
- Trade-off: consumer **chết thật** thì partition của nó treo, không ai xử lý, cho tới khi hết
  session timeout.

*Share groups (KIP-932, "Queues for Kafka")*
- Lộ trình: early access ở 4.0, preview ở 4.1, **production-ready ở 4.2**.
- Khác consumer group ở chỗ:
  - **Nhiều consumer cùng đọc một partition**. Số consumer không còn bị giới hạn bởi số partition.
  - Ack **từng record** thay vì commit một offset.
  - Broker đếm số lần giao mỗi record (để đưa poison message ra ngoài).
  - Record đang được xử lý bị khoá cho consumer đó trong một khoảng thời gian, hết hạn thì giao
    cho người khác, giống visibility timeout của SQS.
- ⚠️ **Không đảm bảo thứ tự**. Hợp cho task queue. Cần thứ tự theo key thì vẫn dùng consumer group.

| | Consumer group | Share group |
|---|---|---|
| Số consumer tối đa | Bằng số partition | Không giới hạn bởi partition |
| Đơn vị ack | Offset của partition | Từng record |
| Thứ tự | Trong partition | Không đảm bảo |
| Hợp với | Event streaming, cần thứ tự theo key | Task queue |

*Client ngoài Java*
- ⚠️ Client ngoài Java (librdkafka, tức cả php-rdkafka) hỗ trợ các tính năng mới chậm hơn client
  Java. Kiểm tra phiên bản thư viện trước khi thiết kế dựa vào chúng.

**Đọc**
- Kafka 4.3: [Consumer Rebalance Protocol](https://kafka.apache.org/43/operations/consumer-rebalance-protocol/), Design: [The Share Consumer](https://kafka.apache.org/43/design/design/#the-share-consumer), [Upgrading](https://kafka.apache.org/43/getting-started/upgrade/)
- [KIP-848](https://cwiki.apache.org/confluence/display/KAFKA/KIP-848%3A+The+Next+Generation+of+the+Consumer+Rebalance+Protocol), [KIP-932](https://cwiki.apache.org/confluence/display/KAFKA/KIP-932%3A+Queues+for+Kafka): đọc phần Motivation
- Release notes: [Kafka 4.0](https://kafka.apache.org/blog/2025/03/18/apache-kafka-4.0.0-release-announcement/), [Kafka 4.2](https://kafka.apache.org/blog/2026/02/17/apache-kafka-4.2.0-release-announcement/)

**Nắm chắc khi**
- [ ] So sánh được eager, cooperative và KIP-848 về việc ai tính assignment và ai phải dừng
- [ ] Chọn được consumer group hay share group cho 2 workload cụ thể và nói điều gì mất đi
- [ ] Giải thích được static membership giải quyết vấn đề gì của rolling deploy trên Kubernetes

#### 3.4 Vận hành Kafka

**Vì sao cần học:** Dùng Kafka trên production nghĩa là sẽ có ngày nhận alert "consumer lag
tăng liên tục" lúc nửa đêm. Người phỏng vấn senior hay đưa đúng tình huống này và nghe xem bạn
chẩn đoán có thứ tự hay không. Red flag là trả lời "thêm consumer" ngay lập tức.

**Học gì**

*Quotas*
- *Quota* là giới hạn tài nguyên cho từng client, đặt theo user hoặc client-id:
  - Số byte mỗi giây khi produce và khi fetch (đọc).
  - Tỉ lệ thời gian xử lý request trên broker.
- Vượt quota thì client bị **throttle** (broker cố ý trả lời chậm lại), **không bị từ chối**.
- Dùng để một client chạy sai không làm nghẽn cả cluster.

*Metric phải có*
- Các khái niệm trong bảng:
  - *Under-replicated partition*: partition có replica chưa theo kịp leader.
  - *Under-min-ISR*: số replica trong ISR thấp hơn `min.insync.replicas` (module 2.1).
  - *Offline partition*: partition không có leader, không đọc ghi được.
  - *Active controller*: controller đang điều hành cluster (module 3.1). Phải có đúng một.

  | Metric | Báo động khi |
  |---|---|
  | Consumer lag theo partition, lag theo thời gian | tăng đều, dồn vào một partition |
  | Under-replicated partitions | > 0 kéo dài |
  | Under-min-ISR partitions | > 0 (producer `acks=all` bị từ chối) |
  | Offline partitions | > 0 |
  | Active controller count | khác 1 |
  | Request latency, disk, network | theo ngưỡng |

*Xử lý "consumer lag tăng liên tục"*
1. **Xem lag dồn vào partition nào.** Dồn vào một partition thì nghĩa là *hot key* (module 2.1),
   thêm consumer không giúp gì.
2. **Xem thời gian xử lý mỗi message và hệ thống phía sau** (*downstream*: DB, API mà consumer gọi).
   Thường nguyên nhân là DB chậm hay API đối tác chậm chứ không phải Kafka.
3. **Xem có rebalance liên tục không** (module 2.2). Group liên tục chia lại partition thì không
   ai xử lý được gì.
4. **Chỉ thêm consumer khi còn partition rảnh.** Số consumer đã bằng số partition thì thêm nữa chỉ
   có consumer ngồi không.
5. ⚠️ **Alert trước khi retention xoá mất message.** Lag theo thời gian tiến gần `retention.ms`
   thì message chưa đọc sắp bị xoá.

*Công cụ*
- `kafka-consumer-groups.sh --describe`: xem offset, lag của từng partition và consumer nào đang giữ.
- Exporter Prometheus để đưa metric lên dashboard và alert.
- *Cruise Control*: công cụ tự cân bằng lại partition giữa các broker.

*Hệ sinh thái*
- *Schema Registry*: lưu và kiểm tra schema của message (module 2.7).
- *Kafka Connect*: chạy các connector đưa dữ liệu vào và ra Kafka.
- *Debezium*: connector CDC chạy trên Kafka Connect (module 2.6, 3.5).
- *Kafka Streams*: thư viện Java xử lý stream ngay trong ứng dụng.
- *ksqlDB*: viết xử lý stream bằng câu lệnh giống SQL.
- *MirrorMaker 2*: chép dữ liệu giữa hai cluster, ví dụ sang region khác.

**Đọc**
- Kafka 4.3: [Monitoring](https://kafka.apache.org/43/operations/monitoring/), Design: [Quotas](https://kafka.apache.org/43/design/design/#quotas), [Basic Kafka Operations](https://kafka.apache.org/43/operations/basic-kafka-operations/)
- *Kafka: The Definitive Guide*: ch.12–13 (administering, monitoring)

**Nắm chắc khi**
- [ ] Kể được quy trình xử lý "consumer lag tăng liên tục" từ lúc nhận alert tới lúc đóng sự cố
- [ ] Đặt được bộ alert tối thiểu cho một cluster Kafka production

#### 3.5 Pattern event-driven: CDC, choreography, CQRS, event sourcing

**Vì sao cần học:** Khi tách monolith Laravel thành nhiều service, hoặc cần đồng bộ MySQL sang
Elasticsearch, bạn sẽ gặp các pattern này. Người phỏng vấn senior thường hỏi "choreography hay
orchestration cho luồng đặt hàng 5 bước" và "khi nào dùng event sourcing". Điều họ muốn nghe là
bạn biết **cái giá** của từng pattern, không chỉ tên gọi.

**Học gì**

*CDC*
- *CDC* (change data capture, module 2.6) với Debezium: đọc binlog dạng row của MySQL, hoặc
  *logical decoding* của Postgres, rồi biến mỗi thay đổi dòng thành một event.
- Dùng để:
  - Đồng bộ dữ liệu sang search (Elasticsearch), cache, warehouse.
  - Làm relay cho outbox.
  - Tách monolith: service mới nhận thay đổi từ DB cũ mà không phải sửa code cũ.
- ⚠️ CDC **thẳng trên bảng nghiệp vụ** biến schema nội bộ thành *contract* (thoả thuận mà bên khác
  phụ thuộc vào). Đổi tên một cột trong bảng `orders` là làm vỡ service khác. Outbox giữ contract
  rõ hơn, vì bảng outbox chứa event được thiết kế riêng để công bố.
- ⚠️ Các điểm khó khi vận hành:
  - *Snapshot* ban đầu của bảng lớn: lần đầu phải đọc toàn bộ bảng, có thể mất hàng giờ.
  - Schema change trên bảng nguồn.
  - Lag của connector.

*Event mang gì*

| | Event notification | Event-carried state transfer |
|---|---|---|
| Nội dung | Event nhỏ, chỉ có id: "đơn 42 vừa đổi" | Event mang đủ dữ liệu cần dùng |
| Consumer làm gì | Gọi ngược API để lấy dữ liệu | Giữ một bản sao dữ liệu cục bộ |
| Ưu | Đơn giản, luôn đọc được dữ liệu mới nhất | Không phụ thuộc service nguồn đang sống |
| Nhược | Service nguồn chịu thêm tải, phải sống | Event to, bản sao có thể cũ |

*Choreography và orchestration*
- *Choreography* (biên đạo tự do): mỗi service tự nghe event và tự phản ứng, không ai điều phối
  chung.
  - Ví dụ: `OrderPlaced` → service kho tự trừ kho → phát `StockReserved` → service thanh toán tự
    charge.
- *Orchestration* (có nhạc trưởng): một *orchestrator* gửi command cho từng service theo thứ tự
  và giữ trạng thái của cả luồng.
- Chọn thế nào:
  - 2–3 bước đơn giản: choreography.
  - Nhiều bước có bù trừ (bước 4 lỗi thì phải hoàn tác bước 1–3): orchestration, vì dễ theo dõi
    luồng đang ở đâu.

*CQRS*
- *CQRS* (command query responsibility segregation): tách **model ghi** và **model đọc**.
  - Ví dụ: ghi vào bảng MySQL chuẩn hoá, đọc từ một bảng tổng hợp hoặc Elasticsearch được cập
    nhật qua event.
- Read model là eventual: cập nhật sau một lúc.
  - ⚠️ User vừa ghi xong, đọc lại ngay có thể **không thấy** thay đổi của mình.
- CQRS **không bắt buộc** đi cùng event sourcing.

*Event sourcing*
- *Event sourcing*: không lưu trạng thái hiện tại, mà lưu **chuỗi event** làm nguồn sự thật.
  Trạng thái hiện tại được tính bằng cách áp lần lượt các event.
  - Ví dụ: tài khoản không lưu `balance = 500`, mà lưu `Deposited 1000`, `Withdrawn 500`.
- Cơ chế:
  - *Snapshot*: lưu trạng thái tính sẵn tại một thời điểm, để không phải replay từ đầu mỗi lần.
  - *Replay*: chạy lại các event để dựng *projection* (bảng đọc được tính từ event).
  - ⚠️ Handler có side effect (gửi email, gọi API) **không được chạy lại** khi replay.
- Cái giá:
  - Versioning event và *upcasting* (chuyển event format cũ sang format mới khi đọc).
  - Query khó: muốn hỏi gì cũng phải có projection.
  - Xoá dữ liệu cá nhân khó (GDPR), vì event không được sửa. Cách thường dùng là *crypto-shredding*:
    mã hoá dữ liệu cá nhân bằng key riêng của từng người, cần xoá thì xoá key.
- ⚠️ Chỉ đáng khi domain thật sự cần lịch sử, ví dụ *ledger* (sổ cái kế toán). Với CRUD thông
  thường thì cái giá lớn hơn lợi ích.

*Saga*
- *Saga* là chuỗi transaction cục bộ ở nhiều service, mỗi bước có một bước bù trừ khi lỗi.
  Chi tiết ở [14-distributed-systems.md](14-distributed-systems.md).

**Đọc**
- Debezium: [Tutorial](https://debezium.io/documentation/reference/stable/tutorial.html), [MySQL connector](https://debezium.io/documentation/reference/stable/connectors/mysql.html) (phần snapshot)
- Martin Fowler: [CQRS](https://martinfowler.com/bliki/CQRS.html), [Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)
- microservices.io: [Saga](https://microservices.io/patterns/data/saga.html), [Event sourcing](https://microservices.io/patterns/data/event-sourcing.html)
- DDIA ch.11: *Databases and Streams*, *Event Sourcing*

**Nắm chắc khi**
- [ ] Chọn được choreography hay orchestration cho luồng đặt hàng 5 bước và bảo vệ lựa chọn
- [ ] Nêu được 3 lý do **không** dùng event sourcing cho một hệ CRUD thông thường
- [ ] Giải thích được vì sao CDC thẳng trên bảng nghiệp vụ nguy hiểm hơn outbox về lâu dài

#### 3.6 Job dài, batch, stream, workflow engine

**Vì sao cần học:** "Import 10 triệu dòng", "tính lại hoa hồng cả tháng", "gửi email cho toàn
bộ user" là việc có ở mọi hệ Laravel, và viết thành một job lớn thì chắc chắn gãy. Ở mức senior,
bạn cần biết chia nhỏ, checkpoint, và khi nào `Bus::batch` là đủ, khi nào cần workflow engine
như Temporal.

**Học gì**

*Job dài*
- Ba kỹ thuật:
  - **Chia nhỏ**: thay vì một job xử lý 10 triệu bản ghi, tạo nhiều job, mỗi job một batch 1.000
    bản ghi. Một job lỗi chỉ phải chạy lại 1.000 bản ghi.
  - **Checkpoint**: lưu id cuối cùng đã xử lý. Job chết thì chạy lại từ đó thay vì từ đầu.
    - Duyệt theo keyset (`WHERE id > ? ORDER BY id LIMIT 1000`), không dùng `OFFSET`, vì `OFFSET`
      càng sâu càng chậm. Xem module 2.3 của [03-database-sql.md](03-database-sql.md).
  - **Graceful shutdown**: nhận SIGTERM thì làm xong batch hiện tại, lưu checkpoint rồi mới thoát.
- ⚠️ Job chạy lâu hơn timeout của queue thì bị giao lại và **chạy song song với chính nó**. Tuỳ
  broker, timeout đó là visibility timeout (SQS), `retry_after` (Laravel) hay consumer timeout
  (RabbitMQ).

*Batch và stream*
- *Batch*: xử lý một tập dữ liệu có giới hạn theo lịch, ví dụ mỗi đêm tổng hợp doanh thu hôm qua.
- *Stream*: xử lý liên tục một luồng dữ liệu không có điểm kết thúc, ví dụ đếm đơn theo từng phút
  ngay khi đơn tới.

  | | Batch | Stream |
  |---|---|---|
  | Dữ liệu | tập có giới hạn, theo lịch | luồng vô hạn |
  | Độ trễ | phút tới giờ | ms tới giây |
  | Độ phức tạp | thấp, dễ chạy lại | window, late event, state, watermark |
  | Công cụ | cron + SQL, Spark, dbt | Kafka Streams, Flink |

- Các khái niệm của stream trong bảng:
  - *Window*: gom sự kiện theo khung thời gian, ví dụ "mỗi 5 phút".
  - *Late event*: sự kiện tới muộn sau khi khung của nó đã đóng.
  - *State*: dữ liệu consumer phải nhớ giữa các sự kiện, ví dụ bộ đếm.
  - *Watermark*: mốc "coi như mọi sự kiện trước thời điểm này đã tới", dùng để quyết định khi nào
    đóng một window.

*Workflow engine*
- *Workflow engine* là hệ thống chạy các luồng nhiều bước kéo dài (phút tới tháng), tự lưu trạng
  thái, nên luồng tiếp tục được sau khi server crash.
- **Temporal**:
  - Workflow viết bằng code thường.
  - Engine lưu lịch sử từng bước và *resume* (chạy tiếp) sau crash.
  - Hỗ trợ timer dài (chờ 30 ngày rồi làm tiếp) và bù trừ khi lỗi.
  - ⚠️ Code workflow phải *deterministic*: chạy lại với cùng lịch sử phải ra cùng quyết định. Không
    gọi `rand()`, `now()` hay API trực tiếp trong workflow, những việc đó phải đưa vào *activity*.
  - Có SDK PHP.
- **Airflow**: chạy *DAG* (đồ thị các bước có thứ tự phụ thuộc) cho pipeline dữ liệu. Không dành cho
  luồng giao dịch cần độ trễ thấp.
- Khác: AWS Step Functions, Camunda.
- Khi nào `Bus::batch` của Laravel là đủ và khi nào cần workflow engine:
  - Batch đủ: các job độc lập, chạy trong vài phút tới vài giờ, chỉ cần biết "xong hết chưa".
  - Cần engine: nhiều bước phụ thuộc nhau, chờ lâu (ngày, tuần), cần bù trừ khi lỗi giữa chừng.

**Đọc**
- DDIA ch.10 (batch) và ch.11 (stream): phần *Reasoning About Time*
- Temporal: [Workflows](https://docs.temporal.io/workflows) (mục deterministic constraints), [PHP SDK](https://docs.temporal.io/develop/php)
- Laravel: [Job Batching](https://laravel.com/docs/queues#job-batching) cho job dài chia nhỏ

**Nắm chắc khi**
- [ ] Thiết kế được job xử lý 10 triệu bản ghi: chia nhỏ, checkpoint, chạy lại an toàn, theo dõi tiến độ
- [ ] Nói được khi nào Laravel batch là đủ và khi nào cần workflow engine

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Vì sao cần message queue? Cho ví dụ việc nên và không nên đẩy vào queue.** (1.1)
- Ý phải có: decouple, load leveling, việc chậm ra background, retry; việc cần kết quả ngay thì gọi đồng bộ
- Điểm cộng: nói được cái giá (vận hành, eventual consistency, trùng và thứ tự)

**2. Queue và topic khác nhau thế nào?** (1.1)
- Ý phải có: mỗi message một consumer so với mỗi subscriber một bản
- Điểm cộng: Kafka gộp cả hai qua consumer group; SNS + SQS

**3. At-most-once, at-least-once, exactly-once khác nhau thế nào? Hệ thống của bạn dùng loại nào?** (1.2)
- Ý phải có: thời điểm ack so với lúc xử lý; thực tế là at-least-once + idempotent
- Red flag: "Kafka có exactly-once nên không lo trùng"

**4. DLQ là gì, dùng để làm gì?** (1.3)
- Ý phải có: chỗ chứa message hết lượt retry; cần alert và redrive
- Điểm cộng: poison message làm crash consumer phải đếm ở broker; lỗi vĩnh viễn thì vào DLQ ngay

**5. Laravel: dispatch job trong DB transaction có vấn đề gì?** (1.4)
- Ý phải có: worker có thể chạy trước khi commit, không thấy dữ liệu hoặc xử lý đơn đã rollback; dùng `afterCommit`
- Điểm cộng: `afterCommit` vẫn mất job nếu process chết ngay sau commit, nên cần outbox

**6. Deploy code mới nhưng worker vẫn chạy logic cũ. Vì sao?** (1.4, 2.8)
- Ý phải có: worker là process chạy lâu, code đã nạp trong memory; `queue:restart` hoặc `horizon:terminate`
- Điểm cộng: job cũ trong queue được serialize theo class cũ, deploy phải tương thích ngược

### 🟡 Mid

**7. Làm sao đảm bảo message không bị xử lý hai lần?** (1.2)
- Ý phải có: giả định at-least-once; INSERT `event_id` vào bảng unique trong cùng transaction với thay đổi nghiệp vụ
- Điểm cộng: side effect ngoài thì idempotency key; message id do producer sinh
- Red flag: `SELECT` kiểm tra đã xử lý chưa rồi mới làm

**8. Tạo đơn xong cần gửi email và trừ kho. Làm sao ghi DB và gửi message luôn đi cùng nhau?** (2.6)
- Ý phải có: dual write sai ở mọi thứ tự; transactional outbox
- Điểm cộng: outbox là at-least-once; bẫy poll theo id tự tăng; CDC; database queue driver cùng connection

**9. Kafka đảm bảo thứ tự thế nào? Chuyện gì xảy ra khi tăng số partition?** (2.1)
- Ý phải có: thứ tự trong partition; key quyết định partition; tăng partition đổi mapping
- Điểm cộng: quy trình tăng partition an toàn (topic mới, chuyển dần, hoặc dừng producer cho tới khi consumer đọc hết)

**10. Topic 6 partition, chạy 10 consumer trong một group. Chuyện gì xảy ra?** (2.1, 3.3)
- Ý phải có: 4 consumer ngồi không
- Điểm cộng: share group (Kafka 4.2) cho phép nhiều consumer hơn partition nhưng mất thứ tự

**11. `acks=all` có đảm bảo không mất dữ liệu không?** (2.1)
- Ý phải có: cần `min.insync.replicas=2` với `replication.factor=3`; unclean leader election tắt
- Điểm cộng: producer phải xử lý callback lỗi; fsync không phải nguồn độ bền chính

**12. Vì sao consumer Kafka hay xử lý trùng? Kể ít nhất hai nguyên nhân.** (2.2)
- Ý phải có: crash sau xử lý trước commit; vượt `max.poll.interval.ms` bị rebalance
- Điểm cộng: producer retry khi chưa bật idempotence; retry topic; sửa bằng INSERT `event_id` trước khi xử lý

**13. Khi nào chọn Kafka, khi nào RabbitMQ, khi nào SQS?** (2.5)
- Ý phải có: replay, nhiều consumer group, retention dài thì Kafka; task queue, định tuyến, retry có delay thì RabbitMQ; trên AWS ít vận hành thì SQS
- Điểm cộng: vài nghìn job/ngày thì bảng DB + `SKIP LOCKED` là đủ; đội có người vận hành Kafka không
- Red flag: "Kafka nhanh hơn nên chọn Kafka"

**14. Prefetch trong RabbitMQ là gì, đặt bao nhiêu?** (2.3)
- Ý phải có: số message giao chưa ack; việc nặng không đều thì nhỏ, việc nhẹ đều thì lớn
- Điểm cộng: consumer chết thì cả prefetch bị giao lại; liên quan tới consumer timeout

**15. Visibility timeout của SQS là gì, cạm bẫy khi job chạy lâu?** (2.4)
- Ý phải có: message ẩn trong khoảng đó; quá hạn chưa xoá thì hiện lại và consumer khác nhận
- Điểm cộng: `ChangeMessageVisibility` như heartbeat; Laravel dùng visibility timeout thay cho `retry_after` với SQS

**16. Laravel: `retry_after` và `timeout` khác nhau thế nào?** (2.8)
- Ý phải có: `retry_after` là lúc queue coi job treo và giao lại; `timeout` là lúc worker tự giết job; `timeout` phải ngắn hơn
- Điểm cộng: `tries` mặc định 1; `WithoutOverlapping` và `release()` tiêu attempt; `backoff` dạng mảng
- Red flag: đặt `timeout` lớn hơn `retry_after` "cho chắc"

**17. `ShouldBeUnique` và `WithoutOverlapping` khác nhau thế nào?** (2.8)
- Ý phải có: unique chặn **dispatch** khi đã có job cùng id trong queue; without overlapping chặn **chạy song song** cùng key
- Điểm cộng: cả hai dựa trên cache lock, không thay idempotency; `DebounceFor` cho trường hợp chỉ cần bản cuối

**18. Chạy cron trên nhiều instance thế nào để không chạy trùng?** (2.9)
- Ý phải có: lock (`onOneServer`), scheduler riêng, hoặc scheduler ngoài đẩy vào queue
- Điểm cộng: lock chỉ giảm trùng, job vẫn phải idempotent; cache dùng chung; lock 24 giờ của `withoutOverlapping`; alert khi job không chạy
- Red flag: "dùng Redis lock là xong"

**19. Thay đổi schema event mà không làm vỡ consumer thế nào?** (2.7)
- Ý phải có: chỉ thêm field optional có default; consumer bỏ qua field lạ; breaking thì phát song song v1/v2
- Điểm cộng: Schema Registry kiểm tra lúc produce; message cũ sống lâu hơn code

### 🔴 Senior

**20. Vì sao Kafka nhanh dù ghi xuống đĩa?** (3.1)
- Ý phải có: sequential I/O, page cache, zero-copy, batching và nén, broker không theo dõi từng message
- Điểm cộng: TLS mất zero-copy; độ bền từ replication không phải fsync; tiered storage

**21. Exactly-once của Kafka hoạt động thế nào? Zombie fencing là gì?** (3.2)
- Ý phải có: idempotent producer + transaction + `read_committed`; `transactional.id` và epoch chặn producer cũ
- Điểm cộng: EOS v2 dựa vào group metadata; transaction treo chặn LSO; chỉ đúng Kafka→Kafka

**22. Rebalance hoạt động thế nào? Kafka 4.x thay đổi gì?** (2.2, 3.3)
- Ý phải có: eager dừng cả group; cooperative chỉ thu hồi phần cần chuyển; KIP-848 để broker tính assignment, GA ở 4.0
- Điểm cộng: static membership cho rolling deploy; client librdkafka có thể chưa theo kịp
- Red flag: vẫn mô tả ZooKeeper là thành phần bắt buộc

**23. Consumer gửi email xác nhận bị gửi trùng vài lần mỗi tuần. Nguyên nhân và cách sửa?** (1.2, 2.2)
- Ý phải có: crash sau gửi trước commit; rebalance do `max.poll.interval.ms`; producer retry
- Điểm cộng: INSERT `event_id` unique **trước** khi gửi (chấp nhận có thể mất) hoặc gửi rồi ghi (chấp nhận trùng), nói rõ chọn bên nào; nhà cung cấp email có idempotency key thì dùng
- Red flag: "kiểm tra bảng đã gửi chưa rồi mới gửi" mà không dựa vào unique constraint

**24. Consumer lag tăng liên tục. Bạn làm gì?** (3.4)
- Ý phải có: xem lag dồn partition nào, thời gian xử lý và downstream, rebalance liên tục; thêm consumer chỉ khi còn partition rảnh
- Điểm cộng: lag theo thời gian; alert trước retention; hot key; xử lý theo lô
- Red flag: "thêm consumer" ngay lập tức

**25. Worker RabbitMQ xử lý video 10–40 phút. Thỉnh thoảng bị xử lý hai lần, và một worker ôm nhiều job trong khi worker khác rảnh.** (2.3)
- Ý phải có: prefetch lớn → đặt 1; vượt consumer timeout thì message bị giao lại
- Điểm cộng: tách "nhận" và "xử lý" (ack sớm, trạng thái job trong DB), chia job nhỏ; kết quả ghi idempotent theo `video_id`; hành vi timeout đổi ở 4.3

**26. Relay outbox kiểu polling thỉnh thoảng bỏ sót event dù dòng vẫn nằm trong bảng.** (2.6)
- Ý phải có: đọc theo `id > last_seen_id` trong khi thứ tự commit khác thứ tự id
- Điểm cộng: dùng cờ `published_at`, đọc dòng cũ hơn một khoảng an toàn, hoặc CDC theo thứ tự commit

**27. Cập nhật số dư qua Kafka, thứ tự rất quan trọng. Thiết kế thế nào?** (2.7, 3.2)
- Ý phải có: key `account_id`; retry tại chỗ không qua retry topic; idempotent bằng `event_id` trong cùng transaction
- Điểm cộng: version để phát hiện sai thứ tự; poison message chặn một tài khoản thì cần quy trình xử lý tay; alert

**28. Laravel worker gọi API thanh toán, thấy cùng một đơn bị charge hai lần.** (2.8, 1.2)
- Ý phải có: job chạy quá `retry_after`/visibility timeout nên bị giao lại; `timeout` không ngắn hơn `retry_after`
- Điểm cộng: idempotency key sang cổng thanh toán; `WithoutOverlapping` theo `order_id` giảm rủi ro nhưng không thay idempotency; kiểm tra trạng thái giao dịch trước khi retry

**29. Choreography hay orchestration cho luồng đặt hàng 5 bước? Khi nào dùng event sourcing?** (3.5)
- Ý phải có: nhiều bước có bù trừ thì orchestration dễ theo dõi; event sourcing chỉ khi domain cần lịch sử
- Điểm cộng: workflow engine (Temporal); cái giá của event sourcing (versioning, GDPR, projection)

**30. Consumer Kafka viết bằng PHP chạy vài giờ thì chậm dần rồi chết. Vì sao?** (2.8)
- Ý phải có: memory leak và state tích luỹ trong process chạy lâu; connection DB chết
- Điểm cộng: tự thoát sau N message/thời gian và để Supervisor bật lại; theo dõi memory; xử lý rebalance callback và commit trước khi thoát

---

## Bài tập tự làm

1. **Outbox relay.** Thiết kế bảng `outbox` (MySQL 8.4) và viết pseudo-code cho relay polling chạy được với 2 instance cùng lúc mà không đảo thứ tự event của cùng một `aggregate_id`. Chỉ rõ chỗ nào vẫn có thể gửi trùng.
2. **Đường mất message.** Liệt kê mọi đường mất hoặc trùng message trong luồng: Laravel dispatch job → Redis queue → worker → gọi API thanh toán. Với mỗi đường, nêu cách chặn.
3. **Tăng partition.** Topic Kafka 12 partition, key là `user_id`, cần tăng lên 24 partition mà không phá thứ tự sự kiện của từng user. Mô tả quy trình chuyển đổi.
4. **So sánh retry.** Lập bảng thiết kế retry 3 lần với delay 1 phút, 10 phút, 1 giờ trên:
   - Kafka
   - RabbitMQ
   - SQS
   - Laravel Queue (Redis driver)
5. **Worker bằng DB.** Viết (bằng ngôn ngữ bạn chọn) một worker đọc từ bảng `jobs` với `FOR UPDATE SKIP LOCKED`. Cần có:
   - Thu hồi job treo
   - Retry có backoff
   - Graceful shutdown khi nhận SIGTERM
6. **PHP/Laravel.** Trong một project Laravel:
   - Viết một job chạy 90 giây với `retry_after = 60`, quan sát job chạy hai lần, rồi sửa cấu hình.
   - Viết một consumer idempotent: gửi cùng một event 3 lần song song, chứng minh chỉ một lần có hiệu lực.
   - Cấu hình Supervisor cho `queue:work` với `--max-jobs`, `--max-time` và `stopwaitsecs` hợp lý cho job dài nhất 5 phút.

> Nộp bài vào đây để được review.
