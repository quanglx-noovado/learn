# 12. Messaging, event-driven, background job

> [← Mục lục](README.md) · Phạm vi: message queue nói chung, Kafka, RabbitMQ, SQS/SNS, Redis Streams, NATS, database làm queue, các pattern outbox/inbox/CDC/CQRS/event sourcing, và cron/batch/background job.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Khái niệm chung**
- [ ] 🟢 Vì sao cần queue: decouple, làm mượt đỉnh tải, việc chậm ra background, retry
- [ ] 🟢 Queue (point-to-point) vs topic (pub/sub)
- [ ] 🟡 Push vs pull
- [ ] Delivery semantics: at-most-once, at-least-once, exactly-once ⚠️
- [ ] Idempotent consumer: bảng processed_messages, unique key, upsert, version
- [ ] Ack/nack, retry có backoff, DLQ, poison message
- [ ] 🟡 Ordering và cái giá của nó
- [ ] 🟡 Backpressure
- [ ] 🟡 Message size, claim-check pattern
- [ ] 🟡 Message schema, versioning, tương thích ngược/xuôi
- [ ] 🟡 Event vs command vs query

**Kafka** 🟡
- [ ] Distributed commit log; broker, topic, partition, offset, consumer group
- [ ] Partition và thứ tự; key → partition; tăng partition phá thứ tự ⚠️; hot partition
- [ ] Producer: `acks`, idempotent producer, batching, nén, callback lỗi
- [ ] Replication, ISR, `min.insync.replicas`, unclean leader election 🔴, KRaft 🔴
- [ ] 🔴 Segment, index file, page cache, sequential I/O, zero-copy: vì sao Kafka nhanh
- [ ] Consumer: poll, commit offset, auto commit ⚠️, `auto.offset.reset` ⚠️, lag
- [ ] 🟡 `__consumer_offsets`, group coordinator
- [ ] Rebalance, `max.poll.interval.ms` ⚠️; 🔴 static membership; 🔴 cooperative sticky assignor
- [ ] 🟡 Log compaction, tombstone, use case của compacted topic
- [ ] 🔴 Exactly-once: transaction, `read_committed`, giới hạn
- [ ] Retry topic, DLQ tự dựng, mất thứ tự khi retry
- [ ] 🔴 Quotas; monitoring (lag, under-replicated partitions, offline partitions)
- [ ] 🟡 Schema Registry, Kafka Connect, Debezium, Kafka Streams

**RabbitMQ** 🟡
- [ ] Exchange types (direct, topic, fanout, headers), binding, routing key, default exchange
- [ ] Ack thủ công, nack/reject, requeue, redelivered
- [ ] Prefetch (`basic.qos`)
- [ ] 🟡 Publisher confirms, `mandatory` flag
- [ ] DLX, TTL, delayed message
- [ ] Durable queue, persistent message
- [ ] 🔴 Quorum queue, lazy queue, stream, single active consumer
- [ ] ⚠️ Khi nào RabbitMQ mất message

**Cloud và lựa chọn khác**
- [ ] 🟡 SQS standard vs FIFO (message group id, deduplication id)
- [ ] 🟡 Visibility timeout ⚠️, long polling, DLQ + redrive
- [ ] 🟡 SNS fan-out sang SQS, filter policy
- [ ] 🟡 Redis Streams, Redis list làm queue, Redis Pub/Sub
- [ ] 🔴 NATS core và JetStream (đại ý)
- [ ] 🟡 Database làm queue: `SELECT ... FOR UPDATE SKIP LOCKED`
- [ ] Bảng so sánh Kafka / RabbitMQ / SQS / Redis Streams

**Pattern**
- [ ] 🟡 Transactional outbox: bảng, relay polling vs CDC, dọn outbox, thứ tự ⚠️
- [ ] 🟡 Inbox pattern
- [ ] 🔴 CDC với Debezium
- [ ] 🟡 Event notification vs event-carried state transfer
- [ ] 🔴 Choreography vs orchestration
- [ ] 🔴 CQRS; event sourcing (snapshot, replay, cái giá)
- [ ] 🔴 Saga (chi tiết ở [14-distributed-systems.md](14-distributed-systems.md))

**Background job, scheduler, batch**
- [ ] 🟡 Cron trên nhiều instance: chạy trùng, lock, leader election
- [ ] 🟡 Job dài: checkpoint, resume, chia nhỏ
- [ ] 🟡 Batch processing vs stream processing
- [ ] 🔴 Workflow engine: Temporal, Airflow (đại ý)
- [ ] Đối chiếu Laravel queue, Spring Kafka/AMQP, Go consumer

## Chi tiết

### Khái niệm chung

- [ ] Vì sao cần queue
  - **Decouple**: producer không cần biết ai tiêu thụ, consumer chết thì producer vẫn chạy
  - **Làm mượt đỉnh tải** (load leveling): 10.000 request/giây đổ vào, worker xử lý 500/giây
    đều đặn, queue giữ phần dư
  - **Việc chậm ra background**: gửi email, resize ảnh, gọi API bên thứ ba, không bắt user chờ
  - **Retry** khi lỗi tạm thời, không mất việc
  - Cái giá: thêm một hệ thống phải vận hành, eventual consistency, debug khó hơn
    (một luồng nghiệp vụ nằm rải rác ở nhiều consumer), phải lo trùng và thứ tự
  - ⚠️ Không phải việc gì cũng nên đẩy qua queue. User cần kết quả ngay (kiểm tra số dư
    trước khi thanh toán) thì gọi đồng bộ
- [ ] Queue vs topic
  - **Queue (point-to-point)**: mỗi message được **một** consumer xử lý. Nhiều worker chia việc
  - **Topic (pub/sub)**: mỗi subscriber nhận **một bản** của mọi message
  - Kafka gộp cả hai qua consumer group; RabbitMQ làm pub/sub bằng fanout exchange tới nhiều
    queue; AWS tách thành SNS (pub/sub) + SQS (queue)
- [ ] Push vs pull
  - **Push** (RabbitMQ, SNS): broker đẩy message tới consumer. Độ trễ thấp, nhưng broker
    phải biết consumer chịu được bao nhiêu → cần prefetch/flow control
  - **Pull** (Kafka, SQS): consumer tự lấy khi sẵn sàng. Backpressure tự nhiên, dễ gom lô,
    nhưng phải polling (long polling để khỏi tốn request rỗng)
- [ ] Delivery semantics
  - **At-most-once**: ack/commit trước khi xử lý. Có thể mất, không trùng
  - **At-least-once**: ack sau khi xử lý. Không mất, có thể trùng. **Mặc định thực tế**
  - **Exactly-once**: mỗi message có hiệu ứng đúng một lần
  - ⚠️ "Exactly-once" thường chỉ đúng trong phạm vi một hệ thống (Kafka→Kafka, SQS FIFO trong
    cửa sổ dedup), không đúng từ đầu đến cuối. Câu trả lời chuẩn: **at-least-once + consumer
    idempotent = effectively-once**
  - Vì sao không có exactly-once đầu cuối: consumer xử lý xong, chết trước khi ack → broker
    không thể biết việc đã làm hay chưa (bài toán hai vị tướng, xem 14)
- [ ] Idempotent consumer: các cách cài

  | Cách | Cơ chế | Hợp khi | Nhược điểm |
  |---|---|---|---|
  | Bảng `processed_messages` | `INSERT message_id` cùng transaction với thay đổi nghiệp vụ; trùng thì unique violation → bỏ qua | side effect nằm trong cùng DB | bảng phình, cần dọn theo thời gian; không bảo vệ side effect ngoài DB |
  | Unique key nghiệp vụ | ví dụ `UNIQUE(order_id)` trong bảng `invoices` | có khoá tự nhiên | không phải việc nào cũng có khoá tự nhiên |
  | Upsert | `INSERT ... ON CONFLICT DO UPDATE` / `ON DUPLICATE KEY UPDATE`; set giá trị tuyệt đối | message mang trạng thái ("status=paid") | không dùng được cho phép cộng dồn ("+100") |
  | Version / sequence | chỉ áp dụng nếu `event.version > row.version` | cập nhật trạng thái có thứ tự | cần producer sinh version tăng dần theo entity |

  ```sql
  BEGIN;
  INSERT INTO processed_messages(message_id, processed_at) VALUES ('evt-42', now());
  -- nếu dòng trên lỗi unique violation → ROLLBACK, ack message, bỏ qua
  UPDATE accounts SET balance = balance + 100 WHERE id = 7;
  COMMIT;  -- sau đó mới ack message
  ```
  - ⚠️ Side effect ngoài DB (gửi email, gọi API thanh toán) không nằm trong transaction.
    Cách giảm thiểu: truyền idempotency key sang API bên kia (Stripe có `Idempotency-Key`);
    với email thì chấp nhận xác suất trùng nhỏ, hoặc ghi "đã gửi" trước rồi gửi (chấp nhận mất)
  - ⚠️ "Check rồi mới xử lý" (`SELECT` xem đã xử lý chưa, rồi xử lý) không an toàn khi hai
    consumer nhận cùng message song song. Phải dựa vào unique constraint
  - ⚠️ Message id phải do **producer** sinh và ổn định qua retry. Id do broker sinh (SQS
    `MessageId`) sẽ khác nếu producer gửi lại
- [ ] Ack/nack
  - Ack: báo đã xử lý xong, broker xoá (RabbitMQ, SQS) hoặc tiến offset (Kafka)
  - Nack/reject: báo lỗi; requeue để thử lại, hoặc không requeue để vào DLQ
  - ⚠️ Nack + requeue ngay lập tức với lỗi cố định = vòng lặp nóng đốt CPU
- [ ] Retry với backoff
  - Phân loại lỗi: **tạm thời** (timeout, 503, deadlock) thì retry; **vĩnh viễn** (validation,
    404, parse lỗi) thì đẩy DLQ ngay, retry vô ích
  - Exponential backoff + jitter (1s, 2s, 4s, 8s... cộng ngẫu nhiên), có trần số lần
  - Retry tại chỗ (sleep trong consumer) chặn cả queue/partition; retry qua queue trễ thì
    không chặn nhưng mất thứ tự
- [ ] DLQ (dead letter queue)
  - Chỗ chứa message đã hết lượt retry. Phải có: alert khi DLQ có message, công cụ xem và
    **redrive** (đẩy lại) sau khi sửa bug
  - Lưu kèm metadata: lỗi cuối, số lần thử, queue gốc, thời điểm
  - ⚠️ DLQ không ai nhìn = mất message một cách có tổ chức
- [ ] Poison message
  - Message luôn làm consumer lỗi (JSON hỏng, field thiếu, bug với dữ liệu lạ)
  - Không giới hạn retry thì chặn cả partition (Kafka) hoặc quay vòng mãi (RabbitMQ requeue)
  - ⚠️ Poison message làm **consumer crash** (không phải exception bắt được, mà OOM hay segfault)
    thì không bao giờ tới được đoạn code đếm retry. Cần đếm ở phía broker: SQS
    `maxReceiveCount`, RabbitMQ quorum queue delivery limit
- [ ] Ordering
  - Thứ tự toàn cục = một partition/một queue + một consumer = không scale
  - Thường chỉ cần **thứ tự theo entity** (theo `order_id`, `account_id`): Kafka key,
    SQS FIFO message group, RabbitMQ consistent hash exchange hoặc single active consumer
  - Cái giá: song song tối đa = số partition/group; một message lỗi chặn cả nhóm phía sau
  - Thay thế: không cần thứ tự nếu consumer **chịu được sai thứ tự** (dùng version, bỏ event
    cũ hơn trạng thái hiện tại; hoặc event chỉ là tín hiệu, consumer đọc lại trạng thái mới
    nhất từ nguồn)
- [ ] Backpressure
  - Producer nhanh hơn consumer: queue dài ra → tăng độ trễ, tốn bộ nhớ/đĩa broker, có thể
    chạm giới hạn và bị chặn hoặc drop
  - RabbitMQ: memory/disk alarm chặn publisher toàn broker. Kafka: disk đầy, hoặc message cũ
    bị retention xoá trước khi kịp đọc ⚠️
  - Cách xử lý: scale consumer, giới hạn tốc độ producer, load shedding ở đầu vào, theo dõi
    queue depth/lag và cảnh báo sớm
- [ ] Message size
  - Broker tối ưu cho message nhỏ (vài KB). Kafka mặc định giới hạn khoảng 1 MB mỗi message
    (`message.max.bytes`); SQS có giới hạn payload (kiểm tra lại, AWS từng nâng giới hạn)
  - **Claim-check pattern**: lưu payload lớn vào S3, message chỉ chứa đường dẫn. Nhớ vòng đời
    object (xoá khi nào)
- [ ] Message schema và versioning
  - Envelope chuẩn: `event_id`, `event_type`, `version`, `occurred_at`, `producer`,
    `correlation_id`/`trace_id`, `payload`
  - **Backward compatible** (consumer mới đọc được message cũ) và **forward compatible**
    (consumer cũ đọc được message mới). An toàn: thêm field optional/có default.
    Nguy hiểm: xoá field, đổi kiểu, đổi nghĩa, đổi tên
  - Đổi breaking: phát song song `v1` và `v2` (hoặc topic mới), chuyển consumer dần, rồi bỏ `v1`
  - Consumer phải **bỏ qua field lạ**, không fail
  - JSON dễ nhưng không có kiểm soát schema; Avro/Protobuf + Schema Registry kiểm tra tương
    thích lúc produce
  - ⚠️ Message trong queue sống lâu hơn code: deploy producer mới trong khi còn message cũ,
    replay Kafka từ 3 tháng trước. Consumer phải đọc được mọi version còn tồn tại
- [ ] Event vs command vs query

  | | Event | Command | Query |
  |---|---|---|---|
  | Nghĩa | "đã xảy ra" | "hãy làm" | "cho tôi biết" |
  | Tên | quá khứ: `OrderPlaced` | mệnh lệnh: `SendInvoice` | `GetOrderStatus` |
  | Người nhận | 0..n, producer không biết là ai | đúng 1 handler | 1, cần trả lời |
  | Từ chối được? | không, đã xảy ra rồi | được | — |
  | Kênh hợp | topic/pub-sub | queue | thường gọi đồng bộ (HTTP/gRPC) |

  - ⚠️ "Event" trá hình command (`OrderPlacedSoPleaseSendEmail`) tạo coupling ngầm: producer
    thực ra đang phụ thuộc vào một consumer cụ thể

### Kafka

Nếu JD có ghi Kafka thì phần này sẽ bị hỏi sâu. Nếu không, nắm mục "Mô hình" và
"Consumer" là đủ.

**Mô hình**
- [ ] Kafka là một **distributed commit log**: message được ghi nối tiếp vào cuối log và
      **không bị xoá khi đọc**. Đây là khác biệt gốc so với queue truyền thống
- [ ] Các khái niệm: broker, topic, partition, offset, producer, consumer, consumer group
- [ ] Mỗi partition là một log có thứ tự; offset là số thứ tự của message trong partition đó
- [ ] Retention: giữ theo thời gian (`retention.ms`, mặc định 7 ngày) hoặc theo dung lượng.
      Consumer có thể tua lại offset để đọc lại
- [ ] Ví dụ trực quan một topic có 3 partition và hai consumer group:

  ```text
  topic: orders (3 partition)

  P0: [0][1][2][3][4][5]      ◄── group "email":   consumer A (đang ở offset 4)
  P1: [0][1][2][3]            ◄── group "email":   consumer B (đang ở offset 2)
  P2: [0][1][2][3][4]         ◄── group "email":   consumer B (đang ở offset 5, đã đọc hết)

  Group "inventory" đọc CÙNG topic đó, với offset riêng của nó.
  Hai group không ảnh hưởng nhau: mỗi group nhận đủ mọi message.
  ```

  - **Trong một group**, mỗi partition chỉ giao cho một consumer, nên các consumer
    trong group chia nhau công việc (giống queue)
  - **Giữa các group**, mỗi group nhận toàn bộ message (giống pub/sub)
  - Kafka làm được cả hai kiểu nhờ cơ chế này

**Partition và thứ tự**
- [ ] Thứ tự chỉ được đảm bảo **trong một partition**, không có thứ tự toàn topic
- [ ] Message có key thì đi vào partition `hash(key) % số_partition`; không có key thì được
      rải đều (sticky partitioner)
- [ ] Ví dụ: các sự kiện của đơn hàng `#123` là `created`, `paid`, `shipped`
  - Dùng `order_id` làm key: cả ba vào cùng partition, nên consumer nhận đúng thứ tự
  - Không dùng key: ba sự kiện có thể rơi vào ba partition, và consumer có thể xử lý
    `shipped` trước `paid`
- [ ] ⚠️ **Tăng số partition làm đổi mapping key → partition.** Sự kiện mới của đơn `#123`
      có thể sang partition khác trong khi sự kiện cũ còn chưa xử lý xong ở partition cũ,
      nên thứ tự bị phá. Không giảm được số partition
- [ ] ⚠️ **Hot partition**: key bị lệch (ví dụ key là `shop_id` và một shop chiếm 80%
      đơn hàng) thì một partition quá tải trong khi các partition khác rảnh
- [ ] Chọn số partition: bằng mức song song tối đa mong muốn của consumer, có dự phòng
      tăng trưởng. ⚠️ Quá nhiều partition làm tăng chi phí cho broker và làm rebalance chậm
- [ ] Số consumer trong group vượt số partition thì consumer thừa ngồi không. Ví dụ topic
      có 3 partition mà chạy 5 consumer thì 2 consumer không nhận được gì

**Producer**
- [ ] `acks`: mức độ chờ xác nhận khi ghi

  | `acks` | Producer chờ gì | Rủi ro |
  |---|---|---|
  | `0` | không chờ | mất message mà không biết |
  | `1` | leader ghi xong | leader chết trước khi replica kịp sao chép thì mất |
  | `all` (mặc định từ Kafka 3.0) | tất cả replica trong ISR ghi xong | chậm nhất, an toàn nhất |

- [ ] Idempotent producer (`enable.idempotence`, mặc định bật từ Kafka 3.0): mỗi message có
      producer id + sequence number, nên broker bỏ được bản trùng do producer retry
- [ ] Batching và nén (`linger.ms`, `batch.size`, `compression.type`): đánh đổi độ trễ lấy
      thông lượng
- [ ] ⚠️ Gửi bất đồng bộ: phải xử lý callback lỗi. Gửi xong không kiểm tra kết quả thì
      message có thể mất mà không ai biết

**Broker và độ bền dữ liệu**
- [ ] Replication: mỗi partition có một leader và các follower; `replication.factor`
- [ ] ISR (in-sync replicas): các replica đang theo kịp leader
- [ ] Cấu hình an toàn phổ biến: `replication.factor=3`, `min.insync.replicas=2`,
      `acks=all`. Chịu được một broker chết mà không mất dữ liệu và vẫn ghi được
- [ ] ⚠️ `acks=all` với `min.insync.replicas=1` thì "all" có thể chỉ là một mình leader
- [ ] 🔴 Unclean leader election: cho replica chưa theo kịp lên làm leader, đổi lại có thể
      mất dữ liệu (mặc định tắt)
- [ ] 🔴 KRaft thay cho ZooKeeper (Kafka 4.0 đã bỏ hẳn ZooKeeper)
- [ ] 🟡 Log compaction: chỉ giữ message mới nhất của mỗi key, thay vì xoá theo thời gian.
      Dùng cho topic lưu trạng thái hiện tại (ví dụ thông tin mới nhất của mỗi user).
      Gửi value `null` (tombstone) để xoá một key
  - Use case của compacted topic: `__consumer_offsets` chính là một compacted topic;
    changelog của Kafka Streams state store; CDC snapshot của bảng (key = primary key);
    topic cấu hình/danh mục để service mới khởi động đọc từ đầu là có trạng thái đầy đủ
  - ⚠️ Compaction chạy nền, không tức thì: consumer vẫn có thể thấy nhiều bản của cùng key.
    Tombstone chỉ được giữ trong một khoảng (`delete.retention.ms`); consumer đọc chậm hơn
    khoảng đó có thể bỏ lỡ lệnh xoá
  - ⚠️ Active segment không bị compact

**Lưu trữ và vì sao Kafka nhanh** 🔴
- [ ] Mỗi partition là một thư mục trên đĩa, chia thành nhiều **segment**. Mỗi segment gồm
      file `.log` (dữ liệu), `.index` (offset → vị trí byte), `.timeindex` (timestamp → offset)
  - Chỉ segment cuối (active) được ghi. Segment đầy (`log.segment.bytes`) hoặc quá hạn thì
    đóng lại và mở segment mới
  - Retention và compaction làm việc **theo segment**: xoá nguyên file cũ, không xoá từng
    message. ⚠️ Vì vậy message có thể sống lâu hơn `retention.ms` một chút
  - Index là **sparse** (không phải mọi offset đều có trong index): tìm vị trí gần nhất rồi
    quét tiếp
- [ ] Vì sao nhanh:
  - **Sequential I/O**: chỉ append vào cuối file, đọc tuần tự. Đĩa (kể cả HDD) đọc/ghi tuần
    tự nhanh hơn nhiều so với ngẫu nhiên
  - **Page cache của OS**: Kafka không tự cache trong JVM heap mà dựa vào page cache. Consumer
    đọc message vừa ghi thường lấy thẳng từ RAM. Heap nhỏ → GC nhẹ
  - **Zero-copy** (`sendfile`): chuyển dữ liệu từ page cache ra socket không qua user space.
    ⚠️ Bật TLS thì mất zero-copy vì phải mã hoá trong user space
  - **Batching** ở mọi tầng (producer gom lô, broker ghi lô, consumer fetch lô) và **nén theo lô**
  - Broker không theo dõi trạng thái từng message (chỉ có offset của group), khác queue
    truyền thống phải đánh dấu ack từng message
  - ⚠️ Kafka không fsync mỗi message theo mặc định; độ bền đến từ replication, không phải fsync

**Consumer**
- [ ] Vòng lặp `poll()`: lấy một lô message, xử lý, commit offset
- [ ] **Thời điểm commit offset quyết định kiểu đảm bảo**:
  - Commit **trước** khi xử lý: consumer chết giữa chừng thì message bị bỏ qua
    (at-most-once)
  - Commit **sau** khi xử lý: consumer chết sau khi xử lý nhưng trước khi commit thì
    message được xử lý lại (at-least-once). Đây là lựa chọn phổ biến, kèm consumer idempotent
- [ ] ⚠️ Auto commit (`enable.auto.commit=true`, mặc định) commit định kỳ theo thời gian,
      không theo việc xử lý xong. Nếu đẩy message sang thread khác xử lý bất đồng bộ thì
      offset có thể được commit trước khi xử lý xong, và message bị mất khi crash
- [ ] `auto.offset.reset`: khi group chưa có offset thì đọc từ đầu (`earliest`) hay chỉ
      đọc message mới (`latest`, mặc định). ⚠️ Deploy consumer group mới với `latest` thì
      bỏ qua toàn bộ message cũ
- [ ] 🟡 Offset lưu ở đâu: internal topic **`__consumer_offsets`** (compacted, key = group +
      topic + partition). Mỗi group được gán cho một **group coordinator** (broker làm leader
      của partition tương ứng trong `__consumer_offsets`), lo membership và nhận commit
  - Commit offset nghĩa là ghi "offset của message **tiếp theo** cần đọc", không phải
    offset message vừa xử lý
  - ⚠️ Offset của group cũng có hạn giữ (`offsets.retention.minutes`); group ngừng hoạt động
    quá lâu thì mất offset và rơi về `auto.offset.reset`
  - Có thể lưu offset ngoài Kafka (trong DB cùng transaction với dữ liệu) rồi `seek()` khi
    khởi động: một cách đạt effectively-once khi đích là DB
- [ ] **Consumer lag**: khoảng cách giữa offset mới nhất và offset đã xử lý. Đây là metric
      quan trọng nhất cần theo dõi; lag tăng đều nghĩa là consumer không theo kịp
- [ ] **Rebalance**: consumer tham gia hoặc rời group thì partition được chia lại
  - Trong lúc rebalance, việc tiêu thụ bị tạm dừng (giảm nhẹ nhờ cooperative rebalancing)
  - ⚠️ Xử lý một lô lâu hơn `max.poll.interval.ms` (mặc định 5 phút) thì consumer bị coi là
    đã chết và bị đá khỏi group. Partition chuyển cho consumer khác, và lô đó bị xử lý
    **hai lần**. Đây là nguồn trùng lặp rất hay gặp
  - Cách sửa: giảm `max.poll.records`, xử lý nhanh hơn, hoặc tăng `max.poll.interval.ms`
  - Hai cơ chế phát hiện chết khác nhau: **heartbeat** (thread nền, `session.timeout.ms`)
    phát hiện process chết; **`max.poll.interval.ms`** phát hiện process sống nhưng kẹt
- [ ] 🔴 **Eager vs cooperative rebalance**
  - Eager (kiểu cũ): mọi consumer thu hồi **toàn bộ** partition rồi mới chia lại → cả group
    dừng ("stop the world")
  - Cooperative (incremental): chỉ thu hồi những partition cần chuyển, qua vài vòng; consumer
    khác tiếp tục đọc partition của mình. Dùng `CooperativeStickyAssignor`
  - Sticky: cố giữ partition ở consumer cũ để tận dụng cache/state cục bộ
  - ⚠️ Đổi assignor từ eager sang cooperative trên group đang chạy cần rolling deploy theo
    đúng thủ tục (hai bước). Kafka 4.x còn có consumer group protocol mới do broker điều phối
    (kiểm tra lại theo phiên bản bạn dùng)
- [ ] 🔴 **Static membership** (`group.instance.id`)
  - Mỗi consumer có id cố định. Restart (rolling deploy, pod reschedule) trong khoảng
    `session.timeout.ms` thì **không** gây rebalance, consumer nhận lại đúng partition cũ
  - Trade-off: consumer chết thật thì partition của nó bị treo tới khi hết session timeout
- [ ] Thứ tự trong consumer: xử lý song song các message của cùng một partition bằng nhiều
      thread sẽ phá thứ tự. Muốn song song mà giữ thứ tự thì song song theo key
  - ⚠️ Xử lý song song trong một partition còn làm khó commit: message 10 xong trước message 7,
    không được commit 11 khi 7 chưa xong. Phải theo dõi offset liên tục thấp nhất đã xong

**Exactly-once** 🔴
- [ ] Idempotent producer chỉ chống trùng do producer retry, chưa phải exactly-once đầu cuối
- [ ] Kafka transaction (`transactional.id`, consumer đặt `isolation.level=read_committed`):
      đọc từ topic A, xử lý, ghi sang topic B và commit offset trong cùng một transaction
- [ ] ⚠️ Chỉ đúng khi cả đầu vào và đầu ra đều là Kafka. Ghi ra DB hay gọi API bên ngoài
      thì vẫn phải tự làm idempotent (unique key, upsert), hoặc lưu offset vào DB trong
      cùng transaction với dữ liệu

**Xử lý lỗi**
- [ ] Kafka không có sẵn DLQ hay retry có delay như RabbitMQ; phải tự dựng
- [ ] Pattern retry topic:

  ```text
  orders ──lỗi──► orders.retry.1m ──lỗi──► orders.retry.10m ──lỗi──► orders.dlq
     ▲                  │                        │
     └──── xử lý lại ───┴────────────────────────┘      (dlq: người xem xét thủ công)
  ```

  - ⚠️ Đẩy sang retry topic thì message đi sau có thể được xử lý trước, nên **mất thứ tự**
  - Nếu thứ tự quan trọng thì phải retry ngay tại chỗ (chặn cả partition) hoặc chặn các
    message cùng key cho tới khi message lỗi được xử lý
- [ ] Poison message: retry vô hạn trên một message sẽ chặn cả partition; phải có giới hạn
      số lần retry rồi đẩy vào DLQ

**Vận hành** 🔴
- [ ] **Quotas**: giới hạn byte/giây produce và fetch, và tỉ lệ request, theo user hoặc
      client-id. Vượt quota thì broker không từ chối mà **làm chậm** (throttle) response.
      Dùng để một client ồn ào không làm nghẽn cả cluster (noisy neighbor)
- [ ] **Monitoring** phải có:

  | Metric | Ý nghĩa | Báo động khi |
  |---|---|---|
  | Consumer lag (theo partition) | consumer chậm bao nhiêu | tăng đều, hoặc dồn vào một partition |
  | Under-replicated partitions | partition có replica tụt khỏi ISR | > 0 kéo dài |
  | Under-min-ISR partitions | ISR < `min.insync.replicas` → producer `acks=all` bị từ chối | > 0 |
  | Offline partitions | partition không có leader, không đọc/ghi được | > 0 |
  | Active controller count | tổng cả cluster phải đúng 1 | khác 1 |
  | Request latency, disk usage, network | sức khoẻ broker | theo ngưỡng |

  - ⚠️ Lag tính bằng số message chưa đủ; nên đo cả **lag theo thời gian** (message cũ nhất
    chưa xử lý đã bao lâu), vì 10.000 message lag có thể là 1 giây hoặc 1 giờ
- [ ] Công cụ: `kafka-consumer-groups.sh --describe`, Burrow, exporter cho Prometheus,
      Cruise Control để cân bằng partition giữa broker

**Hệ sinh thái** 🟡
- [ ] Schema Registry với Avro/Protobuf: thống nhất schema giữa producer và consumer;
      quy tắc tương thích (thêm field có giá trị mặc định thì an toàn)
- [ ] Kafka Connect, Debezium (CDC: đọc binlog của DB rồi đẩy thành sự kiện)
- [ ] Kafka Streams, ksqlDB (xử lý stream)
- [ ] PHP không có client Kafka chính thức trong Laravel; thường dùng extension `rdkafka`,
      hoặc để một service Go/Java lo phần tiêu thụ Kafka

### RabbitMQ

- [ ] Mô hình: producer gửi tới **exchange**, exchange định tuyến tới **queue** theo
      **binding**, consumer đọc từ queue. Producer không gửi thẳng vào queue

  ```text
  producer ──► exchange ──binding(routing key/pattern)──► queue ──► consumer
  ```
- [ ] Exchange types

  | Type | Định tuyến | Ví dụ |
  |---|---|---|
  | direct | routing key khớp chính xác binding key | `email.send` → queue email |
  | topic | khớp pattern theo từ, `*` = đúng một từ, `#` = 0 hoặc nhiều từ | `order.*.vn`, `order.#` |
  | fanout | gửi tới mọi queue đã bind, bỏ qua routing key | broadcast |
  | headers | khớp theo header (`x-match: all/any`) | ít dùng |

  - Default exchange (tên rỗng): kiểu direct, mọi queue tự bind với tên của nó. Vì vậy
    "gửi vào queue X" thực ra là gửi qua default exchange với routing key `X`
  - Pub/sub: mỗi service một queue riêng, cùng bind vào một fanout/topic exchange
  - Work queue: nhiều consumer cùng đọc một queue, broker round-robin
- [ ] Ack
  - Auto-ack: message coi như xong ngay khi gửi đi → consumer crash là mất
  - Manual ack: `basic.ack` sau khi xử lý. Channel/connection đóng mà chưa ack thì message
    quay lại queue và được giao lại với cờ `redelivered`
  - `basic.nack` / `basic.reject` với `requeue=false` → vào DLX nếu có, không thì bị bỏ
  - ⚠️ Quên ack: message kẹt ở trạng thái unacked, bộ nhớ broker tăng, không ai xử lý
  - ⚠️ Có **consumer ack timeout** (mặc định khoảng 30 phút, kiểm tra lại theo phiên bản):
    không ack kịp thì broker đóng channel và giao lại message. Job xử lý rất lâu dễ dính
- [ ] Prefetch (`basic.qos`)
  - Số message tối đa đã giao mà chưa ack cho mỗi consumer. Đây là backpressure của mô hình push
  - Prefetch quá lớn: một consumer ôm hết, consumer khác rảnh; consumer chết thì cả đống
    message bị giao lại. Quá nhỏ (1): mỗi message một round-trip, thông lượng thấp
  - Việc nặng, không đều: prefetch nhỏ. Việc nhẹ, đều: prefetch lớn hơn
- [ ] Publisher confirms
  - Bật confirm mode trên channel, broker gửi ack khi message đã được nhận (với persistent
    message trên queue durable: sau khi ghi đĩa/replicate). Không bật thì producer không
    biết message có tới hay không
  - `mandatory=true`: message không route được tới queue nào thì broker trả lại
    (`basic.return`) thay vì âm thầm bỏ
  - ⚠️ Confirm là bất đồng bộ; chờ đồng bộ từng message thì rất chậm, nên gom lô hoặc
    xử lý callback
- [ ] DLX (dead letter exchange): cấu hình `x-dead-letter-exchange` trên queue. Message bị
      dead-letter khi: bị reject/nack với `requeue=false`, hết TTL, queue vượt `x-max-length`,
      hoặc vượt delivery limit (quorum queue)
- [ ] TTL: theo queue (`x-message-ttl`) hoặc theo từng message (`expiration`); queue cũng có
      thể tự xoá khi không dùng (`x-expires`)
  - ⚠️ Với classic queue, message TTL riêng chỉ bị xử lý khi message tới **đầu queue**.
    Message TTL 10s nằm sau message TTL 1 giờ sẽ chờ 1 giờ
- [ ] Delayed message
  - Cách 1: TTL + DLX. Một queue "chờ" không có consumer, TTL = độ trễ, hết hạn thì DLX đẩy
    sang queue thật. Mỗi mức trễ một queue để tránh cạm bẫy TTL ở trên
  - Cách 2: plugin `rabbitmq_delayed_message_exchange`. Tiện, nhưng có giới hạn về độ bền và
    số lượng message trễ (đọc kỹ tài liệu plugin trước khi dùng cho dữ liệu quan trọng)
- [ ] Durable và persistent
  - **Durable queue**: định nghĩa queue sống qua restart broker
  - **Persistent message** (`delivery_mode=2`): nội dung message được ghi đĩa
  - ⚠️ Cần **cả hai**. Queue durable chứa message transient thì restart vẫn mất message
- [ ] 🔴 Quorum queue
  - Queue được replicate qua nhiều node bằng Raft; ghi được xác nhận khi đa số node ghi xong
  - Thay thế classic mirrored queue (đã bị loại bỏ ở RabbitMQ 4.x)
  - Có **delivery limit**: message bị giao lại quá số lần thì dead-letter. Chống poison message
  - Trade-off: tốn tài nguyên hơn, không hỗ trợ một số tính năng của classic queue
    (ví dụ priority theo kiểu cũ, non-durable); cần số node lẻ (3, 5)
- [ ] 🔴 Lazy queue: đẩy message xuống đĩa sớm thay vì giữ trong RAM, dành cho queue rất dài.
      Từ các bản 3.12 trở đi classic queue đã hoạt động gần như lazy theo mặc định
      (kiểm tra lại theo phiên bản bạn dùng)
- [ ] 🔴 RabbitMQ Streams: kiểu log giống Kafka (đọc lại được, nhiều consumer), trong RabbitMQ
- [ ] 🔴 Single active consumer: nhiều consumer đăng ký nhưng chỉ một nhận message, còn lại dự
      phòng. Giữ thứ tự mà vẫn có failover
- [ ] ⚠️ Khi nào RabbitMQ mất message
  - Producer không dùng publisher confirms, broker chết lúc message đang trên đường
  - Message không route được và không bật `mandatory` (hoặc không có alternate exchange)
  - Queue không durable hoặc message không persistent, broker restart
  - Consumer dùng auto-ack rồi crash
  - Hết TTL hoặc vượt max-length mà không có DLX (overflow mặc định là bỏ message ở đầu queue)
  - Classic queue chỉ nằm trên một node và đĩa node đó hỏng
  - Consumer ack **trước** khi xử lý xong

### SQS/SNS, Redis, NATS, database

**AWS SQS** 🟡
- [ ] Standard queue: at-least-once, thứ tự best-effort (không đảm bảo), thông lượng gần như
      không giới hạn. ⚠️ Có thể nhận trùng dù không có lỗi gì phía bạn
- [ ] FIFO queue: tên kết thúc bằng `.fifo`
  - **Message group id**: thứ tự được đảm bảo trong một group; các group khác nhau xử lý
    song song. Giống vai trò của key/partition trong Kafka
  - **Deduplication id** (hoặc content-based deduplication theo hash nội dung): message
    trùng id gửi trong cửa sổ 5 phút bị bỏ
  - Trong một group, khi còn message đang được xử lý (in-flight) thì message sau không được
    giao → một message lỗi chặn cả group
  - Thông lượng thấp hơn standard (có chế độ high throughput; kiểm tra con số hiện tại)
- [ ] **Visibility timeout** (mặc định 30 giây)
  - Consumer nhận message thì message bị ẩn khỏi consumer khác trong khoảng này. Xoá
    (`DeleteMessage`) trước khi hết hạn = ack. Không xoá = message hiện lại, được giao lại
  - ⚠️ Xử lý lâu hơn visibility timeout: consumer khác nhận **cùng message** và xử lý song
    song. Sửa: đặt timeout lớn hơn thời gian xử lý tối đa, hoặc gọi
    `ChangeMessageVisibility` định kỳ như heartbeat
  - ⚠️ Visibility timeout quá dài: consumer crash thì message chờ rất lâu mới được thử lại
  - Không có nack: muốn retry sớm thì đặt visibility về 0
- [ ] Long polling (`WaitTimeSeconds` tối đa 20 giây): chờ tới khi có message thay vì trả rỗng
      ngay. Giảm request rỗng, giảm chi phí. Short polling còn có thể trả rỗng dù queue có
      message (chỉ hỏi một phần server)
- [ ] DLQ: redrive policy với `maxReceiveCount`, nhận quá số lần thì chuyển sang DLQ. Có
      **DLQ redrive** để đẩy message từ DLQ về queue gốc sau khi sửa lỗi
  - ⚠️ DLQ của FIFO queue phải là FIFO; redrive làm mất thứ tự ban đầu
- [ ] Khác: delay queue / message timer (trễ tối đa 15 phút), retention mặc định 4 ngày
      (tối đa 14 ngày), mỗi lần nhận tối đa 10 message. Lambda đọc SQS nên bật partial batch
      response để một message lỗi không làm cả lô bị giao lại
- [ ] **SNS fan-out**: một SNS topic, nhiều SQS queue subscribe. Mỗi service có queue riêng,
      có buffer, retry và DLQ riêng. **Filter policy** để mỗi queue chỉ nhận loại message mình
      cần. SNS gửi thẳng HTTP/Lambda cũng được nhưng không có buffer bền như SQS
  - Bật raw message delivery để consumer không phải bóc envelope của SNS

**Redis** 🟡
- [ ] Redis List: `LPUSH` + `BRPOP` là queue đơn giản. ⚠️ Pop xong consumer crash là mất.
      Reliable queue: `BLMOVE` sang list "processing", xử lý xong mới xoá, có tiến trình quét
      list processing để đẩy lại việc treo
- [ ] Redis Pub/Sub: fire-and-forget, subscriber offline thì mất. Không dùng cho việc cần tin cậy
- [ ] Redis Streams: log có id, gần với Kafka thu nhỏ
  - `XADD` ghi, `XREADGROUP` đọc theo consumer group, `XACK` ack
  - Message đã giao mà chưa ack nằm trong **PEL** (pending entries list); `XPENDING` để xem,
    `XAUTOCLAIM`/`XCLAIM` để consumer khác nhận lại việc của consumer đã chết
  - Giới hạn độ dài bằng `MAXLEN`/`MINID` khi `XADD` hoặc `XTRIM`, không thì dùng hết RAM
  - ⚠️ Độ bền phụ thuộc cấu hình persistence (RDB/AOF) và replication bất đồng bộ; failover
    có thể mất message mới ghi. Dữ liệu nằm trong RAM nên dung lượng bị giới hạn
  - Hợp: đã có Redis, lưu lượng vừa phải, chấp nhận độ bền thấp hơn Kafka

**NATS** 🔴 (đại ý)
- [ ] Core NATS: pub/sub theo subject (`orders.created`, wildcard `*` và `>`), **at-most-once**,
      không lưu. Queue group để nhiều subscriber chia việc. Rất nhẹ, độ trễ thấp
- [ ] JetStream: lớp persistence trên NATS, có stream, consumer, ack, replay, at-least-once,
      dedup theo message id. Cạnh tranh với Kafka ở quy mô nhỏ và vừa, vận hành đơn giản hơn

**Database làm queue** 🟡
- [ ] Bảng `jobs(id, payload, status, run_at, attempts, locked_by, locked_at)`. Nhiều worker
      lấy việc mà không đụng nhau:

  ```sql
  BEGIN;
  SELECT id, payload FROM jobs
  WHERE status = 'pending' AND run_at <= now()
  ORDER BY id
  LIMIT 10
  FOR UPDATE SKIP LOCKED;       -- dòng đang bị worker khác khoá thì bỏ qua, không chờ
  UPDATE jobs SET status = 'running', locked_at = now() WHERE id IN (...);
  COMMIT;
  ```
  - Có ở PostgreSQL 9.5+ và MySQL 8.0+. Laravel database queue driver dùng kiểu này
  - Ưu: không thêm hạ tầng, **enqueue cùng transaction với dữ liệu nghiệp vụ** (tự động có
    tính chất của outbox), dễ query/debug
  - Nhược: polling tốn tải DB, bảng churn nhiều (Postgres: bloat, cần vacuum), không hợp
    thông lượng rất cao hay nhiều consumer group
  - ⚠️ Job `running` của worker đã chết phải có cơ chế thu hồi (quá `locked_at + timeout`
    thì trả về `pending`)
  - Postgres có `LISTEN/NOTIFY` để giảm polling; thư viện tham khảo: pgmq, River (Go),
    Oban (Elixir), Solid Queue (Rails)

**So sánh**

| | Kafka | RabbitMQ | SQS | Redis Streams |
|---|---|---|---|---|
| Mô hình | log, giữ sau khi đọc | queue, xoá sau ack (có thêm streams) | queue managed | log trong RAM |
| Đọc lại | được, tua offset | không (trừ streams) | không | được, theo id |
| Thứ tự | trong partition | trong queue, một consumer | FIFO: theo message group; standard: không | trong stream |
| Delivery | at-least-once; EOS trong Kafka | at-least-once | at-least-once; FIFO có dedup 5 phút | at-least-once |
| Retry có delay, DLQ | tự dựng | DLX, TTL, delivery limit | redrive policy, delay | tự dựng qua PEL |
| Định tuyến | topic + key | linh hoạt (exchange) | không (dùng SNS filter) | không |
| Backpressure | pull | prefetch | pull | pull |
| Thông lượng | rất cao | cao | standard rất cao, FIFO có giới hạn | cao, giới hạn bởi RAM |
| Vận hành | nặng (hoặc dùng managed: MSK, Confluent) | vừa | không phải vận hành | nhẹ nếu đã có Redis |
| Hợp với | event streaming, CDC, analytics, nhiều bên đọc cùng luồng | task queue, định tuyến phức tạp | task queue trên AWS, ít vận hành | queue nhẹ, đã có Redis |

### Pattern

- [ ] 🟡 **Transactional outbox**: ghi sự kiện vào bảng outbox trong cùng transaction với
      dữ liệu, rồi một process riêng đẩy sự kiện lên queue. Giải quyết vấn đề "ghi DB xong
      nhưng gửi message thất bại" (dual write)
  - Vì sao dual write sai: ghi DB rồi publish → publish lỗi thì mất event. Publish rồi ghi
    DB → DB rollback thì event "ma". Publish trong transaction → transaction rollback sau
    khi đã publish. Không có thứ tự nào an toàn
  - Bảng:

    ```sql
    CREATE TABLE outbox (
      id            BIGSERIAL PRIMARY KEY,
      event_id      UUID NOT NULL UNIQUE,     -- consumer dùng để dedup
      aggregate_type TEXT NOT NULL,           -- 'order'
      aggregate_id  TEXT NOT NULL,            -- dùng làm key Kafka để giữ thứ tự
      event_type    TEXT NOT NULL,            -- 'OrderPlaced'
      payload       JSONB NOT NULL,
      created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
      published_at  TIMESTAMPTZ               -- NULL = chưa gửi (cách polling)
    );
    ```
  - **Relay kiểu polling**: định kỳ `SELECT ... WHERE published_at IS NULL ORDER BY id
    LIMIT n FOR UPDATE SKIP LOCKED`, publish, cập nhật `published_at`
    - Đơn giản, không cần hạ tầng thêm. Độ trễ = chu kỳ poll, tốn tải DB
    - Publish xong mà chưa kịp cập nhật `published_at` thì lần sau gửi lại → **outbox luôn
      là at-least-once**, consumer phải idempotent
    - ⚠️ Poll theo `id > last_id` với id auto-increment có thể **bỏ sót**: transaction lấy
      id 101 commit trước transaction lấy id 100, relay đọc thấy 101 và nhảy qua 100.
      Dùng cờ `published_at` thay vì con trỏ id, hoặc chỉ đọc dòng cũ hơn một khoảng an toàn
  - **Relay kiểu CDC** (Debezium đọc binlog/WAL): không phải poll, độ trễ thấp, thứ tự theo
    thứ tự commit. Debezium có sẵn outbox event router. Cái giá: vận hành Kafka Connect,
    theo dõi replication slot (Postgres: slot bị treo làm WAL phình đầy đĩa ⚠️)
  - **Thứ tự**: cần giữ thứ tự theo aggregate thì dùng `aggregate_id` làm key; chạy nhiều
    relay song song theo kiểu polling có thể đảo thứ tự của cùng aggregate → chia relay
    theo hash của aggregate hoặc chỉ một relay active
  - **Dọn outbox**: xoá dòng đã publish sau N ngày bằng job nền, hoặc partition bảng theo
    thời gian rồi drop partition cũ (rẻ hơn `DELETE` hàng loạt). Với CDC có thể xoá ngay
    sau khi insert vì Debezium đọc từ log (kiểm tra lại với tài liệu Debezium)
- [ ] 🟡 **Inbox pattern**: phía consumer, ghi message nhận được vào bảng `inbox` (unique
      theo `event_id`) rồi ack ngay; một process khác xử lý từ inbox. Tách "nhận" khỏi "xử
      lý", dedup bằng unique key, xử lý lại được. Bản đơn giản chính là bảng
      `processed_messages` ở trên
- [ ] 🔴 **CDC** (Change Data Capture) với Debezium
  - Đọc log của DB (MySQL binlog dạng row, Postgres logical decoding) → mỗi thay đổi thành event
  - Dùng: đồng bộ sang search/cache/data warehouse, outbox relay, tách dần monolith
  - ⚠️ CDC trực tiếp trên bảng nghiệp vụ làm **lộ schema nội bộ** thành contract: đổi tên
    cột là vỡ consumer. Outbox giữ contract rõ ràng hơn
  - ⚠️ Snapshot ban đầu của bảng lớn, schema change, và lag của connector cần theo dõi
- [ ] 🟡 Event-driven architecture; event notification và event-carried state transfer
  - **Event notification**: event nhỏ (`OrderPlaced{order_id}`), consumer cần thêm thì gọi
    ngược API. Ít coupling về dữ liệu, nhưng tạo tải và phụ thuộc lúc chạy vào producer; dữ
    liệu đọc về có thể đã khác lúc event xảy ra
  - **Event-carried state transfer**: event mang đủ dữ liệu, consumer giữ bản sao cục bộ. Không
    cần gọi ngược, chịu được producer chết; đổi lại event to, dữ liệu nhân bản, schema là
    contract lớn hơn
  - Ưu điểm chung: decouple, thêm consumer không sửa producer. Nhược: khó nhìn toàn cảnh
    luồng nghiệp vụ, cần tracing và catalog event
- [ ] 🔴 **Choreography vs orchestration**
  - Choreography: mỗi service nghe event và tự phản ứng, không ai chỉ huy. Ít coupling, nhưng
    luồng nghiệp vụ nằm ngầm trong nhiều service, khó biết đơn hàng đang ở bước nào, dễ có
    vòng lặp event
  - Orchestration: một orchestrator gửi command từng bước và giữ trạng thái. Dễ hiểu, dễ
    theo dõi, xử lý lỗi tập trung; orchestrator thành điểm tập trung logic
  - Kinh nghiệm: 2–3 bước đơn giản thì choreography; nhiều bước, có bù trừ, cần theo dõi thì
    orchestration (thường bằng workflow engine)
- [ ] 🔴 CQRS, event sourcing: lợi ích và độ phức tạp đi kèm
  - **CQRS**: tách model ghi (command, chuẩn hoá, kiểm tra nghiệp vụ) và model đọc (query,
    denormalize cho từng màn hình). Đồng bộ model đọc qua event → read model **eventual**
    ⚠️ user vừa ghi xong đọc không thấy. Không bắt buộc đi cùng event sourcing
  - **Event sourcing**: lưu chuỗi event làm nguồn sự thật, trạng thái hiện tại = fold các event
    - Lợi: audit đầy đủ, dựng lại trạng thái ở bất kỳ thời điểm, tạo read model mới bằng replay
    - **Snapshot**: lưu trạng thái mỗi N event để không phải replay từ đầu
    - **Replay**: dựng lại projection; ⚠️ handler có side effect (gửi email) không được chạy lại
      khi replay
    - Cái giá: schema event bất biến nên versioning/upcasting phức tạp; query theo trạng thái
      khó (phải có projection); xoá dữ liệu cá nhân (GDPR) khó (crypto-shredding); đội ngũ
      phải quen tư duy mới. ⚠️ Chỉ đáng dùng khi domain thực sự cần lịch sử (ledger, kế toán)
- [ ] 🔴 **Saga**: chuỗi transaction cục bộ với hành động bù. Chi tiết (orchestration vs
      choreography, compensating action, không có isolation) ở
      [14-distributed-systems.md](14-distributed-systems.md)

### Background job, scheduler, batch

- [ ] 🟡 Cron trên nhiều instance
  - Deploy 3 instance, mỗi instance chạy crontab → job chạy **3 lần**
  - Cách 1: một instance/container riêng chạy scheduler. Đơn giản, nhưng là single point of
    failure
  - Cách 2: **lock** trước khi chạy (Redis `SET NX PX`, hoặc bảng lock trong DB). Instance nào
    lấy được lock thì chạy. Laravel `onOneServer()`, Spring dùng ShedLock
  - Cách 3: leader election (etcd/ZooKeeper/Kubernetes Lease), chỉ leader chạy scheduler
  - Cách 4: scheduler bên ngoài (Kubernetes CronJob, EventBridge Scheduler) đẩy việc vào queue
  - ⚠️ Lock TTL ngắn hơn thời gian chạy → instance khác cũng chạy. Lock TTL rất dài → instance
    chết giữ lock, lần chạy sau bị bỏ
  - ⚠️ Kubernetes CronJob chỉ đảm bảo "xấp xỉ một lần": có thể chạy hai lần hoặc bỏ lỡ.
    `concurrencyPolicy: Forbid` chặn chạy chồng nhưng không thay được idempotency
  - ⚠️ Chạy chồng lên chính nó: job 5 phút một lần mà có lần chạy 7 phút. Laravel
    `withoutOverlapping()`
  - Nguyên tắc chung: **job phải idempotent** (chạy hai lần không sai), lock chỉ để giảm lãng phí
  - ⚠️ Timezone và DST của cron (xem [22-practical-data.md](22-practical-data.md))
- [ ] 🟡 Job dài
  - Chia thành nhiều job nhỏ (mỗi job một batch 1.000 bản ghi) thay vì một job chạy 3 giờ:
    retry rẻ, song song được, deploy không giết mất việc
  - **Checkpoint**: lưu tiến độ (id cuối đã xử lý) để chạy lại tiếp từ đó. Duyệt theo
    keyset (`WHERE id > ? ORDER BY id LIMIT ?`), không dùng `OFFSET`
  - Graceful shutdown: worker nhận SIGTERM thì làm xong message hiện tại, không lấy thêm
  - ⚠️ Job chạy lâu hơn timeout của queue (visibility timeout, `retry_after`, consumer
    timeout) bị giao lại và chạy song song với chính nó
- [ ] 🟡 Batch vs stream processing

  | | Batch | Stream |
  |---|---|---|
  | Dữ liệu | tập có giới hạn, chạy theo lịch | luồng vô hạn, xử lý liên tục |
  | Độ trễ | phút tới giờ | mili giây tới giây |
  | Độ phức tạp | thấp, dễ chạy lại | cao: window, late event, state, watermark |
  | Ví dụ | báo cáo cuối ngày, đối soát | phát hiện gian lận, dashboard real-time |
  | Công cụ | cron + SQL, Spark, dbt | Kafka Streams, Flink |

  - Nhiều hệ thống dùng cả hai: stream cho số liệu tạm thời, batch chạy lại để có số chính xác
- [ ] 🔴 Workflow engine (đại ý)
  - **Temporal** (và tiền thân Cadence): viết workflow bằng code bình thường, engine lưu lịch sử
    và tự resume sau crash; có retry, timer dài (chờ 3 ngày), bù trừ. Hợp cho saga, quy trình
    nhiều bước. ⚠️ Code workflow phải deterministic (không gọi random, time, I/O trực tiếp)
  - **Airflow**: lập lịch DAG cho pipeline dữ liệu/batch, không dành cho luồng giao dịch
    độ trễ thấp
  - Khác: AWS Step Functions, Camunda (BPMN)
- [ ] Đối chiếu theo ngôn ngữ
  - **Laravel**: `dispatch()` job lên queue (Redis/SQS/database), `queue:work` là worker
    long-running, `$tries`, `$backoff`, bảng `failed_jobs` làm DLQ, Horizon để giám sát.
    ⚠️ `retry_after` phải lớn hơn `timeout` của job, không thì job bị giao lại khi đang chạy.
    ⚠️ Dispatch trong DB transaction: worker có thể chạy trước khi transaction commit, dùng
    `afterCommit()`. Xem [05-php-laravel.md](05-php-laravel.md)
  - **Spring**: `@KafkaListener` với ack mode thủ công, `DefaultErrorHandler` +
    `DeadLetterPublishingRecoverer` cho retry/DLQ; `@RabbitListener`, `RabbitTemplate` với
    confirm callback. Xem [06-java-spring.md](06-java-spring.md)
  - **Go**: client như `franz-go`, `confluent-kafka-go`, `segmentio/kafka-go`,
    `amqp091-go`; tự viết vòng lặp consume, worker pool bằng goroutine, commit/ack thủ công,
    `context` để dừng êm. Xem [07-go.md](07-go.md)

## Senior trả lời khác gì

- **"Làm sao đảm bảo message không bị xử lý hai lần?"**
  - Mid: "Dùng exactly-once của Kafka."
  - Senior: "Giả định at-least-once. Consumer idempotent bằng unique constraint trên
    `event_id` ghi cùng transaction với thay đổi nghiệp vụ. Side effect ra ngoài thì truyền
    idempotency key. Kafka EOS chỉ đúng khi đích cũng là Kafka."
- **"Chọn Kafka hay RabbitMQ?"**
  - Mid: "Kafka nhanh hơn nên chọn Kafka."
  - Senior: hỏi lại nhu cầu: có cần replay, nhiều consumer group, retention dài không (Kafka);
    hay là task queue cần định tuyến, retry có delay, ack từng message (RabbitMQ); đội có
    người vận hành Kafka không; nếu trên AWS và chỉ cần task queue thì SQS rẻ công vận hành
    nhất; nếu chỉ vài nghìn job/ngày thì bảng DB + `SKIP LOCKED` là đủ.
- **"Ghi DB rồi gửi event, làm sao không mất event?"**
  - Mid: "Gửi event trong transaction" hoặc "retry khi gửi lỗi."
  - Senior: giải thích vì sao mọi thứ tự dual write đều sai, đề xuất outbox, nêu outbox là
    at-least-once, cạm bẫy polling theo id tự tăng, dọn bảng, và khi nào đáng dùng CDC.
- **"Consumer lag tăng, làm gì?"**
  - Mid: "Thêm consumer."
  - Senior: xem lag dồn vào partition nào (hot key), xem thời gian xử lý mỗi message và
    downstream (DB, API), kiểm tra rebalance liên tục, chỉ thêm consumer khi còn partition
    rảnh; đo lag theo thời gian và đặt alert trước khi retention xoá mất message.
- **"Cron chạy trên 3 server, làm sao chỉ chạy một lần?"**
  - Mid: "Dùng Redis lock."
  - Senior: lock chỉ giảm chạy trùng chứ không loại bỏ (lock hết hạn, GC pause, CronJob chạy
    hai lần), nên job vẫn phải idempotent; nêu cách chọn TTL, theo dõi lần chạy cuối (alert
    nếu job không chạy), và chuyển sang scheduler + queue khi job nhiều.

## Tình huống

1. *Hệ thống đặt hàng phát sự kiện `order.created`. Ba service email, kho và analytics đều
   cần nhận. Thiết kế thế nào?*
   - Một topic `orders`, ba consumer group riêng. Mỗi group tự quản offset, nên service
     analytics chậm hay chết cũng không ảnh hưởng email và kho.
   - Trên AWS: một SNS topic fan-out sang ba SQS queue, mỗi queue có DLQ riêng.

2. *Consumer gửi email xác nhận bị gửi trùng cho khách vài lần mỗi tuần. Nguyên nhân có thể là gì?*
   - At-least-once: consumer crash sau khi gửi email nhưng trước khi commit offset.
   - Xử lý lô quá `max.poll.interval.ms` nên bị rebalance, lô bị xử lý lại.
   - Producer không bật idempotence nên retry tạo message trùng.
   - Cách sửa: lưu `event_id` đã xử lý vào bảng có unique constraint, kiểm tra trước khi gửi.

3. *Consumer lag tăng liên tục. Bạn làm gì?*
   - Xem xử lý mỗi message có chậm bất thường không (DB chậm, API bên ngoài chậm).
   - Nếu số consumer đang ít hơn số partition thì tăng consumer.
   - Nếu consumer đã bằng số partition thì phải tăng partition (và chấp nhận ảnh hưởng tới
     thứ tự theo key), hoặc xử lý theo lô, hoặc tối ưu phần xử lý.
   - Kiểm tra hot partition: lag dồn vào một partition thì vấn đề nằm ở key.

4. *Cập nhật số dư tài khoản qua Kafka, thứ tự rất quan trọng. Thiết kế thế nào?*
   - Key là `account_id`, để các sự kiện của một tài khoản nằm cùng partition.
   - Mỗi partition xử lý tuần tự; lỗi thì retry tại chỗ, không đẩy sang retry topic.
   - Consumer idempotent: mỗi sự kiện có id, ghi vào DB cùng transaction với việc cập nhật
     số dư.

5. *Ghi đơn hàng vào MySQL xong rồi gửi sự kiện lên Kafka, nhưng đôi khi gửi thất bại và
   các service khác không biết có đơn mới. Sửa thế nào?*
   - Đây là vấn đề dual write. Dùng transactional outbox (xem mục Pattern ở trên):
     ghi đơn và sự kiện vào bảng `outbox` trong cùng transaction, rồi một relay process
     hoặc Debezium đẩy từ `outbox` lên Kafka.

6. *Worker RabbitMQ xử lý video, mỗi job 10–40 phút. Thỉnh thoảng một video bị xử lý hai lần,
   và có lúc một worker ôm nhiều job trong khi worker khác rảnh.*
   - Prefetch đang lớn: đặt prefetch = 1 cho việc nặng và không đều.
   - Job vượt consumer ack timeout thì channel bị đóng, message giao lại → xử lý hai lần.
     Tăng timeout có kiểm soát, hoặc tách: ack ngay, ghi trạng thái job vào DB, worker cập
     nhật tiến độ; hoặc chia job nhỏ hơn.
   - Kết quả ghi idempotent theo `video_id`.

7. *Worker đọc SQS, gọi API bên thứ ba chậm, có lúc 2 phút. Thấy cùng một đơn bị gọi API hai lần.*
   - Visibility timeout 30 giây mặc định nhỏ hơn thời gian xử lý → message hiện lại, worker
     khác nhận.
   - Sửa: tăng visibility timeout lớn hơn p99 thời gian xử lý, hoặc gia hạn định kỳ bằng
     `ChangeMessageVisibility`; truyền idempotency key sang API bên thứ ba.
   - Đặt `maxReceiveCount` + DLQ để message lỗi mãi không quay vòng.

8. *Relay outbox kiểu polling thỉnh thoảng bỏ sót event, dù dòng vẫn nằm trong bảng.*
   - Nghi ngay tới việc đọc theo `id > last_seen_id`: id được cấp lúc insert nhưng thứ tự
     commit khác thứ tự id, dòng commit muộn có id nhỏ bị nhảy qua.
   - Sửa: đánh dấu `published_at` từng dòng, hoặc chỉ đọc dòng `created_at < now() - khoảng
     an toàn`, hoặc chuyển sang CDC đọc theo thứ tự commit.

9. *Job cron "gửi báo cáo ngày" đôi khi gửi hai lần sau khi scale từ 1 lên 3 pod.*
   - Mỗi pod chạy scheduler riêng. Thêm lock (`onOneServer`, ShedLock) hoặc tách scheduler.
   - Ghi bản ghi `report_runs(report_date UNIQUE)` trước khi gửi để lần chạy thứ hai bị
     chặn bởi unique constraint.
   - Thêm alert khi báo cáo không được gửi (lock kẹt cũng nguy hiểm như chạy trùng).

## ❓ Câu hỏi hay gặp

🟢
- Vì sao cần message queue? Cho ví dụ việc nên và không nên đẩy vào queue.
- Queue và topic (pub/sub) khác nhau thế nào?
- At-most-once, at-least-once, exactly-once khác nhau thế nào? Hệ thống của bạn dùng loại nào?
- DLQ là gì, dùng để làm gì?

🟡
- Làm sao đảm bảo message không bị xử lý hai lần?
- Tạo đơn hàng xong cần gửi email và trừ kho. Bạn thiết kế thế nào để ghi DB và gửi
  message luôn đi cùng nhau?
- Kafka đảm bảo thứ tự thế nào? Chuyện gì xảy ra với thứ tự khi tăng số partition?
- Topic có 6 partition, bạn chạy 10 consumer trong một group. Chuyện gì xảy ra?
- `acks=all` có đảm bảo không mất dữ liệu không? Cần thêm cấu hình gì?
- Vì sao consumer Kafka hay xử lý trùng message? Kể ít nhất hai nguyên nhân.
- Khi nào chọn Kafka, khi nào chọn RabbitMQ?
- Prefetch trong RabbitMQ là gì, đặt bao nhiêu?
- Visibility timeout của SQS là gì, cạm bẫy khi job chạy lâu?
- Chạy cron trên nhiều instance thế nào để không chạy trùng?
- Event và command khác nhau thế nào?

🔴
- Vì sao Kafka nhanh dù ghi xuống đĩa?
- Rebalance hoạt động thế nào? Static membership và cooperative rebalance giải quyết gì?
- Exactly-once của Kafka hoạt động thế nào và giới hạn ở đâu?
- Outbox relay bằng polling và bằng CDC khác nhau thế nào? Cạm bẫy của polling?
- Khi nào dùng event sourcing, khi nào không nên?
- Choreography hay orchestration cho một luồng đặt hàng 5 bước?
- Thay đổi schema event mà không làm vỡ consumer thế nào?

## Bài tập tự làm

1. Thiết kế bảng `outbox` và viết pseudo-code cho relay polling chạy được với 2 instance
   cùng lúc mà không làm đảo thứ tự event của cùng một `aggregate_id`. Chỉ rõ chỗ nào vẫn có thể
   gửi trùng.
2. Liệt kê mọi đường mất message trong một luồng: Laravel dispatch job → Redis queue →
   worker → gọi API thanh toán. Với mỗi đường, nêu cách chặn.
3. Với topic Kafka 12 partition, key là `user_id`, bạn cần tăng lên 24 partition mà không
   phá thứ tự sự kiện của từng user. Mô tả quy trình chuyển đổi.
4. So sánh bằng bảng: thiết kế retry 3 lần với delay 1 phút, 10 phút, 1 giờ trên Kafka,
   RabbitMQ và SQS.
5. Viết (bằng ngôn ngữ bạn chọn) một worker đọc từ bảng `jobs` với `FOR UPDATE SKIP LOCKED`,
   có thu hồi job treo và graceful shutdown.

> Nộp bài vào đây để được review.
