# 06. Java, JVM và Spring

> [← Mục lục](README.md) · Phạm vi: ngôn ngữ Java tới Java 21, Collections bên trong, JVM (memory, GC, chẩn đoán, container), concurrency Java, Spring/Spring Boot và JPA/Hibernate.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

Concurrency tổng quát (race condition, deadlock, lock DB) nằm ở [13-concurrency.md](13-concurrency.md).
File này tập trung vào công cụ riêng của Java.

## Bản đồ nhanh

**Ngôn ngữ**
- [ ] Primitive và wrapper, autoboxing, ⚠️ `Integer` cache và `==`, NPE khi unboxing
- [ ] `String` immutable, string pool, `StringBuilder`
- [ ] ⚠️ Hợp đồng `equals`/`hashCode`, key mutable trong `HashMap`
- [ ] Java luôn pass-by-value
- [ ] `final`, `static`, access modifier; 🟡 inner class giữ reference tới outer
- [ ] Interface (default/static/private method) vs abstract class
- [ ] 🟡 Generics, type erasure, wildcard, PECS
- [ ] Checked vs unchecked exception, try-with-resources, suppressed exception
- [ ] Lambda, Stream, `Optional` và cạm bẫy
- [ ] 🟡 `record`, `sealed`, pattern matching (`instanceof`, `switch`)
- [ ] 🔴 Virtual threads (Java 21), pinning

**Collections**
- [ ] `ArrayList` vs `LinkedList`
- [ ] 🟡 `HashMap` bên trong: bucket, hash spreading, treeify, resize, load factor
- [ ] `LinkedHashMap` làm LRU, `TreeMap`, `HashSet`
- [ ] 🟡 `ConcurrentHashMap` (Java 8+)
- [ ] ⚠️ `ConcurrentModificationException`, fail-fast iterator
- [ ] Immutable/unmodifiable collection, ⚠️ `Arrays.asList`

**JVM**
- [ ] Vùng nhớ: heap (young/old), stack, metaspace, off-heap
- [ ] GC: generational, stop-the-world; 🟡 G1, ZGC; Parallel, Serial
- [ ] 🟡 GC tuning cơ bản, GC log
- [ ] 🟡 Class loading, parent delegation
- [ ] 🟡 JIT: interpreter, C1, C2, tiered, warm-up
- [ ] 🟡 Heap dump, thread dump, `jcmd`, JFR
- [ ] ⚠️ Các loại `OutOfMemoryError`
- [ ] 🔴 JVM trong container: nhận memory limit, `MaxRAMPercentage`, OOMKilled

**Concurrency**
- [ ] 🟡 JMM, happens-before
- [ ] `synchronized`, `volatile`, `Atomic*`, `LongAdder`
- [ ] 🟡 `ReentrantLock`, `ReadWriteLock`, `CountDownLatch`, `Semaphore`
- [ ] `ExecutorService`, ⚠️ `Executors.newFixedThreadPool` và queue không giới hạn
- [ ] `CompletableFuture`, ⚠️ common pool
- [ ] ⚠️ `ThreadLocal` leak với thread pool

**Spring**
- [ ] IoC/DI, `ApplicationContext`, bean
- [ ] 🟡 Bean lifecycle, `BeanPostProcessor`; scope; ⚠️ prototype trong singleton
- [ ] Constructor injection, `@Qualifier`, `@Primary`, circular dependency
- [ ] 🟡 AOP, JDK proxy vs CGLIB, ⚠️ self-invocation
- [ ] `@Transactional`: propagation, ⚠️ rollback rules, `readOnly`, ⚠️ `UnexpectedRollbackException`
- [ ] Spring Boot auto-configuration, `@Conditional*`
- [ ] Profiles, externalized config
- [ ] 🟡 Spring MVC vs WebFlux
- [ ] JPA/Hibernate: persistence context, entity state, dirty checking, flush
- [ ] ⚠️ Lazy/eager mặc định, N+1, `LazyInitializationException`, open-in-view
- [ ] 🟡 Optimistic locking `@Version`, pessimistic lock
- [ ] Actuator, testing slice (`@WebMvcTest`, `@DataJpaTest`) — chỉ cần biết tên

## Chi tiết

### Ngôn ngữ

- [ ] Primitive và wrapper
  - 8 primitive: `byte short int long float double char boolean`. Wrapper là object, có thể `null`.
  - ⚠️ `Integer a = 127, b = 127; a == b` là `true`; với `128` là `false`. `Integer.valueOf` cache
    -128..127 (giới hạn trên chỉnh được bằng JVM flag). `Long`, `Short`, `Byte` cũng cache -128..127.
    Luôn so wrapper bằng `equals`.
  - ⚠️ Auto-unboxing `null` → `NullPointerException`: `int x = map.get("k");` khi key không có.
  - Tiền: `BigDecimal` (tạo từ `String`, không từ `double`), so sánh bằng `compareTo` vì
    `equals` so cả scale (`2.0` khác `2.00`).

- [ ] `String`
  - Immutable: an toàn chia sẻ giữa thread, cache được `hashCode`, dùng làm key an toàn.
  - Literal nằm trong string pool (trong heap từ Java 7). `new String("a")` tạo object mới.
    `intern()` đưa vào pool.
  - Nối chuỗi trong vòng lặp: dùng `StringBuilder` (không synchronized) thay `StringBuffer`.
  - Java 9+: compact strings (Latin-1 lưu 1 byte/ký tự).

- [ ] ⚠️ `equals`/`hashCode`
  - Hợp đồng: `a.equals(b)` thì `a.hashCode() == b.hashCode()`. Ngược lại không bắt buộc.
  - Override `equals` mà không override `hashCode`: hai object "bằng nhau" rơi vào bucket khác,
    `HashSet` chứa trùng, `map.get` trả `null`.
  - Sửa field tham gia `hashCode` sau khi đã làm key: object "biến mất" trong `HashMap`
    (nằm ở bucket cũ). Key nên immutable (`String`, `record`).

- [ ] Pass-by-value
  - Luôn truyền bản sao giá trị. Với object, giá trị là **reference**: sửa field thì bên ngoài thấy,
    gán `param = new X()` thì không.

- [ ] `final`, `static`, nested class
  - `final` biến: không gán lại (object bên trong vẫn sửa được). `final` method: không override.
    `final` class: không kế thừa (`String`).
  - Lambda chỉ bắt biến local "effectively final".
  - 🟡 Inner class (non-static) giữ reference ngầm tới outer instance → leak khi sống lâu hơn outer.
    Mặc định dùng `static` nested class.
  - 🔴 Field `final` có đảm bảo JMM: đọc thấy giá trị đã khởi tạo sau khi constructor xong (nếu
    `this` không bị lộ ra trong constructor).

- [ ] Interface vs abstract class
  - Interface: default method, static method (8), private method (9); không có state instance.
  - Abstract class: có field, constructor; chỉ `extends` một class.
  - Default method giúp tiến hoá API không phá implementation cũ. ⚠️ Hai interface cùng default
    method → class phải override.

- [ ] 🟡 Generics
  - Type erasure: thông tin kiểu bị xoá khi compile (`List<String>` và `List<Integer>` cùng là `List`
    lúc runtime). Hệ quả: không `new T()`, không `instanceof List<String>`, không overload chỉ khác
    type parameter, không mảng generic.
  - Wildcard: `? extends T` (đọc ra T, không ghi vào), `? super T` (ghi T vào, đọc ra `Object`).
    PECS: **P**roducer **E**xtends, **C**onsumer **S**uper. Ví dụ `Collections.copy(List<? super T> dest, List<? extends T> src)`.
  - Raw type (`List`) tắt kiểm tra kiểu, dễ `ClassCastException` lúc runtime.

- [ ] Exception
  ```text
  Throwable
  ├── Error (OutOfMemoryError, StackOverflowError) — không nên bắt
  └── Exception — checked (IOException, SQLException)
      └── RuntimeException — unchecked (NPE, IllegalArgumentException, IllegalStateException)
  ```
  - Checked: bắt buộc `catch` hoặc `throws`. Tranh luận: an toàn nhưng làm API dài dòng, không hợp
    với lambda; framework hiện đại (Spring) thường bọc thành unchecked.
  - try-with-resources: tự `close()` mọi `AutoCloseable` theo thứ tự ngược. Exception khi `close`
    thành suppressed exception (`getSuppressed()`), không đè exception chính.
  - ⚠️ `return` trong `finally` nuốt exception. ⚠️ `catch (Exception e) {}` nuốt lỗi.

- [ ] Lambda, Stream, Optional
  - Stream lười: chỉ chạy khi có terminal operation; dùng một lần.
  - ⚠️ Side effect trong `map`/`filter`; sửa collection nguồn trong stream.
  - ⚠️ `parallelStream()` dùng chung `ForkJoinPool.commonPool()`; làm I/O blocking trong đó thì
    chặn mọi parallel stream khác trong JVM. Chỉ dùng cho CPU-bound, dữ liệu lớn, đã đo.
  - ⚠️ `Collectors.toMap` ném `IllegalStateException` khi key trùng (truyền merge function) và NPE khi
    value `null`.
  - `Stream.toList()` (16) trả list **unmodifiable**; `collect(Collectors.toList())` không đảm bảo.
  - `Optional`: dùng làm **kiểu trả về**. ⚠️ Không dùng cho field, tham số, collection.
    ⚠️ `get()` không kiểm tra. ⚠️ `orElse(expensive())` luôn gọi `expensive()`; dùng `orElseGet`.

- [ ] 🟡 Tính năng mới
  | Bản | Tính năng |
  |---|---|
  | 8 | lambda, Stream, `Optional`, default method, `java.time` |
  | 10 | `var` cho biến local |
  | 14 | switch expression |
  | 15 | text block |
  | 16 | `record`, pattern matching cho `instanceof` |
  | 17 (LTS) | `sealed` class/interface |
  | 21 (LTS) | virtual threads, pattern matching cho `switch`, record pattern, sequenced collections |
  - `record`: class dữ liệu immutable (final, field final), tự sinh constructor, accessor, `equals`,
    `hashCode`, `toString`. Hợp làm DTO, value object, key map. ⚠️ Field là mảng/list thì vẫn sửa được bên trong.
  - `sealed` + `record` + `switch` pattern: compiler kiểm tra đủ mọi trường hợp (exhaustive), giống
    sum type.

- [ ] 🔴 Virtual threads (Java 21)
  - Thread nhẹ do JVM lập lịch trên một số ít carrier thread (platform thread). Khi block I/O, virtual
    thread được unmount, carrier làm việc khác.
  - Hợp với workload **I/O-bound**, code blocking kiểu truyền thống; không làm code CPU-bound nhanh hơn.
  - ⚠️ Pinning: block trong `synchronized` (Java 21) hoặc native call giữ luôn carrier. JDK 24 đã bỏ
    pinning với `synchronized` (kiểm tra lại theo phiên bản). Với 21: dùng `ReentrantLock` ở đoạn có I/O.
  - ⚠️ Không pool virtual thread; tạo mới mỗi task. Giới hạn truy cập tài nguyên (DB) bằng `Semaphore`
    hoặc pool connection, vì hàng chục nghìn virtual thread sẽ dồn vào DB.
  - ⚠️ `ThreadLocal` nặng × triệu thread = tốn RAM.
  - Spring Boot 3.2+: `spring.threads.virtual.enabled=true`.

### Collections

- [ ] `ArrayList` vs `LinkedList`
  | Thao tác | `ArrayList` | `LinkedList` |
  |---|---|---|
  | `get(i)` | O(1) | O(n) |
  | Thêm cuối | O(1) amortized | O(1) |
  | Thêm/xoá giữa | O(n) dịch mảng | O(n) tìm vị trí + O(1) nối |
  | Bộ nhớ | Mảng liên tục | Mỗi node thêm 2 con trỏ |
  - Thực tế gần như luôn chọn `ArrayList`: cache locality, ít object. Cần queue/deque thì `ArrayDeque`.
  - `ArrayList` tăng khoảng 1.5 lần khi đầy; biết trước kích thước thì truyền capacity.

- [ ] 🟡 `HashMap` bên trong (Java 8+)
  - Mảng bucket kích thước luỹ thừa của 2; index = `(n - 1) & hash`, với `hash = h ^ (h >>> 16)` để
    trộn bit cao xuống (vì chỉ bit thấp được dùng làm index).
  - Collision: bucket là linked list; khi một bucket có từ 8 phần tử **và** bảng đã đủ 64 bucket thì
    chuyển thành cây đỏ-đen (O(log n)); dưới 6 thì về lại list. Bảng nhỏ hơn 64 thì resize thay vì treeify.
  - Capacity mặc định 16, load factor 0.75: vượt `capacity × 0.75` phần tử thì resize gấp đôi, mỗi
    phần tử ở lại vị trí cũ hoặc dịch thêm `oldCap` (dựa trên một bit).
  - Cho phép một key `null`. Không thread-safe: ghi đồng thời mất dữ liệu (Java 7 còn có thể tạo
    vòng lặp vô hạn khi resize).
  - ⚠️ `hashCode` tệ (trả hằng số) → mọi thứ vào một bucket, hiệu năng sập.

- [ ] `LinkedHashMap`, `TreeMap`, `HashSet`
  - `LinkedHashMap` giữ thứ tự chèn, hoặc thứ tự truy cập (`accessOrder = true`). LRU:
    ```java
    class Lru<K, V> extends LinkedHashMap<K, V> {
        private final int max;
        Lru(int max) { super(16, 0.75f, true); this.max = max; }
        @Override protected boolean removeEldestEntry(Map.Entry<K, V> e) { return size() > max; }
    }
    ```
    (không thread-safe; production dùng Caffeine.)
  - `TreeMap`: cây đỏ-đen, key có thứ tự, O(log n), `floorKey`, `ceilingKey`, `subMap`.
  - `HashSet` dùng `HashMap` bên dưới (value là object giả).

- [ ] 🟡 `ConcurrentHashMap`
  - Java 8+: CAS khi bucket rỗng, `synchronized` trên node đầu bucket khi có collision; đọc không lock.
  - Không cho key/value `null` (không phân biệt được "không có" và "giá trị null" khi đồng thời).
  - `computeIfAbsent`, `merge` là atomic. ⚠️ Không làm việc lâu hoặc sửa chính map trong hàm truyền vào.
  - ⚠️ `if (!map.containsKey(k)) map.put(k, v)` vẫn race; dùng `putIfAbsent`/`computeIfAbsent`.
  - `Collections.synchronizedMap`: một lock cho cả map, duyệt vẫn phải tự `synchronized`.

- [ ] ⚠️ `ConcurrentModificationException`
  - Iterator fail-fast kiểm tra `modCount`; sửa collection khi đang duyệt (kể cả **một thread**) là ném.
  - Sửa: `iterator.remove()`, `removeIf`, duyệt bản sao, `CopyOnWriteArrayList` (đọc nhiều ghi ít).

- [ ] Immutable collection
  - `List.of`, `Set.of`, `Map.of` (9+): immutable thật, ⚠️ không cho `null`, `Set.of` trùng phần tử ném lỗi.
  - `Collections.unmodifiableList(x)`: chỉ là **view**, `x` đổi thì view đổi theo. `List.copyOf` để chụp.
  - ⚠️ `Arrays.asList`: kích thước cố định (`add` ném `UnsupportedOperationException`), ghi xuyên vào mảng gốc.

### JVM

- [ ] Vùng nhớ
  ```text
  Heap (chung mọi thread): Young [Eden | S0 | S1]  +  Old
  Metaspace (native, Java 8+): metadata class
  Mỗi thread: stack (frame, biến local, reference) + PC
  Khác: code cache (JIT), direct buffer (NIO), thread stack, GC data
  ```
  - Object sống ở heap; primitive local và reference nằm trên stack.
  - ⚠️ Tổng RAM process > `-Xmx`: còn metaspace, stack × số thread, direct buffer, code cache.

- [ ] GC
  - Giả thuyết thế hệ: đa số object chết trẻ → dọn young thường xuyên (rẻ), object sống lâu promote lên old.
  - Stop-the-world: dừng thread ứng dụng. Mục tiêu các GC hiện đại là giảm pause.
  | GC | Đặc điểm | Hợp với |
  |---|---|---|
  | Serial | Một thread | Heap nhỏ, container 1 CPU |
  | Parallel | Nhiều thread, tối ưu throughput | Batch, không quan tâm pause |
  | G1 (mặc định từ Java 9) | Chia heap thành region, ưu tiên dọn region nhiều rác, mục tiêu pause (`MaxGCPauseMillis`) | Mặc định cho service |
  | ZGC | Gần như concurrent hoàn toàn, pause rất ngắn, heap lớn; có chế độ generational (21+) | Latency nhạy, heap lớn |
  | Shenandoah | Concurrent compaction, pause ngắn | Tương tự ZGC |

- [ ] 🟡 GC tuning cơ bản
  - Bước đầu: đặt `-Xms` = `-Xmx` (tránh resize heap), chọn collector, bật GC log `-Xlog:gc*`.
  - Đo: tần suất và độ dài pause, allocation rate, old gen sau Full GC có tăng dần không (leak).
  - ⚠️ Tuning flag trước khi giảm allocation là làm ngược. Profiling allocation (JFR, async-profiler) trước.

- [ ] 🟡 Class loading
  - Loader: bootstrap (lớp lõi) → platform (9+, trước là extension) → application (classpath).
  - Parent delegation: hỏi cha trước; tránh class lõi bị giả mạo.
  - Pha: loading → linking (verify, prepare, resolve) → initialization (chạy `static` block, lười,
    lần dùng đầu tiên).
  - ⚠️ Leak classloader trong app server/hot reload: thread hoặc `ThreadLocal` giữ class của app cũ → Metaspace OOM.

- [ ] 🟡 JIT
  - Bytecode chạy bằng interpreter, method nóng được C1 (nhanh, tối ưu ít) rồi C2 (tối ưu mạnh:
    inlining, escape analysis) compile. Tiered compilation mặc định.
  - Warm-up: vài phút đầu chậm hơn. Ảnh hưởng tới benchmark (dùng JMH) và autoscaling.
  - Deoptimization khi giả định sai. Lựa chọn khác: GraalVM native image (khởi động nhanh, đổi lại
    build lâu, hạn chế reflection).

- [ ] 🟡 Chẩn đoán
  - Thread dump: `jstack <pid>` hoặc `jcmd <pid> Thread.print`. Tìm deadlock (JVM tự báo), thread
    `BLOCKED`, pool bị kẹt chờ I/O. Lấy 3 lần cách nhau vài giây để thấy thread nào đứng yên.
  - Heap dump: `jcmd <pid> GC.heap_dump file.hprof`, `jmap -dump`; tự động với
    `-XX:+HeapDumpOnOutOfMemoryError`. Phân tích bằng Eclipse MAT (dominator tree, retained size).
    ⚠️ Heap dump dừng JVM và chứa dữ liệu nhạy cảm.
  - JFR (Java Flight Recorder): overhead thấp, dùng được production. async-profiler cho CPU/allocation.

- [ ] ⚠️ Các loại `OutOfMemoryError`
  | Thông báo | Nguyên nhân thường gặp |
  |---|---|
  | `Java heap space` | Leak (cache không giới hạn, collection static), nạp dữ liệu quá lớn, heap nhỏ |
  | `GC overhead limit exceeded` | GC chạy gần hết thời gian mà thu hồi rất ít; gần hết heap |
  | `Metaspace` | Sinh class động quá nhiều, leak classloader |
  | `unable to create native thread` | Quá nhiều thread, giới hạn OS/container (`ulimit`, pid limit) |
  | `Direct buffer memory` | NIO/Netty dùng off-heap vượt `MaxDirectMemorySize` |
  | `Requested array size exceeds VM limit` | Tạo mảng quá lớn |

- [ ] 🔴 JVM trong container
  - JDK 10+ (và backport 8u191) nhận cgroup limit (`UseContainerSupport` mặc định bật).
  - Mặc định heap tối đa = 25% RAM container (`MaxRAMPercentage`). Container 2 GB chỉ dùng ~512 MB heap.
    Thường đặt `-XX:MaxRAMPercentage` 50–75 tuỳ lượng non-heap.
  - ⚠️ Heap + non-heap vượt limit → kernel **OOMKilled** (exit 137), không có `OutOfMemoryError`,
    không có heap dump. Phân biệt hai loại khi điều tra.
  - CPU limit ảnh hưởng số GC thread, kích thước common pool. Xem [19-devops-cloud.md](19-devops-cloud.md).

### Concurrency

- [ ] 🟡 JMM và happens-before
  - Không có happens-before thì thread khác có thể **không thấy** ghi, hoặc thấy theo thứ tự khác
    (compiler/CPU reorder).
  - Quan hệ chính: thứ tự trong một thread; unlock monitor → lock sau đó cùng monitor; ghi `volatile`
    → đọc sau đó cùng biến; `Thread.start()` → code trong thread; code trong thread → `join()` trả về.
  - ⚠️ Double-checked locking singleton cần field `volatile`, nếu không thread khác thấy object chưa
    khởi tạo xong. Cách đơn giản hơn: holder class hoặc `enum`.

- [ ] `synchronized`, `volatile`, atomic
  - `synchronized`: loại trừ lẫn nhau + visibility; reentrant; lock trên object (`this`, class).
  - `volatile`: visibility + chống reorder, ⚠️ **không** atomic: `count++` trên `volatile` vẫn race.
    Hợp cho cờ `running`.
  - `AtomicInteger`, `AtomicReference`: CAS, lock-free. Tranh chấp cao: `LongAdder` (chia counter).

- [ ] 🟡 Lock và công cụ đồng bộ
  - `ReentrantLock`: `tryLock(timeout)`, fair, `lockInterruptibly`, nhiều `Condition`. ⚠️ Phải `unlock()`
    trong `finally`.
  - `ReadWriteLock`, `StampedLock` (optimistic read).
  - `CountDownLatch` (chờ N việc xong, dùng một lần), `CyclicBarrier`, `Semaphore` (giới hạn N truy cập).

- [ ] `ExecutorService`
  - `Runnable` (không trả kết quả) vs `Callable` (trả kết quả, ném được checked exception); `submit()`
    trả `Future` (`get()` block). Không tự `new Thread()` cho từng task trong service.
  - `ThreadPoolExecutor(core, max, keepAlive, queue, threadFactory, rejectionHandler)`.
    Thread vượt `core` chỉ tạo khi **queue đầy**.
  - ⚠️ `Executors.newFixedThreadPool` dùng `LinkedBlockingQueue` không giới hạn → task dồn tới OOM.
    `newCachedThreadPool` tạo thread không giới hạn. Production: tự tạo với queue có giới hạn và
    rejection policy (`CallerRunsPolicy` tạo backpressure).
  - Đặt tên thread (dễ đọc thread dump). `shutdown()` + `awaitTermination()` khi tắt.
  - ⚠️ Exception trong `submit()` bị giữ trong `Future`; không gọi `get()` thì lỗi im lặng.

- [ ] `CompletableFuture`
  - `supplyAsync`, `thenApply` (map), `thenCompose` (flatMap), `thenCombine`, `allOf`/`anyOf`,
    `exceptionally`/`handle`, `orTimeout` (9+).
  - ⚠️ Không truyền executor thì chạy trên common pool; I/O blocking ở đó làm đói cả JVM.
  - ⚠️ `allOf` không huỷ các future còn lại khi một cái lỗi.

- [ ] ⚠️ `ThreadLocal` với thread pool
  - Thread trong pool sống mãi, `ThreadLocal` không `remove()` thì giá trị **sang request sau**:
    lộ user/tenant của request trước, và giữ object không được GC.
  - Luôn `try { set } finally { remove(); }`. Spring `RequestContextHolder`, MDC logging, security
    context đều dùng `ThreadLocal`; ⚠️ mất khi chuyển sang thread khác (`@Async`, `CompletableFuture`).
  - Scoped values là hướng thay thế cho virtual thread (preview ở 21, kiểm tra lại trạng thái theo phiên bản).

### Spring

- [ ] IoC/DI
  - Container (`ApplicationContext`) tạo và nối bean; code không tự `new` dependency.
  - Khai báo: `@Component`/`@Service`/`@Repository`/`@Controller` + component scan, hoặc `@Bean`
    trong `@Configuration`.
  - `@Repository` còn dịch exception của persistence sang `DataAccessException`.

- [ ] 🟡 Bean lifecycle và scope
  ```text
  khởi tạo (constructor) → inject dependency → *Aware callback
  → BeanPostProcessor.before → @PostConstruct / afterPropertiesSet / init-method
  → BeanPostProcessor.after (proxy AOP được tạo ở đây) → dùng → @PreDestroy khi context đóng
  ```
  - Scope: `singleton` (mặc định, một instance mỗi context), `prototype` (mới mỗi lần lấy, Spring
    không gọi destroy), `request`, `session`, `application`, `websocket`.
  - ⚠️ Singleton dùng chung mọi thread → không giữ state mutable của request trong field.
  - ⚠️ Inject prototype vào singleton: chỉ inject **một lần**. Dùng `ObjectProvider<T>`, `@Lookup`,
    hoặc scoped proxy.

- [ ] Constructor injection
  - Ưu: field `final`, dependency bắt buộc rõ ràng, test không cần container, lộ class có quá nhiều
    dependency (dấu hiệu vi phạm SRP).
  - Field injection (`@Autowired` trên field): khó test, che dependency.
  - Nhiều bean cùng kiểu: `@Qualifier`, `@Primary`, inject `List<T>` để lấy tất cả (Strategy).
  - ⚠️ Circular dependency: Spring Boot 2.6+ mặc định từ chối. Sửa thiết kế, không bật lại cho qua.

- [ ] 🟡 AOP và proxy
  - `@Transactional`, `@Cacheable`, `@Async`, `@Retryable` hoạt động nhờ **proxy** bọc bean.
  - JDK dynamic proxy (theo interface) hoặc CGLIB (sinh class con). Spring Boot mặc định dùng CGLIB.
  - ⚠️ Self-invocation: `this.methodB()` trong cùng bean **không qua proxy** → `@Transactional`/
    `@Async`/`@Cacheable` trên `methodB` không có tác dụng. Sửa: tách sang bean khác (sạch nhất),
    inject chính mình, hoặc `TransactionTemplate`.
  - ⚠️ CGLIB không proxy được method `final`/`private`; chỉ chắc chắn hoạt động với method public
    gọi từ bên ngoài bean.

- [ ] `@Transactional`
  | Propagation | Hành vi |
  |---|---|
  | `REQUIRED` (mặc định) | Dùng transaction hiện có, chưa có thì tạo |
  | `REQUIRES_NEW` | Tạm dừng transaction hiện có, mở transaction mới (connection mới) |
  | `NESTED` | Savepoint trong transaction hiện có |
  | `SUPPORTS` / `NOT_SUPPORTED` / `MANDATORY` / `NEVER` | Có thì dùng / luôn chạy ngoài / bắt buộc có / bắt buộc không |
  - ⚠️ Rollback mặc định chỉ với `RuntimeException` và `Error`. Checked exception → **commit**.
    Dùng `rollbackFor = Exception.class` nếu muốn.
  - ⚠️ `UnexpectedRollbackException`: method trong (REQUIRED) ném exception, đánh dấu transaction
    rollback-only; method ngoài bắt exception rồi tiếp tục → lúc commit Spring ném lỗi này.
  - ⚠️ `REQUIRES_NEW` giữ hai connection cùng lúc; tải cao dễ cạn pool (deadlock ở mức pool).
  - `readOnly = true`: gợi ý; Hibernate bỏ dirty checking/flush, driver có thể tối ưu, dùng để route
    sang replica với routing datasource. Không phải cơ chế bảo mật.
  - `isolation`, `timeout`. ⚠️ Gọi HTTP ngoài trong transaction giữ connection và lock lâu.
  - `@TransactionalEventListener(phase = AFTER_COMMIT)` tương đương `afterCommit` của Laravel.

- [ ] Spring Boot auto-configuration
  - `@SpringBootApplication` = `@Configuration` + `@EnableAutoConfiguration` + `@ComponentScan`.
  - Auto-config là các class `@Configuration` có điều kiện (`@ConditionalOnClass`,
    `@ConditionalOnMissingBean`, `@ConditionalOnProperty`), được liệt kê trong file `AutoConfiguration.imports`
    (Boot 2.7+/3). Có JDBC driver + `spring-boot-starter-jdbc` → tự tạo `DataSource`.
  - Bạn định nghĩa bean cùng kiểu → auto-config lùi lại (`OnMissingBean`).
  - Debug: chạy với `--debug` xem condition evaluation report; Actuator `/actuator/conditions`.

- [ ] Profiles và config
  - `application-{profile}.yml`, `spring.profiles.active`, `@Profile("prod")`.
  - Thứ tự ưu tiên: tham số dòng lệnh, biến môi trường đè lên file config (dùng biến môi trường cho
    secret trong container). `@ConfigurationProperties` gom config có kiểu, validate được.

- [ ] 🟡 Spring MVC vs WebFlux
  | | MVC | WebFlux |
  |---|---|---|
  | Mô hình | Servlet, thread-per-request, blocking | Event loop (Netty), non-blocking, Reactor `Mono`/`Flux` |
  | Hợp với | Đa số service, JDBC/JPA | Nhiều kết nối đồng thời chờ I/O, streaming |
  | Điều kiện | | Toàn chuỗi phải non-blocking (R2DBC, WebClient) |
  - ⚠️ Gọi code blocking (JDBC) trên event loop làm sập throughput.
  - Virtual thread + MVC giải quyết phần lớn bài toán "nhiều request chờ I/O" với code blocking quen thuộc.

- [ ] JPA/Hibernate: persistence context
  - Persistence context (gắn với `EntityManager`, thường theo transaction) = first-level cache +
    identity map: cùng id trong một context trả về cùng object.
  - Trạng thái entity: transient (mới `new`), managed, detached (context đóng), removed.
  - Dirty checking: lúc flush, Hibernate so entity managed với snapshot và tự sinh `UPDATE`. Không cần
    gọi `save()` cho entity managed.
  - Flush xảy ra khi commit, trước query có thể bị ảnh hưởng (`FlushMode.AUTO`), hoặc gọi tay.
  - ⚠️ Load hàng chục nghìn entity trong một context: RAM tăng và flush chậm (snapshot từng entity).
    Batch: `flush()` + `clear()` định kỳ, hoặc dùng JDBC/projection.
  - ⚠️ ID generation `IDENTITY` làm Hibernate không batch insert được.
  - Spring Data `save()`: entity mới → `persist`, có id → `merge` (có thể SELECT trước).

- [ ] ⚠️ Lazy/eager và N+1
  - Mặc định: `@OneToMany`, `@ManyToMany` là LAZY; ⚠️ `@ManyToOne`, `@OneToOne` là **EAGER**.
    Nên đặt tất cả LAZY rồi fetch có chủ đích.
  - N+1: load list rồi truy cập quan hệ lazy từng phần tử. Sửa: `JOIN FETCH`, `@EntityGraph`,
    batch fetching (`@BatchSize`, `hibernate.default_batch_fetch_size`), DTO projection.
  - ⚠️ `JOIN FETCH` collection + phân trang → Hibernate cảnh báo và phân trang **trong RAM**.
    Fetch hai collection kiểu `List` cùng lúc → `MultipleBagFetchException`.
  - `LazyInitializationException`: truy cập quan hệ lazy khi context đã đóng (ngoài transaction,
    trong view, khi serialize JSON).
  - ⚠️ `spring.jpa.open-in-view` mặc định bật (Boot có cảnh báo): giữ context tới hết request, che lỗi
    lazy nhưng giữ connection lâu và N+1 xảy ra ngầm ở tầng view/serializer. Nhiều đội tắt nó.
  - ⚠️ Serialize entity trực tiếp ra JSON: vòng lặp quan hệ, lazy load ngoài ý muốn. Trả DTO.
  - ⚠️ `equals`/`hashCode` của entity dựa trên id tự sinh: đổi sau khi persist. Tránh Lombok `@Data` trên entity.

- [ ] 🟡 Locking
  - Optimistic: field `@Version`; `UPDATE ... WHERE id = ? AND version = ?`; không khớp →
    `OptimisticLockException` (Spring bọc thành `ObjectOptimisticLockingFailureException`). Retry
    hoặc báo người dùng.
  - Pessimistic: `@Lock(LockModeType.PESSIMISTIC_WRITE)` → `SELECT ... FOR UPDATE`.
  - Chi tiết chọn loại nào: [03-database-sql.md](03-database-sql.md).

### Đối chiếu với ngôn ngữ khác

| Khía cạnh | Java/Spring | PHP/Laravel | Go |
|---|---|---|---|
| So sánh bằng | `==` so reference, `equals` so nội dung | `===` chặt, `==` lỏng | `==` so giá trị (struct so từng field), không override được |
| Collection | `HashMap` không giữ thứ tự | array giữ thứ tự chèn | `map` không giữ thứ tự, ngẫu nhiên có chủ đích |
| Generics | Type erasure | Không có (PHPStan generics qua docblock) | Có từ 1.18, không erasure kiểu Java |
| DI | Spring IoC, proxy AOP | Service container, reflection | Constructor tay, không container |
| Transaction | `@Transactional` qua proxy | `DB::transaction(closure)` | `tx, _ := db.BeginTx(...)` tường minh |
| ORM | Data Mapper + Unit of Work (Hibernate) | Active Record (Eloquent) | Ít ORM, thường SQL tường minh |
| Concurrency | Thread, pool, virtual thread | Process FPM, queue worker | Goroutine, channel |
| Thread-local state | `ThreadLocal`, rủi ro leak với pool | Không cần (share-nothing) | Không có, truyền `context.Context` |

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| `@Transactional` không rollback | "Chắc cấu hình sai." | Kiểm tra ba nguyên nhân: self-invocation (không qua proxy), exception là checked, exception bị bắt và nuốt; nói cách xác minh (log transaction của Spring, debug proxy class). |
| HashMap hoạt động thế nào? | "Dùng hash để tìm nhanh O(1)." | Bucket luỹ thừa 2, trộn bit, treeify có điều kiện 64 bucket, resize gấp đôi, không thread-safe; hậu quả thực tế của `hashCode` tệ và key mutable. |
| Service bị OOM trên Kubernetes | "Tăng `-Xmx`." | Phân biệt `OutOfMemoryError` (có heap dump) và OOMKilled (exit 137, vượt limit container do non-heap); tính heap theo `MaxRAMPercentage`, xem metaspace/thread/direct buffer; heap dump và MAT tìm leak. |
| Có nên dùng virtual thread? | "Có, nhanh hơn." | Chỉ lợi cho I/O-bound; kiểm tra pinning (bản JDK, `synchronized` quanh I/O), giới hạn tài nguyên downstream bằng semaphore/pool, `ThreadLocal` nặng; đo trước và sau. |
| N+1 trong JPA | "Đổi sang EAGER." | EAGER là tệ hơn (luôn load, vẫn N+1 với query JPQL); dùng LAZY mặc định + fetch join/entity graph/batch size theo use case; bật log số query; cân nhắc tắt open-in-view. |

## Tình huống

1. **API chậm dần rồi treo, CPU thấp, thread pool đầy.**
   - Gợi ý: lấy thread dump vài lần; tìm thread chờ connection pool (HikariCP), chờ HTTP ngoài không
     timeout, deadlock; kiểm tra `REQUIRES_NEW` giữ hai connection; đặt timeout mọi tầng.
2. **Pod Java bị restart liên tục với exit code 137, log không có lỗi.**
   - Gợi ý: OOMKilled; so `-Xmx`/`MaxRAMPercentage` với limit; đo native memory (NMT); giảm heap
     hoặc tăng limit; nhiều thread quá (stack).
3. **Sau khi thêm `@Async` vào method gửi email, email vẫn gửi đồng bộ.**
   - Gợi ý: chưa `@EnableAsync`, hoặc gọi từ cùng class (self-invocation); kiểm tra executor mặc định,
     exception trong method `void` async bị mất.
4. **User A thỉnh thoảng thấy tenant của user B.**
   - Gợi ý: `ThreadLocal` tenant không `remove()` trong `finally`; field mutable trong singleton bean;
     cache key thiếu tenant.
5. **Batch import 1 triệu dòng bằng JPA chạy 3 giờ, RAM tăng dần.**
   - Gợi ý: persistence context phình; `flush/clear` theo lô; bật JDBC batch (`hibernate.jdbc.batch_size`),
     đổi khỏi `IDENTITY` nếu được; hoặc dùng `JdbcTemplate.batchUpdate`/COPY.
6. **Hai người cùng sửa một đơn hàng, thay đổi của người đầu mất.**
   - Gợi ý: lost update; `@Version` optimistic locking, trả 409 để client tải lại; hoặc lock pessimistic
     nếu tranh chấp cao.

## ❓ Câu hỏi hay gặp

🟢
- Vì sao `Integer` 127 so bằng `==` là `true` còn 128 là `false`?
- Vì sao `String` immutable? String pool là gì?
- Checked và unchecked exception khác nhau thế nào?
- `ArrayList` và `LinkedList` chọn cái nào, vì sao?
- Constructor injection tốt hơn field injection ở điểm nào?

🟡
- Chuyện gì xảy ra khi dùng một object làm key của `HashMap` rồi sửa field của nó?
- `HashMap` resize và treeify khi nào?
- `volatile` đảm bảo gì và không đảm bảo gì?
- Vì sao `@Transactional` không có tác dụng khi gọi method trong cùng class?
- Transaction không rollback khi ném `IOException`, vì sao?
- `LazyInitializationException` xảy ra khi nào? Open-in-view liên quan thế nào?
- PECS là gì? Cho ví dụ.

🔴
- G1 và ZGC khác nhau thế nào? Khi nào đổi GC?
- JVM trong container tính heap thế nào? Vì sao bị OOMKilled mà không có `OutOfMemoryError`?
- Virtual thread khác platform thread thế nào? Pinning là gì?
- `ThreadLocal` gây leak trong thread pool thế nào?
- Dirty checking hoạt động thế nào, ảnh hưởng hiệu năng batch ra sao?
- `UnexpectedRollbackException` xảy ra trong kịch bản nào?

## Bài tập tự làm

1. Viết `LruCache.java` (chạy bằng `java LruCache.java`) dùng `LinkedHashMap`, rồi giải thích vì sao
   nó không thread-safe và bạn sẽ sửa thế nào.
2. Viết một đoạn Java minh hoạ `ConcurrentModificationException` trong **một** thread, và hai cách sửa.
3. Vẽ sơ đồ luồng gọi khi controller gọi `service.a()`, trong `a()` gọi `this.b()` có
   `@Transactional(propagation = REQUIRES_NEW)`. Chỉ ra transaction nào thực sự được tạo.
4. Với entity `Order` có `@ManyToOne Customer` và `@OneToMany items`, viết JPQL/entity graph để lấy
   20 đơn hàng mới nhất kèm customer và items mà không N+1 và không phân trang trong RAM.
5. Tính cấu hình heap cho container limit 2 GB, app có khoảng 200 thread. Nêu giả định của bạn.

> Nộp bài vào đây để được review.
