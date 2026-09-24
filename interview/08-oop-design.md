# 08. OOP, SOLID, design pattern và clean code

> [← Mục lục](README.md) · Phạm vi: OOP, SOLID, các nguyên tắc thiết kế, design pattern GoF phổ biến và ví dụ trong Laravel/Spring/Go, pattern tầng dữ liệu, DI/IoC, clean code, code smell, refactoring và anti-pattern.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

Kiến trúc mức hệ thống (layered, hexagonal, DDD, microservice) ở [15-architecture.md](15-architecture.md).
Test và code review ở [20-testing-quality.md](20-testing-quality.md).

## Bản đồ nhanh

**OOP**
- [ ] 4 tính chất: encapsulation, abstraction, inheritance, polymorphism
- [ ] ⚠️ Composition over inheritance
- [ ] Interface vs abstract class
- [ ] Overloading vs overriding (PHP và Go không có overloading)
- [ ] 🟡 Polymorphism kiểu Go (structural) vs Java/PHP (nominal)

**SOLID**
- [ ] SRP, OCP, LSP, ISP, DIP: định nghĩa, ví dụ vi phạm, cách sửa
- [ ] 🔴 Khi nào áp SOLID quá tay thành over-engineering

**Nguyên tắc khác**
- [ ] DRY, KISS, YAGNI; ⚠️ abstraction sai đắt hơn trùng lặp
- [ ] 🟡 Law of Demeter, tell don't ask
- [ ] Cohesion cao, coupling thấp
- [ ] 🟡 Immutability, value object

**Design pattern GoF**
- [ ] Creational: Singleton, Factory Method, Abstract Factory, Builder
- [ ] Structural: Adapter, Decorator, Facade, Proxy, Composite
- [ ] Behavioral: Strategy, Observer, Command, Chain of Responsibility, Template Method, State, Iterator

**Tầng dữ liệu**
- [ ] Repository, 🟡 Unit of Work
- [ ] Active Record vs Data Mapper
- [ ] DTO, 🟡 Specification, 🟡 Identity Map

**DI và IoC**
- [ ] DI, IoC container
- [ ] ⚠️ Service Locator và vì sao bị coi là anti-pattern

**Clean code và refactoring**
- [ ] Đặt tên, hàm nhỏ, side effect, command-query separation
- [ ] Code smell: long method, god class, feature envy, primitive obsession, shotgun surgery, ...
- [ ] Kỹ thuật refactoring cơ bản, refactor từng bước nhỏ
- [ ] 🔴 Refactor code legacy không có test

**Anti-pattern**
- [ ] 🔴 Anemic domain model (và tranh luận)
- [ ] God object
- [ ] 🔴 Premature abstraction

## Chi tiết

### OOP

- [ ] Bốn tính chất
  | Tính chất | Ý chính | Ví dụ thực tế |
  |---|---|---|
  | Encapsulation | Giấu state, chỉ lộ hành vi; giữ invariant | `Order::addItem()` tự tính lại tổng, không cho set `total` từ ngoài |
  | Abstraction | Lộ "làm gì", giấu "làm thế nào" | `PaymentGateway::charge()` không lộ chi tiết VNPay/Stripe |
  | Inheritance | Tái dùng và phân loại qua quan hệ "is-a" | `Exception` → `DomainException` |
  | Polymorphism | Cùng lời gọi, hành vi khác theo kiểu thực | `$gateway->charge()` với nhiều implementation |
  - ⚠️ Encapsulation không phải "getter/setter cho mọi field". Setter công khai cho mọi thứ là mất encapsulation.

- [ ] ⚠️ Composition over inheritance
  - Kế thừa gắn chặt con với chi tiết của cha (fragile base class): sửa cha làm vỡ con.
  - Kế thừa sâu (4–5 tầng) khó đọc: phải lần qua nhiều file để biết method nào chạy.
  - Kế thừa để tái dùng code (không phải quan hệ "is-a") thường sai. Dùng composition: object chứa
    object khác và uỷ quyền.
  - Kế thừa vẫn hợp khi: quan hệ is-a thật, class cha thiết kế để được kế thừa (template method,
    framework base class), hierarchy nông.

- [ ] Interface vs abstract class
  - Interface: hợp đồng, một class implement nhiều. Abstract class: chia sẻ code và state, một cha.
  - Mặc định: interface cho điểm mở rộng; abstract class khi thật sự có code chung đáng kể.
  - Go chỉ có interface; chia sẻ code bằng embedding hoặc hàm.

- [ ] Overloading vs overriding
  - Overloading: cùng tên, khác tham số, chọn lúc compile. Java có; PHP và Go **không** (PHP giả lập
    bằng tham số tuỳ chọn, union type, `__call`).
  - Overriding: class con định nghĩa lại method của cha, chọn lúc runtime. `@Override` (Java),
    `#[\Override]` (PHP 8.3) để compiler bắt lỗi gõ sai tên.

- [ ] 🟡 Polymorphism: Go vs Java/PHP
  - Java/PHP: nominal typing, class phải khai báo `implements`. Interface thường do **bên cung cấp** định nghĩa.
  - Go: structural typing, có đủ method là thoả. Interface do **bên dùng** định nghĩa, nhỏ (1–3 method).
  - Hệ quả: Go ít cần "interface cho mọi thứ" từ trước; tạo interface khi có nhu cầu thay thế thật
    (test, nhiều implementation).
  - Go không có kế thừa nên không có vấn đề fragile base class; đổi lại không có dynamic dispatch qua embedding.

### SOLID

- [ ] **S** — Single Responsibility
  - Một module chỉ có **một lý do để thay đổi** (một nhóm người/nghiệp vụ yêu cầu thay đổi nó).
    Không phải "chỉ làm một việc".
  - Vi phạm: `OrderController::store()` validate, tính giá, trừ kho, gọi cổng thanh toán, gửi mail, ghi log.
  - Sửa: Form Request cho validate, `PricingService`, `InventoryService`, `PaymentGateway`, event
    `OrderPlaced` + listener gửi mail.
  - ⚠️ Quá tay: mỗi class một method, 20 class cho một luồng CRUD đơn giản; đọc một tính năng phải mở 15 file.

- [ ] **O** — Open/Closed
  - Mở để mở rộng, đóng để sửa đổi: thêm hành vi mới bằng code mới thay vì sửa code cũ đã ổn định.
  ```php
  // Vi phạm: mỗi cổng mới phải sửa hàm này
  match ($type) { 'vnpay' => $this->payVnpay($o), 'momo' => $this->payMomo($o) };
  // Sửa: interface PaymentGateway + registry/container chọn implementation theo $type
  $this->gateways->get($type)->charge($o);
  ```
  - ⚠️ Quá tay: dựng plugin system cho thứ chỉ có một biến thể và không có dấu hiệu sẽ có thêm.
    Chỉ tạo điểm mở rộng khi thay đổi **đã lặp lại** hoặc chắc chắn sẽ tới.

- [ ] **L** — Liskov Substitution
  - Class con dùng thay class cha được mà không phá kỳ vọng của code gọi: không đòi điều kiện đầu vào
    chặt hơn, không trả kết quả lỏng hơn, không ném exception mới bất ngờ, giữ invariant.
  - Ví dụ kinh điển: `Square extends Rectangle`; `setWidth` trên Square đổi luôn height, code tính
    diện tích sau `setWidth(5); setHeight(4)` kỳ vọng 20 nhận 16.
  - Ví dụ thực tế: `ReadOnlyRepository extends Repository` rồi `save()` ném `NotSupportedException`.
  - Sửa: không kế thừa khi hành vi không tương thích; tách interface (`Reader`, `Writer`); dùng value
    object immutable.
  - Dấu hiệu vi phạm: `if ($x instanceof SubClass)` trong code dùng class cha.

- [ ] **I** — Interface Segregation
  - Client không nên phụ thuộc vào method nó không dùng.
  - Vi phạm: `interface Worker { work(); eat(); sleep(); }` bắt `Robot` implement `eat()` rỗng; hay
    `UserRepositoryInterface` 40 method mà mỗi service chỉ dùng 2.
  - Sửa: interface nhỏ theo vai trò (`io.Reader`, `io.Writer` là ví dụ chuẩn).
  - ⚠️ Quá tay: tách mỗi method một interface khi chỉ có một implementation và một client.

- [ ] **D** — Dependency Inversion
  - Module cấp cao (nghiệp vụ) không phụ thuộc module cấp thấp (DB, HTTP, SDK); cả hai phụ thuộc
    abstraction. Abstraction thuộc về phía nghiệp vụ.
  - Vi phạm: `OrderService` gọi thẳng `new StripeClient()` và `DB::table()`.
  - Sửa: `OrderService(PaymentGateway $gw, OrderRepository $repo)`; container bind implementation.
  - Khác với DI: DIP là nguyên tắc thiết kế (hướng phụ thuộc), DI là kỹ thuật (truyền dependency vào),
    IoC container là công cụ.
  - ⚠️ Quá tay: interface cho mọi class (kể cả class thuần tính toán không có I/O), tạo ra cặp
    `FooInterface`/`Foo` không bao giờ có implementation thứ hai.

- [ ] 🔴 SOLID và over-engineering
  - SOLID là công cụ quản lý **thay đổi**. Code không thay đổi, hoặc nhỏ, thì chi phí gián tiếp lớn hơn lợi ích.
  - Dấu hiệu quá tay: nhiều tầng uỷ quyền chỉ chuyển tiếp lời gọi, interface một implementation,
    factory tạo một loại object, người mới mất vài ngày để lần một luồng.
  - Cách senior nói: "Tôi bắt đầu đơn giản, tách ra khi thấy thay đổi thứ hai hoặc khi cần test cô lập."

### Nguyên tắc khác

- [ ] DRY, KISS, YAGNI
  - DRY: mỗi **tri thức** (quy tắc nghiệp vụ) có một nơi định nghĩa. Không phải "không có hai đoạn code giống nhau".
  - ⚠️ Hai đoạn giống nhau nhưng thay đổi vì lý do khác nhau thì không nên gộp. "Duplication is far
    cheaper than the wrong abstraction" (Sandi Metz). Quy tắc thực dụng: gộp khi lặp lần thứ ba.
  - KISS: giải pháp đơn giản nhất chạy được. YAGNI: không làm tính năng/điểm mở rộng cho nhu cầu tưởng tượng.

- [ ] 🟡 Law of Demeter và tell don't ask
  - Chỉ nói chuyện với "bạn trực tiếp": tránh `$order->getCustomer()->getAddress()->getCity()`.
    Chuỗi dài làm caller phụ thuộc cấu trúc bên trong của nhiều object.
  - Không áp cho fluent API/builder (`$query->where()->orderBy()`) vì đó là cùng một object.
  - Tell don't ask: thay vì hỏi state rồi quyết định bên ngoài
    (`if ($acc->getBalance() >= $x) $acc->setBalance(...)`), bảo object làm (`$acc->withdraw($x)`)
    để invariant nằm trong object.

- [ ] Cohesion và coupling
  - Cohesion cao: những thứ thay đổi cùng nhau nằm cùng nhau.
  - Coupling thấp: module biết ít nhất có thể về nhau (qua interface, event, dữ liệu đơn giản).
  - Cách đo thô: một thay đổi nghiệp vụ phải sửa bao nhiêu file/module.

- [ ] 🟡 Immutability và value object
  - Object immutable: an toàn chia sẻ giữa thread, dễ suy luận, làm key map được.
  - Value object: định nghĩa bởi giá trị, không có identity (`Money(amount, currency)`, `Email`,
    `DateRange`). Validate lúc tạo, so sánh theo giá trị, thao tác trả object mới.
  - Chống primitive obsession: `transfer(Money $amount)` thay vì `transfer(int $amount, string $currency)`.
  - Công cụ: `readonly` class (PHP 8.2), `record` (Java), struct truyền theo giá trị (Go).
  - ⚠️ Carbon mutable: `$d->addDay()` sửa chính object; dùng `CarbonImmutable`.

### Design pattern GoF

Biết mục đích, một ví dụ thật, và khi nào **không** dùng. Kể tên 23 pattern không có điểm; nhận ra
pattern trong framework mình dùng thì có.

**Creational**

| Pattern | Mục đích | Laravel / PHP | Spring / Java | Go |
|---|---|---|---|---|
| Singleton | Một instance duy nhất | `$app->singleton()` (theo container, không phải GoF cổ điển) | Bean scope singleton (một mỗi context) | Biến package + `sync.Once` |
| Factory Method | Để subclass/hàm quyết định tạo object nào | `Manager::createXxxDriver()` (Cache, Queue, Mail) | `FactoryBean`, `Calendar.getInstance()` | Hàm `NewXxx()`, `http.NewRequest` |
| Abstract Factory | Tạo họ object liên quan | PSR-17 HTTP factories | `DocumentBuilderFactory` | Interface trả nhiều loại object (ít gặp) |
| Builder | Dựng object phức tạp từng bước | Query builder, `Mail` message | `HttpRequest.newBuilder()`, Lombok `@Builder` | Functional options `NewServer(WithTimeout(...))` |

- ⚠️ Singleton cổ điển (static `getInstance()`): state toàn cục, giấu dependency, khó test (không thay
  được), rủi ro với concurrency và với Octane. Singleton **do container quản lý** và inject vào thì ổn.

**Structural**

| Pattern | Mục đích | Laravel / PHP | Spring / Java | Go |
|---|---|---|---|---|
| Adapter | Đổi interface của thứ có sẵn cho khớp interface mình cần | Flysystem adapter (S3, local), cache store | `InputStreamReader`, `HandlerAdapter` | `http.HandlerFunc` biến func thành `Handler` |
| Decorator | Bọc object để thêm hành vi, cùng interface | Middleware, `CachedRepository` bọc repository | `BufferedInputStream`, `TransactionAwareDataSourceProxy` | `bufio.NewReader(r)`, middleware `func(http.Handler) http.Handler` |
| Facade | Một giao diện đơn giản cho hệ con phức tạp | Service class gom nhiều bước; ⚠️ "Facade" của Laravel thực chất là static proxy tới container | `JdbcTemplate` | `http.Get` gói `Client`, `Request`, `Transport` |
| Proxy | Đại diện, kiểm soát truy cập (lazy, cache, remote, bảo mật) | Lazy collection/relationship; Facade Laravel | AOP proxy (`@Transactional`), Hibernate lazy proxy | `httputil.ReverseProxy` (mức mạng) |
| Composite | Cây object, xử lý node lá và node nhóm như nhau | Rule validation lồng nhau, menu | `CompositeCacheManager` | `io.MultiWriter`, `errors.Join` |

- Decorator vs Proxy: cấu trúc giống nhau; Decorator thêm hành vi, Proxy kiểm soát truy cập.
- Adapter vs Facade: Adapter khớp một interface có sẵn; Facade tạo interface mới đơn giản hơn.

**Behavioral**

| Pattern | Mục đích | Laravel / PHP | Spring / Java | Go |
|---|---|---|---|---|
| Strategy | Hoán đổi thuật toán lúc runtime | Payment gateway, driver cache/queue | `Comparator`, inject `List<Strategy>` | `sort.Slice(s, less)`, interface nhỏ |
| Observer | Một sự kiện, nhiều bên lắng nghe | Event/Listener, model observer | `ApplicationEvent`, `@EventListener` | Channel, callback list |
| Command | Gói yêu cầu thành object (xếp hàng, retry, undo) | Queue job, Artisan command | `Runnable`, `Callable` | `func()` gửi qua channel |
| Chain of Responsibility | Chuỗi handler, mỗi cái xử lý hoặc chuyển tiếp | Middleware `Pipeline` | Servlet filter, Spring Security filter chain | Chuỗi middleware HTTP |
| Template Method | Khung thuật toán cố định, bước con để subclass định nghĩa | Base class có hook (`handle()` trong command) | `JdbcTemplate` + callback, `AbstractController` | `sort.Sort` (khung cố định, `Len/Less/Swap` là bước con) |
| State | Hành vi đổi theo trạng thái; mỗi trạng thái một class | Trạng thái đơn hàng (package model states) | Spring State Machine | Hàm trạng thái trả hàm trạng thái kế tiếp |
| Iterator | Duyệt tập hợp không lộ cấu trúc bên trong | `Iterator`, `Generator`, `LazyCollection` | `Iterator`, `Spliterator` | `range`, `bufio.Scanner`, `sql.Rows.Next()`, `iter.Seq` (1.23) |

- Strategy vs State: Strategy do client chọn; State tự chuyển giữa các trạng thái.
- ⚠️ Observer đồng bộ: listener chậm làm chậm người phát; listener lỗi làm hỏng luồng chính. Lắng nghe
  lỗi thứ tự và vòng lặp event.
- Template Method dùng kế thừa; Strategy dùng composition. Ngôn ngữ không có kế thừa (Go) chuyển
  Template Method thành "hàm khung nhận interface".

### Pattern tầng dữ liệu

- [ ] Repository
  - Giao diện giống collection cho aggregate/entity (`findById`, `save`, `ofCustomer`), giấu cách lưu trữ.
  - Lợi: domain không phụ thuộc ORM, dễ thay bằng fake khi test, gom query về một chỗ.
  - ⚠️ Tranh luận trong Laravel: repository chỉ bọc Eloquent 1-1 (`all()`, `find()`, `create()`) mà vẫn
    trả model Eloquent → thêm tầng mà không giấu được gì. Có ý nghĩa khi query phức tạp, nhiều nguồn dữ
    liệu, hoặc domain thuần tách khỏi ORM.
  - ⚠️ Generic repository với 30 method cho mọi entity vi phạm ISP.

- [ ] 🟡 Unit of Work
  - Theo dõi object mới/sửa/xoá trong một nghiệp vụ, rồi ghi xuống DB một lần theo đúng thứ tự trong
    một transaction.
  - Hibernate `Session`/`EntityManager`, Doctrine `EntityManager` (flush). Eloquent **không** có: mỗi `save()`
    ghi ngay.

- [ ] Active Record vs Data Mapper
  | | Active Record | Data Mapper |
  |---|---|---|
  | Ý tưởng | Object = một dòng, tự `save()` | Entity thuần, mapper riêng lo lưu trữ |
  | Ví dụ | Eloquent, Rails ActiveRecord | Doctrine, Hibernate/JPA |
  | Ưu | Nhanh, ít code, hợp CRUD | Domain tách khỏi DB, hợp domain phức tạp, Unit of Work |
  | Nhược | Domain dính schema, model béo, khó test không DB | Nhiều khái niệm hơn, cấu hình, đường cong học |

- [ ] DTO
  - Object chỉ mang dữ liệu qua ranh giới (request → service, service → response, giữa service).
    Không có logic nghiệp vụ.
  - Lợi: contract rõ, không lộ entity ra API (tránh lộ field, lazy load khi serialize), kiểu an toàn thay mảng.
  - Công cụ: PHP `readonly` class, Java `record`, Go struct với JSON tag.
  - ⚠️ Truyền `array $data` khắp nơi là primitive obsession mức cấu trúc.

- [ ] 🟡 Specification
  - Đóng gói một điều kiện nghiệp vụ thành object ghép được (`and`, `or`, `not`), dùng cho cả kiểm tra
    trong bộ nhớ và sinh query.
  - Spring Data JPA `Specification`; ở Laravel gần nhất là query scope hoặc class filter.
  - Chỉ đáng khi điều kiện phức tạp và tái dùng nhiều chỗ.

- [ ] 🟡 Identity Map: một id một object trong một phiên làm việc (persistence context của Hibernate).

### DI, IoC và Service Locator

- [ ] IoC và DI
  - IoC: framework gọi code của bạn và điều khiển luồng/vòng đời ("don't call us, we'll call you").
  - DI: dependency được **truyền vào** (constructor, setter, method) thay vì tự tạo.
  - Constructor injection là mặc định: dependency rõ ràng, object luôn ở trạng thái hợp lệ, test truyền fake trực tiếp.
  - IoC container (Laravel container, Spring) tự nối dependency. Go thường nối tay trong `main`
    (composition root); Wire/Fx khi đồ thị lớn.

- [ ] ⚠️ Service Locator
  - Code tự hỏi registry toàn cục: `app(PaymentGateway::class)`, `resolve()`, `ApplicationContext.getBean()`.
  - Vì sao bị coi là anti-pattern: dependency ẩn (không thấy trong constructor), lỗi thiếu binding chỉ lộ lúc
    runtime, test phải dựng container, class phụ thuộc vào chính container.
  - Chấp nhận được ở composition root, factory, code framework. Laravel Facade là dạng service locator
    tiện lợi; dùng trong controller/route thì ổn, trong domain logic thì nên inject.

### Clean code và refactoring

- [ ] Đặt tên
  - Tên nói **ý định**: `activeUsersWithUnpaidInvoices()` thay `getData2()`. Boolean dạng `isX`, `hasX`, `canX`.
  - Dùng ngôn ngữ nghiệp vụ (ubiquitous language), một khái niệm một từ (đừng lẫn `fetch`/`get`/`retrieve`).
  - Tránh viết tắt riêng, tên kiểu (`$userArray`), số (`$data1`).

- [ ] Hàm nhỏ và side effect
  - Hàm làm một việc ở một mức trừu tượng; đọc từ trên xuống như câu chuyện.
  - Ít tham số (quá 3–4 thì gom thành object); ⚠️ tham số boolean `render(true)` thường báo hiệu hàm làm hai việc.
  - Command-query separation: hàm hoặc **đổi state** hoặc **trả dữ liệu**, không lén làm cả hai.
    `getUser()` mà tạo user khi không có là side effect bất ngờ.
  - Guard clause/early return thay vì if lồng sâu.
  - Comment giải thích **vì sao**, không lặp lại code làm gì.

- [ ] Code smell
  | Smell | Dấu hiệu | Hướng sửa |
  |---|---|---|
  | Long method | Hàm hàng trăm dòng, nhiều comment chia đoạn | Extract method |
  | God class / large class | `UserService` 3.000 dòng, 40 dependency | Extract class theo trách nhiệm |
  | Feature envy | Method dùng dữ liệu của class khác nhiều hơn của mình | Move method sang class đó |
  | Primitive obsession | Tiền là `float`, email là `string`, trạng thái là số ma thuật | Value object, enum |
  | Shotgun surgery | Một thay đổi phải sửa 10 file rải rác | Gom trách nhiệm về một chỗ |
  | Divergent change | Một class bị sửa vì nhiều lý do khác nhau | Tách class (SRP) |
  | Long parameter list | Hàm 7 tham số | Introduce parameter object |
  | Data clumps | Cùng nhóm tham số đi cùng nhau khắp nơi | Gom thành object |
  | Switch statements lặp lại | Cùng `switch ($type)` ở nhiều nơi | Polymorphism/Strategy |
  | Dead code, speculative generality | Code không ai gọi, hook "để sau này" | Xoá (git còn giữ lịch sử) |
  | Duplicated code | Copy-paste logic nghiệp vụ | Extract (khi đúng là cùng tri thức) |

- [ ] Kỹ thuật refactoring cơ bản
  - Rename, Extract method/variable/class, Inline method/variable, Move method/field,
    Introduce parameter object, Replace conditional with polymorphism, Replace magic number with constant,
    Replace temp with query, Encapsulate field, Extract interface.
  - Dùng công cụ refactor của IDE khi có (rename an toàn hơn tìm-thay thủ công).

- [ ] Refactor từng bước nhỏ
  - Định nghĩa: đổi cấu trúc **không đổi hành vi**. Mỗi bước nhỏ, code luôn chạy được, có lưới an toàn (test).
  - ⚠️ Tách commit/PR refactor khỏi commit đổi hành vi; reviewer đọc được, rollback được.
  - Quy tắc hướng đạo sinh: để code sạch hơn một chút mỗi lần chạm vào; không refactor lan man ngoài phạm vi.
  - Thay đổi lớn: strangler (xây mới song song, chuyển dần), branch by abstraction, feature flag.
    Xem [15-architecture.md](15-architecture.md).

- [ ] 🔴 Code legacy không có test
  - Trước tiên dựng characterization test (ghi lại hành vi hiện tại, kể cả hành vi "sai"), rồi mới đổi.
  - Tìm seam: chỗ có thể thay dependency mà không sửa nhiều (tham số, constructor, interface).
  - Ưu tiên phần hay thay đổi và hay lỗi; phần ổn định không ai đụng thì để yên.
  - Đo rủi ro: log, metric, feature flag, rollout từng phần.

### Anti-pattern

- [ ] 🔴 Anemic domain model
  - Entity chỉ có getter/setter, toàn bộ logic nằm trong service. Fowler gọi là anti-pattern vì mất
    encapsulation: invariant bị kiểm tra (hoặc quên) ở nhiều service.
  - Phía phản biện: với ứng dụng CRUD/nghiệp vụ mỏng, transaction script (service + model đơn giản) dễ hiểu,
    đủ dùng; Active Record của Laravel vốn đã trộn dữ liệu và persistence.
  - Câu trả lời senior: độ giàu của domain model tỉ lệ với độ phức tạp nghiệp vụ. Có invariant quan trọng
    (số dư không âm, trạng thái đơn chỉ đi một chiều) thì đưa vào entity/value object.

- [ ] God object
  - Một class biết và làm quá nhiều (`Helper`, `Utils`, `AppService`, model `User` 2.000 dòng).
  - Hậu quả: mọi người cùng sửa một file, conflict, không test được riêng, thay đổi nhỏ rủi ro lớn.
  - Sửa dần: tách theo nhóm method dùng chung dữ liệu; tạo class mới và chuyển từng method.

- [ ] 🔴 Premature abstraction
  - Tạo interface, base class, generic, plugin system trước khi có biến thể thứ hai.
  - Abstraction đoán sai hình dạng tương lai → khi nhu cầu thật tới, phải vặn vẹo hoặc đập đi.
  - Dấu hiệu: tham số cấu hình không ai dùng, class `Abstract*` một con, "framework nội bộ" cho một dự án.
  - Lạm dụng pattern cũng là dạng này: Factory tạo một loại, Strategy một chiến lược, Observer một listener.

### Đối chiếu với ngôn ngữ khác

| Khía cạnh | PHP | Java | Go |
|---|---|---|---|
| Kế thừa | Một cha, trait để trộn code | Một cha, interface default method | Không có; embedding |
| Interface | Nominal, `implements` | Nominal, `implements` | Structural, ngầm, nhỏ |
| Overloading | Không | Có | Không |
| Value object | `readonly` class (8.2) | `record` | Struct truyền theo giá trị |
| DI | Container reflection | Spring IoC | Nối tay trong `main`, Wire/Fx |
| Pattern "biến mất" | | | Strategy/Command thành `func`; Iterator thành `range`; Template Method thành hàm nhận interface |

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Giải thích SOLID | Đọc định nghĩa năm chữ. | Mỗi chữ một ví dụ từ code thật (vi phạm và cách sửa), và nói chỗ mình **không** áp dụng vì chi phí lớn hơn lợi ích. |
| Có nên dùng Repository trong Laravel? | "Có, vì clean architecture." | Tuỳ: bọc Eloquent 1-1 mà vẫn trả model thì không giấu được gì; đáng khi query phức tạp, nhiều nguồn dữ liệu, hoặc domain cần test không DB. |
| Singleton tốt hay xấu? | "Xấu vì là global." | Phân biệt Singleton cổ điển (static, state toàn cục, khó test) với scope singleton do container quản lý và inject; nêu rủi ro state leak với Octane/thread. |
| Code trùng lặp ở 2 chỗ, gộp không? | "Gộp, vì DRY." | Hỏi hai chỗ có cùng lý do thay đổi không; nếu là trùng lặp ngẫu nhiên thì để; đợi lần thứ ba, và ưu tiên trùng lặp hơn abstraction sai. |
| Refactor module cũ | "Viết lại từ đầu." | Characterization test, bước nhỏ, commit tách biệt, strangler/feature flag; đo trước sau; ưu tiên phần hay đổi. |

## Tình huống

1. **Thiết kế hệ thống thanh toán hỗ trợ nhiều cổng (VNPay, Momo, Stripe) để dễ thêm cổng mới.**
   - Gợi ý: interface `PaymentGateway` (charge, refund, verifyWebhook); Strategy + registry chọn theo cổng;
     Adapter bọc SDK từng cổng; DTO kết quả chung; webhook idempotent; không để chi tiết cổng rò vào domain.
2. **`OrderService` 2.500 dòng, ai sửa cũng sợ.**
   - Gợi ý: tìm cụm method dùng chung dữ liệu; characterization test cho luồng chính; extract class từng
     phần (pricing, inventory, notification); mỗi bước một PR.
3. **Mỗi lần thêm loại thông báo mới (SMS, Zalo, push) phải sửa 6 file có `switch ($channel)`.**
   - Gợi ý: shotgun surgery + switch lặp; interface `Channel`, mỗi kênh một class, đăng ký qua container;
     Laravel Notification channel là ví dụ có sẵn.
4. **Code review thấy mỗi class đều có `XxxInterface` dù chỉ có một implementation.**
   - Gợi ý: hỏi lý do (test? ranh giới module?); interface có giá trị ở ranh giới I/O và điểm mở rộng thật;
     còn lại là premature abstraction; đề xuất quy ước đội.
5. **Tiền được lưu và tính bằng `float`, báo cáo lệch vài đồng.**
   - Gợi ý: primitive obsession; value object `Money` (số nguyên đơn vị nhỏ nhất + currency), quy tắc làm
     tròn tập trung; xem [22-practical-data.md](22-practical-data.md).
6. **Model `Order` có 15 observer và event ẩn, sửa trạng thái đơn gây side effect khó đoán.**
   - Gợi ý: logic nghiệp vụ ẩn trong observer; đưa chuyển trạng thái vào method tường minh (State pattern
     hoặc method trên entity), phát domain event rõ ràng; ghi tài liệu luồng.

## ❓ Câu hỏi hay gặp

🟢
- Bốn tính chất của OOP, mỗi cái một ví dụ.
- Interface và abstract class khác nhau thế nào, khi nào dùng cái nào?
- Overloading và overriding khác nhau thế nào? PHP có overloading không?
- Composition over inheritance nghĩa là gì?
- Kể 3 design pattern bạn đã dùng và dùng ở đâu.

🟡
- Giải thích SOLID, mỗi chữ một ví dụ từ code bạn từng viết.
- Ví dụ vi phạm Liskov ngoài `Square`/`Rectangle`?
- Decorator và Proxy khác nhau thế nào? Middleware là pattern gì?
- Strategy và State khác nhau thế nào?
- Active Record và Repository khác nhau thế nào? Laravel dùng kiểu nào?
- DI và Service Locator khác nhau thế nào? Laravel Facade thuộc loại nào?
- Law of Demeter là gì? Fluent API có vi phạm không?

🔴
- Khi nào áp SOLID là over-engineering? Cho ví dụ bạn đã gặp.
- Anemic domain model có thật sự là anti-pattern không?
- Refactor một module legacy không có test thế nào cho an toàn?
- Vì sao "trùng lặp rẻ hơn abstraction sai"?
- Go không có kế thừa thì các pattern như Template Method, Decorator viết thế nào?

## Bài tập tự làm

1. Lấy một controller hoặc service dài nhất trong dự án bạn đang làm, liệt kê các code smell thấy được và
   kế hoạch refactor theo từng bước nhỏ (mỗi bước một commit, không đổi hành vi).
2. Viết interface và 2 implementation cho `PaymentGateway` bằng PHP (`declare(strict_types=1);`), kèm
   registry chọn cổng theo tên. Giải thích vì sao thiết kế thoả OCP.
3. Viết cùng một middleware (log thời gian xử lý) theo pattern Decorator bằng Go và bằng PHP, rồi so sánh.
4. Tìm trong mã nguồn Laravel (thư mục `vendor/laravel/framework`) ví dụ của Manager (Factory Method),
   Pipeline (Chain of Responsibility) và Facade; ghi đường dẫn file và giải thích ngắn.
5. Thiết kế value object `Money` bằng ngôn ngữ bạn chọn: tạo, cộng, so sánh, chia đều cho N người mà
   không mất đồng nào. Không dùng `float`.

> Nộp bài vào đây để được review.
