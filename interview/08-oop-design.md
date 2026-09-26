# 08. OOP, SOLID, design pattern và clean code

> [← Mục lục](README.md) · Trọng tâm: **PHP 8.4–8.5 / Laravel** (OOP hiện đại, container, contracts), đối chiếu Java 21+ và Go.
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

Kiến trúc mức hệ thống (layered, hexagonal, DDD, microservice) ở [15-architecture.md](15-architecture.md).
Test và code review ở [20-testing-quality.md](20-testing-quality.md).

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| *Design Patterns* (Gamma, Helm, Johnson, Vlissides; 1994) | Sách | Nguồn gốc 23 pattern GoF. Đọc chương 1 (nguyên tắc "program to an interface", "favor composition") và tra từng pattern khi cần |
| [Refactoring.Guru](https://refactoring.guru/design-patterns) | Sách online miễn phí | Pattern và code smell có hình minh hoạ, ví dụ PHP/Java/Go. Dễ đọc hơn sách GoF |
| *Refactoring*, 2nd ed. (Fowler, 2018) và [catalog](https://refactoring.com/catalog/) | Sách + catalog | Code smell (ch.3), các kỹ thuật refactoring, cách refactor từng bước nhỏ |
| *Working Effectively with Legacy Code* (Feathers, 2004) | Sách | Seam, characterization test, đưa code không test vào kiểm soát |
| [*Patterns of Enterprise Application Architecture*](https://martinfowler.com/eaaCatalog/) (Fowler) | Sách + catalog | Repository, Unit of Work, Active Record, Data Mapper, Identity Map |
| [PHP Manual: Classes and Objects](https://www.php.net/manual/en/language.oop5.php) | Official docs | Interface, abstract, trait, enum, readonly, property hooks: hành vi chính xác của PHP |
| [Laravel: Service Container](https://laravel.com/docs/container) | Official docs | DI, binding interface → implementation, contextual binding; nền tảng để hiểu SOLID trong Laravel |
| *Effective Java*, 3rd ed. (Bloch) | Sách | Đối chiếu: item 1 (static factory), item 17 (immutability), item 18 (composition thay kế thừa) |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Nói đúng OOP, phân biệt interface/abstract/trait, áp SOLID vào code thật | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.7 | Dùng OOP hiện đại của PHP, nhận ra pattern trong framework, thiết kế tầng dữ liệu và DI đúng | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.4 | Refactor code legacy an toàn, nhận ra over-engineering, đối chiếu thiết kế giữa các ngôn ngữ | 6–8 ngày |

Học theo thứ tự: pattern ở chặng 2 chỉ là cách áp các nguyên tắc ở chặng 1, và chặng 3 là
biết khi nào **không** áp chúng. Người phỏng vấn senior ít hỏi định nghĩa, hay hỏi "bạn đã
từng quyết định không dùng pattern X ở đâu, vì sao".

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Bốn tính chất OOP và composition over inheritance

**Vì sao cần học:** Đây là câu mở đầu của gần như mọi vòng phỏng vấn OOP. Người phỏng vấn không
cần định nghĩa sách vở, họ muốn nghe ví dụ từ nghiệp vụ, rồi hỏi vặn "vậy getter/setter cho mọi
field có phải encapsulation không". Trong dự án Laravel, hiểu composition giúp bạn tránh dựng
các `BaseController`, `BaseService` nhiều tầng mà về sau không ai dám sửa.

**Học gì**

*Encapsulation (đóng gói)*
- Một object gồm *state* (dữ liệu nó giữ, tức các property) và hành vi (các method).
- Encapsulation là giấu state bên trong, chỉ cho bên ngoài dùng hành vi.
- Mục đích chính là giữ *invariant*: điều kiện luôn phải đúng với object.
  - Ví dụ invariant: "tổng tiền của đơn luôn bằng tổng các dòng hàng".
  - `Order::addItem()` thêm dòng hàng và tự tính lại tổng. Không có cách nào set `total` từ
    ngoài, nên không ai làm lệch tổng được.

  ```php
  final class Order
  {
      private array $items = [];
      private int $total = 0;

      public function addItem(string $sku, int $price, int $qty): void
      {
          $this->items[] = ['sku' => $sku, 'price' => $price, 'qty' => $qty];
          $this->total += $price * $qty;   // invariant được giữ ngay trong object
      }

      public function total(): int
      {
          return $this->total;
      }
  }
  ```
- ⚠️ Encapsulation không phải "private field + getter/setter cho mọi field". Nếu field nào cũng
  có setter công khai thì bên ngoài vẫn sửa tuỳ ý, và không còn ai giữ invariant nữa.

*Abstraction (trừu tượng hoá)*
- Abstraction là lộ ra "làm gì", giấu "làm thế nào".
- Ví dụ: `PaymentGateway::charge()`. Code gọi chỉ biết "thu tiền", không biết bên dưới là VNPay
  hay Stripe, gọi HTTP hay dùng SDK.
- Khác với encapsulation:
  - Encapsulation bảo vệ dữ liệu của một object.
  - Abstraction chọn mức chi tiết mà bên ngoài được thấy.

*Inheritance (kế thừa)*
- Class con nhận lại property và method của class cha, rồi thêm mới hoặc viết lại một số method.
- Kế thừa chỉ đúng khi quan hệ là *is-a* ("là một").
  - Ví dụ: `DomainException` là một `Exception`, nên `DomainException extends Exception` hợp lý.

*Polymorphism (đa hình)*
- Cùng một lời gọi method, nhưng code chạy ra tuỳ vào kiểu thật của object lúc chương trình
  đang chạy (*runtime*), không tuỳ vào kiểu được khai báo.
- Ví dụ: biến `$gateway` khai báo kiểu `PaymentGateway`.
  - Object thật là `VnpayGateway` thì `$gateway->charge()` chạy code VNPay.
  - Object thật là `StripeGateway` thì chạy code Stripe.
- Nhờ vậy code gọi không cần `if ($type === 'vnpay') ... elseif ...`.

*Composition over inheritance*
- *Composition* (kết hợp): object giữ một object khác làm field và *uỷ quyền* (delegate) việc
  cho nó, thay vì kế thừa từ nó.
  - Ví dụ: `OrderService` nhận `PaymentGateway` qua constructor rồi gọi
    `$this->gateway->charge()`, thay vì `OrderService extends BasePaymentService`.
- Vì sao nên ưu tiên composition:
  - *Fragile base class* (class cha dễ vỡ): class con phụ thuộc vào chi tiết bên trong của
    class cha, nên sửa cha có thể làm vỡ con dù không ai đụng tới con.
  - Hierarchy (cây kế thừa) 4–5 tầng rất khó lần: muốn biết method nào thật sự chạy phải mở
    từng tầng một.
- ⚠️ Kế thừa chỉ để tái dùng code, không phải is-a thật, thường là sai.
  - Ví dụ: `UserController extends CsvExporter` chỉ để dùng hàm xuất CSV. Controller không "là
    một" bộ xuất CSV.
  - Cách đúng: dùng composition và uỷ quyền (inject `CsvExporter` rồi gọi nó).
- Kế thừa vẫn là lựa chọn đúng khi:
  - Quan hệ is-a là thật.
  - Class cha được thiết kế để được kế thừa, ví dụ Template Method (module 2.4) hay base class
    của framework như `Illuminate\Database\Eloquent\Model`.
  - Hierarchy nông, một hai tầng.

**Đọc**
- GoF ch.1, mục *Inheritance versus Composition* và *Program to an interface, not an implementation*
- *Effective Java* item 18 (*Favor composition over inheritance*): ví dụ `InstrumentedHashSet` là minh hoạ fragile base class rõ nhất

**Nắm chắc khi**
- [ ] Cho một class có setter cho mọi field, chỉ ra được invariant nào có thể bị phá và sửa bằng method nghiệp vụ
- [ ] Viết lại được một hierarchy kế thừa để tái dùng code thành composition, và nói được cái được cái mất
- [ ] Kể được một trường hợp kế thừa là lựa chọn đúng

#### 1.2 Interface, abstract class, trait; overloading và overriding

**Vì sao cần học:** Với dev PHP, câu "interface, abstract class và trait khác nhau thế nào" gần
như chắc chắn gặp. Chọn sai có hậu quả thật: trait chứa logic nghiệp vụ rải khắp dự án làm code
rất khó lần theo. Câu về overloading hay được dùng để hỏi vặn, vì PHP không có overloading.

**Học gì**

*Interface và abstract class*
- *Interface* là một hợp đồng: danh sách method mà class cam kết phải có, không kèm code.
  - Một class implement được nhiều interface.
- *Abstract class* là class không tạo object trực tiếp được, dùng làm cha.
  - Chứa được code và state dùng chung.
  - Có *abstract method*: method chỉ khai báo tên, class con bắt buộc phải viết thân.
  - Một class chỉ `extends` được một cha.
- Mặc định dùng interface cho *điểm mở rộng* (chỗ bạn dự tính sẽ có nhiều cách làm, ví dụ nhiều
  cổng thanh toán). Chỉ dùng abstract class khi thật sự có code chung đáng kể.

| Tiêu chí | Interface | Abstract class | Trait |
|---|---|---|---|
| Chứa code | Không | Có | Có |
| Chứa state (property) | Không, trừ khai báo property từ PHP 8.4 | Có | Có |
| Mỗi class dùng được | Nhiều | Một | Nhiều |
| Là kiểu (type-hint, `instanceof`) | Có | Có | Không |

*Interface trong PHP*
- Interface chứa được hằng số.
- Từ PHP 8.4, interface khai báo được property, kèm hook (module 2.1). Ví dụ interface bắt mọi
  class implement phải có property `$name` đọc được.

*Trait trong PHP*
- *Trait* là một khối method (và property) được "chép" vào class dùng nó. Người ta gọi là trộn
  code theo chiều ngang: dùng lại code mà không cần quan hệ cha con.
- Trait có thể có abstract method, và từ PHP 8.2 có hằng số.
- Khi hai trait có method trùng tên, phải giải xung đột:
  - `insteadof` chọn bản của trait nào.
  - `as` đặt tên khác cho bản còn lại để vẫn gọi được.

  ```php
  trait LogsToFile { public function log(string $m): void { /* ghi file */ } }
  trait LogsToDb   { public function log(string $m): void { /* ghi DB */ } }

  final class OrderService
  {
      use LogsToFile, LogsToDb {
          LogsToDb::log insteadof LogsToFile;   // log() dùng bản của LogsToDb
          LogsToFile::log as logToFile;         // bản kia gọi qua tên logToFile()
      }
  }
  ```
- ⚠️ Trait không phải kiểu: không type-hint được `function f(LogsToDb $x)`, không
  `instanceof` được.
- ⚠️ Trait chứa state và logic nghiệp vụ, dùng ở khắp nơi, là kế thừa trá hình. Đọc một class
  không thấy code đó ở đâu, phải lần qua từng trait.

*Overloading và overriding*
- *Overloading*: nhiều method cùng tên nhưng khác danh sách tham số. Ngôn ngữ chọn bản nào lúc
  biên dịch (*compile time*, trước khi chương trình chạy), dựa trên kiểu tham số truyền vào.
  - Java có: `print(int x)` và `print(String s)` cùng tồn tại.
  - PHP và Go **không** có. Khai báo hai method cùng tên trong PHP là lỗi.
- PHP giả lập overloading bằng:
  - Tham số tuỳ chọn: `function find(int $id, bool $withTrashed = false)`.
  - Union type: `function find(int|string $idOrSlug)`.
  - Named argument: `find(id: 5, withTrashed: true)`.
  - Magic method `__call`: bắt mọi lời gọi tới method không tồn tại.
  - ⚠️ `__call` làm IDE và static analysis không biết method nào có thật, gõ sai tên chỉ lộ lỗi
    lúc runtime.
- ⚠️ Chữ "overloading" trong manual PHP nói về magic method `__get`, `__set`, `__call`. Nghĩa
  này khác hẳn overloading của Java.
- *Overriding*: class con viết lại method của cha. Bản nào chạy được chọn lúc runtime theo kiểu
  thật của object (chính là polymorphism).
  - Java đánh dấu bằng `@Override`, PHP 8.3 có `#[\Override]`.
  - Tác dụng: nếu gõ sai tên method cha, compiler (Java) hoặc PHP báo lỗi ngay, thay vì lặng lẽ
    tạo ra một method mới không ai gọi.

*Đối chiếu Java/Go*
- Java: interface có `default` method (method có sẵn thân, từ Java 8). Class chỉ có một cha.
- Go: chỉ có interface. Chia sẻ code bằng *embedding* (nhúng struct này vào struct kia) hoặc
  bằng hàm thường.
- 🟡 Hai cách một kiểu "thoả" interface:
  - *Nominal* (Java, PHP): class phải khai báo rõ `implements PaymentGateway`.
  - *Structural* (Go): kiểu nào có đủ các method của interface thì tự động thoả, không cần khai
    báo gì.

**Đọc**
- PHP: [Object Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php), [Class Abstraction](https://www.php.net/manual/en/language.oop5.abstract.php), [Traits](https://www.php.net/manual/en/language.oop5.traits.php), [`#[\Override]`](https://www.php.net/manual/en/class.override.php)
- Go: [Effective Go: Interfaces and embedding](https://go.dev/doc/effective_go#embedding)

**Nắm chắc khi**
- [ ] Chọn được interface, abstract class hay trait cho 3 tình huống cụ thể và giải thích lý do
- [ ] Viết được ví dụ hai trait xung đột tên method và giải bằng `insteadof`
- [ ] Giải thích được vì sao PHP không có overloading và 3 cách giả lập, kèm nhược điểm của `__call`

#### 1.3 SOLID

**Vì sao cần học:** Câu hỏi kinh điển ở mức mid, và người phỏng vấn muốn nghe ví dụ từ code bạn
từng viết chứ không phải đọc năm định nghĩa. Laravel được xây quanh các nguyên tắc này
(contracts, service provider), nên hiểu SOLID cũng là hiểu vì sao framework trông như vậy.

**Học gì**

*S: Single Responsibility Principle (SRP)*
- Một module chỉ có **một lý do để thay đổi**. "Lý do" ở đây là một nhóm người hoặc một mảng
  nghiệp vụ có thể yêu cầu sửa nó.
- ⚠️ SRP không phải "mỗi class chỉ làm một việc". Một class có nhiều method vẫn ổn nếu tất cả
  cùng đổi vì một lý do.
- Ví dụ vi phạm: `OrderController::store()` làm tất cả các việc sau:
  1. Validate input.
  2. Tính giá (đổi khi phòng kinh doanh đổi chính sách giá).
  3. Trừ kho (đổi khi quy trình kho đổi).
  4. Gọi cổng thanh toán (đổi khi đổi cổng).
  5. Gửi mail (đổi khi marketing đổi nội dung).
- Sửa trong Laravel, mỗi lý do thay đổi về một chỗ:
  - Validate: *FormRequest* (class validate riêng mà Laravel tự chạy trước controller).
  - Tính giá: `PricingService`. Trừ kho: `InventoryService`. Thanh toán: `PaymentGateway`.
  - Gửi mail: phát event `OrderPlaced`, một listener nhận event đó và gửi mail.

*O: Open/Closed Principle (OCP)*
- Mở để mở rộng, đóng để sửa: thêm hành vi mới bằng cách viết code mới, không phải sửa code đã
  chạy ổn định.
- Ví dụ: mỗi lần thêm cổng thanh toán lại phải thêm một nhánh vào `match`. Cách sửa là dùng
  interface cộng một *registry* (bảng tra "tên cổng → object xử lý"):

  ```php
  // Trước: thêm cổng mới phải sửa hàm này
  $result = match ($type) {
      'vnpay' => $this->chargeVnpay($order),
      'momo'  => $this->chargeMomo($order),
  };

  // Sau: thêm cổng mới = viết một class implement PaymentGateway và đăng ký vào registry
  $result = $this->gateways->get($type)->charge($order);
  ```

*L: Liskov Substitution Principle (LSP)*
- Class con phải thay được class cha mà không phá kỳ vọng của code đang dùng class cha. Cụ thể,
  class con không được:
  - Siết input: đòi đầu vào khắt khe hơn cha (cha nhận mọi số dương, con chỉ nhận số chẵn).
  - Nới output: trả về thứ rộng hơn cha hứa (cha hứa luôn trả `Order`, con có lúc trả `null`).
  - Ném exception mới mà code gọi không lường trước.
  - Phá invariant của cha.
- Ví dụ kinh điển là `Square extends Rectangle`: đặt chiều rộng của hình vuông thì chiều cao
  cũng đổi theo, code tính diện tích hình chữ nhật bị sai.
- Ví dụ thực tế hơn: `ReadOnlyRepository extends Repository`, rồi `save()` ném
  `NotSupportedException`. Code nào nhận `Repository` và gọi `save()` sẽ vỡ.
- Dấu hiệu nhận ra: code dùng class cha mà phải viết `if ($x instanceof SubClass)` để né.

*I: Interface Segregation Principle (ISP)*
- *Client* ở đây là code gọi interface. Client không nên bị buộc phụ thuộc vào method nó không
  dùng.
- Ví dụ vi phạm: `UserRepositoryInterface` có 40 method, mỗi service chỉ dùng 2. Muốn viết fake
  để test một service cũng phải viết đủ 40 method.
- Cách sửa: interface nhỏ theo vai trò. Go làm điều này rất tốt: `io.Reader` chỉ có `Read`,
  `io.Writer` chỉ có `Write`.

*D: Dependency Inversion Principle (DIP)*
- Code nghiệp vụ không phụ thuộc vào *chi tiết* (DB, HTTP, SDK của bên thứ ba). Cả nghiệp vụ lẫn
  chi tiết cùng phụ thuộc vào một abstraction (thường là interface).
- Abstraction **thuộc về phía nghiệp vụ**: interface đặt trong module nghiệp vụ, đặt tên theo
  nhu cầu của nghiệp vụ (`PaymentGateway`), và class bọc Stripe là bên phải tuân theo nó.
- Ba khái niệm hay bị trộn lẫn:

| Khái niệm | Là gì | Ví dụ |
|---|---|---|
| DIP | Nguyên tắc về hướng phụ thuộc | `OrderService` phụ thuộc `PaymentGateway`, không phụ thuộc `StripeClient` |
| DI (dependency injection) | Kỹ thuật: truyền dependency vào thay vì tự `new` | `__construct(private PaymentGateway $gateway)` |
| IoC container | Công cụ tự tạo và truyền dependency | Service container của Laravel, Spring |

*SOLID trong Laravel*
- `Illuminate\Contracts\*` (Cache, Queue, Mail...) là DIP: code của bạn phụ thuộc interface
  `Illuminate\Contracts\Cache\Repository`, còn Redis hay file chỉ là implementation.
- Bạn làm điều tương tự bằng cách bind interface → implementation trong *service provider*
  (class Laravel chạy lúc khởi động để đăng ký dịch vụ):

  ```php
  $this->app->bind(PaymentGateway::class, VnpayGateway::class);
  ```
- ⚠️ Chữ nào cũng có kiểu áp quá tay, ví dụ interface cho mọi class dù chỉ có một
  implementation (xem 3.3).

**Đọc**
- Robert C. Martin: [The Single Responsibility Principle](https://blog.cleancoder.com/uncle-bob/2014/05/08/SingleReponsibilityPrinciple.html) (định nghĩa "lý do thay đổi" theo người yêu cầu)
- Laravel: [Contracts](https://laravel.com/docs/contracts), [Binding Interfaces to Implementations](https://laravel.com/docs/container#binding-interfaces-to-implementations), [Contextual Binding](https://laravel.com/docs/container#contextual-binding)

**Nắm chắc khi**
- [ ] Với mỗi chữ, lấy được một ví dụ vi phạm **từ code mình từng viết** và cách sửa
- [ ] Viết được ví dụ vi phạm LSP không dùng hình học
- [ ] Refactor được `match ($type)` gọi cổng thanh toán thành interface + registry qua container (bài tập 2)

#### 1.4 DRY, KISS, YAGNI; cohesion và coupling

**Vì sao cần học:** Đây là nhóm nguyên tắc bị hiểu sai nhiều nhất, đặc biệt là DRY. Comment
review "chỗ này trùng, gộp lại đi" rất phổ biến và cũng rất hay sai. Ở mức senior hay bị hỏi
"vì sao trùng lặp rẻ hơn abstraction sai".

**Học gì**

*DRY (Don't Repeat Yourself)*
- Mỗi **tri thức** (một quy tắc nghiệp vụ) chỉ có một nơi định nghĩa.
- DRY không có nghĩa là "không được có hai đoạn code giống nhau".
- Trùng lặp tri thức (cần sửa):
  - Ví dụ: quy tắc "đơn từ 500.000đ được miễn phí ship" viết ở controller, ở job tính lại đơn và
    ở Blade. Đổi ngưỡng thành 300.000đ thì phải nhớ sửa ba chỗ.
- Trùng lặp ngẫu nhiên (không cần gộp):
  - Ví dụ: validate `phone` của khách hàng và của nhà cung cấp hôm nay trông giống nhau, nhưng
    thuộc hai nghiệp vụ và sẽ đổi vì hai lý do khác nhau.

*Khi nào không nên gộp*
- ⚠️ Hai đoạn giống nhau nhưng thay đổi vì những lý do khác nhau thì không gộp.
- Sandi Metz: "Duplication is far cheaper than the wrong abstraction" (trùng lặp rẻ hơn nhiều so
  với abstraction sai). Abstraction sai thường hình thành như sau:
  1. Hai đoạn code giống nhau, được gộp thành một hàm chung.
  2. Có nhu cầu mới hơi khác, người sau thêm một tham số hoặc một cờ `bool` vào hàm đó.
  3. Lặp lại vài lần, hàm đầy `if` cho từng trường hợp, không ai hiểu hết.
  4. Tháo ra lúc này tốn hơn nhiều so với để hai bản copy từ đầu.
- Quy tắc thực dụng: chờ tới lần lặp thứ ba mới gộp. Lúc đó bạn đã thấy phần nào thật sự chung.

*KISS và YAGNI*
- KISS (Keep It Simple, Stupid): chọn giải pháp đơn giản nhất chạy được.
- YAGNI (You Aren't Gonna Need It): không làm điểm mở rộng cho nhu cầu tưởng tượng.
  - Ví dụ: dựng hệ thống plugin cho nhiều cổng thanh toán khi dự án chỉ dùng một cổng và chưa có
    kế hoạch thêm.

*Cohesion và coupling*
- *Cohesion* (độ gắn kết) cao: những thứ thay đổi cùng nhau thì nằm cùng nhau.
  - Ví dụ: mọi code về tính phí ship nằm trong một module, không rải ở controller, model và view.
- *Coupling* (độ phụ thuộc) thấp: các module biết về nhau càng ít càng tốt.
  - Ví dụ: module đơn hàng chỉ gọi `Inventory::reserve()`, không đọc thẳng bảng tồn kho.
- Cách đo thô: một thay đổi nghiệp vụ phải sửa bao nhiêu file hay module. Càng nhiều thì
  cohesion càng thấp và coupling càng cao.

**Đọc**
- Sandi Metz: [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)
- *The Pragmatic Programmer*, 20th anniversary ed. (Thomas, Hunt): topic *The Evils of Duplication* và *Orthogonality*

**Nắm chắc khi**
- [ ] Phân biệt được trùng lặp ngẫu nhiên và trùng lặp tri thức trên một ví dụ thật
- [ ] Kể được một lần gộp code sai và cách tháo ra (inline lại rồi tách theo đúng lý do thay đổi)

---

### Chặng 2: Làm chủ 🟡

#### 2.1 OOP hiện đại trong PHP

**Vì sao cần học:** Module riêng cho người làm PHP. Nhiều câu hỏi như "getter/setter hay public
property", "value object viết thế nào" có câu trả lời khác hẳn từ PHP 8.1 trở đi. Người phỏng
vấn dùng chúng để xem bạn có cập nhật ngôn ngữ không, và code Laravel mới (enum cast, DTO
readonly) dùng các tính năng này hằng ngày.

**Học gì**

*Enum (8.1)*
- Enum là kiểu có một tập giá trị cố định, khai báo sẵn trong code. Dùng để thay *magic
  string/số* (chuỗi hay số mang ý nghĩa ngầm, ví dụ `status = 2` nghĩa là "đã thanh toán").
- Hai loại:
  - *Pure enum*: chỉ có tên case.
  - *Backed enum*: mỗi case gắn một giá trị `string` hoặc `int`, nên lưu DB và trả API được.
- Các method có sẵn của backed enum:
  - `from($v)` đổi giá trị thành case, ném lỗi nếu giá trị lạ.
  - `tryFrom($v)` giống vậy nhưng trả `null` khi giá trị lạ.
  - `cases()` trả danh sách mọi case.
- Enum có method, hằng số, implement được interface, nhưng không có state (không thêm property
  được).

  ```php
  enum OrderStatus: string
  {
      case Pending = 'pending';
      case Paid = 'paid';

      public function label(): string
      {
          return match ($this) {
              self::Pending => 'Chờ thanh toán',
              self::Paid => 'Đã thanh toán',
          };
      }
  }

  OrderStatus::from('paid');     // OrderStatus::Paid
  OrderStatus::tryFrom('xyz');   // null
  ```
- Trong Eloquent, *cast* tự đổi cột DB thành enum khi đọc và ngược lại khi ghi:
  `$casts = ['status' => OrderStatus::class]`.
- ⚠️ `match` trên enum mà thiếu nhánh chỉ lỗi lúc runtime (`UnhandledMatchError`), khi đúng case
  đó xuất hiện. Dùng PHPStan hoặc Psalm (công cụ *phân tích tĩnh*, đọc code mà không chạy) để bắt
  lỗi này trước khi deploy.

*readonly property (8.1) và readonly class (8.2)*
- Property `readonly` chỉ gán được đúng một lần, trong scope của class (thường là trong
  constructor). Gán lần hai là lỗi.
- `readonly class` biến mọi property của class thành readonly.
- ⚠️ Readonly là "nông": nếu property chứa object (hoặc array chứa object) thì chính object bên
  trong vẫn sửa được.
  - Ví dụ: `public readonly DateTime $paidAt`. Không gán lại `$paidAt` được, nhưng
    `$order->paidAt->modify('+1 day')` vẫn đổi được ngày.
- ⚠️ Kiểu viết `withX()` quen thuộc (clone rồi sửa một property) bị lỗi với readonly:

  ```php
  $copy = clone $this;
  $copy->amount = 500;                       // Error: không sửa được property readonly
  return clone($this, ['amount' => 500]);    // PHP 8.5: clone with, tạo bản sao và sửa luôn
  ```
  - Trước 8.5, cách thường dùng là gọi lại constructor với giá trị mới.

*Viết gọn: constructor promotion, named argument, first-class callable*
- *Constructor promotion* (8.0): khai báo property ngay trong tham số constructor, bớt code lặp.
  - Ví dụ: `public function __construct(public readonly int $amount) {}`.
- *Named argument* (8.0): gọi hàm theo tên tham số, không lo nhầm thứ tự.
  - Ví dụ: `new Money(amount: 100, currency: 'VND')`.
- Hai tính năng trên làm DTO và value object (module 2.5, 2.7) rất ngắn gọn.
- *First-class callable* (8.1): `strlen(...)` hay `$this->handle(...)` tạo ra một `Closure`
  (object hàm, truyền đi được như biến).
  - Thay cho cách cũ là chuỗi `'strlen'` hay mảng `[$this, 'handle']`, vốn IDE không kiểm tra
    được.
  - Hợp với Strategy dạng hàm (module 2.4): `array_map($this->normalize(...), $rows)`.

*Property hooks và asymmetric visibility (8.4)*
- *Property hook*: gắn logic vào lúc đọc (`get`) hoặc ghi (`set`) một property, ngay trên khai
  báo của nó.
  - Ví dụ: `public string $email { set => strtolower($value); }` tự chuyển email về chữ thường
    mỗi khi gán.
- *Asymmetric visibility*: quyền đọc và quyền ghi khác nhau.
  - Ví dụ: `public private(set) string $status;` thì ai cũng đọc được, nhưng chỉ code bên trong
    class mới sửa được.
- ⚠️ Hook có side effect nặng (gọi DB, phát event) làm một phép gán trông vô hại nhưng hành xử
  bất ngờ.

*Getter/setter hay public property*
- Lý do cũ để viết `getX()`/`setX()` là "phòng khi sau này cần thêm logic".
- Với hook, lý do đó không còn: sau này thêm hook vào property không phá API, code gọi vẫn viết
  `$user->email` như cũ.
- Nhưng thay đổi trạng thái có quy tắc vẫn nên là method nghiệp vụ.
  - Ví dụ: `$order->cancel()` kiểm tra "chỉ huỷ được khi chưa giao", tốt hơn `$order->status =
    'cancelled'` dù có hook.

*Đối chiếu Java/Go*
- Java: `record` (Java 16) cho object chỉ mang dữ liệu, bất biến. Field `private final` gán một
  lần, tương tự readonly.
- Go: struct truyền theo giá trị (gán hay truyền vào hàm là tạo bản sao). Field viết thường là
  private trong phạm vi package.

**Đọc**
- PHP: [Enumerations](https://www.php.net/manual/en/language.enumerations.php), [Readonly properties](https://www.php.net/manual/en/language.oop5.properties.php#language.oop5.properties.readonly-properties), [Readonly classes](https://www.php.net/manual/en/language.oop5.basic.php#language.oop5.basic.class.readonly), [First class callable syntax](https://www.php.net/manual/en/functions.first_class_callable_syntax.php), [Property Hooks](https://www.php.net/manual/en/language.oop5.property-hooks.php), [Asymmetric visibility](https://www.php.net/manual/en/language.oop5.visibility.php#language.oop5.visibility-members-aviz)
- Release notes: [PHP 8.4](https://www.php.net/releases/8.4/en.php), [PHP 8.5](https://www.php.net/releases/8.5/en.php) (pipe operator, clone with)

**Nắm chắc khi**
- [ ] Viết được enum `OrderStatus` backed string, có method `canTransitionTo()`, dùng làm cast Eloquent
- [ ] Viết được value object readonly có method `withX()` trả object mới, theo cả cách PHP 8.2 và PHP 8.5
- [ ] Bảo vệ được lựa chọn giữa public property + hook, asymmetric visibility và method nghiệp vụ cho một entity cụ thể
- [ ] Chỉ ra được vì sao một readonly class chứa `array` hoặc object vẫn chưa thật sự immutable

#### 2.2 Creational patterns

**Vì sao cần học:** Đây là nhóm pattern về cách tạo object. Hai câu hay gặp nhất là "Singleton
tốt hay xấu" và "`Carbon::parse()` có phải Factory Method không". Nếu dự án chạy Laravel Octane,
hiểu singleton sai nghĩa là rò dữ liệu của user này sang user khác, không còn là chuyện lý
thuyết.

**Học gì**

*Design pattern và nhóm creational*
- *Design pattern* là một lời giải đã được đặt tên cho một vấn đề thiết kế hay lặp lại. Cái tên
  giúp cả đội nói chuyện nhanh: nói "bọc bằng Decorator" là ai cũng hiểu.
- Sách GoF gom 23 pattern thành ba nhóm:
  - *Creational*: cách tạo object (module này).
  - *Structural*: cách ghép các object với nhau (module 2.3).
  - *Behavioral*: cách chia hành vi giữa các object (module 2.4).

*Singleton*
- Singleton đảm bảo cả chương trình chỉ có một instance của một class.
- Kiểu cổ điển dùng biến static:

  ```php
  final class Config
  {
      private static ?self $instance = null;

      public static function getInstance(): self
      {
          return self::$instance ??= new self();
      }
  }
  ```
- ⚠️ Vấn đề của kiểu cổ điển:
  - Là state toàn cục: code nào cũng đọc và sửa được.
  - Giấu dependency: nhìn constructor của một class không biết nó dùng `Config`.
  - Khó thay bằng bản giả khi test.
  - Rò state giữa các request khi chạy Octane (xem nhóm dưới).
- Singleton **do container quản lý** và được inject vào thì ổn:
  `$this->app->singleton(ExchangeRateClient::class)` rồi nhận qua constructor. Đây là
  singleton "theo container", không phải kiểu GoF cổ điển.

*Octane và state theo request*
- PHP-FPM dựng lại toàn bộ app cho mỗi request, nên state không bao giờ sống sang request sau.
- Laravel Octane khởi động app một lần rồi dùng nó phục vụ rất nhiều request. Service đăng ký
  bằng `singleton` sống qua tất cả các request đó.
- Chuỗi sự cố điển hình:
  1. `CartService` là singleton, lưu user hiện tại vào property lúc được tạo.
  2. Request đầu tiên (user A) tạo `CartService`, property chứa user A.
  3. Request sau (user B) nhận lại đúng object đó và thấy giỏ hàng của user A.
- Quy tắc: singleton không được giữ state của request (user hiện tại, object request). Thứ gì
  theo request thì đăng ký bằng `scoped()`: mỗi request một instance, bị bỏ đi khi request kết
  thúc.

*Factory Method và static factory*
- *Factory Method* (GoF): class cha định nghĩa khung, còn việc tạo object cụ thể nào thì giao
  cho một method mà class con override.
  - Ví dụ Laravel: `Illuminate\Support\Manager` là class cha. `CacheManager`, `MailManager` định
    nghĩa các method `createXxxDriver()` (`createRedisDriver()`, `createFileDriver()`...), và
    Manager gọi đúng method theo tên driver trong config.
  - Ví dụ Java: `Collection.iterator()`, mỗi loại collection trả `Iterator` của riêng nó.
- *Static factory method*: một hàm static tạo object và có tên dễ hiểu, dùng thay constructor.
  - Ví dụ: `Carbon::parse()`, `Calendar.getInstance()`, `List.of()` trong Java, các hàm
    `NewXxx()` trong Go.
- ⚠️ Static factory method **không phải** Factory Method của GoF. Nó chỉ là "hàm tạo có tên"
  (*Effective Java* item 1). Factory Method của GoF dựa vào việc class con override.

*Abstract Factory và Builder*
- *Abstract Factory*: một object chuyên tạo cả một họ object liên quan, đảm bảo chúng đi cùng
  nhau.
  - Ví dụ PHP: PSR-17 HTTP factories. Một thư viện cung cấp các factory tạo request, response,
    stream cùng một bộ, code của bạn chỉ phụ thuộc interface PSR-17.
- *Builder*: dựng object phức tạp qua từng bước, cuối cùng mới tạo ra kết quả.
  - Ví dụ Laravel: query builder `DB::table('orders')->where('status', 'paid')->orderBy('id')
    ->get()`, và cách dựng một `Mail` message qua nhiều method.

*Đối chiếu Java/Go*

| Pattern | Mục đích | Laravel / PHP | Java | Go |
|---|---|---|---|---|
| Singleton | Một instance duy nhất | `$app->singleton()` (theo container, không phải GoF cổ điển) | Bean scope singleton | Biến package + `sync.Once` |
| Factory Method | Class con quyết định tạo object nào qua một method được override | `Illuminate\Support\Manager`: `CacheManager`, `MailManager` định nghĩa `createXxxDriver()` | `Collection.iterator()`: mỗi collection trả `Iterator` của riêng nó | Không có dạng kế thừa; gần nhất là truyền hàm factory `func() T` hoặc method interface trả interface |
| Abstract Factory | Tạo họ object liên quan | PSR-17 HTTP factories | `DocumentBuilderFactory` | Interface có nhiều method tạo object (ít gặp) |
| Builder | Dựng object phức tạp từng bước | Query builder, `Mail` message | `HttpRequest.newBuilder()` | Functional options `NewServer(WithTimeout(...))` |

- *Functional options* trong Go: truyền vào constructor một loạt hàm, mỗi hàm chỉnh một tuỳ chọn.
  Go dùng cách này thay builder vì không có tham số tuỳ chọn hay named argument.

**Đọc**
- Refactoring.Guru: [Factory Method](https://refactoring.guru/design-patterns/factory-method), [Abstract Factory](https://refactoring.guru/design-patterns/abstract-factory), [Builder](https://refactoring.guru/design-patterns/builder), [Singleton](https://refactoring.guru/design-patterns/singleton)
- Mã nguồn Laravel: `vendor/laravel/framework/src/Illuminate/Support/Manager.php` (method `createDriver()`)
- Laravel: [Binding Scoped Singletons](https://laravel.com/docs/container#binding-scoped), [Octane: Dependency Injection](https://laravel.com/docs/octane#dependency-injection-and-octane)
- *Effective Java* item 1 (*Consider static factory methods instead of constructors*)

**Nắm chắc khi**
- [ ] Giải thích được vì sao `Calendar.getInstance()` là static factory chứ không phải Factory Method, và chỉ ra một Factory Method thật trong Laravel
- [ ] Chỉ ra được một singleton trong app Laravel của mình sẽ rò dữ liệu giữa request khi chạy Octane
- [ ] Viết được functional options trong Go và builder trong PHP cho cùng một object cấu hình

#### 2.3 Structural patterns

**Vì sao cần học:** Nhóm pattern về cách ghép object, gặp hằng ngày khi bọc SDK bên thứ ba hay
thêm cache cho repository mà không sửa code gọi. Người phỏng vấn rất hay hỏi "Decorator và Proxy
khác gì", "Facade của Laravel có phải Facade GoF không", "middleware là pattern gì".

**Học gì**

*Adapter*
- Adapter đổi interface của một thứ có sẵn cho khớp với interface mình cần.
- Ví dụ:
  - Bọc SDK của cổng thanh toán (mỗi SDK một kiểu hàm) thành interface `PaymentGateway` chung.
  - Flysystem: mỗi adapter (S3, local) làm cho một kiểu lưu trữ khớp với cùng một interface
    filesystem, nên `Storage::disk('s3')` và `Storage::disk('local')` dùng y như nhau.

*Facade (theo GoF)*
- Facade tạo một giao diện mới, đơn giản, đứng trước một hệ con phức tạp.
- Ví dụ: một service class `CheckoutService::checkout()` gói nhiều bước (tính giá, giữ kho, thu
  tiền) sau một method.
- Khác Adapter:
  - Adapter làm khớp với một interface **đã có**.
  - Facade tạo ra một interface **mới**, đơn giản hơn.

*Decorator*
- Decorator bọc một object để thêm hành vi, và có **cùng interface** với object được bọc. Code
  gọi không biết mình đang dùng bản bọc hay bản gốc.
- Ví dụ: `CachedOrderRepository` bọc repository thật và thêm cache.

  ```php
  final class CachedOrderRepository implements OrderRepository
  {
      public function __construct(
          private OrderRepository $inner,
          private CacheRepository $cache,
      ) {}

      public function find(int $id): ?Order
      {
          return $this->cache->remember("order:$id", 60, fn () => $this->inner->find($id));
      }
  }
  ```
- Laravel có `$this->app->extend()` để bọc một binding đã đăng ký bằng decorator, không phải sửa
  chỗ nào đang dùng nó.

*Proxy*
- Proxy là object đứng thay cho object thật để kiểm soát việc truy cập tới nó. Các mục đích
  thường gặp:
  - *Lazy*: chỉ tạo hoặc nạp object thật khi thật sự cần. Ví dụ quan hệ Eloquent `$order->customer`
    chỉ query khi bạn truy cập. PHP 8.4 có sẵn lazy object (`ReflectionClass::newLazyProxy`).
  - Cache, hoặc gọi tới object nằm ở máy khác (*remote*).
- Ví dụ Java: `@Transactional` của Spring hoạt động nhờ một proxy bọc bean, mở transaction trước
  khi gọi method thật.
- Khác Decorator:
  - Cấu trúc giống hệt (cùng interface, bọc object thật).
  - Decorator để **thêm hành vi**, Proxy để **kiểm soát truy cập**.

*Composite*
- Composite tổ chức object thành cây, và xử lý một lá (object đơn) giống hệt một nhóm.
- Ví dụ: rule validation lồng nhau (một rule "và" chứa nhiều rule con, gọi `validate()` như một
  rule đơn), menu nhiều cấp.

*Hai chữ dễ nhầm trong Laravel*
- ⚠️ "Facade" của Laravel **không phải** Facade GoF. Nó là một static proxy tới object nằm trong
  container, tức một dạng service locator (xem 2.6). Khi gọi `Cache::get('k')`:
  1. PHP không tìm thấy static method `get` trên class `Cache`, nên gọi `__callStatic()`.
  2. Facade lấy tên binding (`'cache'`) từ `getFacadeAccessor()`.
  3. Facade hỏi container object thật ứng với tên đó.
  4. Facade gọi `get('k')` trên object thật.
- ⚠️ Middleware của Laravel là Chain of Responsibility (qua class `Pipeline`, module 2.4), không
  phải Decorator. Còn middleware kiểu Go `func(http.Handler) http.Handler` thì là Decorator.

*Đối chiếu Java/Go*

| Pattern | Mục đích | Laravel / PHP | Java | Go |
|---|---|---|---|---|
| Adapter | Đổi interface của thứ có sẵn cho khớp interface mình cần | Flysystem adapter (S3, local), bọc SDK cổng thanh toán | `InputStreamReader` | `http.HandlerFunc` biến func thành `Handler` |
| Decorator | Bọc object để thêm hành vi, cùng interface | `CachedRepository` bọc repository; `$this->app->extend()` | `BufferedInputStream` | `bufio.NewReader(r)`, middleware `func(http.Handler) http.Handler` |
| Facade (GoF) | Một giao diện đơn giản cho hệ con phức tạp | Service class gom nhiều bước | `JdbcTemplate` | `http.Get` gói `Client`, `Request`, `Transport` |
| Proxy | Đại diện, kiểm soát truy cập (lazy, cache, remote) | Lazy relationship, lazy object (PHP 8.4 `ReflectionClass::newLazyProxy`) | AOP proxy của `@Transactional`, Hibernate lazy proxy | `httputil.ReverseProxy` (mức mạng) |
| Composite | Cây object, xử lý lá và nhóm như nhau | Rule validation lồng nhau, menu | `CompositeCacheManager` | `io.MultiWriter`, `errors.Join` |

**Đọc**
- Refactoring.Guru: [Adapter](https://refactoring.guru/design-patterns/adapter), [Decorator](https://refactoring.guru/design-patterns/decorator), [Facade](https://refactoring.guru/design-patterns/facade), [Proxy](https://refactoring.guru/design-patterns/proxy), [Composite](https://refactoring.guru/design-patterns/composite)
- Laravel: [Facades](https://laravel.com/docs/facades) (đọc mục *How Facades Work* và *Facades vs. Dependency Injection*), [Extending Bindings](https://laravel.com/docs/container#extending-bindings)

**Nắm chắc khi**
- [ ] Viết được `CachedOrderRepository` bọc repository thật và đăng ký bằng `extend()` mà không sửa code gọi
- [ ] Giải thích được `Cache::get()` đi qua những bước nào để tới object thật
- [ ] Viết cùng một middleware log thời gian bằng Go (Decorator) và PHP (Pipeline), rồi so sánh (bài tập 3)

#### 2.4 Behavioral patterns

**Vì sao cần học:** Nhóm pattern về cách chia hành vi, và Laravel dùng gần như tất cả: queue job,
event, middleware, driver. Hay bị hỏi "Strategy và State khác gì", "Observer có bẫy gì". Ở mức
senior, Visitor và cách Java 21 thay thế nó là câu phân loại ứng viên.

**Học gì**

*Strategy và Template Method*
- *Strategy*: tách một thuật toán thành object riêng để hoán đổi được lúc runtime. Code gọi (client)
  tự chọn strategy nào.
  - Ví dụ: chọn `PaymentGateway` theo lựa chọn của khách. Driver cache/queue của Laravel cũng là
    Strategy.
- *Template Method*: class cha cố định khung các bước, class con định nghĩa một vài bước bên
  trong.
  - Ví dụ: base class `ReportExporter::export()` luôn chạy "lấy dữ liệu → định dạng → ghi file",
    class con chỉ viết `format()` cho CSV hay Excel.
- Khác nhau ở cơ chế:
  - Template Method dùng kế thừa.
  - Strategy dùng composition.
  - Go không có kế thừa nên viết Template Method thành "hàm khung nhận interface".

*State*
- State: hành vi của object đổi theo trạng thái, mỗi trạng thái là một class. Object tự chuyển
  từ trạng thái này sang trạng thái khác.
  - Ví dụ: đơn hàng `Pending` thì `cancel()` được, `Shipped` thì `cancel()` ném lỗi. Thư viện
    `spatie/laravel-model-states` làm theo cách này.
- Khác Strategy:
  - Strategy do client chọn từ bên ngoài.
  - State tự chuyển giữa các trạng thái từ bên trong.

*Observer*
- Observer: một sự kiện xảy ra, nhiều bên đang "lắng nghe" được báo. Bên phát không cần biết có
  những ai nghe.
  - Ví dụ Laravel: Event/Listener, model observer (`OrderObserver::created()`).
- ⚠️ Khi listener chạy đồng bộ (cùng request với bên phát):
  - Listener chậm làm chậm luôn bên phát.
  - Listener ném lỗi làm hỏng luồng chính.
  - Thứ tự chạy các listener khó kiểm soát, và event này kích hoạt event kia có thể thành vòng
    lặp.
- ⚠️ Model observer ẩn là nguồn side effect khó đoán: gọi `$order->save()` mà không biết sẽ có
  mail gửi đi hay kho bị trừ.

*Command và Chain of Responsibility*
- *Command*: gói một yêu cầu thành object, để xếp hàng, retry hay undo được.
  - Ví dụ Laravel: queue job (`SendInvoiceMail` là object, được đẩy vào queue rồi chạy sau),
    Artisan command.
- *Chain of Responsibility*: một chuỗi handler, mỗi handler xử lý yêu cầu hoặc chuyển tiếp cho
  handler sau.
  - Ví dụ Laravel: middleware chạy qua `Pipeline`. Middleware `auth` có thể dừng chuỗi và trả 401,
    hoặc gọi `$next($request)` để chuyển tiếp.

*Iterator*
- Iterator cho phép duyệt từng phần tử mà không lộ cấu trúc bên trong.
- Ví dụ PHP:
  - Interface `Iterator` có sẵn.
  - `Generator`: hàm dùng `yield` trả từng phần tử một, không cần nạp hết vào RAM.
  - `LazyCollection` của Laravel dựa trên generator, dùng để duyệt bảng lớn.

*Visitor và cách thay thế hiện đại*
- Visitor giải bài toán: có một cây object với các loại node cố định, cần thêm phép toán mới
  (in ra, kiểm tra, biến đổi) mà không sửa các class node.
- Cách làm là *double dispatch*: code chạy ra tuỳ vào cả hai thứ, loại node và loại visitor.
  1. Mỗi node có method `accept($visitor)`.
  2. Trong `accept`, node gọi lại đúng method dành cho loại của mình, ví dụ
     `$visitor->visitClassMethod($this)`.
  3. Mỗi phép toán mới là một class visitor mới.
- Ví dụ thật: `NodeVisitor` của `nikic/php-parser`, nền của PHPStan và Rector.
- Visitor đổi hướng mở rộng:
  - Thêm phép toán mới thì dễ (thêm một visitor).
  - Thêm loại node mới thì khó (phải sửa mọi visitor).
- Java 21 thay Visitor bằng `sealed interface` (interface chỉ cho phép một danh sách class cố
  định implement) cộng `switch` pattern matching:

  ```java
  sealed interface Notice permits Email, Sms {}
  record Email(String to) implements Notice {}
  record Sms(String phone) implements Notice {}

  String channel(Notice n) {
      return switch (n) {
          case Email(String to) -> "mail:" + to;     // record pattern tách luôn field
          case Sms(String phone) -> "sms:" + phone;
      };   // thiếu một nhánh thì compiler báo lỗi, không cần accept()/visit()
  }
  ```
- PHP chưa có sealed class:
  - Tập giá trị đóng thì dùng enum + `match`.
  - Tập class thì dùng `match (true)` với `instanceof`, và dựa vào PHPStan để bắt thiếu nhánh.
- Go dùng *type switch* trên interface, nhưng không có kiểm tra đủ nhánh lúc compile.

*Đối chiếu Java/Go*

| Pattern | Mục đích | Laravel / PHP | Java | Go |
|---|---|---|---|---|
| Strategy | Hoán đổi thuật toán lúc runtime | Payment gateway, driver cache/queue | `Comparator` | `sort.Slice(s, less)`, interface nhỏ |
| Observer | Một sự kiện, nhiều bên lắng nghe | Event/Listener, model observer | `@EventListener` | Callback list, channel |
| Command | Gói yêu cầu thành object (xếp hàng, retry, undo) | Queue job, Artisan command | `Runnable`, `Callable` | `func()` gửi qua channel |
| Chain of Responsibility | Chuỗi handler, mỗi cái xử lý hoặc chuyển tiếp | Middleware, `Pipeline` | Servlet filter, Spring Security filter chain | Chuỗi middleware |
| Template Method | Khung cố định, bước con do class con định nghĩa | Base class có hook | `AbstractList` | `sort.Sort` (khung cố định, `Len/Less/Swap` là bước con) |
| State | Hành vi đổi theo trạng thái, mỗi trạng thái một class | `spatie/laravel-model-states` | Enum có method, state machine | Hàm trạng thái trả hàm trạng thái kế tiếp |
| Iterator | Duyệt không lộ cấu trúc bên trong | `Iterator`, `Generator`, `LazyCollection` | `Iterator`, `Spliterator` | `range`, `sql.Rows.Next()`, `iter.Seq` (1.23) |
| Visitor | Thêm phép toán mới trên một cây object mà không sửa các class trong cây (double dispatch) | `nikic/php-parser` `NodeVisitor` (nền của PHPStan, Rector) | `FileVisitor` của `Files.walkFileTree` | `ast.Visitor` + `ast.Walk` |

**Đọc**
- Refactoring.Guru: [Strategy](https://refactoring.guru/design-patterns/strategy), [Observer](https://refactoring.guru/design-patterns/observer), [Command](https://refactoring.guru/design-patterns/command), [Chain of Responsibility](https://refactoring.guru/design-patterns/chain-of-responsibility), [Template Method](https://refactoring.guru/design-patterns/template-method), [State](https://refactoring.guru/design-patterns/state), [Visitor](https://refactoring.guru/design-patterns/visitor)
- Java: [JEP 409: Sealed Classes](https://openjdk.org/jeps/409), [JEP 441: Pattern Matching for switch](https://openjdk.org/jeps/441), [JEP 440: Record Patterns](https://openjdk.org/jeps/440)
- PHP: [`match`](https://www.php.net/manual/en/control-structures.match.php); [spatie/laravel-model-states](https://spatie.be/docs/laravel-model-states); [nikic/PHP-Parser](https://github.com/nikic/PHP-Parser) (đọc phần *Node traversation* trong docs)
- Laravel: [Pipeline](https://laravel.com/docs/helpers#pipeline), [Events](https://laravel.com/docs/events)

**Nắm chắc khi**
- [ ] Nhận ra được 5 pattern trong mã nguồn Laravel và ghi đường dẫn file (bài tập 4)
- [ ] Viết được cùng một phép tính (diện tích, hoặc tính phí cho các loại đơn) theo Visitor và theo sealed + pattern matching / enum + `match`, và nói hướng mở rộng nào dễ ở mỗi cách
- [ ] Mô hình hoá được trạng thái đơn hàng bằng State pattern hoặc enum có `canTransitionTo()`, và chọn được cách nào cho bài toán cụ thể

#### 2.5 Pattern tầng dữ liệu

**Vì sao cần học:** "Có nên dùng Repository trong Laravel không" là tranh luận gặp ở hầu hết các
đội PHP, và là câu phỏng vấn phổ biến. Hiểu Eloquent thiếu gì so với Doctrine hay Hibernate giúp
bạn tránh bug khi một nghiệp vụ sửa nhiều model cùng lúc.

**Học gì**

*Active Record và Data Mapper*
- *Active Record* (AR): mỗi object vừa mang dữ liệu của một dòng trong bảng, vừa tự biết lưu
  mình (`$order->save()`). Eloquent và Rails dùng cách này.
- *Data Mapper* (DM): *entity* (object nghiệp vụ) là class thuần, không biết gì về DB. Một
  *mapper* riêng lo việc đọc và ghi. Doctrine và Hibernate/JPA dùng cách này.

| Tiêu chí | Active Record | Data Mapper |
|---|---|---|
| Lượng code | Ít, làm nhanh | Nhiều hơn, nhiều khái niệm hơn |
| Hợp với | CRUD, nghiệp vụ đơn giản | Domain phức tạp |
| Domain và schema | Dính nhau: model phản chiếu bảng | Tách rời |
| Test không cần DB | Khó | Dễ |
| Rủi ro | Model béo dần (chứa mọi thứ) | Tốn công dựng lúc đầu |

*Repository*
- Repository là một giao diện giống collection (`find`, `add`, `matching`) cho một *aggregate*
  (một cụm entity luôn được lưu và kiểm tra cùng nhau, ví dụ `Order` cùng các dòng hàng). Nó giấu
  cách lưu trữ.
- ⚠️ Trong Laravel: repository bọc Eloquent 1-1 (`all()`, `find()`, `create()`) mà vẫn trả về
  model Eloquent thì không giấu được gì. Code gọi vẫn dùng được mọi method của Eloquent.
- Repository đáng làm khi:
  - Query phức tạp, cần đặt tên và gom về một chỗ.
  - Dữ liệu đến từ nhiều nguồn (DB, API, cache).
  - Domain cần test mà không có DB.
- ⚠️ *Generic repository* 30 method dùng chung cho mọi entity vi phạm ISP (module 1.3).

*Unit of Work và Identity Map*
- *Unit of Work*: ghi nhận mọi thay đổi trong một phiên làm việc, rồi ghi xuống DB một lần trong
  một transaction.
  - Ví dụ: Doctrine `flush()`, JPA `EntityManager`.
  - Eloquent **không** có: mỗi `save()` ghi xuống DB ngay. Sửa ba model trong một nghiệp vụ là
    ba lần ghi riêng, muốn "cùng thành công hoặc cùng huỷ" thì phải tự bọc `DB::transaction()`.
- *Identity Map*: trong một phiên, mỗi id chỉ ứng với một object trong bộ nhớ.
  - Ví dụ: persistence context của Hibernate.
  - Eloquent không có, nên `Order::find(1)` gọi hai lần ra hai object khác nhau. Sửa object này
    thì object kia không biết, và `save()` cả hai thì bản lưu sau ghi đè bản trước.

*DTO*
- *DTO* (Data Transfer Object): object chỉ mang dữ liệu qua một ranh giới (từ HTTP vào service,
  từ service ra API), không có logic.
- Viết bằng PHP readonly class, Java `record`, Go struct.
- ⚠️ `array $data` được truyền đi khắp nơi là primitive obsession ở mức cấu trúc: không ai biết
  mảng có key nào, kiểu gì, và IDE không giúp được.
  - *Primitive obsession*: dùng kiểu nguyên thủy (string, int, array) cho thứ đáng có kiểu riêng
    (module 2.7).

*Specification*
- Specification là một điều kiện nghiệp vụ đóng gói thành object, ghép được với nhau bằng
  `and`/`or`/`not`.
  - Ví dụ: "khách VIP" và "đơn quá hạn" là hai specification, ghép thành "đơn quá hạn của khách
    VIP".
- Ở Laravel, gần nhất là query scope (`Order::overdue()->vip()`) hoặc một class filter.
- Chỉ đáng làm khi điều kiện phức tạp và được tái dùng ở nhiều nơi.

Tầng SQL và Eloquent chi tiết: [03-database-sql.md](03-database-sql.md).

**Đọc**
- PoEAA catalog: [Active Record](https://martinfowler.com/eaaCatalog/activeRecord.html), [Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html), [Repository](https://martinfowler.com/eaaCatalog/repository.html), [Unit of Work](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- Laravel: [Query Scopes](https://laravel.com/docs/eloquent#query-scopes)

**Nắm chắc khi**
- [ ] Tranh luận được "có nên dùng Repository trong Laravel" với cả hai phía, gắn với một dự án cụ thể
- [ ] Giải thích được hệ quả của việc Eloquent không có Unit of Work và Identity Map khi sửa nhiều model trong một nghiệp vụ
- [ ] Viết được DTO readonly cho một request tạo đơn và map từ FormRequest sang DTO

#### 2.6 DI, IoC container và Service Locator

**Vì sao cần học:** Service container là trái tim của Laravel: controller, job, listener đều được
nó tạo ra. Hiểu nó giúp bạn viết code test được và đọc được framework. Câu hỏi hay gặp là "DI và
Service Locator khác gì" và "Facade thuộc loại nào".

**Học gì**

*IoC và DI*
- *IoC* (Inversion of Control, đảo ngược điều khiển): thay vì code của bạn gọi framework, framework
  gọi code của bạn.
  - Ví dụ: bạn không tự gọi controller. Laravel nhận request, tạo controller và gọi method của nó.
- *DI* (Dependency Injection): *dependency* (object mà class cần để làm việc) được truyền vào từ
  bên ngoài, thay vì class tự `new` ra.

*Các cách inject*
- Ba cách truyền dependency:
  - Qua constructor.
  - Qua setter.
  - Qua tham số của method.
- Constructor injection là mặc định, vì:
  - Dependency hiện rõ ngay ở chữ ký constructor.
  - Object tạo ra luôn hợp lệ, không có lúc "chưa set dependency".
  - Khi test, truyền fake trực tiếp vào constructor, không cần framework.

*Laravel container*
- *Auto-wiring*: container đọc kiểu các tham số của constructor bằng *reflection* (khả năng của
  PHP tự đọc cấu trúc class lúc runtime), rồi tự tạo và truyền dependency vào.
- Ba cách đăng ký:

| Cách | Số instance | Dùng khi |
|---|---|---|
| `bind` | Mỗi lần resolve tạo mới | Object rẻ, không giữ state dùng chung |
| `singleton` | Một cho cả vòng đời app | Client HTTP, object đắt để tạo, không giữ state của request |
| `scoped` | Một cho mỗi request (hoặc job) | State theo request, nhất là khi chạy Octane |

- *Contextual binding*: cùng một interface, mỗi class nhận một implementation khác nhau.
  - Cú pháp: `$this->app->when(PhotoController::class)->needs(Filesystem::class)->give(...)`.
- *Tagging*: gắn nhãn cho nhiều binding, rồi lấy cả nhóm bằng `$app->tagged('reports')`.
- *Method injection*: Laravel inject cả vào tham số method của controller, `handle()` của job.

*Service Locator*
- ⚠️ Service Locator: code tự hỏi một registry toàn cục để lấy dependency, ví dụ `app(X::class)`,
  `resolve()` trong PHP, `getBean()` trong Spring.
- Vấn đề:
  - Dependency bị ẩn: nhìn constructor không biết class cần gì.
  - Thiếu binding chỉ lộ ra lúc runtime, khi đúng dòng đó chạy.
  - Test phải dựng cả container.
- Chấp nhận được ở:
  - *Composition root*: nơi duy nhất lắp ráp các object với nhau (service provider trong Laravel,
    hàm `main` trong Go).
  - Factory, và code của framework.

*Facade và helper của Laravel*
- Facade (`Cache::get()`) và helper (`app()`, `cache()`) là service locator tiện lợi.
- Dùng trong controller, route thì ổn. Trong domain logic (code nghiệp vụ) thì nên inject.
- Facade vẫn test được nhờ `Facade::fake()` hoặc `shouldReceive()`, nhưng dependency vẫn ẩn.

*Đối chiếu Java/Go*
- Go: nối tay các dependency trong `main` (composition root). Khi đồ thị dependency lớn thì dùng
  Wire hoặc Fx.
- Java: Spring IoC container.

**Đọc**
- Martin Fowler: [Inversion of Control Containers and the Dependency Injection pattern](https://martinfowler.com/articles/injection.html) (có phần so sánh với Service Locator)
- Laravel: [Service Container](https://laravel.com/docs/container) (đọc hết), [Facades vs. Dependency Injection](https://laravel.com/docs/facades#facades-vs-dependency-injection)
- [PSR-11: Container interface](https://www.php-fig.org/psr/psr-11/) (đọc phần meta về việc không dùng container như service locator)

**Nắm chắc khi**
- [ ] Phân biệt được DIP, DI và IoC container trong một câu mỗi cái
- [ ] Viết được contextual binding: hai controller nhận hai implementation khác nhau của cùng interface
- [ ] Chỉ ra được chỗ dùng Facade trong domain logic của dự án mình và viết lại bằng constructor injection

#### 2.7 Value object, immutability, Law of Demeter

**Vì sao cần học:** Tiền, email, khoảng thời gian là nơi bug nghiệp vụ hay xảy ra nhất, và value
object là cách chặn bug ngay khi tạo dữ liệu. Carbon mutable là bẫy mà hầu như dev Laravel nào
cũng từng dính. Law of Demeter và tell don't ask hay được hỏi để xem bạn giữ invariant ở đâu.

**Học gì**

*Value object*
- *Entity* là object được nhận diện bằng id: hai khách hàng trùng tên vẫn là hai người khác nhau.
- *Value object* là object được nhận diện bằng giá trị: hai tờ 100.000đ là như nhau.
  - Ví dụ: `Money`, `Email`, `DateRange`.
- Ba đặc điểm:
  - Validate ngay lúc tạo: không tồn tại `Email` sai định dạng.
  - So sánh theo giá trị, không theo object.
  - Mọi thao tác trả về object mới, không sửa object cũ.
- Chống primitive obsession: `transfer(Money $amount)` thay vì
  `transfer(int $amount, string $currency)`. Không thể truyền nhầm đơn vị tiền hay quên truyền.

*Immutability*
- *Immutable* (bất biến): tạo xong thì không đổi được nữa.
- Lợi ích:
  - Chia sẻ an toàn: đưa object cho code khác mà không sợ bị sửa sau lưng.
  - Dễ suy luận: giá trị lúc tạo là giá trị mãi mãi.
  - Dùng làm key (của cache, của map) được.

*Hai bẫy trong PHP*
- ⚠️ Carbon mặc định là mutable: `$d->addDay()` sửa chính object `$d`.

  ```php
  $issuedAt = Carbon::parse('2026-09-01');
  $dueAt = $issuedAt->addDays(30);
  // $issuedAt giờ cũng là 2026-10-01: ngày phát hành hoá đơn bị đổi theo
  ```
  - Dùng `CarbonImmutable`. Trong Laravel có thể đặt mặc định cho cả app:
    `Date::use(CarbonImmutable::class)`.
- ⚠️ Tiền không dùng `float`: xem [22-practical-data.md](22-practical-data.md).

*Law of Demeter*
- Law of Demeter: chỉ nói chuyện với "bạn trực tiếp", không với "bạn của bạn".
- Ví dụ vi phạm: `$order->getCustomer()->getAddress()->getCity()`. Code này phụ thuộc vào cấu
  trúc của ba class, một class đổi là vỡ.
  - Cách sửa: `$order->shippingCity()`.
- Không áp cho fluent API hay builder (`$query->where()->orderBy()->limit()`), vì mỗi lời gọi trả
  về cùng một object.

*Tell don't ask và command-query separation*
- *Tell don't ask*: bảo object làm việc, thay vì hỏi dữ liệu của nó rồi tự quyết định bên ngoài.
  - Ví dụ: `$account->withdraw($x)` thay vì đọc số dư, tự kiểm tra, rồi set số dư mới từ bên
    ngoài. Nhờ vậy invariant "số dư không âm" nằm trong object.
- *Command-query separation*: một hàm hoặc đổi state (command), hoặc trả dữ liệu (query), không
  làm cả hai.
  - ⚠️ `getUser()` mà tự tạo user khi chưa có là side effect bất ngờ: người gọi nghĩ chỉ đọc.

**Đọc**
- Martin Fowler: [Value Object](https://martinfowler.com/bliki/ValueObject.html), [Tell Don't Ask](https://martinfowler.com/bliki/TellDontAsk.html)
- *Effective Java* item 17 (*Minimize mutability*)

**Nắm chắc khi**
- [ ] Viết được `Money` chia đều cho N người không mất đồng nào, không dùng `float` (bài tập 5)
- [ ] Tái hiện được bug do Carbon mutable trong một hàm tính hạn thanh toán
- [ ] Viết lại được một đoạn "ask then set" thành method nghiệp vụ giữ invariant

---

### Chặng 3: Senior 🔴

#### 3.1 Clean code và code smell

**Vì sao cần học:** Ở mức senior, bạn là người review code của người khác, và cần gọi đúng tên
vấn đề thay vì nói "code này khó đọc". Câu phỏng vấn thường cho một đoạn controller dài rồi hỏi
"bạn thấy gì và sửa theo thứ tự nào".

**Học gì**

*Đặt tên*
- Tên nói lên ý định: `activeUsersWithUnpaidInvoices()` tốt hơn `getData2()`.
- Boolean đặt dạng `isX`, `hasX`, `canX`: `isPaid`, `hasShipped`, `canRefund`.
- Một khái niệm một từ: đừng lẫn `fetch`, `get`, `retrieve` cho cùng một kiểu việc.
- Dùng ngôn ngữ của nghiệp vụ: nếu phòng kế toán gọi là "phiếu thu" thì code nên có `Receipt`,
  không phải `MoneyRecord`.

*Hàm*
- Một hàm làm một việc, ở một mức trừu tượng. Đừng trộn "tính chiết khấu" với "nối chuỗi SQL"
  trong cùng một hàm.
- *Guard clause*: kiểm tra điều kiện không hợp lệ và `return` sớm, thay cho `if` lồng sâu.

  ```php
  // if lồng sâu
  if ($order !== null) {
      if ($order->isPaid()) {
          if (! $order->isShipped()) {
              $this->ship($order);
          }
      }
  }

  // guard clause
  if ($order === null || ! $order->isPaid() || $order->isShipped()) {
      return;
  }
  $this->ship($order);
  ```
- Comment giải thích **vì sao**, không giải thích code đang làm gì (code đã nói điều đó).
  - Ví dụ comment tốt: `// VNPay trả mã 24 khi khách tự huỷ, không coi là lỗi`.

*Tham số*
- ⚠️ Tham số boolean như `render(true)` thường báo hiệu hàm đang làm hai việc. Người đọc lời gọi
  không biết `true` nghĩa là gì. Tách thành hai hàm có tên rõ.
- Quá 3–4 tham số thì gom thành một object (DTO hoặc value object).

*Code smell và hướng sửa*
- *Code smell* (mùi code) là dấu hiệu bề mặt cho thấy thiết kế có thể có vấn đề. Nó chưa chắc là
  bug, nhưng đáng xem kỹ.
- Mỗi smell có kỹ thuật refactoring tương ứng (module 3.2):

| Smell | Dấu hiệu | Hướng sửa |
|---|---|---|
| Long method | Hàm hàng trăm dòng, comment chia đoạn | Extract function |
| God class / large class | `UserService` 3.000 dòng, 40 dependency | Extract class theo trách nhiệm |
| Feature envy | Method dùng dữ liệu class khác nhiều hơn của mình | Move function |
| Primitive obsession | Tiền là `float`, trạng thái là số ma thuật | Value object, enum |
| Shotgun surgery | Một thay đổi phải sửa 10 file | Gom trách nhiệm về một chỗ |
| Divergent change | Một class bị sửa vì nhiều lý do | Tách class (SRP) |
| Long parameter list, data clumps | 7 tham số, cùng nhóm tham số đi cùng nhau | Introduce parameter object |
| Repeated switches | Cùng `switch ($type)` ở nhiều nơi | Replace conditional with polymorphism |
| Speculative generality, dead code | Hook "để sau này", code không ai gọi | Xoá (git còn lịch sử) |

- Hai smell hay bị nhầm:
  - Shotgun surgery: **một** thay đổi phải sửa **nhiều** class.
  - Divergent change: **một** class bị sửa vì **nhiều** thay đổi khác nhau.

**Đọc**
- *Refactoring* 2nd ed., ch.3 *Bad Smells in Code*; Refactoring.Guru: [Code Smells](https://refactoring.guru/refactoring/smells)
- *Clean Code* (Robert C. Martin): ch.2 (tên), ch.3 (hàm). Đọc có phê phán: một số lời khuyên (hàm cực ngắn) bị tranh cãi nhiều

**Nắm chắc khi**
- [ ] Liệt kê được code smell trong controller/service dài nhất dự án mình và kế hoạch refactor từng bước (bài tập 1)
- [ ] Gọi đúng tên smell và kỹ thuật refactoring tương ứng khi review PR của người khác

#### 3.2 Refactoring và code legacy

**Vì sao cần học:** Hầu hết dự án PHP lâu năm có những file không ai dám sửa. Senior được kỳ vọng
cải thiện chúng mà không làm hỏng production. Câu "refactor module legacy không có test thế nào"
rất hay gặp, và trả lời "viết lại từ đầu" là red flag.

**Học gì**

*Refactoring là gì*
- *Refactoring* là đổi cấu trúc code mà **không đổi hành vi** nhìn từ bên ngoài.
- Cách làm:
  - Đi từng bước nhỏ.
  - Sau mỗi bước code vẫn chạy được.
  - Có test làm lưới an toàn: chạy test sau mỗi bước để chắc hành vi không đổi.

*Các kỹ thuật cơ bản*

| Kỹ thuật | Làm gì |
|---|---|
| Rename | Đổi tên biến, hàm, class cho đúng ý |
| Extract / Inline function, variable | Tách một đoạn thành hàm hoặc biến có tên; hoặc ngược lại, gộp hàm quá vụn vào chỗ gọi |
| Extract class | Tách một nhóm field và method thành class riêng |
| Move function / field | Chuyển method hoặc field sang class dùng nó nhiều hơn |
| Introduce parameter object | Gom nhóm tham số hay đi cùng nhau thành một object |
| Replace conditional with polymorphism | Thay `switch ($type)` bằng mỗi loại một class |
| Replace magic literal | Thay số hoặc chuỗi ma thuật bằng hằng số hoặc enum |
| Encapsulate variable | Bọc biến dùng chung sau một hàm để kiểm soát truy cập |
| Extract interface (Extract superclass) | Rút interface (hoặc class cha) từ class có sẵn để có chỗ thay thế |

*Kỷ luật khi refactor*
- ⚠️ Tách commit/PR refactor khỏi commit đổi hành vi. Nhờ vậy:
  - Người review biết commit refactor không được đổi kết quả, dễ kiểm tra.
  - Có lỗi thì rollback đúng phần gây lỗi.
- *Quy tắc hướng đạo sinh* (boy scout rule): mỗi lần chạm vào code thì để lại nó sạch hơn một
  chút. Nhưng không lan man ra ngoài phạm vi của việc đang làm.

*Code legacy không có test*
- Quy trình an toàn:
  1. Viết *characterization test*: test ghi lại hành vi **hiện tại** của code, kể cả hành vi
     "sai". Mục đích không phải kiểm tra đúng sai, mà là biết ngay khi hành vi thay đổi.
  2. Tìm *seam*: chỗ thay được dependency mà không phải sửa nhiều code. Các loại seam hay dùng:
     - Tham số: truyền dependency vào method thay vì dùng thẳng.
     - Constructor: chuyển `new StripeClient()` bên trong ra thành tham số constructor.
     - Interface: rút interface để test truyền được bản giả.
  3. Refactor từng bước nhỏ dưới lưới test đó.
- Ưu tiên phần hay đổi và hay lỗi. Phần ổn định mà không ai đụng tới thì để yên.

*Thay đổi lớn và công cụ*
- Với thay đổi lớn, không làm một lần mà chuyển dần (chi tiết ở [15-architecture.md](15-architecture.md)):
  - *Strangler*: dựng phần mới bên cạnh, chuyển dần từng luồng sang, tới khi phần cũ không còn ai
    dùng.
  - *Branch by abstraction*: đặt một abstraction trước code cũ, viết implementation mới sau nó,
    rồi chuyển dần.
  - *Feature flag*: công tắc bật tắt tính năng lúc runtime, để deploy code mới mà chưa bật cho mọi
    người.
- Công cụ PHP:
  - Rector: refactor tự động theo luật, dùng nhiều để nâng version PHP hay Laravel.
  - PHPStan: tăng level kiểm tra dần dần, kèm *baseline* (file ghi lại các lỗi đang có, để chỉ bắt
    lỗi mới, còn lỗi cũ sửa dần).

**Đọc**
- *Refactoring* 2nd ed., ch.1–2 (ví dụ mở đầu và nguyên tắc) và [catalog](https://refactoring.com/catalog/)
- *Working Effectively with Legacy Code*: ch.2 (*Working with Feedback*), ch.4 (*The Seam Model*), ch.13 (*I Need to Make a Change, but I Don't Know What Tests to Write*: characterization test)
- Martin Fowler: [Branch By Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html)
- [Rector](https://getrector.com/documentation), [PHPStan: The Baseline](https://phpstan.org/user-guide/baseline)

**Nắm chắc khi**
- [ ] Viết được characterization test cho một hàm legacy không hiểu hết, rồi refactor nó qua ít nhất 5 commit nhỏ
- [ ] Chỉ ra được 3 loại seam trong một class gọi thẳng `new StripeClient()` và `DB::table()`
- [ ] Lập được kế hoạch tách `OrderService` 2.500 dòng mà mỗi bước một PR deploy được

#### 3.3 Anti-pattern và over-engineering

**Vì sao cần học:** Người phỏng vấn senior ít hỏi định nghĩa SOLID, họ hỏi "khi nào bạn quyết
định **không** dùng nó". Over-engineering làm dự án Laravel nhỏ thành 15 file cho một tính năng
CRUD, và senior phải biết cân chi phí đó với lợi ích.

**Học gì**

*SOLID để quản lý thay đổi*
- SOLID là công cụ quản lý **thay đổi**: nó làm code dễ sửa ở những chỗ hay đổi.
- Code nhỏ hoặc ít đổi thì chi phí gián tiếp (thêm file, thêm tầng, thêm interface) lớn hơn lợi
  ích thu được.

*Dấu hiệu áp quá tay*
- Mỗi class chỉ một method, 20 class cho một luồng CRUD. Đọc một tính năng phải mở 15 file.
- Cặp `FooInterface`/`Foo` mà không bao giờ có implementation thứ hai.
- Interface cho class thuần tính toán, không có I/O (không đọc DB, không gọi mạng), nên cũng
  không cần thay khi test.
- Plugin system cho thứ chỉ có một biến thể.
- Tầng uỷ quyền chỉ chuyển tiếp lời gọi: `OrderService::find()` chỉ gọi
  `OrderRepository::find()`, không thêm gì.

*Premature abstraction*
- *Premature abstraction* (trừu tượng hoá sớm): tạo interface, base class hay generic trước khi có
  biến thể thứ hai.
- Lạm dụng pattern cũng là một dạng: Factory chỉ tạo một loại object, Strategy chỉ có một chiến
  lược.

*Anemic domain model*
- *Anemic domain model* (model thiếu máu): entity chỉ có dữ liệu và getter/setter, mọi logic nằm
  ở service. Hệ quả là invariant bị kiểm tra ở nhiều service, hoặc bị quên ở một service nào đó.
- Phản biện:
  - Với nghiệp vụ mỏng, *transaction script* (mỗi use case là một hàm làm từ đầu tới cuối) là đủ
    dùng.
  - Eloquent vốn đã trộn dữ liệu với persistence, nên "rich model" kiểu DDD thuần không tự nhiên.
- Câu trả lời senior: độ giàu của model tỉ lệ với độ phức tạp của nghiệp vụ. Có invariant quan
  trọng thì đưa nó vào entity hoặc value object.

*God object*
- *God object*: một class biết và làm quá nhiều thứ, ví dụ `Helper`, `Utils`, hay model `User`
  2.000 dòng.
- Vấn đề:
  - Mọi người cùng sửa một file, conflict liên tục.
  - Không test riêng được từng phần.

*Khi nào interface đáng có*
- Ở ranh giới I/O: DB, HTTP, SDK, queue. Đây là chỗ cần thay bằng fake khi test và chỗ hay đổi
  nhà cung cấp.
- Ở điểm mở rộng thật: đã có hoặc chắc chắn sắp có nhiều implementation.
- Còn lại: tạo interface khi có biến thể thứ hai, hoặc khi cần test cô lập.

**Đọc**
- Martin Fowler: [Anemic Domain Model](https://martinfowler.com/bliki/AnemicDomainModel.html), [Yagni](https://martinfowler.com/bliki/Yagni.html)
- Sandi Metz: [The Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) (đọc lại với góc nhìn "tháo abstraction sai")
- Phần DDD và mức đầu tư kiến trúc: [15-architecture.md](15-architecture.md)

**Nắm chắc khi**
- [ ] Kể được một lần mình **không** áp SOLID/pattern vì chi phí lớn hơn lợi ích, và kết quả sau đó
- [ ] Đề xuất được quy ước đội về khi nào tạo interface, có tiêu chí cụ thể
- [ ] Bảo vệ được cả hai phía của tranh luận anemic domain model trong 3 phút

#### 3.4 Đối chiếu thiết kế giữa PHP, Java và Go

**Vì sao cần học:** Người làm PHP chuyển sang hoặc làm thêm Java, Go rất dễ mang nguyên thói quen
cũ sang (ví dụ viết interface lớn phía cung cấp trong Go). Người phỏng vấn đa ngôn ngữ hay hỏi
"Go không có kế thừa thì bạn viết pattern X thế nào".

**Học gì**

*Bảng so sánh*

| Khía cạnh | PHP | Java | Go |
|---|---|---|---|
| Kế thừa | Một cha, trait để trộn code | Một cha, interface `default` method | Không có; embedding |
| Interface | Nominal, `implements` | Nominal, `implements`; sealed (17+) | Structural, ngầm, nhỏ, do **bên dùng** định nghĩa |
| Overloading | Không | Có | Không |
| Value object | readonly class (8.2), clone with (8.5) | `record` | Struct truyền theo giá trị |
| Tập kiểu đóng | enum + `match` | sealed + pattern matching (21) | Type switch, không kiểm tra đủ nhánh |
| DI | Container reflection (Laravel) | Spring IoC | Nối tay trong `main`, Wire/Fx |
| Pattern "biến mất" | Strategy thành closure/first-class callable | Visitor thành sealed + `switch` | Strategy/Command thành `func`; Iterator thành `range`/`iter.Seq`; Template Method thành hàm nhận interface |

*Interface trong Go*
- Quy ước "accept interfaces, return structs": hàm nhận vào interface, nhưng trả về struct cụ thể.
- Vì Go dùng structural typing (module 1.2), bên **dùng** tự khai báo interface nhỏ đúng với thứ
  nó cần. Bên cung cấp không cần biết interface đó tồn tại.
  - Ví dụ: hàm chỉ cần đọc dữ liệu thì nhận `io.Reader`, và `*os.File`, `bytes.Buffer` đều truyền
    vào được.
- Chỉ tạo interface khi có nhu cầu thay thế thật.
- Không có kế thừa nên không có fragile base class. Đổi lại, embedding không có *dynamic
  dispatch* (chọn method theo kiểu thật lúc runtime), nên nó không phải kế thừa:

  ```go
  type Base struct{}
  func (Base) Name() string    { return "base" }
  func (b Base) Hello() string { return "hello " + b.Name() }

  type Child struct{ Base }     // embedding
  func (Child) Name() string   { return "child" }

  Child{}.Hello() // "hello base": Hello() gọi Name() của Base, không phải của Child
  ```

*Pattern là cách bù cho thứ ngôn ngữ thiếu*
- Nhiều pattern sinh ra để bù cho thứ ngôn ngữ không có sẵn.
- Ngôn ngữ có *hàm bậc nhất* (truyền hàm như một giá trị) thì nhiều pattern behavioral chỉ còn là
  một tham số hàm.
  - Ví dụ: Strategy trong Go chỉ là `sort.Slice(s, less)`, với `less` là một hàm.

**Đọc**
- Go: [Code Review Comments: Interfaces](https://go.dev/wiki/CodeReviewComments#interfaces)
- Refactoring.Guru: mỗi trang pattern có ví dụ Go, đọc để thấy pattern co lại thế nào khi không có kế thừa
- Phần ngôn ngữ: [05-php-laravel.md](05-php-laravel.md), [06-java-spring.md](06-java-spring.md), [07-go.md](07-go.md)

**Nắm chắc khi**
- [ ] Viết được Template Method và Decorator bằng Go mà không có kế thừa
- [ ] Giải thích được vì sao interface trong Go nên do bên dùng định nghĩa, còn PHP/Java thường do bên cung cấp

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Bốn tính chất của OOP, mỗi cái một ví dụ.** (1.1)
- Ý phải có: ví dụ từ nghiệp vụ, không đọc định nghĩa; encapsulation là giữ invariant
- Red flag: "encapsulation là private field + getter/setter"

**2. Interface, abstract class và trait khác nhau thế nào? Khi nào dùng cái nào?** (1.2)
- Ý phải có: hợp đồng so với chia sẻ code và state; một cha so với nhiều interface; trait trộn code nhưng không phải kiểu
- Điểm cộng: trait chứa logic nghiệp vụ là kế thừa trá hình; PHP 8.4 interface khai báo được property

**3. Overloading và overriding khác nhau thế nào? PHP có overloading không?** (1.2)
- Ý phải có: compile time so với runtime; PHP và Go không có, PHP giả lập bằng tham số tuỳ chọn/union type
- Điểm cộng: `#[\Override]` (PHP 8.3); "overloading" trong manual PHP là magic method `__get`/`__call`, khác nghĩa với Java

**4. Composition over inheritance nghĩa là gì?** (1.1)
- Ý phải có: fragile base class; kế thừa chỉ cho is-a thật; composition + uỷ quyền
- Điểm cộng: kể một trường hợp kế thừa vẫn đúng

**5. Kể 3 design pattern bạn đã dùng và dùng ở đâu.** (2.2–2.4)
- Ý phải có: gắn với code thật hoặc framework (Pipeline, Manager, Event)
- Red flag: kể tên pattern nhưng không nói được vấn đề nó giải

**6. Enum của PHP 8.1 dùng để làm gì? Có thay được bảng lookup không?** (2.1)
- Ý phải có: thay magic string/số; backed enum, `from`/`tryFrom`, method trên enum, cast Eloquent
- Điểm cộng: enum cố định trong code, còn danh mục người dùng sửa được thì cần bảng; thêm case mới vào enum trả ra API có thể là breaking ([09-api-design.md](09-api-design.md))

### 🟡 Mid

**7. Giải thích SOLID, mỗi chữ một ví dụ từ code bạn từng viết.** (1.3)
- Ý phải có: SRP là "một lý do thay đổi"; mỗi chữ một vi phạm thật và cách sửa
- Điểm cộng: nói chỗ mình **không** áp; liên hệ contracts và service provider của Laravel
- Red flag: đọc định nghĩa năm chữ

**8. Ví dụ vi phạm Liskov ngoài `Square`/`Rectangle`?** (1.3)
- Ý phải có: class con ném exception cho method cha hỗ trợ, siết điều kiện đầu vào, đổi ý nghĩa kết quả
- Điểm cộng: dấu hiệu `instanceof` trong code dùng class cha; sửa bằng tách interface

**9. Decorator và Proxy khác nhau thế nào? Middleware Laravel là pattern gì?** (2.3, 2.4)
- Ý phải có: cùng cấu trúc, khác mục đích; middleware Laravel là Chain of Responsibility qua Pipeline
- Điểm cộng: middleware Go `func(Handler) Handler` là Decorator; `@Transactional` là Proxy

**10. `Calendar.getInstance()` hay `Carbon::parse()` có phải Factory Method không?** (2.2)
- Ý phải có: không, đó là static factory method; Factory Method của GoF dựa vào class con override method tạo object
- Điểm cộng: ví dụ thật `Collection.iterator()`, `Illuminate\Support\Manager`
- Red flag: coi mọi hàm tạo object là Factory Method

**11. Strategy và State khác nhau thế nào?** (2.4)
- Ý phải có: Strategy do client chọn; State tự chuyển và hành vi đổi theo trạng thái
- Điểm cộng: trạng thái đơn hàng bằng enum + `canTransitionTo()` hay `spatie/laravel-model-states`, chọn theo số hành vi khác nhau của mỗi trạng thái

**12. Active Record và Repository khác nhau thế nào? Có nên dùng Repository trong Laravel?** (2.5)
- Ý phải có: AR tự lưu; repository giấu cách lưu; bọc Eloquent 1-1 mà vẫn trả model thì không giấu được gì
- Điểm cộng: đáng khi query phức tạp, nhiều nguồn, domain cần test không DB; Eloquent không có Unit of Work
- Red flag: "luôn dùng vì clean architecture"

**13. DI và Service Locator khác nhau thế nào? Laravel Facade thuộc loại nào?** (2.6)
- Ý phải có: truyền vào so với tự hỏi registry; Facade là static proxy tới container, một dạng service locator
- Điểm cộng: vẫn test được bằng `Facade::fake()` nhưng dependency ẩn; chấp nhận ở controller, tránh trong domain

**14. Getter/setter hay public property trong PHP 8.4?** (2.1)
- Ý phải có: property hooks cho phép thêm logic sau mà không đổi API; asymmetric visibility `public private(set)` cho đọc công khai, ghi nội bộ
- Điểm cộng: thay đổi trạng thái có quy tắc vẫn nên là method nghiệp vụ; hook có side effect nặng là bẫy
- Red flag: sinh getter/setter cho mọi field theo thói quen

**15. Law of Demeter là gì? Fluent API có vi phạm không?** (2.7)
- Ý phải có: chỉ nói chuyện với bạn trực tiếp; fluent API trả cùng object nên không vi phạm
- Điểm cộng: liên hệ tell don't ask

**16. Singleton tốt hay xấu? Octane thay đổi điều gì?** (2.2)
- Ý phải có: phân biệt singleton cổ điển (static, toàn cục) với singleton do container quản lý
- Điểm cộng: Octane giữ singleton qua nhiều request, rò state của request; dùng `scoped()`

### 🔴 Senior

**17. Khi nào áp SOLID là over-engineering? Cho ví dụ bạn đã gặp.** (3.3)
- Ý phải có: SOLID quản lý thay đổi; dấu hiệu quá tay (interface một implementation, tầng chuyển tiếp)
- Điểm cộng: tiêu chí tạo interface (ranh giới I/O, biến thể thứ hai, test cô lập)

**18. Anemic domain model có thật sự là anti-pattern không?** (3.3)
- Ý phải có: nêu cả hai phía; độ giàu của model theo độ phức tạp nghiệp vụ
- Điểm cộng: core subdomain nên rich, CRUD supporting thì transaction script là đủ ([15-architecture.md](15-architecture.md))

**19. Vì sao "trùng lặp rẻ hơn abstraction sai"?** (1.4, 3.3)
- Ý phải có: abstraction sai bị vặn thêm tham số, cờ cho từng trường hợp; khó tháo hơn copy
- Điểm cộng: cách tháo: inline lại rồi tách theo lý do thay đổi

**20. Refactor một module legacy không có test thế nào cho an toàn?** (3.2)
- Ý phải có: characterization test, seam, bước nhỏ, commit refactor tách khỏi đổi hành vi
- Điểm cộng: ưu tiên phần hay đổi; PHPStan baseline, Rector; feature flag, strangler khi thay lớn
- Red flag: "viết lại từ đầu"

**21. Visitor giải bài toán gì? Java 21 và PHP làm thế nào mà không cần Visitor?** (2.4)
- Ý phải có: thêm phép toán trên cây kiểu cố định mà không sửa các class; double dispatch; thêm loại node thì đau
- Điểm cộng: sealed + pattern matching có kiểm tra đủ nhánh; PHP chưa có sealed, dùng enum + `match` và static analysis; ví dụ PHP-Parser/PHPStan

**22. `OrderService` 2.500 dòng, ai sửa cũng sợ. Bạn làm gì?** (3.1, 3.2)
- Ý phải có: tìm cụm method dùng chung dữ liệu; characterization test luồng chính; extract class từng phần (pricing, inventory, notification); mỗi bước một PR
- Điểm cộng: đo tần suất sửa từng phần (git log) để chọn chỗ bắt đầu

**23. Mỗi lần thêm kênh thông báo (SMS, Zalo, push) phải sửa 6 file có `switch ($channel)`.** (3.1, 2.4)
- Ý phải có: shotgun surgery + repeated switches; interface `Channel`, mỗi kênh một class, đăng ký qua container
- Điểm cộng: Laravel Notification channel là ví dụ có sẵn

**24. Code review thấy mỗi class đều có `XxxInterface` dù chỉ có một implementation.** (3.3)
- Ý phải có: hỏi lý do (test, ranh giới module); interface có giá trị ở ranh giới I/O và điểm mở rộng thật
- Điểm cộng: đề xuất quy ước đội, không áp đặt trong một PR

**25. Model `Order` có 15 observer và event ẩn, sửa trạng thái gây side effect khó đoán.** (2.4, 2.7)
- Ý phải có: logic nghiệp vụ ẩn trong observer; đưa chuyển trạng thái vào method tường minh hoặc State pattern; domain event rõ ràng
- Điểm cộng: event phát sau commit (`afterCommit`), ghi tài liệu luồng

**26. Thiết kế hệ thống thanh toán hỗ trợ VNPay, Momo, Stripe, dễ thêm cổng mới.** (1.3, 2.3, 2.4)
- Ý phải có: interface `PaymentGateway` (charge, refund, verifyWebhook); Strategy + registry; Adapter bọc SDK; DTO kết quả chung
- Điểm cộng: webhook idempotent, không để chi tiết cổng rò vào domain, xử lý timeout không rõ kết quả ([22-practical-data.md](22-practical-data.md))

**27. Go không có kế thừa thì Template Method, Decorator viết thế nào?** (3.4)
- Ý phải có: hàm khung nhận interface; wrapper cùng interface hoặc `func(Handler) Handler`
- Điểm cộng: embedding không phải kế thừa (không có dynamic dispatch về "class con")

---

## Bài tập tự làm

1. Lấy controller hoặc service dài nhất trong dự án bạn đang làm, liệt kê code smell thấy được và
   kế hoạch refactor theo từng bước nhỏ (mỗi bước một commit, không đổi hành vi).
2. Viết interface và 2 implementation cho `PaymentGateway` bằng PHP (`declare(strict_types=1);`), kèm
   registry chọn cổng theo tên, đăng ký qua service container. Giải thích vì sao thiết kế thoả OCP.
3. Viết cùng một middleware (log thời gian xử lý) theo Decorator bằng Go và theo Pipeline bằng PHP, rồi so sánh.
4. Tìm trong mã nguồn Laravel (`vendor/laravel/framework`) ví dụ của Manager (Factory Method),
   Pipeline (Chain of Responsibility), Facade (static proxy) và một Decorator hoặc Observer; ghi đường dẫn file và giải thích ngắn.
5. Thiết kế value object `Money` bằng ngôn ngữ bạn chọn: tạo, cộng, so sánh, chia đều cho N người mà
   không mất đồng nào. Không dùng `float`. Nếu dùng PHP: viết bằng readonly class, có method `withX()`.
6. Mô hình hoá trạng thái đơn hàng (`pending`, `paid`, `shipped`, `cancelled`, `refunded`) theo hai cách:
   enum PHP có `canTransitionTo()` và State pattern. Thêm một phép tính mới (phí huỷ theo trạng thái) vào cả hai,
   rồi ghi lại cách nào phải sửa nhiều chỗ hơn.

> Nộp bài vào đây để được review.
