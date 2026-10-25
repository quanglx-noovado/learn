# Chương 23. Partitioning, sharding và mở rộng

> [← Mục lục](README.md) · [← Chương 22: Replication và high availability](22-replication-ha.md) · [Chương 24: Vận hành và giám sát →](24-van-hanh-monitoring.md)

**Bạn sẽ học được:**

- Khi database quá tải thì nên thử những gì, theo thứ tự nào, và vì sao sharding nằm ở cuối danh sách.
- Phân biệt scale dọc (máy to hơn) và scale ngang (nhiều máy hơn).
- Partitioning trong MySQL 8.4: `RANGE`, `RANGE COLUMNS`, `LIST`, `HASH`, `KEY`; partition pruning
  và cách đọc nó trong `EXPLAIN`; các giới hạn quan trọng (unique key phải chứa cột partition, không
  có foreign key); dùng `DROP PARTITION` để xoá dữ liệu cũ trong chớp mắt.
- Archiving: chuyển dữ liệu cũ ra khỏi bảng nóng.
- Sharding: shard key, định tuyến, truy vấn và transaction xuyên shard, ID toàn cục (Snowflake,
  UUIDv7), resharding.
- Hai công cụ có sẵn: Vitess (MySQL) và Citus (PostgreSQL).
- Notion và Figma đã shard Postgres ra sao, theo chính bài blog của họ.

**Cần biết trước:** [Chương 11](11-index.md) (index, B+Tree), [Chương 12](12-explain-toi-uu-query.md)
(`EXPLAIN`), [Chương 13](13-transaction-acid.md) (transaction),
[Chương 20](20-thay-doi-schema-migration.md) (đổi schema trên bảng lớn),
[Chương 22](22-replication-ha.md) (replica, replication lag).

## 1. Database quá tải: làm gì trước?

### 1.1 "Quá tải" nghĩa là gì

Một database được gọi là quá tải khi nó không còn đáp ứng kịp: truy vấn chậm dần, CPU luôn gần 100%,
đĩa đọc ghi hết công suất (IOPS chạm trần), số kết nối chạm `max_connections`, hoặc bảng lớn tới mức
backup, `ALTER TABLE`, khôi phục đều mất hàng giờ.

Trước khi chọn giải pháp, phải **đo** để biết đang thiếu cái gì. Ba câu hỏi:

1. Tải chủ yếu là **đọc** hay **ghi**?
2. Có phải vài truy vấn cụ thể đang ăn phần lớn tài nguyên không? (slow query log,
   `performance_schema`, xem [chương 12](12-explain-toi-uu-query.md) và chương 24)
3. Vấn đề là **lượng dữ liệu** (bảng quá to) hay **lượng truy vấn** (quá nhiều request mỗi giây)?

Mỗi câu trả lời dẫn tới giải pháp khác nhau. Thêm read replica không giúp gì nếu nút thắt là ghi.
Sharding không giúp gì nếu nút thắt là một truy vấn thiếu index.

### 1.2 Thang bậc nên thử

Thứ tự dưới đây xếp theo **chi phí và độ phức tạp tăng dần**. Bậc sau thường đắt hơn bậc trước nhiều
lần, và khó quay lại hơn.

| Bậc | Giải pháp | Giúp được | Cái giá |
|---|---|---|---|
| 1 | Tối ưu query và index | Gần như mọi loại tải | Thời gian kỹ sư; hầu như không thêm hạ tầng |
| 2 | Cache (Redis, cache trong ứng dụng) | Đọc lặp lại cùng dữ liệu | Dữ liệu cũ (stale), phải lo invalidation |
| 3 | Read replica | Tải đọc | Replication lag: đọc ngay sau ghi có thể thấy dữ liệu cũ |
| 4 | Scale dọc (máy mạnh hơn) | Cả đọc lẫn ghi | Tiền; có trần phần cứng; thường cần downtime ngắn để chuyển |
| 5 | Archiving dữ liệu cũ | Bảng quá to | Phải viết job, phải trả lời "dữ liệu cũ ai còn cần" |
| 6 | Partitioning | Quản lý bảng rất to, xoá dữ liệu cũ | Giới hạn về unique key, foreign key; không tự làm nhanh mọi query |
| 7 | Sharding | Ghi vượt quá một máy, dữ liệu vượt quá một máy | Rất đắt: định tuyến, query xuyên shard, transaction xuyên shard, vận hành nhiều cụm |

Vì sao tối ưu query đứng đầu? Vì một truy vấn quét toàn bảng 10 triệu dòng chạy 1000 lần mỗi phút có
thể chiếm 90% CPU, và một index đúng có thể biến nó thành vài lần đọc trang. Không có giải pháp hạ tầng
nào cho mức cải thiện lớn như vậy với chi phí nhỏ như vậy.

Vì sao sharding đứng cuối? Vì khi đã chia dữ liệu ra nhiều máy, mọi thứ mà một database đơn lẻ làm hộ
bạn (join, transaction, unique, foreign key, backup nhất quán) đều phải tự lo lại. Figma kể rằng họ
mất khoảng chín tháng để shard bảng đầu tiên (mục 8.2).

> **Cạm bẫy:** Nhảy thẳng tới sharding vì "hệ thống lớn ai cũng shard". Phần lớn ứng dụng không bao giờ
> cần tới bậc 7. Một máy MySQL hiện đại với RAM lớn, SSD nhanh và index đúng chịu được tải lớn hơn
> nhiều người nghĩ.

## 2. Scale dọc và scale ngang

**Scale dọc** (vertical scaling, *scale up*): thay máy bằng máy mạnh hơn: nhiều CPU hơn, nhiều RAM
hơn, đĩa nhanh hơn. Ứng dụng không phải sửa gì.

**Scale ngang** (horizontal scaling, *scale out*): thêm máy, chia việc cho nhiều máy. Read replica là
scale ngang cho tải đọc; sharding là scale ngang cho cả đọc, ghi và dung lượng.

| | Scale dọc | Scale ngang |
|---|---|---|
| Sửa code | Không | Có (replica: tách đọc/ghi; sharding: nhiều) |
| Giới hạn | Máy to nhất có thể mua/thuê | Về lý thuyết thêm máy mãi được |
| Chi phí | Tăng nhanh ở cấu hình cao | Tăng gần tuyến tính theo số máy, cộng chi phí vận hành |
| Điểm lỗi | Một máy | Nhiều máy, nhiều cách hỏng hơn |
| Nhất quán | Như cũ | Phải chấp nhận lag (replica) hoặc mất transaction xuyên máy (shard) |

Vì sao scale dọc thường được chọn trước dù "không mở rộng mãi được"? Vì nó **mua thời gian** với chi
phí kỹ thuật gần bằng không. Thêm RAM để toàn bộ dữ liệu nóng nằm vừa trong buffer pool
([chương 16](16-ben-trong-innodb.md)) có thể giảm đọc đĩa xuống gần như bằng không.

Giới hạn của scale dọc: máy to nhất cũng có trần (Figma năm 2020 đã chạy trên instance vật lý lớn nhất
của AWS, mục 8.2); và một số giới hạn không phải phần cứng, ví dụ một bảng vài TB khiến mọi thao tác
bảo trì kéo dài.

## 3. Partitioning trong MySQL 8.4

### 3.1 Partitioning là gì

**Partitioning** (phân vùng) là chia **một bảng** thành nhiều phần vật lý gọi là *partition*, nhưng
với ứng dụng nó vẫn là **một bảng**: cùng tên, cùng câu `SELECT`, `INSERT`. Mỗi dòng được đặt vào đúng
một partition dựa trên giá trị của một biểu thức gọi là *partitioning expression* (hay *partition key*).

Với InnoDB, mỗi partition được lưu như một tablespace riêng (với `innodb_file_per_table` bật, mỗi
partition là một file `.ibd` riêng, tên kiểu `orders_p#p#p2026_01.ibd`). Mỗi partition có cây B+Tree
riêng cho clustered index và cho từng secondary index.

```
Bảng orders_p (một bảng logic)
├── partition p2026_01  -> dòng có created_at trong tháng 1/2026
├── partition p2026_02  -> tháng 2/2026
├── partition p2026_03  -> tháng 3/2026
└── partition pmax      -> mọi thứ từ 1/4/2026 trở đi
```

Vài sự thật lấy từ manual MySQL 8.4:

- Chỉ **InnoDB** và **NDB** hỗ trợ partitioning; MyISAM, MERGE, CSV, FEDERATED thì không. Mọi partition
  của một bảng phải cùng storage engine.
- MySQL chỉ có partitioning **theo dòng** (*horizontal partitioning*): các dòng khác nhau vào các
  partition khác nhau. MySQL 8.4 **không** hỗ trợ partitioning theo cột (*vertical partitioning*).
- Với `RANGE`, `LIST`, `HASH`, biểu thức partition phải trả về **số nguyên** (hoặc `NULL`). Riêng
  `KEY`, `RANGE COLUMNS`, `LIST COLUMNS` nhận trực tiếp danh sách cột.

Partitioning **khác** sharding: partitioning chia bảng **trong một server**; sharding chia dữ liệu ra
**nhiều server**. Partitioning không giúp bạn vượt quá sức một máy.

**Vì sao dùng partitioning?** Manual nêu lợi ích chính: dữ liệu hết giá trị thường có thể xoá rất dễ
bằng cách **drop partition** chứa nó; và truy vấn có điều kiện trên cột partition có thể bỏ qua các
partition không liên quan (*partition pruning*). Lợi ích thực tế lớn nhất là cái thứ nhất.

### 3.2 Dữ liệu mẫu và RANGE COLUMNS

Ta dùng bảng đơn hàng chia theo tháng. Chú ý khoá chính là `(id, created_at)` chứ không phải `(id)`;
lý do ở mục 3.7.

```sql
CREATE DATABASE IF NOT EXISTS ch23;
USE ch23;

CREATE TABLE orders_p (
    id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id INT UNSIGNED    NOT NULL,
    total       DECIMAL(10,2)   NOT NULL,
    created_at  DATETIME        NOT NULL,
    PRIMARY KEY (id, created_at),
    KEY idx_customer (customer_id)
)
PARTITION BY RANGE COLUMNS (created_at) (
    PARTITION p2026_01 VALUES LESS THAN ('2026-02-01'),
    PARTITION p2026_02 VALUES LESS THAN ('2026-03-01'),
    PARTITION p2026_03 VALUES LESS THAN ('2026-04-01'),
    PARTITION pmax     VALUES LESS THAN (MAXVALUE)
);

INSERT INTO orders_p (customer_id, total, created_at) VALUES
    (10, 120.00, '2026-01-05 09:00:00'),
    (11,  80.00, '2026-01-20 14:30:00'),
    (10,  45.50, '2026-02-03 08:15:00'),
    (12, 300.00, '2026-02-28 23:59:59'),
    (11,  60.00, '2026-03-01 00:00:00'),
    (13,  99.00, '2026-05-10 10:00:00');
```

Đọc định nghĩa như một chuỗi `if ... elseif`: dòng vào **partition đầu tiên** mà giá trị nhỏ hơn
(`LESS THAN`) mốc của nó. Các mốc phải tăng dần; khoảng liền nhau, không chồng lên nhau. `MAXVALUE` là
giá trị lớn hơn mọi giá trị khác, dùng làm partition "hứng tất cả" ở cuối.

Dòng nào vào đâu (tính tay):

| id | created_at | Partition | Lý do |
|---|---|---|---|
| 1 | 2026-01-05 09:00:00 | p2026_01 | < '2026-02-01' |
| 2 | 2026-01-20 14:30:00 | p2026_01 | < '2026-02-01' |
| 3 | 2026-02-03 08:15:00 | p2026_02 | không < '2026-02-01', nhưng < '2026-03-01' |
| 4 | 2026-02-28 23:59:59 | p2026_02 | < '2026-03-01' |
| 5 | 2026-03-01 00:00:00 | p2026_03 | bằng mốc '2026-03-01' nên **không** thuộc p2026_02 |
| 6 | 2026-05-10 10:00:00 | pmax | lớn hơn mọi mốc |

Dòng 5 là chỗ hay nhầm: `LESS THAN` là **nhỏ hơn hẳn**, mốc thuộc về partition sau.

Bạn có thể đọc riêng một partition bằng cú pháp *partition selection*:

```sql
SELECT id, created_at FROM orders_p PARTITION (p2026_02);
```

```
+----+---------------------+
| id | created_at          |
+----+---------------------+
|  3 | 2026-02-03 08:15:00 |
|  4 | 2026-02-28 23:59:59 |
+----+---------------------+
```

Xem danh sách partition qua `INFORMATION_SCHEMA.PARTITIONS`:

```sql
SELECT PARTITION_NAME, PARTITION_DESCRIPTION, TABLE_ROWS
FROM INFORMATION_SCHEMA.PARTITIONS
WHERE TABLE_SCHEMA = 'ch23' AND TABLE_NAME = 'orders_p';
```

`TABLE_ROWS` với InnoDB là **số ước lượng** từ thống kê, không phải đếm chính xác; muốn số đúng thì
`SELECT COUNT(*) ... PARTITION (...)`.

**Vì sao `RANGE COLUMNS` mà không phải `RANGE`?** `RANGE` thường đòi biểu thức trả về số nguyên, nên
với ngày bạn phải viết `RANGE (TO_DAYS(created_at))` hoặc `RANGE (YEAR(created_at))` và mốc cũng phải
là số. `RANGE COLUMNS` cho phép dùng thẳng cột và mốc dạng ngày, dễ đọc hơn. Các kiểu được phép cho
`COLUMNS` partitioning: mọi kiểu số nguyên, `DATE`, `DATETIME`, `CHAR`, `VARCHAR`, `BINARY`,
`VARBINARY`. **Không** được dùng `DECIMAL`, `FLOAT`, các kiểu thời gian khác (như `TIMESTAMP`,
`TIME`), `TEXT`, `BLOB`.

> **Cạm bẫy với `TIMESTAMP`:** cột `TIMESTAMP` không dùng được trong `RANGE COLUMNS`. Với `RANGE`,
> biểu thức duy nhất được phép trên cột `TIMESTAMP` là `UNIX_TIMESTAMP(col)`. Nếu định partition theo
> thời gian, chọn `DATETIME` ngay từ khi thiết kế bảng.

### 3.3 RANGE với hàm

Cách viết cũ hơn, vẫn gặp nhiều:

```sql
CREATE TABLE logs_by_year (
    id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    created_at DATETIME NOT NULL,
    message    VARCHAR(255) NOT NULL,
    PRIMARY KEY (id, created_at)
)
PARTITION BY RANGE (YEAR(created_at)) (
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026),
    PARTITION p2026 VALUES LESS THAN (2027),
    PARTITION pmax  VALUES LESS THAN MAXVALUE
);
```

Chỉ một nhóm hàm được phép trong biểu thức partition (manual liệt kê 23 hàm, ví dụ `YEAR()`,
`MONTH()`, `TO_DAYS()`, `TO_SECONDS()`, `UNIX_TIMESTAMP()`, `MOD()`, `ABS()`...). Và **chỉ** `TO_DAYS()`,
`TO_SECONDS()`, `YEAR()`, `UNIX_TIMESTAMP()` được optimizer hỗ trợ partition pruning trên khoảng giá
trị. Partition theo `MONTH(created_at)` chẳng hạn hợp lệ nhưng không prune được truy vấn theo khoảng
ngày, và còn gộp tháng 1 của mọi năm vào cùng một chỗ.

**`NULL` trong RANGE:** `NULL` được coi là nhỏ hơn mọi giá trị, nên dòng có giá trị partition là
`NULL` vào **partition thấp nhất**. Ở bảng trên, nếu `created_at` cho phép `NULL`, mọi dòng `NULL`
dồn vào `p2024`, và khi bạn `DROP PARTITION p2024` để xoá năm 2024 thì chúng mất theo. Đây là một lý do
nên khai báo cột partition `NOT NULL`.

### 3.4 LIST

`LIST` gán dòng theo **danh sách giá trị** rời rạc. Ví dụ chia khách hàng theo vùng:

```sql
CREATE TABLE customers_region (
    id        INT UNSIGNED NOT NULL,
    name      VARCHAR(100) NOT NULL,
    region_id TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (id, region_id)
)
PARTITION BY LIST (region_id) (
    PARTITION p_north   VALUES IN (1, 2, 3),
    PARTITION p_central VALUES IN (4, 5),
    PARTITION p_south   VALUES IN (6, 7, 8)
);

INSERT INTO customers_region VALUES (1, 'An', 1), (2, 'Bình', 5);   -- OK
INSERT INTO customers_region VALUES (3, 'Chi', 9);
```

```
ERROR 1526 (HY000): Table has no partition for value 9
```

`LIST` trong MySQL 8.4 **không có** partition "mặc định" kiểu `MAXVALUE`: mọi giá trị có thể xuất hiện
phải được liệt kê. Với InnoDB, một câu `INSERT` nhiều dòng mà có một dòng không khớp partition sẽ thất
bại toàn bộ (không dòng nào được ghi). `INSERT IGNORE` biến lỗi thành warning và **bỏ** các dòng
không khớp: dữ liệu mất lặng lẽ, thường là điều bạn không muốn.

Với `NULL`: bảng `LIST` chỉ nhận `NULL` nếu một partition liệt kê `NULL` trong `VALUES IN (...)`; nếu
không thì báo lỗi `Table has no partition for value NULL`.

Có thêm `LIST COLUMNS` cho phép liệt kê giá trị chuỗi, ví dụ `PARTITION BY LIST COLUMNS (country)
(PARTITION p_vn VALUES IN ('VN'), ...)`.

### 3.5 HASH và KEY

Khi không có thứ tự tự nhiên và chỉ muốn **rải đều** dữ liệu, dùng `HASH` hoặc `KEY`.

`HASH (expr) PARTITIONS N`: MySQL tính `MOD(expr, N)` để ra số thứ tự partition (0 tới N-1).

```sql
CREATE TABLE carts (
    customer_id INT UNSIGNED NOT NULL,
    item_count  INT NOT NULL,
    PRIMARY KEY (customer_id)
)
PARTITION BY HASH (customer_id) PARTITIONS 4;
```

Tính tay: `customer_id` 10 vào p2 (10 mod 4 = 2), 11 vào p3, 12 vào p0, 13 vào p1. MySQL tự đặt tên
partition là `p0`, `p1`, `p2`, `p3`. `NULL` trong `HASH`/`KEY` được coi như 0.

`KEY (cols) PARTITIONS N`: giống `HASH` nhưng hàm băm do MySQL cung cấp, và cột **không** bắt buộc là
số nguyên (dùng được `CHAR`, `VARCHAR`, `BINARY`, `VARBINARY`; không dùng được `TEXT`, `BLOB`). Nếu
viết `PARTITION BY KEY ()` không ghi cột, MySQL dùng khoá chính.

```sql
CREATE TABLE sessions_k (
    session_id CHAR(32) NOT NULL PRIMARY KEY,
    user_id    INT UNSIGNED NOT NULL,
    data       VARCHAR(1000)
)
PARTITION BY KEY () PARTITIONS 8;
```

> **Cạm bẫy:** `HASH`/`KEY` rải đều nhưng **không** cho bạn xoá dữ liệu cũ theo thời gian bằng
> `DROP PARTITION` (mỗi partition chứa lẫn dữ liệu mọi thời điểm). Pruning với `HASH`/`KEY` chỉ hiệu
> quả cho điều kiện `=` (hoặc khoảng rất ngắn trên cột số nguyên, ít giá trị hơn số partition). Truy
> vấn theo khoảng sẽ quét mọi partition.

Còn *subpartitioning* (chia tiếp mỗi partition `RANGE`/`LIST` thành các subpartition `HASH`/`KEY`),
ít dùng; tổng số partition kể cả subpartition tối đa **8192** (với engine không phải NDB).

### 3.6 Partition pruning và EXPLAIN

**Partition pruning** nghĩa là optimizer nhìn điều kiện `WHERE`, suy ra partition nào **không thể**
chứa dòng khớp, và bỏ qua chúng. Cột `partitions` trong `EXPLAIN` cho biết partition nào sẽ được đọc.

```sql
EXPLAIN SELECT SUM(total) FROM orders_p
WHERE created_at >= '2026-02-01' AND created_at < '2026-03-01'\G
```

```
-- output minh hoạ
           id: 1
  select_type: SIMPLE
        table: orders_p
   partitions: p2026_02
         type: ALL
...
```

Chỉ `p2026_02` được đọc. Kết quả câu truy vấn: dòng 3 và 4, `SUM(total)` = 45.50 + 300.00 = **345.50**.

Bây giờ lọc theo cột không phải cột partition:

```sql
EXPLAIN SELECT * FROM orders_p WHERE customer_id = 10\G
```

```
-- output minh hoạ
   partitions: p2026_01,p2026_02,p2026_03,pmax
         type: ref
          key: idx_customer
```

Optimizer không biết khách 10 mua hàng tháng nào, nên phải tra index `idx_customer` trong **cả bốn**
partition. Mỗi partition có cây index riêng (mục 3.1), nên đây là bốn lần đi cây B+Tree thay vì một.
Với 120 partition (10 năm theo tháng), là 120 lần. Đây là lý do partitioning có thể làm truy vấn
**chậm đi**.

Quy tắc để pruning hoạt động:

- Điều kiện phải đặt **trực tiếp lên cột partition** với hằng số: `=`, `IN`, `<`, `>`, `<=`, `>=`,
  `BETWEEN`. Cũng như với index ([chương 11](11-index.md)), đừng bọc cột trong hàm khác ở `WHERE`.
- `SELECT`, `UPDATE`, `DELETE` đều được pruning. `INSERT` mỗi dòng chỉ chạm một partition (nhưng
  `EXPLAIN` không hiện điều này).
- Giá trị ngày không hợp lệ trong `WHERE` (như `'2026-02-30'`) bị coi là `NULL`, truy vấn có thể
  không trả dòng nào.

### 3.7 Giới hạn quan trọng

**Giới hạn 1: mọi unique key phải chứa mọi cột trong biểu thức partition.** Nguyên văn manual: *"every
unique key on the table must use every column in the table's partitioning expression"*, và khoá chính
cũng là một unique key.

```sql
CREATE TABLE orders_bad (
    id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL
)
PARTITION BY RANGE COLUMNS (created_at) (
    PARTITION p0 VALUES LESS THAN ('2026-01-01'),
    PARTITION p1 VALUES LESS THAN (MAXVALUE)
);
```

```
ERROR 1503 (HY000): A PRIMARY KEY must include all columns in the table's partitioning function (prefixed columns are not considered).
```

Cùng mã lỗi 1503 (`ER_UNIQUE_KEY_NEED_ALL_FIELDS_IN_PF`) cho cả khoá chính lẫn `UNIQUE` thường; khi thủ
phạm là một `UNIQUE` thường, thông báo ghi `UNIQUE INDEX` thay cho `PRIMARY KEY`. (Vài ví dụ trong
manual vẫn in mã cũ 1491 và câu thông báo cũ không có phần trong ngoặc.)

**Vì sao có luật này?** Mỗi partition có index riêng. Để kiểm tra "id = 5 đã tồn tại chưa", MySQL chỉ
muốn nhìn **một** partition. Nếu unique key chứa cột partition, giá trị của nó xác định duy nhất
partition cần kiểm tra. Nếu không, MySQL sẽ phải kiểm tra mọi partition ở mỗi lần ghi; MySQL chọn
không hỗ trợ (không có "global index").

**Hệ quả thực tế:** bảng `users` partition theo `created_at` không thể có `UNIQUE (email)`; chỉ có
`UNIQUE (email, created_at)`, nghĩa là cùng email ở hai thời điểm khác nhau vẫn được chấp nhận. Mất
ràng buộc duy nhất toàn cục. Nếu bảng **không có** unique key nào (kể cả không có khoá chính) thì luật
không áp dụng, nhưng InnoDB không có khoá chính là một thiết kế tệ ([chương 16](16-ben-trong-innodb.md)).

**Giới hạn 2: không có foreign key.** Manual: *"Partitioned tables using the InnoDB storage engine do
not support foreign keys."* Cả hai chiều: bảng partition không được khai báo foreign key, và không bảng
InnoDB nào được có foreign key trỏ vào bảng partition. Toàn vẹn tham chiếu phải do ứng dụng lo.

**Các giới hạn khác** (manual 8.4, mục *Restrictions and Limitations on Partitioning*):

- Không hỗ trợ index và tìm kiếm `FULLTEXT`.
- Không dùng được cột kiểu không gian (`POINT`, `GEOMETRY`...).
- Bảng tạm (temporary table) không partition được.
- Tối đa 8192 partition (kể cả subpartition) cho engine không phải NDB.
- Biểu thức partition không được chứa truy vấn con, hàm ngẫu nhiên hay không xác định.

### 3.8 Quản lý partition: thêm, tách, xoá, đổi

**Xoá dữ liệu cũ: `DROP PARTITION`.** Đây là lý do số một để partition theo thời gian.

```sql
ALTER TABLE orders_p DROP PARTITION p2026_01;
```

Dòng 1 và 2 biến mất. Với `DELETE FROM orders_p WHERE created_at < '2026-02-01'`, InnoDB phải tìm từng
dòng, đánh dấu xoá, ghi undo log, ghi redo log, cập nhật từng secondary index, và với replication dựa
trên dòng thì ghi từng dòng vào binlog. Với 50 triệu dòng, việc này mất hàng giờ, sinh replication lag
lớn và file `.ibd` không nhỏ lại. `DROP PARTITION` thì bỏ cả tablespace của partition đó: thao tác
metadata, nhanh gần như không phụ thuộc số dòng, và trả lại dung lượng đĩa.

Cần biết:

- Cần quyền `DROP` trên bảng.
- Server **không báo** số dòng bị xoá (khác với `DELETE`).
- Dữ liệu đi luôn, không rollback được (DDL tự commit, [chương 04](04-ddl-constraint.md)). Backup trước
  nếu cần.

**Xoá dữ liệu nhưng giữ partition:** `ALTER TABLE orders_p TRUNCATE PARTITION p2026_02;`

**Thêm partition mới.** Với `RANGE`, `ADD PARTITION` chỉ thêm được ở **đầu cao** của danh sách. Bảng
của ta đã có `pmax ... MAXVALUE` ở cuối, nên không thể thêm gì sau nó:

```sql
ALTER TABLE orders_p ADD PARTITION (PARTITION p2026_04 VALUES LESS THAN ('2026-05-01'));
```

```
ERROR 1481 (HY000): MAXVALUE can only be used in last partition definition
```

Server từ chối `ADD PARTITION` ngay khi bảng đã có partition `MAXVALUE` (mã nguồn MySQL kiểm tra điều
này trước khi xét mốc). Còn nếu bảng không có `MAXVALUE` mà mốc mới không lớn hơn mốc cuối, lỗi là
`ERROR 1493 (HY000): VALUES LESS THAN value must be strictly increasing for each partition`.

Cách làm là **tách** `pmax` bằng `REORGANIZE PARTITION`:

```sql
ALTER TABLE orders_p REORGANIZE PARTITION pmax INTO (
    PARTITION p2026_04 VALUES LESS THAN ('2026-05-01'),
    PARTITION pmax     VALUES LESS THAN (MAXVALUE)
);
```

Các partition mới phải phủ đúng khoảng của partition cũ. Dòng 6 (2026-05-10) vẫn nằm ở `pmax`.
`REORGANIZE` phải **di chuyển dữ liệu** trong partition bị tách; nếu `pmax` đang rỗng thì rất nhanh,
nếu `pmax` chứa hàng triệu dòng thì chậm. Vì vậy mẹo vận hành: **luôn tạo trước** partition cho vài
tháng tới, để `pmax` gần như luôn rỗng.

Quy trình "cửa sổ trượt" (*rolling window*) hằng tháng, thường chạy bằng job định kỳ:

1. Tách `pmax` để có partition cho tháng N+2 (giữ hai tháng dự phòng).
2. Xuất (hoặc `EXCHANGE`, xem dưới) partition cũ nhất nếu cần lưu trữ.
3. `DROP PARTITION` partition cũ nhất vượt thời hạn giữ dữ liệu.

**Đổi partition với một bảng thường: `EXCHANGE PARTITION`.** Hoán đổi nội dung một partition với một
bảng không partition có cấu trúc giống hệt. Hữu ích để "rút" một tháng ra thành bảng riêng rồi đem đi
lưu trữ:

```sql
CREATE TABLE orders_2026_02 LIKE orders_p;
ALTER TABLE orders_2026_02 REMOVE PARTITIONING;

ALTER TABLE orders_p EXCHANGE PARTITION p2026_02 WITH TABLE orders_2026_02;
```

Sau lệnh, `orders_2026_02` chứa dòng 3 và 4, còn partition `p2026_02` rỗng. Bảng đích không được là bảng
partition, không được có foreign key, và theo mặc định MySQL kiểm tra mọi dòng của bảng đích nằm đúng
khoảng của partition.

### 3.9 Partitioning không phải "thuốc tăng tốc"

Nhiều người partition bảng với hy vọng truy vấn nhanh hơn rồi thất vọng. Tóm lại:

- **Có lợi rõ** khi: xoá dữ liệu theo thời gian (`DROP PARTITION`); truy vấn **luôn** lọc theo cột
  partition (pruning); bảo trì từng partition một (rebuild, `ANALYZE`).
- **Không lợi, thậm chí hại** khi: truy vấn hay lọc theo cột khác (mục 3.6); lookup theo khoá chính
  `id` mà không kèm cột partition (phải dò mọi partition); bạn cần unique toàn cục hay foreign key.
- Một B+Tree 100 triệu dòng chỉ sâu hơn cây 10 triệu dòng khoảng một tầng. Chia nhỏ cây không làm
  lookup qua index nhanh hơn đáng kể. Thứ thực sự làm nhanh là index đúng.

> **Cạm bẫy:** Thêm partitioning vào bảng hiện có là một câu `ALTER TABLE ... PARTITION BY` dựng lại
> toàn bộ bảng (bảng lớn thì lâu, xem [chương 20](20-thay-doi-schema-migration.md)), và có thể buộc bạn
> đổi khoá chính. Nên quyết định từ lúc thiết kế cho các bảng biết trước sẽ phình theo thời gian (log,
> sự kiện, lịch sử giao dịch).

## 4. Archiving dữ liệu cũ

### 4.1 Vì sao

Phần lớn ứng dụng có dữ liệu **nóng** (vài tháng gần nhất, đọc ghi liên tục) và dữ liệu **lạnh** (đơn
hàng ba năm trước, gần như không ai xem). Dữ liệu lạnh vẫn chiếm đĩa, làm backup lâu hơn, làm
`ALTER TABLE` lâu hơn, và chiếm chỗ trong index. **Archiving** là chuyển dữ liệu lạnh ra khỏi bảng
chính: sang bảng lưu trữ, database khác, file (CSV, Parquet) trên object storage, hoặc xoá hẳn nếu
không còn nghĩa vụ giữ.

Câu hỏi nghiệp vụ phải trả lời **trước**: giữ bao lâu (luật kế toán, hợp đồng), ai còn cần đọc, đọc thì
qua đâu (một trang "lịch sử cũ" chậm hơn cũng được không).

### 4.2 Bảng có partition theo thời gian

Dễ nhất: `EXCHANGE PARTITION` ra bảng riêng (mục 3.8), dump bảng đó đi, rồi `DROP PARTITION`.

### 4.3 Bảng không partition: chuyển theo batch

Không bao giờ chạy một câu `DELETE` cho hàng triệu dòng: transaction khổng lồ, giữ lock lâu, undo log
phình to, replica lag ([chương 20](20-thay-doi-schema-migration.md) mục 6 có cùng lý do cho backfill).
Thay vào đó, mỗi batch một transaction nhỏ:

```sql
-- bảng lưu trữ cùng cấu trúc
CREATE TABLE orders_archive LIKE orders;

-- một batch; lặp lại cho tới khi @max là NULL
SELECT MAX(id) INTO @max FROM (
    SELECT id FROM orders
    WHERE created_at < '2025-01-01'
    ORDER BY id LIMIT 1000
) AS batch;

START TRANSACTION;
INSERT INTO orders_archive
    SELECT * FROM orders WHERE created_at < '2025-01-01' AND id <= @max;
DELETE FROM orders WHERE created_at < '2025-01-01' AND id <= @max;
COMMIT;
```

Bước đầu chốt **ranh giới** `@max` của batch (id lớn nhất trong 1000 dòng cũ nhất), sau đó cả `INSERT`
lẫn `DELETE` dùng đúng cùng điều kiện, nên chép và xoá cùng một tập dòng. Điều này đúng vì không ai còn
ghi thêm dòng có `created_at` năm 2024. Cần index trên `created_at` để mỗi batch không quét cả bảng. Giữa
các batch, nghỉ một chút hoặc kiểm tra replica lag. Công cụ có sẵn làm đúng việc này là
`pt-archiver` (Percona Toolkit).

> **Cạm bẫy:** Sau khi `DELETE` hàng triệu dòng, file `.ibd` **không nhỏ đi**: InnoDB giữ các trang
> trống để dùng lại. Muốn trả đĩa cho hệ điều hành phải dựng lại bảng (`OPTIMIZE TABLE` hoặc
> `ALTER TABLE ... FORCE`), một thao tác nặng khác. Đây là thêm một lý do để chọn partition theo thời
> gian nếu biết trước sẽ xoá dữ liệu cũ đều đặn.

## 5. Sharding

### 5.1 Sharding là gì

**Sharding** là chia dữ liệu của **một** ứng dụng ra **nhiều database server độc lập**, mỗi server
gọi là một *shard*, mỗi shard giữ một phần các dòng. Mỗi shard là một MySQL bình thường (thường có
replica riêng), không biết các shard khác tồn tại.

```
                 ứng dụng / router
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
     shard 0        shard 1        shard 2
  tenant 1..N/3  tenant ...     tenant ...
 (primary+replica)(primary+replica)(primary+replica)
```

So sánh để nhớ:

| | Partitioning (MySQL) | Read replica | Sharding |
|---|---|---|---|
| Số server giữ dữ liệu ghi | 1 | 1 (primary) | Nhiều |
| Mỗi server có | Toàn bộ dữ liệu | Bản sao toàn bộ dữ liệu | Một phần dữ liệu |
| Mở rộng ghi | Không | Không | Có |
| Ứng dụng phải biết | Không | Tách đọc/ghi | Dữ liệu nằm ở shard nào |

Sharding là cách duy nhất trong danh sách giúp khi **tải ghi** hoặc **dung lượng** vượt quá một máy.
Cái giá: mọi thứ cần nhiều dòng ở nhiều shard (join, transaction, unique, đếm tổng) không còn do
database lo hộ.

### 5.2 Shard key

**Shard key** là cột (hoặc tổ hợp cột) quyết định một dòng nằm ở shard nào. Đây là quyết định quan
trọng nhất và khó đổi nhất của sharding.

Tiêu chí một shard key tốt:

1. **Hầu hết truy vấn có nó.** Truy vấn có shard key thì đi thẳng tới một shard. Truy vấn không có
   thì phải hỏi mọi shard.
2. **Dữ liệu cần dùng chung nằm cùng shard.** Dữ liệu hay join với nhau, hay sửa trong cùng
   transaction, nên có cùng shard key để ở cùng chỗ.
3. **Phân bố đều**, cả về dung lượng lẫn tải. Tránh *hot shard*: một shard nhận phần lớn tải.
4. **Nhiều giá trị khác nhau** (cardinality cao), để có thể chia mịn.
5. **Không đổi** theo thời gian. Đổi shard key của một dòng nghĩa là chuyển dòng sang shard khác.

Ví dụ với ứng dụng SaaS nhiều khách hàng doanh nghiệp (*multi-tenant*): `tenant_id` (hay
`workspace_id`, `org_id`) thường là lựa chọn tự nhiên. Gần như mọi truy vấn chỉ nhìn dữ liệu của một
tenant, và mọi bảng của tenant (dự án, tài liệu, bình luận) đi cùng nhau. Notion chọn đúng kiểu khoá
này (mục 8.1).

Các lựa chọn tệ hay gặp:

- `created_at` hoặc ID tăng dần **theo range**: mọi dòng mới dồn vào shard cuối, shard đó nóng còn các
  shard khác ngồi chơi.
- `country`: ít giá trị, phân bố lệch (một nước chiếm 70% người dùng).
- `user_id` cho một mạng xã hội rồi truy vấn "mọi bài viết của nhóm X": bài viết của một nhóm rải trên
  mọi shard.

Một tenant quá lớn (một khách hàng chiếm 30% dữ liệu) vẫn có thể thành hot shard dù khoá tốt. Hệ thống
lớn thường có cách tách riêng khách hàng lớn ra shard của họ.

### 5.3 Chia dữ liệu theo cách nào

Có ba cách phổ biến để biến giá trị shard key thành số shard:

| Cách | Ý tưởng | Ưu | Nhược |
|---|---|---|---|
| Range | `tenant_id` 1 tới 1 triệu ở shard 0, tiếp theo ở shard 1... | Truy vấn theo khoảng gọn | Dễ lệch, dễ hot shard với khoá tăng dần |
| Hash | `shard = hash(tenant_id) mod N` | Phân bố đều | Truy vấn khoảng phải hỏi mọi shard; đổi N thì gần như mọi khoá đổi chỗ |
| Directory (lookup) | Bảng tra `tenant_id -> shard` | Linh hoạt, chuyển từng tenant được | Bảng tra là thành phần thêm phải luôn sẵn sàng và nhanh |

**Logical shard nhiều hơn physical shard.** Vấn đề lớn của `hash mod N` là khi tăng N từ 4 lên 5,
`hash mod 5` khác `hash mod 4` với phần lớn khoá, tức gần hết dữ liệu phải di chuyển. Cách làm phổ biến
là chia thành **nhiều shard logic** cố định (ví dụ 480), rồi gán nhiều shard logic vào mỗi server vật
lý. Khoá luôn map vào cùng shard logic; khi thêm máy, chỉ cần chuyển nguyên một số shard logic sang máy
mới, không phải tính lại hash. Notion dùng 480 shard logic trên 32 database vật lý, sau này trên 96
(mục 8.1). (*Consistent hashing* là một kỹ thuật khác cùng mục đích, hay gặp ở cache và key-value
store.)

### 5.4 Định tuyến

Ai quyết định truy vấn đi tới shard nào?

1. **Trong ứng dụng** (application-level sharding): code có một hàm `shardFor(tenantId)` trả về kết nối
   tới đúng database. Đơn giản, minh bạch, nhưng mọi chỗ truy cập dữ liệu phải đi qua lớp này.
2. **Proxy ở giữa**: ứng dụng nói chuyện với một proxy như với một MySQL bình thường; proxy phân tích
   câu SQL, tìm shard key, chuyển tới shard đúng. Vitess (mục 6.1) và DBProxy của Figma (mục 8.2) là
   kiểu này.
3. **Database phân tán tự lo**: Citus (mục 6.2), hay các hệ như CockroachDB, TiDB, Spanner.

Phác thảo cách 1 bằng PHP (minh hoạ, không chạy được nếu chưa có các server tương ứng):

```php
<?php
declare(strict_types=1);

const LOGICAL_SHARDS = 480;

/** Map shard logic -> DSN của server vật lý (thường đọc từ config). */
function physicalDsn(int $logicalShard): string
{
    $server = intdiv($logicalShard, 15);   // 15 shard logic mỗi server, 32 server
    return sprintf('mysql:host=db-%02d.internal;dbname=shard_%03d', $server, $logicalShard);
}

function logicalShardFor(int $tenantId): int
{
    // crc32 trả về số không âm trên PHP 64-bit
    return crc32((string) $tenantId) % LOGICAL_SHARDS;
}

$dsn = physicalDsn(logicalShardFor(42));
```

Điểm quan trọng: công thức tenant -> shard logic **không bao giờ đổi**; chỉ bảng shard logic -> server
vật lý thay đổi khi resharding.

### 5.5 Truy vấn và transaction xuyên shard

**Truy vấn xuyên shard.** "Top 10 sản phẩm bán chạy toàn hệ thống" không có shard key: phải gửi tới
mọi shard (*scatter*), rồi gộp kết quả ở ứng dụng hoặc proxy (*gather*). Hậu quả:

- Độ trễ bằng shard **chậm nhất**; một shard có sự cố làm hỏng cả truy vấn.
- Tổng tải nhân lên theo số shard.
- Gộp không phải lúc nào cũng đơn giản. `COUNT`, `SUM` gộp bằng cách cộng. `AVG` thì **không** được
  lấy trung bình của các trung bình: phải lấy `SUM` và `COUNT` từ mỗi shard rồi chia. `ORDER BY ...
  LIMIT 10` phải lấy 10 dòng đầu từ **mỗi** shard rồi sắp lại. `COUNT(DISTINCT)` thì gần như phải gom
  hết giá trị về.
- Join giữa hai bảng có shard key khác nhau (ví dụ `orders` theo `customer_id`, `products` theo
  `product_id`) không làm được trong database.

Cách giảm: chọn shard key sao cho truy vấn thường gặp nằm trong một shard; bảng nhỏ, ít đổi (danh mục
quốc gia, cấu hình) thì **chép đầy đủ lên mọi shard** (*reference table*); truy vấn báo cáo toàn hệ
thống thì đẩy dữ liệu sang kho dữ liệu riêng (data warehouse) thay vì chạy trên shard.

**Transaction xuyên shard.** Transaction ở [chương 13](13-transaction-acid.md) chỉ có hiệu lực trong
**một** server. Chuyển tiền từ tài khoản ở shard 1 sang tài khoản ở shard 2 là hai transaction độc lập;
nếu cái thứ nhất commit rồi server thứ hai sập, tiền "bốc hơi". Các lựa chọn:

- **Tránh**: thiết kế để những gì phải nguyên tử nằm cùng shard. Đây là cách được dùng nhiều nhất;
  Figma chủ động **không** hỗ trợ transaction nguyên tử xuyên shard.
- **Two-phase commit (2PC)**: một bộ điều phối hỏi mọi shard "chuẩn bị xong chưa", tất cả trả lời có
  mới ra lệnh commit. Đúng nhưng chậm, và khi bộ điều phối chết giữa chừng thì các shard bị treo chờ.
  MySQL có XA transaction (`XA START`, `XA PREPARE`, `XA COMMIT`) làm nền cho việc này.
- **Saga / bù trừ**: chia thành các bước có transaction cục bộ, mỗi bước có bước "hoàn tác" nếu bước
  sau thất bại. Chấp nhận trạng thái trung gian nhìn thấy được.

**Ràng buộc mất đi.** `UNIQUE (email)` chỉ được kiểm tra trong từng shard; hai người dùng cùng email ở
hai shard khác nhau sẽ lọt qua. Foreign key giữa hai shard không tồn tại. Cách thường dùng: một bảng
riêng, không shard (hoặc shard theo chính `email`), giữ `email -> user_id` để kiểm tra trùng.

### 5.6 ID toàn cục

Với `AUTO_INCREMENT`, mỗi shard tự đếm từ 1, nên shard 0 và shard 1 cùng sinh ra `id = 1`. Cần ID
**duy nhất trên mọi shard**. Các cách:

**Cách 1: chia bước AUTO_INCREMENT.** Đặt `auto_increment_increment = N` (bước) và
`auto_increment_offset = k` (điểm bắt đầu) khác nhau trên mỗi server: với N = 3, server 1 sinh 1, 4,
7...; server 2 sinh 2, 5, 8... Đơn giản, nhưng thêm server thì phải đổi lại cả sơ đồ, và ID không cho
biết nó thuộc shard nào sau khi resharding.

**Cách 2: Snowflake.** Twitter công bố năm 2010. ID là số 64 bit ghép từ:

```
| 1 bit (0) | 41 bit: mili giây từ một epoch riêng | 10 bit: mã máy | 12 bit: số thứ tự |
```

- 41 bit mili giây đủ khoảng 69 năm kể từ epoch đã chọn.
- 10 bit mã máy: tối đa 1024 máy sinh ID.
- 12 bit thứ tự: mỗi máy sinh tối đa 4096 ID trong một mili giây.

Ưu: vừa kiểu `BIGINT`, **tăng gần theo thời gian** nên chèn vào clustered index B+Tree luôn ở cuối
(như `AUTO_INCREMENT`, không gây tách trang ngẫu nhiên, xem [chương 16](16-ben-trong-innodb.md)), sinh
ra không cần hỏi database. Nhược: phải cấp mã máy duy nhất cho từng tiến trình sinh ID, và nếu đồng hồ
máy chạy lùi (chỉnh NTP) có thể sinh trùng; cài đặt đúng phải phát hiện điều này.

**Cách 3: UUID.** 128 bit, sinh ở đâu cũng được, xác suất trùng không đáng kể.

- **UUIDv4** hoàn toàn ngẫu nhiên. Làm khoá chính InnoDB thì tệ: mỗi lần chèn rơi vào vị trí ngẫu
  nhiên trong cây, gây tách trang, cây phân mảnh, buffer pool phải giữ cả cây thay vì chỉ phần cuối.
- **UUIDv7** (định nghĩa trong RFC 9562, tháng 5/2024): 48 bit đầu là Unix timestamp tính bằng mili
  giây, phần còn lại (trừ các bit version, variant) là ngẫu nhiên. Nhờ phần đầu tăng theo thời gian,
  chèn vào B+Tree gần như tuần tự như Snowflake, mà không cần cấp mã máy.

MySQL 8.4 **không có** hàm sinh UUIDv7: `UUID()` sinh UUID version 1. Bạn sinh UUIDv7 trong ứng dụng
(nhiều thư viện hỗ trợ) rồi lưu dưới dạng `BINARY(16)` thay vì `CHAR(36)` để tiết kiệm chỗ (16 byte so
với 36 ký tự) và so sánh nhanh hơn:

```sql
CREATE TABLE documents (
    id    BINARY(16) NOT NULL PRIMARY KEY,
    title VARCHAR(200) NOT NULL
);

-- chuỗi UUIDv7 do ứng dụng sinh
INSERT INTO documents VALUES (UUID_TO_BIN('01890a5d-ac96-774b-bcce-b302099a8057'), 'Kế hoạch');

SELECT BIN_TO_UUID(id) AS id, title FROM documents;
```

`UUID_TO_BIN` có tham số thứ hai `swap_flag`; đặt 1 sẽ đảo vị trí phần thời gian, được thiết kế cho
UUID version 1 (kiểu của `UUID()`), để chúng sắp xếp theo thời gian. Với UUIDv7 **đừng** bật cờ này:
UUIDv7 vốn đã có timestamp ở đầu. PostgreSQL 18 có sẵn hàm `uuidv7()`.

So sánh nhanh:

| | AUTO_INCREMENT chia bước | Snowflake | UUIDv4 | UUIDv7 |
|---|---|---|---|---|
| Kích thước | 8 byte | 8 byte | 16 byte | 16 byte |
| Tăng theo thời gian | Mỗi server | Gần đúng | Không | Gần đúng |
| Cần phối hợp | Cấu hình server | Cấp mã máy | Không | Không |
| Lộ thông tin | Số lượng bản ghi | Thời điểm tạo | Không | Thời điểm tạo |

### 5.7 Resharding

**Resharding** là thay đổi cách chia: thêm server, tách một shard nóng, hay đổi cả shard key. Đây là
phần đau nhất của sharding, vì phải di chuyển dữ liệu **trong khi** ứng dụng vẫn đọc ghi.

Trình tự chung (Notion và Figma đều mô tả biến thể của nó):

1. **Chép dữ liệu lịch sử** sang chỗ mới (snapshot hoặc backfill theo batch).
2. **Giữ đồng bộ** các thay đổi mới: replication (binlog, logical replication) hoặc ghi kép
   (*double write*) từ ứng dụng.
3. **Kiểm tra**: so dữ liệu hai bên; *dark read*: đọc cả hai, so kết quả, ghi log khác biệt, nhưng
   chỉ trả kết quả bên cũ cho người dùng.
4. **Chuyển (cutover)**: dừng ghi trong thời gian ngắn, chờ bên mới bắt kịp, đổi bảng định tuyến.
5. **Giữ đường lùi**: đảo chiều replication để bên cũ vẫn được cập nhật, phòng khi phải quay lại.

Thiết kế từ đầu với nhiều shard logic (mục 5.3) biến resharding từ "tính lại chỗ của từng dòng" thành
"chuyển nguyên vài shard logic sang máy mới", đơn giản hơn nhiều.

## 6. Công cụ có sẵn: Vitess và Citus

### 6.1 Vitess (MySQL)

Vitess là hệ thống sharding cho MySQL, khởi đầu ở YouTube, nay là dự án của CNCF. Thành phần chính:

- **VTGate**: proxy mà ứng dụng kết nối tới như một MySQL. Nó phân tích SQL và định tuyến tới shard
  đúng, gộp kết quả với truy vấn xuyên shard.
- **VTTablet**: tiến trình chạy cạnh mỗi `mysqld`, quản lý kết nối, bảo vệ MySQL khỏi truy vấn quá
  nặng.
- **Topology service** (etcd, ZooKeeper hoặc Consul): lưu metadata: có những shard nào, ở đâu.
- **Keyspace**: một database logic, có thể gồm nhiều shard. **VSchema** mô tả bảng nào shard theo cột
  nào; **vindex** là hàm biến giá trị cột thành *keyspace ID*, và mỗi shard giữ một khoảng keyspace ID
  (shard tên kiểu `-80`, `80-` là hai nửa của khoảng).

Vitess có workflow dựng sẵn cho resharding (`Reshard`) và chuyển bảng giữa keyspace (`MoveTables`),
làm đúng các bước ở mục 5.7 một cách tự động. Đổi lại, bạn vận hành thêm một hệ thống nhiều thành
phần, và không phải mọi câu SQL đều được hỗ trợ khi chạy xuyên shard.

### 6.2 Citus (PostgreSQL)

Citus là **extension** của PostgreSQL biến một cụm Postgres thành database phân tán: một node
*coordinator* nhận truy vấn và các node *worker* giữ dữ liệu. Bạn chọn cột phân tán cho từng bảng:

```sql
-- PostgreSQL + Citus
SELECT create_distributed_table('orders', 'tenant_id');
SELECT create_reference_table('countries');   -- chép đầy đủ lên mọi worker
```

Bảng phân tán được chia thành các shard (mặc định `citus.shard_count` = 32), rải lên các worker. Các
bảng phân tán theo cùng cột (cùng `tenant_id`) được đặt cùng chỗ (*co-location*), nên join và
transaction trong một tenant chạy ở một worker. Citus cũng hỗ trợ truy vấn xuyên shard bằng cách đẩy
một phần tính toán xuống các worker song song.

### 6.3 Có nên dùng công cụ không

Notion đã cân nhắc Citus và Vitess nhưng chọn tự viết sharding ở tầng ứng dụng vì muốn kiểm soát cách
phân bố dữ liệu. Figma cân nhắc CockroachDB, TiDB, Spanner, Vitess nhưng chọn tự xây trên RDS Postgres
có sẵn, chủ yếu vì rủi ro di chuyển và để giữ chuyên môn sẵn có. Cả hai đều là công ty có đội database
riêng. Với đội nhỏ, một công cụ trưởng thành thường rẻ hơn tự viết; câu hỏi đầu tiên vẫn là "đã thật
sự cần sharding chưa" (mục 1.2).

## 7. Đối chiếu PostgreSQL

| | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| Partitioning | `PARTITION BY RANGE/LIST/HASH/KEY` trên một bảng | *Declarative partitioning*: bảng cha `PARTITION BY RANGE/LIST/HASH`, mỗi partition là một bảng con tạo bằng `CREATE TABLE ... PARTITION OF` |
| Partition mặc định cho giá trị không khớp | Chỉ `MAXVALUE` với RANGE; LIST không có | Có `DEFAULT` partition |
| Unique key | Phải chứa mọi cột partition | Cũng phải chứa cột partition key |
| Foreign key | Không hỗ trợ trên bảng partition InnoDB | Hỗ trợ |
| Xoá dữ liệu cũ | `DROP PARTITION` | `DROP TABLE` partition con (hoặc `DETACH PARTITION` trước nếu muốn giữ lại dữ liệu) |
| Sharding có sẵn | Vitess (bên ngoài) | Citus (extension) |
| Sinh UUIDv7 | Không có hàm | `uuidv7()` |

Điểm chung đáng nhớ: ở cả hai, partitioning vẫn nằm trong **một** server, và uniqueness chỉ được đảm
bảo nếu khoá chứa cột partition.

## 8. Case study

Phần này chỉ nêu những gì có trong bài blog kỹ thuật chính thức của từng công ty (link ở Đọc thêm).

### 8.1 Notion: shard Postgres theo workspace

Bài *Herding elephants* (10/2021) và *The Great Re-shard* (7/2023):

- **Vì sao:** database Postgres nguyên khối lớn tới mức `VACUUM` bị đình trệ và có nguy cơ
  *transaction ID wraparound* (có thể buộc Postgres ngừng nhận ghi).
- **Cách làm:** sharding ở tầng ứng dụng. Shard key là **workspace ID**: mỗi block thuộc đúng một
  workspace, người dùng thường chỉ truy vấn trong một workspace, nên tránh được hầu hết join xuyên
  shard. Mọi bảng liên quan tới bảng `block` được shard cùng khoá.
- **Con số:** **480 shard logic** trên **32 database vật lý**, mỗi database 15 shard logic, mỗi shard
  logic là một *schema* Postgres. Chọn 480 vì có nhiều ước số, thêm máy theo bước đều (32, 40, 48...) mà
  không bị buộc phải nhân đôi như với 512.
- **Di chuyển:** ghi kép qua audit log, backfill dữ liệu cũ (khoảng ba ngày), kiểm tra bằng so mẫu và
  dark read, rồi chuyển với khoảng năm phút downtime.
- **Năm 2023:** CPU một số shard vượt 90% lúc cao điểm, nên tăng từ **32 lên 96** máy. Số shard logic giữ
  nguyên; mỗi máy giờ giữ 5 schema thay vì 15. Dữ liệu được chép bằng logical replication, cutover qua
  PgBouncer, kiểm tra bằng dark read trước khi chuyển. Đây chính là lợi ích của "logical shard nhiều
  hơn physical shard" ở mục 5.3.

### 8.2 Figma: từ vertical partitioning tới horizontal sharding

Bài *How Figma's databases team lived to tell the scale* (3/2024):

- Năm 2020 Figma chạy một database Postgres trên instance vật lý lớn nhất của AWS. Tầng database tăng
  gần 100 lần từ 2020.
- Bước đầu (tới cuối 2022): cache, read replica và **vertical partitioning**: tách các nhóm bảng liên
  quan (như "Figma files", "Organizations") sang các database riêng, được khoảng một chục database. Họ
  gọi đây là bước nhanh, hiệu quả cao, mua thêm thời gian. (Lưu ý: "vertical partitioning" ở đây nghĩa
  là chia **bảng** ra nhiều database, khác với partitioning theo cột trong mục 3.1.)
- Vertical partitioning không chia được **một** bảng; vài bảng đã lên nhiều TB, hàng tỉ dòng, gần chạm
  giới hạn IOPS của RDS. Nên họ chuyển sang **horizontal sharding**.
- **Colo**: nhóm bảng dùng chung shard key và cách bố trí vật lý; trong một colo, join và transaction
  đầy đủ được hỗ trợ khi giới hạn trong một giá trị shard key. Vài shard key được dùng như UserID,
  FileID, OrgID; định tuyến theo **hash** của shard key để phân bố đều (vì nhiều ID là tự tăng hoặc
  kiểu Snowflake).
- **DBProxy**: một dịch vụ viết bằng Go nằm giữa ứng dụng và PgBouncer, có bộ phân tích và lập kế
  hoạch truy vấn.
- **Shard logic trước, shard vật lý sau**: trước tiên dùng view Postgres để giả lập shard trên database
  chưa tách, triển khai dần bằng feature flag và lùi lại được trong vài giây; sau đó mới tách vật lý.
- Không hỗ trợ transaction nguyên tử xuyên shard.
- Bảng shard đầu tiên lên production vào 9/2023, mất khoảng chín tháng; lần failover gây khoảng mười
  giây gián đoạn một phần trên primary.

Bài học chung từ hai câu chuyện: cả hai đều đi qua các bậc rẻ hơn trước; chọn shard key theo đơn vị
nghiệp vụ mà truy vấn tự nhiên nằm gọn trong đó (workspace, file, org); và dành phần lớn công sức cho
việc **di chuyển an toàn** chứ không phải cho logic định tuyến.

## Lỗi thường gặp

1. **Shard hoặc partition trước khi tối ưu query.** Hầu hết sự cố quá tải được giải bằng index và sửa
   truy vấn (mục 1.2).
2. **Partition bảng rồi truy vấn không lọc theo cột partition.** Mọi partition bị đọc, chậm hơn bảng
   không partition (mục 3.6).
3. **Mong partition giữ `UNIQUE (email)` toàn cục.** Không được: unique key phải chứa cột partition
   (mục 3.7).
4. **Quên MySQL không hỗ trợ foreign key trên bảng partition InnoDB**, rồi phát hiện khi `ALTER` báo
   lỗi trên bảng đã có foreign key.
5. **Không tạo trước partition tương lai**, để dữ liệu dồn vào `pmax` và `REORGANIZE` sau đó phải di
   chuyển cả triệu dòng; hoặc không có `pmax` và `INSERT` báo lỗi vào ngày đầu tháng mới.
6. **Dùng `TIMESTAMP` cho cột định partition theo thời gian**, rồi phát hiện `RANGE COLUMNS` không nhận.
7. **Xoá dữ liệu cũ bằng một câu `DELETE` khổng lồ** thay vì batch hoặc `DROP PARTITION` (mục 3.8, 4.3).
8. **Shard theo khoá tăng dần bằng range**, tạo hot shard ở shard mới nhất (mục 5.2).
9. **Lấy trung bình của các trung bình** khi gộp kết quả từ nhiều shard (mục 5.5).
10. **Dùng UUIDv4 làm khoá chính InnoDB**, hoặc lưu UUID dạng `CHAR(36)` (mục 5.6).
11. **`hash mod số_server`** thay vì shard logic cố định, để mỗi lần thêm máy phải di chuyển gần hết dữ
    liệu (mục 5.3).

## Tóm tắt chương

- Khi quá tải, đo trước rồi đi theo thang chi phí tăng dần: tối ưu query/index, cache, read replica,
  scale dọc, archiving, partitioning, sharding.
- Scale dọc không cần sửa code nhưng có trần; scale ngang không có trần rõ nhưng đẩy độ phức tạp sang
  ứng dụng.
- Partitioning chia **một bảng trong một server**. MySQL 8.4 có `RANGE`, `RANGE COLUMNS`, `LIST`,
  `LIST COLUMNS`, `HASH`, `KEY`; chỉ InnoDB và NDB hỗ trợ.
- Pruning chỉ xảy ra khi `WHERE` lọc trực tiếp trên cột partition; xem cột `partitions` của `EXPLAIN`.
- Giới hạn: mọi unique key (kể cả khoá chính) phải chứa mọi cột partition; bảng partition InnoDB không
  có foreign key; không `FULLTEXT`; tối đa 8192 partition.
- Lợi ích lớn nhất: `DROP PARTITION` xoá cả tháng dữ liệu gần như tức thì và trả lại dung lượng.
  `RANGE` chỉ `ADD PARTITION` ở đầu cao; dùng `REORGANIZE PARTITION` để tách `pmax`.
- Archiving: chuyển dữ liệu lạnh theo batch nhỏ, hoặc `EXCHANGE PARTITION` + `DROP PARTITION`.
- Sharding chia dữ liệu ra **nhiều server**; shard key quyết định gần như mọi thứ. Truy vấn và
  transaction xuyên shard đắt hoặc không có; unique toàn cục phải tự lo.
- ID toàn cục: chia bước auto-increment, Snowflake (64 bit), UUIDv7 (128 bit, có timestamp ở đầu);
  tránh UUIDv4 làm khoá chính InnoDB.
- Nhiều shard logic trên ít server vật lý giúp resharding chỉ là chuyển shard logic.
- Vitess (MySQL) và Citus (PostgreSQL) làm sẵn phần định tuyến và resharding.

## Câu hỏi tự kiểm tra

1. Một hệ thống có CPU database 95%, tải 90% là đọc. Bạn thử những gì, theo thứ tự nào, và vì sao
   sharding không phải bước đầu?
2. Nêu ba điểm khác nhau giữa partitioning và sharding.
3. Ở bảng `orders_p`, dòng có `created_at = '2026-04-01 00:00:00'` vào partition nào trước và sau khi
   chạy `REORGANIZE PARTITION` ở mục 3.8?
4. Vì sao MySQL đòi mọi unique key chứa cột partition? Hệ quả với `UNIQUE (email)` là gì?
5. Truy vấn nào trên `orders_p` được pruning, truy vấn nào không:
   `WHERE id = 5`; `WHERE created_at BETWEEN '2026-02-10' AND '2026-02-20'`;
   `WHERE DATE(created_at) = '2026-02-10'`?
6. Vì sao `DROP PARTITION` nhanh hơn nhiều so với `DELETE` cùng số dòng? Nó mất gì so với `DELETE`?
7. Vì sao không thể `ADD PARTITION` khi bảng `RANGE` đã có partition `MAXVALUE`? Làm thế nào thay thế?
8. Năm tiêu chí của một shard key tốt là gì? Cho ví dụ một shard key tệ và giải thích.
9. Tại sao gộp `AVG` từ nhiều shard không được lấy trung bình các trung bình?
10. So sánh Snowflake ID, UUIDv4, UUIDv7 khi làm khoá chính InnoDB.
11. Notion chọn 480 shard logic thay vì 512 vì sao? Điều đó giúp gì cho lần resharding năm 2023?
12. "Vertical partitioning" trong bài của Figma khác gì với vertical partitioning mà MySQL nói không hỗ
    trợ?

## Bài tập

1. **Bảng log theo ngày.** Thiết kế bảng `access_log` (id, user_id, path, created_at) partition theo
   ngày cho 7 ngày gần nhất cộng `pmax`. Viết câu `REORGANIZE` để thêm ngày mới và câu `DROP` để bỏ ngày
   cũ nhất. Chạy `EXPLAIN` cho một truy vấn trong một ngày và một truy vấn theo `user_id`; ghi lại cột
   `partitions`.
2. **Thử giới hạn.** Trên bảng `orders_p`, thử thêm `UNIQUE (customer_id)`, rồi thử thêm một foreign
   key tới bảng `customers`. Ghi lại thông báo lỗi và giải thích từng cái.
3. **Archiving.** Tạo bảng `orders` không partition với vài nghìn dòng trải trên hai năm (dùng
   recursive CTE ở [chương 09](09-subquery-cte-union.md)). Viết script PHP chạy vòng lặp batch ở mục 4.3
   cho tới hết, in số dòng đã chuyển sau mỗi batch. So `COUNT(*)` hai bảng trước và sau.
4. **Gộp kết quả xuyên shard.** Tạo ba database `shard_0`, `shard_1`, `shard_2` cùng bảng `orders`,
   chia dữ liệu theo `customer_id % 3`. Viết script PHP trả lời: tổng doanh thu, giá trị trung bình mỗi
   đơn, và top 5 đơn lớn nhất toàn hệ thống. Kiểm tra bằng cách chạy cùng truy vấn trên một bảng gộp.
5. **Sinh Snowflake ID.** Viết hàm PHP sinh ID kiểu Snowflake (41/10/12 bit) với epoch tuỳ chọn. Sinh
   10.000 ID trong một vòng lặp và kiểm tra: không trùng, tăng dần. Điều gì xảy ra nếu bạn sinh hơn
   4096 ID trong một mili giây?

## Đọc thêm

- MySQL 8.4 Reference Manual, chương Partitioning:
  [Overview](https://dev.mysql.com/doc/refman/8.4/en/partitioning-overview.html),
  [RANGE](https://dev.mysql.com/doc/refman/8.4/en/partitioning-range.html),
  [LIST](https://dev.mysql.com/doc/refman/8.4/en/partitioning-list.html),
  [COLUMNS](https://dev.mysql.com/doc/refman/8.4/en/partitioning-columns.html),
  [KEY](https://dev.mysql.com/doc/refman/8.4/en/partitioning-key.html),
  [NULL handling](https://dev.mysql.com/doc/refman/8.4/en/partitioning-handling-nulls.html),
  [Management of RANGE and LIST Partitions](https://dev.mysql.com/doc/refman/8.4/en/partitioning-management-range-list.html),
  [Partition Pruning](https://dev.mysql.com/doc/refman/8.4/en/partitioning-pruning.html),
  [Obtaining Information About Partitions](https://dev.mysql.com/doc/refman/8.4/en/partitioning-info.html),
  [Restrictions and Limitations](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html),
  [Partitioning Keys, Primary Keys, and Unique Keys](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-partitioning-keys-unique-keys.html),
  [Functions Permitted](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations-functions.html).
- PostgreSQL 18: [Table Partitioning](https://www.postgresql.org/docs/18/ddl-partitioning.html),
  [UUID Functions](https://www.postgresql.org/docs/18/functions-uuid.html).
- [RFC 9562: Universally Unique IDentifiers](https://www.rfc-editor.org/rfc/rfc9562) (UUIDv7).
- Twitter, [snowflake (bản 2010)](https://github.com/twitter-archive/snowflake/tree/snowflake-2010) (README mô tả cấu trúc 41/10/12 bit).
- [Vitess documentation](https://vitess.io/docs/) (mục Concepts: Keyspace, Shard, VSchema, Vindex).
- [Citus documentation](https://docs.citusdata.com/) (Distributed tables, Reference tables, Co-location).
- Notion: [Herding elephants: lessons learned from sharding Postgres at Notion](https://www.notion.com/blog/sharding-postgres-at-notion) (2021),
  [The Great Re-shard](https://www.notion.com/blog/the-great-re-shard) (2023).
- Figma: [How Figma's databases team lived to tell the scale](https://www.figma.com/blog/how-figmas-databases-team-lived-to-tell-the-scale/) (2024).
- Martin Kleppmann, *Designing Data-Intensive Applications*, chương 6 (Partitioning).
