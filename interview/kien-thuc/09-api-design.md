# 09. Thiết kế API · Kiến thức

> [← Plan ôn tập](../09-api-design.md) · [Mục lục kiến thức](README.md)
> Bài đọc tổng hợp từ tài liệu gốc ở mục "Đọc" của từng module. Đọc sau khi đã xem plan; tick các
> tiêu chí "Nắm chắc khi" ở file plan. Mọi nội dung đã qua một lượt review độc lập đối chiếu nguồn gốc.

## Mục lục

- Chặng 1: Nền
  - [1.1 Resource và method semantics](#11-resource-và-method-semantics)
  - [1.2 Status code](#12-status-code)
  - [1.3 Format lỗi thống nhất](#13-format-lỗi-thống-nhất)
  - [1.4 Filtering, sorting, pagination](#14-filtering-sorting-pagination)
- Chặng 2: Làm chủ
  - [2.1 Idempotency key và retry an toàn](#21-idempotency-key-và-retry-an-toàn)
  - [2.2 Ghi đồng thời, bulk, long-running operation](#22-ghi-đồng-thời-bulk-long-running-operation)
  - [2.3 Rate limiting, auth và CORS](#23-rate-limiting-auth-và-cors)
  - [2.4 Webhook](#24-webhook)
  - [2.5 Gọi API bên thứ ba](#25-gọi-api-bên-thứ-ba)
  - [2.6 Tầng Laravel cho API](#26-tầng-laravel-cho-api)
  - [2.7 Serialization](#27-serialization)
- Chặng 3: Senior
  - [3.1 Tiến hoá API: versioning, deprecation, backward compatibility](#31-tiến-hoá-api-versioning-deprecation-backward-compatibility)
  - [3.2 GraphQL](#32-graphql)
  - [3.3 gRPC và Protobuf](#33-grpc-và-protobuf)
  - [3.4 Contract, tài liệu và hạ tầng API](#34-contract-tài-liệu-và-hạ-tầng-api)

---

## Chặng 1: Nền

### 1.1 Resource và method semantics

Module này trả lời: một endpoint REST gồm hai nửa, URL (tên của "thứ" được thao tác) và method
(muốn làm gì với nó); vì sao chọn method không phải chuyện thẩm mỹ mà quyết định việc proxy, trình
duyệt, crawler và thư viện HTTP có tự retry hay cache request đó hay không.

#### Resource và cách đặt URL

*Resource* là một khái niệm bạn muốn cho client thao tác: một đơn hàng, một user, "danh sách đơn
của user 123", thậm chí "yêu cầu huỷ của đơn 456". URL là **tên** (identifier) của resource đó.
RFC 9110 nhấn mạnh: đừng nghĩ URL là đường dẫn file trên server; phía sau nó có thể là một bảng DB,
một view ghép nhiều bảng, hay một gateway sang hệ thống khác. Chỉ server cần biết URL được ánh xạ
vào đâu. Chính vì vậy URL nên mô tả *cái gì*, còn *làm gì* để cho method nói.

Quy ước thực dụng mà hầu hết guideline (Zalando, Google AIP) thống nhất:

| Quy tắc | Đúng | Sai | Lý do |
|---|---|---|---|
| Danh từ, không động từ | `GET /orders/5` | `GET /getOrder?id=5` | Động từ đã nằm ở method |
| Collection dùng số nhiều | `/orders`, `/orders/5` | `/order/5` | `/orders` là tập hợp, `/orders/5` là một phần tử trong tập đó |
| Lồng tối đa 1–2 cấp | `/users/123/orders` | `/users/123/orders/456/items/7/notes` | URL dài, client phải biết cả chuỗi cha mới gọi được |
| Id đã duy nhất toàn cục thì bỏ cha | `/orders/456` | `/users/123/orders/456` | Cha thừa, lại phải kiểm tra thêm "đơn 456 có thuộc user 123 không" |
| Một quy ước tên field | `created_at` ở mọi nơi | `created_at` chỗ này, `createdAt` chỗ kia | Client không phải đoán |

Về tên field JSON: `snake_case` hay `camelCase` đều được, quan trọng là nhất quán toàn API.
Laravel mặc định serialize model theo tên cột DB, nên nếu cột là `created_at` thì JSON ra
`created_at`. Muốn `camelCase` thì phải tự đổi ở tầng API Resource (module 2.6), và phải đổi ở mọi
chỗ, kể cả response lỗi.

Trong Laravel, `Route::apiResource('orders', OrderController::class)` sinh sẵn năm route theo đúng
quy ước trên:

```
GET       /orders           index    danh sách
POST      /orders           store    tạo mới
GET       /orders/{order}   show     xem một đơn
PUT|PATCH /orders/{order}   update   sửa
DELETE    /orders/{order}   destroy  xoá
```

⚠️ Để ý `update` nhận cả `PUT` lẫn `PATCH` vào cùng một action. Nếu hai method này có ngữ nghĩa
khác nhau trong API của bạn (xem nhóm PUT và PATCH), action phải tự phân biệt, hoặc tách route.

#### Hành động không khớp CRUD

CRUD (Create, Read, Update, Delete) phủ phần lớn nhu cầu, nhưng nghiệp vụ thật có những động từ
như huỷ, hoàn tiền, duyệt, gửi lại email. Nhét chúng vào `PATCH /orders/5 {"status": "cancelled"}`
thường sai: huỷ đơn không chỉ là đổi một field mà kéo theo hoàn kho, hoàn tiền, gửi thông báo, và
có luật riêng (đơn đã giao thì không huỷ được). Có hai cách thiết kế chuẩn:

1. *Sub-resource*: biến hành động thành một danh từ, rồi "tạo" danh từ đó.
   - `POST /orders/5/cancellation`: tạo yêu cầu huỷ cho đơn 5.
   - `POST /orders/5/refunds`: tạo một lần hoàn tiền. Dùng số nhiều vì một đơn có thể hoàn nhiều
     lần (hoàn một phần), và mỗi lần hoàn là một resource có id riêng để tra lại
     (`GET /orders/5/refunds/r_1`).
   - Ưu điểm: vẫn là REST thuần, router nào cũng hỗ trợ, và resource sinh ra (refund) có lịch sử.
2. *Custom method* theo Google AIP-136: gắn động từ sau dấu hai chấm, ví dụ
   `POST /v1/orders/5:cancel`. Quy tắc chính của AIP-136:
   - Chỉ dùng khi không diễn đạt gọn được bằng method chuẩn. AIP nói rõ đừng uốn method chuẩn cho
     "tạm chạy được", nhưng cũng đừng lạm dụng custom method.
   - HTTP method chỉ được là `GET` (đọc dữ liệu) hoặc `POST` (có side effect). Bản cập nhật
     2026-06 cho phép `POST` cả với method chỉ đọc khi request quá lớn, không nhét được vào URL.
   - Động từ viết `camelCase` nếu nhiều từ, không chứa giới từ ("for", "with"), không dùng lại
     các động từ chuẩn (Get, List, Create, Update, Delete).
   - Có thể gắn vào một resource (`/orders/5:cancel`), một collection (`/books:sort`) hoặc không
     gắn gì cho method phi trạng thái (`:translateText`).

Chọn cách nào? Nếu hành động sinh ra một thứ đáng lưu và tra lại (refund, shipment, export), dùng
sub-resource. Nếu nó chỉ là một chuyển trạng thái thuần (archive, cancel) và team đã theo AIP, custom
method đọc rõ hơn. Điều quan trọng là nhất quán trong một API.

Ví dụ bộ endpoint cho `orders` có đủ huỷ, hoàn tiền, đổi địa chỉ:

```
POST   /orders                          tạo đơn
GET    /orders/{id}                     xem đơn
POST   /orders/{id}/cancellation        huỷ đơn (hoặc POST /orders/{id}:cancel)
POST   /orders/{id}/refunds             tạo một lần hoàn tiền
GET    /orders/{id}/refunds             liệt kê các lần hoàn
PUT    /orders/{id}/shipping-address    thay toàn bộ địa chỉ giao hàng (sub-resource số ít)
```

Đổi địa chỉ là "sửa một phần của đơn", nên cũng có thể là `PATCH /orders/{id}` với body chứa
`shipping_address`. Tách thành sub-resource hợp lý khi địa chỉ có luật riêng (chỉ đổi được trước khi
đóng gói) và cần phân quyền riêng.

#### Ba tính chất của method

RFC 9110 mục 9.2 định nghĩa ba tính chất. Hiểu chính xác định nghĩa giúp trả lời mọi câu hỏi vặn.

*Safe*: ngữ nghĩa của method về cơ bản là chỉ đọc, tức client **không yêu cầu và không mong đợi**
server thay đổi trạng thái. Điểm tinh tế: RFC không cấm server làm thêm việc phụ khi nhận GET (ghi
access log, tăng bộ đếm lượt xem). Cái RFC quan tâm là client không yêu cầu những việc đó nên không
phải chịu trách nhiệm. GET, HEAD, OPTIONS, TRACE là safe.

Vì sao phân biệt safe? Để các tiến trình tự động (crawler, prefetch của trình duyệt, công cụ kiểm tra
link) gọi được mà không gây hại. RFC còn nêu đích danh kiểu URL `page?do=delete`: nếu hành động là
không an toàn, chủ resource **bắt buộc** (MUST) chặn nó khi được gọi bằng method safe.

⚠️ Hệ quả: GET không được có side effect về nghiệp vụ. Một link `GET /orders/delete?id=5` trong
trang admin sẽ bị crawler, extension trình duyệt hay prefetch bấm hộ.

*Idempotent*: nhiều request **giống hệt nhau** có **tác động dự định lên server** giống như một
request. PUT, DELETE và mọi method safe là idempotent. Hai chữ cần gạch chân:

- "Tác động lên server", không phải response. `DELETE /orders/5` lần đầu trả `204`, lần hai trả
  `404`, nhưng trạng thái cuối vẫn là "đơn 5 không còn", nên DELETE vẫn idempotent. RFC viết rõ:
  lặp lại request cho cùng tác động dự định, "dù response có thể khác".
- "Dự định" (intended): server vẫn được ghi log từng lần, lưu lịch sử phiên bản. Đó không phải thứ
  client yêu cầu.

Vì sao idempotent quan trọng: khi kết nối đứt **trước khi** client đọc được response, client không
biết request đã được xử lý hay chưa. Với method idempotent, cứ gửi lại, vì gửi thêm lần nữa cũng
không đổi kết quả. RFC quy định:

- Client không nên (SHOULD NOT) tự retry method không idempotent, trừ khi có cách biết chắc request
  thật ra idempotent hoặc biết chắc request gốc chưa được áp dụng. Idempotency key (module 2.1)
  chính là "cách biết chắc" đó.
- Proxy **không được** (MUST NOT) tự retry request không idempotent.
- Client không nên retry một lần retry tự động đã thất bại.

*Cacheable*: response được lưu và dùng lại cho request sau. RFC 9110 định nghĩa ngữ nghĩa cache cho
GET, HEAD và POST, nhưng tuyệt đại đa số cache chỉ hỗ trợ GET và HEAD. POST chỉ cache được khi có
thông tin freshness tường minh và header `Content-Location` trùng URL. Response của PUT, DELETE,
OPTIONS không cacheable; một PUT hay DELETE thành công đi qua cache còn làm các bản đã lưu của URL
đó bị vô hiệu.

| Method | Safe | Idempotent | Cacheable | Dùng cho |
|---|---|---|---|---|
| GET | có | có | có | đọc |
| HEAD | có | có | có | như GET nhưng không có body; kiểm tra tồn tại, lấy header |
| OPTIONS | có | có | không | hỏi khả năng, CORS preflight (module 2.3) |
| POST | không | không | hiếm (điều kiện ở trên) | tạo mới khi server chọn id, hành động |
| PUT | không | có | không | thay toàn bộ, hoặc tạo tại URL client chọn |
| PATCH | không | không bắt buộc | hiếm (điều kiện như POST) | sửa một phần (RFC 5789, không nằm trong RFC 9110) |
| DELETE | không | có | không | xoá |

Vài chi tiết từ RFC hay dùng khi thiết kế:

- Body trong GET, HEAD, DELETE "không có ngữ nghĩa được định nghĩa". Một số server, proxy từ chối
  hoặc bỏ body đó. ⚠️ Đừng thiết kế `GET /search` với body JSON; muốn tìm kiếm phức tạp thì dùng
  `POST /orders:search` (đúng tinh thần AIP-136 ở trên).
- Dữ liệu nhạy cảm không nên nằm trong query string của GET, vì URL bị ghi vào log, history.
- POST tạo resource thành công nên trả `201` kèm `Location` (module 1.2).
- DELETE thành công trả `202` (sẽ xoá sau), `204` (đã xoá, không có gì thêm) hoặc `200` (đã xoá, có
  body mô tả).

#### PUT và PATCH

*PUT* yêu cầu trạng thái của resource **được tạo mới hoặc thay thế** bằng đúng nội dung gửi lên.
Gửi cùng body mười lần thì trạng thái cuối vẫn là body đó, nên PUT idempotent. Hệ quả thực tế:

- Field nào không có trong body PUT, về lý thuyết là bị xoá hoặc về mặc định. ⚠️ Nhiều API gọi là
  PUT nhưng chỉ cập nhật field có mặt; đó thực chất là PATCH, và client nào tin ngữ nghĩa PUT sẽ bất
  ngờ.
- PUT vào URL chưa tồn tại mà tạo được thì server **phải** trả `201`; thay thế thành công thì `200`
  hoặc `204`.
- PUT chỉ đúng khi **client biết URL đích**. Nếu server mới là bên chọn id, RFC khuyên dùng POST.
  Ví dụ hợp PUT: `PUT /users/123/avatar`, `PUT /settings/notifications`, hoặc client tự sinh UUID:
  `PUT /orders/0b6f...`.

*PATCH* (RFC 5789) gửi một **mô tả thay đổi**, không phải trạng thái mới. RFC 5789 định nghĩa PATCH
không safe và không idempotent, nhưng thừa nhận một request PATCH cụ thể có thể được thiết kế để
idempotent; điều đó phụ thuộc nội dung patch:

- "Đặt `name` thành `An`": gọi lại vẫn ra `name = An`, idempotent.
- "Tăng `stock` thêm 1" hoặc "thêm phần tử vào cuối mảng": gọi hai lần là tác động hai lần.

⚠️ Vì PATCH không được coi là idempotent, thư viện HTTP và proxy sẽ không tự retry nó. Muốn retry
an toàn thì dùng conditional request (`If-Match` với ETag, module 2.2) hoặc idempotency key.

Hai format chuẩn cho body PATCH dạng JSON:

**JSON Merge Patch** (RFC 7396, `Content-Type: application/merge-patch+json`): body là một object
"trông giống" resource, chỉ chứa phần cần đổi. Thuật toán áp dụng, diễn giải lại từ RFC:

1. Nếu patch không phải object (là mảng, chuỗi, số...), toàn bộ target bị thay bằng patch.
2. Nếu patch là object: với từng cặp key/value trong patch,
   - value là `null`: xoá key đó khỏi target (nếu có);
   - ngược lại: gán target[key] bằng kết quả áp dụng đệ quy value lên target[key].
3. Key không có trong patch giữ nguyên.

```jsonc
// Target
{"title": "Goodbye!", "author": {"givenName": "John", "familyName": "Doe"},
 "tags": ["example", "sample"], "content": "giữ nguyên"}

// Patch: đổi title, thêm phone, xoá author.familyName, bỏ "sample" khỏi tags
{"title": "Hello!", "phone": "+84-123", "author": {"familyName": null}, "tags": ["example"]}

// Kết quả
{"title": "Hello!", "author": {"givenName": "John"}, "tags": ["example"],
 "content": "giữ nguyên", "phone": "+84-123"}
```

Hai giới hạn của Merge Patch, cả hai đều nằm ngay trong thuật toán:

- ⚠️ Không sửa được một phần tử trong mảng. Muốn bỏ `"sample"` phải gửi lại cả mảng `tags`. Với mảng
  lớn hoặc hai client cùng sửa mảng, gửi cả mảng dễ ghi đè thay đổi của người kia.
- ⚠️ Không đặt được giá trị `null`, vì `null` đã mang nghĩa "xoá". RFC nói format này hợp với tài liệu
  chủ yếu là object và không dùng `null` tường minh.

**JSON Patch** (RFC 6902, `Content-Type: application/json-patch+json`): body là một **mảng các phép**,
chạy tuần tự, kết quả phép trước là đầu vào phép sau. Mỗi phép có `op` và `path`; `path` là một
*JSON Pointer* (RFC 6901), ví dụ `/items/2/qty` (phần tử index 2 của mảng `items`, field `qty`).

| `op` | Làm gì | Ghi chú |
|---|---|---|
| `add` | Thêm vào object hoặc chèn vào mảng tại index | Index `-` nghĩa là nối vào cuối mảng; key đã có thì bị thay |
| `remove` | Xoá giá trị tại `path` | `path` phải tồn tại |
| `replace` | Thay giá trị | `path` phải tồn tại; tương đương remove rồi add |
| `move` | Chuyển giá trị từ `from` sang `path` | Không được chuyển một node vào chính con của nó |
| `copy` | Chép giá trị từ `from` sang `path` | |
| `test` | Kiểm tra giá trị tại `path` bằng `value` | Sai thì cả patch thất bại |

Điểm mạnh nhất của JSON Patch là tính **nguyên tử**: nếu một phép thất bại, cả patch không được coi
là thành công, và vì PATCH theo RFC 5789 là atomic nên không thay đổi nào được áp dụng. Phép `test`
nhờ đó thành một khoá lạc quan (optimistic lock) mini: "chỉ đổi giá nếu giá hiện tại vẫn là 100".

```jsonc
// Merge Patch: đổi name, xoá phone
{"name": "An", "phone": null}

// JSON Patch: cùng thay đổi
[{"op": "replace", "path": "/name", "value": "An"},
 {"op": "remove",  "path": "/phone"}]

// JSON Patch làm được mà Merge Patch không làm được:
// sửa qty của item thứ 3, chỉ khi giá của nó vẫn là 100, rồi thêm tag vào cuối mảng
[{"op": "test",    "path": "/items/2/price", "value": 100},
 {"op": "replace", "path": "/items/2/qty",   "value": 5},
 {"op": "add",     "path": "/tags/-",        "value": "vip"}]
```

⚠️ Trong JSON Pointer, ký tự `/` và `~` trong tên key phải escape: `~1` cho `/`, `~0` cho `~`. Key
`"a/b"` được trỏ bằng `/a~1b`.

| | JSON Merge Patch | JSON Patch |
|---|---|---|
| Body | Object giống resource | Mảng phép |
| Xoá field | Gán `null` | `remove` |
| Đặt field thành `null` | Không được | `replace` với `"value": null` |
| Sửa một phần tử mảng | Không, gửi lại cả mảng | Được, qua index |
| Kiểm tra điều kiện | Không | `test` |
| Độ dễ dùng | Rất dễ, frontend gửi như form | Khó hơn, cần thư viện |

Thực tế đa số API công khai dùng body JSON thường theo kiểu merge (field nào có thì đổi) mà không
khai `application/merge-patch+json`. Chấp nhận được, miễn là tài liệu nói rõ `null` nghĩa là "xoá"
hay "đặt null".

#### Đào sâu (🟡): HATEOAS và Richardson Maturity Model

Leonard Richardson đề xuất, Martin Fowler viết lại (2010), một mô hình bốn mức để mô tả một API
"REST" tới đâu. Ví dụ xuyên suốt của Fowler là đặt lịch khám bệnh:

| Mức | Thêm gì | Ví dụ |
|---|---|---|
| 0: HTTP chỉ là đường ống | Một endpoint, mọi thứ là POST, lỗi nằm trong body | `POST /appointmentService` với body "tìm slot trống" |
| 1: Resource | Mỗi thứ có URL riêng | `POST /slots/1234` để đặt slot đó |
| 2: HTTP verb | Dùng đúng method và status code | `GET /doctors/mjones/slots?date=...`; đặt thành công trả `201` + `Location`; bị người khác đặt trước trả `409` |
| 3: Hypermedia | Response kèm link tới các hành động tiếp theo | Lịch hẹn vừa tạo kèm link "huỷ", "thêm xét nghiệm", "đổi thông tin liên hệ" |

*HATEOAS* (Hypermedia As The Engine Of Application State) là mức 3: client đi theo link server đưa,
không tự ghép URL. Lợi ích Fowler nêu: server đổi cấu trúc URL mà không làm vỡ client, và API tự mô
tả được các bước tiếp theo.

Fowler tóm ý nghĩa từng mức: mức 1 là chia để trị (tách một endpoint khổng lồ thành nhiều resource),
mức 2 là chuẩn hoá (dùng chung một bộ verb, status thay vì tự chế), mức 3 là khả năng tự khám phá.
Ông cũng lưu ý mô hình này không phải định nghĩa REST; theo Roy Fielding, chỉ mức 3 mới là REST.

Với phỏng vấn: biết khái niệm là đủ. Hầu hết API công khai dừng ở mức 2, vì client
thực tế vẫn viết cứng URL theo tài liệu, và thêm link vào mọi response tốn công mà ít được dùng.
Một dạng HATEOAS nhẹ vẫn rất phổ biến: link phân trang `next` (module 1.4).

**Tóm tắt nhanh**
- URL là tên của resource (danh từ, số nhiều, lồng ít); method nói hành động. Hành động ngoài CRUD
  dùng sub-resource (`POST /orders/5/refunds`) hoặc custom method `POST /orders/5:cancel`.
- Safe = client không yêu cầu thay đổi trạng thái (GET, HEAD, OPTIONS, TRACE). Idempotent = nhiều
  request giống nhau có cùng tác động dự định như một (thêm PUT, DELETE); nói về tác động, không
  nói về response.
- Idempotent quan trọng vì retry: proxy không được tự retry request không idempotent; client chỉ retry
  POST khi có cách biết chắc (idempotency key).
- PUT thay toàn bộ và cần client biết URL đích; PATCH mô tả thay đổi, idempotent hay không tuỳ nội dung.
- Merge Patch dễ nhưng không sửa được phần tử mảng và không đặt được `null`; JSON Patch là mảng phép,
  nguyên tử, có `test`.
- Richardson: 0 đường ống, 1 resource, 2 verb + status, 3 hypermedia; thực tế hầu hết API ở mức 2.

**Nguồn**: [RFC 9110 Section 9: Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9) ·
[RFC 7396: JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396) ·
[RFC 6902: JSON Patch](https://www.rfc-editor.org/rfc/rfc6902) ·
[Google AIP-136: Custom methods](https://google.aip.dev/136) ·
[Martin Fowler: Richardson Maturity Model](https://martinfowler.com/articles/richardsonMaturityModel.html)

---

### 1.2 Status code

Module này trả lời: status code nói gì với những ai (client, cache, load balancer, monitoring, code
retry), chọn code nào cho từng tình huống, phân biệt các cặp hay nhầm, và client nên tự retry
những code nào.

#### Cách đọc nhóm code

Status code là số nguyên ba chữ số, hợp lệ trong khoảng 100 tới 599. Theo RFC 9110, chỉ **chữ số
đầu** mang ý phân loại; hai chữ số sau không có quy luật gì.

| Nhóm | Nghĩa | Gửi lại y nguyên thì sao |
|---|---|---|
| `1xx` | Thông tin tạm, request đang được xử lý (ví dụ `100 Continue`) | Không áp dụng |
| `2xx` | Thành công | Không cần |
| `3xx` | Client cần làm thêm một bước (thường là đi tới URL khác) | Đi theo `Location` |
| `4xx` | Client có vẻ đã sai | Vẫn lỗi, trừ vài code tạm thời (`408`, `429`) |
| `5xx` | Server biết mình đã sai hoặc không làm nổi | Thử lại sau có thể thành công |

Quy tắc quan trọng nhất cho người viết client: client **bắt buộc** hiểu được nhóm, và gặp code lạ
thì coi như `x00` của nhóm đó. Nhận `471` (không ai định nghĩa) thì xử lý như `400`. Nhờ vậy server
thêm code mới mà client cũ không vỡ. Code nằm ngoài 100..599 thì client nên coi như `5xx`.

Thêm một chi tiết: *reason phrase* (chữ "OK", "Not Found" đi sau số) chỉ là gợi ý, có thể thay hoặc
bỏ, và HTTP/2 không còn gửi nó. ⚠️ Không bao giờ viết code dựa vào reason phrase.

#### 2xx: thành công

| Code | Khi nào | Chi tiết từ RFC |
|---|---|---|
| `200 OK` | Thành công, có body | Body của GET là resource; của POST là kết quả hành động; của PUT, DELETE là trạng thái hành động |
| `201 Created` | Đã tạo resource mới | Resource chính được chỉ bởi header `Location`; không có `Location` thì chính là URL của request (trường hợp PUT) |
| `202 Accepted` | Đã nhận, sẽ xử lý sau | Cố tình "không hứa": việc có thể vẫn bị từ chối lúc xử lý thật. Body nên mô tả trạng thái và chỉ chỗ theo dõi (module 2.2) |
| `204 No Content` | Thành công, không có body | Hay dùng cho DELETE, hoặc PUT không cần trả lại resource |

```http
POST /orders HTTP/1.1
Content-Type: application/json

{"items": [{"sku": "A1", "qty": 2}]}

HTTP/1.1 201 Created
Location: /orders/789
Content-Type: application/json

{"id": 789, "status": "pending", "items": [{"sku": "A1", "qty": 2}]}
```

Trong Laravel, trả một `JsonResource` bọc model vừa được tạo trong request này (model có
`wasRecentlyCreated = true`) thì response tự có status `201`. Header `Location` thì không tự có, phải
thêm bằng `->header('Location', ...)` nếu muốn.

⚠️ `202` không phải "thành công". Nó chỉ nói "đã nhận". Client nhận `202` phải có cách hỏi lại kết
quả, nếu không thì lỗi xảy ra sau đó sẽ không ai biết.

#### 3xx: chuyển hướng

| Code | Vĩnh viễn hay tạm | Đi theo có giữ method và body? |
|---|---|---|
| `301 Moved Permanently` | Vĩnh viễn | Không chắc: vì lý do lịch sử, client được phép đổi POST thành GET |
| `308 Permanent Redirect` | Vĩnh viễn | Có, client không được đổi method |
| `302 Found` | Tạm | Không chắc, như `301` |
| `307 Temporary Redirect` | Tạm | Có, client không được đổi method |
| `303 See Other` | Không phải "chuyển chỗ" | Chủ đích đổi sang GET: "kết quả của POST nằm ở URL kia, hãy GET nó" |

⚠️ Với API, redirect một `POST` bằng `301`/`302` có thể biến nó thành `GET` mất body, tức request
"thành công" nhưng không tạo gì. Muốn chuyển endpoint ghi thì dùng `308`/`307`. Tốt hơn nữa là
không dựa vào redirect cho API ghi, vì nhiều HTTP client không tự đi theo redirect của POST.

`304 Not Modified` không phải chuyển hướng thật. Nó trả lời *conditional GET*: client gửi kèm
"bản tôi đang có" (header `If-None-Match: "etag"` hoặc `If-Modified-Since`), server thấy chưa đổi thì
trả `304` không body, client dùng lại bản cũ. Tiết kiệm băng thông, không tiết kiệm được việc server
phải tính ETag (module 2.2).

#### 4xx: lỗi phía client

RFC 9110 yêu cầu với `4xx` và `5xx`, trừ response cho HEAD, server nên gửi kèm phần giải thích lỗi,
kể cả việc lỗi là tạm thời hay vĩnh viễn. Đó là lý do cần một format lỗi thống nhất (module 1.3).

| Code | Nghĩa chính xác | Header đi kèm | Ví dụ API |
|---|---|---|---|
| `400 Bad Request` | Server không (hoặc không muốn) xử lý vì thấy lỗi phía client: sai cú pháp, sai framing | | JSON không parse được, thiếu tham số bắt buộc ở query |
| `401 Unauthorized` | Thiếu thông tin xác thực hợp lệ (tên gọi sai lịch sử, nghĩa thật là "unauthenticated") | `WWW-Authenticate` là **bắt buộc** | Thiếu token, token hết hạn |
| `403 Forbidden` | Hiểu request nhưng từ chối; client không nên gửi lại với cùng credential | | User thường gọi API admin |
| `404 Not Found` | Không có resource, **hoặc server không muốn tiết lộ là có** | | Đơn không tồn tại |
| `405 Method Not Allowed` | URL có nhưng không hỗ trợ method này | `Allow` là **bắt buộc** | `DELETE /orders` |
| `406 Not Acceptable` | Không có dạng nào hợp với `Accept` của client | | Client đòi `Accept: application/xml` |
| `408 Request Timeout` | Server chờ nhận request quá lâu | | Client gửi body quá chậm |
| `409 Conflict` | Xung đột với trạng thái hiện tại; user có thể giải quyết rồi gửi lại | | Huỷ đơn đã giao; tạo user trùng email |
| `410 Gone` | Đã từng có, đã gỡ, và gần như chắc là vĩnh viễn | | Endpoint phiên bản cũ đã tắt (module 3.1) |
| `412 Precondition Failed` | Điều kiện trong header (`If-Match`...) sai | | ETag không khớp, người khác đã sửa trước (module 2.2) |
| `413 Content Too Large` | Body lớn quá mức server chấp nhận | `Retry-After` nếu chỉ tạm thời | Upload file quá giới hạn |
| `415 Unsupported Media Type` | Không hỗ trợ định dạng body gửi lên | `Accept` hoặc `Accept-Encoding` để gợi ý | Gửi `text/plain` vào endpoint JSON |
| `422 Unprocessable Content` | Hiểu định dạng, cú pháp đúng, nhưng không xử lý được nội dung | | Email sai định dạng, số lượng âm |
| `428 Precondition Required` | Server bắt buộc request phải có điều kiện | | PUT mà không gửi `If-Match` (RFC 6585) |
| `429 Too Many Requests` | Gửi quá nhiều trong một khoảng thời gian | `Retry-After` là tuỳ chọn (MAY) | Vượt rate limit (module 2.3) |

Vài điểm tinh tế lấy thẳng từ RFC:

- `401` khi request **đã có** credential nghĩa là credential đó bị từ chối. Client có thể thử lại với
  credential mới (ví dụ refresh token rồi gọi lại). `403` thì RFC nói client không nên tự gửi lại với
  cùng credential, vì kết quả sẽ y như cũ.
- Tên `413` trong RFC 9110 là "Content Too Large" (tên cũ "Payload Too Large"), tên `422` là
  "Unprocessable Content" (tên cũ "Unprocessable Entity", vốn từ WebDAV). RFC 9110 đã đưa `422` vào
  chuẩn HTTP chung.
- `409` theo RFC hay gặp nhất với PUT khi có versioning: thay đổi gửi lên xung đột với thay đổi
  của người khác trước đó. Body nên đủ thông tin để user biết xung đột ở đâu.
- `404` không nói tạm thời hay vĩnh viễn; biết chắc là vĩnh viễn thì `410` rõ nghĩa hơn.
- `428`, `429`, `431` (header quá lớn) đến từ RFC 6585, và response mang các code này **không được**
  lưu bởi cache.
- `Retry-After` nhận hai dạng: số giây (`Retry-After: 120`) hoặc một mốc thời gian HTTP-date.

Laravel map sẵn các exception phổ biến sang status code, nên bạn thường chỉ cần ném đúng exception:

| Exception | Status |
|---|---|
| `ValidationException` (FormRequest, `$request->validate()`) | `422` |
| `AuthenticationException` (middleware `auth`) | `401` |
| `AuthorizationException` (Policy, Gate, `$this->authorize()`) | `403` |
| `ModelNotFoundException` (route model binding, `findOrFail`) | `404` |
| `ThrottleRequestsException` (middleware `throttle`) | `429`, kèm `Retry-After` |
| Route có nhưng sai method | `405` |
| `abort(409, '...')` | Code bạn chọn |

#### 5xx: lỗi phía server

| Code | Nghĩa | Ai sinh ra, thường gặp khi |
|---|---|---|
| `500 Internal Server Error` | Server gặp tình huống không lường trước | Exception không ai bắt trong code PHP |
| `501 Not Implemented` | Server không hỗ trợ chức năng cần thiết, ví dụ method lạ với mọi resource | Hiếm gặp trong API |
| `502 Bad Gateway` | Server đứng giữa (proxy, gateway) nhận response **không hợp lệ** từ upstream | Nginx không nói chuyện được với PHP-FPM: FPM chết, socket sai, process bị kill giữa chừng |
| `503 Service Unavailable` | Tạm thời không phục vụ được do quá tải hoặc bảo trì | `php artisan down`, load balancer không còn backend khoẻ; có thể kèm `Retry-After` |
| `504 Gateway Timeout` | Server đứng giữa không nhận được response **kịp thời** từ upstream | Request PHP chạy lâu hơn timeout của Nginx hoặc load balancer |

*Upstream* là server nằm phía sau, được proxy gọi tới. Trong chuỗi
`client → load balancer → Nginx → PHP-FPM`, với Nginx thì PHP-FPM là upstream, với load balancer thì
Nginx là upstream. `502` và `504` do tầng đứng giữa sinh ra, không phải code PHP của bạn, nên log
Laravel thường không có dòng nào cho chúng. Phải xem log của Nginx hoặc load balancer.

⚠️ `504` không có nghĩa là request đã thất bại. Proxy chỉ hết kiên nhẫn; PHP-FPM phía sau có thể vẫn
đang chạy và **ghi xong** đơn hàng sau đó vài giây. Đây là nguồn gốc của nhiều bug trùng đơn.

#### Các cặp hay nhầm

| Cặp | Phân biệt | Câu hỏi để chọn |
|---|---|---|
| `400` / `422` | Không đọc được request so với đọc được nhưng nội dung không hợp lệ | "Tôi có parse được body không?" |
| `401` / `403` | Chưa biết bạn là ai (hoặc credential hỏng) so với biết rồi nhưng không cho | "Đăng nhập lại có giúp được không?" |
| `403` / `404` | Trả `404` thay `403` khi muốn giấu việc resource tồn tại (RFC cho phép) | "Người này có được biết resource tồn tại không?" |
| `409` / `422` | Xung đột với trạng thái hiện tại so với dữ liệu tự nó đã sai | "Gửi y nguyên lúc khác có thể hợp lệ không?" |
| `301` / `308` | Cùng vĩnh viễn, chỉ `308` chắc chắn giữ method và body | "Có redirect request ghi không?" |
| `502` / `504` | Upstream trả rác hoặc không kết nối được so với upstream quá chậm | "Upstream có trả lời không?" |
| `500` / `503` | Bug so với tạm thời không phục vụ (có chủ đích hoặc quá tải) | "Có nên báo động cho dev không?" |

Ví dụ `403`/`404`: user A gọi `GET /orders/5` của user B. Trả `403` là thừa nhận "đơn 5 có tồn tại",
đủ để kẻ tấn công dò id. Nhiều API (GitHub là ví dụ quen thuộc với repo private) trả `404` trong
trường hợp này.

⚠️ Không trả `200` kèm `{"success": false}`. Hậu quả dây chuyền:

1. Monitoring và load balancer đếm tỉ lệ lỗi theo status, nên dashboard báo mọi thứ xanh.
2. Cache có thể lưu lại response lỗi (response `200` của GET mặc định được cache heuristic).
3. Code retry và circuit breaker của client không nhận ra lỗi.
4. Mọi client phải parse body của mọi response mới biết thành công hay không.

Ngược lại cũng sai: đừng trả `500` cho lỗi do input của client. `500` nên có nghĩa là "có bug cần
dev xem", để alert trên `5xx` còn đáng tin.

#### Client nên retry code nào

Quyết định retry dựa trên hai câu hỏi: lỗi này có tạm thời không, và request có an toàn để gửi lại
không (module 1.1).

| Tình huống | Retry? | Lý do |
|---|---|---|
| Lỗi mạng trước khi gửi xong request (connect refused, DNS) | Có | Server chưa nhận được gì |
| Timeout hoặc đứt kết nối sau khi đã gửi request | Chỉ khi idempotent hoặc có idempotency key | Server có thể đã xử lý xong |
| `408` | Có | RFC cho phép client gửi lại |
| `429`, `503` | Có, sau khoảng chờ; tôn trọng `Retry-After` nếu có | Tạm thời, server đang bảo "chưa" |
| `502`, `504` | Có với request idempotent; POST chỉ khi có idempotency key | `504` đặc biệt: upstream có thể đã xử lý xong |
| `500` | Chỉ khi idempotent | Với `POST /payments`, server có thể đã trừ tiền rồi mới lỗi ở bước sau |
| `400`, `401`, `403`, `404`, `409`, `422` | Không retry mù | Gửi lại y nguyên vẫn sai. `401` thì làm mới token rồi gọi lại là một luồng khác, không phải retry mù |

Cách retry đúng (chi tiết ở module 2.1 và 2.5):

1. Giới hạn số lần (ví dụ 3), không retry vô hạn.
2. *Exponential backoff*: chờ tăng dần sau mỗi lần (1s, 2s, 4s...).
3. *Jitter*: cộng một khoảng ngẫu nhiên vào thời gian chờ, để hàng nghìn client không cùng retry
   đúng một thời điểm và đánh sập server vừa hồi phục.
4. Có `Retry-After` thì dùng nó thay cho thời gian tự tính.

⚠️ Retry nhiều tầng nhân nhau: client retry 3 lần, gateway retry 3 lần, service retry 3 lần là tới
27 request cho một thao tác. Chỉ nên retry ở một tầng.

**Tóm tắt nhanh**
- Chữ số đầu là nhóm; client gặp code lạ thì coi như `x00` của nhóm. Không dựa vào reason phrase.
- `201` kèm `Location`; `202` chỉ là "đã nhận"; `204` không body. Redirect request ghi thì dùng
  `307`/`308`, vì `301`/`302` cho phép đổi POST thành GET.
- `401` bắt buộc có `WWW-Authenticate`, `405` bắt buộc có `Allow`; `429` có thể kèm `Retry-After`.
- Các cặp: `400`/`422` (không đọc được / đọc được nhưng sai), `401`/`403` (chưa biết ai / biết mà không
  cho), `404` thay `403` để giấu, `502`/`504` (upstream trả rác / quá chậm).
- Không `200` kèm `success: false`: monitoring, cache, retry đều dựa vào status.
- Retry `408`, `429`, `503` (và `502`, `504` nếu idempotent), có backoff và jitter; `500` và timeout
  của POST chỉ retry khi idempotent hoặc có idempotency key.

**Nguồn**: [RFC 9110 Section 15: Status Codes](https://www.rfc-editor.org/rfc/rfc9110#section-15) ·
[RFC 6585](https://www.rfc-editor.org/rfc/rfc6585) ·
[MDN: HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status)

---

### 1.3 Format lỗi thống nhất

Module này trả lời: status code chỉ nói "loại lỗi chung" (`403`, `422`); client cần thêm thông tin
máy đọc được để biết **chính xác** chuyện gì xảy ra và phản ứng thế nào. Chuẩn cho phần thông tin đó
là RFC 9457 Problem Details; module này đi từ chuẩn tới cách làm thật trong Laravel.

#### Chuẩn RFC 9457 Problem Details

RFC 9457 (07/2023) thay cho RFC 7807 (2016). Nội dung gần như giữ nguyên; những thay đổi chính là
thêm một registry chung cho các problem type, làm rõ cách xử lý khi có nhiều lỗi cùng lúc, và hướng
dẫn dùng type URI không truy cập được.

Ý tưởng: status code dành cho phần mềm HTTP chung (thư viện, cache, proxy), còn body mang chi tiết
riêng của API. Ví dụ trong RFC: tài khoản không đủ tiền mua hàng. Status `403` cho mọi phần mềm biết
"bị từ chối"; body nói lý do cụ thể và số dư hiện tại để client có thể mời user nạp thêm.

```http
HTTP/1.1 403 Forbidden
Content-Type: application/problem+json
Content-Language: vi

{
  "type": "https://api.example.com/problems/out-of-credit",
  "title": "Không đủ số dư",
  "status": 403,
  "detail": "Số dư hiện tại là 30, giao dịch cần 50.",
  "instance": "/accounts/12345/transactions/abc",
  "balance": 30
}
```

Response lỗi khai `Content-Type: application/problem+json` (bản XML là `application/problem+xml`).
Năm field chuẩn, field nào cũng tuỳ chọn:

| Field | Kiểu | Ý nghĩa | Quy tắc đáng nhớ từ RFC |
|---|---|---|---|
| `type` | chuỗi URI | Định danh **loại** lỗi | Client **bắt buộc** dùng `type` làm định danh chính. Thiếu thì mặc định là `about:blank` |
| `title` | chuỗi | Tóm tắt ngắn của loại lỗi, cho người đọc | Không nên đổi giữa các lần xảy ra, trừ khi dịch sang ngôn ngữ khác |
| `status` | số | Status code HTTP | Chỉ để tham khảo; server **bắt buộc** dùng đúng code đó cho response thật |
| `detail` | chuỗi | Giải thích cho **lần** lỗi này | Nên giúp client sửa lỗi, không phải thông tin debug. Client không nên parse `detail` |
| `instance` | chuỗi URI | Định danh lần xảy ra cụ thể | Có thể truy cập được (trả chi tiết) hoặc chỉ là một id mờ |

Vài chi tiết hay bị bỏ qua:

- `type` là một URI nhưng **không bắt buộc** truy cập được. RFC khuyến khích URI `https://` trỏ tới trang
  tài liệu giải thích cách xử lý lỗi, nhưng client không nên tự động gọi vào URI đó. RFC khuyên dùng
  URI tuyệt đối; nếu dùng URI tương đối thì ghi đủ đường dẫn (`/problems/out-of-stock`), vì URI tương
  đối được hiểu theo URL của request và cùng một chuỗi có thể thành hai URI khác nhau.
- `type: "about:blank"` nghĩa là "không có gì thêm ngoài status code"; khi đó `title` nên đúng bằng
  reason phrase chuẩn (`"Not Found"` cho `404`).
- Field `status` trong body có thể lệch với status thật (ví dụ proxy đổi code dọc đường). Phần mềm HTTP
  chung chỉ nhìn status thật.
- Nếu một field có kiểu sai (ví dụ `status` là chuỗi), client phải bỏ qua field đó như thể không có.

*Field mở rộng* (extension members): mỗi problem type được thêm field riêng, như `balance` ở trên, hay
`errors` cho lỗi validation. Hai quy tắc:

1. Client **bắt buộc** bỏ qua field mở rộng mà nó không biết. Nhờ vậy server thêm field mới mà không
   làm vỡ client.
2. Tên field nên bắt đầu bằng chữ cái, chỉ gồm chữ, số và `_`, dài từ 3 ký tự (để còn chuyển được
   sang XML). `trace_id`, `errors`, `balance` đều hợp lệ.

RFC 9457 có sẵn ví dụ cho lỗi validation nhiều field: field mở rộng `errors` là mảng, mỗi phần tử có
`detail` và `pointer`, trong đó `pointer` là JSON Pointer (module 1.1) chỉ vị trí field lỗi trong body
request, dạng `"#/profile/color"`. Còn khi có nhiều lỗi **khác loại** nhau, RFC khuyên chỉ trả lỗi
liên quan hoặc gấp nhất, thay vì dựng một kiểu "lỗi gộp".

Định nghĩa một problem type mới (RFC section 4) bắt buộc phải ghi rõ ba thứ: type URI, `title` ngắn,
và status code đi kèm. Có thể quy định thêm field mở rộng và việc dùng `Retry-After`. RFC cũng khuyên
đừng định nghĩa type cho lỗi mà status code đã tự nói đủ: "không được ghi" thì `403` cho một PUT là
đủ rõ, không cần type riêng.

Đối chiếu Zalando (rule "MUST support problem JSON"): mọi endpoint phải trả được problem JSON cho cả
`4xx` và `5xx`. Nhưng Zalando cố ý **không** cho type URI truy cập được, và khuyên dùng URI tương đối
kiểu `/problems/out-of-stock`, vì tài liệu đã nằm trong OpenAPI còn URL tài liệu thì hay đổi. Cả hai
cách đều hợp chuẩn; quan trọng là chọn một và giữ cố định.

Đối chiếu ngôn ngữ khác: Spring Framework 6 có sẵn class `ProblemDetail` theo chuẩn này; Go không có
kiểu chuẩn trong thư viện, thường tự định nghĩa một struct có các field như trên.

#### Client dựa vào mã lỗi, không dựa vào câu chữ

Một response lỗi phục vụ hai kiểu người đọc khác nhau:

```
            ┌─ status  → phần mềm HTTP chung: retry, cache, monitoring, load balancer
Response ───┼─ type / code → code của client: phân nhánh xử lý (ổn định, là contract)
            └─ title / detail → con người: hiển thị, đọc log (được sửa, được dịch)
```

- Client phân nhánh theo `type` (hoặc một field `code` máy đọc được, như `errors[].code`). Đây là
  **contract**: đổi `type` của một lỗi đang có là breaking change (module 3.1).
- ⚠️ Không phân nhánh theo `title`, `detail` hay `message`. Câu chữ được dịch theo `Accept-Language`,
  được sửa chính tả, được viết lại cho dễ hiểu. `if ($body['message'] === 'Email đã tồn tại')` sẽ vỡ
  âm thầm vào ngày ai đó sửa dấu chấm hoặc bật tiếng Anh.
- ⚠️ Client phải chịu được response lỗi **không** phải problem JSON. Zalando nhấn mạnh điều này: lỗi có
  thể do tầng hạ tầng sinh ra (trang HTML `502` của Nginx, `504` của load balancer) chứ không phải từ
  code của bạn. Code client nên: đọc status trước, sau đó mới thử parse body nếu `Content-Type` đúng.
- Zalando cũng lưu ý: nhiều thư viện không coi `application/problem+json` là một dạng của
  `application/json`, nên client nên khai cả hai trong `Accept`.

```php
<?php

declare(strict_types=1);

// Phía client: phân nhánh theo status rồi theo type, không bao giờ theo câu chữ
function handleOrderError(int $status, string $contentType, string $body): string
{
    if (!str_starts_with($contentType, 'application/problem+json')) {
        // Lỗi từ hạ tầng (HTML của Nginx...), chỉ còn status để dựa vào
        return $status >= 500 ? 'retry_later' : 'show_generic_error';
    }

    /** @var array{type?: string, errors?: list<array{pointer: string, code: string}>} $problem */
    $problem = json_decode($body, true, flags: JSON_THROW_ON_ERROR);
    $type = $problem['type'] ?? 'about:blank';

    return match ($type) {
        'https://api.example.com/problems/out-of-credit' => 'ask_top_up',
        'https://api.example.com/problems/validation'    => 'highlight_fields',
        'https://api.example.com/problems/order-already-shipped' => 'show_contact_support',
        default => 'show_generic_error', // type lạ: xử lý theo status, không crash
    };
}

echo handleOrderError(502, 'text/html', '<html>Bad Gateway</html>'), "\n"; // retry_later
echo handleOrderError(
    403,
    'application/problem+json',
    '{"type":"https://api.example.com/problems/out-of-credit","title":"Không đủ số dư"}',
), "\n"; // ask_top_up
```

Nhiều API lớn không theo RFC 9457 nhưng giữ đúng nguyên tắc này. Ví dụ đối tượng lỗi của Stripe có
`type` (nhóm lỗi), `code` (mã cụ thể, máy đọc được), `message` (cho người đọc), `param` (field gây
lỗi): phần máy đọc và phần người đọc tách riêng.

#### Trace id để tra log

*Trace id* là một mã duy nhất gắn với một request. Mã này được ghi vào mọi dòng log của request đó
(và của mọi service mà request đi qua), và được trả về cho client trong response lỗi. Luồng support:

1. User gặp lỗi, app hiển thị "Mã lỗi: 4bf92f35...".
2. User gửi mã cho support.
3. Support tìm mã đó trong hệ thống log hoặc tracing, thấy đúng các dòng log và stack trace của request
   đó, dù server có hàng triệu request mỗi giờ.

Nên dùng luôn trace id theo chuẩn *W3C Trace Context* thay vì tự đặt format. Chuẩn này truyền qua
header `traceparent`, dạng `00-<trace-id>-<parent-id>-<flags>`, trong đó trace-id là 32 ký tự hex
(16 byte), parent-id là 16 ký tự hex, và trace-id toàn số 0 là không hợp lệ. Dùng chung trace-id với
hệ thống tracing (module 3.4) thì từ một dòng log nhảy thẳng được sang toàn bộ trace của request.

Trong Laravel 11+, facade `Context` giữ dữ liệu theo request và tự đính dữ liệu đó vào metadata của mọi
dòng log ghi ra trong request. Một middleware nhỏ là đủ:

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Context;
use Symfony\Component\HttpFoundation\Response;

final class AssignTraceId
{
    public function handle(Request $request, Closure $next): Response
    {
        // Có traceparent từ gateway/client thì dùng lại, không có thì tự sinh 16 byte ngẫu nhiên
        $traceId = self::fromTraceparent($request->header('traceparent'))
            ?? bin2hex(random_bytes(16));

        Context::add('trace_id', $traceId);   // từ đây mọi Log::... đều mang trace_id

        $response = $next($request);
        // Tên header do mình chọn; client đọc được mã ngay cả khi body không phải JSON
        $response->headers->set('X-Trace-Id', $traceId);

        return $response;
    }

    private static function fromTraceparent(?string $header): ?string
    {
        // 00-<trace-id 32 hex>-<parent-id 16 hex>-<flags 2 hex>
        if ($header === null
            || preg_match('/^[0-9a-f]{2}-([0-9a-f]{32})-[0-9a-f]{16}-[0-9a-f]{2}$/', $header, $m) !== 1) {
            return null;
        }

        return $m[1] === str_repeat('0', 32) ? null : $m[1];
    }
}
```

Đăng ký làm global middleware trong `bootstrap/app.php`:
`->withMiddleware(function (Middleware $middleware): void { $middleware->prepend(AssignTraceId::class); })`.
Exception ném ra bên trong được Laravel render thành response ngay trong pipeline, nên header
`X-Trace-Id` có mặt cả ở response lỗi.

⚠️ Trace id không thay được việc log đủ. Nó chỉ là chìa khoá; nếu lỗi `4xx` không được log (Laravel mặc
định không report `ValidationException`, `ModelNotFoundException`...) thì support tìm thấy mã mà không
thấy chi tiết. Với lỗi nghiệp vụ quan trọng, chủ động ghi log ở mức `info` hoặc `warning`.

#### Không lộ chi tiết nội bộ

RFC 9457 nói thẳng: problem details không phải công cụ debug của phần cài đặt bên dưới, mà là cách mô tả
chi tiết hơn về chính interface HTTP. Zalando có riêng một rule MUST: không trả stack trace. Lý do:
stack trace, câu SQL, tên class, đường dẫn file cho kẻ tấn công biết framework, phiên bản, cấu trúc DB,
và client cũng không được phép dựa vào chúng.

Laravel có ba chỗ cần biết:

| Tình huống | Response JSON mặc định | Rủi ro |
|---|---|---|
| `APP_DEBUG=true`, exception bất kỳ | `message`, `exception` (tên class), `file`, `line`, `trace` | ⚠️ Lộ toàn bộ. Production **luôn** `APP_DEBUG=false` |
| `APP_DEBUG=false`, exception không phải HTTP (ví dụ `QueryException`) | `{"message": "Server Error"}`, status `500` | An toàn |
| `APP_DEBUG=false`, HTTP exception (`abort()`, `NotFoundHttpException`...) | `message` của exception được giữ nguyên | ⚠️ Xem dưới |

⚠️ Bẫy ít người để ý: `findOrFail(5)` không tìm thấy sẽ ném `ModelNotFoundException` với message
`No query results for model [App\Models\Order] 5`, rồi được đổi thành `NotFoundHttpException` giữ
nguyên message đó. Vì là HTTP exception nên message này đi thẳng ra client **ngay cả khi**
`APP_DEBUG=false`, làm lộ tên class model. Handler chuẩn hoá ở nhóm Laravel bên dưới sẽ thay nó bằng
`detail` do mình viết.

Nguyên tắc chung khi viết handler: `detail` luôn là câu do bạn viết cho client, không bao giờ là
`$e->getMessage()` của một exception bạn không kiểm soát. Chi tiết thật để trong log, tra bằng trace id.

#### Laravel

Mặc định, Laravel trả lỗi JSON (khi request "muốn JSON", tức `$request->expectsJson()`) theo ba hình
dạng khác nhau:

```jsonc
// ValidationException, status 422
{"message": "The email field must be a valid email address. (and 1 more error)",
 "errors": {"email": ["The email field must be a valid email address."], "qty": ["..."]}}

// AuthenticationException, status 401 (không có header WWW-Authenticate)
{"message": "Unauthenticated."}

// HttpException và các loại khác (APP_DEBUG=false)
{"message": "No query results for model [App\\Models\\Order] 5"}    // 404
{"message": "This action is unauthorized."}                          // 403
{"message": "Server Error"}                                          // 500
```

Không cái nào là RFC 9457, cũng không có mã lỗi máy đọc được ngoài status. Muốn chuẩn hoá thì đăng ký
các closure `render` trong `withExceptions` ở `bootstrap/app.php` (Laravel 11+ không còn
`app/Exceptions/Handler.php`; cơ chế `report`/`render` chung ở
[05-php-laravel.md#14-exception-và-xử-lý-lỗi](05-php-laravel.md#14-exception-và-xử-lý-lỗi)).

Trước khi viết code, cần biết thứ tự Laravel xử lý một exception khi render (đọc từ
`Illuminate\Foundation\Exceptions\Handler::render`, Laravel 13):

```
1. mapException           các map() bạn đăng ký
2. $e->render() / Responsable   exception tự render thì dừng ở đây
3. prepareException       ĐỔI một số exception thành HTTP exception:
                            ModelNotFoundException  -> NotFoundHttpException (giữ exception gốc ở getPrevious())
                            AuthorizationException  -> AccessDeniedHttpException (403), hoặc HttpException nếu có status riêng
                            TokenMismatchException  -> HttpException 419
4. renderViaCallbacks     các closure render() bạn đăng ký, theo thứ tự đăng ký, closure đầu tiên trả khác null thắng
5. mặc định               HttpResponseException, AuthenticationException, ValidationException, còn lại
```

⚠️ Hệ quả của bước 3 đứng trước bước 4: một closure type-hint `ModelNotFoundException` hoặc
`AuthorizationException` **không bao giờ được gọi**, vì lúc tới bước 4 exception đã bị đổi kiểu. Phải
type-hint `NotFoundHttpException`, `AccessDeniedHttpException` hoặc interface chung
`HttpExceptionInterface`, rồi xem `getPrevious()` để biết exception gốc.

Bước 1: một helper dựng response problem+json, để mọi chỗ ra cùng một hình dạng.

```php
<?php

declare(strict_types=1);

namespace App\Support;

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Context;

final class Problem
{
    private const BASE = 'https://api.example.com/problems/';

    /**
     * @param array<string, mixed> $extensions
     * @param array<string, mixed> $headers
     */
    public static function response(
        int $status,
        string $type,
        string $title,
        ?string $detail = null,
        array $extensions = [],
        array $headers = [],
    ): JsonResponse {
        $body = [
            'type' => $type === 'about:blank' ? $type : self::BASE . $type,
            'title' => $title,
            'status' => $status,
        ];
        if ($detail !== null) {
            $body['detail'] = $detail;
        }
        $body += $extensions;

        $traceId = Context::get('trace_id');
        if (is_string($traceId)) {
            $body['trace_id'] = $traceId;
        }

        // Truyền Content-Type sẵn thì JsonResponse giữ nguyên, không ghi đè thành application/json
        return new JsonResponse($body, $status, ['Content-Type' => 'application/problem+json'] + $headers);
    }
}
```

Bước 2: exception nghiệp vụ tự mang type, status, title. Mỗi lỗi nghiệp vụ là một class, và class đó
chính là "định nghĩa problem type" theo RFC section 4.

```php
<?php

declare(strict_types=1);

namespace App\Exceptions;

use RuntimeException;

abstract class DomainProblem extends RuntimeException
{
    abstract public function status(): int;

    abstract public function type(): string;

    abstract public function title(): string;

    /** @return array<string, mixed> */
    public function extensions(): array
    {
        return [];
    }
}

// (file riêng) app/Exceptions/OrderAlreadyShipped.php
final class OrderAlreadyShipped extends DomainProblem
{
    public function __construct(private readonly int $orderId)
    {
        parent::__construct("Đơn {$orderId} đã giao, không huỷ được.");
    }

    public function status(): int { return 409; }

    public function type(): string { return 'order-already-shipped'; }

    public function title(): string { return 'Đơn đã giao'; }

    public function extensions(): array { return ['order_id' => $this->orderId]; }
}
```

Bước 3: đăng ký các closure trong `bootstrap/app.php` (đoạn trích, không phải file hoàn chỉnh).

```php
use App\Exceptions\DomainProblem;
use App\Support\Problem;
use Illuminate\Auth\Access\AuthorizationException;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Database\Eloquent\ModelNotFoundException;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Http\Exceptions\HttpResponseException;
use Illuminate\Http\Request;
use Illuminate\Support\Str;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Exception\HttpExceptionInterface;

->withExceptions(function (Exceptions $exceptions): void {
    // Request dưới api/* luôn nhận JSON, kể cả khi client quên gửi Accept
    $exceptions->shouldRenderJsonWhen(
        fn (Request $request, Throwable $e): bool => $request->is('api/*') || $request->expectsJson(),
    );

    // 1. Validation -> 422, mỗi field một phần tử có pointer và code máy đọc được
    $exceptions->render(function (ValidationException $e, Request $request) {
        if (! $request->is('api/*')) {
            return null; // trang web: để Laravel redirect back như mặc định
        }
        $failed = $e->validator->failed(); // ['email' => ['Email' => []], 'qty' => ['Min' => ['1']]]
        $errors = [];
        foreach ($e->errors() as $field => $messages) {
            $rule = array_key_first($failed[$field] ?? []) ?? 'invalid';
            $errors[] = [
                'pointer' => '#/' . str_replace('.', '/', $field), // items.0.qty -> #/items/0/qty
                'code' => Str::snake($rule),                        // Email -> email, RequiredIf -> required_if
                'detail' => $messages[0],
            ];
        }

        return Problem::response(422, 'validation', 'Dữ liệu không hợp lệ',
            count($errors) . ' field không hợp lệ', ['errors' => $errors]);
    });

    // 2. Chưa xác thực -> 401, kèm WWW-Authenticate mà RFC 9110 bắt buộc
    $exceptions->render(function (AuthenticationException $e, Request $request) {
        if (! $request->is('api/*')) {
            return null;
        }

        return Problem::response(401, 'unauthenticated', 'Chưa xác thực',
            'Thiếu hoặc sai access token.', headers: ['WWW-Authenticate' => 'Bearer']);
    });

    // 3. Lỗi nghiệp vụ tự định nghĩa
    $exceptions->render(fn (DomainProblem $e, Request $request) => Problem::response(
        $e->status(), $e->type(), $e->title(), $e->getMessage(), $e->extensions(),
    ));

    // 4. Mọi HTTP exception: 404 (kể cả ModelNotFoundException), 403 (AuthorizationException),
    //    405, 429, abort(...). Giữ headers gốc: Allow của 405, Retry-After của 429
    $exceptions->render(function (HttpExceptionInterface $e, Request $request) {
        if (! $request->is('api/*')) {
            return null;
        }
        $status = $e->getStatusCode();
        $previous = $e->getPrevious();

        [$type, $title, $detail] = match (true) {
            $previous instanceof ModelNotFoundException =>
                ['not-found', 'Không tìm thấy', 'Resource không tồn tại.'], // không dùng message gốc: lộ tên model
            $previous instanceof AuthorizationException =>
                ['forbidden', 'Không có quyền', 'Bạn không có quyền thực hiện thao tác này.'],
            $status === 429 => ['rate-limited', 'Gọi quá nhiều', 'Thử lại sau thời gian trong Retry-After.'],
            default => ['about:blank', Response::$statusTexts[$status] ?? 'Error', null],
        };

        return Problem::response($status, $type, $title, $detail, headers: $e->getHeaders());
    });

    // 5. Lưới cuối: lỗi chưa lường trước -> 500 chung chung. Đăng ký SAU CÙNG
    $exceptions->render(function (Throwable $e, Request $request) {
        if (! $request->is('api/*') || $e instanceof HttpResponseException || config('app.debug')) {
            return null; // HttpResponseException đã mang sẵn response; debug thì để trang lỗi chi tiết
        }

        return Problem::response(500, 'internal', 'Lỗi hệ thống',
            'Đã có lỗi xảy ra. Gửi trace_id cho bộ phận hỗ trợ.');
    });
})
```

Giải thích các quyết định trong đoạn trên:

- Mỗi closure trả `null` cho request không thuộc API, để trang web vẫn chạy như mặc định (validation
  redirect back, `401` redirect về trang login).
- Closure `Throwable` đăng ký cuối, vì Laravel duyệt các closure theo thứ tự đăng ký và closure khớp đầu
  tiên trả khác `null` sẽ thắng. ⚠️ Nó phải bỏ qua `HttpResponseException`: exception này đã mang sẵn
  response (ví dụ FormRequest tự override `failedValidation`), nếu bắt nhầm sẽ biến thành `500`.
- `render` chỉ quyết định response, không ảnh hưởng việc report. Lỗi `500` vẫn được log như cũ, và nhờ
  `Context` dòng log có `trace_id` trùng với `trace_id` trong body.
- Mã `code` của validation lấy từ `$e->validator->failed()` (tên rule bị trượt). Với rule là class tự
  viết, key là tên class, nên cần map riêng nếu muốn mã đẹp.

Kết quả cho một request tạo đơn sai hai field (output minh hoạ, không phải chạy thật; `detail` từng
field là message validation mặc định của Laravel):

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json
X-Trace-Id: 4bf92f3577b34da6a3ce929d0e0e4736

{
  "type": "https://api.example.com/problems/validation",
  "title": "Dữ liệu không hợp lệ",
  "status": 422,
  "detail": "2 field không hợp lệ",
  "errors": [
    {"pointer": "#/email", "code": "email", "detail": "The email field must be a valid email address."},
    {"pointer": "#/items/0/qty", "code": "min", "detail": "The items.0.qty field must be at least 1."}
  ],
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
}
```

Cách khác cho lỗi nghiệp vụ: cho chính exception một method `render(Request $request)` trả response.
Laravel gọi method này ở bước 2, trước cả các closure. Gọn khi ít loại lỗi; với nhiều loại, một lớp cha
`DomainProblem` như trên giữ định dạng ở một chỗ duy nhất.

Kiểm tra bằng test (Pest hoặc PHPUnit của Laravel), để định dạng lỗi không bị ai vô tình phá:

```php
public function test_validation_error_is_problem_json(): void
{
    $this->postJson('/api/orders', ['email' => 'khong-phai-email'])
        ->assertStatus(422)
        ->assertHeader('Content-Type', 'application/problem+json')
        ->assertJsonPath('type', 'https://api.example.com/problems/validation')
        ->assertJsonPath('errors.0.pointer', '#/email');
}
```

**Tóm tắt nhanh**
- RFC 9457 (thay RFC 7807): `application/problem+json` với `type`, `title`, `status`, `detail`,
  `instance`, cộng field mở rộng tuỳ ý (`errors`, `trace_id`).
- Client phân nhánh theo `type` hoặc `code`, không theo `title`/`detail`/`message` (được dịch, được sửa);
  bỏ qua field lạ; chịu được lỗi không phải problem JSON từ hạ tầng.
- Trace id theo W3C Trace Context (32 hex trong `traceparent`), ghi vào mọi dòng log và trả về client.
- Không lộ stack trace, SQL, tên class; production `APP_DEBUG=false`; `detail` luôn do mình viết, vì
  message của HTTP exception (kể cả `ModelNotFoundException`) đi thẳng ra client.
- Laravel: `render()` trong `withExceptions`; `ModelNotFoundException` và `AuthorizationException` bị đổi
  thành HTTP exception **trước** khi tới closure, nên phải type-hint `HttpExceptionInterface` và xem
  `getPrevious()`.

**Nguồn**: [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457) ·
[Zalando: HTTP status codes and errors](https://opensource.zalando.com/restful-api-guidelines/#http-status-codes-and-errors) ·
[Laravel: Rendering Exceptions](https://laravel.com/docs/errors#rendering-exceptions) ·
[Laravel source: Foundation/Exceptions/Handler.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Exceptions/Handler.php) ·
[W3C Trace Context](https://www.w3.org/TR/trace-context/)

---

### 1.4 Filtering, sorting, pagination

Module này trả lời: một endpoint danh sách nên nhận tham số lọc, sắp xếp, phân trang theo quy ước
nào; vì sao offset pagination chậm dần và lặp dòng, cursor chứa gì; và các bẫy khi biến tham số
query thành câu SQL.

#### Quy ước tham số query

Endpoint danh sách (`GET /orders`) thường nhận bốn loại tham số. Không có RFC nào chuẩn hoá tên
của chúng, nên điều quan trọng là chọn một quy ước và giữ nhất quán trên toàn API:

| Mục đích | Ví dụ | Ý nghĩa |
|---|---|---|
| Lọc (*filter*) | `?status=paid&created_from=2026-01-01` | Chỉ lấy đơn đã thanh toán, tạo từ 01/01/2026 |
| Sắp xếp (*sort*) | `?sort=-created_at,id` | Mới nhất trước; trùng `created_at` thì theo `id` tăng dần. Dấu `-` là giảm dần |
| Chọn field (*field selection*) | `?fields=id,status,total` | Chỉ trả ba field này, giảm kích thước response |
| Kèm quan hệ | `?include=customer` | Nhúng thông tin khách hàng vào từng đơn |

Tất cả là input do người dùng điều khiển, nên phải coi như dữ liệu không tin được. Có ba bẫy chính:

⚠️ Bẫy 1: đưa thẳng tên cột từ query string vào SQL. Tên cột không bind được bằng placeholder `?`
như giá trị, nên `orderBy($request->query('sort'))` là mở cửa cho SQL injection qua tên cột, và
cũng cho phép sort theo cột nhạy cảm như `password_hash` để dò dữ liệu. Cách đúng là *whitelist*
(danh sách cho phép): ánh xạ từ tên công khai sang tên cột thật, từ chối mọi thứ khác.

⚠️ Bẫy 2: cho sort hoặc filter theo cột không có index. Trên bảng vài chục triệu dòng, một
`ORDER BY` cột không index buộc DB đọc cả bảng rồi sort (filesort), vài giây mỗi request, và một
client gọi lặp lại là đủ làm chậm cả DB. Whitelist vì vậy nên chỉ chứa những tổ hợp có index phục
vụ.

⚠️ Bẫy 3: không giới hạn kích thước trang. `?limit=1000000` bắt server load một triệu dòng vào RAM
của PHP. Google AIP-158 đưa ra quy tắc gọn: `page_size` không bắt buộc; không gửi (hoặc gửi `0`) thì
dùng mặc định có ghi trong tài liệu; gửi lớn hơn mức tối đa thì server tự hạ về mức tối đa chứ
không báo lỗi; gửi số âm thì báo lỗi `INVALID_ARGUMENT` (với REST là `400`). Server cũng được phép
trả ít hơn số yêu cầu, kể cả trả 0 phần tử khi chưa hết dữ liệu, nên client không được suy ra "hết
dữ liệu" từ việc trang bị thiếu.

Ví dụ whitelist trong Laravel (đoạn trích trong controller):

```php
<?php
declare(strict_types=1);

use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;

// Tên công khai => cột thật. Chỉ đưa vào cột có index phục vụ, ví dụ (created_at, id), (total_amount, id)
const SORTABLE = ['created_at' => 'created_at', 'total' => 'total_amount'];

function listOrders(Request $request): mixed
{
    $query = Order::query();

    // Lọc: chỉ nhận giá trị hợp lệ, bind như giá trị bình thường
    $status = $request->query('status');
    if (is_string($status)) {
        if (!in_array($status, ['pending', 'paid', 'cancelled'], true)) {
            throw ValidationException::withMessages(['status' => 'invalid_value']);
        }
        $query->where('status', $status);
    }

    // Sắp xếp: "-created_at" => created_at DESC
    $sort = (string) $request->query('sort', '-created_at');
    $direction = str_starts_with($sort, '-') ? 'desc' : 'asc';
    $field = ltrim($sort, '-');
    if (!array_key_exists($field, SORTABLE)) {
        throw ValidationException::withMessages(['sort' => 'unsupported_sort_field']);
    }
    $query->orderBy(SORTABLE[$field], $direction)
          ->orderBy('id', $direction);          // tie-breaker, xem phần "Cursor chứa gì"

    // Giới hạn trang: mặc định 20, tối đa 100, hạ về 100 nếu vượt
    $limit = min(max((int) $request->query('limit', 20), 1), 100);

    return $query->cursorPaginate($limit);
}
```

Trong thực tế nên đặt các luật này vào FormRequest (module 2.6) để controller gọn, nhưng ý chính
không đổi: tên cột luôn đi qua một bảng ánh xạ do server định nghĩa.

#### Offset và cursor

Có hai cách chia một danh sách dài thành trang.

*Offset pagination*: client nói "cho tôi trang 5, mỗi trang 20 dòng", server dịch thành
`LIMIT 20 OFFSET 80`. Dễ làm, nhảy thẳng tới trang bất kỳ được. Nhưng Use The Index, Luke chỉ ra hai
nhược điểm:

1. Chậm dần theo độ sâu. `OFFSET 80` không có nghĩa là DB "nhảy" tới dòng 81; nó vẫn phải đi qua
   80 dòng đầu theo thứ tự sort rồi vứt đi. Trang 5000 với 20 dòng mỗi trang nghĩa là đọc gần
   100.000 dòng để trả 20.
2. Trang bị "trôi" khi dữ liệu thay đổi. Offset chỉ biết bỏ qua **bao nhiêu** dòng, không biết bỏ
   qua **những dòng nào**. Ví dụ, user đang xem trang 1 (đơn 1 tới 20, mới nhất trước), có một đơn
   mới được tạo:

```
Trước khi có đơn mới          Sau khi có đơn mới X
trang 1: [1 ... 20]           trang 1: [X, 1 ... 19]
trang 2: [21 ... 40]          trang 2: [20, 21 ... 39]   <- đơn 20 hiện lại lần hai
```

   Xoá dòng thì ngược lại: một dòng bị đẩy lên trang đã xem và bị sót.

*Cursor pagination* (còn gọi *keyset pagination*, Use The Index, Luke gọi là *seek method*): thay vì
đếm vị trí, client gửi lại "đã xem tới dòng nào", và server lấy các dòng đứng **sau** dòng đó:

```sql
-- Trang đầu
SELECT id, status, total_amount, created_at FROM orders
ORDER BY created_at DESC, id DESC LIMIT 20;

-- Trang sau: dòng cuối trang trước có created_at = '2026-03-01 10:00:00', id = 734501
SELECT id, status, total_amount, created_at FROM orders
WHERE (created_at, id) < ('2026-03-01 10:00:00', 734501)
ORDER BY created_at DESC, id DESC LIMIT 20;
```

Với index `(created_at, id)`, DB đi thẳng xuống cây B+tree tới đúng vị trí đó rồi đọc 20 entry, nên
trang thứ 5000 rẻ như trang đầu. Dòng mới chèn lên đầu không làm xê dịch điểm bắt đầu, nên không lặp.

| | Offset | Cursor |
|---|---|---|
| Nhảy thẳng tới trang N | Được | Không, chỉ đi tới hoặc lùi |
| Tốc độ trang sâu | Chậm dần, tuyến tính theo offset | Như nhau ở mọi trang, nếu index khớp thứ tự sort |
| Dữ liệu thay đổi lúc đang xem | Lặp hoặc sót dòng | Ổn định |
| Hiện "trang 3/250" | Được, nhưng phải thêm `COUNT(*)` | Không tự nhiên |
| Hợp với | Trang admin cần nhảy trang, bảng nhỏ | Feed, cuộn vô hạn, sync, export, API public |

⚠️ Cú pháp row value `(created_at, id) < (?, ?)` là chuẩn SQL và Postgres dùng index tốt với nó.
Với MySQL, Use The Index, Luke ghi nhận optimizer tính đúng kết quả nhưng không dùng row value để tra
index, nên nên viết thành dạng tách:
`WHERE created_at < ? OR (created_at = ? AND id < ?)` và kiểm tra bằng `EXPLAIN`. Chi tiết tầng SQL
(index, `EXPLAIN`, số liệu) ở
[03-database-sql.md, module 2.3](03-database-sql.md#23-đọc-explain-và-xử-lý-query-chậm).

Khi nào vẫn chọn offset: trang quản trị nội bộ cần "nhảy tới trang 37", bảng nhỏ vài nghìn dòng, hoặc
người dùng thật sự cần tổng số trang. Chi phí lớn nhất khi đó thường là `COUNT(*)` chạy mỗi request
(InnoDB không lưu sẵn số dòng, phải đếm). Các cách giảm:

- Không hiện tổng: dùng "Trang sau" thay vì "Trang 3/250" (`simplePaginate()` bên dưới).
- Đếm có trần: chỉ đếm tới một ngưỡng rồi hiện "hơn 10.000 kết quả", ví dụ
  `SELECT COUNT(*) FROM (SELECT 1 FROM orders WHERE status = 'paid' LIMIT 10001) t`.
- Cache tổng số trong vài phút, hoặc trả số ước lượng. AIP-158 cho phép `total_size` là ước lượng,
  miễn là tài liệu ghi rõ điều đó.
- Giới hạn độ sâu tối đa (ví dụ không cho vượt trang 500) và khuyến khích lọc hẹp hơn.

#### Cursor chứa gì

Cursor là giá trị các cột sort của phần tử cuối trang, cộng một cột *tie-breaker*.

*Tie-breaker* là một cột duy nhất (thường là khoá chính `id`) thêm vào cuối `ORDER BY` để mỗi dòng
có đúng một vị trí. Use The Index, Luke nhấn mạnh: phân trang đòi hỏi thứ tự sort *tất định*
(*deterministic*). Nếu chỉ sort theo `created_at` mà 30 đơn có cùng `created_at`, DB được phép trả
30 đơn đó theo bất kỳ thứ tự nào, và thứ tự có thể khác giữa hai lần chạy (ví dụ khi thực thi song
song). Hậu quả ở ranh giới trang:

- Cursor chỉ có `created_at`, điều kiện `created_at < ?`: mọi đơn cùng thời điểm với dòng cuối trang
  mà chưa được hiển thị bị bỏ qua luôn.
- Điều kiện `created_at <= ?`: những đơn đã hiển thị bị hiện lại.

Tie-breaker phải có mặt ở ba chỗ: `ORDER BY`, điều kiện `WHERE` của cursor, và index.

Cách đóng gói: đưa các giá trị vào JSON, mã hoá base64url (biến thể base64 dùng `-` và `_` thay
cho `+` và `/`, an toàn khi đặt trong URL), rồi trả cho client như một chuỗi.

Cursor phải *opaque* (mờ đục): với client đó là một chuỗi bí ẩn, chỉ được gửi lại nguyên vẹn. Lý do
AIP-158 đưa ra rất thực tế: nếu người dùng giải mã được cursor thì họ **sẽ** giải mã và tự dựng
cursor, và từ lúc đó format bên trong trở thành một phần của API, không đổi được nữa mà không phá
client. AIP-158 còn có các quy tắc đáng nhớ:

- ⚠️ Chỉ base64 một token vốn "trong suốt" thôi thì không đủ để làm mờ: ai cũng decode được trong
  một giây. (Gợi ý ngoài AIP: muốn chắc thì mã hoá (encrypt) hoặc ít nhất ký để phát hiện bị sửa.)
- Cursor chỉ nói "tiếp tục từ đâu", không bao giờ mang quyền truy cập. Server vẫn kiểm tra quyền như
  mọi request, không tin rằng "có cursor thì được xem".
- Khi gửi kèm cursor, các tham số khác (filter, sort) phải giữ như request đã sinh ra cursor đó. Đổi
  filter giữa chừng thì báo lỗi `400` thay vì trả kết quả vô nghĩa. Riêng `page_size` được đổi.
- Server được phép cho cursor hết hạn sau một thời gian hợp lý; AIP gợi ý khoảng ba ngày cho loại
  cursor được lưu trong DB.

Ví dụ đóng gói cursor có ký HMAC (*HMAC* là chữ ký tính từ nội dung và một secret chỉ server biết;
client sửa nội dung thì chữ ký không khớp; chi tiết ở module 2.4):

```php
<?php
declare(strict_types=1);

final class CursorCodec
{
    public function __construct(private readonly string $secret) {}

    /** @param array{created_at: string, id: int} $position */
    public function encode(array $position): string
    {
        $payload = self::b64url(json_encode($position, JSON_THROW_ON_ERROR));
        $signature = self::b64url(hash_hmac('sha256', $payload, $this->secret, true));
        return $payload . '.' . $signature;
    }

    /** @return array{created_at: string, id: int} */
    public function decode(string $cursor): array
    {
        $parts = explode('.', $cursor);
        if (count($parts) !== 2) {
            throw new InvalidArgumentException('invalid_cursor');
        }
        [$payload, $signature] = $parts;
        $expected = self::b64url(hash_hmac('sha256', $payload, $this->secret, true));
        // hash_equals so sánh thời gian hằng, tránh timing attack
        if (!hash_equals($expected, $signature)) {
            throw new InvalidArgumentException('invalid_cursor');
        }
        $json = base64_decode(strtr($payload, '-_', '+/'), true);
        if ($json === false) {
            throw new InvalidArgumentException('invalid_cursor');
        }
        /** @var array{created_at: string, id: int} */
        return json_decode($json, true, 512, JSON_THROW_ON_ERROR);
    }

    private static function b64url(string $bytes): string
    {
        return rtrim(strtr(base64_encode($bytes), '+/', '-_'), '=');
    }
}
```

Chuỗi cursor lỗi hoặc bị sửa thì trả `400` kèm mã lỗi `invalid_cursor` theo format lỗi ở module 1.3.

#### Trả metadata phân trang

Client cần biết hai việc: còn trang sau không, và gọi trang sau thế nào. Có hai cách phổ biến:

Cách 1, trong body:

```json
{
  "data": [{"id": 734520, "status": "paid"}, {"id": 734501, "status": "paid"}],
  "next_cursor": "eyJjcmVhdGVkX2F0Ijoi...Q.x8Kf...",
  "has_more": true
}
```

AIP-158 quy định: trường token trang sau **rỗng** là cách duy nhất báo "hết dữ liệu", và nếu chưa
hết (hoặc server không kịp xác định) thì phải có token. Đừng suy ra "hết" từ việc trang có ít phần
tử hơn `limit`.

Cách 2, header `Link` theo RFC 8288 (Web Linking):

```
Link: <https://api.example.com/orders?cursor=abc&limit=20>; rel="next",
      <https://api.example.com/orders?limit=20>; rel="first"
```

Mỗi link gồm một URI trong ngoặc nhọn và các tham số sau dấu `;`. Tham số `rel` (*relation type*) là
bắt buộc, nói link này quan hệ gì với trang hiện tại; `next`, `prev`, `first`, `last` là các giá trị
đã đăng ký sẵn. Nhiều link cách nhau bằng dấu phẩy. RFC cũng ghi rằng `rel` chỉ được xuất hiện một
lần mỗi link, và URI tương đối phải được phân giải theo quy tắc của RFC 3986. GitHub REST API là ví dụ nổi
tiếng dùng cách này. Ưu điểm: body giữ nguyên là một mảng thuần. Nhược điểm: client phải parse
header, và nhiều người quen đọc body hơn.

Một quy tắc từ AIP-158 cần nhớ khi thiết kế: phải có phân trang **ngay từ đầu**. Thêm phân trang vào
một endpoint đang trả toàn bộ danh sách là thay đổi phá client (*breaking change*): client cũ đang
nhận đủ 75 phần tử, nay chỉ nhận 50 mà không biết phải gọi tiếp (module 3.1).

#### Laravel

Laravel có ba hàm, mỗi hàm trả một class paginator khác nhau:

| Hàm | Class trả về | SQL | Ghi chú |
|---|---|---|---|
| `paginate(15)` | `LengthAwarePaginator` | `LIMIT/OFFSET` + một câu `COUNT(*)` | Có `total()`, `lastPage()` |
| `simplePaginate(15)` | `Paginator` | `LIMIT/OFFSET`, không đếm | Chỉ có "trang trước/sau" |
| `cursorPaginate(15)` | `CursorPaginator` | `WHERE` so sánh cột sort | Không đếm, không có số trang |

Tài liệu Laravel đưa ví dụ trang thứ hai của bảng `users` sort theo `id`:

```sql
-- Offset
select * from users order by id asc limit 15 offset 15;
-- Cursor
select * from users where id > 15 order by id asc limit 15;
```

Các giới hạn của `cursorPaginate()` theo tài liệu:

- Query phải có `ORDER BY`, và các cột sort phải thuộc bảng đang phân trang.
- Thứ tự sort phải dựa trên ít nhất một cột unique hoặc tổ hợp cột unique (chính là tie-breaker).
- ⚠️ Cột sort chứa `NULL` không được hỗ trợ. Muốn sort theo cột nullable (ví dụ `paid_at`) thì phải
  chọn cách khác, ví dụ lọc bỏ `NULL` hoặc dùng cột thay thế.
- Biểu thức trong `ORDER BY` chỉ dùng được khi được đặt alias và đưa vào `SELECT`; biểu thức có tham
  số bind thì không hỗ trợ.

⚠️ Cursor của Laravel là base64 của một JSON, không ký. Ví dụ trong tài liệu,
`eyJpZCI6MTUsIl9wb2ludHNUb05leHRJdGVtcyI6dHJ1ZX0`, decode ra
`{"id":15,"_pointsToNextItems":true}`. Client đọc và sửa được nó. Điều này không gây lỗ hổng quyền
nếu query vẫn lọc theo quyền của user (cursor chỉ đổi điểm bắt đầu), nhưng nó không opaque theo
nghĩa của AIP-158. API public cần chắc chắn thì tự đóng gói như `CursorCodec` ở trên.

Trả paginator thẳng từ route thì Laravel tự chuyển sang JSON, dữ liệu nằm dưới `data`. Với
`paginate()` có các field như `total`, `per_page`, `current_page`, `last_page`, `next_page_url`.
Dùng qua API Resource (`OrderResource::collection($paginator)`) thì hình dạng chuyển thành `data`,
`links`, `meta` (module 2.6). Khi link trang sau cần giữ các tham số filter và sort hiện tại, gọi
`->withQueryString()` trên paginator.

**Tóm tắt nhanh**
- Filter và sort theo whitelist cột có index; tên cột không bao giờ đi thẳng từ query string vào SQL;
  luôn có `limit` mặc định và trần.
- Offset chậm dần (DB vẫn đọc rồi bỏ các dòng trước) và lặp/sót dòng khi dữ liệu thay đổi; cursor
  nhanh đều và ổn định nhưng không nhảy trang được.
- Cursor = giá trị cột sort của dòng cuối + tie-breaker unique; thiếu tie-breaker là sót hoặc lặp ở
  ranh giới trang. Trên MySQL viết điều kiện dạng `OR` thay cho row value.
- Cursor phải opaque, không mang quyền, đi kèm đúng bộ filter đã sinh ra nó; base64 trần không đủ.
- "Hết dữ liệu" báo bằng `next_cursor` rỗng (hoặc không có `rel="next"`), không suy từ trang thiếu.
- Laravel: `paginate()` có `COUNT(*)`, `simplePaginate()` không đếm, `cursorPaginate()` là keyset,
  không hỗ trợ cột sort có `NULL`.

**Nguồn**: [Google AIP-158: Pagination](https://google.aip.dev/158) ·
[Use The Index, Luke: Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page) ·
[RFC 8288: Web Linking](https://www.rfc-editor.org/rfc/rfc8288) (section 3) ·
[Laravel: Pagination](https://laravel.com/docs/pagination#cursor-pagination)


---

## Chặng 2: Làm chủ

### 2.1 Idempotency key và retry an toàn

Module này trả lời: làm sao để client retry một `POST /payments` mà không trừ tiền hai lần; server
phải lưu gì và xử lý thế nào khi hai request trùng đến cùng lúc hoặc server chết giữa chừng; và vì
sao idempotency key vẫn cần một ràng buộc nghiệp vụ trong DB đứng sau.

#### Vấn đề

Bài viết của Stripe về idempotency chia lỗi mạng thành ba thời điểm, và cả ba đều để client trong
trạng thái không biết:

1. Kết nối hỏng trước khi request tới server: server chưa làm gì, retry an toàn.
2. Kết nối hỏng khi server đang xử lý: server có thể đã làm một nửa.
3. Server xử lý xong nhưng response mất trên đường về (timeout, mất sóng): tiền đã trừ, client
   không biết.

Bài viết lưu ý: đôi khi lỗi đủ rõ để biết retry là an toàn (ví dụ không kết nối được tới server),
nhưng nhiều trường hợp khác thì mơ hồ: kết nối đứt giữa chừng hay timeout đều hiện ra như một
exception, và client không biết server đã làm tới đâu. Nếu client retry
`POST /payments` ở trường hợp 3, server trừ tiền lần hai. Nếu client không retry ở trường hợp 1, đơn
hàng không bao giờ được thanh toán.

Với method idempotent (`PUT`, `DELETE`, module 1.1), retry an toàn sẵn. Với `POST`, cần thêm một cơ
chế để server nhận ra "request này là lần thử lại của một request tôi đã thấy". Đó là idempotency key.

Nguồn retry không chỉ đến từ user bấm hai lần: SDK và HTTP client tự retry (SDK của Stripe có cấu hình
số lần retry mạng), load balancer và proxy retry, job queue chạy lại job lỗi. Chống bấm đúp ở UI
không chặn được những nguồn đó.

#### Idempotency key

*Idempotency key* là một chuỗi duy nhất do **client** sinh ra cho mỗi ý định của user, gửi trong
header:

```
POST /payments HTTP/1.1
Idempotency-Key: 8e03978e-40d5-43e8-bc93-6894a57f9324
Content-Type: application/json

{"order_id": 123, "amount": 250000, "currency": "VND"}
```

Quy tắc phía client:

- Sinh key **một lần** cho mỗi ý định ("thanh toán đơn 123 lúc này"), lưu lại, và dùng lại đúng key
  đó cho mọi lần retry. ⚠️ Sinh key mới mỗi lần retry thì server coi mỗi lần là một ý định mới, cơ chế
  mất tác dụng.
- Stripe gợi ý UUID v4 hoặc chuỗi ngẫu nhiên đủ *entropy* (độ ngẫu nhiên) để không trùng. Cách khác
  Stripe nêu: suy key ra từ một đối tượng nghiệp vụ, ví dụ id của giỏ hàng, để chặn gửi đúp một cách
  tự nhiên.
- Stripe giới hạn key tối đa 255 ký tự và khuyên không dùng dữ liệu nhạy cảm (email, số định danh)
  làm key.
- Chỉ đổi sang key mới khi **cố ý** gửi một request khác, ví dụ sau khi sửa tham số vì lỗi `4xx`.
- Retry với *exponential backoff* (chờ tăng theo cấp số nhân, khoảng `2^n` sau lần thất bại thứ n) và
  *jitter* (cộng thêm một khoảng ngẫu nhiên), để hàng nghìn client không cùng retry vào một thời
  điểm và dìm server vừa hồi phục (*thundering herd*). Chi tiết ở module 2.5.

Stripe cho biết mọi request `POST` nhận idempotency key; gửi key cho `GET` và `DELETE` không có tác
dụng vì chúng vốn idempotent. AWS dùng cùng ý tưởng dưới tên *client request token* (field
`ClientToken` trong API của EC2), và SDK/CLI của AWS tự sinh token nếu người gọi không truyền.

Về chuẩn: header `Idempotency-Key` do Stripe phổ biến, nhiều bên dùng theo (bản draft IETF liệt kê
Adyen, Dwolla, WorldPay...), một số bên dùng tên khác (PayPal: `PayPal-Request-Id`; Square đặt
`idempotency_key` trong body). IETF có draft `draft-ietf-httpapi-idempotency-key-header`; bản cuối
là -07 (10/2025), đã hết hạn vào 04/2026 và chưa thành RFC. Nội dung draft vẫn là tham chiếu tốt
cho ngữ nghĩa, nên phần dưới dùng các status code nó đề xuất.

#### Server lưu gì

Mỗi key là một bản ghi trong DB. Bảng tham khảo trong bài của Brandur (viết cho Postgres, mô phỏng
cách Stripe làm) có các nhóm cột sau:

| Nhóm | Cột trong bài Brandur | Để làm gì |
|---|---|---|
| Định danh | `user_id`, `idempotency_key`, unique trên cặp `(user_id, idempotency_key)` | Hai user khác nhau tình cờ sinh cùng key không đụng nhau |
| Khoá xử lý | `locked_at` | Đánh dấu đang có request xử lý key này; quá hạn thì coi như lock đã chết |
| Tham số request | `request_method`, `request_path`, `request_params` | Phát hiện cùng key nhưng nội dung khác; cho tiến trình nền chạy tiếp request dở |
| Tiến độ | `recovery_point` (`started` ... `finished`) | Request retry biết phải làm tiếp từ bước nào |
| Kết quả | `response_code`, `response_body` | Trả lại y nguyên cho lần retry sau khi đã xong |
| Thời gian | `created_at`, `last_run_at` | Dọn key cũ, theo dõi lần chạy gần nhất |

Brandur còn giới hạn độ dài key bằng `CHECK` để "không ai gửi thứ gì quá kỳ quặc". Thay vì lưu toàn
bộ tham số, nhiều hệ thống chỉ lưu *fingerprint* (vân tay) của request: draft IETF liệt kê các cách
như checksum toàn bộ payload, checksum một số field, hoặc so từng field. Lưu ý hash phải tính trên
dạng chuẩn hoá của body (cùng thứ tự key JSON), nếu không hai body cùng nghĩa khác khoảng trắng sẽ
bị coi là khác nhau.

Thiết kế bảng cho MySQL (kiểu cột, index cho việc dọn key, TTL) và middleware Laravel là
[bài tập 2 ở file plan](../09-api-design.md#bài-tập-tự-làm); phần dưới cung cấp đủ nguyên liệu.

#### Luồng xử lý

Lõi của cơ chế là: **dùng unique constraint của DB làm trọng tài** xem request nào là "lần đầu".

1. Server nhận request, lấy key từ header. Endpoint bắt buộc key mà thiếu thì draft IETF đề xuất
   `400`, kèm link tới tài liệu.
2. `INSERT` một bản ghi mới với trạng thái `processing` và hash của request. Cặp
   `(client_id, idempotency_key)` có unique constraint.
3. `INSERT` thành công: đây là lần đầu. Xử lý nghiệp vụ, lưu status và body của response vào bản ghi,
   chuyển sang `completed`.
4. `INSERT` báo trùng key (MySQL: lỗi `1062 Duplicate entry`): đọc bản ghi cũ và rẽ nhánh.

| Bản ghi cũ | Trả về | Lý do |
|---|---|---|
| Hash khác request hiện tại | `422` (draft IETF) | Client dùng lại key cho một request khác: bug phía client, không được đoán ý |
| Đang `processing`, lock chưa quá hạn | `409` (draft IETF, Stripe) | Request đầu chưa xong; client chờ rồi thử lại, không cần sửa gì |
| Đã `completed` | Status và body đã lưu | Client chỉ cần kết quả của lần đầu |

Mã cho trường hợp hash khác không thống nhất giữa các nguồn: draft IETF đề xuất `422`, còn code mẫu
của Brandur trả `409`. Quan trọng là tài liệu API ghi rõ và kèm mã lỗi máy đọc được (module 1.3).
Stripe thêm header `Idempotent-Replayed: true` khi response là bản phát lại, để client phân biệt.
AWS gọi yêu cầu này là trả response *tương đương về ngữ nghĩa*: client nhận cùng một ý nghĩa như lần
đầu, nên code phía client không cần biết đã có retry.

⚠️ Bẫy kinh điển: `SELECT` xem key có chưa, chưa có thì `INSERT`. Đây là *check-then-act*, và hai
request trùng đến cùng lúc sẽ cùng lọt qua (*race condition*, xem
[13-concurrency.md](../13-concurrency.md)):

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `SELECT ... WHERE key = 'k1'` | | A thấy chưa có |
| 2 | | `SELECT ... WHERE key = 'k1'` | B cũng thấy chưa có |
| 3 | Gọi cổng thanh toán, trừ tiền | | |
| 4 | | Gọi cổng thanh toán, trừ tiền | Trừ tiền hai lần |
| 5 | `INSERT` key | `INSERT` key (có thể lỗi trùng, nhưng đã muộn) | |

Cùng tình huống nhưng dùng `INSERT` làm bước đầu tiên:

| Bước | Request A | Request B | Kết quả |
|---|---|---|---|
| 1 | `INSERT ... ('k1', 'processing')`, commit | | A thắng, sở hữu key |
| 2 | | `INSERT ... ('k1', 'processing')` | Lỗi 1062, B không xử lý nghiệp vụ |
| 3 | Gọi cổng thanh toán | B đọc bản ghi: `processing` | B trả `409` |
| 4 | Lưu response, `completed` | | Lần retry sau của B nhận response đã lưu |

`INSERT` có unique constraint là một thao tác nguyên tử: DB đảm bảo chỉ một trong hai thắng. Trong
InnoDB, nếu A chưa commit bản ghi key, `INSERT` của B không lỗi ngay mà **chờ** lock của A; A commit
thì B nhận lỗi trùng, A rollback thì B chèn được (chi tiết lock ở
[03-database-sql.md, module 2.6](03-database-sql.md#26-lock-thực-dụng)). Nếu lưu key trong Redis
thì thao tác tương đương là `SET key value NX EX <giây>` (chỉ set khi key chưa tồn tại, kèm thời hạn).

Minh hoạ phần lõi bằng Laravel (đoạn trích, không phải middleware hoàn chỉnh):

```php
<?php
declare(strict_types=1);

use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Support\Facades\DB;

// $clientId, $key, $requestHash đã có từ request
try {
    DB::table('idempotency_keys')->insert([
        'client_id'       => $clientId,
        'idempotency_key' => $key,
        'request_hash'    => $requestHash,
        'status'          => 'processing',
        'locked_at'       => now(),
        'created_at'      => now(),
    ]);
    // Lần đầu: xử lý nghiệp vụ, rồi UPDATE status = 'completed', response_code, response_body
} catch (UniqueConstraintViolationException) {
    $existing = DB::table('idempotency_keys')
        ->where('client_id', $clientId)
        ->where('idempotency_key', $key)
        ->first();
    // Rẽ nhánh theo bảng ở trên: hash khác => 422, processing => 409, completed => replay
}
```

`UniqueConstraintViolationException` là lớp con của `QueryException`, được thêm trong dòng Laravel
10.x. Ở phiên bản cũ hơn phải bắt `QueryException` rồi kiểm tra mã lỗi.

#### Khi server crash giữa chừng

⚠️ Server chết (OOM, deploy, pod bị kill) sau khi `INSERT` key `processing` nhưng trước khi đánh dấu
`completed`. Bản ghi `processing` nằm đó mãi, và mọi lần retry đều nhận `409`: user không bao giờ
thanh toán được. Cách xử lý của Brandur: lock có hạn. Cột `locked_at` ghi thời điểm khoá; request
retry thấy `locked_at` quá một ngưỡng timeout thì được phép lấy lại lock và chạy tiếp. Vì request có
thể được chạy lại, mọi bước bên trong phải an toàn khi chạy lại. Đây là chỗ khó nhất.

Có hai trường hợp, khó dần:

*Trường hợp 1: nghiệp vụ chỉ ghi vào DB của mình.* Đặt việc ghi key, ghi nghiệp vụ và ghi response
vào **cùng một transaction**. Crash giữa chừng thì transaction rollback, không còn gì dở dang, kể cả
bản ghi key; retry chạy lại từ đầu như lần đầu. Cách này đơn giản hơn nhiều so với trường hợp 2. AWS
nhấn mạnh việc ghi token và mọi thay đổi dữ liệu phải là một thao tác
ACID, để không bao giờ có "đã ghi token mà không tạo resource" hoặc ngược lại.

*Trường hợp 2: nghiệp vụ gọi hệ thống bên ngoài* (cổng thanh toán, gửi email, đẩy message lên Kafka).
Không thể bọc lời gọi bên ngoài trong transaction DB (rollback DB không hoàn lại tiền đã trừ, và giữ
transaction trong lúc chờ mạng là giữ lock). Brandur gọi đây là *foreign state mutation* (thay đổi
trạng thái ở hệ thống khác) và chia request thành nhiều *atomic phase*:

```
tx1: INSERT/lock key                     recovery_point = started
tx2: tạo ride + audit record            recovery_point = ride_created
     ── gọi Stripe tạo charge (bên ngoài, gửi kèm idempotency key riêng) ──
tx3: lưu charge_id                      recovery_point = charge_created
tx4: đưa job gửi email vào bảng staged_jobs, lưu response
                                        recovery_point = finished
```

- Mỗi atomic phase là một transaction DB, commit xong mới làm bước bên ngoài tiếp theo.
- *Recovery point* là tên của mốc đã qua, được cập nhật **trong cùng transaction** với phase đó. Request
  retry đọc `recovery_point` và nhảy thẳng tới bước chưa làm.
- Lời gọi bên ngoài phải tự idempotent. Brandur gửi cho Stripe một key tự dựng từ id bản ghi key
  (`rocket-rides-atomic-<id>`) thay vì chuyển tiếp key của client, để đảm bảo key duy nhất trên toàn
  hệ thống. Server chết lúc đang chờ Stripe thì lần retry gọi lại Stripe với cùng key, và Stripe không
  trừ tiền lần hai.
- Việc không cần kết quả ngay (gửi email biên lai) không gọi trực tiếp mà ghi vào bảng job trong cùng
  transaction, rồi một tiến trình khác đẩy sang queue sau khi commit (cùng ý tưởng với *outbox*, xem
  [12-messaging.md](../12-messaging.md)).
- Lỗi chắc chắn không bao giờ thành công (thẻ bị từ chối) thì lưu response lỗi, đánh dấu `finished`.
  Lỗi tạm thời thì mở lock và để client retry.

Ngoài tiến trình đẩy job từ `staged_jobs` sang queue (*enqueuer*), bài của Brandur còn mô tả hai
tiến trình nền: *completer* (Brandur gọi là mục tiêu mở rộng) tìm các request dở dang mà client đã bỏ
đi và tự đẩy chúng tới cuối; *reaper* xoá key cũ.

⚠️ Nếu dịch vụ bên ngoài không idempotent và cũng không nhận idempotency key, thì khi gặp lỗi không
rõ ràng (timeout, reset kết nối) bạn không biết retry có an toàn không. Brandur khuyên đi đường thận
trọng: đánh dấu thao tác là lỗi và để xử lý thủ công, trừ khi bên kia trả lỗi nói rõ là retry được.

#### Lưu bao lâu

Key không phải kho lưu trữ vĩnh viễn, chỉ để đảm bảo đúng trong ngắn hạn. Thời hạn (*TTL*, time to
live) phải phủ hết mọi lần retry hợp lý:

- Stripe: key có thể bị xoá khi đã được ít nhất 24 giờ. Dùng lại key sau khi bản gốc đã bị dọn thì
  Stripe coi là request mới.
- Brandur: gợi ý khoảng 24 giờ ở đầu bài, và cho *reaper* ngưỡng khoảng 72 giờ, để nếu thứ Sáu lỡ
  deploy bug làm lỗi hàng loạt request thì thứ Hai vẫn còn dữ liệu để sửa và chạy tiếp.
- AWS (EC2): giữ token trong suốt vòng đời resource cộng thêm một khoảng mà sau đó request tới muộn
  hẳn đã tới hoặc không còn hợp lệ.
- Draft IETF: server nên công bố chính sách hết hạn trong tài liệu.

Lưu response nào: đây là chỗ các nguồn khác nhau, cần hiểu cả hai trường phái.

| | Stripe | Brandur |
|---|---|---|
| Response thành công | Lưu | Lưu |
| Lỗi `4xx` do nghiệp vụ (ví dụ thẻ bị từ chối) | Lưu, retry cùng key nhận lại đúng lỗi đó | Lưu (lỗi không thể khắc phục) |
| Lỗi `500` | **Lưu**. Stripe khuyên coi kết quả `500` là chưa xác định và không retry bằng key mới, vì lần đầu có thể đã gây side effect | Không lưu: mở lock để client retry, request đi tiếp từ recovery point |
| Không lưu | Request trượt validation tham số, bị `429` rate limit (rate limiter chạy trước tầng idempotency), trùng với request đang chạy | |

Lý do Stripe lưu cả `500`: server có thể đã làm một phần việc trước khi lỗi, nên cho retry chạy lại
từ đầu là nguy hiểm; Stripe tự đối soát các request `500` ở phía mình và bắn webhook cho object phát
sinh. Lý do Brandur không lưu: nhờ recovery point, chạy lại là an toàn. Tức là: **chỉ được bỏ qua
việc lưu `5xx` khi logic bên trong an toàn khi chạy lại**.

AWS nêu thêm một ca: request retry tới muộn sau khi resource đã bị xoá. Với EC2, họ vẫn trả response
tương đương lần đầu thay vì báo lỗi, vì đó là hành vi ít gây bất ngờ nhất.

#### Các lớp phòng thủ khác

Idempotency key không phải lớp duy nhất:

1. Ràng buộc nghiệp vụ tự nhiên trong DB. Ví dụ bảng `payments` có unique trên `order_id` (hoặc trên
   `(order_id, attempt)` nếu cho thanh toán lại sau khi thất bại). Lớp này vẫn chặn được khi:
   client gửi hai key khác nhau cho cùng một đơn (bug client, hai tab trình duyệt), key đã hết hạn và
   bị dọn, hoặc có bug trong middleware idempotency. Bài của Brandur cũng khai unique cho
   `stripe_charge_id` và `(user_id, idempotency_key_id)` trong bảng `rides`.
2. Kiểm tra trạng thái trong nghiệp vụ: chỉ thanh toán đơn đang `pending`, dùng
   `UPDATE ... WHERE status = 'pending'` và kiểm tra số dòng bị ảnh hưởng.
3. Idempotency ở phía bên dưới: khi gọi sang cổng thanh toán, gửi kèm key của mình như Brandur làm.
4. UI disable nút sau khi bấm. Chỉ là tiện cho người dùng, không phải cơ chế an toàn.

Vì sao key không thay được unique nghiệp vụ: key bảo vệ **một ý định của một client** trong **một
khoảng thời gian**; unique nghiệp vụ bảo vệ **bất biến của dữ liệu** mãi mãi, bất kể request đến từ
đâu. Hai lớp chặn hai loại lỗi khác nhau.

**Tóm tắt nhanh**
- Timeout không cho client biết server đã xử lý hay chưa; idempotency key biến `POST` thành retry
  được. Client sinh key một lần cho mỗi ý định và dùng lại khi retry.
- Server dùng unique constraint trên `(client_id, key)` làm trọng tài, không `SELECT` rồi mới
  `INSERT`. Ba nhánh: hash khác (`422` theo draft IETF), đang xử lý (`409`), đã xong (phát lại response).
- Lock `processing` phải có hạn, và logic bên trong phải chạy lại được: cùng một transaction khi chỉ
  ghi DB của mình; atomic phase + recovery point + key riêng cho bên ngoài khi có gọi hệ thống khác.
- TTL tối thiểu phủ hết retry (Stripe: ít nhất 24 giờ). Lưu `5xx` hay không tuỳ việc chạy lại có an
  toàn không; Stripe lưu cả `500`.
- `Idempotency-Key` chưa phải RFC (draft IETF -07 đã hết hạn 04/2026).
- Luôn giữ unique constraint nghiệp vụ làm lớp phòng thủ cuối.

**Nguồn**: [Stripe: Idempotent requests](https://docs.stripe.com/api/idempotent_requests) ·
[Stripe: Advanced error handling](https://docs.stripe.com/error-low-level) ·
[Stripe blog: Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency) ·
[Brandur: Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys) ·
[AWS Builders' Library: Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) ·
[draft-ietf-httpapi-idempotency-key-header-07](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)


---

### 2.2 Ghi đồng thời, bulk, long-running operation

Module này trả lời: làm sao để hai người cùng sửa một resource mà không ai âm thầm mất thay đổi; thiết
kế API xử lý nhiều item trong một request; thao tác chạy vài phút thì API trả gì; và client với server
thoả thuận định dạng dữ liệu qua header thế nào.

#### Lost update khi hai người cùng sửa

*Lost update* (mất cập nhật) là khi thay đổi của người này bị người kia ghi đè mà không ai được báo.
RFC 9110 mô tả nó là "một client vô tình ghi đè công việc của client khác đang làm song song". Kịch
bản điển hình ở trang admin, với form gửi lại toàn bộ sản phẩm bằng `PUT`:

| Bước | Admin A | Admin B | Trên server |
|---|---|---|---|
| 1 | Mở form sản phẩm 5 | | giá 100, tên "Áo" |
| 2 | | Mở form sản phẩm 5 | giá 100, tên "Áo" |
| 3 | Sửa giá thành 120, lưu | | giá 120, tên "Áo" |
| 4 | | Sửa tên thành "Áo thun", lưu cả form (form vẫn ghi giá 100) | giá 100, tên "Áo thun" |
| 5 | | | Giá 120 của A mất, không ai biết |

Đây không phải lỗi DB: mỗi `UPDATE` đều đúng và nguyên tử. Lỗi nằm ở khoảng thời gian giữa lúc B **đọc**
(bước 2) và lúc B **ghi** (bước 4), có thể kéo dài nhiều phút, vượt xa bất kỳ transaction nào. Vì vậy
không giải được bằng transaction hay `SELECT ... FOR UPDATE` (không ai giữ lock DB trong lúc người
dùng ngồi gõ form). Phía DB của vấn đề này (read-modify-write, lock) ở
[03-database-sql.md, module 2.6](03-database-sql.md#26-lock-thực-dụng).

Có hai hướng:

- *Pessimistic* (bi quan): khoá resource khi người dùng mở form ("đang được A sửa"). Cần cơ chế hết hạn
  khoá, và người khác phải chờ.
- *Optimistic* (lạc quan): không khoá gì, cho mọi người sửa thoải mái; **lúc lưu** mới kiểm tra "bản
  tôi đã đọc có còn là bản mới nhất không". Hợp với API HTTP vì không cần giữ trạng thái giữa các
  request, và xung đột thật ra hiếm.

#### Optimistic concurrency bằng ETag và If-Match

*ETag* (entity tag) là một nhãn phiên bản mà server gắn vào response, trong header `ETag`. Theo RFC
9110, nó là một chuỗi *opaque* trong dấu ngoặc kép: client không cần biết nó được tạo thế nào, chỉ cần
gửi lại. Server tự chọn cách sinh, RFC gợi ý các cách: số revision nội bộ, hash của nội dung, hoặc
timestamp có độ phân giải dưới một giây. RFC cũng giải thích vì sao ETag đáng tin hơn ngày sửa đổi:
header ngày của HTTP (`Last-Modified`, `If-Unmodified-Since`) chỉ chính xác tới **giây**, hai lần sửa
trong cùng một giây không phân biệt được.

`If-Match` là header của request có nghĩa: "chỉ thực hiện nếu ETag hiện tại của resource khớp với một
trong các giá trị tôi gửi". Luồng đầu cuối:

```
Client                                   Server
  │ GET /products/5                        │
  │───────────────────────────────────────>│ SELECT ... → version = 7
  │ 200 OK, ETag: "v7", body {...}         │
  │<───────────────────────────────────────│
  │  (người dùng sửa form)                 │
  │ PUT /products/5, If-Match: "v7"        │
  │───────────────────────────────────────>│ UPDATE ... WHERE id = 5 AND version = 7
  │                                        │   1 dòng: thành công, version = 8
  │ 200 OK, ETag: "v8"                     │   0 dòng: đã có người sửa
  │   hoặc 412 Precondition Failed         │
  │<───────────────────────────────────────│
```

Chạy lại kịch bản của A và B với cơ chế này:

| Bước | Admin A | Admin B | Kết quả |
|---|---|---|---|
| 1 | `GET` → `ETag: "v7"` | | |
| 2 | | `GET` → `ETag: "v7"` | |
| 3 | `PUT`, `If-Match: "v7"` | | Khớp, lưu giá 120, version thành 8 |
| 4 | | `PUT`, `If-Match: "v7"` | Không khớp (hiện là v8): `412` |
| 5 | | Tải lại bản mới, thấy giá 120, sửa tên, `PUT` với `If-Match: "v8"` | Cả hai thay đổi đều còn |

Các status code liên quan:

- `412 Precondition Failed`: điều kiện `If-Match` sai. RFC 9110 bắt buộc server **không được** thực
  hiện method khi điều kiện sai. RFC còn cho một ngoại lệ: nếu server xác định được thay đổi đã được
  áp dụng rồi (ví dụ response lần trước bị mất), nó được phép trả `2xx`; nhưng với resource mà lần
  ghi nào cũng quan trọng, RFC khuyên chặt chẽ, luôn trả `412`.
- `428 Precondition Required` (RFC 6585): server **bắt buộc** request phải có điều kiện mà client
  không gửi `If-Match`. Mục đích đúng là chống lost update: không cho client "quên" kiểm tra. RFC 6585
  yêu cầu response giải thích cách gửi lại cho đúng.
- Zalando dùng đúng hai code này cho optimistic locking, và ghi chú rằng với `GET`/`HEAD` thì dùng
  `304` thay cho `412`.

Tầng DB dùng một cột `version` tăng mỗi lần ghi, và đưa điều kiện version vào chính câu `UPDATE`:

```sql
UPDATE products
SET price = 120, name = 'Áo', version = version + 1
WHERE id = 5 AND version = 7;
-- affected rows = 1: thành công
-- affected rows = 0: hoặc sản phẩm không tồn tại (404), hoặc version đã đổi (412)
```

⚠️ Kiểm tra version bằng một câu `SELECT` riêng rồi mới `UPDATE` là lặp lại lỗi check-then-act ở module
2.1: hai request có thể cùng đọc thấy version 7. Điều kiện phải nằm trong `WHERE` của `UPDATE` để DB
kiểm tra và ghi trong một thao tác nguyên tử.

Minh hoạ trong Laravel (đoạn trích controller, đơn giản hoá: chỉ nhận một ETag, không xử lý `*`):

```php
<?php
declare(strict_types=1);

use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

function updateProduct(Request $request, int $id): JsonResponse
{
    $ifMatch = $request->header('If-Match');
    if ($ifMatch === null) {
        return response()->json([
            'type'   => 'https://api.example.com/errors/precondition-required',
            'title'  => 'Thiếu If-Match',
            'status' => 428,
            'detail' => 'Gửi lại kèm If-Match bằng ETag nhận được từ GET /products/' . $id,
        ], 428)->header('Content-Type', 'application/problem+json');
    }

    // ETag có dạng "v7". W/"v7" không khớp vì If-Match so sánh kiểu strong
    if (preg_match('/^"v(\d+)"$/', $ifMatch, $m) !== 1) {
        return response()->json(['status' => 412, 'title' => 'ETag không khớp'], 412);
    }
    $expectedVersion = (int) $m[1];

    $affected = DB::table('products')
        ->where('id', $id)
        ->where('version', $expectedVersion)
        ->update([
            'price'      => $request->integer('price'),
            'name'       => $request->string('name')->toString(),
            'version'    => DB::raw('version + 1'),
            'updated_at' => now(),
        ]);

    if ($affected === 0) {
        $exists = DB::table('products')->where('id', $id)->exists();
        return response()->json(
            ['status' => $exists ? 412 : 404],
            $exists ? 412 : 404,
        );
    }

    $product = DB::table('products')->find($id);
    return response()->json($product)->header('ETag', '"v' . $product->version . '"');
}
```

Trong code thật, validate bằng FormRequest và render lỗi theo RFC 9457 ở exception handler (module 1.3,
2.6). Eloquent không có sẵn optimistic locking; phải tự viết điều kiện như trên.

UI hiển thị gì khi gặp `412`: không tự động ghi đè, cũng không âm thầm bỏ. Cách phổ biến là tải bản
mới nhất, báo "Sản phẩm vừa được người khác sửa", và cho người dùng xem khác biệt để quyết định áp lại
thay đổi của mình.

*Strong và weak ETag*. RFC 9110 định nghĩa:

- *Strong* ETag, ví dụ `"abc"` (mặc định): đổi mỗi khi dữ liệu của representation đổi.
- *Weak* ETag, có tiền tố `W/`, ví dụ `W/"abc"`: hai bản tương đương về nghĩa nhưng có thể khác
  byte. Server nào sinh ETag không thoả điều kiện strong thì bắt buộc phải đánh dấu weak.
- Có hai phép so sánh. *Strong comparison*: khớp khi cả hai đều không weak và giống nhau từng ký tự.
  *Weak comparison*: bỏ qua tiền tố `W/`, chỉ so phần trong ngoặc kép.

| ETag 1 | ETag 2 | Strong | Weak |
|---|---|---|---|
| `W/"1"` | `W/"1"` | không khớp | khớp |
| `W/"1"` | `W/"2"` | không khớp | không khớp |
| `W/"1"` | `"1"` | không khớp | khớp |
| `"1"` | `"1"` | khớp | khớp |

- `If-Match` bắt buộc dùng **strong** comparison, vì mục đích là chặn ghi khi có **bất kỳ** thay đổi
  nào. Hệ quả: weak ETag không bao giờ khớp với `If-Match`.
- `If-None-Match` dùng **weak** comparison, vì nó chủ yếu phục vụ cache (conditional `GET`, server
  trả `304 Not Modified` khi bản của client vẫn còn dùng được).

⚠️ Bẫy vận hành: RFC 9110 lưu ý bản nén (gzip) và bản không nén là hai representation khác nhau, nên
strong ETag của chúng phải khác nhau. Một số reverse proxy xử lý việc này bằng cách hạ strong ETag
thành weak khi tự nén response (Nginx làm vậy từ bản 1.7.3 khi module gzip nén response). Kết quả:
client nhận bản nén sẽ thấy `W/"v7"`, gửi lại trong `If-Match`, và **mọi** lần ghi của client đó đều
bị `412`. Nếu dùng ETag cho optimistic locking, kiểm tra ETag
mà client thực sự nhận được sau proxy, hoặc so sánh theo phần giá trị ở server nếu bạn chấp nhận.

Hai cách dùng khác của header điều kiện, theo RFC 9110:

- `If-None-Match: *` với `PUT`: "chỉ tạo nếu chưa có". Chống trường hợp hai client cùng tạo một resource
  tại cùng URI và người sau ghi đè người trước. Điều kiện sai thì `412`.
- Khi request có cả `If-Match` và `If-Unmodified-Since`, server đánh giá `If-Match` trước và bỏ qua
  `If-Unmodified-Since`, vì ETag được coi là chính xác hơn ngày.

#### Bulk: nhiều item trong một request

*Bulk* (hay *batch*) là xử lý nhiều item trong một request, ví dụ import 500 đơn hàng, thay vì 500
request riêng. Lý do là hiệu năng: giảm số round-trip và cho phép server ghi DB theo lô. Zalando phân
biệt: *batch* là tập các request kích hoạt các xử lý độc lập, *bulk* là tập các resource được tạo/sửa
cùng lúc; về cách xử lý response thì hai loại như nhau.

Google AIP-233 đặt tên và URL theo kiểu custom method (module 1.1):

```
POST /v1/publishers/123/books:batchCreate
{"requests": [{"book": {...}}, {"book": {...}}]}
```

Quyết định quan trọng nhất là ngữ nghĩa khi **một vài** item lỗi. Phải chọn và ghi vào tài liệu:

| | Atomic | Partial success |
|---|---|---|
| Ý nghĩa | Tất cả thành công, hoặc không item nào được ghi | Item nào ổn thì giữ, trả kết quả từng item |
| Cài đặt | Một transaction DB | Xử lý từng item, gom kết quả |
| Hợp với | Các item phụ thuộc nhau, thao tác là transaction DB đơn giản | Import dữ liệu, item độc lập, resource phức tạp |
| Client phải | Sửa item lỗi rồi gửi lại cả lô | Đọc kết quả từng item, chỉ gửi lại item lỗi |

AIP-233 gợi ý: thao tác chỉ là transaction DB đơn giản thì nên atomic; thao tác quản lý resource phức
tạp thì nên partial success; và cân nhắc từ góc người dùng: chấp nhận cả lô lớn thất bại vì một item
lỗi hay không.

Status code trả về gì: đây là chỗ các nguồn **không thống nhất**, nên cần biết cả hai quan điểm.

- Google AIP-233: batch **đồng bộ** bắt buộc atomic. Lý do: response `200` sẽ bị client hiểu là "tất
  cả đã tạo", nên không có cách sạch để báo lỗi một phần trong một response đồng bộ; thêm field báo
  lỗi một phần sau này là thay đổi phá client. Partial success chỉ dùng với batch **bất đồng bộ** (trả
  về operation, xem phần LRO dưới), với field `failed_requests` là một map từ **vị trí** của item trong
  request sang lỗi của item đó. Khi tất cả item đều lỗi thì operation báo lỗi tổng `ABORTED`.
- Zalando: batch/bulk **luôn** trả `207 Multi-Status`, trừ khi lỗi không gắn với item nào (quá tải, lỗi
  toàn dịch vụ) thì trả `4xx`/`5xx`. Zalando giữ `207` kể cả khi mọi item thành công, và cả khi mọi item
  thất bại, và cố ý **bác bỏ** việc trả `200` khi toàn bộ thành công, để client luôn phải đọc kết quả
  từng item. Body chứa một mảng item, mỗi item có `id`, `status`, và `description` tuỳ chọn.

Ví dụ response kiểu Zalando:

```json
{
  "items": [
    {"id": "row-1", "status": "created"},
    {"id": "row-2", "status": "failed", "description": "email: invalid_format"},
    {"id": "row-3", "status": "created"}
  ]
}
```

Một số quy tắc chung:

- Luôn giới hạn số item mỗi request (AIP-233 khuyên ghi con số tối đa vào tài liệu của field
  `requests`), ví dụ trong Laravel: `'items' => ['required', 'array', 'max:100']`.
- Kết quả từng item phải chỉ ra được item nào: dùng vị trí trong mảng (như AIP-233) hoặc một id do
  client gửi (như Zalando).
- Mỗi item nên có idempotency riêng hoặc toàn lô có một idempotency key (module 2.1), vì retry cả lô
  sau timeout là tình huống thường gặp.
- ⚠️ Lô lớn (hàng nghìn dòng, file Excel) không xử lý đồng bộ trong request. Chuyển sang long-running
  operation.

#### Long-running operation (LRO)

Một request HTTP bình thường không chịu được thao tác chạy vài phút. Ở PHP, request bị cắt bởi nhiều
lớp timeout: Nginx chờ PHP-FPM theo `fastcgi_read_timeout` (mặc định 60 giây), PHP-FPM và PHP có giới
hạn thời gian chạy riêng, load balancer phía trước cũng có timeout. Ngay cả khi không bị cắt, client
mobile giữ kết nối mười phút là điều không thực tế. AIP-151 đưa một quy tắc ước lượng: thao tác có thể
mất quá khoảng **10 giây** thì nên thiết kế thành LRO.

Ý tưởng: thay vì bắt client chờ, server trả ngay một "lời hứa" (AIP-151 so sánh với Promise của
Node.js hay Future của Python), tức một *operation resource* để client theo dõi tiến độ và lấy kết quả.

Luồng export báo cáo:

1. Client gọi `POST /reports:export` với tham số báo cáo.
2. Server validate. Lỗi làm thao tác **không bắt đầu được** (tham số sai, không có quyền) thì trả lỗi
   bình thường ngay (`400`, `403`...), không tạo operation.
3. Server tạo bản ghi operation trong DB (`status = running`), đẩy job vào queue, trả ngay:

   ```
   HTTP/1.1 202 Accepted
   Location: /operations/op_abc
   Retry-After: 5

   {"id": "op_abc", "status": "running", "progress": 0}
   ```

4. Worker xử lý job, cập nhật tiến độ vào bản ghi operation. Queue trong Laravel:
   [05-php-laravel.md, module 2.6](05-php-laravel.md#26-queue).
5. Client `GET /operations/op_abc` định kỳ (*poll*):

   ```json
   {"id": "op_abc", "status": "running", "progress": 40}
   {"id": "op_abc", "status": "succeeded", "result": {"download_url": "https://...", "expires_at": "2026-09-28T10:00:00Z"}}
   {"id": "op_abc", "status": "failed", "error": {"type": "https://api.example.com/errors/report-too-large", "title": "..."}}
   ```

6. Thay vì poll, client có thể đăng ký nhận webhook khi operation kết thúc (module 2.4).

Về `202`, RFC 9110 nói rõ đây là code "cố ý không cam kết": server đã nhận request nhưng chưa xử lý,
và có thể về sau còn từ chối. HTTP không có cách gửi lại status code khi xử lý bất đồng bộ xong, nên
RFC khuyên body của `202` mô tả trạng thái hiện tại và trỏ tới một *status monitor* (chính là
operation resource). Về `Retry-After`, mục định nghĩa header này trong RFC 9110 chỉ nêu ý nghĩa khi
đi với `503` và `3xx` (RFC còn nhắc tới nó ở `413`), không nói gì về `202`; dùng nó trong `202` để gợi
ý khoảng thời gian poll là một quy ước, cần ghi trong tài liệu API của bạn.

Các quy tắc từ AIP-151 đáng mang sang REST:

- Lỗi xảy ra **trong lúc chạy** không trả qua status code của lần poll (lần `GET` operation vẫn là
  `200`), mà nằm trong field `error` của operation, cùng format lỗi như mọi chỗ khác (module 1.3).
- Mọi LRO của API dùng **chung một** kiểu operation và một bộ endpoint `/operations`, không mỗi tính
  năng tự nghĩ một kiểu.
- Resource được tạo bằng LRO nên hiện ngay trong `GET`/`List`, kèm một trường trạng thái cho biết chưa
  dùng được (ví dụ `state: CREATING`).
- Nếu resource không cho hai operation chạy song song, request thứ hai bị từ chối với lỗi `ABORTED`
  (khi ánh xạ sang HTTP là `409`) kèm lời giải thích.
- Operation được phép hết hạn sau khi xong một thời gian; AIP gợi ý khoảng **30 ngày**.
- Đổi kiểu dữ liệu kết quả hay metadata của một LRO là thay đổi phá client.

⚠️ Operation phải lưu bền trong DB (hoặc kho dùng chung), không nằm trong memory hay file local của một
pod. Lần poll tiếp theo có thể rơi vào pod khác, và pod có thể bị restart bất cứ lúc nào. Với PHP-FPM thì
càng rõ: mỗi request là một tiến trình không chia sẻ bộ nhớ với request khác.

⚠️ Dọn dẹp: file kết quả export nên nằm trên object storage (S3...) và trả cho client một URL có chữ ký,
hết hạn sau một thời gian (*presigned URL*), thay vì stream qua PHP. Đặt vòng đời cho file (xoá sau N
ngày), và dọn bản ghi operation cũ bằng job định kỳ. Client gọi `POST /reports:export` lặp lại vì
retry nên được chống bằng idempotency key (module 2.1), nếu không sẽ sinh nhiều job export giống nhau.

#### Content negotiation

*Content negotiation* là việc client và server thoả thuận **dạng biểu diễn** (*representation*) của
cùng một resource qua header: định dạng, ngôn ngữ, kiểu nén.

| Header (gửi trong request) | Nghĩa | Server không đáp ứng được |
|---|---|---|
| `Accept: application/json` | Tôi muốn nhận định dạng này | `406 Not Acceptable` (hoặc trả dạng mặc định) |
| `Content-Type: application/json` | Body tôi gửi là định dạng này | `415 Unsupported Media Type` |
| `Accept-Language: vi, en;q=0.8` | Ưu tiên tiếng Việt, rồi tiếng Anh | Trả ngôn ngữ mặc định |
| `Accept-Encoding: gzip, br` | Tôi giải nén được gzip, brotli | Trả không nén |

Tham số `q` là trọng số ưu tiên từ 0 tới 1, mặc định 1.

Response thay đổi theo header nào của request thì phải khai header đó trong `Vary`. Ví dụ của RFC 9110:
cùng `GET /index`, bản nén gzip và bản không nén có ETag khác nhau (`"123-b"` và `"123-a"`), và cả hai
response đều kèm `Vary: Accept-Encoding`.

⚠️ Thiếu `Vary` thì cache dùng chung (CDN, reverse proxy) coi mọi request tới cùng URL là như nhau: user
đầu tiên gửi `Accept-Language: en` làm cache lưu bản tiếng Anh, và user tiếng Việt sau đó nhận bản tiếng
Anh. Tương tự với nội dung phụ thuộc người dùng: response khác nhau theo `Authorization` thì không được
để cache dùng chung lưu (dùng `Cache-Control: private` hoặc `no-store`).

⚠️ Bẫy Laravel hay gặp: client gọi API mà không gửi `Accept: application/json`. Khi validation lỗi,
Laravel coi đó là request từ trình duyệt và trả redirect `302` về trang trước thay vì JSON `422`, còn
exception thì render thành trang HTML. Cách phòng: client luôn gửi `Accept: application/json`, và phía
server cấu hình trong `bootstrap/app.php` để mọi route `api/*` luôn render lỗi dạng JSON
(`$exceptions->shouldRenderJsonWhen(...)`, xem tài liệu Laravel về exception).

**Tóm tắt nhanh**
- Lost update xảy ra giữa lúc đọc và lúc ghi của người dùng, không giải bằng transaction; dùng
  optimistic concurrency: `ETag` + `If-Match`, sai thì `412`, bắt buộc mà thiếu thì `428`.
- Điều kiện version nằm ngay trong `UPDATE ... WHERE version = ?`, xét số dòng bị ảnh hưởng.
- `If-Match` so sánh strong nên weak ETag (`W/`) không bao giờ khớp; coi chừng proxy gzip hạ ETag
  thành weak.
- Bulk phải chọn atomic hay partial success và giới hạn số item. AIP-233: batch đồng bộ phải atomic;
  Zalando: luôn `207` với kết quả từng item.
- Việc quá khoảng 10 giây: `202` + operation resource lưu bền trong DB, client poll hoặc nhận webhook;
  lỗi lúc chạy nằm trong field `error` của operation.
- Response phụ thuộc header nào thì khai trong `Vary`; API Laravel luôn cần `Accept: application/json`.

**Nguồn**: [RFC 9110 Section 13: Conditional Requests](https://www.rfc-editor.org/rfc/rfc9110#section-13) ·
[RFC 9110 Section 8.8.3: ETag](https://www.rfc-editor.org/rfc/rfc9110#section-8.8.3) ·
[RFC 9110 Section 15.3.3: 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110#section-15.3.3) ·
[RFC 6585](https://www.rfc-editor.org/rfc/rfc6585) (`428`) ·
[Google AIP-151: Long-running operations](https://google.aip.dev/151) ·
[Google AIP-233: Batch create](https://google.aip.dev/233) ·
[Zalando: HTTP status codes and errors](https://opensource.zalando.com/restful-api-guidelines/#http-status-codes-and-errors)

---

### 2.3 Rate limiting, auth và CORS

Module này trả lời: cửa vào của một API cần chặn những gì (quá nhiều request, client không xác
thực, request "hợp lệ" nhưng khổng lồ), và vì sao CORS là luật của trình duyệt chứ không phải hàng
rào bảo vệ server.

#### Rate limiting

*Rate limiting* là giới hạn lượng request một client được gửi trong một khoảng thời gian, ví dụ 60
request mỗi phút cho mỗi user. Mục đích không chỉ là chống tấn công: một client viết lỗi (vòng lặp
retry không có điểm dừng) cũng đủ làm quá tải DB, và rate limit là thứ cô lập client đó khỏi phần
còn lại.

Khi client vượt hạn mức, server trả `429 Too Many Requests`. Mã này được định nghĩa trong RFC 6585,
và RFC nói rõ nó không quy định server nhận diện client hay đếm request thế nào, việc đó tuỳ bạn.
Response 429 nên kèm `Retry-After`. Theo RFC 9110, `Retry-After` nhận một trong hai dạng: số giây
(`Retry-After: 30`) hoặc một mốc thời gian HTTP-date. Dạng số giây an toàn hơn vì không phụ thuộc
đồng hồ client có chạy đúng hay không.

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 30
Content-Type: application/problem+json

{"type": "https://api.shop.vn/problems/rate-limited", "title": "Too many requests", "status": 429}
```

*Header báo hạn mức cho client*. Có hai thế hệ:

| | Kiểu de-facto `X-RateLimit-*` | Draft IETF `RateLimit` / `RateLimit-Policy` |
|---|---|---|
| Trạng thái | Không phải chuẩn, nhưng GitHub, Laravel và rất nhiều API dùng | Internet-Draft của nhóm HTTPAPI (bản -11, 05/2026), chưa thành RFC |
| Hạn mức | `X-RateLimit-Limit: 60` | `RateLimit-Policy: "default";q=60;w=60` (q: quota, w: cửa sổ tính bằng giây) |
| Còn lại | `X-RateLimit-Remaining: 12` | `RateLimit: "default";r=12;t=35` (r: còn lại, t: số giây của cửa sổ hiệu lực) |
| Khi nào đặt lại | `X-RateLimit-Reset`, mỗi API hiểu một kiểu (unix timestamp hoặc số giây) | `t` luôn là số giây tương đối, không phụ thuộc đồng hồ |

Một vài ý đáng nhớ từ draft:

- `RateLimit-Policy` mô tả chính sách, ổn định giữa các response. `RateLimit` mô tả trạng thái hiện
  tại, có thể đổi sau mỗi request. Một response có thể mang nhiều policy cùng lúc, ví dụ
  `"permin";q=50;w=60,"perhr";q=1000;w=3600`.
- Draft chọn số giây tương đối (`t`) thay vì timestamp tuyệt đối có chủ đích: không phụ thuộc
  đồng bộ đồng hồ, và tránh việc rất nhiều client cùng được báo đúng một mốc rồi đổ về cùng lúc.
- Client không được coi `r > 0` là bảo đảm request sau sẽ được phục vụ. Server có quyền hạ hạn mức
  bất cứ lúc nào, ví dụ khi đang quá tải.
- Header này không quy định thuật toán đếm, cũng không phải cơ chế phân quyền.

Laravel (middleware `throttle`) dùng kiểu de-facto: mọi response có `X-RateLimit-Limit` và
`X-RateLimit-Remaining`; response 429 có thêm `Retry-After` (số giây) và `X-RateLimit-Reset` (unix
timestamp). Cách khai báo limiter, và hai cạm bẫy của nó (thuật toán fixed window cho lọt gấp đôi
ở ranh giới cửa sổ, bộ đếm nằm trong cache nên cache `file` trên nhiều server thì mỗi server đếm
riêng) đã viết ở [05: Session và rate limiting](05-php-laravel.md#27-các-thành-phần-khác-của-laravel).
Thuật toán đếm (token bucket, sliding window) thuộc [16-system-design](../16-system-design.md).

*Giới hạn theo gì* (draft gọi là *partition key*, khoá chia hạn mức):

| Khoá | Hợp với | Cạm bẫy |
|---|---|---|
| API key / client id | API public, tính theo gói dịch vụ | Một key bị lộ thì kẻ xấu ăn hết hạn mức của khách thật |
| User id | App có đăng nhập | Request chưa đăng nhập phải có khoá khác (IP) |
| IP | Endpoint công khai: login, quên mật khẩu | Cả công ty sau một NAT chung một IP; sau load balancer phải đọc đúng IP thật (trusted proxy), nếu không mọi request có cùng IP của load balancer |
| Endpoint | Endpoint đắt (export, gửi SMS) cần hạn mức riêng nhỏ hơn | |

Thực tế hay kết hợp: một trần chung theo user, cộng một hạn mức riêng rất nhỏ cho endpoint đắt.

⚠️ Phía client: khi nhận 429, phải chờ đúng `Retry-After` và cộng thêm *jitter* (một khoảng chờ
ngẫu nhiên nhỏ). Nếu một nghìn client cùng bị chặn và cùng chờ đúng 30 giây, cả nghìn client quay
lại trong cùng một giây, lại bị chặn tiếp. Hiện tượng này gọi là *thundering herd* (đàn trâu cùng
lao). Chi tiết backoff và jitter ở module 2.5.

#### Auth: xác thực client

*Authentication* (xác thực) trả lời "ai đang gọi". *Authorization* (phân quyền) trả lời "người đó
được làm gì". Module này chỉ bàn chỗ đặt thông tin xác thực ở tầng API; phân quyền và OWASP ở
[10-security](../10-security.md).

| Cách | Cơ chế | Hợp với | Điểm yếu |
|---|---|---|---|
| API key | Một chuỗi bí mật cố định, server tra trong DB | Server gọi server, tích hợp đối tác | Sống lâu; lộ là dùng được tới khi bị thu hồi. Nên lưu hash, cho phép rotate |
| OAuth2 access token | Chuẩn cấp token để một app hành động thay user, token ngắn hạn kèm phạm vi (*scope*) | App bên thứ ba đại diện cho user | Phức tạp, nhiều luồng; chi tiết ở 10-security |
| Token của chính hệ thống (Sanctum personal access token, JWT) | User đăng nhập, nhận token | Mobile app, SPA, script của user | Phải có cách thu hồi và hết hạn |
| mTLS | Cả client và server cùng trình chứng chỉ TLS khi bắt tay | Service nội bộ gọi nhau, đối tác ngân hàng | Vận hành chứng chỉ (cấp, gia hạn, thu hồi) tốn công |

Token đặt trong header `Authorization`, theo scheme Bearer:

```http
GET /orders/5 HTTP/1.1
Authorization: Bearer 7|lKq3...
```

⚠️ Không đặt token trong query string (`/orders?token=...`). URL đi vào nhiều chỗ mà header không
đi vào: access log của Nginx và load balancer, lịch sử trình duyệt, header `Referer` gửi sang trang
khác khi user bấm link. Chuẩn Bearer token (RFC 6750) cũng khuyên không dùng cách truyền qua URI.

Với Laravel, Sanctum có hai chế độ: SPA của chính bạn dùng session cookie (không có token trong
JavaScript), còn mobile/script dùng personal access token qua `Authorization: Bearer`. Luồng chi tiết
ở [05: Auth](05-php-laravel.md#27-các-thành-phần-khác-của-laravel). Điểm liên quan tới CORS: chế độ
SPA gửi cookie sang domain API, nên cần CORS với credentials (nhóm cuối module này).

#### Chống DoS ở tầng API

*DoS* (Denial of Service) là làm server quá tải để nó không phục vụ được ai. Rate limit đếm số
request, nhưng một request hợp lệ vẫn có thể đắt gấp nghìn lần request khác. OWASP API Security Top
10 (2023) xếp nhóm này là API4 *Unrestricted Resource Consumption*, và liệt kê các giới hạn một API
hay thiếu:

- Timeout thực thi, bộ nhớ tối đa, số process và file descriptor.
- Kích thước upload và kích thước body tối đa.
- Số thao tác trong một request (batch, GraphQL batching).
- Số bản ghi mỗi trang: `per_page=1000000` là DoS miễn phí nếu không có trần.
- Hạn mức chi tiêu với dịch vụ trả tiền theo lượt. Ví dụ trong OWASP: endpoint "quên mật khẩu" gửi
  SMS qua bên thứ ba, kẻ tấn công gọi hàng chục nghìn lần, công ty mất tiền SMS trong vài phút.

Cần thêm độ sâu lồng nhau của JSON: payload lồng hàng nghìn tầng làm parser tốn stack. Trong PHP,
`json_decode($body, true, 32, JSON_THROW_ON_ERROR)` đặt độ sâu tối đa 32 (tham số `depth`) và ném
`JsonException` khi vượt.

Ở Laravel, các giới hạn này đặt ở nhiều tầng: `client_max_body_size` của Nginx và `post_max_size` của
PHP cho kích thước body; rule validation `max:` cho số item trong mảng (`'items' => ['array',
'max:100']`); trần cứng cho `per_page` trong code.

Những mục khác của OWASP API Top 10 2023 hay gặp trong thiết kế API (chi tiết ở 10-security): API1
BOLA (lấy được object của người khác chỉ bằng cách đổi id), API3 Broken Object Property Level
Authorization (gộp "trả thừa field" và mass assignment), API7 SSRF (gặp lại ở module 2.4), API10
Unsafe Consumption of APIs (tin dữ liệu của bên thứ ba hơn dữ liệu của user, gặp lại ở 2.5).

#### CORS: là gì và không là gì

*Origin* là bộ ba scheme + host + port. `https://app.shop.vn` và `https://api.shop.vn` là hai origin
khác nhau (khác host); `http://localhost:5173` và `http://localhost:8000` cũng khác nhau (khác
port).

*Same-origin policy* là luật của trình duyệt: JavaScript chạy trên trang thuộc origin A, khi dùng
`fetch()` hoặc `XMLHttpRequest` gọi sang origin B, thì không được đọc response trừ khi B cho phép.
Luật này bảo vệ user: nếu không có nó, một trang độc mà user lỡ mở có thể dùng cookie đăng nhập
của user để gọi API ngân hàng và đọc số dư.

*CORS* (Cross-Origin Resource Sharing) là cơ chế để server B nói với trình duyệt "tôi cho phép
origin A đọc response của tôi", thông qua các header `Access-Control-*`. CORS **nới lỏng** same-origin
policy, không thêm lớp bảo vệ nào.

```
 Trình duyệt (trang app.shop.vn)                  api.shop.vn
 ────────────────────────────────                 ───────────
 fetch("https://api.shop.vn/me") ──── request ──▶ xử lý, trả 200
                                 ◀─── response ── (có hoặc không có Access-Control-Allow-Origin)
 Trình duyệt kiểm tra header:
   có và khớp origin  -> đưa response cho JS
   không có           -> JS nhận một TypeError chung chung, response bị giấu
```

⚠️ Ba hệ quả hay bị hiểu nhầm:

1. CORS không bảo vệ server. `curl`, Postman, một server khác gọi thẳng API đều không bị chặn, vì
   chúng không phải trình duyệt và không thực thi same-origin policy. Muốn bảo vệ API thì dùng
   auth, không dùng CORS.
2. Với simple request (nhóm tiếp theo), request **đã tới server và đã được xử lý**; trình duyệt chỉ
   giấu response khỏi JS. Nghĩa là một `POST` dạng form từ trang lạ vẫn có thể gây tác dụng phụ; đó
   là bài toán CSRF, chống bằng CSRF token hoặc cookie `SameSite`, không phải bằng CORS.
3. Lỗi CORS không có chi tiết cho JavaScript. MDN ghi rõ: vì lý do bảo mật, code chỉ biết "có lỗi",
   muốn biết lỗi gì phải mở console của trình duyệt. Log server thường thấy request trả 200 bình
   thường, vì chính trình duyệt mới là bên chặn.

#### Simple request và preflight

Trình duyệt chia request cross-origin thành hai loại.

*Simple request* (tên gọi từ spec CORS cũ; spec Fetch hiện hành không dùng tên này): thoả **tất cả**
điều kiện sau:

- Method là `GET`, `HEAD` hoặc `POST`.
- Chỉ đặt các header "an toàn" (*CORS-safelisted*): `Accept`, `Accept-Language`, `Content-Language`,
  `Content-Type`, `Range` (một khoảng).
- `Content-Type` (nếu có) chỉ là `application/x-www-form-urlencoded`, `multipart/form-data` hoặc
  `text/plain`.

Lý do có ngoại lệ này: thẻ `<form>` của HTML từ xưa đã gửi được đúng những request như vậy sang bất
kỳ origin nào, nên server vốn đã phải tự chống CSRF cho chúng. Cho `fetch()` gửi thẳng không làm
tình hình tệ hơn.

Mọi request khác phải qua *preflight*: trình duyệt tự gửi trước một request `OPTIONS` để hỏi xin
phép. Trong API JSON hiện đại, gần như mọi request đều dính preflight vì ít nhất một lý do:

- Method `PUT`, `PATCH`, `DELETE`.
- `Content-Type: application/json` (không nằm trong ba kiểu kể trên).
- Có header không thuộc danh sách an toàn: `Authorization`, `Idempotency-Key`, `X-Request-Id`.

Luồng preflight cho `PUT /orders/5` từ `https://app.shop.vn`:

```http
# 1. Trình duyệt tự gửi (JS không điều khiển được request này, và nó KHÔNG mang cookie/token)
OPTIONS /orders/5 HTTP/1.1
Host: api.shop.vn
Origin: https://app.shop.vn
Access-Control-Request-Method: PUT
Access-Control-Request-Headers: authorization,content-type

# 2. Server trả lời (thường là 204, không có body)
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.shop.vn
Access-Control-Allow-Methods: GET, PUT, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 600
Vary: Origin

# 3. Trình duyệt thấy PUT và hai header đều được phép, mới gửi request thật
PUT /orders/5 HTTP/1.1
Origin: https://app.shop.vn
Authorization: Bearer ...
Content-Type: application/json

# 4. Response của request thật CŨNG phải có Access-Control-Allow-Origin, nếu không JS vẫn không đọc được
```

Nếu preflight không được phép, request thật **không bao giờ được gửi**. Đây là lời giải của câu
"GET chạy mà PUT lỗi CORS": `GET` không header lạ là simple request, chỉ cần response có
`Access-Control-Allow-Origin`; còn `PUT` cần server trả lời đúng cả request `OPTIONS`, mà nhiều
server không xử lý `OPTIONS` (trả 404, 405, hoặc 401).

#### Các header CORS

Header của request (trình duyệt tự đặt, JS không cần và không thể tự đặt):

| Header | Ý nghĩa |
|---|---|
| `Origin` | Origin của trang gọi. Có thể mang giá trị `null` (trang mở từ file, iframe sandbox, một số redirect) |
| `Access-Control-Request-Method` | Chỉ có trong preflight: method của request thật |
| `Access-Control-Request-Headers` | Chỉ có trong preflight: các header của request thật |

Header của response (server đặt):

| Header | Ý nghĩa | Ghi chú |
|---|---|---|
| `Access-Control-Allow-Origin` | Một origin cụ thể, hoặc `*` | Chỉ được một giá trị; muốn cho nhiều origin thì so whitelist rồi trả lại đúng origin khớp |
| `Access-Control-Allow-Methods` | Method được phép | Trả trong preflight |
| `Access-Control-Allow-Headers` | Header được phép | Trả trong preflight |
| `Access-Control-Allow-Credentials: true` | Cho phép request mang credentials (cookie, HTTP auth) và cho JS đọc response đó | Mặc định `fetch()` cross-origin không gửi cookie; client phải đặt `credentials: "include"` (Axios: `withCredentials: true`) |
| `Access-Control-Max-Age` | Số giây trình duyệt được nhớ kết quả preflight | Mặc định 5 giây nếu không gửi. Trình duyệt có trần riêng: Chromium từ bản 76 là 2 giờ, Firefox là 24 giờ |
| `Access-Control-Expose-Headers` | Header nào JS được đọc | Mặc định JS chỉ đọc được nhóm an toàn: `Cache-Control`, `Content-Language`, `Content-Length`, `Content-Type`, `Expires`, `Last-Modified`, `Pragma` |

⚠️ Hệ quả của dòng cuối: frontend gọi `response.headers.get("X-RateLimit-Remaining")` nhận `null`
dù trong tab Network thấy rõ header đó. Phải thêm
`Access-Control-Expose-Headers: X-RateLimit-Remaining, Retry-After`. Tương tự với `Location` sau
khi tạo resource, hay `Link` của pagination.

#### Tái hiện và sửa lỗi CORS chỉ với PHP

Hai server PHP built-in trên hai port là hai origin khác nhau, đủ để tái hiện. Tạo thư mục
`cors-demo/` với hai file:

```php
<?php
// cors-demo/api.php : chạy bằng  php -S localhost:8000 api.php
declare(strict_types=1);

/** @var list<string> $allowedOrigins whitelist, so sánh chính xác từng chuỗi */
$allowedOrigins = ['http://localhost:5173'];
$origin = $_SERVER['HTTP_ORIGIN'] ?? '';

header('Vary: Origin'); // response thay đổi theo Origin, báo cho cache biết

if (in_array($origin, $allowedOrigins, true)) {
    header('Access-Control-Allow-Origin: ' . $origin);
}

// BƯỚC SỬA: xoá khối if này để tái hiện lỗi "GET chạy mà PUT lỗi CORS"
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, PUT');
    header('Access-Control-Allow-Headers: Content-Type, Authorization');
    header('Access-Control-Max-Age: 600');
    http_response_code(204);
    exit;
}

header('Content-Type: application/json');
echo json_encode(['method' => $_SERVER['REQUEST_METHOD']], JSON_THROW_ON_ERROR);
```

```html
<!-- cors-demo/index.html : chạy bằng  php -S localhost:5173  rồi mở http://localhost:5173 -->
<script>
  const api = "http://localhost:8000/";
  fetch(api).then(r => r.json()).then(d => console.log("GET ok", d));
  fetch(api, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: "paid" }),
  }).then(r => r.json()).then(d => console.log("PUT ok", d))
    .catch(e => console.log("PUT lỗi", e));
</script>
```

Chạy hai server ở hai terminal, mở `http://localhost:5173`, xem console:

1. Bản đầy đủ: cả hai dòng `GET ok` và `PUT ok`.
2. Xoá khối `if (... === 'OPTIONS')`: `GET` vẫn chạy; `PUT` báo lỗi CORS vì preflight nhận response
   không có `Access-Control-Allow-Methods`, và terminal của server 8000 chỉ thấy request `OPTIONS`,
   không thấy `PUT` nào.
3. Đổi whitelist thành `http://127.0.0.1:5173` rồi vẫn mở bằng `localhost`: cả `GET` cũng lỗi.
   `localhost` và `127.0.0.1` là hai origin khác nhau với trình duyệt.

Trong Laravel, bạn không tự viết đoạn trên. Middleware `HandleCors` nằm sẵn trong global middleware
stack, đọc `config/cors.php` (publish bằng `php artisan config:publish cors`). Giá trị mặc định của
framework:

```php
'paths' => ['api/*', 'sanctum/csrf-cookie'],
'allowed_methods' => ['*'],
'allowed_origins' => ['*'],
'allowed_origins_patterns' => [],
'allowed_headers' => ['*'],
'exposed_headers' => [],
'max_age' => 0,
'supports_credentials' => false,
```

Theo mã nguồn `HandleCors`: nếu path của request khớp `paths` và đó là preflight, middleware trả
response ngay, không đi tiếp vào route hay middleware `auth`. Nếu path không khớp, middleware bỏ qua
hoàn toàn, không thêm header nào. ⚠️ Route API đặt ngoài `api/*` (ví dụ prefix `v1/*`) sẽ lỗi CORS
cho tới khi thêm path đó vào `paths`.

#### Cạm bẫy CORS

- ⚠️ `Access-Control-Allow-Origin: *` không đi cùng credentials được. Với request mang cookie,
  trình duyệt chặn response nếu thấy `*`. Quy tắc này áp cho cả `Allow-Headers`, `Allow-Methods`,
  `Expose-Headers`: khi có credentials, `*` bị coi là chuỗi `*` theo nghĩa đen chứ không phải ký tự
  đại diện, nên phải liệt kê cụ thể.
- ⚠️ Phản chiếu nguyên `Origin` của request vào `Allow-Origin` kèm `Allow-Credentials: true` là **lỗ
  hổng thật**. Kịch bản: user đang đăng nhập `shop.vn`, lỡ mở `evil.com`. JS trên `evil.com` gọi
  `fetch("https://api.shop.vn/me", {credentials: "include"})`; trình duyệt gửi kèm cookie của user;
  server phản chiếu `Access-Control-Allow-Origin: https://evil.com` và cho credentials; trình duyệt
  thấy khớp nên đưa response (thông tin cá nhân của user) cho JS của `evil.com`. Cách đúng: so
  `Origin` với whitelist bằng so sánh chuỗi chính xác. Regex lỏng như "kết thúc bằng `shop.vn`" cho
  lọt `evilshop.vn`. Không đưa `null` vào whitelist.
- ⚠️ Bẫy riêng của Laravel: trong `config/cors.php`, để `allowed_origins => ['*']` rồi bật
  `supports_credentials => true`. Theo mã nguồn thư viện `fruitcake/php-cors` mà `HandleCors` dùng,
  khi cho mọi origin mà có credentials, nó không trả `*` (vì trình duyệt sẽ từ chối) mà trả lại
  đúng `Origin` của request. Tức là cấu hình này chính là lỗ hổng phản chiếu ở trên. Bật credentials
  thì phải liệt kê origin cụ thể.
- Khi `Allow-Origin` thay đổi theo request, phải có `Vary: Origin`. Nếu không, CDN hoặc cache trung
  gian có thể lưu response mang `Allow-Origin: https://a.shop.vn` rồi trả cho request từ
  `https://b.shop.vn`, khiến `b` lỗi CORS một cách "ngẫu nhiên".
- ⚠️ Preflight bị `401`: middleware auth chặn cả `OPTIONS`, trong khi preflight không bao giờ mang
  cookie hay token. Sửa: xử lý CORS ở tầng trước auth (Laravel đã làm vậy với path trong `paths`),
  hoặc cho `OPTIONS` đi qua auth. Tương tự với API gateway hay Nginx có kiểm tra auth riêng.
- Cấu hình CORS ở hai nơi (Nginx thêm header, Laravel cũng thêm) sinh ra hai header
  `Access-Control-Allow-Origin`, và trình duyệt từ chối vì chỉ được một giá trị. Chọn một tầng duy
  nhất lo CORS.
- Vì sao cấu hình CORS "chặt quá" không phải lỗ hổng phía server: nó chỉ làm frontend hợp lệ không
  đọc được response, server không lộ gì. Cấu hình "lỏng" chỉ nguy hiểm khi kèm credentials, vì khi
  đó trình duyệt của nạn nhân trở thành công cụ đọc dữ liệu của chính nạn nhân. API không dùng
  cookie (chỉ Bearer token do JS tự gắn) mà để `*` thì trang lạ cũng không có token để gắn vào.

**Tóm tắt nhanh**
- Vượt hạn mức trả `429` kèm `Retry-After` (ưu tiên dạng số giây). Header báo hạn mức: kiểu
  `X-RateLimit-*` là de-facto; `RateLimit`/`RateLimit-Policy` của IETF vẫn là draft. Client chờ
  `Retry-After` cộng jitter.
- Token đi trong header `Authorization: Bearer`, không bao giờ trong query string. Rate limit đếm
  request, còn DoS bằng request "to" phải chặn bằng giới hạn body, số item, `per_page`, độ sâu JSON.
- CORS là luật của trình duyệt để nới same-origin policy; không bảo vệ server khỏi `curl`, và simple
  request vẫn tới server.
- API JSON gần như luôn dính preflight (`application/json`, `Authorization`, `PUT`/`DELETE`);
  preflight không mang credentials nên không được đi qua auth.
- `*` không đi với credentials; phản chiếu `Origin` kèm credentials là lỗ hổng (Laravel:
  `allowed_origins ['*']` + `supports_credentials true` chính là cấu hình đó). Nhớ `Vary: Origin`
  và `Access-Control-Expose-Headers`.

**Nguồn**: [draft-ietf-httpapi-ratelimit-headers](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/) ·
[RFC 6585 (429)](https://www.rfc-editor.org/rfc/rfc6585) ·
[RFC 9110: Retry-After](https://www.rfc-editor.org/rfc/rfc9110#field.retry-after) ·
[MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS) ·
[MDN: Access-Control-Max-Age](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Access-Control-Max-Age) ·
[OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) ·
[Laravel: CORS](https://laravel.com/docs/routing#cors) ·
[fruitcake/php-cors: CorsService](https://github.com/fruitcake/php-cors/blob/master/src/CorsService.php)

---

### 2.4 Webhook

Module này trả lời: khi hệ thống của bạn gửi hoặc nhận một thông báo "có chuyện vừa xảy ra" qua
HTTP, làm sao để không mất event, không xử lý trùng, không tin một request giả mạo, và không biến
tính năng webhook thành cửa hậu vào mạng nội bộ.

#### Webhook là gì

*Webhook* là khi hệ thống A chủ động gọi HTTP (gần như luôn là `POST` với body JSON) tới một URL do
hệ thống B đăng ký, để báo một sự kiện vừa xảy ra. Thay vì B phải hỏi A liên tục ("đơn đã trả tiền
chưa?", gọi là *polling*), A báo khi có chuyện.

```
 Cổng thanh toán (bên gửi, producer)                 Shop (bên nhận, consumer)
 ───────────────────────────────────                 ─────────────────────────
 khách trả tiền xong
   ghi event "order.paid" ──── POST /webhooks/payment ───▶ verify chữ ký
                                                          lưu event, đẩy queue
                           ◀────────── 200 ────────────── (trả ngay, chưa xử lý)
 không nhận được 2xx?
   chờ, gửi lại (retry)                                   worker xử lý: đánh dấu đơn đã trả
```

Hai tính chất quyết định mọi thiết kế phía sau:

- *At-least-once*: mỗi event được giao **ít nhất một lần**, có thể nhiều lần. Bên gửi không thể
  biết chắc bên nhận đã xử lý chưa (bên nhận xử lý xong nhưng response bị mất trên đường về thì bên
  gửi vẫn thấy là lỗi và gửi lại). Stripe ghi rõ endpoint "có thể thỉnh thoảng nhận cùng một event
  nhiều lần", và đôi khi còn sinh hai event object khác nhau cho cùng một thay đổi.
- Không đảm bảo thứ tự: Stripe nói thẳng không bảo đảm giao event theo thứ tự sinh ra.

*Standard Webhooks* là một bộ quy ước mở (không phải RFC) gom thực hành tốt của nhiều nhà cung cấp:
tên header, cách ký, lịch retry. Khi phải tự thiết kế webhook cho đối tác, bám theo nó là lựa chọn
an toàn nhất vì đối tác có sẵn thư viện verify.

#### Bên gửi: lưu và gửi

Luồng đúng dùng *outbox pattern* (chi tiết ở [12-messaging](../12-messaging.md)):

1. Trong **cùng transaction** với thay đổi nghiệp vụ (đơn chuyển sang `paid`), ghi một dòng vào bảng
   `webhook_events` (outbox).
2. Commit. Từ đây event chắc chắn tồn tại, và chỉ tồn tại nếu nghiệp vụ thành công.
3. Worker đọc outbox, với mỗi endpoint đã đăng ký nhận loại event đó thì tạo một lần giao
   (*delivery*) và gửi HTTP.
4. Ghi kết quả từng lần thử: status code, thời gian, lỗi. Đây là dữ liệu để đối tác tự tra ("tôi
   không nhận được webhook") và để replay.

⚠️ Vì sao không gọi HTTP ngay trong transaction nghiệp vụ:

- Bên nhận chậm 20 giây thì transaction giữ lock DB 20 giây.
- Gửi xong rồi transaction rollback thì không thu hồi được webhook: đối tác đã nhận `order.paid`
  cho một đơn không hề được trả.
- Gọi HTTP **sau** commit nhưng vẫn trong request thì process chết giữa chừng là mất event vĩnh
  viễn. Outbox giải cả ba.

*Payload*. Standard Webhooks khuyên body JSON gồm `type` (phân cấp bằng dấu chấm, như
`order.paid`), `timestamp` (lúc sự kiện xảy ra, ISO 8601) và `data`. Mã định danh event đi ở header
`webhook-id` (xem nhóm ký request). Có hai kiểu nội dung:

| | *Full payload* | *Thin payload* |
|---|---|---|
| Chứa gì | Toàn bộ trạng thái object lúc sự kiện xảy ra | Chỉ id (và có thể vài field hay dùng) |
| Bên nhận | Dùng ngay, không cần gọi thêm | Phải gọi API để lấy bản mới nhất |
| Ưu điểm | Đơn giản cho bên nhận | Bên nhận lấy bản mới nhất lúc xử lý, không dùng dữ liệu cũ trong payload; payload nhỏ; truy cập dữ liệu qua API nên kiểm soát và audit được; từ thin chuyển sang full thì dễ, ngược lại thì phá client |
| Nhược | Event đến trễ hoặc sai thứ tự mang dữ liệu đã cũ; dữ liệu nhạy cảm đi tới mọi endpoint | Thêm một lời gọi API mỗi event |

Stripe có cả hai loại: *snapshot event* (full, dùng cho API v1) và *thin event* (API v2, SDK có hàm
lấy object liên quan). Standard Webhooks khuyên giữ payload nhỏ, thường dưới 20 KB; dữ liệu lớn thì
gửi link.

```json
{
  "type": "order.paid",
  "timestamp": "2026-09-27T10:15:30Z",
  "data": { "id": "ord_8f2a", "amount": 250000, "currency": "VND", "version": 7 }
}
```

*Timeout mỗi lần gửi*: phải có, để một endpoint chậm không giữ worker mãi. Standard Webhooks gợi ý
15 đến 30 giây, đủ để bên nhận verify và lưu. Cách làm tốt hơn là nhiều worker và hàng đợi riêng
theo endpoint, để một đối tác chậm không làm trễ webhook của mọi đối tác khác.

#### Bên gửi: retry

Giao thành công là nhận `2xx`; mọi thứ khác là thất bại: status khác, timeout, kết nối bị ngắt, lỗi
TLS. Standard Webhooks gợi ý cách xử lý theo status:

| Response | Bên gửi nên làm |
|---|---|
| `2xx` | Thành công |
| `3xx` | Coi là thất bại, không đi theo redirect (bắt đối tác cập nhật URL) |
| `410 Gone` | Bên nhận nói "không muốn nhận nữa": tắt endpoint |
| `429`, `502`, `504` | Bên nhận quá tải: giảm tốc độ gửi; có `Retry-After` thì tôn trọng |
| Còn lại | Thất bại, retry theo lịch |

Lịch retry: *exponential backoff* (khoảng chờ tăng dần theo cấp số nhân) cộng *jitter* (một lượng
ngẫu nhiên), trải dài nhiều ngày. Jitter quan trọng ở đây vì nếu thất bại là do chính đợt webhook
dồn dập gây quá tải, retry đồng loạt sẽ tái tạo đúng đợt quá tải đó. Lịch ví dụ của Standard
Webhooks: ngay lập tức, rồi sau 5 giây, 5 phút, 30 phút, 2 giờ, 5 giờ, 10 giờ, 14 giờ, 20 giờ, 24
giờ (tổng khoảng 75 giờ). Stripe ở live mode retry tới ba ngày với exponential backoff; ở sandbox
chỉ retry ba lần trong vài giờ (một lý do test ở sandbox không phản ánh production).

Sau khi hết lịch retry:

- Đánh dấu delivery là thất bại, hiện trong dashboard cho đối tác xem lý do.
- Cho phép *replay* thủ công từng event hoặc cả một khoảng thời gian (Stripe: nút Resend trong
  dashboard trong 15 ngày, CLI trong 30 ngày). Đây là cách đối tác tự phục hồi sau một đợt sập dài.
- Endpoint lỗi liên tục trong thời gian dài: báo đối tác qua kênh khác (email) và tắt endpoint.

Trong Laravel, một job gửi webhook có thể dựa vào retry của queue:

```php
<?php
declare(strict_types=1);

namespace App\Jobs;

use App\Models\WebhookDelivery;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Queue\Queueable;
use Illuminate\Support\Facades\Http;

final class SendWebhook implements ShouldQueue
{
    use Queueable;

    public int $tries = 10;

    public function __construct(public int $deliveryId) {}

    /** @return list<int> số giây chờ trước mỗi lần thử lại; hết mảng thì dùng lại phần tử cuối */
    public function backoff(): array
    {
        return [5, 300, 1800, 7200, 18000, 36000, 50400, 72000, 86400];
    }

    public function handle(WebhookSigner $signer): void
    {
        $d = WebhookDelivery::with('endpoint', 'event')->findOrFail($this->deliveryId);
        $body = $d->event->payload_json;             // chuỗi JSON đã lưu, ký và gửi đúng chuỗi này
        $ts = time();                                 // timestamp của LẦN GỬI, mỗi lần retry ký lại

        Http::timeout(15)
            ->connectTimeout(5)
            ->withoutRedirecting()                    // 3xx là thất bại, và chặn redirect vào mạng nội bộ
            ->withHeaders([
                'webhook-id' => $d->event->public_id, // giữ nguyên qua mọi lần retry
                'webhook-timestamp' => (string) $ts,
                'webhook-signature' => $signer->sign($d->endpoint->secrets, $d->event->public_id, $ts, $body),
            ])
            ->withBody($body, 'application/json')
            ->post($d->endpoint->url)
            ->throw();                                // không phải 2xx thì ném exception, queue sẽ retry
    }
}
```

Đoạn trên là khung minh hoạ (model, `WebhookSigner` là của bạn tự viết; jitter và việc kiểm tra IP
đích chưa có). Hệ thống lớn thường tự quản lý lịch retry trong bảng `webhook_deliveries` (cột
`next_attempt_at`) thay vì giữ job chờ nhiều ngày trong queue.

#### Bên gửi: ký request

Endpoint nhận webhook là một URL công khai; ai biết URL cũng `POST` được. Bên nhận cần chứng minh
request thật sự đến từ bạn và không bị sửa. Cách phổ biến nhất là *HMAC* (Hash-based Message
Authentication Code): một mã tính từ nội dung và một secret mà chỉ hai bên biết. Không có secret thì
không tạo được mã đúng; sửa một byte nội dung thì mã sai.

Scheme của Standard Webhooks:

1. Chuỗi được ký: `webhook-id` + `.` + `webhook-timestamp` + `.` + raw body. Ký cả id và timestamp
   (không chỉ body), để kẻ tấn công không lấy chữ ký cũ gắn vào id hay timestamp mới được.
2. Thuật toán: HMAC-SHA256. Secret là 24 đến 64 byte ngẫu nhiên, trình bày cho khách dạng base64 với
   tiền tố `whsec_`; khoá HMAC là phần byte sau khi bỏ tiền tố và giải base64.
3. Gửi ba header:

```http
POST /webhooks/payment HTTP/1.1
Content-Type: application/json
webhook-id: msg_2KWPBgLlAfxdpx2AI54pPJ85f4W
webhook-timestamp: 1674087231
webhook-signature: v1,K5oZfzN95Z9UVu1EsfQmfVNQhnkZ2pj9o9NDN/H/pI4=
```

   `v1,` đánh dấu chữ ký đối xứng (HMAC), theo sau là chữ ký base64. `webhook-timestamp` là unix
   timestamp tính bằng giây của **lần gửi** (khác với `timestamp` của sự kiện trong body: retry thì
   timestamp lần gửi đổi, còn `webhook-id` giữ nguyên).
4. Mỗi endpoint một secret riêng. Dùng chung secret cho nhiều khách thì một khách có thể giả webhook
   gửi cho khách khác.

*Rotate secret không downtime*: `webhook-signature` là danh sách chữ ký cách nhau bởi dấu cách.
Trong thời gian chuyển đổi, bên gửi ký bằng cả secret cũ và mới, gửi cả hai chữ ký; bên nhận thử
từng chữ ký, khớp một cái là được. Stripe làm tương tự: khi "roll secret" có thể giữ secret cũ hiệu
lực thêm tối đa 24 giờ, và trong thời gian đó sinh một chữ ký cho mỗi secret.

Standard Webhooks còn cho phép chữ ký bất đối xứng (ed25519, tiền tố `v1a,`): chỉ bên gửi giữ private
key, bên nhận verify bằng public key, nên lộ phía bên nhận không cho phép giả chữ ký. Spec khuyên
ưu tiên bất đối xứng, đổi lại tốn CPU hơn.

Đối chiếu Stripe (định dạng riêng, cùng ý tưởng): header `Stripe-Signature: t=1492774577,v1=<hex>`;
chuỗi được ký là `timestamp.body` (không có id); chữ ký dạng hex; chỉ tin scheme `v1` và bỏ qua
scheme khác để chống *downgrade attack* (ép dùng scheme yếu hơn).

#### Bên gửi: cạm bẫy

⚠️ Thứ tự không được đảm bảo. Retry của event cũ có thể đến sau event mới; hai worker gửi song song
cũng đảo thứ tự. Ví dụ `order.updated` (version 7) đến trước `order.created` (version 6). Cách làm:

- Bên gửi kèm `version` (số tăng dần mỗi lần object đổi) hoặc `updated_at` của object.
- Bên nhận chỉ áp dụng khi version mới hơn bản đang có (`UPDATE ... WHERE version < ?`).
- Hoặc dùng thin event: nhận event nào cũng gọi API lấy bản mới nhất, thứ tự không còn quan trọng.
- ⚠️ Stripe lưu ý `created` của event tính bằng giây, nhiều event có thể trùng timestamp, nên không
  dùng nó để xác định thứ tự hay để phát hiện trùng; dùng event id.

⚠️ *SSRF* (Server-Side Request Forgery): URL webhook do khách tự nhập, và server của bạn sẽ gọi URL
đó từ bên trong mạng. Kẻ xấu nhập `http://169.254.169.254/latest/meta-data/` (địa chỉ metadata của
cloud, có thể trả credential), `http://10.0.0.5:9200/` (Elasticsearch nội bộ) hay
`http://localhost:6379`. OWASP xếp SSRF là API7:2023. Cách chặn:

1. Chỉ cho `https://` (Stripe bắt buộc HTTPS và TLS 1.2 trở lên ở live mode).
2. Resolve DNS và chặn IP private, loopback, link-local (gồm `169.254.169.254`), ở **lúc gửi**, không
   chỉ lúc đăng ký: tên miền có thể trỏ sang IP công khai lúc đăng ký rồi đổi sang IP nội bộ sau đó
   (*DNS rebinding*).
3. Không đi theo redirect: một URL công khai có thể redirect `302` về địa chỉ nội bộ.
4. Tầng mạng: Standard Webhooks khuyên cho mọi request webhook đi qua một proxy lọc IP nội bộ (ví dụ
   `smokescreen` của Stripe), và đặt worker gửi webhook trong subnet riêng không với tới service
   nội bộ. Tầng mạng chặn được cả những gì code bỏ sót.

Một số đối tác doanh nghiệp đặt firewall chỉ nhận request từ danh sách IP cố định; công bố dải IP
gửi đi (Stripe có trang danh sách IP) là tính năng nên có.

#### Bên nhận

Thứ tự các bước trong endpoint nhận:

1. **Verify chữ ký trên raw body**, tức đúng chuỗi byte nhận được, trước khi làm bất cứ gì khác.
   - ⚠️ Parse JSON rồi serialize lại để verify là lỗi rất phổ biến (Standard Webhooks và Stripe đều
     cảnh báo). Chữ ký nhạy với từng byte; encode lại có thể đổi khoảng trắng, thứ tự key, cách
     escape. Ví dụ `json_encode` của PHP mặc định escape `/` thành `\/` và ký tự không phải ASCII
     thành `\uXXXX`, nên "cùng một JSON" ra chuỗi khác.
   - Laravel: `$request->getContent()` trả raw body. Không dùng `$request->all()` hay `json()` để
     dựng lại chuỗi ký.
2. **So sánh chữ ký bằng hàm constant-time**: thời gian so sánh không phụ thuộc vào vị trí ký tự sai
   đầu tiên. So sánh thường (`===`) dừng ngay ở byte khác đầu tiên; kẻ tấn công đo thời gian phản hồi
   qua rất nhiều lần thử để đoán dần từng byte của chữ ký đúng (*timing attack*). Standard Webhooks
   nói so sánh thường biến bên nhận thành "signing oracle" (cỗ máy giúp kẻ tấn công dò chữ ký).
   - PHP: `hash_equals($expected, $received)` (chuỗi biết trước đặt trước).
   - Go: `hmac.Equal(a, b)`.
   - Java: `MessageDigest.isEqual(a, b)`.
3. **Từ chối timestamp lệch quá xa** giờ hiện tại, để chống *replay attack* (kẻ bắt được một request
   hợp lệ gửi lại y nguyên sau này). Vì timestamp nằm trong chuỗi ký, kẻ tấn công không sửa được nó.
   Thư viện của Stripe mặc định cho lệch 5 phút; Stripe cảnh báo đặt tolerance bằng `0` là tắt hẳn
   kiểm tra. Server phải đồng bộ giờ bằng NTP.
4. **Idempotent theo event id**: unique constraint trên `event_id`; insert trùng thì coi là đã nhận
   và trả `2xx`. Timestamp chỉ chặn replay cũ; trong cửa sổ 5 phút, và với retry hợp lệ của bên gửi,
   chỉ id mới chặn được xử lý trùng.
5. **Trả `2xx` nhanh**: chỉ verify, lưu event, đẩy queue, trả. Stripe yêu cầu trả `2xx` trước mọi
   logic phức tạp có thể gây timeout. Xử lý lâu trong request thì bên gửi timeout, coi là thất bại
   và gửi lại, sinh thêm bản trùng; đầu tháng khi mọi subscription gia hạn, lượng webhook dồn dập
   sẽ đè sập endpoint xử lý đồng bộ.

Chỉ đăng ký những loại event cần dùng (Stripe khuyên vậy): nhận "tất cả" là tự thêm tải.

Endpoint nhận trong Laravel (theo định dạng Standard Webhooks):

```php
<?php
declare(strict_types=1);

namespace App\Http\Controllers;

use App\Jobs\ProcessPaymentWebhook;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\DB;

final class PaymentWebhookController
{
    private const TOLERANCE_SECONDS = 300;

    public function __invoke(Request $request): Response
    {
        $raw = $request->getContent();                       // raw body, KHÔNG parse rồi encode lại
        $id  = (string) $request->header('webhook-id', '');
        $ts  = (string) $request->header('webhook-timestamp', '');
        $sig = (string) $request->header('webhook-signature', '');

        if (!ctype_digit($ts) || abs(time() - (int) $ts) > self::TOLERANCE_SECONDS) {
            return response('stale timestamp', 400);
        }

        /** @var list<string> $secrets secret hiện tại, và secret cũ trong lúc rotate */
        $secrets = config('services.payment.webhook_secrets');
        if (!$this->validSignature($secrets, $id, $ts, $raw, $sig)) {
            return response('invalid signature', 400);
        }

        // unique index trên event_id: event trùng thì insertOrIgnore trả 0 dòng
        $inserted = DB::table('webhook_inbox')->insertOrIgnore([
            'event_id'    => $id,
            'payload'     => $raw,
            'status'      => 'received',
            'received_at' => now(),
        ]);

        if ($inserted === 1) {
            ProcessPaymentWebhook::dispatch($id);             // xử lý thật ở worker
        }

        return response()->noContent();                      // 204, trùng hay không cũng trả 2xx
    }

    /** @param list<string> $secrets */
    private function validSignature(array $secrets, string $id, string $ts, string $raw, string $header): bool
    {
        $received = explode(' ', $header);                   // có thể nhiều chữ ký khi rotate
        foreach ($secrets as $secret) {
            $key = base64_decode(substr($secret, strlen('whsec_')), true);
            if ($key === false) {
                continue;
            }
            $expected = 'v1,' . base64_encode(hash_hmac('sha256', "{$id}.{$ts}.{$raw}", $key, true));
            foreach ($received as $candidate) {
                if (hash_equals($expected, $candidate)) {     // constant-time
                    return true;
                }
            }
        }
        return false;
    }
}
```

```php
// routes/api.php : group api không có CSRF middleware, hợp cho webhook
Route::post('/webhooks/payment', \App\Http\Controllers\PaymentWebhookController::class);
```

Ghi chú cho đoạn trên:

- ⚠️ Đặt route trong `routes/web.php` thì middleware chống CSRF sẽ trả 419, vì bên gửi không có CSRF
  token. Laravel docs khuyên đặt route webhook ngoài group `web`; nếu buộc phải để trong `web` thì
  loại trừ URI bằng `$middleware->preventRequestForgery(except: ['webhooks/*'])` trong
  `bootstrap/app.php` (Laravel 13).
- Insert thành công nhưng process chết trước `dispatch` thì event nằm trong bảng mà không có job.
  Thêm một lệnh schedule quét các dòng `received` quá vài phút để dispatch lại, hoặc dùng queue
  driver `database` trong cùng transaction. Bảng `webhook_inbox` chính là *inbox pattern*, đối xứng
  với outbox ở bên gửi.
- Job xử lý cũng phải idempotent (queue cũng là at-least-once): chuyển trạng thái có điều kiện, ví
  dụ `UPDATE webhook_inbox SET status = 'processing' WHERE event_id = ? AND status = 'received'`
  rồi kiểm tra số dòng bị ảnh hưởng.
- Stripe lưu ý thêm: đôi khi có hai event object khác id cho cùng một thay đổi; muốn chặn cả trường
  hợp này thì khử trùng theo id của object trong `data` cộng loại event.

*Với việc quan trọng như thanh toán*, verify chữ ký chưa đủ:

- Coi webhook là **tín hiệu**, không phải sự thật: nhận `order.paid` thì gọi API của cổng thanh toán
  để lấy trạng thái giao dịch, so số tiền và đơn vị tiền với đơn trong DB, rồi mới giao hàng.
- Có job *đối soát* (*reconciliation*: định kỳ so dữ liệu hai bên), vì webhook có thể mất hẳn: hết
  lịch retry, endpoint bị tắt, bug ở bên gửi. Chi tiết ở [22-practical-data](../22-practical-data.md).
- Stripe khuyên dùng cả hai lớp: allowlist IP nguồn của họ và verify chữ ký.

*Chẩn đoán "đối tác nói không nhận được webhook"*: tra log delivery phía gửi theo event id; các
nguyên nhân Stripe liệt kê: không kết nối được (URL không công khai), `3xx` (bị coi là lỗi), `4xx`
(`401/403` do auth hoặc firewall, `404` sai URL, `405` không nhận `POST`), `5xx` (lỗi code bên
nhận), lỗi TLS (chứng chỉ, chuỗi trung gian), timeout (xử lý đồng bộ quá lâu).

**Tóm tắt nhanh**
- Webhook là at-least-once và không có thứ tự: bên nhận khử trùng bằng event id (unique
  constraint) và bỏ qua bản cũ bằng version, hoặc dùng thin event rồi gọi API lấy bản mới.
- Bên gửi: outbox trong cùng transaction, worker gửi với timeout, retry exponential backoff + jitter
  trải nhiều ngày, rồi đánh dấu thất bại, cho replay, tắt endpoint chết. Chặn SSRF lúc gửi (IP nội
  bộ, metadata `169.254.169.254`, redirect).
- Ký: `HMAC-SHA256(secret, id.timestamp.raw_body)`, mỗi endpoint một secret, gửi nhiều chữ ký để
  rotate không downtime (Standard Webhooks: `webhook-id`, `webhook-timestamp`, `webhook-signature`).
- Bên nhận: verify trên raw body (`$request->getContent()`), so bằng `hash_equals`, từ chối timestamp
  lệch (Stripe mặc định 5 phút), insert idempotent, trả `2xx` ngay và xử lý ở queue.
- Thanh toán: webhook chỉ là tín hiệu; xác nhận lại qua API và đối soát định kỳ.

**Nguồn**: [Standard Webhooks specification](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md) ·
[Stripe: Receive webhook events](https://docs.stripe.com/webhooks) ·
[OWASP API7:2023 SSRF](https://owasp.org/API-Security/editions/2023/en/0xa7-server-side-request-forgery/) ·
[Laravel: CSRF, Excluding URIs](https://laravel.com/docs/csrf#csrf-excluding-uris) ·
[Laravel: Queues, backoff](https://laravel.com/docs/queues)

---

### 2.5 Gọi API bên thứ ba

Module này trả lời: khi code của bạn phụ thuộc vào một API bên ngoài (thanh toán, SMS, vận chuyển,
AI) mà sớm muộn sẽ chậm hoặc chết, làm sao để sự cố của họ không thành sự cố của bạn, và làm sao để
retry không biến một lỗi nhỏ thành sập toàn hệ thống.

#### Timeout: luôn đặt

Amazon Builders' Library mở đầu bằng một quan sát: nhiều loại lỗi không hiện ra dưới dạng "lỗi" mà
dưới dạng request **chạy lâu bất thường, có khi không bao giờ xong**. Trong lúc chờ, client vẫn giữ
tài nguyên (bộ nhớ, thread, kết nối, port). Đủ nhiều request cùng chờ thì hết tài nguyên. Thực hành
ở Amazon: đặt timeout cho **mọi** lời gọi remote, kể cả giữa hai process trên cùng một máy, gồm cả
connection timeout lẫn request timeout.

Có hai loại timeout cần phân biệt:

| Loại | Đo gì | Khi nào chạm |
|---|---|---|
| *Connect timeout* | Thời gian mở được kết nối TCP (và thường gồm cả bắt tay TLS, tuỳ thư viện) | Host chết, firewall nuốt gói tin, sai IP |
| *Request timeout* (còn gọi total timeout) | Tổng thời gian của cả request, từ lúc bắt đầu tới khi nhận xong response | Server nhận kết nối nhưng xử lý chậm hoặc treo |

Một số thư viện còn có *read timeout* (khoảng tối đa giữa hai lần nhận được dữ liệu). ⚠️ Read timeout
không giới hạn tổng thời gian: server nhỏ giọt mỗi 20 giây một byte thì read timeout 30 giây không
bao giờ chạm. Cái cần cho request đồng bộ là tổng thời gian.

⚠️ Giá trị mặc định là cái bẫy chính. Nhiều thư viện mặc định **không có giới hạn tổng**:

| Thư viện | Mặc định |
|---|---|
| cURL của PHP | `CURLOPT_TIMEOUT` là 0, tức không giới hạn; `CURLOPT_CONNECTTIMEOUT` theo libcurl là 300 giây |
| Guzzle | `timeout` là 0 (chờ vô hạn) |
| Go `http.Client{}` | Field `Timeout` bằng 0 nghĩa là không có timeout |
| Java `java.net.http.HttpClient` | Không đặt `timeout` trên `HttpRequest` thì chờ vô hạn |
| Laravel HTTP client | `timeout` 30 giây, `connectTimeout` 10 giây (đọc từ docs và mã nguồn `PendingRequest`) |

Laravel có mặc định, nhưng ⚠️ 30 giây là quá dài cho một request mà user đang đứng chờ, và càng quá
dài khi nhân với số lần retry.

*Vì sao nguy hiểm với PHP-FPM*. Mỗi request chiếm trọn một worker FPM từ đầu đến cuối (mô hình ở
[05: PHP-FPM](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing)). Giả sử pool có 50 worker và
trang checkout gọi provider vận chuyển để tính phí:

```
Bình thường: provider trả trong 200 ms  -> mỗi worker phục vụ ~5 request/giây, dư sức
Provider treo, timeout 30 s              -> mỗi request checkout giữ worker 30 s
  sau vài giây: 50/50 worker đang chờ provider
  request vào trang chủ, trang sản phẩm (không liên quan provider) xếp hàng ở Nginx
  -> 502/504 trên toàn site, dù chỉ một tính năng phụ thuộc provider
```

Một lưu ý nữa từ module đó: `max_execution_time` của PHP trên Linux không tính thời gian chờ I/O, nên
nó không cứu bạn khỏi một lời gọi HTTP treo; timeout phải đặt ở chính HTTP client.

*Chọn con số nào*. Cách của Amazon cho gọi nội bộ: chọn tỉ lệ *false timeout* (timeout nhầm những
request đằng nào cũng thành công) chấp nhận được, ví dụ 0,1%, rồi đặt timeout bằng percentile tương
ứng của latency phía bên kia, ở đây là p99.9. Bài viết nêu các ngoại lệ:

- Gọi qua internet thì cộng thêm độ trễ mạng trường hợp xấu.
- Service có p99.9 rất sát p50 thì cần thêm khoảng đệm, nếu không chỉ hơi chậm lên là hàng loạt
  request timeout.
- ⚠️ Timeout có thể bao gồm cả thời gian mở kết nối mới và bắt tay TLS. Bài viết kể một hệ thống đặt
  timeout khoảng 20 ms, chỉ bị timeout ngay sau mỗi lần deploy, vì kết nối TLS mới tốn hơn 20 ms;
  cách sửa cuối cùng là mở sẵn kết nối lúc process khởi động, trước khi nhận traffic.
- Có implementation mà timeout không phủ hết mọi bước, như phân giải DNS hay bắt tay TLS. Nên dùng
  timeout có sẵn của client đã được kiểm chứng thay vì tự chế.

Với request đồng bộ mà user chờ, còn một ràng buộc từ trên xuống: tổng thời gian (mọi lần thử
cộng mọi lần chờ) phải nhỏ hơn timeout của các tầng bên ngoài (Nginx `fastcgi_read_timeout`, load
balancer, timeout của app mobile). Nếu không, tầng ngoài cắt trước, user nhận 504 trong khi PHP vẫn
đang retry vô ích.

#### Retry có điều kiện

Amazon gọi retry là "ích kỷ" (*selfish*): client retry là đang đòi server bỏ thêm tài nguyên cho
request của mình. Khi lỗi hiếm và thoáng qua, việc này có lợi. Khi lỗi do **quá tải**, retry làm
tăng tải, và có thể giữ tải cao rất lâu sau khi nguyên nhân gốc đã hết, làm chậm phục hồi.

Chỉ retry khi thoả **cả hai** điều kiện:

1. **Lỗi có khả năng là tạm thời**. HTTP phân biệt rõ: lỗi `4xx` là lỗi của request, gửi lại y hệt
   vẫn hỏng; lỗi `5xx` có thể thành công ở lần sau (bảng chi tiết ở module
   [1.2 Status code](#12-status-code)). Nhóm đáng retry: lỗi kết nối, timeout, `502`, `503`, `504`,
   `429` (sau khi chờ `Retry-After`). Không retry `400`, `401`, `403`, `404`, `409`, `422`. Amazon lưu
   ý ranh giới này bị mờ trong hệ thống *eventually consistent*: một `404` lúc này có thể thành
   `200` vài giây sau khi dữ liệu lan tới.
2. **Thao tác idempotent**: gọi nhiều lần cho cùng kết quả như gọi một lần. `GET`, `PUT`, `DELETE`
   theo ngữ nghĩa HTTP là idempotent; `POST` tạo đơn, trừ tiền, gửi SMS thì không, **trừ khi** bên
   kia hỗ trợ idempotency key (module [2.1](#21-idempotency-key-và-retry-an-toàn)). Amazon ví dụ API
   `RunInstances` của EC2 nhận một token để retry an toàn. Không có cơ chế này thì retry `POST` gửi
   SMS là gửi hai tin, thu tiền hai lần.

*Backoff và jitter*:

- *Exponential backoff*: chờ tăng theo cấp số nhân sau mỗi lần thử (ví dụ 100 ms, 200 ms, 400 ms...).
- *Capped*: đặt trần cho thời gian chờ, vì hàm mũ tăng rất nhanh.
- *Jitter*: cộng một lượng ngẫu nhiên. Không có jitter, mọi client thất bại cùng lúc sẽ retry cùng
  lúc và lại gây quá tải đúng như lần đầu. Amazon còn thêm jitter cho **mọi** timer, cron, việc
  định kỳ, vì nhiều server cùng chạy job "mỗi phút một lần" sẽ dồn tải vào vài giây đầu mỗi phút.

⚠️ *Retry amplification* (khuếch đại retry). Ví dụ trong bài của Amazon: một lời gọi đi qua 5 tầng
service rồi tới DB, mỗi tầng tự retry 3 lần. Khi DB bắt đầu lỗi vì quá tải, tải lên DB tăng
3^5 = 243 lần, gần như không thể tự phục hồi. Khuyến nghị: retry ở **một điểm duy nhất** trong
chuỗi gọi. Ví dụ trong Laravel: job trong queue đã có `$tries`, mà bên trong lại gọi
`Http::retry(3)` thì một lần gọi thành 3 × `$tries` lần.

*Giới hạn cả số lần và tổng thời gian*. Amazon chọn giới hạn số lần retry và xử lý thất bại sớm ở
tầng trên. Tính thời gian tệ nhất một request có thể treo:

```
tổng tệ nhất  =  số lần thử × timeout mỗi lần  +  tổng thời gian chờ giữa các lần

Ví dụ: 3 lần thử (tức retry 2 lần), timeout 5 s mỗi lần, chờ 1 s rồi 2 s giữa các lần
       = 3 × 5 + 1 + 2 = 18 giây
Cùng cấu hình nhưng để timeout mặc định 30 s của Laravel:
       = 3 × 30 + 1 + 2 = 93 giây, vượt xa fastcgi_read_timeout mặc định 60 s của Nginx
```

⚠️ Cẩn thận cách đếm: `Http::retry(3, ...)` của Laravel là **tổng 3 lần thử** (lần đầu cộng 2 lần
retry), không phải 3 lần retry. Và thời gian chờ giữa các lần thử được `sleep` ngay trong process,
tức worker FPM vẫn bị giữ suốt thời gian đó.

Amazon có thêm một kỹ thuật cho tải: giới hạn retry cục bộ bằng *token bucket* (mỗi lần retry tốn
một token, token hồi dần theo tốc độ cố định). Lúc bình thường mọi lời gọi được retry; khi lỗi hàng
loạt, token cạn và retry bị giới hạn ở tốc độ cố định. AWS SDK có sẵn hành vi này từ 2016.

#### Các pattern chịu lỗi

*Circuit breaker* (cầu dao, pattern được Michael Nygard phổ biến trong sách *Release It!*, Martin
Fowler mô tả lại): bọc lời gọi remote trong một object theo dõi lỗi. Ba trạng thái:

```
              lỗi vượt ngưỡng
   CLOSED ─────────────────────────▶ OPEN
 (gọi bình thường,                  (không gọi nữa, trả lỗi ngay: fail fast)
  đếm lỗi)  ◀──────┐                    │
                   │ thử thành công     │ hết thời gian chờ reset
                   │                    ▼
                   └──────────────── HALF-OPEN
                                    (cho một request thử thật)
                    thử thất bại: quay lại OPEN, đếm lại thời gian chờ
```

Ý nghĩa: khi provider đã chết, không để mọi request đứng chờ đủ 5 giây timeout rồi mới báo lỗi. Cầu
dao mở thì trả lỗi ngay, worker được giải phóng, và provider đang chật vật không bị dội thêm tải.
Fowler nêu thêm vài ý thực dụng:

- Không phải lỗi nào cũng nên làm nhảy cầu dao: lỗi nghiệp vụ bình thường (`422`) phải xử lý như
  logic thường; chỉ lỗi kết nối, timeout, `5xx` mới tính.
- Ngưỡng tinh hơn "đếm N lỗi liên tiếp" là theo tỉ lệ, ví dụ nhảy khi tỉ lệ lỗi tới 50%; có thể đặt
  ngưỡng khác nhau cho từng loại lỗi (timeout 10, lỗi kết nối 3).
- Mọi lần đổi trạng thái phải được log và cảnh báo; đội vận hành nên có cách mở hoặc đóng cầu dao
  bằng tay.
- Code gọi phải quyết định làm gì khi cầu dao mở: làm thất bại thao tác, hay có đường vòng.

Cần biết cả góc nhìn ngược: bài của Amazon nhận xét circuit breaker đưa *modal behavior* (hệ thống
có nhiều "chế độ" hoạt động khác nhau) vào hệ thống, khó test, và có thể làm thời gian phục hồi dài
thêm đáng kể; họ ưu tiên giới hạn retry bằng token bucket. Trả lời phỏng vấn tốt là nêu được cả hai.

Circuit breaker trong Laravel bằng cache (dùng store chung như Redis để mọi server cùng thấy một
trạng thái):

```php
<?php
declare(strict_types=1);

namespace App\Support;

use Illuminate\Contracts\Cache\Repository;

final class CircuitBreaker
{
    public function __construct(
        private readonly Repository $cache,
        private readonly string $name,
        private readonly int $threshold = 5,       // số lỗi trong cửa sổ để mở cầu dao
        private readonly int $windowSeconds = 60,  // cửa sổ đếm lỗi
        private readonly int $openSeconds = 30,    // mở bao lâu thì chuyển half-open
    ) {}

    public function allowRequest(): bool
    {
        $openUntil = $this->cache->get($this->key('open_until'));
        if ($openUntil === null) {
            return true;                                         // CLOSED
        }
        if (time() < (int) $openUntil) {
            return false;                                        // OPEN: fail fast
        }
        // HALF-OPEN: add() chỉ thành công cho đúng một request, request đó được thử thật
        return $this->cache->add($this->key('probe'), 1, 10);
    }

    public function recordSuccess(): void
    {
        foreach (['open_until', 'probe', 'fails'] as $k) {
            $this->cache->forget($this->key($k));                // về CLOSED
        }
    }

    public function recordFailure(): void
    {
        $openUntil = $this->cache->get($this->key('open_until'));
        if ($openUntil !== null && time() >= (int) $openUntil) { // thử ở HALF-OPEN thất bại
            $this->open();
            return;
        }
        $this->cache->add($this->key('fails'), 0, $this->windowSeconds); // tạo key kèm TTL nếu chưa có
        $fails = (int) $this->cache->increment($this->key('fails'));
        if ($fails >= $this->threshold) {
            $this->open();
        }
    }

    private function open(): void
    {
        // giữ key lâu hơn openSeconds để còn biết là đang HALF-OPEN sau khi hết hạn mở
        $this->cache->put($this->key('open_until'), time() + $this->openSeconds, $this->openSeconds * 10);
        $this->cache->forget($this->key('probe'));
        $this->cache->forget($this->key('fails'));
    }

    private function key(string $suffix): string
    {
        return "circuit:{$this->name}:{$suffix}";
    }
}
```

Đây là bản tối giản để hiểu cơ chế (đếm lỗi theo cửa sổ cố định, chưa có log khi đổi trạng thái).
⚠️ Nếu cache là `file` hoặc `array`, mỗi server hoặc mỗi process có cầu dao riêng: vẫn chạy, nhưng mỗi
nơi phải tự chịu đủ số lỗi mới mở.

*Bulkhead* (vách ngăn chống chìm tàu: thủng một khoang không làm chìm cả tàu): giới hạn tài nguyên
dành cho mỗi phụ thuộc, để một provider chậm không chiếm hết tài nguyên chung. Fowler có nhắc một ý
gần: chạy lời gọi remote trên thread lấy từ thread pool, và cho cầu dao nhảy khi pool cạn. Trong PHP-FPM không có
thread pool trong process, nên bulkhead thực tế thường là:

- Đưa lời gọi không cần kết quả ngay vào **queue riêng** cho provider đó, với số worker cố định
  (ví dụ 10). Provider chậm thì chỉ queue đó dồn lại; web worker không bị ảnh hưởng.
- Tách pool FPM riêng cho nhóm endpoint phụ thuộc provider chậm (cấu hình ở tầng FPM/Nginx).

*Fallback*: phương án thay thế khi lời gọi thất bại hoặc cầu dao mở. Ví dụ từ Fowler: yêu cầu thanh
toán thẻ đưa vào queue xử lý sau; dữ liệu không lấy được thì hiện dữ liệu cũ "đủ tốt để hiển thị".
Các dạng khác: trả giá trị mặc định (phí vận chuyển ước tính), chuyển sang provider dự phòng, hoặc
tắt tính năng đó trên giao diện. ⚠️ Fallback cũng là code chạy hiếm khi, nên cũng hay hỏng nhất
đúng lúc cần; phải test nó như code chính.

#### Lớp gọi provider trong Laravel

Ghép các ý trên thành một adapter cho provider SMS (gộp interface, exception và class vào một khối
cho dễ đọc; trong dự án thật mỗi type một file theo PSR-4):

```php
<?php
declare(strict_types=1);

namespace App\Sms;

use App\Support\CircuitBreaker;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\Factory as Http;
use Illuminate\Http\Client\RequestException;
use Psr\Log\LoggerInterface;
use Throwable;

interface SmsSender
{
    /** @throws SmsUnavailable khi provider không dùng được lúc này */
    public function send(string $phone, string $text, string $idempotencyKey): string;
}

final class SmsUnavailable extends \RuntimeException {}

final class AcmeSmsSender implements SmsSender
{
    public function __construct(
        private readonly Http $http,
        private readonly CircuitBreaker $breaker,
        private readonly LoggerInterface $log,
        private readonly string $baseUrl,
        private readonly string $apiKey,
    ) {}

    public function send(string $phone, string $text, string $idempotencyKey): string
    {
        if (!$this->breaker->allowRequest()) {
            throw new SmsUnavailable('acme-sms: circuit open');
        }

        $started = microtime(true);
        try {
            $response = $this->http
                ->baseUrl($this->baseUrl)
                ->withToken($this->apiKey)
                ->withHeaders(['Idempotency-Key' => $idempotencyKey]) // retry POST mới an toàn
                ->connectTimeout(2)
                ->timeout(5)                                           // mỗi lần thử tối đa 5 s
                ->retry(
                    2,                                                 // tổng 2 lần thử
                    fn (int $attempt): int => 200 * $attempt + random_int(0, 100), // ms, có jitter
                    fn (Throwable $e): bool => $e instanceof ConnectionException
                        || ($e instanceof RequestException
                            && ($e->response->serverError() || $e->response->status() === 429)),
                )
                ->post('/v1/messages', ['to' => $phone, 'text' => $text]);
        } catch (ConnectionException $e) {
            $this->breaker->recordFailure();
            throw new SmsUnavailable('acme-sms: connection/timeout', previous: $e);
        } catch (RequestException $e) {
            if ($e->response->serverError()) {
                $this->breaker->recordFailure();                       // chỉ 5xx làm nhảy cầu dao
                throw new SmsUnavailable('acme-sms: ' . $e->response->status(), previous: $e);
            }
            throw $e;                                                  // 4xx: lỗi của mình, không retry
        } finally {
            $this->log->info('acme-sms call', [
                'phone' => substr($phone, 0, 3) . '****' . substr($phone, -2), // che PII
                'ms' => (int) ((microtime(true) - $started) * 1000),
            ]);
        }

        $this->breaker->recordSuccess();
        return (string) $response->json('id');
    }
}
```

Thời gian tệ nhất của cấu hình này: 2 × 5 + khoảng 0,3 giây chờ, tức khoảng 10 giây. Vẫn dài nếu
user đang chờ; với SMS, cách tốt hơn nữa là gọi `send()` trong một job queue, và web request chỉ
dispatch job.

Ghi chú:

- Khi đã gọi `retry()`, response không phải `2xx` ở lần thử cuối sẽ ném `RequestException` (tham số
  `throw` mặc định `true`), nên cả hai nhánh catch đều có tác dụng. ⚠️ Nếu **không** truyền closure
  điều kiện (tham số thứ ba), Laravel retry với mọi response không thành công, **kể cả `4xx`**, theo
  docs ("if a client or server error occurs") và mã nguồn.
- Closure điều kiện còn nhận `PendingRequest` và method HTTP, dùng được để chỉ retry method
  idempotent khi provider không hỗ trợ idempotency key.
- Muốn tôn trọng `Retry-After` của `429`: closure tính thời gian chờ nhận cả exception làm tham số
  thứ hai, từ đó (sau khi kiểm tra `$e instanceof RequestException`) đọc
  `$e->response->header('Retry-After')`.
- Laravel mặc định đi theo redirect (hành vi của Guzzle); với URL do người dùng cung cấp (như webhook ở
  module 2.4) thì tắt bằng `withoutRedirecting()`.

#### Quan sát và kiểm thử

*Log mỗi lần gọi*: provider, endpoint, status, latency, số lần thử, request id của bên kia (nhiều
provider trả trong header, rất cần khi mở ticket hỗ trợ). ⚠️ Che secret (API key, header
`Authorization`) và *PII* (thông tin định danh cá nhân: số điện thoại, email, số thẻ) trước khi ghi.
Log chứa token là cách lộ token phổ biến.

*Metric theo từng provider*: latency (p50, p99), tỉ lệ lỗi, số lần cầu dao mở. Cảnh báo khi tỉ lệ lỗi
của một provider tăng, thường sớm hơn cả trang status của chính provider đó.

⚠️ *Sandbox khác production*. Môi trường thử của provider có rate limit, độ trễ, thậm chí hành vi
khác. Ví dụ ở module 2.4: Stripe ở sandbox chỉ retry webhook ba lần trong vài giờ, còn live mode
retry tới ba ngày. Sau khi lên production, kiểm tra lại với lưu lượng nhỏ (một nhóm user, một tỉ lệ
đơn nhỏ) trước khi mở toàn bộ.

*Không tin dữ liệu của bên thứ ba* (OWASP API10:2023 *Unsafe Consumption of APIs*): lập trình viên
thường tin response của đối tác hơn input của user, và kẻ tấn công lợi dụng điều đó bằng cách tấn
công vào dịch vụ tích hợp thay vì API của bạn. Validate response như validate input (kiểu, độ dài,
giá trị hợp lệ), không đi theo redirect một cách mù quáng, giới hạn kích thước response.

*Bọc provider sau interface* (adapter, [08-oop-design](../08-oop-design.md)): code nghiệp vụ chỉ biết
`SmsSender`, nên đổi provider là viết adapter mới, và test dùng bản giả. Với Laravel HTTP client
còn test được chính adapter mà không gọi mạng thật:

```php
<?php
declare(strict_types=1);

use App\Sms\SmsSender;
use App\Sms\SmsUnavailable;
use Illuminate\Http\Client\Request;
use Illuminate\Support\Facades\Http;

test('provider 503 rồi 200 thì retry và thành công', function (): void {
    Http::preventStrayRequests();                 // request nào chưa fake sẽ ném exception
    Http::fake([
        'sms.example.test/*' => Http::sequence()
            ->pushStatus(503)
            ->push(['id' => 'msg_1'], 200),
    ]);

    expect(app(SmsSender::class)->send('0901234567', 'OTP 1234', 'otp-42'))->toBe('msg_1');
    Http::assertSentCount(2);
    Http::assertSent(fn (Request $r): bool => $r->hasHeader('Idempotency-Key', 'otp-42'));
});

test('422 không retry', function (): void {
    Http::fake(['sms.example.test/*' => Http::response(['error' => 'invalid phone'], 422)]);

    expect(fn () => app(SmsSender::class)->send('abc', 'x', 'k'))
        ->toThrow(\Illuminate\Http\Client\RequestException::class);
    Http::assertSentCount(1);
});

test('mất kết nối thì báo provider không dùng được', function (): void {
    Http::fake(['sms.example.test/*' => Http::failedConnection()]);

    expect(fn () => app(SmsSender::class)->send('0901234567', 'x', 'k'))
        ->toThrow(SmsUnavailable::class);
});
```

Đoạn test trên viết theo Pest, giả định `SmsSender` được bind trong service container với
`baseUrl` là `https://sms.example.test` và cache của test là `array`. `Http::fake`,
`Http::sequence()`, `Http::failedConnection()`, `assertSent`, `assertSentCount`,
`preventStrayRequests` đều là API có trong docs HTTP client. ⚠️ Không có `preventStrayRequests`, URL
nào quên fake sẽ **gọi thật** ra ngoài.

#### Timeout không có nghĩa là thất bại

⚠️ Đây là ý hay bị hỏi vặn nhất. Timeout chỉ nói "tôi không nhận được câu trả lời kịp", không nói
"bên kia không làm". Amazon viết rõ: một timeout hay lỗi không có nghĩa là tác dụng phụ chưa xảy ra.

```
 Shop                                    Cổng thanh toán
  │ POST /charges (số tiền 500.000) ─────▶ │ trừ tiền thẻ khách: THÀNH CÔNG
  │                                        │ gửi response...
  │  (5 s trôi qua, timeout)               │   ...mạng chậm, response tới muộn
  │ báo user "thanh toán lỗi, thử lại"     │
  │ user bấm lại -> POST /charges ───────▶ │ trừ tiền LẦN HAI
```

Ba trạng thái của một lời gọi có tác dụng phụ: thành công, thất bại, và **không rõ**. Timeout, mất
kết nối sau khi đã gửi request, `502`/`504` từ proxy đều rơi vào "không rõ". Với "không rõ":

1. Không được coi là "chưa trừ tiền" rồi cho user trả lại theo luồng mới.
2. Nếu đã gửi idempotency key thì retry **cùng key**: bên kia trả lại kết quả của lần đầu thay vì
   tạo giao dịch mới (module [2.1](#21-idempotency-key-và-retry-an-toàn)).
3. Hoặc hỏi lại trạng thái theo mã tham chiếu của mình (`GET /charges?merchant_ref=ORD-123`).
4. Lưu đơn ở trạng thái trung gian (`payment_pending`), không phải `failed`, và để job đối soát
   chốt kết quả sau ([22-practical-data](../22-practical-data.md)).

#### Đối chiếu Java/Go

| | Laravel / PHP | Java | Go |
|---|---|---|---|
| Timeout | `Http::timeout()->connectTimeout()`; Guzzle: option `timeout`, `connect_timeout` | `HttpClient.newBuilder().connectTimeout(...)`, `HttpRequest.newBuilder().timeout(...)` | `http.Client{Timeout: ...}`, hoặc `context.WithTimeout` cho từng request |
| Retry | `Http::retry()`; Guzzle thuần dùng retry middleware | Resilience4j `Retry` | Tự viết vòng lặp, hoặc thư viện |
| Circuit breaker | Tự viết bằng cache (như trên) hoặc package | Resilience4j `CircuitBreaker` | `sony/gobreaker` |
| Bulkhead | Queue riêng số worker cố định, pool FPM riêng | Resilience4j `Bulkhead` (giới hạn số lời gọi đồng thời) | Semaphore bằng buffered channel |

Điểm khác đáng nói của Go: `context` mang *deadline* xuyên suốt chuỗi gọi. Handler nhận request với
hạn 3 giây, truyền `ctx` xuống mọi lời gọi DB và HTTP; hết hạn thì mọi lời gọi con cùng bị huỷ. PHP
không có cơ chế tương đương sẵn, nên phải tự tính "thời gian còn lại" nếu muốn làm tương tự.

```go
ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
defer cancel()

req, err := http.NewRequestWithContext(ctx, http.MethodGet, "https://ship.example.test/fee", nil)
if err != nil {
	return err
}
resp, err := client.Do(req) // hết 3 s: lỗi context deadline exceeded; client ngắt kết nối: context canceled
if err != nil {
	return err
}
defer resp.Body.Close()
```

**Tóm tắt nhanh**
- Luôn đặt connect timeout và total timeout; cURL, Guzzle, Go `http.Client{}` mặc định không có giới
  hạn tổng, Laravel mặc định 30 s là quá dài cho request đồng bộ. Với PHP-FPM, một provider treo làm
  cạn worker của cả site.
- Retry chỉ khi lỗi tạm thời (kết nối, timeout, `5xx`, `429`) **và** thao tác idempotent hoặc có
  idempotency key; exponential backoff có trần cộng jitter; retry ở một tầng duy nhất (5 tầng × 3 lần
  = 243 lần tải).
- Tính được thời gian treo tệ nhất: số lần thử × timeout + tổng thời gian chờ; `Http::retry(3)` là 3
  lần thử, và mặc định retry cả `4xx` nếu không truyền điều kiện.
- Circuit breaker (closed, open, half-open) để fail fast; bulkhead để cô lập; fallback cho đường
  vòng. Biết cả phản biện của Amazon: breaker thêm modal behavior, token bucket cho retry là lựa chọn
  khác.
- Timeout là "không rõ", không phải "thất bại": retry cùng idempotency key, hỏi lại trạng thái, đối
  soát. Log che secret và PII, test bằng `Http::fake` với `preventStrayRequests`.

**Nguồn**: [Amazon Builders' Library: Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) ·
[Laravel: HTTP Client, Timeout](https://laravel.com/docs/http-client#timeout) ·
[Retries](https://laravel.com/docs/http-client#retries) ·
[Testing](https://laravel.com/docs/http-client#testing) ·
[Laravel framework: PendingRequest.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Http/Client/PendingRequest.php) ·
[Martin Fowler: Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html) ·
[OWASP API10:2023 Unsafe Consumption of APIs](https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/)

---

### 2.6 Tầng Laravel cho API

Module này trả lời: những gì đã học ở các module trước (hình dạng response, validate, auth, rate
limit, idempotency, versioning) được làm thế nào trên Laravel 13, và các lỗi production nào nằm
ngay ở tầng framework này.

Phần lớn các thành phần Laravel dùng ở đây đã được giải thích cơ chế ở file kiến thức PHP/Laravel:
Form Request và mass assignment ở
[05-php-laravel.md, module 1.6](05-php-laravel.md#16-laravel-cơ-bản); Sanctum, Passport, rate
limiting ở [05-php-laravel.md, module 2.7](05-php-laravel.md#27-các-thành-phần-khác-của-laravel);
N+1 và `preventLazyLoading` ở [03-database-sql.md, module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel).
Module này tập trung vào góc nhìn "thiết kế API": dùng chúng thế nào để API đúng và ổn định.

#### API Resources: tách hình dạng API khỏi model

*API Resource* là một lớp biến đổi (*transformation layer*) nằm giữa model Eloquent và JSON trả
cho client. Mỗi Resource có method `toArray()` trả về array sẽ được encode thành JSON. Tạo bằng
`php artisan make:resource OrderResource`; class kế thừa `Illuminate\Http\Resources\Json\JsonResource`.
Resource cho một danh sách kế thừa `ResourceCollection` (tạo bằng cờ `--collection`, hoặc đặt tên
có đuôi `Collection`).

Vì sao không `return $order;` thẳng từ controller? Laravel vẫn encode được model ra JSON (qua
`toArray()`/`toJson()` của model), nhưng khi đó **hình dạng API bằng đúng hình dạng bảng DB**:

- Mọi cột đều ra ngoài, trừ những cột bạn nhớ khai trong `#[Hidden]`/`$hidden`. Thêm một cột nội
  bộ (`internal_note`, `cost_price`) là nó tự lộ ra API. Resource là *allowlist*: chỉ field được
  viết trong `toArray()` mới xuất hiện.
- Đổi tên cột `total` thành `grand_total` trong migration là đổi luôn tên field trong API, làm vỡ
  mọi client (module 3.1). Có Resource thì chỉ sửa một dòng `'total' => $this->grand_total`.

```php
<?php
declare(strict_types=1);

namespace App\Http\Resources;

use Illuminate\Http\Request;
use Illuminate\Http\Resources\Json\JsonResource;

/** @mixin \App\Models\Order */
final class OrderResource extends JsonResource
{
    /** @return array<string, mixed> */
    public function toArray(Request $request): array
    {
        return [
            'id'           => (string) $this->id,            // string để JS không làm tròn (module 2.7)
            'status'       => $this->status,
            'total_minor'  => $this->total_minor,             // tiền: số nguyên đơn vị nhỏ nhất
            'currency'     => $this->currency,
            'created_at'   => $this->created_at?->toIso8601ZuluString(),
            // Chỉ có mặt khi controller đã eager load 'customer'
            'customer'     => new CustomerResource($this->whenLoaded('customer')),
            'items_count'  => $this->whenCounted('items'),
            // Chỉ admin mới thấy
            'internal_note' => $this->when($request->user()?->isAdmin() === true, $this->internal_note),
        ];
    }
}
```

`$this->id` dùng được vì Resource tự chuyển (*proxy*) truy cập property và method xuống model bên
dưới. Các helper có điều kiện, theo docs Laravel:

| Helper | Field xuất hiện khi |
|---|---|
| `when($cond, $value)` | `$cond` đúng. `$value` có thể là closure, chỉ được tính khi cần |
| `mergeWhen($cond, [...])` | `$cond` đúng, gộp nhiều field cùng lúc. Không dùng trong array trộn key chuỗi và key số |
| `whenHas('name')` | Model thật sự có attribute đó (ví dụ query chỉ `select` vài cột) |
| `whenNotNull($value)` | Giá trị khác `null` |
| `whenLoaded('customer')` | Quan hệ đã được load sẵn |
| `whenCounted('items')` | Đã gọi `withCount('items')`/`loadCount('items')` |

Khi điều kiện sai, key bị **xoá hẳn** khỏi JSON, không phải thành `null`. Client phải hiểu "thiếu
field" khác "field bằng null" (module 2.7).

`whenLoaded` và N+1. `whenLoaded` nhận **tên** quan hệ (chuỗi), không nhận `$this->customer`, vì
chỉ cần chạm vào `$this->customer` là Eloquent đã lazy load. Sự khác biệt đo được bằng query log (số query trong comment là minh hoạ, không phải chạy thật):

```php
use App\Http\Resources\OrderResource;
use App\Models\Order;
use Illuminate\Support\Facades\DB;

DB::enableQueryLog();
$orders = Order::with('customer')->withCount('items')->limit(20)->get();
OrderResource::collection($orders)->resolve();
count(DB::getQueryLog());   // 2: một query orders (kèm subquery đếm items), một query customers WHERE id IN (...)

// Nếu toArray() viết 'customer' => new CustomerResource($this->customer)
// và controller quên with('customer'): 1 query orders + 20 query customers = 21 query.
```

Viết Resource bằng `whenLoaded` đẩy quyết định "load gì" về controller: controller nào cần
`customer` thì `with('customer')`, controller không cần thì field tự biến mất, không có query thừa.
Bật thêm `Model::preventLazyLoading(! app()->isProduction())` để lazy load ném exception khi dev.

Các hành vi mặc định cần biết:

- Resource ngoài cùng được bọc trong key `data`: `{"data": {...}}`. Tắt bằng
  `JsonResource::withoutWrapping()` trong `AppServiceProvider::boot()`; lệnh này chỉ tác dụng với
  lớp ngoài cùng. Response phân trang **luôn** bọc `data` kèm `links` và `meta`, kể cả khi đã tắt.
- Truyền paginator: `OrderResource::collection(Order::paginate())` tự sinh `links` (first, last,
  prev, next) và `meta` (`current_page`, `per_page`, `total`...). ⚠️ `paginate()` chạy thêm một
  `COUNT(*)` để có `total`, tốn kém trên bảng lớn; xem lại module 1.4 về cursor pagination.
- Resource bọc model vừa được tạo (`wasRecentlyCreated`) tự trả `201`, còn lại `200` (đọc
  `ResourceResponse::calculateStatus()` trong source framework).
- Thêm header: `->response()->header('X-Foo', 'bar')`, hoặc định nghĩa `withResponse()`. Thêm
  metadata cấp ngoài cùng: `with()` hoặc `->additional([...])`.
- Laravel 13 có thêm `JsonApiResource` (tạo bằng `make:resource --json-api`) sinh response theo
  chuẩn JSON:API (`{"data": {"id": "1", "type": "posts", "attributes": {...}}}`) và đặt
  `Content-Type: application/vnd.api+json`. Chỉ dùng khi team thật sự theo chuẩn JSON:API.

#### FormRequest: validate và kiểm quyền đầu vào

*Form Request* là class gom **kiểm quyền** (`authorize()`) và **luật validate** (`rules()`) cho
một request; type-hint nó vào controller thì Laravel chạy trước khi vào controller. Thứ tự:
`prepareForValidation()` (chuẩn hoá input), `authorize()` (sai thì `403`), `rules()` (sai thì
`ValidationException`). Chi tiết thứ tự và race condition của rule `unique` ở
[05-php-laravel.md, module 1.6](05-php-laravel.md#16-laravel-cơ-bản).

Ba điểm quan trọng với API:

1. Lấy dữ liệu bằng `$request->validated()` hoặc `$request->safe()->only([...])`. Chỉ field có
   trong `rules()` mới được trả về. `$request->all()` trả mọi thứ client gửi.
2. ⚠️ *Mass assignment*: `Order::create($request->all())` cho phép client gửi thêm `is_paid=1`,
   `user_id=999` và được ghi thẳng vào DB nếu model không chặn. Cần cả hai lớp: dữ liệu đi vào
   model là `validated()`, và model khai allowlist (`#[Fillable([...])]` hoặc `$fillable`). Laravel
   13 có thêm `#[FailOnUnknownFields]` (hoặc bật toàn cục `FormRequest::failOnUnknownFields()`) để
   request có field lạ bị từ chối; docs nói rõ nó không thay thế `$fillable`. Từ chối field lạ
   cũng khớp khuyến nghị của Zalando: server nên báo lỗi thay vì âm thầm bỏ qua field không hiểu.
3. ⚠️ Lỗi validation trả JSON hay redirect tuỳ vào việc request có "mong JSON" không. Laravel dùng
   `$request->expectsJson()`: đúng khi header `Accept` ưu tiên đầu tiên chứa `/json` hoặc `+json`,
   hoặc khi là request AJAX (`X-Requested-With: XMLHttpRequest`) chấp nhận mọi kiểu. Thiếu những
   điều này (ví dụ gọi bằng Postman/curl không đặt `Accept`), Laravel coi là form web: trả
   **redirect `302`** về trang trước kèm lỗi trong session, client API nhận HTML hoặc bị chuyển
   hướng khó hiểu.

Response lỗi validation mặc định (status `422`), key lồng nhau được làm phẳng bằng dấu chấm:

```json
{
  "message": "The items.0.qty field is required. (and 1 more error)",
  "errors": {
    "items.0.qty": ["The items.0.qty field is required."],
    "currency": ["The selected currency is invalid."]
  }
}
```

Cách chắc chắn cho API: ép mọi route `api/*` render lỗi dạng JSON, không phụ thuộc client nhớ gửi
`Accept`:

```php
// bootstrap/app.php
use Illuminate\Http\Request;

->withExceptions(function (Exceptions $exceptions): void {
    $exceptions->shouldRenderJsonWhen(
        fn (Request $request, Throwable $e): bool => $request->is('api/*') || $request->expectsJson()
    );
})
```

Nếu API của bạn dùng format lỗi thống nhất (ví dụ Problem Details ở module 1.3), đây cũng là chỗ
đổi `ValidationException` thành format đó bằng `$exceptions->render(...)`.

#### Auth: Sanctum hay Passport

Tóm tắt (cơ chế chi tiết ở [05-php-laravel.md, module 2.7](05-php-laravel.md#27-các-thành-phần-khác-của-laravel)):

| Client | Chọn | Vì sao |
|---|---|---|
| SPA của chính bạn, chung domain gốc với API (`app.shop.vn` và `api.shop.vn`) | Sanctum SPA (cookie session) | Không có token nào nằm trong JavaScript nên XSS không lấy được; có CSRF protection sẵn |
| App mobile, script, server-to-server của khách hàng | Sanctum API token | *Personal access token* lưu dạng SHA-256 hash trong DB, có *abilities*, thu hồi được từng token |
| Ứng dụng **bên thứ ba** xin quyền truy cập dữ liệu user của bạn ("Đăng nhập bằng tài khoản X") | Passport | Cần OAuth2 server thật: authorization code + PKCE, refresh token, quản lý client |

Docs Passport nói thẳng: nếu ứng dụng "absolutely needs to support OAuth2" thì dùng Passport; còn
xác thực SPA, mobile hay phát API token thì dùng Sanctum. ⚠️ Chọn Passport chỉ để "có token" là
nhận thêm độ phức tạp của OAuth2 mà không dùng tới.

Các chi tiết hay bị hỏi:

- Sanctum xét cookie session trước, không có mới xét header `Authorization: Bearer`.
- ⚠️ Token Sanctum mặc định **không hết hạn**. Đặt `expiration` (phút) trong `config/sanctum.php`,
  hoặc truyền hạn làm tham số thứ ba của `createToken()`, và lên lịch `sanctum:prune-expired`.
- ⚠️ Với request từ SPA (cookie), `tokenCan()` luôn trả `true`, nên policy vẫn phải kiểm quyền của
  user, không chỉ ability của token.
- Passport: access token mặc định sống **một năm**; chỉnh bằng `Passport::tokensExpireIn()`. Docs
  Passport hiện không còn khuyến nghị password grant và implicit grant.

#### Rate limiting

Khai *rate limiter* có tên trong `AppServiceProvider::boot()`, rồi gắn middleware
`throttle:<tên>` cho route. Ví dụ ba mức cho ba loại client:

```php
<?php
declare(strict_types=1);

use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;

// Trong AppServiceProvider::boot()
RateLimiter::for('api', function (Request $request): Limit {
    $user = $request->user();

    if ($user === null) {
        return Limit::perMinute(30)->by('ip:' . $request->ip());       // khách chưa đăng nhập
    }

    return $user->isPaid()                                             // method tự viết trên User
        ? Limit::perMinute(600)->by('user:' . $user->id)
        : Limit::perMinute(60)->by('user:' . $user->id);
});

// routes/api.php
// Route::middleware(['auth:sanctum', 'throttle:api'])->group(function (): void { ... });
```

Những gì Laravel làm (đọc `ThrottleRequests` trong source framework):

- Mọi response trong giới hạn mang `X-RateLimit-Limit` và `X-RateLimit-Remaining`.
- Vượt giới hạn: trả `429` kèm `Retry-After` (số giây chờ) và `X-RateLimit-Reset` (thời điểm
  mở lại, dạng Unix timestamp). Đổi body bằng `->response(fn (Request $r, array $headers) => ...)`.
- Trả array nhiều `Limit` để áp nhiều mức (ví dụ theo phút và theo ngày); khi hai limit dùng cùng
  giá trị `by`, thêm tiền tố (`minute:`, `day:`) để key không đè nhau.
- `->after(fn (Response $r): bool => ...)` chỉ đếm những response thoả điều kiện, ví dụ chỉ đếm
  `404` để chống dò ID.

Cạm bẫy:

- ⚠️ Bộ đếm nằm trong **cache** (store mặc định, hoặc key `limiter` trong `config/cache.php`). Có
  4 server chia tải đều mà cache là `file` hoặc `array` thì mỗi server đếm riêng: giới hạn 60 thành
  khoảng 240. Dùng Redis (hoặc store dùng chung khác). Khi cache là Redis, có thể gọi
  `$middleware->throttleWithRedis()` trong `bootstrap/app.php` để dùng middleware
  `ThrottleRequestsWithRedis`.
- ⚠️ Từ Laravel 11, middleware group `api` mặc định chỉ có `SubstituteBindings`, **không** có sẵn
  throttle như skeleton Laravel 10 trở về trước. Phải tự gắn `throttle:api` (hoặc gọi
  `$middleware->throttleApi()`) và tự khai limiter tên `api`.
- ⚠️ `$request->user()` chỉ có giá trị khi route đã qua middleware auth (Laravel xếp
  `AuthenticatesRequests` chạy trước `ThrottleRequests` theo *middleware priority*). Với cấu hình
  guard mặc định, route public không có `auth:sanctum` thì user là `null`, mọi request bị đếm theo IP, kể cả khi client có
  gửi token.
- ⚠️ Đếm theo IP sau load balancer: phải cấu hình *trusted proxies* để `$request->ip()` là IP thật
  của client, nếu không mọi request có cùng IP của load balancer.
- Thuật toán là fixed window (chi tiết ở module 05 đã dẫn): dồn request quanh ranh giới hai cửa sổ
  có thể lọt gần gấp đôi giới hạn trong thời gian ngắn. Lý thuyết các thuật toán khác ở module 2.3.

#### Idempotency

Laravel không có middleware idempotency sẵn. Hai cách: dùng package cộng đồng, hoặc tự viết. Tự
viết là cách tốt để chắc mình hiểu đủ luồng ở [module 2.1](#21-idempotency-key-và-retry-an-toàn).
Khung một middleware dựa trên unique constraint của DB:

```php
<?php
declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Database\UniqueConstraintViolationException;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Symfony\Component\HttpFoundation\Response;

// Bảng idempotency_keys: UNIQUE (client_id, idem_key), cột status, request_hash,
// response_status, response_body, timestamps.
final class EnsureIdempotent
{
    public function handle(Request $request, Closure $next): Response
    {
        $key = $request->header('Idempotency-Key');
        if (! is_string($key) || $key === '') {
            return response()->json(['message' => 'Missing Idempotency-Key'], 400);
        }

        $clientId = (string) $request->user()->getAuthIdentifier();
        $hash     = hash('sha256', $request->getContent());
        $where    = ['client_id' => $clientId, 'idem_key' => $key];

        try {
            // Nhánh 1: INSERT thành công nghĩa là lần đầu thấy key này
            DB::table('idempotency_keys')->insert($where + [
                'status' => 'processing', 'request_hash' => $hash,
                'created_at' => now(), 'updated_at' => now(),
            ]);
        } catch (UniqueConstraintViolationException) {
            $row = DB::table('idempotency_keys')->where($where)->first();

            if ($row->request_hash !== $hash) {              // Nhánh 2: cùng key, body khác
                return response()->json(['message' => 'Key reused with different body'], 422);
            }
            if ($row->status === 'processing') {             // Nhánh 3: request đầu chưa xong
                return response()->json(['message' => 'Request in progress'], 409);
            }

            return response((string) $row->response_body, (int) $row->response_status)  // Nhánh 4
                ->header('Content-Type', 'application/json');
        }

        $response = $next($request);

        if ($response->getStatusCode() >= 500) {
            DB::table('idempotency_keys')->where($where)->delete();  // lỗi server: cho phép retry
        } else {
            DB::table('idempotency_keys')->where($where)->update([
                'status' => 'completed',
                'response_status' => $response->getStatusCode(),
                'response_body' => $response->getContent(),
                'updated_at' => now(),
            ]);
        }

        return $response;
    }
}
```

Những gì khung này **chưa** làm, và là chỗ người phỏng vấn đào:

- ⚠️ Key và kết quả nghiệp vụ không nằm trong cùng một transaction. Process chết sau khi nghiệp
  vụ commit nhưng trước khi `update` sang `completed` thì bản ghi kẹt ở `processing`: cần hạn
  (`updated_at` quá N giây thì cho xử lý lại), và nghiệp vụ bên trong vẫn phải an toàn khi chạy lại.
- Dùng `Cache::lock()` (atomic lock của cache, cần store hỗ trợ lock như Redis, database) thay DB
  thì nhanh hơn, nhưng mất dữ liệu Redis là mất dấu key (module 2.1).
- ⚠️ Không làm kiểu `SELECT` trước rồi `INSERT`: hai request trùng đến cùng lúc đều thấy "chưa có".
  Khung trên dựa vào unique constraint chính vì lý do đó.

#### Versioning

Cách phổ biến trên Laravel là version trong URL (module 3.1 bàn ưu nhược):

```php
// routes/api.php, đã có sẵn tiền tố /api
Route::prefix('v1')->group(function (): void {
    Route::get('/orders/{order}', [V1\OrderController::class, 'show']);
});
Route::prefix('v2')->group(function (): void {
    Route::get('/orders/{order}', [V2\OrderController::class, 'show']);
});
```

`routes/api.php` (tạo bởi `php artisan install:api`) tự có tiền tố `/api`; đổi tiền tố bằng tham số
`apiPrefix` của `withRouting()` trong `bootstrap/app.php`.

⚠️ Đừng copy nguyên controller, service, query cho mỗi version. Thường giữa hai version chỉ
**hình dạng response** khác nhau, nên tách đúng chỗ đó: `App\Http\Resources\V1\OrderResource` và
`V2\OrderResource`, còn logic nghiệp vụ dùng chung. Controller của mỗi version chỉ còn vài dòng
gọi cùng một service rồi bọc bằng Resource của version mình. Version sâu hơn (header theo ngày
kiểu Stripe, chuyển đổi response qua từng bước) ở module 3.1.

#### Đào sâu (🔴): Octane

*Laravel Octane* chạy ứng dụng trên một application server (FrankenPHP, Swoole, RoadRunner): boot
ứng dụng **một lần**, giữ trong memory, rồi phục vụ nhiều request liên tiếp. PHP-FPM thì mỗi request
bắt đầu từ trạng thái sạch (*share-nothing*). Nhanh hơn vì bỏ chi phí boot, đổi lại phải tự lo
state. Chi tiết ở [05-php-laravel.md, module 3.5](05-php-laravel.md#35-process-sống-lâu-queue-worker-octane-daemon).

Theo docs Octane, những gì hay gây lỗi với API:

- `register()`/`boot()` của service provider chỉ chạy một lần khi worker khởi động.
- ⚠️ Singleton nhận `Request`, container hoặc config qua constructor sẽ giữ **bản của request đầu
  tiên** cho mọi request sau: header, input, user đều sai. Hậu quả nặng nhất ở API: request của
  user B đọc thấy dữ liệu của user A. Cách sửa: không đăng ký singleton, hoặc truyền closure lấy
  bản hiện tại (`fn () => $app['request']`), hoặc tốt nhất là truyền đúng giá trị cần vào method lúc
  gọi. Type-hint `Request` trong controller method thì an toàn.
- ⚠️ Thêm phần tử vào array `static` trong mỗi request là rò rỉ memory. Octane mặc định restart
  worker sau 500 request (`--max-requests`) để hạn chế rò rỉ, nhưng đó là lưới an toàn, không phải
  cách sửa.

**Tóm tắt nhanh**

- API Resource là allowlist hình dạng API; `whenLoaded('rel')` nhận tên quan hệ để không lazy load,
  controller quyết định `with()`. Chứng minh không N+1 bằng `DB::getQueryLog()`.
- Dữ liệu vào model luôn là `validated()`, model khai `$fillable`; ép route `api/*` render lỗi JSON
  để thiếu header `Accept` không biến `422` thành redirect `302`.
- Sanctum SPA cho SPA của mình, Sanctum token cho mobile/script, Passport chỉ khi cần OAuth2 cho
  bên thứ ba. Token Sanctum mặc định không hết hạn.
- Rate limit đếm trong cache: nhiều server phải dùng Redis chung; group `api` từ Laravel 11 không
  có throttle sẵn; `user()` chỉ có khi route đã qua auth.
- Versioning: tách Resource theo version, không copy controller. Octane: không giữ state của
  request trong singleton.

**Nguồn**: [Laravel: Eloquent API Resources](https://laravel.com/docs/eloquent-resources) ·
[Laravel: Form Request Validation](https://laravel.com/docs/validation#form-request-validation) ·
[Laravel: Error Handling](https://laravel.com/docs/errors) ·
[Laravel: Sanctum](https://laravel.com/docs/sanctum) ·
[Laravel: Passport](https://laravel.com/docs/passport) ·
[Laravel: Routing, Rate Limiting](https://laravel.com/docs/routing#rate-limiting) ·
[Laravel: Rate Limiting](https://laravel.com/docs/rate-limiting) ·
[Laravel: Middleware](https://laravel.com/docs/middleware) ·
[Laravel: Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment) ·
[Laravel: Octane](https://laravel.com/docs/octane) ·
Source framework 13.x: `ThrottleRequests`, `ResourceResponse`, `InteractsWithContentTypes`

---

### 2.7 Serialization

Module này trả lời: dữ liệu bị méo ở đâu trên đường từ biến PHP tới object trong app client, và
quy ước nào (ID, tiền, thời gian, null, mảng rỗng) phải chốt từ đầu để tránh những lỗi không hề
báo lỗi.

*Serialization* là biến dữ liệu trong bộ nhớ thành chuỗi byte để gửi hoặc lưu (thường là JSON);
*deserialization* là chiều ngược lại. Lỗi ở tầng này nguy hiểm vì hai phía đều "chạy được": server
encode thành công, client parse thành công, chỉ có giá trị là sai.

#### Số lớn và ID

JSON (theo chuẩn) không giới hạn độ chính xác của số, nhưng **parser** thì có. JavaScript chỉ có
một kiểu số `Number` là số thực 64-bit (IEEE 754 *double*), biểu diễn chính xác số nguyên tới
`2^53 - 1` = `9007199254740991` (`Number.MAX_SAFE_INTEGER`). Số nguyên lớn hơn bị làm tròn về số
double gần nhất, **âm thầm**:

```sh
node -e 'console.log(JSON.parse("{\"id\": 9007199254740993}").id)'
# 9007199254740992   (sai 1, không có lỗi hay warning nào)
node -e 'console.log(JSON.parse("{\"id\": \"9007199254740993\"}").id)'
# 9007199254740993   (string giữ nguyên)
```

ID kiểu `BIGINT` tự tăng hiếm khi vượt `2^53`, nhưng ID kiểu *Snowflake* (ID 64-bit ghép từ
timestamp, mã máy và số thứ tự, dùng để sinh ID không cần DB trung tâm) vượt ngưỡng này ngay từ
đầu. Hậu quả điển hình: frontend lấy ID từ danh sách, gọi `GET /orders/{id}` với ID đã bị làm tròn,
nhận `404` hoặc tệ hơn là đơn của người khác.

Cách sửa: trả ID (và mọi số nguyên 64-bit không dùng để tính toán) dạng **string**:
`"id": "9007199254740993"`. Trong Laravel, ép ở Resource: `'id' => (string) $this->id`.

Đây không phải mẹo riêng của ai:

- ProtoJSON (cách Protobuf chuyển sang JSON) encode `int64`, `uint64`, `fixed64` thành **chuỗi
  thập phân** (`"1"`, `"-10"`), còn các kiểu 32-bit là số. Docs Protobuf giải thích: nhiều parser
  coi mọi số là double và "silently lossy" khi số nguyên lớn hơn `2**53`.
- RFC 8259 (chuẩn JSON) lưu ý phần mềm muốn tương thích tốt chỉ nên giả định độ chính xác double.

Chiều ngược lại trong PHP: `int` của PHP là 64-bit, nên `json_decode` đọc đúng `9007199254740993`.
Chỉ số vượt `PHP_INT_MAX` (`9223372036854775807`) mới bị đổi thành `float`; cờ
`JSON_BIGINT_AS_STRING` giữ những số đó dạng string.

#### Tiền và thời gian

Tiền. Không dùng số thực: `0.1 + 0.2` trong double là `0.30000000000000004`, và PHP (với
`serialize_precision = -1`, giá trị mặc định từ PHP 7.1) encode đúng con số đó ra JSON. Hai lựa
chọn an toàn, chốt một cho toàn API:

| Cách | Ví dụ | Ghi chú |
|---|---|---|
| Số nguyên theo *minor unit* (đơn vị nhỏ nhất) | `{"amount": 1999, "currency": "USD"}` nghĩa là 19.99 USD | Cách Stripe dùng. Phải kèm `currency` vì số chữ số thập phân khác nhau theo tiền tệ (VND không có phần lẻ) |
| String decimal | `{"amount": "199000.50", "currency": "VND"}` | Client parse bằng kiểu decimal, không parse thành float |

Lưu trữ và làm tròn tiền ở tầng DB và nghiệp vụ: [22-practical-data.md](../22-practical-data.md).

Thời gian. Dùng định dạng RFC 3339 (một *profile* chặt của ISO 8601, section 5.6), **luôn có
offset múi giờ**:

```
2026-09-23T08:00:00Z            Z nghĩa là UTC
2026-09-23T15:00:00+07:00       cùng thời điểm, giờ Việt Nam
2026-09-23T08:00:00.123456Z     có phần lẻ của giây
```

- Ngữ pháp RFC 3339: `full-date "T" full-time`, trong đó `time-offset = "Z" / ("+" / "-") HH:MM`.
  RFC cho phép `t`/`z` viết thường khi parse, nhưng khuyến nghị bên sinh ra dùng chữ hoa.
- ⚠️ Chuỗi không có offset (`2026-09-23 08:00:00`) là "giờ địa phương không rõ ở đâu": server hiểu
  UTC, app ở Việt Nam hiểu UTC+7, lệch 7 tiếng.
- ⚠️ Epoch dạng số (`1790812800`) thì không ai nhìn là hiểu, và client không biết đó là giây hay
  mili giây (JavaScript `Date` dùng mili giây).
- Chỉ có ngày (sinh nhật, ngày hết hạn hợp đồng): trả `"2026-09-23"`, đừng biến thành nửa đêm UTC,
  vì chuyển múi giờ sẽ làm lệch sang ngày hôm trước.

Trên Laravel: cast `date`/`datetime` mặc định serialize thành chuỗi UTC ISO 8601 dạng
`YYYY-MM-DDTHH:MM:SS.uuuuuuZ`, bất kể `timezone` của app; docs khuyên giữ `timezone` là `UTC`.
Đổi định dạng toàn model bằng cách override `serializeDate()`. Trong PHP thuần, dùng
`DateTimeInterface::RFC3339` (`Y-m-d\TH:i:sP`) hoặc `RFC3339_EXTENDED` (có mili giây). ⚠️ Hằng
`DateTimeInterface::ISO8601` của PHP có tên gây hiểu nhầm: docs PHP ghi rõ nó không tương thích
ISO 8601, dùng `ATOM`/`RFC3339` thay thế.

#### null so với thiếu field

Với `PATCH` (cập nhật một phần, module 1.1), "không gửi field" và "gửi `null`" là hai ý định khác
nhau:

| Body PATCH | Ý nghĩa |
|---|---|
| `{"name": "An"}` | Đổi tên, **giữ nguyên** `note` |
| `{"name": "An", "note": null}` | Đổi tên, **xoá** `note` |

JSON Merge Patch (RFC 7396) chuẩn hoá đúng quy ước này: field có giá trị `null` nghĩa là xoá, field
vắng mặt nghĩa là không đổi. Hệ quả:

- Tài liệu API phải nói rõ quy ước, và server phải **phân biệt được** hai trường hợp. Code kiểu
  `$note = $data['note'] ?? null;` gộp cả hai làm một và xoá nhầm dữ liệu.
- Trong Laravel, `$request->validated()` chỉ chứa key thật sự có trong input (Validator bỏ qua
  field vắng mặt), nên dùng `array_key_exists('note', $validated)` để phân biệt. `$request->has('note')`
  trả `true` khi key có mặt, kể cả khi giá trị là `null`.
- ⚠️ Middleware toàn cục `ConvertEmptyStringsToNull` của Laravel đổi `""` thành `null`. Client gửi
  chuỗi rỗng với ý "để trống" sẽ thành "xoá".
- Chiều response: Resource với `when*()` **xoá key** khi điều kiện sai (module 2.6), còn giá trị
  `null` thì vẫn có key. Chốt một quy ước cho mỗi field (luôn có key, giá trị có thể `null`; hay vắng
  mặt khi không có) và giữ ổn định: AIP-180 coi việc đổi cách serialize field (trước vắng mặt, giờ
  luôn có) là breaking change (module 3.1).

#### Cạm bẫy JSON trong PHP

⚠️ Mảng rỗng. PHP chỉ có một kiểu `array` cho cả list và map. `json_encode` quyết định dựa trên key:
key là `0, 1, 2...` liên tục thì ra JSON array, còn lại ra JSON object. Mảng rỗng thoả điều kiện
"list" nên luôn ra `[]` (output trong comment theo docs PHP, chưa chạy thử vì repo chưa có PHP):

```php
<?php
declare(strict_types=1);

echo json_encode(['settings' => []]), "\n";                 // {"settings":[]}
echo json_encode(['settings' => (object) []]), "\n";        // {"settings":{}}
echo json_encode(['settings' => new stdClass()]), "\n";     // {"settings":{}}
echo json_encode([], JSON_FORCE_OBJECT), "\n";              // {}

$list = ['foo', 'bar', 'baz'];
unset($list[1]);
echo json_encode($list), "\n";                              // {"0":"foo","2":"baz"}
echo json_encode(array_values($list)), "\n";                // ["foo","baz"]
```

- Field `settings` là map: khi có dữ liệu ra `{"theme":"dark"}`, khi rỗng ra `[]`. Client dùng
  ngôn ngữ kiểu chặt (Swift `Codable`, Kotlin) khai field là object sẽ lỗi decode, thường làm hỏng
  cả response hoặc crash màn hình. Sửa bằng `(object)` cho những field là map.
- ⚠️ `JSON_FORCE_OBJECT` ép **mọi** array trong cả cây thành object, kể cả list thật sự
  (`["a","b"]` thành `{"0":"a","1":"b"}`). Chỉ dùng khi biết chắc.
- Chiều ngược lại: list bị mất phần tử ở giữa (`unset`, `array_filter`) có key không liên tục và
  thành **object**. Collection của Laravel cũng vậy: `->filter()` giữ key, cần `->values()` trước
  khi trả ra API.

Lỗi encode/decode im lặng:

- Mặc định `json_encode` trả `false` và `json_decode` trả `null` khi lỗi (ví dụ chuỗi không phải
  UTF-8 hợp lệ, thường gặp khi dữ liệu cũ lưu bằng charset khác). `null` từ `json_decode` còn trùng
  với kết quả hợp lệ của chuỗi `"null"`.
- Cờ `JSON_THROW_ON_ERROR` (từ PHP 7.3) làm cả hai ném `JsonException`. Lưu ý: nếu có cả
  `JSON_PARTIAL_OUTPUT_ON_ERROR` thì cờ partial thắng.

```php
<?php
declare(strict_types=1);

try {
    $data = json_decode($body, true, 512, JSON_THROW_ON_ERROR);
} catch (JsonException $e) {
    // trả 400 với thông báo rõ ràng, thay vì chạy tiếp với $data = null
}
```

- Laravel `JsonResponse` tự kiểm `json_last_error()` sau khi encode và ném
  `InvalidArgumentException` nếu lỗi, nên response JSON của Laravel không âm thầm trả body rỗng.
- Cờ khác hay dùng: `JSON_UNESCAPED_UNICODE` (giữ nguyên chữ tiếng Việt thay vì `\u1ea1`),
  `JSON_UNESCAPED_SLASHES`, `JSON_PRESERVE_ZERO_FRACTION` (`12.0` ra `12.0` thay vì `12`).
  ⚠️ `JSON_NUMERIC_CHECK` đổi chuỗi trông giống số thành số: mã bưu chính `"000337"` thành `337`,
  số điện thoại mất số 0 đầu. Tránh dùng cho response API.

#### Các format khác JSON

| Format | Đặc điểm | Hay dùng cho |
|---|---|---|
| Protobuf | Nhị phân. Mỗi field được định danh bằng một số (*field number*, còn gọi là tag) chứ không bằng tên. Cần file schema `.proto` và sinh code | gRPC (module 3.3) |
| Avro | Nhị phân, schema viết bằng JSON. Dữ liệu không mang tên field, đọc được nhờ biết schema của bên ghi; thường đi kèm *Schema Registry* (dịch vụ lưu các phiên bản schema, message chỉ mang ID của schema) | Kafka, pipeline dữ liệu |
| MessagePack | Mô hình dữ liệu giống JSON nhưng mã hoá nhị phân, không cần schema | Khi cần gọn và nhanh hơn JSON mà không muốn quản lý schema |

JSON thắng ở chỗ ai cũng đọc được, debug bằng mắt, trình duyệt hỗ trợ sẵn. Format nhị phân có
schema thắng ở kích thước, tốc độ, và kiểu dữ liệu chặt (không có chuyện int64 bị làm tròn). Docs
ProtoJSON cũng nói thẳng: bản JSON của Protobuf tốn CPU và dung lượng hơn bản nhị phân, và kém
hơn về khả năng tiến hoá schema.

#### Schema evolution

*Schema evolution* là thay đổi cấu trúc dữ liệu theo thời gian trong khi bên ghi và bên đọc (phiên
bản cũ và mới) vẫn chạy song song, vì không bao giờ deploy được mọi bên cùng lúc.

Hai hướng tương thích:

- *Backward compatible*: code đọc **mới** đọc được dữ liệu **cũ**. Cần: field mới có giá trị mặc
  định, để dữ liệu cũ thiếu field vẫn đọc được.
- *Forward compatible*: code đọc **cũ** đọc được dữ liệu **mới**. Cần: bên đọc bỏ qua field lạ.

Áp vào từng format:

- Protobuf nhị phân: field lạ được giữ lại (unknown fields) nên thêm field là an toàn. ⚠️ Không
  bao giờ đổi hoặc dùng lại field number của field đã xoá (đánh dấu `reserved`), vì dữ liệu cũ mang
  số đó sẽ bị đọc thành field mới.
- ProtoJSON: dùng **tên** field chứ không dùng số, và theo docs thường không giữ unknown fields:
  client dùng schema cũ có thể **lỗi parse** khi gặp field mới, trừ khi bật tuỳ chọn bỏ qua field
  lạ. Đổi tên field là breaking, đổi field number thì không ảnh hưởng JSON (nhưng vẫn hỏng bản nhị
  phân).
- Avro: bên đọc dùng schema của mình đối chiếu với schema của bên ghi; field mới phải có `default`
  thì mới đọc được dữ liệu cũ.
- JSON API thông thường: không có schema bắt buộc, nên quy tắc nằm ở con người: server chỉ thêm
  field optional, client là *tolerant reader* (bỏ qua field lạ, module 3.1).

#### Bảo mật

⚠️ Không dùng serialization gắn với ngôn ngữ cho dữ liệu đến từ bên ngoài: PHP `unserialize()`,
Java native serialization (`ObjectInputStream`), Python `pickle`. Những format này dựng lại
**object của class bất kỳ**, và việc dựng object kích hoạt magic method (`__wakeup`,
`__destruct` trong PHP). Kẻ tấn công ghép chuỗi các class sẵn có trong vendor (*gadget chain*) để
xoá file hoặc chạy lệnh trên server.

- Docs PHP cảnh báo không truyền input không tin cậy vào `unserialize()`, **dù** có dùng tuỳ chọn
  `allowed_classes`. Dữ liệu từ client dùng `json_decode`.
- Ví dụ thực tế: CVE-2018-15133 của Laravel (các bản 5.5.x, 5.6.x cũ). Framework gọi
  `unserialize` trên giá trị đã giải mã của header `X-XSRF-TOKEN`; kẻ tấn công biết `APP_KEY` mã
  hoá được payload serialize hợp lệ và chạy code từ xa. Bài học kép: không `unserialize` dữ liệu
  từ request, và `APP_KEY` là bí mật cấp cao nhất.
- Chi tiết: [10-security.md](../10-security.md).

**Tóm tắt nhanh**

- JavaScript chỉ chính xác tới `2^53 - 1`; ID int64 trả dạng string (ProtoJSON cũng làm vậy).
- Tiền: số nguyên minor unit kèm `currency`, hoặc string decimal. Thời gian: RFC 3339 có offset,
  không dùng epoch.
- PATCH: thiếu field là giữ nguyên, `null` là xoá; server phân biệt bằng `array_key_exists` trên
  `validated()`.
- `json_encode([])` ra `[]`: field là map phải ép `(object)`; list bị `unset`/`filter` thành object,
  cần `array_values`/`->values()`. Luôn dùng `JSON_THROW_ON_ERROR`.
- Thêm field phải có mặc định, bên đọc bỏ qua field lạ; không dùng `unserialize` cho dữ liệu ngoài.

**Nguồn**: [PHP: json_encode](https://www.php.net/manual/en/function.json-encode.php) ·
[PHP: JSON constants](https://www.php.net/manual/en/json.constants.php) ·
[Protobuf: ProtoJSON Format](https://protobuf.dev/programming-guides/json/) ·
[RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) (section 5.6) ·
[RFC 7396: JSON Merge Patch](https://www.rfc-editor.org/rfc/rfc7396) ·
[Laravel: Eloquent Mutators & Casting, Date Serialization](https://laravel.com/docs/eloquent-mutators#date-casting) ·
[Google AIP-180](https://google.aip.dev/180)

---

## Chặng 3: Senior

### 3.1 Tiến hoá API: versioning, deprecation, backward compatibility

Module này trả lời: làm sao thay đổi một API đang có client bạn không kiểm soát (app mobile, đối
tác) mà không làm vỡ ai; thay đổi nào là breaking; và khi buộc phải bỏ một thứ thì báo trước, đo
và gỡ nó thế nào cho đúng quy trình.

API là một **hợp đồng**. Stripe viết trong bài về versioning rằng họ giữ tương thích với mọi phiên
bản API kể từ khi công ty ra đời năm 2011, và ví API như lưới điện: đã cắm vào thì phải chạy
không gián đoạn lâu nhất có thể.

#### Ba cách đánh version

*Breaking change* là thay đổi làm client đang chạy bị lỗi (hoặc âm thầm sai). *Versioning* cho
phép client cũ tiếp tục dùng hành vi cũ trong khi bản mới ra đời.

| Cách | Ví dụ | Ưu | Nhược |
|---|---|---|---|
| Version trong URL | `/v1/orders` | Rõ ràng, dễ route, dễ cache, thử được bằng trình duyệt | Lên version là đổi URL; mỗi bước nhảy lớn nên nâng cấp đau như tích hợp lại |
| Header version theo ngày (kiểu Stripe) | `Stripe-Version: 2026-08-26.dahlia` | URL không đổi; mỗi account được ghim một version; nâng cấp từng bước nhỏ | Response thay đổi theo header nên cache phải khai `Vary`; khó thấy khi debug |
| Media type | `Accept: application/x.zalando.cart+json;version=2` | Đúng tinh thần content negotiation ([module 2.2](#22-ghi-đồng-thời-bulk-long-running-operation)), version theo từng resource | Ít người quen, khó thử nhanh; cache cũng phải `Vary` |

Hai cách tiếp cận đáng biết, vì chúng trái ngược nhau:

- Stripe dùng *rolling version* đặt tên theo ngày. Lần đầu một account gọi API, account được
  **ghim** vào version mới nhất lúc đó; từ đó mọi request mặc định chạy version ấy, nên không ai
  vô tình nhận breaking change. Muốn thử version khác cho một request thì gửi header
  `Stripe-Version`. Bên trong, code chỉ viết cho version mới nhất; mỗi breaking change được đóng
  gói thành một *version change module* biết cách biến response mới thành response cũ. Khi trả
  response, hệ thống "đi lùi" qua từng module cho tới version của client. Theo docs Stripe hiện
  tại, từ bản `2024-09-30.acacia` họ ra version hằng tháng **không** có breaking change, và hai lần
  mỗi năm ra một bản major (đặt tên, ví dụ Basil) mới chứa breaking change. Tên version vì thế có
  dạng `YYYY-MM-DD.<tên bản major>`.
- Zalando thì khuyên **tránh versioning** hoàn toàn: ưu tiên thay đổi tương thích; nếu không được
  thì tạo resource mới hoặc service mới. Khi bắt buộc phải version, guideline của họ yêu cầu dùng
  media type versioning và cấm version trong URL (lý do: URL version buộc client chờ provider
  deploy, và làm phức tạp các liên kết giữa service).

Trên thực tế, URL version (`/v1`) vẫn phổ biến nhất vì đơn giản, và chính Stripe cũng có `/v1`
trong path. Điều mọi nguồn đồng ý: mục tiêu là **hiếm khi phải tăng version**, bằng cách thiết kế
để phần lớn thay đổi không breaking.

⚠️ Khi response thay đổi theo header (`Stripe-Version`, `Accept`), header đó phải có trong `Vary`
(module 2.2), nếu không CDN có thể trả response của version này cho client version khác.

#### Thay đổi nào là breaking

Google AIP-180 chia tương thích làm ba loại, và một thay đổi phải giữ được cả ba:

1. *Source compatibility*: code viết cho bản cũ vẫn compile được với client library mới.
2. *Wire compatibility*: client cũ vẫn nói chuyện đúng với server mới (format gửi/nhận khớp).
3. *Semantic compatibility*: client cũ vẫn nhận được đúng điều mà một lập trình viên hợp lý mong
   đợi. Đây là loại khó nhất vì cần phán đoán.

Bảng tổng hợp từ AIP-180 và Zalando:

| Thay đổi | Phân loại | Vì sao, cách làm an toàn |
|---|---|---|
| Thêm endpoint mới | Không breaking | Client cũ không gọi nó |
| Thêm field optional vào response | Không breaking, **nếu** client là tolerant reader | Client deserialize chặt (ném lỗi khi gặp field lạ) vẫn vỡ |
| Thêm field **bắt buộc** vào request | Breaking | Client cũ không gửi field đó. Thêm dạng optional với mặc định bằng hành vi cũ |
| Xoá field, đổi tên field | Breaking | AIP-180: đổi tên tương đương "xoá rồi thêm". Thêm field mới, giữ field cũ (expand-contract bên dưới) |
| Đổi kiểu field (`int` thành `string`, `bool` thành object) | Breaking | Stripe từng thay `verified` (bool) bằng `status` (string) và coi đó là breaking. Thêm field mới |
| Siết validation input (tên từ 255 xuống 100 ký tự, thêm regex) | Breaking | Request trước hợp lệ giờ bị `422` |
| Nới giới hạn độ dài string trong **response** | Có thể breaking | AIP-180: client có thể lưu vào cột DB có độ dài cố định; coi như không tương thích |
| Đổi format giá trị (IPv4 thành có cả IPv6, đổi thuật toán sinh ID) | Breaking | AIP-180 nêu đúng ví dụ `ip_address` |
| Đổi giá trị mặc định (sắp xếp mặc định, page size mặc định, giá trị mặc định khi tạo) | Breaking theo AIP-180 | Client ngầm phụ thuộc hành vi mặc định dù tài liệu không hứa |
| Đổi cách serialize field mặc định (trước vắng mặt, giờ luôn có) | Breaking theo AIP-180 | Client có thể dựa vào việc field có hay không có |
| Đổi status code hoặc format lỗi | Breaking | Client rẽ nhánh theo status và đọc body lỗi |
| Thêm giá trị enum trong **request** | Không breaking | Client cũ không gửi giá trị mới |
| Thêm giá trị enum trong **response** | Có thể breaking | Client `switch` không có nhánh `default` sẽ lỗi. Zalando: output enum không được mở rộng, trừ khi đã khai là *extensible enum* |

⚠️ Tệ nhất là đổi **ý nghĩa** của field mà giữ nguyên tên và kiểu, ví dụ `amount` từ đồng sang
nghìn đồng, hay `customer_number` thành `customer_id` (Zalando nêu ví dụ này). Không có lỗi nào
xuất hiện, chỉ có số sai chảy vào báo cáo và hoá đơn.

Zalando còn có quy tắc hữu ích theo hướng dữ liệu (nhìn từ phía server):

- Schema chỉ dùng cho **input**: được thêm field optional, được biến field bắt buộc thành optional,
  được mở rộng enum; không được làm ngược lại.
- Schema chỉ dùng cho **output**: được thêm field (kể cả luôn có), được biến optional thành luôn có,
  được thu hẹp enum; không được mở rộng enum.
- Schema dùng cả hai chiều (trường hợp phổ biến): chỉ làm những gì hợp lệ ở **cả hai** chiều, tức
  là chỉ thêm field optional.
- Luôn trả JSON object ở cấp ngoài cùng, không trả array trần: object thêm được field (ví dụ thêm
  thông tin pagination sau này) mà không breaking.

#### Mobile app là trường hợp khó nhất

- Web: deploy xong là mọi user chạy bản mới (sau khi tải lại trang).
- Mobile: bản cũ nằm trên máy người dùng nhiều tháng, nhiều năm; người dùng tắt tự cập nhật, máy
  cũ không lên được OS mới. Bạn không thể "deploy" client.

Hệ quả thực hành:

1. Giữ hành vi cũ rất lâu. Coi mỗi bản app đã phát hành là một client riêng cần được hỗ trợ.
2. App gửi version của mình trong mọi request (ví dụ header `X-App-Version` hoặc trong
   `User-Agent`), để server đo được còn bao nhiêu request từ bản cũ.
3. Có cơ chế *force update*: server trả về phiên bản tối thiểu được hỗ trợ; app thấp hơn thì hiện
   màn hình bắt cập nhật. Cơ chế này phải có **từ bản đầu tiên**, vì bản không có nó thì không bao
   giờ ép được.
4. Test tương thích: chạy bộ test của các bản app cũ còn đang được hỗ trợ trên API mới
   (*consumer-driven contract*, module 3.4).

#### Tolerant reader

*Tolerant reader* là nguyên tắc Martin Fowler đặt tên (2011), dựa trên *Postel's Law*: "be
conservative in what you do, be liberal in what you accept from others". Áp cho client đọc API:

- Chỉ đọc những field mình cần, bỏ qua mọi thứ còn lại.
- Giả định tối thiểu về cấu trúc.
- Gom code đọc payload vào **một chỗ** (một DTO, *data transfer object*), để phần còn lại của app
  không phụ thuộc trực tiếp vào hình dạng JSON.
- Fowler chỉ ra cách làm hỏng điển hình: sinh class từ schema rồi bind chặt, đến khi provider thêm
  một field là client vỡ, dù thêm field "lẽ ra không phải breaking change".

Zalando biến điều này thành quy tắc bắt buộc cho client:

- Bỏ qua field lạ, nhưng đừng xoá chúng nếu cần gửi lại trong `PUT`.
- Chuẩn bị cho enum có giá trị mới: có hành vi mặc định cho giá trị lạ (ví dụ hiển thị "Không rõ").
  Vì thế không map thẳng vào enum đóng của ngôn ngữ (Java `enum`, Swift `enum` không có case
  dự phòng).
- Chuẩn bị cho status code chưa được liệt kê: xử lý theo nhóm của nó (Zalando dẫn RFC 9110: mã lạ
  được coi như mã `x00` cùng nhóm, ví dụ một `2xx` lạ coi như `200`).

Phía server:

- Ghi rõ trong tài liệu những enum nào có thể được mở rộng. Zalando dùng tiền tố mô tả
  "[Extensible enum]" và liệt kê giá trị bằng `examples` thay vì `enum` của JSON Schema (vì `enum`
  theo định nghĩa là tập đóng). Guideline này trước tháng 10/2025 dùng extension
  `x-extensible-enum`.
- ⚠️ Bất đối xứng có chủ đích: client nên dễ dãi khi **đọc**, còn server nên chặt khi **nhận**.
  Zalando khuyên server trả `400` cho field lạ trong input thay vì âm thầm bỏ qua, vì lỗi gõ nhầm
  tên field sẽ bị nuốt mất, và field bị bỏ qua hôm nay có thể xung đột với field cùng tên được
  thêm sau này.

#### Expand–contract: đổi field mà không breaking

Ví dụ: `amount` đang là số thực (`199.5`), cần đổi sang số nguyên minor unit. Đổi kiểu tại chỗ là
breaking. Làm theo *expand–contract* (còn gọi *parallel change*):

1. **Expand** (mở rộng): thêm field mới `amount_minor` (`19950`) bên cạnh `amount` cũ. Không xoá,
   không đổi gì của field cũ.
2. **Chạy song song**: trả **cả hai** field. Nếu field có trong request, nhận cả hai; định nghĩa rõ
   khi client gửi cả hai mà mâu thuẫn thì bên nào thắng (AIP-180 yêu cầu phải nói rõ điều này).
   Đánh dấu `amount` là `deprecated: true` trong OpenAPI kèm mô tả chuyển đổi.
3. **Đo**: log xem client nào còn **gửi** `amount`. Chiều response khó đo hơn (server không biết
   client có đọc field hay không), nên dựa vào version app / API key: bản app nào đã chuyển sang
   `amount_minor`, còn bao nhiêu request từ bản chưa chuyển.
4. **Contract** (thu hẹp): khi lượng dùng về 0, hoặc hết hạn đã cam kết (kèm header `Sunset`, bên
   dưới), xoá `amount`.

Cùng một khuôn áp cho schema DB (thêm cột, ghi cả hai, backfill, chuyển đọc, xoá cột cũ:
[03-database-sql.md, module 3.3](03-database-sql.md#33-thay-đổi-schema-online-và-migration-không-downtime)),
cho endpoint (thêm endpoint mới, chuyển client, gỡ endpoint cũ) và cho event trong queue.

#### Deprecation: ngừng một endpoint đúng cách

*Deprecation* là thông báo "thứ này sắp bị bỏ, đừng dùng mới, hãy chuyển đi". Nó **không** đổi hành
vi: RFC 9745 nói rõ endpoint deprecated vẫn hoạt động như trước. *Sunset* là thời điểm endpoint
thật sự ngừng phục vụ. RFC 8594 mô tả hai giai đoạn: (1) không còn là bản khuyến nghị nhưng vẫn
chạy; (2) bị gỡ. Header `Sunset` chỉ dành cho giai đoạn 2.

Quy trình (tổng hợp từ Zalando):

1. Đánh dấu `deprecated: true` trong OpenAPI, ghi rõ thay bằng gì và cách chuyển.
2. Thông báo trước cho client, kèm hạn sunset. Với đối tác bên ngoài, Zalando yêu cầu thống nhất
   trước khoảng thời gian tối thiểu giữa lúc báo deprecated và lúc sớm nhất có thể sunset.
3. Gắn header `Deprecation` (và `Sunset` nếu đã có hạn) vào mọi response của phần bị deprecated.
4. Đo client nào còn gọi, theo API key hoặc version app; nhắc riêng những client còn lại.
5. Chỉ gỡ khi hết người dùng hoặc tới hạn đã thống nhất. Zalando nhấn mạnh: gắn header thôi
   **chưa phải** là đã có sự đồng ý của client.

Các header chuẩn:

| Header | Chuẩn | Cú pháp | Ý nghĩa |
|---|---|---|---|
| `Deprecation` | RFC 9745 (Standards Track, 3/2025) | `Deprecation: @1790812800`: một *Date* theo Structured Field Values (RFC 9651), là Unix timestamp có `@` ở đầu | Thời điểm resource bị (hoặc đã bị) deprecated. Có thể ở tương lai hoặc quá khứ |
| `Sunset` | RFC 8594 (Informational, 5/2019) | `Sunset: Thu, 01 Apr 2027 00:00:00 GMT`: một *HTTP-date* (định dạng ngày chuẩn của HTTP, luôn là GMT) | Thời điểm resource dự kiến ngừng phản hồi. Nên ở tương lai; ở quá khứ thì hiểu là "có thể ngừng bất cứ lúc nào" |
| `Link` | RFC 9745 section 3 | `Link: <https://docs.example.com/migrate-v2>; rel="deprecation"; type="text/html"` | Trỏ tới tài liệu về việc deprecation, hướng dẫn chuyển đổi |

- ⚠️ Hai header dùng **hai định dạng thời gian khác nhau** vì lý do lịch sử (RFC 9745 và Zalando
  đều ghi chú điều này). Viết `Deprecation: Thu, 01 Oct 2026 ...` là sai cú pháp.
- ⚠️ RFC 9745: thời điểm trong `Sunset` **không được sớm hơn** thời điểm trong `Deprecation`.
- Cả hai chỉ là **gợi ý** (*hint*): client không đọc header vẫn chạy bình thường cho tới lúc bị gỡ.
  Vì vậy header không thay được việc chủ động liên hệ client.
- Zalando khác RFC ở hai điểm nhỏ: họ không khuyến khích dùng `Link rel="deprecation"` (cho rằng
  tài liệu trong OpenAPI là đủ), và họ còn cho phép giá trị `Deprecation: true`; RFC 9745 bản chính
  thức chỉ định nghĩa giá trị dạng Date.
- Sau sunset: RFC 8594 không quy định status cụ thể (chỉ nói có thể là `4xx`, `3xx`, hoặc không kết
  nối được). Lựa chọn rõ ràng nhất là `410 Gone` (RFC 9110: resource không còn và nhiều khả năng
  là vĩnh viễn) kèm body chỉ tới endpoint thay thế, thay vì `404` khiến client tưởng gọi sai URL.

Ví dụ: endpoint `GET /v1/orders` sẽ ngừng sau 6 tháng tính từ 01/10/2026:

```
HTTP/1.1 200 OK
Deprecation: @1790812800
Sunset: Thu, 01 Apr 2027 00:00:00 GMT
Link: <https://docs.example.com/migrate-v2>; rel="deprecation"; type="text/html"
Content-Type: application/json
```

(`1790812800` là `2026-10-01T00:00:00Z`; kiểm bằng `date -u -r 1790812800` trên macOS hoặc
`date -u -d @1790812800` trên Linux.)

Trên Laravel, một middleware gắn header và ghi log để đo:

```php
<?php
declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Log;
use Symfony\Component\HttpFoundation\Response;

final class MarkDeprecated
{
    private const DEPRECATED_AT = 1790812800;                        // 2026-10-01T00:00:00Z
    private const SUNSET        = 'Thu, 01 Apr 2027 00:00:00 GMT';
    private const DOC_URL       = 'https://docs.example.com/migrate-v2';

    public function handle(Request $request, Closure $next): Response
    {
        if (time() >= strtotime(self::SUNSET)) {
            return response()->json([
                'message' => 'This endpoint has been removed. See ' . self::DOC_URL,
            ], 410);
        }

        Log::info('deprecated_endpoint_called', [
            'route'       => $request->route()?->uri(),
            'client_id'   => $request->user()?->getAuthIdentifier(),
            'app_version' => $request->header('X-App-Version'),
        ]);

        $response = $next($request);
        $response->headers->set('Deprecation', '@' . self::DEPRECATED_AT);
        $response->headers->set('Sunset', self::SUNSET);
        $response->headers->set('Link', '<' . self::DOC_URL . '>; rel="deprecation"; type="text/html"');

        return $response;
    }
}
```

Log `deprecated_endpoint_called` gom theo `client_id` và `app_version` chính là dữ liệu cho bước
"đo" ở trên. Phía client, Zalando khuyên dựng cảnh báo khi response có header `Deprecation` hoặc
`Sunset`, để team client biết trước khi quá muộn.

**Tóm tắt nhanh**

- Ba cách version: URL (`/v1`, phổ biến nhất), header theo ngày kiểu Stripe (ghim version theo
  account, đi lùi qua version change module), media type (Zalando). Mục tiêu thật là hiếm khi phải
  tăng version.
- Breaking: thêm field bắt buộc vào request, xoá/đổi tên/đổi kiểu field, siết validation, đổi
  format giá trị, đổi giá trị mặc định, đổi status/format lỗi. Tệ nhất là đổi ý nghĩa mà giữ tên.
- Thêm enum trong response và thêm field chỉ an toàn khi client là tolerant reader; server ghi rõ
  enum nào có thể mở rộng. Client dễ dãi khi đọc, server chặt khi nhận.
- Đổi field: expand (thêm field mới), chạy song song, đo, contract (xoá cũ). Mobile cần force
  update từ bản đầu và gửi version app trong mọi request.
- `Deprecation: @<unix>` (RFC 9745) và `Sunset: <HTTP-date>` (RFC 8594), Sunset không sớm hơn
  Deprecation; sau hạn trả `410 Gone`.

**Nguồn**: [RFC 9745: The Deprecation HTTP Response Header Field](https://www.rfc-editor.org/rfc/rfc9745) ·
[RFC 8594: The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594) ·
[Google AIP-180: Backwards compatibility](https://google.aip.dev/180) ·
[Stripe: APIs as infrastructure: future-proofing Stripe with versioning](https://stripe.com/blog/api-versioning) ·
[Stripe API Reference: Versioning](https://docs.stripe.com/api/versioning) ·
[Zalando: Compatibility](https://opensource.zalando.com/restful-api-guidelines/#compatibility) ·
[Zalando: Deprecation](https://opensource.zalando.com/restful-api-guidelines/#deprecation) ·
[Martin Fowler: Tolerant Reader](https://martinfowler.com/bliki/TolerantReader.html)

---

### 3.2 GraphQL

Module này trả lời: GraphQL khác REST ở mô hình nào, vì sao nó sinh ra N+1 và cách DataLoader gom
lại, vì sao lỗi hay "trốn" sau status 200, và làm sao bảo vệ một GraphQL public khỏi query phá hoại.

#### GraphQL là gì

REST xoay quanh *resource*: mỗi thứ có một URL, và URL chính là định danh. GraphQL xoay quanh một
*đồ thị thực thể* (entity graph): các object nối với nhau qua field. Vì thực thể không được định
danh bằng URL, toàn bộ API chỉ có **một endpoint**, thường là `/graphql`, và client gửi một
*document* mô tả chính xác những field mình muốn.

```graphql
query OrdersPage {
  orders(first: 10) {
    id
    total
    customer { name }
  }
}
```

Response có hình dạng giống hệt query, nằm dưới khoá `data`:

```json
{ "data": { "orders": [ { "id": "10", "total": 100, "customer": { "name": "An" } } ] } }
```

Các khái niệm nền:

- *Schema*: hợp đồng có kiểu của API, viết bằng *SDL* (Schema Definition Language). Điểm vào là ba
  *root type*: `Query` (đọc), `Mutation` (ghi), `Subscription` (nhận dữ liệu đẩy về khi có thay
  đổi, thường chạy trên WebSocket hoặc SSE chứ không phải HTTP request/response thường).

  ```graphql
  type Query    { orders(first: Int!, after: String): OrderConnection! }
  type Mutation { cancelOrder(id: ID!): CancelOrderPayload! }
  type Order    { id: ID!  total: Int!  status: OrderStatus!  customer: Customer }
  enum OrderStatus { PENDING PAID CANCELLED }
  ```
- *Nullability*: trong GraphQL mọi field mặc định là **nullable**, `!` mới là non-null. Lý do: một
  field có thể lỗi riêng (DB con chết, không có quyền) mà phần còn lại vẫn trả được. Nếu một field
  non-null bị lỗi thì null "lan lên" field cha gần nhất cho phép null. Khai `!` bừa bãi làm một lỗi
  nhỏ xoá mất cả nhánh dữ liệu.
- *Introspection*: client hỏi được chính server "schema gồm những type, field nào" qua các meta
  field `__schema`, `__type`. Nhờ đó có GraphiQL tự gợi ý, có công cụ sinh code type-safe cho client.
- *Resolver*: mỗi field của mỗi type có một hàm lấy giá trị. Thực thi bắt đầu từ field của root type,
  đi xuống từng tầng cho tới khi gặp scalar hoặc enum. Resolver nhận bốn tham số: object cha, arguments,
  *context* (thứ dùng chung cả request: user đang đăng nhập, kết nối DB, loader) và info.
- Field của `Query` có thể được resolve song song; field gốc của `Mutation` chạy **tuần tự** theo
  thứ tự viết, vì chúng có side effect.
- Tiến hoá không version: vì client chỉ nhận field đã xin, thêm type hoặc field mới không làm vỡ ai.
  Field cũ đánh dấu `@deprecated(reason: "...")` rồi gỡ khi không còn ai dùng (cùng tinh thần
  expand-contract ở module 3.1). Xoá field hay đổi kiểu vẫn là breaking như REST.

HTTP transport (theo hướng dẫn *GraphQL over HTTP*, bản draft đang được các thư viện dần tuân theo):

- Server phải nhận `POST` với body JSON `{"query": "...", "operationName": "...", "variables": {...}}`;
  có thể nhận thêm `GET` cho query (`/graphql?query={me{name}}`). Mutation không bao giờ đi qua `GET`.
- Client nên gửi `Accept: application/graphql-response+json`, kèm `application/json` nếu phải nói
  chuyện với server cũ.

#### Lỗi trả 200

Response GraphQL có tối đa ba khoá top-level: `data`, `errors`, `extensions`. Có ba loại lỗi:

| Loại | Khi nào | Response |
|---|---|---|
| Request error | Sai cú pháp, field không tồn tại, sai kiểu variable. Phát hiện trước khi chạy resolver | Có `errors`, **không có** `data` |
| Field error | Một resolver ném lỗi, hoặc trả null cho field non-null | Có `errors` và `data` một phần (*partial response*): field nào lấy được vẫn trả |
| Network error | Timeout, lỗi TLS | Không phải chuyện của GraphQL |

Ví dụ partial response (dữ liệu minh hoạ, dựa theo ví dụ xoá hai starship trên graphql.org):

```json
{
  "data": { "firstShip": "3001", "secondShip": null },
  "errors": [ { "message": "No such starship", "path": ["secondShip"], "locations": [{"line": 3, "column": 3}] } ]
}
```

Status code:

- Theo GraphQL over HTTP: hễ `data` có mặt và khác `null` thì server phải trả `2xx`, **kể cả khi có
  `errors`**, vì đây là "thành công một phần" chứ không phải request lỗi. (Bản draft hiện tại còn gợi
  ý một mã riêng, `294`, cho trường hợp có cả `data` lẫn `errors`; draft vẫn đang đổi nên kiểm lại
  trước khi dựa vào.)
- Với media type `application/graphql-response+json`: response không có `data` (request error) phải
  trả `4xx`/`5xx`. Theo bản draft hiện tại, document không parse được trả `400`, không qua
  validation trả `422`.
- Với `application/json` (kiểu cũ, còn rất phổ biến), nhiều server trả `200` cho gần như mọi thứ.

⚠️ Hệ quả: dashboard đếm lỗi theo status code sẽ không thấy phần lớn lỗi GraphQL. Phải log và đếm
theo mảng `errors` (theo `path`, theo `extensions.code`), và gắn tên operation vào metric.

Hai cách báo lỗi, dùng cho hai mục đích:

- `errors` top-level cho lỗi ngoại lệ: DB timeout, query sai cú pháp, thiếu token.
- *Errors-as-data* cho lỗi nghiệp vụ dự kiến được: đưa lỗi vào schema để client thấy qua
  introspection và xử lý có kiểu.

  ```graphql
  type CancelOrderPayload { order: Order  userErrors: [UserError!]! }
  type UserError { message: String!  field: [String!]  code: UserErrorCode! }
  enum UserErrorCode { ALREADY_SHIPPED NOT_FOUND }
  ```

⚠️ Ở production, che bớt chi tiết lỗi: message kiểu "Did you mean `totalAmount`?" giúp kẻ tấn công
đoán ra schema kể cả khi đã tắt introspection; stack trace của field error lộ thông tin server.

#### N+1 và DataLoader

Vì mỗi field có một resolver riêng, query `orders(first: 10) { customer { name } }` chạy như sau
nếu viết ngây thơ:

```
resolver Query.orders        → 1 query: SELECT * FROM orders LIMIT 10
resolver Order.customer × 10 → 10 query: SELECT * FROM customers WHERE id = ?
                               ─────────
                               11 query  (1 + N)
```

Mỗi query đều nhanh nên không lên slow log, nhưng số query tăng theo số item và theo độ sâu lồng.

*DataLoader* (thư viện gốc của GraphQL Foundation cho JavaScript, ý tưởng có từ "Loader" ở Facebook)
sửa bằng hai cơ chế:

1. *Batching*: resolver không truy vấn ngay mà gọi `loader.load(customerId)` và nhận về một lời hứa
   (Promise ở JS, `Deferred` ở graphql-php). Loader gom mọi key được xin trong cùng một lượt thực thi.
2. Khi lượt đó xong, loader gọi *batch function* một lần với cả danh sách key, tức một query
   `WHERE id IN (...)`.
3. *Caching*: key đã load trong request thì lần sau trả từ bộ nhớ, không vào batch nữa.

Ràng buộc của batch function: mảng kết quả phải **cùng độ dài và cùng thứ tự** với mảng key. DB trả
thứ tự tuỳ ý và bỏ qua key không tồn tại, nên batch function phải tự sắp lại và điền `null` hoặc
lỗi vào chỗ thiếu.

⚠️ Cache của DataLoader là cache theo request, không thay Redis. Tạo loader mới khi request bắt
đầu (thường gắn vào context) và bỏ khi request kết thúc. Dùng chung một instance giữa các user thì
user A có thể nhận object đã load theo quyền của user B. Với PHP-FPM điều này tự nhiên đúng vì mỗi
request là một lần chạy mới; với process sống lâu (Octane, RoadRunner) phải cẩn thận không để
loader thành singleton.

⚠️ Trong cùng request, sau một mutation phải xoá key đó khỏi cache (`loader.clear(id)` ở bản JS),
nếu không lần load sau trả dữ liệu cũ.

Mô phỏng bằng PHP thuần để thấy số query (không cần thư viện, chạy `php n1.php`):

```php
<?php
declare(strict_types=1);

final class FakeDb
{
    public int $queries = 0;
    /** @var array<int, string> */
    private array $customers = [1 => 'An', 2 => 'Bình', 3 => 'Chi'];

    /** @return list<array{id: int, customer_id: int}> */
    public function orders(): array
    {
        $this->queries++;
        return [
            ['id' => 10, 'customer_id' => 1],
            ['id' => 11, 'customer_id' => 2],
            ['id' => 12, 'customer_id' => 1],
            ['id' => 13, 'customer_id' => 3],
        ];
    }

    /** @param list<int> $ids  @return array<int, string> */
    public function customersByIds(array $ids): array
    {
        $this->queries++; // một câu SELECT ... WHERE id IN (...)
        return array_intersect_key($this->customers, array_flip($ids));
    }
}

final class CustomerLoader
{
    /** @var array<int, true> */
    private array $pending = [];
    /** @var array<int, string> */
    private array $cache = [];

    public function __construct(private FakeDb $db) {}

    /** Trả về thunk: chỉ khi được gọi mới thực sự chạy batch. */
    public function load(int $id): Closure
    {
        if (!array_key_exists($id, $this->cache)) {
            $this->pending[$id] = true;
        }
        return function () use ($id): string {
            if ($this->pending !== []) {
                $this->cache += $this->db->customersByIds(array_keys($this->pending));
                $this->pending = [];
            }
            return $this->cache[$id];
        };
    }
}

// Cách ngây thơ: mỗi order một query
$db = new FakeDb();
foreach ($db->orders() as $o) {
    $db->customersByIds([$o['customer_id']]);
}
echo "Ngây thơ: {$db->queries} query\n";       // Ngây thơ: 5 query

// Cách batch: lượt 1 gom key, lượt 2 mới lấy giá trị
$db = new FakeDb();
$loader = new CustomerLoader($db);
$thunks = [];
foreach ($db->orders() as $o) {
    $thunks[$o['id']] = $loader->load($o['customer_id']);
}
foreach ($thunks as $orderId => $thunk) {
    $name = $thunk();
    echo "{$orderId}: {$name}\n";               // 4 dòng: 10: An / 11: Bình / 12: An / 13: Chi
}
echo "Batch: {$db->queries} query\n";          // Batch: 2 query
```

graphql-php làm theo cùng ý tưởng: resolver trả `GraphQL\Deferred` thay vì giá trị, executor tiếp
tục đi qua các field khác (các loader nhận thêm key), và chỉ gọi callback của `Deferred` khi cần giá
trị, lúc đó loader chạy batch một lần cho mọi key đã gom.

#### Bảo vệ server khỏi query phá hoại

Client tự viết query, nên một request duy nhất có thể đòi server làm rất nhiều việc. Kể cả khi đã
sửa N+1, query lồng vòng vẫn nở theo cấp số nhân:

```graphql
query { orders(first: 100) { customer { orders(first: 100) { customer { orders(first: 100) { id } } } } } }
```

Các lớp phòng thủ (*demand control*), từ thô tới tinh:

1. Phân trang bắt buộc mọi list có thể lớn, có trần `first` tối đa. Chuẩn phổ biến là *connection*
   của Relay: `edges { cursor node }`, `pageInfo { endCursor hasNextPage }`, cursor là chuỗi mờ
   (thường base64) để client không phụ thuộc cách server phân trang.
2. Giới hạn *depth* (độ sâu lồng). Nên đặt giới hạn riêng, nhỏ hơn, cho độ sâu của list lồng list.
3. Giới hạn *breadth* và batch: số field top-level, số *alias* (`f1: friends(limit: 1) ... f100:
   friends(limit: 100)` nông nhưng vẫn là 100 lần gọi), số operation trong một request.
4. *Query complexity* (cost): gán trọng số cho field, ví dụ field list tốn `childrenComplexity ×
   limit`. Tính tổng trước khi chạy, vượt ngưỡng thì từ chối.
5. *Rate limit theo cost*: mỗi client có ngân sách điểm mỗi khoảng thời gian, trừ theo cost thực của
   request thay vì đếm số request (một request GraphQL có thể rẻ hoặc đắt gấp nghìn lần).
6. *Trusted documents* (tên cũ: persisted queries): chỉ áp dụng khi mọi client là của mình. Lúc
   build, client đăng ký các document vào allowlist, mỗi cái có id (thường là hash). Lúc chạy, client
   gửi id; server chỉ chạy id đã biết. ⚠️ Không dùng được cho API public vì không biết trước query
   của bên thứ ba.
   Phân biệt với *automatic persisted queries* (APQ): client gửi hash, server chưa biết hash thì client
   gửi kèm cả query để server ghi nhớ. APQ chỉ để tiết kiệm băng thông và cho phép `GET`, **không**
   chặn được query tuỳ ý, vì ai cũng đăng ký được query mới.

Thêm vào đó là các biện pháp của mọi HTTP API: HTTPS, timeout, giới hạn kích thước body, và ở PHP
là `max_execution_time`, `memory_limit`, `post_max_size`.

Tắt introspection ở production chỉ là "an ninh nhờ che giấu": có ích cho API nội bộ, nhưng không
đủ nếu đứng một mình. Allowlist và authorization mới là lớp bảo vệ thật.

*Authorization* (kiểm quyền):

- Xác thực (*authentication*) làm ở middleware trước khi vào GraphQL, rồi đặt user vào context.
- Kiểm quyền làm **trong lúc thực thi**, ở từng type và field, vì một query có thể chạm tới hàng
  chục loại object. Không có "endpoint riêng" để gắn middleware như REST.
- graphql.org khuyên đặt logic quyền ở tầng business (repository, policy) và resolver chỉ gọi vào:
  nếu viết thẳng trong resolver thì REST, job, GraphQL mỗi nơi một bản sao và sẽ lệch nhau.
- Vì kiểm quyền theo field, một field bị từ chối có thể thành `null` kèm lỗi trong khi phần còn lại
  vẫn trả về (partial response).

#### Caching

Với REST, URL là khoá cache toàn cục, `GET` cache được ở trình duyệt và CDN. GraphQL mất cả hai: mọi
thứ là `POST /graphql` với body khác nhau, và không có URL nào định danh một object.

Các cách bù:

- *Normalized cache* phía client (Apollo Client, Relay): client tách response thành từng object, lưu
  theo khoá `__typename + id`, nên query khác nhau cùng chạm một object sẽ dùng chung và cập nhật
  cùng lúc. Điều kiện: schema phải có id **duy nhất toàn cục** (hoặc client tự ghép `__typename` với
  id). Server chưa có thì thường ghép tên type với id rồi base64 cho mờ.
- Cache theo request bằng DataLoader (ở trên), và cache kết quả resolver ở tầng business như mọi
  ứng dụng khác.
- `GET` cho query cộng với persisted/trusted documents: query dài vượt giới hạn độ dài URL, nên
  client gửi hash thay cho cả document; request `GET` ngắn, lặp lại được nên CDN cache được (với
  header cache phù hợp, và dữ liệu nhạy cảm phải `private` hoặc không cache).
- Response JSON nén rất tốt, nên bật gzip/brotli.

#### Trong PHP

- `webonyx/graphql-php`: thư viện nền, port của graphql-js. Có sẵn các validation rule chống lạm
  dụng, **đều tắt mặc định**:
  - `QueryDepth` (ví dụ `new QueryDepth(10)`); tài liệu cho biết introspection query mặc định sâu 7.
  - `QueryComplexity`: mỗi field mặc định 1 điểm, tuỳ biến bằng hàm `complexity` trên field.
  - `DisableIntrospection`.
  - Ngoài ra parser có giới hạn đệ quy (tài liệu hiện ghi mặc định 256) để query lồng quá sâu không
    làm tràn stack PHP.
- *Lighthouse*: framework GraphQL cho Laravel, xây trên graphql-php, kiểu *schema-first*: viết file
  `.graphql`, gắn hành vi bằng directive.
  - Quan hệ Eloquent khai bằng `@belongsTo`, `@hasMany`...; Lighthouse tự gom các quan hệ này thành
    batch thay vì lazy load từng dòng.
  - `@with(relation: "...")` để eager load một quan hệ chỉ dùng nội bộ cho field khác, không trả ra.
  - Nguồn không phải Eloquent (service bên ngoài): tự viết batch loader, lấy instance dùng chung theo
    path qua `BatchLoaderRegistry::instance($resolveInfo->path, ...)`, resolver trả `GraphQL\Deferred`.
  - Bảo mật cấu hình ở `config/lighthouse.php`, khoá `security`: `max_query_complexity`,
    `max_query_depth`, `disable_introspection`. Trong file config gốc hai giới hạn đầu là
    `DISABLED`, và `pagination.max_count` là `null` (không giới hạn). ⚠️ Cài xong mà không chỉnh là
    API public mở toang.
  - `@complexity` để tuỳ biến điểm của field; `@guard` và họ `@can*` để xác thực, kiểm quyền theo
    field bằng guard và policy của Laravel.
- N+1 ở tầng Eloquent (lazy loading, `preventLazyLoading`) đã viết ở
  [03-database-sql.md, module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel).

#### Đào sâu (🔴)

*Federation*: ghép nhiều *subgraph* (mỗi team một service, một schema) thành một schema thống nhất
sau một *gateway*. Gateway tách query thành phần cho từng subgraph, gọi, rồi ghép kết quả. Type dùng
chung được khai qua khoá (ví dụ `type Product @key(fields: "id")` theo kiểu Apollo Federation).
*Schema stitching* là cách cũ hơn, ghép schema ở gateway bằng cấu hình. Cái giá: cần gateway,
*schema registry*, đội vận hành riêng. Chính Meta vẫn dùng một GraphQL monolith; graphql.org khuyên
bắt đầu monolith và chỉ federate khi cấu trúc tổ chức thật sự cần. GraphQL Foundation đang chuẩn
hoá federation qua Composite Schema Working Group.

**Tóm tắt nhanh**
- Một endpoint, client chọn field, schema có kiểu; mọi field mặc định nullable; mutation gốc chạy
  tuần tự.
- Có `data` khác null là `2xx` dù có `errors`: monitoring phải đếm mảng `errors`, không đếm status.
- N+1 do resolver theo field; DataLoader gom key trong một lượt thành một `IN (...)`, cache theo
  request, không dùng chung giữa user.
- Chống query phá hoại: phân trang có trần, depth, breadth/alias, complexity, rate limit theo cost;
  trusted documents nếu client là của mình. Graphql-php và Lighthouse tắt các giới hạn này mặc định.
- Kiểm quyền theo field ở tầng business; cache chủ yếu ở client (normalized theo id toàn cục) và
  `GET` + persisted query cho CDN.

**Nguồn**: [GraphQL Learn](https://graphql.org/learn/) ·
[Execution](https://graphql.org/learn/execution/) · [Response](https://graphql.org/learn/response/) ·
[Serving over HTTP](https://graphql.org/learn/serving-over-http/) ·
[Authorization](https://graphql.org/learn/authorization/) ·
[Pagination](https://graphql.org/learn/pagination/) · [Schema Design](https://graphql.org/learn/schema-design/) ·
[Error Handling](https://graphql.org/learn/error-handling/) · [Caching](https://graphql.org/learn/caching/) ·
[Performance](https://graphql.org/learn/performance/) · [Security](https://graphql.org/learn/security/) ·
[Federation](https://graphql.org/learn/federation/) ·
[graphql/dataloader README](https://github.com/graphql/dataloader) ·
[Lighthouse: The N+1 Query Problem](https://lighthouse-php.com/master/performance/n-plus-one.html) ·
[Lighthouse: Resource Exhaustion](https://lighthouse-php.com/master/security/resource-exhaustion.html) ·
[Lighthouse: Directives](https://lighthouse-php.com/master/api-reference/directives.html) ·
[graphql-php: Security](https://webonyx.github.io/graphql-php/security/)

---

### 3.3 gRPC và Protobuf

Module này trả lời: gRPC hoạt động thế nào trên HTTP/2, deadline và status code của nó khác HTTP ra
sao, sửa file `.proto` thế nào để không phá client cũ, vì sao load balancing gRPC hay bị lệch, và khi
nào chọn REST, GraphQL hay gRPC.

#### gRPC là gì

*RPC* (Remote Procedure Call) là ý tưởng "gọi hàm ở máy khác như gọi hàm local". *gRPC* là framework
RPC mã nguồn mở, mặc định dùng *Protocol Buffers* (Protobuf) làm *IDL* (Interface Definition
Language, ngôn ngữ mô tả interface) và làm định dạng dữ liệu.

Quy trình làm việc:

1. Viết file `.proto` mô tả service (các method) và message (kiểu dữ liệu).
2. Chạy `protoc` (trình biên dịch Protobuf) cùng plugin gRPC để sinh code cho từng ngôn ngữ.
3. Phía server: cài đặt các method của service, chạy gRPC server. Thư viện lo giải mã request, gọi
   method, mã hoá response.
4. Phía client: dùng *stub* (đối tượng local có cùng các method). Gọi method trên stub, thư viện đóng
   gói tham số thành message, gửi đi và trả về response.

```proto
syntax = "proto3";
package shop.v1;

service OrderService {
  rpc GetOrder(GetOrderRequest) returns (Order);
  rpc WatchOrders(WatchOrdersRequest) returns (stream OrderEvent);
}

message GetOrderRequest { int64 id = 1; }

message Order {
  int64 id = 1;          // "= 1" là số field (field number), thứ thật sự đi trên dây
  OrderStatus status = 2;
  int64 total_minor = 3; // tiền tính theo đơn vị nhỏ nhất, số nguyên
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_PAID = 2;
}
```

Bốn kiểu method, phân biệt bằng từ khoá `stream`:

| Kiểu | Khai báo | Dùng khi |
|---|---|---|
| Unary | `rpc A(Req) returns (Res)` | Một request, một response, như gọi hàm thường |
| Server streaming | `rpc A(Req) returns (stream Res)` | Kết quả lớn hoặc kéo dài: đẩy dần từng phần, sự kiện |
| Client streaming | `rpc A(stream Req) returns (Res)` | Upload nhiều phần, gom số liệu rồi trả một tổng kết |
| Bidirectional | `rpc A(stream Req) returns (stream Res)` | Hai dòng độc lập, mỗi bên đọc ghi theo thứ tự tuỳ ý (chat, đồng bộ) |

gRPC đảm bảo giữ thứ tự message trong một dòng của một lần gọi.

Vì sao nhanh và chặt:

- Chạy trên HTTP/2: *multiplexing* (nhiều lời gọi song song trên một kết nối TCP), header nén,
  streaming hai chiều. Status của lời gọi gửi ở *trailer* (header ở cuối stream), nên server stream
  xong mới báo kết quả cuối được.
- Protobuf là định dạng nhị phân: mỗi field mã hoá bằng số field cộng kiểu dây (*wire type*) và giá
  trị, không mang tên field. Payload nhỏ hơn JSON và parse rẻ hơn. Số field 1 tới 15 tốn 1 byte cho
  phần tag, 16 tới 2047 tốn 2 byte, nên dành 1 tới 15 cho các field hay dùng.
- Contract chặt: client và server sinh từ cùng một file, sai kiểu là lỗi lúc biên dịch.

Các khái niệm đi kèm:

- *Metadata*: cặp key-value gửi kèm lời gọi (tương tự header), ví dụ token xác thực. Key không phân
  biệt hoa thường, không được bắt đầu bằng `grpc-` (dành cho gRPC), key có giá trị nhị phân kết
  thúc bằng `-bin`.
- *Channel*: kết nối logic tới một server (host:port), stub được tạo từ channel. Channel có trạng thái
  (ví dụ `connected`, `idle`), và nên tái sử dụng thay vì mở mới cho mỗi lời gọi.
- Client và server tự kết luận thành công hay thất bại một cách độc lập, và có thể không khớp:
  server đã gửi xong response nhưng client coi là lỗi vì tới sau deadline.

#### Deadline và status code

*Deadline* là thời điểm mà sau đó client không cần kết quả nữa. Có ngôn ngữ dùng khái niệm
*timeout* (khoảng thời gian), có ngôn ngữ dùng deadline (mốc thời gian); timeout cộng thời điểm bắt
đầu gọi là ra deadline.

⚠️ Mặc định gRPC **không đặt deadline**, tức client có thể chờ mãi. Luôn đặt deadline thực tế cho mọi
lời gọi, ước lượng từ latency mạng và thời gian xử lý rồi kiểm chứng bằng load test.

Chuyện gì xảy ra khi hết hạn:

1. Client bỏ cuộc, lời gọi lỗi với `DEADLINE_EXCEEDED`.
2. Server tự động huỷ lời gọi (status `CANCELLED`) khi deadline client đặt đã qua.
3. Nhưng code ứng dụng phía server phải **tự dừng** việc mình đã khởi động: việc dài phải định kỳ
   kiểm tra xem lời gọi đã bị huỷ chưa.
4. ⚠️ Huỷ không rollback: những gì đã ghi trước lúc huỷ vẫn nằm đó.

*Deadline propagation* (lan truyền deadline): service B nhận lời gọi từ A rồi gọi tiếp C thì lời gọi
tới C nên dùng phần thời gian còn lại của A, không đặt deadline mới dài hơn.

```
Client ──GetUserProfile (deadline 13:00:02)──► User service
  13:00:00                                       │ tốn 0,5 s
                                                 └─GetTransactionHistory (timeout 1,5 s)──► Billing
  13:00:02: client nhận DEADLINE_EXCEEDED, User service huỷ, Billing thấy bị huỷ thì dọn dẹp
```

- Khi lan truyền, gRPC đổi deadline thành timeout đã trừ phần thời gian đã trôi qua, để không bị ảnh
  hưởng khi đồng hồ hai máy lệch nhau (*clock skew*).
- Java và Go lan truyền tự động; C++ phải bật tường minh. Trong Go, deadline đi theo `context`: chỉ
  cần truyền `ctx` của request đến vào lời gọi đi.

```go
// Trích đoạn handler Go: ctx đến từ lời gọi của A, đã mang deadline.
func (s *server) GetUserProfile(ctx context.Context, req *pb.GetUserProfileRequest) (*pb.UserProfile, error) {
	// Có thể siết thêm, nhưng context con không bao giờ kéo dài hơn deadline của cha.
	ctx, cancel := context.WithTimeout(ctx, 1500*time.Millisecond)
	defer cancel()
	hist, err := s.billing.GetTransactionHistory(ctx, &pb.HistoryRequest{UserId: req.GetUserId()})
	if status.Code(err) == codes.DeadlineExceeded {
		return nil, err
	}
	// ...
	_ = hist
	return &pb.UserProfile{}, nil
}
```

*Status code*: mọi lời gọi gRPC kết thúc bằng một status gồm mã số nguyên và mô tả. gRPC có bộ mã
riêng, không dùng status HTTP. Các mã hay gặp:

| Mã | Số | Nghĩa | Gần giống HTTP |
|---|---|---|---|
| `OK` | 0 | Thành công | 200 |
| `CANCELLED` | 1 | Bị huỷ, thường do bên gọi | (499 của nginx) |
| `INVALID_ARGUMENT` | 3 | Tham số sai bất kể trạng thái hệ thống | 400 |
| `DEADLINE_EXCEEDED` | 4 | Hết hạn trước khi xong | 504 |
| `NOT_FOUND` | 5 | Không tìm thấy | 404 |
| `ALREADY_EXISTS` | 6 | Đã tồn tại | 409 |
| `PERMISSION_DENIED` | 7 | Đã biết là ai nhưng không có quyền | 403 |
| `RESOURCE_EXHAUSTED` | 8 | Hết quota, hết tài nguyên | 429 |
| `FAILED_PRECONDITION` | 9 | Hệ thống không ở trạng thái cho phép thao tác | 400/409 |
| `ABORTED` | 10 | Bị huỷ do xung đột đồng thời | 409 |
| `UNIMPLEMENTED` | 12 | Method không có hoặc không bật | 501 |
| `INTERNAL` | 13 | Lỗi nghiêm trọng bên trong | 500 |
| `UNAVAILABLE` | 14 | Tạm thời không sẵn sàng | 503 |
| `UNAUTHENTICATED` | 16 | Không có hoặc sai thông tin xác thực | 401 |

Cột HTTP chỉ là đối chiếu để nhớ, không phải ánh xạ chính thức.

Chọn mã để client biết có nên retry không, theo hướng dẫn của gRPC:

- `UNAVAILABLE`: client retry được đúng lời gọi đó, với backoff. ⚠️ Không phải lúc nào cũng an toàn
  với thao tác không idempotent (module 2.1).
- `ABORTED`: retry ở mức cao hơn, ví dụ làm lại cả chuỗi đọc, sửa, ghi.
- `FAILED_PRECONDITION`: không retry cho tới khi trạng thái được sửa (ví dụ xoá thư mục chưa rỗng).
- `PERMISSION_DENIED` không dùng cho hết quota (dùng `RESOURCE_EXHAUSTED`) và không dùng khi chưa biết
  người gọi là ai (dùng `UNAUTHENTICATED`).
- Một số mã thư viện không bao giờ tự sinh, chỉ code ứng dụng trả: `INVALID_ARGUMENT`, `NOT_FOUND`,
  `ALREADY_EXISTS`, `FAILED_PRECONDITION`, `ABORTED`, `OUT_OF_RANGE`, `DATA_LOSS`. Thấy các mã này
  thì chắc chắn do ứng dụng trả.

⚠️ `DEADLINE_EXCEEDED` không có nghĩa là thao tác chưa chạy: với thao tác ghi, server có thể đã làm
xong nhưng response tới trễ. Đây chính là bài toán "không biết đã thành công chưa" của module 2.1, và
cách giải cũng vậy: idempotency key hoặc thao tác idempotent tự nhiên.

#### Tương thích của file .proto

Nguyên tắc gốc: client và server **không bao giờ** được cập nhật cùng lúc, kể cả khi bạn cố làm vậy
(một bên có thể bị rollback), và dữ liệu đã serialize có thể còn nằm trong log, queue, cache. Nên mọi
thay đổi phải để bản cũ và bản mới đọc được dữ liệu của nhau.

Vì trên dây chỉ có **số field** (kèm wire type), không có tên:

- Không đổi số của field đang dùng. "Đổi số" tương đương xoá field cũ và thêm field mới.
- Không bao giờ dùng lại số của field đã xoá, kể cả khi nghĩ rằng không còn ai dùng. Hậu quả của
  việc dùng lại: tốt nhất là lỗi parse, tệ hơn là dữ liệu hỏng hoặc lộ dữ liệu cá nhân, vì bản cũ
  đọc giá trị mới theo nghĩa cũ mà không hề báo lỗi.
- Xoá field thì `reserved` cả số lẫn tên. Trình biên dịch sẽ báo lỗi nếu ai đó dùng lại. Số và tên
  phải nằm ở hai câu `reserved` khác nhau:

  ```proto
  message Product {
    reserved 4;             // số của field "legacy_sku" đã xoá
    reserved "legacy_sku";  // giữ cả tên, vì JSON và text format dùng tên
    int64 id = 1;
    string name = 2;
  }
  ```

Phân loại thay đổi (theo Language Guide, mục *Updating A Message Type*, cho định dạng nhị phân):

| Thay đổi | Mức an toàn trên dây | Ghi chú |
|---|---|---|
| Thêm field mới | An toàn | Bản cũ gặp field lạ thì coi là *unknown field*, giữ lại khi serialize tiếp |
| Xoá field (và `reserved`) | An toàn | Bản mới đọc dữ liệu cũ thì field đó bị bỏ qua |
| Thêm giá trị enum | An toàn trên dây | Nhưng có thể vỡ code có `switch` phủ hết các giá trị |
| Đổi tên field | An toàn cho nhị phân | Vỡ JSON mapping và vỡ code đã sinh (tên getter đổi) |
| Đổi số field | Không an toàn | Như xoá rồi thêm |
| Đổi kiểu `int32` ↔ `int64` ↔ `uint32` ↔ `uint64` ↔ `bool` | Tương thích có điều kiện | Số lớn bị cắt bit khi bên cũ đọc bằng kiểu hẹp hơn |
| Đổi `string` ↔ `bytes` | Tương thích có điều kiện | Chỉ khi bytes là UTF-8 hợp lệ |
| Đổi kiểu khác (ví dụ `int32` sang `string`) | Không an toàn | Wire type không khớp |
| `repeated` sang singular | Mất dữ liệu | Với `string`, `bytes`, message: không crash, bên đọc singular lấy phần tử cuối (message thì gộp lại), phần còn lại mất. Với số, bool, enum: không an toàn, vì `repeated` kiểu số mặc định mã hoá *packed* |

- "Tương thích có điều kiện" nghĩa là chỉ an toàn khi bạn kiểm soát được việc rollout: ví dụ đổi
  `int32` sang `int64` nhưng tiếp tục chỉ ghi giá trị vừa `int32` cho tới khi mọi bên đã lên bản mới.
  Schema public ra ngoài tổ chức thì đừng làm.
- Protobuf docs khuyên gần như không bao giờ đổi kiểu field. Cách an toàn là expand-contract như
  module 3.1: thêm field mới với số mới (`price_minor`), ghi cả hai, chuyển client đọc field mới, rồi
  xoá field cũ và `reserved` nó.
- ⚠️ Chuyển sang JSON sẽ làm mất unknown field. Nếu hệ thống trao đổi bằng ProtoJSON (JSON mapping
  của Protobuf) thì quy tắc chặt hơn: đổi tên field hoặc tên giá trị enum là breaking.

*Giá trị mặc định và field presence* trong proto3:

- Field không có trên dây thì đọc ra giá trị mặc định theo kiểu: `0` cho số, `""` cho string, `false`
  cho bool, giá trị enum đầu tiên (phải là `0`) cho enum, danh sách rỗng cho `repeated`.
- Với field scalar khai kiểu thường (*implicit presence*), giá trị mặc định **không được gửi đi**, nên
  không phân biệt được "không gửi" với "gửi đúng 0". Ví dụ `discount = 0` và "không có thông tin
  discount" trông giống hệt nhau.
- Khai `optional` thì field có *explicit presence*: kiểm tra được đã set hay chưa (sinh ra hàm dạng
  `hasDiscount()`). Tài liệu protobuf hiện khuyên dùng `optional` cho field đơn.
- Field kiểu message luôn có presence, thêm `optional` không đổi gì.
- ⚠️ Đừng thiết kế bool mà giá trị `false` bật một hành vi, vì "không gửi" cũng là `false`.

*Enum*:

- Giá trị đầu tiên phải là `0`, đặt tên `TÊN_ENUM_UNSPECIFIED` và không mang nghĩa nghiệp vụ, chỉ có
  nghĩa "chưa đặt". Lý do: `0` là giá trị mặc định, nếu `0` là `PAID` thì mọi đơn không set status
  sẽ trông như đã thanh toán.
- Tiền tố tên enum vào từng giá trị (`ORDER_STATUS_PAID`) vì ở C++ các giá trị enum khai trong cùng
  một phạm vi chứa dùng chung không gian tên, hai enum cùng có `UNSPECIFIED` sẽ đụng nhau.
- Giá trị enum lạ (bản mới thêm) được giữ lại khi deserialize; cách biểu diễn tuỳ ngôn ngữ (Go, C++
  giữ số nguyên; Java có một giá trị riêng cho "không nhận ra"). Client nên xử lý như "không rõ"
  (tolerant reader, module 3.1).
- Xoá giá trị enum thì cũng `reserved` số và tên.

Vài quy tắc khác từ Proto Best Practices:

- Không thêm field `required` (proto3 đã bỏ hẳn khái niệm này).
- Bool chỉ dùng cho thứ chắc chắn mãi mãi chỉ có hai trạng thái; còn lại dùng enum.
- Dùng well-known type: `google.protobuf.Timestamp`, `Duration`, `FieldMask`, thay vì tự đặt
  `int64 timeout_millis`.
- Tách message cho API và message cho lưu trữ, dù lúc đầu gần giống nhau.
- Không dựa vào việc serialize ra byte giống hệt nhau giữa các bản build (ví dụ làm cache key).

*Tự động hoá bằng `buf breaking`*: so schema hiện tại với một bản trước (nhánh Git, module trên
Buf Schema Registry, tarball, image) và báo mọi thay đổi làm vỡ client, server hoặc code sinh ra.

```sh
buf breaking --against '.git#branch=main'
# Ví dụ trong tài liệu buf khi đổi `int32 id = 1` thành `string id = 1`:
# user.proto:2:3:Field "1" on message "User" changed type from "int32" to "string".
```

Bốn nhóm quy tắc, từ chặt tới lỏng:

- `FILE`: vỡ code sinh ra theo từng file. Là mặc định khi `buf.yaml` không khai `breaking.use`.
- `PACKAGE`: vỡ code sinh ra theo package (chuyển message giữa các file trong cùng package thì không
  tính).
- `WIRE_JSON`: vỡ định dạng nhị phân hoặc JSON.
- `WIRE`: chỉ vỡ định dạng nhị phân.

Qua được nhóm chặt thì chắc chắn qua các nhóm lỏng hơn. Chọn nhóm theo thứ client thực sự phụ thuộc:
chỉ dùng qua dây thì `WIRE` là đủ; có team khác import code Go sinh ra thì cần `PACKAGE`. Đặt lệnh này
trong CI để chặn PR trước khi merge.

#### Vận hành: trình duyệt và load balancing

*Trình duyệt không gọi gRPC trực tiếp được*: JavaScript trong trình duyệt không kiểm soát được các
frame HTTP/2 và trailer như gRPC cần. Hai cách:

- *gRPC-Web*: một biến thể giao thức dành cho trình duyệt, cần một proxy (ví dụ Envoy) dịch sang gRPC
  thật ở phía sau.
- *grpc-gateway*: plugin sinh ra một reverse proxy REST/JSON từ annotation `google.api.http` trong
  `.proto`, tức một API REST cho client ngoài và gRPC cho nội bộ, cùng một nguồn contract.

*Load balancing bị lệch* (câu hỏi hay gặp khi chạy trên Kubernetes):

1. HTTP/2 được thiết kế để dùng **một kết nối TCP sống lâu** và multiplex mọi request lên đó.
2. Load balancing mặc định của Kubernetes Service là ở mức kết nối (*L4*, tầng TCP): nó chỉ chọn pod
   lúc kết nối được mở.
3. Kết nối đã mở thì mọi lời gọi sau đều vào đúng pod đó. Scale thêm pod không giúp gì: pod mới không
   nhận được lời gọi nào từ client đang có kết nối.
4. HTTP/1.1 không bị nặng như vậy vì mỗi kết nối chỉ chạy một request một lúc, nên client mở nhiều
   kết nối và các kết nối hết hạn rồi mở lại, tải tự nhiên được rải ra.

Cách sửa: chuyển từ cân bằng theo kết nối sang **cân bằng theo request** (*L7*, hiểu HTTP/2):

- *Client-side load balancing*: client giữ kết nối tới nhiều pod và tự chia lời gọi. Trên Kubernetes
  thường đi cùng *headless service* (DNS trả về IP của từng pod thay vì một IP ảo), với client gRPC đủ
  thông minh để đọc nhiều bản ghi DNS. Nhược: phụ thuộc thư viện client, phải xử lý pod thay đổi liên
  tục.
- *L7 proxy* đứng giữa: Envoy, hoặc ingress/gateway có hỗ trợ gRPC, chia từng request.
- *Service mesh* (Linkerd, Istio): gắn một proxy nhỏ cạnh mỗi pod (*sidecar*), proxy tự theo dõi danh
  sách pod và cân bằng theo request, không cần sửa code. Bài blog Kubernetes giới thiệu Linkerd còn
  chọn pod theo latency (trung bình trượt có trọng số mũ).

#### gRPC trong PHP

- Tài liệu gRPC chính thức ghi rõ: PHP chỉ tạo được **client**, muốn có server phải dùng ngôn ngữ khác.
  Lý do sâu xa: PHP-FPM chạy mỗi request một lần rồi dọn sạch (share-nothing), không hợp với server
  phải giữ kết nối HTTP/2 lâu dài và streaming.
- Làm client: cài extension `grpc` (qua PECL) và package Composer `grpc/grpc`, runtime Protobuf
  (extension `protobuf` hoặc package `google/protobuf`), cộng `protoc` với plugin `grpc_php_plugin`
  để sinh class.
- Làm server bằng PHP ngoài đường chính thức: RoadRunner (application server viết bằng Go) có plugin
  gRPC, phần Go giữ kết nối HTTP/2 và chuyển lời gọi cho worker PHP sống lâu. Mô hình worker sống lâu
  có các bẫy riêng (rò bộ nhớ, state dính giữa request): xem
  [05-php-laravel.md, module 3.5](05-php-laravel.md#35-process-sống-lâu-queue-worker-octane-daemon).

Client PHP (trích đoạn, class `Shop\V1\...` là code sinh ra từ `.proto` ở trên):

```php
<?php
declare(strict_types=1);

use Shop\V1\GetOrderRequest;
use Shop\V1\OrderServiceClient;

$client = new OrderServiceClient('orders.internal:50051', [
    'credentials' => Grpc\ChannelCredentials::createInsecure(), // nội bộ; ra ngoài thì dùng TLS
]);

$req = new GetOrderRequest();
$req->setId(42);

// Tham số 2 là metadata, tham số 3 là options. 'timeout' tính bằng MICRO giây.
// Không truyền timeout thì deadline là vô hạn.
[$order, $status] = $client->GetOrder($req, ['x-request-id' => ['abc']], ['timeout' => 500_000])->wait();

if ($status->code !== Grpc\STATUS_OK) {
    // $status->code là mã số (ví dụ 4 = DEADLINE_EXCEEDED), $status->details là mô tả
    throw new RuntimeException("GetOrder lỗi {$status->code}: {$status->details}");
}
echo $order->getTotalMinor(), PHP_EOL;
```

⚠️ Trong PHP-FPM, channel chỉ sống trong một request, nên mỗi request lại mở kết nối mới (tốn bắt tay
TCP và TLS). Ở worker sống lâu (Octane, queue worker) nên tạo client một lần và dùng lại.

#### Chọn REST, GraphQL hay gRPC

| | REST | GraphQL | gRPC |
|---|---|---|---|
| Hợp với | API public, CRUD, đối tác | Nhiều loại client cần ghép dữ liệu linh hoạt | Nội bộ service-to-service |
| Contract | OpenAPI (module 3.4), tuỳ chọn | Schema bắt buộc, introspection | `.proto` bắt buộc, sinh code |
| Điểm mạnh | HTTP cache, CDN, trình duyệt gọi thẳng, ai cũng biết | Client lấy đúng field cần, một round trip | Latency thấp, payload nhỏ, streaming, deadline lan truyền |
| Điểm yếu | Over/under-fetching, nhiều round trip | N+1, khó cache, phải chống query phá hoại (module 3.2) | Không gọi thẳng từ trình duyệt, cần L7 LB, khó debug bằng curl |
| Lỗi | HTTP status + body RFC 9457 | Mảng `errors`, thường vẫn `2xx` | Status code riêng trong trailer |

Cách trả lời câu "hệ có web, mobile và nhiều service nội bộ": không phải chọn một. Phổ biến là gRPC
giữa các service nội bộ, và một lớp ngoài (REST hoặc GraphQL, có thể qua BFF ở module 3.4) cho web và
mobile. Lý do nên nêu: đối tượng dùng (trình duyệt, đối tác, service), nhu cầu cache, đội ngũ và
tooling sẵn có, và chi phí vận hành thêm.

Khi server cần chủ động đẩy dữ liệu xuống trình duyệt (thông báo, chat, tiến độ job):

- *SSE* (Server-Sent Events): một chiều server xuống client, chạy trên HTTP thường, trình duyệt tự nối
  lại khi rớt.
- *WebSocket*: kênh hai chiều sau một lần nâng cấp kết nối (*upgrade*) từ HTTP.
- *Long polling*: client gửi request, server giữ tới khi có dữ liệu hoặc hết thời gian rồi client hỏi
  lại. Dùng làm phương án dự phòng.
- Laravel: Reverb là WebSocket server chính chủ, Echo là thư viện JavaScript phía client để nghe
  broadcast.
- Chi tiết giao thức: [02-networking.md](../02-networking.md).

**Tóm tắt nhanh**
- gRPC: `.proto` sinh stub, chạy trên HTTP/2, Protobuf nhị phân, bốn kiểu method theo `stream`.
- Mặc định không có deadline: luôn đặt, và lan truyền theo phần còn lại; `DEADLINE_EXCEEDED` với thao
  tác ghi không có nghĩa là chưa chạy. `UNAVAILABLE` là mã retry được.
- Trên dây chỉ có số field: không đổi số, không dùng lại số, xoá thì `reserved` số và tên; đổi tên phá
  JSON và code sinh; đổi kiểu gần như luôn tránh. Enum số 0 là `..._UNSPECIFIED`; `optional` để phân
  biệt "không gửi" với "0". `buf breaking` trong CI.
- HTTP/2 một kết nối sống lâu nên L4 LB dồn tải vào một pod; sửa bằng client-side LB, L7 proxy hoặc
  service mesh.
- PHP chỉ làm client chính thức (extension `grpc`, `timeout` tính bằng micro giây); server qua
  RoadRunner.

**Nguồn**: [gRPC: Core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/) ·
[gRPC: Deadlines](https://grpc.io/docs/guides/deadlines/) ·
[gRPC: Status codes](https://grpc.io/docs/guides/status-codes/) ·
[gRPC: PHP](https://grpc.io/docs/languages/php/) ·
[PHP Quick start](https://grpc.io/docs/languages/php/quickstart/) ·
[PHP Basics tutorial](https://grpc.io/docs/languages/php/basics/) ·
[gRPC PHP source: AbstractCall.php](https://github.com/grpc/grpc/blob/master/src/php/lib/Grpc/AbstractCall.php) ·
[Protobuf Language Guide (proto3)](https://protobuf.dev/programming-guides/proto3/) ·
[Proto Best Practices](https://protobuf.dev/best-practices/dos-donts/) ·
[buf breaking](https://buf.build/docs/breaking/) ·
[gRPC Load Balancing on Kubernetes without Tears](https://kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears/)

---

### 3.4 Contract, tài liệu và hạ tầng API

Module này trả lời: làm sao biến "API nhận gì, trả gì" thành một *contract* máy đọc được (OpenAPI),
dùng nó để lint, test và chặn breaking change trong CI, và các lớp hạ tầng đứng trước API (gateway,
BFF, tracing) làm gì, đặt gì vào đó và không đặt gì.

#### OpenAPI

*OpenAPI Specification* (OAS) là chuẩn mô tả HTTP API bằng YAML hoặc JSON, độc lập ngôn ngữ, để cả
người và máy hiểu được API mà không cần đọc source code. Một bản mô tả như vậy gọi là *OpenAPI
Description* (OAD). Từ OAD có thể: validate và lint, validate dữ liệu thật chạy qua API, sinh tài
liệu, sinh code client và server, dựng mock server, phân tích bảo mật từ lúc thiết kế.

Khung của một OAD:

```yaml
openapi: 3.1.1
info: { title: Shop API, version: "2026-09-01" }
servers: [{ url: https://api.example.com/v1 }]
paths:
  /orders/{id}:
    get:
      operationId: getOrder
      tags: [orders]
      parameters:
        - { name: id, in: path, required: true, schema: { type: integer, format: int64 } }
      responses:
        "200":
          description: Đơn hàng
          content:
            application/json:
              schema: { $ref: "#/components/schemas/Order" }
        "404":
          description: Không tìm thấy
          content:
            application/problem+json:           # format lỗi RFC 9457, module 1.3
              schema: { $ref: "#/components/schemas/Problem" }
components:
  schemas:
    Order:
      type: object
      required: [id, status, total_minor]
      properties:
        id: { type: integer, format: int64 }
        status: { type: string, enum: [pending, paid, cancelled] }
        total_minor: { type: integer, description: "Tổng tiền theo đơn vị nhỏ nhất" }
        note: { type: [string, "null"] }        # 3.1: nullable viết theo JSON Schema
    Problem:
      type: object
      properties:
        type: { type: string, format: uri }
        title: { type: string }
        status: { type: integer }
        detail: { type: string }
```

- `components` chứa phần dùng lại (schema, parameter, response, security scheme), tham chiếu bằng
  `$ref`. Thấy cùng một đoạn YAML xuất hiện hai lần là lúc đưa nó vào `components`.
- Ít nhất một trong `paths`, `components`, `webhooks` phải có mặt.
- Phiên bản: `major.minor` quyết định tập tính năng; `.patch` chỉ sửa lỗi và làm rõ câu chữ. Tooling
  hỗ trợ 3.1 phải hiểu mọi bản 3.1.x, và không nên phân biệt 3.1.0 với 3.1.1.

Bản 3.1 (so với 3.0):

- Schema Object là *superset* (tập bao) của JSON Schema Draft 2020-12, nên dùng lại được validator
  và tooling của JSON Schema. Hệ quả dễ thấy: `nullable: true` của 3.0 được thay bằng
  `type: [string, "null"]`, và `examples` là mảng như JSON Schema.
- Có mục `webhooks` ở top-level để mô tả các request mà **bên cung cấp API gửi đi** cho client (module
  2.4), không cần gắn với một API call nào.

Bản 3.2.0 (phát hành 19/09/2025, cùng ngày với bản vá 3.1.2) thêm, theo spec:

- Field `query` trong Path Item cho method HTTP `QUERY` (method an toàn có body, đang là draft của
  IETF), và `additionalOperations` để khai các method khác.
- `itemSchema` trong Media Type: schema áp dụng cho **từng phần tử** của một dòng dữ liệu tuần tự, dùng
  cho `text/event-stream` (SSE), `application/jsonl` (JSON Lines), `application/json-seq`.
- Vị trí tham số mới `in: "querystring"`: mô tả cả chuỗi query như một khối (ví dụ dạng
  `application/x-www-form-urlencoded`), không dùng chung với tham số `in: "query"` trong cùng operation.
- Tag có `parent` (lồng tag thành cây) và `kind` (phân loại tag, ví dụ `nav`, `audience`).
- OAuth2 device authorization flow (`deviceAuthorization` với `deviceAuthorizationUrl`).
- Field `$self` ở top-level: URI tự khai của tài liệu, làm base URI khi resolve `$ref`.

⚠️ Trước khi đổi `openapi: 3.2.0`, kiểm tra từng công cụ trong chuỗi (generator, validator, UI tài
liệu, gateway import). Ví dụ Spectral đã ghi hỗ trợ 3.2 trong README, nhưng Scramble (Laravel) ghi là
sinh ra 3.1.0. Chưa cần tính năng mới thì 3.1.x là lựa chọn an toàn.

#### Contract-first và code-first

| | Contract-first (design-first) | Code-first |
|---|---|---|
| Làm thế nào | Viết OAD trước, review, rồi sinh stub, client, mock từ đó | Viết code trước, sinh OAD từ code, annotation hoặc phân tích tĩnh |
| Ưu | Frontend, mobile, backend làm song song dựa trên mock. Thiết kế được review như code trước khi tốn công cài đặt | Nhanh lúc đầu, không phải học thêm; tài liệu bám sát code |
| Nhược | Tốn công viết spec; phải có CI kiểm code khớp spec | Spec phản ánh "code đang làm gì" chứ không phải "API nên thế nào"; dễ sinh ra API mà OpenAPI không mô tả gọn được |

- OpenAPI Initiative (qua learn.openapis.org) nghiêng hẳn về design-first. Lý do: số API viết được
  bằng code nhiều hơn số API OpenAPI mô tả được. Làm code-first mà không để ý giới hạn này thì tới lúc
  sinh spec sẽ phải "vặn" spec cho gần đúng, ra tài liệu khó hiểu và thiếu.
- Dù chọn cách nào: chỉ giữ **một nguồn sự thật**. Sinh spec từ annotation rồi commit file spec, nhưng
  annotation vẫn nằm trong code, thì người mới không biết cái nào đang được dùng. Nếu có hai nguồn thì
  phải có test trong CI bắt chúng khớp nhau.
- Spec là file nguồn hạng nhất: commit vào repo, chạy trong CI, và công bố cho client (họ dùng để tự
  sinh client).
- Laravel: Scramble (`composer require dedoc/scramble`) là code-first theo kiểu phân tích code, không
  bắt viết annotation. Sau khi cài có `/docs/api` (UI) và `/docs/api.json` (file OpenAPI), mặc định chỉ
  mở ở môi trường `local`. Với API public cho đối tác, cân nhắc có spec viết tay và review như code.

#### Dùng spec trong CI và test

Một pipeline kiểu mẫu cho mỗi PR:

```
PR sửa API ──► 1. Lint spec (Spectral)          phong cách, quy ước đặt tên
            ├► 2. Validate spec hợp lệ           đúng cú pháp OAS
            ├► 3. oasdiff breaking so với main   chặn breaking change (module 3.1)
            └► 4. Test gọi API thật, validate    code trả đúng shape như spec
                  request/response theo spec
```

*Lint bằng Spectral*: Spectral là linter tổng quát cho JSON/YAML, **phải có ruleset** mới chạy. Bộ
có sẵn `spectral:oas` kiểm OpenAPI 2, 3.0, 3.1, 3.2; bạn thêm quy tắc của team:

```yaml
# .spectral.yaml
extends: ["spectral:oas"]
rules:
  properties-snake-case:
    description: Tên field phải là snake_case
    severity: error
    given: "$..properties[*]~"     # dấu ~ lấy tên key thay vì giá trị
    then:
      function: casing
      functionOptions: { type: snake }
```

```sh
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml
```

Nhiều công ty công bố ruleset Spectral của họ (Adidas, Azure, DigitalOcean, Zalando qua API
Stylebook), là chỗ tốt để tham khảo quy tắc.

*Phát hiện breaking change bằng oasdiff*: so hai bản spec và phân loại từng thay đổi thành ba mức:

- `ERR`: chắc chắn breaking.
- `WARN`: có thể breaking nhưng không xác nhận được bằng máy.
- `INFO`: không breaking.

`oasdiff breaking` chỉ báo `ERR` và `WARN`; `oasdiff changelog` báo mọi thay đổi ảnh hưởng tới client
(dùng làm changelog). oasdiff đọc được spec trực tiếp từ một revision Git bằng cú pháp `<ref>:<path>`:

```sh
# Trong CI: so spec của PR với spec trên main, thoát mã 1 nếu có thay đổi mức ERR
oasdiff breaking --fail-on ERR origin/main:openapi.yaml openapi.yaml
# Chặt hơn: coi cả WARN là lỗi
oasdiff breaking --fail-on WARN origin/main:openapi.yaml openapi.yaml
```

Mức độ của từng check chỉnh được theo chính sách của bạn (`--severity-levels`), và có thể gán mức ổn
định (draft, alpha, beta, stable, qua extension `x-stability-level`) cho từng endpoint: mặc định
oasdiff bỏ qua endpoint `draft` và `alpha` khi dò breaking, nên endpoint mới được đổi thoải mái hơn.

*Validate response trong test*: gọi endpoint trong feature test rồi kiểm response theo schema trong
spec, để bắt trường hợp code âm thầm đổi shape (quên field, sai kiểu). Trong PHP có các thư viện
validate PSR-7 request/response theo OpenAPI (ví dụ `league/openapi-psr7-validator`); kiểm tra thư viện
bạn chọn đã hỗ trợ bản OAS bạn dùng chưa.

*Contract test consumer-driven* (Pact): khác với "kiểm provider khớp spec" ở trên.

- Mỗi *consumer* (bên gọi) viết test mô tả các cặp request/response cụ thể **mà nó thực sự dùng**.
  Chạy test sinh ra file contract.
- *Provider* (bên cung cấp) chạy lại các contract đó với code thật của mình.
- Pact tự gọi là "contract by example": không mô tả mọi trạng thái như OpenAPI, chỉ các ví dụ cụ thể.
  Ưu điểm: provider được tự do đổi những phần không consumer nào dùng.
- Theo tài liệu Pact, kiểm provider khớp OpenAPI một mình không chứng minh được consumer gọi đúng, nên
  kém hơn trong việc chặn lỗi tích hợp. Hai cách bổ sung cho nhau: OpenAPI cho API public, Pact cho
  các service nội bộ biết rõ consumer của mình.
- Chi tiết về contract test: [20-testing-quality.md](../20-testing-quality.md).

#### Tài liệu tốt gồm gì

Tài liệu sinh từ spec (Swagger UI, Redoc, Stoplight Elements, Scramble) chỉ là khung. Tài liệu mà đối
tác dùng được cần thêm:

- Ví dụ request và response thật cho mỗi endpoint, gồm cả response lỗi (field `examples` trong spec).
- Danh sách mã lỗi (`type` của problem details), ý nghĩa và cách xử lý từng mã: retry được hay không.
- Xác thực: lấy token thế nào, scope nào cho endpoint nào.
- Rate limit: giới hạn bao nhiêu, header nào báo còn lại bao nhiêu, gặp `429` thì chờ theo gì
  (module 2.3).
- Idempotency: endpoint nào nhận `Idempotency-Key`, key sống bao lâu (module 2.1).
- Pagination và cách lọc, sắp xếp (module 1.4).
- *Changelog* (nhật ký thay đổi), chính sách versioning và deprecation, hướng dẫn migrate (module 3.1).
  `oasdiff changelog` sinh được bản nháp.
- SDK sinh từ spec: đúng chuẩn và nhanh, nhưng mỗi ngôn ngữ là một gói phải phát hành, sửa lỗi, hỗ trợ.
  Nhiều nhà cung cấp chỉ duy trì SDK cho vài ngôn ngữ chính và để phần còn lại tự sinh từ spec.

#### Tracing xuyên API

*Distributed tracing* là theo dấu một request qua nhiều service. Mỗi bước xử lý (nhận request, gọi DB,
gọi service khác) là một *span*; các span có chung một *trace id* và nối với nhau qua quan hệ cha con.
Vấn đề: nếu mỗi hãng tracing dùng header riêng, request đi qua một proxy hay service dùng hãng khác là
đứt. *W3C Trace Context* (W3C Recommendation, 11/2021) chuẩn hoá hai header:

`traceparent`: định dạng chung mọi hãng hiểu, gồm bốn phần ngăn bởi `-`, toàn chữ hex **thường**:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
             │  │                                │                │
             │  trace-id: 32 hex (16 byte)       parent-id:       trace-flags: 2 hex (8 bit)
             │  chung cho cả trace               16 hex (8 byte)  bit thấp nhất = sampled
             version: 2 hex, hiện là 00          id của span bên gọi
```

- `version`: hiện là `00`; `ff` bị cấm.
- `trace-id`: định danh cả trace. Toàn số `0` là không hợp lệ.
- `parent-id`: id của request này theo góc nhìn bên gọi (nhiều hệ thống gọi là *span id* của span cha).
  Toàn số `0` là không hợp lệ.
- `trace-flags`: bản `00` chỉ định nghĩa một cờ là `sampled` (bit thấp nhất): bên gọi *có thể* đã ghi
  lại trace này. Các bit khác phải để 0. Cờ này là gợi ý, bên nhận có thể lấy mẫu ít hơn.
- ⚠️ Đây là bit field: phải dùng phép AND với mặt nạ, không so sánh cả byte. Cờ `09` cũng là sampled.
- Trace id hoặc parent id không hợp lệ thì bên nhận phải bỏ qua `traceparent` và bắt đầu trace mới.

`tracestate`: thông tin riêng của từng hãng, dạng danh sách `key=value` ngăn bởi dấu phẩy, tối đa 32
phần tử, ví dụ `tracestate: rojo=00f067aa0ba902b7,congo=t61rcWkgMzE`. Hãng nào sửa hoặc thêm giá trị
của mình thì nên đưa phần tử đó lên đầu trái; không nên xoá phần tử của hãng khác (spec cho phép
xoá, ví dụ proxy chặn key vì lý do bảo mật hoặc cắt bớt khi quá dài, nhưng xoá key lạ làm đứt liên
kết ở hệ thống khác). Nếu không parse được
`traceparent` thì không được parse `tracestate`.

Quy tắc chuyển tiếp:

1. Service tham gia tracing nhận `traceparent`, tạo span của mình, rồi gửi đi với **cùng `trace-id`**
   và `parent-id` mới là id span của mình. Đây là thay đổi mặc định.
2. Proxy hoặc service không tracing (chỉ đi qua) phải chuyển tiếp nguyên vẹn; nếu không đổi
   `traceparent` thì cũng không được đổi `tracestate`.
3. Ngoại lệ có chủ đích: cổng vào của mạng nội bộ (gateway public) được phép *restart trace* (sinh
   `trace-id` mới) để client ngoài không điều khiển được việc lấy mẫu bên trong, vốn là một hướng tấn
   công từ chối dịch vụ.

⚠️ Một chỗ làm rơi header (gateway viết lại header, HTTP client tự viết không truyền, job queue không
mang theo context) là chuỗi trace bị đứt thành nhiều trace rời.

Đọc `traceparent` bằng PHP (chạy `php tp.php`):

```php
<?php
declare(strict_types=1);

/** @return array{trace_id: string, parent_id: string, sampled: bool}|null */
function parseTraceparent(string $header): ?array
{
    // Chỉ xử lý đúng định dạng version 00; version cao hơn cần luật parse riêng của spec.
    if (preg_match('/^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$/', $header, $m) !== 1) {
        return null;
    }
    [, $traceId, $parentId, $flags] = $m;
    if ($traceId === str_repeat('0', 32) || $parentId === str_repeat('0', 16)) {
        return null;
    }
    $sampled = (hexdec($flags) & 0x01) === 0x01; // AND với mặt nạ, không so sánh cả byte
    return ['trace_id' => $traceId, 'parent_id' => $parentId, 'sampled' => $sampled];
}

foreach ([
    '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01',
    '00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-09',
    '00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01',
] as $h) {
    $tp = parseTraceparent($h);
    echo $tp === null
        ? "không hợp lệ\n"
        : "trace={$tp['trace_id']} parent={$tp['parent_id']} sampled=" . ($tp['sampled'] ? 'có' : 'không') . "\n";
}
// trace=4bf92f3577b34da6a3ce929d0e0e4736 parent=00f067aa0ba902b7 sampled=có
// trace=4bf92f3577b34da6a3ce929d0e0e4736 parent=00f067aa0ba902b7 sampled=có
// không hợp lệ
```

Trên thực tế không tự parse mà dùng SDK OpenTelemetry (propagator mặc định của nó dùng W3C Trace
Context). Chi tiết về trace, span, sampling:
[18-reliability-observability.md](../18-reliability-observability.md).

#### API gateway và BFF

*API gateway* là lớp đứng trước các service, gánh những việc chung mà service nào cũng cần:

| Việc | Ý nghĩa |
|---|---|
| Routing | Đưa `/orders/*` tới service order, `/users/*` tới service user |
| Xác thực | Verify token (chữ ký JWT, introspection), gắn danh tính vào header cho service sau |
| Rate limit, quota | Theo API key, theo IP, theo gói dịch vụ |
| *TLS termination* | Giải mã HTTPS ở gateway; phía sau đi HTTP nội bộ hoặc mTLS |
| Log, metric, trace | Một điểm đo mọi request; bắt đầu hoặc restart trace |
| *Canary*, chia traffic | Chuyển một phần nhỏ traffic sang bản mới để thử trước khi chuyển hết |
| Chuyển đổi giao thức | REST/JSON bên ngoài sang gRPC bên trong (module 3.3) |

Ví dụ sản phẩm: Kong, AWS API Gateway, Envoy (thường làm nền cho gateway và service mesh), Nginx.

- ⚠️ Không đặt logic nghiệp vụ vào gateway: nó thành một "middleware thông minh" không thuộc domain
  nào, mọi team phải xếp hàng sửa nó, và logic ở đó khó test.
- ⚠️ Gateway phải *HA* (high availability: nhiều instance, không có điểm chết đơn), vì nó chết là mọi API
  chết. Nó cũng thêm một chặng mạng vào mọi request, nên đo latency của chính nó.
- Kiểm quyền chi tiết (user này có được xem đơn này không) vẫn ở service; gateway chỉ chặn thô.

*BFF* (Backend For Frontend, pattern Sam Newman mô tả năm 2015, dùng ở SoundCloud và REA):

- Vấn đề: một "API đa năng" phục vụ cả web và mobile. Mobile cần ít dữ liệu hơn, ít lời gọi hơn (pin,
  data), và tương tác khác hẳn. API đa năng phình to, thành nút thắt khi nhiều team cùng sửa, và
  thường sinh ra một team riêng giữ nó, khiến team frontend phải chờ.
- Giải pháp: mỗi trải nghiệm người dùng một backend mỏng riêng, **do chính team làm UI đó sở hữu**.
  BFF gọi các service phía sau và ghép thành đúng shape màn hình cần.

```
Web app ──► BFF web    ──┐
iOS app ──► BFF mobile ──┼──► Wishlist service, Catalog service, Inventory service
Đối tác ──► BFF partner ─┘
```

- Bao nhiêu BFF: nguyên tắc "một trải nghiệm, một BFF". iOS và Android giống nhau và cùng một team thì
  dùng chung được; khác nhiều hoặc khác team thì tách. Cấu trúc team là yếu tố quyết định lớn (định
  luật Conway).
- Gọi nhiều service: gọi song song những gì không phụ thuộc nhau (lấy wishlist trước, rồi catalog và
  inventory cùng lúc). Service phụ chết thì trả kết quả giảm bớt (bỏ thông tin tồn kho) thay vì lỗi cả
  màn hình, và client phải hiểu được response thiếu phần đó.
- Trùng lặp giữa các BFF: Newman chấp nhận trùng lặp giữa các service hơn là rút ra thư viện chung (thư
  viện chung dễ tạo coupling). Khi thật sự cần, tách thành service mới theo domain, hoặc đẩy việc ghép
  dữ liệu xuống service phía dưới.
- Mặt trái: thêm một tầng phải deploy và vận hành, thêm một chặng latency, logic dễ bị nhân bản.
- Khi nào dùng: app chỉ có web và không cần ghép nhiều thì có thể chưa cần. Có mobile hoặc bên thứ ba
  cần API riêng thì Newman khuyên cân nhắc BFF ngay từ đầu. BFF cho đối tác còn giúp không phải giữ
  API cũ cho cả hệ thống chỉ vì vài đối tác không chịu nâng cấp.
- GraphQL (module 3.2) đôi khi được dùng như một BFF chung: client tự chọn field thay vì mỗi client một
  backend. Đổi lại là các chi phí N+1, cache, chống query phá hoại.

**Tóm tắt nhanh**
- OpenAPI là contract máy đọc được của REST API; 3.1 bám JSON Schema 2020-12 và có `webhooks`; 3.2
  (09/2025) thêm `QUERY`, `itemSchema` cho streaming, `querystring`, tag lồng nhau, device flow; kiểm
  tooling trước khi nâng.
- Design-first được OpenAPI Initiative khuyến nghị; dù cách nào cũng giữ một nguồn sự thật và cho spec
  chạy trong CI.
- CI: Spectral lint theo ruleset, `oasdiff breaking --fail-on ERR` chặn breaking, test validate
  response theo spec; Pact cho contract nội bộ theo consumer.
- `traceparent` = `version-traceid(32 hex)-parentid(16 hex)-flags`, sampled là bit thấp nhất (dùng
  mặt nạ). Mọi chặng phải chuyển tiếp; mất một chỗ là đứt trace.
- Gateway gánh việc chung (routing, xác thực, rate limit, TLS, đo đạc), không chứa nghiệp vụ, phải HA.
  BFF là backend mỏng theo từng trải nghiệm, do team UI sở hữu.

**Nguồn**: [OpenAPI Specification 3.2.0](https://spec.openapis.org/oas/v3.2.0.html) ·
[OpenAPI Specification 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) ·
[learn.openapis.org](https://learn.openapis.org/) ·
[OpenAPI Best Practices](https://learn.openapis.org/best-practices.html) ·
[Spectral](https://github.com/stoplightio/spectral) · [oasdiff](https://github.com/oasdiff/oasdiff) ·
[oasdiff: Breaking changes](https://github.com/oasdiff/oasdiff/blob/main/docs/BREAKING-CHANGES.md) ·
[oasdiff: Git revisions](https://github.com/oasdiff/oasdiff/blob/main/docs/GIT-REVISION.md) ·
[Scramble](https://github.com/dedoc/scramble) ·
[W3C Trace Context](https://www.w3.org/TR/trace-context/) ·
[Sam Newman: Backends For Frontends](https://samnewman.io/patterns/architectural/bff/) ·
[Pact docs](https://docs.pact.io/)
