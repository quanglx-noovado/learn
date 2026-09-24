# 10. Bảo mật

> [← Mục lục](README.md) · Phạm vi: password, session/JWT, OAuth2/OIDC, MFA, authorization, OWASP Top 10 và OWASP API Top 10, rate limit và bot, crypto thực dụng, secret, supply chain, dữ liệu cá nhân, threat modeling.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Password**
- [ ] 🟢 bcrypt/argon2, vì sao không MD5/SHA
- [ ] 🟢 Salt, 🟡 pepper, cost factor, rehash khi tăng cost
- [ ] 🟡 Timing attack, constant-time compare
- [ ] 🟡 Password policy theo NIST: độ dài, không bắt đổi định kỳ, chặn password đã lộ
- [ ] 🟡 Quên mật khẩu: token một lần, hết hạn nhanh

**Authentication**
- [ ] 🟢 Session và JWT: khác nhau, chọn khi nào
- [ ] 🟡 JWT sâu: cấu trúc, HS256 vs RS256, `alg: none`, algorithm confusion, `kid`, claim cần kiểm tra
- [ ] 🟡 Revocation, refresh token rotation + reuse detection
- [ ] 🟡 Nơi lưu token, cookie attributes (`HttpOnly`, `Secure`, `SameSite`, `__Host-`)
- [ ] 🟡 OAuth2: vai trò, các flow, authorization code + PKCE, vì sao bỏ implicit, client credentials
- [ ] 🟡 OIDC: ID token vs access token
- [ ] 🔴 SSO, SAML đại ý
- [ ] 🟡 MFA: TOTP, WebAuthn, passkey
- [ ] 🟢 API key: sinh, lưu hash, prefix, scope, rotate

**Authorization**
- [ ] 🟢 Authentication vs authorization
- [ ] 🟡 RBAC, ABAC, 🔴 ReBAC
- [ ] ⚠️ IDOR / BOLA, BFLA
- [ ] 🟡 Kiểm tra quyền ở tầng nào
- [ ] 🔴 Multi-tenant isolation

**Lỗ hổng web và API**
- [ ] 🟡 OWASP Top 10 và OWASP API Security Top 10 (kể tên được)
- [ ] 🟢 SQL injection, 🟢 XSS + CSP, 🟢 CSRF
- [ ] 🟡 SSRF, XXE, path traversal, command injection
- [ ] 🟡 Insecure deserialization, mass assignment, open redirect
- [ ] 🟡 File upload, clickjacking
- [ ] 🟡 Security headers: HSTS, CSP, `X-Content-Type-Options`, `frame-ancestors`, `Referrer-Policy`

**Lạm dụng**
- [ ] 🟡 Rate limiting, brute force, credential stuffing
- [ ] 🟡 Account enumeration
- [ ] 🔴 Bot, CAPTCHA, lạm dụng luồng nghiệp vụ

**Crypto thực dụng**
- [ ] 🟢 Hash vs encrypt vs encode vs sign
- [ ] 🟡 Symmetric (AES-GCM) vs asymmetric, HMAC
- [ ] 🔴 KMS, envelope encryption, key rotation
- [ ] 🟡 TLS (chi tiết ở [02-networking.md](02-networking.md)), encryption at rest
- [ ] ⚠️ Không tự chế crypto

**Secret và supply chain**
- [ ] 🟢 Secret trong env, secret manager, 🟡 rotation
- [ ] ⚠️ Secret lỡ commit
- [ ] 🟡 Dependency audit, lockfile, 🔴 SBOM

**Dữ liệu cá nhân**
- [ ] 🟡 PII, masking trong log, quyền truy cập dữ liệu
- [ ] 🟡 Audit log, xoá dữ liệu
- [ ] 🟢 Biết tồn tại GDPR và Nghị định 13/2023/NĐ-CP

**Nguyên tắc**
- [ ] 🟡 Least privilege, defense in depth
- [ ] 🔴 Threat modeling cơ bản (STRIDE)

## Chi tiết

### Password

- [ ] Hash password
  - Dùng hàm **chậm có chủ đích** và có salt: argon2id (OWASP khuyến nghị đầu tiên), bcrypt, scrypt; PBKDF2 khi cần chuẩn FIPS
  - ⚠️ Không MD5/SHA-1/SHA-256 trần: quá nhanh, GPU thử hàng tỷ lần mỗi giây. "Nhanh" là ưu điểm của hash thường nhưng là nhược điểm khi hash password
  - Salt: ngẫu nhiên, riêng từng user, lưu cùng hash (không bí mật). Chống rainbow table và làm hai user cùng password có hash khác nhau
  - Pepper: secret chung lưu **ngoài DB** (secret manager), trộn vào (thường HMAC trước khi hash). DB lộ mà pepper không lộ thì hash vô dụng với kẻ tấn công. Đổi lại: mất pepper là mất khả năng verify mọi password
  - Cost factor: chỉnh sao cho một lần hash tốn cỡ vài chục tới vài trăm ms trên server của bạn; tham số cụ thể theo OWASP Password Storage Cheat Sheet hiện hành
  - Khi tăng cost/đổi thuật toán: kiểm tra lúc user đăng nhập thành công, rehash và lưu lại (`password_needs_rehash` trong PHP)
  - ⚠️ bcrypt chỉ dùng 72 byte đầu của input; password dài hơn bị cắt âm thầm
  - ⚠️ Hash chậm là mục tiêu DoS: giới hạn độ dài tối đa hợp lý và rate limit endpoint login

  ```php
  $hash = password_hash($password, PASSWORD_ARGON2ID); // hoặc PASSWORD_DEFAULT (bcrypt)
  if (password_verify($input, $hash)) {
      if (password_needs_rehash($hash, PASSWORD_ARGON2ID)) { /* lưu hash mới */ }
  }
  ```

  - **Đối chiếu**: PHP `password_hash` (cost mặc định của bcrypt đã được tăng ở PHP 8.4, kiểm tra lại theo phiên bản bạn dùng); Java: Spring Security `BCryptPasswordEncoder` / `Argon2PasswordEncoder`; Go: `golang.org/x/crypto/bcrypt`, `golang.org/x/crypto/argon2`
- [ ] 🟡 Timing attack
  - So sánh chuỗi thông thường dừng ở byte khác đầu tiên; đo thời gian phản hồi có thể dò ra từng byte của token/chữ ký
  - Dùng constant-time compare cho token, HMAC, API key: PHP `hash_equals`, Go `crypto/subtle.ConstantTimeCompare` hoặc `hmac.Equal`, Java `MessageDigest.isEqual`
  - `password_verify` đã tự làm đúng
  - Login: user không tồn tại vẫn nên chạy một lần hash giả, để thời gian phản hồi không lộ email nào có tài khoản
- [ ] 🟡 Password policy hiện đại (NIST SP 800-63B)
  - Ưu tiên **độ dài** hơn độ phức tạp; cho phép password dài (ít nhất 64 ký tự), mọi ký tự kể cả Unicode và khoảng trắng
  - Không bắt quy tắc "có chữ hoa, số, ký tự đặc biệt"; không bắt đổi định kỳ, **chỉ** bắt đổi khi có dấu hiệu lộ
  - Chặn password nằm trong danh sách đã lộ/phổ biến (ví dụ API k-anonymity của Have I Been Pwned)
  - Cho paste (để dùng password manager); không dùng câu hỏi bí mật, không gợi ý password
  - Độ dài tối thiểu: 8 là mức cũ; bản sửa đổi mới của NIST yêu cầu dài hơn khi password là yếu tố xác thực duy nhất (kiểm tra lại con số theo bản hiện hành)
- [ ] 🟡 Quên mật khẩu
  - Token ngẫu nhiên đủ dài (CSPRNG), chỉ lưu **hash** của token, dùng một lần, hết hạn ngắn (vài chục phút)
  - Thông báo giống nhau dù email có tồn tại hay không
  - Đổi password xong: vô hiệu mọi session/refresh token khác, gửi email báo
  - ⚠️ Link reset dựng từ header `Host` của request có thể bị đầu độc (host header injection): dùng domain cấu hình cứng

### Authentication: session và JWT

- [ ] Session
  - Server lưu state (Redis/DB), cookie chỉ chứa session id ngẫu nhiên
  - Thu hồi dễ (xoá session), đếm/đăng xuất thiết bị dễ
  - Scale: session store dùng chung, không dính sticky session
  - ⚠️ Session fixation: **đổi session id sau khi login** (`session_regenerate_id(true)` trong PHP; Spring Security làm mặc định)
- [ ] 🟡 JWT
  - Cấu trúc: `base64url(header).base64url(payload).signature`. ⚠️ Payload chỉ **encode**, ai cũng đọc được; không đặt dữ liệu nhạy cảm. Cần giấu thì dùng JWE
  - HS256: HMAC với **một secret chung**; ai verify được cũng ký được. Hợp khi chỉ một service vừa phát vừa kiểm tra
  - RS256/ES256: ký bằng private key, verify bằng public key (công bố qua JWKS). Hợp khi nhiều service cần verify mà không được phát token
  - Claim phải kiểm tra: chữ ký, `exp`, `nbf`, `iss`, `aud` (token cho service A không được dùng ở service B), cho phép clock skew nhỏ
  - ⚠️ `alg: none`: thư viện cũ chấp nhận token không chữ ký. Phải **cố định whitelist thuật toán** phía server, không tin `alg` trong header
  - ⚠️ Algorithm confusion: server dùng RS256, kẻ tấn công gửi token HS256 ký bằng **public key** làm secret; thư viện cẩu thả verify bằng chính public key đó và chấp nhận
  - ⚠️ `kid` (key id) là input không tin được: dùng để tra key trong bảng/JWKS đã biết, không nối vào đường dẫn file hay câu SQL. Tương tự, không tự tải key từ `jku`/`x5u` trong header
- [ ] 🟡 Revocation
  - JWT stateless nên không thu hồi được trước `exp` nếu chỉ verify chữ ký
  - Cách xử lý: access token ngắn hạn (5–15 phút) + refresh token lưu server-side; denylist theo `jti` cho các token bị thu hồi (tra Redis, TTL = thời gian còn lại của token); hoặc `token_version` trong user, tăng lên khi đổi password để vô hiệu mọi token cũ
  - Nhận xét thật: khi đã tra state mỗi request thì phần lớn lợi ích "stateless" mất; hãy nói rõ trade-off
- [ ] 🟡 Refresh token rotation + reuse detection
  - Mỗi lần dùng refresh token thì cấp refresh token **mới** và vô hiệu cái cũ; các token cùng một chuỗi login thuộc một "family"
  - Nếu một refresh token **đã dùng rồi** lại được gửi lên: có kẻ đánh cắp. Thu hồi **cả family**, bắt đăng nhập lại
  - ⚠️ Client gửi song song hai request refresh (nhiều tab, mạng retry) sẽ bị báo nhầm là reuse: cho grace period ngắn hoặc để client đồng bộ việc refresh
  - Refresh token lưu **hash** trong DB, gắn thiết bị, có hạn tuyệt đối
- [ ] 🟡 Nơi lưu token phía trình duyệt

  | Nơi lưu | XSS đọc được? | CSRF? | Ghi chú |
  |---|---|---|---|
  | `localStorage` / `sessionStorage` | có | không | XSS lấy được token mang đi dùng ở nơi khác |
  | Cookie `HttpOnly` | không | có, cần chống | trình duyệt tự gửi; chống bằng `SameSite` + CSRF token |
  | Memory của JS (biến) | khó hơn | không | mất khi reload; hay dùng cho access token, refresh token nằm trong cookie `HttpOnly` |

  - ⚠️ XSS vẫn là thảm hoạ dù token nằm trong cookie `HttpOnly`: script chạy trong trang có thể gửi request thay user. `HttpOnly` chỉ chặn việc **lấy token ra ngoài**
  - Mobile: Keychain (iOS) / Keystore (Android), không lưu plain text trong storage chung
- [ ] 🟡 Cookie attributes
  - `HttpOnly`: JS không đọc được. `Secure`: chỉ gửi qua HTTPS
  - `SameSite=Lax` (mặc định của trình duyệt hiện đại khi không khai): không gửi với request cross-site trừ điều hướng top-level GET. `Strict`: không gửi cross-site. `None`: gửi mọi nơi, bắt buộc kèm `Secure`
  - `Domain`: khai thì cookie gửi cho cả subdomain (rộng hơn); không khai thì chỉ host đó. `Path`, `Max-Age`/`Expires`
  - Prefix `__Host-`: bắt buộc `Secure`, `Path=/`, không có `Domain`; chống subdomain ghi đè cookie
- [ ] 🟡 Session hay JWT
  - Web app một domain: session cookie thường đơn giản và an toàn hơn
  - Mobile / SPA gọi nhiều API, nhiều service cần verify độc lập: access token ngắn hạn (JWT) + refresh token
  - Service-to-service: JWT ký bất đối xứng hoặc mTLS

### OAuth2, OIDC, SSO, MFA, API key

- [ ] 🟡 OAuth2 là **ủy quyền** (delegated authorization), không phải giao thức đăng nhập
  - Vai trò: resource owner (user), client (app), authorization server, resource server (API)
  - Flow:

    | Flow | Dùng khi |
    |---|---|
    | Authorization code + PKCE | mọi app có user: web, SPA, mobile |
    | Client credentials | server-to-server, không có user |
    | Device authorization | TV, CLI không có trình duyệt tiện |
    | Refresh token | lấy access token mới |
    | Implicit, Password (ROPC) | ⚠️ đã bị khuyến cáo bỏ (OAuth 2.0 Security BCP, OAuth 2.1) |

  - Authorization code: trình duyệt redirect tới authorization server, user đồng ý, quay về `redirect_uri` kèm `code`; client đổi `code` lấy token qua kênh back-channel
  - PKCE: client sinh `code_verifier` ngẫu nhiên, gửi `code_challenge = BASE64URL(SHA256(code_verifier))` lúc xin code, gửi `code_verifier` lúc đổi token. Kẻ chặn được `code` không có verifier nên không đổi được. Bắt buộc với public client (SPA, mobile không giữ được secret), khuyến nghị cho cả confidential client
  - Implicit bị bỏ vì: access token trả thẳng trên URL fragment (lọt history, `Referer`, extension), không có bước back-channel, không có refresh token an toàn. PKCE giải quyết đúng lý do từng khiến người ta dùng implicit
  - Tham số `state` chống CSRF trên callback; `redirect_uri` phải so khớp **chính xác** với danh sách đăng ký (⚠️ so khớp prefix/wildcard là nguồn lỗi chiếm tài khoản kinh điển)
  - Scope giới hạn quyền của token
- [ ] 🟡 OIDC
  - Lớp authentication trên OAuth2: thêm scope `openid`, trả **ID token** (JWT chứa `sub`, `iss`, `aud`, `exp`, `nonce`)
  - ID token dành cho **client** biết user là ai; access token dành cho **resource server**. ⚠️ Không dùng ID token để gọi API
  - Discovery: `/.well-known/openid-configuration`, key qua JWKS; endpoint `userinfo`
  - `nonce` chống replay ID token
- [ ] 🔴 SSO / SAML
  - SSO: đăng nhập một lần ở Identity Provider (IdP), nhiều Service Provider (SP) tin IdP
  - SAML: chuẩn XML cũ hơn, phổ biến trong doanh nghiệp; IdP gửi assertion đã ký qua trình duyệt (POST binding)
  - ⚠️ Lỗ hổng hay gặp: XML signature wrapping, verify chữ ký nhưng đọc dữ liệu từ phần không được ký. Dùng thư viện đã kiểm chứng
  - Doanh nghiệp còn cần SCIM để tự động tạo/khoá user
- [ ] 🟡 MFA
  - TOTP (RFC 6238): secret chung, mã đổi theo bước thời gian (thường 30 giây); chấp nhận lệch ±1 bước; chống dùng lại mã vừa dùng; secret mã hoá khi lưu
  - SMS OTP: tốt hơn không có, nhưng yếu (SIM swap, chặn tin nhắn); chi tiết OTP ở [22-practical-data.md](22-practical-data.md)
  - WebAuthn / passkey: mỗi site một cặp khoá, private key nằm ở thiết bị/secure hardware; chữ ký gắn với **origin** nên chống phishing (trang giả không dùng được). Passkey là credential WebAuthn được đồng bộ giữa thiết bị
  - Recovery code dùng một lần, lưu hash
  - ⚠️ MFA fatigue: push approve liên tục cho đến khi user bấm nhầm; dùng number matching
- [ ] API key
  - Sinh bằng CSPRNG, đủ dài; có prefix nhận dạng (`sk_live_...`) để secret scanner bắt được khi lộ
  - Lưu **hash** (SHA-256 là đủ vì key ngẫu nhiên entropy cao, khác password); chỉ hiện một lần lúc tạo
  - Scope, ngày hết hạn, cho nhiều key cùng lúc để rotate không downtime, log lần dùng cuối

### Authorization

- [ ] Authentication (bạn là ai) vs authorization (bạn được làm gì)
- [ ] 🟡 Mô hình

  | Mô hình | Quyết định dựa trên | Ví dụ | Hợp khi |
  |---|---|---|---|
  | RBAC | vai trò của user | `admin`, `editor` | quyền theo chức danh, ít ngoại lệ |
  | ABAC | thuộc tính user, resource, môi trường | "sửa được đơn của chi nhánh mình, trong giờ làm việc" | quy tắc động |
  | ReBAC | quan hệ giữa các đối tượng | "xem được file nếu là thành viên folder cha" (kiểu Google Zanzibar, OpenFGA) | chia sẻ, phân cấp lồng nhau |

  - ⚠️ RBAC dễ nổ số role ("role explosion") khi thêm ngoại lệ; thường kết hợp RBAC + kiểm tra ownership
- [ ] ⚠️ IDOR / BOLA (Broken Object Level Authorization)
  - `GET /orders/124` phải kiểm tra đơn **thuộc** user hiện tại (hoặc user có quyền), không chỉ kiểm tra đã đăng nhập
  - Đứng đầu OWASP API Top 10. ID ngẫu nhiên (UUID) làm khó đoán nhưng **không thay** kiểm tra quyền
  - Cách an toàn: query luôn gắn phạm vi: `WHERE id = ? AND user_id = ?`, hoặc policy/scope của framework
  - BFLA (function level): user thường gọi được endpoint admin (`DELETE /admin/users/1`) vì chỉ ẩn nút ở UI
- [ ] 🟡 Kiểm tra quyền ở tầng nào
  - Gateway/middleware: xác thực, quyền thô (có scope không). Tầng service/domain: quyền trên từng object, vì chỉ ở đó mới biết object thuộc ai
  - ⚠️ Chỉ kiểm tra ở controller: job, CLI, GraphQL resolver, consumer từ queue đi vòng qua
  - Deny by default; tập trung logic quyền một chỗ (Laravel Policy/Gate, Spring Security `@PreAuthorize`, middleware trong Go)
- [ ] 🔴 Multi-tenant isolation
  - Tầng cô lập: DB riêng mỗi tenant > schema riêng > chung bảng có `tenant_id`. Càng chung càng rẻ, càng dễ lộ chéo
  - Chung bảng: `tenant_id` lấy từ token/session, **không** từ tham số request; global scope/filter tự thêm điều kiện; Postgres Row-Level Security làm lớp phòng thủ thứ hai
  - ⚠️ Chỗ hay lộ: cache key thiếu tenant, file storage chung prefix, job chạy nền mất context tenant, báo cáo/export, search index
  - Test tự động "tenant A không đọc được dữ liệu tenant B" cho mọi endpoint quan trọng

### Lỗ hổng web và API

- [ ] 🟡 OWASP Top 10 (bản 2021): Broken Access Control; Cryptographic Failures; Injection; Insecure Design; Security Misconfiguration; Vulnerable and Outdated Components; Identification and Authentication Failures; Software and Data Integrity Failures; Security Logging and Monitoring Failures; SSRF. Đã có bản mới hơn với vài thay đổi thứ hạng và nhóm (supply chain được nhấn mạnh hơn); kiểm tra lại danh sách hiện hành
- [ ] 🟡 OWASP API Security Top 10 (2023): BOLA; Broken Authentication; Broken Object Property Level Authorization (mass assignment + lộ field thừa); Unrestricted Resource Consumption; BFLA; Unrestricted Access to Sensitive Business Flows; SSRF; Security Misconfiguration; Improper Inventory Management (API cũ/ẩn còn chạy); Unsafe Consumption of APIs (tin dữ liệu bên thứ ba)
- [ ] SQL injection
  - Prepared statement chặn được vì câu lệnh và dữ liệu gửi **riêng**; DB parse câu lệnh trước, dữ liệu không bao giờ được hiểu là SQL
  - ⚠️ Tên cột/bảng, `ORDER BY`, `LIMIT` không bind được: dùng whitelist. ORM có chỗ nhận raw SQL (`whereRaw`, `DB::raw`, native query) vẫn bị inject nếu nối chuỗi
  - ⚠️ PDO emulate prepares (mặc định bật với MySQL trong PHP) thay tham số ở phía client; vẫn an toàn nếu charset kết nối khai đúng, nhưng nên biết
- [ ] XSS
  - Stored (lưu DB rồi hiện cho người khác), reflected (từ URL), DOM-based (JS phía client tự chèn)
  - Chặn: escape theo **ngữ cảnh** khi output (HTML, attribute, JS, URL khác nhau); template engine tự escape (Blade `{{ }}`, Thymeleaf, Go `html/template`); ⚠️ `{!! !!}`, `innerHTML`, `v-html`, `dangerouslySetInnerHTML` là chỗ lọt
  - HTML do user soạn (rich text): sanitize bằng thư viện whitelist (HTML Purifier, DOMPurify), không tự viết regex
  - CSP làm lớp thứ hai: `script-src 'self'` + nonce/hash, cấm inline script; triển khai trước ở chế độ `Content-Security-Policy-Report-Only`
- [ ] CSRF
  - Trình duyệt tự gửi cookie khi site khác submit form tới bạn
  - Chặn: CSRF token (synchronizer hoặc double-submit), `SameSite=Lax/Strict`, kiểm tra `Origin`; ⚠️ GET không được đổi state
  - API chỉ dùng header `Authorization: Bearer` (không cookie) thì không bị CSRF kiểu cổ điển
- [ ] 🟡 SSRF
  - Server gọi URL do user cung cấp (webhook, tải ảnh từ link, preview link) và bị lừa gọi vào nội bộ: `169.254.169.254` (metadata cloud, lộ credential), `localhost`, dải IP private
  - Chặn: resolve DNS rồi kiểm tra IP (sau mọi redirect), chặn dải private/link-local, whitelist domain nếu được, egress proxy riêng; bật IMDSv2 trên AWS
  - ⚠️ DNS rebinding: kiểm tra IP lúc validate rồi resolve lại lúc gọi ra IP khác. Kết nối tới đúng IP đã kiểm tra
- [ ] 🟡 XXE: parser XML xử lý external entity, đọc được file (`file:///etc/passwd`) hoặc gọi mạng. Tắt DTD/external entity trong parser (mặc định an toàn hay không tuỳ thư viện và phiên bản)
- [ ] 🟡 Path traversal: `../../etc/passwd` trong tên file. Không dùng input làm đường dẫn; nếu phải dùng thì chuẩn hoá (`realpath`) rồi kiểm tra vẫn nằm trong thư mục gốc
- [ ] 🟡 Command injection: `exec("convert " . $file)`. Tránh gọi shell; dùng API truyền mảng tham số (`exec.Command(name, args...)` trong Go, `ProcessBuilder` trong Java, `proc_open` với mảng trong PHP), hoặc `escapeshellarg`
- [ ] 🟡 Insecure deserialization: `unserialize()` (PHP), `ObjectInputStream` (Java) với dữ liệu người dùng cho phép dựng object tuỳ ý, gọi magic method, tới RCE. Dùng JSON; nếu buộc phải dùng thì ký HMAC dữ liệu và giới hạn class (`allowed_classes` trong PHP)
- [ ] 🟡 Mass assignment: user gửi thêm `is_admin=1`, `balance=...`. Whitelist field (`$fillable`, DTO riêng cho request); ⚠️ `$guarded = []` là mở toang. Chiều ngược lại: response trả thừa field (`password_hash`, field nội bộ), dùng resource/DTO cho output
- [ ] 🟡 Open redirect: `?next=https://evil.com` sau login. Chỉ cho redirect path tương đối hoặc whitelist domain; ⚠️ `//evil.com` và `/\evil.com` cũng là URL tuyệt đối với trình duyệt
- [ ] 🟡 File upload
  - Kiểm tra loại thật bằng magic bytes, không tin extension hay `Content-Type` client gửi
  - Đổi tên file (tên ngẫu nhiên), lưu ngoài web root hoặc object storage, không cho thực thi; phục vụ từ domain riêng với `Content-Disposition: attachment` khi hợp
  - Giới hạn kích thước; ảnh thì decode lại/re-encode để bỏ payload lạ; quét virus nếu nhận file từ người lạ
  - ⚠️ SVG chứa được JavaScript; file zip có thể là "zip bomb"; ảnh khổng lồ làm nổ memory khi resize
- [ ] 🟡 Clickjacking: trang của bạn bị nhúng trong iframe trong suốt để lừa click. Chặn bằng CSP `frame-ancestors 'none'` (thay `X-Frame-Options: DENY`)
- [ ] 🟡 Security headers

  | Header | Tác dụng |
  |---|---|
  | `Strict-Transport-Security: max-age=...; includeSubDomains` | bắt trình duyệt chỉ dùng HTTPS; ⚠️ `preload` khó rút lại |
  | `Content-Security-Policy` | giới hạn nguồn script/style/frame; `frame-ancestors` chống clickjacking |
  | `X-Content-Type-Options: nosniff` | không đoán MIME, chống file upload bị hiểu là script |
  | `Referrer-Policy: strict-origin-when-cross-origin` | không lộ full URL (có token) sang site khác |
  | `Permissions-Policy` | tắt camera, micro, geolocation không dùng |
  | `Cache-Control: no-store` | cho response chứa dữ liệu nhạy cảm |

- [ ] 🟡 Security misconfiguration hay gặp: debug mode bật ở production (Laravel `APP_DEBUG=true` lộ env), `.git`/`.env` truy cập được qua web, bucket public, admin panel mở ra internet, CORS quá rộng, lỗi trả stack trace

### Lạm dụng: rate limit, brute force, bot

- [ ] 🟡 Rate limiting nhiều lớp: theo IP, theo tài khoản, theo thiết bị, theo endpoint; endpoint nhạy cảm (login, OTP, reset password, tìm kiếm) chặt hơn
- [ ] 🟡 Brute force một tài khoản: giới hạn theo tài khoản, tăng dần độ trễ, CAPTCHA sau N lần. ⚠️ Khoá cứng tài khoản cho phép kẻ xấu khoá người khác (DoS); nên khoá tạm và thông báo
- [ ] 🟡 Credential stuffing: dùng cặp email/password lộ từ site khác, mỗi IP thử ít nên rate limit theo IP không đủ. Chống bằng MFA, kiểm tra password đã lộ, phát hiện bất thường (thiết bị/vị trí mới), bot detection
- [ ] 🟡 Account enumeration: thông báo lỗi, thời gian phản hồi, form đăng ký/quên mật khẩu tiết lộ email có tài khoản. Trả thông điệp chung ("nếu email tồn tại, chúng tôi đã gửi link"); đăng ký thì gửi email thay vì báo "email đã dùng" trên màn hình khi cần kín
- [ ] 🔴 Bot và lạm dụng luồng nghiệp vụ: gom hàng flash sale, spam tạo tài khoản lấy khuyến mãi, SMS pumping. Giới hạn theo nghiệp vụ (mỗi user một mã), CAPTCHA/challenge có chọn lọc, device fingerprint, theo dõi metric bất thường

### Crypto thực dụng

- [ ] 🟢 Phân biệt

  | | Đảo ngược được? | Cần key? | Dùng cho |
  |---|---|---|---|
  | Encode (base64, URL encode) | có, ai cũng làm được | không | biểu diễn dữ liệu, **không** bảo mật |
  | Hash (SHA-256) | không | không | checksum, fingerprint; password thì dùng hàm chậm |
  | HMAC | không | secret chung | toàn vẹn + xác thực nguồn (webhook, cookie ký) |
  | Encrypt đối xứng (AES-GCM) | có, với key | một key | mã hoá dữ liệu lưu trữ |
  | Encrypt bất đối xứng (RSA-OAEP, ECIES) | có, với private key | cặp key | trao đổi key, gửi dữ liệu cho bên giữ private key |
  | Sign (RSA-PSS, ECDSA, Ed25519) | verify bằng public key | cặp key | JWT RS256, ký release, chứng thư |

- [ ] 🟡 Symmetric vs asymmetric
  - Đối xứng nhanh, dùng cho dữ liệu lớn; vấn đề là phân phối key
  - Bất đối xứng chậm, dùng để trao đổi key hoặc ký; thực tế hai loại đi cùng nhau (TLS: bất đối xứng để thoả thuận key, đối xứng để mã hoá dữ liệu)
  - AES-GCM là authenticated encryption: vừa mã hoá vừa phát hiện bị sửa. ⚠️ Nonce **không bao giờ lặp** với cùng một key; lặp nonce là phá vỡ cả tính bí mật lẫn toàn vẹn
  - ⚠️ ECB mode lộ cấu trúc dữ liệu; CBC không kèm MAC dễ bị padding oracle
- [ ] 🟡 HMAC vs hash thường: `SHA256(secret + message)` bị length extension attack với SHA-2; dùng HMAC
- [ ] 🔴 KMS và envelope encryption
  - Master key (KEK) nằm trong KMS/HSM, không bao giờ ra ngoài. Mỗi bản ghi/file dùng data key (DEK) sinh ngẫu nhiên; DEK mã hoá dữ liệu, KEK mã hoá DEK; lưu DEK đã mã hoá cạnh dữ liệu
  - Lợi ích: gọi KMS ít (chỉ giải mã DEK), rotate KEK không phải mã hoá lại toàn bộ dữ liệu (chỉ mã hoá lại DEK), phân quyền và audit ở KMS
  - Key rotation: key có version, dữ liệu ghi kèm key version, giải mã bằng version tương ứng, mã hoá lại dần ở background
- [ ] 🟡 TLS và at rest
  - TLS cho mọi kết nối, kể cả nội bộ nếu mạng không tin được; mTLS khi cần xác thực hai chiều giữa service. Chi tiết handshake ở [02-networking.md](02-networking.md)
  - Encryption at rest của disk/DB chống mất ổ đĩa hoặc backup, **không** chống kẻ đã vào được app. Field cực nhạy cảm (số CCCD, token bên thứ ba) thì mã hoá ở tầng ứng dụng
  - Cần tìm kiếm trên field mã hoá: lưu thêm blind index (HMAC của giá trị chuẩn hoá)
- [ ] ⚠️ Không tự chế crypto: không tự viết thuật toán, không tự ghép mode, không tự sinh random bằng `rand()`/`Math.random()`. Dùng thư viện cấp cao (libsodium, Tink) và CSPRNG (`random_bytes`, `crypto/rand`, `SecureRandom`)

### Secret và supply chain

- [ ] 🟢 Secret management
  - Không hard-code, không commit `.env`; env var là mức tối thiểu (⚠️ lộ qua `phpinfo()`, crash dump, log in env, `/proc/<pid>/environ`)
  - Secret manager (Vault, AWS Secrets Manager, GCP Secret Manager): quyền theo service, audit truy cập, rotation tự động, 🔴 dynamic secret (Vault sinh DB credential ngắn hạn cho từng lần)
  - Rotation không downtime: hệ thống chấp nhận hai secret cùng lúc trong giai đoạn chuyển
- [ ] ⚠️ Secret lỡ commit
  - Coi như **đã lộ**: thu hồi và thay mới ngay; sau đó mới dọn lịch sử git (`git filter-repo`) nếu cần
  - Xoá commit không đủ: đã có người clone, fork, CI cache, bot quét GitHub public tìm key trong thời gian rất ngắn
  - Phòng: pre-commit hook và secret scanning trong CI (gitleaks, GitHub secret scanning)
- [ ] 🟡 Supply chain
  - Dependency audit: `composer audit`, `npm audit`, `govulncheck`, OWASP Dependency-Check; Dependabot/Renovate cập nhật định kỳ
  - Commit lockfile (`composer.lock`, `package-lock.json`, `go.sum`) để build tái lập và không kéo bản mới bị chèn mã độc
  - ⚠️ Typosquatting (package tên gần giống), dependency confusion (package public trùng tên package nội bộ), maintainer bị chiếm tài khoản
  - 🔴 SBOM: danh sách mọi thành phần trong bản build (định dạng SPDX, CycloneDX) để khi có CVE mới biết ngay mình có bị ảnh hưởng không; ký artifact/image (Sigstore/cosign) biết ở mức khái niệm
  - Base image Docker tối giản, quét image (Trivy); xem [19-devops-cloud.md](19-devops-cloud.md)

### Dữ liệu cá nhân

- [ ] 🟡 PII: tên, email, số điện thoại, địa chỉ, số CCCD, ngày sinh, vị trí, IP; dữ liệu nhạy cảm hơn: sức khoẻ, tài chính, sinh trắc học
  - Thu thập tối thiểu (data minimization): không cần thì đừng lưu
  - Phân loại dữ liệu (public, internal, confidential, restricted) để biết mức bảo vệ
- [ ] 🟡 Masking trong log
  - ⚠️ Không log password, token, OTP, số thẻ, header `Authorization`, cookie; che email/SĐT (`n***@gmail.com`, `090****123`)
  - Làm ở tầng logger (processor/filter theo tên field) thay vì trông vào từng dev nhớ
  - Log, backup, data warehouse, môi trường staging copy từ production: đều là nơi PII lọt. Dữ liệu cho dev/test phải được ẩn danh hoá
- [ ] 🟡 Quyền truy cập dữ liệu: nhân viên support chỉ xem trường cần thiết, truy cập production DB qua bastion/có phê duyệt, tài khoản riêng từng người (không dùng chung tài khoản)
- [ ] 🟡 Audit log
  - Ai, làm gì, trên đối tượng nào, lúc nào, từ đâu, giá trị trước/sau
  - Append-only, tách khỏi quyền của người bị audit, giữ theo chính sách; bản thân audit log cũng chứa PII
- [ ] 🟡 Xoá dữ liệu
  - User yêu cầu xoá: xoá hoặc ẩn danh hoá ở DB chính, cache, search index, object storage, bên thứ ba đã nhận; backup thì hết hạn theo vòng đời
  - Có ràng buộc giữ lại (hoá đơn, kế toán) thì tách: giữ phần luật bắt buộc, ẩn danh phần còn lại
  - 🔴 Crypto-shredding: mỗi user một key, xoá key là dữ liệu (kể cả trong backup) không đọc được nữa
- [ ] 🟢 Pháp lý, mức "biết tồn tại": GDPR (EU) áp dụng khi xử lý dữ liệu người ở EU; Việt Nam có Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân (và luật về bảo vệ dữ liệu cá nhân ban hành sau đó; kiểm tra lại văn bản hiện hành). Ý chung: cần căn cứ/sự đồng ý khi xử lý, quyền của chủ thể dữ liệu (xem, sửa, xoá), thông báo khi có sự cố lộ lọt, lưu ý khi chuyển dữ liệu ra nước ngoài. Chi tiết điều khoản là việc của bộ phận pháp chế

### Nguyên tắc

- [ ] 🟡 Least privilege: tài khoản DB của app không cần quyền `DROP`/`GRANT`; IAM role mỗi service chỉ đúng bucket/queue cần; token scope hẹp; tài khoản admin tách khỏi tài khoản thường
- [ ] 🟡 Defense in depth: nhiều lớp độc lập (WAF, validate input, prepared statement, least privilege DB, CSP, monitoring) để một lớp hỏng không thành thảm hoạ
- [ ] Fail secure: lỗi khi kiểm tra quyền thì từ chối, không cho qua
- [ ] 🔴 Threat modeling cơ bản
  - Bốn câu hỏi: đang xây gì (vẽ data flow, ranh giới tin cậy), cái gì có thể hỏng, làm gì với nó, đã làm đủ chưa
  - STRIDE để gợi ý: **S**poofing (giả danh), **T**ampering (sửa dữ liệu), **R**epudiation (chối bỏ, cần audit log), **I**nformation disclosure (lộ dữ liệu), **D**enial of service, **E**levation of privilege
  - Làm sớm lúc thiết kế tính năng nhạy cảm (thanh toán, upload, tích hợp bên thứ ba), ưu tiên theo khả năng xảy ra x mức thiệt hại
- [ ] 🟡 Logging và phát hiện: log sự kiện bảo mật (login thất bại, đổi quyền, đổi password, truy cập bị từ chối), cảnh báo bất thường; có quy trình phản ứng sự cố (xem [18-reliability-observability.md](18-reliability-observability.md))

## Senior trả lời khác gì

| Câu hỏi | Junior / mid | Senior |
|---|---|---|
| "Lưu password thế nào?" | bcrypt có salt | argon2id/bcrypt, chỉnh cost theo phần cứng, rehash khi đăng nhập, giới hạn 72 byte của bcrypt, pepper trong secret manager và cái giá, rate limit login vì hash chậm là mục tiêu DoS |
| "Session hay JWT?" | JWT vì stateless, scale tốt | Hỏi loại client; web một domain dùng session cookie; JWT khi nhiều service verify độc lập; nói rõ revocation, rotation + reuse detection, nơi lưu, và việc denylist làm mất tính stateless |
| "Chống IDOR?" | Dùng UUID | UUID chỉ làm khó đoán; kiểm tra ownership ở tầng service, query luôn có scope, deny by default, test tự động chéo user/tenant |
| "Secret lỡ push lên GitHub?" | Xoá commit, force push | Rotate ngay, kiểm tra log dùng key trong khoảng lộ, rồi mới dọn lịch sử; thêm secret scanning; viết postmortem |
| "Bảo mật API thế nào?" | HTTPS và JWT | Đi theo OWASP API Top 10: BOLA, mass assignment, resource consumption, inventory API cũ; rate limit nhiều lớp; logging và phát hiện; threat model cho luồng nhạy cảm |

## Tình huống

1. **User đổi mật khẩu, cần đăng xuất khỏi mọi thiết bị, hệ thống dùng JWT.**
   Gợi ý:
   - Xoá mọi refresh token của user; tăng `token_version`, middleware so version trong token với DB/cache
   - Access token ngắn hạn thì chấp nhận trễ vài phút, hoặc denylist
2. **Log cho thấy hàng nghìn IP khác nhau thử đăng nhập, mỗi IP vài lần.**
   Gợi ý:
   - Credential stuffing; rate limit theo IP vô dụng
   - Kiểm tra password đã lộ, bắt MFA/CAPTCHA theo tín hiệu rủi ro, thông báo user bị đăng nhập thành công bất thường
3. **Tính năng "nhập URL ảnh đại diện", pentest báo đọc được credential từ metadata cloud.**
   Gợi ý:
   - SSRF; chặn IP private/link-local sau khi resolve, xử lý redirect, egress proxy, IMDSv2
   - Thu hồi credential đã có thể bị lộ
4. **SaaS nhiều tenant, một khách thấy hoá đơn của khách khác trong một lần export.**
   Gợi ý:
   - Tìm nơi mất `tenant_id`: job nền, cache key, query raw
   - Global scope + RLS, test chéo tenant; quy trình thông báo sự cố lộ dữ liệu
5. **Dev dán access key AWS vào repo public 10 phút rồi xoá.**
   Gợi ý:
   - Vô hiệu key ngay, xem CloudTrail trong khoảng thời gian đó (tài nguyên lạ, đào coin)
   - Secret scanning, pre-commit hook, dùng role thay vì key dài hạn
6. **Upload avatar: có người up file `.php` đổi tên thành `.jpg` và chạy được.**
   Gợi ý:
   - Web server cấu hình thực thi theo pattern tên file; kiểm tra magic bytes, re-encode ảnh, lưu ở object storage/domain riêng, không thực thi trong thư mục upload

## ❓ Câu hỏi hay gặp

🟢
- Làm sao lưu password an toàn? Vì sao không dùng SHA-256?
- Prepared statement chống SQL injection như thế nào?
- XSS và CSRF khác nhau thế nào? Chống mỗi cái ra sao?
- Authentication và authorization khác nhau thế nào?

🟡
- Session và JWT: bạn chọn cái nào cho web app? cho mobile app? Vì sao?
- Người dùng đổi mật khẩu, làm sao đăng xuất họ khỏi mọi thiết bị khi đang dùng JWT?
- HS256 và RS256 khác nhau thế nào? `alg: none` là lỗi gì?
- Authorization code + PKCE hoạt động thế nào? Vì sao implicit flow bị bỏ?
- ID token và access token khác nhau thế nào?
- IDOR là gì? Dùng UUID có đủ không?
- SSRF là gì, chặn thế nào?
- Hash, encrypt, encode, sign khác nhau thế nào? Khi nào dùng HMAC?
- Cookie `SameSite` có những giá trị nào?

🔴
- Refresh token rotation và reuse detection hoạt động thế nào? Xử lý request refresh song song ra sao?
- Thiết kế cô lập dữ liệu cho SaaS multi-tenant.
- Envelope encryption là gì, vì sao dùng?
- Bạn làm threat model cho tính năng thanh toán thế nào?
- Secret lỡ commit vào git: các bước xử lý?

## Bài tập tự làm

1. Thiết kế luồng đăng nhập cho SPA + mobile app: loại token, thời hạn, nơi lưu từng loại, luồng refresh có rotation và reuse detection, đăng xuất mọi thiết bị.
2. Liệt kê 10 endpoint của một ứng dụng bạn từng làm, với mỗi cái ghi rủi ro theo OWASP API Top 10 và cách kiểm tra quyền hiện tại.
3. Viết pseudo-code cho endpoint "quên mật khẩu" và "đặt lại mật khẩu", chỉ rõ chỗ chống enumeration, chống brute force, chống host header injection.
4. Thiết kế cơ chế mã hoá số CCCD trong DB có hỗ trợ tìm kiếm chính xác theo số CCCD và rotate key.
5. Làm threat model STRIDE cho tính năng "upload file đính kèm vào đơn hàng": vẽ data flow, liệt kê mối đe doạ và biện pháp.

> Nộp bài vào đây để được review.
