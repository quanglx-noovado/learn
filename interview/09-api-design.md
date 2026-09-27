# 09. Thiết kế API

> [← Mục lục](README.md) · **[📖 Bài đọc kiến thức](kien-thuc/09-api-design.md)** · Trọng tâm: **REST/HTTP trên Laravel** (API Resources, FormRequest, Sanctum, rate limiting), đối chiếu GraphQL, gRPC.
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

HTTP ở tầng giao thức (HTTP/2, TLS, keep-alive, WebSocket/SSE) ở [02-networking.md](02-networking.md).
Auth và OWASP API Top 10 ở [10-security.md](10-security.md).

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [RFC 9110: HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) | RFC | Nguồn chuẩn cho method, status code, header, conditional request. Khi blog và RFC mâu thuẫn, tin RFC |
| [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) | Guideline công ty | Bộ quy tắc REST đầy đủ và thực dụng nhất: naming, lỗi, pagination, compatibility, deprecation |
| [Google AIP](https://google.aip.dev/) | Guideline công ty | Custom method, long-running operation, pagination, batch, backward compatibility; dùng cho cả REST và gRPC |
| *API Design Patterns* (JJ Geewax; Manning 2021) | Sách | Viết từ AIP của Google: naming, pagination, LRO, versioning, bulk, soft delete |
| [Stripe API Reference](https://docs.stripe.com/api) | Tài liệu thật | Mẫu API public tốt: idempotency, lỗi, pagination, versioning theo ngày, webhook |
| [OpenAPI Specification 3.2](https://spec.openapis.org/oas/v3.2.0.html) | Spec | Mô tả contract REST; [bản 3.1.1](https://spec.openapis.org/oas/v3.1.1.html) vẫn là bản tooling hỗ trợ rộng nhất |
| [Laravel docs](https://laravel.com/docs/eloquent-resources) | Official docs | API Resources, validation, Sanctum/Passport, rate limiting, HTTP client |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Thiết kế endpoint REST đúng ngữ nghĩa HTTP, lỗi thống nhất, pagination đúng | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.7 | API đúng khi retry và ghi đồng thời, webhook, gọi bên thứ ba an toàn, làm đúng trên Laravel | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.4 | Tiến hoá API không phá client, chọn REST/GraphQL/gRPC theo bối cảnh, quản lý contract | 7–9 ngày |

Học theo thứ tự: idempotency ở chặng 2 cần hiểu method semantics ở chặng 1, và phần tiến hoá
API ở chặng 3 chỉ có ý nghĩa khi đã biết thay đổi nào làm vỡ client. Câu "người dùng bấm thanh
toán hai lần" gần như luôn xuất hiện; nó là bài kiểm tra cả ba chặng.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Resource và method semantics

**Vì sao cần học:** Mỗi route bạn khai trong `routes/api.php` là một quyết định thiết kế: đặt
tên URL thế nào, dùng method nào. Chọn sai method không chỉ xấu mà còn gây bug thật, vì proxy,
trình duyệt và thư viện HTTP tự retry hay cache dựa trên method. Câu "PUT khác PATCH thế nào,
cái nào idempotent" gần như luôn có ở vòng đầu.

**Học gì**

*Resource và cách đặt URL*
- *Resource* là "thứ" mà API quản lý: một đơn hàng, một user, danh sách đơn hàng của một user.
  URL là tên của thứ đó, còn method HTTP nói bạn muốn làm gì với nó.
- Dùng danh từ số nhiều, không dùng động từ trong URL.
  - Đúng: `GET /users/123/orders` (lấy đơn hàng của user 123).
  - Sai: `/getUserOrders`. Động từ đã nằm ở method `GET` rồi.
- Lồng URL tối đa 1–2 cấp.
  - Nếu id của đơn hàng đã duy nhất trong toàn hệ thống thì dùng thẳng `/orders/{id}`, không cần
    `/users/123/orders/456`.
- Chọn một quy ước chữ cho tên field JSON, `snake_case` hoặc `camelCase`, và giữ nhất quán cho
  toàn API.
  - Laravel mặc định dùng tên cột DB, tức `snake_case`.

*Hành động không khớp CRUD*
- CRUD là bốn thao tác cơ bản: tạo, đọc, sửa, xoá. Nhiều nghiệp vụ không khớp gọn vào đó, ví dụ
  huỷ đơn, hoàn tiền. Có hai cách thiết kế:
  - *Sub-resource*: coi hành động là một resource con được tạo ra.
    Ví dụ: `POST /orders/{id}/cancellation` nghĩa là "tạo một yêu cầu huỷ cho đơn này".
  - *Custom method* (kiểu Google): thêm tên hành động sau dấu hai chấm.
    Ví dụ: `POST /orders/{id}:cancel`.

*Ba tính chất của method*
- *Safe* (an toàn): gọi method này không làm thay đổi gì trên server. Chỉ đọc.
- *Idempotent*: gọi 1 lần hay gọi 10 lần thì **tác động lên server** là như nhau.
  - Chỉ nói về tác động, không nói về response. Ví dụ: `DELETE /orders/5` lần đầu trả `204`, lần
    hai trả `404`, nhưng đơn 5 vẫn chỉ bị xoá một lần, nên DELETE vẫn là idempotent.
  - Vì sao quan trọng: method idempotent thì retry an toàn khi mạng lỗi. Method không idempotent
    (POST) thì retry có thể tạo hai đơn (module 2.1).
- *Cacheable*: response có thể được lưu lại và dùng lại cho lần gọi sau.

| Method | Safe | Idempotent | Dùng cho |
|---|---|---|---|
| GET, HEAD | có | có | đọc |
| OPTIONS | có | có | hỏi khả năng, CORS preflight (module 2.3) |
| POST | không | không | tạo mới, hành động |
| PUT | không | có | thay toàn bộ, hoặc tạo tại URI client chọn |
| PATCH | không | không bắt buộc | sửa một phần |
| DELETE | không | có | xoá |

- ⚠️ GET không được có side effect (tác dụng phụ, tức làm thay đổi dữ liệu).
  - Crawler của Google, tính năng prefetch của trình duyệt, và proxy khi retry đều tự gọi GET mà
    không hỏi ai.
  - Ví dụ: link "xoá" dạng `GET /orders/delete?id=5` có thể bị crawler bấm hộ.

*PUT và PATCH*
- PUT gửi **toàn bộ** resource mới. Gửi lại cùng body bao nhiêu lần thì kết quả vẫn là một trạng
  thái đó, nên PUT idempotent.
- PATCH gửi **một phần** thay đổi. Có idempotent hay không tuỳ nội dung:
  - "Đặt `name = X`" là idempotent: gọi lại vẫn ra `name = X`.
  - "Tăng `count` thêm 1" thì không: gọi hai lần là tăng 2.
- Hai format chuẩn cho body của PATCH:

| | JSON Merge Patch (RFC 7396) | JSON Patch (RFC 6902) |
|---|---|---|
| Body trông thế nào | Một object chứa các field cần đổi | Một danh sách phép: `add`, `remove`, `replace`, `move`, `copy`, `test` |
| Xoá một field | Gửi field đó với giá trị `null` | Phép `remove` |
| Sửa một phần tử trong mảng | Không được, phải gửi lại cả mảng | Được, trỏ tới phần tử bằng đường dẫn như `/items/2` |
| Độ dễ dùng | Rất dễ, giống body JSON bình thường | Khó hơn, nhưng diễn đạt được nhiều hơn |

  ```jsonc
  // Merge Patch: đổi name, xoá phone
  {"name": "An", "phone": null}

  // JSON Patch: cùng thay đổi
  [{"op": "replace", "path": "/name", "value": "An"},
   {"op": "remove", "path": "/phone"}]
  ```

*Đào sâu (🟡)*
- *HATEOAS*: response kèm sẵn các link tới hành động tiếp theo có thể làm, để client đi theo link
  thay vì tự ghép URL.
- *Richardson Maturity Model* chia API thành 4 mức từ 0 tới 3, mức 3 là có HATEOAS.
- Biết khái niệm là đủ. Rất ít API public làm đầy đủ mức 3.

**Đọc**
- RFC 9110: [Section 9: Methods](https://www.rfc-editor.org/rfc/rfc9110#section-9) (đọc 9.2 *Common Method Properties*)
- [RFC 7396](https://www.rfc-editor.org/rfc/rfc7396) (Merge Patch, ngắn), [RFC 6902](https://www.rfc-editor.org/rfc/rfc6902) (JSON Patch)
- Google AIP: [AIP-136 Custom methods](https://google.aip.dev/136)
- Martin Fowler: [Richardson Maturity Model](https://martinfowler.com/articles/richardsonMaturityModel.html)

**Nắm chắc khi**
- [ ] Thiết kế được bộ endpoint cho `orders` gồm huỷ, hoàn tiền, đổi địa chỉ mà không dùng động từ trong path tuỳ tiện
- [ ] Giải thích được vì sao PUT idempotent còn PATCH thì tuỳ, với ví dụ cụ thể
- [ ] Viết được cùng một thay đổi bằng Merge Patch và JSON Patch, chỉ ra trường hợp Merge Patch không diễn đạt được (sửa một phần tử mảng)

#### 1.2 Status code

**Vì sao cần học:** Status code là thứ đầu tiên mà monitoring, load balancer, SDK của client và
code retry nhìn vào. Trả sai code thì dashboard báo "mọi thứ ổn" trong khi user đang lỗi, hoặc
client retry một request không nên retry. Người phỏng vấn thích hỏi các cặp dễ nhầm như
`401`/`403`, `400`/`422`.

**Học gì**

*Cách đọc nhóm code*
- Chữ số đầu cho biết nhóm:
  - `2xx`: thành công.
  - `3xx`: chuyển hướng, client cần đi chỗ khác.
  - `4xx`: lỗi do client gửi sai. Gửi lại y nguyên thì vẫn lỗi.
  - `5xx`: lỗi phía server. Gửi lại sau có thể thành công.

*2xx: thành công*
- `200 OK`: thành công, có body.
- `201 Created`: đã tạo resource mới. Kèm header `Location` trỏ tới URL của resource vừa tạo,
  ví dụ `Location: /orders/789`.
- `202 Accepted`: đã nhận request nhưng sẽ xử lý sau (module 2.2).
- `204 No Content`: thành công và không có body, hay dùng cho DELETE.

*3xx: chuyển hướng*

| Code | Vĩnh viễn hay tạm | Giữ nguyên method và body khi đi theo? |
|---|---|---|
| `301` | Vĩnh viễn | Không chắc: client cũ có thể đổi POST thành GET |
| `308` | Vĩnh viễn | Có |
| `302` | Tạm | Không chắc, như `301` |
| `307` | Tạm | Có |

- `304 Not Modified` dùng cho *conditional GET*: client hỏi "bản tôi đang có còn mới không", server
  trả `304` không body nếu chưa đổi, để tiết kiệm băng thông.

*4xx: lỗi phía client*
- `400 Bad Request`: request sai định dạng, ví dụ JSON không parse được.
- `401 Unauthorized`: chưa xác thực, tức server chưa biết bạn là ai (thiếu token hoặc token hết
  hạn). Kèm header `WWW-Authenticate` để nói cách xác thực.
- `403 Forbidden`: đã biết bạn là ai, nhưng bạn không có quyền làm việc này.
- `404 Not Found`: không có resource.
- `405 Method Not Allowed`: URL có nhưng không hỗ trợ method này. Kèm header `Allow` liệt kê các
  method được phép.
- `406 Not Acceptable` và `415 Unsupported Media Type`: sai định dạng dữ liệu mong muốn hoặc gửi
  lên (module 2.2).
- `409 Conflict`: xung đột với trạng thái hiện tại, ví dụ huỷ một đơn đã giao.
- `410 Gone`: resource từng có nhưng đã bị gỡ vĩnh viễn (module 3.1).
- `412 Precondition Failed` và `428 Precondition Required`: dùng khi chống ghi đè đồng thời
  (module 2.2).
- `413 Content Too Large`: body quá lớn.
- `422 Unprocessable Content`: JSON đúng định dạng nhưng sai nghiệp vụ, ví dụ email không hợp lệ.
  Laravel trả `422` cho lỗi validation.
- `429 Too Many Requests`: gọi quá nhiều, bị rate limit. Có thể kèm header `Retry-After` nói bao
  lâu nữa mới gọi lại được (RFC 6585 chỉ ghi MAY, không bắt buộc).

*5xx: lỗi phía server*
- `500 Internal Server Error`: lỗi chưa xử lý trong code, ví dụ exception không ai bắt.
- `502 Bad Gateway`: server đứng giữa (Nginx, gateway) gọi *upstream* (server phía sau nó, ví dụ
  PHP-FPM) và nhận về rác hoặc upstream đã chết.
- `503 Service Unavailable`: đang quá tải hoặc bảo trì.
- `504 Gateway Timeout`: upstream trả lời quá chậm, server đứng giữa hết kiên nhẫn.

*Các cặp hay nhầm*
- ⚠️ Người phỏng vấn hay hỏi vặn đúng những cặp này:

| Cặp | Phân biệt |
|---|---|
| `400` / `422` | Sai định dạng so với đúng định dạng nhưng sai nghiệp vụ |
| `401` / `403` | Chưa biết bạn là ai so với biết rồi nhưng không cho |
| `403` / `404` | Trả `404` thay `403` khi muốn giấu việc resource tồn tại |
| `301` / `308` | Cùng vĩnh viễn, nhưng chỉ `308` chắc chắn giữ method và body |
| `502` / `504` | Upstream trả rác hoặc chết so với upstream quá chậm |

- ⚠️ Không trả `200` kèm `{"success": false}`.
  - Monitoring đếm tỉ lệ lỗi theo status code, nên sẽ không thấy lỗi.
  - Code retry và cache cũng dựa vào status code.
  - Client phải parse body mới biết là lỗi.

*Client nên retry code nào*
- Retry được: `408` (request timeout), `429`, `502`, `503`, `504`, và lỗi mạng. Đây là lỗi tạm
  thời, thử lại sau có thể thành công.
  - Với POST, retry `502`/`504` chỉ an toàn khi có idempotency key (module 2.1): upstream có thể đã
    xử lý xong.
- Không retry mù: `400`, `401`, `403`, `404`, `422`. Gửi lại y nguyên vẫn sai.
- `500` chỉ retry khi request là idempotent.
  - Lý do: với `POST /payments`, server có thể đã trừ tiền xong rồi mới lỗi ở bước sau. Retry là
    trừ lần hai.

**Đọc**
- RFC 9110: [Section 15: Status Codes](https://www.rfc-editor.org/rfc/rfc9110#section-15)
- [RFC 6585](https://www.rfc-editor.org/rfc/rfc6585) (`428`, `429`)
- [MDN: HTTP response status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status) để tra nhanh

**Nắm chắc khi**
- [ ] Cho 15 tình huống lỗi, chọn đúng status code và giải thích được các cặp hay nhầm
- [ ] Nói được client nên retry những code nào và vì sao `500` của POST không được retry mù

#### 1.3 Format lỗi thống nhất

**Vì sao cần học:** Khi mỗi endpoint trả lỗi một kiểu, frontend và mobile phải viết code xử lý
riêng cho từng chỗ, và support không tra được lỗi khách báo. Trong Laravel, lỗi validation, lỗi
404 của model và exception tự viết mặc định ra ba hình dạng khác nhau. Người phỏng vấn hay hỏi
"client nên dựa vào đâu để xử lý lỗi".

**Học gì**

*Chuẩn RFC 9457 Problem Details*
- RFC 9457 định nghĩa một hình dạng JSON chung cho lỗi HTTP, gọi là *Problem Details*. Nó thay
  cho RFC 7807 cũ.
- Response lỗi khai `Content-Type: application/problem+json`.
- Các field chuẩn:
  - `type`: một URI định danh **loại** lỗi, ví dụ `https://api.example.com/errors/validation`.
    Đây là thứ client dùng để phân nhánh xử lý.
  - `title`: mô tả ngắn của loại lỗi, cho người đọc.
  - `status`: status code HTTP, lặp lại cho tiện.
  - `detail`: giải thích cụ thể cho lần lỗi này.
  - `instance`: URI định danh lần xảy ra lỗi cụ thể này.
- Được thêm field mở rộng tuỳ ý, ví dụ `errors` (danh sách lỗi từng field) và `trace_id`.

*Client dựa vào mã lỗi, không dựa vào câu chữ*
- Client phải phân nhánh theo **mã lỗi máy đọc được** (`type` hoặc một field `code`).
- ⚠️ Không dựa vào `message`, vì message có thể được dịch sang ngôn ngữ khác hoặc sửa câu chữ bất
  cứ lúc nào. Code kiểu `if (message == "Email đã tồn tại")` sẽ vỡ khi ai đó sửa dấu chấm.

*Trace id để tra log*
- *Trace id* là một mã duy nhất gắn với một request, được ghi vào mọi dòng log liên quan. Khách
  gửi mã này cho support, support tìm ra đúng log của request đó.
- Nên dùng luôn trace id của chuẩn *W3C Trace Context*. Đây là 32 ký tự hex nằm trong header
  `traceparent` (module 3.4), nên khớp được với hệ thống tracing.

*Không lộ chi tiết nội bộ*
- ⚠️ Không trả stack trace, câu SQL, tên bảng ra ngoài. Đó là thông tin cho kẻ tấn công.
- Ở production phải đặt `APP_DEBUG=false`. Nếu để `true`, Laravel trả cả stack trace trong
  response lỗi.

*Laravel*
- Lỗi validation mặc định có dạng `{"message": ..., "errors": {...}}` với status `422`. Đây
  không phải RFC 9457.
- Muốn chuẩn hoá thì render lại các exception trong exception handler, khai ở `withExceptions`
  trong `bootstrap/app.php`.

Ví dụ một response lỗi theo RFC 9457:

```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Dữ liệu không hợp lệ",
  "status": 422,
  "detail": "2 field không hợp lệ",
  "errors": [{"field": "email", "code": "invalid_format"}],
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
}
```

**Đọc**
- [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457): đọc section 3 (members) và 4 (định nghĩa problem type mới)
- Zalando: [chương HTTP status codes and errors](https://opensource.zalando.com/restful-api-guidelines/#http-status-codes-and-errors)
- Laravel: [Rendering Exceptions](https://laravel.com/docs/errors#rendering-exceptions)

**Nắm chắc khi**
- [ ] Viết được handler trong Laravel biến `ValidationException`, `ModelNotFoundException`, `AuthorizationException` thành problem+json, và giải thích được vì sao closure type-hint `ModelNotFoundException`/`AuthorizationException` không được gọi (Laravel đã đổi chúng thành `NotFoundHttpException`/`AccessDeniedHttpException`; phải type-hint `HttpExceptionInterface` rồi xem `getPrevious()`)
- [ ] Giải thích được vì sao client không nên `if (message == "...")`

#### 1.4 Filtering, sorting, pagination

**Vì sao cần học:** Gần như mọi màn hình danh sách đều gọi một endpoint có lọc, sắp xếp và phân
trang. Làm sai thì trang sâu chậm dần theo dữ liệu, hoặc user thấy lặp và sót dòng khi cuộn feed.
Câu "offset khác cursor thế nào, cursor chứa gì" rất hay gặp ở mức mid.

**Học gì**

*Quy ước tham số query*
- Lọc (*filter*): `?status=paid&created_from=2026-01-01`.
- Sắp xếp (*sort*): `?sort=-created_at,id`. Dấu `-` nghĩa là giảm dần.
- Chọn field (*field selection*): `?fields=id,name`, chỉ trả những field này.
- Kèm quan hệ: `?include=customer`, trả kèm dữ liệu khách hàng trong từng đơn.
- ⚠️ Mọi tham số query là input không tin được:
  - Chỉ cho filter và sort theo một danh sách cột cho phép (*whitelist*), và nên là cột có index.
    Nếu không, user sort theo một cột không index trên bảng lớn là làm chậm cả DB.
  - Giới hạn `limit` tối đa, ví dụ 100. Nếu không, ai đó gọi `?limit=1000000`.

*Offset và cursor*
- *Offset pagination*: `?page=5&per_page=20`, tương ứng SQL `LIMIT 20 OFFSET 80`.
- *Cursor pagination* (còn gọi là *keyset pagination*): client gửi lại một "con trỏ" đánh dấu
  phần tử cuối của trang trước, server lấy tiếp từ đó:
  `WHERE (created_at, id) < (?, ?) ORDER BY created_at DESC, id DESC LIMIT 20`.

| | Offset | Cursor |
|---|---|---|
| Nhảy thẳng tới trang N | Được | Không, chỉ đi tới hoặc lui |
| Tốc độ trang sâu | Chậm dần: DB vẫn đọc rồi bỏ đi `OFFSET` dòng | Nhanh đều ở mọi trang (nếu có index khớp thứ tự sort) |
| Khi dữ liệu thay đổi lúc đang xem | Lặp hoặc sót dòng | Ổn định |
| Hợp với | Trang admin cần nhảy trang | Feed, cuộn vô hạn, sync, export |

- Ví dụ lặp dòng với offset: bạn đang ở trang 1, có 1 đơn mới được thêm lên đầu. Sang trang 2,
  mọi dòng bị đẩy xuống 1 vị trí, nên dòng cuối của trang 1 hiện lại ở đầu trang 2.

*Cursor chứa gì*
- Giá trị cột sort của phần tử cuối trang, cộng một cột *tie-breaker* duy nhất, thường là `id`.
  - Tie-breaker là cột dùng để phân định thứ tự khi cột sort bị trùng giá trị.
  - ⚠️ Sort theo cột không duy nhất (nhiều đơn cùng `created_at`) mà không có tie-breaker thì sót
    hoặc lặp dòng ở ranh giới trang.
- Cách đóng gói: đưa các giá trị vào JSON, rồi mã hoá base64url để thành một chuỗi an toàn khi
  đặt trên URL.
- Cursor phải **opaque** (mờ đục): client coi nó là chuỗi bí ẩn, chỉ gửi lại chứ không tự dựng
  hay sửa.
  - Nhờ vậy server tự do đổi format bên trong sau này.
  - Có thể ký HMAC (một chữ ký dùng secret, module 2.4) để phát hiện client sửa cursor.

*Trả metadata phân trang*
- Cách 1: field `next_cursor` trong body. Bằng `null` khi đã hết dữ liệu.
- Cách 2: header `Link: <https://api.example.com/orders?cursor=abc>; rel="next"` theo RFC 8288.

*Laravel*
- `paginate()`: offset, có tổng số trang, nên chạy thêm một câu `COUNT(*)` mỗi request.
- `simplePaginate()`: offset, không đếm tổng, chỉ biết có trang sau hay không.
- `cursorPaginate()`: cursor pagination.
- Tầng SQL của keyset pagination (index, tie-breaker): [03-database-sql.md](03-database-sql.md)

**Đọc**
- Google AIP: [AIP-158 Pagination](https://google.aip.dev/158)
- Use The Index, Luke: [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)
- [RFC 8288](https://www.rfc-editor.org/rfc/rfc8288) (Web Linking), lướt section 3
- Laravel: [Cursor Pagination](https://laravel.com/docs/pagination#cursor-pagination)

**Nắm chắc khi**
- [ ] Thiết kế được cursor cho sort `-created_at` và viết query SQL tương ứng có tie-breaker
- [ ] Nói được khi nào vẫn chọn offset (admin cần nhảy trang) và cách giảm chi phí `COUNT(*)`

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Idempotency key và retry an toàn

**Vì sao cần học:** Mạng mobile chập chờn, Guzzle hay SDK tự retry, user bấm "Thanh toán" hai
lần. Không có cơ chế idempotency thì hệ thống tạo trùng đơn hoặc trừ tiền hai lần. Câu "user bấm
thanh toán hai lần thì sao" gần như chắc chắn gặp, và người phỏng vấn sẽ đào tới "hai request
trùng đến cùng lúc thì sao".

**Học gì**

*Vấn đề*
1. Client gọi `POST /payments`.
2. Server trừ tiền xong, nhưng response bị mất trên đường về (timeout, mất sóng).
3. Client không biết server đã xử lý hay chưa.
4. Client retry, server trừ tiền lần hai.

POST không idempotent (module 1.1), nên cần một cơ chế để biến nó thành an toàn khi retry.

*Idempotency key*
- Client sinh một key duy nhất (thường là UUID) cho mỗi **ý định** của user, ví dụ "thanh toán
  đơn 123 lúc này", và gửi trong header `Idempotency-Key`.
- Khi retry, client gửi lại **đúng key đó**. Server thấy key đã gặp thì không xử lý lần hai.
- ⚠️ Sinh key mới cho mỗi lần retry là vô nghĩa: server coi đó là một ý định mới.
- Nguồn gốc: header này do Stripe phổ biến. IETF từng có draft chuẩn hoá
  (`draft-ietf-httpapi-idempotency-key-header`) nhưng draft đã hết hạn, chưa thành RFC.

*Server lưu gì*
- Khoá lưu là cặp `(client_id, key)`, vì hai client khác nhau có thể tình cờ sinh cùng key.
- Mỗi bản ghi chứa:
  - Trạng thái: `processing` (đang xử lý) hoặc `completed` (đã xong).
  - Hash của request body, để phát hiện cùng key mà nội dung khác.
  - Status code và body của response, để trả lại y nguyên cho lần retry.

*Luồng xử lý*
1. Server `INSERT` bản ghi key với trạng thái `processing`. Cột `(client_id, key)` có unique
   constraint.
2. Nếu `INSERT` thành công, đây là lần đầu: xử lý nghiệp vụ, lưu response, đổi sang `completed`.
3. Nếu `INSERT` bị trùng key, đọc bản ghi cũ và rẽ nhánh:

| Bản ghi cũ | Trả về | Lý do |
|---|---|---|
| Hash body khác | `422` (draft IETF; Brandur dùng `409`) | Client dùng lại key cho một request khác, là bug phía client |
| Đang `processing` | `409` | Request đầu chưa xong, không được xử lý lần hai |
| Đã `completed` | Đúng response đã lưu | Client chỉ cần kết quả của lần đầu |

- ⚠️ Không làm kiểu `SELECT` xem có key chưa rồi mới `INSERT`. Hai request trùng đến cùng lúc
  đều `SELECT` thấy "chưa có", rồi cả hai cùng xử lý. Đây là *race condition*
  ([13-concurrency.md](13-concurrency.md)).
  - Phải dựa vào unique constraint của DB, hoặc một lệnh lock nguyên tử như `SET key value NX`
    của Redis (chỉ set khi key chưa tồn tại).

*Khi server crash giữa chừng*
- ⚠️ Server crash sau bước 1 để lại bản ghi `processing` mãi mãi, và mọi lần retry đều nhận `409`.
  - Cần đặt hạn cho trạng thái `processing`: quá hạn thì cho phép xử lý lại.
  - Vì có thể xử lý lại, nghiệp vụ bên trong vẫn phải an toàn khi chạy lại.
- Lưu key và kết quả nghiệp vụ trong **cùng một transaction DB** là chắc nhất: hoặc cả hai cùng
  có, hoặc cả hai cùng không.
- Lưu key trong Redis thì nhanh hơn, nhưng có khoảng hở: Redis mất dữ liệu (restart, failover)
  thì mất luôn dấu vết key.

*Lưu bao lâu*
- *TTL* (thời gian sống) phải đủ phủ mọi lần retry hợp lý. Stripe giữ key ít nhất 24 giờ.
- Với response lỗi `5xx` có hai trường phái:
  - Stripe lưu cả `500`, coi kết quả là không xác định: client không retry bằng key mới mà đối soát.
  - Brandur không lưu, mở lại key để client retry. Chỉ làm được khi logic bên trong an toàn khi
    chạy lại (recovery point).

*Các lớp phòng thủ khác*
- Lớp thứ hai: ràng buộc nghiệp vụ tự nhiên, ví dụ unique `order_id` trong bảng `payments`. Kể cả
  khi cơ chế idempotency lỗi, DB vẫn chặn thanh toán trùng cho một đơn.
- Chống bấm đúp ở UI (disable nút sau khi bấm) chỉ là phụ. Server vẫn phải idempotent, vì retry
  còn đến từ mạng, SDK, load balancer.

**Đọc**
- Stripe: [Idempotent requests](https://docs.stripe.com/api/idempotent_requests), [Designing robust and predictable APIs with idempotency](https://stripe.com/blog/idempotency)
- Brandur: [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys): thiết kế đầy đủ với recovery point, đọc kỹ
- AWS Builders' Library: [Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/)
- [draft-ietf-httpapi-idempotency-key-header](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/) (bản draft cuối, tham khảo ngữ nghĩa)

**Nắm chắc khi**
- [ ] Vẽ được luồng xử lý khi request thứ hai đến lúc request đầu còn `processing`, và khi server crash giữa chừng
- [ ] Thiết kế được bảng `idempotency_keys` (cột, unique, index, TTL) cho `POST /payments` (bài tập 2)
- [ ] Giải thích được vì sao idempotency key không thay được unique constraint nghiệp vụ

#### 2.2 Ghi đồng thời, bulk, long-running operation

**Vì sao cần học:** Trang admin có hai nhân viên cùng sửa một sản phẩm, import file Excel nghìn
dòng, export báo cáo mất 10 phút: đây là việc hằng ngày của backend PHP. Làm sai thì mất dữ liệu
âm thầm, hoặc request treo tới khi PHP-FPM và Nginx cắt ngang. Người phỏng vấn hay hỏi "hai người
cùng sửa, một người mất thay đổi" và "thiết kế API cho thao tác chạy lâu".

**Học gì**

*Lost update khi hai người cùng sửa*
- *Lost update* là khi thay đổi của người này bị người kia ghi đè mà không ai biết:
  1. Admin A và admin B cùng mở sản phẩm 5, cả hai thấy giá 100.
  2. A sửa giá thành 120 và lưu.
  3. B (vẫn nhìn bản cũ) sửa tên và lưu cả form, kèm giá 100.
  4. Giá 120 của A mất.

*Optimistic concurrency bằng ETag và If-Match*
- *Optimistic concurrency* là cách chống lost update mà không khoá gì: cứ để mọi người sửa, lúc
  lưu mới kiểm tra "dữ liệu có bị ai đổi từ lúc tôi đọc không".
- *ETag* là một nhãn phiên bản của resource, server gửi trong header response.
- Luồng:
  1. `GET /products/5` trả `ETag: "v7"`.
  2. Client sửa rồi gửi `PUT /products/5` kèm header `If-Match: "v7"`, nghĩa là "chỉ lưu nếu bản
     trên server vẫn là v7".
  3. Nếu bản trên server đã thành v8 (ai đó vừa sửa), server trả `412 Precondition Failed`.
  4. Nếu server bắt buộc có `If-Match` mà client không gửi, server trả `428 Precondition Required`.
- Tầng DB dùng một cột `version`:

  ```sql
  UPDATE products SET price = ?, version = version + 1
  WHERE id = ? AND version = ?;
  -- số dòng bị ảnh hưởng = 0 nghĩa là version đã đổi → trả 412
  ```
- Hai loại ETag:
  - *Strong* ETag, ví dụ `"abc"`: hai bản giống nhau từng byte.
  - *Weak* ETag, ví dụ `W/"abc"`: hai bản tương đương về nghĩa, có thể khác byte.
  - `If-Match` so sánh kiểu strong, nên weak ETag không bao giờ khớp.

*Bulk: nhiều item trong một request*
- Ví dụ: `POST /orders:batchCreate` tạo nhiều đơn một lần.
- Luôn giới hạn số item mỗi request.
- Phải chọn và ghi rõ trong tài liệu một trong hai kiểu:
  - *Atomic*: tất cả thành công hoặc không item nào được tạo.
  - *Partial success*: item nào thành công thì giữ, trả kết quả của từng item. Zalando bắt buộc
    `207 Multi-Status` (không dùng `200`); có API khác trả `200` kèm kết quả từng item.
- ⚠️ Bulk lớn thì không xử lý đồng bộ trong request, mà chuyển sang long-running operation ngay
  dưới đây.

*Long-running operation (LRO)*
- Dùng cho việc chạy lâu hơn một request bình thường chịu được, ví dụ export báo cáo 10 phút.
- Luồng:
  1. Client gọi `POST /reports:export`.
  2. Server tạo một *operation resource* để theo dõi tiến độ, đẩy việc vào queue, trả ngay
     `202 Accepted` kèm `Location: /operations/abc`.
  3. Client `GET /operations/abc` để xem trạng thái: `running`, rồi `succeeded` hoặc `failed`.
  4. Client biết khi xong bằng một trong hai cách: *poll* (hỏi lại định kỳ, theo khoảng thời gian
     server gợi ý trong `Retry-After`), hoặc nhận webhook (module 2.4).
- ⚠️ Operation resource phải lưu bền trong DB, không nằm trong memory của một pod. Nếu không,
  request tiếp theo rơi vào pod khác hoặc pod restart là mất trạng thái.

*Content negotiation*
- *Content negotiation* là việc client và server thoả thuận định dạng dữ liệu qua header:
  - `Accept`: client muốn nhận định dạng gì. Server không trả được định dạng đó thì `406`.
  - `Content-Type`: body client gửi lên là định dạng gì. Server không nhận định dạng đó thì `415`.
  - `Accept-Language`: ngôn ngữ mong muốn.
  - `Accept-Encoding`: kiểu nén chấp nhận được, ví dụ `gzip`.
- Response thay đổi theo header nào thì khai header đó trong `Vary`, ví dụ `Vary: Accept-Language`.
  - ⚠️ Thiếu `Vary` thì cache (CDN, proxy) có thể trả bản tiếng Anh cho user tiếng Việt.

**Đọc**
- RFC 9110: [Section 13: Conditional Requests](https://www.rfc-editor.org/rfc/rfc9110#section-13), [Section 8.8.3: ETag](https://www.rfc-editor.org/rfc/rfc9110#section-8.8.3)
- Google AIP: [AIP-151 Long-running operations](https://google.aip.dev/151), [AIP-233 Batch create](https://google.aip.dev/233)
- Zalando: [chương HTTP status codes and errors](https://opensource.zalando.com/restful-api-guidelines/#http-status-codes-and-errors) (quy tắc dùng `207` cho batch/bulk request)

**Nắm chắc khi**
- [ ] Viết được luồng `ETag`/`If-Match` đầu-cuối từ API tới SQL, và nói UI hiển thị gì khi `412`
- [ ] Thiết kế được API export báo cáo 10 phút: endpoint, status, cách client biết khi xong, cách dọn file kết quả

#### 2.3 Rate limiting, auth và CORS

**Vì sao cần học:** Ba thứ này nằm ở cửa vào của mọi API. Rate limit sai thì một client lỗi
vòng lặp làm sập cả hệ thống. CORS là lỗi mà frontend báo backend nhiều nhất ("GET chạy mà PUT
lỗi CORS"), và cũng là chủ đề hay bị hiểu nhầm là cơ chế bảo mật của server.

**Học gì**

*Rate limiting*
- *Rate limiting* là giới hạn số request một client được gọi trong một khoảng thời gian, ví dụ
  60 request mỗi phút.
- Vượt giới hạn thì trả `429 Too Many Requests` kèm `Retry-After` (bao nhiêu giây nữa mới gọi lại
  được).
- Header báo hạn mức cho client:
  - Kiểu de-facto (ai cũng dùng dù không phải chuẩn): `X-RateLimit-Limit` (hạn mức),
    `X-RateLimit-Remaining` (còn lại bao nhiêu), `X-RateLimit-Reset` (khi nào đặt lại).
  - IETF đang chuẩn hoá hai header `RateLimit` và `RateLimit-Policy`, vẫn là draft.
- Giới hạn theo gì: API key, user, IP, hoặc từng endpoint. Có thể kết hợp.
- Thuật toán đếm (token bucket, sliding window) ở [16-system-design.md](16-system-design.md).
- ⚠️ Client phải tôn trọng `Retry-After` và thêm *jitter* (một khoảng chờ ngẫu nhiên nhỏ). Nếu
  không, mọi client bị chặn sẽ cùng quay lại đúng một giây và lại bị chặn tiếp.

*Auth: xác thực client*

| Cách | Hợp với |
|---|---|
| API key | Server gọi server (server-to-server) |
| OAuth2 (chuẩn cấp token để app hành động thay user) hoặc token cấp cho user | App đại diện cho một user |
| mTLS (hai bên cùng trình chứng chỉ TLS) | Service nội bộ gọi nhau |

- Token đặt trong header `Authorization`, ví dụ `Authorization: Bearer <token>`.
- ⚠️ Không đặt token trong query string (`?token=...`). URL bị ghi vào access log, lịch sử trình
  duyệt, và header `Referer` gửi sang trang khác.

*Chống DoS ở tầng API*
- *DoS* là làm server quá tải để nó không phục vụ được ai. Một request "hợp lệ" nhưng khổng lồ
  cũng làm được việc này.
- Giới hạn kích thước body, số item mỗi request, và độ sâu lồng nhau của JSON.
- OWASP API Top 10 (BOLA, mass assignment) ở [10-security.md](10-security.md).

*CORS: là gì và không là gì*
- *Same-origin policy* là luật của **trình duyệt**: JavaScript trên trang `app.example.com` không
  được đọc response từ một *origin* khác (khác scheme, domain hoặc port), ví dụ `api.example.com`.
- *CORS* là cách server nói với trình duyệt "tôi cho phép origin này đọc response của tôi".
- ⚠️ CORS không bảo vệ server. `curl`, Postman, hay một server khác gọi thẳng API đều không bị
  chặn, vì chúng không phải trình duyệt.

*Simple request và preflight*
- *Simple request* (GET, POST với form thường, không header lạ): trình duyệt gửi thẳng, rồi mới
  xem response có cho phép không.
- Các request sau thì trình duyệt gửi trước một request `OPTIONS` để hỏi, gọi là *preflight*:
  - Method `PUT`, `DELETE`.
  - `Content-Type: application/json`.
  - Có header tuỳ chỉnh, ví dụ `Authorization`, `Idempotency-Key`.
- Luồng preflight:
  1. Trình duyệt gửi `OPTIONS /orders/5` kèm `Origin` và method định dùng.
  2. Server trả các header `Access-Control-Allow-*`.
  3. Nếu được phép, trình duyệt mới gửi request `PUT` thật.
- Đây là lý do "GET chạy mà PUT lỗi CORS".

*Các header CORS*
- `Access-Control-Allow-Origin`: origin được phép.
- `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`: method và header được phép.
- `Access-Control-Allow-Credentials`: cho phép gửi kèm cookie.
- `Access-Control-Max-Age`: trình duyệt nhớ kết quả preflight bao lâu, đỡ phải hỏi lại.
- `Access-Control-Expose-Headers`: header nào JS được đọc. Mặc định JS không đọc được header tuỳ
  chỉnh như `X-RateLimit-Remaining`.

*Cạm bẫy CORS*
- ⚠️ Không dùng `Access-Control-Allow-Origin: *` cùng credentials. Trình duyệt từ chối tổ hợp này.
- ⚠️ Phản chiếu nguyên giá trị `Origin` của request vào `Allow-Origin` kèm credentials là **lỗ hổng**:
  bất kỳ trang độc nào cũng đọc được dữ liệu của user đang đăng nhập. Phải so với whitelist.
  - Laravel: `allowed_origins => ['*']` cùng `supports_credentials => true` trong `config/cors.php`
    thì package tự phản chiếu `Origin`, tức rơi đúng vào lỗ hổng này.
- Khi `Allow-Origin` thay đổi theo request, thêm `Vary: Origin` để cache không trả nhầm header
  cho origin khác.
- ⚠️ Preflight bị `401` vì middleware auth chặn cả `OPTIONS` là lỗi rất hay gặp. Request `OPTIONS`
  không mang token.
- Lỗi CORS chỉ nhìn thấy ở console của trình duyệt, không có trong log server, vì server vẫn trả
  response bình thường. Chính trình duyệt mới là bên chặn JS đọc response đó.

**Đọc**
- [draft-ietf-httpapi-ratelimit-headers](https://datatracker.ietf.org/doc/draft-ietf-httpapi-ratelimit-headers/)
- [MDN: CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS) (đọc hết, có sơ đồ preflight)
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x11-t10/)

**Nắm chắc khi**
- [ ] Tái hiện được lỗi CORS khi gọi `PUT` từ trình duyệt và sửa ở server
- [ ] Giải thích được vì sao cấu hình CORS sai không phải lỗ hổng phía server nhưng phản chiếu `Origin` kèm credentials lại là lỗ hổng

#### 2.4 Webhook

**Vì sao cần học:** Dự án PHP nào cũng nhận webhook (cổng thanh toán, vận chuyển, Zalo, Stripe)
và nhiều dự án phải gửi webhook cho đối tác. Webhook là chỗ hay mất tiền: xử lý trùng một event
thanh toán, hoặc tin một request giả mạo. Câu "thiết kế webhook" và "đối tác nói không nhận được
webhook" rất hay gặp ở mức mid.

**Học gì**

*Webhook là gì*
- *Webhook* là khi hệ thống A chủ động gọi HTTP (thường là `POST`) tới một URL của hệ thống B để
  báo "có chuyện vừa xảy ra", thay vì B phải hỏi A liên tục.
  - Ví dụ: cổng thanh toán gọi `POST https://shop.vn/webhooks/payment` khi khách trả tiền xong.
- Webhook là *at-least-once*: mỗi event được gửi **ít nhất một lần**, có thể nhiều lần. Bên nhận
  phải chịu được event trùng.

*Bên gửi: lưu và gửi*
- Ghi event vào DB trong cùng transaction nghiệp vụ (pattern *outbox*), rồi một worker đọc ra
  và gửi. Không gọi HTTP ngay trong transaction nghiệp vụ ([12-messaging.md](12-messaging.md)).
  - Lý do: gọi HTTP trong transaction thì bên nhận chậm là giữ lock DB lâu, và rollback không thu
    hồi được webhook đã gửi.
- Payload có hai kiểu:
  - Đầy đủ: có `event_id` duy nhất, `type` (ví dụ `order.paid`), `created_at`, và dữ liệu.
  - *Thin event*: chỉ có id, bên nhận tự gọi API để lấy bản mới nhất. Tránh được lỗi dữ liệu cũ.
- Đặt timeout ngắn cho mỗi lần gửi (Standard Webhooks gợi ý 15–30 giây), để một bên nhận chậm
  không làm nghẽn cả worker.

*Bên gửi: retry*
- Retry khi không nhận được `2xx`.
- Dùng *exponential backoff*: khoảng chờ tăng gấp bội sau mỗi lần (1 phút, 2, 4, 8...), cộng
  jitter, trải dài nhiều giờ hoặc nhiều ngày.
- Sau N lần thất bại:
  - Đánh dấu event là thất bại.
  - Cho phép *replay* (gửi lại) thủ công.
  - Tự tắt endpoint nào lỗi liên tục.

*Bên gửi: ký request*
- Bên nhận cần biết request thật sự đến từ bạn, nên bên gửi ký bằng *HMAC*: một mã tính từ nội
  dung và một secret chỉ hai bên biết. Ai không có secret thì không tạo được chữ ký đúng.
- Công thức hay dùng: `HMAC-SHA256(secret, id + "." + timestamp + "." + raw_body)`.
  - Gửi kèm timestamp để bên nhận từ chối request cũ bị gửi lại (*replay attack*).
- Mỗi endpoint một secret riêng.
- Khi *rotate* (đổi) secret, cho hai secret cùng hiệu lực một thời gian để bên nhận kịp cập nhật.

*Bên gửi: cạm bẫy*
- ⚠️ Thứ tự không được đảm bảo: `order.updated` có thể đến trước `order.created`. Kèm
  `created_at` hoặc version để bên nhận bỏ qua event cũ hơn bản đang có.
- ⚠️ *SSRF* (Server-Side Request Forgery): URL webhook do khách nhập, nên kẻ xấu có thể nhập IP
  nội bộ để server của bạn gọi vào hệ thống bên trong. Phải chặn IP nội bộ và địa chỉ metadata của
  cloud (như `169.254.169.254`) khi gửi.

*Bên nhận*
1. **Verify chữ ký trên raw body**, tức chuỗi byte nguyên gốc nhận được.
   - ⚠️ Parse JSON rồi serialize lại để verify thì hỏng: thứ tự key, khoảng trắng, escape ký tự
     có thể khác, nên hash khác.
   - Laravel: lấy raw body bằng `$request->getContent()`.
2. **So sánh chữ ký bằng hàm constant-time** (thời gian so sánh không phụ thuộc vào vị trí ký tự
   sai đầu tiên, để kẻ tấn công không đo thời gian đoán dần chữ ký):
   - PHP: `hash_equals`.
   - Go: `hmac.Equal`.
   - Java: `MessageDigest.isEqual`.
3. **Từ chối timestamp lệch quá vài phút** so với giờ hiện tại.
4. **Idempotent theo `event_id`**: đặt unique constraint trên `event_id`, event trùng thì bỏ qua.
5. **Trả `2xx` nhanh**: chỉ verify, lưu vào DB hoặc queue, rồi trả. Việc xử lý thật để worker làm.
   - Nếu xử lý lâu trong request, bên gửi timeout và gửi lại, sinh thêm event trùng.
- Với việc quan trọng như thanh toán:
  - Gọi lại API của bên gửi để xác nhận trạng thái, không tin hoàn toàn vào payload.
  - Có job *đối soát* (so dữ liệu hai bên định kỳ), vì webhook có thể mất hẳn.

**Đọc**
- [Standard Webhooks specification](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md): tên header (`webhook-id`, `webhook-timestamp`, `webhook-signature`), cách ký, retry
- Stripe: [Receive webhook events](https://docs.stripe.com/webhooks) (đọc phần *Best practices*)

**Nắm chắc khi**
- [ ] Viết được đặc tả webhook `order.paid` cho đối tác: payload, header, verify, retry, cam kết thứ tự (bài tập 3)
- [ ] Viết được endpoint nhận webhook trong Laravel verify trên raw body (`$request->getContent()`) và idempotent theo `event_id`

#### 2.5 Gọi API bên thứ ba

**Vì sao cần học:** Cổng thanh toán, SMS, vận chuyển, AI: dự án nào cũng gọi API bên ngoài, và
bên ngoài thì sớm muộn cũng chậm hoặc chết. Với PHP-FPM, một provider treo không có timeout sẽ
giữ worker, hết worker là cả site đứng. Câu "tích hợp một API hay chết thì thiết kế lớp gọi thế
nào" là câu thiết kế thực tế rất hay gặp.

**Học gì**

*Timeout: luôn đặt*
- Có hai loại timeout:
  - *Connect timeout*: chờ tối đa bao lâu để mở được kết nối.
  - *Read timeout*: đã kết nối rồi, chờ tối đa bao lâu để nhận response.
- ⚠️ Nhiều thư viện mặc định không có timeout cho toàn bộ request, tức có thể chờ vô hạn:
  - Go: `http.Client{}` để giá trị zero (không cấu hình gì).
  - PHP: cURL (`CURLOPT_TIMEOUT` mặc định 0, không giới hạn; riêng connect timeout mặc định của
    libcurl là 300 giây) và Guzzle (`timeout` mặc định 0).
- ⚠️ Laravel HTTP client mặc định timeout 30 giây. Con số này thường quá dài cho một request đồng
  bộ mà user đang đứng chờ.
- Vì sao nguy hiểm với PHP-FPM: mỗi request treo giữ một worker. Provider treo thì worker cạn dần,
  và request không liên quan gì tới provider đó cũng bị kẹt.

*Retry có điều kiện*
- Chỉ retry khi lỗi là tạm thời (module 1.2) **và** thao tác là idempotent.
- Dùng exponential backoff cộng jitter (module 2.4).
- Giới hạn cả số lần retry và tổng thời gian.
  - Ví dụ: timeout 5 giây, tổng 3 lần thử, backoff 1 và 2 giây thì request có thể treo tới
    5 × 3 + 1 + 2 = 18 giây.
- Nếu bên kia hỗ trợ idempotency key (module 2.1) thì gửi kèm, để retry POST cũng an toàn.

*Các pattern chịu lỗi*

| Pattern | Là gì | Ví dụ |
|---|---|---|
| *Circuit breaker* | Đếm lỗi. Lỗi quá ngưỡng thì "ngắt mạch": trả lỗi ngay (*fail fast*) mà không gọi nữa. Sau một lúc chuyển sang *half-open*: cho vài request thử, thành công thì đóng mạch lại | Provider SMS chết, không để mọi request đứng chờ 5 giây timeout |
| *Bulkhead* | Giới hạn số kết nối đồng thời tới mỗi provider, để một provider chậm không chiếm hết tài nguyên | Tối đa 10 request đồng thời tới provider vận chuyển |
| *Fallback* | Phương án thay thế khi gọi thất bại | Trả dữ liệu cache, trả giá trị mặc định, hoặc đẩy vào queue làm sau |

*Quan sát và kiểm thử*
- Log mỗi lần gọi, nhưng che secret và *PII* (thông tin định danh cá nhân như số điện thoại,
  email).
- Đo *latency* (thời gian phản hồi) và tỉ lệ lỗi theo từng provider.
- ⚠️ Môi trường *sandbox* (môi trường thử của provider) có hành vi và rate limit khác production.
  Cần kiểm tra lại ở production với lưu lượng nhỏ.
- Bọc provider sau một interface hoặc adapter ([08-oop-design.md](08-oop-design.md)), để đổi
  provider dễ và thay bằng bản giả (*fake*) trong test.

*Timeout không có nghĩa là thất bại*
- ⚠️ Khi bạn timeout, bên kia có thể **đã xử lý xong**, chỉ là response chưa tới.
- Với thanh toán, không được coi timeout là "chưa trừ tiền" rồi cho user trả lại. Phải hỏi lại
  trạng thái hoặc đối soát: [22-practical-data.md](22-practical-data.md).

*Đối chiếu Java/Go*
- Laravel: `Http::timeout()->connectTimeout()->retry()`. Với Guzzle thuần thì dùng middleware.
  - ⚠️ `Http::retry(3)` là tổng 3 lần thử, không phải 3 lần retry. Không truyền closure điều kiện
    thì retry cả `4xx`.
- Java: thư viện Resilience4j (circuit breaker, retry, bulkhead).
- Go: `context.WithTimeout` để đặt hạn, và thư viện `sony/gobreaker` cho circuit breaker.

**Đọc**
- AWS Builders' Library: [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)
- Laravel: [HTTP Client: Timeout](https://laravel.com/docs/http-client#timeout), [Retries](https://laravel.com/docs/http-client#retries), [Testing / Faking](https://laravel.com/docs/http-client#testing)
- Martin Fowler: [Circuit Breaker](https://martinfowler.com/bliki/CircuitBreaker.html)
- Resilience pattern chi tiết: [14-distributed-systems.md](14-distributed-systems.md)

**Nắm chắc khi**
- [ ] Viết được lớp gọi một provider hay chết trong Laravel: timeout, retry có điều kiện, circuit breaker bằng cache, log, fake trong test
- [ ] Tính được thời gian tối đa một request có thể treo với cấu hình timeout và retry hiện tại của dự án mình

#### 2.6 Tầng Laravel cho API

**Vì sao cần học:** Đây là module riêng cho người làm PHP. Người phỏng vấn hay hỏi "trong
Laravel bạn làm việc X thế nào" để kiểm tra bạn hiểu framework hay chỉ copy mẫu. Các lỗi ở tầng
này (lộ field `password`, mass assignment, rate limit đếm sai khi có nhiều server) đều là lỗi
production thật.

**Học gì**

*API Resources: tách hình dạng API khỏi model*
- *API Resource* là một class chuyển model thành JSON trả ra API. `JsonResource` cho một object,
  `ResourceCollection` cho một danh sách.
- Mục đích: hình dạng (*shape*) của API độc lập với cấu trúc bảng DB.
- ⚠️ `return $model` hoặc `$model->toArray()` thẳng ra API có hai hậu quả:
  - Lộ field không nên lộ: `password`, `remember_token`, cột nội bộ.
  - Đổi schema DB (đổi tên cột) là đổi luôn API, làm vỡ client.
- Các hàm hay dùng:
  - `whenLoaded('customer')`: chỉ trả quan hệ nếu đã được *eager load* (nạp sẵn bằng `with('customer')` trong cùng lúc lấy danh sách). Không có hàm này thì
    Resource tự lazy load quan hệ cho từng phần tử, sinh *N+1 query* (1 query lấy danh sách, rồi
    N query cho N phần tử).
  - `when($condition, $value)`: field chỉ xuất hiện khi điều kiện đúng, ví dụ chỉ admin mới thấy.
  - `mergeWhen()`: gộp nhiều field có điều kiện cùng lúc.
- ID lớn trả dạng string nếu client là JavaScript (module 2.7).

*FormRequest: validate và kiểm quyền đầu vào*
- *FormRequest* là class gom luật validate và kiểm quyền cho một request.
  - `authorize()`: user có được làm việc này không.
  - `rules()`: luật validate từng field.
  - `prepareForValidation()`: chuẩn hoá dữ liệu trước khi validate, ví dụ cắt khoảng trắng.
  - `validated()` hoặc `safe()`: lấy **chỉ những field đã qua validate**.
- ⚠️ *Mass assignment*: `Order::create($request->all())` cho phép client gửi thêm field như
  `is_paid=1` hay `user_id=999` và được ghi thẳng vào DB. Dùng `validated()` và khai `$fillable`
  trên model.
- ⚠️ Request có header `Accept: application/json` thì lỗi validation trả `422` dạng JSON. Thiếu
  header này, Laravel coi là request từ form web và **redirect** về trang trước. Đây là lỗi hay gặp
  khi test bằng Postman.

*Auth: Sanctum hay Passport*

| | Sanctum: token | Sanctum: SPA cookie | Passport |
|---|---|---|---|
| Là gì | *Personal access token*, có *abilities* (danh sách quyền của token) | Đăng nhập bằng cookie session như web thường | Một OAuth2 server đầy đủ |
| Hợp với | App mobile, server-to-server | SPA của chính bạn, cùng domain gốc với API | Cấp quyền cho ứng dụng **bên thứ ba** |
| Lưu ý | Token lưu trong DB, thu hồi được | Cần CSRF token (mã chống trang khác lợi dụng cookie để gửi request thay user) vì dùng cookie | Hỗ trợ các luồng OAuth2 như authorization code + PKCE (luồng đăng nhập cho app không giữ được secret), client credentials (server tự xác thực bằng secret của mình) |

- ⚠️ Chọn Passport chỉ để "có token" là nặng không cần thiết. Sanctum đủ cho hầu hết trường hợp.

*Rate limiting*
- Khai giới hạn:

  ```php
  RateLimiter::for('api', fn ($r) => Limit::perMinute(60)->by($r->user()?->id ?: $r->ip()));
  ```

  rồi gắn middleware `throttle:api` cho route (từ Laravel 11, group `api` không có sẵn
  `throttle`). Ví dụ trên đếm theo user nếu đã đăng nhập, theo IP
  nếu chưa.
- Vượt giới hạn thì Laravel trả `429` kèm `Retry-After` và các header `X-RateLimit-*`.
- ⚠️ Bộ đếm nằm trong cache. Có nhiều server mà cache driver là `file` hoặc `array` thì mỗi server
  đếm riêng: với 4 server chia tải đều, giới hạn thực tế thành khoảng 240 thay vì 60. Dùng Redis chung.

*Idempotency*
- Laravel không có sẵn. Hai cách:
  - Tự viết middleware: unique constraint trong DB hoặc `Cache::lock`, lưu response để trả lại.
  - Dùng package cộng đồng.
- Cách nào cũng vậy, vẫn phải hiểu đủ luồng ở module 2.1.

*Versioning*
- Dùng route group `prefix('v1')`, và tách Resource theo version.
- Tránh copy cả controller cho mỗi version. Thường chỉ shape của response khác nhau.

*Đào sâu (🔴): Octane*
- *Octane* chạy Laravel như một process sống lâu, phục vụ nhiều request liên tiếp, khác PHP-FPM
  khởi động sạch mỗi request.
- ⚠️ Vì vậy tài nguyên dùng lại giữa các request (HTTP client đã cấu hình, singleton) không được
  giữ state của một request cụ thể, ví dụ user hiện tại. Nếu không, request sau nhìn thấy dữ liệu
  của request trước.

**Đọc**
- Laravel: [Eloquent API Resources](https://laravel.com/docs/eloquent-resources), [Form Request Validation](https://laravel.com/docs/validation#form-request-validation), [Sanctum](https://laravel.com/docs/sanctum), [Passport](https://laravel.com/docs/passport) (đọc mục *Passport or Sanctum?*), [Rate Limiting (routing)](https://laravel.com/docs/routing#rate-limiting), [Rate Limiting (RateLimiter)](https://laravel.com/docs/rate-limiting)
- Laravel: [Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment)

**Nắm chắc khi**
- [ ] Viết được `OrderResource` dùng `whenLoaded()` và chứng minh bằng query log là không có N+1
- [ ] Giải thích được khi nào chọn Sanctum token, Sanctum SPA cookie hay Passport cho 3 loại client
- [ ] Viết được middleware idempotency cho một route `POST`, xử lý đủ 4 nhánh ở 2.1
- [ ] Cấu hình được rate limit khác nhau cho user thường, user trả phí và IP chưa đăng nhập

#### 2.7 Serialization

**Vì sao cần học:** *Serialization* là việc biến dữ liệu trong code thành chuỗi byte để gửi đi
(thường là JSON), và ngược lại. Lỗi ở tầng này rất khó thấy: ID bị làm tròn âm thầm trên
frontend, `[]` thay vì `{}` làm app iOS crash, giờ lệch vì thiếu múi giờ. Câu "vì sao không trả
ID int64 dạng số" hay gặp ở mức mid.

**Học gì**

*Số lớn và ID*
- ⚠️ Số trong JavaScript là số thực 64-bit, chỉ biểu diễn chính xác số nguyên tới `2^53 - 1`
  (khoảng 9 triệu tỉ).
- ID kiểu int64, ví dụ ID sinh theo kiểu *Snowflake* (ID 64-bit ghép từ thời gian và số máy), vượt
  ngưỡng này. `JSON.parse` làm tròn chúng **âm thầm**, không báo lỗi.
  - Ví dụ: `JSON.parse('{"id": 9007199254740993}').id` ra `9007199254740992`.
- Cách sửa: trả ID dạng **string**, ví dụ `"id": "9007199254740993"`.
  - Protobuf khi chuyển sang JSON cũng encode int64 thành string vì lý do này.

*Tiền và thời gian*
- Tiền: dùng số nguyên theo đơn vị nhỏ nhất (*minor unit*, ví dụ cent) hoặc string decimal như
  `"199000.50"`. Không dùng số thực ([22-practical-data.md](22-practical-data.md)).
- Ngày giờ: dùng chuẩn ISO 8601 hoặc RFC 3339 **có offset múi giờ**, ví dụ `2026-09-23T08:00:00Z`
  (`Z` là UTC).
- Tránh *epoch* (số giây tính từ 1970) vì client không biết con số là giây hay mili giây.

*null so với thiếu field*
- Với PATCH, hai trường hợp này có nghĩa khác nhau:
  - Không gửi field: giữ nguyên giá trị cũ.
  - Gửi `null`: xoá giá trị.
- Phải định nghĩa rõ trong tài liệu API, và code phía server phải phân biệt được hai trường hợp.

*Cạm bẫy JSON trong PHP*
- ⚠️ `json_encode([])` ra `[]`, không phải `{}`. Mảng PHP rỗng không biết mình là list hay object.
  - Client dùng ngôn ngữ có kiểu chặt (Swift, Kotlin) đang chờ object mà nhận mảng thì crash.
  - Sửa bằng `(object)[]`, hoặc cờ `JSON_FORCE_OBJECT` (cờ này ép **mọi** mảng thành object, nên
    chỉ dùng có chủ đích).
- Dùng cờ `JSON_THROW_ON_ERROR` để lỗi encode/decode ném exception, thay vì âm thầm trả `false`
  hoặc `null`.
- `json_decode` với cờ `JSON_BIGINT_AS_STRING` để số vượt `PHP_INT_MAX` được giữ dạng string thay
  vì thành float bị mất chính xác. Số trong phạm vi int64 vẫn đọc ra int.

*Các format khác JSON*

| Format | Đặc điểm | Hay dùng cho |
|---|---|---|
| Protobuf | Nhị phân. Mỗi field được định danh bằng một số (*tag*). Cần file schema `.proto` | gRPC (module 3.3) |
| Avro | Nhị phân, schema viết bằng JSON, thường đi với *Schema Registry* (nơi lưu các phiên bản schema) | Kafka |
| MessagePack | Như JSON nhưng dạng nhị phân, không cần schema | Khi cần gọn hơn JSON mà không muốn quản lý schema |

*Schema evolution*
- *Schema evolution* là việc thay đổi cấu trúc dữ liệu theo thời gian mà các bên đọc cũ và mới
  vẫn chạy.
- Quy tắc: field mới phải có giá trị mặc định, để:
  - Reader mới đọc được dữ liệu cũ (thiếu field thì dùng mặc định).
  - Reader cũ bỏ qua được field mới.

*Bảo mật*
- ⚠️ Không dùng serialization gắn với ngôn ngữ cho dữ liệu từ bên ngoài, ví dụ PHP `unserialize`
  hay Java native serialization. Kẻ tấn công dựng dữ liệu để tạo object tuỳ ý và có thể chạy code
  trên server ([10-security.md](10-security.md)).

**Đọc**
- PHP: [json_encode](https://www.php.net/manual/en/function.json-encode.php), [JSON constants](https://www.php.net/manual/en/json.constants.php)
- Protobuf: [ProtoJSON Format](https://protobuf.dev/programming-guides/json/) (bảng mapping, int64 thành string)
- [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) (section 5.6)

**Nắm chắc khi**
- [ ] Tái hiện được việc `JSON.parse` làm hỏng ID `9007199254740993` và sửa ở API Resource
- [ ] Chỉ ra được chỗ API của mình trả `[]` thay vì `{}` làm client typed (Swift, Kotlin) crash

---

### Chặng 3: Senior 🔴

#### 3.1 Tiến hoá API: versioning, deprecation, backward compatibility

**Vì sao cần học:** API sống lâu hơn code viết ra nó. Khi đã có app mobile và đối tác dùng API,
mọi thay đổi đều có thể làm vỡ một client bạn không kiểm soát được. Senior được kỳ vọng biết
thay đổi nào là breaking, và đổi được API mà không bắt ai phải cập nhật ngay. Câu "cần đổi kiểu
một field mobile đang dùng thì làm thế nào" rất hay gặp.

**Học gì**

*Ba cách đánh version*
- *Breaking change* là thay đổi làm client đang chạy bị lỗi. Versioning là cách cho client cũ tiếp
  tục dùng bản cũ trong khi bản mới ra đời.

| Cách | Ví dụ | Ưu | Nhược |
|---|---|---|---|
| Version trong URL | `/v1/orders` | Rõ ràng, dễ route, dễ cache | URL đổi khi lên version |
| Header theo ngày (kiểu Stripe) | `Stripe-Version: 2026-08-26.dahlia` | URL sạch, mỗi client ghim một ngày | Phải khai `Vary` cho cache, khó thấy khi debug |
| Media type | `Accept: application/vnd.acme.v2+json` | Đúng tinh thần content negotiation (module 2.2) | Ít người quen, khó thử nhanh bằng trình duyệt |

- Mục tiêu thật sự là **ít phải tăng version**: thiết kế sao cho phần lớn thay đổi không breaking.

*Thay đổi nào là breaking*
- Breaking:
  - Thêm field **bắt buộc** vào request. Client cũ không gửi field đó nên bị lỗi.
  - Xoá, đổi tên, hoặc đổi kiểu một field.
  - Siết validation, ví dụ trước cho tên 255 ký tự, giờ chỉ 100.
  - Đổi status code hoặc format lỗi.
- ⚠️ Tệ nhất: đổi **ý nghĩa** của field mà giữ nguyên tên, ví dụ `amount` từ đơn vị đồng sang
  nghìn đồng. Không có lỗi rõ ràng nào, chỉ có số sai.
- **Có thể** breaking:
  - Thêm giá trị mới vào enum trong response. Client viết `switch` mà không có nhánh `default` sẽ
    crash khi gặp giá trị lạ.
  - Đổi thứ tự sắp xếp mặc định, hoặc page size mặc định.
- Không breaking:
  - Thêm endpoint mới.
  - Thêm field optional vào response, với điều kiện client bỏ qua field lạ.

*Mobile app là trường hợp khó nhất*
- Web deploy là mọi user có bản mới. App mobile thì bản cũ còn chạy trên máy người dùng nhiều năm.
- Vì vậy phải giữ API cũ rất lâu, hoặc có cơ chế *force update* (bắt user cập nhật app mới được
  dùng tiếp).

*Tolerant reader*
- *Tolerant reader* là nguyên tắc cho client: chỉ đọc những gì mình cần, và dễ dãi với phần còn
  lại.
  - Bỏ qua field lạ.
  - Không fail khi enum có giá trị lạ, mà xử lý như một trạng thái "không rõ".
- Phía server: ghi rõ trong tài liệu "enum này có thể được mở rộng", để client biết phải chuẩn bị.

*Expand–contract: đổi field mà không breaking*
1. **Expand** (mở rộng): thêm field mới, ví dụ `amount_minor` (số nguyên) bên cạnh `amount` cũ.
2. Trả **cả hai** field trong một thời gian.
3. Đo xem còn client nào đọc field cũ không.
4. **Contract** (thu hẹp): khi không còn ai dùng, xoá field cũ.

*Deprecation: ngừng một endpoint đúng cách*
- *Deprecation* là thông báo "thứ này sắp bị bỏ, hãy chuyển đi". Quy trình:
  1. Thông báo trước cho client.
  2. Đo client nào còn gọi, bằng log theo API key hoặc app version.
  3. Chỉ gỡ khi đã hết người dùng, hoặc đã tới hạn cam kết.
- Các header chuẩn:
  - `Deprecation: @1788134400` theo RFC 9745.
    - Giá trị là Unix timestamp viết dạng *structured field* (có `@` ở đầu).
    - Là thời điểm bắt đầu deprecated, có thể ở quá khứ hoặc tương lai.
  - `Sunset: Wed, 31 Mar 2027 00:00:00 GMT` theo RFC 8594.
    - Giá trị là *HTTP-date*, tức định dạng ngày giờ chuẩn của HTTP.
    - Là thời điểm endpoint ngừng phục vụ.
    - ⚠️ `Sunset` không được sớm hơn `Deprecation`.
  - `Link: <https://...>; rel="deprecation"` trỏ tới tài liệu hướng dẫn chuyển đổi.
- Sau hạn: trả `410 Gone` kèm thông báo rõ ràng, không trả `404` khó hiểu.

**Đọc**
- [RFC 9745: The Deprecation HTTP Response Header Field](https://www.rfc-editor.org/rfc/rfc9745), [RFC 8594: The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594)
- Google AIP: [AIP-180 Backwards compatibility](https://google.aip.dev/180) (bảng thay đổi nào là breaking, rất đáng đọc)
- Stripe: [APIs as infrastructure: future-proofing Stripe with versioning](https://stripe.com/blog/api-versioning)
- Zalando: [chương Compatibility](https://opensource.zalando.com/restful-api-guidelines/#compatibility) và [Deprecation](https://opensource.zalando.com/restful-api-guidelines/#deprecation)
- Martin Fowler: [Tolerant Reader](https://martinfowler.com/bliki/TolerantReader.html)

**Nắm chắc khi**
- [ ] Phân loại được 10 thay đổi cho sẵn thành breaking/không/có thể, và nói cách làm không breaking cho từng cái
- [ ] Lập được kế hoạch đổi kiểu một field đang được mobile dùng: các bước, header, cách đo, hạn gỡ
- [ ] Viết đúng cú pháp `Deprecation` và `Sunset` cho một endpoint sẽ ngừng sau 6 tháng

#### 3.2 GraphQL

**Vì sao cần học:** GraphQL hay được đề xuất khi có nhiều loại client (web, mobile) cần dữ liệu
khác nhau. Senior cần biết nó giải quyết gì và cái giá phải trả: N+1, khó cache, dễ bị query phá
hoại. Người phỏng vấn thường hỏi "GraphQL gặp N+1 thế nào" và "bảo vệ GraphQL public ra sao".

**Học gì**

*GraphQL là gì*
- *GraphQL* là một ngôn ngữ truy vấn cho API. Toàn bộ API chỉ có **một endpoint** (thường là
  `POST /graphql`), và client tự viết query nói rõ mình cần những field nào.

  ```graphql
  query {
    orders(first: 10) {
      id
      total
      customer { name }
    }
  }
  ```
- Server khai một *schema* có kiểu dữ liệu rõ ràng, viết bằng *SDL* (Schema Definition Language).
- *Introspection*: client hỏi được chính server "schema của anh gồm những gì", nhờ đó có tooling
  tự gợi ý và sinh code.
- Ba loại thao tác:
  - *Query*: đọc.
  - *Mutation*: ghi.
  - *Subscription*: nhận dữ liệu đẩy về khi có thay đổi.

*Lỗi trả 200*
- ⚠️ GraphQL thường trả HTTP `200` kể cả khi có lỗi, kèm mảng `errors` trong body. Có thể kèm cả
  `data` một phần (field nào lấy được thì vẫn trả).
- Hệ quả: monitoring đếm lỗi theo status code sẽ không thấy lỗi. Phải đọc mảng `errors`.
- Spec GraphQL over HTTP (còn là draft) với media type `application/graphql-response+json`: có
  `data` khác `null` thì trả `2xx`; request lỗi từ đầu (parse, validation) thì trả `4xx`.

*N+1 và DataLoader*
- *Resolver* là hàm lấy dữ liệu cho một field. Query ở trên có resolver `customer` chạy **cho mỗi
  order**: 10 order là 10 query lấy customer, cộng 1 query lấy order. Đây là N+1.
- *DataLoader* sửa bằng cách:
  1. Gom tất cả key được hỏi trong cùng một lượt, ví dụ 10 `customer_id`.
  2. Chạy một query duy nhất `WHERE id IN (...)`.
  3. Cache kết quả trong phạm vi request, để cùng một customer không bị lấy lại.
- ⚠️ Cache của DataLoader phải theo **từng request**, không dùng chung giữa các user. Dùng chung
  thì user này có thể thấy dữ liệu mà chỉ user kia được xem.

*Bảo vệ server khỏi query phá hoại*
- Client tự viết query, nên một query lồng sâu (`orders { customer { orders { customer ... } } }`)
  có thể làm server sập. Các lớp bảo vệ:
  - Giới hạn *depth* (độ sâu lồng nhau).
  - Tính *complexity* hay *cost* (điểm chi phí) của query, vượt ngưỡng thì từ chối.
  - Giới hạn số item mỗi list.
  - Rate limit theo cost thay vì theo số request.
- *Authorization* (kiểm quyền) phải làm ở tầng resolver hoặc tầng business, cho từng field. Không
  có endpoint riêng để đặt middleware như REST.

*Caching*
- Khó cache hơn REST, vì mọi request đều là `POST` tới cùng một URL với body khác nhau, nên CDN và
  HTTP cache không dùng được như bình thường.
- Các cách bù lại:
  - *Normalized cache* phía client (Apollo, Relay): client lưu từng object theo id, dùng lại giữa
    các query.
  - Cache ở DataLoader.
  - Persisted queries qua `GET` (ngay dưới).
- *Persisted queries*:
  - Client chỉ gửi hash của query thay vì cả query. Gửi được qua `GET`, nên CDN cache được.
  - *Trusted documents*: query được đăng ký trước lúc build, server chỉ chạy những query đã đăng
    ký, nên chặn được query tuỳ ý.
  - ⚠️ *APQ* (Automatic Persisted Queries) cho client tự đăng ký query lúc chạy, nên chỉ để cache,
    không chặn được query tuỳ ý.

*Trong PHP*
- *Lighthouse*: thư viện GraphQL cho Laravel, kiểu *schema-first* (viết schema trước, gắn resolver
  bằng directive).
  - Có directive `@with` và batch loader để chống N+1.
- `webonyx/graphql-php`: thư viện nền, Lighthouse xây trên nó.

*Đào sâu (🔴)*
- *Federation* và *schema stitching*: ghép schema của nhiều service thành một schema chung. Biết là
  có là đủ.

**Đọc**
- [GraphQL Learn](https://graphql.org/learn/): đọc hết phần *Learn*, đặc biệt *Best Practices* (pagination, authorization, caching)
- [graphql/dataloader](https://github.com/graphql/dataloader): README
- Lighthouse: [The N+1 Query Problem](https://lighthouse-php.com/master/performance/n-plus-one.html), [Resource Exhaustion](https://lighthouse-php.com/master/security/resource-exhaustion.html) (depth, complexity)

**Nắm chắc khi**
- [ ] Tái hiện được N+1 trong một schema `orders { customer { name } }` và sửa bằng batch loader
- [ ] Nêu được 4 lớp bảo vệ một GraphQL public khỏi query phá hoại

#### 3.3 gRPC và Protobuf

**Vì sao cần học:** Khi hệ thống tách thành nhiều service, gRPC là lựa chọn phổ biến cho giao
tiếp nội bộ, nhất là giữa các service Go và Java. Người làm PHP thường gặp gRPC khi phải gọi sang
service của team khác. Câu "khi nào chọn REST, GraphQL, gRPC" và "sửa `.proto` thế nào không phá
client cũ" là câu senior kinh điển.

**Học gì**

*gRPC là gì*
- *gRPC* là một framework gọi hàm từ xa (*RPC*, Remote Procedure Call): client gọi một hàm như gọi
  hàm local, gRPC lo việc gửi qua mạng.
- Bạn viết file `.proto` mô tả các hàm và kiểu dữ liệu. Công cụ sinh code client và server cho
  nhiều ngôn ngữ từ file đó.

  ```proto
  service OrderService {
    rpc GetOrder(GetOrderRequest) returns (Order);
  }
  message Order {
    int64 id = 1;      // số 1 là số field, thứ được gửi trên dây
    string status = 2;
  }
  ```
- Chạy trên HTTP/2, nên có *multiplexing* (nhiều request song song trên một kết nối) và
  streaming.
- Dữ liệu mã hoá bằng Protobuf: nhị phân, nhỏ và nhanh hơn JSON.
- Bốn kiểu RPC:
  - *Unary*: gửi một request, nhận một response. Giống REST bình thường.
  - *Server streaming*: gửi một request, nhận về một dòng nhiều response.
  - *Client streaming*: gửi lên một dòng nhiều request, nhận một response.
  - *Bidirectional*: hai bên cùng gửi dòng dữ liệu cùng lúc.

*Deadline và status code*
- *Deadline* là thời điểm mà sau đó client không cần kết quả nữa. Client đặt deadline.
- Deadline được **lan truyền** qua các service: A gọi B với deadline còn 2 giây, B gọi C thì C chỉ
  còn phần thời gian còn lại. Java và Go tự lan truyền (trong Go, deadline đi theo `context`);
  C++ phải bật.
- Hết hạn thì nhận status `DEADLINE_EXCEEDED`.
- Server nên kiểm tra context để dừng việc vô ích khi client đã bỏ cuộc.
- gRPC có bộ status code riêng, không dùng status HTTP: `INVALID_ARGUMENT`, `NOT_FOUND`,
  `UNAVAILABLE`...
- `UNAVAILABLE` (service tạm không sẵn sàng) thường retry được.

*Tương thích của file .proto*
- ⚠️ Trên dây chỉ có **số field**, không có tên field. Vì vậy:
  - Không đổi số của field đang dùng.
  - Không dùng lại số của field đã xoá. Client cũ sẽ hiểu dữ liệu mới theo nghĩa cũ.
  - Khi xoá field, khai `reserved 5; reserved "old_name";` để trình biên dịch chặn ai đó vô tình
    dùng lại.
- Đổi tên field: an toàn với dữ liệu nhị phân, nhưng phá JSON mapping (JSON dùng tên field) và phá
  code đã sinh ra.
- Đổi kiểu field phần lớn là breaking.
- proto3: field không được gửi thì đọc ra giá trị mặc định (`0`, `""`, `false`). Vì vậy không phân
  biệt được "không gửi" và "gửi 0", trừ khi khai field là `optional`.
- Enum phải có giá trị `0`, và quy ước đặt tên là `..._UNSPECIFIED`, để phân biệt "chưa đặt" với
  một giá trị thật.
- Dùng `buf breaking` trong CI để tự phát hiện thay đổi breaking.

*Vận hành: trình duyệt và load balancing*
- Trình duyệt không gọi gRPC trực tiếp được. Phải dùng *gRPC-Web* hoặc một gateway đứng giữa.
- *grpc-gateway* sinh ra một REST/JSON API từ annotation trong `.proto`.
- ⚠️ Load balancing bị lệch:
  1. HTTP/2 giữ kết nối lâu và chạy mọi request trên cùng kết nối đó.
  2. *L4 load balancer* (cân bằng tải ở tầng TCP) chỉ chọn pod lúc mở kết nối.
  3. Kết nối đã mở thì mọi request sau đều vào đúng pod đó, nên thêm pod mới không giúp gì.
- Cách sửa:
  - Dùng *L7 load balancer*, loại hiểu HTTP/2 và chia từng request.
  - *Client-side load balancing*: client tự mở kết nối tới nhiều pod và chia request.
  - *Service mesh* (như Istio, Linkerd), có proxy cạnh mỗi pod lo việc chia tải.

*gRPC trong PHP*
- PHP-FPM không làm gRPC server được, vì mô hình mỗi request một lần chạy không hợp với kết nối
  HTTP/2 sống lâu.
- Làm client: dùng extension `grpc`.
- Làm server: qua RoadRunner (application server viết bằng Go, chạy worker PHP).

*Chọn REST, GraphQL hay gRPC*

| | REST | GraphQL | gRPC |
|---|---|---|---|
| Hợp với | API public, CRUD | Nhiều loại client cần ghép dữ liệu linh hoạt | Nội bộ service-to-service |
| Điểm mạnh | Cache HTTP, trình duyệt gọi thẳng, tooling phong phú | Client lấy đúng field cần | Latency thấp, streaming, contract chặt |
| Điểm yếu | Client có thể phải gọi nhiều endpoint | N+1, khó cache, cần chống query phá hoại (module 3.2) | Không gọi thẳng từ trình duyệt, cần L7 LB |

- Cần server chủ động đẩy dữ liệu xuống trình duyệt (thông báo, chat) thì có ba lựa chọn:
  - *SSE* (Server-Sent Events): một chiều từ server xuống, chạy trên HTTP thường.
  - *WebSocket*: hai chiều.
  - *Long polling*: client hỏi và server giữ request tới khi có dữ liệu. Dùng làm phương án dự
    phòng.
- Laravel: Reverb (WebSocket server) và Echo (thư viện phía client) cho WebSocket.
- Chi tiết giao thức: [02-networking.md](02-networking.md).

**Đọc**
- gRPC: [Core concepts](https://grpc.io/docs/what-is-grpc/core-concepts/), [Deadlines](https://grpc.io/docs/guides/deadlines/), [Status codes](https://grpc.io/docs/guides/status-codes/), [PHP](https://grpc.io/docs/languages/php/)
- Protobuf: [Language Guide (proto3)](https://protobuf.dev/programming-guides/proto3/) (mục *Updating A Message Type*), [Proto Best Practices](https://protobuf.dev/best-practices/dos-donts/)
- [buf breaking](https://buf.build/docs/breaking/)
- Kubernetes blog: [gRPC Load Balancing on Kubernetes without Tears](https://kubernetes.io/blog/2018/11/07/grpc-load-balancing-on-kubernetes-without-tears/)

**Nắm chắc khi**
- [ ] Mô tả được các bước xoá `phone`, đổi `age` thành `birth_date`, thêm `email` trong một message mà không phá client cũ (bài tập 4)
- [ ] Giải thích được vì sao thêm pod B mà tải gRPC vẫn dồn vào một pod, và 3 cách sửa
- [ ] Chọn và bảo vệ được REST/GraphQL/gRPC cho một hệ có web, mobile và 20 service nội bộ

#### 3.4 Contract, tài liệu và hạ tầng API

**Vì sao cần học:** Khi nhiều team và đối tác cùng dùng một API, "tài liệu trên Confluence" không
đủ. Cần một *contract* (bản mô tả chính xác API nhận gì, trả gì) mà máy đọc được, để sinh code,
test và chặn breaking change tự động. Senior cũng hay được hỏi về tầng hạ tầng trước API:
gateway, BFF, tracing.

**Học gì**

*OpenAPI*
- *OpenAPI* là chuẩn viết contract cho REST API bằng YAML hoặc JSON: có những endpoint nào, tham
  số gì, body và response có schema thế nào.
- Bản 3.1:
  - Schema Object là superset của *JSON Schema* 2020-12 (chuẩn mô tả hình dạng dữ liệu JSON),
    nên dùng lại được tooling của JSON Schema.
  - Có mục `webhooks` ở top-level để mô tả webhook bạn gửi đi.
- Bản 3.2 (phát hành 09/2025) thêm:
  - Method `QUERY`.
  - Mô tả streaming: `itemSchema` cho SSE và JSON Lines.
  - Vị trí tham số mới `querystring`.
  - Tag phân cấp (field `parent`).
  - OAuth device flow.
- ⚠️ Kiểm tra tooling của mình đã hỗ trợ 3.2 chưa trước khi nâng.

*Contract-first và code-first*

| | Contract-first | Code-first |
|---|---|---|
| Làm thế nào | Viết spec trước, review, rồi sinh stub, client, mock từ spec | Viết code trước, sinh spec từ code |
| Ưu | Frontend và backend làm song song dựa trên mock. Thiết kế được review trước khi code | Nhanh lúc đầu, spec luôn khớp code |
| Nhược | Tốn công viết spec, phải giữ spec và code khớp nhau | Spec dễ chỉ phản ánh "code đang làm gì" thay vì "API nên thế nào" |

- Laravel: sinh spec từ code bằng package (ví dụ Scramble) là code-first. Với API public, cân nhắc
  có spec viết tay.

*Dùng spec trong CI và test*
- Validate request và response trong test theo spec, để phát hiện code trả sai shape.
- *Lint* spec (kiểm tra theo bộ quy tắc, ví dụ tên field thống nhất) bằng Spectral.
- Phát hiện breaking change bằng `oasdiff`: so spec của PR với spec hiện tại, chặn PR nếu breaking
  (module 3.1).
- *Contract test* kiểu *consumer-driven* (bên gọi tự viết kỳ vọng, bên cung cấp chạy kiểm tra),
  ví dụ Pact, giữa các service nội bộ: [20-testing-quality.md](20-testing-quality.md).

*Tài liệu tốt gồm gì*
- Ví dụ request và response thật.
- Danh sách mã lỗi và cách xử lý từng mã.
- Rate limit và idempotency.
- *Changelog* (nhật ký thay đổi) và hướng dẫn migrate.
- SDK sinh từ spec: đúng chuẩn, nhưng thêm gánh bảo trì cho mỗi ngôn ngữ.

*Tracing xuyên API*
- *Tracing* là theo dấu một request đi qua nhiều service. Chuẩn chung là *W3C Trace Context*, gồm
  hai header:
  - `traceparent` có dạng `00-<trace-id>-<parent-id>-<flags>`:
    - `00`: version.
    - `trace-id`: 32 ký tự hex, chung cho cả chuỗi request.
    - `parent-id`: id của *span* cha (một bước xử lý trong chuỗi).
    - `flags`: cờ, ví dụ trace này có được lấy mẫu (*sampled*) để lưu hay không.
  - `tracestate`: thông tin thêm riêng của từng hệ thống tracing.
- ⚠️ Gateway và mọi service phải chuyển tiếp hai header này, giữ nguyên `trace-id`. Service nào
  tham gia trace thì đổi `parent-id` thành id span của mình. Một chỗ làm rơi là chuỗi trace bị đứt.
- Chi tiết: [18-reliability-observability.md](18-reliability-observability.md).

*API gateway và BFF*
- *API gateway* là lớp đứng trước mọi service, lo các việc chung:
  - Routing request tới đúng service.
  - Verify token.
  - Rate limit.
  - *TLS termination* (giải mã HTTPS ở gateway, phía sau dùng HTTP nội bộ).
  - Log và metric.
  - *Canary* (chuyển một phần nhỏ traffic sang bản mới để thử).
  - Ví dụ: Kong, AWS API Gateway, Envoy, Nginx.
- ⚠️ Không đặt logic nghiệp vụ vào gateway.
- ⚠️ Gateway phải *HA* (high availability, có dự phòng), vì nó chết là mọi API chết.
- *BFF* (Backend For Frontend): mỗi loại client (web, mobile) có một backend mỏng riêng, ghép dữ
  liệu từ các service thành đúng shape màn hình cần.
  - Đổi lại: thêm một tầng phải vận hành, và logic dễ bị nhân bản giữa các BFF.

**Đọc**
- [OpenAPI 3.2.0](https://spec.openapis.org/oas/v3.2.0.html), [OpenAPI 3.1.1](https://spec.openapis.org/oas/v3.1.1.html); [learn.openapis.org](https://learn.openapis.org/) để học từ đầu
- [Spectral](https://github.com/stoplightio/spectral), [oasdiff](https://github.com/oasdiff/oasdiff)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/): section 3 (`traceparent`, `tracestate`)
- Sam Newman: [Backends For Frontends](https://samnewman.io/patterns/architectural/bff/)
- [Pact docs](https://docs.pact.io/)

**Nắm chắc khi**
- [ ] Viết được spec OpenAPI cho `orders` gồm lỗi RFC 9457 và pagination cursor, lint sạch bằng Spectral (bài tập 1)
- [ ] Thiết lập được `oasdiff` trong CI để chặn PR có breaking change
- [ ] Đọc được một `traceparent` và chỉ ra trace id, span cha, cờ sampled

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. PUT và PATCH khác nhau thế nào? Vì sao PUT là idempotent?** (1.1)
- Ý phải có: thay toàn bộ so với sửa một phần; gửi lại PUT cho cùng state; PATCH tuỳ nội dung
- Điểm cộng: Merge Patch và JSON Patch; idempotent nói về tác động lên server, không về response

**2. `401` và `403` khác nhau thế nào? `400` và `422`?** (1.2)
- Ý phải có: chưa xác thực so với không có quyền; sai định dạng so với sai nghiệp vụ
- Điểm cộng: trả `404` thay `403` để giấu resource; `401` kèm `WWW-Authenticate`

**3. Tạo resource thành công thì trả status gì, kèm header gì?** (1.2)
- Ý phải có: `201` + `Location`; xử lý bất đồng bộ thì `202`

**4. Vì sao GET không nên có side effect?** (1.1)
- Ý phải có: crawler, prefetch, proxy retry gọi GET tuỳ ý; cache
- Red flag: link "xoá" dạng `GET /delete?id=`

**5. Vì sao không trả `200` kèm `{"success": false}`?** (1.2, 1.3)
- Ý phải có: monitoring, retry, cache dựa vào status; client phải parse body mới biết lỗi
- Điểm cộng: RFC 9457 và mã lỗi máy đọc được

**6. FormRequest và API Resource trong Laravel dùng để làm gì?** (2.6)
- Ý phải có: validate + authorize đầu vào; tách shape response khỏi model
- Điểm cộng: `validated()` chống mass assignment; `whenLoaded()` chống N+1; thiếu `Accept: application/json` thì bị redirect thay vì `422`

### 🟡 Mid

**7. Người dùng bấm "Thanh toán" hai lần. Làm sao không trừ tiền hai lần?** (2.1)
- Ý phải có: idempotency key do client sinh, unique constraint phía server, trả lại response đã lưu
- Điểm cộng: xử lý request trùng đang `processing`; gọi cổng thanh toán cũng cần idempotency; đối soát khi timeout
- Red flag: chỉ "disable nút"

**8. Thiết kế idempotency key: lưu gì, lưu bao lâu, hai request trùng cùng lúc thì sao?** (2.1)
- Ý phải có: `(client, key)`, hash body, trạng thái, response; TTL; unique constraint chứ không `SELECT` rồi `INSERT`
- Điểm cộng: hạn cho `processing`; cùng transaction với nghiệp vụ; biết hai trường phái lưu/không lưu `5xx` (Stripe/Brandur); header chưa thành RFC

**9. Offset và cursor pagination khác nhau thế nào? Cursor chứa gì?** (1.4)
- Ý phải có: vì sao OFFSET chậm và lặp/sót; cursor = giá trị sort + tie-breaker, opaque
- Điểm cộng: cần index khớp thứ tự sort; offset vẫn hợp cho admin; `cursorPaginate()` của Laravel

**10. Hai nhân viên cùng sửa một sản phẩm, một người mất thay đổi.** (2.2)
- Ý phải có: lost update; version column, `ETag`/`If-Match`, `412`
- Điểm cộng: `428` khi bắt buộc precondition; UI cho so sánh và merge

**11. CORS là gì? Nó có bảo vệ API của bạn không? Frontend báo lỗi CORS khi `PUT` nhưng `GET` chạy.** (2.3)
- Ý phải có: chính sách của trình duyệt, không bảo vệ server; `PUT` có preflight
- Điểm cộng: middleware auth trả `401` cho `OPTIONS`; `Vary: Origin`; phản chiếu `Origin` kèm credentials là lỗ hổng

**12. Thiết kế webhook cho hệ thống của bạn gửi sang khách hàng.** (2.4)
- Ý phải có: outbox, `event_id`, ký HMAC có timestamp, retry backoff, bên nhận idempotent
- Điểm cộng: không đảm bảo thứ tự, replay thủ công, chặn SSRF, rotate secret; Standard Webhooks
- Red flag: gửi webhook đồng bộ trong request tạo đơn

**13. Đối tác nói không nhận được webhook, log bên bạn ghi họ trả `200`.** (2.4)
- Ý phải có: họ trả `200` trước khi xử lý rồi worker lỗi; kiểm tra `event_id` phía họ
- Điểm cộng: API để kéo lại event theo khoảng thời gian; job đối soát hai phía

**14. Vì sao không trả ID int64 dạng số trong JSON cho frontend?** (2.7)
- Ý phải có: `2^53 - 1`; làm tròn âm thầm; trả string
- Điểm cộng: Protobuf JSON mapping làm vậy; sửa ở API Resource

**15. Sanctum hay Passport? Rate limit trong Laravel hoạt động thế nào khi có 4 server?** (2.6)
- Ý phải có: Sanctum cho token của app mình và SPA; Passport khi cần OAuth2 server cho bên thứ ba; `RateLimiter::for` + `throttle`
- Điểm cộng: bộ đếm trong cache nên phải dùng Redis chung; key theo user hoặc IP; header `Retry-After`

**16. Client báo tạo trùng đơn khi mạng chập chờn.** (2.1, 2.5)
- Ý phải có: log cho thấy cùng body cách vài giây là retry; thêm idempotency key + unique constraint
- Điểm cộng: kiểm tra retry của load balancer/SDK/Guzzle với POST

### 🔴 Senior

**17. Thay đổi nào trong API là breaking? Làm sao phát hiện tự động trong CI?** (3.1, 3.4)
- Ý phải có: bảng breaking; thêm enum là có thể breaking; đổi ý nghĩa field là tệ nhất
- Điểm cộng: `oasdiff`, `buf breaking`, contract test
- Red flag: "chỉ xoá field mới breaking"

**18. Bạn cần đổi kiểu một field đang được mobile app dùng. Làm thế nào?** (3.1)
- Ý phải có: expand–contract, trả cả hai, đo theo app version, `Deprecation`/`Sunset`
- Điểm cộng: cú pháp RFC 9745 (`@timestamp`) và RFC 8594; chỉ tăng major khi không còn cách
- Red flag: "lên `/v2`" ngay

**19. Sau khi thêm giá trị `refunded` vào enum `status`, app Android bản cũ crash.** (3.1)
- Ý phải có: thêm enum là breaking với client không có nhánh default
- Điểm cộng: ngắn hạn map giá trị mới về cũ theo app version; dài hạn tolerant reader, tài liệu hoá enum mở, contract test

**20. Endpoint danh sách đơn trang 5000 mất 8 giây.** (1.4)
- Ý phải có: `OFFSET` lớn và `COUNT(*)` mỗi request; chuyển cursor, bỏ hoặc ước lượng tổng
- Điểm cộng: giới hạn trang tối đa cho offset; export thì dùng LRO

**21. Thiết kế API cho thao tác mất 10 phút (export báo cáo).** (2.2)
- Ý phải có: `202` + operation resource, poll hoặc webhook, status lưu bền
- Điểm cộng: idempotency cho request tạo; hết hạn file; huỷ operation; quota theo tenant

**22. Bạn tích hợp một API bên thứ ba hay chết. Thiết kế lớp gọi thế nào?** (2.5)
- Ý phải có: timeout, retry có điều kiện + jitter, circuit breaker, bulkhead, fallback, adapter
- Điểm cộng: timeout không có nghĩa là thất bại; đối soát; metric theo provider; Laravel mặc định 30 giây là quá dài

**23. Khi nào chọn REST, GraphQL, gRPC cho hệ có web, mobile và 20 microservice?** (3.2, 3.3)
- Ý phải có: hỏi ai là client; REST cho public, gRPC nội bộ, GraphQL/BFF cho UI ghép dữ liệu
- Điểm cộng: chi phí vận hành mỗi loại; L7 LB và deadline của gRPC; caching và cost limit của GraphQL
- Red flag: "gRPC nhanh hơn nên dùng cho tất cả"

**24. Đổi field trong `.proto` thế nào để không phá client cũ?** (3.3)
- Ý phải có: không đổi/dùng lại số field, `reserved`, thêm field mới thay đổi kiểu
- Điểm cộng: đổi tên phá JSON mapping; `optional` trong proto3; `buf breaking`

**25. Service A gọi gRPC sang B, thêm pod B nhưng tải vẫn dồn vào một pod.** (3.3)
- Ý phải có: HTTP/2 kết nối dài, L4 LB chỉ cân bằng lúc mở kết nối
- Điểm cộng: client-side LB qua headless service, service mesh, giới hạn tuổi kết nối (`MaxConnectionAge`)

**26. GraphQL gặp N+1 thế nào? Bảo vệ GraphQL public ra sao?** (3.2)
- Ý phải có: resolver theo từng phần tử; DataLoader theo request; depth/complexity limit, persisted queries
- Điểm cộng: lỗi trả `200` nên monitoring phải đọc `errors`; authorization theo field

**27. Làm sao support tra được lỗi một request từ khách hàng báo?** (1.3, 3.4)
- Ý phải có: trace id trong response lỗi và log; W3C `traceparent` xuyên gateway và service
- Điểm cộng: log có cấu trúc gắn trace id; không lộ chi tiết nội bộ trong body

---

## Bài tập tự làm

1. Thiết kế đầy đủ API cho resource `orders` của một shop: endpoint, method, status code cho từng trường hợp lỗi,
   format lỗi theo RFC 9457, pagination cursor (mô tả nội dung cursor). Viết thành spec OpenAPI 3.1 và lint bằng Spectral.
2. Viết bảng thiết kế cho idempotency key của `POST /payments`: schema bảng lưu key, luồng xử lý khi request trùng
   đến lúc request đầu chưa xong, khi server crash giữa chừng, TTL. Sau đó hiện thực thành middleware Laravel.
3. Viết đặc tả webhook `order.paid` cho đối tác: payload, header chữ ký, thuật toán verify (pseudo-code),
   chính sách retry, cam kết về thứ tự.
4. Cho `.proto` có message `User { string name = 1; int32 age = 2; string phone = 3; }`. Mô tả các bước để: xoá
   `phone`, đổi `age` thành `birth_date`, thêm `email`, mà không phá client cũ.
5. So sánh bằng bảng cho một bài toán cụ thể do bạn chọn: dùng REST hay GraphQL, lý do, và cái giá phải trả.
6. Lên kế hoạch ngừng endpoint `GET /v1/reports` sau 6 tháng: header `Deprecation`, `Sunset`, `Link` đúng cú pháp,
   cách đo client còn dùng, thông báo, và phản hồi sau hạn.

> Nộp bài vào đây để được review.
