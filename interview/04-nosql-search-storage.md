# 04. NoSQL, search và storage

> [← Mục lục](README.md) · Trọng tâm: **Redis** (hoặc Valkey), Elasticsearch/OpenSearch và S3 trong stack PHP/Laravel; MongoDB, Cassandra, DynamoDB, time-series, OLAP, vector DB và graph DB ở mức chọn đúng công cụ.
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
| [Redis docs](https://redis.io/docs/latest/) | Official docs | Kiểu dữ liệu, persistence, eviction, replication, Cluster. Phần lớn áp dụng cho cả [Valkey](https://valkey.io/) |
| [MongoDB Manual](https://www.mongodb.com/docs/manual/) | Official docs | Data modeling, index, aggregation, replica set, sharding, change streams |
| [Elastic docs](https://www.elastic.co/docs/) | Official docs | Analyzer, mapping, pagination, alias, vận hành cluster. OpenSearch: [docs.opensearch.org](https://docs.opensearch.org/latest/) |
| [DynamoDB Developer Guide](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html) và [*The DynamoDB Book*](https://www.dynamodbbook.com/) (Alex DeBrie) | Official docs + sách | Query-first modeling, single-table design |
| [Amazon S3 User Guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) | Official docs | Presigned URL, multipart, consistency, conditional write, lifecycle, bảo mật |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.2 data model, ch.3 storage (LSM, column store), ch.5 replication, ch.6 partitioning (số chương theo bản 1) |
| [Laravel docs](https://laravel.com/docs/redis) | Official docs | Redis, [Scout](https://laravel.com/docs/scout), [Filesystem](https://laravel.com/docs/filesystem) (S3) |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Dùng đúng kiểu dữ liệu Redis, biết khi nào cần NoSQL/search/object storage | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.9 | Vận hành Redis không tự bắn vào chân, làm search tiếng Việt, đồng bộ DB sang search, upload file đúng cách | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.7 | Hiểu bên trong Redis, HA và sharding, modeling cho Cassandra/DynamoDB, vận hành search, chọn đúng kho cho phân tích và vector | 10–12 ngày |

Học theo thứ tự: chặng 2 cần mô hình "Redis chạy lệnh trên một thread" của chặng 1, và chặng 3
giải thích *vì sao* các giới hạn ở chặng 2 tồn tại (hash slot, replication async, shard cố định).
Phần cache (pattern, invalidation, stampede) nằm ở [11-cache.md](11-cache.md); file này tập trung
vào bản thân các hệ thống lưu trữ.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Redis: kiểu dữ liệu và use case

**Vì sao cần học:** Trong dự án Laravel, Redis gần như luôn có mặt: cache, session, queue, lock,
rate limit. Chọn đúng kiểu dữ liệu thì một lệnh làm xong việc. Chọn sai thì PHP phải kéo cả cục
dữ liệu về, sửa, rồi ghi lại. Câu hỏi hay gặp: "làm leaderboard, đếm user online, rate limit bằng
Redis thế nào".

**Học gì**

*Redis là gì*
- Redis là một kho *key-value* nằm trong RAM. Mỗi dữ liệu được lưu dưới một cái tên (*key*), và
  giá trị (*value*) có thể là nhiều kiểu cấu trúc khác nhau, không chỉ là chuỗi.
  - Ví dụ: key `user:42:profile` chứa một hash, key `leaderboard:2026-09` chứa một sorted set.
- Dữ liệu nằm trong RAM nên đọc ghi rất nhanh. Cái giá là RAM đắt và có hạn, nên phải tính dung
  lượng và chọn cách xoá bớt khi đầy (module 2.2).
- Mỗi kiểu dữ liệu có bộ lệnh riêng. Ví dụ các lệnh bắt đầu bằng `H` dành cho hash, bằng `Z` dành
  cho sorted set.

*Năm kiểu cơ bản*

| Kiểu | Là gì | Dùng cho | Lệnh chính |
|---|---|---|---|
| String | Một giá trị đơn: chuỗi, số, hoặc dãy byte | Cache, counter, flag, lock | `GET`/`SET`, `INCR`, `SET k v NX PX 30000` |
| Hash | Một key chứa nhiều cặp field → value, giống mảng kết hợp của PHP | Object, đếm theo field | `HSET`, `HGET`, `HINCRBY` |
| List | Danh sách có thứ tự, thêm và lấy ở hai đầu | Queue đơn giản, danh sách mới nhất | `LPUSH`, `BRPOP`, `LTRIM`, `LRANGE` |
| Set | Tập phần tử không trùng, không có thứ tự | Tag, tập duy nhất, giao/hợp | `SADD`, `SISMEMBER`, `SINTER` |
| Sorted set | Set mà mỗi phần tử kèm một điểm số (*score*), luôn được sắp theo score | Leaderboard, sliding window, delay queue | `ZADD`, `ZINCRBY`, `ZRANGE`, `ZREMRANGEBYSCORE` |

- Vài lệnh cần hiểu kỹ:
  - `SET k v NX PX 30000`: `NX` nghĩa là chỉ ghi nếu key chưa tồn tại, `PX 30000` nghĩa là key tự
    hết hạn sau 30.000 ms. Đây là nền móng của distributed lock (module 2.4).
  - `INCR` tăng số lên 1 và trả giá trị mới trong **một lệnh**. Hai request cùng `INCR` thì không
    mất lượt nào. Nếu PHP `GET` rồi `SET` giá trị cộng 1 thì hai request có thể cùng đọc 5 và cùng
    ghi 6.
  - `BRPOP`: chữ `B` là *blocking*, lệnh chờ tới khi list có phần tử rồi mới trả về. Worker của
    queue dùng lệnh này để không phải hỏi liên tục.
  - `LTRIM` cắt list chỉ giữ một khoảng. Ví dụ `LPUSH` thông báo mới rồi `LTRIM notif:42 0 99` để
    chỉ giữ 100 thông báo mới nhất.
  - `ZREMRANGEBYSCORE` xoá các phần tử có score nằm trong một khoảng. Nếu score là thời điểm thì
    lệnh này xoá "mọi thứ cũ hơn X", dùng cho sliding window (module 2.4).
- Delay queue bằng sorted set: score là thời điểm job cần chạy. Worker lấy các phần tử có score
  nhỏ hơn thời điểm hiện tại. Laravel dùng đúng cách này cho delayed job.

*Các kiểu đặc biệt (🟡)*
- **Bitmap**: một chuỗi bit, mỗi vị trí là 0 hoặc 1.
  - Ví dụ điểm danh: key `checkin:2026-09-25`, bật bit ở vị trí bằng `user_id` khi user đó điểm
    danh. 10 triệu user chỉ tốn khoảng 1,25 MB cho một ngày.
- **HyperLogLog**: đếm số phần tử khác nhau (*unique*) một cách gần đúng.
  - Sai số khoảng 0,81%, tối đa 12 KB mỗi key dù đếm hàng trăm triệu phần tử.
  - Cái giá: chỉ ra con số gần đúng, không liệt kê lại được đã đếm những ai, không hỏi được "user
    X đã được đếm chưa".
  - Dùng cho đếm DAU (số user hoạt động mỗi ngày), số visitor unique.
- **Stream**: log sự kiện chỉ ghi thêm vào cuối, có *consumer group* (một nhóm worker chia nhau
  đọc, mỗi message chỉ giao cho một worker trong nhóm). Chi tiết ở module 2.3.
- **Geo**: lưu toạ độ và tìm các điểm trong một bán kính, ví dụ "quán gần tôi". Bên trong được cài
  bằng sorted set.
- Redis 8 gộp các module trước đây của Redis Stack (JSON, Query Engine, TimeSeries,
  Bloom/probabilistic) vào bản phân phối chính. Biết là có, không bắt buộc cho phỏng vấn backend
  thông thường.

*Chọn kiểu theo cách truy cập*
- ⚠️ Chọn kiểu theo **cách truy cập**, không theo hình dạng dữ liệu.
  - Lưu cả object user thành một JSON string thì mỗi lần sửa email phải làm ba bước: `GET` cả
    chuỗi, `json_decode` rồi sửa trong PHP, `SET` lại cả chuỗi.
  - Hai request cùng làm vậy thì bản ghi sau đè mất sửa đổi của bản trước.
  - Dùng hash thì `HSET user:42 email new@x.com` sửa đúng một field, trong một lệnh.
- Ngược lại, nếu lúc nào cũng đọc và ghi nguyên cả object (ví dụ cache kết quả một query) thì
  string chứa JSON là lựa chọn hợp lý.

**Đọc**
- Redis: [Data types](https://redis.io/docs/latest/develop/data-types/) (đọc phần giới thiệu từng kiểu), [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/), [HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/)
- Redis: [What's new in 8.0](https://redis.io/docs/latest/develop/whats-new/8-0/): lướt để biết các kiểu dữ liệu mới được gộp vào

**Nắm chắc khi**
- [ ] Với 8 bài toán (session, top 100, đếm DAU, queue, tag bài viết, rate limit, điểm danh, tìm quán gần), chọn đúng kiểu và viết được lệnh chính
- [ ] Giải thích được vì sao HyperLogLog đếm được hàng trăm triệu phần tử chỉ với 12KB, và cái giá là gì

#### 1.2 Bức tranh NoSQL

**Vì sao cần học:** "Khi nào dùng NoSQL thay MySQL" là câu mở đầu rất hay gặp. Người phỏng vấn
đánh giá bạn qua việc biết **cái giá** của NoSQL, không chỉ ưu điểm. Dự án PHP thực tế thường là
MySQL làm nguồn chính, cộng Redis, Elasticsearch và S3 cho từng việc riêng.

**Học gì**

*NoSQL là gì*
- NoSQL là tên gọi chung cho các DB không theo mô hình bảng quan hệ + SQL. Không có một "NoSQL"
  duy nhất: mỗi loại tối ưu cho một kiểu truy cập riêng.

*Các nhóm chính*

| Nhóm | Dữ liệu tổ chức thế nào | Ví dụ | Hợp khi |
|---|---|---|---|
| Key-value | Tra một giá trị theo key | Redis, DynamoDB, etcd | Luôn biết key cần lấy |
| Document | Mỗi bản ghi là một document JSON/BSON lồng nhau, gom theo aggregate | MongoDB, Couchbase | Một cụm dữ liệu luôn đọc ghi cùng nhau |
| Wide-column | Dữ liệu chia theo partition, trong partition các dòng sort theo clustering key | Cassandra, ScyllaDB, HBase, Bigtable | Ghi rất dày, dữ liệu khổng lồ |
| Graph | Node và cạnh nối giữa chúng | Neo4j, Neptune | Quan hệ nhiều bước (module 3.7) |
| Time-series | Chuỗi giá trị theo thời gian | Prometheus, InfluxDB, TimescaleDB | Metric, số liệu cảm biến (module 3.6) |
| Search | Inverted index | Elasticsearch, OpenSearch | Tìm kiếm văn bản (module 1.3) |

- Giải thích các từ trong bảng:
  - *BSON* là dạng nhị phân của JSON mà MongoDB dùng, có thêm kiểu ngày tháng, số nguyên, ...
  - *Aggregate* là một cụm dữ liệu luôn được đọc và ghi cùng nhau. Ví dụ đơn hàng kèm các dòng
    hàng và địa chỉ giao: trong MongoDB có thể là một document duy nhất.
  - *Partition* là một nhóm dòng có cùng một key (*partition key*), được lưu cùng trên một máy.
    *Clustering key* quyết định thứ tự các dòng bên trong partition (module 3.4).

*Khi nào chọn NoSQL*
- Cách truy cập đơn giản, biết trước, và đi theo key. Ví dụ "lấy giỏ hàng của user 42".
- Cần *scale ghi ngang*: lượng ghi vượt sức một máy, phải chia dữ liệu ra nhiều máy.
- Cần latency thấp và ổn định ở quy mô rất lớn.

*Cái giá phải trả*
- ⚠️ Những thứ mất đi (hoặc vẫn có nhưng đắt):
  - JOIN giữa các loại dữ liệu.
  - Transaction trên nhiều bản ghi.
  - Ràng buộc toàn vẹn: khoá ngoại, unique ngoài key chính.
  - Query *ad-hoc*, tức những câu hỏi bất chợt chưa lường trước khi thiết kế, như "đếm đơn theo
    tỉnh trong tháng trước".
- ⚠️ Kiểu truy cập đổi thì thường phải thiết kế lại dữ liệu, vì dữ liệu được sắp xếp riêng cho các
  query đã biết.
- ⚠️ "Schemaless" (không có schema) là tên gọi sai. Schema không biến mất mà chuyển từ DB sang code.
  - Ví dụ: document tạo năm ngoái không có field `phone`, document mới thì có. Code phải đọc được
    mọi phiên bản document cũ đang nằm trong DB.

*Mặc định an toàn*
- Bắt đầu bằng MySQL/Postgres. Thêm NoSQL cho đúng bài toán nó giỏi.
- Cách dùng mỗi phần hệ thống một kho hợp nhất gọi là *polyglot persistence*.
  - Cái giá: mỗi hệ thống thêm vào là thêm backup, giám sát, nâng cấp, và người biết vận hành nó.
- Nhu cầu "schema linh hoạt" thường chỉ cần cột Postgres `jsonb` hoặc MySQL `JSON`, không cần
  chuyển sang MongoDB.

**Đọc**
- DDIA ch.2 (*Data Models and Query Languages*): relational, document, graph
- MongoDB: [Data Modeling](https://www.mongodb.com/docs/manual/data-modeling/) (phần mở đầu, để thấy tư duy aggregate)

**Nắm chắc khi**
- [ ] Cho một hệ thống thương mại điện tử, chỉ ra được phần nào hợp với SQL, phần nào hợp với key-value, search, object storage, và nói lý do
- [ ] Nói được 3 thứ mất đi khi chuyển một bảng quan hệ sang MongoDB

#### 1.3 Search cơ bản

**Vì sao cần học:** Ô tìm kiếm sản phẩm có ở hầu hết mọi app. `LIKE` chạy được lúc đầu, rồi vừa
chậm vừa cho kết quả kém khi dữ liệu lớn dần. Câu hỏi hay gặp: "vì sao không dùng `LIKE`",
"inverted index là gì".

**Học gì**

*Vì sao `LIKE '%keyword%'` không đủ*
- Không dùng được B+tree index: index sắp theo đầu chuỗi, còn `%` ở đầu thì không biết bắt đầu tìm
  từ đâu, nên phải quét cả bảng (full scan, xem [03-database-sql.md](03-database-sql.md) module 1.2).
- Không xếp hạng theo độ liên quan (*relevance*): kết quả khớp nhiều hơn không được đưa lên trước.
- Không hiểu biến thể của từ: tìm "shoe" không ra "shoes".
- Không chịu được lỗi chính tả, không khớp giữa có dấu và không dấu ("ao khoac" với "áo khoác").
- Không có *facet*, tức bộ đếm theo nhóm bên cạnh kết quả như "Samsung (120), Apple (80)".
- Không có *highlight*, tức tô đậm đoạn khớp trong kết quả.

*Inverted index*
- *Inverted index* là bảng tra ngược: từ mỗi **term** trỏ tới danh sách document chứa nó.
  - *Term* là một đơn vị sau khi phân tích văn bản, thường là một từ đã được chuẩn hoá (viết
    thường, bỏ dấu, ...).
  - Danh sách đó gọi là *posting list*. Mỗi mục lưu document id, vị trí của term trong document (để
    tìm cụm từ liền nhau) và tần suất xuất hiện (để chấm điểm).
- Ví dụ với 3 document:
  - doc 1: "áo khoác nam", doc 2: "áo thun nam", doc 3: "khoác gió"

  | Term | Posting list |
  |---|---|
  | áo | 1, 2 |
  | khoác | 1, 3 |
  | nam | 1, 2 |
  | thun | 2 |
  | gió | 3 |

- Tìm "áo khoác" không quét document nào, mà làm các bước:
  1. Lấy posting list của "áo": 1, 2.
  2. Lấy posting list của "khoác": 1, 3.
  3. Giao hai danh sách (nếu cần có đủ các từ) ra doc 1, hoặc hợp lại (nếu chỉ cần một từ) ra 1, 2,
     3 rồi xếp doc 1 lên đầu vì khớp cả hai term.

*Analyzer*
- *Analyzer* là chuỗi xử lý biến văn bản thô thành các term. Gồm ba bước theo thứ tự:
  1. *Character filter*: sửa chuỗi thô, ví dụ bỏ thẻ HTML.
  2. *Tokenizer*: cắt chuỗi thành các *token* (mảnh), thường theo khoảng trắng và dấu câu.
  3. *Token filter*: biến đổi từng token, gồm:
     - lowercase: viết thường.
     - stopword: bỏ từ quá phổ biến, không giúp phân biệt ("the", "và").
     - stemming: đưa từ về gốc ("running" thành "run").
     - synonym: từ đồng nghĩa ("đt" và "điện thoại").
     - folding: bỏ dấu ("áo" thành "ao").
- Ví dụ: `<b>Áo Khoác</b>` → bỏ HTML thành `Áo Khoác` → tách thành `Áo`, `Khoác` → viết thường
  thành `áo`, `khoác`.

*Hai kiểu field: `text` và `keyword`*

| | `text` | `keyword` |
|---|---|---|
| Có qua analyzer không | Có, bị tách thành nhiều term | Không, giữ nguyên cả chuỗi |
| Dùng cho | Tìm full-text | Lọc chính xác, sort, aggregation (đếm theo nhóm) |
| Ví dụ | Tên sản phẩm, mô tả | Mã đơn hàng, email, trạng thái |

- ⚠️ Mã đơn `ORD-2026-001` mà để `text` thì bị tách thành `ord`, `2026`, `001`. Tìm `001` sẽ ra
  cả đống đơn không liên quan.

*Vị trí của search engine trong hệ thống*
- Search engine là **bản sao để đọc**, không phải nguồn sự thật (*source of truth*, nơi giữ bản dữ
  liệu đúng cuối cùng). Luôn phải rebuild được toàn bộ index từ DB.
- Nhu cầu nhỏ thì chưa cần Elasticsearch. Các lựa chọn nhẹ hơn:
  - MySQL `FULLTEXT` index.
  - Postgres full-text search, cộng `pg_trgm`. `pg_trgm` cắt chuỗi thành các cụm 3 ký tự
    (*trigram*), nhờ đó index được cả `LIKE '%x%'` và tìm gần đúng khi gõ sai nhẹ.
  - Meilisearch, Typesense: search engine nhẹ, dễ vận hành hơn Elasticsearch.

**Đọc**
- Elastic: [Text analysis](https://www.elastic.co/docs/manage-data/data-store/text-analysis) (phần khái niệm: anatomy of an analyzer), [Mapping](https://www.elastic.co/docs/manage-data/data-store/mapping)
- Postgres: [Full Text Search](https://www.postgresql.org/docs/current/textsearch.html) (chương 12.1 Introduction), [pg_trgm](https://www.postgresql.org/docs/current/pgtrgm.html)

**Nắm chắc khi**
- [ ] Vẽ được inverted index cho 3 document ngắn và chỉ ra cách query "áo khoác" chạy trên đó
- [ ] Giải thích được vì sao mã đơn hàng phải là `keyword`, còn tên sản phẩm là `text`

#### 1.4 Object storage cơ bản

**Vì sao cần học:** Upload ảnh đại diện, hoá đơn PDF, video là việc hằng ngày. Laravel mặc định
lưu file vào `storage/app` trên đĩa local: chạy tốt với một server, rồi vỡ khi thêm server thứ
hai. Câu hỏi hay gặp: "thiết kế luồng upload file", "vì sao không upload qua API".

**Học gì**

*Vì sao không lưu file trên đĩa app server*
- App phải *stateless* để scale ngang. Stateless nghĩa là server không giữ dữ liệu riêng, nên
  request vào máy nào cũng cho kết quả như nhau và thêm máy là tăng sức chịu tải.
  - File lưu ở server A thì request rơi vào server B không thấy file đó.
- Instance bị thay (autoscaling, deploy container mới) là mất file.
- Đĩa đầy làm sập cả app, không chỉ tính năng upload.
- Backup rải rác trên nhiều máy rất khó.

*Object storage*
- *Object storage* là kho lưu file dạng *object*. Mỗi object gồm:
  - Key, trông giống đường dẫn, ví dụ `avatars/42/9f3c.jpg`.
  - Nội dung file.
  - Metadata: content type, kích thước, thông tin tự đặt.
- Truy cập qua HTTP API, không mount như ổ đĩa. Các dịch vụ: S3, GCS, Azure Blob, Cloudflare R2,
  MinIO (tự host).
- Cách dùng chuẩn:
  - File nằm ở object storage.
  - DB chỉ lưu key và metadata của file.
  - Người dùng tải file qua CDN (mạng máy chủ đặt gần người dùng, cache sẵn file).

*Presigned URL*
- *Presigned URL* là URL do server ký bằng credential của nó, có thời hạn, cho phép client `PUT`
  (upload) hoặc `GET` (tải) đúng một key trên S3.
- Client không cần credential S3, và file đi thẳng từ client lên S3, **không đi qua app server**.
  - Vì sao quan trọng: upload 2 GB qua PHP-FPM nghĩa là một worker bị giữ suốt thời gian upload,
    và file còn bị giới hạn bởi `upload_max_filesize`, `post_max_size`, timeout.

*Luồng upload bằng presigned URL*
1. Client xin URL upload, gửi kèm loại file và kích thước dự kiến.
2. Server kiểm tra quyền, rồi **tự sinh key** (ví dụ `avatars/42/<uuid>.jpg`). Không dùng tên file
   user gửi lên, vì tên đó có thể trùng, chứa ký tự lạ, hoặc chứa `../`.
3. Client upload thẳng lên S3 bằng URL đó.
4. Client báo "đã xong" cho server, hoặc S3 tự bắn event khi có object mới.
5. Server kiểm tra object thật sự tồn tại, đúng loại và kích thước, rồi mới ghi vào DB.

- ⚠️ URL download có hạn, nhưng trong thời hạn đó **ai có URL cũng tải được**, không cần đăng
  nhập. File nhạy cảm (hợp đồng, CCCD) thì để hạn ngắn.

**Đọc**
- S3: [Uploading objects with presigned URLs](https://docs.aws.amazon.com/AmazonS3/latest/userguide/PresignedUrlUploadObject.html)
- Laravel: [Temporary URLs](https://laravel.com/docs/filesystem#temporary-urls) và [Temporary Upload URLs](https://laravel.com/docs/filesystem#temporary-upload-urls)

**Nắm chắc khi**
- [ ] Vẽ được luồng upload ảnh đại diện bằng presigned URL, chỉ ra chỗ nào server phải kiểm tra
- [ ] Giải thích được vì sao upload file 2GB qua API PHP-FPM là thiết kế sai

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Redis: mô hình thực thi và lệnh nguy hiểm

**Vì sao cần học:** Sự cố Redis kinh điển là "một lệnh làm cả hệ thống chậm theo", ví dụ một
cron job hay một lệnh debug gõ tay trên production. Hiểu mô hình một thread thì mới giải thích
và phòng được. Câu hỏi hay gặp: "Redis chạy một thread sao lại nhanh", "vì sao cấm `KEYS *`".

**Học gì**

*Vì sao một thread mà vẫn nhanh*
- Redis chạy các lệnh **lần lượt từng lệnh một** trên một thread chính (*main thread*).
- Nó vẫn nhanh vì bốn lý do:
  - Dữ liệu nằm trong RAM, không phải chờ đĩa.
  - Cấu trúc dữ liệu được tối ưu cho từng kiểu (module 3.1).
  - Không có lock giữa các lệnh: chỉ một thread chạy lệnh nên không có hai lệnh tranh nhau sửa một
    key.
  - *I/O multiplexing*: một thread theo dõi hàng nghìn socket cùng lúc, nhờ cơ chế `epoll` của
    Linux báo cho biết socket nào đang có dữ liệu ([01-os-linux.md](01-os-linux.md)).
- Nút cổ chai thường là mạng và bộ nhớ, ít khi là CPU.

*Các thread phụ*
- *I/O threads* (Redis 6+, cấu hình `io-threads`): đọc và ghi socket song song trên nhiều thread.
  Lệnh vẫn chạy tuần tự trên main thread, nên tính atomic không đổi.
- Thread nền làm các việc chậm không cần chặn main thread:
  - Giải phóng bộ nhớ của key bị xoá bằng `UNLINK`, và các việc *lazyfree* khác (giải phóng bộ nhớ
    ở nền thay vì ngay lập tức).
  - `fsync` file AOF (module 2.2).

*Hệ quả của một thread*
- Một lệnh chậm chặn **mọi** client. Ví dụ:
  1. Cron job chạy `HGETALL` trên một hash có 2 triệu field.
  2. Main thread bận gom và gửi 2 triệu field đó.
  3. Trong lúc đó, mọi lệnh `GET` từ API phải xếp hàng chờ.
  4. Latency của mọi API dùng Redis tăng vọt, dù chúng chỉ cần những key rất nhỏ.
- Mỗi lệnh là *atomic*: chạy trọn vẹn, không lệnh nào chen vào giữa được.
- Nhưng chuỗi nhiều lệnh thì không atomic. PHP gọi `GET` rồi `SET` thì request khác có thể chen vào
  giữa hai lệnh (cách giải ở module 2.3).

*Lệnh nguy hiểm*
- ⚠️ `KEYS *` duyệt toàn bộ key trong một lệnh, nên chặn server suốt thời gian đó.
  - Dùng `SCAN` thay thế. `SCAN` trả mỗi lần một ít key kèm một *cursor* (con trỏ vị trí), lần sau
    gửi cursor đó để lấy tiếp.
  - `SCAN` có thể trả **trùng key** giữa các lần gọi, nên code phải chịu được việc xử lý một key
    hai lần.
- ⚠️ Lệnh *O(n)*, tức thời gian chạy tăng theo số phần tử, trên key lớn:
  - `HGETALL`, `SMEMBERS`, `LRANGE 0 -1`, `SORT`, `SUNION` trên tập lớn.
  - Thay bằng `HSCAN`/`SSCAN`/`ZSCAN`, hoặc lấy theo trang.
- ⚠️ `DEL` một key rất lớn giải phóng bộ nhớ **đồng bộ** trên main thread, nên chặn server. Dùng
  `UNLINK` (xoá ngay khỏi keyspace, giải phóng bộ nhớ ở thread nền). Xoá sạch thì dùng
  `FLUSHALL ASYNC`.

*Big key và hot key*
- *Big key* là key có value quá lớn: string nhiều MB, hoặc hash có hàng triệu phần tử.
- Tìm: `redis-cli --bigkeys`, `redis-cli --memkeys`, `MEMORY USAGE <key>`.
- Sửa:
  - Chia bucket: tách một hash lớn thành nhiều hash nhỏ theo `id % N`.
  - Nén value.
  - Không lưu blob (file, ảnh) vào Redis.
- *Hot key* là một key bị truy cập quá nhiều. Trong Redis Cluster, mọi request tới key đó dồn vào
  **một node** dù cụm có nhiều node.
- Tìm: `redis-cli --hotkeys`. Lệnh này cần `maxmemory-policy` là một policy LFU, vì Redis chỉ đếm
  tần suất truy cập của key khi dùng LFU (module 2.2).
- Sửa: L1 cache trong app, nhân bản key, đọc từ replica ([11-cache.md](11-cache.md)).

*Bảo vệ và theo dõi*
- Chặn lệnh nguy hiểm bằng ACL (Redis 6+, phân quyền theo user và lệnh) hoặc `rename-command`.
- `SLOWLOG` ghi lại các lệnh chạy lâu hơn một ngưỡng. Theo dõi nó định kỳ.

*Đối chiếu*
- Giống event loop của Node.js: một thread, không được làm việc nặng trong đó.
- Khác Memcached: Memcached chạy lệnh đa luồng.

**Đọc**
- Redis: [Diagnosing latency issues](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/) (phần single-threaded nature, slow commands, fork), [SCAN](https://redis.io/docs/latest/commands/scan/) (mục guarantees), [ACL](https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/)

**Nắm chắc khi**
- [ ] Giải thích được trong 1 phút vì sao một job cron chạy `HGETALL` trên key 2 triệu field làm mọi API chậm theo
- [ ] Viết được vòng lặp `SCAN` xoá key theo prefix mà không chặn server, và nói được vì sao có thể gặp key trùng
- [ ] Tìm được big key trên một instance Redis thật (local cũng được) bằng `--bigkeys` và `MEMORY USAGE`

#### 2.2 Redis: persistence, TTL, eviction

**Vì sao cần học:** Module này quyết định Redis mất gì khi restart hay failover, và key nào bị
xoá khi đầy RAM. Để cache, session và queue của Laravel chung một Redis là cấu hình rất phổ biến,
và cũng là nguồn sự cố rất phổ biến. Câu hỏi hay gặp: "RDB khác AOF thế nào", "Redis đầy RAM thì
sao".

**Học gì**

*Persistence: RDB*
- *Persistence* là lưu dữ liệu từ RAM xuống đĩa để restart không mất. Redis có hai cách: RDB và AOF.
- *RDB* là ảnh chụp (*snapshot*) toàn bộ dữ liệu tại một thời điểm. Cách làm:
  1. Redis gọi `fork()` tạo một process con, là bản sao của process Redis
     ([01-os-linux.md](01-os-linux.md) module 1.1).
  2. Nhờ *copy-on-write* (hai process dùng chung vùng nhớ, chỉ trang nhớ nào bị ghi mới được sao
     ra bản riêng), fork xong gần như chưa tốn thêm RAM.
  3. Process con ghi toàn bộ dữ liệu ra file `.rdb`. Process cha tiếp tục phục vụ client.
- Ưu: file nhỏ, restore nhanh.
- Nhược: mất mọi thay đổi kể từ snapshot cuối.
- ⚠️ Fork một instance nhiều GB gây khựng ngắn.
- ⚠️ Trong lúc snapshot mà ghi nhiều, nhiều trang nhớ bị sao ra, nên bộ nhớ có thể gần gấp đôi và
  bị *OOM* (hết bộ nhớ, kernel kill process). Luôn chừa RAM dư.

*Persistence: AOF*
- *AOF* (append-only file) ghi lại từng lệnh ghi vào cuối một file. Khi khởi động, Redis chạy lại
  các lệnh đó để dựng lại dữ liệu.
- `fsync` là lệnh ép OS ghi thật xuống đĩa thay vì để trong bộ đệm. Cấu hình `appendfsync` chọn
  tần suất fsync:

  | Giá trị | fsync khi nào | Mất tối đa |
  |---|---|---|
  | `always` | Sau mỗi lệnh ghi | Gần như không mất, chậm nhất |
  | `everysec` (mặc định) | Mỗi giây | Khoảng 1 giây |
  | `no` | Để OS tự quyết | Tuỳ OS, trên Linux thường khoảng 30 giây |

- File AOF lớn dần, nên Redis *rewrite* định kỳ: viết lại thành file gọn chỉ chứa trạng thái hiện
  tại.
- Bật cả RDB và AOF là phổ biến. AOF hiện đại có phần mở đầu dạng RDB để load nhanh hơn.
- Redis chỉ dùng làm cache thì có thể tắt persistence.

*Redis không bền như MySQL*
- Redis thường chạy kèm *replica*: server phụ sao chép dữ liệu từ *primary* (server chính nhận ghi).
- ⚠️ Replication của Redis là *async*: primary báo ghi thành công cho client **trước** khi replica
  nhận được. Cộng thêm fsync theo giây, Redis có thể mất ghi khi primary chết và replica được đưa
  lên thay (*failover*).
- Dữ liệu không được phép mất thì nguồn sự thật phải nằm ở DB.

*TTL và cách key hết hạn*
- *TTL* (time to live) là thời gian sống của key. Hết TTL thì key bị coi như không tồn tại.
- Redis xoá key hết hạn theo hai cách kết hợp:
  - *Lazy*: khi có ai truy cập key, Redis kiểm tra và xoá nếu đã hết hạn.
  - *Active*: định kỳ lấy mẫu ngẫu nhiên một số key có TTL và xoá những key đã hết hạn.
- Hệ quả: key hết hạn vẫn có thể chiếm RAM một lúc.
- Replica không tự xoá key hết hạn, mà chờ lệnh `DEL` từ primary gửi sang.
- ⚠️ `SET key value` ghi đè thì **xoá TTL cũ**, key thành vĩnh viễn. Muốn giữ TTL thì thêm
  `KEEPTTL`. Các lệnh sửa giá trị như `INCR`, `HSET` thì giữ nguyên TTL.
- ⚠️ `SET` rồi `EXPIRE` là hai lệnh riêng. Process crash ở giữa là để lại key sống vĩnh viễn:

  ```php
  $redis->set($key, $value);        // SAI: crash ở đây thì key không bao giờ hết hạn
  $redis->expire($key, 60);

  $redis->set($key, $value, ['EX' => 60]);   // ĐÚNG: một lệnh, atomic
  ```
- TTL cho từng field của hash: `HEXPIRE`/`HTTL`/`HPERSIST` (Redis 7.4+, Valkey 9.0+). Trước đây TTL
  chỉ đặt được cho cả key.

*Eviction khi đầy bộ nhớ*
- *Eviction* là việc Redis tự xoá bớt key khi dùng tới giới hạn `maxmemory`. Cấu hình
  `maxmemory-policy` chọn xoá key nào:

  | Policy | Xoá key nào |
  |---|---|
  | `noeviction` (mặc định) | Không xoá, lệnh ghi mới bị báo lỗi |
  | `allkeys-lru` / `allkeys-lfu` | Mọi key, ưu tiên key lâu chưa dùng (LRU) hoặc ít dùng (LFU) |
  | `volatile-lru` / `volatile-lfu` | Chỉ các key có TTL, theo LRU hoặc LFU |
  | `volatile-ttl` | Key có TTL sắp hết hạn nhất |
  | `volatile-random` / `allkeys-random` | Ngẫu nhiên, trong key có TTL hoặc trong mọi key |

- *LRU* (least recently used) là bỏ key lâu nhất chưa được dùng. *LFU* (least frequently used) là
  bỏ key ít được dùng nhất. Chi tiết ở [11-cache.md](11-cache.md) module 1.3.
- LRU/LFU của Redis là **xấp xỉ**: mỗi lần chỉ lấy mẫu `maxmemory-samples` key rồi bỏ key tệ nhất
  trong mẫu, không duyệt toàn bộ.
- ⚠️ Queue, lock, session nằm trên instance có eviction thì có thể bị xoá âm thầm: job biến mất,
  user bị đăng xuất. Tách instance cache (cho phép evict) và instance dữ liệu (`noeviction`).

**Đọc**
- Redis: [Persistence](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/) (đọc hết, phần RDB vs AOF), [EXPIRE](https://redis.io/docs/latest/commands/expire/) (mục *How Redis expires keys*), [Key eviction](https://redis.io/docs/latest/develop/reference/eviction/), [HEXPIRE](https://redis.io/docs/latest/commands/hexpire/)

**Nắm chắc khi**
- [ ] Nói được với cấu hình AOF `everysec` + replica async, những kịch bản nào làm mất ghi và mất tối đa bao nhiêu
- [ ] Chọn được `maxmemory-policy` cho 3 instance: thuần cache, session store, queue của Laravel; giải thích lý do
- [ ] Chỉ ra được bug "key cache sống vĩnh viễn" trong một đoạn code dùng `SET` rồi `EXPIRE`

#### 2.3 Redis: pipeline, transaction, Lua, messaging

**Vì sao cần học:** `Redis::pipeline`, `Redis::transaction` và `Cache::lock` của Laravel đều dựa
trên các cơ chế trong module này. Câu hỏi hay gặp: "`MULTI`/`EXEC` có rollback không", "làm sao
đọc rồi ghi atomic trong Redis", "Pub/Sub khác Stream thế nào".

**Học gì**

*Pipelining*
- *Round-trip* là một lượt gửi lệnh qua mạng rồi chờ phản hồi. Mỗi round-trip tốn thời gian mạng,
  dù lệnh chạy rất nhanh.
- *Pipelining* là gửi nhiều lệnh một lúc mà không chờ phản hồi từng lệnh, rồi nhận tất cả phản hồi
  sau.
  - Ví dụ: 100 lệnh `GET` riêng lẻ tốn 100 round-trip. Pipeline 100 lệnh đó tốn khoảng 1.
- ⚠️ Pipeline **không atomic**: lệnh của client khác vẫn có thể chen vào giữa. Nó chỉ giảm
  round-trip.

*`MULTI`/`EXEC`*
- Cách dùng:
  1. `MULTI` bắt đầu transaction.
  2. Các lệnh sau đó được xếp hàng, chưa chạy.
  3. `EXEC` chạy toàn bộ hàng đợi **liền một mạch**, không lệnh nào của client khác chen vào được.
- ⚠️ **Không rollback**: một lệnh lỗi lúc chạy (ví dụ `INCR` trên key chứa chuỗi) thì các lệnh
  khác vẫn được thực hiện. Đây là khác biệt lớn với transaction của MySQL.
- ⚠️ Không đọc được kết quả giữa chừng, vì lệnh chỉ chạy lúc `EXEC`. Nên không viết được "đọc tồn
  kho, nếu còn thì trừ" chỉ bằng `MULTI`.

*`WATCH`: check-and-set lạc quan*
- `WATCH` là *optimistic locking*: không khoá gì, chỉ kiểm tra lúc cuối xem có ai sửa không.
  1. `WATCH stock:42`.
  2. `GET stock:42`, tính toán ở phía client.
  3. `MULTI`, các lệnh ghi, `EXEC`.
  4. Nếu `stock:42` bị client khác sửa sau bước 1 thì `EXEC` trả null và không chạy gì. Client làm
     lại từ bước 1.

*Lua script*
- `EVAL` gửi một đoạn script Lua cho Redis chạy **trên server**. Cả script chạy atomic, và đọc được
  giá trị rồi quyết định ghi ngay trong script. Redis 7 có thêm *Functions*, là script được lưu sẵn
  trên server.
- Dùng cho các thao tác "đọc rồi ghi có điều kiện":
  - Nhả lock chỉ khi đúng chủ (module 2.4).
  - Rate limiter.
  - Trừ tồn kho nếu còn đủ.
- ⚠️ Script chạy lâu chặn cả server, như mọi lệnh chậm (module 2.1).
- ⚠️ Trong Redis Cluster, mọi key script dùng phải khai trong tham số `KEYS` và phải nằm cùng một
  slot (slot giải thích ở module 3.2).

*So sánh ba cách*

| | Pipeline | `MULTI`/`EXEC` | Lua |
|---|---|---|---|
| Giảm round-trip | Có | Có (khi gửi kèm pipeline) | Có |
| Không bị lệnh khác chen | Không | Có | Có |
| Đọc rồi quyết định ghi | Không | Không (phải kết hợp `WATCH`) | Có |
| Rollback khi lỗi | Không | Không | Không |

*Messaging: Pub/Sub và Stream*
- *Pub/Sub*: publisher gửi message vào một channel, mọi subscriber đang kết nối nhận được ngay.
  - Không lưu message. Subscriber offline lúc đó là mất message.
  - Hợp cho: invalidate cache cục bộ trên từng server, fan-out tới các kết nối WebSocket.
- *Stream*: log message được lưu lại tới khi bị cắt bớt (`MAXLEN`).
  - Consumer group chia message cho nhiều worker.
  - Worker xử lý xong thì `XACK` (xác nhận). Message đã giao mà chưa ack nằm trong *pending list*.
  - `XAUTOCLAIM` cho worker khác nhận lại message đang pending quá lâu của một worker đã chết.

| | Pub/Sub | Stream |
|---|---|---|
| Lưu message | Không | Có, tới khi trim |
| Subscriber offline | Mất message | Đọc tiếp khi quay lại |
| Xác nhận đã xử lý | Không | `XACK`, pending list |
| Hợp cho | Tín hiệu tức thời, mất cũng không sao | Job, event cần xử lý chắc chắn |

- ⚠️ Stream không thay được Kafka khi cần giữ dữ liệu lâu, throughput rất lớn, hoặc đọc lại
  (*replay*) nhiều ngày, vì dữ liệu nằm trong RAM ([12-messaging.md](12-messaging.md)).

**Đọc**
- Redis: [Pipelining](https://redis.io/docs/latest/develop/using-commands/pipelining/), [Transactions](https://redis.io/docs/latest/develop/using-commands/transactions/) (mục *Errors inside a transaction* và *Optimistic locking using check-and-set*), [Scripting with Lua](https://redis.io/docs/latest/develop/programmability/eval-intro/), [Pub/Sub](https://redis.io/docs/latest/develop/pubsub/), [Streams](https://redis.io/docs/latest/develop/data-types/streams/) (phần consumer group)

**Nắm chắc khi**
- [ ] Giải thích được khác nhau giữa pipeline, `MULTI`/`EXEC` và Lua bằng một ví dụ trừ tồn kho
- [ ] Viết được Lua nhả lock chỉ khi đúng token
- [ ] Nói được khi nào dùng Pub/Sub, khi nào dùng Stream, khi nào phải lên Kafka/RabbitMQ

#### 2.4 Redis: use case kinh điển

**Vì sao cần học:** Lock, rate limit, leaderboard, session là bốn bài toán Redis bị hỏi nhiều nhất
trong vòng system design. Laravel có sẵn `Cache::lock`, `RateLimiter`, session driver Redis, nhưng
người phỏng vấn muốn biết bên dưới chúng làm gì và gãy ở đâu.

**Học gì**

*Distributed lock*
- *Distributed lock* là khoá dùng chung giữa nhiều process hoặc nhiều server, để chỉ một bên được
  làm một việc tại một thời điểm. Ví dụ: chỉ một worker được xử lý thanh toán cho đơn 42.
- Lấy lock: `SET lock:order:42 <token> NX PX 30000`.
  - `<token>` là một chuỗi ngẫu nhiên riêng cho mỗi lần lấy lock, để chứng minh "ai đang giữ".
  - `NX` bảo đảm chỉ một bên lấy được. `PX 30000` bảo đảm lock tự hết hạn nếu bên giữ chết.
- Nhả lock bằng Lua: chỉ `DEL` nếu giá trị đang lưu đúng bằng token của mình. Không `DEL` thẳng,
  vì có thể xoá nhầm lock của người khác:
  1. Worker A lấy lock, hạn 30 giây.
  2. A chạy chậm, lock hết hạn ở giây 30.
  3. Worker B lấy được lock.
  4. A chạy xong, gọi `DEL`, xoá mất lock **của B**.
  5. Worker C lấy lock, và B với C cùng chạy.
- ⚠️ Lock hết hạn khi việc chưa xong thì hai bên cùng chạy. Nguyên nhân: GC pause (runtime tạm dừng
  toàn bộ để dọn bộ nhớ), request chậm, mạng chậm.
- ⚠️ Failover async có thể làm mất lock: primary nhận lock rồi chết trước khi kịp gửi sang replica,
  replica lên thay không biết lock đó.
- Cách chặn triệt để: *fencing token*, tức một số tăng dần được cấp kèm mỗi lần lấy lock. Tài
  nguyên đích (DB, service) từ chối mọi thao tác mang số nhỏ hơn số lớn nhất nó đã thấy. Hoặc dùng
  lock trong DB. Redlock và tranh luận xung quanh: [14-distributed-systems.md](14-distributed-systems.md).

*Rate limiter*
- *Rate limiter* giới hạn số request trong một khoảng thời gian, ví dụ 100 request/phút mỗi user.

| Thuật toán | Cách làm | Ưu | Nhược |
|---|---|---|---|
| Fixed window | `INCR rl:{user}:{phút}` + `EXPIRE` | Đơn giản, rất rẻ | Cho phép gấp đôi ở ranh giới hai cửa sổ |
| Sliding window log | Sorted set, score là thời điểm request: `ZREMRANGEBYSCORE` xoá cũ, `ZCARD` đếm, `ZADD` thêm | Chính xác | Tốn bộ nhớ theo số request |
| Token bucket / sliding window counter | Lua để atomic | Cân bằng giữa chính xác và bộ nhớ | Phức tạp hơn |

- Vì sao fixed window cho phép gấp đôi: user gửi 100 request ở giây 59 của phút 1 và 100 request ở
  giây 0 của phút 2. Hai cửa sổ khác nhau nên đều lọt, tức 200 request trong 2 giây.
- Chi tiết và thiết kế API: [09-api-design.md](09-api-design.md).

*Leaderboard*
- Cộng điểm: `ZINCRBY lb 10 user:42`.
- Top 100: `ZRANGE lb 0 99 REV WITHSCORES` (cú pháp `REV` có từ Redis 6.2).
- Hạng của một user: `ZREVRANK lb user:42`.
- ⚠️ Bằng điểm thì Redis sort theo tên member, không theo ai đạt trước.
  - Muốn "ai đạt trước xếp trên" thì mã hoá thời gian vào score, ví dụ phần nguyên là điểm, phần
    lẻ là thời gian đảo ngược.
  - Nhớ score là số thực 64-bit (*double*), chỉ biểu diễn chính xác số nguyên tới khoảng 2^53, nên
    không nhét được quá nhiều chữ số.
- Key theo kỳ (`lb:2026-09`) kèm TTL để bảng cũ tự dọn.
- Hàng trăm triệu user thì chia bucket theo khoảng điểm, hoặc chỉ giữ top N.

*Session store*
- Lưu session trong hash kèm TTL, gia hạn TTL mỗi request.
- ⚠️ Instance có eviction, hoặc không có persistence mà restart, là mất session: đăng xuất hàng
  loạt user.

*Counter và view count*
- `INCR` trên Redis ở mỗi lượt xem, rồi job định kỳ flush dồn về DB theo batch.
- Chấp nhận mất một ít lượt đếm khi Redis chết giữa hai lần flush.

**Đọc**
- Redis: [Distributed Locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/), [SET](https://redis.io/docs/latest/commands/set/) (các option `NX`, `PX`, `KEEPTTL`, `GET`)
- Martin Kleppmann: [How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) (bắt buộc đọc trước khi trả lời câu về Redlock)

**Nắm chắc khi**
- [ ] Vẽ được timeline hai worker cùng giữ lock do lock hết hạn, và chỉ ra fencing token chặn ở đâu
- [ ] Viết được leaderboard có xử lý bằng điểm, lấy top 10 và hạng của một user
- [ ] Viết được rate limiter sliding window bằng Lua (bài tập 1)

#### 2.5 MongoDB

**Vì sao cần học:** MongoDB là document DB phổ biến nhất, hay gặp ở dự án cần schema linh hoạt hoặc
team Node.js. Người phỏng vấn hỏi để xem bạn thiết kế theo tư duy document, hay chỉ bê nguyên các
bảng SQL sang thành collection.

**Học gì**

*Document và aggregate*
- MongoDB lưu *document* (dạng BSON, tối đa 16 MB mỗi document) trong các *collection* (tương đương
  bảng).
- Thiết kế quanh **aggregate**: những gì luôn được đọc và ghi cùng nhau thì để chung một document.
  - Ví dụ: đơn hàng kèm các dòng hàng và địa chỉ giao là một document.

*Embedding hay referencing*

| | Embedding (nhúng) | Referencing (tham chiếu) |
|---|---|---|
| Là gì | Dữ liệu con nằm bên trong document cha | Lưu id, dữ liệu con ở collection khác |
| Hợp khi | Quan hệ 1-ít, dữ liệu con không đứng riêng | Quan hệ 1-nhiều không giới hạn, n-n |
| Đọc | Một lần đọc là đủ | `$lookup` (join giữa collection) hoặc query thứ hai |
| Ghi | Update atomic trong một document | Nhiều document, cần transaction nếu muốn atomic |

- ⚠️ Mảng tăng không giới hạn phá embedding. Ví dụ nhúng comment vào bài viết, bài viral có hàng
  trăm nghìn comment làm document phình tới 16 MB.
  - Sửa: tách comment ra collection riêng, hoặc *bucket pattern* (mỗi document chứa một nhóm, ví
    dụ 100 comment).

*Index*
- Các loại index:
  - single (một field), compound (nhiều field).
  - multikey: index trên field là mảng, mỗi phần tử một entry.
  - text, geo.
  - TTL: tự xoá document sau một thời gian.
  - partial: chỉ index document thoả điều kiện.
  - unique, wildcard (index mọi field theo một mẫu đường dẫn).
- Compound index theo quy tắc **ESR**: field so sánh bằng (*Equality*) trước, rồi field dùng để
  *Sort*, rồi field so sánh khoảng (*Range*). Cùng tinh thần leftmost prefix trong
  [03-database-sql.md](03-database-sql.md) module 1.2 và 2.2.
  - Ví dụ query `status = 'paid'`, sort theo `created_at`, lọc `total > 100` thì index là
    `{status: 1, created_at: 1, total: 1}`.

*Đọc plan và aggregation*
- `explain("executionStats")` là `EXPLAIN` của MongoDB.
  - `COLLSCAN` nghĩa là quét cả collection (full scan).
  - So `totalDocsExamined` (số document đã đọc) với `nReturned` (số trả về). Chênh lệch lớn là
    index chưa tốt.
- *Aggregation pipeline* là chuỗi bước xử lý nối nhau, mỗi bước (*stage*) nhận kết quả bước trước:
  `$match` (lọc) → `$group` (gom nhóm) → `$sort` → `$project` (chọn field). Thêm `$lookup` để join,
  `$unwind` để tách mảng thành nhiều document.
  - Đặt `$match` càng sớm càng tốt để giảm dữ liệu cho các bước sau.
  - ⚠️ Mỗi stage có giới hạn bộ nhớ. Tập dữ liệu lớn cần `allowDiskUse` để được ghi tạm ra đĩa.

*Transaction*
- Thao tác trên **một document** luôn atomic.
- Transaction nhiều document có từ 4.0 (replica set) và 4.2 (sharded cluster).
  - Đắt hơn nhiều, và có giới hạn thời gian chạy.
- Cần rất nhiều transaction nhiều document thường là dấu hiệu dữ liệu nên được mô hình hoá dạng
  quan hệ.

*Write concern, read concern, read preference*
- MongoDB thường chạy dạng *replica set*: một *primary* nhận ghi, các *secondary* sao chép từ
  primary.
- Ba cấu hình quyết định độ an toàn và độ mới của dữ liệu:

| Cấu hình | Quyết định gì | Giá trị |
|---|---|---|
| Write concern | Bao nhiêu node xác nhận thì báo ghi thành công | `w:1` (chỉ primary), `w:"majority"` (đa số, mặc định từ 5.0), `j:true` (đã ghi journal, tức log trên đĩa) |
| Read concern | Đọc dữ liệu ở mức đảm bảo nào | `local` (bản hiện có trên node, có thể bị rollback sau này), `majority` (đã được đa số xác nhận), `linearizable`, `snapshot` |
| Read preference | Đọc từ node nào | `primary` (mặc định), `secondary`, `nearest` |

- ⚠️ Đọc từ secondary có thể gặp dữ liệu cũ, vì secondary sao chép có độ trễ.

*Change streams*
- *Change streams* cho phép subscribe (đăng ký nhận) mọi thay đổi của một collection, database hoặc
  cả cluster. Cần replica set hoặc sharded cluster.
- Mỗi sự kiện có *resume token*: mất kết nối thì dùng token đó để đọc tiếp từ đúng chỗ đã dừng.
- Dùng làm CDC (bắt thay đổi để đẩy sang hệ khác, module 2.7) sang search, invalidate cache,
  outbox.
- ⚠️ Change streams đọc từ *oplog*, là log thao tác có kích thước giới hạn mà secondary dùng để sao
  chép. Resume token chỉ dùng được khi thay đổi đó còn trong oplog. Consumer dừng lâu hơn cửa sổ
  oplog thì phải đồng bộ lại toàn bộ.

**Đọc**
- MongoDB: [Data Model Design](https://www.mongodb.com/docs/manual/core/data-model-design/), [ESR Guideline](https://www.mongodb.com/docs/manual/tutorial/equality-sort-range-guideline/), [Aggregation](https://www.mongodb.com/docs/manual/aggregation/), [Transactions](https://www.mongodb.com/docs/manual/core/transactions/) (mục production considerations), [Write Concern](https://www.mongodb.com/docs/manual/reference/write-concern/), [Read Concern](https://www.mongodb.com/docs/manual/reference/read-concern/), [Read Preference](https://www.mongodb.com/docs/manual/core/read-preference/), [Change Streams](https://www.mongodb.com/docs/manual/changestreams/) (mục resume a change stream)

**Nắm chắc khi**
- [ ] Thiết kế được collection cho blog (bài, tác giả, comment, tag), bảo vệ được chỗ nào embed, chỗ nào reference
- [ ] Cho một query và index, dùng ESR nói được index nào tốt hơn
- [ ] Giải thích được `w:1` + đọc `local` có thể trả dữ liệu mà sau đó bị rollback như thế nào

#### 2.6 Elasticsearch/OpenSearch: analyzer, mapping, tiếng Việt, relevance

**Vì sao cần học:** Làm search tiếng Việt có dấu và không dấu là việc thật ở mọi dự án Việt Nam, và
"có mà tìm không ra" là bug rất phổ biến. Người phỏng vấn hay hỏi analyzer, mapping, vì sao ghi xong
search không thấy, và cách phân trang sâu.

**Học gì**

*Analyzer lúc index và lúc search*
- Văn bản đi qua analyzer (module 1.3) hai lần: khi index document, và khi phân tích câu query.
  Mặc định dùng cùng một analyzer. Có thể đặt `search_analyzer` riêng cho lúc search.
- ⚠️ Lệch analyzer là nguồn "tìm không ra" kinh điển. Ví dụ: index có folding (bỏ dấu) nên lưu
  term `ao`, còn query không folding nên tìm term `áo`, không khớp.
- Kiểm tra bằng API `_analyze`: đưa một chuỗi vào, xem analyzer tách ra những token nào.

*Segment: cách ES lưu index*
- Elasticsearch dựa trên thư viện Lucene. Lucene lưu index thành nhiều *segment*, mỗi segment là
  một index nhỏ **bất biến** (ghi một lần, không sửa).
- Ghi mới thì tạo segment mới. Chạy nền, các segment nhỏ được *merge* (gộp) thành segment lớn.
  Cùng tư duy với *LSM tree* (ghi vào cấu trúc mới rồi gộp dần ở nền, module 3.4).
- Vì segment bất biến, update một document là hai bước:
  1. Đánh dấu xoá bản cũ.
  2. Thêm bản mới vào segment mới.

*Tiếng Việt*
- Tiếng Việt viết cách nhau theo **âm tiết**, không theo từ: "điện thoại" là hai âm tiết nhưng một
  từ. Tokenizer chuẩn tách theo âm tiết.
- Để khớp theo từ, có ba cách:
  - `match_phrase`: yêu cầu các âm tiết đứng liền nhau đúng thứ tự.
  - *Shingle*: ghép các âm tiết liền nhau thành token, ví dụ "điện thoại" thành thêm token
    `điện thoại`.
  - Plugin tách từ tiếng Việt: plugin cộng đồng, phải kiểm tra tương thích phiên bản.
- Người gõ không dấu:
  - `asciifolding`/`icu_folding` bỏ dấu, kể cả "đ" thành "d".
  - Dùng *multi-field*: một field giữ dấu, một sub-field đã folding. Query cả hai, và **boost**
    (tăng trọng số) field có dấu để kết quả đúng dấu lên trước.
- ⚠️ Folding làm mất nghĩa: "bán" và "bạn" cùng thành "ban". Đó là lý do phải giữ field có dấu.
- ⚠️ Cùng một chữ có dấu có thể được mã hoá Unicode theo hai cách (dựng sẵn hoặc tổ hợp), nhìn
  giống nhau nhưng khác byte. Chuẩn hoá về dạng NFC trước khi index
  ([22-practical-data.md](22-practical-data.md)).
- Autocomplete (gợi ý khi đang gõ):
  - `edge_ngram`: index mọi tiền tố của từ, ví dụ "điện" thành `đ`, `đi`, `điệ`, `điện`.
  - Hoặc *completion suggester*, cấu trúc chuyên cho gợi ý.
  - ⚠️ ngram làm index phình to.

*Mapping*
- *Mapping* là schema của index: field nào kiểu gì, dùng analyzer nào.
- ⚠️ *Dynamic mapping* (ES tự đoán kiểu khi gặp field mới) có hai vấn đề:
  - Đoán sai kiểu. Ví dụ giá trị đầu tiên là `"123"` thì field thành text, sau này không sort số được.
  - *Mapping explosion*: JSON có key động (ví dụ key là id người dùng) tạo ra hàng nghìn field, làm
    cluster nặng.
  - Sửa: khai mapping tường minh, đặt `dynamic: strict` (từ chối field lạ) hoặc `false` (lưu nhưng
    không index).
- Không đổi được kiểu của field đã tồn tại. Muốn đổi thì phải reindex sang index mới (module 3.5).

*Near real-time*
- Document mới chỉ tìm thấy được sau một lần *refresh* (tạo segment mới để search nhìn thấy). Mặc
  định refresh mỗi 1 giây. Vì vậy gọi là *near real-time*.
- Hệ quả:
  - Test kiểu "ghi xong search ngay" hay fail. Dùng `refresh=wait_for` khi thật sự cần.
  - Bulk import lớn thì tăng `refresh_interval` để đỡ tốn tài nguyên.
  - `GET` theo id thì realtime, không cần chờ refresh.
- Dữ liệu chưa refresh vẫn bền vì đã được ghi vào *translog* (log ghi của ES).

*Relevance*
- ES chấm điểm độ liên quan bằng *BM25*, dựa trên ba yếu tố:
  - Tần suất term trong document: xuất hiện nhiều thì điểm cao, nhưng có bão hoà (lặp 100 lần không
    hơn 10 lần bao nhiêu).
  - *IDF* (inverse document frequency): term hiếm trong toàn bộ dữ liệu thì có giá trị hơn term phổ
    biến.
  - Độ dài field: khớp trong tiêu đề ngắn giá trị hơn khớp trong mô tả dài.
- Chỉnh điểm: boost theo field, `function_score` (cộng điểm theo độ mới, độ phổ biến), synonym.
- ⚠️ Điểm được tính theo từng *shard* (một phần của index, module 3.5). Dữ liệu ít thì mỗi shard có
  thống kê khác nhau, và xếp hạng có thể bị lệch.

*Deep pagination*
- `from + size` bị giới hạn bởi `index.max_result_window` (mặc định 10000). Trang càng sâu càng tốn,
  vì mọi shard phải lấy `from + size` kết quả rồi gộp lại.
- Cách đúng là `search_after` kèm *PIT* (point in time, giữ một ảnh chụp cố định của index để các
  trang nhất quán). Cùng ý tưởng keyset pagination trong [03-database-sql.md](03-database-sql.md)
  module 2.3.
- Scroll không còn được khuyến nghị cho deep pagination.

**Đọc**
- Elastic: [Text analysis](https://www.elastic.co/docs/manage-data/data-store/text-analysis) (phần test analyzer, index/search analyzer), [ASCII folding token filter](https://www.elastic.co/docs/reference/text-analysis/analysis-asciifolding-tokenfilter), [Multi-fields](https://www.elastic.co/docs/reference/elasticsearch/mapping-reference/multi-fields), [Near real-time search](https://www.elastic.co/docs/manage-data/data-store/near-real-time-search), [Similarity settings](https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity) (BM25), [Paginate search results](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/paginate-search-results)

**Nắm chắc khi**
- [ ] Viết được mapping cho `products` hỗ trợ có dấu, không dấu, ưu tiên khớp đúng dấu (bài tập 3)
- [ ] Dùng `_analyze` chỉ ra được token của "Điện thoại Samsung" với analyzer chuẩn và analyzer có folding
- [ ] Giải thích được vì sao trang 1000 của kết quả tìm kiếm chậm và sửa bằng `search_after`

#### 2.7 Đồng bộ dữ liệu từ DB sang search

**Vì sao cần học:** Có search engine thì phải đồng bộ dữ liệu từ DB sang. Lệch dữ liệu giữa MySQL và
Elasticsearch là loại bug khó thấy: không có lỗi nào, chỉ là search trả giá cũ hoặc thiếu sản phẩm.
Laravel Scout làm việc này, và có lỗ hổng mà người phỏng vấn hay hỏi.

**Học gì**

*Ba cách đồng bộ*

| Cách | Làm thế nào | Ưu | Nhược |
|---|---|---|---|
| Dual write | App ghi DB, rồi ghi ES | Đơn giản | Một bên fail là lệch; hai request đan xen ghi sai thứ tự |
| Outbox + queue | Ghi DB và một dòng vào bảng outbox trong **cùng transaction**, worker đọc outbox đẩy sang ES | Không mất sự kiện, retry được | Trễ vài giây |
| CDC | Tool đọc log thay đổi của DB rồi đẩy sang ES | Bắt mọi thay đổi, kể cả sửa tay trong DB | Hạ tầng nặng; event ở mức bảng, không ở mức nghiệp vụ |

- *CDC* (change data capture) là bắt mọi thay đổi trực tiếp từ log của DB. Ví dụ:
  - Debezium đọc *binlog* (log mọi thay đổi của MySQL, vốn dùng cho replication) → Kafka → ES.
  - MongoDB change streams (module 2.5), DynamoDB Streams.
- Outbox và CDC chi tiết: [12-messaging.md](12-messaging.md).

*Giữ đúng thứ tự*
- ⚠️ Dual write với hai request đan xen:
  1. Request A sửa giá thành 100, ghi DB.
  2. Request B sửa giá thành 120, ghi DB. DB giờ là 120.
  3. B ghi ES giá 120.
  4. A ghi ES giá 100, vì A chạy chậm hơn.
  5. ES giữ 100, DB là 120, và không có lỗi nào được báo.
- Hai cách sửa:
  - *External version*: gửi kèm version lấy từ DB (số version hoặc `updated_at`) với
    `version_type=external`. ES từ chối bản ghi có version nhỏ hơn bản đang có.
  - Chỉ gửi id qua queue. Worker đọc **bản mới nhất** từ DB rồi ghi ES, nên thứ tự đến không còn
    quan trọng.

*Đối soát và reindex*
- Có job đối soát định kỳ so DB với ES để bắt các ca lệch.
- Có sẵn cách reindex toàn bộ từ DB, vì search là bản sao (module 1.3, 3.5).

*Laravel Scout*
- ⚠️ Scout đồng bộ qua model event (`saved`, `deleted` của Eloquent), về bản chất là dual write.
- Update hàng loạt bằng query builder, ví dụ `Product::where(...)->update([...])`, chạy thẳng một
  câu SQL, không load model nên **không bắn event**. Index lệch âm thầm.

**Đọc**
- DynamoDB: [Change data capture for DynamoDB Streams](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html) (đối chiếu cách một DB managed cung cấp CDC)
- DDIA ch.11, mục *Change Data Capture* và *Keeping Systems in Sync* (bản 1)
- Laravel: [Scout: Indexing](https://laravel.com/docs/scout#indexing) và [Queueing](https://laravel.com/docs/scout#queueing)

**Nắm chắc khi**
- [ ] Vẽ được timeline hai lần sửa giá đan xen làm ES giữ giá cũ khi dùng dual write, và chỉ ra external version sửa thế nào
- [ ] Liệt kê được 3 đường ghi trong một app Laravel có thể bỏ qua Scout

#### 2.8 Object storage nâng cao

**Vì sao cần học:** Upload file lớn, lưu backup, giữ chi phí S3 không phình là việc của mid và
senior. Câu hỏi hay gặp: "upload video 2 GB thế nào", "S3 có consistency gì", và các lỗi bảo mật
kiểu bucket public nhầm.

**Học gì**

*Multipart upload*
- *Multipart upload* chia file lớn thành nhiều phần (*part*) để upload riêng:
  1. Gọi `CreateMultipartUpload`, nhận một upload id.
  2. Upload các part song song. Part nào lỗi thì gửi lại đúng part đó, không phải gửi lại cả file.
  3. Gọi `CompleteMultipartUpload` với danh sách part để S3 ghép thành một object.
- Giới hạn: part tối thiểu 5 MB (trừ part cuối), tối đa 10000 part.
- ⚠️ Multipart dở dang (không complete, không abort) vẫn chiếm dung lượng và **vẫn tính tiền**. Đặt
  lifecycle rule tự abort sau vài ngày.

*Kiểm soát file được upload*
- ⚠️ Presigned PUT không giới hạn được kích thước. Dùng *presigned POST* với *policy*, trong đó
  `content-length-range` giới hạn kích thước, và điều kiện về content type.
- Vẫn kiểm tra lại sau upload:
  - *Magic bytes*: vài byte đầu file cho biết loại thật, không tin phần đuôi tên file.
  - Quét virus.

*Consistency*
- Từ tháng 12/2020, S3 có *strong read-after-write consistency* cho PUT, DELETE và LIST: ghi xong
  thì mọi lần đọc sau đều thấy bản mới.
- Storage tương thích S3 khác (MinIO, dịch vụ của nhà cung cấp khác) có thể không đảm bảo giống vậy.

*Conditional write*
- *Conditional write* là ghi có điều kiện, S3 chỉ ghi nếu điều kiện đúng:
  - `If-None-Match: *` (từ 08/2024): chỉ ghi khi key **chưa tồn tại**. Chống hai tiến trình cùng tạo
    một file và đè nhau.
  - `If-Match: <ETag>` (từ 11/2024): chỉ ghi khi object **chưa đổi**. *ETag* là mã định danh nội
    dung của một phiên bản object.
- Luồng dùng `If-Match`, là *optimistic concurrency* trên S3:
  1. Đọc object, nhớ ETag.
  2. Sửa nội dung ở phía app.
  3. Ghi lại kèm `If-Match: <ETag đã nhớ>`.
  4. Có ai ghi trước thì ETag đã khác, S3 từ chối (lỗi 412). Đọc lại và làm lại.
- Bucket policy có thể bắt buộc mọi lần ghi phải kèm hai header này.

*Lifecycle và storage class*
- *Storage class* là các hạng lưu trữ với giá khác nhau: Standard, Infrequent Access (ít truy cập),
  Glacier (lưu trữ lạnh).
- *Lifecycle rule* tự chuyển object sang class rẻ hơn theo tuổi, rồi xoá.
- ⚠️ Class lạnh có phí truy xuất, cần thời gian để lấy lại, và có thời gian lưu tối thiểu (xoá sớm
  vẫn bị tính tiền).

*Versioning và Object Lock*
- *Versioning*: mỗi lần ghi đè hoặc xoá, bản cũ được giữ lại thành *noncurrent version*. Chống ghi
  đè và xoá nhầm.
- *Object Lock*: khoá object không cho xoá hay sửa trong một thời hạn, kể cả với admin. Dùng cho
  backup chống ransomware.
- ⚠️ Bật versioning mà không có lifecycle cho noncurrent version thì dung lượng và tiền cứ tăng mãi.

*Hiệu năng và bảo mật*
- Mỗi prefix (phần đầu của key, ví dụ `uploads/2026/`) chịu khoảng 3500 PUT và 5500 GET mỗi giây.
- Tải lớn thì rải key qua nhiều prefix.
- Bật Block Public Access.
- IAM theo quyền tối thiểu: mỗi service chỉ được đúng các bucket và hành động cần.
- Mã hoá at rest (dữ liệu được mã hoá khi nằm trên đĩa).
- Không để credential ở client, dùng presigned URL.
- ⚠️ Bucket public nhầm là nguồn lộ dữ liệu rất phổ biến ([10-security.md](10-security.md)).

**Đọc**
- S3: [Multipart upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html), [Conditional requests](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-requests.html) và [Conditional writes](https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html), [S3 consistency](https://aws.amazon.com/s3/consistency/), [Lifecycle](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html), [Versioning](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html), [Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html), [Optimizing performance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/optimizing-performance.html)

**Nắm chắc khi**
- [ ] Thiết kế được upload video 2GB: presigned multipart, resume khi rớt mạng, dọn part dở dang, xử lý async sau upload
- [ ] Dùng `If-Match` viết được luồng cập nhật một file cấu hình JSON trên S3 mà hai tiến trình không ghi đè mất sửa đổi của nhau

#### 2.9 Tầng PHP: Redis client, Laravel Redis, Scout, Elasticsearch client, S3

**Vì sao cần học:** Module riêng cho người làm PHP. Người phỏng vấn hay hỏi vào chỗ PHP-FPM giao với
các hệ thống này: số connection, cấu hình client, và những lệnh Laravel tưởng vô hại nhưng xoá mất
dữ liệu.

**Học gì**

*Redis client*

| | phpredis | Predis |
|---|---|---|
| Là gì | C extension | Thư viện thuần PHP |
| Tốc độ | Nhanh hơn | Chậm hơn |
| Cài đặt | Cần cài extension | Chỉ cần Composer |
| Trong Laravel | Mặc định (`REDIS_CLIENT=phpredis`) | Chọn bằng `REDIS_CLIENT=predis` |

- Serializer và compression của phpredis (igbinary, lz4, ...): phpredis tự chuyển value sang dạng
  gọn hơn trước khi lưu.
  - ⚠️ Đổi cấu hình này là không đọc được dữ liệu cũ đang nằm trong Redis.

*Connection từ PHP-FPM*
- PHP-FPM mở connection mới cho mỗi request, trừ khi dùng *persistent connection* (giữ connection
  sống qua nhiều request trong cùng worker).
- Tổng số connection tới Redis bằng số worker trên **mọi** server cộng lại.
  - Ví dụ: 4 server, mỗi server 50 worker FPM, dùng persistent connection thì khoảng 200 connection.

*Prefix và Cluster trong Laravel*
- Laravel tự thêm prefix (`REDIS_PREFIX`, prefix của cache) vào key cho các lệnh thường.
  - ⚠️ Với Lua `EVAL`, prefix không được thêm vào key bên trong script, phải tự xử lý.
- Redis Cluster trong Laravel: cấu hình ở mục `clusters`.
  - ⚠️ Lệnh nhiều key và Lua cần *hash tag* để mọi key nằm cùng slot (module 3.2).

*Laravel dùng Redis ở đâu*
- Cache, session.
- Queue: list cho job chờ, sorted set cho delayed job. Horizon là dashboard quản lý queue Redis.
- `Cache::lock` (distributed lock), `Redis::throttle` (rate limit), `Redis::funnel` (giới hạn số
  job chạy đồng thời).
- Tách connection hoặc DB Redis cho cache và queue, để `php artisan cache:clear` không xoá job
  (chi tiết ở [11-cache.md](11-cache.md) module 2.7).

*Search trong PHP*
- Laravel Scout có driver chính thức cho Algolia, Meilisearch, Typesense, database, collection.
- Elasticsearch không có driver chính thức: dùng driver cộng đồng, hoặc dùng thẳng client.
- `elasticsearch-php` là client chính thức. Import lớn thì dùng bulk API (gửi nhiều document trong
  một request), không index từng document trong vòng lặp.
- Cấu hình Scout `queue => true` để index qua queue, không làm chậm request của người dùng.

*S3 trong Laravel*
- `Storage::disk('s3')`, `temporaryUrl` (presigned URL để tải), `temporaryUploadUrl` (presigned URL
  để upload).
- File lớn thì stream (`putFile`, `readStream`), không dùng `get()`, vì `get()` đọc cả file vào RAM
  của worker.

**Đọc**
- Laravel: [Redis](https://laravel.com/docs/redis) (mục [phpredis](https://laravel.com/docs/redis#phpredis), [Predis](https://laravel.com/docs/redis#predis), [clusters](https://laravel.com/docs/redis#clusters), [pipelining](https://laravel.com/docs/redis#pipelining-commands)), [Scout](https://laravel.com/docs/scout), [Filesystem: S3](https://laravel.com/docs/filesystem#s3-driver-configuration) và [Automatic streaming](https://laravel.com/docs/filesystem#automatic-streaming)
- [phpredis](https://github.com/phpredis/phpredis) (README: persistent connection, serializer), [Predis](https://github.com/predis/predis)
- Elastic: [PHP client](https://www.elastic.co/docs/reference/elasticsearch/clients/php); driver cộng đồng [elastic-scout-driver](https://github.com/babenkoivan/elastic-scout-driver)
- Runtime PHP-FPM: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Giải thích được vì sao `php artisan cache:clear` có thể làm mất job trong queue, và cấu hình để tránh
- [ ] Tính được số connection Redis tối đa của hệ thống mình đang làm
- [ ] Viết được lệnh import 1 triệu sản phẩm vào Elasticsearch bằng bulk API theo chunk, có retry

---

### Chặng 3: Senior 🔴

#### 3.1 Bên trong Redis: encoding

**Vì sao cần học:** Module này giải thích vì sao cùng một lượng dữ liệu mà Redis tốn RAM rất khác
nhau tuỳ cách tổ chức key, và trả lời câu kinh điển ở vòng senior: "sorted set được cài bằng cấu
trúc gì, vì sao".

**Học gì**

*Encoding theo kích thước*
- *Encoding* là cách Redis biểu diễn một kiểu dữ liệu trong bộ nhớ. Cùng là hash, nhưng hash nhỏ và
  hash lớn được lưu bằng cấu trúc khác nhau.
- Tập nhỏ dùng **listpack**: một mảng byte liền nhau chứa các phần tử nối tiếp.
  - Tìm một phần tử là O(n), tức phải duyệt lần lượt. Nhưng n nhỏ nên vẫn nhanh.
  - Rất tiết kiệm RAM, vì không có con trỏ hay bảng băm đi kèm.
- Khi vượt ngưỡng (ví dụ `hash-max-listpack-entries` cho số phần tử), Redis chuyển sang cấu trúc
  lớn hơn, nhanh hơn nhưng tốn RAM hơn.
- Redis 7 thay *ziplist* (cấu trúc liền mảng cũ) bằng listpack.
- Xem encoding của một key bằng `OBJECT ENCODING <key>`.
- Hệ quả thực tế: chia một hash khổng lồ thành nhiều hash nhỏ, mỗi hash dưới ngưỡng, thì mỗi hash
  được lưu dạng listpack và tổng RAM có thể giảm đáng kể.

*String*
- String được lưu bằng *SDS* (simple dynamic string), cấu trúc lưu sẵn độ dài chuỗi.
  - Nhờ vậy `STRLEN` là O(1), không phải đếm từng byte.
  - An toàn nhị phân: chứa được byte `0` ở giữa, nên lưu được dữ liệu nhị phân bất kỳ.
- Số nguyên nhỏ được lưu thẳng dạng `int`, không lưu thành chuỗi.

*List, Hash, Set*

| Kiểu | Encoding khi nhỏ | Encoding khi lớn |
|---|---|---|
| List | listpack (từ Redis 7.2) | quicklist |
| Hash | listpack | hashtable |
| Set | intset (chỉ chứa số nguyên) hoặc listpack | hashtable |

- *Quicklist* là linked list mà mỗi node là một listpack: vừa thêm bớt nhanh ở hai đầu, vừa gọn RAM.
- *Intset* là mảng số nguyên đã sắp xếp.
- Sorted set nhỏ cũng dùng listpack.

*Sorted set: skip list + hashtable*
- Sorted set lớn dùng **hai cấu trúc cùng lúc**:
  - Hashtable từ member tới score: `ZSCORE` là O(1).
  - *Skip list* sắp theo score: `ZRANGE`, `ZRANK` là O(log n + m), với m là số phần tử trả về.
- *Skip list* là linked list đã sắp xếp có thêm nhiều tầng "làn nhanh". Tầng dưới cùng chứa mọi
  phần tử, mỗi tầng trên chỉ chứa một phần ngẫu nhiên của tầng dưới. Tìm kiếm bắt đầu từ tầng trên
  cùng, nhảy xa, rồi xuống dần để tinh chỉnh.
- Vì sao chọn skip list thay vì cây cân bằng:
  - Cài đặt đơn giản hơn nhiều.
  - Duyệt một khoảng rất tự nhiên: tìm điểm đầu rồi đi dọc tầng dưới cùng.
  - Độ phức tạp kỳ vọng tương đương cây cân bằng.
- Redis thêm *span* vào mỗi liên kết (liên kết đó nhảy qua bao nhiêu phần tử). Cộng span dọc đường
  đi là ra hạng, nên `ZRANK` nhanh.

*Rehash tăng dần*
- Hashtable đầy thì phải *rehash*: tạo bảng lớn hơn và chuyển mọi phần tử sang.
- Chuyển hàng triệu phần tử một lúc sẽ chặn server (module 2.1). Nên Redis rehash **tăng dần**:
  1. Giữ hai bảng song song, cũ và mới.
  2. Mỗi lệnh chạm vào hashtable thì chuyển thêm một ít phần tử sang bảng mới.
  3. Trong lúc chuyển, tra cứu tìm ở cả hai bảng.
  4. Chuyển xong thì bỏ bảng cũ.

**Đọc**
- Redis: [Memory optimization](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/) (phần special encoding of small aggregate data types)
- Skip list và độ phức tạp: [21-dsa.md](21-dsa.md)

**Nắm chắc khi**
- [ ] Giải thích được vì sao chia 1 triệu user thành hash nhỏ theo bucket có thể tiết kiệm nhiều RAM
- [ ] Vẽ được skip list và đường đi của `ZRANGEBYSCORE`

#### 3.2 Redis HA: replication, Sentinel, Cluster, license

**Vì sao cần học:** Khi Redis giữ session, queue, lock, thì "Redis chết" là sự cố lớn. Senior phải
chọn được giữa một instance, Sentinel và Cluster, và biết mỗi cách mất dữ liệu ra sao. Câu hỏi hay
gặp: "vì sao `MGET` lỗi trên Cluster", "Redis hay Valkey".

**Học gì**

*Replication*
- *Replication*: replica sao chép dữ liệu từ primary. Replication của Redis là async (module 2.2).
- Replica mất kết nối rồi nối lại thì cố *partial resync*: chỉ lấy phần còn thiếu từ *backlog* (bộ
  đệm chứa các lệnh ghi gần nhất trên primary). Thiếu nhiều hơn backlog thì phải *full sync*:
  primary tạo RDB và gửi toàn bộ.
- `WAIT n timeout`: chờ tới khi ít nhất n replica xác nhận đã nhận các ghi trước đó. Lệnh này
  **giảm** chứ không triệt tiêu khả năng mất ghi.
- ⚠️ Đọc từ replica có thể thấy dữ liệu cũ.

*Sentinel*
- *Sentinel* là các process giám sát primary và tự động failover:
  1. Các Sentinel cùng theo dõi primary.
  2. Khi đủ *quorum* (số Sentinel tối thiểu phải đồng ý) cho rằng primary đã chết, chúng chọn một
     replica và *promote* (nâng) nó lên làm primary.
  3. Client hỏi Sentinel để biết primary hiện tại là ai, rồi kết nối tới đó.
- Cần ít nhất 3 Sentinel trên các máy khác nhau, để một máy chết không làm hỏng việc bỏ phiếu.
- Sentinel không chia dữ liệu: dùng khi toàn bộ dữ liệu vừa một máy.

*Cluster: hash slot*
- *Redis Cluster* chia dữ liệu ra nhiều primary (mỗi primary kèm replica).
- Keyspace được chia thành **16384 hash slot**: `slot = CRC16(key) mod 16384`. CRC16 là một hàm băm
  cho ra số 16 bit. Mỗi node giữ một phần các slot.
- Client giữ bảng "slot nào nằm ở node nào" và gửi lệnh thẳng tới đúng node, không cần proxy ở giữa.
- Hai kiểu chuyển hướng khi client gửi nhầm node:
  - `MOVED`: slot đã chuyển hẳn sang node khác. Client cập nhật bảng slot.
  - `ASK`: slot đang được chuyển dở. Client hỏi node kia **một lần** cho lệnh này, không cập nhật
    bảng.

*Giới hạn của Cluster*
- ⚠️ Lệnh nhiều key (`MGET`, `SUNION`, `MULTI`, Lua) chỉ chạy khi mọi key nằm cùng một slot. Không
  thì báo lỗi `CROSSSLOT`.
- *Hash tag*: nếu key có phần trong ngoặc nhọn thì chỉ phần đó được băm. `user:{42}:cart` và
  `user:{42}:profile` cùng băm `42`, nên cùng slot.
  - ⚠️ Lạm dụng hash tag (ví dụ mọi key cùng `{app}`) dồn hết dữ liệu vào một slot, tức một node.
- Cluster chỉ có database 0, không có `SELECT 1`.
- Có thể *reshard* (chuyển slot giữa các node) khi đang chạy.
- ⚠️ Cluster không đảm bảo consistency mạnh: có cửa sổ mất ghi khi failover hoặc khi mạng bị chia
  cắt.

*Chọn cách triển khai*

| | Một instance | Sentinel | Cluster |
|---|---|---|---|
| Tự failover | Không | Có | Có |
| Chia dữ liệu ra nhiều máy | Không | Không | Có |
| Lệnh nhiều key | Tự do | Tự do | Chỉ khi cùng slot |
| Hợp khi | Dev, cache mất cũng được | Dữ liệu vừa một máy, cần HA | Dữ liệu hoặc tải vượt một máy |

*License và hệ sinh thái*
- 03/2024: Redis bỏ license BSD, chuyển sang RSALv2/SSPLv1 (hai license hạn chế việc cung cấp Redis
  thành dịch vụ). Linux Foundation lập **Valkey**, fork BSD từ Redis 7.2.4, được nhiều cloud dùng
  làm Redis managed.
- Redis 8 (05/2025) thêm lựa chọn **AGPLv3** (license mã nguồn mở), và gộp JSON, Query Engine,
  TimeSeries, Bloom vào lõi.
- Hai nhánh đã bắt đầu tách tính năng, ví dụ lệnh mới ra ở một bên trước.
- Kiến thức trong file dùng được cho cả hai. Khi chọn thì xem dịch vụ managed hỗ trợ bản nào, và
  license có hợp với cách mình phân phối phần mềm không.

**Đọc**
- Redis: [Replication](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/), [Sentinel](https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/), [Scale with Redis Cluster](https://redis.io/docs/latest/operate/oss_and_stack/management/scaling/), [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) (mục key distribution, hash tags, redirection)
- License: [Redis licenses](https://redis.io/legal/licenses/), [Redis is now available under AGPLv3](https://redis.io/blog/agplv3/), [antirez: Redis is open source again](https://antirez.com/news/151), [Linux Foundation launches Valkey](https://www.linuxfoundation.org/press/linux-foundation-launches-open-source-valkey-community)

**Nắm chắc khi**
- [ ] Tính được slot của một key có hash tag và giải thích được vì sao `MGET user:1 user:2` lỗi trên Cluster
- [ ] Kể được kịch bản mất ghi khi failover Sentinel và cách giảm thiểu
- [ ] Chọn được giữa một Redis, Sentinel và Cluster cho 3 quy mô khác nhau

#### 3.3 MongoDB sharding và CAP

**Vì sao cần học:** Chọn shard key sai là lỗi gần như không sửa được khi dữ liệu đã lớn. CAP là câu
lý thuyết hay bị hỏi, và thường bị trả lời bằng nhãn "CP/AP" học thuộc. Senior phải nói được nhãn
đó phụ thuộc vào cấu hình.

**Học gì**

*Kiến trúc sharded cluster của MongoDB*
- *Sharding* là chia dữ liệu của một collection ra nhiều máy (*shard*), mỗi shard là một replica set.
- Các thành phần:
  - `mongos`: router. App kết nối tới đây, nó gửi query tới đúng shard.
  - *Config server*: giữ metadata, tức dữ liệu nào nằm ở shard nào.
  - Dữ liệu được chia theo *shard key* thành các *chunk* (khoảng giá trị của shard key).

*Chọn shard key*

| | Ranged sharding | Hashed sharding |
|---|---|---|
| Chia theo | Khoảng giá trị của shard key | Giá trị băm của shard key |
| Query theo khoảng shard key | Tốt, chỉ chạm vài shard | Phải hỏi mọi shard |
| Ghi với key tăng dần | Dồn vào một shard | Rải đều |

- ⚠️ Shard key tăng dần (ObjectId, timestamp) với ranged sharding: mọi insert mới rơi vào chunk cuối,
  tức một shard. Các shard khác ngồi chơi.
- ⚠️ Query không có shard key phải *scatter-gather*: gửi tới mọi shard rồi gộp kết quả, chậm và tốn.
- Resharding (đổi shard key) có từ 5.0, nhưng nặng. Chọn đúng từ đầu.

*CAP và PACELC*
- *Network partition* là khi mạng giữa các node bị đứt, các node vẫn chạy nhưng không nói chuyện
  được với nhau.
- *CAP*: khi có network partition, hệ thống phải chọn một trong hai:
  - *C* (consistency): từ chối phục vụ ở phía không chắc có dữ liệu mới nhất.
  - *A* (availability): vẫn phục vụ, chấp nhận có thể trả dữ liệu cũ.
- *PACELC* bổ sung: khi **không** có partition (E, else), vẫn phải đánh đổi giữa latency (L) và
  consistency (C).
- Các hệ thống nghiêng về đâu:
  - MongoDB: mỗi replica set chỉ một primary nhận ghi, nghiêng về C.
  - Cassandra, DynamoDB: nghiêng về A, consistency chỉnh được theo từng request.
  - Redis Cluster: replication async, không đảm bảo C.
  - HBase: nghiêng về C.

*Nhãn CP/AP không cố định*
- ⚠️ Nhãn "CP" hay "AP" phụ thuộc cấu hình (write concern, read concern, consistency level), không
  phải bản chất cố định của sản phẩm.
  - Ví dụ: MongoDB với `w:1` và đọc từ secondary thì hành xử khác hẳn với `w:"majority"` và đọc từ
    primary.
- Chi tiết: [14-distributed-systems.md](14-distributed-systems.md).

**Đọc**
- MongoDB: [Sharding](https://www.mongodb.com/docs/manual/sharding/), [Choose a Shard Key](https://www.mongodb.com/docs/manual/core/sharding-choose-a-shard-key/)
- DDIA ch.6 (partitioning) và ch.9 (phần về CAP)

**Nắm chắc khi**
- [ ] Chọn được shard key cho collection `orders` của SaaS nhiều tenant, nói được xử lý tenant rất lớn thế nào
- [ ] Giải thích được vì sao nói "MongoDB là CP" mà không kèm write/read concern là chưa đủ

#### 3.4 Wide-column (Cassandra) và DynamoDB

**Vì sao cần học:** Cassandra và DynamoDB buộc bạn thiết kế dữ liệu ngược với thói quen SQL: bắt đầu
từ query, không từ entity. Người phỏng vấn senior hay đưa một bài (tin nhắn, feed, IoT) để xem bạn
có chọn được partition key không bị quá rộng hay quá nóng không. Với DynamoDB, thiết kế sai là trả
tiền thẳng.

**Học gì**

*Query-first modeling*
- Liệt kê **mọi query** trước, rồi mới thiết kế bảng. Mỗi bảng phục vụ một query.
- Chấp nhận *denormalize*: cùng một dữ liệu lưu lặp ở nhiều bảng.
- Hệ quả: query mới thường nghĩa là bảng mới, cộng *backfill* (chép dữ liệu cũ vào bảng mới).

*Cassandra: key và truy vấn*
- Primary key gồm hai phần: `PRIMARY KEY ((user_id), created_at)`.
  - **Partition key** (`user_id`): quyết định dữ liệu nằm ở node nào, qua *consistent hashing* (cách
    băm key lên một vòng tròn để thêm bớt node chỉ phải chuyển ít dữ liệu).
  - **Clustering columns** (`created_at`): quyết định thứ tự các dòng bên trong partition.
- Query phải có partition key.
- `ALLOW FILTERING` cho phép query không theo key bằng cách quét và lọc, gần như luôn sai trên
  production.

*Cassandra: ghi và consistency*
- Ghi theo *LSM*: ghi vào bộ nhớ và log, rồi flush thành file bất biến và gộp dần ở nền. Ghi rất
  nhanh.
- Hai bản ghi xung đột thì *last-write-wins*: bản có timestamp mới hơn thắng.
- *Tunable consistency*: mỗi request chọn cần bao nhiêu replica trả lời: `ONE`, `QUORUM` (đa số),
  `ALL`, `LOCAL_QUORUM` (đa số trong cùng datacenter).
- Quy tắc: N là số replica, W là số replica phải xác nhận khi ghi, R là số replica phải trả lời khi
  đọc. Nếu `R + W > N` thì đọc thấy ghi mới nhất.
- *Lightweight transaction* (`IF NOT EXISTS`) dùng thuật toán đồng thuận Paxos, nên chậm.

*Cassandra: cạm bẫy*
- ⚠️ *Tombstone*: xoá trong Cassandra là **ghi thêm** một dấu "đã xoá". Đọc phải đi qua mọi
  tombstone. Dùng bảng Cassandra làm queue (ghi rồi xoá liên tục) là anti-pattern kinh điển.
- ⚠️ Partition quá rộng (một thiết bị ghi mỗi giây suốt nhiều năm) làm chậm và mất cân bằng. Sửa
  bằng bucket theo thời gian: partition key `(device_id, day)`.

*DynamoDB: key và index*
- Key là partition key, hoặc partition key + sort key.
- `Query` (theo partition key) hiệu quả. `Scan` đọc cả bảng, đắt.
- Hai loại index phụ:

| | GSI (global secondary index) | LSI (local secondary index) |
|---|---|---|
| Partition key | Khác với bảng | Giống bảng, chỉ đổi sort key |
| Tạo khi nào | Lúc nào cũng được | Chỉ lúc tạo bảng |
| Consistency | Eventually consistent | Đọc strongly consistent được |
| Capacity | Riêng | Dùng chung với bảng |

*DynamoDB: consistency và tính năng*
- Đọc mặc định là *eventually consistent*: có thể chưa thấy ghi vừa xong. Có thể yêu cầu
  *strongly consistent read* trên bảng, nhưng không trên GSI.
- Có transaction, conditional write, TTL, Streams (CDC).
- *Single-table design*: nhiều loại entity chung một bảng, phân biệt bằng tiền tố key, ví dụ
  `PK=USER#42`, `SK=ORDER#2026-09-01`. Một query lấy được user kèm đơn hàng. Mạnh, nhưng khó đọc và
  khó đổi.

*DynamoDB: capacity và hot partition*
- *RCU/WCU* (read/write capacity unit) là đơn vị năng lực đọc và ghi.

| | On-demand | Provisioned |
|---|---|---|
| Trả tiền | Theo số request | Theo RCU/WCU đặt trước |
| Co giãn | Tự động | Auto scaling, có reserved capacity |
| Hợp khi | Tải khó đoán | Tải ổn định, khi đó rẻ hơn |

- AWS đã giảm giá on-demand cuối 2024, nên on-demand thường là lựa chọn mặc định hợp lý.
- ⚠️ *Hot partition*: mỗi partition có giới hạn riêng (khoảng 3000 RCU, 1000 WCU) bất kể mode. Một
  key nóng bị *throttle* (từ chối vì vượt giới hạn) dù tổng capacity của bảng còn dư.
  - Sửa: chọn partition key có nhiều giá trị, hoặc *write sharding*: thêm hậu tố ngẫu nhiên
    (`KEY#1`..`KEY#10`) để rải ghi ra nhiều partition.
- Item tối đa 400 KB. Thiết kế sai kiểu truy cập là trả tiền thẳng.

**Đọc**
- Cassandra: [Data Modeling](https://cassandra.apache.org/doc/latest/cassandra/developing/data-modeling/index.html) (đọc hết loạt bài, có ví dụ từ query tới bảng)
- DynamoDB: [NoSQL design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-general-nosql-design.html), [Partition key design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html), [GSI](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GSI.html), [Read consistency](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.ReadConsistency.html), [Throughput capacity](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/capacity-mode.html) (so sánh [on-demand](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/on-demand-capacity-mode.html) và [provisioned](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/provisioned-capacity-mode.html))
- *The DynamoDB Book*: các chương về single-table design và strategy cho one-to-many
- DDIA ch.3 (LSM) và ch.5 (leaderless replication, quorum)

**Nắm chắc khi**
- [ ] Thiết kế được bảng "tin nhắn mới nhất của mỗi cuộc trò chuyện" cho Cassandra hoặc DynamoDB, chỉ ra partition có thể quá rộng hoặc quá nóng
- [ ] Chọn được on-demand hay provisioned cho 2 workload (flash sale thất thường, job batch ổn định) và giải thích bằng tiền
- [ ] Giải thích được vì sao `QUORUM` đọc + `QUORUM` ghi với N=3 cho đọc thấy ghi mới nhất, và khi nào điều đó vẫn gãy

#### 3.5 Vận hành search: shard, reindex, license

**Vì sao cần học:** Đưa Elasticsearch lên production là phần dễ. Phần khó là đổi mapping hay analyzer
khi index đang nhận ghi, và giữ cluster không chậm dần vì quá nhiều shard. Câu hỏi hay gặp: "đổi
analyzer không downtime thế nào", "Elasticsearch hay OpenSearch".

**Học gì**

*Shard*
- Một index được chia thành nhiều *primary shard*, mỗi shard là một index Lucene riêng, có thể nằm
  trên node khác nhau. *Replica shard* là bản sao của primary shard, để chịu lỗi và chia tải đọc.
- Số primary shard chốt lúc tạo index. Muốn đổi thì phải *split*/*shrink* (tách hoặc gộp shard theo
  bội số) hoặc reindex.
- Số replica shard đổi lúc nào cũng được.
- ⚠️ *Oversharding*: hàng nghìn shard nhỏ tốn heap và làm cluster chậm. Nhắm cỡ shard vài chục GB
  theo hướng dẫn *Size your shards*.

*Reindex không downtime*
- App đọc ghi qua một **alias** (tên ảo trỏ tới index thật), ví dụ `products` trỏ tới `products_v1`.
- Các bước:
  1. Tạo `products_v2` với mapping mới.
  2. Nạp dữ liệu vào `v2`: reindex từ DB, hoặc dùng API `_reindex` chép từ `v1`.
  3. Đổi alias từ `v1` sang `v2` trong **một** lệnh `_aliases` (atomic, không có lúc nào alias trỏ
     vào hư không).
  4. Giữ `v1` một thời gian để rollback: chỉ cần đổi alias về lại.
- ⚠️ Ghi trong lúc reindex dễ bị mất. Hai cách:
  - Ghi vào cả hai index trong suốt quá trình.
  - Ghi lại mốc thời gian lúc bắt đầu, rồi replay các thay đổi từ queue hoặc CDC sau khi xong.

*ES và JVM*
- ES chạy trên JVM, tốn *heap* (vùng nhớ JVM dành cho object).
- Cần ít nhất 3 node *master-eligible* (có thể được bầu làm node điều phối cluster) để tránh *split
  brain*: mạng bị chia cắt, hai nửa cluster cùng bầu master riêng và ghi lệch nhau.

*License*
- 2021: Elastic chuyển sang SSPL/Elastic License. AWS fork thành **OpenSearch** từ bản 7.10.2, nay
  thuộc OpenSearch Software Foundation của Linux Foundation.
- 2024: Elastic thêm lựa chọn **AGPLv3**.
- OpenSearch vẫn là dự án riêng. API cơ bản giống nhau, nhưng tính năng mới đã khác nhau dần.

*Thay thế nhẹ*
- Meilisearch, Typesense.
- Postgres full-text + `pg_trgm` (module 1.3).

**Đọc**
- Elastic: [Aliases](https://www.elastic.co/docs/manage-data/data-store/aliases), [Reindex examples](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reindex-indices), [Size your shards](https://www.elastic.co/docs/deploy-manage/production-guidance/optimize-performance/size-shards)
- [Elastic: Elasticsearch is open source again](https://www.elastic.co/blog/elasticsearch-is-open-source-again) (2024)

**Nắm chắc khi**
- [ ] Viết được từng bước đổi analyzer của index `products` đang nhận ghi, kể cả rollback (bài tập 3)
- [ ] Ước lượng được số primary shard cho index 600GB và giải thích con số

#### 3.6 Time-series, OLAP, data warehouse

**Vì sao cần học:** "Báo cáo doanh thu làm DB chậm" là sự cố gần như mọi hệ thống lớn dần đều gặp.
Senior phải đề xuất được lộ trình đưa phân tích ra khỏi DB chính, và biết khi nào cần time-series DB
hay data warehouse.

**Học gì**

*Time-series DB*
- *Time-series DB* lưu chuỗi điểm dữ liệu dạng timestamp + giá trị + các *label* (nhãn mô tả, như
  `host=web1`, `status=500`).
- Kiểu truy cập đặc trưng: ghi nối thêm (*append*), đọc theo khoảng thời gian, aggregate theo cửa sổ
  (trung bình mỗi 5 phút).
- Ví dụ: Prometheus, InfluxDB, TimescaleDB (dùng *hypertable*, bảng Postgres tự chia theo thời
  gian), VictoriaMetrics.
- Tính năng thường có:
  - *Retention*: tự xoá dữ liệu cũ hơn N ngày.
  - *Downsampling*: gộp dữ liệu cũ thành độ phân giải thấp hơn (từ mỗi giây thành mỗi giờ).
  - Nén theo cột.
- ⚠️ *High cardinality*: label có vô số giá trị (`user_id`, `request_id`). Mỗi tổ hợp label là một
  *series* riêng, nên tạo ra hàng triệu series và nổ bộ nhớ
  ([18-reliability-observability.md](18-reliability-observability.md)).

*OLTP và OLAP*

| | OLTP | OLAP |
|---|---|---|
| Ví dụ | MySQL, Postgres | ClickHouse, BigQuery, Redshift, Snowflake |
| Kiểu query | Rất nhiều query nhỏ, chạm vài dòng | Ít query, quét rất nhiều dòng |
| Lưu trữ | *Row store*: các cột của một dòng nằm cạnh nhau | *Column store*: giá trị của một cột nằm cạnh nhau |
| Nạp dữ liệu | Từng dòng, liên tục | Theo batch |
| Latency | Mili giây | Giây |

*Vì sao column store nhanh cho phân tích*
- Chỉ đọc cột cần: `SUM(amount)` chỉ đọc cột `amount`, bỏ qua mọi cột khác.
- Nén tốt: các giá trị cùng cột giống nhau nhiều, nên nén rất gọn.
- *Vectorized execution*: xử lý cả khối giá trị một lúc thay vì từng dòng, tận dụng CPU tốt hơn.
- ClickHouse dùng engine MergeTree.
  - ⚠️ Insert từng dòng là anti-pattern. Gom batch, hoặc bật *async insert* để server tự gom.
  - Update và delete nặng.
- BigQuery tính tiền theo lượng dữ liệu quét.
  - ⚠️ `SELECT *` là trả tiền thật cho mọi cột.
  - Chia bảng theo partition và cluster để quét ít hơn.

*Không chạy báo cáo nặng trên OLTP*
- Vì sao:
  - Chiếm I/O của query nghiệp vụ.
  - Đẩy dữ liệu nóng ra khỏi *buffer pool* (vùng RAM InnoDB dùng cache page).
  - Transaction dài chặn *purge*/*vacuum* (việc dọn phiên bản dòng cũ) ([03-database-sql.md](03-database-sql.md)).
  - Chuyển báo cáo sang replica thì replica bị lag.
- Lộ trình thường gặp:
  1. Replica riêng chỉ cho báo cáo.
  2. Bảng tổng hợp, được tính sẵn định kỳ.
  3. Warehouse hoặc column store.

*Warehouse, data lake, lakehouse*
- *Data warehouse*: kho dữ liệu phân tích có cấu trúc, thường theo *star schema*: một bảng *fact*
  (sự kiện, như từng đơn hàng) ở giữa, nối tới các bảng *dimension* (chiều, như khách hàng, sản
  phẩm, ngày).
- *Data lake*: file thô trên object storage, thường dạng Parquet (định dạng file lưu theo cột).
- *Lakehouse*: data lake cộng lớp quản lý bảng (Iceberg, Delta Lake) để có schema và transaction.
- *ETL* (extract, transform, load: biến đổi rồi mới nạp) và *ELT* (nạp thô trước, biến đổi trong
  warehouse, ví dụ bằng dbt).
- Nguồn dữ liệu vào: CDC, Kafka, export.

*Dữ liệu cá nhân*
- ⚠️ Dữ liệu cá nhân chảy sang warehouse cũng phải được bảo vệ và xoá theo yêu cầu, giống ở DB chính
  ([10-security.md](10-security.md)).

**Đọc**
- DDIA ch.3, mục *Transaction Processing or Analytics?* và *Column-Oriented Storage*
- Prometheus: [Metric and label naming](https://prometheus.io/docs/practices/naming/) (mục labels, cảnh báo cardinality)
- ClickHouse: [Asynchronous inserts](https://clickhouse.com/docs/optimize/asynchronous-inserts)
- Kimball: [Star schema](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/star-schema-olap-cube/)

**Nắm chắc khi**
- [ ] Giải thích được bằng số liệu vì sao `SUM(amount)` trên 1 tỉ dòng nhanh hơn nhiều ở column store
- [ ] Đề xuất được lộ trình 3 bước cho "báo cáo doanh thu làm DB chậm" và nói cái giá độ trễ dữ liệu ở mỗi bước

#### 3.7 Vector DB và graph DB

**Vì sao cần học:** Tính năng AI (tìm kiếm ngữ nghĩa, RAG) đưa vector search vào backend thường ngày.
Người phỏng vấn muốn biết bạn chọn pgvector hay hệ riêng, và có hiểu cạm bẫy khi lọc theo tenant
không. Graph DB ít gặp hơn, câu hỏi thường là "khi nào thật sự cần".

**Học gì**

*Embedding*
- *Embedding* là một vector nhiều chiều (vài trăm tới vài nghìn số) do model sinh ra từ văn bản hay
  ảnh. Nội dung gần nghĩa thì vector gần nhau.
- Đo độ gần bằng cosine (góc giữa hai vector), dot product (tích vô hướng) hoặc L2 (khoảng cách
  thẳng).

*ANN: tìm gần đúng*
- Tìm chính xác vector gần nhất là O(n): so với mọi vector.
- Quy mô lớn thì dùng **ANN** (approximate nearest neighbor): đổi một chút *recall* (tỉ lệ tìm được
  đúng các vector gần nhất thật) lấy tốc độ.

| | HNSW | IVF |
|---|---|---|
| Ý tưởng | Đồ thị nhiều tầng: tầng trên thưa để nhảy xa, tầng dưới dày để tinh chỉnh | Chia vector thành cụm, chỉ tìm trong vài cụm gần nhất |
| RAM | Tốn | Ít hơn |
| Tốc độ query, recall | Nhanh, recall cao | Tuỳ số cụm được dò |

*Chọn nơi lưu vector*
- pgvector (kiểu `vector`, index `hnsw` hoặc `ivfflat`):
  - Dữ liệu và vector chung một DB.
  - Lọc bằng SQL, có transaction.
- Hệ riêng (Qdrant, Milvus, Weaviate, Pinecone) khi quy mô rất lớn.
- ES/OpenSearch và Redis 8 cũng có vector search.

*Cạm bẫy*
- ⚠️ Lọc metadata (tenant, quyền) kết hợp ANN: nếu lọc **sau** khi ANN đã trả top K, phần lớn kết quả
  có thể thuộc tenant khác và bị loại, nên còn lại quá ít.
- ⚠️ Đổi model embedding là phải embed lại toàn bộ dữ liệu, vì vector của hai model không so sánh
  được với nhau.

*Hybrid search*
- *Hybrid search* kết hợp BM25 (khớp từ khoá, module 2.6) và vector (khớp nghĩa). Thường tốt hơn từng
  cái riêng ([23-ai-llm-backend.md](23-ai-llm-backend.md)).

*Graph DB*
- *Graph DB* (Neo4j với ngôn ngữ Cypher, Neptune) lưu node và cạnh, duyệt quan hệ nhiều bước nhanh.
- Hợp khi quan hệ nhiều bước, độ sâu không cố định:
  - Gợi ý (bạn của bạn thích gì).
  - Phát hiện gian lận theo vòng giao dịch.
  - Knowledge graph.
  - Phân quyền dạng đồ thị.
- ⚠️ Quan hệ nông thì SQL join hoặc recursive CTE là đủ. Graph DB khó shard, và là thêm một hệ thống
  phải vận hành.

**Đọc**
- [pgvector README](https://github.com/pgvector/pgvector) (mục HNSW, IVFFlat, filtering)
- [HNSW paper](https://arxiv.org/abs/1603.09320) (Malkov, Yashunin): đọc phần giới thiệu và hình minh hoạ
- [Neo4j: Getting started](https://neo4j.com/docs/getting-started/) (phần graph database concepts)

**Nắm chắc khi**
- [ ] Giải thích được vì sao tìm vector theo tenant bằng pgvector có thể trả thiếu kết quả, và 2 cách sửa
- [ ] Nêu được một bài toán thật mà graph DB hơn hẳn SQL, và một bài toán nghe giống nhưng SQL đủ

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Redis có những kiểu dữ liệu nào? Cho use case mỗi loại.** (1.1)
- Ý phải có: String, Hash, List, Set, Sorted set, mỗi kiểu một use case thật và lệnh chính
- Điểm cộng: HyperLogLog, Bitmap, Stream; chọn kiểu theo cách truy cập
- Red flag: lưu mọi thứ thành JSON string

**2. Vì sao không lưu file upload trên đĩa app server?** (1.4)
- Ý phải có: app stateless để scale ngang, instance bị thay là mất file, đĩa đầy, backup khó; dùng object storage + CDN
- Điểm cộng: presigned URL để file không đi qua app

**3. Vì sao `LIKE '%keyword%'` không đủ cho tìm kiếm?** (1.3)
- Ý phải có: full scan, không xếp hạng, không hiểu biến thể từ và không dấu; inverted index giải quyết thế nào
- Điểm cộng: nhu cầu nhỏ thì full-text của DB hoặc `pg_trgm` có thể đủ trước khi thêm Elasticsearch

**4. Khi nào chọn NoSQL? Mất gì so với SQL?** (1.2)
- Ý phải có: truy cập theo key biết trước, scale ghi ngang; mất JOIN, transaction đa bản ghi, ràng buộc, query ad-hoc
- Điểm cộng: "schemaless" là schema chuyển vào code; `jsonb`/JSON thường đủ
- Red flag: "NoSQL nhanh hơn SQL"

**5. Presigned URL hoạt động thế nào, server cần kiểm tra gì?** (1.4, 2.8)
- Ý phải có: server ký URL có hạn, client upload thẳng; server kiểm tra quyền, tự sinh key, kiểm tra object sau upload
- Điểm cộng: presigned POST với `content-length-range`; magic bytes, quét virus; hạn ngắn cho file nhạy cảm

### 🟡 Mid

**6. Redis chạy lệnh trên một thread, sao lại nhanh? I/O threads thay đổi gì?** (2.1)
- Ý phải có: RAM, event loop không lock, cấu trúc dữ liệu tối ưu; I/O threads chỉ làm socket/parse, lệnh vẫn tuần tự
- Điểm cộng: hệ quả vận hành: lệnh O(n) chặn mọi client, cấm `KEYS`, theo dõi slowlog
- Red flag: "vì chạy trên RAM" rồi dừng

**7. Vì sao không dùng `KEYS *` trên production? Big key gây hại thế nào?** (2.1)
- Ý phải có: duyệt toàn keyspace chặn server; `SCAN`; big key làm lệnh chậm, mạng nghẽn, xoá chặn server
- Điểm cộng: `UNLINK`; `--bigkeys`, `MEMORY USAGE`; big key làm migrate slot treo

**8. RDB và AOF khác nhau thế nào? Redis mất dữ liệu trong trường hợp nào?** (2.2)
- Ý phải có: snapshot và log lệnh; `everysec` mất khoảng 1 giây; replication async mất ghi khi failover
- Điểm cộng: fork + COW làm bộ nhớ gần gấp đôi; dữ liệu quan trọng phải có nguồn sự thật ở DB

**9. Redis xoá key hết hạn thế nào? Chọn eviction policy ra sao?** (2.2)
- Ý phải có: lazy + active; các policy `allkeys-*`, `volatile-*`, `noeviction`; LRU/LFU xấp xỉ
- Điểm cộng: `SET` ghi đè xoá TTL; queue/session không được nằm chung instance có eviction; `HEXPIRE` cho TTL theo field
- Red flag: không biết mặc định là `noeviction`

**10. `MULTI`/`EXEC` có rollback không? Khi nào dùng Lua?** (2.3)
- Ý phải có: không rollback, lệnh lỗi lúc chạy thì lệnh khác vẫn chạy; không đọc được kết quả giữa chừng; Lua cho đọc-rồi-ghi có điều kiện
- Điểm cộng: `WATCH` là optimistic lock; Lua chạy lâu chặn server; Cluster cần key cùng slot

**11. Làm distributed lock bằng Redis thế nào? Có an toàn tuyệt đối không?** (2.4)
- Ý phải có: `SET NX PX` với token ngẫu nhiên, nhả bằng Lua so token
- Điểm cộng: lock hết hạn khi việc chưa xong, failover async làm mất lock; fencing token; tranh luận Redlock của Kleppmann
- Red flag: `SETNX` rồi `EXPIRE` riêng, hoặc `DEL` thẳng khi nhả

**12. Pub/Sub và Stream khác nhau thế nào?** (2.3)
- Ý phải có: Pub/Sub không lưu, không ack; Stream lưu, consumer group, ack, nhận lại message của consumer chết
- Điểm cộng: khi nào phải lên Kafka; Pub/Sub cho invalidate L1 cache vẫn cần TTL ([11-cache.md](11-cache.md))

**13. MongoDB: khi nào embed, khi nào reference?** (2.5)
- Ý phải có: embed cho 1-ít đọc cùng cha, update atomic; reference cho 1-nhiều không giới hạn, dữ liệu truy cập riêng
- Điểm cộng: giới hạn 16MB, bucket pattern; ESR cho compound index

**14. Làm tìm kiếm tiếng Việt có dấu và không dấu thế nào?** (2.6)
- Ý phải có: `asciifolding` + multi-field, query cả hai, boost field có dấu
- Điểm cộng: chuẩn hoá NFC trước khi index; tách âm tiết và phrase query; `edge_ngram` cho autocomplete; kiểm tra bằng `_analyze`
- Red flag: bỏ dấu toàn bộ dữ liệu và chỉ lưu bản không dấu

**15. Vì sao ghi vào Elasticsearch xong search ngay lại không thấy?** (2.6)
- Ý phải có: near real-time, cần refresh (mặc định 1 giây); `GET` theo id thì thấy
- Điểm cộng: `refresh=wait_for` cho test; không `refresh` sau mỗi lần ghi trên production

**16. Đồng bộ dữ liệu từ MySQL sang Elasticsearch thế nào?** (2.7)
- Ý phải có: dual write sẽ lệch; outbox hoặc CDC; xử lý thứ tự bằng external version hoặc đọc lại từ DB
- Điểm cộng: job đối soát, reindex toàn bộ qua alias; Scout bỏ qua update hàng loạt
- Red flag: "ghi DB xong thì ghi ES là được"

**17. Laravel dùng phpredis hay Predis? Có gì cần để ý khi dùng chung Redis cho cache và queue?** (2.9)
- Ý phải có: phpredis là extension C, nhanh, mặc định; Predis thuần PHP; tách connection/DB cho cache và queue
- Điểm cộng: `cache:clear` xoá sạch DB đang dùng; eviction làm mất job; prefix không áp vào key trong Lua

### 🔴 Senior

**18. Sorted set cài đặt bằng gì? Vì sao Redis chọn skip list?** (3.1)
- Ý phải có: tập nhỏ dùng listpack; lớn dùng skip list + hashtable, mỗi cấu trúc phục vụ loại lệnh nào
- Điểm cộng: đơn giản hơn cây cân bằng, range tự nhiên, span cho rank; rehash tăng dần

**19. Redis Cluster chia dữ liệu thế nào? Vì sao `MGET` nhiều key có thể lỗi?** (3.2)
- Ý phải có: 16384 slot, CRC16; `CROSSSLOT`; hash tag
- Điểm cộng: `MOVED`/`ASK`; lạm dụng hash tag thành hot node; Cluster không đảm bảo consistency mạnh

**20. Chọn Redis hay Valkey cho dự án mới? License có ảnh hưởng gì?** (3.2)
- Ý phải có: lịch sử 2024 (Redis chuyển RSAL/SSPL, Valkey fork BSD), Redis 8 thêm AGPLv3; phần lớn API tương thích
- Điểm cộng: chọn theo dịch vụ managed, tính năng cần (module đã gộp vào Redis 8), rủi ro license khi phân phối phần mềm; hai bên đã bắt đầu khác nhau về tính năng
- Red flag: nói Redis "đóng nguồn" như sự thật hiện tại, hoặc không biết Valkey

**21. Redis CPU 100%, latency mọi request tăng vọt, lượng request không đổi.** (2.1)
- Ý phải có: `SLOWLOG GET`, nghi `KEYS`, lệnh O(n) trên big key, Lua chạy lâu; `--bigkeys`; xem job mới deploy
- Điểm cộng: sửa bằng `SCAN`, chia key, ACL chặn lệnh; kiểm tra fork RDB và swap

**22. Redis đầy bộ nhớ, app lỗi khi ghi hoặc user bị đăng xuất hàng loạt.** (2.2)
- Ý phải có: `noeviction` thì ghi lỗi; `allkeys-*` thì session/lock bị loại; tìm key không TTL, big key
- Điểm cộng: fork làm bộ nhớ nhân đôi; tách instance cache và dữ liệu; TTL cho mọi key cache

**23. Thiết kế bảng Cassandra/DynamoDB cho "tin nhắn mới nhất của mỗi cuộc trò chuyện". Hot partition xử lý thế nào?** (3.4)
- Ý phải có: liệt kê access pattern trước; partition theo conversation, sort theo thời gian; bảng/GSI cho "danh sách hội thoại của user"
- Điểm cộng: bucket theo thời gian cho hội thoại rất dài; write sharding cho key nóng; on-demand vẫn có giới hạn mỗi partition
- Red flag: thiết kế như bảng SQL rồi mới nghĩ query

**24. Đổi mapping Elasticsearch trên index đang chạy mà không downtime.** (3.5)
- Ý phải có: alias, index mới, reindex, đổi alias atomic
- Điểm cộng: ghi trong lúc reindex (ghi đôi hoặc replay từ queue/CDC); giữ index cũ để rollback; tăng `refresh_interval` lúc bulk

**25. Người dùng gõ "dien thoai samsung" không ra, gõ có dấu thì ra.** (2.6, 3.5)
- Ý phải có: analyzer không có folding; thêm sub-field folding, multi-field query, boost field có dấu
- Điểm cộng: đổi analyzer cần index mới + alias; kiểm tra bằng `_analyze`; NFD trong dữ liệu import

**26. Báo cáo doanh thu chạy chậm, làm DB chậm theo. Làm gì?** (3.6)
- Ý phải có: tách tải: replica riêng, bảng tổng hợp tính trước, rồi column store/warehouse qua CDC
- Điểm cộng: nói cái giá độ trễ dữ liệu và ai thật sự cần số realtime; transaction dài chặn purge
- Red flag: "thêm index, chạy lúc đêm" là đủ

**27. Hai tiến trình cùng cập nhật một file manifest trên S3. Làm sao không ghi đè mất nhau?** (2.8)
- Ý phải có: `If-Match` với ETag đã đọc, thất bại (`412`) thì đọc lại và thử lại; `If-None-Match: *` cho tạo mới
- Điểm cộng: trước 2024 phải dùng DynamoDB hoặc DB làm lock; S3 strong consistency từ 2020 giúp đọc-sau-ghi đúng; storage tương thích S3 có thể không hỗ trợ

**28. Upload video 2GB qua API bị timeout, server hết RAM khi nhiều người upload.** (1.4, 2.8)
- Ý phải có: file đang đi qua app; đổi sang presigned multipart upload thẳng lên S3
- Điểm cộng: lifecycle abort multipart dở dang; xử lý video async qua queue; giới hạn kích thước bằng policy

---

## Bài tập tự làm

1. **Rate limiter bằng Redis.** Viết Lua script cho sliding window counter: giới hạn 100 request/phút mỗi user, trả về số request còn lại. Giải thích vì sao cần Lua thay vì nhiều lệnh riêng, và điều gì xảy ra khi Redis failover. Gọi script từ Laravel (`Redis::eval`) và nói rõ key prefix được xử lý thế nào.
2. **Chọn nơi lưu.** Một app thương mại điện tử có: sản phẩm, giỏ hàng, đơn hàng, lịch sử xem, tìm kiếm sản phẩm, ảnh sản phẩm, metric hệ thống, báo cáo doanh thu theo tháng. Với mỗi loại dữ liệu, chọn nơi lưu, giải thích lý do, và nêu cách dữ liệu chảy giữa các hệ thống.
3. **Index tìm kiếm tiếng Việt.** Viết mapping Elasticsearch cho `products` (tên, mô tả, danh mục, giá, trạng thái) hỗ trợ:
   - Tìm có dấu và không dấu, ưu tiên khớp đúng dấu
   - Lọc theo danh mục và khoảng giá
   - Autocomplete tên

   Kèm kế hoạch reindex khi đổi mapping và cách đồng bộ từ MySQL (outbox hoặc CDC).
4. **Mô hình DynamoDB.** Thiết kế single-table cho hệ thống đặt lịch khám: bệnh nhân, bác sĩ, lịch hẹn. Liệt kê access pattern trước, sau đó chọn PK/SK/GSI cho từng pattern, chỉ ra điểm có thể thành hot partition, và chọn capacity mode kèm lý do.
5. **Upload qua S3 trong Laravel.** Viết luồng upload ảnh sản phẩm bằng `temporaryUploadUrl`: endpoint cấp URL, endpoint xác nhận sau upload (kiểm tra kích thước và magic bytes), job tạo thumbnail. Nêu cách dọn file không bao giờ được xác nhận.

> Nộp bài vào đây để được review.
