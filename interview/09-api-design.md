# 09. Thiết kế API

> [← Mục lục](README.md) · Phạm vi: REST (method, status code, lỗi, pagination, versioning, idempotency, concurrency), webhook, gọi API bên thứ ba, GraphQL, gRPC, serialization, API gateway/BFF, OpenAPI.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**REST cơ bản**
- [ ] 🟢 Resource là danh từ, số nhiều, lồng nhau tối đa 1–2 cấp
- [ ] 🟢 Method: safe, idempotent, cacheable; PUT và PATCH khác nhau
- [ ] 🟢 Status code đúng và các cặp hay nhầm (400/422, 401/403, 404/403, 301/308, 502/504)
- [ ] 🟡 Format lỗi thống nhất, RFC 9457 (thay RFC 7807)
- [ ] 🟢 Filtering, sorting, field selection
- [ ] 🟡 Pagination offset và cursor, cách encode cursor
- [ ] 🟡 Bulk operation và partial failure
- [ ] 🟡 Long-running operation: `202` + status resource
- [ ] 🟡 Content negotiation (`Accept`, `Content-Type`)
- [ ] 🟡 HATEOAS (biết là gì là đủ)

**Tiến hoá API**
- [ ] 🟡 Versioning: URL, header, media type
- [ ] 🟡 Deprecation, header `Sunset`
- [ ] ⚠️ Backward compatibility: thay đổi nào là breaking
- [ ] 🔴 Tolerant reader, expand–contract cho API

**Tính đúng khi retry và ghi đồng thời**
- [ ] 🟡 Idempotency key: lưu gì, TTL, request trùng đang xử lý dở
- [ ] 🟡 Optimistic concurrency qua `ETag` / `If-Match` / `412`
- [ ] 🟡 Rate limit headers, `429`, `Retry-After`

**Bảo mật và trình duyệt**
- [ ] 🟢 Auth cho API (chi tiết ở [10-security.md](10-security.md))
- [ ] 🟡 CORS: preflight, credentials, `Vary: Origin`

**Tích hợp**
- [ ] 🟡 Webhook bên gửi: retry, backoff, ký HMAC, timestamp chống replay, thứ tự
- [ ] 🟡 Webhook bên nhận: verify, idempotent, trả 2xx nhanh rồi xử lý async
- [ ] 🟡 Gọi API bên thứ ba: timeout, retry, circuit breaker, idempotency, sandbox, log

**Kiểu API khác**
- [ ] 🟡 GraphQL: schema, resolver, N+1 + DataLoader, depth/complexity limit, caching, persisted queries
- [ ] 🟡 gRPC: protobuf, HTTP/2, 4 kiểu streaming, deadline, compat của proto, grpc-gateway
- [ ] 🟡 So sánh REST / GraphQL / gRPC
- [ ] 🔴 WebSocket / SSE / long polling khi cần push (chi tiết ở [02-networking.md](02-networking.md))

**Serialization**
- [ ] ⚠️ JSON: int64 trong JavaScript, date ISO 8601, null vs thiếu field
- [ ] 🟡 Protobuf, Avro (schema registry), MessagePack

**Hạ tầng và tài liệu**
- [ ] 🟡 API gateway, BFF
- [ ] 🟡 OpenAPI, contract-first và code-first
- [ ] 🔴 Documentation, SDK, changelog, contract test

## Chi tiết

### REST cơ bản

- [ ] Resource naming
  - Danh từ số nhiều: `GET /users/123/orders`, không phải `/getUserOrders`
  - Lồng tối đa 1–2 cấp. `/orders/{id}` tốt hơn `/users/{u}/orders/{id}` nếu order id đã là duy nhất toàn cục
  - Hành động không khớp CRUD: dùng sub-resource (`POST /orders/{id}/cancellation`) hoặc động từ rõ ràng (`POST /orders/{id}:cancel`, kiểu Google API)
  - Chọn một quy ước chữ (`snake_case` hoặc `camelCase`) cho field JSON và giữ nhất quán toàn bộ API
- [ ] Method semantics (RFC 9110)

  | Method | Safe | Idempotent | Cacheable | Dùng cho |
  |---|---|---|---|---|
  | GET | có | có | có | đọc |
  | HEAD | có | có | có | như GET, không có body |
  | OPTIONS | có | có | không | hỏi khả năng, CORS preflight |
  | POST | không | không | hiếm | tạo mới, hành động |
  | PUT | không | có | không | thay thế toàn bộ, hoặc tạo tại URI client chọn |
  | PATCH | không | không bắt buộc | không | sửa một phần |
  | DELETE | không | có | không | xoá |

  - Safe = không đổi state phía server (về mặt ngữ nghĩa). Idempotent = gọi N lần có **tác động lên server** như gọi 1 lần; response có thể khác (DELETE lần 2 trả `404` vẫn là idempotent)
  - PUT gửi toàn bộ resource nên gửi lại cho cùng kết quả. PATCH idempotent hay không tuỳ nội dung: "đặt `name = X`" thì có, "tăng `count` thêm 1" thì không
  - PATCH có hai format chuẩn: JSON Merge Patch (RFC 7396, gửi object con, `null` = xoá field) và JSON Patch (RFC 6902, danh sách phép `add`/`remove`/`replace`/`test`)
  - ⚠️ GET không được có side effect: crawler, prefetch của trình duyệt, retry của proxy đều gọi GET tuỳ ý
- [ ] Status code

  | Nhóm | Code | Khi nào |
  |---|---|---|
  | 2xx | `200` | thành công, có body |
  | | `201` | đã tạo; kèm header `Location` trỏ tới resource mới |
  | | `202` | đã nhận, xử lý sau |
  | | `204` | thành công, không có body |
  | 3xx | `301` / `308` | chuyển vĩnh viễn; `308` giữ nguyên method và body |
  | | `302` / `307` | chuyển tạm; `307` giữ nguyên method |
  | | `304` | không đổi (conditional GET với `If-None-Match` / `If-Modified-Since`) |
  | 4xx | `400` | request sai định dạng (JSON hỏng, thiếu field bắt buộc, sai kiểu) |
  | | `401` | chưa xác thực / token sai; phải kèm `WWW-Authenticate` |
  | | `403` | đã xác thực nhưng không có quyền |
  | | `404` | không tồn tại (hoặc cố tình giấu) |
  | | `405` | method không hỗ trợ; kèm `Allow` |
  | | `406` / `415` | không có representation hợp `Accept` / không hỗ trợ `Content-Type` gửi lên |
  | | `409` | xung đột với state hiện tại (trùng unique, sai trạng thái) |
  | | `410` | đã từng có, nay bị gỡ vĩnh viễn |
  | | `412` / `428` | precondition (`If-Match`) sai / server bắt buộc có precondition |
  | | `413` | body quá lớn |
  | | `422` | đúng định dạng nhưng không hợp lệ về nghiệp vụ |
  | | `429` | vượt rate limit; kèm `Retry-After` |
  | 5xx | `500` | lỗi không lường trước trong app |
  | | `502` | proxy/gateway nhận response lỗi hoặc không hợp lệ từ upstream (upstream chết, reset kết nối) |
  | | `503` | tạm thời không phục vụ (quá tải, bảo trì); có thể kèm `Retry-After` |
  | | `504` | proxy/gateway chờ upstream quá timeout |

  - ⚠️ Các cặp hay nhầm: `400` vs `422`; `401` vs `403`; `403` vs `404` (trả `404` để không lộ resource tồn tại); `301/302` vs `307/308` (client cũ có thể đổi POST thành GET với 301/302); `502` vs `504` (upstream trả rác/chết vs upstream quá chậm)
  - ⚠️ Không trả `200` kèm `{"success": false}`: monitoring, retry, cache đều dựa vào status code
  - Client retry được: `408`, `429`, `502`, `503`, `504` và lỗi mạng. Không retry mù `400`, `401`, `403`, `404`, `422`. Retry `500` chỉ khi request idempotent
- [ ] Format lỗi thống nhất
  - RFC 9457 (Problem Details, thay RFC 7807), `Content-Type: application/problem+json`
  - Field chuẩn: `type` (URI định danh loại lỗi), `title`, `status`, `detail`, `instance`; được thêm field mở rộng

  ```json
  {
    "type": "https://api.example.com/errors/validation",
    "title": "Dữ liệu không hợp lệ",
    "status": 422,
    "detail": "2 field không hợp lệ",
    "errors": [{"field": "email", "code": "invalid_format"}],
    "trace_id": "4bf92f3577b34da6"
  }
  ```

  - Client nên dựa vào **mã lỗi máy đọc được** (`type` / `code`), không dựa vào `message` vì message có thể được dịch hoặc sửa câu chữ
  - Kèm `trace_id` để support tra log. ⚠️ Không trả stack trace, câu SQL, tên bảng ra ngoài
- [ ] Filtering, sorting, field selection
  - Filter: `?status=paid&created_from=2026-01-01`; filter phức tạp: `?filter[status]=paid` hoặc ngôn ngữ riêng (cân nhắc kỹ, dễ thành lỗ hổng injection/DoS)
  - Sort: `?sort=-created_at,id` (`-` là giảm dần). ⚠️ Chỉ cho sort theo whitelist cột có index
  - Field selection: `?fields=id,name` giảm payload; mở rộng quan hệ: `?include=customer` hoặc `?expand=customer`
  - ⚠️ Mọi tham số từ query đều là input không tin được: whitelist tên cột, giới hạn `limit` tối đa
- [ ] Pagination

  | | Offset (`?page=3&limit=20`) | Cursor (`?after=<cursor>&limit=20`) |
  |---|---|---|
  | Nhảy tới trang N | được | không |
  | Hiệu năng trang sâu | chậm: DB vẫn đọc rồi bỏ `OFFSET` dòng | ổn định: `WHERE (created_at, id) < (?, ?)` dùng index |
  | Dữ liệu thay đổi khi đang lướt | lặp hoặc sót dòng | không lặp, không sót |
  | Tổng số trang | dễ (nhưng `COUNT(*)` bảng lớn cũng tốn) | thường không trả |
  | Hợp với | admin, bảng nhỏ | feed, infinite scroll, sync, export |

  - Cursor encode: chứa giá trị các cột sort của phần tử cuối + tie-breaker duy nhất (thường là `id`), serialize JSON rồi base64url. Ví dụ `{"c":"2026-09-01T10:00:00Z","id":98123}`
  - ⚠️ Sort theo cột không duy nhất mà không có tie-breaker thì cursor sót/lặp dòng
  - Cursor nên **opaque**: client không được tự dựng. Có thể ký HMAC hoặc mã hoá nếu không muốn lộ giá trị bên trong, và để server tự do đổi format sau này
  - Trả metadata: `next_cursor` (null khi hết), hoặc header `Link: <...>; rel="next"` (RFC 8288)
  - Chi tiết keyset pagination ở tầng SQL: [03-database-sql.md](03-database-sql.md)
- [ ] 🟡 Bulk operations
  - `POST /orders/bulk` hoặc `POST /orders:batchCreate` với mảng item; đặt giới hạn số item mỗi request
  - Hai lựa chọn: **atomic** (tất cả hoặc không) hoặc **partial success** (trả kết quả từng item). Partial thường trả `200` hoặc `207 Multi-Status` với mảng `{index, status, error}`
  - ⚠️ Bulk lớn không xử lý đồng bộ: chuyển sang long-running operation
- [ ] 🟡 Long-running operation
  - `POST /reports` → `202 Accepted` + `Location: /operations/abc`
  - `GET /operations/abc` → `{"status": "running", "progress": 40}` → `{"status": "succeeded", "result_url": "..."}` hoặc `failed` kèm lỗi
  - Client polling (có `Retry-After` gợi ý nhịp poll) hoặc nhận webhook khi xong
  - Status resource phải bền (lưu DB), không chỉ nằm trong memory của một pod
- [ ] 🟡 Content negotiation
  - Client gửi `Accept: application/json`, server trả `Content-Type` tương ứng; không hỗ trợ thì `406`
  - Body gửi lên sai `Content-Type` thì `415`
  - `Accept-Language` cho i18n, `Accept-Encoding: gzip, br` cho nén
  - Response thay đổi theo header nào thì phải khai `Vary` để cache không trả nhầm
- [ ] 🟡 HATEOAS
  - Response kèm link tới hành động tiếp theo: `"_links": {"cancel": {"href": "/orders/1/cancellation"}}`
  - Lý thuyết: client không hard-code URL, server điều khiển luồng. Thực tế ít API public làm đầy đủ; biết khái niệm và mức Richardson Maturity (0–3) là đủ

### Tiến hoá API

- [ ] 🟡 Versioning

  | Cách | Ví dụ | Ưu | Nhược |
  |---|---|---|---|
  | URL | `/v1/orders` | rõ, dễ route, dễ test bằng browser | "resource" bị nhân bản theo version |
  | Header | `API-Version: 2026-09-01` | URL sạch; version theo ngày như Stripe | khó thấy, cache phải `Vary` |
  | Media type | `Accept: application/vnd.acme.v2+json` | đúng tinh thần HTTP | phức tạp cho client |

  - Tăng major version chỉ khi có breaking change. Mục tiêu là **ít phải tăng version**, nhờ thiết kế thêm-mà-không-phá
- [ ] 🟡 Deprecation
  - Thông báo trước (changelog, email), đo xem client nào còn gọi endpoint cũ (log theo API key/client id), rồi mới gỡ
  - Header `Sunset: <HTTP-date>` (RFC 8594) báo thời điểm endpoint ngừng; header `Deprecation` báo endpoint đã deprecated (đã có RFC riêng, kiểm tra lại số hiệu và cú pháp theo tài liệu bạn dùng); kèm `Link: <...>; rel="deprecation"` trỏ tới tài liệu migrate
  - Sau hạn: `410 Gone` với thông báo rõ, thay vì `404` khó hiểu
- [ ] ⚠️ Backward compatibility

  | Thay đổi | Breaking? |
  |---|---|
  | Thêm endpoint, thêm field optional vào response | không (nếu client bỏ qua field lạ) |
  | Thêm field optional vào request | không |
  | Thêm field **bắt buộc** vào request | có |
  | Xoá / đổi tên field, đổi kiểu (`int` → `string`) | có |
  | Đổi ý nghĩa field giữ nguyên tên (đơn vị từ đồng sang nghìn đồng) | có, và tệ nhất vì không lỗi rõ ràng |
  | Thêm giá trị mới vào enum trong response | **có thể**: client `switch` không có `default` sẽ vỡ |
  | Siết validation (max length nhỏ hơn) | có |
  | Đổi status code, đổi format lỗi | có |
  | Đổi thứ tự mặc định, đổi page size mặc định | có thể |

  - Mobile app là trường hợp khó nhất: bản cũ tồn tại nhiều năm, không ép update được. Cần giữ API cũ lâu hoặc có cơ chế force update
  - 🔴 Tolerant reader: client bỏ qua field lạ, không fail khi enum có giá trị lạ. Tài liệu hoá rõ "enum có thể được mở rộng"
  - 🔴 Đổi kiểu field theo kiểu expand–contract: thêm field mới (`amount_minor`), trả cả hai, đo đến khi không còn client đọc field cũ, rồi mới xoá

### Tính đúng khi retry và ghi đồng thời

- [ ] 🟡 Idempotency key
  - Vấn đề: client gửi `POST /payments`, timeout, không biết server đã xử lý chưa. Retry thì có thể trừ tiền hai lần
  - Client sinh key duy nhất (UUID) cho mỗi **ý định** thao tác, gửi header `Idempotency-Key` (có IETF draft chuẩn hoá header này; Stripe dùng cùng tên). Retry dùng lại **đúng key đó**
  - Server lưu theo `(client_id, key)`: trạng thái (`processing` / `completed`), hash của request body, status code và body response
  - Luồng xử lý:

    ```
    INSERT key với status=processing (unique constraint)
      ├─ insert thành công  → xử lý nghiệp vụ → lưu response, status=completed → trả
      └─ trùng key
           ├─ hash body khác           → 422 (dùng lại key cho request khác)
           ├─ status=processing        → 409 (đang xử lý, retry sau) — không xử lý lần hai
           └─ status=completed         → trả lại đúng response đã lưu
    ```

  - ⚠️ "Kiểm tra rồi mới insert" (`SELECT` rồi `INSERT`) có race condition: hai request cùng lúc đều thấy chưa có. Phải dựa vào unique constraint hoặc lock nguyên tử (`SET NX` trong Redis)
  - ⚠️ Request bị crash giữa chừng để lại `processing` mãi: cần timeout cho trạng thái này (lock có hạn), sau đó cho phép xử lý lại. Nghiệp vụ bên trong vẫn phải an toàn khi chạy lại (transaction, unique constraint ở tầng nghiệp vụ)
  - Lưu key và kết quả nghiệp vụ trong **cùng transaction DB** là cách chắc nhất. Lưu ở Redis nhanh hơn nhưng có khoảng hở nếu Redis mất dữ liệu
  - TTL: đủ dài để phủ mọi lần retry hợp lý của client (Stripe giữ khoảng 24 giờ); hết TTL thì dọn
  - Lưu response lỗi `4xx` do validation? Tuỳ chính sách; thường không lưu lỗi `5xx` để client retry được
  - Bên cạnh key, nên có ràng buộc nghiệp vụ tự nhiên (unique `order_id` trong bảng payment) như lớp phòng thủ thứ hai
- [ ] 🟡 Optimistic concurrency qua ETag
  - `GET /orders/1` → `ETag: "v7"`. Client sửa rồi `PUT /orders/1` kèm `If-Match: "v7"`
  - Server so version: khớp thì ghi và trả ETag mới; không khớp thì `412 Precondition Failed`. Server có thể bắt buộc `If-Match` và trả `428` nếu thiếu
  - Tầng DB: `UPDATE ... SET version = version + 1 WHERE id = ? AND version = ?`, kiểm tra số dòng bị ảnh hưởng
  - Chống **lost update**: hai admin cùng sửa, người lưu sau đè mất thay đổi của người trước
  - Strong ETag (`"abc"`) vs weak ETag (`W/"abc"`): `If-Match` dùng so sánh strong
- [ ] 🟡 Rate limit headers
  - De-facto: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. IETF đang chuẩn hoá `RateLimit` / `RateLimit-Policy` (bản draft)
  - Vượt thì `429` + `Retry-After` (giây hoặc HTTP-date)
  - Giới hạn theo API key/user/IP/endpoint; thuật toán (token bucket, sliding window) ở [16-system-design.md](16-system-design.md)
  - ⚠️ Client phải tôn trọng `Retry-After` và có jitter, nếu không tất cả cùng quay lại một giây

### Bảo mật và trình duyệt

- [ ] Auth cho API: API key cho server-to-server, OAuth2/JWT cho user, mTLS nội bộ. Chi tiết, cùng OWASP API Security Top 10 (BOLA, mass assignment...) ở [10-security.md](10-security.md)
  - Luôn HTTPS; token trong header `Authorization`, ⚠️ không đặt trong query string (lọt vào access log, history, `Referer`)
  - Giới hạn body size, số item, độ sâu JSON để chống DoS
- [ ] 🟡 CORS
  - Same-origin policy là của **trình duyệt**. CORS là cách server nói "trình duyệt được phép cho JS ở origin X đọc response"
  - ⚠️ CORS không bảo vệ server: `curl`, Postman, server khác không bị CORS chặn. Đừng coi nó là cơ chế auth
  - Simple request (GET/POST với content type đơn giản) gửi thẳng; request khác (PUT, DELETE, `Content-Type: application/json`, header tuỳ chỉnh) có **preflight** `OPTIONS` trước
  - Header phản hồi: `Access-Control-Allow-Origin`, `-Methods`, `-Headers`, `-Credentials`, `-Max-Age` (cache preflight), `Access-Control-Expose-Headers` (cho JS đọc header như `X-RateLimit-Remaining`)
  - ⚠️ Không được dùng `Allow-Origin: *` cùng `Allow-Credentials: true`. Và ⚠️ phản chiếu nguyên `Origin` của request vào `Allow-Origin` kèm credentials là lỗ hổng: phải so với whitelist
  - Trả `Allow-Origin` động theo whitelist thì thêm `Vary: Origin` để CDN không cache nhầm
  - Lỗi CORS nhìn trong console trình duyệt, không phải log server; preflight bị `401` vì middleware auth chặn `OPTIONS` là lỗi hay gặp

### Webhook

- [ ] 🟡 Bên gửi
  - Ghi event vào DB (outbox) rồi worker gửi, không gửi trong request/transaction nghiệp vụ. Xem [12-messaging.md](12-messaging.md)
  - Payload có `event_id` duy nhất, `type`, `created_at`, và dữ liệu (hoặc chỉ id để bên nhận gọi API lấy bản mới nhất: "thin event")
  - Retry khi không nhận `2xx` hoặc timeout: exponential backoff + jitter, trải ra nhiều giờ/ngày; sau N lần thì đánh dấu thất bại, cho xem lại và replay thủ công, có thể tự tắt endpoint lỗi liên tục
  - Timeout ngắn (vài giây) cho mỗi lần gửi, để một bên nhận chậm không làm nghẽn worker
  - Ký: `signature = HMAC-SHA256(secret, timestamp + "." + raw_body)`, gửi trong header cùng timestamp. Mỗi endpoint một secret, cho phép hai secret cùng hiệu lực khi rotate
  - Timestamp chống replay: bên nhận từ chối nếu lệch quá vài phút
  - ⚠️ Thứ tự không được đảm bảo (retry làm event cũ đến sau event mới). Kèm `created_at` hoặc version của resource để bên nhận bỏ qua event cũ hơn state đang có
  - 🔴 SSRF: URL webhook do khách nhập, chặn IP nội bộ/metadata khi gửi (xem [10-security.md](10-security.md))
  - Tham khảo đặc tả "Standard Webhooks" cho tên header và cách ký thống nhất
- [ ] 🟡 Bên nhận
  - Verify chữ ký trên **raw body** (byte nguyên bản). ⚠️ Parse JSON rồi serialize lại để verify thì hỏng, vì thứ tự key/khoảng trắng thay đổi
  - So sánh chữ ký bằng constant-time compare (`hash_equals` trong PHP, `hmac.Equal` trong Go, `MessageDigest.isEqual` trong Java)
  - Idempotent theo `event_id`: bảng `processed_events` với unique constraint. Webhook luôn có thể đến trùng (at-least-once)
  - Trả `2xx` nhanh: verify, lưu event vào DB/queue, trả `200`; xử lý nặng ở worker. Xử lý đồng bộ lâu thì bên gửi timeout, retry, gây trùng
  - Không tin nội dung hoàn toàn: với việc quan trọng (thanh toán) gọi lại API bên gửi để xác nhận trạng thái
  - Cần job đối soát định kỳ vì webhook có thể mất hẳn

### Gọi API bên thứ ba

- [ ] 🟡 Những thứ phải có
  - **Timeout** cả connect và read, luôn đặt. ⚠️ Mặc định của nhiều HTTP client là không timeout (Go `http.Client{}` zero value, PHP cURL không đặt `CURLOPT_TIMEOUT`); kiểm tra lại client bạn dùng
  - **Retry** chỉ cho lỗi tạm thời và thao tác idempotent; exponential backoff + jitter; giới hạn số lần và tổng thời gian
  - **Idempotency key** khi API bên kia hỗ trợ, để retry POST an toàn
  - **Circuit breaker**: lỗi vượt ngưỡng thì mở mạch, fail fast một thời gian, rồi half-open thử lại. Tránh treo thread/worker chờ một dịch vụ đã chết
  - **Bulkhead**: giới hạn số kết nối đồng thời tới từng bên thứ ba để một bên chậm không ăn hết pool
  - **Fallback**: dữ liệu cache, giá trị mặc định, hoặc đưa vào queue làm sau
  - **Log** request/response (đã che secret, PII), thời gian, status; metric latency và error rate theo từng provider
  - **Sandbox** để phát triển; ⚠️ sandbox thường khác production ở hành vi và rate limit, cần test lại với production ở mức nhỏ
  - Bọc provider sau một interface/adapter (xem [08-oop-design.md](08-oop-design.md)), để đổi provider hoặc giả lập trong test
  - ⚠️ Timeout không có nghĩa là thất bại: bên kia có thể đã xử lý. Với thanh toán, xem [22-practical-data.md](22-practical-data.md)
- **Đối chiếu**: PHP dùng Guzzle (middleware retry), Java có Resilience4j (circuit breaker, retry, bulkhead), Go tự viết quanh `http.Client` với `context.WithTimeout` hoặc dùng thư viện như `sony/gobreaker`.

### GraphQL

- [ ] 🟡 Khái niệm
  - Một endpoint (`POST /graphql`), client khai báo chính xác field cần; schema có kiểu mạnh (SDL), introspection
  - Query (đọc), Mutation (ghi), Subscription (push, thường qua WebSocket)
  - Resolver: mỗi field có hàm lấy dữ liệu; server ghép kết quả theo cây query
  - ⚠️ Lỗi thường trả HTTP `200` với mảng `errors` (có thể kèm `data` một phần). Monitoring theo status code sẽ không thấy lỗi
- [ ] 🟡 N+1 và DataLoader
  - Query `orders { customer { name } }`: resolver `customer` chạy một lần cho mỗi order, thành N query
  - DataLoader gom các key được yêu cầu trong cùng một tick/lượt thực thi thành một batch (`WHERE id IN (...)`) và cache theo request
  - ⚠️ DataLoader cache phải theo từng request, không dùng chung giữa user (lộ dữ liệu, dữ liệu cũ)
- [ ] 🟡 Bảo vệ server
  - Query lồng sâu (`friends { friends { friends ... } }`) có thể làm sập DB: giới hạn **depth**, tính **complexity/cost** mỗi field, giới hạn số item mỗi list
  - Timeout, rate limit theo cost chứ không theo số request
  - Tắt introspection ở production nếu API không public (không phải biện pháp bảo mật chính)
  - Authorization ở tầng resolver/business, từng field; dễ quên vì một object đi được qua nhiều đường
- [ ] 🟡 Caching khó
  - Cùng URL, method POST, body khác nhau: HTTP cache/CDN không cache được theo mặc định
  - Cách xử lý: client-side normalized cache (Apollo, Relay theo `id` + `__typename`), cache ở tầng resolver/DataLoader, persisted queries qua GET
- [ ] 🟡 Persisted queries
  - Client gửi hash của query thay vì cả query. Server chỉ chạy query nằm trong danh sách đã đăng ký
  - Lợi ích: payload nhỏ, dùng GET được nên CDN cache được, và chặn query tuỳ ý từ bên ngoài
- [ ] 🔴 Federation/schema stitching: ghép schema nhiều service thành một graph; biết tồn tại là đủ

### gRPC

- [ ] 🟡 Khái niệm
  - Định nghĩa service và message bằng `.proto`, sinh code client/server cho nhiều ngôn ngữ
  - Chạy trên HTTP/2: multiplexing nhiều call trên một kết nối, header nén, streaming
  - Binary Protobuf: nhỏ và parse nhanh hơn JSON, nhưng không đọc được bằng mắt
- [ ] 🟡 4 kiểu RPC

  | Kiểu | Ví dụ |
  |---|---|
  | Unary | `GetUser(req) → resp` |
  | Server streaming | server đẩy nhiều message: tail log, kết quả tìm kiếm |
  | Client streaming | client đẩy nhiều message, nhận một response: upload từng chunk |
  | Bidirectional streaming | hai chiều độc lập: chat, đồng bộ realtime |

- [ ] 🟡 Deadline
  - Client đặt deadline cho mỗi call; deadline **lan truyền** qua các service phía sau (Go: qua `context`)
  - Hết hạn thì status `DEADLINE_EXCEEDED`. Server nên kiểm tra context để dừng việc vô ích
  - Status code riêng (`OK`, `INVALID_ARGUMENT`, `NOT_FOUND`, `UNAVAILABLE`, `DEADLINE_EXCEEDED`...), không dùng HTTP status. `UNAVAILABLE` thường là lỗi retry được
- [ ] ⚠️ Backward compat của proto
  - Trên dây chỉ có **số field**, không có tên. Không bao giờ đổi số của field đang dùng, không dùng lại số của field đã xoá
  - Xoá field: đánh dấu `reserved 5; reserved "old_name";`
  - Đổi tên field: an toàn với binary, nhưng phá JSON mapping và code sinh ra
  - Đổi kiểu: phần lớn là breaking; chỉ một số cặp tương thích (kiểm tra bảng tương thích trong tài liệu Protobuf)
  - proto3: field vắng mặt đọc ra giá trị mặc định (0, `""`), không phân biệt được "không gửi" và "gửi 0" trừ khi dùng `optional` hoặc wrapper type
  - Enum nên có giá trị `0` là `UNSPECIFIED`
  - Công cụ như `buf breaking` kiểm tra breaking change trong CI
- [ ] 🟡 Hệ sinh thái
  - Trình duyệt không gọi gRPC trực tiếp được (không điều khiển HTTP/2 frame và trailer): dùng gRPC-Web hoặc gateway
  - grpc-gateway: sinh reverse proxy REST/JSON từ annotation trong `.proto`, một service phục vụ cả gRPC và REST
  - ⚠️ Load balancing: kết nối HTTP/2 sống lâu, L4 load balancer chỉ cân bằng theo kết nối nên dồn hết vào một pod. Cần L7 LB hoặc client-side load balancing
- [ ] 🟡 So sánh

  | | REST | GraphQL | gRPC |
  |---|---|---|---|
  | Transport | HTTP/1.1 hoặc 2 | HTTP, một endpoint | HTTP/2 |
  | Format | JSON thường gặp | JSON | Protobuf |
  | Contract | OpenAPI (tuỳ chọn) | schema bắt buộc | `.proto` bắt buộc |
  | HTTP cache/CDN | dễ | khó | không |
  | Browser | tự nhiên | tự nhiên | cần gRPC-Web/gateway |
  | Streaming | SSE/WebSocket bên ngoài | subscription | có sẵn |
  | Hợp với | API public, CRUD | nhiều loại client, UI cần ghép dữ liệu linh hoạt | nội bộ service-to-service, latency thấp |

### Serialization

- [ ] ⚠️ JSON
  - Số trong JavaScript là IEEE 754 double: số nguyên chính xác tới `2^53 - 1` (9007199254740991). ID int64 (Snowflake) lớn hơn sẽ bị làm tròn âm thầm khi `JSON.parse`. Cách xử lý: trả ID dạng **string**. Protobuf JSON mapping cũng encode int64 thành string
  - Tiền: không dùng số thực; trả integer minor unit hoặc string decimal (xem [22-practical-data.md](22-practical-data.md))
  - Ngày giờ: ISO 8601 / RFC 3339 có offset, `2026-09-23T08:00:00Z`; ngày thuần: `2026-09-23`. Tránh epoch không nói rõ giây hay mili giây
  - `null` vs thiếu field: với PATCH, "không gửi" = giữ nguyên, `null` = xoá. Phải định nghĩa rõ
  - PHP: `json_encode` mảng rỗng ra `[]` chứ không phải `{}`; dùng `JSON_THROW_ON_ERROR` để không bị `false` âm thầm
- [ ] 🟡 Format khác

  | Format | Schema | Đặc điểm | Hay dùng |
  |---|---|---|---|
  | JSON | không (có JSON Schema tuỳ chọn) | đọc được, lớn, chậm hơn | API public |
  | Protobuf | `.proto`, tag số | nhỏ, nhanh, cần schema để đọc | gRPC, event nội bộ |
  | Avro | schema JSON, không có tag trong dữ liệu | cần writer schema để đọc, schema evolution qua default value; thường đi với Schema Registry | Kafka, data pipeline |
  | MessagePack | không | "JSON nhị phân", nhỏ hơn JSON, không cần schema | cache, giao tiếp nội bộ |

  - Schema evolution: thêm field phải có default để reader mới đọc dữ liệu cũ và reader cũ bỏ qua field mới
  - ⚠️ Không dùng serialization gắn với ngôn ngữ (PHP `serialize`, Java native serialization) cho dữ liệu từ bên ngoài: lỗ hổng deserialization (xem [10-security.md](10-security.md))

### Hạ tầng và tài liệu

- [ ] 🟡 API gateway
  - Điểm vào chung: routing, auth (verify JWT), rate limit, TLS termination, log/metric, request transform, canary
  - ⚠️ Không đặt logic nghiệp vụ trong gateway; gateway là single point of failure nên phải HA
  - Ví dụ: Kong, AWS API Gateway, Envoy, Nginx
- [ ] 🟡 BFF (Backend for Frontend)
  - Mỗi loại client (web, mobile) một backend mỏng, ghép dữ liệu từ nhiều service thành đúng shape màn hình cần
  - Đổi lại: thêm một tầng để vận hành, logic dễ bị nhân bản giữa các BFF
- [ ] 🟡 OpenAPI
  - Contract-first: viết spec trước, review, sinh server stub/client/mock; frontend và backend làm song song
  - Code-first: sinh spec từ annotation/code; nhanh lúc đầu, nhưng spec dễ phản ánh "code đang làm gì" thay vì "API nên thế nào"
  - Dùng spec để validate request/response trong test, lint (Spectral), phát hiện breaking change (`oasdiff`) trong CI
- [ ] 🔴 Documentation và SDK
  - Tài liệu tốt có: ví dụ request/response thật, mã lỗi và cách xử lý, rate limit, idempotency, changelog, hướng dẫn migrate
  - SDK sinh tự động từ spec giúp client đúng chuẩn (retry, idempotency key) nhưng thêm gánh bảo trì nhiều ngôn ngữ
  - Contract test (consumer-driven, Pact) giữa các service nội bộ: xem [20-testing-quality.md](20-testing-quality.md)

## Senior trả lời khác gì

| Câu hỏi | Junior / mid | Senior |
|---|---|---|
| "Người dùng bấm Thanh toán hai lần?" | Disable nút, kiểm tra đơn đã thanh toán chưa | Idempotency key từ client + unique constraint; xử lý request trùng đang `processing`; nói luôn tầng gọi cổng thanh toán cũng cần idempotency và đối soát khi timeout |
| "Offset hay cursor?" | Cursor nhanh hơn | Nói rõ vì sao OFFSET chậm, cursor cần tie-breaker và index khớp; chọn offset cho admin cần nhảy trang, cursor cho feed/export; cursor opaque để đổi được về sau |
| "Đổi kiểu field đang được mobile dùng?" | Tăng lên `/v2` | Expand–contract: thêm field mới, trả cả hai, đo client còn đọc field cũ theo app version, đặt `Sunset`, chỉ tăng major khi không còn cách |
| "Thiết kế webhook?" | Gửi POST khi có event, lỗi thì retry | Outbox, ký HMAC có timestamp, retry backoff nhiều ngày, không đảm bảo thứ tự, bên nhận idempotent, dashboard cho khách replay, chặn SSRF |
| "REST hay gRPC?" | gRPC nhanh hơn | Hỏi lại ai là client; gRPC cho nội bộ, chú ý L7 LB và deadline; REST cho public vì tooling, cache, browser; chi phí vận hành của cả hai |

## Tình huống

1. **Client báo tạo trùng đơn khi mạng chập chờn.**
   Gợi ý:
   - Xem log: cùng body, cách nhau vài giây, là retry của client hoặc proxy
   - Thêm idempotency key, unique constraint theo key ở DB
   - Kiểm tra cấu hình retry của load balancer/SDK với POST
2. **Endpoint danh sách đơn hàng trang 5000 mất 8 giây.**
   Gợi ý:
   - `OFFSET` lớn đọc rồi bỏ hàng trăm nghìn dòng; `COUNT(*)` mỗi request
   - Chuyển cursor/keyset, bỏ tổng số hoặc ước lượng, giới hạn trang tối đa cho offset
3. **Đối tác nói không nhận được webhook, bên bạn log gửi `200`.**
   Gợi ý:
   - Kiểm tra họ trả `200` trước khi xử lý rồi worker lỗi; xem `event_id` họ đã lưu chưa
   - Cho họ API để kéo lại event theo khoảng thời gian; job đối soát
4. **Sau khi thêm giá trị `refunded` vào enum `status`, app Android bản cũ crash.**
   Gợi ý:
   - Thêm enum là breaking với client không có nhánh default
   - Khắc phục ngắn: map giá trị mới về giá trị cũ cho client version thấp (dựa vào header app version)
   - Dài hạn: tài liệu hoá enum mở, yêu cầu tolerant reader, contract test
5. **Hai nhân viên cùng sửa một sản phẩm, một người mất thay đổi.**
   Gợi ý:
   - Lost update; thêm version column, `ETag` / `If-Match`, `412` khi lệch
   - UI hiển thị "dữ liệu đã bị người khác sửa", cho so sánh
6. **Service A gọi gRPC sang B, thêm pod B nhưng tải vẫn dồn vào một pod.**
   Gợi ý:
   - HTTP/2 kết nối dài, L4 LB chỉ phân phối khi mở kết nối
   - Client-side LB (DNS headless service + round robin), service mesh, hoặc giới hạn tuổi kết nối
7. **Frontend báo lỗi CORS khi gọi `PUT`, `GET` vẫn chạy.**
   Gợi ý:
   - `PUT` có preflight `OPTIONS`; kiểm tra server có xử lý `OPTIONS` và trả `Allow-Methods`
   - Middleware auth có đang trả `401` cho `OPTIONS` không

## ❓ Câu hỏi hay gặp

🟢
- PUT và PATCH khác nhau thế nào? Vì sao PUT là idempotent?
- `401` và `403` khác nhau thế nào? `400` và `422`?
- Tạo resource thành công thì trả status gì, kèm header gì?
- Vì sao GET không nên có side effect?

🟡
- Người dùng bấm nút "Thanh toán" hai lần. Làm sao để không trừ tiền hai lần?
- Thiết kế idempotency key: lưu gì, lưu bao lâu, hai request trùng cùng lúc thì sao?
- Offset và cursor pagination khác nhau thế nào? Cursor chứa gì?
- Bạn cần đổi kiểu một field trong API đang có mobile app dùng. Làm thế nào?
- Thiết kế webhook cho hệ thống của bạn gửi sang khách hàng.
- CORS là gì? Nó có bảo vệ API của bạn không?
- GraphQL gặp N+1 thế nào? DataLoader giải quyết ra sao?
- Vì sao không trả ID int64 dạng số trong JSON cho frontend?

🔴
- Khi nào chọn REST, GraphQL, gRPC cho một hệ thống có web, mobile và 20 microservice?
- Thay đổi nào trong API là breaking? Làm sao phát hiện tự động trong CI?
- Thiết kế API cho thao tác mất 10 phút (export báo cáo).
- Đổi field trong `.proto` thế nào để không phá client cũ?
- Bạn tích hợp một API bên thứ ba hay chết. Thiết kế lớp gọi thế nào?

## Bài tập tự làm

1. Thiết kế đầy đủ API cho resource `orders` của một shop: endpoint, method, status code cho từng trường hợp lỗi, format lỗi theo RFC 9457, pagination cursor (mô tả nội dung cursor).
2. Viết bảng thiết kế cho idempotency key của `POST /payments`: schema bảng lưu key, luồng xử lý khi request trùng đến lúc request đầu chưa xong, khi server crash giữa chừng, TTL.
3. Viết đặc tả webhook `order.paid` cho đối tác: payload, header chữ ký, thuật toán verify (pseudo-code), chính sách retry, cam kết về thứ tự.
4. Cho một `.proto` có message `User { string name = 1; int32 age = 2; string phone = 3; }`. Mô tả các bước để: xoá `phone`, đổi `age` thành `birth_date`, thêm `email`, mà không phá client cũ.
5. So sánh bằng bảng cho một bài toán cụ thể do bạn chọn: dùng REST hay GraphQL, lý do, và cái giá phải trả.

> Nộp bài vào đây để được review.
