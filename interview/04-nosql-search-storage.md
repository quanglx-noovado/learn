# 04. NoSQL, search và storage

> [← Mục lục](README.md) · Phạm vi: Redis, các loại NoSQL (MongoDB, Cassandra, DynamoDB), search engine (Elasticsearch/OpenSearch), time-series, OLAP/data warehouse, object storage (S3), vector DB và graph DB.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Redis**
- [ ] Kiểu dữ liệu và use case: String, Hash, List, Set, Sorted set; 🟡 Bitmap, HyperLogLog, Stream, Geo
- [ ] 🔴 Cấu trúc bên dưới: listpack, hashtable, intset, quicklist, skip list cho sorted set
- [ ] Vì sao nhanh dù thực thi lệnh trên một thread; 🟡 I/O threads (Redis 6+)
- [ ] ⚠️ Lệnh nguy hiểm: `KEYS`, lệnh O(n) trên key lớn, big key, hot key; `SCAN`, `UNLINK`
- [ ] Persistence: RDB và AOF; đánh đổi tốc độ và lượng dữ liệu có thể mất
- [ ] TTL, cách Redis xoá key hết hạn (lazy + active), eviction policy
- [ ] 🟡 Pipelining, `MULTI`/`EXEC`/`WATCH`, Lua script
- [ ] 🟡 Pub/Sub và Stream (consumer group)
- [ ] 🔴 Replication, Sentinel, Cluster (16384 hash slot, hash tag, lệnh multi-key)
- [ ] 🟡 Use case: distributed lock, rate limiter, leaderboard, session store, counter

**NoSQL nói chung**
- [ ] Phân loại: key-value, document, wide-column, graph, time-series, search
- [ ] Khi nào chọn NoSQL, mất gì so với SQL
- [ ] 🟡 CAP/PACELC của từng loại ở mức đại ý

**MongoDB**
- [ ] 🟡 Document model, embedding vs referencing
- [ ] 🟡 Index (compound, quy tắc ESR, multikey, TTL), aggregation pipeline
- [ ] 🟡 Transaction, write concern, read concern, read preference
- [ ] 🔴 Sharding: shard key, mongos, hot shard

**Wide-column và DynamoDB**
- [ ] 🔴 Query-first modeling; partition key, clustering/sort key
- [ ] 🔴 Cassandra: tunable consistency (`ONE`/`QUORUM`/`ALL`), tombstone
- [ ] 🔴 DynamoDB: GSI/LSI, single-table design, hot partition, strongly consistent read

**Search**
- [ ] Vì sao `LIKE '%keyword%'` không đủ
- [ ] 🟡 Inverted index, analyzer/tokenizer/filter; mapping `text` và `keyword`
- [ ] 🟡 Tiếng Việt có dấu/không dấu (ASCII folding), multi-field
- [ ] 🟡 Shard/replica, near real-time refresh, BM25
- [ ] 🟡 Deep pagination (`search_after` + PIT)
- [ ] 🟡 Đồng bộ từ DB: dual write, queue/outbox, CDC; 🔴 reindex không downtime bằng alias

**Analytics và time-series**
- [ ] 🟡 Time-series DB: retention, downsampling, high cardinality
- [ ] 🟡 OLTP vs OLAP; column store (ClickHouse, BigQuery); vì sao không chạy báo cáo trên DB OLTP
- [ ] 🟡 Data warehouse, data lake, ETL vs ELT, star schema

**Object storage**
- [ ] Không lưu file trên đĩa app server
- [ ] Presigned URL (upload/download trực tiếp); multipart upload
- [ ] 🟡 Consistency, lifecycle, storage class, versioning, bảo mật bucket

**Khác**
- [ ] 🟡 Vector DB / pgvector: embedding, ANN (HNSW) đại ý
- [ ] 🟡 Graph DB: khi nào hợp lý

## Chi tiết

### Redis: kiểu dữ liệu và cấu trúc bên dưới

- [ ] Kiểu dữ liệu và use case

  | Kiểu | Use case | Lệnh hay dùng |
  |---|---|---|
  | String | Cache, counter, flag, lock | `GET/SET`, `INCR`, `SET k v NX PX 30000` |
  | Hash | Object (user, session), đếm theo field | `HSET`, `HGET`, `HINCRBY` |
  | List | Queue đơn giản, danh sách mới nhất | `LPUSH`, `BRPOP`, `LTRIM`, `LRANGE` |
  | Set | Tag, tập duy nhất, giao/hợp | `SADD`, `SISMEMBER`, `SINTER` |
  | Sorted set | Leaderboard, sliding window, delay queue, priority | `ZADD`, `ZINCRBY`, `ZRANGE`, `ZRANGEBYSCORE`, `ZREMRANGEBYSCORE` |
  | Bitmap | Điểm danh theo ngày, cờ theo user id | `SETBIT`, `BITCOUNT` |
  | HyperLogLog | Đếm số phần tử duy nhất gần đúng (sai số ~0.81%, tối đa 12KB/key) | `PFADD`, `PFCOUNT` |
  | Stream | Log sự kiện có consumer group | `XADD`, `XREADGROUP`, `XACK` |
  | Geo | Tìm điểm gần (dựa trên sorted set) | `GEOADD`, `GEOSEARCH` |

- [ ] 🔴 Cấu trúc bên dưới (encoding)
  - Redis chọn encoding theo kích thước: tập nhỏ dùng **listpack** (mảng liền nhau, tiết kiệm bộ nhớ, O(n) nhưng n nhỏ); vượt ngưỡng (`hash-max-listpack-entries`...) thì chuyển sang cấu trúc lớn. Redis 7 thay ziplist bằng listpack. Xem bằng `OBJECT ENCODING key`.
  - String: SDS (simple dynamic string), lưu độ dài nên `STRLEN` O(1), an toàn nhị phân. Số nguyên nhỏ lưu dạng `int`.
  - List: quicklist (linked list các listpack). Hash: listpack hoặc hashtable. Set: intset (toàn số nguyên), listpack, hoặc hashtable.
  - Sorted set lớn: **skip list + hashtable**. Hashtable cho `ZSCORE` O(1); skip list giữ thứ tự theo score cho `ZRANGE`, `ZRANK`, `ZRANGEBYSCORE` O(log n + m).
  - Vì sao skip list mà không phải cây cân bằng: cài đặt đơn giản hơn, duyệt range theo thứ tự tự nhiên (đi tiếp ở tầng dưới cùng), độ phức tạp kỳ vọng tương đương; Redis bổ sung span để tính rank.
  - Hashtable của Redis rehash **tăng dần** (hai bảng song song, mỗi thao tác chuyển một ít) để không chặn server khi bảng lớn.

### Redis: mô hình thực thi và lệnh nguy hiểm

- [ ] Vì sao nhanh dù thực thi lệnh trên một thread
  - Dữ liệu trong RAM; cấu trúc dữ liệu tối ưu; không tốn chi phí lock/context switch giữa các lệnh; I/O multiplexing (epoll) phục vụ hàng nghìn connection trên một event loop.
  - Nút cổ chai thường là mạng và bộ nhớ, không phải CPU.
  - 🟡 Redis 6+ có **I/O threads** (`io-threads`) để đọc/ghi socket và parse song song; lệnh vẫn thực thi tuần tự trên main thread, nên tính atomic của từng lệnh giữ nguyên. Thread nền còn làm `UNLINK`, lazyfree, fsync AOF.
  - Hệ quả: một lệnh chậm chặn **mọi** client. Mỗi lệnh là atomic, nhưng chuỗi lệnh thì không.
  - **Đối chiếu:** giống event loop của Node.js; khác Memcached vốn đa luồng.
- [ ] ⚠️ Lệnh nguy hiểm
  - `KEYS *` duyệt toàn bộ keyspace, chặn server trên production. Dùng `SCAN` (cursor, trả từng đợt; có thể trả trùng, client phải chịu được).
  - Lệnh O(n) trên key lớn: `HGETALL`, `SMEMBERS`, `LRANGE 0 -1`, `ZRANGE 0 -1` trên key triệu phần tử; `SORT`; `SUNION`/`ZUNIONSTORE` tập lớn. Dùng `HSCAN`/`SSCAN`/`ZSCAN` hoặc lấy theo trang.
  - `DEL` key rất lớn giải phóng bộ nhớ đồng bộ, chặn server. Dùng `UNLINK` (giải phóng ở thread nền). `FLUSHALL`/`FLUSHDB` có tuỳ chọn `ASYNC`.
  - Chặn lệnh nguy hiểm bằng ACL (Redis 6+) hoặc `rename-command` trong config.
- [ ] ⚠️ Big key và hot key
  - Big key (string nhiều MB, hash/zset triệu phần tử): lệnh chậm, mạng nghẽn, xoá chặn server, migration slot ở Cluster bị treo, phân bố bộ nhớ lệch giữa các node. Tìm bằng `redis-cli --bigkeys`, `--memkeys`, `MEMORY USAGE`. Sửa: chia nhỏ key (`user:{id}:friends:{bucket}`), nén, không lưu blob lớn.
  - Hot key (một key bị đọc cực nhiều, ví dụ sản phẩm flash sale): dồn tải vào một node dù Cluster có nhiều node. Tìm bằng `redis-cli --hotkeys` (cần policy LFU) hoặc thống kê phía client. Sửa: cache cục bộ trong app với TTL ngắn, nhân bản key (`key:1..N`, đọc ngẫu nhiên), đọc từ replica. Xem thêm [11-cache.md](11-cache.md).

### Redis: persistence, TTL, eviction

- [ ] Persistence
  - **RDB:** snapshot định kỳ bằng `fork()`, process con ghi file, cha tiếp tục phục vụ nhờ copy-on-write. Nhỏ, restore nhanh; mất dữ liệu kể từ snapshot cuối.
  - ⚠️ Fork trên instance nhiều GB tốn thời gian (copy page table) gây khựng; ghi nhiều trong lúc snapshot làm COW nhân đôi bộ nhớ, có thể bị OOM. Chừa RAM dư.
  - **AOF:** ghi log từng lệnh ghi. `appendfsync always` (an toàn nhất, chậm), `everysec` (mặc định, mất tối đa khoảng 1 giây), `no` (để OS quyết định). AOF được rewrite định kỳ cho gọn.
  - Thực tế hay bật cả hai (AOF có phần mở đầu dạng RDB để load nhanh; kiểm tra lại theo phiên bản bạn dùng). Redis thuần cache có thể tắt persistence.
  - ⚠️ Redis không phải DB bền như Postgres: replication async + fsync theo giây nghĩa là có thể mất ghi khi failover. Dữ liệu không được phép mất thì nguồn sự thật phải ở DB.
- [ ] TTL và cách xoá key hết hạn
  - Lazy: khi truy cập key thì kiểm tra hết hạn, hết thì xoá. Active: định kỳ lấy mẫu ngẫu nhiên các key có TTL, xoá key hết hạn, nếu tỉ lệ hết hạn cao thì lặp tiếp. Nên key hết hạn không biến mất đúng từng mili giây và vẫn chiếm RAM một lúc.
  - Replica không tự xoá key hết hạn; primary gửi lệnh `DEL` xuống (replica vẫn trả "không tồn tại" khi đọc key đã quá hạn).
  - ⚠️ `SET key value` ghi đè **xoá TTL cũ** (dùng `KEEPTTL` nếu muốn giữ); `INCR`, `HSET` giữ TTL. `SET` rồi `EXPIRE` là hai lệnh, crash ở giữa để lại key vĩnh viễn: dùng `SET key v EX 60`.
  - ⚠️ Nhiều key cùng hết hạn một lúc gây cache avalanche: thêm jitter vào TTL ([11-cache.md](11-cache.md)).
- [ ] Eviction policy (khi chạm `maxmemory`)
  - `noeviction` (mặc định): trả lỗi khi ghi. `allkeys-lru`/`allkeys-lfu`: loại key ít dùng trong mọi key. `volatile-lru`/`volatile-lfu`/`volatile-ttl`/`volatile-random`: chỉ loại key có TTL. `allkeys-random`.
  - LRU/LFU của Redis là **xấp xỉ** (lấy mẫu `maxmemory-samples` key rồi loại key tệ nhất), không phải LRU chính xác.
  - Chọn: dùng làm cache thì `allkeys-lru` hoặc `allkeys-lfu`; Redis vừa cache vừa lưu dữ liệu quan trọng (session, lock) thì `volatile-*` và đặt TTL cho key cache, hoặc tốt hơn là tách instance.
  - ⚠️ Queue/lock trên instance có eviction có thể bị loại âm thầm.

### Redis: pipeline, transaction, script, messaging

- [ ] 🟡 Pipelining: gửi nhiều lệnh không chờ từng phản hồi, giảm round-trip (1000 lệnh × 1ms RTT thành vài ms). **Không atomic**: lệnh của client khác có thể xen giữa.
- [ ] 🟡 `MULTI`/`EXEC`
  - Xếp lệnh vào hàng đợi, `EXEC` chạy liền một mạch không bị xen. ⚠️ **Không có rollback**: một lệnh lỗi lúc chạy (sai kiểu) thì các lệnh khác vẫn được thực hiện.
  - Không đọc được kết quả giữa chừng để quyết định lệnh sau. Cần check-and-set thì dùng `WATCH` (optimistic: key bị sửa trước `EXEC` thì `EXEC` trả null, client retry) hoặc Lua.
- [ ] 🟡 Lua script (`EVAL`, Redis 7 có Functions)
  - Chạy atomic trên server, đọc rồi ghi có điều kiện trong một bước: nhả lock đúng chủ, rate limiter, trừ tồn kho.
  - ⚠️ Script chạy lâu chặn cả server. Trong Cluster, mọi key script chạm phải khai báo trong `KEYS` và nằm cùng slot.

  ```lua
  -- nhả lock chỉ khi đúng chủ (value là token ngẫu nhiên của người giữ)
  if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
  end
  return 0
  ```
- [ ] 🟡 Pub/Sub và Stream

  | | Pub/Sub | Stream |
  |---|---|---|
  | Lưu message | Không; subscriber offline là mất | Có, tới khi trim (`MAXLEN`) |
  | Consumer group | Không, mọi subscriber nhận hết | Có, chia message giữa consumer |
  | Ack / đọc lại | Không | `XACK`, pending list, `XAUTOCLAIM` nhận lại message của consumer chết |
  | Hợp với | Thông báo realtime, invalidate cache cục bộ, fan-out WebSocket | Queue nhẹ, event log nhỏ |

  - ⚠️ Stream không thay được Kafka khi cần retention dài, throughput rất lớn, replay nhiều ngày: bộ nhớ là RAM. So sánh: [12-messaging.md](12-messaging.md).

### Redis: replication, Sentinel, Cluster

- [ ] 🔴 Replication
  - Async: primary ghi rồi trả lời client, sau đó mới gửi sang replica. Replica kết nối lại thì partial resync qua replication backlog, thiếu quá nhiều thì full sync (gửi RDB).
  - `WAIT n timeout` chờ n replica nhận ghi, giảm (không triệt tiêu) khả năng mất dữ liệu khi failover.
  - ⚠️ Đọc replica có thể thấy dữ liệu cũ.
- [ ] 🔴 Sentinel
  - Nhóm tiến trình giám sát primary, đạt quorum đồng ý primary chết thì promote một replica, báo client địa chỉ mới. Client phải hỗ trợ Sentinel (hỏi Sentinel để tìm primary).
  - Dùng khi dữ liệu vừa một máy và cần HA. Chạy ít nhất 3 Sentinel ở các máy khác nhau.
- [ ] 🔴 Redis Cluster
  - Chia keyspace thành **16384 hash slot**: `slot = CRC16(key) mod 16384`. Mỗi primary giữ một dải slot, mỗi primary có replica. Không cần proxy; client giữ bảng slot → node.
  - Client gửi nhầm node thì nhận `MOVED` (slot đã chuyển hẳn, cập nhật bảng) hoặc `ASK` (slot đang migrate, hỏi tạm node khác một lần).
  - ⚠️ Lệnh multi-key (`MGET`, `SUNION`, `MULTI` nhiều key, Lua nhiều key) chỉ chạy khi mọi key cùng slot, không thì lỗi `CROSSSLOT`.
  - **Hash tag:** chỉ phần trong `{}` được hash: `user:{42}:cart` và `user:{42}:profile` cùng slot. ⚠️ Lạm dụng hash tag dồn dữ liệu vào một slot, thành hot/big node.
  - Chỉ có database 0 (không `SELECT 1`). Thêm node thì reshard slot online.
  - ⚠️ Cluster không đảm bảo consistency mạnh: replication async nên có cửa sổ mất ghi khi failover hoặc khi bị chia mạng.
- [ ] Bối cảnh: năm 2024 Redis đổi license; Valkey là bản fork do Linux Foundation bảo trợ, nhiều cloud chuyển sang. Kiến thức trong file áp dụng cho cả hai (kiểm tra lại tình trạng license theo thời điểm bạn đọc).

### Redis: use case kinh điển

- [ ] 🟡 Distributed lock
  - `SET lock:order:42 <token> NX PX 30000`: chỉ set khi chưa có, tự hết hạn nếu người giữ chết. Nhả bằng Lua so token (snippet trên), không `DEL` thẳng vì có thể xoá lock của người khác khi lock của mình đã hết hạn.
  - ⚠️ Lock hết hạn khi việc chưa xong (GC pause, request chậm) thì hai bên cùng chạy. Cần fencing token ở tài nguyên đích, hoặc dùng DB lock khi cần đúng tuyệt đối. Redlock và tranh luận xung quanh: [14-distributed-systems.md](14-distributed-systems.md).
- [ ] 🟡 Rate limiter
  - Fixed window: `INCR rl:{user}:{phút}` + `EXPIRE`. Đơn giản; cho phép gấp đôi ở ranh giới hai cửa sổ.
  - Sliding window log: sorted set, member là request id, score là timestamp; `ZREMRANGEBYSCORE` bỏ cũ, `ZCARD` đếm, `ZADD` thêm. Chính xác, tốn bộ nhớ theo số request.
  - Token bucket/sliding window counter bằng Lua để atomic. Chi tiết thuật toán: [09-api-design.md](09-api-design.md), [16-system-design.md](16-system-design.md).
- [ ] 🟡 Leaderboard
  - `ZINCRBY lb:week 10 user:42`; top 100: `ZRANGE lb:week 0 99 REV WITHSCORES` (Redis 6.2+, bản cũ `ZREVRANGE`); hạng của tôi: `ZREVRANK`.
  - ⚠️ Bằng điểm thì Redis sort theo member (thứ tự từ điển). Muốn "ai đạt trước xếp trên" thì mã hoá vào score (ví dụ `điểm × 10^k + (MAX_TS - ts)`), nhớ giới hạn độ chính xác của double.
  - Leaderboard theo tuần/tháng: key theo kỳ + TTL. Hàng trăm triệu user: chia theo bucket điểm hoặc chỉ giữ top trong Redis.
- [ ] 🟡 Session store: hash `session:{id}` + TTL, gia hạn TTL mỗi request (sliding expiration). Giúp app stateless, scale ngang. ⚠️ Instance có eviction hoặc không persistence thì mất session là đăng xuất hàng loạt.
- [ ] Counter/view count: `INCR` rồi định kỳ flush về DB theo batch; chấp nhận mất một ít nếu Redis chết.

### NoSQL nói chung

- [ ] Phân loại

  | Loại | Ví dụ | Mô hình | Hợp với |
  |---|---|---|---|
  | Key-value | Redis, DynamoDB, etcd | Tra theo key | Cache, session, cấu hình, truy cập theo id |
  | Document | MongoDB, Couchbase | Document JSON/BSON lồng nhau | Dữ liệu dạng cây theo aggregate, schema thay đổi |
  | Wide-column | Cassandra, ScyllaDB, HBase, Bigtable | Partition → hàng sort theo clustering key | Ghi rất dày, time-series, dữ liệu khổng lồ đa vùng |
  | Graph | Neo4j, Amazon Neptune | Node + edge | Quan hệ nhiều tầng |
  | Time-series | InfluxDB, TimescaleDB, Prometheus | Điểm theo thời gian + label | Metric, IoT |
  | Search | Elasticsearch, OpenSearch | Inverted index | Full-text, lọc đa chiều, log |

- [ ] Khi nào chọn NoSQL
  - Kiểu truy cập đơn giản, biết trước, theo key; cần scale ghi ngang vượt một máy; schema thay đổi nhiều theo từng bản ghi; latency thấp ổn định ở quy mô lớn.
  - ⚠️ Mất gì: JOIN, transaction nhiều bản ghi (hoặc có nhưng đắt/hạn chế), ràng buộc toàn vẹn, query ad-hoc. Kiểu truy cập đổi thì phải thiết kế lại dữ liệu.
  - "Schemaless" là sai tên: schema vẫn có, chỉ chuyển từ DB sang code. Không có migration nghĩa là code phải đọc được mọi phiên bản document cũ.
  - Mặc định an toàn: bắt đầu bằng Postgres/MySQL, thêm NoSQL cho đúng bài toán nó giỏi (polyglot persistence), chấp nhận chi phí vận hành thêm một hệ thống.
- [ ] 🟡 CAP ở mức đại ý
  - CAP: khi có **network partition**, phải chọn giữa Consistency (mọi node trả dữ liệu mới nhất hoặc lỗi) và Availability (luôn trả lời, có thể cũ). Không có partition thì câu hỏi là latency và consistency (PACELC).
  - MongoDB: một primary nhận ghi mỗi replica set, nghiêng về C (phía thiểu số không nhận ghi). Cassandra/DynamoDB: nghiêng về A, consistency chỉnh được theo từng request. Redis Cluster: replication async nên không đảm bảo C. HBase: nghiêng về C.
  - ⚠️ Nhãn "CP/AP" phụ thuộc cấu hình (write/read concern, consistency level), không phải bản chất cố định của sản phẩm. Chi tiết: [14-distributed-systems.md](14-distributed-systems.md).

### MongoDB

- [ ] 🟡 Document model
  - Document BSON, tối đa 16MB. Thiết kế quanh **aggregate** đọc/ghi cùng nhau: đơn hàng kèm danh sách item trong một document.
  - Embedding: một lần đọc, cập nhật atomic trong một document. Hợp quan hệ 1-ít, dữ liệu con không đứng riêng, đọc cùng cha.
  - Referencing: lưu id, join bằng `$lookup` hoặc query thứ hai. Hợp quan hệ 1-nhiều/n-n, dữ liệu con được truy cập riêng hoặc lớn không giới hạn.
  - ⚠️ Mảng tăng không giới hạn (comment của bài viết viral) làm document phình tới giới hạn 16MB và update chậm. Tách collection hoặc bucket pattern.
- [ ] 🟡 Index
  - Single, compound, multikey (index trên mảng), text, geospatial, TTL index (tự xoá document sau thời gian), partial, unique, wildcard.
  - Compound index theo quy tắc **ESR**: Equality trước, Sort giữa, Range sau (cùng tinh thần leftmost prefix của SQL, xem [03-database-sql.md](03-database-sql.md)).
  - `explain("executionStats")`: `COLLSCAN` là full scan; so `totalDocsExamined` với `nReturned`.
- [ ] 🟡 Aggregation pipeline: chuỗi stage `$match` → `$group` → `$sort` → `$project`, thêm `$lookup` (join), `$unwind` (bung mảng). Đặt `$match` sớm để dùng index và giảm dữ liệu. ⚠️ Stage có giới hạn bộ nhớ, cần `allowDiskUse` với tập lớn.
- [ ] 🟡 Transaction và độ bền
  - Ghi một document luôn atomic. Transaction nhiều document có từ 4.0 (replica set) và 4.2 (sharded); chạy được nhưng đắt hơn, có giới hạn thời gian. Cần nhiều transaction đa document thường là dấu hiệu mô hình nên là quan hệ.
  - **Write concern:** `w:1` (primary nhận), `w:"majority"` (đa số node ghi nhận, sống sót qua failover; mặc định từ 5.0), `j:true` (đã ghi journal).
  - **Read concern:** `local` (có thể đọc dữ liệu sau này bị rollback), `majority` (chỉ đọc dữ liệu đa số đã ghi nhận), `linearizable`, `snapshot`.
  - **Read preference:** `primary` (mặc định), `secondary`, `nearest`... ⚠️ Đọc secondary gặp dữ liệu cũ như replica SQL.
- [ ] 🔴 Sharding
  - `mongos` định tuyến, config server giữ metadata, dữ liệu chia thành chunk theo shard key; ranged hoặc hashed.
  - ⚠️ Shard key tăng dần (ObjectId, timestamp) với ranged sharding: mọi insert dồn vào một shard. Query không có shard key thì scatter-gather tới mọi shard. Đổi shard key: có resharding từ 5.0 nhưng nặng; chọn đúng từ đầu.

### Wide-column (Cassandra) và DynamoDB

- [ ] 🔴 Query-first modeling
  - Ngược với SQL: liệt kê **mọi query** trước, rồi thiết kế mỗi bảng phục vụ một query. Chấp nhận denormalize, cùng dữ liệu ghi vào nhiều bảng.
  - Không JOIN, không query ad-hoc hiệu quả. Query mới xuất hiện thường nghĩa là bảng mới + backfill.
- [ ] 🔴 Cassandra
  - Primary key = **partition key** (quyết định node, qua consistent hashing trên ring) + **clustering columns** (sort trong partition). `PRIMARY KEY ((user_id), created_at)` cho "tin nhắn mới nhất của user".
  - Query phải chỉ rõ partition key; lọc theo cột khác cần bảng khác (hoặc `ALLOW FILTERING`, gần như luôn sai trên production).
  - Ghi theo LSM (xem [03](03-database-sql.md)): ghi rất nhanh. Xung đột giải bằng last-write-wins theo timestamp.
  - **Tunable consistency:** mỗi request chọn `ONE`, `QUORUM`, `ALL`, `LOCAL_QUORUM`. Với N replica, `R + W > N` (ví dụ `QUORUM` cả đọc lẫn ghi với N=3) thì đọc thấy ghi mới nhất.
  - ⚠️ Tombstone: xoá là ghi đánh dấu; partition nhiều tombstone đọc rất chậm, có thể lỗi query. Dùng bảng như queue (insert rồi xoá liên tục) là anti-pattern kinh điển.
  - ⚠️ Partition quá rộng (mọi event của một thiết bị từ trước tới nay): chia bucket theo thời gian vào partition key (`(device_id, day)`).
  - Lightweight transaction (`IF NOT EXISTS`) dùng Paxos, chậm hơn nhiều; chỉ dùng khi thật cần.
- [ ] 🔴 DynamoDB
  - Primary key: partition key, hoặc partition key + sort key. `Query` theo partition key (có điều kiện trên sort key) là hiệu quả; `Scan` đọc cả bảng, đắt.
  - **GSI**: index với partition/sort key khác, tạo lúc nào cũng được, eventually consistent, có capacity riêng. **LSI**: cùng partition key, sort key khác, phải tạo cùng lúc với bảng.
  - Read mặc định eventually consistent; có tuỳ chọn strongly consistent read trên bảng (không áp dụng cho GSI). Có transaction (`TransactWriteItems`), conditional write (optimistic locking), TTL, Streams (CDC).
  - Single-table design: nhiều loại entity trong một bảng, key dạng `PK=USER#42`, `SK=ORDER#2026-09-01` để một `Query` lấy user và đơn của họ. Mạnh nhưng khó đọc, khó thay đổi.
  - ⚠️ Hot partition: một partition key nhận quá nhiều traffic bị throttle dù tổng capacity còn dư. Chọn partition key có nhiều giá trị, phân tán đều; thêm hậu tố ngẫu nhiên (write sharding) cho key nóng.
  - Item tối đa 400KB. Chi phí tính theo lượng đọc/ghi: thiết kế sai kiểu truy cập là trả tiền thẳng.

### Search: Elasticsearch / OpenSearch

- [ ] Vì sao `LIKE '%keyword%'` không đủ: không dùng được B-tree index (full scan), không xếp hạng theo độ liên quan, không hiểu từ đồng nghĩa, số ít/số nhiều, lỗi chính tả, tiếng Việt có dấu/không dấu, không có facet/highlight.
- [ ] 🟡 Inverted index
  - Map từ **term** → danh sách document chứa nó (posting list, kèm vị trí và tần suất). Tìm "áo khoác" là lấy posting list của từng term rồi giao/hợp, không quét document.
  - Segment bất biến (Lucene), merge nền: cùng tư duy LSM. Update document = đánh dấu xoá bản cũ + thêm bản mới.
- [ ] 🟡 Analyzer
  - Analyzer = character filter (bỏ HTML...) → **tokenizer** (tách thành token) → token filter (lowercase, stopword, stemming, synonym, folding).
  - Cùng analyzer áp dụng lúc index và lúc search (hoặc có `search_analyzer` riêng). ⚠️ Lệch analyzer giữa hai lúc là nguồn "tìm không ra" kinh điển. Dùng `_analyze` API để xem token thực tế.
- [ ] 🟡 Tiếng Việt
  - Tiếng Việt viết cách nhau theo **âm tiết**, từ có thể gồm nhiều âm tiết ("điện thoại"). Tokenizer chuẩn tách theo âm tiết; dùng match phrase, shingle, hoặc plugin tách từ tiếng Việt để khớp cụm tốt hơn (plugin cộng đồng, kiểm tra độ tương thích phiên bản).
  - Người dùng hay gõ không dấu: filter `asciifolding` (hoặc `icu_folding`) biến "điện thoại" thành "dien thoai", "đ" thành "d".
  - Multi-field: một field giữ dấu, một sub-field đã folding. Query cả hai, **boost field có dấu** để "hà" xếp "Hà Nội" trên "hả", "há".
  - Autocomplete: `edge_ngram` lúc index hoặc completion suggester; ⚠️ ngram làm index phình to.
  - ⚠️ Folding làm mất nghĩa ("bán" và "bạn" cùng thành "ban"): đó là lý do vẫn giữ field có dấu. Chuẩn hoá Unicode NFC trước khi index (tiếng Việt có nhiều cách mã hoá dấu, xem [22-practical-data.md](22-practical-data.md)).
- [ ] 🟡 Mapping
  - `text`: qua analyzer, dùng full-text search. `keyword`: giữ nguyên, dùng lọc chính xác, sort, aggregation (mã đơn, status, email). Hay khai cả hai qua multi-field.
  - ⚠️ Dynamic mapping đoán kiểu sai (chuỗi số thành `long`, ngày thành `date` theo document đầu tiên) và gây **mapping explosion** khi field tuỳ ý (key JSON động). Khai mapping tường minh, `dynamic: strict` hoặc `false` cho dữ liệu không kiểm soát.
  - Không đổi được kiểu của field đã tồn tại: phải tạo index mới và reindex.
- [ ] 🟡 Shard, replica, refresh
  - Index chia thành primary shard (số lượng chốt lúc tạo; đổi phải split/shrink hoặc reindex) và replica shard (đổi lúc nào cũng được, vừa HA vừa tăng throughput đọc).
  - ⚠️ Oversharding (hàng nghìn shard nhỏ) tốn heap và làm cluster chậm. Nhắm shard cỡ vài chục GB (kiểm tra khuyến nghị của phiên bản bạn dùng).
  - **Near real-time:** document ghi vào buffer, chỉ tìm thấy sau **refresh** (mặc định 1 giây). Test "ghi xong search ngay" hay fail vì thế. `refresh=wait_for` khi thật cần; bulk import lớn thì tăng `refresh_interval` hoặc tắt tạm. Độ bền nhờ translog.
  - Đọc theo id (`GET`) là realtime; search thì không.
- [ ] 🟡 Relevance: BM25 (mặc định từ Elasticsearch 5) dựa trên tần suất term trong document (có bão hoà), độ hiếm của term trong toàn bộ (IDF), độ dài field. Tinh chỉnh: boost field, `function_score` (cộng điểm theo độ mới, độ phổ biến), synonym. ⚠️ Điểm tính theo từng shard nên dữ liệu ít có thể xếp hạng lệch.
- [ ] 🟡 Deep pagination
  - `from + size` bị giới hạn bởi `index.max_result_window` (mặc định 10000) vì mỗi shard phải trả `from + size` kết quả để coordinator sort.
  - Dùng `search_after` (giá trị sort của kết quả cuối, kèm tie-breaker) + **PIT** (point in time) để có view ổn định. Scroll API cũ hơn, không còn được khuyến nghị cho deep pagination. Cùng ý tưởng keyset pagination của SQL.
- [ ] 🟡 Đồng bộ dữ liệu từ DB
  - Search engine là **bản sao để đọc**, không phải nguồn sự thật. Luôn phải rebuild được từ DB.

  | Cách | Ưu | Nhược |
  |---|---|---|
  | Dual write (app ghi DB rồi ghi ES) | Đơn giản | Một bên fail là lệch; hai request đan xen ghi sai thứ tự |
  | Outbox/queue (ghi DB + outbox cùng transaction, worker đẩy sang ES) | Không mất sự kiện, retry được | Trễ vài giây, thêm worker |
  | CDC (Debezium đọc binlog/WAL → Kafka → ES) | Bắt mọi thay đổi, kể cả sửa tay trong DB | Hạ tầng nặng, event ở mức bảng chứ không mức nghiệp vụ |

  - Xử lý thứ tự: dùng external version (`version_type=external` với `updated_at`/version từ DB) để bản cũ đến sau không đè bản mới. Hoặc chỉ gửi id, worker đọc bản mới nhất từ DB rồi index.
  - Có job đối soát định kỳ và cách reindex toàn bộ. Outbox, CDC: [12-messaging.md](12-messaging.md).
- [ ] 🔴 Reindex không downtime bằng alias
  - App luôn đọc/ghi qua **alias** (`products` → `products_v1`). Tạo `products_v2` với mapping mới, reindex từ DB hoặc `_reindex` API, rồi đổi alias atomic trong một lệnh `_aliases`.
  - ⚠️ Ghi trong lúc reindex: ghi vào cả hai index, hoặc ghi nhận mốc thời gian rồi replay thay đổi từ queue/CDC sau khi reindex xong. Giữ `v1` một thời gian để rollback.
- [ ] Vận hành: ES tốn heap (JVM), chạy ít nhất 3 node master-eligible để tránh split brain. OpenSearch là fork từ Elasticsearch 7.10 sau khi Elastic đổi license năm 2021; API cơ bản giống nhau. Thay thế nhẹ hơn: Meilisearch, Typesense; với nhu cầu nhỏ thì Postgres full-text + `pg_trgm` có thể đủ.

### Time-series, OLAP, data warehouse

- [ ] 🟡 Time-series DB
  - Dữ liệu: timestamp + giá trị + label/tag; ghi append liên tục, đọc theo khoảng thời gian, aggregate theo cửa sổ.
  - Ví dụ: Prometheus (metric, pull), InfluxDB, TimescaleDB (extension Postgres, hypertable tự partition theo thời gian), VictoriaMetrics.
  - Tính năng: retention (tự xoá dữ liệu cũ), downsampling (giữ trung bình theo giờ cho dữ liệu cũ), nén theo cột.
  - ⚠️ High cardinality: label có vô số giá trị (`user_id`, `request_id`) tạo ra hàng triệu series, làm nổ bộ nhớ. Không đưa id vào label metric ([18-reliability-observability.md](18-reliability-observability.md)).
- [ ] 🟡 OLTP vs OLAP và column store

  | | OLTP (MySQL, Postgres) | OLAP (ClickHouse, BigQuery, Redshift, Snowflake) |
  |---|---|---|
  | Query | Nhiều, nhỏ, theo dòng/khoá | Ít, quét hàng triệu–tỉ dòng, aggregate |
  | Lưu trữ | Theo dòng (row store) | Theo cột (column store) |
  | Ghi | Insert/update từng dòng | Nạp theo batch; update/delete từng dòng đắt |
  | Latency mục tiêu | Mili giây | Giây (chấp nhận được) |

  - Column store nhanh cho phân tích vì chỉ đọc cột cần dùng, cột cùng kiểu nén rất tốt, thực thi vector hoá.
  - ClickHouse: engine MergeTree, rất nhanh cho aggregate; ⚠️ insert từng dòng nhỏ là anti-pattern (gom batch hoặc dùng async insert), update/delete là thao tác nặng.
  - BigQuery: serverless, tính tiền theo lượng dữ liệu quét. ⚠️ `SELECT *` trên bảng lớn là trả tiền thật; partition và cluster bảng để giảm lượng quét.
- [ ] 🟡 Vì sao không chạy báo cáo nặng trên DB OLTP
  - Query quét lớn chiếm I/O/CPU, đẩy dữ liệu nóng ra khỏi buffer pool, làm chậm request người dùng.
  - Transaction dài giữ snapshot: chặn purge/vacuum, gây bloat (xem [03](03-database-sql.md)). Chạy trên replica cũng làm replica lag hoặc bị huỷ query (Postgres hot standby conflict).
  - Schema OLTP normalize tối ưu cho ghi, không cho phân tích.
  - Lộ trình: replica riêng cho báo cáo → bảng tổng hợp tính trước → đẩy sang warehouse/column store.
- [ ] 🟡 Data warehouse, data lake, ETL/ELT
  - Warehouse: kho dữ liệu đã làm sạch cho phân tích, thường theo **star schema** (bảng fact chứa sự kiện/số đo, bảng dimension chứa thuộc tính: thời gian, sản phẩm, khách hàng).
  - Data lake: file thô (Parquet, JSON) trên object storage, schema lúc đọc. Lakehouse: table format (Iceberg, Delta Lake) trên lake để có transaction và schema.
  - ETL: extract → transform (ngoài warehouse) → load. ELT: nạp thô vào warehouse rồi transform bằng SQL bên trong (dbt). ELT phổ biến hơn khi warehouse mạnh và rẻ.
  - Nguồn dữ liệu: CDC từ DB, event từ Kafka, export định kỳ. ⚠️ Dữ liệu cá nhân chảy sang warehouse cũng phải được bảo vệ và xoá theo yêu cầu ([10-security.md](10-security.md)).

### Object storage (S3 và tương thích)

- [ ] Không lưu file trên đĩa app server
  - App cần stateless để scale ngang: file ở máy A thì request vào máy B không thấy. Container/instance bị thay thế là mất file. Đĩa đầy làm sập app. Backup khó.
  - Lưu file vào object storage (S3, GCS, Azure Blob, Cloudflare R2, MinIO tự host); DB chỉ lưu key/metadata (kích thước, content type, người upload). Phục vụ qua CDN.
- [ ] Presigned URL
  - Server ký một URL có hạn (vài phút) cho phép client `PUT`/`GET` trực tiếp lên S3. File không đi qua app server: đỡ băng thông, đỡ timeout, đỡ bộ nhớ.
  - Upload flow: client xin URL → server kiểm tra quyền, sinh key (không dùng tên file của user làm key) → client upload → client báo xong (hoặc S3 event notification) → server kiểm tra object rồi ghi DB.
  - ⚠️ Giới hạn loại và kích thước file: presigned POST với policy (`content-length-range`, content type); vẫn kiểm tra lại sau khi upload (magic bytes, quét virus) vì client có thể nói dối.
  - ⚠️ URL download có hạn nhưng ai có URL cũng tải được trong thời gian đó: hạn ngắn cho file nhạy cảm.
- [ ] Multipart upload
  - File lớn chia thành part upload song song, lỗi part nào upload lại part đó, rồi `CompleteMultipartUpload`. Part tối thiểu 5MB (trừ part cuối), tối đa 10000 part.
  - ⚠️ Multipart dở dang (không complete, không abort) vẫn tính tiền lưu trữ: đặt lifecycle rule tự abort sau vài ngày.
- [ ] 🟡 Consistency: từ cuối năm 2020, S3 có strong read-after-write consistency cho mọi thao tác PUT/DELETE và LIST. Storage tương thích S3 khác có thể không giống: kiểm tra tài liệu của nhà cung cấp.
- [ ] 🟡 Lifecycle, storage class, versioning
  - Lifecycle: chuyển object cũ sang class rẻ hơn (Infrequent Access, Glacier) rồi xoá sau N ngày. ⚠️ Class lạnh có phí truy xuất và thời gian lấy lại; có thời gian lưu tối thiểu.
  - Versioning: chống ghi đè/xoá nhầm; kết hợp Object Lock cho backup chống ransomware. ⚠️ Versioning giữ mọi bản cũ, cần lifecycle cho noncurrent version.
  - Hiệu năng: theo tài liệu AWS, mỗi prefix chịu khoảng 3500 PUT và 5500 GET mỗi giây; tải lớn thì rải key qua nhiều prefix.
- [ ] 🟡 Bảo mật bucket: bật Block Public Access; bucket policy/IAM theo nguyên tắc quyền tối thiểu; mã hoá at rest; không để credential trong client (dùng presigned URL). ⚠️ Bucket public nhầm là một trong những nguồn lộ dữ liệu phổ biến nhất ([10-security.md](10-security.md)).

### Vector DB và graph DB

- [ ] 🟡 Vector DB / pgvector
  - Embedding: model biến văn bản/ảnh thành vector số thực nhiều chiều, nội dung gần nghĩa thì vector gần nhau. Đo bằng cosine, dot product, hoặc khoảng cách L2.
  - Tìm k vector gần nhất chính xác là so với mọi vector (O(n)); quy mô lớn dùng **ANN** (approximate nearest neighbor): đổi một chút recall lấy tốc độ.
  - **HNSW** (đại ý): đồ thị nhiều tầng, tầng trên thưa để nhảy xa, tầng dưới dày để tinh chỉnh; tìm bằng cách đi tham lam về phía gần query. Build tốn bộ nhớ, query nhanh, recall cao. IVF: chia cụm, chỉ tìm trong vài cụm gần nhất.
  - pgvector: extension Postgres, kiểu `vector`, index `hnsw` và `ivfflat`. Ưu: dữ liệu và vector chung DB, lọc bằng SQL, transaction. Hệ riêng (Qdrant, Milvus, Weaviate, Pinecone) khi quy mô rất lớn hoặc cần tính năng chuyên biệt. Elasticsearch/OpenSearch cũng có kNN.
  - ⚠️ Lọc metadata (theo tenant, quyền) kết hợp ANN: lọc sau ANN có thể trả về quá ít kết quả; cần hỗ trợ filtered search đúng cách. Đổi model embedding là phải embed lại toàn bộ.
  - Hybrid search (BM25 + vector) thường tốt hơn từng cái riêng. RAG và tích hợp LLM: [23-ai-llm-backend.md](23-ai-llm-backend.md).
- [ ] 🟡 Graph DB
  - Neo4j (Cypher), Amazon Neptune. Node và edge là công dân hạng nhất; duyệt quan hệ nhiều tầng không cần join bảng lớn lặp lại.
  - Hợp lý: quan hệ nhiều bước và độ sâu không cố định (bạn của bạn của bạn, gợi ý), phát hiện gian lận theo vòng giao dịch, knowledge graph, phân quyền dạng đồ thị.
  - Không cần: quan hệ nông 1–2 tầng (SQL join hoặc recursive CTE đủ tốt). ⚠️ Chi phí: thêm một hệ thống, đội ít kinh nghiệm, graph rất khó shard.

## Senior trả lời khác gì

- **"Redis một thread sao lại nhanh?"**
  - Mid: "Vì chạy trên RAM."
  - Senior: RAM + event loop không lock + cấu trúc dữ liệu tối ưu; từ Redis 6 I/O đa luồng còn thực thi lệnh vẫn một thread; hệ quả vận hành: một lệnh O(n) trên big key chặn mọi client, nên cấm `KEYS`, theo dõi slowlog và big key.
- **"Dùng Redis làm distributed lock?"**
  - Mid: "`SETNX` rồi `DEL`."
  - Senior: `SET NX PX` với token, nhả bằng Lua so token; nói lock có thể hết hạn khi việc chưa xong, failover async có thể làm mất lock; tài nguyên quan trọng cần fencing token hoặc lock trong DB; nêu tranh luận Redlock.
- **"Khi nào chọn MongoDB thay vì MySQL?"**
  - Mid: "Khi schema linh hoạt, cần scale."
  - Senior: khi dữ liệu có dạng aggregate đọc/ghi cả cụm và kiểu truy cập ổn định; nói rõ mất JOIN, ràng buộc, transaction rẻ; Postgres `jsonb` thường đã đủ cho "schema linh hoạt"; tính cả chi phí vận hành thêm một hệ thống.
- **"Đồng bộ DB sang Elasticsearch thế nào?"**
  - Mid: "Ghi DB xong thì ghi ES."
  - Senior: dual write sẽ lệch; dùng outbox hoặc CDC, xử lý thứ tự bằng external version, có đối soát và reindex toàn bộ qua alias; ES là bản sao đọc, rebuild được từ DB.
- **"Báo cáo doanh thu chạy chậm, làm DB chậm theo."**
  - Mid: "Thêm index, chạy lúc đêm."
  - Senior: tách tải: replica riêng cho báo cáo, bảng tổng hợp tính trước theo ngày, rồi đẩy sang column store/warehouse qua CDC khi quy mô lớn; nhắc chi phí độ trễ dữ liệu và ai cần số liệu realtime thật.

## Tình huống

1. **Redis CPU 100%, latency mọi request tăng vọt, dù lượng request không đổi.**
   - Gợi ý: `SLOWLOG GET` tìm lệnh chậm; nghi `KEYS`, `HGETALL`/`SMEMBERS` trên big key, Lua chạy lâu; `--bigkeys` để tìm key lớn; xem có job nào mới deploy dùng lệnh O(n). Sửa bằng `SCAN`, chia nhỏ key, chặn lệnh bằng ACL.
2. **Redis đầy bộ nhớ, app bắt đầu lỗi khi ghi (hoặc user bị đăng xuất hàng loạt).**
   - Gợi ý: `noeviction` thì ghi lỗi; `allkeys-*` thì session/lock bị loại. Kiểm tra key không có TTL (`INFO keyspace`, `SCAN` + `TTL`), big key, fork RDB làm bộ nhớ nhân đôi. Tách instance cache và instance dữ liệu quan trọng, đặt TTL cho mọi key cache.
3. **Thiết kế leaderboard top 100 người chơi theo thời gian thực, 10 triệu người chơi.**
   - Gợi ý: sorted set `ZINCRBY`, `ZRANGE ... REV` cho top, `ZREVRANK` cho hạng của mình; xử lý bằng điểm bằng cách mã hoá thời gian vào score; key theo mùa/tuần + TTL; lưu điểm gốc ở DB, Redis rebuild được; hot key khi mọi người cùng xem top 100: cache kết quả top vài giây.
4. **Người dùng gõ "dien thoai samsung" không ra kết quả, gõ có dấu thì ra.**
   - Gợi ý: analyzer không có folding. Thêm sub-field `asciifolding`, query multi-field và boost field có dấu; đổi mapping cần index mới, reindex và đổi alias; kiểm tra bằng `_analyze`.
5. **Sau khi sửa giá sản phẩm, trang tìm kiếm vẫn hiện giá cũ với một số sản phẩm, mãi không tự đúng.**
   - Gợi ý: dual write bị lỗi hoặc ghi sai thứ tự (bản cũ đến sau đè bản mới). Chuyển sang outbox/CDC, dùng external version, thêm job đối soát so `updated_at` giữa DB và ES.
6. **Upload video 2GB qua API bị timeout, server hết RAM khi nhiều người upload cùng lúc.**
   - Gợi ý: file đang đi qua app server. Đổi sang presigned URL + multipart upload trực tiếp lên S3; server chỉ cấp URL và xác nhận khi xong; lifecycle abort multipart dở dang; xử lý video bất đồng bộ qua queue.

## ❓ Câu hỏi hay gặp

🟢
- Redis có những kiểu dữ liệu nào, cho use case mỗi loại?
- Vì sao không lưu file upload trên đĩa của app server?
- Vì sao `LIKE '%keyword%'` không đủ cho chức năng tìm kiếm?
- Khi nào chọn NoSQL, và mất đi những gì so với SQL?

🟡
- Redis chạy một thread, sao lại nhanh? I/O threads của Redis 6 thay đổi gì?
- Vì sao không được dùng `KEYS *` trên production? Big key gây hại thế nào?
- RDB và AOF khác nhau thế nào? Redis mất dữ liệu trong những trường hợp nào?
- Redis xoá key hết hạn thế nào? Các eviction policy khác nhau ra sao?
- `MULTI`/`EXEC` có rollback không? Khi nào dùng Lua thay thế?
- Pub/Sub và Stream khác nhau thế nào?
- Inverted index là gì? Analyzer gồm những phần nào?
- Làm tìm kiếm tiếng Việt có dấu/không dấu thế nào?
- Vì sao ghi vào Elasticsearch xong search ngay lại không thấy?
- MongoDB: khi nào embed, khi nào reference?
- Presigned URL hoạt động thế nào, cần kiểm tra gì?

🔴
- Sorted set được cài đặt bằng gì? Vì sao Redis chọn skip list?
- Redis Cluster chia dữ liệu thế nào? Vì sao `MGET` nhiều key có thể lỗi, sửa thế nào?
- Thiết kế bảng Cassandra/DynamoDB cho "tin nhắn mới nhất của mỗi cuộc trò chuyện". Hot partition xử lý thế nào?
- Đổi mapping Elasticsearch trên index đang chạy mà không downtime thế nào?
- Vì sao không chạy báo cáo nặng trên DB OLTP? Column store nhanh hơn vì sao?

## Bài tập tự làm

1. **Rate limiter bằng Redis.** Viết Lua script cho sliding window counter: giới hạn 100 request/phút mỗi user, trả về số request còn lại. Giải thích vì sao cần Lua thay vì nhiều lệnh riêng, và điều gì xảy ra khi Redis failover.
2. **Chọn nơi lưu.** Một app thương mại điện tử có: sản phẩm, giỏ hàng, đơn hàng, lịch sử xem, tìm kiếm sản phẩm, ảnh sản phẩm, metric hệ thống, báo cáo doanh thu theo tháng. Với mỗi loại dữ liệu, chọn nơi lưu, giải thích lý do, và nêu cách dữ liệu chảy giữa các hệ thống.
3. **Index tìm kiếm tiếng Việt.** Viết mapping Elasticsearch cho `products` (tên, mô tả, danh mục, giá, trạng thái) hỗ trợ: tìm có dấu và không dấu, ưu tiên khớp đúng dấu, lọc theo danh mục và khoảng giá, autocomplete tên. Kèm kế hoạch reindex khi đổi mapping.
4. **Mô hình DynamoDB.** Thiết kế single-table cho hệ thống đặt lịch khám: bệnh nhân, bác sĩ, lịch hẹn. Liệt kê access pattern trước, sau đó chọn PK/SK/GSI cho từng pattern, và chỉ ra điểm có thể thành hot partition.

> Nộp bài vào đây để được review.
