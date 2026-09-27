# 03. Database quan hệ và SQL

> [← Mục lục](README.md) · **[📖 Bài đọc kiến thức](kien-thuc/03-database-sql.md)** · Trọng tâm: **MySQL 8.4 LTS / InnoDB** (stack PHP), đối chiếu PostgreSQL 17–18.
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
| [MySQL 8.4 Reference Manual](https://dev.mysql.com/doc/refman/8.4/en/) | Official docs | Nguồn chuẩn cho mọi hành vi của MySQL. Khi blog và docs mâu thuẫn, tin docs |
| [Use The Index, Luke](https://use-the-index-luke.com/) | Sách online miễn phí | Index và query, viết cho developer. **Đọc hết**, khoảng 1 tuần |
| *High Performance MySQL*, 4th ed. (Botros, Tinley; O'Reilly 2021) | Sách | Schema, index, query, replication, vận hành MySQL |
| [*Designing Data-Intensive Applications*](https://dataintensive.net/) (Kleppmann) | Sách | Ch.3 storage, ch.5 replication, ch.6 partitioning, **ch.7 transactions** (số chương theo bản 1) |
| [PostgreSQL docs](https://www.postgresql.org/docs/current/) | Official docs | Đối chiếu. Phần MVCC và isolation viết rất rõ, nên đọc kể cả khi dùng MySQL |
| [Jeremy Cole: InnoDB internals](https://blog.jcole.us/innodb/) | Blog | Cấu trúc page, B+tree, record của InnoDB, có hình vẽ |
| [CMU 15-445 Database Systems](https://15445.courses.cs.cmu.edu/) | Khoá học (video + slide) | Nếu muốn hiểu từ gốc: storage, index, concurrency control, recovery |
| [Laravel docs](https://laravel.com/docs/database) | Official docs | Tầng DB của Laravel: query builder, Eloquent, transaction, migration |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Viết SQL đúng, hiểu index và transaction ở mức dùng được | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.8 | Tự tối ưu query, chọn đúng lock, thiết kế schema, không dính bẫy của ORM | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.7 | Hiểu cơ chế bên trong, vận hành, thay đổi schema online, scale, so sánh được các DB | 10–12 ngày |

Học theo thứ tự: chặng 2 cần mô hình B+tree của chặng 1, và chặng 3 giải thích *vì sao* các
hành vi ở chặng 2 xảy ra. Với senior, nếu còn ô nào ở chặng 1–2 chưa tick được thì đó là lỗ
hổng nguy hiểm nhất, vì người phỏng vấn thường mở đầu bằng câu dễ rồi đào sâu dần.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 SQL viết tay

**Vì sao cần học:** Vòng live coding thường có bài SQL. Viết JOIN sai hay xử lý NULL sai là
lỗi production rất phổ biến, và loại lỗi này không làm hệ thống sập mà chỉ làm **báo cáo ra số
sai**, nên không ai biết để sửa.

**Học gì**

*Các kiểu JOIN*
- `INNER JOIN` chỉ giữ những cặp dòng khớp ở cả hai bảng.
  - Ví dụ: `users INNER JOIN orders` thì user chưa có đơn nào bị loại khỏi kết quả.
- `LEFT JOIN` giữ **mọi dòng của bảng bên trái**. Dòng nào không có bên phải khớp thì các cột
  của bảng phải là NULL.
  - Dùng khi cần "lấy mọi user, kèm đơn hàng nếu có".
- `CROSS JOIN` ghép mọi dòng bảng này với mọi dòng bảng kia, tức m × n dòng.
- *Self join* là join một bảng với chính nó.
  - Ví dụ: nhân viên và quản lý cùng nằm trong bảng `employees`, nối qua cột `manager_id`.
- MySQL không có `FULL OUTER JOIN`. Muốn có thì giả lập bằng `LEFT JOIN ... UNION ... RIGHT JOIN`.
- *Anti-join* nghĩa là "lấy những dòng A không có B tương ứng". Có hai cách viết:
  - `LEFT JOIN b ON ... WHERE b.id IS NULL`
  - `WHERE NOT EXISTS (SELECT 1 FROM b WHERE ...)`
- ⚠️ **Bẫy 1: LEFT JOIN bị biến thành INNER JOIN mà không biết.**

  ```sql
  -- Muốn: mọi user, kèm đơn đã thanh toán nếu có
  SELECT u.id, o.id FROM users u
  LEFT JOIN orders o ON o.user_id = u.id
  WHERE o.status = 'paid';          -- SAI: user không có đơn có o.status = NULL, bị WHERE loại

  SELECT u.id, o.id FROM users u
  LEFT JOIN orders o ON o.user_id = u.id AND o.status = 'paid';   -- ĐÚNG: điều kiện nằm ở ON
  ```
- ⚠️ **Bẫy 2: fan-out (nhân dòng).**
  - Ví dụ: `orders JOIN order_items` với một đơn có 3 item sinh ra 3 dòng cho đơn đó. Khi đó
    `SUM(orders.total)` cộng tổng tiền của đơn 3 lần.
  - Cách sửa: gom nhóm trong subquery trước, rồi mới join.

*Thứ tự thực thi logic*
- Bạn viết theo thứ tự `SELECT ... FROM ... WHERE ... GROUP BY ... HAVING ... ORDER BY ... LIMIT`.
  Nhưng về logic, DB xử lý theo thứ tự khác: `FROM`/`JOIN` → `WHERE` → `GROUP BY` → `HAVING` →
  window function → `SELECT` → `ORDER BY` → `LIMIT`.
- Hệ quả:
  - `WHERE` không dùng được alias đặt ở `SELECT`, vì lúc `WHERE` chạy thì alias chưa tồn tại.
  - `ORDER BY` thì dùng được alias.
- `WHERE` lọc **từng dòng** trước khi gom nhóm. `HAVING` lọc **từng nhóm** sau khi gom, nên
  dùng được `COUNT`, `SUM`.
- `ONLY_FULL_GROUP_BY` là chế độ bắt mọi cột trong `SELECT` phải nằm trong `GROUP BY` hoặc nằm
  trong một hàm aggregate. MySQL bật mặc định từ 5.7.
  - ⚠️ Nếu tắt, MySQL trả về giá trị tuỳ ý của nhóm, gây bug ngầm.

*Subquery và UNION*
- Subquery là một câu `SELECT` lồng trong câu khác.
- *Correlated subquery* là subquery tham chiếu cột của câu bên ngoài. Về logic, nó chạy lại cho
  mỗi dòng bên ngoài; trên thực tế optimizer thường viết lại thành join.
- `IN` và `EXISTS`: optimizer hiện đại xử lý hai cái gần như nhau về tốc độ. Khác biệt thật nằm
  ở chỗ gặp NULL khi dùng `NOT IN` (xem phần dưới).
- `UNION` khử các dòng trùng, nên phải sort hoặc hash thêm. `UNION ALL` giữ nguyên nên nhanh
  hơn. Dùng `UNION ALL` khi biết chắc không có dòng trùng.

*NULL*
- NULL nghĩa là "không biết giá trị". So sánh bất kỳ thứ gì với NULL cho ra `UNKNOWN` (không
  phải `TRUE`, cũng không phải `FALSE`), và `WHERE` chỉ giữ dòng có kết quả `TRUE`.
  - `NULL = NULL` cho ra `UNKNOWN`. Muốn kiểm tra NULL thì dùng `IS NULL`.
  - MySQL có toán tử `<=>` so sánh an toàn với NULL: `NULL <=> NULL` bằng 1.
- ⚠️ `x NOT IN (1, NULL)` không bao giờ đúng, vì `x <> NULL` là `UNKNOWN`.
  - Hệ quả: `NOT IN (subquery)` mà subquery trả về dù chỉ một NULL thì kết quả **rỗng**.
  - Dùng `NOT EXISTS` thay cho `NOT IN`.
- Hàm aggregate:
  - `COUNT(*)` đếm số dòng; `COUNT(col)` bỏ qua các giá trị NULL.
  - `SUM` và `AVG` bỏ qua NULL.
  - `SUM` của tập rỗng là NULL, không phải 0. Viết `COALESCE(SUM(x), 0)`.

**Đọc**
- [SQLBolt](https://sqlbolt.com/): bài tập tương tác, nếu cần ôn lại cú pháp
- [modern-sql.com](https://modern-sql.com/): cách SQL chuẩn hoạt động và mức hỗ trợ của từng DB
- MySQL: [SQL mode](https://dev.mysql.com/doc/refman/8.4/en/sql-mode.html) (`ONLY_FULL_GROUP_BY`, strict mode)

**Nắm chắc khi**
- [ ] Viết được anti-join theo 3 cách và chỉ ra cách nào sai khi có NULL
- [ ] Giải thích được vì sao `WHERE` không dùng được alias trong `SELECT`
- [ ] Nhìn một query join 1-n có `SUM`, chỉ ra được chỗ bị nhân dòng và sửa được
- [ ] Nói được kết quả của `NULL = NULL`, `NULL <=> NULL`, `x NOT IN (1, NULL)`

#### 1.2 Index cơ bản

**Vì sao cần học:** Đây là chủ đề được hỏi nhiều nhất trong mảng database. Phần lớn sự cố "DB
chậm" trên thực tế là do thiếu index hoặc có index nhưng không được dùng.

**Học gì**

*Index là gì*
- Khi không có index, câu `WHERE email = ?` phải đọc từng dòng của bảng. Cách này gọi là
  *full table scan*.
- Index là một bản sao của một hoặc vài cột, **được sắp xếp sẵn**, kèm cách tìm về dòng đầy đủ.
  Giống mục lục cuối sách: tra chữ cái là biết trang.
- Cái giá của index:
  - Mỗi lần `INSERT`/`UPDATE`/`DELETE` phải sửa thêm mọi index của bảng.
  - Tốn thêm đĩa và RAM.

*Vì sao là B+tree*
- DB đọc đĩa theo từng khối gọi là *page* (InnoDB: 16 KB), không đọc từng dòng.
- B+tree là một cây mà mỗi node là một page, chứa hàng trăm key.
  - Vì mỗi node chứa rất nhiều key nên cây rất thấp: 3–4 tầng đủ cho hàng trăm triệu dòng.
  - Tìm một dòng chỉ cần đọc 3–4 page, và các tầng trên thường đã nằm sẵn trong RAM.
- Dữ liệu chỉ nằm ở tầng lá, và các lá nối với nhau thành một danh sách. Nhờ vậy `BETWEEN`,
  `>` và `ORDER BY` chỉ cần đi dọc theo các lá.
- Vì sao không dùng cấu trúc khác:
  - Binary tree: mỗi node chỉ có 1 key, nên cây cao khoảng 30 tầng cho 1 tỉ dòng, và mỗi tầng
    là một lần đọc đĩa.
  - Hash: tra `=` rất nhanh, nhưng không làm được range, sort hay prefix.

*Composite index và leftmost prefix*
- Index nhiều cột `(a, b, c)` được sắp theo `a`; trong cùng `a` thì sắp theo `b`; trong cùng `b`
  thì sắp theo `c`. Giống danh bạ sắp theo họ, rồi tên đệm, rồi tên.
- Vì vậy index này chỉ dùng để tra được khi điều kiện **bắt đầu từ cột đầu**: `a`, `a + b`, hoặc
  `a + b + c`.
- Có `b` hoặc `c` mà thiếu `a` thì không tra được, giống biết tên mà không biết họ thì không tìm
  được trong danh bạ.

*Khi có index mà không được dùng*
- **Bọc hàm quanh cột:** `WHERE DATE(created_at) = '2026-01-01'`. Index sắp theo `created_at`,
  không sắp theo `DATE(created_at)`.
  - Sửa thành `created_at >= '2026-01-01' AND created_at < '2026-01-02'`.
- **`LIKE '%abc'`:** ký tự đại diện ở đầu thì không biết bắt đầu tìm từ đâu trong cây.
  `LIKE 'abc%'` thì dùng index được.
- **Ép kiểu ngầm:** cột `phone` kiểu `VARCHAR` mà viết `WHERE phone = 912345678` (số, không có
  dấu nháy). MySQL phải đổi từng dòng sang số rồi mới so sánh.
- **Selectivity thấp:** `WHERE gender = 'F'` khớp khoảng 50% bảng. Đọc thẳng cả bảng khi đó rẻ
  hơn đi qua index rồi nhảy tới từng dòng, nên optimizer bỏ index. Đây là quyết định đúng.

*Khi không nên thêm index*
- Bảng nhỏ (vài nghìn dòng).
- Bảng ghi rất nhiều nhưng ít đọc, ví dụ bảng log.
- Đã có index chứa sẵn cột đó ở đầu: có `(a, b)` rồi thì thêm `(a)` là thừa.

**Đọc**
- Use The Index, Luke: [Anatomy of an Index](https://use-the-index-luke.com/sql/anatomy) và [Concatenated Keys](https://use-the-index-luke.com/sql/where-clause/the-equals-operator/concatenated-keys)
- MySQL: [Multiple-Column Indexes](https://dev.mysql.com/doc/refman/8.4/en/multiple-column-indexes.html)

**Nắm chắc khi**
- [ ] Vẽ được B+tree 3 tầng và chỉ ra đường đi của một range query
- [ ] Với index `(a, b, c)`, nói ngay được query nào seek được, query nào không
- [ ] Sửa được `WHERE DATE(created_at) = ?` thành dạng dùng được index
- [ ] Kể được 3 cái giá của index

#### 1.3 Transaction cơ bản

**Vì sao cần học:** Mọi luồng liên quan tới tiền và tồn kho đều cần transaction. Bẫy hay gặp
nhất là nghĩ "đã bọc trong transaction là an toàn".

**Học gì**

*Transaction là gì*
- Transaction gom nhiều câu lệnh thành một khối. Hoặc tất cả đều có hiệu lực (`COMMIT`), hoặc
  không câu nào có hiệu lực (`ROLLBACK`).
- *Autocommit*: nếu bạn không mở transaction, MySQL coi mỗi câu lệnh lẻ là một transaction riêng
  và tự commit ngay sau đó.

*ACID, mỗi chữ một ví dụ*
- **A, Atomicity (nguyên tử):** chuyển tiền thì trừ tài khoản A và cộng tài khoản B cùng thành
  công hoặc cùng bị huỷ. Không bao giờ có trạng thái "đã trừ mà chưa cộng".
- **C, Consistency (nhất quán):** dữ liệu luôn thoả các ràng buộc (unique, khoá ngoại, `CHECK`).
  - DB chỉ giữ những ràng buộc đã được khai báo.
  - Luật nghiệp vụ như "số dư không được âm" mà không khai báo thì là việc của ứng dụng.
- **I, Isolation (cô lập):** các transaction chạy cùng lúc không thấy trạng thái dở dang của
  nhau. Mức "không thấy" tới đâu tuỳ vào *isolation level* (module 2.5), và mức mặc định yếu hơn
  bạn nghĩ.
- **D, Durability (bền vững):** đã `COMMIT` thì mất điện cũng không mất dữ liệu.
  - DB làm được điều này vì trước khi báo commit thành công, nó ghi log thay đổi xuống đĩa và
    gọi `fsync` để chắc chắn log đã thật sự nằm trên đĩa (module 3.1).

*Hai bẫy*
- ⚠️ **Transaction không tự chống lost update.** Ví dụ, tồn kho còn 1 và hai request chạy cùng lúc:
  1. Cả hai cùng đọc được `stock = 1`.
  2. Cả hai cùng thấy còn hàng.
  3. Cả hai cùng ghi `stock = 0` và cùng tạo đơn.

  Kết quả là bán 2 món khi chỉ có 1, dù cả hai request đều chạy trong transaction. Cách chống
  nằm ở module 2.5 và 2.6.
- ⚠️ **Không gọi API ngoài, gửi email hay upload file bên trong transaction.**
  - API chậm 30 giây nghĩa là giữ lock trên DB 30 giây.
  - Rollback DB không thu hồi được email đã gửi đi.

**Đọc**
- DDIA ch.7, phần đầu (ACID)
- Laravel: [Database Transactions](https://laravel.com/docs/database#database-transactions)

**Nắm chắc khi**
- [ ] Giải thích được Durability dựa vào đâu (WAL/redo log + fsync)
- [ ] Nói được vì sao "đã bọc trong transaction" vẫn có thể bán quá tồn kho

#### 1.4 Kiểu dữ liệu và schema cơ bản

**Vì sao cần học:** Chọn sai kiểu dữ liệu rất khó sửa khi bảng đã lớn. Tiền và thời gian là
nguồn bug kinh điển, nhất là ở Việt Nam với múi giờ UTC+7.

**Học gì**

*Normalization (chuẩn hoá)*
- Mục tiêu: mỗi sự thật chỉ lưu ở một chỗ, để khi sửa chỉ cần sửa một chỗ là mọi nơi đều đúng.
- Ba dạng chuẩn:
  - **1NF**: mỗi ô chứa một giá trị. Không lưu `"tag1,tag2"` trong một cột.
  - **2NF**: nếu khoá chính gồm nhiều cột, các cột khác phải phụ thuộc vào **toàn bộ** khoá chứ
    không chỉ một phần.
  - **3NF**: không có cột phụ thuộc gián tiếp. Bảng `orders` lưu `customer_id`, không lưu kèm
    `customer_city`, vì thành phố là thông tin của khách hàng.
- Các loại quan hệ:
  - 1-n: khoá ngoại nằm ở bảng bên "nhiều", ví dụ `orders.user_id`.
  - n-n: dùng bảng trung gian, ví dụ `user_roles(user_id, role_id)`, và đặt unique trên cặp cột.
  - 1-1: thường dùng để tách các cột ít dùng hoặc rất lớn ra một bảng riêng.

*Tiền*
- ⚠️ Không dùng `FLOAT`/`DOUBLE`. Số thực nhị phân không biểu diễn chính xác được `0.1`, nên cộng
  dồn nhiều lần sẽ lệch.
- Có hai cách đúng:
  - `DECIMAL(19,4)`: lưu chính xác theo số chữ số thập phân đã khai.
  - `BIGINT` theo đơn vị nhỏ nhất: đồng với VND, cent với USD.
- Luôn lưu kèm mã tiền tệ.

*Thời gian*
- `DATETIME` lưu đúng con số bạn đưa vào và không có khái niệm timezone.
- `TIMESTAMP` bị MySQL quy đổi: khi lưu, đổi từ timezone của session sang UTC; khi đọc, đổi
  ngược lại. Kiểu này chỉ lưu được tới 2038-01-19.
- Nguyên tắc chung:
  - Lưu UTC, chỉ đổi sang timezone của người dùng khi hiển thị.
  - Timezone của PHP (`date.timezone`, khoá `timezone` trong `config/app.php` của Laravel) và timezone của session MySQL
    phải thống nhất.
- ⚠️ Bug "lệch 7 tiếng": PHP chạy UTC+7, session MySQL để UTC, cột kiểu `TIMESTAMP`. Giá trị bị
  quy đổi thêm một lần ngoài ý muốn.

*Chuỗi*
- `utf8` cũ của MySQL thực chất là `utf8mb3`, tối đa 3 byte mỗi ký tự, nên không lưu được emoji.
  Luôn dùng `utf8mb4`.
- *Collation* là bộ luật so sánh và sắp xếp chuỗi. Mặc định là `utf8mb4_0900_ai_ci`:
  - `ai` (accent-insensitive): không phân biệt dấu.
  - `ci` (case-insensitive): không phân biệt hoa thường.
- ⚠️ Vì vậy `'Hà' = 'Ha'` là đúng, và unique index coi hai giá trị này là trùng. Cần phân biệt
  dấu thì dùng collation `_as_cs` hoặc `_bin`.

*Id*
- Dùng `BIGINT` cho id. `INT` hết ở khoảng 2,1 tỉ, và đổi kiểu primary key trên một bảng lớn
  rất vất vả.

**Đọc**
- MySQL: [Fixed-Point Types](https://dev.mysql.com/doc/refman/8.4/en/fixed-point-types.html), [DATETIME/TIMESTAMP](https://dev.mysql.com/doc/refman/8.4/en/datetime.html), [utf8mb4](https://dev.mysql.com/doc/refman/8.4/en/charset-unicode-utf8mb4.html)
- [PostgreSQL wiki: Don't Do This](https://wiki.postgresql.org/wiki/Don%27t_Do_This): danh sách anti-pattern ngắn, đa số áp dụng được cho cả MySQL

**Nắm chắc khi**
- [ ] Chứng minh được `0.1 + 0.2 != 0.3` với float và nói hệ quả trong hệ thống tiền
- [ ] Giải thích được bug "lệch 7 tiếng" xảy ra ở đâu giữa PHP, MySQL session và cột dữ liệu
- [ ] Biết một bảng đã có dữ liệu thì đổi collation cần làm gì và rủi ro gì

---

### Chặng 2: Làm chủ 🟡

#### 2.1 InnoDB lưu dữ liệu thế nào

**Vì sao cần học:** Cách InnoDB lưu dữ liệu giải thích phần lớn các hành vi về hiệu năng: vì sao
chọn primary key quan trọng, vì sao covering index nhanh, vì sao UUIDv4 làm chậm insert.

**Học gì**

*Clustered index: bảng chính là một cây*
- Trong InnoDB, bảng **chính là** một B+tree sắp theo primary key (PK), và lá của cây chứa cả dòng
  dữ liệu đầy đủ. Cấu trúc này gọi là *clustered index*.
- Hệ quả: các dòng có PK gần nhau thì nằm gần nhau trên đĩa, nên đọc một khoảng PK rất rẻ.
- Nếu bảng không khai PK:
  - InnoDB dùng cột unique NOT NULL đầu tiên làm PK.
  - Không có cột nào như vậy thì InnoDB tự tạo một id ẩn 6 byte, và bạn không dùng được id này.

*Secondary index: tra hai lần*
- Mọi index khác (gọi là *secondary index*) lưu cặp **(giá trị cột, PK)**, không lưu con trỏ tới
  vị trí vật lý của dòng.
- Vì vậy `SELECT * FROM users WHERE email = ?` phải đi hai bước:
  1. Tìm `email` trong secondary index để lấy PK.
  2. Dùng PK đó tìm trong clustered index để lấy dòng đầy đủ.

  Bước 2 gọi là *lookup*, hay tra lại bảng.
- Hệ quả: PK càng lớn thì mọi secondary index càng lớn theo, vì entry nào cũng chứa PK.
- Nếu query chỉ cần những cột đã có trong index (kể cả PK) thì bỏ được bước 2. Trường hợp này gọi
  là *covering index* (module 2.2).
  - Ví dụ: có index `(email)` thì `SELECT id FROM users WHERE email = ?` là covering.

*Chọn primary key*

| | Auto-increment | UUIDv4 | UUIDv7 / ULID |
|---|---|---|---|
| Giá trị | Tăng dần | Ngẫu nhiên | Tăng dần theo thời gian |
| Insert vào cây | Luôn chèn ở cuối | Rải khắp cây | Gần cuối, như auto-increment |
| Kích thước | 8 byte (`BIGINT`) | 16 byte | 16 byte |
| Sinh ở app hoặc nhiều node | Không, cần DB cấp | Được | Được |
| Lộ thông tin | Lộ số lượng, đoán được id kế tiếp | Không | Lộ thời điểm tạo |

- UUIDv4 ngẫu nhiên nên mỗi lần insert rơi vào một chỗ bất kỳ trong cây:
  - Page ở chỗ đó thường đã đầy, phải tách đôi (*page split*).
  - Page đó có thể không còn trong RAM, phải đọc lại từ đĩa.
  - Lâu dần cây bị phân mảnh.
- Lưu UUID bằng `BINARY(16)`, không dùng `CHAR(36)`. `CHAR(36)` tốn 36 byte, và nhân lên ở mọi
  secondary index.
- Cách hay dùng: PK nội bộ là `BIGINT` auto-increment, thêm một cột `public_id` kiểu UUIDv7 hoặc
  ULID để đưa ra API. Cách này vừa không cho đoán id, vừa không lộ số lượng bản ghi.

*Cột lớn*
- Giá trị dài của cột `TEXT`, `BLOB`, `JSON` được đẩy ra các page riêng (*off-page*). Vì vậy
  `SELECT *` kéo cả những cột này về, tốn thêm I/O.

*Đối chiếu Postgres*
- Dữ liệu nằm trong một vùng gọi là *heap*, không sắp xếp theo gì cả. Mọi index, kể cả PK, trỏ
  tới vị trí vật lý của dòng (gọi là *ctid*).
- Mỗi lần update, Postgres ghi một bản dòng mới ở chỗ khác, nên phải sửa mọi index trỏ tới dòng
  đó. Ngoại lệ là *HOT update*: không cột nào có index bị đổi và page còn chỗ trống.

**Đọc**
- MySQL: [Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)
- Jeremy Cole: [B+Tree index structures in InnoDB](https://blog.jcole.us/2013/01/10/btree-index-structures-in-innodb/)
- [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562) (UUID): đọc phần 5.7 (UUIDv7) và phần 6
- Postgres: [Heap-Only Tuples](https://www.postgresql.org/docs/current/storage-hot.html)

**Nắm chắc khi**
- [ ] Vẽ được đường đi của `SELECT * FROM t WHERE email = ?` qua secondary index rồi clustered index
- [ ] Giải thích được vì sao `SELECT id FROM t WHERE a = ?` là covering chỉ với index `(a)`
- [ ] Tranh luận được chọn PK nào cho bảng orders sinh ra từ nhiều service

#### 2.2 Index nâng cao

**Vì sao cần học:** Ở mức mid trở lên, bạn được kỳ vọng tự thiết kế bộ index từ danh sách query,
và đoán trước được `EXPLAIN` sẽ ra gì.

**Học gì**

*Thứ tự cột trong composite index*
- Quy tắc: cột so sánh `=` đặt trước, cột so sánh khoảng (`>`, `<`, `BETWEEN`) hoặc cột dùng để
  sort đặt sau.
- Lý do: sau một cột so sánh khoảng, các cột phía sau không còn được sắp thứ tự trong phạm vi đang
  quét nữa, nên không dùng để thu hẹp phạm vi được.

  ```sql
  -- index (user_id, status, created_at)
  WHERE user_id = 1 AND status = 2 AND created_at > '2026-01-01'  -- dùng được cả 3 cột
  WHERE user_id = 1 AND created_at > '2026-01-01'                 -- chỉ thu hẹp theo user_id
  WHERE user_id = 1 AND status > 0 AND created_at > '...'         -- status là khoảng, created_at hết tác dụng
  ```

*Covering index và index condition pushdown*
- *Covering index*: mọi cột mà query cần đều có trong index, nên không phải tra lại bảng.
  `EXPLAIN` hiện `Extra: Using index`.
- *Index condition pushdown* (ICP) xảy ra khi điều kiện nằm trên một cột có trong index nhưng không
  dùng để tra được.
  - Ví dụ: index `(zip, last_name)` với điều kiện `last_name LIKE '%an%'`.
  - InnoDB lọc điều kiện đó ngay trên index trước khi tra lại bảng, nên số lần lookup giảm.
  - `EXPLAIN` hiện `Using index condition`.

*Index phục vụ ORDER BY*
- Index `(user_id, created_at)` phục vụ được `WHERE user_id = ? ORDER BY created_at DESC LIMIT 20`
  mà không cần sort: chỉ việc đi ngược 20 entry trong index.
- Khi phải sort, `EXPLAIN` hiện `Using filesort`. Cái tên dễ gây hiểu lầm: đây là sort, không nhất
  thiết phải ghi ra file.
- ⚠️ `WHERE user_id IN (1,2,3) ORDER BY created_at` vẫn phải sort, vì thứ tự `created_at` trong
  index chỉ đúng bên trong từng user.

*Index trên biểu thức và JSON*
- *Functional index* là index trên kết quả của một biểu thức, ví dụ
  `CREATE INDEX idx ON users ((LOWER(email)))`. Query phải viết đúng biểu thức đó
  (`WHERE LOWER(email) = ?`) thì mới dùng được.
- Với JSON:
  - Tạo một *generated column* lấy giá trị từ `data->>'$.sku'`, rồi index cột đó.
  - Với mảng JSON thì dùng *multi-valued index*.

*Cardinality và selectivity*
- *Cardinality* là số giá trị khác nhau của một cột.
- *Selectivity* là tỉ lệ dòng khớp điều kiện. Tỉ lệ càng nhỏ thì index càng có ích.
- Đi qua secondary index nghĩa là mỗi dòng khớp tốn một lần lookup ở vị trí ngẫu nhiên. Nếu khớp
  một phần lớn của bảng, optimizer chọn quét cả bảng tuần tự, và thường đó là quyết định đúng.
- ⚠️ Cột ít giá trị khác nhau vẫn đáng index nếu dữ liệu bị lệch.
  - Ví dụ: `status = 'pending'` chỉ chiếm 0,1% số dòng.
  - Với cột có index, optimizer đếm thử trên chính index (*index dive*) nên thường biết được sự lệch
    này. Với cột không có index, nó cần *histogram* (module 2.3).

*Công cụ nên biết*
- *Skip scan* (MySQL 8.0.13+, Postgres 18) cho phép dùng index `(a, b)` với điều kiện `WHERE b = ?`
  khi cột `a` có ít giá trị. Chỉ cần biết là có; đừng thiết kế dựa vào nó.
- *Invisible index*: ẩn index khỏi optimizer mà không xoá. Dùng để thử xem có query nào cần index
  đó không trước khi xoá thật.
- Tìm index thừa: `sys.schema_unused_indexes` (index không ai dùng) và
  `sys.schema_redundant_indexes` (index trùng tiền tố với index khác).

*Đối chiếu Postgres*
- *Partial index* chỉ index những dòng thoả một điều kiện, ví dụ `WHERE status = 'pending'`.
- `INCLUDE` thêm cột vào index chỉ để phục vụ covering.
- Các loại index khác: GIN (cho jsonb, mảng, full-text), GiST, BRIN.

**Đọc**
- Use The Index, Luke: các chương *The Where Clause*, *Sorting and Grouping*, *Partial Results*
- MySQL: [Index Condition Pushdown](https://dev.mysql.com/doc/refman/8.4/en/index-condition-pushdown-optimization.html), [ORDER BY Optimization](https://dev.mysql.com/doc/refman/8.4/en/order-by-optimization.html), [Range Optimization](https://dev.mysql.com/doc/refman/8.4/en/range-optimization.html) (có mục skip scan), [CREATE INDEX](https://dev.mysql.com/doc/refman/8.4/en/create-index.html) (functional key parts, multi-valued index), [Invisible Indexes](https://dev.mysql.com/doc/refman/8.4/en/invisible-indexes.html)
- Postgres: [Index Types](https://www.postgresql.org/docs/current/indexes-types.html), [Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html), [Index-Only Scans](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)

**Nắm chắc khi**
- [ ] Cho 4–5 query của một bảng, thiết kế được **bộ index tối thiểu** và giải thích thứ tự cột
- [ ] Nói trước được `EXPLAIN` sẽ ra `type` và `Extra` gì trước khi chạy
- [ ] Giải thích được khi nào optimizer chọn full scan thay vì index, và vì sao như vậy là đúng

#### 2.3 Đọc EXPLAIN và xử lý query chậm

**Vì sao cần học:** Câu "có query chậm trên production, bạn làm gì" gần như chắc chắn gặp.
`EXPLAIN` là công cụ trung tâm để trả lời câu đó.

**Học gì**

*Đọc EXPLAIN*
- `EXPLAIN` cho biết plan (kế hoạch chạy) mà optimizer định dùng, nhưng **không chạy** query.

| Cột | Nghĩa |
|---|---|
| `type` | Cách truy cập bảng. Từ tốt tới tệ: `const` (tra PK/unique, ra 1 dòng) > `eq_ref` (join theo unique) > `ref` (index không unique) > `range` > `index` > `ALL` (quét cả bảng) |
| `key` | Index thực sự được chọn. `possible_keys` là các index có thể dùng |
| `key_len` | Số byte của index được dùng, từ đó suy ra composite index được dùng tới mấy cột |
| `rows` | Số dòng optimizer **ước lượng** phải đọc |
| `filtered` | Phần trăm dòng ước lượng còn lại sau khi lọc |
| `Extra` | `Using index` (covering), `Using index condition` (ICP), `Using filesort` (phải sort), `Using temporary` (phải tạo bảng tạm, thường do `GROUP BY`/`DISTINCT`) |

- ⚠️ `type: index` nghĩa là **quét toàn bộ index**, không phải "đã dùng index tốt".

*EXPLAIN ANALYZE*
- `EXPLAIN ANALYZE` chạy query thật, rồi in thời gian và số dòng thật của từng bước.
- So số dòng ước lượng với số dòng thật. Lệch 10–100 lần nghĩa là optimizer đang đoán sai, và đó
  thường là gốc của một plan tệ.
- ⚠️ Vì nó chạy thật, với `UPDATE`/`DELETE` phải bọc trong transaction rồi `ROLLBACK`.

*Statistics*
- Optimizer chọn plan dựa trên thống kê về dữ liệu: số dòng, phân bố giá trị của từng cột.
- Sau một đợt import hoặc xoá lớn, thống kê bị cũ và plan có thể sai.
  - `ANALYZE TABLE` cập nhật thống kê.
  - Với cột có dữ liệu lệch, dùng histogram: `ANALYZE TABLE t UPDATE HISTOGRAM ON col`.
- ⚠️ Sự cố kinh điển: query đang 20ms bỗng thành 8 giây dù code không đổi, vì plan đã đổi.

*Thuật toán join*
- *Nested loop*: với mỗi dòng của bảng ngoài, tra bảng trong. Nhanh khi bảng trong có index trên
  cột join.
- *Hash join* (MySQL 8.0.18+): dựng một hash table từ bảng nhỏ hơn, rồi dò bằng bảng lớn. Dùng khi
  không có index phù hợp.
- MySQL không có *merge join*. Postgres có cả ba loại.

*Quy trình xử lý query chậm*
1. **Tìm query**: slow query log, `performance_schema`, APM.
2. **Xếp hạng theo tần suất × thời gian**. Một query 50ms chạy 10.000 lần mỗi phút nặng hơn nhiều
   so với một query 5 giây chạy mỗi giờ một lần. Dùng `pt-query-digest` để tổng hợp.
3. **`EXPLAIN ANALYZE`** để thấy bước nào tốn.
4. **Sửa**: thêm hoặc đổi index, viết lại query, bớt cột, chia nhỏ.
5. **Đo lại** và tiếp tục theo dõi.

Không phải lúc nào nguyên nhân cũng là query. Hãy kiểm tra cả lock wait, connection bị cạn, và
RAM không chứa đủ dữ liệu nóng.

*Pagination*
- `LIMIT 20 OFFSET 100000` vẫn phải đọc 100.020 dòng rồi bỏ đi 100.000 dòng đầu. Trang càng sâu
  càng chậm.
- *Keyset pagination* (còn gọi là cursor pagination) nhớ giá trị cuối của trang trước:
  `WHERE created_at < ? OR (created_at = ? AND id < ?) ORDER BY created_at DESC, id DESC LIMIT 20`
  - ⚠️ Postgres dùng index tốt với dạng gọn `(created_at, id) < (?, ?)`. MySQL có thể không dùng
    hết index với dạng này, nên với MySQL hãy viết dạng `OR` như trên và kiểm tra bằng `EXPLAIN`.
  - Nhanh đều ở mọi trang.
  - Cần cột `id` làm *tie-breaker* khi nhiều dòng trùng `created_at`.
  - Không nhảy thẳng tới trang N được.

*Mấy thứ hay bị hỏi*
- **`COUNT(*)` trên bảng lớn chậm**: InnoDB không lưu sẵn số dòng, vì mỗi transaction có thể thấy
  một số dòng khác nhau (MVCC). Thay bằng bảng counter riêng, số ước lượng, hoặc hiện
  "hơn 10.000" trên giao diện.
- **`SELECT *`**: kéo cả cột lớn, không tận dụng được covering index, và dễ vỡ code khi bảng thêm cột.
- **Update/delete hàng triệu dòng**: chia batch theo PK, mỗi lần 1.000–10.000 dòng, nghỉ giữa các
  batch. Một transaction khổng lồ làm replica bị trễ và làm undo log phình to.

**Đọc**
- MySQL: [EXPLAIN Output Format](https://dev.mysql.com/doc/refman/8.4/en/explain-output.html), [EXPLAIN ANALYZE](https://dev.mysql.com/doc/refman/8.4/en/explain.html), [Optimizer Statistics / Histogram](https://dev.mysql.com/doc/refman/8.4/en/optimizer-statistics.html), [Hash Joins](https://dev.mysql.com/doc/refman/8.4/en/hash-joins.html), [Slow Query Log](https://dev.mysql.com/doc/refman/8.4/en/slow-query-log.html)
- [pt-query-digest](https://docs.percona.com/percona-toolkit/pt-query-digest.html): tổng hợp slow log
- Use The Index, Luke: [We need tool support for keyset pagination](https://use-the-index-luke.com/no-offset) và [Paging Through Results](https://use-the-index-luke.com/sql/partial-results/fetch-next-page)
- Đối chiếu Postgres: [Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html), [pgMustard: đọc EXPLAIN](https://www.pgmustard.com/docs/explain), [explain.dalibo.com](https://explain.dalibo.com/) (vẽ plan thành hình)

**Nắm chắc khi**
- [ ] Đọc một plan thật và chỉ ra bước tốn nhất
- [ ] Postgres: biết `actual time` là số **của mỗi loop**
- [ ] Viết được keyset pagination có cột tie-breaker, và nói được điểm yếu của nó
- [ ] Kể được quy trình từ lúc có cảnh báo "DB chậm" tới lúc đóng sự cố, kể cả trường hợp nguyên nhân không nằm ở query

#### 2.4 SQL nâng cao

**Vì sao cần học:** Bài SQL live coding ở mức mid và senior hầu hết cần window function.

**Học gì**

*Window function*
- Window function tính một giá trị cho **mỗi dòng**, dựa trên một nhóm dòng liên quan (gọi là
  "cửa sổ"), nhưng **không gộp dòng** như `GROUP BY`.
- Cú pháp: `f() OVER (PARTITION BY ... ORDER BY ...)`. `PARTITION BY` chia các dòng thành nhóm,
  `ORDER BY` sắp thứ tự trong từng nhóm.
- Ba hàm xếp hạng khác nhau ở cách xử lý giá trị bằng nhau:
  - `ROW_NUMBER` đánh số liên tục: 1, 2, 3, 4.
  - `RANK` cho các giá trị bằng nhau cùng hạng và nhảy số sau đó: 1, 2, 2, 4.
  - `DENSE_RANK` cho cùng hạng nhưng không nhảy số: 1, 2, 2, 3.
- `LAG`/`LEAD` lấy giá trị của dòng trước hoặc dòng sau, ví dụ để so doanh thu với hôm qua.
- `SUM() OVER (ORDER BY ...)` cho ra tổng cộng dồn (*running total*).
- ⚠️ Khi có `ORDER BY` trong `OVER`, khung mặc định là `RANGE ... CURRENT ROW`. Với khung này, các
  dòng có cùng giá trị sort được cộng cùng một lúc, nên running total bị "nhảy bậc". Muốn cộng
  từng dòng thì ghi rõ `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`.
- Không lọc được theo kết quả window function trong `WHERE`, vì `WHERE` chạy trước. Phải bọc trong
  subquery hoặc CTE rồi lọc ở tầng ngoài:

  ```sql
  -- Top 3 đơn giá trị lớn nhất của mỗi user
  SELECT * FROM (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY total DESC) AS rn
    FROM orders o
  ) t WHERE rn <= 3;
  ```

*CTE*
- `WITH x AS (...)` đặt tên cho một subquery để câu SQL dễ đọc hơn.
- *Recursive CTE* gồm phần gốc, rồi `UNION ALL`, rồi phần tự gọi lại chính nó. Dùng để duyệt cây,
  ví dụ danh mục cha con hoặc toàn bộ cấp dưới qua nhiều tầng.
- ⚠️ Dữ liệu có vòng (A là cha của B, B là cha của A) thì truy vấn lặp vô hạn. Luôn giới hạn độ sâu.

*UPSERT*
- UPSERT là "có rồi thì cập nhật, chưa có thì thêm mới" trong **một câu lệnh atomic**.
- MySQL viết `INSERT ... ON DUPLICATE KEY UPDATE`. Từ 8.0.19 viết được `AS new` rồi dùng
  `new.qty`; từ 8.0.20 cách cũ `VALUES(qty)` bị deprecate.
- Vì sao không viết SELECT rồi INSERT: hai request cùng SELECT, cùng thấy chưa có, rồi cùng INSERT,
  dẫn tới trùng dữ liệu hoặc lỗi.
- ⚠️ Bảng có nhiều unique key thì không biết key nào đã kích hoạt nhánh update.
- ⚠️ Mỗi lần upsert vẫn tiêu một giá trị auto-increment, nên id bị "lỗ". Đây là chuyện bình
  thường, đừng viết code dựa vào việc id liên tục.

*Các bài kinh điển nên tự viết được*
- Top N mỗi nhóm
- Running total
- Tìm và xoá bản ghi trùng
- *Gaps and islands* (ví dụ chuỗi ngày đăng nhập liên tiếp)
- Giá trị lớn thứ N

**Đọc**
- MySQL: [Window Functions](https://dev.mysql.com/doc/refman/8.4/en/window-functions.html), [WITH (CTE)](https://dev.mysql.com/doc/refman/8.4/en/with.html), [INSERT ... ON DUPLICATE KEY UPDATE](https://dev.mysql.com/doc/refman/8.4/en/insert-on-duplicate.html)
- [modern-sql.com](https://modern-sql.com/): các bài về `OVER`, `WITH RECURSIVE`

**Nắm chắc khi**
- [ ] Viết không cần tra cứu: top 3 mỗi nhóm, running total, chuỗi ngày liên tiếp dài nhất
- [ ] Giải thích được `RANK` và `DENSE_RANK` khác nhau ở dữ liệu có giá trị bằng nhau

#### 2.5 Isolation level và anomaly

**Vì sao cần học:** Đây là phần sâu nhất và bị hỏi vặn nhiều nhất ở vòng senior. Hiểu sai phần
này dẫn thẳng tới bug về tiền và tồn kho.

**Học gì**

*Anomaly là gì*
- Khi nhiều transaction chạy cùng lúc, DB có thể cho ra kết quả mà nếu chạy lần lượt từng cái thì
  không bao giờ xảy ra. Những kết quả lạ đó gọi là *anomaly*.

| Anomaly | Chuyện gì xảy ra | Ví dụ |
|---|---|---|
| Dirty read | Đọc được dữ liệu transaction khác **chưa commit** | Thấy số dư đã trừ, rồi transaction kia rollback |
| Non-repeatable read | Đọc cùng một dòng hai lần, lần sau khác lần trước | Đọc giá, người khác sửa giá, đọc lại thấy giá mới |
| Phantom | Chạy lại cùng điều kiện, thấy thêm hoặc mất dòng | Đếm đơn hôm nay ra 10, đếm lại ra 11 |
| Read skew | Đọc hai dòng liên quan ở hai thời điểm khác nhau | Tổng hai tài khoản bị lệch vì đọc giữa lúc đang chuyển tiền |
| **Lost update** | Hai transaction cùng đọc, sửa, ghi; bản ghi sau đè mất bản trước | Hai người cùng mua món cuối cùng |
| **Write skew** | Hai transaction đọc cùng một tập dữ liệu, mỗi bên sửa một dòng **khác nhau**, gộp lại thì vi phạm ràng buộc | Hai bác sĩ cùng xin nghỉ vì đều thấy "vẫn còn người khác trực" |

*Isolation level*
- Isolation level là mức mà DB chặn các anomaly, đổi lại hiệu năng. Có bốn mức: Read Uncommitted,
  Read Committed (RC), Repeatable Read (RR), Serializable.
- **MySQL InnoDB mặc định là RR. Postgres mặc định là RC.**

| | MySQL RC | MySQL RR (mặc định) | PG RC (mặc định) | PG RR | PG Serializable |
|---|---|---|---|---|---|
| Dirty read | Không | Không | Không | Không | Không |
| Non-repeatable read / read skew | Có | Không | Có | Không | Không |
| Phantom | Có | Phần lớn chặn được | Có | Không | Không |
| Lost update (app đọc rồi ghi) | Có | **Có** | Có | Báo lỗi, phải retry | Báo lỗi |
| Write skew | Có | Có | Có | Có | Chặn |

- Hai ghi chú cho cột MySQL:
  - MySQL RR chặn non-repeatable read và read skew khi transaction **chỉ đọc**. Nếu trong transaction
    có câu ghi hoặc locking read, bạn có thể thấy dữ liệu mới (xem phần "hai kiểu đọc" ngay dưới).
  - MySQL Serializable (không có trong bảng) biến `SELECT` thường thành `SELECT ... FOR SHARE`, nên
    lost update và write skew bị chặn bằng lock, thường lộ ra thành deadlock (lỗi 1213) và phải retry.

*MySQL RR thật ra hoạt động thế nào*
- InnoDB dùng *MVCC*: giữ nhiều phiên bản của một dòng, và mỗi transaction đọc phiên bản đúng với
  thời điểm của nó (chi tiết ở module 3.1).
- Có hai kiểu đọc khác nhau:
  - **Consistent read** là `SELECT` thường. Ở RR, nó đọc theo một *snapshot* chụp ở lần đọc đầu
    tiên, nên đọc lại bao nhiêu lần vẫn thấy như cũ. Kiểu đọc này không lấy lock.
  - **Locking read** là `SELECT ... FOR UPDATE`/`FOR SHARE`, và cả `UPDATE`/`DELETE`. Nó đọc
    **bản mới nhất đã commit** và khoá dòng lại.
- ⚠️ Vì vậy RR của MySQL **không chặn lost update**. Ví dụ:
  1. Hai transaction cùng `SELECT` thường, cùng thấy `stock = 1` từ snapshot.
  2. App của mỗi bên tính ra 0.
  3. Cả hai cùng `UPDATE ... SET stock = 0`, và cả hai đều thành công.

  Postgres ở RR thì báo lỗi `40001` cho transaction thứ hai.
- ⚠️ Trộn hai kiểu đọc sẽ gặp "phantom" dù đang ở RR: một câu `UPDATE` chạm vào dòng người khác vừa
  insert, sau đó `SELECT` thường lại nhìn thấy dòng đó.

*Bốn cách chống lost update*
1. **Update atomic có điều kiện**: `UPDATE ... SET stock = stock - 1 WHERE id = ? AND stock > 0`,
   rồi kiểm tra số dòng bị ảnh hưởng có bằng 1 không. Đơn giản nhất, nên là lựa chọn đầu tiên.
2. **Pessimistic lock**: `SELECT ... FOR UPDATE` trong transaction, rồi mới tính toán và ghi.
3. **Optimistic lock**: dùng cột version (module 2.6).
4. **Isolation level cao hơn kèm retry** (Postgres RR hoặc Serializable).

*Write skew*
- Hai transaction không sửa cùng một dòng, nên các cơ chế chống lost update ở trên không bắt được.
  RR không chặn được write skew.
- Có ba cách chống:
  - Khoá cả tập dữ liệu đã đọc (`FOR UPDATE` trên tập đó).
  - Đưa ràng buộc xuống DB (unique, trigger).
  - Dùng Serializable.

*Đối chiếu Postgres (🔴)*
- RR của Postgres là *snapshot isolation*: một snapshot dùng cho cả transaction.
- Serializable của Postgres là *SSI*: DB theo dõi các phụ thuộc đọc-ghi giữa các transaction, thấy
  nguy cơ thì huỷ một transaction. Vì vậy app **bắt buộc** phải retry khi gặp lỗi `40001`.

**Đọc**
- DDIA ch.7: *Weak Isolation Levels* và *Serializability*. Phần quan trọng nhất của cả file này
- MySQL: [Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html), [Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)
- Postgres: [Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Hermitage](https://github.com/ept/hermitage): bảng thực nghiệm anomaly nào xảy ra ở DB nào, level nào, kèm script tái hiện
- 🔴 [A Critique of ANSI SQL Isolation Levels](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/) (Berenson và cộng sự, 1995): bài gốc định nghĩa lại các anomaly
- 🔴 [Serializable Snapshot Isolation in PostgreSQL](https://arxiv.org/abs/1208.4179) (Ports, Grittner)
- 🔴 [Jepsen: Consistency Models](https://jepsen.io/consistency): bản đồ các mô hình consistency

**Nắm chắc khi**
- [ ] Tái hiện được bằng hai terminal `mysql`: non-repeatable read ở RC và lost update ở RR (bài tập 3)
- [ ] Cho bài "hai bác sĩ cùng xin nghỉ trực", giải thích được vì sao RR không chặn và nêu được 3 cách sửa
- [ ] Nói được vì sao chạy Postgres ở RR hoặc Serializable mà code không retry là có bug

#### 2.6 Lock thực dụng

**Vì sao cần học:** Chọn đúng loại lock là khác biệt giữa một hệ thống chỉ đúng và một hệ thống
vừa đúng vừa nhanh.

**Học gì**

*Shared lock và exclusive lock*
- **Shared lock** (S), lấy bằng `FOR SHARE`: nhiều transaction cùng đọc được, nhưng không ai sửa được.
- **Exclusive lock** (X), lấy bằng `FOR UPDATE`, `UPDATE` hoặc `DELETE`: chỉ một transaction giữ.
  Transaction khác muốn lấy S hay X trên dòng đó đều phải chờ.
- `SELECT` thường không lấy lock nào, vì nó đọc từ snapshot.

*Optimistic lock và pessimistic lock*
- **Pessimistic**: khoá trước, làm sau (`FOR UPDATE`). Hợp khi tranh chấp nhiều và thao tác ngắn,
  ví dụ trừ tồn kho hay trừ số dư.
- **Optimistic**: không khoá gì cả, chỉ ghi kèm điều kiện về version:

  ```sql
  UPDATE posts SET body = ?, version = version + 1 WHERE id = ? AND version = ?;
  -- 0 dòng bị ảnh hưởng: đã có người sửa trước, báo xung đột hoặc thử lại
  ```

  Hợp khi ít tranh chấp và thao tác kéo dài, có người dùng suy nghĩ ở giữa, ví dụ sửa bài viết.
- Trong Laravel: `lockForUpdate()` và `sharedLock()`. Optimistic lock thì tự viết điều kiện
  `where('version', ...)`.

*Deadlock*
- Deadlock là khi hai transaction, mỗi bên giữ một lock mà bên kia đang cần, nên chờ nhau mãi.
  - Ví dụ: T1 khoá sản phẩm A rồi xin khoá B, trong khi T2 khoá B rồi xin khoá A.
- InnoDB phát hiện deadlock ngay lập tức và rollback một bên (lỗi 1213).
- Cách phòng:
  - Khoá theo thứ tự cố định, ví dụ sort các id trước khi khoá.
  - Giữ transaction ngắn.
  - Có index đúng để khoá ít dòng nhất có thể.
- ⚠️ Không thể loại bỏ hoàn toàn deadlock, nên app **luôn phải có retry**.

*Hai bẫy hay gặp*
- ⚠️ `UPDATE` hoặc `FOR UPDATE` có `WHERE` trên cột **không có index**: InnoDB khoá mọi dòng nó quét
  qua, gần như là khoá cả bảng.
- ⚠️ **Lock wait timeout** (`innodb_lock_wait_timeout`, mặc định 50 giây, lỗi 1205): MySQL chỉ
  rollback **câu lệnh** bị timeout, **không** rollback cả transaction. Code bắt lỗi rồi `COMMIT`
  tiếp là commit một nửa công việc.

*Job queue bằng DB*
- `FOR UPDATE SKIP LOCKED` bỏ qua những dòng đang bị khoá thay vì chờ, nên nhiều worker cùng lấy job
  mà không tranh nhau. `NOWAIT` thì báo lỗi ngay nếu dòng đang bị khoá.
- Cần thêm:
  - Index `(status, run_at)`.
  - Cơ chế trả những job bị treo quá lâu về trạng thái pending, cho trường hợp worker chết giữa chừng.
  - Giới hạn số lần thử.
  - Xử lý idempotent, vì một job có thể bị chạy lại.

*Advisory lock*
- `GET_LOCK('name', timeout)` khoá theo một cái tên tuỳ ý, không gắn với dòng nào.
- Dùng để đảm bảo chỉ một instance chạy một cron job. So sánh với lock bằng Redis ở
  [14-distributed-systems.md](14-distributed-systems.md).

**Đọc**
- MySQL: [Locking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html) (có mục `NOWAIT`/`SKIP LOCKED`), [Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html) và [How to Minimize and Handle Deadlocks](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks-handling.html)
- [Brandur: Postgres Job Queues & Failure By MVCC](https://brandur.org/postgres-queues): vì sao job queue bằng DB có thể tự làm mình chậm dần
- Laravel: [Pessimistic Locking](https://laravel.com/docs/queries#pessimistic-locking)

**Nắm chắc khi**
- [ ] Viết được luồng trừ tồn kho theo 3 cách và nói khi nào dùng cách nào
- [ ] Thiết kế được job queue bằng `SKIP LOCKED`: worker chết giữa chừng, retry, idempotent
- [ ] Giải thích được vì sao bắt lỗi 1205 xong rồi `COMMIT` tiếp là commit một nửa

#### 2.7 Tầng PHP: PDO và Laravel

**Vì sao cần học:** Người phỏng vấn dev PHP rất hay hỏi xoáy vào chỗ giao nhau giữa framework và
DB, vì đây là nơi lộ ra bạn chỉ dùng Laravel hay hiểu Laravel làm gì bên dưới.

**Học gì**

*PDO*
- PDO là lớp truy cập DB chuẩn của PHP. Laravel dùng PDO ở bên dưới.
- *Prepared statement*: gửi câu SQL có chỗ trống (`?`) và gửi giá trị riêng. Nhờ vậy giá trị không
  bao giờ bị hiểu là SQL, và đây là cách chống SQL injection.
- ⚠️ `PDO_MYSQL` dùng trực tiếp thì mặc định là **emulate prepare**: PHP tự escape giá trị, ghép vào
  chuỗi SQL rồi gửi một lần, không dùng prepared statement thật của MySQL.
  - Cách này vẫn an toàn nếu charset của kết nối đúng (khai `charset=utf8mb4` trong DSN).
  - Lỗi cú pháp chỉ bị phát hiện lúc execute. Trước PHP 8.1, số nguyên và số thực còn bị trả về dạng
    chuỗi; từ 8.1 đã trả đúng kiểu.
  - Tắt bằng `PDO::ATTR_EMULATE_PREPARES => false` nếu muốn dùng prepare thật.
  - Laravel đã đặt sẵn `ATTR_EMULATE_PREPARES => false` trong connector, nên app Laravel mặc định
    dùng prepare thật.
- `ERRMODE_EXCEPTION`: lỗi SQL ném exception thay vì trả về `false`. Đây là mặc định từ PHP 8.
- *Buffered query* (mặc định): toàn bộ kết quả được kéo về RAM của PHP rồi mới duyệt. Một query ra
  1 triệu dòng có thể vượt `memory_limit`. Muốn duyệt từng dòng thì dùng unbuffered query hoặc cursor.
- ⚠️ Cột `DECIMAL` được trả về dạng chuỗi, ví dụ `"1234.50"`. Như vậy là đúng, để không mất độ chính
  xác. Đừng ép sang `(float)`; hãy dùng bcmath hoặc thư viện `brick/money`.

*Connection*
- Java và Go có *connection pool* trong process: vài chục connection được dùng chung cho hàng nghìn
  request. PHP-FPM thì không có: mỗi worker tự mở connection riêng cho request nó đang xử lý.
- Tổng connection tối đa ≈ số server × `pm.max_children` + số queue worker + cron.
  - Ví dụ: 4 server × 50 + 10 worker = 210 connection.
  - Con số này phải nhỏ hơn `max_connections` của MySQL (mặc định 151).
- ⚠️ Autoscale thêm server là thêm connection, nên có thể đánh sập DB trước khi app kịp chậm.
- *Persistent connection* (`PDO::ATTR_PERSISTENT`): worker giữ connection qua nhiều request để đỡ
  phải mở lại. Rủi ro là trạng thái của request trước (biến session, transaction chưa đóng, lock)
  rò sang request sau.
- Với Octane, Swoole hay RoadRunner, app sống lâu qua nhiều request, nên gặp đúng vấn đề trên.
  Thêm vào đó, MySQL có thể đóng connection đang rảnh (`wait_timeout`) mà app không biết.
- ⚠️ MySQL 8.4 tắt `mysql_native_password` mặc định. PHP từ 7.4.4 đã hỗ trợ
  `caching_sha2_password`.

*Eloquent và N+1*
- Ví dụ N+1:

  ```php
  $posts = Post::all();                    // 1 query
  foreach ($posts as $post) {
      echo $post->author->name;            // thêm 1 query cho mỗi post: N query
  }
  ```

  Từng query đều nhanh nên không lên slow log, nhưng tổng lại thì chậm.
- Cách sửa:
  - `Post::with('author')->get()` chỉ chạy 2 query: một lấy post, một lấy author với
    `WHERE id IN (...)`.
  - `load()` khi đã có sẵn collection.
  - `withCount('comments')` khi chỉ cần đếm.
- Bắt lỗi ngay ở môi trường dev:
  - `Model::preventLazyLoading()` ném exception mỗi khi có lazy load.
  - `Model::shouldBeStrict()` bật thêm vài kiểm tra khác.
- `Model::automaticallyEagerLoadRelationships()` (có từ Laravel 12) tự eager load khi phát hiện.
  Tiện, nhưng vẫn phải hiểu nó load những gì.

*Transaction trong Laravel*
- `DB::transaction(fn, attempts)` tự commit hoặc rollback. Nếu `attempts > 1`, closure được chạy lại
  khi gặp lỗi do tranh chấp: deadlock, lock wait timeout, lỗi serialization (SQLSTATE `40001`). Mặc
  định `attempts` là 1, tức không retry. Retry chỉ xảy ra ở transaction ngoài cùng.
  - ⚠️ Vì vậy closure phải chạy lại được một cách an toàn. Đừng gửi email bên trong nó.
- ⚠️ Câu DDL (`CREATE`, `ALTER`) trong MySQL tự commit transaction đang mở (gọi là *implicit
  commit*). Hệ quả: migration nhiều bước lỗi giữa chừng thì không rollback được, và schema bị dở dang.
- ⚠️ **Dispatch job bên trong transaction**:
  - Job vào queue ngay, nên worker có thể chạy nó trước khi transaction commit. Worker khi đó không
    thấy đơn hàng, hoặc xử lý một đơn mà sau đó bị rollback.
  - Sửa bằng `->afterCommit()` hoặc bật `after_commit` cho queue connection.
  - Muốn đảm bảo tuyệt đối thì dùng outbox pattern ([12-messaging.md](12-messaging.md)).

*Đọc tập dữ liệu lớn*

| Cách | Hoạt động | Khi nào dùng |
|---|---|---|
| `get()` | Kéo toàn bộ vào RAM | Tập nhỏ |
| `chunk(1000, fn)` | Nhiều query với `LIMIT`/`OFFSET` | Tránh dùng khi callback sửa dữ liệu |
| `chunkById(1000, fn)` | Nhiều query với `WHERE id > last_id` | Mặc định nên dùng cách này |
| `lazyById()` | Như `chunkById` nhưng trả về lazy collection | Muốn viết kiểu pipeline |
| `cursor()` | Một query, duyệt từng dòng | Chỉ đọc, tiết kiệm RAM nhất |

- ⚠️ `chunk()` mà trong callback lại sửa chính cột đang lọc (lọc `status = 'pending'` rồi set thành
  `'done'`): tập kết quả co lại trong khi `OFFSET` vẫn tăng, nên bỏ sót khoảng một nửa số dòng.
  Dùng `chunkById()`.

*Read/write connection*
- Cấu hình `read`/`write` trong Laravel: câu `SELECT` đi tới replica, câu ghi đi tới primary.
- `sticky => true`: nếu request đã ghi thì các lần đọc sau trong cùng request đi tới primary. Cách này
  giải bài toán *read-your-writes* trong phạm vi một request.

*ORM sinh SQL tệ*
- `->get()->count()` kéo hết dữ liệu về rồi mới đếm trong PHP. Dùng `->count()`.
- `save()` trong vòng lặp tạo N câu `UPDATE`. Dùng update hàng loạt hoặc `upsert()`.
- `whereHas` sinh subquery `WHERE EXISTS`, có thể chậm trên bảng lớn.
- Raw SQL hợp với báo cáo, window function, thao tác hàng loạt. Raw SQL vẫn phải bind tham số.

*Quan sát*
- `DB::listen` để log mọi query.
- Telescope hoặc Debugbar để đếm số query của mỗi request.
- `DB::whenQueryingForLongerThan` để cảnh báo khi tổng thời gian query của một request vượt ngưỡng.

**Đọc**
- PHP: [PDO](https://www.php.net/manual/en/book.pdo.php), [PDO_MYSQL](https://www.php.net/manual/en/ref.pdo-mysql.php) (ghi chú emulate prepare, buffered query), [PDO::setAttribute](https://www.php.net/manual/en/pdo.setattribute.php), [Persistent Connections](https://www.php.net/manual/en/features.persistent-connections.php), [Buffered and Unbuffered queries](https://www.php.net/manual/en/mysqlinfo.concepts.buffering.php)
- Laravel:
  - [Read & Write Connections / sticky](https://laravel.com/docs/database#read-and-write-connections)
  - [Handling Deadlocks](https://laravel.com/docs/database#handling-deadlocks)
  - [Implicit Commits](https://laravel.com/docs/database#implicit-commits-in-transactions)
  - [Monitoring Cumulative Query Time](https://laravel.com/docs/database#monitoring-cumulative-query-time)
  - [Chunking](https://laravel.com/docs/queries#chunking-results)
  - [Eager Loading](https://laravel.com/docs/eloquent-relationships#eager-loading)
  - [Preventing Lazy Loading](https://laravel.com/docs/eloquent-relationships#preventing-lazy-loading)
  - [Automatic Eager Loading](https://laravel.com/docs/eloquent-relationships#automatic-eager-loading)
  - [Eloquent Strictness](https://laravel.com/docs/eloquent#configuring-eloquent-strictness)
  - [Jobs & Database Transactions](https://laravel.com/docs/queues#jobs-and-database-transactions)
- Chi tiết về runtime PHP-FPM: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Tính được số connection tối đa của hệ thống mình đang làm và so với `max_connections`
- [ ] Giải thích được emulate prepare an toàn với injection ở chỗ nào, và vì sao vẫn nên tắt
- [ ] Chỉ ra được 3 chỗ trong code Laravel thật có thể gây N+1 hoặc load quá nhiều vào RAM
- [ ] Giải thích được bug "job gửi email chạy trước khi đơn hàng được commit" và cách sửa

#### 2.8 Thiết kế schema nâng cao

**Vì sao cần học:** Thiết kế schema là bài hay gặp ở vòng system design và vòng thảo luận dự án.
Các lựa chọn ở đây rất khó đổi lại về sau.

**Học gì**

*Denormalize có kiểm soát*
- *Denormalize* là lưu thêm dữ liệu dẫn xuất để đọc nhanh hơn, ví dụ `posts.comments_count` thay vì
  `COUNT` mỗi lần hiển thị.
- Cái giá: phải giữ nó đồng bộ (cập nhật trong cùng transaction, qua event, hoặc có job đối soát),
  và chấp nhận có lúc bị lệch.
- ⚠️ `order_items.price` (giá tại thời điểm mua) **không phải** bản sao thừa của `products.price`.
  Đó là dữ liệu lịch sử và bắt buộc phải lưu.

*Soft delete và unique*
- *Soft delete* nghĩa là không xoá dòng, chỉ đặt giá trị cho `deleted_at`.
  - Lợi: khôi phục được, giữ được lịch sử.
  - Giá: mọi query phải nhớ lọc. `SoftDeletes` của Laravel tự thêm điều kiện, nhưng raw query và
    join thì dễ quên. Bảng cũng phình to dần.
- ⚠️ `UNIQUE(email, deleted_at)` **không** chặn được hai user chưa xoá có cùng email. Hai dòng đó đều
  có `deleted_at` là NULL, mà unique index coi các NULL là khác nhau.
  - MySQL: tạo generated column `email_active = IF(deleted_at IS NULL, email, NULL)` rồi đặt
    unique trên cột đó.
  - Postgres: partial unique index `WHERE deleted_at IS NULL`.

*Khoá ngoại*
- Khoá ngoại (FK) bắt DB từ chối dữ liệu mồ côi, ví dụ đơn hàng của một user không tồn tại, kể cả
  khi app có bug.
- Cái giá:
  - Mỗi lần ghi đều phải kiểm tra.
  - Phải khoá thêm dòng ở bảng cha, có thể gây deadlock.
  - Không dùng được giữa các DB, các shard hay các service khác nhau.
- Thực tế: monolith dùng một DB thì nên dùng FK. Hệ sharded hoặc microservice thì kiểm tra ở tầng
  app, kèm job đối soát.

*Dữ liệu dạng cây*

| Cách | Lưu thế nào | Đọc cả cây con | Di chuyển một node | Khi nào dùng |
|---|---|---|---|---|
| Adjacency list | Cột `parent_id` | Recursive CTE | Rẻ, sửa 1 dòng | Mặc định, đủ cho hầu hết trường hợp |
| Materialized path | Cột `path = '/1/5/12/'` | `LIKE '/1/5/%'`, dùng được index | Phải sửa path của cả cây con | Đọc nhiều, ít di chuyển |
| Nested set | Hai cột `lft`, `rgt` | Một range query | Rất đắt, phải đánh số lại | Cây gần như không đổi |
| Closure table | Bảng riêng lưu mọi cặp (tổ tiên, con cháu) | Join đơn giản | Trung bình | Cần linh hoạt, chấp nhận tốn dòng |

*JSON và EAV*
- Cột JSON hợp lý khi:
  - Thuộc tính thay đổi theo từng loại sản phẩm.
  - Payload cần lưu nguyên để tra cứu về sau.
  - Dữ liệu cấu hình.
- Dấu hiệu dùng JSON vì lười thiết kế: thường xuyên lọc, join hoặc sort theo một field trong JSON,
  hoặc có ràng buộc cần DB giữ.
- ⚠️ *EAV* (entity–attribute–value) là bảng `(entity_id, attribute, value)` dùng cho "thuộc tính
  tuỳ ý". Nó có nhiều nhược điểm:
  - Mất kiểu dữ liệu, vì mọi giá trị đều là chuỗi.
  - Không đặt được ràng buộc.
  - Lấy một object cần nhiều join, nên query rất chậm.

  Magento là ví dụ nổi tiếng về cái giá của EAV. Thay bằng cột JSON, hoặc mỗi loại một bảng riêng.

*Polymorphic association*
- `comments(commentable_type, commentable_id)`, kiểu `morphTo` của Laravel, dùng một cột id để trỏ
  tới nhiều bảng khác nhau tuỳ theo type. Vì vậy không đặt được khoá ngoại, và dễ có dữ liệu mồ côi.
- Hai cách thay thế:
  - Mỗi loại một cột FK nullable, kèm `CHECK` đảm bảo đúng một cột có giá trị.
  - Mỗi loại một bảng nối riêng.

*Audit và history*
- Ghi lại ai đổi gì, lúc nào, bằng một trong ba cách:
  - Từ app: biết được user nào và lý do.
  - Bằng trigger: không bao giờ sót, nhưng không biết user nào.
  - Bằng CDC (Debezium đọc binlog): không sót và không đụng vào code app.
- Dữ liệu cần tra "tại thời điểm X", như giá hay hợp đồng, thì lưu kèm `valid_from`/`valid_to`.
- ⚠️ Bảng audit lớn rất nhanh. Nên partition theo thời gian ngay từ đầu.

*Enum*
- `ENUM` của MySQL gọn, nhưng đổi danh sách giá trị phải `ALTER TABLE`, và sort theo thứ tự khai báo
  chứ không theo chữ cái. Thêm giá trị vào **cuối** danh sách thường làm được tức thì; xoá hay đổi
  thứ tự thì phải dựng lại bảng.
- Cách thay thế: `VARCHAR` kèm `CHECK`, hoặc bảng lookup kèm FK. Ở tầng app thì dùng enum của PHP 8.1
  với cast của Eloquent.

**Đọc**
- *High Performance MySQL*: chương *Schema Design and Management*
- MySQL: [JSON Data Type](https://dev.mysql.com/doc/refman/8.4/en/json.html)
- *SQL Antipatterns* (Bill Karwin): EAV, polymorphic association, naive tree. Đọc các chương về những chủ đề này
- Laravel: [Polymorphic Relationships](https://laravel.com/docs/eloquent-relationships#polymorphic-relationships)

**Nắm chắc khi**
- [ ] Thiết kế được schema đơn hàng (orders, items, payments, lịch sử trạng thái) và bảo vệ được từng quyết định
- [ ] Nêu được 2 cách thay thế polymorphic association có khoá ngoại

---

### Chặng 3: Senior 🔴

#### 3.1 Bên trong InnoDB: log, bộ nhớ, MVCC

**Vì sao cần học:** Senior hay bị hỏi "commit xong thì dữ liệu an toàn nhờ đâu" và "vì sao một
transaction mở lâu làm cả DB chậm". Muốn trả lời phải hiểu bên trong InnoDB.

**Học gì**

*Buffer pool*
- InnoDB không đọc hay ghi đĩa trực tiếp cho mỗi query. Nó giữ các page trong một vùng RAM lớn gọi
  là *buffer pool* (`innodb_buffer_pool_size`), docs khuyên đặt tới khoảng 80% RAM của một máy chỉ chạy DB.
- Sửa dữ liệu nghĩa là sửa page trong RAM. Page đó trở thành *dirty page*, và được ghi xuống đĩa dần
  ở chế độ nền.
- Dữ liệu hay dùng (*working set*) mà vừa buffer pool thì nhanh. Vượt quá thì phải đọc đĩa liên tục,
  và hiệu năng rơi mạnh. Theo dõi chỉ số *hit ratio*.

*Ba loại log*

| Log | Thuộc tầng | Ghi gì | Dùng để làm gì |
|---|---|---|---|
| Redo log | InnoDB | Page nào đã đổi ra sao (vật lý) | Khôi phục sau crash |
| Undo log | InnoDB | Bản cũ của dòng trước khi sửa | Rollback, và cho transaction khác đọc bản cũ (MVCC) |
| Binlog | MySQL server | Thay đổi dạng logic (dòng hoặc câu lệnh) | Replication, khôi phục tới một thời điểm (PITR) |

- **Redo log** là một dạng *write-ahead log* (WAL), nghĩa là "ghi log trước, ghi dữ liệu sau":
  - Trước khi báo commit thành công, InnoDB ghi thay đổi vào redo log và `fsync`.
  - Ghi log là ghi tuần tự, nhanh hơn nhiều so với ghi các page nằm rải rác.
  - Khi crash, InnoDB replay redo log để khôi phục các thay đổi đã commit mà page chưa kịp ghi xuống đĩa.

*Two-phase commit nội bộ*
- Redo log và binlog là hai log riêng. Nếu crash giữa lúc ghi hai cái, primary (khôi phục theo redo)
  và replica (áp theo binlog) sẽ lệch nhau.
- MySQL dùng *two-phase commit* nội bộ để tránh chuyện này:
  1. Ghi `prepare` vào redo log.
  2. Ghi binlog.
  3. Ghi `commit` vào redo log.

  Khi khôi phục, transaction nào đã có trong binlog thì được commit, chưa có thì bị rollback.

*Đánh đổi giữa độ bền và throughput*
- `innodb_flush_log_at_trx_commit = 1` (fsync redo mỗi lần commit) cùng với `sync_binlog = 1`
  (fsync binlog mỗi lần commit) là an toàn nhất.
- Hạ các giá trị này xuống để tăng throughput nghĩa là chấp nhận mất khoảng 1 giây giao dịch cuối
  cùng khi máy sập.

*Doublewrite buffer*
- Page của InnoDB là 16 KB, nhưng đĩa chỉ đảm bảo ghi nguyên vẹn các đơn vị nhỏ hơn (thường 4 KB).
- Mất điện giữa lúc ghi thì page bị nửa mới nửa cũ (*torn page*). Redo log không sửa được trường
  hợp này, vì redo cần page gốc còn nguyên vẹn.
- Vì vậy InnoDB ghi page vào vùng *doublewrite* trước, rồi mới ghi vào vị trí thật.

*MVCC*
- Mỗi dòng có thể có nhiều phiên bản, và mỗi transaction đọc phiên bản đúng với snapshot của nó. Nhờ
  vậy đọc không chặn ghi, và ghi không chặn đọc.
- InnoDB giữ bản mới nhất trong bảng. Các bản cũ được nối thành một chuỗi trong undo log.
  *Purge thread* dọn undo log khi không còn transaction nào cần các bản cũ đó.
- ⚠️ Một transaction mở lâu (kể cả chỉ `SELECT`, kể cả đang rảnh vì ai đó quên commit) giữ một
  snapshot cũ. Khi đó purge không dọn được, nên:
  - Undo log phình to.
  - Chuỗi phiên bản dài ra.
  - Mọi query đọc chậm dần.

  Chỉ số cần xem là *history list length* trong `SHOW ENGINE INNODB STATUS`.

*Binlog format*
- `ROW` (mặc định) ghi các dòng đã thay đổi. `STATEMENT` ghi câu SQL. `MIXED` kết hợp cả hai.
- ⚠️ `STATEMENT` không an toàn với câu lệnh không tất định như `UUID()`, `SYSDATE()`, `RAND()`, hay
  `LIMIT` không có `ORDER BY`: replica chạy lại có thể ra kết quả khác. `NOW()` thì an toàn, vì binlog
  ghi kèm timestamp của câu lệnh.

*Đối chiếu Postgres*
- Postgres không có undo log. Bản cũ của dòng nằm ngay trong bảng, và `VACUUM` là thứ dọn chúng.
  Vacuum không kịp thì bảng phình (*bloat*).
- Transaction ID của Postgres chỉ có 32 bit. Nếu không vacuum kịp để "freeze" các dòng cũ thì gặp
  *wraparound*, và Postgres buộc phải dừng ghi.

*LSM tree*
- Đây là một kiểu storage engine khác, dùng trong RocksDB/MyRocks và Cassandra:
  - Ghi vào RAM trước, đầy thì flush ra file bất biến đã được sắp xếp.
  - Ở chế độ nền, engine gộp các file lại (*compaction*).
- So với B+tree: ghi rất nhanh vì ghi tuần tự, nhưng đọc có thể phải xem nhiều file, và compaction
  khiến dữ liệu bị ghi lại nhiều lần. Hợp với workload ghi dày như log hay metric.

**Đọc**
- MySQL:
  - [InnoDB Architecture](https://dev.mysql.com/doc/refman/8.4/en/innodb-architecture.html) (xem hình trước)
  - [Buffer Pool](https://dev.mysql.com/doc/refman/8.4/en/innodb-buffer-pool.html)
  - [Redo Log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)
  - [Undo Logs](https://dev.mysql.com/doc/refman/8.4/en/innodb-undo-logs.html)
  - [Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html)
  - [Doublewrite Buffer](https://dev.mysql.com/doc/refman/8.4/en/innodb-doublewrite-buffer.html)
  - [Binary Log](https://dev.mysql.com/doc/refman/8.4/en/binary-log.html)
  - [Replication Formats](https://dev.mysql.com/doc/refman/8.4/en/replication-formats.html)
- Postgres: [WAL](https://www.postgresql.org/docs/current/wal-intro.html), [MVCC](https://www.postgresql.org/docs/current/mvcc-intro.html), [Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html) (có mục wraparound)
- DDIA ch.3 (B-tree so với LSM)
- CMU 15-445: các bài về logging & recovery và multi-version concurrency control

**Nắm chắc khi**
- [ ] Kể được từ lúc `COMMIT` tới lúc dữ liệu an toàn: ghi gì, fsync gì, theo thứ tự nào
- [ ] Giải thích được vì sao một transaction chỉ đọc quên đóng lại làm cả DB chậm dần, ở cả MySQL và Postgres
- [ ] So sánh được MVCC của InnoDB và Postgres, nói được hệ quả vận hành của mỗi bên

#### 3.2 Lock chuyên sâu

**Vì sao cần học:** Deadlock và sự cố metadata lock là hai sự cố DB hay gặp nhất khi hệ thống lớn
lên. Senior phải đọc được log và giải thích được từng bước.

**Học gì**

*InnoDB khoá cái gì*
- InnoDB không khoá "dòng" mà khoá **entry trong index**. Vì vậy một câu lệnh khoá bao nhiêu phụ
  thuộc vào index mà nó dùng.
- Các loại lock:
  - **Record lock**: khoá một entry.
  - **Gap lock**: khoá khoảng trống giữa hai entry để không ai insert vào đó.
  - **Next-key lock**: record lock cộng với gap lock ngay trước nó. RR dùng loại này để chặn phantom
    khi đọc có khoá.
- Ví dụ: index trên cột `age` đang có các giá trị 20 và 30. Ở RR,
  `SELECT ... WHERE age BETWEEN 20 AND 30 FOR UPDATE` khoá cả entry 20, entry 30 và các khoảng ở
  giữa. Không ai insert được `age = 25`.
- **Insert intention lock** là một loại gap lock đặc biệt lấy khi insert. Hai lệnh insert vào cùng
  một khoảng ở hai vị trí khác nhau thì không chặn nhau.
- **Intention lock** (IS, IX) là lock ở mức bảng, báo hiệu "trong bảng này đang có transaction khoá
  dòng". Nhờ đó, ai muốn khoá cả bảng không phải duyệt qua từng dòng.
- Ở RC, InnoDB gần như tắt gap lock, nên ít deadlock hơn nhưng chấp nhận phantom. Nhiều hệ thống
  chuyển sang RC vì lý do này.

*Deadlock kinh điển do gap lock*
- Hay gặp ở code kiểu "kiểm tra chưa có thì tạo mới":
  1. T1 và T2 cùng chạy `SELECT ... WHERE id = 100 FOR UPDATE`, trong khi `id = 100` chưa tồn tại.
  2. Cả hai đều lấy được gap lock, vì gap lock không xung đột với nhau.
  3. Cả hai cùng `INSERT id = 100`, và mỗi bên phải chờ gap lock của bên kia.
  4. Deadlock.

*AUTO-INC lock*
- `innodb_autoinc_lock_mode` từ 8.0 mặc định là 2 (interleaved): id được cấp nhanh nhưng không liên
  tục, và binlog nên dùng format `ROW` hoặc `MIXED`: với `STATEMENT`, id cấp cho insert hàng loạt có thể khác nhau giữa primary và replica.

*Đọc deadlock log*
- Mở `SHOW ENGINE INNODB STATUS` và tìm mục `LATEST DETECTED DEADLOCK`. Với mỗi transaction, xem:
  - Câu SQL đang chạy.
  - `HOLDS THE LOCK(S)`: đang giữ lock nào.
  - `WAITING FOR THIS LOCK`: đang chờ lock nào.
  - Index nào, và loại lock: `locks gap before rec` là gap lock, `rec but not gap` là record lock.
- Bật `innodb_print_all_deadlocks` để ghi mọi deadlock vào error log. Xem các lock đang được giữ qua
  `performance_schema.data_locks`.
- ⚠️ Log chỉ in câu lệnh **đang chạy** của mỗi transaction. Lock có thể đã được lấy bởi một câu
  trước đó trong cùng transaction.

*Metadata lock (MDL)*
- Mọi query trên một bảng giữ một metadata lock dạng shared tới hết transaction, để cấu trúc bảng
  không bị đổi giữa chừng. `ALTER TABLE` cần MDL dạng exclusive, dù chỉ trong một khoảnh khắc.
- Chuỗi sự cố:
  1. Một transaction dài (một báo cáo nặng, hoặc ai đó mở transaction rồi quên commit) đang giữ MDL
     shared.
  2. `ALTER TABLE` xếp hàng chờ MDL exclusive.
  3. Mọi query mới trên bảng xếp hàng **sau** `ALTER`.
  4. Connection pool cạn và app sập, dù `ALTER` chưa chạy được dòng nào.
- Nhận biết: `SHOW PROCESSLIST` thấy trạng thái `Waiting for table metadata lock`.
- Cách phòng:
  - `SET lock_wait_timeout` ngắn (vài giây) cho session chạy DDL, thất bại thì thử lại.
  - Kiểm tra các transaction dài trước khi chạy migration.

**Đọc**
- MySQL:
  - [InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)
  - [Locks Set by Different SQL Statements](https://dev.mysql.com/doc/refman/8.4/en/innodb-locks-set.html)
  - [AUTO_INCREMENT Handling](https://dev.mysql.com/doc/refman/8.4/en/innodb-auto-increment-handling.html)
  - [Metadata Locking](https://dev.mysql.com/doc/refman/8.4/en/metadata-locking.html)
- Postgres: [Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html) (bảng xung đột giữa các table lock, và vì sao `ALTER TABLE` chặn cả `SELECT`)

**Nắm chắc khi**
- [ ] Cho một câu `UPDATE` và index hiện có, nói được nó khoá những dòng và khoảng nào ở RR
- [ ] Đọc được một deadlock log thật: hai transaction giữ gì, chờ gì, vì sao
- [ ] Giải thích được sự cố MDL từng bước và cách phòng

#### 3.3 Thay đổi schema online và migration không downtime

**Vì sao cần học:** Bảng lớn cộng với deploy liên tục thì một lần migration có thể thành sự cố
downtime lớn nhất năm.

**Học gì**

*Online DDL của MySQL*

| Algorithm | Làm gì | Ảnh hưởng | Ví dụ |
|---|---|---|---|
| `INSTANT` | Chỉ sửa metadata | Xong gần như ngay lập tức | Thêm cột (từ 8.0.29, ở mọi vị trí) |
| `INPLACE` | Dựng lại dữ liệu hoặc index tại chỗ | Thường vẫn cho đọc và ghi (`LOCK=NONE`) | Thêm index |
| `COPY` | Tạo bảng mới và copy toàn bộ | Khoá ghi suốt quá trình | Đổi kiểu dữ liệu của cột |

- Khai rõ `ALGORITHM=INSTANT` hoặc `INPLACE` trong câu `ALTER`. Nếu MySQL không làm được theo cách
  đó thì nó báo lỗi ngay, thay vì âm thầm chuyển sang `COPY`.
- Mọi loại đều cần MDL exclusive trong một khoảnh khắc, nên vẫn có thể dính sự cố MDL ở module 3.2.
- Laravel 13 có modifier cho việc này: `->instant()` và `->lock()` cho cột, `->inplace()` cho index
  và khoá ngoại.

*Tool cho các thao tác phải COPY*
- **pt-online-schema-change**:
  1. Tạo bảng mới có cấu trúc đã đổi.
  2. Dùng trigger chép các thay đổi mới sang bảng mới.
  3. Copy dữ liệu cũ theo từng khúc.
  4. Cuối cùng rename để đổi bảng.
- **gh-ost** (của GitHub) làm tương tự nhưng đọc binlog thay vì dùng trigger. Nhờ vậy ít tải lên
  primary hơn, tạm dừng hay điều tốc được, và tự chạy chậm lại khi replica bị trễ.
- Cả hai cần khoảng gấp đôi dung lượng của bảng, và phải cẩn thận nếu có khoá ngoại.

*Expand/contract*
- Trong lúc deploy, code cũ và code mới chạy song song vài phút. Vì vậy mỗi bước đổi schema phải
  chạy được với **cả hai** phiên bản code.
- Đổi tên cột an toàn cần 6 bước, mỗi bước một lần deploy:
  1. Thêm cột mới.
  2. Code ghi vào cả hai cột.
  3. Backfill dữ liệu cũ sang cột mới theo batch.
  4. Code chuyển sang đọc cột mới.
  5. Code ngừng ghi cột cũ.
  6. Xoá cột cũ.
- Thêm một cột `NOT NULL`: thêm cột nullable trước, backfill, rồi mới đặt `NOT NULL`.
- Backfill theo batch, và điều tốc theo độ trễ của replica.
- ⚠️ Xoá cột trong khi code cũ vẫn còn đọc nó sẽ gây lỗi ngay lúc deploy.
- ⚠️ Migration huỷ dữ liệu nên tách khỏi lần deploy app, và phải có kế hoạch lùi.

*Đối chiếu Postgres*
- `CREATE INDEX CONCURRENTLY` không khoá ghi, nhưng không chạy trong transaction được, và nếu lỗi
  thì để lại một index `INVALID`.
- `ADD CONSTRAINT ... NOT VALID` trước, rồi `VALIDATE CONSTRAINT` trong một bước riêng.
- `SET lock_timeout` trước khi chạy DDL.

**Đọc**
- MySQL: [Online DDL Operations](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html): **bảng tra cứu quan trọng nhất** của module này
- [gh-ost](https://github.com/github/gh-ost): README và thư mục `doc/` (đặc biệt phần so sánh với cách dùng trigger)
- [pt-online-schema-change](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html)
- Martin Fowler: [Parallel Change](https://martinfowler.com/bliki/ParallelChange.html)
- Laravel: [Migrations](https://laravel.com/docs/migrations)

**Nắm chắc khi**
- [ ] Lập được kế hoạch tách `full_name` thành hai cột trên bảng 50 triệu dòng đang nhận ghi (bài tập 5)
- [ ] Tra được trong bảng Online DDL: thêm cột, thêm index, đổi kiểu cột thì thuộc loại nào, có khoá ghi không

#### 3.4 Replication và failover

**Vì sao cần học:** Gần như mọi hệ thống production đều có replica. Replication lag và failover vừa
là nguồn sự cố, vừa là chủ đề câu hỏi quen thuộc.

**Học gì**

*Cơ chế*
- Primary nhận mọi thao tác ghi và ghi chúng vào binlog. Replica kéo binlog về và áp lại.
- *GTID*: mỗi transaction có một mã định danh toàn cục. Nhờ đó biết được replica đã áp tới đâu, và
  failover dễ hơn.

*Các mức đồng bộ*
- **Async** (mặc định): primary commit mà không chờ replica. Nếu primary chết, các giao dịch chưa kịp
  sang replica sẽ mất.
- **Semi-sync**: primary chờ ít nhất một replica xác nhận **đã nhận** binlog (chưa chắc đã áp) rồi
  mới báo commit thành công. Giảm khả năng mất dữ liệu, đổi lại latency ghi tăng.
  - ⚠️ Chờ quá timeout thì semi-sync tự quay về async.
- **Group Replication / InnoDB Cluster**: các node đồng thuận với nhau trước khi commit (chỉ cần
  biết đại ý).
- Replica giảm tải đọc, **không** giảm tải ghi, vì replica nào cũng phải áp mọi thao tác ghi.

*Replication lag*
- Nguyên nhân thường gặp:
  - Một transaction rất lớn, ví dụ một câu `UPDATE` 1 triệu dòng.
  - Replica yếu hơn primary.
  - Áp log không đủ song song.
  - Có query nặng đang chạy trên replica.
- Cách đo: `Seconds_Behind_Source`.
  - ⚠️ Chỉ số này không hoàn toàn đáng tin: nó là NULL khi luồng nhận log đã ngừng, và có thể hiện 0
    gây hiểu nhầm khi mạng chậm khiến replica chưa nhận được log mới.
  - Cách tốt hơn là dùng heartbeat table (`pt-heartbeat`).

*Read-your-writes*
- Triệu chứng: user sửa tên, tải lại trang vẫn thấy tên cũ, vì trang đọc từ một replica đang bị trễ.
- Các cách xử lý:
  - Bật sticky trong phạm vi request.
  - Đọc từ primary trong vài giây sau khi user ghi, bằng cách lưu mốc thời gian trong session hoặc
    cookie.
  - Dữ liệu "của chính mình" thì luôn đọc từ primary.
  - Chờ replica áp tới GTID vừa ghi (`WAIT_FOR_EXECUTED_GTID_SET`).
- ⚠️ Luồng "đọc để ghi", ví dụ kiểm tra số dư rồi trừ, **không bao giờ** được đọc từ replica.

*Failover*
- Khi primary chết: chọn replica mới nhất làm primary, rồi trỏ app sang đó (qua DNS, proxy hoặc VIP).
  Tool thường dùng: Orchestrator, MySQL InnoDB Cluster/Router, hoặc dịch vụ managed như RDS, Cloud SQL.
- ⚠️ Failover ở chế độ async có thể mất vài giao dịch cuối.
- ⚠️ *Split brain*: primary cũ sống lại và vẫn nhận ghi, nên có hai primary cùng lúc. Cần *fencing*,
  tức chắc chắn chặn hẳn primary cũ ([14-distributed-systems.md](14-distributed-systems.md)).
- App phải chịu được: connection bị đứt giữa chừng, cần retry, DNS TTL, và pool hoặc persistent
  connection vẫn còn trỏ tới node cũ.

**Đọc**
- MySQL: [Replication](https://dev.mysql.com/doc/refman/8.4/en/replication.html), [Semisynchronous Replication](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html)
- DDIA ch.5
- Phần hệ phân tán: [14-distributed-systems.md](14-distributed-systems.md)

**Nắm chắc khi**
- [ ] Giải thích được semi-sync đảm bảo gì và **không** đảm bảo gì
- [ ] Thiết kế được cơ chế read-your-writes cho app Laravel có 1 primary và 3 replica

#### 3.5 Backup, PITR, RPO/RTO

**Vì sao cần học:** "Ai đó chạy `DELETE` quên `WHERE`" là câu tình huống kinh điển. Senior phải
biết cách khôi phục tới đúng phút.

**Học gì**

*Hai loại backup*
- **Logical backup** dump dữ liệu ra các câu SQL.
  - `mysqldump --single-transaction` lấy được snapshot nhất quán mà không khoá bảng InnoDB. `mydumper`
    chạy song song nên nhanh hơn.
  - Ưu: dễ di chuyển, chọn được từng bảng. Nhược: chậm, và restore rất lâu với DB lớn.
- **Physical backup** copy trực tiếp file dữ liệu (Percona XtraBackup, MySQL Enterprise Backup,
  snapshot ổ đĩa).
  - Ưu: nhanh với DB lớn. Nhược: gắn chặt với phiên bản MySQL.

*Khôi phục tới một thời điểm*
- **PITR** (point-in-time recovery) cần full backup cộng với binlog liên tục:
  1. Restore bản full backup.
  2. Replay binlog tới ngay trước thời điểm sự cố (`mysqlbinlog --stop-datetime` hoặc
     `--stop-position`).

  Điều kiện: binlog phải được copy liên tục ra một nơi khác.
- **RPO và RTO**:
  - *RPO*: được phép mất tối đa bao nhiêu dữ liệu, tính bằng thời gian.
  - *RTO*: mất bao lâu để hệ thống chạy lại.

*Những điều hay bị quên*
- ⚠️ Replica **không phải** backup: `DROP TABLE` được replicate sang ngay. Delayed replica là một
  trường hợp đặc biệt.
- ⚠️ Backup chưa từng restore thử thì coi như chưa có backup. Diễn tập định kỳ và đo thời gian
  restore thật.
- Backup phải được mã hoá, tách quyền truy cập, và để ở account hoặc region khác.

**Đọc**
- MySQL: [Point-in-Time Recovery](https://dev.mysql.com/doc/refman/8.4/en/point-in-time-recovery.html)
- [18-reliability-observability.md](18-reliability-observability.md) (RPO/RTO, DR)

**Nắm chắc khi**
- [ ] Kể được từng bước xử lý sự cố `DELETE` quên `WHERE` lúc 14:03, và ước lượng được RPO thực tế

#### 3.6 Scale: partitioning, sharding, archiving

**Vì sao cần học:** Câu hỏi senior không phải "sharding là gì" mà là "khi nào thì shard, và phải
trả giá gì".

**Học gì**

*Thứ tự nên thử trước khi shard*
1. Tối ưu query và index. Đây là cách rẻ nhất và thường giải quyết được nhiều nhất.
2. Thêm cache cho dữ liệu đọc nhiều.
3. Thêm read replica để giảm tải đọc.
4. Nâng cấp máy lớn hơn (scale dọc). Máy DB hiện nay đi được rất xa.
5. Tách DB theo chức năng: mỗi nhóm bảng hoặc mỗi service một DB.
6. Partition và archive dữ liệu cũ.
7. Shard. Chỉ làm khi đã hết các cách trên, vì nó làm hệ thống phức tạp vĩnh viễn.

*Partitioning (vẫn trong một DB)*
- Một bảng logic được chia thành nhiều phần vật lý theo một cột. Có ba kiểu: range (theo tháng),
  list (theo vùng), hash (chia đều). App vẫn query như với một bảng bình thường.
- Lợi ích:
  - Query có điều kiện trên cột partition chỉ đọc các partition liên quan (*partition pruning*).
  - Xoá dữ liệu cũ bằng `DROP PARTITION` gần như tức thì, thay vì `DELETE` hàng triệu dòng.
- ⚠️ Query không có điều kiện trên cột partition phải quét mọi partition.
- ⚠️ Mọi PK và unique key phải chứa cột partition.
- ⚠️ Bảng partitioned của MySQL không dùng được khoá ngoại.

*Sharding (nhiều DB)*
- Chia dữ liệu ra nhiều server DB độc lập, mỗi server giữ một phần gọi là *shard*. Sharding giảm được
  tải ghi, điều mà replica không làm được. Cái giá là độ phức tạp vĩnh viễn.
- **Shard key** là cột quyết định một dòng nằm ở shard nào. Chọn sao cho tải chia đều, và phần lớn
  query có chứa key đó (thường là `tenant_id` hoặc `user_id`).
  - ⚠️ Shard theo thời gian tạo khiến mọi thao tác ghi dồn vào shard mới nhất.
  - ⚠️ Chọn sai shard key thì rất khó sửa về sau.
- **Định tuyến** (tìm shard cho một key):
  - `hash(key) % N`: đơn giản, nhưng thêm shard thì phải chuyển gần hết dữ liệu.
  - *Consistent hashing*: thêm shard chỉ phải chuyển một phần dữ liệu.
  - *Directory*: một bảng tra key → shard. Linh hoạt, nhưng thêm một thành phần phải giữ cho nó luôn sống.
- **Những gì mất đi khi shard**:
  - Join, aggregate, sort xuyên shard phải làm ở tầng app (*scatter-gather*).
  - Transaction xuyên shard cần 2PC hoặc saga ([14-distributed-systems.md](14-distributed-systems.md)).
  - Unique toàn cục và auto-increment không còn dùng được; phải sinh ID phân tán (Snowflake, UUIDv7).
- **Resharding**:
  - Chia sẵn nhiều shard logic (ví dụ 1024) đặt trên ít máy vật lý. Về sau chỉ việc di chuyển shard
    logic sang máy mới.
  - Quy trình di chuyển: copy dữ liệu kèm CDC, đối soát, chuyển đọc, rồi mới chuyển ghi.
- **Vitess** (YouTube, PlanetScale) là lớp proxy cho MySQL: tự định tuyến theo shard key, và
  resharding online.

*Archiving*
- Ví dụ bảng đơn hàng có 5 năm dữ liệu nhưng chỉ 3 tháng gần nhất hay được đọc. Chuyển dữ liệu cũ
  sang bảng hoặc DB archive, kho OLAP, hoặc object storage.
- ⚠️ `DELETE` hàng triệu dòng một lần sẽ giữ lock lâu, làm replica trễ và undo log phình. Hãy xoá
  theo batch, hoặc drop partition.

**Đọc**
- MySQL: [Partitioning](https://dev.mysql.com/doc/refman/8.4/en/partitioning.html), [Restrictions and Limitations](https://dev.mysql.com/doc/refman/8.4/en/partitioning-limitations.html)
- DDIA ch.6
- [Vitess docs](https://vitess.io/docs/): phần *Concepts* (keyspace, vindex, resharding)
- Case study:
  - [Notion: Sharding Postgres](https://www.notion.com/blog/sharding-postgres-at-notion) (chọn shard key, shard logic, migration)
  - [Figma: How Figma's databases team lived to tell the scale](https://www.figma.com/blog/how-figmas-databases-team-lived-to-tell-the-scale/) (tách theo chiều dọc rồi mới shard ngang)
  - [Shopify Ghostferry](https://github.com/shopify/ghostferry) (di chuyển dữ liệu giữa các shard MySQL online)

**Nắm chắc khi**
- [ ] Bảo vệ được quyết định **chưa** shard cho một hệ 2TB, 5k QPS
- [ ] Chọn được shard key cho SaaS multi-tenant và nói được nó xử lý thế nào khi gặp một tenant rất lớn

#### 3.7 MySQL so với Postgres

**Vì sao cần học:** Câu "chọn MySQL hay Postgres" dùng để xem bạn hiểu trade-off hay chỉ đang theo
thói quen.

**Học gì**

*So sánh 10 điểm*

| | MySQL (InnoDB) | PostgreSQL |
|---|---|---|
| Lưu trữ | Bảng là clustered index theo PK | Heap, index trỏ tới vị trí vật lý |
| MVCC | Bản cũ nằm trong undo log, purge dọn | Bản cũ nằm ngay trong bảng, VACUUM dọn |
| Isolation mặc định | Repeatable Read | Read Committed |
| Connection | Mỗi connection một thread | Mỗi connection một process, thường cần PgBouncer |
| Join | Nested loop, hash join | Nested loop, hash join, merge join |
| Index | B-tree, full-text, spatial, functional | Thêm hash, GIN, GiST, BRIN, partial index |
| DDL trong transaction | Không, DDL tự commit | Có, migration rollback được |
| Kiểu dữ liệu | Cơ bản, có `JSON` | `jsonb`, mảng, range, `inet`, `uuid`, kiểu tự định nghĩa |
| Mở rộng | Plugin hạn chế | Extension: PostGIS, pg_trgm, pgvector, TimescaleDB, Citus |
| Hệ sinh thái scale | Vitess, ProxySQL, gh-ost, Orchestrator | Citus, Patroni, PgBouncer |

*Hệ quả thực tế*
- **Hệ quả khi vận hành**:
  - Postgres với workload update nhiều thì dễ bị bloat và phụ thuộc vào autovacuum. Mỗi connection
    là một process tốn vài MB, nên phải dùng PgBouncer.
  - MySQL không cho DDL trong transaction, nên migration lỗi giữa chừng để lại schema dở dang. Loại
    index và kiểu dữ liệu cũng ít hơn.
- **PgBouncer transaction mode**: một connection tới server được chia cho nhiều client theo từng
  transaction. Vì vậy các tính năng gắn với session sẽ hỏng: `SET`, advisory lock cấp session,
  `LISTEN`, và prepared statement ở một số phiên bản.

*Chọn cái nào*
- **Trả lời "chọn cái nào"**: không có đáp án chung. Cân nhắc theo đội ngũ đang quen gì, cần tính
  năng gì (GIS, jsonb, extension như pgvector), và dịch vụ managed nào sẵn có.

**Đọc**
- [Uber: Why Uber Engineering Switched from Postgres to MySQL](https://www.uber.com/us/en/blog/postgres-to-mysql-migration/) (2016). Đọc kèm phản biện từ cộng đồng Postgres để thấy cả hai phía; một số điểm đã cũ
- [PgBouncer features](https://www.pgbouncer.org/features.html) (bảng tính năng theo từng pooling mode)
- Postgres [release notes 18](https://www.postgresql.org/docs/current/release-18.html): lướt để biết cái mới (async I/O, `uuidv7()`, skip scan)

**Nắm chắc khi**
- [ ] Nói được trong 3 phút vì sao cùng một workload update nhiều, MySQL và Postgres gặp vấn đề khác nhau

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Index là gì, vì sao dùng B+tree? Khi nào không nên thêm index?** (1.2)
- Ý phải có: cấu trúc sắp xếp riêng; cây thấp nên ít lần đọc page; lá nối nhau nên range scan và sort rẻ; hash không làm được range. Không thêm index khi: bảng ghi nhiều đọc ít, cột selectivity thấp, đã có index trùng tiền tố
- Điểm cộng: nói được cái giá khi ghi và khi dùng buffer pool
- Red flag: "index cho mọi cột trong WHERE"

**2. Vì sao `OFFSET` lớn lại chậm? Sửa thế nào?** (2.3)
- Ý phải có: DB vẫn đọc rồi bỏ `OFFSET` dòng đầu; dùng keyset pagination kèm cột tie-breaker
- Điểm cộng: keyset không nhảy thẳng tới trang N được; deferred join khi bắt buộc phải có số trang
- Red flag: "thêm index cho cột id là xong"

**3. `WHERE` và `HAVING` khác nhau thế nào?** (1.1)
- Ý phải có: lọc dòng trước khi gom nhóm so với lọc nhóm sau khi gom; `HAVING` dùng được aggregate
- Điểm cộng: nói luôn thứ tự thực thi logic của cả câu SQL

**4. Vì sao không lưu tiền bằng `FLOAT`?** (1.4)
- Ý phải có: số nhị phân không biểu diễn chính xác `0.1`; cộng dồn thì lệch. Dùng `DECIMAL` hoặc số nguyên theo đơn vị nhỏ nhất
- Điểm cộng (PHP): PDO trả `DECIMAL` dạng string, ép `(float)` là mất luôn độ chính xác; dùng bcmath hoặc thư viện money

**5. ACID là gì? Cho ví dụ từng chữ.** (1.3)
- Ý phải có: mỗi chữ một ví dụ nghiệp vụ, không đọc định nghĩa
- Điểm cộng: chữ C phần lớn do ứng dụng giữ; chữ D phụ thuộc cấu hình flush

**6. N+1 query là gì, phát hiện và sửa thế nào?** (2.7)
- Ý phải có: 1 query lấy danh sách, rồi mỗi phần tử thêm 1 query; sửa bằng eager loading hoặc `IN`
- Điểm cộng: vì sao nó không hiện trên slow log; `preventLazyLoading()` ở môi trường dev; eager load nhiều collection bằng join sẽ nhân dòng

### 🟡 Mid

**7. Index `(user_id, status, created_at)`. Query `WHERE status = 1 AND created_at > ?` có dùng index không?** (2.2)
- Ý phải có: không seek được vì thiếu cột đầu (leftmost prefix); có thể quét cả index nếu index là covering
- Điểm cộng: skip scan tồn tại nhưng phụ thuộc cardinality của `user_id`; đề xuất index mới dựa trên *tập query*, không dựa trên một query

**8. Clustered và secondary index khác nhau thế nào? Covering index là gì?** (2.1)
- Ý phải có: bảng chính là cây theo PK; secondary index lưu PK nên phải lookup thêm; covering index thì không phải lookup
- Điểm cộng: vì sao UUIDv4 làm PK có hại; đối chiếu heap của Postgres

**9. Có một query chậm trên production. Bạn làm gì?** (2.3)
- Ý phải có: đo trước (slow log, APM), `EXPLAIN ANALYZE`, sửa, đo lại
- Điểm cộng: xếp hạng theo tần suất × thời gian; tách các nguyên nhân: query tệ, lock wait, connection cạn, working set vượt RAM, plan đổi do statistics
- Red flag: nhảy ngay vào "thêm cache"

**10. Hai người cùng sửa một bài viết, làm sao không ghi đè mất sửa đổi của nhau?** (2.6)
- Ý phải có: optimistic lock bằng cột version, kiểm tra số dòng bị ảnh hưởng, báo xung đột cho người dùng
- Điểm cộng: vì sao không dùng `FOR UPDATE` ở đây (người dùng suy nghĩ vài phút mà vẫn giữ lock)

**11. Kể các isolation level. MySQL và Postgres mặc định level nào?** (2.5)
- Ý phải có: bảng anomaly theo từng level; MySQL RR, Postgres RC
- Điểm cộng: MySQL RR vẫn để lọt lost update, Postgres RR thì báo `40001`; consistent read và locking read khác nhau
- Red flag: thuộc bảng chuẩn ANSI nhưng không biết DB mình dùng thực tế hành xử thế nào

**12. Flash sale 100 sản phẩm, 10.000 người cùng mua. Làm sao không bán quá?** (2.5, 2.6)
- Ý phải có: `UPDATE ... SET stock = stock - 1 WHERE id = ? AND stock > 0` và kiểm tra số dòng bị ảnh hưởng; hoặc `FOR UPDATE`
- Điểm cộng: một dòng tồn kho trở thành nút cổ chai, nên chia bucket hoặc giữ chỗ trước bằng Redis/queue rồi đối soát; chống double submit bằng idempotency key ([13-concurrency.md](13-concurrency.md))
- Red flag: "bọc trong transaction là đủ"

**13. Deadlock xảy ra thế nào? Phòng thế nào?** (2.6, 3.2)
- Ý phải có: chờ vòng tròn; InnoDB tự phát hiện và rollback một bên; phòng bằng khoá theo thứ tự cố định, transaction ngắn, index đúng
- Điểm cộng: **retry là bắt buộc** (`DB::transaction($fn, 3)`); gap lock là nguồn deadlock ở RR; đọc được deadlock log

**14. `NOT IN` với subquery có NULL trả về gì? Vì sao?** (1.1)
- Ý phải có: tập rỗng, vì `x <> NULL` cho kết quả UNKNOWN; dùng `NOT EXISTS`

**15. Đổi tên cột không downtime thế nào?** (3.3)
- Ý phải có: expand/contract gồm thêm cột, ghi cả hai, backfill, chuyển đọc, bỏ cột cũ; mỗi bước một lần deploy
- Điểm cộng: ORM cache danh sách cột; backfill theo batch và điều tốc theo replica lag

**16. PHP-FPM có connection pool không? Hệ thống của bạn mở tối đa bao nhiêu connection tới DB?** (2.7)
- Ý phải có: không có pool trong process; mỗi worker một connection; tổng = số server × `max_children` + queue worker
- Điểm cộng: autoscale có thể đánh sập DB; ProxySQL làm lớp pool bên ngoài; rủi ro của persistent connection
- Red flag: không biết con số của chính hệ thống mình đang làm

**17. Dispatch job ngay sau khi tạo đơn hàng, trong cùng transaction. Có vấn đề gì?** (2.7)
- Ý phải có: worker có thể chạy trước khi transaction commit, nên không thấy dữ liệu hoặc xử lý đơn đã bị rollback; dùng `afterCommit`
- Điểm cộng: `afterCommit` vẫn mất job nếu process chết ngay sau commit, nên cần outbox pattern để đảm bảo

### 🔴 Senior

**18. Write skew là gì? RR có chặn được không?** (2.5)
- Ý phải có: hai transaction đọc cùng tập dữ liệu rồi sửa các dòng khác nhau, cùng nhau vi phạm ràng buộc; RR không chặn được
- Điểm cộng: 3 cách sửa (khoá tập đã đọc, đưa ràng buộc xuống DB, Serializable); SSI của Postgres phát hiện bằng cách theo dõi phụ thuộc đọc-ghi

**19. MVCC của InnoDB và Postgres khác nhau thế nào? Hệ quả vận hành là gì?** (3.1)
- Ý phải có: InnoDB giữ bản cũ trong undo log và dọn bằng purge; Postgres giữ tuple cũ trong heap và dọn bằng VACUUM
- Điểm cộng: transaction dài hại cả hai phía (history list length, bloat); wraparound của Postgres; HOT update

**20. Redo log, undo log, binlog khác nhau thế nào? Vì sao cần two-phase commit giữa chúng?** (3.1)
- Ý phải có: mục đích của từng log (crash recovery, rollback/MVCC, replication/PITR); không có 2PC thì redo và binlog lệch nhau sau crash, replica khác primary
- Điểm cộng: `flush_log_at_trx_commit` và `sync_binlog`; doublewrite buffer

**21. Gap lock và next-key lock là gì? Vì sao gây deadlock?** (3.2)
- Ý phải có: khoá khoảng trống để chặn phantom; gap lock của các transaction không xung đột nhau nhưng đều chặn insert
- Điểm cộng: kịch bản `FOR UPDATE` trên id chưa tồn tại rồi cùng insert; đánh đổi khi chuyển sang RC

**22. Migration thêm cột làm cả app treo 5 phút, mọi request timeout. Vì sao?** (3.2, 3.3)
- Ý phải có: metadata lock; có một transaction dài đang giữ MDL, `ALTER` chờ, các query sau xếp hàng sau `ALTER`
- Điểm cộng: xác nhận qua `performance_schema.metadata_locks`; phòng bằng `lock_wait_timeout` ngắn kèm retry, kiểm tra transaction dài trước khi migrate
- Red flag: "tại ALTER chậm, chạy lúc nửa đêm là được"

**23. Bảng 500 triệu dòng, cần thêm cột và thêm index. Làm thế nào?** (3.3)
- Ý phải có: tra xem INSTANT/INPLACE làm được không; nếu phải copy bảng thì dùng gh-ost
- Điểm cộng: dung lượng đĩa cần gấp đôi; điều tốc theo replica lag; kế hoạch rollback; theo dõi trong lúc chạy

**24. Query đang 20ms, sau một đợt import thành 8 giây, code không đổi.** (2.3)
- Ý phải có: plan đã đổi; so `EXPLAIN` trước và sau; statistics cũ thì `ANALYZE TABLE`
- Điểm cộng: dữ liệu lệch cần histogram; ngắn hạn dùng hint, dài hạn làm index tốt hơn; cảnh báo khi p95 của query tăng

**25. `DELETE FROM orders` quên `WHERE` lúc 14:03 trên production. Làm gì?** (3.5)
- Ý phải có: dừng ghi liên quan; replica cũng đã xoá theo; PITR ra máy riêng rồi chép phần dữ liệu mất về
- Điểm cộng: RPO thực tế là bao nhiêu; hậu kiểm gồm phân quyền, `sql_safe_updates`, quy trình chạy query tay; postmortem không đổ lỗi cá nhân

**26. Khi nào bạn quyết định shard? Chọn shard key thế nào?** (3.6)
- Ý phải có: shard là lựa chọn cuối; shard key phải chia đều tải và có mặt trong phần lớn query
- Điểm cộng: shard logic nhiều hơn máy vật lý; tenant lớn; ID toàn cục; câu chuyện thật của Notion/Figma
- Red flag: đề xuất shard khi chưa hỏi quy mô

**27. Chọn MySQL hay Postgres cho dự án mới?** (3.7)
- Ý phải có: tuỳ bối cảnh (đội ngũ, tính năng cần, dịch vụ managed); nêu 3–4 khác biệt thật
- Điểm cộng: nói được workload nào làm mỗi DB khổ (update nhiều ở Postgres, thao tác cần DDL trong transaction ở MySQL)
- Red flag: "Postgres tốt hơn" mà không nói tốt hơn ở điểm nào

**28. Replica lag làm user thấy dữ liệu cũ ngay sau khi sửa. Thiết kế cách xử lý.** (3.4)
- Ý phải có: sticky, đọc primary sau khi ghi, chờ replica bắt kịp GTID
- Điểm cộng: chấp nhận eventual consistency ở màn hình không quan trọng; không đọc replica trong luồng đọc để ghi; cảnh báo khi lag vượt ngưỡng

---

## Bài tập tự làm

1. **SQL kinh điển.** Schema:
   - `users(id, name, email, created_at)`
   - `orders(id, user_id, total, status, created_at)`
   - `logins(user_id, login_date)`
   - `employees(id, name, manager_id, department_id, salary)`

   Viết query cho từng đề, chạy trên MySQL 8.4:
   - a. Top 3 đơn giá trị lớn nhất của mỗi user. Nói rõ bạn xử lý các đơn bằng giá trị thế nào.
   - b. Doanh thu theo ngày và doanh thu cộng dồn trong tháng.
   - c. User trùng email (không phân biệt hoa thường), và câu xoá bản trùng, giữ bản có id nhỏ nhất.
   - d. Chuỗi ngày đăng nhập liên tiếp dài nhất của mỗi user.
   - e. User đăng ký trong tháng 1 nhưng chưa từng có đơn `paid`. Viết hai cách, trong đó một cách dính bẫy NULL.
   - f. Nhân viên có lương cao hơn quản lý trực tiếp; và toàn bộ cấp dưới (mọi tầng) của nhân viên id 1.
   - g. Mức lương cao thứ hai của mỗi phòng ban.
   - h. Tỉ lệ user mua lần thứ hai trong vòng 30 ngày kể từ đơn đầu tiên.
2. **Thiết kế index.** Bảng `orders` 100 triệu dòng, có 4 query:
   - Danh sách đơn của một user, mới nhất trước, có phân trang
   - Các đơn `pending` quá 30 phút
   - Doanh thu theo ngày của một shop
   - Tìm đơn theo mã đơn

   Đề xuất bộ index tối thiểu, giải thích thứ tự cột, và ghi `EXPLAIN` bạn kỳ vọng cho từng query.
3. **Anomaly bằng tay.** Mở hai session `mysql` và tái hiện:
   - Non-repeatable read ở RC
   - Lost update ở RR
   - "Phantom" khi trộn consistent read với locking read ở RR
   - Deadlock do gap lock

   Nếu có Postgres: tái hiện thêm lỗi `40001` ở RR, và write skew bị chặn ở Serializable. Ghi lại từng bước và kết quả. Có thể đối chiếu với [Hermitage](https://github.com/ept/hermitage).
4. **Job queue bằng DB.** Thiết kế bảng `jobs` và query cho worker dùng `SKIP LOCKED`. Cần có:
   - Retry có backoff
   - Giới hạn số lần thử
   - Xử lý worker chết giữa chừng

   Nêu dấu hiệu khiến bạn chuyển sang một queue thật.
5. **Migration không downtime.** Lập kế hoạch từng bước để tách `users.full_name` thành `first_name` và `last_name` trên bảng 50 triệu dòng đang nhận ghi liên tục. Mỗi bước ghi rõ: deploy code gì, đổi schema gì, rollback thế nào.
6. **PHP/Laravel.** Trong một project Laravel (có thể là project mới):
   - Tạo một màn hình có N+1, bật `preventLazyLoading()` để bắt lỗi, rồi sửa.
   - Viết một luồng tạo đơn dispatch job trong transaction, tái hiện việc job chạy trước khi commit, rồi sửa bằng `afterCommit`.
   - Tính số connection tối đa khi chạy 4 server × `pm.max_children = 50` cộng 10 queue worker, và so với `max_connections` mặc định của MySQL.

> Nộp bài vào đây để được review.
