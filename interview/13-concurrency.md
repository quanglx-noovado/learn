# 13. Concurrency

> [← Mục lục](README.md) · Phạm vi: khái niệm concurrency, memory model, primitive đồng bộ, deadlock, các pattern xử lý song song, và quan trọng nhất là concurrency ở mức ứng dụng web (DB, Redis, queue, nhiều instance).
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Khái niệm**
- [ ] 🟢 Concurrency vs parallelism
- [ ] 🟢 Race condition, data race, critical section
- [ ] 🟡 Atomicity, visibility, ordering
- [ ] 🔴 Memory model: happens-before; Java JMM vs Go memory model

**Primitive**
- [ ] 🟢 Mutex; 🟡 RW lock; 🟡 semaphore
- [ ] 🟡 Condition variable, spurious wakeup ⚠️
- [ ] 🟡 Atomic, CAS; 🔴 ABA
- [ ] 🔴 Spinlock, lock-free, wait-free

**Lỗi đồng bộ**
- [ ] Deadlock: 4 điều kiện Coffman, phòng tránh, phát hiện; deadlock trong DB
- [ ] 🟡 Livelock, starvation
- [ ] 🔴 Priority inversion

**Pattern**
- [ ] Producer–consumer, bounded buffer
- [ ] 🟡 Thread pool sizing: CPU-bound vs I/O-bound, Little's law
- [ ] 🟡 Worker pool, fan-out/fan-in, pipeline
- [ ] 🔴 Actor model (đại ý)
- [ ] 🟡 Async/await, event loop vs goroutine vs virtual thread

**Concurrency trong ứng dụng web** (quan trọng nhất)
- [ ] Trừ tồn kho: atomic update, pessimistic lock, optimistic lock, distributed lock, queue
- [ ] Check-then-act ⚠️
- [ ] Lost update
- [ ] Double submit, idempotency key
- [ ] Unique constraint làm lưới an toàn
- [ ] 🟡 Đồng thời trong queue worker
- [ ] 🟡 Nhiều instance: distributed lock ([14-distributed-systems.md](14-distributed-systems.md))
- [ ] 🟡 Flash sale
- [ ] Đối chiếu PHP / Java / Go

## Chi tiết

### Khái niệm

- [ ] Concurrency và parallelism khác nhau thế nào
  - **Concurrency**: cấu trúc chương trình để xử lý nhiều việc **đan xen** trong cùng khoảng
    thời gian. Có thể chạy trên một core
  - **Parallelism**: nhiều việc chạy **cùng lúc thật sự** trên nhiều core
  - Rob Pike: "concurrency là về cấu trúc (dealing with), parallelism là về thực thi (doing)"
  - Node.js một thread: concurrent nhưng không parallel. Go với `GOMAXPROCS > 1`: cả hai
- [ ] Race condition, critical section, data race
  - **Race condition**: kết quả phụ thuộc thứ tự/thời điểm thực thi, và có thứ tự cho kết quả
    sai. Là lỗi **logic**, có thể xảy ra cả khi mọi truy cập đều đã khoá (hai transaction DB,
    hai process PHP)
  - **Data race**: hai thread truy cập cùng vùng nhớ, ít nhất một ghi, **không có đồng bộ**.
    Là khái niệm của memory model. Go/Java có công cụ phát hiện (`go test -race`)
  - Có race condition mà không có data race (check-then-act với mỗi bước đều khoá riêng), và
    có data race mà không thành bug thấy được (hiếm, không nên dựa vào)
  - **Critical section**: đoạn code truy cập tài nguyên chung, chỉ một luồng được vào tại một thời điểm
  - Ví dụ kinh điển: `count++` là **read-modify-write** ba bước, hai thread cùng đọc 5,
    cùng ghi 6, mất một lần tăng
- [ ] 🟡 Ba tính chất cần hiểu
  - **Atomicity**: thao tác không bị chia cắt (không thấy trạng thái nửa vời)
  - **Visibility**: thread B có **thấy** giá trị thread A vừa ghi không. Không đồng bộ thì
    có thể không bao giờ thấy (giá trị nằm trong register/cache, compiler hoist ra ngoài vòng lặp)
  - **Ordering**: compiler và CPU được phép **sắp xếp lại** lệnh miễn là kết quả đúng trong
    một thread. Thread khác có thể thấy thứ tự khác
- [ ] 🔴 Memory model
  - Định nghĩa khi nào một lần ghi **đảm bảo** được nhìn thấy bởi một lần đọc, thông qua quan
    hệ **happens-before**. Không có happens-before thì không đảm bảo gì
  - **Java JMM**: happens-before tạo bởi unlock → lock cùng monitor, ghi `volatile` → đọc
    `volatile` đó, `Thread.start()`, `Thread.join()`, các lớp trong `java.util.concurrent`.
    `volatile` đảm bảo visibility và ordering nhưng **không** làm `count++` thành atomic.
    Chương trình có data race vẫn an toàn bộ nhớ nhưng có thể cho kết quả bất ngờ.
    Double-checked locking cần `volatile` mới đúng
  - **Go memory model**: happens-before tạo bởi gửi/nhận channel, `sync.Mutex`, `sync.Once`,
    `sync.WaitGroup`, `sync/atomic` (từ Go 1.19 được mô tả là sequentially consistent).
    Tinh thần: "nếu phải đọc memory model mới hiểu chương trình thì chương trình quá khéo".
    ⚠️ Data race trên map hay interface có thể làm chương trình crash (`concurrent map writes`)
  - Đối chiếu: Java có `volatile`, Go không có; Go khuyến khích channel, Java khuyến khích
    `java.util.concurrent`. Cả hai: dùng primitive có sẵn, đừng tự dựa vào thứ tự lệnh

### Primitive

- [ ] Mutex: chỉ một thread giữ khoá. Giữ khoá càng ngắn càng tốt, không gọi I/O khi giữ khoá
  - Reentrant: Java `synchronized`/`ReentrantLock` cho phép cùng thread lấy lại; Go
    `sync.Mutex` **không** reentrant, lock hai lần là tự deadlock ⚠️
  - Go: ⚠️ copy struct chứa `sync.Mutex` là copy cả khoá (`go vet` bắt được)
- [ ] 🟡 Read-write lock: nhiều reader cùng lúc hoặc một writer
  - Chỉ có lợi khi đọc nhiều, đoạn đọc đủ dài. Đoạn ngắn thì chi phí RW lock còn cao hơn mutex
  - ⚠️ Writer starvation nếu reader liên tục; nâng cấp read lock lên write lock dễ deadlock
- [ ] 🟡 Semaphore: đếm N permit, giới hạn số luồng cùng dùng tài nguyên (ví dụ tối đa 10
      kết nối tới API bên ngoài). Mutex ≈ semaphore 1 permit nhưng có khái niệm "chủ sở hữu"
  - Go: buffered channel `make(chan struct{}, 10)` hoặc `golang.org/x/sync/semaphore`.
    Java: `java.util.concurrent.Semaphore`
- [ ] 🟡 Condition variable: chờ tới khi một điều kiện đúng, đi kèm mutex (`wait` nhả khoá và ngủ)
  - ⚠️ Luôn chờ trong vòng `while (!condition) wait()`, không dùng `if`, vì **spurious wakeup**
    và vì điều kiện có thể đã bị thread khác đổi lại
  - Java: `Object.wait/notify`, `Condition`. Go: `sync.Cond` (ít dùng, thường thay bằng channel)
- [ ] 🟡 Atomic operation và compare-and-swap (CAS)
  - CAS(addr, expected, new): nếu giá trị hiện tại bằng `expected` thì ghi `new`, trả về
    thành công/thất bại. Nền tảng của lock-free, thường dùng trong vòng lặp retry
  - Java `AtomicInteger`, `AtomicReference`, `LongAdder` (khi tranh chấp cao). Go `sync/atomic`
    (`atomic.Int64`, `CompareAndSwap`)
  - ⚠️ Atomic từng biến không làm **nhiều biến** thành atomic cùng nhau
  - Optimistic lock trong DB (`WHERE version = ?`) chính là CAS ở mức dữ liệu
- [ ] 🔴 Vấn đề ABA: thread 1 đọc A, thread 2 đổi A→B→A, thread 1 CAS thành công dù trạng
      thái đã thay đổi (ví dụ node trong lock-free stack đã bị pop rồi push lại). Cách sửa:
      gắn version/tag (`AtomicStampedReference`), hoặc GC/hazard pointer. Trong DB: dùng
      cột `version` tăng dần thay vì so sánh giá trị nghiệp vụ
- [ ] 🔴 Spinlock: vòng lặp CAS chờ thay vì ngủ. Hợp khi critical section cực ngắn và có
      nhiều core; tệ khi giữ lâu (đốt CPU) hoặc trên một core. Mutex hiện đại thường spin một
      chút rồi mới ngủ
- [ ] 🔴 Lock-free và wait-free
  - Lock-free: luôn có **ít nhất một** thread tiến triển, không bị chặn bởi thread bị treo
  - Wait-free: **mọi** thread tiến triển trong số bước hữu hạn
  - Ví dụ: `ConcurrentLinkedQueue` (Java), các cấu trúc dựa trên CAS
  - ⚠️ Khó viết đúng, không nhất thiết nhanh hơn lock khi tranh chấp thấp. Backend thường
    chỉ cần biết dùng thư viện có sẵn

### Lỗi đồng bộ

- [ ] Deadlock: bốn điều kiện Coffman (mutual exclusion, hold and wait, no preemption,
      circular wait); phá một điều kiện là tránh được
  - Phòng tránh thực tế:
    - **Lấy khoá theo thứ tự cố định** (phá circular wait): luôn khoá tài khoản id nhỏ trước
    - **Timeout khi lấy khoá** (`tryLock(timeout)`, `lock_wait_timeout`), thất bại thì nhả hết
      và thử lại
    - Lấy tất cả khoá cùng lúc hoặc không lấy gì (phá hold and wait)
    - Giữ khoá ngắn, không gọi code lạ (callback, I/O) khi giữ khoá
  - Phát hiện: wait-for graph có chu trình. InnoDB và Postgres tự phát hiện, rollback một
    transaction (MySQL error 1213); Java thread dump (`jstack`) chỉ ra deadlock; Go runtime báo
    `all goroutines are asleep - deadlock!` chỉ khi **mọi** goroutine đều kẹt
  - Ví dụ DB: T1 `UPDATE accounts ... WHERE id=1` rồi `id=2`; T2 làm ngược lại → deadlock.
    Sửa: sắp xếp id trước khi update; transaction ngắn; code phải **retry** khi gặp deadlock
  - ⚠️ Go: gửi vào unbuffered channel mà không ai nhận là goroutine leak/deadlock phổ biến
- [ ] 🟡 Livelock: các thread vẫn chạy nhưng liên tục nhường nhau, không ai tiến triển (hai
      người tránh nhau ở hành lang). Sửa bằng backoff ngẫu nhiên
- [ ] 🟡 Starvation: một thread không bao giờ được tài nguyên vì luôn có thread khác được ưu
      tiên. Fair lock (`new ReentrantLock(true)`) giảm starvation, đổi lại thông lượng thấp hơn
- [ ] 🔴 Priority inversion: thread ưu tiên cao chờ khoá do thread ưu tiên thấp giữ, trong khi
      thread ưu tiên trung bình chiếm CPU khiến thread thấp không chạy để nhả khoá. Ví dụ nổi
      tiếng: Mars Pathfinder. Sửa: priority inheritance (thread giữ khoá tạm được nâng ưu tiên)
  - Góc backend: request "quan trọng" chờ connection pool bị chiếm bởi job batch ưu tiên thấp;
    giải bằng pool riêng (bulkhead)

### Pattern

- [ ] Producer–consumer
  - Hàng đợi **có giới hạn** (bounded buffer) giữa bên sinh và bên tiêu thụ. Đầy thì producer
    chờ (backpressure), rỗng thì consumer chờ
  - ⚠️ Queue không giới hạn = OOM khi consumer chậm
  - Java: `BlockingQueue` (`ArrayBlockingQueue`). Go: buffered channel
- [ ] 🟡 Thread pool: vì sao không tạo thread mới cho mỗi việc; chọn kích thước pool cho việc
      nặng CPU và việc nặng I/O
  - Vì sao: tạo thread OS tốn (stack, syscall), không giới hạn thì hết bộ nhớ và context switch
    nhiều. Pool tái sử dụng thread và **giới hạn** mức song song
  - CPU-bound: khoảng số core (có thể +1). Nhiều hơn chỉ thêm context switch
  - I/O-bound: `số core × (1 + thời gian chờ / thời gian tính)` (công thức trong *Java
    Concurrency in Practice*). Ví dụ 8 core, mỗi request chờ DB 90 ms tính 10 ms → khoảng 80
  - **Little's law**: `L = λ × W` (số việc đang xử lý = tốc độ đến × thời gian xử lý). Muốn
    chịu 200 request/giây, mỗi request 50 ms → cần khoảng 10 request đồng thời. Dùng để tính
    cả kích thước connection pool
  - ⚠️ Pool to hơn tài nguyên phía sau là vô ích: 200 thread gọi DB có pool 20 connection thì
    180 thread ngồi chờ. Kích thước phải nhìn **cả chuỗi**
  - ⚠️ Queue của pool: unbounded queue che giấu quá tải (độ trễ tăng vô hạn). Nên bounded +
    chính sách từ chối (reject, caller-runs)
  - ⚠️ Việc chặn lâu trong pool dùng chung (ví dụ gọi I/O trong `ForkJoinPool.commonPool`)
    làm nghẽn cả ứng dụng
- [ ] 🟡 Worker pool (Go): N goroutine đọc từ một channel việc, ghi kết quả ra channel khác

  ```go
  jobs := make(chan Job)
  var wg sync.WaitGroup
  for i := 0; i < 8; i++ {
      wg.Add(1)
      go func() {
          defer wg.Done()
          for j := range jobs { // thoát khi jobs bị close
              process(j)
          }
      }()
  }
  for _, j := range all { jobs <- j }
  close(jobs)
  wg.Wait()
  ```
  - ⚠️ Goroutine rẻ nhưng tài nguyên phía sau không rẻ: `go` cho mỗi phần tử trong vòng lặp
    10 triệu phần tử gọi DB sẽ làm sập DB. Giới hạn bằng worker pool hoặc semaphore
    (`errgroup.SetLimit`)
- [ ] 🟡 Fan-out/fan-in: chia việc cho nhiều worker (fan-out), gom kết quả về một chỗ (fan-in).
      Cần xử lý: lỗi của một worker hủy các worker khác (`errgroup` + `context`), thứ tự kết quả
- [ ] 🟡 Pipeline: chuỗi stage nối bằng channel/queue, mỗi stage một nhóm worker. Throughput bị
      giới hạn bởi stage chậm nhất; phải truyền tín hiệu hủy để không rò goroutine
- [ ] 🔴 Actor model (đại ý): mỗi actor có state riêng và mailbox, chỉ giao tiếp bằng message,
      xử lý tuần tự từng message → không cần lock cho state. Erlang/Elixir, Akka. Trade-off:
      mailbox đầy, khó debug luồng message, request/response phải làm bất đồng bộ
- [ ] 🟡 Async/await, event loop, goroutine, virtual thread

  | Mô hình | Cách chạy | Chặn I/O | Ghi chú |
  |---|---|---|---|
  | Thread OS (Java cổ điển) | mỗi request một thread | thread ngủ, OS lập lịch | tốn bộ nhớ, giới hạn vài nghìn |
  | Event loop + async/await (Node.js, Python asyncio) | một thread, callback/coroutine | không được chặn, phải `await` | ⚠️ một việc CPU nặng chặn cả loop; "function coloring" |
  | Goroutine (Go) | M:N, runtime lập lịch | runtime tự park goroutine | code đồng bộ bình thường, hàng trăm nghìn goroutine |
  | Virtual thread (Java 21+) | M:N trên carrier thread | JVM park virtual thread | code blocking bình thường; ⚠️ đừng pool virtual thread; chú ý pinning khi chặn trong `synchronized` (đã cải thiện ở bản mới, kiểm tra lại theo phiên bản) |
  | PHP-FPM | mỗi request một process | process chờ | không chia sẻ bộ nhớ; Fibers (8.1) + Swoole/ReactPHP cho async |

  - Ý chính: goroutine và virtual thread cho **code đồng bộ dễ đọc** với chi phí gần async.
    Không làm việc CPU-bound nhanh hơn; không bỏ được giới hạn của DB/connection pool

### Concurrency trong ứng dụng web

Phần này hay bị hỏi nhất với backend. Race condition ở đây xảy ra giữa **các request, process,
instance**, không chỉ giữa các thread.

- [ ] **Race condition trong ứng dụng web** (quan trọng nhất với backend), ví dụ hai request
      cùng trừ tồn kho. Phải giải được bằng ít nhất 4 cách và nêu nhược điểm từng cách:
  1. Atomic update: `UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0`,
     rồi kiểm tra số dòng bị ảnh hưởng
  2. Pessimistic lock: `SELECT ... FOR UPDATE` trong transaction
  3. Optimistic lock: cột `version`
  4. Distributed lock bằng Redis
  5. 🟡 Đẩy vào queue và xử lý tuần tự (hợp cho flash sale)

  Code sai thường gặp:

  ```php
  $p = Product::find($id);          // hai request cùng đọc stock = 1
  if ($p->stock > 0) {
      $p->stock = $p->stock - 1;    // cả hai ghi stock = 0, bán 2 cái
      $p->save();
  }
  ```

  | Cách | Cơ chế | Ưu | Nhược / cạm bẫy |
  |---|---|---|---|
  | Atomic update | điều kiện nằm trong `WHERE`, DB khoá dòng khi update | đơn giản, nhanh, đúng | chỉ hợp logic đơn giản gói được trong một câu SQL; ⚠️ phải kiểm tra affected rows |
  | Pessimistic (`FOR UPDATE`) | khoá dòng từ lúc đọc tới commit | logic phức tạp nhiều bước | giảm throughput, dễ deadlock khi khoá nhiều dòng; ⚠️ phải trong transaction, ⚠️ không gọi API ngoài khi giữ khoá |
  | Optimistic (`version`) | `UPDATE ... SET version = version + 1 WHERE id = ? AND version = ?`, 0 dòng thì retry | không giữ khoá, hợp khi ít tranh chấp | tranh chấp cao thì retry liên tục, gần như mọi request thất bại |
  | Distributed lock (Redis) | khoá theo `product_id` bên ngoài DB | điều phối được cả tài nguyên không phải DB | thêm hệ thống; lock hết hạn giữa chừng; ⚠️ không thay được ràng buộc trong DB (xem 14) |
  | Queue tuần tự | mọi yêu cầu theo `product_id` vào một partition/queue, một worker xử lý | không tranh chấp, chịu được đỉnh tải | bất đồng bộ, user phải chờ kết quả; phức tạp hơn |
  | 🟡 Redis `DECR` / Lua | trừ trong Redis (đơn luồng, atomic), sau đó ghi DB bất đồng bộ | rất nhanh cho flash sale | Redis và DB có thể lệch; cần đối soát |

  ```sql
  -- Atomic update: an toàn, ứng dụng kiểm tra affected rows = 1
  UPDATE products SET stock = stock - 1 WHERE id = 42 AND stock >= 1;
  ```
- [ ] ⚠️ "Check-then-act" không an toàn: `if (!exists) insert` giữa hai request vẫn tạo
      trùng. Cách sửa: unique constraint trong DB
  - Các biến thể: "email chưa tồn tại thì tạo user", "chưa có coupon usage thì cho dùng",
    "số dư đủ thì trừ", "slot còn trống thì đặt"
  - Sửa: gộp check và act thành một thao tác atomic (unique constraint, `INSERT ... ON
    CONFLICT`, `UPDATE ... WHERE` điều kiện, Redis `SET NX`)
  - ⚠️ `SELECT ... FOR UPDATE` trên dòng **chưa tồn tại** không khoá được gì ở nhiều cấu hình
    (Postgres). MySQL InnoDB có gap lock ở REPEATABLE READ nhưng dễ gây deadlock. Unique
    constraint vẫn là cách chắc chắn
- [ ] Lost update
  - Hai request đọc cùng bản ghi, sửa field khác nhau hoặc cùng field, request ghi sau đè mất
    thay đổi của request trước
  - Ví dụ: admin A và B cùng mở form sản phẩm; A sửa giá, B sửa mô tả, B lưu cả form → giá cũ
  - Sửa: chỉ update field thay đổi; optimistic lock với `version` (trả 409 Conflict cho UI);
    HTTP `ETag` + `If-Match` cho API; atomic update cho phép cộng dồn
  - ⚠️ `READ COMMITTED` (mặc định của Postgres) không chặn lost update kiểu đọc-sửa-ghi trong
    ứng dụng. Xem isolation level ở [03-database-sql.md](03-database-sql.md)
- [ ] Double submit
  - User bấm hai lần, mạng chập chờn client retry, load balancer retry → hai đơn hàng
  - Frontend disable nút chỉ giảm, không chặn được (retry ở tầng mạng, người dùng mở hai tab)
  - Backend: **idempotency key** do client sinh (header `Idempotency-Key`), server lưu
    `(key, request_hash, response)` với unique constraint; request trùng key thì trả lại
    response cũ. ⚠️ Hai request trùng key đến cùng lúc: bản ghi key phải được tạo atomic
    trước khi xử lý (trạng thái `processing`), request thứ hai trả 409 hoặc chờ
  - Xem thêm [09-api-design.md](09-api-design.md)
- [ ] Unique constraint làm lưới an toàn
  - Dù đã có lock, queue hay kiểm tra ở tầng ứng dụng, **vẫn đặt unique constraint** ở DB cho
    bất biến nghiệp vụ (`UNIQUE(user_id, coupon_id)`, `UNIQUE(order_id)` trong `payments`)
  - Lý do: lock có thể hết hạn, code có thể có đường khác bỏ qua kiểm tra, script migrate dữ
    liệu không đi qua ứng dụng. DB là nơi duy nhất thấy mọi ghi
  - Xử lý lỗi unique violation thành kết quả nghiệp vụ (trả response cũ, báo "đã dùng"),
    không để thành 500
  - Constraint khác: `CHECK (stock >= 0)`, foreign key, exclusion constraint của Postgres
    (chống đặt phòng chồng khoảng thời gian)
- [ ] 🟡 Đồng thời trong queue worker
  - Nhiều worker cùng xử lý message liên quan tới cùng entity → race như request web
  - At-least-once → cùng message có thể được hai worker xử lý song song (visibility timeout,
    rebalance). Idempotency phải chịu được **song song**, không chỉ tuần tự
  - Cần tuần tự theo entity: Kafka key, SQS FIFO message group, hoặc lock theo entity
  - Laravel: `WithoutOverlapping` job middleware, `ShouldBeUnique`. Xem
    [12-messaging.md](12-messaging.md)
- [ ] 🟡 Concurrency giữa nhiều instance
  - Lock trong bộ nhớ (`synchronized`, `sync.Mutex`) chỉ có tác dụng **trong một process**.
    Scale lên 3 pod là lock vô dụng ⚠️
  - Ưu tiên: đẩy tính đúng xuống DB (atomic update, constraint, row lock). Chỉ dùng distributed
    lock khi tài nguyên không nằm trong DB hoặc để tránh làm việc tốn kém hai lần
  - Distributed lock: Redis `SET NX PX` + Lua release, fencing token, lease. Chi tiết và cạm
    bẫy ở [14-distributed-systems.md](14-distributed-systems.md)
- [ ] 🟡 Flash sale: 100 sản phẩm, 10.000 người mua cùng lúc
  - Tầng chặn sớm: rate limit, hàng đợi ảo (waiting room), CDN cho trang tĩnh
  - Trừ số lượng trong Redis bằng `DECR` hoặc Lua (atomic), âm thì hoàn lại và báo hết
  - Người trúng → tạo đơn qua queue, worker ghi DB với atomic update làm chốt chặn cuối,
    unique `(user_id, sale_id)` chống một người mua nhiều lần
  - Giữ chỗ có hạn (reservation 10 phút), không thanh toán thì trả lại kho
  - Đối soát Redis với DB sau đợt sale
  - ⚠️ `SELECT ... FOR UPDATE` trên một dòng hot với 10.000 request = hàng đợi khoá dài, cạn
    connection pool

### Đối chiếu PHP / Java / Go

| | PHP (FPM) | Java | Go |
|---|---|---|---|
| Đơn vị chạy | process mỗi request | thread (platform/virtual) | goroutine |
| Chia sẻ bộ nhớ | không giữa request | có, heap chung | có, nhưng khuyến khích channel |
| Race hay nằm ở đâu | DB, Redis, file, session | biến dùng chung + DB | biến dùng chung, map + DB |
| Công cụ | transaction, row lock, Redis lock, `flock` | `synchronized`, `java.util.concurrent`, `ConcurrentHashMap` | `sync`, channel, `sync/atomic`, `-race` |
| Cạm bẫy riêng | tin rằng "PHP không có race" | `HashMap` không thread-safe, `SimpleDateFormat` | `concurrent map writes` crash, goroutine leak, loop variable (trước Go 1.22) |

- PHP: mỗi request một process độc lập, không có biến chung, nên **không có data race**
  trong code; nhưng **race condition** vẫn đầy ở DB/Redis/file. ⚠️ Session file có khoá:
  nhiều AJAX cùng session bị chạy tuần tự. Swoole/RoadRunner/Octane giữ ứng dụng sống giữa
  các request → biến static/singleton bị chia sẻ, xuất hiện lỗi kiểu thread
- Java: thread chia sẻ heap, phải đồng bộ tường minh. Bean Spring là singleton mặc định →
  ⚠️ field có state trong service là race giữa các request
- Go: "Don't communicate by sharing memory; share memory by communicating." Channel khi chuyển
  quyền sở hữu dữ liệu/điều phối, mutex khi bảo vệ state nhỏ. Không phải lúc nào channel cũng
  tốt hơn mutex

## Senior trả lời khác gì

- **"Hai request cùng trừ tồn kho, sửa thế nào?"**
  - Mid: "Dùng `synchronized`" hoặc "dùng Redis lock."
  - Senior: "`synchronized` vô dụng khi có nhiều instance. Cách đầu tiên là atomic update có
    điều kiện và kiểm tra affected rows; logic phức tạp thì `FOR UPDATE` trong transaction
    ngắn; tranh chấp thấp thì optimistic. Đỉnh tải cực lớn thì Redis + queue, DB vẫn là chốt
    chặn cuối. Luôn có constraint."
- **"Thread pool nên bao nhiêu thread?"**
  - Mid: "Bằng số core" hoặc một con số cố định.
  - Senior: phân biệt CPU-bound và I/O-bound, dùng Little's law, nhìn tài nguyên phía sau
    (connection pool, rate limit của API), bounded queue, đo p99 và điều chỉnh bằng load test.
- **"Deadlock là gì?"**
  - Mid: định nghĩa và bốn điều kiện.
  - Senior: thêm ví dụ trong DB, cách đọc deadlock log (`SHOW ENGINE INNODB STATUS`), khoá theo
    thứ tự, transaction ngắn, và retry có giới hạn vì deadlock không loại bỏ hoàn toàn được.
- **"PHP có race condition không?"**
  - Mid: "Không, PHP không có thread."
  - Senior: "Không có data race trong bộ nhớ, nhưng race condition ở DB/Redis/file là đầy, vì
    nhiều process FPM chạy song song. Octane/Swoole còn đưa state dùng chung trở lại."

## Tình huống

1. *Hệ thống coupon: mỗi user chỉ được dùng một lần. Log cho thấy vài user dùng hai lần.*
   - Gợi ý: check-then-act giữa hai request song song (double click, hai tab).
   - Thêm `UNIQUE(user_id, coupon_id)` vào bảng `coupon_usages`, insert trước khi áp dụng,
     bắt lỗi unique violation. Dọn dữ liệu trùng trước khi thêm constraint.
2. *Chuyển tiền giữa hai tài khoản, thỉnh thoảng gặp lỗi deadlock 1213.*
   - Gợi ý: hai giao dịch A→B và B→A khoá theo thứ tự ngược nhau.
   - Khoá theo thứ tự id tăng dần, transaction ngắn, retry có giới hạn khi deadlock.
3. *Service Java thêm cache `HashMap` làm field của bean, thỉnh thoảng CPU 100% hoặc dữ liệu sai.*
   - Gợi ý: bean singleton dùng chung giữa các thread, `HashMap` không thread-safe.
   - Dùng `ConcurrentHashMap` (`computeIfAbsent`) hoặc thư viện cache (Caffeine).
4. *Go service xử lý file upload: mỗi dòng mở một goroutine gọi API, file 1 triệu dòng làm
   API bên kia trả 429 và service hết bộ nhớ.*
   - Gợi ý: không giới hạn concurrency. Worker pool hoặc `errgroup.SetLimit`, rate limiter,
     đọc file dạng stream, truyền `context` để hủy.
5. *Admin sửa sản phẩm, thay đổi của người khác bị mất.*
   - Gợi ý: lost update. Cột `version`, `UPDATE ... WHERE version = ?`, trả 409 và cho người
     dùng xem bản mới; hoặc chỉ update field thay đổi.
6. *API tạo thanh toán bị gọi hai lần do client retry sau timeout, khách bị trừ tiền hai lần.*
   - Gợi ý: idempotency key từ client, bảng lưu key với unique constraint, trạng thái
     `processing`, trả response cũ; truyền idempotency key sang cổng thanh toán.

## ❓ Câu hỏi hay gặp

🟢
- Concurrency và parallelism khác nhau thế nào?
- Race condition là gì? Cho ví dụ trong ứng dụng web.
- Mutex và semaphore khác nhau thế nào?
- Deadlock là gì? Cho một ví dụ trong database và cách tránh.

🟡
- Flash sale 100 sản phẩm, 10.000 người cùng mua. Làm sao không bán quá số lượng?
- Optimistic lock và pessimistic lock, khi nào dùng cái nào?
- Check-then-act là gì, sửa thế nào?
- Chọn kích thước thread pool thế nào? Little's law là gì?
- Vì sao `synchronized`/`sync.Mutex` không đủ khi chạy nhiều instance?
- Làm sao chống double submit?
- Goroutine khác thread OS thế nào? Virtual thread của Java khác gì?

🔴
- Data race và race condition khác nhau thế nào? Có cái này mà không có cái kia được không?
- Happens-before là gì? `volatile` trong Java đảm bảo gì và không đảm bảo gì?
- CAS là gì, vấn đề ABA là gì và sửa thế nào?
- Priority inversion là gì? Có tương đương ở mức hệ thống backend không?
- Event loop bị chặn thì chuyện gì xảy ra? So sánh với goroutine.

## Bài tập tự làm

1. Viết chương trình Go có data race trên một biến đếm, chạy với `-race`, rồi sửa bằng ba
   cách: `sync.Mutex`, `atomic.Int64`, và channel. So sánh độ dài và độ rõ ràng.
2. Với bảng `accounts(id, balance, version)`, viết SQL chuyển tiền an toàn bằng hai cách:
   pessimistic và optimistic. Chỉ ra kịch bản deadlock của cách pessimistic và cách tránh.
3. Tính kích thước thread pool và connection pool cho service: 300 request/giây, mỗi request
   gọi DB 2 lần mỗi lần 15 ms, và gọi một API ngoài 120 ms. Nêu giả định.
4. Thiết kế bảng và luồng xử lý idempotency key cho API `POST /payments`, xử lý đúng khi hai
   request cùng key đến cùng lúc.
5. Liệt kê mọi race condition có thể có trong luồng "đăng ký tài khoản bằng email + gửi mã
   xác thực + xác thực mã", và cách chặn từng cái.

> Nộp bài vào đây để được review.
