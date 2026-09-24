# 03. Database quan hệ và SQL

> [← Mục lục](README.md) · Phạm vi: storage engine, index, optimizer, SQL viết tay, transaction, lock, thiết kế schema, ORM, vận hành và scale database quan hệ (MySQL/InnoDB và PostgreSQL).
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Storage engine**
- [ ] Dữ liệu lưu theo page (InnoDB 16KB, Postgres 8KB); B+tree và vì sao không dùng binary tree/hash
- [ ] Clustered index + secondary index (InnoDB) và heap + index (Postgres)
- [ ] 🔴 LSM tree (memtable, SSTable, compaction) và so sánh với B-tree
- [ ] 🟡 Buffer pool / shared_buffers; dirty page, checkpoint
- [ ] 🟡 WAL / redo log, undo log, binlog (MySQL); two-phase commit giữa redo và binlog
- [ ] 🔴 Doublewrite buffer (InnoDB) và full_page_writes (Postgres): chống torn page

**Index**
- [ ] Composite index, leftmost prefix, range làm dừng các cột sau
- [ ] Covering index; 🟡 `INCLUDE` (Postgres); 🟡 index condition pushdown (ICP)
- [ ] 🟡 Index phục vụ `ORDER BY` / `GROUP BY` (tránh filesort, bảng tạm)
- [ ] Các trường hợp index không được dùng (hàm, `LIKE '%x'`, ép kiểu, `OR`, selectivity thấp)
- [ ] 🟡 Index trên expression / cột JSON; partial index (Postgres)
- [ ] 🟡 Loại index: B-tree, hash, full-text, GIN, GiST, BRIN
- [ ] 🟡 Cardinality, selectivity; khi nào optimizer bỏ index
- [ ] Cái giá của index; dọn index trùng/không dùng
- [ ] ⚠️ Primary key: auto-increment vs UUIDv4 vs UUIDv7/ULID

**Optimizer và query**
- [ ] Đọc `EXPLAIN` MySQL (`type`, `key`, `rows`, `Extra`)
- [ ] 🟡 Đọc `EXPLAIN ANALYZE` Postgres (cost, actual, loops, estimate lệch)
- [ ] 🟡 Statistics bị cũ, `ANALYZE`, histogram; plan đổi đột ngột
- [ ] 🟡 Join algorithms: nested loop, hash join, merge join
- [ ] Quy trình xử lý query chậm; slow query log
- [ ] Pagination: `OFFSET` lớn chậm, keyset/cursor pagination
- [ ] `COUNT(*)` trên bảng lớn; `SELECT *`; 🟡 batch insert/update/delete

**SQL viết tay**
- [ ] `INNER`/`LEFT`/`RIGHT`/`FULL`/`CROSS JOIN`, self join, anti-join; ⚠️ fan-out khi join 1-n rồi `SUM`
- [ ] `GROUP BY` + `HAVING` và `WHERE`; thứ tự thực thi logic của câu SQL
- [ ] Subquery, correlated subquery, `EXISTS` và `IN`; `UNION` và `UNION ALL`
- [ ] ⚠️ NULL semantics (three-valued logic, `NOT IN` với NULL, `COUNT(col)`)
- [ ] 🟡 Window function: `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `LAG`/`LEAD`, aggregate `OVER`, frame
- [ ] 🟡 CTE, recursive CTE
- [ ] 🟡 UPSERT: `ON DUPLICATE KEY UPDATE` và `ON CONFLICT`
- [ ] 🟡 Bài SQL kinh điển: top-N mỗi nhóm, running total, bản ghi trùng, gaps and islands

**Transaction**
- [ ] ACID nói bằng ngôn ngữ thực tế
- [ ] Anomalies: dirty read, non-repeatable read, phantom, lost update, 🟡 write skew, read skew
- [ ] Isolation level; mặc định MySQL (RR) khác Postgres (RC)
- [ ] 🔴 Postgres Repeatable Read là snapshot isolation; Serializable là SSI; retry `40001`
- [ ] 🟡 MVCC ở InnoDB (undo log, purge) và Postgres (tuple version, VACUUM, bloat)
- [ ] 🔴 Transaction ID wraparound (Postgres)
- [ ] ⚠️ Transaction dài; gọi API bên ngoài trong transaction

**Lock**
- [ ] Shared/exclusive, row/table lock
- [ ] 🟡 Record, gap, next-key, insert intention lock (InnoDB); 🔴 intention lock (IS/IX)
- [ ] ⚠️ `UPDATE` trên cột không có index khoá rất nhiều dòng
- [ ] ⚠️ Metadata lock khi `ALTER TABLE` làm treo cả bảng
- [ ] Optimistic locking (version) và pessimistic locking (`FOR UPDATE`)
- [ ] Deadlock: điều kiện, phát hiện, 🟡 đọc deadlock log, cách phòng
- [ ] 🟡 Lock wait timeout; ⚠️ statement bị huỷ nhưng transaction vẫn mở
- [ ] 🟡 `FOR UPDATE SKIP LOCKED` / `NOWAIT`: làm job queue bằng DB
- [ ] 🟡 Advisory lock (`pg_advisory_lock`, `GET_LOCK`)

**Thiết kế schema**
- [ ] Normalization 1NF/2NF/3NF; denormalization có kiểm soát; quan hệ 1-1, 1-n, n-n
- [ ] Kiểu dữ liệu: `DECIMAL` cho tiền, thời gian/timezone, `utf8mb4` và collation, `BIGINT` cho id
- [ ] Soft delete và unique index
- [ ] Khoá ngoại: có nên dùng
- [ ] 🟡 Dữ liệu dạng cây: adjacency list, nested set, closure table, materialized path
- [ ] 🟡 Cột JSON; ⚠️ EAV là anti-pattern
- [ ] 🟡 Polymorphic association; audit/history table; enum

**ORM**
- [ ] N+1 query; lazy và eager loading
- [ ] 🟡 ORM sinh SQL tệ; khi nào viết raw SQL

**Vận hành**
- [ ] Connection pool: cỡ pool, `max_connections`; 🟡 PgBouncer/ProxySQL
- [ ] 🟡 Online schema change: `ALGORITHM=INSTANT`, gh-ost, pt-osc, `CREATE INDEX CONCURRENTLY`
- [ ] Migration an toàn: expand/contract, backfill theo batch
- [ ] Backup logical/physical, PITR, 🟡 RPO/RTO, restore thử

**Scale**
- [ ] 🟡 Read replica; replication async/semi-sync/sync
- [ ] 🟡 Replication lag và read-your-writes
- [ ] 🔴 Failover, split brain
- [ ] 🔴 Partitioning range/list/hash
- [ ] 🔴 Sharding: shard key, cross-shard query, resharding, Vitess/Citus
- [ ] 🟡 Archiving dữ liệu cũ

**Khác**
- [ ] 🔴 MySQL vs Postgres: khác biệt thực tế
- [ ] 🟡 OLTP vs OLAP (chi tiết ở [04-nosql-search-storage.md](04-nosql-search-storage.md))

## Chi tiết

### Storage engine

- [ ] Page
  - DB đọc/ghi đĩa theo đơn vị page, không theo dòng. InnoDB mặc định 16KB, Postgres 8KB.
  - Đọc một dòng là nạp cả page. Dòng hay được đọc cùng nhau nằm cùng page (đơn của cùng user gần nhau theo clustered key) thì ít I/O.
  - Cột quá to (TEXT/BLOB/JSON lớn) bị đẩy ra page riêng (InnoDB off-page, Postgres TOAST), nên `SELECT *` kéo cột lớn tốn thêm I/O.
- [ ] B+tree
  - Mỗi node là một page, fan-out hàng trăm key, nên cây chỉ cao 3–4 tầng cho hàng trăm triệu dòng; các tầng trên thường nằm sẵn trong RAM.
  - Dữ liệu (hoặc con trỏ) chỉ ở lá; các lá nối nhau thành linked list, nên range scan và `ORDER BY` theo key là đọc tuần tự.
  - Binary tree cao `log2(n)`, mỗi tầng một lần đọc đĩa. Hash tra `=` nhanh nhưng không làm được range, sort, prefix.
  - Insert vào page đầy gây **page split**; xoá nhiều làm page thưa (fragmentation).
- [ ] Clustered index (InnoDB) và heap (Postgres)
  - InnoDB: bảng *chính là* B+tree theo primary key, dòng nằm trong lá. Không khai PK thì dùng unique NOT NULL đầu tiên, không có nữa thì tạo row id ẩn.
  - Secondary index InnoDB lưu `(cột index, PK)`. Tra qua secondary = tìm PK rồi tra tiếp clustered index. PK to thì mọi secondary index to theo.
  - Postgres: dữ liệu nằm trong heap không thứ tự; mọi index (kể cả PK) trỏ tới vị trí vật lý (ctid). `CLUSTER` sắp xếp lại một lần, không duy trì.
  - Hệ quả: InnoDB range scan theo PK rất rẻ. Postgres update tạo tuple mới ở chỗ mới, phải sửa mọi index, trừ khi được **HOT update** (không đổi cột có index và page còn chỗ).
- [ ] 🔴 LSM tree (Log-Structured Merge tree)
  - Ghi vào WAL + memtable trong RAM; memtable đầy thì flush thành SSTable bất biến, đã sort. Nền chạy **compaction** gộp file, bỏ bản cũ và tombstone.
  - Đọc: xem memtable rồi nhiều tầng SSTable; Bloom filter bỏ qua file chắc chắn không chứa key.
  - Dùng ở RocksDB, LevelDB, Cassandra, ScyllaDB, HBase; MyRocks là engine MySQL trên RocksDB.

  | | B+tree | LSM tree |
  |---|---|---|
  | Ghi | Sửa tại chỗ, random I/O | Append tuần tự, ghi rất nhanh |
  | Đọc điểm | Ổn định, vài page | Có thể phải xem nhiều tầng |
  | Range scan | Tốt | Phải merge nhiều file |
  | Amplification | Read amp thấp | Write amp do compaction, space amp do bản cũ |
  | Hợp với | OLTP đọc/ghi cân bằng | Ghi dày: log, metric, event, time-series |

  - ⚠️ Compaction chiếm I/O/CPU nền, làm p99 nhấp nhô; xoá nhiều tạo tombstone làm đọc chậm cho tới khi được dọn.
- [ ] 🟡 Buffer pool
  - InnoDB cache page trong buffer pool (`innodb_buffer_pool_size`, thường phần lớn RAM của máy DB riêng). Postgres có `shared_buffers` và dựa nhiều vào page cache của OS.
  - Page đã sửa trong RAM (dirty page) được flush dần; checkpoint đánh dấu mốc đã flush để giới hạn lượng log phải replay khi crash.
  - Working set (dữ liệu nóng + index) vừa RAM thì nhanh; vượt RAM thì hiệu năng rơi mạnh vì chuyển sang đọc đĩa. Theo dõi hit ratio.
- [ ] 🟡 WAL / redo log, undo log, binlog
  - **WAL:** log mô tả thay đổi phải được ghi và fsync *trước* page dữ liệu. Commit chỉ cần fsync log (tuần tự). Crash thì replay log. Đây là chữ D trong ACID.
  - **Redo log (InnoDB):** WAL ở tầng engine, dạng vật lý (page nào đổi gì).
  - **Undo log (InnoDB):** lưu bản cũ để rollback và để transaction khác đọc snapshot cũ (MVCC). Postgres không có undo log; bản cũ nằm ngay trong heap.
  - **Binlog (MySQL):** log logic ở tầng server, dùng cho replication và PITR. Format `ROW` (mặc định từ 5.7), `STATEMENT`, `MIXED`. ⚠️ `STATEMENT` không an toàn với câu không tất định (`NOW()`, `UUID()`, `LIMIT` không `ORDER BY`).
  - Redo và binlog là hai log riêng, nên MySQL dùng internal two-phase commit để chúng không lệch nhau khi crash.
  - Độ bền: `innodb_flush_log_at_trx_commit=1` + `sync_binlog=1` an toàn nhất; hạ xuống để tăng throughput là chấp nhận mất vài giao dịch cuối khi máy sập. Postgres tương tự với `synchronous_commit`.
- [ ] 🔴 Doublewrite buffer
  - Page InnoDB 16KB nhưng đĩa/OS chỉ ghi atomic ở đơn vị nhỏ hơn. Mất điện giữa chừng tạo **torn page** (nửa mới nửa cũ). Redo log không cứu được vì redo cần page gốc nguyên vẹn.
  - InnoDB ghi page vào vùng doublewrite trước rồi mới ghi vào vị trí thật; crash thì lấy bản nguyên vẹn từ đó.
  - Postgres giải cùng bài toán bằng `full_page_writes`: lần đầu sửa page sau checkpoint thì ghi cả page vào WAL.

### Index

- [ ] Composite index và leftmost prefix
  - Index `(a, b, c)` sắp theo `a`, cùng `a` thì theo `b`, rồi `c`. Giống danh bạ sắp theo họ rồi tên: biết tên mà không biết họ thì không tra được.
  - Dùng được cho `a`, `a+b`, `a+b+c`. Không seek được cho `b` hay `c` riêng.
  - Range (`>`, `<`, `BETWEEN`, `LIKE 'x%'`) ở một cột làm các cột sau không thu hẹp phạm vi quét được nữa (vẫn lọc tại index được nhờ ICP).
  - Thứ tự cột: cột `=` trước, cột range/sort sau. Giữa các cột `=` thì ưu tiên cột xuất hiện trong nhiều query.
  - 🔴 MySQL 8.0 và Postgres 18 có *skip scan*: cột đầu ít giá trị thì vẫn dùng được index khi thiếu điều kiện cột đầu (kiểm tra lại theo phiên bản bạn dùng). Đừng thiết kế dựa vào nó.

  ```sql
  -- index (user_id, status, created_at)
  WHERE user_id = 1 AND status = 2 AND created_at > '2026-01-01'  -- seek cả 3 cột
  WHERE user_id = 1 AND created_at > '2026-01-01'                 -- seek theo user_id, created_at chỉ để lọc
  WHERE user_id = 1 AND status > 0 AND created_at > '...'         -- range ở status: created_at không seek
  ```
- [ ] Covering index
  - Query lấy đủ cột từ index, không tra lại bảng. MySQL: `Extra: Using index`. Postgres: `Index Only Scan`.
  - InnoDB: secondary index đã chứa PK, nên `SELECT id FROM t WHERE a = ?` với index `(a)` đã covering.
  - Postgres 11+: `CREATE INDEX ... (a) INCLUDE (b, c)` thêm cột chỉ để trả về.
  - ⚠️ Index-only scan của Postgres cần visibility map; bảng vừa update nhiều mà chưa VACUUM thì vẫn ghé heap (`Heap Fetches` cao).
- [ ] 🟡 Index condition pushdown (MySQL 5.6+)
  - Điều kiện trên cột có trong index nhưng không seek được thì engine lọc ngay trên index entry trước khi tra bảng. `Extra: Using index condition`.
  - Index `(zip, last_name)`, `WHERE zip = '100' AND last_name LIKE '%an%'`: không seek theo `last_name` nhưng lọc tại index, giảm số lần lookup.
- [ ] 🟡 Index cho `ORDER BY` / `GROUP BY`
  - Index `(user_id, created_at)` phục vụ `WHERE user_id = ? ORDER BY created_at DESC LIMIT 20` không cần sort: đọc ngược 20 entry là xong.
  - ⚠️ `WHERE user_id IN (1,2,3) ORDER BY created_at` thường phải sort lại (thứ tự chỉ đúng trong từng user). `ORDER BY a ASC, b DESC` cần index khai báo hướng tương ứng (MySQL 8 mới có descending index thật).
  - `GROUP BY` theo tiền tố index có thể đọc theo thứ tự thay vì tạo bảng tạm (`Using temporary` là dấu hiệu không làm được).
- [ ] Các trường hợp index không được dùng
  - Bọc hàm quanh cột: `WHERE DATE(created_at) = '2026-01-01'`. Sửa thành range `created_at >= '2026-01-01' AND created_at < '2026-01-02'`, hoặc tạo expression index.
  - `LIKE '%abc'` (wildcard ở đầu): cần full-text, trigram (`pg_trgm` + GIN) hoặc search engine.
  - ⚠️ Ép kiểu ngầm: cột `VARCHAR` so với số (`WHERE phone = 912345678`) làm MySQL convert từng dòng. Join hai cột khác charset/collation cũng vậy.
  - `OR` giữa các cột không cùng index (MySQL có thể `index_merge`, không phải lúc nào cũng tốt); cách khác là tách `UNION ALL`.
  - Điều kiện phủ định (`!=`, `NOT IN`) thường khớp phần lớn bảng. Selectivity thấp (`gender`, `is_active`): optimizer chọn full scan.
- [ ] 🟡 Index trên expression / JSON
  - MySQL 8.0.13+: functional index `CREATE INDEX idx ON users ((LOWER(email)))`; cách cũ là generated column rồi index cột đó. JSON: index generated column từ `data->>'$.sku'`, hoặc multi-valued index cho mảng JSON (8.0.17+).
  - Postgres: expression index `((lower(email)))`; GIN trên `jsonb` cho `@>`, `?`; B-tree trên `((data->>'sku'))` khi chỉ tra một khoá.
  - ⚠️ Query phải viết đúng biểu thức đã index thì mới dùng được.
- [ ] 🟡 Partial index (Postgres)
  - `CREATE INDEX ... ON jobs (run_at) WHERE status = 'pending'`: nhỏ, chỉ chứa dòng cần quan tâm.
  - `CREATE UNIQUE INDEX ON users (email) WHERE deleted_at IS NULL` giải bài soft delete + unique. MySQL không có partial index.
- [ ] 🟡 Các loại index

  | Loại | Dùng cho | Ghi chú |
  |---|---|---|
  | B-tree | `=`, range, sort, prefix | Mặc định, đa số trường hợp |
  | Hash | Chỉ `=` | Postgres có (an toàn từ bản 10); InnoDB không cho tạo, chỉ có adaptive hash index nội bộ |
  | Full-text | Tìm từ trong văn bản | MySQL `FULLTEXT`, Postgres `tsvector` + GIN. Tiếng Việt yếu, xem [04](04-nosql-search-storage.md) |
  | GIN | Giá trị chứa nhiều phần tử: jsonb, mảng, full-text, trigram | Đọc nhanh, ghi chậm hơn |
  | GiST | Hình học, range type, PostGIS, exclusion constraint | Chống đặt phòng trùng khung giờ |
  | BRIN | Bảng rất lớn, cột tương quan với thứ tự vật lý (thời gian ở bảng log append-only) | Rất nhỏ, lưu min/max theo nhóm block |

- [ ] 🟡 Cardinality và selectivity
  - Cardinality: số giá trị phân biệt. Selectivity: tỉ lệ dòng khớp điều kiện (càng nhỏ càng tốt cho index).
  - Secondary index + lookup là random I/O. Khớp một phần đáng kể của bảng thì full scan tuần tự rẻ hơn, nên optimizer bỏ index. Không có ngưỡng cố định; phụ thuộc cost model.
  - ⚠️ Cột selectivity thấp vẫn đáng index nếu dữ liệu lệch: `status = 'pending'` chỉ 0.1% số dòng. Optimizer cần statistics/histogram để biết điều này.
- [ ] 🟡 Khi nào optimizer bỏ index hoặc chọn sai
  - Ước lượng khớp nhiều dòng; statistics cũ; hàm/ép kiểu/collation lệch; `ORDER BY ... LIMIT` nhỏ khiến optimizer chọn quét theo index của sort thay vì index lọc.
  - ⚠️ Postgres prepared statement có thể chuyển sang *generic plan* sau vài lần chạy, không tối ưu cho giá trị lệch (`plan_cache_mode`).
  - Can thiệp: MySQL `FORCE INDEX`, optimizer hint, invisible index (tắt thử trước khi xoá). Postgres không có hint sẵn (extension `pg_hint_plan`); thường sửa bằng statistics, viết lại query, index phù hợp hơn.
- [ ] Cái giá của index
  - Mỗi insert/update/delete phải sửa mọi index liên quan; tốn đĩa và buffer pool; optimizer có thêm lựa chọn để chọn sai.
  - Xoá index trùng (`(a)` khi đã có `(a, b)`) và index không ai dùng: Postgres `pg_stat_user_indexes.idx_scan`, MySQL `sys.schema_unused_indexes`.
- [ ] ⚠️ Chọn primary key

  | | Auto-increment | UUIDv4 | UUIDv7 / ULID |
  |---|---|---|---|
  | Thứ tự | Tăng dần | Ngẫu nhiên | Tăng theo thời gian |
  | Insert vào B+tree | Luôn ở cuối, page đầy đặn | Rải khắp cây: page split, phân mảnh, cache miss | Gần cuối, như auto-increment |
  | Kích thước | 4–8 byte | 16 byte (36 nếu lưu chuỗi) | 16 byte |
  | Sinh ở client / nhiều node | Không (cần DB) | Được | Được |
  | Lộ thông tin | Lộ số lượng, đoán được id kế | Không | Lộ thời điểm tạo |

  - InnoDB chịu thiệt nhất với UUIDv4 vì bảng là clustered index và PK bị nhân vào mọi secondary index. Lưu UUID ở MySQL bằng `BINARY(16)`, không phải `CHAR(36)`.
  - UUIDv7 được chuẩn hoá trong RFC 9562 (2024). Postgres có kiểu `uuid` 16 byte; hàm sinh UUIDv7 có sẵn ở bản mới (kiểm tra lại theo phiên bản bạn dùng).
  - Cách phổ biến: PK nội bộ là `BIGINT`, thêm cột public id (UUID/ULID) để lộ ra API.

### Optimizer và query

- [ ] Đọc `EXPLAIN` MySQL
  - `type` từ tốt tới tệ: `system`/`const` (tra PK/unique) > `eq_ref` (join theo unique) > `ref` (index không unique) > `range` > `index` > `ALL`.
  - ⚠️ `type: index` nghĩa là **quét toàn bộ index**, không phải "dùng index tốt".
  - `key`: index được chọn; `possible_keys`: ứng viên; `key_len`: số byte của index được dùng (suy ra dùng mấy cột composite); `rows`: ước lượng; `filtered`: % còn lại sau lọc.
  - `Extra`: `Using index` (covering), `Using where`, `Using index condition` (ICP), `Using filesort`, `Using temporary`, `Using join buffer (hash join)`.

  ```text
  EXPLAIN SELECT id, total FROM orders WHERE user_id = 42 AND status = 'paid'
          ORDER BY created_at DESC LIMIT 20;
  -- (rút gọn, minh hoạ)  index: idx_user_status_created (user_id, status, created_at)
  type: ref   key: idx_user_status_created   rows: 57   Extra: Using where; Backward index scan
  ```
  - Không có `Using filesort` vì index đã cho đúng thứ tự sau khi cố định `user_id` và `status`.
- [ ] 🟡 `EXPLAIN ANALYZE`
  - Chạy thật query, in thời gian và số dòng thực tế. MySQL 8.0.18+ in dạng cây; ở Postgres nên dùng `EXPLAIN (ANALYZE, BUFFERS)`.
  - ⚠️ Nó **chạy thật**: với `UPDATE`/`DELETE` thì bọc trong `BEGIN; ... ROLLBACK;`.

  ```text
  -- Postgres (rút gọn, số liệu minh hoạ)
  Limit  (cost=0.56..45.10 rows=20 width=24) (actual time=0.041..0.180 rows=20 loops=1)
    ->  Index Scan Backward using idx_orders_user_created on orders
          (cost=0.56..2210.40 rows=990 width=24) (actual time=0.040..0.172 rows=20 loops=1)
          Index Cond: (user_id = 42)
          Filter: (status = 'paid')
          Rows Removed by Filter: 3
          Buffers: shared hit=24
  Planning Time: 0.210 ms
  Execution Time: 0.215 ms
  ```
  - Đọc từ node sâu nhất ra ngoài. `cost` là đơn vị tương đối của planner (không phải ms), dạng `khởi động..tổng`. So `rows` ước lượng với `actual rows`.
  - ⚠️ `actual time` và `rows` là **mỗi loop**; nhân với `loops` để ra tổng. Nested loop `loops=100000` là chỗ hay giấu thời gian.
  - Ước lượng lệch thực tế 10–100 lần là dấu hiệu statistics sai hoặc cột tương quan mà planner không biết; thường là gốc của plan tệ.
  - `Rows Removed by Filter` lớn: index thiếu cột. `Seq Scan` trên bảng lớn trong query OLTP: thiếu index hoặc index bị bỏ. `Buffers: read` lớn: đọc đĩa.
- [ ] 🟡 Statistics bị cũ
  - Optimizer ước lượng từ statistics (số dòng, phân phối giá trị). Sau khi nạp/xoá hàng loạt, statistics cũ khiến plan sai.
  - MySQL: `ANALYZE TABLE`, histogram (`ANALYZE TABLE t UPDATE HISTOGRAM ON col`, 8.0). Postgres: `ANALYZE` (autovacuum tự làm), `CREATE STATISTICS` cho cột tương quan, tăng `default_statistics_target` cho cột lệch.
  - ⚠️ Plan đổi đột ngột khi dữ liệu lớn lên (query 5ms thành 5s dù code không đổi) là sự cố hay gặp.
- [ ] 🟡 Join algorithms

  | Thuật toán | Cơ chế | Hợp khi |
  |---|---|---|
  | Nested loop | Mỗi dòng bảng ngoài, tra bảng trong (lý tưởng qua index) | Bảng ngoài nhỏ, bảng trong có index trên cột join |
  | Hash join | Build hash table từ phía nhỏ, probe bằng phía lớn | Join `=` giữa hai tập lớn, không có index phù hợp |
  | Merge join | Hai phía đã sort theo khoá join, đi song song | Hai phía đã có thứ tự (index) hoặc tập rất lớn |

  - MySQL: nested loop từ xưa, hash join từ 8.0.18, không có merge join. Postgres có cả ba.
  - ⚠️ Nested loop không có index ở bảng trong là O(n·m). Hash join tốn bộ nhớ; tràn `work_mem` (Postgres) thì ghi ra đĩa.
- [ ] Quy trình xử lý query chậm
  - Tìm query (slow query log, `pg_stat_statements`, APM) → xếp theo **tần suất × thời gian** (query 50ms chạy 10 nghìn lần/phút nặng hơn query 5s mỗi giờ) → `EXPLAIN ANALYZE` → sửa (index, viết lại, bớt cột, chia nhỏ) → đo lại → theo dõi.
  - Tách nguyên nhân: query tệ, lock wait, hay DB quá tải chung (CPU, I/O, connection).
  - Slow log: MySQL `slow_query_log`, `long_query_time`, tổng hợp bằng `pt-query-digest`. Postgres `log_min_duration_statement`, `pg_stat_statements`, `auto_explain`.
- [ ] Pagination
  - `LIMIT 20 OFFSET 100000` vẫn đọc 100020 dòng rồi bỏ đi; trang càng sâu càng chậm.
  - Keyset/cursor: `WHERE (created_at, id) < (:last_created, :last_id) ORDER BY created_at DESC, id DESC LIMIT 20`. Nhanh đều mọi trang, ổn định khi có dòng mới chèn; không nhảy thẳng tới trang N. Cần cột tie-breaker unique.
  - ⚠️ So sánh tuple dùng index tốt ở Postgres; MySQL có thể không, khi đó viết `a < x OR (a = x AND b < y)`.
  - Deferred join: `SELECT ... FROM t JOIN (SELECT id FROM t ORDER BY ... LIMIT 20 OFFSET N) x USING (id)` để phần quét sâu chỉ chạy trên index.
- [ ] `COUNT(*)` trên bảng lớn
  - InnoDB và Postgres không lưu sẵn số dòng vì MVCC: mỗi transaction thấy số dòng khác nhau.
  - Thay thế: bảng/counter riêng cập nhật cùng transaction hoặc bất đồng bộ; số ước lượng (`pg_class.reltuples`, `information_schema.TABLES.TABLE_ROWS`); UI hiện "hơn 10.000".
- [ ] `SELECT *`: tốn băng thông và bộ nhớ, kéo cột lớn, không dùng được covering index, dễ vỡ khi thêm cột.
- [ ] 🟡 Batch
  - Insert nhiều dòng một câu, hoặc gom trong một transaction: giảm round-trip và số lần fsync.
  - Update/delete hàng triệu dòng: chia batch theo PK (`WHERE id BETWEEN ? AND ?`), nghỉ giữa batch; tránh một transaction khổng lồ làm lag replica và phình undo/WAL.

### SQL viết tay

- [ ] Thứ tự thực thi logic: `FROM/JOIN` → `WHERE` → `GROUP BY` → `HAVING` → window → `SELECT` → `DISTINCT` → `ORDER BY` → `LIMIT`. Vì vậy `WHERE` không dùng được alias của `SELECT` và không lọc được theo kết quả window function.
- [ ] Join
  - `INNER`: dòng khớp hai bên. `LEFT`: giữ mọi dòng bên trái, bên phải NULL nếu không khớp. `FULL`: giữ cả hai (MySQL không có, giả lập bằng `LEFT ... UNION ... RIGHT`). `CROSS`: tích Descartes. Self join: nhân viên và quản lý.
  - Anti-join "A không có B": `LEFT JOIN b ... WHERE b.id IS NULL` hoặc `NOT EXISTS`.
  - ⚠️ Điều kiện trên bảng bên phải đặt ở `WHERE` biến `LEFT JOIN` thành `INNER JOIN`; đặt vào `ON` nếu muốn giữ dòng bên trái.
  - ⚠️ Join 1-n rồi `SUM` bị nhân dòng (fan-out): tổng tiền đơn bị cộng lặp theo số item. Gom nhóm ở subquery trước rồi mới join.
- [ ] `GROUP BY` / `HAVING`
  - `WHERE` lọc dòng trước khi gom; `HAVING` lọc nhóm sau khi gom (dùng được aggregate).
  - ⚠️ MySQL tắt `ONLY_FULL_GROUP_BY` thì cho chọn cột không nằm trong `GROUP BY` và trả giá trị tuỳ ý. Từ 5.7 mặc định đã bật; Postgres luôn báo lỗi.
- [ ] Subquery, `EXISTS`, `IN`, `UNION`
  - Correlated subquery tham chiếu dòng bên ngoài; về logic chạy lại cho mỗi dòng (optimizer thường viết lại thành join/semi-join).
  - `EXISTS` dừng khi thấy một dòng; optimizer hiện đại thường xử lý `IN` và `EXISTS` như nhau. Khác biệt thật nằm ở NULL với `NOT IN`.
  - `UNION` khử trùng (sort/hash), `UNION ALL` không nên nhanh hơn. Dùng `ALL` khi biết không trùng.
- [ ] ⚠️ NULL semantics
  - Logic ba giá trị: so sánh với NULL cho `UNKNOWN`, `WHERE` chỉ giữ `TRUE`. `NULL = NULL` không phải true; dùng `IS NULL`, `IS DISTINCT FROM` (Postgres), `<=>` (MySQL).
  - `x NOT IN (1, 2, NULL)` không bao giờ true, nên `NOT IN (subquery)` mà subquery có NULL trả về rỗng. Dùng `NOT EXISTS`.
  - `COUNT(*)` đếm dòng; `COUNT(col)` bỏ NULL; `SUM`/`AVG` bỏ NULL (`AVG` không chia cho tổng số dòng). `SUM` của tập rỗng là NULL: dùng `COALESCE`.
  - Unique index cho phép nhiều NULL (cả hai DB; Postgres 15+ có `NULLS NOT DISTINCT`).
  - Sort: MySQL coi NULL nhỏ nhất (đứng đầu khi `ASC`); Postgres coi NULL lớn nhất (đứng cuối khi `ASC`), có `NULLS FIRST/LAST`.
- [ ] 🟡 Window function
  - Tính trên "cửa sổ" các dòng liên quan mà **không gộp dòng** như `GROUP BY`. MySQL có từ 8.0.
  - `ROW_NUMBER` (1,2,3,4), `RANK` (1,2,2,4), `DENSE_RANK` (1,2,2,3); `LAG`/`LEAD` lấy dòng trước/sau; `SUM() OVER (PARTITION BY ... ORDER BY ...)` cộng dồn.
  - ⚠️ Có `ORDER BY` trong `OVER` thì frame mặc định là `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`: các dòng trùng giá trị sort được cộng cùng lúc. Muốn cộng từng dòng thì ghi rõ `ROWS BETWEEN ...`.

  ```sql
  -- cú pháp: đánh số đơn của mỗi user theo giá trị giảm dần, lọc ở tầng ngoài
  SELECT * FROM (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total DESC) AS rn
    FROM orders o
  ) t WHERE rn <= 3;
  ```
- [ ] 🟡 CTE và recursive CTE
  - `WITH x AS (...)` đặt tên cho subquery, dễ đọc. Postgres 12+ mặc định inline CTE (trước đó CTE là "optimization fence"); `MATERIALIZED`/`NOT MATERIALIZED` để ép.
  - Recursive CTE duyệt cây/đồ thị: phần anchor `UNION ALL` phần đệ quy. ⚠️ Dữ liệu có vòng thì lặp vô hạn; giới hạn độ sâu hoặc lưu đường đi.

  ```sql
  WITH RECURSIVE sub AS (
    SELECT id, parent_id, name, 1 AS depth FROM categories WHERE id = 10
    UNION ALL
    SELECT c.id, c.parent_id, c.name, s.depth + 1
    FROM categories c JOIN sub s ON c.parent_id = s.id
    WHERE s.depth < 20
  )
  SELECT * FROM sub;
  ```
- [ ] 🟡 UPSERT
  - MySQL: `INSERT ... ON DUPLICATE KEY UPDATE qty = qty + VALUES(qty)` (8.0.20+ khuyến nghị alias `AS new` thay cho `VALUES()`).
  - Postgres: `INSERT ... ON CONFLICT (sku) DO UPDATE SET qty = t.qty + EXCLUDED.qty`, hoặc `DO NOTHING`. Postgres 15+ có `MERGE`.
  - ⚠️ MySQL: bảng nhiều unique key thì không rõ key nào kích hoạt; upsert vẫn tiêu auto-increment (lỗ hổng id). Upsert atomic, còn "SELECT rồi INSERT" có race.

### Transaction và isolation

- [ ] ACID nói bằng ngôn ngữ thực tế
  - Atomicity: chuyển tiền thì trừ và cộng cùng thành công hoặc cùng huỷ.
  - Consistency: dữ liệu luôn thoả ràng buộc (khoá ngoại, `CHECK`, unique). Phần lớn là trách nhiệm ứng dụng; DB chỉ giữ ràng buộc được khai báo.
  - Isolation: transaction song song không thấy trạng thái dở dang của nhau; mức độ tuỳ isolation level.
  - Durability: đã commit thì mất điện cũng không mất (WAL/redo log fsync). ⚠️ Chỉ đúng khi cấu hình flush an toàn và đĩa không nói dối về fsync.
- [ ] Anomalies

  | Hiện tượng | Mô tả ngắn |
  |---|---|
  | Dirty read | Đọc dữ liệu transaction khác chưa commit |
  | Non-repeatable read | Đọc cùng dòng hai lần, lần sau khác vì có người commit ở giữa |
  | Phantom read | Chạy lại cùng điều kiện, xuất hiện/mất dòng |
  | Read skew | Đọc hai dòng liên quan ở hai thời điểm, thấy trạng thái không nhất quán (tổng hai tài khoản bị lệch) |
  | Lost update | Hai transaction cùng đọc-sửa-ghi, bản ghi sau đè mất bản trước |
  | Write skew | Hai transaction đọc cùng tập dữ liệu, mỗi bên sửa dòng *khác nhau*, cùng nhau vi phạm ràng buộc (hai bác sĩ cùng xin nghỉ vì thấy "vẫn còn người khác trực") |

- [ ] Isolation level ở MySQL (InnoDB) và Postgres

  | | MySQL RC | MySQL RR (mặc định) | PG RC (mặc định) | PG RR | PG Serializable |
  |---|---|---|---|---|---|
  | Dirty read | Không | Không | Không | Không | Không |
  | Non-repeatable / read skew | Có | Không | Có | Không | Không |
  | Phantom | Có | Phần lớn chặn (xem dưới) | Có | Không | Không |
  | Lost update (đọc ở app rồi ghi) | Có | **Có** | Có | Báo lỗi, phải retry | Báo lỗi |
  | Write skew | Có | Có | Có | Có | Chặn |

  - Postgres không có Read Uncommitted thật; khai báo thì chạy như Read Committed.
  - MySQL RR: đọc thường (consistent read) dùng snapshot từ lần đọc đầu; đọc có khoá (`FOR UPDATE`, `UPDATE`, `DELETE`) đọc **bản mới nhất** và dùng next-key lock. ⚠️ Trộn hai kiểu đọc có thể thấy "phantom": `UPDATE` chạm vào dòng người khác vừa insert, sau đó `SELECT` thường thấy dòng đó.
  - 🔴 Postgres RR là **snapshot isolation**: một snapshot cho cả transaction; nếu sửa dòng mà transaction khác đã sửa và commit sau khi snapshot được chụp thì báo `could not serialize access due to concurrent update` (SQLSTATE `40001`).
  - 🔴 Postgres Serializable là **SSI** (Serializable Snapshot Isolation): chạy như snapshot nhưng theo dõi phụ thuộc đọc-ghi, thấy cấu trúc nguy hiểm thì huỷ một transaction. Không khoá chặn đọc; đổi lại ứng dụng phải retry. MySQL Serializable thì biến `SELECT` thường thành `SELECT ... FOR SHARE` (khi không autocommit), tức dùng lock.
  - ⚠️ Chạy RR/Serializable ở Postgres mà code không có vòng retry khi gặp `40001` là bug.
  - Chống lost update ở mọi level: update atomic (`SET stock = stock - 1 WHERE stock > 0`), `SELECT ... FOR UPDATE`, optimistic version, hoặc isolation cao + retry.
  - Chống write skew: khoá các dòng làm điều kiện (`FOR UPDATE` trên tập đã đọc), đưa ràng buộc vào DB (unique, exclusion constraint), hoặc Serializable.
- [ ] 🟡 MVCC
  - Mỗi dòng có nhiều phiên bản; transaction đọc phiên bản khớp snapshot của nó. Đọc không chặn ghi, ghi không chặn đọc (ghi vẫn chặn ghi trên cùng dòng).
  - **InnoDB:** sửa dòng tại chỗ trong clustered index, bản cũ nằm trong undo log thành chuỗi phiên bản. Purge thread dọn undo khi không transaction nào cần. ⚠️ Transaction mở lâu (kể cả chỉ đọc) giữ cả chuỗi undo: *history list length* tăng, đọc chậm dần, undo phình.
  - **Postgres:** update = ghi tuple mới + đánh dấu tuple cũ chết (`xmin`/`xmax`). Tuple chết nằm lại trong heap và index tới khi **VACUUM** dọn; autovacuum chạy nền.
  - ⚠️ **Bloat**: bảng update nhiều, autovacuum không kịp hoặc bị transaction dài/replication slot bỏ quên chặn, bảng và index phình. `VACUUM` thường không trả dung lượng cho OS; `VACUUM FULL` trả lại nhưng khoá cả bảng (dùng `pg_repack` để làm online).
  - 🔴 **Transaction ID wraparound:** xid của Postgres 32 bit; tuple cũ phải được vacuum "freeze". Để lâu không freeze, Postgres ép dừng ghi để bảo vệ dữ liệu. Theo dõi `age(datfrozenxid)`.
- [ ] ⚠️ Transaction dài
  - Giữ lock lâu, tăng deadlock, chặn purge/vacuum, làm lag replica khi commit một cục lớn.
  - Không gọi API bên ngoài, gửi email, upload file trong transaction: API chậm 30 giây là giữ lock 30 giây; rollback DB không thu hồi được email đã gửi. Cần "ghi DB và phát event" nhất quán thì dùng outbox ([12-messaging.md](12-messaging.md)).
  - ⚠️ Framework mở transaction ngầm, hoặc connection về pool khi transaction còn mở (`idle in transaction` ở Postgres). Đặt `idle_in_transaction_session_timeout`.

### Lock

- [ ] Shared (S) và exclusive (X)
  - S tương thích S; X không tương thích với gì. `FOR SHARE` lấy S, `FOR UPDATE`/`UPDATE`/`DELETE` lấy X trên dòng.
  - Row lock (InnoDB, Postgres) và table lock (`LOCK TABLES`, DDL). Postgres có nhiều mức table lock; `ACCESS EXCLUSIVE` (hầu hết `ALTER TABLE`) chặn cả `SELECT`.
  - Postgres ghi row lock ngay trên tuple nên không có lock escalation; InnoDB giữ lock trong bộ nhớ, gắn với index record.
- [ ] 🟡 Record, gap, next-key lock (InnoDB)
  - InnoDB khoá **index record**. Record lock: khoá một entry. Gap lock: khoá khoảng trống giữa hai entry, chặn insert vào đó. Next-key lock = record + gap phía trước. Đây là cách RR chặn phantom khi đọc có khoá.
  - Insert intention lock: loại gap lock đặc biệt khi insert; nhiều insert vào cùng gap ở vị trí khác nhau không chặn nhau.
  - ⚠️ `UPDATE ... WHERE` trên cột không có index phải quét và khoá mọi dòng đã quét (ở RR gần như khoá cả bảng). Luôn có index cho điều kiện của `UPDATE`/`DELETE`/`FOR UPDATE`.
  - ⚠️ Nguồn deadlock kinh điển: hai transaction `SELECT ... FOR UPDATE` một id chưa tồn tại (cùng lấy gap lock, tương thích nhau), rồi cùng insert vào gap đó.
  - Ở Read Committed, InnoDB gần như tắt gap lock (trừ kiểm tra FK và duplicate key), nên nhiều hệ thống chuyển sang RC để giảm deadlock, chấp nhận phantom.
- [ ] 🔴 Intention lock
  - Lock cấp bảng báo "trong bảng có transaction đang/sắp giữ row lock S (IS) hoặc X (IX)". Ai muốn khoá cả bảng chỉ cần xem intention lock thay vì duyệt mọi row lock. IS/IX tương thích nhau nên không cản row lock thường.
- [ ] ⚠️ Metadata lock (MDL) khi `ALTER TABLE`
  - Mọi query trên bảng giữ MDL shared tới **hết transaction**. `ALTER TABLE` cần MDL exclusive, ít nhất trong khoảnh khắc (kể cả DDL online/instant).
  - Sự cố: một transaction mở quên commit (hoặc query báo cáo dài) giữ MDL shared → `ALTER` chờ → mọi query mới trên bảng xếp hàng sau `ALTER` → bảng coi như chết, pool cạn, app sập. `SHOW PROCESSLIST` thấy `Waiting for table metadata lock`.
  - Phòng: kiểm tra transaction dài trước khi migrate; đặt `lock_wait_timeout` ngắn cho session chạy DDL để nó bỏ cuộc rồi thử lại. Postgres cùng bài toán với `ACCESS EXCLUSIVE`: `SET lock_timeout = '3s'` trước DDL.
- [ ] Optimistic và pessimistic locking
  - Optimistic: cột `version`; `UPDATE ... SET ..., version = version + 1 WHERE id = ? AND version = ?`, kiểm tra số dòng bị ảnh hưởng, bằng 0 là xung đột. Hợp khi ít xung đột, thao tác dài có người dùng suy nghĩ ở giữa (sửa bài viết).
  - Pessimistic: `SELECT ... FOR UPDATE` trong transaction. Hợp khi xung đột nhiều và thao tác ngắn (tồn kho, số dư).
  - **Đối chiếu:** JPA `@Version` và `LockModeType.PESSIMISTIC_WRITE`; Laravel `lockForUpdate()`/`sharedLock()`; Go tự viết SQL.
- [ ] Deadlock
  - Hai transaction giữ lock mà bên kia cần, chờ vòng tròn.
  - InnoDB phát hiện ngay (wait-for graph), rollback transaction "nhỏ hơn" (ít thay đổi hơn), lỗi 1213. Postgres kiểm tra sau `deadlock_timeout` (mặc định 1s) rồi huỷ một bên.
  - 🟡 Đọc log: `SHOW ENGINE INNODB STATUS` mục `LATEST DETECTED DEADLOCK` (bật `innodb_print_all_deadlocks` để ghi mọi deadlock vào error log). Với mỗi transaction xem câu SQL, `HOLDS THE LOCK(S)`, `WAITING FOR THIS LOCK`, index nào, loại lock (`locks gap before rec` là gap lock, `rec but not gap` là record lock).
  - ⚠️ Log chỉ in câu SQL đang chạy của mỗi transaction; lock có thể do câu trước đó lấy.
  - Phòng: khoá theo thứ tự cố định (sort id trước), transaction ngắn, index đúng để khoá ít dòng, giảm gap lock (RC). **Luôn có retry** ở tầng ứng dụng: deadlock không loại bỏ hoàn toàn được.
- [ ] 🟡 Lock wait timeout
  - InnoDB `innodb_lock_wait_timeout` (mặc định 50 giây), lỗi 1205. Postgres: `lock_timeout`, `statement_timeout`.
  - ⚠️ Mặc định MySQL chỉ rollback **câu lệnh**, không rollback transaction (`innodb_rollback_on_timeout=OFF`). Code bắt lỗi rồi commit tiếp là commit một nửa.
- [ ] 🟡 `SKIP LOCKED` / `NOWAIT` và job queue bằng DB
  - `FOR UPDATE SKIP LOCKED` bỏ qua dòng đang bị khoá thay vì chờ, nên nhiều worker lấy job song song không tranh nhau. MySQL 8.0+, Postgres 9.5+. `NOWAIT` báo lỗi ngay nếu bị khoá.

  ```sql
  BEGIN;
  SELECT id, payload FROM jobs
  WHERE status = 'pending' AND run_at <= now()
  ORDER BY run_at LIMIT 10
  FOR UPDATE SKIP LOCKED;
  UPDATE jobs SET status = 'running', locked_at = now(), attempts = attempts + 1 WHERE id IN (...);
  COMMIT;
  ```
  - Cần: index `(status, run_at)` (Postgres: partial index `WHERE status = 'pending'`); reaper trả job "running" quá lâu về pending (worker chết); giới hạn attempts; xử lý idempotent vì job có thể chạy lại.
  - Ưu: không thêm hạ tầng, enqueue cùng transaction với dữ liệu nghiệp vụ. Nhược: polling tải lên DB, Postgres bloat do update liên tục; throughput lớn thì chuyển sang queue thật ([12-messaging.md](12-messaging.md)).
- [ ] 🟡 Advisory lock
  - Lock theo khoá do ứng dụng tự đặt, không gắn với dòng nào. Postgres: `pg_advisory_lock(key)` (session), `pg_advisory_xact_lock(key)` (nhả khi hết transaction), `pg_try_advisory_lock`. MySQL: `GET_LOCK('name', timeout)` / `RELEASE_LOCK`.
  - Dùng: chỉ một instance chạy cron/migration, tuần tự hoá thao tác theo một user.
  - ⚠️ Lock cấp session + PgBouncer transaction pooling: lock nằm trên connection server mà request sau không còn giữ. Dùng bản `xact`. So với Redis lock: [14-distributed-systems.md](14-distributed-systems.md).

### Thiết kế schema

- [ ] Normalization
  - 1NF: mỗi ô một giá trị nguyên tử (không lưu `"tag1,tag2"`). 2NF: cột không khoá phụ thuộc *toàn bộ* khoá ghép. 3NF: không phụ thuộc bắc cầu (orders lưu `customer_id`, không lưu kèm `customer_city`).
  - Mục đích: một sự thật lưu một chỗ, tránh update lệch.
  - Denormalize khi đọc nhiều và join đắt: `comments_count`, cột tổng, bảng đọc riêng. Phải có cơ chế đồng bộ (cùng transaction, trigger, job đối soát) và chấp nhận có thể lệch.
  - ⚠️ Không phải mọi bản sao là sai: giá sản phẩm *tại thời điểm mua* trong `order_items` là dữ liệu lịch sử, bắt buộc lưu.
  - Quan hệ: 1-1 (tách cột ít dùng/lớn ra bảng riêng), 1-n (FK ở bên n), n-n (bảng trung gian, unique `(a_id, b_id)`, có thể mang thêm thuộc tính).
- [ ] Kiểu dữ liệu
  - Tiền: `DECIMAL(19,4)` hoặc số nguyên theo đơn vị nhỏ nhất, lưu kèm mã tiền tệ. ⚠️ **Không** dùng `FLOAT`/`DOUBLE`: nhị phân không biểu diễn chính xác `0.1`, cộng dồn sai lệch. Làm tròn, VND: [22-practical-data.md](22-practical-data.md).
  - Thời gian: lưu UTC, hiển thị theo timezone người dùng. MySQL `TIMESTAMP` lưu UTC và convert theo `time_zone` của session, giới hạn tới năm 2038; `DATETIME` không có khái niệm timezone. Postgres dùng `timestamptz` (lưu một thời điểm tuyệt đối, không lưu tên timezone). ⚠️ App và DB khác timezone là nguồn bug lệch 7 tiếng kinh điển ở Việt Nam.
  - Chuỗi: MySQL `utf8` cũ thực chất là `utf8mb3` (tối đa 3 byte), không lưu được emoji; dùng `utf8mb4`. ⚠️ Collation mặc định MySQL 8 `utf8mb4_0900_ai_ci` không phân biệt dấu: `'Hà' = 'Ha'`, unique index coi hai giá trị là trùng. Cần phân biệt dấu thì dùng collation `_as_cs` hoặc `_bin`.
  - Id dùng `BIGINT`: hết `INT` (~2.1 tỉ) là sự cố thật, và đổi kiểu PK trên bảng lớn rất đau. Chọn kiểu nhỏ nhất đủ dùng cho các cột khác.
- [ ] Soft delete (`deleted_at`)
  - Lợi: khôi phục được, giữ lịch sử, không vỡ tham chiếu. Giá: mọi query phải lọc (quên là lộ dữ liệu đã xoá), index nên có `deleted_at`, bảng phình.
  - ⚠️ `UNIQUE(email, deleted_at)` không chặn trùng giữa các dòng chưa xoá vì NULL khác NULL. Postgres: partial unique index `WHERE deleted_at IS NULL`. MySQL: generated column (ví dụ `IF(deleted_at IS NULL, email, NULL)`) rồi unique cột đó.
  - Thay thế: chuyển sang bảng archive khi xoá, hoặc xoá thật + audit log. Dữ liệu cá nhân theo luật có thể phải xoá thật ([10-security.md](10-security.md)).
- [ ] Khoá ngoại có nên dùng
  - Ưu: DB giữ toàn vẹn, không có dòng mồ côi dù ứng dụng có bug. Nhược: kiểm tra khi ghi, lock thêm trên bảng cha (nguồn deadlock), cản xoá/migration lớn, không tồn tại xuyên shard/xuyên service.
  - Thực tế: monolith một DB thì nên dùng; hệ sharded/microservice bỏ và kiểm tra ở ứng dụng + job đối soát.
  - ⚠️ InnoDB tự tạo index cho cột FK; Postgres **không**, thiếu index thì xoá dòng cha phải quét bảng con.
- [ ] 🟡 Dữ liệu dạng cây

  | Cách | Đọc cây con | Di chuyển nút | Ghi chú |
  |---|---|---|---|
  | Adjacency list (`parent_id`) | Recursive CTE | Rẻ (sửa 1 dòng) | Đơn giản nhất, đủ cho hầu hết |
  | Materialized path (`/1/5/12/`) | `LIKE '/1/5/%'` dùng index | Sửa path cả cây con | Postgres có `ltree` |
  | Nested set (`lft`, `rgt`) | Một range query | Rất đắt (đánh số lại) | Hợp cây gần như không đổi |
  | Closure table (ancestor–descendant) | Join đơn giản | Trung bình | Tốn dòng, linh hoạt nhất |

- [ ] 🟡 Cột JSON
  - Hợp lý: thuộc tính thay đổi theo loại sản phẩm, payload webhook lưu nguyên, cấu hình, dữ liệu đọc cả cục.
  - Dấu hiệu thiết kế lười: cột JSON bị lọc/join/sort thường xuyên, có ràng buộc cần giữ, nhiều chỗ update một phần.
  - Postgres `jsonb` (nhị phân, index GIN) tốt hơn `json` (text). MySQL `JSON` được validate và lưu nhị phân; index qua generated column/functional index.
- [ ] ⚠️ EAV (entity–attribute–value) là anti-pattern
  - Bảng `(entity_id, attribute, value)` cho "thuộc tính tuỳ ý": mất kiểu dữ liệu (mọi thứ là chuỗi), không ràng buộc được, lấy một object cần pivot/nhiều join, query rất chậm.
  - Thay bằng cột JSON hoặc bảng riêng theo loại. Magento là ví dụ nổi tiếng về chi phí của EAV.
- [ ] 🟡 Polymorphic association
  - `comments(commentable_type, commentable_id)` (Laravel `morphTo`, Rails): tiện, nhưng **không đặt được khoá ngoại**, join phải theo type, dễ có dòng mồ côi.
  - Thay thế: mỗi loại một cột FK nullable + `CHECK` đúng một cột có giá trị; bảng nối riêng cho từng loại; hoặc bảng cha chung (supertype).
- [ ] 🟡 Audit / history table
  - Trả lời "ai đổi gì, lúc nào, giá trị cũ là gì". Ghi từ ứng dụng (biết user, lý do), trigger (không sót nhưng khó biết user), hoặc CDC đọc binlog/WAL (Debezium) sang nơi lưu riêng.
  - History table `valid_from`/`valid_to` cho dữ liệu cần tra "tại thời điểm X" (giá, hợp đồng). SQL:2011 định nghĩa temporal table; MariaDB có system-versioned table.
  - ⚠️ Bảng audit lớn rất nhanh: partition theo thời gian, lên kế hoạch archive.
- [ ] 🟡 Enum
  - MySQL `ENUM`: gọn, nhưng thêm/bớt giá trị cần `ALTER TABLE`, sort theo thứ tự khai báo. Postgres enum type: `ADD VALUE` dễ, bỏ giá trị khó.
  - Thay thế: `VARCHAR` + `CHECK`, hoặc bảng lookup + FK (khi giá trị có thuộc tính hoặc do người dùng quản lý).

### ORM

- [ ] N+1 query
  - 1 query lấy N bài viết, rồi mỗi bài một query lấy tác giả. Từng query nhanh nên không lên slow log; tổng round-trip mới chết.
  - Phát hiện: đếm query mỗi request (debug toolbar, Telescope, Hibernate statistics, APM); log thấy cùng câu SQL lặp với id khác nhau.
  - Sửa: eager loading, `JOIN`, hoặc gom `WHERE id IN (...)`.
  - **Đối chiếu:** Laravel `with('author')`, `Model::preventLazyLoading()` để bắt ở dev; JPA/Hibernate `JOIN FETCH`, `@EntityGraph`, `@BatchSize`; GORM `Preload`; Go với `sqlc`/`sqlx` thì tự viết `IN`.
- [ ] Lazy và eager loading
  - Lazy: chỉ query khi truy cập quan hệ; tiện, và là nguồn N+1. ⚠️ Hibernate `LazyInitializationException` khi truy cập ngoài session; "sửa" bằng open-session-in-view là giấu N+1 vào tầng view.
  - Eager: tải trước. ⚠️ Eager nhiều collection bằng join tạo tích Descartes (1 đơn × 50 item × 10 payment = 500 dòng). Tách query `IN` thường tốt hơn một join khổng lồ.
- [ ] 🟡 ORM sinh SQL tệ
  - `->get()->count()` tải cả tập vào RAM để đếm; update từng model trong vòng lặp; `SELECT *` kéo cột lớn; `whereHas` sinh subquery `EXISTS` có thể chậm trên bảng lớn; dirty checking/flush của Hibernate tốn khi session giữ hàng nghìn entity.
  - Luôn xem SQL thật mà ORM sinh ra (bật query log) cho các màn hình quan trọng.
- [ ] 🟡 Khi nào viết raw SQL
  - Báo cáo, aggregate phức tạp, window function, CTE, bulk update/upsert, query cần hint hoặc cú pháp riêng, đường nóng cần tối ưu từng chút. Giữ ORM cho CRUD thường.
  - Raw SQL vẫn phải dùng parameter binding, không nối chuỗi ([10-security.md](10-security.md)).

### Vận hành

- [ ] Connection pool
  - Mở connection tốn (TCP, TLS, auth; Postgres fork một process mỗi connection). Pool giữ sẵn connection để dùng lại.
  - ⚠️ Pool quá lớn làm DB quá tải: nhiều query chạy song song hơn số core chỉ thêm context switch và tranh lock. Điểm khởi đầu hay được nhắc (HikariCP): khoảng `số core × 2 + số đĩa`, rồi đo mà chỉnh.
  - ⚠️ Tổng connection = số instance × pool mỗi instance (+ worker, cron). Autoscale lên 50 pod × 20 = 1000 connection, vượt `max_connections` là lỗi "too many connections".
  - **Đối chiếu:** Java/Go có pool trong process (HikariCP, `database/sql` với `SetMaxOpenConns`); PHP-FPM mỗi worker giữ connection riêng, nên số worker quyết định số connection.
  - 🟡 PgBouncer: chế độ session, **transaction** (phổ biến nhất), statement. ⚠️ Transaction mode phá tính năng gắn với session: `SET`, advisory lock cấp session, `LISTEN`, prepared statement phía server (bản mới có hỗ trợ một phần; kiểm tra lại theo phiên bản). ProxySQL (MySQL): pool, định tuyến đọc/ghi, chặn/viết lại query.
- [ ] 🟡 Online schema change
  - MySQL 8.0: nhiều thao tác `ALGORITHM=INSTANT` (thêm cột) hoặc `INPLACE, LOCK=NONE` (thêm index); vẫn cần MDL trong khoảnh khắc. Thao tác phải copy bảng (đổi kiểu cột) thì dùng tool.
  - `pt-online-schema-change`: tạo bảng mới, trigger chép thay đổi, copy theo chunk, rename. `gh-ost`: không trigger, đọc binlog để áp thay đổi, pause/điều tốc được. Cả hai cần xử lý FK cẩn thận và cần gấp đôi dung lượng bảng.
  - Postgres: `CREATE INDEX CONCURRENTLY` không khoá ghi; ⚠️ không chạy trong transaction, chậm hơn, thất bại thì để lại index `INVALID` phải xoá và tạo lại. Thêm cột có default hằng số nhanh từ Postgres 11. Thêm FK/CHECK: `ADD CONSTRAINT ... NOT VALID` rồi `VALIDATE CONSTRAINT` riêng.
- [ ] Migration an toàn: expand/contract
  - Code cũ và mới chạy song song trong lúc deploy, nên mỗi bước schema phải tương thích với cả hai.
  - Đổi tên cột: thêm cột mới → code ghi cả hai → backfill theo batch → code đọc cột mới → ngừng ghi cột cũ → xoá cột cũ. Mỗi bước một lần deploy.
  - Thêm cột `NOT NULL`: thêm nullable → backfill → thêm ràng buộc.
  - ⚠️ Xoá cột khi code cũ còn đọc nó (hoặc ORM cache danh sách cột) là lỗi ngay lúc deploy. Migration huỷ dữ liệu không rollback được: tách khỏi deploy app, có kế hoạch lùi.
- [ ] Backup, PITR, RPO/RTO
  - Logical: `mysqldump --single-transaction`, `mydumper`, `pg_dump`. Di động, chọn được từng bảng; chậm và restore lâu với DB lớn.
  - Physical: Percona XtraBackup, `pg_basebackup`, pgBackRest, snapshot đĩa. Nhanh với DB lớn, gắn với phiên bản.
  - PITR: base backup + replay binlog/WAL tới ngay trước sự cố (trước câu `DELETE` quên `WHERE`). Cần lưu binlog/WAL liên tục ra nơi khác.
  - 🟡 RPO: được phép mất bao nhiêu dữ liệu (tính bằng thời gian). RTO: mất bao lâu để chạy lại. Chi tiết: [18-reliability-observability.md](18-reliability-observability.md).
  - ⚠️ Backup chưa từng restore thử thì chưa chắc dùng được: diễn tập định kỳ, đo thời gian restore thật. Replica **không phải** backup: `DROP TABLE` được replicate ngay. Backup phải mã hoá, tách quyền, để ở account/region khác.

### Scale

- [ ] 🟡 Read replica và replication
  - Primary nhận ghi, replica áp lại thay đổi (MySQL qua binlog; Postgres streaming WAL vật lý, hoặc logical replication).
  - Async: primary không chờ replica; primary chết có thể mất giao dịch chưa sang. Semi-sync (MySQL): chờ ít nhất một replica **nhận** log (chưa chắc đã áp). Sync (Postgres `synchronous_standby_names` + `synchronous_commit`): chờ replica xác nhận; ghi chậm hơn, replica chết có thể chặn ghi.
  - Replica giảm tải đọc, không giảm tải ghi (mọi replica phải áp mọi ghi).
- [ ] 🟡 Replication lag và read-your-writes
  - Lag do transaction lớn, replica yếu hơn, áp log thiếu song song, query dài trên replica. Theo dõi: MySQL `Seconds_Behind_Source` (không hoàn toàn đáng tin), Postgres `pg_stat_replication` (`replay_lag`).
  - Triệu chứng: user vừa đổi tên, reload thấy tên cũ.
  - Xử lý: đọc primary vài giây sau khi user ghi (Laravel có option `sticky`); đọc dữ liệu của chính mình từ primary; lưu GTID/LSN sau khi ghi và chờ replica đuổi kịp; chấp nhận eventual consistency ở màn hình không quan trọng.
  - ⚠️ Không đọc replica trong luồng "đọc để ghi" (kiểm tra số dư rồi trừ).
- [ ] 🔴 Failover
  - Tự động: Orchestrator (MySQL), Patroni (Postgres), dịch vụ managed (RDS, Cloud SQL). Chọn replica mới nhất, trỏ app sang (DNS, proxy, VIP).
  - ⚠️ Async failover có thể mất giao dịch cuối. Split brain: hai node cùng tưởng mình là primary; cần fencing (tắt hẳn primary cũ) và quorum ([14-distributed-systems.md](14-distributed-systems.md)).
  - App phải chịu được connection đứt, retry, DNS TTL, pool giữ connection tới node cũ.
- [ ] 🔴 Partitioning (trong một DB)
  - Range (theo tháng), list (theo vùng), hash (chia đều). Postgres declarative partitioning (từ 10); MySQL có partitioning sẵn.
  - Lợi: partition pruning khi query có khoá partition; xoá dữ liệu cũ bằng `DROP PARTITION` thay vì `DELETE` hàng triệu dòng; index mỗi partition nhỏ hơn.
  - ⚠️ Query không có khoá partition thì quét mọi partition. Unique/PK phải chứa cột partition (cả hai DB). Bảng partitioned của MySQL không hỗ trợ FK.
- [ ] 🔴 Sharding (nhiều DB)
  - Làm khi đã hết cách: tối ưu query, index, cache, replica, máy to hơn, tách DB theo chức năng, partition, archive. Sharding tăng độ phức tạp vĩnh viễn.
  - Shard key: chia đều tải, đa số query chứa key (thường `tenant_id`/`user_id`). ⚠️ Shard theo thời gian tạo hot shard; shard key sai rất khó sửa.
  - Định tuyến: hash (`hash(key) % N`, khó thêm shard), consistent hashing, directory (bảng tra key → shard, linh hoạt nhưng thêm một phụ thuộc).
  - Cross-shard: join, aggregate, sort làm ở tầng app/proxy (scatter-gather); transaction xuyên shard cần 2PC hoặc saga; unique toàn cục và ID cần sinh phân tán (Snowflake, UUIDv7).
  - Resharding: dual write hoặc CDC sang layout mới, backfill, đối soát, chuyển đọc rồi chuyển ghi. Chia trước nhiều shard logic trên ít máy vật lý để về sau chỉ di chuyển shard logic.
  - Vitess (MySQL, xuất phát từ YouTube): proxy `vtgate`, resharding online. Citus (extension Postgres): bảng distributed theo cột, bảng reference nhân bản lên mọi node.
- [ ] 🟡 Archiving dữ liệu cũ
  - Bảng orders 5 năm nhưng chỉ 3 tháng gần đây nóng: chuyển dữ liệu cũ sang bảng/DB archive, kho OLAP hoặc object storage; xoá theo batch hoặc drop partition.
  - ⚠️ `DELETE` hàng triệu dòng một lần: lock lâu, lag replica, undo/WAL phình, Postgres bloat.

### MySQL vs Postgres

- [ ] 🔴 Khác biệt thực tế

  | | MySQL (InnoDB) | PostgreSQL |
  |---|---|---|
  | Lưu trữ | Clustered theo PK | Heap + index trỏ ctid |
  | MVCC | Undo log, purge | Tuple version trong heap, VACUUM |
  | Isolation mặc định | Repeatable Read | Read Committed |
  | Connection | Thread mỗi connection | Process mỗi connection, thường cần PgBouncer |
  | Join | Nested loop, hash join (8.0.18+) | Nested loop, hash, merge |
  | Index | B-tree, full-text, spatial, functional | B-tree, hash, GIN, GiST, BRIN, partial, expression |
  | DDL trong transaction | Không (DDL tự commit) | Có, migration rollback được |
  | Kiểu dữ liệu | Cơ bản, `JSON` | `jsonb`, mảng, range, `inet`, `uuid`, enum type, kiểu tự định nghĩa |
  | Mở rộng | Plugin hạn chế | Extension: PostGIS, pg_trgm, pgvector, TimescaleDB, Citus |
  | Hệ sinh thái scale | Vitess, ProxySQL, gh-ost, Orchestrator | Citus, Patroni, PgBouncer |

  - ⚠️ DDL tự commit ở MySQL: migration nhiều bước fail giữa chừng để lại schema dở dang.
  - Không có "cái nào tốt hơn" chung chung: chọn theo đội ngũ đã quen, tính năng cần (GIS, jsonb, extension), dịch vụ managed sẵn có.

### OLTP vs OLAP

- [ ] 🟡 OLTP: nhiều transaction nhỏ, đọc/ghi theo dòng, latency thấp. OLAP: ít query nhưng quét hàng triệu dòng, aggregate theo cột. ⚠️ Chạy báo cáo nặng trên DB OLTP (kể cả replica) làm nghẽn I/O, đẩy dữ liệu nóng khỏi buffer pool, giữ snapshot lâu. Column store, data warehouse, ETL/ELT: xem [04-nosql-search-storage.md](04-nosql-search-storage.md).

## Senior trả lời khác gì

- **"Index giúp gì?"**
  - Mid: "Index làm query nhanh hơn, nên index các cột trong WHERE."
  - Senior: nói B+tree, leftmost prefix, covering, cái giá khi ghi; thiết kế index từ *tập query* chứ không từ từng cột; kiểm chứng bằng `EXPLAIN ANALYZE`; định kỳ dọn index không ai dùng.
- **"Làm sao tránh hai người cùng mua món hàng cuối cùng?"**
  - Mid: "Dùng transaction."
  - Senior: transaction ở isolation mặc định vẫn cho lost update; chọn giữa update atomic có điều kiện (`WHERE stock > 0` + kiểm tra affected rows), `FOR UPDATE`, hay optimistic version tuỳ mức tranh chấp; flash sale thì một dòng tồn kho thành nút cổ chai, cân nhắc chia bucket hoặc giữ chỗ qua Redis/queue rồi đối soát.
- **"Chọn isolation level nào?"**
  - Mid: "Để mặc định."
  - Senior: biết mặc định của DB mình dùng và nó *không* chặn anomaly nào; đa số hệ thống chạy RC/RR và xử lý điểm nhạy cảm bằng lock tường minh hoặc ràng buộc; lên Serializable thì bắt buộc có retry `40001` và đo tỉ lệ abort.
- **"Bảng 500 triệu dòng, cần thêm cột và index."**
  - Mid: "Chạy `ALTER TABLE` lúc ít người dùng."
  - Senior: kiểm tra có INSTANT/INPLACE được không; phải copy bảng thì gh-ost điều tốc theo replica lag; `lock_wait_timeout` ngắn để không treo vì MDL; kiểm tra dung lượng đĩa; kế hoạch rollback; theo dõi trong lúc chạy.
- **"DB chậm, làm gì?"**
  - Mid: "Thêm index, thêm cache."
  - Senior: đo trước (`pg_stat_statements`/slow log xếp theo tổng thời gian); phân biệt query tệ, lock contention, connection cạn, working set vượt RAM, replication lag; sửa đúng nguyên nhân rồi mới tới replica, cache; sharding là lựa chọn cuối.
- **"Có nên dùng khoá ngoại?"**
  - Mid: "Có, để toàn vẹn" hoặc "Không, vì chậm."
  - Senior: tuỳ bối cảnh: monolith một DB thì dùng, chi phí nhỏ so với dữ liệu hỏng; sharded hoặc nhiều service thì không thể, thay bằng kiểm tra ở ứng dụng + job đối soát; nhắc index cột FK ở Postgres và lock trên bảng cha.

## Tình huống

1. **Deploy migration thêm cột, cả app treo 5 phút, mọi request timeout.**
   - Gợi ý: nghi metadata lock. Transaction dài/idle giữ MDL shared, `ALTER` chờ MDL exclusive, query sau xếp hàng sau `ALTER`.
   - Xác nhận: `SHOW PROCESSLIST` (`Waiting for table metadata lock`), `performance_schema.metadata_locks`; Postgres `pg_locks` + `pg_stat_activity`.
   - Phòng: `lock_wait_timeout`/`lock_timeout` ngắn cho DDL + retry; kiểm tra transaction dài trước khi migrate; timeout cho transaction idle.
2. **Query danh sách đơn hàng đang 20ms, sau đợt import dữ liệu thành 8 giây, code không đổi.**
   - Gợi ý: plan đổi. So `EXPLAIN` trước/sau; statistics cũ (chạy `ANALYZE`); ước lượng rows lệch thực tế; dữ liệu lệch khiến optimizer chọn index khác hoặc full scan.
   - Ngắn hạn: `ANALYZE`, hint/`FORCE INDEX`. Dài hạn: index phù hợp hơn, histogram, cảnh báo khi p95 của query tăng.
3. **Log báo deadlock vài chục lần mỗi giờ ở luồng đặt hàng.**
   - Gợi ý: đọc `LATEST DETECTED DEADLOCK`, xác định hai câu SQL, index, loại lock (gap hay record). Hay gặp: khoá nhiều dòng theo thứ tự khác nhau (trừ tồn kho giỏ hàng không sort theo `product_id`); `FOR UPDATE` trên dòng chưa tồn tại tạo gap lock.
   - Sửa: sort id trước khi khoá, index cho điều kiện khoá, cân nhắc RC, transaction ngắn, retry có backoff.
4. **User báo: vừa sửa hồ sơ, tải lại trang thấy thông tin cũ, lát sau mới đúng.**
   - Gợi ý: replication lag khi đọc từ replica (hoặc cache chưa xoá, xem [11-cache.md](11-cache.md)). Sửa: sticky đọc primary sau khi ghi, đọc dữ liệu của chính mình từ primary, theo dõi và cảnh báo lag.
5. **Bảng `events` Postgres 200GB dù chỉ có vài triệu dòng sống, query ngày càng chậm.**
   - Gợi ý: bloat. Tìm thứ chặn autovacuum: `idle in transaction` trong `pg_stat_activity`, replication slot bỏ quên, transaction dài.
   - Sửa: dọn nguyên nhân, chỉnh autovacuum riêng cho bảng, `pg_repack` để thu hồi; lâu dài partition theo thời gian và drop partition cũ.
6. **Ai đó chạy `DELETE FROM orders` quên `WHERE` lúc 14:03 trên production.**
   - Gợi ý: dừng ghi liên quan; replica cũng đã xoá theo; PITR ra máy riêng: base backup mới nhất + replay binlog/WAL tới ngay trước 14:03, rồi chép dữ liệu mất về; tính RPO thực tế. Hậu kiểm: quyền trên production, `sql_safe_updates`, review query chạy tay.
7. **Tồn kho bị âm trong đợt flash sale dù code có kiểm tra `if stock > 0`.**
   - Gợi ý: check-then-act không atomic (lost update). Sửa: `UPDATE ... SET stock = stock - 1 WHERE id = ? AND stock > 0` và kiểm tra affected rows, hoặc `FOR UPDATE`. Tranh chấp quá cao trên một dòng thì chia bucket tồn kho hoặc xếp hàng qua Redis/queue.

## ❓ Câu hỏi hay gặp

🟢
- Index là gì, vì sao dùng B+tree? Khi nào **không** nên thêm index?
- Vì sao `OFFSET` lớn lại chậm? Sửa thế nào?
- `WHERE` và `HAVING` khác nhau thế nào? `INNER JOIN` và `LEFT JOIN`?
- Vì sao không nên lưu tiền bằng `FLOAT`?
- ACID là gì, cho ví dụ từng chữ.
- N+1 query là gì, phát hiện và sửa thế nào?

🟡
- Bảng có index `(user_id, status, created_at)`. Query `WHERE status = 1 AND created_at > ?` có dùng index không? Vì sao?
- Covering index là gì? Clustered và secondary index khác nhau thế nào trong InnoDB?
- Hai người cùng sửa một bài viết, làm sao không ghi đè mất sửa đổi của nhau?
- Có một query chậm trên production, bạn làm những bước gì?
- Kể các isolation level và anomaly mỗi level chặn. MySQL và Postgres mặc định level nào?
- Vì sao `NOT IN` với subquery có NULL lại trả về rỗng?
- Deadlock xảy ra thế nào, phòng thế nào? Đọc deadlock log ra sao?
- Đổi tên cột không downtime thế nào?
- UUIDv4 làm primary key trong InnoDB có vấn đề gì?

🔴
- Write skew là gì? Postgres Repeatable Read có chặn được không? Serializable (SSI) chặn thế nào?
- MVCC của InnoDB và Postgres khác nhau thế nào? VACUUM để làm gì, bloat từ đâu ra?
- Gap lock và next-key lock là gì, vì sao gây deadlock?
- Redo log, undo log, binlog khác nhau thế nào? Doublewrite buffer giải quyết vấn đề gì?
- LSM tree khác B-tree thế nào, khi nào chọn cái nào?
- Khi nào bạn quyết định shard? Chọn shard key thế nào, resharding ra sao?

## Bài tập tự làm

1. **SQL kinh điển.** Schema: `users(id, name, email, created_at)`, `orders(id, user_id, total, status, created_at)`, `logins(user_id, login_date)`, `employees(id, name, manager_id, department_id, salary)`. Viết query cho mỗi đề, chạy thử trên cả MySQL 8 và Postgres nếu có:
   - a. Top 3 đơn giá trị lớn nhất của mỗi user (nói rõ bạn xử lý trường hợp bằng giá trị thế nào).
   - b. Doanh thu theo ngày và doanh thu cộng dồn (running total) trong tháng.
   - c. Tìm các user trùng email (không phân biệt hoa thường), rồi viết câu xoá bản trùng, giữ bản có id nhỏ nhất.
   - d. Gaps and islands: chuỗi ngày đăng nhập liên tiếp dài nhất của mỗi user trong `logins`.
   - e. User đăng ký trong tháng 1 nhưng chưa từng có đơn `paid` (viết hai cách, một cách dính bẫy NULL).
   - f. Nhân viên lương cao hơn quản lý trực tiếp; và toàn bộ cấp dưới (mọi tầng) của nhân viên id 1.
   - g. Mức lương cao thứ hai của mỗi phòng ban.
   - h. Tỉ lệ user mua lần thứ hai trong vòng 30 ngày kể từ đơn đầu tiên.
2. **Thiết kế index.** Bảng `orders` 100 triệu dòng với 4 query: danh sách đơn của một user mới nhất trước (phân trang), đơn `pending` quá 30 phút, tổng doanh thu theo ngày của một shop, tìm đơn theo mã đơn. Đề xuất bộ index tối thiểu, giải thích thứ tự cột, và viết `EXPLAIN` bạn kỳ vọng thấy cho từng query.
3. **Anomaly bằng tay.** Mở hai session `psql` (hoặc `mysql`). Tái hiện: non-repeatable read ở RC, lost update ở MySQL RR, lỗi `40001` ở Postgres RR, write skew bài bác sĩ trực ở Postgres RR, và chứng minh Serializable chặn được. Ghi lại từng bước và kết quả.
4. **Job queue bằng DB.** Thiết kế bảng `jobs` và query cho worker dùng `SKIP LOCKED`, gồm retry có backoff, giới hạn số lần thử, xử lý worker chết giữa chừng. Nêu điểm nào khiến bạn chuyển sang queue thật.
5. **Migration không downtime.** Lập kế hoạch từng bước (mỗi bước: deploy code gì, đổi schema gì, rollback thế nào) để tách `users.full_name` thành `first_name` và `last_name` trên bảng 50 triệu dòng đang nhận ghi liên tục.

> Nộp bài vào đây để được review.
