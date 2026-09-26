# 13. Concurrency

> [← Mục lục](README.md) · Trọng tâm: **race condition ở mức ứng dụng web** (PHP-FPM, MySQL, Redis, queue, nhiều instance), nền tảng primitive và memory model, đối chiếu Java (JDK 25 LTS) và Go.
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
| [OSTEP](https://pages.cs.wisc.edu/~remzi/OSTEP/) (Arpaci-Dusseau), phần *Concurrency* | Sách online miễn phí | Thread, lock, condition variable, semaphore, bug thường gặp. Ngắn, dễ đọc, có bài tập |
| *Java Concurrency in Practice* (Goetz và cộng sự, 2006) | Sách | Vẫn là sách chuẩn về thread safety, visibility, thread pool. Ví dụ bằng Java nhưng tư duy dùng cho mọi ngôn ngữ |
| [The Go Memory Model](https://go.dev/ref/mem) và [Effective Go: Concurrency](https://go.dev/doc/effective_go#concurrency) | Official docs | Goroutine, channel, happens-before trong Go |
| [JLS ch.17: Threads and Locks](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html) | Đặc tả | Mục 17.4 là Java Memory Model. Đọc sau khi đã hiểu happens-before ở mức ý tưởng |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.7 transactions: race condition ở tầng DB (lost update, write skew). Quan trọng nhất với backend |
| [Laravel docs](https://laravel.com/docs/cache#atomic-locks) | Official docs | Atomic lock, pessimistic locking, unique job, job middleware |
| [The Little Book of Semaphores](https://greenteapress.com/wp/semaphores/) (Downey) | Sách online miễn phí | Bài tập đồng bộ kinh điển, nếu muốn luyện tư duy primitive |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Gọi đúng tên race condition, dùng được mutex/semaphore, chặn được race trong request web | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.7 | Chọn đúng giữa atomic update, lock, optimistic, idempotency; sizing pool; hiểu mô hình chạy của PHP/Java/Go | 7–9 ngày |
| **3. Senior** 🔴 | 3.1–3.5 | Memory model, lock-free, thiết kế cho tranh chấp cực cao, kiểm thử và điều tra lỗi concurrency | 6–8 ngày |

Với backend PHP, module 1.4 và chặng 2 là phần bị hỏi nhiều nhất: race condition xảy ra giữa
**các request, process, instance**, không chỉ giữa các thread. Chặng 3 giúp trả lời câu vặn
khi người phỏng vấn có nền Java/Go.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Concurrency, race condition, critical section

**Vì sao cần học:** Các bug kiểu "thỉnh thoảng mới bị" như bán quá tồn kho, coupon dùng hai
lần, số đếm lượt xem bị thiếu đều là race condition. Người phỏng vấn hay mở đầu bằng
"concurrency khác parallelism thế nào", rồi hỏi tiếp "PHP có race condition không" để xem bạn
có hiểu race xảy ra cả giữa các process và các request, không chỉ giữa các thread.

**Học gì**

*Concurrency và parallelism*
- *Concurrency* là cách tổ chức chương trình để xử lý nhiều việc **đan xen** trong cùng một
  khoảng thời gian.
  - Chạy được trên một core: CPU chuyển qua lại giữa các việc, mỗi lúc chỉ làm một việc.
  - Ví dụ: một người nấu ăn vừa luộc rau vừa thái thịt, trong lúc chờ nước sôi thì quay sang thái.
- *Parallelism* là nhiều việc chạy **cùng một lúc thật sự**, nên cần nhiều core.
  - Ví dụ: hai người nấu, mỗi người một món, cùng lúc.
- Rob Pike tóm lại: concurrency là "dealing with" nhiều việc, parallelism là "doing" nhiều việc.

| Runtime | Concurrent | Parallel | Vì sao |
|---|---|---|---|
| Node.js | Có | Không | Chỉ một thread chạy JavaScript, các việc đan xen nhau quanh I/O |
| Go với `GOMAXPROCS > 1` | Có | Có | Nhiều goroutine, được xếp lên nhiều thread OS chạy trên nhiều core |
| PHP-FPM | Có | Có, giữa các request | Nhiều process chạy song song trên nhiều core, mỗi process xử lý một request tuần tự |

*Race condition và critical section*
- *Race condition* là khi kết quả đúng hay sai phụ thuộc vào **thứ tự** các luồng chạy, và có ít
  nhất một thứ tự cho ra kết quả sai.
  - Đây là lỗi **logic**. Nó xảy ra được cả khi mọi bước đều có khoá riêng (xem ví dụ ở nhóm sau).
- Ví dụ kinh điển là `count++`. Nó trông như một lệnh, nhưng thật ra là ba bước: đọc, cộng, ghi.
  Kiểu thao tác này gọi là *read-modify-write*. Hai thread cùng chạy:
  1. Thread A đọc `count = 5`.
  2. Thread B đọc `count = 5`.
  3. A cộng 1 và ghi `count = 6`.
  4. B cộng 1 và ghi `count = 6`.

  Tăng hai lần nhưng kết quả chỉ tăng một.
- *Critical section* là đoạn code truy cập dữ liệu dùng chung, chỉ được phép một luồng chạy tại
  một thời điểm. Bảo vệ nó bằng mutex (module 1.2).

*Data race khác race condition*
- *Data race* là khi hai thread truy cập **cùng một vùng nhớ**, ít nhất một bên ghi, và giữa chúng
  không có đồng bộ nào.
  - Đây là khái niệm của *memory model*, tức bộ quy tắc của ngôn ngữ về việc khi nào thread này
    chắc chắn thấy giá trị thread kia ghi (module 3.1).
- ⚠️ Hai khái niệm này độc lập, có cái này mà không có cái kia:
  - **Race condition không có data race.** Ví dụ check-then-act mà mỗi bước khoá riêng:

    ```java
    if (account.getBalance() >= 100) {   // bước 1: lock, đọc, unlock
        account.withdraw(100);           // bước 2: lock, trừ, unlock
    }
    // Hai thread cùng qua bước 1 với số dư 100, rồi cùng trừ: số dư âm.
    ```

    Thêm mutex quanh từng bước không sửa được, vì lỗi nằm ở khoảng hở **giữa** hai bước. Hai
    process PHP cũng vậy: chúng không chung vùng nhớ nên không thể có data race, nhưng vẫn có
    race condition trên DB.
  - **Data race không có race condition.** Ví dụ nhiều thread cùng ghi `lastSeenAt = now` mà
    không khoá, và về nghiệp vụ thì giá trị cuối là của ai cũng được. Về memory model đây vẫn là
    data race.
- Vì sao cần phân biệt: công cụ như `go test -race` chỉ bắt được data race. Race condition thì
  phải tự lập luận (module 3.5).

*Ba tính chất cần đảm bảo*
- *Atomicity*: một thao tác nhiều bước diễn ra như một bước, không ai chen vào giữa được.
- *Visibility*: giá trị một thread ghi thì thread khác nhìn thấy được.
- *Ordering*: các lệnh không bị sắp xếp lại theo cách làm thread khác thấy trạng thái vô lý.
- `count++` ở trên hỏng atomicity. Visibility và ordering khó thấy hơn, chi tiết ở module 3.1.

**Đọc**
- OSTEP: [Concurrency: An Introduction](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf)
- Go blog: [Concurrency is not parallelism](https://go.dev/blog/waza-talk) (video Rob Pike)

**Nắm chắc khi**
- [ ] Cho một ví dụ race condition không có data race, và giải thích vì sao thêm mutex quanh từng bước không sửa được
- [ ] Vẽ được timeline hai thread chạy `count++` dẫn tới mất một lần tăng
- [ ] Giải thích được vì sao PHP-FPM không có data race nhưng vẫn đầy race condition

#### 1.2 Primitive đồng bộ cơ bản

**Vì sao cần học:** Trong code PHP bạn ít khi dùng trực tiếp mutex hay semaphore, nhưng các ý
tưởng này xuất hiện lại ở tầng hệ thống: giới hạn số lời gọi API ngoài chính là semaphore, queue
có giới hạn chính là bounded buffer. Câu "mutex khác semaphore thế nào" hay gặp ở mức junior,
còn vòng Java/Go hay bắt viết producer–consumer.

**Học gì**

*Mutex*
- *Primitive đồng bộ* là các công cụ nền do ngôn ngữ hoặc hệ điều hành cung cấp để điều phối
  nhiều luồng. Mutex là cái cơ bản nhất.
- *Mutex* (mutual exclusion) là một cái khoá mà mỗi lúc chỉ một luồng giữ. Luồng khác muốn lấy
  thì phải chờ tới khi nó được nhả.
- Giữ khoá càng ngắn càng tốt.
  - ⚠️ Không gọi I/O (DB, HTTP, file) khi đang giữ khoá. API chậm 2 giây nghĩa là mọi luồng khác
    đứng chờ 2 giây.
- *Reentrant* nghĩa là thread đang giữ khoá lấy lại chính khoá đó được, không tự chặn mình.
  - Java `synchronized` và `ReentrantLock` là reentrant.
  - ⚠️ Go `sync.Mutex` **không** reentrant. Cùng một goroutine lock hai lần là tự deadlock.
- ⚠️ Go: copy một struct chứa `sync.Mutex` là copy luôn trạng thái khoá. Hai bản sao không còn
  bảo vệ nhau. `go vet` bắt được lỗi này.

*Read-write lock*
- *Read-write lock* (RW lock) cho phép **nhiều reader cùng lúc**, hoặc **đúng một writer**.
- Chỉ có lợi khi đọc nhiều hơn ghi rất nhiều **và** đoạn đọc đủ dài. Đoạn đọc ngắn thì chi phí
  quản lý RW lock còn lớn hơn mutex thường.
- ⚠️ *Writer starvation*: reader đến liên tục, lúc nào cũng có người đang đọc, nên writer chờ mãi.
- ⚠️ Nâng read lock lên write lock dễ deadlock:
  1. Reader A và reader B cùng giữ read lock.
  2. Cả hai cùng muốn nâng lên write lock.
  3. Write lock cần mọi reader nhả ra, mà mỗi bên lại đang chờ bên kia nhả. Không ai chạy tiếp.

*Semaphore*
- *Semaphore* giữ N "vé" (*permit*). Luồng lấy một vé thì được vào, trả vé khi xong. Hết vé thì
  luồng mới phải chờ.
- Dùng để giới hạn số luồng cùng dùng một tài nguyên, ví dụ tối đa 10 kết nối cùng lúc tới API ngoài.
- Khác mutex: mutex có "chủ sở hữu" (ai lock thì chính người đó unlock). Semaphore thì không,
  luồng này lấy vé, luồng khác trả được.
- Go có hai cách: buffered channel hoặc `x/sync/semaphore`. Java có `Semaphore`.

  ```go
  sem := make(chan struct{}, 10) // 10 vé
  sem <- struct{}{}              // lấy vé, chờ nếu đã có 10 người giữ
  defer func() { <-sem }()       // trả vé
  callAPI()
  ```

*Condition variable*
- *Condition variable* cho một luồng ngủ chờ tới khi một điều kiện đúng, ví dụ "buffer đã có phần
  tử". Luồng khác làm điều kiện thành đúng thì báo (*signal*) để đánh thức nó.
- Luôn đi kèm một mutex bảo vệ biến điều kiện.
- ⚠️ Luôn viết `while (!cond) wait()`, không viết `if (!cond) wait()`. Hai lý do:
  - *Spurious wakeup*: luồng có thể bị đánh thức dù không ai báo.
  - Giữa lúc được báo và lúc thật sự chạy lại, một thread khác có thể đã đổi điều kiện về sai.
- Go có `sync.Cond` nhưng ít dùng, thường thay bằng channel.

*Producer–consumer và bounded buffer*
- Mô hình *producer–consumer*: producer đẩy việc vào một buffer, consumer lấy ra xử lý.
- *Bounded buffer* là buffer có giới hạn kích thước. Đầy thì producer phải chờ.
  - Việc bên nhận chậm buộc bên gửi chậm lại theo gọi là *backpressure*.
- ⚠️ Queue không giới hạn: consumer chậm thì queue cứ phình tới khi hết RAM (OOM).
- Java có `BlockingQueue`, Go dùng buffered channel.

*Tóm tắt*

| Primitive | Mấy luồng vào cùng lúc | Dùng khi |
|---|---|---|
| Mutex | 1 | Bảo vệ một critical section |
| RW lock | Nhiều reader hoặc 1 writer | Đọc rất nhiều, ghi hiếm, đoạn đọc dài |
| Semaphore | N | Giới hạn số người dùng một tài nguyên |
| Condition variable | Không giới hạn gì, chỉ để chờ | Chờ một điều kiện trở thành đúng |

**Đọc**
- OSTEP: [Locks](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf), [Condition Variables](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-cv.pdf), [Semaphores](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf)
- Go: [x/sync/semaphore](https://pkg.go.dev/golang.org/x/sync/semaphore)
- *Java Concurrency in Practice*: ch.5 (building blocks) và ch.14 (condition queue)

**Nắm chắc khi**
- [ ] Viết được bounded buffer bằng mutex + condition variable, và chỉ ra bug nếu dùng `if` thay `while`
- [ ] Giới hạn được "tối đa 10 lời gọi API cùng lúc" trong Go bằng hai cách
- [ ] Nói được khi nào RW lock chậm hơn mutex thường

#### 1.3 Deadlock, livelock, starvation

**Vì sao cần học:** Lỗi MySQL `1213 Deadlock found` là lỗi production có thật với app Laravel,
thường do hai request cập nhật các dòng theo thứ tự khác nhau. Câu "deadlock là gì, cho ví dụ
trong DB, tránh thế nào" gần như luôn có ở mức junior, và người phỏng vấn muốn nghe bạn nói
"app phải retry".

**Học gì**

*Deadlock là gì*
- *Deadlock* là khi hai hay nhiều luồng chờ nhau theo vòng tròn, nên không ai chạy tiếp được.
- Ví dụ kinh điển trong DB, chuyển tiền hai chiều cùng lúc:
  1. T1 (chuyển A→B) chạy `UPDATE accounts ... WHERE id = 1`, giữ khoá dòng 1.
  2. T2 (chuyển B→A) chạy `UPDATE accounts ... WHERE id = 2`, giữ khoá dòng 2.
  3. T1 muốn update dòng 2, phải chờ T2.
  4. T2 muốn update dòng 1, phải chờ T1. Vòng chờ khép kín.

*Bốn điều kiện Coffman*
- Deadlock chỉ xảy ra khi có **đủ cả bốn** điều kiện dưới đây. Phá được một điều kiện là tránh được.

| Điều kiện | Nghĩa | Cách phá thực tế |
|---|---|---|
| Mutual exclusion | Tài nguyên mỗi lúc chỉ một bên giữ | Thường không phá được, vì đó chính là mục đích của khoá |
| Hold and wait | Giữ khoá này trong lúc chờ khoá khác | Lấy hết mọi khoá một lần, hoặc không lấy gì |
| No preemption | Không ai giật được khoá bên kia đang giữ | Timeout khi lấy khoá (`tryLock`, `innodb_lock_wait_timeout`): chờ quá lâu thì tự bỏ cuộc và nhả khoá của mình |
| Circular wait | Các bên chờ nhau thành vòng | **Khoá theo thứ tự cố định**, ví dụ luôn khoá id nhỏ trước |

- Thêm một quy tắc: không gọi code lạ (callback, hook, event listener) khi đang giữ khoá. Code đó
  có thể lấy thêm khoá khác và tạo ra vòng chờ mà bạn không nhìn thấy.

*Phát hiện deadlock*
- *Wait-for graph* là đồ thị "ai đang chờ ai". Đồ thị có chu trình nghĩa là có deadlock.
- InnoDB và Postgres tự dựng đồ thị này, phát hiện deadlock và rollback một bên.
  - MySQL trả lỗi 1213 cho bên bị rollback.
  - Mục `LATEST DETECTED DEADLOCK` trong `SHOW ENGINE INNODB STATUS` cho biết hai transaction giữ
    gì và chờ gì.
- Java: `jstack` in *thread dump* (trạng thái mọi thread), có mục báo deadlock.
- Go: runtime chỉ báo `all goroutines are asleep - deadlock!` khi **mọi** goroutine đều kẹt.
  - ⚠️ Nếu vẫn còn goroutine khác đang chạy, ví dụ HTTP server, thì một nhóm goroutine kẹt nhau
    sẽ không được báo gì cả.

*Deadlock trong DB và cách sửa*
- Ba việc cần làm:
  - Sắp id trước khi khoá, để mọi transaction khoá theo cùng một thứ tự.
  - Giữ transaction ngắn.
  - **Retry**, vì deadlock không loại bỏ hoàn toàn được.

  ```sql
  -- Chuyển tiền: luôn khoá id nhỏ trước, bất kể chiều chuyển
  START TRANSACTION;
  SELECT id FROM accounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE;
  UPDATE accounts SET balance = balance - 100 WHERE id = 2;
  UPDATE accounts SET balance = balance + 100 WHERE id = 1;
  COMMIT;
  ```
- Laravel: `DB::transaction($fn, $attempts)` tự chạy lại closure khi gặp deadlock.

*Deadlock với channel trong Go*
- *Unbuffered channel* là channel không có chỗ chứa: gửi vào thì phải chờ tới khi có người nhận.
- ⚠️ Gửi vào unbuffered channel mà không ai nhận thì goroutine gửi kẹt mãi. Đây là nguồn phổ biến
  của deadlock và *goroutine leak* (goroutine không bao giờ kết thúc, giữ bộ nhớ mãi).

*Livelock và starvation*
- *Livelock*: các bên vẫn đang chạy, nhưng cứ nhường nhau mãi nên không ai tiến được.
  - Ví dụ: hai người gặp nhau ở hành lang, cùng né sang một bên, rồi lại cùng né sang bên kia.
  - Sửa bằng backoff ngẫu nhiên: mỗi bên chờ một khoảng ngẫu nhiên trước khi thử lại.
- *Starvation*: một luồng mãi không tới lượt được chạy hay được lấy khoá.
  - *Fair lock* như `new ReentrantLock(true)` cấp khoá theo thứ tự đến, nên giảm starvation.
  - Đổi lại throughput thấp hơn.

**Đọc**
- OSTEP: [Common Concurrency Problems](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf)
- MySQL: [Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html); module 2.6 và 3.2 của [03-database-sql.md](03-database-sql.md)
- Laravel: [Handling Deadlocks](https://laravel.com/docs/database#handling-deadlocks) (`DB::transaction($fn, $attempts)`)

**Nắm chắc khi**
- [ ] Viết được SQL chuyển tiền A→B và B→A gây deadlock, rồi sửa bằng khoá theo thứ tự
- [ ] Chỉ ra được điều kiện Coffman nào bị phá bởi từng cách phòng tránh
- [ ] Đọc được mục `LATEST DETECTED DEADLOCK` và nói hai transaction giữ gì, chờ gì

#### 1.4 Race condition trong ứng dụng web

**Vì sao cần học:** Đây là phần quan trọng nhất với backend PHP. Bài "hai request cùng trừ tồn
kho", "coupon bị dùng hai lần", "đăng ký trùng email" gần như chắc chắn gặp. Người phỏng vấn muốn
nghe ít nhất 4 cách sửa kèm nhược điểm của từng cách, và muốn thấy bạn biết đặt chốt chặn cuối ở DB.

**Học gì**

*Code sai kinh điển*
- Đoạn Laravel này trông đúng, nhưng sai khi có hai request cùng lúc:

  ```php
  $product = Product::find($id);
  if ($product->stock > 0) {        // check
      $product->stock -= 1;         // act
      $product->save();
  }
  ```
- Kịch bản khi tồn kho còn 1:
  1. Request A đọc `stock = 1`.
  2. Request B đọc `stock = 1`.
  3. Cả hai cùng thấy `> 0`.
  4. Cả hai cùng ghi `stock = 0` và cùng tạo đơn. Bán 2 món khi chỉ có 1.

*Check-then-act*
- *Check-then-act* ⚠️ là mẫu "kiểm tra điều kiện rồi mới hành động" viết thành hai bước riêng.
  Request khác chen được vào khoảng giữa hai bước.
- Mẫu này có ở khắp nơi:
  - "Email chưa có thì tạo user."
  - "Chưa dùng coupon thì cho dùng."
  - "Đủ số dư thì trừ."
  - "Slot còn trống thì đặt."
- Cách sửa: gộp check và act thành **một thao tác atomic**, tức một bước mà DB hoặc Redis đảm bảo
  không ai chen vào giữa được. Ví dụ:
  - `UPDATE ... WHERE` có điều kiện.
  - Unique constraint.
  - `INSERT ... ON DUPLICATE KEY UPDATE`.
  - Redis `SET key value NX` (chỉ set nếu chưa có).

*Các cách trừ tồn kho*
- Vài thuật ngữ trước khi so sánh:
  - *Affected rows*: số dòng mà câu `UPDATE` thực sự thay đổi. Bằng 0 nghĩa là điều kiện không
    thoả, tức hết hàng.
  - *Pessimistic lock*: khoá dòng ngay khi đọc (`SELECT ... FOR UPDATE`), người khác phải chờ.
  - *Optimistic lock*: không khoá gì, lúc ghi mới kiểm tra xem dữ liệu đã bị ai đổi chưa, bằng một
    cột `version` (module 2.1).
  - *Distributed lock*: khoá đặt ở một hệ thống ngoài như Redis, mà mọi server đều nhìn thấy.
  - Redis `DECR` giảm một số nguyên trong Redis một cách atomic. *Lua script* cho Redis chạy nhiều
    lệnh như một bước duy nhất.
- Phải nêu được ít nhất 4 cách và nhược điểm:

  | Cách | Ưu | Nhược / cạm bẫy |
  |---|---|---|
  | Atomic update `SET stock = stock - 1 WHERE id = ? AND stock > 0` | Đơn giản, nhanh, đúng | Chỉ gói được logic đơn giản. ⚠️ Phải kiểm tra affected rows |
  | Pessimistic `SELECT ... FOR UPDATE` | Làm được logic nhiều bước | Giảm throughput, dễ deadlock. ⚠️ Phải nằm trong transaction, không gọi API ngoài khi giữ khoá |
  | Optimistic (cột `version`) | Không giữ khoá | Tranh chấp cao thì retry liên tục |
  | Distributed lock (Redis) | Điều phối được cả tài nguyên nằm ngoài DB | Thêm một hệ thống, lock có thể hết hạn giữa chừng ([14](14-distributed-systems.md)) |
  | Queue xử lý tuần tự theo `product_id` | Không có tranh chấp, chịu được đỉnh tải | Bất đồng bộ, phức tạp hơn |
  | 🟡 Redis `DECR`/Lua rồi ghi DB sau | Rất nhanh, hợp flash sale | Redis và DB có thể lệch nhau, cần đối soát |

*Unique constraint làm lưới an toàn*
- Dù đã có lock hay queue, vẫn đặt ràng buộc ở DB, ví dụ `UNIQUE(user_id, coupon_id)`. Lý do:
  - Lock có thể hết hạn giữa chừng.
  - Script migrate, lệnh artisan hay `tinker` ghi thẳng vào DB, không đi qua lock của app.
  - DB là nơi duy nhất nhìn thấy **mọi** lần ghi.
- Bắt lỗi unique violation và biến nó thành kết quả nghiệp vụ, đừng để thành lỗi 500:

  ```php
  try {
      CouponUsage::create(['user_id' => $userId, 'coupon_id' => $couponId]);
  } catch (UniqueConstraintViolationException $e) {
      return response()->json(['message' => 'Coupon đã được dùng'], 409);
  }
  ```

*Lock trong bộ nhớ không đủ*
- ⚠️ Lock trong bộ nhớ (`synchronized` của Java, `sync.Mutex` của Go, biến static) chỉ có tác
  dụng trong **một process**.
  - Scale lên 3 pod là mỗi pod có một khoá riêng, và khoá trở nên vô dụng.
  - PHP-FPM còn không có khoá kiểu này, vì mỗi request đã là một process riêng.

**Đọc**
- DDIA ch.7: *Preventing Lost Updates* và *Write Skew and Phantoms*
- Laravel: [Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking)
- Module 2.6 của [03-database-sql.md](03-database-sql.md)

**Nắm chắc khi**
- [ ] Viết được luồng trừ tồn kho theo 4 cách và nói khi nào dùng cách nào
- [ ] Sửa được luồng "đăng ký bằng email" để hai request song song không tạo hai user
- [ ] Giải thích được vì sao "đã bọc trong transaction" vẫn bán quá tồn kho

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Atomic, CAS và optimistic lock

**Vì sao cần học:** CAS là một ý tưởng duy nhất nằm sau ba thứ bạn gặp hằng ngày: biến atomic
trong Java/Go, optimistic lock trong DB (cột `version`), và `ETag` ở tầng API. Hiểu một lần là
dùng được cả ba. Câu hay gặp: "optimistic lock và pessimistic lock, khi nào dùng cái nào".

**Học gì**

*CAS*
- *Atomic operation* là thao tác được phần cứng hoặc runtime đảm bảo làm trọn trong một bước,
  không ai chen vào giữa được.
- *CAS* (compare-and-swap) là một atomic operation dạng `CAS(địa chỉ, expected, new)`:
  - Nếu giá trị hiện tại bằng `expected` thì ghi `new` và báo thành công.
  - Nếu khác (tức ai đó vừa đổi) thì không ghi gì và báo thất bại.
- CAS thường nằm trong một vòng lặp retry:
  1. Đọc giá trị hiện tại `old`.
  2. Tính giá trị mới từ `old`.
  3. CAS với `expected = old`.
  4. Thất bại nghĩa là có người vừa đổi giá trị. Quay lại bước 1.

  ```go
  for {
      old := counter.Load()
      if counter.CompareAndSwap(old, old+1) {
          break
      }
  }
  ```
- CAS là nền tảng của các cấu trúc lock-free (module 3.2).

*Biến atomic trong Java và Go*
- Java: `AtomicInteger`, `AtomicReference`, và `LongAdder` cho bộ đếm bị tranh chấp cao (module 3.2).
- Go: package `sync/atomic`, có các kiểu typed như `atomic.Int64` từ Go 1.19, và hàm `CompareAndSwap`.
- ⚠️ Atomic trên từng biến **không** làm nhiều biến atomic cùng nhau.
  - Ví dụ: `balance` và `version` đều là atomic, nhưng cập nhật cả hai thì vẫn có khoảnh khắc thread
    khác thấy `balance` mới đi với `version` cũ.

*Optimistic lock là CAS ở mức dữ liệu*
- Cột `version` đóng vai `expected`:

  ```sql
  UPDATE products SET price = ?, version = version + 1
  WHERE id = ? AND version = ?;   -- version lúc đọc
  ```
- Affected rows bằng 0 nghĩa là ai đó đã sửa trước. Báo xung đột cho người dùng hoặc đọc lại rồi retry.
- Ở tầng HTTP, cặp `ETag` + `If-Match` là cùng ý tưởng ([09-api-design.md](09-api-design.md)):
  - Server trả `ETag`, một mã đại diện cho phiên bản hiện tại của tài nguyên.
  - Client gửi lại mã đó trong header `If-Match` khi sửa.
  - Mã không khớp nghĩa là tài nguyên đã đổi, server từ chối.

*Chọn optimistic hay pessimistic*

| | Optimistic | Pessimistic (`FOR UPDATE`) |
|---|---|---|
| Hợp khi tranh chấp | Thấp | Cao |
| Hợp khi thao tác | Kéo dài, ví dụ người dùng mở form sửa vài phút | Ngắn, ví dụ trừ tồn kho |
| Khi có xung đột | Một bên thất bại, phải retry hoặc báo người dùng | Bên sau chờ bên trước xong |
| Chi phí | Không giữ khoá | Giữ khoá, giảm throughput, có thể deadlock |

- ⚠️ Người dùng suy nghĩ vài phút trên form thì không thể giữ `FOR UPDATE` suốt thời gian đó,
  nên phải dùng optimistic.

**Đọc**
- Go: [sync/atomic](https://pkg.go.dev/sync/atomic)
- *Java Concurrency in Practice*: ch.15 (atomic variables và nonblocking synchronization)

**Nắm chắc khi**
- [ ] Viết được vòng lặp CAS tăng một bộ đếm và giải thích vì sao phải lặp
- [ ] Thiết kế được luồng sửa sản phẩm của admin có optimistic lock, trả 409 cho UI

#### 2.2 Lost update và isolation level

**Vì sao cần học:** Lost update là bug âm thầm: không có lỗi, không có log, chỉ là dữ liệu của
một người biến mất. Câu vặn nổi tiếng ở vòng mid/senior là "MySQL và Postgres cùng ở REPEATABLE
READ, hai transaction đọc-sửa-ghi cùng một dòng thì sao". Trả lời sai câu này là mất điểm nặng.

**Học gì**

*Lost update*
- *Lost update* là khi hai request cùng đọc một bản ghi, mỗi bên sửa rồi ghi lại, và bên ghi sau
  đè mất thay đổi của bên ghi trước.
- Ví dụ ở trang admin:
  1. Admin A mở form sản phẩm, đổi giá.
  2. Admin B mở cùng form lúc đó, đổi mô tả.
  3. A bấm lưu: giá mới được ghi.
  4. B bấm lưu cả form, gồm cả giá cũ mà B đã đọc lúc đầu. Giá của A mất.
- Bốn cách sửa:
  - Chỉ update những field thực sự thay đổi.
  - Update atomic kiểu cộng dồn: `SET stock = stock - 1`, không tính ở app rồi ghi số cố định.
  - Optimistic lock (module 2.1).
  - `SELECT ... FOR UPDATE`.

*Nhắc lại isolation level*
- *Isolation level* là mức mà DB che các transaction chạy đồng thời khỏi nhau. Hai mức hay gặp:
  - *Read Committed* (RC): mỗi câu `SELECT` thấy dữ liệu đã commit tại thời điểm câu đó chạy.
    Mặc định của Postgres.
  - *Repeatable Read* (RR): cả transaction thấy cùng một *snapshot* (ảnh chụp dữ liệu). Mặc định
    của MySQL InnoDB.
- InnoDB có hai kiểu đọc:
  - `SELECT` thường đọc từ snapshot, không khoá.
  - *Locking read* (`SELECT ... FOR UPDATE`, `UPDATE`, `DELETE`) đọc **bản mới nhất đã commit**
    và khoá dòng.
- Chi tiết đầy đủ ở module 2.5 của [03-database-sql.md](03-database-sql.md).

*Cùng REPEATABLE READ, hai DB khác nhau*

| | Postgres RR | InnoDB RR |
|---|---|---|
| Transaction 2 update một dòng mà transaction 1 đã sửa và commit | Báo lỗi `could not serialize access due to concurrent update` (SQLSTATE `40001`) | Không báo lỗi |
| Kết quả | Transaction 2 bị huỷ, không mất dữ liệu | Nếu app tính giá trị mới từ snapshot cũ, thay đổi của bên kia **mất âm thầm** |
| App phải làm gì | Bắt lỗi `40001` và retry | Tự chống bằng atomic update, `FOR UPDATE` hoặc optimistic lock |

- Kịch bản mất dữ liệu ở InnoDB RR:
  1. T1 và T2 cùng `SELECT stock` thường, cùng thấy `5` từ snapshot.
  2. T1 ghi `stock = 4` và commit.
  3. T2 cũng tính ra 4 từ snapshot, ghi `stock = 4` và commit. Một lần trừ bị mất.
- Vì sao `UPDATE t SET stock = stock - 1` lại an toàn ở InnoDB RR: `UPDATE` là locking read, nên
  nó đọc bản mới nhất (4) chứ không đọc snapshot (5), và khoá dòng trong lúc trừ.
- ⚠️ READ COMMITTED, mặc định của Postgres, không chặn lost update kiểu "app đọc, tự tính, rồi ghi".

*Write skew*
- *Write skew* là khi hai transaction đọc cùng một tập dữ liệu, mỗi bên sửa một dòng **khác nhau**,
  và gộp lại thì vi phạm ràng buộc.
- Ví dụ "hai bác sĩ cùng xin nghỉ trực", ràng buộc là luôn có ít nhất một người trực:
  1. Bác sĩ A và B đang cùng trực.
  2. A đếm số người trực: 2. B cũng đếm: 2.
  3. A thấy "còn người khác", xin nghỉ: sửa dòng của A.
  4. B cũng thấy "còn người khác", xin nghỉ: sửa dòng của B. Không còn ai trực.
- RR không chặn được write skew, vì hai bên không sửa cùng một dòng.

**Đọc**
- Module 2.5 của [03-database-sql.md](03-database-sql.md) (isolation và anomaly, bảng so sánh MySQL/Postgres)
- Postgres: [Repeatable Read Isolation Level](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ)
- [Hermitage](https://github.com/ept/hermitage): kịch bản tái hiện lost update ở từng DB

**Nắm chắc khi**
- [ ] Tái hiện được bằng hai terminal: lost update ở MySQL RR (không lỗi) và lỗi `40001` ở Postgres RR
- [ ] Giải thích được vì sao `UPDATE t SET stock = stock - 1` an toàn ở InnoDB RR còn "đọc rồi ghi `stock = 4`" thì không

#### 2.3 Double submit, idempotency key

**Vì sao cần học:** "Khách bị trừ tiền hai lần" là sự cố nghiêm trọng nhất của mọi hệ thống thanh
toán, và nguyên nhân thường là cùng một request được gửi hai lần. Câu "chống double submit thế
nào" hay gặp ở mức mid. Câu trả lời "disable nút bấm" bị coi là red flag.

**Học gì**

*Vì sao request bị gửi trùng*
- Người dùng bấm nút hai lần, hoặc mở hai tab.
- Client retry sau khi bị timeout, trong khi request đầu thật ra vẫn đang được xử lý.
- Load balancer tự retry.
- ⚠️ Disable nút ở frontend chỉ giảm số lần trùng, không chặn được. Ba nguồn sau nằm ngoài tầm của nút bấm.

*Idempotency key*
- Một thao tác là *idempotent* nếu gọi nó nhiều lần cho kết quả giống hệt gọi một lần.
- *Idempotency key* là một chuỗi ngẫu nhiên do **client** sinh cho mỗi thao tác, gửi trong header
  `Idempotency-Key`. Client retry thì gửi lại đúng key đó.
- Server lưu một bảng, có unique constraint trên key:

  ```sql
  CREATE TABLE idempotency_keys (
    idem_key     VARCHAR(64) PRIMARY KEY,
    request_hash CHAR(64)    NOT NULL,   -- hash của body để phát hiện cùng key khác nội dung
    status       VARCHAR(16) NOT NULL,   -- processing | done
    response     JSON        NULL,
    created_at   DATETIME    NOT NULL
  );
  ```
- Luồng xử lý:
  1. Nhận request, `INSERT` một dòng với `status = 'processing'`. Unique constraint đảm bảo chỉ một
     request insert được.
  2. Insert thành công: xử lý nghiệp vụ, lưu response, đổi `status = 'done'`.
  3. Insert bị trùng key và `status = 'done'`: trả lại response đã lưu, không xử lý lại.
  4. Insert bị trùng key và `status = 'processing'`: request đầu vẫn đang chạy (xem cạm bẫy dưới).

*Hai cạm bẫy*
- ⚠️ Hai request cùng key đến **cùng lúc**. Nếu code là "SELECT xem key có chưa, chưa có thì xử
  lý" thì đó lại là check-then-act. Bản ghi key phải được tạo atomic **trước** khi xử lý (bước 1
  ở trên). Request thứ hai thấy `processing` thì trả 409 hoặc chờ.
- ⚠️ Cùng key nhưng body khác: so `request_hash`, khác thì trả lỗi. Không trả response cũ, vì đó
  là response của một request khác.

*Mở rộng*
- Truyền idempotency key tiếp sang cổng thanh toán (PSP) để chính PSP cũng không trừ tiền hai lần.
- Lưu key có thời hạn (TTL), ví dụ 24 giờ, rồi xoá.

*Queue worker cũng cần idempotency*
- Queue thường chỉ đảm bảo *at-least-once*: mỗi message được giao ít nhất một lần, có thể nhiều hơn.
- ⚠️ Cùng một message có thể bị hai worker xử lý **song song**, không chỉ lần lượt:
  - *Visibility timeout*: worker giữ message quá lâu, queue tưởng worker đã chết và giao message
    cho worker khác trong khi worker đầu vẫn chạy.
  - *Rebalance*: consumer group chia lại partition giữa các worker.
- Vì vậy xử lý idempotent phải chịu được hai lần chạy **đồng thời**, không chỉ hai lần chạy nối tiếp.

**Đọc**
- [Brandur: Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys)
- Stripe: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- [09-api-design.md](09-api-design.md), [12-messaging.md](12-messaging.md)

**Nắm chắc khi**
- [ ] Thiết kế được bảng idempotency và luồng xử lý đúng khi hai request cùng key đến cùng lúc (bài tập 4)
- [ ] Nói được bản ghi idempotency phải tạo trong cùng transaction với việc gì, và khi nào thì không thể

#### 2.4 Thread pool, connection pool, Little's law

**Vì sao cần học:** Đặt `pm.max_children` bao nhiêu, pool DB bao nhiêu connection là việc bạn
làm thật khi vận hành PHP-FPM và Laravel. Làm sai theo hướng "cứ tăng lên" thường làm hệ thống
chậm hơn. Người phỏng vấn muốn thấy bạn tính bằng công thức và nêu giả định, không đưa ra một
con số cố định.

**Học gì**

*Vì sao cần pool*
- *Pool* là một nhóm tài nguyên (thread, connection) được tạo sẵn với số lượng giới hạn, dùng xong
  thì trả lại để dùng tiếp.
- Tạo thread OS tốn kém: mỗi thread cần bộ nhớ cho stack và một lời gọi hệ thống.
- Không giới hạn số thread thì:
  - Hết bộ nhớ.
  - CPU mất nhiều thời gian cho *context switch* (chuyển qua lại giữa các thread) hơn là làm việc thật.
- Ý chính: pool **giới hạn mức song song**.

*Chọn kích thước pool*
- Việc *CPU-bound* (chủ yếu tính toán): khoảng bằng số core. Thêm thread cũng không có thêm core.
- Việc *I/O-bound* (chủ yếu chờ DB, mạng): dùng công thức trong JCIP:

  `số thread ≈ số core × (1 + thời gian chờ / thời gian tính)`

  - Ví dụ: 8 core, mỗi việc chờ DB 90 ms và tính 10 ms: `8 × (1 + 90/10) = 80` thread.

*Little's law*
- `L = λ × W`:
  - `L`: số request đang được xử lý đồng thời, tính trung bình.
  - `λ`: số request đến mỗi giây.
  - `W`: thời gian xử lý mỗi request.
- Ví dụ: 200 request/giây × 50 ms = 10 request đồng thời. Service cần ít nhất 10 thread, hoặc 10
  worker PHP-FPM, hoặc 10 connection nếu request nào cũng giữ connection suốt thời gian xử lý.
- Dùng được cho cả connection pool lẫn số worker PHP-FPM ([16-system-design.md](16-system-design.md)).

*Nhìn cả chuỗi*
- ⚠️ Pool to hơn tài nguyên phía sau là vô ích.
  - Ví dụ: 200 thread cùng gọi DB, nhưng pool DB chỉ có 20 connection. 180 thread ngồi chờ, chỉ tốn
    bộ nhớ.
  - Với PHP-FPM: tăng `pm.max_children` mà DB không chịu thêm được thì chỉ thêm tranh chấp ở DB,
    và mọi request cùng chậm đi.
- Luôn nhìn **cả chuỗi**: worker → connection pool → DB → API ngoài. Chỗ hẹp nhất quyết định.

*Queue chờ và chính sách từ chối*
- Pool đầy thì việc mới vào một queue chờ.
- ⚠️ *Unbounded queue* (queue không giới hạn) che giấu quá tải. Queue dài ra mãi, latency tăng vô
  hạn, mà không có lỗi nào báo ra.
- Nên dùng queue có giới hạn kèm chính sách khi đầy:
  - *Reject*: từ chối ngay, báo lỗi cho bên gọi.
  - *Caller-runs*: chính thread gọi phải tự chạy việc đó, nên tự nó bị chậm lại (một dạng backpressure).

*Pool dùng chung và bulkhead*
- ⚠️ Việc chặn lâu trong pool dùng chung làm nghẽn cả ứng dụng.
  - Ví dụ Java: `ForkJoinPool.commonPool` là pool mặc định cho parallel stream và
    `CompletableFuture` async. Làm I/O chậm trong đó thì mọi nơi khác dùng pool này đứng chờ theo.
- *Bulkhead* (vách ngăn tàu thuỷ): mỗi dependency một pool riêng, để một dependency hỏng không kéo
  chìm tất cả. Chi tiết ở module 3.3.

**Đọc**
- *Java Concurrency in Practice*: ch.8 (*Sizing Thread Pools*)
- [HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing): vì sao pool nhỏ thường nhanh hơn
- [Little's law](https://en.wikipedia.org/wiki/Little%27s_law)

**Nắm chắc khi**
- [ ] Tính được kích thước thread pool và connection pool cho một service cụ thể và nêu giả định (bài tập 3)
- [ ] Giải thích được vì sao tăng `pm.max_children` có thể làm hệ thống **chậm hơn**

#### 2.5 Pattern concurrency trong Go (và đối chiếu Java)

**Vì sao cần học:** Nếu bạn phỏng vấn vị trí Go, hoặc viết service phụ bằng Go cạnh hệ PHP, thì
worker pool và `errgroup` là thứ dùng hằng ngày. Goroutine rẻ nên rất dễ tạo quá nhiều và làm sập
dependency. Câu hay gặp: "viết worker pool có giới hạn và huỷ được".

**Học gì**

*Worker pool*
- *Worker pool*: N goroutine cùng đọc việc từ một channel. Hết việc thì `close(jobs)`, và vòng
  `for range` của mỗi worker tự thoát.
- Go 1.25 có `sync.WaitGroup.Go(f)`. Nó gộp ba việc `Add(1)`, `go`, `defer Done()` thành một.
  - Tránh được lỗi quên `Add`, hoặc gọi `Add` **bên trong** goroutine (lúc đó `Wait` có thể chạy
    trước khi `Add` kịp chạy).
  - `go vet` từ 1.25 có analyzer `waitgroup` bắt lỗi này.

  ```go
  var wg sync.WaitGroup
  for i := 0; i < 8; i++ {
      wg.Go(func() {
          for j := range jobs { // thoát khi jobs bị close
              process(j)
          }
      })
  }
  wg.Wait()
  ```

*Giới hạn concurrency*
- ⚠️ Goroutine rẻ, nhưng tài nguyên phía sau không rẻ. Chạy `go` cho mỗi dòng trong 10 triệu dòng,
  mỗi goroutine gọi DB, là sập DB.
- Giới hạn bằng worker pool, hoặc `errgroup.SetLimit(n)`.

*Fan-out/fan-in và pipeline*
- *Fan-out/fan-in*: chia việc cho nhiều worker (fan-out) rồi gom kết quả về một chỗ (fan-in).
  - Dùng `errgroup` kèm `context`: một worker lỗi thì `context` bị huỷ, các worker khác thấy và
    dừng sớm. `Wait()` trả về lỗi đầu tiên.
- *Pipeline*: chuỗi các stage nối nhau bằng channel, stage này đọc đầu ra của stage trước.
  - Throughput của cả pipeline bằng throughput của stage chậm nhất.
  - ⚠️ Phải truyền tín hiệu huỷ qua mọi stage. Nếu consumer cuối thoát sớm mà stage trước không
    biết, stage trước kẹt mãi ở lệnh gửi vào channel, gây goroutine leak.

*Bẫy thường gặp*
- Biến vòng lặp: trước Go 1.22, closure trong vòng `for` dùng chung **một** biến cho mọi vòng lặp,
  nên các goroutine hay đọc phải giá trị cuối. Từ 1.22, mỗi vòng lặp có một biến riêng.
- ⚠️ Hai goroutine cùng ghi vào một `map` thường thì runtime báo `concurrent map writes` và
  **crash cả process**.
  - Sửa bằng mutex, hoặc `sync.Map`. `sync.Map` chỉ hợp với vài pattern cụ thể (key ghi một lần
    đọc nhiều lần, hoặc các goroutine dùng các key tách biệt), không phải thay thế chung cho map.

*Channel hay mutex*
- Dùng channel khi **chuyển quyền sở hữu** dữ liệu hoặc điều phối các bước.
- Dùng mutex khi bảo vệ một mẩu state nhỏ, ví dụ một bộ đếm hay một cache.
- Channel không phải lúc nào cũng tốt hơn.

*Đối chiếu Java*
- `ExecutorService` là thread pool. `CompletableFuture` để nối và gộp các việc bất đồng bộ.
- `ConcurrentHashMap.computeIfAbsent` là cách an toàn cho "chưa có thì tính và lưu".
- *Structured concurrency* (gom các việc con thành một khối, khối kết thúc khi mọi việc con xong
  hoặc bị huỷ, tương tự `errgroup`) vẫn đang ở dạng preview.

**Đọc**
- Go blog: [Pipelines and cancellation](https://go.dev/blog/pipelines), [Share Memory By Communicating](https://go.dev/blog/codelab-share), [Fixing For Loops in Go 1.22](https://go.dev/blog/loopvar-preview)
- Go: [errgroup](https://pkg.go.dev/golang.org/x/sync/errgroup), [WaitGroup.Go](https://pkg.go.dev/sync#WaitGroup.Go), [Go 1.25 release notes](https://go.dev/doc/go1.25)

**Nắm chắc khi**
- [ ] Viết được worker pool có giới hạn, huỷ bằng `context`, trả lỗi đầu tiên bằng `errgroup`
- [ ] Chỉ ra được goroutine leak trong một pipeline khi consumer thoát sớm, và sửa được

#### 2.6 Mô hình chạy: process, thread, event loop, goroutine, virtual thread

**Vì sao cần học:** Mô hình chạy quyết định một request chậm ảnh hưởng tới các request khác thế
nào, và quyết định bạn tính RAM, số worker ra sao. Câu "PHP-FPM, Node.js, Go khác nhau thế nào khi
xử lý nhiều request" và "event loop bị chặn thì sao" hay gặp. Ứng viên có nền Java còn hay bị hỏi
về virtual thread.

**Học gì**

*Các khái niệm cần biết trước*
- *Blocking I/O*: gọi I/O (đọc DB, gọi HTTP) thì luồng đang chạy dừng lại chờ tới khi có kết quả.
- *Event loop*: một thread duy nhất chạy vòng lặp "lấy sự kiện đã sẵn sàng, chạy callback của nó".
  I/O được đăng ký rồi để đó, không chờ. Có kết quả thì callback được gọi.
- *M:N scheduling*: runtime xếp M luồng nhẹ (goroutine, virtual thread) lên N thread OS, với M lớn
  hơn N rất nhiều.
- *Park*: runtime cất một luồng nhẹ đang chờ I/O sang một bên, và cho luồng nhẹ khác chạy trên thread
  OS đó.
- *Function coloring*: trong mô hình async/await, hàm async chỉ gọi được bằng `await` từ một hàm
  async khác. Code bị chia thành hai "màu" không trộn lẫn tự do được.

*So sánh năm mô hình*

  | Mô hình | Cách chạy | Chặn I/O | Ghi chú |
  |---|---|---|---|
  | PHP-FPM | Mỗi request một process | Process đứng chờ | Share-nothing (các request không chia sẻ biến nào). Số request đồng thời bằng số worker |
  | Thread OS (Java cổ điển) | Mỗi request một thread | OS lập lịch thread khác | Tốn bộ nhớ, giới hạn khoảng vài nghìn |
  | Event loop + async/await (Node.js, ReactPHP, Swoole coroutine) | Một thread, callback hoặc coroutine | Không được chặn, phải `await` | ⚠️ Một việc CPU nặng chặn cả loop. Bị function coloring |
  | Goroutine (Go) | M:N, runtime lập lịch | Runtime park goroutine | Viết code đồng bộ bình thường, chạy được hàng trăm nghìn goroutine |
  | Virtual thread (Java 21+) | M:N trên *carrier thread* (thread OS chở virtual thread) | JVM park virtual thread | Viết code blocking bình thường. ⚠️ Đừng pool virtual thread, vì chúng rẻ, cứ tạo mới |

- Hệ quả khi một request làm việc CPU nặng 2 giây:
  - Event loop: mọi request khác trên loop đứng chờ 2 giây.
  - PHP-FPM: chỉ một worker bận, các worker khác vẫn phục vụ bình thường.
  - Goroutine: các goroutine khác vẫn chạy trên các thread OS còn lại.

*Virtual thread chi tiết*
- *Pinning*: virtual thread bị "ghim" vào carrier thread, nên khi nó chặn thì carrier thread cũng bị
  chặn theo, mất lợi thế của virtual thread.
- Pinning theo phiên bản JDK:
  - JDK 21–23: chặn bên trong `synchronized` gây pin carrier thread. Lời khuyên hồi đó là thay
    `synchronized` bằng `ReentrantLock`.
  - JDK 24 (JEP 491) đã sửa. Với JDK 25 LTS không còn phải thay `synchronized` vì lý do này.
  - Vẫn bị pin khi gọi native method hoặc foreign function.
- *ScopedValue* (final ở JDK 25, JEP 506): thay `ThreadLocal` để truyền context bất biến (ví dụ
  user hiện tại) xuống các hàm con. Hợp với hàng triệu virtual thread hơn `ThreadLocal`.

*Ý chính*
- Goroutine và virtual thread cho bạn **viết code đồng bộ, dễ đọc**, với chi phí gần bằng async.
- Chúng **không** làm việc CPU-bound nhanh hơn.
- Chúng **không** bỏ được giới hạn của DB hay connection pool. 100.000 goroutine vẫn chỉ có 20
  connection DB để dùng.

**Đọc**
- JEP: [444 Virtual Threads](https://openjdk.org/jeps/444), [491 Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491), [506 Scoped Values](https://openjdk.org/jeps/506)
- Node.js: [Don't Block the Event Loop](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)
- [What Color is Your Function?](https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/) (Bob Nystrom)

**Nắm chắc khi**
- [ ] So sánh được chi phí bộ nhớ và cách chặn I/O của 5 mô hình trong bảng
- [ ] Giải thích được chuyện gì xảy ra khi một request làm việc CPU 2 giây trong event loop, và trong PHP-FPM
- [ ] Nói đúng trạng thái pinning của virtual thread theo phiên bản JDK

#### 2.7 Tầng PHP: FPM, Laravel, Octane, async

**Vì sao cần học:** Module riêng cho người làm PHP. Câu "PHP có race condition không?" gần như
chắc chắn bị hỏi, và câu trả lời "không, vì PHP không có thread" là red flag. Laravel có sẵn nhiều
công cụ chống race; biết dùng đúng cái nào cho việc nào là điều phân biệt mid với junior.

**Học gì**

*PHP-FPM share-nothing*
- Mỗi request chạy trong một process riêng, không có biến dùng chung, nên code PHP **không có data
  race**.
- Nhưng nhiều process chạy song song, nên race condition **chuyển xuống** những chỗ dùng chung:
  DB, Redis, file, session.

*Công cụ chống race trong Laravel*

| Công cụ | Chặn cái gì | Cạm bẫy |
|---|---|---|
| `lockForUpdate()` / `sharedLock()` trong `DB::transaction()` | Pessimistic lock ở DB (`FOR UPDATE` / `FOR SHARE`) | Phải nằm trong transaction |
| `Cache::lock('key', 10)->get(fn)` / `->block(5, fn)` | Atomic lock trên Redis, DB hoặc Memcached. `get` thử một lần, `block` chờ tối đa 5 giây | ⚠️ Lock có TTL (ở đây 10 giây). Việc chạy lâu hơn TTL thì người khác lấy được lock |
| Job `ShouldBeUnique` | Không cho dispatch job trùng key khi đã có một job như vậy **nằm trong queue**. Khoá giữ tới khi job chạy xong | Chỉ chặn lúc dispatch, không phải exactly-once. Job vẫn phải idempotent |
| Job `ShouldBeUniqueUntilProcessing` | Như trên, nhưng nhả khoá ngay khi job **bắt đầu chạy** | Job mới cùng key vào queue được trong lúc job cũ đang chạy |
| Job middleware `WithoutOverlapping` | Không cho hai job cùng key **chạy song song** | Không chặn việc dispatch trùng |
| Scheduler `withoutOverlapping()`, `onOneServer()` | Lệnh lịch không chạy chồng, và chỉ chạy trên một server khi có nhiều server | `onOneServer()` cần cache driver dùng chung, ví dụ Redis |
| `DB::transaction($fn, 3)` | Tự retry tối đa 3 lần khi gặp deadlock | Closure phải chạy lại được an toàn |
| `afterCommit` | Job dispatch trong transaction chỉ vào queue sau khi transaction commit | Không dùng thì worker có thể chạy job trước khi dữ liệu được commit |

- Ví dụ `Cache::lock`:

  ```php
  Cache::lock("sync:product:{$id}", 10)->block(5, function () use ($id) {
      // tối đa 10 giây giữ lock; chờ lock tối đa 5 giây
      syncStock($id);
  });
  ```

*Session và file*
- ⚠️ Session lưu bằng file có khoá. Nhiều request AJAX cùng một session bị chạy **tuần tự**, request
  này chờ request kia nhả file session.
  - Gọi `session_write_close()` sớm khi không cần ghi session nữa.
  - Chuyển session sang Redis thì hết khoá, nhưng lỗi đổi thành lost update trên session: hai
    request cùng ghi, bản sau đè bản trước.
- `flock()` khoá file, nhưng chỉ chống race trên **một máy**. Hai server thì mỗi server một file.

*Octane: khi PHP có state dùng chung*
- *Octane* chạy Laravel trên Swoole, RoadRunner hoặc FrankenPHP. App được khởi động một lần và
  **sống qua nhiều request**, không chết sau mỗi request như FPM.
- Hệ quả: biến static, singleton, service container được chia sẻ giữa các request. Xuất hiện loại lỗi
  giống lỗi thread:
  - State của request trước rò sang request sau, ví dụ user hiện tại bị giữ lại trong một singleton.
  - Cùng một connection DB bị dùng lại, kéo theo trạng thái cũ của nó.

*Concurrency trong một process PHP*
- *Fibers* (PHP 8.1): primitive nền để tạm dừng và chạy tiếp một hàm. Tự nó không chạy song song gì cả.
- ReactPHP, AMPHP: event loop, dựa trên Fibers hoặc callback.
- Swoole/OpenSwoole: coroutine.
- Laravel `Concurrency::run()`: chạy nhiều closure song song bằng cách tách ra child process.

*Đối chiếu Java/Go*
- Java Spring: bean mặc định là singleton, dùng chung cho mọi request. ⚠️ Field có state trong bean
  là race giữa các request.
- Go: mỗi request HTTP chạy trên một goroutine riêng. State dùng chung phải được bảo vệ bằng mutex.

**Đọc**
- Laravel:
  - [Atomic Locks](https://laravel.com/docs/cache#atomic-locks)
  - [Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking)
  - [Unique Jobs](https://laravel.com/docs/queues#unique-jobs), [Preventing Job Overlaps](https://laravel.com/docs/queues#preventing-job-overlaps), [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions)
  - [Octane](https://laravel.com/docs/octane) (mục dependency injection và memory leak), [Concurrency](https://laravel.com/docs/concurrency)
- PHP: [Fibers](https://www.php.net/manual/en/language.fibers.php), [session_write_close](https://www.php.net/manual/en/function.session-write-close.php), [flock](https://www.php.net/manual/en/function.flock.php)
- [ReactPHP](https://reactphp.org/), [OpenSwoole](https://openswoole.com/)
- Runtime PHP chi tiết: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Viết được luồng áp coupon bằng `lockForUpdate()` và bằng unique constraint, nói cách nào là chốt chặn cuối
- [ ] Phân biệt được `ShouldBeUnique` và `WithoutOverlapping` bằng một ví dụ job mỗi cái chặn được
- [ ] Chỉ ra được 2 bug chỉ xuất hiện khi chuyển app Laravel sang Octane

---

### Chặng 3: Senior 🔴

#### 3.1 Memory model

**Vì sao cần học:** Người phỏng vấn có nền Java/Go hay hỏi "`volatile` đảm bảo gì" hoặc "vì sao
vòng lặp này không bao giờ dừng". Với PHP-FPM bạn không gặp chuyện này, nhưng ở Octane, Swoole,
hay khi viết service Go thì có. Đây là phần giải thích *vì sao* data race nguy hiểm hơn bạn nghĩ.

**Học gì**

*Vấn đề: thread không tự thấy ghi của nhau*
- *Visibility*: không có đồng bộ thì thread khác có thể **không bao giờ** thấy giá trị mới. Lý do:
  - Giá trị có thể đang nằm trong register hoặc cache của CPU, chưa ghi ra bộ nhớ chung.
  - Compiler thấy vòng lặp không tự sửa biến nên chỉ đọc biến một lần, đưa lệnh đọc ra ngoài vòng
    lặp (*hoist*).

  ```java
  boolean stop = false;             // thiếu volatile
  // Thread 1
  while (!stop) { }                 // có thể chạy mãi: compiler đọc stop một lần rồi thôi
  // Thread 2
  stop = true;
  ```
- *Ordering*: compiler và CPU được phép **sắp xếp lại lệnh** miễn là trong một thread kết quả
  không đổi. Thread khác nhìn vào thì có thể thấy thứ tự vô lý, ví dụ thấy cờ `ready = true` trước
  khi thấy dữ liệu đã được ghi.

*Happens-before*
- *Memory model* định nghĩa khi nào một lần ghi **được đảm bảo** là một lần đọc nhìn thấy.
- Công cụ để định nghĩa là quan hệ *happens-before*: nếu ghi X happens-before đọc X thì lần đọc
  chắc chắn thấy giá trị đã ghi.
- Không có happens-before thì không có đảm bảo gì cả. Chạy thử thấy đúng không có nghĩa là đúng.

*Java Memory Model (JMM)*
- Những thứ tạo ra happens-before:
  - Unlock một *monitor* (khoá gắn sẵn với mỗi object, thứ mà `synchronized` dùng), rồi lock chính
    monitor đó.
  - Ghi một biến `volatile`, rồi đọc chính biến đó.
  - `Thread.start()` (với thread mới) và `Thread.join()` (với thread chờ).
  - Các lớp trong `java.util.concurrent`.
- `volatile` đảm bảo visibility và ordering.
  - ⚠️ `volatile` **không** làm `count++` atomic. Đó vẫn là ba bước đọc, cộng, ghi.
- *Double-checked locking* (kiểm tra null, lock, kiểm tra lại, rồi mới tạo object) chỉ đúng khi
  biến có `volatile`. Thiếu `volatile`, lệnh "gán tham chiếu" có thể bị sắp xếp lên trước lệnh
  "khởi tạo xong object", nên thread khác nhận được object chưa khởi tạo xong.
- Chương trình Java có data race vẫn an toàn bộ nhớ (không crash, không hỏng vùng nhớ), nhưng cho kết
  quả bất ngờ.

*Go memory model*
- Những thứ tạo ra happens-before: channel send/receive, `sync.Mutex`, `sync.Once`, `WaitGroup`,
  `sync/atomic`.
  - Thao tác `sync/atomic` trong Go là *sequentially consistent*: mọi goroutine thấy các thao tác
    atomic theo cùng một thứ tự.
- Tài liệu chính thức có câu: nếu phải đọc memory model mới hiểu được chương trình thì chương trình
  đó quá khéo, hãy viết lại cho đơn giản.
- ⚠️ Khác Java: data race trên map, slice, interface trong Go có thể làm crash hoặc **hỏng bộ nhớ**.

*Đối chiếu Java/Go*
- Java có `volatile`, Go không có. Trong Go dùng `sync/atomic` (ví dụ `atomic.Bool`) cho cùng mục đích.
- Cả hai đều khuyên: dùng primitive có sẵn, đừng tự lập luận trên memory model.

**Đọc**
- [The Go Memory Model](https://go.dev/ref/mem)
- [JLS §17.4 Memory Model](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html)
- Aleksey Shipilëv: [Java Memory Model Pragmatics](https://shipilev.net/blog/2014/jmm-pragmatics/) (dài, đọc phần đầu tới happens-before)
- *Java Concurrency in Practice*: ch.3 (visibility) và ch.16

**Nắm chắc khi**
- [ ] Viết được ví dụ vòng lặp `while (!stop)` không bao giờ dừng và sửa bằng `volatile` / `atomic.Bool`
- [ ] Giải thích được vì sao double-checked locking thiếu `volatile` có thể trả object chưa khởi tạo xong

#### 3.2 Lock-free, ABA, spinlock

**Vì sao cần học:** Backend hiếm khi tự viết code lock-free, nhưng vấn đề ABA có bản sao ở tầng
DB: optimistic lock so sánh sai cột sẽ gặp đúng lỗi này. Câu "CAS là gì, ABA là gì" hay xuất hiện
ở vòng senior Java/Go.

**Học gì**

*Lock-free và wait-free*
- *Lock-free*: thuật toán không dùng khoá, và tại mọi thời điểm luôn có **ít nhất một** thread đang
  tiến triển. Một thread bị treo không chặn được cả hệ thống.
- *Wait-free*: mạnh hơn, **mọi** thread đều xong việc sau một số bước hữu hạn.

*Vấn đề ABA*
- Kịch bản:
  1. Thread 1 đọc giá trị A, chuẩn bị CAS từ A sang giá trị mới.
  2. Thread 2 đổi A thành B.
  3. Thread 2 đổi B về lại A.
  4. Thread 1 CAS với `expected = A`: thành công, dù trạng thái đã thay đổi hai lần.
- Vì sao nguy hiểm: trong lock-free stack, "A" có thể là con trỏ tới một node đã bị lấy ra rồi đưa
  vào lại, nên stack bị hỏng.
- Cách sửa:
  - Gắn version hoặc tag tăng dần vào giá trị, ví dụ `AtomicStampedReference` của Java.
  - Dựa vào GC hoặc *hazard pointer* để một node không bị dùng lại khi còn thread đang nhìn nó.
- Trong DB: optimistic lock phải dùng cột `version` **tăng dần**, không so giá trị nghiệp vụ.
  - Ví dụ: đơn đi từ `pending` sang `paid` rồi bị hoàn về `pending`. So `WHERE status = 'pending'`
    thì một update cũ vẫn khớp.

*Spinlock*
- *Spinlock*: khoá mà luồng chờ không ngủ, cứ quay vòng kiểm tra liên tục.
- Hợp khi critical section cực ngắn và có nhiều core. Không phải trả chi phí ngủ rồi thức dậy.
- Tệ khi giữ khoá lâu, hoặc chỉ có một core: luồng chờ đốt CPU mà người giữ khoá không được chạy.
- Mutex hiện đại kết hợp cả hai: spin một chút, rồi mới ngủ.

*Ví dụ thực tế trong Java*
- `ConcurrentLinkedQueue`: queue lock-free.
- `LongAdder`: bộ đếm chia thành nhiều ô, mỗi thread cộng vào một ô khác nhau, đọc thì cộng các ô
  lại. Ít tranh chấp hơn `AtomicLong`, nơi mọi thread CAS cùng một biến.
- ⚠️ Lock-free khó viết đúng, và không nhất thiết nhanh hơn lock khi tranh chấp thấp. Backend chỉ
  cần biết dùng thư viện có sẵn.

**Đọc**
- *Java Concurrency in Practice*: ch.15
- *The Art of Multiprocessor Programming* (Herlihy, Shavit): nếu muốn đi sâu

**Nắm chắc khi**
- [ ] Vẽ được kịch bản ABA trên lock-free stack và trên cột `status` của một đơn hàng
- [ ] Giải thích được vì sao `LongAdder` nhanh hơn `AtomicLong` khi tranh chấp cao

#### 3.3 Priority inversion, bulkhead, actor model

**Vì sao cần học:** Câu chuyện Mars Pathfinder là ví dụ kinh điển, nhưng điều người phỏng vấn
senior muốn nghe là bản ở tầng hệ thống: job batch chiếm hết connection pool làm request thanh
toán phải chờ, SMS OTP đứng sau chiến dịch marketing. Actor model giải thích vì sao "mỗi entity
một writer" loại bỏ được tranh chấp.

**Học gì**

*Priority inversion*
- *Priority inversion*: thread ưu tiên cao phải chờ thread ưu tiên thấp, vì bị chặn bởi một thread
  ưu tiên trung bình.
- Kịch bản:
  1. Thread thấp (L) lấy khoá X.
  2. Thread cao (H) cần khoá X, phải chờ L.
  3. Thread trung bình (M) không cần khoá, nhưng ưu tiên hơn L nên chiếm CPU.
  4. L không được chạy để nhả khoá, nên H chờ mãi dù có ưu tiên cao nhất.
- Mars Pathfinder (1997) gặp đúng lỗi này và bị reset liên tục.
- Cách sửa: *priority inheritance*. Thread đang giữ khoá tạm được nâng lên bằng ưu tiên của thread
  cao nhất đang chờ nó.

*Bản ở tầng backend và bulkhead*
- Request quan trọng phải chờ connection pool bị job batch chiếm hết.
- SMS OTP đứng trong queue sau hàng trăm nghìn SMS của chiến dịch marketing.
- Cách chặn:
  - *Bulkhead*: pool riêng cho từng loại việc (một pool cho batch, một pool cho request người dùng).
  - Queue ưu tiên riêng: OTP một queue, marketing một queue khác.

*Actor model (đại ý)*
- Mỗi *actor* có state riêng và một hộp thư (*mailbox*). Actor xử lý từng message một, tuần tự,
  nên không cần lock.
- Ví dụ: Erlang/Elixir, Akka.
- Đánh đổi:
  - Mailbox có thể đầy.
  - Khó debug hơn.
  - Kiểu request/response phải viết thành bất đồng bộ.

*"Một writer cho mỗi entity" ở quy mô hệ thống*
- Đây là actor model áp cho cả hệ thống: mọi thay đổi của cùng một entity đi qua một chỗ duy nhất,
  tuần tự.
- Ví dụ:
  - Kafka partition theo key: mọi message cùng `order_id` vào cùng partition, do một consumer đọc
    theo thứ tự.
  - SQS FIFO message group: các message cùng group được xử lý lần lượt.

**Đọc**
- [What really happened on Mars?](https://www.cs.cornell.edu/courses/cs614/1999sp/papers/pathfinder.html) (Glenn Reeves)
- Microsoft: [Bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)

**Nắm chắc khi**
- [ ] Kể được một "priority inversion" ở mức hệ thống backend và cách tách tài nguyên để chặn

#### 3.4 Tranh chấp cực cao: flash sale, hot row

**Vì sao cần học:** Flash sale là bài system design rất hay gặp ở công ty thương mại điện tử Việt
Nam. Nó gom mọi thứ ở các module trước: atomic update, Redis, queue, unique constraint. Người phỏng
vấn muốn thấy bạn chặn ở nhiều tầng, không dồn hết vào DB.

**Học gì**

*Vì sao cách thông thường sập*
- *Hot row* là một dòng mà rất nhiều request cùng muốn sửa, ví dụ dòng tồn kho của sản phẩm đang sale.
- ⚠️ `SELECT ... FOR UPDATE` trên một hot row với 10.000 request:
  1. Mỗi lúc chỉ một transaction giữ khoá, 9.999 cái còn lại xếp hàng.
  2. Mỗi transaction đang chờ vẫn giữ một connection DB.
  3. Connection pool cạn, request khác (kể cả không liên quan tới sale) cũng không lấy được connection.
  4. Request timeout, client retry, tải tăng thêm. Timeout lan dây chuyền.

*Chặn sớm*
- Mục tiêu: **từ chối rẻ**, trước khi request chạm tới DB.
- Rate limit theo user hoặc IP.
- *Waiting room*: phòng chờ, chỉ cho một lượng người vào luồng mua mỗi lúc.
- CDN phục vụ trang tĩnh, để server chỉ nhận request mua thật.

*Luồng trừ tồn kho nhiều tầng*
1. Trừ trong Redis bằng `DECR` hoặc Lua script (atomic), kèm một set lưu user đã mua để chặn mua trùng.
2. Người trúng được đưa vào queue.
3. Worker lấy từ queue và ghi DB bằng atomic update. Đây là chốt chặn cuối.
4. Unique `(user_id, sale_id)` ở DB chặn một người mua hai lần.

*Giữ chỗ và đối soát*
- Giữ chỗ có hạn, ví dụ 10 phút. Không thanh toán thì trả lại kho.
- Sau đợt sale, đối soát số liệu Redis với DB.

*Chia nhỏ điểm nóng*
- Chia tồn kho thành nhiều bucket: nhiều dòng trong DB hoặc nhiều key trong Redis. Mỗi request
  trừ ở một bucket, nên tranh chấp không dồn vào một điểm.
- Thiết kế đầy đủ ở [16-system-design.md](16-system-design.md).

**Đọc**
- Redis: [SET](https://redis.io/docs/latest/commands/set/) (`NX`, `PX`)
- [16-system-design.md](16-system-design.md) bài flash sale

**Nắm chắc khi**
- [ ] Vẽ được luồng flash sale 100 sản phẩm / 10.000 người và chỉ ra chốt chặn ở từng tầng
- [ ] Nói được Redis lệch DB theo hướng nào thì chấp nhận được, hướng nào không

#### 3.5 Kiểm thử và điều tra lỗi concurrency

**Vì sao cần học:** Bug concurrency hiếm khi hiện ra khi test bằng tay, và chạy test nhiều lần
thấy pass không chứng minh gì. Senior phải biết công cụ của từng ngôn ngữ, biết cách tái hiện race
trong app web, và hiểu giới hạn của công cụ. Câu "Java có race detector như Go không" là câu bẫy
hay gặp.

**Học gì**

*Go*
- *Race detector*: chạy `go test -race` hoặc `go run -race`. Runtime theo dõi mọi lần truy cập bộ
  nhớ và báo data race.
  - ⚠️ Chỉ bắt race **thực sự chạy qua** trong lần chạy đó. Đoạn code không được chạy tới thì không
    được kiểm tra.
- `testing/synctest` (GA ở Go 1.25): chạy test trong một "bubble" có đồng hồ ảo.
  - Code có timeout hay `time.Sleep` chạy ngay lập tức theo đồng hồ ảo, nên test không chậm và không
    flaky.
- Go 1.26 có goroutine leak profile ở dạng experiment.
- Điều tra: `pprof` goroutine profile, hoặc gửi `SIGQUIT` để in stack của mọi goroutine.

*Java*
- ⚠️ Java **không có** race detector chuẩn tương đương `-race`.
- Dùng [jcstress](https://github.com/openjdk/jcstress): chạy một đoạn code nhiều lần song song và
  thống kê các kết quả xuất hiện, để thấy kết quả "không thể" có thật sự xảy ra không.
- Kết hợp với code review và static analysis.
- Điều tra: thread dump bằng `jstack` hoặc `jcmd Thread.print`, thấy deadlock và thread nào đang chờ gì.

*Database*
- `SHOW ENGINE INNODB STATUS`: deadlock gần nhất.
- `performance_schema.data_locks`: lock đang được giữ.
- Log lock wait.

*Tái hiện race trong app web*
- Bắn nhiều request song song vào cùng một endpoint:
  - `xargs -P` chạy nhiều `curl` song song.
  - `ab` hoặc `k6` cho tải lớn hơn.
- Test tích hợp mở hai transaction, cho chúng chạy xen kẽ theo đúng thứ tự gây lỗi.

  ```bash
  # 20 request áp coupon cùng lúc
  seq 20 | xargs -P 20 -I{} curl -s -X POST localhost:8000/api/coupons/apply -d 'code=SALE50'
  ```

*Giới hạn của test*
- ⚠️ Test pass không chứng minh là không có race.
- Cần lập luận về *bất biến* (điều luôn phải đúng, ví dụ "tồn kho không âm") và đặt constraint ở DB
  để giữ bất biến đó.

**Đọc**
- Go: [Data Race Detector](https://go.dev/doc/articles/race_detector), [testing/synctest](https://pkg.go.dev/testing/synctest), blog [Testing concurrent code with testing/synctest](https://go.dev/blog/synctest)
- [jcstress](https://github.com/openjdk/jcstress): README và thư mục samples

**Nắm chắc khi**
- [ ] Tạo và bắt được data race bằng `-race`, rồi sửa bằng ba cách (bài tập 1)
- [ ] Viết được test dùng `synctest` cho một hàm có timeout 5 giây mà test chạy dưới 1 giây
- [ ] Tái hiện được race coupon trên app Laravel bằng 20 request song song

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Concurrency và parallelism khác nhau thế nào?** (1.1)
- Ý phải có: đan xen trong cùng khoảng thời gian so với chạy cùng lúc thật; concurrency chạy được trên một core
- Điểm cộng: ví dụ Node.js, Go, PHP-FPM mỗi cái thuộc loại nào

**2. Race condition là gì? Cho ví dụ trong ứng dụng web.** (1.1, 1.4)
- Ý phải có: kết quả phụ thuộc thứ tự thực thi; ví dụ hai request cùng trừ tồn kho hoặc cùng dùng coupon
- Red flag: chỉ nêu ví dụ thread trong bộ nhớ, không nghĩ tới DB

**3. Mutex và semaphore khác nhau thế nào?** (1.2)
- Ý phải có: một người giữ so với N permit; mutex có chủ sở hữu
- Điểm cộng: ví dụ semaphore giới hạn lời gọi API ngoài; buffered channel trong Go

**4. Deadlock là gì? Ví dụ trong database và cách tránh.** (1.3)
- Ý phải có: chờ vòng tròn, bốn điều kiện; ví dụ chuyển tiền hai chiều; khoá theo thứ tự id
- Điểm cộng: DB tự phát hiện và rollback một bên, nên app phải retry; đọc deadlock log

**5. PHP có race condition không?** (2.7)
- Ý phải có: không có data race vì FPM share-nothing, nhưng race condition ở DB/Redis/file/session đầy vì nhiều process chạy song song
- Điểm cộng: Octane/Swoole đưa state dùng chung trở lại; session file lock làm AJAX chạy tuần tự
- Red flag: "Không, PHP không có thread"

**6. Check-then-act là gì, sửa thế nào?** (1.4)
- Ý phải có: kiểm tra và hành động là hai bước, request khác chen vào giữa; sửa bằng thao tác atomic: unique constraint, `UPDATE ... WHERE` điều kiện, `INSERT ... ON DUPLICATE KEY`, Redis `SET NX`
- Red flag: "kiểm tra kỹ hơn ở tầng app"

### 🟡 Mid

**7. Hai request cùng trừ tồn kho. Sửa thế nào?** (1.4)
- Ý phải có: atomic update có điều kiện + kiểm tra affected rows; `FOR UPDATE` khi logic nhiều bước; optimistic khi ít tranh chấp
- Điểm cộng: nói nhược điểm từng cách; constraint làm chốt chặn cuối; Redis + queue khi đỉnh tải cực lớn
- Red flag: "dùng `synchronized`" hoặc "bọc trong transaction là đủ"

**8. Optimistic lock và pessimistic lock, khi nào dùng cái nào?** (2.1, 1.4)
- Ý phải có: optimistic khi tranh chấp thấp hoặc thao tác kéo dài (form người dùng); pessimistic khi tranh chấp cao, thao tác ngắn
- Điểm cộng: optimistic là CAS ở mức dữ liệu; tranh chấp cao thì optimistic retry liên tục; `ETag`/`If-Match`

**9. MySQL và Postgres cùng ở REPEATABLE READ. Hai transaction đọc-sửa-ghi cùng một dòng thì chuyện gì xảy ra ở mỗi DB?** (2.2)
- Ý phải có: Postgres báo lỗi serialization `40001`, app phải retry; InnoDB không báo lỗi, bản ghi sau đè bản trước (lost update)
- Điểm cộng: vì sao `SET x = x - 1` vẫn an toàn ở InnoDB (locking read đọc bản mới nhất); dẫn sang module 2.5 của [03](03-database-sql.md)
- Red flag: "RR thì không có lost update"

**10. Làm sao chống double submit tạo hai đơn hàng?** (2.3)
- Ý phải có: idempotency key do client sinh, lưu với unique constraint, trả response cũ khi trùng
- Điểm cộng: hai request cùng key đến cùng lúc (trạng thái `processing`); cùng key khác body; truyền key sang PSP
- Red flag: "disable nút bấm là đủ"

**11. Chọn kích thước thread pool thế nào? Little's law là gì?** (2.4)
- Ý phải có: CPU-bound ≈ số core; I/O-bound theo tỉ lệ chờ/tính; `L = λ × W`
- Điểm cộng: nhìn tài nguyên phía sau (connection pool, rate limit API); bounded queue; đo p99 bằng load test
- Red flag: một con số cố định không có lập luận

**12. Vì sao `synchronized`/`sync.Mutex` không đủ khi chạy nhiều instance?** (1.4, 2.7)
- Ý phải có: lock trong bộ nhớ chỉ có tác dụng trong một process
- Điểm cộng: ưu tiên đẩy tính đúng xuống DB; distributed lock chỉ khi tài nguyên ngoài DB; lock có TTL và fencing ([14](14-distributed-systems.md))

**13. `Cache::lock`, `ShouldBeUnique` và `WithoutOverlapping` trong Laravel khác nhau thế nào?** (2.7)
- Ý phải có: lock nguyên tử tổng quát; chặn job trùng **nằm trong queue**; chặn job cùng key **chạy song song**
- Điểm cộng: TTL của lock ngắn hơn thời gian chạy thì mất tác dụng; job vẫn phải idempotent vì at-least-once
- Red flag: coi `ShouldBeUnique` là đảm bảo exactly-once

**14. Goroutine khác thread OS thế nào? Virtual thread của Java khác gì?** (2.6)
- Ý phải có: M:N, stack nhỏ tự giãn, runtime lập lịch và park khi chặn I/O; virtual thread cùng ý tưởng trên JVM
- Điểm cộng: pinning trong `synchronized` đã sửa ở JDK 24 (JEP 491); không pool virtual thread; không làm CPU-bound nhanh hơn

**15. Event loop bị chặn thì chuyện gì xảy ra? So sánh với goroutine và PHP-FPM.** (2.6)
- Ý phải có: mọi request khác trên loop đứng chờ; goroutine bị chặn thì runtime chạy goroutine khác; FPM thì chỉ một worker bận
- Điểm cộng: đẩy việc CPU nặng sang worker thread/process; ReactPHP/Swoole có cùng rủi ro với code blocking

**16. Queue có 5 worker, hai message cùng cập nhật một đơn hàng. Có race không?** (2.3, 3.3)
- Ý phải có: có, như hai request web; at-least-once còn cho phép cùng message chạy song song
- Điểm cộng: tuần tự theo entity (Kafka key, SQS FIFO group, `WithoutOverlapping`), idempotent chịu được song song ([12](12-messaging.md))

### 🔴 Senior

**17. Data race và race condition khác nhau thế nào? Có cái này mà không có cái kia được không?** (1.1)
- Ý phải có: data race là khái niệm memory model, race condition là lỗi logic; ví dụ check-then-act có khoá từng bước
- Điểm cộng: công cụ chỉ bắt được data race (`-race`), race condition phải lập luận bất biến

**18. Happens-before là gì? `volatile` trong Java đảm bảo gì và không đảm bảo gì?** (3.1)
- Ý phải có: quan hệ đảm bảo visibility và ordering; `volatile` có visibility, ordering nhưng không atomic cho read-modify-write
- Điểm cộng: double-checked locking; Go không có `volatile`, dùng `sync/atomic`

**19. CAS là gì, vấn đề ABA là gì và sửa thế nào?** (2.1, 3.2)
- Ý phải có: so và ghi nguyên tử; A→B→A làm CAS thành công sai; gắn version
- Điểm cộng: cột `version` tăng dần trong optimistic lock chính là cách chống ABA ở mức DB

**20. Java có race detector như `go test -race` không? Bạn kiểm thử code concurrent thế nào?** (3.5)
- Ý phải có: không có race detector chuẩn; jcstress để stress test; thread dump; review theo bất biến
- Điểm cộng: `-race` chỉ bắt race đã chạy qua; `testing/synctest` cho code có thời gian; tái hiện race DB bằng request song song
- Red flag: "chạy test nhiều lần thấy pass là không có race"

**21. Priority inversion là gì? Có tương đương ở mức hệ thống backend không?** (3.3)
- Ý phải có: thread cao chờ khoá của thread thấp bị thread trung bình chiếm CPU; priority inheritance
- Điểm cộng: job batch chiếm connection pool làm request thanh toán chờ; bulkhead, queue ưu tiên

**22. Flash sale 100 sản phẩm, 10.000 người cùng mua. Không bán quá số lượng thế nào?** (3.4)
- Ý phải có: chặn sớm; trừ nguyên tử trong Redis; queue tạo đơn; DB atomic update + unique làm chốt cuối
- Điểm cộng: vì sao `FOR UPDATE` trên dòng hot sập pool; giữ chỗ có hạn; đối soát; chia bucket
- Red flag: "tăng cấu hình DB"

**23. Tình huống: hệ thống coupon mỗi user dùng một lần, log cho thấy vài user dùng hai lần.** (1.4, 2.7)
- Ý phải có: check-then-act giữa hai request (double click, hai tab); thêm `UNIQUE(user_id, coupon_id)`, insert trước khi áp dụng, bắt lỗi unique
- Điểm cộng: dọn dữ liệu trùng trước khi thêm constraint; xử lý lỗi unique thành thông báo nghiệp vụ

**24. Tình huống: service Java thêm cache `HashMap` làm field của bean, thỉnh thoảng CPU 100% hoặc dữ liệu sai.** (2.7, 3.1)
- Ý phải có: bean singleton dùng chung giữa thread, `HashMap` không thread-safe
- Điểm cộng: `ConcurrentHashMap.computeIfAbsent` hoặc Caffeine; đối chiếu biến static trong Octane

**25. Tình huống: Go service mở một goroutine cho mỗi dòng của file 1 triệu dòng để gọi API, bên kia trả 429 và service hết bộ nhớ.** (2.5)
- Ý phải có: không giới hạn concurrency; worker pool hoặc `errgroup.SetLimit`, rate limiter
- Điểm cộng: đọc file dạng stream; truyền `context` để huỷ; retry có backoff cho 429

**26. Tình huống: API tạo thanh toán bị gọi hai lần do client retry sau timeout, khách bị trừ tiền hai lần.** (2.3)
- Ý phải có: idempotency key từ client, bảng key có unique, trạng thái `processing`, trả response cũ
- Điểm cộng: truyền idempotency key sang cổng thanh toán; timeout không có nghĩa là thất bại ([14](14-distributed-systems.md))

---

## Bài tập tự làm

1. **Data race trong Go.** Viết chương trình có data race trên một biến đếm, chạy với `-race`,
   rồi sửa bằng ba cách: `sync.Mutex`, `atomic.Int64`, và channel. So sánh độ dài và độ rõ
   ràng. Dùng `wg.Go` (Go 1.25+) thay cho `Add`/`Done`.
2. **Chuyển tiền an toàn.** Với bảng `accounts(id, balance, version)`, viết SQL chuyển tiền
   bằng hai cách: pessimistic và optimistic. Chỉ ra kịch bản deadlock của cách pessimistic và
   cách tránh. Nếu có Postgres, chạy cùng kịch bản đọc-sửa-ghi ở RR trên cả hai DB và ghi lại
   khác biệt.
3. **Sizing.** Tính kích thước thread pool và connection pool cho service: 300 request/giây,
   mỗi request gọi DB 2 lần mỗi lần 15 ms, và gọi một API ngoài 120 ms. Nêu giả định. Làm lại
   cho trường hợp service là PHP-FPM: cần bao nhiêu worker, bao nhiêu server nếu mỗi server
   chạy được 40 worker.
4. **Idempotency.** Thiết kế bảng và luồng xử lý idempotency key cho API `POST /payments`,
   xử lý đúng khi hai request cùng key đến cùng lúc, và khi cùng key nhưng body khác.
5. **Liệt kê race.** Liệt kê mọi race condition có thể có trong luồng "đăng ký tài khoản
   bằng email + gửi mã xác thực + xác thực mã", và cách chặn từng cái.
6. **Laravel.** Trong một project Laravel:
   - Viết endpoint áp coupon có race, bắn 20 request song song để tái hiện dùng trùng.
   - Sửa lần lượt bằng `lockForUpdate()`, `Cache::lock()`, và unique constraint. Ghi lại cách
     nào vẫn lọt khi chạy 2 server, cách nào không.
   - Viết một job đồng bộ tồn kho dùng `WithoutOverlapping`, giải thích nó chặn được gì và
     không chặn được gì so với `ShouldBeUnique`.

> Nộp bài vào đây để được review.
