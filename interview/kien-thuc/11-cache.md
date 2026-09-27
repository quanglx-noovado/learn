# 11. Cache · Kiến thức

> [← Plan ôn tập](../11-cache.md) · [Mục lục kiến thức](README.md)
> Bài đọc tổng hợp từ tài liệu gốc ở mục "Đọc" của từng module. Đọc sau khi đã xem plan; tick các
> tiêu chí "Nắm chắc khi" ở file plan. Mọi nội dung đã qua một lượt review độc lập đối chiếu nguồn gốc.

## Mục lục

- Chặng 1: Nền
  - [1.1 Các tầng cache](#11-các-tầng-cache)
  - [1.2 Cache-aside và TTL](#12-cache-aside-và-ttl)
  - [1.3 Eviction cơ bản](#13-eviction-cơ-bản)
- Chặng 2: Làm chủ
  - [2.1 Pattern đọc/ghi](#21-pattern-đọcghi)
  - [2.2 Invalidation và race condition](#22-invalidation-và-race-condition)
  - [2.3 Stampede, penetration, avalanche](#23-stampede-penetration-avalanche)
  - [2.4 Hot key, big key và Redis làm cache](#24-hot-key-big-key-và-redis-làm-cache)
  - [2.5 Vận hành cache](#25-vận-hành-cache)
  - [2.6 Cài LRU `O(1)`](#26-cài-lru-o1)
  - [2.7 Cache trong PHP/Laravel](#27-cache-trong-phplaravel)
- Chặng 3: Senior
  - [3.1 Multi-level cache (L1 + L2)](#31-multi-level-cache-l1--l2)
  - [3.2 Nhất quán cache ở quy mô lớn: lease, CDC](#32-nhất-quán-cache-ở-quy-mô-lớn-lease-cdc)
  - [3.3 Khi cache trở thành phụ thuộc bắt buộc](#33-khi-cache-trở-thành-phụ-thuộc-bắt-buộc)

---

## Chặng 1: Nền

### 1.1 Các tầng cache

Module này trả lời: giữa trình duyệt và MySQL có bao nhiêu chỗ đang giữ bản sao dữ liệu, mỗi chỗ xoá
thế nào, và header `Cache-Control` điều khiển các tầng HTTP ra sao (đặc biệt `no-cache` khác
`no-store`).

#### Cache là gì

*Cache* là một bản sao của dữ liệu, đặt ở chỗ đọc nhanh hơn hoặc gần người dùng hơn nơi giữ dữ liệu
gốc (*origin*, *source of truth*). Mỗi lần đọc có hai kết cục:

- *Hit*: tìm thấy trong cache, trả luôn, không phải chạm tới nguồn.
- *Miss*: không có trong cache, phải đọc nguồn (thường chậm hơn nhiều), rồi thường ghi lại vào cache
  cho lần sau.

Tỉ lệ `hit / (hit + miss)` gọi là *hit ratio*, con số đầu tiên để biết cache có đáng tồn tại không.

Cache đem lại hai lợi ích tách biệt, nên nhớ cả hai khi trả lời phỏng vấn:

1. **Giảm độ trễ**: cache càng gần người dùng thì response càng nhanh (browser cache không cần đi
   mạng).
2. **Giảm tải cho origin**: một request được phục vụ từ cache thì server không phải parse, route,
   khôi phục session, query DB hay render template.

Cái giá của mọi cache là bản sao có thể **cũ** (*stale*) so với nguồn. Toàn bộ phần khó của chủ đề
cache (invalidation, race, TTL) xoay quanh câu hỏi "cũ bao lâu thì chấp nhận được, và làm sao giới
hạn nó".

#### Các tầng, từ gần user tới gần dữ liệu

```
 Người dùng
    │
 [Browser cache]          private: chỉ của một người
    │   (Internet)
 [CDN edge]               shared, managed: bạn cấu hình và purge được
    │
 [Reverse proxy]          shared, managed: Nginx proxy_cache, Varnish
    │
 [App server]
    ├─ in-process cache   mảng/biến trong process, APCu, Caffeine
    └─ distributed cache  Redis / Valkey / Memcached, dùng chung qua mạng
    │
 [Database]               InnoDB buffer pool, OS page cache
```

| Tầng | Ví dụ | Đặc điểm | Xoá thế nào |
|---|---|---|---|
| Browser | HTTP cache, Service Worker + Cache API | Nằm trên máy người dùng, *private cache* | Server gần như không xoá được (xem dưới). Đổi URL bằng tên file có hash |
| CDN | CloudFront, Cloudflare | Máy chủ đặt gần người dùng, *shared cache*, key theo URL (+ header trong `Vary`) | Purge qua API/dashboard, hoặc chờ hết hạn |
| Reverse proxy | Nginx `proxy_cache`, Varnish | Đứng trước app server | Purge (Varnish có sẵn; Nginx bản open source không có lệnh purge sẵn, cần module ngoài hoặc bản thương mại), hoặc chờ hết hạn |
| App in-process | Biến tĩnh, APCu, Caffeine (Java) | Nhanh nhất, không đi mạng, nhưng mỗi process/máy một bản | Phải xoá riêng từng instance, thường chỉ dựa vào TTL ngắn |
| Distributed | Redis, Valkey, Memcached | Dùng chung giữa mọi instance app, mỗi lần đọc tốn một round-trip mạng | `DEL` key, hoặc đổi version trong tên key (module 2.2) |
| DB | InnoDB buffer pool, OS page cache | Có sẵn, DB tự quản | Không cần xoá: DB tự giữ nhất quán |

Giải thích hai khái niệm trong bảng:

- *Private cache* là cache gắn với một client (browser). Nó được phép lưu cả response cá nhân hoá.
- *Shared cache* nằm giữa client và server, phục vụ nhiều người dùng. MDN chia tiếp thành *proxy
  cache* (proxy của mạng công ty/ISP, bạn không kiểm soát) và *managed cache* (CDN, reverse proxy,
  Service Worker: bạn tự triển khai, tự cấu hình, tự xoá được).

Đặc thù PHP: PHP-FPM chạy theo mô hình share-nothing, mỗi request bắt đầu với bộ nhớ userland trống,
nên "cache trong biến" chỉ sống trong một request. Cái gần với in-process cache nhất là APCu: vùng
shared memory dùng chung giữa các worker sinh ra từ cùng một master PHP-FPM trên **một máy**,
không chia sẻ sang máy khác (và CLI/queue worker có vùng APCu riêng). Laravel còn có `Cache::memo()`, giữ giá trị đã đọc trong bộ nhớ trong phạm vi một request
hoặc một job để khỏi gọi Redis lặp lại. Chi tiết mô hình FPM:
[05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing).

⚠️ CDN hoặc reverse proxy cache nhầm một response có dữ liệu cá nhân là sự cố lộ dữ liệu: người sau
mở cùng URL thấy trang "tài khoản của tôi" của người trước. MDN lưu ý thêm: có cookie trong request
không tự làm response thành private; phải khai báo `Cache-Control: private` (hoặc `no-store`).

Tầng DB thường bị quên. InnoDB giữ các page hay dùng trong buffer pool (RAM), nên khi toàn bộ dữ liệu
nóng vừa trong buffer pool, query theo index đã rất nhanh. Tăng RAM cho DB đôi khi giải quyết được
vấn đề mà không phải thêm một tầng Redis cùng toàn bộ bài toán invalidation đi kèm. Buffer pool:
[03-database-sql.md#31-bên-trong-innodb-log-bộ-nhớ-mvcc](03-database-sql.md#31-bên-trong-innodb-log-bộ-nhớ-mvcc).

#### Debug "sửa rồi mà không thấy đổi"

Mỗi tầng là thêm một nơi dữ liệu có thể cũ. Khi báo lỗi "đã sửa giá mà khách vẫn thấy giá cũ", đi
lần lượt từ ngoài vào, loại trừ từng tầng:

1. **Browser**: mở DevTools tab Network, xem request có ghi "(from disk cache)" / "(from memory
   cache)" không, hoặc thử cửa sổ ẩn danh. Browser reload thường gửi request có điều kiện;
   *force reload* (Ctrl+Shift+R) gửi `Cache-Control: no-cache` để bỏ qua bản đang lưu.
2. **CDN / proxy**: gọi thẳng bằng `curl -sI https://site/path` và đọc header. Header `Age: N` cho
   biết response đã nằm trong một shared cache N giây. Nhiều CDN còn thêm header riêng báo HIT/MISS
   (tên header tuỳ nhà cung cấp, kiểm tra docs). Gọi thẳng vào origin (bỏ qua CDN) để so sánh.
3. **App cache**: có đang dùng APCu hay `Cache::memo()` không; key Redis tương ứng còn giá trị cũ
   không (`redis-cli GET ...`, `TTL ...`).
4. **Replica DB**: nếu app đọc từ replica, replication lag có thể khiến chính lần nạp lại cache đọc
   phải dữ liệu cũ (race này quay lại ở module 2.2 và 3.2).

```sh
# Xem header cache của một URL (chỉ lấy header)
curl -sI https://example.com/products/42 | grep -iE 'cache-control|age|etag|last-modified|vary'
```

#### HTTP caching

Tầng browser, CDN, proxy nói chung một ngôn ngữ: các header HTTP chuẩn hoá ở RFC 9111.

**Fresh và stale theo tuổi.** Một response đã lưu ở một trong hai trạng thái: *fresh* (còn dùng lại
được ngay) hoặc *stale* (đã quá hạn). Tiêu chí là *age*: thời gian kể từ khi origin **tạo** response
(không phải từ khi cache nhận được). Với `Cache-Control: max-age=604800` (một tuần), response fresh
khi age dưới một tuần. Nếu một shared cache đã giữ nó một ngày, nó gửi kèm `Age: 86400`, và browser
chỉ còn coi nó fresh thêm `604800 - 86400 = 518400` giây.

Các directive hay dùng trong response:

| Directive | Nghĩa |
|---|---|
| `max-age=N` | Fresh trong N giây kể từ khi được tạo |
| `s-maxage=N` | Như `max-age` nhưng chỉ cho shared cache (CDN, proxy); private cache bỏ qua. Với shared cache, nó thắng `max-age` và `Expires` |
| `private` | Chỉ private cache (browser) được lưu. Bắt buộc cho nội dung cá nhân hoá |
| `public` | Cho phép shared cache lưu, **kể cả** khi request có header `Authorization` (bình thường thì bị cấm) |
| `no-cache` | Được lưu, nhưng phải revalidate với origin trước **mỗi** lần dùng lại |
| `no-store` | Không cache nào (private hay shared) được lưu |
| `must-revalidate` | Fresh thì dùng; stale thì bắt buộc revalidate, không được dùng bản stale kể cả khi mất kết nối tới origin (thay vào đó trả 504) |
| `immutable` | Nội dung không đổi trong thời gian fresh, nên khỏi revalidate cả khi người dùng reload |
| `stale-while-revalidate=N` | Hết fresh rồi vẫn được trả bản stale thêm N giây, trong khi revalidate ở nền |
| `stale-if-error=N` | Khi origin lỗi (500, 502, 503, 504), được trả bản stale thêm tối đa N giây |

Hai điểm MDN nhấn mạnh về `public`: không cần ghi `public` chỉ để CDN cache được, vì một response có
`max-age` đã lưu được ở shared cache; `public` chỉ cần khi muốn mở khoá trường hợp có `Authorization`
(và `s-maxage` hoặc `must-revalidate` cũng mở khoá được). Ghi `public` bừa trên trang có xác thực
Basic Auth là tự mời lộ dữ liệu.

**Không có `Cache-Control` không có nghĩa là không cache.** HTTP cho phép *heuristic caching*: nếu
response có `Last-Modified` mà không có hướng dẫn freshness, cache được tự đoán thời gian fresh (spec
gợi ý khoảng 10% thời gian từ lần sửa cuối). Vì vậy mọi response nên khai báo `Cache-Control` rõ
ràng.

**Revalidate** là hỏi lại origin "bản tôi đang có còn đúng không", thay vì tải lại toàn bộ:

1. Lần đầu, server trả `200` kèm *validator*: `ETag: "33a64df5"` (mã phiên bản do server tự chọn,
   ví dụ hash nội dung) và/hoặc `Last-Modified: <thời điểm sửa cuối>`.
2. Khi bản lưu stale (hoặc gặp `no-cache`), client gửi *conditional request*:
   `If-None-Match: "33a64df5"` và/hoặc `If-Modified-Since: <thời điểm>`.
3. Nếu chưa đổi, server trả `304 Not Modified` không có body, rất nhẹ; client coi bản lưu là fresh
   trở lại. Nếu đã đổi, server trả `200` với nội dung mới.

Khi có cả hai, `If-None-Match` được ưu tiên. `ETag` ra đời vì `Last-Modified` có định dạng thời gian
khó parse và khó đồng bộ giữa nhiều server.

**`Vary`** liệt kê các header của request làm response khác nhau. Mặc định cache phân biệt response
theo URL; `Vary: Accept-Language` khiến key thành "URL + giá trị `Accept-Language`", nên bản tiếng
Anh và tiếng Nhật được lưu riêng. ⚠️ `Vary: User-Agent` gần như giết hit ratio vì giá trị này có vô
số biến thể. Với nội dung cá nhân hoá qua cookie, MDN khuyên dùng `private` thay vì `Vary: Cookie`.

⚠️ `no-cache` **không** có nghĩa "không cache". Nó cho lưu nhưng bắt hỏi lại origin mỗi lần dùng
(nếu origin trả `304` thì vẫn tiết kiệm băng thông). `no-store` mới là "không được lưu". Thêm ba
chi tiết hay bị hỏi vặn:

- `no-store` không xoá bản đã lưu từ trước cho cùng URL. Muốn luôn nhận bản mới nhất thì `no-cache`
  mới đúng.
- `no-store` làm mất cả các tối ưu khác của browser, ví dụ back/forward cache. MDN khuyên với trang
  cá nhân hoá nên ưu tiên `no-cache, private`, để dành `no-store` cho dữ liệu thật sự nhạy cảm.
- `max-age=0, must-revalidate` là cách viết cũ tương đương `no-cache` cho các cache thời HTTP/1.0;
  ngày nay cứ viết `no-cache`.

**Không xoá được cache ở phía client.** Một response đã lưu với `max-age` dài thì server không còn
cách nào đẩy nó ra khỏi browser hay proxy trung gian, vì request không còn tới server nữa.
`Clear-Site-Data: cache` chỉ xoá được cache browser của site đó (khi browser nhận được response có
header này), không tác động tới cache trung gian. Hai hệ quả thực tế:

- Asset tĩnh (JS, CSS, ảnh) dùng *cache busting*: nhét hash/version vào URL (`app.3f9a.js`). Nội
  dung đổi thì URL đổi, bản cũ không bao giờ được xin lại nữa. Nhờ vậy được phép cache rất lâu.
- HTML chính không đổi URL được, nên thường để `no-cache` (kèm `ETag` để tận dụng `304`). Muốn cache
  HTML mạnh tay thì phải dùng managed cache (CDN) có purge API và purge khi nội dung đổi.

Ba cấu hình mẫu (theo các pattern trong MDN):

```http
# 1. Asset có hash trong tên file: cache một năm, khỏi revalidate
Cache-Control: public, max-age=31536000, immutable

# 2. Trang sản phẩm công khai: browser giữ ngắn, CDN giữ lâu hơn, cho phép trả bản cũ khi đang làm mới
Cache-Control: max-age=60, s-maxage=300, stale-while-revalidate=600

# 3. Trang "đơn hàng của tôi": chỉ browser của người đó được lưu, và phải hỏi lại mỗi lần
Cache-Control: no-cache, private
```

Các con số ở mẫu 2 là ví dụ; chọn theo mức cũ nghiệp vụ chấp nhận được. RFC 5861 lưu ý tổng
`max-age + stale-while-revalidate` là thời gian tối đa một response có thể được phục vụ từ cache
(ví dụ cả hai là 600 thì phải chịu được dữ liệu cũ tới 20 phút). Nó cũng lưu ý revalidate nền chỉ xảy
ra khi có request rơi vào cửa sổ stale; traffic thưa thì request vẫn phải chờ như thường.

**Request collapse.** Khi nhiều request giống nhau tới shared cache cùng lúc, cache có thể chỉ gửi một
request tới origin rồi dùng kết quả cho tất cả. MDN lưu ý việc này có thể xảy ra ngay cả với
`max-age=0` hoặc `no-cache`, nên response cá nhân hoá phải có `private`. Ý tưởng "gộp các miss giống
nhau thành một" chính là cách chống stampede ở module 2.3.

**Trong Laravel**, middleware `cache.headers` đặt `Cache-Control` cho một nhóm route. Directive viết
theo snake_case, cách nhau bằng dấu chấm phẩy; thêm `etag` thì Laravel tự tính ETag từ hash nội dung
response và tự trả `304` khi request gửi `If-None-Match` khớp:

```php
use Illuminate\Support\Facades\Route;

Route::middleware('cache.headers:public;max_age=60;s_maxage=300;stale_while_revalidate=600;etag')
    ->group(function (): void {
        Route::get('/products/{id}', [ProductController::class, 'show']);
    });
```

⚠️ Middleware này bỏ qua request không phải GET/HEAD và response không thành công, nhưng nó không
biết response có cá nhân hoá hay không. Đừng gắn nhóm `public` cho route đọc `auth()->user()`.

Chi tiết giao thức HTTP: [plan 02-networking](../02-networking.md).

**Tóm tắt nhanh**
- Kể được sáu tầng: browser, CDN, reverse proxy, in-process, distributed (Redis), DB; và cách xoá
  từng tầng. Browser không xoá được từ server, nên asset dùng URL có hash.
- `no-cache` = lưu được nhưng revalidate trước mỗi lần dùng; `no-store` = không được lưu.
- `private` cho mọi nội dung cá nhân hoá; quên nó là CDN có thể trả trang của người này cho người
  khác.
- Revalidate: `ETag`/`Last-Modified` đi ra, `If-None-Match`/`If-Modified-Since` đi vào, `304` nếu
  chưa đổi.
- Debug dữ liệu cũ: đi từ ngoài vào, đọc header `Age`, `Cache-Control` bằng `curl -sI`.

**Nguồn**: [MDN: HTTP caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Caching) ·
[MDN: Cache-Control](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control) ·
[RFC 5861](https://www.rfc-editor.org/rfc/rfc5861) ·
[Laravel: Cache-Control middleware](https://laravel.com/docs/responses#cache-control-middleware)


---

### 1.2 Cache-aside và TTL

Module này trả lời: pattern cache phổ biến nhất (cache-aside, cũng là thứ `Cache::remember` làm)
chạy từng bước thế nào, TTL nên chọn theo tiêu chí gì, vì sao phải thêm jitter, và vì sao giá trị
`null` là một cái bẫy.

#### Cache-aside

*Cache-aside* (AWS gọi là *lazy caching* hay *lazy loading*): **app** tự điều phối cache, còn cache
chỉ là một kho key-value thụ động, không biết gì về DB. Dữ liệu chỉ được nạp vào cache khi có ai đó
thật sự đọc nó (vì thế gọi là "lazy").

```
 Đọc                                     Ghi
 ───                                     ───
 app ──(1) GET key──► cache              app ──(1) UPDATE──► DB
  │ hit: (2) trả luôn                    app ──(2) DEL key──► cache
  │ miss:
  ├──(3) SELECT──► DB
  ├──(4) SET key value EX ttl──► cache
  └──(5) trả kết quả
```

Luồng đọc:

1. Đọc key trong cache.
2. Hit thì trả luôn.
3. Miss thì đọc DB.
4. Ghi kết quả vào cache kèm TTL.
5. Trả kết quả.

Luồng ghi:

1. Ghi DB (DB là nguồn sự thật).
2. **Xoá** key cache tương ứng. Lần đọc sau sẽ miss và tự nạp bản mới.

Vì sao xoá chứ không ghi đè giá trị mới vào cache: hai request ghi đồng thời có thể ghi cache theo
thứ tự ngược với thứ tự ghi DB, để lại giá trị sai; xoá thì lần đọc sau luôn lấy từ DB. Timeline chi
tiết ở module 2.2.

Viết bằng Redis thuần (extension phpredis) để thấy rõ từng bước mà `remember` che đi:

```php
<?php
declare(strict_types=1);

// Cần extension phpredis và PDO. Bảng: products(id, name, price).
final class ProductRepository
{
    private const NULL_MARKER = '__null__';

    public function __construct(private Redis $redis, private PDO $pdo) {}

    /** @return array<string, mixed>|null */
    public function find(int $id): ?array
    {
        $key = "product:{$id}:v1";

        // (1) Đọc cache. phpredis trả false khi key không tồn tại.
        $cached = $this->redis->get($key);
        if ($cached !== false) {
            // (2) Hit. Marker nghĩa là "đã biết chắc không có bản ghi này".
            return $cached === self::NULL_MARKER
                ? null
                : json_decode($cached, true, flags: JSON_THROW_ON_ERROR);
        }

        // (3) Miss: đọc DB. fetch() trả false khi không có dòng nào.
        $stmt = $this->pdo->prepare('SELECT id, name, price FROM products WHERE id = ?');
        $stmt->execute([$id]);
        $row = $stmt->fetch(PDO::FETCH_ASSOC);

        // (4) Ghi cache kèm TTL. Bản ghi không tồn tại: cache marker với TTL ngắn.
        if ($row === false) {
            $this->redis->setex($key, 30, self::NULL_MARKER);
            return null;
        }
        $this->redis->setex($key, $this->ttlWithJitter(600), json_encode($row, JSON_THROW_ON_ERROR));

        // (5) Trả kết quả.
        return $row;
    }

    public function updatePrice(int $id, string $price): void
    {
        $stmt = $this->pdo->prepare('UPDATE products SET price = ? WHERE id = ?');
        $stmt->execute([$price, $id]);   // (1) ghi DB trước
        $this->redis->del("product:{$id}:v1"); // (2) rồi xoá key
    }

    private function ttlWithJitter(int $base): int
    {
        return $base + random_int(0, intdiv($base, 10));
    }
}
```

Giữa bước (3) và (4) của `find` có một khoảng trống: nếu một request khác update DB và xoá key đúng
lúc đó, `find` sẽ ghi giá trị cũ vào cache **sau** lệnh xoá. Đây là race kinh điển của cache-aside,
phân tích bằng timeline ở module 2.2. Tương tự, nếu `updatePrice` chạy trong một transaction thì lệnh
`del` phải đặt **sau** commit.

Trong Laravel, cả luồng đọc gói trong một lệnh (TTL tính bằng giây):

```php
$user = Cache::remember("user:{$id}:v1", 600, fn () => User::find($id));

// Luồng ghi
$user->update(['name' => $name]);
Cache::forget("user:{$id}:v1");
```

Vài chi tiết API Laravel đáng nhớ (theo docs Laravel 13):

- `Cache::remember($key, $seconds, $callback)`: có thì trả, không có thì chạy callback, lưu kết
  quả, rồi trả.
- `Cache::rememberWithWarmth(...)` trả `[$value, $warm]`, với `$warm` cho biết giá trị lấy từ cache
  hay vừa chạy callback. Tiện để đo hit ratio theo từng loại key.
- `Cache::put($key, $value)` không truyền TTL là lưu vĩnh viễn; truyền `0` hoặc số âm thì key bị
  xoá.
- `Cache::add($key, $value, $seconds)` chỉ ghi khi key chưa tồn tại, là thao tác atomic, trả
  `true` nếu thật sự ghi.

| Ưu | Nhược |
|---|---|
| Đơn giản, hầu như framework nào cũng hỗ trợ | Lần đầu đọc một key luôn miss (thêm một round-trip cache) |
| Cache chỉ chứa thứ thật sự được đọc, nên kích thước tự vừa phải | Có cửa sổ dữ liệu cũ, giới hạn bằng TTL |
| Thêm node cache mới thì cache tự đầy dần theo traffic | Logic cache rải khắp code gọi |
| Redis chết thì app vẫn chạy, chỉ chậm hơn (nếu code bắt lỗi kết nối) | Node cache mới hoặc cache vừa flush: mọi request đều miss cùng lúc |

⚠️ "Redis chết app vẫn chạy" chỉ đúng khi code coi lỗi cache là miss. phpredis ném `RedisException`
khi mất kết nối; không bắt thì lỗi cache thành lỗi 500. Cách xử lý đầy đủ (timeout, failover, circuit
breaker) ở chặng 3.

AWS khuyên dùng cache-aside cho dữ liệu **đọc nhiều, ghi ít**, ví dụ hồ sơ người dùng được đọc hàng
trăm lần một ngày nhưng cả năm chỉ sửa vài lần. Dữ liệu mà lần đọc sau ghi phải thấy ngay giá trị
mới thì cache-aside không đủ (xem các pattern khác ở module 2.1).

#### TTL

*TTL* (time to live) là thời gian sống của một mục cache. Hết TTL, key bị coi như không tồn tại, lần
đọc sau miss và nạp lại.

TTL là **lưới an toàn cuối**. Dù code quên xoá cache ở một đường ghi nào đó (script import, sửa tay
trong DB, service khác ghi thẳng vào bảng), dữ liệu cũng chỉ sai tối đa bằng TTL. AWS khuyên: gắn TTL
cho **mọi** key, trừ key được cập nhật theo kiểu write-through; và TTL dài (vài giờ, vài ngày) vẫn
tốt hơn không có, vì nó chặn được những bug quên invalidate.

Chọn TTL bằng câu hỏi nghiệp vụ "dữ liệu này được phép cũ tối đa bao lâu", không bằng cảm tính:

| Loại dữ liệu | Hướng chọn | Lý do |
|---|---|---|
| Cấu hình, danh mục ít đổi | Vài phút tới vài giờ, kèm xoá khi sửa | Đổi hiếm, đọc ở mọi request |
| Dữ liệu đổi liên tục (comment, bảng xếp hạng, activity stream) | Vài giây | AWS gợi ý TTL vài giây cho loại này: đủ ngắn để gần như mới, vẫn chặn được phần lớn lần đọc lặp |
| Query nặng đang làm sập DB | Bọc bằng TTL rất ngắn (AWS ví dụ 5 giây) | Giảm tải ngay lập tức mà dữ liệu cũ tối đa 5 giây |
| Giá, tồn kho **lúc thanh toán** | Không dùng cache, đọc thẳng DB | AWS: giá hiển thị ở trang danh sách có thể cũ, giá tính tiền thì không |

Một nhận xét hay dùng khi phỏng vấn: với key rất nóng, TTL vài giây đã loại gần hết tải khỏi DB.
1000 request/giây vào một key với TTL 5 giây thì DB chỉ nhận khoảng một query mỗi 5 giây (cộng thêm
các miss đồng thời lúc key vừa hết hạn, chính là vấn đề stampede ở module 2.3).

Hành vi TTL trong Redis cần biết:

```sh
SET product:42:v1 '{"price":100}' EX 600   # ghi kèm TTL 600 giây
TTL product:42:v1                          # số giây còn lại
EXPIRE product:42:v1 60                    # đặt lại TTL
PERSIST product:42:v1                      # bỏ TTL, key sống vĩnh viễn
TTL product:42:v1                          # -1: key tồn tại nhưng không có TTL
TTL khong-co-key-nay                       # -2: key không tồn tại
```

- ⚠️ `SET` ghi đè một key sẽ **xoá TTL cũ** của nó (trừ khi thêm tuỳ chọn `KEEPTTL`). Ghi đè bằng
  `SET k v` không kèm `EX` là biến key thành vĩnh viễn, lỗi rất hay gặp. Lệnh sửa giá trị như
  `INCR` thì giữ nguyên TTL.
- Redis xoá key hết hạn theo hai cách: *passive* (khi có client chạm vào key thì kiểm tra và xoá) và
  *active* (định kỳ lấy mẫu các key có TTL để dọn). Vì vậy key hết hạn có thể còn chiếm bộ nhớ một
  lúc, nhưng không bao giờ được trả về cho client.

#### Jitter

*Jitter* là cộng thêm một khoảng ngẫu nhiên vào TTL, ví dụ `ttl = base + random(0, base * 0.1)`.
AWS đưa ví dụ `ttl = 3600 + (rand() * 120)`, tức lệch thêm tối đa hai phút.

Vì sao cần: các key thường được tạo **cùng lúc** (ngay sau deploy, sau khi flush cache, sau khi job
warm-up chạy). Nếu cùng TTL, chúng hết hạn cùng một giây và toàn bộ miss dồn vào DB một lúc. Hiện
tượng nhiều key hết hạn đồng loạt gọi là *avalanche* (module 2.3). Jitter làm các thời điểm hết hạn
tản ra, tải lên DB đều hơn.

```php
function ttlWithJitter(int $base): int
{
    return $base + random_int(0, intdiv($base, 10)); // 600 → 600..660 giây
}

Cache::remember("product:{$id}:v1", ttlWithJitter(600), fn () => Product::find($id));
```

Jitter giải quyết nhiều key hết hạn cùng lúc. Nó **không** giải quyết trường hợp một key cực nóng
hết hạn và hàng trăm request cùng miss nó (stampede); việc đó cần lock hoặc stale-while-revalidate
(module 2.3).

#### Bẫy giá trị `null`

⚠️ `Cache::remember` coi `null` là "không có trong cache". Nhìn vào mã nguồn Laravel: nó gọi `get`,
nếu kết quả khác `null` thì trả luôn, còn không thì chạy callback và `put` kết quả. Khi callback trả
`null` (ví dụ `User::find(999)` với id không tồn tại):

1. Lần 1: miss, chạy query, được `null`, Laravel vẫn ghi giá trị `null` (đã serialize) vào Redis.
2. Lần 2: `get` đọc được giá trị `null`, không phân biệt được với "không có key", nên lại coi là
   miss và chạy query.
3. Mọi lần sau: giống lần 2. Bản ghi không tồn tại thì **lần nào cũng xuống DB**.

`Cache::has()` cũng trả `false` khi key tồn tại nhưng giá trị là `null` (docs ghi rõ), nên không dùng
nó để phân biệt được.

Tại sao nguy hiểm: kẻ xấu (hoặc một client lỗi) gọi liên tục `GET /users/999999` với id không tồn
tại, cache không chặn được gì, toàn bộ tải rơi thẳng xuống DB. Hiện tượng này gọi là *cache
penetration*; module 2.3 bàn các cách phòng (negative caching, Bloom filter, validate input).

Cách khắc phục trực tiếp là **cache cả kết quả "không có"** (*negative caching*) bằng một giá trị
khác `null`:

```php
// Bọc trong mảng: mảng luôn khác null nên lần sau là hit, kể cả khi 'user' là null
$user = Cache::remember(
    "user:{$id}:v1",
    600,
    fn (): array => ['user' => User::find($id)],
)['user'];
```

Hoặc dùng marker riêng như `NULL_MARKER` trong ví dụ Redis thuần ở trên, kèm TTL ngắn hơn TTL thường
để khi bản ghi được tạo ra thì cache sớm thấy (hoặc xoá key ở luồng tạo mới). Đối chiếu: phpredis
trả `false` khi không có key, nên có vấn đề y hệt nếu bạn cache giá trị `false`.

**Tóm tắt nhanh**
- Cache-aside: đọc cache, miss thì đọc DB rồi ghi cache kèm TTL; ghi thì ghi DB rồi **xoá** key.
- Mọi key đều có TTL: đó là lưới an toàn cho mọi bug quên invalidate. TTL chọn theo mức cũ nghiệp vụ
  chấp nhận được; dữ liệu tính tiền thì không cache.
- Jitter tản thời điểm hết hạn của các key sinh cùng lúc (chống avalanche), không chống stampede của
  một key nóng.
- `remember` với callback trả `null` thì lần nào cũng xuống DB; cache một giá trị khác `null` với TTL
  ngắn.
- `SET` ghi đè xoá TTL cũ; lỗi cache phải được coi là miss thì app mới sống khi Redis chết.

**Nguồn**: [AWS: Caching best practices](https://aws.amazon.com/caching/best-practices/) ·
[Laravel: Retrieve & Store](https://laravel.com/docs/cache#retrieve-store) ·
[Laravel framework: Illuminate/Cache/Repository.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Cache/Repository.php)


---

### 1.3 Eviction cơ bản

Module này trả lời: khi cache đầy bộ nhớ thì bỏ key nào, LRU và LFU khác nhau thế nào (kèm mô phỏng
bằng tay), Redis thực thi các policy ra sao, và vì sao thư viện hiện đại như Caffeine dùng W-TinyLFU.

#### Eviction khác expiration

- *Expiration*: key hết hạn vì **hết TTL**. Do bạn chủ động đặt, xảy ra kể cả khi bộ nhớ còn trống.
- *Eviction*: key bị đuổi ra vì **đầy bộ nhớ**, do cache tự quyết theo một *eviction policy*
  (chính sách chọn key để bỏ).

Hai cơ chế độc lập: một key còn TTL một ngày vẫn có thể bị evict ngay khi bộ nhớ đầy, và một key
không có TTL vẫn có thể bị evict (tuỳ policy). Chúng liên quan ở một điểm: dùng TTL tốt thì nhiều key
tự hết hạn trước khi bộ nhớ kịp đầy, nên ít phải evict.

Vì sao evict được mà không mất dữ liệu: mục cache chỉ là **bản sao**, bỏ đi thì lần sau miss và nạp
lại từ DB. Điều này chỉ đúng khi Redis thật sự chỉ làm cache. Nếu cùng instance Redis còn giữ queue
job, session, rate limit counter, thì evict là **mất dữ liệu thật** (xem cạm bẫy cuối module).

Trong Redis, eviction được điều khiển bằng hai directive:

```sh
# redis.conf, hoặc đổi lúc chạy bằng CONFIG SET
maxmemory 100mb
maxmemory-policy allkeys-lru
```

Cơ chế: mỗi khi client chạy lệnh làm tăng dữ liệu, Redis kiểm tra bộ nhớ đang dùng; nếu vượt
`maxmemory`, nó evict key theo policy cho tới khi xuống dưới giới hạn. Một lệnh ghi rất lớn có thể
tạm thời đẩy bộ nhớ vượt giới hạn khá xa trước khi eviction bắt kịp.

⚠️ Mặc định trên hệ 64-bit, `maxmemory` là `0`, tức **không giới hạn**, và policy mặc định là
`noeviction`. Dựng Redis làm cache mà không cấu hình gì thì nó không bao giờ evict: bộ nhớ tăng tới
khi máy hết RAM (hoặc bị OOM killer). Dịch vụ managed có thể khác: AWS ElastiCache ghi mặc định là
`volatile-lru`. Luôn kiểm tra bằng `CONFIG GET maxmemory*`.

Khi dùng replication hoặc persistence (AOF), Redis cần thêm RAM cho buffer ghi sang replica/AOF, và
phần này **không** tính vào `maxmemory`. Vì vậy đặt `maxmemory` thấp hơn RAM máy một khoảng; lệnh
`INFO memory` có trường `mem_not_counted_for_evict` để ước lượng khoảng đó.

#### Các policy

Các thuật toán kinh điển:

| Policy | Bỏ mục nào | Hợp khi | Điểm yếu |
|---|---|---|---|
| LRU (least recently used) | Mục lâu nhất chưa được truy cập | Truy cập có tính cục bộ theo thời gian: thứ vừa dùng dễ được dùng lại | ⚠️ Một lần quét lớn đẩy hết key nóng ra |
| LFU (least frequently used) | Mục có số lần truy cập ít nhất | Tập key nóng ổn định lâu dài | Key mới khó chen vào; cần *decay* (giảm dần bộ đếm) không thì key từng nóng giữ chỗ mãi |
| FIFO | Mục vào sớm nhất | Rất đơn giản | Không quan tâm key có nóng không |
| TTL | Mục sắp hết hạn nhất | Khi TTL phản ánh độ quan trọng của key | Phụ thuộc hoàn toàn cách đặt TTL |
| Random | Ngẫu nhiên | Truy cập đều nhau; rẻ, không cần theo dõi gì | Có thể bỏ nhầm key nóng |

**Mô phỏng 1: quét lớn làm hại LRU.** Dung lượng 3, chuỗi truy cập `A A A B B C D E A B`. A và B là
key nóng; C, D, E là một lượt quét (ví dụ job export đọc lần lượt). Với LFU, khi hoà số đếm thì bỏ
key lâu chưa dùng hơn.

| Bước | Truy cập | LRU (cũ nhất → mới nhất) | LRU | LFU (key:đếm) | LFU |
|---|---|---|---|---|---|
| 1 | A | [A] | miss | {A:1} | miss |
| 2 | A | [A] | hit | {A:2} | hit |
| 3 | A | [A] | hit | {A:3} | hit |
| 4 | B | [A B] | miss | {A:3 B:1} | miss |
| 5 | B | [A B] | hit | {A:3 B:2} | hit |
| 6 | C | [A B C] | miss | {A:3 B:2 C:1} | miss |
| 7 | D | [B C D], bỏ A | miss | {A:3 B:2 D:1}, bỏ C | miss |
| 8 | E | [C D E], bỏ B | miss | {A:3 B:2 E:1}, bỏ D | miss |
| 9 | A | [D E A], bỏ C | miss | {A:4 B:2 E:1} | hit |
| 10 | B | [E A B], bỏ D | miss | {A:4 B:3 E:1} | hit |
| | | | **3 hit** | | **5 hit** |

LRU chỉ nhìn "vừa dùng lúc nào", nên ba key quét, dù mỗi key chỉ dùng một lần, vẫn đẩy A và B ra.
LFU nhớ A và B đã được dùng nhiều nên giữ lại. Phóng to lên đời thật: cache 1000 mục đang giữ 1000
sản phẩm hot, một job đọc 100.000 sản phẩm qua cache; với LRU thuần, sau job cache chỉ còn 1000 sản
phẩm cuối của job.

**Mô phỏng 2: đổi xu hướng làm hại LFU không decay.** Dung lượng 3, chuỗi `A A B B X Y X Y X Y`. A, B
từng nóng rồi không ai dùng nữa; X, Y là key nóng mới.

| Bước | Truy cập | LRU (cũ nhất → mới nhất) | LRU | LFU (key:đếm) | LFU |
|---|---|---|---|---|---|
| 1 | A | [A] | miss | {A:1} | miss |
| 2 | A | [A] | hit | {A:2} | hit |
| 3 | B | [A B] | miss | {A:2 B:1} | miss |
| 4 | B | [A B] | hit | {A:2 B:2} | hit |
| 5 | X | [A B X] | miss | {A:2 B:2 X:1} | miss |
| 6 | Y | [B X Y], bỏ A | miss | {A:2 B:2 Y:1}, bỏ X | miss |
| 7 | X | [B Y X] | hit | {A:2 B:2 X:1}, bỏ Y | miss |
| 8 | Y | [B X Y] | hit | {A:2 B:2 Y:1}, bỏ X | miss |
| 9 | X | [B Y X] | hit | {A:2 B:2 X:1}, bỏ Y | miss |
| 10 | Y | [B X Y] | hit | {A:2 B:2 Y:1}, bỏ X | miss |
| | | | **6 hit** | | **2 hit** |

Mỗi key mới vào với số đếm 1, nên luôn là nạn nhân kế tiếp, còn A và B "ăn vốn cũ" mãi. Đó là lý do
LFU thực tế phải có decay (bộ đếm giảm dần theo thời gian) và phải cho key mới một cơ hội.

Kết luận để trả lời phỏng vấn: LRU tốt khi tính "gần đây" dự đoán tốt tương lai (feed, session, dữ
liệu vừa tạo), tệ với quét lớn. LFU tốt khi tập key nóng ổn định (danh mục, cấu hình, sản phẩm bán
chạy), tệ khi xu hướng đổi nhanh nếu không có decay.

**Các policy của Redis.** Tên policy gồm hai phần: phạm vi (`allkeys` là mọi key, `volatile` là chỉ
key có TTL) và thuật toán.

| Policy | Hành vi |
|---|---|
| `noeviction` | Không evict. Lệnh ghi thêm dữ liệu trả lỗi (OOM), lệnh đọc vẫn chạy |
| `allkeys-lru` / `volatile-lru` | LRU xấp xỉ, trên mọi key / chỉ key có TTL |
| `allkeys-lfu` / `volatile-lfu` | LFU xấp xỉ (có từ Redis 4.0) |
| `allkeys-random` / `volatile-random` | Ngẫu nhiên |
| `volatile-ttl` | Key có TTL còn lại ngắn nhất |
| `allkeys-lrm` / `volatile-lrm` | *Least recently modified*: như LRU nhưng chỉ tính lần **ghi**, không tính lần đọc (có từ Redis 8.6; với Valkey kiểm tra docs) |

Lời khuyên của docs Redis:

- `allkeys-lru` là mặc định tốt khi không có lý do chọn cái khác: phần lớn workload có một nhóm nhỏ
  key được truy cập nhiều hơn hẳn phần còn lại (nguyên lý Pareto).
- `allkeys-random` khi mọi key được truy cập đều nhau, ví dụ đọc lặp theo vòng.
- `volatile-ttl` khi code tự đánh dấu được key nào nên bị bỏ trước bằng cách cho TTL ngắn.
- Các policy `volatile-*` chủ yếu hữu ích khi một instance vừa làm cache vừa giữ key bền vững (không
  TTL). Nhưng docs khuyên nếu được thì tách hai instance Redis riêng. Nếu không có key nào có TTL,
  các policy `volatile-*` hành xử như `noeviction`.
- `allkeys-lru` tiết kiệm bộ nhớ hơn vì không cần mỗi key mang một giá trị expire.

**LRU xấp xỉ.** Redis không giữ một danh sách LRU chính xác vì tốn bộ nhớ. Thay vào đó mỗi lần cần
evict, nó lấy mẫu ngẫu nhiên vài key và bỏ key có thời gian nhàn rỗi lâu nhất; từ Redis 3.0 có thêm
một *pool* các ứng viên tốt để kết quả sát LRU thật hơn. Số mẫu chỉnh bằng `maxmemory-samples`
(ví dụ trong docs là 5); tăng lên 10 thì sát LRU thật hơn, đổi lại tốn thêm CPU. Docs Redis cho biết
với truy cập theo phân phối luỹ thừa (*power law*, rất phổ biến), khác biệt giữa bản xấp xỉ và LRU
thật là rất nhỏ hoặc không có.

**LFU xấp xỉ.** Mỗi key chỉ có một bộ đếm vài bit, là *Morris counter*: bộ đếm xác suất, càng lên cao
càng khó tăng, nên vài bit đếm được tới cỡ hàng triệu lần truy cập. Kèm theo là decay: bộ đếm giảm
dần nếu key không được dùng, để thuật toán thích nghi khi xu hướng đổi (đúng bài học của mô phỏng 2).
Hai tham số, giá trị mặc định lấy từ docs:

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `lfu-log-factor` | 10 | Bộ đếm nằm trong khoảng 0–255; factor càng cao càng cần nhiều truy cập để chạm trần. Với 10, bộ đếm bão hoà quanh một triệu truy cập |
| `lfu-decay-time` | 1 | Số phút; một bộ đếm được lấy mẫu mà đã "cũ" hơn khoảng này thì bị giảm. `0` là không bao giờ decay |

Bảng trong docs Redis (giá trị bộ đếm theo số lần truy cập) cho thấy với factor 10: 100 lần truy
cập cho bộ đếm 10, 1000 lần cho 18, 100 nghìn lần cho 142, một triệu lần thì chạm 255.

**Chọn policy bằng số liệu, không đoán.** `INFO stats` có `keyspace_hits` và `keyspace_misses`:

```
hit ratio (%) = keyspace_hits / (keyspace_hits + keyspace_misses) * 100
```

Cách đọc theo docs Redis:

- Hit ratio thấp hơn kỳ vọng và `evicted_keys` cao: policy đang đuổi nhầm key, hoặc `maxmemory` quá
  nhỏ so với tập dữ liệu nóng.
- `evicted_keys` thấp nhưng `expired_keys` cao: TTL đang quá ngắn, key biến mất trước khi được dùng
  lại.
- Dùng `noeviction` hoặc `volatile-*`: xem mục `commandstats` để biết lệnh nào đang bị từ chối vì
  chạm `maxmemory`.

Lưu ý `EXISTS` trả "không có" cũng bị tính là một keyspace miss. Evict nhiều liên tục là tín hiệu cần
scale lên (node lớn hơn) hoặc scale ra (thêm node).

⚠️ Bẫy thực tế trong Laravel: config mặc định tách cache và dữ liệu khác bằng số database Redis
(connection `default` dùng DB `0`, connection `cache` dùng DB `1`). Nhưng `maxmemory` và policy áp
cho **cả instance**, không theo từng database. Đặt `allkeys-lru` cho một instance đang chứa cả queue
và session thì lúc đầy bộ nhớ, Redis có thể evict job trong queue hoặc session đang đăng nhập. Đặt
`noeviction` thì lúc đầy, mọi lệnh ghi cache lẫn đẩy job đều lỗi. Cách sạch nhất đúng như docs Redis
khuyên: instance riêng cho cache (`allkeys-lru` hoặc `allkeys-lfu`), instance riêng cho dữ liệu cần
bền (`noeviction`). Thêm một chi tiết: key tạo bằng `Cache::forever` không có TTL, nên với policy
`volatile-*` chúng không bao giờ bị evict.

#### W-TinyLFU

LRU thuần có hit ratio kém ở các workload như quét toàn bộ; LFU thuần kém khi xu hướng đổi. Caffeine
(thư viện cache in-process phổ biến của Java, được Spring Boot hỗ trợ sẵn làm cache provider) chọn *Window TinyLFU* (W-TinyLFU) để lấy ưu điểm của cả hai:

```
 key mới ──► [Window LRU nhỏ] ──bị đẩy ra──► cổng TinyLFU ──được nhận──► [Main: Segmented LRU lớn]
                                                │
                                   so tần suất ước lượng của ứng viên
                                   với key sắp bị bỏ ở vùng main;
                                   thua thì ứng viên bị loại
```

1. Key mới vào một *window* LRU nhỏ. Nhờ vậy key có "bùng nổ ngắn hạn" (vừa xuất hiện đã được đọc
   dồn dập) vẫn được giữ, điều LFU thuần làm không tốt (mô phỏng 2).
2. Khi bị đẩy khỏi window, key phải qua *admission policy* TinyLFU: nó chỉ được vào vùng chính nếu
   tần suất lịch sử ước lượng của nó cao hơn key đang chuẩn bị bị bỏ ở vùng chính. Key của một lượt
   quét chỉ được dùng một lần nên thua, bị loại, không đẩy được key nóng ra (khắc phục mô phỏng 1).
3. Tần suất được ước lượng bằng một *frequency sketch* (CountMinSketch 4 bit), một cấu trúc xác suất
   rất gọn, không cần lưu bộ đếm riêng cho từng key.
4. Tỉ lệ kích thước window so với vùng chính được tự điều chỉnh bằng *hill climbing* (thử tăng/giảm
   rồi giữ hướng làm hit ratio tốt lên), nên policy tự thích nghi khi workload chuyển giữa kiểu
   "gần đây" và kiểu "tần suất".

Kết quả mô phỏng trong wiki Caffeine trên các trace thật (Wikipedia, database ERP, search engine,
OLTP...): W-TinyLFU cho hit ratio gần mức tối ưu lý thuyết (thuật toán Bélády, biết trước tương lai),
cạnh tranh với ARC và LIRS, và hơn LRU đáng kể. Khác ARC và LIRS, nó không phải giữ lại danh sách các
key đã bị evict, nên tốn ít bộ nhớ hơn (ARC còn vướng bằng sáng chế).

Đối chiếu nhanh: Redis cho chọn LRU hoặc LFU xấp xỉ ở phía server; Caffeine (Java) chạy W-TinyLFU
trong process; PHP không có thư viện in-process tương đương vì mô hình share-nothing, và APCu không có
policy tinh vi như vậy. Cache nhiều tầng L1 in-process + L2 Redis ở module 3.1.

**Tóm tắt nhanh**
- Expiration là hết TTL, eviction là đầy bộ nhớ; hai cơ chế độc lập.
- Redis mặc định `maxmemory 0` + `noeviction`: dùng làm cache thì phải đặt cả hai. `allkeys-lru` là
  lựa chọn mặc định hợp lý.
- LRU thua khi có quét lớn; LFU thua khi xu hướng đổi nếu không có decay. Tự mô phỏng được bằng bảng.
- Redis dùng LRU/LFU **xấp xỉ** bằng lấy mẫu (`maxmemory-samples`), LFU dùng Morris counter + decay.
- Không để cache chung instance với queue/session: policy áp cho cả instance. Đo bằng
  `keyspace_hits`, `keyspace_misses`, `evicted_keys`, `expired_keys`.

**Nguồn**: [Redis: Key eviction](https://redis.io/docs/latest/develop/reference/eviction/) ·
[Caffeine wiki: Efficiency](https://github.com/ben-manes/caffeine/wiki/Efficiency) ·
[AWS: Caching best practices](https://aws.amazon.com/caching/best-practices/)

---

## Chặng 2: Làm chủ

### 2.1 Pattern đọc/ghi

Module này trả lời: ngoài cache-aside còn những cách nào để đọc và ghi qua cache, mỗi cách đổi độ
nhất quán lấy tốc độ ra sao, và vì sao write-behind là pattern duy nhất trong nhóm có thể làm
**mất dữ liệu**.

Trước khi so sánh, cần tách hai câu hỏi mà mọi pattern phải trả lời:

1. **Ai nạp dữ liệu vào cache khi đọc?** App tự làm (cache-aside), hay cache tự gọi loader
   (read-through).
2. **Khi ghi, cache và DB được cập nhật theo thứ tự nào, đồng bộ hay không?** Chỉ ghi DB rồi xoá key
   (cache-aside), ghi cả hai đồng bộ (write-through), hay ghi cache trước rồi DB sau (write-behind).

Refresh-ahead là một chiều thứ ba: **khi nào** làm mới, trước hay sau lúc hết hạn.

```
               ĐỌC                                   GHI
  cache-aside   app ──get──▶ cache                   app ──▶ DB, rồi app ──DEL──▶ cache
                app ──miss──▶ DB ──set──▶ cache
  read-through  app ──get──▶ cache ──loader──▶ DB    (kết hợp với một cách ghi bất kỳ)
  write-through                                      app ──▶ cache ──đồng bộ──▶ DB ──▶ OK
  write-behind                                       app ──▶ cache ──▶ OK   ...sau đó theo lô ──▶ DB
```

#### Read-through

*Read-through*: code nghiệp vụ chỉ nói chuyện với cache. Khi miss, **chính thư viện cache** gọi một
hàm nạp (*loader*) đã đăng ký sẵn, lưu kết quả rồi trả về. Về luồng dữ liệu, nó giống hệt cache-aside
(miss thì đọc DB, ghi cache). Khác biệt là **logic nạp nằm ở đâu**:

| | Cache-aside | Read-through |
|---|---|---|
| Ai gọi DB khi miss | Code nghiệp vụ, ở mỗi chỗ đọc | Thư viện cache, qua loader đăng ký một lần |
| Code gọi | `get`, kiểm tra miss, đọc DB, `set` | Chỉ `get(key)` |
| Gom request cùng key | Tự làm | Thường có sẵn trong thư viện |

Ví dụ điển hình ở Java:

- Caffeine `LoadingCache`: tạo cache bằng `Caffeine.newBuilder()...build(key -> loadFromDb(key))`,
  sau đó chỉ gọi `cache.get(key)`. Caffeine đảm bảo cùng một key chỉ có một lần load chạy tại một
  thời điểm trong process, các thread khác chờ kết quả đó (đây là *request coalescing*, module 2.3).
- JCache (JSR-107, chuẩn cache của Java) có sẵn khái niệm `CacheLoader` và cờ bật read-through
  trong cấu hình.

Trong Laravel, `Cache::remember($key, $ttl, $loader)` trông như read-through (bạn chỉ đưa loader),
nhưng bản chất vẫn là cache-aside: loader được truyền vào ở **từng chỗ gọi**, không đăng ký tập trung,
và không có gom request giữa các process PHP.

#### Write-through

Thuật ngữ này được dùng theo hai nghĩa, nên khi phỏng vấn hãy nói rõ bạn đang dùng nghĩa nào:

1. **Nghĩa cổ điển** (thư viện cache đứng giữa app và DB): app ghi vào cache, và cache ghi **đồng bộ**
   xuống DB qua một `CacheWriter`/`MapStore`, chỉ báo thành công khi cả hai xong. JCache có cờ bật
   write-through; Hazelcast `MapStore` với độ trễ ghi bằng 0 là write-through.
2. **Nghĩa trong tài liệu AWS** (cache là Redis riêng, app điều phối): app ghi DB, rồi **ngay sau đó**
   app cập nhật giá trị mới vào cache (thay vì xoá key như cache-aside).

Cả hai nghĩa chung một ý: sau mỗi lần ghi, cache đã chứa giá trị mới, nên lần đọc sau là hit.

Ưu điểm (theo AWS):
- Cache luôn "ấm": dữ liệu vừa ghi có sẵn, xác suất hit cao hơn, DB bớt đọc.

Nhược điểm:
- Mỗi lần ghi chậm hơn vì phải ghi hai nơi.
- Dữ liệu ít được đọc cũng bị đưa vào cache, cache to và tốn tiền hơn. AWS gọi là *cache churn* khi
  cùng một object bị ghi đè liên tục.
- Write-through **không thay được lazy loading**: key vẫn có thể biến mất (evict, hết TTL, Redis
  restart), nên luồng đọc vẫn phải xử lý miss. AWS ghi rõ write-through "gần như luôn" đi kèm lazy
  loading.
- ⚠️ Ở nghĩa 2, "ghi DB rồi set cache" chính là "set thay vì xoá" ở module 2.2: hai request ghi đồng
  thời có thể set cache theo thứ tự ngược với thứ tự ghi DB, để lại giá trị sai. Vì vậy với dữ liệu có
  nhiều người cùng sửa, cách an toàn mặc định vẫn là xoá key.

Khi nào dùng: AWS gợi ý lấy lazy loading làm nền, và write-through cho dữ liệu chắc chắn sẽ được đọc,
thường là dữ liệu tổng hợp do một đoạn code hoặc job riêng cập nhật, ví dụ "top 100 bảng xếp hạng game"
hay "10 tin nổi bật nhất". Thêm điều kiện "ít người cùng sửa" là vì race ở gạch đầu dòng trên. AWS
cũng khuyên luôn đặt TTL cho mọi key, trừ key được cập nhật bằng write-through.

#### Write-behind

*Write-behind* (còn gọi *write-back*): app ghi vào cache rồi **trả về ngay**. Việc ghi xuống DB diễn
ra sau đó, bất đồng bộ, thường gom thành lô.

Vì sao nhanh: request chỉ chờ một lệnh Redis (trong mạng nội bộ thường chưa tới một mili giây) thay vì một câu `UPDATE`
có transaction, fsync redo log. Thêm nữa, 1000 lần `+1` vào cùng một bộ đếm trong 10 giây được gom
thành **một** câu `UPDATE ... SET views = views + 1000`. DB nhận ít ghi hơn hẳn và ít tranh chấp lock
trên cùng một dòng nóng.

Use case thật: view count, like count, "last seen", điểm số tạm thời, metrics. Đặc điểm chung: ghi rất
nhiều, mất một ít thì không ai kiện.

⚠️ Cái giá: trong khoảng giữa "đã báo thành công" và "đã flush xuống DB", dữ liệu **chỉ tồn tại trong
cache**. Cache sập (mất điện, OOM, failover sang replica chưa kịp nhận) trong khoảng đó là mất.
Lượng mất tối đa xấp xỉ bằng một chu kỳ flush: flush mỗi 10 giây thì mất tối đa khoảng 10 giây ghi
(cộng thêm phần chưa kịp nhân bản nếu Redis có persistence/replica). Vì vậy **không bao giờ** dùng
write-behind cho tiền, đơn hàng, tồn kho.

Cài write-behind cho view count bằng Laravel và Redis (ví dụ minh hoạ, cần Redis và bảng `posts` có
cột `views`):

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;

// Đường ghi nóng: mỗi lượt xem chỉ tốn một lệnh Redis, không chạm DB
function recordView(int $postId): void
{
    Redis::hincrby('views:pending', (string) $postId, 1);
}

// Job chạy theo lịch (ví dụ mỗi 10 giây): chu kỳ này chính là lượng dữ liệu tối đa có thể mất
function flushViews(): void
{
    // Đổi tên atomic: lượt xem mới từ giờ rơi vào một hash 'views:pending' mới,
    // không lẫn với lô đang flush
    if ((int) Redis::exists('views:flushing') === 0) {
        if ((int) Redis::exists('views:pending') === 0) {
            return; // không có gì để flush
        }
        Redis::rename('views:pending', 'views:flushing');
    }
    // Nếu lần chạy trước chết giữa chừng, 'views:flushing' còn đó và được flush lại ở đây

    /** @var array<string, string> $batch */
    $batch = Redis::hgetall('views:flushing');
    DB::transaction(function () use ($batch): void {
        foreach ($batch as $postId => $count) {
            DB::update('UPDATE posts SET views = views + ? WHERE id = ?', [(int) $count, (int) $postId]);
        }
    });
    Redis::del('views:flushing');
}
```

Những điểm đáng học trong đoạn code:

- `RENAME` là atomic, nên không có lượt xem nào bị đếm vào lô đang flush sau khi đã đọc.
- ⚠️ Nếu process chết **sau** khi transaction commit nhưng **trước** `DEL`, lần chạy sau flush lại lô
  cũ và đếm trùng. Với view count thì chấp nhận được. Muốn chính xác thì cần ghi kèm một mã lô
  (batch id) vào DB trong cùng transaction để bỏ qua lô đã xử lý, tức là làm cho flush *idempotent*.
- Giữa `exists` và `rename` có khe nhỏ nếu hai worker flush cùng lúc; chạy job bằng một worker duy
  nhất (Laravel scheduler có `withoutOverlapping()`/`onOneServer()`) hoặc gói vào Lua.
- Số liệu hiển thị (DB cộng phần đang chờ trong Redis) có thể trễ tới một chu kỳ flush. Đó là "DB bị
  trễ so với cache" trong bảng so sánh bên dưới.

Ở phía thư viện, Hazelcast `MapStore` với độ trễ ghi lớn hơn 0 là write-behind; nhiều hệ thống dùng
queue (Kafka, Redis Streams) làm lớp đệm bền hơn để giảm rủi ro mất dữ liệu.

#### Refresh-ahead

*Refresh-ahead*: làm mới một key **trước khi** nó hết hạn, để key nóng không bao giờ rơi vào trạng
thái miss. Có hai cách kích hoạt:

1. **Theo lịch**: một job nền định kỳ tính lại và ghi đè các key đã biết là nóng (trang chủ, cấu hình,
   bảng giá). Đây là cách paper XFetch gọi là *external re-computation* (module 2.3): chặn stampede
   hoàn toàn, nhưng phải duy trì thêm một process, và job có thể làm mới cả key không còn ai đọc.
2. **Theo lượt đọc**: khi một lần đọc thấy key "sắp hết hạn" (ví dụ đã qua 80% TTL), nó kích hoạt làm
   mới ở nền và vẫn trả giá trị hiện có. Caffeine có `refreshAfterWrite`: sau khoảng thời gian cấu hình,
   lần đọc kế tiếp kích hoạt reload bất đồng bộ, trong lúc đó vẫn trả giá trị cũ. `Cache::flexible` của
   Laravel và XFetch đều là họ hàng của cách này (module 2.3, 2.7).

Cái giá: tốn công làm mới những key có thể không ai đọc nữa, và phải đoán đúng key nào đáng làm mới
trước. Lợi ích chỉ rõ với key vừa nóng vừa đắt để tính.

#### So sánh

| Pattern | Độ nhất quán | Tốc độ đọc | Tốc độ ghi | Rủi ro chính |
|---|---|---|---|---|
| Cache-aside | Có cửa sổ cũ, giới hạn bằng TTL | Miss lần đầu | Nhanh (ghi DB, xoá key) | Race khi ghi đồng thời (module 2.2) |
| Read-through | Như cache-aside | Miss lần đầu | Như cách ghi đi kèm | Như cache-aside; phụ thuộc thư viện |
| Write-through | Cao ngay sau ghi | Nhanh, ít miss | Chậm hơn (ghi hai nơi) | Cache đầy dữ liệu lạnh; set đồng thời lệch thứ tự |
| Write-behind | DB trễ so với cache | Nhanh | Rất nhanh, gom lô | **Mất dữ liệu chưa flush** |
| Refresh-ahead | Tốt với key nóng | Không miss với key nóng | Không ảnh hưởng | Làm mới thừa |

Thực tế các pattern không loại trừ nhau. Một hệ thống thường dùng: cache-aside làm nền cho hầu hết dữ
liệu, write-through cho vài dữ liệu đọc cực nhiều, write-behind cho counter, refresh-ahead cho vài key
đắt nhất. Câu trả lời phỏng vấn tốt là chọn theo **từng loại dữ liệu**, không chọn một pattern cho cả
hệ thống.

**Tóm tắt nhanh**
- Read-through khác cache-aside ở chỗ loader nằm trong thư viện cache, luồng dữ liệu thì như nhau.
- Write-through: cache luôn có giá trị mới sau ghi, trả bằng ghi chậm hơn và cache đầy dữ liệu lạnh;
  vẫn phải xử lý miss như lazy loading.
- Write-behind: nhanh nhất và gom được ghi, nhưng cache sập trước flush là mất; lượng mất tối đa xấp
  xỉ một chu kỳ flush. Chỉ dùng cho counter và dữ liệu mất được.
- Refresh-ahead: làm mới trước hạn để key nóng không miss; tốn công làm mới thừa.
- Chọn pattern theo từng loại dữ liệu, cache-aside làm nền.

**Nguồn**: [AWS whitepaper: Caching patterns](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html) ·
[AWS: Caching best practices](https://aws.amazon.com/caching/best-practices/) ·
[Optimal Probabilistic Cache Stampede Prevention](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf) (mục 1, phần external re-computation)

---

### 2.2 Invalidation và race condition

Module này trả lời: khi dữ liệu gốc đổi, làm sao để cache không còn trả bản cũ; vì sao cả hai thứ tự
"xoá cache rồi update DB" và "update DB rồi xoá cache" đều có race; và những bug thật trong Laravel
(xoá trong transaction, nạp từ replica) trông như thế nào trên timeline.

#### Invalidation là gì

*Invalidation* là làm cho mục cache cũ không còn được dùng khi dữ liệu gốc thay đổi. Có ba công cụ, từ
yếu tới mạnh về mức chủ động:

1. **TTL**: không làm gì cả, chờ mục cache tự hết hạn. Luôn có, là lưới an toàn cuối (module 1.2).
2. **Xoá key** ngay khi ghi (explicit delete).
3. **Đổi tên key** để code không bao giờ đọc key cũ nữa (versioned key).

*Race condition* ở đây là khi hai request (một đọc, một ghi, hoặc hai ghi) chạy đan xen theo một thứ tự
xấu, và kết quả cuối cùng là cache giữ giá trị cũ **sau khi** DB đã có giá trị mới. Điểm nguy hiểm: giá
trị cũ đó sống tới hết TTL, không ai xoá nữa vì lệnh xoá đã chạy rồi. Paper Facebook gọi đây là
*stale set*: một web server set vào cache một giá trị không còn là giá trị mới nhất, do các thao tác
đồng thời bị đảo thứ tự.

Mọi timeline trong module này dùng quy ước: key `product:1`, DB ban đầu có `price = 100`, request A đổi
giá thành 200.

#### Hai cách invalidate

**Explicit delete**: ghi DB xong thì `DEL` key.

- Rẻ, dễ hiểu, lần đọc sau miss và nạp bản mới.
- ⚠️ Phần khó nhất không phải lệnh xoá mà là **biết hết key nào liên quan**. Sửa giá sản phẩm 1 thì
  phải xoá: `product:1`, danh sách của danh mục chứa nó (mỗi trang một key), trang chủ nếu nó nằm ở
  mục "bán chạy", kết quả search có nó. Quên một key là người dùng thấy hai giá khác nhau trên hai
  trang. Cách giảm đau: cache danh sách dưới dạng **danh sách id** và lấy chi tiết từng id (module 2.5),
  khi đó sửa một sản phẩm chỉ cần xoá một key.

**Versioned key**: nhét một số version vào tên key.

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\Cache;

function catalogVersion(): int
{
    // Khởi tạo bằng timestamp chứ không phải 1: nếu key version bị mất, giá trị mới
    // không trùng với version cũ nào còn sót trong cache
    $v = Cache::get('catalog:version');
    if ($v === null) {
        // add chỉ atomic khi có TTL (Redis store chạy một Lua script: EXISTS rồi SETEX);
        // không truyền TTL thì Laravel làm get rồi put, hai request có thể ghi đè nhau
        Cache::add('catalog:version', time(), 30 * 86400);
        $v = Cache::get('catalog:version');
    }
    return (int) $v;
}

function categoryPage(int $categoryId, int $page): array
{
    $key = sprintf('catalog:v%d:category:%d:page:%d', catalogVersion(), $categoryId, $page);
    return Cache::remember($key, 3600, fn (): array => loadCategoryPage($categoryId, $page));
}

// Invalidate TOÀN BỘ catalog bằng một lệnh, không cần biết có bao nhiêu key
function invalidateCatalog(): void
{
    catalogVersion();                      // đảm bảo key đã tồn tại: INCR trên key trống sẽ ra 1
    Cache::increment('catalog:version');
}
```

- Tăng version thì mọi lần đọc sau tạo ra tên key mới, nên miss và nạp bản mới. Các key version cũ
  không bị xoá mà thành rác, tự biến mất khi hết TTL (hoặc bị evict vì không ai đọc).
- Ưu điểm lớn: invalidate **một nhóm không liệt kê được** (mọi trang, mọi bộ lọc của catalog) chỉ bằng
  một `INCR`, không cần `KEYS catalog:*` (lệnh quét toàn bộ keyspace, chặn Redis).
- Cái giá: mỗi lần đọc thêm một lần đọc key version (có thể gộp bằng `MGET`, hoặc giữ version trong L1
  vài giây); sau mỗi lần tăng version, cả nhóm cùng miss một lượt (nguy cơ stampede nhỏ, module 2.3); bộ
  nhớ tạm thời chứa cả bản cũ lẫn mới.
- ⚠️ Key version là key quan trọng nhất của nhóm. Nếu nó bị evict và code khởi tạo lại bằng `1`, code sẽ
  đọc lại đúng các key `v1` cũ còn sót, tức là **hồi sinh dữ liệu cũ**. Vì vậy ví dụ trên khởi tạo bằng
  timestamp; tốt hơn nữa là để key version trên instance không evict hoặc lưu version trong DB.

Cùng ý tưởng ở quy mô nhỏ: `user:123:v2` khi đổi cấu trúc object (module 2.5).

#### Xoá cache rồi update DB

Thứ tự này có vẻ hợp lý ("dọn trước rồi ghi"), nhưng cửa sổ lỗi rất rộng:

| Bước | Request A (ghi) | Request B (đọc) | Cache `product:1` | DB `price` |
|---|---|---|---|---|
| 1 | `DEL product:1` | | (trống) | 100 |
| 2 | Bắt đầu `UPDATE`, đang chạy | `GET product:1`: miss | (trống) | 100 |
| 3 | | `SELECT price`: đọc được **100** | (trống) | 100 |
| 4 | | `SET product:1 = 100` | **100** | 100 |
| 5 | `UPDATE` xong, commit | | 100 | 200 |
| 6 | | | **100, sai tới hết TTL** | 200 |

Điều kiện để lỗi xảy ra: chỉ cần **một lần đọc bất kỳ** rơi vào khoảng giữa bước 1 và lúc A commit.
Khoảng đó dài bằng cả thời gian chạy transaction của A (có thể hàng chục, hàng trăm mili giây, hoặc lâu
hơn nếu transaction làm nhiều việc). Với key nóng hàng trăm lượt đọc mỗi giây, lỗi gần như **chắc chắn**
xảy ra. Đây là lý do cách này bị coi là sai.

#### Update DB rồi xoá cache (cách thường dùng)

Đây là cách paper Facebook dùng: web server ghi SQL vào DB, sau đó gửi lệnh delete tới memcache. Nó
vẫn có race, nhưng cần một thứ tự hiếm hơn nhiều:

| Bước | Request A (ghi) | Request B (đọc) | Cache `product:1` | DB `price` |
|---|---|---|---|---|
| 1 | | `GET product:1`: miss (key vừa hết hạn) | (trống) | 100 |
| 2 | | `SELECT price`: đọc được **100** | (trống) | 100 |
| 3 | `UPDATE price = 200`, commit | (B bị chậm: GC, CPU, mạng) | (trống) | 200 |
| 4 | `DEL product:1` (không có gì để xoá) | | (trống) | 200 |
| 5 | | `SET product:1 = 100` | **100, sai tới hết TTL** | 200 |

Điều kiện để lỗi xảy ra, cả ba cùng lúc:

1. Cache đang trống đúng lúc đó (key vừa hết hạn, vừa bị evict, hoặc vừa bị xoá bởi lần ghi trước).
2. B đọc DB **trước** khi A commit.
3. B ghi cache **sau** khi A xoá.

Tức là quãng "đọc DB rồi ghi cache" của B phải dài hơn cả quãng "update, commit, xoá" của A. Bình
thường ghi DB chậm hơn nhiều so với một lần `SET`, nên xác suất thấp, nhưng không bằng 0: B có thể bị
pause GC (Java), bị CPU throttle, bị mạng chậm. Ở quy mô lớn, xác suất thấp nhân với hàng tỉ request
là chuyện xảy ra hằng ngày. Vì vậy:

- Luôn có TTL để giới hạn thời gian giá trị sai sống.
- Muốn đóng hẳn khe này thì cần cơ chế từ chối lần `SET` lỗi thời: *lease* của Facebook (module 3.2),
  hoặc set có điều kiện theo version (cuối module này).

So sánh hai thứ tự:

| | Xoá rồi update | Update rồi xoá |
|---|---|---|
| Cửa sổ lỗi | Cả thời gian transaction của A | Chỉ khi đọc chậm hơn cả lần ghi |
| Cần cache đang trống sẵn | Không (A tự làm trống) | Có |
| Xác suất với key nóng | Rất cao | Thấp |
| Kết luận | Tránh | Dùng, kèm TTL |

#### Các lỗi hay gặp khác

**Xoá cache thất bại.** Redis timeout, mất kết nối, hoặc process chết giữa "commit DB" và "DEL". Lúc đó
cache giữ bản cũ tới hết TTL mà không ai biết. Cách xử lý:

- Không nuốt lỗi âm thầm: log và đếm metric cho lỗi xoá cache.
- Retry: đẩy lệnh xoá vào queue (job có retry) thay vì gọi một lần trong request.
- Tách hẳn việc xoá ra khỏi code nghiệp vụ: đọc log thay đổi của DB (binlog MySQL) để phát lệnh xoá,
  gọi là CDC (module 3.2). Facebook làm đúng như vậy: câu SQL ghi kèm danh sách key cần xoá, và một
  daemon tên *mcsqueal* trên mỗi DB đọc các câu đã commit rồi phát lệnh xoá. Paper nêu lợi ích then
  chốt: lệnh xoá nằm trong log bền của DB nên **phát lại được** khi bị mất hay gửi nhầm, trong khi
  để web server tự xoá thì khi có sự cố hệ thống (ví dụ lệnh xoá bị định tuyến sai do lỗi cấu hình)
  rất ít cách khắc phục; trước đây họ thường phải restart cuốn chiếu cả hạ tầng memcache.

**⚠️ Xoá cache bên trong transaction, trước khi commit.** Đây là bug Laravel rất hay gặp, vì
`Cache::forget()` được gọi ngay sau `save()`, mà `save()` lại nằm trong `DB::transaction()`:

```php
DB::transaction(function () use ($product): void {
    $product->update(['price' => 200]);
    Cache::forget("product:{$product->id}");   // SAI: chạy khi transaction chưa commit
    $this->recalculateBundles($product);        // còn chạy thêm 300 ms nữa
});
```

| Bước | Request A (ghi, trong transaction) | Request B (đọc) | Cache | DB (đã commit) |
|---|---|---|---|---|
| 1 | `BEGIN`; `UPDATE price = 200` (chưa commit) | | 100 | 100 |
| 2 | `Cache::forget` | | (trống) | 100 |
| 3 | Đang chạy `recalculateBundles` | Miss; `SELECT`: không thấy dữ liệu chưa commit, đọc **100** | (trống) | 100 |
| 4 | | `SET product:1 = 100` | **100** | 100 |
| 5 | `COMMIT` | | **100, sai tới hết TTL** | 200 |

Về bản chất, đây chính là "xoá rồi update" trá hình: với mọi request khác, update chỉ thật sự xảy ra
lúc commit, nên xoá trước commit tương đương xoá trước update. Ở mọi isolation level (trừ READ
UNCOMMITTED), B không đọc được dữ liệu A chưa commit. Cách sửa là dời lệnh xoá ra **sau commit**:

```php
<?php
declare(strict_types=1);

use App\Models\Product;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;

function changePrice(Product $product, int $newPrice): void
{
    DB::transaction(function () use ($product, $newPrice): void {
        $product->update(['price' => $newPrice]);

        // Đăng ký callback chạy SAU khi transaction ngoài cùng commit.
        // Không có transaction nào đang mở thì Laravel chạy callback ngay.
        DB::afterCommit(fn () => Cache::forget("product:{$product->id}"));
    });
}
```

- `DB::afterCommit()` là method của connection (trait `ManagesTransactions` trong framework). Nó không
  được mô tả trong trang docs Database, nhưng có trong source Laravel; nếu transaction rollback thì
  callback không chạy.
- Nếu xoá cache trong model observer, cho observer `implements ShouldHandleEventsAfterCommit`; nếu
  qua event, cho event `implements ShouldDispatchAfterCommit`. Cả hai làm handler chờ commit.
- Cùng họ bug với dispatch job trong transaction (Laravel docs, mục *Jobs & Database Transactions*):
  job có thể được worker chạy **trước** khi transaction commit, nên không thấy dữ liệu mới. Lời giải
  cũng giống nhau: `->afterCommit()` hoặc cấu hình `'after_commit' => true` cho queue connection; khi
  transaction rollback thì job bị bỏ. Timeline chi tiết:
  [03-database-sql.md, mục 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel).
- Spring có cùng công cụ: `@TransactionalEventListener(phase = AFTER_COMMIT)`.

**⚠️ Nạp cache từ replica đang lag.** Laravel cấu hình `read`/`write` connection gửi `SELECT` sang
replica. *Replication lag* là độ trễ từ lúc primary commit tới lúc replica áp dụng thay đổi đó (DDIA
chương 5, *Problems with Replication Lag*; replication MySQL mặc định là bất đồng bộ nên lag có thể từ
vài mili giây tới vài phút khi replica quá tải).

| Bước | Request A (ghi, primary) | Request B (đọc, replica) | Cache | Primary | Replica |
|---|---|---|---|---|---|
| 1 | `UPDATE price = 200`, commit | | 100 | 200 | 100 (chưa nhận) |
| 2 | `DEL product:1` (sau commit, đúng quy tắc) | | (trống) | 200 | 100 |
| 3 | | Miss; `SELECT` trên replica: đọc **100** | (trống) | 200 | 100 |
| 4 | | `SET product:1 = 100` | **100** | 200 | 100 |
| 5 | | | **100, sai tới hết TTL** | 200 | 200 (đã nhận) |

Lần này mọi thứ tự trong code đều đúng, nhưng vẫn sai, vì "DB" thực ra là hai máy với hai trạng thái.
Tuỳ chọn `sticky` của Laravel không cứu được: nó chỉ ép **cùng request** đã ghi đọc từ primary, còn B là
request khác. Cách sửa:

- Loader của cache đọc từ primary, ví dụ `Product::onWriteConnection()->find($id)`. Hợp lý vì lượng đọc
  vào loader đã được cache giảm đi nhiều; cái giá là thêm tải cho primary.
- Delayed double delete (ngay dưới), với khoảng chờ lớn hơn replica lag điển hình.
- Theo dõi replica lag như một metric; lag vượt ngưỡng thì chuyển loader sang primary.

Chi tiết replication và các kiểu nhất quán đọc (read-your-writes, monotonic reads):
[03-database-sql.md, mục 3.4](03-database-sql.md#34-replication-và-failover).

#### Delayed double delete

Kỹ thuật dọn giá trị cũ lỡ được nạp trong cửa sổ race:

1. Xoá cache.
2. Update DB (và commit).
3. Chờ một khoảng **lớn hơn** thời gian một lần "đọc DB rồi ghi cache", hoặc lớn hơn replica lag.
4. Xoá cache lần nữa, để dọn giá trị cũ có thể đã được nạp trong lúc đó.

Trong Laravel, lần xoá thứ hai là một job có delay, không phải `sleep()` trong request (sleep chiếm một
worker PHP-FPM và làm chậm người dùng):

```php
DB::transaction(function () use ($product): void {
    $product->update(['price' => 200]);
    DB::afterCommit(function () use ($product): void {
        $key = "product:{$product->id}";
        Cache::forget($key);                                          // lần 1
        dispatch(fn () => Cache::forget($key))->delay(now()->addSeconds(2));  // lần 2, sau 2 giây
    });
});
```

- ⚠️ Khoảng chờ là **đoán**, không phải đảm bảo. Replica lag 5 giây thì lần xoá sau 2 giây vẫn không đủ,
  và request B chậm bất thường vẫn có thể `SET` sau lần xoá thứ hai. Nó giảm xác suất, không đóng hẳn
  khe race. Phỏng vấn mà nói "double delete là giải quyết triệt để" là red flag.
- Mỗi lần ghi tạo thêm một job và một lượt miss nữa cho key đó.
- Bước 1 (xoá trước khi update) không bắt buộc; nhiều nơi chỉ làm "update, xoá, chờ, xoá".

#### Vì sao xoá thay vì set

Ghi DB xong mà **set** giá trị mới vào cache (thay vì xoá) thì hai lần ghi đồng thời có thể để cache
lệch với DB vĩnh viễn (tới hết TTL):

| Bước | Request A (giá = 1) | Request B (giá = 2) | Cache | DB |
|---|---|---|---|---|
| 1 | `UPDATE price = 1`, commit | | cũ | 1 |
| 2 | (A bị chậm trước khi set cache) | `UPDATE price = 2`, commit | cũ | 2 |
| 3 | | `SET product:1 = 2` | 2 | 2 |
| 4 | `SET product:1 = 1` | | **1** | 2 |

Thứ tự ghi vào DB (A trước B) và thứ tự ghi vào cache (B trước A) không có gì ràng buộc nhau, vì là
hai hệ thống riêng. Xoá thì không có thứ tự nào để sai: hai lệnh `DEL` chạy theo thứ tự nào cũng để lại
cache trống, và lần đọc sau luôn lấy từ DB. Paper Facebook nói ngắn gọn lý do họ chọn xoá: lệnh xoá là
*idempotent* (chạy một lần hay nhiều lần kết quả như nhau).

Hai lý do phụ để chọn xoá:
- Giá trị cache thường được **tổng hợp** từ nhiều bảng (sản phẩm + giá + khuyến mãi + tồn kho). Tính lại
  toàn bộ giá trị đó ở mỗi đường ghi vừa tốn vừa dễ sai; xoá thì để lần đọc sau tự tính.
- Dữ liệu vừa ghi chưa chắc có ai đọc; set là tốn công cho cache lạnh (nhược điểm của write-through,
  module 2.1).

Ngoại lệ, khi set là an toàn:

- **Phép cộng không phụ thuộc thứ tự**: counter dùng `INCR`/`HINCRBY`. `+1` rồi `+2` hay `+2` rồi `+1`
  đều ra `+3`.
- **Set có điều kiện theo version**: mỗi dòng DB có cột `version` tăng ở mỗi lần update (như optimistic
  lock, [03-database-sql.md, mục 2.6](03-database-sql.md#26-lock-thực-dụng)). Cache lưu kèm version,
  và chỉ nhận bản ghi có version **mới hơn** bản đang có. Việc "so rồi ghi" phải atomic, nên dùng Lua:

```lua
-- KEYS[1] = product:1   ARGV[1] = version mới   ARGV[2] = dữ liệu   ARGV[3] = TTL (giây)
local cur = redis.call('HGET', KEYS[1], 'v')
if cur and tonumber(cur) >= tonumber(ARGV[1]) then
  return 0  -- bản trong cache mới hơn hoặc bằng: bỏ qua lần set lỗi thời
end
redis.call('HSET', KEYS[1], 'v', ARGV[1], 'data', ARGV[2])
redis.call('EXPIRE', KEYS[1], ARGV[3])
return 1
```

  Ở timeline trên, bước 4 (A set version cũ hơn) bị từ chối. Lưu ý: cách này chặn được "set lệch thứ
  tự", nhưng nếu trộn với `DEL` thì sau khi xoá, một lần set version cũ vẫn lọt vào key trống. Lease
  (module 3.2) giải quyết đúng trường hợp đó.

Cuối cùng, câu trả lời trưởng thành nhất: muốn **nhất quán mạnh** (đọc luôn thấy giá trị mới nhất) thì
cache không phải công cụ đúng. Luồng cần chính xác (thanh toán, trừ tồn kho, kiểm tra số dư) đọc thẳng
DB primary; cache chỉ dùng cho hiển thị, nơi chấp nhận cũ vài giây.

**Tóm tắt nhanh**
- Xoá rồi update: cửa sổ lỗi bằng cả transaction của bên ghi, gần như chắc chắn dính với key nóng. Tránh.
- Update rồi xoá: chỉ lỗi khi cache đang trống và lần đọc chậm hơn cả lần ghi; hiếm nhưng có, nên
  luôn có TTL.
- Xoá trong transaction chính là "xoá rồi update" trá hình; dùng `DB::afterCommit`. Nạp từ replica lag
  cũng để lại bản cũ dù code đúng thứ tự.
- Delayed double delete chỉ giảm xác suất, khoảng chờ là đoán.
- Xoá thay vì set vì xoá idempotent; ngoại lệ là `INCR` và set có điều kiện theo version.

**Nguồn**: [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala) (mục 2, 3.2.1, 4.1) ·
[Laravel: Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions) ·
[Laravel: Database, Read and Write Connections](https://laravel.com/docs/database#read-and-write-connections) ·
[Laravel source: ManagesTransactions](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Concerns/ManagesTransactions.php) ·
*Designing Data-Intensive Applications* ch.5, *Problems with Replication Lag*

---

### 2.3 Stampede, penetration, avalanche

Module này trả lời: ba cách cache làm sập DB khác nhau ở đâu, nhận ra từng cái trên dashboard thế nào,
và mỗi kỹ thuật phòng chống (mutex, coalescing, SWR, XFetch, null marker, Bloom filter, jitter) hoạt
động ra sao, trả giá gì.

#### Phân biệt ba sự cố

Cả ba có chung kết cục: rất nhiều request đi xuyên qua cache xuống DB cùng lúc. Khác nhau ở **nguyên
nhân**, nên cách chữa khác nhau:

| Sự cố | Chuyện gì xảy ra | Phạm vi | Dấu hiệu trên dashboard |
|---|---|---|---|
| Stampede (thundering herd, dog-piling) | **Một** key nóng hết hạn, hàng trăm request cùng miss, cùng chạy một query nặng | Một key | Một query giống hệt nhau tăng vọt đúng lúc key hết hạn, lặp theo chu kỳ TTL |
| Penetration | Request hỏi key **không tồn tại** trong DB, nên không bao giờ được cache, lần nào cũng xuống DB | Nhiều key "rác" | Nhiều query tìm theo id trả 0 dòng; hit ratio thấp ở một endpoint; thường đi kèm traffic bất thường (bot) |
| Avalanche | **Nhiều** key cùng hết hạn một lúc, hoặc cả cụm Redis sập hay restart | Diện rộng | Hit ratio toàn hệ thống tụt mạnh, mọi loại query DB cùng tăng |

```
Stampede:     key "homepage" hết hạn ──▶ 500 request ──▶ 500 lần cùng một query nặng
Penetration:  GET product:99999999 (không tồn tại) ──▶ miss ──▶ DB: 0 dòng ──▶ không cache ──▶ lặp lại mãi
Avalanche:    10.000 key cùng TTL 3600 tạo lúc deploy ──▶ 1 giờ sau cùng hết hạn ──▶ mọi query cùng tăng
```

#### Chống stampede

Vì sao stampede tự khuếch đại: số request cùng miss bằng **tốc độ request nhân thời gian tính lại**.
Paper XFetch lấy ví dụ: key được đọc 10 lần mỗi giây, tính lại mất 3 giây, thì 30 request cùng tính
lại. Tệ hơn, 30 query cùng chạy làm DB chậm đi, mỗi lần tính lại lâu hơn, nên càng nhiều request rơi vào
cửa sổ miss. Paper gọi đây là *cascading failure* (lỗi dây chuyền).

Code cache-aside ngây thơ (`get`, miss thì tính rồi `set`) không có gì ngăn điều này. Có sáu nhóm lời
giải.

**1. Mutex (khoá loại trừ phân tán).** Chỉ một request được tính lại, số còn lại chờ hoặc dùng bản cũ.

1. Request thấy miss thì thử lấy lock: `SET lock:homepage <token> NX PX 5000`. `NX` là chỉ set nếu key
   chưa tồn tại (nên chỉ một bên thắng), `PX 5000` là lock tự hết hạn sau 5000 ms, `<token>` là giá trị
   ngẫu nhiên riêng của người giữ.
2. Bên lấy được lock **kiểm tra lại cache** (có thể bên khác vừa nạp xong), rồi đọc DB và nạp cache.
3. Nhả lock bằng Lua "chỉ `DEL` nếu giá trị vẫn là token của mình", để không xoá nhầm lock mà bên khác
   đã lấy sau khi lock của mình hết hạn.
4. Các bên không lấy được lock: chờ ngắn rồi đọc lại cache, hoặc trả giá trị cũ nếu còn giữ.

Trong Laravel, `Cache::lock()` làm đúng các bước 1 và 3 (driver Redis dùng `SET ... EX ... NX` và nhả
lock bằng Lua so owner):

```php
<?php
declare(strict_types=1);

use Illuminate\Contracts\Cache\LockTimeoutException;
use Illuminate\Support\Facades\Cache;

function homepage(): array
{
    $key = 'homepage:v3';
    $value = Cache::get($key);
    if (is_array($value)) {
        return $value;                               // hit: đường nhanh, không đụng lock
    }

    $lock = Cache::lock("lock:{$key}", 10);          // lock tự hết hạn sau 10 giây
    try {
        $lock->block(3);                             // chờ tối đa 3 giây để lấy lock
        $value = Cache::get($key);                   // double-check: bên giữ lock trước có thể đã nạp
        if (is_array($value)) {
            return $value;
        }
        $value = buildHomepage();                    // query nặng, chỉ một request chạy
        Cache::put($key, $value, 300 + random_int(0, 30));
        return $value;
    } catch (LockTimeoutException) {
        return fallbackHomepage();                   // chờ quá lâu: trả bản rút gọn thay vì dồn xuống DB
    } finally {
        $lock->release();                            // chỉ nhả nếu mình là owner
    }
}
```

Những điểm hay bị hỏi vặn:

- ⚠️ Lock **phải có hạn**. Người giữ lock chết (OOM, deploy, timeout) mà lock không hết hạn thì không ai
  được nạp lại nữa. Paper XFetch nêu đúng điểm yếu này: mutex không chịu lỗi tốt, người giữ lock chết thì
  phải chờ lock hết hạn.
- Chọn hạn lock: dài hơn thời gian tính lại bình thường (không thì hai bên cùng tính), nhưng không quá
  dài (người giữ chết thì cả hệ thống chờ lâu).
- Các request thua phải làm gì đó: chờ (tốn worker PHP-FPM, có thể làm cạn pool), trả bản cũ (cần giữ bản
  cũ ở đâu đó, xem SWR), hoặc trả bản rút gọn. Mutex một mình, không có bản cũ, vẫn làm người dùng chờ.
- Mỗi lần miss tốn thêm một lần ghi (lấy lock) và một lần xoá (nhả lock).

**2. Request coalescing (gom request) trong một process.** Nhiều goroutine hoặc thread cùng hỏi một key
trong **cùng process** thì chỉ một cái chạy loader, số còn lại chờ và dùng chung kết quả. Không cần
Redis, không cần lock phân tán.

Go có `golang.org/x/sync/singleflight`. `Group.Do(key, fn)` trả về `(v, err, shared)`: trong lúc một
lời gọi cho `key` đang chạy, các lời gọi trùng key chờ và nhận cùng kết quả; `shared` cho biết kết quả
có được chia cho nhiều bên không. `DoChan` trả về channel thay vì chặn, `Forget(key)` bỏ theo dõi key
để lần gọi sau chạy mới.

```go
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"

	"golang.org/x/sync/singleflight" // module ngoài: go get golang.org/x/sync
)

var (
	group   singleflight.Group
	dbCalls atomic.Int32
)

func loadProduct(id string) (any, error) {
	dbCalls.Add(1)
	time.Sleep(100 * time.Millisecond) // giả lập query chậm
	return "product " + id, nil
}

func main() {
	var wg sync.WaitGroup
	for range 100 {
		wg.Add(1)
		go func() {
			defer wg.Done()
			v, _, _ := group.Do("product:1", func() (any, error) { return loadProduct("1") })
			_ = v
		}()
	}
	wg.Wait()
	// Thường in 1: 100 goroutine xuất phát gần như cùng lúc, trong khi lần load đầu còn đang chạy.
	// Không đảm bảo tuyệt đối: goroutine nào tới sau khi lần load đầu đã xong sẽ gọi load lần nữa.
	fmt.Println("số lần gọi DB:", dbCalls.Load())
}
```

Tương đương ở Java: Caffeine `LoadingCache` tự gom load cùng key, Spring `@Cacheable(sync = true)`.
⚠️ Cả hai chỉ gom trong **một process**. 50 instance app thì vẫn có tới 50 lần tính lại cùng lúc; chống
stampede giữa các instance cần mutex phân tán, SWR hoặc lease. Với PHP-FPM, mỗi request là một process
riêng không chia sẻ bộ nhớ, nên gom trong process gần như không có tác dụng (module 2.7).

**3. Stale-while-revalidate (SWR).** Mỗi mục cache có hai mốc:

```
tạo lúc t0      t0 + fresh                     t0 + fresh + stale (hết hạn cứng)
   │─── fresh ──────│────────── stale ─────────────│──── miss thật ────
   trả ngay          trả bản cũ NGAY, và một        tính lại đồng bộ,
                     request làm mới ở nền          người dùng phải chờ
```

- Trong khoảng stale, người dùng không bao giờ chờ, và DB chỉ nhận một lần làm mới (nếu có lock cho việc
  làm mới) thay vì cả đàn.
- Ý tưởng đến từ header HTTP `stale-while-revalidate` (RFC 5861, module 1.1).
- Laravel: `Cache::flexible('users', [5, 10], fn () => ...)`. Theo docs: trước giây thứ 5 trả ngay; từ
  giây 5 tới 10 trả bản cũ và đăng ký một *deferred function* làm mới **sau khi response đã gửi**; sau giây
  10 thì coi như hết hạn và tính lại ngay. Đọc source Laravel 13.x thấy thêm hai chi tiết đáng biết:
  - Việc làm mới ở nền được bọc trong một cache lock, nên chỉ một request làm mới. Tham số thứ tư
    `$lock` (mảng `seconds`, `owner`) đặt hạn cho lock đó; không truyền thì lock không có hạn, và nếu
    process làm mới chết giữa chừng thì lock kẹt lại (key vẫn tự tính lại được khi quá hạn cứng).
  - ⚠️ Khi key **hoàn toàn trống** (lần đầu, sau `cache:clear`, sau khi quá hạn cứng), `flexible` gọi
    callback trực tiếp, không có lock. Tức là SWR không chống stampede lúc cache nguội. Key cực nóng vẫn
    cần warm-up hoặc mutex cho trường hợp này.

**4. Probabilistic early expiration (XFetch).** Mỗi request tự tung đồng xu có trọng số: càng gần hết
hạn, xác suất "tôi sẽ tính lại sớm" càng cao. Không cần lock, không cần process nền. Paper Vattani,
Chierichetti, Lowenstein (VLDB 2015) chứng minh dùng phân phối mũ (exponential) là tối ưu.

Cách hoạt động, theo pseudo-code của paper:

1. Khi tính lại, đo thời gian tính `delta` và lưu cùng giá trị: `(value, delta)`, cùng với thời điểm hết
   hạn `expiry`.
2. Mỗi lần đọc, tính lại nếu:

   ```
   now - delta * beta * ln(rand()) >= expiry
   ```

   `rand()` là số ngẫu nhiên phân phối đều (paper không ghi khoảng; khi cài phải loại giá trị 0 để tránh
   `ln(0)`, nên dùng (0, 1]), `ln` là logarit tự nhiên, `beta` mặc định 1.
3. Không thoả thì trả giá trị đang có.

Vì sao nó hoạt động: `ln(rand())` luôn ≤ 0, nên `- delta * beta * ln(rand())` là một khoảng dương ngẫu
nhiên, cỡ `delta` (trung bình đúng bằng `delta * beta`). Mỗi request "giả vờ đang ở tương lai" thêm một
khoảng đó, và nếu ở tương lai ấy key đã hết hạn thì nó tính lại ngay bây giờ. Xa hạn thì gần như không
ai vượt ngưỡng; sát hạn thì khả năng cao có **một** request vượt ngưỡng trước những request khác, tính
lại, đẩy `expiry` ra xa, và cả đàn không bao giờ thấy miss.

- `delta` làm khoảng "nhìn trước" tỉ lệ với chi phí tính: key tính mất 10 giây được làm mới sớm hơn key
  tính mất 10 ms.
- `beta > 1`: làm mới sớm hơn, ít stampede hơn. Paper cho thấy tăng `beta` lên 1.5 đã kéo stampede
  trung bình xuống dưới 2 trong thí nghiệm của họ.
- Số liệu thật trong paper (dữ liệu một tuần từ Goodreads, key tính lại mất khoảng 10 giây): với
  `beta = 1`, phần lớn "stampede" chỉ có kích thước 1 (tức là không có stampede) hoặc 2, không lần nào
  vượt quá 8. Phân phối đều (cách thư viện CHI của Perl dùng) cho stampede trung bình gần 10, đôi khi 20
  trở lên.
- Nhược điểm: vẫn có thể có vài request cùng tính lại (xác suất thấp, không phải bằng 0), và nếu key
  hiếm khi được đọc thì không có ai "tung đồng xu" để làm mới sớm; khi đó nó hết hạn như thường. Với key
  ít đọc thì stampede cũng không phải vấn đề.

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\Cache;

/**
 * XFetch: làm mới sớm theo xác suất. Payload lưu [giá trị, delta (giây), expiry (unix time)].
 *
 * @param \Closure(): mixed $recompute
 */
function xfetch(string $key, int $ttl, \Closure $recompute, float $beta = 1.0): mixed
{
    $payload = Cache::get($key);
    $now = microtime(true);

    if (is_array($payload)) {
        [$value, $delta, $expiry] = $payload;
        // rand trong (0, 1]: tránh ln(0) = -INF
        $rand = random_int(1, PHP_INT_MAX) / PHP_INT_MAX;
        if ($now - $delta * $beta * log($rand) < $expiry) {
            return $value;                   // chưa tới lượt: dùng giá trị đang có
        }
    }

    $start = hrtime(true);
    $value = $recompute();
    $delta = (hrtime(true) - $start) / 1e9;  // thời gian tính lại, giây

    // TTL thật của Redis dài hơn expiry logic một chút để lần đọc sát hạn vẫn thấy payload
    Cache::put($key, [$value, $delta, $now + $ttl], $ttl + (int) ceil($delta) + 1);
    return $value;
}
```

**5. Lease (Facebook).** Memcache của Facebook dùng *lease*: cache chỉ cấp "quyền nạp lại" (lease token)
cho mỗi key tối đa một lần mỗi 10 giây (cấu hình mặc định của họ); request khác trong 10 giây đó nhận
thông báo "chờ một chút rồi thử lại", và thường khi thử lại thì bên giữ token đã nạp xong trong vài mili
giây. Kết hợp với việc trả **giá trị cũ** vừa bị xoá (lưu tạm một thời gian ngắn) cho ứng dụng chấp
nhận được dữ liệu hơi cũ. Paper đo trên một nhóm key dễ bị stampede trong một tuần: đỉnh query DB giảm từ
17K/s xuống 1.3K/s. Cơ chế đầy đủ và cách mô phỏng trên Redis: module 3.2.

**6. Key cực nóng: không để nó hết hạn.** Trang chủ, cấu hình toàn cục, bảng giá flash sale: đặt TTL dài
(hoặc không TTL) và cho một job định kỳ tính lại rồi ghi đè (refresh-ahead theo lịch, module 2.1). Paper
XFetch gọi là *external re-computation*: chặn stampede hoàn toàn, đổi lại phải vận hành thêm một process
và biết trước key nào cần làm mới.

| Cách | Phạm vi | Người dùng có chờ không | Cần thêm gì | Điểm yếu |
|---|---|---|---|---|
| Mutex | Mọi instance | Bên thua chờ hoặc nhận bản cũ | Lock phân tán | Người giữ chết thì chờ hết hạn lock |
| Coalescing | Một process | Chờ bên đang load | Không | Không chống được giữa các instance |
| SWR | Mọi instance | Không, trong khoảng stale | Lưu thời điểm tạo | Cache nguội vẫn stampede |
| XFetch | Mọi instance | Gần như không | Lưu `delta`, `expiry` | Xác suất, không tuyệt đối |
| Lease | Mọi instance | Chờ ngắn | Cache hỗ trợ token | Redis không có sẵn |
| Job làm mới | Key đã biết | Không | Process nền | Phải biết trước key nóng |

#### Chống penetration

Gốc của penetration là bẫy `null` ở module 1.2: kết quả "không tồn tại" không được cache, nên mỗi lần
hỏi lại là một lần xuống DB. Kẻ tấn công (hoặc một bug gọi sai id) chỉ cần gửi id ngẫu nhiên là vượt
qua cache hoàn toàn.

**Null marker.** Cache luôn kết quả "không tồn tại" bằng một giá trị đặc biệt, với TTL ngắn:

```php
<?php
declare(strict_types=1);

use App\Models\Product;
use Illuminate\Support\Facades\Cache;

const NOT_FOUND = '__not_found__';

function findProduct(int $id): ?array
{
    $key = "product:{$id}:v1";
    $cached = Cache::get($key);
    if ($cached === NOT_FOUND) {
        return null;                     // đã biết là không có: không xuống DB
    }
    if (is_array($cached)) {
        return $cached;
    }

    $row = Product::query()->find($id)?->only(['id', 'name', 'price']);
    // Có: TTL bình thường. Không có: TTL ngắn, đủ để chặn một đợt dội
    Cache::put($key, $row ?? NOT_FOUND, $row === null ? 60 : 600);
    return $row;
}
```

- Vì sao không lưu thẳng `null`: `Cache::remember` và `Cache::get` của Laravel coi `null` là miss (trong
  source, `remember` chỉ trả giá trị cache khi nó khác `null`), nên cache `null` không chặn được gì. Phải
  dùng giá trị đặc biệt phân biệt được.
- ⚠️ Khi bản ghi đó được **tạo** (ví dụ id được cấp trước, hoặc slug), phải xoá marker, sau commit.
  Không thì bản ghi mới bị báo "không tồn tại" tới hết TTL của marker. TTL ngắn là để giới hạn thiệt hại
  khi quên.
- ⚠️ Null marker không đủ trước tấn công dùng **id khác nhau mỗi lần**: mỗi id vẫn xuống DB một lần, và
  cache đầy marker rác (đẩy key thật ra ngoài khi bị evict). Cần thêm hai lớp dưới.

**Bloom filter.** Một cấu trúc dữ liệu chứa "tập mọi id hợp lệ" ở dạng rất gọn, trả lời một trong hai:
**chắc chắn không có**, hoặc **có thể có**. Kiểm tra nó trước khi xuống DB; "chắc chắn không có" thì trả
404 ngay.

Cách hoạt động:

1. Một mảng `m` bit, ban đầu toàn 0, và `k` hàm hash khác nhau.
2. Thêm phần tử `x`: tính `k` hash của `x`, bật `k` bit ở các vị trí đó thành 1.
3. Kiểm tra `y`: tính `k` hash của `y`. Có **bất kỳ** bit nào bằng 0 thì `y` chắc chắn chưa từng được
   thêm. Tất cả bằng 1 thì "có thể có".

```
m = 16 bit, k = 3
thêm "p:1"  → hash ra vị trí 2, 7, 11   bits: 0010000100010000
thêm "p:2"  → hash ra vị trí 4, 7, 13        0010100100010100
kiểm "p:9"  → vị trí 2, 4, 9: bit 9 = 0 ⇒ CHẮC CHẮN không có
kiểm "p:5"  → vị trí 2, 4, 13: đều = 1  ⇒ "có thể có" (thật ra không có: false positive)
```

- **Không có false negative**: bit chỉ được bật lên, không bao giờ tắt. Phần tử đã thêm thì `k` bit của
  nó đã là 1 và mãi là 1, nên kiểm tra lại luôn ra "có thể có".
- **Có false positive**: các bit của `y` có thể đã bị các phần tử **khác** bật hết (như `p:5` ở trên). Hậu
  quả chỉ là một lần xuống DB thừa, chấp nhận được.
- **Không xoá được**: tắt một bit có thể làm hỏng phần tử khác dùng chung bit đó, sinh ra false negative.
  Biến thể *counting Bloom filter* thay mỗi bit bằng một bộ đếm để xoá được, tốn bộ nhớ hơn. Thực tế
  thường chấp nhận id đã xoá vẫn "có thể có" (rơi vào null marker), và định kỳ dựng lại filter.
- Gọn thế nào: với cấu hình tối ưu, khoảng 9,6 bit cho mỗi phần tử cho tỉ lệ false positive khoảng 1%,
  không phụ thuộc id dài hay ngắn. 10 triệu id cần cỡ 12 MB.
- Ở đâu: Redis 8 có sẵn nhóm lệnh `BF.ADD`, `BF.EXISTS` (trước đó cần module RedisBloom hoặc Redis Stack);
  Valkey dùng module riêng, kiểm tra docs. Cũng có thể giữ filter trong bộ nhớ app. Chi tiết cấu trúc:
  [21-dsa.md](../21-dsa.md).
- ⚠️ Filter phải được cập nhật khi tạo bản ghi mới (thêm id vào filter **trước hoặc cùng lúc** với khi id
  có thể được đọc), không thì bản ghi mới bị báo "chắc chắn không có", tức là chính filter tạo ra false
  negative ở tầng ứng dụng.

**Chặn sớm từ đầu vào.**
- Validate định dạng: id âm, id vượt quá giá trị lớn nhất đang có, UUID sai định dạng thì trả lỗi ngay,
  không chạm cache hay DB.
- Rate limit theo IP hoặc user cho endpoint tra cứu.
- Dùng id công khai khó đoán (UUID, id ngẫu nhiên) thay vì số tự tăng để giảm bề mặt quét.

#### Chống avalanche

Hai nguyên nhân thường gặp:

1. **Nhiều key cùng hết hạn**: deploy xong, hoặc một job warm-up nạp 10.000 key trong một phút, tất cả
   TTL cố định 3600 giây. Đúng một giờ sau, tất cả hết hạn trong cùng một phút.
2. **Cả cụm cache mất**: Redis sập, restart không có persistence, failover, hoặc ai đó chạy
   `cache:clear` trên production (module 2.7). Hit ratio rơi từ 95% về 0%, DB nhận gấp 20 lần tải đọc
   (module 3.3).

Cách phòng, theo từng nguyên nhân:

- **Jitter cho TTL** (module 1.2): AWS đưa ví dụ `ttl = 3600 + (rand() * 120)`, rải thời điểm hết hạn
  ra hai phút thay vì một khoảnh khắc. Trong PHP: `3600 + random_int(0, 120)`. Cũng áp dụng cho thời
  điểm warm-up.
- **Redis HA** (replica + Sentinel, hoặc Cluster): một node chết không mất cả cache (module 3.3).
- **Bảo vệ DB khi cache mất**: timeout ngắn cho Redis, *circuit breaker* (cơ chế tạm ngừng gọi một phụ
  thuộc đang lỗi liên tục, để nó có thời gian hồi phục và không dồn thêm tải), rate limit số query nạp
  cache xuống DB.
- **L1 cache làm đệm** (module 3.1): mất Redis thì L1 trên từng instance vẫn đỡ được key nóng nhất vài
  giây.
- **Degrade**: tạm tắt tính năng phụ (gợi ý, bộ đếm, "người khác cũng xem") để dành DB cho luồng chính
  (xem sản phẩm, đặt hàng).
- ⚠️ **Cold start**: Redis restart mà không có persistence thì cache trống hoàn toàn. Warm-up dần các key
  nóng trước, và mở traffic từ từ (theo phần trăm, hoặc theo từng instance), không bật 100% ngay. AWS gợi
  ý chạy script mô phỏng request thật để làm ấm node cache mới trước khi đưa vào dùng.

Stampede, penetration, avalanche thường đi cùng nhau: avalanche làm mọi key nóng cùng miss, tức là hàng
trăm stampede cùng lúc. Vì vậy hệ thống phòng tốt cả ba thường có đủ: jitter, một cơ chế chống stampede
cho key nóng (SWR hoặc mutex), null marker, và giới hạn tải xuống DB.

**Tóm tắt nhanh**
- Stampede là một key nóng hết hạn; penetration là key không tồn tại nên không bao giờ được cache;
  avalanche là nhiều key hoặc cả cụm cùng mất.
- Chống stampede: mutex có hạn (kèm double-check), coalescing chỉ trong một process, SWR (`flexible`,
  nhưng cache nguội vẫn stampede), XFetch làm mới sớm theo xác suất, lease, job làm mới key cực nóng.
- XFetch: tính lại nếu `now - delta * beta * ln(rand()) >= expiry`; `delta` là thời gian tính lại.
- Chống penetration: null marker TTL ngắn (không dùng `null` trong Laravel), Bloom filter (không false
  negative vì bit chỉ bật không tắt), validate và rate limit.
- Chống avalanche: jitter, Redis HA, circuit breaker và rate limit bảo vệ DB, L1, warm-up dần.

**Nguồn**: [Vattani, Chierichetti, Lowenstein: Optimal Probabilistic Cache Stampede Prevention](https://cseweb.ucsd.edu/~avattani/papers/cache_stampede.pdf) (VLDB 2015, mục 1, 2, 5, 6) ·
[Go: singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight) ·
[Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala) (mục 3.2.1) ·
[Laravel: Cache](https://laravel.com/docs/cache) (Stale While Revalidate, Atomic Locks, Store if Not Present) ·
[Laravel source: Cache Repository](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Cache/Repository.php) ·
[AWS: Caching best practices](https://aws.amazon.com/caching/best-practices/)

---

### 2.4 Hot key, big key và Redis làm cache

Module này trả lời: vì sao một cụm Redis nhiều node vẫn có thể chết vì đúng một key, vì sao một
lệnh xoá có thể làm mọi client khác đứng hình, và cấu hình nào quyết định Redis vứt bỏ key nào khi
đầy bộ nhớ. Chi tiết về bản thân Redis (mô hình thực thi, persistence, Cluster) nằm ở plan
[04-nosql-search-storage.md](../04-nosql-search-storage.md); ở đây chỉ nhìn từ góc cache.

#### Hot key

*Hot key* là một key nhận lượng đọc lớn bất thường so với phần còn lại: sản phẩm đang flash sale,
cấu hình toàn cục, bài viết đang viral, trang chủ.

Vì sao nguy hiểm ngay cả khi có Redis Cluster:

1. Redis Cluster chia keyspace thành 16384 *hash slot*; mỗi key được băm (CRC16) vào đúng một slot,
   mỗi slot thuộc đúng một node primary.
2. Vậy mọi lệnh tới `product:1` đều rơi vào **cùng một node**, bất kể cụm có 3 hay 30 node.
3. Redis thực thi lệnh trên một thread chính (xem [Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/):
   Redis "mostly single threaded", mọi request được phục vụ tuần tự). Node đó bão hoà một core CPU
   hoặc băng thông mạng, latency tăng cho **mọi key khác** trên node, không chỉ key nóng.

Thêm node không giải quyết được hot key: scale ngang chỉ giúp khi tải rải đều trên nhiều key.

Ba cách xử lý, mỗi cách trả giá bằng độ cũ khác nhau:

| Cách | Làm gì | Cái giá |
|---|---|---|
| L1 cache trong app | Mỗi instance app giữ bản sao trong RAM với TTL rất ngắn (vài giây), phần lớn request không tới Redis | Mỗi instance cũ tối đa bằng TTL của L1; PHP-FPM không có L1 in-process, phải dùng APCu (module 2.7, 3.1) |
| Nhân bản key | Lưu N bản `product:1#0` .. `product:1#N-1`, đọc chọn ngẫu nhiên một bản, ghi cập nhật tất cả | Ghi tốn N lần; trong lúc cập nhật, các bản có thể lệch nhau một chút |
| Đọc từ replica | Cho client đọc key nóng từ replica của shard đó | Replication của Redis là bất đồng bộ, replica có thể trễ; chỉ nhân năng lực đọc của đúng shard đó theo số replica |

Nhân bản key hoạt động vì tên key khác nhau thì băm vào slot khác nhau, nên các bản rải ra nhiều
node. ⚠️ Nếu tên key có *hash tag* (phần trong `{...}`, ví dụ `product:{1}#2`), Cluster chỉ băm
phần trong ngoặc, nên mọi bản rơi về **cùng một slot** và việc nhân bản vô nghĩa.

```php
<?php
declare(strict_types=1);

// Minh hoạ nhân bản hot key với phpredis. N bản, đọc ngẫu nhiên, ghi tất cả.
const REPLICAS = 8;

function readHot(Redis $redis, string $key): string|false
{
    $i = random_int(0, REPLICAS - 1);
    return $redis->get("{$key}#{$i}");       // false nếu miss
}

function writeHot(Redis $redis, string $key, string $value, int $ttl): void
{
    for ($i = 0; $i < REPLICAS; $i++) {
        // jitter nhỏ để N bản không cùng hết hạn một lúc (tránh stampede, module 2.3)
        $redis->setex("{$key}#{$i}", $ttl + random_int(0, 5), $value);
    }
}
```

Phát hiện hot key:

- `redis-cli --hotkeys`: quét keyspace bằng `SCAN` và đọc tần suất truy cập của từng key. Theo
  docs redis-cli, tuỳ chọn này "only works when maxmemory-policy is *lfu", vì chỉ ở chế độ LFU
  Redis mới duy trì bộ đếm tần suất cho mỗi key. Instance đang chạy `allkeys-lru` thì không dùng
  được.
- Metric phía client: đếm số lệnh theo tiền tố key trong app, hoặc theo dõi CPU từng node (một node
  CPU cao bất thường trong khi các node khác rảnh là dấu hiệu hot key).
- ⚠️ `MONITOR` in mọi lệnh server nhận được, tiện để soi nhanh, nhưng tốn tài nguyên đáng kể; chỉ
  bật vài giây trên production.

#### Big key

*Big key* là key mà value quá lớn: một string vài MB, hoặc hash/list/set/zset có hàng trăm nghìn
tới hàng triệu phần tử. Không có ngưỡng chính thức; ngưỡng là do đội tự đặt.

Tác hại:

- **Chặn cả server**. Lệnh chạy trên tập nhiều phần tử có độ phức tạp O(N) (`HGETALL`, `SMEMBERS`,
  `LRANGE 0 -1`, `DEL` một key lớn). Vì thread chính chạy tuần tự, trong lúc lệnh đó chạy mọi
  client khác phải chờ. Docs latency của Redis nhấn mạnh: kiểm tra độ phức tạp của lệnh trước khi
  dùng, và chạy lệnh chậm trên replica nếu bắt buộc.
- **Tốn băng thông mạng**: đọc một value 5 MB cho mỗi request làm card mạng của node bão hoà trước
  CPU.
- **Lệch bộ nhớ** giữa các node Cluster: một key không chia được qua nhiều slot, nên node chứa nó
  đầy trước.
- Làm chậm replication và migrate slot khi resharding (key phải chuyển nguyên khối).

Cách xử lý:

- **Chia nhỏ**: thay một hash `user:1:feed` chứa triệu phần tử bằng nhiều hash theo bucket
  (`user:1:feed:0` .. `user:1:feed:99`, chọn bucket bằng hash của field).
- **Nén** value lớn ở phía client (phpredis có compression riêng, module 2.7).
- **Chỉ lấy phần cần**: `HGET`/`HMGET` thay `HGETALL`; duyệt dần bằng `HSCAN`/`SSCAN`/`ZSCAN`
  thay vì lấy toàn bộ một lần.
- **Xoá bằng `UNLINK`** thay `DEL`. Theo docs, `UNLINK` (có từ Redis 4.0) gỡ key khỏi keyspace
  trong O(1) rồi giải phóng bộ nhớ ở một thread khác, nên không chặn; `DEL` giải phóng ngay trên
  thread chính, với key lớn là O(số phần tử).

Phát hiện big key:

| Công cụ | Đo gì |
|---|---|
| `redis-cli --bigkeys` | Quét bằng `SCAN`, báo key có **nhiều phần tử nhất** theo từng kiểu (đếm phần tử, riêng string thì tính độ dài; không phải bộ nhớ thật) |
| `redis-cli --memkeys` | Như trên nhưng xếp theo **bộ nhớ** (byte) |
| `redis-cli --keystats` | Gộp cả hai, kèm phân bố kích thước và top N key (mặc định 10) |
| `MEMORY USAGE key [SAMPLES n]` | Số byte một key chiếm trong RAM, gồm cả overhead. Với kiểu lồng nhau, mặc định lấy mẫu 5 phần tử rồi ngoại suy; `SAMPLES 0` đếm hết |

Các lệnh quét dùng `SCAN` nên không chặn server như `KEYS *`; thêm `-i 0.01` để nghỉ 0,01 giây sau mỗi
100 lệnh `SCAN`, giảm tải lên instance production.

#### `maxmemory-policy`

`maxmemory` là giới hạn bộ nhớ cho dữ liệu. Mỗi khi client chạy lệnh thêm dữ liệu, Redis kiểm tra
bộ nhớ; nếu vượt giới hạn thì *evict* (bỏ) key theo policy cho tới khi xuống dưới. Mặc định
`maxmemory 0` (không giới hạn) trên hệ 64-bit, còn 32-bit ngầm giới hạn 3 GB. Nghĩa là Redis dùng
làm cache mà quên đặt `maxmemory` sẽ ăn RAM tới khi bị OS kill hoặc swap.

Các policy (theo docs Redis hiện tại):

| Policy | Bỏ key nào |
|---|---|
| `noeviction` | Không bỏ gì; lệnh thêm dữ liệu trả lỗi, lệnh đọc vẫn chạy. Đây là giá trị mặc định |
| `allkeys-lru` | Key lâu nhất chưa được dùng, trong mọi key |
| `allkeys-lfu` | Key ít được dùng nhất (tần suất), trong mọi key |
| `allkeys-random` | Ngẫu nhiên trong mọi key |
| `volatile-lru` / `volatile-lfu` / `volatile-random` | Như trên, nhưng chỉ trong các key **có TTL** |
| `volatile-ttl` | Key có TTL còn lại ngắn nhất |
| `allkeys-lrm` / `volatile-lrm` | *Least recently modified*: như LRU nhưng chỉ tính lần **ghi**, không tính lần đọc (có từ Redis 8.6) |

Chi tiết cần nhớ:

- ⚠️ Dịch vụ managed có thể đặt mặc định khác Redis tự cài. Ví dụ theo AWS, ElastiCache for Redis
  mặc định `volatile-lru`: cache nào quên đặt TTL thì không bao giờ bị evict. Luôn kiểm tra
  `CONFIG GET maxmemory-policy` (hoặc parameter group) thay vì đoán.
- ⚠️ Các policy `volatile-*` cư xử như `noeviction` nếu không có key nào có TTL: đầy là lỗi ghi.
- Lời khuyên của docs: không có lý do đặc biệt thì `allkeys-lru` là mặc định tốt (phần nhỏ key nhận
  phần lớn truy cập, kiểu Pareto). `allkeys-random` hợp khi mọi key được truy cập đều nhau.
- LRU của Redis là **xấp xỉ**: lấy mẫu ngẫu nhiên vài key rồi bỏ key có thời gian nhàn rỗi lâu nhất
  (từ Redis 3.0 còn giữ thêm một pool ứng viên tốt). Số mẫu chỉnh bằng `maxmemory-samples` (mặc
  định 5; đặt 10 gần LRU thật hơn, tốn thêm CPU). Không làm LRU chính xác vì tốn bộ nhớ cho mỗi key.
- LFU (có từ Redis 4.0) dùng bộ đếm xác suất (*Morris counter*) chỉ vài bit mỗi key, có *decay*
  (giảm dần theo thời gian) để key từng nóng nhưng nay nguội vẫn bị bỏ. Tham số: `lfu-log-factor`
  (mặc định 10, bão hoà quanh một triệu lượt truy cập) và `lfu-decay-time` (mặc định 1 phút).
  Chi tiết LRU/LFU ở module 1.3.
- Khi có replication hoặc AOF, bộ đệm replication/AOF không bị tính vào `maxmemory`; docs khuyên để
  dư một ít RAM cho các bộ đệm này (xem `mem_not_counted_for_evict` trong `INFO memory`).
- Kiểm tra policy có hợp không bằng `INFO stats`: hit ratio =
  `keyspace_hits / (keyspace_hits + keyspace_misses)`, kèm `evicted_keys` (bị evict nhiều mà hit
  ratio thấp là policy hoặc `maxmemory` không hợp) và `expired_keys` (hết hạn nhiều là TTL quá
  ngắn).

⚠️ Cạm bẫy hay gặp nhất: một instance vừa làm cache vừa chứa session hoặc queue.

- Policy `allkeys-*`: khi đầy, Redis evict cả job trong queue và session. Job biến mất không lỗi,
  người dùng bị đăng xuất ngẫu nhiên.
- Policy `noeviction`: cache đầy thì mọi lệnh ghi lỗi, kể cả ghi job vào queue.
- `volatile-*` là thoả hiệp (chỉ bỏ key có TTL, nên cache phải luôn có TTL, dữ liệu bền thì không
  có). Docs gọi đây là trường hợp dùng chính của `volatile-*`, nhưng cũng khuyên nên chạy hai
  instance tách biệt nếu được.

Cách đúng: tách instance. Instance cache dùng `allkeys-lru` hoặc `allkeys-lfu`; instance cho
session/queue dùng `noeviction` và được giám sát bộ nhớ. Tách DB số (`SELECT 1`) **không** đủ:
`maxmemory` và policy áp cho cả instance, không theo từng DB.

```sh
# Instance cache
redis-cli -p 6379 CONFIG SET maxmemory 2gb
redis-cli -p 6379 CONFIG SET maxmemory-policy allkeys-lfu
# Instance session/queue
redis-cli -p 6380 CONFIG SET maxmemory-policy noeviction
redis-cli -p 6379 INFO stats | grep -E 'keyspace_(hits|misses)|evicted_keys|expired_keys'
```

#### TTL theo field của hash

`HEXPIRE` (có từ Redis 7.4.0) đặt TTL cho **từng field** trong một hash; field hết hạn tự bị xoá
khỏi hash. Họ lệnh đi kèm: `HPEXPIRE` (mili giây), `HEXPIREAT`/`HPEXPIREAT` (mốc thời gian tuyệt
đối), `HTTL`/`HPTTL` (xem TTL còn lại), `HPERSIST` (bỏ TTL). Valkey hỗ trợ từ 9.0 với API tương
thích (kèm `HSETEX`, `HGETEX`, `HEXPIRETIME`).

```
> HSET user:1:cache profile "..." cart "..."
(integer) 2
> HEXPIRE user:1:cache 60 FIELDS 1 cart
1) (integer) 1
> HTTL user:1:cache FIELDS 2 cart profile
1) (integer) 60
2) (integer) -1
```

(Output minh hoạ theo mô tả trong docs, không phải chạy thật.) Mã trả về theo từng field của
`HEXPIRE`: `1` đã đặt, `0` điều kiện `NX`/`XX`/`GT`/`LT` không thoả, `-2` field hoặc key không tồn
tại, `2` khi TTL bằng 0 (field bị xoá luôn). Với `HTTL`, `-1` là field không có TTL.

Vì sao hữu ích cho cache: trước đây muốn nhiều mục cache nhỏ của một user hết hạn riêng thì phải
tách thành nhiều key (tốn overhead mỗi key, khó xoá cả nhóm). Giờ gom vào một hash, xoá cả user
bằng một `UNLINK`, mà mỗi mục vẫn hết hạn riêng.

⚠️ TTL của field chỉ bị xoá bởi lệnh ghi đè hoặc xoá field (`HSET`, `HDEL`); lệnh sửa giá trị tại
chỗ giữ nguyên TTL. Mỗi field có TTL tốn thêm bộ nhớ (blog Valkey đo khoảng 16 tới 29 byte mỗi
field ở bản cài của Valkey). Và hash càng nhiều field càng dễ thành big key.

#### Redis hay Valkey

| Mốc | Chuyện gì xảy ra |
|---|---|
| Redis 7.2 trở về trước | License BSD-3-Clause |
| 03/2024, Redis 7.4 | Redis Ltd. chuyển sang RSALv2 hoặc SSPLv1 (không phải license nguồn mở được OSI công nhận) |
| 2024 | Linux Foundation lập **Valkey**, fork từ nhánh Redis 7.2 còn BSD |
| 2025, Redis 8.0 | Thêm lựa chọn AGPLv3 (license nguồn mở), người dùng chọn một trong ba |

Với vai trò cache, lệnh và giao thức hai bên gần như giống nhau; client phpredis/Predis dùng được
cho cả hai. Chọn theo dịch vụ managed có sẵn (một số cloud lớn đã có bản managed Valkey), yêu cầu pháp lý
về license, và tính năng riêng cần dùng. So sánh sâu hơn ở
[04-nosql-search-storage.md](../04-nosql-search-storage.md) module 3.2.

**Tóm tắt nhanh**
- Hot key dồn tải vào một node vì mỗi key nằm ở đúng một slot; thêm node không cứu được. Xử lý bằng
  L1 TTL ngắn, nhân bản key (cẩn thận hash tag), hoặc đọc replica, mỗi cách một kiểu độ cũ.
- Big key chặn thread chính: chia nhỏ, `HSCAN` thay `HGETALL`, `UNLINK` thay `DEL`. Tìm bằng
  `--bigkeys` (số phần tử), `--memkeys`/`MEMORY USAGE` (byte).
- `maxmemory` mặc định 0 trên 64-bit, `maxmemory-policy` mặc định `noeviction`. Cache nên dùng
  `allkeys-lru`/`allkeys-lfu`.
- Không để cache chung instance với session/queue: tách instance, không chỉ tách DB số.
- `--hotkeys` chỉ chạy khi policy là LFU. `HEXPIRE` (Redis 7.4+, Valkey 9.0+) cho TTL từng field.

**Nguồn**: [Redis: Key eviction](https://redis.io/docs/latest/develop/reference/eviction/) ·
[Redis: HEXPIRE](https://redis.io/docs/latest/commands/hexpire/) ·
[Redis: Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/) ·
[Redis: redis-cli](https://redis.io/docs/latest/develop/tools/cli/) ·
[Redis: UNLINK](https://redis.io/docs/latest/commands/unlink/) ·
[Redis: MEMORY USAGE](https://redis.io/docs/latest/commands/memory-usage/) ·
[Valkey: Introducing Hash Field Expirations](https://valkey.io/blog/hash-fields-expiration/) ·
[Redis licenses](https://redis.io/legal/licenses/)


---

### 2.5 Vận hành cache

Module này trả lời: những gì làm cache gây sự cố khi đã chạy thật (format lưu trữ, tên key, số
round-trip, deploy), đo cache bằng chỉ số nào, và khi nào quyết định đúng là **không** cache. Phần
lớn sự cố cache ngoài đời đến từ các chỗ này chứ không từ thuật toán.

#### Serialization và version

*Serialization* là biến object trong bộ nhớ thành chuỗi byte để lưu vào cache; *deserialization*
là chiều ngược lại khi đọc. Cache chỉ lưu byte, nên mọi thứ bạn cache đều đi qua bước này hai lần.

| Cách | Ưu | Nhược |
|---|---|---|
| JSON | Đọc được bằng mắt (`redis-cli GET` là hiểu), mọi ngôn ngữ đọc được | To hơn, chậm hơn; mất kiểu (object thành mảng, `DateTime` thành chuỗi) |
| igbinary, msgpack | Thường nhỏ hơn và nhanh hơn JSON/`serialize` | Không đọc bằng mắt; trong PHP thường cần cài extension riêng |
| Native (PHP `serialize`, Java serialization) | Tiện: lưu và khôi phục nguyên object | Gắn chặt với tên class và cấu trúc field |

⚠️ Hai vấn đề của native serialization:

1. **Gắn với class**. Đổi tên class, namespace hay kiểu property là bản cache cũ đọc ra lỗi hoặc ra
   object sai. Deploy kiểu rolling (code cũ và mới chạy song song vài phút) làm chuyện này tệ hơn:
   code mới ghi, code cũ đọc, và ngược lại.
2. **Bảo mật**. PHP manual cảnh báo không truyền dữ liệu không tin cậy vào `unserialize()`: chuỗi
   độc có thể tạo object tuỳ ý và kích hoạt magic method (*object injection*). Nếu ai đó ghi được
   vào Redis (Redis không mật khẩu, lộ ra mạng), cache thành đường tấn công. Có thể giới hạn bằng
   tuỳ chọn `allowed_classes` của `unserialize`, hoặc chỉ cache mảng/JSON.

Nén (gzip, lz4, zstd) value lớn khi băng thông mạng là nút thắt, đổi lại tốn CPU ở app. Value nhỏ
thì không đáng nén.

Đổi cấu trúc dữ liệu thì **đổi version trong tên key**, không cố đọc cả hai format:

```
user:123:v1   <- code cũ ghi và đọc
user:123:v2   <- code mới ghi và đọc
```

- Deploy mới chỉ đọc `v2`: lúc đầu miss hết (nên tính trước tải lên DB, xem nhóm Warming), nhưng
  không bao giờ vấp format cũ.
- Rollback thì code cũ vẫn đọc `v1`, bản đó còn nguyên nếu chưa hết TTL.
- Key `v1` không ai đọc nữa sẽ tự hết hạn theo TTL hoặc bị evict. Đây là lý do mọi key cache nên có
  TTL.

#### Đặt tên key

Mẫu thường dùng: `{app}:{env}:{entity}:{id}:{version}`, ví dụ `shop:prod:product:42:v3`. Dấu `:`
chỉ là quy ước, Redis không hiểu cấu trúc; nhưng giữ nhất quán giúp đọc `--bigkeys`, đếm theo tiền
tố, và phân quyền ACL theo pattern.

Quy tắc quan trọng nhất: **key phải chứa mọi thứ làm kết quả khác nhau**. Hỏi: "hai request nào ra
kết quả khác nhau?", mỗi yếu tố đó phải nằm trong key.

- Tenant, user (nếu dữ liệu cá nhân), locale/ngôn ngữ, tiền tệ, vai trò/quyền, tham số query, trang
  và kích thước trang.
- ⚠️ Thiếu `tenant_id` hay `user_id` là **lộ dữ liệu chéo**: tenant B thấy danh sách đơn của tenant
  A, vì request của A nạp cache trước. Đây là sự cố bảo mật, không phải bug hiển thị.
- ⚠️ Thiếu locale thì người dùng tiếng Anh thấy trang tiếng Việt. Thiếu quyền thì user thường thấy
  bản đã nạp bởi admin, kèm các trường chỉ admin được xem.
- Input dài hoặc tuỳ ý (câu search, bộ lọc JSON) thì băm: `search:{sha1(chuẩn hoá(query))}`. Chuẩn
  hoá trước khi băm (sắp xếp tham số, trim, lowercase nếu hợp lý), nếu không thì cùng một truy vấn
  sinh nhiều key.

```php
<?php
declare(strict_types=1);

// Mọi yếu tố làm kết quả khác nhau đều vào key. Thiếu tenant là lộ dữ liệu chéo.
function searchKey(string $tenantId, string $locale, array $filters, int $page): string
{
    ksort($filters);                                   // cùng bộ lọc, khác thứ tự -> cùng key
    $hash = sha1(json_encode($filters, JSON_THROW_ON_ERROR));
    return "shop:prod:t{$tenantId}:{$locale}:search:{$hash}:p{$page}:v1";
}

echo searchKey('7', 'vi', ['color' => 'red', 'brand' => 'x'], 1), PHP_EOL;
echo searchKey('7', 'vi', ['brand' => 'x', 'color' => 'red'], 1), PHP_EOL; // in ra giống dòng trên
```

⚠️ Không dùng `KEYS pattern*` để tìm rồi xoá theo tiền tố trên production. `KEYS` duyệt toàn bộ
keyspace trong một lệnh và chặn server suốt thời gian đó (docs latency của Redis gọi đây là nguồn
latency "VERY common", chỉ nên dùng khi debug). `SCAN` không chặn nhưng vẫn phải đi qua toàn bộ
keyspace theo từng lượt, chậm với hàng chục triệu key. Muốn invalidate cả nhóm thì thiết kế từ đầu:
versioned key (tăng một số version, module 2.2) hoặc cache tag.

#### Cache danh sách và số đếm

Cache nguyên danh sách object (`category:5:products` chứa 50 sản phẩm đầy đủ) có vấn đề: sửa một
sản phẩm thì phải tìm và xoá mọi danh sách chứa nó, việc gần như không làm đúng được.

Cách thường dùng là tách hai tầng:

1. Cache **danh sách id** với TTL ngắn, hoặc versioned theo nhóm: `category:5:ids:v{n}`.
2. Cache từng object theo id: `product:{id}`.
3. Khi đọc: lấy danh sách id, rồi lấy chi tiết mọi id bằng **một** lệnh `MGET`. Id nào miss thì nạp
   bằng một query `WHERE id IN (...)` và ghi lại.

Sửa sản phẩm 42 chỉ cần xoá `product:42`; các danh sách chứa nó tự thấy bản mới ở lần đọc sau.
Danh sách id chỉ cần đổi khi thành phần danh sách đổi (thêm, bớt, đổi thứ tự), và TTL ngắn giới hạn
độ cũ của phần đó.

```php
<?php
declare(strict_types=1);

/**
 * Lấy chi tiết nhiều sản phẩm: một round-trip MGET, phần miss nạp bằng một query IN.
 * @param list<int> $ids
 * @return list<array<string, mixed>> giữ đúng thứ tự $ids
 */
function productsByIds(Redis $redis, PDO $db, array $ids): array
{
    if ($ids === []) {
        return [];
    }
    $keys = array_map(static fn (int $id): string => "shop:prod:product:{$id}:v1", $ids);
    $raw = $redis->mget($keys);          // phpredis trả false cho key không có

    $found = [];
    $missing = [];
    foreach ($ids as $i => $id) {
        if ($raw[$i] === false) {
            $missing[] = $id;
        } else {
            $found[$id] = json_decode($raw[$i], true, 512, JSON_THROW_ON_ERROR);
        }
    }

    if ($missing !== []) {
        $in = implode(',', array_fill(0, count($missing), '?'));
        $stmt = $db->prepare("SELECT id, name, price FROM products WHERE id IN ($in)");
        $stmt->execute($missing);
        $pipe = $redis->multi(Redis::PIPELINE);   // ghi lại cả lô trong một round-trip
        foreach ($stmt->fetchAll(PDO::FETCH_ASSOC) as $row) {
            $id = (int) $row['id'];
            $found[$id] = $row;
            $pipe->setex("shop:prod:product:{$id}:v1", 3600 + random_int(0, 300), json_encode($row, JSON_THROW_ON_ERROR));
        }
        $pipe->exec();
    }

    // id không còn trong DB thì bỏ qua (nên cache null marker, module 2.3)
    return array_values(array_filter(array_map(static fn (int $id): ?array => $found[$id] ?? null, $ids)));
}
```

⚠️ Trong Redis Cluster, `MGET` nhiều key chỉ chạy khi mọi key cùng một hash slot; khác slot thì
Redis trả lỗi `CROSSSLOT`. Client cluster thường tự chia `MGET` theo node, hoặc bạn chuyển sang
pipeline. Trong Laravel, `Cache::many([...])` lấy nhiều key một lần.

Số đếm (lượt xem, lượt thích, tồn kho hiển thị): dùng `INCR`/`HINCRBY` trên Redis, vì phép cộng
nguyên tử không có race đọc-sửa-ghi, rồi đồng bộ định kỳ về DB (đây là write-behind, module 2.1:
Redis mất dữ liệu thì mất phần chưa đồng bộ). Không cache số đếm theo kiểu cache-aside rồi xoá khi
ghi: key bị xoá liên tục, hit ratio gần 0.

#### Cache là một cuộc gọi mạng

Redis nhanh, nhưng mỗi lệnh vẫn tốn một *round-trip time* (RTT: thời gian gói tin đi và về). Docs
pipelining nêu ví dụ: RTT 250 ms (đường Internet rất chậm) thì dù server xử lý được 100k lệnh mỗi
giây, client gửi tuần tự chỉ làm được tối đa bốn lệnh mỗi giây. Trong cùng datacenter RTT nhỏ hơn
nhiều, nhưng nhân với vài trăm lệnh mỗi request thì vẫn thành hàng chục mili giây.

⚠️ *N+1 với cache*: vòng lặp `foreach ($ids as $id) { Cache::get("product:$id"); }` gọi Redis N
lần, N round-trip. Giống hệt N+1 query với DB, chỉ khó thấy hơn vì mỗi lần "nhanh". Sửa:

| Cách | Khi nào | Ghi chú |
|---|---|---|
| Lệnh gộp: `MGET`, `MSET`, `HMGET` | Cùng một loại thao tác trên nhiều key | Docs latency khuyên ưu tiên cách này trước pipeline |
| Pipeline | Nhiều lệnh khác nhau, không lệnh nào cần kết quả của lệnh trước | Gửi hết rồi đọc hết trả lời trong một round-trip; **không** nguyên tử, lệnh của client khác có thể chen vào giữa |
| Lua script | Cần đọc, tính, rồi ghi phía server | Pipeline không làm được "đọc rồi quyết định ghi" vì client cần kết quả đọc trước |

Pipeline còn giảm tải cho chính Redis: nhiều lệnh được đọc bằng một syscall `read()` và trả lời
bằng một `write()`, nên số lệnh mỗi giây tăng gần tuyến tính theo độ dài pipeline, tới khoảng 10 lần
so với không pipeline (theo docs). Benchmark trong docs trên loopback (RTT đã rất nhỏ): 10.000
`PING` mất khoảng 1,19 giây không pipeline và 0,25 giây có pipeline. ⚠️ Server phải giữ toàn bộ trả
lời trong bộ nhớ tới khi client đọc, nên lô rất lớn thì chia nhỏ; docs gợi ý cỡ 10k lệnh mỗi lô.

Timeout: đặt timeout kết nối và timeout đọc của client Redis **ngắn hơn DB nhiều** (vài chục tới vài
trăm mili giây tuỳ hệ thống). Redis chậm hoặc không trả lời thì coi như miss và đọc DB (có bảo vệ DB,
module 2.3, 3.3), đừng để mọi worker PHP-FPM treo chờ Redis rồi cả site không nhận request mới.
Kết nối mới cho mỗi lệnh cũng tốn: docs latency khuyên giữ kết nối sống lâu thay vì connect/disconnect
liên tục.

#### Warming và tag

*Cache warming* là nạp trước các key nóng trước khi traffic thật tới: sau deploy đổi version key,
sau khi Redis restart không có persistence, khi thêm node mới, hoặc trước một sự kiện biết trước
(flash sale). AWS gọi đây là *prewarming*: chạy script mô phỏng các request mà app sẽ gửi, rồi mới
gắn node mới vào.

- Chạy **từ từ**, có giới hạn tốc độ: warm hàng triệu key một lúc chính là tự tạo stampede lên DB.
- Chỉ warm tập key nóng (lấy từ log truy cập hoặc top sản phẩm), không warm "mọi thứ".
- Thêm jitter vào TTL khi warm, nếu không mọi key warm cùng lúc sẽ hết hạn cùng lúc (avalanche,
  module 2.3). AWS đưa ví dụ `ttl = 3600 + (rand() * 120)`.

*Cache tag* là gắn nhãn cho mục cache (`Cache::tags(['products', 'category:5'])`) để sau đó xoá cả
nhóm theo nhãn. Tiện hơn versioned key khi một mục thuộc nhiều nhóm. ⚠️ Không phải driver nào cũng
hỗ trợ, và trên Redis tag tốn thêm bộ nhớ để lưu danh sách key theo tag (chi tiết Laravel ở module
2.7).

#### Đo lường

*Hit ratio* = số lần đọc trúng / tổng số lần đọc. Redis có sẵn tổng qua `INFO stats`
(`keyspace_hits`, `keyspace_misses`), nhưng con số tổng dễ đánh lừa: một nhóm key hit 99% che đi
một nhóm hit 5%. Cần đo **theo nhóm key** ở phía app. Trong Laravel có thể nghe event
`Illuminate\Cache\Events\CacheHit` và `CacheMissed` rồi đếm theo tiền tố key.

Hit ratio thấp thường do:

- Key quá cụ thể: mỗi key chỉ được đọc một lần (ví dụ key chứa timestamp hoặc cả query string chưa
  chuẩn hoá).
- TTL quá ngắn so với tần suất đọc.
- Bị evict vì thiếu bộ nhớ (`evicted_keys` tăng). AWS coi eviction thường xuyên là dấu hiệu cần
  scale up (node nhiều RAM hơn) hoặc scale out, trừ khi bạn chủ ý dùng Redis như LRU cache.

Bộ metric nên có cho mỗi cache:

| Metric | Vì sao |
|---|---|
| Hit ratio tổng và theo nhóm key | Cache có đang làm việc không |
| Latency p50/p99 của lệnh cache (đo từ app) | p99 tăng là dấu hiệu big key, hot key, mạng |
| Số timeout, số lỗi kết nối | Cảnh báo sớm trước khi Redis sập hẳn |
| Số kết nối | PHP-FPM nhiều worker dễ chạm giới hạn kết nối |
| Memory dùng so với `maxmemory`, `evicted_keys`, `expired_keys` | Đủ bộ nhớ chưa, TTL có hợp không |
| Tải và latency của DB | Mục tiêu thật của cache |

Mục tiêu thật là giảm tải và latency cho DB và cho người dùng, không phải một con số hit ratio đẹp.
Hit ratio 99% trên key không ai quan tâm vẫn vô ích.

Nên có *feature flag* tắt cache theo từng tính năng (hoặc chuyển store sang driver `array`/`null`
của Laravel khi debug). ⚠️ Cache làm bug khó tái hiện: "chỉ sai với một số user" rất hay là do một
key cũ hoặc key thiếu yếu tố. Tắt được cache cho một tính năng là có thêm công cụ để xác nhận giả
thuyết đó. Nhưng trước khi tắt trên production, ước lượng DB có chịu được tải khi không có cache
không (module 3.3).

#### Khi nào không cache

Cache thêm một bản sao dữ liệu, tức thêm một nguồn sai. Chỉ đáng khi lợi ích lớn hơn cái giá đó.
⚠️ Không cache (hoặc nghĩ kỹ) khi:

- **Dữ liệu cần chính xác tuyệt đối lúc đọc**: số dư, tồn kho khi trừ, trạng thái thanh toán. Đọc
  thẳng DB (có thể cache để hiển thị, nhưng quyết định thì dựa trên DB).
- **Ghi nhiều hơn đọc**: mỗi lần ghi xoá cache, key gần như không bao giờ được đọc trúng.
- **Query vốn đã nhanh**: tra theo primary key trên bảng vừa phải mất cỡ mili giây; thêm cache chỉ
  thêm độ phức tạp. Nếu chậm vì thiếu index hay query viết sai thì sửa gốc trước (đo bằng `EXPLAIN`,
  xem [03-database-sql.md](03-database-sql.md#23-đọc-explain-và-xử-lý-query-chậm)).
- **Cá nhân hoá cao**: số tổ hợp key bùng nổ (user × bộ lọc × trang), mỗi key hiếm khi được đọc lại,
  hit ratio rất thấp mà tốn bộ nhớ.
- **Cache làm băng dán**: che một thiết kế chậm (endpoint gọi 30 service, query quét cả bảng). Tới
  lúc cache miss (deploy, restart, key mới) thì vấn đề gốc lộ ra đúng lúc tải cao nhất.

Nguyên tắc chung: đo trước khi cache (plan [17-performance.md](../17-performance.md)), biết rõ
query nào chậm và tốn bao nhiêu, rồi mới quyết định cache cái gì với TTL bao lâu.

**Tóm tắt nhanh**
- Đổi cấu trúc dữ liệu thì đổi version trong key; native `serialize` gắn với class và không an toàn
  với dữ liệu không tin cậy.
- Key chứa mọi yếu tố làm kết quả khác nhau (tenant, user, locale, quyền, tham số); thiếu tenant là
  lộ dữ liệu. Không `KEYS *` trên production.
- Cache danh sách id + object theo id, lấy bằng `MGET`; tránh N+1 với cache bằng lệnh gộp hoặc
  pipeline (pipeline không nguyên tử).
- Timeout Redis ngắn, lỗi thì coi như miss. Warm từ từ, có jitter.
- Đo hit ratio theo nhóm key, latency p99, eviction, và tải DB; không cache khi cần chính xác, ghi
  nhiều, query đã nhanh, hoặc key bùng nổ.

**Nguồn**: [Redis: Pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/) ·
[Redis: Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/) ·
[Redis: Key eviction](https://redis.io/docs/latest/develop/reference/eviction/) (mục Using the INFO command) ·
[AWS: Caching best practices](https://aws.amazon.com/caching/best-practices/) ·
[PHP: unserialize](https://www.php.net/manual/en/function.unserialize.php)


---

### 2.6 Cài LRU `O(1)`

Module này trả lời: làm sao để cả `get` lẫn `put` của một LRU cache đều chạy O(1), vì sao phải là
danh sách liên kết **hai chiều**, và các ngôn ngữ Java/Go/PHP có sẵn gì. Đây là bài LeetCode 146,
hay gặp ở vòng live coding; khái niệm LRU nằm ở module 1.3.

#### Ý tưởng

*LRU* (*least recently used*): khi đầy, bỏ mục lâu nhất chưa được dùng. Cần hai thao tác đều O(1):

| Việc cần làm | Hash map | Linked list |
|---|---|---|
| Tìm value theo key | O(1) | O(n), phải duyệt |
| Biết mục nào lâu nhất chưa dùng | Không biết thứ tự | O(1), là phần tử ở cuối |
| Đưa một mục vừa dùng lên đầu | Không có khái niệm thứ tự | O(1) nếu đã cầm sẵn node và list là hai chiều |

Mỗi cấu trúc mạnh ở đúng chỗ cấu trúc kia yếu, nên kết hợp: hash map từ key tới **node**, và các
node cùng nằm trong một *doubly linked list* (danh sách liên kết hai chiều: mỗi node trỏ tới cả node
trước và node sau).

```
map:  1 ─┐   3 ─┐   2 ─┐
         ▼      ▼      ▼
head ⇄ [1:a] ⇄ [3:c] ⇄ [2:b] ⇄ tail
       mới dùng nhất     lâu nhất chưa dùng (bị evict trước)
```

Quy ước trong bài này: đầu danh sách (cạnh `head`) là mục mới dùng nhất, cuối (cạnh `tail`) là mục
lâu nhất chưa dùng. Đảo ngược cũng được, miễn nhất quán.

#### Hai thao tác

`get(key)`:

1. Tra map. Không có thì trả miss (LeetCode yêu cầu trả `-1`).
2. Có thì gỡ node khỏi vị trí hiện tại, gắn lên đầu danh sách, rồi trả value.

`put(key, value)`:

1. Key đã có: cập nhật value, chuyển node lên đầu. Không evict gì (số phần tử không đổi).
2. Key chưa có và cache đã đầy: lấy node ngay trước `tail`, gỡ khỏi danh sách, xoá key của nó khỏi
   map.
3. Tạo node mới, gắn lên đầu, thêm vào map.

Mọi bước chỉ là tra map và sửa vài con trỏ, nên O(1). Map dùng O(1) *trung bình* (hash table), đây
cũng là ý của đề bài.

Timeline ví dụ với dung lượng 2 (đầu danh sách viết bên trái):

| Lệnh | Kết quả | Danh sách sau lệnh |
|---|---|---|
| `put(1, 1)` | | `[1]` |
| `put(2, 2)` | | `[2, 1]` |
| `get(1)` | `1` | `[1, 2]` |
| `put(3, 3)` | evict 2 | `[3, 1]` |
| `get(2)` | miss | `[3, 1]` |
| `put(4, 4)` | evict 1 | `[4, 3]` |
| `get(1)` | miss | `[4, 3]` |
| `get(3)` | `3` | `[3, 4]` |
| `get(4)` | `4` | `[4, 3]` |

#### Chi tiết cài đặt

- **Vì sao hai chiều**: để gỡ một node ở giữa, phải sửa con trỏ `next` của node **trước** nó. Danh
  sách một chiều không biết node trước, phải duyệt từ đầu, mất O(n). Có con trỏ `prev` thì gỡ trong
  O(1).
- **Node lưu cả key**, không chỉ value: khi evict node cuối, cần biết key của nó để xoá khỏi map.
  Quên chỗ này là map giữ key trỏ tới node đã bị gỡ, cache "nhớ" mục đã bị evict.
- **Sentinel** head và tail: hai node giả luôn nằm ở hai đầu và không bao giờ bị gỡ. Nhờ vậy mọi
  node thật luôn có `prev` và `next` khác null, nên thêm/gỡ không cần `if` cho danh sách rỗng, node
  đầu, node cuối. Đây là nguồn bug phổ biến nhất khi viết không có sentinel.
- **Kiểm tra đầy trước khi thêm** key mới, và chỉ khi key chưa tồn tại. Evict khi `put` trùng key là
  bug hay gặp với dung lượng 1.

Bản PHP đầy đủ, chạy bằng `php lru.php`:

```php
<?php
declare(strict_types=1);

final class Node
{
    public ?Node $prev = null;
    public ?Node $next = null;

    public function __construct(public int $key, public int $value) {}
}

final class LRUCache
{
    /** @var array<int, Node> */
    private array $map = [];
    private Node $head; // sentinel: head->next là mục mới dùng nhất
    private Node $tail; // sentinel: tail->prev là mục lâu nhất chưa dùng

    public function __construct(private readonly int $capacity)
    {
        if ($capacity < 1) {
            throw new InvalidArgumentException('capacity phải >= 1');
        }
        $this->head = new Node(0, 0);
        $this->tail = new Node(0, 0);
        $this->head->next = $this->tail;
        $this->tail->prev = $this->head;
    }

    public function get(int $key): ?int
    {
        $node = $this->map[$key] ?? null;
        if ($node === null) {
            return null; // miss
        }
        $this->unlink($node);
        $this->pushFront($node);
        return $node->value;
    }

    public function put(int $key, int $value): void
    {
        $node = $this->map[$key] ?? null;
        if ($node !== null) {           // key đã có: cập nhật, không evict
            $node->value = $value;
            $this->unlink($node);
            $this->pushFront($node);
            return;
        }
        if (count($this->map) === $this->capacity) {
            $lru = $this->tail->prev;   // không bao giờ là head vì map không rỗng
            $this->unlink($lru);
            unset($this->map[$lru->key]);
        }
        $node = new Node($key, $value);
        $this->pushFront($node);
        $this->map[$key] = $node;
    }

    private function unlink(Node $n): void
    {
        $n->prev->next = $n->next;
        $n->next->prev = $n->prev;
        $n->prev = null;
        $n->next = null;
    }

    private function pushFront(Node $n): void
    {
        $n->prev = $this->head;
        $n->next = $this->head->next;
        $this->head->next->prev = $n;
        $this->head->next = $n;
    }
}

$c = new LRUCache(2);
$c->put(1, 1);
$c->put(2, 2);
var_dump($c->get(1)); // int(1)
$c->put(3, 3);        // evict 2
var_dump($c->get(2)); // NULL
$c->put(4, 4);        // evict 1
var_dump($c->get(1)); // NULL
var_dump($c->get(3)); // int(3)
var_dump($c->get(4)); // int(4)

// Trường hợp biên: dung lượng 1, put trùng key không được evict
$one = new LRUCache(1);
$one->put(1, 1);
$one->put(1, 10);
var_dump($one->get(1)); // int(10)
$one->put(2, 2);        // evict 1
var_dump($one->get(1)); // NULL
var_dump($one->get(2)); // int(2)
```

Trả `null` thay cho `-1` của LeetCode để không lẫn "miss" với value hợp lệ là `-1`; khi nộp LeetCode
thì đổi lại theo đề. Lưu ý: code trên chưa được chạy thử trong repo (máy chưa có PHP), bản Go bên
dưới thì đã chạy.

⚠️ **Đa luồng**: `get` cũng là thao tác **ghi**, vì nó đổi thứ tự danh sách. Hai thread cùng `get`
có thể cùng sửa con trỏ và làm hỏng danh sách. Nên `get` cũng phải lấy lock độc quyền; dùng
read-write lock và cho `get` lấy read lock là sai. Đây là câu hỏi vặn phổ biến sau khi viết xong.
Thư viện cache production (Caffeine, ristretto) tránh lock toàn cục bằng cách ghi lại lượt truy cập
vào buffer và áp dụng theo lô, nhưng đó là tối ưu, không cần trong phỏng vấn.

#### Đối chiếu Java/Go/PHP

**Java**: `LinkedHashMap` đã là hash map kèm doubly linked list. Constructor
`LinkedHashMap(initialCapacity, loadFactor, accessOrder)` với `accessOrder = true` thì mỗi lần truy
cập đưa entry xuống cuối thứ tự duyệt (cuối là mới dùng nhất, đầu là lâu nhất). Override
`removeEldestEntry` để tự bỏ entry cũ nhất sau mỗi lần `put`:

```java
import java.util.LinkedHashMap;
import java.util.Map;

public class LruDemo {
    static final class Lru<K, V> extends LinkedHashMap<K, V> {
        private final int capacity;

        Lru(int capacity) {
            super(capacity, 0.75f, true); // true: sắp theo thứ tự truy cập
            this.capacity = capacity;
        }

        @Override
        protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity;     // put/putAll gọi sau khi chèn entry mới
        }
    }

    public static void main(String[] args) {
        Lru<Integer, Integer> c = new Lru<>(2);
        c.put(1, 1);
        c.put(2, 2);
        c.get(1);                         // 1 thành mới dùng nhất
        c.put(3, 3);                      // evict 2
        System.out.println(c.keySet());   // [1, 3]
    }
}
```

⚠️ Javadoc của `LinkedHashMap` ghi rõ: ở chế độ access-order, chỉ gọi `get` cũng là *structural
modification*. Nên `LinkedHashMap` access-order dùng chung giữa nhiều thread phải bọc
`Collections.synchronizedMap` hoặc lock ngoài, cùng lý do như trên. Trong phỏng vấn, dùng
`LinkedHashMap` là câu trả lời "biết thư viện"; người phỏng vấn thường yêu cầu tự cài thêm bản
map + linked list.

**Go**: không có sẵn LRU, nhưng `container/list` là doubly linked list với `PushFront`,
`MoveToFront`, `Back`, `Remove`. Kết hợp với `map[K]*list.Element` (chạy bằng `go run main.go`):

```go
package main

import (
	"container/list"
	"fmt"
	"sync"
)

// entry nằm trong list.Element.Value; giữ cả key để evict thì biết xoá gì khỏi map.
type entry struct {
	key   int
	value int
}

type LRU struct {
	mu       sync.Mutex // Mutex, không phải RWMutex: Get cũng đổi thứ tự list
	capacity int
	ll       *list.List // Front là mới dùng nhất, Back là lâu nhất chưa dùng
	items    map[int]*list.Element
}

func NewLRU(capacity int) *LRU {
	return &LRU{capacity: capacity, ll: list.New(), items: make(map[int]*list.Element)}
}

func (c *LRU) Get(key int) (int, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	e, ok := c.items[key]
	if !ok {
		return 0, false
	}
	c.ll.MoveToFront(e)
	return e.Value.(*entry).value, true
}

func (c *LRU) Put(key, value int) {
	c.mu.Lock()
	defer c.mu.Unlock()
	if e, ok := c.items[key]; ok {
		e.Value.(*entry).value = value
		c.ll.MoveToFront(e)
		return
	}
	if c.ll.Len() == c.capacity {
		oldest := c.ll.Back()
		c.ll.Remove(oldest)
		delete(c.items, oldest.Value.(*entry).key)
	}
	c.items[key] = c.ll.PushFront(&entry{key, value})
}

func main() {
	c := NewLRU(2)
	c.Put(1, 1)
	c.Put(2, 2)
	fmt.Println(c.Get(1)) // 1 true
	c.Put(3, 3)           // evict 2
	fmt.Println(c.Get(2)) // 0 false
	c.Put(4, 4)           // evict 1
	fmt.Println(c.Get(1)) // 0 false
	fmt.Println(c.Get(3)) // 3 true
	fmt.Println(c.Get(4)) // 4 true
}
```

Kiểu `(int, bool)` của Go (*comma ok*) tách rõ "miss" với "value bằng 0", tương tự lý do bản PHP trả
`null`.

**PHP**: không có LRU có sẵn, phải tự cài như bản trên. Có một đường tắt dựa trên việc array PHP là
hash table **giữ thứ tự chèn**:

```php
<?php
declare(strict_types=1);

// Đường tắt: phần tử đầu mảng là lâu nhất chưa dùng, cuối mảng là mới dùng nhất.
/** @param array<int, int> $cache */
function lruGet(array &$cache, int $key): ?int
{
    if (!array_key_exists($key, $cache)) {
        return null;
    }
    $value = $cache[$key];
    unset($cache[$key]);   // gỡ ra
    $cache[$key] = $value; // gán lại: phần tử chuyển xuống cuối
    return $value;
}

/** @param array<int, int> $cache */
function lruPut(array &$cache, int $key, int $value, int $capacity): void
{
    if (array_key_exists($key, $cache)) {
        unset($cache[$key]);
    } elseif (count($cache) === $capacity) {
        unset($cache[array_key_first($cache)]); // bỏ phần tử đầu
    }
    $cache[$key] = $value;
}

$cache = [];
lruPut($cache, 1, 1, 2);
lruPut($cache, 2, 2, 2);
lruGet($cache, 1);
lruPut($cache, 3, 3, 2);           // evict 2
var_dump(array_keys($cache));      // [1, 3] (var_dump in nhiều dòng: array(2) { [0]=> int(1) [1]=> int(3) })
```

Chỉ gán lại key đang có (`$cache[$key] = ...` mà không `unset`) **không** đổi vị trí, nên bước
`unset` là bắt buộc. Cách này ngắn và đủ dùng cho memoize trong một request hay một worker, nhưng
khi phỏng vấn yêu cầu "O(1) và tự cài cấu trúc" thì nên viết bản map + doubly linked list: đường tắt
dựa vào chi tiết cài đặt bên trong của array PHP (các ô bị `unset` để lại chỗ trống cho tới khi PHP
dồn lại bảng), nên khó chứng minh O(1) chặt chẽ.

Ngữ cảnh PHP: với PHP-FPM mỗi request bắt đầu sạch, nên LRU trong process chỉ có ý nghĩa trong
phạm vi một request, hoặc trong process sống lâu như queue worker, Octane (module 2.7). Cache dùng
chung giữa các request vẫn là Redis, và Redis tự lo eviction bằng LRU xấp xỉ (module 2.4).

**Tóm tắt nhanh**
- Hash map (key tới node) + doubly linked list (thứ tự dùng): map cho tra O(1), list cho evict và
  đưa lên đầu O(1).
- Hai chiều để gỡ node giữa trong O(1); node lưu key để evict xong xoá được khỏi map; sentinel để
  bỏ mọi `if` biên.
- `put` trùng key thì cập nhật, không evict; kiểm tra đầy chỉ khi thêm key mới.
- Đa luồng: `get` cũng ghi (đổi thứ tự), nên cần lock độc quyền, không dùng read lock.
- Java `LinkedHashMap(cap, 0.75f, true)` + `removeEldestEntry`; Go `map` + `container/list`; PHP tự
  cài (hoặc đường tắt `unset` rồi gán lại).

**Nguồn**: [LeetCode 146: LRU Cache](https://leetcode.com/problems/lru-cache/) ·
[Java: LinkedHashMap](https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/LinkedHashMap.html) ·
[Go: container/list](https://pkg.go.dev/container/list) ·
[PHP: Arrays](https://www.php.net/manual/en/language.types.array.php)

---

### 2.7 Cache trong PHP/Laravel

Module này trả lời: vì sao PHP-FPM không có "cache trong RAM của app" như Java, các lựa chọn thay
thế (APCu, Octane cache) khác nhau ra sao, dùng đúng các API cache của Laravel để chống stampede, và
những cấu hình nào khiến một lệnh artisan vô hại làm hỏng production.

Nền tảng về PHP-FPM, OPcache, Octane và bảng API cache cơ bản của Laravel đã có ở
[05-php-laravel.md](05-php-laravel.md) (các module
[2.2](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing),
[2.3](05-php-laravel.md#23-opcache-và-deploy),
[2.7 mục Cache](05-php-laravel.md#27-các-thành-phần-khác-của-laravel),
[3.5](05-php-laravel.md#35-process-sống-lâu-queue-worker-octane-daemon)). Ở đây chỉ nhắc lại phần
cần cho góc nhìn cache và bổ sung những gì bên đó chưa nói.

#### Mô hình PHP-FPM và cache trong process

*Share-nothing*: dưới PHP-FPM, hết một request thì mọi biến global, biến `static`, singleton trong
container đều bị huỷ. Request sau, dù rơi vào đúng worker cũ, bắt đầu từ trạng thái trắng
([01-os-linux.md](../01-os-linux.md) module 1.1, [05 module 2.2](05-php-laravel.md#22-php-fpm-và-mô-hình-share-nothing)).
Hệ quả cho cache: một `static array $cache` trong class PHP chỉ sống trong **một request**. Nó vẫn
có ích (memoize trong request), nhưng không phải L1 cache theo nghĩa của Java, nơi một
`ConcurrentHashMap` hay Caffeine sống suốt đời process và phục vụ hàng triệu request.

Thứ sống qua request dưới FPM chỉ nằm ở tầng extension C, trong *shared memory* (vùng nhớ nhiều
process cùng ánh xạ vào). Ba thứ hay bị nhầm với nhau:

| | APCu | OPcache | Octane cache |
|---|---|---|---|
| Cache gì | Dữ liệu key-value do code của bạn ghi | Bytecode (opcode) đã biên dịch của file PHP | Dữ liệu key-value |
| Nằm ở đâu | Shared memory của một máy, các worker FPM do cùng một master sinh ra đọc chung | Shared memory của một máy | Swoole table (shared memory) của server Octane, mọi worker trên server đó đọc chung |
| Mất khi | Restart PHP-FPM | Restart PHP-FPM, hoặc `opcache_reset()` | Restart server Octane |
| Điều kiện | Cài extension `apcu` | Có sẵn trong PHP, bật bằng ini | **Chỉ đúng như mô tả khi chạy Swoole**. Trên RoadRunner/FrankenPHP, store `octane` không báo lỗi mà lặng lẽ dùng `OctaneArrayStore`: mảng riêng trong từng worker, không chia sẻ |
| Thay Redis được không | Không khi có nhiều server | Không liên quan, không phải cache dữ liệu | Không khi có nhiều server |

*APCu* là phần "cache dữ liệu" còn lại của APC cũ sau khi bỏ phần cache opcode (việc đó giao hẳn cho
OPcache). Hàm chính:

```php
<?php
declare(strict_types=1);

// Chạy thử: php -d apc.enable_cli=1 apcu_demo.php (cần extension apcu)
apcu_store('config:features', ['new_checkout' => true], 30);   // TTL 30 giây
$features = apcu_fetch('config:features', $found);             // $found = true nếu hit
var_dump($found, $features);

apcu_add('counter', 0);           // chỉ ghi nếu key chưa có
apcu_inc('counter');              // tăng nguyên tử
apcu_cas('counter', 1, 10);       // compare-and-swap: đổi 1 thành 10 nếu giá trị hiện tại là 1

// apcu_entry: "có thì trả, chưa có thì gọi callback rồi lưu", làm nguyên tử.
// Theo docs PHP, apcu_entry giữ lock độc quyền của CẢ cache trong lúc callback chạy:
// mọi hàm APCu khác ở process khác phải chờ, nên callback phải thật nhanh
$rates = apcu_entry('fx:rates', static fn (string $key): array => ['USD' => 25_000], 60);
```

Các cạm bẫy của APCu:

- ⚠️ Mỗi server một bản riêng. Có 10 server thì có 10 bản APCu độc lập, ghi ở server 1 không làm
  server 2 biết. Không có cách invalidate chéo có sẵn, nên độ cũ tối đa bằng TTL (đây chính là bài
  toán L1 ở module 3.1).
- ⚠️ CLI không thấy dữ liệu của FPM. `apc.enable_cli` mặc định là `0`, và kể cả bật lên thì mỗi lần
  chạy `php artisan ...` là một process riêng với vùng nhớ riêng. Nên `php artisan cache:clear` với
  store `apc` **không** xoá được APCu mà FPM đang dùng; phải xoá từ trong một request web, hoặc
  reload FPM.
- ⚠️ Mặc định `apc.shm_size` là `32M`. Đầy bộ nhớ thì APCu phải dọn bớt; theo dõi bằng
  `apcu_sma_info()` và `apcu_cache_info()`.
- Khi nào APCu vẫn hợp lý: dữ liệu nhỏ, đọc cực nhiều, chấp nhận cũ vài giây tới vài phút, và giống
  nhau giữa các server (cấu hình, feature flag, bảng tỉ giá, route map). Đặt TTL ngắn để giới hạn
  độ cũ. Laravel có driver `apc` (`ApcStore`); khai báo một store `'apc' => ['driver' => 'apc']` trong
  `config/cache.php` (skeleton không có sẵn) rồi gọi `Cache::store('apc')`.

*OPcache* cache bytecode, không cache dữ liệu. ⚠️ Nói "dùng OPcache để cache kết quả query" là red
flag trong phỏng vấn. Điểm liên quan tới vận hành: với `opcache.validate_timestamps=0` (hay dùng trên
production), PHP không kiểm tra file thay đổi, nên deploy code mới phải reload FPM hoặc reset
OPcache, không thì server chạy code cũ. Chi tiết ở [05 module 2.3](05-php-laravel.md#23-opcache-và-deploy).

*Octane* (Swoole, RoadRunner hoặc FrankenPHP) giữ app sống qua nhiều request, nên biến static và
singleton sống lâu, giống Java. Hai hệ quả cho cache:

- Octane cache (`Cache::store('octane')`) chạy trên Swoole table: nhanh (docs Laravel nói tới
  "2 million operations per second"), mọi worker trên server đọc chung, mất khi restart server. Số
  mục tối đa đặt trong `config/octane.php` (`cache.rows`, mặc định 1000). Có thêm `interval()` để một
  giá trị tự làm mới theo chu kỳ, hợp với key cực nóng (module 2.3).
- ⚠️ Docs ghi tính năng này "requires Swoole". Theo mã nguồn `OctaneServiceProvider`, khi không có
  Swoole table (RoadRunner, FrankenPHP) store `octane` vẫn đăng ký được nhưng là `OctaneArrayStore`:
  mỗi worker một mảng riêng, và `interval()` chỉ gọi resolver rồi trả kết quả, không lưu vào cache
  và không tự làm mới. Code không
  lỗi, chỉ âm thầm mất tính "mọi worker đọc chung".
- ⚠️ Một mảng static tự chế làm "cache" trong Octane thì không có TTL, không có giới hạn kích thước,
  và có thể rò dữ liệu của user này sang request của user khác. Xem
  [05 module 3.5](05-php-laravel.md#35-process-sống-lâu-queue-worker-octane-daemon).

#### Laravel Cache API

Bảng method cơ bản (`get`, `put`, `add`, `remember`, `increment`, `touch`...) có ở
[05 module 2.7](05-php-laravel.md#27-các-thành-phần-khác-của-laravel). Ở đây xếp chúng theo pattern
của file này:

| Nhu cầu | API | Pattern |
|---|---|---|
| Đọc, miss thì nạp | `Cache::remember($k, $ttl, $fn)`, `rememberForever` | Cache-aside (module 1.2) |
| Biết lần này hit hay miss | `Cache::rememberWithWarmth(...)` trả `[$value, $warm]` | Đo hit ratio |
| Nhớ trong một request/job | `Cache::memo()`, helper `once()` | Memoize |
| Chống stampede, chấp nhận cũ | `Cache::flexible($k, [$fresh, $stale], $fn)` | Stale-while-revalidate (module 2.3) |
| Chống stampede, không chấp nhận cũ | `Cache::lock(...)` bọc phần nạp | Mutex (module 2.3) |
| Chỉ một bản chạy trên cả hạ tầng | `Cache::withoutOverlapping($k, $fn)` | Mutex |
| Giới hạn N bản chạy song song | `Cache::funnel($k)->limit(N)` | Semaphore |
| Xoá cả nhóm | `Cache::tags([...])->flush()` | Tag (module 2.5) |
| Store chính chết | driver `failover` | Module 3.3 |

⚠️ `Cache::remember` **không** chống stampede: nó chỉ là "get, null thì gọi closure rồi put", không
có lock giữa các request. 500 request cùng miss là 500 lần chạy closure.

*Memoize trong request*: hai công cụ khác nhau về chỗ lưu.

- `Cache::memo()->get('k')` bọc một store: lần đầu gọi Redis, các lần sau trong cùng request/job
  lấy từ bộ nhớ. Mọi thao tác ghi (`put`, `increment`, `remember`...) qua `memo()` tự quên bản nhớ rồi
  ghi xuống store thật. Có từ Laravel 12.
- `once(fn () => ...)` nhớ kết quả của **một closure** trong suốt request, không dính tới cache
  store. Gọi trong method của object thì mỗi instance có bản nhớ riêng.
- Cả hai giải cùng một bệnh: một request gọi `Cache::get('settings')` 40 lần là 40 round-trip Redis
  (N+1 với cache, module 2.5).

*`Cache::flexible`* (có từ Laravel 11, bản 11.23): cách hoạt động và timeline đầy đủ ở
[05 module 2.7](05-php-laravel.md#27-các-thành-phần-khác-của-laravel). Tóm lại theo mã nguồn
`Repository::flexible` ở 13.x:

1. Đọc cùng lúc giá trị và một key phụ lưu thời điểm tạo, cả hai có TTL bằng `$stale`.
2. Chưa có (lần đầu, hoặc đã quá `$stale`): tính **ngay** trong request. Đoạn này vẫn có thể
   stampede khi cache lạnh.
3. Tuổi nhỏ hơn `$fresh`: trả luôn.
4. Tuổi giữa `$fresh` và `$stale`: trả bản cũ, đăng ký một hàm `defer` chạy sau khi gửi response.
   Hàm đó lấy lock `illuminate:cache:flexible:lock:{key}`, kiểm tra chưa ai làm mới, rồi mới gọi
   closure.

Hai điều ít người biết, cũng rút từ mã nguồn:

- ⚠️ Tham số thứ tư `$lock` mặc định có `seconds = 0`. Với Redis, lock 0 giây được lấy bằng `SETNX`
  **không có hạn**. Nếu process đang làm mới bị kill giữa chừng, lock kẹt lại và mọi lần làm mới sau
  đều bỏ qua cho tới khi ai đó xoá lock. Nên truyền hạn cho lock:
  `Cache::flexible('stats', [60, 300], $fn, ['seconds' => 30])`.
- ⚠️ Giá trị `null` bị coi là "chưa có" (bước 2), nên closure trả `null` thì lần nào cũng tính lại.
  Muốn cache kết quả rỗng (chống penetration, module 2.3) thì trả một marker khác `null`, ví dụ
  mảng rỗng.

*`Cache::lock`*: atomic lock qua cache store, dùng owner token để chỉ bên giữ lock nhả được.

```php
<?php
declare(strict_types=1);

use Illuminate\Contracts\Cache\LockTimeoutException;
use Illuminate\Support\Facades\Cache;

// Chống stampede cho một key không được phép trả dữ liệu cũ
function dashboardStats(): array
{
    $key = 'dashboard:stats:v1';
    $cached = Cache::get($key);
    if ($cached !== null) {
        return $cached;
    }

    try {
        // Lock tự hết hạn sau 10 giây (người giữ chết thì người khác vào được),
        // chờ tối đa 3 giây để lấy lock
        return Cache::lock("lock:{$key}", 10)->block(3, function () use ($key): array {
            // Kiểm tra lại: có thể request vừa giữ lock trước đã nạp xong
            $again = Cache::get($key);
            if ($again !== null) {
                return $again;
            }
            $stats = ['orders' => 123]; // thay bằng query nặng thật
            Cache::put($key, $stats, 300);
            return $stats;
        });
    } catch (LockTimeoutException) {
        // Chờ quá lâu: tuỳ nghiệp vụ, trả lỗi 503 hoặc tự query (chấp nhận tải lên DB)
        throw new RuntimeException('Stats đang được tính, thử lại sau');
    }
}
```

So sánh hai cách chống stampede:

| | `Cache::flexible` | `Cache::lock` quanh phần nạp |
|---|---|---|
| Người dùng thấy | Dữ liệu cũ tối đa `$stale` giây | Luôn dữ liệu mới, nhưng một số request phải chờ |
| Latency lúc làm mới | Không ai chờ (làm sau response) | Các request khác chờ tới `block()` giây |
| Khi cache lạnh hoàn toàn | Vẫn stampede ở lần nạp đầu | Vẫn chỉ một request nạp |
| Hợp với | Dashboard, danh sách, trang chủ | Dữ liệu phải mới, hoặc cache đang lạnh sau deploy |

Các chi tiết khác của lock (có trong docs 13.x):

- `Cache::lock($name, $seconds)->get()` thử một lần; `block($n)` chờ tối đa `$n` giây rồi ném
  `LockTimeoutException`.
- Nhả lock ở process khác: truyền `$lock->owner()` vào job, rồi trong job gọi
  `Cache::restoreLock($name, $owner)->release()`. `forceRelease()` bỏ qua owner.
- `$lock->refresh()` gia hạn lock đang giữ, cho việc dài: lấy lock ngắn rồi gia hạn định kỳ thay vì
  lock thật dài.
- Driver hỗ trợ lock: `memcached`, `redis`, `dynamodb`, `database`, `file`, `array`, và mọi server
  phải nói chuyện với cùng một cache server. `file` và `array` chỉ có nghĩa trên một máy.

*Cache tags*: `Cache::tags(['people', 'authors'])->put(...)`, đọc lại phải truyền đúng danh sách tag
đã dùng khi ghi, `Cache::tags('authors')->flush()` xoá mọi mục có tag đó.

- Không hỗ trợ với driver `file`, `dynamodb`, `database`, `storage`.
- ⚠️ Trên Redis, mỗi tag là một sorted set chứa tên mọi key mang tag đó (điểm số là thời điểm hết
  hạn). Tag có hàng triệu key thì tốn memory, và `flush()` phải duyệt set đó rồi xoá từng key, chậm
  và có thể thành big key (module 2.4). Key hết hạn vẫn nằm trong set cho tới khi được dọn; Laravel
  có lệnh `php artisan cache:prune-stale-tags` để dọn, nên cho chạy trong scheduler.
- Thay thế nhẹ hơn: versioned key (module 2.2), tăng một số version là "xoá" cả nhóm.

*Failover driver*: store `failover` thử lần lượt các store trong danh sách, store trước lỗi (ném
exception) thì dùng store sau, và phát event `CacheFailedOver` để bạn log/alert.

```php
// config/cache.php
'failover' => [
    'driver' => 'failover',
    'stores' => ['redis', 'array'],   // Redis chết thì rơi về array (chỉ trong process)
],
// .env: CACHE_STORE=failover
```

- ⚠️ Failover chỉ kích hoạt khi store chính **ném lỗi**. Theo mã nguồn `FailoverStore`, mỗi thao tác
  đều thử store chính trước, nên nếu Redis treo thay vì từ chối kết nối, mỗi lần gọi vẫn chờ hết
  timeout rồi mới chuyển. Timeout ngắn cho kết nối Redis vẫn là bắt buộc (module 3.3).
- Rơi về `array` hay `database` nghĩa là toàn bộ tải đổ về DB hoặc mất tác dụng cache. Đó là quyết
  định cần tính trước, không phải "bật lên là an toàn".

#### Redis client

Laravel nói chuyện với Redis qua một trong hai client, chọn bằng `REDIS_CLIENT`:

| | phpredis | Predis |
|---|---|---|
| Là gì | Extension C, cài qua PECL | Thư viện thuần PHP, cài qua Composer |
| Mặc định trong Laravel | Có (`'client' => env('REDIS_CLIENT', 'phpredis')`) | Không |
| Tốc độ | Nhanh hơn | Chậm hơn, nhưng không cần extension |
| Serializer và nén ở tầng client | Có | Không |
| Persistent connection | Có (`persistent`, `pconnect`) | Có tham số `persistent` riêng |

phpredis cấu hình serializer và nén trong `options` của `config/database.php`:

- Serializer: `Redis::SERIALIZER_NONE` (mặc định), `SERIALIZER_PHP`, `SERIALIZER_JSON`,
  `SERIALIZER_IGBINARY`, `SERIALIZER_MSGPACK`.
- Nén: `Redis::COMPRESSION_NONE` (mặc định), `COMPRESSION_LZF`, `COMPRESSION_ZSTD`,
  `COMPRESSION_LZ4`.
- ⚠️ Đổi serializer hoặc thuật toán nén là mọi value cũ trong Redis đọc ra sai hoặc lỗi. Giống đổi
  format ở module 2.5: đổi prefix/version của key cùng lúc, hoặc chấp nhận flush cache khi deploy.
- ⚠️ Serializer của phpredis là tuỳ chọn của cả client, áp dụng cho các lệnh đi qua connection đó,
  kể cả `Redis::get()`/`Redis::set()` gọi tay ở chỗ khác trong code. Muốn bật cho cache thì nên đặt
  ở connection riêng của cache, không đặt ở `options` chung.

*Persistent connection* (`'persistent' => true`): worker FPM giữ lại kết nối TCP tới Redis sau khi
request xong, request sau dùng lại, bớt thời gian bắt tay (nhất là khi dùng TLS). Cái giá: số kết nối
tới Redis tăng theo tổng số worker FPM trên mọi server, và các kết nối đó luôn mở.

Laravel 13 thêm một lớp bảo vệ liên quan tới serialize: `config/cache.php` của skeleton có
`'serializable_classes' => false`, nghĩa là khi đọc cache, Laravel gọi `unserialize` với
`allowed_classes = false`, không dựng lại object PHP nào. Mục đích: nếu `APP_KEY` hay Redis bị lộ,
kẻ tấn công không nhét được *gadget chain* (chuỗi object độc hại) vào cache
([05 module 3.7](05-php-laravel.md#37-bảo-mật-đặc-thù-php)). Hệ quả: cache một object (model, DTO)
thì đọc ra là `__PHP_Incomplete_Class`. Hoặc liệt kê class được phép trong `serializable_classes`,
hoặc (tốt hơn) cache mảng.

- ⚠️ Khi cache hit, `Repository::get` **không** coi `__PHP_Incomplete_Class` là miss: nó vẫn trả object
  hỏng đó về (chỉ gọi callback nếu bạn đăng ký `Cache::handleUnserializableClassUsing(...)`). Nên với
  `remember`, request đầu (miss) nhận model thật, các request sau nhận object hỏng; gọi method trên nó
  là `Error`, đọc property chỉ ra warning và `null`. Lỗi kiểu "chạy lần đầu thì đúng" này dễ lọt qua test.
- ⚠️ Mặc định an toàn này nằm trong `config/cache.php` của **skeleton**, không nằm trong framework.
  App nâng cấp từ 12 mà không thêm key thì `serializable_classes` là `null`, tức vẫn cho unserialize
  mọi class như cũ (upgrade guide 13.x có mục riêng cho việc này).

#### Các cạm bẫy của Laravel

*`cache:clear` và Redis DB dùng chung*

`php artisan cache:clear` gọi `flush()` trên store mặc định, và `RedisStore::flush()` chạy
**`FLUSHDB`** trên connection của cache. `FLUSHDB` xoá cả database Redis đó, không quan tâm prefix
(docs Laravel cảnh báo rõ: flush "does not respect your configured cache prefix").

Cấu hình skeleton Laravel 13 đã tách sẵn, và đó là cấu hình nên giữ:

```
config/database.php  redis.default  database = REDIS_DB (mặc định 0)
                     redis.cache    database = REDIS_CACHE_DB (mặc định 1)
config/cache.php     stores.redis   connection = 'cache', lock_connection = 'default'
config/queue.php     redis          connection = 'default'
config/session.php   connection = SESSION_CONNECTION (null thì dùng connection 'default')

  (khi QUEUE_CONNECTION, SESSION_DRIVER, CACHE_STORE đặt là redis; .env.example mặc định là database)
  DB 0: queue, session, cache lock        DB 1: cache
  cache:clear -> FLUSHDB trên DB 1, không đụng DB 0
```

Sự cố xảy ra khi phá thế tách đó:

- ⚠️ Đặt `REDIS_CACHE_CONNECTION=default` (hoặc cho `REDIS_CACHE_DB` trùng `REDIS_DB`): cache nằm
  chung DB với queue và session, `cache:clear` là mất job đang chờ và mọi người bị đăng xuất.
- ⚠️ Redis Cluster chỉ hỗ trợ database 0 (nhiều dịch vụ managed chạy ở cluster mode; Valkey từ 9.0 mới
  thêm nhiều database cho cluster, phải bật `cluster-databases`), nên cách tách
  bằng số DB không còn tác dụng. Khi đó tách bằng **instance** Redis riêng cho cache, như module 2.4 đã
  khuyên (instance cache dùng `allkeys-lru`/`allkeys-lfu`, instance queue/session dùng `noeviction`).
- Lock mặc định nằm ở connection `default`, nên `cache:clear` không xoá lock. Muốn xoá lock có
  `Cache::flushLocks()` (hoặc `cache:clear --locks`), và lệnh này chỉ chạy khi lock nằm ở connection
  tách riêng khỏi cache (không thì ném `RuntimeException`).
- ⚠️ Nhưng `RedisStore::flushLocks()` chạy **`FLUSHDB` trên connection của lock**. Với cấu hình
  skeleton, đó là connection `default`, tức DB 0: `cache:clear --locks` xoá luôn queue và session
  đang ở DB 0. Muốn dùng lệnh này an toàn thì cho lock một connection/DB riêng
  (`REDIS_CACHE_LOCK_CONNECTION`), không dùng chung với queue và session.

Cách tự kiểm tra trên một server:

```sh
php artisan tinker --execute="dump(config('cache.stores.redis'), config('database.redis.cache.database'), config('queue.connections.redis.connection'))"
redis-cli -n 0 DBSIZE   # queue + session
redis-cli -n 1 DBSIZE   # cache
```

*Cache nguyên model Eloquent*

- ⚠️ `Cache::remember('user:1', 300, fn () => User::with('orders')->find(1))` serialize cả model,
  cả relation đã load (có thể hàng nghìn dòng), cả các thuộc tính nội bộ. Value phình to.
- ⚠️ Đổi class (thêm cast, đổi namespace) là bản cũ trong cache đọc ra lỗi hoặc sai, đúng lúc deploy.
- ⚠️ Ở Laravel 13 với `serializable_classes = false` (mặc định của skeleton), object đọc ra thành
  `__PHP_Incomplete_Class` như đã nói ở trên: lần đầu chạy đúng, từ lần hit thứ hai thì hỏng.
- Nên cache mảng hoặc DTO đơn giản: `->only(['id', 'name', 'email'])` hay `->toArray()`, và đặt
  version trong key (`user:1:v2`).

*Các bẫy nhỏ khác*

- `Cache::flush()` trong code (không chỉ artisan) có cùng hiệu ứng `FLUSHDB`.
- `Cache::put('k', $v)` không truyền TTL là lưu vô hạn. Với Redis dùng `allkeys-*` thì còn được
  evict, với `noeviction` thì tích tụ tới khi đầy bộ nhớ.
- Xoá cache trong transaction trước khi commit: dùng `DB::afterCommit(...)` (module 2.2).

#### Đối chiếu Java/Go

| | Laravel | Spring | Go |
|---|---|---|---|
| Cache-aside khai báo | `Cache::remember` (gọi tay) | `@Cacheable` trên method | Tự viết, hoặc thư viện |
| Xoá | `Cache::forget`, tag | `@CacheEvict` (mặc định chạy sau khi method thành công; `beforeInvocation = true` để xoá trước) | Tự viết |
| Gom load cùng key trong process | Không có (FPM mỗi process một request) | `@Cacheable(sync = true)`: một thread tính, các thread khác chờ | `singleflight` |
| L1 in-process | APCu, Octane cache | Caffeine | `ristretto`, map + mutex |
| Chống stampede giữa nhiều instance | `Cache::lock`, `flexible` | Tự làm (lock phân tán) | Tự làm |

- Spring `sync = true`: docs Spring nói mặc định abstraction "does not lock anything", cùng một giá trị
  có thể bị tính nhiều lần; `sync` yêu cầu cache provider khoá mục đó khi đang tính. Đây là tính năng
  tuỳ provider, các `CacheManager` có sẵn trong Spring đều hỗ trợ.
- ⚠️ Spring *self-invocation*: ở proxy mode (mặc định), chỉ lời gọi từ ngoài đi qua proxy mới bị chặn.
  Method A trong cùng class gọi method B có `@Cacheable` thì B chạy thẳng, không cache. Sửa: tách B
  sang bean khác, hoặc dùng AspectJ mode. Cũng không dựa vào cache trong `@PostConstruct` vì proxy
  chưa sẵn sàng.
- Go `singleflight.Group.Do(key, fn)`: các goroutine gọi cùng key trong lúc `fn` đang chạy sẽ chờ và
  nhận chung kết quả.
- ⚠️ Cả `sync = true`, Caffeine, `singleflight` chỉ gom trong **một process**. 20 instance vẫn có
  thể 20 lần cùng nạp một key, nên vẫn cần lock phân tán hoặc SWR ở tầng Redis. PHP-FPM thì còn
  không có "một process nhiều request" để gom, nên lock phân tán là lựa chọn duy nhất.

**Tóm tắt nhanh**

- PHP-FPM share-nothing: không có L1 in-process kiểu Java. Gần nhất là APCu (shared memory mỗi máy,
  CLI không thấy) hoặc Octane cache (chỉ Swoole). OPcache cache bytecode, không phải dữ liệu.
- `remember` không chống stampede. `flexible` trả dữ liệu cũ và làm mới sau response (nhớ truyền hạn
  cho lock); `lock` bắt chờ nhưng luôn mới.
- `cache:clear` chạy `FLUSHDB` trên connection của cache: giữ cache ở DB/instance riêng với queue và
  session (skeleton mặc định: cache DB 1, còn lại DB 0; Cluster chỉ có DB 0 nên phải tách instance).
- Không cache nguyên model Eloquent; skeleton Laravel 13 mặc định không unserialize object từ cache
  (hit trả `__PHP_Incomplete_Class`, không phải miss). `cache:clear --locks` là `FLUSHDB` trên DB của lock.
- Đổi serializer/nén của phpredis là đọc lỗi cache cũ; Spring `sync`, Go `singleflight` chỉ gom
  trong một process.

**Nguồn**: [Laravel 13 Cache](https://laravel.com/docs/13.x/cache) ·
[Laravel helpers: once()](https://laravel.com/docs/13.x/helpers#method-once) ·
[Laravel Redis](https://laravel.com/docs/13.x/redis) ·
[Laravel Octane: The Octane Cache](https://laravel.com/docs/13.x/octane#the-octane-cache) ·
[Laravel 13 upgrade guide](https://laravel.com/docs/13.x/upgrade) ·
mã nguồn `laravel/framework` 13.x (`Cache/Repository.php`, `RedisStore.php`, `RedisLock.php`,
`FailoverStore.php`, `RedisTagSet.php`) và `laravel/laravel` 13.x (`config/cache.php`,
`config/queue.php`, `config/session.php`) ·
[PHP: APCu](https://www.php.net/manual/en/book.apcu.php) ·
[APCu configuration](https://www.php.net/manual/en/apcu.configuration.php) ·
[phpredis README](https://github.com/phpredis/phpredis) ·
[Spring: Cache annotations](https://docs.spring.io/spring-framework/reference/integration/cache/annotations.html)

---

## Chặng 3: Senior

### 3.1 Multi-level cache (L1 + L2)

Module này trả lời: khi Redis thành nút thắt, thêm một tầng cache ngay trong app thì được gì, các
bản sao trên nhiều instance lệch nhau ra sao, và làm thế nào nói được con số "độ cũ tối đa" cho một
thiết kế cụ thể.

#### Hai tầng cache

- *L1* là cache *in-process*: nằm trong bộ nhớ của chính process app (Java: Caffeine hay
  `ConcurrentHashMap`; Go: `ristretto` hay map có mutex). Đọc L1 là đọc RAM, không qua mạng.
- *L2* là cache *distributed* dùng chung giữa mọi instance, thường là Redis/Valkey.
- Docs Redis gọi cách làm này là *client-side caching*: tận dụng bộ nhớ của máy app để giữ một phần
  dữ liệu, vì truy cập RAM cục bộ nhanh hơn gọi dịch vụ qua mạng nhiều bậc độ lớn, và thường chỉ một
  phần nhỏ dữ liệu được đọc rất nhiều.

```
 request
    |
    v
 +------------------+   hit: trả ngay (không round-trip)
 | L1 (RAM process) |-------------------------------->
 +------------------+
    | miss
    v
 +------------------+   hit: nạp vào L1, trả
 | L2 (Redis)       |-------------------------------->
 +------------------+
    | miss
    v
 +------------------+
 | DB               |   nạp vào L2 rồi L1, trả
 +------------------+
```

Luồng đọc:

1. Đọc L1. Hit thì trả luôn.
2. Miss thì đọc L2. Hit thì ghi vào L1 (TTL ngắn) rồi trả.
3. Miss tiếp thì đọc DB, ghi vào L2, rồi L1.

L1 đem lại hai thứ:

- Bớt round-trip: 1.000 request/giây đọc cùng key cấu hình, L1 TTL 5 giây, mỗi instance chỉ hỏi
  Redis khoảng một lần mỗi 5 giây thay vì 1.000 lần mỗi giây.
- Chắn hot key (module 2.4): request không còn dồn vào một node Redis giữ key đó.

L2 vẫn cần: nó dùng chung, nên instance mới khởi động hay instance vừa miss L1 không phải xuống DB,
và DB chỉ thấy tải bằng số lần miss của L2.

#### Vấn đề: mỗi instance một bản L1

Với 20 instance, một key có thể có tới 20 bản L1 cộng một bản L2. Khi dữ liệu đổi:

| Bước | Instance A (ghi) | Instance B | Kết quả |
|---|---|---|---|
| 1 | | Đọc `product:1`, nạp L1 = giá 100 | B.L1 = 100 |
| 2 | Update DB giá 120, xoá L2, xoá A.L1 | | DB = 120, L2 trống, A.L1 trống |
| 3 | | Đọc `product:1`: hit L1 = 100 | B trả giá cũ |
| 4 | | ... tới khi L1 của B hết hạn | Độ cũ = phần TTL còn lại của B.L1 |

A xoá được L1 của chính nó và L2, nhưng không với tới bộ nhớ của B. Nếu không làm gì thêm, độ cũ
tối đa ở B bằng đúng TTL của L1.

⚠️ Thứ tự xoá quan trọng: phải xoá **L2 trước**, rồi mới báo các instance xoá L1. Làm ngược lại, B
nhận thông báo, xoá L1, đọc lại L2 vẫn còn bản cũ, và nạp bản cũ vào L1 thêm trọn một TTL nữa.

#### Cách xử lý

*Cách 1: TTL của L1 rất ngắn*

- Đặt TTL L1 vài giây. Đơn giản nhất, không cần hạ tầng gì, và cho một cận trên rõ ràng: B cũ tối
  đa bằng TTL của L1 (cộng độ cũ của chính L2, xem phần tính toán bên dưới).
- Docs Redis cũng khuyên, kể cả khi đã có cơ chế invalidation, vẫn đặt một TTL tối đa cho mọi mục
  L1 để phòng bug hoặc sự cố kết nối làm client giữ bản cũ mãi.

*Cách 2: broadcast invalidation qua Pub/Sub hoặc message bus*

- Instance ghi `PUBLISH invalidate product:1`; mọi instance đều `SUBSCRIBE invalidate` và xoá key
  nhận được khỏi L1 của mình.
- ⚠️ Pub/Sub của Redis là *at-most-once*: docs Redis nói message được gửi một lần nếu có, subscriber
  lỗi hoặc rớt mạng đúng lúc đó thì message "is forever lost". Instance đang reconnect sẽ giữ bản cũ.
  Vì vậy vẫn phải có TTL cho L1 làm lưới an toàn, và nên xoá sạch L1 mỗi khi kết nối subscribe bị
  đứt.
- Docs Redis cũng chỉ ra cái giá: gửi invalidation cho **mọi** client kể cả client không giữ key đó
  (tốn băng thông), và mỗi lần ghi phải thêm một lệnh `PUBLISH`.
- Redis Streams lưu message lại và hỗ trợ cả at-most-once lẫn at-least-once, nên instance
  reconnect có thể đọc lại phần đã lỡ. Kafka cũng vậy. So sánh chi tiết để dành cho bài tập 5 ở
  file plan.
- Trên Redis Cluster, Pub/Sub thường (global) lan message tới mọi node; từ Redis 7.0 có *sharded Pub/Sub*
  (`SPUBLISH`/`SSUBSCRIBE`) giới hạn message trong một shard, giảm tải cho cluster bus.

*Cách 3: Redis client-side caching (tính năng tracking, có từ Redis 6)*

Redis tự làm phần "ai đang giữ key nào", gọi là *tracking*, có hai chế độ:

- Chế độ mặc định: server nhớ client nào đã đọc key nào (mọi key xuất hiện trong lệnh read-only đều
  được coi là "có thể đã cache"). Khi key bị sửa, bị hết hạn, hay bị evict do `maxmemory`, server gửi
  *invalidation message* cho đúng các client đó.
  ```
  Client 1 -> CLIENT TRACKING ON
  Client 1 -> GET foo            (server ghi nhớ: client 1 có thể giữ foo)
  Client 2 -> SET foo other
  Server   -> Client 1: INVALIDATE "foo"
  ```
  - Server giữ các cặp "key, danh sách client id" trong một *Invalidation Table* có giới hạn số mục.
    Bảng đầy thì server bỏ mục cũ bằng cách **giả vờ key đó bị sửa** và gửi invalidation, buộc client
    xoá bản L1 dù dữ liệu không đổi. Số key tối đa chỉnh bằng cấu hình `tracking-table-max-keys`.
  - Bảng không phân biệt số database: sửa `foo` ở DB 3 cũng gửi invalidation cho client cache `foo`
    ở DB 2.
  - `OPTIN`: chỉ track key mà client báo trước bằng `CLIENT CACHING YES` ngay trước lệnh đọc.
    `OPTOUT`: track mọi thứ trừ key bị loại bằng `CLIENT UNTRACKING`.
- Chế độ *broadcasting* (`BCAST`): server không nhớ gì theo từng key. Client đăng ký theo prefix, ví
  dụ `CLIENT TRACKING on REDIRECT 10 BCAST PREFIX object: PREFIX user:`, và nhận invalidation mỗi
  khi bất kỳ key nào khớp prefix bị sửa. Không tốn memory phía server, đổi lại client nhận nhiều
  message thừa, và CPU server tăng theo số prefix đã đăng ký. Hai prefix không được chồng nhau
  (`foo` và `foob` là không hợp lệ).
- `NOLOOP`: không gửi invalidation cho chính connection đã sửa key, dùng khi client tự ghi giá trị
  mới vào L1 của mình lúc ghi.
- Kênh nhận: với RESP3, invalidation đi cùng connection dạng *push message*. Với RESP2 phải dùng
  connection thứ hai `SUBSCRIBE __redis__:invalidate`, rồi connection dữ liệu bật
  `CLIENT TRACKING on REDIRECT <id>`. Đây chỉ là mượn cơ chế Pub/Sub để client cũ dùng được, message
  chỉ tới đúng connection được `REDIRECT`.

⚠️ Race giữa đọc và invalidation khi dùng hai connection (lấy từ docs Redis):

| Bước | Connection dữ liệu (D) | Connection invalidation (I) | L1 |
|---|---|---|---|
| 1 | Gửi `GET foo` | | |
| 2 | | Nhận `INVALIDATE foo` (ai đó vừa sửa) | Không có gì để xoá |
| 3 | Nhận reply cũ `"bar"` | | Ghi `foo = bar`: **cũ mãi** |

Sửa: trước khi gửi `GET`, đặt L1 `foo = "đang nạp"` (placeholder). Invalidation tới thì xoá
placeholder; reply tới mà placeholder đã mất thì **không** ghi vào L1. Dùng một connection cho cả dữ
liệu lẫn invalidation (RESP3) thì không có race này, vì thứ tự message luôn biết trước.

⚠️ Mất kết nối với kênh invalidation: xoá sạch L1, và `PING` định kỳ kênh đó; quá thời gian không
nhận được phản hồi thì đóng connection và xoá L1. Docs giới thiệu của Redis cũng ghi: client library
có hỗ trợ sẽ xoá toàn bộ cache cục bộ khi bất kỳ connection nào bị ngắt.

Client library phải tự cài phần L1 và xử lý invalidation. Docs Redis liệt kê các client có hỗ trợ
từ phiên bản: redis-py 5.1.0, Jedis 5.2.0, node-redis 5.1.0, go-redis 9.22.0. Client chỉ biết gửi
lệnh `CLIENT TRACKING` chưa chắc đã có đủ phần cache phía client.

#### Tính độ cũ tối đa

Câu người phỏng vấn senior muốn nghe là một con số có lập luận. Ví dụ thiết kế cho 20 instance:
L2 là Redis với TTL 10 phút và xoá khi ghi (sau commit), L1 TTL 5 giây, broadcast qua Pub/Sub.

| Trường hợp | Độ cũ của một instance |
|---|---|
| Bình thường | Độ trễ Pub/Sub (thường vài ms) |
| Instance lỡ message (đang reconnect) | Tối đa TTL L1 = 5 giây |
| L2 cũng dính race (module 2.2: ghi cache sau khi đã xoá) | Tối đa TTL L2 + TTL L1 = 10 phút 5 giây |
| Không có broadcast, chỉ có TTL | Tối đa TTL L1 (nếu L2 đúng) |

Cách phát biểu: "Độ cũ tối đa của L1 bằng TTL của L1, cộng với độ cũ của L2 lúc L1 nạp. Broadcast
chỉ làm trường hợp thường tốt hơn, không đổi được cận trên, vì Pub/Sub có thể mất message." Muốn cận
trên nhỏ hơn thì giảm TTL L1 (đổi lại nhiều round-trip hơn) hoặc chọn kênh bền (Streams, Kafka).

#### Chọn gì cho L1

- Hợp với L1: dữ liệu nhỏ, đọc rất nhiều, ít đổi, chấp nhận cũ vài giây. Ví dụ cấu hình, danh mục,
  feature flag, bảng tỉ giá, thông tin sản phẩm đang flash sale (hot key).
- Không hợp: dữ liệu đổi liên tục (docs Redis lấy ví dụ counter được `INCR` liên tục), dữ liệu hiếm
  khi được đọc lại, dữ liệu theo từng user với số lượng lớn.
- ⚠️ Giới hạn kích thước L1 là bắt buộc (số mục hoặc số byte) kèm chính sách evict (LRU, module 2.6).
  L1 nằm trong heap: Java phình heap là GC dài hoặc OOM; mỗi instance một bản nên memory tốn nhân 20.
- ⚠️ L1 trả về **cùng một object** cho nhiều request (Java, Go). Code nào sửa object đó là sửa luôn
  bản trong cache cho mọi người. Lưu object bất biến, hoặc copy khi đọc.
- ⚠️ Dữ liệu cần đọc ngay sau khi ghi (read-your-writes, ví dụ user vừa đổi tên) không nên đi qua L1
  có TTL: request sau có thể rơi vào instance khác vẫn giữ tên cũ.

#### L1 trong PHP

PHP-FPM không có L1 in-process sống qua request (module 2.7). Lựa chọn thực tế:

| Runtime | L1 | Invalidation |
|---|---|---|
| PHP-FPM | APCu (một bản mỗi máy, chung cho các worker) | Gần như chỉ dựa vào TTL ngắn |
| Octane + Swoole | Octane cache (Swoole table) | TTL; có thể chạy một listener Pub/Sub trong process sống lâu |
| Mọi runtime, trong một request | `Cache::memo()`, `once()` | Tự hết khi request xong |

⚠️ Broadcast invalidation vào APCu khó hơn nhiều so với Java: worker FPM không có vòng lặp chạy nền
để `SUBSCRIBE`, và một daemon CLI chạy riêng trên máy cũng **không** xoá được APCu của FPM (CLI có
vùng nhớ riêng, module 2.7). Muốn làm phải cho daemon gọi một endpoint nội bộ trên FPM của chính máy
đó để nó tự `apcu_delete`. Phần lớn đội PHP chọn TTL ngắn cho APCu và chấp nhận cận trên đó.

Ví dụ hai tầng APCu + Redis bằng Laravel, TTL L1 ngắn:

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\Cache;

// Cần khai báo store APCu trong config/cache.php (skeleton không có sẵn):
//   'apc' => ['driver' => 'apc'],

/**
 * Đọc qua hai tầng: APCu (L1, 5 giây) rồi Redis (L2, 600 giây) rồi DB.
 * Độ cũ tối đa trên một server: 5 giây cộng độ cũ của L2.
 */
function featureFlags(): array
{
    $key = 'flags:v1';

    // L1: APCu, riêng từng máy, chung cho mọi worker FPM trên máy đó
    return Cache::store('apc')->remember($key, 5, function () use ($key): array {
        // L2: Redis, dùng chung giữa mọi server
        return Cache::store('redis')->remember($key, 600, function (): array {
            return ['new_checkout' => true]; // thay bằng query DB thật
        });
    });
}

// Khi ghi: xoá L2 sau commit. L1 ở các máy khác tự hết sau tối đa 5 giây.
// DB::afterCommit(fn () => Cache::store('redis')->forget('flags:v1'));
```

Cả hai tầng đều dùng `remember`, nên vẫn có stampede khi key nóng hết hạn (module 2.3); với L1 thì
stampede chỉ xuống tới L2 (Redis), thường chịu được, còn L2 nên dùng `flexible` hoặc lock.

**Tóm tắt nhanh**

- L1 (in-process) bớt round-trip và chắn hot key; L2 (Redis) dùng chung. Đọc L1 → L2 → DB.
- Mỗi instance một bản L1: độ cũ tối đa = TTL L1 + độ cũ của L2. Xoá L2 trước rồi mới báo xoá L1.
- Pub/Sub là at-most-once, nên broadcast chỉ cải thiện trường hợp thường; TTL L1 vẫn là cận trên.
- Redis tracking (Redis 6+): chế độ mặc định nhớ key theo client, BCAST theo prefix; nhớ race
  invalidation tới trước reply (dùng placeholder) và xoá L1 khi mất kết nối.
- L1 chỉ cho dữ liệu nhỏ, đọc nhiều, ít đổi, có giới hạn kích thước. PHP-FPM: APCu với TTL ngắn.

**Nguồn**: [Redis: Client-side caching reference](https://redis.io/docs/latest/develop/reference/client-side-caching/) ·
[Redis: Client-side caching introduction](https://redis.io/docs/latest/develop/clients/client-side-caching/) ·
[Redis: Pub/Sub](https://redis.io/docs/latest/develop/pubsub/) ·
[Laravel 13 Cache](https://laravel.com/docs/13.x/cache) ·
[Laravel Octane: The Octane Cache](https://laravel.com/docs/13.x/octane#the-octane-cache)

---

### 3.2 Nhất quán cache ở quy mô lớn: lease, CDC

Module này trả lời: Facebook đã giải hai race kinh điển của cache-aside (ghi giá trị cũ vào cache
sau khi đã xoá, và stampede) thế nào bằng *lease*, vì sao họ chuyển việc xoá cache từ code sang
commit log của DB (ngày nay gọi là CDC), và làm sao đo được cache lệch DB bao nhiêu.

Bối cảnh từ paper *Scaling Memcache at Facebook* (NSDI 2013): memcache được dùng làm cache
*demand-filled look-aside*, tức cache-aside đúng như module 1.2. Đọc: miss thì web server lấy từ DB
rồi nạp vào cache. Ghi: web server chạy SQL rồi gửi lệnh **xoá** key. Paper giải thích chọn xoá thay
vì cập nhật vì xoá là *idempotent* (làm một lần hay nhiều lần kết quả như nhau), đúng lý do ở
module 2.2.

#### Lease

Paper gọi tên hai vấn đề lease giải quyết:

- *Stale set*: web server ghi vào cache một giá trị không còn là giá trị mới nhất, do các lần cập
  nhật đồng thời bị đảo thứ tự. Đây chính là race "update DB rồi xoá cache" ở module 2.2.
- *Thundering herd*: một key vừa bị đọc vừa bị ghi nhiều; mỗi lần ghi xoá key, và rất nhiều lần đọc
  cùng rơi xuống DB (stampede, module 2.3).

*Lease là gì*: khi client gặp miss, memcached cấp cho client đó một *lease token* (64 bit) gắn với
đúng key đó. Token là "giấy phép ghi giá trị vào key này". Client ghi lại vào cache phải kèm token;
memcached kiểm tra token còn hiệu lực mới nhận. Một lệnh xoá key làm token của key đó mất hiệu lực.
Paper so sánh cơ chế này với *load-link/store-conditional* của CPU: ghi có điều kiện, thất bại nếu
có ai chạm vào ô nhớ từ lúc đọc.

*Lease chặn stale set thế nào*, trên đúng timeline của module 2.2:

| Bước | Client A (ghi) | Client B (đọc) | Cache | Không có lease | Có lease |
|---|---|---|---|---|---|
| 1 | | Đọc `k`, miss | Cấp token T1 cho B | | |
| 2 | | Đọc DB được giá trị cũ `v1` | | | |
| 3 | Update DB thành `v2`, commit | | | | |
| 4 | Xoá `k` | | Key trống; **T1 mất hiệu lực** | | |
| 5 | | `set k = v1` kèm T1 | | Cache giữ `v1` tới hết TTL | Cache **từ chối** |
| 6 | | | Lần đọc sau miss, lấy `v2` từ DB | | Đúng |

Bước bị chặn là bước 5: lệnh ghi cache chậm của B. Điều kiện lỗi ở module 2.2 (B đọc DB trước khi A
ghi, và ghi cache sau khi A xoá) vẫn xảy ra, nhưng hậu quả của nó bị vô hiệu.

*Lease chống thundering herd thế nào*: mỗi memcached server giới hạn tần suất cấp token. Mặc định họ
cấu hình chỉ cấp một token cho mỗi key **mỗi 10 giây**. Request khác miss trong 10 giây đó nhận một
thông báo đặc biệt "chờ một chút rồi thử lại". Paper ghi rằng client giữ token thường nạp xong trong
vài mili giây, nên khi các client kia thử lại, dữ liệu thường đã có. Số liệu trong paper: theo dõi
một tuần các key dễ bị thundering herd, đỉnh query xuống DB là 17K/s khi không có lease và 1,3K/s khi
có lease.

*Stale value*: paper còn cho phép trả dữ liệu hơi cũ. Key bị xoá thì giá trị được chuyển sang một cấu
trúc giữ các mục vừa bị xoá trong thời gian ngắn; lệnh `get` có thể trả về token hoặc giá trị được
đánh dấu là cũ. Ứng dụng chấp nhận được dữ liệu cũ thì dùng luôn, không phải chờ. Ý tưởng giống
stale-while-revalidate (module 2.3).

⚠️ Lease **không phải** distributed lock, và đây là chỗ hay bị nhầm:

| | Distributed lock (module 2.3) | Lease |
|---|---|---|
| Câu hỏi nó trả lời | Ai được **làm việc** (nạp dữ liệu) | Lần ghi cache nào **còn hợp lệ** |
| Người không có quyền | Chờ lock | Chờ ngắn rồi đọc lại (với herd), hoặc bị từ chối ghi (với stale set) |
| Lệnh xoá key | Không liên quan tới lock | Huỷ token, vô hiệu mọi lần ghi đang bay |
| Người giữ chết | Lock tự hết hạn | Token hết hạn, lần sau cấp token mới |
| Chặn được stale set | Không: lock không biết có ai vừa xoá key | Có |

Lock chỉ đảm bảo một người nạp, nhưng người đó vẫn có thể nạp giá trị cũ nếu DB đổi và key bị xoá
trong lúc họ đang nạp. Lease gắn quyền ghi với "không ai xoá key từ lúc tôi miss".

#### Mô phỏng lease trên Redis

Redis không có lease sẵn. Mô phỏng bằng hai script Lua (Lua trong Redis chạy nguyên tử: không lệnh nào
khác chen vào giữa) và một key phụ giữ token:

```lua
-- lease_get.lua
-- KEYS[1] = key dữ liệu, KEYS[2] = key lease
-- ARGV[1] = token ngẫu nhiên do client sinh, ARGV[2] = thời hạn lease (ms)
local v = redis.call('GET', KEYS[1])
if v then
  return {'HIT', v}
end
-- Chưa ai giữ lease thì cấp cho client này. SET NX đảm bảo mỗi key chỉ một lease
-- trong thời hạn PX (tương đương "một token mỗi 10 giây" của paper khi PX = 10000)
if redis.call('SET', KEYS[2], ARGV[1], 'NX', 'PX', ARGV[2]) then
  return {'LEASE', ARGV[1]}
end
return {'WAIT'}
```

```lua
-- lease_set.lua
-- KEYS[1] = key dữ liệu, KEYS[2] = key lease
-- ARGV[1] = token, ARGV[2] = giá trị, ARGV[3] = TTL của dữ liệu (giây)
if redis.call('GET', KEYS[2]) == ARGV[1] then
  redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
  redis.call('DEL', KEYS[2])
  return 1
end
return 0   -- token đã bị huỷ (có người xoá key) hoặc đã hết hạn: bỏ lần ghi này
```

Xoá (invalidate) phải xoá **cả key dữ liệu lẫn key lease** trong một lệnh:

```
DEL product:{1} lease:product:{1}
```

Chạy thử bằng `redis-cli` theo đúng timeline ở trên (với `--eval`, các key đứng trước dấu `,`, các
tham số đứng sau). Giá trị trả về ghi trong comment là suy ra từ logic của script, không phải output
đã chạy:

```sh
redis-cli --eval lease_get.lua 'product:{1}' 'lease:product:{1}' , tokB 10000
# B miss, nhận lease: 1) "LEASE" 2) "tokB"
redis-cli --eval lease_get.lua 'product:{1}' 'lease:product:{1}' , tokC 10000
# C miss trong lúc B giữ lease: 1) "WAIT"
redis-cli DEL 'product:{1}' 'lease:product:{1}'
# A vừa update DB và xoá: huỷ lease của B
redis-cli --eval lease_set.lua 'product:{1}' 'lease:product:{1}' , tokB '{"price":100}' 600
# B ghi giá trị cũ: (integer) 0, bị từ chối
```

Bọc trong PHP (Laravel `Redis` facade, `Redis::eval($script, $soKey, ...$keysVaArgs)`):

```php
<?php
declare(strict_types=1);

use Illuminate\Support\Facades\Redis;

const LEASE_GET = <<<'LUA'
local v = redis.call('GET', KEYS[1])
if v then return {'HIT', v} end
if redis.call('SET', KEYS[2], ARGV[1], 'NX', 'PX', ARGV[2]) then return {'LEASE', ARGV[1]} end
return {'WAIT'}
LUA;

const LEASE_SET = <<<'LUA'
if redis.call('GET', KEYS[2]) == ARGV[1] then
  redis.call('SET', KEYS[1], ARGV[2], 'EX', ARGV[3])
  redis.call('DEL', KEYS[2])
  return 1
end
return 0
LUA;

/** @param callable(): string $load hàm đọc DB, trả chuỗi JSON */
function getWithLease(string $id, callable $load): string
{
    // Hash tag {id}: hai key cùng slot, để script chạy được trên Redis Cluster
    $key = sprintf('product:{%s}', $id);
    $leaseKey = sprintf('lease:product:{%s}', $id);

    for ($attempt = 0; $attempt < 20; $attempt++) {
        $token = bin2hex(random_bytes(16));
        $reply = Redis::eval(LEASE_GET, 2, $key, $leaseKey, $token, 10_000);

        if ($reply[0] === 'HIT') {
            return $reply[1];
        }
        if ($reply[0] === 'LEASE') {
            $fresh = $load();
            // Bị từ chối (trả 0) cũng không sao: request này vẫn dùng $fresh,
            // chỉ là cache không bị ghi giá trị có thể đã cũ
            Redis::eval(LEASE_SET, 2, $key, $leaseKey, $token, $fresh, 600);
            return $fresh;
        }
        usleep(50_000); // WAIT: người giữ lease đang nạp, chờ 50 ms rồi đọc lại
    }

    return $load(); // chờ quá lâu (người giữ lease có thể đã chết): tự đọc DB
}

/** Gọi SAU khi transaction commit, ví dụ trong DB::afterCommit */
function invalidateProduct(string $id): void
{
    Redis::del(sprintf('product:{%s}', $id), sprintf('lease:product:{%s}', $id));
}
```

Các điểm cần để ý:

- ⚠️ Hai key trong một script phải cùng slot trên Redis Cluster, nên dùng *hash tag* (phần trong
  `{}` quyết định slot). Ở đây `{1}` chung cho cả hai key.
- ⚠️ Lệnh xoá mà quên xoá key lease thì lease không bị huỷ, và stale set lại xảy ra. Gom việc xoá vào
  một hàm duy nhất như `invalidateProduct`.
- Dùng cùng một connection cho cả ba thao tác, để prefix (nếu có) áp dụng giống nhau.
- Thời hạn lease (`PX`) phải lớn hơn thời gian nạp bình thường; người giữ chết thì sau thời hạn đó
  người khác lấy được lease.
- Đây vẫn là cache-aside, chỉ thêm điều kiện khi ghi. Nó không cho nhất quán mạnh: giữa lúc DB commit
  và lúc lệnh xoá tới Redis, người đọc vẫn thấy giá trị cũ.

#### Invalidation qua commit log

*Cách của Facebook (mcsqueal)*. Trong một region, cụm lưu trữ (MySQL) giữ bản gốc và chịu trách
nhiệm invalidate cache ở các cụm frontend:

1. Câu SQL sửa dữ liệu được đính kèm danh sách key memcache cần xoá khi transaction commit.
2. Trên mỗi DB chạy một daemon tên *mcsqueal*. Nó đọc các câu SQL mà DB đã commit, rút ra các lệnh
   xoá, rồi phát tới memcache ở mọi cụm frontend trong region.
3. Để giảm số packet, mcsqueal gom các lệnh xoá thành lô, gửi tới các server chạy *mcrouter* ở mỗi
   cụm; mcrouter tách lô ra và gửi từng lệnh xoá tới đúng memcached. Paper ghi việc gom lô cải thiện
   18 lần số lệnh xoá trung vị mỗi packet.
4. Web server sửa dữ liệu vẫn tự gửi lệnh xoá cho cụm của chính nó, để chính user đó đọc lại thấy
   ngay giá trị mới (read-after-write).

Paper nêu hai lý do không để web server tự phát lệnh xoá cho mọi cụm: web server gom lô kém hơn, và
khi có lỗi hệ thống (ví dụ cấu hình sai làm lệnh xoá đi nhầm chỗ) thì gần như không có cách khắc
phục; trước đây việc này thường phải rolling restart cả hạ tầng memcache. Ngược lại, lệnh xoá nằm trong log của DB, vốn bền, nên mcsqueal chỉ cần
**phát lại** các lệnh bị mất hay đi nhầm. Một con số đáng nhớ: chỉ 4% lệnh xoá thực sự xoá một giá trị
đang có trong cache.

*Ngày nay: CDC*. *Change Data Capture* là đọc log thay đổi của DB (binlog của MySQL, WAL của
Postgres) và biến mỗi thay đổi đã commit thành một sự kiện cho hệ thống khác dùng: index tìm kiếm,
data warehouse, và cache. DDIA ch.11 coi cache là một dạng *derived data* (dữ liệu dẫn xuất), và
CDC là cách giữ chúng đồng bộ với nguồn sự thật theo đúng thứ tự thay đổi.

```
 app --UPDATE--> MySQL --binlog (ROW)--> Debezium / Canal --> Kafka --> consumer
                                                                         |
                                           map dòng đổi -> các key cache  |
                                                                         v
                                                                 DEL trên Redis
```

- *Debezium*: đọc binlog MySQL (hoặc WAL Postgres), thường đẩy sự kiện vào Kafka. *Canal* (của
  Alibaba): giả làm một replica MySQL để nhận binlog.
- Cần binlog dạng ROW (mặc định của MySQL 8.x) để sự kiện có đủ giá trị dòng; chi tiết binlog ở
  [03-database-sql.md](03-database-sql.md#31-bên-trong-innodb-log-bộ-nhớ-mvcc).
- Consumer biến "dòng `products` id 1 đổi" thành danh sách key cần xoá, rồi xoá (nên kèm xoá key
  lease nếu dùng lease).

| | Xoá trong code | Xoá qua CDC |
|---|---|---|
| Độ trễ | Ngay sau ghi | Thêm độ trễ của pipeline (đọc binlog, Kafka, consumer) |
| Độ phủ | Chỉ các đường ghi có gọi xoá | Mọi thay đổi đã commit, kể cả sửa tay, script, service khác ghi chung DB |
| Thời điểm | Dễ lỡ xoá trước commit (module 2.2) | Chỉ thấy thay đổi đã commit |
| Mất lệnh xoá | Redis timeout là mất, trừ khi tự retry | Log bền, consumer lỗi thì đọc lại từ offset cũ |
| Độ phức tạp | Logic xoá rải trong code | Thêm hạ tầng (connector, Kafka, consumer), phải giám sát lag |
| Điểm lỗi | Mỗi đường ghi là một chỗ có thể quên | Map từ dòng sang key: key danh sách, key tổng hợp khó suy ra từ một dòng |

Thực tế thường kết hợp: code xoá ngay sau commit để user thấy thay đổi của mình nhanh (giống web
server của Facebook xoá cụm của chính nó), và CDC làm lưới an toàn bắt mọi thay đổi còn lại.

⚠️ CDC không xoá race đọc-ghi: người đọc miss, đọc DB trước commit, ghi cache sau khi CDC đã xoá
vẫn để lại giá trị cũ. CDC giải "xoá có tới và tới sau commit không"; lease giải "lần ghi cache chậm
có bị chặn không". Hai thứ bổ sung cho nhau.

#### Đo độ nhất quán

Bài *Cache made consistent* của Meta (2022, về TAO, hệ thống cache đồ thị của họ) đưa ra hai ý:

- Race gốc vẫn là loại đã gặp: cache đang nạp `x` từ DB; trước khi kết quả `x = 42` tới, ai đó sửa
  thành 43; sự kiện invalidate cho 43 tới cache **trước**; rồi kết quả nạp 42 mới tới và ghi đè. DB là
  43, cache giữ 42 vô thời hạn. Một cách giải là thêm version để giải xung đột (bản cũ không được ghi
  đè bản mới), nhưng nếu mục mang version mới bị evict khỏi cache trước khi dữ liệu cũ tới thì cache
  không còn biết đã có bản mới hơn.
- *Polaris*, dịch vụ đo: nhận sự kiện invalidation (ví dụ `x = 4 @version 4`), rồi hỏi các bản sao
  cache xem có trả giá trị cũ hơn không. Để tránh báo nhầm do đang lag, nó đo theo nhiều khung thời
  gian (bài viết lấy ví dụ 1 phút, 5 phút, 10 phút) và thử lại trước khi phải hỏi thẳng DB, vì lệch thật và
  ghi đua trên cùng key đều hiếm.
- Kết quả bài viết công bố (theo một thước đo, qua nhiều năm): tỉ lệ nhất quán của TAO từ 99,9999% (6 số 9) lên 99,99999999% (10 số 9),
  tức ít hơn 1 trên 10 tỉ lần ghi cache còn lệch sau 5 phút.
- Họ thêm *consistency tracing*: không log mọi thao tác (quá lớn), chỉ log các thay đổi cache trong
  khoảng thời gian ngắn quanh lúc ghi, nơi race xảy ra. Nhờ đó một bug thật (nhánh xử lý lỗi của
  invalidation gọi "xoá nếu version nhỏ hơn", nhưng bản cũ trong cache lại mang version mới nhất nên
  không bị xoá) được tìm ra trong chưa tới 30 phút.

Áp dụng ở quy mô nhỏ hơn (gợi ý, không phải từ bài viết): một job lấy mẫu ngẫu nhiên vài trăm key mỗi
phút, đọc cache và DB (từ primary), bỏ qua key vừa được ghi trong vài giây gần đây, đếm số ca lệch
thành metric. Metric này biến "cache có nhất quán không" từ cảm giác thành con số, và báo động khi một
deploy làm hỏng invalidation.

#### Nhiều region

Paper mô tả kiến trúc: một region giữ DB master, các region khác giữ replica chỉ đọc (MySQL
replication). Mọi thách thức nhất quán ở đây xuất phát từ một chuyện: **replica có thể lag** so với
master (DDIA ch.5, và [03 module 3.4](03-database-sql.md#34-replication-và-failover)).

*Ghi từ region master*: nếu web server ở master tự gửi lệnh xoá sang region replica, lệnh xoá có thể
tới **trước** dữ liệu mới. Request ở region replica miss, đọc replica chưa có thay đổi, và nạp lại
giá trị cũ. Việc để mcsqueal chạy trên chính các DB replica giải được race này: lệnh xoá đi cùng luồng
replication, nên chỉ tới cache khi replica đã có dữ liệu mới.

*Ghi từ region không phải master*: user ở region phụ vừa sửa dữ liệu (ghi đi về master), replica
local chưa kịp nhận. Request tiếp theo của user đó đọc replica sẽ thấy dữ liệu cũ và còn nạp nó vào
cache. Paper dùng *remote marker*:

1. Web server đặt một marker `r_k` trong region (lưu ở regional pool của memcache).
2. Ghi xuống master, trong câu SQL kèm cả `k` và `r_k` là thứ cần invalidate.
3. Xoá `k` ở cụm local.
4. Request sau miss `k`: nếu thấy `r_k` còn thì đọc từ **master region** (chậm hơn nhưng mới), không
   thì đọc replica local.
5. Khi câu SQL đó được replicate tới region này, mcsqueal ở DB replica phát lệnh xoá `r_k` (vì
   `r_k` nằm trong danh sách invalidate của câu SQL), và từ đó request lại đọc replica local.

Đánh đổi paper nêu rõ: thêm latency khi miss để giảm xác suất đọc dữ liệu cũ. Paper cũng thừa nhận
cơ chế có thể lộ dữ liệu cũ khi hai thao tác cùng sửa một key (một bên xoá marker mà bên kia vẫn
cần), và marker bị evict thì mất tác dụng; trong thực tế cả hai đều hiếm. Điểm tinh tế: với cache
thường, xoá hay evict key luôn an toàn (chỉ tăng tải DB); với remote marker thì evict làm **giảm** độ
nhất quán.

Đối chiếu với thứ quen thuộc hơn: remote marker là một cách làm *read-your-writes* (đọc lại thấy
thay đổi của chính mình), cùng họ với "sau khi ghi thì đọc từ primary trong N giây" hay tuỳ chọn
`sticky` của Laravel ([03 module 2.7](03-database-sql.md#27-tầng-php-pdo-và-laravel)).

Mô hình tổng thể paper tự nhận là *best-effort eventual consistency*, ưu tiên hiệu năng và tính sẵn
sàng. Khi component phía sau không phản hồi, DB và mcrouter đệm các lệnh xoá rồi phát lại khi nó
sống lại; trong lúc đó xác suất đọc dữ liệu cũ tăng lên.

**Tóm tắt nhanh**

- Lease = token cấp khi miss, lệnh xoá huỷ token, ghi cache phải kèm token còn hiệu lực: chặn đúng
  bước "ghi cache chậm sau khi đã xoá". Giới hạn một token mỗi 10 giây mỗi key thì chống luôn
  thundering herd (paper: đỉnh DB từ 17K/s xuống 1,3K/s).
- Lease khác lock: lock quyết định ai được nạp, lease quyết định lần ghi nào còn hợp lệ.
- Redis mô phỏng lease bằng Lua: `SET NX PX` key phụ khi miss, set có điều kiện so token, xoá
  `DEL` cả key lẫn key lease; dùng hash tag trên Cluster.
- Xoá qua commit log (mcsqueal, nay là CDC với Debezium/Canal): phủ mọi thay đổi, chỉ sau commit,
  phát lại được; đổi lại thêm độ trễ và hạ tầng. Thường kết hợp với xoá trong code.
- Đo, không đoán: Meta đưa TAO từ 6 lên 10 số 9 nhờ Polaris và consistency tracing. Nhiều region:
  lệnh xoá đi theo replication, remote marker cho read-your-writes.

**Nguồn**: [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala)
(mục 2, 3.2.1, 4.1, 5) ·
[Meta Engineering: Cache made consistent](https://engineering.fb.com/2022/06/08/core-infra/cache-made-consistent/) ·
[Laravel 13 Redis](https://laravel.com/docs/13.x/redis) ·
*Designing Data-Intensive Applications* ch.11 (Change Data Capture), ch.5 (replication lag)

---

### 3.3 Khi cache trở thành phụ thuộc bắt buộc

Module này trả lời: nếu Redis sập hoặc chậm hẳn đi, hệ thống của bạn còn sống không, dựa vào số
liệu nào để khẳng định điều đó, và phải thiết kế gì để câu trả lời là "có".

#### Câu hỏi thật

Cache thường được giới thiệu là "tầng tối ưu": có thì nhanh hơn, không có thì chậm hơn nhưng vẫn
đúng. Điều đó chỉ đúng lúc mới bật cache. Sau vài tháng chạy với hit ratio cao, đội vận hành thu nhỏ
DB (hoặc không nâng cấp nó) vì DB "đang rảnh". Lúc đó DB chỉ còn được sizing cho phần miss.

Phép tính cần làm được ngay trong phỏng vấn: với hit ratio `h`, DB nhận tỉ lệ `1 - h` số lần đọc.

| Hit ratio trước sự cố | DB thấy bình thường | Mất cache hoàn toàn | Hệ số tăng tải đọc lên DB |
|---|---|---|---|
| 90% | 10% | 100% | 10 lần |
| 95% | 5% | 100% | 20 lần |
| 99% | 1% | 100% | 100 lần |

Hai hệ quả không trực giác:

- Hit ratio càng cao thì cú sốc khi mất cache càng lớn. Cache càng "tốt", DB càng phụ thuộc vào nó.
- Không cần mất cache hoàn toàn mới đau: hit ratio tụt từ 99% xuống 98% là tải đọc lên DB gấp đôi,
  dù dashboard hit ratio chỉ nhích 1 điểm.

Từ đó ra định nghĩa: cache là *phụ thuộc bắt buộc* (hard dependency) khi hệ thống không chịu nổi việc
mất nó. Không có gì sai khi chấp nhận điều này, nhưng phải chấp nhận có ý thức, và khi đó cache phải
được vận hành như một DB: có HA, có giám sát, có capacity plan, có runbook sự cố. Đáp án kém nhất là
"cache chỉ là cache, sập thì đọc DB", nói ra mà chưa từng đo DB chịu được bao nhiêu.

⚠️ Hit ratio tính theo số request, không theo chi phí. Các key bị miss khi cache sập có thể chính là
các query nặng nhất (key có TTL dài, tổng hợp nhiều bảng). Hệ số thật trên CPU của DB có thể lớn hơn
con số trong bảng. Ngoài ra, buffer pool của DB đang "lạnh" với những dữ liệu vốn chỉ nằm trong cache,
nên query cũng chậm hơn bình thường.

#### Redis HA

Bước đầu tiên để cache ít khi sập là không để Redis chạy một node. Hai cách chính (chi tiết ở plan
[04-nosql-search-storage.md](../04-nosql-search-storage.md), module 3.2):

- *Replication + Sentinel*: một master, một hoặc nhiều replica. Sentinel là tiến trình riêng làm bốn
  việc: giám sát master/replica, gửi thông báo, tự failover (nâng replica lên master), và làm "nguồn
  cấu hình" để client hỏi địa chỉ master hiện tại.
- *Redis Cluster*: chia keyspace thành slot trên nhiều master, mỗi master có replica, cluster tự
  failover không cần Sentinel.

Những điểm docs Redis nhấn mạnh về Sentinel, hay bị hỏi:

- Cần ít nhất ba tiến trình Sentinel, đặt trên các máy hỏng độc lập nhau (khác máy vật lý, khác
  availability zone). Hai Sentinel là cấu hình hỏng: mất máy chứa master thì cũng mất một Sentinel,
  Sentinel còn lại không đủ đa số để cho phép failover.
- Tham số *quorum* chỉ dùng để phát hiện lỗi (bao nhiêu Sentinel cùng đồng ý master không liên lạc
  được). Để thật sự failover, một Sentinel phải được bầu làm leader bằng phiếu của đa số các tiến trình
  Sentinel. Phía thiểu số trong network partition không bao giờ tự failover.
- `down-after-milliseconds` là thời gian một instance không trả lời thì Sentinel bắt đầu coi là down.
  Tổng thời gian failover gồm thời gian phát hiện này cộng bầu leader cộng nâng replica, nên luôn có
  một khoảng Redis không nhận ghi. App phải sống qua khoảng đó.
- Client phải hỗ trợ Sentinel (hỏi Sentinel để tìm master mới). Không phải thư viện nào cũng có.
- Docs Redis cảnh báo: HA chưa từng được test thì không tính là HA; cấu hình sai chỉ lộ ra khi master
  chết thật.

Failover có thể mất ghi. Replication của Redis mặc định là async: master trả OK cho client trước khi
replica nhận được lệnh. Master chết ngay sau đó thì replica được nâng lên không có lệnh ấy. Lệnh
`WAIT` và cặp `min-replicas-to-write` / `min-replicas-max-lag` chỉ thu hẹp cửa sổ mất dữ liệu, docs
nói rõ chúng không biến Redis thành hệ nhất quán mạnh.

Với cache thì mất vài lệnh `SET` thường chấp nhận được, vì nguồn sự thật nằm ở DB: lần đọc sau miss
và nạp lại. Nhưng cần nghĩ tiếp ba trường hợp:

- Mất một lệnh xoá. Invalidation (`DEL`) cũng là một lệnh ghi. Nếu lệnh xoá đã được master cũ xác
  nhận rồi mất trong failover, master mới vẫn giữ giá trị cũ và phục vụ nó tới hết TTL. Đây là thêm
  một lý do TTL luôn phải có, kể cả khi đã xoá chủ động (module 2.2).
- Lock trong Redis (`Cache::lock`, lock chống stampede) có thể mất khi failover: hai request cùng
  nghĩ mình giữ lock. Dùng để chống stampede thì chấp nhận được (chỉ thêm một lần rebuild); dùng để
  bảo vệ tính đúng của nghiệp vụ thì không.
- Redis dùng chung cho queue, session: mất ghi lúc đó là mất job, mất phiên đăng nhập. Tách instance
  cache khỏi queue/session để mỗi thứ có mức chịu mất dữ liệu riêng (xem
  [2.7 Cache trong PHP/Laravel](#27-cache-trong-phplaravel)).

⚠️ "Có replica rồi nên không sập" là red flag. Replica giảm xác suất mất hẳn Redis nhưng không loại
trừ: failover mất thời gian, cả cụm có thể cùng hết memory, cùng bị một lệnh chặn, cùng nhận một cấu
hình sai, hoặc mạng giữa app và Redis có vấn đề.

#### Hành vi khi Redis chậm hoặc chết

Redis chậm thường nguy hiểm hơn Redis chết hẳn. Tiến trình Redis chết mà máy vẫn sống thì kết nối
thường bị từ chối ngay, app biết ngay (còn nếu cả máy hoặc đường mạng mất, gói tin bị bỏ, thì kết nối
cũng treo tới timeout y như trường hợp chậm). Chậm thì mỗi request treo tới hết timeout, giữ worker PHP-FPM, và khi mọi worker đều đang chờ Redis thì
app ngừng phục vụ dù DB vẫn khoẻ. Bốn lớp phòng thủ, từ trong ra ngoài:

```
request
  │
  ├─ 1. timeout ngắn cho Redis (vài chục tới vài trăm ms, không phải giây)
  │
  ├─ 2. circuit breaker: lỗi liên tục -> "mở mạch", bỏ qua Redis một lúc
  │
  ├─ 3. coi như miss, nhưng giới hạn lượng request được xuống DB
  │        vượt giới hạn -> trả dữ liệu dự phòng, degrade, hoặc 503 cho tính năng phụ
  │
  └─ 4. store phụ: L1 (APCu/Octane), hoặc Laravel failover store
```

*1. Timeout ngắn.* Đặt timeout kết nối và timeout đọc tường minh cho connection dùng làm cache, ngắn
hơn nhiều so với connection dùng cho queue. Với phpredis trong Laravel, các option `timeout` và
`read_timeout` khai báo trong `config/database.php` (docs Laravel liệt kê chúng trong danh sách tham
số PhpRedis). Cũng để ý retry: file `config/database.php` mặc định của Laravel 13 đặt
`max_retries` là 3 kèm backoff (`decorrelated_jitter`) cho cả connection `default` lẫn `cache`. Retry
hợp lý với lỗi mạng thoáng qua, nhưng khi Redis chết hẳn thì mỗi lệnh cache tốn vài lần timeout cộng
thời gian backoff trước khi báo lỗi. Với connection cache, cân nhắc giảm retry.

*2. Circuit breaker.* Sau N lỗi liên tiếp, ngừng gọi Redis trong một khoảng (mạch "mở"), mọi request
đi thẳng đường dự phòng mà không phải chờ timeout. Hết khoảng đó thì cho vài request thử lại (trạng
thái "nửa mở"); thành công thì đóng mạch. Với PHP-FPM có một cái bẫy: mỗi request là một vòng đời
riêng, biến PHP không sống qua request, nên trạng thái breaker phải nằm ở chỗ dùng chung giữa các
worker, ví dụ APCu (không thể nằm trong chính Redis đang chết).

Phác thảo bằng PHP để thấy ý tưởng (chưa chạy thử; cần extension APCu; phần "nửa mở" làm đơn giản:
hết hạn mở mạch là mọi request cùng thử lại):

```php
<?php
declare(strict_types=1);

// Breaker đặt trạng thái trong APCu: dùng chung giữa các worker FPM trên CÙNG một máy.
final class RedisBreaker
{
    private const FAILURES = 'breaker:redis:failures';
    private const OPEN_UNTIL = 'breaker:redis:open_until';

    public function __construct(
        private readonly int $failureThreshold = 5,
        private readonly int $openSeconds = 10,
    ) {}

    public function isOpen(): bool
    {
        $until = apcu_fetch(self::OPEN_UNTIL);   // miss thì trả false
        return is_int($until) && $until > time();
    }

    public function recordFailure(): void
    {
        apcu_add(self::FAILURES, 0, 60);          // tạo bộ đếm nếu chưa có, sống 60 giây
        $n = apcu_inc(self::FAILURES);
        if ($n !== false && $n >= $this->failureThreshold) {
            apcu_store(self::OPEN_UNTIL, time() + $this->openSeconds);
            apcu_delete(self::FAILURES);
        }
    }

    public function recordSuccess(): void
    {
        apcu_delete(self::FAILURES);
    }
}
```

Dùng quanh lời gọi cache: nếu `isOpen()` thì bỏ qua Redis; nếu gọi Redis ném exception thì
`recordFailure()` rồi đi đường dự phòng. Mỗi máy có breaker riêng, nên với 20 máy thì Redis nhận tối
đa 20 "đợt thử" mỗi chu kỳ, không phải hàng nghìn.

*3. Coi như miss, có giới hạn.* Bỏ qua Redis nghĩa là mọi request xuống DB, đúng kịch bản trong bảng
ở trên (gấp 20 lần với hit ratio 95%). Phải có giới hạn:

- Giới hạn số truy vấn đồng thời xuống DB (connection pool có trần, hoặc semaphore cục bộ). Với
  PHP-FPM, tổng số worker trên mọi máy đã là trần tự nhiên của số kết nối DB đồng thời; tính xem trần
  đó có vượt sức DB không.
- Load shedding: vượt giới hạn thì từ chối sớm, ưu tiên luồng chính (thanh toán, đăng nhập), tắt tính
  năng phụ (gợi ý, bộ đếm lượt xem).
- ⚠️ Không dùng lock trong Redis để giới hạn: Laravel `Cache::lock` và `Cache::funnel` cần store hỗ
  trợ lock, mà store đó đang chết.

*4. Store phụ.* L1 cache ([3.1](#31-multi-level-cache-l1--l2)) tiếp tục phục vụ các key nhỏ, ít đổi
khi L2 mất. Laravel có driver `failover`: khai báo danh sách store theo thứ tự, store đầu lỗi thì
dùng store kế tiếp, và phát event `Illuminate\Cache\Events\CacheFailedOver` để bạn log hoặc alert.
Cấu hình ví dụ trong docs Laravel:

```php
// config/cache.php (trích từ docs Laravel)
'failover' => [
    'driver' => 'failover',
    'stores' => [
        'database',
        'array',
    ],
],
// .env: CACHE_STORE=failover
```

Đọc source `Illuminate\Cache\FailoverStore` (Laravel 13) thấy ba điều cần biết trước khi tin vào nó:

- Mỗi thao tác đều thử lại từ store đầu tiên trong danh sách, bắt mọi `Throwable` rồi chuyển sang
  store kế tiếp. Không có circuit breaker bên trong: Redis chết thì mỗi lệnh vẫn phải chờ Redis báo
  lỗi trước. Timeout ngắn (lớp 1) là điều kiện để failover store có ích.
- Store dự phòng là `database` nghĩa là dồn tải cache vào chính DB bạn đang muốn bảo vệ. Hợp lý khi
  DB dư sức, nguy hiểm khi DB vốn chỉ sống nhờ cache.
- Store `array` chỉ sống trong một request (với PHP-FPM), nên về bản chất là "coi như miss" cộng
  memo trong request.

#### Đo, không đoán

"DB chịu được khi mất cache" là một giả thuyết cho tới khi có load test chứng minh. Bài load test tối
thiểu:

1. Môi trường gần giống production về cấu hình DB (cùng loại máy, cùng kích thước dữ liệu, cùng
   index). DB nhỏ hơn cho kết quả vô nghĩa.
2. Tải mô phỏng traffic thật: tỉ lệ endpoint, phân bố key (có key nóng), không phải một endpoint lặp
   lại.
3. Hạ hit ratio có kiểm soát: thêm cờ cho phép bỏ qua cache với xác suất `p`, tăng dần `p` để hit
   ratio đi từ 95% xuống 90%, 75%, 50%, 0%. Mỗi bậc giữ đủ lâu để hệ thống ổn định.
4. Ở mỗi bậc ghi lại: CPU và số kết nối của DB, p99 latency của API, tỉ lệ lỗi, số worker FPM bận.
5. Kết quả là một con số dùng được: "DB chịu tới hit ratio X% mà vẫn trong SLO". Nếu X cao (ví dụ phải
   giữ trên 80%), thì cache là phụ thuộc bắt buộc, và HA, breaker, load shedding không còn là tuỳ chọn.
6. Chạy thêm một kịch bản "Redis chậm" (chèn độ trễ mạng tới Redis thay vì tắt hẳn) để kiểm tra
   timeout và breaker thật sự hoạt động.

Kiểm tra tương tự ở production thì làm như một bài diễn tập có kế hoạch (plan
[18-reliability-observability.md](../18-reliability-observability.md), module 3.5 Resilience
testing), bắt đầu từ phạm vi nhỏ.

#### Phục hồi sau sự cố

Redis sống lại không có nghĩa là sự cố kết thúc. Hai vấn đề mới xuất hiện:

*Cache trống, cả cụm cùng nạp lại.* Nếu Redis restart không có persistence, mọi key cùng miss: đúng
kịch bản avalanche ([2.3](#23-stampede-penetration-avalanche)). Cách làm:

- Mở lại traffic dần (ví dụ tắt breaker theo từng nhóm máy, hoặc tăng dần tỉ lệ request được dùng
  Redis), thay vì bật 100% cùng lúc.
- Nạp trước (pre-warm) các key nóng nhất từ một danh sách đã biết, bằng job chạy có giới hạn tốc độ.
- TTL có jitter cho các key nạp lại, để chúng không cùng hết hạn lần nữa sau đúng một TTL.

*Cache sống lại nhưng giữ dữ liệu cũ.* Nếu Redis chỉ mất kết nối (network partition) chứ không
restart, dữ liệu trong nó vẫn còn nguyên, nhưng các lệnh xoá phát ra trong lúc mất kết nối đã thất bại
(hoặc đi vào store phụ). Khi kết nối trở lại, app đọc lại các giá trị đã lỗi thời. Cách xử lý: tăng
version trong prefix key (versioned key, module 2.5) để bỏ toàn bộ dữ liệu cũ, hoặc chấp nhận độ cũ
bằng TTL nếu nghiệp vụ cho phép.

Facebook gặp đúng vấn đề nạp lại ở quy mô lớn. Paper memcache mô tả hai cơ chế đáng kể lại:

- *Gutter pool* (mục 3.3): một nhóm máy nhỏ, khoảng 1% số máy memcached trong cluster, nằm chờ sẵn.
  Client gọi một máy memcached mà không nhận được phản hồi thì coi máy đó hỏng và gửi lại request tới
  Gutter. Gutter cũng miss thì client đọc DB rồi ghi vào Gutter. Giá trị trong Gutter hết hạn nhanh
  để khỏi phải invalidate, đổi lại là dữ liệu hơi cũ. Paper giải thích vì sao không chia lại key cho
  các máy còn sống (rehash): một key nóng có thể chiếm 20% request của một máy, máy nào nhận key đó
  cũng có thể quá tải theo, thành lỗi dây chuyền. Theo paper, Gutter giảm 99% lỗi mà client thấy, và
  khi một máy chết hẳn thì hit rate trong Gutter thường vượt 35% trong chưa tới 4 phút.
- *Cold Cluster Warmup* (mục 4.3): cluster mới hoặc vừa hỏng có cache trống. Thay vì đọc DB, client
  ở cluster "lạnh" lấy dữ liệu từ cluster "ấm" (hit rate bình thường) rồi ghi vào cluster lạnh. Cách
  này đưa cluster lạnh về đủ công suất trong vài giờ thay vì vài ngày. Race cần xử lý: giá trị lấy từ
  cluster ấm có thể đã cũ. Họ giải bằng lệnh xoá có *hold-off* hai giây: trong hai giây sau khi xoá,
  lệnh `add` vào key đó bị từ chối, client hiểu là DB có dữ liệu mới hơn và đọc lại từ DB. Tắt cơ chế
  này khi hit rate của cluster lạnh đã ổn định.

Bài học mang về hệ thống nhỏ hơn: cần có một nơi "hứng" tải khi cache hỏng (L1, store phụ) thay vì đổ
thẳng vào DB, và nạp lại cache là một thao tác cần kiểm soát tốc độ, không phải chuyện tự nhiên.

*Postmortem.* Câu hỏi đúng không phải "vì sao Redis sập" (lần sau nó vẫn có thể sập) mà là "vì sao
một lượt miss làm sập DB". Sửa gốc: query chậm, thiếu index, endpoint gọi quá nhiều query, không có
giới hạn đồng thời. ⚠️ "Tăng TTL" hoặc "thêm RAM cho Redis" không sửa gì: DB vẫn sập ở lần mất cache
tiếp theo. Quy trình postmortem ở plan [18-reliability-observability.md](../18-reliability-observability.md)
(module 2.8).

**Tóm tắt nhanh**

- Hit ratio `h` nghĩa là DB chỉ thấy `1 - h` lượt đọc: 95% thì mất cache là DB gấp 20 lần tải, và
  hit ratio càng cao thì cú sốc càng lớn.
- Cache mà hệ thống không sống nổi khi thiếu là phụ thuộc bắt buộc: vận hành như DB (HA, giám sát,
  capacity plan) và chứng minh bằng load test hạ dần hit ratio.
- Sentinel cần ít nhất 3 tiến trình trên máy độc lập; replication async nên failover có thể mất ghi,
  kể cả lệnh xoá cache, vì vậy TTL vẫn bắt buộc.
- Redis chậm nguy hiểm hơn Redis chết: timeout ngắn, circuit breaker (trạng thái dùng chung giữa
  worker, ví dụ APCu), coi như miss nhưng giới hạn tải xuống DB, store phụ.
- Laravel failover store luôn thử store chính trước và không có breaker; store dự phòng `database` là
  dồn tải vào chính DB.
- Phục hồi: warm-up dần, pre-warm key nóng, jitter; postmortem hỏi vì sao DB không chịu nổi một lượt
  miss (gutter pool, cold cluster warmup là lời giải của Facebook).

**Nguồn**: [Scaling Memcache at Facebook](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala) (mục 3.3 Handling Failures, 4.3 Cold Cluster Warmup) · [Redis: High availability with Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/) · [Redis: Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/) · [Laravel: Cache Failover](https://laravel.com/docs/cache#cache-failover) · [Laravel: Redis](https://laravel.com/docs/redis) · [Laravel source: FailoverStore.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Cache/FailoverStore.php)
