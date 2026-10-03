# Chương 20. Hiệu năng và profiling

> [← Mục lục](README.md) · [← Chương 19: Bên trong Zend Engine](19-ben-trong-engine.md) · [Chương 21: Chất lượng code: test, phân tích tĩnh, chuẩn code →](21-chat-luong-code.md)

**Bạn sẽ học được:**

- "Nhanh" nghĩa là gì khi nói về một ứng dụng web: latency, throughput, percentile, và vì sao phải
  đo trước khi sửa.
- Phân biệt bốn loại nút thắt (I/O, database, CPU, bộ nhớ) và cách nhận ra mình đang gặp loại nào.
- Tự đo bằng `hrtime()`, `memory_get_peak_usage()`; dùng profiler (Xdebug, SPX, Blackfire, Tideways)
  và đọc được flame graph.
- Các tối ưu mang lại nhiều nhất trong ứng dụng PHP: OPcache, autoloader tối ưu, bỏ N+1, cache,
  generator cho dữ liệu lớn, chọn đúng cấu trúc dữ liệu, và các lệnh cache của Laravel.
- PHP làm nhiều việc cùng lúc bằng cách nào: `Http::pool`, process song song, Fibers, và các runtime
  bất đồng bộ như Swoole, ReactPHP.

**Cần biết trước:** [Chương 02: PHP chạy như thế nào](02-php-chay-nhu-the-nao.md) (opcode, OPcache,
share-nothing), [Chương 06: Mảng](06-mang.md), [Chương 13: Generator, iterator và SPL](13-generator-iterator-spl.md),
[Chương 16: PHP làm việc với database](16-php-va-database.md). Đọc thêm
[Chương 18](18-fpm-nginx-opcache.md) và [Chương 19](19-ben-trong-engine.md) sẽ hiểu sâu hơn phần
OPcache và bộ nhớ, nhưng không bắt buộc.

Cách chạy ví dụ: lưu thành file `.php` rồi chạy `php ten-file.php`. Ví dụ viết cho PHP 8.5. Máy chưa
cài PHP thì dùng Docker, chạy trong thư mục chứa file:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

⚠️ Chương này có nhiều con số thời gian (ms, µs). Thời gian đo được phụ thuộc máy, phiên bản PHP, có
OPcache/JIT hay không, máy đang bận gì. Các con số thời gian và bộ nhớ trong comment đều là **output minh hoạ**
đo trên môi trường thử (php-wasm 32-bit, khác máy 64-bit thật) trong một lần chạy: bạn chạy lại sẽ ra số khác. Điều cần để ý là **tỉ lệ** giữa các cách làm, không
phải con số tuyệt đối. Những output không phụ thuộc thời gian (số query, số phần tử, kết quả tính
toán) thì giống hệt khi bạn chạy.

## 1. Hiệu năng là gì và vì sao phải đo trước

### 1.1 "Nhanh" nghĩa là gì

Khi người dùng nói "trang này chậm", họ đang nói về một trong vài thứ khác nhau. Cần tách bạch, vì
mỗi thứ có cách đo và cách sửa riêng:

| Khái niệm | Nghĩa (lời thường) | Đơn vị hay dùng | Ví dụ |
|---|---|---|---|
| *Latency* (độ trễ, *response time*) | Một request mất bao lâu từ lúc gửi tới lúc nhận đủ kết quả | ms | Trang danh sách đơn hàng mất 850 ms |
| *Throughput* (thông lượng) | Hệ thống xử lý được bao nhiêu việc trong một đơn vị thời gian | request/giây (RPS), job/phút | Server chịu được 400 request/giây |
| *Resource usage* (tài nguyên) | Mỗi việc tốn bao nhiêu CPU, RAM, kết nối DB | % CPU, MB, số connection | Mỗi worker PHP-FPM chiếm 60 MB |
| *Concurrency* (độ đồng thời) | Bao nhiêu việc đang được xử lý cùng một lúc | số request đang chạy | 50 request đang chờ DB |

Các đại lượng này liên quan nhưng không thay thế nhau:

- Giảm latency thường tăng throughput (mỗi worker rảnh sớm hơn, nhận được việc khác), nhưng không
  phải luôn luôn. Ví dụ cache một trang vào RAM giảm latency nhưng nếu cache quá nhiều thì RAM hết,
  phải giảm số worker, throughput giảm.
- Throughput có thể tăng mà latency không đổi: thêm server.
- Một hệ thống có thể nhanh khi vắng (latency thấp) nhưng sập khi đông (throughput không đủ), vì các
  request bắt đầu **xếp hàng** chờ nhau. Phần lớn sự cố "giờ cao điểm thì chậm" là chuyện xếp hàng,
  không phải code chậm đi.

Chương này tập trung vào latency của một request và tài nguyên của một process PHP, vì đó là phần
người viết code PHP kiểm soát trực tiếp. Phần throughput ở tầng hạ tầng (số worker FPM, hàng đợi,
timeout) nằm ở [Chương 18](18-fpm-nginx-opcache.md).

### 1.2 Trung bình đánh lừa: dùng percentile

Giả sử bạn đo 20 request vào cùng một endpoint. Phần lớn nhanh, nhưng có hai request rất chậm (có
thể do cache hết hạn đúng lúc đó, hoặc gặp lock trong DB). Hãy tính vài con số:

```php
<?php
declare(strict_types=1);

/**
 * Percentile theo phương pháp nearest-rank: sắp xếp tăng dần,
 * lấy phần tử thứ ceil(p/100 * n) (đếm từ 1).
 *
 * @param list<int|float> $values
 */
function percentile(array $values, float $p): float
{
    sort($values);
    $rank = (int) ceil($p / 100 * count($values));
    return $values[max($rank, 1) - 1];
}

// Thời gian phản hồi (ms) của 20 request vào cùng một endpoint
$ms = [80, 85, 90, 92, 95, 95, 98, 100, 100, 102,
       105, 110, 110, 115, 120, 125, 130, 140, 1500, 2400];

printf("trung bình: %.1f ms\n", array_sum($ms) / count($ms));
printf("p50: %.0f ms\n", percentile($ms, 50));
printf("p95: %.0f ms\n", percentile($ms, 95));
printf("p99: %.0f ms\n", percentile($ms, 99));

// in ra:
// trung bình: 289.6 ms
// p50: 102 ms
// p95: 1500 ms
// p99: 2400 ms
```

Đọc kết quả:

- *Trung bình* (mean) 289.6 ms không mô tả **ai cả**: 18 request nhanh hơn nhiều, 2 request chậm hơn
  nhiều. Trung bình bị vài giá trị cực lớn kéo lệch.
- *Percentile* thứ p (viết tắt pXX) là giá trị mà p% số mẫu nhỏ hơn hoặc bằng nó. *p50* (còn gọi là
  *median*, trung vị) 102 ms: một nửa số request xong trong 102 ms. *p95* 1500 ms: 5% request tệ nhất
  mất từ 1500 ms trở lên. *p99* là 1% tệ nhất.
- Người dùng cảm nhận được phần đuôi (*tail latency*): một trang web gọi 10 API, chỉ cần một API rơi
  vào p99 là cả trang chậm. Vì vậy các mục tiêu hiệu năng thường viết theo percentile: "p95 dưới
  300 ms".

Có vài cách tính percentile khác nhau (nearest-rank như trên, nội suy tuyến tính...), với ít mẫu thì
kết quả hơi khác nhau. Với hàng nghìn mẫu thì chênh lệch không đáng kể. Công cụ giám sát (APM, mục
4.7) tính sẵn cho bạn.

⚠️ Đừng so sánh trước và sau tối ưu bằng **một lần chạy**. Một lần chạy có thể rơi đúng lúc máy bận.
Chạy nhiều lần, so median và p95.

### 1.3 Đo trước khi tối ưu

Câu nổi tiếng của Donald Knuth (bài "Structured Programming with go to Statements", 1974):
"*premature optimization is the root of all evil*" (tối ưu sớm là gốc rễ của mọi điều tệ hại). Câu
này hay bị trích thiếu. Ý đầy đủ: lập trình viên tốn rất nhiều thời gian lo về tốc độ của những phần
**không quan trọng**, nên hãy quên các cải thiện nhỏ trong khoảng 97% trường hợp; nhưng đừng bỏ lỡ cơ
hội ở 3% quan trọng. Việc của bạn là **tìm ra** phần quan trọng đó rồi dồn sức vào đó.

Tại sao phải đo mà không đoán? Vì trực giác của lập trình viên về chỗ chậm thường sai, và vì lợi ích
của một tối ưu bị giới hạn bởi tỉ lệ thời gian của phần được tối ưu. Quy luật này có tên *định luật
Amdahl* (*Amdahl's law*): nếu phần chiếm tỉ lệ `p` của tổng thời gian được làm nhanh gấp `s` lần, thì
cả chương trình nhanh gấp:

```
                1
speedup = ─────────────────
          (1 - p) + p / s
```

Thử với một request 1000 ms:

```php
<?php
declare(strict_types=1);

// Định luật Amdahl: phần p của tổng thời gian được tăng tốc s lần
function overallSpeedup(float $p, float $s): float
{
    return 1 / ((1 - $p) + $p / $s);
}

$total = 1000.0; // ms
foreach ([[0.02, 2.0], [0.02, 100.0], [0.70, 2.0], [0.70, 10.0]] as [$p, $s]) {
    $speedup = overallSpeedup($p, $s);
    printf("phần %2.0f%% nhanh gấp %5.1f lần -> tổng %6.1f ms (nhanh gấp %.2f lần)\n",
        $p * 100, $s, $total / $speedup, $speedup);
}

// in ra:
// phần  2% nhanh gấp   2.0 lần -> tổng  990.0 ms (nhanh gấp 1.01 lần)
// phần  2% nhanh gấp 100.0 lần -> tổng  980.2 ms (nhanh gấp 1.02 lần)
// phần 70% nhanh gấp   2.0 lần -> tổng  650.0 ms (nhanh gấp 1.54 lần)
// phần 70% nhanh gấp  10.0 lần -> tổng  370.0 ms (nhanh gấp 2.70 lần)
```

Một hàm chiếm 2% thời gian, bạn có làm nó nhanh gấp 100 lần thì request cũng chỉ nhanh hơn 2%. Ngược
lại, chỉ cần làm phần chiếm 70% nhanh gấp đôi là đã giảm 350 ms. Muốn biết phần nào chiếm 70% thì
phải đo.

⚠️ Cạm bẫy kinh điển trong PHP: đổi `array_map` sang `foreach`, đổi nháy kép sang nháy đơn, bỏ
Collection của Laravel... vì "nghe nói nhanh hơn", trong khi request đó tốn 90% thời gian chờ
database. Các thay đổi kiểu đó làm code khó đọc hơn mà người dùng không thấy khác biệt.

Điều này **không** có nghĩa là được phép viết code chậm một cách vô lý. Chọn thuật toán O(n) thay vì
O(n²), không query trong vòng lặp, không nạp cả bảng vào RAM: đó là thiết kế đúng ngay từ đầu, không
phải "tối ưu sớm". Mục 6 nói về những thói quen như vậy.

### 1.4 Quy trình sáu bước

Đây là quy trình nên làm theo mỗi khi gặp "endpoint này chậm":

```
 ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
 │ 1. Đo, khoanh    │──▶│ 2. Phân rã thời  │──▶│ 3. Tái hiện với  │
 │ vùng (APM, log,  │   │ gian: DB? HTTP?  │   │ dữ liệu cỡ thật  │
 │ p95, lúc nào)    │   │ CPU? chờ worker? │   │ (local/staging)  │
 └──────────────────┘   └──────────────────┘   └────────┬─────────┘
                                                        │
 ┌──────────────────┐   ┌──────────────────┐   ┌────────▼─────────┐
 │ 6. Đo lại cùng   │◀──│ 5. Sửa chỗ tốn   │◀──│ 4. Profile: hàm  │
 │ điều kiện, so    │   │ nhất, từng thay  │   │ nào, query nào   │
 │ trước/sau        │   │ đổi một          │   │ tốn nhất         │
 └──────────────────┘   └──────────────────┘   └──────────────────┘
```

1. **Đo và khoanh vùng.** Endpoint nào chậm, chậm bao nhiêu (p95, p99), chậm lúc nào: luôn luôn, hay
   chỉ giờ cao điểm, hay chỉ với một số khách hàng (ví dụ khách có 50.000 đơn hàng). Dữ liệu này đến
   từ log hoặc công cụ giám sát.
2. **Phân rã thời gian.** Một request chậm gồm những phần nào: chờ worker rảnh, thời gian query DB,
   thời gian gọi HTTP ra ngoài, thời gian CPU của PHP. Mục 2 nói về các loại này.
3. **Tái hiện** ở nơi bạn được phép đo kỹ (máy local, staging) với dữ liệu cỡ gần thật. Endpoint
   chậm vì bảng 10 triệu dòng sẽ nhanh vèo trên máy dev chỉ có 100 dòng.
4. **Profile** để biết chính xác hàm nào, query nào tốn thời gian (mục 4 và 5).
5. **Sửa chỗ tốn nhất**, mỗi lần một thay đổi, để biết thay đổi nào có tác dụng.
6. **Đo lại cùng điều kiện** (cùng dữ liệu, cùng tải, cùng số lần lặp) và so sánh với số đo trước.
   Không có số trước và sau thì chưa thể nói là đã cải thiện.

Lặp lại cho tới khi đạt mục tiêu đã đặt ra (ví dụ p95 dưới 300 ms). Có mục tiêu cụ thể để biết lúc
nào **dừng**: tối ưu không có điểm kết thúc nếu không đặt ra.

## 2. Các loại nút thắt

*Nút thắt* (*bottleneck*) là phần chậm nhất trên đường đi của một việc, phần quyết định tổng thời
gian. Giống cổ chai: thân chai to bao nhiêu thì nước cũng chỉ chảy ra nhanh bằng cổ chai. Tối ưu chỗ
không phải nút thắt thì không thay đổi gì (định luật Amdahl ở mục 1.3).

### 2.1 Một request PHP tiêu thời gian vào đâu

Nhắc lại từ [Chương 02](02-php-chay-nhu-the-nao.md): mỗi request vào PHP-FPM được một worker nhận,
chạy script từ đầu tới cuối rồi dọn sạch (mô hình *share-nothing*). Thời gian của một request điển
hình trong ứng dụng Laravel chia ra như sau (minh hoạ):

```
Nginx nhận request
  │
  ├─ [chờ worker rảnh]      ← hàng đợi FPM: 0 ms lúc vắng, hàng giây lúc quá tải
  │
  ├─ bootstrap framework     ← nạp file, autoload class, đọc config, đăng ký provider
  │                            (OPcache, autoloader tối ưu, config:cache làm phần này nhỏ lại)
  ├─ middleware, routing
  │
  ├─ controller
  │    ├─ query DB #1  ─────────── chờ MySQL
  │    ├─ query DB #2..#51 ─────── chờ MySQL (vòng lặp N+1?)
  │    ├─ gọi API thanh toán ───── chờ mạng
  │    └─ xử lý dữ liệu ────────── CPU của PHP
  │
  ├─ render view / json_encode   ← CPU
  │
  └─ gửi response, dọn dẹp
```

Có thể xếp mọi nút thắt vào bốn nhóm: I/O, database (một dạng I/O đặc biệt quan trọng nên tách
riêng), CPU, bộ nhớ. Thêm một nhóm thứ năm nằm ngoài code: **chờ worker** khi tất cả worker đều bận.

### 2.2 I/O: chờ thế giới bên ngoài

*I/O* (*input/output*) là mọi thao tác đọc ghi ra ngoài CPU và RAM: gọi HTTP sang API khác, đọc ghi
file, gửi mail qua SMTP, đọc Redis, và cả query database. Đặc điểm chung: CPU gần như **không làm gì**,
process chỉ ngồi chờ dữ liệu về.

PHP mặc định chạy I/O kiểu *blocking* (chặn): gọi `file_get_contents('https://...')` thì dòng code
tiếp theo chỉ chạy khi có kết quả hoặc hết timeout. Trong lúc chờ, worker FPM đó vẫn bị chiếm, không
nhận request khác được. Vì vậy I/O chậm gây hai hậu quả:

1. Request đó chậm (latency).
2. Worker bị giữ lâu, hệ thống ít worker rảnh hơn, các request khác phải xếp hàng (throughput).

Một API bên ngoài bị treo 30 giây có thể làm toàn bộ pool FPM bị chiếm hết và cả trang web "sập",
dù CPU server gần như rảnh. Đây là lý do mọi lời gọi ra ngoài phải có **timeout**.

Các hướng xử lý (từ dễ tới khó):

- Đặt timeout ngắn và hợp lý cho mọi lời gọi mạng.
- Gọi ít lần hơn: gộp nhiều lời gọi thành một (API có endpoint batch), cache kết quả (mục 6.4).
- Gọi **đồng thời** thay vì tuần tự (mục 8).
- Không làm trong request: đẩy sang queue (gửi mail, gọi webhook), trả response ngay cho người dùng.

### 2.3 Database: nút thắt hay gặp nhất

Với các ứng dụng web kiểu CRUD (tạo, đọc, sửa, xoá dữ liệu), thời gian chờ database thường chiếm
phần lớn latency. Các nguyên nhân hay gặp:

| Nguyên nhân | Dấu hiệu | Đọc thêm |
|---|---|---|
| *N+1 query*: query trong vòng lặp, mỗi phần tử một query | Một request chạy hàng chục, hàng trăm query giống nhau chỉ khác tham số | Mục 6.3, [Chương 16](16-php-va-database.md), [Chương 27](27-laravel-database-eloquent.md) |
| Thiếu index, query quét cả bảng | Một query đơn lẻ chậm, càng nhiều dữ liệu càng chậm | [Database 11: Index](../database/11-index.md), [Database 12: EXPLAIN](../database/12-explain-toi-uu-query.md) |
| Lấy quá nhiều dữ liệu: `SELECT *` cả bảng, không phân trang | Query trả về hàng nghìn dòng, PHP tốn RAM và CPU để biến chúng thành object | Mục 6.5 |
| Chờ lock: transaction khác đang giữ dòng | Query đơn giản nhưng thỉnh thoảng mất vài giây | [Database 15: Lock và deadlock](../database/15-lock-deadlock.md) |
| Hết connection, chờ kết nối | Lỗi "Too many connections", latency tăng khi đông | [Chương 16](16-php-va-database.md) |

Điểm cần nhớ: **số lượng** query thường quan trọng hơn tốc độ từng query. Một query 1 ms chạy 300 lần
là 300 ms, chưa kể chi phí mạng mỗi lần đi về (*round trip*) giữa PHP và MySQL.

### 2.4 CPU: PHP đang tính toán

Nút thắt CPU là khi process PHP thật sự bận tính: CPU chạy liên tục, không chờ ai. Trong ứng dụng web,
nguồn tốn CPU thường là:

- Biến hàng nghìn dòng DB thành object (*hydration*) Eloquent, rồi biến ngược thành JSON.
- `json_encode`/`json_decode`, `serialize`/`unserialize` trên dữ liệu lớn.
- Render template phức tạp.
- Thuật toán kém trên dữ liệu lớn: vòng lặp lồng nhau O(n²), `in_array` trong vòng lặp (mục 6.6).
- Regex phức tạp, xử lý ảnh, tạo PDF, nén dữ liệu.
- Băm mật khẩu: `password_hash()` và `password_verify()` **cố ý** chậm để chống dò mật khẩu.
  ⚠️ Đừng bao giờ "tối ưu" bằng cách giảm `cost`; đó là tính năng bảo mật, không phải lỗi hiệu năng.

Hướng xử lý: giảm lượng việc (lấy ít dữ liệu hơn, xử lý ít phần tử hơn), dùng thuật toán và cấu trúc
dữ liệu tốt hơn, cache kết quả tính toán, đưa việc nặng sang queue. JIT của PHP chỉ có thể giúp nhóm
này, không giúp I/O (mục 6.8).

### 2.5 Bộ nhớ

Mỗi process PHP có giới hạn bộ nhớ đặt bằng `memory_limit` trong `php.ini` (giá trị mặc định là
`128M`). Vượt giới hạn là **fatal error**, script dừng ngay:

```php
<?php
declare(strict_types=1);

ini_set('memory_limit', '16M');   // hạ thấp để thấy lỗi nhanh

$rows = [];
for ($i = 0; $i < 1_000_000; $i++) {
    $rows[] = ['id' => $i, 'name' => "user$i"];   // giữ một triệu mảng con trong RAM
}
echo count($rows), "\n";

// in ra (output minh hoạ (php-wasm 32-bit), đường dẫn rút gọn; số "tried to allocate" tuỳ máy):
// Fatal error: Allowed memory size of 16777216 bytes exhausted (tried to allocate 20480 bytes) in .../p4.php on line 8
// Stack trace:
// #0 {main}
```

Hai điều cần hiểu:

- Con số "tried to allocate" chỉ là lần cấp phát **cuối cùng**, giọt nước tràn ly. Thủ phạm là toàn bộ
  dữ liệu đã tích luỹ trước đó, ở đây là mảng `$rows`. Đừng tìm lỗi ở dòng báo lỗi; hãy tìm thứ đang
  chiếm RAM.
- Bộ nhớ ảnh hưởng tới throughput chứ không chỉ một request: server có 4 GB RAM, mỗi worker FPM dùng
  tối đa 100 MB thì chỉ chạy được khoảng 40 worker cùng lúc. Giảm bộ nhớ mỗi request là tăng số
  worker chạy được ([Chương 18](18-fpm-nginx-opcache.md) tính cỡ pool theo RAM).

Nguồn tốn bộ nhớ hay gặp: nạp cả bảng (`Model::all()`), `file_get_contents()` một file vài trăm MB,
gom kết quả vào mảng lớn rồi mới xử lý. Cách chữa chung là xử lý **từng phần** (*streaming*): đọc một
ít, xử lý, bỏ đi, đọc tiếp. Generator (mục 6.5) là công cụ chính trong PHP.

⚠️ Đừng "chữa" bằng cách tăng `memory_limit` lên `-1` (không giới hạn) hay vài GB. Script vẫn ngốn RAM
như cũ, chỉ là giờ nó có thể làm cả server hết RAM thay vì chết một mình.

### 2.6 Chờ hay tính: wall time và CPU time

Làm sao biết một đoạn code chậm vì chờ (I/O, DB) hay vì tính (CPU)? So hai loại thời gian:

- *Wall time* (*wall-clock time*): thời gian thực trôi qua, như nhìn đồng hồ treo tường.
- *CPU time*: thời gian CPU thực sự chạy code của process. Gồm *user time* (chạy code của chương trình)
  và *system time* (kernel làm việc hộ, ví dụ đọc file).

Nếu wall time lớn hơn CPU time nhiều thì process đã **chờ** phần lớn thời gian. Nếu hai số xấp xỉ
nhau thì process **tính** suốt thời gian đó. Trong PHP, `getrusage()` (giao diện tới system call
`getrusage(2)`) trả về CPU time đã dùng:

```php
<?php
declare(strict_types=1);

/** Thời gian CPU (user + system) của process hiện tại, tính bằng ms */
function cpuMs(): float
{
    $r = getrusage();
    return ($r['ru_utime.tv_sec'] + $r['ru_stime.tv_sec']) * 1000
         + ($r['ru_utime.tv_usec'] + $r['ru_stime.tv_usec']) / 1000;
}

/** @param callable(): void $work */
function wallVsCpu(string $label, callable $work): void
{
    $wall0 = hrtime(true);           // nano giây, xem mục 3.2
    $cpu0  = cpuMs();
    $work();
    $wallMs = (hrtime(true) - $wall0) / 1e6;
    $cpuMs  = cpuMs() - $cpu0;
    printf("wall %6.1f ms | cpu %6.1f ms | %s\n", $wallMs, $cpuMs, $label);
}

// Giả lập chờ I/O: process ngủ, không dùng CPU
wallVsCpu('chờ I/O', function (): void {
    usleep(200_000); // 200 ms
});

// Tính toán thuần: CPU chạy liên tục
wallVsCpu('tính toán', function (): void {
    $x = 0;
    for ($i = 0; $i < 5_000_000; $i++) {
        $x += $i % 7;
    }
});

// in ra (output minh hoạ tự dựng theo hành vi trên Linux, số của bạn sẽ khác):
// wall  200.2 ms | cpu    0.1 ms | chờ I/O
// wall   61.4 ms | cpu   61.2 ms | tính toán
```

Profiler (mục 4) đo sẵn cả hai loại cho từng hàm. Nhìn thấy `PDOStatement::execute` có wall time lớn
mà CPU time nhỏ là biết ngay thời gian nằm ở phía MySQL.

⚠️ `getrusage()` trên Windows chỉ trả về một số trường (trong đó có `ru_utime.*` và `ru_stime.*`); một
số môi trường đặc biệt có thể trả về toàn số 0. Kiểm tra trước khi tin.

### 2.7 Bảng tổng hợp

| Loại | Dấu hiệu | Công cụ nhìn ra | Hướng xử lý |
|---|---|---|---|
| I/O (HTTP, file, mail) | Wall ≫ CPU; thời gian nằm ở `curl_exec`, `fread`, stream | Profiler, APM trace, log thời gian từng lời gọi | Timeout, cache, gọi đồng thời, đẩy sang queue |
| Database | Nhiều query/request, query đơn lẻ chậm | Đếm query (Debugbar, Telescope), slow query log, EXPLAIN | Eager loading, index, chỉ lấy cột/dòng cần, phân trang |
| CPU | CPU ≈ wall; CPU server cao | Profiler (exclusive time) | Thuật toán, cấu trúc dữ liệu, giảm lượng dữ liệu, cache kết quả |
| Bộ nhớ | Peak memory cao, fatal "Allowed memory size" | `memory_get_peak_usage()`, profiler có metric bộ nhớ | Streaming, generator, chunk |
| Chờ worker | Latency tăng vọt lúc đông, mọi endpoint cùng chậm | Status page của FPM (các trường `listen queue`, `max children reached`) | Giảm thời gian mỗi request, tăng worker/server ([Chương 18](18-fpm-nginx-opcache.md)) |

## 3. Tự đo bằng code: thời gian và bộ nhớ

Trước khi cài công cụ gì, PHP đã có sẵn vài hàm để đo. Chúng đủ dùng cho hai việc: đo một đoạn code
cụ thể mà bạn nghi ngờ, và so sánh hai cách viết (*micro-benchmark*).

### 3.1 `microtime(true)`: đồng hồ treo tường

`microtime(true)` trả về số giây kể từ *Unix epoch* (00:00:00 ngày 1/1/1970 GMT) dưới dạng `float`,
chính xác tới micro giây. Lấy hiệu hai lần gọi là ra thời gian trôi qua:

```php
<?php
declare(strict_types=1);

$t0 = microtime(true);          // giây kể từ 1970-01-01 (Unix epoch), dạng float
usleep(50_000);                 // ngủ 50 ms
$t1 = microtime(true);
printf("microtime: %.1f ms\n", ($t1 - $t0) * 1000);

// in ra (output minh hoạ): microtime: 50.1 ms
```

Gọi không có tham số, `microtime()` trả về **chuỗi** dạng `"0.65432100 1727940000"` (phần micro giây
trước, số giây sau). ⚠️ Trừ hai chuỗi đó cho nhau là sai, luôn truyền `true`.

Vấn đề của `microtime()`: nó đọc **giờ hệ thống**, mà giờ hệ thống có thể bị chỉnh giữa chừng (đồng bộ
NTP, người quản trị đổi giờ). Nếu giờ bị lùi lại trong lúc đo, hiệu số có thể ra âm hoặc sai lệch.
Manual PHP khuyên: để đo hiệu năng, dùng `hrtime()`.

### 3.2 `hrtime()`: đồng hồ bấm giờ

`hrtime()` (có từ PHP 7.3) trả về thời gian độ phân giải cao, tính từ **một mốc tuỳ ý** (thường là
lúc máy khởi động). Hai đặc điểm quan trọng:

- *Monotonic* (đơn điệu): luôn tăng, không bị chỉnh lùi như giờ hệ thống. Đúng thứ cần cho việc bấm
  giờ.
- Đơn vị nano giây. `hrtime(true)` trả về một số nguyên (trên hệ 64-bit); `hrtime()` không tham số trả
  về mảng `[giây, nano giây]`.

Vì mốc là tuỳ ý nên **giá trị đơn lẻ không có ý nghĩa**, chỉ hiệu hai lần gọi mới có nghĩa. Đừng dùng
`hrtime()` để biết bây giờ là mấy giờ.

```php
<?php
declare(strict_types=1);

$h0 = hrtime(true);             // nano giây kể từ một mốc tuỳ ý, kiểu int
usleep(50_000);
$h1 = hrtime(true);
printf("hrtime: %.1f ms\n", ($h1 - $h0) / 1e6);   // 1 ms = 1.000.000 ns

var_dump(is_int($h0));
print_r(hrtime());              // dạng mảng [giây, nano giây]

// in ra (output minh hoạ, hai số trong mảng tuỳ máy):
// hrtime: 50.2 ms
// bool(true)
// Array
// (
//     [0] => 81234
//     [1] => 255795708
// )
```

Trong ứng dụng web còn có `$_SERVER['REQUEST_TIME_FLOAT']`: thời điểm request bắt đầu (Unix
timestamp, chính xác tới micro giây). `microtime(true) - $_SERVER['REQUEST_TIME_FLOAT']` cho biết
request đã chạy được bao lâu tính tới dòng hiện tại, tiện để ghi log cuối request.

### 3.3 Viết một hàm đo nhỏ

Đo một lần thì kết quả dao động nhiều. Một hàm đo tử tế cần:

1. Chạy *warm-up* (khởi động) vài lần trước, không tính. Lần chạy đầu thường chậm hơn: file vừa được
   biên dịch, cache CPU còn lạnh, autoloader vừa nạp class.
2. Chạy nhiều lần, ghi thời gian từng lần.
3. Báo **median** (ít bị ảnh hưởng bởi lần chạy bất thường) và **min** (gần với chi phí thật nhất khi
   không bị gì làm phiền), thay vì trung bình.

```php
<?php
declare(strict_types=1);

/**
 * Chạy $fn nhiều lần, trả về thời gian (ms) của từng lần đã sắp xếp,
 * cùng median và min. Lần chạy khởi động (warm-up) không được tính.
 *
 * @param callable(): mixed $fn
 * @return array{median: float, min: float, runs: list<float>}
 */
function bench(callable $fn, int $runs = 7, int $warmup = 1): array
{
    for ($i = 0; $i < $warmup; $i++) {
        $fn();
    }

    $times = [];
    for ($i = 0; $i < $runs; $i++) {
        $start = hrtime(true);
        $fn();
        $times[] = (hrtime(true) - $start) / 1e6;
    }
    sort($times);

    return [
        'median' => $times[intdiv($runs, 2)],   // $runs lẻ nên phần tử giữa là median
        'min'    => $times[0],
        'runs'   => $times,
    ];
}

$data = range(1, 200_000);
shuffle($data);

$r = bench(function () use ($data): int {
    sort($data);                // sắp xếp bản sao: biến trong use được copy, mảng gốc vẫn xáo trộn
    return count($data);
});

printf("median %.2f ms, min %.2f ms\n", $r['median'], $r['min']);
echo implode(' ', array_map(fn (float $t): string => sprintf('%.2f', $t), $r['runs'])), "\n";

// in ra (output minh hoạ):
// median 26.44 ms, min 25.77 ms
// 25.77 26.05 26.36 26.44 26.50 26.66 26.74
```

Lưu ý dòng `sort($data)` trong closure: `use ($data)` bắt biến **theo giá trị** lúc tạo closure, nên mỗi
lần gọi closure nhận lại mảng đã xáo trộn ban đầu, `sort()` chỉ sắp xếp bản sao (copy-on-write, xem
[Chương 19](19-ben-trong-engine.md)). Nếu bạn viết `use (&$data)`, lần chạy thứ hai trở đi sẽ sắp xếp
một mảng **đã sắp xếp sẵn**, nhanh hơn hẳn, và kết quả đo vô nghĩa. Đây là loại lỗi rất hay gặp khi tự
viết benchmark: lần chạy sau không làm cùng một việc như lần chạy đầu.

### 3.4 Đo bộ nhớ

Ba hàm cần biết:

| Hàm | Trả về | Ghi chú |
|---|---|---|
| `memory_get_usage()` | Số byte bộ nhớ đang cấp cho script **lúc này** | Do bộ quản lý bộ nhớ của PHP (Zend memory manager) cấp |
| `memory_get_peak_usage()` | Số byte **cao nhất** từng đạt tới | Thứ cần nhìn khi lo chạm `memory_limit` |
| `memory_reset_peak_usage()` | Đặt lại mức đỉnh về mức hiện tại | Có từ PHP 8.2 |

Tham số `$real_usage = true` của hai hàm đầu cho biết tổng bộ nhớ mà memory manager của PHP đã xin từ
hệ điều hành (gồm cả phần đã xin nhưng chưa dùng). Theo manual, đó là con số mà `memory_limit` so
sánh. Bộ nhớ do extension cấp phát trực tiếp bằng `malloc()` không được tính vào cả hai con số.

```php
<?php
declare(strict_types=1);

function mb(int $bytes): string
{
    return sprintf('%.2f MB', $bytes / 1_048_576);
}

/**
 * Đo bộ nhớ đỉnh mà $fn dùng thêm (PHP 8.2+ vì cần memory_reset_peak_usage).
 *
 * @param callable(): mixed $fn
 */
function peakOf(callable $fn): int
{
    $before = memory_get_usage();
    memory_reset_peak_usage();          // đưa "đỉnh" về mức hiện tại
    $fn();
    return memory_get_peak_usage() - $before;
}

echo "đầu script:  ", mb(memory_get_usage()), "\n";

$big = range(1, 1_000_000);             // mảng một triệu số nguyên
echo "giữ \$big:    ", mb(memory_get_usage()), "\n";

unset($big);                            // bỏ biến, refcount về 0, bộ nhớ được trả lại
echo "sau unset:   ", mb(memory_get_usage()), "\n";
echo "đỉnh:        ", mb(memory_get_peak_usage()), "\n";   // đỉnh vẫn nhớ lúc cao nhất

$used = peakOf(function (): int {
    $tmp = range(1, 1_000_000);
    return count($tmp);                 // $tmp bị giải phóng khi hàm kết thúc
});
echo "peakOf:      ", mb($used), "\n";
echo "sau peakOf:  ", mb(memory_get_usage()), "\n";

// in ra (output minh hoạ (php-wasm 32-bit), PHP 8.5; máy 64-bit thật ra số hơi khác):
// đầu script:  0.44 MB
// giữ $big:    16.50 MB
// sau unset:   0.44 MB
// đỉnh:        16.50 MB
// peakOf:      16.06 MB
// sau peakOf:  0.44 MB
```

Đọc kết quả:

- Một triệu số nguyên tốn khoảng 16 MB, tức khoảng 16 byte mỗi phần tử (từ PHP 8.2, mảng dạng danh sách lưu mỗi phần tử là một zval 16 byte), chứ không phải 8 byte như một
  mảng `int64` trong C. Mỗi phần tử mảng PHP là một *zval* có kèm thông tin kiểu
  ([Chương 19](19-ben-trong-engine.md) giải thích chi tiết). Mảng có key chuỗi còn tốn hơn nhiều.
- Sau `unset()` thì `memory_get_usage()` giảm về như cũ, nhưng `memory_get_peak_usage()` vẫn nhớ đỉnh
  16.5 MB. Vì vậy muốn đo đỉnh của **một đoạn** code thì phải `memory_reset_peak_usage()` trước
  đoạn đó, như hàm `peakOf()`.
- `peakOf()` cho thấy hàm dùng tạm 16 MB rồi trả lại hết. Đỉnh tạm thời cũng quan trọng: 50 request
  đồng thời, mỗi request có đỉnh 16 MB là 800 MB RAM.

⚠️ `memory_get_usage()` không phải bộ nhớ của **cả process** mà hệ điều hành thấy (RSS). Process PHP
còn chứa code của engine, extension, OPcache (bộ nhớ dùng chung)... Khi tính RAM cho FPM, dùng số liệu
của hệ điều hành ([Chương 18](18-fpm-nginx-opcache.md)).

### 3.5 Micro-benchmark: những cái bẫy

*Micro-benchmark* là đo một đoạn code rất nhỏ (một hàm, một phép toán) để so hai cách viết. Rất dễ
đo sai. Các bẫy hay gặp:

| Bẫy | Chuyện gì xảy ra | Cách tránh |
|---|---|---|
| Đo một lần | Một lần chạy có thể trùng lúc máy bận | Lặp nhiều lần, lấy median (mục 3.3) |
| Không warm-up | Lần đầu tính cả chi phí biên dịch, nạp class | Chạy bỏ vài lần đầu |
| Lần sau làm việc khác lần đầu | Sắp xếp mảng đã sắp xếp, cache đã ấm, dữ liệu đã bị sửa | Mỗi lần chạy phải bắt đầu từ cùng trạng thái |
| Đo bằng CLI rồi suy ra web | Theo manual, `opcache.enable_cli` mặc định là `0`: CLI chạy không có OPcache (và không có JIT), còn FPM thường có | Bật `-d opcache.enable_cli=1` khi muốn giống production |
| Xdebug đang được nạp | Xdebug ở mode khác `off` làm mọi thứ chậm đi, và chậm không đều giữa các loại code | `php -m` kiểm tra, tắt Xdebug khi đo |
| Dữ liệu quá nhỏ | 10 phần tử thì O(n²) và O(n) gần như bằng nhau | Đo với cỡ dữ liệu thật của bạn |
| Code bị tính sẵn | Biểu thức hằng như `60 * 60 * 24` được trình biên dịch tính sẵn, vòng lặp chỉ đo... vòng lặp | Dùng dữ liệu đến lúc chạy (biến, input) |
| Kết luận từ chênh lệch nhỏ | 2% chênh lệch nằm trong mức dao động tự nhiên | Chỉ tin khi chênh lệch lớn và lặp lại được |

Quan trọng nhất: micro-benchmark trả lời "cách A nhanh hơn cách B bao nhiêu **trong điều kiện này**".
Nó **không** trả lời "request của tôi sẽ nhanh hơn bao nhiêu". Câu hỏi sau cần profiler và đo cả
request (mục 4).

### 3.6 Laravel: `Benchmark`

Laravel có sẵn class `Illuminate\Support\Benchmark` cho việc đo nhanh:

```php
use App\Models\User;
use Illuminate\Support\Benchmark;

// In kết quả (ms) rồi dừng chương trình (dump and die)
Benchmark::dd([
    'count trong SQL' => fn () => User::count(),
    'đếm trong PHP'   => fn () => User::all()->count(),
], iterations: 10);

// Lấy cả giá trị trả về và thời gian (ms)
[$count, $duration] = Benchmark::value(fn () => User::count());
```

Đọc mã nguồn Laravel 13.x thì thấy `Benchmark::measure()` (hàm mà `dd()` gọi) làm đúng những việc ở
mục 3.3 nhưng đơn giản hơn: mỗi lần lặp gọi `gc_collect_cycles()`, bấm giờ bằng `hrtime(true)`, rồi
trả về **trung bình** (average) số ms của các lần lặp. Không có warm-up, không có median. Dùng nó để
so sánh nhanh, khi cần chính xác thì lặp nhiều và tự kiểm tra độ dao động.

Ví dụ trên cũng là một bài học: `User::count()` để MySQL đếm và trả về một con số; `User::all()->count()`
kéo **mọi dòng** của bảng về PHP, dựng thành object, rồi mới đếm. Bảng càng lớn thì chênh lệch càng
lớn, cả thời gian lẫn bộ nhớ.

### 3.7 Đo trong ứng dụng thật: ghi lại query và request chậm

Đo bằng tay chỉ dùng được khi bạn đã biết chỗ cần đo. Để **phát hiện** chỗ chậm trong ứng dụng đang
chạy, hãy cho ứng dụng tự ghi lại. Ví dụ trong Laravel, đặt trong `boot()` của `AppServiceProvider`:

```php
use Illuminate\Database\Connection;
use Illuminate\Database\Events\QueryExecuted;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Log;

public function boot(): void
{
    // Ghi log mọi query chạy lâu hơn 100 ms ($query->time tính bằng ms)
    DB::listen(function (QueryExecuted $query): void {
        if ($query->time > 100) {
            Log::warning('Query chậm', ['sql' => $query->sql, 'ms' => $query->time]);
        }
    });

    // Gọi callback khi TỔNG thời gian query trong một request vượt 500 ms
    DB::whenQueryingForLongerThan(500, function (Connection $connection, QueryExecuted $event): void {
        Log::warning('Request tốn quá nhiều thời gian chờ DB', [
            'connection' => $connection->getName(),
            'url'        => request()->fullUrl(),
        ]);
    });
}
```

- `DB::listen` được gọi sau **mỗi** query, nhận object `QueryExecuted` có `sql`, `bindings`, `time`
  (số mili giây). Đừng làm việc nặng trong listener này, vì nó chạy cho mọi query.
- `DB::whenQueryingForLongerThan` theo dõi thời gian query **cộng dồn** trong một request, bắt được
  trường hợp N+1 (từng query nhanh nhưng tổng lại chậm) mà ngưỡng từng query bỏ sót.
- Phía MySQL cũng có *slow query log* ghi lại query vượt ngưỡng `long_query_time`, xem
  [Database 24: Vận hành và giám sát](../database/24-van-hanh-monitoring.md).

Khi ứng dụng lớn dần, tự ghi log kiểu này không còn đủ. Lúc đó cần profiler (đào sâu một request) và
công cụ giám sát (nhìn toàn hệ thống). Hai mục tiếp theo nói về chúng.

## 4. Profiler

### 4.1 Profiler là gì, vì sao cần

Đo bằng tay (mục 3) buộc bạn phải **đoán trước** chỗ cần đo rồi chèn code đo vào đó. Với một request
Laravel đi qua vài trăm class và hàng chục nghìn lời gọi hàm, đoán như vậy không khả thi.

*Profiler* là công cụ tự động ghi lại thời gian (và thường cả bộ nhớ) tiêu tốn **theo từng hàm** trong
một lần chạy, không cần sửa code. Kết quả là một *profile*: bảng hoặc biểu đồ cho biết hàm nào được gọi
bao nhiêu lần, tốn bao nhiêu thời gian, ai gọi ai.

Profiler của PHP thường là một *extension* (phần mở rộng viết bằng C, nạp vào engine), vì chỉ ở tầng
engine mới thấy được mọi lần vào và ra khỏi hàm.

### 4.2 Hai cách thu dữ liệu: instrumenting và sampling

| | *Instrumenting* (đo mọi lời gọi) | *Sampling* (lấy mẫu) |
|---|---|---|
| Cơ chế | Móc (*hook*) vào mọi lần vào và ra khỏi hàm, ghi thời điểm | Cứ sau một khoảng thời gian cố định, chụp lại call stack hiện tại; hàm nào xuất hiện trong nhiều mẫu thì tốn nhiều thời gian |
| Cho biết | Số lần gọi chính xác, thời gian từng hàm | Tỉ lệ thời gian theo stack; không có số lần gọi chính xác |
| Overhead | Lớn, tăng theo số lời gọi hàm | Nhỏ và gần như cố định, chỉnh được bằng chu kỳ lấy mẫu |
| Méo kết quả | Hàm nhỏ gọi hàng triệu lần bị **phóng đại**, vì chi phí đo mỗi lần gọi có khi lớn hơn chính hàm đó | Hàm chạy quá ngắn có thể không lọt vào mẫu nào |
| Ví dụ | Xdebug profiler, SPX (mặc định), XHProf, callgraph của Blackfire và Tideways | SPX với `SPX_SAMPLING_PERIOD`, Excimer |

Hình dung bằng ví dụ đời thường: muốn biết một nhân viên dành thời gian cho việc gì trong ngày.
Instrumenting là ghi lại giờ bắt đầu và kết thúc của **mọi** việc họ làm, kể cả từng lần nhấp chuột:
chính xác, nhưng việc ghi chép làm họ chậm hẳn đi. Sampling là cứ 10 phút nhìn qua xem họ đang làm gì:
không biết chính xác từng việc, nhưng sau một ngày thì tỉ lệ thời gian cho từng loại việc khá đúng, và
người đó hầu như không bị làm phiền.

Vì overhead nhỏ, sampling là cách duy nhất phù hợp để chạy liên tục trên production. Instrumenting
dùng ở môi trường dev, staging, hoặc bật cho **từng request được chọn**.

### 4.3 Các con số trong một profile

Mọi profiler đều dùng những khái niệm sau, nên hiểu một lần là đọc được mọi công cụ:

- *Inclusive* (Incl., "total", "tổng"): thời gian của hàm **cộng cả mọi hàm nó gọi**. Dùng để đi từ
  trên xuống: controller tốn 800 ms, trong đó service A tốn 700 ms.
- *Exclusive* (Excl., *self*): thời gian **chỉ trong thân hàm**, trừ đi các hàm con. Dùng để tìm chỗ
  thực sự đốt thời gian. Một hàm có inclusive lớn mà exclusive nhỏ chỉ là "người chuyển việc": thời
  gian nằm ở các hàm nó gọi.
- *Calls*: số lần hàm được gọi. Số lần gọi lớn bất thường (một hàm query chạy 500 lần) là dấu hiệu
  của vòng lặp gọi việc tốn kém, ví dụ N+1.
- *Wall time* và *CPU time*: như mục 2.6. SPX gọi phần chênh lệch là *idle time* (thời gian không chạy
  trên CPU: chờ I/O, chờ lock, ngủ).
- *Memory*: bộ nhớ hàm cấp phát thêm (có thể âm nếu hàm giải phóng nhiều hơn cấp phát).

Để thấy rõ inclusive và exclusive được tính thế nào, hãy tự viết một profiler đồ chơi kiểu
instrumenting. Mỗi lần "vào hàm" ghi lại thời điểm; lúc "ra khỏi hàm" thì tính thời gian, trừ đi phần
của các hàm con:

```php
<?php
declare(strict_types=1);

/**
 * Profiler đồ chơi kiểu instrumenting: mỗi lần "vào hàm" và "ra khỏi hàm"
 * đều ghi lại thời điểm. Profiler thật (Xdebug, SPX) làm việc này tự động
 * cho MỌI hàm, ở tầng C bên trong engine.
 */
final class ToyProfiler
{
    /** @var array<string, array{calls: int, incl: int, excl: int}> */
    private array $flat = [];

    /** @var array<string, int> chuỗi stack "a;b;c" => thời gian exclusive (ns) */
    private array $folded = [];

    /** @var list<array{name: string, start: int, child: int}> */
    private array $stack = [];

    /**
     * @template T
     * @param callable(): T $fn
     * @return T
     */
    public function call(string $name, callable $fn): mixed
    {
        $this->stack[] = ['name' => $name, 'start' => hrtime(true), 'child' => 0];
        try {
            return $fn();
        } finally {
            $path  = implode(';', array_column($this->stack, 'name'));
            $frame = array_pop($this->stack);
            $incl  = hrtime(true) - $frame['start'];      // gồm cả hàm con
            $excl  = $incl - $frame['child'];              // trừ phần của hàm con

            $this->flat[$name] ??= ['calls' => 0, 'incl' => 0, 'excl' => 0];
            $this->flat[$name]['calls']++;
            $this->flat[$name]['incl'] += $incl;
            $this->flat[$name]['excl'] += $excl;

            $this->folded[$path] = ($this->folded[$path] ?? 0) + $excl;

            if ($this->stack !== []) {
                // báo cho hàm cha: "con của bạn đã tốn $incl"
                $this->stack[array_key_last($this->stack)]['child'] += $incl;
            }
        }
    }

    public function printFlat(): void
    {
        $rows = $this->flat;
        uasort($rows, fn (array $a, array $b): int => $b['excl'] <=> $a['excl']);
        printf("%-14s %6s %10s %10s\n", 'function', 'calls', 'incl(ms)', 'excl(ms)');
        foreach ($rows as $name => $r) {
            printf("%-14s %6d %10.1f %10.1f\n", $name, $r['calls'], $r['incl'] / 1e6, $r['excl'] / 1e6);
        }
    }

    public function printFolded(): void
    {
        foreach ($this->folded as $path => $ns) {
            printf("%s %d\n", $path, (int) round($ns / 1e6));   // đơn vị: ms
        }
    }
}

// ----- Một "request" giả lập -----
$p = new ToyProfiler();

$query = fn (): mixed => $p->call('query', function (): void {
    usleep(3_000);                       // chờ DB 3 ms
});

$p->call('handle', function () use ($p, $query): void {
    $p->call('controller', function () use ($p, $query): void {
        $query();                        // lấy danh sách 10 bài viết
        for ($i = 0; $i < 10; $i++) {
            $p->call('loadAuthor', $query);   // N+1: mỗi bài một query
        }
        $p->call('callApi', function (): void {
            usleep(40_000);              // gọi API bên ngoài 40 ms
        });
    });
    $p->call('render', function (): void {
        $s = 0;
        for ($i = 0; $i < 1_000_000; $i++) {
            $s += $i;                    // tính toán thuần CPU
        }
    });
});

$p->printFlat();
echo "\n";
$p->printFolded();

// in ra (output minh hoạ; cột calls luôn như vậy, thời gian thì tuỳ máy):
// function        calls   incl(ms)   excl(ms)
// callApi             1       40.1       40.1
// query              11       39.0       39.0
// render              1       27.9       27.9
// controller          1       80.0        0.6
// handle              1      108.2        0.3
// loadAuthor         10       35.5        0.3
//
// handle;controller;query 4
// handle;controller;loadAuthor;query 35
// handle;controller;loadAuthor 0
// handle;controller;callApi 40
// handle;controller 1
// handle;render 28
// handle 0
```

Đọc bảng trên như đọc output của một profiler thật (gọi là *flat profile*, bảng phẳng các hàm):

- `handle` có inclusive 108 ms (cả request) nhưng exclusive gần 0: nó chỉ gọi hàm khác. Tương tự
  `controller`, `loadAuthor`.
- Sắp xếp theo exclusive thì ba thủ phạm nổi lên: `callApi` (chờ API), `query` (chờ DB), `render`
  (CPU).
- `query` từng lần chỉ 3 ms, nhưng **calls = 11** đẩy tổng lên gần 40 ms. Cột calls là nơi N+1 lộ diện.
- Phần thứ hai (*folded stacks*, các stack đã gộp) là định dạng dùng để vẽ flame graph, mục 5.

Profiler thật làm đúng việc này nhưng tự động cho mọi hàm, kể cả hàm có sẵn của PHP như
`PDOStatement::execute`, và đo chính xác hơn nhiều.

### 4.4 Xdebug profiler

*Xdebug* là extension nổi tiếng nhất cho PHP: debugger từng bước (step debugging), đo độ phủ code
(code coverage), và profiler. Cấu hình của Xdebug 3 xoay quanh setting `xdebug.mode`:

| Giá trị `xdebug.mode` | Bật tính năng |
|---|---|
| `off` | Không bật gì. Theo tài liệu Xdebug, dùng khi muốn overhead gần bằng 0 |
| `develop` | Công cụ hỗ trợ phát triển, ví dụ `var_dump()` đẹp hơn. **Đây là giá trị mặc định** |
| `debug` | Step debugging |
| `coverage` | Code coverage (dùng với PHPUnit) |
| `profile` | Profiler |
| `trace` | Ghi lại mọi lời gọi hàm (function trace), và flame graph |
| `gcstats` | Thống kê garbage collector |

Có thể bật nhiều mode cùng lúc, cách nhau bởi dấu phẩy: `xdebug.mode=debug,develop`. Biến môi trường
`XDEBUG_MODE` ghi đè setting này.

Cấu hình để profile **theo yêu cầu** (chỉ request nào có "trigger" mới bị profile):

```ini
; ví dụ: /etc/php/8.5/fpm/conf.d/99-xdebug.ini (đường dẫn tuỳ bản phân phối)
zend_extension = xdebug
xdebug.mode = profile
xdebug.start_with_request = trigger    ; chỉ profile khi có XDEBUG_TRIGGER
xdebug.output_dir = /tmp/xdebug        ; mặc định /tmp
; tên file mặc định: cachegrind.out.%p (%p là PID của process)
```

Nếu không đặt `start_with_request`, giá trị `default` với mode `profile` nghĩa là `yes`: **mọi**
request đều bị profile, ổ đĩa đầy rất nhanh.

Kích hoạt trigger:

```bash
# Chạy ở máy dev, nơi PHP đã cài Xdebug với cấu hình trên
curl -b 'XDEBUG_TRIGGER=1' http://localhost/orders    # cookie; hoặc ?XDEBUG_TRIGGER=1 trên URL
XDEBUG_TRIGGER=1 php artisan report:daily             # CLI: dùng biến môi trường
```

Xdebug kiểm tra `XDEBUG_TRIGGER` trong biến môi trường, `$_GET`, `$_POST` và `$_COOKIE`. Response của
request được profile có header `X-Xdebug-Profile-Filename` chứa đường dẫn file kết quả. File có định
dạng *cachegrind* (định dạng của công cụ Callgrind/KCachegrind) và mặc định được nén gzip
(`xdebug.use_compression`, mặc định bật nếu Xdebug được build có hỗ trợ zlib).

Mở file bằng:

- *KCachegrind* (Linux) hoặc *QCachegrind* (bản không cần KDE, có cho Windows; trên macOS cài qua
  Homebrew). ⚠️ Theo tài liệu Xdebug, QCachegrind không đọc được file nén gzip; dùng QCachegrind thì
  đặt `xdebug.use_compression = false`.
- PhpStorm (có sẵn trình xem profile, đọc được file nén).
- Webgrind (giao diện web).

Trong KCachegrind, khung bên trái là flat profile với các cột *Incl.*, *Self* (exclusive), *Called*
(số lần gọi). Hàm có sẵn của PHP được Xdebug thêm tiền tố `php::`, ví dụ `php::PDOStatement->execute`.
Khung bên phải cho biết *callers* (ai gọi hàm đang chọn) và *callees* (hàm đang chọn gọi ai).

⚠️ Những điều cần nhớ về Xdebug:

- **Không** cài Xdebug trên production. Ngay cả khi không profile, mode mặc định là `develop` chứ không
  phải `off`; theo tài liệu Xdebug, chỉ mode `off` (Xdebug không làm gì ngoài kiểm tra tính năng nào
  được bật) mới cho overhead gần bằng 0. Nếu buộc phải nạp extension thì đặt `xdebug.mode=off`.
- Xdebug là profiler instrumenting, overhead lớn, và phóng đại các hàm nhỏ gọi nhiều lần. Hãy coi số
  liệu tuyệt đối với sự nghi ngờ; tỉ lệ và số lần gọi đáng tin hơn.
- File profile của một request framework có thể rất lớn (tài liệu Xdebug cảnh báo "can be enormous").
  Nhớ dọn thư mục `output_dir`.
- Tài liệu của Blackfire khuyên tắt Xdebug khi profile bằng Blackfire; nói chung đừng nạp nhiều
  extension profiler/debugger cùng lúc.

### 4.5 SPX

*SPX* (*Simple Profiling eXtension*) là profiler mã nguồn mở, điểm mạnh là rất dễ dùng và có sẵn giao
diện web với *timeline* (dòng thời gian các lời gọi), flat profile và flame graph. Cài bằng PIE (công
cụ cài extension mới của PHP) hoặc build từ mã nguồn:

```bash
pie install noisebynorthwest/php-spx
```

Với script CLI, chỉ cần một biến môi trường:

```bash
# In flat profile ra STDERR khi script kết thúc (kể cả khi bấm Ctrl-C giữa chừng)
SPX_ENABLED=1 php artisan report:daily

# Tạo báo cáo đầy đủ để xem trên giao diện web
SPX_ENABLED=1 SPX_REPORT=full php artisan report:daily
```

Với request web, cấu hình cho môi trường dev riêng (theo README của SPX):

```ini
extension = spx.so
spx.http_enabled = 1
spx.http_key = "dev"
spx.http_ip_whitelist = "127.0.0.1"
```

Rồi mở `http://localhost/?SPX_KEY=dev&SPX_UI_URI=/`, bật "Enabled" trong bảng điều khiển, tải lại trang
cần đo và mở báo cáo trong danh sách.

Vài tham số đáng biết (đặt bằng biến môi trường khi chạy CLI):

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `SPX_METRICS` | `wt,zm` | Các metric thu thập: `wt` wall time, `zm` bộ nhớ Zend Engine; thêm `ct` (CPU time), `it` (idle time), `zo` (số object đang sống, hữu ích khi tìm leak)... |
| `SPX_BUILTINS` | `0` | Có profile cả hàm có sẵn của PHP hay không. Mặc định **không**, nên muốn thấy `PDOStatement::execute` thì đặt `1` |
| `SPX_SAMPLING_PERIOD` | `0` | Khác 0 thì chuyển sang chế độ sampling. README khuyên thử sampling để không phóng đại hàm nhỏ |
| `SPX_AUTO_START` | `1` | Đặt `0` để tự gọi `spx_profiler_start()` / `spx_profiler_stop()` quanh đoạn cần đo |

`SPX_AUTO_START=0` hữu ích với process sống lâu như queue worker: profile cả vòng đời một worker ngồi
chờ việc là vô nghĩa, hãy bọc từng job:

```php
while ($task = getNextTask()) {     // getNextTask() là hàm giả định của bạn
    spx_profiler_start();
    try {
        $task->process();
    } finally {
        spx_profiler_stop();
    }
}
```

⚠️ Tác giả SPX ghi rõ dự án vẫn ở trạng thái *experimental*, chỉ nên dùng ở môi trường
**không phải production**. Lý do chính là bảo mật: ai vào được giao diện web của SPX sẽ xem được chi
tiết bên trong ứng dụng. Trên PHP-FPM, các metric đọc từ `/proc` (như `mor`, `io`) cần thêm
`process.dumpable = yes` vào cấu hình pool.

### 4.6 Blackfire và Tideways (khái niệm)

*Blackfire* và *Tideways* là dịch vụ thương mại. Cả hai gồm ba phần:

```
┌──────────────────────┐    ┌───────────────┐    ┌──────────────────────┐
│ Extension trong PHP  │───▶│ Agent/daemon  │───▶│ Dịch vụ của hãng     │
│ (Blackfire gọi là    │    │ chạy trên     │    │ (giao diện web, lưu  │
│ "probe")             │    │ server        │    │ trữ, so sánh)        │
└──────────────────────┘    └───────────────┘    └──────────────────────┘
          ▲
          │ kích hoạt profile cho một request cụ thể
┌──────────────────────┐
│ Client: browser      │
│ extension hoặc CLI   │
└──────────────────────┘
```

Điểm khác với Xdebug: request bình thường **không** bị profile. Chỉ request được client kích hoạt (kèm
thông tin xác thực do client tạo) mới bị đo, nên có thể profile ngay trên production bằng một request do bạn tự gửi:

```bash
# Blackfire: profile một request HTTP và một script CLI
blackfire curl https://app.example.com/orders
blackfire run php artisan report:daily
```

Những gì các dịch vụ này cho thêm so với công cụ miễn phí:

- Call graph có tô sẵn *hot path* (đường đi tốn nhiều thời gian nhất từ gốc tới lá).
- **So sánh hai profile** (trước và sau khi sửa) ngay trên giao diện.
- Đếm sẵn query SQL, lời gọi HTTP, kèm thời gian.
- Blackfire: viết *assertion* hiệu năng (ví dụ "trang này không được chạy quá 10 query") để chạy trong
  CI.
- Tideways: kết hợp giám sát liên tục (APM) với profiler. Theo tài liệu Tideways, *timeline profiler*
  (nhẹ) thu trace cho một phần request, còn *callgraph profiler* (đầy đủ từng hàm) có overhead đáng kể
  hơn nên mặc định chỉ chạy cho trace do lập trình viên chủ động kích hoạt.

Bạn không cần thuộc cách cài đặt; cần hiểu chúng thuộc loại nào và giải quyết vấn đề gì.

### 4.7 Sampling trên production: Excimer

*Excimer* là extension do Wikimedia (tổ chức vận hành Wikipedia) viết: một profiler sampling overhead
thấp. Wikimedia giải thích lý do viết nó: profiler instrumenting phải cài một hook chặn mọi lời gọi
hàm, và chỉ riêng việc có hook đó (dù không làm gì) đã khiến engine bỏ qua một số tối ưu. Excimer
không dùng hook đó, đổi lại không đếm được chính xác số lần gọi hàm, nhưng đủ nhẹ để cài trên toàn bộ
server production.

```php
// Cần extension excimer. Lấy mẫu mỗi 1 ms theo wall time, ghi folded stacks khi request kết thúc
$profiler = new ExcimerProfiler();
$profiler->setPeriod(0.001);
$profiler->setEventType(EXCIMER_REAL);
$profiler->start();

register_shutdown_function(function () use ($profiler): void {
    $profiler->stop();
    file_put_contents('/tmp/trace.log', $profiler->getLog()->formatCollapsed());
});
```

`formatCollapsed()` xuất đúng định dạng folded stacks như profiler đồ chơi ở mục 4.3, đưa thẳng vào
công cụ vẽ flame graph (mục 5.4).

### 4.8 Giám sát (APM) và công cụ của Laravel

Profiler trả lời "trong request **này**, hàm nào tốn". Nhưng câu hỏi đầu tiên (bước 1 của quy trình)
là "endpoint **nào** chậm, chậm từ khi nào, chậm với ai". Câu đó cần công cụ giám sát chạy liên tục:

- *APM* (*Application Performance Monitoring*): New Relic, Datadog, Tideways, hoặc tự dựng bằng
  *OpenTelemetry* (chuẩn mở để thu trace, metric, log). APM ghi lại mọi request (hoặc một phần), tính
  sẵn p50/p95/p99 cho từng endpoint, và chia thời gian mỗi request theo tầng (PHP, DB, HTTP, cache).
- Laravel Telescope: ghi lại request, query, job, cache, exception... để xem lúc phát triển. Tài liệu
  Laravel mô tả nó là "companion to your local Laravel development environment".
- Laravel Debugbar (package cộng đồng): thanh công cụ hiện ngay trên trang số query, thời gian, bộ nhớ
  của request vừa xem. Rất tiện để phát hiện N+1 khi đang code.
- Laravel Pulse: dashboard cho production, theo dõi request chậm, query chậm, job chậm, người dùng
  hoạt động nhiều. Laravel Nightwatch là dịch vụ giám sát (chạy trên hạ tầng của Laravel) do chính Laravel cung cấp.

Chi tiết các công cụ Laravel nằm ở [Chương 30](30-laravel-testing-octane-deploy.md).

### 4.9 Chọn công cụ nào

| Công cụ | Loại | Dùng ở đâu | Dùng khi |
|---|---|---|---|
| `hrtime`, `memory_get_peak_usage` | Đo tay | Mọi nơi | Đã biết chỗ cần đo, so sánh hai cách viết |
| Xdebug profiler | Instrumenting, file cachegrind | Chỉ dev | Phân tích chi tiết một request, đã có sẵn Xdebug cho debug |
| SPX | Instrumenting hoặc sampling, web UI | Dev, staging | Muốn timeline và flame graph ngay, không tốn tiền |
| Blackfire, Tideways | Dịch vụ thương mại | Cả production (theo yêu cầu) | So sánh trước/sau, assertion trong CI, profile production |
| Excimer | Sampling | Cả production | Flame graph của traffic thật, overhead thấp |
| Telescope, Debugbar | Ghi sự kiện Laravel | Dev | Đếm query, xem N+1 khi đang code |
| APM, Pulse, Nightwatch | Giám sát | Production | Biết endpoint nào chậm, p95, xu hướng theo thời gian |

Quy tắc dễ nhớ: **giám sát** để biết *ở đâu*, **profiler** để biết *vì sao*.

## 5. Flame graph

### 5.1 Từ call stack tới flame graph

Một request Laravel có thể sinh ra hàng chục nghìn call stack khác nhau. Bảng flat profile cho biết
hàm nào tốn, nhưng mất bối cảnh "ai gọi nó". Cây call graph thì giữ bối cảnh nhưng quá rối để nhìn.
*Flame graph*, do Brendan Gregg nghĩ ra khi phân tích một vấn đề hiệu năng của MySQL, gộp tất cả call
stack thành **một hình** đọc được trong vài giây.

Nguyên liệu của flame graph là *folded stacks* (stack đã gộp): mỗi dòng là một call stack, các hàm nối
nhau bằng dấu `;` từ gốc tới ngọn, cuối dòng là một con số (số mẫu, hoặc thời gian). Đây chính là
phần thứ hai trong output của profiler đồ chơi ở mục 4.3:

```
handle;controller;query 4
handle;controller;loadAuthor;query 35
handle;controller;loadAuthor 0
handle;controller;callApi 40
handle;controller 1
handle;render 28
handle 0
```

Vẽ từ dữ liệu này (hình minh hoạ, mỗi ký tự khoảng 1.5 ms):

```
                           [query................]
[callApi..................][loadAuthor...........][q]
[controller.........................................][render...........]
[handle................................................................]
```

(khối `[q]` là `query` gọi thẳng từ controller, quá hẹp nên không đủ chỗ ghi tên; công cụ thật cho
rê chuột vào để xem tên đầy đủ)

### 5.2 Cách đọc

1. **Trục dọc là độ sâu stack.** Hàng dưới cùng là gốc (`handle`), mỗi hàng lên trên là hàm được hàng
   dưới gọi. Một khối nằm trên khối khác nghĩa là "được gọi bởi".
2. **Chiều rộng là tất cả.** Khối rộng bao nhiêu phần trăm thì hàm đó (tính cả các hàm nó gọi, tức
   inclusive) chiếm bấy nhiêu phần trăm thời gian. Ở hình trên, `controller` chiếm khoảng 3/4,
   `render` khoảng 1/4.
3. **Trục ngang KHÔNG phải thời gian.** Đây là điểm hay bị hiểu nhầm nhất. Theo Brendan Gregg, các
   khối được **sắp theo thứ tự chữ cái** để gộp được nhiều stack giống nhau nhất: `callApi` nằm bên
   trái `loadAuthor` vì chữ c đứng trước chữ l, chứ không phải vì được gọi trước. Muốn xem theo thứ
   tự thời gian thì dùng *flame chart* (trục ngang là thời gian, có trong Chrome DevTools, SPX gọi là
   timeline). Một số công cụ (ví dụ chế độ "left heavy" của speedscope) xếp khối lớn nhất sang trái
   thay vì theo chữ cái; dù xếp kiểu nào, vị trí ngang cũng không nói gì về thời điểm.
4. **Tìm "cao nguyên".** Khối rộng mà phía trên **không còn gì** (hoặc chỉ có khối con hẹp) là hàm
   tiêu thời gian *tự thân* (exclusive). Ở hình trên có ba cao nguyên: `callApi`, `query` (trên
   `loadAuthor`), `render`. Đó là nơi cần nhìn trước.
5. **Đi từ dưới lên theo khối rộng** để biết code nào của mình dẫn tới cao nguyên đó.
6. **Màu sắc** trong flame graph gốc là ngẫu nhiên trong dải màu "nóng", chỉ để phân biệt các khối
   cạnh nhau, không mang ý nghĩa. Một số công cụ dùng màu để phân loại (code của bạn, vendor, hàm có
   sẵn của PHP), xem chú thích của từng công cụ.
7. *Icicle graph* là flame graph lộn ngược (gốc ở trên, ngọn ở dưới), đọc y hệt.

### 5.3 Đọc flame graph của một request Laravel

Hình minh hoạ một request danh sách đơn hàng (tên hàm rút gọn, khối xếp theo chữ cái như mục 5.2):

```
                            [PDOStatement::execute...........][curl_exec.......]
                        [Builder::get........................][PaymentClient...]
[json_encode][toArray]  [OrderController::index................................]
[JsonResponse........][Pipeline::then (middleware).......................................]
[Kernel::handle..........................................................................]
```

Đọc:

- Gốc là `Kernel::handle`. Phần lớn thời gian đi qua chuỗi middleware (`Pipeline::then`) vào
  `OrderController::index`; một phần nhỏ hơn nằm ở `JsonResponse` (biến dữ liệu thành JSON).
- Cao nguyên rộng nhất là `PDOStatement::execute` nằm trên `Builder::get`: phần lớn thời gian là chờ
  database. Khoảng hở giữa `Builder::get` và khối phía trên nó (phần đầu bên trái) là thời gian tự
  thân của query builder, ví dụ dựng model từ kết quả.
- Cao nguyên thứ hai là `curl_exec` (gọi API thanh toán qua `PaymentClient`).
- `json_encode` và `toArray` là chi phí biến model thành JSON, nhỏ hơn nhiều.
- Kết luận: tối ưu query trước (đếm số query, xem EXPLAIN), sau đó tính chuyện cache hoặc gọi API
  đồng thời. Viết lại vòng lặp PHP không giải quyết được gì ở đây.

### 5.4 N+1 trên flame graph

Flame graph **gộp** các stack giống nhau. 50 lần lazy load quan hệ, mỗi lần đi qua cùng một chuỗi hàm
`Model::__get → ... → Builder::get → PDOStatement::execute`, hiện thành **một khối rộng duy nhất**,
trông y như một query chậm. Nhìn flame graph thôi thì không phân biệt được "1 query chậm 500 ms" với
"50 query mỗi cái 10 ms". Hai cách phân biệt:

- Xem cột **số lần gọi** (calls) trong flat profile của profiler instrumenting: `PDOStatement::execute`
  được gọi 51 lần là N+1.
- Xem **timeline / flame chart**: N+1 hiện ra như một dãy dài các khối hẹp giống hệt nhau nối tiếp
  nhau, trong khi một query chậm là một khối dài duy nhất.

Hai trường hợp có cách chữa khác hẳn nhau (eager loading cho N+1, index hoặc viết lại query cho query
chậm), nên đừng kết luận trước khi phân biệt.

### 5.5 Tạo flame graph bằng công cụ có sẵn

| Nguồn dữ liệu | Cách làm |
|---|---|
| SPX | Có sẵn tab flame graph trong giao diện web, không cần làm gì thêm |
| Xdebug | `xdebug.mode=trace` và `xdebug.trace_format=3` (thời gian) hoặc `4` (bộ nhớ); file sinh ra đưa vào script `flamegraph.pl` |
| Excimer | `getLog()->formatCollapsed()` ra folded stacks cho `flamegraph.pl`; hoặc `getSpeedscopeData()` để mở bằng speedscope.app |
| Blackfire, Tideways | Có sẵn trong giao diện web |

Với Xdebug (theo tài liệu Xdebug, chạy ở máy dev):

```bash
# 1. Lấy script vẽ flame graph của Brendan Gregg
git clone https://github.com/brendangregg/FlameGraph ~/FlameGraph

# 2. Chạy script với cấu hình trace cho flame graph
XDEBUG_MODE=trace XDEBUG_TRIGGER=1 php -d xdebug.trace_format=3 -d xdebug.output_dir=/tmp \
    artisan report:daily

# 3. File trace mặc định được nén gzip (đuôi .xt.gz); giải nén rồi vẽ ra SVG
zcat /tmp/trace.*.xt.gz | ~/FlameGraph/flamegraph.pl > /tmp/flame.svg
```

Mở file SVG bằng trình duyệt: rê chuột vào khối để xem tên và tỉ lệ, bấm vào khối để phóng to nhánh
đó, có ô tìm kiếm tên hàm.

## 6. Các tối ưu thường gặp

### 6.1 Thứ tự ưu tiên

Không phải tối ưu nào cũng đáng công như nhau. Thứ tự gợi ý cho một ứng dụng PHP web, từ "rẻ mà lợi
nhiều" tới "đắt mà lợi ít":

| Nhóm | Ví dụ | Công sức | Lợi ích điển hình |
|---|---|---|---|
| Cấu hình runtime, làm một lần | OPcache, autoloader tối ưu, cache của Laravel (mục 7) | Rất thấp | Giảm thời gian khởi động **mọi** request |
| Database | Bỏ N+1, thêm index, chỉ lấy cột và dòng cần | Thấp tới vừa | Thường lớn nhất cho từng endpoint chậm |
| I/O | Cache kết quả, gọi đồng thời (mục 8), đẩy việc sang queue | Vừa | Lớn khi endpoint gọi API ngoài |
| Lượng dữ liệu | Generator, xử lý theo lô, phân trang | Vừa | Giảm bộ nhớ, tránh fatal error |
| Thuật toán, cấu trúc dữ liệu | Thay `in_array` trong vòng lặp bằng tra key | Thấp khi đã tìm ra | Lớn nếu đúng là nút thắt CPU |
| Vi mô (*micro-optimization*) | Đổi nháy, đổi `array_map` sang `foreach` | Thấp | Gần như không đáng kể (mục 6.9) |

Dù ở nhóm nào, vẫn theo đúng quy trình ở mục 1.4: đo, sửa, đo lại.

### 6.2 OPcache: bật chưa?

Nhắc lại [Chương 02](02-php-chay-nhu-the-nao.md): không có OPcache thì **mỗi request** PHP phải đọc
và biên dịch lại mọi file (với Laravel là hàng trăm file) thành opcode trước khi chạy. OPcache lưu
opcode đã biên dịch vào bộ nhớ dùng chung giữa các worker, nên từ request thứ hai trở đi bỏ được bước
biên dịch. Đây là tối ưu có lợi lớn nhất và rẻ nhất, nhưng vẫn hay bị quên trên server tự dựng.

Kiểm tra nhanh:

```php
<?php
declare(strict_types=1);

// Chạy trong môi trường bạn muốn kiểm tra. Với web (FPM) thì đặt đoạn này
// vào một trang nội bộ có bảo vệ, vì CLI và FPM có cấu hình OPcache riêng.
$status = function_exists('opcache_get_status') ? opcache_get_status(false) : false;

if ($status === false) {
    echo "OPcache chưa bật trong SAPI này (", PHP_SAPI, ")\n";
    exit;
}

$mem   = $status['memory_usage'];
$stats = $status['opcache_statistics'];

printf("enabled:       %s\n", $status['opcache_enabled'] ? 'yes' : 'no');
printf("cache full:    %s\n", $status['cache_full'] ? 'yes' : 'no');
printf("used memory:   %.1f MB, free %.1f MB\n", $mem['used_memory'] / 1_048_576, $mem['free_memory'] / 1_048_576);
printf("scripts:       %d / max keys %d\n", $stats['num_cached_scripts'], $stats['max_cached_keys']);
printf("hit rate:      %.2f%%\n", $stats['opcache_hit_rate']);

// in ra khi chạy `php file.php` với cấu hình mặc định (opcache.enable_cli = 0):
// OPcache chưa bật trong SAPI này (cli)
//
// in ra khi chạy `php -d opcache.enable_cli=1 file.php` (output minh hoạ (php-wasm 32-bit)):
// enabled:       yes
// cache full:    no
// used memory:   8.4 MB, free 119.6 MB
// scripts:       1 / max keys 16229
// hit rate:      0.00%
```

Những gì cần nhìn trên server thật (chi tiết cấu hình ở [Chương 18](18-fpm-nginx-opcache.md)):

- `opcache_enabled` phải là `yes` trong **FPM**, không phải trong CLI. Hai SAPI có thể dùng file
  `php.ini` khác nhau.
- `cache_full` là `yes` hoặc `free_memory` gần hết: tăng `opcache.memory_consumption` (mặc định 128,
  đơn vị MB).
- Số script đã cache gần chạm `max_cached_keys`: tăng `opcache.max_accelerated_files` (mặc định
  10000; PHP làm tròn lên số nguyên tố kế tiếp trong một danh sách cố định, vì vậy mới thấy 16229).
- Hit rate trên server chạy ổn định nên rất gần 100%. Hit rate thấp kéo dài nghĩa là cache liên tục
  bị nạp lại.
- Trên production thường đặt `opcache.validate_timestamps=0` để OPcache không kiểm tra file có đổi
  không; đổi lại phải reset cache mỗi lần deploy ([Chương 18](18-fpm-nginx-opcache.md)).

### 6.3 Autoloader tối ưu

Composer mặc định nạp class theo quy tắc PSR-4 ([Chương 11](11-namespace-composer.md)): từ tên class
suy ra đường dẫn file, rồi **kiểm tra file có tồn tại trên đĩa không**. Mỗi class cần nạp là một lần
hỏi hệ thống file. Tài liệu Composer gọi việc này là "slows things down quite a bit", và đưa ra ba
mức tối ưu:

| Mức | Bật bằng | Làm gì | Đánh đổi |
|---|---|---|---|
| 1: class map | `composer dump-autoload -o` (`--optimize`), hoặc `install`/`update` với `-o`, hoặc `"optimize-autoloader": true` trong `config` | Quét trước mọi thư mục PSR-4/PSR-0, sinh sẵn bảng `class => file`. Class có trong bảng thì trả đường dẫn ngay, không hỏi đĩa | Theo tài liệu: không có đánh đổi thật sự, nên luôn bật trên production. Class **không tồn tại** vẫn rơi về PSR-4 và hỏi đĩa |
| 2/A: authoritative | `-a` / `--classmap-authoritative` | Không có trong class map thì coi như không tồn tại, không hỏi đĩa | Class sinh ra lúc chạy (runtime) sẽ báo "class not found" |
| 2/B: APCu | `--apcu-autoloader` (với `dump-autoload` là `--apcu`) | Cache kết quả tra cứu (kể cả tra hụt) vào APCu | Cần extension APCu; không dùng chung được với 2/A |

Lệnh deploy thường dùng:

```bash
# Chạy trong thư mục dự án trên server (hoặc trong bước build image)
composer install --no-dev --optimize-autoloader --no-interaction
```

- `--no-dev`: không cài các package chỉ dùng khi phát triển (PHPUnit, Debugbar...), autoloader cũng
  nhỏ hơn.
- Skeleton Laravel 13.x đặt sẵn `"optimize-autoloader": true` trong `config` của `composer.json`, nên
  mức 1 được bật cả khi chạy `composer install` ở máy dev.
- ⚠️ Tài liệu Composer khuyên **không** bật các tối ưu này khi đang phát triển, vì thêm, xoá, đổi tên
  class sẽ gây lỗi nếu quên chạy lại `dump-autoload`. Với mức 1, class mới thêm vẫn được tìm qua PSR-4
  nên ít gặp vấn đề; với mức 2/A thì gặp ngay.
- Với OPcache bật, file class map (một mảng PHP lớn) cũng được cache dưới dạng opcode, nên nạp gần
  như tức thì.

### 6.4 Tránh N+1

*N+1* là lỗi hiệu năng phổ biến nhất trong ứng dụng có database: 1 query lấy danh sách N phần tử, rồi
trong vòng lặp chạy thêm **1 query cho mỗi phần tử** để lấy dữ liệu liên quan. Tổng cộng N+1 query.
Ví dụ sau dùng SQLite trong bộ nhớ (có sẵn trong PHP, không cần cài gì) và đếm số query:

```php
<?php
declare(strict_types=1);

/** Bọc PDO, đếm số query đã gửi tới database */
final class Db
{
    public int $count = 0;

    public function __construct(private readonly PDO $pdo) {}

    /**
     * @param list<int|string> $params
     * @return list<array<string, mixed>>
     */
    public function select(string $sql, array $params = []): array
    {
        $this->count++;
        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}

$pdo = new PDO('sqlite::memory:', options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);

// Dữ liệu mẫu: 100 tác giả, 1000 bài viết; bài i thuộc tác giả (i % 100) + 1
$pdo->exec('CREATE TABLE authors (id INTEGER PRIMARY KEY, name TEXT NOT NULL)');
$pdo->exec('CREATE TABLE posts (id INTEGER PRIMARY KEY, author_id INTEGER NOT NULL, title TEXT NOT NULL)');
$pdo->beginTransaction();
$insA = $pdo->prepare('INSERT INTO authors (id, name) VALUES (?, ?)');
for ($i = 1; $i <= 100; $i++) {
    $insA->execute([$i, "Tác giả $i"]);
}
$insP = $pdo->prepare('INSERT INTO posts (id, author_id, title) VALUES (?, ?, ?)');
for ($i = 1; $i <= 1000; $i++) {
    $insP->execute([$i, ($i % 100) + 1, "Bài $i"]);
}
$pdo->commit();

$db = new Db($pdo);

// ---- Cách 1: N+1 ----
$db->count = 0;
$posts = $db->select('SELECT id, author_id, title FROM posts ORDER BY id LIMIT 200');   // 1 query
foreach ($posts as $k => $post) {
    $row = $db->select('SELECT name FROM authors WHERE id = ?', [$post['author_id']]);  // +1 mỗi bài
    $posts[$k]['author'] = $row[0]['name'];
}
printf("N+1:      %3d query | %s - %s\n", $db->count, $posts[0]['title'], $posts[0]['author']);

// ---- Cách 2: 2 query, WHERE IN (cách eager loading của ORM làm) ----
$db->count = 0;
$posts = $db->select('SELECT id, author_id, title FROM posts ORDER BY id LIMIT 200');
$ids   = array_values(array_unique(array_column($posts, 'author_id')));
$marks = implode(',', array_fill(0, count($ids), '?'));
$names = array_column(
    $db->select("SELECT id, name FROM authors WHERE id IN ($marks)", $ids),
    'name', 'id'                                    // [id => name]
);
foreach ($posts as $k => $post) {
    $posts[$k]['author'] = $names[$post['author_id']];   // tra mảng trong RAM, không query
}
printf("WHERE IN: %3d query | %s - %s\n", $db->count, $posts[0]['title'], $posts[0]['author']);

// ---- Cách 3: 1 query, JOIN ----
$db->count = 0;
$posts = $db->select(
    'SELECT p.id, p.title, a.name AS author
       FROM posts p JOIN authors a ON a.id = p.author_id
      ORDER BY p.id LIMIT 200'
);
printf("JOIN:     %3d query | %s - %s\n", $db->count, $posts[0]['title'], $posts[0]['author']);

// in ra:
// N+1:      201 query | Bài 1 - Tác giả 2
// WHERE IN:   2 query | Bài 1 - Tác giả 2
// JOIN:       1 query | Bài 1 - Tác giả 2
```

Ba cách cho cùng kết quả, nhưng 201 query so với 2 hoặc 1. Với SQLite trong bộ nhớ, mỗi query rất rẻ
nên chênh lệch thời gian chưa lộ rõ. Với MySQL thật qua mạng, **mỗi query** còn tốn thêm một lượt đi
về giữa PHP và MySQL, nên 201 query có thể chậm hơn hàng chục tới hàng trăm lần so với 1-2 query.

Trong Laravel, N+1 thường không nhìn thấy trong code vì Eloquent tự query khi bạn truy cập quan hệ
(*lazy loading*):

```php
// N+1: mỗi $post->author là một query ẩn
foreach (Post::all() as $post) {
    echo $post->author->name;
}

// Eager loading: 2 query (posts, rồi authors WHERE id IN (...)), giống Cách 2 ở trên
foreach (Post::with('author')->get() as $post) {
    echo $post->author->name;
}
```

Và có thể bắt Laravel **báo lỗi** khi lazy loading xảy ra, để phát hiện N+1 ngay khi đang code. Theo
tài liệu Laravel, đặt trong `boot()` của `AppServiceProvider`:

```php
use Illuminate\Database\Eloquent\Model;

Model::preventLazyLoading(! $this->app->isProduction());   // chỉ ném exception ngoài production
```

Chi tiết về eager loading nằm ở [Chương 27](27-laravel-database-eloquent.md); N+1 ở tầng PDO và cách
nhận ra ở [Chương 16](16-php-va-database.md); phía database ở
[Database 19: Database từ phía ứng dụng](../database/19-database-tu-ung-dung.md).

### 6.5 Cache

*Cache* là lưu lại kết quả của một việc tốn kém để lần sau dùng lại, thay vì làm lại. Câu hỏi đầu
tiên luôn là: **dữ liệu này được phép cũ bao lâu?** Tỉ giá cũ 5 phút có thể chấp nhận; số dư tài khoản
cũ 5 giây thì không.

Các tầng cache trong một ứng dụng PHP, từ gần tới xa:

| Tầng | Sống bao lâu | Dùng chung giữa | Ví dụ |
|---|---|---|---|
| Biến trong request (memoization) | Hết request | Không | Thuộc tính của object, biến `static`, `once()` của Laravel |
| APCu | Tới khi hết TTL, bị đẩy ra khi bộ nhớ đầy, hoặc FPM khởi động lại | Các worker trên **cùng một server** | Cấu hình ít đổi, kết quả tính toán nhỏ |
| Redis, Memcached | Tới khi hết TTL hoặc bị xoá | **Mọi server** | Kết quả query, response API ngoài, session |
| HTTP cache, CDN | Theo header `Cache-Control` | Mọi người dùng (hoặc từng trình duyệt) | Trang công khai, ảnh, file tĩnh |

Tầng đơn giản nhất, và hay bị bỏ qua, là **cache trong request**: cùng một request gọi một hàm tốn kém
nhiều lần với cùng tham số.

```php
<?php
declare(strict_types=1);

final class ExchangeRates
{
    public int $slowCalls = 0;

    /** @var array<string, float> cache trong RAM, sống cùng object (tức tới hết request) */
    private array $memo = [];

    public function rate(string $currency): float
    {
        return $this->memo[$currency] ??= $this->load($currency);
    }

    /** Giả lập việc tốn kém: gọi API tỉ giá, đọc DB... */
    private function load(string $currency): float
    {
        $this->slowCalls++;
        usleep(20_000);                               // 20 ms
        return match ($currency) {
            'USD'   => 25_400.0,
            'EUR'   => 27_500.0,
            default => throw new InvalidArgumentException("Không hỗ trợ $currency"),
        };
    }
}

$rates = new ExchangeRates();
$t = hrtime(true);
$total = 0.0;
foreach ([10, 20, 30, 40, 50] as $usd) {              // 5 dòng hàng, cùng đơn vị USD
    $total += $usd * $rates->rate('USD');
}
printf("tổng: %s VND | gọi chậm: %d lần | %.0f ms\n",
    number_format($total), $rates->slowCalls, (hrtime(true) - $t) / 1e6);

// in ra (thời gian là output minh hoạ):
// tổng: 3,810,000 VND | gọi chậm: 1 lần | 22 ms
```

Không có `$memo`, vòng lặp gọi `load()` 5 lần, mất khoảng 100 ms. Toán tử `??=` gán và trả về giá trị
nếu key chưa có, nên chỉ lần đầu là chạy `load()`.

Với cache dùng chung (Redis), Laravel có sẵn các hàm (chi tiết ở
[Chương 29](29-laravel-queue-event-schedule-cache.md)):

```php
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;

// Có trong cache thì trả về; không có thì chạy closure, lưu kết quả 600 giây
$top = Cache::remember('products:top', 600, fn () => DB::table('products')->orderByDesc('sold')->limit(10)->get());

// "Stale-while-revalidate": trong 5 giây đầu là dữ liệu tươi; từ giây 5 tới 10 vẫn trả dữ liệu cũ
// ngay lập tức và làm mới cache SAU khi đã gửi response; quá 10 giây thì tính lại ngay
$stats = Cache::flexible('dashboard:stats', [5, 10], fn () => DB::table('orders')->count());
```

⚠️ Các cạm bẫy của cache:

- **Invalidation** (làm mất hiệu lực): dữ liệu gốc đổi mà cache chưa đổi, người dùng thấy dữ liệu cũ.
  Phải quyết định rõ: hết TTL thì thôi, hay xoá cache ngay khi dữ liệu gốc thay đổi.
- **Cache stampede** (đàn bò giẫm đạp): một key "nóng" hết hạn, hàng trăm request cùng lúc thấy cache
  trống và cùng chạy query nặng để tính lại, database quá tải. Cách chống: `Cache::flexible`, khoá
  (lock) để chỉ một request tính lại, hoặc làm mới cache bằng job chạy nền trước khi hết hạn.
- **Key không đủ phân biệt**: cache dữ liệu riêng của từng người dùng bằng một key chung, người này
  thấy dữ liệu của người kia. Đây là lỗi bảo mật chứ không chỉ là lỗi hiển thị.
- **Cache thứ rẻ**: cache một query 1 ms bằng Redis (cũng tốn một lượt đi về qua mạng) không lợi gì,
  còn thêm độ phức tạp. Đo trước khi cache.

### 6.6 Generator và xử lý theo lô cho dữ liệu lớn

Khi phải xử lý nhiều dữ liệu (xuất báo cáo, import file, duyệt cả bảng), cách viết tự nhiên là gom tất
cả vào một mảng rồi xử lý. Bộ nhớ khi đó tăng theo số dòng, và tới một lúc sẽ chạm `memory_limit`.

*Generator* ([Chương 13](13-generator-iterator-spl.md)) cho phép viết hàm "trả về từng phần tử khi
được hỏi" bằng `yield`. Code gọi vẫn dùng `foreach` như với mảng, nhưng tại mỗi thời điểm chỉ một phần
tử nằm trong bộ nhớ:

```php
<?php
declare(strict_types=1);

/** Cách 1: dựng cả danh sách trong RAM rồi trả về */
function rowsArray(int $n): array
{
    $rows = [];
    for ($i = 1; $i <= $n; $i++) {
        $rows[] = ['id' => $i, 'email' => "user$i@example.com", 'total' => $i * 1000];
    }
    return $rows;
}

/** Cách 2: generator, mỗi lần chỉ "đưa ra" một dòng */
function rowsGenerator(int $n): Generator
{
    for ($i = 1; $i <= $n; $i++) {
        yield ['id' => $i, 'email' => "user$i@example.com", 'total' => $i * 1000];
    }
}

/** @param iterable<array{id: int, email: string, total: int}> $rows */
function sumTotal(iterable $rows): int
{
    $sum = 0;
    foreach ($rows as $row) {
        $sum += $row['total'];
    }
    return $sum;
}

$n = 200_000;

memory_reset_peak_usage();
$base = memory_get_usage();
$sum = sumTotal(rowsArray($n));
printf("array:     tổng %d | đỉnh bộ nhớ thêm %9.1f KB\n", $sum, (memory_get_peak_usage() - $base) / 1024);

memory_reset_peak_usage();
$base = memory_get_usage();
$sum = sumTotal(rowsGenerator($n));
printf("generator: tổng %d | đỉnh bộ nhớ thêm %9.1f KB\n", $sum, (memory_get_peak_usage() - $base) / 1024);

// in ra (output minh hoạ (php-wasm 32-bit), PHP 8.5; số bộ nhớ trên máy 64-bit thật sẽ khác):
// array:     tổng 20000100000000 | đỉnh bộ nhớ thêm   86968.8 KB
// generator: tổng 20000100000000 | đỉnh bộ nhớ thêm       1.4 KB
```

Cùng kết quả, nhưng cách 1 cần hàng chục MB (và tăng gấp đôi nếu số dòng gấp đôi), cách 2 cần vài
KB bất kể bao nhiêu dòng. Hàm `sumTotal()` nhận `iterable` nên dùng được cho cả hai: đó là lợi thế
thiết kế của generator, đổi cách lấy dữ liệu mà không phải sửa code xử lý.

Áp dụng vào thực tế:

- Đọc file lớn: `fopen` + `fgets`/`fgetcsv` trong vòng lặp, bọc bằng generator, thay vì
  `file_get_contents()` hay `file()` (nạp cả file vào RAM). Chi tiết ở
  [Chương 14](14-file-json-thoi-gian.md).
- Đọc bảng lớn: lấy **theo lô** thay vì cả bảng. Laravel có `chunkById()`, `lazyById()` (mỗi lần lấy
  một lô theo khoá chính) và `cursor()` (một query, dựng từng model khi duyệt tới). ⚠️ Tài liệu
  Laravel lưu ý `cursor()` vẫn có thể hết bộ nhớ với số dòng rất lớn, vì driver PDO MySQL mặc định
  đệm (*buffer*) toàn bộ kết quả thô của query ([Chương 16](16-php-va-database.md),
  [Chương 27](27-laravel-database-eloquent.md)).
- Ghi theo lô: insert mỗi lần vài trăm tới vài nghìn dòng trong một câu `INSERT` nhiều giá trị, thay
  vì từng dòng một (mỗi dòng một lượt đi về) hay cả triệu dòng một lúc.
- Việc xử lý hàng triệu dòng không nên chạy trong request HTTP: đẩy sang queue
  ([Chương 29](29-laravel-queue-event-schedule-cache.md)).

### 6.7 Chọn đúng cấu trúc dữ liệu

Mảng của PHP là *hash table* có thứ tự ([Chương 06](06-mang.md)): tra theo **key** rất nhanh (trung
bình O(1)), nhưng tìm theo **giá trị** thì phải duyệt từng phần tử (O(n)). Nhiều đoạn code chậm chỉ vì
quên điều này. Bốn ví dụ hay gặp:

**Ví dụ 1: kiểm tra "có trong danh sách không" bên trong vòng lặp.**

```php
<?php
declare(strict_types=1);

/** @param callable(): mixed $fn */
function timeMs(callable $fn): float
{
    $t = hrtime(true);
    $fn();
    return (hrtime(true) - $t) / 1e6;
}

// 20.000 user đã mua hàng, kiểm tra 20.000 user khác xem ai đã mua
$buyers   = range(1, 40_000, 2);          // số lẻ: 1, 3, 5, ... (20.000 phần tử)
$toCheck  = range(1, 20_000);
$buyerSet = array_flip($buyers);          // [id => vị trí]: đổi giá trị thành key

$found1 = 0;
$ms1 = timeMs(function () use ($buyers, $toCheck, &$found1): void {
    foreach ($toCheck as $id) {
        if (in_array($id, $buyers, true)) {   // quét tuần tự: O(n) mỗi lần
            $found1++;
        }
    }
});

$found2 = 0;
$ms2 = timeMs(function () use ($buyerSet, $toCheck, &$found2): void {
    foreach ($toCheck as $id) {
        if (isset($buyerSet[$id])) {          // tra hash table: O(1) trung bình
            $found2++;
        }
    }
});

printf("in_array: tìm thấy %d, %8.2f ms\n", $found1, $ms1);
printf("isset:    tìm thấy %d, %8.2f ms\n", $found2, $ms2);

// in ra (thời gian là output minh hoạ):
// in_array: tìm thấy 10000,   196.48 ms
// isset:    tìm thấy 10000,     0.75 ms
```

`in_array` trong vòng lặp là O(n × m): 20.000 × 20.000 = 400 triệu phép so sánh trong trường hợp xấu
nhất. `array_flip` một lần (O(n)) rồi `isset` (O(1)) thì tổng là O(n + m). ⚠️ `array_flip` chỉ dùng
được khi giá trị là `int` hoặc `string` (vì chúng thành key), và các giá trị trùng nhau sẽ gộp làm
một.

**Ví dụ 2: hàng đợi bằng `array_shift`.**

```php
<?php
declare(strict_types=1);

/** @param callable(): mixed $fn */
function timeMs(callable $fn): float
{
    $t = hrtime(true);
    $fn();
    return (hrtime(true) - $t) / 1e6;
}

$n = 50_000;

// Hàng đợi bằng array_shift: mỗi lần lấy đầu mảng, PHP đánh lại số thứ tự mọi phần tử còn lại
$ms1 = timeMs(function () use ($n): void {
    $queue = range(1, $n);
    while ($queue !== []) {
        array_shift($queue);
    }
});

// Hàng đợi bằng SplQueue (danh sách liên kết kép): lấy đầu là O(1)
$ms2 = timeMs(function () use ($n): void {
    $queue = new SplQueue();
    for ($i = 1; $i <= $n; $i++) {
        $queue->enqueue($i);
    }
    while (!$queue->isEmpty()) {
        $queue->dequeue();
    }
});

// Hoặc giữ mảng nguyên, chỉ dời một chỉ số "đầu hàng"
$ms3 = timeMs(function () use ($n): void {
    $queue = range(1, $n);
    for ($head = 0, $len = count($queue); $head < $len; $head++) {
        $item = $queue[$head];
    }
});

printf("array_shift: %8.2f ms\n", $ms1);
printf("SplQueue:    %8.2f ms\n", $ms2);
printf("chỉ số:      %8.2f ms\n", $ms3);

// in ra (output minh hoạ):
// array_shift:   878.64 ms
// SplQueue:        7.55 ms
// chỉ số:          2.16 ms
```

Theo manual, `array_shift()` đánh lại mọi key số sau khi bỏ phần tử đầu, nên mỗi lần gọi là O(n) và
cả vòng lặp là O(n²). `array_pop()` (lấy ở **cuối**) thì không phải đánh số lại. Các cấu trúc dữ liệu
của SPL như `SplQueue`, `SplStack`, `SplPriorityQueue` ở [Chương 13](13-generator-iterator-spl.md).

**Ví dụ 3: `array_merge` trong vòng lặp.**

```php
<?php
declare(strict_types=1);

/** @param callable(): mixed $fn */
function timeMs(callable $fn): float
{
    $t = hrtime(true);
    $fn();
    return (hrtime(true) - $t) / 1e6;
}

// 2.000 trang kết quả, mỗi trang 50 dòng
$pages = array_fill(0, 2_000, range(1, 50));

$c1 = 0;
$ms1 = timeMs(function () use ($pages, &$c1): void {
    $all = [];
    foreach ($pages as $page) {
        $all = array_merge($all, $page);   // mỗi lần tạo mảng mới, chép lại TOÀN BỘ $all: O(n²)
    }
    $c1 = count($all);
});

$c2 = 0;
$ms2 = timeMs(function () use ($pages, &$c2): void {
    $all = array_merge(...$pages);         // gộp một lần: O(n)
    $c2 = count($all);
});

$c3 = 0;
$ms3 = timeMs(function () use ($pages, &$c3): void {
    $all = [];
    foreach ($pages as $page) {
        foreach ($page as $row) {
            $all[] = $row;                 // thêm vào cuối: O(1) trung bình
        }
    }
    $c3 = count($all);
});

printf("array_merge trong vòng lặp: %d phần tử, %8.2f ms\n", $c1, $ms1);
printf("array_merge(...\$pages):     %d phần tử, %8.2f ms\n", $c2, $ms2);
printf("\$all[] = ...:               %d phần tử, %8.2f ms\n", $c3, $ms3);

// in ra (thời gian là output minh hoạ):
// array_merge trong vòng lặp: 100000 phần tử,   145.35 ms
// array_merge(...$pages):     100000 phần tử,     0.24 ms
// $all[] = ...:               100000 phần tử,     3.24 ms
```

**Ví dụ 4: bộ nhớ của mảng kết hợp so với object.**

```php
<?php
declare(strict_types=1);

final class OrderRow
{
    public function __construct(
        public int $id,
        public string $status,
        public int $total,
    ) {}
}

$n = 100_000;

$base = memory_get_usage();
$arrays = [];
for ($i = 0; $i < $n; $i++) {
    $arrays[] = ['id' => $i, 'status' => 'paid', 'total' => $i * 10];
}
printf("mảng kết hợp: %6.2f MB\n", (memory_get_usage() - $base) / 1_048_576);
unset($arrays);

$base = memory_get_usage();
$objects = [];
for ($i = 0; $i < $n; $i++) {
    $objects[] = new OrderRow($i, 'paid', $i * 10);
}
printf("object:       %6.2f MB\n", (memory_get_usage() - $base) / 1_048_576);

// in ra (output minh hoạ (php-wasm 32-bit), PHP 8.5; số trên máy 64-bit thật sẽ khác,
// nhưng mảng kết hợp vẫn tốn hơn object nhiều lần):
// mảng kết hợp:  37.92 MB
// object:        10.19 MB
```

Mỗi mảng kết hợp là một hash table riêng, có bảng băm và chỗ trống dự phòng. Object có property
**khai báo sẵn** lưu giá trị trong một bảng cố định theo thứ tự khai báo, không cần lưu tên key cho
từng object ([Chương 19](19-ben-trong-engine.md)). ⚠️ Điều này **không** áp dụng cho model Eloquent:
model lưu dữ liệu trong một mảng `$attributes` bên trong, cộng thêm nhiều thuộc tính của chính model,
nên nặng hơn mảng thường nhiều. Đó là lý do khi đọc hàng chục nghìn dòng chỉ để xuất báo cáo, dùng
query builder (`DB::table(...)`) thường nhẹ hơn dựng model Eloquent.

Bảng tóm tắt:

| Việc cần làm | Tránh | Nên dùng |
|---|---|---|
| Kiểm tra phần tử có trong tập không, nhiều lần | `in_array` trong vòng lặp | `array_flip` một lần + `isset` |
| Tìm bản ghi theo id, nhiều lần | `array_filter`/vòng lặp mỗi lần tìm | Dựng index `[id => bản ghi]` một lần (`array_column($rows, null, 'id')`) |
| Hàng đợi FIFO | `array_shift` | `SplQueue`, hoặc chỉ số đầu hàng |
| Gộp nhiều mảng | `array_merge` trong vòng lặp | `array_merge(...$list)` hoặc `$all[] =` |
| Ghép chuỗi lớn từ nhiều phần | Không có vấn đề lớn với `.=` | `.=` hoặc gom vào mảng rồi `implode` |
| Hàng đợi ưu tiên | Sắp xếp lại mảng sau mỗi lần thêm | `SplPriorityQueue` hoặc `SplMinHeap` |

### 6.8 JIT: khi nào có ích

PHP 8.0 thêm *JIT* (*just-in-time compiler*): biên dịch opcode "nóng" thành mã máy để CPU chạy trực
tiếp, bỏ qua bước thông dịch từng opcode. Cơ chế và các chế độ của JIT nằm ở
[Chương 19](19-ben-trong-engine.md); cấu hình ở [Chương 18](18-fpm-nginx-opcache.md). Ở góc độ hiệu
năng, chỉ cần nhớ:

- JIT chỉ tăng tốc phần **CPU của PHP**. Nó không làm query nhanh hơn, không làm API trả lời sớm hơn.
  Ứng dụng web điển hình dành phần lớn thời gian chờ I/O, nên lợi ích thường nhỏ: trang công bố PHP 8.0
  ghi rằng tracing JIT nhanh khoảng 3 lần trên benchmark tổng hợp, 1.5 tới 2 lần với vài ứng dụng
  chạy lâu cụ thể, còn hiệu năng ứng dụng điển hình thì ngang PHP 7.4. Code tính toán nặng (xử lý ảnh,
  toán học, mô phỏng) mới thấy rõ khác biệt.
- JIT nằm trong OPcache. Theo manual, từ PHP 8.4 giá trị mặc định là `opcache.jit=disable` (và
  `opcache.jit_buffer_size=64M`); trước 8.4 mặc định là `tracing` nhưng `jit_buffer_size=0`, nên
  thực tế cũng không chạy. Nghĩa là muốn dùng JIT thì phải chủ động bật.
- Bật JIT rồi thì **đo** (mục 1.4). Nếu không thấy cải thiện ở p95 thì không cần giữ.

### 6.9 Những "tối ưu" không đáng làm

Internet đầy những mẹo kiểu "cách viết A nhanh hơn cách viết B". Phần lớn đã lỗi thời, hoặc đúng
nhưng chênh lệch nhỏ tới mức không bao giờ hiện ra trong profile của một ứng dụng thật:

- **Nháy đơn và nháy kép.** Chuỗi nháy kép không chứa biến được trình biên dịch xử lý thành hằng chuỗi
  giống hệt chuỗi nháy đơn. Với OPcache, việc biên dịch còn chỉ diễn ra một lần. Chọn theo quy ước
  code, không theo tốc độ.
- **`$i++` và `++$i`**: chênh lệch không đáng kể.
- **Gọi `count()` trong điều kiện vòng `for`**: `count()` của mảng là O(1) (mảng lưu sẵn số phần tử).
  Đưa ra ngoài vòng lặp gọn hơn, nhưng đừng kỳ vọng request nhanh hơn.
- **Truyền mảng bằng tham chiếu `&` "để khỏi copy".** PHP dùng *copy-on-write*: truyền mảng theo giá
  trị **không** copy cho tới khi bên nhận sửa mảng. Dùng `&` không tiết kiệm gì, có khi còn buộc engine
  phải tách bản sao sớm hơn ([Chương 19](19-ben-trong-engine.md)).
- **Bỏ Collection, `array_map` để viết `foreach`.** Có chi phí gọi hàm thật, nhưng chỉ đáng kể trong
  vòng lặp chạy hàng triệu lần. Với vài trăm phần tử, đổi code dễ đọc lấy vài micro giây là lỗ.

Quy tắc chung: mẹo nào không xuất hiện như một khối rộng trên flame graph của bạn thì chưa đáng để ý.

## 7. Laravel: cache phần khởi động

### 7.1 Vì sao Laravel cần các lệnh cache

Với PHP-FPM, mỗi request khởi động lại framework từ đầu (share-nothing, [Chương 02](02-php-chay-nhu-the-nao.md)).
Trước khi chạy tới controller, Laravel phải:

- Đọc và chạy mọi file trong `config/` (vài chục file), mỗi file gọi `env()` để đọc biến môi trường
  đã nạp từ file `.env`.
- Chạy các file route (`routes/web.php`, `routes/api.php`...), đăng ký từng route.
- Tìm listener của event: theo tài liệu Laravel, mặc định framework tự quét thư mục `Listeners` của
  ứng dụng để tìm listener (*event discovery*).
- Với mỗi view Blade: kiểm tra đã có bản biên dịch (file PHP) chưa và bản đó có cũ hơn file gốc không;
  nếu cần thì biên dịch lại ngay trong request.

Mỗi việc không lớn, nhưng lặp lại ở **mọi** request. Laravel có bốn lệnh để làm sẵn các việc này một
lần lúc deploy, ghi kết quả ra file; OPcache lại cache các file đó dưới dạng opcode, nên nạp gần như
tức thì.

### 7.2 Bốn lệnh cache

| Lệnh | Làm gì | File sinh ra (mặc định) | Xoá bằng |
|---|---|---|---|
| `php artisan config:cache` | Gộp mọi file config thành một file | `bootstrap/cache/config.php` | `config:clear` |
| `php artisan route:cache` | Gộp mọi route đã đăng ký thành một file đã "biên dịch" sẵn | `bootstrap/cache/routes-v7.php` | `route:clear` |
| `php artisan view:cache` | Biên dịch trước mọi view Blade thành file PHP | Thư mục view đã biên dịch (mặc định `storage/framework/views`) | `view:clear` |
| `php artisan event:cache` | Lưu danh sách event và listener tìm được | `bootstrap/cache/events.php` | `event:clear` |

Đường dẫn file lấy từ mã nguồn `Illuminate\Foundation\Application` của Laravel 13.x (các hàm
`getCachedConfigPath()`, `getCachedRoutesPath()`, `getCachedEventsPath()`).

Và một lệnh gộp:

```bash
# Chạy trong thư mục dự án trên server, trong bước deploy
php artisan optimize
```

Đọc mã nguồn `OptimizeCommand` của Laravel 13.x: `optimize` chạy lần lượt `config:cache`,
`event:cache`, `route:cache`, `view:cache`, cộng thêm lệnh do package đăng ký. Có thể bỏ bớt bằng
`--except`, ví dụ `php artisan optimize --except=views`.

Lệnh ngược lại `php artisan optimize:clear` xoá các file cache trên, và **cả dữ liệu trong cache store
mặc định** (nó gọi `cache:clear`; tài liệu deployment của Laravel ghi rõ "as well as all keys in the
default cache driver"). ⚠️ Chạy `optimize:clear` trên production nghĩa là xoá luôn cache ứng dụng
trong Redis: mọi request ngay sau đó tính lại từ đầu, có thể gây cache stampede (mục 6.5). Nếu chỉ
muốn làm mới cache khởi động thì chạy lại `optimize` (mỗi lệnh `*:cache` tự ghi đè file cũ).

### 7.3 Cạm bẫy lớn nhất: `env()` sau `config:cache`

Theo tài liệu Laravel: sau khi chạy `config:cache`, file `.env` **không được nạp nữa**, và `env()` chỉ
còn trả về biến môi trường thật của hệ thống (biến chỉ khai báo trong `.env` sẽ ra `null`). Vì vậy
quy tắc là: **chỉ gọi `env()` trong các file `config/*.php`**, mọi chỗ khác dùng `config()`.

```php
// config/services.php: ĐÚNG chỗ để gọi env()
return [
    'payment' => [
        'key' => env('PAYMENT_KEY'),
    ],
];

// app/Services/PaymentClient.php
$key = config('services.payment.key');   // ĐÚNG: đọc từ config đã cache
$key = env('PAYMENT_KEY');               // SAI: chạy ổn ở máy dev, ra null trên production sau config:cache
```

Lỗi này nguy hiểm vì nó **chỉ xuất hiện trên production** (nơi chạy `config:cache`), còn ở máy dev mọi
thứ vẫn chạy.

Các cạm bẫy khác:

- Đổi `.env` hoặc file config trên server mà không chạy lại `config:cache` thì thay đổi không có hiệu
  lực.
- Thêm hoặc sửa route mà quên `route:cache`: route mới báo 404. Vì vậy các lệnh cache phải nằm trong
  script deploy, không chạy tay.
- Tài liệu Laravel khuyên **không** chạy `config:cache` khi phát triển ở máy local, vì config thay đổi
  liên tục.
- Thư mục `bootstrap/cache` và `storage` phải ghi được bởi user chạy PHP.

### 7.4 Ghép lại: bước tối ưu trong script deploy

```bash
# Chạy trên server (hoặc trong bước build image), trong thư mục dự án
composer install --no-dev --optimize-autoloader --no-interaction   # autoloader tối ưu (mục 6.3)
php artisan optimize                                               # config, event, route, view cache
# ... rồi reload PHP-FPM hoặc reset OPcache nếu validate_timestamps=0 (Chương 18)
```

Quy trình deploy đầy đủ (migration, restart queue worker, zero-downtime) ở
[Chương 30](30-laravel-testing-octane-deploy.md). Bước xa hơn nữa là bỏ hẳn việc khởi động lại
framework cho mỗi request bằng *Laravel Octane* (giữ ứng dụng sống trong bộ nhớ giữa các request),
cũng ở Chương 30. Octane nhanh hơn nhưng mang theo cả loạt lỗi mới do trạng thái bị giữ lại giữa các
request, nên chỉ cân nhắc sau khi đã làm hết các bước rẻ ở trên.

## 8. Làm nhiều việc cùng lúc: concurrency trong PHP

### 8.1 Concurrency và parallelism

Hai từ hay bị dùng lẫn:

- *Concurrency* (đồng thời): nhiều việc **đang dở dang** trong cùng một khoảng thời gian, có thể xen
  kẽ nhau. Một đầu bếp nấu ba món: đặt nồi canh lên bếp, trong lúc chờ sôi thì thái rau, rồi quay lại
  nêm canh. Chỉ một người, nhưng ba món cùng tiến triển.
- *Parallelism* (song song): nhiều việc **chạy thật sự cùng một lúc** trên nhiều CPU. Ba đầu bếp, mỗi
  người một món.

Concurrency giúp khi các việc chủ yếu **chờ** (chờ nước sôi, chờ API trả lời): trong lúc chờ việc này
thì làm việc khác. Parallelism giúp khi các việc chủ yếu **tính** (CPU): muốn nhanh hơn thì cần thêm
CPU.

### 8.2 Mô hình của PHP-FPM: song song giữa request, tuần tự trong request

```
          ┌─ worker 1: request A ── query ── gọi API ── render ──┐
Nginx ────┼─ worker 2: request B ── query ── render ─────────────┼──▶ song song GIỮA các request
          └─ worker 3: request C ── gọi API ── gọi API ── query ─┘
                                    ▲
                                    └── tuần tự TRONG một request: xong việc này mới tới việc kia
```

PHP-FPM chạy nhiều worker process, mỗi worker xử lý một request; hệ điều hành chia các process cho
các CPU. Vì vậy **giữa các request** PHP đã song song sẵn. Nhưng **bên trong một request**, code chạy
tuần tự từ trên xuống, và mọi I/O đều chặn (mục 2.2). Ba lời gọi API, mỗi cái 300 ms, là 900 ms.

Câu hỏi của mục này: làm sao để **một request** gửi nhiều lời gọi I/O cùng lúc, hoặc chia một việc
nặng ra nhiều CPU.

### 8.3 Tuần tự và đồng thời: nhìn theo thời gian

Trang chi tiết khách hàng cần ba API: thông tin user (300 ms), đơn hàng (300 ms), điểm thưởng
(200 ms). Không API nào phụ thuộc kết quả của API khác.

| Thời điểm | Tuần tự | Đồng thời |
|---|---|---|
| 0 ms | Gửi request user, chờ | Gửi cả ba request |
| 200 ms | Vẫn chờ user | Điểm thưởng về |
| 300 ms | User về; gửi request đơn hàng | User và đơn hàng về; **xong** |
| 600 ms | Đơn hàng về; gửi request điểm thưởng | |
| 800 ms | Điểm thưởng về; **xong** | |

Tuần tự: tổng các thời gian (800 ms). Đồng thời: xấp xỉ thời gian của request **chậm nhất** (300 ms).
Điều kiện tiên quyết: các việc **độc lập** với nhau. Nếu cần id từ API thứ nhất để gọi API thứ hai thì
hai cái đó buộc phải tuần tự.

### 8.4 `curl_multi`: đồng thời bằng PHP thuần

Extension cURL của PHP có bộ hàm `curl_multi_*` để nhiều transfer HTTP chạy cùng lúc trong một
process. Bên dưới, libcurl mở nhiều socket và dùng cơ chế theo dõi nhiều socket một lúc của hệ điều
hành; code PHP chỉ cần một vòng lặp "đẩy tiến các transfer, chờ socket nào có dữ liệu":

```php
<?php
declare(strict_types=1);

/**
 * Gửi nhiều HTTP GET cùng lúc bằng curl_multi.
 *
 * @param array<string, string> $urls tên => URL
 * @return array<string, array{status: int, ms: float, error: string, body: string}>
 */
function fetchAll(array $urls, int $timeoutSec = 3): array
{
    $mh = curl_multi_init();
    $handles = [];
    foreach ($urls as $name => $url) {
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,          // trả body về thay vì in ra
            CURLOPT_CONNECTTIMEOUT => 1,             // tối đa 1 giây để kết nối
            CURLOPT_TIMEOUT        => $timeoutSec,   // tối đa cho cả request
        ]);
        curl_multi_add_handle($mh, $ch);
        $handles[$name] = $ch;
    }

    // Vòng lặp thu nhỏ: đẩy mọi transfer tiến lên, rồi chờ tới khi có socket sẵn sàng
    do {
        $status = curl_multi_exec($mh, $running);
        if ($running > 0 && curl_multi_select($mh, 1.0) === -1) {
            usleep(1_000);                           // select lỗi: nghỉ chút để không quay vòng rỗng
        }
    } while ($running > 0 && $status === CURLM_OK);

    $results = [];
    foreach ($handles as $name => $ch) {
        $results[$name] = [
            'status' => curl_getinfo($ch, CURLINFO_RESPONSE_CODE),
            'ms'     => curl_getinfo($ch, CURLINFO_TOTAL_TIME) * 1000,
            'error'  => curl_error($ch),
            'body'   => curl_multi_getcontent($ch) ?? '',
        ];
        curl_multi_remove_handle($mh, $ch);
    }
    curl_multi_close($mh);

    return $results;
}

$t = hrtime(true);
$results = fetchAll([
    'user'   => 'https://api.example.com/users/7',
    'orders' => 'https://api.example.com/users/7/orders',
    'points' => 'https://loyalty.example.com/points/7',
]);
foreach ($results as $name => $r) {
    printf("%-7s HTTP %d, %.0f ms %s\n", $name, $r['status'], $r['ms'], $r['error']);
}
printf("tổng: %.0f ms\n", (hrtime(true) - $t) / 1e6);

// in ra (output minh hoạ tự dựng, giả sử ba API trả lời trong 300, 300, 200 ms):
// user    HTTP 200, 301 ms
// orders  HTTP 200, 298 ms
// points  HTTP 200, 203 ms
// tổng: 305 ms
```

Viết tay như vậy dài dòng và dễ sai (quên timeout, quên xử lý lỗi). Trong thực tế dùng thư viện:
Guzzle có *promise* và `Pool`, còn Laravel có `Http::pool`.

### 8.5 Laravel: `Http::pool`

HTTP client của Laravel (bọc Guzzle) gửi đồng thời bằng `Http::pool`:

```php
use Illuminate\Http\Client\Pool;
use Illuminate\Support\Facades\Http;

$responses = Http::pool(fn (Pool $pool) => [
    $pool->as('user')->timeout(2)->get('https://api.example.com/users/7'),
    $pool->as('orders')->timeout(2)->get('https://api.example.com/users/7/orders'),
    $pool->as('points')->timeout(2)->get('https://loyalty.example.com/points/7'),
]);

$data = [];
foreach ($responses as $name => $response) {
    if ($response instanceof Throwable) {
        // Lỗi ở mức kết nối (timeout, DNS...): phần tử là ConnectionException, KHÔNG phải Response
        report($response);
        continue;
    }
    if ($response->failed()) {
        // Kết nối được nhưng API trả lỗi (4xx, 5xx)
        continue;
    }
    $data[$name] = $response->json();
}
```

Những điều tài liệu Laravel 13.x nêu, cần nhớ:

- `as('tên')` để lấy kết quả theo tên thay vì theo thứ tự thêm vào.
- Theo tài liệu, nếu một request trong pool lỗi ở mức kết nối thì phần tử tương ứng là một
  `Illuminate\Http\Client\ConnectionException` chứ không phải `Response`. ⚠️ Gọi thẳng
  `$responses['user']->json()` mà không kiểm tra sẽ lỗi đúng lúc API bên kia gặp sự cố.
- Tham số `concurrency` giới hạn số request bay cùng lúc, ví dụ `Http::pool(fn (Pool $pool) => [...], concurrency: 5)`.
  Hữu ích khi gửi hàng trăm request tới một API có giới hạn tần suất.
- `pool` không nối được với các method như `withHeaders()` của client: header, middleware phải đặt
  trên từng request trong pool.
- Có thêm `Http::batch()`, tương tự `pool` nhưng cho phép đăng ký callback khi hoàn thành.
- ⚠️ Luôn đặt timeout cho từng request. Tổng thời gian của pool xấp xỉ request chậm nhất, nên một API
  treo giữ cả request của bạn tới khi hết timeout.

### 8.6 Song song bằng nhiều process

`Http::pool` giải quyết việc **chờ** nhiều HTTP. Với việc **tính** nặng, hoặc việc chờ không phải
HTTP (nhiều query DB độc lập), cách phổ biến trong PHP là chạy thêm process.

**Laravel `Process`**: chạy lệnh shell, nhiều lệnh cùng lúc:

```php
use Illuminate\Process\Pool;
use Illuminate\Support\Facades\Process;

// Chạy ba lệnh đồng thời và chờ cả ba xong
[$first, $second, $third] = Process::concurrently(function (Pool $pool) {
    $pool->path(base_path())->command('php artisan import:part 1');
    $pool->path(base_path())->command('php artisan import:part 2');
    $pool->path(base_path())->command('php artisan import:part 3');
});

echo $first->output();
```

**Laravel `Concurrency`**: chạy **closure PHP** trong các process con:

```php
use Illuminate\Support\Facades\Concurrency;
use Illuminate\Support\Facades\DB;

[$userCount, $orderCount] = Concurrency::run([
    fn () => DB::table('users')->count(),
    fn () => DB::table('orders')->count(),
]);
```

Cách nó hoạt động (theo tài liệu và mã nguồn `ProcessDriver` của Laravel 13.x): mỗi closure được
serialize, truyền cho một lệnh Artisan ẩn chạy trong **process PHP mới**; process con unserialize
closure, chạy, rồi serialize kết quả trả về process cha. Hệ quả:

- Mỗi process con phải **khởi động lại cả ứng dụng Laravel** và mở kết nối DB riêng. Chỉ đáng dùng
  khi mỗi việc tốn nhiều hơn hẳn chi phí khởi động đó. Gom hai câu `count()` nhanh như ví dụ trên
  vào `Concurrency::run` có thể còn chậm hơn chạy tuần tự. Đo rồi mới quyết.
- Closure và kết quả phải serialize được (không mang theo connection, file handle...).
- Có ba driver: `process` (mặc định), `fork` (nhanh hơn, cần package `spatie/fork`, **chỉ chạy ở
  CLI** vì PHP không hỗ trợ fork trong web request), và `sync` (chạy tuần tự, dùng khi test).
- `Concurrency::defer([...])` chạy các closure sau khi đã gửi response cho người dùng, khi bạn không
  cần kết quả.

**Queue worker** mới là cách chính để PHP dùng nhiều CPU cho việc nặng: chia việc thành nhiều job
nhỏ, đẩy vào queue, chạy nhiều worker ([Chương 29](29-laravel-queue-event-schedule-cache.md)). Ngoài
ra, ở CLI còn có `pcntl_fork()` của extension pcntl (không dùng được trong FPM).

### 8.7 Fibers

*Fiber* (có từ PHP 8.1, chi tiết ở [Chương 13](13-generator-iterator-spl.md)) là một hàm có **call
stack riêng**, có thể tự dừng giữa chừng bằng `Fiber::suspend()` ở bất kỳ độ sâu lời gọi nào, và
được code bên ngoài cho chạy tiếp bằng `$fiber->resume()`.

Fiber tự nó **không** làm gì chạy đồng thời. Nó chỉ là viên gạch: muốn có concurrency phải có thêm một
*event loop* (vòng lặp sự kiện) quyết định fiber nào chạy tiếp, và các thao tác chờ phải **nhường**
cho loop thay vì chặn cả process. Ví dụ sau tự viết một event loop đồ chơi để thấy rõ điều đó:

```php
<?php
declare(strict_types=1);

/**
 * Event loop đồ chơi: chạy nhiều Fiber xen kẽ trong MỘT process, MỘT luồng.
 * Fiber gọi Loop::delay() để nói "tôi cần chờ X giây, ai khác cứ chạy đi".
 */
final class Loop
{
    /** @var array<int, array{fiber: Fiber, wakeAt: float}> */
    private array $tasks = [];

    public function spawn(Closure $fn): void
    {
        $this->tasks[] = ['fiber' => new Fiber($fn), 'wakeAt' => 0.0];
    }

    /** Gọi từ BÊN TRONG fiber: tạm dừng fiber, báo cho loop biết cần chờ bao lâu */
    public static function delay(float $seconds): void
    {
        Fiber::suspend($seconds);
    }

    public function run(): void
    {
        while ($this->tasks !== []) {
            foreach ($this->tasks as $i => $task) {
                if ($task['wakeAt'] > microtime(true)) {
                    continue;                                   // chưa tới giờ chạy tiếp
                }
                $fiber = $task['fiber'];
                // start()/resume() chạy fiber tới lần suspend kế tiếp (hoặc tới khi xong)
                $wait = $fiber->isStarted() ? $fiber->resume() : $fiber->start();
                if ($fiber->isTerminated()) {
                    unset($this->tasks[$i]);
                } else {
                    $this->tasks[$i]['wakeAt'] = microtime(true) + (float) $wait;
                }
            }
            if ($this->tasks !== []) {                          // không ai sẵn sàng: ngủ tới việc gần nhất
                $next = min(array_column($this->tasks, 'wakeAt'));
                usleep(max(0, (int) (($next - microtime(true)) * 1e6)));
            }
        }
    }
}

/** @param Closure(): void $waitForApi cách "chờ API" mà mỗi tác vụ dùng */
function demo(string $title, Closure $waitForApi): void
{
    $start = microtime(true);
    $log = function (string $msg) use ($start): void {
        printf("[%3.0f ms] %s\n", (microtime(true) - $start) * 1000, $msg);
    };

    echo "--- $title\n";
    $loop = new Loop();
    foreach (['A', 'B', 'C'] as $name) {
        $loop->spawn(function () use ($name, $log, $waitForApi): void {
            $log("$name gửi request");
            $waitForApi();
            $log("$name nhận response");
        });
    }
    $loop->run();
    $log('xong');
}

demo('chờ kiểu nhường (non-blocking)', fn () => Loop::delay(0.1));   // chờ 100 ms, nhường loop
demo('chờ kiểu chặn (blocking)', fn () => usleep(100_000));         // chặn CẢ process 100 ms

// in ra (output minh hoạ, lệch vài ms tuỳ máy):
// --- chờ kiểu nhường (non-blocking)
// [  0 ms] A gửi request
// [  0 ms] B gửi request
// [  0 ms] C gửi request
// [101 ms] A nhận response
// [101 ms] B nhận response
// [101 ms] C nhận response
// [101 ms] xong
// --- chờ kiểu chặn (blocking)
// [  0 ms] A gửi request
// [100 ms] A nhận response
// [100 ms] B gửi request
// [200 ms] B nhận response
// [200 ms] C gửi request
// [301 ms] C nhận response
// [301 ms] xong
```

Đọc kết quả:

- Lần đầu, ba tác vụ "chờ" bằng `Loop::delay()`: fiber dừng lại, loop chuyển sang fiber khác, nên ba
  lần chờ chồng lên nhau, tổng khoảng 100 ms.
- Lần hai, cùng ba fiber, cùng loop, nhưng chờ bằng `usleep()`: hàm này chặn **cả process**, loop
  không có cơ hội chuyển sang fiber khác. Tổng 300 ms, y như code tuần tự.
- Để ý `Fiber::suspend()` được gọi bên trong `Loop::delay()`, tức sâu hai tầng hàm so với hàm gốc của
  fiber. Generator không làm được điều này (`yield` chỉ dừng được chính hàm chứa nó); đây là điểm mạnh
  của fiber.

⚠️ Bài học chính: `PDO::query()`, `file_get_contents()`, `curl_exec()` đều là lời gọi **chặn**, giống
`usleep()` ở trên. Bỏ chúng vào fiber không làm chúng chạy đồng thời. Muốn đồng thời thật phải dùng
driver I/O được viết riêng cho event loop (các thư viện ở mục 8.8). Fiber cũng **không phải thread**:
tại mỗi thời điểm chỉ một fiber chạy, nên nó không giúp gì cho việc nặng CPU.

Fiber là công cụ cho **tác giả thư viện** async; người viết ứng dụng gần như không gọi `new Fiber`
trực tiếp.

### 8.8 Thư viện và runtime bất đồng bộ (giới thiệu)

| Tên | Là gì | Cách đạt concurrency | Ghi chú |
|---|---|---|---|
| *ReactPHP* | Thư viện PHP thuần cho lập trình hướng sự kiện | Event loop (kiểu *reactor*) + stream, socket, HTTP client/server non-blocking | Không cần extension. Package `react/async` có `await()` dựa trên Fiber |
| *AMPHP* (v3) | Bộ thư viện async: HTTP client/server, MySQL, Postgres, Redis... | Fiber + event loop *Revolt* | Viết code async trông như code đồng bộ, không callback |
| *Swoole*, *OpenSwoole* | Extension viết bằng C/C++: server, coroutine, client | Coroutine + event loop trong engine; *runtime hooks* (`Swoole\Runtime::enableCoroutine()`) làm một số hàm chặn (stream, file, sleep, cURL, một số thao tác DB) nhường được cho coroutine khác | Theo README của Swoole: coroutine là công cụ concurrency, không tự song song hoá việc CPU |
| *FrankenPHP*, *RoadRunner* | Application server giữ ứng dụng PHP sống lâu (worker mode) | Nhiều worker, bỏ chi phí khởi động mỗi request | Không làm I/O trong một request thành đồng thời; dùng qua Laravel Octane |

Đặc điểm chung của nhóm ReactPHP, AMPHP, Swoole: process PHP **sống lâu**, xử lý nhiều kết nối cùng lúc
trong một process. Đó là mô hình khác hẳn PHP-FPM, với các vấn đề riêng: rò rỉ bộ nhớ, trạng thái
toàn cục bị giữ lại giữa các request, thư viện chặn làm đứng cả process. Laravel Octane (chạy trên
FrankenPHP, RoadRunner, Swoole, Open Swoole) và các cạm bẫy của nó ở
[Chương 30](30-laravel-testing-octane-deploy.md).

Với ứng dụng Laravel thông thường, thứ tự lựa chọn hợp lý: `Http::pool` cho nhiều HTTP → queue cho
việc nặng hoặc không cần kết quả ngay → `Concurrency`/`Process` cho vài việc nặng độc lập → chỉ xét
runtime async khi bài toán thật sự cần hàng nghìn kết nối đồng thời (websocket, proxy, crawler).

### 8.9 Cạm bẫy khi làm đồng thời

- **API bên kia chịu không nổi**: gửi 500 request cùng lúc có thể vượt rate limit hoặc làm sập dịch
  vụ đối tác. Giới hạn bằng `concurrency`.
- **Lỗi từng phần**: 3 request thì 1 cái lỗi. Phải quyết định trước: báo lỗi cả trang, hay hiển thị
  phần có được (mục 8.5).
- **Timeout**: thiếu timeout thì một request treo kéo theo cả nhóm.
- **Tài nguyên nhân lên**: mỗi process con mở một kết nối DB và chiếm một phần RAM. 10 request web,
  mỗi request `Concurrency::run` 5 việc, là 50 process và 50 kết nối DB cùng lúc.
- **Thứ tự kết quả**: kết quả về không theo thứ tự gửi. Đặt tên (`as()`, key của mảng) thay vì dựa vào
  vị trí.
- **Không phải chỗ nào cũng cần**: tổng thời gian chờ chỉ vài chục ms thì cái giá phức tạp không đáng.

### 8.10 Đối chiếu với Go, Java, Node.js

| | PHP-FPM | Node.js | Go | Java |
|---|---|---|---|---|
| Song song giữa các request | Nhiều process worker | Một luồng JS chính mỗi process; chạy nhiều process để dùng nhiều CPU | Goroutine trên nhiều luồng OS | Thread pool (và virtual thread từ Java 21) |
| Đồng thời trong một request | Không có sẵn; dùng `curl_multi`/`Http::pool`, process con, hoặc runtime async | Mặc định: mọi I/O là non-blocking, `Promise.all` | Mở goroutine, chờ bằng `sync.WaitGroup` hoặc channel | `CompletableFuture`, executor, virtual thread |
| I/O chặn có làm đứng cả process không | Có, nhưng chỉ ảnh hưởng một request (mỗi worker một request) | Có: một lời gọi chặn làm đứng **mọi** request của process | Không: runtime chuyển goroutine khác sang chạy | Chỉ chặn thread đó |
| Trạng thái giữa request | Không có (share-nothing) | Có, process sống lâu | Có | Có |

Mô hình share-nothing của PHP đơn giản và an toàn (một request lỗi không làm hỏng request khác, không
có trạng thái chia sẻ để tranh chấp), đổi lại không có concurrency sẵn trong request. Với phần lớn ứng
dụng web, chỗ cần concurrency chỉ là vài lời gọi HTTP, và `Http::pool` là đủ.

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Tối ưu theo cảm tính (đổi nháy, bỏ Collection) | Phần được tối ưu chiếm tỉ lệ nhỏ, định luật Amdahl giới hạn lợi ích | Đo, profile, sửa khối rộng nhất trên flame graph (mục 1.3, 5) |
| So sánh bằng trung bình hoặc một lần chạy | Trung bình bị vài giá trị cực lớn kéo lệch; một lần chạy có thể trùng lúc máy bận | Dùng p50/p95, chạy nhiều lần, lấy median (mục 1.2, 3.3) |
| Đo bằng `microtime()` không tham số | Trả về chuỗi `"msec sec"`, trừ chuỗi cho nhau là sai | `hrtime(true)` cho đo thời gian (mục 3.1, 3.2) |
| Benchmark bằng CLI rồi suy ra web | CLI mặc định không bật OPcache, có thể đang nạp Xdebug | Bật `opcache.enable_cli`, tắt Xdebug, hoặc đo trên môi trường giống production (mục 3.5) |
| Cài Xdebug trên production | Mode mặc định là `develop`, không phải `off` (chỉ `off` mới gần như không tốn gì); profile làm chậm nhiều | Không cài; nếu phải nạp thì `xdebug.mode=off` (mục 4.4) |
| Đọc flame graph theo trục ngang như dòng thời gian | Trục ngang được sắp theo chữ cái (hoặc theo độ lớn), không phải thời gian | Dùng timeline/flame chart khi cần thứ tự (mục 5.2) |
| Không phân biệt N+1 với một query chậm | Flame graph gộp các stack giống nhau | Xem số lần gọi, timeline (mục 5.4) |
| `in_array`, `array_shift`, `array_merge` trong vòng lặp lớn | Mỗi lần O(n), cả vòng lặp O(n²) | Tra key bằng `isset`, `SplQueue`, `array_merge(...$list)` (mục 6.7) |
| Nạp cả bảng hoặc cả file vào RAM | Bộ nhớ tăng theo dữ liệu, chạm `memory_limit` | Generator, xử lý theo lô (mục 6.6) |
| Tăng `memory_limit` thành `-1` để "sửa" lỗi hết bộ nhớ | Script vẫn ngốn RAM, giờ có thể làm cả server hết RAM | Sửa cách xử lý dữ liệu (mục 2.5) |
| Gọi `env()` ngoài thư mục `config/` | Sau `config:cache`, `.env` không được nạp, `env()` ra `null` cho biến chỉ có trong `.env` | Chỉ gọi `env()` trong `config/*.php`, code dùng `config()` (mục 7.3) |
| Chạy `optimize:clear` trên production để "làm mới" | Nó xoá cả dữ liệu trong cache store mặc định | Chạy lại `optimize` (mục 7.2) |
| Bỏ code chặn vào Fiber và mong chạy đồng thời | Fiber không biến I/O chặn thành non-blocking | Dùng `Http::pool`, process, hoặc thư viện async có driver riêng (mục 8.7) |
| Gửi đồng thời không timeout, không kiểm tra lỗi từng phần | Một API treo giữ cả request; phần tử lỗi là exception chứ không phải response | Timeout từng request, kiểm tra `instanceof Throwable` (mục 8.5) |

## Tóm tắt chương

- Hiệu năng gồm latency, throughput, tài nguyên. Đánh giá bằng percentile (p95, p99), không bằng trung
  bình.
- Đo trước khi tối ưu: theo định luật Amdahl, lợi ích bị giới hạn bởi tỉ lệ thời gian của phần được
  tối ưu. Quy trình: đo, phân rã, tái hiện, profile, sửa chỗ tốn nhất, đo lại.
- Bốn loại nút thắt: I/O, database, CPU, bộ nhớ (cộng thêm chờ worker). Wall time lớn hơn CPU time
  nhiều nghĩa là đang chờ.
- Tự đo bằng `hrtime(true)` (monotonic, nano giây) và `memory_get_peak_usage()`; micro-benchmark cần
  warm-up, lặp nhiều lần, median, và điều kiện giống thật.
- Profiler instrumenting (Xdebug, SPX) cho số lần gọi chính xác nhưng overhead lớn, phóng đại hàm nhỏ;
  sampling (Excimer, SPX sampling) nhẹ, dùng được trên production. Inclusive để đi từ trên xuống,
  exclusive để tìm chỗ đốt thời gian.
- Flame graph: chiều rộng là tỉ lệ thời gian, trục ngang không phải thời gian, tìm "cao nguyên".
- Tối ưu nên làm theo thứ tự: OPcache, autoloader tối ưu, cache khởi động của Laravel; rồi N+1, index;
  rồi cache, đồng thời, queue; rồi generator và cấu trúc dữ liệu đúng.
- `php artisan optimize` chạy `config:cache`, `event:cache`, `route:cache`, `view:cache`; sau
  `config:cache` chỉ được gọi `env()` trong file config.
- Trong một request PHP chạy tuần tự. Gọi nhiều HTTP cùng lúc bằng `curl_multi`/`Http::pool`; việc nặng
  thì process con hoặc queue. Fiber chỉ là viên gạch cho thư viện async, không tự tạo concurrency.

## Câu hỏi tự kiểm tra

1. Một endpoint có trung bình 120 ms nhưng người dùng vẫn phàn nàn chậm. Bạn cần xem thêm số liệu gì,
   và vì sao? (mục 1.2)
2. Một hàm chiếm 5% thời gian request. Làm hàm đó nhanh gấp 10 lần thì request nhanh hơn khoảng bao
   nhiêu phần trăm? Tính bằng định luật Amdahl.
3. Vì sao manual PHP khuyên dùng `hrtime()` thay vì `microtime()` để đo hiệu năng?
4. Profile cho thấy một request có wall time 900 ms nhưng CPU time chỉ 80 ms. Nút thắt nhiều khả năng
   thuộc loại nào, và bạn sẽ tìm tiếp ở đâu? (mục 2.6)
5. Phân biệt inclusive time và exclusive time. Hàm nào thường có inclusive lớn nhưng exclusive gần 0?
6. Vì sao profiler instrumenting có thể làm một hàm nhỏ trông tốn hơn thực tế? Sampling khắc phục điều
   đó thế nào, và đánh đổi gì?
7. Trên flame graph, `PDOStatement::execute` là một khối rộng 40%. Bạn có kết luận ngay được là có một
   query chậm không? (mục 5.4)
8. Composer có những mức tối ưu autoloader nào? Mức nào có thể gây lỗi "class not found" và trong tình
   huống nào?
9. Sau khi deploy với `php artisan optimize`, một tính năng đọc `env('PAYMENT_KEY')` trong service bị
   lỗi. Giải thích nguyên nhân và cách sửa đúng.
10. Đặt `PDO::query()` vào ba Fiber khác nhau có làm ba query chạy đồng thời không? Vì sao? (mục 8.7)

## Bài tập

1. **Benchmark có kỷ luật.** Viết script so sánh ba cách đếm số phần tử xuất hiện trong cả hai danh
   sách số nguyên (mỗi danh sách 50.000 phần tử): `in_array` trong vòng lặp, `array_flip` + `isset`,
   và `array_intersect`. Dùng hàm `bench()` ở mục 3.3 (warm-up, 7 lần, median). Chạy với cỡ 1.000,
   10.000, 50.000 và ghi nhận xét: thời gian tăng theo cỡ dữ liệu như thế nào với từng cách?
2. **Mở rộng profiler đồ chơi.** Thêm vào `ToyProfiler` ở mục 4.3: (a) đo bộ nhớ đỉnh mỗi hàm bằng
   `memory_get_peak_usage()`/`memory_reset_peak_usage()`; (b) phương thức ghi folded stacks ra file.
   Nếu có Perl, đưa file vào `flamegraph.pl` để tạo SVG và mở bằng trình duyệt.
3. **Săn N+1.** Dựa trên ví dụ SQLite ở mục 6.4, thêm bảng `comments` (mỗi bài vài bình luận). Viết
   trang "danh sách 50 bài kèm tên tác giả và số bình luận" theo ba cách: N+1, `WHERE IN`, và một query
   có `JOIN` + `GROUP BY`. In số query và thời gian của từng cách (đo với `bench()`).
4. **Bộ nhớ khi xử lý file lớn.** Viết script sinh file CSV 500.000 dòng, rồi tính tổng một cột theo
   hai cách: `file()` nạp cả file, và generator đọc từng dòng bằng `fgetcsv()` (nhớ truyền tham số
   `$escape`). In `memory_get_peak_usage()` của từng cách và giải thích chênh lệch.

## Đọc thêm

- PHP manual: [hrtime](https://www.php.net/manual/en/function.hrtime.php),
  [microtime](https://www.php.net/manual/en/function.microtime.php),
  [memory_get_usage](https://www.php.net/manual/en/function.memory-get-usage.php),
  [memory_reset_peak_usage](https://www.php.net/manual/en/function.memory-reset-peak-usage.php),
  [getrusage](https://www.php.net/manual/en/function.getrusage.php),
  [OPcache runtime configuration](https://www.php.net/manual/en/opcache.configuration.php),
  [Fibers](https://www.php.net/manual/en/language.fibers.php),
  [curl_multi_exec](https://www.php.net/manual/en/function.curl-multi-exec.php)
- Xdebug: [Profiling](https://xdebug.org/docs/profiler), [Flame Graphs](https://xdebug.org/docs/flamegraphs)
- [SPX README](https://github.com/NoiseByNorthwest/php-spx)
- [Blackfire documentation](https://docs.blackfire.io/), [Tideways documentation](https://support.tideways.com/documentation/)
- [Excimer (MediaWiki)](https://www.mediawiki.org/wiki/Excimer) và bài
  [Profiling PHP in production at scale](https://techblog.wikimedia.org/2021/03/03/profiling-php-in-production-at-scale/)
- Brendan Gregg: [Flame Graphs](https://www.brendangregg.com/flamegraphs.html)
- Composer: [Autoloader optimization](https://getcomposer.org/doc/articles/autoloader-optimization.md)
- Laravel 13.x: [Deployment (Optimization)](https://laravel.com/docs/13.x/deployment#optimization),
  [Configuration caching](https://laravel.com/docs/13.x/configuration#configuration-caching),
  [HTTP Client: Concurrent Requests](https://laravel.com/docs/13.x/http-client#concurrent-requests),
  [Concurrency](https://laravel.com/docs/13.x/concurrency),
  [Processes](https://laravel.com/docs/13.x/processes),
  [Cache](https://laravel.com/docs/13.x/cache),
  [Helpers: Benchmarking](https://laravel.com/docs/13.x/helpers#benchmarking),
  [Database: Monitoring Cumulative Query Time](https://laravel.com/docs/13.x/database#monitoring-cumulative-query-time),
  [Eloquent: Preventing Lazy Loading](https://laravel.com/docs/13.x/eloquent-relationships#preventing-lazy-loading)
- [ReactPHP](https://reactphp.org/), [AMPHP](https://amphp.org/), [Swoole](https://github.com/swoole/swoole-src)
- Donald Knuth, "Structured Programming with go to Statements", ACM Computing Surveys, 1974
