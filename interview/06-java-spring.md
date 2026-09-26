# 06. Java, JVM và Spring

> [← Mục lục](README.md) · Trọng tâm: **Java 25 LTS** (đối chiếu 21 LTS, ghi chú JDK 26–27), JVM, concurrency, **Spring Boot 4 / Spring Framework 7**, JPA/Hibernate 7.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn.

Đây là ngôn ngữ phụ (ngôn ngữ chính là PHP, xem [05-php-laravel.md](05-php-laravel.md)).
**Ôn sâu khi JD yêu cầu Java/Go; nếu không, chặng 1 đủ để đối chiếu.**

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

Concurrency tổng quát (race, deadlock, lock DB) ở [13-concurrency.md](13-concurrency.md). Code Java
chạy được trong repo: [java/](../java/README.md) (chạy `java File.java`, cần JDK 11+; cài bằng
`brew install openjdk`).

---

## Tài liệu nền

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [dev.java Learn](https://dev.java/learn/) | Official tutorial | Ngôn ngữ, Collections, JVM tools. Bản dịch một phần ở [java/03-collections/](../java/03-collections/README.md) |
| [JEP index](https://openjdk.org/jeps/0) | Đặc tả tính năng | Nguồn chuẩn cho "tính năng X có từ bản nào, còn preview không" |
| *Effective Java*, 3rd ed. (Joshua Bloch) | Sách | Item về `equals`/`hashCode`, generics, exception, concurrency. Đọc theo item, không cần đọc hết |
| *Java Concurrency in Practice* (Goetz và cộng sự) | Sách | Ch.2–3 (thread safety, visibility), ch.6–8 (executor, pool). Cũ nhưng nền tảng không đổi |
| [Spring Framework reference](https://docs.spring.io/spring-framework/reference/) | Official docs | Container, AOP, transaction, web |
| [Spring Boot reference](https://docs.spring.io/spring-boot/reference/) | Official docs | Auto-configuration, config, task execution, testing, Actuator |
| [Hibernate ORM User Guide](https://docs.jboss.org/hibernate/orm/7.2/userguide/html_single/Hibernate_User_Guide.html) | Official docs | Persistence context, fetching, batching, locking |
| [Vlad Mihalcea: Hibernate tutorials](https://vladmihalcea.com/tutorials/hibernate/) | Blog | Các bẫy hiệu năng JPA thực tế, có đo SQL sinh ra |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.5 | Đọc và viết Java/Spring cơ bản, đối chiếu được với PHP/Laravel | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.7 | Dùng đúng Java hiện đại, collections, concurrency, Spring proxy/transaction, JPA, security, test | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.5 | Hiểu JVM, chẩn đoán production, container, virtual thread, nâng cấp Boot 4 | 7–9 ngày |

Nếu JD chỉ ghi "biết thêm Java là lợi thế", dừng ở chặng 1 và module 2.4. Nếu JD là Java/Spring
chính, học hết và coi chặng 3 là phần bị hỏi nhiều nhất.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Ngôn ngữ cốt lõi

**Vì sao cần học:** Các câu vặn kiểu `==` với `Integer` hay `equals`/`hashCode` là bộ lọc junior
kinh điển của phỏng vấn Java. Với người từ PHP, nhiều chỗ ngược trực giác: ở PHP `==`/`===` với số
và chuỗi là so giá trị, còn ở Java `==` với object là so xem có phải cùng một object không.

**Học gì**

*Primitive và wrapper*
- Java có 8 kiểu *primitive* (kiểu nguyên thuỷ, lưu thẳng giá trị, không phải object): `byte`,
  `short`, `int`, `long`, `float`, `double`, `char`, `boolean`.
- Mỗi primitive có một lớp *wrapper* bọc nó thành object: `Integer`, `Long`, `Double`...
  - Collection như `List<Integer>` chỉ chứa object, nên phải dùng wrapper.
  - *Autoboxing/unboxing*: Java tự đổi qua lại giữa `int` và `Integer` khi cần.
- `==` với object so **reference** (hai biến có trỏ cùng một object không), không so giá trị.
  Muốn so giá trị thì dùng `equals`.
- ⚠️ Cache `Integer` từ -128 tới 127:

  ```java
  Integer a = 127, b = 127;   // a == b là true: cùng một object lấy từ cache
  Integer c = 128, d = 128;   // c == d là false: hai object khác nhau
  c.equals(d);                // true
  ```

  - Autoboxing gọi `Integer.valueOf`, và hàm này trả object dựng sẵn cho khoảng -128..127.
  - Test với số nhỏ thì chạy đúng, production với id lớn thì sai. Bug kiểu này rất khó thấy.
- ⚠️ Unboxing `null` ném `NullPointerException` (NPE): `Integer x = null; int y = x;`. Hay gặp
  khi lấy từ `Map` một key không có rồi gán vào `int`.

*Tiền: BigDecimal*
- `double` không lưu chính xác được `0.1` (giống float của PHP), nên tiền dùng `BigDecimal`.
- Tạo từ `String`: `new BigDecimal("0.1")`. Tạo từ `double` thì mang theo luôn sai số của double.
- ⚠️ So bằng `compareTo`, không so bằng `equals`. `equals` so cả *scale* (số chữ số sau dấu
  phẩy), nên `2.0` và `2.00` bị coi là khác nhau.

*String*
- `String` là *immutable*: không sửa được, mọi thao tác "sửa" đều tạo chuỗi mới.
- *String pool*: các chuỗi literal giống nhau dùng chung một object. Vì vậy `"a" == "a"` đôi khi
  ra `true`, làm người mới tưởng `==` dùng được. ⚠️ Luôn so chuỗi bằng `equals`.
- Nối nhiều lần trong vòng lặp thì dùng `StringBuilder`, để không tạo hàng loạt chuỗi trung gian.
- *Compact strings*: chuỗi chỉ gồm ký tự Latin-1 được lưu 1 byte mỗi ký tự thay vì 2, tiết kiệm heap.

*equals và hashCode*
- `HashMap` tìm key theo hai bước:
  1. Gọi `hashCode()` để chọn ngăn chứa (*bucket*).
  2. Gọi `equals()` để so với từng key trong ngăn đó.
- Hợp đồng: hai object `equals` nhau thì **bắt buộc** `hashCode` bằng nhau.
  - Override `equals` mà quên `hashCode` thì `HashSet` chứa phần tử trùng, `map.get` trả `null`.
- ⚠️ Key mutable: put một object vào `HashMap`, rồi sửa field mà `hashCode` dùng tới.
  - Hash mới trỏ sang bucket khác, nên `get` trả `null` dù phần tử vẫn nằm trong map. Phần tử
    "biến mất".
  - Cách an toàn: dùng key immutable, ví dụ `String` hoặc `record` (module 2.1).

*Truyền tham số*
- Java luôn *pass-by-value*: hàm nhận bản sao của giá trị. Với object, giá trị đó là reference.
  - Sửa field qua tham số: caller thấy thay đổi, vì hai bên cùng trỏ một object.
  - Gán lại tham số (`p = new Person()`): caller không thấy gì, vì chỉ bản sao reference bị đổi.
- Đối chiếu PHP: object PHP cũng truyền kiểu này. Java không có `&$x` để truyền tham chiếu thật.

*final, static, inner class, interface*
- `final`:
  - Trên biến: không gán lại được. Object mà biến trỏ tới vẫn sửa được bên trong.
  - Trên class: không kế thừa được. Trên method: không override được.
- `static`: thuộc về class, không thuộc object nào. Biến `static` dùng chung cho cả JVM
  (module 1.5 giải thích vì sao điều này nguy hiểm hơn ở PHP).
- ⚠️ Inner class không `static` ngầm giữ reference tới object bên ngoài (*outer*).
  - Object inner sống lâu (listener, phần tử cache) giữ luôn outer, nên outer không được thu hồi.
  - Không cần tới outer thì khai `static class`.
- Interface có thể chứa method `default` (có thân, class implement được thừa hưởng), method
  `static` và method `private`.
- Abstract class khác interface ở chỗ có field trạng thái và constructor.
  - Đối chiếu PHP: interface có `default` method gần giống interface kết hợp trait.

**Đọc**
- dev.java: [Getting started / Language basics](https://dev.java/learn/) (mục *Classes and Objects*, *Numbers and Strings*, *Interfaces*)
- Repo: [java/01-basics/Basics.java](../java/01-basics/Basics.java) (`==` và `equals`, collection, exception)
- *Effective Java*: Item 10–11 (`equals`, `hashCode`), Item 17 (immutability)

**Nắm chắc khi**
- [ ] Giải thích được vì sao `Integer a = 128, b = 128; a == b` là `false`
- [ ] Viết được một class làm key `HashMap` đúng hợp đồng, rồi chứng minh bằng code rằng sửa field sau khi put làm `get` trả `null`
- [ ] Giải thích được "Java pass-by-value" bằng ví dụ gán lại tham số so với sửa field

#### 1.2 Exception, lambda, Stream, Optional

**Vì sao cần học:** Code Java hiện đại dày đặc lambda và Stream, và review code hay bắt lỗi ở
đây. Checked exception là khác biệt lớn nhất so với PHP, và ảnh hưởng trực tiếp tới việc
`@Transactional` có rollback hay không (module 2.4).

**Học gì**

*Cây exception*
- Mọi thứ ném được đều là `Throwable`, chia hai nhánh:
  - `Error`: lỗi của JVM như `OutOfMemoryError`, `StackOverflowError`. Không bắt.
  - `Exception`: lỗi của chương trình.
- Trong `Exception` có hai loại:
  - *Checked exception* (ví dụ `IOException`): compiler bắt buộc bạn `catch`, hoặc khai `throws`
    trên method để đẩy lên caller.
  - *Unchecked exception*: `RuntimeException` và các lớp con (ví dụ `IllegalArgumentException`,
    NPE). Không bắt buộc gì.
- PHP chỉ có loại unchecked: không ai bắt bạn khai `throws`.
- Checked exception không hợp với lambda: các interface hàm mà Stream dùng (`Function`,
  `Predicate`) không khai `throws`, nên trong `map(...)` không ném checked exception được, phải bọc.
- Spring bọc các lỗi checked (ví dụ của JDBC) thành unchecked, để code không phải khai `throws`
  khắp nơi.

*try-with-resources và finally*
- `try (var in = open(); var out = create()) { ... }` tự gọi `close()` cho từng resource khi ra
  khỏi khối, kể cả khi có exception.
  - Thứ tự `close()` ngược với thứ tự mở: `out` đóng trước, `in` đóng sau.
  - Giống viết `finally { fclose($fh); }` nhưng không thể quên.
- Thân `try` ném exception và `close()` cũng ném: exception của `close()` được gắn vào exception
  chính dưới dạng *suppressed* (lấy bằng `getSuppressed()`), nên lỗi gốc không bị đè mất.
- ⚠️ `return` trong `finally` nuốt exception đang được ném: method trả về bình thường, lỗi biến mất.
- ⚠️ `catch (Exception e) {}` để trống: lỗi biến mất không dấu vết.

*Lambda và Stream*
- *Lambda* là hàm ẩn danh: `x -> x * 2`, giống `fn($x) => $x * 2` của PHP.
  - Lambda chỉ dùng được biến local *effectively final*, tức biến không bị gán lại sau khi khai.
- *Stream* là chuỗi thao tác trên dữ liệu: `list.stream().filter(...).map(...).toList()`. Giống
  collection của Laravel.
  - Stream *lười* (lazy): `filter`, `map` chưa chạy cho tới khi gặp thao tác kết thúc như
    `toList()`, `count()`.
  - Mỗi stream chỉ dùng được một lần.
- ⚠️ Side effect trong `map`/`filter` (sửa biến bên ngoài, ghi DB): vì stream lười và có thể chạy
  song song, số lần và thứ tự chạy không được đảm bảo.
- ⚠️ `parallelStream()` chạy trên `ForkJoinPool.commonPool()`, một thread pool dùng chung cho
  **cả JVM**. Làm I/O blocking trong đó chặn mọi chỗ khác đang dùng pool này.
- ⚠️ `Collectors.toMap`:
  - Hai phần tử có cùng key thì ném lỗi. Cần truyền thêm hàm gộp: `toMap(k, v, (a, b) -> a)`.
  - Value là `null` thì ném NPE.
- `Stream.toList()` (Java 16+) trả list *unmodifiable*, tức không thêm, xoá hay sửa được.

*Optional*
- `Optional<T>` là cái hộp có thể rỗng. Hàm trả `Optional` để nói rõ "có thể không có kết quả"
  thay vì trả `null`, giống kiểu trả về `?User` của PHP.
- Chỉ dùng làm kiểu trả về. Không dùng cho field hay tham số.
- ⚠️ `get()` không kiểm tra gì: hộp rỗng thì ném exception. Dùng `orElseThrow`, `map`, `ifPresent`.
- ⚠️ `orElse(expensive())` **luôn** gọi `expensive()`, kể cả khi hộp có giá trị, vì tham số được
  tính trước khi gọi hàm. Dùng `orElseGet(() -> expensive())` để chỉ gọi khi cần.

**Đọc**
- dev.java: [Exceptions](https://dev.java/learn/exceptions/), [Lambda Expressions](https://dev.java/learn/lambdas/), [Collections and Streams](https://dev.java/learn/api/collections-and-streams/)
- Javadoc: [java.util.stream package summary](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/stream/package-summary.html) (mục *Non-interference*, *Stateless behaviors*)

**Nắm chắc khi**
- [ ] Viết được try-with-resources với hai resource và nói thứ tự `close()` cùng chỗ exception phụ nằm
- [ ] Chỉ ra được 3 lỗi trong một đoạn Stream có side effect, `toMap` trùng key và `orElse` tốn kém

#### 1.3 Collections cơ bản

**Vì sao cần học:** PHP chỉ có một kiểu `array` làm mọi việc. Java tách thành nhiều cấu trúc riêng,
chọn sai thì chậm hoặc sai hành vi. Các câu hay gặp: `ArrayList` hay `LinkedList`, viết LRU cache,
vì sao có `ConcurrentModificationException` khi chỉ có một thread.

**Học gì**

*List và queue*
- `ArrayList`: mảng tự giãn. Truy cập theo index rất nhanh, O(1).
- `LinkedList`: danh sách liên kết. Chèn hoặc xoá ở giữa nhanh nếu đã đứng sẵn ở đó, nhưng truy
  cập theo index là O(n).
- Thực tế gần như luôn chọn `ArrayList`:
  - Phần tử nằm liền nhau trong bộ nhớ nên CPU đọc qua cache rất nhanh (*cache locality*).
  - Node của `LinkedList` nằm rải rác khắp heap, mỗi bước là một lần nhảy bộ nhớ.
- Cần queue hoặc deque (thêm và lấy ở hai đầu) thì dùng `ArrayDeque`.

*Map và Set*

| | Thứ tự khi duyệt | Dùng khi |
|---|---|---|
| `HashMap` | Không đảm bảo | Mặc định |
| `LinkedHashMap` | Thứ tự chèn, hoặc thứ tự truy cập | Cần giữ thứ tự, làm LRU cache |
| `TreeMap` | Sắp theo key | Cần tìm key gần nhất: `floorKey(x)` (key lớn nhất ≤ x), `ceilingKey(x)` (key nhỏ nhất ≥ x) |

- *LRU cache* (Least Recently Used): cache đầy thì bỏ phần tử lâu không được dùng nhất.
  `LinkedHashMap` ở chế độ thứ tự truy cập làm được việc này gần như có sẵn.
- `HashSet` thực chất là một `HashMap` chỉ dùng phần key.
- Đối chiếu PHP: array của PHP là *ordered hash map*, luôn giữ thứ tự chèn.
  - ⚠️ `HashMap` thì không. Port code PHP sang mà dựa vào thứ tự duyệt là sai.

*ConcurrentModificationException*
- Sửa list trong lúc đang duyệt bằng for-each thì ném `ConcurrentModificationException`:

  ```java
  for (String s : list) { if (s.isEmpty()) list.remove(s); }   // ném lỗi
  list.removeIf(String::isEmpty);                               // đúng
  ```

- ⚠️ Tên có chữ "concurrent" nhưng lỗi này xảy ra cả trong **một** thread. Iterator (đối tượng
  làm việc duyệt) phát hiện collection bị sửa bởi thứ khác ngoài nó.
- Sửa bằng `iterator.remove()` hoặc `removeIf`.

*Collection không sửa được*
- `List.of(...)`, `Map.of(...)`: immutable thật sự.
  - ⚠️ Không cho phần tử `null`, có `null` là ném NPE.
- `Collections.unmodifiableList(list)`: chỉ là *view*, tức cửa sổ nhìn vào list gốc.
  - Không sửa được qua view, nhưng ai đó sửa list gốc thì view thay đổi theo.
- `List.copyOf(list)`: chụp một bản immutable độc lập với list gốc.
- ⚠️ `Arrays.asList(arr)`:
  - Kích thước cố định: `add`, `remove` ném lỗi.
  - `set` ghi xuyên vào mảng gốc.

**Đọc**
- Repo (bản dịch dev.java): [Collections](../java/03-collections/README.md), đặc biệt [List](../java/03-collections/05-list.md), [Map](../java/03-collections/09-map.md), [Chọn key immutable](../java/03-collections/13-chon-key-immutable.md), [ArrayList vs LinkedList](../java/03-collections/14-arraylist-vs-linkedlist.md)

**Nắm chắc khi**
- [ ] Viết được LRU cache bằng `LinkedHashMap` trong 10 dòng (bài tập 1)
- [ ] Tái hiện được `ConcurrentModificationException` trong một thread và sửa theo hai cách (bài tập 2)

#### 1.4 Spring và Spring Boot cơ bản

**Vì sao cần học:** Spring Boot là framework mặc định của backend Java, giống vị trí của Laravel
với PHP. Câu hỏi hay gặp: DI là gì, vì sao nên dùng constructor injection, và "vì sao thêm một
dependency là tự có `DataSource`".

**Học gì**

*IoC và DI*
- *Dependency Injection* (DI): class không tự `new` các dependency mà nhận chúng từ bên ngoài,
  thường qua constructor.
- *Inversion of Control* (IoC): framework, không phải code của bạn, lo việc tạo và nối các object.
- Trong Spring:
  - Object do container quản lý gọi là *bean*.
  - Container là `ApplicationContext`, tương đương service container của Laravel.
- Hai cách khai bean:
  - Gắn `@Component`, `@Service` hoặc `@Repository` lên class. Lúc khởi động Spring quét các
    package để tìm chúng (*component scan*). Ba annotation này gần như giống nhau, chủ yếu để phân vai.
  - Viết một method trả về object, gắn `@Bean`, đặt trong class có `@Configuration`. Giống
    `$this->app->singleton(...)` trong ServiceProvider.

*Constructor injection*
- Có ba cách inject: qua constructor, qua setter, hoặc gắn `@Autowired` thẳng lên field.
- Nên dùng constructor, vì:
  - Field khai được `final`, không bị thay sau khi tạo.
  - Test chỉ cần `new OrderService(fakeRepo)`, không cần khởi động container.
  - Constructor quá dài lộ ra class có quá nhiều dependency, dấu hiệu nên tách class.
- Field injection khó test: phải dùng reflection hoặc container mới gán được dependency.

*Nhiều bean cùng kiểu*
- Có hai bean cùng kiểu `PaymentGateway` thì Spring không biết inject cái nào, báo lỗi lúc khởi động.
- Cách chọn:
  - `@Qualifier("momo")`: chọn theo tên.
  - `@Primary`: đặt một bean làm mặc định.
  - Inject `List<PaymentGateway>`: nhận tất cả. Hợp với pattern Strategy (chọn gateway lúc chạy).

*Circular dependency*
- *Circular dependency*: bean A cần B, và B lại cần A.
- ⚠️ Từ Boot 2.6, mặc định app từ chối khởi động khi gặp vòng này. Hãy sửa thiết kế, ví dụ tách
  phần dùng chung ra class thứ ba. Đừng bật lại cho phép vòng chỉ để chạy được.

*Auto-configuration*
- Boot có sẵn rất nhiều class cấu hình, mỗi class chỉ bật khi thoả điều kiện:
  - `@ConditionalOnClass`: trên *classpath* có class X. Classpath là tập thư viện app đang nạp,
    tương tự thư mục `vendor/`.
  - `@ConditionalOnMissingBean`: bạn chưa tự khai bean cùng kiểu.
  - `@ConditionalOnProperty`: config có property Y.
- Mỗi thư viện liệt kê các class auto-config của nó trong file `AutoConfiguration.imports` (nằm
  trong `META-INF/spring/`).
- Ví dụ, thêm starter JDBC và driver MySQL:
  1. Classpath có class `DataSource`, nên điều kiện `OnClass` đúng.
  2. Bạn chưa khai `DataSource`, nên điều kiện `OnMissingBean` đúng.
  3. Boot tạo `DataSource` từ các key `spring.datasource.*`.
- Bạn tự khai bean cùng kiểu thì auto-config lùi lại, nhờ điều kiện `OnMissingBean`.
- Debug "vì sao bean này có hoặc không có": chạy app với `--debug`, hoặc xem
  `/actuator/conditions`. Cả hai in ra *condition report*, tức danh sách điều kiện nào đúng, nào sai.

*Config và profile*
- `application.yml` là file config, vai trò như `.env` cộng thư mục `config/` của Laravel.
- *Profile*: file `application-{profile}.yml` (ví dụ `application-prod.yml`) được nạp thêm khi
  bật profile đó.
- Thứ tự ưu tiên khi cùng một key có ở nhiều nơi: tham số dòng lệnh đè biến môi trường, biến môi
  trường đè file.
- `@ConfigurationProperties(prefix = "payment")` map cả nhóm config vào một class có kiểu, và
  validate được. Tốt hơn rải `@Value("${...}")` khắp nơi.

**Đọc**
- Spring: [The IoC Container](https://docs.spring.io/spring-framework/reference/core/beans.html) (đọc *Dependencies*, *Bean Scopes*)
- Boot: [Auto-configuration](https://docs.spring.io/spring-boot/reference/using/auto-configuration.html), [Creating Your Own Auto-configuration](https://docs.spring.io/spring-boot/reference/features/developing-auto-configuration.html) (mục *Condition Annotations*), [Externalized Configuration](https://docs.spring.io/spring-boot/reference/features/external-config.html), [Profiles](https://docs.spring.io/spring-boot/reference/features/profiles.html)

**Nắm chắc khi**
- [ ] Giải thích được vì sao thêm một dependency JDBC vào classpath là có `DataSource` mà không viết dòng nào
- [ ] Ghi đè được một bean auto-config và chứng minh bằng condition report
- [ ] Nói được thứ tự ưu tiên khi cùng một key có trong `application.yml`, biến môi trường và tham số dòng lệnh

#### 1.5 Đối chiếu với PHP/Laravel

**Vì sao cần học:** Module này là lý do chính để người làm PHP học chặng 1: người phỏng vấn
thường hỏi "khác gì so với stack bạn đang dùng". Hiểu đúng khác biệt mô hình runtime giúp tránh
cả nhóm bug mà PHP-FPM không bao giờ gặp.

**Học gì**

*Mô hình runtime*

| | PHP-FPM | Spring MVC |
|---|---|---|
| Process | Nhiều worker process | Một process JVM sống lâu |
| Đơn vị xử lý một request | Một worker | Một thread lấy từ pool (Tomcat mặc định tối đa 200), hoặc một virtual thread (module 3.4) |
| Số request đồng thời tối đa | `pm.max_children` | Số thread của pool |
| Sau khi request xong | Dọn sạch mọi biến | Mọi object vẫn còn |

- *Share-nothing*: ở PHP-FPM mỗi request bắt đầu sạch, không thấy biến của request khác.
- Ở Spring, bean singleton (mỗi class một object cho cả app) và biến `static` **dùng chung** giữa
  mọi request đang chạy song song.
- Bug mà PHP-FPM không có:
  - State rò giữa request: lưu user hiện tại vào field của một service, request khác đọc nhầm.
  - Race trên field: hai thread cùng sửa một field một lúc.
- Octane/Swoole giữ app PHP sống qua nhiều request, nên gặp lại đúng các bẫy này
  ([05-php-laravel.md](05-php-laravel.md)).

*Connection pool*
- PHP-FPM: mỗi worker giữ một connection DB riêng.
- Java: một pool dùng chung trong process (HikariCP là pool mặc định của Boot). Tổng số connection
  tới DB = pool size × số instance.

*DI container*

| | Spring | Laravel |
|---|---|---|
| Mặc định | Singleton: một object cho cả app | `bind`: tạo object mới mỗi lần resolve |
| `singleton` sống bao lâu | Cả đời process | Một request (dưới FPM) |
| Lúc tạo và nối | Lúc khởi động | Lúc resolve, bằng reflection (*auto-wiring*) |
| Thiếu dependency | *Fail-fast*: app không khởi động được | Chỉ lỗi khi chạy tới chỗ cần |
| Proxy bọc bean | Có, để làm transaction, async, cache (module 2.4) | Không |

- Laravel còn có *facade* (gọi kiểu static như `Cache::get`), khác với injection tường minh qua
  constructor.

*Lỗi và transaction*
- Java có checked exception, PHP chỉ có unchecked (module 1.2).
- ⚠️ `@Transactional` của Spring rollback theo **loại** exception, mặc định chỉ với unchecked
  (module 2.4). `DB::transaction` của Laravel rollback với mọi `Throwable`.

*ORM*
- Hibernate theo mô hình *Data Mapper* + *Unit of Work*:
  - Entity là object thường, không tự biết lưu mình. Một lớp riêng lo việc đọc ghi DB.
  - Hibernate nhớ các entity đã load. Cuối transaction nó tự so sánh và sinh `UPDATE` cho những
    cái đã đổi (*dirty checking*, module 2.5).
- Eloquent theo mô hình *Active Record*: model tự lưu chính nó, và bạn phải gọi `save()` tường minh.
- ⚠️ Hệ quả: với Hibernate, chỉ cần `order.setStatus(...)` trong transaction là DB bị update, dù
  không gọi hàm lưu nào.

*Việc sau commit và request context*
- Chạy việc sau khi transaction commit (gửi email, bắn event):
  `@TransactionalEventListener(phase = AFTER_COMMIT)` tương đương `afterCommit` của Laravel.
- Dữ liệu theo request (user đăng nhập của Spring Security, MDC của log) được Spring lưu trong
  `ThreadLocal`, tức biến mà mỗi thread có một bản riêng (module 2.3).
  - *MDC* (Mapped Diagnostic Context): map key/value tự gắn vào mọi dòng log của thread hiện tại.
  - Laravel thì dùng request object và container theo request.

**Đọc**
- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (`pm.*`); Laravel: [Service Container](https://laravel.com/docs/container) (binding, singleton, scoped); Spring: [Bean Scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html)

**Nắm chắc khi**
- [ ] Giải thích được trong 2 phút vì sao lưu `currentUser` vào field của một `@Service` là bug ở Spring nhưng lưu vào thuộc tính của service Laravel thì (dưới FPM) không
- [ ] So sánh được cách tính số connection DB tối đa của một hệ PHP-FPM và một hệ Spring Boot cùng quy mô

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Generics và Java hiện đại (17 → 25)

**Vì sao cần học:** Code Java 17+ khác hẳn Java 8 mà nhiều tài liệu cũ còn dạy. Người phỏng vấn
hay hỏi "tính năng X có từ bản nào", về `record`, `sealed`, pattern matching. Generics thì hay bị
hỏi qua type erasure và wildcard.

**Học gì**

*Generics và type erasure*
- *Generics*: `List<String>` báo cho compiler kiểu của phần tử, để bắt lỗi ngay lúc compile. PHP
  chỉ ghi được trong docblock (`@var array<string>`) cho PHPStan đọc.
- *Type erasure*: sau khi compile, thông tin kiểu generic bị xoá. Lúc chạy, `List<String>` và
  `List<Integer>` đều chỉ là `List`.
- Hệ quả:
  - Không viết được `new T()`.
  - Không viết được `x instanceof List<String>`.
  - Không tạo được mảng generic như `new T[10]`.
- *Raw type*: dùng `List` không kèm `<...>`. Chỉ còn để tương thích code cũ, và mất kiểm tra kiểu.

*Wildcard và PECS*
- ⚠️ `List<String>` **không** phải là `List<Object>`, dù `String` là `Object`. Nếu được, bạn có thể
  `add(123)` vào một list chuỗi.
- *Wildcard* nới lỏng quy tắc trên:
  - `List<? extends Number>`: list của một kiểu con nào đó của `Number`. Đọc ra được `Number`,
    nhưng không thêm vào được.
  - `List<? super Integer>`: list của `Integer` hoặc một kiểu cha. Thêm `Integer` vào được, nhưng
    đọc ra chỉ biết là `Object`.
- Quy tắc nhớ *PECS*: Producer Extends, Consumer Super. Nguồn để đọc dùng `extends`, đích để ghi
  dùng `super`.
  - Ví dụ: `Collections.copy(List<? super T> dest, List<? extends T> src)`.

*record*
- `record Point(int x, int y) {}` là class chỉ để chứa dữ liệu:
  - Immutable.
  - Tự sinh constructor, accessor `x()`, `y()`, cùng `equals`, `hashCode`, `toString`.
  - Gần giống class PHP có `readonly` kết hợp constructor promotion.
- ⚠️ Immutable chỉ ở mức nông: field là một `List` thì vẫn `add` được vào list đó.

*sealed và pattern matching*
- `sealed interface Payment permits Card, Momo, Cod {}`: chỉ các class được liệt kê mới được
  implement interface này.
- *Pattern matching cho `switch`* (Java 21): `switch` theo kiểu của object, và gán luôn vào biến:

  ```java
  long fee = switch (payment) {
      case Card c -> c.amount() / 50;
      case Momo m -> 1000;
      case Cod x  -> 0;
  };   // không cần default
  ```

  - Vì `Payment` là sealed, compiler biết chỉ có ba trường hợp và kiểm tra *exhaustive* (đủ mọi
    nhánh). Thêm loại thứ tư mà quên xử lý là lỗi compile.
  - Kiểu "một trong mấy dạng, mỗi dạng mang dữ liệu riêng" này gọi là *sum type*.

*Mốc tính năng cần nhớ*
- *LTS* (Long-Term Support): bản được hỗ trợ nhiều năm. Production thường chỉ chạy bản LTS.

  | Bản | Tính năng |
  |---|---|
  | 8 | lambda, Stream, `Optional`, `java.time` |
  | 10–16 | `var`, switch expression, text block, `record`, pattern `instanceof` |
  | 17 LTS | `sealed` |
  | 21 LTS | virtual thread, pattern matching cho `switch`, record pattern, sequenced collections, generational ZGC (tuỳ chọn) |
  | 24 | Stream Gatherers (final), virtual thread không còn pin trong `synchronized` |
  | 25 LTS | scoped values (final), flexible constructor bodies, compact source files và instance `main`, module import, compact object headers (tuỳ chọn) |
  | 26, 27 | không phải LTS; structured concurrency vẫn preview (lần 7 ở 27) |

- Bảng này dùng để tra mốc. Tên tính năng nào chưa quen thì tra JEP tương ứng ở mục Đọc.
- Các mục về thread và bộ nhớ trong bảng được giải thích ở chặng 3: virtual thread, pinning,
  scoped values, structured concurrency ở module 3.4; ZGC và compact object headers ở module 3.1.
- *Preview feature*: tính năng đã có trong JDK nhưng chưa chốt thiết kế.
  - ⚠️ Phải bật `--enable-preview`, API còn đổi giữa các bản, không dùng cho production.

**Đọc**
- Oracle tutorial: [Generics](https://docs.oracle.com/javase/tutorial/java/generics/index.html) (mục *Wildcards*, *Type Erasure*)
- JEP: [395 Records](https://openjdk.org/jeps/395), [409 Sealed Classes](https://openjdk.org/jeps/409), [440 Record Patterns](https://openjdk.org/jeps/440), [441 Pattern Matching for switch](https://openjdk.org/jeps/441), [485 Stream Gatherers](https://openjdk.org/jeps/485), [513 Flexible Constructor Bodies](https://openjdk.org/jeps/513), [512 Compact Source Files](https://openjdk.org/jeps/512)
- Danh sách JEP theo bản: [JDK 25](https://openjdk.org/projects/jdk/25/), [JDK 27](https://openjdk.org/projects/jdk/27/)

**Nắm chắc khi**
- [ ] Viết được `sealed interface Payment` với 3 record và một `switch` exhaustive không có `default`
- [ ] Giải thích được vì sao `List<Object>` không nhận `List<String>` nhưng `List<? extends Object>` thì nhận
- [ ] Trả lời được ngay "tính năng X final ở bản nào" cho virtual thread, scoped values, structured concurrency

#### 2.2 Collections bên trong

**Vì sao cần học:** "HashMap hoạt động thế nào" là câu mid kinh điển của phỏng vấn Java, và gần
như luôn bị hỏi tiếp sang `ConcurrentHashMap`. Đây cũng là nền để hiểu cache trong process, thứ
PHP-FPM không có.

**Học gì**

*HashMap: put một phần tử*
1. Tính `h = key.hashCode()`, rồi trộn `hash = h ^ (h >>> 16)`, tức đưa 16 bit cao xuống trộn với
   16 bit thấp.
2. Chọn bucket: `index = (n - 1) & hash`, với `n` là số bucket, luôn là luỹ thừa của 2. Khi `n` là
   luỹ thừa của 2, phép `&` này cho kết quả như phép chia lấy dư nhưng nhanh hơn.
3. Bucket trống thì đặt vào. Đã có phần tử thì so từng key bằng `equals`: trùng thì thay value,
   không trùng thì nối thêm vào bucket.

- Vì sao phải trộn bit cao: `& (n - 1)` chỉ lấy vài bit thấp. Không trộn thì các hash chỉ khác
  nhau ở bit cao sẽ dồn hết vào cùng một bucket.

*Resize*
- Mặc định có 16 bucket, *load factor* 0.75. Khi số phần tử vượt 16 × 0.75 = 12 thì bảng *resize*
  lên gấp đôi.
- Khi gấp đôi, mỗi phần tử hoặc ở nguyên index cũ, hoặc dịch thêm đúng `oldCap` (số bucket cũ),
  tuỳ vào một bit của hash. Không cần tính lại hash.

*Treeify*
- *Collision*: nhiều key rơi vào cùng bucket, bucket thành danh sách dài, tra mất O(n).
- Từ Java 8, khi một bucket có ≥ 8 phần tử **và** bảng có ≥ 64 bucket, bucket đó đổi thành cây
  đỏ-đen (tra O(log n)). Việc này gọi là *treeify*.
  - Bảng còn nhỏ hơn 64 bucket thì resize thay vì treeify.
  - Cây co còn dưới 6 phần tử thì đổi lại thành danh sách.
- ⚠️ `hashCode` trả về hằng số: mọi key dồn vào một bucket, hiệu năng sập.

*Các điểm khác của HashMap*
- Cho phép một key `null`.
- Không thread-safe: nhiều thread cùng ghi có thể làm hỏng cấu trúc bên trong.

*ConcurrentHashMap*
- Map an toàn khi nhiều thread cùng dùng, mà không khoá cả map:
  - Bucket rỗng: đặt phần tử bằng *CAS* (compare-and-swap), một lệnh CPU nghĩa là "ghi giá trị
    mới nếu giá trị hiện tại vẫn là X", không cần lock.
  - Bucket đã có phần tử: `synchronized` trên node đầu của bucket đó, tức chỉ khoá một bucket.
  - Đọc không lock.
- Không cho key hoặc value là `null`.
- `computeIfAbsent`, `merge` là atomic (cả thao tác chạy trọn vẹn, không bị thread khác chen vào).
  - ⚠️ Hàm bạn truyền vào chạy trong lúc đang giữ lock của bucket. Không làm việc lâu (gọi DB,
    HTTP) và không sửa chính map đó trong hàm này.
- ⚠️ Kiểm tra rồi mới làm vẫn race:

  ```java
  if (!map.containsKey(k)) map.put(k, load(k));   // hai thread cùng thấy chưa có, cùng put
  map.computeIfAbsent(k, this::load);             // atomic
  ```

*Các lựa chọn khác*
- `Collections.synchronizedMap`: một lock cho cả map, mọi thao tác xếp hàng chờ nhau.
- `CopyOnWriteArrayList`: mỗi lần ghi copy cả mảng. Hợp khi đọc rất nhiều, ghi rất ít.
- Cache trong production dùng thư viện Caffeine (có giới hạn kích thước, hết hạn, thống kê), không
  tự viết bằng `LinkedHashMap` cộng đồng bộ.

**Đọc**
- Source: [HashMap.java](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/HashMap.java) (đọc comment *Implementation notes* ở đầu class)
- Javadoc: [ConcurrentHashMap](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html)
- dev.java: [Collections Framework](https://dev.java/learn/api/collections-framework/)

**Nắm chắc khi**
- [ ] Vẽ được `HashMap` lúc resize từ 16 lên 32 và nói phần tử nào đổi chỗ
- [ ] Giải thích được vì sao `ConcurrentHashMap` cấm `null` còn `HashMap` thì không

#### 2.3 Concurrency trong Java

**Vì sao cần học:** Java chạy mọi request trong cùng một process nhiều thread, nên bug
concurrency là chuyện hằng ngày, khác hẳn PHP-FPM. Câu hỏi hay gặp: `volatile` để làm gì, cấu hình
thread pool thế nào, và vì sao `ThreadLocal` làm lộ dữ liệu giữa các request.

**Học gì**

*Visibility và Java Memory Model*
- Mỗi core CPU có cache riêng, và compiler được phép đổi thứ tự lệnh. Vì vậy thread A ghi một
  biến, thread B có thể **không bao giờ thấy** giá trị mới. Đây là vấn đề *visibility*.
- *Java Memory Model* (JMM) quy định khi nào một lần ghi chắc chắn được thread khác thấy, qua quan
  hệ *happens-before*: A happens-before B thì B thấy mọi thứ A đã ghi.
- Các cặp tạo ra happens-before:
  - Unlock một *monitor* → lần lock sau đó trên **cùng** monitor. Monitor là lock gắn với mỗi
    object, thứ mà `synchronized` dùng.
  - Ghi một biến `volatile` → lần đọc biến đó sau này.
  - Gọi `Thread.start()` → mọi thứ chạy trong thread mới.
  - Mọi thứ trong một thread → thread khác gọi `join()` chờ nó xong.
- ⚠️ *Double-checked locking* (kiểm tra null, lock, kiểm tra lại, rồi mới tạo object) cần field
  `volatile`. Thiếu nó, thread khác có thể thấy object mới tạo dở.
  - Cách đơn giản hơn: *holder class* (class static lồng bên trong, JVM đảm bảo chỉ khởi tạo một
    lần) hoặc dùng `enum`.

*synchronized, volatile, atomic*
- `synchronized`:
  - Loại trừ: chỉ một thread được chạy đoạn code đó một lúc.
  - Đảm bảo visibility.
  - *Reentrant*: thread đang giữ lock gọi vào lại được mà không tự chặn mình.
- `volatile`: chỉ đảm bảo visibility.
  - ⚠️ **Không** atomic: `count++` gồm ba bước đọc, cộng, ghi, nên hai thread vẫn đè nhau.
- `AtomicInteger`: `incrementAndGet()` là atomic nhờ CAS.
- `LongAdder`: nhanh hơn khi tranh chấp cao (nhiều thread cùng tăng một counter), vì chia counter
  thành nhiều ô rồi cộng lại khi đọc.

*Lock và công cụ phối hợp*
- `ReentrantLock`: như `synchronized` nhưng có thêm `tryLock` và timeout.
  - ⚠️ Luôn gọi `unlock()` trong `finally`.
- `ReadWriteLock`: nhiều thread đọc cùng lúc được, ghi thì độc quyền.
- `CountDownLatch`: chờ N việc xong rồi mới đi tiếp.
- `Semaphore`: cho tối đa N thread cùng làm một việc, ví dụ tối đa 10 lời gọi đồng thời tới đối tác.

*Thread pool*
- Tạo thread tốn kém, nên dùng *thread pool*: một nhóm thread dựng sẵn, lấy task từ một queue ra làm.
- `ThreadPoolExecutor(core, max, keepAlive, queue, factory, handler)`. Khi có task mới:
  1. Chưa đủ `core` thread thì tạo thread mới.
  2. Đủ `core` thì đưa task vào queue.
  3. ⚠️ Chỉ khi **queue đầy** mới tạo thêm thread, tới tối đa `max`.
  4. Đủ `max` và queue cũng đầy thì gọi `handler`, gọi là *rejection policy*.
- ⚠️ `Executors.newFixedThreadPool` dùng queue không giới hạn:
  - Bước 3 không bao giờ xảy ra.
  - Task dồn trong RAM tới `OutOfMemoryError`, còn latency tăng dần mà không báo lỗi gì.
- ⚠️ `Executors.newCachedThreadPool` tạo thread không giới hạn.
- Cấu hình cho production:
  - Queue có giới hạn.
  - Rejection policy rõ ràng. `CallerRunsPolicy` bắt chính thread gửi task tự chạy task đó, nên
    bên gửi chậm lại. Đẩy áp lực ngược về phía nguồn như vậy gọi là *backpressure*.
  - Đặt tên thread để dễ đọc thread dump (module 3.3).
- ⚠️ Task gửi bằng `submit()` mà ném exception thì exception bị giữ trong `Future` (đối tượng đại
  diện cho kết quả sẽ có). Không ai gọi `get()` thì lỗi mất không dấu vết.

*CompletableFuture*
- Giống Promise của JavaScript: chạy việc bất đồng bộ và nối tiếp các bước.
  - `thenApply`: biến đổi kết quả.
  - `thenCompose`: nối với một bước bất đồng bộ khác.
  - `thenCombine`: gộp hai kết quả.
  - `allOf`: chờ nhiều future.
  - `orTimeout`: đặt timeout.
- ⚠️ Không truyền executor thì chạy trên common pool dùng chung cả JVM (module 1.2).
- ⚠️ `allOf` không huỷ các future còn lại khi một cái lỗi.

*ThreadLocal*
- `ThreadLocal` là biến mà mỗi thread có một bản riêng. Spring dùng nó để giữ dữ liệu theo request.
- ⚠️ Thread trong pool được dùng lại cho request sau. Không `remove()` thì request sau đọc được
  giá trị của request trước, ví dụ user A thấy tenant của user B.

  ```java
  TENANT.set(tenantId);
  try { handle(request); } finally { TENANT.remove(); }
  ```

- ⚠️ MDC, `SecurityContext`, `RequestContextHolder` đều là `ThreadLocal`, nên bị mất khi công
  việc chuyển sang thread khác (`@Async`, `CompletableFuture`).

**Đọc**
- *Java Concurrency in Practice*: ch.3 (visibility), ch.8 (thread pool)
- [JSR-133 FAQ](https://www.cs.umd.edu/~pugh/java/memoryModel/jsr-133-faq.html): JMM ngắn gọn; nâng cao: [Shipilëv: JMM Pragmatics](https://shipilev.net/blog/2014/jmm-pragmatics/)
- Javadoc: [ThreadPoolExecutor](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/ThreadPoolExecutor.html) (mục *Queuing*, *Rejected tasks*)

**Nắm chắc khi**
- [ ] Giải thích được một đoạn code có cờ `running` không `volatile` có thể lặp mãi vì sao
- [ ] Cấu hình được một `ThreadPoolExecutor` cho việc gọi API đối tác, nói rõ lý do từng tham số
- [ ] Kể được kịch bản "user A thấy tenant của user B" do `ThreadLocal` và cách sửa

#### 2.4 Spring bên trong: lifecycle, proxy, transaction, async

**Vì sao cần học:** Phần lớn bug kiểu "Spring không làm như annotation nói" (transaction không
rollback, `@Async` vẫn chạy đồng bộ, cache không có tác dụng) đều bắt nguồn từ proxy. Đây là nhóm
câu hỏi về Spring phổ biến nhất ở vòng mid và senior.

**Học gì**

*Bean lifecycle*
1. Gọi constructor.
2. Inject các dependency còn lại (qua setter, field).
3. Gọi các interface `*Aware` (ví dụ `ApplicationContextAware`) để bean nhận tham chiếu tới
   container.
4. `BeanPostProcessor.before...`: móc (*hook*) cho framework can thiệp vào bean.
5. `@PostConstruct`: code khởi tạo của bạn.
6. `BeanPostProcessor.after...`: **proxy AOP được tạo ở bước này**, và từ đây bean thật bị thay
   bằng proxy.
7. App chạy.
8. `@PreDestroy` khi app tắt.

*Scope*
- *Scope* quyết định một bean có bao nhiêu object:
  - `singleton` (mặc định): một object cho cả app.
  - `prototype`: mỗi lần xin là một object mới.
  - `request`, `session`: một object cho mỗi request hoặc mỗi session HTTP.
- ⚠️ Inject bean prototype vào bean singleton: chỉ inject **một lần** lúc tạo singleton, nên thực
  chất vẫn chỉ dùng một object. Muốn mỗi lần một object mới thì inject `ObjectProvider<T>` và gọi
  `getObject()`.

*AOP proxy*
- *AOP* (Aspect-Oriented Programming): gắn thêm hành vi (mở transaction, cache, chạy async) quanh
  method mà không sửa code của method.
- Spring làm việc này bằng *proxy*: một object đứng trước bean thật, nhận lời gọi, làm phần việc
  thêm, rồi chuyển vào bean thật. Có hai cách tạo proxy:
  - JDK dynamic proxy: implement cùng interface với bean.
  - CGLIB: sinh lúc runtime một class con của class bean. Boot mặc định dùng CGLIB.
- ⚠️ *Self-invocation*: method trong bean gọi một method khác của chính nó.

  ```java
  public void a() { this.b(); }        // this là object thật, lời gọi không đi qua proxy
  @Transactional public void b() {}    // nên @Transactional ở đây không có tác dụng
  ```

  - Áp dụng cho mọi annotation dựa trên proxy: `@Transactional`, `@Async`, `@Cacheable`.
- ⚠️ Method `final` hoặc `private` không proxy được, vì class con không override được chúng.

*@Transactional: propagation*
- *Propagation* quy định chuyện gì xảy ra khi method có `@Transactional` được gọi trong lúc đã có
  sẵn một transaction.

  | Propagation | Hành vi |
  |---|---|
  | `REQUIRED` (mặc định) | Có sẵn thì tham gia, chưa có thì tạo mới |
  | `REQUIRES_NEW` | Luôn tạo transaction mới trên connection mới, tạm treo transaction bên ngoài |
  | `NESTED` | Tạo *savepoint* (điểm đánh dấu) trong transaction hiện tại, rollback được riêng phần này |
  | `SUPPORTS` | Có thì tham gia, không có thì chạy không transaction |
  | `NOT_SUPPORTED` | Luôn chạy không transaction, treo transaction đang có |
  | `MANDATORY` | Bắt buộc phải có sẵn transaction, không có thì lỗi |
  | `NEVER` | Bắt buộc không có transaction, có thì lỗi |

- ⚠️ `REQUIRES_NEW` giữ hai connection cùng lúc: một của transaction ngoài đang treo, một của
  transaction mới. Tải cao dễ cạn pool: mọi thread đều giữ một connection và chờ thêm cái thứ hai.

*@Transactional: rollback và các bẫy*
- ⚠️ Mặc định chỉ rollback với `RuntimeException` và `Error`. Checked exception (ví dụ
  `IOException`) thì transaction vẫn **commit**.
  - Người từ Laravel rất hay dính, vì `DB::transaction` rollback với mọi exception.
- ⚠️ `UnexpectedRollbackException` xảy ra theo chuỗi:
  1. Method ngoài và method trong đều `REQUIRED`, nên dùng chung một transaction.
  2. Method trong ném exception. Spring đánh dấu transaction là *rollback-only*.
  3. Method ngoài bắt exception đó, chạy tiếp, và tới cuối định commit.
  4. Spring thấy cờ rollback-only, nên rollback rồi ném `UnexpectedRollbackException`.
- `readOnly = true`: chỉ là gợi ý để tối ưu (ví dụ route sang replica). Không phải cơ chế bảo mật
  chặn ghi.
- ⚠️ Gọi HTTP ra ngoài trong transaction giữ connection DB suốt thời gian chờ.

*@Async*
- Chạy method trên thread khác, caller không chờ. Giống `dispatch()` một job, nhưng chạy ngay
  trong process, không qua queue bền vững nào.
- Cần `@EnableAsync`. Dính cùng bẫy self-invocation như trên.
- Executor mặc định (executor là thứ quản lý thread chạy task):
  - Boot tự tạo bean `applicationTaskExecutor` kiểu `ThreadPoolTaskExecutor`: 8 core thread,
    queue không giới hạn theo mặc định.
  - Khi `spring.threads.virtual.enabled=true` thì là `SimpleAsyncTaskExecutor` dùng virtual thread.
- ⚠️ Method `void` async ném exception thì caller không bao giờ biết. Cần đăng ký
  `AsyncUncaughtExceptionHandler`.
- Boot 4.1 thêm việc tự lan truyền context (MDC, tracing) cho `@Async`. Bản cũ hơn phải tự cấu hình
  `TaskDecorator` để copy context sang thread mới.

*Resilience trong core (Spring Framework 7)*
- `@Retryable`: tự thử lại method khi nó ném exception.
- `@ConcurrencyLimit`: giới hạn số lời gọi đồng thời vào method.
- Hai annotation này nằm trong package `org.springframework.resilience.annotation`, bật bằng
  `@EnableResilientMethods`.
- `RetryTemplate`: bản dùng trong code thường, không qua annotation.
- Trước bản 7 phải dùng thư viện Spring Retry hoặc Resilience4j.

**Đọc**
- Spring: [Customizing the Nature of a Bean](https://docs.spring.io/spring-framework/reference/core/beans/factory-nature.html), [Proxying Mechanisms](https://docs.spring.io/spring-framework/reference/core/aop/proxying.html) (mục *Understanding AOP Proxies*, có ví dụ self-invocation)
- Transaction: [Declarative Transaction Management](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html), [Propagation](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/tx-propagation.html), [Rolling Back](https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative/rolling-back.html), [Transaction-bound Events](https://docs.spring.io/spring-framework/reference/data-access/transaction/event.html)
- Boot: [Task Execution and Scheduling](https://docs.spring.io/spring-boot/reference/features/task-execution-and-scheduling.html)
- Spring: [Resilience Features](https://docs.spring.io/spring-framework/reference/core/resilience.html)

**Nắm chắc khi**
- [ ] Vẽ được luồng gọi controller → proxy → `a()` → `this.b()` và chỉ ra transaction nào thực sự tồn tại (bài tập 3)
- [ ] Liệt kê được 3 nguyên nhân `@Transactional` "không rollback" và cách xác minh từng cái
- [ ] Nói được executor nào chạy method `@Async` trong app Boot của mình, và điều gì xảy ra khi queue của nó đầy

#### 2.5 JPA/Hibernate

**Vì sao cần học:** JPA/Hibernate là tầng DB mặc định của Spring, giống vị trí của Eloquent, nhưng
có nhiều hành vi ngầm hơn. Phần lớn sự cố hiệu năng của app Spring nằm ở đây: N+1, batch chậm dần,
giữ connection quá lâu.

**Học gì**

*Persistence context*
- *JPA* là đặc tả chuẩn (bộ interface), Hibernate là implementation phổ biến nhất.
- *Entity* là class map với một bảng.
- *Persistence context* là vùng nhớ mà Hibernate giữ các entity đã load trong một transaction. Nó
  đóng hai vai:
  - *First-level cache*: tìm cùng một id lần thứ hai không query lại.
  - *Identity map*: mỗi dòng trong DB chỉ có đúng một object trong context.
- Bốn trạng thái của entity:
  - *Transient*: vừa `new`, Hibernate chưa biết tới.
  - *Managed*: đang nằm trong persistence context, mọi thay đổi được theo dõi.
  - *Detached*: context đã đóng, object vẫn còn nhưng không được theo dõi nữa.
  - *Removed*: đã đánh dấu xoá, sẽ sinh `DELETE` khi flush.

*Dirty checking và flush*
- *Flush* là lúc Hibernate đẩy các thay đổi xuống DB. Xảy ra khi:
  - Commit.
  - Trước khi chạy một query có liên quan tới dữ liệu đã sửa.
  - Bạn gọi `flush()`.
- Lúc flush, Hibernate so từng entity managed với bản chụp lúc load. Cái nào khác thì tự sinh
  `UPDATE`. Cơ chế này gọi là *dirty checking*.

*Batch lớn*
- ⚠️ Load hoặc insert hàng chục nghìn entity trong một transaction:
  - Context giữ tất cả trong RAM, nên RAM tăng dần.
  - Mỗi lần flush phải so từng entity, nên chạy chậm dần.
- Cách sửa:
  - Cứ mỗi lô (ví dụ 500 entity) gọi `flush()` rồi `clear()` để xả context.
  - Bật `hibernate.jdbc.batch_size` để gộp nhiều câu `INSERT` vào một lần gửi.
- ⚠️ `GenerationType.IDENTITY` (id do auto-increment của DB cấp) chặn batch insert, vì Hibernate
  phải insert từng dòng một để lấy id ngay.
- ⚠️ `save()` của Spring Data với entity đã có id sẽ gọi `merge`, và có thể chạy thêm một `SELECT`
  trước mỗi lần lưu.

*Fetch và N+1*
- *Fetch type* quy định quan hệ được load ngay (*EAGER*) hay chỉ khi truy cập tới (*LAZY*).
- Mặc định:
  - `@OneToMany`, `@ManyToMany`: LAZY.
  - ⚠️ `@ManyToOne`, `@OneToOne`: **EAGER**. Mỗi lần load `Order` là kéo theo `Customer`.
  - Nên đặt tất cả thành LAZY, rồi chủ động fetch ở từng query.
- *N+1*: 1 query lấy N đơn hàng, rồi thêm N query lấy customer của từng đơn. Giống lặp
  `$order->customer` mà quên `with('customer')` trong Eloquent.
- Cách sửa:
  - `JOIN FETCH` trong JPQL (ngôn ngữ query của JPA): `select o from Order o join fetch o.customer`.
  - `@EntityGraph` trên method của repository.
  - `@BatchSize` hoặc `default_batch_fetch_size`: gom thành một query `WHERE id IN (...)`, gần
    giống cách `with()` của Eloquent làm.
  - *DTO projection*: query thẳng vào một class chỉ chứa đúng các cột cần.
- ⚠️ `JOIN FETCH` một collection kèm phân trang: join làm nhân dòng nên không `LIMIT` được ở SQL.
  Hibernate kéo **hết** về rồi phân trang trong RAM.
- ⚠️ Fetch hai collection kiểu `List` cùng lúc ném `MultipleBagFetchException`.

*Lazy loading và open-in-view*
- `LazyInitializationException`: truy cập quan hệ LAZY khi persistence context đã đóng, ví dụ ở
  controller sau khi service đã trả về.
- ⚠️ `spring.jpa.open-in-view` mặc định **bật** (Boot in cảnh báo lúc khởi động): giữ context mở
  tới hết request, nên lỗi trên không xảy ra.
  - Cái giá: giữ connection DB tới hết request.
  - Lazy load ngầm, tức N+1, xảy ra cả lúc render JSON.

*Entity ra JSON*
- ⚠️ Serialize entity thẳng ra JSON:
  - Quan hệ hai chiều (`Order` → `Customer` → danh sách `orders`) gây vòng lặp vô hạn.
  - Serializer chạm vào quan hệ LAZY, kích hoạt query ngầm.
  - Nên trả DTO, giống API Resource của Laravel.
- ⚠️ Không dùng `@Data` của Lombok (thư viện tự sinh getter, setter, `equals`...) trên entity. Các
  method sinh ra chạm vào mọi field, kể cả quan hệ LAZY.

*Locking và pool*
- `@Version`: optimistic lock bằng cột version.
- `@Lock(PESSIMISTIC_WRITE)`: sinh `SELECT ... FOR UPDATE`.
- Chọn loại nào: [03-database-sql.md](03-database-sql.md).
- HikariCP: pool nhỏ thường nhanh hơn pool to, vì thêm connection chỉ thêm tranh chấp bên trong DB.

**Đọc**
- Hibernate User Guide: chương *Persistence Contexts*, *Fetching*, *Batching*, *Locking*
- Boot: [Open EntityManager in View](https://docs.spring.io/spring-boot/reference/data/sql.html#data.sql.jpa-and-spring-data.open-entity-manager-in-view)
- Spring Data JPA: [Query Methods](https://docs.spring.io/spring-data/jpa/reference/jpa/query-methods.html) (mục projection, entity graph)
- Vlad Mihalcea: [N+1 query problem](https://vladmihalcea.com/n-plus-1-query-problem/), [The Open Session in View Anti-Pattern](https://vladmihalcea.com/the-open-session-in-view-anti-pattern/)
- HikariCP: [About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)

**Nắm chắc khi**
- [ ] Viết được query lấy 20 đơn mới nhất kèm customer và items, không N+1, không phân trang trong RAM (bài tập 4)
- [ ] Giải thích được vì sao batch import 1 triệu dòng bằng JPA chậm dần và RAM tăng, nêu 3 cách sửa
- [ ] Đối chiếu được dirty checking của Hibernate với `save()` tường minh và `$model->isDirty()` của Eloquent

#### 2.6 Web: MVC, WebFlux, Security, API versioning

**Vì sao cần học:** Chọn Spring MVC hay WebFlux và hiểu filter chain của Spring Security là câu
hỏi hay gặp khi JD có Spring. Spring Security phức tạp hơn middleware của Laravel nhiều, và người
mới thường cấu hình theo mẫu mà không hiểu request đi qua những đâu.

**Học gì**

*MVC và WebFlux*

| | Spring MVC | WebFlux |
|---|---|---|
| Mô hình | *Thread-per-request*: mỗi request giữ một thread tới khi xong | *Event loop*: vài thread xử lý mọi request, và không bao giờ được đứng chờ |
| Cách viết code | Blocking, tuần tự như PHP | Reactive: `Mono` (0 hoặc 1 giá trị sẽ có), `Flux` (nhiều giá trị) |
| Điều kiện | Không có | Cả chuỗi phải non-blocking, từ driver DB tới HTTP client |

- ⚠️ Gọi JDBC (blocking) trên event loop: vài thread event loop bị kẹt chờ DB, cả app đứng,
  throughput sập.
- Virtual thread kết hợp MVC giải được phần lớn bài toán "nhiều request cùng chờ I/O" mà vẫn giữ
  kiểu code blocking quen thuộc (module 3.4).

*Spring Security: filter chain*
- *Filter* là lớp chặn request trước khi tới controller, vai trò như middleware của Laravel.
- Đường đi của một request:
  1. Servlet container (Tomcat) gọi `DelegatingFilterProxy`, cầu nối từ container sang bean của Spring.
  2. Nó chuyển request cho `FilterChainProxy`.
  3. `FilterChainProxy` chọn **một** `SecurityFilterChain` khớp với request, theo *request matcher*
     (ví dụ `/api/**`). Một app có thể có nhiều chain cho các nhóm URL khác nhau.
  4. Chain đó là một danh sách filter có thứ tự: đọc token, xác thực, kiểm tra quyền...
  5. Qua hết filter thì tới controller.
- `SecurityContextHolder`: nơi giữ user đã xác thực của request hiện tại, dựa trên `ThreadLocal`
  (module 2.3).
- Xác thực: `AuthenticationManager` giao việc cho các `AuthenticationProvider`, mỗi provider lo
  một kiểu (password, JWT...).
- Phân quyền:
  - Theo request (URL), khai trong cấu hình chain.
  - Theo method, bằng `@PreAuthorize("hasRole('ADMIN')")`. Gần giống Gate/Policy của Laravel.

*JWT resource server*
- *Resource server*: API nhận access token do một auth server khác cấp.
- Cấu hình bằng `oauth2ResourceServer().jwt()`, cùng `issuer-uri` hoặc `jwk-set-uri` (nơi lấy
  public key để kiểm tra chữ ký).
- Với mỗi request, Spring:
  1. Kiểm tra chữ ký của token.
  2. Kiểm tra `exp` (hết hạn chưa), `iss` (ai cấp), `aud` (cấp cho ai).
  3. Map claim trong token sang *authority*, tức quyền theo cách Spring hiểu.
- ⚠️ *CSRF* là kiểu tấn công lợi dụng cookie mà trình duyệt tự gửi kèm. Tắt chống CSRF chỉ hợp lý
  với API stateless không dùng cookie. Chi tiết JWT, CORS: [10-security.md](10-security.md).

*API versioning*
- Spring Framework 7 có sẵn:
  - Thuộc tính `version` trên `@RequestMapping`.
  - Cấu hình lấy version từ header, path, query hoặc media type.
  - Boot 4 có nhóm property `spring.mvc.apiversion.*`.
- Thiết kế versioning: [09-api-design.md](09-api-design.md).

**Đọc**
- Spring: [Spring Web MVC](https://docs.spring.io/spring-framework/reference/web/webmvc.html), [WebFlux](https://docs.spring.io/spring-framework/reference/web/webflux.html) (mục *Overview*, *Concurrency Model*), [API Versioning](https://docs.spring.io/spring-framework/reference/web/webmvc-versioning.html)
- Spring Security: [Servlet Architecture](https://docs.spring.io/spring-security/reference/servlet/architecture.html), [OAuth 2.0 Resource Server JWT](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)

**Nắm chắc khi**
- [ ] Vẽ được đường đi của một request có Bearer token qua filter chain tới controller
- [ ] Nói được khi nào chọn WebFlux thay vì MVC + virtual thread, và khi nào không
- [ ] Đối chiếu được Spring Security filter chain với middleware stack và guard của Laravel

#### 2.7 Testing trong Spring

**Vì sao cần học:** Suite test chậm dần và test xanh mà production vẫn lỗi là hai than phiền phổ
biến nhất về test trong Spring. Người phỏng vấn muốn biết bạn chọn đúng loại test, và biết những
bẫy làm test "nói dối".

**Học gì**

*Các loại test*

| Loại | Khởi động gì | Dùng cho |
|---|---|---|
| Unit (JUnit + Mockito) | Không có container | Logic trong service |
| `@WebMvcTest` | Chỉ tầng web | Controller: routing, validate, JSON |
| `@DataJpaTest` | Chỉ tầng JPA, rollback sau mỗi test | Repository, query |
| `@SpringBootTest` | Cả application context | Luồng đầy đủ |

- *Test slice* là các annotation như `@WebMvcTest`, `@DataJpaTest`: chỉ nạp một phần app nên nhanh
  hơn nạp toàn bộ.
- Mockito là thư viện tạo *mock* (object giả thay cho dependency thật), vai trò như Mockery trong PHP.

*Context caching*
- Spring giữ lại application context giữa các test để khỏi khởi động lại.
- ⚠️ Mỗi tổ hợp cấu hình khác nhau tạo một context mới: bộ `@MockitoBean` khác nhau, profile khác
  nhau... Càng nhiều tổ hợp thì suite càng chậm.
  - `@MockitoBean` thay một bean trong context bằng mock.

*DB thật với Testcontainers*
- *Testcontainers*: thư viện bật DB, Redis, Kafka thật trong Docker để test chạy trên đó.
- Boot 3.1+ có `@ServiceConnection`: tự nối cấu hình connection tới container.
- ⚠️ Dùng H2 (DB chạy trong RAM) thay cho MySQL che mất lỗi SQL và lỗi lock, vì dialect, lock và
  isolation khác production.

*Bẫy @Transactional trên test*
- ⚠️ Test có `@Transactional` sẽ rollback sau khi chạy, tức không bao giờ commit:
  - Che `LazyInitializationException`, vì persistence context còn mở suốt test.
  - Không bắt được bug xảy ra sau commit (ví dụ listener `AFTER_COMMIT`).

*Benchmark*
- Micro-benchmark dùng JMH. JMH lo phần warm-up của JIT (module 3.2) và chống *dead-code
  elimination*, tức JIT xoá code có kết quả không ai dùng, làm số đo đẹp giả.
- Nguyên lý test chung: [20-testing-quality.md](20-testing-quality.md).

**Đọc**
- Boot: [Testing](https://docs.spring.io/spring-boot/reference/testing/index.html), [Testing Spring Boot Applications](https://docs.spring.io/spring-boot/reference/testing/spring-boot-applications.html) (mục *Auto-configured Tests*), [Testcontainers](https://docs.spring.io/spring-boot/reference/testing/testcontainers.html)
- Spring: [TestContext Framework](https://docs.spring.io/spring-framework/reference/testing/testcontext-framework.html) (mục *Context Caching*)
- [Testcontainers for Java](https://java.testcontainers.org/), [JMH](https://github.com/openjdk/jmh)

**Nắm chắc khi**
- [ ] Chọn được đúng loại test (unit, slice, full + Testcontainers) cho controller, repository có query native, và luồng đặt hàng
- [ ] Giải thích được vì sao test `@DataJpaTest` xanh nhưng production vẫn ném `LazyInitializationException`

---

### Chặng 3: Senior 🔴

#### 3.1 Bộ nhớ JVM và GC

**Vì sao cần học:** Service Java bị kill vì RAM, hoặc p99 nhảy vọt vì GC, là sự cố production phổ
biến. PHP-FPM gần như không có vấn đề này vì worker chết là trả hết RAM. JVM thì sống lâu và tự
quản lý bộ nhớ, nên senior Java phải đọc được GC.

**Học gì**

*Vùng nhớ của JVM*
- *Heap*: nơi chứa object. Kích thước tối đa đặt bằng `-Xmx`. Heap chia hai thế hệ:
  - Young: gồm Eden (object mới tạo) và hai vùng survivor S0, S1.
  - Old: object đã sống sót qua nhiều lần GC.
- Ngoài heap (*non-heap*):
  - Metaspace: thông tin về các class.
  - Stack của từng thread.
  - Code cache: mã máy do JIT sinh ra (module 3.2).
  - Direct buffer: bộ nhớ mà NIO hoặc Netty cấp bên ngoài heap.
- ⚠️ Vì vậy RAM của process luôn lớn hơn `-Xmx`.

*GC cơ bản*
- *GC* (garbage collector): tự tìm object không còn ai tham chiếu tới và thu hồi bộ nhớ.
- *Giả thuyết thế hệ*: đa số object chết rất trẻ, ví dụ object tạo ra trong một request. Vì vậy GC
  dọn vùng young thường xuyên với chi phí rẻ, và ít khi phải đụng tới old.
- *Stop-the-world* (STW): khoảng thời gian GC dừng mọi thread của app. Pause dài thì p99 tăng.

*Các collector*

| Collector | Đặc điểm | Hợp khi |
|---|---|---|
| Serial | Một thread GC, dừng app trong lúc dọn | Heap nhỏ |
| Parallel | Nhiều thread GC, tối ưu throughput | Batch, không quan tâm pause |
| **G1** (mặc định) | Chia heap thành nhiều *region*, cố giữ pause dưới `MaxGCPauseMillis` | Đa số service |
| **ZGC** | Làm gần hết việc song song với app, pause dưới 1 ms | Heap lớn, cần latency thấp |
| Shenandoah | Cùng hướng với ZGC; bản generational có từ JDK 25 | Như ZGC |

- ZGC: bản generational mặc định từ JDK 23, bản non-generational bị bỏ ở JDK 24.
- ⚠️ Trước JDK 27, JVM tự chọn Serial thay vì G1 khi máy hoặc container nhỏ (dưới 2 CPU hoặc dưới
  khoảng 1792 MB). Service trong container nhỏ chạy Serial mà không ai biết. JDK 27 chọn G1 ở mọi
  môi trường.
- *Compact object headers*: mỗi object có một phần *header* (thông tin JVM dùng nội bộ) đứng trước
  dữ liệu. Tính năng này thu header từ 12 xuống 8 byte, nên heap nhỏ đi.
  - Tuỳ chọn ở JDK 25 (`-XX:+UseCompactObjectHeaders`), mặc định từ JDK 27.

*Tuning*
- Đặt `-Xms` bằng `-Xmx` để cấp đủ heap ngay từ đầu.
- Bật GC log bằng `-Xlog:gc*`.
- ⚠️ Giảm allocation (lượng object tạo ra, đo bằng JFR ở module 3.3) trước khi chỉnh flag.
- Dấu hiệu leak: dung lượng vùng old sau mỗi lần *full GC* (GC dọn cả heap) tăng dần.

**Đọc**
- Oracle: [HotSpot GC Tuning Guide (JDK 25)](https://docs.oracle.com/en/java/javase/25/gctuning/) (đọc *Ergonomics*, *Garbage-First Garbage Collector*, *The Z Garbage Collector*)
- JEP: [474 ZGC generational mặc định](https://openjdk.org/jeps/474), [490 bỏ non-generational ZGC](https://openjdk.org/jeps/490), [519 Compact Object Headers](https://openjdk.org/jeps/519), [534 Compact Object Headers by Default](https://openjdk.org/jeps/534), [523 G1 mặc định mọi môi trường](https://openjdk.org/jeps/523)

**Nắm chắc khi**
- [ ] Đọc được một đoạn GC log G1 và chỉ ra pause dài nhất, loại GC gây ra nó
- [ ] Giải thích được khi nào đổi G1 sang ZGC và cái giá (CPU, footprint)
- [ ] Nói được vì sao service trong container 1 CPU trên JDK 21 lại chạy Serial GC

#### 3.2 JIT, class loading, khởi động

**Vì sao cần học:** Pod Java mới scale lên thường chậm trong vài phút đầu, làm autoscaling kém tác
dụng đúng lúc cần nhất. JIT và class loading giải thích vì sao, và các giải pháp mới (AOT cache,
native image) là chủ đề hay được hỏi khi bàn chuyện chạy Java trên Kubernetes.

**Học gì**

*JIT*
- Java được biên dịch ra *bytecode*, chưa phải mã máy. Lúc chạy, JVM:
  1. Thông dịch bytecode bằng *interpreter*. Chậm.
  2. Method được gọi nhiều thì *C1* biên dịch nhanh ra mã máy.
  3. Method rất nóng thì *C2* biên dịch lại, tối ưu mạnh:
     - *Inlining*: chép thân hàm nhỏ vào chỗ gọi.
     - *Escape analysis*: object không thoát ra khỏi method thì không cần cấp trên heap.
- C2 tối ưu dựa trên giả định rút ra từ lúc chạy. Giả định sai (ví dụ xuất hiện một kiểu mới) thì
  JVM bỏ bản đã tối ưu và quay lại thông dịch. Việc này gọi là *deoptimization*.
- *Warm-up*: vài phút đầu code chưa được JIT nên chậm. Ảnh hưởng autoscaling và làm benchmark đo sai.

*Class loading*
- Class được nạp qua các tầng *classloader*: bootstrap (lõi JDK) → platform → application (code và
  thư viện của bạn).
- *Parent delegation*: classloader hỏi tầng cha trước, cha không có mới tự nạp.
- Ba bước:
  1. Loading: đọc bytecode.
  2. Linking: kiểm tra và chuẩn bị.
  3. Initialization: chạy các khối `static`. Bước này *lười*, chỉ xảy ra khi class được dùng lần đầu.
- ⚠️ Leak classloader:
  1. App được *hot reload* (nạp lại code mà không tắt JVM).
  2. Một thread hoặc `ThreadLocal` còn giữ class của bản cũ.
  3. Cả classloader cũ và mọi class của nó không được thu hồi.
  4. Lặp lại vài lần là `OutOfMemoryError: Metaspace`.

*Giảm thời gian khởi động và warm-up*
- *CDS/AppCDS* (Class Data Sharing): lưu các class đã xử lý vào file để lần sau nạp nhanh hơn.
- AOT cache của Project Leyden:
  - JEP 483 (JDK 24): nạp và link class trước.
  - JEP 514 (JDK 25): `-XX:AOTCacheOutput` gộp việc tạo cache thành một bước.
  - JEP 515 (JDK 25): lưu profile method để JIT tối ưu sớm hơn.
- GraalVM native image: biên dịch trước cả app thành một binary.
  - Được: khởi động nhanh, RAM thấp.
  - Mất: build lâu, hạn chế reflection, không có JIT lúc runtime.

*Đối chiếu PHP*
- OPcache và preload giải bài "biên dịch lại mỗi request".
- JVM thì giải bài "chưa tối ưu lúc mới chạy".

**Đọc**
- JEP: [483 AOT Class Loading & Linking](https://openjdk.org/jeps/483), [514 AOT Command-Line Ergonomics](https://openjdk.org/jeps/514), [515 AOT Method Profiling](https://openjdk.org/jeps/515)
- Boot: [GraalVM Native Images](https://docs.spring.io/spring-boot/reference/packaging/native-image/index.html) (mục *Key Differences with JVM Deployments*)

**Nắm chắc khi**
- [ ] Giải thích được vì sao pod Java mới scale lên có p99 cao trong vài phút đầu và 3 cách giảm
- [ ] So sánh được AOT cache với native image theo khởi động, throughput, độ phức tạp build

#### 3.3 Chẩn đoán production và JVM trong container

**Vì sao cần học:** Câu hỏi senior Java hay đi từ sự cố: "API treo mà CPU thấp", "pod restart với
exit 137". Bạn cần biết lấy bằng chứng gì và đọc nó thế nào, thay vì đoán rồi tăng RAM.

**Học gì**

*Thread dump*
- *Thread dump* là ảnh chụp mọi thread đang làm gì, dưới dạng stack trace. Lấy bằng
  `jcmd <pid> Thread.print`.
- Lấy 3 lần, cách nhau vài giây. Thread đứng yên một chỗ qua cả 3 lần là đang kẹt.
- Tìm:
  - Thread ở trạng thái `BLOCKED`: đang chờ lock.
  - Nhiều thread cùng chờ lấy connection từ pool.
  - Deadlock.

*Heap dump*
- *Heap dump* là ảnh chụp mọi object trong heap. Lấy bằng `jcmd <pid> GC.heap_dump`, hoặc tự động
  khi OOM với `-XX:+HeapDumpOnOutOfMemoryError`. Phân tích bằng Eclipse MAT.
- ⚠️ Lúc dump, JVM bị dừng. File dump chứa dữ liệu nhạy cảm (token, dữ liệu user).

*Profiler*
- *JFR* (JDK Flight Recorder): ghi sự kiện CPU, allocation, lock, GC. Overhead thấp, bật được trên
  production.
- async-profiler: lấy mẫu CPU và allocation, vẽ *flame graph* (biểu đồ cho thấy hàm nào chiếm bao
  nhiêu thời gian).

*Các loại OutOfMemoryError*

| Thông báo | Nguyên nhân thường gặp |
|---|---|
| `Java heap space` | Leak (cache không giới hạn, collection static), nạp dữ liệu quá lớn |
| `GC overhead limit exceeded` | GC chạy gần hết thời gian mà thu hồi rất ít |
| `Metaspace` | Sinh class động quá nhiều, leak classloader |
| `unable to create native thread` | Quá nhiều thread, giới hạn pid/`ulimit` |
| `Direct buffer memory` | NIO/Netty vượt `MaxDirectMemorySize` |

*JVM trong container*
- JDK 10+ đọc giới hạn *cgroup*, tức giới hạn RAM và CPU mà container được cấp.
- Heap mặc định bằng 25% RAM container (`MaxRAMPercentage`). Container 2 GB chỉ có khoảng 512 MB
  heap. Thường đặt 50–75%.
- ⚠️ Heap cộng non-heap vượt limit thì kernel giết process (*OOMKilled*, exit code 137):
  - Không có `OutOfMemoryError`, không có heap dump.
  - Đo non-heap bằng *Native Memory Tracking*: `-XX:NativeMemoryTracking=summary`.
- CPU limit ảnh hưởng số thread GC, kích thước common pool và việc JVM chọn GC nào (module 3.1).
  Chi tiết Kubernetes: [19-devops-cloud.md](19-devops-cloud.md).

**Đọc**
- Oracle: [Troubleshooting Guide (JDK 25)](https://docs.oracle.com/en/java/javase/25/troubleshoot/) (chương *Diagnostic Tools*, *Troubleshoot Memory Leaks*)
- dev.java: [JDK Flight Recorder](https://dev.java/learn/jvm/jfr/)
- [async-profiler](https://github.com/async-profiler/async-profiler), [Eclipse MAT](https://eclipse.dev/mat/)

**Nắm chắc khi**
- [ ] Từ 3 thread dump, chỉ ra được pool nào đang kẹt và kẹt ở đâu
- [ ] Phân biệt được `OutOfMemoryError` với OOMKilled bằng bằng chứng (exit code, log, event k8s)
- [ ] Tính được cấu hình heap cho container 2 GB có 200 thread, nêu rõ giả định (bài tập 5)

#### 3.4 Virtual thread, structured concurrency, scoped values

**Vì sao cần học:** Virtual thread là thay đổi lớn nhất về concurrency của Java trong nhiều năm,
và là lý do nhiều team quay lại code blocking thay vì WebFlux. Câu "có nên bật không" kiểm tra bạn
hiểu giới hạn của nó, không chỉ biết tên.

**Học gì**

*Virtual thread là gì*
- Thread thường (*platform thread*) ứng với một OS thread, tốn tài nguyên nên chỉ tạo được vài nghìn.
- *Virtual thread* (final ở Java 21): thread nhẹ do JVM quản lý, tạo được hàng triệu.
- JVM chạy virtual thread trên vài *carrier thread* (OS thread thật):
  1. Virtual thread chạy trên một carrier.
  2. Gặp I/O blocking (chờ DB, chờ HTTP), JVM tháo nó khỏi carrier (*unmount*).
  3. Carrier rảnh, chạy virtual thread khác.
  4. I/O xong, virtual thread được gắn lại vào một carrier và chạy tiếp.
- Chỉ có lợi cho việc *I/O-bound* (phần lớn thời gian là chờ). Việc *CPU-bound* (tính toán nặng)
  không nhanh hơn.
- Đối chiếu:
  - Goroutine của Go cùng ý tưởng ([07-go.md](07-go.md)).
  - Fiber của PHP chỉ là *coroutine* (hàm tạm dừng rồi chạy tiếp được), không có sẵn bộ lập lịch
    tự chuyển khi chờ I/O.

*Pinning*
- *Pinning*: virtual thread bị dính vào carrier, chờ I/O mà không unmount được, nên chiếm luôn carrier.
- JDK 21–23: block bên trong `synchronized` gây pinning. JDK 24 (JEP 491) đã sửa.
- Native call/JNI (gọi code C) vẫn pin.
- Trên JDK 21: dùng `ReentrantLock` quanh đoạn có I/O, hoặc nâng JDK.

*Bẫy khi dùng*
- ⚠️ Không pool virtual thread. Mỗi task một virtual thread mới, tạo bằng
  `Executors.newVirtualThreadPerTaskExecutor()`.
- ⚠️ `ThreadLocal` chứa dữ liệu nặng nhân với hàng triệu thread thì tốn rất nhiều RAM.
- ⚠️ Phải giới hạn tải xuống downstream (DB, API đối tác) bằng `Semaphore`, pool connection hoặc
  `@ConcurrencyLimit`. Nếu không, hàng chục nghìn virtual thread cùng dồn vào DB.

*Scoped values và structured concurrency*
- *Scoped values* (final ở 25, JEP 506): thay `ThreadLocal` cho dữ liệu bất biến theo phạm vi gọi.
  Giá trị chỉ tồn tại trong khối code đã gán và tự hết hạn khi khối kết thúc.
- *Structured concurrency* (`StructuredTaskScope`): chạy nhiều việc con như một khối, quản lý lỗi
  và huỷ chung cho cả nhóm.
  - Vẫn **preview** ở JDK 25, 26, 27; API đổi qua từng bản.

*Bật trong Spring Boot*
- `spring.threads.virtual.enabled=true` áp dụng cho Tomcat, `@Async` và scheduler.

**Đọc**
- JEP: [444 Virtual Threads](https://openjdk.org/jeps/444), [491 Synchronize Virtual Threads without Pinning](https://openjdk.org/jeps/491), [506 Scoped Values](https://openjdk.org/jeps/506), [533 Structured Concurrency (Seventh Preview)](https://openjdk.org/jeps/533)
- dev.java: [Virtual Threads](https://dev.java/learn/new-features/virtual-threads/)
- Boot: [SpringApplication](https://docs.spring.io/spring-boot/reference/features/spring-application.html) (mục *Virtual Threads*)

**Nắm chắc khi**
- [ ] Giải thích được vì sao bật virtual thread làm DB quá tải dù app không đổi code, và cách chặn
- [ ] Nói được pinning còn là vấn đề trên JDK nào, trong tình huống nào
- [ ] So sánh được virtual thread, goroutine và PHP-FPM worker theo chi phí mỗi đơn vị đồng thời

#### 3.5 Nâng cấp Spring Boot 4 / Spring Framework 7

**Vì sao cần học:** Boot 4 ra cuối 2025, nên nhiều team đang hoặc sắp nâng cấp. Phỏng vấn senior
hay hỏi kế hoạch nâng cấp và rủi ro, tương tự việc nâng Laravel qua một major version.

**Học gì**

*Mốc và baseline*
- Mốc: Spring Framework 7.0 (11/2025), Spring Boot 4.0 (20/11/2025), Boot 4.1 (06/2026).
- *Baseline* (phiên bản tối thiểu của các thành phần nền):
  - Java 17 tối thiểu, khuyến nghị Java 25.
  - Jakarta EE 11 (Servlet 6.1, JPA 3.2). *Jakarta EE* là bộ đặc tả chuẩn (Servlet, JPA...) mà
    Spring dựa vào.
  - Hibernate 7, Spring Security 7, JUnit 6.

*Thay đổi lớn*
- Jackson 3 (thư viện JSON) là mặc định, với package `tools.jackson`. Jackson 2 chỉ còn ở dạng
  deprecated.
- Null-safety bằng JSpecify (`@Nullable`, `@NullMarked`) thay các annotation cũ của Spring. Đây là
  annotation để IDE và công cụ phân tích bắt lỗi null.
- Codebase Boot được modular hoá: starter và auto-config chia nhỏ hơn.
- ⚠️ Bỏ Undertow (một web server nhúng thay cho Tomcat).
- Mới trong core: API versioning (module 2.6), resilience với `@Retryable`, `@ConcurrencyLimit`
  (module 2.4), auto-config cho HTTP service client.

*Cách nâng cấp*
1. Lên bản 3.5 mới nhất trước.
2. Sửa hết deprecation.
3. Lên 4.0 theo migration guide.

- ⚠️ Rủi ro chính: thư viện bên thứ ba chưa hỗ trợ Jackson 3 hoặc Jakarta EE 11.

**Đọc**
- [Spring Boot 4.0.0 available now](https://spring.io/blog/2025/11/20/spring-boot-4-0-0-available-now/)
- [Spring Boot 4.0 Release Notes](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Release-Notes), [Migration Guide](https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-4.0-Migration-Guide)
- Spring: [Null-safety](https://docs.spring.io/spring-framework/reference/core/null-safety.html)

**Nắm chắc khi**
- [ ] Lập được kế hoạch nâng một service Boot 3.x lên 4.x: thứ tự bước, rủi ro, cách kiểm chứng
- [ ] Kể được 3 thay đổi của Boot 4 có thể làm vỡ code đang chạy

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Vì sao `Integer` 127 so bằng `==` là `true` còn 128 là `false`?** (1.1)
- Ý phải có: `Integer.valueOf` cache -128..127; ngoài khoảng đó là object khác nhau; `==` so reference
- Điểm cộng: NPE khi unboxing `null`; `Long` cũng cache tương tự

**2. Hợp đồng `equals`/`hashCode` là gì? Vi phạm thì sao?** (1.1)
- Ý phải có: equals bằng nhau thì hashCode bằng nhau; vi phạm thì `HashSet` chứa trùng, `get` trả `null`
- Điểm cộng: key mutable; dùng `record` làm key

**3. Checked và unchecked exception khác nhau thế nào? So với PHP?** (1.2, 1.5)
- Ý phải có: checked bắt buộc `catch`/`throws`; unchecked thì không; PHP chỉ có unchecked
- Điểm cộng: vì sao Spring bọc thành unchecked; hệ quả với rollback của `@Transactional`

**4. Constructor injection tốt hơn field injection ở điểm nào?** (1.4)
- Ý phải có: field `final`, dependency rõ, test không cần container
- Điểm cộng: constructor dài là dấu hiệu class làm quá nhiều việc

**5. Mô hình xử lý request của Spring MVC khác PHP-FPM thế nào?** (1.5)
- Ý phải có: một process sống lâu, thread pool, state dùng chung giữa request; FPM share-nothing mỗi request
- Điểm cộng: hệ quả với singleton, `ThreadLocal`, connection pool; Octane gặp lại cùng bẫy
- Red flag: không thấy khác biệt về rủi ro state

### 🟡 Mid

**6. `HashMap` resize và treeify khi nào?** (2.2)
- Ý phải có: vượt `capacity × 0.75` thì gấp đôi; bucket ≥ 8 và bảng ≥ 64 thì thành cây đỏ-đen
- Điểm cộng: vì sao phải trộn bit cao (`h ^ h >>> 16`); phần tử chỉ ở lại hoặc dịch `oldCap`

**7. Vì sao `Executors.newFixedThreadPool` nguy hiểm trong production?** (2.3)
- Ý phải có: queue không giới hạn, task dồn tới OOM, latency tăng không báo lỗi
- Điểm cộng: thread vượt core chỉ tạo khi queue đầy; `CallerRunsPolicy` tạo backpressure

**8. Vì sao `@Transactional` không có tác dụng khi gọi method trong cùng class?** (2.4)
- Ý phải có: proxy bọc bean, `this.b()` không đi qua proxy
- Điểm cộng: 3 cách sửa (tách bean, `TransactionTemplate`, inject chính mình); method `private`/`final` cũng không proxy được

**9. Ném `IOException` trong method `@Transactional` mà dữ liệu vẫn được commit. Vì sao?** (2.4)
- Ý phải có: mặc định chỉ rollback với unchecked; dùng `rollbackFor`
- Điểm cộng: `UnexpectedRollbackException` khi bắt exception của method trong
- Red flag: "Spring bị lỗi"

**10. Thêm `@Async` vào method gửi email mà email vẫn gửi đồng bộ, hoặc lỗi biến mất.** (2.4)
- Ý phải có: thiếu `@EnableAsync` hoặc self-invocation; exception của method `void` không tới caller
- Điểm cộng: nói được executor mặc định của Boot (thread pool 8 core, queue không giới hạn, hoặc virtual thread khi bật); MDC/security context mất khi đổi thread

**11. `LazyInitializationException` xảy ra khi nào? Open-in-view liên quan thế nào?** (2.5)
- Ý phải có: truy cập quan hệ lazy khi persistence context đã đóng; open-in-view giữ context tới hết request nên che lỗi
- Điểm cộng: cái giá là giữ connection lâu và N+1 ngầm ở serializer; nhiều đội tắt nó và trả DTO

**12. Sửa N+1 trong JPA thế nào?** (2.5)
- Ý phải có: fetch join, entity graph, batch size, projection theo use case
- Điểm cộng: fetch join collection + phân trang thì phân trang trong RAM
- Red flag: "đổi sang EAGER"

**13. Spring Security xử lý một request có JWT thế nào?** (2.6)
- Ý phải có: filter chain, filter bearer token, decode và validate chữ ký/`exp`/`iss`, đặt `Authentication` vào `SecurityContext`, rồi phân quyền
- Điểm cộng: lấy key qua JWKS và cache; nhiều `SecurityFilterChain` cho các nhóm URL; so sánh với middleware `auth:sanctum`

**14. Test repository nên dùng H2 hay Testcontainers?** (2.7)
- Ý phải có: Testcontainers với đúng DB production; H2 khác dialect, lock, isolation
- Điểm cộng: `@ServiceConnection`; context caching; `@Transactional` trên test che lỗi

### 🔴 Senior

**15. Service bị restart liên tục trên Kubernetes, exit code 137, log không có lỗi.** (3.3)
- Ý phải có: OOMKilled do vượt limit container, không phải `OutOfMemoryError`; so heap (`MaxRAMPercentage`) với limit; tính non-heap
- Điểm cộng: Native Memory Tracking; số thread × stack; direct buffer
- Red flag: "tăng `-Xmx`"

**16. G1 và ZGC khác nhau thế nào? Khi nào đổi?** (3.1)
- Ý phải có: G1 region + mục tiêu pause, cân bằng; ZGC concurrent, pause dưới ms, tốn CPU và footprint hơn
- Điểm cộng: ZGC generational mặc định từ 23; đo p99 và GC log trước khi đổi; JVM có thể đang chạy Serial trong container nhỏ (trước JDK 27)

**17. API chậm dần rồi treo, CPU thấp, thread pool đầy.** (2.3, 3.3)
- Ý phải có: thread dump nhiều lần; tìm thread chờ HikariCP, chờ HTTP ngoài không timeout, deadlock
- Điểm cộng: `REQUIRES_NEW` giữ hai connection; timeout ở mọi tầng; metric pool (active, pending)

**18. Có nên bật virtual thread cho service này?** (3.4)
- Ý phải có: chỉ lợi với I/O-bound; kiểm tra bản JDK (pinning trước 24), native call; giới hạn downstream
- Điểm cộng: `ThreadLocal` nặng; đo trước và sau; so với WebFlux về độ phức tạp code
- Red flag: "bật lên là nhanh hơn"

**19. Batch import 1 triệu dòng bằng JPA chạy 3 giờ, RAM tăng dần.** (2.5)
- Ý phải có: persistence context phình; `flush`/`clear` theo lô; bật JDBC batch
- Điểm cộng: `IDENTITY` chặn batch insert; dùng `JdbcTemplate.batchUpdate` hoặc `LOAD DATA`

**20. Pod Java mới scale lên có p99 rất cao trong vài phút đầu.** (3.2)
- Ý phải có: JIT warm-up, class loading, pool lười khởi tạo
- Điểm cộng: AOT cache (JDK 24–25), CDS, readiness chờ warm-up, native image và đánh đổi

**21. Bạn sẽ nâng một hệ thống Boot 3 lên Boot 4 thế nào?** (3.5)
- Ý phải có: lên 3.5 trước, dọn deprecation, đọc migration guide, chạy test đầy đủ
- Điểm cộng: rủi ro Jackson 3 (serialize khác, package đổi), Jakarta EE 11, thư viện bên thứ ba; rollout từng service
- Red flag: đổi version trong build file rồi "chạy thử xem"

---

## Bài tập tự làm

Cần JDK: `brew install openjdk`. Mỗi file chạy bằng `java TenFile.java`.

1. Viết `LruCache.java` dùng `LinkedHashMap`, rồi giải thích vì sao nó không thread-safe và bạn sẽ sửa thế nào.
2. Viết một đoạn Java minh hoạ `ConcurrentModificationException` trong **một** thread, và hai cách sửa.
3. Vẽ sơ đồ luồng gọi khi controller gọi `service.a()`, trong `a()` gọi `this.b()` có
   `@Transactional(propagation = REQUIRES_NEW)`. Chỉ ra transaction nào thực sự được tạo.
4. Với entity `Order` có `@ManyToOne Customer` và `@OneToMany items`, viết JPQL/entity graph để lấy
   20 đơn hàng mới nhất kèm customer và items mà không N+1 và không phân trang trong RAM.
5. Tính cấu hình heap cho container limit 2 GB, app có khoảng 200 thread. Nêu giả định của bạn.
6. Viết `Payment.java` gồm `sealed interface` và 3 `record`, một hàm tính phí dùng `switch` pattern
   không có `default`. Thêm record thứ tư và quan sát lỗi compile.
7. Viết một bảng so sánh một trang: cùng luồng "tạo đơn, gửi email sau commit" viết bằng Laravel và
   Spring Boot (transaction, event after commit, queue/`@Async`, retry). Chỉ ra chỗ mỗi bên dễ sai.

> Nộp bài vào đây để được review.
