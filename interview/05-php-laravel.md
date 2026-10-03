# 05. PHP và Laravel

> [← Mục lục](README.md) · **[📖 Giáo trình PHP và Laravel (30 chương)](kien-thuc/php/README.md)** · Trọng tâm: **PHP 8.4–8.5** (runtime Zend Engine, OPcache, PHP-FPM, GC), Composer/PSR, **Laravel 12–13** từ lifecycle tới queue/Octane, chất lượng code, hiệu năng, bảo mật đặc thù PHP.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn.

Nếu PHP/Laravel là ngôn ngữ chính trong CV, đây là file bị đào sâu nhất. Trả lời hời hợt ở
đây bị trừ điểm nặng hơn nhiều so với không biết Go hay Java.

Cách học: kiến thức đầy đủ từ cơ bản tới nâng cao nằm trong
[Giáo trình PHP và Laravel](kien-thuc/php/README.md) (30 chương, có ví dụ chạy được, câu hỏi tự
kiểm tra và bài tập). File này là bản đồ ôn tập: mỗi module ghi rõ chương giáo trình cần đọc, rồi
dùng tiêu chí "Nắm chắc khi" và Phần 2 để tự kiểm tra.

File gồm hai phần:

1. **Lộ trình kiến thức** (phần chính): ba chặng từ nền tới senior. Mỗi module có:
   - **Giáo trình**: các chương cần đọc trong giáo trình.
   - **Vì sao cần học**: module này dùng vào việc gì và hay bị hỏi thế nào.
   - **Học gì**: các khái niệm, giải thích bằng lời thường kèm ví dụ, và các cạm bẫy ⚠️. Đọc phần
     này để biết cần học gì, rồi học sâu qua tài liệu ở mục Đọc.
   - **Đọc**: tài liệu gốc.
   - **Nắm chắc khi**: tiêu chí tự kiểm tra. Chỉ tick ô khi làm được điều đó mà không cần nhìn
     tài liệu.
2. **Câu hỏi thường gặp** (bonus): mỗi câu kèm hướng trả lời mong đợi, gồm ý phải có, điểm
   cộng senior và red flag. Dùng để kiểm tra sau khi học, không dùng để học thuộc.

Mốc phiên bản (tháng 9/2026): PHP 8.5 là bản mới nhất (phát hành 20/11/2025), 8.4 còn active
support tới hết 2026, 8.2 chỉ còn security fix tới hết 2026. Laravel 13 phát hành 17/03/2026
(PHP ≥ 8.3); Laravel 12 đã hết bug fix (13/08/2026), còn security fix tới 24/02/2027.

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [PHP Manual](https://www.php.net/manual/en/) | Official docs | Nguồn chuẩn cho ngôn ngữ, ini, FPM, OPcache. Đọc cả phần *Changelog* cuối mỗi trang hàm |
| [PHP RFC wiki](https://wiki.php.net/rfc) | Đặc tả thay đổi | Vì sao một tính năng tồn tại, ca biên, thứ bị từ chối. RFC trả lời "vì sao" tốt hơn manual |
| [PHP.Watch: versions](https://php.watch/versions) | Tổng hợp theo phiên bản | Mỗi bản 8.x có gì mới, gì deprecated, gì đổi mặc định. Dùng khi nâng cấp |
| [PHP Internals Book](https://www.phpinternalsbook.com/) | Sách online miễn phí | zval, refcount, `zend_string`, hashtable, lifecycle của extension. Đọc phần PHP 7/8 |
| [Nikita Popov (nikic) blog](https://www.npopov.com/) | Blog của core dev | Các bài kinh điển về biểu diễn giá trị, hashtable, VM của PHP 7+ |
| [Laravel docs](https://laravel.com/docs/lifecycle) | Official docs | Luôn là bản mới nhất (13.x). Đọc kỹ *Architecture Concepts*, *Queues*, *Eloquent* |
| [laravel/framework](https://github.com/laravel/framework) | Source code | Đọc `Container.php`, `Facade.php`, `Http/Kernel.php` khi muốn trả lời "bên dưới làm gì" |
| [PHPStan docs](https://phpstan.org/user-guide/getting-started) | Official docs | Static analysis: rule level, baseline, generics trong PHPDoc |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.6 | Viết PHP hiện đại không dính bẫy type juggling, hiểu OOP của PHP, Composer, Laravel cơ bản | 5–6 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.8 | PHP 8.x, PHP-FPM và OPcache ở mức vận hành, lõi Laravel (container, provider, facade), Eloquent, queue, công cụ chất lượng | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.8 | Hiểu engine (zval, COW, GC, JIT), tinh chỉnh FPM, process sống lâu và Octane, profiling, bảo mật, so sánh kiến trúc | 10–12 ngày |

Học theo thứ tự. Người phỏng vấn PHP senior hay đi theo đúng đường này: hỏi `==` và `===`,
rồi array copy thế nào, rồi copy-on-write, rồi refcount và GC, rồi vì sao worker sống lâu bị
leak. Mỗi tầng giải thích tầng phía trên.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Type system và so sánh

📖 **Giáo trình:** [Chương 04. Kiểu dữ liệu và hệ thống kiểu](kien-thuc/php/04-kieu-du-lieu.md), [Chương 07. Toán tử và cấu trúc điều khiển](kien-thuc/php/07-toan-tu-dieu-khien.md)

**Vì sao cần học:** Rất nhiều bug PHP kiểu "kiểm tra quyền bị qua mặt", "token sai vẫn khớp",
"trạng thái đơn so sai" bắt nguồn từ việc PHP tự đổi kiểu khi so sánh. Đây gần như luôn là câu
mở màn của phỏng vấn PHP: hỏi `==` và `===`, rồi hỏi tiếp PHP 8 đã đổi gì và `strict_types` có
cứu được không.

**Học gì**

*Các kiểu dữ liệu và type declaration*
- *Type declaration* là khai báo kiểu cho tham số, giá trị trả về và property, ví dụ
  `function total(int $qty): float`. PHP kiểm tra lúc chạy, sai kiểu thì ném `TypeError`.
- Các kiểu cơ bản:
  - *Scalar* (kiểu đơn): `int`, `float`, `string`, `bool`.
  - `array` và `object`.
  - `callable`: thứ gọi được như hàm (tên hàm, closure, `[$obj, 'method']`).
  - `iterable`: array hoặc object duyệt được bằng `foreach`.
  - `mixed`: kiểu bất kỳ, kể cả `null`.
  - `void`: hàm không trả về gì.
  - `never` (8.1): hàm không bao giờ kết thúc bình thường, luôn ném exception hoặc `exit`.
- Các kiểu ghép:
  - *Union type* `A|B` (8.0): giá trị là A **hoặc** B, ví dụ `int|string`.
  - *Intersection type* `A&B` (8.1): giá trị phải **vừa là** A **vừa là** B, ví dụ object
    implement cả hai interface `Countable&Traversable`.
  - *DNF type* `(A&B)|null` (8.2): viết tắt của *Disjunctive Normal Form*, tức "hợp của các
    intersection". Dùng khi cần "vừa A vừa B, hoặc là null".
  - `null` và `false` đứng riêng làm kiểu được từ 8.2, ví dụ `function f(): false` (trước đó chỉ
    dùng trong union như `string|false`, có từ 8.0). Kiểu `true` cũng có từ 8.2.
- ⚠️ *Implicit nullable*: viết `function f(Foo $x = null)` thì PHP ngầm hiểu `$x` nhận được
  `null`. Cách viết này bị deprecated từ 8.4. Viết tường minh `?Foo $x = null`.

*strict_types: chế độ ép kiểu và chế độ chặt*
- Mặc định PHP chạy ở *coercive mode* (chế độ ép kiểu): nếu đổi được thì PHP tự ép giá trị sang
  kiểu đã khai báo.
  - Ví dụ: hàm `f(int $x)` được gọi với `"5"` thì `$x` nhận `5`, không có lỗi.
- `declare(strict_types=1);` ở dòng đầu file bật *strict mode*: sai kiểu là `TypeError`, không ép.
- ⚠️ Strict mode áp dụng **theo file của phía gọi**, không theo file khai báo hàm:

  ```php
  // b.php
  declare(strict_types=1);
  function f(int $x): int { return $x; }

  // a.php (không có declare)
  require 'b.php';
  f("5");   // chạy bình thường, "5" bị ép thành 5, vì file gọi (a.php) không strict
  ```

  - Lý do: strict là lựa chọn của người viết code gọi, "tôi muốn code của tôi truyền đúng kiểu".
  - Return type thì ngược lại, kiểm theo file **khai báo hàm**, vì đó là code của người viết hàm.
- Strict vẫn cho phép một phép ép duy nhất: int sang float. `function g(float $x)` nhận `5` được.
- ⚠️ Strict mode **không ảnh hưởng** toán tử `==`. Nó chỉ áp cho tham số, return và property.

*Type juggling và toán tử so sánh*
- *Type juggling* là việc PHP tự đổi kiểu khi so sánh hoặc tính toán hai giá trị khác kiểu.
- `===` so cả kiểu lẫn giá trị, không đổi kiểu gì cả. `==` đổi hai bên về cùng kiểu rồi mới so.
- *Numeric string* (chuỗi số) là chuỗi trông như một số: `"10"`, `"01"`, `"1e1"` (ký hiệu khoa
  học, nghĩa là 1 × 10¹ = 10).
- PHP 8 đổi quy tắc khi so **số** với **chuỗi không phải số** (RFC *Saner string to number
  comparisons*):
  - PHP 7: ép chuỗi thành số. `"a"` thành `0`, nên `0 == "a"` là `true`.
  - PHP 8: đổi số thành chuỗi rồi so như chuỗi. `"0"` khác `"a"`, nên kết quả là `false`.
  - Nếu chuỗi là numeric string thì cả hai bản vẫn so như số.

  | Biểu thức | PHP 7 | PHP 8 | Vì sao |
  |---|---|---|---|
  | `0 == "a"` | `true` | `false` | Quy tắc mới ở trên |
  | `"1" == "01"` | `true` | `true` | Hai numeric string, so như số: 1 = 1 |
  | `"10" == "1e1"` | `true` | `true` | `"1e1"` là 10 |
  | `100 == "1e2"` | `true` | `true` | `"1e2"` là 100 |
  | `null == false` | `true` | `true` | Cả hai đổi sang bool là `false` |
  | `[] == false` | `true` | `true` | Array rỗng đổi sang bool là `false` |

- Thói quen an toàn: luôn dùng `===`. Chỉ dùng `==` khi thật sự muốn ép kiểu và biết rõ quy tắc.

*Hàm và cấu trúc so lỏng ngầm*
- ⚠️ `in_array`, `array_search`, `array_keys($a, $v)` mặc định dùng `==`. Luôn truyền `true` ở
  tham số strict:

  ```php
  in_array('abc', [0]);          // PHP 7: true, vì 'abc' bị ép thành 0
  in_array('1e1', ['10']);       // PHP 8 vẫn true: hai numeric string so như số
  in_array('1e1', ['10'], true); // false: so bằng ===
  ```
- `switch` so bằng `==`. `match` (8.0) so bằng `===`:
  - `match` là *biểu thức*, tức trả về giá trị, gán thẳng được: `$label = match ($status) { ... };`
  - Không có nhánh nào khớp thì ném `UnhandledMatchError`, thay vì lặng lẽ bỏ qua như `switch`.
  - Không cần `break`, nên không có bug "quên break rơi xuống nhánh sau".

**Đọc**
- PHP: [Type declarations](https://www.php.net/manual/en/language.types.declarations.php) (mục [Strict typing](https://www.php.net/manual/en/language.types.declarations.php#language.types.declarations.strict)), [Type juggling](https://www.php.net/manual/en/language.types.type-juggling.php), [Comparison operators](https://www.php.net/manual/en/language.operators.comparison.php), [Type comparison tables](https://www.php.net/manual/en/types.comparisons.php), [`match`](https://www.php.net/manual/en/control-structures.match.php)
- RFC: [Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison) (bảng so sánh PHP 7 và PHP 8), [Deprecate implicitly nullable parameter types](https://wiki.php.net/rfc/deprecate-implicitly-nullable-types)

**Nắm chắc khi**
- [ ] Dự đoán đúng kết quả của 10 biểu thức `==` trong bảng RFC, cả ở PHP 7 lẫn PHP 8
- [ ] Giải thích được vì sao file A strict gọi hàm trong file B không strict thì kiểm tra theo A
- [ ] Chỉ ra được bug của `in_array('abc', [0])` ở PHP 7 và `in_array('1e1', ['10'])` ở PHP 8

#### 1.2 Array, reference và object handle

📖 **Giáo trình:** [Chương 06. Mảng (array)](kien-thuc/php/06-mang.md), [Chương 08. Hàm](kien-thuc/php/08-ham.md), [Chương 09. OOP cơ bản: class và object](kien-thuc/php/09-oop-co-ban.md)

**Vì sao cần học:** Array là cấu trúc dữ liệu dùng nhiều nhất trong PHP: kết quả query, payload
JSON, config đều là array. Hiểu sai cách array được copy và cách reference hoạt động dẫn tới bug
khó thấy (bẫy `foreach` by reference) và "tối ưu" ngược. Đây cũng là bậc đầu tiên để người
phỏng vấn đào xuống copy-on-write và refcount ở module 3.1.

**Học gì**

*Array là hash table có thứ tự*
- *Hash table* là cấu trúc lưu cặp key → value, tra theo key rất nhanh (trung bình O(1)).
- Array của PHP là một *ordered hash table*: hash table nhưng **giữ thứ tự chèn**. Nhờ vậy một
  kiểu dùng được cho cả hai vai:
  - *List*: key là 0, 1, 2... liên tục, như `['a', 'b', 'c']`.
  - *Map*: key tuỳ ý, như `['name' => 'An', 'age' => 30]`.
- *Packed array*: khi key là số nguyên tăng dần (thường là 0..n), PHP lưu gọn như mảng thường, bỏ hẳn phần
  hash. Tiết kiệm RAM và nhanh hơn (chi tiết ở 3.1).
- ⚠️ Key bị ép kiểu khi ghi vào array:
  - `"1"` thành `1` (chuỗi số nguyên dạng chuẩn thành int).
  - `true` thành `1`, `false` thành `0`.
  - `null` thành `""`.
  - Float bị cắt phần thập phân, `1.7` thành `1`. Từ 8.1, dùng float **có phần thập phân** làm key (ví dụ `1.7`) bị deprecated; float nguyên như `1.0` thì không.
  - `"01"` **vẫn là string**, vì nó không phải dạng chuẩn của số 1.
  - Hệ quả: `['1' => 'a', 1 => 'b', true => 'c']` chỉ có **một** phần tử `[1 => 'c']`.

*Gộp và kiểm tra array*
- `array_merge($a, $b)` đánh lại số cho các key số (0, 1, 2...), key chuỗi của `$b` ghi đè `$a`.
- `$a + $b` giữ nguyên key. Key nào đã có ở vế trái thì bỏ giá trị bên phải.

  ```php
  array_merge([5 => 'x'], [5 => 'y']);  // [0 => 'x', 1 => 'y']
  [5 => 'x'] + [5 => 'y'];              // [5 => 'x']
  ```
- `array_is_list($a)` (8.1) kiểm tra array có phải list (key đúng là 0, 1, ..., count-1 theo thứ tự) không. Có ích khi
  quyết định encode JSON ra `[]` hay `{}`.

*Gán giá trị: array copy, object là handle*
- Gán array là **copy theo giá trị**: `$b = $a` rồi sửa `$b` thì `$a` không đổi.
  - Bên dưới PHP không copy ngay mà dùng *copy-on-write*: hai biến dùng chung một bản, chỉ khi
    một bên ghi thì mới tách ra bản riêng. Vì vậy gán array lớn gần như không tốn gì (module 3.1).
- Object thì khác. Biến không chứa object mà chứa một *handle*, tức một mã số trỏ tới object.
  - `$b = $a` là copy handle, nên cả hai biến trỏ **cùng một object**. Sửa qua `$b` thì `$a` thấy.
  - Vì vậy câu "object được truyền by reference" là **sai**: cái được truyền là bản copy của handle.
    Hàm sửa property thì bên ngoài thấy, nhưng hàm gán `$obj = new X` thì chỉ đổi handle của biến
    cục bộ, bên ngoài không thấy.
- `clone $obj` tạo object mới nhưng là *shallow copy* (copy nông): property là object thì vẫn
  copy handle, nên object con vẫn dùng chung.
  - Override `__clone()` để clone tiếp những object con cần tách riêng (*deep copy*).

*Reference `&`*
- *Reference* là hai tên biến cùng trỏ vào **một chỗ chứa**. `$b = &$a` rồi gán `$b = 5` thì
  `$a` cũng là 5.
- ⚠️ Cạm bẫy kinh điển:

  ```php
  $a = [1, 2, 3];
  foreach ($a as &$v) {}      // $v giờ là reference tới $a[2]
  foreach ($a as $v) {}       // mỗi vòng ghi đè $a[2]
  // $a === [1, 2, 2]
  ```

  Diễn biến vòng thứ hai:
  1. Vòng 1 gán `$v = $a[0]`, tức ghi 1 vào `$a[2]`. Array thành `[1, 2, 1]`.
  2. Vòng 2 gán `$v = $a[1]`, ghi 2 vào `$a[2]`. Array thành `[1, 2, 2]`.
  3. Vòng 3 gán `$v = $a[2]`, tức gán `$a[2]` cho chính nó, vẫn là 2.

  Sửa: gọi `unset($v)` ngay sau vòng lặp by reference để cắt liên kết.
- ⚠️ Reference phá cơ chế copy-on-write, nên thường **chậm hơn** chứ không nhanh hơn. Đừng dùng
  `&` để "tối ưu" việc truyền array lớn vào hàm.
- Object không cần `&` để sửa nội dung, vì handle đã trỏ tới cùng object rồi.

*Chi phí bộ nhớ*
- Mỗi phần tử array PHP tốn nhiều RAM hơn mảng C: mỗi phần tử là một zval 16 byte (có thông tin
  kiểu). Array dạng hash còn phải lưu key và hash cho từng phần tử; *packed array* (key 0, 1, 2...
  theo thứ tự) từ PHP 8.2 chỉ lưu zval, không lưu key và hash.
- Dữ liệu cỡ triệu dòng:
  - Dùng *generator* (hàm `yield` từng phần tử thay vì trả cả array, module 2.1).
  - Hoặc `SplFixedArray` (mảng cố định kích thước, chỉ key số).
  - Hoặc tốt nhất là đừng nạp hết vào RAM, xử lý theo lô.

**Đọc**
- PHP: [Arrays](https://www.php.net/manual/en/language.types.array.php) (phần key casting), [References Explained](https://www.php.net/manual/en/language.references.php), [foreach](https://www.php.net/manual/en/control-structures.foreach.php) (cảnh báo về reference), [Objects and references](https://www.php.net/manual/en/language.oop5.references.php), [Object Cloning](https://www.php.net/manual/en/language.oop5.cloning.php)

**Nắm chắc khi**
- [ ] Viết lại được đoạn `foreach` trên, dự đoán output rồi chạy `php file.php` để kiểm (bài tập 1)
- [ ] Giải thích được "object được truyền by reference" sai ở chỗ nào
- [ ] Nói được `['1' => 'a', 1 => 'b', true => 'c']` có mấy phần tử và vì sao

#### 1.3 OOP trong PHP

📖 **Giáo trình:** [Chương 09. OOP cơ bản: class và object](kien-thuc/php/09-oop-co-ban.md), [Chương 10. OOP nâng cao và các tính năng hiện đại](kien-thuc/php/10-oop-nang-cao.md)

**Vì sao cần học:** Laravel dựa rất nhiều vào những tính năng OOP riêng của PHP: trait,
`static::`, magic method, closure. Không hiểu chúng thì đọc source Laravel như đọc phép thuật, và
không trả lời được câu "`User::where()` gọi được dù `where` không phải static method là vì sao".

**Học gì**

*Interface, abstract class, trait*

| | Interface | Abstract class | Trait |
|---|---|---|---|
| Là gì | Hợp đồng: danh sách method phải có | Class dở dang, không `new` được | Khối code được chép vào class |
| Có state (property) | Không lưu state; có hằng, và từ 8.4 khai báo được property (kèm hook) mà class phải hiện thực | Có | Có |
| Có constructor | Khai báo được chữ ký nhưng không nên | Có | Có thể có, nhưng hiếm khi nên |
| Là một type (`instanceof`, type hint) | Có | Có | **Không** |
| Một class dùng được mấy cái | Nhiều | Một (kế thừa đơn) | Nhiều |

- Trait hoạt động như "copy-paste lúc compile": các method của trait được chép vào class dùng nó.
- Xung đột tên khi hai trait cùng có method `hello`:

  ```php
  class Greeter {
      use A, B {
          A::hello insteadof B;   // dùng bản của A
          B::hello as helloB;     // bản của B vẫn gọi được qua tên khác
      }
  }
  ```
- Trait khai báo được abstract method (bắt class dùng nó phải viết). Static property trong trait
  là **riêng cho mỗi class** dùng trait. ⚠️ Trước 8.3, nếu class cha và class con cùng `use` một
  trait thì hai class vẫn dùng chung static property đó; từ 8.3 mới tách riêng. Từ 8.2 trait có hằng.
- ⚠️ Trait không phải type: không `instanceof Trait` được, không type hint bằng trait được.
- ⚠️ Lạm dụng trait là một dạng kế thừa ngầm: method từ đâu tới, property nào đè property nào rất
  khó lần. Nếu cần "có khả năng X" thì interface + composition (inject object làm việc X) thường
  rõ hơn.

*Late static binding: `self::` và `static::`*
- `self::` gắn với class **nơi dòng code được viết**. `static::` gắn với class **được gọi lúc
  chạy** (cơ chế gọi là *late static binding*, "gắn muộn").

  ```php
  class Model {
      public static function make(): static { return new static(); }
      public static function makeSelf(): self { return new self(); }
  }
  class User extends Model {}

  User::make();      // User, vì static:: là class được gọi
  User::makeSelf();  // Model, vì self:: là class chứa dòng code
  ```
- Eloquent dùng `new static()` khắp nơi, nhờ vậy `User::query()` trả builder cho `User` dù
  method viết ở class `Model`.

*Magic method*
- *Magic method* là method có tên bắt đầu bằng `__` mà PHP tự gọi khi có sự kiện đặc biệt:
  - `__get`/`__set`/`__isset`/`__unset`: đọc, ghi, `isset`, `unset` một property không tồn tại
    hoặc không truy cập được.
  - `__call`/`__callStatic`: gọi method không tồn tại (trên object, hoặc kiểu static).
  - `__toString`: khi object bị dùng như chuỗi. `__invoke`: khi gọi object như hàm `$obj()`.
  - `__clone`: sau khi `clone`. `__serialize`/`__unserialize`: khi serialize.
  - `__debugInfo`: quyết định `var_dump` in ra gì.
- Eloquent sống nhờ magic:
  - `$user->name` không phải property thật. `__get` tra trong mảng attribute của model.
  - `User::where(...)`: class không có static method `where`, nên PHP gọi `__callStatic`. Hàm này
    tạo một instance rồi chuyển lời gọi sang query builder qua `__call`.
- ⚠️ Magic làm IDE và static analysis "mù": công cụ không biết `$user->name` có tồn tại không nếu
  không có PHPDoc hoặc Larastan (module 2.8). Magic cũng chậm hơn truy cập trực tiếp.
- `__sleep`/`__wakeup` là cách cũ để điều khiển serialize, soft-deprecated từ 8.5 (khuyên không
  dùng nữa, chưa bắn cảnh báo). Dùng `__serialize`/`__unserialize`.

*Closure và arrow function*
- *Closure* là hàm không tên, gán được vào biến và mang theo biến từ bên ngoài.
  - `function () use ($x) { ... }` bắt **giá trị** của `$x` tại lúc định nghĩa closure. Đổi `$x`
    bên ngoài sau đó thì closure không thấy.
  - `use (&$x)` bắt reference, closure thấy thay đổi và sửa được `$x` bên ngoài.
- *Arrow function* `fn($y) => $x + $y`: tự bắt mọi biến bên ngoài theo giá trị, không cần `use`,
  nhưng thân chỉ được một biểu thức.
- Closure viết bên trong method của class tự *bind* `$this`, tức giữ tham chiếu tới object đó.
  - `static fn () => ...` hoặc `static function` thì không bind `$this`.
  - ⚠️ Có ích trong process sống lâu (queue worker, Octane, module 3.5): closure giữ `$this` làm
    object không được giải phóng khi closure còn sống.
- *First-class callable* `strlen(...)` (8.1): tạo closure từ một hàm hoặc method có sẵn, ví dụ
  `array_map(strtoupper(...), $names)`.
- `Closure::bind` gắn closure vào object hoặc scope khác. `Closure::fromCallable` là cách cũ trước
  cú pháp `(...)`.

**Đọc**
- PHP: [Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php), [Traits](https://www.php.net/manual/en/language.oop5.traits.php), [Late Static Bindings](https://www.php.net/manual/en/language.oop5.late-static-bindings.php), [Magic Methods](https://www.php.net/manual/en/language.oop5.magic.php), [Anonymous functions](https://www.php.net/manual/en/functions.anonymous.php), [Arrow Functions](https://www.php.net/manual/en/functions.arrow.php), [First class callable syntax](https://www.php.net/manual/en/functions.first_class_callable_syntax.php)
- Nguyên lý thiết kế chung (SOLID, composition): [08-oop-design.md](08-oop-design.md)

**Nắm chắc khi**
- [ ] Viết được ví dụ `self` và `static` cho ra kết quả khác nhau
- [ ] Giải thích được `User::where(...)` gọi được dù `where` không phải static method
- [ ] Nêu được một ca trait là lựa chọn đúng và một ca nên thay bằng composition

#### 1.4 Exception và xử lý lỗi

📖 **Giáo trình:** [Chương 12. Lỗi và exception](kien-thuc/php/12-loi-exception.md)

**Vì sao cần học:** Bắt exception sai tầng hoặc bắt sai loại là nguồn của các bug "job chết im
lặng", "lỗi bị nuốt, log không có gì". Người phỏng vấn hay hỏi `Exception` khác `Error` thế nào,
và nhờ đó biết bạn có hiểu cây `Throwable` của PHP 7+ không.

**Học gì**

*Cây Throwable*
- Mọi thứ ném được (`throw`) đều implement interface `Throwable`. Có hai nhánh:
  ```text
  Throwable
  ├── Exception  (RuntimeException, LogicException, InvalidArgumentException, PDOException, JsonException...)
  └── Error      (TypeError → ArgumentCountError, ValueError, ArithmeticError → DivisionByZeroError,
                  CompileError → ParseError, UnhandledMatchError, ...)
  ```
- `Exception`: lỗi mà ứng dụng dự kiến có thể xảy ra và có thể xử lý (DB lỗi, input sai).
- `Error`: lỗi của engine hoặc của lập trình (sai kiểu, gọi hàm không tồn tại, chia cho 0).
  - Trước PHP 7, các lỗi này là *fatal error*: script dừng hẳn, không bắt được. PHP 7 biến nhiều
    fatal error thành `Error` để `catch` được.
- ⚠️ `catch (Exception $e)` **không** bắt `Error`. Muốn bắt cả hai thì `catch (Throwable $e)`.

  ```php
  try {
      strlen();                       // ArgumentCountError, một loại Error
  } catch (Exception $e) {
      // không vào đây
  } catch (Throwable $e) {
      // vào đây
  }
  ```
  - Hệ quả thực tế: job Laravel chỉ `catch (Exception)` sẽ để `TypeError` bay qua, và nếu không có
    tầng nào log thì trông như job "chết im lặng".
- Code của bạn không implement `Throwable` trực tiếp được, phải `extends Exception` hoặc
  `extends Error`.

*try/catch/finally*
- `finally` luôn chạy, dù `try` kết thúc bình thường, `return` sớm hay ném exception.
- ⚠️ `return` bên trong `finally` **đè** giá trị `return` trong `try`, và còn nuốt luôn exception
  đang bay. Đừng `return` trong `finally`.
- `json_decode($s, flags: JSON_THROW_ON_ERROR)` ném `JsonException` khi JSON hỏng. Cách cũ là
  gọi `json_last_error()` sau mỗi lần decode, rất dễ quên.

*Warning, notice và fatal error*
- Warning và notice (ví dụ đọc key không tồn tại) **không** phải exception. PHP in cảnh báo rồi
  chạy tiếp.
  - Chỉ khi có *error handler* (hàm đăng ký qua `set_error_handler`) đổi chúng thành exception thì
    mới bắt được. Laravel làm việc này ở **mọi môi trường** (class `HandleExceptions`): warning và
    notice thành `ErrorException`, còn deprecation thì chỉ ghi log.
- PHP 8.5: fatal error (loại vẫn không bắt được, ví dụ hết bộ nhớ) có kèm *backtrace*, tức danh
  sách các hàm đang gọi dở, giúp tìm chỗ gây lỗi.

*Trong Laravel*
- Exception handler cấu hình trong `bootstrap/app.php` qua `withExceptions()`.
  - `report()`: quyết định exception được log hoặc gửi đi đâu (Sentry, Slack...).
  - `render()`: quyết định exception biến thành response HTTP nào.

*Đối chiếu Java/Go*
- PHP không có *checked exception* như Java (loại exception bắt buộc phải khai báo `throws` hoặc
  bắt, nếu không thì compile lỗi). Mọi exception PHP giống unchecked exception của Java.
- Go không có exception, lỗi là một giá trị kiểu `error` được trả về và kiểm tra bằng `if err != nil`
  ([07-go.md](07-go.md)).

**Đọc**
- PHP: [Exceptions](https://www.php.net/manual/en/language.exceptions.php), [Errors in PHP 7](https://www.php.net/manual/en/language.errors.php7.php)
- Laravel: [Error Handling](https://laravel.com/docs/errors)

**Nắm chắc khi**
- [ ] Vẽ được cây `Throwable` và nói `TypeError` bắt bằng `catch` nào
- [ ] Giải thích được vì sao job Laravel "chết im lặng" khi code chỉ `catch (Exception)`

#### 1.5 Composer và PSR

📖 **Giáo trình:** [Chương 11. Namespace, autoload và Composer](kien-thuc/php/11-namespace-composer.md), [Chương 21. Chất lượng code: test, phân tích tĩnh, chuẩn code](kien-thuc/php/21-chat-luong-code.md)

**Vì sao cần học:** Mọi project PHP hiện đại đều đứng trên Composer. Lỗi deploy kiểu "máy dev
chạy, production vỡ" rất hay đến từ việc không commit `composer.lock` hoặc chạy nhầm `update`.
Người phỏng vấn thường hỏi `install` khác `update`, class được nạp thế nào, và PSR là gì.

**Học gì**

*Autoload và PSR-4*
- *Autoload*: thay vì viết `require` cho từng file, PHP cho đăng ký một hàm (qua
  `spl_autoload_register`). Khi code dùng một class chưa được nạp, PHP gọi hàm đó với tên class,
  và hàm tự tìm file để `require`.
- *PSR* (PHP Standards Recommendation) là các chuẩn chung do nhóm PHP-FIG đặt ra để thư viện của
  nhiều bên dùng chung được với nhau.
- PSR-4 là chuẩn map *namespace prefix* sang thư mục. Ví dụ với `"App\\": "app/"`:
  1. Code dùng `App\Models\User`, class chưa có.
  2. PHP gọi autoloader của Composer với tên `App\Models\User`.
  3. Autoloader thấy prefix `App\` map tới `app/`, đổi phần còn lại thành đường dẫn:
     `app/Models/User.php`.
  4. File tồn tại thì `require` nó. Chỉ những class **thật sự được dùng** mới được nạp.

*Tối ưu autoloader*
- `composer dump-autoload -o` sinh *classmap*: một mảng PHP lớn "tên class → đường dẫn file",
  tra một lần là thấy, không phải kiểm tra file tồn tại trên đĩa.
- `--classmap-authoritative` (`-a`): class không có trong classmap thì coi như không tồn tại, bỏ
  luôn bước tìm theo PSR-4.
  - ⚠️ Class được sinh ra lúc runtime (sau khi đã dump) sẽ không được tìm thấy.
- Deploy: `composer install --no-dev --optimize-autoloader` (bỏ package chỉ dùng khi dev, và sinh
  classmap).

*composer.json, composer.lock và semver*
- `composer.json` khai báo **ràng buộc**, ví dụ "cần `guzzlehttp/guzzle` bản 7.x".
  `composer.lock` ghi **phiên bản chính xác** đã được chọn, ví dụ `7.9.2`, kèm hash.

  | Lệnh | Đọc gì | Làm gì | Khi nào chạy |
  |---|---|---|---|
  | `composer install` | `composer.lock` | Cài đúng các bản trong lock | CI, deploy, máy dev mới clone |
  | `composer update` | `composer.json` | Resolve lại, chọn bản mới nhất thoả ràng buộc, ghi lại lock | Khi chủ động nâng dependency, trên máy dev |

- ⚠️ App phải commit `composer.lock`, để mọi môi trường cài đúng cùng một bộ phiên bản. Library
  thì lock của nó không ảnh hưởng project dùng nó (project đó resolve theo `composer.json` của
  library).
- *Semver* (semantic versioning): phiên bản `MAJOR.MINOR.PATCH`. Tăng MAJOR là có thay đổi phá vỡ
  tương thích. Các ràng buộc hay gặp:

  | Ràng buộc | Nghĩa | Vì sao |
  |---|---|---|
  | `^1.2.3` | `>=1.2.3 <2.0.0` | Cho mọi bản không đổi MAJOR |
  | `^0.3.1` | `>=0.3.1 <0.4.0` | Với 0.x, MINOR được coi là có thể phá vỡ |
  | `~1.2` | `>=1.2 <2.0` | `~` cho phép tăng chữ số cuối cùng được viết ra |
  | `~1.2.3` | `>=1.2.3 <1.3.0` | Chữ số cuối là PATCH, nên chỉ tăng PATCH |

- `composer audit` kiểm tra các package đang dùng có advisory bảo mật đã công bố không. Chạy trong CI.

*Các PSR cần biết*

| PSR | Về gì |
|---|---|
| 1, 12, và PER Coding Style | Quy tắc viết code (PER là bản kế thừa PSR-12) |
| 3 | Interface logger |
| 4 | Autoload |
| 6, 16 | Cache |
| 7, 17 | HTTP message (request/response bất biến) và factory tạo chúng |
| 11 | Container |
| 14 | Event dispatcher |
| 15 | HTTP middleware |
| 18 | HTTP client |
| 20 | Clock (lấy thời gian hiện tại, dễ giả lập khi test) |

- ⚠️ `Request` của Laravel dựa trên Symfony HttpFoundation, là object **mutable** (sửa được),
  **không** phải PSR-7. Khi cần tích hợp thư viện đòi PSR-7 thì dùng bridge chuyển đổi.

**Đọc**
- Composer: [Basic usage](https://getcomposer.org/doc/01-basic-usage.md) (phần lock file), [Versions and constraints](https://getcomposer.org/doc/articles/versions.md), [Autoloader optimization](https://getcomposer.org/doc/articles/autoloader-optimization.md) (so sánh level 1, 2/A, 2/B)
- PHP-FIG: [danh sách PSR](https://www.php-fig.org/psr/), [PSR-4](https://www.php-fig.org/psr/psr-4/), [PER Coding Style](https://www.php-fig.org/per/coding-style/)

**Nắm chắc khi**
- [ ] Giải thích được `composer install` và `composer update` khác nhau thế nào và khi nào chạy lệnh nào trên CI
- [ ] Nói được class `App\Models\User` được nạp từ file nào qua từng bước autoload
- [ ] Viết đúng ràng buộc cho "nhận mọi bản 2.x từ 2.4 trở lên"

#### 1.6 Laravel cơ bản

📖 **Giáo trình:** [Chương 23. Laravel: giới thiệu và cấu trúc dự án](kien-thuc/php/23-laravel-gioi-thieu.md), [Chương 24. Routing, controller và middleware](kien-thuc/php/24-laravel-routing-controller-middleware.md), [Chương 25. Request, validation, response và view](kien-thuc/php/25-laravel-request-validation-response.md)

**Vì sao cần học:** Đây là phần dùng hằng ngày, nhưng cũng là nơi có những lỗ hổng bảo mật phổ
biến nhất của app Laravel: mass assignment, IDOR, validation có race condition. Câu hỏi phỏng vấn
ở mức này thường là "chỉ ra lỗ hổng trong đoạn code này".

**Học gì**

*Skeleton từ Laravel 11*
- *Skeleton* là bộ khung thư mục của project mới. Từ Laravel 11 skeleton được làm tối giản:
  - Cấu hình middleware, exception và routing nằm trong `bootstrap/app.php`. Không còn
    `app/Http/Kernel.php`.
  - `routes/api.php` chỉ có khi chạy `php artisan install:api`.
  - Lịch chạy định kỳ (scheduler) khai báo trong `routes/console.php`.
- Mặc định của app mới:
  - DB là **SQLite**.
  - Queue, cache, session dùng driver **`database`** (lưu trong bảng DB).
  - ⚠️ Lên production với MySQL/Redis phải đổi `.env` tường minh (`DB_CONNECTION`,
    `QUEUE_CONNECTION`, `CACHE_STORE`, `SESSION_DRIVER`).

*Routing và route model binding*
- Route, route group (gom route chung prefix hoặc middleware).
- *Route model binding*: Laravel tự đổi tham số trên URL thành model.
  - *Implicit*: route `/posts/{post}` và controller nhận `Post $post` thì Laravel tự tìm theo id.
    `{post:slug}` thì tìm theo cột `slug`.
  - *Explicit*: tự khai báo cách tìm bằng `Route::bind()` hoặc `Route::model()`.
  - *Scoped binding*: `/users/{user}/posts/{post}` chỉ tìm post **thuộc** user đó.
- ⚠️ Binding chỉ trả lời "record này có tồn tại không", **không** trả lời "user hiện tại có được
  xem không". Thiếu kiểm tra quyền là lỗ hổng *IDOR* (Insecure Direct Object Reference): đổi id
  trên URL là xem được dữ liệu người khác. Phải có policy hoặc `authorize()`.

*Middleware*
- *Middleware* là lớp code chạy bọc quanh controller, xử lý request trước và response sau.
- Ba cấp: global (mọi request), group (`web`, `api`), route (gắn cho từng route).
- Chạy theo kiểu *củ hành* (pipeline):

  ```php
  public function handle(Request $request, Closure $next): Response
  {
      // chạy TRƯỚC controller, theo thứ tự đăng ký
      $response = $next($request);
      // chạy SAU controller, theo thứ tự ngược lại
      return $response;
  }
  ```
- Middleware nhận tham số sau dấu hai chấm, ví dụ `throttle:60,1` là 60 request mỗi 1 phút.

*Validation và Form Request*
- *Form Request* là class riêng chứa logic kiểm tra input của một request:
  - `authorize()`: user có được làm việc này không.
  - `rules()`: luật kiểm tra từng field.
  - `prepareForValidation()`: chuẩn hoá input trước khi kiểm (trim, đổi định dạng).
  - `after()`: kiểm tra thêm sau khi các rule đã chạy.
- Rule hay dùng: `bail` (dừng ở lỗi đầu tiên của field), `sometimes` (chỉ kiểm khi field có mặt),
  `nullable`, `exists:users,id`, `Rule::unique('users')->ignore($id)` (bỏ qua chính record đang sửa).
- ⚠️ Dùng `$request->validated()` hoặc `$request->safe()->only([...])` để lấy dữ liệu, không dùng
  `$request->all()`. `all()` trả cả những field không được validate.
- ⚠️ Rule `unique` có *race condition*: hai request đăng ký cùng email tới cùng lúc, cả hai cùng
  kiểm "chưa có", cả hai cùng qua, cả hai cùng insert. Phải có **unique index** ở DB làm hàng rào
  cuối cùng.

*Eloquent cơ bản và mass assignment*
- *Eloquent* là ORM của Laravel: mỗi bảng là một class model, mỗi dòng là một object.
- Relationship: `hasOne`, `hasMany`, `belongsTo`, `belongsToMany`.
- *Eager loading* `with('author')`: nạp sẵn relationship bằng một query riêng thay vì một query
  cho mỗi dòng (bài toán N+1, chi tiết ở [03-database-sql.md](03-database-sql.md) module 2.7).
- *Mass assignment* là gán nhiều attribute một lần từ một mảng, như `User::create($data)`.
  - `$fillable`: whitelist các field được gán hàng loạt.
  - `$guarded`: blacklist các field bị cấm. `$guarded = []` nghĩa là **tắt bảo vệ**.
  - ⚠️ Tấn công: gửi thêm `is_admin=1` trong form. Nếu code là `User::create($request->all())`
    và model có `$guarded = []`, user tự nâng mình thành admin.

*Artisan và công cụ đi kèm*
- *Artisan* là CLI của Laravel (`php artisan ...`).
- Migration (file mô tả thay đổi schema), seeder (đổ dữ liệu mẫu), factory (sinh model giả để test).
- `php artisan about`: in tổng quan môi trường, driver đang dùng, trạng thái cache. Lệnh đầu tiên
  nên chạy khi nhận một project lạ.

**Đọc**
- Laravel: [Directory Structure](https://laravel.com/docs/structure), [Routing](https://laravel.com/docs/routing) (mục [Route Model Binding](https://laravel.com/docs/routing#route-model-binding)), [Middleware](https://laravel.com/docs/middleware), [Validation](https://laravel.com/docs/validation) (mục [Form Request](https://laravel.com/docs/validation#form-request-validation)), [Eloquent: Mass Assignment](https://laravel.com/docs/eloquent#mass-assignment), [Installation](https://laravel.com/docs/installation) (phần *Databases and Migrations*)

**Nắm chắc khi**
- [ ] Tạo được project mới, đổi sang MySQL và queue Redis, giải thích từng biến `.env` đã đổi
- [ ] Viết được route `/users/{user}/posts/{post}` đảm bảo post thuộc user **và** user hiện tại được xem
- [ ] Chỉ ra được lỗ hổng trong `User::create($request->all())` khi model có `$guarded = []`

---

### Chặng 2: Làm chủ 🟡

#### 2.1 PHP hiện đại: 8.0 tới 8.5

📖 **Giáo trình:** [Chương 22. Tổng hợp PHP 8.0 tới 8.5](kien-thuc/php/22-phien-ban-moi.md)

**Vì sao cần học:** Codebase PHP thật thường kẹt ở 7.x hoặc 8.0 và cần nâng cấp. Người phỏng vấn
muốn biết bạn theo kịp ngôn ngữ, biết tính năng nào giải bài toán gì, và biết cái gì sẽ vỡ khi
nâng bản. Kể được tính năng của 8.4/8.5 kèm ví dụ dùng thật là điểm cộng rõ.

**Học gì**

*Bảng tính năng theo bản (chỉ liệt kê cái hay bị hỏi)*

| Bản | Tính năng |
|---|---|
| 8.0 | `match`, named arguments, nullsafe `?->`, constructor promotion, union type, `mixed`, attributes, JIT, `throw` là biểu thức, `WeakMap`, `str_contains`, `Stringable`, so sánh chuỗi/số mới |
| 8.1 | `enum` (pure, backed), `readonly` property, Fibers, first-class callable, `never`, intersection type, `new` trong initializer, `array_is_list` |
| 8.2 | `readonly` class, DNF type, `null`/`false`/`true` type, deprecated dynamic property, `#[\SensitiveParameter]`, extension Random |
| 8.3 | typed class constants, `#[\Override]`, `json_validate()`, dynamic class constant fetch |
| 8.4 | **property hooks**, **asymmetric visibility** (`public private(set)`), **lazy objects**, `array_find`/`array_find_key`/`array_any`/`array_all`, `#[\Deprecated]`, `new Foo()->bar()` không cần ngoặc, implicit nullable deprecated, bcrypt cost mặc định 10 → 12, JIT viết lại trên IR framework, `mb_trim`, PDO subclass theo driver (`Pdo\Mysql`) |
| 8.5 | **pipe operator `\|>`**, **clone with** `clone($obj, ['x' => 1])`, `#[\NoDiscard]`, `array_first`/`array_last`, **URI extension** (RFC 3986 và WHATWG), closure trong constant expression, backtrace cho fatal error, OPcache luôn được build sẵn, deprecate backtick operator và cast `(integer)`/`(boolean)` |

- Vài tính năng trong bảng cần giải thích ngắn:
  - *Named arguments*: gọi hàm theo tên tham số, `htmlspecialchars($s, double_encode: false)`.
  - *Nullsafe* `$user?->profile?->city`: gặp `null` ở đâu thì cả biểu thức trả `null`, không lỗi.
  - *Constructor promotion*: `public function __construct(private Repo $repo) {}` vừa khai báo vừa
    gán property.
  - *Pipe operator* (8.5): `$x |> trim(...) |> strtolower(...)` truyền kết quả vế trái làm tham số
    cho callable vế phải, đọc từ trái sang phải thay vì lồng `strtolower(trim($x))`.

*Enum*
- *Enum* là kiểu có tập giá trị cố định, ví dụ trạng thái đơn hàng.
  - *Pure enum*: `enum Suit { case Hearts; case Spades; }`, không gắn giá trị.
  - *Backed enum*: `enum Status: string { case Paid = 'paid'; }`, mỗi case gắn một giá trị int
    hoặc string để lưu DB.
- `Status::from('paid')` đổi giá trị thành case, sai thì ném lỗi. `tryFrom()` trả `null` thay vì
  ném. `cases()` trả danh sách mọi case.
- Enum có method và implement interface được, nhưng **không có state** (không có property thay đổi).

*Object bất biến: readonly, property hooks, asymmetric visibility, clone with*
- `readonly` property chỉ gán được **một lần**, và chỉ từ bên trong class. `readonly class` (8.2)
  làm mọi property readonly.
  - ⚠️ readonly là **nông**: property là object thì không gán lại được, nhưng nội dung object đó
    vẫn sửa được.
- Bài toán *wither*: object bất biến muốn "đổi một field" thì phải tạo bản mới, ví dụ
  `$money->withAmount(200)`. Với readonly class, trước 8.5 viết wither rất vướng vì không gán
  được property trên bản clone.
  - *Clone with* (8.5) giải bài này: `clone($this, ['amount' => 200])`.
- *Property hooks* (8.4): viết logic `get`/`set` ngay trên property, thay cho cặp getter/setter:

  ```php
  class User {
      public string $email {
          set => strtolower($value);   // chạy mỗi lần gán
      }
  }
  ```
- *Asymmetric visibility* (8.4): quyền đọc và ghi khác nhau, `public private(set) int $count`,
  tức bên ngoài đọc được nhưng chỉ class tự ghi.
- ⚠️ Property có hook không khai báo `readonly` cùng lúc được.

*Lazy objects và dynamic property*
- *Lazy object* (8.4): object mà việc khởi tạo thật bị hoãn tới lần truy cập đầu tiên. Có hai
  dạng:
  - *Ghost*: chính object đó, được khởi tạo tại chỗ khi dùng tới.
  - *Proxy*: object đứng thay, lần dùng đầu mới tạo object thật và chuyển mọi truy cập sang.
  - Chủ yếu cho framework/ORM (Doctrine, Symfony DI), ít khi viết tay.
- *Dynamic property* là gán property chưa khai báo, `$obj->foo = 1`. Từ 8.2 việc này
  bị deprecated, trừ `stdClass` và class gắn `#[\AllowDynamicProperties]`.
  - ⚠️ Gặp rất nhiều khi nâng code cũ.

*Attributes*
- *Attribute* là metadata gắn lên class, method, property, viết dạng `#[Route('/users')]`.
- Attribute **tự nó không làm gì**. Phải có code đọc nó bằng *Reflection* (API của PHP để đọc cấu
  trúc class, method lúc chạy), ví dụ `$ref->getAttributes()`, rồi hành động.
- Laravel 13 dùng nhiều, ví dụ `#[Middleware]`, `#[Tries]`.

*Generator và iterator*
- *Generator* là hàm có `yield`: mỗi lần `yield` trả một giá trị rồi **tạm dừng**, lần lặp sau chạy
  tiếp từ chỗ dừng. Nhờ vậy xử lý từng phần tử mà không cần giữ cả danh sách trong RAM.

  ```php
  function numbers(int $n): \Generator {
      for ($i = 1; $i <= $n; $i++) { yield $i; }
  }
  foreach (numbers(10_000_000) as $x) { /* RAM gần như không đổi */ }
  ```
- Cú pháp thêm: `yield $k => $v` (trả cả key), `yield from` (uỷ quyền cho generator khác),
  `send()` (đẩy giá trị vào generator), `getReturn()` (lấy giá trị `return` cuối).
- ⚠️ Generator chỉ duyệt được **một lần**. Duyệt lại thì phải gọi hàm tạo generator mới.
- `LazyCollection` của Laravel bọc generator để có API giống Collection.
- Các interface cho object tự định nghĩa cách duyệt và truy cập: `Iterator`, `IteratorAggregate`
  (duyệt bằng `foreach`), `ArrayAccess` (dùng `$obj['key']`), `Countable` (dùng `count($obj)`).

*Fibers*
- *Fiber* (8.1) là *coroutine* cấp thấp: một đoạn code có stack riêng, tự dừng giữa chừng
  (`Fiber::suspend()`) và được tiếp tục sau (`$fiber->resume()`).
- ⚠️ Fiber **không phải thread**: tại một thời điểm chỉ một fiber chạy.
- ⚠️ Fiber **không tự biến I/O thành non-blocking**. `PDO::query()` bên trong fiber vẫn chặn cả
  process tới khi DB trả lời. Phải có event loop và driver I/O viết riêng, như Revolt/AMPHP xây
  trên Fiber.

**Đọc**
- PHP release page: [8.4](https://www.php.net/releases/8.4/en.php), [8.5](https://www.php.net/releases/8.5/en.php) (có ví dụ trước/sau cho từng tính năng)
- PHP.Watch: [PHP 8.4](https://php.watch/versions/8.4), [PHP 8.5](https://php.watch/versions/8.5) (đọc cả mục *Deprecations* để biết cái sẽ vỡ khi nâng cấp)
- PHP manual: [Enumerations](https://www.php.net/manual/en/language.enumerations.php), [Property Hooks](https://www.php.net/manual/en/language.oop5.property-hooks.php), [Asymmetric visibility](https://www.php.net/manual/en/language.oop5.visibility.php#language.oop5.visibility-members-aviz), [Lazy Objects](https://www.php.net/manual/en/language.oop5.lazy-objects.php), [Attributes](https://www.php.net/manual/en/language.attributes.php), [Generators](https://www.php.net/manual/en/language.generators.php), [Fibers](https://www.php.net/manual/en/language.fibers.php), [URI](https://www.php.net/manual/en/book.uri.php)
- RFC (đọc phần *Proposal* và *Rejected features*): [Property hooks](https://wiki.php.net/rfc/property-hooks), [Asymmetric visibility v2](https://wiki.php.net/rfc/asymmetric-visibility-v2), [Lazy objects](https://wiki.php.net/rfc/lazy-objects), [array_find](https://wiki.php.net/rfc/array_find), [#\[\Deprecated\]](https://wiki.php.net/rfc/deprecated_attribute), [new without parentheses](https://wiki.php.net/rfc/new_without_parentheses), [bcrypt cost](https://wiki.php.net/rfc/bcrypt_cost_2023), [Pipe operator v3](https://wiki.php.net/rfc/pipe-operator-v3), [Clone with v2](https://wiki.php.net/rfc/clone_with_v2), [#\[\NoDiscard\]](https://wiki.php.net/rfc/marking_return_value_as_important), [array_first/array_last](https://wiki.php.net/rfc/array_first_last), [URL parsing API](https://wiki.php.net/rfc/url_parsing_api), [Fibers](https://wiki.php.net/rfc/fibers), [Deprecate dynamic properties](https://wiki.php.net/rfc/deprecate_dynamic_properties)

**Nắm chắc khi**
- [ ] Viết lại một value object PHP 7 (private property + getter + `withX()`) bằng readonly class, property hooks hoặc clone with, và nói cách nào hợp khi nào
- [ ] Liệt kê được 3 deprecation sẽ gặp khi nâng một codebase từ 8.1 lên 8.4/8.5
- [ ] Giải thích được vì sao Fibers không làm `PDO::query()` thành non-blocking

#### 2.2 PHP-FPM và mô hình share-nothing

📖 **Giáo trình:** [Chương 02. PHP chạy như thế nào](kien-thuc/php/02-php-chay-nhu-the-nao.md), [Chương 18. PHP-FPM, Nginx và OPcache trên production](kien-thuc/php/18-fpm-nginx-opcache.md)

**Vì sao cần học:** Gần như mọi app PHP production chạy sau PHP-FPM. Sự cố "502/504 lúc cao điểm",
"server swap", "request treo không bị cắt" đều nằm ở tầng này. Người phỏng vấn hỏi cách tính
`pm.max_children` để xem bạn đã từng vận hành thật hay chỉ viết code.

**Học gì**

*Kiến trúc master, pool, worker*
- *PHP-FPM* (FastCGI Process Manager) là chương trình chạy PHP cho web server. Cấu trúc:
  - Một *master process*: đọc cấu hình, tạo và quản lý worker, không chạy code PHP của bạn.
  - Một hoặc nhiều *pool*: mỗi pool là một nhóm worker có cấu hình riêng (user, socket, số worker).
  - Mỗi pool có nhiều *worker process*. Mỗi worker xử lý **một request tại một thời điểm**.
  - Hệ quả: số request chạy song song tối đa bằng tổng số worker.
- *FastCGI* là giao thức Nginx dùng để chuyển request cho FPM, qua unix socket (cùng máy) hoặc TCP.
- Một request đi thế này:
  1. Nginx nhận HTTP request, thấy cần chạy PHP.
  2. Nginx gửi request qua FastCGI tới socket của pool.
  3. Một worker đang rảnh nhận request. Nếu mọi worker đều bận, request **xếp hàng** trong
     backlog của socket (`listen.backlog`).
  4. Worker chạy script PHP từ đầu tới cuối, trả output cho Nginx.
  5. Worker dọn sạch state của request rồi quay lại chờ request tiếp.

*Mô hình share-nothing*
- *Share-nothing*: hết request thì mọi biến, object, kết nối không persistent đều bị giải phóng.
  Request sau bắt đầu từ trạng thái trắng.
- Lợi ích:
  - Leak hiếm khi tích tụ, vì RAM được dọn sau mỗi request.
  - Gần như không có bug state rò từ request này sang request khác.
- Cái giá: **mỗi request boot lại framework** (nạp config, đăng ký service...). Đó là lý do có
  `config:cache`, OPcache (module 2.3), và Octane (module 3.5).

*Process manager (`pm`)*
- *Process manager* là cách master quyết định giữ bao nhiêu worker:

  | `pm` | Hành vi | Khi nào dùng |
  |---|---|---|
  | `static` | Luôn giữ đúng `pm.max_children` worker | Server riêng cho app, tải ổn định, muốn latency đều |
  | `dynamic` | Giữ số worker rảnh trong khoảng `min_spare`–`max_spare`, tối đa `max_children` | Mặc định phổ biến, nhiều pool trên một máy |
  | `ondemand` | Chỉ fork khi có request, kill sau `process_idle_timeout` | Pool ít traffic; fork lúc có request làm tăng latency |

- *Fork* là tạo process con bằng cách nhân bản process hiện tại ([01-os-linux.md](01-os-linux.md)).

*Tính `pm.max_children`*
- *RSS* (Resident Set Size) là lượng RAM thật một process đang chiếm.
- Công thức: `pm.max_children` ≈ (RAM dành cho PHP) / (RSS trung bình mỗi worker).
  1. Lấy tổng RAM trừ phần của OS, Nginx, Redis... để ra RAM dành cho PHP.
  2. Đo RSS thật của worker lúc tải cao bằng `ps`, không đo lúc rảnh.
  3. Chia, rồi để dư biên. Ví dụ còn 6 GB, worker 60 MB thì khoảng 100.
- RSS đếm cả trang nhớ dùng chung giữa các worker (OPcache, thư viện) vào từng worker, nên chia
  theo RSS cho kết quả thấp hơn thực tế (an toàn nhưng lãng phí). Đo chính xác hơn bằng PSS hoặc
  USS (ví dụ `smem`), xem giáo trình chương 18.
- ⚠️ Không lấy `memory_limit` để chia. `memory_limit` là **trần** mỗi request, không phải mức dùng
  thật.
- ⚠️ Đặt quá cao: hết RAM, máy swap (đẩy RAM xuống đĩa, chậm hẳn), rồi *OOM killer* của Linux giết
  process. Đặt quá thấp: request xếp hàng ở `listen.backlog`, Nginx trả 502/504, log FPM có dòng
  "server reached pm.max_children".
- ⚠️ Giới hạn **downstream** (các hệ thống phía sau như DB): 100 worker × 4 server = 400 connection
  DB tiềm năng. Tính chi tiết ở [03-database-sql.md](03-database-sql.md) module 2.7.
- `pm.max_requests`: worker tự khởi động lại sau N request, chặn leak từ extension hoặc code. Mặc
  định 0 là không bao giờ khởi động lại.

*Timeout và giới hạn*
- `memory_limit`: trần RAM mỗi request. CLI dùng file ini riêng nên có thể khác FPM.
- `request_terminate_timeout`: FPM kill worker nếu một request chạy quá N giây **thời gian thực**.
- ⚠️ Trên Linux, `max_execution_time` chỉ tính thời gian CPU chạy script, **không tính** thời
  gian nằm trong system call, stream, chờ query DB. Request chờ API ngoài 5 phút vẫn không bị
  cắt.
  - Chặn theo thời gian thực bằng: `request_terminate_timeout`, timeout của HTTP client,
    `fastcgi_read_timeout` ở Nginx.
  - CLI mặc định `max_execution_time = 0`, tức không giới hạn.

*Quan sát*
- *Slow log*: đặt `request_slowlog_timeout` (ví dụ 5s) và `slowlog` (đường dẫn file). Request nào
  chạy quá ngưỡng thì FPM ghi **stack trace** lúc đó, tức request đang đứng ở hàm nào. Đây là công
  cụ rẻ nhất để tìm request chậm trên production.
- *Status page* (`pm.status_path`): số worker active/idle, *listen queue* (số request đang xếp
  hàng), *max children reached* (số lần chạm trần worker).
- `ping.path`: endpoint trả "pong", dùng cho health check.

**Đọc**
- PHP: [FPM](https://www.php.net/manual/en/install.fpm.php), [FPM Configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (mọi directive `pm.*`, `request_*`, `slowlog`), [FPM Status Page](https://www.php.net/manual/en/fpm.status.php)
- [`www.conf.in`](https://github.com/php/php-src/blob/master/sapi/fpm/www.conf.in) trong php-src: file mẫu có chú thích dài cho từng tham số, đọc kỹ phần `pm`
- PHP: [`max_execution_time`](https://www.php.net/manual/en/info.configuration.php#ini.max-execution-time) và ghi chú trong [set_time_limit](https://www.php.net/manual/en/function.set-time-limit.php), [`memory_limit`](https://www.php.net/manual/en/ini.core.php#ini.memory-limit)

**Nắm chắc khi**
- [ ] Tính được `pm.max_children` cho server 8 GB chạy Nginx + FPM + Redis từ số đo thật (bài tập 2)
- [ ] Đọc được một dòng slow log và chỉ ra request chậm ở hàm nào
- [ ] Giải thích được vì sao request gọi API treo 10 phút mà `max_execution_time = 30` không cắt

#### 2.3 OPcache và deploy

📖 **Giáo trình:** [Chương 18. PHP-FPM, Nginx và OPcache trên production](kien-thuc/php/18-fpm-nginx-opcache.md), [Chương 30. Laravel: kiểm thử, Octane và triển khai](kien-thuc/php/30-laravel-testing-octane-deploy.md)

**Vì sao cần học:** OPcache là lý do PHP đủ nhanh cho production, và cũng là thủ phạm quen thuộc
của sự cố "deploy xong vẫn chạy code cũ". Câu hỏi hay gặp: OPcache làm gì, vì sao sau deploy phải
reload FPM, vì sao `env()` trả `null`.

**Học gì**

*PHP chạy một file thế nào*
1. *Lexer* cắt mã nguồn thành các *token* (từ khoá, tên biến, dấu).
2. *Parser* dựng token thành *AST* (Abstract Syntax Tree), cây mô tả cấu trúc chương trình.
3. *Compiler* biến AST thành *opcode*: các lệnh đơn giản của máy ảo PHP, ví dụ `ASSIGN`, `ADD`,
   `DO_FCALL`.
4. *Zend VM* (máy ảo của PHP) chạy lần lượt các opcode.

- Không có OPcache thì **mỗi request** phải làm lại bước 1–3 cho **mọi file** được include. Một
  request Laravel nạp hàng trăm file.

*OPcache*
- OPcache lưu kết quả bước 3 (opcode) trong *shared memory*: vùng RAM mà nhiều process cùng đọc
  được. Mọi worker của cùng một FPM master dùng chung một cache.
  - Request sau chỉ còn bước 4.
- Từ 8.5 OPcache luôn được build vào PHP, không còn là extension tuỳ chọn. Vẫn tắt được bằng ini.
- OPcache biết file đổi bằng cách kiểm tra *mtime* (thời điểm sửa file):
  - `opcache.validate_timestamps=1`: kiểm mtime, tối đa mỗi `revalidate_freq` giây một lần.
  - Production thường đặt `0` (không bao giờ kiểm, đỡ tốn syscall), và **reload FPM khi deploy**
    để xoá cache.
- ⚠️ Cache đầy mà không báo lỗi. Ba tham số giới hạn:
  - `opcache.memory_consumption`: dung lượng cho opcode.
  - `opcache.interned_strings_buffer`: dung lượng cho chuỗi dùng chung (module 3.1).
  - `opcache.max_accelerated_files`: số file tối đa.
  - Một trong ba cái đầy thì file mới không được cache, hit rate tụt, app chậm dần mà không có lỗi
    rõ ràng. Riêng khi bộ nhớ bị lãng phí (wasted) vượt `opcache.max_wasted_percentage` thì OPcache
    lên lịch restart, xoá sạch cache. Theo dõi bằng `opcache_get_status()`.

*Deploy kiểu symlink và realpath cache*
- Deploy kiểu *symlink swap*: mỗi bản code nằm ở `releases/123`, và `current` là symlink trỏ tới
  bản mới nhất. Deploy là đổi symlink.
- ⚠️ Đổi symlink mà không reload FPM thì vẫn chạy code cũ, vì:
  - OPcache vẫn giữ key theo đường dẫn symlink (`current/...`) trỏ tới bản biên dịch của release
    cũ; với `validate_timestamps=0` key này không bao giờ bị kiểm lại.
  - *Realpath cache* của PHP (bộ nhớ đệm "symlink này trỏ tới đâu") vẫn nhớ đích cũ.
- Cách xử lý: reload FPM sau khi đổi symlink, hoặc cấu hình Nginx truyền `$realpath_root` thay vì
  `$document_root` để PHP nhận đường dẫn thật của bản mới.

*Quy trình deploy Laravel*
1. `composer install --no-dev -o`.
2. `php artisan optimize`: gộp `config:cache`, `route:cache`, `view:cache`, `event:cache`, tức
   biên dịch sẵn config, route, view Blade, danh sách event thành file PHP để khỏi tính lại mỗi
   request.
3. `php artisan migrate --force` (`--force` vì production mặc định hỏi xác nhận).
4. Reload FPM để xoá OPcache.
5. `php artisan queue:restart` để queue worker nạp code mới. Từ Laravel 12.x có `php artisan reload`
   gộp sẵn `queue:restart`, `schedule:interrupt` và lệnh reload của các package.

- ⚠️ Sau `config:cache`, file `.env` không được đọc nữa. `env()` gọi ở bất kỳ đâu ngoài
  `config/*.php` sẽ trả `null` với biến chỉ khai báo trong `.env` (biến môi trường thật của hệ
  thống vẫn đọc được, nên lỗi có thể chỉ xuất hiện ở một số môi trường).
  - Quy tắc: chỉ gọi `env()` trong file config, còn code dùng `config('app.x')`.
- ⚠️ Queue worker, Horizon, Octane là *process sống lâu*: nạp code một lần rồi chạy mãi. Không
  restart chúng thì vẫn chạy **code cũ**, dù FPM đã có code mới.

**Đọc**
- PHP: [OPcache runtime configuration](https://www.php.net/manual/en/opcache.configuration.php) (các mục [`validate_timestamps`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps), [`memory_consumption`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.memory-consumption), [`max_accelerated_files`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.max-accelerated-files)), [opcache_get_status](https://www.php.net/manual/en/function.opcache-get-status.php)
- RFC: [Make OPcache a non-optional part of PHP](https://wiki.php.net/rfc/make_opcache_required) (8.5)
- Laravel: [Deployment](https://laravel.com/docs/deployment) (mục [Optimization](https://laravel.com/docs/deployment#optimization)), [Configuration Caching](https://laravel.com/docs/configuration#configuration-caching), [Queue Workers and Deployment](https://laravel.com/docs/queues#queue-workers-and-deployment)
- Quy trình deploy tổng quát: [19-devops-cloud.md](19-devops-cloud.md)

**Nắm chắc khi**
- [ ] Viết được script deploy Laravel đủ bước, giải thích bỏ bước nào thì hỏng gì
- [ ] Liệt kê được 5 lý do "sau deploy vẫn chạy code cũ" và cách kiểm tra từng lý do
- [ ] Đọc được output `opcache_get_status()` và nói cache đã đầy chưa

#### 2.4 Lõi Laravel: lifecycle, container, provider, facade

📖 **Giáo trình:** [Chương 26. Service container, provider, facade và vòng đời request](kien-thuc/php/26-laravel-container-provider-facade.md)

**Vì sao cần học:** Service container là trái tim của Laravel: mọi thứ từ controller, facade tới
queue job đều đi qua nó. Người phỏng vấn senior Laravel gần như chắc chắn hỏi "container resolve
một class thế nào", "facade hoạt động ra sao bên dưới", và "`register` khác `boot` thế nào".

**Học gì**

*Request lifecycle*
- *Lifecycle* là chuỗi bước từ khi request vào tới khi response ra. Với Laravel trên FPM:
  1. Nginx gọi `public/index.php`.
  2. `vendor/autoload.php` đăng ký autoloader của Composer.
  3. `bootstrap/app.php` tạo `Application`. Object này **chính là service container**.
  4. HTTP Kernel nhận request (`Kernel::handle`) và chạy các *bootstrapper* theo thứ tự: nạp
     env, nạp config, đăng ký exception handler, đăng ký facade, **register** mọi service provider,
     rồi **boot** mọi service provider.
  5. Request đi qua global middleware.
  6. Router tìm route khớp, request đi qua middleware của group và của route.
  7. Controller chạy, trả response.
  8. Response đi ngược qua các middleware rồi được gửi về client.
  9. `terminate()`: chạy terminable middleware và các callback đăng ký `terminating`.

  ```text
  public/index.php → vendor/autoload.php → bootstrap/app.php (Application = container)
  → HTTP Kernel::handle → bootstrappers (env, config, exception handler, facades,
    register providers, boot providers)
  → global middleware → Router → route/group middleware → controller
  → Response gửi về client → terminate() (terminable middleware, callback terminating)
  ```
- Trên FPM toàn bộ chuỗi này chạy lại **mỗi request** (mô hình share-nothing, module 2.2).

*Service container: đăng ký*
- *Service container* là object biết cách tạo ra các object khác và các dependency của chúng. Code
  xin "cho tôi một `PaymentGateway`", container tạo và trả về.
- *Dependency injection* (DI): class nhận thứ nó cần qua constructor thay vì tự `new`. Container là
  công cụ làm DI tự động.
- Các cách đăng ký:

  | Cách | Mỗi lần resolve | Vòng đời instance |
  |---|---|---|
  | `bind` | Tạo mới | Không giữ |
  | `singleton` | Dùng lại một instance | Cả vòng đời app: FPM là một request; queue worker là **cả process**; Octane là cả process nếu tạo lúc boot (hoặc trong `warm`), còn tạo trong request thì bị bỏ cùng bản clone sau request |
  | `scoped` | Dùng lại trong một request/job | Được xoá giữa các request Octane và giữa các job |
  | `instance` | Trả object có sẵn đã đăng ký | Như singleton |

  ```php
  $this->app->bind(PaymentGateway::class, StripeGateway::class);
  $this->app->singleton(Clock::class, fn () => new SystemClock());
  ```
- Cách đăng ký khác:
  - *Contextual binding*: cùng một interface, class khác nhau nhận bản khác nhau.
    `$this->app->when(PhotoController::class)->needs(Filesystem::class)->give(...)`.
  - *Contextual attribute*: gắn attribute lên tham số constructor để lấy thẳng giá trị, ví dụ
    `#[Config('app.timezone')] string $tz`, `#[Storage('s3')] Filesystem $disk`.
  - *Tagging*: gắn nhãn cho nhiều binding rồi lấy tất cả một lần (`tagged('reports')`).
  - `extend`: bọc thêm lớp quanh service đã đăng ký (*decorate*).
  - `resolving` callback: chạy mỗi khi một kiểu được resolve.
  - Attribute `#[Singleton]`, `#[Scoped]`, `#[Bind]` đặt ngay trên class thay vì đăng ký trong
    provider.

*Service container: auto-wiring*
- *Auto-wiring*: container tự tìm ra dependency bằng cách đọc type hint của constructor, không cần
  đăng ký trước. Khi gọi `app(OrderService::class)`:
  1. Container kiểm tra có binding cho `OrderService` không. Không có và đây là class cụ thể thì
     tự build.
  2. Dùng `ReflectionClass` (API của PHP để đọc cấu trúc class lúc chạy) lấy constructor và danh
     sách tham số.
  3. Với mỗi tham số có type hint là class hoặc interface, **gọi đệ quy** bước 1 cho kiểu đó.
  4. Tạo `OrderService` với các dependency vừa có.

  Bản mini để hiểu ý tưởng:

  ```php
  function make(string $class): object {
      $ctor = (new ReflectionClass($class))->getConstructor();
      if ($ctor === null) { return new $class(); }
      $deps = array_map(
          fn (ReflectionParameter $p) => make($p->getType()->getName()),
          $ctor->getParameters(),
      );
      return new $class(...$deps);
  }
  ```
- ⚠️ Type hint là **interface** mà chưa bind thì container không biết chọn class nào, ném
  `BindingResolutionException`. Tham số scalar (`string $apiKey`) không có giá trị mặc định cũng
  không resolve được.
- ⚠️ Rải `app()` hoặc `resolve()` khắp domain code là *service locator*: class tự đi xin
  dependency thay vì nhận qua constructor. Dependency bị giấu, khó đọc và khó test.

*Service provider*
- *Service provider* là class nơi app đăng ký service vào container. Có hai method:
  - `register()`: **chỉ bind** vào container. Lúc này các provider khác có thể chưa đăng ký xong,
    nên không được dùng service khác ở đây.
  - `boot()`: chạy sau khi **mọi** provider đã register xong. Nơi đăng ký event listener, route,
    macro, observer.
- 🟡 *Deferred provider*: implement `DeferrableProvider` và khai báo `provides()`. Provider chỉ
  được nạp khi có code thật sự xin service nó cung cấp, đỡ tốn thời gian boot mỗi request.

*Facade*
- *Facade* là class cho gọi kiểu static (`Cache::get('k')`) nhưng thực ra chuyển lời gọi tới một
  object thật lấy từ container. Diễn biến:
  1. `Cache::get('k')`: class `Cache` không có static method `get`, nên PHP gọi
     `Facade::__callStatic('get', ['k'])` (magic method, module 1.3).
  2. `__callStatic` gọi `static::getFacadeRoot()`.
  3. `getFacadeRoot()` lấy tên dịch vụ từ `getFacadeAccessor()` (với `Cache` là `'cache'`) rồi gọi
     `app()->make('cache')`.
  4. Gọi `$instance->get('k')` trên object thật (cache manager, rồi tới store Redis).

  ```text
  Cache::get('k')
  → Facade::__callStatic('get', ['k'])
  → static::getFacadeRoot() → app()->make(static::getFacadeAccessor())   // 'cache'
  → $instance->get('k')
  ```
- Instance đã resolve được lưu vào một static property của facade, lần gọi sau không resolve lại.
- Test code dùng facade: `Cache::shouldReceive('get')->andReturn(...)` (mock), hoặc fake như
  `Queue::fake()`, `Mail::fake()`.
- *Real-time facade*: `use Facades\App\Services\Payment;` biến bất kỳ class nào thành facade.
- Tranh luận: facade giấu dependency (nhìn constructor không thấy class dùng cache). Chấp nhận ở
  controller và code mỏng, tránh trong domain logic quan trọng.

*Chạy sau khi gửi response*
- *Terminable middleware* (có method `terminate()`) và `defer()` chạy sau khi response đã gửi
  cho client. Trên FPM điều này nhờ hàm `fastcgi_finish_request()`: đóng kết nối với client nhưng
  worker chạy tiếp.
- ⚠️ Worker FPM **vẫn bị giữ** trong lúc chạy phần sau đó, không nhận request khác được. Không
  thay được queue cho việc nặng.

*Laravel 13*
- Attribute `#[Middleware]`, `#[Authorize]` gắn trên controller.
- `PreventRequestForgery`: middleware chống *CSRF* (trang web khác lừa trình duyệt của user gửi
  request kèm cookie đăng nhập), có kiểm tra thêm origin của request.

**Đọc**
- Laravel: [Request Lifecycle](https://laravel.com/docs/lifecycle), [Service Container](https://laravel.com/docs/container) (đọc hết, đặc biệt [Contextual Binding](https://laravel.com/docs/container#contextual-binding) và [Binding Scoped](https://laravel.com/docs/container#binding-scoped)), [Service Providers](https://laravel.com/docs/providers), [Facades](https://laravel.com/docs/facades) (mục [How Facades Work](https://laravel.com/docs/facades#how-facades-work)), [Terminable Middleware](https://laravel.com/docs/middleware#terminable-middleware), [Deferred Functions](https://laravel.com/docs/helpers#deferred-functions)
- Source: [`Container.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Container/Container.php) (hàm `build()` và `resolveDependencies()`), [`Facade.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Support/Facades/Facade.php), [`Http/Kernel.php`](https://github.com/laravel/framework/blob/13.x/src/Illuminate/Foundation/Http/Kernel.php), [`bootstrap/app.php`](https://github.com/laravel/laravel/blob/13.x/bootstrap/app.php) của skeleton
- PHP: [fastcgi_finish_request](https://www.php.net/manual/en/function.fastcgi-finish-request.php)

**Nắm chắc khi**
- [ ] Vẽ được lifecycle từ `index.php` tới terminable middleware, đánh dấu `register`/`boot` ở đâu (bài tập 3)
- [ ] Tự viết được container mini 30 dòng có auto-wiring bằng Reflection
- [ ] Giải thích được `Cache::get()` đi qua những hàm nào tới Redis
- [ ] Nói được singleton trong FPM và trong Octane khác nhau thế nào về vòng đời

#### 2.5 Eloquent ở mức làm chủ

📖 **Giáo trình:** [Chương 27. Database trong Laravel: migration, query builder, Eloquent](kien-thuc/php/27-laravel-database-eloquent.md)

**Vì sao cần học:** Eloquent là nơi code Laravel dành nhiều thời gian nhất, và cũng là nơi có
nhiều hành vi ngầm nhất: event không bắn, scope lọc mất dữ liệu, accessor gây N+1. Người phỏng vấn
hay đưa một tình huống "observer không chạy" hoặc "báo cáo thiếu dữ liệu" để xem bạn biết Eloquent
làm gì bên dưới.

Phần tầng DB (PDO, connection, N+1, transaction, `chunk`/`cursor`, read/write connection,
ORM sinh SQL tệ) đã có ở [03-database-sql.md](03-database-sql.md) **module 2.7**. Module này
chỉ bổ sung phần thuộc về model.

**Học gì**

*Relationship nâng cao*
- `hasOneThrough`, `hasManyThrough`: đi qua một bảng trung gian. Ví dụ `Country` → `User` → `Post`,
  lấy mọi post của một nước.
- `belongsToMany`: quan hệ n-n qua *pivot table* (bảng nối). `withPivot('role')` để lấy thêm cột
  của bảng nối.
- *Polymorphic*: một bảng thuộc về nhiều loại model. Ví dụ bảng `comments` có `commentable_type`
  và `commentable_id`, comment gắn được vào `Post` hoặc `Video`.
  - ⚠️ Mặc định cột `_type` lưu **tên class đầy đủ** (`App\Models\Post`). Đổi tên class là dữ liệu
    cũ gãy. Dùng `Relation::enforceMorphMap(['post' => Post::class])` để lưu tên ngắn cố định.
  - Cái giá: không có khoá ngoại được, vì `commentable_id` trỏ tới nhiều bảng.

*Eager loading nâng cao và strict mode*
- *Constrained eager loading*: nạp relationship kèm điều kiện,
  `Post::with(['comments' => fn ($q) => $q->where('approved', true)])`.
- `withCount('comments')`, `withSum('items', 'price')`, `withExists('likes')`: lấy số liệu tổng
  hợp mà không nạp cả relationship.
- `loadMissing('author')`: chỉ nạp nếu chưa nạp.
- *Automatic eager loading* (Laravel 12+): tự eager load khi phát hiện truy cập relationship trong
  vòng lặp.

- `Model::shouldBeStrict()` bật ba kiểm tra cùng lúc:
  1. Chặn *lazy loading* (truy cập relationship chưa nạp, nguyên nhân của N+1).
  2. Chặn việc gán attribute không nằm trong `$fillable` mà bị bỏ qua âm thầm.
  3. Chặn truy cập attribute không tồn tại (thường do gõ sai tên hoặc quên select cột).
- Bật ở môi trường non-production, ví dụ `Model::shouldBeStrict(! app()->isProduction())`.

*Cast, accessor, mutator*
- *Cast*: tự đổi kiểu khi đọc từ DB và khi ghi vào DB. Khai báo trong method `casts()` (từ
  Laravel 11):
  - `array` (JSON ↔ array), `datetime`, `decimal:2`, `encrypted`, `hashed` (tự hash khi gán),
    enum, hoặc class tự viết implement `CastsAttributes`.
  - ⚠️ Cast `float` cho tiền làm sai số ([22-practical-data.md](22-practical-data.md)).
- *Accessor* (biến đổi khi đọc) và *mutator* (biến đổi khi ghi): viết bằng
  `Attribute::make(get: fn ($v) => ..., set: fn ($v) => ...)`.
- ⚠️ Accessor có chạy query, lại được thêm vào `$appends` (tự đưa vào JSON khi serialize): trả
  một danh sách 100 model ra JSON là 100 query ẩn.

*Scope*
- *Local scope*: đóng gói điều kiện hay dùng. Method `scopeActive($q)` (hoặc gắn attribute
  `#[Scope]`), gọi `User::active()`.
- *Global scope*: điều kiện tự thêm vào **mọi** query của model, ví dụ lọc theo tenant.
  - ⚠️ Dễ làm query "thiếu dữ liệu" bất ngờ, vì người đọc query không thấy điều kiện đó.
    Bỏ bằng `withoutGlobalScope()`.

*Model event và observer*
- Eloquent bắn event quanh vòng đời model: `creating`, `created`, `updating`, `updated`, `saving`,
  `saved`, `deleting`, `deleted`... *Observer* là class gom các handler của những event đó.
- ⚠️ Các lệnh trên **query builder** không tạo object model (không *hydrate*, tức không dựng model
  từ dòng DB), nên **không** bắn event, **không** chạy observer, **không** áp cast:

  ```php
  $order->update(['status' => 'paid']);                      // có event, observer chạy
  Order::where('id', $id)->update(['status' => 'paid']);     // KHÔNG có event
  ```
  - Cùng nhóm: `insert()`, `upsert()`, `delete()` gọi trên builder.
- `saveQuietly()`, `Model::withoutEvents(fn)`: lưu mà không bắn event.
- ⚠️ Logic nghiệp vụ giấu trong observer khó lần: đọc controller không biết có email được gửi. Hay
  gây side effect bất ngờ khi seed hoặc import dữ liệu.

*Soft delete*
- *Soft delete*: không xoá dòng mà ghi thời điểm vào `deleted_at`. Eloquent thêm global scope
  `whereNull('deleted_at')` để ẩn các dòng đó.
- ⚠️ Cạm bẫy:
  - Unique index va chạm với bản ghi đã xoá mềm: xoá user email `a@x.com` rồi đăng ký lại cùng
    email thì lỗi trùng. Cách xử lý ở module 2.8 của [03-database-sql.md](03-database-sql.md).
  - Raw query, join, báo cáo viết tay quên điều kiện `deleted_at IS NULL`.

*Query builder, Eloquent, và kiến trúc*
- Query builder (`DB::table('orders')`) nhanh hơn Eloquent vì không dựng model, không event, không
  cast. Hợp cho báo cáo và thao tác hàng loạt.
- ⚠️ `whereRaw("name = '$name'")` là SQL injection. Dùng `whereRaw('name = ?', [$name])`. Tên cột
  để sort lấy từ input phải kiểm theo whitelist, vì tên cột không bind được bằng `?`.
- *Active Record* (Eloquent): object model vừa chứa dữ liệu vừa tự lưu mình (`$user->save()`).
  *Data Mapper* (Doctrine): entity là object thuần, một lớp riêng lo lưu xuống DB. Hệ quả với
  domain phức tạp ở module 3.8.

**Đọc**
- Laravel: [Eloquent Relationships](https://laravel.com/docs/eloquent-relationships) (mục [Eager Loading](https://laravel.com/docs/eloquent-relationships#eager-loading), [Automatic Eager Loading](https://laravel.com/docs/eloquent-relationships#automatic-eager-loading), [Custom Polymorphic Types](https://laravel.com/docs/eloquent-relationships#custom-polymorphic-types)), [Mutators & Casting](https://laravel.com/docs/eloquent-mutators), [Eloquent](https://laravel.com/docs/eloquent) (mục [Strictness](https://laravel.com/docs/eloquent#configuring-eloquent-strictness), [Mass Updates](https://laravel.com/docs/eloquent#mass-updates), [Global Scopes](https://laravel.com/docs/eloquent#global-scopes), [Observers](https://laravel.com/docs/eloquent#observers))
- Martin Fowler: [Active Record](https://martinfowler.com/eaaCatalog/activeRecord.html), [Data Mapper](https://martinfowler.com/eaaCatalog/dataMapper.html)

**Nắm chắc khi**
- [ ] Chỉ ra được vì sao observer gửi email khi `updated` không chạy với `Order::where(...)->update()`
- [ ] Bật `shouldBeStrict()` trên một project thật và sửa hết lỗi nó bắn ra
- [ ] Thiết kế được polymorphic `comments` có morph map, và nói được cái giá (không có khoá ngoại)

#### 2.6 Queue

📖 **Giáo trình:** [Chương 29. Queue, event, scheduler, cache, mail và notification](kien-thuc/php/29-laravel-queue-event-schedule-cache.md)

**Vì sao cần học:** Mọi việc chậm hoặc có thể lỗi (gửi email, gọi API đối tác, xử lý file) đều
nên đưa vào queue. Queue cũng là nơi sinh ra các bug khó nhất: job chạy hai lần, job chết không
ai biết, worker chạy code cũ. Người phỏng vấn rất hay hỏi quan hệ giữa `retry_after` và `timeout`.

**Học gì**

*Driver và worker*
- *Queue* là hàng đợi công việc: request đẩy *job* (một đơn vị việc) vào, *worker* (process chạy
  nền) lấy ra và xử lý.
- Driver (nơi lưu hàng đợi): `sync` (chạy ngay, chỉ dev), `database` (mặc định từ Laravel 11),
  `redis`, `sqs`, `beanstalkd`.
- `queue:work` boot framework **một lần** rồi xử lý job liên tục. `queue:listen` boot lại mỗi job,
  chậm, chỉ dùng khi dev.
- Tuỳ chọn của worker:
  - `--queue=high,default,low`: thứ tự ưu tiên, hết job ở `high` mới lấy `default`.
  - `--tries`, `--backoff` (chờ bao lâu trước khi thử lại), `--timeout`.
  - `--memory`, `--max-jobs`, `--max-time`: tự thoát khi vượt ngưỡng để được khởi động lại.
  - `--sleep`: nghỉ bao lâu khi hàng đợi trống.
- Laravel 13: `Queue::route()` định tuyến job vào queue theo class.

*Cấu hình trên job*
- Property: `$tries` (số lần thử), `$backoff` (mảng thì tăng dần, ví dụ `[10, 60, 300]`),
  `$timeout`, `$maxExceptions` (số exception tối đa, khác số lần thử), `$failOnTimeout`.
- `retryUntil()`: thử lại tới một thời điểm, thay vì đếm số lần.
- Laravel 13 có attribute tương ứng: `#[Tries]`, `#[Backoff]`, `#[Timeout]`, `#[FailOnTimeout]`.
- `timeout` cần extension `pcntl` (điều khiển process và signal) để worker tự ngắt job chạy quá giờ.

*retry_after và timeout*
- `retry_after` (trong config connection, mặc định 90 giây): nếu một job đã được lấy ra quá
  `retry_after` giây mà chưa xong, queue coi như worker đã chết và cho job đó hiện lại để worker
  khác lấy.
- ⚠️ `retry_after` phải **lớn hơn** `timeout` của job dài nhất. Nếu không, với job cần 120 giây và
  `retry_after = 90`:
  1. Giây 0: worker A lấy job, bắt đầu chạy.
  2. Giây 90: job chưa xong, queue tưởng A đã chết, cho job hiện lại.
  3. Worker B lấy job và chạy từ đầu. Giờ **hai worker chạy cùng một job song song**.
  4. Giây 120: A xong. B vẫn đang chạy, và sẽ làm lại mọi việc A vừa làm (gửi email lần hai, trừ
     tiền lần hai).

*Idempotent và job thất bại*
- *Idempotent*: chạy một lần hay nhiều lần cho cùng một kết quả.
- ⚠️ Job **phải idempotent**, vì có nhiều đường khiến một job chạy lại: retry, timeout, worker chết
  giữa chừng, SQS giao *at-least-once* (ít nhất một lần, có thể nhiều hơn).
  - Cách làm: *idempotency key* (mã duy nhất cho mỗi thao tác), unique constraint ở DB, kiểm trạng
    thái trước khi làm ("đơn đã thanh toán thì bỏ qua").
  - Lý thuyết delivery semantics: [12-messaging.md](12-messaging.md).
- Job thử hết lượt thì vào bảng `failed_jobs`, và method `failed()` của job được gọi.
  - `queue:retry` đẩy lại job lỗi, `queue:prune-failed` dọn bảng.
  - Lỗi biết chắc là vĩnh viễn (dữ liệu sai) thì gọi `$this->fail()` ngay, không phí lượt thử.

*Điều phối job: chain, batch, unique job, job middleware*
- *Chain* (`Bus::chain([...])`): các job chạy lần lượt, một job fail thì dừng cả chuỗi.
- *Batch* (`Bus::batch([...])->then()->catch()->finally()`): nhóm job chạy song song, có callback
  khi xong hoặc lỗi. Job cần trait `Batchable`. `allowFailures()` để một job lỗi không huỷ cả batch.
- *Unique job*: implement `ShouldBeUnique`, khai báo `uniqueId()` và `$uniqueFor`. Trong thời gian
  đó không dispatch được job trùng id.
  - `ShouldBeUniqueUntilProcessing`: chỉ giữ unique tới khi job bắt đầu chạy.
  - Bên dưới dựa trên cache lock, nên cần cache dùng chung giữa các server.

- *Job middleware* bọc quanh job, giống middleware HTTP:
  - `RateLimited`: giới hạn tần suất.
  - `WithoutOverlapping`: không cho hai job cùng key chạy đồng thời. `releaseAfter` (đẩy lại sau
    N giây), `expireAfter` (lock tự hết hạn). ⚠️ Mặc định lock **không bao giờ hết hạn**: worker bị kill giữa
    chừng thì lock treo mãi, nên luôn đặt `expireAfter`.
  - `ThrottlesExceptions`: gặp lỗi liên tiếp thì tạm hoãn.
  - `Skip`: bỏ qua job theo điều kiện.
- ⚠️ Job bị `release()` (đẩy lại hàng đợi, ví dụ do rate limit) vẫn tính là một **attempt**. `tries`
  nhỏ cộng rate limit chặt thì job fail oan dù chưa từng chạy thật. Dùng `retryUntil()`.

*Model trong job và transaction*
- ⚠️ `SerializesModels`: khi dispatch, model chỉ được lưu dạng class + id. Lúc job chạy thì query
  lại từ DB. Hệ quả:
  - Model đã bị xoá thì ném `ModelNotFoundException`. Đặt `$deleteWhenMissingModels = true` để bỏ
    job luôn.
  - Dữ liệu đổi giữa lúc dispatch và lúc chạy thì job thấy bản **mới**.
  - Relationship đã load cũng được lưu, làm payload phình to.
- ⚠️ Dispatch bên trong transaction: job có thể chạy trước khi transaction commit. Sửa bằng
  `afterCommit` (chi tiết ở module 2.7 của [03-database-sql.md](03-database-sql.md)).

*Horizon, restart và supervisor*
- *Horizon*: dashboard và bộ quản lý worker cho queue Redis (chỉ Redis).
  - Cấu hình supervisor bằng code, chiến lược cân bằng số worker `simple`, `auto`, `false`, có tag
    để lọc job.
  - Deploy bằng `horizon:terminate`.
- `queue:restart` không kill worker ngay. Nó ghi một timestamp vào **cache**; mỗi worker kiểm
  timestamp ở cuối mỗi vòng lặp (sau mỗi job, cả khi queue rỗng) và tự thoát êm nếu thấy mới hơn lúc nó khởi động.
  - ⚠️ Cần cache dùng chung giữa các server (Redis, không phải `file`), và cần *process manager*
    (supervisor, systemd, Kubernetes) để khởi động worker lại sau khi nó thoát.
- *Supervisor* (chương trình quản lý process trên Linux): `numprocs` (số worker), `autorestart`.
  - ⚠️ `stopwaitsecs` (thời gian chờ worker tự dừng trước khi bị kill) phải lớn hơn timeout của
    job dài nhất, nếu không job bị giết giữa chừng mỗi lần deploy.

**Đọc**
- Laravel: [Queues](https://laravel.com/docs/queues), đọc hết. Quan trọng nhất: [Max Attempts and Timeout](https://laravel.com/docs/queues#max-job-attempts-and-timeout), [Job Expiration and Timeouts](https://laravel.com/docs/queues#job-expirations-and-timeouts) (quan hệ `retry_after` và `timeout`), [Job Middleware](https://laravel.com/docs/queues#job-middleware), [Unique Jobs](https://laravel.com/docs/queues#unique-jobs), [Handling Relationships](https://laravel.com/docs/queues#handling-relationships), [Supervisor Configuration](https://laravel.com/docs/queues#supervisor-configuration)
- Laravel: [Horizon](https://laravel.com/docs/horizon) (mục [Balancing Strategies](https://laravel.com/docs/horizon#balancing-strategies), [Deploying Horizon](https://laravel.com/docs/horizon#deploying-horizon))

**Nắm chắc khi**
- [ ] Giải thích được từng bước vì sao job 120 giây với `retry_after = 90` bị chạy ít nhất hai lần
- [ ] Thiết kế được job gọi API bị giới hạn 60 request/phút, idempotent, không chạy trùng theo `order_id` (bài tập 4)
- [ ] Viết được cấu hình supervisor cho worker và giải thích `stopwaitsecs`

#### 2.7 Các thành phần khác của Laravel

📖 **Giáo trình:** [Chương 28. Xác thực và phân quyền trong Laravel](kien-thuc/php/28-laravel-auth.md), [Chương 29. Queue, event, scheduler, cache, mail và notification](kien-thuc/php/29-laravel-queue-event-schedule-cache.md)

**Vì sao cần học:** Scheduler, cache, event, auth là những phần gần như app nào cũng dùng, và lỗi
của chúng chỉ lộ ra khi scale lên nhiều server: task chạy ba lần, session mất, cache stampede.
Người phỏng vấn thường hỏi theo kiểu tình huống "sau khi thêm server thì X bị hỏng".

**Học gì**

*Scheduler*
- Chỉ cần **một** dòng cron chạy `php artisan schedule:run` mỗi phút. Laravel tự quyết task nào
  đến giờ. Task khai báo trong `routes/console.php`.
- ⚠️ Có N server cùng chạy cron thì mỗi task chạy N lần.
  - `->onOneServer()`: server đầu tiên lấy được lock mới chạy. Cần cache lock **dùng chung** (Redis,
    Memcached, database, DynamoDB).
- `->withoutOverlapping()`: không chạy lần mới khi lần trước chưa xong.
  - ⚠️ Lock mặc định hết hạn sau **24 giờ**. Process chết giữa chừng thì lock không được nhả, task
    kẹt tới khi lock hết hạn.
- `->runInBackground()` (không chặn các task khác cùng phút), `->timezone()`.

*Cache*
- `Cache::remember($key, $ttl, fn)`: có thì trả, chưa có thì tính rồi lưu. `rememberForever`,
  `increment`.
- *Tag*: gắn nhãn cho nhiều key để xoá cả nhóm. ⚠️ Không hỗ trợ ở driver `file`, `database`,
  `dynamodb`.
- *Atomic lock* `Cache::lock('k', 10)->block(5, fn)`: khoá phân tán qua cache. Chỉ *owner* (bên đã
  lấy lock) mới release được.
- *Cache stampede*: key hết hạn đúng lúc nhiều request cùng tới, tất cả cùng tính lại, dồn tải vào
  DB. ⚠️ `remember` thường **không** chống được ([11-cache.md](11-cache.md)).
  - `Cache::flexible($key, [fresh, stale], fn)`: *stale-while-revalidate*. Trong khoảng `fresh` trả
    bản cache. Trong khoảng `stale` vẫn trả bản cũ ngay, và tính lại **sau khi gửi response**.
- `Cache::memo()` (từ Laravel 12) nhớ kết quả trong phạm vi một request, khỏi gọi Redis lặp lại.
  Laravel 13 thêm `Cache::touch()` gia hạn TTL không cần đọc lại giá trị.

*Session và rate limiting*
- Driver session: `file`, `database`, `redis`.
  - ⚠️ `file` hỏng khi có nhiều server sau load balancer: session nằm trên đĩa server A, request
    sau vào server B thì không thấy, user bị đăng xuất.
- Rate limiting: định nghĩa bằng `RateLimiter::for('api', fn)`, gắn vào route bằng middleware
  `throttle:api`.

*Event, notification, broadcasting*
- *Event/listener*: code bắn event, các listener đăng ký sẽ chạy.
  - Listener implement `ShouldQueue` thì chạy trong queue.
  - `ShouldHandleEventsAfterCommit`: chỉ chạy sau khi transaction commit.
  - ⚠️ Listener đồng bộ và chậm làm request chậm. Listener ném lỗi làm hỏng cả request.
- *Notification*: gửi thông báo qua nhiều kênh, chọn kênh trong `via()`. On-demand notification
  gửi cho địa chỉ không phải user trong DB.
- 🟡 *Broadcasting*: đẩy event xuống trình duyệt qua WebSocket. Server: Reverb, Pusher, Ably.
  Client: Laravel Echo. Private channel (cần xác thực), presence channel (biết ai đang online).

*Auth*
- *Guard*: **cách** xác thực (session cookie, token). *Provider*: lấy user **từ đâu** (bảng
  `users` qua Eloquent...).
- *Sanctum*: gói auth nhẹ, hai chế độ:
  - SPA mode: SPA cùng domain gốc dùng cookie session + CSRF, như web thường.
  - Token mode: *personal access token*, DB chỉ lưu **hash** của token, token có *abilities*
    (quyền hạn).
  - Sanctum **không** phải OAuth2.
- *Passport*: OAuth2 server đầy đủ. Chỉ dùng khi thật sự cần, ví dụ bên thứ ba đăng nhập bằng tài
  khoản hệ thống của bạn.
- Phân quyền: *Gate* (closure kiểm quyền), *Policy* (class gom quyền theo model), `Gate::before()`
  (chạy trước mọi kiểm tra, ví dụ cho super admin qua hết).
- Lý thuyết JWT/session/OAuth: [10-security.md](10-security.md).

*Tiện ích nên biết (nhiều cái có từ trước Laravel 11)*

| Công cụ | Làm gì | Cạm bẫy |
|---|---|---|
| `defer(fn)` | Chạy sau khi response đã gửi, chỉ khi request thành công (trừ khi gọi `->always()`) | Vẫn giữ worker FPM trong lúc chạy |
| `Concurrency::run([...])` | Chạy nhiều closure song song bằng **process PHP con** (driver `process` mặc định, `fork` chỉ ở CLI) | ⚠️ Closure bị serialize sang process khác, không chia sẻ biến; không phải thread |
| `Context` | Gắn dữ liệu (request id, tenant) vào mọi dòng log, và **tự truyền sang queued job** | |
| `Http::pool()` | Gửi nhiều HTTP request song song | |
| `Process` facade | Chạy lệnh ngoài có timeout, tham số dạng mảng | |

- Laravel 13 thêm: JSON:API resources, vector search (`whereVectorSimilarTo` trên Postgres +
  pgvector), Laravel AI SDK ([23-ai-llm-backend.md](23-ai-llm-backend.md)).

**Đọc**
- Laravel: [Task Scheduling](https://laravel.com/docs/scheduling) (mục [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server)), [Cache](https://laravel.com/docs/cache) (mục [Stale While Revalidate](https://laravel.com/docs/cache#swr), [Atomic Locks](https://laravel.com/docs/cache#atomic-locks)), [Events](https://laravel.com/docs/events) (mục [Queued Event Listeners](https://laravel.com/docs/events#queued-event-listeners)), [Sanctum](https://laravel.com/docs/sanctum) (mục [How it Works](https://laravel.com/docs/sanctum#how-it-works)), [Authorization](https://laravel.com/docs/authorization), [Broadcasting](https://laravel.com/docs/broadcasting)
- Laravel: [Concurrency](https://laravel.com/docs/concurrency) (mục [How it Works](https://laravel.com/docs/concurrency#how-it-works)), [Context](https://laravel.com/docs/context), [HTTP Client: Concurrent Requests](https://laravel.com/docs/http-client#concurrent-requests), [Processes](https://laravel.com/docs/processes)
- Laravel: [Release Notes](https://laravel.com/docs/releases) (bảng support policy và tính năng 13), [Upgrade Guide](https://laravel.com/docs/upgrade)

**Nắm chắc khi**
- [ ] Giải thích được vì sao scheduler gửi báo cáo 3 lần sau khi scale lên 3 server và sửa được theo 2 cách
- [ ] Chọn đúng giữa `defer()`, queued job và `Concurrency::run()` cho 3 ca: ghi metric, gửi email, gọi 3 API cùng lúc
- [ ] Giải thích được Sanctum SPA mode và token mode khác nhau thế nào, khi nào cần Passport

#### 2.8 Chất lượng code PHP: PHPStan, Rector, Pint

📖 **Giáo trình:** [Chương 21. Chất lượng code: test, phân tích tĩnh, chuẩn code](kien-thuc/php/21-chat-luong-code.md)

**Vì sao cần học:** PHP không có bước compile kiểm kiểu, nên lỗi kiểu chỉ lộ ra khi code chạy tới,
thường là trên production. Static analysis và formatter là cách team PHP giữ chất lượng khi
codebase lớn. Câu hỏi hay gặp: "đưa PHPStan vào codebase cũ thế nào mà không bắt cả team dừng lại".

**Học gì**

*Vì sao cần static analysis*
- *Static analysis* là đọc code mà không chạy nó để tìm lỗi: gọi method không tồn tại, truyền sai
  kiểu, biến có thể `null`.
- PHP chỉ kiểm kiểu lúc chạy. Vì vậy static analysis gần như là **compiler thứ hai**, bắt lỗi trước
  khi code lên production.

*PHPStan*
- PHPStan 2.x có *rule level* từ 0 tới 10, level càng cao càng khắt khe. Level 10 mới có từ 2.0,
  siết cả giá trị `mixed` ngầm (giá trị không rõ kiểu). `--level max` là level cao nhất.
- Kiểu chi tiết khai báo trong PHPDoc mà PHP không có sẵn:
  - *Generics*: `array<int, User>` (array key int, value là `User`), `Collection<int, Order>`.
  - `list<string>`: array là list các chuỗi.
  - *Array shape*: `array{id: int, name: string}`.
- Đưa vào codebase cũ:
  1. Cài PHPStan và Larastan.
  2. Bắt đầu ở level thấp, hoặc tạo *baseline*: file ghi nhận toàn bộ lỗi hiện có để tạm bỏ qua.
  3. CI chặn **lỗi mới**, lỗi cũ trong baseline sửa dần.
  4. Nâng level từng bước.
- *Larastan*: extension của PHPStan cho Laravel, hiểu facade, magic của Eloquent, relationship.
- Psalm là công cụ thay thế, mạnh ở *taint analysis* (lần dữ liệu từ input người dùng tới chỗ nguy
  hiểm như SQL) cho bảo mật.

*Rector*
- *Rector* sửa code tự động theo rule: nâng cú pháp PHP 7.4 lên 8.4, thêm type, bỏ code chết.
- `rector-laravel` chứa rule cho nâng cấp Laravel.
- Chạy `--dry-run` trong CI để chỉ báo diff, không sửa.

*Formatter*
- *Formatter* tự sắp xếp code theo một style thống nhất (thụt lề, dấu cách, xuống dòng).
- Laravel Pint bọc PHP-CS-Fixer, có preset `laravel`, `psr12`, `per`. Hoặc dùng PHP-CS-Fixer trực
  tiếp.
- Chạy trong pre-commit hoặc CI để lúc review không phải bàn chuyện dấu cách.

*Kiểm tra khi nâng cấp và test*
- `composer audit` (lỗ hổng đã biết) và `phpstan-deprecation-rules` (báo code dùng thứ đã
  deprecated) trước khi nâng PHP hoặc Laravel.
- Test: PHPUnit, Pest, và các fake của Laravel. Chiến lược chi tiết ở
  [20-testing-quality.md](20-testing-quality.md).
- ⚠️ Test phải trỏ **DB riêng** (cấu hình trong `phpunit.xml` hoặc `.env.testing`). Trait
  `RefreshDatabase` xoá và tạo lại schema, trỏ nhầm DB dev là mất dữ liệu thật.

**Đọc**
- PHPStan: [Rule Levels](https://phpstan.org/user-guide/rule-levels), [Baseline](https://phpstan.org/user-guide/baseline); [Larastan](https://github.com/larastan/larastan) (README, phần cấu hình); [phpstan-deprecation-rules](https://github.com/phpstan/phpstan-deprecation-rules)
- [Rector documentation](https://getrector.com/documentation) (phần *Set lists* và *PHP version upgrade*); [rector-laravel](https://github.com/driftingly/rector-laravel)
- Laravel: [Pint](https://laravel.com/docs/pint); [PHP-CS-Fixer](https://cs.symfony.com/); [Psalm](https://psalm.dev/)

**Nắm chắc khi**
- [ ] Đưa PHPStan + Larastan vào một project, tạo baseline, đặt CI chặn lỗi mới (bài tập 6)
- [ ] Chạy Rector nâng một thư mục lên PHP 8.4 và đọc được diff nó sinh ra
- [ ] Giải thích được vì sao level 9–10 hay bắn lỗi ở code dùng `$request->input()` và cách xử lý

---

### Chặng 3: Senior 🔴

#### 3.1 Bên trong Zend Engine: zval, refcount, copy-on-write

📖 **Giáo trình:** [Chương 19. Bên trong Zend Engine](kien-thuc/php/19-ben-trong-engine.md)

**Vì sao cần học:** Đây là tầng người phỏng vấn senior PHP hay đào tới: "array được copy khi nào",
"vì sao `&` không làm nhanh hơn", "vì sao gán array 100 MB mà RAM không tăng". Hiểu zval và
copy-on-write giúp bạn đoán đúng chi phí bộ nhớ của code, và là nền để hiểu GC (3.2) và leak trong
process sống lâu (3.5).

**Học gì**

*zval: một biến PHP trông thế nào bên trong*
- PHP viết bằng C. Mỗi giá trị PHP được biểu diễn bằng một struct C tên *zval* ("Zend value").
- Từ PHP 7, một zval chiếm **16 byte**, gồm:
  - 8 byte *value*: hoặc chứa thẳng giá trị, hoặc chứa con trỏ tới dữ liệu nằm chỗ khác.
  - 8 byte còn lại: 4 byte *type info* cho biết giá trị là kiểu gì (int, string, array...), và
    4 byte phụ engine dùng cho việc khác.
- Kiểu nhỏ nằm **thẳng trong zval**: `int`, `float`, `bool`, `null`.
  - Không cần cấp phát bộ nhớ riêng (*heap allocation*), không cần đếm tham chiếu.
  - Copy một int là copy 16 byte, rất rẻ.
- Kiểu lớn nằm ở cấu trúc riêng, zval chỉ giữ con trỏ:
  - String là `zend_string`, array là `zend_array` (còn gọi là HashTable), object là `zend_object`.
  - Mỗi cấu trúc này có một bộ đếm *refcount*: số zval đang trỏ tới nó.

*Refcount và copy-on-write*
- *Refcount* (reference count) đếm có bao nhiêu biến đang dùng chung một giá trị. Về 0 thì giá trị
  được giải phóng (module 3.2).
- *Copy-on-write* (COW): gán hoặc truyền array không copy dữ liệu, chỉ tăng refcount. Chỉ khi
  **ghi** vào một bên mà refcount > 1 thì PHP mới copy ra bản riêng. Bước copy đó gọi là
  *separation* (tách).
- Theo dõi refcount của một array qua 4 bước:
  1. `$a = [1, 2, 3];` tạo `zend_array`, refcount = 1.
  2. `$b = $a;` `$b` trỏ cùng array, refcount = 2. Không copy gì.
  3. `f($a);` trong lúc hàm chạy, tham số cũng trỏ tới array đó, refcount = 3.
  4. Hàm ghi `$param[] = 4;` refcount > 1 nên PHP tách: copy ra array mới cho `$param`
     (refcount 1), array cũ về refcount 2. `$a` và `$b` không bị ảnh hưởng.
- Hệ quả: truyền array lớn vào hàm **không tốn** gì chừng nào hàm không sửa nó.

  ```php
  $a = range(1, 1_000_000);
  $m1 = memory_get_usage();
  $b = $a;                                  // chỉ tăng refcount
  echo memory_get_usage() - $m1, "\n";      // gần 0
  $b[] = 1;                                 // ghi: separation, copy cả array
  echo memory_get_usage() - $m1, "\n";      // tăng khoảng 16 MiB (từ 8.2 mỗi phần tử packed array tốn 16 byte)
  ```
- `foreach ($arr as $v)` (by value) cũng không copy array, chỉ tăng refcount trong lúc duyệt.

*Reference và vì sao `&` thường chậm hơn*
- Khi tạo reference (`$b = &$a`), PHP bọc giá trị trong một cấu trúc `zend_reference`, và cả hai
  biến trỏ tới cấu trúc đó.
- ⚠️ "Dùng `&` để tránh copy array" là hiểu sai:
  - Khi hàm chỉ đọc, COW đã không copy rồi. `&` không tiết kiệm được gì.
  - Ngược lại, `&` thêm một lớp gián tiếp (`zend_reference`), và biến là reference khiến engine
    bỏ qua một số tối ưu.
  - Trộn reference với biến thường cùng trỏ một array vẫn phải tách bản sao khi ghi. Ở PHP 5 việc
    trộn này còn buộc copy cả array ngay khi truyền vào hàm. PHP 7 đỡ hơn, nhưng lời khuyên giữ
    nguyên: chỉ dùng `&` khi thật sự cần sửa biến của phía gọi.

*Interned string*
- *Interned string*: các chuỗi cố định như literal trong code (`'status'`), tên class, tên hàm,
  tên biến được lưu **một bản duy nhất** và không đếm refcount.
- Có OPcache thì các chuỗi này nằm trong shared memory, dùng chung cho mọi worker. Dung lượng giới
  hạn bởi `opcache.interned_strings_buffer` (module 2.3).

*Object: handle, không COW*
- Biến chứa object chỉ giữ một *handle* trỏ vào *object store* (bảng mọi object đang sống của
  request).
- Object **không có copy-on-write**: gán object chỉ copy handle, và mọi biến cùng sửa một object
  (module 1.2). Muốn bản riêng thì `clone`.

*Hashtable, opcode và VM*
- `zend_array` gồm hai phần:
  - Mảng *bucket* nằm liền nhau trong bộ nhớ, **theo thứ tự chèn**. Mỗi bucket chứa key, hash và
    zval giá trị.
  - Mảng *hash*: từ hash của key trỏ vào vị trí bucket, để tra key nhanh.
- Hệ quả:
  - `foreach` chỉ cần đi dọc mảng bucket, nên vừa giữ thứ tự chèn vừa nhanh (dữ liệu liền nhau, CPU
    cache hiệu quả).
  - *Packed array* (key số nguyên tăng dần, thường là 0..n) bỏ hẳn mảng hash, key chính là vị trí. Tiết kiệm thêm RAM.
- So với PHP 5 (mỗi phần tử là một zval cấp phát riêng, nối bằng danh sách liên kết), PHP 7 dùng ít
  RAM hơn hẳn cho cùng một array và nhanh hơn.

- Mỗi hàm sau khi compile là một *op array*: danh sách opcode cùng thông tin biến. *VM executor*
  chạy lần lượt các opcode đó (module 2.3).
- Muốn xem opcode để học: `opcache.opt_debug_level` hoặc extension VLD. Chỉ để học, không dùng
  trên production.

*Đối chiếu Java/Go*
- Java và Go: object có *object header* (thông tin kiểu, lock, GC) và biến giữ con trỏ. Không có
  COW ở mức ngôn ngữ cho collection: gán `List` trong Java là hai biến cùng trỏ một list, giống
  object của PHP chứ không giống array.

**Đọc**
- PHP Internals Book: [Zvals](https://www.phpinternalsbook.com/php7/zvals.html) → [Basic structure](https://www.phpinternalsbook.com/php7/zvals/basic_structure.html), [Memory management](https://www.phpinternalsbook.com/php7/zvals/memory_management.html) (refcount, COW, separation); [zend_string](https://www.phpinternalsbook.com/php7/internal_types/strings/zend_strings.html) (interned string)
- nikic: [Internal value representation in PHP 7, part 1](https://www.npopov.com/2015/05/05/Internal-value-representation-in-PHP-7-part-1.html) và [part 2](https://www.npopov.com/2015/06/19/Internal-value-representation-in-PHP-7-part-2.html), [PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html), [PHP 7 Virtual Machine](https://www.npopov.com/2017/04/14/PHP-7-Virtual-machine.html)
- Tham khảo source: [`Zend/zend_types.h`](https://github.com/php/php-src/blob/master/Zend/zend_types.h) (định nghĩa `zval`)

**Nắm chắc khi**
- [ ] Vẽ được refcount của một array qua 4 bước: tạo, gán cho biến khác, truyền vào hàm, sửa trong hàm
- [ ] Giải thích được vì sao `memory_get_usage()` gần như không tăng khi gán array 100 MB sang biến khác
- [ ] Giải thích được vì sao PHP 7 dùng ít RAM hơn PHP 5 hẳn cho cùng một array

#### 3.2 Bộ nhớ và garbage collection

📖 **Giáo trình:** [Chương 19. Bên trong Zend Engine](kien-thuc/php/19-ben-trong-engine.md)

**Vì sao cần học:** PHP quản lý bộ nhớ khác hẳn Java và Go. Trong FPM điều này hầu như vô hình,
nhưng trong queue worker hay Octane nó quyết định worker có leak hay không. Câu hỏi hay gặp: "PHP
dọn vòng tham chiếu thế nào, so với GC của Java/Go".

**Học gì**

*Reference counting là cơ chế chính*
- Mỗi giá trị lớn có refcount (module 3.1). Refcount về 0 thì giá trị được giải phóng **ngay lập
  tức**, và `__destruct()` của object chạy ngay lúc đó.

  ```php
  function f(): void {
      $conn = new Connection();   // refcount 1
  }                               // hết hàm, $conn mất, refcount 0, __destruct chạy tại đây
  ```
- Khác với *tracing GC* của Java/Go: loại GC này định kỳ đi từ các "gốc" (biến global, stack) tìm
  mọi object còn với tới được, cái nào không với tới thì dọn. Thời điểm dọn không đoán trước được.

*Vòng tham chiếu*
- *Vòng tham chiếu* (cycle): các giá trị trỏ vòng vào nhau nên refcount không bao giờ về 0, kể cả
  khi code không còn biến nào dùng tới chúng.

  ```php
  $a = new stdClass(); $b = new stdClass();
  $a->b = $b; $b->a = $a;     // mỗi object refcount 2
  unset($a, $b);              // còn refcount 1 mỗi cái, vì trỏ vào nhau. Rác, nhưng chưa được dọn
  ```
- Các dạng hay gặp: parent và child trỏ nhau (cây, Eloquent relationship hai chiều), closure giữ
  `$this` được gán vào property của chính object đó, event listener giữ object đăng ký nó.

*Cycle collector*
- PHP có thêm một bộ *cycle collector* để dọn riêng các vòng:
  1. Mỗi khi refcount của một array hoặc object **giảm nhưng chưa về 0**, giá trị đó có thể là một
     phần của vòng, nên được ghi vào *root buffer* (danh sách nghi vấn).
  2. Khi root buffer đầy (ngưỡng ban đầu **10.000 root**; từ 7.3 ngưỡng tự nới ra nếu lần chạy trước
     thu hồi được ít), thuật toán chạy.
  3. Với mỗi root, PHP thử trừ refcount của mọi thứ nó trỏ tới (mô phỏng "nếu bỏ các liên kết nội
     bộ thì sao").
  4. Giá trị nào refcount mô phỏng về 0 thì chỉ được giữ sống bởi chính vòng đó, tức là rác.
  5. Giá trị còn refcount > 0 thì còn biến bên ngoài dùng, khôi phục lại refcount.
  6. Giải phóng các giá trị rác.
- Từ PHP 7.3, ngưỡng tự điều chỉnh: nếu các lần chạy gần đây thu được ít rác thì ngưỡng tăng lên,
  đỡ tốn thời gian chạy vô ích.
- Hàm liên quan:
  - `gc_collect_cycles()`: chạy thu gom ngay. `gc_disable()`: tắt cycle collector.
  - `gc_status()`: số lần đã chạy, số root trong buffer, ngưỡng hiện tại.
- Trong FPM thường không cần quan tâm, vì hết request mọi thứ bị dọn. Trong worker sống lâu thì có.

*Weak reference*
- *Weak reference* là tham chiếu **không tăng refcount**, nên không giữ object sống.
  - `WeakReference` (7.4): trỏ yếu tới một object, `->get()` trả `null` nếu object đã bị giải phóng.
  - `WeakMap` (8.0): map với key là object, key yếu. Object bị giải phóng thì mục tương ứng tự biến
    mất.
- Dùng làm cache gắn với object mà không giữ object sống:

  ```php
  $cache = new WeakMap();
  $cache[$order] = computeTotal($order);   // $order hết dùng thì mục này tự mất
  // Mảng thường $cache[spl_object_id($order)] giữ dữ liệu mãi, và id còn bị tái dùng: leak và sai
  ```

*Đo bộ nhớ*
- `memory_get_usage()`: bộ nhớ các giá trị PHP đang dùng.
- `memory_get_usage(true)`: bộ nhớ *Zend MM* (bộ quản lý bộ nhớ của PHP) đã xin từ OS, thường lớn
  hơn vì Zend MM xin theo khối lớn rồi tự chia.
- `memory_get_peak_usage()`: mức cao nhất từng đạt.
- ⚠️ Zend MM ít khi trả RAM về OS. Một job ăn 500 MB xong thì PHP giải phóng giá trị, nhưng RSS của
  worker vẫn cao. RSS gần như chỉ tăng. Đó là lý do `pm.max_requests` và `--max-jobs` có ích: khởi
  động lại process là cách chắc chắn để trả RAM.
- 8.5 thêm ini `max_memory_limit`: đặt trần mà `ini_set('memory_limit', ...)` trong code không nâng
  vượt được.

*Đối chiếu Java/Go*

| | PHP | Java | Go |
|---|---|---|---|
| Cơ chế | Refcount + cycle collector | Tracing GC chia thế hệ | Tracing GC concurrent, không chia thế hệ |
| Khi nào giải phóng | Ngay khi refcount về 0 (trừ vòng) | Khi GC chạy | Khi GC chạy |
| Chi phí | Mỗi phép gán phải tăng/giảm refcount | Có pause khi GC, cần tinh chỉnh heap | Pause ngắn, tốn CPU chạy song song |
| Destructor | Chạy tức thời, đoán trước được | Không có destructor đáng tin | Chỉ có finalizer, không đoán được thời điểm |
| Gây đau khi | Vòng tham chiếu trong process sống lâu | Heap lớn, pause dài | Tạo rất nhiều object nhỏ |

**Đọc**
- PHP: [Garbage Collection](https://www.php.net/manual/en/features.gc.php) → [Reference Counting Basics](https://www.php.net/manual/en/features.gc.refcounting-basics.php), [Collecting Cycles](https://www.php.net/manual/en/features.gc.collecting-cycles.php); [gc_status](https://www.php.net/manual/en/function.gc-status.php), [WeakMap](https://www.php.net/manual/en/class.weakmap.php), [WeakReference](https://www.php.net/manual/en/class.weakreference.php), [memory_get_usage](https://www.php.net/manual/en/function.memory-get-usage.php)

**Nắm chắc khi**
- [ ] Viết được script tạo vòng tham chiếu trong vòng lặp, đo memory có và không có `gc_collect_cycles()`
- [ ] So sánh được refcount + cycle collector của PHP với tracing GC của Java/Go: ưu, nhược, khi nào mỗi cái gây đau
- [ ] Viết được cache theo object bằng `WeakMap` và giải thích vì sao mảng thường thì leak

#### 3.3 OPcache chuyên sâu, preloading, JIT

📖 **Giáo trình:** [Chương 18. PHP-FPM, Nginx và OPcache trên production](kien-thuc/php/18-fpm-nginx-opcache.md), [Chương 19. Bên trong Zend Engine](kien-thuc/php/19-ben-trong-engine.md), [Chương 20. Hiệu năng và profiling](kien-thuc/php/20-hieu-nang.md)

**Vì sao cần học:** Người phỏng vấn hay hỏi "PHP 8 có JIT rồi, sao app không nhanh hơn" để xem
bạn phân biệt được các tầng tối ưu và biết đo trước khi bật. Preloading và JIT cũng có cái giá
vận hành khi deploy mà nhiều người không để ý.

**Học gì**

*OPcache làm thêm những gì*
- Ngoài cache opcode (module 2.3), OPcache còn:
  - Chạy các *optimizer pass*: tối ưu opcode trước khi lưu, ví dụ tính sẵn biểu thức hằng, bỏ code
    không bao giờ chạy tới.
  - Lưu interned string trong shared memory (module 3.1).
  - *File cache* (`opcache.file_cache`): lưu opcode ra đĩa. Có ích cho CLI (mỗi lần chạy là một
    process mới, shared memory mất khi process kết thúc) và container khởi động lạnh.

*Preloading*
- *Preloading* (7.4+): khai báo `opcache.preload` trỏ tới một script. Khi FPM khởi động, script
  này nạp sẵn các class vào shared memory, và mọi request thấy chúng như class có sẵn của PHP, không
  cần autoload.
- Khi chạy FPM bằng root thì phải đặt `opcache.preload_user` (user hệ điều hành chạy script
  preload), vì PHP không cho preload chạy dưới root.
- Đánh giá:
  - Lợi ít với app đã có autoload tối ưu và OPcache tốt, vì phần tiết kiệm là rất nhỏ.
  - ⚠️ Đổi code của class đã preload thì phải **restart FPM**, reload thường không đủ.

*JIT*
- *JIT* (Just-In-Time compiler, 8.0+): nằm trong OPcache, biến opcode chạy nhiều (*hot*) thành **mã
  máy** của CPU, bỏ qua bước VM thông dịch từng opcode.

  | Tầng | Bỏ được bước nào | Lợi cho |
  |---|---|---|
  | OPcache | Parse và compile mỗi request | Mọi app |
  | JIT | Thông dịch opcode, thay bằng mã máy | Code tính toán nhiều |

- Hai chế độ:
  - `tracing` (mặc định khi bật): theo dõi các đường chạy nóng (vòng lặp, chuỗi hàm hay gọi) rồi
    compile đúng đường đó.
  - `function`: compile nguyên cả hàm.
- PHP 8.4 viết lại JIT trên *IR framework* (một lớp biểu diễn trung gian mới, dễ tối ưu và bảo trì
  hơn). Mặc định ini đổi theo:
  - `opcache.jit=disable`, `opcache.jit_buffer_size=64M`.
  - ⚠️ Trước 8.4, JIT bật bằng cách đặt `jit_buffer_size` khác 0. Từ 8.4 phải đặt
    `opcache.jit=tracing` tường minh, chỉ đặt buffer size thì JIT vẫn tắt.

  ```ini
  ; PHP 8.4+
  opcache.enable=1
  opcache.jit=tracing
  opcache.jit_buffer_size=64M
  ```
- JIT có lợi rõ cho code **CPU-bound** (thời gian chủ yếu là tính toán): xử lý ảnh bằng PHP thuần,
  thuật toán nặng.
- Web app thường **I/O-bound** (thời gian chủ yếu là chờ DB, Redis, HTTP): CPU chỉ chạy một phần nhỏ
  thời gian, JIT tăng tốc phần nhỏ đó thì tổng lợi rất ít.
- Câu trả lời senior: "đo trước khi bật; nút thắt thường là query chứ không phải CPU". Đo bằng
  benchmark cùng tải, trước và sau, so p50/p95 (độ trễ mà 50% và 95% request nằm dưới).

*Đối chiếu Java*
- JVM cũng có JIT, nhưng cần *warm-up*: code chạy nhiều lần trong một process sống lâu thì mới được
  compile và tối ưu dần.
- PHP-FPM có OPcache dùng chung giữa các worker, nhưng mỗi request vẫn khởi động lại phần userland
  (boot framework), nên không có "process ấm dần" như JVM.

**Đọc**
- PHP: [Preloading](https://www.php.net/manual/en/opcache.preloading.php), [`opcache.jit`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.jit), [`opcache.jit_buffer_size`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.jit-buffer-size), [`opcache.preload`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.preload)
- RFC: [Preloading](https://wiki.php.net/rfc/preload), [JIT](https://wiki.php.net/rfc/jit) (phần benchmark), [New JIT based on IR framework](https://wiki.php.net/rfc/jit-ir)
- PHP.Watch: [PHP 8.4 JIT INI changes](https://php.watch/versions/8.4/opcache-jit-ini-default-changes)
- Tideways: [What's new in PHP 8.5 for performance, debugging and operations](https://tideways.com/profiler/blog/whats-new-in-php-8-5-in-terms-of-performance-debugging-and-operations)

**Nắm chắc khi**
- [ ] Giải thích được OPcache và JIT khác nhau ở tầng nào, và vì sao JIT ít giúp app CRUD
- [ ] Viết được cấu hình ini bật JIT đúng cho PHP 8.4+ và nói cách đo xem có lợi không
- [ ] Nói được khi nào preloading đáng dùng và cái giá khi deploy

#### 3.4 PHP-FPM ở mức vận hành

📖 **Giáo trình:** [Chương 18. PHP-FPM, Nginx và OPcache trên production](kien-thuc/php/18-fpm-nginx-opcache.md)

**Vì sao cần học:** Module 2.2 là cấu hình FPM. Module này là chẩn đoán khi FPM gặp sự cố trên
production: 502 lúc cao điểm, timeout lệch nhau giữa các tầng, chạy FPM trên Kubernetes. Người
phỏng vấn senior thường đưa một tình huống sự cố và hỏi bạn xem gì trước, sửa gì trước.

**Học gì**

*Lifecycle ở mức engine*
- Bên dưới userland, PHP có vòng đời riêng cho extension (thư viện C như PDO, OPcache, Redis):
  1. *MINIT* (module init): chạy **một lần** khi process khởi động. Extension khởi tạo tài nguyên
     dùng lâu dài.
  2. *RINIT* (request init): chạy đầu mỗi request.
  3. Chạy script PHP của bạn.
  4. *RSHUTDOWN*: cuối mỗi request, dọn state của request.
  5. *MSHUTDOWN*: khi process tắt.
- Hệ quả: userland share-nothing, nhưng extension **giữ được state giữa các request** qua MINIT.
  Đó là cách OPcache giữ cache và `PDO::ATTR_PERSISTENT` giữ connection.

*Đọc status page theo thời gian*
- Nhìn một lần thì ít giá trị, cần nhìn theo thời gian (đưa vào dashboard):
  - `listen queue` > 0 kéo dài: request đang phải xếp hàng chờ worker.
  - `max children reached` tăng: đã chạm trần số worker. ⚠️ Chỉ số này chỉ có ý nghĩa với
    `pm = dynamic` và `ondemand`; với `pm = static` nó luôn bằng 0.
- Hai dấu hiệu trên có nghĩa là thiếu worker, **hoặc** worker đang bị chặn chờ downstream (DB, API
  ngoài) nên không rảnh để nhận request.

*Chẩn đoán 502/504 lúc cao điểm khi CPU không cao*
1. CPU thấp mà hết worker nghĩa là worker không bận tính toán, mà đang **chờ** (DB chậm, API ngoài
   treo, lock).
2. Xem slow log để biết worker đang đứng ở hàm nào.
3. Sửa nguyên nhân: thêm timeout cho HTTP client, sửa query chậm, đưa việc chậm vào queue.
4. Chỉ tăng số worker khi còn RAM **và** downstream chịu được thêm connection. Tăng worker khi DB
  đang là nút thắt chỉ dồn thêm tải vào DB.

*Chuỗi timeout*
- Thứ tự phải là: timeout HTTP client < `request_terminate_timeout` < `fastcgi_read_timeout` (Nginx)
  < timeout của load balancer.
- Lý do: tầng trong cùng phải hết giờ trước, để code PHP còn kịp bắt lỗi, log, trả response có
  nghĩa. Nếu tầng ngoài hết giờ trước:
  - Load balancer trả 504 cho client, nhưng worker vẫn chạy tiếp và chiếm chỗ.
  - Client retry, gửi thêm request vào một hệ thống đang quá tải.

*Tách pool và chạy trên container*
- Nhiều pool tách theo loại traffic (API nhanh, admin chậm, webhook), mỗi pool socket và số worker
  riêng. Một loại traffic chậm không ăn hết worker của loại khác.
- Container/Kubernetes:
  - Mỗi pod một pool `pm = static`, scale bằng số pod thay vì số worker.
  - `pm.max_children` tính theo memory limit của pod.
  - ⚠️ Autoscale thêm pod là nhân thêm số connection DB.
- *Persistent connection* (`ATTR_PERSISTENT`): giữ connection DB qua nhiều request, rủi ro rò trạng
  thái giữa request (xem module 2.7 của [03-database-sql.md](03-database-sql.md)).

**Đọc**
- PHP Internals Book: [Learning the PHP lifecycle](https://www.phpinternalsbook.com/php7/extensions_design/php_lifecycle.html)
- PHP: [FPM Status Page](https://www.php.net/manual/en/fpm.status.php) (ý nghĩa từng trường), [Persistent Connections](https://www.php.net/manual/en/features.persistent-connections.php)
- Phần Linux (process, memory, OOM killer): [01-os-linux.md](01-os-linux.md)

**Nắm chắc khi**
- [ ] Từ status page và slow log, chẩn đoán được sự cố 502 và đề xuất sửa theo thứ tự ưu tiên
- [ ] Vẽ được chuỗi timeout từ load balancer tới HTTP client và giải thích vì sao thứ tự quan trọng
- [ ] Nói được một pod FPM trên K8s nên cấu hình `pm` thế nào và vì sao

#### 3.5 Process sống lâu: queue worker, Octane, daemon

📖 **Giáo trình:** [Chương 29. Queue, event, scheduler, cache, mail và notification](kien-thuc/php/29-laravel-queue-event-schedule-cache.md), [Chương 30. Laravel: kiểm thử, Octane và triển khai](kien-thuc/php/30-laravel-testing-octane-deploy.md), [Chương 13. Generator, iterator và SPL](kien-thuc/php/13-generator-iterator-spl.md)

**Vì sao cần học:** Khi app lớn, PHP không còn chỉ chạy trong FPM: queue worker, Horizon, Octane,
consumer Kafka đều là process sống hàng giờ tới hàng ngày. Ở đó các lợi thế của share-nothing mất
đi, và bug kiểu "user A thấy dữ liệu user B" hay "worker RAM tăng tới OOM" xuất hiện. Đây là chủ
đề phân biệt senior với mid rõ nhất.

**Học gì**

*Mất lợi thế share-nothing*
- *Process sống lâu* (long-running process) là process boot app một lần rồi xử lý nhiều request
  hoặc job: queue worker, Horizon, Octane, consumer Kafka/RabbitMQ, daemon tự viết.
- Mọi thứ không được dọn giữa các lần xử lý: static property, singleton trong container, vòng tham
  chiếu chưa thu gom. Cái gì tích luỹ thì tích luỹ mãi.

*Nguồn leak hay gặp*
- Static array dùng làm cache, thêm mãi không xoá.
- Listener hoặc callback đăng ký lặp lại mỗi job (mỗi lần xử lý lại `Event::listen` thêm một lần).
- `DB::enableQueryLog()`: lưu mọi query vào mảng trong RAM.
- Telescope, Debugbar chạy trong worker: ghi lại mọi thứ.
- Vòng tham chiếu (module 3.2).
- Collection gán vào property của một singleton.

*Phòng và tìm leak*
- Lưới an toàn: `--max-jobs`, `--max-time`, `--memory` để worker tự thoát và được process manager
  khởi động lại.
- Tìm gốc:
  1. Log `memory_get_usage()` sau **từng job**, kèm tên job.
  2. Tìm loại job làm memory tăng mà không giảm.
  3. Chạy riêng loại job đó lặp nhiều lần để cô lập.
  4. Tìm chỗ giữ tham chiếu: static, singleton, listener, vòng tham chiếu. Thử `gc_collect_cycles()`
     để biết có phải do vòng không.
- ⚠️ Connection DB/Redis có thể bị server đóng (idle timeout, failover). Worker cần reconnect.
- ⚠️ Transaction bị bỏ dở (job lỗi giữa chừng mà không rollback) rò sang job sau trên cùng
  connection.

*Signal và dừng êm*
- *Signal* là thông báo OS gửi tới process. `SIGTERM` nghĩa là "hãy dừng lại".
- Dừng êm (*graceful shutdown*): nhận `SIGTERM` thì làm xong job hiện tại rồi mới thoát. Worker
  Laravel đã có sẵn. Script tự viết dùng `pcntl_signal()` và `pcntl_async_signals(true)`.

*Octane*
- *Octane* chạy Laravel trên application server sống lâu: FrankenPHP, RoadRunner, Swoole/OpenSwoole.
  App boot **một lần** mỗi worker rồi phục vụ nhiều request.
- ⚠️ *State leak*: dữ liệu của request trước lọt sang request sau.

  ```php
  // AppServiceProvider::register()
  $this->app->singleton(ReportService::class, fn ($app) =>
      new ReportService($app['request'])   // nếu resolve lúc boot: giữ mãi Request giả lúc boot
  );
  ```
  - Singleton được resolve lúc boot (hoặc trong `warm`) mà giữ `Request`, user đăng nhập, hoặc config
    lúc boot: mọi request sau thấy dữ liệu cũ. (Singleton resolve lần đầu trong request thì nằm ở bản
    clone của app và bị bỏ sau request đó.)
  - Static property tăng mãi.
  - Inject container hoặc request vào constructor của singleton: giữ bản cũ.
  - Sửa: inject closure resolver (`fn () => $app['request']`), đăng ký bằng `scoped`, hoặc resolve
    ngay lúc dùng (`request()` trong method).
- Octane tự reset một số service của framework giữa các request. ⚠️ Package bên thứ ba chưa chắc
  tương thích.
- Mặc định recycle worker sau **500 request** (`--max-requests`).
- Khi nào đáng dùng: hiệu quả nhất khi boot framework chiếm phần lớn thời gian request. Nếu nút thắt
  là DB thì lợi ít.
- Khác biệt giữa các server:
  - Swoole có *coroutine* (nhiều luồng việc xen kẽ trong một process), task worker,
    `Octane::concurrently()`.
  - FrankenPHP worker mode chạy trên web server Caddy.

*Đối chiếu Java/Go*
- Java và Go luôn là process sống lâu, nên dev quen nghĩ về state dùng chung và thread safety từ
  đầu. Dev PHP chuyển sang Octane phải học lại đúng thói quen đó ([06-java-spring.md](06-java-spring.md),
  [07-go.md](07-go.md)).

**Đọc**
- Laravel: [Octane](https://laravel.com/docs/octane), đọc kỹ [Dependency Injection and Octane](https://laravel.com/docs/octane#dependency-injection-and-octane) và [Managing Memory Leaks](https://laravel.com/docs/octane#managing-memory-leaks); [Queues: Resource Considerations](https://laravel.com/docs/queues#resource-considerations)
- [FrankenPHP worker mode](https://frankenphp.dev/docs/worker/), [RoadRunner docs](https://roadrunner.dev/docs)
- PHP: [PCNTL](https://www.php.net/manual/en/book.pcntl.php)

**Nắm chắc khi**
- [ ] Liệt kê được 5 chỗ trong codebase của mình sẽ gây state leak nếu bật Octane (bài tập 5)
- [ ] Viết được một singleton gây leak user giữa hai request Octane rồi sửa bằng `scoped`
- [ ] Mô tả được quy trình tìm leak của queue worker: đo, cô lập job, tìm gốc

#### 3.6 Hiệu năng và profiling

📖 **Giáo trình:** [Chương 20. Hiệu năng và profiling](kien-thuc/php/20-hieu-nang.md)

**Vì sao cần học:** "Endpoint này chậm, bạn làm gì" là câu hỏi hiệu năng phổ biến nhất. Người phỏng
vấn muốn nghe quy trình đo trước sửa sau, biết chọn công cụ nào, và xử lý được bài toán dữ liệu lớn
(import/export triệu dòng) mà không hết RAM.

**Học gì**

*Quy trình*
1. Đo: xác định endpoint nào chậm và chậm bao nhiêu (APM, log).
2. Tìm nút thắt: thường là query, N+1, gọi API tuần tự, hiếm khi là CPU.
3. Sửa đúng chỗ đó.
4. Đo lại với cùng điều kiện ([17-performance.md](17-performance.md)).

*Công cụ*
- *Profiler* là công cụ ghi lại thời gian và bộ nhớ của từng hàm trong một lần chạy.

  | Công cụ | Loại | Dùng ở đâu |
  |---|---|---|
  | Xdebug | Debugger + profiler (xuất file cachegrind) | Chỉ dev. ⚠️ Overhead lớn, không bật trên production |
  | Blackfire, Tideways | Profiler thương mại, chạy theo yêu cầu hoặc sampling | Production được. Có call graph, so sánh trước/sau |
  | XHProf, SPX | Profiler nhẹ, mã nguồn mở | Dev và staging |
  | Telescope, Debugbar | Công cụ Laravel xem query, request, job | Dev |
  | Pulse, Nightwatch | Giám sát Laravel | Production |
  | APM (New Relic, Datadog, OpenTelemetry) | Theo dõi toàn hệ thống | Production, bức tranh tổng |

- APM cho biết endpoint nào chậm. Profiler để đào sâu vào một endpoint cụ thể.

*Đọc file lớn*
- ⚠️ `file_get_contents()` và `file()` nạp **cả file** vào RAM. File 2 GB là 2 GB RAM.
- Đọc từng dòng bằng `fopen` + `fgets`/`fgetcsv`, hoặc `SplFileObject`, và bọc trong generator để
  code gọi dùng như một danh sách:
  ```php
  function rows(string $path): \Generator {
      $h = fopen($path, 'rb');
      try {
          // PHP 8.4+: truyền rõ $escape, không thì bị deprecation
          while (($row = fgetcsv($h, null, ',', '"', '')) !== false) { yield $row; }
      } finally { fclose($h); }
  }
  ```

*Import dữ liệu lớn*
1. Đọc stream theo lô (ví dụ 1000 dòng).
2. Insert batch 500–1000 dòng mỗi câu `INSERT`.
3. Mỗi lô một transaction ngắn, không bọc cả file trong một transaction.
4. Chạy trong queue, không chạy trong request HTTP.
5. Lưu tiến độ (dòng đã xử lý) để khi lỗi thì chạy tiếp từ đó thay vì làm lại từ đầu.

*Export dữ liệu lớn*
- Streaming CSV: `response()->streamDownload()` kết hợp `lazyById()`, mỗi dòng đọc ra thì ghi thẳng
  xuống client. Bộ nhớ gần như hằng số.
- ⚠️ Dữ liệu có thể bị giữ lại ở các tầng buffer: output buffering của PHP, buffering của Nginx
  (tắt bằng header `X-Accel-Buffering: no`). Timeout các tầng cũng phải đủ dài.
- Export rất lớn: chạy nền, ghi file lên S3, gửi link cho user.
- ⚠️ Excel mở CSV UTF-8 tiếng Việt bị sai dấu: thêm *BOM* `\xEF\xBB\xBF` (vài byte đánh dấu file là
  UTF-8) ở đầu file.
- ⚠️ *CSV injection*: ô bắt đầu bằng `=`, `+`, `-`, `@` bị Excel hiểu là công thức, có thể chạy lệnh.
  Thêm dấu `'` ở đầu các ô đó.

*Gọi nhiều API*
- Gọi tuần tự 3 API mỗi cái 300 ms là 900 ms. `Http::pool()` gửi song song, tổng cỡ 300 ms.

**Đọc**
- [Xdebug profiler](https://xdebug.org/docs/profiler), [Blackfire docs](https://docs.blackfire.io/), [php-spx](https://github.com/NoiseByNorthwest/php-spx)
- Laravel: [Pulse](https://laravel.com/docs/pulse), [Telescope](https://laravel.com/docs/telescope)
- PHP: [SplFileObject](https://www.php.net/manual/en/class.splfileobject.php), [fgetcsv](https://www.php.net/manual/en/function.fgetcsv.php)

**Nắm chắc khi**
- [ ] Profile được một endpoint chậm bằng SPX hoặc Xdebug và chỉ ra hàm tốn nhất
- [ ] Viết được export 2 triệu dòng với RAM dưới 50 MB và giải thích từng tầng buffer
- [ ] Thiết kế được import CSV 5 triệu dòng chạy tiếp được khi lỗi giữa chừng

#### 3.7 Bảo mật đặc thù PHP

📖 **Giáo trình:** [Chương 17. Bảo mật ứng dụng PHP](kien-thuc/php/17-bao-mat.md), [Chương 15. PHP và HTTP: request, response, session, cookie, upload](kien-thuc/php/15-php-va-web.md)

**Vì sao cần học:** PHP có những lỗ hổng mang đặc thù ngôn ngữ mà OWASP chung chung không nói kỹ:
object injection qua `unserialize`, magic hash, include file theo input. Người phỏng vấn senior
thường hỏi "vì sao `unserialize` dữ liệu người dùng nguy hiểm" hoặc đưa đoạn code xác thực webhook
để bạn chỉ lỗi.

**Học gì**

*unserialize và object injection*
- `serialize()` biến giá trị PHP (kể cả object) thành chuỗi. `unserialize()` dựng lại, **kể cả tạo
  object thuộc class bất kỳ** được ghi trong chuỗi.
- ⚠️ `unserialize()` dữ liệu người dùng dẫn tới *object injection*:
  1. Kẻ tấn công gửi chuỗi serialize chứa object của một class có sẵn trong app (thường từ
     vendor), với property do họ chọn.
  2. `unserialize()` tạo object đó. Magic method `__wakeup()` chạy ngay, và `__destruct()` chạy khi
     object bị giải phóng.
  3. Magic method đó gọi method khác trên property do kẻ tấn công chọn, nối tiếp nhau thành một
     *gadget chain* (chuỗi các đoạn code có sẵn).
  4. Cuối chuỗi là một thao tác nguy hiểm: ghi file, gọi `system()`. Kết quả là *RCE* (Remote Code
     Execution, chạy lệnh tuỳ ý trên server).
  - Công cụ phpggc có sẵn gadget chain cho nhiều framework, kể cả Laravel.
- Cách phòng: dùng JSON cho dữ liệu từ ngoài. Bắt buộc phải `unserialize` thì truyền
  `['allowed_classes' => false]` để không tạo object nào.
- `phar://` từng cho phép deserialize ngầm qua các hàm file như `file_exists('phar://...')`, vì
  metadata của file phar được `unserialize` tự động. Đã đổi ở PHP 8.0.

*APP_KEY*
- `APP_KEY` là khoá Laravel dùng để mã hoá cookie, session và dữ liệu `encrypt()`.
- ⚠️ Lộ `APP_KEY` thì kẻ tấn công giải mã và giả mạo được cookie cùng dữ liệu mã hoá. Laravel bản cũ
  từng có RCE qua cookie được serialize khi lộ key (ghép với object injection ở trên).
- Coi như secret cấp cao nhất. Khi lộ thì xoay vòng key, đưa key cũ vào `APP_PREVIOUS_KEYS` để dữ
  liệu cũ vẫn giải mã được trong thời gian chuyển.

*Include file và upload*
- `include $_GET['page']` cho phép *LFI* (Local File Inclusion, include file bất kỳ trên server),
  và *RFI* (Remote File Inclusion, include file từ URL ngoài) nếu `allow_url_include=On`.
  - Phòng: whitelist tên file. `open_basedir` (giới hạn thư mục PHP được mở) chỉ là lớp phụ.
- Upload file:
  - Kiểm MIME theo **nội dung** file (`finfo`, rule `mimes` của Laravel), không tin extension hay
    header `Content-Type` do client gửi.
  - Đặt tên file ngẫu nhiên, lưu ngoài webroot hoặc lên S3.
  - ⚠️ Nginx chỉ được chạy PHP cho `index.php`, không bao giờ cho file trong thư mục upload. Nếu
    không, upload `shell.php` (hoặc ảnh chứa code PHP) rồi truy cập là chạy được code.
  - ⚠️ File SVG có thể chứa JavaScript, mở trực tiếp trên domain của bạn là *XSS* (chạy
    JavaScript của kẻ tấn công trong trình duyệt người dùng).

*So sánh an toàn: magic hash*
- ⚠️ `md5('240610708') == md5('QNKCDZO')` là `true`:
  - Cả hai hash có dạng `0e` theo sau toàn chữ số, tức là numeric string ở dạng khoa học: 0 × 10^n.
  - `==` so hai numeric string như số, cả hai đều bằng 0. Vẫn đúng ở PHP 8 (quy tắc ở module 1.1).
- Dùng `hash_equals($known, $user)` cho token, chữ ký webhook:
  - So chặt từng byte.
  - *Constant-time*: thời gian so không phụ thuộc vị trí byte đầu tiên sai, nên kẻ tấn công không đo
    thời gian phản hồi để đoán dần được chữ ký.

*Mật khẩu và số ngẫu nhiên*
- Mật khẩu: `password_hash()` (bcrypt, cost mặc định 12 từ 8.4; hoặc argon2id), `password_verify()`,
  `password_needs_rehash()` (kiểm tra hash cũ cần hash lại với cấu hình mới). Không dùng md5/sha1.
- Số ngẫu nhiên cho bảo mật (token, mã OTP): `random_bytes()`, `random_int()`, `Str::random()`.
  Không dùng `rand()`, `mt_rand()`, `uniqid()`, vì chúng đoán được.

*Những chỗ khác cần nhớ*
- `APP_DEBUG=true` hoặc `display_errors=On` trên production: trang lỗi lộ stack trace, giá trị cấu hình nhạy cảm và secret.
- Blade `{!! $x !!}` không escape HTML, dễ thành XSS. `{{ $x }}` thì có escape.
- `extract()`, biến biến `$$var`, `eval`: biến input thành biến hoặc code.
- `shell_exec` với input: dùng `escapeshellarg`, hoặc `Process` với tham số dạng mảng.
- `#[\SensitiveParameter]` gắn lên tham số (mật khẩu, key) để giấu giá trị khỏi stack trace trong
  log.
- OWASP tổng quát: [10-security.md](10-security.md).

**Đọc**
- PHP: [unserialize](https://www.php.net/manual/en/function.unserialize.php) (khung cảnh báo đầu trang), [hash_equals](https://www.php.net/manual/en/function.hash-equals.php), [password_hash](https://www.php.net/manual/en/function.password-hash.php), [random_int](https://www.php.net/manual/en/function.random-int.php), [Handling file uploads](https://www.php.net/manual/en/features.file-upload.php)
- [phpggc](https://github.com/ambionics/phpggc): xem danh sách gadget chain để hiểu mức độ nghiêm trọng
- OWASP: [Laravel Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Laravel_Cheat_Sheet.html), [PHP Configuration Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/PHP_Configuration_Cheat_Sheet.html)
- Laravel: [Encryption](https://laravel.com/docs/encryption) (phần key rotation), [Hashing](https://laravel.com/docs/hashing)

**Nắm chắc khi**
- [ ] Giải thích được chuỗi từ `unserialize($_COOKIE[...])` tới RCE qua một gadget cụ thể
- [ ] Viết được hàm xác thực chữ ký webhook HMAC đúng (so sánh, encoding, raw body)
- [ ] Rà được một cấu hình Nginx + upload và chỉ ra chỗ có thể chạy file PHP bị upload lên

#### 3.8 So sánh kiến trúc: Laravel, Symfony và ngôn ngữ khác

📖 **Giáo trình:** [Chương 02. PHP chạy như thế nào](kien-thuc/php/02-php-chay-nhu-the-nao.md), [Chương 26. Service container, provider, facade và vòng đời request](kien-thuc/php/26-laravel-container-provider-facade.md)

**Vì sao cần học:** Câu "vì sao team chọn Laravel" hay "Laravel hay Symfony cho dự án này" kiểm tra
bạn có nhìn được điểm mạnh và điểm yếu thật của công cụ mình dùng hằng ngày không. Đối chiếu với
Java/Go cũng hay được hỏi khi team dùng nhiều ngôn ngữ.

**Học gì**

*Laravel so với Symfony*

| | Laravel | Symfony |
|---|---|---|
| Triết lý | Convention, dev nhanh, "magic" có chủ đích | Tường minh, component tách rời |
| ORM mặc định | Eloquent (Active Record) | Doctrine (Data Mapper, Unit of Work) |
| Container | Resolve lúc runtime bằng reflection | Compile container thành PHP code, lỗi wiring lộ lúc build |
| Truy cập service | Facade, helper, DI | DI, autowiring |

- Giải thích vài thuật ngữ trong bảng:
  - *Unit of Work*: Doctrine theo dõi mọi entity đã thay đổi trong một phiên, rồi `flush()` ghi tất
    cả xuống DB một lần.
  - *Compile container*: lúc build, Symfony đọc toàn bộ cấu hình service và sinh ra một class PHP
    chứa sẵn code tạo từng service. Binding thiếu hoặc sai kiểu bị phát hiện ngay lúc build, thay vì
    lúc request chạy tới như Laravel.
- Laravel dùng nhiều component của Symfony: HttpFoundation, Console, Mailer...

*Chọn thế nào*
- Chọn theo đội và domain, không theo "framework nào tốt hơn".
  - Domain nhiều *invariant* (quy tắc nghiệp vụ luôn phải đúng, ví dụ "tổng tiền đơn bằng tổng các
    dòng"): Data Mapper giữ entity sạch, không dính logic lưu DB.
  - CRUD, admin, startup cần ra sản phẩm nhanh: Laravel nhanh hơn.
- Laravel vẫn làm *DDD* (Domain-Driven Design, thiết kế xoay quanh mô hình nghiệp vụ) được nếu có kỷ luật tách domain khỏi Eloquent ([15-architecture.md](15-architecture.md)).

*Đối chiếu ngôn ngữ*

| Khía cạnh | PHP/Laravel | Java/Spring | Go |
|---|---|---|---|
| Mô hình chạy | FPM: process/request, share-nothing | JVM sống lâu, thread pool (virtual thread từ 21) | Một process, goroutine mỗi request |
| State giữa request | Không có (trừ Octane/worker) | Có, singleton bean | Có, biến package, struct server |
| Memory | Refcount + cycle collector | Tracing GC chia thế hệ | Tracing GC concurrent, không chia thế hệ |
| Lỗi | Exception, không checked | Checked + unchecked | `error` là giá trị |
| DI | Container runtime, reflection | IoC container, proxy | Truyền tay qua constructor |
| ORM | Eloquent Active Record | JPA/Hibernate Data Mapper | database/sql, sqlc, GORM |
| Job nền | Queue + worker process | Executor, consumer, Spring Batch | goroutine + channel, worker riêng |
| Concurrency trong request | Gần như không (process con, `Http::pool`, Fibers) | Thread, CompletableFuture | goroutine |

- Array PHP giữ thứ tự chèn. `HashMap` của Java và `map` của Go **không** giữ thứ tự.
- Enum PHP gần enum Java (có method, implement interface) hơn là `iota` của Go (chỉ là hằng số
  nguyên tăng dần).

**Đọc**
- Symfony: [Service Container](https://symfony.com/doc/current/service_container.html), [Compiler Passes](https://symfony.com/doc/current/service_container/compiler_passes.html)
- Doctrine: [Unit of Work](https://www.doctrine-project.org/projects/doctrine-orm/en/current/reference/unitofwork.html)

**Nắm chắc khi**
- [ ] Trả lời được trong 3 phút "vì sao team bạn chọn Laravel" với ít nhất một điểm yếu thật của Laravel
- [ ] Giải thích được vì sao container compile của Symfony bắt lỗi wiring sớm hơn Laravel

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. `==` và `===` khác nhau thế nào? Cho ví dụ đổi kết quả giữa PHP 7 và PHP 8.** (1.1)
- Ý phải có: `==` ép kiểu trước khi so, `===` so cả kiểu; `0 == "a"` đổi từ `true` sang `false` ở PHP 8
- Điểm cộng: chuỗi số vẫn so như số (`"1e1" == "10"`); `in_array` mặc định so lỏng; magic hash `0e...`
- Red flag: "PHP 8 bỏ type juggling rồi"

**2. Interface, abstract class và trait khác nhau thế nào?** (1.3)
- Ý phải có: hợp đồng; kế thừa đơn có state; tái dùng code copy vào class lúc compile, không phải type
- Điểm cộng: `insteadof`/`as`; trait lạm dụng thành kế thừa ngầm; khi nào composition tốt hơn

**3. Vì sao phải commit `composer.lock`? `install` và `update` khác nhau thế nào?** (1.5)
- Ý phải có: lock ghi phiên bản chính xác để mọi môi trường giống nhau; `install` đọc lock, `update` resolve lại
- Điểm cộng: library khác app; `composer audit` trong CI; `--no-dev -o` khi deploy

**4. `$fillable` và `$guarded` để làm gì?** (1.6)
- Ý phải có: chống mass assignment, ví dụ gửi `is_admin=1`; whitelist an toàn hơn blacklist
- Điểm cộng: dùng `validated()` thay `all()`; `shouldBeStrict()` báo lỗi khi gán field không fillable

**5. `register()` và `boot()` của service provider khác nhau thế nào?** (2.4)
- Ý phải có: `register` chỉ bind; `boot` chạy sau khi mọi provider đã register nên dùng được service khác
- Điểm cộng: deferred provider; provider nặng làm chậm mọi request trên FPM

**6. `catch (Exception $e)` có bắt được `TypeError` không?** (1.4)
- Ý phải có: không; `TypeError` là `Error`; bắt cả hai bằng `Throwable`
- Điểm cộng: vì sao job có thể "chết im lặng"; không nên nuốt `Throwable` bừa bãi

**7. Vì sao gọi `env()` trong code lại trả `null` trên production?** (2.3)
- Ý phải có: `config:cache` gộp config và không nạp `.env` nữa; chỉ gọi `env()` trong `config/*.php`, code dùng `config()`
- Điểm cộng: nêu được toàn bộ bước deploy có `optimize`

### 🟡 Mid

**8. Vì sao PHP ít bị memory leak kéo dài như Java? Khi nào thì PHP lại có?** (2.2, 3.5)
- Ý phải có: FPM share-nothing dọn sạch mỗi request; leak xuất hiện ở queue worker, Octane, daemon
- Điểm cộng: nguồn leak cụ thể (static cache, query log, listener đăng ký lặp); đo bằng `memory_get_usage` theo job; `--max-jobs`, `pm.max_requests`
- Red flag: "PHP không bao giờ leak"

**9. `pm.max_children` tính thế nào? `static`, `dynamic`, `ondemand` chọn khi nào?** (2.2)
- Ý phải có: RAM còn lại chia RSS trung bình đo thật, để biên; bảng ba chế độ
- Điểm cộng: giới hạn downstream (connection DB); status page và log "max_children reached"; pod K8s dùng `static`
- Red flag: lấy `memory_limit` để chia, hoặc chép con số trên mạng

**10. Service container resolve một class có dependency trong constructor thế nào?** (2.4)
- Ý phải có: Reflection đọc constructor, đệ quy resolve theo type hint; interface cần bind
- Điểm cộng: contextual binding; `singleton` và `scoped` khác nhau ở Octane/queue; service locator là anti-pattern

**11. Facade hoạt động thế nào bên dưới? Test code dùng facade ra sao?** (2.4)
- Ý phải có: `__callStatic` → resolve accessor từ container → gọi method trên instance thật
- Điểm cộng: `shouldReceive`, `Queue::fake()`; real-time facade; tranh luận facade giấu dependency
- Red flag: "facade là static class"

**12. `max_execution_time = 30` nhưng request gọi API treo 10 phút không bị cắt. Vì sao?** (2.2)
- Ý phải có: trên Linux không tính thời gian chờ I/O, stream, query; dùng timeout HTTP client, `request_terminate_timeout`, `fastcgi_read_timeout`
- Điểm cộng: chuỗi timeout các tầng phải khớp nhau (3.4)

**13. `retry_after` và `timeout` của queue liên quan thế nào? Sai thì hậu quả gì?** (2.6)
- Ý phải có: `retry_after` phải lớn hơn `timeout` job dài nhất, không thì job bị nhận lại và chạy hai lần song song
- Điểm cộng: job vẫn phải idempotent vì còn nhiều nguồn chạy lại khác; `stopwaitsecs` của supervisor
- Red flag: "tăng `tries` là xong"

**14. Model event không chạy khi update hàng loạt. Vì sao?** (2.5)
- Ý phải có: `where()->update()` là query builder, không hydrate model nên không có event, observer, cast
- Điểm cộng: lựa chọn: lặp từng model (chậm), bắn event tay, hoặc chuyển logic ra service tường minh

**15. Sanctum và Passport khác nhau thế nào?** (2.7)
- Ý phải có: Sanctum cho SPA cùng domain gốc (cookie + CSRF) và token đơn giản lưu hash; Passport là OAuth2 server đầy đủ
- Điểm cộng: chỉ dùng Passport khi bên thứ ba cần OAuth; token có abilities và hạn

**16. PHP 8.4 và 8.5 có gì mới đáng dùng?** (2.1)
- Ý phải có: property hooks, asymmetric visibility, `array_find`/`array_any`/`array_all`, `new` không ngoặc; pipe operator, clone with, `array_first`/`array_last`, URI extension
- Điểm cộng: deprecation ảnh hưởng nâng cấp (implicit nullable, backtick); bcrypt cost 12 làm login chậm hơn; JIT phải bật bằng `opcache.jit` từ 8.4
- Red flag: chỉ kể được tính năng của 8.0

**17. Scheduler gửi báo cáo 3 lần mỗi sáng sau khi scale lên 3 server.** (2.7)
- Ý phải có: mỗi server chạy cron riêng; `onOneServer()` với cache lock dùng chung, hoặc scheduler chạy trên một instance riêng
- Điểm cộng: job gửi idempotent (ghi đã gửi ngày nào); `withoutOverlapping` của scheduler hết hạn 24 giờ khi process chết (còn job middleware `WithoutOverlapping` mặc định không hết hạn)

**18. Bạn đưa PHPStan vào một codebase Laravel cũ thế nào?** (2.8)
- Ý phải có: Larastan, bắt đầu level thấp hoặc baseline, CI chặn lỗi mới, nâng level dần
- Điểm cộng: Rector để sửa hàng loạt; generics trong PHPDoc cho collection; đo số lỗi baseline giảm theo thời gian
- Red flag: bật level max rồi bắt cả team sửa hết một lần

### 🔴 Senior

**19. Copy-on-write của array hoạt động thế nào? Reference `&` ảnh hưởng gì?** (3.1)
- Ý phải có: gán chỉ tăng refcount, ghi mới separation; int/float nằm trong zval không refcount; object là handle không COW
- Điểm cộng: reference bọc `zend_reference` và buộc tách bản sao, nên `&` để "tối ưu" thường chậm hơn; interned string; `foreach` by value không copy
- Red flag: "PHP copy array mỗi lần truyền vào hàm nên phải dùng `&`"

**20. PHP dọn vòng tham chiếu thế nào? So với GC của Java/Go?** (3.2)
- Ý phải có: refcount giải phóng tức thời; cycle collector dùng root buffer và thuật toán đánh dấu khi buffer đầy
- Điểm cộng: `WeakMap`; Zend MM ít trả RAM về OS; tracing GC có pause nhưng không cần refcount mỗi phép gán

**21. OPcache và JIT khác nhau thế nào? JIT có giúp web app không?** (2.3, 3.3)
- Ý phải có: OPcache cache opcode, bỏ parse/compile; JIT biến opcode nóng thành mã máy; web app I/O-bound nên lợi ít
- Điểm cộng: JIT IR của 8.4 và đổi mặc định ini; preloading; "đo trước khi bật"

**22. Sau deploy, một số request vẫn chạy code cũ.** (2.3)
- Ý phải có: `validate_timestamps=0` chưa reload FPM; symlink và realpath cache; worker/Horizon chưa restart; config cache cũ
- Điểm cộng: `$realpath_root`; `queue:restart` cần cache chung; kiểm tra bằng endpoint trả commit hash

**23. Nginx trả 502/504 hàng loạt lúc cao điểm, CPU không cao.** (2.2, 3.4)
- Ý phải có: FPM hết worker vì worker bị chặn chờ DB/API; xem status page, slow log
- Điểm cộng: timeout HTTP client; tách pool theo loại traffic; chuyển việc chậm vào queue; tăng worker chỉ khi còn RAM và DB chịu được
- Red flag: tăng `pm.max_children` gấp đôi ngay

**24. Queue worker RAM tăng dần tới khi bị OOM kill sau vài giờ.** (3.5)
- Ý phải có: đo memory theo từng job, cô lập loại job; tìm static cache, query log, listener đăng ký lặp, Telescope
- Điểm cộng: `--max-jobs`/`--memory` là lưới an toàn, không phải cách chữa; vòng tham chiếu và `gc_collect_cycles`

**25. Bật Octane xong thỉnh thoảng user A thấy dữ liệu của user B.** (3.5)
- Ý phải có: singleton/static giữ request hoặc user; rollback trước, điều tra sau; chuyển sang `scoped` hoặc resolve lúc dùng
- Điểm cộng: rà package bên thứ ba; test hai request liên tiếp khác user trong CI; review danh sách singleton trước khi bật
- Red flag: "Octane lỗi, tắt đi là xong" mà không tìm gốc

**26. Có nên chuyển sang Octane? Bạn đánh giá thế nào?** (3.5)
- Ý phải có: đo phần trăm thời gian boot trong request; nếu nút thắt là DB thì lợi ít; rủi ro state leak
- Điểm cộng: chọn FrankenPHP/RoadRunner/Swoole theo hạ tầng; thử trên một phần traffic; so p95 và RAM

**27. Webhook thanh toán bị xử lý hai lần, và có lần chữ ký bị bypass.** (3.7, 2.6)
- Ý phải có: so chữ ký bằng `hash_equals` trên raw body, không `==`; idempotency theo transaction id của cổng với unique index
- Điểm cộng: trả 200 nhanh rồi xử lý trong queue; kiểm timestamp chống replay ([09-api-design.md](09-api-design.md))

**28. `unserialize()` dữ liệu người dùng nguy hiểm thế nào?** (3.7)
- Ý phải có: object injection, magic method chạy, gadget chain tới RCE; dùng JSON hoặc `allowed_classes => false`
- Điểm cộng: phpggc; lộ `APP_KEY` với cookie serialize; `phar://` trước 8.0

**29. Thiết kế import CSV 5 triệu dòng chạy tiếp được khi lỗi giữa chừng.** (3.6, 2.6)
- Ý phải có: đọc stream bằng generator, batch insert, transaction ngắn mỗi lô, chạy trong queue, lưu offset/tiến độ
- Điểm cộng: idempotent theo khoá nghiệp vụ (upsert); validate trước, báo cáo dòng lỗi; điều tốc theo replica lag; batch job của Laravel
- Red flag: `file()` rồi `foreach` trong một request HTTP

**30. Laravel hay Symfony cho một dự án mới có domain phức tạp?** (3.8)
- Ý phải có: tuỳ đội và domain; Active Record và Data Mapper khác nhau ở chỗ giữ invariant; container runtime và compile
- Điểm cộng: nói được cách giữ domain sạch trong Laravel (tách entity khỏi Eloquent, service layer, PHPStan level cao)
- Red flag: "Laravel chỉ dành cho dự án nhỏ" hoặc ngược lại mà không có lý do

---

## Bài tập tự làm

1. **Bẫy ngôn ngữ.** Viết một đoạn PHP 10–15 dòng minh hoạ cạm bẫy `foreach` by reference và
   một đoạn minh hoạ `in_array` so sánh lỏng. Dự đoán output trước, rồi mới chạy (`php file.php`).
   Thêm một đoạn đo `memory_get_usage()` trước và sau khi gán, rồi sửa một array 10 triệu phần tử.
2. **Tinh chỉnh FPM.** Với một server 8 GB RAM chạy Nginx + PHP-FPM + Redis, viết ra các bước bạn
   sẽ làm để chọn `pm`, `pm.max_children`, `pm.max_requests`, các timeout, kèm lý do. Không cần
   con số đúng, cần quy trình đúng.
3. **Lifecycle.** Vẽ sơ đồ (ASCII) một request Laravel từ `public/index.php` tới khi terminable
   middleware chạy, ghi rõ service provider `register`/`boot` nằm ở bước nào và `defer()` chạy ở đâu.
4. **Queue job.** Thiết kế một job gọi API đối tác bị giới hạn 60 request/phút, phải idempotent
   và không chạy trùng theo `order_id`. Liệt kê cấu hình `tries`/`backoff`/`retryUntil`/
   middleware/`retry_after` bạn chọn và vì sao.
5. **Octane.** Liệt kê 5 chỗ trong một codebase Laravel bạn từng làm có thể gây state leak nếu
   bật Octane, và cách sửa từng chỗ.
6. **Chất lượng code.** Đưa PHPStan + Larastan vào một project Laravel: tạo baseline, cấu hình CI
   chặn lỗi mới, rồi chạy Rector với set PHP 8.4 trên một thư mục. Ghi lại số lỗi baseline và
   ba loại lỗi phổ biến nhất.

> Nộp bài vào đây để được review.
