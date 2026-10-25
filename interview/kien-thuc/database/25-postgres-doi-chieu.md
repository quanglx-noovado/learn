# Chương 25. PostgreSQL: đối chiếu với MySQL

> [← Mục lục](README.md) · [← Chương 24: Vận hành và giám sát](24-van-hanh-monitoring.md) · (chương cuối)

**Bạn sẽ học được:**

- PostgreSQL chạy thế nào ở mức hệ điều hành: mỗi connection là một process riêng (postmaster, backend),
  bộ nhớ chung `shared_buffers`, và vì sao điều đó làm connection của Postgres "đắt" hơn MySQL.
- MVCC kiểu Postgres: phiên bản cũ của dòng nằm **ngay trong bảng** (`xmin`, `xmax`), không có undo log.
  Từ đó hiểu VACUUM, autovacuum, bloat, HOT update và xid wraparound.
- Isolation level của Postgres: mặc định `READ COMMITTED`, `REPEATABLE READ` là snapshot isolation thật
  (lỗi 40001), `SERIALIZABLE` là SSI.
- Những thứ Postgres có mà MySQL 8.4 không có hoặc có ít hơn: `jsonb`, array, range type, index GIN, GiST,
  BRIN, partial index, expression index, `INCLUDE`, DDL trong transaction, `CREATE INDEX CONCURRENTLY`,
  hệ extension (PostGIS, pgvector, pg_trgm, pg_stat_statements).
- PgBouncer và ba chế độ pool, cùng cái bẫy prepared statement ở chế độ `transaction`.
- Bảng so sánh tổng MySQL 8.4 và PostgreSQL 18, và cách chọn giữa hai hệ cho một dự án thật.

**Cần biết trước:** Gần như cả giáo trình. Chương này là **bản tổng hợp**: các chương trước đã có đoạn
đối chiếu Postgres ngắn đặt cạnh từng chủ đề MySQL, ở đây gom lại thành một bức tranh và đi sâu thêm chỗ
cần. Đặc biệt nên đọc trước [chương 11](11-index.md) (index), [chương 14](14-isolation-mvcc.md)
(isolation, MVCC), [chương 16](16-ben-trong-innodb.md) (undo log, purge, redo) và
[chương 20](20-thay-doi-schema-migration.md) (online DDL).

Mọi số liệu mặc định trong chương lấy từ tài liệu PostgreSQL 18 (postgresql.org/docs/18) và tài liệu
MySQL 8.4. Mặc định có thể đổi giữa các bản, nên khi vận hành thật hãy kiểm lại bằng `SHOW` trên server
của bạn.

## 1. Chuẩn bị: chạy PostgreSQL 18 và dữ liệu mẫu

### 1.1 Chạy server

Cách chạy giống [chương 1 mục 7.2](01-database-la-gi.md):

```bash
docker run -d --name pg18 -e POSTGRES_PASSWORD=pg -p 5432:5432 \
  -v pg18data:/var/lib/postgresql postgres:18
docker exec -it pg18 psql -U postgres
```

Muốn hai session A, B cho các timeline, mở hai cửa sổ terminal và chạy `docker exec -it pg18 psql -U
postgres` ở mỗi cửa sổ. Các lệnh `psql` hay dùng (`\d`, `\dt`, `\x`, `\timing`) xem
[chương 1 mục 10.7](01-database-la-gi.md#107-đối-chiếu-các-lệnh-tương-đương-trong-psql).

Trong chương này, **mọi câu SQL là PostgreSQL** trừ chỗ ghi rõ `-- MySQL`.

### 1.2 Dữ liệu mẫu

```sql
-- PostgreSQL 18
CREATE TABLE accounts (
    id      integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    owner   text          NOT NULL,
    balance numeric(12,2) NOT NULL CHECK (balance >= 0)
);
INSERT INTO accounts (owner, balance) VALUES ('An', 500), ('Binh', 300);

CREATE TABLE doctors (
    id       integer PRIMARY KEY,
    name     text    NOT NULL,
    shift_id integer NOT NULL,
    on_call  boolean NOT NULL
);
INSERT INTO doctors VALUES (1, 'Alice', 1, true), (2, 'Bob', 1, true);

CREATE TABLE products (
    id     bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name   text    NOT NULL,
    price  numeric(12,2) NOT NULL,
    tags   text[]  NOT NULL DEFAULT '{}',
    attrs  jsonb   NOT NULL DEFAULT '{}'
);
INSERT INTO products (name, price, tags, attrs) VALUES
  ('Ao thun',   150000, '{thoi-trang,nam}', '{"color": "red",  "size": ["M","L"]}'),
  ('Quan jean', 450000, '{thoi-trang}',      '{"color": "blue", "size": ["L"]}'),
  ('Tai nghe',  900000, '{dien-tu}',         '{"color": "black", "wireless": true}');
```

Vài khác biệt cú pháp đã thấy ngay, so với bản MySQL ở các chương trước:

- `GENERATED ALWAYS AS IDENTITY` là cách chuẩn SQL để có cột tự tăng; tương đương `AUTO_INCREMENT` của
  MySQL. (`serial` là cách cũ, vẫn chạy.)
- `text` không cần độ dài; `boolean` là kiểu thật, giá trị `true`/`false` (MySQL `BOOLEAN` là
  `TINYINT(1)`).
- `text[]` là mảng, `jsonb` là JSON nhị phân. Mục 6 nói kỹ.
- Không có `ENGINE = InnoDB`: Postgres chỉ có một cách lưu bảng chuẩn (heap).

## 2. Kiến trúc: mỗi connection một process

### 2.1 Postmaster và backend

MySQL là **một process** (`mysqld`), mỗi connection được phục vụ bởi một **thread** trong process đó.
PostgreSQL thì theo mô hình *process per user*, như tài liệu gọi:

1. Khi server khởi động, process đầu tiên chạy là *postmaster* (trong `ps` hiện là `postgres`). Nó lắng
   nghe cổng (mặc định 5432), cấp phát vùng nhớ chung, rồi sinh các process nền.
2. Mỗi khi client kết nối, postmaster **fork** ra một process mới, gọi là *backend*, dành riêng cho
   connection đó. Từ đó client nói chuyện thẳng với backend của mình.
3. Client ngắt kết nối thì backend kết thúc.

```
                 +-------------+
  client 1 ----> | backend 1   |\
  client 2 ----> | backend 2   | \        +-------------------+
  client 3 ----> | backend 3   |  >-----> | shared memory     |
                 +-------------+ /        | (shared_buffers,  |
   postmaster (fork backend) ---/         |  WAL buffers,     |
   checkpointer, bgwriter, walwriter,     |  lock table ...)  |
   autovacuum launcher, io workers ...    +-------------------+
```

Xem các process trong container (output minh hoạ, đã rút gọn):

```bash
docker exec pg18 ps -eo pid,cmd
```

```
  PID CMD
    1 postgres
   27 postgres: io worker 0
   28 postgres: io worker 1
   29 postgres: io worker 2
   30 postgres: checkpointer
   31 postgres: background writer
   33 postgres: walwriter
   34 postgres: autovacuum launcher
   35 postgres: logical replication launcher
   61 postgres: postgres postgres [local] idle
```

Dòng cuối là backend của session `psql` đang mở: user `postgres`, database `postgres`, trạng thái
`idle`. Trong SQL, xem bằng `pg_stat_activity` (tương đương `SHOW PROCESSLIST` của MySQL):

```sql
SELECT pid, usename, datname, state, backend_type, query
FROM pg_stat_activity;
```

`pid` ở đây chính là PID của process hệ điều hành. Huỷ câu đang chạy: `SELECT pg_cancel_backend(pid)`;
ngắt hẳn connection: `SELECT pg_terminate_backend(pid)` (tương đương `KILL QUERY` và `KILL` của MySQL).

### 2.2 Các process nền

| Process | Việc | Tương đương gần nhất ở InnoDB |
|---|---|---|
| checkpointer | Định kỳ ghi mọi page bẩn ra đĩa, đánh dấu checkpoint trong WAL | Checkpoint của InnoDB ([chương 16](16-ben-trong-innodb.md)) |
| background writer | Ghi dần page bẩn để backend ít phải tự ghi khi cần chỗ trống | Page cleaner thread |
| walwriter | Ghi WAL buffer xuống đĩa | Log writer |
| autovacuum launcher + worker | Dọn dead tuple, cập nhật thống kê, freeze (mục 4) | Purge thread (chỉ một phần việc) |
| io worker | Thực hiện I/O bất đồng bộ (mới ở bản 18, mục 2.3) | Thread I/O của InnoDB |
| walsender | Gửi WAL cho replica | Binlog dump thread |

### 2.3 Shared buffers và cache của hệ điều hành

`shared_buffers` là vùng cache page dữ liệu dùng chung của mọi backend, vai trò như buffer pool của
InnoDB. Mặc định **128MB** (cùng con số với `innodb_buffer_pool_size` mặc định của MySQL 8.4), nhưng
cách định cỡ khác hẳn:

- InnoDB thường được cấu hình để tự quản lý cache và bỏ qua cache của hệ điều hành; lời khuyên phổ biến
  là cho buffer pool phần lớn RAM của máy chỉ chạy database.
- Postgres đọc ghi file qua hệ điều hành và **dựa vào cả page cache của OS**. Tài liệu Postgres 18 khuyên:
  với server riêng có từ 1GB RAM, khởi điểm hợp lý là **25% RAM**; và vì Postgres còn dựa vào cache của
  OS, khó có chuyện để quá **40% RAM** cho `shared_buffers` lại tốt hơn mức nhỏ hơn.

Vài tham số bộ nhớ khác, theo tài liệu (giá trị mặc định):

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `shared_buffers` | 128MB | Cache page dùng chung; đổi phải restart |
| `work_mem` | 4MB | Bộ nhớ cho **mỗi** thao tác sort/hash trong một query trước khi tràn ra file tạm |
| `maintenance_work_mem` | 64MB | Cho `VACUUM`, `CREATE INDEX`, thêm foreign key; mỗi autovacuum worker được dùng tới mức này |
| `max_connections` | 100 | Số connection tối đa (MySQL 8.4: `max_connections` mặc định 151) |

Cạm bẫy của `work_mem`: con số là cho **mỗi thao tác**, không phải mỗi query hay mỗi connection. Một
query có ba phép sort và hai hash join, chạy song song trên 200 connection, có thể dùng gấp hàng nghìn
lần `work_mem`. Tăng `work_mem` lên 1GB "cho nhanh" là cách nhanh nhất làm server hết RAM.

**Mới ở PostgreSQL 18: asynchronous I/O.** Bản 18 thêm hệ thống I/O bất đồng bộ, theo release notes có thể
tăng tốc sequential scan, bitmap heap scan, vacuum. Bật bằng `io_method`: mặc định `worker` (dùng các
process io worker, số lượng `io_workers` mặc định 3), hoặc `io_uring` (Linux, cần bản build có liburing),
hoặc `sync` (cách cũ, đồng bộ).

### 2.4 Hệ quả: connection của Postgres đắt

Fork một process và khởi tạo bộ nhớ riêng cho nó tốn hơn tạo một thread. Mỗi backend còn giữ cache riêng
(catalog, plan) và có `work_mem` riêng. Vì vậy:

- Mở và đóng connection liên tục (kiểu PHP-FPM không có pool, mỗi request một connection) tốn hơn trên
  Postgres so với MySQL.
- Vài nghìn connection đồng thời, phần lớn đứng `idle`, vẫn chiếm bộ nhớ và làm nặng các thao tác phải
  duyệt danh sách mọi backend (ví dụ chụp snapshot).

Lời giải gần như bắt buộc ở quy mô lớn là **connection pool đặt trước Postgres**, phổ biến nhất là
PgBouncer (mục 10). MySQL cũng có giới hạn tương tự nhưng ngưỡng đau đến muộn hơn; ProxySQL đóng vai
trò giống PgBouncer ([chương 19](19-database-tu-ung-dung.md)).

## 3. Lưu trữ và MVCC: phiên bản cũ nằm trong bảng

[Chương 16 mục 11](16-ben-trong-innodb.md#11-đối-chiếu-postgresql) đã đặt hai cách lưu cạnh nhau. Ở đây ta
tự tay nhìn thấy cơ chế.

### 3.1 Heap và ctid

Bảng Postgres là một *heap*: các dòng (gọi là *tuple*) nằm trong page 8KB, không theo thứ tự nào. Mỗi
tuple có địa chỉ vật lý *ctid* dạng `(số page, số thứ tự trong page)`. Mọi index, kể cả primary key, là
cấu trúc riêng, lá chứa ctid.

So với InnoDB: bảng **là** clustered index theo primary key, secondary index chứa giá trị primary key
([chương 11 mục 4.5](11-index.md#45-đối-chiếu-nhanh-postgresql-không-có-clustered-index-kiểu-innodb)).
Hệ quả thực tế:

- Ở MySQL, chọn primary key tăng dần (không dùng UUID v4 ngẫu nhiên) rất quan trọng vì nó quyết định
  thứ tự vật lý. Ở Postgres, PK chỉ là một index như mọi index khác; UUID ngẫu nhiên vẫn làm index PK
  phân mảnh, nhưng không làm "cả bảng" bị chèn lung tung. (Postgres 18 có hàm `uuidv7()` sinh UUID tăng
  dần theo thời gian.)
- Secondary index của Postgres trỏ thẳng tới heap, không phải đi qua cây PK lần hai.
- Ngược lại, khi dòng đổi chỗ (mỗi `UPDATE` tạo tuple mới, mục 3.2), index phải biết chỗ mới.

### 3.2 Tự xem xmin, xmax, ctid

Mỗi tuple có các cột hệ thống ẩn, phải gọi đích danh mới thấy. Hai cột quan trọng:

- `xmin`: id của transaction đã tạo ra tuple này.
- `xmax`: id của transaction đã xoá hoặc thay thế nó (0 nếu chưa ai đụng tới).

```sql
SELECT ctid, xmin, xmax, id, owner, balance FROM accounts;
```

```
 ctid  | xmin | xmax | id | owner | balance
-------+------+------+----+-------+---------
 (0,1) |  754 |    0 |  1 | An    |  500.00
 (0,2) |  754 |    0 |  2 | Binh  |  300.00
```

(Output minh hoạ: số transaction trên máy bạn sẽ khác.) Cả hai dòng được tạo bởi cùng câu `INSERT`, tức
transaction 754. Giờ sửa một dòng:

```sql
BEGIN;
SELECT pg_current_xact_id();          -- giả sử ra 755
UPDATE accounts SET balance = 450 WHERE id = 1;
SELECT ctid, xmin, xmax, id, balance FROM accounts;
COMMIT;
```

```
 ctid  | xmin | xmax | id | balance
-------+------+------+----+---------
 (0,2) |  754 |    0 |  2 |  300.00
 (0,3) |  755 |    0 |  1 |  450.00
```

Dòng `id = 1` giờ ở ctid `(0,3)`, `xmin = 755`. Tuple cũ ở `(0,1)` **vẫn nằm trong page**, chỉ là được
đánh `xmax = 755` nên câu `SELECT` thường không còn thấy. Nói cách khác:

- `UPDATE` = ghi tuple mới + đánh dấu tuple cũ. Không sửa tại chỗ.
- `DELETE` = chỉ đặt `xmax`. Dữ liệu vẫn nằm đó.
- `ROLLBACK` gần như không tốn gì: transaction được ghi là aborted, các tuple nó tạo ra trở thành vô hình
  với mọi người, chờ dọn. InnoDB thì phải áp ngược undo log, transaction lớn rollback rất lâu.

Muốn nhìn thấy cả tuple đã chết, cần extension `pageinspect` (đọc page thô); không cần cho mục đích học
ở đây.

### 3.3 Snapshot quyết định ai thấy tuple nào

Khi một câu lệnh (ở `READ COMMITTED`) hoặc một transaction (ở `REPEATABLE READ`) bắt đầu, Postgres chụp
một *snapshot*: danh sách transaction nào đã commit, transaction nào còn đang chạy. Một tuple là "nhìn
thấy được" với snapshot đó khi, nói gọn:

- `xmin` là transaction đã commit trước snapshot (hoặc chính mình), **và**
- `xmax` là 0, hoặc là transaction bị abort, hoặc là transaction chưa commit tại thời điểm snapshot.

Đây đúng là ý tưởng read view của InnoDB ([chương 14](14-isolation-mvcc.md)), chỉ khác chỗ để các phiên
bản: InnoDB đi theo chuỗi `roll_ptr` vào undo log để dựng lại bản cũ, Postgres thì các bản đều là tuple
thật trong heap, chỉ cần lọc theo `xmin`/`xmax`.

### 3.4 Bảng so sánh nhanh

| Khía cạnh | InnoDB (MySQL 8.4) | PostgreSQL 18 |
|---|---|---|
| Bảng | Clustered index theo PK | Heap, mọi index trỏ tới ctid |
| Phiên bản cũ | Trong undo log, tách khỏi bảng | Tuple cũ nằm ngay trong heap |
| `UPDATE` | Sửa tại chỗ, bản cũ ghi sang undo | Ghi tuple mới, đặt `xmax` cho tuple cũ |
| Dọn rác | Purge thread dọn undo | VACUUM dọn dead tuple trong bảng và index |
| Rollback | Áp ngược undo, tốn thời gian | Gần như tức thì |
| Rủi ro riêng | Transaction dài làm undo phình | Bloat, xid wraparound |

Không có cách nào "tốt hơn tuyệt đối". Cách của Postgres làm rollback rẻ và đọc bản cũ rẻ, nhưng đẩy chi
phí sang việc dọn dẹp, mà việc dọn dẹp đó là chủ đề của mục tiếp theo.

## 4. VACUUM, autovacuum, bloat, HOT, wraparound

### 4.1 VACUUM làm gì

Tuple không còn transaction nào có thể nhìn thấy gọi là *dead tuple*. `VACUUM` (không có `FULL`):

1. Dọn dead tuple trong bảng và các entry index trỏ tới chúng, đánh dấu chỗ trống để tái sử dụng.
2. Cập nhật *visibility map*: page nào chỉ chứa tuple mà mọi transaction đều thấy. Index-only scan cần
   bản đồ này để khỏi phải đọc heap kiểm tra tính nhìn thấy.
3. *Freeze* tuple đủ cũ để chống xid wraparound (mục 4.5).
4. Cập nhật thống kê kích thước (`pg_class.reltuples`); `VACUUM ANALYZE` cập nhật thêm thống kê cho
   planner.

Theo tài liệu, `VACUUM` thường **chạy song song** với `SELECT`, `INSERT`, `UPDATE`, `DELETE`; chỉ thay đổi
schema như `ALTER TABLE` bị chặn trong lúc nó chạy. Nó **không trả chỗ trống về hệ điều hành**, trừ khi một
hoặc nhiều page ở cuối bảng trống hẳn và lấy được lock độc quyền dễ dàng. File bảng không nhỏ đi, nhưng
chỗ trống được dùng lại cho dòng mới.

`VACUUM FULL` thì khác: viết lại cả bảng sang file mới, trả chỗ về OS, nhưng cần lock `ACCESS EXCLUSIVE`
(chặn cả đọc) suốt thời gian chạy, chậm hơn nhiều và cần thêm dung lượng đĩa cho bản sao. Đừng chạy nó
trên bảng production đang phục vụ như một thói quen.

```sql
VACUUM (VERBOSE) accounts;      -- dọn và in chi tiết
VACUUM ANALYZE accounts;        -- dọn rồi cập nhật thống kê
```

### 4.2 Autovacuum: khi nào tự chạy

Autovacuum bật mặc định (`autovacuum = on`). Process launcher thức dậy theo chu kỳ `autovacuum_naptime`
(mặc định 1 phút), xem bảng nào cần vacuum và giao cho worker (`autovacuum_max_workers` mặc định 3).

Công thức trong tài liệu Postgres 18: một bảng được vacuum khi số tuple đã lỗi thời kể từ lần vacuum trước
vượt

```
vacuum threshold = Minimum(autovacuum_vacuum_max_threshold,
                           autovacuum_vacuum_threshold
                           + autovacuum_vacuum_scale_factor * reltuples)
```

Mặc định: `autovacuum_vacuum_threshold` = 50, `autovacuum_vacuum_scale_factor` = 0.2 (20% bảng),
`autovacuum_vacuum_max_threshold` = 100.000.000 (tham số này mới ở bản 18). Tính tay:

| Số dòng (`reltuples`) | 50 + 0.2 × dòng | Ngưỡng thật (lấy min với 100 triệu) |
|---|---|---|
| 1.000 | 250 | 250 |
| 1.000.000 | 200.050 | 200.050 |
| 1.000.000.000 | 200.000.050 | 100.000.000 |

Bảng một tỉ dòng, trước bản 18, phải tích tới 200 triệu dead tuple mới bị vacuum; bản 18 chặn trần ở 100
triệu. Với bảng lớn ghi nhiều, người ta vẫn hay hạ scale factor riêng cho bảng đó:

```sql
ALTER TABLE accounts SET (autovacuum_vacuum_scale_factor = 0.02);
```

Ngoài ra còn ngưỡng theo số dòng **insert** (`autovacuum_vacuum_insert_threshold`, mặc định 1000, kèm
scale factor riêng), để bảng chỉ insert cũng được vacuum định kỳ (cập nhật visibility map, freeze), và
ngưỡng `ANALYZE` (50 + 10% số dòng).

Theo dõi:

```sql
SELECT relname, n_live_tup, n_dead_tup, n_tup_upd, n_tup_hot_upd,
       last_vacuum, last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC;
```

### 4.3 Bloat và những thứ chặn VACUUM

Khi vacuum không theo kịp, bảng và index đầy dead tuple, phình to: gọi là *bloat*. Scan đọc nhiều page hơn
cho cùng số dòng sống, cache chứa nhiều rác hơn, index sâu và to hơn.

Lý do phổ biến nhất **không** phải autovacuum cấu hình yếu, mà là có thứ **giữ snapshot cũ**. VACUUM
không được dọn tuple mà một transaction nào đó còn có thể nhìn thấy. Những "cái neo" hay gặp:

- Transaction mở rất lâu, kể cả connection đứng ở trạng thái `idle in transaction` (app `BEGIN` rồi quên
  `COMMIT`, hoặc gọi API ngoài khi đang trong transaction).
- Replication slot bị bỏ quên (replica đã chết nhưng slot còn).
- Replica bật `hot_standby_feedback` đang chạy query dài.
- Prepared transaction (`PREPARE TRANSACTION`, two-phase commit) bị bỏ dở.

Đây là bài toán **y hệt** "transaction dài chặn purge, undo phình, history list length tăng" của InnoDB
([chương 16](16-ben-trong-innodb.md)), chỉ khác chỗ rác nằm: InnoDB phình undo tablespace, Postgres phình
chính bảng. Tìm transaction dài:

```sql
SELECT pid, state, now() - xact_start AS tuoi_transaction, query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY xact_start
LIMIT 5;
```

Phòng bằng tham số `idle_in_transaction_session_timeout` (ngắt session đứng idle trong transaction quá
lâu) và `statement_timeout`.

Bloat đã có rồi thì sao? VACUUM thường không làm file nhỏ lại. Muốn thu nhỏ: `VACUUM FULL` hoặc `CLUSTER`
(cả hai khoá bảng hoàn toàn), `REINDEX INDEX CONCURRENTLY` cho index bị phình, hoặc extension bên ngoài
`pg_repack` (viết lại bảng mà gần như không khoá, cùng ý tưởng với gh-ost/pt-osc của MySQL ở
[chương 20](20-thay-doi-schema-migration.md)).

### 4.4 HOT update

Vấn đề: `UPDATE` tạo tuple mới ở ctid mới. Nếu bảng có 5 index thì về nguyên tắc mỗi lần update phải thêm
entry vào **cả 5 index**, kể cả khi chỉ đổi một cột không có index nào. InnoDB không gặp chuyện này vì
secondary index chứa PK chứ không chứa vị trí vật lý.

Postgres giảm chi phí bằng *HOT update* (heap-only tuple). Theo tài liệu, update được làm theo kiểu HOT
khi:

1. Không sửa cột nào được index tham chiếu (trừ *summarizing index*; trong bản chuẩn chỉ có BRIN thuộc
   loại này), **và**
2. Page chứa dòng cũ còn đủ chỗ cho dòng mới.

Khi đó không cần thêm entry index nào: index vẫn trỏ tới tuple cũ, tuple cũ trỏ tiếp tới tuple mới trong
cùng page. Thêm nữa, các bản trung gian của một chuỗi HOT có thể được dọn ngay trong lúc hoạt động bình
thường (kể cả khi `SELECT` đọc page), không phải chờ VACUUM.

Hai cách tăng tỉ lệ HOT:

- **Đừng index cột hay bị update** nếu không thật cần (ví dụ `updated_at`, `view_count`).
- Hạ `fillfactor` của bảng (mặc định 100, tức nhét đầy page) để chừa chỗ trong page:

  ```sql
  ALTER TABLE accounts SET (fillfactor = 90);   -- áp dụng cho page ghi sau này
  ```

Đo tỉ lệ bằng `n_tup_hot_upd / n_tup_upd` trong `pg_stat_user_tables`.

### 4.5 Xid wraparound

Transaction id (xid) của Postgres là số 32 bit, so sánh theo vòng tròn: với mỗi xid, khoảng hai tỉ xid là
"quá khứ", hai tỉ là "tương lai". Một tuple sống quá hai tỉ transaction mà không được xử lý thì bỗng trông
như được tạo "trong tương lai" và trở thành vô hình. Tài liệu gọi đây là mất dữ liệu thảm khốc.

Lời giải là VACUUM *freeze*: đánh dấu tuple đủ cũ là "luôn thuộc quá khứ". Các mốc trong tài liệu 18:

| Mốc | Chuyện gì xảy ra |
|---|---|
| Tuổi `relfrozenxid` của bảng vượt `autovacuum_freeze_max_age` (mặc định 200 triệu) | Autovacuum buộc phải vacuum bảng đó, **kể cả khi autovacuum bị tắt** |
| Vượt `vacuum_failsafe_age` (mặc định 1,6 tỉ) | VACUUM vào chế độ failsafe: bỏ các việc không cần thiết để freeze cho nhanh |
| Còn 40 triệu transaction tới điểm wraparound | Server bắt đầu in `WARNING: database "..." must be vacuumed within ... transactions` |
| Còn dưới 3 triệu | Từ chối cấp xid mới: chỉ transaction chỉ-đọc được bắt đầu, mọi thao tác ghi lỗi, cho tới khi VACUUM xong |

Theo dõi:

```sql
SELECT datname, age(datfrozenxid) FROM pg_database;
```

Tình huống thật hay gặp: một bảng rất lớn, autovacuum chống wraparound chạy hàng giờ (và vì là
anti-wraparound nên không tự nhường lock), đúng lúc một migration `ALTER TABLE` xếp hàng chờ lock, kéo theo
mọi query khác chờ sau nó (cùng kiểu xếp hàng lock ở [chương 20](20-thay-doi-schema-migration.md)). Cái
tương tự cũng xảy ra với *MultiXact id* (dùng khi nhiều transaction cùng khoá một dòng, ví dụ nhiều
`SELECT ... FOR SHARE`), với các mốc cảnh báo giống hệt.

InnoDB không có bài toán này: trx id 6 byte (48 bit), và bản cũ nằm ở undo, được purge dọn đi chứ không
ở lại trong bảng chờ freeze.

## 5. Isolation level

[Chương 14 mục 7](14-isolation-mvcc.md#7-postgresql-repeatable-read-và-serializable) đã chạy đầy đủ
timeline trên cả hai hệ. Ở đây tóm lại và bổ sung phần `READ COMMITTED`.

### 5.1 Mặc định READ COMMITTED

`default_transaction_isolation` của Postgres mặc định là `read committed`, khác MySQL (`REPEATABLE READ`).
Ở Postgres:

- `READ UNCOMMITTED` được chấp nhận về cú pháp nhưng chạy y như `READ COMMITTED`: Postgres không bao giờ
  cho dirty read.
- Mỗi **câu lệnh** chụp snapshot mới, nên hai câu `SELECT` trong cùng transaction có thể thấy dữ liệu khác
  nhau.
- Khi `UPDATE`/`DELETE` gặp dòng đang bị transaction khác sửa, nó chờ. Nếu bên kia commit, Postgres **đánh
  giá lại `WHERE`** trên phiên bản mới nhất của dòng rồi mới ghi (nếu dòng không còn thoả điều kiện thì bỏ
  qua).

Nhờ điểm cuối, câu ghi nguyên tử an toàn ở RC:

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `BEGIN;` | `BEGIN;` | |
| 2 | `UPDATE accounts SET balance = balance - 30 WHERE id = 2;` | | A khoá dòng 2 (300 → 270) |
| 3 | | `UPDATE accounts SET balance = balance - 50 WHERE id = 2;` | B chờ |
| 4 | `COMMIT;` | | B thấy bản mới 270, ghi 220 |
| 5 | | `COMMIT;` | `balance` = 220, đúng |

Nhưng đọc lên app, tính, rồi ghi số cố định (`SET balance = 250`) thì vẫn **lost update** ở RC, giống
MySQL. Cách chống giống hệt [chương 14 mục 9](14-isolation-mvcc.md): câu ghi nguyên tử, `SELECT ... FOR
UPDATE`, optimistic lock bằng cột version, hoặc nâng level.

### 5.2 REPEATABLE READ là snapshot isolation thật

Snapshot chụp một lần ở câu đầu tiên và dùng cho **mọi** câu, cả đọc lẫn ghi. Khi `UPDATE`, `DELETE` hay
`SELECT ... FOR UPDATE` gặp dòng đã bị transaction khác sửa và commit sau snapshot, Postgres không ghi đè
mà báo:

```
ERROR:  could not serialize access due to concurrent update
```

SQLSTATE `40001`. Timeline đầy đủ ở [chương 14 mục 7.1](14-isolation-mvcc.md#71-postgresql-rr-snapshot-isolation-thật-và-lỗi-40001).
Khác biệt lớn với MySQL RR:

| Tình huống | MySQL RR | PostgreSQL RR |
|---|---|---|
| Hai transaction đọc rồi cùng ghi một dòng | Bên sau ghi đè, **lost update lọt** | Bên sau nhận 40001 |
| `SELECT` thường và `UPDATE` trong cùng transaction | Có thể "SELECT không thấy, UPDATE thấy" (UPDATE đọc bản mới nhất) | Mọi câu dùng cùng snapshot |
| Phantom | Chặn với `SELECT` thường, locking read có thể thấy | Không xảy ra |
| Write skew | Lọt | Lọt |

Hệ quả cho code: app dùng RR hoặc Serializable trên Postgres **bắt buộc có vòng retry** bắt 40001 và chạy
lại cả transaction từ đầu.

### 5.3 SERIALIZABLE là SSI

Postgres làm Serializable bằng *Serializable Snapshot Isolation*: chạy như RR, không thêm khoá chặn nào,
nhưng ghi nhận đọc gì bằng *predicate lock* (`SIReadLock` trong `pg_locks`, không chặn ai) và huỷ một
transaction (40001, `could not serialize access due to read/write dependencies among transactions`) khi
phát hiện mẫu phụ thuộc nguy hiểm. Timeline write skew với bảng `doctors` ở
[chương 14 mục 7.2](14-isolation-mvcc.md#72-postgresql-serializable-ssi).

MySQL đi hướng ngược lại: Serializable biến mọi `SELECT` trong transaction thành `SELECT ... FOR SHARE`,
tức **chặn bằng khoá**, xung đột lộ ra dưới dạng chờ khoá và deadlock (lỗi 1213, cũng mang SQLSTATE 40001).

| | MySQL 8.4 Serializable | PostgreSQL 18 Serializable |
|---|---|---|
| Cơ chế | Khoá S cho mọi `SELECT` | Snapshot + theo dõi phụ thuộc (SSI) |
| Người đọc chặn người ghi | Có | Không |
| Khi xung đột | Chờ khoá, có thể deadlock | Một bên bị huỷ lúc ghi hoặc commit |
| Huỷ nhầm | Không (chỉ deadlock thật) | Có thể (false positive) |
| App cần | Retry khi deadlock | Retry khi 40001 |

Trên Postgres, Serializable dùng được thật cho nghiệp vụ khó (đặt chỗ, kiểm ràng buộc trên nhiều dòng) với
điều kiện transaction ngắn, có retry, và khai báo `READ ONLY` cho transaction chỉ đọc.

## 6. Kiểu dữ liệu phong phú

[Chương 3 mục 14](03-kieu-du-lieu.md#14-đối-chiếu-postgresql) đã so các kiểu cơ bản (số, chuỗi, thời
gian, `timestamptz`, `uuid`). Mục này nói về ba nhóm kiểu mà MySQL 8.4 không có tương đương đầy đủ.

### 6.1 jsonb

Postgres có hai kiểu JSON: `json` giữ nguyên văn bản (kể cả khoảng trắng, thứ tự key, key trùng), `jsonb`
lưu dạng nhị phân đã phân tích (bỏ key trùng, không giữ thứ tự key). Tài liệu khuyên dùng `jsonb` trong
hầu hết trường hợp. MySQL chỉ có một kiểu `JSON`, cũng lưu nhị phân.

```sql
SELECT name, attrs->>'color' AS color
FROM products
WHERE attrs @> '{"color": "red"}';       -- @>: "chứa" một khối JSON
```

```
  name   | color
---------+-------
 Ao thun | red
```

Toán tử hay dùng:

| Toán tử | Ý nghĩa | Ví dụ | MySQL 8.4 gần nhất |
|---|---|---|---|
| `->` | Lấy phần tử, trả về `jsonb` | `attrs->'size'` | `attrs->'$.size'` |
| `->>` | Lấy phần tử, trả về `text` | `attrs->>'color'` | `attrs->>'$.color'` |
| `@>` | Vế trái chứa vế phải | `attrs @> '{"wireless": true}'` | `JSON_CONTAINS()` |
| `?` | Có key (ở mức ngoài cùng) | `attrs ? 'wireless'` | `JSON_CONTAINS_PATH()` |

Điểm mạnh thật sự là **index GIN trên cả cột** (mục 7.2): một index phục vụ mọi câu `@>` và `?` trên bất
kỳ key nào. MySQL phải tạo index riêng cho từng đường dẫn (generated column hoặc functional index), hoặc
multi-valued index cho mảng ([chương 11](11-index.md)).

Cạm bẫy: `jsonb` không thay được thiết kế bảng. Dữ liệu có cấu trúc ổn định, cần ràng buộc, cần join thì
vẫn nên là cột thường. `jsonb` hợp với thuộc tính thay đổi theo loại sản phẩm, payload webhook, cấu hình.

### 6.2 Array

Một cột có thể chứa mảng của bất kỳ kiểu nào: `integer[]`, `text[]`...

```sql
SELECT name FROM products WHERE 'thoi-trang' = ANY (tags);    -- có phần tử này
SELECT name FROM products WHERE tags @> '{thoi-trang,nam}';   -- chứa mọi phần tử này
SELECT name, cardinality(tags) FROM products;                 -- số phần tử
```

Kết quả câu đầu: `Ao thun`, `Quan jean`. Câu hai: `Ao thun`. Câu ba: 2, 1, 1. Mảng trong Postgres đánh số
**từ 1**, không phải 0.

Hợp với danh sách nhỏ, đọc cả cụm, không cần ràng buộc từng phần tử (tag, danh sách quyền). Không dùng để
thay bảng nối nhiều-nhiều: mảng không có foreign key tới từng phần tử. MySQL không có kiểu mảng; cách gần
nhất là mảng JSON kèm multi-valued index.

### 6.3 Range type và ràng buộc "không chồng lấn"

*Range type* biểu diễn một khoảng: `int4range`, `int8range`, `numrange`, `daterange`, `tsrange`,
`tstzrange` (và *multirange* tương ứng). Ký hiệu `[` là gồm biên, `)` là không gồm.

Bài toán kinh điển: một phòng không được đặt hai lần cho hai khoảng thời gian chồng nhau. Ở MySQL, bạn
phải tự kiểm trong transaction có khoá (dễ sai khi đồng thời, xem write skew ở
[chương 14](14-isolation-mvcc.md)). Ở Postgres, database tự chặn bằng *exclusion constraint*:

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;     -- cho phép so "=" trên integer trong index GiST

CREATE TABLE bookings (
    room_id integer   NOT NULL,
    during  tstzrange NOT NULL,
    EXCLUDE USING gist (room_id WITH =, during WITH &&)
);

INSERT INTO bookings VALUES (1, '[2026-11-01 14:00+07, 2026-11-03 12:00+07)');
INSERT INTO bookings VALUES (1, '[2026-11-03 12:00+07, 2026-11-05 12:00+07)');  -- được: chỉ chạm biên
INSERT INTO bookings VALUES (1, '[2026-11-02 00:00+07, 2026-11-04 00:00+07)');  -- lỗi
```

Câu thứ ba bị từ chối với lỗi `conflicting key value violates exclusion constraint` (SQLSTATE `23P01`),
vì cùng `room_id` và hai khoảng chồng nhau (`&&`). Câu thứ hai được vì khoảng đầu không gồm biên phải.

PostgreSQL 18 thêm cú pháp chuẩn hơn cho đúng việc này, *temporal constraint*:
`PRIMARY KEY (room_id, during WITHOUT OVERLAPS)` hoặc `UNIQUE (...)`. Theo tài liệu, nó tương đương một
exclusion constraint dùng index GiST; cột không phải range cần extension `btree_gist`, đây là cách dùng
được tài liệu mong đợi.

### 6.4 Vài khác biệt khác đáng nhớ

- `RETURNING`: `INSERT ... RETURNING id`, `UPDATE ... RETURNING *` trả lại dòng vừa ghi trong cùng câu.
  Bản 18 cho phép `RETURNING old.balance, new.balance`. MySQL không có `RETURNING`; phải dùng
  `LAST_INSERT_ID()` hoặc đọc lại.
- Upsert: `INSERT ... ON CONFLICT (cột) DO UPDATE` và `MERGE`, so với `ON DUPLICATE KEY UPDATE` của MySQL
  ([chương 9 mục 13](09-subquery-cte-union.md#13-postgresql-on-conflict-và-upsert-từ-laravel)).
- So sánh chuỗi: collation mặc định của MySQL 8.4 (`utf8mb4_0900_ai_ci`) không phân biệt hoa thường, nên
  `'abc' = 'ABC'` là đúng. Ở Postgres mặc định **phân biệt**; muốn tìm email không phân biệt hoa thường
  thì dùng expression index trên `lower(email)` (mục 7.6) hoặc collation nondeterministic.
- Generated column: Postgres 18 hỗ trợ cột `VIRTUAL` (tính khi đọc) và đặt nó làm **mặc định**; trước bản
  18 chỉ có `STORED`. MySQL có cả hai từ lâu, mặc định cũng là `VIRTUAL`.
- `uuidv7()` có sẵn ở bản 18 để sinh UUID tăng theo thời gian.

## 7. Index phong phú

[Chương 11 mục 13](11-index.md#13-đối-chiếu-postgresql) đã liệt kê. Mục này cho ví dụ chạy được.

### 7.1 Sáu access method

| Loại | Dùng cho | Toán tử điển hình |
|---|---|---|
| B-tree (mặc định) | So sánh, sắp xếp, `=`, `<`, `BETWEEN`, `LIKE 'abc%'` | `=`, `<`, `>` |
| Hash | Chỉ `=` | `=` |
| GIN | Giá trị chứa nhiều phần tử: `jsonb`, mảng, full-text, trigram | `@>`, `?`, `&&`, `@@` |
| GiST | Hình học, range, tìm láng giềng gần nhất, exclusion constraint | `&&`, `<->` |
| SP-GiST | Cấu trúc phân hoạch không cân bằng (quad-tree, trie) | tuỳ opclass |
| BRIN | Bảng rất lớn, giá trị tương quan với thứ tự vật lý | `<`, `=`, `>` |

MySQL 8.4 có B-tree, full-text, spatial (R-tree) và multi-valued index, không có cơ chế tổng quát để thêm
loại index mới như Postgres.

Một bổ sung của bản 18 đáng biết: B-tree hỗ trợ *skip scan*, theo release notes cho phép dùng index nhiều
cột trong nhiều trường hợp hơn, ví dụ khi điều kiện không có cột đầu. MySQL có skip scan từ bản 8.0.13.
Quy tắc leftmost prefix của [chương 11](11-index.md) vẫn là cách thiết kế đúng; skip scan chỉ hiệu quả khi
cột đầu có ít giá trị khác nhau.

### 7.2 GIN

*Generalized Inverted Index*: với mỗi phần tử (key JSON, phần tử mảng, từ), lưu danh sách dòng chứa nó.
Giống mục lục cuối sách.

```sql
CREATE INDEX products_attrs_gin ON products USING gin (attrs);
CREATE INDEX products_tags_gin  ON products USING gin (tags);
```

Opclass mặc định cho `jsonb` (`jsonb_ops`) hỗ trợ `@>`, `?`, `?|`, `?&` và các toán tử jsonpath. Opclass
`jsonb_path_ops` nhỏ hơn và thường nhanh hơn nhưng chỉ hỗ trợ `@>` và jsonpath:

```sql
CREATE INDEX products_attrs_path ON products USING gin (attrs jsonb_path_ops);
```

Cái giá: GIN đọc nhanh nhưng **ghi đắt** (một dòng sinh nhiều entry). Postgres giảm bằng *pending list*
(gom entry mới, chèn hàng loạt sau), đổi lại tìm kiếm phải quét thêm danh sách chờ.

Cạm bẫy: index GIN trên `attrs` **không** giúp `attrs->>'color' = 'red'`. Câu đó so một biểu thức text,
không phải toán tử GIN. Viết lại thành `attrs @> '{"color":"red"}'`, hoặc tạo expression index B-tree
trên `(attrs->>'color')`.

### 7.3 GiST

*Generalized Search Tree* là khung cây cân bằng tổng quát: mỗi node lưu một "vùng bao" (hình chữ nhật bao,
khoảng bao) của mọi thứ bên dưới. Dùng cho:

- Range và exclusion constraint (mục 6.3 tự tạo index GiST).
- Hình học, PostGIS (mục 9.4).
- Tìm k láng giềng gần nhất: `ORDER BY location <-> điểm LIMIT 10` dùng được index.
- Full-text và trigram (thay cho GIN khi bảng ghi nhiều, đọc chấp nhận chậm hơn).

### 7.4 BRIN

*Block Range Index* không lưu từng dòng, chỉ lưu **tóm tắt** (mặc định min và max) cho mỗi dải page liền
nhau (tham số `pages_per_range`, mặc định 128 page). Khi truy vấn, Postgres bỏ qua những dải mà min/max
cho biết chắc không chứa giá trị cần.

```sql
CREATE TABLE events (
    id         bigint GENERATED ALWAYS AS IDENTITY,
    created_at timestamptz NOT NULL DEFAULT now(),
    payload    jsonb
);
CREATE INDEX events_created_brin ON events USING brin (created_at);
```

Với bảng log chỉ insert, `created_at` tăng dần theo vị trí vật lý, nên index BRIN cho bảng hàng trăm GB chỉ
cỡ vài trăm KB tới vài MB, trong khi B-tree có thể hàng GB. Nếu dữ liệu không tương quan với thứ tự vật lý
(cột update lung tung, insert ngẫu nhiên), BRIN gần như vô dụng: mỗi dải đều có min/max trải rộng.

### 7.5 Partial index

Chỉ index những dòng thoả một điều kiện:

```sql
CREATE TABLE orders (
    id         bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id    bigint      NOT NULL,
    status     text        NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX orders_pending ON orders (created_at) WHERE status = 'pending';

-- dùng được index: WHERE của câu suy ra được điều kiện của index
SELECT id FROM orders WHERE status = 'pending' AND created_at < now() - interval '1 day';
```

Nếu 99% đơn đã `done`, index chỉ chứa 1% dòng: nhỏ, ghi rẻ (đơn `done` không phải cập nhật index). Dùng
partial **unique** index để ràng buộc có điều kiện:

```sql
CREATE TABLE subscriptions (user_id bigint NOT NULL, active boolean NOT NULL);
CREATE UNIQUE INDEX one_active_sub ON subscriptions (user_id) WHERE active;
```

Mỗi user tối đa một gói `active`, nhưng bao nhiêu gói cũ cũng được. Đây cũng là cách làm "unique trừ dòng
đã soft delete": `... WHERE deleted_at IS NULL`. MySQL 8.4 không có partial index; cách vòng là generated
column trả `NULL` cho dòng không cần (unique index cho phép nhiều `NULL`).

Cạm bẫy: planner chỉ dùng partial index khi **chứng minh được** từ `WHERE` của câu truy vấn. Với prepared
statement, `WHERE status = $1` thì plan tổng quát không biết `$1` là `'pending'`, có thể không dùng được
index.

### 7.6 Expression index

Index trên kết quả một biểu thức:

```sql
CREATE TABLE users (id bigint PRIMARY KEY, email text NOT NULL);
CREATE UNIQUE INDEX users_email_lower ON users (lower(email));

SELECT id FROM users WHERE lower(email) = lower('An@Example.com');   -- dùng index
```

Câu truy vấn phải viết **đúng biểu thức** của index. MySQL có tương đương từ 8.0.13 (functional key part,
cú pháp có cặp ngoặc kép: `INDEX ((lower(email)))`). Hàm dùng trong index của Postgres phải được khai báo
`IMMUTABLE` (cùng đầu vào luôn cùng kết quả).

### 7.7 INCLUDE: covering index không làm to key

```sql
CREATE INDEX orders_user_created ON orders (user_id, created_at) INCLUDE (status);

SELECT created_at, status FROM orders WHERE user_id = 42 ORDER BY created_at DESC LIMIT 20;
```

`status` chỉ nằm ở lá, không phải một phần key: không ảnh hưởng thứ tự, không tham gia unique, nhưng đủ để
câu trên chạy *index-only scan*. Theo tài liệu, hiện B-tree, GiST, SP-GiST hỗ trợ `INCLUDE`. MySQL không
có `INCLUDE`; muốn covering phải thêm cột vào key.

Cạm bẫy riêng của Postgres: index-only scan vẫn phải ghé heap cho những page chưa được đánh "all-visible"
trong visibility map. Bảng update nhiều mà vacuum chậm thì `EXPLAIN ANALYZE` hiện `Heap Fetches` lớn, và
index-only scan chẳng còn "only". Ở InnoDB, secondary index cũng có chuyện tương tự (kiểm tra phiên bản),
nhưng cơ chế khác.

## 8. DDL trong transaction và CREATE INDEX CONCURRENTLY

### 8.1 DDL rollback được

MySQL: mọi DDL gây *implicit commit*; MySQL 8.0 trở lên có *atomic DDL* (một câu DDL hoặc xong hẳn hoặc
không làm gì), nhưng **không gộp nhiều câu DDL vào một transaction** được
([chương 4](04-ddl-constraint.md), [chương 13](13-transaction-acid.md)).

Postgres: phần lớn DDL là transactional.

```sql
BEGIN;
ALTER TABLE accounts ADD COLUMN currency text NOT NULL DEFAULT 'VND';
CREATE INDEX accounts_owner ON accounts (owner);
UPDATE accounts SET currency = 'USD' WHERE id = 2;
-- phát hiện sai sót
ROLLBACK;
```

Sau `ROLLBACK`, bảng không có cột `currency`, không có index `accounts_owner`: như chưa có gì xảy ra. Một
migration nhiều bước lỗi giữa chừng không để lại schema dở dang. Laravel trên Postgres mặc định bọc mỗi
migration trong transaction vì lý do này.

Ngoại lệ: một số lệnh **không chạy được trong transaction block**, theo tài liệu từng lệnh: `CREATE
DATABASE`, `DROP DATABASE`, `CREATE TABLESPACE`, `VACUUM`, `CREATE INDEX CONCURRENTLY`, `DROP INDEX
CONCURRENTLY`, `REINDEX ... CONCURRENTLY`, `ALTER SYSTEM`. Và sequence không rollback: `nextval()` đã
cấp số thì không trả lại, giống `AUTO_INCREMENT` của MySQL để lại lỗ hổng.

Cạm bẫy: DDL trong transaction **giữ lock tới khi commit**. `ALTER TABLE` lấy `ACCESS EXCLUSIVE`; nếu
migration làm `ALTER` rồi chạy thêm một `UPDATE` hàng triệu dòng trong cùng transaction, bảng bị khoá hoàn
toàn suốt thời gian đó. Lock xếp hàng: `ALTER` chờ một transaction dài, mọi query sau phải chờ `ALTER`
([chương 20 mục 9.1](20-thay-doi-schema-migration.md#91-mô-hình-lock-khác-cùng-một-cái-bẫy)). Luôn đặt
`SET lock_timeout = '5s';` trước DDL trên production.

### 8.2 CREATE INDEX CONCURRENTLY

`CREATE INDEX` thường cho đọc nhưng **chặn ghi** suốt thời gian dựng. `CONCURRENTLY` không chặn ghi:

```sql
CREATE INDEX CONCURRENTLY orders_user_status ON orders (user_id, status);
```

Cái giá và cạm bẫy (chi tiết ở [chương 20 mục 9.2](20-thay-doi-schema-migration.md#92-create-index-concurrently)):

- Quét bảng hai lần và chờ các transaction đang dùng bảng kết thúc: lâu hơn đáng kể.
- Không chạy trong transaction block: migration phải tắt transaction.
- Lỗi giữa chừng để lại index `INVALID`, không dùng để đọc nhưng **vẫn tốn chi phí khi ghi**. Tìm bằng
  `\d orders` (dòng ghi `INVALID`) hoặc `pg_index.indisvalid = false`, rồi `DROP INDEX` và tạo lại.

So với MySQL: InnoDB tạo secondary index online (`ALGORITHM=INPLACE, LOCK=NONE`) là mặc định, không cần
từ khoá riêng, nhưng không có cách gom vào transaction để rollback.

## 9. Extension

### 9.1 CREATE EXTENSION

Extension là gói mở rộng cài vào một database: thêm kiểu dữ liệu, hàm, toán tử, loại index, thậm chí cả
hook vào planner. Đây là điểm khác biệt lớn nhất về hệ sinh thái giữa hai hệ.

```sql
SELECT name, default_version, installed_version
FROM pg_available_extensions ORDER BY name;      -- extension có sẵn trên server

CREATE EXTENSION pg_trgm;                          -- cài vào database hiện tại
```

Liệt kê extension đã cài bằng lệnh psql `\dx` (gõ riêng một dòng: lệnh `\` của psql coi phần còn lại
của dòng là tham số, nên đừng viết comment `--` phía sau).

Hai nhóm:

- *contrib*: đi kèm bản phân phối Postgres (`pg_trgm`, `pg_stat_statements`, `btree_gist`, `pgcrypto`,
  `citext`, `hstore`, `postgres_fdw`, `pageinspect`...). Image Docker `postgres` có sẵn.
- Bên ngoài: phải cài gói riêng vào server rồi mới `CREATE EXTENSION` được (PostGIS, pgvector,
  TimescaleDB, Citus...). Trên dịch vụ cloud (RDS, Cloud SQL...), chỉ dùng được danh sách extension nhà
  cung cấp cho phép; kiểm trước khi chọn kiến trúc dựa vào một extension.

MySQL có *plugin* và *component* (ví dụ plugin xác thực, validate_password), nhưng không có hệ sinh thái
thêm kiểu dữ liệu và loại index tương đương.

### 9.2 pg_stat_statements

Thống kê mọi câu lệnh đã chạy, đã chuẩn hoá (hằng số thay bằng `$1`): số lần gọi, tổng thời gian, số dòng,
cache hit. Tương đương bảng digest trong `performance_schema` của MySQL
([chương 12](12-explain-toi-uu-query.md)). Cần nạp lúc khởi động, sửa `postgresql.conf`:

```
shared_preload_libraries = 'pg_stat_statements'
```

Restart server rồi:

```sql
CREATE EXTENSION pg_stat_statements;

SELECT calls, round(total_exec_time) AS tong_ms, round(mean_exec_time, 2) AS tb_ms, query
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

Xếp theo **tổng** thời gian chứ không phải trung bình: câu 2ms gọi một triệu lần tốn hơn câu 5 giây gọi
mười lần.

### 9.3 pg_trgm

Tách chuỗi thành các *trigram* (bộ ba ký tự liên tiếp) để đo độ giống nhau và, quan trọng hơn, để index
được `LIKE '%abc%'`, thứ B-tree không làm được:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX products_name_trgm ON products USING gin (name gin_trgm_ops);

SELECT name FROM products WHERE name ILIKE '%jea%';        -- dùng được index
SELECT name, similarity(name, 'quan jeen') FROM products   -- tìm gần đúng, chịu lỗi gõ
WHERE name % 'quan jeen' ORDER BY 2 DESC;
```

Chuỗi tìm quá ngắn (dưới 3 ký tự) thì không tách được trigram có ích, index không giúp. MySQL không có
tương đương; cách gần nhất là full-text index với parser ngram.

### 9.4 PostGIS

Extension bên ngoài, biến Postgres thành database không gian địa lý đầy đủ: kiểu `geometry`, `geography`,
hàng trăm hàm (`ST_DWithin`, `ST_Contains`, `ST_Distance`...), index GiST. Ví dụ (cần image có PostGIS,
như `postgis/postgis`; image `postgres` gốc không có):

```sql
CREATE EXTENSION postgis;
CREATE TABLE stores (id int PRIMARY KEY, name text, location geography(Point, 4326));
CREATE INDEX stores_loc ON stores USING gist (location);

-- cửa hàng trong bán kính 2 km (geography tính theo mét)
SELECT name FROM stores
WHERE ST_DWithin(location, ST_MakePoint(105.85, 21.03)::geography, 2000);
```

MySQL 8.4 có kiểu spatial, SRID và index R-tree, đủ cho bài toán "điểm gần đây" cơ bản; PostGIS rộng hơn
nhiều về hàm, định dạng và công cụ.

### 9.5 pgvector

Extension bên ngoài thêm kiểu `vector` để lưu embedding và tìm láng giềng gần nhất, nền tảng cho tìm kiếm
ngữ nghĩa, RAG:

```sql
CREATE EXTENSION vector;
CREATE TABLE docs (id bigint PRIMARY KEY, content text, embedding vector(3));
INSERT INTO docs VALUES (1, 'a', '[1,0,0]'), (2, 'b', '[0.9,0.1,0]'), (3, 'c', '[0,1,0]');

SELECT id FROM docs ORDER BY embedding <=> '[1,0,0]' LIMIT 2;   -- <=> khoảng cách cosine
CREATE INDEX docs_emb ON docs USING hnsw (embedding vector_cosine_ops);
```

Kết quả: 1 rồi 2. Toán tử `<->` là khoảng cách L2, `<=>` cosine, `<#>` tích vô hướng âm. Index HNSW và
IVFFlat là index *xấp xỉ*: nhanh nhưng có thể bỏ sót vài kết quả gần nhất thật. Lợi thế lớn: vector nằm
cạnh dữ liệu nghiệp vụ, lọc bằng `WHERE` và join trong cùng câu, cùng transaction. MySQL 8.4 không có kiểu
vector (kiểu `VECTOR` xuất hiện ở dòng MySQL 9.x, không thuộc bản LTS 8.4).

## 10. PgBouncer

### 10.1 Vì sao cần

Mục 2.4: connection Postgres là process, đắt. App PHP-FPM 50 worker × 20 server = 1000 connection, phần
lớn thời gian `idle`. PgBouncer đứng giữa, nhận hàng nghìn connection từ client nhưng chỉ mở vài chục
connection thật tới Postgres. Theo tài liệu PgBouncer: cổng mặc định 6432, `max_client_conn` mặc định 100,
`default_pool_size` (connection server tối đa cho mỗi cặp user/database) mặc định 20.

### 10.2 Ba chế độ pool

| `pool_mode` | Connection server trả về pool khi | Ghi chú |
|---|---|---|
| `session` (mặc định) | Client ngắt kết nối | Tương thích hoàn toàn; chỉ giảm chi phí mở connection, không giảm số connection đang giữ |
| `transaction` | Transaction kết thúc | Phổ biến nhất; một client giữ connection server chỉ trong lúc có transaction |
| `statement` | Mỗi câu lệnh xong | Cấm transaction nhiều câu |

Ở chế độ `transaction`, hai transaction liên tiếp của cùng một client có thể chạy trên **hai connection
server khác nhau**. Mọi thứ gắn với *session* đều hỏng: `SET` (không phải `SET LOCAL`), advisory lock cấp
session, `LISTEN`, cursor `WITH HOLD`, bảng tạm giữ qua transaction, lệnh SQL `PREPARE`
([chương 19 mục 3.6](19-database-tu-ung-dung.md#36-proxy-pool-cho-postgresql-pgbouncer)).

### 10.3 Cạm bẫy prepared statement

Driver thường dùng *prepared statement có tên* ở mức giao thức: gửi `Parse` (đặt tên, ví dụ `S_1`) một lần,
sau đó chỉ gửi `Bind`/`Execute` với tên đó. Statement này sống trong **backend** đã nhận `Parse`.

| Bước | Client | PgBouncer (transaction mode) | Kết quả |
|---|---|---|---|
| 1 | Transaction 1: `Parse S_1`, chạy | Gán connection server X | `S_1` tồn tại trên X |
| 2 | Kết thúc transaction 1 | Trả X về pool | |
| 3 | Transaction 2: chạy lại `S_1` (không `Parse` lại) | Gán connection server Y | `ERROR: prepared statement "S_1" does not exist` |
| 4 | Client khác, trên X, `Parse S_1` câu khác | | `ERROR: prepared statement "S_1" already exists` |

Cách xử lý:

- PgBouncer từ bản 1.21 có `max_prepared_statements`: khi khác 0, PgBouncer theo dõi prepared statement ở
  mức giao thức của client và bảo đảm nó có mặt trên connection server đang được gán (tự chuẩn bị lại khi
  cần). Từ bản 1.24.0 mặc định là 200; bản 1.21 đến 1.23 mặc định 0 (tắt), nên kiểm cấu hình của bạn. Cơ chế
  này **không** áp dụng cho lệnh SQL `PREPARE`/`EXECUTE`.
- Hoặc tắt prepared statement phía server trong driver: PHP PDO đặt `PDO::ATTR_EMULATE_PREPARES => true`
  (PDO tự ghép tham số, an toàn vì vẫn escape đúng); JDBC đặt `prepareThreshold=0`; Go pgx chọn
  `default_query_exec_mode` không cache statement (ví dụ `simple_protocol`).

So với MySQL: ProxySQL có multiplexing tương tự và cũng phải xử lý chuyện trạng thái session. Theo tài
liệu ProxySQL, nó tắt multiplexing cho connection khi gặp thứ gắn với session: transaction đang mở, biến
`@...`, bảng tạm, `LOCK TABLES`, `GET_LOCK()`, lệnh SQL `PREPARE`. Prepared statement qua binary protocol
(thứ PDO dùng khi tắt emulate) thì ProxySQL tự quản lý, không làm tắt multiplexing.

### 10.4 Những điều khác cần nhớ

- Đặt thiết lập cần cho transaction bằng `SET LOCAL` trong chính transaction.
- `statement_timeout`, `search_path` nên đặt ở cấp role hoặc database (`ALTER ROLE app SET
  statement_timeout = '5s'`), không đặt bằng `SET` lúc mở connection.
- Pool của app (Java HikariCP, Go `database/sql`) **cộng** với PgBouncer: tổng connection tới Postgres là
  `default_pool_size` × số cặp user/database × số instance PgBouncer.
- Postgres 18 vẫn chưa có connection pool tích hợp trong server; PgBouncer (hoặc Pgpool-II, Odyssey,
  PgCat, RDS Proxy) là thành phần chạy riêng.

## 11. Bảng so sánh tổng MySQL 8.4 và PostgreSQL 18

| Chủ đề | MySQL 8.4 LTS | PostgreSQL 18 |
|---|---|---|
| Giấy phép | GPL hoặc thương mại (Oracle) | PostgreSQL License (kiểu BSD), cộng đồng phát triển |
| Mô hình xử lý | Một process, mỗi connection một thread | Mỗi connection một process (backend) |
| `max_connections` mặc định | 151 | 100 |
| Cache dữ liệu | Buffer pool (InnoDB), thường cho phần lớn RAM | `shared_buffers` (khởi điểm 25% RAM) + cache OS |
| Storage engine | Cắm được nhiều engine, thực tế InnoDB | Một kiểu lưu chuẩn (heap); có Table Access Method API |
| Tổ chức bảng | Clustered index theo PK | Heap, index trỏ ctid |
| MVCC | Undo log, purge | Tuple cũ trong bảng, VACUUM |
| Rủi ro vận hành riêng | Undo phình, history list length | Bloat, xid wraparound |
| Isolation mặc định | `REPEATABLE READ` | `READ COMMITTED` |
| RR | Consistent read + locking read đọc bản mới nhất; lost update lọt | Snapshot isolation; lỗi 40001 |
| Serializable | Khoá S cho `SELECT` | SSI |
| DDL | Implicit commit; atomic DDL từng câu; online/instant DDL | Phần lớn DDL transactional |
| Tạo index không chặn ghi | Online DDL (mặc định cho secondary index) | `CREATE INDEX CONCURRENTLY` |
| Loại index | B-tree, full-text, spatial, multi-valued | B-tree, Hash, GIN, GiST, SP-GiST, BRIN, + extension |
| Partial index | Không | Có |
| Expression index | Có (8.0.13+) | Có |
| Covering `INCLUDE` | Không | Có (B-tree, GiST, SP-GiST) |
| JSON | `JSON` nhị phân, index theo đường dẫn | `json`, `jsonb`; GIN trên cả cột |
| Mảng, range, exclusion constraint | Không | Có |
| `RETURNING` | Không | Có |
| Upsert | `ON DUPLICATE KEY UPDATE` | `ON CONFLICT`, `MERGE` |
| `CHECK` | Có (thực thi từ 8.0.16) | Có |
| So sánh chuỗi mặc định | Không phân biệt hoa thường (`utf8mb4_0900_ai_ci`) | Phân biệt |
| Database và schema | Là một | Schema là tầng trong database |
| Hint cho optimizer | Có | Không có trong bản chuẩn |
| Thống kê câu lệnh | `performance_schema`, `sys` | `pg_stat_statements` |
| Log | Redo (InnoDB) + binlog (server) | Một WAL |
| Replication | Binlog (row-based), Group Replication / InnoDB Cluster | Streaming (vật lý) và logical replication |
| Mở rộng | Plugin, component | Extension (PostGIS, pgvector, TimescaleDB, Citus...) |
| Connection pool ngoài | ProxySQL, MySQL Router (định tuyến) | PgBouncer, Pgpool-II |

## 12. Khi nào chọn cái nào

Cả hai đều là database quan hệ trưởng thành, ACID, chạy được hệ thống rất lớn. Với đa số ứng dụng web
CRUD, chọn hệ nào cũng ổn, và **hệ đội bạn vận hành giỏi hơn** thường là câu trả lời đúng. Những tín hiệu
nghiêng về một bên:

**Nghiêng về PostgreSQL khi:**

- Dữ liệu và truy vấn phong phú: JSON có truy vấn linh hoạt (`jsonb` + GIN), mảng, khoảng thời gian có ràng
  buộc không chồng lấn, full-text tiếng Anh, tìm gần đúng (`pg_trgm`).
- Cần dữ liệu không gian địa lý nghiêm túc (PostGIS) hoặc tìm kiếm vector cạnh dữ liệu nghiệp vụ
  (pgvector).
- Cần ràng buộc mạnh trong database: partial unique index, exclusion constraint, Serializable dùng được
  thật.
- Migration phức tạp muốn rollback được (DDL transactional).
- Truy vấn phân tích nặng: planner có merge join, nhiều chiến lược hơn, parallel query.

**Nghiêng về MySQL khi:**

- Hệ sinh thái và đội ngũ sẵn có: PHP/Laravel, WordPress, nhiều công cụ quen thuộc (gh-ost, pt-tools,
  Vitess cho sharding).
- Tải OLTP đơn giản, đọc theo primary key rất nhiều: clustered index cho dòng nằm ngay trên lá PK.
- Ứng dụng nhiều connection ngắn mà chưa muốn thêm tầng pool: thread rẻ hơn process.
- Bảng update rất nhiều trên cột có index: InnoDB update tại chỗ, không có bloat và không lo wraparound
  (đổi lại là undo và purge).
- Cần replication nhiều tầng quen thuộc, nhiều kinh nghiệm vận hành sẵn có trong đội.

**Những thứ đừng dùng làm lý do:**

- "Postgres chuẩn SQL hơn nên luôn tốt hơn" hay "MySQL nhanh hơn": benchmark phụ thuộc tải, schema, cấu
  hình; hãy đo với tải của chính bạn.
- "Dùng ORM nên không quan trọng": ORM che cú pháp, không che isolation mặc định, cơ chế lock, bloat, hay
  hành vi so sánh chuỗi. Chuyển hệ giữa chừng luôn lộ ra những khác biệt này.

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Chuyển từ MySQL sang, giả định isolation vẫn là RR | Mặc định Postgres là RC: hai câu `SELECT` trong transaction có thể thấy dữ liệu khác nhau | Đặt level rõ ràng cho transaction cần nhất quán |
| Dùng RR/Serializable mà không có retry | 40001 là hành vi bình thường | Bắt 40001, chạy lại cả transaction |
| Tắt autovacuum vì "nó tốn I/O" | Bloat, thống kê cũ, tới lúc wraparound thì buộc vacuum khẩn cấp | Giữ bật, chỉnh ngưỡng theo bảng |
| Để connection `idle in transaction` | Giữ snapshot, VACUUM không dọn được, bloat | `idle_in_transaction_session_timeout`, không gọi API ngoài trong transaction |
| Quên replication slot của replica đã bỏ | Giữ WAL và chặn dọn dẹp, đầy đĩa | Giám sát `pg_replication_slots`, xoá slot không dùng |
| Chạy `VACUUM FULL` trên bảng production | Khoá `ACCESS EXCLUSIVE` suốt thời gian chạy | `pg_repack`, hoặc chấp nhận bloat và dùng lại chỗ trống |
| Index cột `updated_at` hay đổi | Mất HOT update, mọi update ghi vào mọi index | Chỉ index khi thật cần |
| Đặt `work_mem` rất lớn toàn cục | Nhân theo số thao tác × số connection | Tăng theo session/role cho query báo cáo |
| Hàng nghìn connection thẳng vào Postgres | Mỗi connection là một process | PgBouncer chế độ `transaction` |
| Bật PgBouncer `transaction` mà driver dùng named prepared statement | "prepared statement does not exist/already exists" | `max_prepared_statements`, hoặc tắt server-side prepare |
| Dùng `SET` (session) sau PgBouncer | Thiết lập rơi sang client khác hoặc mất | `SET LOCAL` hoặc `ALTER ROLE ... SET` |
| `CREATE INDEX CONCURRENTLY` lỗi rồi bỏ đó | Index `INVALID` vẫn tốn chi phí ghi | Kiểm `indisvalid`, drop và tạo lại |
| Index GIN trên `jsonb` rồi viết `attrs->>'k' = 'v'` | Câu không dùng toán tử GIN | Viết `attrs @> '{"k":"v"}'` |
| So email như MySQL | Postgres phân biệt hoa thường | `lower()` + expression index, hoặc collation phù hợp |
| DDL dài trong transaction cùng `UPDATE` lớn | Giữ `ACCESS EXCLUSIVE` tới khi commit | Tách bước, đặt `lock_timeout` |

## Tóm tắt chương

- Postgres: postmaster fork một backend process cho mỗi connection; `shared_buffers` (mặc định 128MB,
  khởi điểm 25% RAM) cộng cache OS. Connection đắt, cần PgBouncer ở quy mô lớn. Bản 18 có async I/O
  (`io_method`, mặc định `worker`).
- MVCC trong bảng: `UPDATE` ghi tuple mới, tuple cũ mang `xmax` nằm lại heap; không có undo log; rollback
  gần như tức thì.
- VACUUM dọn dead tuple, cập nhật visibility map, freeze; autovacuum chạy khi dead tuple vượt
  `min(100 triệu, 50 + 20% số dòng)` theo mặc định. Transaction dài, replication slot bỏ quên gây bloat.
- HOT update tránh sửa index khi không đổi cột có index và page còn chỗ; hạ `fillfactor` giúp HOT.
- Xid 32 bit phải freeze; mặc định autovacuum chống wraparound ở tuổi 200 triệu; còn dưới 3 triệu thì
  server từ chối ghi.
- Mặc định `READ COMMITTED`; RR là snapshot isolation (40001 thay cho lost update); Serializable là SSI.
- `jsonb`, array, range + exclusion constraint (bản 18 có `WITHOUT OVERLAPS`); index GIN, GiST, BRIN,
  partial, expression, `INCLUDE`.
- DDL phần lớn transactional; `CREATE INDEX CONCURRENTLY` không chặn ghi nhưng không chạy trong
  transaction và có thể để lại index `INVALID`.
- Extension: `pg_stat_statements` (cần `shared_preload_libraries`), `pg_trgm`, PostGIS, pgvector.
- PgBouncer: `session`, `transaction`, `statement`; ở `transaction` mọi trạng thái session hỏng, named
  prepared statement cần `max_prepared_statements` hoặc tắt ở driver.

## Câu hỏi tự kiểm tra

1. Khi client kết nối tới Postgres, những process nào tham gia? Vì sao điều này làm connection Postgres
   đắt hơn MySQL?
2. Vì sao tài liệu Postgres không khuyên để `shared_buffers` chiếm phần lớn RAM như buffer pool của InnoDB?
3. Sau `UPDATE accounts SET balance = 450 WHERE id = 1`, `ctid`, `xmin`, `xmax` của bản cũ và bản mới thay
   đổi thế nào?
4. So sánh chi phí `ROLLBACK` một transaction sửa 10 triệu dòng trên InnoDB và trên Postgres. Vì sao khác?
5. `VACUUM` và `VACUUM FULL` khác nhau ở những điểm nào (lock, dung lượng trả về OS)?
6. Bảng 10 triệu dòng, cấu hình mặc định: cần bao nhiêu dead tuple để autovacuum vacuum bảng đó?
7. Nêu hai điều kiện của HOT update. Vì sao index cột `updated_at` có thể làm hiệu năng update giảm?
8. Xid wraparound là gì? Server phản ứng thế nào khi còn 40 triệu, và khi còn dưới 3 triệu transaction?
9. Cùng kịch bản lost update, MySQL RR và Postgres RR cho kết quả khác nhau thế nào?
10. SSI của Postgres và Serializable của MySQL khác nhau về cách phát hiện xung đột ra sao?
11. Vì sao index GIN trên cột `jsonb` không giúp câu `WHERE attrs->>'color' = 'red'`?
12. BRIN hợp với dữ liệu nào và vô dụng với dữ liệu nào?
13. Viết partial unique index bảo đảm mỗi user chỉ có một địa chỉ mặc định. MySQL làm việc này thế nào?
14. Lệnh nào không chạy được trong transaction block? Điều đó ảnh hưởng gì tới migration?
15. Ở PgBouncer chế độ `transaction`, vì sao `SET search_path` và named prepared statement gây lỗi?

## Bài tập

1. **Nhìn MVCC tận mắt.** Trên bảng `accounts`, ghi lại `ctid`, `xmin`, `xmax` trước và sau ba lần
   `UPDATE` cùng một dòng. Mở session B với `BEGIN ISOLATION LEVEL REPEATABLE READ; SELECT * FROM
   accounts;` giữ nguyên, rồi ở session A chạy `VACUUM (VERBOSE) accounts;`. Ghi lại số dead tuple không
   xoá được và giải thích; commit B rồi vacuum lại.
2. **Đo HOT.** Tạo bảng 100.000 dòng có cột `counter integer`. Chạy update `counter` cho mọi dòng, ghi
   `n_tup_upd` và `n_tup_hot_upd`. Tạo index trên `counter`, lặp lại, so sánh. Thử thêm `fillfactor = 80`.
3. **Autovacuum.** Tính tay ngưỡng vacuum cho bảng 50.000 dòng, rồi xoá đủ số dòng vượt ngưỡng và theo dõi
   `last_autovacuum` trong `pg_stat_user_tables`. Giải thích thời gian chờ.
4. **Đặt phòng.** Dùng exclusion constraint (hoặc `WITHOUT OVERLAPS` của bản 18), viết bảng đặt phòng và
   ba câu `INSERT` chứng minh: chồng lấn bị chặn, chạm biên được, khác phòng được. Mô tả cách bạn sẽ làm
   bài toán này trên MySQL 8.4 và chỗ dễ sai khi đồng thời.
5. **Index cho sản phẩm.** Với bảng `products`, sinh 200.000 dòng. So sánh `EXPLAIN ANALYZE` của truy vấn
   lọc theo `attrs @> ...`, `tags @> ...`, `name ILIKE '%...%'` trước và sau khi thêm index phù hợp. Ghi lại
   kích thước index bằng `pg_relation_size`.
6. **Migration rollback.** Viết một migration ba bước (thêm cột, backfill, thêm `NOT NULL`) trong một
   transaction, cố ý làm bước ba lỗi, chứng minh schema trở lại như cũ. Làm lại trên MySQL 8.4 và mô tả
   trạng thái schema sau lỗi.
7. **PgBouncer.** Chạy PgBouncer (Docker) trước Postgres ở chế độ `transaction`, đặt
   `max_prepared_statements = 0`. Viết một script PHP PDO dùng prepared statement thật
   (`ATTR_EMULATE_PREPARES = false`) chạy nhiều transaction song song, quan sát lỗi. Sau đó sửa bằng hai
   cách và so sánh.
8. **Chọn database.** Viết một trang lập luận chọn MySQL hay Postgres cho: (a) shop Laravel 10.000 đơn
   mỗi ngày; (b) app giao đồ ăn cần tìm cửa hàng trong bán kính; (c) hệ thống log 1 tỉ dòng mỗi tháng chỉ
   insert. Mỗi lập luận dựa trên ít nhất hai khác biệt trong bảng mục 11.

## Đọc thêm

- PostgreSQL 18: [Release notes](https://www.postgresql.org/docs/18/release-18.html),
  [Resource Consumption](https://www.postgresql.org/docs/18/runtime-config-resource.html),
  [Connection establishment](https://www.postgresql.org/docs/18/connect-estab.html).
- MVCC và vacuum: [Concurrency Control](https://www.postgresql.org/docs/18/mvcc.html),
  [Transaction Isolation](https://www.postgresql.org/docs/18/transaction-iso.html),
  [Routine Vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html),
  [Automatic Vacuuming](https://www.postgresql.org/docs/18/runtime-config-vacuum.html),
  [Heap-Only Tuples](https://www.postgresql.org/docs/18/storage-hot.html).
- Kiểu và index: [JSON Types](https://www.postgresql.org/docs/18/datatype-json.html),
  [Arrays](https://www.postgresql.org/docs/18/arrays.html),
  [Range Types](https://www.postgresql.org/docs/18/rangetypes.html),
  [Index Types](https://www.postgresql.org/docs/18/indexes-types.html),
  [Partial Indexes](https://www.postgresql.org/docs/18/indexes-partial.html),
  [Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/18/indexes-index-only-scans.html),
  [BRIN](https://www.postgresql.org/docs/18/brin.html),
  [CREATE TABLE](https://www.postgresql.org/docs/18/sql-createtable.html),
  [CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html).
- Extension: [pg_stat_statements](https://www.postgresql.org/docs/18/pgstatstatements.html),
  [pg_trgm](https://www.postgresql.org/docs/18/pgtrgm.html),
  [btree_gist](https://www.postgresql.org/docs/18/btree-gist.html),
  [PostGIS](https://postgis.net/documentation/),
  [pgvector](https://github.com/pgvector/pgvector).
- PgBouncer: [Configuration](https://www.pgbouncer.org/config.html),
  [Features](https://www.pgbouncer.org/features.html).
- Các đoạn đối chiếu ngắn trong giáo trình: [chương 3 mục 14](03-kieu-du-lieu.md#14-đối-chiếu-postgresql),
  [chương 11 mục 13](11-index.md#13-đối-chiếu-postgresql),
  [chương 12 mục 13](12-explain-toi-uu-query.md#13-đối-chiếu-postgresql),
  [chương 13 mục 12](13-transaction-acid.md#12-đối-chiếu-mysql-và-postgresql),
  [chương 14 mục 7](14-isolation-mvcc.md#7-postgresql-repeatable-read-và-serializable),
  [chương 15 mục 12](15-lock-deadlock.md#12-đối-chiếu-postgresql),
  [chương 16 mục 11](16-ben-trong-innodb.md#11-đối-chiếu-postgresql),
  [chương 17 mục 11](17-view-procedure-trigger.md#11-đối-chiếu-postgresql),
  [chương 19 mục 3.6](19-database-tu-ung-dung.md#36-proxy-pool-cho-postgresql-pgbouncer),
  [chương 20 mục 9](20-thay-doi-schema-migration.md#9-đối-chiếu-postgresql).
- Martin Kleppmann, [Hermitage](https://github.com/ept/hermitage): kiểm thử isolation trên nhiều database.
