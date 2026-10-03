# Chương 14. File, stream, JSON và thời gian

> [← Mục lục](README.md) · [← Chương 13: Generator, iterator và SPL](13-generator-iterator-spl.md) · [Chương 15: PHP và HTTP: request, response, session, cookie, upload →](15-php-va-web.md)

**Bạn sẽ học được:**

- Đọc và ghi file theo hai kiểu (cả file một lần, hoặc từng phần qua file handle), ghi file an toàn
  không để người khác thấy file ghi dở, khoá file bằng `flock` khi nhiều tiến trình cùng ghi.
- Đường dẫn, thư mục và quyền file trên Linux, đủ để hiểu lỗi "Permission denied" trên server.
- Stream và stream wrapper: vì sao `fopen()` mở được cả file, bộ nhớ, stdin và URL; đọc ghi CSV đúng
  chuẩn, kể cả thay đổi về tham số `escape` của PHP 8.4; `SplFileObject`.
- JSON: chuyển qua lại giữa PHP và JSON, các flag hay dùng, bắt lỗi bằng `JSON_THROW_ON_ERROR`, số
  lớn, UTF-8 và `json_validate()` (PHP 8.3).
- Ngày giờ: Unix timestamp, `DateTimeImmutable` thay cho `DateTime`, timezone, `DateInterval`,
  `DatePeriod`, và các bẫy về timezone, cuối tháng, giờ mùa hè (DST).
- Tiền: vì sao không được dùng float, cách tính bằng số nguyên và bằng `bcmath`.

**Cần biết trước:** [Chương 04: Kiểu dữ liệu](04-kieu-du-lieu.md) (int, float, null),
[Chương 05: Chuỗi](05-chuoi.md) (byte và ký tự, UTF-8), [Chương 06: Mảng](06-mang.md) (list và mảng
có key), [Chương 09: OOP cơ bản](09-oop-co-ban.md), [Chương 12: Lỗi và
exception](12-loi-exception.md) và [Chương 13: Generator](13-generator-iterator-spl.md) (đọc file lớn
theo từng dòng).

Cách chạy ví dụ: lưu thành file `.php` rồi chạy `php ten-file.php`. Ví dụ viết cho PHP 8.5 và output
ghi trong comment là output trên 8.5. Các ví dụ về file đều đọc ghi trong thư mục chứa file `.php`
(`__DIR__`) và tự xoá file đã tạo (trừ file khoá `import.lock` ở mục 3.3, cố ý để lại). Máy chưa cài PHP thì dùng Docker, chạy trong thư mục chứa file:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

## 1. Đọc và ghi file

### 1.1 File và hai cách làm việc với file trong PHP

*File* là một dãy byte được hệ điều hành lưu trên đĩa, có tên và nằm trong một thư mục. Hệ điều hành
không quan tâm dãy byte đó là văn bản, ảnh hay JSON: ý nghĩa là do chương trình đọc nó tự hiểu. Vì
vậy mọi hàm file của PHP làm việc với *string* theo nghĩa dãy byte (chương 05), không phải "chuỗi ký
tự". Một chữ `ò` trong file UTF-8 chiếm 2 byte, và các hàm file đếm 2.

Một backend PHP đọc ghi file trong rất nhiều việc: ghi log, đọc file cấu hình, xuất báo cáo CSV, nhận
file người dùng upload, cache ra đĩa. PHP cho bạn hai kiểu làm việc:

| Kiểu | Hàm chính | Khi nào dùng |
|---|---|---|
| Cả file một lần | `file_get_contents()`, `file_put_contents()`, `file()` | File nhỏ (cấu hình, template, JSON vài MB). Code ngắn, ít lỗi |
| Qua *file handle*, từng phần | `fopen()`, `fgets()`, `fread()`, `fwrite()`, `fclose()` | File lớn (log, CSV hàng triệu dòng), ghi dần, cần khoá file, cần nhảy tới vị trí bất kỳ |

Điểm khác cốt lõi là bộ nhớ. Kiểu thứ nhất nạp toàn bộ nội dung vào một biến, file 2 GB cần ít nhất
2 GB RAM và chắc chắn vượt `memory_limit` (giới hạn bộ nhớ của một script, cấu hình trong `php.ini`).
Kiểu thứ hai chỉ giữ trong RAM phần đang xử lý.

### 1.2 Đọc và ghi cả file

```php
<?php
declare(strict_types=1);

$path = __DIR__ . '/ghi-chu.txt';

// Ghi cả file: tạo mới nếu chưa có, ghi đè nếu đã có. Trả về số byte đã ghi
$bytes = file_put_contents($path, "dòng 1\ndòng 2\n");
var_dump($bytes);                       // in ra: int(16)  ("dòng 1\n" là 8 byte vì "ò" chiếm 2)

// Ghi nối vào cuối file thay vì ghi đè
file_put_contents($path, "dòng 3\n", FILE_APPEND);

// Đọc cả file thành một chuỗi
$content = file_get_contents($path);
var_dump(strlen($content));             // in ra: int(24)

// Đọc cả file thành mảng, mỗi phần tử là một dòng
$raw = file($path);
var_dump($raw[0]);                      // in ra: string(8) "dòng 1
                                        // "   <- còn nguyên ký tự xuống dòng ở cuối
$lines = file($path, FILE_IGNORE_NEW_LINES);
var_dump($lines[0]);                    // in ra: string(7) "dòng 1"

unlink($path);                          // xoá file
```

Những điều cần nhớ về ba hàm này (theo PHP manual):

- `file_put_contents($filename, $data, $flags)` tương đương gọi lần lượt `fopen()`, `fwrite()`,
  `fclose()`. Nó tạo file nếu chưa có, nhưng không tạo thư mục: thư mục cha chưa tồn tại thì lỗi.
  `$data` có thể là string, mảng một chiều (được nối lại như `implode('', $data)`) hoặc một stream.
- Các flag của `file_put_contents()` ghép bằng `|`: `FILE_APPEND` (ghi nối vào cuối), `LOCK_EX` (lấy
  khoá độc quyền trong lúc ghi, xem mục 3).
- `file()` trả mảng các dòng, mỗi dòng còn ký tự xuống dòng ở cuối, trừ khi truyền
  `FILE_IGNORE_NEW_LINES`. Thêm `FILE_SKIP_EMPTY_LINES` để bỏ dòng rỗng (flag này chỉ có tác dụng khi
  đi cùng `FILE_IGNORE_NEW_LINES`, vì nếu giữ `\n` thì không dòng nào rỗng cả).
- `file_get_contents()` có thêm tham số `$offset` và `$length` để đọc một đoạn.

### 1.3 Mở file và đọc ghi từng phần

`fopen()` trả về một *file handle*: một giá trị kiểu `resource` (loại `stream`) đại diện cho file đang
mở. Bên trong, handle giữ một *file descriptor* của hệ điều hành và một *con trỏ file* (file pointer):
vị trí byte mà lần đọc hoặc ghi tiếp theo sẽ bắt đầu. Mỗi lần đọc/ghi, con trỏ tiến lên đúng số byte
vừa xử lý.

```
file trên đĩa:   a l p h a \n b e t a \n g a m m a
vị trí byte:     0 1 2 3 4 5  6 7 8 9 10 11 ...
                 ^
                 con trỏ sau fopen(..., 'r')
fgets() lần 1 -> "alpha\n", con trỏ nhảy tới 6
fgets() lần 2 -> "beta\n",  con trỏ nhảy tới 11
```

Tham số thứ hai của `fopen()` là *mode*, quyết định đọc hay ghi, con trỏ đặt ở đâu, và làm gì với
nội dung cũ:

| Mode | Đọc | Ghi | File chưa có | File đã có | Con trỏ ban đầu |
|---|---|---|---|---|---|
| `r` | có | | lỗi | giữ nguyên | đầu file |
| `r+` | có | có | lỗi | giữ nguyên | đầu file |
| `w` | | có | tạo mới | xoá rỗng (truncate) | đầu file |
| `w+` | có | có | tạo mới | xoá rỗng | đầu file |
| `a` | | có | tạo mới | giữ nguyên | cuối file, mọi lần ghi luôn nối vào cuối |
| `a+` | có | có | tạo mới | giữ nguyên | cuối file; `fseek()` chỉ đổi vị trí đọc, ghi vẫn luôn nối vào cuối |
| `x` | | có | tạo mới | lỗi (trả `false` + warning) | đầu file |
| `x+` | có | có | tạo mới | lỗi | đầu file |
| `c` | | có | tạo mới | giữ nguyên, không xoá | đầu file |
| `c+` | có | có | tạo mới | giữ nguyên | đầu file |

Có thể thêm `b` vào cuối mode (`rb`, `wb`) để chỉ rõ chế độ nhị phân. Trên Linux, `b` không làm gì
(mặc định đã là nhị phân); trên Windows còn có chế độ `t` tự đổi `\n` thành `\r\n`, manual khuyên
không dùng `t`. Thói quen tốt là luôn dùng `rb`/`wb` cho file nhị phân để code chạy giống nhau trên
mọi hệ điều hành.

Hai mode ít người biết nhưng quan trọng:

- `x` tạo file mới và thất bại nếu file đã có. Hệ điều hành kiểm tra "đã có chưa" và tạo file trong
  cùng một bước (cờ `O_CREAT|O_EXCL` của lời gọi hệ thống `open(2)`), nên hai tiến trình cùng chạy
  `fopen($p, 'x')` thì chỉ một bên thành công. Viết `if (!file_exists($p)) { fopen($p, 'w'); }` thì
  không có bảo đảm đó (mục 3.1 giải thích vì sao).
- `c` mở để ghi mà không xoá nội dung cũ. Dùng khi cần khoá file trước rồi mới xoá: mở bằng `w` thì
  file bị xoá rỗng ngay lúc mở, trước khi bạn kịp lấy khoá (mục 3.3).

Đọc ghi qua handle:

```php
<?php
declare(strict_types=1);

$path = __DIR__ . '/log.txt';

$fh = fopen($path, 'w');                 // mở để ghi, xoá rỗng nếu đã có
if ($fh === false) {
    throw new RuntimeException("Không mở được $path");
}
var_dump(get_resource_type($fh));        // in ra: string(6) "stream"

fwrite($fh, "alpha\n");
fwrite($fh, "beta\n");
fwrite($fh, "gamma");                    // dòng cuối không có \n
fclose($fh);                             // đóng handle, trả file descriptor cho hệ điều hành

$fh = fopen($path, 'r');
while (($line = fgets($fh)) !== false) { // fgets đọc tới hết dòng, gồm cả "\n"
    echo json_encode($line), PHP_EOL;    // json_encode để thấy rõ "\n"
}
// in ra: "alpha\n"
//        "beta\n"
//        "gamma"
var_dump(feof($fh));                     // in ra: bool(true)

rewind($fh);                             // đưa con trỏ về đầu file
var_dump(ftell($fh));                    // in ra: int(0)
var_dump(fread($fh, 3));                 // in ra: string(3) "alp"
var_dump(ftell($fh));                    // in ra: int(3)
fseek($fh, -5, SEEK_END);                // đặt con trỏ cách cuối file 5 byte
var_dump(fread($fh, 100));               // in ra: string(5) "gamma" (hết file thì trả ít hơn 100)
fclose($fh);
unlink($path);
```

Các hàm trong ví dụ:

| Hàm | Làm gì |
|---|---|
| `fgets($fh)` | Đọc tới hết dòng (gồm `\n`), hoặc tới hết file. Hết dữ liệu thì trả `false`. Có tham số `$length` để giới hạn: đọc tối đa `$length - 1` byte |
| `fread($fh, $n)` | Đọc tối đa `$n` byte, không quan tâm dòng. Dùng cho file nhị phân |
| `fwrite($fh, $s)` | Ghi chuỗi, trả số byte đã ghi hoặc `false` |
| `feof($fh)` | `true` khi một lần đọc trước đó đã chạm cuối file |
| `ftell`, `fseek`, `rewind` | Đọc vị trí con trỏ, đặt con trỏ (`SEEK_SET` tính từ đầu, `SEEK_CUR` từ vị trí hiện tại, `SEEK_END` từ cuối), về đầu |
| `fclose($fh)` | Đóng handle |
| `stream_get_contents($fh)` | Đọc phần còn lại của stream thành chuỗi |

⚠️ Bẫy kinh điển: dùng `feof()` làm điều kiện vòng lặp.

```php
<?php
declare(strict_types=1);

$path = __DIR__ . '/hai-dong.txt';
file_put_contents($path, "a\nb\n");      // file kết thúc bằng \n, như hầu hết file text

$fh = fopen($path, 'r');
while (!feof($fh)) {                     // SAI: hỏi "hết file chưa" TRƯỚC khi đọc
    $line = fgets($fh);
    var_dump($line);
}
fclose($fh);
// in ra: string(2) "a
// "
// string(2) "b
// "
// bool(false)       <- vòng lặp chạy thêm một lần và nhận false
unlink($path);
```

Vì sao: `feof()` chỉ trả `true` sau khi một lần đọc đã thử đọc quá cuối file. Sau khi đọc `"b\n"`, con
trỏ đứng ở cuối file nhưng chưa ai "chạm" vào cuối, nên `feof()` vẫn `false`. Lần lặp thứ ba
`fgets()` mới phát hiện hết dữ liệu và trả `false`. Với `strict_types`, truyền `false` đó vào hàm
nhận `string` sẽ gây `TypeError`. Cách đúng là kiểm tra chính giá trị trả về:
`while (($line = fgets($fh)) !== false)`.

Không gọi `fclose()` thì sao? PHP tự đóng handle khi biến giữ nó không còn được tham chiếu, và chắc
chắn đóng mọi handle khi script kết thúc. Nhưng nên đóng sớm và tường minh: một worker chạy lâu (queue
worker, Octane) mở file trong vòng lặp mà quên đóng sẽ cạn số file descriptor hệ điều hành cho phép
(lỗi "Too many open files"). Mẫu an toàn là `try { ... } finally { fclose($fh); }`.

### 1.4 Hàm file báo lỗi bằng warning, không phải exception

Các hàm file của PHP ra đời trước khi PHP có exception. Khi thất bại, chúng trả `false` và phát một
*warning* (`E_WARNING`), chứ không ném exception:

```php
<?php
declare(strict_types=1);

$content = file_get_contents(__DIR__ . '/khong-ton-tai.txt');
// Warning: file_get_contents(.../khong-ton-tai.txt): Failed to open stream: No such file or directory in ...
var_dump($content);                          // in ra: bool(false)
echo error_get_last()['message'], PHP_EOL;   // in ra: file_get_contents(...): Failed to open stream: ...
```

Hệ quả:

- Script không dừng. Nếu không kiểm tra, `false` chảy tiếp vào code phía sau và gây lỗi ở chỗ khác
  khó tìm (với `strict_types` thường là `TypeError` khi truyền `false` vào tham số `string`).
- ⚠️ Luôn so sánh bằng `=== false`. `file_get_contents()` của một file rỗng trả `""`, mà `""` cũng
  "falsy": viết `if (!$content)` sẽ coi file rỗng là lỗi. Tương tự, `fwrite()` ghi chuỗi rỗng trả `0`.
- Muốn có exception thì tự ném sau khi kiểm tra (như các ví dụ trong chương này), hoặc đăng ký error
  handler đổi mọi warning thành `ErrorException` ([chương 12](12-loi-exception.md)). Framework như
  Laravel làm sẵn việc đổi này, nên trong Laravel một `file_get_contents()` hỏng sẽ thành exception.
- ⚠️ Đừng dùng toán tử `@` (`@file_get_contents(...)`) để "tắt" warning rồi bỏ qua kết quả: lỗi vẫn
  xảy ra, chỉ là bạn không còn thấy nó.

### 1.5 Ghi file an toàn: ghi file tạm rồi đổi tên

`file_put_contents($path, $data)` không phải một thao tác "tất cả hoặc không có gì". Nó mở file và
xoá rỗng file trước, rồi mới ghi dữ liệu. Giữa hai bước đó:

- Một tiến trình khác đọc file sẽ thấy file rỗng hoặc ghi dở một nửa.
- Nếu tiến trình ghi chết giữa chừng (hết RAM, bị kill, mất điện), file nằm lại ở trạng thái hỏng.

Với file cấu hình hay file cache mà nhiều request cùng đọc, đó là lỗi thật. Cách làm chuẩn là *ghi
nguyên tử* (atomic write): ghi toàn bộ nội dung vào một file tạm, rồi `rename()` file tạm thành tên
đích.

```php
<?php
declare(strict_types=1);

/**
 * Ghi file nguyên tử: người đọc chỉ thấy bản cũ hoặc bản mới, không bao giờ thấy bản ghi dở.
 */
function writeAtomic(string $path, string $data): void
{
    $dir = dirname($path);
    // File tạm phải nằm cùng thư mục (cùng filesystem) với file đích thì rename mới nguyên tử
    $tmp = tempnam($dir, '.tmp-');
    if ($tmp === false) {
        throw new RuntimeException("Không tạo được file tạm trong $dir");
    }
    try {
        if (file_put_contents($tmp, $data) !== strlen($data)) {
            throw new RuntimeException("Ghi file tạm $tmp thất bại");
        }
        chmod($tmp, 0644);                  // tempnam tạo file quyền 0600, nới ra cho đúng ý (mục 2.4)
        if (!rename($tmp, $path)) {         // thay file đích trong một bước
            throw new RuntimeException("Không đổi tên được $tmp thành $path");
        }
    } catch (Throwable $e) {
        if (is_file($tmp)) {
            unlink($tmp);                   // dọn file tạm khi có lỗi
        }
        throw $e;
    }
}

$config = __DIR__ . '/config.json';
writeAtomic($config, '{"version": 1}');
writeAtomic($config, '{"version": 2}');
echo file_get_contents($config), PHP_EOL;    // in ra: {"version": 2}
printf("%o\n", fileperms($config) & 0777);    // in ra: 644
unlink($config);
```

Vì sao cách này đúng:

- `tempnam($dir, $prefix)` tạo một file mới có tên duy nhất trong `$dir`, quyền `0600`, và trả về
  đường dẫn. Không có hai tiến trình nào trùng file tạm.
- Trên Linux/macOS, `rename()` của PHP gọi lời gọi hệ thống `rename(2)`. Chuẩn POSIX bảo đảm nếu tên
  đích đã tồn tại thì nó được thay thế nguyên tử: mọi tiến trình mở file theo tên đó hoặc thấy file
  cũ, hoặc thấy file mới.
- ⚠️ Bảo đảm này chỉ có khi file tạm và file đích nằm trên cùng một filesystem. Nếu khác (ví dụ file
  tạm ở `/tmp` mà `/tmp` là một phân vùng riêng), hệ điều hành không đổi tên được và PHP tự lùi về
  "copy rồi xoá", không còn nguyên tử. Vì vậy ví dụ tạo file tạm bằng `tempnam(dirname($path), ...)`
  chứ không dùng `sys_get_temp_dir()`.
- Muốn chịu được cả mất điện thì trước khi `rename()` còn phải đẩy dữ liệu xuống đĩa thật bằng
  `fsync()` (có từ PHP 8.1). Lý do: `fwrite()` trả về khi dữ liệu mới nằm trong bộ đệm của hệ điều
  hành, chưa chắc đã nằm trên đĩa. Đa số ứng dụng web không cần mức này.

Laravel có sẵn `File::replace($path, $content)` dùng đúng kỹ thuật này: `tempnam()` trong cùng thư
mục, `chmod()` lại quyền, `file_put_contents()` vào file tạm, rồi `rename()`.

## 2. Đường dẫn, thư mục và quyền

### 2.1 Đường dẫn tuyệt đối, tương đối và `__DIR__`

*Đường dẫn* (path) chỉ vị trí của file trong cây thư mục. Có hai loại:

- *Đường dẫn tuyệt đối* bắt đầu từ gốc: `/var/www/app/storage/logs/laravel.log` (Linux, macOS),
  `C:\www\app\...` (Windows).
- *Đường dẫn tương đối* không bắt đầu từ gốc: `data/users.csv`, `../config.json`. Nó được ghép với
  *thư mục làm việc hiện tại* (current working directory, xem bằng `getcwd()`) để ra đường dẫn thật.
  `.` là thư mục hiện tại, `..` là thư mục cha.

⚠️ Bẫy hay gặp nhất: đường dẫn tương đối tính theo thư mục làm việc của tiến trình, không phải theo
thư mục chứa file `.php`. Chạy CLI thì thư mục làm việc là nơi bạn đứng khi gõ lệnh:

```
/home/u/app/
├── scripts/import.php      <- trong file: file_get_contents('data.csv')
└── scripts/data.csv

$ cd /home/u/app/scripts && php import.php      -> đọc /home/u/app/scripts/data.csv   (chạy được)
$ cd /home/u/app && php scripts/import.php      -> đọc /home/u/app/data.csv           (không thấy file)
cron chạy "php /home/u/app/scripts/import.php"  -> thư mục làm việc thường là thư mục home (HOME) của user sở hữu crontab
```

Cách tránh: ghép đường dẫn từ hằng `__DIR__` (thư mục chứa file đang chạy dòng code đó, chương 03)
hoặc từ một thư mục gốc của dự án. Laravel có sẵn các helper `base_path()`, `storage_path()`,
`config_path()`, `public_path()` trả đường dẫn tuyệt đối.

```php
$csv = __DIR__ . '/data.csv';                    // luôn đúng, dù chạy từ đâu
```

Dấu phân cách thư mục là `/` trên Linux, macOS và `\` trên Windows; hằng `DIRECTORY_SEPARATOR` cho
biết dấu của hệ điều hành đang chạy. Windows chấp nhận cả `/`, nên viết `/` trong code PHP là chạy
được ở mọi nơi.

### 2.2 Tách và chuẩn hoá đường dẫn

```php
<?php
declare(strict_types=1);

$p = '/var/www/app/storage/logs/laravel-2026-10-03.log';
var_dump(basename($p));             // in ra: string(22) "laravel-2026-10-03.log"
var_dump(basename($p, '.log'));     // in ra: string(18) "laravel-2026-10-03"
var_dump(dirname($p));              // in ra: string(25) "/var/www/app/storage/logs"
var_dump(dirname($p, 3));           // in ra: string(12) "/var/www/app"  (đi lên 3 cấp)

print_r(pathinfo('/backup/db.tar.gz'));
// in ra: Array
// (
//     [dirname] => /backup
//     [basename] => db.tar.gz
//     [extension] => gz          <- chỉ phần sau dấu chấm cuối cùng
//     [filename] => db.tar
// )
print_r(pathinfo('/home/u/.env'));
// in ra: Array ( [dirname] => /home/u [basename] => .env [extension] => env [filename] => )

var_dump(realpath(__DIR__ . '/./../' . basename(__DIR__)) === __DIR__);   // in ra: bool(true)
var_dump(realpath(__DIR__ . '/khong-co.txt'));                              // in ra: bool(false)
```

- `basename()`, `dirname()`, `pathinfo()` chỉ xử lý chuỗi, không nhìn vào ổ đĩa và không hiểu `..`.
  File không tồn tại vẫn tách được.
- `realpath()` thì có hỏi hệ điều hành: nó giải `.`, `..`, dấu `/` thừa và symlink, trả đường dẫn
  tuyệt đối "chuẩn". File không tồn tại thì trả `false`.
- ⚠️ `pathinfo()` lấy phần mở rộng theo dấu chấm cuối cùng: `db.tar.gz` có extension `gz`. Đừng dùng
  extension để quyết định file là loại gì khi file đến từ người dùng; đó là chuyện của chương 15 và
  17.

### 2.3 Kiểm tra file và thư mục

| Hàm | Trả về |
|---|---|
| `file_exists($p)` | `true` nếu là file hoặc thư mục tồn tại |
| `is_file($p)`, `is_dir($p)`, `is_link($p)` | Đúng loại hay không |
| `is_readable($p)`, `is_writable($p)` | Tiến trình PHP hiện tại có quyền đọc/ghi không |
| `filesize($p)` | Kích thước theo byte |
| `filemtime($p)` | Thời điểm sửa cuối, dạng Unix timestamp (mục 8.2) |
| `fileperms($p)` | Quyền (mục 2.5) |

Hai điều cần biết:

- *Stat cache*: để nhanh hơn, PHP ghi nhớ kết quả của các hàm trên cho một file trong suốt script.
  Nếu file có thể bị tiến trình khác thay đổi trong lúc script đang chạy (queue worker, daemon chạy
  hàng giờ), gọi `clearstatcache()` trước khi kiểm tra lại. `unlink()` tự xoá cache này.
- ⚠️ "Kiểm tra rồi mới làm" không an toàn khi có nhiều tiến trình. Giữa lúc `file_exists()` trả
  `false` và lúc bạn tạo file, tiến trình khác có thể đã tạo nó. Lỗi loại này gọi là *TOCTOU* (time of
  check to time of use). Muốn "tạo nếu chưa có" thì dùng mode `x` của `fopen()` (mục 1.3); muốn ghi
  không đụng nhau thì dùng khoá (mục 3).

### 2.4 Tạo, liệt kê, xoá

```php
<?php
declare(strict_types=1);

$base = __DIR__ . '/du-lieu';

// Tạo cả cây thư mục một lần (tham số thứ ba $recursive = true)
mkdir($base . '/2026/10', 0775, true);
touch($base . '/a.csv');                 // tạo file rỗng (hoặc cập nhật thời điểm sửa)
touch($base . '/b.csv');
touch($base . '/c.txt');

print_r(scandir($base));
// in ra: Array ( [0] => . [1] => .. [2] => 2026 [3] => a.csv [4] => b.csv [5] => c.txt )

print_r(array_map(basename(...), glob($base . '/*.csv')));
// in ra: Array ( [0] => a.csv [1] => b.csv )

var_dump(rmdir($base . '/2026'));
// Warning: rmdir(.../du-lieu/2026): Directory not empty in ...
// in ra: bool(false)                    <- rmdir chỉ xoá thư mục rỗng

// Dọn dẹp: xoá file trước, thư mục sau, từ trong ra ngoài
foreach (glob($base . '/*.*') as $f) {
    unlink($f);
}
rmdir($base . '/2026/10');
rmdir($base . '/2026');
rmdir($base);
```

| Việc | Hàm | Ghi chú |
|---|---|---|
| Tạo thư mục | `mkdir($dir, $perm = 0777, $recursive = false)` | Thư mục đã có thì trả `false` + warning |
| Xoá thư mục | `rmdir($dir)` | Chỉ xoá được thư mục rỗng |
| Xoá file | `unlink($file)` | |
| Đổi tên, di chuyển | `rename($from, $to)` | Ghi đè nếu đích là file đã có (mục 1.5) |
| Sao chép | `copy($from, $to)` | |
| Liệt kê | `scandir($dir)` | Có cả `.` và `..`, đã sắp xếp theo tên |
| Tìm theo mẫu | `glob($pattern)` | `*`, `?`, `[...]` như shell; không khớp gì thì trả mảng rỗng |
| Thư mục tạm của hệ thống | `sys_get_temp_dir()` | |
| Duyệt đệ quy | `RecursiveDirectoryIterator` | [Chương 13](13-generator-iterator-spl.md) |

⚠️ `mkdir()` khi nhiều tiến trình cùng chạy: hai request cùng thấy thư mục chưa có rồi cùng gọi
`mkdir()`, một bên sẽ nhận warning "File exists". Mẫu an toàn là thử tạo, nếu thất bại thì kiểm tra
lại xem thư mục đã có chưa:

```php
if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
    throw new RuntimeException("Không tạo được thư mục $dir");
}
```

(Dòng `mkdir()` vẫn có thể phát warning trong ca tranh chấp, nhưng code không còn coi đó là lỗi.)

### 2.5 Quyền file trên Linux

Mỗi file trên Linux có một *owner* (user sở hữu), một *group*, và ba nhóm quyền cho ba đối tượng:
owner, group, và *others* (mọi user còn lại). Mỗi nhóm gồm ba quyền:

| Quyền | Với file | Với thư mục | Giá trị |
|---|---|---|---|
| `r` (read) | Đọc nội dung | Liệt kê tên các mục bên trong | 4 |
| `w` (write) | Sửa nội dung | Tạo, xoá, đổi tên mục bên trong | 2 |
| `x` (execute) | Chạy như chương trình | Đi vào thư mục, truy cập mục bên trong | 1 |

Cộng giá trị lại được một chữ số cho mỗi nhóm, viết ở hệ bát phân (octal):

```
$ ls -l storage/logs/laravel.log          (chạy trong terminal của server)
-rw-r--r--  1 www-data www-data  20480 Oct  3 10:00 laravel.log
 └┬┘└┬┘└┬┘     └──┬───┘ └──┬───┘
 owner group others  owner    group
  rw-  r--  r--
  6    4    4      -> quyền 0644
```

- `0644`: owner đọc ghi, còn lại chỉ đọc. Mặc định hợp lý cho file.
- `0755`: owner toàn quyền, còn lại đọc và đi vào. Mặc định hợp lý cho thư mục.
- `0600`: chỉ owner đọc ghi. Dùng cho file bí mật (khoá riêng, file `.env`).

Trong PHP:

- ⚠️ Quyền phải viết ở hệ bát phân, có số `0` đứng đầu: `chmod($f, 0755)`. Viết `chmod($f, 755)` là
  số thập phân 755, tức bát phân `1363`, ra một bộ quyền vô nghĩa (manual cảnh báo đúng lỗi này).
  PHP 8.1 trở lên viết được `0o755` cho rõ ràng hơn (chương 04).
- `mkdir()` và việc tạo file đều bị *umask* lọc bớt quyền: quyền thật bằng quyền yêu cầu bỏ đi các bit
  có trong umask. Umask thường là `0022`, nên `mkdir($d, 0775)` cho ra `0755`, và `mkdir($d)` (mặc
  định `0777`) cho ra `0755`. Xem bằng `umask()`.
- `fileperms($f) & 0777` lấy phần quyền; in ra dạng bát phân bằng `printf('%o', ...)`.

Vì sao chuyện này quan trọng với backend: PHP chạy dưới user của tiến trình đang chạy nó. Trên server
thường gặp:

| Ai chạy PHP | User thường gặp |
|---|---|
| PHP-FPM phục vụ web ([chương 18](18-fpm-nginx-opcache.md)) | `www-data` (Debian/Ubuntu), `nginx` hoặc `apache` (tuỳ distro) |
| Lệnh CLI bạn gõ, cron, deploy script | User bạn đăng nhập, `deploy`, đôi khi `root` |

⚠️ Bug kinh điển trên Laravel: deploy script chạy `php artisan ...` bằng `root` hoặc `deploy`, lệnh đó
tạo file log mới `storage/logs/laravel.log` thuộc user đó với quyền `0644`. Sau đó FPM chạy bằng
`www-data` không ghi được vào file, và mọi request đều lỗi với thông báo của Monolog: `The stream or
file ".../laravel.log" could not be opened in append mode: Failed to open stream: Permission denied`.
Cách sửa đúng là chạy lệnh artisan bằng cùng user với FPM (`sudo -u www-data php artisan ...`) hoặc
đặt chung group, chứ không phải `chmod -R 777` (cho mọi user trên máy quyền ghi). Tài liệu deploy
của Laravel 13 ghi rõ: Laravel cần ghi vào `storage` và `bootstrap/cache`, nên user chạy web server
phải có quyền ghi vào hai thư mục này.

### 2.6 Đường dẫn từ người dùng: path traversal

Khi một phần đường dẫn đến từ request (tên file muốn tải, tên template...), kẻ tấn công có thể gửi
`../../../etc/passwd` để đi ra khỏi thư mục bạn định cho phép. Lỗi này gọi là *path traversal*.

```php
<?php
declare(strict_types=1);

function safePath(string $baseDir, string $userInput): string
{
    $base = realpath($baseDir);
    $full = realpath($baseDir . '/' . $userInput);
    // realpath đã giải hết "..", nên chỉ cần kiểm tra kết quả còn nằm trong $base
    if ($base === false || $full === false || !str_starts_with($full, $base . DIRECTORY_SEPARATOR)) {
        throw new InvalidArgumentException('Đường dẫn không hợp lệ');
    }
    return $full;
}
```

Đây chỉ là một lớp phòng thủ; [chương 17](17-bao-mat.md) nói đầy đủ về path traversal, upload và
`open_basedir`. Cách tốt nhất vẫn là không dùng tên file người dùng gửi lên: lưu file theo tên do bạn
sinh ra (ví dụ UUID) và giữ tên gốc trong database.

## 3. Khoá file với `flock`

### 3.1 Vấn đề: hai tiến trình cùng sửa một file

Trên server, nhiều tiến trình PHP chạy song song: mỗi request được một worker FPM riêng xử lý, cùng
lúc với cron và queue worker. Giả sử bạn đếm lượt xem bằng một file chứa con số, theo kiểu "đọc, cộng
một, ghi lại":

```php
$n = (int) file_get_contents($path);
file_put_contents($path, (string) ($n + 1));
```

Hai request chạy gần như đồng thời:

| Bước | Tiến trình A | Tiến trình B | File chứa |
|---|---|---|---|
| 1 | đọc được `41` | | `41` |
| 2 | | đọc được `41` | `41` |
| 3 | ghi `42` | | `42` |
| 4 | | ghi `42` | `42` |
| Kết quả | | | `42`, mất một lượt (đúng phải là `43`) |

Đây là *race condition*: kết quả phụ thuộc vào thứ tự xen kẽ ngẫu nhiên của các tiến trình. Nó còn có
thể tệ hơn mất một lượt: vì `file_put_contents()` xoá rỗng file trước khi ghi (mục 1.5), B có thể đọc
đúng lúc file đang rỗng, được `0`, rồi ghi `1`.

Cách sửa là bắt cả chuỗi "đọc, tính, ghi" chạy độc quyền: tại một thời điểm chỉ một tiến trình được
làm. Công cụ cho việc đó ở mức file là *khoá file* (file lock).

### 3.2 `flock()`: khoá chia sẻ và khoá độc quyền

`flock($handle, $operation)` đặt khoá lên file mà `$handle` đang mở. Có hai loại khoá, theo mô hình
"nhiều người đọc, một người ghi":

| Hằng | Loại | Ai được giữ cùng lúc |
|---|---|---|
| `LOCK_SH` | *Shared lock* (khoá chia sẻ, cho người đọc) | Nhiều tiến trình cùng giữ `LOCK_SH` được |
| `LOCK_EX` | *Exclusive lock* (khoá độc quyền, cho người ghi) | Chỉ một tiến trình, và khi đó không ai giữ `LOCK_SH` |
| `LOCK_UN` | Nhả khoá đang giữ | |
| `LOCK_NB` | Ghép thêm bằng `\|`: không chờ, lấy không được thì trả `false` ngay | |

| Đang có người giữ → Yêu cầu mới | `LOCK_SH` | `LOCK_EX` |
|---|---|---|
| Không ai giữ | được ngay | được ngay |
| Có người giữ `LOCK_SH` | được ngay | phải chờ |
| Có người giữ `LOCK_EX` | phải chờ | phải chờ |

Mặc định `flock()` *chặn* (block): tiến trình đứng chờ tới khi lấy được khoá. Khoá được nhả khi gọi
`flock($fh, LOCK_UN)`, khi `fclose($fh)`, hoặc khi handle bị giải phóng; tiến trình chết thì hệ điều
hành đóng mọi file nó đang mở và khoá cũng được nhả, nên không có chuyện khoá bị treo mãi vì một tiến
trình crash.

Đếm lượt xem đúng cách:

```php
<?php
declare(strict_types=1);

/** Tăng bộ đếm lưu trong file, an toàn khi nhiều tiến trình cùng gọi. */
function incrementCounter(string $path): int
{
    $fh = fopen($path, 'c+');                // đọc + ghi, tạo nếu chưa có, KHÔNG xoá nội dung
    if ($fh === false) {
        throw new RuntimeException("Không mở được $path");
    }
    try {
        if (!flock($fh, LOCK_EX)) {          // chờ tới khi lấy được khoá độc quyền
            throw new RuntimeException("Không khoá được $path");
        }
        $current = (int) stream_get_contents($fh);   // file rỗng -> "" -> 0
        $next = $current + 1;
        ftruncate($fh, 0);                   // xoá nội dung cũ
        rewind($fh);                         // về đầu file trước khi ghi
        fwrite($fh, (string) $next);
        fflush($fh);                         // đẩy dữ liệu ra trước khi nhả khoá
        flock($fh, LOCK_UN);
        return $next;
    } finally {
        fclose($fh);                         // fclose cũng nhả khoá, kể cả khi có exception
    }
}

$path = __DIR__ . '/counter.txt';
echo incrementCounter($path), PHP_EOL;       // in ra: 1
echo incrementCounter($path), PHP_EOL;       // in ra: 2
echo incrementCounter($path), PHP_EOL;       // in ra: 3
unlink($path);
```

Những chi tiết nhỏ nhưng quyết định:

- Mở bằng `c+`, không phải `w+`. `w+` xoá rỗng file ngay lúc `fopen()`, tức là trước khi có khoá: một
  tiến trình khác đang giữ khoá và đọc file sẽ thấy file bị xoá dưới chân nó. PHP manual nêu đúng lý
  do này khi giới thiệu mode `c`.
- Xoá nội dung bằng `ftruncate()` sau khi đã có khoá, rồi `rewind()` vì `ftruncate()` không di chuyển
  con trỏ file.
- Có khoá, timeline của mục 3.1 trở thành:

| Bước | Tiến trình A | Tiến trình B | File chứa |
|---|---|---|---|
| 1 | `flock(LOCK_EX)` được ngay | | `41` |
| 2 | | `flock(LOCK_EX)`: phải chờ | `41` |
| 3 | đọc `41`, ghi `42`, nhả khoá | (vẫn chờ) | `42` |
| 4 | | lấy được khoá, đọc `42`, ghi `43` | `43` |

`file_put_contents($path, $data, LOCK_EX)` là cách viết tắt cho phía ghi: nó lấy `LOCK_EX` trong lúc
ghi. Nhưng chỉ phía ghi có khoá thì chưa đủ cho bài toán "đọc, tính, ghi", vì bước đọc nằm ngoài khoá.

### 3.3 Khoá không chờ: chống chạy trùng một job

Một job import chạy mỗi 5 phút bằng cron, nhưng có lần chạy mất 7 phút. Lần chạy sau bắt đầu khi lần
trước chưa xong, hai tiến trình cùng import một dữ liệu. Dùng `LOCK_NB` để lần sau thấy có người đang
giữ khoá thì thoát ngay:

```php
<?php
declare(strict_types=1);

$lock = fopen(__DIR__ . '/import.lock', 'c');   // file chỉ dùng làm "ổ khoá", nội dung không quan trọng
if ($lock === false) {
    throw new RuntimeException('Không mở được file khoá');
}
if (!flock($lock, LOCK_EX | LOCK_NB, $wouldBlock)) {
    // $wouldBlock === 1 nghĩa là có tiến trình khác đang giữ khoá
    echo "Đang có một tiến trình import khác chạy, thoát.\n";
    exit(0);
}

echo "Bắt đầu import...\n";
// ... công việc dài ...
// Không cần nhả khoá tường minh: script kết thúc thì handle đóng và khoá được nhả.
// Biến $lock phải còn sống suốt thời gian làm việc, gán đè nó là mất khoá.
```

Laravel có sẵn `Schedule::command(...)->withoutOverlapping()` cho đúng nhu cầu này, nhưng nó không
dùng `flock`: nó dùng *cache lock* (khoá lưu trong cache store như Redis), mặc định hết hạn sau 24 giờ
([chương 29](29-laravel-queue-event-schedule-cache.md)).

### 3.4 Giới hạn của `flock`

- ⚠️ Khoá là *advisory* (tự nguyện): nó chỉ có tác dụng giữa những tiến trình cùng gọi `flock()`. Một
  tiến trình khác cứ `file_get_contents()` hay `file_put_contents()` không có `LOCK_EX` thì vẫn đọc
  ghi thoải mái, hệ điều hành không chặn. (Windows thì khác, khoá ở đó là bắt buộc.) Mọi chỗ đụng vào
  file phải theo cùng một quy ước.
- ⚠️ `flock` chỉ phối hợp các tiến trình trên cùng một máy. Ứng dụng chạy nhiều server sau load
  balancer, mỗi server có ổ đĩa riêng, thì khoá file trên server này không chặn được server kia. Khi
  đó cần khoá dùng chung: khoá trong database (`SELECT ... FOR UPDATE`, [chương 16](16-php-va-database.md)) hoặc Redis.
- Trên filesystem mạng (NFS) hay filesystem cũ như FAT, hành vi của `flock` phụ thuộc hệ điều hành và
  cấu hình; manual ghi rõ FAT không hỗ trợ và `flock()` luôn trả `false` ở đó. Đừng dựa vào `flock`
  trên ổ mạng.
- Cần khoá một file mà bạn sẽ mở bằng `w`? Khoá một file riêng (`data.lock`) thay vì chính file đó.
- Nhu cầu "đếm" thật trong ứng dụng web nên đặt ở database hoặc Redis (`INCR` là thao tác nguyên tử),
  không phải ở file. Ví dụ trên chỉ để hiểu cơ chế.

## 4. Stream và stream wrapper

### 4.1 Stream là gì

Ở mục 1, `fopen()` trả về một resource loại `stream`. *Stream* là khái niệm tổng quát hơn file: một
nguồn dữ liệu đọc tuần tự (hoặc một đích ghi tuần tự) theo từng đoạn byte. File trên đĩa là một loại
stream; dữ liệu trong RAM, đầu vào bàn phím, body của HTTP request, một kết nối mạng cũng là stream.

Điểm hay là mọi stream dùng chung một bộ hàm: `fopen`, `fgets`, `fread`, `fwrite`, `fclose`,
`file_get_contents`... Bạn viết một hàm nhận `resource $stream` và hàm đó chạy được với file, bộ nhớ
hay socket mà không cần sửa.

Loại stream được chọn bằng tiền tố `scheme://` trong đường dẫn. Phần code xử lý từng scheme gọi là
*stream wrapper*:

```
fopen("data.csv")                     ->  wrapper file://   (không ghi scheme thì mặc định là file)
fopen("php://memory")                 ->  wrapper php://    (bộ nhớ, stdin, stdout, input...)
fopen("compress.zlib://log.gz")       ->  wrapper zlib      (đọc ghi file gzip, giải nén trong suốt)
fopen("https://example.com/a.json")   ->  wrapper https://  (tải qua mạng)
fopen("data://text/plain;base64,...") ->  wrapper data://   (dữ liệu nằm ngay trong chuỗi, RFC 2397)
```

`stream_get_wrappers()` liệt kê các wrapper có trong bản PHP đang chạy. Bạn còn có thể tự đăng ký
wrapper của mình bằng `stream_wrapper_register()`; AWS SDK for PHP dùng cơ chế này để đăng ký wrapper
`s3://`, nhờ đó `file_get_contents('s3://bucket/key')` đọc được file trên S3.

### 4.2 Các stream `php://`

| Stream | Đọc/ghi | Dùng để |
|---|---|---|
| `php://stdin` | Đọc | Đầu vào chuẩn của tiến trình (dữ liệu gõ vào hoặc pipe vào CLI) |
| `php://stdout` | Ghi | Đầu ra chuẩn, ghi thẳng ra file descriptor, bỏ qua output buffering |
| `php://stderr` | Ghi | Đầu ra lỗi chuẩn, nơi nên ghi log/thông báo lỗi của script CLI |
| `php://input` | Đọc | Body thô của HTTP request (JSON API nhận dữ liệu qua đây, [chương 15](15-php-va-web.md)) |
| `php://output` | Ghi | Ghi vào cơ chế output giống `echo` (có đi qua output buffering) |
| `php://memory` | Đọc và ghi | Một "file" nằm hoàn toàn trong RAM |
| `php://temp` | Đọc và ghi | Như `php://memory`, nhưng vượt ngưỡng (mặc định 2 MB) thì chuyển sang file tạm trên đĩa |
| `php://filter` | Tuỳ | Áp bộ lọc lên một stream khác khi đọc/ghi |

Ở CLI, PHP mở sẵn ba hằng `STDIN`, `STDOUT`, `STDERR` tương ứng ba stream đầu; manual khuyên dùng
hằng thay vì tự `fopen('php://stdin', 'r')`.

```php
<?php
declare(strict_types=1);

// dem-dong.php: đếm số dòng từ stdin. Chạy trong terminal:
//   printf "a\nb\nc\n" | php dem-dong.php
$count = 0;
while (fgets(STDIN) !== false) {
    $count++;
}
fwrite(STDOUT, "Số dòng: $count\n");          // in ra: Số dòng: 3
fwrite(STDERR, "Xong.\n");                     // ra stderr: không lẫn vào dữ liệu nếu stdout bị pipe tiếp
```

Tách stdout và stderr quan trọng với script CLI: người dùng có thể chuyển kết quả sang file
(`php export.php > out.csv`) trong khi thông báo tiến độ và lỗi vẫn hiện trên màn hình.

### 4.3 `php://memory` và `php://temp`

Hai stream này cho bạn một "file" không có tên trên đĩa. Công dụng phổ biến: dựng nội dung bằng các
hàm chỉ làm việc với stream (như `fputcsv()`), rồi lấy ra thành chuỗi.

```php
<?php
declare(strict_types=1);

$mem = fopen('php://memory', 'r+');
fwrite($mem, "xin chào\n");
fwrite($mem, "tạm biệt\n");
rewind($mem);                                    // quay về đầu trước khi đọc, giống file thật
echo fgets($mem);                                // in ra: xin chào
var_dump(stream_get_meta_data($mem)['stream_type']);   // in ra: string(6) "MEMORY"
fclose($mem);                                    // đóng là mất dữ liệu: stream này không mở lại được

// php://temp giữ trong RAM tới ngưỡng maxmemory (byte), quá ngưỡng thì ghi ra file tạm
$tmp = fopen('php://temp/maxmemory:' . (5 * 1024 * 1024), 'r+');   // ngưỡng 5 MB
```

| | `php://memory` | `php://temp` |
|---|---|---|
| Lưu ở đâu | Luôn trong RAM | RAM, vượt ngưỡng thì chuyển sang file tạm (thư mục giống `sys_get_temp_dir()`) |
| Ngưỡng | Không có, dữ liệu lớn thì RAM tăng tới `memory_limit` | Mặc định 2 MB, đổi bằng `/maxmemory:NN` |
| Dùng khi | Biết chắc dữ liệu nhỏ | Dữ liệu có thể lớn (xuất file, tải file về) |

Guzzle (thư viện HTTP mà `Http::` của Laravel dùng bên dưới) tạo body của HTTP message (PSR-7) từ
chuỗi bằng `php://temp` vì lý do này: body nhỏ thì nhanh như RAM, body lớn không làm nổ bộ nhớ.

### 4.4 Bộ lọc, nén, sao chép stream

```php
<?php
declare(strict_types=1);

$f = __DIR__ . '/hello.txt';
file_put_contents($f, 'hello world');

// php://filter áp bộ lọc khi đọc
echo file_get_contents('php://filter/read=string.toupper/resource=' . $f), PHP_EOL;
// in ra: HELLO WORLD
echo file_get_contents('php://filter/read=convert.base64-encode/resource=' . $f), PHP_EOL;
// in ra: aGVsbG8gd29ybGQ=

// data:// (RFC 2397): dữ liệu nằm ngay trong URL
echo file_get_contents('data://text/plain;base64,SGVsbG8='), PHP_EOL;   // in ra: Hello

// compress.zlib://: ghi và đọc file .gz, nén/giải nén trong suốt
$gz = __DIR__ . '/app.log.gz';
file_put_contents('compress.zlib://' . $gz, str_repeat("dòng log\n", 1000));
echo strlen(file_get_contents('compress.zlib://' . $gz)), PHP_EOL;       // in ra: 10000
var_dump(filesize($gz) < 10000);                                         // in ra: bool(true)

// Sao chép từ stream này sang stream khác theo từng khối, không nạp hết vào RAM
$src = fopen($f, 'r');
$dst = fopen('php://memory', 'w+');
var_dump(stream_copy_to_stream($src, $dst));                             // in ra: int(11)

unlink($f);
unlink($gz);
```

`compress.zlib://` cần extension zlib (bản PHP chính thức trên Docker và đa số distro đều có).
`stream_copy_to_stream()` là cách đúng để chuyển một file lớn đi nơi khác (ví dụ từ upload sang
storage): bộ nhớ dùng không phụ thuộc kích thước file.

### 4.5 Stream qua mạng, context và rủi ro

Với `allow_url_fopen = 1` (giá trị mặc định trong `php.ini`), các hàm file mở được cả URL:

```php
<?php
declare(strict_types=1);

// Cần mạng để chạy. Context truyền tuỳ chọn cho wrapper http(s)
$context = stream_context_create([
    'http' => [
        'method'  => 'GET',
        'header'  => "Accept: application/json\r\n",
        'timeout' => 5.0,          // giây; mặc định lấy từ ini default_socket_timeout ("60")
    ],
]);
$body = file_get_contents('https://api.github.com/zen', false, $context);
// PHP 8.4+: lấy header của response vừa nhận
// var_dump(http_get_last_response_headers());
```

Biết là được, nhưng trong ứng dụng thật hãy dùng HTTP client (Guzzle, Laravel `Http::`) vì có retry,
timeout rõ ràng, xử lý mã lỗi và test được. Ba điều cần nhớ:

- ⚠️ Không đặt timeout thì một API chậm giữ worker PHP rất lâu: mỗi lần chờ đọc dữ liệu được phép kéo dài
  tới 60 giây (theo `default_socket_timeout`).
- Biến ma thuật `$http_response_header` (PHP tự tạo sau khi đọc URL) bị deprecated từ PHP 8.5; dùng
  hàm `http_get_last_response_headers()` có từ PHP 8.4.
- ⚠️ Truyền đường dẫn do người dùng gửi vào `file_get_contents()` là lỗ hổng: họ có thể đưa
  `http://169.254.169.254/...` (SSRF, đọc metadata của cloud), `php://filter/...` hay `phar://...`.
  `allow_url_include` (cho `include` file từ URL) mặc định tắt và đã deprecated từ PHP 7.4. Chi tiết
  ở [chương 17](17-bao-mat.md).

## 5. CSV

### 5.1 CSV là gì, và "chuẩn" của nó

*CSV* (comma-separated values) là định dạng bảng dạng text: mỗi dòng là một bản ghi, các ô cách nhau
bởi dấu phẩy. Nó là định dạng trao đổi dữ liệu phổ biến nhất với người dùng không phải dev: xuất báo
cáo cho kế toán, nhập danh sách sản phẩm từ Excel.

CSV chưa bao giờ có chuẩn chính thức; tài liệu gần nhất là RFC 4180 (dạng "informational"). Quy tắc
cốt lõi của RFC 4180:

1. Ô chứa dấu phẩy, dấu nháy kép `"` hoặc xuống dòng thì phải bọc trong nháy kép.
2. Dấu nháy kép bên trong ô được viết thành hai dấu nháy kép `""`.
3. Không có ký tự escape nào khác. Dấu `\` chỉ là một ký tự bình thường.

```
id,ten,ghi_chu
1,An,"Giao trước 9h, gọi trước"        <- ô có dấu phẩy: bọc nháy
2,"Trần ""Bé"" B",                     <- nháy trong ô: nhân đôi; ô cuối rỗng
3,Lê C,"Dòng 1
Dòng 2"                                <- ô có xuống dòng: một bản ghi trải trên hai dòng vật lý
```

⚠️ Hệ quả của quy tắc 1 và ví dụ dòng 3: một bản ghi CSV có thể dài nhiều dòng. Tách file bằng
`explode("\n", ...)` rồi `explode(',', ...)` là sai ngay khi có ô chứa dấu phẩy hoặc xuống dòng. Luôn
dùng hàm CSV có sẵn.

### 5.2 `fputcsv`, `fgetcsv`, `str_getcsv`

| Hàm | Làm gì |
|---|---|
| `fputcsv($stream, $fields, $separator, $enclosure, $escape, $eol)` | Ghi một mảng thành một dòng CSV, tự bọc nháy khi cần. Tham số `$eol` có từ PHP 8.1 |
| `fgetcsv($stream, $length, $separator, $enclosure, $escape)` | Đọc một bản ghi (có thể nhiều dòng vật lý), trả mảng chuỗi; hết file trả `false` |
| `str_getcsv($string, $separator, $enclosure, $escape)` | Tách một chuỗi CSV đã có trong biến |

Ví dụ đầy đủ: ghi một file CSV có tiếng Việt, rồi đọc lại thành mảng có key theo dòng tiêu đề, dùng
generator để file lớn tới đâu cũng chỉ giữ một bản ghi trong RAM ([chương
13](13-generator-iterator-spl.md)):

```php
<?php
declare(strict_types=1);

$path = __DIR__ . '/don-hang.csv';

// ---- Ghi ----
$rows = [
    ['id', 'khach_hang', 'ghi_chu', 'tong_tien'],
    [1, 'Nguyễn Văn A', 'Giao giờ hành chính', '150000'],
    [2, 'Trần "Bé" B', "Gọi trước,\nđể ở bảo vệ", '2500000'],
    [3, 'Lê C', 'C:\\kho\\', '99000'],
];
$fh = fopen($path, 'w');
fwrite($fh, "\xEF\xBB\xBF");                 // BOM UTF-8, để Excel hiển thị đúng tiếng Việt (mục 5.4)
foreach ($rows as $row) {
    fputcsv($fh, $row, ',', '"', '');        // escape '' = đúng RFC 4180 (mục 5.3)
}
fclose($fh);
echo file_get_contents($path);
// in ra (ký tự BOM vô hình ở đầu):
// id,khach_hang,ghi_chu,tong_tien
// 1,"Nguyễn Văn A","Giao giờ hành chính",150000
// 2,"Trần ""Bé"" B","Gọi trước,
// để ở bảo vệ",2500000
// 3,"Lê C",C:\kho\,99000

// ---- Đọc ----
/** @return Generator<int, array<string, string|null>> */
function readCsv(string $path): Generator
{
    $fh = fopen($path, 'r');
    if ($fh === false) {
        throw new RuntimeException("Không mở được $path");
    }
    try {
        $header = fgetcsv($fh, null, ',', '"', '');
        if ($header === false) {
            return;                                     // file rỗng
        }
        $header[0] = preg_replace('/^\xEF\xBB\xBF/', '', (string) $header[0]);   // bỏ BOM
        $record = 1;
        while (($row = fgetcsv($fh, null, ',', '"', '')) !== false) {
            $record++;
            if ($row === [null]) {
                continue;                               // dòng trống được trả về là [null]
            }
            if (count($row) !== count($header)) {
                throw new UnexpectedValueException("Bản ghi $record có " . count($row) . ' cột');
            }
            yield $record => array_combine($header, $row);
        }
    } finally {
        fclose($fh);                                    // chạy cả khi bên ngoài break sớm
    }
}

foreach (readCsv($path) as $record => $order) {
    echo $record, ': ', json_encode($order, JSON_UNESCAPED_UNICODE), PHP_EOL;
}
// in ra: 2: {"id":"1","khach_hang":"Nguyễn Văn A","ghi_chu":"Giao giờ hành chính","tong_tien":"150000"}
//        3: {"id":"2","khach_hang":"Trần \"Bé\" B","ghi_chu":"Gọi trước,\nđể ở bảo vệ","tong_tien":"2500000"}
//        4: {"id":"3","khach_hang":"Lê C","ghi_chu":"C:\\kho\\","tong_tien":"99000"}
unlink($path);
```

Quan sát:

- `fputcsv()` tự bọc nháy những ô có dấu phẩy, nháy, xuống dòng, và cả ô có khoảng trắng; ô `id`
  kiểu int được đổi thành chuỗi.
- `fgetcsv()` luôn trả chuỗi: `"1"`, `"150000"`. Đổi kiểu và kiểm tra dữ liệu là việc của bạn (dữ liệu
  từ file người dùng gửi lên là dữ liệu không tin được).
- Dòng trống trong file được trả về là mảng `[null]`, không phải `false` (theo manual), nên phải tự bỏ
  qua.
- Truyền `$length = null` để không giới hạn độ dài dòng.

### 5.3 Tham số `$escape` và thay đổi của PHP 8.4

Ngoài cách nhân đôi nháy của RFC 4180, PHP từ lâu có thêm một cơ chế escape riêng: ký tự `$escape`
(mặc định `\`). Cơ chế này không có trong chuẩn và làm hỏng dữ liệu ở một số ca. Ca dễ gặp nhất là ô
kết thúc bằng dấu `\`, ví dụ một đường dẫn Windows:

```php
<?php
declare(strict_types=1);

$row = ['C:\\temp\\', 'x'];                       // ô đầu là: C:\temp\

foreach (['\\', ''] as $escape) {
    $h = fopen('php://memory', 'w+');
    fputcsv($h, $row, ',', '"', $escape);
    rewind($h);
    $line = stream_get_contents($h);
    rewind($h);
    $back = fgetcsv($h, null, ',', '"', $escape);
    echo 'escape=', json_encode($escape), ' ghi ra: ', json_encode($line),
        ' đọc lại: ', json_encode($back), PHP_EOL;
}
// in ra: escape="\\" ghi ra: "\"C:\\temp\\\",x\n" đọc lại: ["C:\\temp\\\",x\n"]
//        escape="" ghi ra: "C:\\temp\\,x\n" đọc lại: ["C:\\temp\\","x"]
// Dòng 1 hỏng: đọc lại chỉ được 1 ô thay vì 2. Dòng 2 đúng.
```

(Output là JSON nên mỗi `\` hiện thành `\\`.) Với escape mặc định, dòng ghi ra là `"C:\temp\",x`.
Khi đọc lại, `\"` bị hiểu là "nháy đã được escape" chứ không phải nháy đóng ô, nên cả phần còn lại của
dòng dính vào ô đầu: dữ liệu không đi trọn vòng ghi rồi đọc. Một file CSV chuẩn do Excel hay Google
Sheets xuất ra có ô kết thúc bằng `\` cũng bị đọc sai y như vậy.

Lộ trình của PHP:

| Phiên bản | Thay đổi |
|---|---|
| 7.4 | Cho phép truyền `$escape = ""` (chuỗi rỗng) để tắt hẳn cơ chế escape riêng |
| 8.4 | Gọi `fputcsv()`, `fgetcsv()`, `str_getcsv()`, `SplFileObject::setCsvControl()`, `SplFileObject::fputcsv()`, `SplFileObject::fgetcsv()` mà không truyền `$escape` sẽ phát `E_DEPRECATED` |
| Tương lai (không sớm hơn 9.0, theo manual) | Giá trị mặc định của `$escape` sẽ đổi |

Thông báo bạn sẽ thấy trên PHP 8.4 và 8.5:

```
Deprecated: str_getcsv(): the $escape parameter must be provided as its default value will change in ...
```

Quy tắc thực hành: luôn truyền `$escape` một cách tường minh, và truyền `''` trừ khi bạn chắc chắn
đang đọc file do một hệ thống dùng đúng kiểu escape `\` sinh ra. Viết bằng named argument cho gọn:
`fgetcsv($fh, escape: '')`. Truyền tường minh `'\\'` cũng hết cảnh báo, nhưng giữ nguyên hành vi lỗi
ở trên.

### 5.4 BOM, dấu phân cách và Excel

- *BOM* (byte order mark) là 3 byte `EF BB BF` đặt ở đầu file để báo "file này là UTF-8". Excel trên
  Windows thường cần BOM mới hiển thị đúng tiếng Việt khi mở file CSV bằng double-click; thiếu BOM thì
  ra chữ lỗi kiểu `Nguyá»…n`. Ngược lại, khi đọc file có BOM, ô đầu tiên của dòng tiêu đề dính 3 byte
  đó (`"\xEF\xBB\xBFid"` khác `"id"`), nên phải bỏ đi như ví dụ ở mục 5.2.
- Excel trên Windows lưu CSV theo "list separator" trong thiết lập vùng (Region) của máy. Ở các máy
  đặt dấu phẩy làm dấu thập phân (nhiều nước châu Âu), list separator thường là `;`, nên file CSV
  xuất ra dùng dấu phân cách `;`. Nhận file từ người dùng thì nên cho chọn dấu phân cách hoặc tự phát hiện từ dòng đầu.
- File từ Windows có thể kết thúc dòng bằng `\r\n`. `fgetcsv()` xử lý được, còn `fgets()` sẽ để lại
  `\r` ở cuối dòng.
- ⚠️ *CSV injection*: ô bắt đầu bằng `=`, `+`, `-`, `@` có thể bị Excel hiểu là công thức khi người
  dùng mở file bạn xuất ra. Dữ liệu người dùng nhập mà đi vào file CSV xuất ra cần được xử lý; chi tiết
  ở [chương 17](17-bao-mat.md).

## 6. `SplFileObject`

### 6.1 File dưới dạng object

`SplFileObject` (thuộc SPL, [chương 13](13-generator-iterator-spl.md)) gói một file handle thành
object, và quan trọng nhất là nó là một *iterator*: `foreach` trên nó cho từng dòng, key là số thứ tự
dòng (bắt đầu từ 0). Nó có gần như mọi hàm file dưới dạng method: `fgets()`, `fwrite()`, `fgetcsv()`,
`fputcsv()`, `flock()`, `ftruncate()`, `seek()`...

So với hàm thủ tục:

- Mở thất bại thì constructor ném `RuntimeException` (đường dẫn là thư mục thì `LogicException`),
  thay vì trả `false` kèm warning.
- File tự đóng khi object bị huỷ; không có method `fclose()`.
- Dùng được ở mọi nơi nhận `iterable` hoặc `Iterator`.

```php
<?php
declare(strict_types=1);

$path = __DIR__ . '/sp.csv';
file_put_contents($path, "id,ten\n1,An\n\n2,Bình\n");   // có một dòng trống ở giữa

$file = new SplFileObject($path, 'r');
$file->setFlags(SplFileObject::READ_CSV);
$file->setCsvControl(',', '"', '');                 // nhớ truyền escape (mục 5.3)
foreach ($file as $i => $row) {
    echo $i, ' ', json_encode($row, JSON_UNESCAPED_UNICODE), PHP_EOL;
}
// in ra: 0 ["id","ten"]
//        1 ["1","An"]
//        2 [null]          <- dòng trống
//        3 ["2","Bình"]
//        4 [null]          <- "dòng" sau ký tự \n cuối cùng

$file->setFlags(
    SplFileObject::READ_CSV | SplFileObject::READ_AHEAD
    | SplFileObject::SKIP_EMPTY | SplFileObject::DROP_NEW_LINE
);
foreach ($file as $i => $row) {
    echo $i, ' ', json_encode($row, JSON_UNESCAPED_UNICODE), PHP_EOL;
}
// in ra: 0 ["id","ten"]
//        1 ["1","An"]
//        3 ["2","Bình"]    <- key vẫn là số dòng thật trong file

unlink($path);
```

Các flag (ghép bằng `|` trong `setFlags()`):

| Flag | Tác dụng |
|---|---|
| `DROP_NEW_LINE` | Bỏ ký tự xuống dòng ở cuối mỗi dòng |
| `READ_AHEAD` | Đọc trước dòng kế tiếp khi `rewind`/`next` |
| `SKIP_EMPTY` | Bỏ dòng trống; manual ghi cần bật kèm `READ_AHEAD` mới chạy đúng |
| `READ_CSV` | Mỗi dòng được tách thành mảng như `fgetcsv()` |

Tổ hợp `READ_CSV | READ_AHEAD | SKIP_EMPTY | DROP_NEW_LINE` là cấu hình hay dùng nhất khi đọc CSV.

⚠️ Khi lặp với `READ_CSV`, PHP dùng cấu hình CSV lưu trong object. Nếu chưa gọi `setCsvControl()`, nó
dùng escape mặc định `\` mà không phát cảnh báo deprecated nào (đã chạy thử trên 8.4 và 8.5), tức là
dính lỗi ở mục 5.3 một cách im lặng. Luôn gọi `setCsvControl(',', '"', '')`.

### 6.2 Nhảy tới dòng, file tạm, thông tin file

```php
<?php
declare(strict_types=1);

$path = __DIR__ . '/lines.txt';
file_put_contents($path, "a\nb\nc\nd\n");

$file = new SplFileObject($path);
$file->seek(2);                       // nhảy tới dòng số 2 (đếm từ 0)
var_dump($file->current());           // in ra: string(2) "c
                                      // "
$file->seek(PHP_INT_MAX);             // nhảy quá cuối file: dừng ở dòng cuối cùng
var_dump($file->key());               // in ra: int(4)

// SplTempFileObject: một SplFileObject trên php://temp
$tmp = new SplTempFileObject();
$tmp->fputcsv(['a', 'b c'], ',', '"', '');
$tmp->rewind();
var_dump($tmp->fgets());              // in ra: string(8) "a,"b c"
                                      // "

// SplFileInfo: thông tin về một đường dẫn, không mở file
$info = new SplFileInfo($path);
var_dump($info->getExtension(), $info->getSize(), $info->isFile());
// in ra: string(3) "txt"  int(8)  bool(true)
unlink($path);
```

`seek(PHP_INT_MAX)` hay được dùng để đếm dòng, nhưng cần hiểu đúng con số: `key()` là chỉ số của dòng
cuối cùng. File `"a\nb\nc\nd\n"` kết thúc bằng `\n` nên dòng cuối là "dòng" rỗng sau `\n` đó, chỉ số 4,
trùng với số dòng có nội dung. File `"a\nb\nc\nd"` (không có `\n` cuối) cho `key()` bằng 3 dù vẫn có 4
dòng. Ngoài ra `seek()` phải đọc lần lượt từ đầu file tới dòng cần tới (file text không có mục lục
dòng), nên tốn thời gian tỉ lệ với kích thước file, chỉ là không tốn RAM.

## 7. JSON

### 7.1 JSON là gì và ánh xạ sang kiểu PHP

*JSON* (JavaScript Object Notation) là định dạng text để biểu diễn dữ liệu có cấu trúc. Nó là ngôn ngữ
chung của web API: frontend gửi JSON lên, backend trả JSON về, các service nói chuyện với nhau bằng
JSON, MySQL có kiểu cột `JSON`. Đặc tả hiện hành là RFC 8259. JSON chỉ có 6 loại giá trị: object,
array, string, number, `true`/`false`, `null`.

Extension `json` luôn có sẵn trong PHP (từ PHP 8.0 không tắt được nữa). Hai hàm chính:
`json_encode()` (PHP → chuỗi JSON) và `json_decode()` (chuỗi JSON → PHP).

| JSON | PHP khi decode | PHP nào thì encode ra loại này |
|---|---|---|
| `{"a": 1}` (object) | `stdClass`, hoặc mảng có key nếu decode với `true` | Mảng có key không phải dãy 0, 1, 2...; object |
| `[1, 2]` (array) | Mảng list | Mảng là list (key 0, 1, 2... liên tục) |
| `"text"` | `string` | `string` (phải là UTF-8 hợp lệ) |
| `10` | `int` | `int` |
| `1.5`, `1e2`, `1.0` | `float` | `float` |
| `true`, `false` | `bool` | `bool` |
| `null` | `null` | `null` |

### 7.2 `json_encode()`: từ PHP sang JSON

```php
<?php
declare(strict_types=1);

final class User
{
    public function __construct(
        public int $id,
        public string $name,
        protected string $password,      // không public: không xuất hiện trong JSON
    ) {}
}

enum Status: string
{
    case Active = 'active';
    case Banned = 'banned';
}

$data = [
    'id'     => 42,
    'price'  => 10.0,
    'name'   => 'Nguyễn Văn A',
    'url'    => 'https://example.com/a',
    'tags'   => ['php', 'json'],
    'empty'  => [],
    'map'    => ['a' => 1],
    'status' => Status::Active,
    'user'   => new User(1, 'An', 'secret'),
];
echo json_encode($data), PHP_EOL;
// in ra: {"id":42,"price":10,"name":"Nguy\u1ec5n V\u0103n A","url":"https:\/\/example.com\/a",
//         "tags":["php","json"],"empty":[],"map":{"a":1},"status":"active","user":{"id":1,"name":"An"}}
//         (output thật nằm trên một dòng)
```

Quan sát từng phần:

- `10.0` thành `10`: JSON không phân biệt int với float, PHP bỏ phần `.0` (flag
  `JSON_PRESERVE_ZERO_FRACTION` giữ lại).
- Chữ có dấu thành dạng `\uXXXX` (`ễ` thành `\u1ec5`), dấu `/` thành `\/`. Đều là JSON hợp lệ, đọc lại vẫn đúng, nhưng khó đọc;
  dùng `JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES` để giữ nguyên (mục 7.3).
- Object mặc định chỉ xuất các property `public`. `password` là `protected` nên không lộ ra.
- Enum có kiểu (backed enum, chương 10) được encode thành giá trị của nó. Enum thuần (pure enum) thì
  không encode được: lỗi "Non-backed enums have no default serialization".

⚠️ Mảng nào thành JSON array, mảng nào thành JSON object? Chỉ mảng là *list* (key đúng là 0, 1, 2...
liên tục, chương 06) mới thành `[...]`, còn lại thành `{...}`:

```php
var_dump(json_encode([0 => 'a', 1 => 'b']));        // in ra: string(9) "["a","b"]"
var_dump(json_encode([1 => 'a', 2 => 'b']));        // in ra: string(17) "{"1":"a","2":"b"}"
var_dump(json_encode(array_filter([1, 0, 2])));     // in ra: string(13) "{"0":1,"2":2}"
var_dump(json_encode(array_values(array_filter([1, 0, 2]))));   // in ra: string(5) "[1,2]"
```

`array_filter()`, `unset()` làm mảng có "lỗ hổng" ở key, và client đang chờ một array bỗng nhận một
object. Gọi `array_values()` trước khi trả về. Laravel Collection cũng vậy: sau `->filter()` cần
`->values()`.

⚠️ Mảng rỗng luôn thành `[]`. Nếu API hứa trả object (ví dụ `"settings": {}`), mảng rỗng phá vỡ hứa
hẹn đó. Dùng `new stdClass()` hoặc `(object) []` cho object rỗng; flag `JSON_FORCE_OBJECT` thì biến
mọi mảng (kể cả list) thành object nên hiếm khi là thứ bạn muốn.

```php
var_dump(json_encode([]));                 // in ra: string(2) "[]"
var_dump(json_encode(new stdClass()));     // in ra: string(2) "{}"
```

#### `JsonSerializable`: tự quyết định hình dạng JSON

Class implement interface `JsonSerializable` thì `json_encode()` gọi method `jsonSerialize()` và encode
giá trị method đó trả về, thay vì lấy các property public:

```php
<?php
declare(strict_types=1);

final class Money implements JsonSerializable
{
    public function __construct(
        private readonly int $amount,          // đơn vị nhỏ nhất của tiền tệ (mục 9)
        private readonly string $currency,
    ) {}

    public function jsonSerialize(): array
    {
        return ['amount' => (string) $this->amount, 'currency' => $this->currency];
    }
}

echo json_encode(['total' => new Money(150000, 'VND')]), PHP_EOL;
// in ra: {"total":{"amount":"150000","currency":"VND"}}
```

⚠️ `DateTime` và `DateTimeImmutable` không implement `JsonSerializable`; encode chúng ra một cấu trúc
nội bộ mà client không nên phải hiểu:

```php
echo json_encode(new DateTimeImmutable('2026-10-03 08:30:00', new DateTimeZone('Asia/Ho_Chi_Minh')));
// in ra: {"date":"2026-10-03 08:30:00.000000","timezone_type":3,"timezone":"Asia\/Ho_Chi_Minh"}
```

Hãy tự format ngày thành chuỗi ISO 8601 trước khi encode (mục 8.4). Laravel làm việc này cho bạn khi
serialize model.

### 7.3 Các flag của `json_encode()`

Flag ghép bằng `|` ở tham số thứ hai:

| Flag | Tác dụng | Dùng khi |
|---|---|---|
| `JSON_THROW_ON_ERROR` | Lỗi thì ném `JsonException` (PHP 7.3+) | Luôn luôn (mục 7.5) |
| `JSON_UNESCAPED_UNICODE` | Giữ nguyên ký tự UTF-8 thay vì `\uXXXX` | Log, file, API: dễ đọc, ngắn hơn |
| `JSON_UNESCAPED_SLASHES` | Không đổi `/` thành `\/` | Hầu hết trường hợp, trừ khi nhúng JSON vào thẻ `<script>` trong HTML |
| `JSON_PRETTY_PRINT` | Xuống dòng, thụt lề 4 dấu cách | File cấu hình, debug |
| `JSON_PRESERVE_ZERO_FRACTION` | `10.0` ra `10.0` thay vì `10` | Bên nhận phân biệt int/float |
| `JSON_FORCE_OBJECT` | Mọi mảng thành object | Hiếm |
| `JSON_HEX_TAG`, `JSON_HEX_AMP`, `JSON_HEX_APOS`, `JSON_HEX_QUOT` | Đổi `< >`, `&`, `'`, `"` thành `\u003C \u003E`, `\u0026`, `\u0027`, `\u0022` | Nhúng JSON vào HTML |
| `JSON_INVALID_UTF8_SUBSTITUTE` / `_IGNORE` | Byte UTF-8 hỏng được thay bằng `U+FFFD` / bị bỏ đi | Dữ liệu bẩn mà vẫn phải xuất (mục 7.7) |
| `JSON_PARTIAL_OUTPUT_ON_ERROR` | Giá trị không encode được thay bằng `null`/`0` thay vì thất bại | Gần như không nên dùng: che lỗi |
| `JSON_NUMERIC_CHECK` | Chuỗi trông như số thành số | ⚠️ Không nên dùng, xem dưới |

```php
<?php
declare(strict_types=1);

echo json_encode(['a' => [1, 2], 'b' => []], JSON_PRETTY_PRINT), PHP_EOL;
// in ra:
// {
//     "a": [
//         1,
//         2
//     ],
//     "b": []
// }

$flags = JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES;
echo json_encode(['name' => 'Nguyễn Văn A', 'url' => 'https://example.com/a'], $flags), PHP_EOL;
// in ra: {"name":"Nguyễn Văn A","url":"https://example.com/a"}

// ⚠️ JSON_NUMERIC_CHECK làm hỏng dữ liệu là chuỗi số
var_dump(json_encode(['phone' => '0912345678', 'code' => '1e3'], JSON_NUMERIC_CHECK));
// in ra: string(31) "{"phone":912345678,"code":1000}"    <- mất số 0 đầu, "1e3" thành 1000
```

Số điện thoại, mã bưu chính, mã sản phẩm là chuỗi chứ không phải số. Muốn trả số thì ép kiểu đúng
chỗ (`(int) $row['qty']`) thay vì nhờ một flag đoán hộ.

### 7.4 `json_decode()`: từ JSON sang PHP

```php
<?php
declare(strict_types=1);

$json = '{"id": 7, "tags": ["a", "b"], "address": {"city": "Hà Nội"}, "score": 9.5, "deleted": null}';

$obj = json_decode($json);                      // mặc định: object JSON -> stdClass
var_dump($obj->address->city);                  // in ra: string(9) "Hà Nội"
var_dump($obj->tags[1]);                        // in ra: string(1) "b"  (array JSON vẫn là mảng PHP)

$arr = json_decode($json, true);                // true: object JSON -> mảng có key
var_dump($arr['address']['city']);              // in ra: string(9) "Hà Nội"

// Giá trị gốc không nhất thiết là object hay array
var_dump(json_decode('"hello"'), json_decode('123'), json_decode('true'));
// in ra: string(5) "hello"  int(123)  bool(true)
```

Chữ ký: `json_decode(string $json, ?bool $associative = null, int $depth = 512, int $flags = 0)`.

- `$associative = true` cho mảng, `false` hoặc `null` (mặc định) cho `stdClass`; `null` kèm flag
  `JSON_OBJECT_AS_ARRAY` thì cũng ra mảng. Trong ứng dụng, mảng hay dùng hơn vì làm việc được với mọi
  hàm mảng; `stdClass` có ích khi cần phân biệt object rỗng với array rỗng (dưới đây).
- `$depth`: độ lồng tối đa; JSON lồng sâu hơn thì thất bại với lỗi "Maximum stack depth exceeded".
  Cách PHP đếm: số cấp array/object lồng nhau phải nhỏ hơn `$depth` (chạy thử: `[]` cần 2, `[[1]]` và
  cả `[[]]` cần ít nhất 3). Mặc định 512 là đủ cho dữ liệu bình thường; giảm xuống khi nhận JSON từ
  ngoài để chặn payload lồng sâu bất thường.

Những điều bất ngờ khi decode thành mảng:

```php
var_dump(json_decode('{"10": "a", "x": 1}', true));
// in ra: array(2) { [10]=> string(1) "a"  ["x"]=> int(1) }   <- key "10" thành int 10 (chương 06)

var_dump(json_decode('{"a": 1, "a": 2}', true));
// in ra: array(1) { ["a"]=> int(2) }                          <- key trùng: giá trị sau thắng

// ⚠️ Đi một vòng decode(true) rồi encode làm object rỗng thành array rỗng
$in = '{"settings": {}, "items": []}';
echo json_encode(json_decode($in, true)), PHP_EOL;   // in ra: {"settings":[],"items":[]}
echo json_encode(json_decode($in)), PHP_EOL;         // in ra: {"settings":{},"items":[]}
```

Khi decode thành mảng, cả `{}` và `[]` đều thành `[]` của PHP, thông tin "đây là object" bị mất. Service
trung gian nhận JSON, sửa vài trường rồi gửi tiếp có thể vô tình đổi `{}` thành `[]` và làm hỏng bên
nhận. Nếu cần giữ nguyên hình dạng, decode thành `stdClass`.

Key có ký tự đặc biệt thì truy cập bằng cú pháp `{}`: `$obj->{'first-name'}`.

### 7.5 Bắt lỗi: `null` mơ hồ và `JSON_THROW_ON_ERROR`

Mặc định, khi JSON hỏng, `json_decode()` trả `null` và `json_encode()` trả `false`, không có warning hay
exception nào. Với `json_decode()` điều này đặc biệt nguy hiểm vì `null` cũng là kết quả hợp lệ của
chuỗi JSON `"null"`:

```php
var_dump(json_decode('null'));       // in ra: NULL   <- JSON hợp lệ, giá trị là null
var_dump(json_decode('{bad'));       // in ra: NULL   <- JSON hỏng
var_dump(json_decode(''));           // in ra: NULL   <- chuỗi rỗng cũng là JSON hỏng
```

Cách cũ là hỏi lỗi sau mỗi lần gọi bằng `json_last_error()` (trả hằng `JSON_ERROR_*`, `0` là
`JSON_ERROR_NONE`) và `json_last_error_msg()`. Rất dễ quên. Từ PHP 7.3, truyền `JSON_THROW_ON_ERROR`
để hàm ném `JsonException` (mã lỗi nằm trong `getCode()`):

```php
<?php
declare(strict_types=1);

try {
    $data = json_decode('{"a":1,', true, 512, JSON_THROW_ON_ERROR);
} catch (JsonException $e) {
    echo get_class($e), ': ', $e->getMessage(), ' code=', $e->getCode(), PHP_EOL;
    // in ra: JsonException: Syntax error code=4
}

// Named argument cho gọn, không phải viết lại 512
$data = json_decode('{"a":1}', true, flags: JSON_THROW_ON_ERROR);

try {
    json_encode(NAN, JSON_THROW_ON_ERROR);
} catch (JsonException $e) {
    echo $e->getMessage(), PHP_EOL;     // in ra: Inf and NaN cannot be JSON encoded
}
```

Những lỗi hay gặp khi decode, đều ra "Syntax error": JSON dùng nháy đơn (`{'a': 1}`), dấu phẩy thừa ở
cuối (`[1, 2,]`), chuỗi rỗng, comment. PHP theo đúng đặc tả, không "dễ dãi" như JavaScript.

⚠️ Với `JSON_THROW_ON_ERROR`, hàm không cập nhật trạng thái lỗi toàn cục (manual: ném exception "thay
vì" đặt trạng thái lỗi). Vì thế đừng trộn hai kiểu:

```php
json_decode('{bad');                                 // kiểu cũ: đặt lỗi toàn cục = Syntax error
json_decode('1', flags: JSON_THROW_ON_ERROR);        // thành công, nhưng không xoá lỗi cũ
var_dump(json_last_error_msg());                     // in ra: string(12) "Syntax error"  <- lỗi của lần trước!
```

Quy tắc: mọi lần gọi `json_encode()`/`json_decode()` đều có `JSON_THROW_ON_ERROR`, và không gọi
`json_last_error()` nữa.

### 7.6 Số lớn và số thực

Số trong JSON không có giới hạn độ lớn theo đặc tả, nhưng mỗi ngôn ngữ đọc nó vào một kiểu có giới
hạn:

```php
<?php
declare(strict_types=1);

var_dump(json_decode('{"id": 9223372036854775807}', true));    // vừa PHP_INT_MAX (64-bit)
// in ra: array(1) { ["id"]=> int(9223372036854775807) }

var_dump(json_decode('{"id": 9223372036854775808}', true));    // lớn hơn PHP_INT_MAX một đơn vị
// in ra: array(1) { ["id"]=> float(9.223372036854776E+18) }   <- thành float, mất chính xác

var_dump(json_decode('{"id": 12345678901234567890}', true, 512, JSON_BIGINT_AS_STRING));
// in ra: array(1) { ["id"]=> string(20) "12345678901234567890" }   <- giữ nguyên dạng chuỗi

var_dump(json_encode(0.1 + 0.2));    // in ra: string(19) "0.30000000000000004"
```

- Số nguyên vượt `PHP_INT_MAX` bị đọc thành float và mất các chữ số cuối, trừ khi dùng
  `JSON_BIGINT_AS_STRING`.
- Float được encode theo ini `serialize_precision` (mặc định `-1`: dùng số chữ số ngắn nhất mà đọc lại
  vẫn ra đúng giá trị float đó). `0.1 + 0.2` vốn không bằng `0.3` trong float (mục 9.1), JSON chỉ trung
  thực in ra điều đó.
- ⚠️ Phía JavaScript còn chặt hơn: `JSON.parse` đọc mọi số thành *double* (số thực 64-bit), nên số
  nguyên chỉ chính xác tới `2^53 - 1 = 9007199254740991` (`Number.MAX_SAFE_INTEGER`). ID 64-bit kiểu
  Snowflake, hoặc `BIGINT UNSIGNED` lớn, gửi xuống trình duyệt dạng số sẽ bị làm tròn âm thầm thành ID
  khác.

Quy tắc cho API:

- ID có thể vượt `2^53` thì trả dạng chuỗi: `"id": "1234567890123456789"`.
- Tiền trả dạng chuỗi thập phân (`"amount": "150000.50"`) hoặc số nguyên theo đơn vị nhỏ nhất kèm mã
  tiền tệ, không trả float (mục 9).

### 7.7 JSON và UTF-8

Đặc tả JSON yêu cầu text trao đổi giữa các hệ thống phải là UTF-8, và PHP bắt buộc mọi chuỗi đưa vào
`json_encode()` phải là UTF-8 hợp lệ. Chỉ một byte sai (thường đến từ dữ liệu cũ lưu bằng
Windows-1258/latin1, hoặc từ `substr()` cắt đôi một ký tự nhiều byte, chương 05) là cả lần encode thất
bại:

```php
<?php
declare(strict_types=1);

$broken = "abc\xB1";                                   // \xB1 không phải UTF-8 hợp lệ
var_dump(json_encode($broken));                        // in ra: bool(false)
echo json_last_error_msg(), PHP_EOL;                   // in ra: Malformed UTF-8 characters, possibly incorrectly encoded

var_dump(json_encode($broken, JSON_INVALID_UTF8_SUBSTITUTE));   // in ra: string(11) ""abc\ufffd""  (U+FFFD, viết dạng \uXXXX)
var_dump(json_encode($broken, JSON_INVALID_UTF8_IGNORE));       // in ra: string(5) ""abc""
var_dump(mb_check_encoding($broken, 'UTF-8'));                  // in ra: bool(false)
```

⚠️ Bug kinh điển: một API trả `false` (hoặc body rỗng) cho đúng một bản ghi có dữ liệu bẩn, trong khi
mọi bản ghi khác bình thường, vì code không kiểm tra kết quả `json_encode()`. Có
`JSON_THROW_ON_ERROR` thì lỗi lộ ra ngay. Sửa tận gốc là làm sạch dữ liệu đầu vào (kiểm tra bằng
`mb_check_encoding()`, chuyển mã bằng `mb_convert_encoding()`) và để database dùng `utf8mb4`.

### 7.8 `json_validate()` (PHP 8.3)

`json_validate(string $json, int $depth = 512, int $flags = 0): bool` kiểm tra một chuỗi có phải JSON
hợp lệ hay không mà không dựng mảng/object kết quả, nên tốn ít bộ nhớ hơn `json_decode()`.

```php
<?php
declare(strict_types=1);

var_dump(json_validate('{"test": {"foo": "bar"}}'));   // in ra: bool(true)
var_dump(json_validate('{"a": 1,}'));                  // in ra: bool(false)
echo json_last_error_msg(), PHP_EOL;                   // in ra: Syntax error
```

⚠️ Đừng viết `if (json_validate($s)) { $data = json_decode($s, ...); }`: chuỗi bị parse hai lần, vì
`json_decode()` vốn đã kiểm tra trong lúc decode (manual cảnh báo đúng điều này). Chỉ dùng
`json_validate()` khi bạn cần biết "có hợp lệ không" mà không dùng dữ liệu, ví dụ validate một trường
trước khi lưu nguyên chuỗi vào cột `JSON` của MySQL. Laravel có rule validation `json` cho việc đó.

### 7.9 Đối chiếu với Go và Java

| | PHP | Go (`encoding/json`) | Java (Jackson) |
|---|---|---|---|
| Decode vào | Mảng/`stdClass` động, không cần khai báo | Struct có tag `json:"name"`, hoặc `map[string]any` | Class/record, hoặc `JsonNode` |
| Field không public | Bỏ qua | Field viết thường (unexported) bị bỏ qua | Tuỳ cấu hình visibility |
| Báo lỗi | `JSON_THROW_ON_ERROR` → `JsonException` | Trả `error` | Ném exception (`JsonProcessingException` ở Jackson 2.x) |
| Số lớn | Vượt `PHP_INT_MAX` thành float (trừ `JSON_BIGINT_AS_STRING`) | Vào `any` thì thành `float64` (trừ `UseNumber()`) | Tuỳ kiểu đích (`long`, `BigInteger`...) |

Điểm chung: số vào kiểu "động" thường thành float. Cùng một bài học ở mọi ngôn ngữ: ID và tiền đi qua
JSON nên là chuỗi.

## 8. Ngày giờ

Ngày giờ là nguồn bug âm thầm bậc nhất của backend: đơn hàng bị tính vào ngày hôm trước, email nhắc
lịch gửi lệch 7 tiếng, gói thuê bao gia hạn nhảy cóc một tháng. Phần lớn đến từ việc lẫn lộn vài khái
niệm cơ bản. Mục này đi từ các khái niệm đó tới API của PHP.

### 8.1 Các khái niệm: thời điểm, UTC, timezone, offset

- *Thời điểm* (instant): một điểm duy nhất trên dòng thời gian, như "lúc khách bấm nút đặt hàng". Nó
  giống nhau với mọi người trên Trái Đất, chỉ có cách đọc giờ là khác.
- *UTC* (Coordinated Universal Time): giờ chuẩn quốc tế, dùng làm mốc chung. Không có giờ mùa hè.
- *Offset*: độ lệch của giờ địa phương so với UTC tại một thời điểm, ví dụ `+07:00`.
- *Timezone* (múi giờ) theo nghĩa của lập trình: một vùng địa lý có chung quy tắc giờ, đặt tên theo
  cơ sở dữ liệu *IANA tz* (còn gọi tzdata), ví dụ `Asia/Ho_Chi_Minh`, `America/New_York`. Một timezone
  biết offset của nó ở mọi thời điểm trong quá khứ và (theo luật hiện hành) tương lai, kể cả khi offset
  đó thay đổi theo mùa.
- *DST* (daylight saving time, giờ mùa hè): một số nước vặn đồng hồ nhanh 1 giờ vào mùa hè rồi vặn lùi
  vào mùa đông. New York là `-05:00` vào mùa đông và `-04:00` vào mùa hè. Việt Nam luôn là `+07:00`,
  không có DST, nên dev Việt hay không gặp lỗi DST cho tới khi có khách nước ngoài.
- *Unix timestamp*: số giây đã trôi qua kể từ `1970-01-01 00:00:00 UTC` (gọi là *Unix epoch*). Nó là
  một con số đại diện cho một thời điểm, không gắn với timezone nào.

```
                         một thời điểm duy nhất
                                  │
   Unix timestamp:          1790991000
   UTC:                     2026-10-03 01:30:00
   Asia/Ho_Chi_Minh (+07):  2026-10-03 08:30:00
   Asia/Tokyo (+09):        2026-10-03 10:30:00
   America/Los_Angeles:     2026-10-02 18:30:00   (mùa hè nên -07:00; sang ngày hôm trước!)
```

Hệ quả quan trọng: chuỗi `2026-10-03 08:30:00` đứng một mình không phải là một thời điểm. Nó chỉ thành
thời điểm khi biết đi kèm timezone nào. Mọi bug "lệch 7 tiếng" đều bắt đầu từ một chuỗi như vậy bị
hiểu theo timezone khác với lúc nó được tạo ra.

### 8.2 Các hàm thủ tục: `time()`, `date()`, `strtotime()`

PHP có một bộ hàm cũ làm việc trực tiếp với Unix timestamp (kiểu `int`):

```php
<?php
declare(strict_types=1);

$ts = 1790991000;                                   // một thời điểm cụ thể

date_default_timezone_set('UTC');
echo date('Y-m-d H:i:s', $ts), PHP_EOL;              // in ra: 2026-10-03 01:30:00
date_default_timezone_set('Asia/Ho_Chi_Minh');
echo date('Y-m-d H:i:s', $ts), PHP_EOL;              // in ra: 2026-10-03 08:30:00
echo gmdate('Y-m-d H:i:s', $ts), PHP_EOL;            // in ra: 2026-10-03 01:30:00 (gmdate luôn dùng UTC)

// Chiều ngược lại: giờ địa phương -> timestamp, theo timezone mặc định (đang là Asia/Ho_Chi_Minh)
var_dump(mktime(8, 30, 0, 10, 3, 2026));             // in ra: int(1790991000)  (giờ, phút, giây, tháng, ngày, năm)
var_dump(strtotime('2026-10-03 08:30:00'));          // in ra: int(1790991000)
var_dump(strtotime('2026-10-03T01:30:00Z'));         // in ra: int(1790991000)  (chuỗi có "Z" = UTC)
var_dump(strtotime('khong phai ngay'));              // in ra: bool(false)
```

| Hàm | Làm gì |
|---|---|
| `time()` | Unix timestamp hiện tại (giây, `int`) |
| `date($format, $ts)` | Định dạng timestamp theo timezone mặc định; bỏ `$ts` thì lấy giờ hiện tại |
| `gmdate($format, $ts)` | Như `date()` nhưng luôn theo UTC |
| `mktime(...)`, `strtotime($s)` | Giờ địa phương (theo timezone mặc định) → timestamp. `strtotime()` trả `false` nếu không hiểu chuỗi |
| `microtime(true)` | Giờ hiện tại dạng `float`, có phần lẻ micro giây |
| `hrtime(true)` | Đồng hồ đơn điệu, nano giây (`int` trên máy 64-bit) |

Hai điều cần nhớ:

- Kết quả của `date()`, `mktime()`, `strtotime()` phụ thuộc timezone mặc định của tiến trình (mục
  8.3). Cùng một dòng code chạy trên hai server cấu hình khác nhau cho hai kết quả khác nhau.
- *Năm 2038*: số nguyên có dấu 32-bit chỉ chứa được timestamp tới `2038-01-19 03:14:07 UTC`. PHP trên
  máy 64-bit (`PHP_INT_SIZE === 8`, gần như mọi server hiện nay) không bị giới hạn này, nhưng các hệ
  thống khác thì có thể, ví dụ kiểu cột `TIMESTAMP` của MySQL ([chương 16](16-php-va-database.md)).

Đo thời gian chạy một đoạn code thì dùng `hrtime()`, không dùng `microtime()` hay `time()`:

```php
<?php
declare(strict_types=1);

$start = hrtime(true);                    // nano giây, tính từ một mốc bất kỳ, chỉ tăng
usleep(20_000);                           // giả lập công việc mất 20 ms
$elapsedMs = (hrtime(true) - $start) / 1_000_000;
printf("Mất %.1f ms\n", $elapsedMs);      // in ra: Mất 21.2 ms (con số thay đổi mỗi lần chạy)
```

`microtime()` và `time()` đọc *wall clock* (đồng hồ hệ thống), thứ mà NTP có thể chỉnh nhảy tới hoặc
lùi bất kỳ lúc nào, nên hiệu hai lần đọc có thể ra số âm hoặc sai. `hrtime()` đọc *monotonic clock*:
manual mô tả giá trị của nó "đơn điệu và không thể bị chỉnh". Đổi lại, giá trị của `hrtime()` không có
ý nghĩa như một ngày giờ, chỉ dùng để lấy hiệu.

### 8.3 Timezone mặc định của tiến trình

Mọi hàm ngày giờ cần biết "giờ địa phương" đều dùng *timezone mặc định*. Theo manual,
`date_default_timezone_get()` xác định nó theo thứ tự:

1. Giá trị đã đặt bằng `date_default_timezone_set()` trong code (nếu có).
2. Ini `date.timezone` trong `php.ini` (giá trị mặc định là `"UTC"`).
3. Không có gì cả thì dùng `UTC`.

Laravel gọi `date_default_timezone_set(config('app.timezone'))` khi khởi động
(`Illuminate\Foundation\Bootstrap\LoadConfiguration`), và `config/app.php` của Laravel 13 để
`'timezone' => 'UTC'`. Tài liệu Laravel khuyến nghị mạnh không đổi giá trị này.

⚠️ Vì sao nên giữ timezone mặc định là UTC, kể cả khi mọi khách hàng ở Việt Nam:

- Dữ liệu ghi xuống database, log, queue đều cùng một quy ước, không phụ thuộc server.
- Lệnh CLI, cron, queue worker có thể chạy với `php.ini` khác web (ví dụ CLI dùng
  `/etc/php/8.5/cli/php.ini`, FPM dùng `/etc/php/8.5/fpm/php.ini` trên Debian/Ubuntu). Đặt timezone ở
  `php.ini` cho một bên mà quên bên kia là có ngay hai tiến trình ghi giờ lệch nhau 7 tiếng vào cùng
  một bảng.
- Khi có khách ở timezone khác, bạn chỉ cần đổi lúc hiển thị (mục 8.7), không phải sửa dữ liệu.

### 8.4 `DateTime` và `DateTimeImmutable`

Bộ hàm thủ tục ở mục 8.2 dễ dùng nhưng nghèo nàn: timestamp không mang theo timezone, cộng trừ tháng
phải tự tính. PHP có bộ class hướng đối tượng đầy đủ hơn:

| Class | Vai trò |
|---|---|
| `DateTimeImmutable` | Một thời điểm + timezone. Không đổi được: mọi method "sửa" trả object mới |
| `DateTime` | Như trên nhưng *mutable*: method sửa trực tiếp object |
| `DateTimeInterface` | Interface chung của hai class trên; dùng làm kiểu tham số khi chấp nhận cả hai |
| `DateTimeZone` | Một timezone (mục 8.7) |
| `DateInterval` | Một khoảng thời gian: "2 tháng 5 ngày" (mục 8.9) |
| `DatePeriod` | Một dãy thời điểm cách đều: "mỗi ngày từ 1/10 tới 5/10" (mục 8.10) |

Khác biệt giữa `DateTime` và `DateTimeImmutable` là chuyện quan trọng nhất của mục này:

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');

// DateTime: mutable, method sửa chính object rồi trả về chính nó
$start = new DateTime('2026-10-03');
$end = $start->modify('+1 day');
echo $start->format('Y-m-d'), ' ', $end->format('Y-m-d'), PHP_EOL;   // in ra: 2026-10-04 2026-10-04
var_dump($start === $end);                                          // in ra: bool(true)  (cùng một object)

// DateTimeImmutable: method trả object MỚI, object cũ giữ nguyên
$start = new DateTimeImmutable('2026-10-03');
$end = $start->modify('+1 day');
echo $start->format('Y-m-d'), ' ', $end->format('Y-m-d'), PHP_EOL;   // in ra: 2026-10-03 2026-10-04
```

Với `DateTime`, `$end = $start->modify(...)` không tạo ra ngày mới: `$start` và `$end` là hai biến
cùng trỏ vào một object (object được truyền theo handle, chương 09). Bug này nguy hiểm nhất khi object
đi qua ranh giới hàm:

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');

function dueDate(DateTime $createdAt): DateTime
{
    return $createdAt->modify('+7 days');        // tưởng là tính ngày mới, thực ra sửa luôn tham số
}

$createdAt = new DateTime('2026-10-03');
$due = dueDate($createdAt);
echo $createdAt->format('Y-m-d'), PHP_EOL;       // in ra: 2026-10-10   <- ngày tạo đơn bị đổi!
echo $due->format('Y-m-d'), PHP_EOL;             // in ra: 2026-10-10
```

Quy tắc: dùng `DateTimeImmutable` mặc định, nhận tham số kiểu `DateTimeInterface` nếu muốn chấp nhận
cả hai. Gặp `DateTime` từ thư viện cũ thì đổi bằng `DateTimeImmutable::createFromMutable($dt)` hoặc
`DateTimeImmutable::createFromInterface($dt)`.

⚠️ Bẫy ngược lại của `DateTimeImmutable`: gọi method mà quên gán kết quả.

```php
<?php
declare(strict_types=1);

$d = new DateTimeImmutable('2026-10-03 15:45:00', new DateTimeZone('UTC'));
$d->setTime(0, 0);                 // không gán lại: dòng này không làm gì cả
echo $d->format('H:i'), PHP_EOL;   // in ra: 15:45
$d = $d->setTime(0, 0);            // đúng
echo $d->format('H:i'), PHP_EOL;   // in ra: 00:00
```

Từ PHP 8.5, các method như `modify()`, `add()`, `sub()`, `setTime()`, `setDate()`, `setTimezone()`
của `DateTimeImmutable` được gắn attribute `#[\NoDiscard]` (chương 10), nên dòng `$d->setTime(0, 0);`
ở trên phát warning "The return value of method DateTimeImmutable::setTime() should either be used or
intentionally ignored...". PHP 8.4 trở về trước thì im lặng.

Trong Laravel: Carbon (thư viện ngày giờ Laravel dùng) có `Carbon` kế thừa `DateTime` (mutable) và
`CarbonImmutable` kế thừa `DateTimeImmutable`. Helper `now()` và cast `datetime` của Eloquent mặc định
trả `Carbon` mutable; cast `immutable_datetime` trả bản immutable, và `Date::use(CarbonImmutable::class)`
đổi mặc định cho toàn ứng dụng ([chương 27](27-laravel-database-eloquent.md)).

### 8.5 Tạo đối tượng ngày giờ

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');
$vn = new DateTimeZone('Asia/Ho_Chi_Minh');

$now   = new DateTimeImmutable();                          // bây giờ, theo timezone mặc định
$a     = new DateTimeImmutable('2026-10-03 08:30:00', $vn); // chuỗi + timezone để hiểu chuỗi đó
$b     = new DateTimeImmutable('2026-10-03T01:30:00Z');    // chuỗi ISO 8601 có sẵn offset
$c     = new DateTimeImmutable('@1790991000');             // từ Unix timestamp
$d     = DateTimeImmutable::createFromTimestamp(1790991000); // từ timestamp, PHP 8.4+
$e     = new DateTimeImmutable('tomorrow', $vn);           // chuỗi tương đối: 00:00 ngày mai
$f     = new DateTimeImmutable('first day of next month'); // mục 8.8

var_dump($a == $b, $b == $c, $c == $d);                    // in ra: bool(true) bool(true) bool(true)
echo $a->getTimestamp(), PHP_EOL;                          // in ra: 1790991000
```

`$a`, `$b`, `$c`, `$d` là cùng một thời điểm, nên so sánh `==` cho `true` (so sánh `<`, `>`, `==` giữa
hai object ngày giờ là so sánh thời điểm, không so sánh cách hiển thị).

Constructor nhận một chuỗi *free-form* rất "dễ dãi" (cùng bộ phân tích với `strtotime()`). Điều đó
tiện khi bạn viết chuỗi trong code, nhưng nguy hiểm với dữ liệu người dùng nhập: chuỗi sai kiểu vẫn có
thể được hiểu thành một ngày nào đó. Với input có định dạng biết trước, dùng `createFromFormat()`:

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');

$d = DateTimeImmutable::createFromFormat('!d/m/Y', '03/10/2026');
echo $d->format('Y-m-d H:i:s'), PHP_EOL;          // in ra: 2026-10-03 00:00:00

var_dump(DateTimeImmutable::createFromFormat('d/m/Y', '2026-10-03'));   // in ra: bool(false)  (sai định dạng)

// ⚠️ Ngày không tồn tại không bị từ chối mà bị "tràn" sang tháng sau
$d = DateTimeImmutable::createFromFormat('!d/m/Y', '31/02/2026');
echo $d->format('Y-m-d'), PHP_EOL;                // in ra: 2026-03-03
print_r(DateTimeImmutable::getLastErrors());
// in ra: Array ( [warning_count] => 1 [warnings] => Array ( [10] => The parsed date was invalid )
//                [error_count] => 0 [errors] => Array ( ) )
```

Những điều cần biết về `createFromFormat()`:

- ⚠️ Không có `!` ở đầu (hoặc `|` ở cuối) thì các trường không có trong định dạng lấy theo giờ hiện
  tại: `createFromFormat('d/m/Y', '03/10/2026')` cho ra ngày 3/10/2026 nhưng giờ phút giây là lúc
  chạy code. So sánh hai ngày tạo theo cách này cho kết quả ngẫu nhiên. `!` đặt mọi trường về mốc
  epoch trước khi đọc chuỗi, `|` đặt các trường chưa đọc về 0.
- Trả `false` khi chuỗi không khớp định dạng. Ngày tràn (31/02) thì vẫn trả object, chỉ ghi một
  warning vào `getLastErrors()`. Từ PHP 8.2, `getLastErrors()` trả `false` khi không có warning hay
  lỗi nào. Muốn chặt chẽ thì kiểm tra cả hai:

```php
function parseDate(string $input): DateTimeImmutable
{
    $d = DateTimeImmutable::createFromFormat('!Y-m-d', $input);
    if ($d === false || DateTimeImmutable::getLastErrors() !== false) {
        throw new InvalidArgumentException("Ngày không hợp lệ: $input");
    }
    return $d;
}
```

Báo lỗi khi chuỗi free-form không hiểu được thay đổi theo phiên bản:

| Thao tác | PHP 8.2 trở về trước | PHP 8.3 trở lên |
|---|---|---|
| `new DateTimeImmutable('ngay mai')` | Ném `Exception` | Ném `DateMalformedStringException` |
| `$d->modify('ngay mai')` | Warning + trả `false` | Ném `DateMalformedStringException` |
| `new DateTimeZone('Asia/Hanoi_City')` | Ném `Exception` | Ném `DateInvalidTimeZoneException` |
| `new DateInterval('1 day')` (sai cú pháp) | Ném `Exception` | Ném `DateMalformedIntervalStringException` |

Các exception mới đều kế thừa `DateException` (kế thừa `Exception`), nên `catch (Exception $e)` cũ vẫn
bắt được. Hàm thủ tục (`strtotime()`, `date_create()`...) không đổi, vẫn trả `false`.

### 8.6 Định dạng: `format()`

`format()` (và hàm `date()`) nhận một chuỗi mẫu, trong đó mỗi chữ cái là một trường:

| Ký tự | Nghĩa | Ví dụ minh hoạ |
|---|---|---|
| `Y` | Năm 4 chữ số | `2026` |
| `y` | Năm 2 chữ số | `26` |
| `m` / `n` | Tháng có / không có số 0 đầu | `03` / `3` |
| `d` / `j` | Ngày có / không có số 0 đầu | `03` / `3` |
| `H` / `G` | Giờ 0–23 có / không có số 0 đầu | `08` / `8` |
| `h` / `g` | Giờ 1–12 có / không có số 0 đầu | `08` / `8` |
| `A` / `a` | `AM`/`PM`, `am`/`pm` | |
| `i` | Phút | `05` |
| `s` | Giây | `09` |
| `v` / `u` | Mili giây / micro giây | `123` / `123456` |
| `D` / `l` | Tên thứ viết tắt / đầy đủ (tiếng Anh) | `Sat` / `Saturday` |
| `N` | Thứ trong tuần theo ISO 8601 (1 = thứ Hai, 7 = Chủ nhật) | `6` |
| `M` / `F` | Tên tháng viết tắt / đầy đủ (tiếng Anh) | `Oct` / `October` |
| `t` | Số ngày của tháng | `31` |
| `L` | Năm nhuận (`1`/`0`) | `0` |
| `W` / `o` | Số tuần ISO / năm theo tuần ISO | `40` / `2026` |
| `e` | Tên timezone | `Asia/Ho_Chi_Minh` |
| `P` / `p` | Offset `+07:00`; `p` giống `P` nhưng in `Z` cho UTC (PHP 8.0+) | `+07:00` |
| `T` | Viết tắt timezone nếu có, không thì offset | `JST`, `+07` |
| `U` | Unix timestamp | `1790989509` |
| `c` | ISO 8601 đầy đủ | `2026-10-03T08:05:09+07:00` |

Ký tự muốn in nguyên văn thì đặt `\` phía trước, ví dụ `'Y-m-d\TH:i:s'` in chữ `T` ở giữa. Chú ý
viết chuỗi định dạng trong nháy đơn để PHP không hiểu `\t` thành ký tự tab.

```php
<?php
declare(strict_types=1);

$d = new DateTimeImmutable('2026-10-03 08:05:09.123456', new DateTimeZone('Asia/Ho_Chi_Minh'));

echo $d->format('Y-m-d H:i:s'), PHP_EOL;            // in ra: 2026-10-03 08:05:09
echo $d->format('d/m/Y'), PHP_EOL;                  // in ra: 03/10/2026
echo $d->format('D, d M Y g:i a'), PHP_EOL;         // in ra: Sat, 03 Oct 2026 8:05 am
echo $d->format('Y-m-d H:i:s.v'), PHP_EOL;          // in ra: 2026-10-03 08:05:09.123
echo $d->format(DateTimeInterface::ATOM), PHP_EOL;  // in ra: 2026-10-03T08:05:09+07:00
echo $d->format(DateTimeInterface::RFC3339_EXTENDED), PHP_EOL;   // in ra: 2026-10-03T08:05:09.123+07:00
echo $d->format('U'), PHP_EOL;                      // in ra: 1790989509
echo $d->setTimezone(new DateTimeZone('UTC'))->format('Y-m-d\TH:i:sp'), PHP_EOL;   // in ra: 2026-10-03T01:05:09Z

// ⚠️ Các lỗi gõ nhầm hay gặp
echo $d->format('Y-m-d H:m:s'), PHP_EOL;            // in ra: 2026-10-03 08:10:09   <- "m" là THÁNG, không phải phút
echo (new DateTimeImmutable('2026-10-03 20:05'))->format('h:i'), PHP_EOL;   // in ra: 08:05   <- "h" là giờ 12h
echo (new DateTimeImmutable('2024-12-30'))->format('Y o W'), PHP_EOL;      // in ra: 2024 2025 01
```

Dòng cuối: ngày 30/12/2024 thuộc tuần ISO số 1 của năm 2025. `o` là "năm của tuần ISO", chỉ dùng cùng
`W`; in ngày tháng bình thường thì luôn dùng `Y`.

Chọn định dạng khi trao đổi giữa các hệ thống:

- API và JSON: ISO 8601 / RFC 3339 có offset, tức `DateTimeInterface::ATOM` (giống `RFC3339` và `'c'`)
  hoặc `RFC3339_EXTENDED` nếu cần mili giây. Bên nhận đọc được thời điểm chính xác mà không phải đoán
  timezone.
- ⚠️ Hằng `DateTimeInterface::ISO8601` có tên gây hiểu lầm: offset của nó in dạng `+0700` (không có
  dấu `:`), manual ghi rõ nó "không tương thích ISO 8601" và giữ lại chỉ để tương thích ngược. Dùng
  `ATOM`.
- Tên thứ, tên tháng của `format()` luôn là tiếng Anh. Hiển thị "Thứ Bảy, 3 tháng 10" theo ngôn ngữ
  người dùng thì dùng `IntlDateFormatter` của extension intl, hoặc `translatedFormat()` của Carbon.

### 8.7 `DateTimeZone`: đổi timezone và các bẫy khi tạo

```php
<?php
declare(strict_types=1);

$vn  = new DateTimeZone('Asia/Ho_Chi_Minh');
$utc = new DateTimeZone('UTC');

$order = new DateTimeImmutable('2026-10-03 08:30:00', $vn);
$inUtc = $order->setTimezone($utc);                  // cùng thời điểm, đổi cách hiển thị
echo $order->format('Y-m-d H:i P'), PHP_EOL;         // in ra: 2026-10-03 08:30 +07:00
echo $inUtc->format('Y-m-d H:i P'), PHP_EOL;         // in ra: 2026-10-03 01:30 +00:00
var_dump($order == $inUtc);                          // in ra: bool(true)

foreach (['Asia/Tokyo', 'Europe/London', 'America/Los_Angeles'] as $tz) {
    echo str_pad($tz, 20), $order->setTimezone(new DateTimeZone($tz))->format('Y-m-d H:i T'), PHP_EOL;
}
// in ra: Asia/Tokyo          2026-10-03 10:30 JST
//        Europe/London       2026-10-03 02:30 BST
//        America/Los_Angeles 2026-10-02 18:30 PDT

// ⚠️ Chuỗi đã có offset (hoặc là "@timestamp") thì tham số timezone bị BỎ QUA
$x = new DateTimeImmutable('2026-10-03T01:30:00Z', $vn);
echo $x->getTimezone()->getName(), PHP_EOL;          // in ra: Z
$y = new DateTimeImmutable('@1790991000', $vn);
echo $y->getTimezone()->getName(), PHP_EOL;          // in ra: +00:00

// ⚠️ Không truyền timezone thì chuỗi được hiểu theo timezone MẶC ĐỊNH
date_default_timezone_set('Asia/Ho_Chi_Minh');
echo (new DateTimeImmutable('2026-10-03 08:30:00'))->getTimestamp(), PHP_EOL;   // in ra: 1790991000
date_default_timezone_set('UTC');
echo (new DateTimeImmutable('2026-10-03 08:30:00'))->getTimestamp(), PHP_EOL;   // in ra: 1791016200 (lệch 7 giờ)

// Offset cố định khác timezone có tên
$fixed = new DateTimeImmutable('2026-07-01 12:00', new DateTimeZone('-04:00'));
$named = new DateTimeImmutable('2026-07-01 12:00', new DateTimeZone('America/New_York'));
echo $fixed->modify('+6 months')->format('c'), PHP_EOL;   // in ra: 2027-01-01T12:00:00-04:00
echo $named->modify('+6 months')->format('c'), PHP_EOL;   // in ra: 2027-01-01T12:00:00-05:00
```

Điểm mấu chốt:

- `setTimezone()` không đổi thời điểm, chỉ đổi giờ địa phương dùng để hiển thị. Đây là thao tác "lưu
  UTC, hiển thị theo giờ người xem".
- Tham số timezone của constructor chỉ dùng để hiểu những chuỗi không tự mang offset. Chuỗi có `Z`,
  `+07:00` hay dạng `@timestamp` thì mang timezone của chính nó.
- ⚠️ Hai dòng cuối: offset cố định `-04:00` không biết gì về mùa đông, còn `America/New_York` tự
  chuyển sang `-05:00`. Vì vậy timezone của người dùng phải lưu bằng tên IANA (`America/New_York`),
  không lưu offset (`-04:00`): offset chỉ đúng tại một thời điểm.
- Tên timezone có alias cũ: `Asia/Saigon` vẫn dùng được, nhưng `DateTimeZone::listIdentifiers()` (danh
  sách tên chuẩn, hợp để làm dropdown chọn timezone) chỉ có `Asia/Ho_Chi_Minh`.
- Viết tắt như `EST`, `CST`, `IST` mơ hồ (`IST` có thể là giờ Ấn Độ, Ireland hay Israel), đừng dùng
  làm đầu vào.
- Luật giờ của các nước thay đổi theo thời gian, nên cơ sở dữ liệu timezone cũng có phiên bản. PHP
  mang theo bản riêng của nó; `timezone_version_get()` cho biết phiên bản (dạng `2026.3`). Manual ghi:
  một số distro Linux vá PHP để dùng tzdata của hệ điều hành (khi đó hàm trả `0.system`); muốn cập nhật
  thì nâng PHP hoặc cài PECL `timezonedb`.

### 8.8 Cộng trừ ngày giờ

Có hai cách:

- `modify($chuoi)`: nhận chuỗi *relative format* bằng tiếng Anh, cùng cú pháp với `strtotime()`.
- `add($interval)` / `sub($interval)`: nhận một `DateInterval` (mục 8.9).

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');
$d = new DateTimeImmutable('2026-10-03 15:00');

echo $d->modify('+1 day')->format('Y-m-d H:i'), PHP_EOL;            // in ra: 2026-10-04 15:00
echo $d->modify('-2 weeks')->format('Y-m-d H:i'), PHP_EOL;          // in ra: 2026-09-19 15:00
echo $d->modify('+1 day +3 hours')->format('Y-m-d H:i'), PHP_EOL;   // in ra: 2026-10-04 18:00
echo $d->modify('midnight')->format('Y-m-d H:i'), PHP_EOL;          // in ra: 2026-10-03 00:00
echo $d->modify('tomorrow')->format('Y-m-d H:i'), PHP_EOL;          // in ra: 2026-10-04 00:00
echo $d->modify('next monday')->format('Y-m-d D'), PHP_EOL;         // in ra: 2026-10-05 Mon
echo $d->modify('monday this week')->format('Y-m-d D'), PHP_EOL;    // in ra: 2026-09-28 Mon
echo $d->modify('last day of this month')->format('Y-m-d H:i'), PHP_EOL;   // in ra: 2026-10-31 15:00

// add()/sub() nhận DateInterval (mục 8.9)
echo $d->add(new DateInterval('P1M2D'))->format('Y-m-d'), PHP_EOL;  // in ra: 2026-11-05
echo $d->sub(new DateInterval('PT90M'))->format('H:i'), PHP_EOL;    // in ra: 13:30
```

Danh sách đầy đủ các chuỗi `modify()` hiểu được nằm ở trang "Relative Formats" của manual. Chú ý
`first day of` / `last day of` giữ nguyên giờ phút, còn `midnight`, `today`, `tomorrow` đặt giờ về
`00:00`.

⚠️ Bẫy lớn nhất: cộng tháng vào ngày cuối tháng. PHP cộng con số tháng trước, được một ngày không tồn
tại như "31/02", rồi *tràn* phần dư sang tháng sau:

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');

$jan31 = new DateTimeImmutable('2026-01-31');
echo $jan31->modify('+1 month')->format('Y-m-d'), PHP_EOL;                   // in ra: 2026-03-03
echo (new DateTimeImmutable('2024-01-31'))->modify('+1 month')->format('Y-m-d'), PHP_EOL;   // in ra: 2024-03-02 (năm nhuận)
echo (new DateTimeImmutable('2026-03-31'))->modify('-1 month')->format('Y-m-d'), PHP_EOL;   // in ra: 2026-03-03

echo $jan31->modify('last day of next month')->format('Y-m-d'), PHP_EOL;     // in ra: 2026-02-28
echo $jan31->modify('first day of next month')->format('Y-m-d'), PHP_EOL;    // in ra: 2026-02-01
```

`2026-01-31 +1 month` thành "2026-02-31", tháng 2/2026 có 28 ngày nên tràn 3 ngày thành 3/3.
`add(new DateInterval('P1M'))` cho kết quả giống hệt. Đây không phải bug mà là quy tắc của PHP (và của
nhiều thư viện khác), nhưng gần như không bao giờ là điều nghiệp vụ muốn. Với gói thuê bao theo tháng,
ngày gia hạn của người đăng ký ngày 31/1 thường phải là ngày cuối tháng 2:

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');

/** Cộng tháng, nếu tháng đích không có ngày đó thì lùi về ngày cuối tháng (không tràn). */
function addMonthsNoOverflow(DateTimeImmutable $date, int $months): DateTimeImmutable
{
    $target = $date->modify('first day of this month')->modify("+{$months} months");   // ngày 1 không bao giờ tràn
    $day = min((int) $date->format('j'), (int) $target->format('t'));                   // t = số ngày của tháng đích
    return $target->setDate((int) $target->format('Y'), (int) $target->format('n'), $day);
}

$anchor = new DateTimeImmutable('2026-01-31');      // ngày bắt đầu gói thuê bao

// Đúng: luôn tính từ ngày gốc
for ($i = 1; $i <= 4; $i++) {
    echo addMonthsNoOverflow($anchor, $i)->format('Y-m-d'), ' ';
}
echo PHP_EOL;                                        // in ra: 2026-02-28 2026-03-31 2026-04-30 2026-05-31

// Sai: cộng nối tiếp từ kỳ trước, ngày bị "trôi" vĩnh viễn về 28
$d = $anchor;
for ($i = 1; $i <= 4; $i++) {
    $d = addMonthsNoOverflow($d, 1);
    echo $d->format('Y-m-d'), ' ';
}
echo PHP_EOL;                                        // in ra: 2026-02-28 2026-03-28 2026-04-28 2026-05-28
```

Hai bài học: dùng `first day of` để tránh tràn rồi tự kẹp ngày vào cuối tháng; và luôn tính kỳ thứ n
từ ngày gốc, không cộng nối tiếp từ kỳ trước. Carbon có sẵn `addMonthsNoOverflow()` cho việc kẹp này.

### 8.9 `DateInterval` và `diff()`

`DateInterval` biểu diễn một khoảng thời gian theo các thành phần lịch: bao nhiêu năm, tháng, ngày,
giờ, phút, giây. Constructor nhận chuỗi *duration* theo ISO 8601: bắt đầu bằng `P` (period), phần ngày
trước, phần giờ sau chữ `T`:

| Chuỗi | Nghĩa |
|---|---|
| `P1D` | 1 ngày |
| `P2W` | 2 tuần |
| `P1M` | 1 tháng |
| `PT90M` | 90 phút (`M` sau `T` là phút, trước `T` là tháng) |
| `P1Y2M10DT2H30M` | 1 năm 2 tháng 10 ngày 2 giờ 30 phút |

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');

$i = new DateInterval('P1Y2M10DT2H30M');           // 1 năm 2 tháng 10 ngày 2 giờ 30 phút
echo $i->y, ' ', $i->m, ' ', $i->d, ' ', $i->h, ' ', $i->i, PHP_EOL;   // in ra: 1 2 10 2 30
echo $i->format('%y năm %m tháng %d ngày %h giờ %i phút'), PHP_EOL;  // in ra: 1 năm 2 tháng 10 ngày 2 giờ 30 phút
var_dump($i->days);                                 // in ra: bool(false)  (interval tự tạo không biết tổng số ngày)

$a = new DateTimeImmutable('2026-01-15 08:00');
$b = new DateTimeImmutable('2026-03-20 10:30');
$diff = $a->diff($b);                               // khoảng từ $a tới $b
echo $diff->format('%m tháng %d ngày %h giờ %i phút'), PHP_EOL;  // in ra: 2 tháng 5 ngày 2 giờ 30 phút
echo $diff->format('tổng %a ngày, dấu %R'), PHP_EOL;            // in ra: tổng 64 ngày, dấu +
var_dump($diff->days, $diff->invert);               // in ra: int(64) int(0)
echo $b->diff($a)->format('%R%a'), PHP_EOL;         // in ra: -64   (đảo chiều: invert = 1)

// Tuổi: số năm tròn
$birth = new DateTimeImmutable('2000-10-04');
$today = new DateTimeImmutable('2026-10-03');
echo $birth->diff($today)->y, PHP_EOL;              // in ra: 25   (còn một ngày nữa mới 26)

// Tạo interval từ chuỗi tự nhiên
echo DateInterval::createFromDateString('3 days')->d, PHP_EOL;  // in ra: 3
```

Những điều cần biết:

- `diff()` trả `DateInterval` từ object gọi tới object tham số. `invert = 1` nghĩa là tham số nằm trước
  (khoảng âm); truyền `true` làm tham số thứ hai để luôn lấy giá trị tuyệt đối.
- ⚠️ `%d` là phần "ngày" sau khi đã tách tháng (5 ngày trong "2 tháng 5 ngày"), còn `%a` là tổng số
  ngày (64). Tính "còn bao nhiêu ngày nữa" mà dùng `%d` hay `$diff->d` là sai ngay khi khoảng dài hơn
  một tháng. Tổng số ngày nằm trong `$diff->days` (chỉ có giá trị với interval do `diff()` tạo ra; interval
  tự tạo thì `days` là `false`).
- So sánh hai thời điểm thì dùng thẳng `<`, `>`, `==` trên hai object, không cần `diff()`.
- Muốn số giây chính xác giữa hai thời điểm thì lấy hiệu `getTimestamp()`: không phụ thuộc lịch hay
  DST.

### 8.10 `DatePeriod`: lặp qua một dãy ngày

`DatePeriod` sinh ra các thời điểm cách đều nhau từ một mốc bắt đầu, dùng để vẽ lịch, tạo báo cáo theo
từng ngày, liệt kê các kỳ thanh toán. Nó là một `Traversable`, lặp bằng `foreach`:

```php
<?php
declare(strict_types=1);

date_default_timezone_set('UTC');
$start = new DateTimeImmutable('2026-10-01');
$end   = new DateTimeImmutable('2026-10-05');
$oneDay = new DateInterval('P1D');

foreach (new DatePeriod($start, $oneDay, $end) as $day) {          // không gồm ngày kết thúc
    echo $day->format('m-d '), '';
}
echo PHP_EOL;                                                       // in ra: 10-01 10-02 10-03 10-04

foreach (new DatePeriod($start, $oneDay, $end, DatePeriod::INCLUDE_END_DATE) as $day) {   // PHP 8.2+
    echo $day->format('m-d '), '';
}
echo PHP_EOL;                                                       // in ra: 10-01 10-02 10-03 10-04 10-05

// Số lần lặp thay cho ngày kết thúc: ngày bắt đầu + 3 lần lặp
foreach (new DatePeriod($start, new DateInterval('P1W'), 3) as $day) {
    echo $day->format('m-d '), '';
}
echo PHP_EOL;                                                       // in ra: 10-01 10-08 10-15 10-22

foreach (new DatePeriod($start, new DateInterval('P1W'), 3, DatePeriod::EXCLUDE_START_DATE) as $day) {
    echo $day->format('m-d '), '';
}
echo PHP_EOL;                                                       // in ra: 10-08 10-15 10-22

// Chuỗi ISO 8601 "lặp R3 lần, bắt đầu từ..., mỗi P1D" (PHP 8.3+)
foreach (DatePeriod::createFromISO8601String('R3/2026-10-01T00:00:00Z/P1D') as $day) {
    echo $day->format('m-d '), '';
}
echo PHP_EOL;                                                       // in ra: 10-01 10-02 10-03 10-04
```

- Mặc định ngày kết thúc không nằm trong dãy (khoảng *nửa mở* `[start, end)`), giống cách nên viết điều
  kiện lọc theo khoảng thời gian trong SQL. Hằng `DatePeriod::INCLUDE_END_DATE` có từ PHP 8.2.
- Phần tử sinh ra cùng class với ngày bắt đầu: bắt đầu bằng `DateTimeImmutable` thì nhận
  `DateTimeImmutable`.
- `DatePeriod::createFromISO8601String()` có từ PHP 8.3; cách cũ là truyền chuỗi ISO vào constructor,
  bị deprecated từ PHP 8.4.

### 8.11 Giờ mùa hè (DST)

Ở vùng có DST, mỗi năm có hai ngày bất thường. Lấy New York năm 2026 làm ví dụ (không có DST ở Việt
Nam nên phải mượn timezone khác để thấy):

```
8/3/2026  (vặn nhanh): 01:59:59 EST  ->  03:00:00 EDT    ngày chỉ có 23 giờ, không có 02:xx
1/11/2026 (vặn lùi):   01:59:59 EDT  ->  01:00:00 EST    ngày có 25 giờ, 01:xx xảy ra hai lần
```

```php
<?php
declare(strict_types=1);

$ny  = new DateTimeZone('America/New_York');
$fmt = 'Y-m-d H:i T';

// 1. Giờ không tồn tại: 2026-03-08 đồng hồ nhảy từ 01:59:59 lên 03:00:00
echo (new DateTimeImmutable('2026-03-08 02:30', $ny))->format($fmt), PHP_EOL;   // in ra: 2026-03-08 03:30 EDT

// 2. Giờ xảy ra hai lần: 2026-11-01 đồng hồ quay từ 01:59:59 EDT về 01:00:00 EST
$utc = new DateTimeZone('UTC');
echo (new DateTimeImmutable('2026-11-01 05:30', $utc))->setTimezone($ny)->format($fmt), PHP_EOL;  // in ra: 2026-11-01 01:30 EDT
echo (new DateTimeImmutable('2026-11-01 06:30', $utc))->setTimezone($ny)->format($fmt), PHP_EOL;  // in ra: 2026-11-01 01:30 EST
echo (new DateTimeImmutable('2026-11-01 01:30', $ny))->format($fmt), PHP_EOL;   // in ra: 2026-11-01 01:30 EDT (PHP chọn lần đầu)

// 3. "Một ngày" của lịch không phải lúc nào cũng là 24 giờ
$sat = new DateTimeImmutable('2026-03-07 12:00', $ny);
$hours = fn (DateTimeImmutable $x): string => $x->format($fmt) . ' (sau ' . (($x->getTimestamp() - $sat->getTimestamp()) / 3600) . ' giờ thật)';
echo $hours($sat->modify('+1 day')), PHP_EOL;                        // in ra: 2026-03-08 12:00 EDT (sau 23 giờ thật)
echo $hours($sat->add(new DateInterval('P1D'))), PHP_EOL;           // in ra: 2026-03-08 12:00 EDT (sau 23 giờ thật)
echo $hours($sat->add(new DateInterval('PT24H'))), PHP_EOL;         // in ra: 2026-03-08 13:00 EDT (sau 24 giờ thật)
echo $hours($sat->modify('+24 hours')), PHP_EOL;                    // in ra: 2026-03-08 12:00 EDT (sau 23 giờ thật)  <- bất ngờ
echo $hours($sat->setTimestamp($sat->getTimestamp() + 86400)), PHP_EOL;   // in ra: 2026-03-08 13:00 EDT (sau 24 giờ thật)

// Liệt kê các lần đổi giờ trong năm
foreach ($ny->getTransitions(1767225600, 1798761599) as $t) {   // 2026-01-01 tới 2026-12-31 UTC
    echo gmdate('Y-m-d H:i', $t['ts']), ' UTC ', $t['abbr'], ' ', $t['offset'] / 3600, PHP_EOL;
}
// in ra: 2026-01-01 00:00 UTC EST -5   (dòng đầu là trạng thái tại mốc bắt đầu)
//        2026-03-08 07:00 UTC EDT -4
//        2026-11-01 06:00 UTC EST -5
```

Kết quả trên chạy thử trên PHP 8.1 tới 8.5 giống nhau, trừ một điểm: với PHP 8.0 trở về trước,
`add(new DateInterval('PT24H'))` cũng cho `12:00` (sau 23 giờ thật). Rút ra:

- *Giờ không tồn tại* (02:30 ngày 8/3) bị PHP đẩy tới 03:30. *Giờ mơ hồ* (01:30 ngày 1/11) được PHP
  hiểu là lần thứ nhất (EDT). Không có lỗi nào được báo. Nếu người dùng đặt lịch vào đúng những giờ
  này, bạn cần quyết định nghiệp vụ (chạy lúc nào? chạy mấy lần?) thay vì để thư viện tự chọn.
- "Cộng 1 ngày" theo lịch (`+1 day`, `P1D`) giữ nguyên giờ trên đồng hồ, nên trôi qua 23 hoặc 25 giờ
  thật. Đó thường là điều người dùng muốn với lịch hẹn: "cùng giờ ngày mai".
- ⚠️ "Cộng 24 giờ thật" thì không nên dùng `modify('+24 hours')`: như dòng có chú thích "bất ngờ" cho
  thấy, nó cho cùng kết quả với `+1 day`. Dùng `add(new DateInterval('PT24H'))` (PHP 8.1+), hoặc chắc
  chắn nhất là làm phép tính trên timestamp hay trên object ở timezone UTC (UTC không có DST), rồi mới
  đổi sang giờ địa phương để hiển thị.
- Cron, scheduler ở vùng có DST: job đặt lúc 02:30 có thể không chạy (giờ không tồn tại) hoặc chạy hai
  lần (giờ lặp). Laravel scheduler có `->timezone()` để chỉ rõ timezone của từng job
  ([chương 29](29-laravel-queue-event-schedule-cache.md)).

### 8.12 Quy tắc thực hành

| Nhu cầu | Cách làm |
|---|---|
| Lưu một thời điểm (đơn hàng tạo lúc nào) | Lưu ở UTC; timezone mặc định của PHP và Laravel để `UTC` |
| Hiển thị cho người dùng | `setTimezone(new DateTimeZone($user->timezone))` ngay trước khi `format()` |
| Timezone của người dùng | Lưu tên IANA (`Asia/Ho_Chi_Minh`), không lưu offset |
| Ngày thuần (ngày sinh, ngày lễ) | Lưu và xử lý như ngày không có giờ (`Y-m-d`, kiểu `DATE` trong MySQL); đừng đổi timezone |
| Lịch theo giờ địa phương trong tương lai ("họp 9h sáng thứ Hai hằng tuần ở Sydney") | Lưu giờ địa phương + tên timezone, tính ra UTC lúc cần (luật DST có thể đổi trước ngày đó) |
| Trao đổi qua API | Chuỗi ISO 8601 có offset (`DateTimeInterface::ATOM`), hoặc UTC có `Z` |
| Nhận ngày người dùng nhập | `createFromFormat('!...')` + kiểm tra `getLastErrors()` |
| Cộng trừ | `DateTimeImmutable`; cộng tháng thì cẩn thận cuối tháng; cộng "giờ thật" thì làm ở UTC |
| Đo thời gian chạy | `hrtime(true)` |
| Viết test có "bây giờ" | Không gọi `new DateTimeImmutable()` rải rác; nhận một *clock* qua constructor (PSR-20 `ClockInterface::now()` trả `DateTimeImmutable`), hoặc dùng `Carbon::setTestNow()` / `$this->travel()` trong Laravel ([chương 30](30-laravel-testing-octane-deploy.md)) |

Kiểu cột ngày giờ của MySQL (`DATETIME` hay `TIMESTAMP`, `time_zone` của session) và cách PDO trả về
chúng nằm ở [chương 16](16-php-va-database.md).

Đối chiếu với Java và Go:

| | PHP | Java (`java.time`) | Go (`time`) |
|---|---|---|---|
| Thời điểm | `DateTimeImmutable` (luôn kèm timezone) | `Instant` (không timezone), `ZonedDateTime` (kèm timezone) | `time.Time` (giá trị, không đổi được, kèm `Location`) |
| Ngày thuần | Không có class riêng, dùng chuỗi `Y-m-d` hoặc `DateTimeImmutable` lúc 00:00 | `LocalDate` | Không có kiểu riêng |
| Mutable? | `DateTime` mutable, `DateTimeImmutable` không | Mọi class `java.time` immutable (`java.util.Date` cũ thì mutable) | Không đổi được |
| Định dạng | Ký tự `Y-m-d H:i:s` | Mẫu `yyyy-MM-dd HH:mm:ss` | Ngày mẫu `2006-01-02 15:04:05` |

## 9. Tiền: vì sao không dùng float

### 9.1 Float không biểu diễn chính xác số thập phân

Kiểu `float` của PHP (chương 04) là số thực dấu phẩy động 64-bit theo chuẩn IEEE 754. Nó lưu số ở hệ
nhị phân, và nhiều số thập phân rất "tròn" như `0,1` không có biểu diễn hữu hạn trong hệ nhị phân, cũng
như `1/3` không viết hết được trong hệ thập phân (`0,333...`). Máy lưu giá trị gần nhất có thể, và sai
số nhỏ đó lộ ra khi tính toán:

```php
<?php
declare(strict_types=1);

var_dump(0.1 + 0.2);                   // in ra: float(0.30000000000000004)
var_dump(0.1 + 0.2 === 0.3);           // in ra: bool(false)
printf("%.20f\n", 0.1);                // in ra: 0.10000000000000000555  (giá trị thật được lưu)

$total = 0.0;
for ($i = 0; $i < 10; $i++) {
    $total += 0.1;                     // cộng 10 lần 0,1
}
var_dump($total);                      // in ra: float(0.9999999999999999)

var_dump(19.99 * 100);                 // in ra: float(1998.9999999999998)
var_dump((int) (19.99 * 100));         // in ra: int(1998)   <- 19,99 USD đổi sang cent mất 1 cent
var_dump(floor((0.1 + 0.7) * 10));     // in ra: float(7)    <- tưởng là 8
```

Với một phép tính đơn lẻ, sai số chỉ ở chữ số thứ 16, 17. Nhưng tiền thì:

- Phải chính xác tới đồng cuối cùng: báo cáo kế toán, đối soát với ngân hàng phải khớp tuyệt đối.
- Được cộng dồn hàng triệu lần (tổng doanh thu, số dư), sai số tích luỹ.
- Hay bị ép sang số nguyên (`(int)` cắt bỏ phần lẻ), và `1998,9999...` thành `1998`: mất một xu.
- So sánh `===` giữa hai số float tính theo hai đường khác nhau cho kết quả sai.

Quy tắc: không bao giờ dùng `float` để lưu hay tính tiền, ở PHP, ở database (`FLOAT`, `DOUBLE`), lẫn
trong JSON (mục 7.6). Có hai cách đúng: số nguyên theo đơn vị nhỏ nhất, hoặc số thập phân dạng chuỗi
tính bằng thư viện số chính xác.

### 9.2 Cách 1: số nguyên theo đơn vị nhỏ nhất

Lưu số tiền bằng `int` theo *minor unit* (đơn vị nhỏ nhất) của tiền tệ: `12,50 USD` lưu là `1250`
(cent), `150.000 VND` lưu là `150000`. Phép cộng, trừ, nhân với số nguyên trên `int` là chính xác tuyệt
đối, và `int` 64-bit chứa được tới khoảng 9,2 × 10^18, thừa cho mọi số tiền thực tế.

Số chữ số thập phân của mỗi tiền tệ theo chuẩn ISO 4217 khác nhau, nên luôn lưu mã tiền tệ đi kèm số
tiền và không bao giờ "chia 100" cho mọi loại tiền:

| Tiền tệ | Số chữ số thập phân | `150` đơn vị nhỏ nhất nghĩa là |
|---|---|---|
| `VND`, `JPY` | 0 | 150 đồng, 150 yên |
| `USD`, `EUR` | 2 | 1,50 USD |
| `KWD`, `BHD` | 3 | 0,150 dinar |

Khó khăn xuất hiện ở phép chia (chia đều, chia theo tỉ lệ, tính phần trăm): kết quả không chia hết thì
phần dư phải được phân bổ có chủ đích, không được để "rơi" mất:

```php
<?php
declare(strict_types=1);

/**
 * Chia một số tiền (số nguyên, đơn vị nhỏ nhất) thành $parts phần gần bằng nhau,
 * tổng các phần luôn đúng bằng số ban đầu.
 *
 * @return list<int>
 */
function allocate(int $amount, int $parts): array
{
    if ($parts <= 0) {
        throw new InvalidArgumentException('Số phần phải lớn hơn 0');
    }
    $base = intdiv($amount, $parts);        // phần nguyên của phép chia
    $remainder = $amount % $parts;          // số đơn vị còn dư
    $result = [];
    for ($i = 0; $i < $parts; $i++) {
        $result[] = $base + ($i < $remainder ? 1 : 0);   // rải phần dư cho các phần đầu
    }
    return $result;
}

print_r(allocate(100_000, 3));          // 100.000 đồng chia 3 người
// in ra: Array ( [0] => 33334 [1] => 33333 [2] => 33333 )
var_dump(array_sum(allocate(100_000, 3)) === 100_000);   // in ra: bool(true)

// Cách sai: chia rồi làm tròn từng phần
$each = round(100_000 / 3);
var_dump($each * 3);                    // in ra: float(99999)   <- mất 1 đồng
```

### 9.3 Cách 2: số thập phân dạng chuỗi với `bcmath`

Khi cần phần thập phân (tỉ giá, lãi suất, đơn giá có lẻ), dùng extension *bcmath* (Binary Calculator):
các hàm nhận số dưới dạng chuỗi thập phân và tính với độ chính xác tuỳ ý, không qua float.

Extension này không phải lúc nào cũng có sẵn: manual ghi nó chỉ có khi PHP được build với
`--enable-bcmath`. Image Docker chính thức `php:8.5-cli` không bật sẵn; cài bằng
`docker-php-ext-install bcmath` trong Dockerfile. Kiểm tra bằng `php -m | grep bcmath`.

```php
<?php
declare(strict_types=1);

var_dump(bcadd('0.1', '0.2', 1));          // in ra: string(3) "0.3"
var_dump(bcmul('19.99', '100', 0));        // in ra: string(4) "1999"
var_dump(bcsub('100000', '33333.33', 2));  // in ra: string(8) "66666.67"
var_dump(bccomp('10.50', '10.5', 2));      // in ra: int(0)   (bằng nhau; 1 nếu lớn hơn, -1 nếu nhỏ hơn)

// ⚠️ Quên tham số scale: dùng scale mặc định (ini bcmath.scale, mặc định 0)
var_dump(bcadd('0.1', '0.2'));             // in ra: string(1) "0"

// ⚠️ bc* CẮT BỎ phần thừa chứ không làm tròn
var_dump(bcdiv('2', '3', 2));              // in ra: string(4) "0.66"   (không phải 0.67)
var_dump(bcmul('1.25', '1.1', 2));         // in ra: string(4) "1.37"   (1.375 bị cắt)

// ⚠️ Chỉ nhận chuỗi số "chuẩn": không số mũ, không dấu phẩy, không khoảng trắng
try {
    bcadd('1e3', '1', 0);
} catch (ValueError $e) {
    echo $e->getMessage(), PHP_EOL;         // in ra: bcadd(): Argument #1 ($num1) is not well-formed
}
var_dump((string) 0.00001);                // in ra: string(6) "1.0E-5"  <- vì vậy đừng đổi float sang chuỗi rồi đưa vào bcmath
```

Các hàm chính: `bcadd`, `bcsub`, `bcmul`, `bcdiv`, `bcmod`, `bcpow`, `bcsqrt`, `bccomp`. Tham số cuối
`$scale` là số chữ số sau dấu thập phân của kết quả. Ba bẫy trong ví dụ:

- ⚠️ Bỏ `$scale` thì dùng ini `bcmath.scale`, mặc định `"0"`: `bcadd('0.1', '0.2')` ra `"0"`. Luôn truyền
  scale tường minh.
- ⚠️ Phần thừa bị *cắt bỏ* (truncate), không làm tròn: `2/3` với scale 2 là `"0.66"`. Muốn làm tròn thì
  tính với scale lớn hơn rồi làm tròn có chủ đích (`bcround()`, PHP 8.4+).
- Đầu vào phải là chuỗi số đúng dạng, sai thì ném `ValueError`. Đừng truyền float đã ép sang chuỗi:
  `(string) 0.00001` là `"1.0E-5"`, và nếu số đó vốn đã sai lệch vì là float thì bcmath cũng không cứu
  được.

PHP 8.4 bổ sung hai thứ quan trọng: các hàm làm tròn `bcround()`, `bcfloor()`, `bcceil()` (thêm
`bcdivmod()`), và class `BcMath\Number`: một object không đổi được (immutable) bọc một số thập phân,
dùng được toán tử `+ - * / % **` và so sánh `< > ==`.

```php
<?php
declare(strict_types=1);

use BcMath\Number;

// PHP 8.4+: làm tròn có chủ đích
var_dump(bcround('1.385', 2));                          // in ra: string(4) "1.39"  (mặc định: .5 ra xa số 0)
var_dump(bcround('1.385', 2, RoundingMode::HalfEven));  // in ra: string(4) "1.38"  (.5 về số chẵn)
var_dump(bcfloor('-1.5'), bcceil('1.2'));               // in ra: string(2) "-2"  string(1) "2"

// PHP 8.4+: BcMath\Number, dùng được toán tử
$price    = new Number('199000');
$quantity = 3;
$vatRate  = new Number('0.08');

$subtotal = $price * $quantity;                         // int, string, Number đều dùng được làm toán hạng
$vat      = ($subtotal * $vatRate)->round(0, RoundingMode::HalfEven);
$total    = $subtotal + $vat;
echo $subtotal, ' + ', $vat, ' = ', $total, PHP_EOL;   // in ra: 597000 + 47760 = 644760

var_dump($subtotal->scale, ($subtotal * $vatRate)->scale);   // in ra: int(0) int(2)
var_dump(new Number('0.1') + new Number('0.2') == new Number('0.3'));   // in ra: bool(true)
echo new Number('10') / 3, PHP_EOL;                    // in ra: 3.3333333333  (chia không hết: scale tự nới tối đa +10)
echo (new Number('2'))->div('3', 2), PHP_EOL;          // in ra: 0.66  (vẫn là cắt bỏ, muốn làm tròn thì ->round())
```

Về `BcMath\Number` (theo RFC "Support object type in BCMath" và RFC sửa đổi "Fix up BCMath Number
class" đi kèm, cả hai vào PHP 8.4):

- Không dùng ini `bcmath.scale`. Scale của kết quả được tự tính: cộng trừ lấy scale lớn hơn của hai
  toán hạng, nhân lấy tổng hai scale, chia không hết thì nới thêm tối đa 10 chữ số so với số bị chia.
- Phép tính luôn cắt bỏ phần thừa như các hàm `bc*`; làm tròn thì gọi `->round($scale, $mode)`.
- ⚠️ Toán hạng nên là `Number`, chuỗi số hoặc `int`. Constructor không nhận float: có `strict_types` thì
  `new Number(0.1)` ném `TypeError`; không có `strict_types` thì chạy thử thấy float bị ép về int (`0`)
  kèm `Deprecated`. Còn với toán tử, chạy thử `new Number('0.1') + 0.1` trên PHP 8.5 cho kết quả `0.1` kèm
  thông báo `Deprecated: Implicit conversion from float 0.1 to int loses precision`: float bị ép về int,
  phép cộng âm thầm sai.
- ⚠️ `json_encode()` một `Number` ra `{"value":"1.50","scale":2}` (hai property public của nó). Đổi sang
  chuỗi (`(string) $n`) trước khi đưa vào JSON.

### 9.4 Làm tròn

Làm tròn tiền là quyết định nghiệp vụ (thuế làm tròn theo hoá đơn hay theo dòng? `.5` lên hay xuống?),
nên phải làm tường minh, đúng một chỗ, với chế độ làm tròn được chọn có chủ đích:

```php
<?php
declare(strict_types=1);

var_dump(round(2.5), round(3.5), round(-2.5));           // in ra: float(3) float(4) float(-3)
var_dump(round(2.5, 0, PHP_ROUND_HALF_EVEN));            // in ra: float(2)
var_dump(round(2.5, 0, RoundingMode::HalfEven));         // in ra: float(2)   (enum, PHP 8.4+)
var_dump(number_format(1234567.891, 2, ',', '.'));       // in ra: string(12) "1.234.567,89"
```

- `round()` mặc định là *half away from zero*: `.5` làm tròn ra xa số 0 (`2.5 → 3`, `-2.5 → -3`). Hằng
  cũ của nó tên là `PHP_ROUND_HALF_UP`, dễ gây hiểu lầm là "luôn làm tròn lên".
- *Half even* (còn gọi *banker's rounding*): `.5` làm tròn về số chẵn gần nhất (`2.5 → 2`, `3.5 → 4`).
  Vì lúc lên lúc xuống nên khi cộng nhiều số đã làm tròn, sai lệch không dồn về một phía. Có trong
  `round()` từ lâu qua hằng `PHP_ROUND_HALF_EVEN`.
- PHP 8.4 thêm enum `RoundingMode` dùng được cho `round()`, `bcround()` và `BcMath\Number::round()`, với
  tám chế độ: `HalfAwayFromZero`, `HalfTowardsZero`, `HalfEven`, `HalfOdd`, `TowardsZero`,
  `AwayFromZero`, `NegativeInfinity`, `PositiveInfinity`.
- `round()` vẫn nhận và trả `float`, nên chỉ dùng cho hiển thị hoặc số liệu không phải tiền. Tiền thì
  làm tròn bằng `bcround()` / `Number::round()` hoặc trên số nguyên.
- `number_format($so, $chuSoLe, $dauThapPhan, $dauNghin)` để hiển thị; nó cũng làm tròn, nên chỉ gọi ở
  bước cuối cùng.

### 9.5 Trong dự án thật

- Thư viện: [brick/money](https://github.com/brick/money) hoặc [moneyphp/money](https://github.com/moneyphp/money)
  cung cấp object `Money` gồm số tiền và tiền tệ, có sẵn phân bổ (allocate) và làm tròn tường minh.
  Laravel dùng [brick/math](https://github.com/brick/math) bên trong cho cast `decimal`.
- Database: cột `DECIMAL(p, s)` lưu số thập phân chính xác; PDO trả giá trị cột `DECIMAL` về PHP dạng
  chuỗi ([chương 16](16-php-va-database.md)). ⚠️ Đừng ép `(float)` chuỗi đó "cho tiện".
- Laravel: cast `decimal:2` trả về chuỗi (bên trong dùng `BigDecimal` của brick/math, làm tròn
  `HalfUp`), không phải float. `Number::currency()` để hiển thị theo locale.
- API: trả tiền dạng chuỗi thập phân hoặc số nguyên minor unit kèm mã tiền tệ (mục 7.6).

| | PHP | Java | Go |
|---|---|---|---|
| Số thập phân chính xác | `bcmath`, `BcMath\Number` (8.4), brick/math | `BigDecimal` (phải truyền `RoundingMode` khi chia không hết) | Không có trong thư viện chuẩn; dùng `int64` minor unit hoặc thư viện như `shopspring/decimal` |
| Bẫy chung | `float` | `double`, và `new BigDecimal(0.1)` (dựng từ double, mang theo sai số) | `float64` |

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| `if (!$content)` sau `file_get_contents()` | File rỗng trả `""`, cũng "falsy" | So sánh `=== false` (mục 1.4) |
| `while (!feof($fh)) { $line = fgets($fh); ... }` | Vòng lặp chạy thêm một lần với `false` | `while (($line = fgets($fh)) !== false)` (mục 1.3) |
| `file_put_contents()` thẳng vào file cấu hình/cache nhiều người đọc | Người đọc thấy file rỗng hoặc ghi dở | Ghi file tạm cùng thư mục rồi `rename()` (mục 1.5) |
| Đường dẫn tương đối `'data.csv'` trong script chạy bằng cron | Tính theo thư mục làm việc, không theo vị trí file | `__DIR__ . '/data.csv'` (mục 2.1) |
| `chmod($f, 755)` | Số thập phân, không phải bát phân | `chmod($f, 0755)` (mục 2.5) |
| Chạy `php artisan` bằng `root` trên server | File log/cache tạo ra thuộc `root`, FPM không ghi được | Chạy bằng user của FPM; không `chmod 777` (mục 2.5) |
| "Đọc, tính, ghi" một file mà không khoá | Race condition, mất cập nhật | `fopen('c+')` + `flock(LOCK_EX)` (mục 3.2) |
| Dựa vào `flock` khi chạy nhiều server | Khoá chỉ có hiệu lực trên một máy | Khoá trong database hoặc Redis (mục 3.4) |
| `explode(',', $line)` để đọc CSV | Sai khi ô có dấu phẩy, nháy, xuống dòng | `fgetcsv()` / `SplFileObject::READ_CSV` (mục 5.1) |
| Không truyền `$escape` cho hàm CSV | Deprecated từ 8.4; escape `\` làm hỏng dữ liệu | Truyền `escape: ''` (mục 5.3) |
| `json_decode()` không kiểm tra lỗi | JSON hỏng trả `null`, lẫn với JSON `"null"` | Luôn `JSON_THROW_ON_ERROR` (mục 7.5) |
| Trả mảng sau `array_filter()` ra JSON | Mảng không còn là list, thành object | `array_values()` (mục 7.2) |
| `JSON_NUMERIC_CHECK` | Số điện thoại mất số 0 đầu | Ép kiểu đúng chỗ (mục 7.3) |
| Gửi ID 64-bit dạng số cho JavaScript | Mất chính xác quá `2^53 - 1` | Gửi dạng chuỗi (mục 7.6) |
| `DateTime` truyền qua hàm rồi `modify()` | Sửa luôn object của người gọi | `DateTimeImmutable` (mục 8.4) |
| `$d->setTime(0, 0);` với `DateTimeImmutable` | Không gán kết quả, không có tác dụng | `$d = $d->setTime(0, 0);` (mục 8.4) |
| `createFromFormat('d/m/Y', ...)` không có `!` | Giờ phút giây lấy theo lúc chạy | `'!d/m/Y'` + kiểm tra `getLastErrors()` (mục 8.5) |
| `H:m:s` trong chuỗi định dạng | `m` là tháng | `H:i:s` (mục 8.6) |
| Lưu offset `+07:00` làm timezone người dùng | Offset đổi theo DST | Lưu tên IANA (mục 8.7) |
| `+1 month` từ ngày 31 | Tràn sang tháng sau | `first day of` + kẹp cuối tháng, tính từ ngày gốc (mục 8.8) |
| Dùng `$diff->d` làm "số ngày còn lại" | Chỉ là phần ngày sau khi tách tháng | `$diff->days` / `%a` (mục 8.9) |
| `float` cho tiền | Sai số nhị phân, mất xu khi ép `int` | Số nguyên minor unit hoặc bcmath (mục 9) |
| `bcadd('0.1', '0.2')` không có scale | Scale mặc định 0, ra `"0"` | Luôn truyền scale (mục 9.3) |

## Tóm tắt chương

- Hàm file trả `false` kèm warning chứ không ném exception; luôn kiểm tra `=== false`. File nhỏ đọc ghi
  cả file, file lớn đọc từng dòng qua handle hoặc `SplFileObject` bọc trong generator.
- Ghi file nhiều người đọc thì ghi file tạm cùng thư mục rồi `rename()`. Nhiều tiến trình cùng sửa thì
  khoá bằng `flock`, nhớ rằng khoá chỉ tự nguyện và chỉ trên một máy.
- Đường dẫn tương đối tính theo thư mục làm việc; dùng `__DIR__`. Quyền file viết bát phân và phụ thuộc
  user đang chạy PHP.
- Stream là khái niệm chung cho file, bộ nhớ, stdin, mạng; `php://temp` cho dữ liệu tạm có thể lớn.
- CSV phải đọc ghi bằng hàm CSV, luôn truyền `escape: ''`; chú ý BOM khi làm việc với Excel.
- JSON: luôn `JSON_THROW_ON_ERROR`; chỉ list mới thành JSON array; ID và tiền đi qua JSON dạng chuỗi;
  chuỗi phải là UTF-8 hợp lệ. `json_validate()` (8.3) chỉ dùng khi không cần dữ liệu.
- Ngày giờ: phân biệt thời điểm với giờ địa phương; giữ timezone mặc định là UTC, chỉ đổi khi hiển
  thị; dùng `DateTimeImmutable`, timezone tên IANA, ISO 8601 có offset khi trao đổi.
- Cộng tháng ở cuối tháng và DST là hai nơi phép tính ngày giờ ra kết quả bất ngờ; "1 ngày" lịch khác
  "24 giờ" thật.
- Tiền: không dùng float. Dùng số nguyên theo đơn vị nhỏ nhất kèm mã tiền tệ, hoặc bcmath /
  `BcMath\Number` với scale và chế độ làm tròn tường minh.

## Câu hỏi tự kiểm tra

1. Vì sao `while (!feof($fh))` xử lý thêm một lần với `false`? Viết lại vòng lặp đúng. (mục 1.3)
2. Ghi file tạm rồi `rename()` bảo đảm điều gì, và điều kiện nào làm mất bảo đảm đó? (mục 1.5)
3. Một script chạy tốt khi bạn gõ tay nhưng báo không tìm thấy file khi chạy bằng cron. Nguyên nhân
   có thể là gì? (mục 2.1)
4. Vì sao đếm lượt xem bằng file phải mở mode `c+` thay vì `w+`, và vì sao
   `file_put_contents(..., LOCK_EX)` chưa đủ cho bài toán này? (mục 3.2)
5. `php://memory` khác `php://temp` ở đâu? Khi nào chọn cái nào? (mục 4.3)
6. Một ô CSV có giá trị `C:\temp\`. Điều gì xảy ra khi ghi rồi đọc lại với escape mặc định? PHP 8.4
   thay đổi gì? (mục 5.3)
7. Vì sao `json_decode()` trả `null` là chưa đủ để biết có lỗi? Vì sao không nên trộn
   `JSON_THROW_ON_ERROR` với `json_last_error()`? (mục 7.5)
8. Đơn đặt lúc 06:00 sáng 3/10 giờ Việt Nam được lưu ở UTC. Theo UTC nó thuộc ngày nào, và điều đó ảnh
   hưởng gì tới báo cáo doanh thu theo ngày? (mục 8.1, 8.12)
9. Ở New York, `modify('+1 day')`, `add(new DateInterval('PT24H'))` và `modify('+24 hours')` tính từ
   trưa 7/3/2026 cho kết quả gì? (mục 8.11)
10. Vì sao `(int) (19.99 * 100)` ra `1998`? Nêu hai cách lưu tiền đúng và ưu nhược điểm của mỗi cách.
    (mục 9.1 tới 9.3)

## Bài tập

1. **Đọc CSV đơn hàng.** Viết hàm `readOrders(string $path): Generator` đọc một file CSV (có thể có BOM,
   dấu phân cách `,` hoặc `;` tự phát hiện từ dòng tiêu đề), trả từng đơn dạng mảng có key, bỏ dòng
   trống, ném exception kèm số bản ghi khi số cột sai. Tạo một file 1 triệu dòng để thử và in
   `memory_get_peak_usage(true)` sau khi đọc hết để chứng minh bộ nhớ không tăng theo kích thước file.
2. **Cache ra file an toàn.** Viết class `FileCache` với `get(string $key): mixed` và
   `set(string $key, mixed $value, int $ttlSeconds): void`, lưu mỗi key thành một file JSON (gồm giá trị
   và thời điểm hết hạn). Yêu cầu: ghi nguyên tử, JSON luôn dùng `JSON_THROW_ON_ERROR`, key được băm
   thành tên file để tránh path traversal, thời điểm hết hạn tính theo UTC. Viết thêm một script CLI xoá
   các file đã hết hạn và in số file đã xoá ra `STDERR`.
3. **Lịch thanh toán.** Viết hàm nhận ngày bắt đầu, số kỳ, timezone IANA của khách và tổng số tiền
   (số nguyên theo đơn vị nhỏ nhất), trả danh sách kỳ thanh toán: ngày đến hạn hằng tháng (không tràn
   cuối tháng, tính từ ngày gốc), thời điểm đến hạn là 09:00 giờ địa phương của khách đổi ra UTC dạng
   ISO 8601, và số tiền mỗi kỳ chia sao cho tổng khớp tuyệt đối. Thử với khách ở `America/New_York` có
   kỳ rơi vào tháng 3 và tháng 11 để kiểm tra DST.
4. **So sánh float và bcmath.** Cộng 0,1 một triệu lần bằng `float`, bằng `bcadd()` và bằng
   `BcMath\Number` (nếu có PHP 8.4). In kết quả, sai lệch so với 100000 và thời gian chạy đo bằng
   `hrtime()`. Giải thích con số bạn thấy.

## Đọc thêm

PHP manual:

- Filesystem: [file_get_contents](https://www.php.net/manual/en/function.file-get-contents.php) ·
  [file_put_contents](https://www.php.net/manual/en/function.file-put-contents.php) ·
  [fopen](https://www.php.net/manual/en/function.fopen.php) ·
  [fgets](https://www.php.net/manual/en/function.fgets.php) ·
  [flock](https://www.php.net/manual/en/function.flock.php) ·
  [rename](https://www.php.net/manual/en/function.rename.php) ·
  [tempnam](https://www.php.net/manual/en/function.tempnam.php) ·
  [chmod](https://www.php.net/manual/en/function.chmod.php) ·
  [clearstatcache](https://www.php.net/manual/en/function.clearstatcache.php) ·
  [fsync](https://www.php.net/manual/en/function.fsync.php)
- Stream: [php:// wrappers](https://www.php.net/manual/en/wrappers.php.php) ·
  [Supported Protocols and Wrappers](https://www.php.net/manual/en/wrappers.php) ·
  [HTTP context options](https://www.php.net/manual/en/context.http.php) ·
  [Filesystem ini](https://www.php.net/manual/en/filesystem.configuration.php) ·
  [CLI I/O streams](https://www.php.net/manual/en/features.commandline.io-streams.php)
- CSV và SPL: [fgetcsv](https://www.php.net/manual/en/function.fgetcsv.php) ·
  [fputcsv](https://www.php.net/manual/en/function.fputcsv.php) ·
  [SplFileObject](https://www.php.net/manual/en/class.splfileobject.php)
- JSON: [json_encode](https://www.php.net/manual/en/function.json-encode.php) ·
  [json_decode](https://www.php.net/manual/en/function.json-decode.php) ·
  [JSON constants](https://www.php.net/manual/en/json.constants.php) ·
  [json_validate](https://www.php.net/manual/en/function.json-validate.php) ·
  [JsonSerializable](https://www.php.net/manual/en/class.jsonserializable.php)
- Date/Time: [DateTimeImmutable](https://www.php.net/manual/en/class.datetimeimmutable.php) ·
  [DateTimeInterface](https://www.php.net/manual/en/class.datetimeinterface.php) ·
  [format](https://www.php.net/manual/en/datetime.format.php) ·
  [Supported Date and Time Formats](https://www.php.net/manual/en/datetime.formats.php) ·
  [DateTimeZone](https://www.php.net/manual/en/class.datetimezone.php) ·
  [DateInterval](https://www.php.net/manual/en/class.dateinterval.php) ·
  [DatePeriod](https://www.php.net/manual/en/class.dateperiod.php) ·
  [Date/Time configuration](https://www.php.net/manual/en/datetime.configuration.php) ·
  [hrtime](https://www.php.net/manual/en/function.hrtime.php) ·
  [timezone_version_get](https://www.php.net/manual/en/function.timezone-version-get.php)
- Số: [BCMath](https://www.php.net/manual/en/book.bc.php) ·
  [BcMath\Number](https://www.php.net/manual/en/class.bcmath-number.php) ·
  [round](https://www.php.net/manual/en/function.round.php) ·
  [RoundingMode](https://www.php.net/manual/en/enum.roundingmode.php)

RFC và php-src:

- [Deprecations for PHP 8.4](https://wiki.php.net/rfc/deprecations_php_8_4) (mục CSV escaping) ·
  [Kill proprietary CSV escaping mechanism](https://wiki.php.net/rfc/kill-csv-escaping)
- [json_validate](https://wiki.php.net/rfc/json_validate) ·
  [More Appropriate Date/Time Exceptions](https://wiki.php.net/rfc/datetime-exceptions) ·
  [Marking return value as important (#\[\NoDiscard\])](https://wiki.php.net/rfc/marking_return_value_as_important)
- [Support object type in BCMath](https://wiki.php.net/rfc/support_object_type_in_bcmath) ·
  [Fix up BCMath Number class](https://wiki.php.net/rfc/fix_up_bcmath_number_class) ·
  [RoundingMode enum](https://wiki.php.net/rfc/correctly_name_the_rounding_mode_and_make_it_an_enum) ·
  [bcround, bcfloor, bcceil](https://wiki.php.net/rfc/adding_bcround_bcfloor_bcceil_to_bcmath)
- php-src `UPGRADING` của 8.0 tới 8.5 (mốc phiên bản trong chương đối chiếu với các file này).

Khác:

- [RFC 4180](https://www.rfc-editor.org/rfc/rfc4180) (CSV) ·
  [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) (JSON) ·
  [RFC 3339](https://www.rfc-editor.org/rfc/rfc3339) (ngày giờ trên Internet)
- Laravel 13: [Deployment: Directory Permissions](https://laravel.com/docs/13.x/deployment#directory-permissions) ·
  [Date Casting, Serialization, and Timezones](https://laravel.com/docs/13.x/eloquent-mutators#date-casting-and-timezones) ·
  [Preventing Task Overlaps](https://laravel.com/docs/13.x/scheduling#preventing-task-overlaps)
- Jon Skeet: [Storing UTC is not a silver bullet](https://codeblog.jonskeet.uk/2019/03/27/storing-utc-is-not-a-silver-bullet/)
- [brick/money](https://github.com/brick/money) · [moneyphp/money](https://github.com/moneyphp/money)
