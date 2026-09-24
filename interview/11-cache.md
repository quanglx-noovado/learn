# 11. Cache

> [← Mục lục](README.md) · Phạm vi: các tầng cache, pattern đọc/ghi, invalidation và race condition, sự cố kinh điển (stampede, penetration, avalanche, hot/big key), eviction, multi-level cache, đo lường, cache trong Laravel/Spring/Go.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Tầng cache**
- [ ] 🟢 Browser, CDN, reverse proxy, app in-process, distributed (Redis), DB buffer pool
- [ ] 🟡 HTTP caching: `Cache-Control`, `ETag`, `Vary` (chi tiết ở [02-networking.md](02-networking.md))

**Pattern**
- [ ] 🟢 Cache-aside (lazy loading)
- [ ] 🟡 Read-through, write-through, write-behind, refresh-ahead

**Invalidation**
- [ ] 🟢 TTL, chọn TTL, jitter
- [ ] 🟡 Explicit delete, versioned key, 🔴 event-driven/CDC
- [ ] ⚠️ Update DB rồi xoá cache vs xoá cache rồi update DB: race condition từng thứ tự
- [ ] 🟡 Delayed double delete
- [ ] ⚠️ Vì sao xoá thay vì set

**Sự cố**
- [ ] 🟡 Stampede / thundering herd: mutex, stale-while-revalidate, probabilistic early expiration
- [ ] 🟡 Penetration: cache null, Bloom filter
- [ ] 🟡 Avalanche: jitter, HA, circuit breaker
- [ ] 🟡 Hot key, 🟡 big key

**Eviction**
- [ ] 🟢 LRU, LFU, FIFO, TTL
- [ ] 🟡 Cài LRU `O(1)`: hash map + doubly linked list
- [ ] 🟡 Chính sách `maxmemory-policy` của Redis

**Vận hành**
- [ ] 🟡 Serialization, key naming, namespace
- [ ] 🟡 Cache danh sách, số đếm; timeout và pipeline khi gọi cache
- [ ] 🟡 Cache warming, cache tag
- [ ] 🔴 Multi-level cache (L1 in-process + L2 Redis), nhất quán giữa các node
- [ ] 🟡 Đo hit ratio, latency, memory
- [ ] ⚠️ Khi nào KHÔNG nên cache
- [ ] 🟡 Cache trong Laravel, Spring, Go

## Chi tiết

### Tầng cache

- [ ] Từ gần user tới gần dữ liệu

  | Tầng | Ví dụ | Ai invalidate | Ghi chú |
  |---|---|---|---|
  | Browser | HTTP cache, Service Worker | header, đổi URL | không xoá được từ server; dùng tên file có hash cho asset |
  | CDN | CloudFront, Cloudflare | purge API, TTL | cache theo URL + `Vary`; ⚠️ cache nhầm response có dữ liệu cá nhân |
  | Reverse proxy | Nginx `proxy_cache`, Varnish | TTL, purge | chắn trước app |
  | App in-process | map trong memory, Caffeine, APCu | code | nhanh nhất (không qua mạng), mỗi instance một bản |
  | Distributed | Redis, Memcached | code | dùng chung giữa instance, qua mạng |
  | DB | InnoDB buffer pool, Postgres shared buffers + OS page cache | DB tự quản | "cache miễn phí"; thêm RAM cho DB đôi khi đủ, khỏi cache ở app |

  - Mỗi tầng thêm một nơi dữ liệu có thể cũ. Khi debug "sửa rồi mà không thấy đổi", đi lần lượt từng tầng
- [ ] 🟡 HTTP caching: `Cache-Control: public/private, max-age, s-maxage, no-cache, no-store`, `stale-while-revalidate`, conditional request với `ETag`/`Last-Modified`, `Vary`. ⚠️ `no-cache` nghĩa là "được lưu nhưng phải revalidate", `no-store` mới là "không lưu". Chi tiết ở [02-networking.md](02-networking.md)

### Pattern

- [ ] 🟢 Cache-aside (lazy loading)
  - Đọc: tìm cache; miss thì đọc DB, ghi vào cache kèm TTL, trả. Ghi: ghi DB, xoá key cache
  - Ưu: đơn giản, chỉ cache thứ được đọc, Redis chết thì app vẫn chạy (chậm hơn)
  - Nhược: lần đầu luôn miss; có cửa sổ dữ liệu cũ; logic cache rải trong code

  ```php
  $user = Cache::remember("user:{$id}:v1", 600, fn () => User::find($id));
  ```

- [ ] 🟡 Read-through: cache tự gọi loader khi miss (app chỉ nói chuyện với cache). Code gọn, logic tập trung; cần thư viện/cache hỗ trợ loader (Caffeine `LoadingCache`)
- [ ] 🟡 Write-through: ghi vào cache, cache ghi đồng bộ xuống DB. Cache luôn mới; ghi chậm hơn, cache chứa cả dữ liệu không ai đọc
- [ ] 🟡 Write-behind (write-back): ghi vào cache, xuống DB sau theo lô. Ghi rất nhanh, gom được ghi (counter, view count); ⚠️ cache sập là **mất dữ liệu** chưa flush, thứ tự và nhất quán phức tạp
- [ ] 🟡 Refresh-ahead: làm mới key sắp hết hạn trước khi hết (theo lịch hoặc khi được đọc gần hạn). Không có miss cho key nóng; tốn công làm mới key không còn ai đọc
- [ ] Tóm tắt

  | Pattern | Nhất quán | Tốc độ đọc | Tốc độ ghi | Rủi ro |
  |---|---|---|---|---|
  | Cache-aside | cửa sổ cũ ngắn | miss lần đầu | bằng DB | race khi ghi đồng thời |
  | Read-through | như cache-aside | miss lần đầu | bằng DB | phụ thuộc thư viện |
  | Write-through | cao | luôn hit sau khi ghi | chậm hơn | cache đầy dữ liệu lạnh |
  | Write-behind | thấp | nhanh | rất nhanh | mất dữ liệu khi sập |
  | Refresh-ahead | tốt với key nóng | gần như luôn hit | không ảnh hưởng | làm mới thừa |

### Invalidation

- [ ] 🟢 TTL
  - Lưới an toàn cuối cùng: dù quên xoá thì dữ liệu cũng chỉ cũ tối đa bằng TTL
  - Chọn TTL theo "chấp nhận cũ bao lâu" của nghiệp vụ: cấu hình vài phút, giá sản phẩm ngắn, tồn kho lúc thanh toán thì không đọc từ cache
  - Jitter: `ttl = base + random(0, base * 0.1)` để các key tạo cùng lúc không hết hạn cùng lúc
- [ ] 🟡 Explicit delete: ghi DB xong thì xoá key liên quan. ⚠️ Khó nhất là **biết hết key nào liên quan** (danh sách, trang chủ, kết quả tìm kiếm có chứa object đó)
- [ ] 🟡 Versioned key: `product:123:v{version}` hoặc `catalog:v{n}:...`; tăng version là mọi key cũ tự thành rác và hết hạn dần. Invalidate cả nhóm bằng một phép `INCR`; tốn memory tạm thời
- [ ] 🔴 Event-driven / CDC: service phát event khi dữ liệu đổi, hoặc đọc binlog/WAL (Debezium, Canal) rồi xoá key. Tách logic xoá khỏi code nghiệp vụ, bắt được cả thay đổi từ script/admin sửa DB trực tiếp; đổi lại có độ trễ và thêm hạ tầng
- [ ] ⚠️ Xoá cache rồi update DB

  ```
  A (ghi)                     B (đọc)                     Cache      DB
  xoá cache                                               (trống)    cũ
                              đọc cache: miss
                              đọc DB: giá trị CŨ
                              ghi cache = CŨ              CŨ
  update DB = MỚI                                         CŨ         MỚI
  → cache giữ giá trị cũ tới khi hết TTL
  ```

  - Cửa sổ lỗi rộng: B chỉ cần đọc trong lúc A đang update (update DB thường chậm hơn đọc)
- [ ] ⚠️ Update DB rồi xoá cache (cách thường dùng)

  ```
  A (ghi)                     B (đọc)                     Cache      DB
                              đọc cache: miss (vừa hết hạn)(trống)   cũ
                              đọc DB: giá trị CŨ
  update DB = MỚI                                                    MỚI
  xoá cache                                               (trống)
                              ghi cache = CŨ              CŨ
  → vẫn sai, nhưng cần: cache miss đúng lúc + B đọc DB trước A ghi + B ghi cache SAU khi A xoá
  ```

  - Xác suất thấp hơn nhiều vì ghi cache thường nhanh hơn update DB; vẫn có, nên luôn có TTL
  - Lỗi khác: update DB thành công nhưng xoá cache thất bại (Redis timeout) → retry xoá, hoặc đẩy lệnh xoá vào queue/CDC
  - ⚠️ Xoá cache **trong** transaction trước khi commit: request khác đọc DB lúc chưa commit, nạp lại giá trị cũ. Xoá **sau** commit (Laravel `DB::afterCommit`, Spring `@TransactionalEventListener(phase = AFTER_COMMIT)`)
  - ⚠️ DB có replica: B đọc từ replica đang lag, nạp giá trị cũ vào cache ngay sau khi A xoá. Đọc để nạp cache từ primary, hoặc delayed double delete
- [ ] 🟡 Delayed double delete
  - Xoá cache → update DB → chờ một khoảng (lớn hơn thời gian một lần đọc DB + ghi cache, hoặc lớn hơn replica lag) → xoá lần nữa
  - Lần xoá thứ hai dọn giá trị cũ bị nạp lại trong cửa sổ race. Khoảng chờ là con số đoán, không phải đảm bảo; làm async (queue delay) chứ không `sleep` trong request
- [ ] ⚠️ Vì sao xoá thay vì set
  - Hai lần ghi đồng thời có thể set cache theo thứ tự ngược với thứ tự ghi DB:

    ```
    A: update DB = 1
    B: update DB = 2
    B: set cache = 2
    A: set cache = 1      → DB = 2, cache = 1, sai tới khi hết TTL
    ```

  - Xoá thì lần đọc sau luôn nạp từ DB. Thêm nữa: set cache khi ghi là tốn công nếu không ai đọc, và giá trị cache thường là kết quả tính từ nhiều bảng, khó dựng lại đúng lúc ghi
  - Ngoại lệ: dữ liệu ghi rất nhiều và đọc ngay (counter), dùng thao tác nguyên tử trên cache (`INCR`) hoặc set có kèm version và chỉ ghi nếu version mới hơn
- [ ] 🔴 Muốn nhất quán mạnh thì cache không phải công cụ đúng: đọc thẳng DB cho luồng cần chính xác (thanh toán, tồn kho khi đặt), cache cho luồng hiển thị

### Sự cố kinh điển

- [ ] 🟡 Cache stampede / thundering herd
  - Key nóng hết hạn, hàng nghìn request cùng miss, cùng đánh vào DB với cùng một query nặng
  - **Mutex/lock**: request đầu lấy lock (`SET key:lock 1 NX PX 5000`) và rebuild; request khác chờ ngắn rồi đọc lại cache, hoặc trả giá trị cũ. ⚠️ Lock phải có hạn, và người giữ lock chết thì người khác phải lấy được
  - **Request coalescing** trong một process: Go `singleflight`, Caffeine tự gom load cùng key
  - **Stale-while-revalidate**: lưu kèm "hạn mềm" và "hạn cứng"; quá hạn mềm thì vẫn trả giá trị cũ và một request làm mới ở background
  - **Probabilistic early expiration** (XFetch): mỗi lần đọc, với xác suất tăng dần khi gần hết hạn, request tự làm mới sớm. Điều kiện thường gặp: `now - delta * beta * ln(rand()) >= expiry` (`delta` = thời gian tính lại, `rand()` trong (0,1]); không cần lock
  - Key cực nóng: không để hết hạn, làm mới chủ động bằng job
- [ ] 🟡 Cache penetration
  - Query key **không tồn tại** (id âm, id ngẫu nhiên từ bot): cache không bao giờ có, lần nào cũng xuống DB
  - Cache giá trị rỗng (`null` marker) với TTL ngắn. ⚠️ Nhớ xoá marker khi bản ghi được tạo
  - Bloom filter chứa mọi id hợp lệ: "chắc chắn không có" thì trả luôn. Có false positive, không có false negative; không xoá phần tử được (trừ counting Bloom filter). Chi tiết ở [21-dsa.md](21-dsa.md)
  - Validate input sớm (id đúng định dạng), rate limit
- [ ] 🟡 Cache avalanche
  - Nhiều key cùng hết hạn một lúc (nạp cùng lúc sau deploy/warm-up, TTL cố định), hoặc cả cụm Redis sập: toàn bộ tải dồn xuống DB
  - TTL có jitter; Redis HA (replica + Sentinel hoặc Cluster); circuit breaker/rate limit bảo vệ DB; L1 in-process làm đệm; degrade (tắt tính năng phụ)
  - ⚠️ Cold start sau khi Redis restart không có persistence: warm-up dần, không bật 100% traffic ngay
- [ ] 🟡 Hot key
  - Một key bị đọc quá nhiều (sản phẩm flash sale, cấu hình toàn cục); trong Redis Cluster mọi request dồn vào **một** node
  - L1 cache trong app với TTL rất ngắn; nhân bản key (`product:1#1`..`#N`, đọc ngẫu nhiên một bản, ghi thì cập nhật tất cả); đọc từ replica
  - Phát hiện: `redis-cli --hotkeys` (cần policy LFU), monitor phía client, metric theo key
- [ ] 🟡 Big key
  - Một value vài MB, hoặc hash/list/set hàng triệu phần tử
  - Redis đơn luồng thực thi lệnh: đọc/xoá big key chặn mọi lệnh khác; tốn băng thông; phân bố memory lệch trong cluster
  - Chia nhỏ (theo trang, theo bucket hash), nén, chỉ lấy phần cần (`HGET` thay `HGETALL`, `SCAN`/`HSCAN` thay lệnh lấy hết); xoá bằng `UNLINK` (xoá async) thay `DEL`
  - Phát hiện: `redis-cli --bigkeys`, `MEMORY USAGE key`
  - Chi tiết Redis ở [04-nosql-search-storage.md](04-nosql-search-storage.md)

### Eviction

- [ ] 🟢 Thuật toán

  | | Loại bỏ | Hợp với | Nhược |
  |---|---|---|---|
  | LRU | lâu nhất chưa được dùng | truy cập có tính cục bộ theo thời gian | một lần quét lớn đẩy hết key nóng ra |
  | LFU | ít được dùng nhất | key nóng ổn định | key từng nóng giữ chỗ lâu; cần cơ chế giảm dần (decay) |
  | FIFO | vào sớm nhất | đơn giản | không quan tâm key nào nóng |
  | TTL | sắp hết hạn trước | dữ liệu có hạn rõ ràng | |
  | Random | ngẫu nhiên | rẻ | |

  - Caffeine dùng W-TinyLFU, kết hợp tần suất và độ mới, hit ratio thường tốt hơn LRU thuần
- [ ] 🟡 Cài LRU với `get`/`put` `O(1)`
  - Hash map: key → node trong danh sách liên kết đôi
  - Doubly linked list: đầu là mới dùng nhất, cuối là lâu nhất
  - `get`: tra map, chuyển node lên đầu. `put`: có rồi thì cập nhật và chuyển lên đầu; chưa có thì thêm vào đầu, vượt dung lượng thì bỏ node cuối và xoá khỏi map
  - Cần danh sách **đôi** để gỡ một node ở giữa trong `O(1)`; node lưu cả key để xoá khỏi map khi evict; dùng sentinel head/tail để bớt xử lý biên
  - ⚠️ Dùng đa luồng thì cả `get` cũng là thao tác ghi (đổi thứ tự) nên phải lock
  - **Đối chiếu**: Java có `LinkedHashMap(capacity, 0.75f, true)` + override `removeEldestEntry`; Go tự ghép `map` + `container/list`; PHP không có sẵn, tự cài bằng mảng + danh sách
- [ ] 🟡 Redis `maxmemory-policy`: `noeviction` (mặc định; ghi lỗi khi đầy), `allkeys-lru`, `volatile-lru` (chỉ key có TTL), `allkeys-lfu`, `volatile-lfu`, `allkeys-random`, `volatile-random`, `volatile-ttl`
  - LRU/LFU của Redis là **xấp xỉ** bằng cách lấy mẫu vài key, không phải LRU chính xác
  - ⚠️ Dùng Redis vừa làm cache vừa lưu dữ liệu quan trọng (session, queue) với `allkeys-*` thì dữ liệu quan trọng cũng bị evict. Tách instance

### Vận hành

- [ ] 🟡 Serialization
  - JSON: đọc được, đa ngôn ngữ; igbinary/msgpack: nhỏ hơn; ⚠️ native serialization (PHP `serialize`, Java) gắn với class: đổi class là không đọc được cache cũ, và có rủi ro deserialization
  - Nén value lớn (gzip/lz4) khi băng thông là nút thắt
  - Đổi cấu trúc object thì đổi version trong key (`user:123:v2`) để deploy mới không đọc format cũ và rollback không vỡ
- [ ] 🟡 Key naming, namespace
  - `{app}:{env}:{entity}:{id}:{version}`, ví dụ `shop:prod:product:123:v2`
  - Key chứa mọi thứ làm kết quả khác nhau: tenant, locale, quyền, tham số query. ⚠️ Thiếu `tenant_id` hoặc `user_id` trong key là lộ dữ liệu chéo
  - Key từ input dài/tuỳ ý thì hash (`search:{sha1(query)}`)
  - Không `KEYS *` ở production; dùng `SCAN`. Xoá theo prefix nên thay bằng versioned key hoặc tag
- [ ] 🟡 Cache danh sách và kết quả tổng hợp
  - Cache từng object theo id thì dễ invalidate; cache danh sách/trang/kết quả search thì một object đổi làm sai nhiều key
  - Cách thường dùng: cache **danh sách id** (TTL ngắn hoặc versioned key theo nhóm), rồi lấy chi tiết từng object qua cache theo id (`MGET`)
  - Số đếm, tổng (lượt thích, số đơn hôm nay): cập nhật nguyên tử bằng `INCR`/`HINCRBY` và đồng bộ định kỳ với DB, thay vì xoá rồi `COUNT(*)` lại
- [ ] 🟡 Gọi cache cũng là gọi mạng
  - Timeout ngắn cho Redis (ngắn hơn nhiều so với DB); Redis chậm thì coi như miss hoặc trả lỗi nhanh, không để request treo
  - Connection pool đủ lớn; ⚠️ mỗi request gọi Redis hàng trăm lần trong vòng lặp (N+1 với cache) thì dùng `MGET`/pipeline
- [ ] 🟡 Cache warming: nạp trước key nóng sau deploy/restart hoặc trước sự kiện lớn; chạy từ từ để không tự gây tải
- [ ] 🟡 Cache tag: gắn key với tag (`product:123`, `category:5`), invalidate cả nhóm theo tag. ⚠️ Chỉ một số driver hỗ trợ (Laravel: Redis, Memcached; không có với file/database)
- [ ] 🔴 Multi-level cache (L1 in-process + L2 Redis)
  - Đọc L1 → L2 → DB. L1 bớt round-trip mạng và bảo vệ trước hot key; L2 dùng chung giữa instance
  - Vấn đề: mỗi instance có L1 riêng, ghi ở instance A thì L1 ở B vẫn cũ
  - Cách xử lý: TTL của L1 rất ngắn (vài giây) để giới hạn độ cũ; broadcast invalidation qua Redis Pub/Sub hoặc message bus (⚠️ Pub/Sub không bền: instance mất kết nối lúc đó sẽ bỏ lỡ message, nên vẫn cần TTL); Redis client-side caching (tracking) nếu client hỗ trợ
  - Chỉ đưa vào L1 dữ liệu ít đổi và nhỏ; để ý memory của từng instance (JVM heap). PHP-FPM không giữ biến giữa các request, L1 trong PHP thường là APCu (dùng chung giữa các worker trên cùng một máy)
- [ ] 🟡 Đo lường
  - Hit ratio (tổng và theo nhóm key); hit ratio thấp là dấu hiệu key quá cụ thể hoặc TTL quá ngắn
  - Latency p50/p99 của cache, số kết nối, timeout, memory, số key bị evict, số key hết hạn
  - Tải DB trước và sau khi thêm cache: mục tiêu thật sự là giảm tải/latency, không phải hit ratio đẹp
  - Có cách tắt cache theo tính năng (feature flag) và xoá theo nhóm; ⚠️ cache làm bug khó tái hiện
- [ ] ⚠️ Khi nào KHÔNG nên cache
  - Dữ liệu cần chính xác tuyệt đối tại thời điểm đọc (số dư, tồn kho khi trừ)
  - Ghi nhiều hơn đọc, hoặc mỗi key hiếm khi được đọc lại (hit ratio thấp, chỉ thêm độ trễ và độ phức tạp)
  - Query vốn đã nhanh nhờ index; nên sửa query/index trước khi cache
  - Dữ liệu cá nhân hoá cao, số tổ hợp key bùng nổ
  - Cache như "băng dán" che thiết kế chậm: khi cache sập, hệ thống có chịu nổi không? Nếu không, cache đã thành phụ thuộc bắt buộc và phải được vận hành như một DB
- [ ] 🟡 Cache trong framework
  - Laravel: `Cache::remember`, `Cache::lock` (atomic lock chống stampede), `Cache::tags` (driver hỗ trợ), `Cache::flexible` cho stale-while-revalidate (có từ Laravel 11, kiểm tra lại theo phiên bản bạn dùng); `once()` để memoize trong phạm vi một request
  - Spring: `@Cacheable`, `@CachePut`, `@CacheEvict`; `@Cacheable(sync = true)` để chỉ một thread load mỗi key trong một instance; Caffeine làm L1, Redis làm L2. ⚠️ Gọi method có `@Cacheable` từ chính class đó (self-invocation) không đi qua proxy nên cache không chạy
  - Go: không có annotation; `sync.Map`/map + mutex, thư viện như `ristretto`, `groupcache`; `golang.org/x/sync/singleflight` để gom request cùng key
  - **Đối chiếu**: cả ba đều cho stampede protection trong một process (`sync = true`, `singleflight`, `Cache::lock`), nhưng giữa nhiều instance vẫn cần lock phân tán hoặc stale-while-revalidate

## Senior trả lời khác gì

| Câu hỏi | Junior / mid | Senior |
|---|---|---|
| "Làm sao cache và DB nhất quán?" | Update DB rồi xoá cache | Vẽ timeline cả hai thứ tự, nói cửa sổ race còn lại; xoá sau commit; retry xoá hoặc CDC; TTL làm lưới an toàn; luồng cần chính xác thì không đọc cache |
| "Trang chủ chậm, thêm cache nhé?" | Thêm Redis, TTL 1 giờ | Đo trước: query nào chậm, sửa index được không; cache thì chọn TTL theo nghiệp vụ, tính stampede, invalidation, đo hit ratio và tải DB sau đó |
| "Key nóng hết hạn làm sập DB?" | Tăng TTL | Stampede: lock/singleflight, stale-while-revalidate, làm mới chủ động key nóng, jitter; bảo vệ DB bằng rate limit; post-mortem vì sao DB không chịu nổi khi cache miss |
| "Dùng L1 in-process cho nhanh?" | Đồng ý | Nhanh nhưng mỗi node một bản: TTL ngắn, broadcast invalidation không bền, chỉ cho dữ liệu nhỏ ít đổi; memory mỗi instance |
| "Redis sập thì sao?" | Có replica | App vẫn chạy được ở chế độ chậm không? Timeout ngắn cho Redis, circuit breaker, DB chịu được bao nhiêu phần trăm tải khi mất cache, warm-up dần |

## Tình huống

1. **Trang chủ có key cache hết hạn đúng giờ cao điểm và DB sập.**
   Gợi ý:
   - Stampede trên key nóng, có thể kèm avalanche nếu nhiều key cùng TTL
   - Lock rebuild, stale-while-revalidate, làm mới bằng job, jitter; kiểm tra DB có chịu được một lượt miss không
2. **Admin sửa giá sản phẩm, 10 phút sau một số người vẫn thấy giá cũ.**
   Gợi ý:
   - Đi từng tầng: CDN, L1 của từng instance, Redis, replica lag
   - Kiểm tra xoá cache có chạy sau commit, có lỗi xoá bị nuốt không; đổi sang versioned key hoặc CDC
3. **Bot gọi `/products/{id}` với id ngẫu nhiên, DB CPU 100%.**
   Gợi ý:
   - Penetration: cache null TTL ngắn, Bloom filter, validate id, rate limit theo client
4. **Redis memory tăng đều, latency thỉnh thoảng vọt lên vài trăm ms.**
   Gợi ý:
   - Key không có TTL, big key; `--bigkeys`, `MEMORY USAGE`; lệnh chặn (`KEYS`, `HGETALL` lớn, `DEL` big key)
   - Đặt TTL, `maxmemory` + policy, chia nhỏ key, `UNLINK`
5. **Sau khi bật cache danh sách đơn hàng, một khách thấy đơn của khách khác.**
   Gợi ý:
   - Key thiếu `user_id`/`tenant_id`, hoặc CDN cache response cá nhân vì thiếu `Cache-Control: private`
   - Xoá toàn bộ cache liên quan, sửa key, rà mọi key có dữ liệu cá nhân, xử lý như sự cố lộ dữ liệu
6. **Deploy phiên bản mới đổi class `UserDto`, log đầy lỗi deserialize từ cache.**
   Gợi ý:
   - Format cache cũ; version trong key, serialize JSON thay native, đọc lỗi thì coi là miss

## ❓ Câu hỏi hay gặp

🟢
- Cache-aside hoạt động thế nào?
- TTL dùng để làm gì? Vì sao thêm jitter?
- LRU là gì? Khác LFU thế nào?
- Các tầng cache từ trình duyệt tới DB?

🟡
- Làm sao đảm bảo cache và DB nhất quán?
- Update DB rồi xoá cache, hay xoá cache rồi update DB? Vẽ race condition.
- Vì sao nên xoá cache thay vì cập nhật cache?
- Stampede, penetration, avalanche khác nhau thế nào? Cách phòng từng cái?
- Cài đặt LRU cache với `get`/`put` đều `O(1)`.
- Hot key và big key trong Redis xử lý ra sao?
- Write-through và write-behind khác nhau thế nào? Khi nào dùng write-behind?

🔴
- Thiết kế multi-level cache L1 + L2 cho 20 instance, giữ nhất quán thế nào?
- Khi nào bạn quyết định không dùng cache?
- Dùng CDC để invalidate cache: ưu nhược so với xoá trong code?
- Redis cache sập hoàn toàn, hệ thống của bạn phản ứng thế nào?

## Bài tập tự làm

1. Vẽ timeline cho kịch bản: DB có một replica lag 500 ms, app đọc từ replica khi cache miss, dùng "update DB rồi xoá cache". Chỉ ra dữ liệu cũ vào cache thế nào và đề xuất hai cách sửa kèm cái giá.
2. Viết pseudo-code cho hàm `getWithCache(key, loader, ttl)` có chống stampede bằng stale-while-revalidate và lock phân tán, xử lý trường hợp người giữ lock chết.
3. Cài LRU cache `O(1)` bằng ngôn ngữ bạn chọn (Go, Java hoặc PHP), sau đó bổ sung TTL cho từng key.
4. Chọn một màn hình trong dự án của bạn, liệt kê dữ liệu trên đó, quyết định cache hay không cho từng phần, TTL, key naming, và cách invalidate.
5. So sánh bằng bảng: Redis Pub/Sub, Redis Streams, Kafka dùng để broadcast invalidation cho L1 cache.

> Nộp bài vào đây để được review.
