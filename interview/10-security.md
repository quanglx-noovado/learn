# 10. Bảo mật

> [← Mục lục](README.md) · **[📖 Bài đọc kiến thức](kien-thuc/10-security.md)** · Trọng tâm: **bảo mật ứng dụng backend PHP/Laravel 13** theo OWASP Top 10:2025 và OWASP API Security Top 10 (2023), OAuth 2.0 theo RFC 9700.
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
| [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) | Hướng dẫn thực hành | Nguồn tra cứu chính cho gần như mọi module. Mỗi cheat sheet ngắn, có khuyến nghị cụ thể |
| [OWASP Top 10:2025](https://owasp.org/Top10/2025/) và [OWASP API Security Top 10 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/) | Danh mục rủi ro | Khung để nói chuyện về lỗ hổng. Người phỏng vấn hay hỏi "kể tên" |
| [PortSwigger Web Security Academy](https://portswigger.net/web-security) | Khoá học + lab miễn phí | Hiểu lỗ hổng bằng cách tự khai thác. **Làm lab** quan trọng hơn đọc lý thuyết |
| [OWASP ASVS](https://github.com/OWASP/ASVS) | Tiêu chuẩn kiểm chứng | Checklist yêu cầu bảo mật theo cấp độ, dùng khi review thiết kế |
| [NIST SP 800-63B-4](https://pages.nist.gov/800-63-4/sp800-63b.html) | Tiêu chuẩn | Password, MFA, authenticator, session (bản chính thức 07/2025) |
| [RFC 9700: OAuth 2.0 Security BCP](https://www.rfc-editor.org/rfc/rfc9700) | RFC (01/2025) | Cách dùng OAuth 2.0 an toàn hiện nay. OAuth 2.1 vẫn là Internet-Draft |
| *Serious Cryptography*, 2nd ed. (Jean-Philippe Aumasson; No Starch 2024) | Sách | Crypto cho kỹ sư: hash, AEAD, RSA/ECC, TLS. Đọc ch.1–4 và phần về authenticated encryption |
| [Laravel docs](https://laravel.com/docs) và [PHP manual: Security](https://www.php.net/manual/en/security.php) | Official docs | Tầng framework: CSRF, auth, authorization, encryption, hashing |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.5 | Lưu password đúng, hiểu session/cookie, chặn được injection/XSS/CSRF, phân biệt các khái niệm crypto | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.9 | Thiết kế luồng đăng nhập bằng token, OAuth/OIDC, authorization, nắm OWASP Top 10, chống lạm dụng, không dính bẫy của Laravel | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.6 | Token gắn người giữ, multi-tenant, key management, supply chain, dữ liệu cá nhân, threat modeling | 8–10 ngày |

Học theo thứ tự: chặng 2 dựa trên cookie, hash và HMAC của chặng 1; chặng 3 là những quyết định
thiết kế mà senior phải bảo vệ được trước người phỏng vấn. Song song với việc đọc, làm lab trên
PortSwigger cho từng lỗ hổng: tự khai thác một lần nhớ lâu hơn đọc mười lần.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Lưu password

**Vì sao cần học:** Gần như app nào cũng có bảng `users` với cột password. Khi DB bị lộ (qua
SQL injection, backup để quên, nhân viên cũ), cách bạn lưu password quyết định kẻ tấn công
lấy được vài password hay toàn bộ. Câu "lưu password thế nào, vì sao không dùng SHA-256" là câu
mở đầu kinh điển, rồi bị hỏi tiếp sang salt, pepper, reset password.

**Học gì**

*Hash chậm có chủ đích*
- *Hash* là hàm biến input bất kỳ thành một chuỗi cố định, không đảo ngược được. Lưu password
  nghĩa là lưu hash, lúc login thì hash lại input rồi so.
- Kẻ lấy được DB không đảo ngược được hash, nhưng có thể **đoán**: hash thử từng password phổ
  biến rồi so với hash trong DB. Vì vậy hàm hash càng nhanh thì đoán càng nhanh.
- ⚠️ Không dùng MD5, SHA-1, SHA-256 "trần" cho password. Chúng được thiết kế để nhanh, GPU thử
  được hàng chục tỷ lần mỗi giây.
- Dùng hàm hash password, vốn **chậm có chủ đích** và tự kèm salt:
  - argon2id: OWASP xếp đầu. Tốn cả CPU lẫn RAM, nên GPU khó chạy song song.
  - bcrypt: lâu đời, được hỗ trợ ở mọi nơi. `PASSWORD_DEFAULT` của PHP là bcrypt.
  - scrypt: cũng tốn RAM như argon2id.
  - PBKDF2: dùng khi hệ thống cần chuẩn FIPS (yêu cầu của một số khách hàng chính phủ, ngân hàng).
- *Cost factor* là tham số chỉnh độ chậm.
  - Chỉnh sao cho một lần hash tốn vài chục tới vài trăm ms trên server thật.
  - Tăng dần khi phần cứng mạnh lên.
- *Rehash*: khi user đăng nhập thành công, nếu cost hoặc thuật toán đã đổi thì hash lại password
  (lúc này bạn đang có password gốc trong tay) và lưu hash mới.
  - PHP làm việc này bằng `password_needs_rehash`.

*Salt và pepper*
- *Salt* là chuỗi ngẫu nhiên, riêng cho từng user, ghép vào password trước khi hash.
  - Lưu ngay cạnh hash (bcrypt và argon2id nhét luôn salt vào chuỗi hash). Salt không cần bí mật.
  - Tác dụng: hai user cùng password `123456` có hai hash khác nhau.
  - Chống *rainbow table*, tức bảng tính sẵn "hash → password" cho hàng tỷ password phổ biến.
    Có salt thì bảng tính sẵn vô dụng, phải đoán lại từ đầu cho từng user.
- *Pepper* là một secret **dùng chung** cho mọi user, lưu **ngoài DB** (ví dụ trong secret manager).
  - Bảo vệ khỏi kịch bản: DB lộ mà pepper không lộ thì hash vô dụng với kẻ tấn công.
  - Không bảo vệ khỏi kịch bản kẻ tấn công vào được server app, vì ở đó có cả hai.
  - Cái giá vận hành: mất pepper là mất khả năng verify mọi password.

*Các cạm bẫy khi hash*
- ⚠️ bcrypt chỉ dùng **72 byte** đầu của input, phần sau bị cắt âm thầm. Password dài hơn
  72 byte mà giống nhau ở 72 byte đầu thì được coi là một.
- ⚠️ Hash chậm là mục tiêu DoS (*Denial of Service*, làm server quá tải). Kẻ tấn công gửi
  password dài 1 MB liên tục là CPU cạn.
  - Giới hạn độ dài tối đa hợp lý.
  - Rate limit endpoint login (module 2.9).
- *Timing attack*: đoán bí mật bằng cách đo thời gian phản hồi.
  - So sánh chuỗi thông thường dừng ngay ở byte khác đầu tiên. Đoán đúng càng nhiều byte đầu thì
    phản hồi càng chậm hơn một chút, và kẻ tấn công đo được.
  - Token, HMAC, API key phải so bằng *constant-time compare*, tức hàm so sánh luôn tốn cùng một
    thời gian (PHP: `hash_equals`).
  - Login với email không tồn tại vẫn phải chạy một lần hash giả. Nếu không, email không tồn tại
    trả lời nhanh hơn hẳn, lộ ra email nào có tài khoản.

*Password policy theo NIST SP 800-63B-4*
- Độ dài tối thiểu:
  - **15 ký tự** khi password là yếu tố xác thực duy nhất.
  - **8 ký tự** khi password chỉ dùng kèm MFA (xác thực nhiều yếu tố, module 2.4).
- Cho phép tối đa ít nhất 64 ký tự. Nhận mọi ký tự in được, khoảng trắng và Unicode.
- Không bắt quy tắc "chữ hoa + số + ký tự đặc biệt". Không bắt đổi định kỳ. Chỉ bắt đổi khi có
  dấu hiệu password đã lộ.
  - Lý do: các quy tắc này khiến người dùng chọn `Password1!` rồi đổi thành `Password2!`.
- Chặn password nằm trong danh sách đã lộ, ví dụ qua Have I Been Pwned.
  - Dịch vụ này dùng *k-anonymity*: bạn chỉ gửi 5 ký tự đầu của SHA-1(password), nhận về danh sách
    hash có cùng đầu đó rồi tự so. Password thật không rời server của bạn.
- Cho phép paste (để dùng password manager). Bỏ câu hỏi bí mật.

*Quên mật khẩu*
- Quy trình an toàn:
  1. Sinh token bằng CSPRNG (bộ sinh số ngẫu nhiên an toàn cho crypto, module 1.4).
  2. Chỉ lưu **hash** của token trong DB, gửi token gốc qua email.
  3. Token dùng một lần và hết hạn ngắn.
  4. Thông báo giống nhau dù email có tồn tại hay không.
  5. Đổi password xong thì thu hồi mọi session và refresh token khác của user.
- ⚠️ *Host header injection*: code dựng link reset từ header `Host` của request, ví dụ
  `https://{Host}/reset?token=...`. Kẻ tấn công gửi request quên mật khẩu cho email nạn nhân với
  `Host: evil.com`, nạn nhân bấm link là token bay về evil.com.
  - Sửa: dựng link từ domain cấu hình cứng, hoặc chỉ chấp nhận `Host` trong whitelist.
  - ⚠️ Laravel: đặt `APP_URL` thôi là chưa đủ, vì khi xử lý request, URL tuyệt đối được dựng từ
    header `Host`. Cần bật `trustHosts()` hoặc cấu hình web server chỉ nhận đúng domain.

*Đối chiếu Java/Go*
- PHP: `password_hash`, `password_verify`, `password_needs_rehash`.
- Java Spring Security: `BCryptPasswordEncoder`, `Argon2PasswordEncoder`.
- Go: `golang.org/x/crypto/bcrypt` và `golang.org/x/crypto/argon2`.

**Đọc**
- OWASP: [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) (tham số argon2id/bcrypt khuyến nghị), [Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html)
- NIST SP 800-63B-4: mục về password (memorized secret) trong [phần Authenticators](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/)
- [Have I Been Pwned: Pwned Passwords API](https://haveibeenpwned.com/API/v3#PwnedPasswords) (cơ chế k-anonymity)
- PortSwigger: [Password reset poisoning](https://portswigger.net/web-security/host-header/exploiting/password-reset-poisoning)

**Nắm chắc khi**
- [ ] Giải thích được vì sao "nhanh" là nhược điểm của hash khi dùng cho password, bằng con số ước lượng
- [ ] Nói được pepper bảo vệ khỏi kịch bản nào, không bảo vệ khỏi kịch bản nào, và cái giá vận hành
- [ ] Viết được luồng login có rehash khi đổi cost, không lộ email tồn tại qua thời gian phản hồi
- [ ] Nêu đúng yêu cầu độ dài của NIST SP 800-63B-4 cho hai trường hợp có và không có MFA

#### 1.2 Session và cookie

**Vì sao cần học:** Đăng nhập web bằng Laravel mặc định là session lưu ở server và một cookie ở
trình duyệt. Hiểu từng thuộc tính của cookie là nền để hiểu CSRF, XSS và JWT ở các module sau.
Người phỏng vấn hay đưa một header `Set-Cookie` và hỏi từng thuộc tính làm gì, hoặc hỏi về
`SameSite` và session fixation.

**Học gì**

*Session là gì*
- *Session*: server lưu trạng thái đăng nhập (ai đang đăng nhập, dữ liệu tạm) trong Redis hoặc
  DB. Cookie ở trình duyệt chỉ chứa *session id*, một chuỗi ngẫu nhiên dùng để tra.
- Ưu điểm:
  - Thu hồi dễ: xoá bản ghi session ở server là user bị đăng xuất ngay.
  - Đăng xuất từng thiết bị dễ.
- Khi scale ra nhiều server, mọi server phải đọc chung một session store (ví dụ Redis).
  - Không nên dựa vào *sticky session* (load balancer luôn đưa một user về cùng một server), vì
    server đó chết là user mất session.

*Session fixation*
- Kịch bản tấn công:
  1. Kẻ tấn công lấy một session id hợp lệ (chưa đăng nhập) từ site của bạn.
  2. Hắn cài session id đó vào trình duyệt nạn nhân, ví dụ qua một subdomain hắn kiểm soát.
  3. Nạn nhân đăng nhập. Server đánh dấu session id đó là "đã đăng nhập".
  4. Kẻ tấn công dùng chính session id đó, và giờ hắn là nạn nhân.
- ⚠️ Sửa: **đổi session id ngay sau khi login**.
  - PHP thuần: `session_regenerate_id(true)`.
  - Laravel: `$request->session()->regenerate()` (các starter kit đã gọi sẵn). `Auth::login()`
    cũng tự đổi session id.

*Các thuộc tính của cookie*
- `HttpOnly`: JavaScript không đọc được cookie qua `document.cookie`.
- `Secure`: chỉ gửi qua HTTPS.
- `Path`: chỉ gửi với URL bắt đầu bằng path này.
- `Max-Age` / `Expires`: thời gian sống. Không khai thì cookie mất khi đóng trình duyệt.
- `Domain`:
  - Có khai thì cookie được gửi cho cả các subdomain.
  - Không khai thì chỉ gửi cho đúng host đã đặt nó. Cách này hẹp hơn nên an toàn hơn.
- Prefix `__Host-`: cookie có tên bắt đầu bằng `__Host-` bị trình duyệt bắt buộc phải có
  `Secure`, `Path=/` và không có `Domain`.
  - Tác dụng: một subdomain (có thể bị chiếm) không ghi đè được cookie này.
- Ví dụ một session cookie an toàn:

  ```
  Set-Cookie: __Host-session=8f3a...; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=7200
  ```

*SameSite*
- Trước hết cần phân biệt hai khái niệm:
  - *Origin* là bộ ba scheme + host + port. `https://a.example.com` và `https://b.example.com`
    là hai origin khác nhau.
  - *Site* là scheme + domain đăng ký được (ví dụ `example.com`). Hai URL trên là **same-site**.
  - Request *cross-site* là request mà trang đang mở và đích đến khác site.
- `SameSite` quyết định cookie có được gửi kèm request cross-site hay không:

  | Giá trị | Gửi cookie với request cross-site khi nào |
  |---|---|
  | `Strict` | Không bao giờ, kể cả khi user bấm link từ site khác sang |
  | `Lax` | Chỉ khi điều hướng top-level (thanh địa chỉ đổi URL) bằng method an toàn như GET |
  | `None` | Mọi lúc. Bắt buộc kèm `Secure` |

- ⚠️ "Không khai `SameSite` thì mặc định là `Lax`" **chỉ đúng với Chrome/Edge**.
  - Kèm ngoại lệ "Lax+POST": cookie mới đặt dưới 2 phút vẫn được gửi theo POST top-level
    cross-site (để không làm hỏng luồng đăng nhập SSO).
  - Firefox và Safari không áp dụng mặc định này.
  - Vì vậy **luôn khai `SameSite` rõ ràng**, và không coi mặc định của trình duyệt là lớp chống
    CSRF (module 1.3).
- ⚠️ Vì `a.example.com` và `b.example.com` là same-site, nếu một subdomain bị chiếm thì
  `SameSite` không cứu được.

*HttpOnly không chống được XSS*
- ⚠️ XSS (chèn script vào trang, module 1.3) vẫn là thảm hoạ dù cookie có `HttpOnly`.
  - Script độc chạy ngay trong trang của bạn, nên nó gửi request thay user được, và trình duyệt
    vẫn tự kèm cookie.
  - `HttpOnly` chỉ chặn được việc lấy cookie mang ra ngoài dùng nơi khác.

**Đọc**
- OWASP: [Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- MDN: [Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) (mục cookie prefixes và `SameSite`)
- Chromium: [SameSite Updates](https://www.chromium.org/updates/same-site/) (lịch sử Lax-by-default và Lax+POST)
- PortSwigger: [Bypassing SameSite cookie restrictions](https://portswigger.net/web-security/csrf/bypassing-samesite-restrictions)
- Laravel: [Regenerating the Session ID](https://laravel.com/docs/session#regenerating-the-session-id)

**Nắm chắc khi**
- [ ] Viết được một header `Set-Cookie` cho session cookie an toàn và giải thích từng thuộc tính
- [ ] Giải thích được session fixation bằng một kịch bản cụ thể và chỗ sửa trong code
- [ ] Nói được vì sao không thể dựa vào "Lax mặc định" để chống CSRF, nêu tên trình duyệt

#### 1.3 Injection, XSS, CSRF

**Vì sao cần học:** Ba lỗ hổng web kinh điển nhất, gần như chắc chắn bị hỏi ở mọi level. Laravel
chặn sẵn phần lớn (query builder bind tham số, Blade escape, middleware CSRF), nên câu hỏi thật
thường là "chỗ nào framework **không** chặn hộ" và "XSS khác CSRF thế nào".

**Học gì**

*SQL injection*
- Là gì: input của user bị ghép vào câu SQL và được DB hiểu như một phần của câu lệnh.

  ```php
  // SAI: $email = "' OR 1=1 -- " thì câu lệnh trả về mọi user
  $db->query("SELECT * FROM users WHERE email = '$email'");

  // ĐÚNG: prepared statement
  $stmt = $pdo->prepare('SELECT * FROM users WHERE email = ?');
  $stmt->execute([$email]);
  ```
- *Prepared statement* chặn được vì câu lệnh và dữ liệu được gửi **riêng**. DB parse câu lệnh
  trước, dữ liệu đến sau chỉ là giá trị, không bao giờ được parse như SQL.
- ⚠️ Tên cột, tên bảng, hướng `ORDER BY` (`ASC`/`DESC`) không bind được bằng `?`. Với những chỗ
  này phải dùng *whitelist*: chỉ chấp nhận giá trị nằm trong danh sách cho phép.

  ```php
  $sort = in_array($request->sort, ['name', 'created_at'], true) ? $request->sort : 'id';
  ```
- ⚠️ Trong Laravel, `whereRaw`, `DB::raw`, `orderByRaw` và native query vẫn bị inject nếu nối
  chuỗi input vào. Dùng tham số thứ hai để bind: `whereRaw('price > ?', [$min])`.
- ⚠️ PDO_MYSQL mặc định *emulate prepare*, tức PDO tự escape và ghép dữ liệu vào câu lệnh ở phía
  PHP thay vì gửi riêng. Vẫn an toàn nếu charset kết nối khai đúng trong DSN (chi tiết ở
  [03-database-sql.md](03-database-sql.md)).

*XSS (Cross-Site Scripting)*
- Là gì: kẻ tấn công chèn được JavaScript vào trang của bạn, và script đó chạy trong trình duyệt
  của người khác với quyền của họ.
- Ba loại:
  - *Stored*: script được lưu vào DB (ví dụ trong bình luận) rồi hiện cho mọi người xem.
  - *Reflected*: script nằm trong URL, server in lại vào trang (ví dụ trang tìm kiếm in lại từ khoá).
  - *DOM-based*: JS phía trình duyệt tự lấy dữ liệu từ URL và ghi vào trang, server không liên quan.
- Cách chặn chính: *escape* khi output, tức đổi các ký tự đặc biệt thành dạng vô hại (`<` thành
  `&lt;`).
  - Escape phải theo **ngữ cảnh** nơi dữ liệu được đặt vào: nội dung HTML, thuộc tính HTML, trong
    JS, trong URL. Mỗi ngữ cảnh có quy tắc khác.
  - Template engine tự escape. Blade `{{ $x }}` escape HTML.
- ⚠️ Những chỗ lọt XSS hay gặp:
  - Blade `{!! $x !!}` (in nguyên, không escape).
  - JS: `innerHTML`, Vue `v-html`, React `dangerouslySetInnerHTML`.
  - URL `javascript:alert(1)` trong `href`. Escape HTML không chặn được, phải kiểm tra scheme là
    `http`/`https`.
- Rich text (user được nhập HTML, ví dụ trình soạn thảo bài viết): *sanitize* bằng thư viện
  whitelist (HTML Purifier ở PHP, DOMPurify ở JS), tức chỉ giữ các thẻ và thuộc tính cho phép.
  Không tự viết regex.
- *CSP* (Content Security Policy, module 2.7) làm lớp thứ hai: header báo trình duyệt chỉ chạy
  script từ nguồn cho phép.
  - Dùng nonce hoặc hash cho script hợp lệ, cấm inline script.
  - Bật `Content-Security-Policy-Report-Only` trước để xem cái gì sẽ bị chặn mà chưa làm hỏng trang.

*CSRF (Cross-Site Request Forgery)*
- Là gì: site độc làm trình duyệt của nạn nhân gửi request tới site của bạn. Trình duyệt **tự
  gửi kèm cookie**, nên server tưởng đó là nạn nhân thật.
  - Ví dụ: evil.com có một form ẩn tự submit `POST https://bank.vn/transfer`. Nạn nhân đang đăng
    nhập bank.vn, cookie session đi kèm, lệnh chuyển tiền chạy.
- Cách chặn:
  - *CSRF token*: server đặt một token bí mật vào form, request phải gửi kèm token đó. Site khác
    không đọc được token.
    - *Synchronizer token*: token lưu trong session ở server.
    - *Double-submit* có ký: token nằm cả trong cookie và trong form, server so hai cái và kiểm
      tra chữ ký.
  - Kiểm tra header Fetch Metadata và `Origin` (module 2.7).
  - Khai `SameSite` rõ ràng (module 1.2).
- ⚠️ GET không được đổi state. Nếu `GET /logout` hay `GET /delete?id=1` đổi dữ liệu thì một thẻ
  `<img src=...>` ở site khác cũng kích hoạt được.
- API chỉ nhận `Authorization: Bearer <token>` (không dùng cookie) thì không bị CSRF kiểu cổ điển,
  vì trình duyệt không tự gửi header này.

*XSS khác CSRF thế nào*

| | XSS | CSRF |
|---|---|---|
| Kẻ tấn công làm được gì | Chạy JS trong trang của bạn: đọc trang, gửi request, đọc response | Chỉ gửi được request, không đọc được response |
| Cần gì | Chỗ output không escape | Server tin cookie mà không kiểm tra nguồn request |
| Chặn bằng | Escape theo ngữ cảnh, sanitize, CSP | CSRF token, Fetch Metadata/`Origin`, `SameSite` |
| Ghi chú | Có XSS thì CSRF token cũng vô dụng, vì script đọc được token | |

**Đọc**
- OWASP: [SQL Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html), [XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html), [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- PortSwigger: [SQL injection](https://portswigger.net/web-security/sql-injection), [Cross-site scripting](https://portswigger.net/web-security/cross-site-scripting), [CSRF](https://portswigger.net/web-security/csrf). Làm ít nhất 3 lab mỗi chủ đề
- Laravel: [CSRF Protection](https://laravel.com/docs/csrf), [Blade: Displaying Unescaped Data](https://laravel.com/docs/blade#displaying-unescaped-data)

**Nắm chắc khi**
- [ ] Giải thích được prepared statement chặn injection ở tầng nào, và 2 chỗ nó không giúp được
- [ ] Cho một đoạn Blade/JS, chỉ ra chỗ lọt XSS theo từng ngữ cảnh output
- [ ] Phân biệt rõ XSS và CSRF: kẻ tấn công làm được gì, không làm được gì, chặn bằng gì

#### 1.4 Crypto cơ bản

**Vì sao cần học:** Backend thường xuyên đụng tới crypto: verify webhook từ cổng thanh toán, ký
cookie, sinh token reset password, mã hoá số CCCD. Nhầm encode với encrypt, hay dùng `rand()`
sinh token, là lỗi thật trong code review. Người phỏng vấn hay đưa vài tình huống và hỏi "dùng
công cụ nào".

**Học gì**

*Sáu khái niệm hay bị nhầm*
- *Encode* (base64, URL encode): đổi cách biểu diễn dữ liệu. Ai cũng giải ngược được, không có
  bí mật nào.
- *Hash* (SHA-256): biến input thành chuỗi cố định, không đảo ngược. Cùng input luôn ra cùng hash.
- *HMAC*: hash có trộn thêm một secret. Chỉ ai có secret mới tạo được HMAC đúng.
  - Ví dụ: cổng thanh toán gửi webhook kèm `HMAC(secret, body)`. Bạn tính lại và so, khớp nghĩa
    là body không bị sửa và đúng là do cổng thanh toán gửi.
- *Encrypt đối xứng*: một key dùng cho cả mã hoá và giải mã.
- *Encrypt bất đối xứng*: cặp key. Mã hoá bằng public key, chỉ private key giải được.
- *Sign* (ký số): ký bằng private key, ai có public key cũng verify được.

| | Đảo ngược được? | Cần key? | Dùng cho |
|---|---|---|---|
| Encode (base64, URL encode) | Có, ai cũng làm được | Không | Biểu diễn dữ liệu, **không** bảo mật |
| Hash (SHA-256) | Không | Không | Checksum, fingerprint |
| HMAC | Không | Secret chung | Toàn vẹn + xác thực nguồn (webhook, cookie ký) |
| Encrypt đối xứng (AES-GCM, XChaCha20-Poly1305) | Có, với key | Một key | Mã hoá dữ liệu |
| Encrypt bất đối xứng (RSA-OAEP, ECIES) | Có, với private key | Cặp key | Trao đổi key |
| Sign (Ed25519, ECDSA, RSA-PSS) | Verify bằng public key | Cặp key | JWT RS256/ES256, ký bản release |

*Vì sao phải dùng HMAC*
- ⚠️ Cách tự chế `SHA256(secret + message)` bị *length extension attack* với SHA-2.
  - Ý tưởng: SHA-256 xử lý dữ liệu theo từng khối, và hash đầu ra chính là trạng thái bên trong
    sau khối cuối. Biết hash của `secret + message` thì kẻ tấn công tiếp tục "nối thêm" dữ liệu và
    tính được hash hợp lệ của `secret + message + phần_thêm`, dù không biết secret.
  - HMAC hash hai lần lồng nhau với secret, nên không bị kiểu tấn công này.

*Số ngẫu nhiên an toàn*
- *CSPRNG* (Cryptographically Secure Pseudo-Random Number Generator) là bộ sinh số ngẫu nhiên mà
  không ai đoán được số tiếp theo, kể cả khi đã thấy các số trước.
  - PHP: `random_bytes`, `random_int`.
  - Go: `crypto/rand`.
  - Java: `SecureRandom`.
- ⚠️ Không dùng `rand()`, `mt_rand()`, `uniqid()`, JS `Math.random()` cho token. Chúng đoán
  được: seed của `mt_rand` đoán lại được từ output của nó, `uniqid` chỉ là thời gian hiện tại.

*Không tự chế crypto*
- ⚠️ Không tự ghép *mode* (cách dùng thuật toán mã hoá khối cho dữ liệu dài, module 3.3), không tự
  viết thuật toán.
- Dùng thư viện cấp cao, loại đã chọn sẵn tham số an toàn: libsodium (có sẵn trong PHP), Google Tink.
- Mọi kết nối mạng dùng TLS. Chi tiết handshake ở [02-networking.md](02-networking.md).

**Đọc**
- *Serious Cryptography*: ch.1 (encryption), ch.2 (randomness), ch.6 (hash), ch.7 (MAC)
- OWASP: [Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- PHP: [random_bytes](https://www.php.net/manual/en/function.random-bytes.php), [hash_hmac](https://www.php.net/manual/en/function.hash-hmac.php), [hash_equals](https://www.php.net/manual/en/function.hash-equals.php)

**Nắm chắc khi**
- [ ] Với 6 tình huống (lưu password, xác minh webhook, lưu số CCCD, token reset, ký JWT, truyền ảnh qua URL), chọn đúng công cụ và giải thích
- [ ] Giải thích được length extension attack ở mức ý tưởng và vì sao HMAC không bị

#### 1.5 Authentication, authorization và IDOR

**Vì sao cần học:** Lỗi phân quyền là loại lỗ hổng phổ biến nhất trong API thật, và scanner tự
động không phát hiện được, vì request trông hoàn toàn hợp lệ. Trong Laravel, quên gắn
`where user_id` hay quên gọi Policy là đủ để user này xem đơn của user khác. Người phỏng vấn hay
đưa một controller và hỏi "chỗ này có lỗi gì".

**Học gì**

*Hai khái niệm*
- *Authentication* (xác thực): bạn là ai. Ví dụ: đăng nhập bằng email và password.
- *Authorization* (phân quyền): bạn được làm gì. Ví dụ: user A được sửa đơn của A, không được sửa
  đơn của B.
- Lỗi hay gặp là chỉ làm cái đầu: "đã đăng nhập" bị coi như "được phép".

*IDOR / BOLA*
- *IDOR* (Insecure Direct Object Reference), trong OWASP API gọi là *BOLA* (Broken Object Level
  Authorization): API nhận id của một object mà không kiểm tra object đó có thuộc về user hiện tại.
  - Ví dụ: user đang xem `GET /orders/123`, đổi thành `GET /orders/124` và thấy đơn của người khác.
- ⚠️ Phải kiểm tra đơn **thuộc** user hiện tại, không chỉ kiểm tra đã đăng nhập.
- BOLA đứng đầu OWASP API Top 10 (module 2.6).
- ⚠️ UUID làm id khó đoán hơn, nhưng **không thay** được kiểm tra quyền. Id vẫn lọt qua log, URL
  chia sẻ, response của API khác.
- Cách sửa: query luôn gắn phạm vi của user.

  ```php
  // SAI: ai đăng nhập cũng xem được mọi đơn
  $order = Order::findOrFail($id);

  // ĐÚNG: chỉ tìm trong đơn của user hiện tại
  $order = $request->user()->orders()->findOrFail($id);
  // tương đương WHERE id = ? AND user_id = ?
  ```

*BFLA và nguyên tắc mặc định*
- *BFLA* (Broken Function Level Authorization): user thường gọi được chức năng dành cho admin.
  - Ví dụ: user thường gọi được `DELETE /admin/users/1`, vì app chỉ ẩn nút ở UI mà server không
    kiểm tra vai trò.
- *Deny by default*: mặc định là từ chối, chỉ cho phép những gì được khai rõ.
- *Fail secure*: khi việc kiểm tra quyền bị lỗi (exception, timeout) thì từ chối, không cho qua.

*API key*
- Quy tắc tạo và lưu:
  - Sinh bằng CSPRNG (module 1.4).
  - Có prefix nhận dạng, ví dụ `sk_live_...`, để công cụ quét secret (secret scanner, module 3.4)
    bắt được khi key lỡ bị commit lên git.
  - Lưu **hash** trong DB. SHA-256 là đủ, khác với password.
    - Lý do: key ngẫu nhiên 32 byte có *entropy* (độ khó đoán) cực cao, không có danh sách "key
      phổ biến" nào để đoán. Password do người đặt nên dễ đoán, phải dùng hash chậm.
  - Chỉ hiện key cho user **một lần** lúc tạo.
- Quản lý:
  - Mỗi key có scope (quyền giới hạn) và hạn dùng.
  - Cho phép nhiều key cùng lúc để *rotate* (thay key mới) mà không gián đoạn.

**Đọc**
- OWASP: [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html), [IDOR Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html)
- OWASP API Top 10: [API1:2023 BOLA](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/)
- PortSwigger: [Access control](https://portswigger.net/web-security/access-control)

**Nắm chắc khi**
- [ ] Nhìn một controller Laravel, chỉ ra được chỗ có IDOR và sửa bằng scope hoặc Policy
- [ ] Giải thích được vì sao API key lưu SHA-256 là đủ, còn password thì không

---

### Chặng 2: Làm chủ 🟡

#### 2.1 JWT

**Vì sao cần học:** JWT có mặt ở hầu hết hệ thống dùng token: mobile app, microservice, đăng
nhập bằng Google. Thư viện JWT dùng sai cấu hình từng gây nhiều lỗ hổng chiếm tài khoản nổi
tiếng. Người phỏng vấn hay hỏi "verify một JWT gồm những bước nào" và "HS256 khác RS256 ra sao".

**Học gì**

*JWT là gì*
- *JWT* (JSON Web Token) là một chuỗi gồm ba phần nối bằng dấu chấm:
  `base64url(header).base64url(payload).signature`.
  - Header: thuật toán ký (`alg`), loại token (`typ`), id của key (`kid`).
  - Payload: các *claim*, tức các cặp key-value như `sub` (user id), `exp` (hết hạn lúc nào).
  - Signature: chữ ký trên hai phần đầu. Ai sửa header hoặc payload thì chữ ký không còn khớp.
- ⚠️ Payload chỉ được **encode** (base64url), không mã hoá. Ai có token cũng đọc được nội dung.
  - Cần giấu nội dung thì dùng *JWE* (JSON Web Encryption), hoặc đơn giản là không đặt dữ liệu
    nhạy cảm vào token.

*Hai kiểu ký*

| | HS256 | RS256 / ES256 / EdDSA |
|---|---|---|
| Loại | HMAC, một secret chung (đối xứng) | Chữ ký số, cặp key (bất đối xứng) |
| Ai ký được | Bất kỳ ai có secret | Chỉ bên giữ private key |
| Ai verify được | Bất kỳ ai có secret | Bất kỳ ai có public key |
| Phân phối key | Phải chia secret cho mọi bên verify | Công bố public key qua *JWKS* (một URL trả danh sách public key) |
| Hợp khi | Một service vừa ký vừa verify | Nhiều service verify, chỉ một nơi ký |

- ⚠️ Với HS256, service nào verify được thì cũng **ký được**. Chia secret cho 5 service là 5 nơi
  có thể giả token.

*Verify một JWT: kiểm tra những gì*
1. Chữ ký, với thuật toán nằm trong whitelist cố định phía server.
2. `exp` (expiration): token chưa hết hạn.
3. `nbf` (not before): token đã tới thời điểm có hiệu lực.
4. `iss` (issuer): đúng bên phát hành mình tin.
5. `aud` (audience): token được phát cho chính service này.
6. Cho phép *clock skew* nhỏ (lệch giờ giữa các server; RFC 9068 nói thường không quá vài phút) khi so thời gian.

*Các tấn công kinh điển*
- ⚠️ `alg: none`: kẻ tấn công sửa header thành "không ký" và bỏ chữ ký. Thư viện nào tin `alg`
  trong header sẽ chấp nhận.
  - Sửa: **cố định whitelist thuật toán** phía server, không tin `alg` trong header.
- ⚠️ *Algorithm confusion*:
  1. Server dùng RS256, verify bằng public key. Public key thì ai cũng lấy được.
  2. Kẻ tấn công tạo token với `alg: HS256`, ký HMAC bằng chính public key đó làm secret.
  3. Thư viện đọc `alg: HS256`, lấy "key" đang cấu hình (là public key) làm secret HMAC để verify.
  4. Chữ ký khớp, token giả được chấp nhận.
  - Sửa: cũng là cố định thuật toán theo từng key.
- ⚠️ `kid` là input không tin được. Chỉ dùng nó để tra trong bảng key đã biết trước.
  - Không tự tải key theo URL trong header `jku` hoặc `x5u`, vì kẻ tấn công trỏ được URL về
    server của hắn.
- ⚠️ Nhầm loại token: ID token, access token (module 2.3) và token của hệ khác có thể cùng định
  dạng JWT, cùng được ký bởi một bên.
  - Kiểm tra `typ` (ví dụ `at+jwt` cho access token, theo RFC 9068) và `aud` để loại token này
    không dùng thay được loại kia.
- *JWT BCP* (RFC 8725) gom các khuyến nghị trên vào một chỗ. BCP là *Best Current Practice*, loại
  RFC ghi cách làm tốt nhất hiện nay.

**Đọc**
- [RFC 8725: JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725): đọc hết mục 2 và 3, ngắn
- [RFC 9068: JWT Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068)
- PortSwigger: [JWT attacks](https://portswigger.net/web-security/jwt) và [Algorithm confusion](https://portswigger.net/web-security/jwt/algorithm-confusion), làm lab
- [jwt.io introduction](https://jwt.io/introduction)

**Nắm chắc khi**
- [ ] Liệt kê được thứ tự kiểm tra một JWT nhận vào, và kiểm tra nào thiếu thì dẫn tới lỗ hổng nào
- [ ] Giải thích được algorithm confusion từng bước và dòng cấu hình nào chặn được nó
- [ ] Chọn được HS256 hay ES256 cho một hệ 5 service và bảo vệ lựa chọn đó

#### 2.2 Vòng đời token: revocation, refresh, nơi lưu, BFF

**Vì sao cần học:** Chọn JWT xong thì câu hỏi tiếp theo luôn là "đăng xuất thế nào", "đổi password
thì token cũ còn dùng được không", "token lưu ở đâu trên trình duyệt". Đây là phần thiết kế mà
người phỏng vấn dùng để phân biệt người chỉ biết dùng thư viện với người hiểu trade-off.

**Học gì**

*Vì sao JWT khó thu hồi*
- JWT *stateless*: server chỉ cần verify chữ ký là tin token, không tra DB. Hệ quả là không thu hồi
  được token trước `exp` nếu chỉ verify chữ ký.
- Các cách xử lý:
  - Access token sống ngắn (5–15 phút), kèm *refresh token* (token sống lâu, chỉ dùng để xin
    access token mới) lưu ở server.
  - *Denylist* theo `jti` (id duy nhất của token): lưu các token bị thu hồi trong Redis, TTL bằng
    thời gian còn lại tới `exp`.
  - `token_version` trong bảng user: token mang version, đổi password thì tăng version, token cũ
    bị từ chối.
- ⚠️ Khi đã phải tra state (Redis, DB) mỗi request thì phần lớn lợi ích "stateless" mất. Nói rõ
  trade-off này khi trả lời.

*Refresh token rotation và reuse detection*
- *Rotation*: mỗi lần dùng refresh token, server cấp một refresh token **mới** và vô hiệu cái cũ.
  - Các refresh token sinh ra từ cùng một lần login thuộc một *family* (một chuỗi).
- *Reuse detection*: nếu một refresh token **đã dùng rồi** lại được gửi lên, nghĩa là có hai bên
  cùng giữ nó (một bên là kẻ trộm). Server thu hồi **cả family**, buộc đăng nhập lại.
- ⚠️ Báo nhầm: nhiều tab, hoặc mạng retry, gửi song song hai request refresh với cùng token. Cái
  thứ hai bị coi là reuse.
  - Sửa: cho một *grace period* ngắn (vài giây chấp nhận token cũ), hoặc client đồng bộ để chỉ
    một tab refresh.
- Refresh token lưu **hash** trong DB, gắn với thiết bị, có hạn tuyệt đối (ví dụ 30 ngày thì phải
  đăng nhập lại dù vẫn đang dùng).

*Lưu token ở đâu trên trình duyệt*

| Nơi lưu | XSS đọc được? | Bị CSRF? | Ghi chú |
|---|---|---|---|
| `localStorage` / `sessionStorage` | Có | Không | XSS lấy token mang đi dùng nơi khác |
| Cookie `HttpOnly` | Không | Có, phải chống | Trình duyệt tự gửi |
| Biến trong memory của JS | Khó hơn | Không | Mất khi reload trang |

*BFF (Backend for Frontend)*
- Là gì: với SPA (ứng dụng một trang, chạy bằng JS), một backend cùng site đứng giữa giữ các token
  OAuth. Trình duyệt chỉ có session cookie `HttpOnly` tới backend đó.
- Luồng:
  1. SPA gọi API qua BFF, kèm session cookie.
  2. BFF tra session, lấy access token và gọi API thật.
  3. Token không bao giờ xuống trình duyệt.
- RFC 10017 (OAuth 2.0 for Browser-Based Applications, BCP, 08/2026) khuyến nghị mạnh mô hình này
  cho ứng dụng nghiệp vụ, vì JS độc trong trang không lấy được token.

*Chọn session hay token*
- Web app một domain (Blade, Inertia, SPA cùng site): session cookie thường đơn giản và an toàn hơn.
- Mobile, hoặc nhiều service verify độc lập: access token ngắn + refresh token.
- Service-to-service: JWT ký bất đối xứng, client credentials (module 2.3), hoặc *mTLS* (hai bên
  cùng xuất trình certificate TLS).
- Mobile lưu token trong kho an toàn của hệ điều hành: Keychain (iOS), Keystore (Android).

**Đọc**
- [RFC 10017: OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017): mục 5 (mối đe doạ từ JavaScript độc) và mục 6 (BFF, token-mediating backend, browser-based client)
- RFC 9700: [mục 4.14 Refresh Token Protection](https://www.rfc-editor.org/rfc/rfc9700#section-4.14)
- [Auth0: Refresh Token Rotation](https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation) (có mục reuse detection)
- OWASP: [JSON Web Token Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html): phần threats on JWTs, revocation và replay protection

**Nắm chắc khi**
- [ ] Vẽ được luồng refresh có rotation, reuse detection và xử lý hai tab refresh cùng lúc
- [ ] Thiết kế được "đăng xuất mọi thiết bị khi đổi password" cho hệ dùng JWT, nói rõ độ trễ chấp nhận được
- [ ] Giải thích được vì sao RFC 10017 ưu tiên BFF hơn việc để SPA tự giữ token

#### 2.3 OAuth 2.0 và OIDC

**Vì sao cần học:** "Đăng nhập bằng Google", cho app bên thứ ba truy cập dữ liệu, SSO nội bộ đều
dựa trên OAuth 2.0 và OIDC. Hiểu sai OAuth dẫn tới lỗi chiếm tài khoản kinh điển. Câu hay bị hỏi:
"authorization code + PKCE chạy thế nào", "vì sao bỏ implicit flow", "ID token khác access token
ở đâu".

**Học gì**

*OAuth 2.0 là gì*
- OAuth2 là giao thức **ủy quyền** (*delegated authorization*): user cho phép một app truy cập
  dữ liệu của mình ở nơi khác, mà không đưa password cho app đó.
  - Ví dụ: app in ảnh xin quyền đọc Google Photos của bạn.
- OAuth2 **không phải** giao thức đăng nhập. Đăng nhập là việc của OIDC (xem dưới).
- Bốn vai trò:
  - *Resource owner*: user, chủ dữ liệu.
  - *Client*: app muốn truy cập.
  - *Authorization server*: nơi user đăng nhập và đồng ý, phát token (ví dụ Google).
  - *Resource server*: API chứa dữ liệu, nhận access token.

*Các flow*

| Flow | Dùng khi |
|---|---|
| Authorization code + PKCE | Mọi app có user: web, SPA, mobile |
| Client credentials | Server-to-server, không có user |
| Device authorization (RFC 8628) | TV, CLI (nhập mã trên một thiết bị khác) |
| Refresh token | Lấy access token mới |
| Implicit, Password (ROPC) | ⚠️ RFC 9700 khuyến cáo không dùng. OAuth 2.1 (draft) bỏ hẳn |

*Authorization code + PKCE từng bước*
- Hai kênh cần phân biệt:
  - *Front-channel*: dữ liệu đi qua trình duyệt, qua URL redirect. Dễ bị lộ.
  - *Back-channel*: server gọi thẳng server. An toàn hơn.
- Các bước:
  1. Client sinh `code_verifier` ngẫu nhiên, tính `code_challenge = BASE64URL(SHA256(code_verifier))`.
  2. Client chuyển trình duyệt tới authorization server, kèm `code_challenge`, `state`,
     `redirect_uri` (front-channel).
  3. User đăng nhập và đồng ý.
  4. Authorization server redirect về `redirect_uri` kèm `code` ngắn hạn (front-channel).
  5. Client gửi `code` + `code_verifier` tới token endpoint (back-channel).
  6. Server kiểm tra `SHA256(code_verifier)` khớp `code_challenge` rồi mới trả token.
- *PKCE* (Proof Key for Code Exchange) chặn việc kẻ chặn được `code` ở bước 4 đem đổi lấy token,
  vì hắn không có `code_verifier`.
  - RFC 9700 yêu cầu PKCE cho *public client* (app không giữ được secret: SPA, mobile) và khuyến
    nghị cho cả *confidential client* (có backend giữ secret).
- Implicit flow bị bỏ vì:
  - Token trả thẳng trên URL fragment, lọt vào lịch sử trình duyệt, và script hay extension chạy
    trong trang đọc được (trình duyệt không gửi fragment trong header `Referer`).
  - Client không kiểm được access token nhận về có thật sự được phát cho nó không (RFC 10017 mục
    7.2.4).

*Các cạm bẫy ở callback*
- `state`: giá trị ngẫu nhiên client gửi đi ở bước 2 và kiểm tra lại ở bước 4, chống CSRF trên
  callback (kẻ tấn công ép nạn nhân đăng nhập vào tài khoản của hắn).
- ⚠️ `redirect_uri` phải so khớp **chính xác** với giá trị đã đăng ký.
  - So theo prefix hoặc wildcard là lỗi chiếm tài khoản kinh điển: kẻ tấn công đặt
    `redirect_uri=https://app.com.evil.com/` và nhận `code` của nạn nhân.
- *Mix-up attack*: client dùng nhiều authorization server, bị lừa gửi `code` của server này sang
  server kia. Chặn bằng cách kiểm tra `iss` trong response (RFC 9207).

*OIDC: lớp đăng nhập trên OAuth*
- *OIDC* (OpenID Connect) thêm phần "user là ai" lên OAuth2.
  - Client xin scope `openid`, nhận thêm **ID token**: một JWT chứa `sub` (id user), `iss`, `aud`,
    `exp`, `nonce` (giá trị ngẫu nhiên chống dùng lại token).
  - Discovery: `/.well-known/openid-configuration` trả về mọi endpoint và URL JWKS.
  - Endpoint `userinfo` trả thêm thông tin user.
- ⚠️ ID token và access token khác nhau:

  | | ID token | Access token |
  |---|---|---|
  | Cho ai đọc | Client | Resource server |
  | Nói gì | User là ai, đăng nhập lúc nào | Bên cầm được làm gì (scope) |
  | Dùng để gọi API? | Không | Có |

- ⚠️ "Đăng nhập bằng OAuth" mà chỉ dùng access token là sai: access token không được phát cho
  client, nên client không biết chắc nó là của user nào và dành cho app nào.

*Trong Laravel*
- Passport: authorization server OAuth2 đầy đủ.
- Sanctum không phải OAuth (module 2.8).
- Đăng nhập bằng Google/GitHub: Socialite.

**Đọc**
- [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700): mục 2 (khuyến nghị tóm tắt) là bắt buộc; mục 4 đọc theo từng tấn công
- [RFC 7636: PKCE](https://www.rfc-editor.org/rfc/rfc7636)
- [OAuth 2.0 Simplified](https://www.oauth.com/) (Aaron Parecki): cách dễ đọc nhất để nắm các flow
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html): mục 2 (ID Token) và 3.1 (Authorization Code Flow)
- PortSwigger: [OAuth 2.0 authentication vulnerabilities](https://portswigger.net/web-security/oauth)
- OWASP: [OAuth 2.0 Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html)
- Laravel: [Passport or Sanctum?](https://laravel.com/docs/passport#passport-or-sanctum), [Passport PKCE](https://laravel.com/docs/passport#code-grant-pkce)

**Nắm chắc khi**
- [ ] Vẽ được authorization code + PKCE từng bước, chỉ ra kênh front-channel và back-channel
- [ ] Giải thích được PKCE chặn tấn công nào mà `state` không chặn được, và ngược lại
- [ ] Giải thích được cho người khác vì sao "đăng nhập bằng OAuth" mà chỉ dùng access token là sai

#### 2.4 MFA và passkey

**Vì sao cần học:** Password lộ là chuyện thường ngày, nên các hệ có tiền hay dữ liệu nhạy cảm
đều cần MFA. Passkey đang thay dần password ở các sản phẩm lớn. Câu hay bị hỏi: "vì sao passkey
chống phishing còn OTP thì không", "user mất điện thoại thì khôi phục thế nào".

**Học gì**

*MFA là gì*
- *MFA* (Multi-Factor Authentication): xác thực bằng ít nhất hai loại yếu tố khác nhau.
  - Thứ bạn biết: password.
  - Thứ bạn có: điện thoại, khoá bảo mật.
  - Thứ bạn là: vân tay, khuôn mặt.

*TOTP*
- *TOTP* (RFC 6238) là mã 6 số trong app như Google Authenticator.
  - Server và app cùng giữ một secret chung. Mã = hàm(secret, thời gian hiện tại chia bước 30 giây).
- Khi triển khai:
  - Chấp nhận lệch ±1 bước để bù đồng hồ lệch.
  - Chống dùng lại mã vừa dùng (lưu bước thời gian cuối đã dùng).
  - Secret phải mã hoá khi lưu, vì lộ secret là sinh được mọi mã.

*SMS OTP*
- Yếu vì:
  - *SIM swap*: kẻ tấn công lừa nhà mạng cấp lại SIM của nạn nhân.
  - Tin nhắn bị chặn trên đường truyền.
  - *SMS pumping*: kẻ gian dùng form gửi OTP của bạn để bắn SMS tới số của hắn và ăn chia cước.
- Chi tiết thiết kế OTP ở [22-practical-data.md](22-practical-data.md).

*WebAuthn và passkey*
- *WebAuthn* là chuẩn web để đăng nhập bằng cặp key.
  - Mỗi site một cặp khoá riêng. Private key nằm ở thiết bị hoặc password manager, không bao giờ
    gửi đi.
  - Credential gắn với *RP ID* (Relying Party ID): một domain, bằng hoặc là hậu tố của domain
    trang (ví dụ `example.com` cho `login.example.com`). Trình duyệt chỉ cho dùng key khi RP ID khớp
    với trang, và **origin** (scheme + host + port) nằm trong dữ liệu được ký. Trang
    giả `g00gle.com` không dùng được key của `google.com`, nên passkey chống phishing.
- *Passkey* là credential WebAuthn, có hai loại:
  - *Synced*: đồng bộ giữa các thiết bị qua iCloud Keychain, Google Password Manager.
  - *Device-bound*: gắn một thiết bị, ví dụ khoá YubiKey.
- Server lưu public key, credential id và *sign counter* (bộ đếm tăng mỗi lần ký, giúp phát hiện
  key bị nhân bản). ⚠️ Synced passkey thường luôn trả counter bằng 0, nên counter chỉ có ý nghĩa
  với credential một thiết bị. Không có secret nào để lộ khi DB bị lấy.
- Luồng đăng ký (*registration*):
  1. Server gửi một *challenge* (chuỗi ngẫu nhiên dùng một lần).
  2. Trình duyệt gọi `navigator.credentials.create`, thiết bị tạo cặp key.
  3. Server lưu public key.
- Luồng đăng nhập (*authentication*):
  1. Server gửi challenge mới.
  2. Trình duyệt gọi `navigator.credentials.get`, thiết bị ký challenge.
  3. Server verify chữ ký bằng public key đã lưu, kiểm tra origin và challenge.

*Khôi phục và các cạm bẫy*
- *Recovery code*: mã dùng một lần phát cho user lúc bật MFA, lưu hash.
- ⚠️ Luồng khôi phục tài khoản thường là điểm yếu nhất. MFA chặt mà "quên thiết bị" chỉ cần email
  là coi như không có MFA.
- ⚠️ *MFA fatigue*: kẻ có password gửi push xác nhận liên tục cho tới khi user bấm nhầm "Đồng ý".
  - Chống bằng *number matching*: user phải gõ số hiện trên màn hình đăng nhập.
- ⚠️ MFA không chặn được:
  - *Session hijack*: trộm session cookie sau khi user đã đăng nhập xong.
  - *AiTM* (Adversary-in-the-Middle): trang phishing làm proxy, chuyển tiếp cả password lẫn OTP
    tới site thật trong thời gian thực.
- Passkey thì chặn được AiTM, vì chữ ký gắn với origin của trang giả.

**Đọc**
- [passkeys.dev](https://passkeys.dev/): hướng dẫn triển khai cho developer
- [W3C WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/): đọc phần giới thiệu và các use case, không cần đọc hết
- OWASP: [Multifactor Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)
- [RFC 6238: TOTP](https://www.rfc-editor.org/rfc/rfc6238)
- PHP: [web-auth/webauthn-framework](https://github.com/web-auth/webauthn-framework) (thư viện WebAuthn cho PHP)

**Nắm chắc khi**
- [ ] Giải thích được vì sao passkey chống phishing còn TOTP thì không
- [ ] Vẽ được luồng đăng ký và đăng nhập bằng passkey, nói server lưu gì và kiểm tra gì
- [ ] Thiết kế được luồng khôi phục khi user mất thiết bị mà không mở toang cửa sau

#### 2.5 Authorization: mô hình và tầng kiểm tra

**Vì sao cần học:** Module 1.5 dạy kiểm tra "đơn có thuộc user không". Khi app lớn lên, bạn cần
một mô hình quyền rõ ràng (vai trò, chi nhánh, chia sẻ) và một chỗ tập trung để kiểm tra. Trong
Laravel đó là Gate và Policy. Câu hay bị hỏi: "RBAC khác ABAC thế nào", "kiểm tra quyền ở tầng
nào".

**Học gì**

*Ba mô hình*
- *RBAC* (Role-Based Access Control): quyền gắn với vai trò, user được gán vai trò.
- *ABAC* (Attribute-Based Access Control): quyền tính từ thuộc tính của user, của resource và của
  môi trường (giờ, IP).
- *ReBAC* (Relationship-Based Access Control): quyền tính từ quan hệ giữa các đối tượng, kiểu đồ thị.

| Mô hình | Quyết định dựa trên | Ví dụ | Hợp khi |
|---|---|---|---|
| RBAC | Vai trò | `admin`, `editor` | Quyền theo chức danh, ít ngoại lệ |
| ABAC | Thuộc tính user, resource, môi trường | "Sửa đơn của chi nhánh mình, trong giờ làm việc" | Quy tắc động |
| ReBAC | Quan hệ giữa các đối tượng | "Xem file nếu là thành viên folder cha" (Zanzibar, OpenFGA) | Chia sẻ, phân cấp lồng nhau |

- ⚠️ RBAC dễ nổ số role khi thêm ngoại lệ (`editor_hanoi`, `editor_hanoi_readonly`...). Thực tế
  thường là RBAC kết hợp kiểm tra ownership.

*Kiểm tra ở tầng nào*
- Gateway hoặc middleware: xác thực, và quyền thô (token có scope này không).
- Service hoặc domain: quyền trên từng object, vì chỉ ở tầng này mới biết object thuộc ai.
- ⚠️ Chỉ kiểm tra ở controller thì các đường khác đi vòng qua được:
  - Job trong queue.
  - Artisan command.
  - GraphQL resolver.
  - Consumer đọc message từ queue.
- Tập trung logic quyền vào một chỗ:
  - Laravel: Gate, Policy.
  - Java: Spring Security `@PreAuthorize`.
  - Go: middleware tự viết.

*Gate và Policy trong Laravel*
- Gate cho quyền không gắn với model cụ thể (ví dụ "xem dashboard báo cáo").
- Policy cho quyền theo model (ví dụ `OrderPolicy::update($user, $order)`).
- `Gate::before` chạy trước mọi kiểm tra, hay dùng cho super admin.
  - ⚠️ Trả về `true` ở đây là bỏ qua mọi policy.
- Các chỗ gọi:
  - Controller: `Gate::authorize('update', $order)`.
  - Route middleware: `can:update,order`.
  - Blade: `@can`.
  - Form Request: method `authorize()`.
- ⚠️ Policy chỉ chạy khi được gọi. Viết Policy mà không gọi là không có kiểm tra nào.

*Quyền ở mức field*
- *Broken Object Property Level Authorization*: user có quyền với object, nhưng sửa được hoặc đọc
  được field không được phép.
  - Sửa được field cấm: *mass assignment*, ví dụ gửi thêm `is_admin=1` khi cập nhật profile
    (module 2.6).
  - Đọc được field thừa: response trả cả `password_hash`, `internal_note`.

**Đọc**
- OWASP: [Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html)
- [Zanzibar: Google's Consistent, Global Authorization System](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/) (paper, 2019): đọc mục 2 về mô hình dữ liệu
- [OpenFGA concepts](https://openfga.dev/docs/concepts)
- Laravel: [Authorization](https://laravel.com/docs/authorization) (Gates, Policies, `before` filter)

**Nắm chắc khi**
- [ ] Chọn được mô hình cho "Google Drive thu nhỏ" và cho "CRM có 5 vai trò" và giải thích vì sao
- [ ] Chỉ ra được 3 đường trong một app Laravel đi vòng qua kiểm tra quyền ở controller

#### 2.6 Lỗ hổng web và API theo OWASP

**Vì sao cần học:** OWASP Top 10 là "ngôn ngữ chung" khi nói về lỗ hổng, người phỏng vấn hay bảo
"kể tên" rồi chọn một mục để đào sâu. Các lỗ hổng như SSRF, `unserialize`, upload file là những
thứ backend PHP gặp thật khi làm tính năng webhook, tải ảnh từ URL, import file.

**Học gì**

*OWASP Top 10:2025*
- Danh sách 10 nhóm rủi ro phổ biến nhất của ứng dụng web:
  - A01 Broken Access Control (đã gộp SSRF vào đây)
  - A02 Security Misconfiguration
  - A03 Software Supply Chain Failures
  - A04 Cryptographic Failures
  - A05 Injection
  - A06 Insecure Design
  - A07 Authentication Failures
  - A08 Software or Data Integrity Failures
  - A09 Security Logging and Alerting Failures
  - A10 Mishandling of Exceptional Conditions (mới: xử lý lỗi sai dẫn tới *fail open*, tức lỗi thì
    cho qua, hoặc lộ thông tin)
- A02 trong thực tế:
  - Debug mode bật ở production.
  - `.git`, `.env` truy cập được qua web.
  - Bucket public.
  - Admin panel mở ra internet.
  - CORS quá rộng (module 2.7).
  - Trang lỗi trả stack trace.
- A10 trong thực tế:
  - `try/catch` nuốt exception rồi cho qua.
  - Kiểm tra quyền bị lỗi thì trả `true`.
  - Trang lỗi lộ stack trace.

*OWASP API Security Top 10 (2023)*
- Danh sách riêng cho API:
  1. BOLA (module 1.5)
  2. Broken Authentication
  3. Broken Object Property Level Authorization (module 2.5)
  4. Unrestricted Resource Consumption
  5. BFLA (module 1.5)
  6. Unrestricted Access to Sensitive Business Flows (module 2.9)
  7. SSRF
  8. Security Misconfiguration
  9. Improper Inventory Management (không biết mình đang chạy những API và phiên bản nào)
  10. Unsafe Consumption of APIs (tin tưởng mù quáng dữ liệu từ API bên thứ ba)

*SSRF (Server-Side Request Forgery)*
- Là gì: server gọi một URL do user cung cấp, và bị lừa gọi vào địa chỉ nội bộ.
  - Tính năng hay dính: webhook, tải ảnh từ URL, preview link.
  - Đích nguy hiểm: `169.254.169.254` (metadata của cloud, trả được credential của máy), `localhost`,
    dải IP private (`10.x`, `192.168.x`...).
- Cách chặn:
  - Resolve DNS rồi kiểm tra IP.
  - Tắt tự động follow redirect (OWASP khuyên vậy). Nếu buộc phải theo, kiểm tra lại từ đầu sau
    **mọi** redirect.
  - Chặn IP private và link-local, kể cả IPv6.
  - Whitelist domain nếu được.
  - Đi qua *egress proxy* (proxy kiểm soát mọi kết nối ra ngoài).
  - Trên AWS bật IMDSv2 (metadata yêu cầu token, khó bị SSRF đơn giản khai thác).
- ⚠️ *DNS rebinding*:
  1. Lúc validate, domain của kẻ tấn công resolve ra IP công khai, qua được kiểm tra.
  2. Lúc gọi thật, thư viện HTTP resolve lại, lần này ra `127.0.0.1`.
  - Sửa: kết nối tới đúng IP đã kiểm tra, không resolve lại.

*Các lỗi injection khác*
- *XXE* (XML External Entity): file XML khai báo "entity" trỏ tới file hoặc URL, parser đọc vào.
  Top 10:2025 xếp XXE vào A02 Security Misconfiguration.
  - Chặn: tắt DTD và external entity trong parser.
  - PHP 8 với libxml ≥ 2.9 mặc định không nạp external entity. ⚠️ Đừng truyền cờ `LIBXML_NOENT`,
    cờ này bật lại việc thay entity. PHP 8.4 thêm cờ `LIBXML_NO_XXE` (cần libxml2 ≥ 2.13) để dùng
    kèm khi buộc phải có `LIBXML_NOENT`.
- *Path traversal*: input như `../../etc/passwd` làm đọc file ngoài thư mục cho phép.
  - Chặn: `realpath` rồi kiểm tra đường dẫn vẫn nằm trong thư mục gốc.
  - Tốt hơn: không dùng input làm đường dẫn, dùng id tra ra tên file.
- *Command injection*: input được ghép vào lệnh shell, ví dụ `exec("convert $file out.png")` với
  `$file = "a.jpg; rm -rf /"`.
  - Chặn: tránh shell, truyền mảng tham số (`proc_open` với mảng, Symfony Process, `exec.Command`
    trong Go).
  - Tối thiểu là `escapeshellarg` cho từng tham số.

*Insecure deserialization*
- ⚠️ `unserialize()` với dữ liệu người dùng dựng được object của bất kỳ class nào đang có trong
  project.
  1. Kẻ tấn công gửi chuỗi serialize của một object với property do hắn chọn.
  2. PHP tự gọi *magic method* (`__wakeup` khi unserialize, `__destruct` khi object bị huỷ).
  3. Code trong các magic method đó của thư viện (gọi là *gadget*) nối với nhau thành *gadget
     chain*, cuối cùng ghi file hoặc chạy lệnh. Đó là RCE (*Remote Code Execution*).
  - Code của bạn không cần gọi hàm nguy hiểm nào, gadget có sẵn trong vendor là đủ.
- Cách sửa: dùng JSON.
  - ⚠️ Docs PHP: không truyền input không tin cậy vào `unserialize` **dù** có `allowed_classes`.
  - Chỉ `unserialize` dữ liệu do chính mình serialize: ký HMAC lúc tạo, kiểm HMAC **trước** khi
    unserialize, và vẫn truyền `['allowed_classes' => false]` hoặc danh sách class cụ thể.

*Mass assignment, open redirect, clickjacking*
- *Mass assignment*: gán thẳng mọi field từ request vào model, user gửi thêm field không được phép.
  - Chặn: whitelist field (`$fillable`, DTO, Form Request).
  - ⚠️ `$guarded = []` là mở toang.
  - Chiều ngược lại, response trả thừa field: dùng API Resource để chọn field trả ra.
- *Open redirect*: `?next=` cho phép redirect tới site bất kỳ, bị dùng để phishing trông như link
  của bạn.
  - Chặn: chỉ cho path tương đối, hoặc whitelist domain.
  - ⚠️ `//evil.com` và `/\evil.com` trông như path, nhưng trình duyệt hiểu là URL tuyệt đối.
- *Clickjacking*: site độc nhúng trang của bạn vào iframe trong suốt, lừa user bấm vào nút thật.
  - Chặn bằng CSP `frame-ancestors 'none'` (thay cho header cũ `X-Frame-Options`).

*File upload*
- Kiểm tra và lưu:
  - Kiểm tra loại thật bằng *magic bytes* (vài byte đầu file), không tin đuôi file hay
    `Content-Type` client gửi. Magic bytes cũng dễ giả, nên chỉ là một lớp, phải đi kèm các bước dưới.
  - Đổi tên ngẫu nhiên.
  - Lưu ngoài web root hoặc trên object storage (S3). Không cho thực thi.
- Phục vụ file:
  - Từ domain riêng, để file độc không chạy được với cookie của domain chính.
  - `Content-Disposition: attachment` khi hợp.
  - Re-encode ảnh (mở ra rồi lưu lại) để bỏ dữ liệu lạ nhét trong file.
  - Giới hạn kích thước.
- ⚠️ Các bẫy:
  - SVG chứa được JavaScript.
  - *Zip bomb*: file nén vài KB giải ra hàng GB.
  - Ảnh kích thước pixel khổng lồ làm nổ memory khi resize.

**Đọc**
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/): đọc trang giới thiệu (thay đổi so với 2021) và trang của A01, A03, A10
- [OWASP API Security Top 10 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/)
- OWASP cheat sheets: [SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html), [XXE](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html), [Deserialization](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html), [Mass Assignment](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html), [File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [OS Command Injection](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html), [Unvalidated Redirects](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html)
- PortSwigger (làm lab): [SSRF](https://portswigger.net/web-security/ssrf), [XXE](https://portswigger.net/web-security/xxe), [Path traversal](https://portswigger.net/web-security/file-path-traversal), [OS command injection](https://portswigger.net/web-security/os-command-injection), [Insecure deserialization](https://portswigger.net/web-security/deserialization), [File upload](https://portswigger.net/web-security/file-upload)
- PHP: [unserialize](https://www.php.net/manual/en/function.unserialize.php) (đọc khung cảnh báo), [escapeshellarg](https://www.php.net/manual/en/function.escapeshellarg.php)

**Nắm chắc khi**
- [ ] Kể được OWASP Top 10:2025 và nói 3 thay đổi lớn so với bản 2021
- [ ] Viết được pseudo-code cho hàm "tải ảnh từ URL" chống SSRF, kể cả redirect và DNS rebinding
- [ ] Giải thích được vì sao `unserialize` dữ liệu người dùng dẫn tới RCE dù code của bạn không gọi hàm nguy hiểm nào
- [ ] Cho 10 endpoint của một app, gán được rủi ro theo OWASP API Top 10 (bài tập 2)

#### 2.7 Header bảo mật, CSRF hiện đại, CORS

**Vì sao cần học:** Một phần lớn việc bảo vệ nằm ở header HTTP: trình duyệt làm hộ nếu server bảo
nó làm. Laravel 13 đổi cách chống CSRF sang dùng header Fetch Metadata. CORS là thứ backend nào
làm API cho SPA cũng phải cấu hình, và cấu hình sai rất phổ biến. Câu hay bị hỏi: "CORS có chống
CSRF không".

**Học gì**

*Fetch Metadata*
- Là các header trình duyệt tự gắn vào request, JS không sửa được:
  - `Sec-Fetch-Site`: request đến từ đâu so với đích (`same-origin`, `same-site`, `cross-site`,
    `none` khi user tự gõ URL).
  - `Sec-Fetch-Mode`: kiểu request (`navigate`, `cors`, `no-cors`...).
  - `Sec-Fetch-Dest`: request dùng để làm gì (`document`, `image`, `script`...).
- *Resource isolation policy*: từ chối request có `Sec-Fetch-Site: cross-site` tới endpoint đổi
  state, trừ những điều hướng top-level thật sự cần (ví dụ link từ email).
- Giới hạn:
  - Chỉ gửi trên HTTPS.
  - Trình duyệt cũ không gửi. Khi đó fallback sang CSRF token.
- Laravel 13: middleware `PreventRequestForgery` kiểm tra `Sec-Fetch-Site` trước, không đạt mới
  kiểm tra CSRF token. Có chế độ `originOnly`.
- Kiểm tra header `Origin` với request đổi state là một lớp bổ sung rẻ.

*Security headers*

| Header | Tác dụng |
|---|---|
| `Strict-Transport-Security: max-age=...; includeSubDomains` | *HSTS*: trình duyệt chỉ dùng HTTPS với site. ⚠️ `preload` (đưa vào danh sách cứng trong trình duyệt) khó rút lại |
| `Content-Security-Policy` | Giới hạn nguồn script, style, frame. `frame-ancestors` chống clickjacking |
| `X-Content-Type-Options: nosniff` | Trình duyệt không tự đoán MIME (ví dụ coi file text là script) |
| `Referrer-Policy: strict-origin-when-cross-origin` | Không gửi full URL (có thể chứa token) sang site khác |
| `Permissions-Policy` | Tắt camera, micro, geolocation không dùng |
| `Cache-Control: no-store` | Cho response chứa dữ liệu nhạy cảm, không lưu vào cache |

*CORS*
- Nền tảng là *same-origin policy*: JS của trang origin A không được đọc response từ origin B.
- *CORS* (Cross-Origin Resource Sharing) là cơ chế để server B **nới lỏng** luật đó, bằng header
  như `Access-Control-Allow-Origin`. CORS không phải cơ chế bảo vệ server.
- ⚠️ Phản chiếu mọi `Origin` gửi lên, kèm `Access-Control-Allow-Credentials: true`, là cho mọi
  site đọc được dữ liệu của user đang đăng nhập.
- ⚠️ CORS không chặn request tới server, nó chỉ chặn JS **đọc** response.
  - *Simple request* (ví dụ form POST thường) vẫn tới server và chạy bình thường, không có
    *preflight* (request `OPTIONS` hỏi trước).
  - Vì vậy CORS không thay được CSRF protection.

**Đọc**
- [web.dev: Protect your resources with Fetch Metadata](https://web.dev/articles/fetch-metadata)
- OWASP: [CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) (mục Fetch Metadata), [HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html), [Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html)
- PortSwigger: [CORS](https://portswigger.net/web-security/cors), [Clickjacking](https://portswigger.net/web-security/clickjacking)
- Laravel: [CSRF: Origin Verification](https://laravel.com/docs/csrf#origin-verification)
- [Mozilla HTTP Observatory](https://developer.mozilla.org/en-US/observatory): quét header của site thật

**Nắm chắc khi**
- [ ] Viết được một resource isolation policy dựa trên `Sec-Fetch-Site` và nói khi nào cần fallback
- [ ] Giải thích được vì sao cấu hình CORS sai là lỗ hổng, còn CORS đúng thì không chống được CSRF
- [ ] Quét header một site mình làm và giải thích từng dòng còn thiếu

#### 2.8 Tầng PHP/Laravel

**Vì sao cần học:** Đây là module riêng cho người làm PHP. Laravel làm hộ rất nhiều thứ, nên người
phỏng vấn hay hỏi vào chỗ framework làm hộ và chỗ framework **không** làm hộ: Sanctum khác Passport
ra sao, `APP_KEY` lộ thì sao, `==` của PHP nguy hiểm thế nào.

**Học gì**

*PHP core*
- Password: `password_hash`, `password_verify`, `password_needs_rehash` (module 1.1).
  - `PASSWORD_DEFAULT` hiện là bcrypt.
  - PHP 8.4 tăng cost mặc định của bcrypt từ 10 lên **12**.
- Token: `random_bytes`, `random_int`. Ví dụ token 64 ký tự hex: `bin2hex(random_bytes(32))`.
- So sánh token hoặc HMAC: `hash_equals` (constant-time). Tính HMAC cho webhook: `hash_hmac`.
- Sodium (`sodium_crypto_secretbox`, `sodium_crypto_aead_xchacha20poly1305_ietf_*`,
  `sodium_crypto_sign`) có sẵn từ PHP 7.2. Dùng thay vì tự ghép OpenSSL.
- ⚠️ `unserialize` với dữ liệu người dùng: *object injection* (module 2.6).
- ⚠️ `==` so sánh lỏng: chuỗi dạng số được đổi sang số trước khi so.
  - `"0e123" == "0e456"` là `true`, vì cả hai được hiểu là 0 × 10^n = 0.
  - Hash MD5 bắt đầu bằng `0e` và toàn số phía sau từng làm "so hash" bằng `==` cho qua với
    password sai.
  - Luôn dùng `===`, và `hash_equals` cho chuỗi bí mật.

*Laravel: xác thực*
- Session guard cho web (Blade, Inertia).
- *Sanctum* có hai chế độ:
  - **SPA cookie**: dùng session + CSRF như web thường, cho SPA chạy cùng top-level domain.
  - **API token**: *personal access token* lưu hash trong DB, có *abilities* (quyền), có hạn dùng.
    Cho mobile, script, bên thứ ba đơn giản.
- *Passport* khi cần authorization server OAuth2 thật: bên thứ ba đăng ký app, PKCE, client credentials.
- Fortify và starter kit: login, 2FA TOTP, reset password.
  - Rate limit login có sẵn, nhưng phải kiểm tra key throttle (theo email + IP hay chỉ IP).

*Laravel: CSRF và authorization*
- Middleware `PreventRequestForgery` nằm trong nhóm `web` (module 2.7).
  - ⚠️ `except` quá rộng (ví dụ `webhook/*` hay `*`) mở lỗ hổng.
  - Webhook thì verify chữ ký HMAC thay cho CSRF.
- Gate và Policy (module 2.5).

*Laravel: dữ liệu*
- Mass assignment:
  - Khai `$fillable`.
  - Bật `Model::preventSilentlyDiscardingAttributes()` ở môi trường dev để thấy ngay field bị bỏ qua.
  - ⚠️ Đưa thẳng `$request->all()` vào `create()`.
- *Encrypted casts* (`encrypted`, `encrypted:array`) cho field nhạy cảm, tự mã hoá khi lưu và giải
  mã khi đọc.
  - ⚠️ Không query hay index được field này. Cần tìm kiếm thì dùng *blind index* (module 3.3).
- Cookie mặc định được mã hoá và ký bằng `APP_KEY`.

*Laravel: cấu hình*
- ⚠️ `APP_KEY` lộ thì kẻ tấn công giả mạo được cookie, session, dữ liệu đã mã hoá và signed URL.
  - Trước đây, kết hợp với việc cookie được serialize, lộ `APP_KEY` đã dẫn tới RCE.
  - Rotate bằng `APP_PREVIOUS_KEYS` (key cũ vẫn giải mã được trong lúc chuyển).
- ⚠️ `APP_DEBUG=true` ở production: trang lỗi lộ biến môi trường, query, stack trace.
  - Ignition bản cũ có CVE-2021-3129 (*CVE* là mã định danh công khai của một lỗ hổng): RCE khi
    debug bật.
- ⚠️ `.env`, `.git`, `storage/logs` truy cập được qua web khi document root trỏ sai. Document root
  phải là `public/`.
- Dashboard Horizon, Telescope, Pulse phải có gate ở production.

*Supply chain*
- `composer audit` kiểm tra dependency có lỗ hổng đã công bố.
- Từ Composer 2.9, mặc định **chặn update** sang bản có security advisory (`audit.block-insecure`).
  `composer install` từ lockfile có sẵn thì không bị chặn, nên vẫn cần `composer audit` trong CI.
- Commit `composer.lock` (module 3.4).

**Đọc**
- PHP: [password_hash](https://www.php.net/manual/en/function.password-hash.php), [password_needs_rehash](https://www.php.net/manual/en/function.password-needs-rehash.php), [PHP 8.4: Other Changes](https://www.php.net/manual/en/migration84.other-changes.php) (bcrypt cost), [Sodium](https://www.php.net/manual/en/book.sodium.php)
- Laravel:
  - [Hashing](https://laravel.com/docs/hashing), [Encryption: rotating keys](https://laravel.com/docs/encryption#gracefully-rotating-encryption-keys), [Encrypted Casting](https://laravel.com/docs/eloquent-mutators#encrypted-casting)
  - [Sanctum: How it Works](https://laravel.com/docs/sanctum#how-it-works), [SPA Authentication](https://laravel.com/docs/sanctum#spa-authentication), [Token Expiration](https://laravel.com/docs/sanctum#token-expiration)
  - [Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment), [Rate Limiting](https://laravel.com/docs/rate-limiting)
  - [Configuration: Debug Mode](https://laravel.com/docs/configuration#debug-mode)
- OWASP: [Laravel Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html), [PHP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)
- [Composer 2.9 release](https://blog.packagist.com/composer-2-9/) (automatic security blocking)
- Paragon IE: [Using Encryption and Authentication Correctly](https://paragonie.com/blog/2015/05/using-encryption-and-authentication-correctly) (bài cũ nhưng giải thích rất rõ vì sao encrypt phải kèm authenticate)

**Nắm chắc khi**
- [ ] Chọn đúng giữa session, Sanctum SPA, Sanctum token và Passport cho 4 loại client khác nhau
- [ ] Liệt kê được những gì kẻ tấn công làm được khi có `APP_KEY`, và các bước khi phát hiện nó bị lộ
- [ ] Review một project Laravel thật, chỉ ra ít nhất 3 điểm trong checklist trên đang sai
- [ ] Giải thích được vì sao `"0e1" == "0e2"` và nó từng gây lỗ hổng so sánh hash thế nào

#### 2.9 Chống lạm dụng: rate limit, brute force, bot

**Vì sao cần học:** Endpoint login, OTP, reset password và các luồng khuyến mãi luôn bị bot tấn
công, và đây là chỗ bị lạm dụng tốn tiền thật (SMS, voucher). Người phỏng vấn hay hỏi "chống brute
force thế nào" rồi hỏi tiếp "vậy credential stuffing thì sao".

**Học gì**

*Rate limit nhiều lớp*
- *Rate limit*: giới hạn số request trong một khoảng thời gian.
- Đặt theo nhiều key: IP, tài khoản, thiết bị, endpoint.
- Endpoint nhạy cảm phải chặt hơn: login, OTP, reset password, tìm kiếm.
- Thuật toán (token bucket, sliding window) ở [09-api-design.md](09-api-design.md).

*Brute force và credential stuffing*
- *Brute force* một tài khoản: thử rất nhiều password cho một email.
  - Chống: giới hạn theo tài khoản, tăng dần độ trễ, CAPTCHA sau N lần sai.
  - ⚠️ Khoá cứng tài khoản sau N lần sai thì kẻ xấu cố tình khoá tài khoản người khác được.
- *Credential stuffing*: dùng danh sách email + password đã lộ từ site khác, thử trên site của bạn.
  - Mỗi IP chỉ thử vài lần (kẻ tấn công dùng hàng nghìn IP), nên rate limit theo IP không đủ.
  - Chống bằng:
    - MFA hoặc passkey.
    - Kiểm tra password đã lộ (module 1.1).
    - Phát hiện thiết bị hoặc vị trí mới.
    - Bot detection.

| | Brute force | Credential stuffing |
|---|---|---|
| Thử gì | Nhiều password cho một tài khoản | Một cặp đúng (ở site khác) cho nhiều tài khoản |
| Dấu hiệu | Nhiều lần sai trên một tài khoản | Tỉ lệ sai cao trên toàn hệ thống, rải nhiều IP |
| Chống chính | Giới hạn theo tài khoản, độ trễ, CAPTCHA | MFA/passkey, password đã lộ, tín hiệu thiết bị, bot detection |

*Account enumeration*
- Là gì: kẻ tấn công dò ra email nào có tài khoản.
- Chỗ lộ:
  - Thông báo lỗi ("email không tồn tại" khác "sai password").
  - Thời gian phản hồi (module 1.1).
  - Form đăng ký và quên mật khẩu.
- Chặn: trả thông điệp chung.

*Đào sâu (🔴)*
- Lạm dụng luồng nghiệp vụ (API6:2023): request hoàn toàn hợp lệ, nhưng bị dùng hàng loạt.
  - Ví dụ: gom hàng flash sale, spam tạo tài khoản để lấy khuyến mãi, SMS pumping (module 2.4).
  - Chống bằng giới hạn theo nghiệp vụ (mỗi số điện thoại một voucher), challenge có chọn lọc
    (chỉ hiện CAPTCHA khi đáng ngờ), và metric bất thường.

**Đọc**
- OWASP: [Credential Stuffing Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html), [Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) (mục account lockout và error messages)
- OWASP API Top 10: [API6:2023 Unrestricted Access to Sensitive Business Flows](https://api-security.owasp.org/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/)
- Laravel: [Rate Limiting](https://laravel.com/docs/rate-limiting)

**Nắm chắc khi**
- [ ] Thiết kế được bộ rate limit cho login và OTP: key nào, ngưỡng nào, phản hồi gì
- [ ] Giải thích được vì sao chặn theo IP không chống được credential stuffing và nêu 3 tín hiệu thay thế

---

### Chặng 3: Senior 🔴

#### 3.1 OAuth nâng cao: token gắn người giữ, PAR, SSO

**Vì sao cần học:** Ở hệ thống tài chính, open banking hay khách hàng doanh nghiệp, access token
"ai cầm cũng dùng được" không còn đủ, và khách doanh nghiệp đòi SSO qua SAML. Senior được hỏi để
xem có hiểu giới hạn của bearer token và biết các cơ chế bổ sung, không cần nhớ từng field.

**Học gì**

*Bearer token và sender-constrained token*
- *Bearer token*: ai cầm cũng dùng được, giống tiền mặt. Token lọt qua log, proxy hay XSS là bị
  dùng ngay.
- *Sender-constrained token*: token gắn với khoá của client. Kẻ trộm token mà không có private key
  thì không dùng được.
- Hai cách làm:
  - **DPoP** (RFC 9449):
    - Mỗi request, client ký một *proof JWT* chứa method, URL và thời điểm của request đó.
    - Access token chứa *thumbprint* (dấu vân tay) của public key client.
    - Resource server kiểm tra proof được ký bằng đúng key có thumbprint trong token.
    - Hợp với SPA, mobile.
  - **mTLS-bound token** (RFC 8705):
    - Token gắn với certificate TLS của client, kiểm tra ở tầng kết nối.
    - Hợp với server-to-server, open banking.
- RFC 9700 khuyến nghị dùng sender-constrained token khi có thể.

| | DPoP | mTLS-bound token |
|---|---|---|
| Gắn token với | Cặp key do client tự sinh | Certificate TLS của client |
| Kiểm tra ở | Tầng ứng dụng (header `DPoP`) | Tầng TLS |
| Hợp với | SPA, mobile | Server-to-server, open banking |
| Cái giá | Ký thêm mỗi request, chống replay proof | Quản lý certificate. TLS kết thúc ở load balancer thì phải chuyển cert của client vào app |

*PAR và token exchange*
- *PAR* (Pushed Authorization Requests, RFC 9126):
  1. Client gửi các tham số authorization qua back-channel tới authorization server.
  2. Nhận lại một `request_uri`.
  3. Chỉ đưa `request_uri` lên URL trình duyệt.
  - Lợi ích: chống sửa tham số trên URL, URL ngắn. Bắt buộc trong *FAPI 2.0* (bộ quy chuẩn bảo
    mật OAuth cho tài chính).
- *Token exchange* (RFC 8693): service A đổi token của user lấy một token mới để gọi service B thay
  mặt user, với `aud` và scope hẹp hơn.

*SSO và SAML*
- *SSO* (Single Sign-On): đăng nhập một lần ở *IdP* (Identity Provider, ví dụ Okta, Azure AD),
  nhiều *SP* (Service Provider, các app) tin IdP.
- *SAML*: chuẩn SSO dựa trên XML, phổ biến trong doanh nghiệp.
  - IdP gửi một *assertion* (khẳng định "user này là X") đã ký, đi qua trình duyệt tới SP.
- ⚠️ *XML signature wrapping*:
  - Code verify chữ ký trên một phần của tài liệu XML, nhưng đọc dữ liệu (như email user) từ một
    phần khác không được ký, do kẻ tấn công chèn thêm.
  - Chặn: dùng thư viện đã kiểm chứng, không tự parse.
- *SCIM*: chuẩn để IdP tự tạo, cập nhật, khoá user ở app. Nhân viên nghỉ việc là tài khoản bị khoá
  ở mọi app.

*Session ở hai tầng*
- Session ở IdP và session ở từng app là hai thứ khác nhau. Logout ở một nơi không tự logout nơi
  khác.
- OIDC có *back-channel logout*: IdP gọi thẳng server của app để báo "user này đã logout".

**Đọc**
- [RFC 9449: DPoP](https://www.rfc-editor.org/rfc/rfc9449): mục 1 (vấn đề), 4 (DPoP proof), 7 (resource server kiểm tra gì)
- [RFC 8705: OAuth 2.0 Mutual-TLS](https://www.rfc-editor.org/rfc/rfc8705): mục 3 (certificate-bound token)
- [RFC 9126: PAR](https://www.rfc-editor.org/rfc/rfc9126)
- RFC 9700: [mục 2.2 Token Replay Prevention](https://www.rfc-editor.org/rfc/rfc9700#section-2.2)
- [OWASP SAML Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html)

**Nắm chắc khi**
- [ ] Giải thích được DPoP chặn được gì mà HTTPS + token ngắn hạn không chặn được, và cái giá của nó
- [ ] Chọn được DPoP hay mTLS cho 2 bối cảnh cụ thể
- [ ] Giải thích được XML signature wrapping bằng hình vẽ

#### 3.2 Multi-tenant isolation

**Vì sao cần học:** SaaS B2B gần như luôn là multi-tenant: nhiều công ty khách hàng dùng chung một
hệ thống. Lộ dữ liệu giữa tenant là sự cố mất khách lớn nhất. Senior được hỏi chọn mức cô lập
nào và làm sao chắc chắn không có query nào quên lọc `tenant_id`.

**Học gì**

*Ba mức cô lập*
- *Tenant* là một khách hàng (một công ty) trong hệ thống dùng chung.

| Mức | Mô tả | Chi phí | Rủi ro lộ chéo |
|---|---|---|---|
| DB riêng | Mỗi tenant một database | Cao nhất | Thấp nhất |
| Schema riêng | Chung server DB, mỗi tenant một schema | Trung bình | Trung bình |
| Chung bảng | Mọi tenant chung bảng, phân biệt bằng cột `tenant_id` | Rẻ nhất | Cao nhất |

- Càng chung càng rẻ, càng dễ lộ chéo.

*Chung bảng làm sao cho an toàn*
- `tenant_id` lấy từ token hoặc session của user đang đăng nhập, **không** lấy từ tham số request.
- Laravel: *global scope* tự thêm `WHERE tenant_id = ?` vào mọi query của model.
  - ⚠️ Các đường đi vòng qua global scope: `withoutGlobalScopes()`, query raw, `DB::table()`.
- Lớp thứ hai ở DB:
  - Postgres có *Row-Level Security* (RLS): DB tự lọc dòng theo policy, kể cả khi app quên.
  - MySQL không có RLS, phải dựa vào view hoặc tầng app.

*Những chỗ hay lộ*
- ⚠️ Ngoài controller, các chỗ sau hay quên tenant:
  - Cache key thiếu tenant (`report:monthly` thay vì `tenant:5:report:monthly`).
  - File storage dùng chung prefix.
  - Job nền mất context tenant khi được đẩy vào queue.
  - Export và báo cáo.
  - Search index.
- Viết test tự động "tenant A không đọc được dữ liệu tenant B" cho mọi endpoint quan trọng.

*Noisy neighbor*
- Một tenant dùng quá nhiều tài nguyên làm chậm các tenant khác. Đây cũng là vấn đề bảo mật: DoS
  giữa các tenant.
- Chống bằng quota theo tenant.

**Đọc**
- Postgres: [Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- Laravel: [Global Scopes](https://laravel.com/docs/eloquent#global-scopes)
- AWS: [SaaS Tenant Isolation Strategies](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html) (whitepaper): silo, pool, bridge

**Nắm chắc khi**
- [ ] Chọn và bảo vệ được mức cô lập cho SaaS B2B 500 tenant, trong đó 3 tenant rất lớn
- [ ] Liệt kê được 5 chỗ ngoài HTTP controller có thể làm mất `tenant_id` trong một app Laravel

#### 3.3 Crypto ứng dụng và quản lý key

**Vì sao cần học:** Khi phải lưu số CCCD, số tài khoản ngân hàng hay token của bên thứ ba, "bật
encryption at rest" là chưa đủ. Senior cần biết chọn thuật toán, quản lý key, rotate key, và tìm
kiếm trên dữ liệu đã mã hoá. Câu hay bị hỏi: "envelope encryption là gì", "DB đã mã hoá rồi còn
cần gì nữa".

**Học gì**

*Đối xứng và bất đối xứng*
- Mã hoá đối xứng nhanh, dùng cho dữ liệu lớn.
- Mã hoá bất đối xứng chậm, dùng để trao đổi key hoặc ký.
- TLS dùng cả hai: bất đối xứng để thống nhất một key chung, rồi đối xứng để mã hoá dữ liệu.

*AEAD*
- *Plaintext* là dữ liệu gốc, *ciphertext* là dữ liệu sau khi mã hoá.
- *AEAD* (Authenticated Encryption with Associated Data) vừa mã hoá vừa phát hiện ciphertext bị
  sửa. Ví dụ: AES-GCM, XChaCha20-Poly1305.
- *Nonce* là giá trị dùng một lần, truyền vào mỗi lần mã hoá để hai lần mã hoá cùng dữ liệu ra
  kết quả khác nhau.
- ⚠️ AES-GCM: nonce **không bao giờ được lặp** với cùng một key.
  - Lặp nonce là phá cả bí mật lẫn toàn vẹn: lộ quan hệ giữa hai plaintext, và kẻ tấn công giả được
    ciphertext hợp lệ.
  - Nonce của AES-GCM dài 96 bit. Sinh ngẫu nhiên thì có giới hạn số lần mã hoá mỗi key trước khi
    xác suất trùng thành đáng kể.
  - XChaCha20 có nonce 192 bit, sinh ngẫu nhiên thoải mái hơn nhiều.
- ⚠️ Các mode cũ:
  - *ECB* mã hoá từng khối độc lập, khối giống nhau cho ra ciphertext giống nhau, nên lộ cấu trúc
    dữ liệu.
  - *CBC* không kèm MAC dễ bị *padding oracle*: server báo lỗi "padding sai" khác lỗi khác, kẻ tấn
    công dùng điều đó để giải mã từng byte.

*KMS và envelope encryption*
- *KMS* (Key Management Service, ví dụ AWS KMS) và *HSM* (Hardware Security Module) giữ key trong
  phần cứng hoặc dịch vụ riêng, key không bao giờ rời ra ngoài.
- *Envelope encryption* dùng hai tầng key:
  - *KEK* (Key Encryption Key): nằm trong KMS/HSM, không ra ngoài.
  - *DEK* (Data Encryption Key): sinh ngẫu nhiên cho mỗi bản ghi hoặc file.
- Quy trình mã hoá:
  1. Sinh DEK ngẫu nhiên.
  2. Dùng DEK mã hoá dữ liệu, ngay trong app.
  3. Gọi KMS dùng KEK mã hoá DEK.
  4. Lưu DEK đã mã hoá cạnh dữ liệu đã mã hoá. Xoá DEK gốc khỏi memory.
- Giải mã thì ngược lại: gửi DEK đã mã hoá cho KMS giải, rồi dùng DEK giải dữ liệu.
- Lợi ích:
  - Ít gọi KMS: dữ liệu lớn không phải gửi qua KMS.
  - Rotate KEK không phải mã hoá lại dữ liệu, chỉ mã hoá lại các DEK.
  - Phân quyền và audit tập trung ở KMS.

*Key rotation*
- Key có version. Ciphertext ghi kèm version của key đã dùng.
- Khi có key mới: mã hoá mới bằng key mới, dữ liệu cũ vẫn giải được bằng key cũ, và được mã hoá
  lại dần ở background.

*Encryption at rest không đủ*
- *Encryption at rest* của disk hoặc DB chống mất ổ đĩa hoặc lộ file backup.
- Nó **không** chống kẻ đã vào được app, vì app đọc DB thì DB tự giải mã.
- Field cực nhạy cảm thì mã hoá ở tầng ứng dụng.

*Tìm kiếm trên field đã mã hoá*
- Vấn đề: AEAD cho ra ciphertext khác nhau mỗi lần, nên không `WHERE cccd = ?` được.
- *Blind index*: lưu thêm một cột HMAC của giá trị đã chuẩn hoá (bỏ khoảng trắng, viết thường), dùng
  key riêng. Tìm kiếm bằng cách tính HMAC của giá trị cần tìm.
- ⚠️ Blind index lộ tần suất: nhiều dòng cùng HMAC nghĩa là cùng giá trị.
  - Với giá trị có ít khả năng (như giới tính), blind index vô nghĩa, đoán ra ngay.

*mTLS*
- *mTLS* (mutual TLS): cả client và server cùng xuất trình certificate. Dùng giữa các service khi
  mạng nội bộ không tin được.

**Đọc**
- *Serious Cryptography*: ch.4 (block cipher modes), ch.8 (authenticated encryption)
- AWS KMS: [Envelope encryption](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html#enveloping)
- OWASP: [Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html)
- [Google Tink](https://developers.google.com/tink): xem cách một thư viện cấp cao thiết kế API để khó dùng sai
- [CipherSweet](https://ciphersweet.paragonie.com/) (Paragon IE): blind index cho PHP, đọc phần giải thích thiết kế

**Nắm chắc khi**
- [ ] Vẽ được envelope encryption và luồng rotate KEK
- [ ] Thiết kế được cách lưu số CCCD có tìm kiếm chính xác và rotate key (bài tập 4)
- [ ] Giải thích được vì sao "DB đã bật encryption at rest" không trả lời được câu hỏi "dữ liệu nhạy cảm có được bảo vệ không"

#### 3.4 Secret và supply chain

**Vì sao cần học:** Lộ secret (commit `.env`, key AWS lên GitHub) và dependency bị chèn mã độc là
hai nguồn sự cố lớn hiện nay. Supply chain đã thành mục A03 của OWASP Top 10:2025. Câu hay bị hỏi:
"lỡ push key AWS lên repo public thì làm gì, theo thứ tự nào".

**Học gì**

*Lưu secret*
- *Secret* là mọi thứ cấp quyền truy cập: password DB, API key, `APP_KEY`, private key.
- ⚠️ Không hard-code trong code, không commit `.env`.
- Biến môi trường (env var) là mức tối thiểu.
  - ⚠️ Env var vẫn lộ qua `phpinfo()`, crash dump, `/proc/<pid>/environ`, trang debug.
- *Secret manager* (Vault, AWS Secrets Manager, GCP Secret Manager):
  - Quyền theo từng service, có audit ai đọc secret nào.
  - Hỗ trợ rotation.
  - *Dynamic secret*: Vault sinh credential DB ngắn hạn cho từng lần xin, hết hạn tự thu hồi.
- Rotation không downtime: hệ thống chấp nhận cả secret cũ và mới trong giai đoạn chuyển.
- Dùng *IAM role* (quyền gắn với danh tính trên cloud, không cần key) hoặc *workload identity* (danh tính gắn với máy hay pod, cloud tự cấp credential
  ngắn hạn) thay cho access key dài hạn.

*Khi secret lỡ bị commit*
- ⚠️ Coi như **đã lộ**. Bot quét GitHub public tìm key trong vài phút.
- Thứ tự xử lý:
  1. Thu hồi key cũ và thay key mới.
  2. Xem log sử dụng key để biết đã bị dùng chưa, dùng vào việc gì.
  3. Rồi mới dọn lịch sử git (`git filter-repo`).
  - Dọn lịch sử trước là sai thứ tự: key vẫn còn hiệu lực và có thể đã bị sao chép.
- Phòng ngừa:
  - Pre-commit hook quét secret trước khi commit.
  - Secret scanning trong CI (gitleaks, GitHub push protection).

*Supply chain (A03:2025)*
- *Supply chain*: mọi thứ bạn không tự viết nhưng chạy trong sản phẩm, như package Composer/npm,
  base image, công cụ build.
- Kiểm tra lỗ hổng đã biết:
  - `composer audit`, `npm audit`, `govulncheck`.
  - Dependabot hoặc Renovate tự mở PR nâng version.
- Commit lockfile (`composer.lock`) để build tái lập, lần build nào cũng ra đúng một bộ version.
- ⚠️ Các kiểu tấn công:
  - *Typosquatting*: package tên gần giống package thật (`larvel/framework`).
  - *Dependency confusion*: package nội bộ tên `acme/utils`, kẻ tấn công đăng package cùng tên lên
    registry public, trình cài đặt lấy nhầm bản public.
  - Maintainer bị chiếm tài khoản, đẩy version mới có mã độc.
  - Package bị chèn mã độc qua chính pipeline CI của nó.
- *SBOM* (Software Bill of Materials, định dạng SPDX hoặc CycloneDX): danh sách mọi thành phần và
  version trong sản phẩm. Khi có CVE mới, tra SBOM là biết ngay mình có bị ảnh hưởng không.
- Ký artifact hoặc image (Sigstore/cosign) để chứng minh nó được build từ pipeline của bạn. *SLSA*
  là khung các level đảm bảo cho quá trình build, cần biết ở mức khái niệm.
- Base image tối giản, quét image (Trivy). Xem [19-devops-cloud.md](19-devops-cloud.md).

**Đọc**
- OWASP: [Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [OWASP Top 10:2025 A03 Software Supply Chain Failures](https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/)
- [SLSA](https://slsa.dev/): trang "About" và các level
- [CycloneDX](https://cyclonedx.org/), [Sigstore](https://www.sigstore.dev/)
- [gitleaks](https://github.com/gitleaks/gitleaks), GitHub: [Secret scanning](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning)

**Nắm chắc khi**
- [ ] Kể được từng bước xử lý khi access key AWS bị push lên repo public, theo đúng thứ tự
- [ ] Giải thích được dependency confusion và cách chặn với Composer (repository nội bộ, `canonical`)
- [ ] Nói được SBOM giúp gì trong 24 giờ đầu sau khi một CVE lớn được công bố

#### 3.5 Dữ liệu cá nhân và pháp lý

**Vì sao cần học:** Luật Bảo vệ dữ liệu cá nhân của Việt Nam có hiệu lực từ 01/01/2026, và PII lọt
qua log, backup, môi trường staging là chuyện rất thường. Senior được hỏi "xoá dữ liệu một user
thì phải xoá ở đâu", "log thế nào để không lộ PII".

**Học gì**

*PII và phân loại*
- *PII* (Personally Identifiable Information): dữ liệu xác định được một người.
  - Thông thường: tên, email, SĐT, địa chỉ, số CCCD, ngày sinh, IP.
  - Nhạy cảm (Nghị định 356/2025/NĐ-CP Điều 4): sức khoẻ, sinh trắc học, vị trí xác định qua dịch vụ
    định vị, thông tin tài chính và lịch sử giao dịch tại tổ chức tín dụng, trung gian thanh toán...
- *Data minimization*: chỉ thu thập và giữ dữ liệu thật sự cần.
- Phân loại dữ liệu theo mức: public, internal, confidential, restricted. Mỗi mức có quy tắc truy
  cập và lưu trữ riêng.

*Masking trong log*
- ⚠️ Không log password, token, OTP, số thẻ, header `Authorization`, cookie. Che bớt email, SĐT
  (`ng***@gmail.com`).
- Làm ở tầng logger thay vì trông vào từng dev nhớ. Ví dụ: Monolog processor lọc field trước khi ghi.
- Các nơi PII hay lọt ngoài DB chính:
  - Log.
  - Backup.
  - Data warehouse.
  - Staging copy từ production. Dữ liệu cho dev và test phải được ẩn danh hoá.

*Quyền truy cập và audit log*
- Support chỉ xem những trường cần cho công việc.
- Truy cập DB production qua *bastion* (máy trung gian duy nhất được vào), có phê duyệt, mỗi người
  một tài khoản riêng.
- *Audit log* ghi: ai, làm gì, trên đối tượng nào, lúc nào, từ đâu, giá trị trước và sau.
  - Append-only (chỉ ghi thêm, không sửa xoá), tách quyền với người vận hành.
  - Bản thân audit log cũng chứa PII, cần bảo vệ như dữ liệu chính.

*Xoá dữ liệu*
- Phải xoá ở mọi nơi: DB chính, cache, search index, object storage, dữ liệu đã gửi bên thứ ba.
- Backup: không sửa được từng dòng, nên để backup hết hạn theo vòng đời.
- Phần luật bắt buộc giữ (ví dụ hoá đơn) thì giữ, phần còn lại ẩn danh hoá.
- *Crypto-shredding*: mỗi user một key mã hoá. Xoá key là dữ liệu của user đó không đọc được nữa,
  kể cả bản nằm trong backup.

*Pháp lý, mức "biết tồn tại"*
- GDPR (EU) áp dụng cả với công ty ở Việt Nam nếu chào bán hàng hoá, dịch vụ cho người ở EU hoặc
  theo dõi hành vi của họ trong EU (Art. 3(2)).
- Việt Nam: **Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15**, hiệu lực từ 01/01/2026.
  Nghị định 356/2025/NĐ-CP (31/12/2025) quy định chi tiết, và theo Điều 42 của nó thì Nghị định
  13/2023/NĐ-CP hết hiệu lực từ 01/01/2026.
- Ý chung của các luật:
  - Có căn cứ hoặc sự đồng ý khi xử lý dữ liệu.
  - Quyền của chủ thể dữ liệu: biết, đồng ý, truy cập, sửa, xoá.
  - Thông báo khi có sự cố lộ dữ liệu.
  - Lưu ý khi chuyển dữ liệu ra nước ngoài.
- Chi tiết điều khoản là việc của pháp chế. Kỹ sư cần biết để thiết kế hệ thống đáp ứng được.

**Đọc**
- OWASP: [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) (mục data to exclude)
- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://chinhphu.vn/?pageid=27160&docid=214590&classid=1&typegroupid=3): lướt mục lục, đọc Điều 4 (quyền và nghĩa vụ của chủ thể dữ liệu, trong Chương I)
- [GDPR: Art. 17 Right to erasure](https://gdpr-info.eu/art-17-gdpr/) và [Art. 33 Notification of breach](https://gdpr-info.eu/art-33-gdpr/)

**Nắm chắc khi**
- [ ] Liệt kê được mọi nơi dữ liệu của một user nằm trong hệ thống của mình, và cách xoá ở từng nơi
- [ ] Cấu hình được Monolog processor che field nhạy cảm và chứng minh bằng log thật
- [ ] Nói đúng tên, số hiệu và ngày hiệu lực của luật bảo vệ dữ liệu cá nhân Việt Nam

#### 3.6 Nguyên tắc, threat modeling, phát hiện

**Vì sao cần học:** Ở level senior, câu hỏi chuyển từ "chặn lỗ hổng X thế nào" sang "làm sao biết
tính năng mới có những rủi ro gì" và "bị tấn công thì phát hiện bằng cách nào". Threat modeling là
kỹ năng senior được kỳ vọng dẫn dắt trong buổi review thiết kế.

**Học gì**

*Hai nguyên tắc nền*
- *Least privilege* (quyền tối thiểu): mỗi thành phần chỉ có đúng quyền cần dùng.
  - User DB của app không có quyền `DROP`, `GRANT`.
  - IAM role của mỗi service chỉ truy cập đúng bucket, queue nó cần.
  - Token có scope hẹp.
  - Tài khoản admin tách khỏi tài khoản dùng hằng ngày.
- *Defense in depth* (phòng thủ nhiều lớp): nhiều lớp độc lập, một lớp hỏng thì lớp khác vẫn chặn.
  - Ví dụ các lớp: WAF (*Web Application Firewall*, lọc request độc trước khi tới app),
    validate input, prepared statement, least privilege, CSP, monitoring.

*Threat modeling*
- *Threat modeling* là ngồi lại phân tích một tính năng có thể bị tấn công thế nào, trước khi code.
- Bốn câu hỏi:
  1. Đang xây gì? Vẽ *data flow* (dữ liệu đi qua đâu) và *ranh giới tin cậy* (chỗ dữ liệu đi từ
     vùng kém tin cậy sang vùng tin cậy hơn, ví dụ từ internet vào app).
  2. Cái gì có thể hỏng?
  3. Làm gì với nó?
  4. Đã làm đủ chưa?
- *STRIDE* là bộ gợi ý để trả lời câu 2, mỗi chữ một loại mối đe doạ:

  | Chữ | Mối đe doạ | Ví dụ |
  |---|---|---|
  | S, Spoofing | Giả danh | Dùng token của người khác |
  | T, Tampering | Sửa dữ liệu | Sửa giá trong request thanh toán |
  | R, Repudiation | Chối bỏ hành động | "Tôi không hề chuyển tiền", mà không có log để chứng minh |
  | I, Information disclosure | Lộ thông tin | API trả thừa field |
  | D, Denial of service | Làm sập dịch vụ | Upload ảnh khổng lồ làm nổ memory |
  | E, Elevation of privilege | Leo thang quyền | User thường gọi được API admin |

- Làm sớm khi thiết kế tính năng nhạy cảm: thanh toán, upload, tích hợp bên thứ ba.
- Ưu tiên xử lý theo khả năng xảy ra × thiệt hại.

*Logging và phát hiện (A09:2025)*
- Log các sự kiện bảo mật: login thất bại, đổi quyền, đổi password, truy cập bị từ chối.
- Cảnh báo khi có bất thường (ví dụ số login thất bại tăng vọt).
- Có quy trình phản ứng sự cố ([18-reliability-observability.md](18-reliability-observability.md)).

*Xử lý lỗi đúng (A10:2025)*
- *Fail closed*: khi có lỗi thì từ chối, không cho qua.
- Không nuốt exception.
- Không lộ chi tiết lỗi ra ngoài.

**Đọc**
- [Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/)
- OWASP: [Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html)
- Microsoft: [Threat Modeling Tool threats (STRIDE)](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- *Threat Modeling: Designing for Security* (Adam Shostack; Wiley 2014): phần I
- [OWASP Top 10:2025 A10 Mishandling of Exceptional Conditions](https://owasp.org/Top10/2025/A10_2025-Mishandling_of_Exceptional_Conditions/)

**Nắm chắc khi**
- [ ] Làm được threat model STRIDE cho một tính năng trong 30 phút, có data flow và ranh giới tin cậy (bài tập 5)
- [ ] Chỉ ra được 3 chỗ trong code thật đang fail open khi có exception

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Lưu password an toàn thế nào? Vì sao không dùng SHA-256?** (1.1)
- Ý phải có: hàm chậm có salt (argon2id, bcrypt); SHA-256 quá nhanh nên brute force bằng GPU rẻ; salt chống rainbow table
- Điểm cộng: cost theo phần cứng, rehash khi đăng nhập, giới hạn 72 byte của bcrypt, PHP 8.4 tăng cost mặc định lên 12, pepper và cái giá của nó
- Red flag: "mã hoá password bằng AES"

**2. Prepared statement chống SQL injection như thế nào?** (1.3)
- Ý phải có: câu lệnh và dữ liệu gửi riêng, dữ liệu không được parse như SQL
- Điểm cộng: tên cột và `ORDER BY` không bind được nên phải whitelist; `whereRaw` vẫn bị inject; emulate prepare của PDO

**3. XSS và CSRF khác nhau thế nào? Chống mỗi cái ra sao?** (1.3)
- Ý phải có: XSS chạy script của kẻ xấu trong trang của bạn; CSRF lợi dụng trình duyệt tự gửi cookie. XSS: escape theo ngữ cảnh + CSP. CSRF: token, Fetch Metadata/`Origin`, `SameSite`
- Điểm cộng: có XSS thì mọi biện pháp chống CSRF đều vô nghĩa
- Red flag: "dùng HTTPS là chống được"

**4. Authentication và authorization khác nhau thế nào? IDOR là gì? Dùng UUID có đủ không?** (1.5)
- Ý phải có: bạn là ai so với bạn được làm gì; IDOR là thiếu kiểm tra quyền trên object; UUID chỉ làm khó đoán
- Điểm cộng: query luôn có scope theo user; Policy; test tự động chéo user

**5. Hash, encrypt, encode, sign khác nhau thế nào? Khi nào dùng HMAC?** (1.4)
- Ý phải có: bảng phân biệt theo đảo ngược được không và cần key gì; HMAC cho toàn vẹn và xác thực nguồn (webhook)
- Red flag: "base64 là mã hoá"

**6. Cookie có những thuộc tính bảo mật nào? `SameSite` có những giá trị nào?** (1.2)
- Ý phải có: `HttpOnly`, `Secure`, `SameSite` (Strict/Lax/None), `Domain`, `Path`, prefix `__Host-`
- Điểm cộng: Lax mặc định chỉ có ở Chrome/Edge và có ngoại lệ Lax+POST 2 phút, nên phải khai rõ; same-site khác same-origin

### 🟡 Mid

**7. Session hay JWT cho web app? Cho mobile app?** (2.2)
- Ý phải có: web một domain dùng session cookie; mobile hoặc nhiều service verify độc lập dùng access token ngắn + refresh token
- Điểm cộng: revocation làm mất tính stateless; BFF cho SPA theo RFC 10017; Sanctum SPA cookie so với Sanctum token
- Red flag: "JWT vì stateless nên scale tốt hơn" mà không nói tới revocation

**8. User đổi mật khẩu, làm sao đăng xuất họ khỏi mọi thiết bị khi dùng JWT?** (2.2)
- Ý phải có: thu hồi mọi refresh token; `token_version` hoặc denylist; access token ngắn thì chấp nhận trễ vài phút
- Điểm cộng: nói rõ độ trễ tối đa và vì sao chấp nhận được; thông báo email

**9. HS256 và RS256 khác nhau thế nào? `alg: none` và algorithm confusion là gì?** (2.1)
- Ý phải có: secret chung so với cặp khoá; server phải cố định thuật toán, không tin header
- Điểm cộng: `kid`/`jku` là input không tin được; kiểm tra `aud`, `typ`; RFC 8725

**10. Authorization code + PKCE hoạt động thế nào? Vì sao implicit flow bị bỏ? ID token khác access token ở đâu?** (2.3)
- Ý phải có: luồng redirect, đổi code qua back-channel, `code_verifier`/`code_challenge`; implicit để token trên URL; ID token cho client, access token cho resource server
- Điểm cộng: RFC 9700 khuyến nghị PKCE cả cho confidential client; `redirect_uri` so khớp chính xác; OAuth 2.1 vẫn là draft
- Red flag: nhầm OAuth là giao thức đăng nhập

**11. Refresh token rotation và reuse detection hoạt động thế nào? Xử lý request refresh song song?** (2.2)
- Ý phải có: token mới mỗi lần, family, reuse thì thu hồi cả family
- Điểm cộng: grace period ngắn hoặc client khoá việc refresh; lưu hash; hạn tuyệt đối

**12. SSRF là gì, chặn thế nào?** (2.6)
- Ý phải có: server bị lừa gọi vào nội bộ/metadata cloud; resolve rồi kiểm tra IP, chặn dải private, whitelist
- Điểm cộng: redirect, DNS rebinding, IPv6, IMDSv2, egress proxy; SSRF nằm trong A01 ở bản 2025
- Red flag: chặn bằng regex trên chuỗi URL

**13. Kể OWASP Top 10 bản mới nhất.** (2.6)
- Ý phải có: 10 mục của bản 2025 theo đúng thứ tự tương đối
- Điểm cộng: nói được thay đổi so với 2021 (Supply Chain lên A03, SSRF gộp vào A01, A10 mới về xử lý lỗi); kể thêm vài mục API Top 10
- Red flag: đọc danh sách 2021 mà không biết đã có bản mới

**14. Passkey khác password + OTP ở điểm nào?** (2.4)
- Ý phải có: cặp khoá, server chỉ lưu public key; chữ ký gắn origin nên chống phishing
- Điểm cộng: OTP bị proxy phishing (AiTM) lấy được; synced và device-bound passkey; luồng khôi phục là điểm yếu

**15. Laravel: dùng Sanctum hay Passport? Sanctum SPA hoạt động thế nào?** (2.8)
- Ý phải có: Sanctum cho SPA cùng domain (session cookie + CSRF) và token đơn giản; Passport khi cần OAuth2 server cho bên thứ ba
- Điểm cộng: SPA phải cùng top-level domain; gọi `/sanctum/csrf-cookie` trước; token Sanctum lưu hash, có abilities và expiration

**16. `APP_KEY` của Laravel bị lộ thì sao?** (2.8)
- Ý phải có: giả mạo cookie/session, giải mã dữ liệu encrypted cast, ký signed URL
- Điểm cộng: rotate bằng `APP_PREVIOUS_KEYS`, dữ liệu encrypted cần mã hoá lại; lịch sử RCE qua cookie serialize; kiểm tra `APP_DEBUG`

**17. Cấu hình CORS `Access-Control-Allow-Origin: *` có nguy hiểm không?** (2.7)
- Ý phải có: `*` không đi kèm credentials được; nguy hiểm thật là phản chiếu mọi Origin kèm `Allow-Credentials: true`
- Điểm cộng: CORS không chặn request tới server nên không thay CSRF protection

### 🔴 Senior

**18. Thiết kế chống CSRF cho app có cả Blade, SPA cùng domain và mobile.** (1.2, 2.7, 2.8)
- Ý phải có: web và SPA dùng session cookie + token/Fetch Metadata; mobile dùng Bearer token nên không cần CSRF
- Điểm cộng: `PreventRequestForgery` của Laravel 13 kiểm tra `Sec-Fetch-Site` rồi mới fallback token; không dựa vào Lax mặc định; webhook verify HMAC thay vì bỏ CSRF tuỳ tiện
- Red flag: "đã có SameSite rồi, không cần token"

**19. Access token bị đánh cắp và dùng lại từ máy khác. Thiết kế để giảm thiệt hại.** (3.1)
- Ý phải có: token ngắn, sender-constrained token (DPoP, mTLS), BFF để token không nằm trong trình duyệt
- Điểm cộng: nói được cái giá của DPoP (client ký mỗi request, nonce phía server); PAR; phát hiện bất thường

**20. Thiết kế cô lập dữ liệu cho SaaS multi-tenant.** (3.2)
- Ý phải có: chọn mức cô lập theo yêu cầu khách và chi phí; `tenant_id` từ context đã xác thực; global scope
- Điểm cộng: RLS ở Postgres; cache key, job, export, search index; test chéo tenant; tenant lớn tách silo
- Red flag: `tenant_id` lấy từ query string

**21. Envelope encryption là gì, vì sao dùng? Tìm kiếm chính xác trên cột đã mã hoá thế nào?** (3.3)
- Ý phải có: KEK trong KMS, DEK cho dữ liệu, lưu DEK đã mã hoá
- Điểm cộng: rotate KEK không mã hoá lại dữ liệu; cache DEK và cái giá; crypto-shredding; blind index bằng HMAC với key riêng và rủi ro lộ tần suất

**22. Dev dán access key AWS vào repo public 10 phút rồi xoá. Làm gì?** (3.4)
- Ý phải có: vô hiệu key ngay, xem CloudTrail trong khoảng lộ, dọn tài nguyên lạ; xoá commit không đủ
- Điểm cộng: chuyển sang role thay key dài hạn; push protection; postmortem không đổ lỗi cá nhân
- Red flag: "force push xoá commit là xong"

**23. Log cho thấy hàng nghìn IP khác nhau thử đăng nhập, mỗi IP vài lần.** (2.9)
- Ý phải có: credential stuffing; rate limit theo IP vô dụng; kiểm tra password đã lộ, MFA/CAPTCHA theo rủi ro
- Điểm cộng: thông báo user bị đăng nhập bất thường; buộc reset với tài khoản bị trúng; metric tỉ lệ login thất bại

**24. Tính năng "nhập URL ảnh đại diện", pentest báo đọc được credential từ metadata cloud.** (2.6)
- Ý phải có: SSRF; chặn IP private/link-local sau resolve, xử lý redirect, IMDSv2
- Điểm cộng: thu hồi credential đã có thể lộ; egress proxy; chạy tính năng tải URL trong môi trường tách mạng

**25. Upload avatar: có người up file `.php` đổi tên thành `.jpg` và chạy được.** (2.6)
- Ý phải có: web server thực thi theo pattern tên file; kiểm tra magic bytes, re-encode, tên ngẫu nhiên
- Điểm cộng: lưu object storage/domain riêng, cấu hình không thực thi trong thư mục upload, kiểm tra xem đã bị cài webshell chưa

**26. SaaS nhiều tenant, một khách thấy hoá đơn của khách khác trong một lần export.** (3.2, 3.5)
- Ý phải có: tìm chỗ mất `tenant_id` (job nền, cache key, query raw); sửa và thêm test chéo tenant
- Điểm cộng: đánh giá phạm vi lộ, quy trình thông báo sự cố theo luật dữ liệu cá nhân, RLS làm lớp thứ hai

**27. Làm threat model cho tính năng thanh toán thế nào?** (3.6)
- Ý phải có: vẽ data flow và ranh giới tin cậy, đi qua STRIDE, ưu tiên theo khả năng × thiệt hại
- Điểm cộng: webhook giả mạo, replay, idempotency, số tiền do client gửi, race condition khi trừ tiền; ghi lại quyết định

**28. Bảo mật API thế nào?** (2.6, 2.9)
- Ý phải có: đi theo OWASP API Top 10: BOLA, mass assignment, resource consumption, inventory API cũ
- Điểm cộng: rate limit nhiều lớp, logging và phát hiện, threat model cho luồng nhạy cảm, sender-constrained token cho API quan trọng
- Red flag: "HTTPS và JWT là đủ"

---

## Bài tập tự làm

1. **Luồng đăng nhập.** Thiết kế cho một SPA (cùng domain với API) và một mobile app:
   - Loại token, thời hạn, nơi lưu từng loại
   - Luồng refresh có rotation và reuse detection
   - Đăng xuất mọi thiết bị
   - So sánh với phương án BFF và Sanctum SPA cookie
2. **OWASP API Top 10.** Liệt kê 10 endpoint của một ứng dụng bạn từng làm. Với mỗi endpoint ghi rủi ro theo OWASP API Top 10 và cách kiểm tra quyền hiện tại.
3. **Quên mật khẩu.** Viết pseudo-code cho endpoint "quên mật khẩu" và "đặt lại mật khẩu", chỉ rõ chỗ:
   - Chống account enumeration
   - Chống brute force token
   - Chống host header injection
   - Thu hồi session sau khi đổi
4. **Mã hoá số CCCD.** Thiết kế cơ chế lưu số CCCD trong MySQL có hỗ trợ tìm kiếm chính xác và rotate key. Ghi rõ key nằm ở đâu, bảng có cột gì, luồng rotate.
5. **Threat model.** Làm STRIDE cho tính năng "upload file đính kèm vào đơn hàng": vẽ data flow, liệt kê mối đe doạ và biện pháp.
6. **PHP/Laravel.** Trong một project Laravel (có thể là project mới):
   - Tạo một endpoint có IDOR, viết test chứng minh, rồi sửa bằng Policy.
   - Tạo một model dùng `$guarded = []`, khai thác mass assignment để tự nâng quyền, rồi sửa.
   - Bật `APP_DEBUG=true`, gây lỗi và liệt kê những gì trang lỗi làm lộ.
   - Chạy `composer audit` và giải thích từng advisory tìm thấy.

> Nộp bài vào đây để được review.
