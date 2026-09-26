# 14. Hệ phân tán

> [← Mục lục](README.md) · Trọng tâm: **failure mode và các pattern xử lý** mà backend gặp hằng ngày (timeout, retry, idempotency, lock, saga), rồi tới nền lý thuyết: consistency model, replication, partitioning, consensus, thời gian.
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
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | **Ch.5 replication, ch.6 partitioning, ch.8 trouble with distributed systems, ch.9 consistency and consensus** (số chương theo bản 1). Xương sống của file này |
| [Raft paper](https://raft.github.io/raft.pdf) và [raft.github.io](https://raft.github.io/) | Paper + trang minh hoạ | Consensus. Paper viết để dễ hiểu, đọc được trong một buổi; trang có mô phỏng chạy trực tiếp |
| [Jepsen](https://jepsen.io/consistency) | Bản đồ consistency model + [phân tích DB thật](https://jepsen.io/analyses) | Định nghĩa chuẩn các model; xem DB nào hứa gì và thực tế vi phạm ra sao |
| [Aphyr (Kyle Kingsbury)](https://aphyr.com/) | Blog | Tác giả Jepsen. Các bài về strong consistency, network partition viết rất dễ hiểu |
| [Martin Kleppmann: How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) | Blog | Lock cho hiệu quả và lock cho đúng đắn, fencing token, phản biện Redlock |
| [Amazon Builders' Library](https://aws.amazon.com/builders-library/) | Blog kỹ thuật | Timeout, retry, jitter, load shedding, idempotency: kinh nghiệm vận hành thật |
| [Google SRE Book](https://sre.google/sre-book/table-of-contents/) | Sách online miễn phí | Ch.21 *Handling Overload*, ch.22 *Addressing Cascading Failures*, ch.23 *Managing Critical State* |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Hiểu partial failure, gọi mạng an toàn (timeout, retry, idempotency), nói CAP đúng, hiểu replication lag | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.8 | Chọn consistency model, replication, partitioning; thiết kế saga, distributed lock, resilience, sinh ID | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.6 | Consensus, thời gian, transaction xuyên shard, conflict resolution, failure mode phức tạp | 8–10 ngày |

Chặng 1 và các module 2.4–2.6 là phần backend dùng hằng ngày và bị hỏi nhiều nhất. Chặng 3
là nơi người phỏng vấn senior đào sâu: đừng học thuộc tên thuật toán, hãy tập giải thích
**vì sao** nó cần tồn tại.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Bản chất: partial failure và "không biết request có thành công không"

**Vì sao cần học:** Một app Laravel gọi cổng thanh toán (PSP), API vận chuyển, dịch vụ SMS đã là
một hệ phân tán. Mọi bug kiểu "khách bị trừ tiền mà không có đơn" hay "đơn bị tạo hai lần" đều bắt
nguồn từ việc bên gọi không biết request có thành công hay không. Câu "gọi PSP bị timeout, bạn làm
gì" rất hay gặp, và trả lời "retry 3 lần" là red flag.

**Học gì**

*Hệ phân tán và tám giả định sai*
- *Hệ phân tán* là nhiều process trên nhiều máy phối hợp với nhau qua mạng. App + MySQL + Redis +
  PSP đã là một hệ như vậy.
- *Fallacies of distributed computing* là tám giả định sai mà lập trình viên hay ngầm tin. Mỗi giả
  định sai sinh ra một loại bug:

| Giả định sai | Bug tương ứng |
|---|---|
| Mạng ổn định | Gọi API không đặt timeout, dependency treo là worker treo theo |
| Latency bằng 0 | Gọi API trong vòng lặp (N+1 qua mạng), 100 lần × 50 ms là 5 giây |
| Băng thông vô hạn | Trả response 10 MB cho một danh sách |
| Mạng an toàn | Gọi service nội bộ bằng HTTP không mã hoá, không xác thực |
| Topology không đổi | Hardcode IP của service khác, IP đổi là gãy |
| Chỉ một người quản trị | Đội khác đổi firewall hay cấu hình mà bạn không biết |
| Chi phí truyền tải bằng 0 | Chuyển dữ liệu lớn giữa các region, hoá đơn băng thông tăng vọt |
| Mạng đồng nhất | Giả định mọi client có mạng nhanh như văn phòng |

*Partial failure*
- *Partial failure* là khi một phần hệ thống hỏng còn phần khác vẫn chạy: một service chết, một
  service chậm, một đường mạng mất gói.
- Từ phía bên gọi, bạn **không phân biệt được** bên kia đã chết hay chỉ đang chậm. Cả hai đều trông
  như "chưa có response".
- ⚠️ Chậm còn tệ hơn chết. Ví dụ với PHP-FPM:
  1. API vận chuyển đang trả lời chậm 30 giây.
  2. Mỗi request gọi API đó giữ một worker FPM trong 30 giây.
  3. Chỉ sau vài chục giây, mọi worker đều đang chờ API vận chuyển.
  4. Các trang không liên quan gì tới vận chuyển cũng không còn worker để chạy. Cả site chậm theo.

  Nếu API kia chết hẳn thì kết nối bị từ chối ngay, worker được giải phóng ngay.

*Timeout: bên gọi không thể biết*
- Gửi request rồi nhận timeout, có ba khả năng:
  1. Request mất trên đường đi, bên kia chưa hề nhận được.
  2. Bên kia đã xử lý xong, nhưng response bị mất trên đường về.
  3. Bên kia vẫn đang xử lý.
- Bên gọi **không thể biết** là khả năng nào.
- Hệ quả:
  - Retry mù có thể trừ tiền hai lần (khả năng 2 và 3).
  - Không retry có thể mất đơn (khả năng 1).
- Cách giải:
  - *Idempotency key*: gửi kèm một mã duy nhất cho thao tác, để retry không bị xử lý hai lần
    (module 1.2, và module 2.3 của [13-concurrency.md](13-concurrency.md)).
  - API tra trạng thái: hỏi lại bên kia "giao dịch mã X ra sao rồi".
  - Đối soát định kỳ: so danh sách giao dịch hai bên, xử lý chỗ lệch.

*Two generals*
- Bài toán *two generals*: hai vị tướng phải cùng tấn công, chỉ liên lạc được bằng người đưa tin có
  thể bị bắt giữa đường.
  - Tướng A gửi "tấn công lúc 6 giờ". A không biết B đã nhận chưa, nên cần B xác nhận.
  - B gửi xác nhận. B lại không biết A đã nhận xác nhận chưa, nên cần A xác nhận lại. Cứ thế mãi.
- Kết luận: không có giao thức nào đảm bảo hai bên **chắc chắn** đồng thuận qua một kênh không tin cậy.
  Đây là lý do cần idempotency và đối soát, thay vì cố "gửi cho chắc".

**Đọc**
- DDIA ch.8: *Faults and Partial Failures*, *Unreliable Networks*
- [Fallacies of distributed computing](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing)
- Aphyr, Bailis: [The Network is Reliable](https://aphyr.com/posts/288-the-network-is-reliable) (tổng hợp sự cố mạng thật)

**Nắm chắc khi**
- [ ] Với mỗi fallacy, kể được một bug cụ thể trong code PHP/Laravel
- [ ] Liệt kê được 3 khả năng khi gọi PSP bị timeout, và việc phải làm cho từng khả năng

#### 1.2 Timeout, retry, backoff, jitter, idempotency

**Vì sao cần học:** Đặt timeout và retry là việc bạn làm mỗi lần viết `Http::get()` hay cấu hình
queue job. Làm sai theo một hướng thì một dependency chậm kéo sập cả site; sai theo hướng kia thì
retry dồn dập làm dependency đang yếu chết hẳn. Câu "exponential backoff là gì, vì sao cần
jitter" rất hay gặp ở mức junior.

**Học gì**

*Timeout*
- Mọi lời gọi ra ngoài phải có hai loại timeout:
  - *Connect timeout*: thời gian tối đa để mở được kết nối. Thường ngắn, vài trăm ms tới 1–2 giây.
  - *Read timeout*: thời gian tối đa chờ dữ liệu trả về sau khi đã kết nối.
- ⚠️ Nhiều HTTP client mặc định không có timeout, hoặc timeout rất dài:
  - PHP `default_socket_timeout` mặc định 60 giây.
  - Guzzle mặc định `timeout = 0`, nghĩa là chờ vô hạn.
- Chọn timeout theo p99 hoặc p99.9 latency của dependency.
  - *p99* là mức latency mà 99% request nhanh hơn. p99 là 800 ms thì timeout 1–2 giây là hợp lý,
    timeout 30 giây là quá dài.
- *Deadline propagation*: truyền "thời gian còn lại" xuống các lời gọi con.
  - Ví dụ: request có hạn 2 giây, đã dùng 1,5 giây, thì lời gọi con chỉ được 0,5 giây. Không có ý
    nghĩa gì khi cho lời gọi con 2 giây nữa, vì client đã bỏ đi rồi.
  - Có sẵn trong gRPC deadline và `context` của Go.

*Retry cái gì*
- Chỉ retry **lỗi tạm thời**:
  - Timeout.
  - HTTP 503 (service tạm không phục vụ được).
  - HTTP 429 (bị giới hạn tốc độ), và chờ đúng số giây trong header `Retry-After`.
- Chỉ retry thao tác **idempotent**, tức gọi nhiều lần cũng cho kết quả như gọi một lần.
- Không retry lỗi 4xx khác như 400, 401, 404: gửi lại y hệt thì vẫn lỗi y hệt.

*Backoff và jitter*
- *Exponential backoff*: mỗi lần retry chờ lâu gấp đôi lần trước, `base × 2^attempt`, có một mức
  trần (*cap*).
  - Ví dụ `base = 100 ms`, trần 5 giây: chờ 100, 200, 400, 800 ms...
- *Jitter*: thêm ngẫu nhiên vào thời gian chờ.
  - Không có jitter: 1.000 client cùng lỗi lúc 10:00:00 thì cùng retry lúc 10:00:00.1, rồi cùng lúc
    10:00:00.3. Dependency nhận từng đợt tải dồn cục.
  - *Full jitter*: chờ `random(0, backoff)`. Các lần retry trải đều ra.

  ```php
  $backoff = min($cap, $base * 2 ** $attempt);
  usleep(random_int(0, $backoff) * 1000);   // full jitter, đơn vị ms
  ```

*Retry ở nhiều tầng*
- ⚠️ Retry ở nhiều tầng thì số request **nhân lên**:
  - Tầng web retry 3 lần, mỗi lần gọi tầng service.
  - Tầng service retry 3 lần, mỗi lần gọi tầng dữ liệu.
  - Tầng dữ liệu retry 3 lần, mỗi lần gọi DB.
  - Một request gốc thành 3 × 3 × 3 = 27 request xuống DB, đúng lúc DB đang yếu.
- Chỉ retry ở **một tầng**, thường là tầng gần lỗi nhất hoặc tầng ngoài cùng.

*Idempotency là điều kiện để retry an toàn*
- Các cách làm thao tác thành idempotent: idempotency key, upsert, unique constraint
  ([13-concurrency.md](13-concurrency.md), [09-api-design.md](09-api-design.md)).

*Trong Laravel*
- HTTP client:

  ```php
  Http::connectTimeout(2)
      ->timeout(5)
      ->retry(3, 200, fn ($e) => $e instanceof ConnectionException)
      ->post($url, $payload);
  ```
- Queue job có `$tries` (số lần chạy tối đa) và `$backoff` (số giây chờ giữa các lần, có thể là
  một mảng tăng dần).

**Đọc**
- Amazon Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/), [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- AWS Architecture Blog: [Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) (có biểu đồ so sánh các kiểu jitter)

**Nắm chắc khi**
- [ ] Viết được pseudo-code HTTP client có timeout, full jitter, chỉ retry lỗi tạm thời (bài tập 2)
- [ ] Tính được số request dồn xuống DB khi 3 tầng mỗi tầng retry 3 lần, và nói nên giữ retry ở tầng nào

#### 1.3 CAP và PACELC

**Vì sao cần học:** CAP là câu gần như chắc chắn bị hỏi, và là câu mà phần lớn ứng viên trả lời
sai bằng "chọn 2 trong 3". Hiểu đúng CAP giúp bạn nói rõ khi chọn DB hay thiết kế multi-region:
khi mạng đứt thì hệ thống nên từ chối hay trả dữ liệu cũ.

**Học gì**

*Định nghĩa chặt*
- **C, Consistency**, nghĩa chính xác là *linearizability*: hệ thống cư xử như thể chỉ có **một bản
  dữ liệu duy nhất**. Ghi xong thì mọi lần đọc sau đó, ở bất kỳ node nào, đều thấy giá trị mới.
- **A, Availability**: mọi request tới một node còn sống đều nhận được response không lỗi.
- **P, Partition tolerance**: hệ thống tiếp tục hoạt động khi mạng làm mất message giữa các node.
  Tình trạng các node không liên lạc được với nhau gọi là *network partition*.
- ⚠️ C của CAP khác C của ACID. C của ACID là "dữ liệu thoả các ràng buộc đã khai báo".

*Hiểu đúng CAP*
- ⚠️ Không phải "chọn 2 trong 3". Partition **luôn có thể** xảy ra, bạn không chọn được việc bỏ P.
- Câu đúng: **khi partition xảy ra**, node bị tách ra phải chọn một trong hai:
  - Từ chối request, để không trả dữ liệu có thể sai. Đây là CP.
  - Vẫn trả lời, chấp nhận dữ liệu có thể cũ. Đây là AP.
- Ví dụ hai data center (DC) mất kết nối với nhau:
  1. DC chính và DC phụ đều đang nhận request.
  2. Đường mạng giữa hai DC đứt. DC phụ không biết DC chính vừa ghi gì.
  3. Hệ thống ngân hàng: DC phụ ngừng nhận giao dịch, vì trả số dư cũ có thể cho rút quá tiền (CP).
  4. Giỏ hàng: cả hai DC vẫn nhận thêm hàng vào giỏ, khi mạng nối lại thì gộp hai giỏ (AP).
- "CA" với một node Postgres chỉ có nghĩa là hệ thống không phân tán, nên không có partition để bàn.

*Không có DB nào thuần CP hay AP*
- ⚠️ Phần lớn DB không thuần CP hay AP. Nhiều hệ thống cho chọn **theo từng thao tác**:
  - Cassandra: *consistency level* đặt cho từng câu query (`ONE`, `QUORUM`, `ALL`).
  - DynamoDB: mỗi lần đọc chọn strongly consistent read hoặc eventually consistent read.
- Vì vậy câu "MongoDB là CP, Cassandra là AP" là cách nói quá đơn giản.

*PACELC*
- *PACELC* bổ sung cho CAP:
  - Có **P**artition thì chọn **A** hoặc **C**.
  - **E**lse (lúc bình thường, không có partition) thì chọn **L**atency hoặc **C**onsistency.
- Có ích hơn CAP, vì partition hiếm xảy ra, còn đánh đổi latency xảy ra **ở mọi request**: muốn đọc
  chắc chắn mới thì phải hỏi nhiều node hoặc hỏi leader, nên chậm hơn.

| Hệ thống | Khi partition | Lúc bình thường |
|---|---|---|
| Cassandra, Riak (mặc định) | A | L |
| Spanner, các hệ dùng consensus | C | C |

**Đọc**
- DDIA ch.9: *Linearizability* (mục *The Cost of Linearizability* nói về CAP)
- Kleppmann: [Please stop calling databases CP or AP](https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html)

**Nắm chắc khi**
- [ ] Giải thích được CAP trong 2 phút bằng ví dụ hai data center mất kết nối, không dùng câu "chọn 2 trong 3"
- [ ] Nói được vì sao "MongoDB là CP, Cassandra là AP" là cách nói quá đơn giản

#### 1.4 Replication cơ bản và replication lag

**Vì sao cần học:** App Laravel lớn gần như luôn có MySQL primary kèm vài replica để đọc. Bug
"đăng bài xong F5 thì bài biến mất" là do replication lag, và là câu phỏng vấn rất hay gặp. Nguy
hiểm hơn là đọc tồn kho từ replica rồi quyết định bán, hoặc mất đơn đã xác nhận sau khi failover.

**Học gì**

*Primary–replica*
- *Replication* là giữ bản sao dữ liệu trên nhiều máy.
- Mô hình *primary–replica* (còn gọi *single-leader*):
  - Mọi lệnh ghi vào **primary**.
  - Primary gửi thay đổi sang các **replica**. Đọc có thể từ replica.
- Replica chỉ giảm tải **đọc**. Mọi lệnh ghi vẫn dồn vào primary.
- *Replication lag* là độ trễ giữa lúc primary ghi và lúc replica có dữ liệu đó.

*Sync, async, semi-sync*

| | Sync | Async | Semi-sync |
|---|---|---|---|
| Primary báo commit thành công khi | Mọi replica đã nhận | Chính nó ghi xong, không chờ replica | Ít nhất một replica đã nhận |
| Tốc độ ghi | Chậm | Nhanh | Ở giữa |
| Khi primary chết và chuyển sang replica (*failover*) | Không mất dữ liệu | ⚠️ Có thể **mất các ghi đã báo thành công** cho khách | Ít rủi ro hơn async |

- Ví dụ mất ghi với async:
  1. Khách đặt hàng, primary ghi và trả "đặt hàng thành công".
  2. Primary chết trước khi kịp gửi đơn đó sang replica.
  3. Replica được nâng lên làm primary mới. Đơn không có ở đó.
  4. Khách có email xác nhận, nhưng hệ thống không có đơn.

*Replication lag gây ra gì*
- Sai *read-after-write*: đăng bài xong F5, trang đọc từ replica chưa có bài, bài "biến mất".
- Đọc lùi thời gian: F5 lần 1 trúng replica mới thấy comment, F5 lần 2 trúng replica cũ thì không thấy.
- ⚠️ Quyết định sai khi đọc replica rồi ghi primary. Ví dụ kiểm tra tồn kho trên replica (còn 1,
  thật ra đã hết) rồi ghi đơn vào primary.

*Read-your-writes*
- *Read-your-writes*: người vừa ghi luôn thấy thứ mình vừa ghi. Các cách làm:
  - Laravel `sticky`: trong cùng một request, sau khi đã có lệnh ghi thì các lệnh đọc tiếp theo đi
    vào primary.

    ```php
    'mysql' => [
        'read'   => ['host' => ['10.0.0.2', '10.0.0.3']],
        'write'  => ['host' => ['10.0.0.1']],
        'sticky' => true,
        // ...
    ],
    ```
  - `sticky` không giúp được request **sau** (ví dụ F5). Muốn vậy thì tự lưu thời điểm ghi vào
    session, và cho user đó đọc primary trong vài giây sau khi ghi.
  - Chính xác hơn: gắn vị trí ghi vào session, rồi chỉ đọc từ replica đã bắt kịp vị trí đó. Vị trí
    này là *GTID* ở MySQL (mã định danh toàn cục của mỗi transaction) hoặc *LSN* ở Postgres (vị trí
    trong log).

*Monotonic reads*
- *Monotonic reads*: đã thấy dữ liệu mới thì không bao giờ thấy lại dữ liệu cũ hơn.
- Cách làm: gắn mỗi user với một replica cố định, ví dụ chọn replica theo hash của user id.

*Eventual không có nghĩa là nhanh*
- ⚠️ *Eventual consistency* chỉ hứa "cuối cùng sẽ giống nhau", không hứa bao lâu. Lag có thể lên tới
  vài phút khi replica quá tải hoặc đang chạy một transaction lớn.

**Đọc**
- DDIA ch.5: *Leaders and Followers*, *Problems with Replication Lag*
- Module 3.4 của [03-database-sql.md](03-database-sql.md) (replication MySQL, read-your-writes với Laravel)

**Nắm chắc khi**
- [ ] Thiết kế được read-your-writes cho app Laravel 1 primary + 3 replica
- [ ] Giải thích được vì sao sau failover async, khách đã nhận xác nhận mà đơn biến mất

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Consistency model, linearizability và serializability

**Vì sao cần học:** Khi chọn cache, replica hay DB phân tán, câu hỏi thật là "người dùng có thể
thấy dữ liệu sai theo kiểu nào". Consistency model là từ vựng để trả lời câu đó. Câu vặn kinh
điển ở vòng senior: "linearizability và serializability khác nhau thế nào".

**Học gì**

*Consistency model là gì*
- *Consistency model* là lời hứa của hệ thống về việc đọc thấy dữ liệu gì khi có nhiều bản sao và
  nhiều người ghi. Hứa càng mạnh thì càng dễ lập trình, nhưng càng chậm và càng khó giữ khi mạng lỗi.
- Các model từ mạnh tới yếu, mỗi cái một ví dụ vi phạm:

  | Model | Đảm bảo | Ví dụ vi phạm |
  |---|---|---|
  | Linearizable | Mọi thao tác như xảy ra tức thời tại một điểm, nằm giữa lúc gửi và lúc nhận response | A đổi mật khẩu xong, B vẫn đăng nhập được bằng mật khẩu cũ |
  | Sequential | Mọi node thấy cùng một thứ tự thao tác, khớp thứ tự của từng client, nhưng không cần khớp thời gian thực | Hai node thấy hai cập nhật theo hai thứ tự khác nhau |
  | Causal | Thao tác có quan hệ nhân quả được thấy đúng thứ tự | Thấy câu trả lời trước câu hỏi |
  | Read-your-writes | Chính mình luôn thấy thứ mình vừa ghi | Đăng bài xong F5 thì mất |
  | Monotonic reads | Đã thấy dữ liệu mới thì không lùi về cũ | F5 lần 1 thấy comment, lần 2 không thấy |
  | Eventual | Ngừng ghi thì cuối cùng mọi replica giống nhau | Ngừng ghi đã lâu mà hai replica vẫn lệch nhau |

- Read-your-writes và monotonic reads là đảm bảo **theo session** (của một người dùng), không phải
  của cả hệ thống.

*Linearizability khác serializability*

| | Serializability | Linearizability |
|---|---|---|
| Là tính chất của | **Transaction**, gồm nhiều object | **Một object** (một key, một ô nhớ) |
| Đảm bảo | Kết quả tương đương **một** thứ tự chạy tuần tự nào đó | Mỗi thao tác thấy giá trị mới nhất theo thời gian thực |
| Có cần khớp thời gian thực không | Không | Có |
| Là chữ nào | Chữ I trong ACID | Chữ C trong CAP |

- *Strict serializability* là có cả hai. Spanner gọi nó là *external consistency*.
- Serializable Snapshot Isolation (SSI) của Postgres là serializable nhưng không linearizable:
  transaction chỉ đọc có thể thấy một snapshot cũ, và vẫn hợp lệ vì tồn tại một thứ tự tuần tự
  trong đó nó chạy "trước".

**Đọc**
- DDIA ch.9: *Linearizability* (có mục so sánh với serializability)
- Peter Bailis: [Linearizability versus Serializability](https://www.bailis.org/blog/linearizability-versus-serializability/) (ngắn, đọc đầu tiên)
- Jepsen: [Consistency Models](https://jepsen.io/consistency), [Linearizable](https://jepsen.io/consistency/models/linearizable), [Serializable](https://jepsen.io/consistency/models/serializable)
- Aphyr: [Strong consistency models](https://aphyr.com/posts/313-strong-consistency-models)

**Nắm chắc khi**
- [ ] Phân biệt được linearizability và serializability bằng một ví dụ hệ thống có cái này mà không có cái kia
- [ ] Đọc bản đồ trên jepsen.io và chỉ ra model nào mạnh hơn model nào

#### 2.2 Ba kiểu replication và quorum

**Vì sao cần học:** Khi đánh giá Cassandra, DynamoDB hay một hệ multi-region, bạn cần biết ai
được ghi và xung đột được xử lý ra sao. Câu "`R + W > N` có đảm bảo đọc mới nhất không" và
"DynamoDB có leaderless như Cassandra không" là hai câu bẫy hay gặp.

**Học gì**

*Ba kiểu replication*

  | | Single-leader | Multi-leader | Leaderless |
  |---|---|---|---|
  | Ghi ở đâu | Chỉ leader | Nhiều leader, thường mỗi DC một | Bất kỳ node nào, gửi tới nhiều node cùng lúc |
  | Xung đột ghi | Không có | Có | Có |
  | Ví dụ | MySQL/Postgres primary–replica, Kafka partition, DynamoDB (leader theo từng partition) | MySQL multi-source, CouchDB, hệ multi-region | Cassandra, Riak, ScyllaDB (kiểu Dynamo) |
  | Điểm yếu | Leader là nút cổ chai cho ghi, failover phức tạp | Phải giải quyết xung đột | Consistency khó hiểu |

*DynamoDB không phải leaderless*
- DynamoDB cùng tên với paper Dynamo (2007), nhưng kiến trúc khác:
  - Mỗi partition có một nhóm replica trải qua nhiều AZ (*availability zone*, các trung tâm dữ liệu
    tách biệt trong cùng region).
  - Nhóm này bầu một leader bằng *Multi-Paxos*, một thuật toán consensus (module 3.1).
  - Ghi đi qua leader. Strongly consistent read đọc từ leader.
- Leaderless kiểu Dynamo là Cassandra, Riak, ScyllaDB.

*Quorum*
- Trong hệ leaderless có N replica cho mỗi key:
  - Ghi thành công khi **W** node xác nhận.
  - Đọc thì hỏi **R** node, lấy bản mới nhất trong các câu trả lời.
- `R + W > N` thì tập node được đọc và tập node được ghi **giao nhau** ít nhất một node, nên lần
  đọc có cơ hội thấy bản mới.
- Ví dụ `N = 3, W = 2, R = 2`:
  1. Ghi vào node 1 và 2, node 3 chưa có.
  2. Đọc hỏi 2 node bất kỳ. Dù chọn cặp nào cũng có ít nhất một trong node 1 hoặc 2.
  3. Một node chết thì vẫn đủ 2 node để đọc và ghi.

*Sửa dữ liệu lệch giữa các replica*
- *Read repair*: lúc đọc thấy một replica có bản cũ thì ghi bản mới vào nó.
- *Anti-entropy*: tiến trình chạy nền so sánh dữ liệu giữa các replica. Dùng *Merkle tree* (cây
  hash) để tìm nhanh chỗ khác nhau mà không phải so từng dòng.
- *Hinted handoff*: node đích đang chết thì một node khác giữ hộ bản ghi, node đích sống lại thì
  chuyển giao.

*`R + W > N` vẫn không đảm bảo linearizable*
- Ghi đồng thời: hai client cùng ghi, các replica nhận theo thứ tự khác nhau.
- Ghi thất bại một phần: ghi được 1 node thay vì 2, client nhận lỗi, nhưng bản ghi trên 1 node đó
  **không bị rollback**, và lần đọc sau có thể thấy nó.
- *Sloppy quorum*: khi thiếu node, hệ thống ghi tạm vào node **không nằm trong** N node của key đó,
  nên tập đọc và tập ghi không còn chắc chắn giao nhau.
- *LWW* (last write wins, giữ bản có timestamp lớn nhất) kết hợp đồng hồ lệch giữa các máy: bản ghi
  sau có thể bị bỏ vì timestamp nhỏ hơn (module 3.2).

**Đọc**
- DDIA ch.5: *Multi-Leader Replication*, *Leaderless Replication*
- [Dynamo paper](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf) (SOSP 2007): mục 4 (consistent hashing, vector clock, sloppy quorum)
- [Amazon DynamoDB paper](https://www.usenix.org/conference/atc22/presentation/elhemali) (USENIX ATC 2022): mục về replication bằng Multi-Paxos, để thấy DynamoDB khác Dynamo thế nào
- Cassandra: [Dynamo architecture](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html)

**Nắm chắc khi**
- [ ] Liệt kê được các cặp (R, W) với N=3 và số node chết chịu được (bài tập 3)
- [ ] Nêu được 3 kịch bản `R + W > N` vẫn đọc ra dữ liệu cũ
- [ ] Giải thích được khác biệt kiến trúc giữa Dynamo (paper) và DynamoDB (dịch vụ)

#### 2.3 Partitioning, consistent hashing, rebalancing

**Vì sao cần học:** Redis Cluster, Kafka, Elasticsearch, và sharding MySQL đều chia dữ liệu theo
một key. Chọn sai key thì một shard nóng rực còn các shard khác ngồi chơi. Câu "consistent hashing
là gì, vì sao không dùng `hash % N`" rất hay gặp trong bài system design.

**Học gì**

*Range và hash*
- *Partitioning* (hay *sharding*) là chia dữ liệu thành nhiều phần, mỗi phần (*partition*, *shard*)
  nằm trên một node, để dữ liệu và tải vượt quá một máy.

  | | Range | Hash |
  |---|---|---|
  | Chia theo | Khoảng giá trị của key | `hash(key)` |
  | Range query | Nhanh, các key liền nhau nằm cùng partition | Phải hỏi mọi partition |
  | Hot spot | Dễ bị: key tăng dần dồn hết vào partition cuối | Phân tán đều hơn |
  | Ví dụ | HBase, Bigtable, TiKV, MySQL `PARTITION BY RANGE` | Cassandra, DynamoDB (partition key), Redis Cluster (hash slot) |

*Vì sao không dùng `hash(key) % N`*
- ⚠️ Đổi N là gần như mọi key đổi chỗ.
  - Ví dụ: từ 4 lên 5 node, một key chỉ ở yên khi `hash % 4` bằng `hash % 5`, tức khoảng 20% số key.
    80% dữ liệu phải di chuyển.

*Consistent hashing*
- Cách làm:
  1. Đặt các node lên một vòng tròn giá trị hash, mỗi node ở vị trí `hash(tên node)`.
  2. Mỗi key đặt ở vị trí `hash(key)` trên cùng vòng đó.
  3. Key thuộc về node đầu tiên gặp được khi đi theo chiều kim đồng hồ.
- Thêm một node chỉ lấy dữ liệu từ node đứng ngay sau nó trên vòng, tức chỉ khoảng `1/N` dữ liệu
  phải di chuyển.
- *Virtual node* (vnode): mỗi node thật chiếm nhiều vị trí trên vòng. Lợi ích:
  - Dữ liệu phân bố đều hơn.
  - Node chết thì phần tải của nó chia cho nhiều node, không dồn vào một node hàng xóm.
  - Node mạnh hơn thì nhận nhiều vnode hơn.
- Biến thể: *rendezvous hashing*, *jump hash*.

*Số partition cố định*
- Cách khác: tạo sẵn số partition lớn hơn nhiều so với số node. Thêm node thì chỉ **di chuyển nguyên
  partition**, không chia lại key.
- Ví dụ: Kafka partition, Elasticsearch shard, Redis Cluster 16384 hash slot.

*Hot key*
- Hash vẫn không cứu được một key quá nóng, ví dụ trang của một người nổi tiếng.
- Cách xử lý:
  - Tách key bằng hậu tố ngẫu nhiên (`post:42:0` tới `post:42:9`), ghi rải ra, khi đọc thì gộp lại.
  - Cache riêng cho key đó.

*Secondary index trên dữ liệu đã chia*
- *Local index*: mỗi partition tự index dữ liệu của nó. Ghi rẻ, nhưng query theo index phải hỏi mọi
  partition rồi gộp kết quả (*scatter-gather*).
- *Global index*: index được chia theo chính giá trị được index. Đọc nhanh, nhưng một lần ghi phải
  cập nhật cả partition khác, và thường làm bất đồng bộ.

*Rebalance tự động*
- Rebalance tự động có thể gây sự cố dây chuyền:
  1. Một node chỉ chậm, nhưng bị hệ thống tưởng là chết.
  2. Dữ liệu của nó được chuyển sang node khác.
  3. Việc chuyển dữ liệu cộng với tải mới làm node nhận quá tải, và nó cũng bị tưởng là chết.

**Đọc**
- DDIA ch.6 (cả chương)
- Redis: [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) (phần hash slot)
- Module 3.6 của [03-database-sql.md](03-database-sql.md) (sharding MySQL)

**Nắm chắc khi**
- [ ] Vẽ được vòng consistent hashing, thêm một node và chỉ ra key nào di chuyển
- [ ] Chọn được partition key cho bảng đơn hàng và nói nó hot ở đâu

#### 2.4 Distributed transaction: 2PC, saga, outbox, TCC

**Vì sao cần học:** Khi tách monolith Laravel thành nhiều service, luồng "đặt hàng, trừ tiền, trừ
kho" không còn nằm trong một `DB::transaction()` được nữa. Câu "làm sao nhất quán giữa ba service"
gần như chắc chắn gặp ở vòng mid/senior. Trả lời "dùng distributed transaction" mà không biết cái
giá của nó là red flag.

**Học gì**

*2PC (two-phase commit)*
- 2PC có một *coordinator* (bên điều phối) và nhiều *participant* (các DB hay service tham gia):
  1. **Prepare**: coordinator hỏi mọi participant "commit được không". Mỗi participant ghi log, giữ
     khoá, rồi trả lời yes hoặc no.
  2. **Commit/abort**: mọi bên yes thì coordinator gửi commit. Có bên no thì gửi abort.
- ⚠️ Vì sao 2PC *blocking*:
  - Participant đã trả lời "yes" thì không được tự quyết commit hay abort nữa, phải chờ coordinator.
  - Coordinator chết đúng lúc đó thì participant giữ khoá **vô thời hạn**.
- Nhược điểm khác:
  - Nhiều round-trip qua mạng.
  - Mọi bên phải hỗ trợ *XA*, chuẩn giao tiếp 2PC giữa các DB.
  - Availability bằng **tích** availability của các bên: 3 bên mỗi bên 99,9% thì cả hệ khoảng 99,7%.
- Ít dùng giữa các microservice. Vẫn được dùng **bên trong** DB phân tán (module 3.3).
- 🔴 *3PC* (đại ý): thêm một pha pre-commit. Chỉ đúng khi độ trễ mạng có giới hạn. Gặp partition vẫn
  không nhất quán, nên hầu như không dùng.

*Saga*
- *Saga* là chuỗi các transaction cục bộ, mỗi service một transaction. Bước sau lỗi thì chạy
  *compensating action* (hành động bù) của các bước trước, theo thứ tự ngược lại.
- Ví dụ đặt vé:
  1. Giữ chỗ. Bù: nhả chỗ.
  2. Trừ tiền. Bù: hoàn tiền.
  3. Cộng điểm thưởng.

  Bước 2 lỗi thì chạy bù của bước 1 (nhả chỗ).
- Hai cách điều phối (so sánh chi tiết ở [12-messaging.md](12-messaging.md)):

  | | Orchestration | Choreography |
  |---|---|---|
  | Ai điều khiển | Một *orchestrator* giữ trạng thái saga và gọi từng bước | Không ai, mỗi service nghe event và tự làm bước của mình |
  | Dễ theo dõi | Dễ, trạng thái nằm một chỗ | Khó, luồng rải qua nhiều service |
  | Hợp khi | Luồng dài, nhiều nhánh | Luồng ngắn, ít bước |

- Compensation là **nghiệp vụ**, không phải rollback DB: hoàn tiền, gửi email xin lỗi. Email đã gửi
  thì không "huỷ gửi" được.
- ⚠️ Saga **không có isolation**: service khác nhìn thấy trạng thái trung gian (đã giữ chỗ nhưng
  chưa trừ tiền). Cách giảm thiểu:
  - *Semantic lock*: đánh dấu bản ghi là `pending` để nơi khác biết nó chưa xong.
  - Đặt các bước dễ lỗi lên trước.
  - *Bước pivot* là bước mà qua rồi thì saga chỉ còn đi tới, không quay lui (ví dụ trừ tiền thành
    công). Các bước sau pivot phải là loại retry mãi cũng được.
- ⚠️ Compensation cũng có thể lỗi. Khi đó phải retry tới khi thành công, nên compensation phải
  idempotent.
- *Workflow engine* như Temporal gánh phần lớn độ phức tạp của orchestration: lưu trạng thái, retry,
  timeout.

*Outbox*
- *Outbox*: ghi dữ liệu nghiệp vụ và event cần gửi vào **cùng một transaction cục bộ** (event nằm
  trong bảng `outbox`). Một tiến trình khác đọc bảng này và gửi event đi.
- Tránh được lỗi "DB đã commit mà event chưa gửi" hoặc ngược lại ([12-messaging.md](12-messaging.md)).

*Đào sâu (🔴): TCC*
- *TCC* (Try–Confirm–Cancel):
  - **Try**: giữ tài nguyên, ví dụ tạm khoá 100.000đ trong ví.
  - **Confirm**: dùng thật phần đã giữ.
  - **Cancel**: nhả phần đã giữ.
- Isolation tốt hơn saga, vì tài nguyên được giữ trước chứ không bị dùng ngay.
- Phải xử lý:
  - Cancel đến **trước** Try (do mạng đảo thứ tự).
  - Gọi lặp, nên mọi bước phải idempotent.
  - Phần giữ chỗ quá hạn phải tự nhả.

**Đọc**
- DDIA ch.9: *Distributed Transactions and Consensus* (2PC, XA)
- [microservices.io: Saga](https://microservices.io/patterns/data/saga.html), [Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)
- Microsoft: [Saga pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga)
- [Temporal docs: Workflows](https://docs.temporal.io/workflows)

**Nắm chắc khi**
- [ ] Vẽ được sơ đồ trạng thái saga có compensation, bước pivot, và xử lý compensation lỗi (bài tập 1)
- [ ] Giải thích được chính xác thời điểm 2PC bị kẹt và ai đang giữ khoá

#### 2.5 Distributed lock

**Vì sao cần học:** `Cache::lock()` trên Redis là thứ dev Laravel dùng rất nhiều cho job đồng bộ,
chống chạy trùng. Nhưng lock có TTL có thể hết hạn giữa chừng, và hai pod cùng chạy một việc. Câu
"làm distributed lock bằng Redis thế nào cho đúng" hay gặp ở mức mid, còn fencing token và Redlock
là phần đào sâu ở vòng senior.

**Học gì**

*Lock bằng Redis*
- Lấy lock:

  ```
  SET lock:order:42 <random_token> NX PX 30000
  ```
  - `NX`: chỉ set khi key chưa tồn tại. Ai set được thì giữ lock.
  - `PX 30000`: key tự hết hạn sau 30 giây (*TTL*). Process giữ lock chết thì lock tự nhả.
  - `<random_token>`: chuỗi ngẫu nhiên riêng của người giữ lock.
- Nhả lock bằng Lua script, chỉ xoá nếu token đúng là của mình:

  ```lua
  if redis.call("GET", KEYS[1]) == ARGV[1] then
      return redis.call("DEL", KEYS[1])
  end
  return 0
  ```
- Vì sao phải dùng token và Lua, không `GET` rồi `DEL` bằng hai lệnh riêng:
  1. A `GET` thấy đúng token của mình.
  2. Ngay lúc đó lock của A hết hạn, B lấy được lock.
  3. A `DEL`, xoá mất lock của B.

  Lua script chạy như một bước atomic nên không có khoảng hở này.

*Lease*
- *Lease* là lock có thời hạn, người giữ phải chủ động gia hạn khi việc chưa xong.
- Ví dụ: watchdog của Redisson tự gia hạn lock, etcd có lease keepalive.

*Lock hết hạn khi việc chưa xong*
- Kịch bản:
  1. Process A lấy lock với TTL 30 giây.
  2. A bị dừng 40 giây: GC pause, VM bị tạm dừng, hoặc mạng chậm.
  3. Lock hết hạn. Process B lấy được lock và bắt đầu ghi.
  4. A tỉnh dậy, vẫn nghĩ mình giữ lock, và cũng ghi. Hai bên cùng ghi.
- Kiểm tra lại lock trước khi ghi không cứu được: A có thể bị dừng ngay **sau** lúc kiểm tra và
  **trước** lúc ghi.

*Lock bằng DB và ZooKeeper*
- DB:
  - `FOR UPDATE` trên một dòng dành riêng làm lock.
  - MySQL `GET_LOCK()`, Postgres `pg_advisory_lock`: *advisory lock*, lock theo tên do app tự đặt,
    không gắn với dòng nào.
  - ⚠️ Advisory lock gắn với **session** DB. Dùng connection pool thì connection được trả về pool mà
    lock vẫn còn, dễ rò.
- ZooKeeper: mỗi client tạo một *ephemeral sequential node* (node tự mất khi client ngắt, có số thứ
  tự tăng dần). Node số nhỏ nhất giữ lock.
  - Người kế tiếp chỉ theo dõi node ngay trước mình, không theo dõi node giữ lock. Nhờ vậy khi lock
    được nhả, chỉ một client được đánh thức thay vì tất cả cùng lao vào (*herd effect*).

*Kết luận thực dụng*

| | Lock cho hiệu quả | Lock cho đúng đắn |
|---|---|---|
| Nếu hai bên cùng chạy | Tốn công gấp đôi, chấp nhận được | Dữ liệu sai, không chấp nhận được |
| Ví dụ | Hai pod cùng build lại cache, cùng gửi một báo cáo | Trừ tiền, trừ kho |
| Đủ dùng | Một Redis `SET NX` | Consensus (etcd, ZooKeeper) kèm *fencing token* (số tăng dần giúp storage chặn người giữ lock cũ, xem nhóm cuối), hoặc tốt hơn là đẩy ràng buộc xuống DB |

- Laravel: `Cache::lock()` với Redis là lock cho **hiệu quả**, không có fencing token ([13-concurrency.md](13-concurrency.md)).

*Đào sâu (🔴): fencing token và Redlock*
- *Fencing token* là một số tăng dần, cấp kèm mỗi lần cấp lock.
- Storage (nơi bị ghi) nhớ token lớn nhất đã thấy, và từ chối mọi lần ghi có token nhỏ hơn:

  ```sql
  UPDATE jobs SET result = ?, last_token = ?
  WHERE id = ? AND last_token < ?;
  ```
- Với kịch bản trên: A có token 33, B có token 34. B ghi trước, storage nhớ 34. A ghi với 33 thì bị
  từ chối.
- Redis `SET NX` không sinh token. etcd (revision) và ZooKeeper (zxid) có sẵn số tăng dần dùng được.
- *Redlock*: lấy lock trên đa số trong 5 Redis master độc lập.
- Kleppmann phản biện: Redlock dựa vào giả định về thời gian (đồng hồ, độ trễ có giới hạn) và không
  có fencing token. antirez (tác giả Redis) có bài phản hồi. Nên đọc cả hai.

**Đọc**
- Kleppmann: [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html); antirez: [Is Redlock safe?](http://antirez.com/news/101). Đọc cả hai
- Redis: [Distributed Locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)
- ZooKeeper: [Recipes](https://zookeeper.apache.org/doc/current/recipes.html) (mục Locks)
- DDIA ch.8: *The Truth Is Defined by the Majority* (fencing token)

**Nắm chắc khi**
- [ ] Vẽ được timeline GC pause làm hai process cùng ghi, và chỉ ra fencing token chặn ở đâu
- [ ] Phân loại được 3 use case trong hệ thống của mình: lock cho hiệu quả hay cho đúng đắn
- [ ] Viết được Lua release lock và giải thích vì sao không dùng `GET` + `DEL`

#### 2.6 Resilience: circuit breaker, bulkhead, rate limit, load shedding

**Vì sao cần học:** Sự cố "service gợi ý chậm làm cả trang chủ timeout" là kiểu sự cố hay gặp nhất
khi hệ thống có nhiều dependency. Các pattern ở module này là cách chặn một chỗ hỏng lan ra toàn hệ
thống. Câu "circuit breaker hoạt động thế nào" hay gặp ở mức mid.

**Học gì**

*Cascading failure: vấn đề cần giải*
- *Cascading failure* là khi lỗi ở một service lan dần lên các service gọi nó:
  1. Service gợi ý bị chậm.
  2. Trang chủ gọi service gợi ý, mỗi request giữ một thread hoặc worker trong lúc chờ.
  3. Pool thread hoặc worker của trang chủ cạn.
  4. Trang chủ không nhận request mới được. Các service gọi trang chủ cũng bắt đầu chờ.
- Chặn bằng timeout (module 1.2), circuit breaker, bulkhead, load shedding (dưới đây).

*Circuit breaker*
- *Circuit breaker* đứng trước một dependency, như cầu dao điện. Ba trạng thái:
  1. **Closed** (bình thường): request đi qua, breaker đếm số lỗi.
  2. **Open**: lỗi vượt ngưỡng thì breaker "nhảy". Mọi request bị từ chối ngay (*fail fast*) và trả
     fallback, không gọi dependency nữa.
  3. **Half-open**: sau một khoảng chờ, cho vài request thử đi qua. Thành công thì về closed, lỗi thì
     về open.
- ⚠️ Cạm bẫy:
  - Cửa sổ đếm lỗi quá nhỏ thì breaker bật tắt liên tục.
  - Tính cả lỗi 4xx (lỗi do bên gọi) làm breaker mở oan.
  - Mỗi dependency một breaker riêng, đừng dùng chung.
- Thư viện: Resilience4j (Java), `sony/gobreaker` (Go), *outlier detection* của Envoy.

*Bulkhead*
- *Bulkhead* (vách ngăn tàu thuỷ): tách pool theo dependency hoặc theo loại khách, để một bên cạn
  không kéo bên kia.
- Ví dụ: pool riêng cho API thanh toán và pool riêng cho API gợi ý. Gợi ý chậm chỉ làm cạn pool của
  gợi ý.

*Rate limiting*
- *Rate limiting* giới hạn số request trong một khoảng thời gian. Các thuật toán chính:
  - *Token bucket*: một xô được đổ token đều đặn. Mỗi request lấy một token, hết token thì bị từ chối.
    Cho phép đỉnh ngắn bằng số token còn trong xô.
  - *Leaky bucket*: request vào một hàng đợi, được xử lý ra với tốc độ cố định.
  - *Fixed window*: đếm theo từng khung cố định, ví dụ mỗi phút tối đa 100.
  - *Sliding window*: đếm trong khoảng thời gian trượt, tránh việc dồn tải ở ranh giới hai khung.
- Chi tiết ở [09-api-design.md](09-api-design.md), bài rate limiter ở [16-system-design.md](16-system-design.md).

*Load shedding*
- *Load shedding*: khi quá tải, chủ động từ chối sớm (trả 503) thay vì nhận hết rồi cùng chậm.
- Ưu tiên theo loại request: giữ thanh toán, bỏ bớt request gợi ý.
- Bỏ các request đã chờ trong queue quá deadline, vì client đã bỏ đi rồi.

*Graceful degradation và fallback*
- *Graceful degradation*: tắt tính năng phụ để giữ tính năng chính.
- *Fallback*: câu trả lời thay thế khi dependency lỗi, ví dụ cache cũ, danh sách sản phẩm phổ biến.
- ⚠️ Fallback ít khi chạy nên hay có bug. Phải test nó.
- ⚠️ Fallback không được gọi vào chính dependency đang lỗi.
- *Feature flag* / *kill switch*: công tắc bật tắt tính năng lúc chạy, không cần deploy.

**Đọc**
- Martin Fowler: [CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html); Microsoft: [Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker), [Bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
- Amazon Builders' Library: [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/), [Avoiding fallback in distributed systems](https://aws.amazon.com/builders-library/avoiding-fallback-in-distributed-systems/)
- Google SRE: [Handling Overload](https://sre.google/sre-book/handling-overload/), [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)

**Nắm chắc khi**
- [ ] Vẽ được state machine của circuit breaker và nói ngưỡng nào mình sẽ chọn cho một dependency cụ thể
- [ ] Vẽ được chuỗi cascading failure "service gợi ý chậm làm trang chủ timeout" và chặn ở từng bước

#### 2.7 Sinh ID phân tán

**Vì sao cần học:** Khi có nhiều service hoặc nhiều shard cùng tạo bản ghi, auto-increment của
một DB không còn đủ. Chọn sai kiểu ID làm chậm insert (UUIDv4 trong InnoDB), lộ thông tin kinh
doanh, hoặc gây hot partition. Câu "Snowflake gồm những phần nào" hay gặp ở mức mid.

**Học gì**

*Các loại ID*
- Vài thuật ngữ trong bảng:
  - *Page split*: B+tree của InnoDB lưu dữ liệu theo page. Chèn vào một page đã đầy thì phải tách
    page đó làm đôi, tốn I/O (module 2.1 của [03-database-sql.md](03-database-sql.md)).
  - *Epoch*: mốc thời gian mà phần timestamp trong ID đếm từ đó.
  - *Base32*: cách viết dữ liệu nhị phân bằng 32 ký tự chữ và số.

  | Loại | Cấu trúc | Sắp theo thời gian | Ghi chú |
  |---|---|---|---|
  | Auto-increment | Một bộ đếm | Có | Một điểm sinh duy nhất. Lộ số lượng. Khó khi sharding |
  | UUID v4 | 122 bit ngẫu nhiên | Không | ⚠️ Chèn ngẫu nhiên vào B+tree: page split, cache miss |
  | UUID v7 | 48 bit Unix ms + phần ngẫu nhiên (RFC 9562) | Có | Thay thế tốt cho v4 khi làm PK |
  | ULID | 48 bit ms + 80 bit ngẫu nhiên, 26 ký tự base32 | Có | Tương tự v7 |
  | Snowflake | 1 bit dấu + 41 bit ms + 10 bit machine + 12 bit sequence | Có | 64 bit, vừa `BIGINT`. 4096 ID/ms/máy. Dùng được khoảng 69 năm từ epoch |
  | Segment (Meituan Leaf) | Xin một dải `[1000, 2000)` từ DB, rồi cấp dần trong bộ nhớ | Gần đúng | Ít gọi DB. Restart thì phần còn lại của dải bị bỏ, ID bị thủng số |

*Snowflake*
- Cấu trúc 64 bit, từ trái sang:
  - 1 bit dấu, luôn 0.
  - 41 bit: số ms tính từ epoch bạn tự chọn.
  - 10 bit: *machine id*, tối đa 1024 máy.
  - 12 bit: *sequence*, số thứ tự trong cùng một ms, tối đa 4096.
- ⚠️ Đồng hồ nhảy lùi có thể sinh ID trùng. Phải phát hiện rồi chờ đồng hồ vượt qua mốc cũ, hoặc
  báo lỗi.
- Machine id phải được cấp không trùng: qua config, qua ZooKeeper, hoặc qua số thứ tự của pod
  (*pod ordinal* trong StatefulSet).

*Lộ thông tin*
- ⚠️ ID theo thời gian lộ thời điểm tạo.
- ⚠️ ID tuần tự lộ số lượng (đơn thứ 10.523) và cho phép đoán ID kế tiếp.
- ID công khai nên khó đoán, nhưng **không thay** được việc kiểm tra quyền. Đoán được ID của người
  khác mà xem được dữ liệu của họ là lỗi phân quyền, không phải lỗi ID.

*ID tăng dần và partition*
- ID tăng dần (auto-increment, UUIDv7, Snowflake) dùng làm key khi **partition theo range** thì mọi
  ghi mới dồn vào partition cuối (*hot partition*).
- Partition theo hash thì không bị, nhưng mất khả năng quét theo khoảng thời gian.

**Đọc**
- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562): mục 5.7 (UUIDv7)
- [Twitter Snowflake](https://github.com/twitter-archive/snowflake) (README bản gốc)
- [Meituan Leaf](https://tech.meituan.com/2017/04/21/mt-leaf.html) (tiếng Trung, xem hình kiến trúc segment và snowflake)

**Nắm chắc khi**
- [ ] Thiết kế được bộ sinh Snowflake cho 1.000 pod: cấp machine id, xử lý đồng hồ lùi, chọn epoch (bài tập 4)
- [ ] Tranh luận được UUIDv7 hay Snowflake cho bảng orders MySQL

#### 2.8 Service discovery, health check, graceful shutdown

**Vì sao cần học:** Deploy app Laravel lên Kubernetes mà cấu hình probe sai là nguồn sự cố phổ
biến: pod bị restart hàng loạt khi DB chậm, hoặc rớt request mỗi lần deploy. Câu "liveness và
readiness khác nhau thế nào" hay gặp ở mức mid.

**Học gì**

*Service discovery*
- *Service discovery*: service A tìm địa chỉ các instance đang sống của service B.

  | | Client-side | Server-side |
  |---|---|---|
  | Cách làm | A hỏi *registry* (Consul, Eureka) danh sách instance, rồi tự chọn instance để gọi | A gọi một địa chỉ cố định (load balancer hoặc DNS), bên đó chọn instance |
  | Ưu | Không qua thêm một chặng mạng | Client đơn giản |
  | Nhược | Mỗi ngôn ngữ cần thư viện riêng | Thêm một thành phần phải vận hành |

- Kubernetes: mỗi Service có một tên DNS nội bộ. *Service mesh* đẩy việc này sang một *sidecar* (một
  container proxy chạy cạnh app).
- ⚠️ DNS cache ở client làm app gọi tới IP cũ:
  - JVM từng cache kết quả DNS rất lâu.
  - Worker PHP-FPM giữ connection cũ tới IP đã không còn.

*Liveness, readiness, startup*

| Probe | Câu hỏi | Nếu fail |
|---|---|---|
| Liveness | Process còn sống không | Restart container |
| Readiness | Sẵn sàng nhận traffic không | Rút khỏi load balancer, không restart |
| Startup | Đã khởi động xong chưa | Chờ, chưa chạy hai probe kia. Dùng cho app khởi động chậm |

- ⚠️ Liveness kiểm tra cả DB là nguy hiểm:
  1. DB chậm vài giây.
  2. Liveness của mọi pod cùng fail.
  3. Kubernetes restart mọi pod cùng lúc.
  4. Hệ thống mất hết pod, lại thêm tải khởi động dồn vào DB. Tệ hơn hẳn việc chỉ chậm.
- Liveness chỉ kiểm tra chính process. Readiness mới là chỗ kiểm tra dependency, nếu cần.

*Graceful shutdown*
- Các bước để tắt pod mà không rớt request:
  1. Pod nhận SIGTERM.
  2. App cho readiness fail.
  3. Chờ load balancer rút pod ra khỏi danh sách (vài giây).
  4. Xử lý nốt các request đang dở.
  5. Thoát.
- PHP-FPM: `process_control_timeout` cho worker thời gian làm xong request trước khi dừng.
- Laravel queue worker nhận SIGTERM thì làm xong job hiện tại rồi mới thoát.

**Đọc**
- Kubernetes: [Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)
- [19-devops-cloud.md](19-devops-cloud.md), [18-reliability-observability.md](18-reliability-observability.md)

**Nắm chắc khi**
- [ ] Viết được endpoint liveness và readiness cho app Laravel, nói mỗi cái kiểm tra gì và không kiểm tra gì
- [ ] Kể được từng bước từ lúc pod nhận SIGTERM tới lúc thoát mà không rớt request

---

### Chặng 3: Senior 🔴

#### 3.1 Consensus và Raft

**Vì sao cần học:** etcd (nơi Kubernetes lưu state), ZooKeeper, Kafka KRaft, và mọi DB phân tán
đều dựa trên consensus. Bạn không tự cài Raft, nhưng senior phải giải thích được vì sao cluster cần
số node lẻ, split brain là gì, và leader cũ bị cô lập có ghi được không. Đây là nơi người phỏng
vấn senior đào sâu nhất.

**Học gì**

*Consensus là gì*
- *Consensus*: nhiều node đồng ý về một giá trị, hoặc một chuỗi log, dù có node chết.
- Dùng cho: bầu leader, lưu cấu hình, lock, metadata của cluster.

*FLP impossibility*
- *FLP* (Fischer, Lynch, Paterson 1985): trong hệ **bất đồng bộ hoàn toàn** (không có giới hạn nào
  về độ trễ message), chỉ cần một node có thể crash là không thuật toán tất định nào đảm bảo được cả
  hai điều:
  - *Safety*: không bao giờ quyết định sai.
  - *Liveness*: luôn đi tới quyết định.
- Thực tế: Raft và Paxos **luôn giữ safety**. Liveness dựa vào timeout, tức giả định mạng "phần lớn
  thời gian" có độ trễ hợp lý (*partial synchrony*), cộng với timeout ngẫu nhiên.
- ⚠️ FLP không có nghĩa "consensus là bất khả thi". Nó nghĩa là có những lúc hệ thống tạm không đi
  tới quyết định được.

*Raft: vai trò, term và bầu leader*
- Mỗi node ở một trong ba vai trò: *follower*, *candidate*, *leader*.
- *Term* là số nhiệm kỳ, tăng dần. Mỗi term có tối đa một leader.
- Node nhận được message có term cao hơn term của mình thì lùi về follower.
- Các bước bầu leader:
  1. Follower không nghe thấy leader trong khoảng *election timeout* (chọn ngẫu nhiên, ví dụ
     150–300 ms).
  2. Nó tăng term, trở thành candidate, và xin phiếu các node khác.
  3. Mỗi node chỉ bầu **một phiếu mỗi term**, và chỉ bầu cho candidate có log **ít nhất mới bằng**
     log của mình.
  4. Candidate được đa số phiếu thì thành leader.
- Timeout ngẫu nhiên để các node không cùng lúc ứng cử rồi chia phiếu mãi.

*Raft: replicate log và pre-vote*
- Các bước replicate một lệnh ghi:
  1. Client gửi lệnh ghi tới leader.
  2. Leader thêm entry vào log của mình, rồi gửi `AppendEntries` cho các follower.
  3. Khi **đa số** node đã ghi entry đó, entry được coi là *commit*.
  4. Chỉ sau đó entry mới được áp vào *state machine* (dữ liệu thật) và trả kết quả cho client.
- Leader cũ bị cô lập khỏi đa số thì không gom được đa số, nên **không commit được** gì.
- Vấn đề mà pre-vote giải: một node bị cô lập cứ hết timeout là tăng term. Khi mạng nối lại, term của nó cao hơn,
  làm leader đang chạy tốt phải bước xuống, cluster bầu lại vô ích.
- *Pre-vote*: trước khi tăng term, node hỏi thử "nếu tôi ứng cử thì có thắng không". Không thắng thì
  không tăng term.
- *Check quorum*: leader tự bước xuống khi mất liên lạc với đa số.
- etcd bật pre-vote mặc định từ v3.5.

*Quorum, số node và đánh đổi*
- `2f + 1` node chịu được `f` node chết.

| Số node | Đa số cần | Chịu được mấy node chết |
|---|---|---|
| 3 | 2 | 1 |
| 4 | 3 | 1 |
| 5 | 3 | 2 |

- ⚠️ 4 node vẫn chỉ chịu được 1 node chết, như 3 node, mà mỗi lần ghi phải chờ thêm một node. Số
  chẵn không có lợi.
- Đánh đổi của consensus:
  - Mỗi lần ghi cần một round-trip tới đa số node.
  - Hợp cho metadata và cấu hình. Không hợp cho dữ liệu khối lượng lớn, trừ khi chia thành nhiều
    Raft group, mỗi group lo một phần dữ liệu (TiKV, CockroachDB làm vậy).

*Split brain*
- *Split brain*: hai node cùng nghĩ mình là leader và cùng nhận ghi.
- Cách chống:
  - Quorum: chỉ bên có đa số mới làm leader được.
  - Fencing: chặn leader cũ bằng cách tắt hẳn nó (*STONITH*, "shoot the other node in the head")
    hoặc bằng fencing token (module 2.5).
  - *Witness node*: một node nhẹ chỉ để bỏ phiếu.
- ⚠️ Hai DC, mỗi bên một nửa số node: mất kết nối thì không bên nào có đa số, không bầu được leader.
  Cần một node thứ ba ở vị trí khác.

*etcd, ZooKeeper, Paxos*
- etcd và ZooKeeper lưu cấu hình và metadata cần nhất quán mạnh (Kubernetes lưu toàn bộ state trong
  etcd). Dùng cho leader election, lock, membership. Không dùng làm DB của ứng dụng.
- Paxos cùng mục đích với Raft, ra đời trước, khó hiểu hơn.

**Đọc**
- [Raft paper](https://raft.github.io/raft.pdf) (đọc hết), mô phỏng ở [raft.github.io](https://raft.github.io/) và [The Secret Lives of Data](https://thesecretlivesofdata.com/raft/)
- [Luận án Ongaro](https://github.com/ongardie/dissertation) mục 9.6 (pre-vote) và ch.4 (thay đổi thành viên cluster)
- DDIA ch.9: *Fault-Tolerant Consensus*
- [FLP paper](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf) (đọc phần giới thiệu là đủ)
- Lamport: [Paxos Made Simple](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf) (tuỳ chọn)
- [etcd docs](https://etcd.io/docs/), Jepsen: [etcd 3.4.3](https://jepsen.io/analyses/etcd-3.4.3)

**Nắm chắc khi**
- [ ] Vẽ được một lần bầu leader và một lần commit entry với 5 node, có một node chết giữa chừng
- [ ] Giải thích được vì sao leader cũ bị cô lập không thể commit, và pre-vote chặn vấn đề gì
- [ ] Nói được FLP nghĩa là gì trong thực tế, không nói "consensus là bất khả thi"

#### 3.2 Thời gian và thứ tự sự kiện

**Vì sao cần học:** Dùng `created_at` hay `now()` để quyết định "cái nào xảy ra trước" giữa nhiều
server là bug phổ biến: bản ghi mới bị bản cũ đè, log hiện response trước request. Câu "vì sao
không dùng timestamp để sắp thứ tự sự kiện giữa nhiều máy" hay gặp ở vòng senior.

**Học gì**

*Đồng hồ không tin được*
- *Clock skew*: đồng hồ của các máy lệch nhau, từ vài ms tới vài giây.
- NTP (giao thức đồng bộ giờ) chỉnh đồng hồ, và có thể làm đồng hồ **nhảy lùi**.
- Đo khoảng thời gian phải dùng *monotonic clock*, đồng hồ chỉ đi tới, không bị NTP chỉnh:
  - PHP: `hrtime()`.
  - Java: `System.nanoTime()`.
  - Go: `time.Now()` có kèm monotonic reading, nên `time.Since()` an toàn.
- Không dùng *wall clock* (giờ thật, ví dụ `microtime()`, `time()`) để đo khoảng thời gian.

*LWW sai vì đồng hồ lệch*
1. Máy A ghi lúc 10:00:00.100 theo đồng hồ của A.
2. Máy B ghi **sau** A, nhưng đồng hồ B chậm 200 ms nên ghi nhận 10:00:00.000.
3. LWW (last write wins) giữ bản có timestamp lớn hơn, tức bản của A. Bản mới hơn của B bị bỏ.

*Lamport clock*
- *Lamport clock* là một bộ đếm logic, không dùng giờ thật:
  - Mỗi sự kiện ở một node: tăng bộ đếm lên 1.
  - Gửi message: kèm giá trị bộ đếm.
  - Nhận message: đặt bộ đếm bằng `max(local, received) + 1`.
- Đảm bảo: A xảy ra trước B (theo nhân quả) thì `L(A) < L(B)`.
- ⚠️ Chiều ngược lại **không** đúng. `L(A) < L(B)` không cho biết A trước B hay hai cái đồng thời.

*Vector clock*
- *Vector clock*: mỗi node giữ một mảng bộ đếm, mỗi node một ô.
- Phân biệt được "A trước B", "B trước A" và "đồng thời".
- Nhược: kích thước tăng theo số node.

*Đồng hồ trong DB phân tán*
- *Hybrid logical clock* (HLC), dùng ở CockroachDB: giá trị gần với giờ thật, nhưng vẫn giữ được
  quan hệ nhân quả như Lamport clock.
- *TrueTime* của Spanner: API trả về một **khoảng** thời gian với sai số đã biết, nhờ GPS và đồng
  hồ nguyên tử trong DC.
  - Khi commit, Spanner chờ cho hết khoảng bất định đó (*commit wait*), để chắc rằng mọi transaction
    commit sau đều có timestamp lớn hơn.

*Thực dụng*
- Thứ tự trong **một** entity: dùng version hoặc sequence do một nơi duy nhất sinh ra, ví dụ cột
  `version` trong DB.
- Điều tra sự cố: dùng *trace id* và quan hệ span cha–con (tracing) để biết cái gì gọi cái gì.
  Đừng sắp log của nhiều máy theo timestamp.

**Đọc**
- DDIA ch.8: *Unreliable Clocks*
- Lamport: [Time, Clocks, and the Ordering of Events](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) (paper kinh điển, ngắn)
- CockroachDB: [Living without atomic clocks](https://www.cockroachlabs.com/blog/living-without-atomic-clocks/)
- Google Cloud: [TrueTime and external consistency](https://cloud.google.com/spanner/docs/true-time-external-consistency)

**Nắm chắc khi**
- [ ] Tính được Lamport timestamp cho một chuỗi message giữa 3 node, và chỉ ra cặp sự kiện đồng thời mà Lamport không phân biệt được
- [ ] Giải thích được vì sao Spanner cần commit wait

#### 3.3 Transaction xuyên shard

**Vì sao cần học:** Khi MySQL đã shard, hoặc khi dùng TiDB, CockroachDB, Spanner, sẽ có lúc một
transaction chạm hai shard. Senior cần hiểu các DB này làm việc đó thế nào, và vì sao 2PC ở đây
không bị kẹt như 2PC giữa microservice. Ở tầng ứng dụng, câu trả lời tốt nhất thường là chọn shard
key để tránh hẳn chuyện này.

**Học gì**

*Bài toán*
- Một transaction chạm nhiều shard mà vẫn phải ACID. Ví dụ chuyển tiền giữa hai user nằm ở hai shard.

*Vì sao 2PC trong DB phân tán không bị kẹt*
- Ở 2PC giữa microservice (module 2.4), coordinator là một máy. Máy đó chết thì mọi bên chờ.
- Trong DB phân tán, coordinator và mỗi participant đều là một **Raft/Paxos group** (nhiều máy cùng
  giữ một trạng thái). Một máy chết thì máy khác trong group tiếp tục, nên 2PC không kẹt vô hạn.

*Percolator*
- *Percolator* (Google 2010, TiDB/TiKV dùng lại): 2PC trên Bigtable, cho snapshot isolation.
- Các thành phần:
  - *Timestamp oracle* (TSO): một dịch vụ cấp timestamp tăng dần cho mọi transaction.
  - *Primary lock*: một khoá chính quyết định số phận cả transaction.
  - *Secondary lock*: khoá trên các dòng khác, trỏ về primary lock.
- Luồng:
  1. Lấy start timestamp từ TSO.
  2. *Prewrite*: ghi dữ liệu và đặt lock lên mọi dòng, một dòng làm primary.
  3. Lấy commit timestamp từ TSO.
  4. Commit primary. Từ lúc này transaction coi như đã commit.
  5. Commit các secondary, có thể làm bất đồng bộ.
- Transaction khác gặp một secondary lock bỏ dở thì nhìn sang primary: primary đã commit thì hoàn tất
  secondary, chưa commit và đã quá hạn thì dọn lock.

*Spanner và CockroachDB*
- Spanner: 2PC trên các Paxos group, cộng TrueTime commit wait (module 3.2). Kết quả là external
  consistency, tức strict serializability.
- CockroachDB: dùng HLC, và *parallel commits* để giảm số round-trip của 2PC.

*Ở tầng ứng dụng*
- Tránh transaction xuyên shard bằng cách chọn shard key: mọi dữ liệu của một tenant nằm cùng shard.
- Buộc phải có thì dùng saga kèm đối soát.
- Vitess (sharding cho MySQL) cũng hỗ trợ 2PC giữa shard nhưng có giới hạn. Đọc kỹ trước khi dựa vào.

**Đọc**
- [Percolator paper](https://research.google/pubs/large-scale-incremental-processing-using-distributed-transactions-and-notifications/) (OSDI 2010), TiKV: [Percolator](https://tikv.org/deep-dive/distributed-transaction/percolator/) (giải thích dễ hơn paper)
- [Spanner paper](https://research.google/pubs/spanner-googles-globally-distributed-database-2/) (OSDI 2012): mục 4 (concurrency control)
- CockroachDB: [Transaction Layer](https://www.cockroachlabs.com/docs/stable/architecture/transaction-layer), [Parallel Commits](https://www.cockroachlabs.com/blog/parallel-commits/)

**Nắm chắc khi**
- [ ] Vẽ được luồng Percolator: prewrite primary/secondary, commit primary, và cách transaction khác xử lý lock bỏ dở
- [ ] Giải thích được vì sao 2PC trong Spanner không blocking theo kiểu 2PC cổ điển

#### 3.4 Conflict resolution

**Vì sao cần học:** Hệ multi-region cho ghi ở nhiều nơi, app offline-first, hay collaborative
editing đều phải trả lời "hai bản ghi đồng thời thì giữ bản nào". Chọn LWW mà không biết nó âm thầm
mất dữ liệu là lỗi hay gặp. Câu "vì sao không dùng CRDT cho số dư" là câu kiểm tra hiểu giới hạn.

**Học gì**

*LWW*
- *LWW* (last write wins): giữ bản có timestamp lớn nhất, bỏ các bản còn lại.
- Đơn giản, nhưng ⚠️ **âm thầm mất dữ liệu** khi có ghi đồng thời, và phụ thuộc đồng hồ vốn có thể
  lệch (module 3.2).

*Version vector*
- *Version vector*: mỗi bản ghi kèm một vector bộ đếm, mỗi replica một ô, tương tự vector clock.
- So hai vector thì biết bản nào "xảy ra trước", hoặc hai bản **đồng thời**.
- Đồng thời thì giữ cả hai bản (gọi là *siblings*), để ứng dụng tự gộp.
  - Ví dụ giỏ hàng: DC1 thêm áo, DC2 thêm quần cùng lúc. Hai sibling được giữ, app gộp thành giỏ có
    cả áo và quần.

*CRDT*
- *CRDT* (conflict-free replicated data type): kiểu dữ liệu được thiết kế để gộp **luôn hội tụ**, bất
  kể các thay đổi đến theo thứ tự nào.
- Ví dụ:
  - *G-Counter*: bộ đếm chỉ tăng.
  - *PN-Counter*: bộ đếm tăng và giảm.
  - *OR-Set*: tập hợp thêm và xoá phần tử được.
  - *LWW-Register*: một ô giá trị, gộp theo LWW.
- Dùng cho: collaborative editing, bộ đếm lượt thích, giỏ hàng.
- ⚠️ CRDT không biểu diễn được ràng buộc toàn cục như "số dư không âm". Hai DC cùng trừ 100.000đ từ số
  dư 150.000đ, mỗi bên đều thấy hợp lệ, gộp lại thì âm.

*Thực dụng*
- Tránh xung đột thay vì giải quyết nó: định tuyến mọi ghi của một entity về một leader.
- Ví dụ: mỗi user có một "home region", mọi ghi của user đó đi về region đó.

**Đọc**
- DDIA ch.5: *Handling Write Conflicts*, *Detecting Concurrent Writes*
- [crdt.tech](https://crdt.tech/): danh sách paper và bài giới thiệu

**Nắm chắc khi**
- [ ] Mô phỏng được giỏ hàng hai DC với version vector, chỉ ra lúc nào sinh sibling
- [ ] Giải thích được vì sao không dùng CRDT cho số dư tài khoản

#### 3.5 Failure mode nâng cao

**Vì sao cần học:** Sự cố lớn nhất thường không đến từ một máy chết, mà từ vòng phản hồi: retry
làm tải tăng, tải tăng làm thêm lỗi, lỗi lại sinh thêm retry. Senior được kỳ vọng nhận ra kiểu sự
cố này và biết cách cắt vòng. Câu tình huống "xoá cache xong hệ thống không hồi phục" hay gặp.

**Học gì**

*Retry storm và retry budget*
- *Retry storm*: dependency chậm, mọi client cùng retry, tải lên dependency tăng gấp bội đúng lúc nó
  yếu nhất.
- *Retry budget*: giới hạn retry theo **tỉ lệ**, thay vì theo số lần mỗi request.
  - Ví dụ: tổng số retry không vượt 10% số request thành công gần đây.
  - Dependency chết hẳn thì gần như không còn request thành công, nên retry tự tắt.

*Hedged requests*
- *Tail latency*: latency của những request chậm nhất (p99, p99.9).
- *Hedged request*: quá p95 mà chưa có trả lời thì gửi thêm một request tới replica khác, lấy cái về
  trước.
  - Cắt được tail latency với chi phí chỉ vài phần trăm tải.
  - ⚠️ Chỉ dùng cho request idempotent, và phải có giới hạn.

*Metastable failure*
- *Metastable failure*: một sự cố ngắn đẩy hệ thống vào trạng thái xấu **tự duy trì**, dù nguyên nhân
  ban đầu đã hết.
- Ví dụ xoá cache toàn cụm:
  1. Cache bị xoá (hoặc deploy, hoặc một đỉnh tải ngắn).
  2. Mọi request đều cache miss, dồn thẳng vào DB.
  3. DB quá tải, query chậm, request timeout.
  4. Client retry, cache vẫn trống vì query không kịp chạy xong để ghi lại cache.
  5. Quay lại bước 2. Traffic đã về bình thường nhưng hệ thống không tự hồi phục.
- Hồi phục cần chủ động giảm tải mạnh: chặn bớt traffic, tắt retry, làm ấm cache dần.

*Shuffle sharding*
- *Shuffle sharding*: gán mỗi khách hàng một tổ hợp node ngẫu nhiên (ví dụ 2 trong 8 node).
- Một khách xấu (gửi request độc) chỉ kéo chết 2 node của họ. Rất ít khách khác trùng đúng cả 2 node đó.

**Đọc**
- Dean, Barroso: [The Tail at Scale](https://research.google/pubs/the-tail-at-scale/)
- [Metastable Failures in Distributed Systems](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf) (HotOS 2021, ngắn)
- Amazon Builders' Library: [Workload isolation using shuffle-sharding](https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/)
- Postmortem thật: [AWS S3 us-east-1 2017](https://aws.amazon.com/message/41926/) (khởi động lại subsystem mất hàng giờ), [GitHub Oct 21 2018](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/) (network partition, failover MySQL giữa hai DC)

**Nắm chắc khi**
- [ ] Vẽ được vòng phản hồi của một metastable failure và chỉ ra điểm cắt
- [ ] Đọc postmortem GitHub 2018 và chỉ ra chỗ nào là partition, split brain, mất ghi

#### 3.6 Membership, leader election, exactly-once

**Vì sao cần học:** Scheduler Laravel chạy trên nhiều pod, consumer chỉ được chạy một bản, là bài
toán leader election thật. Còn "exactly-once" là từ hay bị dùng sai: người phỏng vấn senior muốn
nghe bạn phân biệt giao đúng một lần (không làm được) với hiệu ứng đúng một lần (làm được).

**Học gì**

*Leader election*
- Dùng khi chỉ một bên được làm một việc: scheduler, consumer đơn, job dọn dẹp.
- Công cụ: etcd, ZooKeeper, Kubernetes Lease, hoặc lock trong DB.
- ⚠️ Leader phải chịu được việc **mất quyền mà không biết**, giống lock hết hạn ở module 2.5. Giải
  bằng lease kèm fencing token.

*Gossip và failure detector*
- *Gossip* (đại ý): mỗi node định kỳ trao đổi thông tin với vài node ngẫu nhiên. Thông tin lan khắp
  cluster trong khoảng `O(log N)` vòng.
  - Ví dụ: giao thức SWIM, Consul/Serf, Cassandra, Redis Cluster.
  - Không có điểm tập trung, đổi lại thông tin chỉ eventual.
- *Failure detector* (bộ phát hiện node chết) không bao giờ chắc chắn được, vì không phân biệt được
  chết hay chậm (module 1.1). Luôn phải đánh đổi giữa phát hiện nhanh và báo nhầm.

*Exactly-once*
- Không thể đảm bảo **giao** một message đúng một lần qua mạng không tin cậy (nhớ bài two generals).
- Làm được **hiệu ứng** đúng một lần: giao at-least-once (ít nhất một lần), kèm xử lý idempotent.
  Cách gọi đúng là *effectively-once*.
- Kafka EOS (exactly-once semantics) là exactly-once **trong phạm vi Kafka**: đọc từ Kafka, xử lý,
  ghi vào Kafka, và commit offset trong một transaction atomic ([12-messaging.md](12-messaging.md)).
  - ⚠️ Consumer ghi ra ngoài Kafka, ví dụ vào MySQL, thì Kafka EOS không bảo vệ phần đó. Phần ghi
    MySQL vẫn phải idempotent.

*End-to-end argument*
- *End-to-end argument* (Saltzer, Reed, Clark): tính đúng chỉ đảm bảo được ở **hai đầu cuối**. Các
  tầng giữa (TCP, message broker) chỉ giúp tối ưu, không thay được kiểm tra ở hai đầu.
- Hệ quả: idempotency key phải đi từ client tới tận DB cuối cùng, không dừng ở tầng giữa nào.

**Đọc**
- Amazon Builders' Library: [Leader election in distributed systems](https://aws.amazon.com/builders-library/leader-election-in-distributed-systems/)
- Kubernetes: [Leases](https://kubernetes.io/docs/concepts/architecture/leases/)
- [SWIM paper](https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf); HashiCorp: [Consul gossip](https://developer.hashicorp.com/consul/docs/architecture/gossip)
- [End-to-End Arguments in System Design](https://web.mit.edu/Saltzer/www/publications/endtoend/endtoend.pdf)
- Confluent: [Exactly-once Semantics Are Possible](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)

**Nắm chắc khi**
- [ ] Thiết kế được leader election cho một scheduler Laravel chạy trên 3 pod, có xử lý leader cũ chưa biết mình mất quyền
- [ ] Giải thích được bằng end-to-end argument vì sao Kafka EOS không giúp gì khi consumer ghi vào MySQL

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Kể vài giả định sai về hệ phân tán và bug tương ứng.** (1.1)
- Ý phải có: 3–4 fallacy, mỗi cái một bug cụ thể (không timeout, gọi N+1 qua mạng, hardcode IP)

**2. Vì sao mọi lời gọi mạng cần timeout?** (1.2)
- Ý phải có: không timeout thì một dependency treo làm cạn worker/thread; connect và read timeout
- Điểm cộng: chọn theo p99; deadline propagation; PHP-FPM mỗi worker treo là mất một worker
- Red flag: không biết client HTTP mình đang dùng có timeout mặc định bao nhiêu

**3. Retry với exponential backoff là gì? Vì sao cần jitter?** (1.2)
- Ý phải có: chờ tăng dần có trần; jitter để client không retry đồng loạt
- Điểm cộng: chỉ retry lỗi tạm thời và thao tác idempotent; retry một tầng

**4. Service A gọi B bị timeout. B có thể đã xử lý hoặc chưa. Bạn làm gì?** (1.1, 1.2)
- Ý phải có: timeout không có nghĩa là thất bại; idempotency key; API tra trạng thái; đối soát
- Red flag: "retry 3 lần" cho thao tác trừ tiền

**5. Đăng bài xong F5 thì bài biến mất. Vì sao, sửa thế nào?** (1.4)
- Ý phải có: đọc từ replica bị lag; read-your-writes bằng đọc primary sau khi ghi (sticky) hoặc chờ replica bắt kịp
- Điểm cộng: monotonic reads; không đọc replica trong luồng đọc để ghi

### 🟡 Mid

**6. Giải thích CAP theorem bằng một ví dụ thực tế.** (1.3)
- Ý phải có: partition không phải lựa chọn; khi partition thì từ chối hoặc trả dữ liệu cũ; C là linearizability
- Điểm cộng: PACELC; nhiều hệ thống chỉnh theo từng thao tác
- Red flag: "chọn 2 trong 3", "MongoDB là CP"

**7. Linearizability và serializability khác nhau thế nào?** (2.1)
- Ý phải có: một object + thời gian thực so với nhiều object trong transaction + một thứ tự tuần tự bất kỳ
- Điểm cộng: strict serializability; SSI của Postgres serializable nhưng không linearizable; Spanner external consistency
- Red flag: coi hai khái niệm là một

**8. Eventual consistency và read-your-writes khác nhau thế nào?** (2.1, 1.4)
- Ý phải có: eventual chỉ hứa hội tụ; read-your-writes là đảm bảo theo session của người ghi
- Điểm cộng: cách cài đặt bằng GTID/LSN trong session

**9. DynamoDB có phải hệ leaderless như Cassandra không?** (2.2)
- Ý phải có: không; mỗi partition có leader, replicate bằng Multi-Paxos; leaderless kiểu Dynamo là Cassandra/Riak/ScyllaDB
- Điểm cộng: paper Dynamo 2007 khác dịch vụ DynamoDB; strongly consistent read đọc từ leader
- Red flag: "DynamoDB là Dynamo nên leaderless"

**10. `R + W > N` có đảm bảo đọc luôn thấy ghi mới nhất không?** (2.2)
- Ý phải có: không linearizable; ghi đồng thời, ghi thất bại một phần, sloppy quorum, LWW với đồng hồ lệch

**11. 2PC là gì, vì sao ít dùng giữa microservice?** (2.4)
- Ý phải có: prepare/commit; blocking khi coordinator chết sau khi participant đã "yes"; mọi bên phải hỗ trợ XA
- Điểm cộng: vẫn dùng bên trong DB phân tán vì coordinator là Raft group (3.3)

**12. Saga là gì? Orchestration và choreography khác nhau thế nào?** (2.4)
- Ý phải có: chuỗi transaction cục bộ + compensation; không có isolation; hai cách điều phối
- Điểm cộng: bước pivot; compensation lỗi phải retry nên idempotent; outbox cho mỗi bước; Temporal

**13. Làm distributed lock bằng Redis thế nào cho đúng?** (2.5)
- Ý phải có: `SET NX PX` với token ngẫu nhiên, release bằng Lua kiểm tra token, TTL
- Điểm cộng: lock hết hạn giữa chừng; lease gia hạn; phân biệt lock cho hiệu quả và cho đúng đắn
- Red flag: `SETNX` rồi `EXPIRE` bằng hai lệnh riêng; `DEL` không kiểm tra token

**14. Circuit breaker hoạt động thế nào?** (2.6)
- Ý phải có: ba trạng thái và điều kiện chuyển; fail fast khi open
- Điểm cộng: không tính 4xx; breaker theo dependency; kèm fallback

**15. Snowflake ID gồm những phần nào? UUID v4 làm primary key có vấn đề gì?** (2.7)
- Ý phải có: timestamp + machine id + sequence, 64 bit; UUIDv4 chèn ngẫu nhiên vào B+tree
- Điểm cộng: đồng hồ lùi; UUIDv7; ID tăng dần gây hot partition khi partition theo range

**16. Liveness và readiness probe khác nhau thế nào?** (2.8)
- Ý phải có: restart so với rút khỏi LB
- Điểm cộng: liveness kiểm tra DB là nguy hiểm; graceful shutdown

### 🔴 Senior

**17. Raft bầu leader và replicate log thế nào? Vì sao cluster nên có số node lẻ?** (3.1)
- Ý phải có: term, election timeout ngẫu nhiên, điều kiện log mới nhất, commit khi đa số ghi; 4 node vẫn chỉ chịu 1 lỗi
- Điểm cộng: pre-vote và check quorum; thay đổi thành viên cluster

**18. FLP impossibility nói gì? Vậy Raft chạy được bằng cách nào?** (3.1)
- Ý phải có: hệ bất đồng bộ + một node có thể crash thì không đảm bảo kết thúc; Raft giữ safety luôn, liveness nhờ timeout
- Red flag: "consensus là bất khả thi nên không ai dùng"

**19. Split brain là gì, chống thế nào?** (3.1)
- Ý phải có: hai leader cùng nhận ghi; quorum, fencing, witness
- Điểm cộng: vì sao hai DC chia đôi node không bầu được; ví dụ GitHub 2018

**20. Fencing token là gì? Vì sao Redlock bị tranh cãi?** (2.5)
- Ý phải có: số tăng dần storage kiểm tra; Redlock dựa vào giả định thời gian, không có fencing
- Điểm cộng: kết luận thực dụng: tính đúng đặt ở DB (atomic update, constraint)

**21. Vì sao không dùng timestamp để sắp thứ tự sự kiện giữa nhiều máy? Lamport clock giải quyết được gì?** (3.2)
- Ý phải có: clock skew, NTP nhảy lùi; Lamport giữ được "trước thì nhỏ hơn" nhưng không phân biệt đồng thời
- Điểm cộng: vector clock, HLC, TrueTime; dùng trace id khi điều tra

**22. Làm sao một DB phân tán như Spanner/TiDB làm transaction xuyên shard?** (3.3)
- Ý phải có: 2PC trên các nhóm consensus; TSO (Percolator) hoặc TrueTime (Spanner)
- Điểm cộng: primary lock của Percolator; commit wait; ở app thì chọn shard key để tránh

**23. Exactly-once có tồn tại không? End-to-end argument nói gì?** (3.6)
- Ý phải có: không có exactly-once delivery; at-least-once + idempotent = effectively-once
- Điểm cộng: phạm vi của Kafka EOS; idempotency key đi từ client tới DB

**24. Tình huống: sau khi xoá cache toàn cụm, DB quá tải và hệ thống không hồi phục dù traffic bình thường.** (3.5)
- Ý phải có: metastable failure + cache stampede; chủ động chặn bớt traffic, tắt retry, làm ấm cache dần
- Điểm cộng: request coalescing; không xoá cache toàn bộ cùng lúc ([11-cache.md](11-cache.md))

**25. Tình huống: job đồng bộ chạy trên 3 pod với Redis lock, log cho thấy đôi khi hai pod cùng chạy.** (2.5, 3.6)
- Ý phải có: TTL ngắn hơn thời gian chạy, GC/VM pause, Redis failover mất key
- Điểm cộng: gia hạn lease, fencing token ở chỗ ghi, làm job idempotent

**26. Tình huống: đặt vé, trừ tiền và cộng điểm thưởng ở ba service. Làm sao nhất quán?** (2.4)
- Ý phải có: saga orchestration; giữ chỗ (bù: nhả chỗ) → trừ tiền (pivot) → cộng điểm (retry tới khi thành công)
- Điểm cộng: outbox mỗi bước; trạng thái pending cho user; đối soát định kỳ
- Red flag: "dùng distributed transaction"

**27. Tình huống: sắp log từ 20 máy theo timestamp, thấy response xuất hiện trước request.** (3.2)
- Ý phải có: clock skew; dùng trace id và span cha–con để lấy quan hệ nhân quả

---

## Bài tập tự làm

1. **Saga.** Vẽ sơ đồ trạng thái saga "đặt phòng khách sạn + thanh toán + gửi voucher", liệt
   kê compensating action, bước pivot, và điều gì xảy ra nếu compensation thất bại.
2. **HTTP client an toàn.** Viết pseudo-code (hoặc PHP) cho một HTTP client wrapper có:
   timeout, retry với full jitter, chỉ retry lỗi tạm thời, retry budget, và circuit breaker.
3. **Quorum.** Với cluster Cassandra `N=3`, liệt kê các cặp (R, W) và nói với mỗi cặp: chịu
   được bao nhiêu node chết khi đọc, khi ghi, và có `R + W > N` không.
4. **Snowflake.** Thiết kế bộ sinh ID kiểu Snowflake cho 1.000 pod Kubernetes: cấp machine id
   thế nào, xử lý đồng hồ nhảy lùi thế nào, và chọn epoch ra sao.
5. **Cascading failure.** Mô tả một sự cố cascading failure bạn từng gặp (hoặc tưởng tượng),
   vẽ chuỗi lan truyền, và chỉ ra pattern nào ở module 2.6 và 3.5 sẽ chặn được ở bước nào.
6. **Raft bằng tay.** Dùng mô phỏng ở raft.github.io: tạo tình huống leader bị cô lập, ghi lại
   term của từng node, entry nào được commit, entry nào bị ghi đè khi mạng nối lại.

> Nộp bài vào đây để được review.
