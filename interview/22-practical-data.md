# 22. Dữ liệu thực tế: những thứ "đời thường" hay gây bug production

> [← Mục lục](README.md) · Trọng tâm: thời gian và timezone, tiền, Unicode và tiếng Việt, số và ID, file và import/export, email/SMS/OTP, cổng thanh toán, state machine, soft delete, cô lập môi trường. Stack **PHP/Laravel + MySQL 8.4 LTS** (MySQL 8.0 đã hết hỗ trợ từ 04/2026), đối chiếu PostgreSQL, Java, Go.
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

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [MySQL 8.4 Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/) | Official docs | Kiểu thời gian, timezone, charset/collation, số |
| [PHP Manual](https://www.php.net/manual/en/) | Official docs | Date/Time, bcmath, mbstring, intl (Normalizer, Transliterator, NumberFormatter), SPL file |
| [Laravel docs](https://laravel.com/docs/eloquent-mutators#date-casting) | Official docs | Date casting, scheduler timezone, queue sau commit, streamed download |
| [Unicode UAX #15](https://unicode.org/reports/tr15/) và [UAX #29](https://unicode.org/reports/tr29/) | Chuẩn | Normalization (NFC/NFD) và grapheme cluster. Đọc phần giới thiệu và hình ví dụ |
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | Hướng dẫn bảo mật | Upload file, [CSV injection](https://owasp.org/www-community/attacks/CSV_Injection) |
| [Stripe docs](https://docs.stripe.com/webhooks) | Official docs của cổng thanh toán | Webhook, [idempotent request](https://docs.stripe.com/api/idempotent_requests): tài liệu mẫu mực để hiểu khái niệm, áp dụng cho cả VNPay/Momo |
| [Modern Treasury: Accounting for Developers](https://www.moderntreasury.com/journal/accounting-for-developers-part-i) | Blog kỹ thuật | Ledger, bút toán kép viết cho developer |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Lưu thời gian, tiền, chuỗi đúng kiểu; gửi thông báo qua queue | 2–3 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.7 | Không dính bug timezone, làm tròn, Unicode tiếng Việt, ID, import/export, OTP; dùng đúng công cụ PHP | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.4 | Thiết kế ledger, tích hợp thanh toán an toàn, state machine, vệ sinh dữ liệu và môi trường | 5–7 ngày |

Học theo thứ tự: các bug ở chặng 2 hầu hết bắt nguồn từ việc bỏ qua một nguyên tắc ở chặng 1
(lưu UTC, không float, UTF-8 mọi nơi). Chặng 3 là nơi các chủ đề gặp nhau: một luồng thanh toán
đụng cả tiền, thời gian, idempotency và state machine.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Thời gian cơ bản

**Vì sao cần học:** Hầu như bảng nào cũng có cột thời gian, và bug thời gian thường chỉ lộ ra
khi có khách ở múi giờ khác hoặc khi hai hệ thống trao đổi dữ liệu. Với dev Việt Nam, bug kinh
điển là "lệch 7 tiếng". Người phỏng vấn hay hỏi "lưu thời gian thế nào" rồi đưa ra một trường
hợp mà "cứ lưu UTC" là sai.

**Học gì**

*Thời điểm và UTC*
- *Instant* (thời điểm) là một khoảnh khắc duy nhất trên dòng thời gian, giống nhau với mọi người
  trên thế giới. Ví dụ: lúc khách bấm "đặt hàng".
- Quy tắc: lưu instant ở **UTC**, chỉ đổi sang timezone của người xem khi hiển thị.
  - Ví dụ: đơn đặt lúc 8:30 sáng giờ Việt Nam được lưu là `01:30 UTC`. Khách ở Tokyo xem thì thấy
    10:30.

*Định dạng khi trao đổi qua API*
- Dùng chuẩn ISO 8601 / RFC 3339 **có offset** (độ lệch so với UTC):
  - `2026-09-23T01:30:00Z`: chữ `Z` nghĩa là UTC.
  - `2026-09-23T08:30:00+07:00`: cùng thời điểm đó, viết theo giờ Việt Nam.
- ⚠️ Chuỗi không có offset như `2026-09-23 08:30:00` là mơ hồ: bên nhận không biết đó là giờ
  Việt Nam hay UTC.

*Epoch*
- *Epoch timestamp* là số đơn vị thời gian đã trôi qua kể từ `1970-01-01T00:00:00Z`.
- Luôn nói rõ đơn vị là **giây hay mili giây**:
  - PHP `time()` trả giây.
  - Java `System.currentTimeMillis()` và JS `Date.now()` trả mili giây.
- ⚠️ Nhầm đơn vị thì ra ngày rất sai:
  - Số giây bị đọc như mili giây: ra một ngày đầu năm 1970.
  - Số mili giây bị đọc như giây: ra một ngày khoảng năm 50000.
  - Mẹo nhận biết: timestamp hiện tại tính bằng giây có 10 chữ số, bằng mili giây có 13 chữ số.

*Không phải thứ gì cũng là instant*
- *Ngày thuần* (không có giờ, không có timezone): ngày sinh, ngày lễ. Lưu bằng kiểu `DATE`.
  - ⚠️ Lưu ngày sinh thành timestamp UTC lúc nửa đêm thì người ở múi giờ âm (ví dụ Mỹ) thấy lệch
    một ngày: `1990-05-10T00:00:00Z` ở New York là tối 9/5.
- *Giờ địa phương + timezone*: "cửa hàng mở cửa 8:00 hằng ngày" nghĩa là 8:00 theo giờ nơi cửa
  hàng đặt, dù đổi giờ mùa hè hay không. Lưu giờ `08:00` kèm tên timezone, không đổi ra UTC.

**Đọc**
- [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) (mục 5.6 Internet Date/Time Format)
- Jon Skeet: [Storing UTC is not a silver bullet](https://codeblog.jonskeet.uk/2019/03/27/storing-utc-is-not-a-silver-bullet/): khi nào lưu UTC là sai (sự kiện tương lai theo giờ địa phương)
- [Falsehoods programmers believe about time](https://infiniteundo.com/post/25326999628/falsehoods-programmers-believe-about-time): danh sách ngắn, đọc để biết mình đang giả định gì

**Nắm chắc khi**
- [ ] Phân loại được 6 trường (thời điểm đặt hàng, ngày sinh, giờ mở cửa, hạn voucher, lịch họp tuần sau, `updated_at`) thành instant, ngày thuần hay giờ địa phương + timezone
- [ ] Nhìn một timestamp số nói được ngay là giây hay mili giây

#### 1.2 Tiền cơ bản

**Vì sao cần học:** Tiền sai một đồng cũng là bug nghiêm trọng, vì kế toán đối soát không khớp
và khách khiếu nại. Chọn sai kiểu dữ liệu ở đầu dự án thì về sau rất khó sửa. "Vì sao không
dùng float cho tiền" là câu hỏi gần như chắc chắn gặp.

**Học gì**

*Kiểu dữ liệu cho tiền*
- ⚠️ Không dùng `FLOAT`/`DOUBLE`. Số thực nhị phân không biểu diễn chính xác được `0.1`, nên
  `0.1 + 0.2 != 0.3`, và sai số cộng dồn qua nhiều phép tính.
- Hai cách đúng:
  - `DECIMAL(19,4)` (hoặc độ chính xác theo nghiệp vụ): DB lưu chính xác theo số chữ số thập phân
    đã khai.
  - Số nguyên theo *minor unit*, tức đơn vị nhỏ nhất của tiền tệ: xu, cent. Ví dụ 12,50 USD lưu
    là `1250`.

*Mã tiền tệ và số chữ số thập phân*
- Luôn lưu kèm mã tiền tệ theo chuẩn ISO 4217: `VND`, `USD`. Một con số không có tiền tệ đi kèm
  thì không có nghĩa.
- Mỗi tiền tệ có số chữ số thập phân (*exponent*) khác nhau:

| Tiền tệ | Số chữ số thập phân | Ví dụ minor unit |
|---|---|---|
| VND, JPY | 0 | 125.000đ lưu `125000` |
| USD | 2 | 12,50 USD lưu `1250` |
| KWD | 3 | 1,250 KWD lưu `1250` |

- ⚠️ Dùng số nguyên theo minor unit thì code phải biết exponent của từng tiền tệ. Chia 100 cho
  mọi tiền tệ là bug.

*Tiền trong API*
- Trả số nguyên minor unit (`125000`), hoặc chuỗi decimal (`"125000.50"`).
- Không trả số thực trong JSON, vì client (đặc biệt JavaScript) sẽ đọc nó thành float.

*Khi nào float vẫn dùng được*
- Phần trăm, tỷ lệ chỉ để hiển thị.
- Không so sánh hai số float bằng `==` trực tiếp. So sánh với một sai số cho phép.

**Đọc**
- MySQL: [Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html)
- Martin Fowler: [Money](https://martinfowler.com/eaaCatalog/money.html) (pattern `Money(amount, currency)`)

**Nắm chắc khi**
- [ ] Chứng minh được `0.1 + 0.2 != 0.3` trong PHP và giải thích bằng biểu diễn nhị phân
- [ ] Thiết kế được cột và JSON cho số tiền đa tiền tệ

#### 1.3 Chuỗi và UTF-8 cơ bản

**Vì sao cần học:** App tiếng Việt thì chuỗi có dấu có mặt ở mọi nơi: tên người, địa chỉ, tiêu
đề bài viết. Emoji bị thành `????`, tên bị cắt ra ký tự rác, slug mất chữ `đ` đều là bug hay
gặp. Người phỏng vấn thường hỏi "vì sao MySQL không lưu được emoji" và "độ dài chuỗi tính thế
nào".

**Học gì**

*UTF-8 ở mọi nơi*
- *UTF-8* là cách mã hoá ký tự Unicode thành byte: chữ Latin 1 byte, chữ có dấu tiếng Việt 2–3
  byte, emoji 4 byte.
- Mọi chỗ dữ liệu đi qua đều phải dùng UTF-8:
  - DB: bảng và cột.
  - **Kết nối DB**: charset của connection (Laravel: `'charset' => 'utf8mb4'` trong
    `config/database.php`).
  - File nguồn, file import/export.
  - Header HTTP: `Content-Type: ...; charset=utf-8`.
- ⚠️ `utf8` của MySQL thực chất là `utf8mb3`: tối đa 3 byte mỗi ký tự, nên không lưu được emoji.
  Dùng `utf8mb4` cho bảng, cột **và** kết nối. Thiếu một chỗ là emoji thành `?`.

*Ba đơn vị độ dài*
- *Byte*: số byte sau khi mã hoá UTF-8. `"ệ"` là 3 byte.
- *Code point*: một ký tự trong bảng Unicode, ví dụ U+1EC7 là `ệ`.
- *Grapheme*: cái người dùng coi là "một ký tự" khi nhìn.
  - Ví dụ: emoji gia đình 👨‍👩‍👧 gồm nhiều code point nối với nhau bằng ký tự *ZWJ* (zero-width
    joiner, ký tự vô hình dùng để ghép), nhưng người dùng thấy là một hình.
- MySQL `VARCHAR(n)` tính theo **ký tự** (code point), không theo byte.
- ⚠️ Giới hạn độ dài ở frontend, backend và DB phải dùng cùng một đơn vị. Frontend đếm grapheme,
  backend đếm byte là user nhập đủ 50 ký tự mà backend báo quá dài.

*Slug*
- *Slug* là phần chữ trong URL tạo từ tiêu đề. Ví dụ `"Hướng dẫn Đà Nẵng 2026"` thành
  `huong-dan-da-nang-2026`.
- Các bước:
  1. Bỏ dấu. ⚠️ Nhớ `đ`/`Đ`: đây là chữ riêng, không phải `d` có dấu, nhiều hàm bỏ dấu bỏ sót.
  2. Đổi sang chữ thường.
  3. Thay ký tự không phải chữ hay số bằng `-`.
  4. Gộp nhiều `-` liên tiếp thành một.
- Kèm id vào URL (`/posts/123-huong-dan`) để đổi tiêu đề không làm vỡ link cũ.
- Khi slug đổi, slug cũ redirect `301` sang slug mới.

**Đọc**
- MySQL: [The utf8mb4 Character Set](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb4.html), [Unicode Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html)
- Laravel: [`Str::slug`](https://laravel.com/docs/strings#method-str-slug)

**Nắm chắc khi**
- [ ] Liệt kê được mọi chỗ trong một app Laravel + MySQL phải khai UTF-8 để emoji lưu và hiển thị đúng
- [ ] Nói được độ dài theo byte, code point, grapheme của `"Việt 👨‍👩‍👧"`

#### 1.4 Thông báo qua queue

**Vì sao cần học:** Gần như app nào cũng gửi email xác nhận đơn, OTP, thông báo. Gửi sai cách
làm request chậm, hoặc tệ hơn là gửi "đặt hàng thành công" cho một đơn không tồn tại. Đây là
bug rất hay gặp trong Laravel và hay được hỏi cùng chủ đề transaction.

**Học gì**

*Vì sao gửi qua queue*
- Gửi email hay SMS ngay trong request có hai vấn đề:
  - Request chậm theo SMTP hay API của nhà cung cấp (có khi vài giây).
  - Lỗi SMTP làm hỏng cả nghiệp vụ, dù đơn hàng đã tạo xong.
- Cách làm: đẩy việc gửi vào *queue* (hàng đợi job), để một worker gửi ở nền.

*Gửi sau commit*
- ⚠️ Chuỗi sự cố khi dispatch job trong transaction:
  1. Code mở transaction, tạo đơn, dispatch job gửi mail.
  2. Worker lấy job ngay và gửi mail "đặt hàng thành công".
  3. Một bước sau trong transaction lỗi, transaction rollback.
  4. Khách nhận mail cho một đơn không tồn tại.
- Cách sửa:
  - Dispatch **sau khi commit**: Laravel có `afterCommit`.
  - Hoặc dùng *outbox*: ghi "việc cần gửi" vào một bảng trong cùng transaction, rồi một tiến trình
    khác đọc bảng đó và gửi ([12-messaging.md](12-messaging.md)).

*Job có thể chạy lại*
- Worker chết giữa chừng hay job timeout thì queue chạy lại job. Mail có thể bị gửi hai lần.
- Hai lựa chọn:
  - Chấp nhận trùng hiếm hoi (thường ổn với email thông báo).
  - Lưu trạng thái "đã gửi" và kiểm tra trước khi gửi.

*Môi trường dev và staging*
- ⚠️ Không bao giờ gửi mail thật tới khách từ dev hay staging. Dùng *mail catcher* (Mailpit,
  Mailtrap): nó nhận mọi mail và hiển thị trên giao diện web, không gửi đi đâu.

**Đọc**
- Laravel: [Queueing Mail](https://laravel.com/docs/mail#queueing-mail), [Queued Mailables and Database Transactions](https://laravel.com/docs/mail#queued-mailables-and-database-transactions), [Mail and Local Development](https://laravel.com/docs/mail#mail-and-local-development)

**Nắm chắc khi**
- [ ] Tái hiện được bug "email gửi cho đơn đã rollback" trong Laravel và sửa bằng `afterCommit`
- [ ] Nói được `afterCommit` còn thiếu gì so với outbox

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Timezone, DST, kiểu cột, cron, báo cáo

**Vì sao cần học:** Đây là module có nhiều bug production nhất trong file: báo cáo doanh thu
theo ngày bị lệch, cron chạy sai giờ, job chạy hai lần khi đổi giờ mùa hè. Dev ở Việt Nam ít gặp
DST nên hay bị bất ngờ khi có khách nước ngoài. Người phỏng vấn thường hỏi "viết query doanh thu
theo ngày" để xem bạn có nghĩ tới timezone không.

**Học gì**

*Kiểu cột thời gian trong MySQL*

| | `TIMESTAMP` | `DATETIME` |
|---|---|---|
| Khi lưu | Đổi từ `time_zone` của session sang UTC | Lưu nguyên con số bạn đưa vào |
| Khi đọc | Đổi từ UTC sang `time_zone` của session | Trả nguyên |
| Biết timezone? | Có, qua session | Không, app phải tự quy ước |
| Phạm vi | 1970 → 2038-01-19 UTC | năm 1000 → 9999 |

- ⚠️ Với `TIMESTAMP`, đổi `time_zone` của session là giá trị đọc ra cũng đổi theo. Còn vấn đề năm
  2038: sau 2038-01-19 kiểu này không lưu được.
- Hai cách làm đúng:
  - `DATETIME`, và app luôn ghi UTC.
  - `TIMESTAMP`, và cố định `time_zone = '+00:00'` cho **mọi** kết nối (web, worker, cron).

*Đối chiếu Postgres*
- `timestamptz` lưu instant (bên trong là UTC), khi hiển thị thì đổi theo setting `TimeZone` của
  session.
- ⚠️ Tên dễ gây hiểu lầm: `timestamptz` **không** lưu timezone gốc của dữ liệu. Cần biết timezone
  gốc thì thêm cột `tz` riêng.
- `timestamp` (không có `tz`) giống `DATETIME` của MySQL.

*Timezone là tên vùng, không phải offset*
- Timezone phải lưu bằng **tên vùng IANA**, ví dụ `Asia/Ho_Chi_Minh`, `Australia/Sydney`. Không
  lưu offset như `+07:00`.
- Lý do: offset của một vùng thay đổi theo mùa (DST) và theo luật của từng nước qua các năm. Tên
  vùng kèm cơ sở dữ liệu *tzdata* thì biết được offset đúng ở mọi thời điểm.
- Cập nhật tzdata ở mọi nơi: OS, PHP, JVM. Nước nào đổi luật giờ thì tzdata cũ tính sai.

*DST*
- *DST* (Daylight Saving Time, giờ mùa hè): một số nước vặn đồng hồ nhanh 1 giờ vào mùa hè, rồi
  vặn lùi vào mùa đông.
- Việt Nam luôn là UTC+7, không có DST. Vì vậy dev Việt hay không gặp lỗi DST cho tới khi có khách
  nước ngoài.
- Hệ quả của DST:
  - Có giờ **không tồn tại**: ngày vặn nhanh, đồng hồ nhảy từ 1:59 sang 3:00, không có 2:30.
  - Có giờ **xảy ra hai lần**: ngày vặn lùi, 1:30 xuất hiện hai lần.
  - "Cộng 1 ngày" khác "cộng 24 giờ" vào ngày đổi giờ, vì ngày đó chỉ có 23 hoặc 25 giờ.

*Đồng hồ giữa các máy*
- *Clock skew*: đồng hồ của các server lệch nhau từ vài ms tới vài giây. *NTP* (giao thức đồng bộ
  giờ) giảm độ lệch chứ không xoá hết.
- ⚠️ Không dùng timestamp của nhiều máy để xếp thứ tự sự kiện một cách chính xác.
- Các chỗ phải cho phép lệch nhỏ: JWT `exp`/`nbf`, chữ ký webhook có timestamp, OTP theo thời gian
  ([14-distributed-systems.md](14-distributed-systems.md)).
- Đo khoảng thời gian (một đoạn code chạy mất bao lâu) bằng *monotonic clock*, tức đồng hồ chỉ
  tăng, không bao giờ nhảy lùi: PHP `hrtime()`, Java `System.nanoTime()`, Go `time.Since`.
  - Không dùng *wall clock* (giờ hệ thống), vì NTP có thể chỉnh nó nhảy lùi, ra thời gian âm.

*Cron và scheduler*
- Cron chạy theo timezone của máy hoặc container, thường là UTC.
  - Ví dụ: "8h sáng giờ Việt Nam" là `0 1 * * *` theo UTC.
- Luôn ghi rõ timezone trong cấu hình: Laravel `->timezone()`, Spring `@Scheduled(zone = ...)`,
  Kubernetes CronJob `timeZone`.
- ⚠️ Ở vùng có DST, job đặt lúc 2:30 sáng có thể không chạy (giờ đó không tồn tại) hoặc chạy hai
  lần (giờ đó xảy ra hai lần).
- Job "8h sáng theo giờ của từng user":
  1. Chạy job mỗi 15 phút.
  2. Mỗi lần chạy, chọn những user mà giờ địa phương hiện tại khớp 8:00.
  3. Job phải *idempotent* (chạy lại không gây tác dụng hai lần), vì có thể chạy trùng.

*Báo cáo theo ngày*
- ⚠️ "Ngày" trong báo cáo là ngày theo timezone của doanh nghiệp, không phải ngày UTC.
  - Ví dụ: ngày 23/09 giờ Việt Nam là khoảng `[2026-09-22T17:00:00Z, 2026-09-23T17:00:00Z)` theo UTC.
- ⚠️ `GROUP BY DATE(created_at)` trên cột lưu UTC gán đơn lúc 6h sáng giờ VN vào ngày hôm trước,
  vì 6h sáng VN là 23h hôm trước theo UTC.
- Cách làm đúng:
  - Lọc một ngày: tính khoảng UTC ở app rồi viết `WHERE created_at >= ? AND created_at < ?`. Cách
    này dùng được index.
  - Gom nhóm theo ngày: đổi timezone trong query bằng `CONVERT_TZ` (MySQL, muốn dùng tên vùng thì
    phải nạp bảng timezone vào MySQL trước) hoặc `AT TIME ZONE` (Postgres).
  - Báo cáo lớn: lưu thêm cột `local_date` lúc ghi dữ liệu.
- Dùng khoảng *nửa mở* `[start, end)`. Không dùng `BETWEEN '... 00:00:00' AND '... 23:59:59'` vì
  sót các giá trị có phần lẻ giây như `23:59:59.500`.

**Đọc**
- MySQL: [DATETIME, DATE, TIMESTAMP](https://dev.mysql.com/doc/refman/8.4/en/datetime.html), [Time Zone Support](https://dev.mysql.com/doc/refman/8.4/en/time-zone-support.html) (mục nạp bảng timezone, `time_zone` per session), [Date and Time Functions](https://dev.mysql.com/doc/refman/8.4/en/date-and-time-functions.html) (`CONVERT_TZ`)
- Postgres: [Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html) (mục 8.5.1.3 và 8.5.3 time zones)
- [IANA Time Zone Database](https://www.iana.org/time-zones)
- Laravel: [Scheduling: Timezones](https://laravel.com/docs/scheduling#timezones)

**Nắm chắc khi**
- [ ] Viết được query doanh thu theo ngày giờ VN trên cột UTC, dùng được index (bài tập 2)
- [ ] Giải thích được bug "lệch 7 tiếng" xảy ra ở đâu giữa PHP, MySQL session và cột dữ liệu
- [ ] Lên lịch được job "8h sáng giờ của từng user" cho khách ở Sydney, chạy đúng qua ngày đổi giờ

#### 2.2 Tiền: làm tròn, đa tiền tệ, chia tiền

**Vì sao cần học:** Làm tròn và chia tiền là nơi các hệ thống thương mại điện tử, ví điện tử hay
lệch một vài đồng khi đối soát. Mỗi đồng lệch đều phải giải trình với kế toán. Người phỏng vấn
hay hỏi "chia 100.000đ cho 3 người thế nào" hoặc "phân bổ giảm giá cho từng dòng hàng".

**Học gì**

*Kiểu làm tròn*
- *Half-up*: `.5` làm tròn lên. 2,5 → 3, 3,5 → 4.
- *Half-even* (còn gọi *banker's rounding*): `.5` làm tròn về số chẵn gần nhất. 2,5 → 2, 3,5 → 4.
  - Vì sao có: làm tròn half-up luôn đẩy lên, cộng nhiều số thì lệch tích luỹ về một phía.
    Half-even lúc lên lúc xuống nên sai lệch tích luỹ nhỏ hơn.
- Dùng kiểu nào là do nghiệp vụ và luật thuế quyết định, không phải dev tự chọn.

*Làm tròn ở đâu*
- Làm tròn **ở bước nào** quan trọng không kém làm tròn thế nào.
  - Ví dụ: tính thuế cho từng dòng rồi làm tròn rồi cộng lại, khác với cộng tổng rồi mới tính thuế
    và làm tròn. Hai cách có thể lệch vài đồng.
- Quy tắc:
  - Chốt cách làm với kế toán.
  - Làm tròn ở **một chỗ** trong code.
  - Lưu giá trị **đã làm tròn**, không tính lại mỗi lần hiển thị.

*Đa tiền tệ*
- Với giao dịch có quy đổi, lưu đủ bốn thứ:
  - Số tiền gốc của giao dịch (kèm tiền tệ).
  - Số tiền sau quy đổi.
  - Tỷ giá đã dùng.
  - Thời điểm lấy tỷ giá.
- ⚠️ Không quy đổi lại theo tỷ giá hôm nay khi xem đơn cũ. Đơn đã chốt theo tỷ giá lúc đặt.
- Pattern `Money(amount, currency)`: một object gồm số tiền và tiền tệ, từ chối cộng hai số khác
  tiền tệ.
- Nguồn tỷ giá và *spread* (chênh lệch giữa giá mua và giá bán) là quyết định nghiệp vụ.

*Chia tiền không mất đồng lẻ*
- Ví dụ: 100.000đ chia 3 phần. Chia đều ra 33.333,33 không trả được. Làm như sau:
  1. Chia lấy phần nguyên: mỗi phần 33.333, tổng 99.999.
  2. Còn dư 1 đồng, cộng vào một phần.
  3. Kết quả `33.334 + 33.333 + 33.333` = 100.000.
- Chia theo tỷ lệ (ví dụ 50% / 30% / 20%) thì dùng thuật toán *largest remainder*: phần nào có phần
  dư lớn nhất được nhận đồng lẻ trước.
- Bất biến phải giữ: **tổng các phần bằng đúng tổng ban đầu**. Viết assert hoặc test cho bất biến
  này.
- Áp dụng:
  - Phân bổ giảm giá của cả đơn xuống từng dòng hàng.
  - Hoàn tiền một phần.
  - Chia hoa hồng.
- ⚠️ Lưu số đã phân bổ lúc đặt hàng. Khi hoàn tiền thì hoàn theo số đã lưu, không tính lại.

*Đối chiếu Java/Go/JS*
- Java `BigDecimal`:
  - ⚠️ `new BigDecimal(0.1)` mang theo sai số của double. Dùng `BigDecimal.valueOf(0.1)` hoặc
    `new BigDecimal("0.1")`.
  - ⚠️ `equals` so sánh cả *scale* (số chữ số thập phân): `2.0` khác `2.00`. So sánh giá trị thì
    dùng `compareTo`.
  - `setScale` phải truyền `RoundingMode`.
- Go không có kiểu decimal trong thư viện chuẩn. Dùng `shopspring/decimal` hoặc số nguyên.
- JS `toFixed` dựa trên double nên cũng có sai số.

**Đọc**
- [moneyphp/money](https://github.com/moneyphp/money) (README, mục allocation): đọc để thấy thư viện giải bài chia tiền thế nào, kể cả khi không dùng
- Martin Fowler: [Money](https://martinfowler.com/eaaCatalog/money.html) (phần allocate)

**Nắm chắc khi**
- [ ] Viết được `allocate(amount, ratios)` có test bất biến tổng (bài tập 1)
- [ ] Tính được thuế VAT cho đơn 3 dòng theo hai cách làm tròn và chỉ ra chênh lệch

#### 2.3 Unicode và tiếng Việt

**Vì sao cần học:** Tiếng Việt có dấu làm mọi chuyện so sánh, tìm kiếm, sắp xếp chuỗi phức tạp
hơn tiếng Anh nhiều. Bug hay gặp: không đăng ký được username vì "trùng" với một tên khác dấu,
tìm "Huệ" không ra dù dữ liệu có, tên file upload từ Mac không khớp. Người phỏng vấn ở công ty
Việt hay hỏi "làm tìm kiếm không dấu thế nào".

**Học gì**

*Collation*
- *Collation* là bộ luật so sánh và sắp xếp chuỗi. MySQL 8.4 mặc định `utf8mb4_0900_ai_ci`:
  - `ai` (accent-insensitive): không phân biệt dấu.
  - `ci` (case-insensitive): không phân biệt hoa thường.
- ⚠️ Hệ quả:
  - `'Nguyễn' = 'nguyen'` cho ra đúng.
  - Unique index trên `username` coi `"hoà"` và `"hoa"` là trùng, nên người thứ hai không đăng ký
    được.
  - `WHERE name = 'Lê'` trả về cả `"Le"`.
- Cột cần khớp chính xác (mã giảm giá, token, hash) thì dùng collation `_bin` hoặc `_as_cs`.
- Đối chiếu Postgres: mặc định **phân biệt** hoa thường. Muốn so sánh không phân biệt thì có ba
  cách:
  - `lower(col)` kèm index trên biểu thức `lower(col)`.
  - Kiểu `citext` (chuỗi không phân biệt hoa thường).
  - ICU *nondeterministic collation*: collation cho phép hai chuỗi khác byte vẫn được coi là bằng.
- Chuyển sang `utf8mb4` làm tăng số byte tối đa mỗi ký tự lên 4. InnoDB (row format `DYNAMIC`, mặc
  định) giới hạn key của index 3072 byte, nên cột index đầy đủ tối đa là `VARCHAR(768)` utf8mb4.

*Unicode normalization*
- ⚠️ Cùng một chữ `"ệ"` có thể được lưu theo hai cách:
  - *NFC* (dạng dựng sẵn): một code point U+1EC7.
  - *NFD* (dạng tách rời): `e` + U+0323 (dấu nặng) + U+0302 (dấu mũ), ba code point.
- Hai dạng nhìn giống hệt nhau, nhưng so sánh byte thì khác, độ dài cũng khác. Hệ quả: tìm không
  ra, unique không chặn được trùng, hash khác nhau.
- Nguồn hay sinh ra NFD:
  - Tên file từ macOS.
  - Văn bản copy từ một số trình soạn thảo hoặc bộ gõ.
  - Dữ liệu import từ hệ thống khác.
- Cách làm: chuẩn hoá về **NFC** ngay tại ranh giới nhập liệu, trước khi lưu, so sánh, hash, hay
  tạo unique key.

*Kiểu đặt dấu*
- ⚠️ Tiếng Việt có hai kiểu đặt dấu: kiểu cũ `hòa` (dấu trên `o`) và kiểu mới `hoà` (dấu trên
  `a`). Đây là **các code point khác nhau**, và NFC **không** gộp chúng.
- Cần coi hai kiểu là một thì phải tự chuẩn hoá theo một quy tắc đặt dấu, hoặc so sánh trên dạng
  đã bỏ dấu.

*Tìm kiếm không dấu*
- Bỏ dấu: chuyển về NFD rồi bỏ các *combining mark* (các code point dấu đứng sau chữ cái).
  - ⚠️ `đ`/`Đ` không tách được thành `d` + dấu, phải map tay.
- Cách lưu để tìm:
  - Thêm cột `name_search` chứa chuỗi đã bỏ dấu + chữ thường, có index.
  - Hoặc dựa vào collation `ai_ci` của MySQL.
- Full-text search:
  - Postgres: extension `unaccent` (bỏ dấu) + `pg_trgm` (tìm theo cụm 3 ký tự).
  - Elasticsearch: filter `asciifolding` ([04-nosql-search-storage.md](04-nosql-search-storage.md)).
  - Tiếng Việt tách từ theo âm tiết, nên cụm nhiều âm tiết ("thành phố") cần *phrase query* hoặc
    *tokenizer* (bộ tách từ) riêng cho tiếng Việt.

*Cắt chuỗi và đếm độ dài*
- ⚠️ `substr` của PHP cắt theo byte. Cắt giữa một chữ có dấu (2–3 byte) là ra UTF-8 không hợp lệ,
  và `json_encode` báo lỗi khi gặp chuỗi đó.
- Đối chiếu cách đếm độ dài:

| Ngôn ngữ | Hàm | Đếm gì |
|---|---|---|
| Go | `len(s)` | byte |
| Go | `utf8.RuneCountInString(s)` | rune (code point) |
| Java | `String.length()` | UTF-16 code unit: emoji ngoài BMP tính là 2 |

**Đọc**
- [UAX #15: Unicode Normalization Forms](https://unicode.org/reports/tr15/) (mục 1, hình ví dụ canonical equivalence)
- [UAX #29: Text Segmentation](https://unicode.org/reports/tr29/) (mục grapheme cluster boundaries)
- MySQL: [Unicode Character Sets](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-sets.html) (mục collation `_0900_`, pad attribute)
- Postgres: [unaccent](https://www.postgresql.org/docs/current/unaccent.html)

**Nắm chắc khi**
- [ ] Tạo được hai chuỗi "Huệ" NFC và NFD, chứng minh chúng khác nhau khi so sánh byte và bằng nhau sau khi chuẩn hoá
- [ ] Giải thích được vì sao unique index trên `username` với `utf8mb4_0900_ai_ci` có thể chặn đăng ký hợp lệ, và sửa thế nào
- [ ] Viết được hàm chuẩn hoá chuỗi tìm kiếm tiếng Việt (bài tập 3)

#### 2.4 Số và ID

**Vì sao cần học:** Kiểu ID chọn lúc tạo bảng gần như không đổi được về sau, và nó ảnh hưởng tới
tốc độ insert, bảo mật URL, và việc sinh ID ở nhiều service. Tràn số thì âm thầm cho tới một
ngày insert bị lỗi. Câu "auto-increment hay UUID" là câu thảo luận rất phổ biến.

**Học gì**

*Integer overflow*
- *Overflow* (tràn số) xảy ra khi giá trị vượt giới hạn của kiểu. `INT` có dấu tối đa khoảng 2,1
  tỷ.
- Các cột có thể chạm tới: id auto-increment, bảng log/event, bộ đếm.
- Phòng: dùng `BIGINT` cho id của bảng lớn, và theo dõi phần trăm đã dùng của auto-increment.
- ⚠️ Đổi kiểu cột id trên bảng lớn là migration rất nặng ([03-database-sql.md](03-database-sql.md)).
- Mỗi ngôn ngữ xử lý tràn khác nhau:
  - Java `int` tràn âm thầm thành số âm. Dùng `Math.addExact` để phát hiện.
  - Go *wraparound* (quay vòng về giá trị nhỏ nhất).
  - ⚠️ PHP tự chuyển sang float khi vượt `PHP_INT_MAX`, mất chính xác mà không báo lỗi.

*ID lớn trong JSON*
- JavaScript lưu mọi số dạng double, chỉ chính xác tới `2^53 - 1`. Số int64 lớn hơn bị làm tròn
  khi `JSON.parse`.
- Cách làm: trả ID lớn dạng string trong JSON ([09-api-design.md](09-api-design.md)).

*Các kiểu ID*

| Kiểu | Kích thước | Ưu | Nhược |
|---|---|---|---|
| Auto-increment | 4–8 byte, có thứ tự | Nhỏ, index tốt | Lộ số lượng, đoán được, khó sinh ở nhiều nơi |
| UUIDv4 | 16 byte, ngẫu nhiên | Sinh ở đâu cũng được | Chèn ngẫu nhiên vào B+tree gây *page split* (nặng với clustered index InnoDB) |
| UUIDv7 (RFC 9562) | 16 byte, theo thời gian | Sinh phân tán, chèn gần tuần tự | Lộ thời điểm tạo |
| ULID | 16 byte, 26 ký tự Crockford base32 | Như UUIDv7, chuỗi ngắn hơn | Như UUIDv7 |
| Snowflake | 8 byte | Nhỏ, có thứ tự | Cần machine id; ⚠️ đồng hồ lùi sinh trùng; vượt `2^53` trong JS |

- *Page split*: khi chèn vào giữa một page B+tree đã đầy, DB phải tách page làm hai. Trong InnoDB,
  bảng chính là một B+tree sắp theo khoá chính (*clustered index*), nên khoá chính là UUIDv4 ngẫu
  nhiên thì gần như lần chèn nào cũng rơi vào giữa (chi tiết ở [03-database-sql.md](03-database-sql.md)).
- Lưu UUID bằng `BINARY(16)` (MySQL) hoặc kiểu `uuid` (Postgres), không dùng `CHAR(36)` vì tốn
  gấp đôi và index to hơn.

*ID lộ ra ngoài*
- ⚠️ Auto-increment trong URL (`/orders/10523`):
  - Đối thủ đếm được số đơn mỗi ngày bằng cách đặt hai đơn cách nhau một ngày.
  - Kẻ xấu duyệt lần lượt từng id để xem dữ liệu người khác, nếu thiếu kiểm tra quyền. Lỗi này gọi
    là *IDOR* ([10-security.md](10-security.md)).
- Cách làm phổ biến: tách ba loại id.
  - `BIGINT` auto-increment làm khoá chính nội bộ, dùng để join.
  - Cột `public_id` (UUID/ULID) để lộ ra API.
  - Mã hiển thị cho người đọc (`DH-260923-4821`) là một cột riêng nữa.

**Đọc**
- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) (UUID): mục 5.7 UUIDv7 và mục 6 best practices
- MySQL: [Integer Types](https://dev.mysql.com/doc/refman/8.4/en/integer-types.html)
- PHP: [ramsey/uuid](https://github.com/ramsey/uuid) (UUIDv7); Laravel có `HasUuids`/`HasUlids` cho model

**Nắm chắc khi**
- [ ] Chọn và bảo vệ được kiểu ID cho bảng `orders` sinh từ nhiều service, lộ ra API công khai
- [ ] Tính được bảng `INT` nhận 500 insert/giây thì bao lâu hết id

#### 2.5 File: upload, import, export

**Vì sao cần học:** Import sản phẩm từ Excel, export báo cáo, upload ảnh là tính năng có ở hầu
hết app nội bộ và thương mại điện tử. Làm ngây thơ thì PHP hết `memory_limit`, request timeout,
dữ liệu Excel bị méo, và file export còn có thể thành công cụ tấn công. Phỏng vấn hay yêu cầu
thiết kế luồng import file lớn.

**Học gì**

*Upload file lớn*
- File lớn không nên đi qua app server. Ba cách:
  - *Presigned URL*: server tạo một URL có chữ ký và hạn dùng, client upload thẳng lên storage
    (S3...) bằng URL đó.
  - *Multipart upload*: chia file thành nhiều phần, upload từng phần, cuối cùng ghép lại.
  - Giao thức *resumable* như tus: upload đứt thì tiếp tục từ chỗ dừng.
- ⚠️ Multipart upload dở dang (không ghép xong) vẫn nằm trên storage và vẫn tính tiền. Cần
  *lifecycle rule* tự dọn ([04-nosql-search-storage.md](04-nosql-search-storage.md)).
- Nếu phải đi qua app server:
  - Giới hạn ở các tầng phải khớp nhau: Nginx `client_max_body_size`, PHP `upload_max_filesize` và
    `post_max_size`, rồi giới hạn của framework.
  - Stream thẳng xuống storage, không đọc cả file vào RAM.

*Kiểm tra file*
- Kiểm tra loại file thật bằng *magic bytes* (vài byte đầu file cho biết định dạng): PHP `finfo`,
  Go `http.DetectContentType`. Không tin đuôi file.
- Kiểm tra kích thước, số trang (PDF), kích thước ảnh.
- Đổi tên file khi lưu, không dùng tên client gửi lên ([10-security.md](10-security.md)).
- Xử lý ảnh/video chạy async, với trạng thái `processing` → `ready` hoặc `failed`.
- ⚠️ Giới hạn kích thước pixel **trước khi** decode ảnh. Một ảnh 50000×50000 có thể chỉ vài trăm
  KB trên đĩa nhưng decode ra cần hàng GB RAM.

*Import CSV/Excel lớn*
- Luồng chuẩn:
  1. Nhận file, lưu vào storage.
  2. Tạo job import, trả `202 Accepted` kèm id của job ([09-api-design.md](09-api-design.md)).
  3. Worker đọc file **streaming** từng dòng, không load cả file.
  4. Xử lý theo *chunk* vài trăm tới vài nghìn dòng, mỗi chunk một transaction ngắn.
  5. Cập nhật tiến độ `processed_rows/total_rows`, client poll để hiển thị.
- ⚠️ Nhiều thư viện Excel mặc định load cả workbook vào RAM (module 2.7).
- Validate:
  - Validate từng dòng, **thu lỗi** theo số dòng thay vì dừng ở lỗi đầu tiên.
  - Cho người dùng tải về file các dòng lỗi.
  - Quy định rõ trước: có dòng lỗi thì bỏ dòng đó hay huỷ cả file.
- Chạy lại an toàn (idempotent):
  - Nhận diện file bằng hash nội dung hoặc import id.
  - *Upsert* (có thì cập nhật, chưa có thì thêm) theo *khoá tự nhiên* như mã SKU, để chạy lại không
    tạo bản ghi trùng.
- ⚠️ Excel tự đổi dữ liệu khi người dùng mở và lưu lại:
  - Số điện thoại mất số 0 đầu: `0912345678` thành `912345678`.
  - Mã dài thành dạng khoa học: `1.23E+15`.
  - Chuỗi trông giống ngày thành ngày.
  - Cách làm: đọc cell dạng text và chuẩn hoá lại.

*Export lớn*
- Luồng: chạy job nền → stream dữ liệu từ DB (cursor hoặc chunk, không `->get()` cả bảng) → ghi
  file → upload storage → gửi link tải có hạn.
- File `.xlsx` giới hạn 1.048.576 dòng mỗi sheet.
- ⚠️ *BOM* (Byte Order Mark) là 3 byte `EF BB BF` đặt đầu file để báo "đây là UTF-8".
  - Excel trên Windows mở CSV UTF-8 **không** có BOM thường hiện tiếng Việt thành ký tự rác. Khi
    file dành cho Excel thì ghi BOM ở đầu.
  - Khi **đọc** CSV thì phải bỏ BOM, không thì tên cột đầu tiên dính ký tự lạ và không khớp.

*CSV injection*
- ⚠️ *CSV injection*: ô bắt đầu bằng `=`, `+`, `-`, `@`, tab (`\t`, 0x09), CR (`\r`, 0x0D) hoặc LF
  (0x0A) có thể bị Excel/LibreOffice hiểu là **công thức** và thực thi khi người dùng mở file.
  - Ví dụ: khách đặt tên là `=HYPERLINK("http://evil.example","Bấm vào")`, admin export danh sách
    khách và mở bằng Excel.
- Cách phòng với ô chứa dữ liệu người dùng nhập:
  - Bọc ô trong nháy kép, escape nháy kép bên trong.
  - Thêm `'` phía trước ô bắt đầu bằng ký tự nguy hiểm.
- ⚠️ Không chỉ kiểm tra ký tự đầu chuỗi. Kẻ tấn công có thể chèn dấu phân cách (`,`, `;`) hoặc
  nháy để mở một ô mới giữa chuỗi.
- Không có cách sanitize nào an toàn cho mọi phần mềm bảng tính. Mặt khác, file để máy đọc tiếp mà
  bị thêm `'` thì dữ liệu bị bẩn. Vì vậy tách hai loại: "export để xem" và "export để import".

**Đọc**
- OWASP: [CSV Injection](https://owasp.org/www-community/attacks/CSV_Injection) (đọc hết, ngắn), [File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [tus.io](https://tus.io/) (giao thức resumable upload)

**Nắm chắc khi**
- [ ] Thiết kế được luồng import sản phẩm từ Excel: bảng job, bảng lỗi theo dòng, chạy lại an toàn, tiến độ (bài tập 5)
- [ ] Tạo được một file CSV chứa payload injection và chứng minh hàm export của mình vô hiệu hoá được nó
- [ ] Giải thích được vì sao cùng một file CSV mở bằng Excel ra rác, mở bằng VS Code thì đúng

#### 2.6 Email, SMS, OTP

**Vì sao cần học:** Email xác nhận vào spam, OTP không tới, hoá đơn SMS tăng vọt vì bot là ba sự
cố hay gặp khi app bắt đầu có nhiều người dùng. Từ 2024 các nhà cung cấp mail lớn đã siết điều
kiện gửi, nên cấu hình DNS cho mail không còn là việc "để sau". Thiết kế endpoint gửi OTP là câu
hỏi thiết kế hay gặp.

**Học gì**

*SPF, DKIM, DMARC*
- Ba bản ghi DNS giúp bên nhận tin mail thật sự đến từ domain của bạn:
  - *SPF*: bản ghi TXT liệt kê những server được phép gửi mail cho domain.
    - ⚠️ SPF giới hạn 10 lần tra DNS lồng nhau (mỗi `include` là một lần). Vượt thì SPF fail.
  - *DKIM*: server gửi ký header và body của mail bằng private key. Public key đặt ở bản ghi
    `selector._domainkey.domain` để bên nhận kiểm tra chữ ký.
  - *DMARC*: chính sách xử lý khi SPF/DKIM fail, hoặc khi domain đã xác thực không khớp với domain
    ở dòng `From` (yêu cầu khớp này gọi là *alignment*).
    - Các mức: `p=none` (chỉ theo dõi) → `quarantine` (cho vào spam) → `reject` (từ chối).
    - `rua` là địa chỉ nhận báo cáo tổng hợp.
    - Bắt đầu bằng `none` để quan sát trước khi siết.
- Từ 02/2024, Gmail và Yahoo yêu cầu người gửi số lượng lớn phải có:
  - SPF, DKIM, DMARC.
  - Unsubscribe một chạm.
  - Tỉ lệ bị báo spam thấp.

*Vận hành gửi mail*
- Tách domain hoặc subdomain cho mail giao dịch (đơn hàng, OTP) và mail marketing. Mail marketing
  bị báo spam không kéo mail giao dịch vào spam theo.
- *Bounce*: mail bị trả lại. *Hard bounce* (địa chỉ không tồn tại) thì ngừng gửi hẳn tới địa chỉ
  đó.
- *Complaint*: người nhận bấm "báo spam". Coi như huỷ đăng ký.
- Nhận bounce và complaint qua webhook của nhà cung cấp (SES, SendGrid, Mailgun), lưu vào
  *suppression list* (danh sách không được gửi nữa).

*OTP*
- *OTP* (one-time password) là mã dùng một lần. Các yêu cầu:
  - Sinh bằng *CSPRNG* (bộ sinh số ngẫu nhiên an toàn cho mật mã, PHP `random_int`), 6 chữ số.
  - Lưu **hash** của OTP, không lưu mã gốc.
  - Hết hạn sau vài phút.
  - Dùng một lần.
  - Gắn với mục đích: OTP cho đăng nhập không dùng được để đổi số điện thoại.
- Chống *brute force* (thử lần lượt mọi mã):
  - Giới hạn số lần nhập sai cho mỗi OTP.
  - Giới hạn số lần gửi theo số điện thoại, IP, thiết bị.
  - Thời gian chờ trước khi được gửi lại.
- ⚠️ *SMS pumping*: bot gọi endpoint gửi OTP tới các số premium hoặc số quốc tế, để ăn chia cước
  với nhà mạng. Bạn trả tiền SMS.
  - Giới hạn quốc gia được gửi.
  - CAPTCHA trước khi gửi.
  - Cảnh báo khi chi phí SMS tăng đột biến.

*SMS ở Việt Nam*
- SMS thường gửi qua *brandname* (tên người gửi) đăng ký với nhà mạng, nội dung phải theo mẫu đã
  đăng ký.
- Nhà cung cấp có thể chậm hoặc rớt tin, nên cần kênh dự phòng: Zalo ZNS, email, voice OTP.

**Đọc**
- [DMARC overview](https://dmarc.org/overview/)
- Google: [Email sender guidelines](https://support.google.com/a/answer/81126)
- OTP và xác thực: [10-security.md](10-security.md)

**Nắm chắc khi**
- [ ] Đọc được bản ghi SPF/DKIM/DMARC thật của một domain (`dig TXT`) và giải thích từng phần
- [ ] Thiết kế được endpoint gửi OTP chịu được bot SMS pumping, liệt kê mọi giới hạn

#### 2.7 Tầng PHP: thời gian, tiền, chuỗi, file lớn

**Vì sao cần học:** Đây là module riêng cho người làm PHP. Phần lớn bug "đời thường" trong PHP
đến từ hàm mặc định không làm điều mình nghĩ: `DateTime` bị sửa ngầm, `round` không phải half-even,
`strtolower` làm hỏng tiếng Việt, PhpSpreadsheet ngốn hết RAM. Biết đúng công cụ là câu trả lời
mà người phỏng vấn PHP muốn nghe.

**Học gì**

*Thời gian*
- Dùng `DateTimeImmutable` + `DateTimeZone`. Tránh `DateTime` vì nó *mutable* (bị sửa tại chỗ):

  ```php
  $start = new DateTime('2026-09-23');
  $end = $start->modify('+1 day');   // SAI: $start cũng bị đổi thành 24/09

  $start = new DateTimeImmutable('2026-09-23');
  $end = $start->modify('+1 day');   // ĐÚNG: trả object mới, $start giữ nguyên
  ```
- Carbon thì dùng `CarbonImmutable`. Laravel có cast `immutable_datetime` và
  `Date::use(CarbonImmutable::class)` để mặc định dùng bản immutable.
- Ba nơi đặt timezone phải thống nhất:
  1. `php.ini` `date.timezone` (mặc định `UTC`).
  2. `config/app.php` `timezone`: Laravel gọi `date_default_timezone_set`, ghi đè php.ini.
  3. `time_zone` của session MySQL: Laravel đặt khi có `'timezone' => '+00:00'` trong cấu hình
     connection.
- ⚠️ Hai kịch bản của bug lệch 7 tiếng:
  - App đặt `Asia/Ho_Chi_Minh` và ghi giờ địa phương vào cột `DATETIME`, trong khi job hay service
    khác ghi UTC vào cùng cột.
  - Cột `TIMESTAMP`, nhưng session timezone của web và của worker khác nhau.
- Laravel serialize ngày ra JSON dạng ISO 8601 UTC (`...Z`). Đổi bằng `serializeDate` nếu thật
  cần.
- Đo khoảng thời gian bằng `hrtime(true)` (monotonic clock, module 2.1). Không dùng `microtime` vì
  nó là wall clock.

*Tiền*
- PDO trả cột `DECIMAL` dạng **string**. ⚠️ Đừng ép `(float)`, vì làm vậy là quay lại float.
- `bcmath`: các hàm tính trên string, tự chỉ định *scale* (số chữ số thập phân).
  - PHP 8.4 có thêm `BcMath\Number` (object, dùng được toán tử `+ - * /`) và `bcround`, `bcfloor`,
    `bcceil`.
- Thư viện [brick/money](https://github.com/brick/money) hoặc [moneyphp/money](https://github.com/moneyphp/money):
  object `Money` kèm tiền tệ, có allocate, làm tròn tường minh.
- ⚠️ `round()` mặc định là *half away from zero* (`.5` làm tròn ra xa số 0), không phải half-even.
  PHP 8.4 thêm enum `RoundingMode`, có `HalfEven`.
- Laravel:
  - Cast `decimal:2` trả về string.
  - `Number::currency()`, `Number::format()` để hiển thị theo locale.

*Chuỗi*
- Ba hàm đếm độ dài theo ba đơn vị (module 1.3):
  - `strlen` đếm byte.
  - `mb_strlen` đếm code point.
  - `grapheme_strlen` đếm grapheme.
- ⚠️ `substr`, `strtolower`, `ucfirst` làm việc trên byte nên làm vỡ hoặc bỏ sót chữ tiếng Việt.
  Dùng `mb_substr`, `mb_strtolower`. PHP 8.4 có thêm `mb_trim`, `mb_ucfirst`.
- Chuẩn hoá NFC: `Normalizer::normalize($s, Normalizer::FORM_C)` (cần ext-intl).
- Bỏ dấu:
  - `Transliterator::create('Any-Latin; Latin-ASCII; Lower()')`.
  - Hoặc Laravel `Str::ascii`, `Str::slug`.
  - ⚠️ Vẫn phải viết test với `đ`/`Đ` và với input dạng NFD.
- `NumberFormatter`, `IntlDateFormatter` để định dạng số và ngày theo locale.

*File lớn*
- Đọc CSV từng dòng bằng `fgetcsv` hoặc `SplFileObject` (flag `READ_CSV`).
- Bọc trong *generator* (hàm dùng `yield`, trả từng giá trị một khi được hỏi) để phía gọi xử lý
  từng dòng mà memory không tăng:

  ```php
  function readCsv(string $path): Generator {
      $f = new SplFileObject($path);
      $f->setFlags(SplFileObject::READ_CSV | SplFileObject::SKIP_EMPTY);
      foreach ($f as $row) {
          yield $row;               // mỗi lần chỉ giữ một dòng trong RAM
      }
  }
  ```
- ⚠️ PhpSpreadsheet load cả workbook, tốn khoảng 1 KB RAM mỗi cell. File 500.000 dòng × 20 cột có
  thể cần khoảng 10 GB.
  - Giảm bằng read filter, `setReadDataOnly`.
  - Hoặc dùng thư viện streaming như OpenSpout cho `.xlsx`.
- Laravel Excel (xây trên PhpSpreadsheet):
  - Import: `WithChunkReading` + `ShouldQueue` để đọc theo chunk trong queue, `WithBatchInserts`.
  - Export: `FromQuery` + queue.
- Export qua HTTP: `response()->streamDownload()` + `lazyById()` hoặc `cursor()`, ghi BOM khi cần.
  - ⚠️ FPM có `memory_limit` và `max_execution_time`, nên file lớn luôn chạy trong job.
- Kiểm tra MIME thật bằng `finfo`. Không tin `$_FILES['type']` (do client gửi) hay đuôi file.

*Đối chiếu Java/Go*

| Việc | Java | Go |
|---|---|---|
| Thời gian | `java.time`: `Instant`, `ZonedDateTime`, `LocalDate`. Tránh `java.util.Date` | `time.LoadLocation`. ⚠️ Layout định dạng viết bằng ngày mẫu `2006-01-02T15:04:05Z07:00` |
| Chuẩn hoá Unicode | `java.text.Normalizer` | `golang.org/x/text/unicode/norm` |
| File lớn | Apache POI streaming (SXSSF để ghi, SAX để đọc) | `encoding/csv` |

**Đọc**
- PHP:
  - [DateTimeImmutable](https://www.php.net/manual/en/class.datetimeimmutable.php), [Date/Time configuration](https://www.php.net/manual/en/datetime.configuration.php) (`date.timezone`), [hrtime](https://www.php.net/manual/en/function.hrtime.php)
  - [BCMath](https://www.php.net/manual/en/book.bc.php), [BcMath\Number](https://www.php.net/manual/en/class.bcmath-number.php), [round](https://www.php.net/manual/en/function.round.php), [RoundingMode](https://www.php.net/manual/en/enum.roundingmode.php)
  - [mbstring](https://www.php.net/manual/en/book.mbstring.php), [Normalizer](https://www.php.net/manual/en/class.normalizer.php), [Transliterator](https://www.php.net/manual/en/class.transliterator.php), [Grapheme functions](https://www.php.net/manual/en/ref.intl.grapheme.php), [NumberFormatter](https://www.php.net/manual/en/class.numberformatter.php)
  - [SplFileObject](https://www.php.net/manual/en/class.splfileobject.php), [fgetcsv](https://www.php.net/manual/en/function.fgetcsv.php), [Generators](https://www.php.net/manual/en/language.generators.overview.php), [Fileinfo](https://www.php.net/manual/en/book.fileinfo.php)
- [Carbon](https://carbon.nesbot.com/)
- Laravel: [Date Casting and Timezones](https://laravel.com/docs/eloquent-mutators#date-casting-and-timezones), [Date Serialization](https://laravel.com/docs/eloquent-serialization#date-serialization), [Streamed Downloads](https://laravel.com/docs/responses#streamed-downloads), [`Number::currency`](https://laravel.com/docs/helpers#method-number-currency), [`Str::ascii`](https://laravel.com/docs/strings#method-str-ascii)
- PhpSpreadsheet: [Memory saving](https://phpspreadsheet.readthedocs.io/en/latest/topics/memory_saving/); [OpenSpout](https://github.com/openspout/openspout); Laravel Excel: [Chunk reading](https://docs.laravel-excel.com/3.1/imports/chunk-reading.html), [Queued exports](https://docs.laravel-excel.com/3.1/exports/queued.html)

**Nắm chắc khi**
- [ ] Chỉ ra được 3 nơi đặt timezone trong app Laravel của mình và giá trị hiện tại của từng nơi
- [ ] Viết được hàm đọc CSV 1 triệu dòng bằng generator, đo memory trước và sau bằng `memory_get_peak_usage()`
- [ ] Viết được phép chia tiền và làm tròn half-even bằng `bcmath` hoặc brick/money, có test
- [ ] Giải thích được vì sao `strtoupper('việt')` và `mb_strtoupper('việt')` cho kết quả khác nhau

---

### Chặng 3: Senior 🔴

#### 3.1 Ledger và bút toán kép

**Vì sao cần học:** Ví điện tử, điểm thưởng, số dư tài khoản, công nợ đều cần một cách ghi tiền
mà kiểm tra lại được và không bao giờ "mất dấu" một đồng. Cách ngây thơ (một cột `balance` rồi
`UPDATE`) không trả lời được câu "vì sao số dư là con số này". Phỏng vấn senior ở công ty
fintech hay thương mại điện tử gần như chắc chắn hỏi thiết kế ví hoặc ledger.

**Học gì**

*Ledger: ghi giao dịch, không chỉ ghi số dư*
- ⚠️ Cách ngây thơ: một cột `balance`, mỗi lần trừ tiền thì `UPDATE balance = balance - x`. Khi
  số dư sai, không có cách nào biết sai từ đâu.
- *Ledger* (sổ cái): ghi **mỗi giao dịch** thành một *bút toán* (entry) bất biến, chỉ thêm vào
  không sửa (*append-only*).

*Bút toán kép*
- *Bút toán kép* (double-entry): mỗi giao dịch gồm ít nhất một dòng *ghi nợ* và một dòng *ghi có*,
  tổng hai bên bằng nhau.
  - Ví dụ: chuyển 100 từ A sang B sinh hai entry: A −100, B +100.
- Hệ quả: tổng mọi entry trong toàn hệ thống **luôn bằng 0**. Đây là *bất biến* (điều luôn phải
  đúng) để kiểm tra hệ thống còn đúng không.
- Nạp tiền từ ngoài vào thì bên kia là một tài khoản hệ thống (ví dụ "tiền nhận từ cổng thanh
  toán"), nên tổng vẫn bằng 0.

*Sửa sai*
- Sai thì **không sửa, không xoá** bút toán cũ.
- Thay vào đó:
  1. Ghi *bút toán đảo* (reversal) triệt tiêu bút toán sai.
  2. Ghi bút toán đúng.
- Nhờ vậy lịch sử luôn đầy đủ: nhìn vào là biết đã sai gì, sửa lúc nào.

*Số dư*
- Số dư = tổng các bút toán của tài khoản.
- Cộng lại mỗi lần thì chậm, nên có thể lưu *snapshot* (bản chụp) hoặc cache số dư:
  - Cập nhật snapshot **trong cùng transaction** với việc ghi bút toán.
  - Đối chiếu định kỳ snapshot với tổng bút toán. Lệch là có bug.

*Đồng thời và idempotency*
- Chống số dư âm khi hai lệnh trừ chạy cùng lúc ([13-concurrency.md](13-concurrency.md)):
  - `SELECT ... FOR UPDATE` để khoá dòng số dư trước khi kiểm tra.
  - Hoặc `UPDATE ... SET balance = balance - x WHERE id = ? AND balance >= x`, rồi kiểm tra số dòng
    bị ảnh hưởng. 0 dòng nghĩa là không đủ tiền.
- Idempotency cho **mọi** lệnh ghi tiền: đặt khoá duy nhất (unique) theo mã giao dịch nghiệp vụ.
  Lệnh bị gửi lại thì vướng unique, không ghi lần hai.

**Đọc**
- Modern Treasury: [Accounting for Developers, Part I](https://www.moderntreasury.com/journal/accounting-for-developers-part-i) (và các phần tiếp theo)
- Lock và lost update: [03-database-sql.md](03-database-sql.md) module 2.5–2.6

**Nắm chắc khi**
- [ ] Thiết kế được schema ví điện tử (accounts, transactions, entries) và viết được luồng chuyển tiền an toàn với đồng thời
- [ ] Viết được query kiểm tra bất biến "tổng bút toán bằng 0" và giải thích dùng nó khi nào

#### 3.2 Thanh toán qua cổng

**Vì sao cần học:** Tích hợp VNPay, Momo, Stripe là việc gần như mọi app bán hàng phải làm, và
lỗi ở đây là mất tiền thật: đơn chưa trả mà thành đã trả, khách bị trừ tiền hai lần, hoàn tiền
hai lần. Người phỏng vấn hay hỏi "vì sao không tin return URL" và "gọi cổng bị timeout thì làm
gì".

**Học gì**

*Luồng chung*
- VNPay, Momo, Stripe khác nhau về chi tiết, nhưng giống nhau về khái niệm:
  1. Client tạo đơn. Server tạo bản ghi payment trạng thái `pending` với một mã giao dịch duy nhất.
  2. Server tạo URL thanh toán có chữ ký, rồi redirect user sang trang của cổng.
  3. User trả tiền xong, cổng redirect trình duyệt về *return URL* của bạn. Chỉ dùng để **hiển
     thị** kết quả, không tin để cập nhật đơn.
  4. Cổng gọi *IPN*/*webhook* (lời gọi server-to-server từ cổng tới server của bạn). Server verify
     chữ ký rồi mới cập nhật đơn.
  5. Đối soát định kỳ với cổng.
- ⚠️ Vì sao không tin return URL: nó đi qua trình duyệt, nên user sửa được tham số, có thể đóng
  tab, hoặc rớt mạng trước khi tới. Nguồn sự thật là IPN/webhook và API tra cứu giao dịch của cổng.

*Xử lý IPN*
- Verify chữ ký:
  - Đúng thuật toán và đúng thứ tự tham số mà cổng quy định (thường là *HMAC*, chữ ký dùng khoá bí
    mật chung).
  - So sánh chữ ký bằng hàm *constant-time* (`hash_equals`), để kẻ tấn công không đoán được chữ ký
    qua thời gian phản hồi.
  - Kiểm tra **số tiền và mã đơn** khớp với đơn của mình, không chỉ kiểm tra chữ ký.
- IPN phải idempotent: cổng gửi lại cùng một IPN nhiều lần.
  - Đơn đã `paid` thì trả thành công luôn, không cộng tiền lần hai.
  - Trả đúng format response mà cổng yêu cầu, không thì cổng tưởng lỗi và gửi lại mãi.

*Timeout không rõ kết quả*
- ⚠️ Gọi cổng (thanh toán, hoàn tiền) bị timeout nghĩa là **không biết** bên kia đã trừ tiền hay
  chưa. Không coi là thất bại, không tạo giao dịch mới.
- Cách xử lý:
  1. Đặt trạng thái `unknown` hoặc `pending_confirmation`.
  2. Tra cứu giao dịch theo mã giao dịch, retry với backoff.
  3. Đồng thời chờ IPN.
  4. Nếu cần gọi lại lệnh gốc thì chỉ gọi với **cùng idempotency key**, để cổng nhận ra là lệnh cũ.
- User quay lại khi đơn đang `pending`: hiển thị "đang xác nhận", không cho thanh toán lần hai bằng
  mã giao dịch mới.

*Đối soát*
- *Đối soát* hằng ngày: so dữ liệu của mình với file hoặc API của cổng. Tìm ba loại lệch:
  - Lệch số tiền.
  - Có bên này mà không có bên kia.
  - Trạng thái khác nhau.
- Kết quả lệch phải có người xử lý. Chỉ ghi log thì không ai biết.

*Thiết kế cho nhiều cổng*
- Interface `PaymentGateway` với các method `createPayment`, `verifyCallback`, `query`, `refund`,
  mỗi cổng một adapter ([08-oop-design.md](08-oop-design.md)).
- Bảng `payments` tách khỏi `orders`, vì một đơn có thể có nhiều lần thử thanh toán.
- Lưu nguyên văn (*raw payload*) mọi IPN nhận được, để tra lại khi có tranh chấp.

**Đọc**
- Stripe: [Webhooks](https://docs.stripe.com/webhooks) (mục verify signature, retry, xử lý trùng), [Idempotent requests](https://docs.stripe.com/api/idempotent_requests)
- Brandur: [Implementing Stripe-like Idempotency Keys in Postgres](https://brandur.org/idempotency-keys): thiết kế idempotency key ở phía mình, áp dụng được cho MySQL
- Tài liệu tích hợp của cổng bạn đang dùng (VNPay, Momo): đọc mục IPN và API truy vấn giao dịch

**Nắm chắc khi**
- [ ] Vẽ được sequence diagram thanh toán có IPN đến trước return URL, IPN đến trễ, và IPN không bao giờ đến
- [ ] Xử lý được đúng kịch bản "gọi API hoàn tiền timeout, dev retry, khách được hoàn hai lần"

#### 3.3 State machine và audit trail

**Vì sao cần học:** Đơn hàng, thanh toán, vận chuyển, hoàn tiền đều là các trạng thái chuyển qua
lại. Không kiểm soát chuyển trạng thái thì sẽ có đơn đã huỷ bỗng thành đã trả, đơn đang giao bị
huỷ. Khi có tranh chấp, câu hỏi đầu tiên luôn là "ai đổi trạng thái, lúc nào, vì sao".

**Học gì**

*State machine*
- *State machine* (máy trạng thái): liệt kê mọi trạng thái và mọi **chuyển đổi hợp lệ** giữa
  chúng. Mọi thay đổi trạng thái đều đi qua **một hàm** kiểm tra chuyển đổi đó có hợp lệ không.
- Ví dụ với đơn hàng:
  - Luồng chính: `pending → paid → shipped → delivered`.
  - Nhánh: `pending → cancelled`, `paid → refunded`, `delivered → returned`.
- ⚠️ `UPDATE orders SET status = 'paid'` rải rác khắp code dẫn tới:
  - IPN đến trễ đưa đơn đã `cancelled` quay về `paid`.
  - Đơn đã `shipped` vẫn bị huỷ.

*Chuyển trạng thái nguyên tử*
- Kiểm tra và đổi trạng thái trong **một câu lệnh**, để hai request đồng thời không cùng qua được:

  ```sql
  UPDATE orders SET status = 'paid'
  WHERE id = ? AND status = 'pending';
  ```
- Kiểm tra số dòng bị ảnh hưởng. 0 dòng nghĩa là trạng thái không còn là `pending`, xử lý theo
  nghiệp vụ:
  - Đã `paid`: đây là IPN lặp lại, trả thành công (idempotent).
  - Đã `cancelled`: tiền đã về cho một đơn đã huỷ, cần hoàn tiền.
- "Đã huỷ nhưng tiền về" là chuyện có thật. State machine phải có nhánh cho nó.

*Cài đặt trong PHP*
- PHP 8.1+ có *enum*. Dùng enum cho trạng thái, kèm method `canTransitionTo()`.
- Laravel cast cột `status` thành enum.

*Audit trail*
- *Audit trail* là nhật ký mọi lần đổi trạng thái, để trả lời "ai đổi, lúc nào, vì sao"
  ([10-security.md](10-security.md)).
- Các cột: `order_id, from_status, to_status, actor, reason, created_at`, và payload khi cần.
  - `actor` là ai gây ra thay đổi: user, system, hay webhook.
- Bảng này append-only: chỉ thêm, không sửa, không xoá.

**Đọc**
- Laravel: [Enum Casting](https://laravel.com/docs/eloquent-mutators#enum-casting)
- Thiết kế pattern State: [08-oop-design.md](08-oop-design.md)

**Nắm chắc khi**
- [ ] Vẽ được state machine đơn hàng có thanh toán online với mọi nhánh bất thường (bài tập 4)
- [ ] Viết được hàm chuyển trạng thái an toàn khi hai IPN đến đồng thời

#### 3.4 i18n, soft delete, vệ sinh dữ liệu, cô lập môi trường

**Vì sao cần học:** Module gom các vấn đề "vệ sinh" mà dự án nào lớn lên cũng gặp: mở rộng sang
nước khác, xoá dữ liệu mà không làm vỡ báo cáo, dữ liệu rác tích tụ, và sự cố kinh hoàng nhất là
test xoá sạch database thật. Người phỏng vấn senior hay hỏi soft delete có vấn đề gì, và bạn đã
từng chặn sự cố môi trường thế nào.

**Học gì**

*i18n và l10n*
- *i18n* (internationalization): chuẩn bị code để hỗ trợ nhiều ngôn ngữ và vùng.
- *l10n* (localization): làm cho một vùng cụ thể, ví dụ dịch sang tiếng Nhật, định dạng tiền yên.
- Chuỗi hiển thị:
  - Lấy từ file dịch theo key, không viết cứng trong code.
  - Quy tắc số nhiều (*plural rules*) khác nhau giữa các ngôn ngữ: tiếng Anh có "1 item / 2 items",
    tiếng Việt không đổi.
  - Chuỗi có tham số (`:name đã đặt :count đơn`).
- Số theo locale: `1.234.567,5` (vi-VN) và `1,234,567.5` (en-US).
  - ⚠️ Parse số người dùng nhập theo sai locale là lệch 1000 lần: `1.234` là một nghìn hai trăm ba
    mươi tư theo vi-VN, nhưng là một phẩy hai theo en-US.
- Ngày: định dạng theo locale ở tầng hiển thị. API luôn dùng ISO 8601.
- Sắp xếp tên tiếng Việt cần collation đúng locale.
- Nội dung đa ngôn ngữ trong DB (tên sản phẩm, mô tả):
  - Bảng translation riêng, hoặc cột JSON theo locale.
  - Có *fallback*: thiếu bản dịch thì dùng ngôn ngữ mặc định.

*Soft delete*
- *Soft delete*: không xoá dòng, mà đặt cột `deleted_at`. Laravel có trait `SoftDeletes`.
- Lợi:
  - Khôi phục được khi xoá nhầm.
  - Giữ được tham chiếu lịch sử (đơn cũ vẫn trỏ tới sản phẩm đã "xoá").
- ⚠️ Hại:
  - Mọi query phải lọc `deleted_at IS NULL`. Eloquent tự lọc, nhưng hay quên ở raw query, report,
    join.
  - Unique index bị ảnh hưởng: email đã "xoá" vẫn chặn người mới đăng ký email đó. Postgres dùng
    *partial unique index* (unique chỉ trên các dòng chưa xoá). MySQL không có partial index nên
    dùng generated column ([03-database-sql.md](03-database-sql.md) module 2.8).
  - Bảng phình to theo thời gian.
  - Dữ liệu cá nhân "đã xoá" vẫn còn, vướng yêu cầu xoá dữ liệu theo luật
    ([10-security.md](10-security.md)).
- Thay thế:
  - Chuyển sang bảng archive.
  - Hoặc dùng trạng thái nghiệp vụ rõ ràng: `archived`, `deactivated`.

*Dữ liệu mồ côi*
- *Dữ liệu mồ côi* là dữ liệu còn lại khi thứ nó thuộc về đã bị xoá:
  - Xoá bản ghi cha mà bản ghi con còn.
  - File trên storage không còn bản ghi nào trỏ tới.
  - Key cache, document trong search index của bản ghi đã xoá.
- Cách chống:
  - Foreign key với hành vi khi xoá được khai rõ ràng (`CASCADE`, `RESTRICT`...).
  - Xoá theo đúng thứ tự trong transaction.
  - Job dọn định kỳ.
  - Query kiểm tra toàn vẹn chạy định kỳ.

*Dữ liệu test trên production*
- ⚠️ Tài khoản test trên production làm sai báo cáo doanh thu, nhận email marketing, dính vào đối
  soát với cổng thanh toán.
- Cách làm:
  - Đánh dấu bằng cột `is_test`.
  - Loại khỏi báo cáo.
  - Dùng cổng thanh toán sandbox cho các tài khoản đó.

*Cô lập môi trường test*
- ⚠️ Môi trường test dùng chung DB với người khác: `RefreshDatabase`, `migrate:fresh`, hay
  `TRUNCATE` trong setup của test có thể **xoá sạch DB của cả team**, hoặc tệ hơn là DB thật.
- Cách cô lập:
  - DB riêng cho test, cấu hình trong `phpunit.xml` hoặc `.env.testing`.
  - Container DB tạm, tạo mới cho mỗi lần chạy (Testcontainers).
  - Mỗi test chạy trong một transaction và rollback khi xong.
- Rào chắn phòng khi cấu hình sai ([20-testing-quality.md](20-testing-quality.md)):
  - Test từ chối chạy nếu tên DB không có hậu tố `_test`.
  - Tài khoản DB của test không có quyền trên DB khác.
  - Credential production không bao giờ có trên máy dev.

**Đọc**
- Laravel: [Soft Deleting](https://laravel.com/docs/eloquent#soft-deleting), [Pluralization](https://laravel.com/docs/localization#pluralization), [Environment Configuration](https://laravel.com/docs/configuration#environment-configuration)
- PHP: [NumberFormatter](https://www.php.net/manual/en/class.numberformatter.php) (parse và format theo locale)

**Nắm chắc khi**
- [ ] Viết được guard trong `TestCase` từ chối chạy khi DB không phải DB test
- [ ] Nêu được 3 bảng trong dự án không nên dùng soft delete và thay bằng gì
- [ ] Parse đúng được chuỗi `"1.234,5"` theo vi-VN và `"1,234.5"` theo en-US bằng `NumberFormatter`

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Vì sao nên lưu thời gian ở UTC?** (1.1)
- Ý phải có: một chuẩn chung, không phụ thuộc server/DST, chuyển timezone khi hiển thị
- Điểm cộng: ngày sinh và giờ địa phương lặp lại không phải instant; sự kiện tương lai theo giờ địa phương cần lưu kèm timezone
- Red flag: "lưu theo giờ Việt Nam vì khách toàn người Việt"

**2. Vì sao không lưu tiền bằng `FLOAT`?** (1.2)
- Ý phải có: nhị phân không biểu diễn chính xác `0.1`; dùng `DECIMAL` hoặc integer minor unit
- Điểm cộng: PDO trả `DECIMAL` dạng string, ép float là mất chính xác; currency đi kèm

**3. MySQL `utf8` và `utf8mb4` khác nhau thế nào?** (1.3)
- Ý phải có: `utf8` là `utf8mb3`, tối đa 3 byte, không lưu emoji; dùng `utf8mb4` cho bảng, cột và kết nối
- Điểm cộng: giới hạn độ dài key index khi chuyển sang `utf8mb4`

**4. Vì sao không gửi email trong transaction DB?** (1.4)
- Ý phải có: mail đi mà transaction rollback; request chậm; dispatch sau commit
- Điểm cộng: outbox cho đảm bảo mạnh hơn `afterCommit`; mail catcher ở staging

**5. `strlen` và `mb_strlen` khác nhau thế nào?** (1.3, 2.7)
- Ý phải có: byte so với code point; `substr` cắt vỡ ký tự tiếng Việt
- Điểm cộng: grapheme (`grapheme_strlen`) cho emoji; `VARCHAR(n)` đếm ký tự

### 🟡 Mid

**6. `TIMESTAMP` và `DATETIME` trong MySQL khác nhau thế nào? `timestamptz` của Postgres lưu gì?** (2.1)
- Ý phải có: `TIMESTAMP` quy đổi theo session timezone, giới hạn 2038; `DATETIME` lưu nguyên; `timestamptz` lưu instant, không lưu timezone gốc
- Điểm cộng: cố định `time_zone` của connection; Laravel `'timezone'` trong cấu hình connection

**7. Làm báo cáo doanh thu theo ngày cho người dùng ở UTC+7 khi dữ liệu lưu UTC?** (2.1)
- Ý phải có: tính khoảng UTC `[17:00Z hôm trước, 17:00Z hôm nay)`, `WHERE` theo khoảng nửa mở
- Điểm cộng: `CONVERT_TZ`/`AT TIME ZONE` khi group, cần bảng timezone; cột `local_date` cho báo cáo lớn
- Red flag: `GROUP BY DATE(created_at)`, `BETWEEN ... 23:59:59`

**8. Chia 100.000đ cho 3 người thế nào để không mất đồng nào?** (2.2)
- Ý phải có: phần nguyên cho mỗi người, phần dư phân cho vài phần đầu; tổng bằng tổng gốc
- Điểm cộng: largest remainder khi chia theo tỷ lệ; lưu số đã phân bổ để hoàn tiền theo đó

**9. NFC và NFD là gì? Vì sao hai chuỗi tiếng Việt nhìn giống nhau lại không bằng nhau?** (2.3)
- Ý phải có: dựng sẵn và tổ hợp; so sánh byte khác; chuẩn hoá NFC tại ranh giới nhập liệu (`Normalizer::normalize`)
- Điểm cộng: kiểu đặt dấu cũ/mới NFC không gộp; nguồn NFD từ macOS

**10. Collation `utf8mb4_0900_ai_ci` ảnh hưởng gì tới unique index?** (2.3)
- Ý phải có: không phân biệt dấu và hoa thường, nên `"hoà"` trùng `"hoa"`; cột cần khớp chính xác dùng `_bin`/`_as_cs`
- Điểm cộng: tìm kiếm lại được lợi từ `ai_ci`; đổi collation bảng lớn là migration nặng

**11. Vì sao không lộ id auto-increment ra URL? UUIDv4 có vấn đề gì với index?** (2.4)
- Ý phải có: lộ số lượng, đoán được, IDOR; UUIDv4 ngẫu nhiên gây page split với clustered index
- Điểm cộng: UUIDv7/ULID; internal id + public id; `BINARY(16)`

**12. SPF, DKIM, DMARC là gì?** (2.6)
- Ý phải có: ai được gửi, chữ ký nội dung, chính sách khi fail + alignment
- Điểm cộng: giới hạn 10 lần tra DNS của SPF; yêu cầu người gửi số lượng lớn của Gmail/Yahoo từ 2024; tách domain giao dịch và marketing

**13. Thiết kế import file CSV 1 triệu dòng trong Laravel.** (2.5, 2.7)
- Ý phải có: job nền, streaming bằng generator/`SplFileObject`, chunk + transaction ngắn, thu lỗi theo dòng, tiến độ
- Điểm cộng: idempotent qua upsert khoá tự nhiên; BOM; Excel đổi kiểu dữ liệu; PhpSpreadsheet tốn RAM, dùng OpenSpout hoặc chunk reading
- Red flag: đọc cả file vào mảng rồi insert từng dòng trong request

**14. CSV injection là gì, chặn thế nào?** (2.5)
- Ý phải có: ô bắt đầu bằng `=`, `+`, `-`, `@`, tab, CR bị hiểu là công thức; bọc nháy kép, escape, thêm `'` phía trước
- Điểm cộng: dấu phân cách và nháy chèn giữa chuỗi mở ô mới; không có cách sanitize an toàn cho mọi app; tách export cho người xem và cho máy
- Red flag: chỉ kiểm tra `=`

**15. Luồng thanh toán qua cổng: return URL và IPN khác nhau thế nào? Tin cái nào?** (3.2)
- Ý phải có: return URL qua trình duyệt chỉ để hiển thị; IPN server-to-server, verify chữ ký, là nguồn sự thật
- Điểm cộng: kiểm tra số tiền và mã đơn; IPN idempotent; đối soát bắt IPN mất

**16. Trong PHP, lưu và tính tiền thế nào?** (2.7)
- Ý phải có: integer minor unit hoặc string decimal với bcmath/thư viện money; không float
- Điểm cộng: `BcMath\Number` và `RoundingMode::HalfEven` của PHP 8.4; `round()` mặc định half away from zero; cast `decimal:2` trả string

### 🔴 Senior

**17. Gọi cổng thanh toán bị timeout, bạn xử lý thế nào?** (3.2)
- Ý phải có: không coi là thất bại; trạng thái `unknown`, tra cứu theo mã giao dịch, chờ IPN; retry chỉ với cùng idempotency key
- Điểm cộng: chặn user thanh toán lần hai; đối soát; quy trình thu hồi khi đã trùng
- Red flag: "timeout thì báo lỗi, cho user thanh toán lại"

**18. Thiết kế ví điện tử theo ledger bút toán kép.** (3.1)
- Ý phải có: bút toán append-only, mỗi giao dịch cân bằng; số dư là tổng hoặc snapshot đối chiếu; sửa bằng reversal
- Điểm cộng: chống âm số dư khi đồng thời; idempotency theo mã giao dịch; bất biến tổng bằng 0

**19. IPN báo thành công nhưng đơn đã bị huỷ.** (3.3)
- Ý phải có: state machine có nhánh này; không đổi trạng thái mù; hoàn tiền hoặc khôi phục đơn theo nghiệp vụ
- Điểm cộng: audit trail; đối soát; cảnh báo cho vận hành
- Red flag: `UPDATE status = 'paid'` luôn

**20. Soft delete có vấn đề gì? Khi nào bạn không dùng?** (3.4)
- Ý phải có: quên lọc, unique index, bảng phình, dữ liệu cá nhân vẫn còn
- Điểm cộng: archive table, trạng thái nghiệp vụ rõ ràng; generated column cho unique ở MySQL

**21. Làm sao đảm bảo test tự động không bao giờ đụng vào DB dùng chung hoặc production?** (3.4)
- Ý phải có: DB riêng khai rõ trong `.env.testing`/`phpunit.xml`, guard theo tên DB, quyền DB tách
- Điểm cộng: container tạm; credential production không có trên máy dev; `RefreshDatabase` chạy migrate thật

**22. Báo cáo doanh thu ngày của sếp lệch với số của kế toán.** (2.1, 2.2)
- Ý phải có: kiểm tra ranh giới ngày UTC/UTC+7, `BETWEEN 23:59:59`, đơn hoàn tiền tính vào ngày nào, làm tròn ở đâu
- Điểm cộng: chốt định nghĩa "doanh thu ngày" với kế toán, viết thành query chuẩn dùng chung

**23. Khách tên "Nguyễn Thị Huệ" không tìm được bằng chính tên đó dù dữ liệu có.** (2.3)
- Ý phải có: dữ liệu NFD (import từ macOS), từ khoá NFC; hoặc kiểu đặt dấu cũ/mới
- Điểm cộng: chuẩn hoá khi lưu và khi tìm, migrate dữ liệu cũ, cột tìm kiếm đã bỏ dấu

**24. Mở file export đơn hàng bằng Excel: tên khách thành ký tự lạ, số điện thoại mất số 0.** (2.5)
- Ý phải có: thêm BOM UTF-8; số điện thoại xuất dạng text hoặc `.xlsx` với cell kiểu text
- Điểm cộng: kiểm tra luôn CSV injection với dữ liệu user nhập

**25. Job gửi email nhắc lịch 8h sáng: khách ở Úc nhận lúc 11h trưa, có ngày nhận hai lần.** (2.1)
- Ý phải có: cron theo giờ server; phải tính theo timezone từng user; DST ở Úc
- Điểm cộng: chạy mỗi 15 phút chọn user tới giờ, lưu "đã gửi cho ngày X" để idempotent

**26. Chạy test ở máy local làm mất dữ liệu DB staging của cả team.** (3.4)
- Ý phải có: cấu hình test không khai DB riêng nên dùng `.env` trỏ staging; setup có migrate/`TRUNCATE`
- Điểm cộng: guard, quyền DB tách, khôi phục từ backup, postmortem không đổ lỗi cá nhân

**27. Import 500.000 dòng Excel làm worker PHP chết vì hết memory.** (2.7)
- Ý phải có: PhpSpreadsheet load cả workbook; chuyển sang streaming (OpenSpout) hoặc chunk reading, chạy trong queue
- Điểm cộng: ước lượng RAM theo số cell; đo `memory_get_peak_usage`; tách đọc file và ghi DB theo chunk

**28. Chia khuyến mãi 50.000đ cho 3 dòng, tổng hoàn tiền khi trả từng dòng lệch vài đồng.** (2.2)
- Ý phải có: phân bổ có phần dư lúc đặt hàng và lưu lại; hoàn theo số đã lưu, không tính lại
- Điểm cộng: assert tổng phân bổ bằng tổng khuyến mãi; test với số lẻ

---

## Bài tập tự làm

1. Viết hàm `allocate(amount, ratios)` (ngôn ngữ tuỳ chọn) chia một số tiền integer theo tỷ lệ, đảm bảo tổng các phần bằng đúng `amount`. Tự liệt kê các test case cần có.
2. Viết query báo cáo số đơn theo ngày giờ Việt Nam trong tháng 9/2026 từ bảng `orders(created_at UTC)`, bằng cả MySQL 8.4 và Postgres, và giải thích query nào dùng được index.
3. Viết hàm PHP chuẩn hoá chuỗi tìm kiếm tiếng Việt: NFC, lowercase, bỏ dấu (xử lý `đ`), gộp khoảng trắng. Liệt kê ít nhất 8 input kiểm tra, gồm cả NFD và kiểu đặt dấu cũ/mới.
4. Vẽ state machine cho đơn hàng có thanh toán online, gồm các nhánh: IPN đến trễ sau khi đơn bị huỷ, thanh toán timeout, hoàn tiền một phần. Viết bảng chuyển đổi hợp lệ.
5. Thiết kế bảng và luồng cho tính năng import sản phẩm từ Excel: bảng job import, bảng lỗi theo dòng, cách chạy lại an toàn, cách báo tiến độ. Chọn thư viện đọc file (PhpSpreadsheet, OpenSpout hay Laravel Excel) và giải thích bằng ước lượng memory.
6. Viết hàm export CSV cho Laravel dùng `streamDownload` + `lazyById()`, có BOM và chống CSV injection. Kèm file test chứa các payload bắt đầu bằng `=`, `+`, `-`, `@`, tab, CR.

> Nộp bài vào đây để được review.
