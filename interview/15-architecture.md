# 15. Kiến trúc phần mềm

> [← Mục lục](README.md) · Trọng tâm: **Laravel monolith → modular monolith → service** (DDD, ranh giới module, multi-tenancy), đối chiếu Spring và Go.
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

OOP, SOLID, pattern mức class ở [08-oop-design.md](08-oop-design.md). Saga, outbox, consistency ở
[14-distributed-systems.md](14-distributed-systems.md) và [12-messaging.md](12-messaging.md).

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| *Learning Domain-Driven Design* (Vlad Khononov; O'Reilly 2021) | Sách | Cửa vào DDD dễ nhất: subdomain, bounded context, aggregate, và khi nào **không** cần DDD. Đọc trước sách Evans |
| *Domain-Driven Design* (Eric Evans, 2003) | Sách | Nguồn gốc. Phần IV (strategic design) quan trọng hơn phần tactical |
| *Building Microservices*, 2nd ed. (Sam Newman; O'Reilly 2021) | Sách | Tách service, giao tiếp, dữ liệu, tổ chức team |
| *Monolith to Microservices* (Sam Newman; O'Reilly 2019) | Sách | Strangler fig, tách dữ liệu từng bước; thực dụng nhất cho người đang có monolith Laravel |
| *Fundamentals of Software Architecture*, 2nd ed. (Richards, Ford; O'Reilly 2025) | Sách | Các kiểu kiến trúc, quality attributes, trade-off, ADR |
| [Martin Fowler: Microservices Guide](https://martinfowler.com/articles/microservices.html) | Blog | Bài gốc về microservices và các bài bliki liên quan (MonolithFirst, StranglerFig, BoundedContext) |
| [microservices.io](https://microservices.io/patterns/index.html) (Chris Richardson) | Catalog pattern | Database per service, API composition, saga, CQRS; mỗi pattern có bối cảnh và nhược điểm |
| [Laravel docs](https://laravel.com/docs/octane) | Official docs | Octane, events, Pennant, global scope: chỗ kiến trúc giao với framework |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.3 | Tổ chức code một app Laravel đúng tầng, app stateless, config và flag đúng cách | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.5 | Hexagonal/clean, DDD tactical, modular monolith, giao tiếp giữa service, multi-tenancy | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.4 | Vẽ ranh giới bằng DDD strategic, tách service và dữ liệu, ra quyết định và viết tài liệu kiến trúc | 8–10 ngày |

Học theo thứ tự: modular monolith ở chặng 2 cần hiểu tầng và dependency ở chặng 1, và việc tách
service ở chặng 3 chỉ an toàn khi ranh giới module đã đúng. Câu "monolith hay microservices"
ở vòng senior là câu hỏi về **trade-off và tổ chức**, không phải về công nghệ.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Layered, MVC và nơi đặt logic nghiệp vụ

**Vì sao cần học:** "Logic nghiệp vụ đặt ở đâu" là tranh cãi có mặt trong gần như mọi code
review của dự án Laravel. Khi controller hay model phình tới vài nghìn dòng thì sửa một chỗ vỡ
ba chỗ và rất khó viết test. Phỏng vấn thường hỏi "controller, service, repository mỗi tầng làm
gì", rồi hỏi tiếp "có phải lúc nào cũng cần tầng service không".

**Học gì**

*Kiến trúc phân tầng*
- *Layered architecture* chia code thành các tầng, mỗi tầng một trách nhiệm. Bốn tầng hay gặp,
  từ ngoài vào trong:
  1. *Presentation*: nhận request, trả response. Trong Laravel là controller, FormRequest,
     API Resource.
  2. *Application*: mỗi class là một *use case*, tức một việc người dùng muốn làm, ví dụ "đặt
     hàng" hay "huỷ đơn".
  3. *Domain*: các quy tắc nghiệp vụ, ví dụ "đơn đã giao thì không được huỷ".
  4. *Infrastructure*: phần nói chuyện với bên ngoài. Gồm DB, API của bên thứ ba, mail. Truy cập
     DB thường đi qua *repository*, là class giấu chi tiết lưu trữ sau các method như
     `save($order)`, `findById($id)`.
- Quy tắc: tầng trên gọi tầng dưới, không gọi ngược. Tầng domain không biết HTTP tồn tại.
- ⚠️ Layered cổ điển để domain phụ thuộc vào tầng lưu trữ (*persistence*).
  - Ví dụ: service gọi thẳng Eloquent, nên muốn test quy tắc nghiệp vụ phải có DB.
  - Đây chính là điểm mà hexagonal và clean architecture sửa (module 2.1).

*Controller làm gì, không làm gì*
- Controller nên làm bốn việc:
  1. Parse request.
  2. Validate hình thức: field bắt buộc, đúng định dạng email, số dương.
  3. Gọi use case.
  4. Map kết quả sang response.
- Controller không chứa quy tắc nghiệp vụ và không viết SQL.
- ⚠️ *Fat controller* là controller ôm cả nghiệp vụ. Hai hệ quả:
  - Không dùng lại được logic từ queue job hay Artisan command.
  - Muốn test phải dựng cả HTTP request.
- ⚠️ *Fat model* là model ôm mọi thứ, ví dụ `User` 3.000 dòng trộn quy tắc, query, gửi mail và
  gọi API ngoài.

*MVC không phải là kiến trúc cho nghiệp vụ*
- MVC (Model, View, Controller) gốc là một pattern cho giao diện: tách dữ liệu, cách hiển thị và
  cách xử lý input.
- MVC không nói gì về:
  - Logic nghiệp vụ đặt ở đâu.
  - Transaction mở ở đâu.
  - Gọi API ngoài ở đâu.
  - Dùng lại logic từ job hay CLI thế nào.
- Dấu hiệu đã vượt quá MVC: cùng một nghiệp vụ được gọi từ HTTP, từ queue job và từ Artisan
  command. Lúc đó cần một tầng use case để cả ba cùng gọi.

*Application service và domain service*

| | Application service | Domain service |
|---|---|---|
| Là gì | Một use case, ví dụ `PlaceOrder` | Một quy tắc nghiệp vụ không thuộc về riêng một đối tượng nào |
| Làm gì | Điều phối: mở transaction, gọi repository, phát event | Tính toán theo quy tắc, ví dụ tính phí ship từ đơn hàng và vị trí kho |
| Chứa quy tắc nghiệp vụ | Không | Có |
| Biết transaction, DB | Có | Không |

*Công cụ của Laravel cho từng việc*
- Validate hình thức: FormRequest.
- Use case: Action class như `PlaceOrderAction`, hoặc package `lorisleiva/laravel-actions`.
- Việc chạy nền: Job.
- Phản ứng sau một sự kiện: Event và Listener.
- Phân quyền: Policy.
- Ví dụ một use case được gọi từ nhiều nơi:

  ```php
  final class PlaceOrderAction
  {
      public function __construct(private OrderRepository $orders) {}

      public function execute(PlaceOrderData $data): Order
      {
          return DB::transaction(function () use ($data): Order {
              $order = Order::place($data);   // quy tắc nằm ở domain
              $this->orders->save($order);
              return $order;
          });
      }
  }

  // Controller, Job và Artisan command đều chỉ gọi một dòng:
  app(PlaceOrderAction::class)->execute($data);
  ```

*Khi nào không cần nhiều tầng*
- ⚠️ *Pass-through layer* là tầng chỉ gọi lại tầng dưới, ví dụ service có method một dòng gọi
  repository.
  - Một vài chỗ như vậy không sai.
  - Cả app như vậy thì tầng đó chưa có lý do tồn tại.
- CRUD đơn giản thì controller cộng model là chấp nhận được. Không có câu trả lời "luôn luôn".

**Đọc**
- *Fundamentals of Software Architecture*: chương *Layered Architecture Style*
- Martin Fowler: [PresentationDomainDataLayering](https://martinfowler.com/bliki/PresentationDomainDataLayering.html)
- [lorisleiva/laravel-actions](https://github.com/lorisleiva/laravel-actions): README, để thấy một cách tổ chức use case trong Laravel

**Nắm chắc khi**
- [ ] Lấy một controller dày trong dự án, tách được thành FormRequest + Action + Event mà hành vi không đổi
- [ ] Gọi được cùng một use case từ controller, job và Artisan command mà không copy code
- [ ] Giải thích được vì sao "MVC" không đủ làm kiến trúc cho một app nghiệp vụ lớn

#### 1.2 Monolith, 12-factor và app stateless

**Vì sao cần học:** Đa số dự án PHP đang chạy là monolith, và câu "monolith có gì tốt" dùng để
kiểm tra bạn có nghĩ bằng trade-off hay chỉ theo trào lưu. Khi đưa app lên nhiều server hoặc lên
Kubernetes, các lỗi kiểu "đăng nhập xong bị đá ra" hay "file upload lúc có lúc không" đều bắt
nguồn từ việc app chưa stateless. Octane và queue worker thêm một loại bug mà PHP-FPM không có.

**Học gì**

*Monolith là gì và tốt ở đâu*
- *Monolith* là ứng dụng được build và deploy thành **một đơn vị**. Một app Laravel với một
  repo, một lần deploy là monolith.
- Ưu điểm thật:
  - Module gọi nhau bằng lời gọi hàm, không phải gọi qua mạng, nên nhanh và không lỗi mạng.
  - Có transaction ACID (nhiều thao tác cùng thành công hoặc cùng bị huỷ) trên cả nghiệp vụ, vì
    mọi thứ dùng chung một DB.
  - Debug và trace dễ: một stack trace đi xuyên suốt.
  - Refactor xuyên module dễ: IDE đổi tên một lần là xong.
  - Vận hành rẻ: một pipeline, một bộ monitoring.
- Nhược điểm khi app và team lớn lên:
  - Build và test chậm.
  - Deploy chung nên rủi ro chung: một lỗi nhỏ ở module A làm cả app phải rollback.
  - Nhiều team sửa chung một codebase, giẫm chân nhau.
  - Không scale riêng được phần đang nóng.
- ⚠️ "Monolith" không đồng nghĩa với *big ball of mud* (code rối, không ranh giới). Vấn đề thường
  là thiếu ranh giới giữa các phần, không phải là việc có một đơn vị deploy.

*12-factor app*
- *12-factor* là bộ 12 nguyên tắc cho app chạy trên cloud, viết bởi Heroku. Đủ 12 mục:
  1. Codebase: một repo, deploy ra nhiều môi trường.
  2. Dependencies: khai báo rõ (composer.json), không dựa vào thứ cài sẵn trên máy.
  3. **Config qua biến môi trường** (module 1.3).
  4. Backing services: DB, Redis, S3 là tài nguyên gắn vào qua config, đổi được mà không sửa code.
  5. Build, release, run tách bạch.
  6. **Process stateless** (xem ngay dưới).
  7. Port binding: app tự lắng nghe trên một port.
  8. Concurrency: scale bằng cách chạy thêm process.
  9. Disposability: khởi động nhanh, tắt êm. Tắt êm (*graceful shutdown*) nghĩa là khi nhận tín
     hiệu dừng thì làm xong request hoặc job đang dở rồi mới thoát.
  10. Dev/prod parity: môi trường dev giống production nhất có thể.
  11. **Log ra stdout**, để hạ tầng thu gom, app không tự ghi file log.
  12. Admin process: việc một lần như migration chạy bằng cùng codebase đó.

*Stateless*
- App *stateless* là app không giữ trạng thái nào quan trọng trên chính máy đang chạy nó. Bất kỳ
  instance nào cũng xử lý được bất kỳ request nào.
- Nhờ vậy mới *scale ngang* được, tức thêm máy chạy song song phía sau load balancer, và thay
  hay tắt một máy bất kỳ lúc nào.
- ⚠️ Hai vi phạm hay gặp:
  - Session lưu trên file local. Request sau rơi vào máy khác là mất session.
  - File upload lưu trên đĩa của app server. Máy khác không thấy file, máy chết là mất file.
- Cách sửa trong Laravel: session và cache dùng driver Redis, file dùng filesystem S3.

*Process sống lâu: Octane và queue worker*
- PHP-FPM vốn *share-nothing* theo request: mỗi request boot lại framework từ đầu, xong là mọi
  biến bị dọn sạch.
- *Octane* (chạy trên Swoole, RoadRunner hoặc FrankenPHP) boot app một lần và giữ nó trong RAM
  để phục vụ nhiều request liên tiếp.
  - Lợi: nhanh hơn vì không boot lại framework mỗi request.
  - ⚠️ Rủi ro 1: static property và singleton giữ lại state của request trước. Ví dụ singleton
    lưu "user hiện tại" thì request sau của người khác thấy nhầm user.
  - ⚠️ Rủi ro 2: memory leak tích luỹ qua hàng nghìn request thay vì bị dọn sau mỗi request.
  - Khi deploy, worker phải được reload êm (*graceful reload*) để nạp code mới mà không cắt
    request đang chạy.
- Queue worker (`queue:work`) cũng là process sống lâu, nên cùng loại rủi ro. Dùng `--max-jobs`
  hoặc `--max-time` để worker tự khởi động lại định kỳ.

**Đọc**
- [The Twelve-Factor App](https://12factor.net/): đọc hết, ngắn
- Laravel: [Octane](https://laravel.com/docs/octane) (mục *Dependency Injection and Octane*, *Managing Memory Leaks*)
- Martin Fowler: [MonolithFirst](https://martinfowler.com/bliki/MonolithFirst.html)

**Nắm chắc khi**
- [ ] Chỉ ra được 3 chỗ trong app Laravel của mình vi phạm stateless và cách sửa
- [ ] Tái hiện được một bug rò state giữa request khi chạy Octane (singleton giữ user hiện tại)
- [ ] Kể được 5 ưu điểm thật của monolith mà không dùng từ "đơn giản"

#### 1.3 Configuration và feature flag

**Vì sao cần học:** Bug "chạy local được, lên production thì `env()` trả `null`" là bug kinh điển
của Laravel. Feature flag là cách các team deploy hằng ngày mà vẫn kiểm soát được rủi ro, và là
công cụ chính khi migrate dần từ hệ cũ sang hệ mới. Câu hỏi thường gặp: "deploy khác release thế
nào", "flag service chết thì sao".

**Học gì**

*Config và secret*
- *Config* là những giá trị khác nhau giữa các môi trường (local, staging, production), ví dụ
  host DB, URL của API đối tác. Config phải tách khỏi code.
- *Secret* là config nhạy cảm như mật khẩu DB, API key. Secret tách khỏi config thường và lưu ở
  kho riêng: Vault, AWS Secrets Manager, Kubernetes Secret ([10-security.md](10-security.md)).
- Validate config ngay khi app khởi động: thiếu biến bắt buộc thì fail ngay, đừng để tới lúc có
  request mới lỗi.

*Bẫy `env()` của Laravel*
- ⚠️ Chỉ gọi `env()` bên trong các file ở thư mục `config/`. Ở chỗ khác thì đọc qua `config()`.
- Lý do, theo từng bước:
  1. Khi deploy, chạy `php artisan config:cache`. Lệnh này gộp mọi file config thành một file
     cache.
  2. Từ đó Laravel không đọc file `.env` nữa.
  3. Mọi lời gọi `env('X')` nằm ngoài `config/` trả về `null`.

*Config động*
- *Config động* là config đổi được lúc app đang chạy, không cần deploy, ví dụ bật tắt tính năng
  từ trang admin.
- ⚠️ Đây là một đường thay đổi production giống như deploy code, nên cũng cần audit (ai đổi, lúc
  nào) và cách rollback.

*Feature flag*
- *Feature flag* là một công tắc trong code: `if (flag bật) { code mới } else { code cũ }`.
- Ý nghĩa chính: tách **deploy** (đưa code lên server) khỏi **release** (cho người dùng thấy
  tính năng). Code mới có thể nằm trên production nhiều ngày ở trạng thái tắt.
- Các loại flag:

| Loại | Dùng để | Sống bao lâu |
|---|---|---|
| Release | Ẩn tính năng đang làm dở, bật dần | Ngắn, xoá sau khi bật 100% |
| Ops / kill switch | Tắt nhanh một tính năng nặng hoặc lỗi khi có sự cố | Lâu dài |
| Experiment | A/B test | Theo thời gian thí nghiệm |
| Permission | Chỉ nhóm người dùng nào đó thấy tính năng, ví dụ gói trả phí | Lâu dài |

- Dùng trong migration: chạy song song hệ cũ và hệ mới, chuyển dần theo phần trăm người dùng.
- ⚠️ *Nợ flag*: flag không được xoá sau khi dùng xong, số tổ hợp bật tắt bùng nổ, không ai dám
  động vào. Mỗi release flag cần có người chịu trách nhiệm (owner) và hạn xoá.
- ⚠️ Nếu dùng một dịch vụ flag bên ngoài và dịch vụ đó chết, app phải có giá trị mặc định an toàn
  và cache local của trạng thái flag.
- Laravel Pennant: định nghĩa flag theo *scope* (theo user, theo team), lưu bằng driver database
  hoặc array.

**Đọc**
- Martin Fowler (Pete Hodgson): [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html): đọc hết, có phân loại flag
- Laravel: [Configuration](https://laravel.com/docs/configuration) (mục *Configuration Caching*), [Pennant](https://laravel.com/docs/pennant)

**Nắm chắc khi**
- [ ] Giải thích được vì sao `env('X')` trong controller trả `null` sau khi deploy
- [ ] Thiết kế được rollout một tính năng theo 1% → 10% → 100% bằng Pennant, có kill switch và kế hoạch xoá flag

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Hexagonal, Clean, Onion, vertical slice

**Vì sao cần học:** Khi nghiệp vụ phức tạp dần (thanh toán, tính giá, đối soát), bạn cần test
quy tắc nghiệp vụ mà không phải dựng DB hay gọi Stripe thật. Hexagonal và clean architecture giải
quyết đúng việc đó. Câu hỏi hay gặp: "hexagonal khác layered ở đâu" và "có nên dùng Clean
Architecture cho Laravel không", với đáp án tốt phải nói được cái giá.

**Học gì**

*Hexagonal (ports & adapters)*
- Ý tưởng: phần lõi nghiệp vụ nằm giữa, mọi thứ bên ngoài cắm vào lõi qua các "cổng".
- *Port* là interface do lõi định nghĩa. Có hai chiều:
  - Port vào: cách bên ngoài gọi vào lõi, ví dụ interface `PlaceOrder`.
  - Port ra: thứ lõi cần từ bên ngoài, ví dụ interface `OrderRepository`, `PaymentGateway`.
- *Adapter* là class hiện thực một port:
  - Adapter vào: HTTP controller, queue consumer, CLI command.
  - Adapter ra: repository dùng MySQL, client gọi Stripe, class gửi mail qua SMTP.
- Ví dụ: trong test, thay adapter Stripe bằng một adapter giả trả kết quả cố định. Lõi không hề
  biết mình đang được test.

*Clean và Onion*
- Clean Architecture và Onion Architecture cùng tư tưởng với hexagonal, chỉ vẽ bằng các vòng tròn
  đồng tâm: lõi ở giữa, framework và DB ở vòng ngoài cùng.
- *Dependency rule*: phụ thuộc trong source code chỉ được hướng vào trong. Lõi không `use` class
  nào của framework, ORM hay HTTP.
- Cách đạt được, theo từng bước:
  1. Lõi khai báo interface cho thứ nó cần (port ra).
  2. Tầng ngoài viết class hiện thực interface đó.
  3. *Service container* của framework ráp hai thứ lại lúc chạy.

  Đây là *dependency inversion* ([08-oop-design.md](08-oop-design.md)).
- Khác biệt với layered cổ điển: ở layered, domain phụ thuộc xuống persistence. Ở đây,
  persistence phụ thuộc vào interface do domain định nghĩa.

*Vertical slice*
- *Vertical slice* tổ chức code theo **tính năng** thay vì theo tầng. Mỗi thư mục là một tính
  năng (`PlaceOrder/`, `CancelOrder/`) chứa đủ controller, logic, query của nó.
- Mỗi slice tự chọn độ phức tạp: tính năng đơn giản viết thẳng, tính năng phức tạp mới tách tầng.

*So sánh*

| Kiểu | Hợp khi | Không hợp khi |
|---|---|---|
| MVC + model của framework | CRUD, admin, prototype, team nhỏ | Nghiệp vụ nhiều quy tắc, nhiều entry point |
| Layered + service layer | Đa số app nghiệp vụ vừa | Cần thay hạ tầng thường xuyên |
| Hexagonal / Clean / Onion | Domain phức tạp, sống lâu, nhiều adapter, cần test lõi độc lập | App đơn giản, deadline gấp |
| Vertical slice | Nhiều tính năng độc lập | Logic dùng chung nhiều giữa tính năng |

*Cái giá*
- ⚠️ Nhiều interface và nhiều bước chuyển đổi dữ liệu (*mapping*): entity của domain ↔ Eloquent
  model ↔ DTO (*Data Transfer Object*, object chỉ chứa dữ liệu để truyền giữa các tầng).
- Eloquent là *Active Record*, tức object vừa chứa dữ liệu vừa tự lưu mình xuống DB. Tách lõi
  khỏi Eloquent hoàn toàn nghĩa là bỏ phần lớn sự tiện lợi đó.
- ⚠️ Tách khỏi framework tuyệt đối (*framework-agnostic*) hiếm khi đáng, vì thay framework cho cả
  app là việc rất hiếm xảy ra. Lý do thật để dùng kiểu kiến trúc này là **test** được và
  **hiểu** được lõi nghiệp vụ.
- Kiến trúc là **mức đầu tư** tương xứng với độ phức tạp. Có thể áp hexagonal chỉ cho module
  core, phần còn lại vẫn là MVC.

*Đối chiếu Java/Go*
- Spring có sẵn các annotation `@Controller`, `@Service`, `@Repository`, và JPA theo kiểu *Data
  Mapper* (entity không tự lưu mình, một lớp riêng lo việc lưu). Tách lõi khỏi persistence tự
  nhiên hơn Eloquent.
- Go tổ chức theo package domain. Interface nhỏ được khai báo ở phía **dùng** chứ không ở phía
  hiện thực, nên dependency inversion gần như tự có.

**Đọc**
- Alistair Cockburn: [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/) (bài gốc)
- Robert C. Martin: [The Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- Jeffrey Palermo: [The Onion Architecture, part 1](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/)
- Jimmy Bogard: [Vertical Slice Architecture](https://www.jimmybogard.com/vertical-slice-architecture/)

**Nắm chắc khi**
- [ ] Vẽ được hexagon cho module thanh toán: các port vào/ra và adapter tương ứng
- [ ] Viết được test cho một use case chỉ dùng adapter in-memory, không cần DB
- [ ] Phản biện được đề xuất "hexagonal cho toàn bộ admin CRUD 40 màn hình" bằng chi phí/lợi ích

#### 2.2 DDD tactical và DDD trong Laravel

**Vì sao cần học:** DDD tactical cho bạn bộ từ vựng để thiết kế phần nghiệp vụ lõi: gom dữ liệu
nào vào một transaction, đặt quy tắc ở đâu, phát event lúc nào. Trong Laravel, các lỗi như "event
đã gửi mail nhưng transaction rollback" hay "khoá tranh chấp liên tục trên bảng khách hàng" đều
liên quan tới phần này. Câu hỏi hay gặp: "entity khác value object thế nào", "aggregate là gì".

**Học gì**

*Entity và value object*
- *Entity* là đối tượng có **danh tính** (identity) giữ nguyên theo thời gian, dù dữ liệu đổi.
  - Ví dụ: đơn hàng #1001 đổi địa chỉ giao vẫn là đơn #1001.
- *Value object* là đối tượng **không có danh tính**, chỉ được định nghĩa bởi giá trị của nó.
  - Ví dụ: `Money(100000, 'VND')`, `Email`, `DateRange`.
  - Hai value object cùng giá trị thì coi là một.
  - **Immutable**: không sửa được sau khi tạo. Muốn đổi thì tạo object mới, ví dụ
    `$price->add($tax)` trả về `Money` mới.
  - Lợi ích: kiểm tra hợp lệ một lần lúc tạo, ví dụ `Email` sai định dạng thì không tạo được.

*Aggregate*
- *Invariant* là quy tắc nghiệp vụ phải **luôn đúng**, ví dụ "tổng tiền đơn bằng tổng các dòng"
  hay "đơn tối đa 50 dòng".
- *Aggregate* là một cụm entity và value object được coi là **một đơn vị nhất quán**: invariant
  của cụm luôn được giữ sau mỗi thao tác.
- Chỉ truy cập aggregate qua một entity đứng đầu gọi là *aggregate root*.
  - Ví dụ: `Order` là root, chứa các `OrderLine`. Thêm dòng bằng `$order->addLine()`, không tạo
    `OrderLine` rồi lưu thẳng, vì như vậy `Order` không kiểm tra được giới hạn 50 dòng.

*Bốn quy tắc aggregate của Vaughn Vernon*
1. Bảo vệ invariant thật trong ranh giới aggregate.
2. Thiết kế aggregate **nhỏ**.
3. Tham chiếu aggregate khác **bằng id**, không giữ cả object.
4. Giữa các aggregate dùng *eventual consistency*: dữ liệu ở các nơi có thể lệch nhau một lúc,
   rồi sẽ khớp lại sau (thường qua event).

- Hệ quả: một transaction chỉ sửa **một** aggregate. Cần sửa hai aggregate trong cùng một
  transaction thường là dấu hiệu ranh giới vẽ sai.
- Xử lý hai request cùng sửa một aggregate: dùng *optimistic lock*.
  1. Root có cột `version`.
  2. Khi lưu: `UPDATE ... SET version = version + 1 WHERE id = ? AND version = ?`.
  3. Không dòng nào bị ảnh hưởng nghĩa là có người sửa trước, báo lỗi để thử lại.
- ⚠️ Aggregate quá to, ví dụ `Customer` chứa mọi `Order`:
  - Load chậm, vì phải kéo cả nghìn đơn lên mỗi lần.
  - Tranh chấp version liên tục, vì mọi thao tác trên bất kỳ đơn nào cũng sửa cùng một root.

*Domain event*
- *Domain event* là một sự việc đã xảy ra trong nghiệp vụ, đặt tên ở **thì quá khứ**:
  `OrderPlaced`, `PaymentFailed`.
- ⚠️ Phải phát event **sau khi commit**, hoặc qua *outbox* (ghi event vào một bảng trong cùng
  transaction, một process khác đọc bảng và gửi đi; [12-messaging.md](12-messaging.md)).
  - Nếu phát trước commit mà transaction rollback, listener đã gửi mail "đặt hàng thành công"
    cho một đơn không tồn tại. Đây gọi là event "ma".
- Hai loại event:

| | Domain event | Integration event |
|---|---|---|
| Phạm vi | Nội bộ một module hoặc service | Gửi cho service hay team khác |
| Là hợp đồng công khai | Không, đổi thoải mái | Có |
| Versioning | Không cần | Bắt buộc, vì bên nhận phụ thuộc vào format |

*Repository theo nghĩa DDD*
- Mỗi aggregate root có một repository. Không có repository riêng cho `OrderLine`.
- Interface của repository nằm ở domain, class hiện thực nằm ở infrastructure.
- ⚠️ Repository có 40 method `findByX` phục vụ báo cáo là dấu hiệu cần tách phần đọc ra một *read
  model* hoặc *query service* riêng, chỉ để truy vấn.

*Anemic và rich domain model*
- *Anemic model*: model chỉ chứa dữ liệu và getter/setter, mọi quy tắc nằm ở service.
- *Rich model*: model tự giữ quy tắc của mình.
  - Ví dụ: `$order->cancel()` tự ném exception nếu đơn đã giao.
- Core subdomain (phần nghiệp vụ tạo lợi thế, module 3.1) nên dùng rich model. Phần CRUD hỗ trợ
  thì anemic là đủ dùng.

*DDD trong Laravel*
- Eloquent model làm aggregate root được, nếu chấp nhận nó dính với persistence:
  - Giữ invariant trong method của model.
  - Chặn set trực tiếp các field quan trọng, ví dụ không cho `$order->status = 'paid'` từ ngoài.
- Value object làm *custom cast* của Eloquent (interface `CastsAttributes`): cột `amount` và
  `currency` được đọc ra thành một object `Money`. Enum của PHP dùng cho trạng thái.
- Phát event sau commit: event implement `ShouldDispatchAfterCommit`, hoặc dùng
  `DB::afterCommit()`.
- Package tham khảo:
  - `spatie/laravel-data`: DTO.
  - `spatie/laravel-event-sourcing`: aggregate, projector, reactor.
  - `spatie/laravel-model-states`: state machine cho trạng thái.
- ⚠️ Tạo thư mục `Domain/`, `Application/`, `Infrastructure/` không tự làm ra DDD. Ranh giới và
  ngôn ngữ chung với nghiệp vụ mới là phần chính.

**Đọc**
- Vaughn Vernon: [Effective Aggregate Design](https://www.dddcommunity.org/library/vernon_2011/) (3 phần, PDF)
- Martin Fowler: [DDD Aggregate](https://martinfowler.com/bliki/DDD_Aggregate.html), [Value Object](https://martinfowler.com/bliki/ValueObject.html)
- *Learning Domain-Driven Design*: phần II (tactical), đặc biệt chương về aggregate và domain event
- Laravel: [Custom Casts](https://laravel.com/docs/eloquent-mutators#custom-casts), [Dispatching Events After Transactions](https://laravel.com/docs/events#dispatching-events-after-database-transactions)
- [spatie/laravel-event-sourcing](https://spatie.be/docs/laravel-event-sourcing): phần *Using aggregates*, để thấy aggregate trong một package PHP thật

**Nắm chắc khi**
- [ ] Mô hình hoá được aggregate `Order`: invariant, entity, value object, domain event (bài tập 3)
- [ ] Giải thích được vì sao `Order` không nên chứa object `Customer` mà chỉ `customer_id`
- [ ] Viết được `Money` làm custom cast Eloquent và một method trên model bảo vệ invariant

#### 2.3 Modular monolith

**Vì sao cần học:** Modular monolith là bước đi thực tế nhất cho một monolith Laravel đang rối:
có ranh giới rõ như microservices nhưng vẫn giữ chi phí vận hành của monolith. Câu "monolith 5
năm tuổi, nên tách microservices không" ở vòng senior thường có đáp án tốt bắt đầu từ đây.

**Học gì**

*Modular monolith là gì*
- Vẫn là **một đơn vị deploy**, nhưng code chia thành các module theo *bounded context* (vùng
  nghiệp vụ có model và ngôn ngữ riêng, ví dụ Order, Billing, Notification; module 3.1).
- Khác monolith thường ở chỗ ranh giới giữa module được **cưỡng chế** bằng công cụ, không chỉ là
  quy ước.

*Quy tắc giữa các module*
- Module gọi nhau qua *public API* của module (một interface hoặc facade được công bố), hoặc qua
  event nội bộ.
- ⚠️ **Không query hay JOIN bảng của module khác.** Mỗi module sở hữu các bảng của nó.
- Không chia sẻ Eloquent model giữa module. Trao đổi bằng DTO hoặc bằng id.
- ⚠️ Quan hệ Eloquent như `belongsTo` trỏ sang model của module khác là JOIN chéo trá hình:
  - Ví dụ: trong module Billing viết `$invoice->order->customer->email`.
  - Billing đang đọc thẳng bảng của Order và Customer, chỉ là không nhìn thấy câu SQL.

*Cưỡng chế bằng công cụ*
- Chạy trong CI, vi phạm ranh giới thì build fail:
  - PHP: Deptrac.
  - Ruby: Packwerk (của Shopify).
  - Java: ArchUnit, Spring Modulith.
  - Go: package `internal/`, compiler cấm package ngoài import.

*Tổ chức module trong Laravel*
- Mỗi module là một thư mục hoặc package, có service provider, route và migration riêng.
- Các cách làm:
  - Package `InterNACHI/modular`.
  - Package `nWidart/laravel-modules`.
  - Tự tổ chức bằng Composer path repository.

*Lợi ích và case study*
- Khi thật sự cần tách service thì ranh giới đã sẵn. Trong lúc chưa tách, chi phí vận hành vẫn là
  của một monolith.
- Case study: Shopify giữ monolith Rails rất lớn và modular hoá bằng Packwerk, thay vì tách
  microservices.

**Đọc**
- Shopify Engineering: [Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity), [Under Deconstruction: The State of Shopify's Monolith](https://shopify.engineering/shopify-monolith)
- [Deptrac](https://deptrac.github.io/deptrac/): phần layers, rulesets
- [InterNACHI/modular](https://github.com/InterNACHI/modular): README (cách tổ chức module bằng package Composer trong Laravel)
- Đối chiếu: [Spring Modulith](https://docs.spring.io/spring-modulith/reference/)

**Nắm chắc khi**
- [ ] Cấu hình được Deptrac cấm module `Billing` dùng class nội bộ của `Order`, và CI fail khi vi phạm
- [ ] Liệt kê được mọi chỗ JOIN chéo module trong dự án mình và kế hoạch gỡ từng chỗ
- [ ] Viết được RFC chuyển một monolith (Order, Payment, Notification) sang modular monolith (bài tập 4)

#### 2.4 Microservices và giao tiếp giữa service

**Vì sao cần học:** "Lợi ích và cái giá của microservices" là câu gần như chắc chắn gặp ở vòng
mid trở lên, và red flag lớn nhất là trả lời "vì scale tốt, hiện đại". Khi làm việc với nhiều
service, bạn cần biết chọn gọi sync hay async, vì sao cần timeout, và các thành phần như gateway,
service mesh làm gì.

**Học gì**

*Lợi ích và cái giá*

| Lợi ích | Cái giá |
|---|---|
| Deploy độc lập từng service | Gọi qua mạng: thêm latency, và có *lỗi một phần* (service A sống, B chết) |
| Scale độc lập phần nóng | Mất transaction ACID xuyên service |
| Cô lập lỗi, nếu thiết kế đúng | *Observability* (log, metric, trace để biết hệ thống đang ra sao) trở thành bắt buộc |
| Team tự chủ công nghệ và lịch deploy | CI/CD và vận hành cho từng service |
| | Test tích hợp khó |
| | Dữ liệu bị trùng lặp giữa các service |

- **Điều kiện tiên quyết** trước khi tách:
  - CI/CD tự động.
  - Tạo môi trường, máy chủ mới nhanh (*provisioning*).
  - Monitoring, alerting và tracing.
  - Đủ người để mỗi service có một team sở hữu.
  - Ranh giới domain đã rõ.

*Sync và async*
- *Sync*: gọi và chờ kết quả ngay, qua HTTP hoặc gRPC.
  - Gây *temporal coupling* (phụ thuộc về thời gian): service gọi chỉ chạy được khi service bị
    gọi đang sống **đúng lúc đó**.
  - Availability của một chuỗi gọi nối tiếp là **tích** các availability. Ví dụ: 5 service mỗi
    cái 99,9% nối tiếp thì còn khoảng 99,5%.
  - ⚠️ Chuỗi gọi sync phải có ba thứ ([14-distributed-systems.md](14-distributed-systems.md)):
    - Timeout.
    - Retry có giới hạn số lần.
    - *Circuit breaker*: sau nhiều lỗi liên tiếp thì ngừng gọi service đó một lúc và trả lỗi ngay,
      để không dồn thêm tải lên service đang chết.
- *Async*: gửi message hoặc event vào queue rồi đi tiếp, không chờ.
  - Cô lập lỗi tốt hơn: bên nhận chết thì message nằm chờ trong queue.
  - Đổi lại: eventual consistency, message có thể đến trùng hoặc lệch thứ tự, và cần *DLQ*
    (*dead letter queue*, nơi chứa message xử lý thất bại nhiều lần để xem lại).

*Orchestration và choreography*

| | Orchestration | Choreography |
|---|---|---|
| Cách chạy | Một service trung tâm hoặc *workflow engine* (như Temporal) ra lệnh từng bước | Mỗi service nghe event và tự phản ứng |
| Thấy toàn cảnh luồng | Dễ, nằm ở một chỗ | Khó, phải ghép từ nhiều service |
| Coupling | Tập trung vào bên điều phối | Lỏng hơn |
| ⚠️ Rủi ro | Bên điều phối thành điểm phình to | Luồng dài thành "event spaghetti" |

*Gateway, BFF, service discovery*
- *API gateway* là điểm vào chung cho mọi client. Lo các việc chung (*cross-cutting*): routing,
  xác thực, rate limit. ⚠️ Không đặt logic nghiệp vụ ở gateway.
- *BFF* (*Backend for Frontend*): mỗi loại client (web, mobile) có một backend mỏng riêng, ghép dữ
  liệu đúng như client đó cần ([09-api-design.md](09-api-design.md)).
- *Service discovery* là cách một service tìm địa chỉ của service khác khi instance liên tục thay
  đổi:
  - Client-side: client hỏi registry (như Consul) rồi tự chọn instance.
  - Server-side: client gọi load balancer, load balancer chọn instance.
  - DNS: Kubernetes Service cho một tên DNS cố định.

*Service mesh*
- *Service mesh* đưa các việc mạng ra khỏi code và giao cho một lớp proxy:
  - *mTLS*: mã hoá và xác thực hai chiều giữa các service.
  - Retry và timeout.
  - *Traffic splitting*: chia phần trăm traffic giữa hai phiên bản.
  - Metric và trace.
- Hai mô hình:
  - *Sidecar*: mỗi pod (đơn vị chạy container nhỏ nhất của Kubernetes) chạy kèm một proxy. Istio dùng Envoy, Linkerd dùng proxy riêng.
  - Istio *ambient mode* (GA từ Istio 1.24, 11/2024): không có sidecar.
    - *ztunnel* chạy một bản mỗi node, lo tầng L4 (tầng kết nối TCP), tức mTLS.
    - *Waypoint proxy* là tuỳ chọn, lo tầng L7 (tầng HTTP: route theo path, retry).
    - Sidecar vẫn được hỗ trợ.
- Cái giá: thêm thành phần phải vận hành, thêm latency mỗi bước qua proxy. Chỉ đáng khi có nhiều
  service và nhiều ngôn ngữ.

*Database per service*
- Mỗi service có DB riêng, service khác chỉ lấy dữ liệu qua API hoặc event của nó.
- ⚠️ Nhiều service dùng chung một DB là coupling qua schema: đổi một cột có thể làm vỡ service của
  team khác.

**Đọc**
- Martin Fowler: [Microservices](https://martinfowler.com/articles/microservices.html), [MicroservicePrerequisites](https://martinfowler.com/bliki/MicroservicePrerequisites.html)
- microservices.io: [Database per service](https://microservices.io/patterns/data/database-per-service.html)
- *Building Microservices*: chương về communication styles và workflow (orchestration/choreography)
- Istio: [Ambient mode overview](https://istio.io/latest/docs/ambient/overview/), [Ambient reaches GA](https://istio.io/latest/blog/2024/ambient-reaches-ga/)
- Case study ngược chiều: Segment: [Goodbye Microservices](https://segment.com/blog/goodbye-microservices/)

**Nắm chắc khi**
- [ ] Tính được availability của một chuỗi gọi sync và đề xuất chỗ chuyển sang async
- [ ] Nêu được điều kiện tiên quyết còn thiếu trong tổ chức mình trước khi tách service
- [ ] So sánh được sidecar và ambient mode về tài nguyên, cách nâng cấp và phạm vi L4/L7

#### 2.5 Multi-tenancy

**Vì sao cần học:** Hầu hết sản phẩm SaaS B2B đều là multi-tenant, và lỗi nặng nhất có thể xảy ra
là khách hàng A nhìn thấy dữ liệu của khách hàng B. Trong Laravel, lỗi này thường đến từ một raw
query hoặc một queue job quên lọc `tenant_id`. Câu hỏi hay gặp: so sánh ba mô hình, và "khách
enterprise đòi dữ liệu riêng thì làm sao".

**Học gì**

*Ba mô hình*
- *Tenant* là một khách hàng của hệ thống SaaS, thường là một công ty với nhiều user.
  *Multi-tenancy* là một hệ thống phục vụ nhiều tenant cùng lúc.

| | DB per tenant | Schema per tenant | Row per tenant (`tenant_id`) |
|---|---|---|---|
| Isolation | Mạnh nhất | Trung bình | Yếu nhất, dựa vào code |
| Chi phí mỗi tenant | Cao | Trung bình | Thấp nhất |
| Migration | Chạy N lần, dễ lệch | Chạy N lần | Một lần |
| Số tenant hợp lý | Ít, enterprise | Vừa | Rất nhiều (self-serve) |
| Backup/restore một tenant | Dễ | Khá dễ | Khó |
| Data residency (dữ liệu phải nằm ở một quốc gia hay vùng nhất định) | Dễ | Tuỳ | Khó |

- Với MySQL, "schema" và "database" là cùng một thứ. Nên schema per tenant trên MySQL chính là DB
  per tenant trên cùng một server.

*Row per tenant: chống rò dữ liệu*
- ⚠️ Mọi bảng có cột `tenant_id`. Quên `WHERE tenant_id = ?` ở một query là rò dữ liệu giữa khách
  hàng.
- Ba lớp phòng:
  - Eloquent *global scope*: tự thêm điều kiện `tenant_id` vào mọi query của model.
  - PostgreSQL *Row-Level Security* (RLS): DB tự lọc dòng theo policy. MySQL không có RLS.
  - Test tự động thử truy cập chéo tenant.
- `tenant_id` đứng đầu composite index và unique, ví dụ `UNIQUE(tenant_id, email)`, để hai tenant
  có thể có cùng một email.
- ⚠️ Global scope bị bỏ qua trong bốn trường hợp:
  - Query qua `DB::table()`.
  - Raw query.
  - Gọi `withoutGlobalScopes()`.
  - Trong queue job, nếu không khôi phục *tenant context* (thông tin "đang xử lý cho tenant nào").
- Cache key, đường dẫn file và queue cũng phải chứa tenant. Cache key thiếu tenant là nguồn rò hay
  gặp nhất, ví dụ key `dashboard_stats` dùng chung cho mọi tenant.

*Noisy neighbor*
- *Noisy neighbor* là khi một tenant dùng quá nhiều tài nguyên làm chậm các tenant khác.
- Cách chống:
  - Rate limit và quota theo tenant.
  - Xếp lịch queue công bằng giữa tenant (*fair scheduling*).
  - Tách tenant lớn sang DB riêng.

*Hybrid và định danh tenant*
- *Hybrid* (pool + silo): đa số tenant dùng chung (pool), tenant enterprise có DB riêng (silo).
  Cần một lớp routing `tenant → DB` để biết kết nối vào đâu.
- Xác định tenant từ nguồn tin cậy: subdomain đã xác thực, hoặc claim trong token. ⚠️ Không lấy
  từ một tham số client tự gửi lên.
- Package Laravel:
  - `stancl/tenancy`.
  - `spatie/laravel-multitenancy`: hỗ trợ cả single DB và multi DB, tự chuyển tenant context cho
    job.

**Đọc**
- AWS: [SaaS Architecture Fundamentals](https://docs.aws.amazon.com/whitepapers/latest/saas-architecture-fundamentals/saas-architecture-fundamentals.html), [Silo, pool, and bridge models](https://docs.aws.amazon.com/wellarchitected/latest/saas-lens/silo-pool-and-bridge-models.html)
- Postgres: [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- Laravel: [Global Scopes](https://laravel.com/docs/eloquent#global-scopes); [spatie/laravel-multitenancy](https://spatie.be/docs/laravel-multitenancy), [Tenancy for Laravel](https://tenancyforlaravel.com/docs/v3/)
- AWS Builders' Library: [Workload isolation using shuffle-sharding](https://aws.amazon.com/builders-library/workload-isolation-using-shuffle-sharding/) (noisy neighbor ở quy mô lớn)

**Nắm chắc khi**
- [ ] Thiết kế được lớp cưỡng chế `tenant_id` ở ORM, DB, cache key, queue job, và danh sách test (bài tập 5)
- [ ] Chỉ ra được 4 cách global scope bị bỏ qua trong Laravel
- [ ] Lập được kế hoạch chuyển một tenant lớn từ pool sang DB riêng không downtime

---

### Chặng 3: Senior 🔴

#### 3.1 DDD strategic: tìm ranh giới

**Vì sao cần học:** Trước khi tách module hay service, phải biết ranh giới nằm ở đâu. Vẽ sai ranh
giới thì mọi thứ phía sau đều đắt: module gọi chéo liên tục, service phải deploy cùng nhau. Senior
hay bị hỏi "bounded context là gì, xác định thế nào" và "anticorruption layer dùng khi nào".

**Học gì**

*Ubiquitous language*
- *Ubiquitous language* là bộ từ vựng chung giữa dev và người làm nghiệp vụ. Code dùng đúng những
  từ đó: nghiệp vụ nói "xuất hoá đơn" thì code có `issueInvoice()`, không phải `createBill()`.
- Một từ mà hai nơi hiểu hai nghĩa khác nhau là dấu hiệu ở đó có hai bounded context.

*Bounded context*
- *Bounded context* là ranh giới mà bên trong đó một model và bộ từ vựng luôn nhất quán.
- Ví dụ: cùng từ `Product` nhưng ba nơi quan tâm ba thứ khác nhau:
  - Catalog: mô tả, ảnh.
  - Inventory: SKU (mã quản lý hàng tồn), số lượng tồn.
  - Billing: giá, thuế.
- ⚠️ Dùng một class `Product` cho mọi nơi: model khổng lồ, team nào cũng sửa vào, đụng nhau liên
  tục.
- Bounded context là ứng viên tự nhiên cho một module (module 2.3) hoặc một service.

*Context map*
- *Context map* là sơ đồ các bounded context và kiểu quan hệ giữa chúng:

| Kiểu quan hệ | Nghĩa là |
|---|---|
| Partnership | Hai team phối hợp chặt, cùng thành công hoặc cùng thất bại |
| Shared kernel | Hai context dùng chung một phần model. ⚠️ Sửa phần chung phải được cả hai đồng ý |
| Customer/supplier | Bên cung cấp (upstream) lắng nghe nhu cầu của bên dùng (downstream) |
| Conformist | Bên dùng chấp nhận nguyên model của bên cung cấp, không dịch lại |
| **Anticorruption layer** (ACL) | Bên dùng dựng một lớp dịch model bên ngoài sang model của mình. Dùng với hệ cũ hoặc bên thứ ba có model xấu |
| Open host service + published language | Bên cung cấp công bố một API và format chuẩn cho mọi bên dùng |
| Separate ways | Không tích hợp, mỗi bên tự làm |

*Subdomain*
- *Subdomain* là một mảng nghiệp vụ của công ty. Có ba loại:

| Loại | Là gì | Ví dụ | Đầu tư thế nào |
|---|---|---|---|
| Core | Tạo lợi thế cạnh tranh | Thuật toán định giá, ghép chuyến | Tự xây, model kỹ, người giỏi nhất |
| Supporting | Cần cho nghiệp vụ nhưng không tạo khác biệt | Quản lý kho nội bộ | Xây đơn giản |
| Generic | Công ty nào cũng cần như nhau | Auth, email, thanh toán | Mua hoặc dùng SaaS |

- Dùng cách phân loại này để quyết định đầu tư kiến trúc ở đâu. Không áp DDD tactical (module 2.2)
  đồng đều cho mọi phần.

*Event Storming*
- *Event Storming* là buổi workshop với người nghiệp vụ, dán giấy lên tường theo các bước:
  1. Liệt kê mọi domain event theo thời gian ("Đơn đã đặt", "Tiền đã thu").
  2. Thêm *command* (hành động gây ra event) và người thực hiện.
  3. Gom các event và command thành aggregate.
  4. Vẽ ranh giới bounded context ở chỗ ngôn ngữ đổi nghĩa.

**Đọc**
- Martin Fowler: [BoundedContext](https://martinfowler.com/bliki/BoundedContext.html)
- DDD Crew: [Context Mapping](https://github.com/ddd-crew/context-mapping) (có cheat sheet các kiểu quan hệ), [DDD Starter Modelling Process](https://github.com/ddd-crew/ddd-starter-modelling-process)
- *Learning Domain-Driven Design*: phần I (strategic design)
- *Domain-Driven Design* (Evans): phần IV, chương *Maintaining Model Integrity*
- [EventStorming](https://www.eventstorming.com/)

**Nắm chắc khi**
- [ ] Liệt kê được bounded context của dự án mình và vẽ context map (bài tập 1)
- [ ] Phân loại được subdomain của công ty mình thành core/supporting/generic và nói hệ quả đầu tư
- [ ] Thiết kế được ACL khi tích hợp một hệ thống kế toán cũ có model xấu

#### 3.2 Tách service, strangler fig và dữ liệu xuyên service

**Vì sao cần học:** Đây là phần senior được hỏi nhiều nhất trong chủ đề kiến trúc: khi nào tách,
tách thế nào mà không dừng kinh doanh, và làm gì với dữ liệu khi không còn JOIN được. Sai lầm hay
gặp nhất ngoài thực tế là tạo ra một distributed monolith: tách xong mà vẫn phải deploy cùng nhau.

**Học gì**

*Tách theo gì, tách dữ liệu thế nào*
- Tách theo bounded context hoặc khả năng nghiệp vụ (Order, Payment). **Không** tách theo tầng kỹ
  thuật, ví dụ một service "DB access" cho mọi service khác gọi.
- Hai service luôn phải deploy cùng nhau là dấu hiệu ranh giới sai.
- Tách trước phần ít phụ thuộc và có lý do rõ, ví dụ notification hay xử lý file.
- Lý do chính đáng để tách:
  - Cần scale khác hẳn phần còn lại.
  - Nhiều team cần deploy độc lập.
  - Cô lập lỗi hoặc cô lập bảo mật, ví dụ phần xử lý thẻ phải tuân theo chuẩn bảo mật thẻ PCI DSS
    thì tách ra để thu hẹp phạm vi phải kiểm toán.
  - Cần công nghệ khác hẳn.
- Tách dữ liệu là phần khó nhất. Thứ tự an toàn:
  1. Dừng JOIN sang bảng của phần sắp tách.
  2. Chuyển việc đọc sang gọi API hoặc nghe event.
  3. Rồi mới tách DB.

*Strangler fig*
- *Strangler fig* (tên một loại cây mọc bao quanh cây chủ rồi thay thế dần) là cách thay hệ cũ từng
  phần:
  1. Đặt một lớp chặn phía trước hệ cũ (proxy hoặc gateway).
  2. Chuyển dần từng route sang hệ mới.
  3. Đồng bộ dữ liệu giữa hai hệ trong thời gian chuyển tiếp.
  4. Xoá code cũ khi không còn route nào dùng.
- Kỹ thuật đi kèm:
  - ACL (module 3.1) giữa hệ mới và hệ cũ.
  - *CDC* (*change data capture*): đọc log thay đổi của DB (binlog của MySQL) để đồng bộ dữ liệu
    sang hệ mới.
  - *Dark launch* hay *shadow traffic*: gửi bản sao request thật sang hệ mới, so kết quả, nhưng
    vẫn trả người dùng kết quả của hệ cũ.
  - Feature flag chuyển theo phần trăm (module 1.3).
- ⚠️ Viết lại toàn bộ rồi chuyển một lần (*big bang rewrite*) hay thất bại:
  - Không ai nhớ hết tính năng của hệ cũ.
  - Hệ cũ vẫn phải phát triển song song, hệ mới đuổi mãi không kịp.

*Distributed monolith*
- ⚠️ *Distributed monolith* là hệ đã tách thành nhiều service nhưng vẫn dính nhau. Dấu hiệu:
  - Phải deploy cùng nhau.
  - Gọi sync dây chuyền, một service chết là cả chuỗi chết.
  - Dùng chung DB.
  - Shared library chứa domain model, sửa một class phải build lại mọi service.
- Hệ này có mọi cái giá của microservices mà không có lợi ích nào.
- Cách sửa: gộp lại, chuyển các lời gọi không cần kết quả ngay sang event, tách dữ liệu.

*Kích thước service*
- Không có số dòng code "đúng". Tiêu chí thực tế:
  - Một team sở hữu được.
  - Thay đổi thường gặp chỉ đụng một service.
  - Có dữ liệu riêng.
- Quá nhỏ (*nano-service*) cũng là vấn đề: mọi thao tác đều thành chuỗi gọi mạng.

*"JOIN" xuyên service*

| Cách | Làm thế nào | Ưu | ⚠️ Nhược |
|---|---|---|---|
| API composition | Gọi API từng service rồi ghép kết quả ở một chỗ | Đơn giản | Chậm khi phải gọi nhiều (fan-out lớn), khó sort và phân trang theo field của service khác |
| CQRS / read model | Nghe event, dựng sẵn một bảng *denormalize* (gộp sẵn dữ liệu nhiều nguồn) chỉ để đọc | Đọc nhanh, sort/lọc thoải mái | Eventual consistency, dữ liệu có thể trễ vài giây |
| Sao chép dữ liệu cần thiết | Lưu kèm tên, giá sản phẩm lúc đặt vào đơn hàng | Không cần gọi ai | Dữ liệu trùng. Nhưng thường đây là yêu cầu nghiệp vụ thật: giá lúc đặt không được đổi theo giá mới |
| Báo cáo | CDC hoặc ETL đổ vào data warehouse | Không ảnh hưởng production | Có độ trễ |

- *CQRS* (*Command Query Responsibility Segregation*) nghĩa là tách mô hình ghi và mô hình đọc.
- ⚠️ Không query chéo DB production của service khác để làm báo cáo.

*Distributed transaction*
- Tránh *2PC* (*two-phase commit*, giao thức khoá mọi bên tham gia cho tới khi tất cả đồng ý
  commit) xuyên service: chậm, và một bên treo là mọi bên treo.
- Thay bằng: *saga* (chuỗi transaction cục bộ, bước sau lỗi thì chạy bước bù trừ cho các bước
  trước), outbox, và consumer *idempotent* (xử lý cùng một message nhiều lần vẫn cho kết quả như
  một lần). Chi tiết ở [14-distributed-systems.md](14-distributed-systems.md) và
  [12-messaging.md](12-messaging.md).

*Góc Laravel*
- Service tách ra đầu tiên thường là một worker hoặc queue riêng, hoặc một service nhỏ.
- Giữ monolith làm "host", gọi service mới qua HTTP client có timeout và circuit breaker.

**Đọc**
- Martin Fowler: [StranglerFigApplication](https://martinfowler.com/bliki/StranglerFigApplication.html), [CQRS](https://martinfowler.com/bliki/CQRS.html)
- *Monolith to Microservices*: ch.3 (tách chức năng, strangler fig, branch by abstraction) và ch.4 (tách database)
- microservices.io: [API Composition](https://microservices.io/patterns/data/api-composition.html), [Saga](https://microservices.io/patterns/data/saga.html)

**Nắm chắc khi**
- [ ] Lập được kế hoạch strangler fig thay hệ thanh toán cũ: từng bước, cách so kết quả, cách rollback
- [ ] Thiết kế được trang "Đơn hàng của tôi" cần dữ liệu từ Catalog, Shipping, Payment mỗi service một DB, và nói độ trễ đồng bộ chấp nhận được
- [ ] Nhận ra được 4 dấu hiệu distributed monolith trong một sơ đồ cho sẵn

#### 3.3 Tài liệu kiến trúc và ra quyết định

**Vì sao cần học:** Senior được đánh giá qua cách ra quyết định và để lại dấu vết cho người sau,
không chỉ qua code. Một năm sau không ai nhớ vì sao chọn Postgres cho Billing nếu không có ADR.
Câu hỏi hay gặp: "bạn quyết định một thay đổi kiến trúc lớn thế nào, viết tài liệu gì", với red
flag là "team lead quyết".

**Học gì**

*ADR*
- *ADR* (*Architecture Decision Record*) là một file ngắn ghi lại một quyết định kiến trúc quan
  trọng.
  - Nằm trong repo, đánh số tăng dần.
  - Không sửa nội dung ADR cũ. Quyết định bị thay thì tạo ADR mới và đổi status của ADR cũ thành
    "Superseded by ADR-xxx".
- Mẫu của Michael Nygard gồm: Status, Context, Decision, Consequences. Nên thêm Alternatives
  (phương án đã cân nhắc và vì sao loại).

  ```markdown
  # ADR-012: Dùng PostgreSQL thay MySQL cho service Billing
  Status: Accepted (2026-03-02)
  Context: cần JSONB, partial index, RLS cho multi-tenant...
  Decision: dùng PostgreSQL 17 trên RDS.
  Consequences: team cần học vận hành Postgres; migrate 3 bảng...
  Alternatives considered: MySQL 8.4 LTS (thiếu RLS, partial index), MongoDB (mất transaction đa bảng...)
  ```

- ⚠️ Mốc phiên bản trong ADR phải đúng tại thời điểm viết. Ví dụ: MySQL 8.0 đã hết hỗ trợ từ
  04/2026, bản LTS hiện hành là 8.4.

*C4 và RFC*
- *C4 model* vẽ kiến trúc theo bốn mức zoom:
  1. System context: hệ thống của bạn và người dùng, hệ thống bên ngoài.
  2. Container: các thứ chạy riêng như web app, API, DB, queue.
  3. Component: các khối bên trong một container.
  4. Code: class.

  Đa số tài liệu chỉ cần mức 1 và 2. Giữ sơ đồ dạng code (Structurizr, PlantUML, Mermaid) để sửa
  và review được như code.
- *RFC* hay *design doc*: tài liệu viết **trước** khi làm một việc lớn, để người khác góp ý. Gồm:
  - Bối cảnh.
  - Mục tiêu, và **non-goals** (những gì cố ý không làm).
  - Đề xuất.
  - Phương án đã loại và vì sao.
  - Rủi ro.
  - Rollout và rollback.
  - Cách đo thành công.
- Việc nhỏ mà cũng viết RFC là lãng phí.

*Quyết định đảo ngược được và không đảo ngược được*

| | Two-way door (đảo ngược được) | One-way door (khó đảo ngược) |
|---|---|---|
| Ví dụ | Chọn thư viện log, cách đặt tên thư mục | Chọn DB chính, format ID công khai, API public, mô hình multi-tenant, tách service |
| Cách quyết | Nhanh, để team tự quyết | Chậm lại, viết RFC và ADR, thử nhỏ trước |

- Biến quyết định one-way thành two-way khi có thể:
  - Đặt abstraction ở đúng chỗ dễ đổi.
  - Dùng feature flag.
  - Migrate từng bước.

*Quality attributes và fitness function*
- *Quality attributes* là các thuộc tính chất lượng của hệ thống: performance, scalability,
  availability, security, maintainability, cost, time-to-market.
  - Không tối ưu được tất cả cùng lúc. Phải nói rõ ưu tiên cái nào, hy sinh cái nào.
- *Fitness function* là một kiểm tra tự động cho một thuộc tính kiến trúc, để kiến trúc không mục
  dần theo thời gian. Ví dụ:
  - Deptrac cấm import chéo module chạy trong CI.
  - Load test fail nếu p99 (mức latency mà 99% request nhanh hơn) vượt ngưỡng.
- ⚠️ *Resume-driven development*: chọn công nghệ vì muốn học hay muốn ghi vào CV, không vì bài
  toán cần.

**Đọc**
- Michael Nygard: [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions); [adr.github.io](https://adr.github.io/) (các mẫu ADR)
- [C4 model](https://c4model.com/): phần *Diagrams* (system context, container)
- Amazon: [2016 Letter to Shareholders](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders) (đoạn two-way door và ra quyết định với 70% thông tin)
- Thoughtworks: [Fitness function-driven development](https://www.thoughtworks.com/insights/articles/fitness-function-driven-development)
- *Fundamentals of Software Architecture*: phần về architecture characteristics và ADR

**Nắm chắc khi**
- [ ] Viết được một ADR thật đủ context, decision, consequences, alternatives (bài tập 2)
- [ ] Vẽ được C4 mức 1 và 2 cho dự án mình
- [ ] Phân loại được 5 quyết định gần đây của team thành one-way/two-way và nói có quyết định nào đã xử lý sai loại

#### 3.4 Tổ chức: Conway's law và Team Topologies

**Vì sao cần học:** Kiến trúc và cơ cấu team luôn ảnh hưởng lẫn nhau. Tách service mà không đổi
cách chia team thì ranh giới sẽ trượt về lại hình dạng cũ. Senior và lead hay bị hỏi "Conway's law
ảnh hưởng kiến trúc thế nào", và trích sai câu gốc là điểm trừ dễ thấy.

**Học gì**

*Conway's law*
- Câu gốc trong bài báo năm 1968 của Melvin Conway: "organizations which design systems ... are
  constrained to produce designs which are copies of the communication structures of these
  organizations".
  - Nghĩa là: hệ thống một tổ chức làm ra sẽ có cấu trúc giống cách các nhóm trong tổ chức đó
    giao tiếp với nhau.
- Ví dụ trong chính bài báo: 8 người làm hai compiler, 5 người làm COBOL và 3 người làm ALGOL. Kết
  quả: compiler COBOL chạy 5 phase, compiler ALGOL chạy 3 phase.
- ⚠️ Câu "four groups working on a compiler → 4-pass compiler" hay được trích như của Conway,
  nhưng thực ra là của Eric Raymond trong Jargon File.

*Inverse Conway maneuver*
- *Inverse Conway maneuver*: muốn có kiến trúc nào thì tổ chức team theo đúng hình dạng đó trước.
- ⚠️ Dấu hiệu lệch Conway, sẽ có ma sát:
  - Một team sở hữu 15 service.
  - 3 team cùng sửa một service.

*Team Topologies*
- Bốn loại team:

| Loại team | Làm gì |
|---|---|
| Stream-aligned | Làm một luồng giá trị cho người dùng từ đầu tới cuối, ví dụ team Checkout |
| Platform | Cung cấp nền tảng nội bộ (CI/CD, hạ tầng) dưới dạng dịch vụ tự phục vụ |
| Enabling | Giúp các team khác lên tay một kỹ năng mới, rồi rút ra |
| Complicated-subsystem | Sở hữu một phần cần chuyên môn sâu, ví dụ engine định giá |

- Ba kiểu tương tác giữa team:
  - Collaboration: làm chung trong một giai đoạn.
  - X-as-a-service: một team dùng dịch vụ của team kia qua giao diện rõ ràng.
  - Facilitating: một team hướng dẫn team kia.
- Ý chính: giảm *cognitive load* (lượng thứ một team phải hiểu và giữ trong đầu), và làm ranh giới
  service khớp với ranh giới team.

**Đọc**
- Melvin Conway: [How Do Committees Invent?](https://www.melconway.com/Home/Committees_Paper.html) (1968, bài gốc, đọc cả ghi chú của tác giả ở đầu)
- [Jargon File: Conway's Law](http://www.catb.org/jargon/html/C/Conways-Law.html) (nguồn của câu "4-pass compiler")
- Martin Fowler: [Conway's Law](https://martinfowler.com/bliki/ConwaysLaw.html)
- [Team Topologies: Key Concepts](https://teamtopologies.com/key-concepts); sách *Team Topologies* (Skelton, Pais; 2019)

**Nắm chắc khi**
- [ ] Trích đúng câu của Conway và phân biệt được với bản diễn giải trong Jargon File
- [ ] Vẽ được sơ đồ team hiện tại cạnh sơ đồ kiến trúc và chỉ ra chỗ lệch
- [ ] Đề xuất được cách tổ chức team khi tách monolith thành 4 bounded context

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Controller, service, repository mỗi tầng làm gì?** (1.1)
- Ý phải có: controller mỏng; service/use case điều phối; repository giấu lưu trữ; tầng trên gọi tầng dưới
- Điểm cộng: pass-through layer; Laravel Action/FormRequest

**2. Logic nghiệp vụ nên đặt trong controller, model hay service?** (1.1, 2.2)
- Ý phải có: quy tắc thuần ở domain (entity/value object), điều phối ở application service, controller mỏng
- Điểm cộng: với CRUD thì không cần nhiều tầng; mức đầu tư theo độ phức tạp
- Red flag: "luôn trong service" mà không nói vì sao

**3. 12-factor app là gì? Vì sao app phải stateless?** (1.2)
- Ý phải có: config qua env, stateless, log ra stdout, graceful shutdown; stateless để scale ngang và thay instance tự do
- Điểm cộng: session/file local là vi phạm; Octane và queue worker là process sống lâu

**4. Monolith có gì tốt?** (1.2)
- Ý phải có: gọi hàm, ACID, debug dễ, vận hành rẻ, refactor dễ
- Điểm cộng: vấn đề thường là thiếu ranh giới, không phải một đơn vị deploy

**5. Vì sao `env()` trong controller trả `null` trên production?** (1.3)
- Ý phải có: `config:cache` làm `.env` không được đọc nữa; chỉ gọi `env()` trong `config/`

### 🟡 Mid

**6. Hexagonal khác layered ở điểm nào?** (2.1)
- Ý phải có: hướng phụ thuộc; lõi định nghĩa port, hạ tầng là adapter; test lõi không cần DB
- Điểm cộng: cái giá mapping; áp cho module core, không cho cả app

**7. Entity khác value object thế nào? Cho ví dụ value object.** (2.2)
- Ý phải có: identity so với giá trị; immutable; `Money`, `Email`
- Điểm cộng: value object làm cast Eloquent; readonly class

**8. Aggregate là gì? Vì sao một transaction chỉ nên sửa một aggregate?** (2.2)
- Ý phải có: đơn vị nhất quán, truy cập qua root, bảo vệ invariant; 4 quy tắc Vernon
- Điểm cộng: aggregate to gây tranh chấp; eventual consistency giữa aggregate qua domain event sau commit

**9. Modular monolith là gì? Làm sao ngăn module truy cập bảng của nhau?** (2.3)
- Ý phải có: một đơn vị deploy, ranh giới cưỡng chế; public API hoặc event; không JOIN chéo
- Điểm cộng: Deptrac trong CI; quan hệ Eloquent sang model module khác là JOIN trá hình; Shopify/Packwerk

**10. Lợi ích và cái giá của microservices? Điều kiện tiên quyết?** (2.4)
- Ý phải có: deploy/scale độc lập so với network, mất ACID, observability, vận hành
- Điểm cộng: điều kiện tiên quyết cụ thể; availability chuỗi sync là tích
- Red flag: "microservices vì scale tốt, hiện đại"

**11. API gateway và BFF khác nhau thế nào?** (2.4)
- Ý phải có: một điểm vào chung với cross-cutting concern so với backend riêng cho từng loại client
- Điểm cộng: logic nghiệp vụ lọt vào BFF và bị lặp; team frontend sở hữu BFF

**12. Orchestration và choreography khác nhau thế nào? Khi nào chọn cái nào?** (2.4)
- Ý phải có: điều khiển tập trung so với phản ứng theo event
- Điểm cộng: choreography khó thấy toàn cảnh khi luồng dài; workflow engine (Temporal) cho saga nhiều bước

**13. Service mesh giải quyết gì? Có bắt buộc sidecar không?** (2.4)
- Ý phải có: mTLS, retry/timeout, traffic splitting, telemetry ngoài code
- Điểm cộng: Istio ambient mode GA không cần sidecar (ztunnel L4, waypoint L7); chỉ đáng khi nhiều service
- Red flag: "service mesh là mỗi pod một sidecar" như mô hình duy nhất

**14. So sánh ba mô hình multi-tenancy.** (2.5)
- Ý phải có: isolation, chi phí, migration, số tenant, compliance
- Điểm cộng: MySQL không có RLS; global scope bị bỏ qua ở raw query và job; hybrid cho tenant lớn
- Red flag: "thêm cột `tenant_id` là xong"

### 🔴 Senior

**15. Monolith Laravel 5 năm tuổi, 8 dev, deploy mỗi tuần hay vỡ. CTO muốn chuyển microservices.** (2.3, 3.2)
- Ý phải có: hỏi vấn đề thật (thiếu test, coupling, tải); modular hoá trước, Deptrac, cắt JOIN chéo; cải thiện CI/CD, test, feature flag
- Điểm cộng: 8 dev khó vận hành nhiều service; nếu tách thì chọn một phần có lý do rõ, strangler fig
- Red flag: đồng ý tách ngay theo tầng kỹ thuật

**16. Khi nào bạn tách một module ra thành service? Tách thế nào?** (3.2)
- Ý phải có: lý do cụ thể (scale, deploy độc lập, cô lập lỗi/bảo mật); theo bounded context; tách dữ liệu từng bước
- Điểm cộng: ranh giới module phải đúng trước; kế hoạch rollback

**17. Ba service luôn phải deploy cùng lúc, một cái chết là cả hệ thống lỗi.** (3.2)
- Ý phải có: distributed monolith; vẽ lại dependency; chung DB, shared library domain model
- Điểm cộng: chuyển gọi không cần kết quả ngay sang event; timeout, circuit breaker; cân nhắc gộp lại

**18. Làm sao lấy dữ liệu "JOIN" từ ba service có DB riêng?** (3.2)
- Ý phải có: API composition, read model qua event, sao chép dữ liệu cần thiết
- Điểm cộng: chọn theo nhu cầu sort/filter; độ trễ đồng bộ và cách hiển thị khi chưa về; snapshot tên/giá lúc đặt là yêu cầu nghiệp vụ
- Red flag: "JOIN sang DB bên đó"

**19. Bounded context là gì? Xác định ranh giới thế nào?** (3.1)
- Ý phải có: ranh giới của model và ngôn ngữ nhất quán; một từ hai nghĩa là dấu hiệu
- Điểm cộng: Event Storming; khớp với team; subdomain core/supporting/generic

**20. Anticorruption layer dùng khi nào?** (3.1)
- Ý phải có: tích hợp hệ cũ hoặc bên thứ ba có model xấu; dịch sang model của mình
- Điểm cộng: dùng trong strangler fig giữa hệ mới và cũ

**21. SaaS B2B dùng `tenant_id`, một khách enterprise yêu cầu dữ liệu tách riêng và đặt ở EU.** (2.5)
- Ý phải có: hybrid, routing tenant → DB; migrate một tenant không downtime (CDC hoặc dual write, cutover)
- Điểm cộng: cache, object storage, log, backup cũng phải tuân thủ data residency

**22. Thay hệ thanh toán cũ (framework hết hỗ trợ) mà không dừng kinh doanh.** (3.2)
- Ý phải có: strangler fig qua gateway; ACL; shadow traffic hoặc chạy song song và đối soát
- Điểm cộng: chuyển theo % hoặc nhóm merchant bằng flag; rollback từng bước

**23. Conway's law ảnh hưởng tới kiến trúc thế nào?** (3.4)
- Ý phải có: kiến trúc phản chiếu cấu trúc giao tiếp; inverse Conway maneuver
- Điểm cộng: trích đúng câu gốc và ví dụ COBOL 5 phase/ALGOL 3 phase; biết câu "4-pass compiler" là của Jargon File; Team Topologies

**24. Bạn quyết định một thay đổi kiến trúc lớn như thế nào? Viết tài liệu gì?** (3.3)
- Ý phải có: phân loại reversible/irreversible; RFC trước, ADR sau; thử nhỏ; định nghĩa cách đo thành công
- Điểm cộng: quality attributes ưu tiên; fitness function để kiến trúc không mục dần
- Red flag: "team lead quyết"

**25. Có nên dùng Clean Architecture cho dự án Laravel không?** (2.1, 2.2)
- Ý phải có: chỉ cho phần core có nghiệp vụ phức tạp và sống lâu; cái giá mapping và mất tiện lợi Eloquent
- Điểm cộng: lý do thật là test và cô lập nghiệp vụ, không phải để thay framework; thư mục `Domain/` không tự làm ra DDD

---

## Bài tập tự làm

1. Lấy một dự án bạn đang làm, vẽ sơ đồ C4 mức 1 và mức 2. Liệt kê các bounded context bạn thấy và chỗ nào
   đang vi phạm ranh giới (JOIN chéo, model dùng chung).
2. Viết một ADR thật cho một quyết định bạn từng đưa ra (hoặc từng thấy), có đủ context, decision,
   consequences và alternatives. Kiểm tra mọi mốc phiên bản trong ADR còn đúng.
3. Mô hình hoá aggregate `Order` cho một shop: xác định invariant, entity, value object, các domain event.
   Viết code (PHP, Java hoặc Go) cho `Money` là value object; nếu dùng Laravel, viết thêm custom cast.
4. Viết một RFC 1–2 trang: chuyển một monolith có module Order, Payment, Notification sang modular monolith,
   nêu bước đi, cách cưỡng chế ranh giới (Deptrac), rủi ro và cách rollback.
5. Thiết kế lớp cưỡng chế `tenant_id` cho một app row-per-tenant: ở tầng ORM, ở tầng DB, ở cache key, ở queue job;
   liệt kê test cần có.
6. Chạy một app Laravel nhỏ bằng Octane, viết một singleton giữ state của request, tái hiện việc rò dữ liệu giữa
   hai request, rồi sửa. Ghi lại cách bạn phát hiện.

> Nộp bài vào đây để được review.
