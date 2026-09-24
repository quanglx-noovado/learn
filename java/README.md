# Java

Chạy một bài (JDK 11+, không cần `javac`): `java java/01-basics/Basics.java`

Kiểm tra đã cài chưa: `java -version`. Nếu chưa: `brew install openjdk`.

## Cách dùng checklist này

Ba mức, hiểu theo *bạn làm được gì* chứ không phải *bạn đã đọc gì*:

| Mức | Nghĩa là |
|---|---|
| **N** — Nền tảng | Viết được code chạy đúng, biết API nào dùng cho việc gì. |
| **V** — Vững | Giải thích được **cơ chế bên dưới**: nó lưu gì trong memory, chạy bao nhiêu bước, hỏng khi nào. |
| **S** — Senior | Nêu được **đánh đổi** và **chọn được** giữa các phương án; debug được khi nó cháy trên production; biết chi phí (CPU, memory, latency) của lựa chọn đó. |

> Chỉ tick `[x]` khi bạn **giảng lại được cho người khác mà không mở tài liệu**.
> Đọc hiểu thì mới là mức N.

## Lộ trình bài học trong repo

- [x] **01-basics** — primitive vs reference, `==` vs `.equals()`, class/object, collection, exception
- [ ] 02-oop — kế thừa, `abstract`, `interface`, đa hình, `record`, `sealed`
- [x] **03-collections** — Collections Framework, dịch từ dev.java; bản gốc tiếng Anh ở `03-collections/en/`
- [ ] 04-generics — type parameter, wildcard, type erasure
- [ ] 05-streams — `map`/`filter`/`collect`, `Optional`, lazy evaluation
- [ ] 06-concurrency — Java Memory Model, `ExecutorService`, virtual thread
- [ ] 07-jvm — memory layout, GC, class loading, đọc JFR
- [ ] 08-build — Maven, dependency resolution, multi-module
- [ ] 09-spring — DI container, proxy/AOP, transaction
- [ ] 10-persistence — JDBC, connection pool, JPA và bẫy N+1

---

## Checklist ôn tập

### 1. Ngôn ngữ & hệ thống kiểu

- [ ] **N** — primitive vs reference; autoboxing và chi phí của nó
- [ ] **N** — `==` vs `.equals()`; hợp đồng `equals`/`hashCode` (5 điều kiện của `equals`)
- [ ] **N** — `final` trên biến / method / class khác nhau chỗ nào
- [ ] **V** — String pool: `new String("a")` khác `"a"` ra sao; `intern()` làm gì
- [ ] **V** — vì sao `String` bất biến (immutable), và điều đó giúp gì cho hashcode caching & thread safety
- [ ] **V** — `StringBuilder` vs nối chuỗi trong vòng lặp: compiler tự tối ưu tới đâu (và chỗ nào nó **không** tối ưu được)
- [ ] **V** — `Integer` cache `-128..127`: vì sao `Integer.valueOf(127) == Integer.valueOf(127)` là `true` còn `128` thì `false`
- [ ] **V** — floating point: vì sao `0.1 + 0.2 != 0.3`, khi nào bắt buộc dùng `BigDecimal` (tiền!)
- [ ] **S** — `record` vs class thường: sinh ra gì, khi nào **không** nên dùng record
- [ ] **S** — `sealed` interface + pattern matching `switch`: mô hình hóa được kiểu tổng (sum type), compiler check đủ nhánh
- [ ] **S** — text block, `var`: khi nào `var` làm code khó đọc hơn

### 2. OOP & thiết kế

- [ ] **N** — kế thừa, `abstract`, `interface`, đa hình; overload vs override
- [ ] **N** — access modifier: `private` / package-private / `protected` / `public`
- [ ] **V** — `default method` trên interface: vì sao Java 8 phải thêm nó (câu trả lời nằm ở Collections Framework)
- [ ] **V** — static dispatch vs dynamic dispatch; vtable trong JVM
- [ ] **V** — vì sao "composition over inheritance"; bài toán fragile base class
- [ ] **S** — Liskov substitution bị vi phạm trông như thế nào trong code thật (ví dụ kinh điển: `Square extends Rectangle`)
- [ ] **S** — design pattern **thực sự** hay dùng: Strategy, Factory, Builder, Adapter, Decorator, Observer, Template Method — và mùi của việc lạm dụng pattern
- [ ] **S** — SOLID: giải thích được từng chữ bằng code trong dự án thật, không bằng ví dụ animal/dog
- [ ] **S** — thiết kế API: immutability, fail-fast, tối thiểu hóa bề mặt public, đặt tên; vì sao thêm API dễ còn bỏ API rất khó

### 3. Collections

- [ ] **N** — chọn đúng `List` / `Set` / `Map` / `Deque` cho từng nhu cầu
- [ ] **N** — `ArrayList` vs `LinkedList`; `HashMap` vs `TreeMap` vs `LinkedHashMap`
- [ ] **V** — `ArrayList` tăng dung lượng thế nào (1.5×), vì sao `add` là **amortized** O(1)
- [ ] **V** — `HashMap` bên trong: bucket, `hash()` spread function, load factor 0.75, resize, **treeify** khi bucket > 8 (Java 8+)
- [ ] **V** — `hashCode` tồi gây hậu quả gì; tấn công hash collision (vì sao Java phải treeify)
- [ ] **V** — fail-fast iterator & `ConcurrentModificationException`: `modCount` hoạt động ra sao
- [ ] **V** — vì sao `LinkedList` nhanh về lý thuyết nhưng chậm trong thực tế (cache locality, pointer chasing)
- [ ] **S** — `ConcurrentHashMap` vs `Collections.synchronizedMap` vs `HashMap` + lock: khác nhau ở đâu, `computeIfAbsent` có atomic không
- [ ] **S** — `CopyOnWriteArrayList`: hợp lý khi nào (đọc nhiều ghi cực ít), tốn gì
- [ ] **S** — `EnumMap` / `EnumSet`: vì sao nhanh hơn hẳn `HashMap` khi key là enum (bitset & array indexing)
- [ ] **S** — immutable collection (`List.of`, `Map.copyOf`): khác `Collections.unmodifiableList` ở chỗ nào

### 4. Generics

- [ ] **N** — type parameter, bounded type `<T extends Comparable<T>>`
- [ ] **V** — **type erasure**: generic biến mất lúc runtime, hệ quả là gì (không `new T[]`, không `instanceof List<String>`)
- [ ] **V** — PECS: `? extends` để đọc, `? super` để ghi — giải thích bằng `Collections.copy`
- [ ] **V** — vì sao `List<String>` **không phải** là `List<Object>` (invariance), trong khi `String[]` lại là `Object[]` (covariance của array — và cái bẫy `ArrayStoreException`)
- [ ] **S** — bridge method do compiler sinh ra để nối erasure với override
- [ ] **S** — khi nào cần truyền `Class<T>` hoặc `TypeToken` để lách erasure (Jackson, Gson làm thế)

### 5. Streams & functional

- [ ] **N** — `map` / `filter` / `collect` / `reduce`; `Optional` dùng đúng cách (không `.get()` bừa)
- [ ] **V** — stream là **lazy**: intermediate op không chạy cho tới khi gặp terminal op; short-circuit (`findFirst`, `anyMatch`)
- [ ] **V** — `Collectors.groupingBy` / `toMap` (và bẫy duplicate key, bẫy `null` value)
- [ ] **V** — method reference bên trong là gì: `invokedynamic` + `LambdaMetafactory`, khác hẳn anonymous class
- [ ] **S** — `parallelStream()`: dùng chung ForkJoinPool.commonPool → vì sao **gần như luôn sai** trong web app; khi nào mới đáng dùng
- [ ] **S** — chi phí của stream so với vòng lặp thường (megamorphic call site, boxing); dùng `IntStream` để tránh boxing
- [ ] **S** — viết được custom `Collector`, hiểu `Spliterator` để nguồn dữ liệu của bạn chạy được stream

### 6. Exception & xử lý lỗi

- [ ] **N** — checked vs unchecked; `try-with-resources`
- [ ] **V** — `finally` vs `try-with-resources`: thứ tự đóng, suppressed exception
- [ ] **V** — vì sao **không** nuốt exception (`catch (Exception e) {}`), vì sao không `catch Throwable`
- [ ] **V** — chi phí của việc tạo exception (`fillInStackTrace`); vì sao dùng exception cho control flow là đắt
- [ ] **S** — thiết kế phân tầng exception: lỗi nghiệp vụ vs lỗi hạ tầng, cái nào retry được, cái nào không
- [ ] **S** — đối chiếu với Go: error là giá trị (xem `go/README.md`) — mỗi mô hình mạnh/yếu ở đâu

### 7. JVM: memory, GC, class loading

- [ ] **N** — stack vs heap; cái gì nằm ở đâu
- [ ] **V** — cấu trúc bộ nhớ: heap (young/old), metaspace, thread stack, code cache, direct buffer
- [ ] **V** — vòng đời object: eden → survivor → old; vì sao "hầu hết object chết trẻ" (weak generational hypothesis)
- [ ] **V** — `OutOfMemoryError` có nhiều loại khác nhau (heap space, GC overhead, metaspace, direct buffer, unable to create native thread) — mỗi loại nguyên nhân khác nhau
- [ ] **V** — memory leak trong Java dù có GC: static collection phình, `ThreadLocal` không remove, listener không gỡ, classloader leak
- [ ] **S** — chọn GC: G1 (mặc định) vs ZGC vs Parallel — theo tiêu chí throughput / latency / footprint
- [ ] **S** — đọc được GC log: pause time, allocation rate, promotion rate; phân biệt "GC nhiều" với "leak"
- [ ] **S** — JIT: interpreter → C1 → C2, inlining, escape analysis, deoptimization; vì sao benchmark phải warm-up (và vì sao cần JMH)
- [ ] **S** — class loading: parent delegation, vì sao có `NoClassDefFoundError` vs `ClassNotFoundException`, jar hell
- [ ] **S** — đọc được bytecode bằng `javap -c` để trả lời câu hỏi "thật ra dòng này biên dịch thành gì"

### 8. Concurrency

- [ ] **N** — `Thread`, `Runnable`, `ExecutorService`, `Future`
- [ ] **N** — `synchronized`, `volatile`, `AtomicInteger`
- [ ] **V** — **Java Memory Model**: happens-before, visibility, reordering — vì sao `volatile` không đủ để làm counter
- [ ] **V** — race condition vs deadlock vs livelock vs starvation; cách tái hiện từng cái
- [ ] **V** — `ConcurrentHashMap`, `BlockingQueue`, `CountDownLatch`, `Semaphore` dùng khi nào
- [ ] **V** — thread pool sizing: CPU-bound (≈ số core) vs IO-bound (lớn hơn nhiều); hàng đợi unbounded là bom hẹn giờ
- [ ] **S** — `AbstractQueuedSynchronizer` (AQS) — nền của `ReentrantLock`, `Semaphore`, `CountDownLatch`
- [ ] **S** — `CompletableFuture`: compose, exception, và bẫy chạy nhầm trên common pool
- [ ] **S** — **virtual thread** (Java 21+): giải quyết vấn đề gì, pinning vì `synchronized`, vì sao pool thread không còn cần thiết
- [ ] **S** — structured concurrency; đối chiếu với goroutine + `context` của Go
- [ ] **S** — false sharing, cache line, `@Contended`; vì sao `LongAdder` nhanh hơn `AtomicLong` khi tranh chấp cao

### 9. I/O & serialization

- [ ] **N** — `InputStream`/`Reader`, đọc/ghi file, `Files` API
- [ ] **V** — blocking vs non-blocking IO; NIO buffer & channel; `ByteBuffer` direct vs heap
- [ ] **V** — encoding: UTF-8, `Charset` mặc định (và vì sao Java 18 đổi mặc định sang UTF-8 là chuyện lớn)
- [ ] **S** — JSON (Jackson): streaming vs databind, chi phí reflection, cấu hình an toàn
- [ ] **S** — `Serializable` của Java: vì sao bị coi là sai lầm thiết kế, lỗ hổng deserialization

### 10. Build, dependency, module

- [ ] **N** — Maven lifecycle, `pom.xml`, scope của dependency
- [ ] **V** — dependency resolution: nearest-wins, `dependencyManagement`, BOM, `mvn dependency:tree` để gỡ xung đột
- [ ] **V** — Gradle khác Maven chỗ nào (incremental build, build cache, configuration cache)
- [ ] **S** — multi-module: cắt module theo đâu để không thành đống vòng lặp phụ thuộc
- [ ] **S** — JPMS (module system), fat jar vs thin jar, reproducible build
- [ ] **S** — supply chain: pin version, `mvn versions:display-dependency-updates`, quét CVE

### 11. Chất lượng & kiểm thử

> Repo này **không tự viết test** (xem `~/.claude/CLAUDE.md`) — nhưng hiểu chiến lược test vẫn là kỹ năng senior.

- [ ] **N** — JUnit 5: `@Test`, assertion, `@ParameterizedTest`
- [ ] **V** — test pyramid: unit / integration / e2e — tỷ lệ hợp lý và vì sao
- [ ] **V** — mock vs stub vs fake vs spy; dấu hiệu mock quá nhiều (test dính chặt vào implementation)
- [ ] **S** — Testcontainers: test với DB thật thay vì H2 (và vì sao H2 hay cho kết quả sai lệch)
- [ ] **S** — flaky test: nguyên nhân hay gặp (thời gian, thứ tự, trạng thái chung, concurrency) và cách chặn
- [ ] **S** — static analysis: SpotBugs, Error Prone, NullAway; chọn rule nào đáng bật

### 12. Spring

- [ ] **N** — DI, `@Component`/`@Service`, `@RestController`, cấu hình qua `application.yml`
- [ ] **V** — bean lifecycle, scope (singleton là **mặc định** → bean có state là bug), circular dependency
- [ ] **V** — `@Transactional` thực chất là **proxy**: vì sao gọi method nội bộ (self-invocation) không mở transaction
- [ ] **V** — propagation (`REQUIRED` vs `REQUIRES_NEW`) và isolation level
- [ ] **S** — Spring Boot auto-configuration hoạt động ra sao (`@Conditional`, `spring.factories` / `AutoConfiguration.imports`)
- [ ] **S** — AOP: JDK dynamic proxy vs CGLIB, giới hạn của từng loại
- [ ] **S** — Spring MVC (thread-per-request) vs WebFlux (reactive): khi nào reactive **không** đáng
- [ ] **S** — actuator, health check, graceful shutdown, readiness vs liveness

### 13. Database từ phía Java

- [ ] **N** — JDBC, `PreparedStatement` (và vì sao nó chống SQL injection)
- [ ] **V** — connection pool (HikariCP): pool size hợp lý, leak detection, vì sao pool to **không** nhanh hơn
- [ ] **V** — JPA/Hibernate: persistence context, dirty checking, lazy loading, `LazyInitializationException`
- [ ] **V** — **N+1 query**: nhận ra nó, và sửa bằng `join fetch` / `@EntityGraph` / batch size
- [ ] **S** — isolation level & hiện tượng đi kèm (dirty read, non-repeatable read, phantom); khóa lạc quan vs bi quan
- [ ] **S** — transaction ôm cả HTTP call bên ngoài = giữ connection quá lâu; vì sao đó là sự cố production kinh điển
- [ ] **S** — migration (Flyway/Liquibase): migration tương thích ngược để deploy không downtime

### 14. Chạy production & gỡ lỗi

- [ ] **V** — `jps`, `jstack`, `jmap`, `jcmd`: lấy thread dump & heap dump
- [ ] **V** — đọc thread dump: tìm deadlock, tìm thread bị block, tìm pool cạn
- [ ] **S** — JFR (Java Flight Recorder) + JMC; async-profiler để vẽ flame graph
- [ ] **S** — phân tích heap dump bằng MAT: dominator tree, tìm cái gì giữ reference
- [ ] **S** — quy trình xử lý "app chậm": đo trước, đoán sau — latency ở tầng nào (GC? DB? lock? network?)
- [ ] **S** — JVM flag đáng biết: `-Xmx`, `-XX:+HeapDumpOnOutOfMemoryError`, `-XX:MaxRAMPercentage` (quan trọng khi chạy trong container)
- [ ] **S** — JVM trong container: vì sao ngày xưa JVM đọc sai giới hạn memory của cgroup, giờ ra sao

---

## Câu hỏi tự kiểm tra mức senior

Trả lời trôi chảy được hết là ổn. Vấp chỗ nào thì đó là bài học tiếp theo.

1. `HashMap` xử lý collision thế nào, và vì sao Java 8 đổi linked list thành cây đỏ-đen ở bucket lớn?
2. `volatile` bảo đảm điều gì và **không** bảo đảm điều gì? Viết một counter đúng bằng 3 cách khác nhau.
3. Service đang chạy ngon bỗng p99 latency vọt lên 2s, CPU thấp. Bạn kiểm tra gì, theo thứ tự nào?
4. Vì sao `@Transactional` trên method `private` hoặc gọi từ trong cùng class lại không có tác dụng?
5. `parallelStream()` trong một HTTP handler gây hại gì cho phần còn lại của ứng dụng?
6. Phân biệt `OutOfMemoryError: Java heap space` với `GC overhead limit exceeded` — cách xử lý khác nhau ra sao?
7. Virtual thread giải quyết vấn đề gì mà thread pool không giải quyết được? Nó **không** giúp gì?
8. Cho một endpoint chạy 40 query thay vì 1. Bạn phát hiện bằng cách nào, sửa thế nào?
9. Vì sao `String` bất biến, và nếu nó khả biến thì hỏng những gì?
10. Type erasure khiến bạn **không** viết được những gì? Nêu 3 ví dụ và cách lách.

## Bài tập cho 01-basics

1. Thêm class `KhoNgonNgu` với method `timTheoTen(String)` trả về `Optional<NgonNgu>`.
2. Cho `NgonNgu` implement `Comparable<NgonNgu>` (sắp theo năm) rồi `Collections.sort`.
3. Ghi đè `equals` và `hashCode` cho `NgonNgu`, kiểm tra bằng `HashSet` xem có chặn trùng.
4. Bỏ `hashCode` đi (chỉ giữ `equals`) rồi cho vào `HashMap` — giải thích **vì sao** tra cứu hỏng.
5. Dùng `javap -c` xem `Basics.class`: tìm chỗ compiler biến `+` trên String thành `invokedynamic`.
