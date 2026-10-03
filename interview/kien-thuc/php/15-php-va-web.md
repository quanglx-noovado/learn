# Chương 15. PHP và HTTP: request, response, session, cookie, upload

> [← Mục lục](README.md) · [← Chương 14: File, stream, JSON và thời gian](14-file-json-thoi-gian.md) · [Chương 16: PHP làm việc với database →](16-php-va-database.md)

**Bạn sẽ học được:**

- HTTP từ con số 0: một request và một response trông như thế nào khi đi trên dây, method, status
  code, header, body, và vì sao HTTP "không nhớ gì" giữa hai request.
- Cách PHP biến một HTTP request thành các *superglobal* `$_GET`, `$_POST`, `$_SERVER`, `$_COOKIE`,
  `$_FILES`, `$_REQUEST`, và cách đọc body JSON qua `php://input`.
- Gửi response đúng cách: `echo`, `header()`, `http_response_code()`, redirect, output buffering, và
  gốc rễ của lỗi kinh điển "headers already sent".
- Cookie và session: `setcookie()` với `Secure`, `HttpOnly`, `SameSite`; session của PHP chạy bên
  trong ra sao (file, session ID, khoá session), session fixation và `session_regenerate_id()`.
- Nhận file upload an toàn: `$_FILES`, mã lỗi, các giới hạn `upload_max_filesize`, `post_max_size`,
  `move_uploaded_file()` và danh sách kiểm tra trước khi lưu.
- Tự viết một mini router để thấy framework như Laravel làm gì ở tầng dưới cùng.

**Cần biết trước:** [Chương 02](02-php-chay-nhu-the-nao.md) mục 6 và 7 (một request đi qua Nginx,
PHP-FPM ra sao; share-nothing), [Chương 06](06-mang.md) (mảng), [Chương 12](12-loi-exception.md)
(exception), [Chương 14](14-file-json-thoi-gian.md) (file, stream, JSON).

**Cách chạy ví dụ.** Phần lớn ví dụ chương này là trang web, nên cần một web server. PHP có sẵn
*built-in web server* (`php -S`, đã gặp ở [chương 01](01-php-la-gi.md)), đủ dùng để học. Lưu ví dụ
thành `index.php` trong một thư mục trống rồi:

```bash
# Chạy tại thư mục chứa index.php (cửa sổ terminal 1): mở server ở cổng 8000
php -S localhost:8000

# Không cài PHP thì dùng Docker. Phải nghe ở 0.0.0.0 để máy ngoài container gọi vào được
docker run --rm -it -p 8000:8000 -v "$PWD":/app -w /app php:8.5-cli php -S 0.0.0.0:8000
```

Sau đó mở `http://localhost:8000/` bằng trình duyệt, hoặc gọi bằng `curl` ở một terminal khác (terminal
2). `curl` có sẵn trên macOS, Linux và Windows 10 trở lên. Các ví dụ không cần web server thì chạy
bằng `php ten-file.php` như các chương trước. Output trong comment là output thật trên PHP 8.5, trừ
chỗ ghi "output minh hoạ".

## 1. HTTP từ con số 0

### 1.1 Web là một cuộc hỏi đáp

Khi bạn gõ `https://shop.vn/products?page=2` vào trình duyệt, trình duyệt mở kết nối tới máy chủ của
`shop.vn` và gửi một tin nhắn văn bản hỏi "cho tôi trang `/products?page=2`". Máy chủ đọc tin nhắn,
làm việc gì đó (đọc database, chạy code PHP...) rồi gửi về một tin nhắn trả lời chứa HTML. Trình duyệt
vẽ HTML đó lên màn hình. Xong một lượt.

Luật quy định hai tin nhắn đó phải viết thế nào gọi là *HTTP* (HyperText Transfer Protocol). Tin
nhắn hỏi gọi là *request*, tin nhắn trả lời gọi là *response*. Bên gửi request gọi là *client*
(trình duyệt, app điện thoại, lệnh `curl`, một server khác gọi API), bên trả lời là *server*.

```
  Client (trình duyệt)                              Server (Nginx + PHP)
        │                                                  │
        │ ─────── request: "GET /products?page=2" ───────► │
        │                                                  │  chạy code, đọc DB...
        │ ◄────── response: "200 OK" + HTML ────────────── │
        │                                                  │
```

Hai điều quan trọng nhất về HTTP:

1. **Luôn là client hỏi trước, server trả lời sau.** Server không tự gửi gì cho client nếu client
   không hỏi. Mỗi request nhận về một response cuối cùng.
2. **HTTP là *stateless* (không trạng thái).** Mỗi request là một tin nhắn độc lập. Theo bản thân giao
   thức, request thứ hai không có cách nào biết nó đến từ cùng người với request thứ nhất. Muốn "nhớ"
   người dùng (giỏ hàng, đăng nhập) phải tự xây thêm cơ chế: đó là cookie và session ở mục 5 và 6.

PHP hợp với mô hình này một cách tự nhiên. Như [chương 02](02-php-chay-nhu-the-nao.md) mục 7 đã nói,
PHP chạy theo kiểu *share-nothing*: mỗi request chạy script từ đầu với bộ nhớ trống, hết request thì
mọi biến bị xoá. HTTP không nhớ, PHP cũng không nhớ.

### 1.2 Một request trông như thế nào

HTTP/1.1 là giao thức dạng văn bản: request thật sự là các dòng chữ đi qua kết nối mạng. Đây là
request trình duyệt gửi khi bạn điền form đăng nhập và bấm nút (đã lược bớt header):

```http
POST /login?next=%2Fcart HTTP/1.1
Host: shop.vn
User-Agent: Mozilla/5.0 (Macintosh; ...)
Accept: text/html
Content-Type: application/x-www-form-urlencoded
Content-Length: 29
Cookie: theme=dark

email=an%40shop.vn&password=1
```

Request gồm bốn phần, theo đúng thứ tự:

```
┌────────────────────────────────────────────────────┐
│ POST /login?next=%2Fcart HTTP/1.1                  │  1. Request line: method, đích, phiên bản
├────────────────────────────────────────────────────┤
│ Host: shop.vn                                      │
│ Content-Type: application/x-www-form-urlencoded    │  2. Header: mỗi dòng "Tên: giá trị"
│ Content-Length: 29                                 │
│ Cookie: theme=dark                                 │
├────────────────────────────────────────────────────┤
│ (dòng trống)                                       │  3. Một dòng trống: hết phần header
├────────────────────────────────────────────────────┤
│ email=an%40shop.vn&password=1                      │  4. Body (có thể không có)
└────────────────────────────────────────────────────┘
```

1. *Request line* (dòng đầu): *method* `POST` (muốn làm gì), *request target* `/login?next=%2Fcart`
   (với cái gì), phiên bản giao thức `HTTP/1.1`. Phần sau dấu `?` là *query string*: các cặp
   `tên=giá trị` nối bằng `&`.
2. *Header* (còn gọi *header field*): thông tin phụ về request, mỗi dòng một cặp `Tên: giá trị`. Tên
   header không phân biệt hoa thường (`content-type` và `Content-Type` là một). `Host` cho biết
   client muốn tên miền nào, vì một server có thể phục vụ nhiều tên miền; HTTP/1.1 bắt buộc có header
   này.
3. Một dòng trống đánh dấu hết header. Theo chuẩn, mỗi dòng kết thúc bằng hai ký tự `\r\n` (CRLF), nên
   chỗ hết header là chuỗi `\r\n\r\n`.
4. *Body* (thân): dữ liệu gửi kèm. Request `GET` thường không có body. `Content-Type` nói body viết
   theo định dạng nào, `Content-Length` nói body dài bao nhiêu byte để server biết đọc tới đâu thì
   dừng.

Để ý hai chỗ có dấu `%`: `%2F` là `/`, `%40` là `@`. Query string và body dạng form không được chứa
tự do mọi ký tự (ví dụ `&` và `=` đã có nghĩa riêng), nên ký tự đặc biệt được mã hoá thành `%` và hai
chữ số hex của byte đó. Cách mã hoá này gọi là *percent-encoding* hay *URL encoding*. PHP tự giải mã
khi dựng `$_GET`, `$_POST` (mục 2), nên trong code bạn nhận được `an@shop.vn` chứ không phải
`an%40shop.vn`.

### 1.3 Một response trông như thế nào

Response có cấu trúc giống hệt, chỉ khác dòng đầu:

```http
HTTP/1.1 200 OK
Date: Sat, 03 Oct 2026 08:00:00 GMT
Content-Type: text/html; charset=UTF-8
Content-Length: 47
Set-Cookie: theme=dark; Path=/

<html><body><h1>Xin chào An</h1></body></html>
```

1. *Status line*: phiên bản, *status code* `200` (con số cho máy đọc), *reason phrase* `OK` (chữ cho
   người đọc, client không dựa vào nó).
2. Header của response: `Content-Type` nói body là gì (HTML, JSON, ảnh...), `Set-Cookie` bảo trình
   duyệt lưu cookie (mục 5), `Location` bảo trình duyệt đi sang URL khác (mục 4)...
3. Dòng trống.
4. Body: HTML, JSON, byte của ảnh, file PDF...

⚠️ Thứ tự này là cố định: **header đi trước, body đi sau**. Khi byte đầu tiên của body đã rời server
thì không còn chỗ nào để chèn thêm header. Đây chính là gốc rễ của lỗi "headers already sent" mà bạn
sẽ gặp ở mục 3.4.

### 1.4 Status code

Status code có ba chữ số, chữ số đầu cho biết nhóm:

| Nhóm | Ý nghĩa | Hay gặp |
|---|---|---|
| `1xx` | Thông tin, request đang được xử lý tiếp | Hiếm khi tự dùng |
| `2xx` | Thành công | `200 OK`, `201 Created` (đã tạo tài nguyên mới), `204 No Content` (thành công, không có body) |
| `3xx` | Chuyển hướng: client cần làm thêm một bước | `301`, `302`, `303`, `307`, `308` (mục 4), `304 Not Modified` (bản cache của client vẫn dùng được) |
| `4xx` | Lỗi phía client: request sai, thiếu quyền... | `400 Bad Request`, `401 Unauthorized` (chưa xác thực), `403 Forbidden` (đã biết là ai nhưng không có quyền), `404 Not Found`, `405 Method Not Allowed`, `409 Conflict`, `413 Content Too Large`, `415 Unsupported Media Type`, `422 Unprocessable Content` (đúng cú pháp nhưng dữ liệu không hợp lệ), `429 Too Many Requests` |
| `5xx` | Lỗi phía server | `500 Internal Server Error`, `502 Bad Gateway` và `504 Gateway Timeout` (proxy như Nginx không nhận được trả lời tử tế từ phía sau, ví dụ PHP-FPM), `503 Service Unavailable` |

Chọn đúng status code không phải chuyện hình thức. Trình duyệt, proxy, CDN, công cụ giám sát và code
gọi API của người khác đều ra quyết định dựa trên con số này: có cache không, có thử lại không, có báo
lỗi không. Một API trả `200` kèm body `{"error": "not found"}` buộc mọi client phải đọc body mới biết
là lỗi, và hệ thống giám sát sẽ đếm nó là request thành công.

### 1.5 Method

Method nói client muốn làm gì với tài nguyên ở URL đó:

| Method | Dùng để | Có body? | Safe | Idempotent |
|---|---|---|---|---|
| `GET` | Lấy dữ liệu | Thường không | Có | Có |
| `HEAD` | Như `GET` nhưng chỉ lấy header, không lấy body | Không | Có | Có |
| `POST` | Gửi dữ liệu để server xử lý: tạo mới, đăng nhập, thanh toán... | Có | Không | Không |
| `PUT` | Thay toàn bộ tài nguyên bằng dữ liệu gửi lên | Có | Không | Có |
| `PATCH` | Sửa một phần tài nguyên | Có | Không | Không |
| `DELETE` | Xoá tài nguyên | Thường không | Không | Có |
| `OPTIONS` | Hỏi server hỗ trợ gì (trình duyệt dùng cho CORS preflight) | Thường không | Có | Có |

Hai cột cuối là định nghĩa của RFC 9110, chuẩn ngữ nghĩa HTTP hiện hành (riêng `PATCH` do RFC 5789
định nghĩa và RFC này nói rõ `PATCH` không safe, không idempotent):

- *Safe*: client coi như request chỉ đọc, không yêu cầu thay đổi gì trên server. Trình duyệt, công cụ
  tìm kiếm, phần mềm "tải trước trang" có thể gửi `GET` bất cứ lúc nào mà không hỏi người dùng. Vì
  vậy ⚠️ đừng bao giờ để một link `GET /orders/5/delete` xoá dữ liệu: một con bot đi theo link là mất
  đơn hàng.
- *Idempotent*: gửi một lần hay gửi mười lần giống hệt nhau thì kết quả cuối cùng trên server như nhau.
  `DELETE /orders/5` hai lần thì đơn 5 vẫn chỉ bị xoá một lần. `POST /orders` hai lần là hai đơn hàng.
  Nhờ tính chất này, client và proxy được phép tự gửi lại request idempotent khi mạng lỗi; với `POST`
  thì không. Đó là lý do trình duyệt hỏi "Gửi lại biểu mẫu?" khi bạn bấm tải lại một trang vừa
  `POST` (mục 4.4 chỉ cách tránh).

Form HTML chỉ gửi được `GET` và `POST`. `PUT`, `PATCH`, `DELETE` thường đến từ JavaScript (`fetch`) hoặc
từ client gọi API. Laravel giả lập chúng trong form bằng một trường ẩn `_method`
([chương 24](24-laravel-routing-controller-middleware.md)).

### 1.6 Tự nhìn thấy HTTP bằng curl

Cách tốt nhất để hiểu HTTP là nhìn tận mắt. Tạo `index.php`:

```php
<?php
declare(strict_types=1);

echo "Xin chào\n";
```

Chạy `php -S localhost:8000` (terminal 1), rồi ở terminal 2:

```bash
# Terminal 2: -v in cả request lẫn response; dòng ">" là curl gửi đi, dòng "<" là server trả về
curl -v http://localhost:8000/index.php?page=2
```

Output minh hoạ (số cổng, ngày giờ, phiên bản sẽ khác trên máy bạn):

```
> GET /index.php?page=2 HTTP/1.1
> Host: localhost:8000
> User-Agent: curl/8.7.1
> Accept: */*
>
< HTTP/1.1 200 OK
< Host: localhost:8000
< Date: Sat, 03 Oct 2026 08:00:00 GMT
< Connection: close
< X-Powered-By: PHP/8.5.0
< Content-type: text/html; charset=UTF-8
<
Xin chào
```

Bạn không hề viết header nào, nhưng response vẫn có `Content-type: text/html; charset=UTF-8`. PHP tự
thêm header này từ hai thiết lập `default_mimetype` (mặc định `"text/html"`) và `default_charset`
(mặc định `"UTF-8"`). `X-Powered-By` cũng do PHP tự thêm khi `expose_php` bật; production nên tắt nó
để không khoe phiên bản ([chương 17](17-bao-mat.md)).

Vài lệnh `curl` dùng suốt chương:

```bash
# Chạy ở terminal 2, khi server ở terminal 1 đang chạy
curl -i http://localhost:8000/                     # -i: in header response kèm body
curl -d 'name=An&age=20' http://localhost:8000/   # gửi form (urlencoded), -d tự chuyển sang POST
curl -H 'Content-Type: application/json' \
     -d '{"name":"An"}' http://localhost:8000/     # gửi JSON
curl -F 'avatar=@anh.png' http://localhost:8000/   # upload file (multipart/form-data)
curl -c cookies.txt -b cookies.txt http://localhost:8000/   # lưu cookie vào file và gửi lại
```

### 1.7 HTTP/2, HTTP/3 và HTTPS

Mục 1.2 dùng HTTP/1.1 vì nó là văn bản, đọc được bằng mắt. HTTP/2 và HTTP/3 đóng gói tin nhắn thành
khung nhị phân và cho nhiều request chạy chung một kết nối, nhưng *ý nghĩa* không đổi: vẫn method,
URL, header, status code, body. HTTPS là HTTP đi bên trong một kết nối mã hoá TLS, để người đứng giữa
không đọc hay sửa được nội dung.

Với code PHP, khác biệt này gần như vô hình. Nginx (hoặc load balancer phía trước) lo phần giao thức
và mã hoá, rồi chuyển cho PHP-FPM cùng một bộ thông tin như nhau qua FastCGI
([chương 02](02-php-chay-nhu-the-nao.md) mục 6). Code PHP của bạn không phải quan tâm request đến bằng
HTTP/1.1 hay HTTP/3.

## 2. Từ HTTP request tới biến PHP: superglobal

### 2.1 PHP dựng sẵn dữ liệu request cho bạn

Bạn không phải tự đọc từng byte của request như mục 1.2. Trước khi dòng đầu tiên của script chạy, PHP
đã đọc request (Nginx chuyển sang qua FastCGI, xem [chương 02](02-php-chay-nhu-the-nao.md) mục 6.2),
cắt nó ra và bỏ vào mấy mảng có sẵn:

| Biến | Lấy từ phần nào của request |
|---|---|
| `$_GET` | Query string trên URL (phần sau `?`) |
| `$_POST` | Body, khi body là form (`application/x-www-form-urlencoded` hoặc `multipart/form-data`) |
| `$_COOKIE` | Header `Cookie` |
| `$_FILES` | Các file upload trong body `multipart/form-data` (mục 7) |
| `$_SERVER` | Request line, các header, và thông tin do web server, môi trường cung cấp |
| `$_REQUEST` | Gộp `$_GET`, `$_POST` (và có thể cả `$_COOKIE`) theo cấu hình (mục 2.8) |
| `$_SESSION` | Không lấy từ request; là dữ liệu session, chỉ có sau `session_start()` (mục 6) |
| `$_ENV` | Biến môi trường của process (thường để trống trên production, mục 2.8) |
| `php://input` | Không phải biến mà là một stream: body thô, chưa qua xử lý (mục 2.5) |

Các biến này gọi là *superglobal*: dùng được ở mọi nơi, kể cả bên trong hàm và method, không cần từ khoá
`global`. Chúng là mảng PHP bình thường, được dựng mới cho từng request và mất khi request kết thúc
(share-nothing). Request sau của cùng người dùng có `$_GET` riêng của nó.

### 2.2 `$_GET`: query string

```php
<?php
declare(strict_types=1);

var_dump($_GET);
```

Gọi `http://localhost:8000/?ten=Nguy%E1%BB%85n&page=2&page=3&tags[]=php&tags[]=go&a.b=1&n=null`
(trên terminal, nhớ đặt URL trong nháy đơn vì shell hiểu `&` và `[]` theo nghĩa riêng):

```
array(5) {
  ["ten"]=>
  string(8) "Nguyễn"
  ["page"]=>
  string(1) "3"
  ["tags"]=>
  array(2) {
    [0]=>
    string(3) "php"
    [1]=>
    string(2) "go"
  }
  ["a_b"]=>
  string(1) "1"
  ["n"]=>
  string(4) "null"
}
```

Mỗi dòng của output dạy một quy tắc:

- `ten`: PHP đã giải mã percent-encoding. `%E1%BB%85` là ba byte UTF-8 của chữ "ễ", nên chuỗi
  "Nguyễn" dài 8 byte dù chỉ có 6 ký tự ([chương 05](05-chuoi.md)).
- `page`: tên trùng thì **giá trị sau ghi đè giá trị trước**, chỉ còn `"3"`. Nhiều ngôn ngữ, framework
  khác gom thành danh sách; PHP thì không, trừ khi tên có `[]`.
- `tags[]`: tên kết thúc bằng `[]` thì PHP dựng mảng. Viết `user[name]=An&user[age]=20` sẽ ra mảng
  `['name' => 'An', 'age' => '20']`.
- `a.b` thành `a_b`: PHP thay dấu chấm và khoảng trắng trong **tên** biến bằng dấu gạch dưới (lý do
  lịch sử: thời PHP còn tự biến input thành biến `$a.b`, mà dấu chấm không hợp lệ trong tên biến).
- `n` là chuỗi `"null"`, `page` là chuỗi `"3"`: **mọi giá trị đều là string** (hoặc mảng string).
  HTTP chỉ chở văn bản; PHP không đoán kiểu giúp bạn.

`$_GET` có mặt bất kể method: request `POST /login?next=/cart` vẫn có `$_GET['next']`. Tên `$_GET` chỉ
là tên lịch sử, đúng hơn nên gọi là "tham số trên URL".

### 2.3 Input có kiểu `string|array`, không phải kiểu bạn mong đợi

Vì client tự viết URL, một tham số bạn nghĩ là số có thể là chuỗi bất kỳ, hoặc là mảng. Với
`strict_types=1`, truyền nhầm kiểu là `TypeError`:

```php
<?php
declare(strict_types=1);

function findProduct(string $id): string
{
    return "Sản phẩm #$id";
}

$id = $_GET['id'] ?? '';
echo findProduct($id), "\n";
// ?id=5    → in ra: Sản phẩm #5
// ?id[]=5  → Fatal error: Uncaught TypeError: findProduct(): Argument #1 ($id) must be of type
//            string, array given
```

Kẻ tấn công rất thích kiểu lỗi này: chỉ thêm `[]` vào URL là có trang lỗi 500, đôi khi kèm đường dẫn
file nếu `display_errors` đang bật. Quy tắc: **trước khi dùng một giá trị từ request, kiểm tra nó có
đúng kiểu và đúng miền giá trị không**. Với số nguyên, `filter_var()` cùng `FILTER_VALIDATE_INT` làm
gọn việc này:

```php
<?php
declare(strict_types=1);

/**
 * Lấy một tham số số nguyên dương từ query string.
 * Trả về $default nếu không có tham số; trả về null nếu có nhưng không hợp lệ.
 */
function queryInt(string $name, int $default): ?int
{
    if (!array_key_exists($name, $_GET)) {
        return $default;
    }
    $raw = $_GET[$name];
    if (!is_string($raw)) {          // ?page[]=1 cho ra mảng, không phải chuỗi
        return null;
    }
    $value = filter_var($raw, FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
    return $value === false ? null : $value;
}

$page = queryInt('page', 1);
if ($page === null) {
    http_response_code(400);
    echo "Tham số page không hợp lệ\n";
    exit;
}
var_dump($page);
```

| URL | Kết quả |
|---|---|
| `/` | `int(1)` (mặc định) |
| `/?page=3` | `int(3)` |
| `/?page=%203` (có khoảng trắng đầu) | `int(3)`: `FILTER_VALIDATE_INT` bỏ khoảng trắng hai đầu |
| `/?page=03` | 400: số có số 0 ở đầu bị coi là không hợp lệ |
| `/?page=abc`, `/?page=2.0`, `/?page=0`, `/?page[]=1` | 400 |

`filter_var()` trả `false` khi không hợp lệ, nên phải so bằng `=== false` chứ không dùng `!$value`
(số `0` cũng falsy). Ngoài ra còn `filter_input(INPUT_GET, 'page', FILTER_VALIDATE_INT)` làm cùng việc
nhưng đọc từ dữ liệu gốc mà SAPI cung cấp, không thấy các thay đổi bạn đã ghi vào `$_GET`; nó trả
`null` khi không có tham số.

Kiểm tra từng trường bằng tay như vầy nhanh chóng trở nên dài dòng. Framework gom nó thành
*validation* khai báo (`'page' => 'integer|min:1'` trong Laravel,
[chương 25](25-laravel-request-validation-response.md)). Còn chuyện vì sao "validate đầu vào" khác
"escape đầu ra" là nội dung của [chương 17](17-bao-mat.md).

### 2.4 `$_POST`: dữ liệu form

Form HTML gửi dữ liệu bằng `POST`:

```php
<?php
declare(strict_types=1);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = $_POST['name'] ?? '';
    $topics = $_POST['topics'] ?? [];
    $agree = isset($_POST['agree']);      // checkbox không tick thì không được gửi lên
    echo '<pre>', htmlspecialchars(print_r($_POST, true)), '</pre>';
}
?>
<form method="post" action="">
    <input name="name" value="An">
    <label><input type="checkbox" name="topics[]" value="php" checked> PHP</label>
    <label><input type="checkbox" name="topics[]" value="go"> Go</label>
    <label><input type="checkbox" name="agree" value="1"> Đồng ý</label>
    <button>Gửi</button>
</form>
```

Bấm "Gửi" với PHP được tick, "Đồng ý" không tick, trình duyệt gửi body
`name=An&topics%5B%5D=php` (`%5B%5D` là `[]` đã mã hoá) và trang hiển thị:

```
Array
(
    [name] => An
    [topics] => Array
        (
            [0] => php
        )

)
```

Ba điều cần nhớ:

- PHP chỉ điền `$_POST` khi method là `POST` **và** body có `Content-Type` là
  `application/x-www-form-urlencoded` hoặc `multipart/form-data`. Body JSON, XML, hay method `PUT`,
  `PATCH` thì `$_POST` rỗng (mục 2.5, 2.6).
- Checkbox không tick, `<select>` bị `disabled`, nút submit không được bấm: trình duyệt không gửi tên
  đó lên. Phải dùng `isset()` hoặc `??`, không được giả định key luôn có.
- `htmlspecialchars()` khi in ra: dữ liệu người dùng in thẳng vào HTML là lỗ hổng XSS
  ([chương 17](17-bao-mat.md)).

### 2.5 Body JSON: đọc từ `php://input`

API hiện đại thường nhận body JSON (`Content-Type: application/json`). PHP không tự giải mã JSON vào
`$_POST`; bạn đọc body thô từ stream `php://input` rồi tự `json_decode()`. Ví dụ dưới là một endpoint
nhận JSON hoàn chỉnh, có kiểm tra method, `Content-Type`, cú pháp JSON và nội dung:

```php
<?php
declare(strict_types=1);

/** Gửi một response JSON rồi dừng script. */
function sendJson(int $status, array $data): never
{
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Allow: POST');
    sendJson(405, ['error' => 'Chỉ nhận POST']);
}

// Content-Type có thể kèm tham số, ví dụ "application/json; charset=utf-8"
$contentType = $_SERVER['CONTENT_TYPE'] ?? '';
if (strtolower(trim(explode(';', $contentType)[0])) !== 'application/json') {
    sendJson(415, ['error' => 'Body phải là JSON']);
}

$raw = file_get_contents('php://input');
try {
    $data = json_decode($raw, true, 512, JSON_THROW_ON_ERROR);
} catch (JsonException $e) {
    sendJson(400, ['error' => 'JSON không hợp lệ: ' . $e->getMessage()]);
}

// JSON hợp lệ chưa chắc là object: "42", "[1,2]", "null" đều là JSON hợp lệ
if (!is_array($data) || !isset($data['name']) || !is_string($data['name'])) {
    sendJson(422, ['error' => 'Thiếu trường name kiểu chuỗi']);
}

sendJson(201, ['message' => 'Đã tạo', 'name' => $data['name']]);
```

Thử bằng `curl` (terminal 2):

```bash
curl -i -H 'Content-Type: application/json' -d '{"name":"An"}' http://localhost:8000/
# HTTP/1.1 201 Created ... body: {"message":"Đã tạo","name":"An"}
curl -i -H 'Content-Type: application/json' -d '{"name":' http://localhost:8000/
# 400, body: {"error":"JSON không hợp lệ: Syntax error"}
curl -i -H 'Content-Type: application/json' -d '42' http://localhost:8000/
# 422, body: {"error":"Thiếu trường name kiểu chuỗi"}
curl -i -d 'name=An' http://localhost:8000/
# 415, body: {"error":"Body phải là JSON"}
curl -i http://localhost:8000/
# 405, có header Allow: POST
```

Vài điểm về `php://input`:

- Đây là stream chỉ đọc chứa body thô. Từ PHP 5.6 nó đọc lại được nhiều lần, nên gọi
  `file_get_contents('php://input')` hai lần vẫn ra cùng nội dung.
- ⚠️ Với request `multipart/form-data` (form có upload file), `php://input` **không có dữ liệu**, vì PHP
  đã tự đọc body đó để dựng `$_POST` và `$_FILES` (trừ khi tắt `enable_post_data_reading`, xem dưới).
- Tên header `Content-Type` nằm trong `$_SERVER['CONTENT_TYPE']`, không có tiền tố `HTTP_` (mục 2.7).
- Hàm `sendJson()` khai báo kiểu trả về `never` ([chương 08](08-ham.md)) để người đọc và công cụ phân
  tích biết code phía sau lời gọi không bao giờ chạy tới.
- JSON chi tiết (flag, số lớn, `json_validate()`) ở [chương 14](14-file-json-thoi-gian.md).

Thiết lập `enable_post_data_reading` (mặc định bật) quyết định PHP có tự đọc body để dựng `$_POST`,
`$_FILES` hay không. Tắt nó đi thì hai mảng đó luôn rỗng, body nằm nguyên trong `php://input` để bạn
tự đọc dần, hữu ích khi viết proxy hoặc xử lý body rất lớn mà không muốn PHP đọc hết vào bộ nhớ.

### 2.6 `PUT`, `PATCH`, `DELETE` và `request_parse_body()`

PHP chỉ tự phân tích body cho method `POST`. Một request `PUT` với body dạng form vẫn để `$_POST`
rỗng. Trước PHP 8.4 muốn đọc nó phải tự đọc `php://input` rồi `parse_str()` (với form urlencoded) hoặc
tự viết bộ phân tích multipart. PHP 8.4 thêm `request_parse_body()`: đọc body theo `Content-Type` và
trả về một cặp `[$post, $files]` tương đương `$_POST` và `$_FILES`.

```php
<?php
declare(strict_types=1);

// PHP 8.4+. Gọi bằng: curl -X PUT -d 'name=An&age=20' http://localhost:8000/
var_dump($_POST);                       // PUT không được tự phân tích
// in ra:
// array(0) {
// }

[$post, $files] = request_parse_body();
var_dump($post);
// in ra:
// array(2) {
//   ["name"]=>
//   string(2) "An"
//   ["age"]=>
//   string(2) "20"
// }
```

- Chỉ hỗ trợ hai kiểu `application/x-www-form-urlencoded` và `multipart/form-data`. Gặp kiểu khác (ví
  dụ JSON) nó ném `RequestParseBodyException` với thông báo
  `Content-Type "application/json" is not supported`. JSON thì vẫn đọc `php://input` như mục 2.5.
- ⚠️ Body chỉ được "tiêu thụ" một lần. Theo php.net, nếu body đã bị đọc (ví dụ qua `php://input`) thì
  `request_parse_body()` trả về dữ liệu rỗng. Chọn một trong hai cách đọc, đừng dùng cả hai.
- Tham số `$options` cho phép ghi đè riêng cho lần gọi đó các giới hạn `post_max_size`,
  `upload_max_filesize`, `max_file_uploads`, `max_input_vars`, `max_multipart_body_parts`.

### 2.7 `$_SERVER`: request line, header và môi trường

`$_SERVER` chứa mọi thứ còn lại. Nội dung của nó do web server và SAPI cung cấp nên mỗi môi trường
có thể khác nhau một chút; các key dưới đây hầu như luôn có sau Nginx + PHP-FPM hoặc `php -S`. Giá trị
minh hoạ cho request `GET https://shop.vn/products/index.php?page=2`:

| Key | Ý nghĩa | Ví dụ |
|---|---|---|
| `REQUEST_METHOD` | Method | `GET` |
| `REQUEST_URI` | Đích trong request line, **gồm cả query string** | `/products/index.php?page=2` |
| `QUERY_STRING` | Phần sau `?`, chưa giải mã | `page=2` |
| `SCRIPT_NAME` | Đường dẫn URL của script đang chạy | `/products/index.php` |
| `SCRIPT_FILENAME` | Đường dẫn tuyệt đối của file trên đĩa | `/var/www/html/products/index.php` |
| `DOCUMENT_ROOT` | Thư mục gốc của web | `/var/www/html` |
| `SERVER_PROTOCOL` | Phiên bản giao thức | `HTTP/1.1` |
| `HTTPS` | Có giá trị khác rỗng nếu request đến qua HTTPS | `on` |
| `REMOTE_ADDR` | IP của bên **trực tiếp** kết nối tới web server | `203.0.113.7` |
| `REQUEST_TIME_FLOAT` | Thời điểm PHP bắt đầu xử lý request, có phần micro giây | `1791014400.1234` |
| `HTTP_*` | Mỗi header của request | `HTTP_HOST`, `HTTP_USER_AGENT`... |
| `CONTENT_TYPE`, `CONTENT_LENGTH` | Hai header về body, **không** có tiền tố `HTTP_` | `application/json` |

Quy tắc đổi tên header: viết hoa, thay `-` bằng `_`, thêm `HTTP_` phía trước. `Accept-Language` thành
`HTTP_ACCEPT_LANGUAGE`, `X-Request-Id` thành `HTTP_X_REQUEST_ID`, `Authorization` thành
`HTTP_AUTHORIZATION`. Riêng `Content-Type` và `Content-Length` theo quy ước CGI/1.1 nằm ở
`CONTENT_TYPE`, `CONTENT_LENGTH`. Hàm `getallheaders()` trả mảng header với tên gốc; trên PHP-FPM nó có
từ PHP 7.3.

Lấy đường dẫn không kèm query string để định tuyến (mục 8):

```php
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);   // "/products/index.php"
```

⚠️ Phần lớn `$_SERVER` cũng là input của người dùng:

- **Mọi `HTTP_*` do client tự viết**, kể cả `HTTP_HOST`. Nếu bạn dựng link "đặt lại mật khẩu" từ
  `$_SERVER['HTTP_HOST']`, kẻ tấn công gửi request với `Host: evil.com` và email gửi cho nạn nhân
  chứa link trỏ về `evil.com`. Hãy lấy tên miền từ cấu hình của ứng dụng (như `APP_URL` của Laravel).
- **`REMOTE_ADDR` là IP của bên kết nối trực tiếp.** Khi có load balancer hay CDN đứng trước, đó là IP
  của load balancer; IP thật của người dùng nằm trong header như `X-Forwarded-For`. Nhưng header đó ai
  cũng tự viết được, nên chỉ tin nó khi request thực sự đến từ proxy mà bạn biết (Laravel cấu hình việc
  này bằng *trusted proxies*).
- **`HTTPS`**: php.net chỉ nói nó "khác rỗng" khi qua HTTPS. Một số server (IIS) đặt giá trị `off` khi
  không phải HTTPS, nên kiểm tra như Symfony và Laravel làm:
  `($_SERVER['HTTPS'] ?? '') !== '' && strtolower($_SERVER['HTTPS']) !== 'off'`.
  Sau load balancer kết thúc TLS, PHP có thể thấy HTTP thường dù người dùng đang dùng HTTPS.
- **`PHP_SELF`** gồm cả phần *path info* mà client thêm sau tên script, khi web server chuyển phần đó
  cho PHP (built-in server `php -S` luôn chuyển; Apache, Nginx tuỳ cấu hình): với URL
  `/login.php/bat-ky-gi`, `PHP_SELF` là `/login.php/bat-ky-gi`. In nó vào `<form action="...">` mà
  không escape là XSS. Dùng `SCRIPT_NAME` hoặc để `action=""`.

### 2.8 `$_REQUEST`, `$_ENV` và `variables_order`

`$_REQUEST` gộp `$_GET`, `$_POST` và có thể cả `$_COOKIE` vào một mảng. Gộp thế nào phụ thuộc hai
thiết lập:

- `variables_order` quyết định PHP dựng những superglobal nào. Mặc định gốc là `"EGPCS"` (Env, Get,
  Post, Cookie, Server); file `php.ini-production` và `php.ini-development` đi kèm PHP đặt `"GPCS"`,
  tức không dựng `$_ENV` (lý do hiệu năng). Vì vậy trên nhiều server `$_ENV` rỗng; đọc biến môi
  trường bằng `getenv()`.
- `request_order` quyết định `$_REQUEST` gồm gì và theo thứ tự nào; nguồn đứng sau ghi đè nguồn đứng
  trước khi trùng tên. Mặc định gốc là rỗng, nghĩa là dùng theo `variables_order` (có cả cookie); hai
  file ini mẫu đặt `"GP"` và php.net ghi rõ lý do bỏ `C` là vì bảo mật.

Cùng một request `POST /?x=get&y=get`, body `x=post`, cookie `x=cookie; z=cookie`:

| Cấu hình | `$_REQUEST` |
|---|---|
| Không có php.ini (giá trị mặc định gốc) | `['x' => 'cookie', 'y' => 'get', 'z' => 'cookie']` |
| `request_order = "GP"` (theo file ini mẫu) | `['x' => 'post', 'y' => 'get']` |

Cùng một code mà `$_REQUEST['x']` là `post` ở server này, `cookie` ở server khác. Lời khuyên: **không
dùng `$_REQUEST`**. Đọc rõ ràng từ `$_GET` hoặc `$_POST` để biết dữ liệu đến từ đâu.

Các giới hạn PHP áp lên input:

| Thiết lập | Mặc định | Tác dụng |
|---|---|---|
| `max_input_vars` | 1000 | Số biến tối đa đọc từ mỗi nguồn (GET, POST, COOKIE). Vượt quá thì phần thừa bị bỏ và có warning `Input variables exceeded 1000` |
| `max_input_nesting_level` | 64 | Độ sâu tối đa của tên dạng mảng `a[b][c]...` |
| `post_max_size` | `8M` | Kích thước body tối đa (mục 7.4) |

⚠️ `max_input_vars` gây lỗi rất khó tìm: một form quản trị có 1200 ô (ví dụ bảng phân quyền) gửi lên
thì những ô cuối biến mất lặng lẽ, chỉ để lại một warning trong log.

## 3. Gửi response

### 3.1 Body: mọi thứ script in ra

Trong PHP, body của response chính là **output** của script: mọi thứ `echo`, `print`, `printf()`,
`var_dump()` in ra, mọi đoạn HTML nằm ngoài cặp `<?php ... ?>`, và cả thông báo lỗi nếu
`display_errors` đang bật. Không có hàm "gửi body" riêng.

Còn status code và header thì PHP giữ trong một danh sách trong bộ nhớ. Ban đầu danh sách là: status
`200`, `Content-type: text/html; charset=UTF-8` (từ `default_mimetype` và `default_charset`), và
`X-Powered-By` nếu `expose_php` bật. Bạn sửa danh sách này bằng `header()` và
`http_response_code()`. Khi có byte output đầu tiên cần gửi đi, PHP gửi toàn bộ danh sách header trước,
rồi mới tới byte đó:

```
 header('X-A: 1')     header('X-B: 2')          echo 'Xin chào'
        │                    │                         │
        ▼                    ▼                         ▼
 ┌─────────────────────────────────────┐    output đầu tiên cần gửi
 │ Danh sách header (trong bộ nhớ PHP) │    ──► PHP gửi status line + toàn bộ header
 │ 200, Content-type, X-A, X-B         │        ──► rồi gửi "Xin chào"
 └─────────────────────────────────────┘        ──► từ giờ header đã "đóng"
                                                   header('X-C: 3') → Warning, bị bỏ qua
```

### 3.2 `header()`: đặt header

```php
<?php
declare(strict_types=1);

header('X-Version: 1');
header('X-Version: 2');                      // cùng tên: thay header cũ (replace = true)
header('Link: </a.css>; rel=preload', false);
header('Link: </b.js>; rel=preload', false); // replace = false: thêm dòng thứ hai
header('X-Debug: abc');
header_remove('X-Debug');                    // gỡ header đã đặt nhưng chưa gửi

$before = http_response_code();              // mã hiện tại
$old = http_response_code(404);              // đặt 404, nhận lại mã cũ
$after = http_response_code();

// Chỉ in ra SAU KHI đã đặt xong header và status: in là bắt đầu gửi body
var_dump($before, $old, $after);
print_r(headers_list());
```

Output (gọi qua web server; phiên bản PHP trong `X-Powered-By` tuỳ máy):

```
int(200)
int(200)
int(404)
Array
(
    [0] => X-Powered-By: PHP/8.5.10
    [1] => X-Version: 2
    [2] => Link: </a.css>; rel=preload
    [3] => Link: </b.js>; rel=preload
    [4] => Content-type: text/html; charset=UTF-8
)
```

Response thật có status `404`, một `X-Version: 2`, hai dòng `Link`, không có `X-Debug`.

- `header(string $header, bool $replace = true, int $response_code = 0)`. Tham số thứ hai mặc định
  `true`: header cùng tên đặt sau thay header trước. Truyền `false` để có nhiều dòng cùng tên.
- `headers_list()` cho xem danh sách header sẽ gửi (hoặc đã gửi); `header_remove()` gỡ một header
  chưa gửi.
- Nếu chèn `var_dump(http_response_code());` ngay sau dòng `header_remove()`, lời gọi
  `http_response_code(404)` phía sau sẽ báo warning `Cannot set response code - headers already sent`
  (khi không có output buffer), vì chính `var_dump` là output. Đặt header và status trước, in sau.
- ⚠️ `header()` từ chối chuỗi chứa ký tự xuống dòng. Nếu ghép input của người dùng vào header, ví dụ
  `header('Content-Language: ' . $lang)` với `$lang = "vi\r\nSet-Cookie: admin=1"`, PHP chỉ phát warning
  `Header may not contain more than a single header, new line detected` và **không gửi header đó**. Đây
  là lớp bảo vệ chống *header injection*, nhưng bạn vẫn nên validate input trước khi đưa vào header.

### 3.3 Status code

Hai cách đặt status:

```php
http_response_code(404);                       // cách nên dùng
header('Location: /orders/42', true, 303);     // đặt header kèm status trong một lời gọi
header('HTTP/1.1 404 Not Found');              // cách cũ: tự viết cả status line
```

`http_response_code()` không có tham số thì trả mã hiện tại (mặc định `200`); có tham số thì đặt mã mới
và trả mã cũ. Chạy trong CLI (không có web server) nó trả `false` khi đọc.

⚠️ Status khi script chết vì lỗi nghiêm trọng (fatal error, exception không ai bắt) phụ thuộc
`display_errors`. Mã nguồn PHP (`main/main.c`) chỉ tự đổi status thành `500` khi **cả ba** điều kiện
đúng: `display_errors` tắt, header chưa gửi, và status vẫn đang là `200`. Thử với một script bị
`TypeError` ngay từ đầu:

| `display_errors` | Status nhận được | Body |
|---|---|---|
| `0` (production) | `500` | Trống |
| `1` (dev) | `200` | Thông báo lỗi |

Vì sao? Khi `display_errors` bật, thông báo lỗi được in ra, tức là body đã bắt đầu và header (gồm status
`200`) đã bay đi trước khi PHP kịp đổi. Nên đừng ngạc nhiên khi môi trường dev trả `200` cho một trang
lỗi; còn hệ thống giám sát chỉ đếm đúng lỗi khi `display_errors` tắt. Tương tự, nếu script đã in một
phần trang rồi mới gặp lỗi, client vẫn nhận `200` kèm nửa trang.

### 3.4 Lỗi "headers already sent"

Đây có lẽ là lỗi PHP mà người mới gặp nhiều nhất:

```
Warning: Cannot modify header information - headers already sent by (output started at
/var/www/config.php:6) in /var/www/index.php on line 6
```

Đọc kỹ thông báo: nó chỉ ra **hai** vị trí. `in /var/www/index.php on line 6` là chỗ gọi `header()`
bị từ chối. `output started at /var/www/config.php:6` mới là **thủ phạm**: chỗ in ra byte đầu tiên.
Hãy sửa chỗ thứ hai. Hàm `headers_sent($file, $line)` cho bạn hỏi đúng thông tin đó trong code.

Tái hiện với hai file. `config.php` (để ý sau `?>` có thêm một dòng trống):

```php
<?php
declare(strict_types=1);

const APP_NAME = 'Shop';
?>

```

`index.php`:

```php
<?php
declare(strict_types=1);

require __DIR__ . '/config.php';

header('Location: /dashboard');
exit;
```

Với `output_buffering = 0` (mục 3.5), mở `index.php` sẽ thấy đúng warning ở trên và trình duyệt không
chuyển trang. Nguyên nhân: PHP nuốt **một** ký tự xuống dòng ngay sau `?>`, nhưng dòng trống thứ hai là
văn bản ngoài thẻ PHP, tức là output. Một dòng trống vô hình đã đẩy toàn bộ header đi.

Các thủ phạm hay gặp:

| Thủ phạm | Cách tránh |
|---|---|
| Khoảng trắng, dòng trống sau `?>` cuối một file được `require` | **Không viết `?>` ở cuối file chỉ chứa PHP.** PSR-12 yêu cầu đúng điều này |
| Khoảng trắng hoặc dòng trống trước `<?php` | Bắt đầu file bằng `<?php` ở byte đầu tiên. File có `declare(strict_types=1)` còn bị lỗi compile `strict_types declaration must be the very first statement` nên lộ ra sớm |
| BOM: ba byte ẩn `EF BB BF` mà một số editor chèn vào đầu file khi lưu "UTF-8 with BOM" | Lưu file UTF-8 không BOM; editor hiện đại có tuỳ chọn này |
| `echo`, `var_dump()` để debug đặt trước `header()` | Debug bằng log, hoặc dùng debugger |
| Warning, notice được in ra màn hình (`display_errors=On`) trước `header()` | Sửa lỗi gây warning; production tắt `display_errors` |

### 3.5 Output buffering

*Output buffering* (bộ đệm output) nghĩa là PHP **giữ output lại trong bộ nhớ** thay vì gửi ngay. Khi
output còn nằm trong buffer, chưa có byte nào rời PHP, nên bạn vẫn đặt header thoải mái.

Có hai nguồn bật buffering:

1. Thiết lập `output_buffering` trong php.ini: bật một buffer từ dòng đầu tiên của script. Giá trị
   `Off`/`0` là tắt, `On` là không giới hạn kích thước, một con số (byte) là buffer có giới hạn, đầy thì
   tự gửi đi.
2. Hàm `ob_start()` trong code: mở thêm một buffer. Các buffer lồng nhau thành một chồng (stack); hàm
   `ob_*` chỉ tác động lên buffer trên cùng; `ob_get_level()` cho biết đang lồng mấy tầng.

Giá trị `output_buffering` khác nhau tuỳ môi trường, và đây là nguồn gốc của câu "máy tôi chạy được":

| Môi trường | `output_buffering` |
|---|---|
| Không có php.ini (giá trị mặc định gốc) | `0` |
| Dùng `php.ini-production` hoặc `php.ini-development` đi kèm PHP | `4096` |
| CLI | Luôn tắt, bất kể php.ini |

Image Docker `php` chính thức mặc định không có `php.ini` (chỉ để sẵn hai file mẫu để bạn tự chọn), nên
chạy bằng image đó là `0`. Cùng một code lỗi như mục 3.4 có thể chạy êm trên server có buffer 4096 byte
và hỏng trên máy khác.

⚠️ Buffer 4096 byte còn có thể **giấu lỗi rồi để nó nổ ngẫu nhiên**. Script dưới in ra `n` byte rồi mới
đặt header:

```php
<?php
declare(strict_types=1);

$n = (int) ($_GET['n'] ?? '10');
echo str_repeat('x', $n);          // "nội dung" in ra trước
header('X-Done: 1');               // rồi mới đặt header
var_dump(headers_sent());
```

Với `output_buffering = 4096`:

| Request | Kết quả |
|---|---|
| `?n=100` | Có header `X-Done: 1`, in `bool(false)` |
| `?n=5000` | Warning `headers already sent ... output started at ...:5`, không có `X-Done`, in `bool(true)` |

Trang "thỉnh thoảng không redirect được" thường là thế này: hôm nào dữ liệu nhiều, phần in ra trước
`header()` vượt 4096 byte. Buffer không sửa lỗi; thứ tự đúng (header trước, body sau) mới sửa lỗi.

Công dụng chính đáng của `ob_start()` là **bắt output thành chuỗi**, ví dụ để render một template ra
HTML rồi mới quyết định làm gì với nó:

```php
<?php
declare(strict_types=1);

/** Chạy một template PHP và trả về HTML dạng chuỗi thay vì in thẳng ra. */
function render(string $template, array $vars): string
{
    ob_start();                       // mở một buffer mới: mọi output từ đây bị giữ lại
    try {
        extract($vars);               // biến $vars['title'] thành $title cho template dùng
        require $template;
        return ob_get_clean();        // lấy nội dung buffer và đóng buffer
    } catch (Throwable $e) {
        ob_end_clean();               // lỗi giữa chừng: bỏ phần HTML dở dang
        throw $e;
    }
}

file_put_contents(__DIR__ . '/hello.tpl.php', '<h1><?= htmlspecialchars($title) ?></h1>');

$html = render(__DIR__ . '/hello.tpl.php', ['title' => 'Xin chào <An>']);
header('X-Rendered: yes');            // vẫn đặt header được: chưa có gì được gửi đi
var_dump(ob_get_level());
echo $html, "\n";
unlink(__DIR__ . '/hello.tpl.php');
// in ra (khi output_buffering = 0):
// int(0)
// <h1>Xin chào &lt;An&gt;</h1>
```

Đây cũng là cách các template engine như Blade của Laravel chạy view. `extract()` ở đây chỉ nhận mảng
do code của bạn tạo; ⚠️ đừng bao giờ `extract()` input của người dùng ([chương 17](17-bao-mat.md)).

Muốn đẩy output đi sớm (ví dụ báo tiến độ cho một tác vụ dài) thì làm ngược lại: `ob_flush()` đẩy
buffer của PHP xuống tầng dưới, `flush()` yêu cầu SAPI và web server gửi đi. Nhưng php.net ghi rõ
`flush()` không thắng được cơ chế đệm của web server (Nginx mặc định gom response từ PHP-FPM) hay của
trình duyệt. Streaming response là chủ đề của [chương 18](18-fpm-nginx-opcache.md) và
[chương 20](20-hieu-nang.md).

### 3.6 Trả file cho người dùng tải

```php
<?php
declare(strict_types=1);

// Tạo file mẫu để có cái mà tải
$path = __DIR__ . '/bao-cao.csv';
file_put_contents($path, "id,ten\n1,An\n");

header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="bao-cao-2026-10.csv"');
header('Content-Length: ' . filesize($path));
readfile($path);                    // đọc file và đẩy thẳng ra output theo từng khúc
unlink($path);
exit;
```

`Content-Disposition: attachment` bảo trình duyệt hiện hộp thoại lưu file thay vì mở trong tab, với
tên gợi ý `bao-cao-2026-10.csv`. `readfile()` không nạp cả file vào một biến nên tải file lớn không tốn
RAM theo kích thước file, miễn là không có output buffer nào đang giữ lại toàn bộ (đóng chúng bằng
`ob_end_clean()` trước khi gửi file lớn). ⚠️ Nếu đường dẫn file đến từ người dùng, xem lại path traversal
ở [chương 14](14-file-json-thoi-gian.md) mục 2.6.

Một chi tiết nhỏ: với request `HEAD`, php.net ghi rằng PHP dừng script ngay sau khi gửi header (tức là
sau output đầu tiên nếu không có buffer). Đừng đặt việc quan trọng sau output đầu tiên với giả định
script luôn chạy hết.

## 4. Redirect

### 4.1 Redirect là gì

*Redirect* (chuyển hướng) là response có status `3xx` và header `Location` chứa URL mới. Trình duyệt
nhận nó thì tự gửi một request mới tới URL đó, người dùng chỉ thấy thanh địa chỉ đổi.

```
Trình duyệt                                   Server
    │ POST /orders (tạo đơn) ─────────────────► │
    │ ◄──────────── 303 See Other               │
    │               Location: /orders/42        │
    │ GET /orders/42 ─────────────────────────► │   trình duyệt tự đi, không cần người bấm
    │ ◄──────────── 200 OK + trang đơn hàng     │
```

Các status redirect theo RFC 9110:

| Code | Tên | Tạm thời hay vĩnh viễn | Request tiếp theo dùng method gì |
|---|---|---|---|
| `301` | Moved Permanently | Vĩnh viễn, trình duyệt có thể cache | RFC cho phép (vì lý do lịch sử) đổi `POST` thành `GET`, và trình duyệt thực tế làm vậy |
| `302` | Found | Tạm thời | Như `301`: `POST` thành `GET` |
| `303` | See Other | Tạm thời | Luôn là `GET` (hoặc `HEAD`) |
| `307` | Temporary Redirect | Tạm thời | Bắt buộc giữ nguyên method và body |
| `308` | Permanent Redirect | Vĩnh viễn, có thể cache | Bắt buộc giữ nguyên method và body |

Chọn nhanh: sau khi xử lý form `POST` thì dùng `303`; đổi URL vĩnh viễn (đổi tên miền, đổi cấu trúc
link) dùng `301` hoặc `308`; chuyển tạm một trang `GET` (ví dụ chưa đăng nhập thì sang `/login`) dùng
`302`. ⚠️ Cẩn thận với `301`: trình duyệt có thể nhớ nó rất lâu, đặt nhầm thì người dùng cũ bị kẹt ở URL
mới kể cả khi bạn đã sửa server.

### 4.2 Redirect trong PHP

```php
<?php
declare(strict_types=1);

header('Location: /orders/42', true, 303);
exit;
```

Nếu không truyền status, `header('Location: ...')` tự đặt status theo luật sau (trong `main/SAPI.c`
của php-src): nếu status hiện tại đã là `201` hoặc một mã `3xx` thì giữ nguyên; nếu không, đặt `302`.
Riêng khi SAPI báo request là HTTP/1.1 trở lên (biến `proto_num` lớn hơn `1000`) và method không phải
`GET`/`HEAD` thì đặt `303`. Module Apache báo đúng giá trị này, nên redirect từ một `POST` ra `303`.
PHP-FPM không tính phiên bản giao thức (code có ghi chú `FIXME`, giữ mặc định HTTP/1.0), còn built-in
server `php -S` lưu phiên bản theo cách đánh số khác (`101` cho HTTP/1.1) nên điều kiện trên không bao giờ
đúng; ở hai SAPI này redirect từ một `POST` vẫn ra `302`. Hành vi khác nhau theo SAPI là lý do nên
**luôn ghi rõ status**.

Theo RFC 9110, `Location` có thể là URL tương đối (`/orders/42`); trình duyệt hiện đại đều hiểu.

### 4.3 Luôn `exit` sau redirect

`header()` chỉ thêm một dòng vào danh sách header, **không dừng script**. Code phía sau vẫn chạy:

```php
<?php
declare(strict_types=1);

session_start();

if (($_SESSION['role'] ?? '') !== 'admin') {
    header('Location: /login', true, 302);
    // QUÊN exit: script chạy tiếp xuống dưới
}

deleteAllUsers();     // (hàm minh hoạ) khách chưa đăng nhập vẫn chạy tới dòng này
```

Trình duyệt thấy `302` thì chuyển sang `/login`, nên khi thử bằng trình duyệt bạn tưởng trang đã được
bảo vệ. Nhưng code xoá dữ liệu đã chạy xong ở server. Kẻ tấn công dùng `curl` (mặc định không đi theo
redirect) còn đọc được cả body. Quy tắc: `header('Location: ...')` luôn đi kèm `exit;` ngay sau, hoặc
gói vào một hàm kiểu `never` như `sendJson()` ở mục 2.5.

### 4.4 Post/Redirect/Get

Nếu trang xử lý form trả thẳng HTML "Đặt hàng thành công", người dùng bấm F5 sẽ khiến trình duyệt hỏi
"Gửi lại biểu mẫu?" và một cú bấm "Tiếp tục" là thêm một đơn hàng. Mẫu *Post/Redirect/Get* (PRG) tránh
việc đó:

| Bước | Trình duyệt | Server | Kết quả |
|---|---|---|---|
| 1 | `POST /orders` với dữ liệu form | Validate, lưu đơn 42 | |
| 2 | | Trả `303`, `Location: /orders/42`, không có HTML | |
| 3 | Tự gửi `GET /orders/42` | Đọc đơn 42, trả HTML | Trang cuối cùng là kết quả của một `GET` |
| 4 | Người dùng bấm F5 | Nhận lại `GET /orders/42` | Chỉ tải lại trang xem, không tạo thêm đơn |

Muốn hiện thông báo "Đặt hàng thành công" ở bước 3, bạn cần chuyển một mẩu tin từ request này sang
request sau. HTTP không nhớ gì, nên phải nhờ session (mục 6.3 có ví dụ *flash message*). Validation
lỗi cũng đi theo đường này: redirect về form kèm lỗi và dữ liệu cũ trong session; Laravel làm sẵn việc
này ([chương 25](25-laravel-request-validation-response.md)).

### 4.5 Open redirect

Trang đăng nhập thường nhận `?next=/cart` để đăng nhập xong quay về đúng chỗ. Nếu bạn redirect thẳng tới
`$_GET['next']`, kẻ tấn công gửi cho nạn nhân link `https://shop.vn/login?next=https://evil.com`: link
nhìn như của bạn, đăng nhập xong nạn nhân bị chuyển sang trang giả. Đó là lỗ hổng *open redirect*.

Cách chặn: chỉ chấp nhận đường dẫn trong chính site, hoặc so với một danh sách cho phép.

```php
<?php
declare(strict_types=1);

/** Chỉ chấp nhận đường dẫn tương đối trong chính site; còn lại trả về trang mặc định. */
function safeNext(mixed $next, string $default = '/'): string
{
    if (!is_string($next)
        || !str_starts_with($next, '/')        // phải là đường dẫn tuyệt đối trong site: /cart
        || str_starts_with($next, '//')        // //evil.com là URL sang host khác
        || str_starts_with($next, '/\\')       // /\evil.com: trình duyệt coi \ như /
        || preg_match('/[\x00-\x1F\x7F]/', $next) === 1   // ký tự điều khiển, xuống dòng
    ) {
        return $default;
    }
    return $next;
}

foreach (['/cart', '/orders?id=5', 'https://evil.com', '//evil.com', '/\\evil.com', "/a\r\nb", 'cart', ['x']] as $n) {
    printf("%-20s => %s\n", json_encode($n, JSON_UNESCAPED_SLASHES), safeNext($n));
}
// in ra:
// "/cart"              => /cart
// "/orders?id=5"       => /orders?id=5
// "https://evil.com"   => /
// "//evil.com"         => /
// "/\\evil.com"        => /
// "/a\r\nb"            => /
// "cart"               => /
// ["x"]                => /
```

`//evil.com` là *protocol-relative URL*: trình duyệt hiểu là "cùng giao thức, host `evil.com`", nên
chỉ kiểm tra "bắt đầu bằng `/`" là chưa đủ. Chi tiết các lỗ hổng web ở [chương 17](17-bao-mat.md).

## 5. Cookie

### 5.1 Cookie là gì

HTTP không nhớ gì giữa hai request (mục 1.1). *Cookie* là cách đơn giản nhất để có "trí nhớ": server
nhờ trình duyệt **giữ hộ** một mẩu dữ liệu nhỏ, và trình duyệt tự gửi lại mẩu đó trong mọi request sau
tới cùng site. Cơ chế được chuẩn hoá trong RFC 6265 và chỉ dùng hai header:

- Response có header `Set-Cookie: theme=dark; Path=/; ...`: "hãy lưu cookie `theme` giá trị `dark`,
  kèm các thuộc tính này".
- Mọi request sau phù hợp với thuộc tính đó có header `Cookie: theme=dark; lang=vi`: trình duyệt gửi
  lại tất cả cookie đang giữ cho site (chỉ tên và giá trị, không gửi thuộc tính).

| Bước | Trình duyệt | Server PHP | Trong `$_COOKIE` |
|---|---|---|---|
| 1 | `GET /` (chưa có cookie nào) | Gọi `setcookie('theme', 'dark')`, response có `Set-Cookie: theme=dark` | `[]` |
| 2 | Lưu `theme=dark` vào kho cookie | | |
| 3 | `GET /products`, tự gắn `Cookie: theme=dark` | Đọc `$_COOKIE['theme']` | `['theme' => 'dark']` |
| 4 | Mọi request sau tới site đều gắn `Cookie: theme=dark` cho tới khi cookie hết hạn hoặc bị xoá | | `['theme' => 'dark']` |

### 5.2 Đặt cookie bằng `setcookie()`

Từ PHP 7.3 `setcookie()` nhận một mảng tuỳ chọn, cách viết nên dùng vì rõ ràng và có `samesite`:

```php
<?php
declare(strict_types=1);

setcookie('theme', 'dark', [
    'expires'  => time() + 30 * 24 * 3600,  // 30 ngày nữa
    'path'     => '/',
    'secure'   => true,
    'httponly' => true,
    'samesite' => 'Lax',
]);
setcookie('ghi_chu', 'xin chào & tạm biệt');   // cookie phiên, giá trị có dấu cách, ký tự đặc biệt
setcookie('old', '', ['expires' => 1, 'path' => '/']);   // xoá cookie
setcookie('gone');                               // value rỗng
var_dump($_COOKIE['theme'] ?? 'chưa có');        // cookie vừa đặt chưa có trong request này
print_r(array_filter(headers_list(), fn(string $h): bool => str_starts_with($h, 'Set-Cookie')));
```

Output (ngày trong `expires` tuỳ lúc chạy):

```
string(9) "chưa có"
Array
(
    [1] => Set-Cookie: theme=dark; expires=Mon, 02 Nov 2026 10:11:02 GMT; Max-Age=2592000; path=/; secure; HttpOnly; SameSite=Lax
    [2] => Set-Cookie: ghi_chu=xin%20ch%C3%A0o%20%26%20t%E1%BA%A1m%20bi%E1%BB%87t
    [3] => Set-Cookie: old=deleted; expires=Thu, 01 Jan 1970 00:00:01 GMT; Max-Age=0; path=/
    [4] => Set-Cookie: gone=deleted; expires=Thu, 01 Jan 1970 00:00:01 GMT; Max-Age=0
)
```

Đọc từng dòng:

- `setcookie()` chỉ thêm một header `Set-Cookie` vào danh sách, nên chịu đúng luật của `header()`: phải
  gọi trước output đầu tiên. Có output rồi thì nó trả `false` kèm warning "headers already sent".
- Bạn truyền `expires` là Unix timestamp; PHP tự đổi sang ngày dạng `expires=...` và thêm `Max-Age`
  (số giây còn lại). Trình duyệt nào hiểu `Max-Age` sẽ ưu tiên nó.
- Giá trị được PHP tự mã hoá bằng percent-encoding (`%20` cho dấu cách, `%C3%A0` cho "à"), và tự giải
  mã khi bạn đọc `$_COOKIE`. Muốn tự lo việc mã hoá thì dùng `setrawcookie()`.
- `ghi_chu` không có `expires` nên là *session cookie* (cookie phiên): trình duyệt xoá khi đóng phiên
  duyệt web. Chữ "session" ở đây không liên quan tới session của PHP ở mục 6. Một số trình duyệt có tính
  năng "mở lại các tab trước" giữ luôn cả cookie phiên, nên đừng coi đó là cơ chế bảo mật.
- `var_dump` in `"chưa có"`: `$_COOKIE` được dựng từ header `Cookie` của **request hiện tại**. Cookie
  vừa đặt chỉ xuất hiện từ request sau (bước 3 ở bảng mục 5.1).
- Truyền một key không hỗ trợ (ví dụ gõ nhầm `expire` thay vì `expires`) thì từ PHP 8.0 là
  `ValueError: setcookie(): option "expire" is invalid`.

### 5.3 Xoá cookie

Server không ra lệnh "xoá" trực tiếp được. Cách duy nhất là gửi lại cookie cùng tên với thời hạn trong
quá khứ, trình duyệt thấy hết hạn thì bỏ. Hai dòng cuối của output trên cho thấy PHP làm đúng như vậy:
giá trị thành `deleted`, `expires` là năm 1970, `Max-Age=0`.

- ⚠️ Phải xoá **cùng `path` và `domain`** như lúc đặt. Đặt với `'path' => '/'` mà xoá không ghi `path`
  thì trình duyệt coi là một cookie khác, cookie cũ vẫn còn.
- ⚠️ Gọi `setcookie('x', '')` (giá trị rỗng) cũng là xoá, như dòng `gone`. Muốn lưu "rỗng" thì lưu một
  giá trị như `'0'`.
- `unset($_COOKIE['x'])` chỉ xoá phần tử trong mảng của request hiện tại, không đụng tới trình duyệt.

### 5.4 Các thuộc tính quyết định cookie được gửi đi đâu

| Thuộc tính | Nghĩa | Khuyến nghị |
|---|---|---|
| `expires` / `Max-Age` | Khi nào hết hạn. Không có thì là cookie phiên | Đặt thời hạn ngắn nhất đủ dùng |
| `path` | Chỉ gửi cho URL bắt đầu bằng đường dẫn này. Không ghi thì mặc định là "thư mục" của URL đang đặt cookie | Gần như luôn `/`, để tránh cookie chỉ hiện ở một số trang |
| `domain` | Không ghi: chỉ gửi về **đúng host** đã đặt (*host-only*). Ghi `shop.vn`: gửi cho `shop.vn` và **mọi subdomain** (`api.shop.vn`, `blog.shop.vn`) | Không ghi, trừ khi thật sự cần chia sẻ giữa các subdomain |
| `secure` | Chỉ gửi qua HTTPS | Luôn bật trên production |
| `httponly` | JavaScript trên trang không đọc được cookie qua `document.cookie` | Bật cho mọi cookie mà JavaScript không cần đọc, bắt buộc cho session ID |
| `samesite` | Có gửi cookie khi request xuất phát từ site khác không (`Strict`, `Lax`, `None`) | `Lax` là mặc định hợp lý; `Strict` cho thao tác nhạy cảm |
| `partitioned` | Cookie trong ngữ cảnh bên thứ ba được tách riêng theo site cấp cao nhất (CHIPS) | Chỉ khi nhúng dịch vụ của bạn vào site khác |

Vì sao `secure` và `httponly` quan trọng? Cookie thường chứa thứ quý nhất: session ID, tức "chìa khoá"
đăng nhập (mục 6). Thiếu `secure`, cookie có thể đi qua HTTP thường và bị đọc trên mạng Wi-Fi công
cộng. Thiếu `httponly`, chỉ cần một lỗ hổng XSS là đoạn script của kẻ tấn công đọc `document.cookie`
và gửi chìa khoá đi.

**SameSite** cần giải thích kỹ hơn. Hai URL là *cùng site* (same-site) khi cùng scheme và cùng tên miền
đăng ký được (`https://shop.vn` và `https://api.shop.vn` là cùng site; `https://evil.com` là khác site).
Thuộc tính `SameSite` quyết định cookie của `shop.vn` có được gửi kèm khi request tới `shop.vn` được
khởi phát từ một trang **khác site** hay không:

| Tình huống (người dùng đang ở `evil.com`) | `Strict` | `Lax` | `None` (phải kèm `Secure`) |
|---|---|---|---|
| Bấm link sang `https://shop.vn/orders` (điều hướng cấp cao nhất, `GET`) | Không gửi | Gửi | Gửi |
| Form trên `evil.com` tự `POST` sang `https://shop.vn/transfer` | Không gửi | Không gửi | Gửi |
| `<img src="https://shop.vn/...">`, `fetch()`, `<iframe>` tới `shop.vn` | Không gửi | Không gửi | Gửi |

Ở cột `None`, hàng thứ ba còn tuỳ trình duyệt: trình duyệt chặn hoặc tách riêng cookie bên thứ ba
(như Safari, Firefox theo mặc định) có thể vẫn không gửi.

Hàng thứ hai chính là kịch bản tấn công *CSRF*: trang lạ khiến trình duyệt của nạn nhân gửi request kèm
cookie đăng nhập. `Lax` chặn được dạng phổ biến nhất của nó, nhưng không thay thế CSRF token
([chương 17](17-bao-mat.md)). `Strict` an toàn hơn nhưng bất tiện: người dùng bấm link từ email sang
trang của bạn sẽ thấy như chưa đăng nhập.

Ba cạm bẫy với `samesite`:

- ⚠️ Không ghi `samesite` thì PHP **không gửi** thuộc tính này, và hành vi phụ thuộc trình duyệt:
  Chrome (và các trình duyệt dựa trên Chromium) coi như `Lax`, không phải trình duyệt nào cũng vậy.
  Luôn ghi rõ.
- ⚠️ `None` mà không có `secure` thì theo php.net cookie bị trình duyệt chặn. PHP vẫn gửi đi bình
  thường, không báo lỗi.
- ⚠️ PHP không kiểm tra giá trị: `'samesite' => 'Bogus'` vẫn được gửi thành `SameSite=Bogus`. Gõ sai
  chính tả là mất bảo vệ mà không có cảnh báo nào.

**Partitioned** là thuộc tính mới: PHP 8.5 thêm key `partitioned` cho `setcookie()`, cho
`session_set_cookie_params()` và thêm thiết lập `session.cookie_partitioned` cho cookie session.
Nó yêu cầu `secure`, thiếu thì `ValueError: setcookie(): "partitioned" option cannot be used without
"secure" option`. Trên PHP 8.4 key này chưa tồn tại nên là `ValueError` "option is invalid"; khi đó
phải tự viết header như ví dụ trên php.net:
`header('Set-Cookie: name=value; Secure; Path=/; SameSite=None; Partitioned;')`.

**Tiền tố tên cookie.** Trình duyệt hiện đại áp luật đặc biệt cho cookie có tên bắt đầu bằng `__Host-`
(bắt buộc `Secure`, `Path=/`, không có `Domain`, tức chỉ gắn với đúng một host) và `__Secure-` (bắt
buộc `Secure`). Cookie đặt sai luật bị từ chối. Đặt session cookie tên `__Host-sid` là cách chặn
subdomain khác (có thể bị chiếm) ghi đè cookie của bạn.

### 5.5 Cookie là dữ liệu người dùng kiểm soát

Người dùng mở DevTools của trình duyệt là sửa được mọi cookie, kể cả cookie `httponly` (`httponly` chỉ
ngăn JavaScript của trang đọc, không ngăn chủ máy). Vì vậy:

- ⚠️ **Không bao giờ** lưu thứ quyết định quyền vào cookie dạng trần: `role=admin`, `user_id=5`,
  `price=100000`. Người dùng sửa thành `role=admin` là thành admin.
- Cookie bị gửi kèm **mọi** request tới site (cả request ảnh, CSS nếu cùng domain), nên cookie to làm
  chậm mọi thứ. RFC 6265 chỉ yêu cầu trình duyệt hỗ trợ tối thiểu 4096 byte mỗi cookie và 50 cookie mỗi
  domain; đừng dựa vào nhiều hơn.
- Tên cookie cũng bị đổi như tên biến GET: cookie `a.b` vào PHP thành `$_COOKIE['a_b']`. Từ PHP 7.4.11
  (và 7.3.23, 7.2.34) tên cookie **không còn bị giải mã** percent-encoding nữa, vì lý do bảo mật: trước
  đó kẻ tấn công gửi `%5F%5FHost-x` là có thể giả một cookie `__Host-x`.

Khi thật sự cần lưu dữ liệu ở cookie mà không cho người dùng sửa, hãy **ký** nó bằng HMAC: server gắn
thêm một chữ ký tính từ giá trị và một khoá bí mật; người dùng sửa giá trị thì chữ ký không còn khớp.

```php
<?php
declare(strict_types=1);

// Khoá bí mật chỉ server biết. Thật thì đọc từ biến môi trường, không viết cứng trong code.
const COOKIE_KEY = 'doi-thanh-chuoi-ngau-nhien-dai-32-byte-tro-len';

/** Gắn chữ ký HMAC vào giá trị: "giá trị.chữ ký". */
function signValue(string $value): string
{
    return $value . '.' . hash_hmac('sha256', $value, COOKIE_KEY);
}

/** Trả về giá trị gốc nếu chữ ký đúng, null nếu cookie bị sửa. */
function verifyValue(string $signed): ?string
{
    $pos = strrpos($signed, '.');
    if ($pos === false) {
        return null;
    }
    $value = substr($signed, 0, $pos);
    $mac = substr($signed, $pos + 1);
    $expected = hash_hmac('sha256', $value, COOKIE_KEY);
    return hash_equals($expected, $mac) ? $value : null;   // so sánh thời gian hằng
}

$cookie = signValue('vi');
echo $cookie, "\n";
var_dump(verifyValue($cookie));                         // giá trị hợp lệ
var_dump(verifyValue('en' . substr($cookie, 2)));       // người dùng sửa "vi" thành "en"
// in ra:
// vi.54dd6260e2272ed0670eda21750ceb29789de0dc2cdaae74a7667d9063fa09e3
// string(2) "vi"
// NULL
```

Ký chỉ chống **sửa**, không chống **đọc**: ai cũng thấy giá trị `vi`. Muốn giấu nội dung thì phải mã
hoá (Laravel mặc định mã hoá cookie của các route nhóm `web` bằng `APP_KEY`; mã hoá trong PHP thuần bằng `sodium` ở
[chương 17](17-bao-mat.md)). `hash_equals()` so sánh hai chuỗi trong thời gian không phụ thuộc vị trí
khác nhau đầu tiên, tránh để lộ chữ ký qua đo thời gian; lý do chi tiết cũng ở chương 17.

Cách tốt hơn trong đa số trường hợp: cookie chỉ chứa một **mã định danh ngẫu nhiên**, còn dữ liệu thật
nằm ở server. Đó chính là session.

## 6. Session

### 6.1 Ý tưởng: cookie giữ chìa khoá, server giữ dữ liệu

Mục 5.5 kết luận: đừng để dữ liệu quan trọng nằm ở cookie. *Session* (phiên làm việc) giải quyết đúng
chuyện đó:

1. Lần đầu người dùng ghé, server sinh một chuỗi ngẫu nhiên khó đoán gọi là *session ID*, ví dụ
   `fca6900c81e53defa79e31508ca9c796`, và gửi nó về trong một cookie.
2. Dữ liệu thật (`user_id`, giỏ hàng...) nằm ở **server**, trong một "ngăn kéo" đánh dấu bằng ID đó.
3. Mỗi request sau, trình duyệt gửi lại cookie; server dùng ID mở đúng ngăn kéo.

Người dùng chỉ cầm chìa khoá, không thấy và không sửa được dữ liệu. Đổi lại, **ai cầm được chìa khoá thì
là người dùng đó**: lộ session ID tương đương lộ mật khẩu trong suốt thời gian session còn sống. Gần như
mọi chuyện bảo mật session (mục 6.6, 6.7) xoay quanh việc giữ chìa khoá này.

### 6.2 Dùng session trong PHP

```php
<?php
declare(strict_types=1);

session_start();

$_SESSION['views'] = ($_SESSION['views'] ?? 0) + 1;
$_SESSION['user'] = ['name' => 'An', 'role' => 'member'];

echo 'Session ID: ', session_id(), "\n";
echo 'Lượt xem: ', $_SESSION['views'], "\n";
```

Gọi ba lần liên tiếp bằng `curl` có lưu cookie (terminal 2):

```bash
curl -c jar.txt -b jar.txt http://localhost:8000/
curl -c jar.txt -b jar.txt http://localhost:8000/
curl -c jar.txt -b jar.txt http://localhost:8000/
```

```
Session ID: fca6900c81e53defa79e31508ca9c796
Lượt xem: 1
Session ID: fca6900c81e53defa79e31508ca9c796
Lượt xem: 2
Session ID: fca6900c81e53defa79e31508ca9c796
Lượt xem: 3
```

(ID trên máy bạn sẽ khác.) Bỏ `-b jar.txt` thì lần nào cũng là "Lượt xem: 1" với một ID mới, vì không
gửi lại cookie nghĩa là không cầm chìa khoá.

- `session_start()` phải được gọi trước khi dùng `$_SESSION`, ở **mọi** request cần session. Không
  gọi thì `$_SESSION` không có dữ liệu cũ.
- `session_start()` gửi header (`Set-Cookie`, và các header chống cache ở mục 6.3), nên phải gọi trước
  output. Gọi sau output thì nhận warning `Session cannot be started after headers have already been
  sent` và hàm trả `false`.
- `$_SESSION` là mảng bình thường: gán, đọc, `unset()`. Bạn không phải gọi hàm "lưu"; PHP tự lưu khi
  script kết thúc.

### 6.3 Bên trong: chuyện gì xảy ra ở mỗi request

Với *save handler* mặc định là `files` (lưu mỗi session thành một file), một request có session đi
qua các bước:

```
 Request: Cookie: PHPSESSID=fca69...
     │
     ▼
 session_start()
   1. Đọc tên cookie theo session.name (mặc định PHPSESSID) → lấy ID fca69...
      (không có cookie → sinh ID mới, chuẩn bị Set-Cookie)
   2. Mở file  <session.save_path>/sess_fca69...   và KHOÁ file (flock, khoá độc quyền)
   3. Đọc nội dung, unserialize thành mảng $_SESSION
     │
     ▼
 Code của bạn đọc, ghi $_SESSION
     │
     ▼
 Cuối request (hoặc khi gọi session_write_close())
   4. serialize $_SESSION, ghi đè vào file
   5. Nhả khoá, đóng file
```

Nhìn tận mắt file session sau ba lượt xem ở mục 6.2:

```
sess_fca6900c81e53defa79e31508ca9c796 => views|i:3;user|a:2:{s:4:"name";s:2:"An";s:4:"role";s:6:"member";}
```

Định dạng này là của *serialize handler* `php` (mặc định): mỗi key ghi thành `tên|`, nối với giá trị đã
`serialize()` ([chương 10](10-oop-nang-cao.md) mục 11). Hệ quả:

- ⚠️ Dấu `|` là ký tự phân cách nên **key của `$_SESSION` không được chứa `|`**. Có một key như vậy là
  PHP không ghi được cả session. PHP 8.4 trở về trước im lặng bỏ qua (dữ liệu mất mà không báo gì); từ
  PHP 8.5 có warning `Failed to write session data. Data contains invalid key "a|b"`.
- Lưu object vào session thì file chứa object đã serialize, và class phải được nạp được khi
  `session_start()` unserialize. Lưu dữ liệu đơn giản (số, chuỗi, mảng) là an toàn nhất.

Mặc định `session.save_path` rỗng, nghĩa là dùng thư mục tạm của hệ thống (thường là `/tmp`). php.net
cảnh báo: nếu thư mục đó ai cũng đọc được danh sách file, người dùng khác trên cùng máy có thể lấy được
session ID từ tên file. Production nên trỏ `session.save_path` vào thư mục riêng, chỉ user chạy PHP có
quyền; một số bản phân phối Linux đã làm sẵn việc này.

`session_start()` còn gửi header chống cache theo `session.cache_limiter` (mặc định `nocache`), vì trang
có session thường chứa dữ liệu riêng của từng người, không được để proxy cache lại rồi trả cho người khác:

```
Set-Cookie: PHPSESSID=fca6900c81e53defa79e31508ca9c796; path=/
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
```

`Set-Cookie` chỉ xuất hiện khi PHP cần gửi ID mới (lần đầu, hoặc khi đổi ID); các request sau đã có
cookie thì không gửi lại.

Giờ bạn có đủ công cụ cho *flash message* đã hứa ở mục 4.4: một thông báo ghi vào session ở request này
để request sau đọc đúng một lần rồi xoá.

```php
<?php
declare(strict_types=1);

session_start();

/** Ghi một thông báo để request SAU đọc đúng một lần. */
function flash(string $message): void
{
    $_SESSION['flash'][] = $message;
}

/** Lấy ra và xoá các thông báo đang chờ. */
function takeFlashes(): array
{
    $messages = $_SESSION['flash'] ?? [];
    unset($_SESSION['flash']);
    return $messages;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // ... validate và lưu đơn hàng ...
    flash('Đặt hàng thành công!');
    header('Location: /', true, 303);
    exit;
}

foreach (takeFlashes() as $m) {
    echo '<p class="ok">', htmlspecialchars($m), "</p>\n";
}
echo "<form method=\"post\"><button>Đặt hàng</button></form>\n";
```

| Bước | Request | Server | Người dùng thấy |
|---|---|---|---|
| 1 | `GET /` | Không có flash | Form |
| 2 | Bấm nút: `POST /` | Ghi flash vào session, trả `303` về `/` | (trình duyệt tự đi tiếp) |
| 3 | `GET /` | Lấy flash ra rồi xoá khỏi session | "Đặt hàng thành công!" và form |
| 4 | F5: `GET /` | Flash đã bị xoá ở bước 3 | Chỉ còn form |

### 6.4 Session ID và các thiết lập quan trọng

Session ID mặc định là 32 ký tự hex (`session.sid_length = 32`, `session.sid_bits_per_character = 4`),
tức 128 bit ngẫu nhiên, đủ để không ai đoán được. Từ PHP 8.4, đổi hai thiết lập này bị deprecated;
php.net khuyên giữ mặc định.

| Thiết lập | Mặc định (không có php.ini) | Nên đặt | Ghi chú |
|---|---|---|---|
| `session.use_strict_mode` | `0` | `1` | php.net gọi là "bắt buộc" cho session an toàn (mục 6.6) |
| `session.cookie_httponly` | `0` | `1` | Chặn JavaScript đọc session ID |
| `session.cookie_secure` | `0` | `1` khi site chạy HTTPS | Bật lên thì session chỉ hoạt động qua HTTPS |
| `session.cookie_samesite` | `""` (không gửi) | `Lax` hoặc `Strict` | |
| `session.use_only_cookies` | `1` | Giữ `1` | Chỉ nhận ID từ cookie, không nhận từ URL. Tắt nó bị deprecated từ PHP 8.4 |
| `session.use_trans_sid` | `0` | Giữ `0` | Bật thì PHP chèn ID vào link trên trang, dễ lộ qua URL. Bật bị deprecated từ PHP 8.4 |
| `session.cookie_lifetime` | `0` | `0` | Cookie phiên, mất khi đóng trình duyệt |
| `session.gc_maxlifetime` | `1440` (24 phút) | Nhỏ nhất có thể | Sau bao nhiêu giây không hoạt động thì dữ liệu được coi là rác |
| `session.gc_probability` / `session.gc_divisor` | `1` / `100` | | Xác suất dọn rác mỗi lần `session_start()`; `php.ini-production` đặt divisor `1000` |
| `session.name` | `PHPSESSID` | Tuỳ | Tên cookie. Chạy HTTPS thì có thể đặt `__Host-sid` (mục 5.4) kèm `cookie_secure`; PHP chấp nhận tên này |

Các thiết lập này đặt trong php.ini, hoặc truyền thẳng cho `session_start()` dưới dạng mảng (bỏ tiền tố
`session.`), như ví dụ ở mục 6.6.

Về **dọn rác** (*garbage collection*, GC): file session của người đã bỏ đi không tự biến mất. Mỗi lần
có `session_start()`, PHP tung xúc xắc với xác suất `gc_probability / gc_divisor`; trúng thì quét và
xoá các session không hoạt động quá `gc_maxlifetime` giây. php.net nhấn mạnh cơ chế xác suất này
**không đảm bảo** session hết hạn đúng giờ: site ít người thì GC hiếm khi chạy, session cũ sống lâu hơn
bạn nghĩ. Nếu cần "tự đăng xuất sau 30 phút không hoạt động" chính xác, hãy tự lưu timestamp vào
`$_SESSION` và tự kiểm tra; việc dọn rác thì giao cho cron gọi `session_gc()`.

### 6.5 Khoá session: vì sao request của bạn xếp hàng

Bước 2 ở mục 6.3 khoá file session cho tới khi request kết thúc. php.net nói rõ trong trang
`session_write_close()`: dữ liệu session bị khoá để chống ghi đồng thời, nên **mỗi lúc chỉ một script
được làm việc với một session**. Với handler `files`, khoá là `flock()` độc quyền
([chương 14](14-file-json-thoi-gian.md)).

Hậu quả thấy được: một người dùng mở trang xuất báo cáo mất 10 giây, rồi bấm sang trang khác:

| Bước | Request A (`/report`, cùng session) | Request B (`/products`, cùng session) | Kết quả |
|---|---|---|---|
| 1 | `session_start()`: khoá file `sess_abc` | | |
| 2 | Chạy truy vấn nặng, 10 giây | Gửi tới, `session_start()` chờ khoá | B đứng yên dù trang rất nhẹ |
| 3 | Kết thúc, ghi session, nhả khoá | | |
| 4 | | Có khoá, chạy tiếp | Người dùng chờ B gần 10 giây |

Trang có nhiều request AJAX song song cùng session cũng bị xếp hàng y như vậy. Cách xử lý:

- Gọi `session_write_close()` ngay khi đã đọc, ghi xong session, trước phần việc chậm. Sau đó vẫn đọc
  được `$_SESSION` trong bộ nhớ, nhưng thay đổi không còn được lưu.
- Request chỉ cần đọc session thì mở bằng `session_start(['read_and_close' => true])`: đọc xong đóng
  ngay, không giữ khoá.

```php
<?php
declare(strict_types=1);

session_start(['read_and_close' => true]);   // đọc xong đóng ngay, nhả khoá
var_dump($_SESSION['user_id'] ?? null);       // vẫn đọc được: int(42) nếu đã đăng nhập
var_dump(session_status() === PHP_SESSION_NONE);   // in ra: bool(true), session không còn mở
$_SESSION['x'] = 1;                                 // không được lưu: session đã đóng
```

Khoá này là đặc điểm của handler `files` và của cách PHP quản lý session. Handler khác (Redis,
database, handler bạn tự viết) có cơ chế khoá riêng hoặc không khoá. Laravel không dùng session gốc của
PHP mà tự quản lý; theo mặc định các request cùng session chạy song song không khoá, và nếu cần thì bật
khoá cho từng route bằng `block()` ([chương 29](29-laravel-queue-event-schedule-cache.md)). Không khoá
thì nhanh, nhưng hai request cùng ghi session sẽ có một bên ghi đè bên kia.

### 6.6 Session fixation và `session_regenerate_id()`

*Session fixation* là kiểu tấn công mà kẻ xấu **không cần lấy trộm** ID của nạn nhân; hắn **cài sẵn**
một ID hắn biết vào trình duyệt nạn nhân, chờ nạn nhân đăng nhập, rồi dùng chính ID đó.

Thử nghiệm sau cho thấy PHP mặc định sẵn sàng "nhận nuôi" một ID do client tự bịa. Script chỉ có
`session_start(); echo session_id();`, gửi request với cookie tự viết `PHPSESSID=hacker123`:

| `session.use_strict_mode` | Kết quả |
|---|---|
| `0` (mặc định) | In `hacker123`: PHP dùng luôn ID lạ, tạo session mới với ID đó |
| `1` | In một ID mới do PHP sinh, kèm `Set-Cookie` gửi ID mới về |

Kịch bản tấn công khi `use_strict_mode = 0` và ứng dụng không đổi ID lúc đăng nhập:

| Bước | Kẻ tấn công | Nạn nhân | Server | Kết quả |
|---|---|---|---|---|
| 1 | Bằng cách nào đó đặt cookie `PHPSESSID=hacker123` vào trình duyệt nạn nhân (ví dụ qua một subdomain bị chiếm, hoặc lỗ hổng XSS) | | | |
| 2 | | Mở `shop.vn`, gửi `Cookie: PHPSESSID=hacker123` | Nhận ID lạ, tạo session `hacker123` | |
| 3 | | Đăng nhập thành công | Ghi `user_id = 42` vào session `hacker123` | Session `hacker123` giờ là "đã đăng nhập" |
| 4 | Gửi request với `Cookie: PHPSESSID=hacker123` | | Mở session `hacker123`, thấy `user_id = 42` | Kẻ tấn công vào được tài khoản nạn nhân |

Hai lớp phòng thủ, nên dùng cả hai:

1. `session.use_strict_mode = 1`: PHP từ chối ID chưa từng được chính nó khởi tạo. Chặn bước 2.
2. **Đổi session ID mỗi khi quyền hạn thay đổi**, đặc biệt ngay khi đăng nhập thành công, bằng
   `session_regenerate_id()`. Dù kẻ tấn công cài được ID ở bước 1, sau bước 3 ID đó không còn là ID đã
   đăng nhập. php.net yêu cầu gọi nó **trước** khi ghi thông tin xác thực vào `$_SESSION`.

Một luồng đăng nhập, đăng xuất đầy đủ:

```php
<?php
declare(strict_types=1);

// Cấu hình cookie session an toàn, phải đặt TRƯỚC session_start()
session_start([
    'use_strict_mode' => true,     // không nhận session ID lạ do client tự bịa
    'cookie_httponly' => true,     // JavaScript không đọc được session ID
    'cookie_secure'   => false,    // đổi thành true khi chạy HTTPS (bắt buộc trên production)
    'cookie_samesite' => 'Lax',
]);

$action = $_GET['action'] ?? 'me';

if ($action === 'login') {
    // Giả sử email và mật khẩu đã kiểm tra đúng (chương 16, 17)
    $oldId = session_id();
    session_regenerate_id(true);           // đổi ID mới, xoá file session cũ
    $_SESSION['user_id'] = 42;
    $_SESSION['logged_in_at'] = time();
    echo "Đăng nhập xong. ID cũ: $oldId, ID mới: ", session_id(), "\n";
} elseif ($action === 'logout') {
    $_SESSION = [];                        // 1. xoá dữ liệu trong bộ nhớ
    $p = session_get_cookie_params();
    setcookie(session_name(), '', [        // 2. bảo trình duyệt xoá cookie, cùng path, domain
        'expires' => time() - 3600,
        'path' => $p['path'], 'domain' => $p['domain'],
        'secure' => $p['secure'], 'httponly' => $p['httponly'], 'samesite' => $p['samesite'],
    ]);
    session_destroy();                     // 3. xoá dữ liệu session trên server
    echo "Đã đăng xuất\n";
} else {
    echo isset($_SESSION['user_id']) ? "Xin chào user #{$_SESSION['user_id']}\n" : "Chưa đăng nhập\n";
}
```

Chạy lần lượt `?action=me`, `?action=login`, `?action=me`, `?action=logout`, `?action=me` bằng `curl`
có lưu cookie (`-c jar.txt -b jar.txt`):

| Request | Output | Header đáng chú ý |
|---|---|---|
| `?action=me` | `Chưa đăng nhập` | `Set-Cookie: PHPSESSID=5664...; path=/; HttpOnly; SameSite=Lax` |
| `?action=login` | `Đăng nhập xong. ID cũ: 5664..., ID mới: 8346...` | `Set-Cookie: PHPSESSID=8346...` (ID mới); file `sess_5664...` đã bị xoá |
| `?action=me` | `Xin chào user #42` | |
| `?action=logout` | `Đã đăng xuất` | `Set-Cookie: PHPSESSID=deleted; expires=Thu, 01 Jan 1970 00:00:01 GMT; Max-Age=0; ...` |
| `?action=me` | `Chưa đăng nhập` | Một session ID mới |

Ba bước của logout đều cần: `$_SESSION = []` xoá dữ liệu đang có trong bộ nhớ, `setcookie()` bảo
trình duyệt bỏ chìa khoá, `session_destroy()` xoá ngăn kéo trên server (php.net ghi rõ
`session_destroy()` không tự xoá cookie, cũng không xoá biến `$_SESSION`).

⚠️ Về tham số `true` của `session_regenerate_id(true)`: nó xoá ngay session cũ. Cách này đơn giản và
phổ biến (Laravel cũng huỷ session cũ khi đăng nhập), nhưng php.net cảnh báo: nếu cùng lúc có request
khác đang dùng ID cũ (nhiều tab, AJAX, mạng di động chập chờn làm mất cookie mới), request đó có thể
thấy session biến mất. php.net đề xuất cách cẩn thận hơn: không xoá ngay, ghi một mốc thời gian
"đã huỷ" vào session cũ và từ chối nó sau vài phút; trang `session_regenerate_id()` trên php.net có ví dụ
đầy đủ. Ngoài lúc đăng nhập, php.net khuyên đổi ID định kỳ (ví dụ 15 phút một lần) với nội dung nhạy
cảm.

### 6.7 Session hijacking

*Session hijacking* (chiếm phiên) là khi kẻ tấn công lấy được session ID đang hợp lệ. Các đường lộ và
cách chặn:

| Đường lộ | Cách chặn |
|---|---|
| Nghe lén mạng khi site chạy HTTP | HTTPS cho toàn site, `session.cookie_secure = 1`, thêm HSTS |
| Script độc (XSS) đọc `document.cookie` | `session.cookie_httponly = 1`, và sửa lỗ hổng XSS ([chương 17](17-bao-mat.md)) |
| ID nằm trong URL, lộ qua lịch sử, log, header `Referer` | `session.use_only_cookies = 1`, `session.use_trans_sid = 0` (mặc định) |
| Đọc file session trên server dùng chung | `session.save_path` riêng, quyền chặt (mục 6.3) |
| ID bị đánh cắp vẫn dùng được rất lâu | Đổi ID định kỳ, hết hạn theo timestamp tự quản lý (mục 6.4, 6.6) |

### 6.8 Nhiều server: session phải nằm ở chỗ dùng chung

Handler `files` lưu session trên đĩa của **một** máy. Khi có hai web server sau load balancer:

```
                ┌──► Server A: /var/lib/php/sessions/sess_abc  (user_id = 42)
 Load balancer ─┤
                └──► Server B: không có sess_abc → "Chưa đăng nhập"
```

Người dùng đăng nhập ở A, request sau rơi vào B và thấy mình bị đăng xuất. "Sticky session" (load
balancer ghim mỗi người vào một server) chỉ che bệnh: server chết là mất session. Cách đúng là lưu
session ở nơi mọi server cùng thấy: Redis, Memcached hoặc database.

PHP cho phép thay chỗ lưu mà không đổi code dùng `$_SESSION`: đổi `session.save_handler` sang handler
do extension cung cấp (extension `redis`, `memcached` đăng ký handler riêng), hoặc tự viết một class
implement `SessionHandlerInterface` (các method `open`, `read`, `write`, `close`, `destroy`, `gc`) rồi
đăng ký bằng `session_set_save_handler()`. ⚠️ php.net lưu ý: handler tự viết mà không implement
`validateId()` của `SessionUpdateTimestampHandlerInterface` thì `use_strict_mode` mất tác dụng, bất kể
bạn bật nó hay không.

Laravel có hệ thống session riêng với các driver `file`, `database`, `redis`... và chạy được trên nhiều
server khi chọn driver dùng chung ([chương 29](29-laravel-queue-event-schedule-cache.md)).

## 7. Upload file

### 7.1 Trình duyệt gửi file như thế nào

Form muốn gửi file phải có `method="post"` và `enctype="multipart/form-data"`:

```html
<form method="post" enctype="multipart/form-data">
    <input name="title" value="Ảnh đại diện">
    <input type="file" name="avatar">
    <button>Tải lên</button>
</form>
```

Thiếu `enctype`, trình duyệt gửi form dạng urlencoded và chỉ gửi **tên** file, không gửi nội dung. Với
`multipart/form-data`, body được chia thành nhiều *part* (phần), ngăn cách bằng một chuỗi *boundary*
mà trình duyệt tự chọn và khai báo trong `Content-Type`. Request trông như sau (output minh hoạ, nội dung
file bị rút gọn):

```http
POST /upload.php HTTP/1.1
Host: localhost:8000
Content-Type: multipart/form-data; boundary=----XyZbOuNdArY
Content-Length: 412

------XyZbOuNdArY
Content-Disposition: form-data; name="title"

Ảnh đại diện
------XyZbOuNdArY
Content-Disposition: form-data; name="avatar"; filename="meo.png"
Content-Type: image/png

<các byte nhị phân của file meo.png>
------XyZbOuNdArY--
```

Mỗi part có header riêng: `name` là tên ô trong form, `filename` là tên file **trên máy người dùng**,
`Content-Type` là loại file **do trình duyệt đoán** (thường theo phần mở rộng). Hai thông tin sau hoàn
toàn do client quyết định; `curl -F 'avatar=@shell.php;filename=meo.png;type=image/png'` gửi file PHP
với tên và loại tuỳ ý.

### 7.2 PHP nhận file: `$_FILES`

Khi gặp body `multipart/form-data`, PHP tự đọc nó trước khi script chạy: các ô thường vào `$_POST`, mỗi
file được **ghi thẳng xuống một file tạm trên đĩa** (không nằm trong RAM của script), thông tin về file
vào `$_FILES`. Với request ở mục 7.1:

```php
<?php
declare(strict_types=1);

var_dump($_POST);
print_r($_FILES);
var_dump(is_uploaded_file($_FILES['avatar']['tmp_name']));
var_dump(file_get_contents('php://input'));
```

```
array(1) {
  ["title"]=>
  string(19) "Ảnh đại diện"
}
Array
(
    [avatar] => Array
        (
            [name] => meo.png
            [full_path] => meo.png
            [type] => image/png
            [tmp_name] => /tmp/php4656tbomrgsd0EcFbdj
            [error] => 0
            [size] => 14
        )

)
bool(true)
string(0) ""
```

(Tên file tạm và kích thước tuỳ lần chạy.) Ý nghĩa từng trường:

| Trường | Ý nghĩa | Tin được không |
|---|---|---|
| `name` | Tên file trên máy người dùng | **Không**: client viết gì cũng được, kể cả `../../index.php` |
| `full_path` | Đường dẫn tương đối client gửi khi upload cả thư mục (PHP 8.1+) | **Không** |
| `type` | MIME type do trình duyệt khai | **Không**: php.net ghi rõ PHP không kiểm tra giá trị này |
| `tmp_name` | Đường dẫn file tạm PHP vừa ghi, trong `upload_tmp_dir` hoặc thư mục tạm hệ thống | Có (do PHP đặt) |
| `error` | Mã lỗi `UPLOAD_ERR_*` | Có |
| `size` | Kích thước file nhận được, byte | Có |

Ba điều cần nhớ:

- **File tạm bị xoá khi request kết thúc** nếu bạn chưa chuyển nó đi chỗ khác. Không có bước "để đó
  xử lý sau".
- `php://input` rỗng với request multipart (dòng cuối của output), vì PHP đã tiêu thụ body.
- Muốn biết "người dùng có chọn file không" thì xem `error`: ô file để trống vẫn tạo một phần tử với
  `name` rỗng và `error` là `UPLOAD_ERR_NO_FILE` (4).

### 7.3 Mã lỗi upload

| Hằng | Giá trị | Nghĩa |
|---|---|---|
| `UPLOAD_ERR_OK` | 0 | Thành công |
| `UPLOAD_ERR_INI_SIZE` | 1 | File vượt `upload_max_filesize` |
| `UPLOAD_ERR_FORM_SIZE` | 2 | File vượt trường ẩn `MAX_FILE_SIZE` trong form |
| `UPLOAD_ERR_PARTIAL` | 3 | Chỉ nhận được một phần file (mất kết nối giữa chừng) |
| `UPLOAD_ERR_NO_FILE` | 4 | Không có file nào được chọn |
| `UPLOAD_ERR_NO_TMP_DIR` | 6 | Thiếu thư mục tạm |
| `UPLOAD_ERR_CANT_WRITE` | 7 | Không ghi được file xuống đĩa |
| `UPLOAD_ERR_EXTENSION` | 8 | Một extension của PHP chặn upload |

Không có giá trị 5. Khi file vượt `upload_max_filesize`, phần tử vẫn có trong `$_FILES` nhưng
`error` là `1`, `tmp_name` rỗng, `size` là `0`. Trường ẩn `MAX_FILE_SIZE` chỉ là tiện ích cho người
dùng; php.net nhắc rằng phía trình duyệt rất dễ qua mặt nó, chỉ giới hạn trong php.ini mới không lừa
được.

### 7.4 Các giới hạn kích thước: từ Nginx tới PHP

Một file lớn phải lọt qua nhiều tầng giới hạn, và mỗi tầng báo lỗi theo cách khác nhau:

| Tầng | Thiết lập | Mặc định | Vượt quá thì |
|---|---|---|---|
| Nginx | `client_max_body_size` | `1m` | Nginx trả `413` ngay, PHP không hề chạy |
| PHP | `post_max_size` | `8M` | Warning `POST Content-Length of ... bytes exceeds the limit of ... bytes`; `$_POST` **và** `$_FILES` đều rỗng; script vẫn chạy với status `200` |
| PHP | `upload_max_filesize` | `2M` | File đó có `error = 1`; các ô khác trong form vẫn có trong `$_POST` |
| PHP | `max_file_uploads` | `20` | Chỉ nhận tối đa 20 file mỗi request (ô file để trống không tính), file sau bị bỏ |
| PHP | `max_input_time` | `-1` (dùng `max_execution_time`); `php.ini-production` đặt `60` | Thời gian tối đa để nhận input; mạng chậm, file lớn có thể vượt |
| Ứng dụng | Luật của bạn, ví dụ 2 MB cho ảnh đại diện | | Bạn tự kiểm `size` và trả lỗi |

⚠️ Luật bắt buộc: `post_max_size` phải **lớn hơn** `upload_max_filesize` (php.net), vì body chứa cả
file lẫn các ô khác và phần phân cách. Tăng `upload_max_filesize` lên 50M mà quên `post_max_size`
(vẫn 8M) thì upload 20 MB không báo lỗi `1` mà rơi vào trường hợp tệ hơn: mọi thứ rỗng.

⚠️ Trường hợp `post_max_size` khó phát hiện nhất, vì code thường viết `$_FILES['avatar']['error']` và
nhận một warning "Undefined array key" khó hiểu. Kiểm tra riêng nó:

```php
// Body vượt post_max_size: PHP bỏ cả $_POST lẫn $_FILES, chỉ để lại warning
if ($_POST === [] && $_FILES === [] && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
    http_response_code(413);
    exit("Dữ liệu gửi lên quá lớn\n");
}
```

`post_max_size`, `upload_max_filesize` là thiết lập `INI_PERDIR`: đặt trong php.ini, file cấu hình pool
của PHP-FPM hoặc `.user.ini`, **không** đổi được bằng `ini_set()` trong script, vì lúc script chạy thì
body đã được đọc xong.

### 7.5 Nhiều file: cấu trúc `$_FILES` bị "lật"

Với `<input type="file" name="photos[]" multiple>` chọn hai file, bạn có thể đoán `$_FILES['photos']` là
danh sách hai file. Không phải: PHP gom theo **trường** trước, chỉ số file sau.

```
Array
(
    [photos] => Array
        (
            [name] => Array ( [0] => a.jpg   [1] => b.jpg )
            [full_path] => Array ( [0] => a.jpg   [1] => b.jpg )
            [type] => Array ( [0] => image/jpeg   [1] => image/jpeg )
            [tmp_name] => Array ( [0] => /tmp/phpgqcr8calksjpaLCcOhh   [1] => /tmp/phpqjlh8k7ffb1d3McCNih )
            [error] => Array ( [0] => 0   [1] => 0 )
            [size] => Array ( [0] => 3   [1] => 5 )
        )
)
```

(Output của `print_r` đã được viết gọn trên một dòng cho mỗi trường.) Thường ta viết một hàm nhỏ lật
lại thành danh sách các file, mỗi phần tử có đủ `name`, `type`, `tmp_name`, `error`, `size`; đó là bài
tập 3 cuối chương. Laravel làm việc này cho bạn: `$request->file('photos')` trả mảng các object
`UploadedFile`.

### 7.6 `move_uploaded_file()` và tại sao không dùng `rename()`

`move_uploaded_file($from, $to)` chuyển file tạm tới chỗ lưu lâu dài. Khác `rename()` ở chỗ nó **kiểm
tra `$from` đúng là file vừa được upload qua HTTP POST trong request này** (giống `is_uploaded_file()`);
không phải thì không làm gì và trả `false`. Lớp kiểm tra này chặn kiểu tấn công lừa code xử lý một file
có sẵn trên server (ví dụ một file cấu hình) như thể đó là file upload. ⚠️ Nếu `$to` đã tồn tại, nó bị
**ghi đè** không báo; thêm một lý do để tự sinh tên file.

### 7.7 Danh sách kiểm tra khi nhận file

Upload là một trong những tính năng nguy hiểm nhất của ứng dụng web, vì nó cho người lạ đặt file lên
máy chủ của bạn. Kịch bản kinh điển: kẻ tấn công upload `shell.php`, file được lưu trong thư mục
public, rồi hắn mở `https://shop.vn/uploads/shell.php` và Nginx đưa nó cho PHP-FPM chạy. Từ đó hắn
chạy được mọi lệnh trên server.

Một handler upload ảnh đại diện làm đủ các bước:

```php
<?php
declare(strict_types=1);

const MAX_BYTES = 2 * 1024 * 1024;                      // 2 MB, giới hạn của riêng ứng dụng
const ALLOWED = [                                       // MIME thật → phần mở rộng sẽ dùng
    'image/jpeg' => 'jpg',
    'image/png'  => 'png',
    'image/webp' => 'webp',
];
const UPLOAD_DIR = __DIR__ . '/../storage/avatars';    // NGOÀI thư mục public của web

function uploadErrorMessage(int $code): string
{
    return match ($code) {
        UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE => 'File quá lớn',
        UPLOAD_ERR_PARTIAL    => 'File mới được gửi lên một phần, hãy thử lại',
        UPLOAD_ERR_NO_FILE    => 'Bạn chưa chọn file',
        UPLOAD_ERR_NO_TMP_DIR, UPLOAD_ERR_CANT_WRITE, UPLOAD_ERR_EXTENSION => 'Lỗi máy chủ khi nhận file',
        default               => 'Lỗi upload không xác định',
    };
}

/** Kiểm tra và lưu một file upload. Trả về tên file đã lưu; lỗi thì ném RuntimeException. */
function storeUpload(mixed $file): string
{
    // 1. Đúng cấu trúc của MỘT file (client gửi name="avatar[]" thì các trường là mảng)
    if (!is_array($file) || !is_int($file['error'] ?? null) || !is_string($file['tmp_name'] ?? null)) {
        throw new RuntimeException('Dữ liệu upload không hợp lệ');
    }
    // 2. PHP có nhận file thành công không
    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new RuntimeException(uploadErrorMessage($file['error']));
    }
    // 3. Kích thước theo luật của ứng dụng
    if ($file['size'] > MAX_BYTES) {
        throw new RuntimeException('File quá lớn');
    }
    // 4. Loại file theo NỘI DUNG, không theo tên hay Content-Type client gửi
    $mime = (new finfo(FILEINFO_MIME_TYPE))->file($file['tmp_name']);
    $ext = ALLOWED[$mime] ?? null;
    if ($ext === null) {
        throw new RuntimeException("Không nhận loại file $mime");
    }
    // 5. Tên mới do server sinh: không dùng $file['name']
    $name = bin2hex(random_bytes(16)) . '.' . $ext;
    if (!is_dir(UPLOAD_DIR) && !mkdir(UPLOAD_DIR, 0750, true) && !is_dir(UPLOAD_DIR)) {
        throw new RuntimeException('Không tạo được thư mục lưu');
    }
    // 6. move_uploaded_file chỉ chịu chuyển file mà PHP vừa nhận qua upload của request này
    if (!move_uploaded_file($file['tmp_name'], UPLOAD_DIR . '/' . $name)) {
        throw new RuntimeException('Không lưu được file');
    }
    return $name;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo <<<HTML
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="avatar" accept="image/jpeg,image/png,image/webp">
        <button>Tải lên</button>
    </form>
    HTML;
    exit;
}

// Body vượt post_max_size: PHP bỏ cả $_POST lẫn $_FILES, chỉ để lại warning
if ($_POST === [] && $_FILES === [] && (int) ($_SERVER['CONTENT_LENGTH'] ?? 0) > 0) {
    http_response_code(413);
    exit("Dữ liệu gửi lên quá lớn\n");
}

try {
    $saved = storeUpload($_FILES['avatar'] ?? null);
    echo "Đã lưu: $saved\n";
} catch (RuntimeException $e) {
    http_response_code(422);
    echo 'Lỗi: ', $e->getMessage(), "\n";
}
```

Kết quả với từng kiểu request (tên file lưu là ngẫu nhiên):

| Gửi lên | Status | Output |
|---|---|---|
| Ảnh PNG thật, tên `meo.png` | 200 | `Đã lưu: 45c73bf95bb182e71e8c10c9c2e139c0.png` |
| File chứa `<?php system($_GET["c"]); ?>`, tên `meo.jpg`, `type` khai `image/jpeg` | 422 | `Lỗi: Không nhận loại file text/x-php` |
| Ảnh thật nhưng gửi với `name="avatar[]"` | 422 | `Lỗi: Dữ liệu upload không hợp lệ` |
| Không chọn file | 422 | `Lỗi: Bạn chưa chọn file` |
| Ảnh lớn hơn `upload_max_filesize` | 422 | `Lỗi: File quá lớn` |
| Body lớn hơn `post_max_size` | 413 | `Dữ liệu gửi lên quá lớn` |

`finfo` (extension `fileinfo`, theo php.net được bật mặc định khi build PHP) đoán loại file bằng cách đọc các
byte đầu, giống lệnh `file` của Linux. Nó không tin tên file hay header của client. Danh sách kiểm tra
đầy đủ, theo thứ tự quan trọng:

1. **Web server không bao giờ chạy code trong thư mục upload.** Cách chắc nhất: lưu **ngoài** document
   root (như `UPLOAD_DIR` ở trên) hoặc lên object storage (S3...). Nếu buộc phải để trong public thì cấu
   hình Nginx chỉ chuyển cho PHP-FPM đúng file `index.php`, không phải mọi file `.php`
   ([chương 18](18-fpm-nginx-opcache.md)).
2. **Tự sinh tên file**, phần mở rộng lấy từ MIME đã kiểm tra. Tên của client có thể chứa `../` (path
   traversal, [chương 14](14-file-json-thoi-gian.md) mục 2.6), ký tự lạ, hoặc trùng tên để ghi đè
   file người khác.
3. **Kiểm tra loại file theo nội dung** bằng `finfo` và so với một **allowlist** (danh sách cho phép),
   không dùng denylist kiểu "cấm `.php`" (còn `.phtml`, `.phar`, `.php5`...).
4. **Kiểm tra `error` và `size`**, và giới hạn số lượng, dung lượng theo người dùng nếu cần.
5. ⚠️ `finfo` chưa đủ để coi file là vô hại. Một file có thể vừa là JPEG hợp lệ vừa chứa đoạn mã PHP
   trong phần metadata (*polyglot*); `finfo` vẫn nói `image/jpeg`. Đó là lý do bước 1 quan trọng nhất.
   Với ảnh, mã hoá lại ảnh bằng GD hoặc Imagick (tạo ảnh mới từ pixel) loại bỏ được phần thừa đó.
6. ⚠️ SVG là XML và chứa được JavaScript. Phục vụ SVG do người dùng upload trên chính domain của bạn là
   XSS. Hoặc không nhận SVG, hoặc phục vụ từ domain riêng, kèm `Content-Disposition: attachment`.
7. Khi phục vụ lại file, đặt `Content-Type` đúng loại đã kiểm tra và header
   `X-Content-Type-Options: nosniff` để trình duyệt không tự "đoán" ra HTML.

Các lỗ hổng xoay quanh file và đường dẫn được phân tích sâu hơn ở [chương 17](17-bao-mat.md).

PHP còn có tính năng *session upload progress* (báo tiến độ upload qua session) và từ PHP 8.4,
`request_parse_body()` (mục 2.6) để nhận file qua `PUT`, `PATCH`.

## 8. Tự viết một mini router

### 8.1 Front controller: mọi request đi qua một file

Đến giờ mỗi trang là một file: `/login.php`, `/products.php?id=5`. Cách này đơn giản nhưng URL xấu, và
phần chung (mở session, kiểm tra đăng nhập, xử lý lỗi) phải chép vào mọi file. Gần như mọi framework
PHP hiện đại, kể cả Laravel, dùng mẫu *front controller*: **mọi request đều được web server chuyển cho
một file duy nhất** (`public/index.php`), file đó đọc method và đường dẫn rồi quyết định gọi đoạn code
nào. Phần "quyết định" đó gọi là *router* (bộ định tuyến).

```
GET  /products/5    ─┐
POST /products      ─┼──► index.php ──► Router: so method + path với danh sách route
GET  /cart          ─┘                    ├─ khớp      → gọi handler, nhận kết quả, gửi response
                                          ├─ sai method → 405 + header Allow
                                          └─ không khớp → 404
```

Cách đưa mọi request vào `index.php`:

- Built-in server: truyền tên file làm *router script*: `php -S localhost:8000 index.php`. Mọi request
  đều chạy file đó ([chương 01](01-php-la-gi.md)).
- Nginx: `try_files $uri $uri/ /index.php?$query_string;`, nghĩa là có file tĩnh thật thì trả file đó,
  không thì chuyển cho `index.php`. Đây đúng là cấu hình Laravel dùng ([chương 18](18-fpm-nginx-opcache.md)).

### 8.2 Code

Router dưới đây khoảng 60 dòng nhưng có đủ các ý chính của router thật: route theo method và đường
dẫn, tham số trong đường dẫn (`{id}`), `404`, `405` kèm header `Allow`, `HEAD` dùng chung route `GET`,
và một chỗ duy nhất biến kết quả hoặc lỗi thành response.

```php
<?php
declare(strict_types=1);

// Chạy: php -S localhost:8000 index.php   (mọi request đều đi qua file này)

final class HttpException extends RuntimeException
{
    /** @param array<string, string> $headers */
    public function __construct(
        public readonly int $status,
        string $message,
        public readonly array $headers = [],
    ) {
        parent::__construct($message);
    }
}

final class Router
{
    /** @var list<array{method: string, regex: string, handler: Closure}> */
    private array $routes = [];

    public function get(string $pattern, Closure $handler): void
    {
        $this->add('GET', $pattern, $handler);
    }

    public function post(string $pattern, Closure $handler): void
    {
        $this->add('POST', $pattern, $handler);
    }

    /** Đổi "/products/{id}" thành regex "#^/products/(?P<id>[^/]+)$#". */
    public function add(string $method, string $pattern, Closure $handler): void
    {
        $parts = preg_split('#(\{[a-z_][a-z0-9_]*\})#i', $pattern, -1, PREG_SPLIT_DELIM_CAPTURE);
        $regex = '';
        foreach ($parts as $part) {
            $regex .= preg_match('#^\{([a-z_][a-z0-9_]*)\}$#i', $part, $m) === 1
                ? '(?P<' . $m[1] . '>[^/]+)'      // tham số: một đoạn không chứa "/"
                : preg_quote($part, '#');         // phần chữ cố định: escape ký tự đặc biệt
        }
        $this->routes[] = ['method' => $method, 'regex' => '#^' . $regex . '$#', 'handler' => $handler];
    }

    public function dispatch(string $method, string $path): mixed
    {
        $allowed = [];
        foreach ($this->routes as $route) {
            if (preg_match($route['regex'], $path, $m) !== 1) {
                continue;                                   // đường dẫn không khớp
            }
            $sameMethod = $route['method'] === $method
                || ($method === 'HEAD' && $route['method'] === 'GET');
            if (!$sameMethod) {
                $allowed[] = $route['method'];              // khớp đường dẫn, sai method
                continue;
            }
            // Chỉ giữ các nhóm có tên (bỏ $m[0], $m[1]...), và giải mã %xx
            $params = array_map('rawurldecode', array_filter($m, 'is_string', ARRAY_FILTER_USE_KEY));
            return ($route['handler'])($params);
        }
        if ($allowed !== []) {
            throw new HttpException(405, 'Method Not Allowed', ['Allow' => implode(', ', array_unique($allowed))]);
        }
        throw new HttpException(404, 'Not Found');
    }
}

// ---- Khai báo route ----
$router = new Router();

$router->get('/', fn(array $p): string => "Trang chủ\n");

$router->get('/products/{id}', function (array $p): array {
    $id = filter_var($p['id'], FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
    if ($id === false) {
        throw new HttpException(404, 'Not Found');
    }
    return ['id' => $id, 'name' => "Sản phẩm #$id"];
});

$router->post('/products', function (array $p): array {
    $name = $_POST['name'] ?? null;
    if (!is_string($name) || trim($name) === '') {
        throw new HttpException(422, 'Thiếu tên sản phẩm');
    }
    $id = 101;                                   // giả sử vừa INSERT vào database (chương 16)
    http_response_code(201);
    header("Location: /products/$id");
    return ['id' => $id, 'name' => trim($name)];
});

// ---- Front controller: mọi request đều chạy đoạn này ----
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
if (!is_string($path)) {
    $path = '/';
}

try {
    $result = $router->dispatch($_SERVER['REQUEST_METHOD'], $path);
} catch (HttpException $e) {
    http_response_code($e->status);
    foreach ($e->headers as $name => $value) {
        header("$name: $value");
    }
    $result = ['error' => $e->getMessage()];
}

if (is_array($result)) {
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($result, JSON_UNESCAPED_UNICODE | JSON_THROW_ON_ERROR), "\n";
} else {
    echo $result;
}
```

Thử bằng `curl -i` (terminal 2):

| Request | Status | Body |
|---|---|---|
| `GET /` | 200 | `Trang chủ` |
| `GET /products/5?ref=home` | 200 | `{"id":5,"name":"Sản phẩm #5"}` |
| `GET /products/abc` | 404 | `{"error":"Not Found"}` |
| `POST /products/5` | 405, header `Allow: GET` | `{"error":"Method Not Allowed"}` |
| `POST /products` với `name=Bút bi` | 201, header `Location: /products/101` | `{"id":101,"name":"Bút bi"}` |
| `POST /products` với `name=` | 422 | `{"error":"Thiếu tên sản phẩm"}` |
| `GET /nope` | 404 | `{"error":"Not Found"}` |
| `HEAD /products/5` | 200 | (không có body) |

### 8.3 Các quyết định thiết kế đáng chú ý

- **Đường dẫn lấy từ `REQUEST_URI` qua `parse_url(..., PHP_URL_PATH)`** để bỏ query string;
  `?ref=home` không làm route trượt. `parse_url()` có thể trả `false` hoặc `null` với URI dị dạng, nên
  có nhánh dự phòng.
- **Phần chữ cố định được `preg_quote()`**: route `/files/report.pdf` sẽ không vô tình khớp
  `/files/reportXpdf` (dấu `.` trong regex khớp mọi ký tự).
- **Tham số được giải mã `rawurldecode()`**: `REQUEST_URI` giữ nguyên dạng mã hoá, nên `/products/%35`
  vẫn là sản phẩm 5. Tham số vẫn là chuỗi; handler tự validate (`FILTER_VALIDATE_INT`) như mọi input
  khác ở mục 2.3.
- **405 khác 404**: đường dẫn có tồn tại nhưng sai method thì trả `405` kèm header `Allow`; RFC 9110 bắt
  buộc response `405` phải có header này.
- **Một chỗ duy nhất tạo response**: handler chỉ trả dữ liệu hoặc ném `HttpException`; khối cuối file
  lo status, header, mã hoá JSON. Nhờ vậy không handler nào lỡ `echo` trước khi đặt header (mục 3.4).
- Thứ tự duyệt route là thứ tự khai báo, route khớp đầu tiên thắng. Router thật thường biên dịch các
  route thành một cây hoặc một regex lớn để không phải duyệt tuần tự.

Thứ mini router này còn thiếu so với router của Laravel: middleware (đoạn code chạy trước và sau
handler, ví dụ kiểm tra đăng nhập), route có tên để sinh URL, ràng buộc tham số, nhóm route, inject
dependency vào handler, cache route... Những thứ đó là nội dung của
[chương 24](24-laravel-routing-controller-middleware.md) và
[chương 26](26-laravel-container-provider-facade.md). Biết router chạy thế nào ở tầng dưới, bạn sẽ đọc
hiểu chúng nhanh hơn nhiều.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| "Cannot modify header information - headers already sent" | Đã có output (khoảng trắng sau `?>`, BOM, `echo` debug, warning in ra màn hình) trước `header()`, `setcookie()`, `session_start()` (mục 3.4) | Đọc phần `output started at`; bỏ `?>` cuối file; đặt header trước, in sau |
| Redirect chạy được trên server này, hỏng trên server khác | `output_buffering` khác nhau (0 hay 4096) che giấu output sớm (mục 3.5) | Sửa thứ tự code, đừng dựa vào buffer |
| Code sau `header('Location: ...')` vẫn chạy | `header()` không dừng script (mục 4.3) | Luôn `exit` ngay sau redirect |
| `$_POST` rỗng khi client gửi JSON | PHP chỉ phân tích form urlencoded, multipart cho `POST` (mục 2.4, 2.5) | Đọc `php://input` rồi `json_decode` |
| `$_POST` rỗng với `PUT`, `PATCH` | PHP chỉ tự phân tích body của `POST` (mục 2.6) | `request_parse_body()` (PHP 8.4+) hoặc tự đọc `php://input` |
| `TypeError` khi client gửi `?id[]=1` | Input có thể là mảng, không chỉ chuỗi (mục 2.3) | Kiểm tra `is_string()`, dùng `filter_var` |
| Dùng `$_REQUEST`, kết quả khác nhau theo server | Thứ tự và nguồn phụ thuộc `request_order`, `variables_order` (mục 2.8) | Đọc rõ `$_GET` hoặc `$_POST` |
| Tin `HTTP_HOST`, `X-Forwarded-For`, `$_FILES[...]['type']`, cookie | Đều do client tự viết (mục 2.7, 5.5, 7.2) | Lấy domain từ cấu hình; chỉ tin proxy đã biết; kiểm tra nội dung file bằng `finfo` |
| Cookie vừa đặt mà `$_COOKIE` không có | `$_COOKIE` đến từ request hiện tại, cookie mới chỉ có từ request sau (mục 5.2) | Dùng biến trong request hiện tại |
| Xoá cookie không được | Khác `path` hoặc `domain` so với lúc đặt (mục 5.3) | Xoá với đúng tham số đã dùng khi đặt |
| Cookie `SameSite=None` không được gửi | Thiếu `Secure` (mục 5.4) | Luôn đi kèm `secure => true` |
| Trang chờ nhau khi mở nhiều tab hoặc nhiều AJAX | Khoá session của handler `files` (mục 6.5) | `session_write_close()` sớm, `read_and_close` |
| Toàn bộ session không được lưu, không báo lỗi | Key của `$_SESSION` chứa `\|` (mục 6.3); PHP 8.5 mới có warning | Không dùng `\|` trong key |
| Đăng nhập xong vẫn dùng session ID cũ | Không `session_regenerate_id()` sau đăng nhập, mở đường cho session fixation (mục 6.6) | Đổi ID khi thay đổi quyền hạn; bật `use_strict_mode` |
| Người dùng bị đăng xuất ngẫu nhiên khi có nhiều server | Session `files` nằm trên đĩa từng máy (mục 6.8) | Lưu session ở Redis, database |
| Upload lớn: mọi thứ rỗng, chỉ có warning | Vượt `post_max_size` (mục 7.4) | Kiểm tra riêng trường hợp này; `post_max_size` lớn hơn `upload_max_filesize`; chỉnh cả `client_max_body_size` của Nginx |
| Lưu file upload bằng tên client gửi, trong thư mục public | Path traversal, ghi đè file, chạy file PHP bị upload (mục 7.7) | Tên ngẫu nhiên, lưu ngoài webroot, kiểm tra bằng `finfo` |

## Tóm tắt chương

- HTTP là giao thức hỏi đáp, stateless. Request gồm request line, header, dòng trống, body; response
  gồm status line, header, dòng trống, body. Header luôn đi trước body.
- PHP dựng sẵn superglobal cho mỗi request: `$_GET` (query string), `$_POST` (form, chỉ với `POST`),
  `$_COOKIE`, `$_FILES`, `$_SERVER` (header thành `HTTP_*`). Body JSON đọc từ `php://input`; `PUT`,
  `PATCH` dạng form dùng `request_parse_body()` từ PHP 8.4. Mọi giá trị là chuỗi hoặc mảng, và đều là
  input không đáng tin.
- Output của script chính là body. `header()`, `http_response_code()`, `setcookie()`,
  `session_start()` phải chạy trước output đầu tiên; output buffering chỉ hoãn thời điểm gửi chứ không
  sửa lỗi thứ tự.
- Redirect là `3xx` + `Location`; sau form dùng `303` theo mẫu Post/Redirect/Get; luôn `exit` sau
  redirect; chống open redirect bằng cách chỉ nhận đường dẫn nội bộ.
- Cookie do trình duyệt giữ và gửi lại; luôn đặt `secure`, `httponly`, `samesite` rõ ràng; cookie là
  input người dùng sửa được, ký bằng HMAC nếu cần chống sửa.
- Session: cookie chỉ giữ session ID, dữ liệu nằm ở server (mặc định file `sess_<id>`, serialize). Handler
  `files` khoá session suốt request. Bật `use_strict_mode`, gọi `session_regenerate_id()` khi đăng nhập,
  đăng xuất đủ ba bước.
- Upload: `$_FILES` cho biết file tạm, mã lỗi, kích thước; tên và type do client gửi không tin được.
  Giới hạn qua nhiều tầng (Nginx, `post_max_size`, `upload_max_filesize`). Kiểm tra bằng `finfo` theo
  allowlist, tự sinh tên, lưu ngoài webroot, `move_uploaded_file()`.
- Front controller + router: mọi request vào một `index.php`, router so method và đường dẫn để gọi
  handler, trả `404` hoặc `405` kèm `Allow`. Đây là nền móng của routing trong Laravel.

## Câu hỏi tự kiểm tra

1. Viết ra đầy đủ (từng dòng) một HTTP request `POST /login` gửi form `email`, `password`. Dòng trống
   nằm ở đâu và để làm gì? (gợi ý: mục 1.2)
2. Phân biệt *safe* và *idempotent*. Vì sao không được làm link `GET` để xoá dữ liệu? Vì sao trình duyệt
   hỏi trước khi gửi lại một `POST`?
3. Với URL `/?tag=php&tag=go&a.b=1`, `$_GET` chứa gì? Muốn nhận cả hai `tag` thì phải viết URL thế nào?
4. Vì sao client gửi body JSON thì `$_POST` rỗng? Viết các bước để đọc an toàn một body JSON và trả
   status phù hợp cho từng loại lỗi. (gợi ý: mục 2.5)
5. Giải thích vì sao cùng một đoạn code có `echo` trước `header('Location: ...')` chạy được trên server
   này nhưng báo "headers already sent" trên server khác, và vì sao nó có thể hỏng "ngẫu nhiên".
   (gợi ý: mục 3.5)
6. Khi nào nên dùng `301`, `302`, `303`, `307`, `308`? `header('Location: /x')` không kèm status thì PHP
   gửi mã nào, và vì sao đáp án phụ thuộc SAPI?
7. Một cookie có `Domain=shop.vn; Path=/; Secure; HttpOnly; SameSite=Lax`. Nó được gửi trong những
   request nào sau đây: `https://api.shop.vn/x`, `http://shop.vn/`, một form trên `evil.com` tự `POST`
   sang `https://shop.vn/transfer`, người dùng bấm link từ `evil.com` sang `https://shop.vn/`?
8. Mô tả từng bước chuyện gì xảy ra trên đĩa và trong bộ nhớ khi một request gọi `session_start()`,
   sửa `$_SESSION` rồi kết thúc. Vì sao hai request cùng session phải chờ nhau? (gợi ý: mục 6.3, 6.5)
9. Trình bày kịch bản session fixation và hai lớp phòng thủ. Vì sao `session_regenerate_id()` phải gọi
   trước khi ghi `user_id` vào session?
10. Một người dùng upload file 20 MB, server đặt `upload_max_filesize = 50M`, `post_max_size = 8M`.
    Script thấy gì trong `$_POST`, `$_FILES`? Nếu Nginx để `client_max_body_size` mặc định thì sao?
    (gợi ý: mục 7.4)

## Bài tập

1. **Trang "Echo request".** Viết `index.php` chạy bằng `php -S localhost:8000 index.php`, với mọi
   request trả về JSON gồm: method, đường dẫn (không có query string), mảng query đã giải mã, toàn bộ
   header của request (tên dạng gốc như `Content-Type`, dựng lại từ `$_SERVER`, không dùng
   `getallheaders()`), và body: nếu là JSON thì trả object đã decode, nếu là form thì trả mảng form, còn
   lại trả chuỗi thô. Thử bằng ít nhất năm lệnh `curl` khác nhau (GET có query, POST form, POST JSON,
   PUT form, JSON sai cú pháp phải ra `400`).
2. **Đăng nhập bằng session.** Viết ba trang `/login` (form và xử lý `POST`), `/me` (chỉ xem được khi
   đã đăng nhập, chưa thì redirect `302` về `/login?next=/me`) và `/logout` (chỉ nhận `POST`). Dùng một
   mảng user cố định với mật khẩu đã băm bằng `password_hash()`. Yêu cầu: `use_strict_mode`, cookie
   `httponly` và `samesite=Lax`, `session_regenerate_id()` khi đăng nhập, flash message "Sai email hoặc
   mật khẩu", Post/Redirect/Get, `next` được kiểm tra chống open redirect, logout đủ ba bước. Kiểm tra
   bằng `curl -c jar.txt -b jar.txt -i` và ghi lại các header `Set-Cookie` qua từng bước.
3. **Chuẩn hoá `$_FILES`.** Viết hàm `normalizeFiles(array $files): array` biến `$_FILES` thành cấu trúc
   "mỗi file một mảng" cho cả ba trường hợp: một ô `avatar`, một ô `photos[]` chọn nhiều file, và ô lồng
   nhau `docs[contract][]`. Sau đó viết trang upload album ảnh: tối đa 5 ảnh mỗi lần, mỗi ảnh tối đa
   1 MB, chỉ JPEG/PNG/WebP theo `finfo`, lưu ngoài thư mục public với tên ngẫu nhiên, và một route
   `GET /photos/{name}` đọc file đó trả về với `Content-Type` đúng và `X-Content-Type-Options: nosniff`
   (nhớ chặn path traversal ở `{name}`).
4. **Nâng cấp mini router.** Thêm vào router ở mục 8: (a) phương thức `put()`, `delete()` và hỗ trợ trường
   ẩn `_method` trong form `POST` như Laravel; (b) ràng buộc tham số kiểu `{id:\d+}`; (c) middleware:
   `$router->get('/admin', $handler, middleware: [$requireLogin])`, trong đó middleware là `Closure` nhận
   tham số và một `$next`. Viết thêm phần xử lý exception chung: lỗi không phải `HttpException` thì trả
   `500` với body chung chung và ghi chi tiết vào log bằng `error_log()`.

## Đọc thêm

- RFC 9110 [HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) (method, status code, redirect,
  header `Allow`, `Location`), RFC 9112 [HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112) (định dạng
  message), RFC 6265 [HTTP State Management Mechanism](https://www.rfc-editor.org/rfc/rfc6265) (cookie),
  RFC 5789 [PATCH Method for HTTP](https://www.rfc-editor.org/rfc/rfc5789).
- php.net, dữ liệu request:
  [Variables From External Sources](https://www.php.net/manual/en/language.variables.external.php),
  [$_SERVER](https://www.php.net/manual/en/reserved.variables.server.php),
  [$_POST](https://www.php.net/manual/en/reserved.variables.post.php),
  [$_REQUEST](https://www.php.net/manual/en/reserved.variables.request.php),
  [php:// wrappers](https://www.php.net/manual/en/wrappers.php.php),
  [request_parse_body()](https://www.php.net/manual/en/function.request-parse-body.php),
  [filter_input()](https://www.php.net/manual/en/function.filter-input.php),
  [Core php.ini directives](https://www.php.net/manual/en/ini.core.php) (`variables_order`,
  `request_order`, `post_max_size`, `upload_max_filesize`),
  [Runtime configuration](https://www.php.net/manual/en/info.configuration.php) (`max_input_vars`,
  `max_input_time`).
- php.net, response: [header()](https://www.php.net/manual/en/function.header.php),
  [headers_sent()](https://www.php.net/manual/en/function.headers-sent.php),
  [http_response_code()](https://www.php.net/manual/en/function.http-response-code.php),
  [Output Control](https://www.php.net/manual/en/book.outcontrol.php),
  [Output buffering configuration](https://www.php.net/manual/en/outcontrol.configuration.php),
  [flush()](https://www.php.net/manual/en/function.flush.php).
- php.net, cookie và session: [setcookie()](https://www.php.net/manual/en/function.setcookie.php),
  [Sessions](https://www.php.net/manual/en/book.session.php),
  [Session configuration](https://www.php.net/manual/en/session.configuration.php),
  [Session Management Basics](https://www.php.net/manual/en/features.session.security.management.php),
  [Securing Session INI Settings](https://www.php.net/manual/en/session.security.ini.php),
  [session_regenerate_id()](https://www.php.net/manual/en/function.session-regenerate-id.php),
  [session_destroy()](https://www.php.net/manual/en/function.session-destroy.php),
  [session_write_close()](https://www.php.net/manual/en/function.session-write-close.php).
- php.net, upload: [Handling file uploads](https://www.php.net/manual/en/features.file-upload.php),
  [Error Messages Explained](https://www.php.net/manual/en/features.file-upload.errors.php),
  [Common Pitfalls](https://www.php.net/manual/en/features.file-upload.common-pitfalls.php),
  [move_uploaded_file()](https://www.php.net/manual/en/function.move-uploaded-file.php),
  [finfo](https://www.php.net/manual/en/class.finfo.php).
- php-src: [UPGRADING của PHP 8.4](https://github.com/php/php-src/blob/PHP-8.4/UPGRADING) và
  [PHP 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING) (`request_parse_body()`,
  deprecation của session, cookie `partitioned`); mã nguồn
  [main/SAPI.c](https://github.com/php/php-src/blob/PHP-8.5/main/SAPI.c) (status mặc định của
  `Location`) và [main/main.c](https://github.com/php/php-src/blob/PHP-8.5/main/main.c) (status `500`
  khi fatal error); file [php.ini-production](https://github.com/php/php-src/blob/PHP-8.5/php.ini-production).
- Nginx: [client_max_body_size](https://nginx.org/en/docs/http/ngx_http_core_module.html#client_max_body_size).
- [PSR-12: Extended Coding Style](https://www.php-fig.org/psr/psr-12/) (bỏ thẻ đóng `?>`).
- OWASP Cheat Sheets: [Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html),
  [File Upload](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).
- MDN: [Using HTTP cookies](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies),
  [Set-Cookie](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Set-Cookie) (SameSite,
  tiền tố `__Host-`, `Partitioned`).
