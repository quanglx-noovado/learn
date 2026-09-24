# 15. Kiến trúc phần mềm

> [← Mục lục](README.md) · Phạm vi: cách tổ chức code bên trong một service (layered, hexagonal, clean), DDD, monolith và microservices, giao tiếp giữa service, multi-tenancy, 12-factor, tài liệu kiến trúc và cách ra quyết định kiến trúc.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Kiến trúc bên trong một service**
- [ ] 🟢 Layered architecture: controller, service, repository; mỗi tầng được phép làm gì
- [ ] 🟢 MVC và giới hạn của nó (MVC là pattern cho tầng giao diện, không phải kiến trúc cả ứng dụng)
- [ ] ⚠️ Fat controller, fat model; logic nghiệp vụ nên nằm ở đâu
- [ ] 🟡 Service layer, application service và domain service khác nhau thế nào
- [ ] 🟡 Hexagonal (ports & adapters)
- [ ] 🟡 Clean Architecture, Onion Architecture; dependency rule
- [ ] 🔴 So sánh các kiểu trên và khi nào đáng dùng, khi nào là over-engineering
- [ ] 🟡 Vertical slice architecture (tổ chức theo tính năng thay vì theo tầng)

**DDD**
- [ ] 🟡 Ubiquitous language
- [ ] 🟡 Bounded context
- [ ] 🔴 Context map: shared kernel, customer/supplier, conformist, anticorruption layer, open host service, published language
- [ ] 🔴 Subdomain: core, supporting, generic
- [ ] 🟡 Entity và value object
- [ ] 🟡 Aggregate, aggregate root và 4 quy tắc aggregate
- [ ] 🟡 Domain event
- [ ] 🟡 Repository (theo nghĩa DDD, mỗi aggregate một repository)
- [ ] 🟡 Domain service, application service
- [ ] 🔴 Anemic domain model vs rich domain model

**Monolith và microservices**
- [ ] 🟢 Monolith: ưu điểm thật sự, không phải "cái cũ"
- [ ] 🟡 Modular monolith: ranh giới module, public API của module, không đụng bảng của module khác
- [ ] 🟡 Microservices: lợi ích, cái giá, điều kiện tiên quyết
- [ ] 🔴 Cách tách service: theo bounded context, theo khả năng nghiệp vụ, không theo tầng kỹ thuật
- [ ] 🔴 Strangler fig migration
- [ ] ⚠️ Distributed monolith (anti-pattern)
- [ ] 🔴 Kích thước service: quá nhỏ (nano-service) cũng là vấn đề

**Giao tiếp giữa service**
- [ ] 🟡 Sync (HTTP/gRPC) và async (event, message); temporal coupling
- [ ] 🟡 Orchestration và choreography
- [ ] 🟡 API gateway, BFF (Backend for Frontend)
- [ ] 🟡 Service discovery (client-side, server-side, DNS)
- [ ] 🔴 Service mesh (đại ý: sidecar, mTLS, retry, observability)
- [ ] 🟡 Database per service; ⚠️ JOIN xuyên service
- [ ] 🔴 API composition, CQRS/read model, dữ liệu sao chép qua event
- [ ] 🔴 Distributed transaction: saga, outbox (chi tiết ở [14](14-distributed-systems.md), [12](12-messaging.md))

**Multi-tenancy**
- [ ] 🟡 DB per tenant, schema per tenant, row per tenant (`tenant_id`)
- [ ] 🔴 Noisy neighbor, tenant isolation, hybrid (tenant lớn tách riêng)
- [ ] ⚠️ Quên lọc `tenant_id` = rò dữ liệu giữa khách hàng

**Cấu hình và vận hành**
- [ ] 🟢 12-factor app
- [ ] 🟡 Configuration: env var, config service, secret tách khỏi config
- [ ] 🟡 Feature flag như công cụ kiến trúc (release, ops, experiment, permission); nợ flag

**Tài liệu và ra quyết định**
- [ ] 🟡 ADR (Architecture Decision Record)
- [ ] 🟡 C4 model: context, container, component, code
- [ ] 🔴 RFC/design doc: cấu trúc, khi nào cần
- [ ] 🔴 Conway's law, inverse Conway maneuver
- [ ] 🔴 Team Topologies (đại ý)
- [ ] 🔴 Reversible vs irreversible decision (two-way door vs one-way door)
- [ ] 🔴 Quality attributes (-ility) và fitness function

## Chi tiết

### Kiến trúc bên trong một service

- [ ] **Layered architecture** 🟢
  - Các tầng phổ biến: presentation (controller) → application/service → domain → infrastructure (repository, client gọi API ngoài)
  - Quy tắc: tầng trên gọi tầng dưới, không gọi ngược. Controller không viết SQL; repository không biết HTTP
  - Controller làm gì: parse request, validate đầu vào ở mức hình thức, gọi service, map kết quả sang response. Không chứa quy tắc nghiệp vụ
  - ⚠️ Layered cổ điển để domain **phụ thuộc** vào tầng persistence (service gọi thẳng ORM). Đây là điểm hexagonal/clean sửa
  - ⚠️ "Pass-through layer": service chỉ gọi lại repository một dòng. Không sai, nhưng nếu toàn bộ app như vậy thì tầng đó chưa có lý do tồn tại
- [ ] **MVC và giới hạn** 🟢
  - MVC gốc là pattern cho UI. Trong web framework (Laravel, Spring MVC, Rails), "Model" thường bị hiểu là ORM model, nên mọi logic dồn vào model hoặc controller
  - MVC không nói gì về: logic nghiệp vụ đặt ở đâu, gọi API ngoài ở đâu, transaction bao quanh cái gì, job/queue/CLI dùng lại logic thế nào
  - Dấu hiệu vượt quá MVC: cùng một nghiệp vụ cần gọi từ HTTP, từ job queue và từ command line → cần service layer
- [ ] **Fat controller, fat model** ⚠️
  - Fat controller: logic nghiệp vụ nằm trong action, không dùng lại được, test phải dựng HTTP request
  - Fat model (ActiveRecord "god model"): `User` có 3.000 dòng, trộn quy tắc nghiệp vụ, query, gửi mail, gọi API
  - Câu trả lời tốt: logic nghiệp vụ thuần nằm ở domain (entity/value object hoặc domain service); điều phối use case (mở transaction, gọi repository, phát event) nằm ở application service; controller mỏng
  - Không có câu trả lời "luôn luôn": CRUD đơn giản thì logic trong controller + model cũng chấp nhận được
- [ ] **Service layer** 🟡
  - Application service = một use case (`PlaceOrder`, `CancelSubscription`). Điều phối, không chứa quy tắc sâu
  - Domain service = quy tắc nghiệp vụ không thuộc tự nhiên về một entity (tính phí vận chuyển dựa trên nhiều aggregate)
  - ⚠️ "Service" chứa mọi thứ, entity chỉ còn getter/setter → anemic domain model. Chấp nhận được với domain đơn giản, thành vấn đề khi quy tắc nhiều và bị lặp khắp nơi
- [ ] **Hexagonal (ports & adapters)** 🟡
  - Lõi ứng dụng định nghĩa **port** (interface): port vào (use case mà bên ngoài gọi) và port ra (thứ lõi cần: lưu đơn hàng, gửi email, gọi cổng thanh toán)
  - **Adapter** hiện thực port: HTTP controller, consumer Kafka, CLI là adapter vào; repository MySQL, client Stripe là adapter ra
  - Lợi ích: đổi hạ tầng không đụng lõi; test lõi bằng adapter giả (in-memory) mà không cần DB
  - ⚠️ Cái giá: nhiều interface, nhiều mapping (entity ↔ ORM model ↔ DTO). Với app CRUD là thừa

  ```
          HTTP ─┐                          ┌─► MySQL adapter
          Kafka ├─► [port vào] LÕI [port ra]├─► Stripe adapter
          CLI  ─┘     (use case, domain)    └─► SMTP adapter
  ```
- [ ] **Clean Architecture, Onion** 🟡
  - Cùng tư tưởng với hexagonal, vẽ bằng vòng tròn đồng tâm: entities → use cases → interface adapters → frameworks & drivers
  - **Dependency rule**: phụ thuộc trong source code chỉ hướng vào trong. Lõi không import framework, ORM, HTTP
  - Onion: domain model ở giữa, domain services, application services, rồi infrastructure/UI ở ngoài. Khác biệt với Clean chủ yếu là cách đặt tên
  - Cách đạt được: dependency inversion (lõi khai báo interface, tầng ngoài hiện thực, DI container ráp lại) — xem [08-oop-design.md](08-oop-design.md)
- [ ] **So sánh và khi nào đáng dùng** 🔴

  | Kiểu | Hợp khi | Không hợp khi |
  |---|---|---|
  | MVC + model của framework | CRUD, admin, prototype, team nhỏ | Nghiệp vụ nhiều quy tắc, nhiều entry point |
  | Layered + service layer | Đa số app nghiệp vụ vừa | Cần thay hạ tầng thường xuyên |
  | Hexagonal / Clean / Onion | Domain phức tạp, sống lâu, nhiều adapter, cần test lõi độc lập | App đơn giản, deadline gấp, team chưa quen |
  | Vertical slice | Nhiều tính năng độc lập, mỗi tính năng tự chọn độ phức tạp | Logic dùng chung nhiều giữa các tính năng |

  - Góc senior: kiến trúc là **mức đầu tư** tương xứng với độ phức tạp và tuổi thọ. Có thể áp hexagonal chỉ cho module core, phần còn lại CRUD đơn giản
  - ⚠️ Framework-agnostic tuyệt đối hiếm khi đáng. Thay framework cả app là chuyện rất hiếm; tách lõi để **test** và để **hiểu** thường là lý do thật
- **Đối chiếu:** Laravel khuyến khích ActiveRecord (Eloquent) nên dễ ra fat model; Spring có sẵn phân tầng `@Controller`/`@Service`/`@Repository` và JPA (Data Mapper); Go không có framework áp đặt, thường tổ chức theo package domain + interface nhỏ khai báo ở phía dùng

### DDD — strategic design

- [ ] **Ubiquitous language** 🟡
  - Dev và người nghiệp vụ dùng chung một bộ từ, và code dùng đúng từ đó (class, method, event)
  - Một từ có hai nghĩa ở hai nơi ("Customer" ở bán hàng khác "Customer" ở chăm sóc khách hàng) là dấu hiệu có hai bounded context
- [ ] **Bounded context** 🟡
  - Ranh giới trong đó một model và ngôn ngữ có nghĩa nhất quán. Ngoài ranh giới, cùng khái niệm có thể được mô hình khác
  - Ví dụ: `Product` ở Catalog có mô tả, ảnh, SEO; ở Inventory chỉ có SKU và số lượng; ở Billing có giá và thuế
  - ⚠️ Cố làm một `Product` dùng cho mọi nơi → model khổng lồ, mọi team đụng nhau
  - Bounded context là ứng viên tự nhiên cho module (modular monolith) hoặc service
- [ ] **Context map** 🔴 — quan hệ giữa các bounded context
  - Partnership: hai team cùng thành bại, phối hợp chặt
  - Shared kernel: dùng chung một phần model/code; ⚠️ phải đồng thuận khi sửa
  - Customer/supplier: upstream cung cấp, downstream có tiếng nói về nhu cầu
  - Conformist: downstream chấp nhận nguyên model của upstream (thường với vendor lớn)
  - **Anticorruption layer (ACL)**: lớp dịch model bên ngoài sang model của mình. Dùng khi tích hợp hệ thống cũ hoặc bên thứ ba có model xấu
  - Open host service + published language: upstream mở API/format chuẩn cho nhiều bên dùng
  - Separate ways: không tích hợp, mỗi bên tự làm
- [ ] **Subdomain** 🔴
  - Core: tạo lợi thế cạnh tranh, đầu tư người giỏi nhất, tự xây, model kỹ
  - Supporting: cần cho nghiệp vụ nhưng không khác biệt; xây đơn giản
  - Generic: bài toán ai cũng có (auth, email, thanh toán, kế toán); ưu tiên mua/dùng SaaS/thư viện
  - Góc senior: dùng phân loại này để quyết định đầu tư kiến trúc ở đâu, không áp DDD tactical đồng đều cho mọi thứ

### DDD — tactical design

- [ ] **Entity** 🟡: có identity tồn tại qua thời gian; hai entity bằng nhau khi cùng id dù thuộc tính khác
- [ ] **Value object** 🟡
  - Không có identity, bằng nhau khi mọi thuộc tính bằng nhau, **immutable**
  - Ví dụ: `Money(amount, currency)`, `Email`, `Address`, `DateRange`
  - Lợi ích: validate một lần khi tạo, gom hành vi (`Money.add` kiểm tra cùng currency), tránh "primitive obsession"
  - ⚠️ Dùng `float` cho tiền thay vì value object với số nguyên/decimal — xem [22-practical-data.md](22-practical-data.md)
- [ ] **Aggregate** 🟡
  - Cụm entity + value object được coi là **một đơn vị nhất quán**; bên ngoài chỉ được truy cập qua **aggregate root**
  - Ví dụ: `Order` (root) chứa `OrderLine`. Không ai sửa `OrderLine` trực tiếp; gọi `order.addLine()` để root kiểm tra invariant (tổng tiền, số dòng tối đa, trạng thái cho phép sửa)
  - **4 quy tắc** (theo Vaughn Vernon):
    1. Bảo vệ invariant thật sự bên trong ranh giới aggregate
    2. Thiết kế aggregate **nhỏ**
    3. Tham chiếu aggregate khác **bằng id**, không bằng object reference
    4. Giữa các aggregate dùng **eventual consistency** (qua domain event)
  - Một transaction chỉ sửa **một** aggregate. Cần sửa hai aggregate cùng lúc thường là dấu hiệu ranh giới sai, hoặc phải chấp nhận eventual consistency
  - ⚠️ Aggregate quá to (`Customer` chứa mọi `Order`): load chậm, tranh chấp lock/optimistic version liên tục
  - Concurrency: thường dùng optimistic locking theo version của aggregate root
- [ ] **Domain event** 🟡
  - Sự việc đã xảy ra, đặt tên thì quá khứ: `OrderPlaced`, `PaymentFailed`
  - Dùng để aggregate khác/bounded context khác phản ứng mà không coupling trực tiếp
  - ⚠️ Phát event sau commit DB, hoặc dùng outbox. Phát trong transaction rồi transaction rollback → event "ma" — xem [12-messaging.md](12-messaging.md)
  - Phân biệt domain event (nội bộ context) và integration event (hợp đồng công khai giữa context, phải versioning)
- [ ] **Repository** 🟡
  - Giả lập một collection các aggregate: `orders.get(id)`, `orders.save(order)`. Mỗi aggregate root một repository, không có repository cho `OrderLine`
  - Interface nằm ở domain, implementation nằm ở infrastructure
  - ⚠️ Repository với 40 method `findByXAndYOrderByZ` cho màn hình báo cáo → tách read model/query service riêng (CQRS nhẹ)
- [ ] **Domain service** 🟡: logic nghiệp vụ không thuộc về một entity; stateless; đặt tên theo ngôn ngữ nghiệp vụ (`TransferService`, `PricingPolicy`)
- [ ] **Anemic vs rich domain model** 🔴
  - Anemic: entity chỉ có dữ liệu, logic ở service. Đơn giản, quen thuộc, nhưng invariant dễ bị bỏ qua vì ai cũng set được field
  - Rich: entity tự bảo vệ trạng thái (`order.cancel()` ném exception nếu đã giao)
  - Góc senior: core subdomain nên rich; CRUD supporting thì anemic là đủ

### Monolith, modular monolith, microservices

- [ ] **Monolith** 🟢
  - Một đơn vị deploy. Ưu điểm: gọi hàm thay vì gọi mạng, transaction ACID tự nhiên, debug/trace dễ, refactor xuyên module dễ, vận hành rẻ
  - Nhược khi lớn: build/test chậm, deploy chung rủi ro chung, nhiều team giẫm chân nhau, không scale riêng phần nóng, một memory leak làm sập tất cả
  - ⚠️ "Monolith" ≠ "big ball of mud". Vấn đề thường là thiếu ranh giới, không phải một đơn vị deploy
- [ ] **Modular monolith** 🟡
  - Một đơn vị deploy, nhưng chia module theo bounded context với ranh giới được **cưỡng chế**
  - Quy tắc:
    - Module chỉ gọi nhau qua public API (interface/facade) hoặc event nội bộ
    - ⚠️ **Không query/JOIN bảng của module khác.** Mỗi module sở hữu bảng của nó (có thể tách schema)
    - Không chia sẻ entity/ORM model giữa module; trao đổi bằng DTO hoặc id
  - Cưỡng chế bằng công cụ: ArchUnit (Java), Spring Modulith, Deptrac (PHP), package `internal/` (Go); kiểm tra trong CI
  - Lợi ích: khi cần tách service, ranh giới đã sẵn; chi phí vận hành vẫn là monolith
- [ ] **Microservices** 🟡
  - Lợi ích: deploy độc lập, scale độc lập, cô lập lỗi (nếu thiết kế đúng), team tự chủ, chọn công nghệ riêng
  - Cái giá:
    - Network: latency, lỗi một phần, timeout, retry — xem [14-distributed-systems.md](14-distributed-systems.md)
    - Mất transaction ACID xuyên service → saga, outbox, eventual consistency
    - Observability bắt buộc: tracing, log tập trung, correlation id
    - Vận hành: CI/CD mỗi service, service discovery, config, secret, versioning API
    - Test tích hợp khó hơn; contract test
    - Dữ liệu trùng lặp, đồng bộ dữ liệu
  - **Điều kiện tiên quyết** (thiếu thì đừng tách): CI/CD tự động, provisioning nhanh (container/K8s hoặc tương đương), monitoring + alerting + tracing, team đủ người để sở hữu từng service, ranh giới domain đã rõ
  - ⚠️ Câu trả lời trưởng thành: bắt đầu với monolith gọn gàng (có module rõ ràng), tách service khi có lý do cụ thể: một phần cần scale khác hẳn, cần deploy độc lập vì nhiều team, cần cô lập lỗi/bảo mật (ví dụ phần xử lý thẻ theo PCI DSS), hoặc công nghệ khác hẳn
- [ ] **Cách tách service** 🔴
  - Tách theo bounded context / khả năng nghiệp vụ (Order, Payment, Catalog), **không** theo tầng kỹ thuật (service "DB access", service "validation")
  - Mục tiêu: high cohesion bên trong, low coupling bên ngoài. Hai service luôn phải deploy cùng nhau → ranh giới sai
  - Tách phần dễ tách và có giá trị trước (ít phụ thuộc, có lý do scale/deploy rõ)
  - Tách dữ liệu là phần khó nhất: dừng JOIN, chuyển đọc qua API/event, rồi mới tách DB
- [ ] **Strangler fig migration** 🔴
  - Thay hệ thống cũ từng phần: đặt một lớp chặn phía trước (proxy/gateway), chuyển dần từng route/tính năng sang hệ mới, hệ cũ co lại tới khi bỏ được
  - Các bước: (1) chọn một lát cắt, (2) xây ở hệ mới, (3) định tuyến traffic (có thể từng %), (4) đồng bộ dữ liệu hai chiều nếu cần trong thời gian chuyển tiếp, (5) xoá code cũ
  - Kỹ thuật đi kèm: ACL giữa mới và cũ, change data capture để đồng bộ dữ liệu, dark launch / shadow traffic để so kết quả
  - ⚠️ Rewrite toàn bộ một lần ("big bang") hay thất bại: tính năng cũ không ai nhớ hết, hệ cũ vẫn phải phát triển song song
- [ ] **Distributed monolith** ⚠️
  - Có nhiều service nhưng: phải deploy cùng nhau, gọi sync dây chuyền, dùng chung DB, thay đổi một tính năng phải sửa 5 service
  - Có mọi cái giá của microservices mà không có lợi ích
  - Dấu hiệu: shared library chứa domain model, release train chung, một service chết kéo cả hệ thống, chuỗi gọi sync sâu (A → B → C → D)
  - Cách sửa: gộp các service dính nhau lại, chuyển gọi sync sang event khi không cần kết quả ngay, tách dữ liệu
- [ ] **Kích thước service** 🔴: không có số dòng code "đúng". Thước đo tốt hơn: một team sở hữu được, thay đổi nghiệp vụ thường gặp chỉ đụng một service, có dữ liệu riêng

### Giao tiếp giữa service

- [ ] **Sync vs async** 🟡

  | | Sync (HTTP/REST, gRPC) | Async (queue, event) |
  |---|---|---|
  | Khi dùng | Cần kết quả ngay (query, validate) | Việc có thể làm sau, thông báo sự việc |
  | Coupling | Temporal coupling: bên nhận phải sống | Bên nhận có thể chết tạm, message chờ |
  | Availability | Tích các availability trong chuỗi gọi | Cô lập lỗi tốt hơn |
  | Độ phức tạp | Dễ hiểu, dễ debug | Eventual consistency, trùng/lệch thứ tự, cần DLQ |

  - Availability chuỗi sync: 5 service mỗi cái 99,9% gọi nối tiếp → khoảng 99,5% (0,999^5)
  - ⚠️ Chuỗi sync phải có timeout, retry có giới hạn, circuit breaker — xem [14-distributed-systems.md](14-distributed-systems.md)
- [ ] **Orchestration vs choreography** 🟡
  - Orchestration: một service trung tâm (hoặc workflow engine như Temporal, Camunda) điều khiển các bước. Dễ theo dõi luồng, có điểm tập trung
  - Choreography: mỗi service nghe event và tự phản ứng. Coupling lỏng, nhưng luồng nghiệp vụ khó thấy toàn cảnh, dễ thành "event spaghetti"
- [ ] **API gateway** 🟡: một điểm vào cho client; routing, auth, rate limit, TLS termination, logging, có thể aggregation. ⚠️ Đừng đưa logic nghiệp vụ vào gateway. Chi tiết ở [09-api-design.md](09-api-design.md)
- [ ] **BFF (Backend for Frontend)** 🟡
  - Mỗi loại client (web, mobile, partner) có một backend riêng, gom và định hình dữ liệu cho đúng màn hình
  - Lý do: mobile cần payload nhỏ, ít round trip; web cần dữ liệu khác; tránh một API chung phình to vì mọi client
  - Team frontend thường sở hữu BFF. ⚠️ Logic nghiệp vụ lọt vào BFF và bị lặp giữa các BFF
- [ ] **Service discovery** 🟡: client-side (client hỏi registry như Consul/Eureka rồi tự chọn instance), server-side (qua load balancer), DNS-based (Kubernetes Service)
- [ ] **Service mesh** 🔴 (đại ý)
  - Mỗi pod có một sidecar proxy (Envoy trong Istio; Linkerd dùng proxy riêng) chặn traffic vào/ra
  - Cung cấp ngoài code: mTLS giữa service, retry/timeout, circuit breaking, traffic splitting (canary), metric và trace
  - Cái giá: thêm latency mỗi hop, thêm thành phần phức tạp để vận hành. Chỉ đáng khi có nhiều service và nhiều ngôn ngữ
- [ ] **Database per service** 🟡
  - Mỗi service sở hữu dữ liệu của mình; service khác chỉ truy cập qua API/event. Đây là điều kiện để deploy và thay đổi schema độc lập
  - ⚠️ Chung DB = coupling qua schema: đổi một cột phải phối hợp nhiều team
- [ ] **JOIN xuyên service** 🔴 — ba cách chính
  - **API composition**: một service (hoặc BFF/gateway) gọi nhiều service rồi ghép trong bộ nhớ. Đơn giản; ⚠️ chậm khi fan-out lớn, khó phân trang/sort theo field của service khác, availability là tích
  - **CQRS / read model**: service đọc nghe event từ các service nguồn, dựng sẵn bảng đã denormalize để query. Nhanh, query linh hoạt; đánh đổi eventual consistency và công đồng bộ
  - **Sao chép dữ liệu cần thiết**: service Order lưu kèm tên sản phẩm, giá tại thời điểm đặt (đây thường là yêu cầu nghiệp vụ thật, không chỉ là cache)
  - Báo cáo tổng hợp: đổ dữ liệu vào data warehouse (CDC/ETL), không query chéo DB production
- [ ] **Distributed transaction** 🔴: tránh 2PC xuyên service; dùng saga (các bước có compensating action) + transactional outbox + consumer idempotent. Chi tiết ở [14-distributed-systems.md](14-distributed-systems.md) và [12-messaging.md](12-messaging.md)

### Multi-tenancy

- [ ] **Ba mô hình** 🟡

  | | DB per tenant | Schema per tenant | Row per tenant (`tenant_id`) |
  |---|---|---|---|
  | Isolation | Mạnh nhất | Trung bình | Yếu nhất, dựa vào code |
  | Chi phí mỗi tenant | Cao | Trung bình | Thấp nhất |
  | Migration | Chạy N lần, lâu, dễ lệch phiên bản | Chạy N lần | Chạy một lần |
  | Số tenant hợp lý | Ít, tenant lớn (enterprise) | Vừa | Rất nhiều (SaaS self-serve) |
  | Backup/restore một tenant | Dễ | Khá dễ | Khó |
  | Compliance (data residency) | Dễ đặt DB theo vùng | Tuỳ | Khó |

- [ ] **Row per tenant — cạm bẫy** ⚠️
  - Quên `WHERE tenant_id = ?` ở một query = rò dữ liệu khách này sang khách khác, sự cố bảo mật nghiêm trọng
  - Phòng: global scope trong ORM (Eloquent global scope, Hibernate filter), Row-Level Security của PostgreSQL, test tự động kiểm tra truy cập chéo tenant
  - `tenant_id` phải nằm đầu trong composite index và trong unique constraint (`UNIQUE(tenant_id, email)`)
  - Cache key, tên file trên object storage, topic/queue cũng phải có tenant; ⚠️ cache key thiếu tenant là nguồn rò rỉ hay gặp
- [ ] **Noisy neighbor** 🔴: một tenant chạy báo cáo nặng làm chậm mọi tenant. Giảm bằng: rate limit/quota theo tenant, queue riêng hoặc fair scheduling theo tenant, tách tenant lớn sang DB/cluster riêng
- [ ] **Hybrid** 🔴: đa số tenant chung (pool), tenant enterprise riêng (silo). Cần một lớp routing `tenant → DB/cluster`
- [ ] Xác định tenant: subdomain, header, claim trong JWT. Tenant phải lấy từ nguồn tin cậy (token đã xác thực), không lấy từ tham số client gửi tuỳ ý

### 12-factor, configuration, feature flag

- [ ] **12-factor app** 🟢 — 12 nguyên tắc cho app chạy trên cloud:
  1. Codebase: một repo, nhiều deploy
  2. Dependencies: khai báo tường minh (composer.json, go.mod, pom.xml), không dựa vào thứ cài sẵn trên máy
  3. **Config qua biến môi trường**, tách khỏi code
  4. Backing services (DB, cache, queue) là tài nguyên gắn vào, đổi bằng config
  5. Build, release, run tách biệt
  6. **Process stateless**, share-nothing; state nằm ở backing service
  7. Port binding: app tự expose cổng
  8. Concurrency: scale bằng thêm process
  9. Disposability: khởi động nhanh, **graceful shutdown**
  10. Dev/prod parity: các môi trường giống nhau nhất có thể
  11. **Log ra stdout** như một luồng sự kiện; hạ tầng thu gom
  12. Admin process (migration, script) chạy như one-off process trong cùng môi trường
  - ⚠️ Session lưu trên file local, file upload lưu trên disk app server → vi phạm stateless, không scale ngang được
- [ ] **Configuration** 🟡
  - Config (khác nhau giữa môi trường) tách khỏi code; secret tách khỏi config thường (Vault, AWS Secrets Manager, K8s Secret) — xem [10-security.md](10-security.md)
  - Validate config khi khởi động: thiếu biến bắt buộc thì fail ngay, đừng chạy rồi lỗi lúc 3 giờ sáng
  - Config động (đổi không cần deploy) tiện nhưng là một đường thay đổi production; cần audit và rollback như code
- [ ] **Feature flag như công cụ kiến trúc** 🟡
  - Tách **deploy** (code lên production) khỏi **release** (người dùng thấy)
  - Các loại: release flag (ngắn hạn, trunk-based development), ops flag / kill switch (tắt tính năng nặng khi sự cố), experiment flag (A/B test), permission flag (tính năng theo gói)
  - Dùng trong migration: đọc từ hệ cũ và mới song song, so sánh, chuyển dần theo % (strangler fig)
  - ⚠️ Nợ flag: flag không bao giờ xoá, tổ hợp flag bùng nổ, code rẽ nhánh khắp nơi. Mỗi release flag cần owner và hạn xoá
  - ⚠️ Flag service chết thì sao: phải có giá trị mặc định an toàn và cache local

### Tài liệu kiến trúc

- [ ] **ADR (Architecture Decision Record)** 🟡
  - Một file ngắn cho mỗi quyết định quan trọng, lưu trong repo, đánh số, không sửa nội dung cũ (bị thay thế thì tạo ADR mới và đổi status)
  - Mẫu phổ biến (Michael Nygard):

  ```markdown
  # ADR-012: Dùng PostgreSQL thay MySQL cho service Billing
  Status: Accepted (2026-03-02)
  Context: cần JSONB, partial index, RLS cho multi-tenant...
  Decision: dùng PostgreSQL 16 trên RDS.
  Consequences: team cần học vận hành Postgres; migrate 3 bảng...
  Alternatives considered: MySQL 8 (thiếu RLS), MongoDB (mất transaction đa bảng...)
  ```
  - Giá trị lớn nhất: một năm sau, người mới biết **vì sao**, không chỉ biết **cái gì**
- [ ] **C4 model** 🟡 — bốn mức zoom
  1. System context: hệ thống của mình, người dùng, hệ thống bên ngoài
  2. Container: các đơn vị chạy được (web app, API, DB, queue), công nghệ, giao thức
  3. Component: các thành phần chính bên trong một container
  4. Code: class diagram, thường không cần vẽ tay
  - Hầu hết tài liệu chỉ cần mức 1 và 2. Giữ sơ đồ dạng code (Structurizr, PlantUML, Mermaid) để review được
- [ ] **RFC / design doc** 🔴
  - Viết **trước** khi làm việc lớn, để người khác phản biện khi thay đổi còn rẻ
  - Cấu trúc gợi ý: bối cảnh và vấn đề, mục tiêu và **non-goals**, đề xuất, các phương án đã cân nhắc và vì sao loại, rủi ro, kế hoạch rollout/rollback, cách đo thành công, câu hỏi mở
  - Khi nào cần: thay đổi khó đảo ngược, ảnh hưởng nhiều team, tốn nhiều tuần. Việc nhỏ viết RFC là lãng phí

### Tổ chức và ra quyết định

- [ ] **Conway's law** 🔴: hệ thống phản chiếu cấu trúc giao tiếp của tổ chức thiết kế nó. Ba team làm compiler thì ra compiler ba pass
  - Inverse Conway maneuver: muốn kiến trúc nào thì tổ chức team theo đúng hình đó
  - ⚠️ Tách microservices mà một team sở hữu 15 service, hoặc 3 team cùng sửa một service → không khớp Conway, sẽ có ma sát
- [ ] **Team Topologies** 🔴 (đại ý)
  - Bốn loại team: stream-aligned (theo luồng giá trị/sản phẩm), platform (cung cấp nền tảng tự phục vụ), enabling (giúp team khác học kỹ năng mới), complicated-subsystem (phần cần chuyên môn sâu)
  - Ba kiểu tương tác: collaboration, X-as-a-service, facilitating
  - Ý chính: giảm cognitive load của team; ranh giới service nên khớp ranh giới team
- [ ] **Reversible vs irreversible** 🔴
  - Two-way door (đảo ngược được, rẻ): quyết nhanh, để team tự quyết, thử rồi sửa. Ví dụ: thư viện HTTP client, cấu trúc thư mục
  - One-way door (khó đảo ngược): chậm lại, viết RFC/ADR, thử nghiệm nhỏ trước. Ví dụ: chọn DB chính, format ID công khai, API public, mô hình multi-tenant, tách microservices
  - Senior biến quyết định one-way thành two-way khi có thể: đặt interface/abstraction ở chỗ nhiều khả năng đổi, feature flag, migration theo từng bước
- [ ] **Cách đánh giá một quyết định kiến trúc** 🔴
  - Quality attributes cần ưu tiên: performance, scalability, availability, security, maintainability, cost, time-to-market. Không tối ưu được hết; nói rõ đang ưu tiên cái nào
  - Các câu hỏi: Vấn đề thật là gì, có số liệu không? Phương án đơn giản nhất giải được chưa? Chi phí vận hành lâu dài? Team có kỹ năng không? Sai thì đảo ngược tốn bao nhiêu? Đo thế nào để biết đúng?
  - Fitness function: kiểm tra tự động một thuộc tính kiến trúc (test cấm import chéo module, ngưỡng p99 trong load test, kích thước bundle) để kiến trúc không mục dần
  - ⚠️ Resume-driven development: chọn công nghệ vì muốn học, không vì bài toán cần

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Monolith hay microservices? | "Microservices vì scale tốt, hiện đại" | Hỏi số team, tần suất deploy, phần nào cần scale khác. Mặc định modular monolith; nêu điều kiện tiên quyết và lý do cụ thể để tách; nhắc distributed monolith |
| Logic nghiệp vụ đặt ở đâu? | "Trong service" | Quy tắc thuần ở domain (entity/value object), điều phối use case ở application service, controller mỏng. Với CRUD thì không cần nhiều tầng; mức đầu tư theo độ phức tạp |
| Có nên dùng Clean Architecture không? | "Có, vì nó clean" | Chỉ cho phần core có nghiệp vụ phức tạp và sống lâu. Nêu cái giá (mapping, interface), và lý do thật là test và cô lập nghiệp vụ, không phải để thay framework |
| Cần dữ liệu của service khác để hiển thị danh sách | "JOIN sang DB bên đó" | API composition nếu nhỏ; read model qua event nếu cần sort/filter; chấp nhận eventual consistency và nói độ trễ đồng bộ chấp nhận được là bao nhiêu |
| Thiết kế multi-tenant | "Thêm cột `tenant_id`" | So ba mô hình theo isolation, chi phí, số tenant, compliance. Nêu cách cưỡng chế lọc tenant (RLS, global scope, test), cache key, noisy neighbor, hybrid cho tenant lớn |
| Một quyết định kiến trúc được đưa ra thế nào? | "Team lead quyết" | Phân loại reversible/irreversible; việc khó đảo ngược thì RFC, ADR, thử nghiệm nhỏ, định nghĩa cách đo thành công |

## Tình huống

1. **Monolith Laravel 5 năm tuổi, 8 dev, deploy mỗi tuần hay vỡ. CTO muốn chuyển microservices.**
   - Gợi ý: hỏi vấn đề thật (deploy vỡ vì thiếu test? vì coupling? vì một phần tải nặng?)
   - Thường nên modular hoá trước: xác định bounded context, cưỡng chế ranh giới (Deptrac), cắt truy cập bảng chéo
   - Cải thiện CI/CD, test, feature flag trước; 8 dev khó vận hành nhiều service
   - Nếu tách: chọn một phần có lý do rõ (ví dụ notification, xử lý file), dùng strangler fig

2. **Ba service luôn phải deploy cùng lúc, một cái chết là cả hệ thống lỗi.**
   - Gợi ý: đây là distributed monolith. Vẽ lại dependency và luồng gọi
   - Xem có dùng chung DB hay shared library chứa domain model không
   - Chuyển những lời gọi không cần kết quả ngay sang event; thêm timeout, circuit breaker, fallback
   - Cân nhắc gộp lại nếu ranh giới vốn sai

3. **Trang "Đơn hàng của tôi" cần tên sản phẩm (Catalog), trạng thái giao hàng (Shipping), trạng thái thanh toán (Payment). Mỗi service một DB.**
   - Gợi ý: API composition cho trang chi tiết một đơn; danh sách có filter/sort thì dựng read model trong service Order hoặc một query service nghe event
   - Tên sản phẩm lúc đặt nên được snapshot vào đơn (yêu cầu nghiệp vụ)
   - Nói rõ độ trễ đồng bộ và cách hiển thị khi dữ liệu chưa về

4. **SaaS B2B dùng `tenant_id`, một khách hàng enterprise yêu cầu dữ liệu tách riêng và đặt ở EU.**
   - Gợi ý: mô hình hybrid, lớp routing tenant → DB
   - Quy trình migrate dữ liệu một tenant sang DB riêng không downtime (dual write hoặc CDC, cutover)
   - Kiểm tra cache, object storage, log, backup cũng phải tuân thủ data residency

5. **Đội muốn dùng hexagonal cho toàn bộ app admin CRUD 40 màn hình.**
   - Gợi ý: phản biện bằng chi phí/lợi ích; admin CRUD dùng MVC của framework là đủ
   - Đề xuất áp kiến trúc kỹ hơn chỉ cho module có nghiệp vụ phức tạp (tính giá, đối soát)
   - Ghi ADR để thống nhất

6. **Thay hệ thống thanh toán cũ (viết bằng framework đã hết hỗ trợ) mà không dừng kinh doanh.**
   - Gợi ý: strangler fig qua gateway; ACL để hệ mới không nhiễm model cũ
   - Shadow traffic hoặc chạy song song và đối soát kết quả trước khi chuyển
   - Chuyển theo % hoặc theo nhóm merchant bằng feature flag; kế hoạch rollback từng bước

## ❓ Câu hỏi hay gặp

🟢
- Controller, service, repository mỗi tầng làm gì?
- 12-factor app là gì? Vì sao app phải stateless?
- Logic nghiệp vụ nên đặt trong controller, model hay service? Vì sao?

🟡
- Hexagonal architecture khác layered architecture ở điểm nào?
- Entity khác value object thế nào? Cho ví dụ value object.
- Aggregate là gì? Vì sao một transaction chỉ nên sửa một aggregate?
- Modular monolith là gì? Làm sao ngăn module truy cập bảng của nhau?
- Lợi ích và cái giá của microservices?
- API gateway và BFF khác nhau thế nào?
- So sánh ba mô hình multi-tenancy.

🔴
- Khi nào bạn tách một module ra thành microservice? Bạn tách thế nào?
- Distributed monolith là gì, nhận biết và sửa thế nào?
- Làm sao lấy dữ liệu "JOIN" từ ba service có DB riêng?
- Bounded context là gì? Cách xác định ranh giới?
- Anticorruption layer dùng khi nào?
- Conway's law ảnh hưởng tới kiến trúc thế nào?
- Bạn quyết định một thay đổi kiến trúc lớn như thế nào? Viết tài liệu gì?

## Bài tập tự làm

1. Lấy một dự án bạn đang làm, vẽ sơ đồ C4 mức 1 và mức 2. Liệt kê các bounded context bạn thấy và chỗ nào đang vi phạm ranh giới (JOIN chéo, model dùng chung).
2. Viết một ADR thật cho một quyết định bạn từng đưa ra (hoặc từng thấy), có đủ context, decision, consequences và alternatives.
3. Mô hình hoá aggregate `Order` cho một shop: xác định invariant, entity, value object, các domain event. Viết code (PHP, Java hoặc Go) cho `Money` là value object.
4. Viết một RFC 1–2 trang: chuyển một monolith có module Order, Payment, Notification sang modular monolith, nêu bước đi, rủi ro và cách rollback.
5. Thiết kế lớp cưỡng chế `tenant_id` cho một app row-per-tenant: ở tầng ORM, ở tầng DB, ở cache key; liệt kê test cần có.

> Nộp bài vào đây để được review.
