# Chương 16. Bên trong InnoDB

> [← Mục lục](README.md) · [← Chương 15: Lock và deadlock](15-lock-deadlock.md) · [Chương 17: View, stored procedure, function, trigger, event →](17-view-procedure-trigger.md)

**Bạn sẽ học được:**

- Một câu SQL đi qua những tầng nào trong MySQL server (connection, parser, optimizer, executor,
  storage engine API), và vì sao MySQL tách "tầng SQL" khỏi "tầng lưu trữ".
- Dữ liệu InnoDB nằm trên đĩa ra sao: tablespace, segment, extent, page 16 KB, row format, và chuyện
  gì xảy ra với cột `TEXT`/`BLOB` dài (off-page).
- Buffer pool hoạt động thế nào: LRU có midpoint, dirty page, flush, checkpoint.
- Redo log (write-ahead log) giúp InnoDB sống sót qua crash ra sao; undo log phục vụ rollback và
  MVCC ra sao; purge và history list length là gì và vì sao một transaction quên đóng làm cả DB chậm.
- Binlog khác redo log ở đâu, internal two-phase commit giữ hai log khớp nhau thế nào, doublewrite
  buffer chống page ghi dở ra sao, và hai biến cấu hình độ bền quan trọng nhất
  (`innodb_flush_log_at_trx_commit`, `sync_binlog`).
- Đối chiếu với PostgreSQL (heap, WAL, VACUUM, bloat, xid wraparound) và làm quen với LSM tree.

**Cần biết trước:** [Chương 11](11-index.md) (B+tree, clustered index, secondary index),
[Chương 13](13-transaction-acid.md) (transaction, ACID, COMMIT/ROLLBACK),
[Chương 14](14-isolation-mvcc.md) (isolation level, snapshot, MVCC ở mức người dùng),
[Chương 15](15-lock-deadlock.md) (lock). Chương này không cần dữ liệu mẫu phức tạp; các mục có
ví dụ chạy được sẽ tự tạo bảng riêng.

Cách chạy thử: mọi lệnh SQL trong chương chạy trên MySQL 8.4. Nếu chưa có, dựng nhanh bằng Docker
(chạy ở terminal máy bạn):

```bash
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
docker exec -it my84 mysql -uroot -proot
```

Một số mục cần xem file trên đĩa của MySQL; khi đó dùng `docker exec -it my84 bash` rồi vào thư mục
dữ liệu (`/var/lib/mysql` trong image chính thức).

---

## 1. Vì sao phải nhìn vào bên trong

### 1.1 Câu hỏi mà tầng SQL không trả lời được

Ở các chương trước, bạn làm việc với database như một "hộp đen": gửi câu SQL vào, nhận kết quả ra.
Như vậy là đủ để viết query đúng. Nhưng khi hệ thống chạy thật, sẽ có những câu hỏi mà chỉ nhìn câu
SQL thì không trả lời được:

- Vì sao `COMMIT` trả về OK xong, máy mất điện ngay sau đó, mà dữ liệu vẫn còn? Lúc `COMMIT` trả về,
  dữ liệu đã thật sự nằm trong file bảng chưa?
- Vì sao query hôm qua chạy 2 ms, hôm nay sau khi restart server lại chạy 200 ms, rồi vài phút sau
  lại nhanh?
- Vì sao một transaction chỉ `SELECT` mà quên `COMMIT` trong cả buổi chiều có thể làm mọi query khác
  chậm dần?
- Vì sao xoá một nửa bảng mà file `.ibd` trên đĩa không nhỏ đi?
- Vì sao tắt `sync_binlog` cho "nhanh hơn" lại làm replica lệch dữ liệu sau một lần mất điện?
- Vì sao Postgres cần `VACUUM` còn MySQL thì không nói nhiều về nó?

Tất cả các câu trả lời đều nằm ở tầng lưu trữ: dữ liệu được tổ chức thế nào trên đĩa, được giữ
thế nào trong RAM, và các loại log nào được ghi lúc nào. Chương này mở hộp đen đó ra, với InnoDB là
storage engine mặc định của MySQL 8.4.

### 1.2 Hai bài toán gốc mà mọi database phải giải

Trước khi đi vào chi tiết InnoDB, hãy nhìn hai bài toán gốc. Mọi thành phần trong chương này
(buffer pool, redo log, undo log, doublewrite, binlog) đều là lời giải cho một trong hai.

**Bài toán 1: đĩa chậm, RAM nhanh nhưng mất khi tắt máy.**

- Đọc một vùng nhỏ trên SSD mất cỡ vài chục tới vài trăm micro giây; đọc từ RAM mất cỡ trăm nano
  giây. Chênh nhau hàng trăm tới hàng nghìn lần (con số cụ thể tuỳ phần cứng, ở đây chỉ cần nhớ thứ
  bậc).
- Nên database muốn làm việc trên RAM càng nhiều càng tốt: đọc dữ liệu từ đĩa lên RAM một lần, rồi
  đọc và sửa trên RAM.
- Nhưng dữ liệu chỉ nằm trên RAM thì mất điện là mất. Mà chữ D trong ACID (durability, chương 13)
  hứa rằng đã commit là không mất.

**Bài toán 2: nhiều người cùng đọc và ghi một lúc, và có thể bỏ dở giữa chừng.**

- Một transaction đang sửa dở mà người khác đọc thì nên thấy gì? (chương 14)
- Transaction sửa 1000 dòng rồi `ROLLBACK`, hoặc server crash giữa chừng: làm sao đưa 1000 dòng về
  như cũ?

InnoDB giải hai bài toán này bằng một bộ cơ chế khá kinh điển, và PostgreSQL, SQL Server, Oracle đều
có các cơ chế tương tự dưới tên khác. Học kỹ InnoDB, bạn sẽ đọc được kiến trúc của hầu hết các
database quan hệ khác.

| Bài toán | Cơ chế của InnoDB | Mục trong chương |
|---|---|---|
| Đọc ghi nhanh trên RAM | Buffer pool | Mục 4 |
| Ghi page xuống đĩa chậm, nhưng commit phải bền | Redo log (write-ahead log) | Mục 5 |
| Rollback, và cho người khác đọc bản cũ | Undo log, MVCC, purge | Mục 6 |
| Page bị ghi dở khi mất điện | Doublewrite buffer | Mục 7 |
| Ghi secondary index ngẫu nhiên tốn I/O | Change buffer (khái niệm) | Mục 8 |
| Gửi thay đổi cho replica, khôi phục theo thời điểm | Binlog và two-phase commit nội bộ | Mục 9 |

### 1.3 Thuật ngữ nền cần nắm trước

Một vài từ sẽ xuất hiện liên tục trong chương, định nghĩa trước cho chắc:

- *Page* (trang): đơn vị nhỏ nhất InnoDB đọc từ đĩa và ghi xuống đĩa. Mặc định 16 KB. InnoDB không
  bao giờ đọc "một dòng" từ đĩa; nó đọc cả page chứa dòng đó.
- *Flush*: ghi một thứ đang ở RAM xuống đĩa. "Flush dirty page" là ghi các page đã bị sửa xuống file.
- *fsync*: lời gọi hệ điều hành yêu cầu đẩy dữ liệu của một file từ cache của OS xuống thiết bị lưu
  trữ thật, và chỉ trả về khi thiết bị báo đã ghi xong. Ghi file bằng `write()` thông thường chỉ đưa
  dữ liệu vào cache của OS (page cache); nếu mất điện ngay sau đó, dữ liệu có thể chưa xuống đĩa.
  Chỉ sau `fsync` (hoặc các biến thể như `fdatasync`, hay mở file với cờ đồng bộ) thì mới yên tâm.
  Phân biệt "ghi vào file" và "fsync" là chìa khoá để hiểu mục 5 và mục 9.
- *Ghi tuần tự* (sequential write) và *ghi ngẫu nhiên* (random write): ghi nối liên tiếp vào cuối
  một file rẻ hơn nhiều so với ghi nhiều mảnh nhỏ rải rác ở các vị trí khác nhau, kể cả trên SSD
  (ít hơn HDD nhưng vẫn đáng kể, vì có thể gom lô và ít lần fsync hơn).
- *Crash*: tiến trình `mysqld` chết đột ngột (bị kill, lỗi) hoặc cả máy mất điện. Hai trường hợp khác
  nhau: mysqld chết thì cache của OS vẫn còn và sẽ được OS ghi xuống đĩa; mất điện thì cả cache của
  OS cũng mất. Mục 9.5 sẽ dùng đúng sự khác biệt này.

---

## 2. Kiến trúc MySQL server: một câu SQL đi đâu

### 2.1 Hai tầng: tầng SQL và tầng storage engine

MySQL chia mình thành hai tầng lớn:

- *Tầng server* (còn gọi là tầng SQL): nhận kết nối, kiểm tra quyền, phân tích câu SQL, chọn cách
  chạy, tính toán biểu thức, sắp xếp, gom nhóm, ghi binlog. Tầng này không biết dữ liệu nằm trên
  đĩa thế nào.
- *Tầng storage engine*: thật sự lưu và lấy dữ liệu: tổ chức file, index, cache, transaction, lock
  dòng, crash recovery. Tầng này không hiểu câu SQL.

Hai tầng nói chuyện với nhau qua một bộ hàm chung gọi là *storage engine API* (trong mã nguồn MySQL
là lớp `handler`). Tầng server gọi kiểu "mở bảng này", "đọc dòng tiếp theo theo index này", "ghi
dòng này", "sửa dòng này"; engine nào cũng phải cài đặt các hàm đó theo cách của mình.

```
        Ứng dụng (PHP/PDO, mysql client, ...)
                     |  giao thức MySQL qua TCP (cổng 3306) hoặc Unix socket
                     v
 +---------------------------------------------------------------+
 |                     TẦNG SERVER (SQL layer)                    |
 |                                                               |
 |  Connection handling: xác thực, mỗi connection một thread     |
 |        |                                                      |
 |        v                                                      |
 |  Parser: chữ SQL -> cây cú pháp (lỗi 1064 sinh ra ở đây)       |
 |        |                                                      |
 |        v                                                      |
 |  Resolver / kiểm tra: bảng, cột có tồn tại? có quyền không?    |
 |        |                                                      |
 |        v                                                      |
 |  Optimizer: chọn index, thứ tự join, cách chạy (chương 12)    |
 |        |                                                      |
 |        v                                                      |
 |  Executor: chạy kế hoạch, tính biểu thức, sort, group, ...    |
 |        |                                     \                |
 |        |                                      binlog          |
 +--------|------------------------------------------------------+
          |  Storage engine API (handler): đọc dòng, ghi dòng, ...
          v
 +-------------+  +-----------+  +--------+  +----------------+
 |   InnoDB    |  |  MyISAM   |  | MEMORY |  | CSV, ARCHIVE,  |
 | (mặc định)  |  |           |  |        |  | BLACKHOLE, ... |
 +-------------+  +-----------+  +--------+  +----------------+
          |
          v
   File trên đĩa (.ibd, redo log, undo tablespace, ...)
```

Kiến trúc này gọi là *pluggable storage engine*: engine là một plugin, có thể nạp hoặc gỡ khi server
đang chạy, và mỗi bảng tự chọn engine của mình bằng `ENGINE=...` trong `CREATE TABLE`. Xem server
đang có những engine nào:

```sql
SHOW ENGINES;
-- Cột Support: DEFAULT cho InnoDB (engine mặc định), YES cho engine dùng được, NO cho engine không có.
-- Cột Transactions: InnoDB là YES; MyISAM, MEMORY, CSV ... là NO.
```

### 2.2 Đi qua từng bước của một câu SELECT

Lấy câu sau làm ví dụ:

```sql
SELECT name FROM users WHERE email = 'an@example.com';
```

1. **Connection.** Ứng dụng mở kết nối, gửi user và mật khẩu. Server xác thực, rồi gán một thread
   để phục vụ connection đó. Mặc định MySQL dùng mô hình *một thread cho mỗi connection*; thread
   được tái sử dụng qua một cache thread (`thread_cache_size`) để đỡ chi phí tạo mới. Vì mỗi
   connection có thread và bộ nhớ riêng, mở hàng nghìn connection cùng lúc là tốn kém; chương 19 bàn
   về connection pool phía ứng dụng.
2. **Parser.** Câu SQL (một chuỗi ký tự) được tách thành token và dựng thành cây cú pháp. Gõ sai
   cú pháp (`SELEC name ...`) thì dừng ở đây với lỗi 1064 (`You have an error in your SQL syntax`).
3. **Resolver.** Server tra *data dictionary* để biết bảng `users` có tồn tại, có cột `name`, `email`
   không, user hiện tại có quyền `SELECT` không. Sai tên cột thì lỗi 1054 (`Unknown column`), sai tên
   bảng thì lỗi 1146 (`Table ... doesn't exist`).
4. **Optimizer.** Dựa trên index có sẵn và thống kê, ước lượng chi phí các cách chạy rồi chọn cách
   rẻ nhất: dùng index trên `email` hay quét cả bảng. `EXPLAIN` cho bạn xem kết quả bước này
   (chương 12).
5. **Executor.** Chạy kế hoạch đã chọn. Khi cần dữ liệu, nó gọi storage engine qua handler API, đại
   ý: "InnoDB ơi, tìm trong index `idx_email` dòng đầu tiên có giá trị `'an@example.com'`", rồi
   "cho dòng tiếp theo", cho tới khi engine báo hết. Với mỗi dòng nhận về, executor kiểm tra phần
   điều kiện còn lại (nếu có), lấy cột `name`, gửi về client.

Với câu ghi (`INSERT`, `UPDATE`, `DELETE`), các bước 1 tới 4 giống hệt; ở bước 5 executor gọi các
hàm ghi của engine, và khi commit thì tầng server còn ghi thêm binlog (mục 9).

### 2.3 Cái gì thuộc tầng nào

Biết một tính năng nằm ở tầng nào giúp bạn đoán được hành vi của nó:

| Thuộc tầng server (chung cho mọi engine) | Thuộc storage engine (InnoDB tự làm) |
|---|---|
| Phân tích câu SQL, optimizer, executor | Cách lưu dòng trên đĩa, page, file |
| Kiểm tra quyền (chương 18) | Index: B+tree, clustered index (chương 11) |
| Hàm SQL, view, stored procedure, trigger (chương 17) | Transaction, commit, rollback |
| Binlog, replication (chương 22) | Lock dòng, MVCC (chương 14, 15) |
| Data dictionary (lưu trong bảng InnoDB, xem dưới) | Redo log, undo log, crash recovery |
| Sort, group, bảng tạm nội bộ | Buffer pool (cache dữ liệu) |

Vài hệ quả thực tế:

- Transaction là chuyện của engine. Nếu một transaction sửa cả bảng InnoDB lẫn bảng MyISAM rồi
  `ROLLBACK`, chỉ phần InnoDB được hoàn tác; phần MyISAM đã ghi là ghi luôn (MySQL trả về một warning
  báo rằng một số bảng không transactional không rollback được). Vì vậy hãy dùng InnoDB cho mọi bảng
  nghiệp vụ.
- Có hai loại log khác nhau ở hai tầng: binlog (tầng server, engine nào cũng có) và redo log
  (riêng InnoDB). Mục 9 giải thích vì sao phải có cả hai và cách giữ chúng khớp nhau.
- Từ MySQL 8.0, thông tin về bảng, cột, index (*metadata*) được lưu trong *data dictionary* dạng
  bảng InnoDB, nên có tính transactional và crash-safe. Các file metadata cũ như `.frm` của 5.7 đã
  bị bỏ. Nhờ đó MySQL 8 có *atomic DDL*: một câu DDL hoặc xong hẳn, hoặc như chưa chạy.
- Query cache (cache kết quả câu `SELECT` ở tầng server) đã bị gỡ hẳn từ MySQL 8.0. Nếu đọc tài
  liệu cũ nhắc `query_cache_size`, đó là chuyện của 5.7 trở về trước. Cache quan trọng còn lại là
  buffer pool của InnoDB, cache theo page chứ không theo kết quả query.

### 2.4 Vì sao InnoDB là mặc định

Thời MySQL 5.1 trở về trước, engine mặc định là MyISAM. Từ 5.5, mặc định chuyển sang InnoDB, và tài
liệu MySQL 8.4 khuyến nghị dùng InnoDB cho mọi bảng trừ trường hợp đặc biệt. So sánh ngắn:

| Tiêu chí | InnoDB | MyISAM |
|---|---|---|
| Transaction (COMMIT/ROLLBACK) | Có | Không |
| Crash recovery | Tự động nhờ redo log | Không đảm bảo, có thể phải sửa bảng bằng tay |
| Mức lock khi ghi | Lock dòng | Lock cả bảng |
| Foreign key | Có | Không |
| MVCC (đọc không chặn ghi) | Có | Không |
| Cách tổ chức bảng | Clustered index theo PK | Heap (dữ liệu và index để riêng) |

Các engine khác có công dụng hẹp: `MEMORY` giữ bảng trong RAM (mất khi restart), `CSV` lưu thành
file CSV, `ARCHIVE` nén để lưu trữ, `BLACKHOLE` nhận ghi rồi bỏ đi (vẫn ghi binlog). Bạn sẽ hiếm khi
cần tới chúng. Phần còn lại của chương chỉ nói về InnoDB.

---

## 3. Dữ liệu nằm trên đĩa thế nào

### 3.1 Tổng quan: các cấu trúc trên đĩa và trong RAM

Tài liệu MySQL chia InnoDB thành hai nhóm: *in-memory structures* (nằm trong RAM) và *on-disk
structures* (nằm trên đĩa). Sơ đồ dưới đây là "bản đồ" cho cả chương; mỗi ô sẽ được giải thích ở
một mục.

```
 RAM (mất khi tắt máy)
 +-------------------------------------------------------------------+
 |  Buffer pool (mục 4)                                               |
 |    page dữ liệu và index (16 KB mỗi page), page undo, ...          |
 |    LRU list, flush list (dirty page)                              |
 |    [Adaptive hash index (mục 8)]   [Change buffer (mục 8)]        |
 |                                                                   |
 |  Log buffer (mục 5): redo đang chờ ghi xuống đĩa                  |
 +-------------------------------------------------------------------+
            |                         |
            v                         v
 ĐĨA (bền)
 +---------------------+  +------------------------+  +-------------------+
 | Redo log (mục 5)    |  | Doublewrite (mục 7)    |  | Undo tablespace   |
 | #innodb_redo/       |  | #ib_16384_0.dblwr, ... |  | undo_001, undo_002|
 +---------------------+  +------------------------+  | (mục 6)           |
                                                       +-------------------+
 +--------------------------------------------------------------------+
 | Tablespace: ibdata1 (system), mysql.ibd (data dictionary),         |
 | <db>/<bảng>.ibd (file-per-table), ibtmp1 và #innodb_temp (tạm)      |
 +--------------------------------------------------------------------+

 Tầng server (không thuộc InnoDB): binlog.000001, binlog.000002, ... (mục 9)
```

### 3.2 Tablespace: các file chứa dữ liệu

*Tablespace* là một "kho chứa" logic gồm một hoặc nhiều file trên đĩa. InnoDB có mấy loại:

| Tablespace | File (mặc định, trong thư mục dữ liệu) | Chứa gì |
|---|---|---|
| System tablespace | `ibdata1` | Change buffer; và bảng nếu cố tình tạo trong đó |
| File-per-table | `<tên_db>/<tên_bảng>.ibd` | Một bảng: clustered index và mọi secondary index của nó |
| General tablespace | Tạo bằng `CREATE TABLESPACE` | Nhiều bảng chung một file (ít dùng) |
| Undo tablespace | `undo_001`, `undo_002` | Undo log (mục 6) |
| Temporary tablespace | `ibtmp1` (global), thư mục `#innodb_temp` (`.ibt`, theo session) | Bảng tạm của người dùng và bảng tạm nội bộ trên đĩa |
| Data dictionary | `mysql.ibd` | Metadata của mọi bảng (mục 2.3) |

`innodb_file_per_table` bật mặc định, nên mỗi bảng bạn tạo có một file `.ibd` riêng. Lợi ích:
`DROP TABLE` hoặc `TRUNCATE TABLE` trả chỗ trống về cho hệ điều hành ngay; còn nếu mọi bảng dồn trong
`ibdata1` thì file đó chỉ phình ra chứ không co lại.

Ở MySQL 5.x, `ibdata1` còn chứa undo log và doublewrite buffer, nên là file "phình mãi". Từ 8.0, undo
đã sang undo tablespace riêng và (từ 8.0.20) doublewrite sang file riêng, nên `ibdata1` nhỏ đi nhiều.
Đọc tài liệu cũ nói "ibdata1 to vì undo" thì nhớ đó là chuyện thời 5.x.

Thử xem (trong mysql client):

```sql
CREATE DATABASE IF NOT EXISTS lab16;
USE lab16;
CREATE TABLE pages_demo (
  id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  note VARCHAR(200) NOT NULL
);

SELECT NAME, ROW_FORMAT, SPACE_TYPE
FROM information_schema.INNODB_TABLES
WHERE NAME = 'lab16/pages_demo';
-- Kết quả mong đợi: lab16/pages_demo | Dynamic | Single
-- (Single: bảng có tablespace riêng, tức file-per-table)
```

Và trong container (`docker exec -it my84 bash`):

```bash
ls -l /var/lib/mysql/lab16/          # thấy pages_demo.ibd
ls /var/lib/mysql/ | head -50        # thấy ibdata1, mysql.ibd, undo_001, undo_002, #innodb_redo, ...
```

### 3.3 Page, extent, segment

Bên trong một tablespace, dữ liệu được tổ chức theo ba cấp:

- *Page*: 16 KB mặc định (đặt bằng `innodb_page_size` lúc khởi tạo instance, các giá trị hợp lệ là
  4, 8, 16, 32, 64 KB; mọi tablespace trong instance dùng chung một cỡ page, và không đổi được sau khi
  đã khởi tạo).
- *Extent*: nhóm page liên tiếp, 1 MB với page 16 KB trở xuống (tức 64 page 16 KB). InnoDB cấp phát
  theo extent để page của cùng một index nằm gần nhau trên đĩa, giúp đọc tuần tự.
- *Segment*: một "file con" trong tablespace. Mỗi index có hai segment: một cho các page không phải
  lá (non-leaf) của B+tree, một cho page lá. Page lá của clustered index chứa dữ liệu thật, để
  chúng liền nhau giúp quét bảng tuần tự hiệu quả hơn.

Theo tài liệu: khi một segment lớn lên, 32 page đầu được cấp từng page một; sau đó InnoDB cấp cả
extent.

```
 pages_demo.ibd
 +--------- extent 0 (1 MB) ---------+--------- extent 1 ---------+---
 | p0 | p1 | p2 | p3 | ... | p63     | p64 | ...                   |
 +-----------------------------------+----------------------------+---
   ^ vài page đầu là page quản lý (bitmap, thông tin segment, ...)
   các page còn lại thuộc segment non-leaf hoặc segment leaf của từng index
```

### 3.4 Bên trong một page index

Mọi thứ trong InnoDB là index: bảng chính là clustered index (B+tree sắp theo PK, chương 11), mỗi
secondary index là một B+tree khác. Mỗi node của cây là một page. Cấu trúc một page index (theo bài
viết của Jeremy Cole, người đã giải phẫu định dạng file InnoDB):

```
 +--------------------------------------------------+  offset 0
 | FIL header (38 byte): checksum, số page,          |
 |   page trước / page sau cùng tầng, LSN lần sửa    |
 |   cuối, loại page, id tablespace                  |
 +--------------------------------------------------+
 | INDEX header: id index, tầng (lá = 0), số record, |
 |   max trx id, vị trí chỗ trống, ...               |
 | FSEG header                                       |
 +--------------------------------------------------+
 | infimum  (record ảo, nhỏ hơn mọi key)             |
 | supremum (record ảo, lớn hơn mọi key)             |
 +--------------------------------------------------+
 | User records: các dòng thật, nối nhau theo thứ tự  |
 |   key bằng con trỏ "next record"                  |
 |   (thứ tự vật lý là thứ tự chèn, không phải key)   |
 +--------------------------------------------------+
 | Free space (chỗ trống)                            |
 +--------------------------------------------------+
 | Page directory: mảng con trỏ tới một số record     |
 |   (cứ khoảng 4 tới 8 record một con trỏ), để tìm   |
 |   nhị phân trong page                             |
 +--------------------------------------------------+
 | FIL trailer (8 byte): một phần checksum và LSN    |
 +--------------------------------------------------+  offset 16383
```

Những điểm đáng nhớ:

- Các page cùng tầng nối với nhau thành danh sách liên kết đôi (page trước, page sau). Nhờ vậy range
  scan đi dọc tầng lá mà không phải quay lên gốc.
- Trong một page, các record nối với nhau theo thứ tự key, từ infimum tới supremum. Tìm một key trong
  page: tìm nhị phân trên page directory để ra gần đúng vị trí, rồi đi tuyến tính vài record.
- Header có LSN của lần sửa cuối, và trailer giữ lại một phần LSN cùng checksum. Khi đọc page, InnoDB
  so checksum; header và trailer không khớp là dấu hiệu page bị ghi dở (mục 7).
- Theo tài liệu MySQL, khi chèn vào clustered index InnoDB cố chừa khoảng 1/16 page trống cho update
  sau. Chèn tuần tự (PK tăng dần) thì page đầy khoảng 15/16; chèn ngẫu nhiên (ví dụ UUIDv4 làm PK)
  thì page chỉ đầy từ 1/2 tới 15/16, vì page bị tách đôi liên tục (page split). Đó là một lý do
  chương 11 khuyên dùng PK tăng dần.
- Khi page vơi dưới ngưỡng `MERGE_THRESHOLD` (mặc định 50%) do xoá, InnoDB thử gộp nó với page
  bên cạnh.

### 3.5 Row format: một dòng được lưu thế nào

*Row format* quyết định cách các cột của một dòng được xếp thành byte. InnoDB có bốn loại:
`REDUNDANT` (cũ nhất, để tương thích), `COMPACT`, `DYNAMIC` (mặc định, biến
`innodb_default_row_format`), và `COMPRESSED` (như DYNAMIC nhưng nén page). Thực tế bạn chỉ gặp
DYNAMIC.

Một record trong clustered index với COMPACT/DYNAMIC gồm:

```
 | độ dài các cột   | bitmap NULL | header 5 byte | PK | DB_TRX_ID | DB_ROLL_PTR | các cột còn lại |
 | biến đổi (1-2 B  | (1 bit mỗi  | (next record, |    | 6 byte    | 7 byte      |                 |
 | mỗi cột)         | cột NULLable)| cờ xoá, ...) |    |           |             |                 |
```

- Bitmap NULL: mỗi cột cho phép NULL tốn 1 bit (làm tròn lên byte). Cột đang NULL không tốn thêm
  byte nào trong phần dữ liệu.
- Mỗi cột độ dài biến đổi (`VARCHAR`, `VARBINARY`, `TEXT`, `BLOB`) có 1 hoặc 2 byte ghi độ dài.
- Header 5 byte chứa con trỏ "next record" và các cờ, trong đó có cờ *delete-mark* (dòng đã bị đánh
  dấu xoá, chờ purge; mục 6).
- Hai cột ẩn: `DB_TRX_ID` (6 byte, id transaction sửa dòng lần cuối) và `DB_ROLL_PTR` (7 byte, trỏ
  vào undo log để lần ra phiên bản cũ). Đây chính là "móc" để MVCC hoạt động (mục 6). Bảng không có
  PK cũng không có cột UNIQUE NOT NULL nào thì có thêm `DB_ROW_ID` (6 byte) làm khoá ẩn.
- Record của secondary index chứa các cột của index cộng với các cột PK (không chứa `DB_TRX_ID`,
  `DB_ROLL_PTR`). Vì vậy PK dài làm mọi secondary index phình theo.

Ước lượng thô: một dòng `(id INT, note VARCHAR(200))` với note dài 50 ký tự ASCII tốn khoảng
4 (id) + 6 + 7 (cột ẩn) + 50 (note) + 1 (độ dài) + 5 (header) = 73 byte, chưa kể phần quản lý
của page. Một page 16 KB vì thế chứa cỡ hai trăm dòng như vậy. Đây là phép tính minh hoạ để có cảm
giác về con số, không phải số đo chính xác.

### 3.6 Dòng dài và off-page

Một page 16 KB phải chứa được ít nhất hai dòng (để B+tree còn ý nghĩa), nên InnoDB giới hạn phần dòng
nằm trong page ở mức hơi ít hơn nửa page: khoảng 8000 byte với page 16 KB.

Vậy cột `TEXT` 1 MB nằm ở đâu? Với DYNAMIC: khi dòng quá dài, InnoDB chọn **các cột dài nhất** đẩy
ra *overflow page* riêng (gọi là lưu *off-page*), trong record chỉ còn con trỏ 20 byte; cứ thế cho tới
khi record vừa giới hạn. Cột `TEXT`/`BLOB` không quá 40 byte luôn nằm ngay trong record. (COMPACT và
REDUNDANT thì khác: giữ 768 byte đầu trong record, phần còn lại mới ra overflow page.)

```
 Clustered index, page lá                         Overflow pages
 +-----------------------------------------+
 | id=7 | title='...' | body: [ptr 20 B] ---+----> [page 1 của body] -> [page 2] -> ...
 +-----------------------------------------+
```

Hệ quả:

- `SELECT *` trên bảng có cột `TEXT` lớn phải đọc thêm các overflow page, tốn I/O và chỗ trong
  buffer pool. Chỉ lấy cột cần dùng. Bảng hay đọc danh sách mà có một cột nội dung rất dài, tách cột
  đó sang bảng riêng 1-1 là cách tối ưu thường gặp.
- Có hai giới hạn kích thước dòng khác nhau, sinh hai thông báo lỗi khác nhau:
  1. Giới hạn của MySQL server: tổng kích thước khai báo các cột không quá 65.535 byte (không tính
     `TEXT`/`BLOB`, vì chúng chỉ góp 9 tới 12 byte). Vượt thì lỗi
     `ERROR 1118 (42000): Row size too large. The maximum row size for the used table type, not counting BLOBs, is 65535. ...`
  2. Giới hạn của InnoDB: phần nằm trong page không quá khoảng nửa page. Ví dụ trong tài liệu MySQL:
     bảng 33 cột `CHAR(255)` charset latin1 (8415 byte, cột cố định không đẩy off-page được) báo
     `ERROR 1118 (42000): Row size too large (> 8126). Changing some columns to TEXT or BLOB may help. ...`

```sql
-- Thử giới hạn 65.535 của server (ví dụ lấy từ tài liệu MySQL):
CREATE TABLE t_too_wide (c1 VARCHAR(65535) NOT NULL) ENGINE=InnoDB CHARACTER SET latin1;
-- ERROR 1118 (42000): Row size too large. The maximum row size for the used table type, ...
CREATE TABLE t_ok (c1 VARCHAR(65533) NOT NULL) ENGINE=InnoDB CHARACTER SET latin1;
-- Query OK (65.533 byte dữ liệu + 2 byte độ dài = 65.535)
DROP TABLE t_ok;
```

⚠️ Với `utf8mb4`, `VARCHAR(n)` tính tối đa 4n byte vào giới hạn 65.535, nên `VARCHAR(16383)` là
mức trần lý thuyết cho một cột utf8mb4 đơn lẻ, và hai cột `VARCHAR(10000)` utf8mb4 đã vượt.

### 3.7 Xoá dữ liệu mà file không nhỏ đi

Thử:

```sql
USE lab16;
-- Tạo nhanh khoảng 260 nghìn dòng (mỗi lần chạy câu INSERT ... SELECT số dòng gấp đôi):
INSERT INTO pages_demo (note) VALUES (REPEAT('x', 150));
INSERT INTO pages_demo (note) SELECT note FROM pages_demo;   -- chạy lại câu này 18 lần

SELECT FILE_SIZE, ALLOCATED_SIZE
FROM information_schema.INNODB_TABLESPACES WHERE NAME = 'lab16/pages_demo';

DELETE FROM pages_demo WHERE id % 2 = 0;   -- xoá một nửa
-- Đợi vài giây cho purge chạy, rồi xem lại: FILE_SIZE gần như không đổi.

OPTIMIZE TABLE pages_demo;
-- Với InnoDB, MySQL báo "Table does not support optimize, doing recreate + analyze instead":
-- bảng được dựng lại, file nhỏ đi.
```

Vì sao: `DELETE` chỉ đánh dấu xoá; purge (mục 6) mới gỡ record khỏi page, và chỗ trống được giữ lại
trong file để dòng mới dùng, không trả về hệ điều hành. Tài liệu MySQL nói rõ: chỗ trống đó dùng lại
được cho dữ liệu khác trong cùng tablespace hay không còn tuỳ việc xoá giải phóng từng page lẻ hay cả
extent; còn trả chỗ về hệ điều hành thì (với file-per-table) chỉ xảy ra khi `DROP`/`TRUNCATE` hoặc
dựng lại bảng. `OPTIMIZE TABLE` (với InnoDB
tương đương `ALTER TABLE ... FORCE`) dựng lại bảng thành file mới gọn hơn; trên bảng lớn nó tốn thời
gian và I/O, cách làm an toàn trên production bàn ở chương 20.

---

## 4. Buffer pool: bộ nhớ đệm của InnoDB

### 4.1 Buffer pool là gì

*Buffer pool* là vùng RAM nơi InnoDB giữ bản sao các page của bảng và index. Quy tắc cốt lõi: **mọi
đọc và ghi đều diễn ra trên page trong buffer pool**. Đĩa chỉ được chạm tới trong hai trường hợp:

- Cần một page chưa có trong RAM: đọc page đó từ file `.ibd` vào buffer pool (*page miss*).
- Một page đã bị sửa trong RAM cần được ghi lại xuống file (flush, mục 4.4).

```
  Query cần dòng id=42 của bảng orders
        |
        v
  Page chứa id=42 có trong buffer pool?  --có-->  đọc trên RAM (nhanh)
        | không
        v
  Đọc page 16 KB từ orders.ibd vào một chỗ trống trong buffer pool
  (nếu hết chỗ: loại bỏ một page ít dùng, mục 4.3), rồi đọc trên RAM
```

Vì vậy hiệu năng InnoDB phụ thuộc rất mạnh vào việc phần dữ liệu hay dùng (*working set*) có nằm gọn
trong buffer pool hay không. Một bảng 500 GB vẫn chạy nhanh nếu phần được truy cập thường xuyên chỉ vài
GB và vừa RAM.

### 4.2 Kích thước

- `innodb_buffer_pool_size` mặc định 128 MB (134217728 byte). Quá nhỏ cho production.
- Tài liệu MySQL viết: trên server chỉ chạy database, thường cấp tới 80% RAM cho buffer pool. Phần còn
  lại cho hệ điều hành, bộ nhớ theo từng connection (sort buffer, join buffer, bảng tạm), binlog cache.
  ⚠️ Cấp quá tay làm máy phải dùng swap, còn tệ hơn buffer pool nhỏ.
- Buffer pool lớn được chia thành nhiều *instance* (`innodb_buffer_pool_instances`) để các thread
  không tranh nhau một khoá chung. Ở MySQL 8.4, giá trị mặc định được tính tự động: 1 nếu pool không
  quá 1 GB, lớn hơn thì tính theo kích thước pool và số CPU (MySQL 8.0 mặc định là 8, hoặc 1 nếu pool
  nhỏ hơn 1 GB).
- Đổi kích thước khi đang chạy được: `SET GLOBAL innodb_buffer_pool_size = 8 * 1024 * 1024 * 1024;`
  (InnoDB thay đổi theo từng khối *chunk*, mặc định 128 MB một chunk, nên giá trị thật được làm tròn).
- `innodb_dedicated_server = ON` (mặc định OFF) cho InnoDB tự tính buffer pool và redo log theo RAM
  của máy; chỉ dùng khi máy dành riêng cho MySQL.

```sql
SELECT @@innodb_buffer_pool_size / 1024 / 1024 AS pool_mb,
       @@innodb_buffer_pool_instances AS instances;
-- Trên container mặc định (output minh hoạ): pool_mb = 128.00000000, instances = 1
-- (mỗi phép chia thêm 4 chữ số thập phân theo div_precision_increment, nên ra 8 chữ số)
```

### 4.3 Thay page nào ra: LRU có midpoint

Khi buffer pool đầy mà cần nạp page mới, phải loại một page cũ. Cách tự nhiên là *LRU* (least
recently used): bỏ page lâu nhất không ai dùng. Nhưng LRU thuần có điểm yếu chết người: một lần quét
toàn bảng lớn (báo cáo cuối tháng, `mysqldump`) đọc hàng triệu page chỉ một lần, và đẩy sạch dữ liệu
nóng ra khỏi RAM. Sáng hôm sau mọi query thường ngày đều phải đọc lại từ đĩa.

InnoDB dùng biến thể *midpoint insertion*:

```
  đầu danh sách (dùng gần đây nhất)                         đuôi (sắp bị loại)
  +--------------------- new / young (5/8) ---------+-------- old (3/8) --------+
  | page nóng ...                                   | ^                  ... ->  | loại
  +-------------------------------------------------+-|-------------------------+
                                                      |
                                    midpoint: page MỚI đọc từ đĩa được chèn ở đây
```

1. Danh sách chia hai phần: *new* (hay *young*) ở đầu, *old* ở đuôi. Phần old chiếm
   `innodb_old_blocks_pct` phần trăm (mặc định 37, tức khoảng 3/8).
2. Page mới đọc từ đĩa được chèn vào midpoint, tức đầu phần old, chứ không phải đầu danh sách.
3. Page trong phần old được truy cập lại thì được đưa lên đầu phần new. Nhưng có điều kiện:
   `innodb_old_blocks_time` (mặc định 1000 ms) là khoảng thời gian sau lần truy cập đầu tiên mà các lần
   truy cập tiếp theo không làm page được "thăng hạng".
4. Page không được dùng trôi dần về đuôi và bị loại.

Vì sao điều kiện thời gian quan trọng: khi quét bảng, một page bị đọc vài lần liên tiếp rất nhanh
(mỗi dòng trong page một lần) rồi không bao giờ được đụng lại. Với ngưỡng 1000 ms, các lần đọc dồn
dập đó không đưa page lên phần new; page của lần quét chỉ đi qua phần old rồi bị loại, phần new
(working set thật) không bị ảnh hưởng.

### 4.4 Dirty page, flush và checkpoint

Khi bạn `UPDATE` một dòng, InnoDB sửa page trong buffer pool. Page đó giờ khác bản trên đĩa, gọi là
*dirty page*. InnoDB **không** ghi page đó xuống đĩa ngay khi commit, vì:

- Ghi page là ghi ngẫu nhiên 16 KB vào vị trí bất kỳ trong file, đắt.
- Một page nóng có thể bị sửa hàng nghìn lần mỗi giây; ghi một lần sau đó rẻ hơn ghi hàng nghìn lần.

Dirty page được các thread nền (*page cleaner*) ghi xuống đĩa dần dần. Thứ tự và tốc độ flush do vài
cơ chế điều khiển:

- *Flush list*: danh sách dirty page sắp theo LSN của lần sửa đầu tiên (LSN là "số thứ tự" trong redo
  log, mục 5). Flush page cũ nhất trước giúp checkpoint tiến lên (mục 5.4).
- Ngưỡng: khi tỉ lệ dirty page vượt `innodb_max_dirty_pages_pct_lwm` (mặc định 10%) thì bắt đầu flush
  sớm; tới `innodb_max_dirty_pages_pct` (mặc định 90%) thì flush mạnh tay.
- *Adaptive flushing*: InnoDB tự điều chỉnh tốc độ flush theo tốc độ sinh redo, để không bị dồn ứ.
  `innodb_io_capacity` báo cho InnoDB biết thiết bị chịu được khoảng bao nhiêu I/O mỗi giây cho việc
  nền; MySQL 8.4 nâng mặc định lên 10000 (8.0 là 200) vì giả định SSD.
- Flush trên đường LRU: muốn loại một page dirty ở đuôi LRU thì phải ghi nó trước.

Câu hỏi tự nhiên: dirty page chưa xuống đĩa mà mất điện thì sao? Câu trả lời là redo log, mục 5.

### 4.5 Theo dõi buffer pool

```sql
SHOW ENGINE INNODB STATUS\G
-- Mục BUFFER POOL AND MEMORY, ví dụ trong tài liệu MySQL:
-- Buffer pool size   131072      (đơn vị page: 131072 x 16 KB = 2 GB)
-- Free buffers       124908
-- Database pages     5720
-- Old database pages 2071
-- Modified db pages  910         (số dirty page)
-- Buffer pool hit rate 1000 / 1000

SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read%';
-- Innodb_buffer_pool_read_requests: số lần đọc logic (tìm page trong pool)
-- Innodb_buffer_pool_reads:         số lần không có sẵn, phải đọc từ đĩa
```

Tỉ lệ `Innodb_buffer_pool_reads / Innodb_buffer_pool_read_requests` càng nhỏ càng tốt; hệ thống OLTP
khoẻ thường có hit rate trên 99%. Hit rate tụt mạnh nghĩa là working set đã vượt RAM: cần thêm RAM,
giảm dữ liệu nóng (index thừa, cột thừa, `SELECT *`), hoặc sửa query đang quét lớn.

### 4.6 Buffer pool lạnh sau restart

Restart xong, buffer pool rỗng: mọi query đều phải đọc đĩa, gọi là buffer pool "lạnh". Đó là câu
trả lời cho "vì sao sau restart query chậm vài phút rồi mới nhanh lại" ở mục 1.1.

InnoDB giảm vấn đề này bằng cách lưu danh sách page (chỉ số hiệu page, không phải dữ liệu) khi tắt
(`innodb_buffer_pool_dump_at_shutdown`, mặc định ON) và đọc lại các page đó khi khởi động
(`innodb_buffer_pool_load_at_startup`, mặc định ON). Mặc định chỉ lưu 25% page dùng gần đây nhất
(`innodb_buffer_pool_dump_pct = 25`). Xem tiến độ nạp:

```sql
SHOW STATUS LIKE 'Innodb_buffer_pool_load_status';
```

---

## 5. Redo log: write-ahead log và crash recovery

### 5.1 Bài toán: commit phải bền, nhưng page thì chưa ghi

Mục 4 để lại một mâu thuẫn: dirty page chưa được ghi xuống đĩa khi commit, vậy mà chữ D trong ACID
yêu cầu commit xong là không mất. Có hai cách nghĩ tới đầu tiên, đều tệ:

- Commit thì ghi mọi page bị sửa xuống đĩa và fsync: chậm, vì là ghi ngẫu nhiên nhiều page 16 KB cho
  có khi chỉ vài byte thay đổi.
- Không ghi gì: mất điện là mất.

Lời giải gần như mọi database dùng là *write-ahead logging* (WAL): trước khi coi một thay đổi là bền,
ghi một bản **mô tả ngắn** của thay đổi đó vào một file log chỉ ghi nối, rồi fsync file log. Page dữ
liệu thật có thể ghi sau, lúc nào tiện. Nếu crash, đọc log và làm lại (*redo*) các thay đổi chưa kịp
vào page. Trong InnoDB, log đó gọi là *redo log*.

Vì sao rẻ hơn: thay vì ghi ngẫu nhiên nhiều page 16 KB, commit chỉ cần ghi nối vài trăm byte vào cuối
một file và fsync một lần. Ghi nối tuần tự và nhỏ.

Quy tắc "write-ahead" có hai vế:

1. Redo của một thay đổi phải xuống đĩa **trước khi** page chứa thay đổi đó được ghi xuống đĩa.
2. Redo của một transaction phải xuống đĩa (fsync) **trước khi** báo commit thành công cho client (với
   cấu hình mặc định, mục 5.5).

### 5.2 Redo log ghi gì

Redo mô tả thay đổi ở mức vật lý của page, kiểu "trong page số 57 của tablespace 12, ở vị trí này, ghi
các byte này" hoặc "chèn record này vào page này". Nó không ghi câu SQL. Vì vậy redo chỉ có ý nghĩa
với chính các file dữ liệu của server đó; một server khác không dùng redo này để "chạy lại" được
(đó là việc của binlog, mục 9).

Mọi thay đổi trên page đều sinh redo, kể cả thay đổi trên page undo (mục 6). Nhờ vậy sau crash InnoDB
khôi phục được cả undo log, và từ undo rollback được các transaction dở dang.

InnoDB gom các thay đổi page cần nguyên tử với nhau (ví dụ một lần tách page B+tree động tới vài page)
thành một *mini-transaction*; redo của một mini-transaction được ghi như một khối, nên recovery không
bao giờ thấy cây B+tree ở trạng thái "tách dở".

### 5.3 LSN, log buffer, file redo

- *LSN* (*log sequence number*): một con số 64 bit chỉ tăng, tăng theo số byte redo đã sinh ra, nên
  có thể hiểu là "vị trí" trong dòng redo vô tận. Mỗi bản ghi redo nằm ở một LSN. Mỗi page ghi trong FIL header LSN của lần sửa cuối cùng
  (mục 3.4). Khi recovery, so LSN của page với LSN của bản ghi redo là biết bản ghi đó đã có trong page
  chưa: page có LSN lớn hơn hoặc bằng thì bỏ qua, nhỏ hơn thì áp. Nhờ vậy áp redo nhiều lần cũng
  không sai (*idempotent*).
- *Log buffer*: redo mới sinh được để trong vùng RAM này trước, rồi mới ghi xuống file. Kích thước
  `innodb_log_buffer_size`, MySQL 8.4 mặc định 64 MB (8.0 là 16 MB). Transaction lớn sinh nhiều redo
  mà log buffer nhỏ thì phải ghi xuống đĩa giữa chừng.
- File redo: từ MySQL 8.0.30 nằm trong thư mục `#innodb_redo` của data directory, tên dạng
  `#ib_redoN`. InnoDB cố duy trì 32 file, mỗi file bằng 1/32 của `innodb_redo_log_capacity` (mặc định
  100 MB, đổi được khi đang chạy bằng `SET GLOBAL`). Hai biến cũ `innodb_log_file_size` và
  `innodb_log_files_in_group` đã deprecated.

```sql
SHOW GLOBAL STATUS LIKE 'Innodb_redo_log_%lsn';
-- Innodb_redo_log_checkpoint_lsn       : LSN của checkpoint gần nhất (mục 5.4)
-- Innodb_redo_log_current_lsn          : LSN hiện tại (redo đã sinh tới đâu)
-- Innodb_redo_log_flushed_to_disk_lsn  : redo đã fsync xuống đĩa tới đâu

SELECT FILE_NAME, START_LSN, END_LSN FROM performance_schema.innodb_redo_log_files;
```

Thử: ghi `SHOW GLOBAL STATUS LIKE 'Innodb_redo_log_current_lsn';`, chạy vài `INSERT`, xem lại: con số
tăng lên theo lượng redo vừa sinh.

### 5.4 Checkpoint: redo không thể dài mãi

Redo dùng dung lượng cố định, nên phần cũ phải được giải phóng để dùng lại. Phần redo nào bỏ được? Phần
mô tả những thay đổi **đã nằm trong file dữ liệu** (page tương ứng đã được flush). Điểm LSN mà mọi thay
đổi trước nó đều đã có trong tablespace gọi là *checkpoint*.

```
 LSN tăng dần --->
 |---------- đã bỏ được ----------|====== redo còn cần ======|.... chỗ trống ....|
                                  ^                          ^
                           checkpoint LSN              current LSN
                (mọi thay đổi trước điểm này       (redo mới nhất)
                 đã có trong file .ibd)

 Khoảng giữa checkpoint và current LSN = "checkpoint age": lượng redo mà recovery sẽ phải áp lại.
```

InnoDB dùng *fuzzy checkpoint*: không dừng hệ thống để flush tất cả một lượt, mà flush dirty page cũ
nhất từng lô nhỏ (đó là lý do flush list sắp theo LSN, mục 4.4) và đẩy checkpoint lên dần.

Cân nhắc kích thước redo:

- ⚠️ Quá nhỏ so với lượng ghi: redo sắp đầy, InnoDB buộc phải flush dirty page gấp để đẩy checkpoint
  lên, ghi mới bị chậm lại hoặc khựng từng đợt. Triệu chứng: hệ thống ghi nhiều có những nhịp chậm đột
  ngột theo chu kỳ.
- Quá lớn: dirty page được giữ lâu hơn (ít ghi lặp hơn, tốt), nhưng sau crash có nhiều redo để áp hơn,
  recovery lâu hơn.

### 5.5 Crash recovery

Theo tài liệu MySQL, khi khởi động lại sau crash, InnoDB tự làm các bước sau, bạn chỉ cần khởi động
lại server:

1. *Tablespace discovery*: xác định các tablespace cần áp redo.
2. *Redo log application* (roll forward): đọc redo từ checkpoint cuối tới hết, áp vào page nào có LSN
   cũ hơn. Bước này chạy **trước khi** nhận connection. Xong bước này, mọi page về đúng trạng thái
   ngay trước lúc crash, gồm cả thay đổi của transaction chưa commit, và cả undo log của chúng.
3. *Rollback transaction dở dang*: transaction nào lúc crash chưa commit thì dùng undo để hoàn tác.
   Bước này chạy song song với hoạt động bình thường (server đã nhận connection). Tài liệu ghi chú:
   rollback có thể mất gấp ba bốn lần thời gian transaction đã chạy, và không huỷ được.
4. *Change buffer merge* và *purge* tiếp tục như lúc chạy bình thường.

```
 Trước crash:       T1 commit (redo đã fsync)     T2 đang chạy dở
 Trên đĩa:          page của T1 chưa flush         một số page của T2 đã flush (có thể!)
 Sau bước 2:        page có thay đổi của T1        page có thay đổi của T2
 Sau bước 3:        giữ nguyên T1 (đã commit)      undo T2 -> như chưa từng chạy
```

Chú ý dòng "một số page của T2 đã flush (có thể!)": InnoDB được phép flush dirty page của transaction
chưa commit (chính sách *steal*), và không bắt buộc flush page lúc commit (*no-force*). Redo lo phần
"làm lại", undo lo phần "hoàn tác". Đây là kiến trúc kinh điển trong lý thuyết database (thường gọi
theo tên thuật toán ARIES), dù InnoDB không cài đặt y nguyên ARIES.

### 5.6 Commit ghi redo thế nào: `innodb_flush_log_at_trx_commit`

Biến này quyết định redo được ghi và fsync lúc nào khi commit. Đây là "núm vặn" độ bền quan trọng nhất
của InnoDB:

| Giá trị | Lúc COMMIT | Mỗi khoảng 1 giây | Mất gì khi chỉ mysqld chết (suy luận, xem dưới) | Mất gì khi mất điện / OS sập |
|---|---|---|---|---|
| `1` (mặc định) | Ghi redo vào file và fsync | | Không | Không |
| `2` | Ghi redo vào file (vào cache của OS), không fsync | fsync | Thường không (dữ liệu đã nằm trong cache của OS) | Tới khoảng 1 giây cuối |
| `0` | Không ghi gì | Ghi và fsync | Tới khoảng 1 giây cuối | Tới khoảng 1 giây cuối |

- Tài liệu MySQL 8.4 chỉ nói chung cho cả `0` và `2`: transaction mà redo chưa được flush có thể mất
  khi crash, tới khoảng 1 giây. Cột "chỉ mysqld chết" là suy luận từ cách OS hoạt động (mục 1.3): với
  `2`, redo đã `write()` vào cache của OS nên OS vẫn ghi xuống dù mysqld chết; đừng coi đó là cam kết
  của MySQL.
- Chu kỳ "khoảng 1 giây" đặt bằng `innodb_flush_log_at_timeout` (mặc định 1). Tài liệu MySQL nhấn mạnh
  chu kỳ này không đảm bảo chính xác 100%: có thể dày hơn (do DDL và hoạt động nội bộ) hoặc thưa hơn.
- Dù đặt giá trị nào, crash recovery vẫn đúng theo nghĩa transaction được áp trọn vẹn hoặc bị xoá
  trọn vẹn; cái mất chỉ là vài transaction cuối đã báo commit cho client.
- Chỉ `1` cho đầy đủ ACID. Tài liệu MySQL khuyến nghị với replication: luôn đặt
  `innodb_flush_log_at_trx_commit=1` và `sync_binlog=1` (mục 9.5).
- ⚠️ Tài liệu cũng cảnh báo: nhiều hệ điều hành và phần cứng "nói dối" về fsync (báo đã ghi trong khi
  dữ liệu còn trong cache của ổ đĩa). Khi đó cấu hình nào cũng không đảm bảo được độ bền. Ổ đĩa
  server có cache được pin/tụ bảo vệ là lời giải ở tầng phần cứng.

Vì sao `1` vẫn chạy được nhanh khi nhiều client cùng commit: InnoDB gom các commit đến gần như cùng
lúc để chung một lần fsync (*group commit*, mục 9.4).

---

## 6. Undo log, MVCC và purge

Chương 14 đã giải thích MVCC từ phía người dùng: mỗi transaction đọc trên một snapshot, đọc không chặn
ghi. Mục này nhìn vào phần máy móc bên dưới: bản cũ của dòng nằm ở đâu, ai dọn nó, và khi nào việc dọn
dẹp bị kẹt.

### 6.1 Undo log là gì

*Undo log* lưu thông tin để **đảo ngược** thay đổi mới nhất của một transaction trên một record của
clustered index. Nó phục vụ hai việc:

1. **Rollback**: `ROLLBACK`, hoặc rollback transaction dở dang sau crash (mục 5.5), hoặc rollback một
   câu lệnh bị lỗi giữa chừng.
2. **MVCC**: transaction khác cần đọc phiên bản cũ của dòng thì InnoDB dựng lại phiên bản đó từ undo.

Ví dụ với `UPDATE products SET stock = 7 WHERE id = 5` (giá trị cũ là 8):

- InnoDB ghi vào undo một bản ghi đại ý "dòng id=5 trước đó có stock=8, do transaction X sửa, bản trước
  nữa ở chỗ này".
- Sửa dòng **tại chỗ** trong clustered index: stock thành 7, `DB_TRX_ID` thành id transaction hiện tại,
  `DB_ROLL_PTR` trỏ vào bản ghi undo vừa viết.

Phân loại theo tài liệu MySQL:

- *Insert undo log*: cho `INSERT`. Chỉ cần cho rollback (dòng mới không có "bản cũ" để ai đọc), nên bỏ
  được ngay khi transaction commit.
- *Update undo log*: cho `UPDATE` và `DELETE`. Cần cho cả rollback lẫn MVCC, nên chỉ bỏ được khi không
  còn snapshot nào có thể cần nó.

Về lưu trữ: undo log nằm trong *rollback segment*, rollback segment nằm trong undo tablespace (mặc định
hai file `undo_001`, `undo_002`, mục 3.2). Undo của bảng tạm do người dùng tạo nằm trong temporary
tablespace và không sinh redo, vì bảng tạm không cần khôi phục sau crash.

### 6.2 Version chain: chuỗi phiên bản

Mỗi bản ghi undo lại có con trỏ tới bản cũ hơn nữa, tạo thành *version chain*:

```
 Clustered index (bản MỚI NHẤT luôn ở đây)        Undo log (các bản cũ)
 +-------------------------------------+
 | id=5 | stock=7 | trx=300 | roll_ptr-+---> [stock=8, trx=250, roll_ptr]---> [stock=10, trx=100, roll_ptr=null]
 +-------------------------------------+
```

Đọc theo chiều mũi tên là đi ngược thời gian: trx 100 đặt stock=10, trx 250 sửa thành 8, trx 300 sửa
thành 7.

Khi một transaction đọc dòng id=5 bằng consistent read, InnoDB lấy *read view* của nó (snapshot) và kiểm
tra `DB_TRX_ID` của bản mới nhất:

1. Là id của chính mình: thấy.
2. Nhỏ hơn id nhỏ nhất trong số transaction đang hoạt động lúc tạo read view: đã commit trước đó, thấy.
3. Lớn hơn hoặc bằng id sẽ được cấp tiếp theo tại lúc tạo read view: transaction bắt đầu sau snapshot,
   không thấy.
4. Nằm giữa: thấy nếu id đó không nằm trong danh sách đang hoạt động lúc tạo read view.

Không thấy thì theo `roll_ptr` sang bản cũ hơn và kiểm tra lại, cho tới khi gặp bản thấy được (hoặc hết
chuỗi: dòng "chưa tồn tại" với snapshot đó). Read view được tạo khi nào (một lần mỗi transaction ở
REPEATABLE READ, mỗi câu lệnh ở READ COMMITTED) đã bàn ở chương 14.

Hai hệ quả quan trọng:

- Bản mới nhất nằm ngay trong bảng, nên đọc dữ liệu mới là đường ngắn nhất. Transaction đọc snapshot
  càng cũ, và dòng bị sửa càng nhiều lần kể từ đó, thì chuỗi phải đi càng dài.
- Rollback ở InnoDB là công việc thật: phải đọc undo và áp ngược từng thay đổi. Transaction sửa 10 triệu
  dòng rồi rollback có thể mất thời gian cỡ lúc chạy, thậm chí hơn.

### 6.3 Secondary index và MVCC

Theo tài liệu MySQL, secondary index được xử lý khác: record của secondary index **không** có cột ẩn
`DB_TRX_ID`/`DB_ROLL_PTR` và **không** được sửa tại chỗ. Khi cột trong secondary index bị đổi, entry cũ
bị đánh dấu xoá (*delete-mark*), entry mới được chèn, entry cũ được purge sau.

Vì secondary index không biết phiên bản, InnoDB chỉ dựa vào một con số trên page: "max trx id" (id
transaction lớn nhất từng sửa page đó, nằm trong INDEX header, mục 3.4). Nếu entry đang bị delete-mark
hoặc page vừa bị một transaction mới hơn snapshot sửa, InnoDB phải quay về clustered index để kiểm
tra phiên bản đúng. ⚠️ Trong trường hợp đó covering index (chương 11) tạm mất tác dụng: query vốn chỉ
cần đọc secondary index lại phải đọc thêm clustered index. Bảng bị sửa liên tục làm covering index
kém hiệu quả hơn bạn tưởng.

### 6.4 DELETE không xoá ngay: purge

`DELETE FROM t WHERE id = 5` không gỡ dòng ra khỏi page. Nó chỉ:

- Bật cờ delete-mark trên record (mục 3.5) và ghi undo cho thao tác đó.
- Các transaction có snapshot cũ vẫn thấy dòng này (qua undo), transaction mới thì không.

Việc gỡ thật sự record khỏi clustered index và các secondary index, cùng việc giải phóng undo log không
còn ai cần, do các *purge thread* chạy nền làm. Tài liệu MySQL mô tả:

- Danh sách các undo log của transaction **đã commit** chờ được xử lý gọi là *history list*.
- Purge định kỳ đọc history list, gỡ những record bị delete-mark và bỏ những undo log mà không còn read
  view nào có thể cần.
- Số purge thread tối đa là `innodb_purge_threads` (MySQL 8.4 mặc định 1 nếu máy có không quá 16 CPU
  logic, ngược lại 4); hệ thống tự điều chỉnh số thread thực dùng.

Điều kiện "không còn read view nào có thể cần" là mấu chốt: purge chỉ dọn được những gì **cũ hơn read
view cũ nhất đang tồn tại**. Một read view cũ là một "cái neo" giữ lại toàn bộ lịch sử từ thời điểm đó.

### 6.5 History list length và sự cố "transaction quên đóng"

*History list length* (HLL) là độ dài history list: lượng undo của transaction đã commit mà purge chưa
dọn. Tài liệu MySQL gọi nó là *purge lag*. Đây là chỉ số sức khoẻ quan trọng nhất của MVCC:

```sql
SHOW ENGINE INNODB STATUS\G
-- Mục TRANSACTIONS có dòng: History list length 1234

SELECT `count` FROM information_schema.INNODB_METRICS
WHERE name = 'trx_rseg_history_len';

-- Tìm thủ phạm: transaction mở lâu nhất
SELECT trx_id, trx_state, trx_started, trx_mysql_thread_id, trx_query
FROM information_schema.INNODB_TRX
ORDER BY trx_started
LIMIT 5;
```

HLL dao động vài trăm tới vài nghìn là bình thường với hệ thống ghi nhiều. Tăng đều lên hàng trăm nghìn,
hàng triệu mà không giảm là dấu hiệu có thứ gì giữ snapshot cũ.

Tự dựng lại sự cố với hai session (dữ liệu mẫu):

```sql
USE lab16;
CREATE TABLE products (
  id INT PRIMARY KEY,
  stock INT NOT NULL
);
INSERT INTO products VALUES (1, 1000000);
```

Để tạo nhiều update nhanh ở session B, dùng một stored procedure nhỏ (chương 17 sẽ giải thích cú pháp):

```sql
DELIMITER //
CREATE PROCEDURE burn_updates(IN n INT)
BEGIN
  DECLARE i INT DEFAULT 0;
  WHILE i < n DO
    UPDATE products SET stock = stock - 1 WHERE id = 1;  -- autocommit: mỗi câu là một transaction
    SET i = i + 1;
  END WHILE;
END //
DELIMITER ;
```

| Bước | Session A | Session B | Kết quả |
|---|---|---|---|
| 1 | `START TRANSACTION;` `SELECT stock FROM products WHERE id = 1;` | | A tạo read view, thấy 1000000. Rồi bỏ đó (giống dev mở console quên commit) |
| 2 | | `CALL burn_updates(100000);` | 100.000 transaction nhỏ, mỗi cái sinh một bản undo |
| 3 | | `SHOW ENGINE INNODB STATUS\G` | History list length tăng lên cỡ hàng chục nghìn trở lên và không giảm: purge không được dọn vì A có thể cần bất kỳ bản cũ nào |
| 4 | `SELECT stock FROM products WHERE id = 1;` | | Vẫn thấy 1000000 (REPEATABLE READ), nhưng phải đi ngược chuỗi khoảng 100.000 phiên bản: chậm thấy rõ so với bình thường |
| 5 | `COMMIT;` | | Read view của A biến mất |
| 6 | | `SHOW ENGINE INNODB STATUS\G` sau ít giây | HLL giảm dần về mức thấp: purge đã dọn |

(Con số HLL cụ thể phụ thuộc máy và thời điểm, đừng mong ra đúng số. Thời gian ở bước 4 cũng vậy; điểm
cần thấy là chênh lệch.)

Bài học:

- Một transaction **chỉ đọc** cũng gây hại nếu để mở lâu, vì nó giữ read view. Tài liệu MySQL khuyến
  nghị commit đều đặn, kể cả transaction chỉ có consistent read.
- Hậu quả lan ra toàn hệ thống: undo tablespace phình, các query khác cũng phải lướt qua phiên bản cũ và
  record delete-mark chưa purge, bảng ghi-xoá nhiều phình to.
- Phòng ở tầng ứng dụng: không mở transaction rồi chờ người dùng, chờ gọi API, chờ queue; với PHP, cẩn
  thận script chạy lâu (worker, cron) mở transaction ở đầu rồi quên commit. Phòng ở tầng vận hành: cảnh
  báo khi `INNODB_TRX` có transaction sống quá vài phút, và khi HLL vượt ngưỡng (chương 24).
- `innodb_max_purge_lag` (mặc định 0, tức tắt) có thể bật để InnoDB làm chậm DML khi purge tụt quá xa;
  đây là biện pháp chữa cháy, không chữa nguyên nhân.

### 6.6 Undo tablespace phình và co

Undo tablespace lớn lên khi có nhiều undo chưa dọn. Với `innodb_undo_log_truncate = ON` (mặc định), một
undo tablespace vượt `innodb_max_undo_log_size` (mặc định 1 GB) được đánh dấu để thu nhỏ: InnoDB ngừng
cấp undo mới trong nó, đợi purge dọn hết, rồi cắt về kích thước ban đầu. Cần ít nhất hai undo tablespace
để luân phiên, đó là lý do mặc định có hai file.

Nếu một transaction mở lâu giữ read view, undo không dọn được, nên truncate cũng không làm được gì: thủ
phạm vẫn là transaction đó.

---

## 7. Doublewrite buffer: chống page ghi dở

### 7.1 Torn page: thứ redo không cứu được

Page InnoDB 16 KB, nhưng hệ điều hành và thiết bị lưu trữ thường chỉ đảm bảo ghi nguyên tử theo đơn vị
nhỏ hơn (ví dụ 4 KB). Nếu mất điện đúng lúc InnoDB đang ghi một page 16 KB xuống file `.ibd`, trên đĩa
có thể còn lại một page nửa mới nửa cũ: *torn page* (page bị xé), hay *partial page write*.

```
 Page 57 trên đĩa sau khi mất điện giữa chừng:
 +---------+---------+---------+---------+
 | 4KB mới | 4KB mới | 4KB CŨ  | 4KB CŨ  |   -> checksum sai, page hỏng
 +---------+---------+---------+---------+
```

Tại sao redo không cứu được? Redo mô tả thay đổi kiểu "trên page 57, ở vị trí X, sửa thành Y" (mục
5.2). Áp nó lên một page vốn đã hỏng thì kết quả vẫn hỏng. Redo cần một bản gốc nguyên vẹn của page để
làm việc.

### 7.2 Cơ chế

Doublewrite buffer cung cấp bản nguyên vẹn đó:

1. Khi flush một lô dirty page, InnoDB **trước tiên** ghi cả lô vào *doublewrite file* thành một khối
   tuần tự lớn, rồi fsync.
2. **Sau đó** mới ghi từng page vào đúng vị trí của nó trong tablespace.
3. Khi recovery, nếu phát hiện page trong tablespace hỏng (checksum sai), InnoDB lấy bản nguyên vẹn từ
   doublewrite file, chép đè vào, rồi mới áp redo.

```
 Buffer pool (dirty page 57, 88, 130)
        |
        | (1) ghi tuần tự cả lô + fsync
        v
 #ib_16384_0.dblwr  [57][88][130]
        |
        | (2) ghi từng page vào vị trí thật
        v
 orders.ibd: ... [57] ... [88] ... [130] ...

 Crash ở (1): page trong .ibd vẫn là bản cũ nguyên vẹn -> áp redo bình thường.
 Crash ở (2): page trong .ibd có thể bị xé, nhưng bản trong .dblwr nguyên vẹn -> chép lại, rồi áp redo.
```

Theo tài liệu MySQL, dù dữ liệu được ghi hai lần, chi phí không gấp đôi: lần ghi vào doublewrite là
một khối tuần tự lớn với một lần fsync.

### 7.3 Cấu hình

- `innodb_doublewrite`: mặc định `ON` (tương đương `DETECT_AND_RECOVER`). `DETECT_ONLY` chỉ ghi metadata,
  đủ để **phát hiện** page ghi dở nhưng không sửa được. `OFF` tắt hẳn; tài liệu chỉ gợi ý cân nhắc khi
  bạn quan tâm hiệu năng hơn toàn vẹn dữ liệu, ví dụ lúc benchmark. ⚠️ Đừng tắt trên production trừ khi
  hệ thống file/thiết bị đảm bảo ghi nguyên tử nguyên page và bạn đã kiểm chứng điều đó.
- Từ MySQL 8.0.20, doublewrite nằm trong file riêng (trước đó nằm trong `ibdata1`). Tên dạng
  `#ib_<page_size>_<số>.dblwr`, ví dụ `#ib_16384_0.dblwr` và `#ib_16384_1.dblwr` cho page 16 KB và một
  buffer pool instance. Mặc định hai file cho mỗi buffer pool instance (một cho flush từ flush list, một
  cho flush từ LRU list).
- `innodb_doublewrite_dir` cho phép đặt các file này trên thiết bị nhanh nhất.

Postgres giải cùng bài toán theo cách khác: lần đầu một page bị sửa sau mỗi checkpoint, nó ghi **cả
page** vào WAL (*full page write*, biến `full_page_writes`, mặc định on). Mục 11.

---

## 8. Change buffer và adaptive hash index

Hai cấu trúc này nằm trong buffer pool và từng là "tính năng tối ưu" bật sẵn. Ở MySQL 8.4, cả hai đều
**tắt mặc định**, nên bạn chỉ cần hiểu khái niệm để đọc tài liệu cũ và để biết khi nào nên cân nhắc bật.

### 8.1 Change buffer

Bài toán: bảng có vài secondary index. Mỗi `INSERT` phải chèn entry vào **mọi** secondary index. Clustered
index theo PK tăng dần thì chèn vào cuối (page nóng, có sẵn trong RAM), nhưng secondary index (ví dụ
`email`, `created_by`) thì giá trị rải rác, mỗi lần chèn rơi vào một page khác nhau, có thể không có trong
buffer pool. Đọc page đó từ đĩa chỉ để chèn một entry là đắt.

Change buffer: khi page secondary index cần sửa **không có trong buffer pool**, InnoDB ghi tạm thay đổi
vào change buffer thay vì đọc page lên. Sau này, khi page đó được đọc vào buffer pool vì lý do khác (hoặc
khi hệ thống rảnh, hoặc lúc tắt máy chậm), các thay đổi được gộp (*merge*) vào page. Nhiều thay đổi cho
cùng một page được gộp một lần.

Những điểm cần biết (theo tài liệu MySQL 8.4):

- Chỉ áp dụng cho secondary index, không cho clustered index. Thao tác chèn vào unique index thì không
  được buffer, vì để kiểm tra trùng InnoDB vẫn phải đọc page. Cũng không hỗ trợ khi index (hoặc PK) có cột sắp giảm dần.
- Trong RAM nó chiếm một phần buffer pool (tối đa `innodb_change_buffer_max_size` phần trăm, mặc định
  25); trên đĩa nó nằm trong system tablespace `ibdata1` (mục 3.2).
- `innodb_change_buffering`: MySQL 8.4 mặc định `none` (tắt), 8.0 mặc định `all`. Lý do thực tế: với SSD
  và buffer pool lớn, lợi ích nhỏ đi, trong khi việc merge dồn ứ có thể kéo dài nhiều giờ và làm chậm hệ
  thống (tài liệu có cảnh báo này).

### 8.2 Adaptive hash index (AHI)

B+tree tìm một key phải đi từ gốc xuống lá, mỗi tầng một page. AHI là một bảng băm (hash) InnoDB **tự
dựng** trong RAM cho những phần index được tra cứu thường xuyên, để tra bằng giá trị key nhảy thẳng tới
record mà không đi qua các tầng cây.

- Tự động: InnoDB theo dõi mẫu tìm kiếm và chỉ dựng hash cho những page hay được truy cập. Bạn không tạo
  hay chọn được.
- Lợi khi dữ liệu gần như nằm gọn trong RAM và tra cứu bằng đẳng thức lặp lại nhiều. Không lợi với
  `LIKE '%...'`, và có thể thành điểm tranh chấp khi tải cao (tài liệu nêu ví dụ nhiều join đồng thời).
- `innodb_adaptive_hash_index`: MySQL 8.4 mặc định `OFF` (8.0 là `ON`). Tài liệu khuyên benchmark cả hai
  chế độ với tải thật trước khi quyết định.

Đừng nhầm AHI với index kiểu `HASH` người dùng tự tạo: InnoDB không hỗ trợ index hash do người dùng định
nghĩa (khai `USING HASH` trên bảng InnoDB thì vẫn ra B-tree, chương 11); index hash thật chỉ có ở engine
`MEMORY`.

---

## 9. Binlog và internal two-phase commit

### 9.1 Binlog là gì, khác redo log ở đâu

*Binary log* (binlog) là log của **tầng server** (mục 2), ghi lại mọi thay đổi dữ liệu dưới dạng *event*
logic. Nó có hai công dụng chính:

- **Replication**: replica đọc binlog của primary và áp lại (chương 22).
- **Point-in-time recovery** (PITR): khôi phục bản backup rồi áp binlog tới đúng thời điểm mong muốn,
  ví dụ ngay trước câu `DELETE` nhầm (chương 21).

MySQL 8.4 bật binlog mặc định (tắt bằng `--skip-log-bin` hoặc `--disable-log-bin`). File nằm trong data
directory với tên dạng `binlog.000001`, `binlog.000002`, ...

```sql
SHOW BINARY LOGS;                        -- liệt kê file binlog và kích thước
SHOW BINLOG EVENTS IN 'binlog.000002' LIMIT 10;
SELECT @@binlog_format, @@sync_binlog, @@binlog_expire_logs_seconds;
-- Mặc định: ROW, 1, 2592000 (30 ngày)
```

So sánh ba loại log trong chương:

| | Redo log | Undo log | Binlog |
|---|---|---|---|
| Thuộc tầng | InnoDB | InnoDB | Server (mọi engine) |
| Ghi gì | Thay đổi vật lý trên page | Cách đảo ngược thay đổi trên dòng | Thay đổi logic: giá trị dòng (ROW) hoặc câu SQL (STATEMENT) |
| Dùng để | Crash recovery | Rollback, MVCC | Replication, PITR |
| Ai đọc được | Chỉ InnoDB của chính server đó | Chỉ InnoDB | Replica, `mysqlbinlog`, công cụ CDC |
| Khi nào bỏ | Sau checkpoint | Sau purge | Theo thời hạn (`binlog_expire_logs_seconds`) |
| Cách ghi | Vòng tròn, dung lượng cố định | Trong undo tablespace | Nối thêm file mới, xoá file cũ theo hạn |

Ví dụ trực giác: redo nói "byte thứ 200 của page 57 trong tablespace 12 thành 0x1F" (chỉ có nghĩa trên
đúng các file đó); binlog dạng ROW nói "bảng `shop.orders`, dòng có id=5: status từ 'new' thành 'paid'"
(một server khác, phiên bản khác vẫn áp được).

Về `binlog_format`: `ROW` (mặc định) ghi giá trị dòng trước/sau; `STATEMENT` ghi câu SQL; `MIXED` tự chọn.
Biến này đã bị đánh dấu deprecated từ 8.0.34; cứ giữ `ROW`. Chi tiết và các cạm bẫy của từng format để
dành cho chương 22.

Trong lúc transaction chạy, các event được gom trong *binlog cache* riêng của session (kích thước
`binlog_cache_size`, lớn quá thì tràn ra file tạm); chỉ khi commit chúng mới được ghi liền một khối vào
file binlog. Vì vậy trong binlog, event của các transaction không xen kẽ nhau.

### 9.2 Vấn đề: hai log, hai file, crash ở giữa

Một transaction commit phải có mặt ở **cả hai** nơi: redo (để primary tự khôi phục) và binlog (để replica
và PITR có). Hai file khác nhau không thể ghi nguyên tử cùng một lúc. Nếu commit đơn giản là "ghi cái này
rồi ghi cái kia", crash ở giữa gây lệch:

| Crash khi | Primary sau recovery | Replica | Hậu quả |
|---|---|---|---|
| Đã có trong redo, chưa có trong binlog | Có transaction | Không bao giờ nhận được | Replica thiếu dữ liệu |
| Đã có trong binlog, chưa có trong redo | Rollback transaction | Đã/ sẽ nhận và áp | Replica thừa dữ liệu primary không có |

Tài liệu MySQL kể lại đúng tình huống thứ hai ở các bản cũ: binlog đã fsync, InnoDB chưa kịp commit thì
crash, InnoDB rollback lúc khởi động nhưng binlog vẫn còn transaction đó.

### 9.3 Lời giải: internal two-phase commit (XA nội bộ)

MySQL coi binlog như "người điều phối" và InnoDB như "người tham gia" trong một giao thức
*two-phase commit* (2PC) nội bộ. Ở MySQL 8.4 cơ chế này luôn bật. Mỗi transaction có một *XID* (mã định
danh) được ghi vào cả hai phía. Với cấu hình mặc định (`innodb_flush_log_at_trx_commit=1`,
`sync_binlog=1`), một `COMMIT` diễn ra như sau:

```
 COMMIT
   |
   | Phase 1 - PREPARE (InnoDB)
   |   InnoDB đánh dấu transaction "prepared" (kèm XID), ghi redo, fsync redo.
   |   Từ đây InnoDB hứa: "tôi commit được nếu được bảo".
   v
   | Ghi BINLOG
   |   Toàn bộ event trong binlog cache được ghi vào file binlog kèm XID, fsync binlog.
   |   ==> ĐIỂM COMMIT THẬT: có trong binlog (đã fsync) là chắc chắn sẽ được commit.
   v
   | Phase 2 - COMMIT (InnoDB)
   |   InnoDB ghi dấu commit, nhả lock. Client nhận OK.
   v
```

Khi khởi động lại sau crash (mô tả trong tài liệu Binary Log):

1. InnoDB khôi phục bằng redo (mục 5.5) và rollback các transaction chưa tới trạng thái prepared.
2. Server quét file binlog cuối cùng, thu thập các XID có trong đó và xác định vị trí hợp lệ cuối cùng.
3. Transaction đang ở trạng thái prepared: **XID có trong binlog** thì InnoDB commit nó; **không có** thì
   rollback.
4. Binlog được cắt về vị trí hợp lệ cuối cùng (bỏ phần ghi dở).

Kiểm tra lại với mọi điểm crash có thể:

| Crash ở đâu | Trạng thái lúc khởi động | Quyết định | Primary và binlog |
|---|---|---|---|
| Trước khi prepare xong | Chưa prepared | Rollback | Đều không có |
| Đã prepared, binlog chưa ghi xong | Prepared, XID không có trong binlog (hợp lệ) | Rollback | Đều không có |
| Binlog đã fsync, InnoDB chưa commit | Prepared, XID có trong binlog | Commit | Đều có |
| Sau phase 2 | Đã commit | Giữ nguyên | Đều có |

Không có trường hợp nào lệch: đó là mục đích của 2PC. Kết quả đi kèm: replica không bao giờ nhận một
transaction mà primary đã rollback. Tài liệu MySQL còn ghi: nếu lúc recovery server thấy binlog **ngắn
hơn** kích thước đáng lẽ phải có (thiếu transaction đã commit), nó báo lỗi `The binary log file_name is
shorter than its expected size`, nghĩa là binlog không còn tin được và replica cần dựng lại từ snapshot
mới. Điều này không nên xảy ra nếu `sync_binlog=1` và đĩa thật sự fsync khi được yêu cầu.

### 9.4 Group commit

Mỗi commit cần ít nhất hai lần fsync (redo lúc prepare, binlog). fsync tốn từ vài chục micro giây tới vài
mili giây tuỳ thiết bị, nên nếu mỗi transaction tự fsync riêng thì throughput bị chặn bởi số fsync mỗi
giây của đĩa.

*Group commit* giải quyết bằng cách gom: các transaction commit gần như cùng lúc được xếp hàng, một
thread "đại diện" (leader) ghi và fsync hộ cả nhóm. Binlog group commit chia quá trình commit thành
các giai đoạn nối tiếp (ghi vào file, fsync, commit trong engine), mỗi giai đoạn có hàng đợi riêng, nên
khi nhiều client cùng commit, mỗi lần fsync phục vụ được nhiều transaction. Đây là lý do `sync_binlog=1`
không chậm như phép tính "một fsync mỗi transaction" gợi ý. Cũng là lý do tài liệu nói `sync_binlog=N`
là fsync sau N **nhóm commit** (commit group), không phải N transaction.

`binlog_group_commit_sync_delay` (micro giây, mặc định 0) cho phép cố ý chờ thêm một chút để gom nhóm
lớn hơn: tăng throughput, đổi lại mỗi commit trễ hơn. Chỉ chỉnh khi đã đo.

### 9.5 Hai núm vặn độ bền: `innodb_flush_log_at_trx_commit` và `sync_binlog`

`innodb_flush_log_at_trx_commit` đã gặp ở mục 5.6. `sync_binlog` là núm tương ứng cho binlog:

| `sync_binlog` | Ý nghĩa | Khi mất điện / OS sập |
|---|---|---|
| `1` (mặc định) | fsync binlog trước khi transaction commit | Transaction thiếu trong binlog chỉ ở trạng thái prepared, recovery rollback chúng: không mất gì khỏi binlog |
| `N` (> 1) | fsync sau mỗi N nhóm commit | Có thể đã commit những transaction chưa kịp xuống binlog |
| `0` | MySQL không tự fsync, để OS ghi khi nào tuỳ nó | Như trên, lượng mất không xác định |

Để ý: các rủi ro của `sync_binlog` khác 1 và `innodb_flush_log_at_trx_commit` khác 1 xuất hiện khi **OS
sập hoặc mất điện**. Suy luận từ cách OS hoạt động (tài liệu MySQL không tách riêng trường hợp này): nếu chỉ tiến trình
mysqld chết thì dữ liệu đã `write()` vẫn nằm trong cache của OS và sẽ được OS ghi xuống (trừ
`innodb_flush_log_at_trx_commit=0`, vốn chưa `write()` gì lúc commit).

Các cấu hình thường gặp:

| Cấu hình | Khi nào dùng | Cái giá |
|---|---|---|
| `1` / `1` (mặc định) | Primary production, dữ liệu tiền, đơn hàng | Mỗi nhóm commit hai fsync |
| `2` / `0` hoặc `2` / `1000` | Replica chỉ dùng cho báo cáo, môi trường dev, import dữ liệu một lần | Mất điện có thể mất giao dịch cuối; redo và binlog có thể lệch nhau |
| `0` / `0` | Nạp dữ liệu hàng loạt có thể làm lại từ đầu | Kể cả mysqld crash cũng mất khoảng 1 giây |

⚠️ Hạ một trong hai biến không chỉ "mất một giây dữ liệu". Sau khi mất điện, redo và binlog có thể ở hai
thời điểm khác nhau: InnoDB có transaction mà binlog không có, hoặc ngược lại. Hệ quả là replica lệch
primary một cách âm thầm, hoặc PITR từ binlog ra dữ liệu khác với thực tế. Tài liệu MySQL khuyến nghị
cả hai bằng 1 cho mọi hệ thống replication cần độ bền.

```sql
-- Xem cấu hình hiện tại
SELECT @@innodb_flush_log_at_trx_commit, @@sync_binlog, @@log_bin;
-- Mặc định MySQL 8.4: 1, 1, 1
```

---

## 10. Ghép lại: hành trình của một câu UPDATE

Đây là câu hỏi phỏng vấn senior kinh điển: "Từ lúc gửi `UPDATE` tới lúc dữ liệu an toàn trên đĩa, chuyện
gì xảy ra?". Giờ bạn đã có đủ mảnh để trả lời. Lấy ví dụ, với autocommit bật và cấu hình mặc định:

```sql
UPDATE accounts SET balance = balance - 100 WHERE id = 7;
```

**Giai đoạn A: chạy câu lệnh**

1. Tầng server: parser, resolver, optimizer chọn tra clustered index theo PK `id = 7` (mục 2.2).
2. Executor gọi InnoDB tìm dòng id=7. InnoDB đi từ gốc B+tree xuống lá; mỗi page cần đọc mà chưa có
   trong buffer pool thì được đọc từ `accounts.ibd` vào (mục 4.1).
3. InnoDB đặt lock X lên record id=7 (chương 15).
4. Ghi bản ghi undo: "balance cũ là 500, trx_id cũ, roll_ptr cũ" vào page undo trong buffer pool
   (mục 6.1). Việc sửa page undo này sinh redo.
5. Sửa record trong page lá **ngay trong buffer pool**: balance = 400, `DB_TRX_ID` = id transaction này,
   `DB_ROLL_PTR` trỏ tới bản undo vừa ghi. Page thành dirty page (mục 4.4). Việc sửa sinh redo vào log
   buffer, page được gắn LSN mới (mục 5.3).
6. Nếu `balance` nằm trong một secondary index thì entry cũ bị delete-mark, entry mới được chèn (mục 6.3).
7. Tầng server sinh event binlog dạng ROW (dòng trước/sau) vào binlog cache của session (mục 9.1).

**Giai đoạn B: COMMIT (internal 2PC, mục 9.3)**

8. Prepare: InnoDB đánh dấu transaction prepared, redo được ghi và fsync (gom nhóm với các transaction
   khác nếu có, mục 9.4).
9. Binlog: event trong binlog cache được ghi vào file binlog, fsync. Điểm commit thật.
10. InnoDB commit: ghi dấu commit, nhả lock. Client nhận `Query OK, 1 row affected`.

**Giai đoạn C: sau khi đã trả lời client (giây tới phút sau)**

11. Page cleaner flush dirty page: ghi vào doublewrite file trước, rồi vào `accounts.ibd` (mục 7.2).
12. Checkpoint tiến lên, phần redo cũ được tái sử dụng (mục 5.4).
13. Khi không còn read view nào cần bản balance=500, purge giải phóng bản ghi undo đó (mục 6.4).
14. Binlog được replica kéo về và áp lại (chương 22); hết hạn thì file binlog bị xoá.

```
 Thời gian -->
 | A: buffer pool + undo + redo buffer + binlog cache | B: redo fsync -> binlog fsync -> commit | trả OK | C: flush page (doublewrite) ... checkpoint ... purge
                                                                                                ^
                                                    Tại đây: page dữ liệu CHƯA chắc đã xuống .ibd,
                                                    nhưng redo và binlog đã bền. Crash lúc này -> recovery áp redo.
```

Câu trả lời ngắn cho câu hỏi ở mục 1.1 "lúc COMMIT trả về, dữ liệu đã nằm trong file bảng chưa?":
**chưa chắc**, và không cần. Dữ liệu an toàn vì redo log (và binlog) đã được fsync; file bảng sẽ được cập
nhật sau.

---

## 11. Đối chiếu PostgreSQL

PostgreSQL giải cùng hai bài toán gốc (mục 1.2) nhưng chọn cách khác cho chuyện "bản cũ của dòng nằm ở
đâu". Chương 25 đối chiếu Postgres toàn diện; mục này chỉ tập trung vào phần lưu trữ.

### 11.1 Heap và tuple nhiều phiên bản

- Bảng Postgres là một *heap*: các dòng (gọi là *tuple*) nằm trong page 8 KB không theo thứ tự nào. Mọi
  index, kể cả primary key, đều là cấu trúc riêng trỏ tới vị trí vật lý của tuple (*ctid*: số page, số
  thứ tự trong page). Không có khái niệm clustered index như InnoDB.
- Mỗi tuple có hai trường hệ thống: `xmin` (transaction tạo ra tuple) và `xmax` (transaction xoá hoặc
  thay thế nó).
- `UPDATE` **không sửa tại chỗ**: nó ghi một tuple mới (xmin = transaction hiện tại) và đặt `xmax` cho
  tuple cũ. Bản cũ vẫn nằm trong chính file bảng, không có undo log riêng.
- `DELETE` chỉ đặt `xmax`.
- Tuple đã "chết" (không transaction nào còn nhìn thấy) gọi là *dead tuple*, chờ VACUUM dọn.

```
 InnoDB:   bảng [id=5 stock=7]  --roll_ptr-->  undo [stock=8] --> [stock=10]
           bản mới tại chỗ, bản cũ ở chỗ khác

 Postgres: heap page: [id=5 stock=10 xmin=100 xmax=250] [id=5 stock=8 xmin=250 xmax=300] [id=5 stock=7 xmin=300 xmax=0]
           mọi phiên bản cùng nằm trong bảng
```

Hệ quả của update "ghi tuple mới": tuple mới có ctid mới, nên về nguyên tắc **mọi index** của bảng phải
thêm entry trỏ tới nó, kể cả index trên cột không đổi. Postgres giảm chi phí này bằng *HOT update*
(heap-only tuple): nếu không cột nào có index bị đổi và page hiện tại còn chỗ, tuple mới nằm cùng page và
index không phải sửa.

### 11.2 VACUUM và bloat

VACUUM là "purge" của Postgres, nhưng gánh nhiều việc hơn:

- Dọn dead tuple trong bảng và index, đánh dấu chỗ trống để tái sử dụng. VACUUM thường **không** trả chỗ
  về hệ điều hành (trừ các page trống ở cuối file), giống InnoDB ở mục 3.7.
- Cập nhật *visibility map* (page nào chỉ chứa tuple mọi transaction đều thấy), thứ giúp index-only scan
  không phải đọc heap.
- Freeze tuple cũ để chống xid wraparound (mục 11.3).
- *Autovacuum* chạy nền tự động. `VACUUM FULL` thì viết lại toàn bộ bảng sang file mới, trả chỗ về OS,
  nhưng cần lock `ACCESS EXCLUSIVE` (chặn cả đọc lẫn ghi) và tốn thêm dung lượng cỡ bằng bảng trong lúc
  chạy; autovacuum không bao giờ chạy `VACUUM FULL`.

Khi vacuum không theo kịp lượng update/delete, bảng và index đầy dead tuple, phình ra: gọi là *bloat*.
Scan phải đọc nhiều page hơn, cache kém hơn.

Giống InnoDB: một transaction mở lâu giữ snapshot cũ thì VACUUM không được dọn những tuple mà
transaction đó còn có thể thấy. Ở Postgres còn có thêm các "cái neo" khác: replication slot bị bỏ quên,
`hot_standby_feedback` từ replica có query dài.

### 11.3 Transaction ID wraparound

Theo tài liệu PostgreSQL:

- XID là số 32 bit, so sánh theo kiểu vòng tròn (modulo 2^32): với mỗi XID có khoảng hai tỉ XID "cũ hơn"
  và hai tỉ XID "mới hơn". Một tuple tồn tại quá hai tỉ transaction mà chưa được xử lý thì bỗng nhiên trông
  như "ở tương lai" và trở nên vô hình: tài liệu gọi đây là mất dữ liệu thảm khốc (dữ liệu vẫn còn, nhưng
  không đọc được).
- Lời giải: VACUUM *freeze* các tuple đủ cũ, đánh dấu chúng là "luôn ở quá khứ". Mỗi bảng phải được vacuum
  (freeze) ít nhất một lần mỗi hai tỉ transaction.
- Autovacuum tự chạy chống wraparound khi tuổi XID cũ nhất của bảng vượt `autovacuum_freeze_max_age`
  (mặc định 200 triệu), kể cả khi autovacuum bị tắt.
- Nếu vẫn bị bỏ qua: khi còn 40 triệu transaction tới điểm wraparound, Postgres bắt đầu cảnh báo; khi còn
  dưới 3 triệu, nó **từ chối cấp XID mới**, tức không nhận thêm thao tác ghi, cho tới khi có người chạy
  VACUUM.

InnoDB không có vấn đề tương tự: trx id của nó 6 byte (48 bit), và phiên bản cũ nằm ở undo nên được purge
dọn đi chứ không ở lại trong bảng chờ freeze.

### 11.4 WAL và rollback

- Postgres có **một** WAL duy nhất phục vụ cả crash recovery lẫn replication (streaming replication gửi
  chính WAL sang replica; logical replication giải mã WAL thành thay đổi logic). MySQL có hai log (redo
  của InnoDB, binlog của server) và cần 2PC nội bộ để giữ chúng khớp.
- Chống torn page: Postgres ghi nguyên page vào WAL lần đầu page bị sửa sau mỗi checkpoint
  (`full_page_writes`), InnoDB dùng doublewrite (mục 7).
- Rollback ở Postgres gần như tức thì: chỉ cần ghi nhận transaction là aborted; các tuple nó tạo ra trở
  thành rác cho VACUUM. Rollback ở InnoDB phải áp ngược undo, lâu với transaction lớn.

| Khía cạnh | InnoDB | PostgreSQL |
|---|---|---|
| Tổ chức bảng | Clustered index theo PK | Heap, mọi index trỏ tới ctid |
| Bản cũ của dòng | Undo log, tách khỏi bảng | Tuple cũ ngay trong heap |
| UPDATE | Sửa tại chỗ, bản cũ sang undo | Ghi tuple mới, đánh dấu tuple cũ |
| Dọn dẹp | Purge thread | VACUUM / autovacuum |
| Không dọn kịp | Undo phình, HLL cao, đọc chậm | Bloat bảng và index |
| Rollback | Áp ngược undo (tốn thời gian) | Gần như tức thì |
| Log | Redo (vật lý) + binlog (logic) + 2PC | Một WAL |
| Chống torn page | Doublewrite | Full page writes trong WAL |
| Rủi ro riêng | Transaction mở lâu chặn purge | Thêm xid wraparound, cần freeze |

---

## 12. LSM tree: một hướng khác để lưu dữ liệu

InnoDB và Postgres đều dựa trên B+tree (hoặc heap) và **sửa page tại chỗ**. Có một họ storage engine khác
đi theo hướng ngược lại: không bao giờ sửa tại chỗ, chỉ ghi nối. Đó là *LSM tree* (*log-structured merge
tree*), dùng trong RocksDB, LevelDB, Cassandra, ScyllaDB, và MyRocks (storage engine dựa trên RocksDB cho
MySQL, có trong Percona Server và MariaDB, không có trong MySQL bản Oracle).

Cách hoạt động, ở mức khái niệm:

1. Ghi: thêm bản ghi vào WAL (để bền) và vào *memtable*, một cấu trúc sắp xếp trong RAM.
2. Memtable đầy thì được ghi nguyên khối ra đĩa thành một *SSTable* (sorted string table): file bất biến,
   đã sắp theo key. Ghi tuần tự, rất nhanh.
3. Xoá không xoá gì cả: ghi một bản ghi đặc biệt *tombstone* ("key này đã bị xoá"). Update cũng chỉ là ghi
   bản mới.
4. *Compaction* chạy nền: gộp nhiều SSTable thành SSTable lớn hơn, bỏ bản cũ và tombstone.
5. Đọc một key: xem memtable, rồi các SSTable từ mới tới cũ. *Bloom filter* trên mỗi file cho biết nhanh
   "chắc chắn không có key này ở đây" để bỏ qua file đó.

```
 ghi --> [WAL]          
     \-> [memtable (RAM)] --đầy--> SSTable mới nhất
                                   SSTable ...          --compaction--> SSTable lớn, đã gộp
                                   SSTable cũ nhất
 đọc: memtable -> SSTable mới -> ... -> SSTable cũ (bloom filter giúp bỏ qua)
```

| Tiêu chí | B+tree (InnoDB) | LSM tree |
|---|---|---|
| Ghi | Sửa page ngẫu nhiên (kèm redo) | Ghi tuần tự, thông lượng ghi cao |
| Đọc theo key | Một đường gốc tới lá, ổn định | Có thể phải xem nhiều file |
| Khuếch đại ghi | Sửa vài byte vẫn phải ghi cả page 16 KB (cộng doublewrite) | Compaction ghi lại dữ liệu nhiều lần |
| Nén | Kém hơn (page chừa chỗ trống) | Tốt (file bất biến, sắp xếp) |
| Hợp với | OLTP đọc nhiều, cần độ trễ đọc ổn định | Ghi rất dày: log, metric, time series, event |

Bạn không cần dùng LSM tree khi làm việc với MySQL thông thường; mục này để bạn nhận ra rằng các đánh đổi
trong chương (ghi tại chỗ hay ghi nối, dọn rác lúc nào, khuếch đại ghi ở đâu) là lựa chọn thiết kế, không
phải chân lý duy nhất. Chương 3 của sách *Designing Data-Intensive Applications* trình bày kỹ hai hướng này.

---

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Để `innodb_buffer_pool_size` mặc định 128 MB trên production | Working set không vừa RAM, query liên tục đọc đĩa | Đặt theo RAM của máy (tới khoảng 80% trên máy chỉ chạy MySQL), theo dõi hit rate |
| Cấp buffer pool gần hết RAM | Hệ điều hành và bộ nhớ theo connection không còn chỗ, máy swap | Chừa phần cho OS, connection, binlog cache; theo dõi swap |
| Mở transaction rồi chờ người dùng, gọi API, hoặc quên commit trong console/worker | Read view cũ chặn purge, HLL tăng, undo phình, mọi đọc chậm dần (mục 6.5) | Transaction ngắn; cảnh báo transaction sống lâu trong `INNODB_TRX` và HLL cao |
| Nghĩ transaction chỉ `SELECT` thì vô hại | Nó vẫn giữ read view | Commit đều đặn kể cả transaction chỉ đọc |
| Hạ `sync_binlog` hoặc `innodb_flush_log_at_trx_commit` trên primary cho "nhanh" | Mất điện có thể mất giao dịch đã báo commit, redo và binlog lệch, replica lệch | Giữ 1/1 trên primary; chỉ hạ ở nơi chấp nhận mất dữ liệu |
| Tin rằng `DELETE` nhiều sẽ làm file `.ibd` nhỏ đi | Chỗ trống được giữ lại trong tablespace | Dùng `DROP`/`TRUNCATE` khi xoá hết; dựng lại bảng (`OPTIMIZE TABLE`, hoặc công cụ online ở chương 20) khi thật cần thu hồi |
| Tắt doublewrite để tăng tốc ghi | Mất điện có thể để lại page hỏng mà redo không sửa được | Giữ `innodb_doublewrite=ON` trừ khi thiết bị đảm bảo ghi nguyên tử nguyên page |
| `redo log` quá nhỏ cho tải ghi lớn | Checkpoint bị dí, flush gấp, ghi khựng từng đợt | Tăng `innodb_redo_log_capacity`, theo dõi khoảng cách current LSN và checkpoint LSN |
| Rollback hoặc kill một transaction khổng lồ rồi chờ nó dừng ngay | Rollback phải áp ngược undo, có thể lâu như lúc chạy | Chia việc lớn thành lô nhỏ, mỗi lô commit riêng |
| Trộn bảng MyISAM và InnoDB trong một transaction | Phần MyISAM không rollback được | Dùng InnoDB cho mọi bảng nghiệp vụ |
| `SELECT *` trên bảng có cột `TEXT`/`BLOB` lớn | Phải đọc thêm overflow page, tốn I/O và buffer pool | Chỉ lấy cột cần; tách cột lớn ít dùng sang bảng riêng |
| Đọc tài liệu cũ rồi cấu hình `query_cache_size`, `innodb_log_file_size`, hoặc tin AHI/change buffer bật sẵn | Query cache đã bị gỡ từ 8.0; redo log cấu hình bằng `innodb_redo_log_capacity` từ 8.0.30; MySQL 8.4 tắt mặc định AHI và change buffer | Luôn kiểm tra tài liệu đúng phiên bản (8.4) |

## Tóm tắt chương

- MySQL chia hai tầng: tầng server (parser, optimizer, executor, binlog, quyền) và storage engine
  (lưu trữ, index, transaction, lock, recovery), nói chuyện qua handler API. InnoDB là engine mặc định.
- Dữ liệu InnoDB nằm trong tablespace (mặc định mỗi bảng một file `.ibd`), chia thành segment, extent
  (1 MB) và page (16 KB). Bảng là clustered index; record DYNAMIC có hai cột ẩn `DB_TRX_ID`,
  `DB_ROLL_PTR`; cột dài bị đẩy ra overflow page.
- Mọi đọc ghi diễn ra trên buffer pool; LRU có midpoint chống quét lớn đẩy dữ liệu nóng ra; dirty page
  được flush nền, không phải lúc commit.
- Redo log là write-ahead log: commit chỉ cần fsync redo (nhỏ, tuần tự); crash thì áp lại redo từ
  checkpoint. `innodb_flush_log_at_trx_commit=1` là mặc định bền.
- Undo log phục vụ rollback và MVCC qua version chain; purge dọn bản cũ khi không còn read view nào cần.
  Transaction mở lâu, kể cả chỉ đọc, làm history list length tăng và cả hệ thống chậm dần.
- Doublewrite chống torn page, thứ redo không sửa được. Change buffer và AHI là tối ưu tuỳ chọn, MySQL
  8.4 tắt mặc định.
- Binlog là log logic của tầng server cho replication và PITR. Internal 2PC (prepare InnoDB, ghi binlog,
  commit InnoDB) đảm bảo redo và binlog luôn khớp; binlog là điểm commit thật. Group commit giúp fsync
  mỗi commit vẫn có throughput cao.
- Giữ `sync_binlog=1` và `innodb_flush_log_at_trx_commit=1` trên primary; hạ xuống là chấp nhận mất dữ
  liệu và lệch replica khi mất điện.
- Postgres lưu bản cũ ngay trong heap, dọn bằng VACUUM, có rủi ro bloat và xid wraparound, dùng một WAL
  duy nhất. LSM tree chỉ ghi nối và compaction, hợp với tải ghi rất dày.

## Câu hỏi tự kiểm tra

1. Một tính năng như "kiểm tra quyền", "lock dòng", "ghi binlog", "crash recovery" thuộc tầng server hay
   tầng storage engine? Hệ quả khi một transaction đụng cả bảng InnoDB lẫn MyISAM là gì? (mục 2.3)
2. Vì sao InnoDB không ghi page dữ liệu xuống đĩa lúc `COMMIT` mà vẫn đảm bảo durability? Quy tắc
   "write-ahead" gồm hai vế nào? (mục 5.1)
3. Giải thích vì sao một lần `mysqldump` quét toàn bộ bảng lớn không đẩy dữ liệu nóng ra khỏi buffer pool.
   Vai trò của `innodb_old_blocks_time` là gì? (mục 4.3)
4. Checkpoint là gì? Redo log quá nhỏ gây triệu chứng gì, quá lớn thì sao? (mục 5.4)
5. Sau crash, InnoDB làm những bước gì trước và sau khi nhận connection? Vì sao page của transaction chưa
   commit có thể đã nằm trên đĩa mà vẫn không sao? (mục 5.5)
6. Một transaction chỉ chạy `SELECT` rồi để mở ba tiếng. Mô tả chuỗi hậu quả bên trong InnoDB và cách bạn
   tìm ra nó. (mục 6.4, 6.5)
7. Vì sao redo log không cứu được torn page, và doublewrite cứu bằng cách nào? (mục 7)
8. Trình bày internal two-phase commit giữa InnoDB và binlog. Với mỗi điểm crash có thể, recovery quyết
   định commit hay rollback dựa vào đâu? (mục 9.3)
9. So sánh `innodb_flush_log_at_trx_commit` bằng 0, 1, 2 khi (a) chỉ mysqld chết, (b) mất điện. (mục 5.6,
   9.5)
10. Nêu ba khác biệt giữa MVCC của InnoDB và Postgres, và vì sao chỉ Postgres có rủi ro xid wraparound.
    (mục 11)

## Bài tập

1. **Quan sát file trên đĩa.** Trên container MySQL 8.4, liệt kê data directory và chỉ ra file nào là
   system tablespace, data dictionary, undo tablespace, redo log, doublewrite, binlog, và file `.ibd`
   của một bảng bạn tạo. Dùng `information_schema.INNODB_TABLESPACES` để đối chiếu kích thước. Sau đó làm
   lại thí nghiệm ở mục 3.7: chèn khoảng 250 nghìn dòng, xoá một nửa, so sánh `FILE_SIZE` trước và sau
   `DELETE`, rồi sau `OPTIMIZE TABLE`. Ghi lại số liệu và giải thích.
2. **Đo redo và binlog sinh ra.** Ghi lại `Innodb_redo_log_current_lsn` và kích thước binlog hiện tại
   (`SHOW BINARY LOGS`). Chạy 10.000 câu `UPDATE` một dòng (dùng procedure như mục 6.5), rồi đo lại. Tính
   trung bình mỗi update sinh bao nhiêu byte redo và bao nhiêu byte binlog. Thử lại với một câu `UPDATE`
   duy nhất sửa 10.000 dòng. So sánh và giải thích chênh lệch (gợi ý: binlog ROW, group commit, overhead
   mỗi transaction).
3. **Tái hiện history list length.** Làm đúng timeline ở mục 6.5 với hai session. Ở mỗi bước, ghi lại
   `History list length` và thời gian của câu `SELECT` ở session A. Sau đó lặp lại với session A dùng
   `READ COMMITTED` (chương 14) và giải thích vì sao kết quả khác (hoặc giống).
4. **Viết bằng lời của bạn.** Viết một trang (không quá 400 từ) trả lời câu phỏng vấn "Từ lúc gửi
   `UPDATE` tới lúc dữ liệu an toàn trên đĩa, chuyện gì xảy ra?" mà không nhìn lại mục 10. Sau đó so với
   mục 10 và đánh dấu những bước bạn bỏ sót.

## Đọc thêm

- MySQL 8.4 Reference Manual:
  [InnoDB Architecture](https://dev.mysql.com/doc/refman/8.4/en/innodb-architecture.html) ·
  [Overview of MySQL Storage Engine Architecture](https://dev.mysql.com/doc/refman/8.4/en/pluggable-storage-overview.html) ·
  [Buffer Pool](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html) ·
  [Making the Buffer Pool Scan Resistant](https://dev.mysql.com/doc/refman/8.4/en/innodb-performance-midpoint_insertion.html) ·
  [Configuring Buffer Pool Flushing](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool-flushing.html) ·
  [Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html) ·
  [InnoDB Checkpoints](https://dev.mysql.com/doc/refman/8.4/en/innodb-checkpoints.html) ·
  [InnoDB Recovery](https://dev.mysql.com/doc/refman/8.4/en/innodb-recovery.html) ·
  [Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html) ·
  [Undo Tablespaces](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-tablespaces.html) ·
  [InnoDB Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html) ·
  [Purge Configuration](https://dev.mysql.com/doc/refman/8.4/en/innodb-purge-configuration.html) ·
  [Doublewrite Buffer](https://dev.mysql.com/doc/refman/8.4/en/innodb-doublewrite-buffer.html) ·
  [Change Buffer](https://dev.mysql.com/doc/refman/8.4/en/innodb-change-buffer.html) ·
  [Adaptive Hash Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-adaptive-hash.html) ·
  [File Space Management](https://dev.mysql.com/doc/refman/8.4/en/innodb-file-space.html) ·
  [Physical Structure of an InnoDB Index](https://dev.mysql.com/doc/refman/8.4/en/innodb-physical-structure.html) ·
  [InnoDB Row Formats](https://dev.mysql.com/doc/refman/8.4/en/innodb-row-format.html) ·
  [Limits on Table Column Count and Row Size](https://dev.mysql.com/doc/refman/8.4/en/column-count-limit.html) ·
  [The Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html) ·
  [Binary Logging Options and Variables (sync_binlog)](https://dev.mysql.com/doc/refman/8.4/en/replication-options-binary-log.html) ·
  [InnoDB Startup Options and System Variables](https://dev.mysql.com/doc/refman/8.4/en/innodb-parameters.html) ·
  [What Is New in MySQL 8.4 since MySQL 8.0](https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html) (bảng giá trị mặc định InnoDB thay đổi) ·
  [MySQL Data Dictionary](https://dev.mysql.com/doc/refman/8.4/en/data-dictionary.html)
- Jeremy Cole:
  [The basics of InnoDB space file layout](https://blog.jcole.us/2013/01/03/the-basics-of-innodb-space-file-layout/) ·
  [The physical structure of InnoDB index pages](https://blog.jcole.us/2013/01/07/the-physical-structure-of-innodb-index-pages/) ·
  [The basics of the InnoDB undo logging and history system](https://blog.jcole.us/2014/04/16/the-basics-of-the-innodb-undo-logging-and-history-system/)
- PostgreSQL 18 docs:
  [Routine Vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html) ·
  [MVCC](https://www.postgresql.org/docs/18/mvcc-intro.html) ·
  [Reliability and the Write-Ahead Log](https://www.postgresql.org/docs/18/wal.html)
- Martin Kleppmann, *Designing Data-Intensive Applications*, chương 3 (B-tree và LSM tree) và chương 7
  (transaction).
