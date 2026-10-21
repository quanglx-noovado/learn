# Chương 10. Window function

> [← Mục lục](README.md) · [← Chương 09: Subquery, CTE, UNION](09-subquery-cte-union.md) · [Chương 11: Index →](11-index.md)

**Bạn sẽ học được:**

- Window function là gì, khác `GROUP BY` ở chỗ nào, và vì sao nó giải gọn những bài mà trước đây phải
  self-join hoặc subquery lồng nhau.
- Đọc và viết được mệnh đề `OVER`: `PARTITION BY`, `ORDER BY`, frame, và window đặt tên bằng
  mệnh đề `WINDOW`.
- Dùng đúng các hàm xếp hạng (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`), các hàm lấy giá trị
  theo vị trí (`LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE`) và aggregate dùng như window
  function (running total, trung bình trượt).
- Hiểu frame `ROWS` và `RANGE`, frame mặc định, và hai cái bẫy kinh điển do frame mặc định gây ra.
- Tự viết được các bài kinh điển: top N mỗi nhóm, running total, giá trị lớn thứ N, so với kỳ trước,
  gaps and islands.
- Biết MySQL thực thi window function ra sao, tốn kém ở đâu, và khác PostgreSQL ở những điểm nào.

**Cần biết trước:** [Chương 05](05-select-co-ban.md) (`SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, thứ
tự thực thi logic), [Chương 06](06-ham-bieu-thuc-null.md) (NULL, `CASE`, `COALESCE`, `NULLIF`, hàm
ngày giờ), [Chương 08](08-group-by-aggregate.md) (`GROUP BY`, hàm tổng hợp, `ONLY_FULL_GROUP_BY`),
[Chương 09](09-subquery-cte-union.md) (subquery trong `FROM`, CTE, recursive CTE).

## 1. Dữ liệu mẫu của chương

Mọi ví dụ trong chương chạy trên MySQL 8.4 với bộ dữ liệu dưới đây; chỗ nào là PostgreSQL sẽ ghi rõ.
Nếu chưa có MySQL, chạy bằng Docker:

```bash
# Chạy trên máy của bạn (terminal thường)
docker run -d --name my84 -e MYSQL_ROOT_PASSWORD=root mysql:8.4
# đợi vài giây cho server khởi động xong, rồi mở client:
docker exec -it my84 mysql -uroot -proot --default-character-set=utf8mb4
```

Rồi dán đoạn SQL sau vào client `mysql`:

```sql
DROP DATABASE IF EXISTS ch10;      -- database riêng của chương này, xoá đi tạo lại cho sạch
CREATE DATABASE ch10;
USE ch10;

-- Nhân viên: dùng cho xếp hạng, top N mỗi nhóm, giá trị lớn thứ N
CREATE TABLE employees (
  id     INT PRIMARY KEY,
  dept   VARCHAR(20) NOT NULL,       -- phòng ban
  name   VARCHAR(50) NOT NULL,
  salary INT NOT NULL                -- lương tháng, đơn vị: USD
);
INSERT INTO employees VALUES
  (1, 'eng',   'An',    3000),
  (2, 'eng',   'Bình',  2500),
  (3, 'eng',   'Chi',   2500),       -- Bình và Chi bằng lương nhau: cố ý, để thấy cách xử lý "đồng hạng"
  (4, 'eng',   'Dũng',  2000),
  (5, 'sales', 'Em',    2200),
  (6, 'sales', 'Giang', 1800),
  (7, 'sales', 'Hà',    1800),
  (8, 'ops',   'Khoa',  1500);

-- Giao dịch tài khoản: dùng cho running total (số dư sau từng giao dịch)
CREATE TABLE transactions (
  id       INT PRIMARY KEY,
  account  VARCHAR(10) NOT NULL,
  txn_date DATE NOT NULL,
  amount   INT NOT NULL              -- dương: nạp vào, âm: rút ra
);
INSERT INTO transactions VALUES
  (1, 'A', '2026-03-01',  100),
  (2, 'A', '2026-03-02',   50),
  (3, 'A', '2026-03-02',  -30),      -- hai giao dịch cùng ngày 02: cố ý
  (4, 'A', '2026-03-04',   20),
  (5, 'B', '2026-03-01',  200),
  (6, 'B', '2026-03-03',  -50);

-- Doanh thu theo ngày: dùng cho LAG/LEAD, trung bình trượt.
-- Ngày 2026-04-04 cửa hàng nghỉ nên KHÔNG có dòng nào (cố ý).
CREATE TABLE daily_sales (
  day     DATE PRIMARY KEY,
  revenue INT NOT NULL
);
INSERT INTO daily_sales VALUES
  ('2026-04-01', 100),
  ('2026-04-02', 120),
  ('2026-04-03',  80),
  ('2026-04-05', 150),
  ('2026-04-06', 130);

-- Doanh thu theo tháng: dùng cho "so với kỳ trước". Chỉ có quý 1 của hai năm (cố ý).
CREATE TABLE monthly_revenue (
  month_start DATE PRIMARY KEY,      -- ngày đầu tháng, ví dụ 2026-01-01 là tháng 1/2026
  revenue     INT NOT NULL
);
INSERT INTO monthly_revenue VALUES
  ('2025-01-01', 100), ('2025-02-01',  80), ('2025-03-01', 120),
  ('2026-01-01', 150), ('2026-02-01',  60), ('2026-03-01', 180);

-- Lịch sử đăng nhập: dùng cho gaps and islands. User 1 đăng nhập hai lần trong ngày 05-02 (cố ý).
CREATE TABLE logins (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  login_date DATE NOT NULL
);
INSERT INTO logins (user_id, login_date) VALUES
  (1, '2026-05-01'), (1, '2026-05-02'), (1, '2026-05-02'), (1, '2026-05-03'),
  (1, '2026-05-05'), (1, '2026-05-06'),
  (2, '2026-05-01'), (2, '2026-05-03'), (2, '2026-05-04'), (2, '2026-05-05'),
  (2, '2026-05-06');

-- Số đo cảm biến theo phút: NULL là lúc cảm biến không gửi số liệu
CREATE TABLE readings (
  t   INT PRIMARY KEY,               -- phút thứ t
  val INT NULL
);
INSERT INTO readings VALUES (1, 10), (2, NULL), (3, NULL), (4, 15), (5, NULL);
```

Bảng `employees` được dùng nhiều nhất, nên nhớ hình dạng của nó:

```
+----+-------+-------+--------+
| id | dept  | name  | salary |
+----+-------+-------+--------+
|  1 | eng   | An    |   3000 |
|  2 | eng   | Bình  |   2500 |
|  3 | eng   | Chi   |   2500 |
|  4 | eng   | Dũng  |   2000 |
|  5 | sales | Em    |   2200 |
|  6 | sales | Giang |   1800 |
|  7 | sales | Hà    |   1800 |
|  8 | ops   | Khoa  |   1500 |
+----+-------+-------+--------+
```

Tổng lương: phòng `eng` 10000 (4 người), `sales` 5800 (3 người), `ops` 1500 (1 người), cả công ty
17300. Các con số này sẽ xuất hiện lại nhiều lần, bạn có thể tự kiểm tra kết quả bằng tay.

Quy ước trình bày: kết quả in sau mỗi câu SQL là kết quả mong đợi khi chạy trên dữ liệu trên (tự
tính bằng tay theo tài liệu MySQL, khung bảng có thể rộng hẹp khác client của bạn một chút). Những
chỗ là "output minh hoạ" sẽ ghi rõ.

## 2. Window function là gì

### 2.1 Bài toán mở đầu: đặt "trung bình phòng" cạnh từng nhân viên

Sếp nhờ bạn: "Liệt kê từng nhân viên, kèm lương trung bình của phòng người đó, để xem ai đang được
trả cao hay thấp hơn mặt bằng phòng."

Thử với `GROUP BY` (chương 08):

```sql
SELECT dept, AVG(salary) AS dept_avg
FROM employees
GROUP BY dept
ORDER BY dept;
```

```
+-------+-----------+
| dept  | dept_avg  |
+-------+-----------+
| eng   | 2500.0000 |
| ops   | 1500.0000 |
| sales | 1933.3333 |
+-------+-----------+
```

Có trung bình, nhưng mất từng người: `GROUP BY` gộp mỗi nhóm thành **một** dòng. Thêm `name` vào
danh sách `SELECT` thì sao?

```sql
SELECT name, dept, salary, AVG(salary)
FROM employees
GROUP BY dept;
-- ERROR 1055 (42000): Expression #1 of SELECT list is not in GROUP BY clause and contains
-- nonaggregated column 'ch10.employees.name' which is not functionally dependent on columns
-- in GROUP BY clause; this is incompatible with sql_mode=only_full_group_by
```

Lỗi này là đúng (chương 08 đã giải thích): một nhóm `eng` có bốn tên, MySQL không biết in tên nào
lên dòng duy nhất của nhóm. Câu hỏi của sếp vốn cần **giữ nguyên tám dòng** và **thêm một cột** tính
từ cả nhóm. Trước khi có window function, phải viết vòng:

```sql
-- Cách 1: tính trung bình từng phòng trong derived table, rồi JOIN ngược lại
SELECT e.name, e.dept, e.salary, d.dept_avg
FROM employees e
JOIN (SELECT dept, AVG(salary) AS dept_avg FROM employees GROUP BY dept) d
  ON d.dept = e.dept
ORDER BY e.id;

-- Cách 2: correlated subquery, chạy lại cho mỗi dòng (về logic)
SELECT e.name, e.dept, e.salary,
       (SELECT AVG(x.salary) FROM employees x WHERE x.dept = e.dept) AS dept_avg
FROM employees e
ORDER BY e.id;
```

Cả hai đều đúng, nhưng phải đọc bảng hai lần và câu SQL dài ra theo số chỉ số cần tính. Với window
function:

```sql
SELECT name, dept, salary,
       AVG(salary) OVER (PARTITION BY dept)          AS dept_avg,
       salary - AVG(salary) OVER (PARTITION BY dept) AS diff
FROM employees
ORDER BY id;
```

```
+-------+-------+--------+-----------+-----------+
| name  | dept  | salary | dept_avg  | diff      |
+-------+-------+--------+-----------+-----------+
| An    | eng   |   3000 | 2500.0000 |  500.0000 |
| Bình  | eng   |   2500 | 2500.0000 |    0.0000 |
| Chi   | eng   |   2500 | 2500.0000 |    0.0000 |
| Dũng  | eng   |   2000 | 2500.0000 | -500.0000 |
| Em    | sales |   2200 | 1933.3333 |  266.6667 |
| Giang | sales |   1800 | 1933.3333 | -133.3333 |
| Hà    | sales |   1800 | 1933.3333 | -133.3333 |
| Khoa  | ops   |   1500 | 1500.0000 |    0.0000 |
+-------+-------+--------+-----------+-----------+
```

Đọc `AVG(salary) OVER (PARTITION BY dept)` là: "trung bình `salary`, tính trên các dòng **cùng `dept`**
với dòng đang xét, rồi gắn kết quả vào dòng đang xét". Tám dòng vào, tám dòng ra. (`AVG` của cột
`INT` trả về `DECIMAL` với 4 chữ số thập phân, nên mới có `2500.0000`; chương 08 đã nói.)

### 2.2 Định nghĩa

*Window function* (hàm cửa sổ) là hàm tính cho **mỗi dòng** của kết quả một giá trị, dựa trên một
tập các dòng có liên quan tới dòng đó. Tài liệu MySQL dùng ba thuật ngữ, bạn sẽ gặp suốt chương:

- *Current row* (dòng hiện tại): dòng mà hàm đang tính giá trị cho.
- *Window* (cửa sổ): tập các dòng liên quan tới current row mà hàm được phép "nhìn thấy" khi tính.
- *Partition*: một nhóm dòng do `PARTITION BY` chia ra. Window của một dòng nằm gọn trong partition
  chứa dòng đó, không bao giờ nhìn sang partition khác.

Hình dung với câu `AVG(salary) OVER (PARTITION BY dept)` ở trên:

```
 dòng (đã chia theo dept)        window của dòng = cả partition       giá trị gắn vào dòng
 -----------------------------   ---------------------------------   ---------------------
 eng   An    3000  <- current    {An, Bình, Chi, Dũng}                AVG = 2500.0000
 eng   Bình  2500  <- current    {An, Bình, Chi, Dũng}                AVG = 2500.0000
 eng   Chi   2500                ...                                  2500.0000
 eng   Dũng  2000                                                     2500.0000
 ops   Khoa  1500                {Khoa}                               1500.0000
 sales Em    2200                {Em, Giang, Hà}                      1933.3333
 sales Giang 1800                                                     1933.3333
 sales Hà    1800                                                     1933.3333
```

Ở ví dụ này window của mọi dòng trong một partition đều giống nhau (cả partition). Từ mục 5 trở đi
bạn sẽ thấy window có thể khác nhau cho từng dòng: "các dòng từ đầu partition tới dòng hiện tại"
(running total), "hai dòng trước và dòng hiện tại" (trung bình trượt), "dòng ngay trước" (`LAG`).
Chính khả năng "nhìn sang dòng khác mà không gộp dòng" làm window function mạnh.

Cú pháp nhận diện: một window function **luôn có `OVER`** ngay sau lời gọi hàm. Cùng là `AVG(salary)`:

- Không có `OVER`: aggregate thường, gộp nhóm, cần `GROUP BY` (hoặc gộp cả bảng thành một dòng).
- Có `OVER (...)`: window function, không gộp dòng.

### 2.3 So sánh với GROUP BY

| Tiêu chí | `GROUP BY` + aggregate | Window function |
|---|---|---|
| Số dòng kết quả | Mỗi nhóm một dòng | Giữ nguyên số dòng đầu vào |
| Cột chi tiết (`name`) | Chỉ cột trong `GROUP BY`, cột phụ thuộc hàm, hoặc nằm trong aggregate | Dùng thoải mái |
| Nhiều cách chia nhóm trong một câu | Không, mỗi câu `SELECT` một `GROUP BY` | Có, mỗi `OVER` một cách chia |
| Thứ tự các dòng trong nhóm | Không có ý nghĩa với `SUM`, `AVG`... | Có ý nghĩa: `ORDER BY` trong `OVER` quyết định xếp hạng, cộng dồn, dòng trước, dòng sau |
| Chạy ở bước nào | `GROUP BY`, `HAVING` | Sau `HAVING`, trước `ORDER BY` và `LIMIT` (mục 4) |

Hai thứ không loại trừ nhau: một câu có thể vừa `GROUP BY` vừa có window function, khi đó window
function chạy trên các dòng **đã gộp** (mục 4.5).

### 2.4 Hỗ trợ trong các hệ quản trị

- MySQL có window function từ bản 8.0. MySQL 5.7 không có.
- PostgreSQL có từ bản 8.4 (2009), và hỗ trợ đầy đủ các tuỳ chọn frame của chuẩn SQL từ bản 11
  (mục 12).

⚠️ Code cũ viết cho MySQL 5.7 thường giả lập `ROW_NUMBER` bằng biến người dùng, kiểu
`@rn := @rn + 1` ngay trong câu `SELECT`. Đừng học theo:

- Tài liệu MySQL 8.4 ghi rõ việc gán biến người dùng trong câu lệnh khác `SET` chỉ còn được hỗ trợ để
  tương thích ngược và sẽ bị bỏ ở bản sau; MySQL 8.4 in cảnh báo (warning) "Setting user variables
  within expressions is deprecated..." khi gặp cách viết này.
- Tài liệu cũng ghi thứ tự đánh giá biểu thức có biến người dùng là *không xác định* (undefined).
  Kết quả đúng hay sai phụ thuộc vào plan mà optimizer chọn, nên có thể đang đúng rồi một ngày sai.

Có MySQL 8 thì dùng window function.

## 3. Mệnh đề OVER

### 3.1 Cú pháp tổng quát

Theo tài liệu MySQL 8.4, sau lời gọi hàm có hai cách viết `OVER`:

```
ham(...) OVER (window_spec)        -- định nghĩa window ngay tại chỗ
ham(...) OVER ten_window           -- dùng window đã đặt tên ở mệnh đề WINDOW (mục 9)

window_spec:
    [ten_window] [PARTITION BY ...] [ORDER BY ...] [frame]
```

Cả bốn phần trong `window_spec` đều tuỳ chọn:

```sql
ham(...) OVER (
    PARTITION BY dept               -- chia dòng thành các partition độc lập
    ORDER BY salary DESC            -- thứ tự các dòng TRONG mỗi partition
    ROWS BETWEEN 2 PRECEDING
             AND CURRENT ROW        -- frame: tập con của partition mà hàm nhìn thấy (mục 8)
)
```

Mục này nói về `OVER ()` rỗng, `PARTITION BY` và `ORDER BY`. Frame để dành tới mục 8, vì cần biết các
hàm trước đã.

### 3.2 OVER () rỗng: cả kết quả là một window

Không có gì trong ngoặc nghĩa là: một partition duy nhất chứa mọi dòng của kết quả, và mọi dòng đều
nhìn thấy tất cả. Dùng khi cần "tổng của cả bảng" đặt cạnh từng dòng, ví dụ tỉ lệ phần trăm:

```sql
SELECT name, salary,
       SUM(salary) OVER ()                           AS total_payroll,
       ROUND(100 * salary / SUM(salary) OVER (), 1)  AS pct_of_total
FROM employees
ORDER BY id;
```

```
+-------+--------+---------------+--------------+
| name  | salary | total_payroll | pct_of_total |
+-------+--------+---------------+--------------+
| An    |   3000 |         17300 |         17.3 |
| Bình  |   2500 |         17300 |         14.5 |
| Chi   |   2500 |         17300 |         14.5 |
| Dũng  |   2000 |         17300 |         11.6 |
| Em    |   2200 |         17300 |         12.7 |
| Giang |   1800 |         17300 |         10.4 |
| Hà    |   1800 |         17300 |         10.4 |
| Khoa  |   1500 |         17300 |          8.7 |
+-------+--------+---------------+--------------+
```

Lưu ý cụm `SUM(salary) OVER ()` được dùng như một giá trị bình thường bên trong biểu thức
`100 * salary / ...`. Window function là một biểu thức, ghép với toán tử và hàm khác được.

### 3.3 PARTITION BY: chia thành các nhóm độc lập

`PARTITION BY` chia các dòng thành các partition theo giá trị của một hoặc nhiều biểu thức; hàm tính
riêng cho từng partition, như thể mỗi partition là một bảng riêng. Không có `PARTITION BY` thì cả kết
quả là một partition.

```sql
SELECT name, dept, salary,
       COUNT(*)    OVER (PARTITION BY dept) AS dept_size,
       SUM(salary) OVER (PARTITION BY dept) AS dept_total,
       SUM(salary) OVER ()                  AS company_total
FROM employees
ORDER BY id;
```

```
+-------+-------+--------+-----------+------------+---------------+
| name  | dept  | salary | dept_size | dept_total | company_total |
+-------+-------+--------+-----------+------------+---------------+
| An    | eng   |   3000 |         4 |      10000 |         17300 |
| Bình  | eng   |   2500 |         4 |      10000 |         17300 |
| Chi   | eng   |   2500 |         4 |      10000 |         17300 |
| Dũng  | eng   |   2000 |         4 |      10000 |         17300 |
| Em    | sales |   2200 |         3 |       5800 |         17300 |
| Giang | sales |   1800 |         3 |       5800 |         17300 |
| Hà    | sales |   1800 |         3 |       5800 |         17300 |
| Khoa  | ops   |   1500 |         1 |       1500 |         17300 |
+-------+-------+--------+-----------+------------+---------------+
```

Một câu có ba window với ba cách chia khác nhau: điều `GROUP BY` không làm được.

Vài chi tiết:

- Chia theo nhiều cột: `PARTITION BY dept, YEAR(hired_at)` nghĩa là mỗi cặp (phòng, năm) là một
  partition.
- Chuẩn SQL chỉ cho viết tên cột sau `PARTITION BY`. MySQL mở rộng cho viết cả biểu thức, ví dụ
  `PARTITION BY HOUR(ts)` (tài liệu MySQL lấy đúng ví dụ này). PostgreSQL cũng nhận biểu thức.
- ⚠️ Đừng nhầm với *table partitioning* (chia một bảng lớn thành nhiều phần lưu trữ riêng, chương 23).
  Tài liệu MySQL nhắc riêng điều này: hai khái niệm trùng chữ "partition" nhưng không liên quan gì nhau.

### 3.4 ORDER BY trong OVER: thứ tự bên trong partition

`ORDER BY` đặt trong `OVER` quyết định thứ tự các dòng **bên trong mỗi partition** khi hàm xử lý
chúng. Nó cần cho mọi hàm mà "thứ tự" có nghĩa: xếp hạng, dòng trước dòng sau, cộng dồn.

```sql
SELECT id, name, dept, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC, id)                   AS rn_company,
       ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC, id) AS rn_in_dept
FROM employees
ORDER BY id;
```

```
+----+-------+-------+--------+------------+------------+
| id | name  | dept  | salary | rn_company | rn_in_dept |
+----+-------+-------+--------+------------+------------+
|  1 | An    | eng   |   3000 |          1 |          1 |
|  2 | Bình  | eng   |   2500 |          2 |          2 |
|  3 | Chi   | eng   |   2500 |          3 |          3 |
|  4 | Dũng  | eng   |   2000 |          5 |          4 |
|  5 | Em    | sales |   2200 |          4 |          1 |
|  6 | Giang | sales |   1800 |          6 |          2 |
|  7 | Hà    | sales |   1800 |          7 |          3 |
|  8 | Khoa  | ops   |   1500 |          8 |          1 |
+----+-------+-------+--------+------------+------------+
```

`ROW_NUMBER()` đánh số 1, 2, 3... theo thứ tự của `ORDER BY` trong `OVER` (mục 5.1). Để ý ba điều:

1. Hai window trong cùng một câu có thứ tự khác nhau: `rn_company` sắp cả công ty theo lương,
   `rn_in_dept` sắp riêng từng phòng và đếm lại từ 1 khi sang phòng mới.
2. **`ORDER BY` trong `OVER` không quyết định thứ tự in ra.** Kết quả trên in theo `id` vì câu có
   `ORDER BY id` ở cuối. Tài liệu MySQL viết rõ: `ORDER BY` trong định nghĩa window chỉ áp dụng bên
   trong từng partition; muốn sắp cả kết quả thì phải có `ORDER BY` ở cấp câu truy vấn. ⚠️ Thiếu
   `ORDER BY` cuối câu thì thứ tự dòng in ra là không đảm bảo, dù trên máy bạn "trông như đã sắp".
3. `id` được thêm sau `salary DESC` làm *tie-breaker* (tiêu chí phá hoà). Lý do ở ngay dưới.

Các dòng bằng nhau theo `ORDER BY` của window được gọi là *peers* (đồng hạng, ngang hàng). Nếu chỉ
viết `ORDER BY salary DESC`, Bình và Chi (cùng 2500) là peers. Đây là khái niệm quan trọng nhất của
chương, vì mỗi nhóm hàm đối xử với peers theo một cách:

- `ROW_NUMBER` cho peers các số **khác nhau**, nhưng ai nhận số nhỏ hơn là **không xác định**
  (*nondeterministic*): chạy lại, đổi plan, đổi version có thể đổi.
- `RANK`, `DENSE_RANK` cho peers **cùng hạng** (mục 5.2).
- Frame mặc định khi có `ORDER BY` coi peers là **một khối**: cộng dồn tới dòng hiện tại là cộng luôn
  mọi peer của nó (mục 8.4).

Thêm `id` (khoá chính, không trùng) vào cuối `ORDER BY` thì không còn hai dòng nào là peers, mọi thứ
trở nên xác định.

Các quy tắc khác của `ORDER BY` trong `OVER`, theo tài liệu MySQL:

- Mặc định `ASC`. NULL đứng đầu khi sắp tăng dần, đứng cuối khi sắp giảm dần. MySQL không có cú pháp
  `NULLS FIRST` / `NULLS LAST` (PostgreSQL có, mục 12).
- Không có `ORDER BY` thì các dòng trong partition không có thứ tự nào, và **mọi dòng đều là peers
  của nhau**. Hệ quả: `ROW_NUMBER() OVER (PARTITION BY dept)` đánh số tuỳ ý; `RANK()` không có
  `ORDER BY` thì mọi dòng hạng 1.
- Không viết được số thứ tự cột kiểu `ORDER BY 2` trong window; MySQL báo lỗi 3592 ("ORDER BY or
  PARTITION BY uses legacy position indication which is not supported, use expression").

## 4. Window function chạy ở bước nào của câu SELECT

### 4.1 Vị trí trong thứ tự thực thi logic

Chương 05 và 08 đã có thứ tự thực thi logic của `SELECT`. Thêm window function vào:

```
1. FROM / JOIN / ON      tạo tập dòng
2. WHERE                 lọc từng dòng
3. GROUP BY              gom nhóm
4. HAVING                lọc nhóm
5. Window function       tính mọi OVER(...)        <- ở đây
6. SELECT                các biểu thức còn lại, alias, DISTINCT
7. ORDER BY              sắp xếp kết quả
8. LIMIT / OFFSET        cắt
```

Tài liệu MySQL 8.4 nói đúng ý này: các dòng mà window function làm việc là kết quả của `FROM` sau khi
qua `WHERE`, `GROUP BY`, `HAVING`; việc tính window diễn ra trước `ORDER BY`, `LIMIT` và
`SELECT DISTINCT`. Và vì thế window function **chỉ được viết ở danh sách `SELECT` và mệnh đề
`ORDER BY`** (PostgreSQL cùng quy tắc).

Từ vị trí số 5 này suy ra được hầu hết các quy tắc và cạm bẫy của chương. Lần lượt từng cái.

### 4.2 Không dùng trong WHERE, GROUP BY, HAVING

Ở bước 2 (`WHERE`) window function chưa được tính, nên không thể lọc theo nó:

```sql
SELECT id, name, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn
FROM employees
WHERE ROW_NUMBER() OVER (ORDER BY salary DESC, id) <= 3;
-- ERROR 3593 (HY000): You cannot use the window function 'row_number' in this context.'
```

Dùng alias cũng không được, vì alias của `SELECT` chưa tồn tại ở bước `WHERE` (chương 05):

```sql
SELECT id, name, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn
FROM employees
WHERE rn <= 3;
-- ERROR 1054 (42S22): Unknown column 'rn' in 'where clause'
```

MySQL vốn cho `HAVING` tham chiếu alias của `SELECT` (một mở rộng riêng, chương 08), nhưng riêng alias
chứa window function thì bị chặn, vì `HAVING` (bước 4) cũng chạy trước window:

```sql
SELECT id, name, ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn
FROM employees
HAVING rn <= 3;
-- ERROR 3594 (HY000): You cannot use the alias 'rn' of an expression containing a window
-- function in this context.'
```

(Dấu `'` thừa ở cuối hai thông báo lỗi 3593, 3594 có thật trong chuỗi thông báo của MySQL, không phải
lỗi đánh máy.)

### 4.3 Muốn lọc theo kết quả window function: thêm một tầng

Cách duy nhất trong MySQL và PostgreSQL: tính window function ở tầng trong (CTE hoặc derived table),
lọc ở tầng ngoài. Ví dụ người lương cao nhất mỗi phòng:

```sql
WITH ranked AS (
  SELECT id, name, dept, salary,
         ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC, id) AS rn
  FROM employees
)
SELECT dept, name, salary
FROM ranked
WHERE rn = 1
ORDER BY dept;
```

```
+-------+------+--------+
| dept  | name | salary |
+-------+------+--------+
| eng   | An   |   3000 |
| ops   | Khoa |   1500 |
| sales | Em   |   2200 |
+-------+------+--------+
```

Viết bằng derived table cũng được, kết quả như nhau:

```sql
SELECT dept, name, salary
FROM (
  SELECT id, name, dept, salary,
         ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC, id) AS rn
  FROM employees
) AS ranked
WHERE rn = 1
ORDER BY dept;
```

Tầng ngoài nhìn tầng trong như một bảng bình thường có cột `rn`, nên `WHERE rn = 1` hợp lệ. Mẫu "tính
ở trong, lọc ở ngoài" này là nền của gần như mọi bài ở mục 11.

Một số hệ quản trị khác (Snowflake, DuckDB, BigQuery, Teradata...) có mệnh đề `QUALIFY` để lọc kết quả
window function ngay trong một tầng. PostgreSQL 18 không có `QUALIFY`. Tài liệu MySQL 8.4 cũng không
mô tả mệnh đề này; mã nguồn MySQL 8.4 có phân tích cú pháp `QUALIFY` nhưng chỉ cho chạy khi bật
*hypergraph optimizer*, thứ mà bản phát hành thông thường không cho bật (mặc định chỉ bản build debug có), nên
trên MySQL 8.4 bạn cài từ Docker hay gói cài đặt, câu có `QUALIFY` sẽ báo lỗi ("'QUALIFY clause' can be
used only if the hypergraph optimizer is enabled."). Gặp lời giải dùng
`QUALIFY` trên mạng thì đổi về mẫu hai tầng ở trên.

### 4.4 WHERE lọc trước khi window chạy: đặt điều kiện ở tầng nào cho kết quả khác nhau

Vì `WHERE` chạy trước, những dòng bị `WHERE` loại thì window function **không bao giờ nhìn thấy**. Cùng
điều kiện `dept = 'sales'`, đặt ở hai tầng khác nhau là hai câu hỏi khác nhau:

```sql
-- (a) Lọc trước rồi xếp hạng: "hạng lương TRONG phòng sales"
SELECT name, salary, RANK() OVER (ORDER BY salary DESC) AS rnk
FROM employees
WHERE dept = 'sales'
ORDER BY rnk, name;
```

```
+-------+--------+-----+
| name  | salary | rnk |
+-------+--------+-----+
| Em    |   2200 |   1 |
| Giang |   1800 |   2 |
| Hà    |   1800 |   2 |
+-------+--------+-----+
```

```sql
-- (b) Xếp hạng cả công ty rồi mới lọc: "người phòng sales đứng hạng mấy trong CÔNG TY"
WITH r AS (
  SELECT name, dept, salary, RANK() OVER (ORDER BY salary DESC) AS rnk
  FROM employees
)
SELECT name, salary, rnk
FROM r
WHERE dept = 'sales'
ORDER BY rnk, name;
```

```
+-------+--------+-----+
| name  | salary | rnk |
+-------+--------+-----+
| Em    |   2200 |   4 |
| Giang |   1800 |   6 |
| Hà    |   1800 |   6 |
+-------+--------+-----+
```

Ở (b), trên Em còn An (3000), Bình và Chi (2500) nên Em hạng 4. (`RANK` cho đồng hạng và nhảy số,
mục 5.2.) Không câu nào sai; sai là khi bạn muốn câu này mà viết câu kia. Mỗi lần đặt điều kiện lọc,
tự hỏi: "dòng này có cần được tính vào window của dòng khác không?"

Có một trường hợp đặt trong hay ngoài đều cho cùng kết quả: điều kiện chỉ dính tới cột của
`PARTITION BY`. Ví dụ với `ROW_NUMBER() OVER (PARTITION BY dept ...)`, lọc `dept = 'eng'` ở trong hay
ngoài đều ra cùng số thứ tự, vì bỏ nguyên một partition không ảnh hưởng tới các partition còn lại. Khi
đó nên đặt ở tầng trong cho đỡ tính thừa (mục 10.2).

### 4.5 Window function trên kết quả GROUP BY

Window chạy sau `GROUP BY` (bước 5 sau bước 3), nên trong câu có `GROUP BY`, window function làm việc
trên các dòng **đã gộp**, và tham số của nó được phép chứa aggregate. Ví dụ tỉ trọng quỹ lương mỗi
phòng và xếp hạng phòng:

```sql
SELECT dept,
       SUM(salary)                                             AS dept_total,
       SUM(SUM(salary)) OVER ()                                AS company_total,
       ROUND(100 * SUM(salary) / SUM(SUM(salary)) OVER (), 1)  AS pct,
       RANK() OVER (ORDER BY SUM(salary) DESC)                 AS rnk
FROM employees
GROUP BY dept
ORDER BY dept_total DESC;
```

```
+-------+------------+---------------+------+-----+
| dept  | dept_total | company_total | pct  | rnk |
+-------+------------+---------------+------+-----+
| eng   |      10000 |         17300 | 57.8 |   1 |
| sales |       5800 |         17300 | 33.5 |   2 |
| ops   |       1500 |         17300 |  8.7 |   3 |
+-------+------------+---------------+------+-----+
```

Đọc `SUM(SUM(salary)) OVER ()` từ trong ra ngoài:

- `SUM(salary)` bên trong là aggregate của `GROUP BY dept`: tổng lương mỗi phòng (10000, 5800, 1500).
- `SUM(...) OVER ()` bên ngoài là window function, chạy trên ba dòng đã gộp: cộng ba tổng phòng thành
  17300 và gắn vào cả ba dòng.

Thứ tự ngược lại thì không được: aggregate không thể chứa window function (`SUM(ROW_NUMBER() OVER
(...))` là lỗi), vì aggregate chạy trước. Tài liệu PostgreSQL nói gọn: window function chạy sau
aggregate thường, nên đặt aggregate trong tham số window function thì được, ngược lại thì không. Cần
gộp kết quả của window function thì lại thêm một tầng (mục 4.3).

### 4.6 DISTINCT và LIMIT chạy sau window

`DISTINCT` (bước 6) và `LIMIT` (bước 8) đều chạy sau khi window đã tính xong trên **toàn bộ** các dòng
qua được `WHERE`. Hai hệ quả thực tế.

Hệ quả 1, đếm tổng số dòng cho phân trang: `COUNT(*) OVER ()` trả về số dòng thoả `WHERE` **trước khi
`LIMIT` cắt**, nên một câu lấy được cả trang dữ liệu lẫn tổng số dòng:

```sql
SELECT id, name, salary, COUNT(*) OVER () AS total_rows
FROM employees
WHERE salary >= 2000
ORDER BY salary DESC, id
LIMIT 3;
```

```
+----+------+--------+------------+
| id | name | salary | total_rows |
+----+------+--------+------------+
|  1 | An   |   3000 |          5 |
|  2 | Bình |   2500 |          5 |
|  3 | Chi  |   2500 |          5 |
+----+------+--------+------------+
```

Có 5 người lương từ 2000 trở lên (An, Bình, Chi, Em, Dũng), trang đầu lấy 3. ⚠️ Cái giá: để biết tổng,
MySQL phải đọc **hết** mọi dòng thoả `WHERE`, không dừng sớm sau 3 dòng như một câu `ORDER BY ...
LIMIT 3` có index phù hợp. Trên bảng lớn, câu này có thể chậm hơn hẳn hai câu riêng (một câu lấy
trang, một câu `COUNT(*)` có thể dùng index). Đo trước khi dùng.

Hệ quả 2, `DISTINCT` không khử được các dòng mà window function làm cho khác nhau:

```sql
-- DISTINCT chạy sau window: khử được, vì ba dòng sales có cùng (dept, dept_size)
SELECT DISTINCT dept, COUNT(*) OVER (PARTITION BY dept) AS dept_size
FROM employees
ORDER BY dept;
```

```
+-------+-----------+
| dept  | dept_size |
+-------+-----------+
| eng   |         4 |
| ops   |         1 |
| sales |         3 |
+-------+-----------+
```

Ngược lại, `SELECT DISTINCT dept, ROW_NUMBER() OVER (...)` vẫn ra đủ 8 dòng, vì số thứ tự làm mọi dòng
khác nhau. Câu trên chỉ để minh hoạ thứ tự thực thi; viết thật thì dùng `GROUP BY dept` cho rõ nghĩa.

## 5. Hàm xếp hạng: ROW_NUMBER, RANK, DENSE_RANK, NTILE

Đây là nhóm hàm chỉ dùng được như window function (tài liệu MySQL gọi là *nonaggregate window
function*, bắt buộc có `OVER`). Chúng không nhận tham số cột: mọi thông tin cần để xếp hạng nằm trong
`PARTITION BY` và `ORDER BY` của `OVER`.

### 5.1 ROW_NUMBER: đánh số thứ tự

`ROW_NUMBER()` trả về số thứ tự của dòng trong partition, từ 1 tới số dòng của partition, theo thứ
tự của `ORDER BY` trong `OVER`. Bạn đã thấy nó ở mục 3.4 và 4.3. Ba điều cần nhớ:

- Peers (dòng bằng nhau theo `ORDER BY`) vẫn nhận số **khác nhau**; ai nhận số nào giữa các peers là
  không xác định. Không có `ORDER BY` thì cả việc đánh số là không xác định (tài liệu MySQL ghi rõ:
  *nondeterministic*).
- Vì thế khi dùng `ROW_NUMBER` để chọn đúng N dòng, hãy thêm tie-breaker là cột không trùng (khoá
  chính) vào cuối `ORDER BY`, để chạy lần nào cũng ra cùng kết quả.
- Kiểu trả về trong MySQL là số nguyên **không dấu** `BIGINT UNSIGNED` (mã nguồn MySQL đặt cờ
  unsigned cho `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`). Điều này gây bẫy khi đem đi trừ, xem mục
  11.5.

Dùng `ROW_NUMBER` khi cần: lấy đúng N dòng mỗi nhóm, khử trùng (giữ dòng số 1 của mỗi nhóm trùng),
đánh số để phân trang trong nhóm.

### 5.2 RANK và DENSE_RANK: xếp hạng có đồng hạng

Cả hai cho peers **cùng một hạng**. Khác nhau ở hạng của nhóm đứng sau:

```sql
SELECT dept, name, salary,
       ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC, id) AS rn,
       RANK()       OVER (PARTITION BY dept ORDER BY salary DESC)     AS rnk,
       DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC)     AS drnk
FROM employees
ORDER BY dept, salary DESC, id;
```

```
+-------+-------+--------+----+-----+------+
| dept  | name  | salary | rn | rnk | drnk |
+-------+-------+--------+----+-----+------+
| eng   | An    |   3000 |  1 |   1 |    1 |
| eng   | Bình  |   2500 |  2 |   2 |    2 |
| eng   | Chi   |   2500 |  3 |   2 |    2 |
| eng   | Dũng  |   2000 |  4 |   4 |    3 |
| ops   | Khoa  |   1500 |  1 |   1 |    1 |
| sales | Em    |   2200 |  1 |   1 |    1 |
| sales | Giang |   1800 |  2 |   2 |    2 |
| sales | Hà    |   1800 |  3 |   2 |    2 |
+-------+-------+--------+----+-----+------+
```

Nhìn dòng Dũng:

- `RANK` = 4: có ba người đứng trên Dũng (An, Bình, Chi), nên Dũng hạng 3 + 1 = 4. Hạng 3 bị "bỏ
  trống". Công thức: hạng = 1 + số dòng đứng **hẳn** trước (lương cao hơn hẳn). Đây là cách xếp hạng
  trong thi đấu: hai người đồng hạng nhì thì không có ai hạng ba.
- `DENSE_RANK` = 3: phía trên Dũng có hai **mức** lương khác nhau (3000, 2500), nên Dũng ở mức thứ ba.
  Công thức: hạng = 1 + số giá trị khác nhau đứng trước. Hạng liên tục, không bỏ số.

| Hàm | Peers nhận | Sau một nhóm peers | Dãy hạng ví dụ | Dùng khi |
|---|---|---|---|---|
| `ROW_NUMBER()` | Số khác nhau (thứ tự giữa peers không xác định) | Liên tục | 1, 2, 3, 4 | Cần đúng N dòng, khử trùng |
| `RANK()` | Cùng hạng | Nhảy số | 1, 2, 2, 4 | Bảng xếp hạng thi đấu, "top N kể cả đồng hạng" |
| `DENSE_RANK()` | Cùng hạng | Không nhảy | 1, 2, 2, 3 | "Mức lương cao thứ N", "N mức giá cao nhất" |

⚠️ Đừng thêm tie-breaker vào `ORDER BY` của `RANK` / `DENSE_RANK` nếu bạn muốn đồng hạng. Viết
`RANK() OVER (ORDER BY salary DESC, id)` thì không còn peers nào, `RANK` trở thành giống hệt
`ROW_NUMBER`. Tie-breaker là cho `ROW_NUMBER`; với `RANK` và `DENSE_RANK`, cột trong `ORDER BY` chính
là định nghĩa của "bằng nhau".

⚠️ Thiếu `ORDER BY` trong `OVER` thì mọi dòng là peers, `RANK()` và `DENSE_RANK()` trả về 1 cho tất
cả. Không có lỗi nào báo cho bạn biết.

### 5.3 NTILE: chia thành N nhóm gần bằng nhau

`NTILE(N)` chia các dòng của partition (đã sắp theo `ORDER BY`) thành N nhóm (*bucket*) có số dòng gần
bằng nhau, và trả về số thứ tự nhóm (1 tới N) của dòng hiện tại. Dùng để chia khách hàng thành 4 nhóm
theo chi tiêu (*quartile*), 10 nhóm (*decile*)...

```sql
SELECT name, salary, NTILE(3) OVER (ORDER BY salary DESC, id) AS bucket
FROM employees
ORDER BY salary DESC, id;
```

```
+-------+--------+--------+
| name  | salary | bucket |
+-------+--------+--------+
| An    |   3000 |      1 |
| Bình  |   2500 |      1 |
| Chi   |   2500 |      1 |
| Em    |   2200 |      2 |
| Dũng  |   2000 |      2 |
| Giang |   1800 |      2 |
| Hà    |   1800 |      3 |
| Khoa  |   1500 |      3 |
+-------+--------+--------+
```

8 dòng chia 3 nhóm: 8 = 3 + 3 + 2. Các nhóm chênh nhau nhiều nhất một dòng, và những dòng dư được
dồn cho các nhóm đầu (ví dụ trong tài liệu MySQL: 9 dòng với `NTILE(4)` ra các nhóm 3, 2, 2, 2 dòng).
Partition có ít dòng hơn N thì chỉ các nhóm đầu có dòng.

⚠️ `NTILE` chia theo **số dòng**, không quan tâm giá trị: Giang và Hà cùng lương 1800 nhưng rơi vào
hai nhóm khác nhau. Nếu "cùng giá trị phải cùng nhóm" là yêu cầu nghiệp vụ, `NTILE` không đáp ứng
được; cần tự định nghĩa ngưỡng (ví dụ theo `PERCENT_RANK` ở mục dưới).

Tham số N theo tài liệu MySQL: phải là số nguyên dương viết thẳng (literal), hoặc dấu `?` của
prepared statement, hoặc biến người dùng, hoặc biến cục bộ trong stored routine; không được là
`NULL`, không được là một cột hay biểu thức tính theo từng dòng.

### 5.4 PERCENT_RANK và CUME_DIST: vị trí tương đối

Hai hàm này trả về số thực (`DOUBLE`) từ 0 tới 1, cho biết dòng hiện tại đứng ở đâu trong partition:

- `PERCENT_RANK()` = `(rank - 1) / (số dòng của partition - 1)`, với `rank` là giá trị của `RANK()`.
  Đọc là: trong những người **khác**, bao nhiêu phần đứng hẳn trước mình. Dòng hạng 1 luôn là 0.
- `CUME_DIST()` = số dòng đứng trước hoặc là peer của dòng hiện tại / số dòng của partition. Với
  `ORDER BY salary` (tăng dần), đọc là: bao nhiêu phần trăm người có lương **nhỏ hơn hoặc bằng** mình.

```sql
SELECT dept, name, salary,
       RANK()         OVER w AS rnk,
       PERCENT_RANK() OVER w AS pct_rank,
       CUME_DIST()    OVER w AS cume
FROM employees
WINDOW w AS (PARTITION BY dept ORDER BY salary)   -- đặt tên window để khỏi viết lại 3 lần (mục 9)
ORDER BY dept, salary, id;
```

```
+-------+-------+--------+-----+--------------------+--------------------+
| dept  | name  | salary | rnk | pct_rank           | cume               |
+-------+-------+--------+-----+--------------------+--------------------+
| eng   | Dũng  |   2000 |   1 |                  0 |               0.25 |
| eng   | Bình  |   2500 |   2 | 0.3333333333333333 |               0.75 |
| eng   | Chi   |   2500 |   2 | 0.3333333333333333 |               0.75 |
| eng   | An    |   3000 |   4 |                  1 |                  1 |
| ops   | Khoa  |   1500 |   1 |                  0 |                  1 |
| sales | Giang |   1800 |   1 |                  0 | 0.6666666666666666 |
| sales | Hà    |   1800 |   1 |                  0 | 0.6666666666666666 |
| sales | Em    |   2200 |   3 |                  1 |                  1 |
+-------+-------+--------+-----+--------------------+--------------------+
```

Kiểm tra dòng Bình: `RANK` = 2, phòng có 4 người, `PERCENT_RANK` = (2 - 1) / (4 - 1) = 1/3; có 3 người
lương ≤ 2500 (Dũng, Bình, Chi) nên `CUME_DIST` = 3/4 = 0.75. Partition chỉ có một dòng (Khoa) thì
`PERCENT_RANK` là 0 và `CUME_DIST` là 1.

Ứng dụng: "nhân viên thuộc nhóm 10% lương cao nhất phòng" là `CUME_DIST() OVER (PARTITION BY dept
ORDER BY salary DESC) <= 0.1` (lọc ở tầng ngoài, như mục 4.3). Khác `NTILE`, peers luôn nhận cùng giá
trị, nên người cùng lương không bị tách nhóm.

### 5.5 Tóm tắt nhóm hàm xếp hạng

| Hàm | Trả về | Peers | Cần `ORDER BY` để có nghĩa |
|---|---|---|---|
| `ROW_NUMBER()` | 1, 2, 3... (`BIGINT UNSIGNED`) | Số khác nhau, thứ tự không xác định | Có |
| `RANK()` | Hạng có nhảy số (`BIGINT UNSIGNED`) | Cùng hạng | Có |
| `DENSE_RANK()` | Hạng liên tục (`BIGINT UNSIGNED`) | Cùng hạng | Có |
| `NTILE(N)` | Số nhóm 1..N (`BIGINT UNSIGNED`) | Có thể bị tách nhóm | Có |
| `PERCENT_RANK()` | 0..1 (`DOUBLE`) | Cùng giá trị | Có |
| `CUME_DIST()` | 0..1 (`DOUBLE`) | Cùng giá trị | Có |

Cả sáu hàm đều **bỏ qua frame** (mục 8): chúng luôn tính trên toàn bộ partition.

## 6. Hàm lấy giá trị theo vị trí: LAG, LEAD, FIRST_VALUE, LAST_VALUE, NTH_VALUE

Nhóm này trả về **giá trị của một dòng khác** trong partition: dòng trước, dòng sau, dòng đầu, dòng
cuối, dòng thứ N. Chúng thay cho những self-join rườm rà kiểu "nối bảng với chính nó, lệch một dòng".

### 6.1 LAG và LEAD: dòng trước, dòng sau

Cú pháp theo tài liệu MySQL:

```
LAG(expr [, N [, default]])  OVER (...)   -- giá trị expr ở dòng đứng TRƯỚC dòng hiện tại N dòng
LEAD(expr [, N [, default]]) OVER (...)   -- giá trị expr ở dòng đứng SAU dòng hiện tại N dòng
```

- `N` mặc định là 1. Nếu không có dòng như vậy (đầu hoặc cuối partition), hàm trả về `default`, mặc
  định là `NULL`.
- `N` phải là số nguyên không âm viết thẳng, hoặc `?`, hoặc biến người dùng, hoặc biến cục bộ của
  stored routine; không được âm, không được `NULL`. `N = 0` nghĩa là chính dòng hiện tại.
- Cần `ORDER BY` trong `OVER` thì "trước" và "sau" mới có nghĩa.

So doanh thu mỗi ngày với dòng trước và dòng sau:

```sql
SELECT day, revenue,
       LAG(revenue)       OVER (ORDER BY day) AS prev_revenue,
       LEAD(revenue)      OVER (ORDER BY day) AS next_revenue,
       LAG(revenue, 2, 0) OVER (ORDER BY day) AS revenue_2_rows_back
FROM daily_sales
ORDER BY day;
```

```
+------------+---------+--------------+--------------+---------------------+
| day        | revenue | prev_revenue | next_revenue | revenue_2_rows_back |
+------------+---------+--------------+--------------+---------------------+
| 2026-04-01 |     100 |         NULL |          120 |                   0 |
| 2026-04-02 |     120 |          100 |           80 |                   0 |
| 2026-04-03 |      80 |          120 |          150 |                 100 |
| 2026-04-05 |     150 |           80 |          130 |                 120 |
| 2026-04-06 |     130 |          150 |         NULL |                  80 |
+------------+---------+--------------+--------------+---------------------+
```

Dòng đầu không có dòng trước nên `prev_revenue` là `NULL`; dòng cuối không có dòng sau nên
`next_revenue` là `NULL`; `LAG(revenue, 2, 0)` trả về `0` (giá trị default tự chọn) cho hai dòng đầu.

Tính mức tăng giảm so với dòng trước, kể cả phần trăm:

```sql
SELECT day, revenue,
       revenue - LAG(revenue) OVER (ORDER BY day) AS diff,
       ROUND(100 * (revenue - LAG(revenue) OVER (ORDER BY day))
                 / LAG(revenue) OVER (ORDER BY day), 1) AS pct_change
FROM daily_sales
ORDER BY day;
```

```
+------------+---------+------+------------+
| day        | revenue | diff | pct_change |
+------------+---------+------+------------+
| 2026-04-01 |     100 | NULL |       NULL |
| 2026-04-02 |     120 |   20 |       20.0 |
| 2026-04-03 |      80 |  -40 |      -33.3 |
| 2026-04-05 |     150 |   70 |       87.5 |
| 2026-04-06 |     130 |  -20 |      -13.3 |
+------------+---------+------+------------+
```

⚠️ Nhìn dòng 2026-04-05: nó được so với 2026-04-03, vì ngày 04 không có dòng. `LAG` lấy **dòng liền
trước** theo thứ tự sắp xếp, không phải "ngày hôm qua". Nếu báo cáo ghi cột này là "so với hôm qua"
thì số 87.5% là sai. Cách sửa ở mục 11.4.

`LAG`/`LEAD` cũng tôn trọng `PARTITION BY`: sang partition mới là không còn "dòng trước". Ví dụ khoảng
cách lương với người xếp ngay trên trong cùng phòng:

```sql
SELECT dept, name, salary,
       LAG(salary) OVER (PARTITION BY dept ORDER BY salary DESC, id)          AS above_salary,
       LAG(salary) OVER (PARTITION BY dept ORDER BY salary DESC, id) - salary AS gap
FROM employees
ORDER BY dept, salary DESC, id;
```

```
+-------+-------+--------+--------------+------+
| dept  | name  | salary | above_salary | gap  |
+-------+-------+--------+--------------+------+
| eng   | An    |   3000 |         NULL | NULL |
| eng   | Bình  |   2500 |         3000 |  500 |
| eng   | Chi   |   2500 |         2500 |    0 |
| eng   | Dũng  |   2000 |         2500 |  500 |
| ops   | Khoa  |   1500 |         NULL | NULL |
| sales | Em    |   2200 |         NULL | NULL |
| sales | Giang |   1800 |         2200 |  400 |
| sales | Hà    |   1800 |         1800 |    0 |
+-------+-------+--------+--------------+------+
```

Em là người đầu tiên của partition `sales` nên `above_salary` là `NULL`, dù dòng in ngay trên Em
trong kết quả là Khoa của phòng `ops`.

### 6.2 FIRST_VALUE, LAST_VALUE, NTH_VALUE: giá trị ở dòng đầu, cuối, thứ N của frame

```
FIRST_VALUE(expr)    OVER (...)   -- expr ở dòng ĐẦU của frame
LAST_VALUE(expr)     OVER (...)   -- expr ở dòng CUỐI của frame
NTH_VALUE(expr, N)   OVER (...)   -- expr ở dòng thứ N của frame (N nguyên dương); không có thì NULL
```

Chữ quan trọng là **frame**, không phải partition. Frame là phần của partition mà hàm được nhìn thấy
khi tính cho dòng hiện tại; mục 8 sẽ nói kỹ. Ở đây chỉ cần biết trước một điều: khi `OVER` có
`ORDER BY` mà không ghi frame, frame mặc định là "từ dòng đầu partition **tới dòng hiện tại** (và các
peer của nó)", **không** phải cả partition. Xem nó gây chuyện gì:

```sql
SELECT dept, name, salary,
       FIRST_VALUE(name)  OVER w AS top_paid,
       LAST_VALUE(name)   OVER w AS last_default,
       LAST_VALUE(name)   OVER (w ROWS BETWEEN UNBOUNDED PRECEDING
                                       AND UNBOUNDED FOLLOWING) AS lowest_paid,
       NTH_VALUE(name, 2) OVER w AS second_default
FROM employees
WINDOW w AS (PARTITION BY dept ORDER BY salary DESC, id)
ORDER BY dept, salary DESC, id;
```

```
+-------+-------+--------+----------+--------------+-------------+----------------+
| dept  | name  | salary | top_paid | last_default | lowest_paid | second_default |
+-------+-------+--------+----------+--------------+-------------+----------------+
| eng   | An    |   3000 | An       | An           | Dũng        | NULL           |
| eng   | Bình  |   2500 | An       | Bình         | Dũng        | Bình           |
| eng   | Chi   |   2500 | An       | Chi          | Dũng        | Bình           |
| eng   | Dũng  |   2000 | An       | Dũng         | Dũng        | Bình           |
| ops   | Khoa  |   1500 | Khoa     | Khoa         | Khoa        | NULL           |
| sales | Em    |   2200 | Em       | Em           | Hà          | NULL           |
| sales | Giang |   1800 | Em       | Giang        | Hà          | Giang          |
| sales | Hà    |   1800 | Em       | Hà           | Hà          | Giang          |
+-------+-------+--------+----------+--------------+-------------+----------------+
```

- `top_paid` đúng như mong đợi: dòng đầu của frame luôn là dòng đầu partition, tức người lương cao
  nhất phòng.
- `last_default` **không** phải người lương thấp nhất mà là... chính dòng hiện tại. Vì frame mặc định
  dừng ở dòng hiện tại, nên "dòng cuối của frame" là dòng hiện tại. Đây là cái bẫy nổi tiếng nhất của
  `LAST_VALUE`.
- `lowest_paid` ghi rõ frame là cả partition (`ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED
  FOLLOWING`) nên mới ra người lương thấp nhất. Cách khác thường gọn hơn: dùng `FIRST_VALUE` với
  `ORDER BY` đảo chiều (`ORDER BY salary ASC, id DESC`).
- `second_default` là `NULL` ở dòng đầu mỗi partition vì lúc đó frame mới có một dòng, chưa có "dòng
  thứ 2". Tài liệu MySQL có ví dụ y hệt hiện tượng này.

Cú pháp `OVER (w ROWS BETWEEN ...)` là "lấy window `w` rồi thêm frame"; quy tắc của nó ở mục 9.

### 6.3 NULL: chỉ có RESPECT NULLS, và cách lấy "giá trị gần nhất khác NULL"

Chuẩn SQL cho phép viết `LAG(val) IGNORE NULLS OVER (...)` để bỏ qua các dòng NULL. MySQL 8.4 chỉ hỗ
trợ `RESPECT NULLS` (mặc định, tính cả NULL); viết `IGNORE NULLS` thì parser nhận nhưng báo lỗi
`ERROR 1235 (42000): This version of MySQL doesn't yet support 'IGNORE NULLS'`. Tương tự, `NTH_VALUE`
chỉ hỗ trợ `FROM FIRST`; `FROM LAST` báo lỗi (muốn đếm từ cuối thì đảo chiều `ORDER BY`). PostgreSQL
18 cũng chưa hỗ trợ hai tuỳ chọn này.

Bài toán hay gặp cần `IGNORE NULLS`: cảm biến thỉnh thoảng không gửi số liệu, muốn điền chỗ trống
bằng giá trị đo gần nhất trước đó (*forward fill*). `LAG` không làm được, vì nó trả về đúng dòng trước,
kể cả khi dòng đó là NULL:

```sql
SELECT t, val, LAG(val) OVER (ORDER BY t) AS prev_val
FROM readings
ORDER BY t;
```

```
+---+------+----------+
| t | val  | prev_val |
+---+------+----------+
| 1 |   10 |     NULL |
| 2 | NULL |       10 |
| 3 | NULL |     NULL |
| 4 |   15 |     NULL |
| 5 | NULL |       15 |
+---+------+----------+
```

Cách làm không cần `IGNORE NULLS`, dựa trên việc `COUNT(cột)` bỏ qua NULL (chương 08):

```sql
WITH g AS (
  SELECT t, val,
         COUNT(val) OVER (ORDER BY t ROWS UNBOUNDED PRECEDING) AS grp
  FROM readings
)
SELECT t, val, grp,
       MAX(val) OVER (PARTITION BY grp) AS last_known
FROM g
ORDER BY t;
```

```
+---+------+-----+------------+
| t | val  | grp | last_known |
+---+------+-----+------------+
| 1 |   10 |   1 |         10 |
| 2 | NULL |   1 |         10 |
| 3 | NULL |   1 |         10 |
| 4 |   15 |   2 |         15 |
| 5 | NULL |   2 |         15 |
+---+------+-----+------------+
```

Bước 1: `COUNT(val)` cộng dồn theo thời gian chỉ tăng ở những dòng có giá trị, nên mỗi giá trị khác
NULL "mở" một nhóm mới, và các dòng NULL phía sau nó mang cùng số nhóm. Bước 2: trong mỗi nhóm chỉ có
đúng một giá trị khác NULL (dòng mở nhóm), nên `MAX` của nhóm chính là giá trị đó. Nếu dòng đầu tiên
của bảng là NULL thì nó thuộc nhóm 0 và `last_known` là NULL, đúng nghĩa "chưa từng đo được".

Bước 1 và bước 2 phải tách thành hai tầng vì MySQL không cho lồng window function (`MAX(...) OVER
(PARTITION BY COUNT(val) OVER (...))` là lỗi). Mẫu "đánh dấu bằng window function, rồi dùng dấu đó
làm `PARTITION BY` ở tầng sau" còn gặp lại ở bài gaps and islands (mục 11.5).

## 7. Aggregate function dùng như window function

### 7.1 Hàm nào dùng được với OVER

Theo tài liệu MySQL 8.4, các aggregate sau nhận `OVER` và khi đó chạy như window function: `AVG`,
`BIT_AND`, `BIT_OR`, `BIT_XOR`, `COUNT`, `JSON_ARRAYAGG`, `JSON_OBJECTAGG`, `MAX`, `MIN`,
`STDDEV_POP` (cùng các tên khác `STDDEV`, `STD`), `STDDEV_SAMP`, `SUM`, `VAR_POP` (cùng `VARIANCE`),
`VAR_SAMP`. Cùng một hàm: có `OVER` là window function, không có `OVER` là aggregate thường.

Hai thứ **không** có:

- `GROUP_CONCAT` không nhận `OVER`. Cần gom chuỗi theo window thì dùng `JSON_ARRAYAGG(...) OVER (...)`,
  hoặc gom bằng `GROUP BY` ở một tầng riêng rồi `JOIN` lại.
- `DISTINCT` bên trong aggregate window: `COUNT(DISTINCT salary) OVER (PARTITION BY dept)` báo lỗi
  `ERROR 1235 (42000): This version of MySQL doesn't yet support '<window function>(DISTINCT ..)'`.
  PostgreSQL cũng không hỗ trợ.

Cần đếm số giá trị khác nhau trong partition mà vẫn giữ từng dòng, có một mẹo dùng hai `DENSE_RANK`
ngược chiều:

```sql
SELECT dept, name, salary,
       DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary)
     + DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) - 1 AS distinct_salaries
FROM employees
ORDER BY dept, salary DESC, id;
```

Phòng `eng` ra 3 ở mọi dòng (ba mức 3000, 2500, 2000), `sales` ra 2, `ops` ra 1. Lý do: `DENSE_RANK`
tăng dần cho biết có bao nhiêu mức lương ≤ lương của mình, giảm dần cho biết bao nhiêu mức ≥ lương
của mình; cộng lại thì mức của chính mình bị đếm hai lần, nên trừ 1. ⚠️ Mẹo này coi NULL là một giá
trị (các NULL là peers của nhau), còn `COUNT(DISTINCT ...)` thì bỏ qua NULL; cột có NULL thì phải
lọc hoặc trừ thêm. Cách chắc ăn hơn và dễ đọc hơn vẫn là `GROUP BY` ở tầng riêng rồi `JOIN`.

### 7.2 Chỉ số của nhóm đặt cạnh từng dòng

Đây là dạng dùng nhiều nhất: `OVER (PARTITION BY ...)` không có `ORDER BY`, frame là cả partition, hàm
cho cùng một giá trị cho mọi dòng trong partition (như mục 2.1, 3.3):

```sql
SELECT dept, name, salary,
       MAX(salary) OVER (PARTITION BY dept)                          AS dept_max,
       MAX(salary) OVER (PARTITION BY dept) - salary                 AS below_top,
       ROUND(100 * salary / SUM(salary) OVER (PARTITION BY dept), 1) AS pct_of_dept
FROM employees
ORDER BY dept, salary DESC, id;
```

```
+-------+-------+--------+----------+-----------+-------------+
| dept  | name  | salary | dept_max | below_top | pct_of_dept |
+-------+-------+--------+----------+-----------+-------------+
| eng   | An    |   3000 |     3000 |         0 |        30.0 |
| eng   | Bình  |   2500 |     3000 |       500 |        25.0 |
| eng   | Chi   |   2500 |     3000 |       500 |        25.0 |
| eng   | Dũng  |   2000 |     3000 |      1000 |        20.0 |
| ops   | Khoa  |   1500 |     1500 |         0 |       100.0 |
| sales | Em    |   2200 |     2200 |         0 |        37.9 |
| sales | Giang |   1800 |     2200 |       400 |        31.0 |
| sales | Hà    |   1800 |     2200 |       400 |        31.0 |
+-------+-------+--------+----------+-----------+-------------+
```

### 7.3 Thêm ORDER BY: running total (cộng dồn)

Thêm `ORDER BY` vào `OVER` của `SUM` thì mỗi dòng chỉ cộng các dòng **từ đầu partition tới nó**: đó
là *running total* (tổng luỹ kế, cộng dồn). Ví dụ số dư tài khoản sau từng giao dịch:

```sql
SELECT account, txn_date, id, amount,
       SUM(amount) OVER (PARTITION BY account
                         ORDER BY txn_date, id
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS balance
FROM transactions
ORDER BY account, txn_date, id;
```

```
+---------+------------+----+--------+---------+
| account | txn_date   | id | amount | balance |
+---------+------------+----+--------+---------+
| A       | 2026-03-01 |  1 |    100 |     100 |
| A       | 2026-03-02 |  2 |     50 |     150 |
| A       | 2026-03-02 |  3 |    -30 |     120 |
| A       | 2026-03-04 |  4 |     20 |     140 |
| B       | 2026-03-01 |  5 |    200 |     200 |
| B       | 2026-03-03 |  6 |    -50 |     150 |
+---------+------------+----+--------+---------+
```

- `PARTITION BY account`: mỗi tài khoản cộng dồn riêng, sang tài khoản B thì bắt đầu lại từ 0.
- `ORDER BY txn_date, id`: cộng theo thời gian; `id` phá hoà hai giao dịch cùng ngày 03-02.
- `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`: "từ dòng đầu partition tới đúng dòng hiện tại".

Dòng frame này có vẻ thừa, vì frame mặc định khi có `ORDER BY` nghe cũng giống thế. Nhưng không hoàn
toàn: bỏ nó đi (và bỏ `id`) thì hai giao dịch ngày 03-02 cùng hiện số dư 120. Mục 8.4 giải thích vì
sao và khi nào điều đó lại là cái bạn muốn.

### 7.4 Frame trượt: trung bình trượt (moving average)

Thay `UNBOUNDED PRECEDING` bằng một con số, frame sẽ "trượt" theo dòng hiện tại. Trung bình 3 dòng
gần nhất (dòng hiện tại và 2 dòng trước):

```sql
SELECT day, revenue,
       AVG(revenue) OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS avg_3_rows,
       COUNT(*)     OVER (ORDER BY day ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rows_in_frame
FROM daily_sales
ORDER BY day;
```

```
+------------+---------+------------+---------------+
| day        | revenue | avg_3_rows | rows_in_frame |
+------------+---------+------------+---------------+
| 2026-04-01 |     100 |   100.0000 |             1 |
| 2026-04-02 |     120 |   110.0000 |             2 |
| 2026-04-03 |      80 |   100.0000 |             3 |
| 2026-04-05 |     150 |   116.6667 |             3 |
| 2026-04-06 |     130 |   120.0000 |             3 |
+------------+---------+------------+---------------+
```

Cột `rows_in_frame` (cùng frame, dùng `COUNT(*)`) là mẹo debug rất đáng dùng: nó cho thấy frame của
mỗi dòng có bao nhiêu dòng. Hai điều rút ra:

- Ở đầu partition không đủ 2 dòng trước, frame chỉ chứa những dòng có thật; tài liệu MySQL ghi: khi
  không có dòng phía trước hay phía sau, `AVG()` tính trung bình của các dòng hiện có. Nên 110.0000
  ở dòng 04-02 là trung bình **2** ngày, không phải 3. Báo cáo cần "đủ 3 ngày mới tính" thì lọc
  `rows_in_frame = 3` ở tầng ngoài.
- ⚠️ `ROWS` đếm **dòng**, không đếm ngày: dòng 04-05 lấy 04-02, 04-03, 04-05 (3 dòng) chứ không phải
  "3 ngày gần nhất" (04-03, 04-04, 04-05). Muốn trượt theo thời gian thật thì dùng `RANGE` với
  `INTERVAL` (mục 8.3).

## 8. Frame: ROWS, RANGE và frame mặc định

### 8.1 Frame là gì, hàm nào dùng frame

*Frame* (khung) là một tập con của partition, được xác định **so với dòng hiện tại**. Khi dòng hiện
tại dịch xuống, frame dịch theo; vì vậy tài liệu MySQL gọi đây là *moving frame*. Partition trả lời
câu hỏi "dòng này thuộc nhóm nào", frame trả lời "trong nhóm đó, khi tính cho dòng này thì được nhìn
những dòng nào".

Không phải hàm nào cũng dùng frame. Theo tài liệu MySQL 8.4:

| Dùng frame | Bỏ qua frame, luôn làm việc trên cả partition |
|---|---|
| Mọi aggregate dùng như window function (`SUM`, `AVG`, `COUNT`, `MIN`, `MAX`...) | `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE` |
| `FIRST_VALUE`, `LAST_VALUE`, `NTH_VALUE` | `PERCENT_RANK`, `CUME_DIST` |
| | `LAG`, `LEAD` (chúng đếm lệch theo dòng trong partition) |

⚠️ Viết frame cho hàm thuộc cột phải không gây lỗi, frame chỉ bị lặng lẽ bỏ qua. Theo mã nguồn MySQL,
chỉ khi chạy `EXPLAIN` bạn mới thấy một Note (mã 3599): "Window function 'row_number' ignores the frame
clause of window ... and aggregates over the whole partition".

### 8.2 Cú pháp frame

```
{ROWS | RANGE} mốc_đầu                          -- dạng rút gọn: mốc cuối ngầm là CURRENT ROW
{ROWS | RANGE} BETWEEN mốc_đầu AND mốc_cuối

mốc:
  UNBOUNDED PRECEDING     dòng đầu tiên của partition
  N PRECEDING             N dòng trước (ROWS), hoặc giá trị nhỏ hơn N đơn vị (RANGE)
  CURRENT ROW             dòng hiện tại (ROWS), hoặc dòng hiện tại cùng mọi peer của nó (RANGE)
  N FOLLOWING             N dòng sau (ROWS), hoặc giá trị lớn hơn N đơn vị (RANGE)
  UNBOUNDED FOLLOWING     dòng cuối cùng của partition
```

Hình dung với `ROWS`, dòng hiện tại là d4 trong partition 6 dòng đã sắp:

```
partition đã sắp:                                   d1   d2   d3   d4   d5   d6
                                                                   ^ dòng hiện tại
ROWS BETWEEN 2 PRECEDING AND CURRENT ROW                      [d2   d3   d4]
ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING                           [d3   d4   d5]
ROWS UNBOUNDED PRECEDING   (= ... AND CURRENT ROW)           [d1   d2   d3   d4]
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING                        [d4   d5   d6]
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING     [d1   d2   d3   d4   d5   d6]
```

Quy tắc (tài liệu MySQL và thông báo lỗi trong mã nguồn MySQL 8.4):

- Dạng rút gọn chỉ ghi mốc đầu, mốc cuối ngầm là `CURRENT ROW`: `ROWS UNBOUNDED PRECEDING` chính là
  `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Mốc đầu của dạng rút gọn chỉ được là
  `UNBOUNDED PRECEDING`, `N PRECEDING` hoặc `CURRENT ROW`.
- Với `BETWEEN`, mốc đầu không được đứng sau mốc cuối. Mốc đầu không được là `UNBOUNDED FOLLOWING`
  (lỗi 3584), mốc cuối không được là `UNBOUNDED PRECEDING` (lỗi 3585).
- `N` phải là hằng: số không âm viết thẳng, dấu `?` của prepared statement, hoặc `INTERVAL giá_trị
  đơn_vị` (chỉ dùng với `RANGE`; dùng với `ROWS` là lỗi 3596). Không được là một cột hay biểu thức tính
  theo từng dòng: tài liệu MySQL liệt kê "mốc frame động phụ thuộc giá trị của dòng hiện tại" vào danh
  sách tính năng không hỗ trợ.
- Ở hai đầu partition, frame tự co lại theo số dòng có thật (như `rows_in_frame` ở mục 7.4).

### 8.3 ROWS và RANGE

Hai *frame unit* (đơn vị đo frame) khác nhau ở thứ được đếm:

- `ROWS`: đếm theo **vị trí dòng**. "2 PRECEDING" là hai dòng đứng trước, bất kể giá trị của chúng.
- `RANGE`: đo theo **giá trị** của cột trong `ORDER BY`. "300 PRECEDING" là các dòng có giá trị trong
  khoảng [giá trị hiện tại - 300, giá trị hiện tại]. Và `CURRENT ROW` trong `RANGE` nghĩa là dòng hiện
  tại **cùng mọi peer** của nó.

`RANGE` với một con số. Ví dụ: với mỗi nhân viên, có bao nhiêu người khác có lương chênh không quá 300
so với mình?

```sql
SELECT name, salary,
       COUNT(*) OVER (ORDER BY salary
                      RANGE BETWEEN 300 PRECEDING AND 300 FOLLOWING) - 1 AS others_within_300
FROM employees
ORDER BY salary, id;
```

```
+-------+--------+-------------------+
| name  | salary | others_within_300 |
+-------+--------+-------------------+
| Khoa  |   1500 |                 2 |
| Giang |   1800 |                 3 |
| Hà    |   1800 |                 3 |
| Dũng  |   2000 |                 3 |
| Em    |   2200 |                 3 |
| Bình  |   2500 |                 2 |
| Chi   |   2500 |                 2 |
| An    |   3000 |                 0 |
+-------+--------+-------------------+
```

Dòng Dũng (2000): frame là mọi dòng có lương trong [1700, 2300], tức Giang, Hà, Dũng, Em: 4 dòng, trừ
chính Dũng còn 3. Dòng An (3000): khoảng [2700, 3300] chỉ có An. Với `ROWS BETWEEN 300 PRECEDING AND
300 FOLLOWING` thì nghĩa hoàn toàn khác: 300 dòng trước và 300 dòng sau.

`RANGE` với `INTERVAL` trên cột ngày giờ: đây là cách đúng để làm "trung bình 3 ngày gần nhất" khi dữ
liệu có thể thiếu ngày. So sánh với `ROWS` ở mục 7.4:

```sql
SELECT day, revenue,
       AVG(revenue) OVER (ORDER BY day
                          ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)                AS avg_3_rows,
       AVG(revenue) OVER (ORDER BY day
                          RANGE BETWEEN INTERVAL 2 DAY PRECEDING AND CURRENT ROW)  AS avg_3_days,
       COUNT(*)     OVER (ORDER BY day
                          RANGE BETWEEN INTERVAL 2 DAY PRECEDING AND CURRENT ROW)  AS days_with_data
FROM daily_sales
ORDER BY day;
```

```
+------------+---------+------------+------------+----------------+
| day        | revenue | avg_3_rows | avg_3_days | days_with_data |
+------------+---------+------------+------------+----------------+
| 2026-04-01 |     100 |   100.0000 |   100.0000 |              1 |
| 2026-04-02 |     120 |   110.0000 |   110.0000 |              2 |
| 2026-04-03 |      80 |   100.0000 |   100.0000 |              3 |
| 2026-04-05 |     150 |   116.6667 |   115.0000 |              2 |
| 2026-04-06 |     130 |   120.0000 |   140.0000 |              2 |
+------------+---------+------------+------------+----------------+
```

Dòng 2026-04-05: `ROWS` lấy 3 dòng gần nhất là 04-02, 04-03, 04-05 (kéo cả ngày 02 vào, vì ngày 04
không có dòng); `RANGE ... INTERVAL 2 DAY` lấy các ngày từ 04-03 tới 04-05, tức chỉ 04-03 và 04-05,
trung bình (80 + 150) / 2 = 115. ⚠️ `AVG` chỉ chia cho số ngày **có dữ liệu**. Nếu "không có dòng"
nghĩa là doanh thu bằng 0 (cửa hàng nghỉ) và bạn muốn chia cho 3 ngày lịch, hãy dùng
`SUM(revenue) OVER (...) / 3`, hoặc lấp đủ dãy ngày trước (mục 11.4) rồi mới tính.

Ràng buộc của `RANGE` có con số (theo thông báo lỗi của MySQL 8.4):

- `ORDER BY` của window phải có **đúng một** biểu thức, kiểu số hoặc kiểu ngày giờ; sai là lỗi 3587
  ("Window '...' with RANGE N PRECEDING/FOLLOWING frame requires exactly one ORDER BY expression, of
  numeric or temporal type"). Tài liệu PostgreSQL ghi cùng ràng buộc này.
- Cột ngày giờ thì mốc phải là `INTERVAL` (lỗi 3588 nếu viết số trần); cột số thì không được dùng
  `INTERVAL` (lỗi 3589).
- `RANGE` chỉ với `UNBOUNDED` và `CURRENT ROW` (như frame mặc định) thì không có ràng buộc này.

### 8.4 Frame mặc định, và hai cái bẫy của nó

Không ghi frame thì MySQL dùng frame mặc định, và nó **phụ thuộc vào việc có `ORDER BY` hay không**
(tài liệu MySQL 8.4):

| `OVER` có | Frame mặc định | Nghĩa |
|---|---|---|
| Không có `ORDER BY` | `RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` | Cả partition (mọi dòng là peers) |
| Có `ORDER BY` | `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` | Từ đầu partition tới dòng hiện tại **và mọi peer của nó** |

Dòng thứ hai là nguồn gốc của hai cái bẫy.

**Bẫy 1: running total "nhảy bậc" khi có giá trị trùng.** So sánh frame mặc định với `ROWS` có
tie-breaker:

```sql
SELECT account, txn_date, id, amount,
       SUM(amount) OVER (PARTITION BY account ORDER BY txn_date)  AS sum_default,
       SUM(amount) OVER (PARTITION BY account ORDER BY txn_date, id
                         ROWS UNBOUNDED PRECEDING)                AS sum_rows
FROM transactions
ORDER BY account, txn_date, id;
```

```
+---------+------------+----+--------+-------------+----------+
| account | txn_date   | id | amount | sum_default | sum_rows |
+---------+------------+----+--------+-------------+----------+
| A       | 2026-03-01 |  1 |    100 |         100 |      100 |
| A       | 2026-03-02 |  2 |     50 |         120 |      150 |
| A       | 2026-03-02 |  3 |    -30 |         120 |      120 |
| A       | 2026-03-04 |  4 |     20 |         140 |      140 |
| B       | 2026-03-01 |  5 |    200 |         200 |      200 |
| B       | 2026-03-03 |  6 |    -50 |         150 |      150 |
+---------+------------+----+--------+-------------+----------+
```

Dòng id 2 có `sum_default` = 120 chứ không phải 150. Vì `ORDER BY txn_date` nên hai giao dịch cùng ngày
03-02 là peers; frame mặc định kết thúc ở "dòng hiện tại và mọi peer", nên khi tính cho id 2, frame đã
chứa luôn id 3 (-30). Hai peer luôn nhận cùng một giá trị.

Cả hai cột đều "đúng", tuỳ câu hỏi:

- "Số dư cuối mỗi ngày" (báo cáo theo ngày): `sum_default` đúng, vì giá trị trùng nhau là ý muốn.
- "Số dư ngay sau từng giao dịch" (sao kê): `sum_rows` đúng, và phải có tie-breaker `id`. Thiếu
  tie-breaker thì `ROWS` cũng không cứu được: hai dòng cùng ngày được cộng theo thứ tự tuỳ ý, số dư
  trung gian có thể là 150 hoặc 70 tuỳ lần chạy. Tài liệu PostgreSQL cảnh báo đúng điều này: chế độ
  `ROWS` có thể cho kết quả không đoán trước được nếu `ORDER BY` không sắp các dòng một cách duy nhất.

**Bẫy 2: `LAST_VALUE` trả về dòng hiện tại.** Đã thấy ở mục 6.2: frame mặc định dừng ở dòng hiện tại
(cùng peers), nên "dòng cuối của frame" là dòng hiện tại (hoặc peer cuối của nó), không phải dòng cuối
partition. `NTH_VALUE(x, N)` cũng chịu cùng ảnh hưởng: khi frame chưa đủ N dòng thì trả về NULL.

Hệ quả thứ ba ít người để ý, tài liệu MySQL nêu riêng: **thêm `ORDER BY` vào `OVER` có thể làm đổi kết
quả của aggregate**, vì frame mặc định đổi theo. `SUM(amount) OVER (PARTITION BY account)` là tổng của
cả tài khoản; thêm `ORDER BY txn_date` vào (chẳng hạn để "cho kết quả ổn định") thì nó biến thành
running total. Muốn có thứ tự mà vẫn tính trên cả partition, ghi rõ frame `ROWS BETWEEN UNBOUNDED
PRECEDING AND UNBOUNDED FOLLOWING`.

Quy tắc thực hành rút ra: **hễ dùng aggregate có `ORDER BY` trong `OVER`, hoặc dùng `FIRST_VALUE` /
`LAST_VALUE` / `NTH_VALUE`, hãy ghi frame ra cho rõ**, đừng dựa vào mặc định. Người đọc code sau (kể cả
bạn sáu tháng sau) không phải nhớ bảng ở trên.

### 8.5 Những gì MySQL chưa hỗ trợ về frame

Chuẩn SQL còn hai tính năng frame mà MySQL 8.4 nhận diện trong cú pháp nhưng báo lỗi khi chạy (tài
liệu MySQL, mục *Window Function Restrictions*):

- Đơn vị `GROUPS`: đo frame theo **số nhóm peers** (ví dụ "1 nhóm peers trước tới 1 nhóm peers sau").
  MySQL báo `ERROR 1235 (42000): This version of MySQL doesn't yet support 'GROUPS'`.
- Mệnh đề `EXCLUDE` (`EXCLUDE CURRENT ROW`, `EXCLUDE GROUP`, `EXCLUDE TIES`): loại bớt dòng hiện tại
  hoặc các peer khỏi frame. MySQL báo lỗi tương tự với `'EXCLUDE'`.

PostgreSQL hỗ trợ cả hai từ bản 11 (mục 12). Trên MySQL, muốn "trung bình của các dòng khác trừ chính
mình" thì tự trừ: `(SUM(x) OVER w - x) / (COUNT(*) OVER w - 1)` (nhớ xử lý trường hợp partition chỉ có
một dòng, mẫu số bằng 0).

## 9. Named window: mệnh đề WINDOW

### 9.1 Đặt tên để dùng lại

Khi nhiều hàm dùng cùng một định nghĩa window, viết lặp lại vừa dài vừa dễ sai lệch (sửa chỗ này quên
chỗ kia). Mệnh đề `WINDOW` đặt tên cho định nghĩa đó:

```sql
SELECT dept, name, salary,
       ROW_NUMBER() OVER w AS rn,
       RANK()       OVER w AS rnk,
       DENSE_RANK() OVER w AS drnk
FROM employees
WINDOW w AS (PARTITION BY dept ORDER BY salary DESC)
ORDER BY dept, salary DESC, id;
```

(`rn` của Bình và Chi ở câu này có thể đổi chỗ cho nhau giữa các lần chạy, vì `w` không có
tie-breaker; với `RANK` và `DENSE_RANK` thì không sao.)

- Vị trí: theo tài liệu MySQL, mệnh đề `WINDOW` nằm **giữa `HAVING` và `ORDER BY`**. Thứ tự đầy đủ:
  `SELECT ... FROM ... WHERE ... GROUP BY ... HAVING ... WINDOW ... ORDER BY ... LIMIT`.
- Định nghĩa nhiều window, cách nhau dấu phẩy: `WINDOW w1 AS (...), w2 AS (...)`.
- `OVER w` (không ngoặc) là dùng nguyên window `w`.

### 9.2 Kế thừa và bổ sung

Viết `OVER (w ...)` hoặc `WINDOW w2 AS (w ...)` là tạo window mới **dựa trên** `w` rồi bổ sung thêm.
Ví dụ dùng chung phần chia nhóm, mỗi hàm thêm thứ tự riêng (tài liệu MySQL có một ví dụ cùng kiểu):

```sql
SELECT dept, name, salary,
       FIRST_VALUE(name) OVER (w ORDER BY salary DESC, id) AS top_paid,
       FIRST_VALUE(name) OVER (w ORDER BY salary ASC, id)  AS lowest_paid
FROM employees
WINDOW w AS (PARTITION BY dept)
ORDER BY dept, salary DESC, id;
```

```
+-------+-------+--------+----------+-------------+
| dept  | name  | salary | top_paid | lowest_paid |
+-------+-------+--------+----------+-------------+
| eng   | An    |   3000 | An       | Dũng        |
| eng   | Bình  |   2500 | An       | Dũng        |
| eng   | Chi   |   2500 | An       | Dũng        |
| eng   | Dũng  |   2000 | An       | Dũng        |
| ops   | Khoa  |   1500 | Khoa     | Khoa        |
| sales | Em    |   2200 | Em       | Giang       |
| sales | Giang |   1800 | Em       | Giang       |
| sales | Hà    |   1800 | Em       | Giang       |
+-------+-------+--------+----------+-------------+
```

`FIRST_VALUE` với frame mặc định vẫn đúng (frame luôn bắt đầu từ dòng đầu partition), nên đảo chiều
`ORDER BY` rồi lấy `FIRST_VALUE` là cách gọn để có "dòng cuối" mà không phải ghi frame. Giang và Hà
cùng 1800; tie-breaker `id` tăng dần chọn Giang (id nhỏ hơn).

Mục 6.2 đã dùng dạng thêm frame: `OVER (w ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)`.

Quy tắc, theo tài liệu và thông báo lỗi của MySQL 8.4:

- **Chỉ được thêm, không được sửa.** Tài liệu ghi: `OVER` chỉ có thể thêm thuộc tính cho window đã đặt
  tên, không thể sửa; nếu window gốc đã có một loại thuộc tính (phân vùng, sắp xếp, frame) thì `OVER`
  tham chiếu nó không được có lại loại đó.
  - Window gốc đã có `ORDER BY` thì window kế thừa không được có `ORDER BY` nữa (lỗi 3583, "...cannot
    inherit ... since both contain an ORDER BY clause").
  - `PARTITION BY` chỉ được đặt ở window gốc: mã nguồn MySQL từ chối mọi window kế thừa có
    `PARTITION BY` (lỗi 3581, "A window which depends on another cannot define partitioning").
  - Window gốc có frame thì **không window nào được kế thừa nó** (lỗi 3582, "Window '...' has a frame
    definition, so cannot be referenced by another window"); nó chỉ dùng trực tiếp được bằng `OVER w`.
    Vì vậy hãy để frame ở window "lá" (chỗ dùng), không đặt ở window gốc dùng chung.
- Tham chiếu xuôi hay ngược đều được, miễn không thành vòng: `WINDOW w1 AS (w2), w2 AS (), w3 AS (w1)`
  hợp lệ; `WINDOW w1 AS (w2), w2 AS (w3), w3 AS (w1)` là lỗi (vòng tròn). PostgreSQL chặt hơn: window
  được tham chiếu phải đứng **trước** trong danh sách `WINDOW`.
- Tên window trùng nhau trong một câu là lỗi; dùng tên chưa định nghĩa cũng là lỗi.

### 9.3 Không chỉ là cho gọn: ảnh hưởng hiệu năng

Tài liệu MySQL (mục *Window Function Optimization*) ghi: optimizer **không** cố gộp các window có thể
tính trong một bước, ví dụ khi nhiều `OVER` có định nghĩa giống hệt nhau; cách khắc phục là định nghĩa
window trong mệnh đề `WINDOW` rồi tham chiếu bằng tên. Nghĩa là ba lần viết `OVER (PARTITION BY dept
ORDER BY salary DESC)` có thể tốn hơn một lần `WINDOW w AS (...)` dùng ba lần.

Giới hạn: tối đa 127 window cho mỗi khối `SELECT` (tính cả window đặt tên lẫn window viết thẳng trong
`OVER`), theo tài liệu MySQL.

## 10. Bên trong: MySQL tính window function thế nào

Mục này giúp bạn đoán được chi phí của một câu có window function. Phần cơ chế dựa trên tài liệu MySQL
(mục *Window Function Optimization*) và mã nguồn MySQL 8.4 (`sql/window.h`, `sql/window.cc`); tên các
cấu trúc bên trong có thể đổi giữa các phiên bản, ý tưởng thì ổn định.

### 10.1 Các bước thực thi

```
  dòng sau FROM / WHERE / GROUP BY / HAVING
                 |
                 v
  [1] sắp xếp theo (PARTITION BY..., ORDER BY...) của window thứ nhất
                 |
                 v
  [2] quét tuần tự từ trên xuống:
      eng An | eng Bình | eng Chi | eng Dũng | ops Khoa | sales Em | ...
                                             ^ giá trị dept đổi: bắt đầu partition mới, reset trạng thái
                 |
                 v
  [3] window kế tiếp: nếu cần thứ tự khác thì sắp lại, rồi quét tiếp
                 |
                 v
  SELECT còn lại -> ORDER BY -> LIMIT
```

1. Kết quả của `FROM`/`WHERE`/`GROUP BY`/`HAVING` được đưa vào bộ máy windowing (thường qua bảng tạm
   nội bộ).
2. Với mỗi window, các dòng được sắp theo các cột `PARTITION BY` rồi tới các cột `ORDER BY` (mã nguồn
   gộp hai danh sách này thành một khoá sắp xếp). Nhờ đã sắp, các dòng cùng partition nằm liền nhau.
3. MySQL quét các dòng đã sắp từ trên xuống, nhận ra ranh giới partition khi giá trị `PARTITION BY`
   đổi, và giữ một ít trạng thái cho từng hàm: `ROW_NUMBER` chỉ cần một bộ đếm, running total
   `SUM ... ROWS UNBOUNDED PRECEDING` chỉ cần một tổng đang cộng dở. Những hàm như vậy tính được ngay
   khi đọc tới dòng, theo một lượt.
4. Những hàm cần nhìn **về phía sau** hoặc cần **biết cả partition** thì không tính một lượt được:
   `LEAD`, frame có `FOLLOWING`, frame `RANGE` (phải đọc tới hết các peer), `NTILE`, `PERCENT_RANK`,
   `CUME_DIST` (cần biết partition có bao nhiêu dòng). Với chúng MySQL phải đệm các dòng vào một bảng
   tạm gọi là *frame buffer* rồi mới tính (mã nguồn MySQL 8.4 cũng đệm cho cả `LAG`). Theo mã nguồn,
   aggregate với frame `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` là trường hợp được miễn
   buffer, còn frame mặc định (`RANGE`) thì không. Thêm một lý do để ghi rõ `ROWS` khi bạn thật sự muốn
   cộng từng dòng.
5. Nhiều window: tài liệu MySQL ghi optimizer xử lý liền nhau các window có cùng yêu cầu sắp xếp để bỏ
   bớt bước sort cho các window sau window đầu tiên. Window có thứ tự khác thì phải sắp lại.

Trên `EXPLAIN FORMAT=TREE` (chương 12), bước windowing hiện thành một node riêng. Output minh hoạ (rút
gọn, bỏ phần cost):

```
-> Window aggregate: row_number() OVER (PARTITION BY employees.dept ORDER BY employees.salary desc )
    -> Sort: employees.dept, employees.salary DESC
        -> Table scan on employees
```

Theo mã nguồn, tên node là `Window aggregate` khi không cần buffer, `Window aggregate with buffering`
hoặc `Window multi-pass aggregate with buffering` khi cần. Với `EXPLAIN` dạng bảng truyền thống, tài
liệu MySQL nói thông tin windowing quá nhiều để hiển thị; muốn xem thì dùng `EXPLAIN FORMAT=JSON` và tìm
phần tử `windowing`.

### 10.2 Hệ quả về hiệu năng

- **Chi phí chính là sắp xếp và đệm dòng.** Một window trên N dòng tốn cỡ một lần sort N dòng (trừ khi
  dữ liệu đi vào đã đúng thứ tự cần), cộng bộ nhớ hoặc đĩa cho bảng tạm. Đòn bẩy lớn nhất là **giảm số
  dòng đi vào window**: lọc bằng `WHERE` ở tầng trong càng sớm càng tốt (khi điều kiện đó không làm
  đổi ý nghĩa, xem mục 4.4).
- **CTE / derived table chứa window function luôn được materialize.** Tài liệu MySQL ghi: subquery có
  window function thì không được merge vào câu ngoài, luôn được materialize. Hệ quả: với mẫu "tính ở
  trong, lọc `rn <= 3` ở ngoài", tầng trong vẫn đánh số **toàn bộ** các dòng nó đọc, rồi tầng ngoài
  mới bỏ đi phần lớn. Điều kiện trên `rn` không bao giờ đẩy vào trong được, vì nó phụ thuộc kết quả
  của chính window.
- Điều kiện chỉ dính tới cột `PARTITION BY` (ví dụ `dept = 'eng'` với window `PARTITION BY dept`) thì
  đặt trong hay ngoài đều cùng kết quả. Mã nguồn MySQL 8.4 có cơ chế *derived condition pushdown* đẩy
  loại điều kiện này qua window function vào tầng trong (khi các cột của điều kiện nằm trong
  `PARTITION BY` của mọi window ở tầng trong); nhưng tự viết vào tầng trong là cách chắc
  chắn nhất, dễ đọc, và không phụ thuộc optimizer.
- **Index** giúp phần đọc dữ liệu (`WHERE`, `JOIN`) như mọi câu khác. Với bài "top N mỗi nhóm" khi số
  nhóm ít mà mỗi nhóm rất nhiều dòng, có cách khác dùng index tốt hơn window function (mục 11.1).
- **Số thực và `windowing_use_high_precision`.** Với frame trượt, MySQL có thể tính nhanh bằng cách
  "trừ dòng vừa rời frame, cộng dòng vừa vào" (*inverse aggregation*) thay vì cộng lại cả frame cho mỗi
  dòng. Tài liệu MySQL: với kiểu không phải số thực (kể cả `DECIMAL`), cách này luôn an toàn và luôn
  được dùng; với `FLOAT`/`DOUBLE` nó có thể làm mất độ chính xác, nên mặc định biến
  `windowing_use_high_precision` bật (ON) và MySQL tránh inverse aggregation cho số thực (chậm hơn
  nhưng chính xác). `MIN()` và `MAX()` không bao giờ dùng inverse aggregation. Đây là thêm một lý do
  để lưu tiền bằng `DECIMAL` (chương 03).

## 11. Các bài toán kinh điển

Đây là các bài hay gặp trong công việc và trong phỏng vấn SQL. Mỗi bài: đề, lời giải, chỗ dễ sai.

### 11.1 Top N mỗi nhóm

Đề: lấy 2 người lương cao nhất của mỗi phòng.

```sql
WITH ranked AS (
  SELECT dept, name, salary,
         ROW_NUMBER() OVER (PARTITION BY dept ORDER BY salary DESC, id) AS rn
  FROM employees
)
SELECT dept, name, salary, rn
FROM ranked
WHERE rn <= 2
ORDER BY dept, rn;
```

```
+-------+-------+--------+----+
| dept  | name  | salary | rn |
+-------+-------+--------+----+
| eng   | An    |   3000 |  1 |
| eng   | Bình  |   2500 |  2 |
| ops   | Khoa  |   1500 |  1 |
| sales | Em    |   2200 |  1 |
| sales | Giang |   1800 |  2 |
+-------+-------+--------+----+
```

Chỗ cần hỏi lại người ra đề: Bình và Chi cùng 2500, "2 người cao nhất" của phòng `eng` là ai? Ba hàm
xếp hạng là ba cách hiểu khác nhau:

| Điều kiện | Top 2 phòng `eng` | Top 3 phòng `eng` | Nghĩa |
|---|---|---|---|
| `ROW_NUMBER() <= N` | An, Bình | An, Bình, Chi | Đúng N người; ai bị loại giữa những người đồng hạng do tie-breaker quyết định |
| `RANK() <= N` | An, Bình, Chi | An, Bình, Chi | N vị trí đầu, giữ cả người đồng hạng (có thể ra nhiều hơn N) |
| `DENSE_RANK() <= N` | An, Bình, Chi | An, Bình, Chi, Dũng | Mọi người thuộc N mức lương cao nhất (có thể ra rất nhiều) |

Trong phỏng vấn, chủ động nêu ba cách hiểu này là điểm cộng.

**Hiệu năng.** Lời giải trên đánh số mọi dòng của bảng (mục 10.2). Với bảng nhỏ hoặc khi cần gần hết
các nhóm thì ổn. Khi bảng rất lớn mà số nhóm ít (ví dụ 3 đơn hàng lớn nhất của mỗi trong 100 khách,
giữa 10 triệu đơn), cách khác là *lateral derived table* (MySQL 8.0.14 trở lên): với mỗi nhóm, chạy
một câu con `ORDER BY ... LIMIT N`, câu con này tận dụng được index:

```sql
-- Trên bảng lớn cần index phù hợp, ví dụ: CREATE INDEX idx_dept_salary ON employees (dept, salary);
SELECT d.dept, t.name, t.salary
FROM (SELECT DISTINCT dept FROM employees) AS d
JOIN LATERAL (
  SELECT e.name, e.salary
  FROM employees AS e
  WHERE e.dept = d.dept               -- LATERAL: câu con được nhắc tới d, bảng đứng trước nó
  ORDER BY e.salary DESC, e.id
  LIMIT 2
) AS t ON TRUE
ORDER BY d.dept, t.salary DESC;
```

Kết quả giống hệt bảng trên (5 dòng). Không có từ khoá `LATERAL`, câu con không được nhắc tới cột của
bảng đứng trước trong cùng `FROM` (tài liệu MySQL đưa ví dụ lỗi `ERROR 1054 ... Unknown column`).
`LIMIT N` cho nghĩa giống `ROW_NUMBER`. Cách nào nhanh hơn thì đo bằng `EXPLAIN ANALYZE` (chương 12),
đừng đoán.

Liên hệ Laravel: khi eager load quan hệ có giới hạn số dòng mỗi cha, ví dụ
`User::with(['posts' => fn ($query) => $query->latest()->limit(3)])->get()`, Laravel không thể dùng
`LIMIT 3` cho cả câu (vì cần 3 bài **mỗi** user). Mã nguồn Laravel 13 (`Grammar::compileGroupLimit`)
sinh ra đúng mẫu "tính ở trong, lọc ở ngoài" với `ROW_NUMBER`. Output minh hoạ:

```sql
select * from (
  select *, row_number() over (partition by `posts`.`user_id` order by `created_at` desc)
         as `laravel_row`
  from `posts` where `posts`.`user_id` in (1, 2, 3)
) as `laravel_table`
where `laravel_row` <= 3
order by `laravel_row`
```

Để ý điều kiện `user_id in (...)` nằm ở tầng trong: chỉ đánh số các bài của những user cần, đúng lời
khuyên ở mục 10.2. (Với MySQL cũ hơn 8.0.11, Laravel chuyển sang cách giả lập bằng biến người dùng như
mục 2.4 đã cảnh báo.)

### 11.2 Running total và "chạm ngưỡng"

Running total cơ bản đã có ở mục 7.3. Biến thể hay gặp: lọc theo tổng luỹ kế, ví dụ "những người lương
cao nhất nào cộng lại chiếm một nửa quỹ lương công ty?" (kiểu phân tích Pareto).

```sql
WITH c AS (
  SELECT name, salary,
         SUM(salary) OVER (ORDER BY salary DESC, id ROWS UNBOUNDED PRECEDING) AS running,
         SUM(salary) OVER ()                                                  AS total
  FROM employees
)
SELECT name, salary, running, ROUND(100 * running / total, 1) AS running_pct
FROM c
ORDER BY running;
```

```
+-------+--------+---------+-------------+
| name  | salary | running | running_pct |
+-------+--------+---------+-------------+
| An    |   3000 |    3000 |        17.3 |
| Bình  |   2500 |    5500 |        31.8 |
| Chi   |   2500 |    8000 |        46.2 |
| Em    |   2200 |   10200 |        59.0 |
| Dũng  |   2000 |   12200 |        70.5 |
| Giang |   1800 |   14000 |        80.9 |
| Hà    |   1800 |   15800 |        91.3 |
| Khoa  |   1500 |   17300 |       100.0 |
+-------+--------+---------+-------------+
```

Muốn lấy đúng nhóm "vừa đủ chạm 50%", điều kiện là: **trước khi** cộng người này, tổng vẫn chưa tới
50%. Thêm vào tầng ngoài:

```sql
WHERE running - salary < 0.5 * total     -- running - salary: tổng luỹ kế của những người đứng trước
```

Kết quả: An, Bình, Chi, Em (Em là người làm tổng vượt 50%: 8000 trước Em, 10200 sau Em). Viết
`WHERE running <= 0.5 * total` sẽ thiếu mất Em, lỗi lệch một (*off-by-one*) kinh điển của bài này.

### 11.3 Giá trị lớn thứ N

Đề: tìm mức lương cao thứ 3 của công ty. Xếp hạng cả công ty bằng ba hàm để thấy hàm nào đúng:

```sql
SELECT name, salary,
       ROW_NUMBER() OVER (ORDER BY salary DESC, id) AS rn,
       RANK()       OVER (ORDER BY salary DESC)     AS rnk,
       DENSE_RANK() OVER (ORDER BY salary DESC)     AS drnk
FROM employees
ORDER BY salary DESC, id;
```

```
+-------+--------+----+-----+------+
| name  | salary | rn | rnk | drnk |
+-------+--------+----+-----+------+
| An    |   3000 |  1 |   1 |    1 |
| Bình  |   2500 |  2 |   2 |    2 |
| Chi   |   2500 |  3 |   2 |    2 |
| Em    |   2200 |  4 |   4 |    3 |
| Dũng  |   2000 |  5 |   5 |    4 |
| Giang |   1800 |  6 |   6 |    5 |
| Hà    |   1800 |  7 |   6 |    5 |
| Khoa  |   1500 |  8 |   8 |    6 |
+-------+--------+----+-----+------+
```

Các mức lương từ cao xuống là 3000, 2500, 2200..., nên mức cao thứ 3 là 2200.

- `drnk = 3` ra Em, 2200: đúng.
- `rnk = 3` không ra dòng nào (hạng 3 bị bỏ trống vì Bình và Chi đồng hạng 2): sai.
- `rn = 3` ra Chi, 2500: sai, đó là mức cao thứ 2.

Lời giải trả về `NULL` khi không tồn tại mức thứ N (yêu cầu thường gặp trong đề bài):

```sql
SELECT (
  SELECT DISTINCT salary
  FROM (SELECT salary, DENSE_RANK() OVER (ORDER BY salary DESC) AS drnk
        FROM employees) AS r
  WHERE drnk = 3
) AS third_highest;
-- third_highest = 2200; đổi 3 thành 7 thì ra NULL (công ty chỉ có 6 mức lương)
```

- `DISTINCT` cần thiết vì nhiều người có thể cùng mức (thử với `drnk = 2`: Bình và Chi). Thiếu nó, scalar
  subquery trả về hai dòng và MySQL báo lỗi.
- Bọc trong `SELECT (...)` (scalar subquery, chương 09) để "không có dòng" biến thành `NULL`.

Theo từng nhóm, ví dụ mức lương cao thứ 2 của mỗi phòng:

```sql
WITH r AS (
  SELECT dept, salary,
         DENSE_RANK() OVER (PARTITION BY dept ORDER BY salary DESC) AS drnk
  FROM employees
)
SELECT DISTINCT dept, salary AS second_highest
FROM r
WHERE drnk = 2
ORDER BY dept;
```

```
+-------+----------------+
| dept  | second_highest |
+-------+----------------+
| eng   |           2500 |
| sales |           1800 |
+-------+----------------+
```

Phòng `ops` chỉ có một mức lương nên không có dòng. Muốn `ops` hiện ra với `NULL` thì lấy danh sách
phòng rồi `LEFT JOIN` với kết quả trên (bài tập cuối chương).

Cách không dùng window: `SELECT DISTINCT salary FROM employees ORDER BY salary DESC LIMIT 1 OFFSET 2`
cũng ra 2200. Nhưng nó trả về tập rỗng (không phải `NULL`) khi không có, không làm theo nhóm được, và
quên `DISTINCT` là ra 2500 (sai như `ROW_NUMBER`).

### 11.4 So với kỳ trước

Đề: doanh thu mỗi tháng tăng giảm bao nhiêu phần trăm so với tháng trước (*month over month*, MoM) và so
với cùng tháng năm trước (*year over year*, YoY). Bảng `monthly_revenue` chỉ có quý 1 của 2025 và 2026.

Lời giải ngây thơ dùng `LAG` trên thứ tự thời gian:

```sql
SELECT month_start, revenue,
       LAG(revenue) OVER (ORDER BY month_start) AS prev_row_revenue
FROM monthly_revenue
ORDER BY month_start;
```

```
+-------------+---------+------------------+
| month_start | revenue | prev_row_revenue |
+-------------+---------+------------------+
| 2025-01-01  |     100 |             NULL |
| 2025-02-01  |      80 |              100 |
| 2025-03-01  |     120 |               80 |
| 2026-01-01  |     150 |              120 |
| 2026-02-01  |      60 |              150 |
| 2026-03-01  |     180 |               60 |
+-------------+---------+------------------+
```

⚠️ Tháng 1/2026 bị so với tháng 3/2025, vì đó là **dòng** liền trước. Cùng một lỗi với mục 6.1: `LAG`
không biết gì về lịch. Hai cách sửa.

Cách 1, kiểm tra khoảng cách: lấy cả mốc thời gian của dòng trước, chỉ dùng giá trị khi mốc đó đúng là
kỳ mong đợi. Cùng ý đó cho YoY: chia partition theo tháng trong năm, dòng trước trong partition là cùng
tháng của năm trước đó (nếu có).

```sql
WITH m AS (
  SELECT month_start, revenue,
         CASE WHEN LAG(month_start) OVER w_time = month_start - INTERVAL 1 MONTH
              THEN LAG(revenue) OVER w_time END                   AS prev_month,
         CASE WHEN LAG(month_start) OVER w_year = month_start - INTERVAL 1 YEAR
              THEN LAG(revenue) OVER w_year END                   AS same_month_last_year
  FROM monthly_revenue
  WINDOW w_time AS (ORDER BY month_start),
         w_year AS (PARTITION BY MONTH(month_start) ORDER BY month_start)
)
SELECT month_start, revenue, prev_month, same_month_last_year,
       ROUND(100 * (revenue - prev_month) / NULLIF(prev_month, 0), 1)                     AS mom_pct,
       ROUND(100 * (revenue - same_month_last_year) / NULLIF(same_month_last_year, 0), 1) AS yoy_pct
FROM m
ORDER BY month_start;
```

```
+-------------+---------+------------+----------------------+---------+---------+
| month_start | revenue | prev_month | same_month_last_year | mom_pct | yoy_pct |
+-------------+---------+------------+----------------------+---------+---------+
| 2025-01-01  |     100 |       NULL |                 NULL |    NULL |    NULL |
| 2025-02-01  |      80 |        100 |                 NULL |   -20.0 |    NULL |
| 2025-03-01  |     120 |         80 |                 NULL |    50.0 |    NULL |
| 2026-01-01  |     150 |       NULL |                  100 |    NULL |    50.0 |
| 2026-02-01  |      60 |        150 |                   80 |   -60.0 |   -25.0 |
| 2026-03-01  |     180 |         60 |                  120 |   200.0 |    50.0 |
+-------------+---------+------------+----------------------+---------+---------+
```

- `CASE WHEN ... THEN ... END` không có `ELSE` trả về `NULL` khi điều kiện không đúng, kể cả khi
  `LAG(month_start)` là `NULL` ở dòng đầu (so sánh với NULL ra NULL, không phải đúng; chương 06).
- `NULLIF(prev, 0)`: kỳ trước bằng 0 thì phép chia trả về `NULL` thay vì chia cho 0. MySQL trả về
  `NULL` cho phép chia cho 0 trong `SELECT` (kèm warning) nên không sập, nhưng viết `NULLIF` thể hiện
  rõ ý đồ và chạy giống nhau trên PostgreSQL (nơi chia cho 0 là lỗi).
- `PARTITION BY MONTH(month_start)` là biểu thức trong `PARTITION BY`, MySQL cho phép (mục 3.3).

Cách 2, lấp đủ dãy thời gian trước khi `LAG`: sinh lịch bằng recursive CTE (chương 09) rồi
`LEFT JOIN`. Ví dụ "so với đúng ngày hôm qua" cho `daily_sales`:

```sql
WITH RECURSIVE calendar AS (
  SELECT DATE '2026-04-01' AS day
  UNION ALL
  SELECT day + INTERVAL 1 DAY FROM calendar WHERE day < '2026-04-06'
)
SELECT c.day,
       COALESCE(s.revenue, 0)                            AS revenue,
       LAG(COALESCE(s.revenue, 0)) OVER (ORDER BY c.day) AS yesterday_revenue
FROM calendar AS c
LEFT JOIN daily_sales AS s ON s.day = c.day
ORDER BY c.day;
```

```
+------------+---------+-------------------+
| day        | revenue | yesterday_revenue |
+------------+---------+-------------------+
| 2026-04-01 |     100 |              NULL |
| 2026-04-02 |     120 |               100 |
| 2026-04-03 |      80 |               120 |
| 2026-04-04 |       0 |                80 |
| 2026-04-05 |     150 |                 0 |
| 2026-04-06 |     130 |               150 |
+------------+---------+-------------------+
```

Giờ ngày 04-05 được so với ngày 04-04 (doanh thu 0). Điền 0 hay để `NULL` là quyết định nghiệp vụ:
"cửa hàng nghỉ" là 0, "mất dữ liệu" thì nên để `NULL` để không kéo lệch các chỉ số. Cách 2 cũng là
tiền đề cho trung bình trượt theo ngày lịch bằng `ROWS` (vì sau khi lấp, mỗi ngày đúng một dòng).

### 11.5 Gaps and islands

*Gaps and islands* là họ bài toán trên một dãy có thứ tự (ngày, số, thời điểm): tìm các đoạn liên tiếp
(*island*, "đảo") và các chỗ đứt (*gap*, "khe"). Ví dụ: chuỗi ngày đăng nhập liên tiếp dài nhất, các
khoảng máy chủ hoạt động liên tục, các số hoá đơn bị nhảy.

Dữ liệu `logins` theo ngày (bỏ trùng):

```
user 1:  05-01  05-02  05-03  .....  05-05  05-06      -> đảo [01..03] và [05..06], khe 05-04
user 2:  05-01  .....  05-03  05-04  05-05  05-06      -> đảo [01..01] và [03..06], khe 05-02
```

**Ý tưởng chính.** Trong một đảo, ngày tăng đúng 1 mỗi dòng, và số thứ tự `ROW_NUMBER` cũng tăng đúng 1
mỗi dòng. Vậy `ngày - số thứ tự` là **hằng số** trong một đảo, và nhảy sang giá trị khác khi qua khe.
Hằng số đó dùng làm mã nhóm:

```sql
WITH days AS (
  SELECT DISTINCT user_id, login_date FROM logins        -- bước 1: mỗi ngày một dòng
),
numbered AS (
  SELECT user_id, login_date,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
  FROM days
)
SELECT user_id, login_date, rn,
       login_date - INTERVAL rn DAY AS grp               -- bước 2: hằng số trong mỗi đảo
FROM numbered
ORDER BY user_id, login_date;
```

```
+---------+------------+----+------------+
| user_id | login_date | rn | grp        |
+---------+------------+----+------------+
|       1 | 2026-05-01 |  1 | 2026-04-30 |
|       1 | 2026-05-02 |  2 | 2026-04-30 |
|       1 | 2026-05-03 |  3 | 2026-04-30 |
|       1 | 2026-05-05 |  4 | 2026-05-01 |
|       1 | 2026-05-06 |  5 | 2026-05-01 |
|       2 | 2026-05-01 |  1 | 2026-04-30 |
|       2 | 2026-05-03 |  2 | 2026-05-01 |
|       2 | 2026-05-04 |  3 | 2026-05-01 |
|       2 | 2026-05-05 |  4 | 2026-05-01 |
|       2 | 2026-05-06 |  5 | 2026-05-01 |
+---------+------------+----+------------+
```

Bước 3, gom theo `(user_id, grp)` để ra từng đảo:

```sql
WITH days AS (
  SELECT DISTINCT user_id, login_date FROM logins
),
numbered AS (
  SELECT user_id, login_date,
         ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY login_date) AS rn
  FROM days
)
SELECT user_id,
       MIN(login_date) AS streak_start,
       MAX(login_date) AS streak_end,
       COUNT(*)        AS days
FROM numbered
GROUP BY user_id, login_date - INTERVAL rn DAY
ORDER BY user_id, streak_start;
```

```
+---------+--------------+------------+------+
| user_id | streak_start | streak_end | days |
+---------+--------------+------------+------+
|       1 | 2026-05-01   | 2026-05-03 |    3 |
|       1 | 2026-05-05   | 2026-05-06 |    2 |
|       2 | 2026-05-01   | 2026-05-01 |    1 |
|       2 | 2026-05-03   | 2026-05-06 |    4 |
+---------+--------------+------------+------+
```

Chuỗi dài nhất của mỗi user là thêm một tầng `GROUP BY user_id` lấy `MAX(days)`: user 1 là 3 ngày, user
2 là 4 ngày.

Chỗ dễ sai:

- ⚠️ **Quên bỏ trùng.** User 1 đăng nhập hai lần ngày 05-02. Không có bước `DISTINCT`, `ROW_NUMBER` đánh
  số 6 dòng, `grp` lần lượt là 04-30, 04-30, 04-29, 04-29, 04-30, 04-30: nhóm 04-30 gom cả 05-01,
  05-02, 05-05, 05-06 thành một "chuỗi" 4 ngày, sai hoàn toàn. Thay vì `DISTINCT` có thể dùng
  `DENSE_RANK()` (các dòng cùng ngày cùng hạng), nhưng khi đó phải đếm `COUNT(DISTINCT login_date)`.
- ⚠️ **Phép trừ số không dấu.** Bài trên trừ ngày cho một khoảng (`INTERVAL rn DAY`), không có vấn đề.
  Nhưng với dãy **số nguyên** (số hoá đơn, số phiên bản...), người ta hay viết `so - ROW_NUMBER() OVER
  (...)`. Trong MySQL, `ROW_NUMBER` có kiểu `BIGINT UNSIGNED` (mục 5.1), và tài liệu MySQL ghi: phép
  trừ giữa hai số nguyên mà một bên `UNSIGNED` cho kết quả không dấu; nếu kết quả lẽ ra âm thì báo lỗi
  `ERROR 1690 (22003): BIGINT UNSIGNED value is out of range in ...`. Dãy bắt đầu từ 0, có số âm, hay
  đơn giản là giá trị nhỏ hơn số thứ tự là dính. Cách an toàn: `so - CAST(ROW_NUMBER() OVER (...) AS
  SIGNED)`. PostgreSQL không có bẫy này (`row_number()` trả về `bigint` có dấu).

**Cách thứ hai: đánh dấu điểm đầu đảo rồi cộng dồn.** Cách này tổng quát hơn: đổi được luật "liên tiếp"
(ví dụ cho phép nghỉ một ngày) và dùng được cho đảo theo giá trị bằng nhau (chuỗi trạng thái giống nhau
liên tiếp).

```sql
WITH days AS (
  SELECT DISTINCT user_id, login_date FROM logins
),
flagged AS (
  SELECT user_id, login_date,
         -- 1 nếu dòng này mở đảo mới. Dòng đầu: LAG là NULL, DATEDIFF ra NULL,
         -- "NULL = 1" không đúng nên rơi vào ELSE 1.
         CASE WHEN DATEDIFF(login_date,
                            LAG(login_date) OVER (PARTITION BY user_id ORDER BY login_date)) = 1
              THEN 0 ELSE 1 END AS is_start
  FROM days
),
grouped AS (
  SELECT user_id, login_date,
         SUM(is_start) OVER (PARTITION BY user_id ORDER BY login_date
                             ROWS UNBOUNDED PRECEDING) AS island_id
  FROM flagged
)
SELECT user_id, island_id,
       MIN(login_date) AS streak_start, MAX(login_date) AS streak_end, COUNT(*) AS days
FROM grouped
GROUP BY user_id, island_id
ORDER BY user_id, island_id;
```

```
+---------+-----------+--------------+------------+------+
| user_id | island_id | streak_start | streak_end | days |
+---------+-----------+--------------+------------+------+
|       1 |         1 | 2026-05-01   | 2026-05-03 |    3 |
|       1 |         2 | 2026-05-05   | 2026-05-06 |    2 |
|       2 |         1 | 2026-05-01   | 2026-05-01 |    1 |
|       2 |         2 | 2026-05-03   | 2026-05-06 |    4 |
+---------+-----------+--------------+------------+------+
```

`is_start` của user 1 là 1, 0, 0, 1, 0; cộng dồn ra `island_id` 1, 1, 1, 2, 2. Phải tách thành ba tầng
vì không lồng được window function (`SUM(...LAG(...) OVER...) OVER` là lỗi, mục 6.3). Đây cũng chính
là mẫu "đánh dấu rồi cộng dồn" của bài forward fill.

**Tìm khe (gaps)** thì dùng `LEAD`: khe nằm giữa một ngày và ngày kế tiếp khi chúng cách nhau hơn 1:

```sql
WITH days AS (
  SELECT DISTINCT user_id, login_date FROM logins
),
nxt AS (
  SELECT user_id, login_date,
         LEAD(login_date) OVER (PARTITION BY user_id ORDER BY login_date) AS next_date
  FROM days
)
SELECT user_id,
       login_date + INTERVAL 1 DAY AS gap_start,
       next_date  - INTERVAL 1 DAY AS gap_end
FROM nxt
WHERE next_date > login_date + INTERVAL 1 DAY
ORDER BY user_id, gap_start;
```

```
+---------+------------+------------+
| user_id | gap_start  | gap_end    |
+---------+------------+------------+
|       1 | 2026-05-04 | 2026-05-04 |
|       2 | 2026-05-02 | 2026-05-02 |
+---------+------------+------------+
```

Dòng cuối mỗi user có `next_date` là `NULL`, điều kiện `NULL > ...` không đúng nên tự bị loại.

### 11.6 Khử trùng: giữ một dòng mỗi nhóm trùng

Bảng `logins` có hai dòng (user 1, 2026-05-02). Muốn giữ dòng `id` nhỏ nhất, xoá các dòng còn lại:
đánh số trong mỗi nhóm trùng, dòng nào số lớn hơn 1 là dòng thừa. Luôn **xem trước** những gì sẽ xoá:

```sql
WITH ranked AS (
  SELECT id, user_id, login_date,
         ROW_NUMBER() OVER (PARTITION BY user_id, login_date ORDER BY id) AS rn
  FROM logins
)
SELECT * FROM ranked WHERE rn > 1;
-- một dòng: id = 3, user_id = 1, login_date = 2026-05-02, rn = 2
```

Rồi mới xoá. Tài liệu MySQL ghi window function không được dùng trực tiếp trong `UPDATE`/`DELETE` để
sửa dòng, nhưng được dùng trong subquery của chúng để chọn dòng. Chương 09 (mục 6.5) đã nói về lỗi 1093
khi vừa sửa vừa đọc cùng một bảng, và ngoại lệ: derived table được materialize. Derived table chứa
window function luôn được materialize (mục 10.2), nên dạng `DELETE` nhiều bảng sau hợp lệ:

```sql
DELETE l
FROM logins AS l
JOIN (
  SELECT id
  FROM (
    SELECT id, ROW_NUMBER() OVER (PARTITION BY user_id, login_date ORDER BY id) AS rn
    FROM logins
  ) AS ranked
  WHERE rn > 1
) AS dup ON dup.id = l.id;
-- Query OK, 1 row affected
```

Sau câu này bảng `logins` không còn dòng trùng. Muốn làm lại các ví dụ ở mục 11.5 với dữ liệu gốc thì
chạy lại đoạn tạo dữ liệu ở mục 1. Xoá trùng xong, hãy thêm `UNIQUE (user_id, login_date)` (chương 04)
để chặn trùng từ gốc; nếu không, dọn xong hôm nay thì mai lại có.

## 12. Đối chiếu PostgreSQL

Cú pháp lõi (`OVER`, `PARTITION BY`, `ORDER BY`, `ROWS`/`RANGE`, `WINDOW`) và các hàm trong chương này
giống nhau giữa MySQL 8.4 và PostgreSQL 18. Khác biệt nằm ở các tuỳ chọn mở rộng và ở chi tiết:

| Điểm | MySQL 8.4 | PostgreSQL 18 |
|---|---|---|
| Có window function từ | 8.0 | 8.4 |
| Đơn vị frame | `ROWS`, `RANGE` (`GROUPS` báo lỗi 1235) | `ROWS`, `RANGE`, `GROUPS` (từ bản 11) |
| `EXCLUDE CURRENT ROW / GROUP / TIES` | Báo lỗi 1235 | Có (từ bản 11) |
| `RANGE` có offset trên cột ngày | `RANGE BETWEEN INTERVAL 2 DAY PRECEDING AND CURRENT ROW` | `RANGE BETWEEN INTERVAL '2 days' PRECEDING AND CURRENT ROW` |
| `FILTER (WHERE ...)` cho aggregate | Không có | Có: `count(*) FILTER (WHERE ...) OVER (...)` |
| `IGNORE NULLS`, `FROM LAST` | Parser nhận, báo lỗi | Không hỗ trợ |
| `DISTINCT` trong aggregate dùng như window | Báo lỗi 1235 | Không hỗ trợ |
| Tham số offset của `LAG`/`LEAD` | Phải là hằng (literal, `?`, biến) | Được là biểu thức, tính theo từng dòng |
| Kiểu của `row_number`, `rank`, `dense_rank` | `BIGINT UNSIGNED` | `bigint` (có dấu) |
| Kiểu của `ntile` | `BIGINT UNSIGNED` | `integer` |
| NULL khi `ORDER BY` tăng dần | Đứng đầu; không có cú pháp `NULLS FIRST/LAST` | Đứng cuối (NULL coi như lớn nhất); có `NULLS FIRST/LAST` |
| Tham chiếu window trong `WINDOW` | Xuôi và ngược, không được vòng | Chỉ tới window đứng trước |
| `QUALIFY` | Không dùng được trên bản phát hành (mục 4.3) | Không có |
| Top-N bằng `ROW_NUMBER` dừng sớm khi đủ dòng | Không (theo Use The Index, Luke!) | Có thể, từ bản 15 |

Vài điểm đáng nói thêm.

**`FILTER`** thay cho `CASE` bên trong aggregate. Đếm số người lương từ 2000 trở lên trong phòng của
mỗi nhân viên:

```sql
-- PostgreSQL
SELECT dept, name, salary,
       count(*) FILTER (WHERE salary >= 2000) OVER (PARTITION BY dept) AS high_paid_in_dept
FROM employees;

-- MySQL (và cũng chạy được trên PostgreSQL): COUNT bỏ qua NULL, CASE không có ELSE trả về NULL
SELECT dept, name, salary,
       COUNT(CASE WHEN salary >= 2000 THEN 1 END) OVER (PARTITION BY dept) AS high_paid_in_dept
FROM employees;
-- eng: 4 ở mọi dòng, sales: 1, ops: 0
```

**`GROUPS`** đo frame theo số nhóm peers. "Tổng của ngày hiện tại và ngày có giao dịch liền trước" (mỗi
ngày là một nhóm peers khi `ORDER BY txn_date`):

```sql
-- PostgreSQL 11+
SELECT account, txn_date, id, amount,
       sum(amount) OVER (PARTITION BY account ORDER BY txn_date
                         GROUPS BETWEEN 1 PRECEDING AND CURRENT ROW) AS sum_2_days
FROM transactions
ORDER BY account, txn_date, id;
-- A 03-01: 100 | A 03-02 (cả hai dòng): 120 | A 03-04: 40 | B 03-01: 200 | B 03-03: 150
```

Dòng A 03-04: nhóm hiện tại là {20}, nhóm liền trước là ngày 03-02 {50, -30}, tổng 40. Trên MySQL không
có `GROUPS`; cách gần nhất là gộp theo ngày bằng `GROUP BY` trước, rồi dùng `ROWS` trên các dòng đã gộp
(mỗi ngày một dòng).

**`EXCLUDE CURRENT ROW`**, ví dụ "lương trung bình của các đồng nghiệp khác cùng phòng":

```sql
-- PostgreSQL 11+
SELECT dept, name, salary,
       avg(salary) OVER (PARTITION BY dept
                         ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                         EXCLUDE CURRENT ROW) AS colleagues_avg
FROM employees;
```

Khoa (một mình phòng `ops`) có frame rỗng nên `colleagues_avg` là NULL. MySQL làm bằng cách tự trừ như
mục 8.5.

**NULL trong `ORDER BY`** là chỗ dễ gây khác kết quả khi chuyển câu truy vấn giữa hai hệ. Với
`ROW_NUMBER() OVER (ORDER BY bonus)` mà cột `bonus` có NULL, MySQL cho các dòng NULL số 1, 2...,
PostgreSQL đẩy chúng xuống cuối. Muốn hai bên giống nhau thì ghi rõ: PostgreSQL viết
`ORDER BY bonus NULLS LAST`; MySQL viết `ORDER BY bonus IS NULL, bonus` (biểu thức `bonus IS NULL` là 0
với dòng có giá trị, 1 với dòng NULL, nên dòng NULL xuống cuối).

**Hàm ngày giờ** trong chương là của MySQL; đổi khi chạy trên PostgreSQL: `DATEDIFF(a, b)` thành `a - b`
(hai `date` trừ nhau ra số ngày), `login_date - INTERVAL rn DAY` thành `login_date - rn::int`,
`MONTH(d)` thành `EXTRACT(MONTH FROM d)`, và trong recursive CTE sinh lịch dùng `day + 1` để giữ kiểu
`date`.

**Top-N dừng sớm.** Theo Markus Winand (Use The Index, Luke!), khi phân trang hoặc lấy top-N bằng
`ROW_NUMBER` rồi lọc `rn <= N` ở tầng ngoài, PostgreSQL từ bản 15 (cùng Oracle, SQL Server) có thể dừng
đọc index khi đã đủ dòng, còn MySQL thì không, nên trên MySQL kiểu câu này kém hiệu quả với bảng lớn.
Đây là lý do thực tế để dùng `LIMIT` (hoặc `LATERAL ... LIMIT` cho từng nhóm) trên MySQL khi chỉ cần vài
dòng đầu.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Lọc theo window function trong `WHERE` / `HAVING` (lỗi 3593, 3594, hoặc 1054 khi dùng alias) | Window chạy sau `WHERE`, `GROUP BY`, `HAVING` | Tính ở CTE / derived table, lọc ở tầng ngoài (mục 4.3) |
| Tưởng `ORDER BY` trong `OVER` sắp luôn kết quả | Nó chỉ sắp bên trong partition cho hàm xử lý | Luôn có `ORDER BY` ở cuối câu nếu cần thứ tự |
| `ROW_NUMBER` cho kết quả khác nhau giữa các lần chạy | Peers nhận số tuỳ ý | Thêm tie-breaker duy nhất (khoá chính) vào `ORDER BY` |
| `RANK` / `DENSE_RANK` không còn đồng hạng | Lỡ thêm tie-breaker vào `ORDER BY` | Chỉ để các cột định nghĩa "bằng nhau" |
| Running total "nhảy bậc", hai dòng cùng ngày cùng số | Frame mặc định là `RANGE ... CURRENT ROW`, gồm cả peers | `ROWS UNBOUNDED PRECEDING` + tie-breaker; hoặc giữ `RANGE` nếu muốn số theo ngày (mục 8.4) |
| `LAST_VALUE` trả về chính dòng hiện tại | Frame mặc định dừng ở dòng hiện tại | Ghi frame tới `UNBOUNDED FOLLOWING`, hoặc `FIRST_VALUE` với thứ tự đảo |
| Thêm `ORDER BY` vào `OVER` làm `SUM` đổi nghĩa | Frame mặc định đổi khi có `ORDER BY` | Ghi frame rõ ràng |
| `LAG` "so với hôm qua" nhưng so nhầm với ngày trước nữa | `LAG` lấy dòng liền trước, không biết lịch | Kiểm tra khoảng cách bằng `LAG(ngày)`, hoặc lấp đủ lịch trước (mục 11.4) |
| "Trung bình 7 ngày" bằng `ROWS 6 PRECEDING` sai khi thiếu ngày | `ROWS` đếm dòng | `RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT ROW`, hoặc lấp lịch |
| Đặt điều kiện lọc ở sai tầng | `WHERE` ở tầng trong làm window không nhìn thấy dòng bị loại | Hỏi: dòng bị loại có cần được tính vào window không? (mục 4.4) |
| Dùng `RANK` hoặc `ROW_NUMBER` để tìm "giá trị lớn thứ N" | `RANK` bỏ trống hạng, `ROW_NUMBER` đếm cả người trùng | `DENSE_RANK` (mục 11.3) |
| Gaps and islands ra đảo sai | Có dòng trùng ngày nên số thứ tự lệch | `DISTINCT` trước, hoặc `DENSE_RANK` |
| `so - ROW_NUMBER() OVER (...)` báo lỗi 1690 | `ROW_NUMBER` là `BIGINT UNSIGNED`, phép trừ ra âm | `CAST(ROW_NUMBER() OVER (...) AS SIGNED)` |
| `COUNT(DISTINCT x) OVER (...)` báo lỗi 1235 | MySQL không hỗ trợ `DISTINCT` trong aggregate window | `GROUP BY` ở tầng riêng rồi `JOIN`, hoặc mẹo hai `DENSE_RANK` (mục 7.1) |
| `NTILE` tách hai người cùng giá trị vào hai nhóm | `NTILE` chia theo số dòng | Dùng ngưỡng trên `PERCENT_RANK` / `CUME_DIST` |
| Câu window chậm trên bảng lớn | Tầng trong tính cho mọi dòng, sort và đệm dòng | Lọc sớm ở tầng trong, cân nhắc `LATERAL ... LIMIT`, đo bằng `EXPLAIN ANALYZE` |
| Giả lập xếp hạng bằng biến `@rn := @rn + 1` | Deprecated, thứ tự đánh giá không xác định | Dùng window function |

## Tóm tắt chương

- Window function tính cho **mỗi dòng** một giá trị từ một tập dòng liên quan (window), **không gộp
  dòng** như `GROUP BY`. Dấu hiệu nhận biết: có `OVER` sau lời gọi hàm.
- `OVER (PARTITION BY ... ORDER BY ... frame)`: `PARTITION BY` chia nhóm độc lập, `ORDER BY` xếp thứ tự
  bên trong nhóm (không xếp kết quả), frame chọn tập con của nhóm mà hàm nhìn thấy. `OVER ()` là cả
  kết quả.
- Window function chạy sau `WHERE`/`GROUP BY`/`HAVING`, trước `SELECT DISTINCT`/`ORDER BY`/`LIMIT`, chỉ
  viết được ở danh sách `SELECT` và `ORDER BY`. Muốn lọc theo nó: thêm một tầng (CTE hoặc derived
  table). Tham số của window function được chứa aggregate (`SUM(SUM(x)) OVER ()`), ngược lại thì không.
- Xếp hạng: `ROW_NUMBER` (1, 2, 3, 4, cần tie-breaker), `RANK` (1, 2, 2, 4), `DENSE_RANK` (1, 2, 2, 3),
  `NTILE(n)` (chia nhóm theo số dòng), `PERCENT_RANK`, `CUME_DIST` (vị trí tương đối 0..1).
- Lấy giá trị: `LAG`/`LEAD` (dòng trước/sau, có default), `FIRST_VALUE`/`LAST_VALUE`/`NTH_VALUE` (theo
  frame). MySQL chỉ có `RESPECT NULLS`; forward fill làm bằng `COUNT(col)` cộng dồn rồi `MAX` theo nhóm.
- Aggregate + `OVER`: chỉ số của nhóm trên từng dòng, running total, trung bình trượt. Không có
  `DISTINCT`, không có `GROUP_CONCAT`.
- Frame: `ROWS` đếm dòng, `RANGE` đo giá trị (và `CURRENT ROW` gồm cả peers). Mặc định: không
  `ORDER BY` là cả partition; có `ORDER BY` là "từ đầu tới dòng hiện tại cùng peers", gây ra running
  total nhảy bậc và `LAST_VALUE` sai. Có `ORDER BY` thì ghi frame ra.
- `WINDOW w AS (...)` đặt tên để dùng lại; kế thừa chỉ được thêm, không được sửa; dùng tên còn giúp
  optimizer không phải tính lặp các window giống nhau.
- Chi phí chính là sort và đệm dòng; CTE chứa window function luôn được materialize nên tầng trong
  tính cho mọi dòng nó đọc. Lọc sớm, và với top-N trên bảng lớn cân nhắc `LATERAL ... LIMIT`.
- Bài kinh điển: top N mỗi nhóm (hỏi rõ cách xử lý đồng hạng), running total và chạm ngưỡng, giá trị
  lớn thứ N (`DENSE_RANK`), so với kỳ trước (coi chừng thiếu kỳ), gaps and islands (`ngày - số thứ
  tự`, hoặc đánh dấu rồi cộng dồn).

## Câu hỏi tự kiểm tra

1. Cùng là `SUM(salary)`, khi nào nó gộp dòng và khi nào không? Một câu `SELECT` có thể vừa có
   `GROUP BY` vừa có window function không, và khi đó window function nhìn thấy những dòng nào? (mục 4.5)
2. Vì sao `WHERE ROW_NUMBER() OVER (...) <= 3` lỗi, còn `ORDER BY ROW_NUMBER() OVER (...)` thì không?
3. Hai dòng có cùng lương: `ROW_NUMBER`, `RANK`, `DENSE_RANK` cho hai dòng đó giá trị gì, và dòng đứng
   ngay sau chúng nhận giá trị gì với mỗi hàm?
4. Câu `SELECT name, LAST_VALUE(name) OVER (ORDER BY salary) FROM employees` trả về gì ở mỗi dòng, và
   tại sao? Sửa thế nào để ra tên người lương cao nhất? (mục 8.4)
5. Giải thích vì sao `SUM(amount) OVER (ORDER BY txn_date)` cho hai giao dịch cùng ngày cùng một số dư.
   Khi nào đó là kết quả bạn muốn?
6. `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` và `RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT
   ROW` khác nhau thế nào trên một bảng doanh thu thiếu vài ngày?
7. Với mẫu "CTE đánh số rồi lọc `rn <= 3` ở ngoài", tầng trong xử lý bao nhiêu dòng? Đặt điều kiện
   `dept = 'eng'` ở tầng trong hay tầng ngoài có làm đổi kết quả không? Còn điều kiện `salary > 2000`?
   (mục 4.4, 10.2)
8. Tại sao kỹ thuật `ngày - ROW_NUMBER()` tìm được các chuỗi ngày liên tiếp? Nó hỏng khi nào?
9. Vì sao `id - ROW_NUMBER() OVER (ORDER BY id)` có thể báo lỗi trên MySQL mà không lỗi trên
   PostgreSQL? (mục 11.5)
10. Kể ba tính năng window function PostgreSQL có mà MySQL 8.4 không có, và cách viết thay thế trên
    MySQL cho mỗi cái.

## Bài tập

Làm trên database `ch10` của chương (bài 2 và 4 tự tạo thêm bảng). Tự kiểm tra kết quả bằng cách tính
tay trên dữ liệu nhỏ trước khi tin vào câu truy vấn.

**Bài 1. Lịch sử đơn hàng.** Tạo bảng và dữ liệu:

```sql
CREATE TABLE orders (
  id          INT PRIMARY KEY,
  customer_id INT NOT NULL,
  ordered_at  DATE NOT NULL,
  total       INT NOT NULL
);
INSERT INTO orders VALUES
  (1, 1, '2026-01-03', 300), (2, 1, '2026-01-20', 150), (3, 1, '2026-02-11', 300),
  (4, 2, '2026-01-05', 500), (5, 2, '2026-03-01',  80),
  (6, 3, '2026-02-02', 120);
```

Viết **một** câu truy vấn trả về mỗi đơn kèm: số thứ tự đơn của khách (đơn đầu tiên là 1), tổng số đơn
của khách, số ngày kể từ đơn trước của cùng khách (`NULL` với đơn đầu), tổng chi tiêu luỹ kế của khách
tính tới đơn đó, và hạng của đơn theo giá trị trong các đơn của khách (đơn bằng giá trị thì đồng hạng).
Sau đó viết câu thứ hai chỉ lấy 2 đơn gần nhất của mỗi khách.

**Bài 2. Mức lương cao thứ hai, kể cả phòng không có.** Viết câu truy vấn liệt kê **mọi** phòng ban
cùng mức lương cao thứ hai của phòng đó; phòng chỉ có một mức lương (`ops`) phải hiện ra với `NULL`.
Thêm một nhân viên mới vào phòng `ops` với lương 1500 (bằng Khoa) và kiểm tra kết quả vẫn đúng.

**Bài 3. Thời gian máy chủ ngừng hoạt động.** Tạo bảng:

```sql
CREATE TABLE health_checks (
  checked_at DATETIME PRIMARY KEY,
  status     VARCHAR(4) NOT NULL         -- 'up' hoặc 'down'
);
INSERT INTO health_checks VALUES
  ('2026-06-01 10:00:00', 'up'),   ('2026-06-01 10:01:00', 'down'),
  ('2026-06-01 10:02:00', 'down'), ('2026-06-01 10:03:00', 'up'),
  ('2026-06-01 10:04:00', 'down'), ('2026-06-01 10:05:00', 'down'),
  ('2026-06-01 10:06:00', 'down'), ('2026-06-01 10:07:00', 'up');
```

Tìm từng đợt `down` liên tiếp: thời điểm bắt đầu, thời điểm kết thúc, số lần kiểm tra trong đợt. Rồi
tìm đợt dài nhất. Làm bằng cách "đánh dấu điểm đầu đảo rồi cộng dồn" ở mục 11.5. Thử thêm: lấy
`ROW_NUMBER()` trên toàn bảng trừ đi `ROW_NUMBER()` trong từng `status` (cả hai sắp theo thời gian); tự
giải thích vì sao hiệu này là hằng số trong một đợt, rồi so sánh độ dễ đọc của hai cách.

**Bài 4. Đo hiệu năng top N mỗi nhóm.** Sinh một bảng lớn:

```sql
SET SESSION cte_max_recursion_depth = 300000;   -- mặc định 1000, không đủ cho 200000 vòng
CREATE TABLE big_orders (
  id          INT PRIMARY KEY,
  customer_id INT NOT NULL,
  total       INT NOT NULL
);
INSERT INTO big_orders
WITH RECURSIVE seq (n) AS (
  SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 200000
)
SELECT n, 1 + (n * 7919) % 1000, (n * 104729) % 100000 FROM seq;
```

(a) Lấy 3 đơn có `total` lớn nhất của **mỗi** khách bằng `ROW_NUMBER`. (b) Làm lại bằng `LATERAL ...
LIMIT 3`, lần đầu chưa có index, sau đó thêm index `(customer_id, total)`. (c) Lặp lại (a) và (b) nhưng
chỉ cho 5 khách hàng. Đo bốn trường hợp bằng `EXPLAIN ANALYZE` (chương 12), ghi lại thời gian và rút ra
khi nào cách nào nhanh hơn.

## Đọc thêm

- MySQL 8.4 Reference Manual, mục Window Functions:
  [Window Functions](https://dev.mysql.com/doc/refman/8.4/en/window-functions.html),
  [Window Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/window-function-descriptions.html),
  [Window Function Concepts and Syntax](https://dev.mysql.com/doc/refman/8.4/en/window-functions-usage.html),
  [Window Function Frame Specification](https://dev.mysql.com/doc/refman/8.4/en/window-functions-frames.html),
  [Named Windows](https://dev.mysql.com/doc/refman/8.4/en/window-functions-named-windows.html),
  [Window Function Restrictions](https://dev.mysql.com/doc/refman/8.4/en/window-function-restrictions.html).
- MySQL 8.4: [Window Function Optimization](https://dev.mysql.com/doc/refman/8.4/en/window-function-optimization.html),
  [Aggregate Function Descriptions](https://dev.mysql.com/doc/refman/8.4/en/aggregate-functions.html),
  [Lateral Derived Tables](https://dev.mysql.com/doc/refman/8.4/en/lateral-derived-tables.html),
  [Derived Condition Pushdown Optimization](https://dev.mysql.com/doc/refman/8.4/en/derived-condition-pushdown-optimization.html),
  [Out-of-Range and Overflow Handling](https://dev.mysql.com/doc/refman/8.4/en/out-of-range-and-overflow.html)
  (phép trừ số không dấu), [User-Defined Variables](https://dev.mysql.com/doc/refman/8.4/en/user-variables.html).
- Mã nguồn MySQL 8.4 (để kiểm tra các chi tiết bên trong nêu ở mục 5.1, 8, 9, 10):
  [sql/window.cc](https://github.com/mysql/mysql-server/blob/8.4/sql/window.cc),
  [sql/item_sum.h](https://github.com/mysql/mysql-server/blob/8.4/sql/item_sum.h),
  [share/messages_to_clients.txt](https://github.com/mysql/mysql-server/blob/8.4/share/messages_to_clients.txt)
  (nội dung các thông báo lỗi).
- PostgreSQL 18: [Tutorial: Window Functions](https://www.postgresql.org/docs/18/tutorial-window.html),
  [Window Function Calls](https://www.postgresql.org/docs/18/sql-expressions.html#SYNTAX-WINDOW-FUNCTIONS),
  [Window Functions](https://www.postgresql.org/docs/18/functions-window.html),
  [SELECT: WINDOW Clause](https://www.postgresql.org/docs/18/sql-select.html#SQL-WINDOW).
- Markus Winand: [Using Window Functions for Efficient Pagination](https://use-the-index-luke.com/sql/partial-results/window-functions)
  (Use The Index, Luke!), [The FILTER clause](https://modern-sql.com/feature/filter) và
  [QUALIFY: hệ nào hỗ trợ](https://modern-sql.com/caniuse/qualify) (modern-sql.com).
- Laravel 13, cách eager loading có `limit` sinh `ROW_NUMBER`:
  [Query/Grammars/Grammar.php](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Database/Query/Grammars/Grammar.php)
  (hàm `compileGroupLimit`).
