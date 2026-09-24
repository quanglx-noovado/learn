# 22. Dữ liệu thực tế: những thứ "đời thường" hay gây bug production

> [← Mục lục](README.md) · Phạm vi: thời gian và timezone, tiền, chuỗi Unicode và tiếng Việt, số, ID, file và import/export, email/SMS/OTP, tích hợp cổng thanh toán, state machine, i18n, soft delete và vệ sinh dữ liệu, cô lập môi trường.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Thời gian**
- [ ] 🟢 Lưu UTC, hiển thị theo timezone người dùng; ISO 8601; epoch giây vs mili giây
- [ ] 🟡 MySQL `TIMESTAMP` vs `DATETIME`, Postgres `timestamptz` vs `timestamp`
- [ ] 🟡 DST, timezone là tên vùng (`Asia/Ho_Chi_Minh`) chứ không phải offset
- [ ] 🟡 Clock skew giữa server, monotonic clock
- [ ] 🟡 Cron và timezone
- [ ] ⚠️ "Ngày" theo timezone người dùng khi làm báo cáo

**Tiền**
- [ ] 🟢 `DECIMAL` hoặc integer minor units, không float
- [ ] 🟡 Làm tròn, banker's rounding; làm tròn ở đâu
- [ ] 🟡 Đa tiền tệ, số chữ số thập phân khác nhau, tỷ giá
- [ ] 🟡 Chia tiền không mất đồng lẻ
- [ ] 🔴 Ledger, bút toán kép

**Chuỗi**
- [ ] 🟢 UTF-8; MySQL `utf8` vs `utf8mb4`
- [ ] 🟡 Collation: so sánh không phân biệt hoa thường/dấu
- [ ] ⚠️ Unicode normalization NFC/NFD, tiếng Việt có hai cách biểu diễn dấu
- [ ] 🟡 Tìm kiếm tiếng Việt không dấu
- [ ] 🟡 Độ dài chuỗi: byte vs code point vs grapheme
- [ ] 🟢 Slug

**Số và ID**
- [ ] 🟡 Integer overflow, int64 trong JSON với JavaScript, floating point
- [ ] 🟡 Auto-increment lộ thông tin; UUID, UUIDv7, ULID, Snowflake; public id vs internal id

**File**
- [ ] 🟡 Upload lớn: multipart/chunked, presigned URL
- [ ] 🟡 Kiểm tra loại file thật, xử lý ảnh async
- [ ] 🟡 Import/export CSV/Excel lớn: streaming, chunk, queue, tiến độ, validate từng dòng, idempotent
- [ ] ⚠️ BOM khi mở CSV bằng Excel; CSV injection

**Email, SMS, OTP**
- [ ] 🟡 SPF, DKIM, DMARC; bounce, complaint
- [ ] 🟢 Gửi qua queue, không gửi trong transaction
- [ ] 🟡 OTP: hết hạn, rate limit, chống brute force, chi phí SMS

**Thanh toán**
- [ ] 🟡 Redirect + IPN/webhook, verify chữ ký
- [ ] 🟡 Idempotency, đối soát
- [ ] ⚠️ Timeout không rõ kết quả
- [ ] 🟡 State machine trạng thái đơn

**Nghiệp vụ và vệ sinh dữ liệu**
- [ ] 🟡 State machine, audit trail
- [ ] 🟢 i18n/l10n, định dạng số/ngày theo locale
- [ ] 🟡 Soft delete và cái giá; dữ liệu mồ côi
- [ ] ⚠️ Dữ liệu test lẫn dữ liệu thật; môi trường test dùng chung DB

## Chi tiết

### Thời gian

- [ ] Nguyên tắc chung
  - Lưu **thời điểm** (instant) ở UTC; chuyển sang timezone của người xem khi hiển thị
  - Truyền qua API bằng ISO 8601 / RFC 3339 **có offset**: `2026-09-23T01:30:00Z` hoặc `2026-09-23T08:30:00+07:00`. ⚠️ Chuỗi không offset (`2026-09-23 08:30:00`) là mơ hồ
  - Epoch: nói rõ giây hay mili giây (PHP `time()` là giây, Java `System.currentTimeMillis()` và JS `Date.now()` là mili giây). Nhầm đơn vị ra năm 1970 hoặc năm 50000
  - Không phải thứ gì cũng là instant: ngày sinh là **ngày thuần** (`DATE`), giờ mở cửa "8:00 hằng ngày" là giờ địa phương + timezone. Lưu ngày sinh thành timestamp UTC nửa đêm thì người ở múi âm thấy lệch một ngày
- [ ] 🟡 MySQL `TIMESTAMP` vs `DATETIME`

  | | `TIMESTAMP` | `DATETIME` |
  |---|---|---|
  | Lưu | chuyển từ `time_zone` của session sang UTC, đọc thì chuyển ngược | lưu nguyên giá trị, không biết timezone |
  | Phạm vi | 1970 → 2038-01-19 (UTC) | năm 1000 → 9999 |
  | ⚠️ | vấn đề năm 2038; đổi `time_zone` session là giá trị đọc ra đổi theo | app phải tự quy ước là UTC |

  - Thực hành phổ biến: `DATETIME` + app luôn ghi UTC, hoặc `TIMESTAMP` + cố định `time_zone = '+00:00'` cho kết nối
- [ ] 🟡 Postgres `timestamptz` vs `timestamp`
  - `timestamptz` lưu một instant (nội bộ là UTC), hiển thị theo setting `TimeZone` của session. ⚠️ Nó **không** lưu timezone gốc; cần timezone gốc thì lưu thêm cột `tz` (`Asia/Ho_Chi_Minh`)
  - `timestamp` (without time zone) giống `DATETIME`. Mặc định dùng `timestamptz`
- [ ] 🟡 Timezone và DST
  - Timezone là **tên vùng IANA** (`Asia/Ho_Chi_Minh`, `America/New_York`), không phải offset: offset của một vùng đổi theo DST và theo lịch sử luật
  - Việt Nam UTC+7, không có DST, nên dev Việt hay không gặp lỗi DST cho tới khi có khách nước ngoài
  - DST: có giờ không tồn tại (đồng hồ nhảy từ 2:00 sang 3:00) và giờ xảy ra hai lần (lùi từ 2:00 về 1:00). "Cộng 1 ngày" khác "cộng 24 giờ" vào ngày đổi giờ
  - Cập nhật tzdata (OS, JVM, thư viện) khi có nước đổi luật giờ
  - **Đối chiếu**: Java `Instant` / `ZonedDateTime` / `LocalDate` (java.time, tránh `java.util.Date`); Go `time.Time` + `time.LoadLocation` (⚠️ layout format kiểu `2006-01-02T15:04:05Z07:00`); PHP `DateTimeImmutable` + `DateTimeZone` (tránh `DateTime` mutable), Carbon
- [ ] 🟡 Clock skew
  - Đồng hồ các server lệch nhau vài ms tới vài giây (NTP giảm chứ không xoá lệch). ⚠️ Không dùng timestamp của nhiều máy để xác định thứ tự sự kiện chính xác
  - JWT `exp`/`nbf`, chữ ký webhook có timestamp, OTP: cho phép lệch nhỏ
  - Đo khoảng thời gian (timeout, latency) bằng monotonic clock, không dùng wall clock vì wall clock có thể nhảy lùi (Go `time.Since` đã dùng monotonic; Java `System.nanoTime()`; PHP `hrtime()`)
  - Thứ tự trong hệ phân tán: xem [14-distributed-systems.md](14-distributed-systems.md)
- [ ] 🟡 Cron và timezone
  - Cron chạy theo timezone của máy/container (thường UTC). "Gửi báo cáo lúc 8h sáng giờ Việt Nam" = `0 1 * * *` UTC. Ghi rõ timezone trong cấu hình scheduler (Laravel `->timezone()`, Spring `@Scheduled(zone = ...)`, Kubernetes CronJob có `timeZone`)
  - Ở vùng có DST: job 2:30 sáng có thể không chạy hoặc chạy hai lần; lên lịch ngoài khung đổi giờ hoặc chạy theo UTC
  - Job theo timezone từng user ("8h sáng giờ của user"): chạy mỗi giờ/15 phút, chọn user có giờ địa phương khớp
  - Job phải idempotent vì có thể chạy trùng (xem [12-messaging.md](12-messaging.md))
- [ ] ⚠️ "Ngày" trong báo cáo
  - "Doanh thu ngày 23/09" là ngày theo timezone **của doanh nghiệp/người xem**: từ `2026-09-22T17:00:00Z` đến `2026-09-23T17:00:00Z` với UTC+7
  - ⚠️ `GROUP BY DATE(created_at)` trên cột UTC gán đơn lúc 6h sáng giờ Việt Nam vào ngày hôm trước
  - Cách làm: tính khoảng UTC ở app rồi `WHERE created_at >= ? AND created_at < ?` (dùng được index); hoặc `CONVERT_TZ` (MySQL, cần nạp bảng timezone) / `AT TIME ZONE` (Postgres) khi group; với báo cáo lớn, lưu thêm cột `local_date` lúc ghi
  - Dùng khoảng nửa mở `[start, end)`, không dùng `BETWEEN '... 00:00:00' AND '... 23:59:59'` (sót phần lẻ giây)

### Tiền

- [ ] 🟢 Kiểu dữ liệu
  - `DECIMAL(19,4)` (hoặc độ chính xác theo nghiệp vụ) hoặc integer theo **minor unit** (xu, cent). ⚠️ Không `FLOAT`/`DOUBLE`: `0.1 + 0.2 != 0.3` vì số nhị phân không biểu diễn chính xác được `0.1`
  - Luôn lưu kèm mã tiền tệ (ISO 4217: `VND`, `USD`); một số tiền không có currency là vô nghĩa
  - Số chữ số thập phân khác nhau theo tiền tệ: VND và JPY là 0, USD là 2, một số tiền như KWD là 3. Integer minor unit phải biết exponent của từng loại
  - API: trả integer minor unit hoặc string decimal (`"125000.50"`), không trả số thực JSON
  - **Đối chiếu**: Java `BigDecimal` (⚠️ `new BigDecimal(0.1)` mang theo sai số của double; dùng `new BigDecimal("0.1")` hoặc `BigDecimal.valueOf`; `equals` so cả scale nên `2.0` khác `2.00`, dùng `compareTo`); Go không có decimal trong thư viện chuẩn, dùng integer hoặc thư viện như `shopspring/decimal`; PHP dùng integer, `bcmath` (string) hoặc thư viện như `brick/money`
- [ ] 🟡 Làm tròn
  - Half-up (0.5 lên), half-even/banker's rounding (0.5 về số chẵn gần nhất: 2.5 → 2, 3.5 → 4) giảm sai lệch tích luỹ khi cộng nhiều số đã làm tròn; nghiệp vụ/luật thuế quyết định dùng kiểu nào
  - Làm tròn **ở đâu** quan trọng như làm tròn thế nào: làm tròn thuế từng dòng rồi cộng khác với cộng rồi làm tròn. Chốt quy tắc với kế toán, làm tròn ở một chỗ, lưu giá trị đã làm tròn
  - ⚠️ PHP `round()` mặc định half away from zero; Java `BigDecimal.setScale` phải chỉ định `RoundingMode`; JS `toFixed` dựa trên double nên có kết quả bất ngờ
- [ ] 🟡 Đa tiền tệ và tỷ giá
  - Lưu số tiền theo tiền tệ gốc giao dịch, cộng thêm số tiền quy đổi + tỷ giá + thời điểm tỷ giá đã dùng. Không quy đổi lại từ tỷ giá hiện tại khi xem đơn cũ
  - Không cộng tiền khác loại; kiểu `Money(amount, currency)` từ chối phép cộng khác currency
  - Tỷ giá lấy từ nguồn nào, cập nhật khi nào, spread mua/bán: là quyết định nghiệp vụ, ghi rõ
- [ ] 🟡 Chia tiền không mất đồng lẻ
  - 100.000đ chia 3: `33.333 + 33.333 + 33.333 = 99.999`, mất 1 đồng
  - Cách làm: tính phần nguyên cho mỗi phần, đem phần dư phân cho vài phần đầu (hoặc theo largest remainder khi chia theo tỷ lệ): `33.334 + 33.333 + 33.333`
  - Tổng các phần phải bằng đúng tổng ban đầu; viết assert cho bất biến này
  - Áp dụng: chia giảm giá cho từng dòng đơn, hoàn tiền một phần, chia hoa hồng
- [ ] 🔴 Ledger và bút toán kép
  - Không lưu số dư bằng một cột rồi `UPDATE balance = balance - x` là xong; ghi **mỗi giao dịch** thành các bút toán bất biến (append-only)
  - Bút toán kép: mỗi giao dịch có ít nhất một ghi nợ và một ghi có, tổng bằng nhau. Chuyển 100 từ ví A sang B: A −100, B +100. Tổng toàn hệ thống luôn bằng 0, là bất biến để kiểm tra
  - Sai thì **không sửa/xoá** bút toán cũ, ghi bút toán đảo (reversal) và bút toán đúng
  - Số dư = tổng bút toán; có thể lưu số dư cache/snapshot, cập nhật trong cùng transaction, đối chiếu định kỳ với tổng bút toán
  - Chống âm số dư khi trừ đồng thời: lock dòng (`SELECT ... FOR UPDATE`) hoặc `UPDATE ... WHERE balance >= x` và kiểm tra số dòng bị ảnh hưởng (xem [13-concurrency.md](13-concurrency.md))

### Chuỗi

- [ ] 🟢 UTF-8 ở mọi nơi: DB, kết nối DB (charset của connection), file, HTTP header `Content-Type: ...; charset=utf-8`
  - ⚠️ MySQL `utf8` là `utf8mb3`: tối đa 3 byte mỗi ký tự, không lưu được emoji và một số ký tự ngoài BMP; lưu vào bị lỗi hoặc bị cắt tuỳ `sql_mode`. Dùng `utf8mb4` cho cả bảng, cột **và** kết nối
  - Chuyển bảng sang `utf8mb4` làm tăng số byte tối đa của cột: để ý giới hạn độ dài index (kiểm tra theo phiên bản và row format)
- [ ] 🟡 Collation
  - Quyết định so sánh và sắp xếp. MySQL 8 mặc định `utf8mb4_0900_ai_ci`: `ai` = accent-insensitive, `ci` = case-insensitive
  - ⚠️ Hệ quả với tiếng Việt: `'Nguyễn' = 'nguyen'` là đúng; unique index trên `username` coi `"hoà"` và `"hoa"` là trùng; `WHERE name = 'Lê'` trả cả `"Le"`. Có lúc muốn vậy (tìm kiếm), có lúc không (mã, username, token)
  - Cột cần so khớp chính xác (mã giảm giá, token, hash) dùng collation `_bin` hoặc `_as_cs`
  - Postgres: so sánh mặc định phân biệt hoa thường; dùng `lower()` + index biểu thức, `citext`, hoặc ICU nondeterministic collation
- [ ] ⚠️ Unicode normalization
  - Một chữ có thể biểu diễn nhiều cách: `"ệ"` là một code point (U+1EC7, dạng dựng sẵn, NFC) hoặc `e` + dấu nặng (U+0323) + dấu mũ (U+0302) (dạng tổ hợp, NFD). Nhìn giống hệt nhau, so sánh byte thì khác, độ dài khác
  - Nguồn NFD hay gặp: tên file từ macOS, văn bản copy từ một số trình soạn thảo/bộ gõ, dữ liệu import
  - Chuẩn hoá về **NFC** tại ranh giới nhập liệu (trước khi lưu, trước khi so sánh/hash/tạo unique key). PHP `Normalizer::normalize($s, Normalizer::FORM_C)` (ext-intl), Java `java.text.Normalizer`, Go `golang.org/x/text/unicode/norm`
  - ⚠️ Tiếng Việt còn có hai kiểu **đặt dấu** (kiểu cũ `hòa`, kiểu mới `hoà`): khác code point, normalization NFC **không** gộp hai kiểu này. Cần gộp thì tự chuẩn hoá theo một quy tắc, hoặc so sánh dạng đã bỏ dấu
- [ ] 🟡 Tìm kiếm tiếng Việt không dấu
  - Bỏ dấu: NFD rồi bỏ các combining mark. ⚠️ `đ`/`Đ` không tách được thành `d` + dấu, phải map tay
  - Lưu thêm cột đã bỏ dấu + lowercase (`name_search`) và index cột đó, hoặc dựa vào collation `ai_ci` của MySQL
  - Full-text: Postgres `unaccent` + `pg_trgm`; Elasticsearch/OpenSearch với `asciifolding` filter và analyzer cho tiếng Việt (xem [04-nosql-search-storage.md](04-nosql-search-storage.md))
  - Tiếng Việt tách từ theo âm tiết, cụm từ nhiều âm tiết ("thành phố") cần phrase query hoặc tokenizer riêng
- [ ] 🟡 Độ dài chuỗi
  - Ba đơn vị: byte, code point, grapheme cluster (cái người dùng coi là "một ký tự"). Emoji gia đình 👨‍👩‍👧 là nhiều code point nối bằng ZWJ nhưng là một grapheme
  - PHP `strlen` đếm byte, `mb_strlen` đếm code point, `grapheme_strlen` đếm grapheme; Go `len(s)` đếm byte, `utf8.RuneCountInString` đếm rune; Java `String.length()` đếm UTF-16 code unit (emoji ngoài BMP tính 2)
  - ⚠️ `substr` cắt theo byte làm vỡ ký tự tiếng Việt giữa chừng, ra chuỗi UTF-8 không hợp lệ (JSON encode lỗi). Dùng hàm `mb_*` hoặc cắt theo rune/grapheme
  - MySQL `VARCHAR(n)` tính theo **ký tự**; giới hạn của frontend, backend, DB phải khớp cùng một đơn vị
- [ ] 🟢 Slug
  - `"Hướng dẫn Đà Nẵng 2026"` → `huong-dan-da-nang-2026`: bỏ dấu (nhớ `đ`), lowercase, thay ký tự lạ bằng `-`, gộp `-` liên tiếp
  - Unique: thêm hậu tố hoặc kèm id (`/posts/123-huong-dan`) để đổi tiêu đề không vỡ link; slug cũ nên redirect `301`
  - Laravel `Str::slug` có hỗ trợ tiếng Việt, vẫn kiểm tra với `đ`

### Số

- [ ] 🟡 Integer overflow
  - `INT` MySQL có dấu tối đa khoảng 2,1 tỷ: bảng log/event, counter lượt xem, cột id auto-increment đều có thể chạm. Dùng `BIGINT` cho id bảng lớn; theo dõi % đã dùng của auto-increment
  - ⚠️ Đổi kiểu cột id trên bảng lớn là migration nặng (xem [03-database-sql.md](03-database-sql.md)); chọn đúng từ đầu
  - Ngôn ngữ: Java `int` tràn âm thầm (dùng `Math.addExact` khi cần phát hiện); Go tràn theo wraparound; PHP tự chuyển sang float khi vượt `PHP_INT_MAX`, mất chính xác âm thầm
- [ ] 🟡 int64 trong JSON với JavaScript: vượt `2^53 - 1` thì bị làm tròn. Trả ID lớn dạng string. Chi tiết ở [09-api-design.md](09-api-design.md)
- [ ] 🟢 Floating point: không so sánh `==` trực tiếp; không dùng cho tiền; phần trăm, tỷ lệ cho hiển thị thì được

### ID

- [ ] 🟡 Chọn kiểu ID

  | Kiểu | Kích thước | Có thứ tự | Ưu | Nhược |
  |---|---|---|---|---|
  | Auto-increment | 4–8 byte | có | nhỏ, index tốt | lộ số lượng, đoán được, khó sinh phân tán, merge DB khó |
  | UUIDv4 | 16 byte | không | sinh ở bất kỳ đâu, không đoán được | chèn ngẫu nhiên vào B-tree: page split, index phân mảnh (nặng với clustered index của InnoDB) |
  | UUIDv7 | 16 byte | theo thời gian | sinh phân tán, chèn gần như tuần tự | lộ thời điểm tạo |
  | ULID | 16 byte (26 ký tự Crockford base32) | theo thời gian | như UUIDv7, chuỗi ngắn hơn | lộ thời điểm tạo |
  | Snowflake | 8 byte | theo thời gian | nhỏ, có thứ tự | cần cấp machine id, phụ thuộc đồng hồ (⚠️ đồng hồ lùi), vượt `2^53` trong JS |

  - UUIDv7 được chuẩn hoá trong RFC 9562. Lưu UUID dạng `BINARY(16)` / kiểu `uuid` (Postgres), không `CHAR(36)`
  - ⚠️ Auto-increment lộ thông tin: `/orders/10523` hôm nay và `/orders/10890` ngày mai cho đối thủ biết số đơn mỗi ngày; kẻ xấu duyệt lần lượt id (kết hợp IDOR, xem [10-security.md](10-security.md))
- [ ] 🟡 Public id vs internal id: giữ `BIGINT` auto-increment làm khoá chính nội bộ (join nhanh, index nhỏ), thêm cột `public_id` (UUID/ULID/chuỗi ngẫu nhiên, unique) để lộ ra URL/API. Mã hiển thị cho người (mã đơn `DH-260923-4821`) là cột riêng nữa

### File

- [ ] 🟡 Upload lớn
  - Không để file lớn đi qua app server nếu tránh được: app cấp **presigned URL** (S3/GCS) có hạn ngắn, client upload thẳng lên object storage, sau đó báo app (hoặc event từ storage) để xử lý
  - File rất lớn: multipart upload (chia phần, upload song song, retry từng phần), hoặc giao thức resumable (tus). ⚠️ Multipart upload dở dang vẫn tốn tiền lưu trữ; đặt lifecycle rule dọn
  - Qua app server: giới hạn ở mọi tầng khớp nhau (Nginx `client_max_body_size`, PHP `upload_max_filesize`/`post_max_size`, framework), stream xuống đĩa/storage thay vì đọc cả file vào memory
- [ ] 🟡 Kiểm tra file: loại thật bằng magic bytes (PHP `finfo`, Go `http.DetectContentType`), kích thước, số trang/kích thước ảnh; đổi tên; chi tiết bảo mật ở [10-security.md](10-security.md)
- [ ] 🟡 Xử lý ảnh/video async: upload xong trả ngay, job tạo thumbnail/resize/transcode; trạng thái `processing` → `ready`/`failed`; giới hạn kích thước pixel trước khi decode (ảnh 50000×50000 nhỏ trên đĩa nhưng nổ RAM)
- [ ] 🟡 Import CSV/Excel lớn
  - Nhận file → lưu storage → tạo job → trả `202` + id (xem long-running operation ở [09-api-design.md](09-api-design.md))
  - Đọc **streaming** từng dòng (`fgetcsv`, `SplFileObject`, Go `encoding/csv`, Apache POI streaming/SAX cho `.xlsx`), không load cả file vào memory. ⚠️ Nhiều thư viện Excel mặc định load toàn bộ workbook
  - Xử lý theo chunk (ví dụ vài trăm tới vài nghìn dòng mỗi batch insert), mỗi chunk một transaction; không một transaction khổng lồ khoá bảng lâu
  - Validate từng dòng, **thu lỗi** theo số dòng thay vì dừng ở lỗi đầu tiên; cho tải file lỗi về sửa. Quy định rõ: dòng lỗi thì bỏ qua dòng đó hay huỷ cả file
  - Báo tiến độ: lưu `processed_rows/total_rows` vào DB/cache, client poll
  - Idempotent: hash file hoặc import id để không import hai lần; upsert theo khoá tự nhiên (mã sản phẩm) để chạy lại sau lỗi giữa chừng không tạo trùng
  - ⚠️ Excel tự đổi dữ liệu: số điện thoại mất số 0 đầu, mã dài thành dạng khoa học `1.23E+15`, chuỗi giống ngày thành ngày. Đọc cell dạng text, chuẩn hoá lại
- [ ] 🟡 Export lớn
  - Job nền, stream ra file (cursor/chunk từ DB, không `->get()` cả bảng), upload storage, gửi link có hạn
  - Excel `.xlsx` giới hạn 1.048.576 dòng mỗi sheet
  - ⚠️ BOM: Excel trên Windows mở CSV UTF-8 không có BOM thường hiện tiếng Việt thành ký tự rác. Ghi 3 byte BOM `EF BB BF` ở đầu file khi mục tiêu là Excel; ngược lại, khi **đọc** CSV phải bỏ BOM nếu có (không thì tên cột đầu tiên có ký tự lạ và so khớp header thất bại)
  - ⚠️ CSV injection: ô bắt đầu bằng `=`, `+`, `-`, `@` bị Excel hiểu là công thức. Dữ liệu do user nhập, khi export thì thêm `'` phía trước hoặc escape

### Email, SMS, OTP

- [ ] 🟡 Xác thực email gửi đi (bản ghi DNS)
  - SPF: bản ghi TXT liệt kê server/dịch vụ được phép gửi mail cho domain. ⚠️ Giới hạn số lần tra DNS lồng nhau (`include`), vượt thì SPF fail
  - DKIM: server gửi ký header/body bằng private key; public key công bố ở `selector._domainkey.domain`. Chứng minh mail không bị sửa và đúng domain ký
  - DMARC: chính sách khi SPF/DKIM fail hoặc không khớp domain `From` (alignment): `p=none` → `quarantine` → `reject`; `rua` nhận báo cáo. Bắt đầu bằng `none` để quan sát
  - Các nhà cung cấp lớn (Gmail, Yahoo) đã siết yêu cầu với người gửi số lượng lớn: cần SPF, DKIM, DMARC, unsubscribe một chạm, tỷ lệ spam thấp (kiểm tra lại yêu cầu hiện hành)
  - Tách domain/subdomain cho mail giao dịch và mail marketing để uy tín không kéo nhau xuống
- [ ] 🟡 Bounce và complaint: hard bounce (địa chỉ không tồn tại) thì ngừng gửi địa chỉ đó; complaint (bấm "spam") thì hủy đăng ký. Nhận qua webhook của nhà cung cấp (SES, SendGrid, Mailgun), lưu suppression list
- [ ] 🟢 Gửi qua queue, không gửi trong transaction
  - Gửi mail trong request làm request chậm và lỗi SMTP làm lỗi cả nghiệp vụ
  - ⚠️ Gửi trong transaction: mail đã đi nhưng transaction rollback (khách nhận "đặt hàng thành công" cho đơn không tồn tại). Dispatch job **sau commit** (Laravel `afterCommit`, Spring `@TransactionalEventListener(AFTER_COMMIT)`) hoặc outbox (xem [12-messaging.md](12-messaging.md))
  - Job gửi mail có thể chạy lại: chấp nhận trùng hiếm hoi hoặc lưu trạng thái đã gửi
  - Môi trường dev/staging: dùng mail catcher (Mailpit, Mailtrap), ⚠️ không bao giờ gửi mail thật tới khách từ staging
- [ ] 🟡 SMS / OTP
  - OTP ngẫu nhiên bằng CSPRNG, 6 chữ số là phổ biến; lưu hash, hết hạn ngắn (vài phút), dùng một lần, gắn với mục đích (login khác đổi SĐT)
  - Chống brute force: giới hạn số lần nhập sai mỗi OTP (quá thì huỷ OTP), giới hạn số lần gửi theo SĐT/IP/thiết bị, thời gian chờ giữa hai lần gửi lại
  - ⚠️ Chi phí và SMS pumping: bot gọi endpoint gửi OTP tới số premium/quốc tế để ăn chia cước. Giới hạn quốc gia được gửi, CAPTCHA trước khi gửi, cảnh báo khi chi phí SMS tăng đột biến
  - Ở Việt Nam, SMS thường phải qua brandname đăng ký với nhà mạng và nội dung theo mẫu; nhà cung cấp có thể chậm hoặc rớt tin, nên có kênh dự phòng (Zalo ZNS, email, voice OTP)

### Thanh toán qua cổng

- [ ] 🟡 Luồng chung (VNPay, Momo, Stripe khác nhau về chi tiết, giống nhau về khái niệm)

  ```
  1. Client tạo đơn → server tạo payment (pending) với mã giao dịch duy nhất
  2. Server tạo URL thanh toán (có chữ ký) → redirect user sang cổng
  3. User trả tiền ở cổng
  4a. Cổng redirect user về return URL  → chỉ để HIỂN THỊ, không tin để cập nhật đơn
  4b. Cổng gọi IPN/webhook server-to-server → verify chữ ký → cập nhật đơn
  5. Đối soát định kỳ với báo cáo của cổng
  ```

  - ⚠️ Return URL đi qua trình duyệt: user có thể sửa tham số, đóng tab trước khi redirect xong, hoặc mạng rớt. Nguồn sự thật là IPN/webhook và API tra cứu giao dịch
  - Verify chữ ký theo đúng thuật toán và thứ tự tham số trong tài liệu của từng cổng (thường là HMAC với secret được cấp); so sánh constant-time; kiểm tra **số tiền và mã đơn** trong IPN khớp với đơn của mình
  - IPN phải idempotent: cổng gửi lại nhiều lần; đơn đã `paid` thì trả thành công, không cộng tiền lần hai. Trả đúng format response mà cổng yêu cầu, không thì cổng tiếp tục gửi lại
- [ ] ⚠️ Timeout không rõ kết quả
  - Gọi API thanh toán/hoàn tiền bị timeout: **không biết** bên kia đã trừ tiền chưa. ⚠️ Không coi là thất bại, không tạo giao dịch mới ngay
  - Đặt trạng thái `unknown`/`pending_confirmation`, gọi API tra cứu theo mã giao dịch (có retry backoff), chờ IPN; retry lệnh gốc chỉ khi dùng cùng idempotency key/mã giao dịch
  - User quay lại khi đơn đang `pending`: hiển thị "đang xác nhận", không cho thanh toán lần hai với mã mới khi chưa chắc lần trước thất bại
- [ ] 🟡 Đối soát (reconciliation)
  - Job hằng ngày so giao dịch của mình với file/API đối soát của cổng: lệch số tiền, có bên này không có bên kia, trạng thái khác
  - Bắt được IPN bị mất, bug cập nhật, gian lận; kết quả lệch phải có người xử lý, không chỉ ghi log
- [ ] 🟡 Thiết kế nhiều cổng: interface `PaymentGateway` (`createPayment`, `verifyCallback`, `query`, `refund`) với adapter từng cổng (strategy/adapter, xem [08-oop-design.md](08-oop-design.md)); bảng `payments` tách khỏi `orders` (một đơn có thể nhiều lần thử thanh toán); lưu raw payload IPN để điều tra

### State machine và audit trail

- [ ] 🟡 State machine cho trạng thái nghiệp vụ
  - Liệt kê trạng thái và **chuyển đổi hợp lệ**; mọi thay đổi trạng thái đi qua một hàm kiểm tra

    ```
    pending ──pay──▶ paid ──ship──▶ shipped ──deliver──▶ delivered
       │               │                                     │
     cancel         refund                                 return
       ▼               ▼                                     ▼
    cancelled       refunded                              returned
    ```

  - ⚠️ `UPDATE orders SET status = 'paid'` rải rác khắp code là nguồn bug: IPN đến trễ đưa đơn `cancelled` về `paid`, hoặc đơn `shipped` bị huỷ
  - Chuyển trạng thái nguyên tử có điều kiện: `UPDATE orders SET status = 'paid' WHERE id = ? AND status = 'pending'`, kiểm tra số dòng bị ảnh hưởng; 0 dòng thì xử lý theo nghiệp vụ (đã paid rồi thì idempotent, đã cancelled thì cần hoàn tiền)
  - Trường hợp "đã huỷ nhưng tiền về" là thật; state machine phải có nhánh cho nó
- [ ] 🟡 Audit trail
  - Bảng lịch sử: `order_id, from_status, to_status, actor (user/system/webhook), reason, created_at`, thêm payload thay đổi khi cần
  - Trả lời được "ai đổi cái này, lúc nào, vì sao" khi khách khiếu nại; append-only; xem thêm audit log ở [10-security.md](10-security.md)

### i18n / l10n

- [ ] 🟢 i18n là chuẩn bị để hỗ trợ nhiều ngôn ngữ/vùng; l10n là làm cho một vùng cụ thể
  - Chuỗi hiển thị lấy từ file dịch theo key, không hard-code; hỗ trợ số nhiều (plural rules khác nhau giữa ngôn ngữ) và tham số
  - Định dạng số theo locale: `1.234.567,5` (vi-VN) vs `1,234,567.5` (en-US); tiền: `1.234.567 ₫` vs `$1,234.57`. ⚠️ Parse số người dùng nhập theo locale sai là lệch 1000 lần
  - Định dạng ngày theo locale (`23/09/2026` vs `09/23/2026`); API luôn dùng ISO 8601, chỉ tầng hiển thị định dạng theo locale
  - Dùng thư viện ICU/CLDR (PHP `intl` `NumberFormatter`/`IntlDateFormatter`, Java `NumberFormat`/`DateTimeFormatter` với `Locale`, Go `golang.org/x/text`)
  - Sắp xếp theo ngôn ngữ (tên tiếng Việt) cần collation đúng locale
  - Nội dung đa ngôn ngữ trong DB: bảng translation riêng hoặc cột JSON theo locale; có fallback locale

### Soft delete, dữ liệu mồ côi, môi trường

- [ ] 🟡 Soft delete (`deleted_at`)
  - Lợi: khôi phục được, giữ tham chiếu lịch sử (đơn cũ vẫn trỏ tới sản phẩm đã xoá)
  - Giá: mọi query phải lọc (⚠️ quên ở query raw, report, join); ⚠️ unique index bị ảnh hưởng: xoá mềm `a@x.com` rồi đăng ký lại bị trùng. Postgres dùng partial unique index `WHERE deleted_at IS NULL`; MySQL không có partial index, dùng generated column hoặc đưa `deleted_at`/cờ vào unique key
  - Bảng phình to, dữ liệu cá nhân "đã xoá" vẫn còn (vướng yêu cầu xoá dữ liệu, xem [10-security.md](10-security.md))
  - Thay thế: chuyển sang bảng archive, hoặc trạng thái nghiệp vụ rõ ràng (`archived`, `deactivated`) thay vì xoá mềm chung chung
- [ ] 🟡 Dữ liệu mồ côi
  - Xoá cha mà con còn (thiếu foreign key, hoặc xoá mềm cha nhưng con không biết); file trên storage không còn bản ghi nào trỏ tới; key cache/search index của bản ghi đã xoá
  - Chống: foreign key với hành vi rõ ràng (`RESTRICT`/`CASCADE`), xoá theo thứ tự trong transaction, job dọn định kỳ, truy vấn kiểm tra toàn vẹn
- [ ] ⚠️ Dữ liệu test lẫn dữ liệu thật
  - Tài khoản test trên production làm sai báo cáo doanh thu, nhận email marketing, dính đối soát
  - Đánh dấu rõ (`is_test`), loại khỏi báo cáo, dùng domain email riêng, cổng thanh toán sandbox tách biệt
- [ ] ⚠️ Môi trường test dùng chung DB
  - Test tự động nối vào DB dev/staging dùng chung có thể xoá sạch dữ liệu người khác: `TRUNCATE` trong setup test, `migrate:fresh`, `RefreshDatabase`; lệnh trông như "chỉ chạy test" nhưng bên trong có migration và xoá bảng
  - Cô lập: DB riêng cho test (khai rõ trong `phpunit.xml`/`.env.testing`, profile Spring, biến môi trường riêng), container DB tạm (Testcontainers), transaction rollback sau mỗi test
  - Rào chắn: code test từ chối chạy nếu tên DB không có hậu tố `_test`; tài khoản DB của môi trường test không có quyền trên DB khác; production credential không bao giờ có trên máy dev
  - Xem thêm [20-testing-quality.md](20-testing-quality.md)

## Senior trả lời khác gì

| Câu hỏi | Junior / mid | Senior |
|---|---|---|
| "Lưu thời gian thế nào?" | Lưu UTC | Phân biệt instant, ngày thuần, giờ địa phương lặp lại; kiểu cột theo DB; timezone là tên vùng; báo cáo theo ngày địa phương dùng khoảng UTC nửa mở; cron ghi rõ timezone |
| "Vì sao không dùng float cho tiền?" | Sai số làm tròn | Thêm: currency đi kèm, exponent từng loại, làm tròn ở đâu và theo quy tắc nào, chia không mất đồng lẻ, ledger append-only thay vì sửa số dư |
| "Tìm kiếm tên tiếng Việt không dấu?" | Dùng `LIKE` | Chuẩn hoá NFC khi lưu, cột đã bỏ dấu (nhớ `đ`) có index, hoặc collation `ai_ci` và hệ quả của nó với unique; lên search engine khi cần full-text |
| "IPN báo thành công nhưng đơn đã bị huỷ?" | Cập nhật lại thành paid | State machine có nhánh này: không đổi trạng thái mù, tạo yêu cầu hoàn tiền hoặc khôi phục đơn theo nghiệp vụ, audit trail, đối soát bắt được |
| "Import 500.000 dòng Excel?" | Đọc file rồi insert vòng lặp | Job nền, streaming, chunk + transaction ngắn, validate và thu lỗi theo dòng, tiến độ, idempotent qua upsert khoá tự nhiên, cẩn thận Excel đổi kiểu dữ liệu |

## Tình huống

1. **Báo cáo doanh thu ngày của sếp lệch với số của kế toán.**
   Gợi ý:
   - Kiểm tra ranh giới ngày: UTC hay UTC+7; `BETWEEN` với `23:59:59`; đơn hoàn tiền tính vào ngày nào
   - Chốt định nghĩa "doanh thu ngày" với kế toán, viết thành query chuẩn dùng chung
2. **Khách tên "Nguyễn Thị Huệ" không tìm được bằng chính tên đó dù dữ liệu có.**
   Gợi ý:
   - Dữ liệu lưu NFD (import từ file macOS), từ khoá gõ NFC; hoặc kiểu đặt dấu cũ/mới
   - Chuẩn hoá NFC khi lưu và khi tìm, migrate dữ liệu cũ, thêm cột tìm kiếm đã bỏ dấu
3. **Gọi API hoàn tiền bị timeout, dev retry và khách được hoàn hai lần.**
   Gợi ý:
   - Timeout không phải thất bại; trạng thái `unknown`, tra cứu trước khi retry, idempotency key/mã hoàn tiền cố định
   - Đối soát hằng ngày; quy trình thu hồi
4. **Mở file export đơn hàng bằng Excel, tên khách thành ký tự lạ và số điện thoại mất số 0.**
   Gợi ý:
   - Thêm BOM UTF-8; số điện thoại xuất dạng text (hoặc xuất `.xlsx` với kiểu cell text)
   - Kiểm tra luôn CSV injection với dữ liệu user nhập
5. **Chạy test ở máy local làm mất dữ liệu trên DB staging của cả team.**
   Gợi ý:
   - Cấu hình test không khai DB riêng nên dùng `.env` trỏ staging; setup có `TRUNCATE`/migrate
   - DB riêng cho test, guard theo tên DB, quyền DB tách, khôi phục từ backup, postmortem
6. **Job gửi email nhắc lịch lúc 8h sáng, khách ở Úc nhận lúc 11h trưa, và có ngày nhận hai lần.**
   Gợi ý:
   - Cron chạy theo giờ server; phải tính theo timezone từng user; DST ở Úc làm lệch
   - Chạy mỗi 15 phút chọn user tới giờ, lưu "đã gửi cho ngày X" để idempotent
7. **Chia khuyến mãi 50.000đ cho 3 dòng sản phẩm, tổng hoàn tiền khi trả từng dòng lệch vài đồng.**
   Gợi ý:
   - Phân bổ có phần dư, lưu số đã phân bổ cho từng dòng lúc đặt hàng; hoàn theo số đã lưu, không tính lại

## ❓ Câu hỏi hay gặp

🟢
- Vì sao nên lưu thời gian ở UTC?
- Vì sao không nên lưu tiền bằng `FLOAT`?
- MySQL `utf8` và `utf8mb4` khác nhau thế nào?
- Vì sao không gửi email trong transaction DB?

🟡
- `TIMESTAMP` và `DATETIME` trong MySQL khác nhau thế nào? `timestamptz` trong Postgres lưu gì?
- Làm báo cáo doanh thu theo ngày cho người dùng ở UTC+7 khi dữ liệu lưu UTC?
- Chia 100.000đ cho 3 người thế nào để không mất đồng nào?
- NFC và NFD là gì? Vì sao hai chuỗi tiếng Việt nhìn giống nhau lại không bằng nhau?
- Collation `utf8mb4_0900_ai_ci` ảnh hưởng gì tới unique index?
- Vì sao không lộ id auto-increment ra URL? UUIDv4 có vấn đề gì với index?
- SPF, DKIM, DMARC là gì?
- Thiết kế import file CSV 1 triệu dòng.
- Luồng thanh toán qua cổng: return URL và IPN khác nhau thế nào? Tin cái nào?

🔴
- Gọi cổng thanh toán bị timeout, bạn xử lý thế nào?
- Thiết kế ví điện tử theo ledger bút toán kép.
- Soft delete có vấn đề gì? Khi nào bạn không dùng?
- Làm sao đảm bảo test tự động không bao giờ đụng vào DB dùng chung hoặc production?

## Bài tập tự làm

1. Viết hàm `allocate(amount, ratios)` (ngôn ngữ tuỳ chọn) chia một số tiền integer theo tỷ lệ, đảm bảo tổng các phần bằng đúng `amount`. Tự liệt kê các test case cần có.
2. Viết query báo cáo số đơn theo ngày giờ Việt Nam trong tháng 9/2026 từ bảng `orders(created_at UTC)`, bằng cả MySQL và Postgres, và giải thích query nào dùng được index.
3. Viết hàm chuẩn hoá chuỗi tìm kiếm tiếng Việt: NFC, lowercase, bỏ dấu (xử lý `đ`), gộp khoảng trắng. Liệt kê ít nhất 8 input kiểm tra, gồm cả NFD và kiểu đặt dấu cũ/mới.
4. Vẽ state machine cho đơn hàng có thanh toán online, gồm các nhánh: IPN đến trễ sau khi đơn bị huỷ, thanh toán timeout, hoàn tiền một phần. Viết bảng chuyển đổi hợp lệ.
5. Thiết kế bảng và luồng cho tính năng import sản phẩm từ Excel: bảng job import, bảng lỗi theo dòng, cách chạy lại an toàn, cách báo tiến độ.

> Nộp bài vào đây để được review.
