# Chương 21. Chất lượng code: test, phân tích tĩnh, chuẩn code

> [← Mục lục](README.md) · [← Chương 20: Hiệu năng và profiling](20-hieu-nang.md) · [Chương 22: Tổng hợp PHP 8.0 tới 8.5 →](22-phien-ban-moi.md)

**Bạn sẽ học được:**

- Test tự động là gì, các loại test (unit, integration, feature, end-to-end) khác nhau ở đâu, và nên
  viết loại nào cho chỗ nào.
- Viết và chạy test bằng PHPUnit; đọc được test viết bằng Pest; dùng test double (stub, mock, fake,
  spy) đúng chỗ và thiết kế code để test được.
- Phân tích tĩnh (static analysis) là gì; dùng PHPStan với level, baseline, kiểu trong PHPDoc và
  generics; biết Larastan và Psalm làm thêm gì.
- Dùng Rector để sửa code hàng loạt và nâng cấp phiên bản PHP một cách an toàn.
- Chuẩn code PSR-12 và PER Coding Style; giữ style tự động bằng PHP-CS-Fixer hoặc Laravel Pint.
- Ghép tất cả vào CI, và dùng mutation testing (Infection, `pest --mutate`) để đo xem test có thật sự
  bắt được lỗi hay không.

**Cần biết trước:** [Chương 04: Kiểu dữ liệu](04-kieu-du-lieu.md) (`strict_types`, khai báo kiểu,
`TypeError`), [Chương 08: Hàm](08-ham.md), [Chương 09](09-oop-co-ban.md) và
[Chương 10](10-oop-nang-cao.md) (class, interface, `final`, `readonly`),
[Chương 11: Namespace, autoload và Composer](11-namespace-composer.md) (`require-dev`, `vendor/bin`,
PSR-4), [Chương 12: Lỗi và exception](12-loi-exception.md).

Cách chạy ví dụ: các ví dụ PHP thuần (không cần thư viện) lưu thành file `.php` rồi chạy
`php ten-file.php`. Ví dụ viết cho PHP 8.5 và đã chạy thử trên 8.5. Máy chưa cài PHP thì dùng Docker,
chạy trong thư mục chứa file:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

Các ví dụ dùng PHPUnit, Pest, PHPStan, Rector, PHP-CS-Fixer cần một project Composer. Cách dựng một
project nhỏ để chạy chúng có ở [mục 3.1](#31-cài-đặt-và-dựng-project-thử). Mốc phiên bản trong chương
(10/2026): PHPUnit 13.4, Pest 5.3, PHPStan 2.2, Larastan 3.12, Psalm 6.19 (7.0 đang beta), Rector
2.6, PHP-CS-Fixer 3.95, Pint 1.32, Infection 0.35.

## 1. Chất lượng code là gì và vì sao cần công cụ

### 1.1 Bug được phát hiện ở đâu

Mọi đoạn code đều có thể sai. Câu hỏi thực tế không phải "làm sao để không bao giờ sai" mà là "lỗi bị
phát hiện **ở đâu** và **khi nào**". Cùng một lỗi, phát hiện càng muộn thì càng đắt:

```
 lúc gõ code      lúc commit       lúc mở PR (CI)      lúc QA test      trên production
 ───────────► ───────────────► ──────────────────► ───────────────► ──────────────────►
 IDE gạch đỏ     formatter,       phân tích tĩnh,     người kiểm thử   khách hàng gặp lỗi,
                 hook kiểm tra    test tự động,       bấm thử          mất dữ liệu, mất tiền,
                                  review của đồng                      phải điều tra log
                                  nghiệp
 rẻ nhất  ─────────────────────────────────────────────────────────────────────►  đắt nhất
```

Lỗi bị IDE gạch đỏ thì sửa trong 5 giây. Cùng lỗi đó lên production có thể làm hỏng dữ liệu của hàng
nghìn đơn hàng, phải viết script sửa dữ liệu, giải thích với khách. Vì vậy các team chuyên nghiệp đặt
nhiều lớp kiểm tra tự động ở phía bên trái của trục thời gian, để lỗi bị chặn càng sớm càng tốt.

*Chất lượng code* (code quality) trong chương này hiểu theo nghĩa thực dụng: code **làm đúng việc**
(đúng hành vi), **dễ đọc** (người khác hiểu được), và **dễ sửa mà không vỡ** (có lưới an toàn khi thay
đổi). Không có công cụ nào đo được trọn vẹn "chất lượng", nhưng có công cụ cho từng khía cạnh.

### 1.2 Bốn lớp bảo vệ

| Lớp | Câu hỏi nó trả lời | Có chạy code không | Công cụ PHP tiêu biểu |
|---|---|---|---|
| Chuẩn code (*coding standard*) và *formatter* | Code có viết theo một kiểu thống nhất không (thụt lề, dấu cách, vị trí ngoặc) | Không | PHP-CS-Fixer, Laravel Pint, PHP_CodeSniffer |
| Phân tích tĩnh (*static analysis*) | Code có chỗ nào chắc chắn hoặc có thể sai không (gọi method không tồn tại, truyền sai kiểu, dùng `null`) | Không | PHPStan, Psalm, Larastan |
| Test tự động (*automated test*) | Khi chạy với input cụ thể, code có cho ra kết quả mong đợi không | Có | PHPUnit, Pest |
| Đo chất lượng test | Bộ test có thật sự bắt được lỗi không | Có (chạy test nhiều lần) | Infection, `pest --mutate`, code coverage |

Thêm một loại công cụ không "kiểm" mà "sửa": *Rector* tự động viết lại code theo quy tắc (ví dụ đổi
`strpos($s, 'x') !== false` thành `str_contains($s, 'x')` trên toàn bộ dự án).

Và một lớp con người: *code review* (đồng nghiệp đọc thay đổi trước khi merge). Các công cụ tự động
tồn tại một phần để giải phóng review khỏi những việc máy làm được (dấu cách, kiểu dữ liệu), để người
review tập trung vào thiết kế và nghiệp vụ.

Tất cả được ghép lại trong *CI* (continuous integration, tích hợp liên tục): mỗi lần có người đẩy code
lên, một máy chủ tự chạy toàn bộ các lớp trên, và chặn merge nếu có lớp nào báo lỗi (mục 9).

```
                     ┌─────────────────────── CI chạy trên mỗi pull request ───────────────────────┐
 dev đẩy code  ───►  │  formatter --test  ─►  Rector --dry-run  ─►  PHPStan  ─►  PHPUnit/Pest       │  ─► được merge
                     │  (style)               (code kiểu cũ)        (kiểu,       (hành vi)            │
                     │                                              logic)                           │
                     └──────────────── một bước đỏ là chặn merge ──────────────────────────────────┘
```

### 1.3 Vì sao PHP đặc biệt cần các công cụ này

Java, Go, C# có bước *compile* (biên dịch) trước khi chạy. Trình biên dịch đọc toàn bộ code và từ chối
build nếu bạn gọi method không tồn tại hay truyền `string` vào chỗ cần `int`. Lỗi bị chặn ở máy dev.

PHP không có bước đó. PHP biên dịch từng file thành opcode ngay lúc chạy (xem
[Chương 02](02-php-chay-nhu-the-nao.md)) và chỉ kiểm tra kiểu **ở dòng code thực sự được chạy tới**.
Một dòng sai nằm trong nhánh `if` hiếm khi chạy có thể nằm im hàng tháng:

```php
<?php
declare(strict_types=1);

final class User
{
    public function __construct(public string $name) {}
}

function findUser(int $id): ?User
{
    return $id === 1 ? new User('An') : null;
}

function greet(int $id): string
{
    return 'Xin chào ' . findUser($id)->name;   // quên xử lý trường hợp null
}

echo greet(1), PHP_EOL;       // in ra: Xin chào An
echo greet(2), PHP_EOL;       // in ra: Warning: Attempt to read property "name" on null in ... on line 16
                              //        rồi in "Xin chào " (chuỗi rỗng ở chỗ tên)
echo 'Vẫn chạy tiếp', PHP_EOL; // in ra: Vẫn chạy tiếp
```

Ba điều đáng chú ý:

- File này parse và chạy bình thường. Không có bước nào báo lỗi trước khi chạy.
- Với `greet(1)` mọi thứ đúng. Nếu bạn chỉ thử bằng tay với user có thật, bạn sẽ không bao giờ thấy
  lỗi.
- Với `greet(2)`, PHP 8 chỉ phát `Warning` rồi chạy tiếp và trả về một chuỗi sai. Trên production
  warning thường chỉ được ghi vào log, người dùng nhận một trang có nội dung sai.

Hai cách bắt lỗi này trước production:

1. **Test**: viết một test gọi `greet(2)` và khẳng định kết quả phải là gì. Test chỉ bắt được nếu
   **có người nghĩ ra** ca `id = 2`.
2. **Phân tích tĩnh**: PHPStan đọc code, thấy `findUser()` khai báo trả về `?User` (có thể là `null`),
   và báo ngay dòng `->name` là truy cập property trên giá trị có thể `null`, **không cần ai nghĩ ra
   ca thử**. Lỗi này thuộc nhóm kiểm tra ở level 8 của PHPStan (mục 6.3).

Hai cách bổ sung cho nhau, không thay thế nhau: phân tích tĩnh bắt được cả lớp lỗi về kiểu mà không cần
ca thử, nhưng không biết nghiệp vụ (nó không biết giảm giá 10% hay 20% mới đúng). Test kiểm được nghiệp
vụ, nhưng chỉ kiểm những ca người viết nghĩ tới. Vì vậy trong hệ sinh thái PHP, phân tích tĩnh thường
được gọi là "compiler thứ hai".

⚠️ `declare(strict_types=1)` và khai báo kiểu đầy đủ không thay thế được phân tích tĩnh. Chúng chỉ
khiến PHP **ném `TypeError` lúc chạy** khi sai kiểu, tức là vẫn ở phía bên phải của trục thời gian.
Nhưng chúng làm phân tích tĩnh **mạnh hơn rất nhiều**, vì công cụ có thêm thông tin về kiểu để suy
luận.

### 1.4 Bản đồ công cụ trong chương

| Công cụ | Làm gì | Sửa code của bạn? | Mục |
|---|---|---|---|
| PHPUnit | Framework test chuẩn của PHP | Không | 3 |
| Pest | Framework test cú pháp gọn, chạy trên nền PHPUnit | Không | 4 |
| Mockery | Thư viện tạo test double (Laravel dùng nó) | Không | 5.5 |
| PHPStan | Phân tích tĩnh, có level 0 tới 10 | Không | 6 |
| Larastan | Extension của PHPStan để hiểu Laravel | Không | 6.7 |
| Psalm | Phân tích tĩnh, mạnh về taint analysis (lần dấu dữ liệu bẩn) | Không (có chế độ tự sửa riêng) | 6.8 |
| Rector | Viết lại code theo quy tắc, nâng cấp phiên bản | Có | 7 |
| PHP-CS-Fixer | Sửa style theo chuẩn | Có | 8.4 |
| Laravel Pint | Bọc PHP-CS-Fixer, cấu hình sẵn cho Laravel | Có | 8.5 |
| Infection | Mutation testing | Không (sửa tạm trong bộ nhớ để thử) | 10.3 |

Tất cả đều cài bằng Composer vào `require-dev` (chỉ dùng lúc phát triển, không lên production; xem
[Chương 11](11-namespace-composer.md)) và chạy qua `vendor/bin/<tên>`.

## 2. Test tự động là gì

### 2.1 Test là code kiểm tra code

Khi mới học, cách kiểm tra code quen thuộc nhất là chạy thử rồi nhìn bằng mắt: `var_dump()` kết quả,
mở trình duyệt bấm thử. Cách đó có ba vấn đề:

- **Không lặp lại được rẻ.** Sửa một dòng, bạn phải bấm lại toàn bộ các ca đã thử. Thực tế không ai
  làm, nên các ca cũ không được kiểm lại.
- **Phụ thuộc trí nhớ và con mắt.** Người nhìn phải biết kết quả đúng là gì và phải để ý được chỗ sai.
- **Không chạy tự động được.** Máy CI không có mắt.

*Test tự động* (automated test) là một đoạn code gọi code của bạn với input cụ thể, rồi **so** kết quả
nhận được với kết quả mong đợi, và tự kết luận "đạt" (*pass*) hay "không đạt" (*fail*). Không cần
người đọc output.

Để thấy rằng không có gì ma thuật, ta tự viết một "framework test" tí hon bằng PHP thuần:

```php
<?php
declare(strict_types=1);

// ===== Code cần test (system under test) =====
function applyDiscount(int $price, int $percent): int
{
    if ($percent < 0 || $percent > 100) {
        throw new InvalidArgumentException('percent phải nằm trong 0..100');
    }
    return intdiv($price * (100 - $percent), 100);
}

// ===== Một "framework test" tí hon =====
final class MiniTest
{
    private int $passed = 0;
    /** @var list<string> */
    private array $failures = [];

    public function assertSame(string $name, mixed $expected, mixed $actual): void
    {
        if ($expected === $actual) {
            $this->passed++;
            return;
        }
        $this->failures[] = sprintf(
            '%s: mong đợi %s, nhận được %s',
            $name,
            var_export($expected, true),
            var_export($actual, true),
        );
    }

    /** @param class-string<Throwable> $class */
    public function assertThrows(string $name, string $class, callable $action): void
    {
        try {
            $action();
        } catch (Throwable $e) {
            if ($e instanceof $class) {
                $this->passed++;
                return;
            }
            $this->failures[] = "$name: ném " . $e::class . " thay vì $class";
            return;
        }
        $this->failures[] = "$name: không ném exception nào";
    }

    public function report(): int
    {
        foreach ($this->failures as $f) {
            echo 'FAIL ', $f, PHP_EOL;
        }
        printf("%d pass, %d fail%s", $this->passed, count($this->failures), PHP_EOL);
        return $this->failures === [] ? 0 : 1;   // exit code: 0 = thành công
    }
}

// ===== Các test =====
$t = new MiniTest();
$t->assertSame('giảm 10%', 90_000, applyDiscount(100_000, 10));
$t->assertSame('giảm 0% giữ nguyên giá', 100_000, applyDiscount(100_000, 0));
$t->assertSame('giảm 100% về 0', 0, applyDiscount(100_000, 100));
$t->assertSame('làm tròn xuống', 669, applyDiscount(999, 33));
$t->assertThrows('percent âm bị từ chối', InvalidArgumentException::class, fn () => applyDiscount(100, -1));
$t->assertThrows('percent > 100 bị từ chối', InvalidArgumentException::class, fn () => applyDiscount(100, 101));

exit($t->report());
// in ra: 6 pass, 0 fail
```

Giờ giả sử ai đó vô tình sửa dòng `return` thành `intdiv(...) + 1`. Chạy lại, không cần nhìn code:

```
FAIL giảm 10%: mong đợi 90000, nhận được 90001
FAIL giảm 0% giữ nguyên giá: mong đợi 100000, nhận được 100001
FAIL giảm 100% về 0: mong đợi 0, nhận được 1
FAIL làm tròn xuống: mong đợi 669, nhận được 670
2 pass, 4 fail
```

Và script kết thúc bằng `exit(1)`. *Exit code* (mã thoát) là con số process trả cho hệ điều hành khi
kết thúc: quy ước 0 là thành công, khác 0 là có lỗi. CI chỉ nhìn vào con số này để quyết định bước đó
xanh hay đỏ. Mọi công cụ trong chương (PHPUnit, PHPStan, Pint...) đều tuân theo quy ước này.

Một framework test thật như PHPUnit làm đúng những việc trên, cộng thêm rất nhiều tiện ích: tự tìm
file test, chạy từng test cô lập, hàng trăm loại assertion, báo lỗi dễ đọc, đo coverage, xuất báo cáo
cho CI. Nhưng ý tưởng cốt lõi chỉ là: **gọi code, so kết quả, báo pass/fail**.

### 2.2 Giải phẫu một test

Vài thuật ngữ sẽ gặp suốt chương:

- *System under test* (SUT): phần code mà test đang kiểm. Trong ví dụ trên là `applyDiscount()`.
- *Assertion* (khẳng định): một phép kiểm "giá trị này phải bằng giá trị kia", "đoạn này phải ném
  exception". Assertion sai thì test fail.
- *Arrange, Act, Assert* (AAA, còn gọi là *Given, When, Then*): cấu trúc ba đoạn của một test.
  1. Arrange (chuẩn bị): tạo dữ liệu, object cần thiết.
  2. Act (hành động): gọi **một** hành động trên SUT.
  3. Assert (kiểm): so kết quả.
- *Happy path*: kịch bản mọi thứ hợp lệ (giảm 10% cho giá 100.000). *Unhappy path* (hay *error
  path*): kịch bản lỗi (percent âm). Một hàm chưa được test đủ nếu mới có happy path.
- *Edge case* (ca biên): giá trị ở rìa của miền hợp lệ, nơi bug hay nấp: 0, 100, chuỗi rỗng, mảng
  rỗng, số âm, ngày cuối tháng, năm nhuận. Trong ví dụ, `0%`, `100%` và `-1`, `101` là các ca biên.

```php
public function testGiamGiaChoKhachVip(): void
{
    // Arrange
    $cart = new Cart();
    $cart->add(new Item('Áo', 200_000), quantity: 2);
    $customer = Customer::vip();

    // Act
    $total = $cart->totalFor($customer);

    // Assert
    $this->assertSame(360_000, $total);
}
```

(Đoạn trên minh hoạ hình dạng, các class `Cart`, `Item`, `Customer` là giả định.)

### 2.3 Thế nào là một test tốt

Test tồi còn tệ hơn không có test: nó tốn thời gian chạy, đỏ vô cớ khiến team mất niềm tin, hoặc xanh
trong khi code sai. Một test tốt có các tính chất sau:

| Tính chất | Nghĩa | Vi phạm thường gặp |
|---|---|---|
| Nhanh | Chạy trong vài mili giây tới vài trăm mili giây | Gọi API thật, `sleep()`, khởi tạo cả framework cho một phép tính |
| Độc lập (*isolated*) | Chạy riêng hay chạy chung, theo thứ tự nào cũng cho cùng kết quả | Test B dùng dữ liệu do test A tạo ra |
| Lặp lại được (*deterministic*) | Chạy 1000 lần ra cùng kết quả | Phụ thuộc giờ hiện tại, số ngẫu nhiên, thứ tự dòng của `SELECT` không có `ORDER BY` |
| Tự kiểm (*self-validating*) | Tự kết luận pass/fail, không cần người đọc output | Test chỉ `var_dump()` mà không assert |
| Kiểm hành vi, không kiểm cách làm | Assert trên thứ người ngoài thấy được (giá trị trả về, dữ liệu đã lưu, email đã gửi) | Assert thứ tự gọi method nội bộ, gọi method private bằng reflection |
| Tên nói lên hành vi | Đọc tên là biết đang kiểm gì | `testRefund2`, `testItWorks` |

Test lúc đỏ lúc xanh dù code không đổi gọi là *flaky test*. Đây là loại test nguy hiểm nhất: team quen
bấm "chạy lại" và bỏ qua cả lần đỏ thật. Các nguyên nhân phổ biến (thời gian, thứ tự, mạng, dữ liệu
dùng chung) và cách chữa được bàn ở mục 5.7 (thiết kế để test được) và
[Chương 30](30-laravel-testing-octane-deploy.md) (cô lập database trong test Laravel).

⚠️ "Kiểm hành vi, không kiểm cách làm" là nguyên tắc quan trọng nhất về lâu dài. Test gắn chặt vào
cách viết bên trong (*implementation*) sẽ đỏ hàng loạt mỗi khi bạn *refactor* (sửa cấu trúc code mà
không đổi hành vi), dù hành vi vẫn đúng. Khi đó test trở thành vật cản thay vì lưới an toàn.

### 2.4 Các loại test

Các loại test khác nhau ở chỗ **mỗi test kiểm bao nhiêu phần của hệ thống cùng lúc**. Kiểm càng nhiều
thành phần thật thì càng giống thực tế, nhưng càng chậm, càng khó dựng, và khi đỏ thì càng khó biết
hỏng ở đâu.

```
                 phạm vi một test
  ┌─────────────────────────────────────────────────────────────────┐
  │ End-to-end: trình duyệt/HTTP client → Nginx → PHP → DB, Redis,   │
  │             queue, dịch vụ ngoài (môi trường giống production)   │
  │   ┌───────────────────────────────────────────────────────┐     │
  │   │ Feature (Laravel): HTTP request giả lập trong cùng     │     │
  │   │ process → routing → middleware → controller → DB test  │     │
  │   │   ┌─────────────────────────────────────────────┐     │     │
  │   │   │ Integration: code của bạn + một thành phần   │     │     │
  │   │   │ thật (DB, filesystem, Redis)                 │     │     │
  │   │   │   ┌─────────────────────────────────┐       │     │     │
  │   │   │   │ Unit: một hàm/class, phụ thuộc   │       │     │     │
  │   │   │   │ được thay bằng đồ giả hoặc thuần │       │     │     │
  │   │   │   └─────────────────────────────────┘       │     │     │
  │   │   └─────────────────────────────────────────────┘     │     │
  │   └───────────────────────────────────────────────────────┘     │
  └─────────────────────────────────────────────────────────────────┘
```

| Loại | Kiểm gì | Ví dụ | Tốc độ | Bắt được |
|---|---|---|---|---|
| *Unit test* | Một hàm hoặc một nhóm nhỏ class, không đụng DB, mạng, file | `applyDiscount()`, class `Money`, một quy tắc tính phí ship | Rất nhanh (ms) | Sai logic, sai công thức, quên ca biên |
| *Integration test* | Code của bạn chạy cùng một thành phần thật | Repository lưu đơn vào MySQL rồi đọc lại; class đọc file CSV thật | Chậm hơn (chục tới trăm ms) | Câu SQL sai, *mapping* sai (chuyển dòng DB thành object), lỗi transaction, sai quyền file |
| *Feature test* (thuật ngữ của Laravel) | Một tính năng từ request HTTP tới DB, chạy trong cùng process, không qua web server thật | `POST /orders` trả 201, có dòng mới trong bảng `orders`, job gửi mail được đẩy vào queue | Trung bình | Lỗi route, middleware, validation, phân quyền, ghép các tầng |
| *End-to-end test* (E2E) | Cả hệ thống từ ngoài vào, giống người dùng thật, thường qua trình duyệt | Mở trang, đăng nhập, đặt hàng, thấy trang cảm ơn | Chậm (giây) | Lỗi cấu hình, JavaScript, tích hợp giữa các dịch vụ |

Vài loại khác hay nghe, phân theo **mục đích** chứ không theo phạm vi:

- *Regression test* (test hồi quy): test viết ra để chứng minh một bug đã sửa không quay lại. Quy tắc
  tốt: **mỗi bug fix đi kèm một test tái hiện bug đó**. Viết test trước, thấy nó đỏ, rồi sửa code cho
  nó xanh.
- *Smoke test*: vài kiểm tra nhanh ngay sau khi deploy, xem hệ thống còn sống và luồng chính chạy được
  (trang chủ trả 200, đăng nhập được).
- *Contract test*: kiểm hai dịch vụ vẫn hiểu nhau về định dạng request/response. Dùng khi có nhiều
  dịch vụ do nhiều team sở hữu.

⚠️ "Unit" không nhất thiết là "một class". Có hai trường phái:

- *Solitary* (đơn độc): mỗi test chỉ chạy đúng một class, mọi class khác nó dùng đều được thay bằng đồ
  giả.
- *Sociable* (hoà đồng): test một hành vi, cho phép đi qua vài class thật của chính bạn, chỉ thay đồ
  giả cho những thứ chậm hoặc không kiểm soát được (DB, mạng, thời gian).

Hai thuật ngữ này do Jay Fields đặt. Martin Fowler (bài *UnitTest*) gọi người theo solitary là trường
phái *mockist*, người theo sociable là trường phái *classic*, và tự nhận mình theo classic. Sách
*Software Engineering at Google* (chương 13) cũng có lời khuyên "Prefer Realism Over Isolation": ưu
tiên dùng đồ thật hơn là cô lập bằng đồ giả. Lý do chính: test sociable ít gắn vào cấu trúc bên trong
hơn, nên refactor ít làm vỡ test hơn.

Trong Laravel: thư mục `tests/Unit` chứa test **không khởi động** ứng dụng (không có database, không
có service của framework); `tests/Feature` chứa test có khởi động ứng dụng. Tài liệu Laravel khuyên
phần lớn test nên là feature test, vì chúng cho nhiều tự tin nhất rằng hệ thống chạy đúng như một
tổng thể. Cách viết feature test, cô lập database, và các *fake* của Laravel được dạy ở
[Chương 30](30-laravel-testing-octane-deploy.md). Chương này tập trung vào phần nền chung cho mọi
project PHP.

### 2.5 Viết bao nhiêu test, loại nào

*Test pyramid* (kim tự tháp test, Mike Cohn) là lời khuyên kinh điển: nhiều unit test nhất, ít
integration test hơn, ít E2E nhất. Lý do: unit test nhanh, rẻ, đỏ thì chỉ đúng chỗ hỏng; E2E chậm và
dễ flaky.

*Testing trophy* (chiếc cúp, Kent C. Dodds) là mô hình khác: dưới cùng là phân tích tĩnh, rồi unit,
phần **lớn nhất là integration**, trên cùng là một ít E2E. Lập luận: với ứng dụng web nhiều CRUD (tạo,
đọc, sửa, xoá dữ liệu), logic thuần không nhiều; bug thường nằm ở chỗ nối các tầng (câu SQL,
validation, phân quyền), và unit test với DB giả bỏ sót đúng những bug đó.

```
     Pyramid                Trophy
       /E2E\                [ E2E ]
      /integ.\        [  integration  ]   ← phần lớn nhất
     /  unit  \            [ unit ]
    /__________\          [ static ]      ← PHPStan, Psalm
```

Không có hình dạng đúng cho mọi dự án. Tỉ lệ phụ thuộc vào **rủi ro nằm ở đâu**:

- Module tính giá, thuế, lương với nhiều công thức và ca biên: nhiều unit test, mỗi ca biên một test.
- Trang quản trị CRUD trên Laravel: chủ yếu feature test có database thật.
- Luồng thanh toán, đăng ký: thêm vài E2E cho đúng các luồng sống còn.

Khi thời gian có hạn, ưu tiên test theo thứ tự:

1. Chỗ mất tiền hoặc mất dữ liệu: thanh toán, hoàn tiền, phân quyền, xoá dữ liệu.
2. Logic nhiều nhánh và nhiều ca biên.
3. Chỗ đã từng có bug (regression test).
4. Không đáng test: getter/setter không có logic, code của framework (framework đã tự test), code sắp
   xoá.

*TDD* (test-driven development, phát triển hướng test) là cách làm viết test **trước** code, theo vòng
*red, green, refactor*: viết một test cho hành vi chưa có (đỏ), viết code tối thiểu cho test xanh, rồi
dọn code trong khi giữ test xanh. TDD là một phương pháp, không phải điều kiện để có test tốt; nhưng
viết test trước cho bug fix (regression test) là thói quen nên có dù không theo TDD.

## 3. PHPUnit

*PHPUnit* (tác giả Sebastian Bergmann) là framework test chuẩn của PHP. Gần như mọi thư viện
và framework PHP đều được test bằng nó; Pest (mục 4) cũng chạy trên nền PHPUnit. Học PHPUnit trước là
học phần lõi của mọi công cụ test PHP.

### 3.1 Cài đặt và dựng project thử

PHPUnit ra một bản major mỗi năm vào đầu tháng 2, mỗi bản yêu cầu một mức PHP tối thiểu:

| Bản | PHP tối thiểu | Phát hành | Hết sửa lỗi |
|---|---|---|---|
| PHPUnit 13 | 8.4 | 06/02/2026 | 04/02/2028 |
| PHPUnit 12 | 8.3 | 07/02/2025 | 05/02/2027 |
| PHPUnit 11 | 8.2 | 02/02/2024 | 06/02/2026 (đã hết) |

(Nguồn: trang *Supported Versions* của PHPUnit.) Bản mới nhất lúc viết là 13.4. Ứng dụng Laravel 13
mới tạo dùng `phpunit/phpunit: ^12.5.12`, vì Laravel 13 còn hỗ trợ PHP 8.3 mà PHPUnit 13 cần 8.4. Ví
dụ trong chương chạy được trên cả 12.5 và 13.x, chỗ nào khác nhau sẽ ghi rõ.

Dựng một project nhỏ để thực hành, cấu trúc thư mục:

```
demo/
├── composer.json
├── phpunit.xml
├── src/            code của bạn, namespace App\
│   └── PriceCalculator.php
├── tests/          test, namespace Tests\
│   └── PriceCalculatorTest.php
└── vendor/         Composer tạo ra
```

`composer.json` khai autoload PSR-4 cho cả code và test (xem [Chương 11](11-namespace-composer.md)):

```json
{
    "name": "demo/chat-luong-code",
    "type": "project",
    "require": {
        "php": "^8.4"
    },
    "autoload": {
        "psr-4": { "App\\": "src/" }
    },
    "autoload-dev": {
        "psr-4": { "Tests\\": "tests/" }
    }
}
```

Chạy trong thư mục `demo/`:

```bash
composer require --dev phpunit/phpunit       # thêm vào require-dev, tạo vendor/bin/phpunit
vendor/bin/phpunit --generate-configuration  # hỏi vài câu (Enter để nhận mặc định), tạo phpunit.xml
vendor/bin/phpunit                           # chạy toàn bộ test
```

Máy chưa có PHP và Composer thì chạy Composer bằng Docker như [Chương 11](11-namespace-composer.md),
còn PHPUnit chạy bằng `docker run --rm -v "$PWD":/app -w /app php:8.5-cli vendor/bin/phpunit`.

PHPUnit còn được phát hành dạng một file *PHAR* (`phpunit-13.phar` tải ở phar.phpunit.de), và tài liệu
PHPUnit khuyến nghị cách này. Trong thực tế các project ứng dụng (đặc biệt là Laravel) hầu hết cài qua
Composer; cả hai cách đều chạy cùng một bộ test.

File `phpunit.xml` do `--generate-configuration` của PHPUnit 13.4 tạo ra (giữ nguyên, chỉ thêm chú
thích):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="https://schema.phpunit.de/13.4/phpunit.xsd"
         bootstrap="vendor/autoload.php"
         cacheDirectory=".phpunit.cache"
         executionOrder="defects"
         requireCoverageMetadata="true"
         beStrictAboutCoverageMetadata="true"
         beStrictAboutOutputDuringTests="true"
         displayDetailsOnPhpunitDeprecations="true"
         failOnPhpunitDeprecation="true"
         failOnRisky="true"
         failOnWarning="true"
         warnWhenPhpIsNotConfiguredForDevelopment="true">
    <testsuites>
        <testsuite name="default">
            <directory>tests</directory>
        </testsuite>
    </testsuites>

    <source ignoreIndirectDeprecations="true" restrictNotices="true" restrictWarnings="true">
        <include>
            <directory>src</directory>
        </include>
    </source>
</phpunit>
```

| Thuộc tính / phần tử | Nghĩa |
|---|---|
| `bootstrap` | File chạy trước mọi test, thường là autoloader của Composer |
| `cacheDirectory` | Nơi PHPUnit lưu lịch sử chạy (để chạy test vừa fail trước) và cache phân tích. Thêm vào `.gitignore` |
| `executionOrder="defects"` | Chạy các test lần trước bị fail lên đầu, để thấy lỗi sớm |
| `requireCoverageMetadata` | Mỗi test class phải khai mình kiểm code nào (`#[CoversClass]`, `#[CoversNothing]`...), không thì bị coi là *risky* |
| `failOnRisky`, `failOnWarning` | Test risky hoặc code phát `E_WARNING` trong lúc test thì cả lượt chạy bị tính là thất bại (exit code khác 0) |
| `<testsuites>` | Thư mục chứa test. Laravel có hai suite `Unit` và `Feature` |
| `<source>` | Thư mục chứa code **của bạn**. PHPUnit dùng nó để tính coverage và để phân biệt cảnh báo phát ra từ code của bạn với cảnh báo từ thư viện trong `vendor/` |
| `warnWhenPhpIsNotConfiguredForDevelopment` | Cảnh báo khi `php.ini` không theo khuyến nghị cho môi trường dev (ví dụ `memory_limit` không phải `-1`, `error_reporting` không phải `-1`, `zend.assertions` không bật) |

⚠️ Với cấu hình trên, một test class **không** có `#[CoversClass(...)]` hay `#[CoversNothing]` sẽ bị
đánh dấu risky, và vì `failOnRisky="true"` nên cả lượt chạy đỏ. Đây là chủ ý (bắt bạn nói rõ test kiểm
gì, coverage chính xác hơn), nhưng người mới hay bất ngờ. Các ví dụ dưới đây đều khai `#[CoversClass]`.

### 3.2 Test đầu tiên

Code cần test, đặt ở `src/PriceCalculator.php`:

```php
<?php
declare(strict_types=1);

namespace App;

use InvalidArgumentException;

final class PriceCalculator
{
    public function applyDiscount(int $price, int $percent): int
    {
        if ($percent < 0 || $percent > 100) {
            throw new InvalidArgumentException("percent phải nằm trong 0..100, nhận $percent");
        }
        return intdiv($price * (100 - $percent), 100);
    }

    public function shippingFee(int $orderTotal): int
    {
        return $orderTotal >= 500_000 ? 0 : 30_000;
    }
}
```

Test, đặt ở `tests/PriceCalculatorTest.php`:

```php
<?php
declare(strict_types=1);

namespace Tests;

use App\PriceCalculator;
use InvalidArgumentException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Test;
use PHPUnit\Framework\TestCase;

#[CoversClass(PriceCalculator::class)]
final class PriceCalculatorTest extends TestCase
{
    public function testAppliesTenPercentDiscount(): void
    {
        // Arrange
        $calc = new PriceCalculator();

        // Act
        $result = $calc->applyDiscount(100_000, 10);

        // Assert
        $this->assertSame(90_000, $result);
    }

    #[Test]
    public function rounds_down_to_whole_dong(): void
    {
        $calc = new PriceCalculator();

        $this->assertSame(669, $calc->applyDiscount(999, 33));
    }

    public function testRejectsNegativePercent(): void
    {
        $calc = new PriceCalculator();

        $this->expectException(InvalidArgumentException::class);

        $calc->applyDiscount(100_000, -5);
    }
}
```

Các quy tắc PHPUnit dùng để nhận ra test:

- Một *test class* kế thừa `PHPUnit\Framework\TestCase`. Quy ước: test cho class `X` tên là `XTest`,
  file `XTest.php`.
- Một *test method* là method `public` có tên bắt đầu bằng `test`, **hoặc** có attribute `#[Test]`
  (khi đó đặt tên tự do, ví dụ kiểu snake_case như `rounds_down_to_whole_dong`, quen thuộc trong
  Laravel).
- Mỗi test method chạy trên **một object test class mới**. Thuộc tính gán ở test này không còn ở test
  sau.

Chạy:

```
$ vendor/bin/phpunit
PHPUnit 13.4.0 by Sebastian Bergmann and contributors.

Runtime:       PHP 8.5.10
Configuration: /app/phpunit.xml

...                                                                 3 / 3 (100%)

Time: 00:00.006, Memory: 28.38 MB

OK (3 tests, 3 assertions)
```

(Số `Time`, `Memory` trong các output của chương đo trên môi trường thử, chỉ để minh hoạ; máy bạn sẽ
ra số khác.)

Mỗi dấu `.` là một test đạt. Các ký tự khác có thể gặp:

| Ký tự | Nghĩa |
|---|---|
| `.` | Đạt, không có vấn đề gì |
| `F` | *Failure*: một assertion sai |
| `E` | *Error*: có exception không mong đợi hoặc lỗi PHP trong lúc chạy test |
| `W`, `N`, `D` | Test chạy qua code phát warning, notice, deprecation |
| `R` | *Risky*: test có vấn đề (không assert gì, thiếu coverage metadata...) |
| `S`, `I` | Bị bỏ qua (*skipped*), chưa hoàn thành (*incomplete*) |

Tuỳ chọn `--testdox` in tên test thành câu dễ đọc, hữu ích để xem test có mô tả đúng hành vi không:

```
$ vendor/bin/phpunit --testdox
...
Price Calculator (Tests\PriceCalculator)
 ✔ Applies ten percent discount
 ✔ Rounds down to whole dong
 ✔ Rejects negative percent

OK (3 tests, 3 assertions)
```

Một vài lệnh chạy hay dùng:

```bash
vendor/bin/phpunit tests/PriceCalculatorTest.php        # chỉ một file
vendor/bin/phpunit --filter testRejectsNegativePercent  # chỉ test có tên khớp mẫu
vendor/bin/phpunit --testsuite Unit                     # chỉ một suite trong phpunit.xml
vendor/bin/phpunit --stop-on-failure                    # dừng ngay ở test fail đầu tiên
```

Trong Laravel, `php artisan test` gọi PHPUnit (hoặc Pest nếu project dùng Pest) với output đẹp hơn;
các tuỳ chọn trên vẫn dùng được.

### 3.3 Assertion và cách đọc lỗi

PHPUnit có hàng trăm assertion. Một nhóm nhỏ dùng nhiều nhất:

| Assertion | Đạt khi |
|---|---|
| `assertSame($expected, $actual)` | `$expected === $actual` (cùng kiểu, cùng giá trị; với object là **cùng một object**) |
| `assertEquals($expected, $actual)` | Bằng nhau theo so sánh "lỏng" của PHPUnit (không xét kiểu chặt, object so theo thuộc tính) |
| `assertEqualsWithDelta($e, $a, $delta)` | Hai số thực chênh nhau không quá `$delta` |
| `assertTrue($x)`, `assertFalse($x)`, `assertNull($x)` | `$x` đúng là `true`, `false`, `null` |
| `assertCount($n, $arrayOrCountable)` | Có đúng `$n` phần tử |
| `assertContains($needle, $array)` | Mảng chứa phần tử (so bằng `===`) |
| `assertArrayHasKey($key, $array)` | Mảng có key |
| `assertInstanceOf(Foo::class, $obj)` | `$obj instanceof Foo` |
| `assertStringContainsString($needle, $s)` | Chuỗi chứa chuỗi con |

Quy ước tham số: **giá trị mong đợi đứng trước, giá trị thực đứng sau**. Đảo ngược không làm test sai,
nhưng thông báo lỗi sẽ nói ngược ("mong đợi X" thành "mong đợi Y"), rất dễ gây nhầm khi đọc.

⚠️ Ưu tiên `assertSame` thay vì `assertEquals`. Ví dụ chạy thật (PHPUnit 13.4):

```php
$this->assertEquals(90000, '90000');   // ĐẠT: so sánh lỏng, int và string "bằng nhau"
$this->assertSame(90000, '90000');     // FAIL: Failed asserting that '90000' is identical to 90000.

$this->assertSame(0.3, 0.1 + 0.2);     // FAIL: Failed asserting that 0.30000000000000004 is identical to 0.3.
$this->assertEqualsWithDelta(0.3, 0.1 + 0.2, 0.000001);   // ĐẠT

$this->assertSame(['id' => 1, 'name' => 'An'], ['name' => 'An', 'id' => 1]);   // FAIL: thứ tự key khác
$this->assertEquals(['id' => 1, 'name' => 'An'], ['name' => 'An', 'id' => 1]); // ĐẠT
```

Một hàm lẽ ra trả `int` mà trả `string` là bug (ví dụ JSON trả `"90000"` thay vì `90000`, client
JavaScript cộng chuỗi). `assertEquals` để lọt bug đó, `assertSame` thì không. Chỉ dùng `assertEquals`
khi bạn chủ ý không quan tâm kiểu hoặc thứ tự key, hoặc khi so hai object khác nhau theo giá trị thuộc
tính. Số thực thì dùng `assertEqualsWithDelta` (lý do sai số dấu phẩy động: xem
[Chương 04](04-kieu-du-lieu.md)).

Khi assertion fail, PHPUnit in tên test, thông báo, và với mảng thì in *diff* (dòng `-` là mong đợi,
dòng `+` là thực tế):

```
There was 1 failure:

1) Tests\CompareTest::testArrays
Failed asserting that two arrays are identical.
--- Expected
+++ Actual
@@ @@
 Array &0 [
-    'id' => 1,
     'name' => 'An',
+    'id' => 1,
 ]

/app/tests/CompareTest.php:34

FAILURES!
Tests: 6, Assertions: 6, Failures: 3.
```

Một assertion fail sẽ **dừng** test method đó ngay: các assertion phía sau không chạy.

**Kiểm exception.** Gọi `expectException()` **trước** dòng được cho là sẽ ném, và để dòng đó là dòng
cuối của test:

```php
public function testRejectsNegativePercent(): void
{
    $calc = new PriceCalculator();

    $this->expectException(InvalidArgumentException::class);
    $this->expectExceptionMessage('percent phải nằm trong 0..100');   // PHPUnit 12.5: kiểm "chứa chuỗi"

    $calc->applyDiscount(100_000, -5);
    // mọi dòng sau đây không bao giờ chạy, vì exception đã thoát khỏi method
}
```

- Nếu không có exception nào được ném, test fail.
- Từ PHPUnit 13.2, `expectExceptionMessage()` bị *soft-deprecated* (đánh dấu lỗi thời trong tài liệu,
  sẽ bị xoá ở PHPUnit 15). Thay bằng `expectExceptionMessageIsOrContains()` (cùng nghĩa "bằng hoặc
  chứa") hoặc `expectExceptionMessageIs()` (phải bằng đúng). Trên PHPUnit 12.5 thì vẫn dùng
  `expectExceptionMessage()`.

⚠️ Đặt `expectException()` ở đầu test rồi chạy nhiều dòng phía sau là bẫy: nếu một dòng **chuẩn bị**
(Arrange) vô tình ném cùng loại exception, test vẫn đạt dù dòng cần kiểm chưa hề chạy.

### 3.4 Fixture: `setUp()` và `tearDown()`

*Fixture* là trạng thái cần dựng sẵn cho test (object, file tạm, dữ liệu). Khi nhiều test cần cùng một
fixture, đưa phần dựng vào `setUp()`:

| Method | Chạy khi nào |
|---|---|
| `setUp(): void` | Trước **mỗi** test method |
| `tearDown(): void` | Sau **mỗi** test method (kể cả khi test fail), dùng để dọn: xoá file tạm, đóng kết nối |
| `setUpBeforeClass(): void` (static) | Một lần trước test đầu tiên của class |
| `tearDownAfterClass(): void` (static) | Một lần sau test cuối cùng của class |

```php
final class ShippingFeeTest extends TestCase
{
    private PriceCalculator $calc;

    protected function setUp(): void
    {
        // chạy lại trước MỖI test: mỗi test có một object mới, không dính trạng thái test trước
        $this->calc = new PriceCalculator();
    }

    // ... các test dùng $this->calc
}
```

⚠️ Dùng `setUpBeforeClass()` hay thuộc tính `static` để chia sẻ object **có trạng thái** giữa các test
là nguồn gốc của test phụ thuộc thứ tự: test A sửa object, test B chạy sau thấy object đã bị sửa. Chỉ
chia sẻ những thứ đắt và không đổi (ví dụ một kết nối tới database test). PHPUnit có tuỳ chọn
`--order-by random` để chạy test theo thứ tự ngẫu nhiên và lộ ra các phụ thuộc kiểu này.

### 3.5 Data provider: một test, nhiều bộ dữ liệu

Ca biên thường đi thành bộ: ngay dưới ngưỡng, đúng ngưỡng, trên ngưỡng. Viết mỗi ca một method thì lặp
code. *Data provider* là một method `public static` trả về danh sách các bộ tham số; PHPUnit gọi test
method một lần cho mỗi bộ, và tính **mỗi bộ là một test riêng** (bộ này fail không che bộ khác).

```php
<?php
declare(strict_types=1);

namespace Tests;

use App\PriceCalculator;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\TestWith;
use PHPUnit\Framework\TestCase;

#[CoversClass(PriceCalculator::class)]
final class ShippingFeeTest extends TestCase
{
    private PriceCalculator $calc;

    protected function setUp(): void
    {
        $this->calc = new PriceCalculator();
    }

    /** @return array<string, array{int, int}> */
    public static function shippingCases(): array
    {
        return [
            'đơn nhỏ trả phí'           => [100_000, 30_000],
            'ngay dưới ngưỡng'          => [499_999, 30_000],
            'đúng ngưỡng được miễn phí' => [500_000, 0],
            'trên ngưỡng'               => [800_000, 0],
        ];
    }

    #[DataProvider('shippingCases')]
    public function testShippingFee(int $orderTotal, int $expectedFee): void
    {
        $this->assertSame($expectedFee, $this->calc->shippingFee($orderTotal));
    }

    // Bộ dữ liệu ngắn thì khai thẳng bằng attribute, không cần method riêng
    #[TestWith([0, 100_000])]
    #[TestWith([50, 50_000])]
    #[TestWith([100, 0])]
    public function testDiscountBoundaries(int $percent, int $expected): void
    {
        $this->assertSame($expected, $this->calc->applyDiscount(100_000, $percent));
    }
}
```

```
$ vendor/bin/phpunit --testdox tests/ShippingFeeTest.php
.......                                                             7 / 7 (100%)

Shipping Fee (Tests\ShippingFee)
 ✔ Shipping fee with data set "đơn nhỏ trả phí"
 ✔ Shipping fee with data set "ngay dưới ngưỡng"
 ✔ Shipping fee with data set "đúng ngưỡng được miễn phí"
 ✔ Shipping fee with data set "trên ngưỡng"
 ✔ Discount boundaries with data set #0
 ✔ Discount boundaries with data set #1
 ✔ Discount boundaries with data set #2

OK (7 tests, 7 assertions)
```

Đặt **key là chuỗi mô tả** cho từng bộ: khi fail, PHPUnit in tên bộ, đọc là biết ca nào hỏng. Ví dụ
sửa ca cuối thành `[800_000, 1]`:

```
1) Tests\ShippingFeeTest::testShippingFee@trên ngưỡng with data (800000, 1)
Failed asserting that 0 is identical to 1.
```

Quy tắc của data provider (theo tài liệu PHPUnit 13): method phải `public static`, tên không bắt đầu
bằng `test`, trả về `iterable` mà mỗi phần tử là một mảng tham số. Data provider chạy **trước** mọi
`setUp()`, nên không dùng được `$this`. Chỉ nên chứa giá trị vô hướng, value object bất biến hoặc
stub; không tạo mock trong data provider.

### 3.6 Attribute thay cho docblock

Từ PHPUnit 10, thông tin cho test (*metadata*) được khai bằng *attribute* của PHP 8 (`#[Test]`,
`#[DataProvider]`, `#[CoversClass]`, `#[Group]`...). Code cũ dùng annotation trong docblock
(`/** @test */`, `@dataProvider`, `@covers`).

⚠️ PHPUnit 12 **xoá hẳn** hỗ trợ metadata trong docblock. Nâng từ 11 lên 12 mà không đổi code test:

- Method `/** @test */ public function it_works()` **lặng lẽ biến mất** khỏi lượt chạy: tên không bắt
  đầu bằng `test` và docblock không còn được đọc. Không có lỗi nào, chỉ là số test giảm.
- Method `/** @dataProvider cases */ public function testWithProvider(int $a, int $b)` được chạy
  **không có tham số** và báo lỗi `ArgumentCountError: Too few arguments to function ...` (đã chạy
  thử trên PHPUnit 13.4).

Rector có sẵn bộ quy tắc `PHPUnitSetList::ANNOTATIONS_TO_ATTRIBUTES` chuyển annotation sang attribute
tự động (gói `rector/rector` đã kèm các quy tắc cho PHPUnit; xem mục 7). Sau khi nâng cấp, so số test
trước và sau để chắc không có test nào biến mất.

### 3.7 Warning trong lúc test

Quay lại lỗi ở mục 1.3, lần này viết thành class trong `src/Greeter.php`:

```php
<?php
declare(strict_types=1);

namespace App;

use stdClass;

final class Greeter
{
    /** @param array<int, string> $users */
    public function __construct(private array $users) {}

    public function greet(int $id): string
    {
        $user = $this->find($id);
        return 'Xin chào ' . $user->name;      // dòng 16: quên xử lý null
    }

    private function find(int $id): ?stdClass
    {
        if (!isset($this->users[$id])) {
            return null;
        }
        $u = new stdClass();
        $u->name = $this->users[$id];
        return $u;
    }
}
```

Và test. Test thứ hai có **assertion đúng** với output thực tế (`'Xin chào '`), tức người viết test
vô tình "chốt" luôn hành vi sai. Test thứ ba cố ý ném exception để thấy ký tự `E`:

```php
<?php
declare(strict_types=1);

namespace Tests;

use App\Greeter;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

#[CoversClass(Greeter::class)]
final class GreeterTest extends TestCase
{
    public function testGreetsKnownUser(): void
    {
        $this->assertSame('Xin chào An', (new Greeter([1 => 'An']))->greet(1));
    }

    public function testUnknownUser(): void
    {
        $this->assertSame('Xin chào ', (new Greeter([1 => 'An']))->greet(2));
    }

    public function testThrowsUnexpected(): void
    {
        throw new \RuntimeException('bất ngờ');
    }
}
```

```
.WE                                                                 3 / 3 (100%)

There was 1 error:

1) Tests\GreeterTest::testThrowsUnexpected
RuntimeException: bất ngờ
...

1 test triggered 1 PHP warning:

1) /app/src/Greeter.php:16
Attempt to read property "name" on null

Triggered by:

* Tests\GreeterTest::testUnknownUser
  /app/tests/GreeterTest.php:18

ERRORS!
Tests: 3, Assertions: 2, Errors: 1, Warnings: 1.
```

(Output thật của PHPUnit 13.4 với `phpunit.xml` ở mục 3.1, rút gọn đường dẫn. Chạy lại lần nữa, dòng
tiến trình đổi thành `E.W`: `executionOrder="defects"` đưa test vừa lỗi lên chạy trước.)

PHPUnit gắn một *error handler* bắt các `E_WARNING`, `E_NOTICE`, `E_DEPRECATED` phát ra trong lúc test
và báo cáo chúng như những "vấn đề" (*issue*). Điều quan trọng: **mặc định** các issue này **không làm
lượt chạy thất bại**; PHPUnit in `OK, but there were issues!` và exit code vẫn là 0. Muốn chúng chặn CI
thì bật `failOnWarning`, `failOnNotice`, `failOnDeprecation` trong `phpunit.xml` (hoặc
`--fail-on-warning`...). Cấu hình do `--generate-configuration` tạo đã bật `failOnWarning`.

Exit code của PHPUnit: `0` khi mọi test đạt, `1` khi có test fail, `2` khi có test error.

Để ý thêm: `testUnknownUser` **đạt**, dù hàm `greet()` sai. Test chỉ tốt bằng kỳ vọng mà người viết đặt
vào nó; ở đây người viết đã chép lại output sai làm kỳ vọng. Đó là lý do cần thêm phân tích tĩnh
(mục 6, bắt lỗi này mà không cần ai viết test) và cách đo chất lượng test (mục 10).

## 4. Pest

### 4.1 Pest là gì

*Pest* (tác giả Nuno Maduro) là một framework test PHP **chạy trên nền PHPUnit**: Pest dùng bộ chạy,
assertion, cấu hình `phpunit.xml` của PHPUnit, nhưng cho bạn viết test bằng **hàm và closure** thay vì
class và method. Mục tiêu là test ngắn, đọc như câu văn.

| Bản Pest | PHP tối thiểu | Nền | Phát hành |
|---|---|---|---|
| Pest 5 | 8.4 | PHPUnit 13 | 28/07/2026 |
| Pest 4 | 8.3 | PHPUnit 12 | 21/08/2025 |
| Pest 3 | 8.2 | PHPUnit 11 | 09/09/2024 |

(Nguồn: trang *Support Policy* của Pest và `composer.json` của từng bản.) Khi tạo ứng dụng Laravel mới
bằng `laravel new`, trình cài đặt hỏi chọn Pest hay PHPUnit (mặc định Pest); các ví dụ test trong tài
liệu Laravel có cả hai phiên bản.

Cài vào một project đang dùng PHPUnit (theo tài liệu Pest):

```bash
composer remove phpunit/phpunit
composer require pestphp/pest --dev --with-all-dependencies
vendor/bin/pest --init        # tạo tests/Pest.php
vendor/bin/pest               # chạy test
```

Pest chạy được cả test class kiểu PHPUnit có sẵn, nên có thể chuyển dần. Plugin `pestphp/pest-plugin-drift`
(`vendor/bin/pest --drift`) tự chuyển test PHPUnit sang cú pháp Pest.

### 4.2 Cú pháp cơ bản

Cùng các test ở mục 3.2 và 3.5, viết bằng Pest (file `tests/PriceCalculatorTest.php`):

```php
<?php
declare(strict_types=1);

use App\PriceCalculator;

covers(PriceCalculator::class);           // tương đương #[CoversClass]

beforeEach(function (): void {            // tương đương setUp()
    $this->calc = new PriceCalculator();
});

it('applies ten percent discount', function (): void {
    expect($this->calc->applyDiscount(100_000, 10))->toBe(90_000);
});

test('rounds down to whole dong', function (): void {
    expect($this->calc->applyDiscount(999, 33))->toBe(669);
});

it('rejects negative percent', function (): void {
    $this->calc->applyDiscount(100_000, -5);
})->throws(InvalidArgumentException::class, 'percent phải nằm trong 0..100');

it('charges shipping by order total', function (int $total, int $fee): void {
    expect($this->calc->shippingFee($total))->toBe($fee);
})->with([
    'đơn nhỏ trả phí'           => [100_000, 30_000],
    'ngay dưới ngưỡng'          => [499_999, 30_000],
    'đúng ngưỡng được miễn phí' => [500_000, 0],
]);
```

Output dạng (output minh hoạ theo định dạng trong tài liệu Pest, chưa chạy trên máy viết sách):

```
   PASS  Tests\PriceCalculatorTest
  ✓ it applies ten percent discount
  ✓ rounds down to whole dong
  ✓ it rejects negative percent
  ✓ it charges shipping by order total with data set "đơn nhỏ trả phí"
  ✓ it charges shipping by order total with data set "ngay dưới ngưỡng"
  ✓ it charges shipping by order total with data set "đúng ngưỡng được miễn phí"

  Tests:    6 passed (6 assertions)
```

Ánh xạ khái niệm:

| PHPUnit | Pest |
|---|---|
| `final class XTest extends TestCase` | Không cần class; mỗi file là một nhóm test |
| `public function testFoo(): void { ... }` | `test('foo', function () { ... })` hoặc `it('does foo', ...)` (tên in ra có tiền tố "it") |
| `$this->assertSame(3, $x)` | `expect($x)->toBe(3)` (vẫn dùng được `$this->assertSame`) |
| `assertEquals` | `toEqual` |
| `setUp()`, `tearDown()` | `beforeEach()`, `afterEach()` |
| `#[DataProvider]` | `->with([...])` (Pest gọi là *dataset*) |
| `expectException()` | `->throws(Foo::class, 'message')` hoặc `expect(fn () => ...)->toThrow(...)` |
| `#[CoversClass]` | `covers(...)` |
| Nhóm test theo class | `describe('...', function () { ... })` lồng nhau được |

Một số điểm cần biết:

- `$this` bên trong closure là object test case (mặc định `PHPUnit\Framework\TestCase`). File
  `tests/Pest.php` cấu hình class nền cho từng thư mục, ví dụ Laravel có
  `pest()->extend(Tests\TestCase::class)->in('Feature');` để test trong `Feature` có `$this->get()`,
  `$this->actingAs()`...
- `expect()` nối chuỗi được: `expect($x)->toBeInt()->toBe(3)`. Viết thẳng tên property hoặc method
  sau `expect()` để kiểm giá trị đó (*higher order expectation*):
  `expect($user)->name->toBe('An')->email->toBe('an@example.com')`. Phủ định bằng `->not`:
  `expect($list)->not->toBeEmpty()`.
- `toBe()` so bằng `===` (với object là cùng một object), `toEqual()` so lỏng như `assertEquals`. Cùng
  lời khuyên như PHPUnit: mặc định dùng `toBe()`.

### 4.3 Architecture test

Pest có thêm loại test mà PHPUnit không có sẵn: *architecture test* (kiểm tra kiến trúc). Thay vì chạy
code, nó đọc code và kiểm các **quy tắc cấu trúc** mà team đặt ra:

```php
arch()
    ->expect('App')
    ->toUseStrictTypes()                     // mọi file trong App phải declare(strict_types=1)
    ->not->toUse(['die', 'dd', 'dump']);     // không để sót hàm debug

arch()
    ->expect('App\Models')
    ->toOnlyBeUsedIn('App\Repositories');    // chỉ tầng Repository được đụng tới Model

arch()->preset()->php();                     // bộ quy tắc chung cho mọi project PHP
arch()->preset()->security()->ignoring('md5');
```

(Ví dụ lấy từ tài liệu Pest.) Đây là cách biến các quy ước hay bị quên trong review ("controller không
gọi thẳng DB", "không commit `dd()`") thành kiểm tra tự động.

### 4.4 Chọn PHPUnit hay Pest

| Tiêu chí | PHPUnit | Pest |
|---|---|---|
| Nền tảng | Là nền | Chạy trên PHPUnit |
| Cú pháp | Class, method, attribute | Hàm, closure, `expect()` |
| Độ phổ biến ngoài Laravel | Gần như mọi thư viện và framework PHP | Chủ yếu trong hệ Laravel |
| Tính năng tích hợp sẵn | Đầy đủ phần lõi | Thêm architecture test, `--mutate`, `--parallel`, chia shard cho CI, browser test (plugin) |
| Hỗ trợ của IDE và phân tích tĩnh | Tốt sẵn (class, kiểu rõ ràng) | Cần plugin để IDE và PHPStan hiểu `$this` trong closure (Pest 5 có plugin PHPStan chính chủ) |

Hai lựa chọn đều tốt; khác biệt chủ yếu là sở thích cú pháp. Vì Pest dựng trên PHPUnit, hiểu PHPUnit
là hiểu được cái lõi của cả hai. Phần còn lại của chương dùng PHPUnit cho ví dụ chạy được.

## 5. Test double

### 5.1 Vì sao cần đồ giả

Xét một service thanh toán đơn hàng. Để làm việc, nó cần bốn thứ bên ngoài:

```
                      ┌──────────────────┐
                      │ CheckoutService  │  ← thứ ta muốn test (SUT)
                      └──┬───┬───┬───┬───┘
          ┌──────────────┘   │   │   └───────────────┐
          ▼                  ▼   ▼                   ▼
   PaymentGateway     OrderRepository   Mailer        Clock
   (gọi API cổng      (MySQL)           (gửi email    (giờ hiện tại)
    thanh toán thật,                     thật)
    trừ tiền thật)
```

Dùng đồ thật trong test thì: mỗi lần chạy trừ tiền thẻ thật, cần mạng, chậm, gửi email thật tới
khách, kết quả phụ thuộc giờ chạy. Và không có cách nào bắt cổng thanh toán "từ chối thẻ" theo ý mình
để test nhánh lỗi.

*Test double* (đồ thế thân, như diễn viên đóng thế trong phim) là tên chung cho mọi object giả thay cho
một phụ thuộc thật trong test. Thuật ngữ do Gerard Meszaros đưa ra trong sách *xUnit Test Patterns*;
tài liệu PHPUnit dùng đúng định nghĩa đó. Điều kiện để thay được: SUT phải **nhận** phụ thuộc từ bên
ngoài (qua constructor) và phụ thuộc vào **interface** chứ không tự `new` class cụ thể bên trong (mục 5.7).

### 5.2 Năm loại test double

| Loại | Làm gì | Ví dụ |
|---|---|---|
| *Dummy* | Chỉ để đủ tham số, không bao giờ được dùng | Một logger truyền vào cho đủ constructor, nhánh đang test không ghi log |
| *Stub* | Trả về giá trị định sẵn khi được gọi | Cổng thanh toán luôn "chấp nhận"; đồng hồ luôn trả 09:00 ngày 03/10/2026 |
| *Fake* | Một cài đặt thật nhưng đơn giản hoá, không dùng được cho production | Repository lưu trong mảng thay vì MySQL |
| *Spy* | Ghi lại nó được gọi thế nào, để test kiểm **sau** khi chạy | Mailer giả ghi lại danh sách email "đã gửi" |
| *Mock* | Được lập trình **trước** kỳ vọng về cách gọi; tự làm test fail nếu bị gọi sai | "Phải gọi `send()` đúng một lần với `an@example.com`" |

Tài liệu PHPUnit tóm gọn sự khác nhau cốt lõi: stub kiểm soát **đầu vào gián tiếp** (*indirect input*,
dữ liệu chảy từ phụ thuộc vào SUT), còn mock là điểm quan sát **đầu ra gián tiếp** (*indirect output*,
các lời gọi từ SUT ra phụ thuộc).

Viết tay tất cả bằng PHP thuần, không cần thư viện nào. Đây là cách dễ hiểu nhất, và trong thực tế fake
viết tay thường **tốt hơn** mock do thư viện sinh ra (mục 5.6):

```php
<?php
declare(strict_types=1);

// ===== Code thật (SUT và các interface nó phụ thuộc) =====
final readonly class PaymentResult
{
    public function __construct(public bool $success, public string $transactionId = '') {}
}

interface PaymentGateway
{
    public function charge(string $customerId, int $amount): PaymentResult;
}

interface Mailer
{
    public function send(string $to, string $subject): void;
}

interface Clock
{
    public function now(): DateTimeImmutable;
}

final class Order
{
    public string $status = 'pending';
    public ?DateTimeImmutable $paidAt = null;

    public function __construct(
        public readonly int $id,
        public readonly string $customerId,
        public readonly string $email,
        public readonly int $amount,
    ) {}
}

interface OrderRepository
{
    public function find(int $id): ?Order;
    public function save(Order $order): void;
}

final class CheckoutService
{
    public function __construct(
        private PaymentGateway $gateway,
        private OrderRepository $orders,
        private Mailer $mailer,
        private Clock $clock,
    ) {}

    public function pay(int $orderId): bool
    {
        $order = $this->orders->find($orderId)
            ?? throw new DomainException("Không có đơn $orderId");

        if ($order->status === 'paid') {
            return true;                       // đã trả rồi: không trừ tiền lần nữa
        }

        $result = $this->gateway->charge($order->customerId, $order->amount);
        if (!$result->success) {
            $order->status = 'failed';
            $this->orders->save($order);
            return false;
        }

        $order->status = 'paid';
        $order->paidAt = $this->clock->now();
        $this->orders->save($order);
        $this->mailer->send($order->email, "Đơn #{$order->id} đã thanh toán");
        return true;
    }
}

// ===== Test double viết tay =====
final class StubGateway implements PaymentGateway           // STUB: trả kết quả định sẵn
{
    public int $calls = 0;                                   // đếm số lần gọi (biến nó thành spy luôn)

    public function __construct(private bool $approve) {}

    public function charge(string $customerId, int $amount): PaymentResult
    {
        $this->calls++;
        return new PaymentResult($this->approve, $this->approve ? 'tx_1' : '');
    }
}

final class InMemoryOrderRepository implements OrderRepository  // FAKE: cài đặt thật nhưng đơn giản
{
    /** @var array<int, Order> */
    private array $rows = [];

    public function find(int $id): ?Order
    {
        return $this->rows[$id] ?? null;
    }

    public function save(Order $order): void
    {
        $this->rows[$order->id] = $order;
    }
}

final class SpyMailer implements Mailer                      // SPY: ghi lại cách được gọi
{
    /** @var list<array{string, string}> */
    public array $sent = [];

    public function send(string $to, string $subject): void
    {
        $this->sent[] = [$to, $subject];
    }
}

final class FixedClock implements Clock                     // STUB cho thời gian
{
    public function __construct(private DateTimeImmutable $at) {}

    public function now(): DateTimeImmutable
    {
        return $this->at;
    }
}

function check(string $name, bool $ok): void
{
    echo ($ok ? 'PASS ' : 'FAIL '), $name, PHP_EOL;
}

// ===== Test 1: thanh toán thành công =====
$repo = new InMemoryOrderRepository();
$repo->save(new Order(1, 'cus_9', 'an@example.com', 250_000));
$mailer = new SpyMailer();
$clock = new FixedClock(new DateTimeImmutable('2026-10-03 09:00:00'));
$service = new CheckoutService(new StubGateway(approve: true), $repo, $mailer, $clock);

$ok = $service->pay(1);

check('trả về true', $ok === true);
check('đơn chuyển sang paid', $repo->find(1)?->status === 'paid');
check('ghi thời điểm trả', $repo->find(1)?->paidAt?->format('Y-m-d H:i') === '2026-10-03 09:00');
check('gửi đúng một email', $mailer->sent === [['an@example.com', 'Đơn #1 đã thanh toán']]);

// ===== Test 2: thẻ bị từ chối =====
$repo = new InMemoryOrderRepository();
$repo->save(new Order(2, 'cus_9', 'an@example.com', 250_000));
$mailer = new SpyMailer();
$service = new CheckoutService(new StubGateway(approve: false), $repo, $mailer, $clock);

check('bị từ chối trả về false', $service->pay(2) === false);
check('đơn chuyển sang failed', $repo->find(2)?->status === 'failed');
check('không gửi email', $mailer->sent === []);

// ===== Test 3: trả lại đơn đã paid thì không trừ tiền lần hai =====
$repo = new InMemoryOrderRepository();
$repo->save(new Order(3, 'cus_9', 'an@example.com', 250_000));
$gateway = new StubGateway(approve: true);
$service = new CheckoutService($gateway, $repo, new SpyMailer(), $clock);
$service->pay(3);
$service->pay(3);

check('chỉ gọi cổng thanh toán một lần', $gateway->calls === 1);

// in ra:
// PASS trả về true
// PASS đơn chuyển sang paid
// PASS ghi thời điểm trả
// PASS gửi đúng một email
// PASS bị từ chối trả về false
// PASS đơn chuyển sang failed
// PASS không gửi email
// PASS chỉ gọi cổng thanh toán một lần
```

Để ý: với `FixedClock`, test kiểm được chính xác thời điểm `paidAt` mà không phụ thuộc giờ chạy. Đó là
lợi ích lớn nhất của việc đưa thời gian vào qua interface.

### 5.3 Stub trong PHPUnit

Viết tay mỗi interface một class sẽ mỏi khi interface có nhiều method. PHPUnit sinh test double tự
động lúc chạy (tạo một class con hoặc class cài interface, trong bộ nhớ):

```php
$gateway = $this->createStub(PaymentGateway::class);
$gateway->method('charge')->willReturn(new PaymentResult(true, 'tx_1'));
```

- `createStub(X::class)`: tạo stub. Mọi method chưa cấu hình trả về giá trị mặc định khớp kiểu trả về
  khai báo (`0` cho `int`, `''` cho `string`, một test double khác cho kiểu object...).
- `->method('ten')->willReturn($v)`: cấu hình giá trị trả về. Các biến thể: `willThrowException($e)`
  (để test nhánh lỗi), `willReturnMap([...])` (trả theo tham số), `willReturnCallback(fn (...) => ...)`,
  `willReturnSelf()`, `willReturnArgument(0)`.
- `createConfiguredStub(X::class, ['methodA' => 1, 'methodB' => 'x'])`: viết gọn cho ca đơn giản.

### 5.4 Mock trong PHPUnit

Cùng service, viết bằng PHPUnit. Fake repository vẫn viết tay (đặt trong `tests/Checkout/`), clock và
gateway dùng stub, mailer dùng mock:

```php
<?php
declare(strict_types=1);

namespace Tests\Checkout;

use App\Checkout\CheckoutService;
use App\Checkout\Clock;
use App\Checkout\Mailer;
use App\Checkout\Order;
use App\Checkout\PaymentGateway;
use App\Checkout\PaymentResult;
use DateTimeImmutable;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\TestCase;

#[CoversClass(CheckoutService::class)]
final class CheckoutServiceTest extends TestCase
{
    private InMemoryOrderRepository $orders;
    private Clock $clock;

    protected function setUp(): void
    {
        $this->orders = new InMemoryOrderRepository();                 // fake viết tay
        $this->orders->save(new Order(1, 'cus_9', 'an@example.com', 250_000));

        $this->clock = $this->createStub(Clock::class);                // stub
        $this->clock->method('now')->willReturn(new DateTimeImmutable('2026-10-03 09:00:00'));
    }

    public function testPaidOrderSendsReceipt(): void
    {
        $gateway = $this->createStub(PaymentGateway::class);           // stub: chỉ cần nó trả kết quả
        $gateway->method('charge')->willReturn(new PaymentResult(true, 'tx_1'));

        $mailer = $this->createMock(Mailer::class);                    // mock: cần kiểm nó được gọi thế nào
        $mailer->expects($this->once())
            ->method('send')
            ->with('an@example.com', 'Đơn #1 đã thanh toán');

        $service = new CheckoutService($gateway, $this->orders, $mailer, $this->clock);

        $this->assertTrue($service->pay(1));
        $this->assertSame('paid', $this->orders->find(1)?->status);
    }

    public function testDeclinedCardSendsNothing(): void
    {
        $gateway = $this->createStub(PaymentGateway::class);
        $gateway->method('charge')->willReturn(new PaymentResult(false));

        $mailer = $this->createMock(Mailer::class);
        $mailer->expects($this->never())->method('send');

        $service = new CheckoutService($gateway, $this->orders, $mailer, $this->clock);

        $this->assertFalse($service->pay(1));
        $this->assertSame('failed', $this->orders->find(1)?->status);
    }

    public function testPayingTwiceChargesOnce(): void
    {
        $gateway = $this->createMock(PaymentGateway::class);
        $gateway->expects($this->once())
            ->method('charge')
            ->with('cus_9', 250_000)
            ->willReturn(new PaymentResult(true, 'tx_1'));

        $service = new CheckoutService($gateway, $this->orders, $this->createStub(Mailer::class), $this->clock);

        $service->pay(1);
        $service->pay(1);
    }
}
```

```
$ vendor/bin/phpunit --testdox tests/Checkout
...                                                                 3 / 3 (100%)

Checkout Service (Tests\Checkout\CheckoutService)
 ✔ Paid order sends receipt
 ✔ Declined card sends nothing
 ✔ Paying twice charges once

OK (3 tests, 11 assertions)
```

(Chạy thật trên PHPUnit 13.4. Số assertion là 11 vì mỗi kỳ vọng của mock cũng được đếm.)

Cách mock hoạt động: `expects($this->once())` ghi kỳ vọng "method này phải được gọi đúng 1 lần";
`with(...)` ghi kỳ vọng về tham số. Lời gọi sai tham số làm test fail **ngay lúc gọi**; còn số lần gọi
được PHPUnit kiểm **khi test method kết thúc**. Test cuối không có `assert` nào: kỳ vọng của mock chính
là phép kiểm. Các bộ đếm: `once()`, `exactly(n)`, `never()`, `atLeastOnce()`, `atLeast(n)`, `atMost(n)`
(tài liệu PHPUnit khuyên tránh ba cái sau vì làm ý định của test mờ đi).

Khi kỳ vọng không được đáp ứng (output thật, PHPUnit 13.4):

```
1) Tests\MockFailTest::testNeverCalled
App\Checkout\Mailer::send() was expected to be invoked once but was never invoked.

2) Tests\MockFailTest::testWrongArgs
Expectation for App\Checkout\Mailer::send() failed.
Parameter $to for invocation App\Checkout\Mailer::send('binh@example.com', 'Xin chào'): void does not match expected value.
Failed asserting that two strings are equal.
--- Expected
+++ Actual
@@ @@
-'an@example.com'
+'binh@example.com'
```

Ba điều PHPUnit hiện đại ép bạn phân biệt stub và mock:

- Tạo bằng `createMock()` mà không đặt kỳ vọng nào thì PHPUnit (từ bản 12.5) phát *PHPUnit notice*:
  `No expectations were configured for the mock object for App\Checkout\Mailer. Consider refactoring
  your test code to use a test stub instead.` Cần object chỉ để trả giá trị thì dùng `createStub()`.
- Từ PHPUnit 12, gọi `expects()` trên một stub (tạo bằng `createStub()`) không còn được hỗ trợ.
- `expects($this->any())` bị deprecated ở PHPUnit 13 và sẽ bị xoá ở 14, vì "mock nhưng không quan tâm
  có được gọi hay không" chính là định nghĩa của stub.

⚠️ Không double được class `final`, enum, method `final`/`private`/`static`. Thử
`$this->createStub(PriceCalculator::class)` với class `final` sẽ báo lỗi:

```
PHPUnit\Framework\MockObject\Generator\ClassIsFinalException: Class "App\PriceCalculator" is declared "final" and cannot be doubled
```

Đây không phải lý do để bỏ `final`. Cách đúng: SUT phụ thuộc vào **interface** (như `PaymentGateway`),
và double interface. Còn class `final` thuần tính toán như `PriceCalculator` thì không cần double: dùng
object thật, nó nhanh và không có side effect.

### 5.5 Mockery và các fake của Laravel

*Mockery* là thư viện mock độc lập, cú pháp khác PHPUnit nhưng cùng ý tưởng; Laravel cài sẵn nó trong
`require-dev`:

```php
$gateway = Mockery::mock(PaymentGateway::class);
$gateway->shouldReceive('charge')
    ->once()
    ->with('cus_9', 250_000)
    ->andReturn(new PaymentResult(true, 'tx_1'));
```

Kỳ vọng của Mockery được kiểm khi gọi `Mockery::close()` cuối test; `TestCase` của Laravel tự làm việc
này. Laravel còn có sẵn các *fake* cho dịch vụ của framework (`Mail::fake()`, `Queue::fake()`,
`Http::fake()`, `Event::fake()`, `Storage::fake()`...), thực chất là spy: ghi lại mọi thứ rồi cho bạn
assert sau (`Mail::assertSent(...)`). Chúng được dạy ở [Chương 30](30-laravel-testing-octane-deploy.md).

### 5.6 Khi nào dùng đồ giả, loại nào

Quy tắc thực dụng:

- **Stub cho truy vấn, mock/spy cho mệnh lệnh.** Method chỉ trả dữ liệu (tỉ giá, giờ hiện tại, tìm
  user) thì stub; kiểm số lần gọi một truy vấn là gắn test vào cách viết bên trong. Method gây tác động
  ra ngoài (trừ tiền, gửi email, đẩy job) thì cần kiểm nó có xảy ra, với tham số đúng: mock hoặc spy.
- **Chỉ thay đồ giả ở biên hệ thống**: API bên ngoài, email, SMS, thời gian, số ngẫu nhiên. Các class
  thuần của chính bạn thì dùng đồ thật (test sociable, mục 2.4).
- **Đừng mock thứ không phải của mình** (*don't mock what you don't own*). Không mock thẳng SDK của
  Stripe hay `GuzzleHttp\Client`: API của chúng phức tạp, mock sai cách chúng thật sự chạy thì test xanh
  mà production đỏ. Bọc thư viện ngoài bằng interface của mình (`PaymentGateway`), mock interface đó,
  rồi test class cài đặt thật (adapter) bằng integration test riêng.
- **Database**: mock repository không bao giờ bắt được câu SQL sai. Logic nghiệp vụ test với fake
  repository; bản thân repository test với database thật (integration test).

⚠️ Dấu hiệu *over-mocking* (mock quá tay):

- Một test có năm, sáu `expects()`, lặp lại gần như từng dòng của code được test.
- Refactor không đổi hành vi mà hàng loạt test đỏ.
- Test xanh trong khi tính năng hỏng, vì mock trả đúng thứ người viết **nghĩ** là đúng.

### 5.7 Thiết kế để test được

Code khó test thường là code có thiết kế khó thay đổi. Những thứ làm code khó test:

| Thứ gây khó | Vì sao | Cách sửa |
|---|---|---|
| `new` class phụ thuộc ngay bên trong method | Test không thay được bằng đồ giả | Nhận qua constructor (*dependency injection*), kiểu là interface |
| Gọi `time()`, `date()`, `new DateTimeImmutable()` trong logic | Kết quả đổi theo giờ chạy; không test được "cuối tháng", "token hết hạn đúng giây" | Nhận một clock. PSR-20 định nghĩa sẵn `Psr\Clock\ClockInterface` với một method `now(): DateTimeImmutable` |
| `random_int()`, `uniqid()` trong logic | Không lặp lại được | Nhận một generator qua interface; PHP 8.2+ có `Random\Randomizer` nhận engine có seed cố định |
| Gọi static, biến toàn cục, singleton | Không thay được, trạng thái dính giữa các test | Đưa vào qua constructor |
| Method làm quá nhiều việc (đọc DB, tính, gửi mail) | Phải giả lập mọi thứ cho một phép tính | Tách phần tính toán thuần ra hàm riêng, test không cần double |

Mẫu cuối là quan trọng nhất: tách **logic thuần** (nhận input, trả output, không I/O) khỏi **phần nối với
thế giới bên ngoài**. Phần thuần test bằng unit test nhanh và không cần double; phần nối test bằng ít
integration test. Ví dụ `CheckoutService` ở trên có thể tách quy tắc "đơn nào được thanh toán" thành
một method thuần trên `Order`.

## 6. Phân tích tĩnh

### 6.1 Phân tích tĩnh là gì

*Phân tích tĩnh* (static analysis) là đọc mã nguồn **mà không chạy nó** để tìm lỗi. Công cụ làm việc
giống một trình biên dịch: phân tích cú pháp mỗi file thành *AST* (abstract syntax tree, cây cú pháp),
đọc kiểu khai báo ở code và ở PHPDoc, suy luận kiểu của từng biểu thức theo luồng code, rồi áp các quy
tắc kiểm tra.

Mức thấp nhất mà PHP có sẵn là `php -l file.php` (*lint*): chỉ kiểm **cú pháp** (thiếu dấu `;`, ngoặc
không đóng). Nó không biết method có tồn tại hay không, kiểu có đúng hay không. Các công cụ dưới đây
làm phần còn lại.

| Công cụ | Ai làm | Điểm mạnh |
|---|---|---|
| PHPStan | Ondřej Mirtes | Phổ biến nhất; level 0 tới 10; hệ sinh thái extension lớn (Larastan, Doctrine, PHPUnit...) |
| Psalm | Vimeo (khởi đầu), nay cộng đồng | Tương đương về kiểm kiểu; mạnh về *taint analysis* (mục 6.8) |
| Larastan | Cộng đồng Laravel | Extension của PHPStan, dạy PHPStan hiểu "phép màu" của Laravel |

Cách PHPStan suy luận kiểu theo luồng code (*type narrowing*, thu hẹp kiểu) là thứ làm nó mạnh:

```php
$user = findUser($id);          // PHPStan biết: User|null
if ($user === null) {
    return 'Không tìm thấy';
}
return $user->name;             // tới đây PHPStan biết: User (nhánh null đã return)
```

PHPStan hiểu các phép kiểm `=== null`, `instanceof`, `is_int()`, `is_array()`, `isset()`, `assert()`
và dùng chúng để thu hẹp kiểu ở các dòng sau.

### 6.2 Cài và chạy PHPStan

Chạy trong thư mục project:

```bash
composer require --dev phpstan/phpstan
vendor/bin/phpstan analyse --level 5 src tests
```

Hoặc khai trong file cấu hình `phpstan.neon` ở thư mục gốc (định dạng *NEON*, gần giống YAML; PHPStan tự
đọc file này nếu có):

```neon
parameters:
    level: 6
    paths:
        - src
        - tests
```

rồi chỉ cần `vendor/bin/phpstan analyse`. PHPStan dùng autoloader của Composer để đọc class của thư
viện trong `vendor/`. Bản mới nhất lúc viết là 2.2.

Chạy trên ví dụ `greet()` ở mục 1.3 (output thật của PHPStan 2.2.16):

```
$ vendor/bin/phpstan analyse --level 8 greet.php
 ------ -------------------------------------------- 
  Line   greet.php                                   
 ------ -------------------------------------------- 
  16     Cannot access property $name on User|null.  
         🪪  property.nonObject                      
 ------ -------------------------------------------- 

 [ERROR] Found 1 error
```

Không ai phải viết ca `id = 2`. Dòng `🪪 property.nonObject` là *error identifier*: mã định danh của
loại lỗi, dùng khi muốn bỏ qua có chọn lọc (mục 6.6) và tra tài liệu tại
`phpstan.org/error-identifiers/<identifier>`. Exit code khác 0 khi có lỗi, nên CI chặn được.

⚠️ PHPStan cần bộ nhớ lớn trên codebase lớn. Gặp `Allowed memory size exhausted` thì thêm
`--memory-limit=1G` (hoặc lớn hơn).

### 6.3 Rule level

PHPStan có 11 *rule level*, từ 0 (lỏng nhất) tới 10 (chặt nhất); mặc định là 0 khi không khai. Level
**cộng dồn**: level 5 gồm mọi kiểm tra của 0 tới 4. Theo tài liệu PHPStan:

| Level | Thêm kiểm tra gì |
|---|---|
| 0 | Kiểm tra cơ bản: class, hàm không tồn tại; method không tồn tại khi gọi trên `$this`; sai số tham số khi gọi các hàm, method đó (trên thực tế level 0 chỉ báo **thiếu** tham số, xem bảng kết quả dưới); biến chắc chắn chưa định nghĩa |
| 1 | Biến *có thể* chưa định nghĩa; method và property "magic" không rõ trên class có `__call`, `__get`; truyền **thừa** tham số |
| 2 | Method không tồn tại trên **mọi** biểu thức (không chỉ `$this`); kiểm PHPDoc hợp lệ |
| 3 | Kiểu trả về; kiểu của giá trị gán vào property |
| 4 | Code chết cơ bản: `instanceof` luôn sai, nhánh `else` không bao giờ chạy, code sau `return` |
| 5 | Kiểu của tham số truyền vào hàm và method |
| 6 | Báo thiếu khai báo kiểu (kể cả thiếu kiểu phần tử của `array`) |
| 7 | Union type sai một phần: gọi method chỉ có trên một số kiểu trong union |
| 8 | Gọi method, truy cập property trên kiểu *nullable* (có thể `null`) |
| 9 | Chặt với `mixed` **khai báo rõ**: chỉ được truyền nó cho chỗ nhận `mixed` |
| 10 | (Mới từ PHPStan 2.0) Chặt cả với `mixed` **ngầm**, tức chỗ thiếu khai báo kiểu |

`--level max` là bí danh cho level cao nhất của bản đang cài (cẩn thận: nâng PHPStan lên bản có level
mới thì `max` tự chặt hơn).

Thử trên một file có nhiều loại lỗi:

```php
<?php
declare(strict_types=1);

final class Invoice
{
    public function __construct(public int $total) {}
}

function loadInvoice(int $id): Invoice
{
    return new Invoice($id * 1000);
}

function totalOf(array $ids)                 // thiếu kiểu phần tử và kiểu trả về
{
    $sum = 0;
    foreach ($ids as $id) {
        $sum += loadInvoice($id)->total;
    }
    return $sum;
}

function report(int $id): string
{
    $invoice = loadInvoice($id);
    return 'Tổng: ' . $invoice->totl;       // gõ sai tên property
}

function shout(string $s): string
{
    return strtoupper($s);
}

echo shout(42);                              // sai kiểu tham số
echo report(1, 2);                           // thừa tham số
```

Kết quả chạy thật với PHPStan 2.2.16 ở từng level:

| Level | Lỗi được báo (dòng: thông báo, identifier) |
|---|---|
| 0 | Không có lỗi |
| 1 | 35: `Function report invoked with 2 parameters, 1 required.` (`arguments.count`). Lỗi **thừa** tham số chỉ bị báo từ level 1 (cấu hình level 1 của PHPStan bật tuỳ chọn `checkExtraArguments`); lỗi **thiếu** tham số, ví dụ `report()`, thì level 0 đã báo |
| 2 | Thêm 26: `Access to an undefined property Invoice::$totl.` (`property.notFound`) |
| 5 | Thêm 34: `Parameter #1 $s of function shout expects string, int given.` (`argument.type`) |
| 6 | Thêm 14: `Function totalOf() has no return type specified.` (`missingType.return`) và `Function totalOf() has parameter $ids with no value type specified in iterable type array.` (`missingType.iterableValue`) |

Bài học: ở level thấp, rất nhiều lỗi thật lọt qua. Chạy PHP thật thì dòng 34 ném `TypeError` (vì có
`strict_types`), dòng 26 phát warning, nhưng chỉ khi dòng đó được chạy tới.

Level 9 và `mixed`: hàm như `json_decode()` trả về `mixed` (không biết là gì). Ở level 8 PHPStan cho qua
mọi thao tác trên `mixed`; level 9 thì không:

```php
<?php
declare(strict_types=1);

function isAdult(int $age): bool
{
    return $age >= 18;
}

function checkBad(string $json): bool
{
    $data = json_decode($json, true);       // json_decode trả về mixed
    return isAdult($data['age']);
    // level 9: Cannot access offset 'age' on mixed.
    // level 9: Parameter #1 $age of function isAdult expects int, mixed given.
}

function checkGood(string $json): bool
{
    $data = json_decode($json, true, flags: JSON_THROW_ON_ERROR);
    if (!is_array($data) || !is_int($data['age'] ?? null)) {
        throw new InvalidArgumentException('age phải là số nguyên');
    }
    return isAdult($data['age']);           // từ đây PHPStan biết là int: không lỗi
}
```

Cách sửa đúng là **kiểm tra lúc chạy** để thu hẹp kiểu (cũng là validate dữ liệu từ ngoài vào, điều
nên làm dù không có PHPStan), không phải ép kiểu `(int)` cho im lỗi. Trong Laravel, `$request->input()`
cũng trả `mixed`; dùng `$request->integer('age')`, `$request->string('name')` hoặc validate rồi đưa vào
một DTO có khai kiểu.

Chọn level nào: dự án mới nên bắt đầu ở level cao (8 trở lên) ngay từ đầu, vì sửa từng lỗi khi viết rẻ
hơn nhiều. Dự án cũ thì dùng baseline (mục 6.6) hoặc bắt đầu thấp rồi nâng dần.

### 6.4 Kiểu trong PHPDoc

Kiểu native của PHP (khai trong code) chưa đủ để mô tả nhiều thứ: `array` không nói phần tử là gì,
không có generics. PHPStan và Psalm đọc thêm kiểu trong PHPDoc (`@param`, `@return`, `@var`), với cú
pháp phong phú hơn. PHP bỏ qua các comment này lúc chạy; chúng chỉ phục vụ công cụ và IDE.

| Cú pháp | Nghĩa |
|---|---|
| `array<int, User>` | Mảng key `int`, value `User` |
| `list<string>` | Mảng key liên tục 0, 1, 2... (*list*), value `string` |
| `non-empty-list<int>` | Như trên, ít nhất một phần tử |
| `array{id: int, name: string, email?: string}` | *Array shape*: từng key có kiểu riêng; `?` là key tuỳ chọn |
| `int<1, 100>`, `positive-int`, `non-negative-int` | Số nguyên trong khoảng |
| `non-empty-string`, `numeric-string` | Chuỗi khác `''`; chuỗi dạng số |
| `class-string<Model>` | Chuỗi là tên một class con của `Model` |
| `'draft'\|'paid'` | *Literal type*: chỉ nhận đúng các giá trị này |

```php
/**
 * @param array{id: int, name: string, email?: string} $row
 */
function displayName(array $row): string
{
    return $row['name'] . ' #' . $row['id'];
}

echo displayName(['id' => 1, 'name' => 'An']);     // đúng
echo displayName(['id' => '1', 'name' => 'An']);   // PHPStan: Parameter #1 $row of function displayName expects
                                                   // array{id: int, name: string, email?: string},
                                                   // array{id: '1', name: 'An'} given.
```

Để ý PHP **không** báo lỗi dòng thứ hai lúc chạy: kiểu native chỉ là `array`. Chỉ PHPStan biết `id`
phải là `int`.

### 6.5 Generics qua PHPDoc

PHP không có *generics* (kiểu tham số hoá, như `List<User>` của Java) ở mức ngôn ngữ. PHPStan và Psalm
định nghĩa generics trong PHPDoc bằng `@template`:

```php
<?php
declare(strict_types=1);

/**
 * @template T
 */
final class TypedList
{
    /** @var list<T> */
    private array $items = [];

    /** @param T $item */
    public function add(mixed $item): void
    {
        $this->items[] = $item;
    }

    /** @return T|null */
    public function first(): mixed
    {
        return $this->items[0] ?? null;
    }
}

/** @var TypedList<DateTimeImmutable> $dates */
$dates = new TypedList();
$dates->add(new DateTimeImmutable('2026-10-03'));
$dates->add('2026-01-01');
// PHPStan: Parameter #1 $item of method TypedList<DateTimeImmutable>::add() expects DateTimeImmutable, string given.

\PHPStan\dumpType($dates->first());
// PHPStan: Dumped type: DateTimeImmutable|null
```

- `@template T` khai một *type variable*; `TypedList<DateTimeImmutable>` thay `T` bằng kiểu cụ thể.
- `@template T of object` đặt cận trên: `T` phải là object. Hay dùng kèm `class-string<T>`:
  `@param class-string<T> $class` và `@return T` cho hàm kiểu `make(User::class)` trả về `User`.
- Class con chỉ định kiểu cho cha bằng `@extends Collection<int, User>`, `@implements Repository<User>`.
- `\PHPStan\dumpType($x)` chỉ có nghĩa với PHPStan (in kiểu nó suy ra). Lúc chạy PHP thật, hàm này không
  tồn tại và gây lỗi; xoá trước khi commit.

Laravel dùng generics PHPDoc rất nhiều: `Collection<int, User>`, relationship `HasMany<Post, $this>`.
Nhờ đó IDE và PHPStan biết `$user->posts->first()` là `Post|null`.

### 6.6 Baseline và bỏ qua lỗi

Chạy PHPStan lần đầu ở level 6 trên một codebase cũ có thể ra hàng nghìn lỗi. Không ai dừng tính năng
để sửa hết. *Baseline* giải quyết việc này: ghi **toàn bộ lỗi hiện có** vào một file để tạm bỏ qua, từ
đó chỉ lỗi **mới** bị báo.

```bash
vendor/bin/phpstan analyse --generate-baseline      # tạo phpstan-baseline.neon
```

File baseline được tạo thật từ ví dụ ở mục 6.3 (level 6, rút gọn còn 2 mục):

```neon
parameters:
	ignoreErrors:
		-
			message: '#^Access to an undefined property Invoice\:\:\$totl\.$#'
			identifier: property.notFound
			count: 1
			path: src/levels.php

		-
			message: '#^Parameter \#1 \$s of function shout expects string, int given\.$#'
			identifier: argument.type
			count: 1
			path: src/levels.php
```

Thêm nó vào `phpstan.neon`:

```neon
includes:
    - phpstan-baseline.neon

parameters:
    level: 6
    paths:
        - src
```

Cách baseline so khớp:

- Mỗi mục gồm **nội dung lỗi + file + số lần** (`count`), không theo số dòng. Sửa code chỗ khác trong
  file không làm baseline lệch.
- Thêm một lỗi **cùng loại** vào cùng file thì số lần vượt `count`, và lỗi bị báo. Chạy thật sau khi
  thêm `echo shout(7);`:

  ```
  34     Ignored error pattern #^Parameter \#1 \$s of function shout expects
         string, int given\.$# (argument.type) in path .../src/levels.php
         is expected to occur 1 time, but occurred 2 times.
         🪪  ignore.count (non-ignorable)
  36     Parameter #1 $s of function shout expects string, int given.
  ```

- Sửa xong một lỗi có trong baseline thì PHPStan báo mẫu bỏ qua không còn khớp
  (`reportUnmatchedIgnoredErrors`, mặc định bật). Chạy lại `--generate-baseline` để baseline nhỏ đi.

⚠️ Đừng chạy lại `--generate-baseline` để "giấu" lỗi mới vừa xuất hiện. Baseline là danh sách nợ cần
trả dần, chỉ được phép nhỏ lại. Tài liệu PHPStan cũng lưu ý baseline hợp với vài chục tới vài trăm lỗi;
với hàng chục nghìn lỗi thì nên bắt đầu ở level thấp hơn.

Bỏ qua tại chỗ một lỗi thật sự không sửa được (ví dụ thư viện ngoài khai kiểu sai), luôn kèm
identifier và lý do:

```php
$client->send($payload); // @phpstan-ignore argument.type (SDK khai kiểu sai, đã báo upstream)
```

Bật `reportIgnoresWithoutComments: true` trong cấu hình thì PHPStan bắt buộc mọi `@phpstan-ignore` phải
có lý do trong ngoặc, và cấm `@phpstan-ignore-line`, `@phpstan-ignore-next-line` (hai dạng này bỏ qua
mọi lỗi trên dòng, không chọn được loại).

Quy trình đưa PHPStan vào dự án cũ:

1. Cài PHPStan (và Larastan nếu là Laravel), chọn level mục tiêu (thường 5 hoặc 6 cho app cũ).
2. Tạo baseline, commit cả `phpstan.neon` và `phpstan-baseline.neon`.
3. CI chạy `phpstan analyse` trên mọi pull request: lỗi cũ nằm trong baseline, lỗi mới làm PR đỏ.
4. Mỗi lần sửa file nào thì dọn lỗi của file đó trong baseline. Baseline nhỏ lại thì nâng một level, tạo
   baseline mới cho các lỗi của level đó, lặp lại.

### 6.7 Larastan

Laravel dùng nhiều "phép màu" mà PHPStan thuần không hiểu: facade (`Cache::get()` gọi static nhưng thực
chất gọi method của một object trong container), property của Eloquent model đến từ cột trong database
(không khai trong class), relationship, query scope. Không có Larastan, PHPStan báo hàng loạt lỗi
"property không tồn tại" sai.

*Larastan* (`larastan/larastan`) là extension PHPStan cho Laravel. Nó **khởi động ứng dụng** để biết
facade trỏ tới class nào, và đọc các migration để suy ra cột của từng bảng (tức property của model).
README của Larastan gọi đây là "code analysis" vì nó có chạy một phần ứng dụng. Bản 3.x yêu cầu PHP 8.2+
và Laravel 11.15+.

```bash
composer require --dev "larastan/larastan:^3.0"
```

```neon
# phpstan.neon
includes:
    - vendor/larastan/larastan/extension.neon

parameters:
    level: 5
    paths:
        - app/
```

Để Larastan biết model đích của relationship, khai generic trong PHPDoc:

```php
/** @return HasMany<Comment, $this> */
public function comments(): HasMany
{
    return $this->hasMany(Comment::class);
}
```

Chi tiết dùng Larastan với Eloquent nằm ở [Chương 27](27-laravel-database-eloquent.md) và
[Chương 30](30-laravel-testing-octane-deploy.md).

### 6.8 Psalm

*Psalm* là công cụ phân tích tĩnh tương đương PHPStan về kiểm kiểu, cũng đọc generics và array shape
trong PHPDoc (hai công cụ dùng chung phần lớn cú pháp). Khác biệt hay gặp:

- Thang mức của Psalm **ngược** PHPStan: `errorLevel` 1 là chặt nhất, 8 là lỏng nhất.
- *Taint analysis* (`--taint-analysis`): đánh dấu dữ liệu từ nguồn người dùng điều khiển được (*taint
  source*, ví dụ `$_GET['id']`) và lần theo dòng chảy của nó qua biến, hàm, property tới những chỗ
  nguy hiểm (*taint sink*, ví dụ câu SQL ghép chuỗi, `echo` ra HTML, lệnh shell). Nó báo các lỗ hổng
  kiểu SQL injection, XSS ([Chương 17](17-bao-mat.md)) mà không cần chạy code. Theo tài liệu Psalm 6, khi
  bật chế độ này thì Psalm chỉ làm taint analysis, không làm phân tích thường.

Bản ổn định lúc viết là Psalm 6.19, Psalm 7 đang beta. Nhiều team dùng PHPStan cho kiểm kiểu hằng ngày
và chạy thêm Psalm chỉ để làm taint analysis.

### 6.9 Giới hạn của phân tích tĩnh

- **Không biết nghiệp vụ.** Giảm 10% hay 20% là đúng, PHPStan không biết. Đó là việc của test.
- **Chỉ giỏi bằng thông tin kiểu.** Code đầy `mixed`, `array` trống trơn, magic `__get` thì công cụ mù.
  Khai kiểu đầy đủ là đầu tư cho cả người đọc lẫn công cụ.
- **Code động.** `$obj->$methodName()`, `call_user_func($name)`, tên class ghép từ chuỗi: công cụ không
  suy ra được.
- **Có thể báo sai** (*false positive*) khi thiếu extension cho framework, hoặc khi thư viện khai PHPDoc
  sai. Cách đúng là cài extension, hoặc bỏ qua tại chỗ kèm lý do; không hạ level cả dự án.

## 7. Rector: sửa code tự động

### 7.1 Rector là gì

PHPStan **chỉ ra** lỗi; *Rector* **sửa** code. Rector đọc code thành AST, áp các *rule* (quy tắc biến
đổi): mỗi rule tìm một mẫu trong cây và thay bằng mẫu khác, rồi in cây đã sửa trở lại thành code. Rector
dùng PHPStan bên trong để biết kiểu của biểu thức, nên chỉ đổi những chỗ nó chứng minh được là an toàn
(thứ PHPStan thấy là `mixed` thì Rector không dám đụng).

```
  code cũ ──parse──► AST ──rule 1──► rule 2 ──► ... ──in lại──► code mới
                          (tìm mẫu, thay nút cây, dùng kiểu do PHPStan suy ra)
```

Dùng vào việc:

- **Nâng cấp phiên bản PHP**: đổi cú pháp cũ sang cú pháp mới trên toàn dự án (constructor promotion,
  `match`, `str_contains`, `readonly`...).
- **Nâng cấp framework, thư viện**: đổi API đã bỏ sang API mới (có bộ rule cho PHPUnit, Symfony, Doctrine;
  Laravel có gói cộng đồng `driftingly/rector-laravel`).
- **Thêm khai báo kiểu, xoá code chết** hàng loạt.

Rector có thể làm trong vài phút việc mà con người làm hàng tuần, trên hàng nghìn file.

### 7.2 Cấu hình và chạy

```bash
composer require --dev rector/rector
```

File `rector.php` ở thư mục gốc:

```php
<?php
declare(strict_types=1);

use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src', __DIR__ . '/tests'])
    ->withPhpSets(php84: true)                       // mọi rule nâng cú pháp tới PHP 8.4
    ->withPreparedSets(typeDeclarations: true);      // thêm khai báo kiểu suy ra được chắc chắn
```

Các khái niệm:

- *Set*: một nhóm rule theo chủ đề. `withPhpSets()` không tham số sẽ đọc ràng buộc `"php"` trong
  `composer.json` để chọn bản; `withPhpSets(php84: true)` chỉ định rõ. `withPreparedSets(...)` có các
  nhóm như `deadCode`, `codeQuality`, `typeDeclarations`, `earlyReturn`...
- `withAttributesSets(phpunit: true)`: chuyển annotation docblock sang attribute (mục 3.6).
- `withComposerBased(phpunit: true)`: tự chọn bộ rule nâng cấp theo bản thư viện đang cài.

Chạy thử với class cũ sau (`src/Money.php`):

```php
<?php
declare(strict_types=1);

namespace App;

final class Money
{
    private int $amount;
    private string $currency;

    public function __construct(int $amount, string $currency)
    {
        $this->amount = $amount;
        $this->currency = $currency;
    }

    public function isVnd()
    {
        return strpos($this->currency, 'VND') !== false;
    }

    public function format(): string
    {
        switch ($this->currency) {
            case 'VND':
                return number_format($this->amount) . ' ₫';
            case 'USD':
                return '$' . number_format($this->amount / 100, 2);
            default:
                return (string) $this->amount;
        }
    }
}
```

`--dry-run` chỉ in diff, không ghi file (output thật của Rector 2.6.7):

```
$ vendor/bin/rector process --dry-run
1 file with changes
===================

1) src/Money.php:3

    ---------- begin diff ----------
@@ Line 3 @@

 namespace App;

-final class Money
+final readonly class Money
 {
-    private int $amount;
-    private string $currency;
-
-    public function __construct(int $amount, string $currency)
+    public function __construct(private int $amount, private string $currency)
     {
-        $this->amount = $amount;
-        $this->currency = $currency;
     }

-    public function isVnd()
+    public function isVnd(): bool
     {
-        return strpos($this->currency, 'VND') !== false;
+        return str_contains($this->currency, 'VND');
     }

     public function format(): string
     {
-        switch ($this->currency) {
-            case 'VND':
-                return number_format($this->amount) . ' ₫';
-            case 'USD':
-                return '$' . number_format($this->amount / 100, 2);
-            default:
-                return (string) $this->amount;
-        }
+        return match ($this->currency) {
+            'VND' => number_format($this->amount) . ' ₫',
+            'USD' => '$' . number_format($this->amount / 100, 2),
+            default => (string) $this->amount,
+        };
     }
 }
    ----------- end diff -----------

Applied rules:
 * ClassPropertyAssignToConstructorPromotionRector
 * StrContainsRector
 * ChangeSwitchToMatchRector
 * ReadOnlyPropertyRector
 * ReadOnlyClassRector
 * BoolReturnTypeFromBooleanStrictReturnsRector


 [OK] 1 file would have been changed (dry-run) by Rector
```

Bỏ `--dry-run` thì Rector ghi đè file. `--dry-run` trả exit code khác 0 khi có file sẽ bị đổi, nên CI
dùng nó để chặn code mới viết theo kiểu cũ.

### 7.3 Đưa Rector vào dự án cũ an toàn

⚠️ Bật cả loạt set một lúc trên codebase lớn sinh ra một diff chạm gần như mọi file, không ai review
nổi. Tài liệu Rector khuyên đi từng bậc bằng các method *level*: `withTypeCoverageLevel(0)`,
`withDeadCodeLevel(0)`, `withCodeQualityLevel(0)`, `withPhpLevel(0)`... Mỗi level bật thêm rule tiếp theo
trong một danh sách xếp từ an toàn nhất. Mỗi lần tăng một bậc: chạy, review diff nhỏ, chạy test, merge,
lặp lại.

Quy trình gợi ý:

1. Có test và PHPStan chạy xanh trước (Rector đổi code, test là lưới an toàn).
2. Làm việc trên một nhánh riêng, mỗi set hoặc mỗi level một pull request.
3. Chạy Rector, đọc diff như review code của đồng nghiệp, chạy toàn bộ test.
4. Chạy formatter **sau** Rector: Rector in lại code bằng bộ in của thư viện php-parser, khoảng trắng có
   thể lệch chuẩn của dự án.
5. Thêm `rector process --dry-run` vào CI để code mới không quay lại kiểu cũ.

⚠️ Rector không phải lúc nào cũng chỉ đổi cú pháp. Ví dụ trên có hai thay đổi đáng để ý khi review:

- `switch` so sánh lỏng (`==`), `match` so sánh chặt (`===`). Ở đây `$currency` là `string` nên kết quả
  như nhau; Rector dựa vào kiểu để quyết định, nhưng code có kiểu sai hoặc thiếu kiểu thì bạn phải tự
  nghĩ.
- `readonly class`: từ nay không gán lại được property sau constructor, class con (nếu sau này bỏ
  `final`) cũng phải `readonly`. Đó là thay đổi về thiết kế, nên có người duyệt.

Đọc diff, chạy test; đừng merge một diff Rector mà không ai đọc.

## 8. Chuẩn code và formatter

### 8.1 Vì sao cần một chuẩn chung

Ba người trong team, ba kiểu viết: người đặt `{` cùng dòng, người xuống dòng; người dùng tab, người
dùng 4 dấu cách. Hậu quả:

- Review tốn công bàn chuyện khoảng trắng thay vì logic.
- Diff bẩn: một người mở file, editor tự định dạng lại, diff 300 dòng trong khi chỉ sửa 1 dòng thật.
- Đọc code khó hơn vì mắt phải làm quen lại với mỗi file.

Giải pháp: team chọn **một** chuẩn và để **máy** áp dụng nó tự động. Không ai phải nhớ quy tắc.

### 8.2 PHP-FIG, PSR-1 và PSR-12

*PHP-FIG* (PHP Framework Interop Group) là nhóm đại diện các framework và thư viện PHP lớn, soạn ra các
*PSR* (PHP Standards Recommendation). Một số PSR về giao diện chung (PSR-4 autoload ở
[Chương 11](11-namespace-composer.md), PSR-7 HTTP message, PSR-20 clock ở mục 5.7), một số về cách viết:

- *PSR-1* (Basic Coding Standard): quy tắc tối thiểu. Tên class viết `StudlyCaps` (`OrderService`), tên
  method viết `camelCase` (`createOrder`), hằng số viết HOA có gạch dưới (`MAX_ITEMS`). Một file hoặc
  **khai báo** (class, hàm, hằng) hoặc **gây tác động** (in ra, sửa ini), không làm cả hai.
- *PSR-12* (Extended Coding Style, 2019): chi tiết về định dạng. Thụt lề 4 dấu cách; `{` của class và
  method nằm trên dòng riêng; `{` của `if`, `foreach` cùng dòng; một dấu cách sau từ khoá điều khiển;
  từ khoá viết thường; khai báo visibility cho mọi property, method, hằng của class...

### 8.3 PER Coding Style

PSR-12 ra năm 2019, trước khi có `match`, enum, `readonly`, attribute, property hook. PSR đã chốt thì
không sửa, nên PHP-FIG tạo ra *PER* (PHP Evolving Recommendation), loại tài liệu được phép ra bản mới.
*PER Coding Style* tự mô tả là "mở rộng, bổ sung và **thay thế** PSR-12". Các bản: 1.0 (06/2022), 2.0
(04/2023), 3.0 (07/2025).

Vài quy tắc của PER CS 3.0 (trích từ đặc tả):

- Thụt lề 4 dấu cách, không dùng tab.
- Giới hạn mềm độ dài dòng là 120 ký tự; dòng không nên dài quá 80 ký tự.
- Danh sách (tham số, phần tử mảng...) viết trên nhiều dòng thì phần tử cuối **phải** có dấu phẩy
  cuối (*trailing comma*); viết trên một dòng thì **không** được có.
- `declare(strict_types=1)` viết đúng như vậy, không có dấu cách.

Dự án mới không phải Laravel: chọn PER CS. Dự án Laravel: dùng preset `laravel` của Pint (gần PSR-12/PER,
cộng thêm một số quy ước riêng của Laravel).

### 8.4 PHP-CS-Fixer

*PHP-CS-Fixer* (`friendsofphp/php-cs-fixer`) đọc code, áp các *rule* định dạng và sửa file. Các rule được
nhóm thành *rule set*, ký hiệu bắt đầu bằng `@`: `@PER-CS` (luôn trỏ tới bản PER CS mới nhất),
`@PSR12`, `@Symfony`, `@PhpCsFixer`...

Thử với một file viết ẩu (lệnh chạy trong thư mục project; `check` chỉ kiểm, không sửa):

```php
<?php
namespace App;
use App\Models\User;
use App\Models\Order;
class order_service {
    const max_items=10;
    public function Create(User $user,array $items):?Order{
        if(count($items)>self::max_items){ return null; }
        $order=new Order($user->id,$items);
        return $order;
    }
}
```

```
$ vendor/bin/php-cs-fixer check --rules=@PER-CS --diff src/order_service.php
   1) src/order_service.php
      ---------- begin diff ----------
@@ -1,12 +1,19 @@
 <?php
+
 namespace App;
+
 use App\Models\User;
 use App\Models\Order;
-class order_service {
-    const max_items=10;
-    public function Create(User $user,array $items):?Order{
-        if(count($items)>self::max_items){ return null; }
-        $order=new Order($user->id,$items);
+
+class order_service
+{
+    public const max_items = 10;
+    public function Create(User $user, array $items): ?Order
+    {
+        if (count($items) > self::max_items) {
+            return null;
+        }
+        $order = new Order($user->id, $items);
         return $order;
     }
 }

      ----------- end diff -----------

Found 1 of 1 files that can be fixed in 0.016 seconds, 19.56 MB memory used
```

(Output thật của PHP-CS-Fixer 3.95.27, rút gọn phần đầu.) Để ý những gì formatter **không** sửa: tên
class `order_service`, hằng `max_items`, method `Create` vẫn sai quy ước của PSR-1. Đổi tên làm thay đổi
API (code khác đang gọi tên đó), nên formatter không đụng; đó là việc của con người hoặc Rector.

Cấu hình cho dự án đặt ở `.php-cs-fixer.dist.php`:

```php
<?php
declare(strict_types=1);

use PhpCsFixer\Config;
use PhpCsFixer\Finder;

return (new Config())
    ->setRules([
        '@PER-CS' => true,
        'declare_strict_types' => true,      // rule "risky"
    ])
    ->setRiskyAllowed(true)
    ->setFinder(Finder::create()->in([__DIR__ . '/src', __DIR__ . '/tests']));
```

```bash
vendor/bin/php-cs-fixer fix              # sửa file
vendor/bin/php-cs-fixer check --diff     # chỉ kiểm, in diff (dùng trong CI)
```

⚠️ *Risky rule*: một số rule có thể **đổi hành vi** chứ không chỉ khoảng trắng, và mặc định bị tắt.
`declare_strict_types` thêm `declare(strict_types=1)` vào mọi file: lời gọi nào đang chạy được nhờ PHP
tự ép kiểu (`strlen(123)`) sẽ ném `TypeError`. `strict_comparison` đổi `==` thành `===`: kết quả so sánh
có thể khác. Bật risky rule trên code cũ thì phải chạy toàn bộ test.

### 8.5 Laravel Pint

*Laravel Pint* (`laravel/pint`) là lớp bọc PHP-CS-Fixer, cài sẵn trong ứng dụng Laravel mới, không cần
cấu hình: mặc định dùng preset `laravel`. Các preset hỗ trợ: `laravel`, `per`, `psr12`, `symfony`,
`empty` (tự khai từ đầu). Mọi rule của PHP-CS-Fixer đều dùng được trong `pint.json`:

```json
{
    "preset": "laravel",
    "rules": {
        "declare_strict_types": true
    }
}
```

| Lệnh | Dùng khi |
|---|---|
| `vendor/bin/pint` | Sửa toàn bộ dự án |
| `vendor/bin/pint --test` | CI: chỉ kiểm, exit code khác 0 nếu có lỗi style |
| `vendor/bin/pint --dirty` | Trước khi commit: chỉ các file có thay đổi chưa commit |
| `vendor/bin/pint --diff=main` | Chỉ các file khác nhánh `main` |
| `vendor/bin/pint --repair` | Sửa, nhưng vẫn trả exit code khác 0 nếu đã phải sửa |

### 8.6 Công cụ khác và thứ tự chạy

- *PHP_CodeSniffer* (`phpcs` để kiểm, `phpcbf` để sửa) là công cụ lâu đời khác cùng mục đích, dùng nhiều
  trong WordPress, Drupal và các dự án theo chuẩn riêng.
- Cấu hình *EditorConfig* (`.editorconfig`) và formatter trong IDE giúp code đúng ngay từ lúc gõ.
- Thứ tự: **Rector trước, formatter sau** (Rector có thể in code lệch style). Phân tích tĩnh và test
  chạy trên code đã định dạng.

⚠️ Khi áp formatter lần đầu cho dự án cũ, làm trong **một commit riêng chỉ chứa định dạng**, không lẫn
thay đổi logic. Người review chỉ cần xác nhận "chỉ có khoảng trắng". Git có thể bỏ qua commit đó khi
xem lịch sử từng dòng: liệt kê mã commit trong file `.git-blame-ignore-revs` rồi dùng
`git blame --ignore-revs-file .git-blame-ignore-revs` (GitHub đọc file này tự động).

## 9. Ghép lại trong CI

### 9.1 CI là gì

*Continuous integration* (CI, tích hợp liên tục) là thói quen đẩy code lên nhánh chung thường xuyên,
và mỗi lần đẩy thì một máy chủ **tự động** build và chạy mọi kiểm tra. Các dịch vụ phổ biến: GitHub
Actions, GitLab CI, Bitbucket Pipelines, Jenkins. Kết quả hiện ngay trên pull request (PR): xanh thì
được merge, đỏ thì chặn.

Lợi ích không nằm ở công cụ mà ở **tính bắt buộc**: "nhớ chạy PHPStan trước khi push" sẽ có ngày bị
quên; CI thì không quên. Trên GitHub, bật *branch protection* (hoặc *ruleset*) cho nhánh `main` với điều
kiện "các check bắt buộc phải xanh" để không ai merge được khi CI đỏ.

### 9.2 Một workflow GitHub Actions

File `.github/workflows/quality.yml` trong repo:

```yaml
name: quality

on:
  pull_request:
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          coverage: none            # không cần coverage ở job này: chạy nhanh hơn

      - run: composer install --no-interaction --prefer-dist --no-progress

      - run: vendor/bin/php-cs-fixer check --diff                     # 1. style (hoặc: vendor/bin/pint --test)
      - run: vendor/bin/rector process --dry-run --no-progress-bar     # 2. code kiểu cũ
      - run: vendor/bin/phpstan analyse --no-progress --memory-limit=1G # 3. phân tích tĩnh
      - run: vendor/bin/phpunit                                        # 4. test
```

Mỗi bước `run` thất bại (exit code khác 0) làm job dừng và đỏ. Thứ tự: bước **rẻ và nhanh** đặt trước
để báo lỗi sớm; test (chậm nhất) đặt cuối.

Vài kỹ thuật thường dùng khi dự án lớn dần:

- **Tách job song song**: style, PHPStan, test là các job riêng chạy cùng lúc; tổng thời gian bằng job
  chậm nhất thay vì tổng các bước.
- **Cache**: thư mục `vendor/` (khoá theo `composer.lock`), cache của PHPStan và Rector. Lần chạy sau
  nhanh hơn nhiều.
- **Ma trận phiên bản** (`strategy.matrix`): chạy test trên nhiều bản PHP (ví dụ 8.4 và 8.5) trong thời
  gian chuyển đổi.
- **Dịch vụ phụ**: test cần MySQL, Redis thì khai trong khối `services:` của job; GitHub chạy chúng thành
  container cạnh job.
- **Chạy test song song** (Paratest, `php artisan test --parallel`, `pest --parallel`) khi suite dài.

⚠️ CI chậm là CI bị lách. Khi pipeline mất 40 phút, người ta bắt đầu merge mà không chờ. Giữ pipeline
cho PR dưới khoảng 10 phút là mục tiêu thực tế của nhiều team.

### 9.3 Trước khi tới CI: chạy ở máy dev

CI là chốt chặn cuối, nhưng chờ CI báo lỗi dấu cách thì phí thời gian. Gom các lệnh vào `scripts` của
`composer.json` để cả team gõ cùng một lệnh:

```json
{
    "scripts": {
        "lint": "php-cs-fixer check --diff",
        "fix": ["rector process", "php-cs-fixer fix"],
        "analyse": "phpstan analyse",
        "test": "phpunit",
        "ci": ["@lint", "@analyse", "@test"]
    }
}
```

Chạy `composer ci` (Composer tự thêm `vendor/bin` vào `PATH` khi chạy script). Có thể gắn bước nhanh
(formatter cho file đã sửa, như `pint --dirty`) vào *pre-commit hook* của Git; không gắn bước chậm vào
hook vì người ta sẽ tắt hook đi.

### 9.4 Đưa vào dự án cũ không có gì

Thứ tự hợp lý khi một dự án chưa có công cụ nào:

1. **Formatter** trong một commit riêng (mục 8.6). Rẻ nhất, không đổi hành vi.
2. **PHPStan level thấp + baseline**, CI chặn lỗi mới (mục 6.6).
3. **Test cho chỗ đau nhất trước**: luồng tiền, phân quyền, chỗ hay có bug. Với code cũ khó test, viết
   *characterization test* (test "chốt" hành vi hiện tại, kể cả hành vi lạ) trước khi refactor, để biết
   mình không làm đổi gì ngoài ý muốn. Mỗi bug fix kèm một regression test.
4. **Rector** từng level nhỏ, có test làm lưới.
5. Nâng level PHPStan dần, thu nhỏ baseline. Đo xu hướng (số lỗi baseline, số test) theo thời gian.

## 10. Đo chất lượng test: coverage và mutation testing

### 10.1 Code coverage và giới hạn của nó

*Code coverage* (độ phủ) là tỉ lệ code được **chạy qua** khi chạy bộ test. PHPUnit đo được nhiều loại:

- *Line coverage*: tỉ lệ dòng thực thi được đã chạy.
- *Branch coverage*: mỗi điều kiện (`if`, `?:`, `&&`...) đã được thấy cả nhánh đúng lẫn sai chưa.
- *Path coverage*: mỗi đường đi từ đầu tới cuối hàm đã được đi qua chưa.

Cần extension *PCOV* (nhanh, chỉ đo line coverage) hoặc *Xdebug* (bật `xdebug.mode=coverage`; đo được cả
branch và path coverage, bật bằng `--branch-coverage`, `--path-coverage`). Thư mục được tính là các thư
mục trong `<source>` của `phpunit.xml`.

```bash
vendor/bin/phpunit --coverage-text           # in bảng tóm tắt ra terminal
vendor/bin/phpunit --coverage-html coverage/ # báo cáo HTML, tô màu từng dòng
```

Coverage trả lời tốt câu hỏi "**chỗ nào chưa có test chạy qua**": dòng đỏ trong báo cáo HTML chắc chắn
chưa được test. Nhưng coverage cao **không** có nghĩa test tốt:

- Test chạy qua code mà không assert gì vẫn được tính là phủ. (Cấu hình mặc định của PHPUnit đánh dấu
  test không assert là risky, nhưng một assertion hời hợt như `assertNotNull($result)` thì qua.)
- Ở mục 3.7, `testUnknownUser` chạy qua dòng lỗi (100% phủ dòng đó) và còn chốt luôn kết quả sai.
- Hàm một dòng `return $total >= 500_000 ? 0 : 30_000;` được phủ 100% dòng chỉ với một test.

⚠️ Đặt KPI "coverage phải đạt 80%" thường sinh ra test viết cho đủ số, không kiểm gì. Cách dùng tốt
hơn: xem báo cáo để tìm chỗ quan trọng chưa được test, và đặt quy tắc "code mới không làm coverage giảm".

Lưu ý thêm từ tài liệu PHPUnit: coverage của các nhánh trong biểu thức `match` không đáng tin; cả biểu
thức có thể được báo là đã phủ dù chưa chạy hết các nhánh.

### 10.2 Ý tưởng của mutation testing

*Mutation testing* trả lời câu hỏi coverage không trả lời được: **nếu code có bug, test có phát hiện
không?** Cách làm:

1. Công cụ tạo ra nhiều bản sao code, mỗi bản sửa **một** chỗ nhỏ giống lỗi người hay mắc: đổi `>=`
   thành `>`, `true` thành `false`, `+` thành `-`, xoá một lời gọi hàm, đổi giá trị trả về. Mỗi bản gọi
   là một *mutant*; mỗi loại sửa gọi là một *mutator*.
2. Chạy bộ test trên từng mutant.
3. Test đỏ: mutant bị **giết** (*killed*), tốt, test đã phát hiện lỗi. Test vẫn xanh: mutant **sống
   sót** (*escaped*), nghĩa là có một lỗi mà không test nào bắt được.

Mô phỏng bằng PHP thuần, mỗi mutant là một closure:

```php
<?php
declare(strict_types=1);

// Bản gốc: đơn từ 500.000 trở lên được miễn phí ship
$original = fn (int $total): int => $total >= 500_000 ? 0 : 30_000;

// Các "mutant": mỗi bản sửa đúng MỘT chỗ nhỏ, giống cách công cụ mutation testing làm
$mutants = [
    '>= thành >'          => fn (int $total): int => $total > 500_000 ? 0 : 30_000,
    '>= thành <'          => fn (int $total): int => $total < 500_000 ? 0 : 30_000,
    '0 thành 1'           => fn (int $total): int => $total >= 500_000 ? 1 : 30_000,
    '30_000 thành 30_001' => fn (int $total): int => $total >= 500_000 ? 0 : 30_001,
];

/**
 * Một bộ test = danh sách [input, kết quả mong đợi].
 * Trả về true nếu MỌI test đạt với hàm $fee.
 *
 * @param list<array{int, int}> $cases
 */
function suitePasses(callable $fee, array $cases): bool
{
    foreach ($cases as [$input, $expected]) {
        if ($fee($input) !== $expected) {
            return false;
        }
    }
    return true;
}

/**
 * @param list<array{int, int}> $cases
 * @param array<string, callable> $mutants
 */
function report(string $title, array $cases, callable $original, array $mutants): void
{
    echo "== $title", PHP_EOL;
    echo 'Bản gốc: ', suitePasses($original, $cases) ? 'test xanh' : 'test ĐỎ', PHP_EOL;
    $killed = 0;
    foreach ($mutants as $name => $mutant) {
        $survived = suitePasses($mutant, $cases);   // test vẫn xanh = mutant sống sót
        $killed += $survived ? 0 : 1;
        printf("  %-22s %s%s", $name, $survived ? 'SỐNG (test không phát hiện)' : 'bị giết', PHP_EOL);
    }
    printf("  Điểm: %d/%d mutant bị giết (%d%%)%s", $killed, count($mutants), intdiv($killed * 100, count($mutants)), PHP_EOL);
}

// Bộ test yếu: không có ca đúng ngưỡng
$weak = [[100_000, 30_000], [800_000, 0]];
// Bộ test tốt: thêm ca biên
$strong = [[100_000, 30_000], [800_000, 0], [500_000, 0], [499_999, 30_000]];

report('Bộ test yếu', $weak, $original, $mutants);
report('Bộ test có ca biên', $strong, $original, $mutants);
```

```
== Bộ test yếu
Bản gốc: test xanh
  >= thành >            SỐNG (test không phát hiện)
  >= thành <            bị giết
  0 thành 1             bị giết
  30_000 thành 30_001   bị giết
  Điểm: 3/4 mutant bị giết (75%)
== Bộ test có ca biên
Bản gốc: test xanh
  >= thành >            bị giết
  >= thành <            bị giết
  0 thành 1             bị giết
  30_000 thành 30_001   bị giết
  Điểm: 4/4 mutant bị giết (100%)
```

Cả hai bộ test đều phủ 100% dòng code. Chỉ mutation testing cho thấy bộ thứ nhất không kiểm ngưỡng
500.000: nếu ai đó viết nhầm `>` thay cho `>=`, khách đặt đúng 500.000 bị tính phí ship mà không test nào
đỏ. Mutant sống sót **chỉ thẳng** vào ca test còn thiếu.

### 10.3 Infection

*Infection* (`infection/infection`) là công cụ mutation testing chính của PHP. Nó tạo mutant bằng cách
biến đổi AST, hỗ trợ PHPUnit (và PhpSpec, Codeception), yêu cầu PHP 8.3+ và một coverage driver (Xdebug,
PCOV hoặc phpdbg). Bản mới nhất lúc viết là 0.35. Tài liệu Infection khuyến nghị cài bằng PHAR; cài qua
Composer cũng được.

Quy trình bên trong:

1. Chạy toàn bộ test một lần, kèm coverage, để biết test nào chạy qua dòng nào.
2. Sinh mutant từ các *mutator* có sẵn.
3. Với mỗi mutant, **chỉ chạy các test phủ dòng bị sửa** (mutant ở dòng không test nào phủ thì khỏi
   chạy, ghi là *not covered*).
4. Tổng hợp: killed, escaped, timeout, error, not covered.

Lần chạy đầu, Infection hỏi vài câu và tạo file `infection.json5`, ví dụ tối giản:

```json5
{
    "source": {
        "directories": ["src"]
    },
    "threads": "max",
    "logs": {
        "text": "infection.log",
        "html": "infection.html"
    }
}
```

Ba chỉ số chính (theo tài liệu Infection):

| Chỉ số | Công thức | Ý nghĩa |
|---|---|---|
| *Mutation Score Indicator* (MSI) | (killed + timeout + error) / tổng số mutant | Chỉ số chính: tỉ lệ lỗi giả lập bị phát hiện |
| *Mutation Code Coverage* | (tổng mutant - not covered) / tổng mutant | Gần với code coverage thông thường |
| *Covered Code MSI* | (killed + timeout + error) / số mutant được test phủ | Test **đang có** mạnh tới đâu, không tính phần chưa có test |

```
Metrics:
    Mutation Score Indicator (MSI): 47%
    Mutation Code Coverage: 67%
    Covered Code MSI: 70%
```

(Ví dụ lấy từ tài liệu Infection.) Đọc: 67% mutant nằm ở code có test chạy qua, nhưng chỉ 47% tổng số
bị bắt; ngay cả trong phần có test, 30% lỗi giả lập lọt qua.

Dùng trong CI với ngưỡng tối thiểu và chỉ trên phần code thay đổi của PR, vì chạy toàn bộ rất chậm:

```bash
vendor/bin/infection --threads=max --min-msi=70 --min-covered-msi=85
vendor/bin/infection --git-diff-lines --git-diff-base=origin/main   # chỉ mutate các dòng đã sửa
```

- `--min-msi`, `--min-covered-msi`: dưới ngưỡng thì trả exit code khác 0.
- `--git-diff-filter=AM` (chỉ các file thêm mới hoặc sửa), `--git-diff-lines` (chỉ các dòng đã sửa),
  `--git-diff-base` (nhánh để so).
- `--threads`: chạy song song. Tài liệu Infection lưu ý test phụ thuộc nhau hoặc dùng chung database có
  thể cho kết quả sai khi chạy song song.

### 10.4 `pest --mutate`

Pest tích hợp sẵn mutation testing (cũng cần Xdebug hoặc PCOV). Mỗi file test khai nó kiểm code nào bằng
`covers()` hoặc `mutates()`, rồi chạy:

```bash
vendor/bin/pest --mutate --parallel
vendor/bin/pest --mutate --min=40      # dưới 40% thì thất bại
```

Pest gọi mutant bị giết là *tested*, mutant sống sót là *untested*, và in diff của từng mutant sống
sót kèm vị trí. Một dòng cố ý không cần mutate thì đánh dấu `// @pest-mutate-ignore`.

### 10.5 Khi nào dùng mutation testing

- **Giá**: mỗi mutant là một lần chạy (một phần) bộ test. Hàng nghìn mutant nhân với vài giây là rất
  lâu. Vì vậy dùng chọn lọc: module tiền, giá, phân quyền; hoặc chỉ trên dòng đã sửa trong PR.
- **Mutant tương đương** (*equivalent mutant*): có mutant không đổi hành vi (ví dụ đổi điều kiện trong
  nhánh không bao giờ tới được với dữ liệu hợp lệ). Không test nào giết được nó, và đó không phải lỗi
  của test. Đừng đặt mục tiêu 100% MSI cho cả dự án.
- **Cách đọc kết quả**: không cần nhìn con số trước. Đọc danh sách mutant sống sót, mỗi mutant là một câu
  hỏi "nếu code sai như thế này, có ai biết không?". Thường câu trả lời dẫn tới một ca biên còn thiếu.

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách tránh |
|---|---|---|
| Dùng `assertEquals` / `toEqual` cho mọi thứ | So lỏng: `'90000'` bằng `90000`, lọt bug sai kiểu | Mặc định `assertSame` / `toBe`; số thực dùng `assertEqualsWithDelta` |
| Đảo thứ tự tham số `assertSame($actual, $expected)` | Thông báo lỗi nói ngược, gây nhầm khi đọc | Mong đợi trước, thực tế sau |
| `expectException()` ở đầu test rồi chạy nhiều dòng | Dòng chuẩn bị ném cùng exception cũng làm test đạt | Gọi `expectException()` ngay trước dòng được kiểm, dòng đó là dòng cuối |
| Test phụ thuộc thứ tự hoặc dữ liệu test khác để lại | Chạy riêng lẻ hoặc đổi thứ tự là đỏ | Dựng fixture trong `setUp()`; thử `--order-by random` |
| Test gọi `now()`, `rand()`, API thật | Flaky, chậm, có tác dụng phụ thật | Đưa clock, random, gateway vào qua interface; dùng stub/fake |
| `createMock()` cho thứ chỉ cần trả giá trị; năm, sáu `expects()` một test | Gắn test vào cách viết bên trong, refactor là vỡ | Stub cho truy vấn, mock cho mệnh lệnh; fake viết tay cho repository |
| Mock thẳng thư viện ngoài (SDK, HTTP client) | Mock sai cách thư viện thật chạy: test xanh, production đỏ | Bọc bằng interface của mình, mock interface; adapter test riêng |
| Bỏ `final` khỏi class chỉ để mock được | Phá thiết kế vì test | Phụ thuộc vào interface; class tính toán thuần thì dùng object thật |
| Nâng PHPUnit 12 mà vẫn dùng `@test`, `@dataProvider` | Test biến mất lặng lẽ hoặc lỗi thiếu tham số | Chuyển sang attribute (Rector `ANNOTATIONS_TO_ATTRIBUTES`); so số test trước và sau |
| Tin rằng warning trong test sẽ làm CI đỏ | Mặc định PHPUnit chỉ báo "OK, but there were issues!", exit code 0 | Bật `failOnWarning`, `failOnNotice`, `failOnDeprecation` |
| Regenerate baseline PHPStan để giấu lỗi mới | Baseline phình ra thay vì nhỏ lại | Sửa lỗi mới; nếu không sửa được thì `@phpstan-ignore <identifier> (lý do)` |
| Chạy PHPStan trên Laravel không có Larastan | Hàng loạt báo sai về facade, property của model | Cài Larastan; khai generic cho relationship |
| Ép kiểu `(int)` hoặc `@var` cho im lỗi `mixed` | Che lỗi thật, dữ liệu sai vẫn chảy qua | Kiểm tra lúc chạy (`is_int`, validate) để thu hẹp kiểu |
| Merge diff Rector khổng lồ không ai đọc | Rector có thể đổi ngữ nghĩa (`switch` sang `match`, `readonly`) | Đi từng level nhỏ, review diff, chạy test |
| Commit định dạng lẫn với thay đổi logic | Review không nổi, `git blame` mất thông tin | Một commit chỉ định dạng, ghi vào `.git-blame-ignore-revs` |
| Bật risky rule của PHP-CS-Fixer trên code cũ mà không chạy test | `declare_strict_types`, `strict_comparison` đổi hành vi | Bật từng rule, chạy toàn bộ test |
| Lấy coverage làm KPI | Sinh test không kiểm gì cho đủ số | Dùng coverage để tìm chỗ chưa test; dùng mutation testing để đo chất lượng |

## Tóm tắt chương

- PHP chỉ kiểm kiểu ở dòng được chạy tới, nên cần nhiều lớp bắt lỗi trước production: formatter, phân
  tích tĩnh, test, và CI bắt buộc tất cả.
- Test tự động là code gọi code, so kết quả, báo pass/fail qua exit code. Test tốt thì nhanh, độc lập,
  lặp lại được, kiểm hành vi chứ không kiểm cách viết bên trong.
- Unit, integration, feature, E2E khác nhau ở phạm vi; tỉ lệ giữa chúng tuỳ rủi ro nằm ở đâu. Mỗi bug fix
  kèm một regression test.
- PHPUnit 13 (PHP 8.4+), 12 (PHP 8.3+; Laravel 13 mặc định dùng 12.5): test class kế thừa `TestCase`,
  metadata bằng attribute, data provider `public static`, ưu tiên `assertSame`. Pest chạy trên PHPUnit với
  cú pháp hàm và `expect()`.
- Test double: stub cho đầu vào gián tiếp, mock/spy cho đầu ra gián tiếp, fake cho repository. Chỉ thay
  đồ giả ở biên hệ thống, phụ thuộc vào interface, đưa clock và random vào từ ngoài.
- PHPStan: level 0 tới 10 cộng dồn (8 là nullable, 9 và 10 là `mixed`); kiểu PHPDoc và generics
  `@template`; baseline cho dự án cũ và chỉ được nhỏ lại; Larastan cho Laravel; Psalm mạnh về taint
  analysis.
- Rector sửa code theo rule (nâng PHP, thêm kiểu), dùng `--dry-run` trong CI, đi từng bậc và review
  diff. Formatter chạy sau Rector.
- PER Coding Style thay thế PSR-12; PHP-CS-Fixer (`@PER-CS`) hoặc Pint (preset `laravel`) áp style tự
  động; risky rule có thể đổi hành vi.
- Coverage cho biết chỗ chưa test, không cho biết test tốt. Mutation testing (Infection, `pest --mutate`)
  sửa code thành các mutant và xem test có bắt được không; MSI và danh sách mutant sống sót chỉ ra ca test
  còn thiếu.

## Câu hỏi tự kiểm tra

1. Vì sao một dòng code sai kiểu trong PHP có thể nằm im trên production nhiều tháng, trong khi ở Java
   nó không build được? Phân tích tĩnh và test bổ sung cho nhau thế nào? (mục 1.3)
2. Phân biệt unit test, integration test và feature test của Laravel. "Unit" có bắt buộc là một class
   không? (mục 2.4)
3. `assertSame(90000, '90000')` và `assertEquals(90000, '90000')` cho kết quả gì, và vì sao nên mặc định
   dùng cái đầu? (mục 3.3)
4. Một test gọi code phát `E_WARNING` nhưng mọi assertion đúng. PHPUnit báo gì và exit code là bao
   nhiêu với cấu hình mặc định? Muốn CI đỏ thì làm gì? (mục 3.7)
5. Stub và mock khác nhau ở điểm nào? Với một method gửi email và một method lấy tỉ giá, bạn dùng loại
   nào cho mỗi cái, vì sao? (mục 5.2, 5.6)
6. Vì sao không double được class `final`, và cách thiết kế đúng để vẫn test được code phụ thuộc vào
   nó là gì? (mục 5.4, 5.7)
7. PHPStan level 8, 9, 10 lần lượt thêm kiểm tra gì? Vì sao `json_decode()` gây lỗi ở level 9 và cách
   sửa đúng là gì? (mục 6.3)
8. Baseline của PHPStan so khớp lỗi theo những thông tin nào? Chuyện gì xảy ra khi bạn thêm một lỗi
   cùng loại vào file đã có lỗi đó trong baseline? (mục 6.6)
9. Vì sao không nên merge diff của Rector mà không review, dù Rector dùng PHPStan để chỉ đổi chỗ "an
   toàn"? (mục 7.3)
10. Bộ test có 100% line coverage mà vẫn có mutant sống sót nghĩa là gì? MSI và Covered Code MSI khác
    nhau thế nào? (mục 10.1 tới 10.3)

## Bài tập

1. **Framework test tí hon.** Mở rộng `MiniTest` ở mục 2.1: thêm `assertEqualsWithDelta()` cho số thực,
   đếm thời gian chạy mỗi test bằng `hrtime()`, và in tên test fail kèm số dòng gọi assertion (gợi ý:
   `debug_backtrace()`). Viết ít nhất 8 test cho một hàm tính tiền điện bậc thang của riêng bạn, đủ các
   ca biên giữa các bậc.
2. **Từ khó test tới dễ test.** Viết một class `SubscriptionService` có method `isActive(int $userId):
   bool` đọc ngày hết hạn từ một mảng và so với `new DateTimeImmutable()` gọi trực tiếp bên trong. Sau
   đó refactor để nhận một clock và một repository qua constructor (dùng interface tự định nghĩa hoặc
   theo PSR-20). Viết test PHPUnit cho: còn hạn, hết hạn, hết hạn đúng giây hiện tại, user không tồn tại.
   Dùng fake viết tay cho repository, stub cho clock.
3. **Đưa PHPStan vào code có sẵn.** Lấy một thư mục PHP bạn đã viết trong các chương trước (hoặc code
   cũ của mình). Chạy PHPStan từ level 0 tăng dần tới 8; ghi lại số lỗi ở mỗi level và ba loại lỗi gặp
   nhiều nhất. Tạo baseline ở level 6, rồi cố ý thêm một lỗi mới để thấy CI sẽ bắt nó. Sửa dần cho tới
   khi baseline rỗng.
4. **Mutation testing bằng tay rồi bằng công cụ.** Viết hàm `discountFor(int $points): int` (dưới 100
   điểm: 0%, 100 tới 499: 5%, từ 500: 10%) cùng một bộ test PHPUnit "có vẻ đủ" chỉ gồm ba ca 50, 300,
   800. Liệt kê bằng tay ít nhất 5 mutant, dự đoán mutant nào sống sót, rồi kiểm lại bằng cách mô phỏng
   như mục 10.2 (hoặc chạy Infection nếu máy có Xdebug/PCOV). Thêm test cho tới khi không còn mutant
   sống sót, và ghi lại những ca nào đã thêm.

## Đọc thêm

- PHPUnit 13 Manual: [Writing Tests](https://docs.phpunit.de/en/13.4/writing-tests-for-phpunit.html),
  [Test Doubles](https://docs.phpunit.de/en/13.4/test-doubles.html),
  [Code Coverage](https://docs.phpunit.de/en/13.4/code-coverage.html),
  [Error Handling](https://docs.phpunit.de/en/13.4/error-handling.html),
  [The Command-Line Test Runner](https://docs.phpunit.de/en/13.4/textui.html),
  [XML Configuration File](https://docs.phpunit.de/en/13.4/configuration.html);
  [Supported Versions](https://phpunit.de/supported-versions.html); ChangeLog
  [12.0](https://github.com/sebastianbergmann/phpunit/blob/12.0.0/ChangeLog-12.0.md),
  [13.0](https://github.com/sebastianbergmann/phpunit/blob/13.0.0/ChangeLog-13.0.md)
- Pest: [Writing Tests](https://pestphp.com/docs/writing-tests),
  [Expectations](https://pestphp.com/docs/expectations),
  [Architecture Testing](https://pestphp.com/docs/arch-testing),
  [Mutation Testing](https://pestphp.com/docs/mutation-testing),
  [Pest 5 Now Available](https://pestphp.com/docs/pest5-now-available),
  [Support Policy](https://pestphp.com/docs/support-policy)
- Laravel 13.x: [Testing: Getting Started](https://laravel.com/docs/13.x/testing),
  [Laravel Pint](https://laravel.com/docs/13.x/pint)
- PHPStan: [Rule Levels](https://phpstan.org/user-guide/rule-levels),
  [The Baseline](https://phpstan.org/user-guide/baseline),
  [Ignoring Errors](https://phpstan.org/user-guide/ignoring-errors),
  [PHPDoc Types](https://phpstan.org/writing-php-code/phpdoc-types),
  [Generics in PHP using PHPDocs](https://phpstan.org/blog/generics-in-php-using-phpdocs);
  [Larastan](https://github.com/larastan/larastan);
  Psalm: [Security Analysis](https://psalm.dev/docs/security_analysis/)
- [Rector documentation](https://getrector.com/documentation) (Set Lists, Levels);
  [rector-laravel](https://github.com/driftingly/rector-laravel)
- PHP-FIG: [PSR-1](https://www.php-fig.org/psr/psr-1/), [PSR-12](https://www.php-fig.org/psr/psr-12/),
  [PER Coding Style](https://www.php-fig.org/per/coding-style/), [PSR-20 Clock](https://www.php-fig.org/psr/psr-20/);
  [PHP-CS-Fixer](https://cs.symfony.com/) (Usage, Rule Sets)
- Infection: [Introduction](https://infection.github.io/guide/),
  [Command Line Options](https://infection.github.io/guide/command-line-options.html)
- Martin Fowler: [UnitTest](https://martinfowler.com/bliki/UnitTest.html),
  [Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html),
  [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)
- *Software Engineering at Google*, [chương 12 Unit Testing](https://abseil.io/resources/swe-book/html/ch12.html)
  và [chương 13 Test Doubles](https://abseil.io/resources/swe-book/html/ch13.html)
- Gerard Meszaros, *xUnit Test Patterns* (nguồn của thuật ngữ test double); Michael Feathers, *Working
  Effectively with Legacy Code* (characterization test, đưa test vào code cũ)
