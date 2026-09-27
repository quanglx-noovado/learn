# 13. Concurrency · Kiến thức

> [← Plan ôn tập](../13-concurrency.md) · [Mục lục kiến thức](README.md)
> Bài đọc tổng hợp từ tài liệu gốc ở mục "Đọc" của từng module. Đọc sau khi đã xem plan; tick các
> tiêu chí "Nắm chắc khi" ở file plan. Mọi nội dung đã qua một lượt review độc lập đối chiếu nguồn gốc.

## Mục lục

- Chặng 1: Nền
  - [1.1 Concurrency, race condition, critical section](#11-concurrency-race-condition-critical-section)
  - [1.2 Primitive đồng bộ cơ bản](#12-primitive-đồng-bộ-cơ-bản)
  - [1.3 Deadlock, livelock, starvation](#13-deadlock-livelock-starvation)
  - [1.4 Race condition trong ứng dụng web](#14-race-condition-trong-ứng-dụng-web)
- Chặng 2: Làm chủ
  - [2.1 Atomic, CAS và optimistic lock](#21-atomic-cas-và-optimistic-lock)
  - [2.2 Lost update và isolation level](#22-lost-update-và-isolation-level)
  - [2.3 Double submit, idempotency key](#23-double-submit-idempotency-key)
  - [2.4 Thread pool, connection pool, Little's law](#24-thread-pool-connection-pool-littles-law)
  - [2.5 Pattern concurrency trong Go (và đối chiếu Java)](#25-pattern-concurrency-trong-go-và-đối-chiếu-java)
  - [2.6 Mô hình chạy: process, thread, event loop, goroutine, virtual thread](#26-mô-hình-chạy-process-thread-event-loop-goroutine-virtual-thread)
  - [2.7 Tầng PHP: FPM, Laravel, Octane, async](#27-tầng-php-fpm-laravel-octane-async)
- Chặng 3: Senior
  - [3.1 Memory model](#31-memory-model)
  - [3.2 Lock-free, ABA, spinlock](#32-lock-free-aba-spinlock)
  - [3.3 Priority inversion, bulkhead, actor model](#33-priority-inversion-bulkhead-actor-model)
  - [3.4 Tranh chấp cực cao: flash sale, hot row](#34-tranh-chấp-cực-cao-flash-sale-hot-row)
  - [3.5 Kiểm thử và điều tra lỗi concurrency](#35-kiểm-thử-và-điều-tra-lỗi-concurrency)

---

## Chặng 1: Nền

### 1.1 Concurrency, race condition, critical section

Module này trả lời: concurrency và parallelism khác nhau ở đâu, vì sao `count++` có thể mất lần tăng,
và vì sao PHP-FPM không chia sẻ biến giữa các request mà vẫn đầy race condition.

#### Concurrency và parallelism

Hai từ này hay bị dùng lẫn, nhưng nói về hai tầng khác nhau:

- *Concurrency* là cách **cấu trúc** chương trình: chia việc thành nhiều luồng thực thi độc lập, để
  chúng tiến triển đan xen trong cùng một khoảng thời gian. Theo bài Go blog giới thiệu talk của Rob
  Pike, concurrency là "the composition of independently executing processes", tức là *dealing with*
  nhiều việc cùng lúc.
- *Parallelism* là chuyện **thực thi**: nhiều phép tính chạy đồng thời thật sự trên nhiều core. Nó là
  *doing* nhiều việc cùng lúc.

Một chương trình concurrent chạy được trên một core: CPU chuyển qua lại giữa các luồng (*context
switch*), mỗi lúc chỉ chạy một luồng, nhưng nhìn từ ngoài thì các việc cùng tiến triển. Chạy chương
trình đó trên nhiều core thì nó có thêm parallelism. Concurrency là điều kiện để có thể song song hoá;
nó không bảo đảm chạy nhanh hơn.

OSTEP nêu hai lý do để dùng nhiều thread trong một chương trình, tương ứng đúng hai khái niệm trên:

1. **Parallelism**: chia một việc tính toán lớn cho mỗi CPU một phần.
2. **Không bị chặn bởi I/O chậm**: trong lúc một thread chờ đĩa hay mạng, scheduler cho thread khác
   chạy. Đây là concurrency thuần tuý, có ích cả trên máy một core. Web server và DB dùng thread chủ
   yếu vì lý do này.

| Runtime | Concurrent | Parallel | Ghi chú |
|---|---|---|---|
| Node.js | Có | Mặc định không (trừ khi dùng `worker_threads`) | Một thread chạy JavaScript, các việc đan xen quanh I/O qua event loop |
| Go | Có | Có khi `GOMAXPROCS > 1` | Runtime xếp nhiều goroutine lên nhiều thread OS. `GOMAXPROCS` mặc định theo số CPU dùng được |
| Java | Có | Có | Mỗi platform thread là một thread OS; virtual thread ở module 2.6 |
| PHP-FPM | Có, giữa các request | Có, giữa các request | Nhiều worker process chạy song song; trong một process, request chạy tuần tự từ đầu đến cuối |

Điểm cần nói được khi phỏng vấn: PHP-FPM không có thread trong code của bạn, nhưng hệ thống vẫn
**concurrent và parallel** ở mức process. Hai request cùng lúc là hai process chạy song song trên hai
core, cùng đọc ghi một MySQL, một Redis. Mọi vấn đề ở module này đều áp dụng, chỉ khác chỗ dữ liệu dùng
chung nằm ở DB/cache chứ không nằm trong RAM của process.

#### Race condition và critical section

*Race condition* là khi tính đúng của kết quả phụ thuộc vào **thứ tự hay thời điểm** các luồng được
chạy, và tồn tại ít nhất một thứ tự cho ra kết quả sai. Chương trình có race condition là
*indeterminate* (OSTEP dùng từ này): chạy cùng đầu vào nhiều lần có thể ra kết quả khác nhau.

Ví dụ kinh điển là tăng một bộ đếm dùng chung. `count++` trông như một lệnh, nhưng CPU làm ba bước:

```
load  count -> eax    ; 1. đọc giá trị từ bộ nhớ vào thanh ghi
add   eax, 1         ; 2. cộng trong thanh ghi
store eax -> count   ; 3. ghi thanh ghi về bộ nhớ
```

(Pseudo-assembly cho dễ đọc; trên x86 thật là hai lệnh `mov` kẹp một lệnh `add`, như OSTEP minh hoạ.) Kiểu thao tác "đọc, tính, ghi"
này gọi là *read-modify-write*. Mỗi thread có bộ thanh ghi riêng, và scheduler có thể ngắt thread ở
**bất kỳ** lệnh nào. Timeline hai thread, `count` ban đầu bằng 50:

| Bước | Thread A | Thread B | `count` trong bộ nhớ |
|---|---|---|---|
| 1 | đọc: `eax = 50` | | 50 |
| 2 | cộng: `eax = 51` | | 50 |
| 3 | (bị ngắt, scheduler chuyển sang B) | đọc: `eax = 50` | 50 |
| 4 | | cộng: `eax = 51` | 50 |
| 5 | | ghi | 51 |
| 6 | ghi (vẫn là 51 trong thanh ghi của A) | | 51 |

Hai lần tăng, kết quả chỉ tăng một. Tự chạy thử bằng Go (lưu thành `race.go`, chạy `go run race.go`,
cần Go 1.25+ vì dùng `WaitGroup.Go`):

```go
package main

import (
	"fmt"
	"sync"
)

func main() {
	var count int
	var wg sync.WaitGroup
	for range 2 {
		wg.Go(func() {
			for range 1_000_000 {
				count++ // đọc, cộng, ghi: ba bước, không được bảo vệ
			}
		})
	}
	wg.Wait()
	fmt.Println(count) // kỳ vọng 2000000; thực tế nhỏ hơn và mỗi lần chạy một khác
}
```

Ba lần chạy thử trên một máy Apple Silicon ra `1001649`, `1000752`, `1003474`: gần một nửa số lần
tăng bị mất. Con số cụ thể phụ thuộc máy và lần chạy; điều chắc chắn là nó không đáng tin.

*Critical section* là đoạn code truy cập tài nguyên dùng chung (biến, cấu trúc dữ liệu, dòng trong DB,
file) và **không được** có hơn một luồng chạy nó cùng lúc. Ở ví dụ trên, critical section là dòng
`count++`. Tính chất cần có cho critical section gọi là *mutual exclusion*: một luồng đang ở trong thì
các luồng khác bị chặn ở ngoài. Công cụ tạo ra mutual exclusion là mutex (module 1.2). Sửa ví dụ trên:

```go
var mu sync.Mutex
// ... trong goroutine:
mu.Lock()
count++ // giờ chỉ một goroutine ở đây tại một thời điểm
mu.Unlock()
// kết quả luôn là 2000000
```

Các khái niệm critical section, mutual exclusion phần lớn do Edsger Dijkstra đặt ra từ những năm
1960, khi viết hệ điều hành: kernel là chương trình concurrent đầu tiên.

Hai dạng race hay gặp nhất trong code thật (nghiên cứu của Lu và cộng sự năm 2008 trên MySQL, Apache,
Mozilla, OpenOffice, được OSTEP trích: 97% bug concurrency không phải deadlock thuộc hai dạng này):

- *Atomicity violation*: một đoạn nhiều bước được **ngầm giả định** là không bị chen, nhưng không có
  gì bảo đảm điều đó. Ví dụ từ MySQL: thread 1 kiểm tra `if (thd->proc_info)` rồi mới dùng nó, thread 2
  gán `proc_info = NULL` vào giữa, thread 1 dùng con trỏ NULL và crash. `count++` và mọi mẫu
  *check-then-act* ("kiểm tra rồi hành động", module 1.4) thuộc dạng này.
- *Order violation*: code giả định A luôn xảy ra trước B, nhưng không có gì ép thứ tự đó. Ví dụ: thread
  cha tạo thread con rồi gán `mThread`, nhưng thread con chạy ngay và đọc `mThread` khi nó còn NULL.
  Sửa bằng cơ chế chờ, như condition variable hay channel (module 1.2).

Cùng hai dạng này ở ứng dụng web PHP:

- Atomicity violation: `if (!User::where('email', $e)->exists()) { User::create(...); }`, hai request
  cùng qua bước kiểm tra, tạo hai user trùng email.
- Order violation: dispatch job trong transaction; worker chạy job trước khi transaction commit và không
  tìm thấy bản ghi (xem [module 2.6 Queue của 05](05-php-laravel.md#26-queue)).

#### Data race khác race condition

*Data race* là khái niệm hẹp và chính xác hơn, thuộc về *memory model* (bộ quy tắc của ngôn ngữ về
việc khi nào một thread chắc chắn thấy giá trị thread khác ghi, module 3.1). Có data race khi:

1. Hai luồng truy cập **cùng một vùng nhớ**,
2. ít nhất một truy cập là ghi,
3. và giữa hai truy cập không có quan hệ đồng bộ nào (không mutex, không atomic, không channel).

⚠️ Nhiều tài liệu dùng hai từ như nhau (OSTEP viết "race condition (or data race)"), nhưng phỏng vấn
senior hay hỏi để phân biệt, vì chúng **độc lập**: có cái này không kéo theo cái kia.

| | Có data race | Không có data race |
|---|---|---|
| **Có race condition** | `count++` không khoá ở trên | Check-then-act mà mỗi bước khoá riêng; hai process PHP cùng đọc rồi ghi một dòng DB |
| **Không có race condition** | Nhiều thread cùng ghi `lastSeenAt = now()` không khoá, ai thắng cũng được về nghiệp vụ (nhưng vẫn là data race, vẫn là bug theo memory model) | Code đồng bộ đúng |

Ví dụ race condition không có data race, bằng Java:

```java
// Mỗi method của account đều synchronized, nên không có data race nào.
if (account.getBalance() >= 100) {   // bước 1: lock, đọc, unlock
    account.withdraw(100);           // bước 2: lock, trừ, unlock
}
// Hai thread cùng qua bước 1 khi số dư là 100, rồi cùng trừ: số dư thành -100.
```

Khoá từng bước không sửa được, vì lỗi nằm ở **khoảng hở giữa** bước 1 và bước 2. Cách sửa là mở rộng
critical section cho trùm cả check lẫn act, tức một thao tác duy nhất:

```java
// Trong class Account: kiểm tra và trừ nằm trong cùng một critical section
public synchronized boolean withdrawIfEnough(long amount) {
    if (balance < amount) return false;
    balance -= amount;
    return true;
}
```

Ở tầng DB, cách sửa tương đương là gộp check và act vào một câu lệnh:
`UPDATE accounts SET balance = balance - 100 WHERE id = ? AND balance >= 100`, rồi kiểm tra affected
rows (module 1.4).

Vì sao phân biệt quan trọng: công cụ tự động chỉ bắt được data race. Chạy ví dụ Go ở trên với
`go run -race race.go`, *race detector* in ra báo cáo bắt đầu bằng `WARNING: DATA RACE` kèm stack của
lần đọc và lần ghi xung đột. Nhưng ví dụ `withdrawIfEnough` viết sai (hai bước khoá riêng) thì race
detector im lặng, vì mọi truy cập đều có khoá. Race condition logic phải tự lập luận, hoặc bắt bằng
test tải và ràng buộc ở DB (module 3.5).

PHP-FPM là trường hợp cực đoan: mỗi request là một process riêng, không có vùng nhớ chung, nên về định
nghĩa **không thể** có data race giữa các request. Nhưng race condition thì có ở khắp nơi, vì dữ liệu
dùng chung nằm ở MySQL, Redis, file. Thử bằng file (chạy được với PHP CLI, không cần extension):

```php
<?php
// race.php: mỗi process tăng bộ đếm trong file 1000 lần, không khoá
declare(strict_types=1);

$file = __DIR__ . '/counter.txt';
for ($i = 0; $i < 1000; $i++) {
    $n = (int) file_get_contents($file);          // đọc
    file_put_contents($file, (string) ($n + 1));  // ghi
}
```

```sh
echo 0 > counter.txt
for i in $(seq 10); do php race.php & done; wait
cat counter.txt   # kỳ vọng 10000; thực tế nhỏ hơn và đổi theo từng lần chạy
```

Sửa bằng `flock()`, một khoá cấp hệ điều hành mà mọi process mở cùng file đều thấy:

```php
<?php
// race_fixed.php: critical section được bảo vệ bằng flock
declare(strict_types=1);

$fp = fopen(__DIR__ . '/counter.txt', 'c+');
for ($i = 0; $i < 1000; $i++) {
    flock($fp, LOCK_EX);                  // chờ tới khi không process nào giữ khoá
    rewind($fp);
    $n = (int) stream_get_contents($fp);
    ftruncate($fp, 0);
    rewind($fp);
    fwrite($fp, (string) ($n + 1));
    fflush($fp);                          // đẩy dữ liệu xuống trước khi nhả khoá
    flock($fp, LOCK_UN);
}
fclose($fp);
```

⚠️ `flock` là *advisory lock*: nó chỉ chặn những process cũng gọi `flock`, không chặn process ghi thẳng
vào file. Và nó chỉ có tác dụng trên **một máy**. Hai server thì phải dùng khoá ở DB hoặc Redis
(module 1.4, 2.1).

#### Ba tính chất cần đảm bảo

Đồng bộ đúng nghĩa là giữ được ba tính chất:

- *Atomicity*: một thao tác nhiều bước diễn ra như một khối, "tất cả hoặc không gì cả", không ai thấy
  hay chen vào trạng thái nửa chừng. `count++` không khoá hỏng tính chất này. Cùng ý tưởng ở DB gọi là
  transaction.
- *Visibility*: giá trị một thread ghi thì thread khác **chắc chắn nhìn thấy**. Không có đồng bộ,
  giá trị có thể nằm trong thanh ghi hay cache của một core, và compiler được phép giả định không ai
  khác đọc nó. Ví dụ kinh điển: một thread lặp `while (!stop) {}` không bao giờ thấy `stop = true`.
- *Ordering*: các lệnh không bị compiler hay CPU sắp xếp lại theo cách làm thread khác thấy trạng thái
  vô lý, ví dụ thấy cờ `ready = true` trước khi thấy dữ liệu đã được ghi.

Mutex cho cả ba: bên trong critical section là atomic, và mọi thứ ghi trước `Unlock` được bảo đảm
nhìn thấy bởi luồng `Lock` sau đó. Visibility và ordering là trọng tâm của module 3.1 (memory model,
happens-before). Với PHP-FPM, visibility và ordering ở mức bộ nhớ không phải lo, nhưng phiên bản ở mức
DB của chúng thì có: một transaction thấy gì của transaction khác là chuyện isolation level (module 2.2).

**Tóm tắt nhanh**
- Concurrency là cấu trúc (xử lý nhiều việc đan xen), parallelism là thực thi (chạy đồng thời thật
  trên nhiều core). PHP-FPM có cả hai ở mức process.
- Race condition: kết quả phụ thuộc thứ tự chạy. `count++` là read-modify-write ba bước, hai luồng chen
  nhau làm mất lần tăng.
- Critical section là đoạn truy cập tài nguyên chung, cần mutual exclusion; phải trùm **cả** check lẫn
  act, khoá từng bước riêng không đủ.
- Data race (cùng vùng nhớ, có ghi, không đồng bộ) khác race condition; `-race` chỉ bắt data race.
  PHP-FPM không có data race giữa request nhưng đầy race condition trên DB.
- Ba tính chất: atomicity, visibility, ordering.

**Nguồn**: [OSTEP: Concurrency: An Introduction](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-intro.pdf) ·
[OSTEP: Common Concurrency Problems](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf) ·
[Go blog: Concurrency is not parallelism](https://go.dev/blog/waza-talk)


---

### 1.2 Primitive đồng bộ cơ bản

Module này trả lời: mutex, read-write lock, semaphore, condition variable mỗi cái giải quyết bài toán
gì, chúng được dựng lên thế nào, và vì sao bounded buffer (queue có giới hạn) là mẫu bạn gặp lại ở mọi
tầng của hệ thống.

*Primitive đồng bộ* (synchronization primitive) là các công cụ nền do phần cứng, hệ điều hành hoặc
runtime cung cấp để điều phối nhiều luồng. Chúng giải hai loại bài toán khác nhau (OSTEP tách rõ):

1. **Loại trừ nhau** (mutual exclusion): không cho hai luồng cùng ở trong critical section. Dùng mutex,
   RW lock.
2. **Chờ nhau** (waiting/ordering): một luồng phải chờ tới khi luồng khác làm xong việc gì đó, ví dụ
   "buffer đã có phần tử". Dùng condition variable. Semaphore làm được cả hai.

#### Mutex

*Mutex* (mutual exclusion lock) là một biến có hai trạng thái: *free* (không ai giữ) hoặc *held* (đúng
một luồng giữ). `lock()` lấy khoá nếu nó đang free; nếu không thì luồng gọi bị chặn tới khi khoá được
nhả. `unlock()` trả khoá về free, và nếu có luồng đang chờ thì một trong số đó sẽ lấy được.

Mutex được dựng thế nào (OSTEP, chương Locks), đủ sâu để trả lời câu vặn:

1. Chỉ dùng một biến cờ với lệnh đọc/ghi thường thì **không** làm được: kiểm tra `flag == 0` rồi gán
   `flag = 1` chính là check-then-act, hai luồng cùng lọt qua.
2. Cần một lệnh phần cứng làm "đọc và ghi" trong một bước không thể chen: *test-and-set* (x86 là
   `xchg`), *compare-and-swap* (x86 là `cmpxchg`), hoặc cặp *load-linked/store-conditional* (ARM, MIPS,
   PowerPC). Với lệnh đó dựng được *spin lock*: lặp thử tới khi lấy được khoá.
3. Spin lock tốn CPU khi phải chờ lâu: luồng chờ đốt trọn time slice để kiểm tra một giá trị không đổi.
   Nên mutex thật cần hệ điều hành giúp: không lấy được thì đưa luồng vào hàng đợi và cho ngủ, nhả khoá
   thì đánh thức một luồng. Linux cung cấp *futex* cho việc này.
4. Nhiều cài đặt là *two-phase lock* (mutex của Go là một ví dụ): spin một chút phòng khi khoá sắp
   được nhả, không được thì ngủ. Khi không có tranh chấp, lock/unlock chỉ tốn vài lệnh atomic, không cần gọi vào kernel.

Hệ quả thực tế: mutex **không tranh chấp** rất rẻ. Cái đắt là **tranh chấp**: nhiều luồng cùng xếp hàng
chờ một khoá, và thời gian giữ khoá càng dài thì hàng càng dài.

Cách dùng đúng ở ba ngôn ngữ:

```go
// Go: Lock rồi defer Unlock ngay dòng sau, để mọi đường return đều nhả khoá
mu.Lock()
defer mu.Unlock()
balance -= amount
```

```java
// Java: synchronized tự nhả khi ra khỏi khối, kể cả khi có exception
synchronized (this) { balance -= amount; }

// ReentrantLock: tài liệu JDK khuyên lock() ngay trước try, unlock() là lệnh đầu tiên trong finally
lock.lock();
try {
    balance -= amount;
} finally {
    lock.unlock();
}
```

```php
<?php
// PHP: không có thread trong request, nên "mutex" là khoá dùng chung giữa các process/server
declare(strict_types=1);

use Illuminate\Support\Facades\Cache;

// Khoá phân tán qua cache store (Redis...): tự hết hạn sau 10 giây, chờ tối đa 5 giây để lấy
Cache::lock('report:daily', 10)->block(5, function (): void {
    // critical section: chỉ một process trên toàn cụm chạy đoạn này tại một thời điểm
});
// Không lấy được trong 5 giây thì ném Illuminate\Contracts\Cache\LockTimeoutException
```

Ngoài `Cache::lock`, PHP còn có `flock()` (một máy, module 1.1), `GET_LOCK()` của MySQL và
`pg_advisory_lock()` của Postgres (xem mục Advisory lock ở
[03 module 2.6](03-database-sql.md#26-lock-thực-dụng)), và `SELECT ... FOR UPDATE` khoá theo dòng.

Các quy tắc và cạm bẫy:

- Giữ khoá càng ngắn càng tốt. ⚠️ Không gọi I/O (DB, HTTP, file) khi đang giữ khoá trong bộ nhớ: API
  chậm 2 giây nghĩa là mọi luồng khác cần khoá đứng chờ 2 giây. Cùng quy tắc với transaction DB: không
  gọi API ngoài khi đang giữ `FOR UPDATE`.
- *Coarse-grained* (một khoá to cho mọi thứ) dễ đúng nhưng ít song song; *fine-grained* (mỗi cấu trúc
  một khoá) song song hơn nhưng nhiều khoá thì nhiều nguy cơ deadlock (module 1.3). Bắt đầu bằng khoá
  to, chỉ chia nhỏ khi đo thấy tranh chấp.
- *Reentrant* (tái nhập): luồng đang giữ khoá lấy lại chính khoá đó được, khoá đếm số lần lấy và chỉ
  thật sự nhả khi `unlock` đủ số lần. Java `synchronized` và `ReentrantLock` là reentrant.
  ⚠️ Go `sync.Mutex` **không** reentrant: cùng goroutine `Lock()` hai lần là tự chặn mình. Chương trình
  chỉ có một goroutine như vậy sẽ chết với `fatal error: all goroutines are asleep - deadlock!`. Lỗi
  hay gặp: method A khoá rồi gọi method B, B cũng khoá. Cách chữa quen thuộc là tách B thành hai bản:
  bản public tự khoá, bản private (quy ước tên như `bLocked`) giả định người gọi đã giữ khoá.
- *Chủ sở hữu*: với Java, chỉ thread đang giữ `ReentrantLock` mới `unlock()` được, thread khác gọi sẽ
  nhận `IllegalMonitorStateException`. ⚠️ Go thì khác: tài liệu `sync` ghi rõ mutex đang khoá "không
  gắn với goroutine cụ thể nào", goroutine này lock thì goroutine khác unlock được. Được phép không có
  nghĩa là nên làm; nó chỉ có nghĩa là Go không bắt lỗi giúp bạn.
- ⚠️ Go: "A Mutex must not be copied after first use". Copy một struct chứa `sync.Mutex` (truyền theo
  giá trị, method receiver không phải con trỏ) là copy luôn trạng thái khoá; hai bản sao không còn bảo
  vệ nhau. `go vet` (analyzer `copylocks`) bắt được lỗi này.

#### Read-write lock

*Read-write lock* (RW lock) phân biệt hai kiểu truy cập: cho phép **nhiều reader cùng lúc**, hoặc
**đúng một writer** (và khi đó không có reader nào). Ý tưởng: đọc không làm hỏng gì nhau, chỉ ghi mới
cần độc quyền.

Cách dựng đơn giản trong OSTEP cho thấy bản chất: một khoá `writelock`; reader **đầu tiên** vào thì lấy
`writelock`, reader **cuối cùng** ra thì nhả, ở giữa các reader khác chỉ tăng giảm một bộ đếm. Writer
phải lấy `writelock`, tức là phải chờ tới khi không còn reader nào.

Khi nào RW lock thật sự có lợi:

- Đọc nhiều hơn ghi rất nhiều, **và** đoạn đọc đủ dài để việc cho nhiều reader chạy song song bù được
  chi phí quản lý.
- ⚠️ Đoạn đọc ngắn (đọc một field, tra một map nhỏ) thì RW lock thường **chậm hơn** mutex thường, vì
  mỗi lần `RLock`/`RUnlock` vẫn phải cập nhật bộ đếm dùng chung, và bộ đếm đó thành điểm tranh chấp.
  OSTEP gọi lời khuyên này là Hill's Law: cái đơn giản và "ngốc" thường thắng. Đo trước khi đổi.

⚠️ *Writer starvation*: với cách dựng đơn giản ở trên, reader đến liên tục thì lúc nào cũng còn người
đang đọc, writer chờ mãi. Mỗi thư viện xử lý khác nhau, nên đọc tài liệu:

| | Go `sync.RWMutex` | Java `ReentrantReadWriteLock` |
|---|---|---|
| Writer đang chờ thì reader mới | **Bị chặn** tới khi writer lấy và nhả khoá, nên writer không bị bỏ đói | Mặc định (non-fair): thứ tự không xác định, có thể hoãn vô hạn một reader hay writer. Chế độ fair (`new ReentrantReadWriteLock(true)`): xấp xỉ theo thứ tự đến |
| Reader lấy lại read lock khi đang giữ (đệ quy) | ⚠️ Cấm: nếu có writer chen vào hàng giữa hai lần `RLock`, lần thứ hai bị chặn sau writer, writer lại chờ lần thứ nhất nhả, thành deadlock | Được (reentrant) |
| Nâng read lên write (*upgrade*) | Không hỗ trợ | Không hỗ trợ: thread đang giữ read lock mà gọi `writeLock().lock()` sẽ chờ chính nó, kẹt mãi |
| Hạ write xuống read (*downgrade*) | Không hỗ trợ | Được: giữ write lock, lấy read lock, rồi nhả write lock |

⚠️ Vì sao upgrade dễ deadlock, kể cả khi thư viện cho phép thử:

1. Reader A và reader B cùng giữ read lock.
2. Cả hai cùng muốn nâng lên write lock.
3. Write lock cần mọi reader nhả ra. A chờ B nhả, B chờ A nhả. Không ai chạy tiếp.

Muốn "đọc rồi quyết định ghi" thì lấy write lock ngay từ đầu. Cùng bài học đó ở DB: `SELECT ... FOR
SHARE` là read lock (khoá S), `FOR UPDATE` là write lock (khoá X). Hai transaction cùng `FOR SHARE` một
dòng rồi cùng `UPDATE` dòng đó chính là kịch bản upgrade ở trên, và InnoDB sẽ báo deadlock. Vì vậy mẫu
"đọc để sửa" luôn dùng `FOR UPDATE` (xem [03 module 2.6](03-database-sql.md#26-lock-thực-dụng)).

#### Semaphore

*Semaphore* (Dijkstra) là một số nguyên cùng hai thao tác atomic. Trong POSIX là `sem_wait()` và
`sem_post()`; Dijkstra gọi là P và V:

- `wait` (P, "lấy vé"): giảm giá trị đi 1; nếu kết quả âm thì luồng gọi ngủ chờ.
- `post` (V, "trả vé"): tăng giá trị lên 1; nếu có luồng đang chờ thì đánh thức một luồng.

Theo định nghĩa gốc của Dijkstra, khi giá trị âm thì độ lớn của nó bằng số luồng đang chờ. (Cài đặt
trên Linux không giữ bất biến này, giá trị không xuống dưới 0, nhưng hành vi nhìn từ ngoài như nhau.)

Hãy nghĩ theo kiểu N vé: semaphore giữ N vé (*permit*), mỗi luồng vào lấy một vé, ra thì trả, hết vé thì
phải chờ. **Giá trị khởi tạo quyết định semaphore dùng để làm gì**:

| Giá trị đầu | Tác dụng | Ví dụ |
|---|---|---|
| 1 | *Binary semaphore*, tương đương một lock | Bảo vệ critical section |
| 0 | Chờ một sự kiện (ordering): bên chờ gọi `wait` và ngủ tới khi bên kia `post` | Thread cha chờ thread con làm xong |
| N | *Throttling*: tối đa N luồng cùng làm một việc (OSTEP gọi đây là một dạng *admission control*) | Tối đa 10 kết nối cùng lúc tới API ngoài; giới hạn số luồng cùng chạy đoạn tốn RAM để máy không phải swap |

Khác mutex ở chỗ semaphore **không có khái niệm chủ sở hữu**: luồng này `wait`, luồng khác `post` là
cách dùng hợp lệ và thường gặp (chính là trường hợp giá trị đầu bằng 0). Tài liệu `Semaphore` của Java
cũng nói rõ luồng `release()` không cần là luồng đã `acquire()`.

Go có hai cách giới hạn "tối đa 10 lời gọi cùng lúc". Chương trình dưới đây đo số lời gọi chạy đồng thời
lớn nhất (`peak`) để kiểm chứng; cách 2 cần `go get golang.org/x/sync` trong một module:

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"golang.org/x/sync/semaphore"
)

var inFlight, peak atomic.Int64

// callAPI giả lập lời gọi API ngoài, đồng thời ghi nhận số lời gọi đang chạy cùng lúc.
func callAPI() {
	n := inFlight.Add(1)
	for {
		p := peak.Load()
		if n <= p || peak.CompareAndSwap(p, n) {
			break
		}
	}
	time.Sleep(20 * time.Millisecond)
	inFlight.Add(-1)
}

func main() {
	// Cách 1: buffered channel dung lượng 10 làm semaphore 10 vé
	sem := make(chan struct{}, 10)
	var wg sync.WaitGroup
	for range 100 {
		wg.Go(func() {
			sem <- struct{}{}        // lấy vé; chờ nếu 10 vé đã bị giữ
			defer func() { <-sem }() // trả vé
			callAPI()
		})
	}
	wg.Wait()
	fmt.Println("channel, peak =", peak.Load()) // channel, peak = 10

	// Cách 2: semaphore có trọng số, chờ được huỷ bằng context
	peak.Store(0)
	ws := semaphore.NewWeighted(10)
	ctx := context.Background()
	for range 100 {
		if err := ws.Acquire(ctx, 1); err != nil { // chỉ lỗi khi ctx bị huỷ: trả ctx.Err()
			break
		}
		wg.Go(func() {
			defer ws.Release(1)
			callAPI()
		})
	}
	wg.Wait()
	fmt.Println("x/sync, peak =", peak.Load()) // x/sync, peak = 10
}
```

Chi tiết của `x/sync/semaphore` đáng biết:

- `Acquire(ctx, n)` chặn tới khi đủ `n` vé hoặc `ctx` xong; thất bại thì trả `ctx.Err()` và không đổi
  gì. `TryAcquire(n)` không chặn, trả `bool`. `Release` nhiều hơn số đang giữ thì panic.
- Khác biệt so với channel: vé có **trọng số** (một việc nặng lấy 5 vé), và chờ có thể **huỷ** bằng
  context. Channel cũng huỷ được nếu viết `select` với `ctx.Done()`, nhưng dài hơn.
- Theo comment trong mã nguồn, người chờ được phục vụ theo thứ tự: một yêu cầu lớn đứng đầu hàng thì
  các yêu cầu nhỏ phía sau cũng phải chờ, dù còn đủ vé cho chúng. Làm vậy để yêu cầu lớn không bị bỏ đói.

Java: `Semaphore sem = new Semaphore(10);` rồi `sem.acquire(); try { callApi(); } finally {
sem.release(); }`. Constructor có thêm tham số `fair`.

Đối chiếu tầng hệ thống PHP: bạn hiếm khi viết semaphore, nhưng đang sống trong nó. `pm.max_children`
của PHP-FPM là số vé: request thứ `max_children + 1` phải xếp hàng chờ một worker rảnh. Số queue worker
chạy song song cũng vậy. Pool connection DB cũng vậy. Chọn số vé thế nào là chủ đề của module 2.4.

#### Condition variable

*Condition variable* (CV) là một hàng đợi các luồng đang chờ một **điều kiện** về trạng thái chương
trình trở thành đúng, ví dụ "buffer có phần tử" hay "thread con đã xong". Luồng làm điều kiện thành đúng
thì báo (*signal*) để đánh thức luồng chờ. Nếu không có CV, cách duy nhất để chờ là lặp kiểm tra liên tục
(*spin*), tốn CPU vô ích.

Hai thao tác (tên POSIX): `pthread_cond_wait(c, m)` và `pthread_cond_signal(c)`. Điểm tinh tế nằm ở
`wait`: nó nhận thêm mutex `m`, và phải được gọi khi **đang giữ** `m`. `wait` làm atomic hai việc: nhả
`m` và đưa luồng vào ngủ. Khi được đánh thức, nó **lấy lại** `m` trước khi trả về.

Vì sao phải có mutex và phải có biến trạng thái, OSTEP chỉ ra qua hai bản sai:

1. **Không có biến trạng thái** (chỉ `wait`/`signal` trần): nếu thread con chạy xong và `signal` trước
   khi thread cha kịp `wait`, tín hiệu rơi vào hư không, vì CV không nhớ gì cả. Thread cha `wait` sau đó
   và ngủ mãi. Nên luôn có một biến (ví dụ `done`) ghi lại sự thật, và CV chỉ là cơ chế ngủ/thức quanh
   biến đó.
2. **Không giữ mutex**: cha đọc `done == 0`, định đi ngủ, nhưng bị ngắt ngay trước khi gọi `wait`. Con
   chạy, gán `done = 1`, `signal` (không ai nghe). Cha chạy tiếp, gọi `wait`, ngủ mãi. Đây là
   *lost wakeup*, và mutex cùng tính atomic của `wait` tồn tại để chặn đúng khoảng hở này.

⚠️ Luôn viết `while (!cond) wait()`, không bao giờ `if (!cond) wait()`. Hai lý do:

- *Mesa semantics*: gần như mọi hệ thống cài đặt `signal` như một **gợi ý** rằng trạng thái đã đổi,
  không phải lời hứa rằng khi luồng được đánh thức chạy lại thì điều kiện vẫn đúng. Giữa lúc được báo
  và lúc thật sự lấy lại mutex, một luồng khác có thể đã chen vào và đổi điều kiện về sai. (Ngược lại là
  *Hoare semantics*: luồng được báo chạy ngay lập tức; mạnh hơn nhưng khó cài đặt, hầu như không ai dùng.)
- *Spurious wakeup*: một số cài đặt có thể đánh thức luồng dù không ai `signal`.

Tài liệu `sync.Cond` của Go ghi cùng mẫu đó: vì lúc chờ thì `c.L` không bị khoá, người gọi không được
giả định điều kiện đúng khi `Wait` trả về, và phải `Wait` trong vòng lặp `for !condition() { c.Wait() }`.

`signal` so với `broadcast`:

- `signal` đánh thức **một** luồng đang chờ, `broadcast` đánh thức **tất cả**.
- Dùng `broadcast` khi luồng báo không biết ai trong số người chờ cần được đánh thức. Ví dụ của OSTEP:
  bộ cấp phát bộ nhớ, luồng Ta chờ 100 byte, Tb chờ 10 byte, có ai đó giải phóng 50 byte. `signal` có
  thể đánh thức nhầm Ta (vẫn chưa đủ) và bỏ Tb ngủ. `broadcast` đánh thức cả hai, mỗi luồng tự kiểm tra
  lại điều kiện; cái giá là đánh thức thừa. Kiểu điều kiện này gọi là *covering condition*.
- ⚠️ OSTEP cảnh báo: nếu chương trình chỉ chạy đúng khi đổi `signal` thành `broadcast` mà bạn không
  hiểu vì sao, gần như chắc là có bug khác (thường là dùng chung một CV cho hai loại người chờ).

Ở từng ngôn ngữ:

- Java: mọi object có sẵn một "condition queue". Trong khối `synchronized (obj)` gọi `obj.wait()`,
  `obj.notify()`, `obj.notifyAll()`. Hoặc dùng `ReentrantLock.newCondition()` để có nhiều CV trên cùng
  một khoá, với `await()`/`signal()`/`signalAll()`.
- Go: `sync.Cond`, nhưng chính tài liệu khuyên với đa số trường hợp đơn giản thì nên dùng channel
  (`Broadcast` tương ứng với đóng channel, `Signal` tương ứng với gửi vào channel).

#### Producer–consumer và bounded buffer

Mô hình *producer–consumer*: một hay nhiều producer sinh việc và đặt vào buffer dùng chung, một hay
nhiều consumer lấy ra xử lý. *Bounded buffer* là buffer có sức chứa giới hạn: buffer đầy thì producer
phải chờ, rỗng thì consumer phải chờ. Bài toán do Dijkstra đặt ra, và nó có ở khắp nơi:

- `grep foo file.txt | wc -l`: kernel đặt một bounded buffer (pipe) giữa hai process. `grep` là
  producer, `wc` là consumer; `wc` đọc chậm thì `grep` bị chặn khi ghi.
- Web server đa luồng: thread nhận kết nối đẩy request vào work queue, các worker thread lấy ra xử lý.
- Queue job của Laravel, channel trong Go, `BlockingQueue` trong Java.

Buffer đầy buộc producer chậm lại theo tốc độ của consumer. Việc bên nhận chậm "đẩy ngược" lên bên gửi
như vậy gọi là *backpressure*, và đó là lý do chính để giới hạn kích thước. ⚠️ Queue không giới hạn
không có backpressure: consumer chậm thì queue cứ phình ra, độ trễ tăng dần, tới khi hết RAM (OOM).

Cài đặt đúng bằng mutex và **hai** condition variable (lưu thành `bb.go`, chạy `go run bb.go`):

```go
package main

import (
	"fmt"
	"sync"
)

// BoundedBuffer: queue có sức chứa cố định, bảo vệ bằng một mutex và hai condition variable.
type BoundedBuffer struct {
	mu       sync.Mutex
	notFull  *sync.Cond // producer chờ ở đây khi buffer đầy
	notEmpty *sync.Cond // consumer chờ ở đây khi buffer rỗng
	items    []int
	capacity int
}

func NewBoundedBuffer(capacity int) *BoundedBuffer {
	b := &BoundedBuffer{capacity: capacity}
	b.notFull = sync.NewCond(&b.mu)
	b.notEmpty = sync.NewCond(&b.mu)
	return b
}

func (b *BoundedBuffer) Put(v int) {
	b.mu.Lock()
	defer b.mu.Unlock()
	for len(b.items) == b.capacity { // while, không phải if
		b.notFull.Wait() // nhả mu và ngủ; khi thức dậy đã lấy lại mu
	}
	b.items = append(b.items, v)
	b.notEmpty.Signal() // chỉ đánh thức phía consumer
}

func (b *BoundedBuffer) Get() int {
	b.mu.Lock()
	defer b.mu.Unlock()
	for len(b.items) == 0 {
		b.notEmpty.Wait()
	}
	v := b.items[0]
	b.items = b.items[1:]
	b.notFull.Signal() // chỉ đánh thức phía producer
	return v
}

func main() {
	buf := NewBoundedBuffer(2)
	var wg sync.WaitGroup
	for p := range 2 { // 2 producer, mỗi producer đẩy 5 số
		wg.Go(func() {
			for i := range 5 {
				buf.Put(p*100 + i)
			}
		})
	}
	sum := 0
	for range 10 { // main là consumer, lấy đủ 10 số
		sum += buf.Get()
	}
	wg.Wait()
	fmt.Println(sum) // 520 = (0+1+2+3+4) + (100+101+102+103+104)
}
```

Hai bug kinh điển mà cài đặt trên tránh được (OSTEP dựng lại từng bước với hai consumer, một producer):

1. **Dùng `if` thay `while`**: producer đặt một phần tử và `signal`, consumer C1 được chuyển sang trạng
   thái sẵn sàng nhưng chưa chạy. Consumer C2 chen vào, lấy mất phần tử. C1 chạy, không kiểm tra lại,
   lấy từ buffer rỗng. Với code trên: index out of range, hoặc đọc rác.
2. **Chỉ một CV cho cả hai phía** (dù đã dùng `while`): C1 và C2 cùng ngủ chờ; producer đặt một phần
   tử, đánh thức C1, rồi tự ngủ vì buffer đầy. C1 lấy phần tử và `signal`, nhưng lại đánh thức nhầm C2
   (cùng một hàng đợi). C2 thấy rỗng, ngủ tiếp. Producer không bao giờ được đánh thức: cả ba cùng ngủ.
   Hai CV riêng (`notFull`, `notEmpty`) làm cho consumer không thể đánh thức nhầm consumer.

Cài đặt bằng semaphore dùng ba cái: `empty` khởi tạo bằng N (số chỗ trống), `full` khởi tạo bằng 0
(số phần tử), và `mutex` bằng 1. ⚠️ Bẫy mà OSTEP chỉ ra: nếu lấy `mutex` **trước** khi `wait(full)`,
consumer ngủ trong khi vẫn giữ `mutex`; producer muốn đặt phần tử lại phải chờ `mutex`. Hai bên chờ nhau:
deadlock. Mutex chỉ được bọc đúng đoạn đặt/lấy phần tử, còn `wait(empty)`/`wait(full)` nằm ngoài.

Trong code thật bạn gần như không tự viết bounded buffer, vì ngôn ngữ đã có:

- Go: `jobs := make(chan Job, 100)` là một bounded buffer đầy đủ. Gửi vào channel đầy thì chặn, nhận
  từ channel rỗng thì chặn.
- Java: `ArrayBlockingQueue` (luôn có sức chứa), `put()` chặn khi đầy, `take()` chặn khi rỗng.
  ⚠️ `LinkedBlockingQueue` tạo không truyền sức chứa thì sức chứa là `Integer.MAX_VALUE`, tức gần như
  không giới hạn. `Executors.newFixedThreadPool(n)` dùng chính queue đó, nên việc gửi vào nhanh hơn tốc
  độ xử lý sẽ tích tụ trong bộ nhớ không giới hạn (module 2.4).
- PHP/Laravel: queue trên Redis hay bảng `jobs` không chặn producer khi dài ra. Không có backpressure
  tự nhiên, nên phải tự theo dõi độ dài và độ trễ của queue (ví dụ bằng Horizon), và từ chối hoặc hoãn
  việc ở đầu vào khi queue quá tải.

#### So sánh các primitive

| Primitive | Mấy luồng vào cùng lúc | Có chủ sở hữu | Dùng khi | Tương đương ở tầng PHP/DB |
|---|---|---|---|---|
| Mutex | 1 | Java: có. Go: không bắt buộc | Bảo vệ một critical section | `Cache::lock`, `flock`, `GET_LOCK`, `FOR UPDATE` |
| RW lock | Nhiều reader hoặc 1 writer | Có | Đọc rất nhiều, ghi hiếm, đoạn đọc dài | `FOR SHARE` (S) và `FOR UPDATE` (X) |
| Semaphore | N | Không | Giới hạn số người dùng một tài nguyên; báo sự kiện | `pm.max_children`, số queue worker, pool connection |
| Condition variable | Không giới hạn gì, chỉ để chờ | Đi kèm một mutex | Ngủ chờ một điều kiện về trạng thái | Worker chờ job bằng blocking pop thay vì hỏi liên tục (tuỳ chọn `block_for` của Redis queue trong Laravel) |

**Tóm tắt nhanh**
- Mutex dựng trên lệnh atomic phần cứng (test-and-set, CAS) cộng hỗ trợ của OS để ngủ thay vì spin;
  không tranh chấp thì rẻ, tranh chấp mới đắt. Không làm I/O khi giữ khoá.
- Go `sync.Mutex` không reentrant và không được copy; Java `synchronized`/`ReentrantLock` reentrant.
- RW lock chỉ lợi khi đọc nhiều và đoạn đọc dài; không nâng read lên write (deadlock), ở DB cũng vậy
  (`FOR SHARE` rồi `UPDATE`).
- Semaphore là N vé, không có chủ; giá trị đầu 1 là lock, 0 là chờ sự kiện, N là throttling.
- Condition variable: luôn giữ mutex, luôn có biến trạng thái, luôn `while` không `if`; hai phía chờ
  khác nhau thì hai CV.
- Bounded buffer tạo backpressure; queue không giới hạn là OOM chờ ngày xảy ra.

**Nguồn**: [OSTEP: Locks](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf) ·
[OSTEP: Condition Variables](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-cv.pdf) ·
[OSTEP: Semaphores](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-sema.pdf) ·
[Go: x/sync/semaphore](https://pkg.go.dev/golang.org/x/sync/semaphore) ·
[Go: package sync](https://pkg.go.dev/sync) ·
[Java 25: ReentrantLock](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html) ·
[Java 25: ReentrantReadWriteLock](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantReadWriteLock.html)


---

### 1.3 Deadlock, livelock, starvation

Module này trả lời: vì sao hai luồng có thể chờ nhau mãi mãi, bốn điều kiện nào phải cùng có mặt, phá
điều kiện nào thì thực tế nhất, và ai phát hiện deadlock cho bạn (DB, JVM, Go runtime) còn ai thì không.
Phần DB chỉ tóm tắt; cơ chế khoá của InnoDB và cách đọc log chi tiết nằm ở
[03 module 2.6](03-database-sql.md#26-lock-thực-dụng) và [03 module 3.2](03-database-sql.md#32-lock-chuyên-sâu).

#### Deadlock là gì

*Deadlock* là khi hai hay nhiều luồng chờ nhau thành vòng tròn: mỗi luồng giữ một tài nguyên mà luồng
kế tiếp cần, nên không luồng nào chạy tiếp được, và tình trạng này không bao giờ tự gỡ. Dijkstra, người
đầu tiên mô tả nó bằng văn bản, gọi là "deadly embrace".

Dạng tối giản (OSTEP):

```
Thread 1:            Thread 2:
lock(L1);            lock(L2);
lock(L2);            lock(L1);
```

Code này **không phải lúc nào cũng** deadlock. Chỉ khi thread 1 lấy L1, rồi bị ngắt đúng lúc thread 2
lấy L2, thì cả hai mới kẹt. Vì vậy deadlock hay qua được test và chỉ lộ ra dưới tải thật. Vẽ thành đồ
thị phụ thuộc thì thấy một chu trình:

```
        giữ               chờ
  T1 ─────────▶ L1 ◀─────────── T2
   │                             │
   │ chờ                    giữ  │
   └──────────▶ L2 ◀─────────────┘

T1 giữ L1 và chờ L2; T2 giữ L2 và chờ L1: vòng T1 → L2 → T2 → L1 → T1.
```

Tái hiện chắc chắn bằng Go (chèn `Sleep` để nới rộng cửa sổ thời gian):

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

func main() {
	var a, b sync.Mutex
	var wg sync.WaitGroup
	wg.Go(func() {
		a.Lock()
		time.Sleep(10 * time.Millisecond)
		b.Lock() // chờ goroutine 2 nhả b
		fmt.Println("G1 xong")
		b.Unlock()
		a.Unlock()
	})
	wg.Go(func() {
		b.Lock()
		time.Sleep(10 * time.Millisecond)
		a.Lock() // chờ goroutine 1 nhả a
		fmt.Println("G2 xong")
		a.Unlock()
		b.Unlock()
	})
	wg.Wait()
}
// Output: fatal error: all goroutines are asleep - deadlock!  (kèm stack của từng goroutine)
```

Trong code lớn, deadlock hiếm khi hiện rõ như vậy. OSTEP nêu hai nguyên nhân:

- **Phụ thuộc vòng giữa các thành phần**: ví dụ trong kernel, hệ thống bộ nhớ ảo cần gọi file system
  để đọc một trang từ đĩa, còn file system lại cần xin một trang bộ nhớ từ hệ thống bộ nhớ ảo.
- **Đóng gói che mất thứ tự khoá**: `v1.addAll(v2)` trên `Vector` của Java phải khoá cả `v1` lẫn `v2`,
  theo một thứ tự nào đó bên trong. Thread khác gọi `v2.addAll(v1)` cùng lúc là có nguy cơ deadlock,
  mà người gọi không hề thấy chữ "lock" nào trong code của mình.

Deadlock không hiếm: trong nghiên cứu của Lu và cộng sự trên MySQL, Apache, Mozilla, OpenOffice,
31 trên 105 bug concurrency là deadlock.

Ví dụ trong DB, chuyển tiền hai chiều cùng lúc (A chuyển 100 từ tài khoản 1 sang 2, B chuyển 50 từ 2
sang 1; mỗi `UPDATE` giữ khoá X trên dòng tới khi transaction kết thúc):

| Bước | Session A (1 → 2) | Session B (2 → 1) | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `UPDATE accounts SET balance = balance - 100 WHERE id = 1;` | | A giữ khoá dòng 1 |
| 2 | | `START TRANSACTION;` `UPDATE accounts SET balance = balance - 50 WHERE id = 2;` | B giữ khoá dòng 2 |
| 3 | `UPDATE accounts SET balance = balance + 100 WHERE id = 2;` | | A chờ B nhả dòng 2 |
| 4 | | `UPDATE accounts SET balance = balance + 50 WHERE id = 1;` | Vòng chờ khép lại. InnoDB phát hiện ngay, rollback một bên (ví dụ B): `ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction` |
| 5 | (câu ở bước 3 chạy xong) `COMMIT;` | App retry cả transaction B | |

#### Bốn điều kiện Coffman

Coffman và cộng sự (1971) chỉ ra deadlock chỉ xảy ra khi có **đủ cả bốn** điều kiện. Thiếu một là không
thể deadlock, nên mọi kỹ thuật *phòng* deadlock (prevention) đều nhắm phá một điều kiện.

| Điều kiện | Nghĩa | Cách phá | Cái giá |
|---|---|---|---|
| Mutual exclusion | Tài nguyên mỗi lúc chỉ một bên giữ | Không dùng khoá: cấu trúc *lock-free* dựng trên CAS (module 3.2); hoặc gộp việc thành một thao tác atomic duy nhất | Lock-free rất khó viết đúng cho cấu trúc phức tạp |
| Hold and wait | Giữ khoá này trong lúc chờ khoá khác | Lấy mọi khoá cần dùng **một lần**, ngay từ đầu (OSTEP: bọc cả đợt lấy khoá bằng một khoá toàn cục `prevention`) | Phải biết trước mọi khoá cần dùng, trái với đóng gói; giữ khoá sớm hơn cần thiết nên giảm song song |
| No preemption | Không ai giật được khoá bên kia đang giữ | `tryLock`: lấy được L1 mà không lấy được L2 thì **tự nhả** L1 rồi thử lại từ đầu | Có thể thành livelock (nhóm cuối); phải hoàn tác mọi thứ đã làm giữa chừng |
| Circular wait | Các bên chờ nhau thành vòng | **Lấy khoá theo một thứ tự cố định** cho mọi luồng, ví dụ luôn khoá id nhỏ trước | Phải có kỷ luật trên toàn codebase; một chỗ làm sai là đủ |

Phá circular wait là cách thực tế và phổ biến nhất. Vài chi tiết:

- Thứ tự không cần là toàn phần. Linux dùng *thứ tự từng phần* (partial order): comment "Lock ordering"
  gần đầu file `mm/filemap.c` liệt kê các nhóm quy tắc kiểu "`i_rwsem` trước `i_mmap_rwsem`" (OSTEP
  trích bản cũ, khi khoá này còn tên `i_mutex`).
- Khi một hàm nhận hai khoá từ tham số, như `transfer(from, to)`, người gọi có thể truyền theo hai thứ
  tự. OSTEP gợi ý sắp theo địa chỉ của khoá; ở tầng ứng dụng thì sắp theo id: luôn khoá `min(from, to)`
  trước. (Nhớ xử lý trường hợp `from == to`.)

Về `tryLock` và "no preemption", cần nói chính xác: `tryLock` không giật khoá của ai, nó cho phép luồng
**tự** rút lui. OSTEP cũng lưu ý điểm này. Các cơ chế timeout ở tầng ứng dụng cũng cần hiểu đúng:

- ⚠️ `innodb_lock_wait_timeout` (mặc định 50 giây) hết hạn thì mặc định InnoDB chỉ rollback **câu lệnh
  đang chờ** và trả lỗi 1205. Transaction vẫn mở và **vẫn giữ** mọi khoá đã lấy. App phải tự rollback
  thì khoá mới được nhả (chi tiết và timeline ở [03 module 2.6](03-database-sql.md#26-lock-thực-dụng)).
- Khoá có TTL như `Cache::lock('key', 10)` là preemption thật: hết 10 giây thì khoá tự mất dù người giữ
  chưa xong. Nó chống được deadlock vĩnh viễn nhưng mở ra bug khác: hai bên cùng nghĩ mình đang giữ
  khoá (module 14 về distributed lock).

Ngoài phòng, còn hai hướng khác:

- *Tránh* (avoidance) bằng lập lịch, như thuật toán Banker của Dijkstra: biết trước luồng nào cần khoá
  nào để không bao giờ cho chạy cùng lúc những luồng có thể kẹt nhau. Chỉ dùng được khi biết trước mọi
  việc (ví dụ hệ nhúng), hầu như không gặp ở backend.
- *Phát hiện rồi gỡ* (detect and recover): cho phép deadlock xảy ra, định kỳ hoặc mỗi lần phải chờ thì
  tìm chu trình, rồi huỷ một bên. Đây đúng là cách DB làm (nhóm sau).

Một quy tắc nữa từ thực tế: không gọi *code lạ* (callback, hook, event listener, method có thể bị
override) khi đang giữ khoá. Code đó có thể lấy thêm khoá khác và tạo ra vòng chờ mà bạn không nhìn
thấy, đúng như ví dụ `Vector.addAll`.

#### Phát hiện deadlock

Công cụ lý thuyết là *wait-for graph*: mỗi luồng là một đỉnh, cạnh T1 → T2 nghĩa là "T1 đang chờ tài
nguyên T2 giữ". Có chu trình nghĩa là có deadlock. Mỗi môi trường làm việc này khác nhau:

**MySQL InnoDB**

1. Mỗi khi một transaction phải chờ khoá, InnoDB tìm chu trình ngay (`innodb_deadlock_detect`, mặc
   định bật). Phát hiện gần như tức thì, không phải đợi timeout.
2. Chọn *victim* để rollback: InnoDB cố chọn transaction "nhỏ", đo bằng số dòng đã insert, update,
   delete. Victim bị rollback **cả transaction** và nhận lỗi 1213, SQLSTATE `40001`.
3. `SHOW ENGINE INNODB STATUS\G`, mục `LATEST DETECTED DEADLOCK`, chỉ giữ deadlock **gần nhất**. Bật
   `innodb_print_all_deadlocks` (mặc định tắt) để ghi mọi deadlock vào error log. Đếm tổng số deadlock:
   `SELECT count FROM information_schema.INNODB_METRICS WHERE name = 'lock_deadlocks';`.

Khung của mục `LATEST DETECTED DEADLOCK` (lược từ ví dụ trong tài liệu MySQL 8.4, bỏ các dòng hex):

```
*** (1) TRANSACTION:
TRANSACTION 43260, ACTIVE 186 sec starting index read
UPDATE Animals SET value=30 WHERE name='Aardvark'
*** (1) HOLDS THE LOCK(S):
RECORD LOCKS ... index PRIMARY of table `test`.`Birds` ... lock mode S locks rec but not gap
*** (1) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS ... index PRIMARY of table `test`.`Animals` ... lock_mode X locks rec but not gap waiting
*** (2) TRANSACTION:
TRANSACTION 43261, ACTIVE 209 sec starting index read
UPDATE Birds SET value=40 WHERE name='Buzzard'
*** (2) HOLDS THE LOCK(S):
RECORD LOCKS ... index PRIMARY of table `test`.`Animals` ... lock mode S locks rec but not gap
*** (2) WAITING FOR THIS LOCK TO BE GRANTED:
RECORD LOCKS ... index PRIMARY of table `test`.`Birds` ... lock_mode X locks rec but not gap waiting
*** WE ROLL BACK TRANSACTION (2)
```

Cách đọc: với mỗi transaction, xem **câu lệnh đang chạy**, nó **giữ** khoá gì trên index nào của bảng
nào (`HOLDS`), và nó **chờ** khoá gì (`WAITING FOR`). Nối lại: (1) giữ S trên Birds, chờ X trên
Animals; (2) giữ S trên Animals, chờ X trên Birds, thành vòng. Dòng cuối cho biết victim. Ví dụ này
cùng gốc với mẫu "`FOR SHARE` rồi `UPDATE`" ở module 1.2 (giữ khoá S rồi xin khoá X), chỉ khác là hai
khoá S nằm trên hai dòng khác nhau chứ không phải cùng một dòng. ⚠️ Log chỉ cho câu lệnh **đang chạy** của mỗi
transaction, không cho câu đã lấy khoá trước đó; phải tự đối chiếu với code để biết khoá được lấy ở
đâu. Các kiểu khoá (`locks rec but not gap`, gap lock, insert intention) giải thích ở
[03 module 3.2](03-database-sql.md#32-lock-chuyên-sâu).

**PostgreSQL**: transaction phải chờ khoá quá `deadlock_timeout` (mặc định 1 giây) thì Postgres mới
chạy kiểm tra chu trình, vì kiểm tra tốn kém mà đa số lần chờ tự hết. Có deadlock thì huỷ một bên với
`ERROR: deadlock detected`, SQLSTATE `40P01`.

**Java**: `jstack <pid>` hoặc `jcmd <pid> Thread.print` in *thread dump* (stack và trạng thái của mọi
thread). Nếu có deadlock, cuối dump có mục `Found one Java-level deadlock:` liệt kê thread nào chờ khoá
nào, đang bị thread nào giữ. Trong code, `ThreadMXBean.findDeadlockedThreads()` làm việc tương tự. JVM
**không tự gỡ**: các thread kẹt mãi tới khi restart.

**Go**: runtime chỉ báo `fatal error: all goroutines are asleep - deadlock!` khi **mọi** goroutine đều
bị chặn. ⚠️ Service thật luôn còn goroutine khác đang sống, ví dụ HTTP server chờ kết nối, nên một nhóm
goroutine kẹt nhau sẽ **không được báo gì**. Đã thử: thêm `go http.ListenAndServe(...)` vào chương trình
tự `Lock()` hai lần thì nó treo im lặng thay vì crash. Để điều tra, xem stack mọi goroutine qua endpoint
`/debug/pprof/goroutine?debug=2` của `net/http/pprof`, hoặc gửi `SIGQUIT` (`kill -QUIT <pid>`) để
runtime in stack mọi goroutine rồi thoát.

#### Deadlock trong DB và cách sửa

Tài liệu MySQL nói thẳng: deadlock "không nguy hiểm", trừ khi xảy ra thường tới mức một số transaction
không chạy được, và **dù logic đúng, app vẫn phải xử lý trường hợp transaction cần chạy lại**. Ba việc cần làm:

1. **Khoá theo thứ tự cố định**, sắp id trước khi khoá, để mọi transaction đi cùng một chiều:

   ```sql
   -- Chuyển tiền: luôn khoá id nhỏ trước, bất kể chiều chuyển
   START TRANSACTION;
   SELECT id FROM accounts WHERE id IN (1, 2) ORDER BY id FOR UPDATE;
   UPDATE accounts SET balance = balance - 100 WHERE id = 2;
   UPDATE accounts SET balance = balance + 100 WHERE id = 1;
   COMMIT;
   ```

   `FOR UPDATE` lấy khoá theo thứ tự quét; quét khoá chính theo `id` tăng dần thì dòng 1 luôn bị khoá
   trước dòng 2, nên transaction chuyển chiều ngược lại phải chờ ngay ở bước đầu thay vì tạo vòng.
   Cùng ý đó trong Laravel:

   ```php
   <?php
   declare(strict_types=1);

   use Illuminate\Support\Facades\DB;

   function transfer(int $fromId, int $toId, int $amount): void
   {
       DB::transaction(function () use ($fromId, $toId, $amount): void {
           // Khoá cả hai dòng theo id tăng dần, bất kể chiều chuyển
           $accounts = DB::table('accounts')
               ->whereIn('id', [$fromId, $toId])
               ->orderBy('id')
               ->lockForUpdate()
               ->get()
               ->keyBy('id');

           if ($accounts[$fromId]->balance < $amount) {
               throw new RuntimeException('Không đủ số dư'); // rollback, không retry
           }
           DB::table('accounts')->where('id', $fromId)->decrement('balance', $amount);
           DB::table('accounts')->where('id', $toId)->increment('balance', $amount);
       }, attempts: 3); // deadlock thì chạy lại cả closure, tối đa 3 lần
   }
   ```

2. **Transaction ngắn**, commit ngay khi xong; có **index** cho `WHERE` của `UPDATE` và `FOR UPDATE`
   để khoá ít bản ghi nhất; bớt locking read khi không thật cần. Đây là các gợi ý trong trang
   "How to Minimize and Handle Deadlocks" của MySQL.
3. **Retry**, vì không loại bỏ hoàn toàn được. Laravel: `DB::transaction($closure, attempts: 3)` chạy
   lại toàn bộ closure khi gặp deadlock; hết lượt thì ném exception. ⚠️ Closure có thể chạy nhiều lần,
   nên chỉ đặt thao tác DB bên trong; gửi mail hay gọi API trong đó thì mỗi lần retry làm thêm một lần
   (chi tiết và các lỗi Laravel coi là "lỗi concurrency" ở
   [03 module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel)).

⚠️ Một kiểu deadlock DB không có "hai dòng ngược thứ tự": hai session cùng `SELECT ... FOR UPDATE` một
id **chưa tồn tại** rồi cùng `INSERT`, do gap lock ở REPEATABLE READ. Xem nhóm Deadlock ở
[03 module 2.6](03-database-sql.md#26-lock-thực-dụng).

#### Deadlock với channel trong Go

*Unbuffered channel* (`make(chan T)`) không có chỗ chứa: lệnh gửi chặn tới khi có người nhận, lệnh nhận
chặn tới khi có người gửi. Nó là điểm hẹn giữa hai goroutine. Vì vậy mọi deadlock của khoá đều có phiên
bản channel, cộng thêm vài kiểu riêng:

```go
func main() {
	ch := make(chan int) // unbuffered
	ch <- 1              // không có goroutine nào nhận: main kẹt ngay tại đây
	fmt.Println(<-ch)
}
// Output: fatal error: all goroutines are asleep - deadlock!
//         goroutine 1 [chan send]: ...
```

Các kiểu hay gặp:

- Gửi vào unbuffered channel mà không ai nhận, như trên.
- `for v := range ch` mà bên gửi quên `close(ch)`: vòng lặp chờ mãi phần tử tiếp theo.
- Gửi hoặc nhận trên channel `nil` (khai báo mà chưa `make`) thì chặn vĩnh viễn.
- Giữ mutex trong lúc gửi vào channel, trong khi bên nhận cần chính mutex đó.

⚠️ Nguy hiểm hơn deadlock toàn chương trình là *goroutine leak*: một goroutine kẹt mãi, giữ bộ nhớ mãi,
và runtime không báo gì vì chương trình vẫn đang chạy. Mẫu kinh điển là timeout:

```go
func query(ctx context.Context) (int, error) {
	ch := make(chan int) // ⚠️ unbuffered
	go func() { ch <- slowQuery() }()
	select {
	case v := <-ch:
		return v, nil
	case <-ctx.Done():
		// Hàm trả về, không còn ai đọc ch. Goroutine ở trên kẹt mãi ở lệnh gửi: leak.
		return 0, ctx.Err()
	}
}
```

Mỗi request timeout để lại một goroutine chết, số goroutine tăng dần tới khi hết RAM. Sửa bằng
`make(chan int, 1)`: goroutine gửi được vào buffer rồi thoát dù không ai đọc. Kiểm tra leak bằng cách
theo dõi `runtime.NumGoroutine()` hoặc goroutine profile theo thời gian.

#### Livelock và starvation

*Livelock*: các luồng **vẫn đang chạy**, tốn CPU, đổi trạng thái liên tục, nhưng không luồng nào tiến
được. Ví dụ đời thường: hai người gặp nhau ở hành lang, cùng né sang trái, rồi cùng né sang phải, cứ
thế mãi. Ví dụ trong code chính là cách phá "no preemption" ở trên (OSTEP):

```
top:
  lock(L1);
  if (trylock(L2) fails) {
      unlock(L1);
      goto top;   // hai thread lấy khoá ngược thứ tự có thể cứ cùng nhả, cùng thử lại, mãi mãi
  }
```

Cách sửa: *backoff ngẫu nhiên*, mỗi bên chờ một khoảng ngẫu nhiên trước khi thử lại để phá sự đồng
bộ. Ở backend, livelock thường mang dạng *retry storm*: nhiều request cùng gặp deadlock hoặc xung đột
optimistic lock, cùng retry **ngay lập tức**, lại cùng đụng nhau. Retry nên có *exponential backoff*
(chờ tăng dần: 50 ms, 100 ms, 200 ms...) cộng *jitter* (thêm một khoảng ngẫu nhiên) và giới hạn số lần.

*Starvation* (bỏ đói): hệ thống nhìn chung vẫn tiến triển, nhưng **một** luồng cụ thể mãi không tới lượt
được lấy khoá hay được chạy. Các nguồn gây starvation:

- Khoá không công bằng: spin lock test-and-set không bảo đảm thứ tự, một luồng có thể thua mãi. OSTEP
  đưa ra *ticket lock* dựng trên fetch-and-add: mỗi luồng lấy một số thứ tự như ở quầy ngân hàng, nên ai
  đến trước được phục vụ trước và ai cũng tới lượt.
- RW lock ưu tiên reader: writer chờ mãi (module 1.2).
- Ưu tiên queue: worker Laravel chạy `php artisan queue:work --queue=high,low` xử lý queue theo thứ tự
  liệt kê, nên nếu `high` không bao giờ cạn thì job ở `low` không bao giờ chạy. Cần worker riêng cho
  `low`, hoặc theo dõi độ trễ của từng queue.
- Ưu tiên luồng: luồng ưu tiên thấp giữ khoá mà luồng ưu tiên cao cần (*priority inversion*, module 3.3).

*Fair lock* chống starvation bằng cách cấp khoá theo thứ tự đến. Java: `new ReentrantLock(true)`. Tài
liệu JDK nêu rõ cái giá và giới hạn:

- Throughput tổng thể thấp hơn, "thường là thấp hơn nhiều", đổi lại độ trễ lấy khoá ít dao động hơn và
  bảo đảm không có starvation.
- Fair lock không làm cho **việc lập lịch thread** công bằng: một thread vẫn có thể lấy khoá nhiều lần
  liên tiếp trong khi thread khác chưa được CPU chạy.
- ⚠️ `tryLock()` không có timeout thì **bỏ qua** fairness: khoá đang rảnh là lấy được ngay, dù có thread
  khác đang xếp hàng.

Phân biệt ba hiện tượng:

| | Deadlock | Livelock | Starvation |
|---|---|---|---|
| Trạng thái các luồng | Bị chặn, đứng chờ | Đang chạy | Hầu hết chạy bình thường, một số chờ mãi |
| CPU | Thấp (mọi người ngủ) | Cao (bận rộn vô ích) | Bình thường |
| Hệ thống có tiến triển | Không (với các luồng trong vòng) | Không | Có, trừ luồng bị bỏ đói |
| Tự hết không | Không, phải có bên ngoài gỡ (DB rollback victim, restart) | Có thể, nếu thời điểm tình cờ lệch nhau | Có thể, khi tải giảm |
| Cách chữa chính | Khoá theo thứ tự, timeout, retry | Backoff ngẫu nhiên | Fair lock, ticket, tách hàng đợi |

**Tóm tắt nhanh**
- Deadlock cần đủ bốn điều kiện Coffman: mutual exclusion, hold and wait, no preemption, circular wait.
  Cách thực tế nhất là phá circular wait: mọi luồng lấy khoá theo cùng một thứ tự (id nhỏ trước).
- InnoDB phát hiện ngay và rollback cả transaction nhỏ hơn với lỗi 1213; Postgres kiểm tra sau
  `deadlock_timeout` (1 giây) với lỗi 40P01. App **luôn** phải retry cả transaction.
- Lock wait timeout (1205) của InnoDB mặc định chỉ rollback câu lệnh, transaction vẫn giữ khoá.
- Go chỉ báo deadlock khi mọi goroutine cùng kẹt; service thật thì treo im lặng hoặc leak goroutine.
  JVM có `jstack` phát hiện nhưng không tự gỡ.
- Livelock là bận mà không tiến, chữa bằng backoff có jitter; starvation là một luồng mãi không tới
  lượt, chữa bằng fair lock hoặc tách hàng đợi, đổi lại throughput thấp hơn.

**Nguồn**: [OSTEP: Common Concurrency Problems](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-bugs.pdf) ·
[OSTEP: Locks](https://pages.cs.wisc.edu/~remzi/OSTEP/threads-locks.pdf) ·
[MySQL 8.4: Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html) ·
[MySQL 8.4: Deadlock Detection](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-detection.html) ·
[MySQL 8.4: An InnoDB Deadlock Example](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-example.html) ·
[MySQL 8.4: How to Minimize and Handle Deadlocks](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html) ·
[Laravel: Handling Deadlocks](https://laravel.com/docs/13.x/database#handling-deadlocks) ·
[Java 25: ReentrantLock](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html)

---

### 1.4 Race condition trong ứng dụng web

Module này trả lời: race condition trông thế nào trong một app Laravel chạy trên PHP-FPM và nhiều
server, vì sao "đã bọc trong transaction" hay "đã có mutex" vẫn chưa đủ, và có những cách sửa nào,
mỗi cách trả giá gì.

#### Code sai kinh điển

Ở module 1.1, race condition là chuyện giữa các thread. Trong app web, các "luồng" tranh nhau là
**các request**. Mỗi request PHP-FPM chạy trong một worker process riêng, không chung biến nào với
request khác ([05-php-laravel.md, module 2.2](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing)).
Dữ liệu dùng chung duy nhất là thứ nằm ngoài process: MySQL, Redis, file, API ngoài. Vì vậy race
condition ở tầng web gần như luôn là race condition **trên DB hoặc Redis**, và chỉ DB hoặc Redis mới
chặn được nó.

Đoạn code dưới đây qua được mọi test chạy tuần tự:

```php
$product = Product::find($id);          // SELECT stock ... (đọc)
if ($product->stock > 0) {              // quyết định ở app
    $product->stock -= 1;               // tính ở app
    $product->save();                   // UPDATE products SET stock = 0 ... (ghi số cố định)
    Order::create([...]);
}
```

Timeline khi tồn kho còn 1 và hai khách bấm "Mua" cùng lúc:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `SELECT stock FROM products WHERE id = 7;` | | A thấy 1 |
| 2 | | `SELECT stock FROM products WHERE id = 7;` | B cũng thấy 1, vì A chưa ghi |
| 3 | `1 > 0`, `UPDATE products SET stock = 0 WHERE id = 7;` | | |
| 4 | | `1 > 0`, `UPDATE products SET stock = 0 WHERE id = 7;` | Ghi đè cùng giá trị 0, không lỗi |
| 5 | `INSERT INTO orders ...` | `INSERT INTO orders ...` | Hai đơn, một món hàng |

Khoảng hở giữa bước 1 và bước 3 chỉ vài mili giây, nên khi test bằng tay gần như không bao giờ thấy
lỗi. Dưới tải thật (flash sale, bot, người dùng bấm đúp) thì lỗi xuất hiện đều đặn.

⚠️ Bọc đoạn code trên trong `DB::transaction()` **không sửa được**. Ở Repeatable Read mặc định của
MySQL, `SELECT` thường đọc từ snapshot và không khoá gì; bước 4 của B chỉ phải chờ khoá dòng của A,
rồi vẫn ghi `stock = 0` như cũ. Transaction đảm bảo "mỗi request hoặc xong hết hoặc không gì cả",
không đảm bảo giá trị đã đọc còn đúng lúc ghi. Timeline đầy đủ ở
[03-database-sql.md, module 1.3](03-database-sql.md#13-transaction-cơ-bản) (mục "Hai bẫy"), cơ chế
snapshot ở module 2.2 bên dưới.

#### Check-then-act

Đoạn code trên là một trường hợp của mẫu *check-then-act* ⚠️: kiểm tra một điều kiện, rồi hành động
dựa trên kết quả kiểm tra, trong hai bước tách rời. Bất kỳ request nào chen vào giữa hai bước đều có
thể làm điều kiện sai đi mà request đầu không biết. Kleppmann (DDIA ch.7) mô tả cùng cấu trúc cho
write skew: một câu `SELECT` kiểm tra điều kiện, app quyết định, rồi app ghi, và chính câu ghi làm
thay đổi kết quả của câu kiểm tra.

Một khi đã nhận ra mẫu này, bạn sẽ thấy nó ở khắp nơi:

| Nghiệp vụ | Check | Act | Hậu quả khi race |
|---|---|---|---|
| Đăng ký | Email chưa tồn tại | `INSERT` user | Hai tài khoản cùng email |
| Coupon | User chưa dùng coupon này | Ghi lượt dùng, giảm giá | Một coupon dùng hai lần |
| Ví | Số dư đủ | Trừ tiền | Số dư âm |
| Đặt chỗ | Slot còn trống | Tạo booking | Hai người một ghế |
| Giới hạn | Coupon còn lượt (dưới 100 lượt) | Tăng số lượt | Lượt thứ 101, 102 lọt qua |

Nguyên tắc sửa: **gộp check và act thành một thao tác atomic** ở nơi dữ liệu thực sự nằm. "Atomic" ở
đây nghĩa là DB hoặc Redis tự làm cả kiểm tra lẫn ghi trong một bước mà không request nào chen vào
được. Các công cụ có sẵn:

1. `UPDATE ... WHERE <điều kiện>` rồi kiểm tra số dòng bị ảnh hưởng. InnoDB khoá dòng và đánh giá
   `WHERE` trên bản mới nhất, nên hai câu đồng thời được xếp hàng: câu sau thấy kết quả của câu trước.
2. Unique constraint: DB từ chối `INSERT` thứ hai với lỗi duplicate key (MySQL error 1062, SQLSTATE
   `23000`; Postgres SQLSTATE `23505`).
3. `INSERT ... ON DUPLICATE KEY UPDATE` (MySQL) hoặc `INSERT ... ON CONFLICT` (Postgres): "chưa có thì
   tạo, có rồi thì cập nhật" trong một câu ([03-database-sql.md, module 2.4](03-database-sql.md#24-sql-nâng-cao)).
4. Redis `SET key value NX EX 30`: chỉ set nếu key chưa có, kèm hạn 30 giây. Lệnh trả `OK` cho đúng
   một bên, bên kia nhận `nil`.

Ví dụ giới hạn 100 lượt dùng coupon, viết dạng atomic:

```sql
UPDATE coupons SET used_count = used_count + 1
WHERE id = 5 AND used_count < max_uses;
-- affected rows = 1: được dùng; = 0: hết lượt (hoặc coupon không tồn tại)
```

⚠️ Eloquent có hai hàm trông atomic nhưng không phải: `firstOrCreate()` và `updateOrCreate()` chạy
`SELECT` rồi mới `INSERT` ở app, tức vẫn là check-then-act. Ở Laravel bản mới, khi `SELECT` không
thấy dòng, `firstOrCreate()` gọi `createOrFirst()`: thử `INSERT`, gặp lỗi unique thì `SELECT` lại dòng
mà request khác vừa chèn (`updateOrCreate()` đi qua `firstOrCreate()` nên cũng vậy). Cơ chế đó chỉ an
toàn khi có unique index đỡ phía dưới; không có unique index thì vẫn sinh dòng trùng
([03-database-sql.md, module 2.4](03-database-sql.md#24-sql-nâng-cao)).

#### Các cách trừ tồn kho

Vài thuật ngữ dùng trong bảng:

- *Affected rows*: số dòng câu `UPDATE` thực sự thay đổi. Trong Laravel, `DB::update()` và
  `->update()`, `->decrement()` của query builder trả về con số này.
- *Pessimistic lock*: khoá dòng ngay lúc đọc bằng `SELECT ... FOR UPDATE` (Laravel `lockForUpdate()`),
  người đến sau phải chờ tới khi transaction đầu commit.
- *Optimistic lock*: không khoá, lúc ghi mới kiểm tra "dòng có bị ai đổi từ lúc mình đọc không" bằng
  cột `version` (module 2.1).
- *Distributed lock*: khoá nằm ở một hệ thống ngoài mà mọi server cùng thấy, ví dụ Redis qua
  `Cache::lock()` của Laravel.
- Redis `DECR` giảm một số nguyên atomic. *Lua script* chạy trên Redis như một lệnh duy nhất: trong
  lúc script chạy, Redis không xử lý lệnh của client khác.

| Cách | Ưu | Nhược, cạm bẫy |
|---|---|---|
| Atomic update `SET stock = stock - 1 WHERE id = ? AND stock > 0` | Một câu, một round-trip, khoá dòng vài mili giây. Chịu được tranh chấp cao nhất | Chỉ gói được logic diễn đạt được trong SQL. ⚠️ Quên kiểm tra affected rows là mất tác dụng |
| Pessimistic `SELECT ... FOR UPDATE` trong transaction | Logic nhiều bước tuỳ ý ở app (hạn mức mỗi khách, combo) | Các request xếp hàng, dễ deadlock khi khoá nhiều dòng. ⚠️ Thiếu transaction thì khoá nhả ngay; không gọi API ngoài khi đang giữ khoá |
| Optimistic, cột `version` | Không giữ khoá, không giữ connection | Tranh chấp cao thì đa số lần thử thất bại, tốn round-trip |
| Distributed lock (Redis) | Điều phối được cả việc không nằm trong DB (gọi API ngoài, sinh file) | Thêm một hệ thống phải vận hành. Lock có TTL, có thể hết hạn khi việc chưa xong ([14](../14-distributed-systems.md)) |
| Queue xử lý tuần tự theo `product_id` | Không còn tranh chấp: mỗi sản phẩm chỉ một worker xử lý tại một thời điểm. Hấp thụ được đỉnh tải | Bất đồng bộ: người dùng không biết ngay mua được hay không. Phức tạp hơn |
| 🟡 Redis `DECR`/Lua trước, ghi DB sau | Rất nhanh, Redis chịu tải lớn hơn một dòng MySQL bị khoá | Redis và DB có thể lệch nhau (Redis trừ xong thì app chết), cần job đối soát |

Code PHP của ba cách đầu (atomic, pessimistic, optimistic) đã có đủ ở
[03-database-sql.md, module 2.6](03-database-sql.md#26-lock-thực-dụng). Cách atomic trong Laravel viết
gọn bằng query builder:

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;

function reserve(int $productId): bool
{
    // Sinh: UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0
    $affected = DB::table('products')
        ->where('id', $productId)
        ->where('stock', '>', 0)
        ->decrement('stock');

    return $affected === 1;   // 0: hết hàng
}
```

⚠️ `$product->decrement('stock')` trên một model đã load cũng sinh `stock = stock - 1` (atomic),
nhưng không có điều kiện `stock > 0`, nên hai request vẫn trừ được xuống âm. Điều kiện phải nằm trong
`WHERE`, không phải trong `if` ở PHP.

Cách Redis cho flash sale: nạp tồn kho vào Redis trước giờ mở bán, rồi mỗi request chạy một Lua script
"kiểm tra đủ hàng thì trừ":

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\Redis;

function reserveInRedis(int $productId, int $qty): bool
{
    $left = Redis::eval(<<<'LUA'
        local stock = tonumber(redis.call('GET', KEYS[1]) or '-1')
        if stock < tonumber(ARGV[1]) then
            return -1
        end
        return redis.call('DECRBY', KEYS[1], ARGV[1])
    LUA, 1, "stock:{$productId}", $qty);

    return $left >= 0;   // -1: không đủ hàng hoặc key chưa được nạp
}
```

Check và act nằm trong cùng một script nên không request nào chen vào giữa được. Sau khi Redis trả
thành công, đơn hàng được ghi vào DB (thường qua queue). Vì hai hệ thống không cùng một transaction,
cần một job đối soát định kỳ so tồn kho Redis với DB.

Cách queue: thay vì để 1000 request cùng tranh một dòng, request chỉ đẩy yêu cầu vào queue, và worker
xử lý tuần tự từng yêu cầu cho cùng một sản phẩm. Trong Laravel có thể dùng job middleware
`WithoutOverlapping($productId)`: job cùng loại và cùng key với một job đang chạy sẽ bị trả lại queue để chạy sau. Tài liệu
Laravel lưu ý mỗi lần bị trả lại vẫn tính là một lần thử, nên phải tăng số lần thử của job. Queue có
thể giao một message hai lần, nên worker vẫn phải idempotent (module
[2.3](#23-double-submit-idempotency-key)).

Chọn cách nào: atomic update trước; logic không gói được vào một câu SQL thì pessimistic cho thao tác
ngắn; optimistic khi thao tác kéo dài qua lần tương tác của người dùng; Redis hoặc queue khi một dòng
DB không chịu nổi mức tranh chấp.

#### Unique constraint làm lưới an toàn

Dù đã có lock, queue hay Lua script, vẫn đặt ràng buộc ở DB cho những bất biến quan trọng, ví dụ
`UNIQUE(user_id, coupon_id)` trên bảng lượt dùng coupon, `UNIQUE(email)` trên bảng user. Lý do:

- Distributed lock có thể hết hạn giữa chừng, khi đó hai process cùng nghĩ mình đang giữ khoá.
- Không phải mọi đường ghi đều đi qua code có lock: lệnh artisan, script migrate dữ liệu, `tinker`,
  một service khác ghi thẳng vào bảng.
- DB là nơi duy nhất nhìn thấy **mọi** lần ghi, nên chỉ ràng buộc ở DB mới đúng trong mọi trường hợp.

Timeline "dùng coupon" khi có unique constraint:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `SELECT 1 FROM coupon_usages WHERE user_id = 9 AND coupon_id = 5;` | | Không có, qua |
| 2 | | Cùng câu `SELECT` | Không có, qua (A chưa ghi) |
| 3 | `INSERT INTO coupon_usages (user_id, coupon_id) VALUES (9, 5);` | | Thành công |
| 4 | | Cùng câu `INSERT` | Lỗi duplicate key (MySQL 1062). Không có unique thì coupon đã dùng hai lần |

Bước 1 và 2 vẫn hữu ích để trả thông báo đẹp cho trường hợp thường gặp, nhưng hàng rào thật là bước
4. Code phải bắt lỗi trùng key và biến nó thành kết quả nghiệp vụ, không để thành lỗi 500:

```php
<?php
declare(strict_types=1);

use App\Models\CouponUsage;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\JsonResponse;

function redeem(int $userId, int $couponId): JsonResponse
{
    try {
        CouponUsage::create(['user_id' => $userId, 'coupon_id' => $couponId]);
    } catch (UniqueConstraintViolationException) {
        return response()->json(['message' => 'Coupon đã được dùng'], 409);
    }

    return response()->json(['message' => 'Áp dụng thành công'], 201);
}
```

Luồng "đăng ký bằng email" sửa theo cùng cách: migration có `$table->string('email')->unique();`,
rule validation `unique:users` chỉ để báo lỗi sớm, còn `User::create()` được bọc `try/catch
UniqueConstraintViolationException` và trả 422 "email đã được dùng". Chi tiết ở
[05-php-laravel.md, module 1.6](05-php-laravel.md#16-laravel-cơ-bản).

⚠️ Nếu việc ghi lượt dùng coupon nằm trong transaction cùng với việc tạo đơn, lỗi duplicate key làm
câu `INSERT` thất bại; hãy để exception thoát ra khỏi closure của `DB::transaction()` để cả
transaction rollback, rồi mới bắt ở ngoài, thay vì nuốt lỗi bên trong và commit một đơn hàng dở dang.

#### Lock trong bộ nhớ không đủ

⚠️ Lock trong bộ nhớ chỉ có tác dụng trong **một process**: `synchronized` hay `ReentrantLock` của
Java, `sync.Mutex` của Go, một biến static trong PHP.

```
            load balancer
          /       |       \
      pod 1     pod 2     pod 3        mỗi pod một mutex riêng,
      [mutex]   [mutex]   [mutex]      không pod nào thấy mutex của pod khác
          \       |       /
             MySQL (dòng stock)        chỉ ở đây mới có một điểm chung
```

- Java hay Go chạy một instance thì mutex quanh đoạn trừ kho "có vẻ" đúng. Scale lên 3 pod, mỗi pod có
  khoá riêng, request ở pod 1 và pod 2 vẫn chạy song song trên cùng một dòng.
- PHP-FPM còn không có khoá kiểu này: mỗi request đã là một process riêng, biến static sống đúng một
  request. Ngay trên một máy, hai worker FPM đã là hai "server" khác nhau.
- Khoá bằng file (`flock`) chỉ đúng trong một máy, và không còn đúng khi chạy nhiều máy hoặc nhiều
  container không chung ổ đĩa.

Vì vậy điểm chặn phải đặt ở nơi mọi instance cùng nhìn thấy: DB (atomic update, row lock, unique,
advisory lock) hoặc Redis (atomic command, Lua, `Cache::lock()`). Đối chiếu: đây cũng là lý do trong
Java/Spring, `synchronized` trên một method `@Transactional` không chống được bán quá tồn kho khi chạy
nhiều instance, và người ta vẫn phải dùng `@Version` hoặc `SELECT ... FOR UPDATE`.

**Tóm tắt nhanh**
- Race ở tầng web là giữa các request, process, pod; dữ liệu chung nằm ở DB/Redis nên chốt chặn phải
  nằm ở đó, mutex trong bộ nhớ vô dụng khi có nhiều instance.
- Check-then-act là mẫu gốc của mọi bug "dùng hai lần"; sửa bằng một thao tác atomic: `UPDATE ... WHERE`
  kèm kiểm tra affected rows, unique constraint, upsert, `SET NX`, Lua.
- Bọc trong transaction không sửa được đọc-rồi-ghi ở RR mặc định, vì `SELECT` thường không khoá.
- Bốn cách trừ kho và giá của chúng: atomic (đơn giản nhất), `FOR UPDATE` (logic phức tạp, giữ khoá),
  optimistic (không khoá, retry), Redis/queue (tải cực cao, phải đối soát).
- Luôn có unique constraint làm lưới an toàn cuối và bắt lỗi trùng key thành 409/422.

**Nguồn**: *Designing Data-Intensive Applications* ch.7 (*Preventing Lost Updates*, *Write Skew and
Phantoms*) · [Laravel: Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking) ·
[Laravel: Increment and Decrement](https://laravel.com/docs/queries#increment-and-decrement) ·
[Laravel: Redis, Lua scripts](https://laravel.com/docs/redis#lua-scripts) ·
[Laravel: Preventing Job Overlaps](https://laravel.com/docs/queues#preventing-job-overlaps) ·
[03-database-sql.md, module 2.6](03-database-sql.md#26-lock-thực-dụng)


---

## Chặng 2: Làm chủ

### 2.1 Atomic, CAS và optimistic lock

Module này trả lời: CAS là gì và vì sao nó luôn đi kèm vòng lặp retry, biến atomic trong Java và Go
làm được gì và không làm được gì, và vì sao optimistic lock trong DB hay `ETag` ở tầng HTTP thật ra
là cùng một ý tưởng CAS.

#### CAS

*Atomic operation* là thao tác mà phần cứng hoặc runtime đảm bảo diễn ra trọn vẹn trong một bước:
không thread nào nhìn thấy trạng thái "làm được một nửa", và không thread nào chen vào giữa được.
`count++` thường **không** atomic (đọc, cộng, ghi là ba bước, module 1.1); `atomic.Int64.Add(1)` thì
có.

*CAS* (compare-and-swap) là atomic operation quan trọng nhất. Tài liệu `sync/atomic` của Go mô tả nó
bằng đoạn code tương đương sau, với điều kiện cả khối chạy như một bước duy nhất:

```go
// CompareAndSwap(addr, old, new) tương đương, nhưng atomic:
if *addr == old {
	*addr = new
	return true
}
return false
```

Nói bằng lời: "nếu giá trị vẫn là cái tôi đã thấy thì ghi giá trị mới, còn nếu ai đó đã đổi rồi thì
đừng ghi gì cả và báo cho tôi biết". CPU có lệnh riêng cho việc này (x86 có `LOCK CMPXCHG`; ARM dùng
cặp lệnh load-exclusive/store-exclusive, các đời mới có thêm lệnh CAS), nên không cần khoá.

CAS một mình chỉ ghi được khi không ai chen vào. Để luôn hoàn thành được việc, nó nằm trong vòng lặp:

1. Đọc giá trị hiện tại, gọi là `old`.
2. Tính giá trị mới từ `old` (việc này có thể phức tạp tuỳ ý).
3. Gọi `CAS(addr, old, new)`.
4. Thất bại nghĩa là giữa bước 1 và bước 3 có thread khác đã ghi. Giá trị `new` vừa tính dựa trên dữ
   liệu cũ nên vô giá trị; quay lại bước 1 đọc giá trị mới.

Chương trình Go chạy được (Go 1.25+ vì dùng `wg.Go`; lưu thành `main.go`, chạy `go run main.go`):

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

// incrementCAS tăng bộ đếm bằng vòng lặp CAS, trả về số lần CAS thất bại.
func incrementCAS(c *atomic.Int64) (retries int) {
	for {
		old := c.Load()                  // 1. đọc giá trị hiện tại
		next := old + 1                  // 2. tính giá trị mới từ old
		if c.CompareAndSwap(old, next) { // 3. chỉ ghi nếu vẫn còn là old
			return retries
		}
		retries++ // 4. có goroutine khác vừa ghi, quay lại bước 1
	}
}

func main() {
	var counter atomic.Int64
	var retries atomic.Int64
	var wg sync.WaitGroup

	for g := 0; g < 8; g++ {
		wg.Go(func() {
			for i := 0; i < 100_000; i++ {
				retries.Add(int64(incrementCAS(&counter)))
			}
		})
	}
	wg.Wait()

	fmt.Println("counter =", counter.Load())     // luôn 800000
	fmt.Println("CAS thất bại:", retries.Load()) // mỗi lần chạy một khác, thường > 0
}
```

`counter` luôn đúng 800000. Trên một máy Apple Silicon nhiều core, hai lần chạy thử cho số lần CAS
thất bại là 1749554 và 1065367 (con số chỉ để minh hoạ, máy khác cho kết quả khác). Nghĩa là dưới
tranh chấp cao, mỗi lần tăng trung bình phải thử lại hơn một lần: CAS không khoá, nhưng không miễn
phí. Hai hệ quả:

- Chỉ để cộng một số thì dùng thẳng `Add`; nó là một thao tác atomic, không cần vòng lặp ở code của
  bạn. Vòng CAS dành cho trường hợp giá trị mới phải tính từ giá trị cũ theo cách mà `Add` không làm
  được, ví dụ "tăng nhưng không vượt 100", "cập nhật max", "đổi trạng thái từ `pending` sang `running`
  chỉ khi đang là `pending`".
- Phần tính ở bước 2 có thể chạy nhiều lần, nên không được có tác dụng phụ (ghi log, gửi request).
  Javadoc của `AtomicInteger.updateAndGet` cũng yêu cầu hàm truyền vào không có tác dụng phụ vì lý do
  này.

JCIP (ch.15) so sánh hiệu năng và rút ra: ở mức tranh chấp rất cao, lock có thể nhanh hơn atomic (vì
lock cho các thread ngủ chờ, còn CAS làm chúng quay vòng đụng nhau liên tục); ở mức tranh chấp thực
tế thường gặp, atomic nhanh hơn. CAS là nền của các cấu trúc lock-free (module 3.2).

⚠️ *Vấn đề ABA*: CAS chỉ so **giá trị**, không biết giá trị đó đã đổi qua lại hay chưa. Thread 1 đọc
`A`; thread 2 đổi `A` thành `B` rồi lại thành `A`; CAS của thread 1 vẫn thành công dù trạng thái đã
thay đổi ở giữa. Với bộ đếm số nguyên thì thường vô hại. Với con trỏ trong cấu trúc lock-free (node
bị giải phóng rồi cấp phát lại đúng địa chỉ) thì là bug thật. Cách chữa kinh điển là ghép thêm một số
phiên bản tăng dần: Java có `AtomicStampedReference` (giá trị cộng một "stamp" số nguyên). Đây cũng
là lý do optimistic lock ở DB dùng cột `version` tăng mãi thay vì so giá trị cũ của chính cột dữ liệu.

#### Biến atomic trong Java và Go

Java, package `java.util.concurrent.atomic`:

```java
AtomicInteger stock = new AtomicInteger(10);
stock.incrementAndGet();                 // ++stock, trả 11
stock.compareAndSet(11, 20);             // true: đang là 11 nên thành 20
stock.compareAndSet(11, 30);             // false: đã là 20, không ghi
stock.updateAndGet(x -> Math.min(x + 5, 22)); // vòng CAS có sẵn, trả 22
```

- `AtomicInteger`, `AtomicLong`, `AtomicBoolean`, `AtomicReference<V>` cho một biến.
- `LongAdder` cho bộ đếm bị rất nhiều thread cùng ghi: nó chia tổng thành nhiều ô, mỗi thread thường
  cộng vào ô riêng nên ít đụng nhau; `sum()` cộng các ô lại. Đổi lại `sum()` không phải một ảnh chụp
  atomic khi đang có thread ghi. Hợp với số liệu thống kê, không hợp khi cần CAS trên tổng (module 3.2).
- Tầng thấp hơn là `VarHandle` (từ Java 9): thao tác atomic, kể cả CAS, trên một field hay phần tử mảng bất kỳ mà không cần bọc trong một object atomic.

Go, package `sync/atomic`:

- Từ Go 1.19 có các kiểu typed: `atomic.Int32`, `atomic.Int64`, `atomic.Uint32`, `atomic.Uint64`,
  `atomic.Uintptr`, `atomic.Bool`, `atomic.Pointer[T]`. Mỗi kiểu có `Load`, `Store`, `Swap`,
  `CompareAndSwap`, kiểu số có thêm `Add`; `And` và `Or` được thêm từ Go 1.23.
- Các hàm kiểu cũ (`atomic.AddInt64(&x, 1)`, `atomic.CompareAndSwapInt64(...)`) vẫn còn, nhưng tài liệu
  khuyên dùng kiểu typed vì ít lỗi hơn. Lý do cụ thể: trên kiến trúc 32 bit (ARM, 386, MIPS 32 bit),
  hàm cũ đòi người gọi tự đảm bảo biến 64 bit được căn lề 64 bit, còn `atomic.Int64`, `atomic.Uint64`
  tự căn lề.
- `atomic.Value` (từ Go 1.4) giữ một giá trị bất kỳ; mọi lần `Store` phải cùng một kiểu cụ thể, sai
  kiểu hoặc `Store(nil)` thì panic. Ví dụ trong tài liệu: giữ cấu hình hiện tại, một goroutine nạp lại
  cấu hình định kỳ bằng `Store`, các worker đọc bằng `Load`.
- ⚠️ Các kiểu atomic "must not be copied after first use". Chúng có trường `noCopy` bên trong, nên
  `go vet` (analyzer `copylocks`) báo khi bạn copy, giống với `sync.Mutex` ở module 1.2.
- Ngữ nghĩa bộ nhớ: tài liệu Go ghi mọi atomic operation hành xử như chạy theo một thứ tự tuần tự nhất
  quán duy nhất, tương đương atomic sequentially consistent của C++ và biến `volatile` của Java. Nói
  gọn: ghi atomic ở goroutine này thì `Load` ở goroutine khác chắc chắn thấy (visibility, module 3.1).
- Chính tài liệu `sync/atomic` cảnh báo đây là primitive cấp thấp, "require great care"; ngoài các
  trường hợp đặc biệt, đồng bộ bằng channel hoặc package `sync` tốt hơn.

⚠️ Atomic trên **từng biến** không làm **nhiều biến** atomic cùng nhau:

```go
var balance, version atomic.Int64

// Goroutine ghi:
balance.Store(50)   // (1)
version.Add(1)      // (2)

// Goroutine đọc chạy giữa (1) và (2) thấy balance mới đi với version cũ.
```

Mỗi thao tác đều atomic, nhưng cặp `(balance, version)` thì không. Có hai cách sửa:

1. Dùng mutex bảo vệ cả hai (đơn giản, thường là đáp án đúng).
2. Gói chúng vào một struct bất biến và thay cả struct bằng một con trỏ atomic:

   ```go
   type account struct{ balance, version int64 }

   var cur atomic.Pointer[account]

   func withdraw(amount int64) bool {
   	for {
   		old := cur.Load()
   		if old.balance < amount {
   			return false
   		}
   		next := &account{balance: old.balance - amount, version: old.version + 1}
   		if cur.CompareAndSwap(old, next) {
   			return true
   		}
   	}
   }
   ```

   Không ai sửa struct cũ tại chỗ; mỗi lần ghi tạo struct mới rồi CAS con trỏ, nên người đọc luôn thấy
   một cặp nhất quán. Đây là mẫu copy-on-write, ví dụ `ReadMostly` trong tài liệu `sync/atomic` dùng
   đúng ý này cho một map đọc nhiều ghi ít. Trước khi gọi `withdraw` phải `cur.Store(&account{...})`
   một lần, nếu không `Load()` trả `nil`.

Đối chiếu PHP: PHP-FPM không chia sẻ bộ nhớ giữa các request, nên không có biến atomic ở tầng ngôn
ngữ. "Biến atomic dùng chung" của app PHP là Redis (`INCR`, `DECR`, `SET NX`, Lua) hoặc một câu
`UPDATE` atomic trong MySQL.

#### Optimistic lock là CAS ở mức dữ liệu

Đặt CAS cạnh câu SQL optimistic lock:

```
CAS(addr,          old,             new)
     │              │                │
UPDATE products SET price = ?, version = version + 1
WHERE id = ?     AND version = ?;         -- version đã đọc lúc mở form
     │              │
  "địa chỉ"      "expected"         affected rows = 1  ⇔ CAS thành công
                                    affected rows = 0  ⇔ CAS thất bại
```

- Cột `version` là `expected`. Nó tăng mỗi lần ghi nên không bị ABA.
- Affected rows bằng 0 nghĩa là ai đó đã ghi trước (hoặc dòng không còn). Như vòng CAS, app có hai
  lựa chọn: đọc lại rồi tự retry (khi thay đổi tự động tính lại được, ví dụ trừ tồn kho), hoặc báo
  xung đột cho người dùng (khi thay đổi đến từ một người đang nhìn dữ liệu cũ).
- Câu `UPDATE` là locking read, luôn đánh giá `WHERE` trên bản mới nhất, nên đúng ở mọi isolation level
  của MySQL. Timeline hai biên tập viên, cạm bẫy `PDO` đếm dòng thay đổi và vì sao không dùng
  `updated_at` làm version ở [03-database-sql.md, module 2.6](03-database-sql.md#26-lock-thực-dụng).

Luồng admin sửa sản phẩm, trả 409 khi xung đột (tiêu chí "Nắm chắc khi" của plan):

1. `GET /admin/products/7` trả dữ liệu kèm `version` hiện tại, form giữ nó trong một field ẩn.
2. Admin sửa vài phút. Không có khoá nào, không có transaction nào đang mở.
3. `PUT /admin/products/7` gửi dữ liệu mới kèm `version` cũ.
4. Server chạy `UPDATE ... WHERE id = 7 AND version = ?`. Được 1 dòng: trả version mới. Được 0 dòng:
   trả `409 Conflict` kèm bản hiện tại để UI hiện "Sản phẩm đã bị người khác sửa, xem thay đổi và lưu
   lại".

```php
<?php
declare(strict_types=1);

namespace App\Http\Controllers\Admin;

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

final class ProductController
{
    public function update(Request $request, int $id): JsonResponse
    {
        $data = $request->validate([
            'name'    => ['required', 'string', 'max:255'],
            'price'   => ['required', 'integer', 'min:0'],
            'version' => ['required', 'integer', 'min:1'],
        ]);
        $version = (int) $data['version'];

        $affected = DB::table('products')
            ->where('id', $id)
            ->where('version', $version)                 // "expected" của CAS
            ->update([
                'name'    => $data['name'],
                'price'   => (int) $data['price'],
                'version' => DB::raw('version + 1'),
            ]);

        if ($affected === 1) {
            return response()->json(['version' => $version + 1]);
        }

        $current = DB::table('products')->find($id);
        if ($current === null) {
            return response()->json(['message' => 'Sản phẩm không còn tồn tại'], 404);
        }

        return response()->json([
            'message' => 'Sản phẩm đã bị người khác sửa',
            'current' => $current,                       // để UI cho so sánh và sửa lại
        ], 409);
    }
}
```

Eloquent không có optimistic lock dựng sẵn, phải tự viết điều kiện như trên. JPA/Hibernate có
`@Version`: tự thêm `WHERE version = ?` và ném `OptimisticLockException` khi 0 dòng. ⚠️ Mọi đường ghi
vào bảng (job, lệnh artisan, admin khác) đều phải tăng `version`, nếu không đường ghi đó bị ghi đè
mà không ai phát hiện.

Ở tầng HTTP, cặp `ETag` và `If-Match` (RFC 9110) là cùng ý tưởng, nhưng chuẩn hoá bằng header thay vì
field trong body ([09-api-design.md](../09-api-design.md)):

1. `GET /products/7` trả header `ETag: "v5"`, một mã đại diện cho phiên bản hiện tại của tài nguyên
   (có thể là version, hoặc hash nội dung).
2. Client sửa rồi gửi `PUT /products/7` kèm `If-Match: "v5"`.
3. Server so với ETag hiện tại. Khớp: ghi. Không khớp: trả `412 Precondition Failed`, không ghi gì.

Phía server, bước 3 vẫn phải là một `UPDATE ... WHERE version = ?` atomic; nếu server tự "đọc ETag,
so, rồi ghi" trong ba bước thì lại là check-then-act. Server muốn bắt buộc client gửi `If-Match` có
thể trả `428 Precondition Required` khi thiếu header (RFC 6585). Chọn 409 hay 412: 412 là mã chuẩn
khi dùng `If-Match`; 409 hợp khi version đi trong body như ví dụ Laravel ở trên.

#### Chọn optimistic hay pessimistic

| | Optimistic (`version`, CAS) | Pessimistic (`FOR UPDATE`, mutex) |
|---|---|---|
| Giả định | Xung đột hiếm | Xung đột thường xuyên |
| Hợp khi tranh chấp | Thấp | Cao |
| Hợp khi thao tác | Kéo dài, qua nhiều request, có người suy nghĩ giữa chừng | Ngắn, trong một request, ví dụ trừ tồn kho |
| Khi có xung đột | Bên ghi sau thất bại, phải retry hoặc báo người dùng | Bên sau chờ bên trước xong rồi chạy tiếp |
| Giữ tài nguyên | Không giữ khoá, không giữ transaction hay connection | Giữ khoá và connection suốt thời gian thao tác |
| Rủi ro | Quên kiểm tra affected rows; retry bão khi tranh chấp cao; đường ghi quên tăng version | Deadlock, lock wait timeout, throughput giảm |

- ⚠️ Người dùng suy nghĩ vài phút trên form thì không thể giữ `FOR UPDATE` suốt thời gian đó: khoá chỉ
  sống trong một transaction, transaction chỉ sống trong một request PHP, và giữ khoá vài phút sẽ làm
  mọi request khác chạm vào dòng đó đứng chờ. Thao tác qua nhiều request gần như luôn phải là optimistic.
- ⚠️ Optimistic dưới tranh chấp cao (1000 người cùng mua một sản phẩm flash sale) tệ hơn cả hai lựa
  chọn còn lại: đa số lần thử thất bại, mỗi lần tốn một round-trip. Khi đó dùng atomic update hoặc
  pessimistic (module 1.4).
- Cả hai đều cần thiết kế cho thất bại: optimistic cần đường retry hoặc UI xử lý 409, pessimistic cần
  retry cho deadlock (module 1.3).

**Tóm tắt nhanh**
- CAS: "vẫn là giá trị tôi đã thấy thì ghi, không thì báo thất bại"; phải nằm trong vòng lặp đọc lại
  và tính lại, và phần tính không được có tác dụng phụ.
- Bộ đếm thì dùng `Add`/`incrementAndGet`, CAS loop khi giá trị mới phụ thuộc giá trị cũ theo luật
  riêng. Dưới tranh chấp cao CAS retry rất nhiều.
- Atomic từng biến không làm nhóm biến atomic: dùng mutex, hoặc struct bất biến và `atomic.Pointer`.
- Optimistic lock là CAS trên dòng dữ liệu: `WHERE version = ?`, affected rows 0 là thua; `ETag` +
  `If-Match` là CAS ở tầng HTTP (412).
- Optimistic cho thao tác dài, tranh chấp thấp; pessimistic cho thao tác ngắn, tranh chấp cao.

**Nguồn**: [Go: sync/atomic](https://pkg.go.dev/sync/atomic) · *Java Concurrency in Practice* ch.15
(*Atomic Variables and Nonblocking Synchronization*) ·
[03-database-sql.md, module 2.6](03-database-sql.md#26-lock-thực-dụng) ·
[RFC 9110: If-Match](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1)


---

### 2.2 Lost update và isolation level

Module này trả lời: lost update xảy ra ở đâu (trong DB và cả giữa các request HTTP), isolation level
chặn được nó tới mức nào, vì sao MySQL và Postgres cùng tên "REPEATABLE READ" mà cư xử ngược nhau, và
write skew là loại race mà cả hai đều để lọt. Phần isolation đầy đủ (mọi anomaly, timeline chi tiết,
SSI của Postgres) ở [03-database-sql.md, module 2.5](03-database-sql.md#25-isolation-level-và-anomaly);
module này đứng ở góc nhìn concurrency và chỉ nhắc lại những gì cần để trả lời câu hỏi vặn.

#### Lost update

*Lost update* là khi hai bên cùng đọc một bản ghi, mỗi bên sửa dựa trên thứ mình đọc rồi ghi lại, và
bên ghi sau đè mất thay đổi của bên ghi trước. Đây là check-then-act (module 1.4) ở dạng
*read-modify-write*: đọc, tính ở app, ghi giá trị cố định. Nó nguy hiểm vì không có dấu hiệu gì: không
exception, không log lỗi, không deadlock, chỉ là một thay đổi biến mất.

Lost update có hai "tầng", và cách sửa khác nhau:

**Tầng 1: trong DB, hai transaction chạy chồng nhau** (vài mili giây). Ví dụ trừ tồn kho ở module
1.4, hoặc cộng điểm thưởng: `SELECT points` được 100, app tính 100 + 10, `UPDATE ... SET points = 110`.
Isolation level có ảnh hưởng ở tầng này (xem các nhóm dưới).

**Tầng 2: giữa các request HTTP** (vài phút). Ví dụ trang admin:

1. Admin A mở form sản phẩm (request 1 đọc giá 100, mô tả "cũ").
2. Admin B mở cùng form (request 2 đọc cùng dữ liệu).
3. A đổi giá thành 90, bấm lưu (request 3 ghi giá 90).
4. B đổi mô tả thành "mới", bấm lưu cả form, gồm cả giá 100 đang hiện trên form của B (request 4 ghi
   giá 100, mô tả "mới"). Giá của A mất.

⚠️ Ở tầng 2, **không isolation level nào cứu được**, kể cả Serializable: lần đọc (request 2) và lần ghi
(request 4) nằm ở hai transaction khác nhau, cách nhau vài phút, nên DB thấy request 4 chỉ là một câu
`UPDATE` bình thường. Chỉ app mới biết B đã ra quyết định dựa trên dữ liệu cũ.

Bốn cách sửa, và tầng mà mỗi cách áp dụng được:

| Cách | Ý tưởng | Tầng 1 | Tầng 2 |
|---|---|---|---|
| Chỉ ghi field thật sự thay đổi | B chỉ gửi và chỉ ghi `description`, không đụng `price` | Không đủ | Giảm được, không chặn được khi hai người sửa cùng field |
| Atomic update | `SET stock = stock - 1`, `SET points = points + 10`: DB tính trên bản mới nhất | Có | Không áp dụng (người dùng nhập giá trị mới, không phải phép cộng) |
| Optimistic lock | `WHERE version = ?`, 0 dòng là thua (module 2.1) | Có | Có, đây là cách chuẩn |
| `SELECT ... FOR UPDATE` | Khoá dòng từ lúc đọc tới lúc commit | Có | Không: không thể giữ khoá qua nhiều request |

⚠️ Bẫy của cách "chỉ ghi field thay đổi" trong Laravel: `save()` của Eloquent chỉ gửi các cột *dirty*
(khác với giá trị lúc model được load). Nhưng ở request 4, model được load lại từ DB, lúc đó giá đã là
90; form của B gửi lên giá 100, khác 90, nên cột `price` bị coi là dirty và bị ghi đè. "Thay đổi" phải
được tính so với giá trị **form đã hiển thị cho B**, không phải so với DB lúc lưu. Cách chắc chắn vẫn
là cột `version`.

DDIA còn nhắc hai điểm:

- ORM làm cho việc viết read-modify-write rất dễ (`$model->points += 10; $model->save();`), trong khi
  atomic update phải viết có chủ đích (`->increment('points', 10)`).
- Khi dữ liệu được ghi ở nhiều replica (multi-leader, leaderless), chiến lược "last write wins" (bản
  ghi có timestamp mới nhất thắng) là lost update theo thiết kế. Chi tiết ở
  [14-distributed-systems.md](../14-distributed-systems.md).

#### Nhắc lại isolation level

*Isolation level* là mức DB che các transaction đồng thời khỏi nhau. Mức càng cao càng ít anomaly,
đổi lại chờ nhiều hơn hoặc phải retry nhiều hơn. Hai mức hay gặp:

- *Read Committed* (RC), mặc định của Postgres: mỗi câu lệnh thấy dữ liệu đã commit tại lúc **câu đó**
  bắt đầu. Hai câu `SELECT` liên tiếp trong một transaction có thể thấy dữ liệu khác nhau.
- *Repeatable Read* (RR), mặc định của MySQL InnoDB: cả transaction đọc từ cùng một *snapshot* (ảnh
  chụp dữ liệu). Ở Postgres, snapshot được chụp ở câu lệnh đầu tiên không phải lệnh điều khiển
  transaction; ở MySQL, ở câu đọc nhất quán đầu tiên, không phải ở `START TRANSACTION`.

Điểm then chốt để hiểu lost update ở InnoDB: trong cùng một transaction có **hai kiểu đọc** nhìn thấy
hai "thế giới" khác nhau.

```
transaction T2 (MySQL RR), sau khi T1 đã trừ 5 thành 4 và commit

  SELECT stock ...            consistent read: đọc SNAPSHOT, không khoá      → thấy 5 (cũ)
  UPDATE ... / FOR UPDATE     locking read: đọc BẢN MỚI NHẤT đã commit,      → thấy 4 (mới)
                              khoá dòng, chờ nếu dòng đang bị khoá
```

Lý do: không thể ghi đè lên một phiên bản cũ, muốn sửa thì phải sửa bản mới nhất. Chi tiết cơ chế
MVCC và undo log ở [03-database-sql.md, module 2.5](03-database-sql.md#25-isolation-level-và-anomaly)
và module 3.1 cùng file.

Thử nhanh bằng hai terminal (lệnh Docker ở đầu file 03):

```sql
-- MySQL, chạy một lần
CREATE TABLE products (id INT PRIMARY KEY, stock INT NOT NULL);
INSERT INTO products VALUES (1, 5);
SELECT @@transaction_isolation;   -- REPEATABLE-READ (biến cũ @@tx_isolation đã bị bỏ từ 8.0)

-- Postgres, chạy một lần
CREATE TABLE products (id INT PRIMARY KEY, stock INT NOT NULL);
INSERT INTO products VALUES (1, 5);
-- mỗi session mở transaction bằng: BEGIN ISOLATION LEVEL REPEATABLE READ;
```

#### Cùng REPEATABLE READ, hai DB khác nhau

Kịch bản: tồn kho 5, hai request cùng trừ 1 theo kiểu đọc rồi ghi số cố định.

| Bước | T1 | T2 | MySQL RR | Postgres RR |
|---|---|---|---|---|
| 1 | `BEGIN;` `SELECT stock FROM products WHERE id = 1;` | | T1 thấy 5 | T1 thấy 5 |
| 2 | | `BEGIN;` `SELECT stock FROM products WHERE id = 1;` | T2 thấy 5 | T2 thấy 5 |
| 3 | `UPDATE products SET stock = 4 WHERE id = 1;` | | T1 khoá dòng | T1 khoá dòng |
| 4 | | `UPDATE products SET stock = 4 WHERE id = 1;` | T2 chờ khoá | T2 chờ khoá |
| 5 | `COMMIT;` | | T2 chạy tiếp, **không lỗi** | T2 nhận `ERROR: could not serialize access due to concurrent update` |
| 6 | | `COMMIT;` | stock = 4. Một lần trừ **mất âm thầm** | T2 phải `ROLLBACK` rồi chạy lại từ đầu, lần sau thấy 4, ghi 3. Đúng |

(Ở MySQL dùng `START TRANSACTION;` hoặc `BEGIN;` sau khi đã đặt level; ở Postgres dùng `BEGIN
ISOLATION LEVEL REPEATABLE READ;`.) Đây chính là test P4 (Lost Update) trong Hermitage: Postgres
"repeatable read" chặn P4, MySQL/InnoDB "repeatable read" thì không. Hermitage chạy trên các phiên bản
cũ (MySQL 5.6), nhưng cơ chế consistent read và locking read ở trên là hành vi được mô tả trong tài
liệu InnoDB hiện hành.

| | Postgres RR | InnoDB RR |
|---|---|---|
| Transaction ghi vào dòng mà transaction khác đã sửa và commit sau khi snapshot của mình được chụp | Bị huỷ, lỗi `40001` | Chờ khoá rồi ghi đè, không lỗi |
| Thực chất level này là gì (theo Hermitage) | Snapshot isolation | Yếu hơn snapshot isolation |
| App phải làm gì | Bắt `40001`, retry **cả transaction** | Tự chống lost update: atomic update, `FOR UPDATE`, hoặc `version` |

Vì sao `UPDATE products SET stock = stock - 1 WHERE id = 1` lại an toàn ở InnoDB RR, dù T2 đã đọc 5
từ snapshot: câu `UPDATE` là locking read. Ở bước 4 nó chờ khoá của T1; khi T1 commit, nó đọc **bản
mới nhất** (4) chứ không đọc snapshot (5), tính `4 - 1 = 3` rồi ghi. Giá trị app "đã đọc" không tham
gia vào phép tính, nên không có gì cũ để ghi đè. Còn "đọc 5 rồi ghi `stock = 4`" thì con số 4 được tính
ở app từ snapshot cũ; DB chỉ nhận một hằng số và ghi nó, không biết nó sai.

Ba điểm hay bị hỏi vặn:

- ⚠️ Ở Postgres RR, cả câu atomic `SET stock = stock - 1` cũng bị lỗi `40001` nếu dòng đã bị transaction
  khác sửa sau khi snapshot được chụp, vì quy tắc của RR là không được sửa dòng như vậy. Tài liệu
  Postgres ghi rõ app dùng level này "must be prepared to retry". Chỉ transaction có ghi mới cần retry;
  transaction chỉ đọc không bao giờ gặp lỗi serialization.
- ⚠️ Read Committed, mặc định của Postgres, **không** chặn lost update kiểu "app đọc, tự tính, rồi ghi"
  (Hermitage: Postgres RC không chặn P4). Ở RC, câu `UPDATE` bị chặn sẽ chờ, rồi đánh giá lại `WHERE`
  trên bản mới của dòng và ghi. Vì thế atomic update đúng ở Postgres RC, còn ghi hằng số tính từ lần
  đọc trước thì đè mất.
- ⚠️ MySQL Serializable chặn được lost update nhưng bằng cách khác: mọi `SELECT` thường (khi autocommit
  tắt) thành `FOR SHARE`, hai bên cùng giữ khoá S, cùng xin khoá X để ghi, và InnoDB phát hiện deadlock:
  một bên nhận `ERROR 1213 (40001): Deadlock found`. An toàn, nhưng trả giá bằng khoá và vẫn phải retry.

Retry trong Laravel: `DB::transaction($fn, 3)` thử tối đa 3 lần khi gặp deadlock hoặc lỗi
serialization; mặc định chỉ 1 lần, tức không retry. Retry phải chạy lại từ câu đọc đầu tiên, và
closure không được có tác dụng phụ ra ngoài DB. Chi tiết và code ở
[03-database-sql.md, module 2.5](03-database-sql.md#25-isolation-level-và-anomaly) (mục "Bốn cách chống
lost update").

#### Write skew

*Write skew* là khi hai transaction đọc cùng một tập dữ liệu, mỗi bên ghi vào một dòng **khác nhau**,
và gộp lại thì vi phạm một ràng buộc mà mỗi bên, nếu chạy một mình, đều giữ đúng. Nó là "người anh"
của lost update: lost update là hai bên ghi cùng một dòng, write skew là hai bên ghi hai dòng khác nhau
dựa trên cùng một tiền đề.

Ví dụ trong DDIA: ca trực luôn phải có ít nhất một bác sĩ.

| Bước | T1 (bác sĩ A) | T2 (bác sĩ B) | Kết quả |
|---|---|---|---|
| 1 | `SELECT COUNT(*) FROM doctors WHERE shift_id = 1 AND on_call = TRUE;` | | 2 |
| 2 | | Cùng câu đếm | 2 |
| 3 | Còn người khác, `UPDATE doctors SET on_call = FALSE WHERE id = 1;` | | T1 khoá dòng 1 |
| 4 | | Còn người khác, `UPDATE doctors SET on_call = FALSE WHERE id = 2;` | Không chờ: dòng 2 không ai khoá |
| 5 | `COMMIT;` | `COMMIT;` | Cả hai thành công, ca 1 không còn ai trực |

RR của cả MySQL lẫn Postgres đều để lọt (Hermitage test G2-item), vì không có dòng nào bị hai bên cùng
ghi: cơ chế "phát hiện ghi đè trên cùng một dòng" của Postgres RR không có gì để phát hiện, và khoá
dòng của InnoDB không có gì để chặn.

Cùng cấu trúc xuất hiện ở nhiều nơi: đặt phòng họp không trùng giờ, đăng ký username chưa ai dùng, hai
lần rút tiền cùng kiểm tra tổng số dư của nhiều tài khoản. Khi câu kiểm tra là "**chưa có** dòng nào
thoả" (phòng trống, username chưa có) thì hiện tượng gọi là *phantom*: câu ghi của bên này tạo ra một
dòng làm thay đổi kết quả câu tìm kiếm của bên kia, và không có dòng sẵn có nào để khoá.

Ba hướng sửa (chi tiết và timeline ở 03, module 2.5):

1. Khoá cả tập đã đọc: đổi câu đếm thành `SELECT ... FOR UPDATE`. Chỉ ổn khi các dòng đó đang tồn tại.
2. Đưa ràng buộc xuống DB: unique index cho điều kiện "không trùng"; với điều kiện dạng đếm thì
   *materialize conflict*, tức tạo một dòng đại diện (ví dụ `shifts.on_call_count`) để mọi transaction
   liên quan cùng phải ghi vào nó bằng atomic update. Write skew khi đó trở thành lost update trên một
   dòng, và đã giải được bằng các cách ở trên.
3. Serializable kèm retry: Postgres Serializable (SSI) huỷ một bên với `40001`; MySQL
   Serializable biến câu đếm thành `FOR SHARE` và một bên nhận deadlock 1213.

**Tóm tắt nhanh**
- Lost update = read-modify-write, bên ghi sau đè bên ghi trước, không có lỗi nào. Giữa các request
  HTTP (form admin) thì không isolation level nào cứu, chỉ `version` cứu.
- InnoDB có hai kiểu đọc: `SELECT` thường đọc snapshot, `UPDATE`/`FOR UPDATE` đọc bản mới nhất và khoá.
  Vì vậy `SET stock = stock - 1` an toàn, "đọc rồi ghi `stock = 4`" thì mất dữ liệu âm thầm.
- Cùng RR: Postgres huỷ bên ghi sau với `40001` (phải retry cả transaction), InnoDB cho ghi đè không
  lỗi. Postgres RC cũng để lọt lost update kiểu đọc rồi ghi.
- Write skew ghi hai dòng khác nhau nên RR của cả hai DB đều lọt; sửa bằng `FOR UPDATE` cả tập,
  materialize conflict hoặc unique, hoặc Serializable kèm retry.

**Nguồn**: [PostgreSQL: Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-REPEATABLE-READ) ·
[Hermitage](https://github.com/ept/hermitage) (README, `mysql.md`, `postgres.md`, test P4 và G2-item) ·
*Designing Data-Intensive Applications* ch.7 (*Preventing Lost Updates*, *Write Skew and Phantoms*) ·
[03-database-sql.md, module 2.5](03-database-sql.md#25-isolation-level-và-anomaly)

---

### 2.3 Double submit, idempotency key

Module này trả lời: vì sao cùng một thao tác (thanh toán, tạo đơn) lại tới server hai lần, và làm
thế nào để server xử lý nó đúng một lần kể cả khi hai bản sao tới cùng một lúc.

#### Vì sao request bị gửi trùng

Có bốn nguồn chính. Chỉ nguồn đầu tiên là do người dùng:

1. Người dùng bấm nút hai lần, bấm F5 sau khi submit form, hoặc mở hai tab.
2. Client (app mobile, SDK, service khác) gặp timeout rồi retry. Timeout ở phía client **không có
   nghĩa là** server chưa xử lý: request đầu có thể đang chạy, hoặc đã chạy xong nhưng response bị
   mất trên đường về.
3. Load balancer, API gateway hoặc service mesh tự retry khi upstream chậm hoặc đứt kết nối.
4. Mạng di động chập chờn: request tới server, response không tới client.

Kịch bản số 2 là kịch bản nguy hiểm nhất, vì cả hai bên đều "làm đúng":

```
Client                          Server                         Cổng thanh toán (PSP)
  │  POST /payments  ─────────────>│
  │                                │  charge 500.000đ ───────────>│
  │  (10 giây, timeout)            │                               │ trừ tiền OK
  │  POST /payments  ─────────────>│  <── response rất chậm ───────│
  │  (retry, không biết lần 1       │  charge 500.000đ ───────────>│
  │   đã thành công)               │                               │ trừ tiền lần 2
```

Brandur (kỹ sư Stripe) nhấn mạnh rằng ở quy mô hàng triệu request mỗi ngày, các lỗi này không còn là
hiếm mà xảy ra liên tục: mất sóng, gọi Stripe lỗi, client ngắt kết nối giữa chừng.

⚠️ Disable nút bấm ở frontend chỉ giảm nguồn 1. Nó không chặn được hai tab, không chặn được retry
của client hay load balancer, và không có tác dụng gì với client gọi API trực tiếp. Trong phỏng vấn,
nói "disable nút" như câu trả lời chính là red flag; nói nó như một lớp UX bổ sung thì được.

#### Idempotency key

Một thao tác là *idempotent* nếu gọi nó nhiều lần cho cùng kết quả như gọi một lần. Theo đặc tả HTTP
(RFC 9110), các method safe như `GET` cùng với `PUT`, `DELETE` được định nghĩa là idempotent:
`PUT /users/7 {name: "An"}` gửi mười lần thì kết quả vẫn là một user tên An. `POST` thì không: `POST /payments` gửi hai lần là hai
khoản thanh toán. Idempotency key là cách biến một `POST` thành idempotent.

*Idempotency key* là một chuỗi duy nhất do **client** sinh ra cho mỗi thao tác logic (một lần bấm
"Thanh toán"), gửi kèm trong header. Client retry thì gửi lại **đúng key cũ**. Server dùng key để
nhận ra "đây là lần thử lại của thao tác đã thấy", và trả lại kết quả cũ thay vì làm lại.

```http
POST /v1/payments HTTP/1.1
Idempotency-Key: 0ccb7813-e63d-4377-93c5-476cb93038f3
Content-Type: application/json

{"order_id": 981, "amount": 500000}
```

Tên header `Idempotency-Key` bắt nguồn từ API của Stripe. IETF có một draft chuẩn hoá nó
(`draft-ietf-httpapi-idempotency-key-header`); draft này chưa thành RFC, bản gần nhất (-07) đã hết hạn.
Stripe khuyên dùng UUID v4 hoặc chuỗi ngẫu nhiên đủ entropy để không trùng, key dài tối đa 255 ký
tự, và không dùng dữ liệu nhạy cảm (email, số định danh) làm key.

Bảng lưu key cho MySQL 8.4. Theo thiết kế của Brandur, unique constraint đặt trên cặp
`(user_id, idem_key)` để hai user khác nhau vô tình sinh trùng key cũng không ảnh hưởng nhau:

```sql
CREATE TABLE idempotency_keys (
  id            BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  user_id       BIGINT UNSIGNED NOT NULL,
  idem_key      VARCHAR(64)     NOT NULL,
  request_hash  CHAR(64)        NOT NULL,   -- sha256 của body, phát hiện cùng key khác nội dung
  status        VARCHAR(16)     NOT NULL,   -- processing | done
  locked_at     DATETIME(3)     NULL,       -- request nào đang giữ key, từ lúc nào
  response_code SMALLINT        NULL,
  response_body JSON            NULL,
  created_at    DATETIME(3)     NOT NULL,
  UNIQUE KEY uq_user_key (user_id, idem_key)
);
```

Luồng xử lý:

1. Nhận request, `INSERT` một dòng `status = 'processing'`, `locked_at = now()`. Unique constraint
   đảm bảo trong mọi request mang cùng key, **chỉ một** insert thành công.
2. Insert thành công: request này là "chủ" của key. Xử lý nghiệp vụ, lưu `response_code`,
   `response_body`, đổi `status = 'done'`.
3. Insert lỗi trùng key: đọc dòng hiện có.
   - `request_hash` khác: cùng key nhưng khác nội dung, trả lỗi.
   - `status = 'done'`: trả lại đúng response đã lưu, không xử lý lại.
   - `status = 'processing'`: request đầu vẫn đang chạy, trả `409 Conflict` để client thử lại sau.

Stripe lưu kết quả của lần gọi đầu **bất kể thành công hay thất bại**, kể cả lỗi 500: gọi lại với
cùng key nhận đúng lỗi 500 đó. Ngoại lệ: nếu request bị từ chối ở bước validate tham số, hoặc đụng
một request cùng key đang chạy, Stripe không lưu gì (vì endpoint chưa bắt đầu chạy), nên client retry
được. Stripe cũng ghi rõ key chỉ có ý nghĩa với `POST`; gửi kèm `GET` hay `DELETE` không có tác dụng
vì chúng vốn idempotent.

Một bản Laravel rút gọn (từ Laravel 10.20 có `UniqueConstraintViolationException` riêng cho lỗi
trùng unique key, là lớp con của `QueryException`):

```php
<?php
declare(strict_types=1);

namespace App\Http\Controllers;

use App\Services\PaymentGateway;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

final class PaymentController
{
    public function store(Request $request, PaymentGateway $gateway): JsonResponse
    {
        $key = (string) $request->header('Idempotency-Key', '');
        if ($key === '' || strlen($key) > 64) {
            return response()->json(['error' => 'Thiếu hoặc sai Idempotency-Key'], 400);
        }
        $userId = (int) $request->user()->id;
        $hash   = hash('sha256', $request->getContent());

        // Bước 1: chiếm key bằng INSERT. Không SELECT trước (xem cạm bẫy 1)
        try {
            DB::table('idempotency_keys')->insert([
                'user_id' => $userId, 'idem_key' => $key, 'request_hash' => $hash,
                'status' => 'processing', 'locked_at' => now(), 'created_at' => now(),
            ]);
        } catch (UniqueConstraintViolationException) {
            return $this->replay($userId, $key, $hash);   // bước 3
        }

        // Bước 2: làm việc thật. Key gửi sang PSP suy ra từ key của client, ổn định qua mọi lần retry
        $charge = $gateway->charge(
            amount: $request->integer('amount'),
            idempotencyKey: 'pay-' . hash('sha256', $userId . ':' . $key),
        );
        $body = ['charge_id' => $charge->id, 'status' => 'paid'];

        DB::table('idempotency_keys')
            ->where('user_id', $userId)->where('idem_key', $key)
            ->update([
                'status' => 'done', 'locked_at' => null,
                'response_code' => 201,
                'response_body' => json_encode($body, JSON_THROW_ON_ERROR),
            ]);

        return response()->json($body, 201);
    }

    private function replay(int $userId, string $key, string $hash): JsonResponse
    {
        $row = DB::table('idempotency_keys')
            ->where('user_id', $userId)->where('idem_key', $key)->first();

        if ($row === null) {                       // bị dọn ngay giữa chừng, rất hiếm
            return response()->json(['error' => 'Thử lại'], 409);
        }
        if ($row->request_hash !== $hash) {
            return response()->json(['error' => 'Key đã dùng cho nội dung khác'], 422);
        }
        if ($row->status === 'done') {
            return response()->json(
                json_decode($row->response_body, true, 512, JSON_THROW_ON_ERROR),
                (int) $row->response_code,
            );
        }
        return response()->json(['error' => 'Request cùng key đang được xử lý'], 409);
    }
}
```

Đoạn code trên cố tình bỏ qua xử lý lỗi của bước 2 để dễ đọc; phần dưới nói phải làm gì khi PSP lỗi
hoặc process chết giữa chừng.

#### Hai cạm bẫy

⚠️ Cạm bẫy 1: kiểm tra key bằng `SELECT` rồi mới xử lý. Đây lại chính là check-then-act (module 1.4),
hai request cùng key tới cùng lúc đều lọt qua:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `SELECT ... WHERE idem_key='k1'` | | Chưa có |
| 2 | | `SELECT ... WHERE idem_key='k1'` | Cũng chưa có |
| 3 | Gọi PSP, trừ tiền | | |
| 4 | | Gọi PSP, trừ tiền | Trừ hai lần |
| 5 | `INSERT` key | `INSERT` key | Một bên lỗi trùng key, nhưng tiền đã trừ hai lần |

Cách đúng là để DB phân xử **trước** khi làm bất cứ việc gì, bằng chính thao tác ghi có unique
constraint:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `INSERT ... ('k1','processing')` | | A thành công, là chủ key |
| 2 | | `INSERT ... ('k1','processing')` | Lỗi trùng key (1062), B đọc dòng |
| 3 | Gọi PSP | B thấy `processing`, trả 409 | Chỉ A gọi PSP |
| 4 | Lưu response, `status='done'` | | |
| 5 | | Client retry, `INSERT` lỗi trùng | B thấy `done`, trả response của A |

(Nếu bước 1 của A nằm trong một transaction chưa commit, `INSERT` của B ở bước 2 sẽ **chờ** lock trên
bản ghi index trùng cho tới khi A commit hoặc rollback. A commit thì B nhận lỗi trùng; A rollback thì
B insert thành công và thành chủ key.)

Brandur dùng Postgres với transaction `SERIALIZABLE` cho bước chiếm key, nên kể cả khi hai request
cùng cố "khoá" một key đã có sẵn, Postgres huỷ một trong hai. Với MySQL, unique constraint cộng
`INSERT` là cách đơn giản và đủ.

⚠️ Cạm bẫy 2: cùng key nhưng body khác. Thường là bug ở client (tái dùng key cho thao tác mới). Nếu
server chỉ nhìn key rồi trả response cũ, client tưởng thao tác mới đã xong trong khi nó chưa từng
chạy. Phải so `request_hash` và trả lỗi. Stripe và Brandur đều báo lỗi trong trường hợp này; draft
của IETF đề nghị mã `422`, còn trường hợp "request cùng key đang chạy" dùng `409`, thiếu key ở endpoint
bắt buộc có key thì `400`.

Hai chi tiết thêm dễ bị hỏi vặn:

- Key kẹt ở `processing` mãi mãi: process giữ key chết (OOM, bị kill, deploy). Brandur xử lý bằng cột
  `locked_at` và một ngưỡng timeout: request sau chỉ được chiếm lại key khi `locked_at` đã quá hạn.
  Chiếm lại phải là một `UPDATE` có điều kiện, kiểu CAS (module 2.1), để hai request retry không cùng
  chiếm:

  ```sql
  UPDATE idempotency_keys
  SET locked_at = NOW(3)
  WHERE user_id = ? AND idem_key = ? AND status = 'processing'
    AND locked_at < NOW(3) - INTERVAL 60 SECOND;   -- ngưỡng tuỳ thời gian xử lý dài nhất
  -- affected rows = 1: mình là chủ mới; = 0: người khác đang giữ hoặc đã xong
  ```
- Khi lỗi, Brandur mở khoá key (`locked_at = NULL`) chứ không xoá dòng, để lần retry tiếp tục từ chỗ
  đã dừng.

#### Mở rộng: transaction, PSP và thời hạn

*Bản ghi key nên nằm trong cùng transaction với việc gì?* Brandur tách hai loại thay đổi:

- Thay đổi trạng thái cục bộ: ghi vào DB của chính mình (bảng orders, audit log). Nằm được trong
  một transaction ACID.
- *Foreign state mutation* (thay đổi trạng thái ở hệ thống khác): gọi PSP, gửi email, publish lên
  Kafka. Không rollback được. Brandur lưu ý kể cả Kafka trong nhà cũng tính là "bên ngoài".

Nếu request **chỉ** thay đổi DB cục bộ, cách tốt nhất là đặt `INSERT` key, các thay đổi nghiệp vụ và
response vào **cùng một transaction**. Hoặc tất cả cùng commit, hoặc không gì cả; retry sau lỗi sẽ
thấy key chưa có và làm lại từ đầu một cách an toàn. Với endpoint chỉ đổi state cục bộ, Brandur khuyên
ánh xạ mỗi request thành một transaction bất cứ khi nào có thể, vì đơn giản hơn nhiều.

Khi có gọi ra ngoài thì **không thể** gói trong một transaction: không thể giữ transaction mở trong
lúc chờ PSP (giữ lock, giữ connection, module 1.3 của [03-database-sql.md](03-database-sql.md#13-transaction-cơ-bản)),
và rollback DB không huỷ được khoản đã trừ. Brandur chia request thành các *atomic phase* (pha
nguyên tử), mỗi pha là một transaction nằm giữa hai lần gọi ra ngoài, và lưu *recovery point* (điểm
khôi phục) lên chính dòng idempotency key:

```
tx1: INSERT key (recovery_point = started)
tx2: tạo ride + audit record, recovery_point = ride_created
     ── gọi Stripe (foreign, kèm idempotency key riêng) ──
tx3: lưu charge_id, recovery_point = charge_created
tx4: INSERT staged job gửi email, lưu response, recovery_point = finished
```

Retry với cùng key đọc `recovery_point` và nhảy tới đúng pha tiếp theo, không làm lại pha đã xong.
Việc gửi email được đưa thành bản ghi job trong transaction (mẫu outbox, [12-messaging.md](../12-messaging.md)),
nên không còn là gọi ra ngoài trong request.

*Truyền key sang PSP.* Nếu process chết lúc đang chờ PSP, lần retry sẽ gọi PSP lại. Chỉ an toàn khi
lần gọi PSP cũng mang idempotency key, và key đó **giống hệt** lần trước. Brandur tự sinh key cho
Stripe từ id nội bộ của dòng idempotency (không chuyển thẳng key của client), để key gửi sang Stripe là
duy nhất trên mọi user của ứng dụng (key của client chỉ duy nhất trong phạm vi một user). ⚠️ Nếu code xoá dòng key khi lỗi rồi tạo dòng mới lúc retry, id
nội bộ đổi, key gửi PSP đổi theo, và PSP coi đó là khoản thanh toán mới. Vì vậy hoặc giữ dòng (chỉ mở
khoá), hoặc suy key PSP từ thứ ổn định như `(user_id, key của client)`.

Nếu dịch vụ bên ngoài không hỗ trợ idempotency key và lần gọi gặp lỗi mơ hồ (timeout, connection
reset), không biết nó đã chạy hay chưa. Brandur khuyên chọn hướng an toàn: đánh dấu thao tác là thất
bại vĩnh viễn, thay vì đoán mò rồi gọi lại.

*Thời hạn.* Key không phải kho lưu trữ vĩnh viễn, chỉ đảm bảo đúng đắn trong ngắn hạn. Stripe cho
phép dọn key sau ít nhất 24 giờ; dùng lại key sau khi đã bị dọn thì được coi là request mới. Brandur
gợi ý giữ khoảng 72 giờ để nếu deploy lỗi hôm thứ Sáu thì thứ Hai vẫn còn dữ liệu mà hoàn tất các
request dở dang. Một job định kỳ (*reaper*) xoá key quá hạn.

Không chỉ API: form HTML cũng dùng được. Lúc render form, nhúng một `<input type="hidden">` chứa key
sinh sẵn. Bấm submit bao nhiêu lần thì key vẫn thế, server lọc trùng như trên.

#### Queue worker cũng cần idempotency

Hầu hết queue chỉ đảm bảo *at-least-once* (mỗi message được giao ít nhất một lần, có thể nhiều hơn).
Ở tầng Laravel, [05-php-laravel.md](05-php-laravel.md#26-queue) liệt kê năm đường làm job chạy lại;
lý thuyết delivery semantics ở [12-messaging.md](../12-messaging.md).

⚠️ Điều hay bị bỏ sót: hai lần chạy có thể **song song**, không chỉ nối tiếp.

- *Visibility timeout* (SQS; `retry_after` là khái niệm tương đương trong Laravel): worker nhận
  message thì message bị ẩn đi trong một khoảng thời gian. Worker xử lý lâu hơn khoảng đó thì queue
  tưởng worker đã chết và giao message cho worker khác, trong khi worker đầu vẫn đang chạy.
- *Rebalance* (Kafka): consumer group chia lại partition giữa các consumer. Consumer cũ có thể còn
  đang xử lý batch của partition vừa bị lấy đi, trong khi consumer mới đọc lại từ offset đã commit.

| Bước | Worker A | Worker B | Kết quả |
|---|---|---|---|
| 1 | Nhận message M, bắt đầu xử lý | | M bị ẩn 30 giây |
| 2 | Vẫn đang chạy ở giây 31 | | Hết visibility timeout, M hiện lại |
| 3 | | Nhận M, bắt đầu xử lý | Hai worker cùng xử lý M |
| 4 | Kiểm tra "đã xử lý M chưa?": chưa | Kiểm tra "đã xử lý M chưa?": chưa | Check-then-act, cả hai làm |

Vì vậy "kiểm tra xem đã làm chưa" bằng `SELECT` không đủ. Cách chịu được chạy song song là dùng đúng
công cụ của phần idempotency key: một bảng `processed_messages` có unique key trên `message_id`, và
`INSERT` vào bảng đó **trong cùng transaction** với thay đổi nghiệp vụ. Worker thứ hai hoặc chờ lock
rồi nhận lỗi trùng, hoặc nhận lỗi trùng ngay; hiệu ứng chỉ commit một lần. Với việc gọi ra ngoài, lại
cần idempotency key gửi sang bên kia như ở trên.

**Tóm tắt nhanh**
- Request trùng đến từ người dùng, client retry sau timeout, LB retry, mạng; disable nút chỉ là UX.
- Idempotency key do client sinh, retry gửi lại đúng key; server phân xử bằng `INSERT` vào cột
  unique **trước** khi làm việc, không bằng `SELECT` trước.
- Trùng key: khác body thì lỗi (IETF draft: 422), `done` thì trả response cũ, `processing` thì 409;
  key kẹt `processing` cần `locked_at` và chiếm lại bằng `UPDATE` có điều kiện.
- Chỉ ghi DB cục bộ: key và nghiệp vụ chung một transaction. Có gọi ra ngoài: chia atomic phase,
  lưu recovery point, truyền key ổn định sang PSP.
- Queue at-least-once có thể chạy trùng song song: unique `message_id` ghi chung transaction với
  hiệu ứng.

**Nguồn**: [Brandur: Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys) ·
[Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests) ·
[IETF draft: The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)


---

### 2.4 Thread pool, connection pool, Little's law

Module này trả lời: pool để làm gì, đặt kích thước pool (thread, connection, worker PHP-FPM) bằng
cách tính nào, và vì sao "tăng lên cho chắc" thường làm hệ thống chậm đi.

#### Vì sao cần pool

*Pool* là một nhóm tài nguyên đắt (thread, connection DB, process) được tạo sẵn với số lượng có giới
hạn. Việc cần tài nguyên thì mượn, xong thì trả lại cho việc khác dùng. Pool giải hai bài toán:

1. Tái sử dụng. Tạo một thread của hệ điều hành cần cấp bộ nhớ cho stack và gọi vào kernel. Mở một
   connection MySQL cần bắt tay TCP, có thể TLS, rồi xác thực. Làm việc đó cho mỗi request là lãng phí.
2. Giới hạn mức song song. Đây là ý quan trọng hơn. Không có giới hạn thì lúc tải tăng, số thread
   tăng theo cho tới khi hết bộ nhớ, và CPU tốn ngày càng nhiều thời gian cho *context switch* (lưu
   trạng thái thread này, nạp trạng thái thread kia) thay vì làm việc thật.

Tài liệu HikariCP (connection pool phổ biến nhất của Java) giải thích bằng một nguyên lý đơn giản: một
core CPU tại mỗi thời điểm chỉ chạy được một thread; nhiều thread "cùng lúc" chỉ là hệ điều hành chia
lát thời gian. Với một core, chạy A rồi B luôn nhanh hơn chạy A và B xen kẽ. Thread nhiều hơn core chỉ
có lợi khi thread bị **chặn** (chờ đĩa, chờ mạng), vì lúc đó core rảnh để chạy thread khác.

PHP-FPM chính là một pool: pool **process**, mỗi worker xử lý một request một lúc, và
`pm.max_children` là trần mức song song
([05-php-laravel.md](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing)). PHP-FPM không có
connection pool dùng chung: mỗi worker tự giữ connection của mình
([03-database-sql.md](03-database-sql.md#27-tầng-php-pdo-và-laravel)).

#### Chọn kích thước pool

*Việc CPU-bound* (chủ yếu tính toán: resize ảnh, mã hoá, parse lớn): thêm thread không thêm core.
JCIP (ch.8, *Sizing Thread Pools*) khuyên khoảng `số core + 1`; thread dư ra để core không bỏ phí khi
một thread thỉnh thoảng bị dừng (ví dụ page fault).

*Việc I/O-bound* (chủ yếu chờ DB, HTTP): JCIP đưa công thức

```
N_threads = N_cpu × U_cpu × (1 + W / C)

N_cpu : số core
U_cpu : mức dùng CPU mục tiêu, từ 0 tới 1 (1 = muốn dùng hết CPU)
W / C : tỉ lệ thời gian chờ trên thời gian tính của một việc
```

Ví dụ: 8 core, muốn dùng hết CPU (`U_cpu = 1`), mỗi việc chờ DB 90 ms và tính 10 ms:
`8 × 1 × (1 + 90/10) = 80` thread. Trực giác: mỗi thread chỉ dùng CPU 10% thời gian, nên cần khoảng
10 thread để lấp kín một core.

⚠️ `W` và `C` phải **đo** (profiler, APM, log thời gian), không đoán. Và công thức chỉ nói CPU của
**máy này** đủ cho bao nhiêu thread; nó không nói DB phía sau chịu được bao nhiêu (phần "Nhìn cả
chuỗi").

*Connection pool của DB* thì nhìn từ phía DB. HikariCP dẫn công thức khởi điểm do cộng đồng
PostgreSQL đưa ra, và cho rằng dùng được cho phần lớn DB:

```
connections = (core_count × 2) + effective_spindle_count
```

- `core_count` là core vật lý của **máy DB**, không tính hyper-threading.
- `effective_spindle_count` (số đĩa quay hiệu dụng) bằng 0 nếu dữ liệu nóng nằm hết trong cache, và
  tiến tới số đĩa thật khi tỉ lệ cache hit giảm. Công thức này chưa được phân tích kỹ với SSD.
- Ví dụ của HikariCP: máy 4 core, một ổ đĩa: `4 × 2 + 1 = 9`, làm tròn 10.
- ⚠️ Nghe ngược đời nhưng SSD nhanh hơn thì cần **ít** connection hơn, không phải nhiều hơn: ít phải
  chờ đĩa thì ít cơ hội cho thread khác chen vào, nên số tối ưu gần với số core hơn.
- Đây là điểm khởi đầu để load test quanh nó, không phải đáp án.

Hai con số minh hoạ HikariCP dẫn lại: trong video của nhóm Oracle Real-World Performance, chỉ giảm
connection pool (từ 2048 xuống 96, không đổi gì khác) mà thời gian phản hồi giảm từ khoảng 100 ms
xuống khoảng 2 ms; trong một benchmark PostgreSQL, TPS bắt đầu đi ngang quanh 50 connection. Tiên đề
của họ: bạn muốn **một pool nhỏ, và phần còn lại của thread ứng dụng xếp hàng chờ connection**. Chờ
connection ở pool rẻ hơn nhiều so với để DB tự chia CPU cho hàng trăm query cùng lúc.

⚠️ *Pool-locking*: một thread cần giữ nhiều connection cùng lúc (ví dụ hai transaction lồng nhau trên
hai connection) có thể làm pool deadlock: mọi thread đều giữ một connection và chờ connection thứ hai.
HikariCP đưa công thức kích thước **tối thiểu** để không thể deadlock:
`pool = Tn × (Cm − 1) + 1`, với `Tn` là số thread tối đa, `Cm` là số connection tối đa một thread giữ
cùng lúc. Ví dụ 8 thread, mỗi thread cần 3 connection: `8 × 2 + 1 = 17`. Họ khuyên sửa ở tầng ứng dụng
trước khi tăng pool. JCIP gọi hiện tượng cùng họ là *thread starvation deadlock*: việc trong pool gửi
việc con vào **chính pool đó** rồi chờ kết quả, trong khi mọi thread của pool đều đang chờ như vậy.

#### Little's law

*Little's law* là một định lý của lý thuyết hàng đợi:

```
L = λ × W

L : số việc trung bình đang nằm trong hệ thống (đang xử lý + đang xếp hàng)
λ : tốc độ việc đi vào (việc/giây), ở trạng thái ổn định bằng tốc độ việc đi ra
W : thời gian trung bình một việc nằm trong hệ thống
```

Điểm mạnh của nó là gần như không cần giả định: không phụ thuộc phân phối thời điểm đến, phân phối
thời gian phục vụ hay thứ tự phục vụ. Điều kiện là hệ thống ổn định lâu dài (việc vào bằng việc ra).
Và nó áp dụng được cho **hệ thống con**: cả service, riêng hàng đợi, riêng pool connection, mỗi cái một
phép tính.

Ba cách dùng:

1. Tính mức song song cần có. 200 request/giây, mỗi request 50 ms: `L = 200 × 0,05 = 10` request đồng
   thời trung bình. Service cần ít nhất 10 thread (hoặc 10 worker FPM). Nếu chỉ có 8, việc sẽ xếp
   hàng, `W` tăng.
2. Tính connection cần có. Dùng thời gian **giữ connection**, không phải thời gian request. Service
   Java giữ connection 5 ms trong một request 50 ms: `200 × 0,005 = 1` connection bận trung bình.
   PHP-FPM thì khác: worker mở connection ở query đầu và giữ tới hết request, nên số connection bận
   gần bằng số worker bận.
3. Suy ngược thời gian phản hồi. Ví dụ ở Wikipedia: trung bình 10 việc trong hệ thống, throughput 50
   việc/giây, suy ra `W = 10 / 50 = 0,2` giây. Hữu ích khi kiểm tra kết quả load test có hợp lý không.

⚠️ `L` là **trung bình**. Traffic có đỉnh và latency có đuôi dài (p99 lớn hơn nhiều p50). Tính theo λ
giờ cao điểm, W ở điều kiện tải cao, rồi chừa biên. Và khi λ tiến gần năng lực xử lý tối đa, hàng đợi
dài ra rất nhanh: `W` tăng, kéo `L` tăng, đòi thêm tài nguyên đúng lúc không còn.

#### Nhìn cả chuỗi

Một request đi qua nhiều pool nối tiếp. Pool nào nhỏ nhất (tính theo năng lực thật) quyết định
throughput của cả chuỗi (số liệu dưới đây là giả định để minh hoạ):

```
Nginx ──> PHP-FPM (max_children = 80) ──> MySQL (max_connections, CPU, lock) ──> API ngoài
          x 4 server = 320 worker          máy 16 core: vài chục query        rate limit
                                           chạy song song là hiệu quả nhất    100 req/s
```

⚠️ Pool to hơn tài nguyên phía sau là vô ích, thậm chí có hại:

- 200 thread Java cùng cần DB nhưng pool chỉ có 20 connection: 180 thread ngồi chờ ở pool. Đó là
  điều HikariCP **muốn** (chờ ở pool rẻ), miễn là số thread không lớn tới mức tốn bộ nhớ vô ích.
- PHP-FPM không có pool ở giữa, nên tăng `pm.max_children` là tăng thẳng số query chạy song song ở DB.

Vì sao tăng `pm.max_children` có thể làm hệ thống **chậm hơn**, theo từng bước:

1. Thêm worker nghĩa là thêm query đồng thời tới DB. DB đã hết CPU (hoặc đĩa) thì mỗi query chạy chậm
   đi, cộng thêm tranh chấp lock dòng, lock nội bộ và context switch.
2. Mỗi request giữ worker lâu hơn (`W` tăng). Theo Little, `L = λ × W`: cùng lượng traffic mà số worker
   bận tăng lên, càng đẩy thêm query vào DB. Vòng lặp tự khuếch đại.
3. Worker nhiều hơn cũng tốn RAM hơn. Vượt RAM thì máy swap hoặc bị OOM killer
   ([05-php-laravel.md](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing) có cách tính theo
   RAM).
4. Số connection tới MySQL = số server × số worker. Vượt `max_connections` (mặc định 151) thì request
   nhận lỗi 1040 "Too many connections"
   ([03-database-sql.md](03-database-sql.md#27-tầng-php-pdo-và-laravel)).

Cách tiếp cận đúng khi phỏng vấn: nêu giả định (traffic đỉnh, thời gian mỗi request, bao nhiêu phần
là chờ DB), tính bằng Little và JCIP, đối chiếu với trần của DB và RAM, rồi nói sẽ load test để chỉnh.

#### Queue chờ và chính sách từ chối

Pool đầy thì việc mới phải đi đâu đó. Trong Java, `ThreadPoolExecutor` có bộ tham số thể hiện rõ các
lựa chọn:

```java
// Một pool cố định 16 thread, hàng đợi tối đa 100 việc, đầy thì thread gọi tự chạy việc đó
ExecutorService pool = new ThreadPoolExecutor(
        16, 16,                               // corePoolSize, maximumPoolSize
        0L, TimeUnit.MILLISECONDS,            // keepAlive cho thread vượt core
        new ArrayBlockingQueue<>(100),        // hàng đợi CÓ giới hạn
        new ThreadPoolExecutor.CallerRunsPolicy());
```

Thứ tự `ThreadPoolExecutor` xử lý một việc mới: còn dưới `corePoolSize` thì tạo thread mới; đủ core
thì đưa vào queue; queue đầy mới tạo thêm thread tới `maximumPoolSize`; vượt nữa thì gọi chính sách
từ chối (*saturation policy*).

⚠️ `Executors.newFixedThreadPool(n)` dùng `LinkedBlockingQueue` **không giới hạn**. Khi quá tải, không
có lỗi nào: queue cứ dài ra, bộ nhớ tăng, latency tăng vô hạn, và quá tải bị che giấu tới lúc hết
heap. Cũng vì queue không bao giờ đầy nên `maximumPoolSize` không bao giờ có tác dụng với loại queue
này.

Bốn chính sách có sẵn:

| Chính sách | Khi queue đầy | Dùng khi |
|---|---|---|
| `AbortPolicy` (mặc định) | Ném `RejectedExecutionException` cho bên gọi | Muốn báo lỗi rõ ràng, bên gọi tự xử lý (trả 503) |
| `CallerRunsPolicy` | Thread đang gửi việc tự chạy việc đó | Muốn *backpressure*: bên gửi bị chậm lại, tự giảm tốc độ gửi |
| `DiscardPolicy` | Lặng lẽ bỏ việc mới | Việc không quan trọng (metric lấy mẫu) |
| `DiscardOldestPolicy` | Bỏ việc cũ nhất trong queue, thử lại việc mới | Chỉ cần dữ liệu mới nhất |

*Backpressure* là cơ chế để bên nhận quá tải đẩy ngược áp lực về bên gửi, thay vì âm thầm tích việc.

Đối chiếu:

- PHP-FPM: queue chờ là *listen backlog* của socket. Mọi worker bận thì request xếp hàng ở đó; backlog
  đầy thì kernel từ chối kết nối và Nginx trả 502. Cách đọc `listen queue` trên status page ở
  [05-php-laravel.md](05-php-laravel.md#34-php-fpm-ở-mức-vận-hành).
- Go: channel có buffer là queue có giới hạn. Gửi vào channel đầy thì bị chặn (backpressure tự nhiên);
  muốn từ chối ngay thì dùng `select` với nhánh `default`.

#### Pool dùng chung và bulkhead

⚠️ Việc chặn lâu trong một pool dùng chung làm nghẽn mọi thứ khác dùng pool đó. Ví dụ Java kinh
điển: `ForkJoinPool.commonPool()` là pool mặc định cho parallel stream và cho các method `...Async`
của `CompletableFuture` khi không truyền executor. Kích thước mặc định của nó chỉ khoảng số core trừ
một, vì nó được thiết kế cho việc CPU-bound. Gọi HTTP chậm trong đó thì vài request là chiếm hết
thread, và mọi parallel stream ở chỗ khác của ứng dụng đứng chờ theo.

```java
// Sai: I/O chặn trong commonPool
CompletableFuture.supplyAsync(() -> httpClient.fetch(url));
// Đúng hơn: truyền executor riêng dành cho I/O
CompletableFuture.supplyAsync(() -> httpClient.fetch(url), ioExecutor);
```

*Bulkhead* (vách ngăn chia khoang tàu thuỷ, một khoang thủng không làm chìm cả tàu): mỗi dependency
hoặc mỗi loại việc một pool riêng, để dependency A treo chỉ làm cạn pool của A. HikariCP gợi ý cùng ý
ở tầng connection: hệ thống trộn transaction rất dài và rất ngắn thì tạo hai pool (một cho job dài,
một cho query realtime). Với PHP-FPM, cách tương đương là tách pool FPM (hoặc tách deployment) cho
endpoint chậm, như export báo cáo, khỏi endpoint chính. Chi tiết bulkhead ở module 3.3.

Ghi chú Java 21 trở lên: *virtual thread* rẻ tới mức không nên pool chúng; muốn giới hạn số việc gọi
DB đồng thời thì dùng `Semaphore` hoặc chính connection pool làm giới hạn (module 2.6).

**Tóm tắt nhanh**
- Pool để tái sử dụng và, quan trọng hơn, để giới hạn mức song song.
- CPU-bound: khoảng số core (+1). I/O-bound: `N_cpu × U_cpu × (1 + W/C)`, với W/C phải đo.
- Connection pool DB nên nhỏ: khởi điểm `core × 2 + spindle` của máy DB, load test quanh đó.
- `L = λ × W` cho số việc đồng thời; dùng thời gian **giữ** tài nguyên, lấy số giờ cao điểm.
- Chỗ hẹp nhất của chuỗi quyết định; tăng `pm.max_children` khi DB đã bão hoà làm mọi request chậm đi.
- Queue phải có giới hạn và có chính sách khi đầy; tách pool (bulkhead) cho việc chậm.

**Nguồn**: *Java Concurrency in Practice* ch.8 (*Sizing Thread Pools*, *Saturation Policies*) ·
[HikariCP: About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing) ·
[Wikipedia: Little's law](https://en.wikipedia.org/wiki/Little%27s_law)


---

### 2.5 Pattern concurrency trong Go (và đối chiếu Java)

Module này trả lời: viết một worker pool có giới hạn, huỷ được và trả lỗi đúng trong Go thế nào, các
bẫy làm crash hoặc rò goroutine, và Java giải cùng bài toán bằng công cụ gì.

Các ví dụ dưới đây chạy được với Go 1.25 trở lên (cần `sync.WaitGroup.Go` và `for range` trên số
nguyên từ 1.22). Ví dụ `errgroup` cần module ngoài `golang.org/x/sync`; các ví dụ còn lại chỉ dùng
thư viện chuẩn. Lưu vào `main.go` trong một thư mục có `go.mod` (`go mod init demo`) rồi `go run .`.

#### Worker pool

*Goroutine* là một hàm chạy đồng thời, do runtime Go lập lịch lên một số ít thread hệ điều hành. Tạo
goroutine rất rẻ (stack khởi đầu nhỏ, lớn dần khi cần), nên Go khuyến khích dùng nhiều. *Channel* là
đường ống có kiểu để các goroutine gửi và nhận giá trị; gửi vào channel không buffer sẽ chặn cho tới
khi có bên nhận.

*Worker pool*: N goroutine cùng đọc việc từ **một** channel (Go blog gọi việc nhiều hàm cùng đọc một
channel là *fan-out*). Khi hết việc, bên gửi `close(jobs)`; vòng `for j := range jobs` của mỗi worker
tự thoát khi channel đã đóng và đã đọc hết. Số worker chính là trần mức song song.

Trước Go 1.25, mẫu chuẩn là:

```go
wg.Add(1)          // PHẢI gọi trước khi chạy goroutine
go func() {
	defer wg.Done()
	work()
}()
```

⚠️ Bẫy kinh điển là gọi `wg.Add(1)` **bên trong** goroutine: `wg.Wait()` ở goroutine chính có thể chạy
trước khi goroutine con kịp `Add`, thấy bộ đếm bằng 0 và trả về ngay. Go 1.25 thêm hai thứ:

- `wg.Go(f)`: chạy `f` trong goroutine mới và tự lo phần đếm. Theo tài liệu package `sync`, `f` không
  được panic, và nếu WaitGroup đang rỗng thì `Go` phải xảy ra trước `Wait`.
- `go vet` có analyzer mới `waitgroup`, báo các lời gọi `sync.WaitGroup.Add` đặt sai chỗ.

Worker pool hoàn chỉnh: 100 việc, 4 worker, việc số 7 lỗi thì huỷ tất cả và giữ lỗi đầu tiên. Chỉ
dùng thư viện chuẩn:

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"time"
)

type result struct {
	id  int
	val int
}

// process giả lập một việc gọi DB mất 10 ms. Việc số 7 bị lỗi.
func process(ctx context.Context, id int) (int, error) {
	select {
	case <-time.After(10 * time.Millisecond):
	case <-ctx.Done():
		return 0, ctx.Err()
	}
	if id == 7 {
		return 0, errors.New("job 7 lỗi")
	}
	return id * id, nil
}

func main() {
	ctx, cancel := context.WithCancelCause(context.Background())
	defer cancel(nil)

	jobs := make(chan int)
	results := make(chan result)

	// Producer: dừng gửi ngay khi ctx bị huỷ, và luôn close(jobs) khi thoát.
	go func() {
		defer close(jobs)
		for i := 1; i <= 100; i++ {
			select {
			case jobs <- i:
			case <-ctx.Done():
				return
			}
		}
	}()

	// 4 worker: mức song song tối đa là 4, dù có 100 việc.
	var wg sync.WaitGroup
	for range 4 {
		wg.Go(func() {
			for id := range jobs {
				v, err := process(ctx, id)
				if err != nil {
					cancel(err) // huỷ tất cả; chỉ lỗi đầu tiên được giữ làm cause
					return
				}
				select {
				case results <- result{id, v}:
				case <-ctx.Done():
					return
				}
			}
		})
	}
	go func() { wg.Wait(); close(results) }()

	n := 0
	for range results {
		n++
	}
	fmt.Println("xong", n, "việc trước khi dừng")
	fmt.Println("lỗi:", context.Cause(ctx))
}
```

Output (số việc xong trước khi dừng thay đổi mỗi lần chạy, thường trong khoảng 4 tới 7):

```
xong 6 việc trước khi dừng
lỗi: job 7 lỗi
```

Những điểm cần giải thích được khi bị hỏi:

1. Mọi lệnh gửi (`jobs <- i`, `results <- ...`) đều nằm trong `select` với `<-ctx.Done()`. Nếu không,
   khi đã huỷ mà không còn ai nhận, bên gửi kẹt mãi (goroutine leak, phần Pipeline bên dưới).
2. `context.WithCancelCause` (từ Go 1.20) cho phép huỷ kèm lý do; `context.Cause(ctx)` trả lý do
   của lần huỷ **đầu tiên**, các lần gọi `cancel` sau không ghi đè.
3. `close(results)` nằm trong một goroutine riêng chờ `wg.Wait()`: chỉ đóng channel khi chắc chắn
   không còn worker nào gửi, vì gửi vào channel đã đóng là panic.
4. `process` cũng nhận `ctx` và dừng sớm khi bị huỷ. Huỷ trong Go là **hợp tác**: context chỉ phát
   tín hiệu, code phải tự kiểm tra.

#### Giới hạn concurrency

⚠️ Goroutine rẻ, tài nguyên phía sau thì không. Chạy `go` cho từng dòng của file 10 triệu dòng, mỗi
goroutine gọi DB, nghĩa là cùng lúc hàng triệu query đổ vào DB (hoặc hàng triệu goroutine chờ
connection pool, tốn bộ nhớ). Go blog *Pipelines and cancellation* gặp đúng bài toán này ở phiên bản
MD5 song song: tạo một goroutine cho mỗi file có thể cấp phát nhiều bộ nhớ hơn máy có, và sửa bằng
cách dùng một số cố định goroutine đọc file (*bounded parallelism*). Con số giới hạn tính như module
2.4.

Ba cách giới hạn:

- Worker pool như trên: số goroutine cố định.
- Semaphore bằng channel có buffer: `sem := make(chan struct{}, 10)`, mỗi việc `sem <- struct{}{}`
  trước khi làm và `<-sem` khi xong. Tối đa 10 việc chạy cùng lúc.
- `errgroup` với `SetLimit(n)`, gọn nhất khi cần cả giới hạn, huỷ và lỗi.

#### Fan-out/fan-in, errgroup và pipeline

*Fan-in* là gom nhiều channel đầu vào về một channel đầu ra (hàm `merge` trong Go blog): mỗi channel
vào một goroutine chép sang channel ra, cộng một goroutine chờ tất cả xong rồi mới `close` channel ra.

Package `golang.org/x/sync/errgroup` gói sẵn mẫu "chạy N việc, việc nào lỗi thì huỷ phần còn lại, trả
lỗi đầu tiên":

- `errgroup.WithContext(ctx)` trả về một `Group` và một context con. Context con bị huỷ ở lần **đầu
  tiên** một hàm truyền vào `Go` trả lỗi khác nil, hoặc khi `Wait` trả về, tuỳ cái nào tới trước.
- `g.Go(f)` chạy `f` trong goroutine mới. `g.Wait()` chờ tất cả xong rồi trả lỗi khác nil đầu tiên.
- `g.SetLimit(n)`: tối đa n goroutine hoạt động. ⚠️ Khi đã đủ n, lời gọi `g.Go` **chặn goroutine gọi**
  cho tới khi có chỗ. Muốn không chặn thì dùng `g.TryGo(f)`, trả `false` nếu không chạy được.
- Tài liệu ghi `Group` không nên dùng lại cho nhiều tác vụ khác nhau, và `Group` rỗng (zero value) thì
  không giới hạn, không huỷ khi lỗi.

```go
package main

import (
	"context"
	"fmt"
	"time"

	"golang.org/x/sync/errgroup"
)

func fetchUser(ctx context.Context, id int) error {
	select {
	case <-time.After(20 * time.Millisecond):
	case <-ctx.Done():
		return ctx.Err() // thấy huỷ thì dừng sớm
	}
	if id == 3 {
		return fmt.Errorf("user %d: not found", id)
	}
	return nil
}

func main() {
	g, ctx := errgroup.WithContext(context.Background())
	g.SetLimit(2) // tối đa 2 goroutine chạy cùng lúc; Go() sẽ CHẶN khi đã đủ 2

	for id := 1; id <= 10; id++ {
		g.Go(func() error { // từ Go 1.22 mỗi vòng lặp có biến id riêng
			return fetchUser(ctx, id)
		})
	}
	if err := g.Wait(); err != nil {
		fmt.Println("lỗi đầu tiên:", err)
	}
}
```

Output: `lỗi đầu tiên: user 3: not found`. Sau khi user 3 lỗi, context bị huỷ; các lời gọi
`fetchUser` sau đó trả `context.Canceled` ngay, nhưng `Wait` chỉ trả lỗi **đầu tiên**. Vòng `for` vẫn
tiếp tục gọi `g.Go` cho các id còn lại (chúng thoát ngay); muốn dừng giao việc sớm thì kiểm tra
`ctx.Err()` trong vòng lặp.

*Pipeline* (theo Go blog): chuỗi các *stage* (công đoạn) nối bằng channel. Mỗi stage nhận giá trị từ
channel vào, xử lý, gửi sang channel ra. Stage đầu là *source* (nguồn), stage cuối là *sink*
(đích). Throughput của cả pipeline bị giới hạn bởi stage chậm nhất, nên fan-out thường áp cho đúng
stage đó.

Go blog đưa hai quy tắc dựng pipeline:

1. Stage đóng channel ra khi đã gửi xong.
2. Stage nhận tiếp từ channel vào cho tới khi channel đó đóng, **hoặc** bên gửi được giải phóng.

⚠️ Goroutine leak khi consumer thoát sớm: stage trước vẫn cố gửi giá trị tiếp theo, không ai nhận, nên
nó kẹt mãi ở lệnh gửi. Goroutine **không được garbage collect**; nó phải tự thoát. Goroutine kẹt còn
giữ tham chiếu tới dữ liệu trên heap, nên rò cả bộ nhớ. Go blog xét rồi loại cách "thêm buffer cho
channel", vì kích thước buffer phụ thuộc vào việc biết trước bên nhận đọc bao nhiêu giá trị, rất dễ
vỡ. Cách đúng là một channel `done` dùng chung: `close(done)` là tín hiệu phát tới **mọi** goroutine
cùng lúc, vì nhận từ channel đã đóng luôn trả về ngay. Ngày nay `ctx.Done()` đóng đúng vai trò đó.

```go
package main

import (
	"fmt"
	"runtime"
	"time"
)

// gen gửi n số vào channel. Không có cách nào bảo nó dừng.
func gen(n int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for i := range n {
			out <- i // kẹt ở đây mãi nếu không ai đọc nữa
		}
	}()
	return out
}

// genDone giống gen nhưng dừng khi done bị close.
func genDone(done <-chan struct{}, n int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for i := range n {
			select {
			case out <- i:
			case <-done:
				return
			}
		}
	}()
	return out
}

func firstLeaky() int {
	for v := range gen(1000) {
		return v // consumer thoát sớm, goroutine của gen bị bỏ rơi
	}
	return -1
}

func firstFixed() int {
	done := make(chan struct{})
	defer close(done) // mọi đường return đều báo cho stage trước dừng
	for v := range genDone(done, 1000) {
		return v
	}
	return -1
}

func main() {
	for range 100 {
		firstFixed()
	}
	time.Sleep(50 * time.Millisecond)
	fmt.Println("sau 100 lần firstFixed:", runtime.NumGoroutine(), "goroutine")

	for range 100 {
		firstLeaky()
	}
	time.Sleep(50 * time.Millisecond)
	fmt.Println("sau 100 lần firstLeaky:", runtime.NumGoroutine(), "goroutine")
}
```

Output:

```
sau 100 lần firstFixed: 1 goroutine
sau 100 lần firstLeaky: 101 goroutine
```

Mỗi lần gọi `firstLeaky` bỏ lại một goroutine kẹt ở `out <- i`. Trong một server, hàm như vậy chạy
theo mỗi request, số goroutine tăng dần cho tới khi hết bộ nhớ. Cách phát hiện: theo dõi
`runtime.NumGoroutine()` theo thời gian, hoặc xem profile goroutine qua `net/http/pprof`.

#### Bẫy thường gặp

*Biến vòng lặp trước Go 1.22.* Trước 1.22, biến của vòng `for` có phạm vi **cả vòng lặp**: mọi lần lặp
dùng chung một biến. Closure chạy muộn (goroutine, hàm lưu lại) nên thường thấy giá trị cuối. Ví dụ
trong bài *Fixing For Loops in Go 1.22*: ba goroutine in `v` của `[]string{"a", "b", "c"}` thường in
"c", "c", "c". Bug này không cần goroutine mới xảy ra; append các closure `func() { fmt.Println(i) }`
vào slice rồi gọi sau cũng dính.

Từ Go 1.22, mỗi lần lặp có biến riêng. ⚠️ Ngữ nghĩa mới **chỉ áp dụng cho package thuộc module khai
báo `go 1.22` trở lên trong `go.mod`**. Module cũ khai báo `go 1.21` vẫn giữ ngữ nghĩa cũ dù biên dịch
bằng Go mới. Vì vậy code cũ có dòng `v := v` (như ví dụ trong tài liệu errgroup) giờ là thừa với
module mới, nhưng xoá đi trong module cũ thì thành bug.

*Ghi `map` đồng thời.* Map thường của Go không an toàn cho truy cập đồng thời. Hai goroutine cùng ghi
thì runtime phát hiện và dừng cả process với `fatal error: concurrent map writes`. ⚠️ Đây là fatal
error, **không phải panic**: `recover` không bắt được. Một goroutine ghi, goroutine khác đọc cũng có
thể bị phát hiện tương tự (`concurrent map read and map write`). Sửa:

- `sync.Mutex` (hoặc `sync.RWMutex`) bọc map. Đây là lựa chọn mặc định.
- `sync.Map`: tài liệu package `sync` nói rõ nó "chuyên biệt", hầu hết code nên dùng map thường kèm
  lock để có type safety và dễ giữ các bất biến khác. `sync.Map` chỉ tối ưu cho hai trường hợp: key
  được ghi một lần nhưng đọc nhiều lần (cache chỉ lớn dần), hoặc các goroutine đọc ghi trên các tập
  key tách biệt nhau.
- Chạy test với `go test -race` (race detector) để bắt các truy cập đồng thời không đồng bộ mà runtime
  chưa kịp phát hiện.

#### Channel hay mutex

Go có câu nổi tiếng trong Effective Go: *"Do not communicate by sharing memory; instead, share memory
by communicating."* Bài *Share Memory By Communicating* minh hoạ bằng chương trình poll danh sách URL:

- Cách truyền thống: một slice resource dùng chung, mỗi resource có cờ `polling`, mọi thread phải khoá
  mutex để tìm resource rảnh, đánh dấu, rồi khoá lại lần nữa để cập nhật. Dài cả trang và dễ sai.
- Cách Go: hàm `Poller` nhận resource từ channel `in`, xử lý, gửi sang channel `out`. Resource nằm
  trong tay đúng một goroutine tại một thời điểm, nên không cần cờ, không cần lock.

Ý chính là **chuyển quyền sở hữu**: gửi con trỏ qua channel nghĩa là "từ giờ bên kia giữ nó". Nhưng
channel không phải lúc nào cũng tốt hơn:

| Tình huống | Chọn | Vì sao |
|---|---|---|
| Giao việc cho worker, chuyển dữ liệu giữa các stage | Channel | Chuyển quyền sở hữu, có backpressure tự nhiên |
| Báo "dừng lại" cho nhiều goroutine | `close` channel / `context` | Phát tín hiệu tới tất cả cùng lúc |
| Bộ đếm, cache, một struct state nhỏ nhiều goroutine cùng đọc sửa | `sync.Mutex` | Đơn giản, rõ, nhanh hơn dựng goroutine giữ state |
| Một con số đơn lẻ | `sync/atomic` | Module 2.1 |

#### Đối chiếu Java

| Việc | Go | Java |
|---|---|---|
| Thread pool / worker pool | N goroutine đọc một channel | `ExecutorService` (`Executors.newFixedThreadPool(n)` hoặc `ThreadPoolExecutor`, module 2.4) |
| Chạy việc bất đồng bộ, nối và gộp kết quả | goroutine + channel, `errgroup` | `CompletableFuture` (`thenApply`, `thenCombine`, `allOf`) |
| Huỷ | `context`, hợp tác | `Future.cancel(true)` gửi interrupt; thread phải tự kiểm tra, cũng là hợp tác |
| "Chưa có thì tính và lưu", an toàn đồng thời | map + mutex, `sync.Map.LoadOrStore` | `ConcurrentHashMap.computeIfAbsent` |
| Nhóm việc con: một cái lỗi thì huỷ phần còn lại | `errgroup.WithContext` | Structured concurrency (`StructuredTaskScope`), còn preview tới JDK 27 |

Vài điểm cần nói rõ:

- `ConcurrentHashMap.computeIfAbsent(key, fn)` thực hiện atomic cho từng key: hai thread cùng hỏi một
  key thì `fn` chỉ chạy một lần, thread kia chờ và nhận kết quả. ⚠️ Cách "check rồi put" (`if
  (!map.containsKey(k)) map.put(k, compute())`) là check-then-act, hai thread cùng tính và ghi. Javadoc
  yêu cầu `fn` ngắn gọn và không được sửa chính map đó trong lúc tính.
- ⚠️ `CompletableFuture` không có huỷ theo nhóm: một future lỗi thì các future khác vẫn chạy tiếp, và
  `cancel` trên `CompletableFuture` không interrupt thread đang chạy. Đó là khoảng trống mà
  `errgroup` bên Go (và structured concurrency bên Java) lấp vào.
- Từ JDK 19, `ExecutorService` là `AutoCloseable`: dùng trong `try (var ex = ...) { ... }` thì cuối
  khối sẽ chờ các việc đã gửi chạy xong.
- *Structured concurrency*: gom các việc con thành một khối có phạm vi rõ ràng; khối kết thúc khi mọi
  việc con xong, một việc lỗi thì các việc còn lại bị huỷ, và không việc con nào sống lâu hơn khối cha.
  Đây đúng là thứ `errgroup` làm. Nó vẫn là preview API, cần `--enable-preview`: JDK 25 LTS là lần
  preview thứ năm (JEP 505), JDK 26 lần thứ sáu (JEP 525), JDK 27 lần thứ bảy (JEP 533). JEP 543 đề
  xuất đưa thành final nhưng mới ở trạng thái Candidate, chưa gắn với bản JDK nào. API đã đổi qua các
  lần preview (JDK 25 thay constructor bằng các method `open`), nên kiểm tra lại ở bản JDK đang dùng.
- Với virtual thread (JDK 21), Java tiến gần mô hình goroutine: tạo một virtual thread cho mỗi việc,
  không pool, giới hạn tài nguyên phía sau bằng `Semaphore` (module 2.6).

```java
// Gộp hai việc I/O song song bằng CompletableFuture, dùng executor riêng (không dùng commonPool)
try (ExecutorService io = Executors.newFixedThreadPool(8)) {
    CompletableFuture<User> user = CompletableFuture.supplyAsync(() -> loadUser(id), io);
    CompletableFuture<List<Order>> orders = CompletableFuture.supplyAsync(() -> loadOrders(id), io);
    Profile profile = user.thenCombine(orders, Profile::new).join();   // join ném lỗi nếu một bên lỗi
}
```

**Tóm tắt nhanh**
- Worker pool = N goroutine đọc một channel; `close(jobs)` để kết thúc; Go 1.25 có `wg.Go`, và `go vet`
  bắt `Add` đặt sai chỗ.
- Goroutine rẻ nhưng DB thì không: luôn giới hạn bằng pool, semaphore hoặc `errgroup.SetLimit`.
- `errgroup.WithContext`: lỗi đầu tiên huỷ context và được `Wait` trả về; `Go` chặn khi đủ limit.
- Mọi lệnh gửi phải `select` với `ctx.Done()`; consumer thoát sớm mà không báo thì goroutine leak.
- Map thường ghi đồng thời là fatal error không recover được; biến vòng lặp riêng từng lần chỉ khi
  `go.mod` khai báo `go 1.22+`.
- Java: `ExecutorService`, `CompletableFuture`, `computeIfAbsent`; structured concurrency còn preview ở
  JDK 25, 26 và 27.

**Nguồn**: [Go blog: Pipelines and cancellation](https://go.dev/blog/pipelines) ·
[Go blog: Share Memory By Communicating](https://go.dev/blog/codelab-share) ·
[Go blog: Fixing For Loops in Go 1.22](https://go.dev/blog/loopvar-preview) ·
[errgroup](https://pkg.go.dev/golang.org/x/sync/errgroup) ·
[sync: WaitGroup.Go, Map](https://pkg.go.dev/sync) ·
[Go 1.25 release notes](https://go.dev/doc/go1.25) ·
[JEP 533: Structured Concurrency (Seventh Preview)](https://openjdk.org/jeps/533)

---

### 2.6 Mô hình chạy: process, thread, event loop, goroutine, virtual thread

Module này trả lời: khi có một nghìn request cùng lúc, mỗi runtime (PHP-FPM, Java cổ điển, Node.js,
Go, Java virtual thread) "chở" chúng bằng cái gì, request chờ I/O thì cái gì đứng yên, request làm CPU
nặng thì ai bị vạ lây, và vì sao goroutine hay virtual thread không phải phép màu.

#### Các khái niệm cần biết trước

*Blocking I/O*: luồng gọi `read()` trên socket DB rồi đứng im tới khi có dữ liệu. Trong lúc đó luồng
không làm được gì khác, nhưng vẫn chiếm tài nguyên của mình (stack, một slot trong pool, một worker).

*Non-blocking I/O*: luồng đăng ký "báo tôi khi socket này có dữ liệu" với hệ điều hành rồi đi làm việc
khác. Hệ điều hành theo dõi hàng nghìn socket cùng lúc bằng cơ chế như `epoll` (Linux), `kqueue`
(macOS/BSD), IOCP (Windows).

*Event loop*: một thread chạy vòng lặp:

```
while (còn việc):
    sự_kiện = hỏi OS "socket/timer nào đã sẵn sàng?"   (epoll_wait, kqueue...)
    for mỗi sự kiện:
        chạy callback đã đăng ký cho sự kiện đó         (chạy trọn, không ai chen ngang)
```

Nhờ vậy một thread phục vụ được rất nhiều kết nối. Cái giá: callback nào chạy lâu thì mọi kết nối
khác phải chờ, vì chỉ có một thread chạy code ứng dụng.

*M:N scheduling*: runtime tự xếp M luồng nhẹ (goroutine, virtual thread) lên N thread hệ điều hành, M
lớn hơn N rất nhiều. So sánh: thread Java cổ điển là 1:1 (mỗi `Thread` là một thread OS); "green
thread" thời Java đầu tiên là M:1 (mọi thread chung một thread OS) và đã bị bỏ.

*Park / mount / unmount*: khi luồng nhẹ gọi một thao tác sẽ chờ (đọc socket, `sleep`, lấy lock),
runtime cất trạng thái của nó (stack) sang một bên, gọi là *park* hay *unmount*, rồi cho luồng nhẹ khác
chạy trên chính thread OS đó (*mount*). Khi I/O xong, luồng nhẹ được đưa lại vào hàng chờ lập lịch.

*Function coloring* (Bob Nystrom, 2015): trong ngôn ngữ dùng callback, promise hay async/await, hàm
chia thành hai "màu":

- Hàm đồng bộ (xanh) trả giá trị bình thường.
- Hàm async (đỏ) trả một `Promise`/`Future`/`Task`, và chỉ lấy được kết quả bằng `await` bên trong
  một hàm async khác.

Hàm xanh không gọi được hàm đỏ mà lấy ngay kết quả, nên một hàm ở sâu bên dưới chuyển sang async là
kéo cả chuỗi gọi phía trên phải đổi màu theo. Gốc rễ, theo Nystrom: async/await là trình biên dịch cắt
hàm thành nhiều mảnh closure (continuation-passing style) nằm trên heap, nên phải "gỡ" cả call stack về
event loop. Ngôn ngữ có nhiều call stack độc lập chuyển qua lại được (thread, goroutine, coroutine
của Lua, fiber của Ruby) thì không bị tô màu: gặp I/O chỉ cần treo cả call stack đó lại.

Trong thế giới PHP, cả hai kiểu đều có (chi tiết ở module 2.7):

- ReactPHP dùng callback và promise: có màu, giống Node.js.
- AMPHP v3 và `react/async` dựa trên Fiber (PHP 8.1): Fiber có call stack riêng nên hàm gọi `await()`
  không phải đổi chữ ký. Nhưng vẫn cần event loop và driver I/O viết riêng cho loop đó.
- Swoole/OpenSwoole coroutine có *runtime hook*: bật hook thì PDO (mysqlnd), phpredis, curl,
  `file_get_contents`, `sleep` tự trở thành non-blocking bên trong coroutine, code trông đồng bộ như
  Go. ⚠️ Mỗi worker process vẫn chỉ có một thread chạy coroutine, nên việc CPU nặng vẫn chặn mọi
  coroutine của worker đó, như event loop.

#### So sánh năm mô hình

| Mô hình | Đơn vị chở request | Khi chờ I/O | Chi phí mỗi đơn vị | Giới hạn thực tế |
|---|---|---|---|---|
| PHP-FPM | Một process worker | Process đứng chờ, không làm gì khác | Cả một process PHP; với app Laravel thường hàng chục MB mỗi worker (tuỳ app, đo bằng PSS) | Số request đồng thời bằng `pm.max_children` |
| Thread OS (Java cổ điển, Tomcat) | Một thread OS, thường lấy từ pool | OS cho thread khác chạy | Stack dành sẵn cỡ MB (mặc định 1 MB trên Linux x64, 2 MB trên macOS arm64; chỉnh bằng `-Xss`), cộng chi phí context switch | Vài trăm tới vài nghìn thread |
| Event loop (Node.js, ReactPHP, AMPHP, Swoole coroutine) | Một callback hoặc một coroutine trên loop | Đăng ký với OS rồi quay về loop | Một closure/promise trên heap | Rất nhiều kết nối, nhưng chỉ một thread chạy code |
| Goroutine (Go) | Một goroutine, M:N | Runtime park goroutine, thread OS chạy goroutine khác | Stack khởi đầu vài KB, tự lớn lên | Hàng trăm nghìn goroutine |
| Virtual thread (Java 21+) | Một virtual thread, M:N trên *carrier thread* | JVM unmount virtual thread khỏi carrier | Stack là object trên heap, co giãn | Hàng triệu virtual thread |

Chi tiết từng mô hình:

**PHP-FPM.** Mỗi worker là một process xử lý trọn một request rồi mới nhận request tiếp. Không có biến
nào dùng chung giữa hai request (share-nothing). Muốn 200 request đồng thời thì cần 200 worker, và RAM
tăng theo. Cách tính `pm.max_children` theo RAM và theo Little's law ở module 2.4 và
[05-php-laravel.md, module 2.2](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing).

**Thread OS.** Mô hình *thread-per-request*: mỗi request một thread từ đầu tới cuối. Dễ viết, dễ debug
(stack trace, profiler, debugger đều hiểu thread). Vấn đề là thread OS đắt nên phải giới hạn bằng pool.
JEP 444 nêu rõ: pool giúp tránh chi phí tạo thread, nhưng không tăng tổng số thread, nên số thread trở
thành giới hạn throughput trước cả CPU hay số connection mạng.

Ví dụ Little's law trong JEP 444: latency trung bình 50 ms, muốn 200 request/giây thì cần 10 request
đồng thời; muốn 2000 request/giây thì cần 100. Mỗi request giữ một thread suốt thời gian chờ, nên số
thread phải tăng theo throughput.

**Event loop (Node.js).** Theo tài liệu "Don't Block the Event Loop", Node.js có hai loại thread:

- Một event loop chạy toàn bộ JavaScript của bạn (callback, phần code giữa các `await`) và I/O mạng
  non-blocking.
- Một *Worker Pool* gồm k thread do libuv quản lý, chạy những việc OS không có bản non-blocking hoặc
  tốn CPU: phần lớn API `fs`, `dns.lookup()`, `crypto.pbkdf2()`, `crypto.scrypt()`, `zlib`.

Hai loại thread này, mỗi thread tại một thời điểm chỉ làm một việc. Với Apache kiểu một thread mỗi
client, OS tự chia lượt công bằng; với Node.js, chia lượt công bằng là **trách nhiệm của code ứng
dụng**. Những thứ hay chặn loop mà tài liệu nêu:

- Regex dễ bị *ReDoS* (thời gian khớp tăng theo cấp số mũ với input xấu), ví dụ `/(\/.+)+$/`.
- `JSON.parse`/`JSON.stringify` trên dữ liệu lớn: ví dụ trong tài liệu, chuỗi 50 MB mất khoảng 0,7
  giây để stringify và 1,3 giây để parse.
- API đồng bộ trong server: `crypto.pbkdf2Sync`, `zlib.inflateSync`, `fs.readFileSync`,
  `child_process.execSync`.

Cách xử lý việc nặng: *partitioning* (chia nhỏ, mỗi mảnh xong thì `setImmediate` mảnh sau để nhường
loop) hoặc *offloading* (đẩy sang worker thread hay child process, trả giá serialize dữ liệu qua lại).

**Goroutine.** Mỗi request HTTP trong `net/http` chạy trên một goroutine riêng. Bạn viết code đồng bộ
bình thường (`rows, err := db.Query(...)`); khi goroutine chờ mạng, runtime park nó và cho goroutine
khác chạy. Số thread OS chạy code Go song song bằng `GOMAXPROCS`, mặc định bằng số CPU logic. Từ Go
1.25, trên Linux, mặc định này còn tính tới CPU limit của cgroup (tức "CPU limit" của container
Kubernetes), và được runtime cập nhật định kỳ.

**Virtual thread.** Một instance `java.lang.Thread` không gắn cố định với thread OS nào (JEP 444, final
ở JDK 21). Bộ lập lịch là một `ForkJoinPool` riêng, chạy chế độ FIFO, với số carrier mặc định bằng
số CPU (chỉnh bằng `jdk.virtualThreadScheduler.parallelism`). Pool này khác `ForkJoinPool.commonPool`
mà parallel stream dùng.

Ví dụ giới hạn số lời gọi DB bằng `Semaphore` khi dùng virtual thread (đã chạy thử với
`java VtSemaphore.java`):

```java
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;

public class VtSemaphore {
    // Tối đa 20 lời gọi "DB" cùng lúc, giống pool 20 connection
    private static final Semaphore DB_PERMITS = new Semaphore(20);
    private static final AtomicInteger inFlight = new AtomicInteger();
    private static final AtomicInteger maxSeen = new AtomicInteger();

    public static void main(String[] args) {
        long start = System.nanoTime();
        try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 10_000; i++) {           // 10.000 virtual thread, mỗi task một cái
                executor.submit(() -> {
                    DB_PERMITS.acquireUninterruptibly();
                    try {
                        maxSeen.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                        Thread.sleep(10);                // giả lập query 10 ms: virtual thread được unmount
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    } finally {
                        inFlight.decrementAndGet();
                        DB_PERMITS.release();
                    }
                });
            }
        }                                                // close() chờ mọi task xong
        System.out.println("tối đa đồng thời: " + maxSeen.get());   // tối đa đồng thời: 20
        System.out.println("thời gian ~" + (System.nanoTime() - start) / 1_000_000 + " ms");
        // khoảng 10.000 / 20 × 10 ms = 5 giây cộng chi phí, tuỳ máy (lần chạy thử: ~6100 ms)
    }
}
```

⚠️ Đừng pool virtual thread. JEP 444 nói thẳng: virtual thread rẻ nên mỗi task một cái mới; muốn giới
hạn truy cập một tài nguyên thì dùng `Semaphore` như trên, đừng dùng `newFixedThreadPool(20)` như
thói quen cũ.

⚠️ Code cũ hay cất tài nguyên đắt (connection, formatter) vào `ThreadLocal` để các task trên cùng một
thread trong pool dùng lại. Chuyển sang virtual thread thì mỗi task một thread, nên thủ thuật này thành
tạo tài nguyên đắt cho **mỗi** task.

#### Việc CPU nặng 2 giây: ai bị vạ lây

Đây là câu hỏi phân biệt các mô hình rõ nhất.

| Mô hình | Chuyện gì xảy ra | Vì sao |
|---|---|---|
| Node.js event loop | Mọi request khác trên process đó đứng chờ 2 giây, kể cả timer | Chỉ một thread chạy JavaScript |
| PHP-FPM | Chỉ worker đó bận; worker khác phục vụ bình thường | Mỗi request một process riêng |
| Thread OS | Các thread khác vẫn chạy | OS chia lượt (time slicing) giữa các thread |
| Goroutine | Goroutine khác vẫn chạy, kể cả khi `GOMAXPROCS=1` | Từ Go 1.14 runtime preempt (giành lại) goroutine chạy quá lâu, cỡ 10 ms, kể cả vòng lặp không gọi hàm |
| Virtual thread | Chiếm trọn một carrier trong 2 giây; nếu mọi carrier đều bận CPU thì virtual thread khác phải chờ | JEP 444: bộ lập lịch **không** có time sharing cho virtual thread |

Chạy thử ba bản dưới đây (Node 25, JDK 26, Go 1.26, trên Mac):

```js
// block.js, chạy: node block.js
const start = Date.now();
const t = () => `${Date.now() - start} ms`;
setTimeout(() => console.log('timer 100 ms chạy lúc', t()), 100);
setTimeout(() => {
  console.log('bắt đầu việc CPU lúc', t());
  while (Date.now() - start < 2050) {}          // bận CPU khoảng 2 giây
  console.log('xong việc CPU lúc', t());
}, 50);
// bắt đầu việc CPU lúc 51 ms
// xong việc CPU lúc 2050 ms
// timer 100 ms chạy lúc 2050 ms     <- hẹn 100 ms nhưng trễ gần 2 giây
```

```java
// VtNoTimeSlice.java, chạy: java -Djdk.virtualThreadScheduler.parallelism=1 VtNoTimeSlice.java
public class VtNoTimeSlice {
    public static void main(String[] args) throws InterruptedException {
        long start = System.nanoTime();
        Thread cpu = Thread.ofVirtual().start(() -> {
            while (System.nanoTime() - start < 2_000_000_000L) { }   // bận CPU 2 giây
        });
        Thread.sleep(10);                                             // để cpu chiếm carrier trước
        Thread other = Thread.ofVirtual().start(() ->
            System.out.println("other chạy sau " + (System.nanoTime() - start) / 1_000_000 + " ms"));
        cpu.join();
        other.join();
    }
}
// Với parallelism=1: other chạy sau 2000 ms
// Không đặt parallelism (nhiều carrier): other chạy sau 14 ms
```

```go
// main.go, chạy: GOMAXPROCS=1 go run main.go
package main

import (
	"fmt"
	"time"
)

func main() {
	start := time.Now()
	go func() {
		for time.Since(start) < 2*time.Second { // bận CPU 2 giây
		}
	}()
	time.Sleep(10 * time.Millisecond)
	done := make(chan struct{})
	go func() {
		fmt.Println("other chạy sau", time.Since(start).Round(time.Millisecond))
		close(done)
	}()
	<-done
}
// other chạy sau 14ms   (dù chỉ có một thread chạy code Go)
```

Con số ms là của một lần chạy, máy khác sẽ lệch chút ít; hình dạng kết quả thì không đổi.

#### Virtual thread chi tiết

*Pinning*: virtual thread bị "ghim" vào carrier, nên khi nó chặn thì carrier (và thread OS bên dưới)
cũng bị chặn theo. Pinning không làm chương trình sai, nhưng làm mất khả năng mở rộng: đủ nhiều
virtual thread bị ghim cùng lúc là hết carrier, các virtual thread khác đứng chờ, thậm chí deadlock.

Theo phiên bản JDK:

| JDK | Trạng thái |
|---|---|
| 21–23 (JEP 444) | Bị ghim khi chặn **bên trong** `synchronized` (hoặc khi chờ để vào một `synchronized` mà thread khác đang giữ, hoặc `Object.wait()`), và khi chạy native method / foreign function. Lời khuyên hồi đó: `synchronized` nào chạy thường xuyên và bọc I/O dài thì đổi sang `ReentrantLock`. Công cụ: `-Djdk.tracePinnedThreads=full`, sự kiện JFR `jdk.VirtualThreadPinned` (bật mặc định, ngưỡng 20 ms) |
| 24 trở đi (JEP 491), gồm 25 LTS | JVM theo dõi monitor theo virtual thread thay vì theo carrier, nên virtual thread unmount được khi ở trong `synchronized`, khi chờ vào monitor, và trong `Object.wait()`. Không cần đổi `synchronized` sang `ReentrantLock` vì lý do này nữa (code đã đổi thì không cần đổi lại). `jdk.tracePinnedThreads` bị bỏ |
| Vẫn còn ghim ở 24+ | Native method hoặc Foreign Function & Memory API gọi ngược lại Java rồi chặn; chặn trong lúc load class hay trong class initializer (`static {}`); chờ class khác khởi tạo xong. JFR `jdk.VirtualThreadPinned` vẫn còn để bắt các ca này |

Vì sao JDK 21 phải ghim trong `synchronized`: JVM ghi nhận **carrier** là chủ monitor. Nếu virtual
thread unmount giữa chừng, một virtual thread khác mount lên đúng carrier đó sẽ được JVM coi là đang
giữ monitor, và mất tính loại trừ. JEP 491 sửa chính chỗ ghi nhận này.

Lời khuyên sau JEP 491 (trích ý JEP, dựa theo JCIP §13.4): code mới dùng `synchronized` khi đủ, dùng
`ReentrantLock` khi cần tính năng thêm (tryLock có timeout, fair lock, nhiều condition). Dù dùng cái
nào, vẫn giữ khoá ngắn và tránh I/O khi đang giữ khoá.

Vài đặc điểm khác của virtual thread nên biết:

- Luôn là daemon thread, priority cố định `NORM_PRIORITY`; `setPriority` không có tác dụng.
- `Thread.currentThread()` trả về chính virtual thread, không phải carrier.
- Thread dump kiểu cũ (`jstack`) không liệt kê virtual thread; dùng
  `jcmd <pid> Thread.dump_to_file -format=json <file>`.
- `ThreadMXBean.findDeadlockedThreads()` chỉ tìm deadlock giữa platform thread.

*ScopedValue* (final ở JDK 25, JEP 506): cách truyền dữ liệu bất biến từ hàm gọi xuống mọi hàm con
(và sang thread con trong structured concurrency) mà không phải thêm tham số. JEP chỉ ra ba nhược
điểm của `ThreadLocal`: ai cũng `set` được bất cứ lúc nào, giá trị sống tới khi thread chết hoặc có ai
gọi `remove()` (quên là rò dữ liệu sang task sau trong pool), và thread con kế thừa thì phải chép cả
bộ. Với hàng triệu virtual thread, chi phí này đáng kể.

```java
private static final ScopedValue<String> USER = ScopedValue.newInstance();

void serve(Request req) {
    ScopedValue.where(USER, req.userId())
               .run(() -> handle(req));   // trong run(): mọi hàm con gọi USER.get() thấy userId
}                                          // ra khỏi run(): USER không còn được gán, get() ném exception
```

Không có `set`: hàm con muốn đổi giá trị cho các hàm con của nó thì mở một `where(...).run(...)` lồng
bên trong; ra khỏi khối đó, giá trị cũ trở lại. *Structured concurrency* (JEP 505, gom các task con
thành một khối, tương tự `errgroup` của Go) vẫn ở dạng preview trong JDK 25.

#### Ý chính

- Goroutine và virtual thread cho bạn viết code blocking, đồng bộ, dễ đọc, với khả năng mở rộng gần
  bằng async. Không có function coloring.
- Chúng **không** làm code chạy nhanh hơn. JEP 444: virtual thread mang lại *scale* (throughput cao
  hơn), không mang lại *speed* (latency thấp hơn). Chúng có lợi khi số task đồng thời lớn (hơn vài
  nghìn) **và** công việc không CPU-bound.
- Chúng **không** bỏ được giới hạn phía sau. 100.000 goroutine vẫn chỉ có 20 connection DB; phần còn
  lại xếp hàng chờ pool (module 2.4). Tài nguyên thật vẫn phải giới hạn bằng semaphore, pool, rate limit.
- PHP-FPM ở chiều ngược lại: đắt RAM, số đồng thời thấp, nhưng cô lập tuyệt đối. Một request CPU nặng
  hay rò bộ nhớ chỉ ảnh hưởng một worker.

**Tóm tắt nhanh**

- PHP-FPM: process mỗi request, chờ I/O là process đứng im, số đồng thời bằng số worker. Thread OS:
  1:1, stack cỡ MB, giới hạn vài nghìn. Event loop: một thread chạy code, không được chặn.
  Goroutine và virtual thread: M:N, runtime park luồng nhẹ khi chờ I/O.
- CPU nặng 2 giây: Node đứng cả process; FPM chỉ một worker bận; Go preempt được; virtual thread
  không có time sharing nên chiếm trọn một carrier.
- Pinning: JDK 21–23 ghim trong `synchronized`; JDK 24+ (JEP 491, có trong 25 LTS) hết, chỉ còn native
  / FFM, class loading, class initializer.
- Không pool virtual thread, giới hạn tài nguyên bằng `Semaphore`. `ScopedValue` final ở JDK 25 thay
  `ThreadLocal` cho context bất biến.
- Async/await gây function coloring; goroutine, virtual thread, Swoole coroutine có hook thì không.

**Nguồn**: [JEP 444: Virtual Threads](https://openjdk.org/jeps/444) ·
[JEP 491: Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491) ·
[JEP 506: Scoped Values](https://openjdk.org/jeps/506) ·
[Node.js: Don't Block the Event Loop (or the Worker Pool)](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop) ·
[What Color is Your Function?](https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/) ·
[Go 1.25 release notes: Container-aware GOMAXPROCS](https://go.dev/doc/go1.25)


---

### 2.7 Tầng PHP: FPM, Laravel, Octane, async

Module này trả lời: PHP không có thread thì race condition nằm ở đâu, Laravel có sẵn công cụ nào
để chặn từng loại race (và mỗi công cụ **không** chặn được gì), và cái gì thay đổi khi app chuyển sang
Octane hoặc chạy nhiều việc song song trong một request.

#### PHP-FPM share-nothing

Mỗi request chạy trong một worker process riêng; hết request, mọi biến, static, singleton đều bị huỷ
([05-php-laravel.md, module 2.2](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing)). Hai
request không bao giờ cùng đụng một vùng nhớ userland, nên code PHP **không có data race**.

Nhưng các worker chạy song song thật trên nhiều core, và trên nhiều server. Race condition vì thế
**chuyển xuống** mọi chỗ dùng chung giữa các process:

```
 server 1                       server 2
 [FPM worker 1] [worker 2] ...  [worker 1] [worker 2] ...
       \            |               |           /
        +-----------+------+--------+----------+
                           |
        DB (MySQL)   Redis/cache   file/session   API ngoài
        ^ đây mới là "bộ nhớ dùng chung", và là nơi race xảy ra
```

Kịch bản coupon "mỗi user dùng một lần", viết kiểu check-then-act, hai request cùng user đến cùng lúc:

| Bước | Worker A | Worker B | Kết quả |
|---|---|---|---|
| 1 | `SELECT ... FROM coupon_usages WHERE user_id=7 AND coupon_id=3` → rỗng | | |
| 2 | | Cùng câu SELECT → rỗng | Cả hai tin là "chưa dùng" |
| 3 | `INSERT coupon_usages (7, 3)` | | |
| 4 | | `INSERT coupon_usages (7, 3)` | Coupon dùng hai lần |

Một chỗ dùng chung ít người để ý: **APCu**. Nó là shared memory giữa các worker của cùng một FPM
master, nên `apcu_fetch` rồi `apcu_store` cũng là check-then-act giữa các process. Dùng các hàm
atomic của nó: `apcu_add` (chỉ ghi khi key chưa có, trả `false` nếu đã có), `apcu_inc`, `apcu_cas`.

⚠️ Câu "PHP không có race condition vì không có thread" là red flag. Câu đúng: "PHP-FPM không có data
race trong bộ nhớ, nhưng race condition giữa các request vẫn xảy ra ở DB, cache, file, session".

#### Công cụ chống race trong Laravel

| Công cụ | Chặn cái gì | Không chặn / cạm bẫy |
|---|---|---|
| `lockForUpdate()` / `sharedLock()` | Pessimistic lock ở DB. Với MySQL, grammar của Laravel 13.x sinh `for update` / `lock in share mode` (cú pháp cũ, tương đương `FOR SHARE`) | Docs ghi "không bắt buộc nhưng nên" bọc trong transaction. Thực tế ngoài transaction (autocommit) lock nhả ngay khi câu SELECT xong, nên vô tác dụng |
| Unique index + bắt `UniqueConstraintViolationException` | Hai lần ghi trùng, **từ bất kỳ đường nào** (app, script, tinker) | Chỉ chặn trùng lặp, không chặn được ràng buộc kiểu "tổng không vượt X" |
| `Cache::lock('k', 10)->get(fn)` / `->block(5, fn)` | Loại trừ lẫn nhau giữa các process, server (atomic lock). `get` thử một lần; `block(5)` chờ tối đa 5 giây rồi ném `LockTimeoutException` | ⚠️ Lock có TTL (10 giây). Việc chạy quá TTL thì người khác lấy được lock. Driver `file` chỉ có tác dụng trong một máy, `array` chỉ trong một process |
| `Cache::funnel('k')->limit(3)` (docs 13.x) | Tối đa N việc cùng lúc: một semaphore phân tán | `releaseAfter()` là thời hạn an toàn, cùng cạm bẫy TTL như trên |
| Job `ShouldBeUnique` | Không dispatch thêm job cùng `uniqueId` khi đã có một job như vậy đang chờ hoặc đang chạy. Lock nhả khi job xong hoặc fail hẳn | Chỉ chặn lúc dispatch, dispatch trùng bị **bỏ qua lặng lẽ**. Không phải exactly-once, job vẫn phải idempotent |
| Job `ShouldBeUniqueUntilProcessing` | Như trên, nhưng nhả lock ngay khi job **bắt đầu chạy** | Job mới cùng key vào queue được trong lúc job cũ đang chạy |
| Job middleware `WithoutOverlapping($key)` | Hai job cùng key không **chạy** song song; job đến sau bị `release()` lại queue | Không chặn dispatch trùng. Release vẫn tính một attempt. Không đặt `expireAfter` thì worker chết giữa chừng là lock treo |
| Scheduler `withoutOverlapping()` | Lần chạy mới bị bỏ qua nếu lần trước chưa xong. Lock mặc định hết hạn sau 24 giờ | Lock kẹt sau sự cố thì xoá bằng `schedule:clear-cache` |
| Scheduler `onOneServer()` | Nhiều server cùng chạy `schedule:run`, task chỉ chạy trên server lấy được lock trước | Cần cache dùng chung (`database`, `memcached`, `dynamodb`, `redis`); closure phải có `name()` |
| `DB::transaction($fn, attempts: 3)` | Chạy lại cả closure khi lỗi do tranh chấp (deadlock, lock wait timeout). `attempts` là **tổng số lần chạy**, mặc định 1 (không retry) | Closure phải chạy lại được an toàn: không gửi mail, không gọi API ngoài bên trong |
| `->afterCommit()` / `'after_commit' => true` | Job dispatch trong transaction chỉ vào queue sau khi transaction ngoài cùng commit; rollback thì job bị bỏ | Không dùng thì worker có thể chạy job trước khi dữ liệu commit, và không thấy dữ liệu |
| Route `->block(10, 10)` | Các request cùng session xếp hàng (session lock) | Mặc định Laravel **không** khoá session, xem nhóm dưới |

Chi tiết cơ chế bên trong `ShouldBeUnique`, `WithoutOverlapping`, `retry_after` ở
[05-php-laravel.md, module 2.6](05-php-laravel.md#26-queue); chi tiết `lockForUpdate`, deadlock,
`afterCommit` ở [03-database-sql.md, module 2.6](03-database-sql.md#26-lock-thực-dụng) và
[2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel).

Áp coupon theo hai cách. Giả sử bảng `coupon_usages` có `UNIQUE(coupon_id, user_id)`, bảng
`coupons` có `used_count`, `max_uses`:

```php
<?php
declare(strict_types=1);

namespace App\Services;

use App\Models\Coupon;
use App\Models\CouponUsage;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Support\Facades\DB;

final class ApplyCoupon
{
    // Cách 1: pessimistic lock trên dòng coupon. Mọi request dùng coupon 3 xếp hàng ở đây.
    public function withLock(int $couponId, int $userId): bool
    {
        return DB::transaction(function () use ($couponId, $userId): bool {
            $coupon = Coupon::whereKey($couponId)->lockForUpdate()->firstOrFail();

            $used = CouponUsage::where('coupon_id', $couponId)
                ->where('user_id', $userId)
                ->exists();                     // an toàn: ai muốn ghi usage của coupon này đều phải qua lock ở trên
            if ($used || $coupon->used_count >= $coupon->max_uses) {
                return false;
            }

            CouponUsage::create(['coupon_id' => $couponId, 'user_id' => $userId]);
            $coupon->increment('used_count');

            return true;
        }, attempts: 3);
    }

    // Cách 2: không SELECT trước. UPDATE có điều kiện chặn vượt số lượt, unique index chặn trùng.
    public function withConstraint(int $couponId, int $userId): bool
    {
        try {
            return DB::transaction(function () use ($couponId, $userId): bool {
                // UPDATE coupons SET used_count = used_count + 1 WHERE id = ? AND used_count < max_uses
                $affected = Coupon::whereKey($couponId)
                    ->whereColumn('used_count', '<', 'max_uses')
                    ->increment('used_count');
                if ($affected === 0) {
                    return false;               // hết lượt, chưa ghi gì
                }

                // Trùng (coupon_id, user_id) thì ném exception, transaction rollback luôn lượt vừa cộng
                CouponUsage::create(['coupon_id' => $couponId, 'user_id' => $userId]);

                return true;
            });
        } catch (UniqueConstraintViolationException) {
            return false;                       // user này đã dùng coupon: kết quả nghiệp vụ, không phải lỗi 500
        }
    }
}
```

Cách nào là chốt chặn cuối? **Unique index.** Cách 1 chỉ đúng khi mọi đường ghi `coupon_usages` đều đi
qua `withLock`; một script import, một lệnh `tinker`, hay một dev khác viết endpoint mới là đủ phá.
Unique index nằm ở DB, nơi thấy mọi lần ghi. Thực tế nên có cả hai: logic nhiều bước dùng lock, và unique
index làm lưới an toàn.

⚠️ Trong Postgres, một câu lỗi (kể cả unique violation) làm hỏng cả transaction đang mở, phải
rollback. Vì vậy ví dụ trên bắt exception **bên ngoài** `DB::transaction`. Nếu muốn bắt bên trong thì
dùng savepoint; `createOrFirst()` của Eloquent tự làm việc này (bọc `create` trong savepoint khi đang ở
trong transaction, gặp unique violation thì đọc lại dòng đã có).

Cạm bẫy TTL của `Cache::lock`, timeline với lock 10 giây và việc tốn 15 giây:

| Giây | Process A | Process B | Kết quả |
|---|---|---|---|
| 0 | Lấy lock `sync:1` (TTL 10 s), bắt đầu đồng bộ | | |
| 10 | Vẫn đang chạy | Lock hết hạn, B lấy được | **Hai process cùng chạy** việc đáng ra phải độc quyền |
| 15 | Xong, gọi `release()` | Vẫn đang chạy | Release của Laravel so owner token (Lua script trên Redis), nên A **không** xoá nhầm lock của B |

Cách giảm rủi ro: đặt TTL lớn hơn thời gian chạy tệ nhất, hoặc lock ngắn rồi `refresh()` định kỳ
trong vòng lặp; và quan trọng nhất là thao tác bên trong vẫn idempotent hoặc có ràng buộc ở DB. Vì sao
lock phân tán không bao giờ an toàn tuyệt đối (GC pause, fencing token): xem
[14-distributed-systems.md](../14-distributed-systems.md).

#### Session và file

Hai thế giới session khác nhau, đừng lẫn:

- **Session gốc của PHP** (`session_start()`, handler `files` mặc định): file session bị khoá độc quyền
  từ lúc `session_start()` tới hết request. Tài liệu `session_write_close` nói rõ: vì dữ liệu session
  bị khoá để chống ghi đồng thời, mỗi lúc chỉ một script thao tác được một session. Hệ quả: năm request
  AJAX cùng session chạy **tuần tự**. Sửa: gọi `session_write_close()` ngay khi không cần ghi session
  nữa. Handler Redis của phpredis mặc định **không** khoá (`redis.session.locking_enabled`, mặc định 0),
  nên request chạy song song, đổi lại bên ghi sau đè bên ghi trước.
- **Session của Laravel** không dùng `session_start()`; Laravel tự đọc session lúc đầu request và ghi
  lại lúc cuối, qua driver của nó (mặc định `database`). Docs nói: mặc định các request cùng session
  **chạy đồng thời**. Hai endpoint cùng ghi session thì mất dữ liệu kiểu lost update. Chỉ những route
  thật sự cần thì gắn `->block($lockSeconds, $waitSeconds)` (mặc định 10 và 10) để xếp hàng; cần cache
  hỗ trợ atomic lock, không dùng được với driver session `cookie`.

| Bước | Request A (`/cart/add`) | Request B (`/wishlist/add`) | Session sau cùng |
|---|---|---|---|
| 1 | Đọc session `{cart: [], wish: []}` | | |
| 2 | | Đọc session `{cart: [], wish: []}` | |
| 3 | Ghi `{cart: [sp1], wish: []}` | | `cart` có sp1 |
| 4 | | Ghi `{cart: [], wish: [sp2]}` | **sp1 biến mất** khỏi giỏ |

`flock()` là advisory lock trên file:

```php
<?php
declare(strict_types=1);

// Chặn hai lần chạy script import chồng nhau trên CÙNG một máy
$fp = fopen('/tmp/import.lock', 'c');           // 'c': tạo nếu chưa có, không xoá nội dung
if ($fp === false || !flock($fp, LOCK_EX | LOCK_NB)) {
    fwrite(STDERR, "Đang có tiến trình import khác chạy\n");
    exit(1);
}
try {
    // ... import ...
} finally {
    flock($fp, LOCK_UN);
    fclose($fp);                                // đóng file (hoặc process chết) cũng nhả lock
}
```

- *Advisory* nghĩa là chỉ process nào cũng gọi `flock` mới tôn trọng khoá; process khác vẫn đọc ghi
  file bình thường.
- `LOCK_SH` cho nhiều reader, `LOCK_EX` cho một writer, `LOCK_NB` để không chờ.
- ⚠️ Chỉ chống race trên **một máy**: hai server là hai file khác nhau. Manual còn ghi `flock` chỉ dùng
  cho file local, và trên một số OS được cài ở mức process, nên với SAPI đa luồng (ví dụ PHP bản ZTS
  chạy trong FrankenPHP) có thể không chặn được các thread cùng process. Nhiều server thì dùng
  `Cache::lock` với Redis/DB, hoặc lock ở DB.

#### Octane: khi PHP có state dùng chung

*Octane* chạy Laravel trên FrankenPHP, RoadRunner hoặc Swoole. Mỗi worker boot app **một lần** rồi phục
vụ nhiều request liên tiếp, nên static, singleton resolve lúc boot, listener, connection DB sống qua
các request. Cơ chế sandbox, danh sách state Octane tự reset, ví dụ đầy đủ và bảng bẫy nằm ở
[05-php-laravel.md, module 3.5](05-php-laravel.md#35-process-sống-lâu-queue-worker-octane-daemon).
Ở góc nhìn concurrency, cần nắm ba điều:

1. **Trong một worker, request vẫn chạy lần lượt.** Octane cấu hình Swoole với
   `enable_coroutine => false`; RoadRunner và FrankenPHP cũng giao mỗi worker một request một lúc. Nên
   lỗi điển hình không phải hai request đan xen trên cùng biến, mà là **state của request trước rò sang
   request sau**. Tính chất giống lỗi thread (state dùng chung không được bảo vệ), chỉ khác là tuần tự.
2. **Giữa các worker vẫn không chung bộ nhớ userland**, trừ những thứ được thiết kế để chung: Swoole
   table và Octane cache (driver `octane`, chỉ có khi chạy Swoole, chung cho mọi worker trên server). Đọc rồi ghi trên đó là
   check-then-act giữa các worker, phải dùng thao tác atomic hoặc lock chứ không đọc rồi ghi.
3. **Hai bug chỉ xuất hiện khi chuyển sang Octane**, hay được hỏi:
   - Singleton giữ `Request`, user hay config lúc boot. Docs Octane cảnh báo: service singleton nhận
     `$app['request']` trong constructor sẽ giữ request đầu tiên cho mọi request sau, sai header, input,
     query string. Sửa: truyền dữ liệu qua tham số method, đăng ký `scoped`, hoặc inject closure
     `fn () => $app['request']`.
   - Static array tích luỹ: `Service::$data[] = ...` mỗi request là memory leak, vì không còn cuối request
     để dọn. Trên FPM cùng dòng code đó vô hại.

   Bug thứ ba hay gặp: transaction mở tay không đóng, request sau chạy tiếp trong transaction cũ trên
   cùng connection.

#### Concurrency trong một process PHP

| Công cụ | Là gì | Song song thật? | Ghi chú |
|---|---|---|---|
| Fiber (PHP 8.1) | Hàm có call stack riêng, tự `Fiber::suspend()` và được `resume()` từ ngoài | Không. Mỗi lúc một fiber chạy, chuyển lượt tường minh | Không tự biến I/O thành non-blocking: `PDO::query()` trong fiber vẫn chặn cả process. Dành cho tác giả thư viện async ([05, module 2.1](05-php-laravel.md#21-php-hiện-đại-80-tới-85)) |
| ReactPHP | Event loop kiểu reactor, stream, promise; gói `react/async` thêm `async()`/`await()` dựa trên Fiber | Không, một thread | Cần thư viện non-blocking của hệ sinh thái; hàm blocking như `sleep()`, PDO chặn cả loop |
| AMPHP v3 | Event loop Revolt, xây trên Fiber | Không, một thread | Như trên |
| Swoole / OpenSwoole | Extension C, coroutine; runtime hook biến PDO (mysqlnd), phpredis, curl, file I/O thành non-blocking | Trong một worker: không. Nhiều worker process: có | Coroutine chỉ chạy trên một core; Swoole dùng nhiều process để dùng nhiều core |
| Laravel `Concurrency::run([...])` | Serialize closure, chạy mỗi closure trong một **process PHP con** (driver `process`, mặc định), trả kết quả serialize về | Có, nhiều process | Driver `fork` nhanh hơn nhưng chỉ dùng được ở CLI (cần `spatie/fork`); `sync` để test. `Concurrency::defer([...])` chạy sau khi đã gửi response |

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\Concurrency;
use Illuminate\Support\Facades\DB;

// Hai query độc lập chạy song song trong hai process con
[$userCount, $orderCount] = Concurrency::run([
    fn (): int => DB::table('users')->count(),
    fn (): int => DB::table('orders')->count(),
], timeout: 30);   // timeout chỉ áp cho driver process
```

⚠️ Các closure chạy ở process khác: không chia sẻ biến với process cha (giá trị được serialize sang),
mỗi process mở connection DB riêng, và không nằm trong transaction của process cha. Hai closure cùng
sửa một dòng thì race ở DB y như hai request.

#### Đối chiếu Java/Go

Cùng một lỗi "state của request nằm ở chỗ dùng chung", ba nền tảng lộ ra ba kiểu:

| | PHP-FPM | Octane | Java Spring | Go `net/http` |
|---|---|---|---|---|
| Đơn vị chạy request | Process | Worker, lần lượt | Thread (hoặc virtual thread) từ pool, **đồng thời** | Goroutine mỗi request, **đồng thời** |
| Chỗ dùng chung trong process | Không có | Static, singleton lúc boot | Bean singleton (scope mặc định) | Biến package, field của struct handler |
| Lỗi khi quên | Không có | State rò sang request sau | Data race giữa request đang chạy | Data race; ghi `map` đồng thời thì runtime crash cả process |

```java
@Service                                   // singleton: MỘT object cho mọi request
public class ReportService {
    private Long currentUserId;            // SAI: field có state trong bean singleton

    public Report build(long userId) {
        this.currentUserId = userId;       // thread A ghi 7, thread B ghi 9 ngay sau
        return load(this.currentUserId);   // thread A có thể đọc 9: báo cáo của người khác
    }
}
```

```go
// SAI: map dùng chung giữa các goroutine request mà không khoá
var hits = map[string]int{}

func handler(w http.ResponseWriter, r *http.Request) {
	hits[r.URL.Path]++ // hai request cùng lúc: "fatal error: concurrent map writes"
}

// ĐÚNG: bảo vệ bằng mutex
var (
	mu    sync.Mutex
	hits2 = map[string]int{}
)

func handler2(w http.ResponseWriter, r *http.Request) {
	mu.Lock()
	hits2[r.URL.Path]++
	mu.Unlock()
}
```

Cách sửa ở cả ba nơi giống nhau về tư duy: giữ service **không có state theo request** (truyền qua
tham số), state dùng chung thật sự thì bảo vệ bằng primitive đồng bộ, và state cần đúng giữa nhiều
process hay server thì đưa xuống DB với ràng buộc hoặc thao tác atomic.

**Tóm tắt nhanh**

- PHP-FPM không có data race nhưng đầy race condition: DB, Redis, file, session, APCu là bộ nhớ dùng
  chung giữa các process và server. "PHP không có thread nên không có race" là red flag.
- Unique index là chốt chặn cuối vì DB thấy mọi lần ghi; `lockForUpdate()` chỉ có tác dụng trong
  transaction và chỉ đúng khi mọi đường ghi đều đi qua nó.
- `ShouldBeUnique` chặn lúc dispatch; `WithoutOverlapping` chặn lúc chạy; cả hai không thay được
  idempotent. `Cache::lock` có TTL: việc chạy quá TTL thì hai bên cùng chạy.
- `DB::transaction($fn, attempts: 3)`: 3 là tổng số lần chạy, mặc định 1. Session gốc PHP khoá file
  nên request cùng session chạy tuần tự; session Laravel không khoá, dùng `->block()` khi cần.
- Octane: request trong một worker vẫn tuần tự, bug là state rò giữa request (singleton giữ request,
  static tích luỹ). `Concurrency::run` chạy closure ở process con, race lại quay về DB.

**Nguồn**: [Laravel: Atomic Locks](https://laravel.com/docs/13.x/cache#atomic-locks) ·
[Laravel: Pessimistic Locking](https://laravel.com/docs/13.x/queries#pessimistic-locking) ·
[Laravel: Handling Deadlocks](https://laravel.com/docs/13.x/database#handling-deadlocks) ·
[Laravel: Unique Jobs](https://laravel.com/docs/13.x/queues#unique-jobs) ·
[Laravel: Preventing Job Overlaps](https://laravel.com/docs/13.x/queues#preventing-job-overlaps) ·
[Laravel: Jobs & Database Transactions](https://laravel.com/docs/13.x/queues#jobs-and-database-transactions) ·
[Laravel: Scheduling (Preventing Task Overlaps, Running Tasks on One Server)](https://laravel.com/docs/13.x/scheduling#preventing-task-overlaps) ·
[Laravel: Session Blocking](https://laravel.com/docs/13.x/session#session-blocking) ·
[Laravel: Octane](https://laravel.com/docs/13.x/octane) ·
[Laravel: Concurrency](https://laravel.com/docs/13.x/concurrency) ·
[laravel/octane: StartSwooleCommand.php](https://github.com/laravel/octane/blob/2.x/src/Commands/StartSwooleCommand.php) ·
[laravel/framework: RedisLock.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Cache/RedisLock.php) ·
[PHP: Fibers](https://www.php.net/manual/en/language.fibers.php) ·
[PHP: session_write_close](https://www.php.net/manual/en/function.session-write-close.php) ·
[PHP: flock](https://www.php.net/manual/en/function.flock.php) ·
[PHP: apcu_cas](https://www.php.net/manual/en/function.apcu-cas.php) ·
[phpredis: Session locking](https://github.com/phpredis/phpredis#session-locking) ·
[ReactPHP](https://reactphp.org/) · [ReactPHP Async](https://reactphp.org/async/) ·
[OpenSwoole: Coroutine](https://openswoole.com/docs/modules/swoole-coroutine) ·
[OpenSwoole: Runtime Hooks](https://openswoole.com/docs/modules/swoole-runtime-flags)


---

## Chặng 3: Senior

### 3.1 Memory model

Module này trả lời: vì sao một thread ghi biến mà thread khác có thể **không bao giờ** thấy, vì sao
thứ tự lệnh mà thread khác quan sát có thể "vô lý", và ngôn ngữ đưa ra quy tắc nào (happens-before)
để bạn biết chắc lần đọc nào thấy lần ghi nào. Với PHP-FPM bạn không gặp chuyện này; với service Go,
Java, hay extension đa luồng thì có.

#### Vấn đề: thread không tự thấy ghi của nhau

*Visibility* (khả năng nhìn thấy): không có đồng bộ thì không có gì đảm bảo thread B thấy giá trị
thread A vừa ghi, kể cả sau rất lâu. Nguyên nhân thực tế:

- Compiler/JIT được phép giữ giá trị trong register và bỏ các lần đọc lại. Vòng lặp không tự sửa biến
  thì compiler có thể đọc biến **một lần** rồi đưa ra ngoài vòng lặp (*hoisting*).
- CPU có store buffer và được phép thực hiện đọc/ghi không theo thứ tự chương trình. Cách nói "giá trị
  nằm trong cache của CPU chưa ghi ra RAM" là hình ảnh đơn giản hoá; cache của CPU hiện đại có cơ chế
  đồng bộ (cache coherence), thủ phạm chính thường là compiler và store buffer. Memory model của ngôn
  ngữ cố ý không nói tới phần cứng cụ thể.

JLS §17.3 có đúng ví dụ này: với `done` không phải `volatile`, vòng `while (!this.done)
Thread.sleep(1000);` có thể không bao giờ dừng, vì compiler được phép đọc `done` một lần, và
`Thread.sleep`/`Thread.yield` **không** có ngữ nghĩa đồng bộ nào.

Chạy thử (JDK 26, macOS arm64, `java StopFlag.java`, ba lần như nhau):

```java
public class StopFlag {
    static boolean stop = false;             // thiếu volatile
    static volatile boolean stopV = false;   // có volatile

    public static void main(String[] args) throws InterruptedException {
        Thread t1 = new Thread(() -> { long n = 0; while (!stop) { n++; } });
        Thread t2 = new Thread(() -> { long n = 0; while (!stopV) { n++; } });
        t1.setDaemon(true);                  // để JVM thoát được dù t1 kẹt
        t1.start();
        t2.start();
        Thread.sleep(1000);                  // cho JIT kịp biên dịch vòng lặp
        stop = true;
        stopV = true;
        t1.join(2000);
        t2.join(2000);
        System.out.println("không volatile, còn chạy: " + t1.isAlive());  // true
        System.out.println("volatile, còn chạy: " + t2.isAlive());        // false
    }
}
```

Kết quả `true` ở dòng đầu không được đặc tả bảo đảm; nó là một kết quả **được phép** xảy ra, và JIT
thực tế đã làm vậy. Máy khác, JVM khác có thể cho `false`. Đó chính là cái nguy: bản thiếu `volatile`
sai dù đôi khi chạy đúng.

*Ordering* (thứ tự): compiler và CPU được sắp xếp lại lệnh miễn là **bên trong một thread** kết quả
không đổi. Thread khác nhìn vào thì có thể thấy thứ tự vô lý. Ví dụ trong JLS (bảng 17.4-A), ban đầu
`A == B == 0`:

| Thread 1 | Thread 2 |
|---|---|
| `r2 = A;` | `r1 = B;` |
| `B = 1;` | `A = 2;` |

Trực giác bảo `r2 == 2 && r1 == 1` là không thể (sẽ cần một vòng thời gian khép kín). Nhưng mỗi thread
có hai lệnh không phụ thuộc nhau, compiler được đảo `B = 1` lên trước `r2 = A`, và kết quả "không thể"
xảy ra được. Go memory model có ví dụ tương tự: `f()` ghi `a = 1; b = 2`, `g()` đọc `print(b);
print(a)` có thể in `2` rồi `0`.

Hệ quả thực tế nguy hiểm nhất là *publication* (công bố object cho thread khác):

```
Thread A                          Thread B
data = 42                         if (ready)          // thấy true
ready = true   (biến thường)          use(data)       // có thể thấy 0!
```

Không có đồng bộ, việc B thấy `ready = true` **không** kéo theo việc B thấy `data = 42`.

#### Happens-before

*Memory model* là bộ quy tắc trả lời câu hỏi: một lần đọc biến được phép thấy những lần ghi nào.
Cả Java và Go đều xây quy tắc trên quan hệ *happens-before* (hb):

1. *Program order* (Go gọi là *sequenced before*): trong cùng một thread, lệnh viết trước hb lệnh
   viết sau.
2. *Synchronizes-with* (Go: *synchronized before*): một số cặp thao tác đồng bộ nối hai thread. Đầu
   nguồn gọi là *release*, đầu đích gọi là *acquire*. Ví dụ: unlock một mutex và lần lock sau đó trên
   cùng mutex; ghi một biến `volatile` và lần đọc thấy giá trị đó.
3. Hb là **bắc cầu** của hai quan hệ trên: x hb y và y hb z thì x hb z.

Quy tắc đọc: nếu lần ghi w hb lần đọc r, và không có lần ghi nào khác chen giữa theo hb, thì r thấy
đúng w. Nếu w và r **không** được hb sắp thứ tự, và ít nhất một bên là thao tác thường, đó là *data
race*, và r có thể thấy giá trị cũ, giá trị mới, hay (với dữ liệu nhiều word trong Go) một thứ lẫn lộn.

```
Thread A                                  Thread B
data = 42          (program order)
   |
ready = true  ── volatile write (release)
                 ╲
                  ╲ synchronizes-with (B đọc ĐÚNG biến ready và THẤY true)
                   ╲
                    ready == true  ── volatile read (acquire)
                       |           (program order)
                    đọc data  →  chắc chắn thấy 42
```

Ba điều hay bị hiểu sai:

- Hb chỉ nối khi acquire và release là **cùng một biến / cùng một lock**, và bên đọc **thấy** giá trị
  bên ghi đã ghi. Shipilëv có câu đố: setter `synchronized` nhưng getter không `synchronized` thì vẫn
  sai, vì getter không có acquire nào để ghép với release của setter. Đọc một biến `volatile` khác
  "cho có barrier" cũng không được đặc tả bảo đảm.
- Hb không có nghĩa là máy phải chạy theo đúng thứ tự đó; nó chỉ ràng buộc kết quả mà các thread có
  quan hệ hb với nhau quan sát được.
- *DRF-SC*: chương trình **không có data race** thì mọi lần chạy đều trông như một cách đan xen tuần tự
  nào đó (*sequentially consistent*). Đây là đảm bảo chung của Java, Go, C++, Rust, JavaScript. Nhưng
  không có data race **không** có nghĩa là hết race condition: JLS nói thẳng, tuần tự nhất quán vẫn để
  lọt lỗi của những nhóm thao tác cần atomic mà không được làm atomic (check-then-act, module 1.1).

#### Java Memory Model (JMM)

Những cặp tạo hb trong JLS §17.4.4 và §17.4.5:

| Release | hb | Acquire |
|---|---|---|
| Unlock một *monitor* (khoá gắn với mỗi object, thứ `synchronized` dùng) | → | Mọi lần lock sau đó trên cùng monitor |
| Ghi biến `volatile` | → | Mọi lần đọc sau đó của cùng biến |
| `t.start()` | → | Lệnh đầu tiên trong thread `t` |
| Mọi lệnh trong thread `t` | → | Thread khác trả về thành công từ `t.join()` (hoặc thấy `t.isAlive() == false`) |
| `t.interrupt()` | → | Chỗ phát hiện `t` bị interrupt (`InterruptedException`, `isInterrupted()`) |
| Khởi tạo giá trị mặc định (0, `false`, `null`) | → | Mọi thao tác khác |

Các lớp trong `java.util.concurrent` (`ConcurrentHashMap`, `BlockingQueue`, `ExecutorService`,
`CountDownLatch`, biến atomic...) ghi rõ "memory consistency effects" trong Javadoc, ví dụ đặt một
phần tử vào `BlockingQueue` hb việc lấy nó ra ở thread khác. Dùng chúng là có hb mà không cần tự lập
luận.

`volatile` cho ba thứ: visibility, ordering (các thao tác trên biến volatile có một thứ tự toàn cục,
và làm mốc release/acquire cho các biến thường quanh nó), và ghi/đọc atomic cho `long`/`double`. Nó
**không** cho atomicity của thao tác nhiều bước:

```java
volatile int count = 0;
count++;                                // vẫn là đọc, cộng, ghi: hai thread vẫn mất lượt tăng

AtomicInteger safe = new AtomicInteger();
safe.incrementAndGet();                 // CAS, atomic thật (module 2.1)
```

Vài quy tắc nhỏ nhưng hay bị hỏi (JLS §17.5 và §17.7):

- Ghi `long`/`double` **không** volatile được phép tách làm hai lần ghi 32 bit, thread khác có thể thấy
  nửa này của giá trị cũ, nửa kia của giá trị mới. `volatile long`/`double` luôn atomic; ghi/đọc
  **tham chiếu** luôn atomic.
- *Final field*: object được khởi tạo xong rồi mới công bố tham chiếu (không để `this` lọt ra ngoài
  trong constructor) thì thread khác đọc field `final` chắc chắn thấy giá trị đã gán, kể cả khi tham
  chiếu được truyền qua data race. Field không `final` thì không có đảm bảo đó. Ví dụ JLS 17.5-1:
  `x` là final đọc ra 3, `y` không final có thể đọc ra 0. Đây là lý do object bất biến an toàn khi
  chia sẻ.

*Double-checked locking* (DCL): khởi tạo lười một singleton mà không muốn lock mỗi lần đọc.

```java
public class Config {
    private static volatile Config instance;   // BẮT BUỘC volatile

    public static Config get() {
        Config c = instance;                   // đọc volatile một lần vào biến local
        if (c == null) {
            synchronized (Config.class) {
                c = instance;
                if (c == null) {
                    c = new Config();          // 1. cấp bộ nhớ 2. chạy constructor 3. gán tham chiếu
                    instance = c;
                }
            }
        }
        return c;
    }
}
```

Thiếu `volatile`, lệnh gán `instance` có thể được sắp xếp (với thread khác nhìn vào) lên trước khi
constructor chạy xong. Thread thứ hai đi nhánh ngoài, **không** vào `synchronized` nên không có
acquire nào, thấy `instance != null` và dùng một object mà field còn giá trị mặc định. Có `volatile`,
việc ghi `instance` là release, việc đọc ở dòng đầu là acquire, nên mọi thứ constructor ghi đều được
nhìn thấy. Cách đơn giản hơn DCL: *holder class idiom* (`private static class Holder { static final
Config I = new Config(); }`), dựa vào việc khởi tạo class của JVM vốn đã thread-safe.

Java có data race vẫn **an toàn bộ nhớ**: JLS ghi data race không thể làm những thao tác như đọc độ dài
mảng hay kiểm tra kiểu cast trả sai, và cấm giá trị "từ không khí" (*out-of-thin-air*). Bạn nhận giá trị
cũ, giá trị mới, hay thứ tự vô lý, nhưng không crash vì hỏng bộ nhớ.

#### Go memory model

Tài liệu chính thức mở đầu bằng lời khuyên: chương trình sửa dữ liệu mà goroutine khác đang truy cập
thì phải tuần tự hoá truy cập đó bằng channel hoặc `sync`, `sync/atomic`; và "nếu bạn phải đọc hết
tài liệu này mới hiểu được chương trình của mình, bạn đang quá khéo. Đừng khéo."

Định nghĩa data race của Go: một lần ghi vào một vị trí bộ nhớ xảy ra đồng thời với một lần đọc hoặc
ghi khác vào cùng vị trí, trừ khi mọi truy cập đều là atomic của `sync/atomic`. Không có data race thì
chương trình chạy như thể mọi goroutine được dồn lên một CPU (DRF-SC).

Những gì tạo hb (Go gọi là *synchronized before*):

| Thao tác trước | Được đảm bảo trước |
|---|---|
| Lệnh `go f()` | Lúc `f` bắt đầu chạy |
| Gửi vào channel | Lúc lần nhận tương ứng hoàn tất |
| `close(ch)` | Lần nhận trả về giá trị zero vì channel đã đóng |
| Nhận từ **unbuffered** channel | Lúc lần gửi tương ứng hoàn tất |
| Lần nhận thứ k từ channel có sức chứa C | Lúc lần gửi thứ k+C hoàn tất (đây là lý do buffered channel làm semaphore được) |
| `Unlock()` lần thứ n của `sync.Mutex`/`RWMutex` | Lúc `Lock()` lần thứ m trả về, với n < m |
| Lần chạy `f` duy nhất trong `once.Do(f)` | Lúc mọi lời gọi `once.Do(f)` trả về |
| Thao tác atomic A mà thao tác atomic B thấy kết quả | B |
| `wg.Done()` (theo tài liệu package `sync`) | Lúc `wg.Wait()` mà nó mở khoá trả về |

Và những gì **không** tạo hb:

- Goroutine **kết thúc** không đồng bộ với ai. `go func() { a = "hello" }(); print(a)` không đảm bảo
  in gì; compiler được phép xoá hẳn lệnh `go` đó.
- `TryLock()` thất bại không có tác dụng đồng bộ nào.

Mọi thao tác `sync/atomic` hành xử như được thực hiện theo một thứ tự tuần tự nhất quán duy nhất; tài
liệu Go ghi rõ đây là cùng ngữ nghĩa với atomic sequentially consistent của C++ và biến `volatile` của
Java.

Ba idiom sai mà tài liệu Go liệt kê, đều cùng một gốc:

- DCL bằng biến `done bool` thường: thấy `done == true` không kéo theo thấy dữ liệu `setup()` đã ghi.
  Dùng `sync.Once`.
- Chờ bận `for !done {}`: có thể in chuỗi rỗng, và vòng lặp **không được đảm bảo** kết thúc.
- Công bố con trỏ `g = t` sau khi gán `t.msg`: goroutine khác thấy `g != nil` vẫn có thể thấy
  `g.msg` chưa khởi tạo.

Chạy thử bản chờ bận với biến thường so với `atomic.Bool` (Go 1.26, macOS arm64):

```go
package main

import (
	"fmt"
	"sync/atomic"
	"time"
)

var stop bool         // biến thường, không đồng bộ
var stopA atomic.Bool // atomic

func wait(name string, loop func()) {
	done := make(chan struct{})
	go func() { loop(); close(done) }()
	time.Sleep(100 * time.Millisecond)
	stop = true
	stopA.Store(true)
	select {
	case <-done:
		fmt.Println(name + ": đã dừng")
	case <-time.After(2 * time.Second):
		fmt.Println(name + ": vẫn chạy sau 2 giây")
	}
}

func main() {
	wait("bool thường", func() {
		for !stop {
		}
	})
	wait("atomic.Bool", func() {
		for !stopA.Load() {
		}
	})
}
// go run main.go       → bool thường: đã dừng / atomic.Bool: đã dừng
// go run -race main.go → WARNING: DATA RACE (ghi stop ở wait, đọc stop trong vòng lặp)
```

Lần chạy này bản biến thường **tình cờ** dừng, khác với Java ở trên. Không có gì bảo đảm điều đó ở
phiên bản compiler khác hay máy khác; race detector báo ngay đây là data race. Bài học: chạy thử
đúng không chứng minh được gì, phải lập luận bằng hb hoặc để `-race` kiểm.

⚠️ Khác Java ở hậu quả: Go chỉ đảm bảo lần đọc một giá trị **cỡ một word máy trở xuống** thấy một lần
ghi có thật. Với dữ liệu nhiều word mà bên trong là cặp (con trỏ, độ dài) hay (con trỏ, kiểu), như
interface, slice, string, map, data race có thể tạo giá trị lai giữa hai lần ghi và dẫn tới **hỏng bộ
nhớ tuỳ ý**. Ví dụ: đọc một slice trong lúc goroutine khác gán slice mới, có thể nhận con trỏ của slice
mới với độ dài của slice cũ, rồi đọc ra ngoài vùng cấp phát. Ghi `map` đồng thời thì runtime phát hiện
và dừng cả process (`fatal error: concurrent map writes`).

Memory model cũng trói tay compiler: compiler Go không được thêm lần ghi không có trong code (ví dụ
đảo `if` để ghi trước rồi ghi lại), không được đọc lại một biến chia sẻ để lấy lại giá trị local đã
kiểm tra, và không được giả định vòng lặp hay lời gọi hàm luôn kết thúc để kéo truy cập lên trước.
Những biến đổi đó hợp lệ với C/C++ nhưng không hợp lệ với Go.

#### Đối chiếu Java/Go

| | Java | Go |
|---|---|---|
| Cờ dừng, cờ "ready" | `volatile boolean` | `atomic.Bool` (Go không có `volatile`) |
| Ngữ nghĩa của biến đồng bộ nhẹ | `volatile`: thứ tự toàn cục, release/acquire | `sync/atomic`: sequentially consistent, tài liệu nói tương đương `volatile` của Java |
| Khoá | `synchronized`, `ReentrantLock` | `sync.Mutex`, `sync.RWMutex` |
| Khởi tạo một lần | Holder class, DCL với `volatile` | `sync.Once`, `sync.OnceValue` |
| Bắt đầu / chờ luồng | `Thread.start()`, `join()` | Lệnh `go`, `WaitGroup` hoặc channel (goroutine kết thúc không tự đồng bộ) |
| Hậu quả data race | An toàn bộ nhớ, giá trị bất ngờ | Word đơn thì thấy một giá trị có thật; interface/slice/map có thể hỏng bộ nhớ hoặc crash |
| Công cụ bắt race | Không có sẵn trong JDK; kiểm thử concurrency bằng jcstress (OpenJDK) | `go test -race`, `go run -race` (ThreadSanitizer) |

Với PHP: PHP-FPM không chia sẻ bộ nhớ userland giữa các request, nên không có câu hỏi memory model.
Swoole coroutine chạy trên một thread mỗi worker và mặc định chỉ chuyển lượt ở điểm I/O hay khi
gọi yield, nên các coroutine không thấy lệnh của nhau bị đảo; race ở đó là race **logic** giữa
các điểm chuyển lượt (đọc biến, gọi Redis, ghi biến). Memory model chỉ là chuyện của bạn khi viết Go, Java, hay extension C đa luồng.

Cả hai ngôn ngữ cùng một lời khuyên cuối: dùng primitive có sẵn (lock, channel, atomic, collection
concurrent). Đừng tự lập luận trên memory model để "tiết kiệm" một lần đồng bộ.

**Tóm tắt nhanh**

- Không đồng bộ thì không có đảm bảo visibility hay ordering: compiler được hoist lần đọc ra khỏi vòng
  lặp, compiler và CPU được đảo lệnh. `while (!stop)` thiếu `volatile` treo thật trên HotSpot.
- Happens-before = program order + synchronizes-with (release → acquire trên **cùng** biến/lock), bắc
  cầu. Không có hb giữa ghi và đọc là data race. Không có data race thì chương trình tuần tự nhất quán
  (DRF-SC), nhưng vẫn có thể có race condition.
- Java: unlock→lock, ghi→đọc `volatile`, `start`, `join`, lớp `java.util.concurrent`. `volatile` không
  làm `count++` atomic. DCL cần `volatile` vì tham chiếu có thể được công bố trước khi constructor xong.
- Go: `go`, channel, mutex, `Once`, atomic (sequentially consistent, như `volatile` của Java). Goroutine
  kết thúc không đồng bộ với ai. Race trên interface/slice/map có thể hỏng bộ nhớ, khác Java.
- Chạy thử đúng không chứng minh gì. Dùng primitive có sẵn và `-race`.

**Nguồn**: [The Go Memory Model](https://go.dev/ref/mem) ·
[JLS SE 25, ch.17: Threads and Locks (§17.3, §17.4, §17.5, §17.7)](https://docs.oracle.com/javase/specs/jls/se25/html/jls-17.html) ·
[Aleksey Shipilëv: Java Memory Model Pragmatics](https://shipilev.net/blog/2014/jmm-pragmatics/) (Part III: SC-DRF) ·
[Go: package sync (WaitGroup)](https://pkg.go.dev/sync#WaitGroup)

---

### 3.2 Lock-free, ABA, spinlock

Module này trả lời: "lock-free" thật ra hứa hẹn điều gì, vì sao CAS có thể thành công mà vẫn sai
(vấn đề ABA), khi nào quay vòng chờ khoá (spin) có lợi, và bản sao của ABA ở tầng DB mà backend
PHP gặp thật.

#### Lock-free và wait-free

Nhắc lại từ [module 2.1](#21-atomic-cas-và-optimistic-lock): CAS (compare-and-swap) ghi giá trị
mới chỉ khi giá trị hiện tại vẫn bằng `expected`, và thường nằm trong vòng lặp "đọc, tính, CAS,
thất bại thì làm lại". Các thuật toán *non-blocking* (không chặn) xây trên CAS, và được xếp hạng
theo mức đảm bảo tiến triển (*progress guarantee*):

| Mức | Đảm bảo | Ý nghĩa thực tế |
|---|---|---|
| Blocking (dùng lock) | Không có | Thread giữ lock bị treo, bị swap ra đĩa, bị preempt thì mọi thread chờ lock đứng theo |
| Obstruction-free | Một thread chạy một mình (không ai chen) thì xong sau hữu hạn bước | Yếu nhất trong nhóm non-blocking |
| Lock-free | Tại mọi thời điểm, **ít nhất một** thread đang tiến triển | Cả hệ thống không bao giờ kẹt, nhưng một thread cụ thể có thể thua CAS mãi (starvation) |
| Wait-free | **Mọi** thread xong việc sau hữu hạn bước | Mạnh nhất, khó viết nhất, thường chậm hơn lock-free ở trường hợp trung bình |

Vì sao vòng lặp CAS là lock-free: một thread thua CAS chỉ vì **có thread khác vừa CAS thành công**.
Tức mỗi lần có người thất bại là có người khác đã tiến lên một bước. Ngược lại, với lock, nếu
thread giữ lock bị OS dừng lại (preempt, page fault), không ai tiến được.

⚠️ "Không dùng `synchronized`/`Mutex`" chưa chắc là lock-free. Đoạn code tự quay vòng chờ một cờ
do thread khác bật (`while (!flag) {}`) thực chất là một khoá tự chế: thread bật cờ bị treo thì mọi
người chờ theo. Lock-free là một tính chất về tiến triển, không phải "code không có chữ lock".

#### Vấn đề ABA

CAS chỉ so **giá trị hiện tại** với `expected`. Nó không biết giá trị đó đã bị đổi đi rồi đổi về
bao nhiêu lần. Kịch bản kinh điển trên *Treiber stack* (lock-free stack đơn giản nhất: `top` là một
con trỏ atomic, `pop` là CAS `top` từ node đầu sang `node.next`):

```
Ban đầu:  top -> A -> B -> C

1. Thread 1 pop: đọc top = A, next = B. Chuẩn bị CAS(top, A, B). Bị OS tạm dừng.
2. Thread 2 pop A, pop B.              top -> C
3. Thread 2 push lại node A (tái sử dụng node, hoặc bộ cấp phát trả lại đúng địa chỉ cũ).
                                       top -> A -> C
4. Thread 1 chạy tiếp: CAS(top, A, B). top vẫn là A nên THÀNH CÔNG.
                                       top -> B -> C
   B đã bị thread 2 lấy ra (có thể đã free) nhưng lại nằm trên stack. C thì... tuỳ may rủi.
```

Chương trình Go dưới đây tự "xen kẽ" các bước trên trong một goroutine (nên kết quả tất định) để
thấy CAS thành công sai. Lưu thành `main.go` trong một thư mục trống, chạy `go mod init aba && go run .`:

```go
// Mô phỏng ABA trên Treiber stack bằng cách tự xen kẽ từng bước của hai "thread".
package main

import (
	"fmt"
	"sync/atomic"
)

type node struct {
	val  string
	next *node
}

type stack struct{ top atomic.Pointer[node] }

func (s *stack) push(n *node) {
	for {
		old := s.top.Load()
		n.next = old
		if s.top.CompareAndSwap(old, n) {
			return
		}
	}
}

func (s *stack) pop() *node {
	for {
		old := s.top.Load()
		if old == nil {
			return nil
		}
		if s.top.CompareAndSwap(old, old.next) {
			return old
		}
	}
}

func (s *stack) values() []string {
	var out []string
	for n := s.top.Load(); n != nil; n = n.next {
		out = append(out, n.val)
	}
	return out
}

func main() {
	var s stack
	c, b, a := &node{val: "C"}, &node{val: "B"}, &node{val: "A"}
	s.push(c)
	s.push(b)
	s.push(a)
	fmt.Println("ban đầu:", s.values()) // ban đầu: [A B C]

	// Thread 1 bắt đầu pop: đọc top = A và next = B, rồi bị "tạm dừng".
	old := s.top.Load()
	next := old.next

	// Thread 2 chen vào: pop A, pop B, rồi push lại chính node A.
	x := s.pop()
	s.pop() // B đã bị lấy ra khỏi stack
	s.push(x)
	fmt.Println("sau thread 2:", s.values()) // sau thread 2: [A C]

	// Thread 1 chạy tiếp: CAS(top, A, B). top vẫn là A nên CAS thành công.
	ok := s.top.CompareAndSwap(old, next)
	fmt.Println("CAS của thread 1 thành công:", ok) // CAS của thread 1 thành công: true
	fmt.Println("sau thread 1:", s.values())        // sau thread 1: [B C]  <- B "sống lại"
}
```

Vì sao ở Java/Go ít gặp hơn C/C++: có GC. Nếu mỗi lần `push` bạn tạo node **mới**, thì chừng nào
thread 1 còn giữ tham chiếu tới A, GC không thu hồi A, nên không thể có một node "khác" mang cùng
địa chỉ A. ABA chỉ quay lại khi bạn chủ động tái sử dụng node (object pool) như ví dụ trên. Ở C/C++
không có GC, node bị `free` rồi `malloc` lại đúng địa chỉ cũ là chuyện bình thường.

Các cách sửa:

1. **Gắn version (stamp, tag) tăng dần** vào giá trị và CAS cả cặp. Giá trị có về lại A thì version
   cũng đã khác. Java có sẵn `AtomicStampedReference<V>`: giữ cặp (tham chiếu, `int` stamp), và
   `compareAndSet(expectedRef, newRef, expectedStamp, newStamp)` chỉ ghi khi **cả hai** khớp.

   ```java
   AtomicStampedReference<Node> top = new AtomicStampedReference<>(initialTop, 0);

   int[] stampHolder = new int[1];
   Node old = top.get(stampHolder);          // đọc cùng lúc tham chiếu và stamp
   int stamp = stampHolder[0];
   boolean ok = top.compareAndSet(old, old.next, stamp, stamp + 1);
   ```

   ⚠️ Javadoc ghi rõ phần tham chiếu được so bằng `==` (cùng object), không phải `equals`. Dùng với
   kiểu boxed như `Integer` thì hai giá trị "bằng nhau" vẫn có thể là hai object khác nhau, CAS thất
   bại khó hiểu. (Java còn có `AtomicMarkableReference`, giữ một bit `boolean` thay cho `int`.)
2. **Không cho node bị tái sử dụng khi còn thread đang nhìn nó**:
   - Dựa vào GC (Java, Go), như đã nói.
   - *Hazard pointer* (ngôn ngữ không GC): trước khi đọc một node, thread "công bố" con trỏ đó vào
     một danh sách chung; bên muốn giải phóng node phải kiểm tra danh sách này, node còn được công
     bố thì hoãn giải phóng.

#### ABA ở tầng DB

Optimistic lock ([module 2.1](#21-atomic-cas-và-optimistic-lock)) là CAS trên một dòng DB, nên
cũng dính ABA nếu `expected` là một cột **có thể quay về giá trị cũ**. Ví dụ đơn hàng đi
`pending -> paid -> refunded -> pending` (khách được cho thanh toán lại), và một worker huỷ đơn quá
hạn đã đọc đơn từ trước:

| Bước | Session A (worker huỷ đơn quá hạn) | Session B (luồng thanh toán, hoàn tiền) | Kết quả |
|---|---|---|---|
| 1 | Đọc đơn 42: `status = 'pending'`, `version = 1`. Chuẩn bị huỷ | | |
| 2 | (bị chậm vì gọi API bên ngoài) | Khách trả tiền: `status = 'paid'`, `version = 2` | |
| 3 | | Hoàn tiền rồi mở lại đơn: `status = 'pending'`, `version = 3` | Trạng thái giống bước 1, nhưng đây là một lượt thanh toán mới |
| 4 | `UPDATE orders SET status = 'cancelled' WHERE id = 42 AND status = 'pending'` | | Khớp, 1 dòng bị sửa: huỷ nhầm lượt thanh toán mới (ABA) |
| 4' (cách đúng, thay cho 4) | `UPDATE orders SET status = 'cancelled', version = version + 1 WHERE id = 42 AND version = 1` | | 0 dòng: phát hiện đơn đã đổi, đọc lại rồi quyết định |

Quy tắc:

- Cột dùng làm `expected` phải **chỉ tăng**: `version INT` cộng 1 ở mọi câu ghi. JPA có sẵn
  `@Version` làm việc này.
- So `status` vẫn hữu ích như một điều kiện nghiệp vụ (chỉ huỷ khi còn `pending`), nhưng không thay
  được `version`. Hai điều kiện có thể dùng cùng lúc.
- ⚠️ `updated_at` làm version là cách hay gặp và dễ sai: cột `TIMESTAMP` không có phần lẻ giây thì
  hai lần ghi trong cùng một giây cho cùng giá trị, và đồng hồ các server có thể lệch hoặc lùi.
- ⚠️ Mọi đường ghi (admin sửa tay, job import, câu `UPDATE` hàng loạt) đều phải tăng `version`.
  Một đường ghi quên tăng là một lỗ ABA.

#### Spinlock

*Spinlock* là khoá mà thread chờ **không ngủ**: nó quay vòng kiểm tra liên tục cho tới khi khoá rảnh.
So với mutex thông thường (chờ thì báo OS cho ngủ, được đánh thức khi khoá rảnh):

| | Spinlock | Mutex ngủ (block) |
|---|---|---|
| Chi phí khi chờ | Đốt CPU suốt thời gian chờ | Gần như không tốn CPU |
| Chi phí khi có khoá | Gần như tức thì, không qua OS | Phải context switch để ngủ rồi thức |
| Hợp khi | Critical section cực ngắn (vài chục lệnh), nhiều core, người giữ khoá đang chạy trên core khác | Giữ khoá lâu hoặc không đoán được, có I/O trong critical section |

Spinlock tệ khi:

1. Giữ khoá lâu: các thread chờ đốt CPU mà không làm gì.
2. Chỉ có một core, hoặc người giữ khoá bị OS preempt: thread chờ quay hết time slice của nó trong
   khi người giữ khoá thậm chí không được chạy để nhả khoá. Đây là lý do kernel Linux tắt preemption
   khi giữ spinlock, còn spinlock tự viết ở user space không có đặc quyền đó.
3. Nhiều thread cùng spin trên một biến: mỗi lần CAS là một lần giành quyền ghi cache line chứa biến
   đó giữa các core (*cache line bouncing*), bus bận, chậm cả người giữ khoá.

Một spinlock tối giản bằng Java (minh hoạ, đừng dùng thay `ReentrantLock` trong code thật):

```java
import java.util.concurrent.atomic.AtomicBoolean;

final class SpinLock {
    private final AtomicBoolean locked = new AtomicBoolean(false);

    void lock() {
        while (true) {
            // "test-and-test-and-set": đọc thường trước (chỉ đọc cache của core mình, không tranh ghi),
            // chỉ khi thấy rảnh mới thử CAS
            while (locked.get()) {
                Thread.onSpinWait(); // gợi ý CPU là đang spin (trên x86 thường thành lệnh PAUSE)
            }
            if (locked.compareAndSet(false, true)) {
                return;
            }
        }
    }

    void unlock() {
        locked.set(false);
    }
}
```

Mutex hiện đại lai cả hai: **spin một chút rồi mới ngủ**. Go là ví dụ có mã nguồn dễ đọc
(`src/internal/sync/mutex.go` và `runtime/proc.go`):

- Nhánh nhanh: một CAS từ "rảnh" sang "đã khoá". Không tranh chấp thì xong ngay.
- Nhánh chậm: chỉ spin vài lần, và chỉ khi máy nhiều core, `GOMAXPROCS > 1`, có ít nhất một P khác
  đang chạy và hàng đợi goroutine cục bộ đang trống. Không thoả thì vào hàng chờ và ngủ.
- Chống starvation: waiter chờ quá 1 ms thì mutex chuyển sang *starvation mode*, giao thẳng quyền
  sở hữu cho waiter đầu hàng, goroutine mới đến không được spin hay chen ngang. Nối với phần
  starvation ở [module 1.3](#13-deadlock-livelock-starvation).

HotSpot cũng spin một chút trước khi cho thread chờ `synchronized` đi ngủ, còn glibc có loại mutex
tuỳ chọn `PTHREAD_MUTEX_ADAPTIVE_NP` spin trước khi ngủ; chi tiết tuỳ phiên bản. Kết luận thực dụng: backend gần như không bao giờ cần tự viết spinlock.

#### Ví dụ thực tế trong Java

*`LongAdder` và `AtomicLong`*

- `AtomicLong.incrementAndGet()` là một thao tác atomic trên **một** biến (trong mã nguồn JDK là
  vòng CAS; JIT có thể thay bằng một lệnh atomic của CPU). Khi 32 thread cùng tăng, tất cả giành
  cùng một cache line nên phải lần lượt; với vòng CAS, mỗi lần chỉ một CAS thắng, số còn lại thất
  bại và thử lại. Tranh chấp càng cao, càng chậm.
- `LongAdder` (từ Java 8) chia tổng thành **nhiều biến**: một biến `base` và một mảng ô (*cell*).
  Không tranh chấp thì cộng thẳng vào `base`. Khi CAS trên `base` thất bại (dấu hiệu có tranh chấp),
  thread chuyển sang cộng vào một ô được băm theo thread, và mảng ô có thể lớn dần. Các ô được đệm
  để nằm trên cache line khác nhau, tránh *false sharing* (hai biến độc lập nằm chung một cache line,
  thường 64 byte trên x86-64, nên vẫn tranh nhau như một biến).
- `sum()` cộng `base` với mọi ô.

```java
LongAdder hits = new LongAdder();
hits.increment();                  // gọi từ nhiều thread
long total = hits.sum();           // đọc để báo cáo

// Đếm tần suất theo key, mẫu có trong Javadoc
ConcurrentHashMap<String, LongAdder> freqs = new ConcurrentHashMap<>();
freqs.computeIfAbsent("GET /home", k -> new LongAdder()).increment();
```

Đánh đổi (theo Javadoc): tranh chấp thấp thì hai lớp tương đương; tranh chấp cao thì `LongAdder` cho
throughput cao hơn đáng kể, đổi lại tốn bộ nhớ hơn.

⚠️ `sum()` **không phải snapshot atomic**: đang có thread cộng thì kết quả có thể thiếu các lần cộng
đồng thời. `LongAdder` cũng không có `compareAndSet` hay `incrementAndGet`. Vì vậy nó hợp cho thống kê
(đếm request, metrics), **không** dùng để sinh id tuần tự hay kiểm tra "đạt ngưỡng thì chặn".

*`ConcurrentLinkedQueue`*

- Queue FIFO không giới hạn, lock-free, cài theo thuật toán của Michael và Scott.
- ⚠️ `size()` không phải O(1): phải duyệt cả queue, và kết quả có thể sai nếu queue đang bị sửa.
- ⚠️ Không giới hạn kích thước nên không có *backpressure* (cơ chế bắt bên gửi chậm lại). Producer
  nhanh hơn consumer thì queue phình tới hết heap. Cần giới hạn thì dùng `ArrayBlockingQueue` hoặc
  `LinkedBlockingQueue` có capacity.

*Lock-free có nhanh hơn lock không?*

Không nhất thiết. *Java Concurrency in Practice* mục 15.3.2 đo hai cách cài một bộ sinh số ngẫu
nhiên (lock và `AtomicInteger`): ở mức tranh chấp thực tế hơn (thấp tới vừa), atomic thắng; ở mức
tranh chấp rất cao, lock thường thắng, vì lock cho thread chờ đi ngủ (bớt tốn CPU và bớt lưu lượng
đồng bộ trên bus bộ nhớ), còn vòng CAS thất bại thì thử lại ngay, làm tranh chấp nặng thêm. Cách tốt
nhất cho tranh chấp cao là **bớt chia sẻ** (như `LongAdder` chia ô), không phải đổi primitive.

Ở tầng Redis cũng có bản CAS: từ Redis 8.4, `SET key value IFEQ old` chỉ ghi khi giá trị hiện tại
bằng `old`. Trước đó phải viết Lua script "GET, so sánh, SET" (module 3.4). Cả hai đều chịu ABA như
nhau nếu giá trị có thể quay về cũ.

**Tóm tắt nhanh**
- Lock-free: luôn có ít nhất một thread tiến triển; wait-free: mọi thread đều xong sau hữu hạn bước.
  CAS thất bại nghĩa là người khác vừa thành công.
- ABA: giá trị đổi A -> B -> A, CAS vẫn thành công. Sửa bằng version/stamp tăng dần
  (`AtomicStampedReference`) hoặc không tái sử dụng node (GC, hazard pointer).
- Trong DB: optimistic lock so `version` chỉ tăng, không so cột nghiệp vụ như `status` hay
  `updated_at`.
- Spinlock chỉ hợp critical section cực ngắn trên máy nhiều core; mutex hiện đại spin một chút rồi ngủ.
- `LongAdder` chia bộ đếm thành nhiều ô nên ít tranh chấp hơn `AtomicLong`, nhưng `sum()` không atomic.

**Nguồn**: *Java Concurrency in Practice* ch.15 ·
[Javadoc LongAdder](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/LongAdder.html) ·
[Javadoc AtomicStampedReference](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/atomic/AtomicStampedReference.html) ·
[Javadoc ConcurrentLinkedQueue](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentLinkedQueue.html) ·
[Go: internal/sync/mutex.go](https://github.com/golang/go/blob/master/src/internal/sync/mutex.go) ·
[Redis: SET](https://redis.io/docs/latest/commands/set/)


---

### 3.3 Priority inversion, bulkhead, actor model

Module này trả lời: vì sao việc quan trọng lại có thể phải chờ việc kém quan trọng, cách tách tài
nguyên (bulkhead) để việc này không kéo sập việc kia, và vì sao "mỗi entity chỉ có một người ghi"
(actor model) xoá được tranh chấp mà không cần lock.

#### Priority inversion

*Priority inversion* (đảo ngược ưu tiên) là khi một thread ưu tiên cao bị chặn lâu **không giới hạn**
vì một thread ưu tiên thấp, mà nguyên nhân gián tiếp là một thread ưu tiên trung bình. Cần ba bên:
H (cao), M (trung bình), L (thấp), và một khoá X mà H và L cùng dùng. Scheduler ở đây là
*preemptive priority*: thread ưu tiên cao hơn sẵn sàng chạy thì giành CPU ngay.

| Bước | L (thấp) | H (cao) | M (trung bình) | Kết quả |
|---|---|---|---|---|
| 1 | Lấy khoá X, vào critical section | | | |
| 2 | Bị giành CPU | Thức dậy, cần X, bị chặn | | H chờ L. Chưa sao: L chỉ cần chạy nốt đoạn ngắn |
| 3 | Sẵn sàng nhưng không được chạy | Vẫn chờ | Thức dậy, không cần X, ưu tiên hơn L nên chiếm CPU | M chạy bao lâu, L đứng bấy lâu |
| 4 | Không nhả được X | Chờ mãi | Vẫn chạy | H, thread quan trọng nhất, bị M chặn gián tiếp |

Bước 2 là chặn *có giới hạn* (bounded): H chờ đúng bằng phần critical section còn lại của L, đó là
cái giá bình thường của việc dùng chung khoá. Bước 3 biến nó thành *không giới hạn* (unbounded):
thời gian chờ của H giờ phụ thuộc vào M, một thread chẳng liên quan gì tới khoá X.

*Mars Pathfinder (1997)*: vài ngày sau khi đáp xuống sao Hoả ngày 4/7/1997, tàu liên tục tự reset
toàn hệ thống. Theo bài của Mike Jones kể lại keynote của David Wilner, CTO của Wind River (hãng làm
hệ điều hành thời gian thực VxWorks chạy trên tàu):

1. Tàu có một "information bus" (vùng nhớ chung để các thành phần trao đổi dữ liệu), bảo vệ bằng mutex.
2. H là task quản lý bus, chạy thường xuyên với ưu tiên cao. L là task thu thập dữ liệu khí tượng,
   ưu tiên thấp, lấy mutex để ghi dữ liệu lên bus. M là task truyền thông, ưu tiên trung bình, chạy lâu.
3. Hiếm khi, M được lên lịch đúng lúc H đang chờ mutex do L giữ. M chặn L, L không nhả mutex, H đứng.
4. Một *watchdog timer* (bộ đếm giờ canh chừng, hết giờ mà không ai "báo còn sống" thì coi là hỏng)
   thấy task bus lâu không chạy, kết luận hệ thống hỏng và reset toàn bộ.

Kỹ sư JPL tái hiện được lỗi trên bản sao của tàu nhờ chế độ ghi trace mọi sự kiện (context switch,
dùng khoá, interrupt) của VxWorks. Mutex của VxWorks có một tham số bật *priority inheritance*, và
mutex này đã được tạo với tham số tắt. Họ sửa bằng cách gửi lên tàu một đoạn C nhỏ đổi các biến
toàn cục chứa tham số đó từ FALSE sang TRUE, nhờ tàu được phóng với trình thông dịch C gỡ lỗi vẫn
bật. Bài học trong bài viết: lúc đầu kỹ sư cho rằng task bus quá quan trọng về thời gian nên không
muốn tốn thêm chi phí cho priority inheritance, và đó chính là quyết định sai; một hai lần reset
trong lúc test trước khi phóng cũng đã bị bỏ qua vì không tái hiện được.

Hai cách sửa kinh điển:

- *Priority inheritance*: khi H chờ khoá do L giữ, L tạm được **nâng lên** bằng ưu tiên của H cho
  tới khi nhả khoá. M không còn chen được vào giữa. Linux có tuỳ chọn này cho pthread mutex
  (`PTHREAD_PRIO_INHERIT`).
- *Priority ceiling*: mỗi khoá gắn một mức ưu tiên "trần" bằng ưu tiên cao nhất trong những thread
  có thể dùng nó. Ở biến thể đơn giản hay gặp (*immediate ceiling*), ai lấy được khoá thì chạy ngay ở
  mức trần đó cho tới khi nhả.

Nền lý thuyết là bài báo của Sha, Rajkumar và Lehoczky (1990) về các giao thức priority inheritance.

#### Bản ở tầng backend và bulkhead

Backend web ít khi đặt ưu tiên cho thread, nhưng cùng một hình dạng lỗi xuất hiện mỗi khi **việc
quan trọng và việc kém quan trọng dùng chung một tài nguyên có hạn**: "khoá X" là connection pool,
worker pool, queue, rate limit của bên thứ ba.

| Tình huống | "Khoá" dùng chung | Việc kém quan trọng chiếm chỗ | Việc quan trọng bị chặn |
|---|---|---|---|
| Job xuất báo cáo chạy chung app với API | Connection pool của DB | Query báo cáo giữ connection vài chục giây | Request thanh toán chờ connection rồi timeout |
| Một queue cho mọi SMS | Queue và worker | 300.000 SMS chiến dịch marketing | SMS OTP đứng cuối hàng, tới nơi khi đã hết hạn |
| Một pool PHP-FPM cho cả site | `pm.max_children` | Trang admin export chậm, hoặc một API bên thứ ba chậm | Mọi trang khác chờ worker FPM rảnh (xem [05-php-laravel.md](05-php-laravel.md#34-php-fpm-ở-mức-vận-hành)) |
| Gọi nhiều service qua chung HTTP client pool | Connection tới các service | Service A treo, request tới A giữ connection tới lúc timeout | Gọi service B, C cũng hết connection |

*Bulkhead* (vách ngăn) lấy tên từ vách ngăn trong thân tàu thuỷ: thủng một khoang thì chỉ khoang đó
ngập, tàu không chìm. Ý tưởng: **chia tài nguyên thành các ngăn riêng** theo loại việc hoặc theo
dependency, để một ngăn cạn không kéo theo ngăn khác. Tài liệu Microsoft nêu ba lợi ích: chặn lỗi lan
dây chuyền (*cascading failure*), giữ được một phần chức năng khi một service hỏng, và cho phép chất
lượng dịch vụ khác nhau (pool ưu tiên cao cho consumer quan trọng).

Cách áp trong một hệ thống PHP/Laravel thông thường:

1. **Queue riêng và worker riêng** cho việc gấp:

   ```sh
   # Worker chỉ lo OTP: marketing có dồn bao nhiêu cũng không chạm tới
   php artisan queue:work redis --queue=otp
   # Worker cho phần còn lại
   php artisan queue:work redis --queue=default,marketing
   ```

   ⚠️ `--queue=high,low` trên **một** worker chỉ là ưu tiên khi lấy job (Laravel docs: xử lý hết job
   `high` rồi mới tới `low`). Nó không phải bulkhead: worker đang bận một job `low` chạy 30 giây thì
   job `high` mới đến vẫn phải chờ. Việc có SLA chặt cần worker riêng.
2. **Pool PHP-FPM riêng** cho nhóm route nặng (admin, export): FPM cho khai báo nhiều pool, mỗi pool
   một socket và một `pm.max_children`; Nginx route `location /admin` sang socket của pool đó.
3. **Connection DB riêng** cho báo cáo, tốt nhất trỏ vào replica: báo cáo chậm chỉ làm cạn pool của
   chính nó. Kết hợp với timeout query ngắn cho luồng người dùng.
4. **Giới hạn đồng thời theo dependency**: tối đa N lời gọi song song tới API bên thứ ba chậm, vượt
   thì từ chối ngay thay vì xếp hàng giữ worker. Trong Laravel có thể dùng `Cache::funnel`
   ([05-php-laravel.md](05-php-laravel.md#27-các-thành-phần-khác-của-laravel)) hoặc job middleware
   ([05-php-laravel.md](05-php-laravel.md#26-queue));
   bên Java có resilience4j Bulkhead.

Cách chia ngăn theo tầng, từ nhẹ tới nặng: semaphore trong process, thread pool/worker pool riêng,
process riêng, container hoặc VM riêng, cluster riêng. Microsoft khuyên kết hợp bulkhead với retry,
circuit breaker và throttling.

⚠️ Cái giá: tài nguyên dùng kém hiệu quả hơn (ngăn này rảnh không cho ngăn kia mượn), cấu hình và
giám sát phức tạp hơn. Microsoft ghi rõ pattern không hợp khi không chấp nhận được việc dùng tài
nguyên kém hiệu quả, hoặc khi hệ thống chưa cần độ phức tạp đó. Kích thước từng ngăn tính theo
Little's law ([module 2.4](#24-thread-pool-connection-pool-littles-law)), không đoán.

#### Actor model (đại ý)

Mọi race condition cần hai điều kiện: state **dùng chung** và **nhiều bên cùng ghi**. Lock giữ
nguyên hai điều kiện đó rồi bắt các bên xếp hàng. Actor model bỏ hẳn điều kiện đầu:

- Một *actor* là một đơn vị có **state riêng** (không ai khác đọc hay ghi trực tiếp) và một hộp thư
  (*mailbox*).
- Muốn actor làm gì thì gửi *message* vào mailbox. Actor lấy từng message ra xử lý **tuần tự**, một
  lần một message. Khi xử lý, nó có thể đổi state của mình, gửi message cho actor khác, hoặc tạo
  actor mới.
- Vì chỉ có một luồng chạm vào state, không cần lock. Tranh chấp chuyển thành **thứ tự trong mailbox**.

Go không có "actor" chính thức nhưng viết được đúng ý này bằng goroutine và channel, theo tinh thần
Effective Go "đừng giao tiếp bằng cách chia sẻ bộ nhớ, hãy chia sẻ bộ nhớ bằng cách giao tiếp".
Chạy `go mod init actor && go run -race .`:

```go
// Actor tối giản: một goroutine sở hữu state, mọi thay đổi đi qua mailbox (channel).
package main

import (
	"fmt"
	"sync"
)

// Message gửi vào mailbox. reply là "địa chỉ trả lời" cho kiểu request/response.
type withdraw struct {
	amount int
	reply  chan error
}

type account struct {
	mailbox chan withdraw
}

func newAccount(balance int) *account {
	a := &account{mailbox: make(chan withdraw, 100)} // mailbox có giới hạn: đầy thì người gửi phải chờ
	go func() {
		// Chỉ goroutine này đọc và ghi balance, nên không cần mutex.
		for msg := range a.mailbox {
			if msg.amount > balance {
				msg.reply <- fmt.Errorf("không đủ tiền: còn %d", balance)
				continue
			}
			balance -= msg.amount
			msg.reply <- nil
		}
	}()
	return a
}

func (a *account) Withdraw(amount int) error {
	reply := make(chan error, 1)
	a.mailbox <- withdraw{amount: amount, reply: reply}
	return <-reply // request/response phải tự dựng trên hai chiều message
}

func main() {
	acc := newAccount(100)
	var wg sync.WaitGroup
	var mu sync.Mutex
	ok := 0
	for range 10 {
		wg.Go(func() { // WaitGroup.Go có từ Go 1.25
			if acc.Withdraw(30) == nil {
				mu.Lock()
				ok++
				mu.Unlock()
			}
		})
	}
	wg.Wait()
	fmt.Println("số lần rút thành công:", ok) // luôn là 3: 3 x 30 = 90 <= 100
}
```

Ví dụ ngoài đời:

- *Erlang/Elixir*: mỗi process của máy ảo BEAM là một actor rất nhẹ, có mailbox riêng. Đi kèm triết
  lý "let it crash": process lỗi thì chết, một *supervisor* (process giám sát) khởi động lại nó.
- *Akka* trên JVM. Từ 2022 Akka đổi sang giấy phép BSL; bản fork giữ giấy phép Apache là Apache Pekko.

Đánh đổi:

- ⚠️ Mailbox có thể đầy hoặc phình. Mailbox của process Erlang và mailbox mặc định của Akka không
  giới hạn, nên actor xử lý chậm hơn tốc độ nhận làm bộ nhớ tăng dần. Channel có buffer trong Go là
  mailbox có giới hạn: đầy thì bên gửi bị chặn (backpressure).
- ⚠️ Một actor là một điểm tuần tự: actor "hot" (mọi người cùng gửi cho một actor) chính là hot row
  của thế giới actor ([module 3.4](#34-tranh-chấp-cực-cao-flash-sale-hot-row)).
- Khó debug hơn: lỗi là một chuỗi message qua nhiều actor, không có stack trace liền mạch.
- Kiểu request/response phải viết thành bất đồng bộ (gửi message kèm địa chỉ trả lời, chờ message
  trả về, tự lo timeout).
- Hai actor chờ trả lời của nhau vẫn deadlock được. Actor bỏ lock chứ không bỏ được mọi lỗi concurrency.

#### "Một writer cho mỗi entity" ở quy mô hệ thống

Áp actor model cho cả hệ thống phân tán: **mọi thay đổi của cùng một entity đi qua một chỗ duy nhất,
theo thứ tự**, còn các entity khác nhau vẫn xử lý song song. Không cần lock phân tán cho từng entity.

```
producer                      Kafka topic "orders" (3 partition)       consumer group
 order_id=7  ─┐  hash(key)    ┌ partition 0: 7, 7, 19, 7 ─────────────> consumer A
 order_id=19 ─┼─────────────> ├ partition 1: 8, 11, 8    ─────────────> consumer B
 order_id=8  ─┘               └ partition 2: 5, 5        ─────────────> consumer C
Mọi message của order 7 vào cùng partition 0, và partition 0 chỉ do một consumer trong group đọc,
theo đúng thứ tự ghi. Đó là "một writer cho order 7".
```

- *Kafka partition theo key*: partitioner mặc định băm key để chọn partition, nên cùng key thì cùng
  partition; Kafka đảm bảo thứ tự **trong một partition**, và trong một consumer group mỗi partition
  chỉ giao cho một consumer tại một thời điểm.
  - ⚠️ Tăng số partition làm đổi ánh xạ key sang partition; message cũ và mới của cùng key có thể
    nằm ở hai partition khác nhau trong giai đoạn chuyển.
  - ⚠️ Consumer tự xử lý song song nhiều message trong một partition (thread pool bên trong) là tự
    phá đảm bảo thứ tự.
  - ⚠️ Rebalance (partition chuyển sang consumer khác) có thể làm một message được xử lý hai lần,
    nên consumer vẫn phải idempotent ([module 2.3](#23-double-submit-idempotency-key)).
- *SQS FIFO message group*: message cùng `MessageGroupId` được xử lý lần lượt theo thứ tự; các group
  khác nhau chạy song song.
- Trong một app PHP: dùng key định tuyến như trên cho queue, hoặc ít nhất job middleware
  `WithoutOverlapping` theo id entity để hai job của cùng một entity không chạy chồng nhau (chỉ chặn
  chạy song song, không giữ thứ tự; xem [05-php-laravel.md](05-php-laravel.md#26-queue)).

Chi tiết Kafka và SQS ở [12-messaging.md](../12-messaging.md).

**Tóm tắt nhanh**
- Priority inversion cần ba bên: H chờ khoá của L, M chiếm CPU của L nên H chờ không giới hạn. Sửa
  bằng priority inheritance (hoặc priority ceiling).
- Mars Pathfinder 1997: mutex VxWorks tạo với priority inheritance tắt, watchdog reset tàu; sửa bằng
  cách bật tham số từ Trái Đất.
- Bản backend: việc quan trọng và việc kém quan trọng chung một pool, queue, worker. Sửa bằng
  bulkhead: pool riêng, queue riêng và **worker riêng**, không chỉ thứ tự ưu tiên trên một worker.
- Actor: state riêng + mailbox + xử lý tuần tự, nên không cần lock; cái giá là mailbox phình, khó
  debug, request/response bất đồng bộ.
- "Một writer cho mỗi entity": Kafka partition theo key, SQS FIFO message group.

**Nguồn**: [What really happened on Mars Rover Pathfinder](https://www.cs.cornell.edu/courses/cs614/1999sp/papers/pathfinder.html) ·
[Microsoft: Bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead) ·
[Laravel: Queue priorities](https://laravel.com/docs/13.x/queues#queue-priorities) ·
[Effective Go: Concurrency](https://go.dev/doc/effective_go#concurrency)


---

### 3.4 Tranh chấp cực cao: flash sale, hot row

Module này trả lời: vì sao cách chống oversell đúng ở tải thường (`FOR UPDATE`, atomic update) lại
làm sập cả hệ thống khi 10.000 người cùng mua 100 sản phẩm, và cách chặn ở nhiều tầng để DB chỉ còn
là chốt chặn cuối. Đây là phần concurrency của bài flash sale; phần kiến trúc đầy đủ ở
[16-system-design.md](../16-system-design.md) (module 3.2).

#### Vì sao cách thông thường sập

*Hot row* là một dòng mà rất nhiều transaction cùng muốn sửa, ví dụ dòng tồn kho của sản phẩm đang
sale. Mọi cách ghi an toàn vào một dòng (khoá bi quan `FOR UPDATE`, hay `UPDATE ... WHERE stock > 0`)
đều phải lấy **row lock** trên dòng đó, nên các transaction ghi dòng này bắt buộc chạy **tuần tự**.
Chuyện gì xảy ra với 10.000 request `SELECT ... FOR UPDATE` cùng lúc:

1. Mỗi lúc chỉ một transaction giữ khoá, 9.999 cái còn lại xếp hàng chờ khoá.
2. Mỗi transaction đang chờ vẫn **giữ một connection DB** (và một worker PHP-FPM đứng chờ theo).
3. Connection pool và worker pool cạn. Request không liên quan tới sale (xem trang chủ, đăng nhập,
   thanh toán đơn khác) cũng không lấy được connection. Đây là priority inversion ở tầng hệ thống
   ([module 3.3](#33-priority-inversion-bulkhead-actor-model)).
4. Request timeout, client bấm lại hoặc tự retry, tải tăng thêm. Timeout lan dây chuyền.

Ước lượng thô để thấy vì sao không thể "cho DB mạnh hơn" (con số giả định để tính nhẩm, không phải
đo thật): nếu mỗi transaction giữ khoá 5 ms (đọc, tính, ghi, commit, cộng round-trip mạng), thì một
hot row xử lý tối đa khoảng 1 / 0,005 = 200 transaction mỗi giây, **bất kể DB có bao nhiêu core**,
vì các transaction không chạy song song được trên cùng một dòng. 10.000 request cần khoảng 50 giây
chỉ để đi qua dòng đó. Theo Little's law ([module 2.4](#24-thread-pool-connection-pool-littles-law)),
số request đang chờ đồng thời lúc đỉnh là hàng nghìn, lớn hơn nhiều so với bất kỳ pool nào.

Hệ quả thiết kế:

- Giảm **thời gian giữ khoá** trên hot row (atomic update một câu thay cho `FOR UPDATE` rồi tính ở
  app; xem bảng so sánh ở [03-database-sql.md](03-database-sql.md#26-lock-thực-dụng)).
- Giảm **số request chạm tới hot row**: đa số request sẽ thua, hãy cho chúng thua ở tầng rẻ.
- Giảm **số request chờ**: chờ khoá lâu còn tệ hơn thua ngay. MySQL có `NOWAIT` và `SKIP LOCKED` cho
  `SELECT ... FOR UPDATE`, và `innodb_lock_wait_timeout` (mặc định 50 giây) đặt được theo session.

#### Chặn sớm

Mục tiêu: **từ chối rẻ**, trước khi request chạm tới DB. Traffic tăng hàng trăm lần trong vài giây,
nhưng chỉ 100 đơn thành công, nên hầu hết request đằng nào cũng bị từ chối.

```
10.000 người
   │  Client: nút "Mua" disable tới đúng giờ, chống bấm liên tục, captcha
   ▼
 CDN: trang sản phẩm, ảnh, JS là tĩnh; server không nhận các request này
   ▼
 Gateway / Nginx: rate limit theo user và IP, chặn bot
   ▼
 Waiting room: chỉ cho N người/giây vào luồng mua
   ▼
 Flash sale service: Redis trừ kho (tầng đầu tiên có "sự thật" về số lượng)
   ▼
 Queue ──> Worker ──> MySQL (chốt chặn cuối, tải đã được làm phẳng)
```

- *Rate limit*: giới hạn số request mỗi user (và mỗi IP) trong một cửa sổ thời gian. Trong Laravel
  là middleware `throttle`; ở tầng Nginx/gateway rẻ hơn nữa vì không tốn worker PHP.
- *Waiting room* (phòng chờ): người dùng vào một hàng đợi ảo, được cấp token vào luồng mua theo lượt,
  với tốc độ mà hệ thống phía sau chịu được. Biến một cú đỉnh vài giây thành một dòng chảy đều. Nhiều
  CDN có sẵn tính năng này.
- *Cô lập*: flash sale chạy trên pool worker, connection pool, thậm chí cluster riêng (bulkhead,
  [module 3.3](#33-priority-inversion-bulkhead-actor-model)), để sale có sập thì luồng mua hàng
  thường vẫn sống.
- Scale **trước** giờ mở bán. Autoscale phản ứng theo phút, đỉnh flash sale tính bằng giây.

#### Luồng trừ tồn kho nhiều tầng

Nguyên tắc: mỗi tầng chặn một loại lỗi, và tầng sau không tin tầng trước.

1. **Redis trừ kho atomic.** Redis thực thi lệnh tuần tự trên một luồng, nên `DECR` là atomic. Nhưng
   `DECR` một mình không kiểm tra được "còn hàng không" và "user này mua chưa" trong cùng một bước.
   Có hai cách:
   - `DECR` rồi xem kết quả: nhỏ hơn 0 thì `INCR` trả lại và báo hết. Đơn giản, nhưng không chặn
     được mua trùng.
   - Lua script: Redis chạy cả script như một khối atomic, không lệnh nào khác chen vào giữa. Kiểm
     tra, trừ, ghi nhận người mua trong một bước:

   ```php
   <?php
   declare(strict_types=1);

   use Illuminate\Support\Facades\Redis;

   // Trả về 1: giữ được suất; 0: hết hàng; -1: user này đã có suất.
   // {sale:42} là hash tag: trên Redis Cluster, hai key cùng tag nằm cùng slot,
   // điều kiện bắt buộc để một script dùng được cả hai key.
   function tryReserve(int $saleId, int $userId): int
   {
       $script = <<<'LUA'
           if redis.call('SISMEMBER', KEYS[2], ARGV[1]) == 1 then
               return -1
           end
           local stock = tonumber(redis.call('GET', KEYS[1]) or '0')
           if stock <= 0 then
               return 0
           end
           redis.call('DECR', KEYS[1])
           redis.call('SADD', KEYS[2], ARGV[1])
           return 1
       LUA;

       return (int) Redis::eval(
           $script,
           2,
           "{sale:{$saleId}}:stock",
           "{sale:{$saleId}}:buyers",
           (string) $userId,
       );
   }
   ```

   Trước giờ mở bán, nạp tồn kho: `SET {sale:42}:stock 100`.
   ⚠️ Script chạy atomic nên cũng **chặn** mọi lệnh khác trong lúc chạy; giữ script ngắn, không lặp
   trên tập lớn.
2. **Người trúng vào queue.** API trả ngay "đang xử lý đơn của bạn", không chờ DB. Queue làm phẳng
   đỉnh: worker ghi DB với tốc độ DB chịu được, số worker quyết định số transaction đồng thời trên
   hot row (ít worker = ít chờ khoá).
3. **Worker ghi DB, atomic update có điều kiện là chốt chặn cuối.** Redis có lệch thì đây vẫn chặn
   oversell:

   ```sql
   START TRANSACTION;
   -- (a) Tạo đơn trước: dòng mới, không tranh chấp với ai.
   --     Unique (user_id, sale_id) chặn một người hai đơn, kể cả khi job bị chạy lại.
   INSERT INTO sale_orders (sale_id, user_id, status, expires_at)
   VALUES (42, 7, 'pending_payment', NOW() + INTERVAL 10 MINUTE);
   -- (b) Chạm hot row SAU CÙNG, ngay trước COMMIT: giữ row lock ngắn nhất có thể.
   UPDATE flash_sales SET sold = sold + 1 WHERE id = 42 AND sold < quota;
   -- Code worker kiểm tra affected rows: 1 thì COMMIT;
   -- 0 thì hết hàng thật, ROLLBACK (đơn ở bước a cũng mất) và báo user
   COMMIT;
   ```

   Vì sao thứ tự (a) rồi (b): row lock giữ tới lúc transaction kết thúc. Làm `UPDATE` hot row trước
   thì mọi việc sau đó (insert, gọi service khác) đều diễn ra trong lúc đang giữ khoá, người khác chờ
   lâu hơn.
4. **Unique `(user_id, sale_id)`** là chốt chặn mua trùng cuối cùng, và biến việc worker chạy lại
   một job (retry, rebalance) thành vô hại: lần hai gặp lỗi duplicate key, worker coi là đã xong.
   Chi tiết idempotency ở [module 2.3](#23-double-submit-idempotency-key).

```sql
CREATE TABLE sale_orders (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  sale_id BIGINT NOT NULL,
  user_id BIGINT NOT NULL,
  status VARCHAR(20) NOT NULL,
  expires_at DATETIME NOT NULL,
  UNIQUE KEY uq_sale_user (sale_id, user_id),
  KEY idx_expire (status, expires_at)
);
```

#### Giữ chỗ và đối soát

*Giữ chỗ có hạn*: trúng suất chưa phải đã mua. Đơn ở trạng thái `pending_payment` với `expires_at`,
ví dụ 10 phút. Hết hạn mà chưa thanh toán thì trả lại kho. Job trả kho phải là một **chuyển trạng
thái có điều kiện**, vì nó chạy đua với callback thanh toán đến muộn:

```sql
-- Job quét đơn hết hạn. Chỉ bên nào đổi được status mới được làm tiếp.
UPDATE sale_orders SET status = 'expired'
WHERE id = ? AND status = 'pending_payment' AND expires_at < NOW();
-- affected = 1: trong cùng transaction trả kho ở DB (UPDATE flash_sales SET sold = sold - 1 ...),
--               commit xong mới INCR ở Redis
-- affected = 0: callback thanh toán đã thắng (status = 'paid'), không làm gì

-- Callback thanh toán, cùng kiểu điều kiện:
UPDATE sale_orders SET status = 'paid' WHERE id = ? AND status = 'pending_payment';
-- affected = 0: đơn đã hết hạn -> hoàn tiền tự động, không giao hàng
```

Đây là CAS trên cột `status`. Nó an toàn ở đây vì trạng thái chỉ đi một chiều
(`pending_payment -> paid` hoặc `-> expired`, không quay lại); nếu có đường quay về
`pending_payment` thì phải thêm `version` để tránh ABA ([module 3.2](#32-lock-free-aba-spinlock)).
Cả trả kho ở DB và `INCR` ở Redis nên nằm sau một điều kiện kiểu này, để một đơn chỉ trả kho một lần.

*Redis lệch DB theo hướng nào thì chấp nhận được*. Redis và DB là hai hệ thống, không có transaction
chung, nên chắc chắn sẽ lệch (worker crash giữa chừng, Redis mất dữ liệu khi restart, trả kho ở DB
xong nhưng `INCR` Redis lỗi):

| Hướng lệch | Hậu quả | Chấp nhận? |
|---|---|---|
| Redis **thấp hơn** thật (Redis nghĩ đã bán nhiều hơn DB) | Từ chối người mua dù DB còn hàng: *bán thiếu* | Được. Mất doanh thu nhỏ; đối soát sau sale rồi mở bán nốt |
| Redis **cao hơn** thật (Redis nghĩ còn hàng khi DB đã hết) | Nhiều người qua Redis hơn số hàng; câu `UPDATE ... sold < quota` ở DB từ chối số dư | Được **nhờ DB chặn**: không oversell, nhưng vài người bị báo "đang xử lý" rồi mới biết hết. Vì vậy API chỉ nói "đang xử lý", không nói "thành công", tới khi DB xác nhận |
| DB không có chốt chặn, tin Redis tuyệt đối | Redis cao hơn thật là oversell thật | Không bao giờ |

Quy tắc: lệch về phía **bán thiếu** thì được, lệch về phía **bán vượt** thì DB phải chặn. Thiết kế sao
cho mọi lỗi giữa chừng rơi vào hướng an toàn: trừ Redis trước, ghi DB sau (lỗi giữa chừng thì Redis
thấp hơn thật).

*Đối soát sau đợt sale*: so `stock` còn lại ở Redis và kích thước set `buyers` với `quota - sold` và số
dòng `sale_orders` ở DB; tìm user có trong Redis mà không có đơn DB (job mất) và ngược lại. DB là
nguồn sự thật, Redis chỉ là bộ lọc.

#### Chia nhỏ điểm nóng

Khi một dòng (hoặc một key Redis) là nút cổ chai tuần tự, cách mạnh nhất là **bớt chia sẻ**: chia nó
thành nhiều phần độc lập, giống `LongAdder` chia bộ đếm thành nhiều ô ([module 3.2](#32-lock-free-aba-spinlock)).

```sql
-- 100 suất chia thành 10 bucket, mỗi bucket 10 suất
CREATE TABLE sale_buckets (
  sale_id BIGINT NOT NULL,
  bucket  INT NOT NULL,
  remaining INT NOT NULL,
  PRIMARY KEY (sale_id, bucket)
);
-- Mỗi request chọn ngẫu nhiên một bucket; 0 dòng thì thử bucket khác
UPDATE sale_buckets SET remaining = remaining - 1
WHERE sale_id = 42 AND bucket = ? AND remaining > 0;
```

- Mười dòng thì có tới mười transaction ghi song song, trần throughput nhân lên khoảng mười lần.
- Redis Cluster: đặt các bucket key với hash tag khác nhau (`{sale:42:b0}`, `{sale:42:b1}`...) để chúng
  nằm trên nhiều node, chia tải của một *hot key* (key nóng dồn hết vào một node).
- ⚠️ Gần cuối đợt, phần lớn bucket đã về 0, request thử trượt nhiều lần. Cần giới hạn số lần thử,
  hoặc giữ một bảng/set các bucket còn hàng.
- ⚠️ Tổng tồn kho giờ là tổng các bucket, không còn một con số để đọc nhanh; "còn hàng không" trên UI
  nên đọc từ cache xấp xỉ.
- ⚠️ Chống mua trùng không còn nằm cùng key với tồn kho (khác bucket, khác slot), nên không gói chung
  vào một Lua script được. Tách thành hai bước: giành quyền mua bằng `SET {sale:42}:user:7 1 NX EX 600`
  (lệnh `SET` với `NX` chỉ ghi khi key chưa có, `EX` đặt hạn theo giây), trừ bucket thất bại thì xoá
  key đó; unique ở DB vẫn là chốt cuối.

Cách khác cho hot row: worker gom nhiều lượt trừ trong một khoảng ngắn thành một câu `UPDATE` (ví dụ
`sold = sold + 20`), đổi độ trễ lấy ít lượt khoá hơn; khi đó phải tự xử lý trường hợp chỉ còn ít hơn
số đã gom.

**Tóm tắt nhanh**
- Hot row buộc các transaction ghi nó chạy tuần tự; trần throughput là 1 / thời gian giữ khoá, không
  tăng theo số core. `FOR UPDATE` với hàng nghìn request làm cạn connection pool của cả hệ thống.
- Từ chối rẻ và sớm: client, CDN, rate limit, waiting room; chạy sale trong ngăn riêng (bulkhead).
- Luồng: Redis Lua (kiểm tra kho + chống mua trùng, atomic) -> queue -> worker atomic update
  `sold < quota` -> unique `(user_id, sale_id)`. Trong transaction, chạm hot row sau cùng.
- Giữ chỗ có hạn; trả kho bằng chuyển trạng thái có điều kiện để không đua với callback thanh toán.
- Redis thấp hơn DB (bán thiếu) chấp nhận được; Redis cao hơn DB thì DB phải chặn. DB là nguồn sự thật.
- Chia tồn kho thành bucket để tách hot row / hot key, trả giá bằng độ phức tạp cuối đợt.

**Nguồn**: [Redis: SET](https://redis.io/docs/latest/commands/set/) ·
[Laravel: Redis, Lua scripts](https://laravel.com/docs/13.x/redis#lua-scripts) ·
[16-system-design.md](../16-system-design.md) (module 3.2 Flash sale)

---

### 3.5 Kiểm thử và điều tra lỗi concurrency

Module này trả lời: bug concurrency chỉ hiện ra ở một vài thứ tự chạy hiếm gặp, vậy làm sao bắt nó
trong test, làm sao tái hiện nó trên app web, làm sao điều tra khi nó đã xảy ra trên production, và
công cụ của Go, Java, MySQL mỗi cái bắt được gì, bỏ sót gì.

Vì sao khó: test thông thường chạy một thứ tự thực thi; race condition cần một thứ tự cụ thể mà
scheduler hiếm khi chọn. Chạy 100 lần thấy pass nghĩa là 100 lần scheduler không chọn thứ tự xấu,
không có nghĩa là thứ tự xấu không tồn tại. Có ba hướng tấn công, và module này đi qua cả ba:

1. **Công cụ phân tích lúc chạy**: theo dõi truy cập bộ nhớ và báo data race dù lần chạy đó cho kết
   quả đúng (Go `-race`).
2. **Ép thứ tự xấu xảy ra**: stress test (chạy rất nhiều lần, thật song song), hoặc test điều khiển
   thứ tự xen kẽ một cách xác định (hai session DB, đồng hồ ảo của `synctest`).
3. **Lập luận và chốt chặn**: viết ra bất biến, đặt constraint để DB từ chối trạng thái sai dù code
   có race.

#### Go

*Race detector.* Thêm cờ `-race` vào lệnh go: `go test -race ./...`, `go run -race main.go`,
`go build -race`. Compiler chèn code theo dõi vào mỗi lần đọc/ghi bộ nhớ, runtime (dựa trên
ThreadSanitizer) ghi lại quan hệ happens-before giữa các goroutine
([module 3.1](#31-memory-model)). Hai truy cập cùng một biến, ít nhất một là ghi, mà không có
happens-before giữa chúng thì bị báo, **kể cả khi lần chạy đó ra kết quả đúng**. Đây là điểm mạnh
lớn nhất: nó không cần thứ tự xấu thật sự xảy ra, chỉ cần hai truy cập xung đột cùng được chạy tới.

Thử với một bộ đếm có mutex nhưng `Inc` quên dùng (lưu hai file vào thư mục `counter`, tạo `go.mod`
bằng `go mod init counter`):

```go
// counter.go
package counter

import "sync"

// Counter đếm số lượt truy cập. Bản này CỐ Ý có data race.
type Counter struct {
	mu sync.Mutex // có mutex nhưng Inc quên dùng
	n  int
}

func (c *Counter) Inc() { c.n++ } // data race: đọc-sửa-ghi không khoá

func (c *Counter) Value() int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.n
}
```

```go
// counter_test.go
package counter

import (
	"sync"
	"testing"
)

func TestCounterConcurrent(t *testing.T) {
	var c Counter
	var wg sync.WaitGroup
	for range 100 {
		wg.Go(func() { c.Inc() }) // wg.Go: Go 1.25+
	}
	wg.Wait()
	if got := c.Value(); got != 100 {
		t.Errorf("Value() = %d, want 100", got)
	}
}
```

Kết quả khi chạy thử (Go 1.25, macOS arm64): `go test -count=1` năm lần thì một lần `ok`, bốn lần
`FAIL`. Đó là test *flaky*, lúc pass lúc fail, và lần pass không chứng minh gì. `go test -race` thì
lần nào cũng báo (rút gọn, bỏ đường dẫn):

```
WARNING: DATA RACE
Read at 0x00c0000102c8 by goroutine 10:
  counter.(*Counter).Inc()          counter.go:12
Previous write at 0x00c0000102c8 by goroutine 8:
  counter.(*Counter).Inc()          counter.go:12
Goroutine 10 (running) created at:
  counter.TestCounterConcurrent()   counter_test.go:13
...
--- FAIL: TestCounterConcurrent (0.00s)
    testing.go:1617: race detected during execution of test
```

Báo cáo gồm stack của hai truy cập xung đột và stack nơi tạo ra từng goroutine. Có race thì test
fail dù assertion có pass. Với binary build bằng `-race`, chương trình vẫn chạy tiếp, in
`Found 1 data race(s)` khi kết thúc và thoát với exit code 66 (giá trị mặc định của tuỳ chọn
`exitcode`).

Một ví dụ cho thấy `time.Sleep` không phải là đồng bộ:

```go
func main() {
	x := 0
	go func() { x = 1 }()   // ghi
	time.Sleep(time.Second) // "chắc chắn" goroutine kia đã chạy xong
	fmt.Println(x)          // đọc: vẫn là data race
}
```

Chạy thật in `1` gần như mọi lần, nhưng `-race` vẫn báo `WARNING: DATA RACE`: sleep không tạo
happens-before, nên theo memory model lần đọc không được đảm bảo thấy lần ghi.

Tuỳ chọn và chi phí (theo tài liệu Data Race Detector):

| Mục | Chi tiết |
|---|---|
| Biến môi trường | `GORACE="option=val ..."`: `log_path` (mặc định stderr), `exitcode` (mặc định 66), `halt_on_error` (mặc định 0, đặt 1 để dừng ở race đầu tiên), `atexit_sleep_ms` (mặc định 1000) |
| Build tag | Build với `-race` thì tag `race` được bật; dùng `//go:build !race` để loại test quá chậm dưới race detector |
| Chi phí | Tuỳ chương trình, thường bộ nhớ tăng 5–10 lần, thời gian chạy tăng 2–20 lần |
| Yêu cầu | Cần cgo; ngoài macOS cần có C compiler. Chỉ hỗ trợ một số nền tảng (có linux/amd64, linux/arm64, darwin/amd64, darwin/arm64, windows/amd64...) |

⚠️ Giới hạn quan trọng nhất: race detector **chỉ bắt race xảy ra trong lần chạy đó**. Đoạn code
không được chạy tới, hoặc chỉ chạy bởi một goroutine trong test, thì không được kiểm tra. Hệ quả:

- Test phải thật sự chạy code **đồng thời** (nhiều goroutine gọi cùng lúc), không chỉ gọi tuần tự.
- Coverage thấp thì race detector thấy ít. Tài liệu Go gợi ý chạy thêm một binary build bằng
  `-race` dưới tải giống thật (ví dụ một instance canary hoặc môi trường staging), chấp nhận chi phí
  ở trên.
- Kết hợp với `go test -count=N` (chạy lặp) và `-cpu 1,2,4` (chạy với nhiều giá trị GOMAXPROCS) để
  tăng số thứ tự xen kẽ được thử.
- ⚠️ Race detector chỉ thấy bộ nhớ của **một process Go**. Hai instance cùng đọc-rồi-ghi một dòng
  MySQL là race condition, không phải data race, và `-race` không bao giờ thấy nó
  ([module 1.1](#11-concurrency-race-condition-critical-section) phân biệt hai khái niệm).

*`testing/synctest`.* Code concurrent hay dính tới thời gian: timeout, retry có backoff, ticker. Test
bằng thời gian thật thì phải chờ thật (chậm) và phải đoán "đợi bao lâu là đủ" (flaky: 10 ms là dài
trên laptop nhưng ngắn trên CI đang quá tải). `synctest` giải quyết bằng một "bubble":

- `synctest.Test(t, f)` chạy `f` trong một bubble. Mọi goroutine sinh ra bên trong thuộc bubble đó.
- Trong bubble, package `time` dùng **đồng hồ ảo**, bắt đầu từ nửa đêm UTC ngày 2000-01-01.
- Đồng hồ ảo chỉ nhảy khi **mọi goroutine trong bubble bị chặn bền** (*durably blocked*): bị chặn
  và chỉ goroutine khác trong cùng bubble mới gỡ được. Khi đó nó nhảy thẳng tới mốc thời gian gần
  nhất có thể đánh thức ai đó. Vì vậy `time.Sleep(5 * time.Second)` trả về ngay.
- `synctest.Wait()` chờ tới khi mọi goroutine khác trong bubble đều bị chặn bền: "hệ thống đã
  lắng xuống", giờ kiểm tra được. Race detector hiểu `Wait`, nên đọc biến sau `Wait` không bị báo race.
- Các thao tác chặn bền: gửi/nhận trên channel tạo **trong** bubble, `select` mà mọi case là channel
  trong bubble, `sync.Cond.Wait`, `sync.WaitGroup.Wait` (khi `Add` gọi trong bubble), `time.Sleep`.
- ⚠️ Không chặn bền: khoá `sync.Mutex`/`RWMutex`, I/O mạng thật, system call. Test code mạng thì
  dùng mạng giả trong bộ nhớ, ví dụ `net.Pipe()`.
- Hết `f` mà còn goroutine kẹt trong bubble thì test fail: `synctest` bắt được goroutine leak.

Lịch sử phiên bản: Go 1.24 có bản thử nghiệm sau `GOEXPERIMENT=synctest` với API cũ
`synctest.Run(func())` (blog "Testing concurrent code with testing/synctest" viết theo API này).
Go 1.25 đưa lên GA với `synctest.Test(t, func(t *testing.T))`; release notes 1.25 báo API cũ sẽ bị bỏ
ở Go 1.26. Go 1.27 thêm
`synctest.Sleep(d)`, tương đương `time.Sleep(d)` rồi `synctest.Wait()`.

Ví dụ: hàm gọi dịch vụ báo giá, bỏ cuộc sau 5 giây. Test kiểm tra đúng 5 giây là timeout, mà
chạy tức thì:

```go
// quote.go
package quote

import (
	"context"
	"time"
)

// GetPrice gọi dịch vụ báo giá, bỏ cuộc sau 5 giây.
func GetPrice(ctx context.Context, fetch func(context.Context) (int, error)) (int, error) {
	ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()

	type result struct {
		price int
		err   error
	}
	ch := make(chan result, 1) // buffer 1: goroutine không kẹt nếu ta đã bỏ đi
	go func() {
		p, err := fetch(ctx)
		ch <- result{p, err}
	}()

	select {
	case r := <-ch:
		return r.price, r.err
	case <-ctx.Done():
		return 0, ctx.Err()
	}
}
```

```go
// quote_test.go
package quote

import (
	"context"
	"errors"
	"testing"
	"testing/synctest"
	"time"
)

func TestGetPriceTimeout(t *testing.T) {
	synctest.Test(t, func(t *testing.T) {
		start := time.Now() // đồng hồ ảo
		// Dịch vụ giả: trả lời sau 10 giây (ảo), hoặc dừng khi ctx bị huỷ.
		slow := func(ctx context.Context) (int, error) {
			select {
			case <-time.After(10 * time.Second):
				return 42, nil
			case <-ctx.Done():
				return 0, ctx.Err()
			}
		}

		_, err := GetPrice(t.Context(), slow)

		if !errors.Is(err, context.DeadlineExceeded) {
			t.Fatalf("err = %v, want DeadlineExceeded", err)
		}
		if got := time.Since(start); got != 5*time.Second {
			t.Fatalf("elapsed = %v, want 5s", got)
		}
	})
}
```

`go test -v` in `--- PASS: TestGetPriceTimeout (0.00s)`. Thời gian đo được chính xác bằng 5 giây vì
đồng hồ là ảo, nên assertion `== 5*time.Second` không flaky. Thử đổi `make(chan result, 1)` thành
`make(chan result)` (không buffer): sau timeout không ai nhận từ `ch`, goroutine gọi `fetch` kẹt mãi ở
lệnh gửi. Không có `synctest`, test vẫn pass và goroutine rò rỉ âm thầm. Có `synctest`, test fail
(output thật, rút gọn):

```
--- FAIL: TestGetPriceTimeout (0.00s)
panic: deadlock: main bubble goroutine has exited but blocked goroutines remain
goroutine 10 [chan send (durable), synctest bubble 1]:
quote.GetPrice.func1()   quote.go:21
```

*Goroutine leak profile.* Go 1.26 thêm profile `goroutineleak` dạng thử nghiệm (bật bằng
`GOEXPERIMENT=goroutineleakprofile`); Go 1.27 đưa lên GA và bỏ cờ experiment. Có trong
`runtime/pprof` và endpoint `/debug/pprof/goroutineleak` của `net/http/pprof`. Cơ chế dựa vào garbage
collector: goroutine G bị chặn trên primitive P (channel, mutex, cond), mà P không còn tới được từ bất
kỳ goroutine nào đang chạy được (hay goroutine mà chúng có thể đánh thức), thì G không bao giờ thức dậy nữa, tức là rò rỉ. Ví dụ điển hình là
lỗi ở trên: hàm trả về sớm, channel không buffer không còn ai giữ. ⚠️ Vì dựa trên khả năng tới được,
nó bỏ sót trường hợp primitive nằm trong biến global hoặc biến local của goroutine còn chạy.

*Điều tra trên process đang chạy.* Khi service treo hoặc số goroutine tăng mãi:

- Import `net/http/pprof` (import `_`, nó tự đăng ký handler vào `http.DefaultServeMux`), mở
  `/debug/pprof/goroutine?debug=1` để xem các stack giống nhau được gộp kèm số lượng (tìm stack có
  hàng nghìn goroutine), `?debug=2` để xem từng goroutine kèm trạng thái chờ.
- Gửi `SIGQUIT` (`kill -QUIT <pid>`, hoặc Ctrl+\ trong terminal): runtime in stack mọi goroutine
  ra stderr rồi **thoát**. Chỉ dùng khi chấp nhận mất process.

Thử với hai goroutine khoá hai mutex ngược thứ tự trong một service vẫn đang chạy HTTP server (runtime
không báo deadlock vì còn goroutine sống, xem [module 1.3](#13-deadlock-livelock-starvation)).
`?debug=2` cho thấy (output thật, rút gọn):

```
goroutine 20 [sync.Mutex.Lock]:
...
main.transferAB()   main.go:12
goroutine 21 [sync.Mutex.Lock]:
...
main.transferBA()   main.go:13
```

Trạng thái trong ngoặc vuông (`sync.Mutex.Lock`, `chan receive`, `IO wait`, `select`) là thứ goroutine
đang chờ. Goroutine chờ từ một phút trở lên có thêm thời lượng, ví dụ `[chan receive, 12 minutes]`:
dấu hiệu rõ của kẹt hoặc rò rỉ.

#### Java

⚠️ Java **không có** race detector chuẩn tương đương `go test -race` trong JDK. Đây là câu bẫy: trả
lời "có, dùng jstack" là sai, vì thread dump chỉ chụp trạng thái tại một thời điểm, không phân tích
truy cập bộ nhớ. Thay vào đó, Java dựa vào bốn thứ:

*1. Stress test tự viết.* Kỹ thuật "cổng xuất phát" (*starting gate*, có trong ví dụ `TestHarness` của
*Java Concurrency in Practice*): mọi thread chờ ở một `CountDownLatch`, rồi thả cùng lúc để tối đa hoá
chồng lấn.

```java
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;

public class CounterStress {
    static int count = 0; // không đồng bộ: cố ý có data race

    public static void main(String[] args) throws InterruptedException {
        int threads = 8, perThread = 100_000;
        CountDownLatch startGate = new CountDownLatch(1);
        List<Thread> ts = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            Thread t = new Thread(() -> {
                try {
                    startGate.await(); // mọi thread chờ ở vạch xuất phát
                } catch (InterruptedException e) {
                    return;
                }
                for (int j = 0; j < perThread; j++) {
                    count++;
                }
            });
            t.start();
            ts.add(t);
        }
        startGate.countDown(); // thả tất cả cùng lúc
        for (Thread t : ts) {
            t.join();
        }
        System.out.println("expected=" + threads * perThread + " actual=" + count);
    }
}
```

`java CounterStress.java` ba lần trên máy thử (8 thread) in `actual=145174`, `119512`, `136043` thay
vì 800000; số mỗi lần mỗi khác. Stress test tự viết bắt được lỗi thô như thế này, nhưng không bắt
được lỗi reorder tinh vi chỉ hiện ra một lần trên một triệu, và không nói kết quả nào là "được phép".

*2. jcstress* (Java Concurrency Stress, dự án của OpenJDK). Đây là harness chạy một đoạn code trên
nhiều thread hàng triệu lần, trên nhiều object state mới, rồi **thống kê tần suất từng kết quả** và
đối chiếu với danh sách kết quả mà bạn khai báo là được phép. Các khái niệm:

- `@JCStressTest` đánh dấu test; `@State` là object dùng chung, được tạo mới cho mỗi lần thử.
- `@Actor`: mỗi method là một thread chạy đồng thời với các actor khác.
- `@Arbiter`: chạy **sau khi** mọi actor xong, dùng để đọc trạng thái cuối.
- Kết quả ghi vào object kiểu `I_Result`, `II_Result`, `III_Result`... (số chữ I là số giá trị int).
- `@Outcome(id = "...", expect = ...)` phân loại từng kết quả: `ACCEPTABLE`, `ACCEPTABLE_INTERESTING`
  (được phép nhưng đáng chú ý), `FORBIDDEN` (không được xảy ra; xảy ra là test fail).

Mẫu `API_02_Arbiters` trong thư mục samples (giữ nguyên code, thêm chú thích):

```java
@JCStressTest
@Outcome(id = "1", expect = ACCEPTABLE_INTERESTING, desc = "One update lost: atomicity failure.")
@Outcome(id = "2", expect = ACCEPTABLE,             desc = "Actors updated independently.")
@State
public class API_02_Arbiters {
    int v;

    @Actor
    public void actor1() { v++; }   // thread 1

    @Actor
    public void actor2() { v++; }   // thread 2, chạy đồng thời

    @Arbiter
    public void arbiter(I_Result r) { r.r1 = v; } // đọc kết quả cuối
}
```

Kết quả do tác giả ghi trong comment của file mẫu: kết quả `1` (mất một lần tăng) xuất hiện khoảng
6,37% số mẫu, kết quả `2` khoảng 93,63%. Mẫu `RaceCondition_01_RMW` cho thấy biến `volatile` vẫn mất
update khi đọc-sửa-ghi; bản bọc `synchronized` thì các kết quả xung đột được khai báo `FORBIDDEN` và
xuất hiện 0 lần. Cách chạy: tạo project bằng Maven archetype `jcstress-java-test-archetype`, rồi
`mvn clean verify` và `java -jar target/jcstress.jar` (thêm `-t <tên test>` để chạy một test,
`-m quick` để chạy nhanh trên CI). ⚠️ Test mang tính xác suất: README khuyên chạy lâu hơn để kết quả
tin cậy, và máy nhiều CPU nhanh thì thu được nhiều mẫu hơn. jcstress hợp để kiểm chứng một primitive
hay một class nhỏ (lazy init, double-checked locking, một cấu trúc lock-free), không phải để test cả
service.

*3. Code review và static analysis.* Ghi rõ lock nào bảo vệ field nào (annotation `@GuardedBy` của
JCIP, được checker `GuardedBy` của Error Prone kiểm tra lúc compile); SpotBugs có nhóm cảnh báo
multithreaded correctness (ví dụ field lúc thì truy cập trong `synchronized`, lúc thì không).

*4. Thread dump khi điều tra.* `jstack <pid>` hoặc `jcmd <pid> Thread.print` in stack và trạng thái
(`RUNNABLE`, `BLOCKED`, `WAITING`...) của mọi thread; có deadlock thì cuối dump có
`Found one Java-level deadlock:`. Chạy thử hai thread `synchronized` ngược thứ tự (JDK 26), output
thật, rút gọn địa chỉ:

```
Found one Java-level deadlock:
=============================
"transfer-ab":
  waiting to lock monitor 0x...d10 (object 0x...ce8, a java.lang.Object),
  which is held by "transfer-ba"
"transfer-ba":
  waiting to lock monitor 0x...870 (object 0x...cd8, a java.lang.Object),
  which is held by "transfer-ab"
```

Đặt tên thread (như `transfer-ab` ở trên, hoặc tên thread pool có nghĩa) để dump đọc được. Lấy vài dump
cách nhau vài giây: thread nào đứng yên ở cùng một stack qua nhiều dump là thread đang kẹt. Với virtual
thread, dump kiểu cũ không liệt kê chúng; dùng `jcmd <pid> Thread.dump_to_file -format=json <file>`
([module 2.6](#26-mô-hình-chạy-process-thread-event-loop-goroutine-virtual-thread)).

#### Database

Với backend PHP, phần lớn race nằm ở DB, nên công cụ điều tra quan trọng nhất nằm ở MySQL. Chi tiết
cách đọc từng công cụ đã có ở [module 1.3](#13-deadlock-livelock-starvation) và
[03 module 3.2](03-database-sql.md#32-lock-chuyên-sâu); ở đây là bản đồ "hỏi gì, xem ở đâu":

| Câu hỏi | Công cụ |
|---|---|
| Deadlock vừa rồi gồm những transaction nào, khoá gì? | `SHOW ENGINE INNODB STATUS\G`, mục `LATEST DETECTED DEADLOCK` (chỉ giữ cái **gần nhất**) |
| Muốn giữ **mọi** deadlock để phân tích sau | Bật `innodb_print_all_deadlocks` (mặc định tắt), deadlock được ghi vào error log |
| Lúc này ai đang giữ lock gì? | `performance_schema.data_locks` |
| Ai đang chờ ai? | `performance_schema.data_lock_waits` join với `data_locks`, hoặc gọn hơn `SELECT * FROM sys.innodb_lock_waits\G` |
| Transaction nào mở lâu, giữ lock mà không commit? | `information_schema.INNODB_TRX` (cột `trx_started`) |
| Tình trạng chờ lock có tăng dần theo thời gian? | Status `Innodb_row_lock_waits`, `Innodb_row_lock_time_avg`, `Innodb_row_lock_current_waits` (`SHOW GLOBAL STATUS LIKE 'Innodb_row_lock%'`) |

```sql
-- Ai đang chặn ai, kèm câu KILL gợi ý
SELECT waiting_pid, waiting_query, blocking_pid, blocking_query, sql_kill_blocking_connection
FROM sys.innodb_lock_waits\G

-- Transaction mở quá 30 giây
SELECT trx_id, trx_mysql_thread_id, trx_started, trx_query
FROM information_schema.INNODB_TRX
WHERE trx_started < NOW() - INTERVAL 30 SECOND;
```

Phía app, *log lock wait*: ghi lại mọi lỗi deadlock (mã 1213, SQLSTATE `40001`) và lock wait timeout
(mã 1205, sau `innodb_lock_wait_timeout` giây, mặc định 50) kèm route, user, câu SQL. Trong Laravel đó
là `QueryException`; đếm theo route cho thấy endpoint nào đang tranh chấp. Một đợt tăng đột biến của
hai lỗi này sau khi deploy thường là dấu hiệu code mới đổi thứ tự khoá hoặc kéo dài transaction.

#### Tái hiện race trong app web

Muốn sửa race thì trước hết phải tái hiện được, để sau khi sửa chứng minh được là hết. Hai cách bổ
sung cho nhau: bắn request song song (gần với thật, xác suất), và test tích hợp điều khiển thứ tự
(xác định, lặp lại được).

*Bắn request song song.* Kịch bản: endpoint áp coupon viết kiểu check-then-act
([module 1.4](#14-race-condition-trong-ứng-dụng-web)), mỗi user chỉ được dùng một lần.

```bash
# 20 request áp coupon cùng lúc, cùng một user (cùng token)
seq 20 | xargs -P 20 -I{} curl -s -X POST localhost:8000/api/coupons/apply \
  -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' -d 'code=SALE50'

# Kiểm tra bất biến ngay sau đó
mysql -e "SELECT user_id, coupon_id, COUNT(*) c FROM app.coupon_usages
          GROUP BY user_id, coupon_id HAVING c > 1;"
```

- `xargs -P 20` chạy tối đa 20 `curl` song song; `-I{}` chỉ để mỗi dòng của `seq` sinh một lệnh.
- `ab -n 20 -c 20 -p body.txt -T application/x-www-form-urlencoded <url>` (ApacheBench: `-n` tổng số
  request, `-c` số request đồng thời, `-p` file body cho POST) hoặc k6 cho tải lớn và kịch bản dài hơn.
- ⚠️ Bẫy lớn nhất khi thử trên máy dev: `php artisan serve` dùng web server có sẵn của PHP, mà theo
  manual PHP nó chạy **một process đơn luồng**, xử lý từng request một. 20 request bị xếp hàng, race
  không bao giờ hiện ra, và bạn kết luận sai là code an toàn. Cách chữa: chạy qua PHP-FPM thật (Sail,
  Docker, Nginx), hoặc bật nhiều worker cho server có sẵn (PHP 7.4+, không hỗ trợ Windows). Với
  Laravel, `artisan serve` chỉ tôn trọng biến này khi có `--no-reload` (ngoại lệ: chạy trong Sail):

  ```bash
  PHP_CLI_SERVER_WORKERS=8 php artisan serve --no-reload
  ```

- Cửa sổ race trên máy dev rất hẹp (DB local trả lời trong chưa tới một mili giây). Để tái hiện chắc
  chắn hơn, tạm chèn độ trễ giữa bước check và bước act, ví dụ `usleep(200_000);` (0,2 giây), chỉ trong
  lúc thử rồi xoá. Cách này không tạo ra bug mới, chỉ phóng to cửa sổ đã có sẵn.
- Đo bằng **bất biến ở DB** (câu `HAVING c > 1` ở trên), không bằng response: response có thể đều
  báo thành công hoặc đều báo lỗi mà dữ liệu vẫn sai.

*Test tích hợp điều khiển thứ tự.* Mở hai connection DB trong cùng một script và tự tay xen kẽ các
bước theo đúng thứ tự gây lỗi. Không cần may mắn, chạy lần nào cũng ra cùng kết quả:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `SELECT COUNT(*) ... WHERE user_id = 7 AND coupon_id = 1` | | 0: chưa dùng |
| 2 | | Cùng câu `SELECT` | 0: chưa dùng |
| 3 | `INSERT INTO coupon_usages (7, 1)` | | Thành công |
| 4 | | `INSERT INTO coupon_usages (7, 1)` | Không có unique: thành công, dùng hai lần. Có `UNIQUE(user_id, coupon_id)`: lỗi 1062, SQLSTATE `23000` |

```php
<?php
declare(strict_types=1);

// race_coupon.php: tái hiện xác định check-then-act bằng hai connection.
// Chạy: php race_coupon.php (cần MySQL local, database `race_demo` đã tạo sẵn).
// Code viết theo PDO chuẩn, chưa được chạy thử trong repo này.

function connect(): PDO
{
    return new PDO('mysql:host=127.0.0.1;dbname=race_demo', 'root', '', [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    ]);
}

function alreadyUsed(PDO $db, int $userId, int $couponId): bool
{
    $stmt = $db->prepare('SELECT COUNT(*) FROM coupon_usages WHERE user_id = ? AND coupon_id = ?');
    $stmt->execute([$userId, $couponId]);
    return (int) $stmt->fetchColumn() > 0;
}

function markUsed(PDO $db, int $userId, int $couponId): void
{
    $db->prepare('INSERT INTO coupon_usages (user_id, coupon_id) VALUES (?, ?)')
        ->execute([$userId, $couponId]);
}

function run(bool $withUnique): void
{
    $a = connect();
    $b = connect();
    $a->exec('DROP TABLE IF EXISTS coupon_usages');
    $a->exec('CREATE TABLE coupon_usages (user_id INT NOT NULL, coupon_id INT NOT NULL'
        . ($withUnique ? ', UNIQUE KEY uq_user_coupon (user_id, coupon_id)' : '') . ')');

    $usedA = alreadyUsed($a, 7, 1);   // bước 1
    $usedB = alreadyUsed($b, 7, 1);   // bước 2: B cũng thấy "chưa dùng"
    if ($usedA === false) {
        markUsed($a, 7, 1);           // bước 3
    }
    if ($usedB === false) {
        try {
            markUsed($b, 7, 1);       // bước 4
        } catch (PDOException $e) {
            // SQLSTATE 23000 = vi phạm ràng buộc; đây là chỗ đổi thành thông báo nghiệp vụ
            echo "B bị chặn: SQLSTATE {$e->getCode()}\n";
        }
    }
    $rows = (int) $a->query('SELECT COUNT(*) FROM coupon_usages')->fetchColumn();
    echo ($withUnique ? 'Có unique' : 'Không unique') . ": {$rows} lượt dùng\n";
}

run(false); // Không unique: 2 lượt dùng
run(true);  // B bị chặn: SQLSTATE 23000, rồi "Có unique: 1 lượt dùng"
```

Vì mỗi câu chạy ở autocommit và không câu nào chờ lock, một process PHP đơn luồng xen kẽ được hai
session mà không tự chặn mình. ⚠️ Nếu kịch bản cần session B **chờ** lock của A (ví dụ thử
`FOR UPDATE`), script đơn luồng sẽ treo ở bước B; khi đó dùng `FOR UPDATE NOWAIT` để B báo lỗi ngay
thay vì chờ, hoặc chạy hai process.

Đưa kịch bản này vào test của Laravel thì cần một connection thứ hai trong `config/database.php`, và
hai bẫy:

- ⚠️ Trait `RefreshDatabase` bọc mỗi test trong một transaction không commit. Connection thứ hai không
  thấy dữ liệu chưa commit đó, kịch bản sai từ gốc. Dùng `DatabaseMigrations` hoặc
  `DatabaseTruncation` cho các test này.
- ⚠️ Test chạy trên SQLite in-memory không tái hiện được hành vi lock và isolation của MySQL. Test
  concurrency phải chạy trên đúng loại DB của production.

#### Giới hạn của test

⚠️ Test pass không chứng minh là không có race. Số thứ tự xen kẽ tăng theo cấp số nhân với số thread
và số bước; test chỉ thử được một phần rất nhỏ. Race detector chỉ thấy code đã chạy và chỉ thấy bộ
nhớ trong một process. Stress test là xác suất. Test điều khiển thứ tự chỉ kiểm tra những thứ tự bạn
đã nghĩ ra.

Vì vậy tầng phòng thủ chính là **lập luận về bất biến**, và để DB giữ bất biến đó:

1. Viết bất biến ra thành câu: "tồn kho không âm", "mỗi user dùng mỗi coupon tối đa một lần", "tổng
   số dư các tài khoản không đổi sau chuyển tiền", "một đơn chỉ có một payment thành công".
2. Với mỗi bất biến, hỏi: hai request chạy xen kẽ ở **bất kỳ** điểm nào thì bất biến còn đúng không?
   Chỗ nào có đọc rồi ghi dựa trên cái vừa đọc là chỗ cần xem kỹ.
3. Đặt bất biến vào DB để DB từ chối trạng thái sai, dù code có race hay không:

   ```sql
   ALTER TABLE coupon_usages ADD UNIQUE KEY uq_user_coupon (user_id, coupon_id);
   ALTER TABLE products ADD CONSTRAINT chk_stock_non_negative CHECK (stock >= 0); -- MySQL 8.0.16+ mới thực thi CHECK
   ```

4. Biến bất biến thành **truy vấn giám sát** chạy định kỳ trên production (ví dụ câu `HAVING c > 1` ở
   trên, hoặc so tổng số dư theo ngày). Race sót qua test sẽ lộ ra ở đây trước khi khách hàng báo.

Với thiết kế phân tán phức tạp (nhiều service, nhiều bước), một số team dùng đặc tả hình thức như TLA+
để kiểm tra mọi thứ tự xen kẽ của *thiết kế* trước khi viết code; ở phỏng vấn backend, biết rằng có
cách này là đủ.

**Tóm tắt nhanh**
- Go `-race` báo data race kể cả khi lần chạy ra kết quả đúng, nhưng chỉ trong code **đã chạy**, chỉ
  trong một process; không thấy race condition ở DB. Chi phí khoảng 5–10 lần bộ nhớ, 2–20 lần thời gian.
- `testing/synctest` (GA ở Go 1.25): đồng hồ ảo trong bubble, timeout 5 giây test chạy tức thì,
  `Wait` chờ hệ thống lắng xuống, và fail khi còn goroutine kẹt. Mutex và I/O thật không "chặn bền".
- Java không có race detector chuẩn: stress test với starting gate, jcstress (thống kê kết quả theo
  `@Outcome`), `@GuardedBy` và static analysis; điều tra bằng `jstack`/`jcmd Thread.print`.
- MySQL: `LATEST DETECTED DEADLOCK` chỉ giữ cái gần nhất (bật `innodb_print_all_deadlocks`),
  `data_locks`/`sys.innodb_lock_waits` xem ai chặn ai, `INNODB_TRX` tìm transaction treo.
- Tái hiện race web: `xargs -P` + curl, đo bằng bất biến ở DB; `php artisan serve` mặc định một worker
  nên không tái hiện được; test tích hợp hai connection xen kẽ cho kết quả xác định.
- Test pass không chứng minh gì; viết bất biến, đặt constraint ở DB, giám sát bất biến trên production.

**Nguồn**: [Go: Data Race Detector](https://go.dev/doc/articles/race_detector) ·
[testing/synctest](https://pkg.go.dev/testing/synctest) ·
[Go blog: Testing concurrent code with testing/synctest](https://go.dev/blog/synctest) ·
[Go 1.25 release notes](https://go.dev/doc/go1.25) · [Go 1.26 release notes](https://go.dev/doc/go1.26) ·
[Go 1.27 release notes](https://go.dev/doc/go1.27) ·
[jcstress: README và samples](https://github.com/openjdk/jcstress) ·
[PHP: Built-in web server](https://www.php.net/manual/en/features.commandline.webserver.php) ·
[Laravel ServeCommand (13.x)](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Console/ServeCommand.php)
