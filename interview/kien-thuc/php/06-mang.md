# Chương 06. Mảng (array)

> [← Mục lục](README.md) · [← Chương 05: Chuỗi (string)](05-chuoi.md) · [Chương 07: Toán tử và cấu trúc điều khiển →](07-toan-tu-dieu-khien.md)

**Bạn sẽ học được:**

- Array của PHP thực chất là gì (một *ordered map*), và vì sao một kiểu duy nhất đóng được vai list,
  map, set, stack.
- Luật về key: key chỉ là `int` hoặc `string`, PHP tự đổi kiểu key ra sao (`'1'` thành `1`,
  `true` thành `1`, `null` thành `''`...) và những bug sinh ra từ đó.
- Thêm, xoá, duyệt phần tử; `foreach` by value và by reference cùng các cái bẫy kinh điển;
  destructuring và spread `...`.
- Các hàm mảng dùng hằng ngày, hàm nào giữ key, hàm nào đánh số lại, hàm nào so sánh lỏng `==`.
- Sắp xếp: chọn đúng hàm trong họ `sort`, viết comparator, và ý nghĩa của "sort ổn định từ PHP 8.0".
- Array được copy thế nào (copy-on-write) và vài quy tắc hiệu năng: vì sao `isset` nhanh hơn
  `in_array` rất nhiều trên array lớn.

**Cần biết trước:** [Chương 03](03-cu-phap-bien-hang.md) (biến, `echo`, chạy file PHP),
[Chương 04](04-kieu-du-lieu.md) (các kiểu dữ liệu, `==` và `===`, ép kiểu),
[Chương 05](05-chuoi.md) (chuỗi, numeric string).

Mọi ví dụ trong chương là file PHP hoàn chỉnh (hoặc đoạn ngắn có thể dán vào một file như vậy).
Chạy bằng `php ten-file.php`, hoặc không cần cài gì: `docker run --rm -it php:8.5-cli php -a` rồi
dán code vào. Output ghi trong comment đã được chạy thật trên PHP 8.5, trừ chỗ ghi "output minh hoạ".
Output nhiều dòng của `var_dump` đôi khi được viết gọn trên một dòng, và đường dẫn file trong thông
báo lỗi được thay bằng `...`.

---

## 1. Array là gì và để làm gì

### 1.1 Bài toán: giữ nhiều giá trị trong một biến

Một biến giữ một giá trị. Nhưng chương trình thật thường làm việc với cả một nhóm giá trị: các món
trong giỏ hàng, các dòng kết quả của một câu query, các tham số cấu hình. Đặt tên `$item1`,
`$item2`, `$item3` không giải quyết được: bạn không biết trước có bao nhiêu món, và không thể duyệt
chúng bằng một vòng lặp.

*Array* (mảng) là kiểu dữ liệu giữ nhiều giá trị trong cùng một biến. Mỗi giá trị được gắn với một
*key* (khoá) để lấy lại nó; cặp key và value gọi là một *phần tử* (*element*).

```php
<?php
declare(strict_types=1);

$cart = ['bút', 'vở', 'thước'];   // 3 phần tử, PHP tự gán key 0, 1, 2
echo $cart[0], PHP_EOL;           // in ra: bút
echo count($cart), PHP_EOL;       // in ra: 3

foreach ($cart as $item) {        // duyệt từng phần tử (mục 5)
    echo $item, PHP_EOL;          // in ra lần lượt: bút, vở, thước
}
```

### 1.2 Array của PHP là một ordered map

Trong C hay Java, "mảng" là một dãy phần tử đánh số 0 tới n-1, kích thước cố định khi tạo, mọi phần
tử cùng một kiểu. Array của PHP khác hẳn. Manual định nghĩa: "An array in PHP is actually an ordered
map", nghĩa là:

- *Map* (còn gọi là *dictionary*, *associative array*): cấu trúc lưu các cặp key → value và cho
  phép tra value theo key. Key không bắt buộc là số liên tục; nó có thể là `'email'`, `42` hay `-7`.
- *Ordered*: map này nhớ thứ tự các phần tử được thêm vào. Duyệt array luôn đi theo đúng thứ tự
  đó, cho tới khi bạn chủ động sắp xếp lại.

Bên trong, PHP cài đặt map này bằng một *hash table* (bảng băm): key được đưa qua một *hàm băm*
(*hash function*) để ra một con số, con số đó cho biết phần tử nằm ở đâu, nên tra theo key không cần
dò từng phần tử. Thời gian tra trung bình là O(1), tức là gần như không tăng khi array lớn lên. Cấu
trúc bên trong (bucket, packed array) được mổ xẻ ở [Chương 19](19-ben-trong-engine.md); ở chương này
chỉ cần nhớ hai tính chất: tra theo key nhanh, và giữ thứ tự chèn.

Nhờ hai tính chất đó, cùng một kiểu `array` đóng được nhiều vai mà ngôn ngữ khác phải dùng nhiều
kiểu riêng:

```php
<?php
declare(strict_types=1);

// Vai 1: danh sách (list), key tự đánh số 0, 1, 2...
$fruits = ['tao', 'cam', 'xoai'];
echo $fruits[1], PHP_EOL;              // in ra: cam

// Vai 2: bảng tra (map), key do bạn đặt
$prices = ['tao' => 30000, 'cam' => 25000];
echo $prices['cam'], PHP_EOL;          // in ra: 25000

// Vai 3: tập hợp (set), chỉ quan tâm key có mặt hay không
$seen = ['an' => true, 'binh' => true];
var_dump(isset($seen['an']));          // in ra: bool(true)

// Vai 4: stack (ngăn xếp), vào sau ra trước
$stack = [];
$stack[] = 'a';
$stack[] = 'b';
echo array_pop($stack), PHP_EOL;       // in ra: b

// Vai 5: cấu trúc lồng nhau (bản ghi, cây)
$user = ['name' => 'An', 'roles' => ['admin', 'editor']];
echo $user['roles'][0], PHP_EOL;       // in ra: admin

// Thứ tự giữ đúng như lúc thêm vào, kể cả khi key lẫn số và chuỗi
$order = [];
$order['z'] = 1;
$order['a'] = 2;
$order[5] = 3;
echo implode(',', array_keys($order)), PHP_EOL; // in ra: z,a,5
```

Đối chiếu với hai ngôn ngữ khác trong repo:

| Vai trò | PHP | Java | Go |
|---|---|---|---|
| Danh sách | `array` key 0..n-1 | `T[]`, `ArrayList<T>` | slice `[]T` |
| Bảng tra | `array` key chuỗi hoặc số | `HashMap<K,V>` (không đảm bảo thứ tự), `LinkedHashMap<K,V>` (giữ thứ tự chèn) | `map[K]V` (thứ tự duyệt không được đảm bảo) |
| Tập hợp | `array` dùng key | `HashSet<T>` | `map[T]struct{}` |
| Stack | `array` + `array_push`/`array_pop` | `ArrayDeque<T>` | slice + `append` và cắt đuôi |

Cái giá của sự tiện lợi:

- Tốn bộ nhớ hơn nhiều so với mảng của C, Java hay Go, vì mỗi phần tử phải mang theo thông tin kiểu,
  và với array có key tuỳ ý thì cả key lẫn giá trị băm (số đo cụ thể ở mục 10.3).
- Không có kiểm tra kiểu ở cấp phần tử: cùng một array có thể chứa `int`, `string`, array khác.
  Type hint `array` chỉ nói "đây là array", không nói "array của `int`". Muốn mô tả chi tiết hơn thì
  dùng PHPDoc như `list<int>` hay `array<string, User>` cho công cụ phân tích tĩnh
  ([Chương 21](21-chat-luong-code.md)).
- "List" và "map" là cùng một kiểu, nên một list rất dễ bị biến thành map mà không ai để ý (key bị
  lủng lỗ sau khi xoá hay lọc). Bug này xuất hiện nhiều lần trong chương (mục 3.1, 7.3).

### 1.3 Tạo array

Có hai cú pháp tương đương: `[...]` (ngắn, dùng trong code hiện đại) và `array(...)` (cũ, vẫn gặp
trong code lâu năm). Bên trong là các cặp `key => value` cách nhau bởi dấu phẩy; bỏ `key =>` thì PHP
tự gán key số (mục 2.4).

```php
<?php
declare(strict_types=1);

$empty  = [];                                  // array rỗng
$list   = [10, 20, 30];                        // key 0, 1, 2
$map    = ['host' => 'localhost', 'port' => 3306];
$old    = array('host' => 'localhost');        // cú pháp cũ, cùng kết quả
$nested = [
    'db'    => ['host' => 'localhost', 'port' => 3306],
    'debug' => true,                           // dấu phẩy cuối được phép
];

echo $nested['db']['port'], PHP_EOL;           // in ra: 3306
```

Dấu phẩy sau phần tử cuối là tuỳ chọn. Với array viết trên nhiều dòng, nên luôn để dấu phẩy đó:
thêm phần tử mới chỉ sửa một dòng, diff trong git gọn hơn.

Value có thể là bất kỳ kiểu nào: số, chuỗi, `null`, object, closure, array khác. Key thì bị giới hạn
chặt hơn nhiều, và đó là chủ đề của mục 2.

### 1.4 Xem nội dung một array

`echo` không in được array (nó in chữ `Array` kèm Warning "Array to string conversion"). Khi cần xem
bên trong, có bốn công cụ:

```php
<?php
declare(strict_types=1);

$a = ['id' => 7, 'tags' => ['php', 'sql'], 'active' => true, 'note' => null];

var_dump($a);
print_r($a);
var_export($a);
echo PHP_EOL, json_encode($a), PHP_EOL;
```

Output (rút gọn phần lặp lại):

```
array(4) {                      <- var_dump: có kiểu và độ dài của từng giá trị
  ["id"]=>
  int(7)
  ["tags"]=>
  array(2) {
    [0]=>
    string(3) "php"
    ...
  }
  ["active"]=>
  bool(true)
  ["note"]=>
  NULL
}
Array                           <- print_r: dễ đọc nhưng mất thông tin kiểu
(
    [id] => 7
    [tags] => Array
        (
            [0] => php
            [1] => sql
        )

    [active] => 1               <- true in thành 1
    [note] =>                   <- null in thành rỗng
)
array (                         <- var_export: in ra code PHP hợp lệ
  'id' => 7,
  'tags' =>
  array (
    0 => 'php',
    1 => 'sql',
  ),
  'active' => true,
  'note' => NULL,
)
{"id":7,"tags":["php","sql"],"active":true,"note":null}   <- json_encode
```

| Công cụ | Dùng khi | Lưu ý |
|---|---|---|
| `var_dump()` | Debug, cần biết chính xác kiểu | Dài, nhưng không giấu gì |
| `print_r()` | Xem nhanh cấu trúc | `true` thành `1`, `false` và `null` thành rỗng: dễ đọc nhầm |
| `var_export()` | Cần code PHP tái tạo được array (sinh file config, test) | |
| `json_encode()` | Trả về cho client, ghi log | List thành JSON array `[...]`, còn lại thành JSON object `{...}` (mục 3.1) |

⚠️ Khi debug một giá trị có thể là `false`, `null` hay chuỗi rỗng, đừng dùng `print_r`: cả ba
in ra giống hệt nhau. Dùng `var_dump`.

---

## 2. Key và value

### 2.1 Key chỉ có thể là int hoặc string

Value của array là gì cũng được, nhưng key chỉ có hai kiểu: `int` hoặc `string`. Khi bạn dùng một
giá trị kiểu khác làm key, PHP không báo lỗi mà lặng lẽ đổi nó sang `int` hoặc `string` theo một
bảng luật cố định. Phần lớn thời gian điều này vô hại, nhưng nó là nguồn gốc của cả một họ bug, nên
cần thuộc luật.

### 2.2 Luật đổi kiểu key

| Key bạn viết | Key thật được lưu | Ghi chú |
|---|---|---|
| `'8'`, `'-5'` | `8`, `-5` (int) | Chuỗi là số nguyên thập phân viết dạng chuẩn thì thành int |
| `'08'`, `'+8'`, `' 8'`, `'8.0'`, `'-0'` | giữ nguyên chuỗi | Có số 0 ở đầu, dấu `+`, khoảng trắng, dấu chấm... đều không phải dạng chuẩn |
| `'9223372036854775808'` | giữ nguyên chuỗi | Vượt `PHP_INT_MAX` trên máy 64-bit thì không đổi được sang int |
| `8.7` (float) | `8` | Cắt bỏ phần lẻ (không làm tròn). Từ PHP 8.1 báo Deprecated khi phần lẻ bị mất |
| `true`, `false` | `1`, `0` | |
| `null` | `''` (chuỗi rỗng) | Từ PHP 8.5 báo Deprecated khi đọc, ghi, `isset`, `??` và cả `array_key_exists(null, ...)`; nên viết thẳng `''` |
| array, object | không được | Ném `TypeError` (từ PHP 8.0) |

⚠️ Luật "chuỗi số" của key hẹp hơn luật *numeric string* của phép so sánh và phép toán (Chương 05):
`'08'` hay `'1e3'` là numeric string khi so sánh `==`, nhưng làm key thì vẫn là chuỗi. Chỉ chuỗi
trông giống hệt cách PHP tự in một số nguyên (không dấu `+`, không số 0 ở đầu, không khoảng trắng)
mới bị đổi.

```php
<?php
declare(strict_types=1);

$a = [
    1     => 'a',
    '1'   => 'b',   // '1' là chuỗi số nguyên dạng chuẩn: thành key 1, ghi đè 'a'
    true  => 'c',   // true thành 1, ghi đè tiếp
    '01'  => 'd',   // có số 0 ở đầu: giữ nguyên chuỗi '01'
    '+1'  => 'e',   // có dấu +: giữ nguyên chuỗi
    '1.0' => 'f',   // không phải số nguyên: giữ nguyên chuỗi
    '-1'  => 'g',   // số nguyên âm dạng chuẩn: thành key -1
    false => 'h',   // false thành 0
    ''    => 'i',
];
var_dump($a);
// in ra:
// array(7) {
//   [1]=>
//   string(1) "c"
//   ["01"]=>
//   string(1) "d"
//   ["+1"]=>
//   string(1) "e"
//   ["1.0"]=>
//   string(1) "f"
//   [-1]=>
//   string(1) "g"
//   [0]=>
//   string(1) "h"
//   [""]=>
//   string(1) "i"
// }
```

Nhìn vào `var_dump`: key int in không có dấu nháy (`[1]`), key chuỗi có nháy (`["01"]`). Đây là
cách nhanh nhất để biết key thật sự là kiểu gì.

Float có phần lẻ và `null` làm key giờ đều kèm cảnh báo Deprecated:

```php
<?php
declare(strict_types=1);

$a = [];
$a[2.0] = 'x';      // float không có phần lẻ: thành key 2, không cảnh báo
$a[2.7] = 'y';      // cắt phần lẻ thành 2 (ghi đè 'x')
// PHP 8.1+ in ra: Deprecated: Implicit conversion from float 2.7 to int loses precision in ...
var_dump($a);       // in ra: array(1) { [2]=> string(1) "y" }

$b = [];
$b[null] = 'z';     // null thành ''
// PHP 8.5 in ra: Deprecated: Using null as an array offset is deprecated, use an empty string instead in ...
var_dump(array_keys($b));   // in ra: array(1) { [0]=> string(0) "" }
```

Array hay object làm key thì không có chuyện đổi kiểu, PHP ném `TypeError` ngay:

```php
<?php
declare(strict_types=1);

$a = [];
try {
    $a[['x']] = 1;
} catch (TypeError $e) {
    echo $e->getMessage(), PHP_EOL;
    // PHP 8.3+ in ra: Cannot access offset of type array on array
    // PHP 8.0 tới 8.2 in ra: Illegal offset type
}
```

Muốn dùng object làm key (ví dụ gắn dữ liệu phụ cho từng object) thì array không làm được; dùng
`SplObjectStorage` ([Chương 13](13-generator-iterator-spl.md)) hoặc `WeakMap`.

### 2.3 Key trùng: phần tử sau ghi đè phần tử trước

Trong một array, mỗi key chỉ xuất hiện một lần. Gán vào key đã có thì value cũ bị thay, và phần tử
giữ nguyên vị trí cũ trong thứ tự (không bị đẩy xuống cuối):

```php
<?php
declare(strict_types=1);

$c = ['a' => 1, 'b' => 2, 'a' => 3];
var_dump($c);
// in ra:
// array(2) {
//   ["a"]=>
//   int(3)
//   ["b"]=>
//   int(2)
// }
```

Kết hợp với mục 2.2: `1`, `'1'`, `true`, `1.5` đều là cùng một key `1`, nên chúng ghi đè lẫn nhau.

### 2.4 Key tự động khi không ghi key

Viết `$a[] = $value` (hoặc bỏ `key =>` trong `[...]`) thì PHP tự chọn key: lấy key int lớn nhất từng
có trong array cộng 1; nếu chưa từng có key int nào thì bắt đầu từ 0. (Có một ngoại lệ nhỏ với
`array_pop`, xem mục 4.2.)

```php
<?php
declare(strict_types=1);

$a = ['x', 'y', 5 => 'z'];
$a[] = 'w';                  // key int lớn nhất đang là 5, nên key mới là 6
$a['name'] = 'An';           // key chuỗi không ảnh hưởng bộ đếm
$a[] = 'v';                  // key 7
echo implode(',', array_keys($a)), PHP_EOL;   // in ra: 0,1,5,6,name,7

$b = [10, 20, 30];
unset($b[2]);                // xoá phần tử key 2
$b[] = 40;                   // key mới là 3, KHÔNG phải 2
echo implode(',', array_keys($b)), PHP_EOL;   // in ra: 0,1,3

$c = ['a' => 1];
$c[] = 2;                    // chưa có key int nào: bắt đầu từ 0
echo implode(',', array_keys($c)), PHP_EOL;   // in ra: a,0

$d = [];
$d[-5] = 'x';
$d[] = 'y';
echo implode(',', array_keys($d)), PHP_EOL;   // PHP 8.3+: -5,-4. PHP 8.0 tới 8.2: -5,0
```

Hai điều cần để ý:

- Bộ đếm nhớ key lớn nhất *từng* tồn tại, không phải key lớn nhất *đang* tồn tại. Xoá phần tử cuối
  rồi thêm mới sẽ để lại một "lỗ" trong dãy key (`0,1,3` ở trên). Muốn đánh số lại từ 0 thì dùng
  `array_values()` (mục 7.2).
- Key âm: nếu key int lớn nhất là số âm `n` thì key kế tiếp là `n + 1`. Riêng trường hợp gán key âm
  vào một array rỗng như `$d` ở trên, quy tắc này chỉ áp dụng từ PHP 8.3; bản 8.0 tới 8.2 cho key
  kế tiếp là 0.

Nếu key `PHP_INT_MAX` đã bị dùng thì `$a[] = ...` không còn chỗ, PHP ném `Error` "Cannot add element
to the array as the next element is already occupied". Trường hợp này hiếm, chỉ cần biết là có.

### 2.5 Hệ quả thực tế của việc đổi kiểu key

Mọi dữ liệu đến từ bên ngoài (query string, form, CSV, header) đều là chuỗi. Khi dùng chúng làm key,
những chuỗi như `'15'` lặng lẽ biến thành int, và vài dòng sau đó bug xuất hiện ở chỗ không ngờ:

```php
<?php
declare(strict_types=1);

// ID đọc từ form, query string, CSV... luôn là chuỗi
$rows = [
    ['id' => '15', 'name' => 'An'],
    ['id' => '7',  'name' => 'Binh'],
];

$byId = [];
foreach ($rows as $row) {
    $byId[$row['id']] = $row['name'];   // key '15' bị đổi thành int 15
}

var_dump(array_keys($byId));                        // in ra: array(2) { [0]=> int(15) [1]=> int(7) }, cả hai là int
var_dump(in_array('15', array_keys($byId), true));  // in ra: bool(false)
var_dump(isset($byId['15']));                       // in ra: bool(true), vì khi tra '15' cũng thành 15

// Bẫy: array_merge đánh số lại mọi key int (mục 7.5), ID mất sạch
$merged = array_merge($byId, ['99' => 'Cuong']);
echo json_encode($merged), PHP_EOL;                 // in ra: ["An","Binh","Cuong"]

// Bẫy: key int đi vào tham số string trong file strict_types
function label(string $id): string
{
    return "#{$id}";
}

$firstId = array_key_first($byId);   // key đầu tiên: int 15
try {
    echo label($firstId), PHP_EOL;
} catch (TypeError $e) {
    echo $e->getMessage(), PHP_EOL;
    // in ra: label(): Argument #1 ($id) must be of type string, int given, called in ...
}
echo label((string) $firstId), PHP_EOL;  // in ra: #15

// json_decode sang array cũng đổi key như vậy
var_dump(json_decode('{"10": "a", "x": "b"}', true));
// in ra: array(2) { [10]=> string(1) "a" ["x"]=> string(1) "b" }
```

Cách phòng:

- Coi kiểu của key là "int hoặc string, không chắc cái nào". Khi cần đúng kiểu, ép rõ ràng:
  `(string) $id`, `(int) $id`.
- Khi so sánh key lấy từ `array_keys()` với dữ liệu ngoài, đổi cả hai về cùng một kiểu trước rồi
  mới dùng `===`, hoặc tra bằng `isset($map[$id])` (tra key thì cả hai phía đều được đổi theo cùng
  một luật).
- Đừng dùng `array_merge` cho array mà key là ID (mục 7.5).

---

## 3. Mảng chỉ số, mảng kết hợp, mảng nhiều chiều

PHP chỉ có một kiểu `array`, nhưng trong thực tế người ta dùng nó theo ba "hình dạng" khác nhau.
Gọi đúng tên hình dạng giúp bạn chọn đúng hàm và tránh đúng bẫy.

### 3.1 Mảng chỉ số (indexed array) và list

*Mảng chỉ số* (*indexed array*) dùng key int làm số thứ tự. Trường hợp đặc biệt và hay gặp nhất là
*list*: key đúng là 0, 1, 2... liên tục, theo đúng thứ tự đó. Array tạo bằng `[a, b, c]` hay bằng
các lệnh `$a[] = ...` liên tiếp đều là list.

Từ PHP 8.1 có hàm `array_is_list(array $array): bool` để kiểm tra điều này. Manual định nghĩa: array
là list nếu key của nó gồm các số liên tiếp từ 0 tới `count($array) - 1` (theo đúng thứ tự). Array
rỗng cũng là list.

Vì sao phải phân biệt list với "array có key số bất kỳ"? Vì nhiều thứ chỉ đúng với list:

- `json_encode` xuất list thành JSON array `[...]`, còn mọi array khác thành JSON object `{...}`.
- Vòng `for ($i = 0; $i < count($a); $i++)` chỉ đi đúng mọi phần tử khi key của `$a` đúng là 0 tới
  `count($a) - 1`.
- Destructuring `[$x, $y] = $a` lấy theo key 0, 1 (mục 6.1).

Và list rất dễ bị "lủng lỗ" mà không ai để ý:

```php
<?php
declare(strict_types=1);

$ids = [10, 20, 30, 40];
var_dump(array_is_list($ids));                  // in ra: bool(true)
echo json_encode($ids), PHP_EOL;                // in ra: [10,20,30,40]

unset($ids[1]);                                 // xoá phần tử thứ hai
var_dump(array_is_list($ids));                  // in ra: bool(false), key giờ là 0, 2, 3
echo json_encode($ids), PHP_EOL;                // in ra: {"0":10,"2":30,"3":40}

$ids = array_values($ids);                      // đánh số lại 0, 1, 2
echo json_encode($ids), PHP_EOL;                // in ra: [10,30,40]

var_dump(array_is_list([]));                    // in ra: bool(true)
var_dump(array_is_list([1 => 'a', 0 => 'b']));  // in ra: bool(false): đủ key 0 và 1 nhưng sai thứ tự
```

⚠️ Đây là bug API rất phổ biến: server trả `[10,20,30,40]`, sau một lần sửa code có thêm `unset`
hoặc `array_filter` (mục 7.3), cùng endpoint đó trả `{"0":10,"2":30,"3":40}`, và client JavaScript
đang gọi `.map()` trên kết quả thì vỡ. Quy tắc: trước khi trả một list ra ngoài (JSON, API), gọi
`array_values()` nếu có bất kỳ bước nào có thể xoá phần tử.

### 3.2 Mảng kết hợp (associative array)

*Mảng kết hợp* (*associative array*) dùng key chuỗi có nghĩa, giống một bản ghi hay một bảng tra:

```php
$user = ['id' => 7, 'email' => 'an@example.com', 'active' => true];
$httpStatus = [200 => 'OK', 404 => 'Not Found', 500 => 'Internal Server Error'];
```

Ví dụ thứ hai có key là số, nhưng về bản chất nó là bảng tra (mã → tên), không phải list: số 404
mang nghĩa, không phải số thứ tự. Phân biệt hai loại theo cách dùng chứ không theo kiểu của key.

Array kết hợp rất tiện để chở dữ liệu tạm (đọc config, decode JSON, một dòng kết quả query). Nhưng
khi dữ liệu có cấu trúc cố định và đi qua nhiều tầng code, nó có nhược điểm: PHP không biết array có
những key gì, nên gõ sai tên key (`$user['emial']`) chỉ lộ ra lúc chạy, dưới dạng Warning và `null`.
Công cụ phân tích tĩnh chỉ bắt được lỗi này nếu bạn tự mô tả "hình dạng" của array bằng PHPDoc
(`array{id: int, email: string}`). Với dữ liệu như vậy, một class nhỏ với property có kiểu
([Chương 09](09-oop-co-ban.md)) an toàn hơn nhiều.

### 3.3 Mảng nhiều chiều

Value của array có thể là array khác, nên ta có *mảng nhiều chiều* (*multidimensional array*): ma
trận, bảng dữ liệu, cây. Truy cập bằng nhiều cặp ngoặc liên tiếp.

```php
<?php
declare(strict_types=1);

// Ma trận 2 x 3: array của các array
$matrix = [
    [1, 2, 3],
    [4, 5, 6],
];
echo $matrix[1][2], PHP_EOL;          // in ra: 6 (hàng 1, cột 2)

foreach ($matrix as $row) {
    echo implode(' ', $row), PHP_EOL;
}
// in ra:
// 1 2 3
// 4 5 6

// Dữ liệu dạng bảng: list các bản ghi, giống kết quả một câu query
$orders = [
    ['id' => 1, 'customer' => 'an',   'total' => 100],
    ['id' => 2, 'customer' => 'binh', 'total' => 50],
    ['id' => 3, 'customer' => 'an',   'total' => 70],
];

// Gom nhóm theo khách hàng: array con được tạo ngay khi gán lần đầu
$byCustomer = [];
foreach ($orders as $order) {
    $byCustomer[$order['customer']][] = $order['total'];
}
echo json_encode($byCustomer), PHP_EOL;   // in ra: {"an":[100,70],"binh":[50]}
```

Dòng `$byCustomer[$order['customer']][] = ...` chạy được dù `$byCustomer['an']` chưa tồn tại: khi
*ghi* vào một vị trí chưa có (hoặc đang là `null`), PHP tự tạo array rỗng ở đó rồi ghi tiếp. Tính
năng này gọi là *autovivification*. Hai giới hạn:

- Tự tạo từ `false` bị deprecated từ PHP 8.1 (`$f = false; $f[] = 1;` in ra "Deprecated: Automatic
  conversion of false to array is deprecated").
- Không áp dụng cho chuỗi: `$s = ''; $s[] = 'a';` ném `Error` "[] operator not supported for
  strings".

Manual khuyên luôn khởi tạo biến bằng `$x = [];` thay vì trông vào autovivification, vì nếu biến đó
tình cờ đang chứa một chuỗi thì `[]` sẽ hiểu thành truy cập ký tự của chuỗi.

### 3.4 Đọc key không tồn tại

Ghi vào key chưa có thì tạo mới. Còn *đọc* một key chưa có thì PHP trả về `null` kèm Warning (từ
PHP 8.0; trước đó chỉ là Notice):

```php
<?php
declare(strict_types=1);

$a = ['x' => 1];
var_dump($a['y']);
// in ra:
// Warning: Undefined array key "y" in ... on line 5
// NULL

$list = [10, 20];
$v = $list[5];      // in ra: Warning: Undefined array key 5 in ...

$n = null;
$w = $n['k'];       // in ra: Warning: Trying to access array offset on null in ...
                    // (PHP 8.0 tới 8.2: "... on value of type null")
```

Warning không dừng chương trình, nên code chạy tiếp với `null` và hỏng ở chỗ khác, xa nơi gây lỗi.
Có ba cách đọc an toàn:

| Cách | Ý nghĩa | Dùng khi |
|---|---|---|
| `$a['k'] ?? 'mặc định'` | Key không có, hoặc có mà value là `null`, thì lấy giá trị mặc định | Cách thường dùng nhất để đọc input, config |
| `isset($a['k'])` | `true` khi key có mặt và value khác `null` | Kiểm tra trước khi xử lý |
| `array_key_exists('k', $a)` | `true` khi key có mặt, kể cả value là `null` | Khi `null` là một giá trị hợp lệ cần phân biệt với "không có" |

Toán tử `??` và `isset` không phát Warning dù đi sâu nhiều cấp: `$config['cache']['ttl'] ?? 60` trả
`60` khi `'cache'` không tồn tại mà không in gì. Khác biệt giữa `isset` và `array_key_exists` được
phân tích kỹ ở mục 7.1.

---

## 4. Thêm, sửa, xoá phần tử

### 4.1 Thêm và sửa

| Thao tác | Cách viết | Ghi chú |
|---|---|---|
| Thêm vào cuối, key tự động | `$a[] = $v;` | Cách thường dùng nhất |
| Thêm hoặc sửa theo key | `$a['k'] = $v;` | Key đã có thì ghi đè value, vị trí giữ nguyên |
| Thêm nhiều phần tử vào cuối | `array_push($a, $v1, $v2)` | Trả về số phần tử mới |
| Thêm vào đầu | `array_unshift($a, $v1, $v2)` | Key số bị đánh lại từ 0, key chuỗi giữ nguyên |

Manual của `array_push` khuyên: nếu chỉ thêm một phần tử thì dùng `$a[] = $v`, vì không tốn chi phí
gọi hàm.

`array_push`, `array_pop`, `array_shift`, `array_unshift`, và cả họ hàm `sort` ở mục 8, nhận array
*by reference* (`array &$array` trong chữ ký hàm): chúng sửa trực tiếp biến bạn truyền vào. Vì vậy
phải truyền một biến. Truyền kết quả của một lời gọi hàm (`array_pop(getItems())`) chỉ nhận Notice
"Only variables should be passed by reference" và hàm sửa một bản tạm rồi vứt đi; truyền thẳng một
array viết sẵn như `sort([3, 1, 2])` thì ném `Error` "... could not be passed by reference".

### 4.2 Xoá

```php
<?php
declare(strict_types=1);

$a = ['a', 'b', 'c', 'd', 'e', 'f'];

$last  = array_pop($a);             // lấy ra (và xoá) phần tử cuối
$first = array_shift($a);           // lấy ra phần tử đầu, key số được đánh lại từ 0
echo $first, ' ', $last, ' ', json_encode($a), PHP_EOL;  // in ra: a f ["b","c","d","e"]

unset($a[1]);                       // xoá key 1, KHÔNG đánh số lại
echo json_encode($a), PHP_EOL;      // in ra: {"0":"b","2":"d","3":"e"}
unset($a[99]);                      // xoá key không tồn tại: không lỗi, không cảnh báo

$m = [5 => 'five', 'x' => 'ex', 9 => 'nine'];
array_shift($m);                    // key chuỗi giữ nguyên, key số đánh lại từ 0
var_dump($m);                       // in ra: array(2) { ["x"]=> string(2) "ex" [0]=> string(4) "nine" }

$e = [];
var_dump(array_pop($e));            // in ra: NULL (array rỗng thì trả null)
```

Ba điều hay bị hiểu sai:

- `unset($a[$k])` xoá phần tử nhưng không dồn các phần tử phía sau lên. List bị lủng lỗ (mục 3.1);
  cần `array_values()` để đánh số lại.
- Gán `$a[$k] = null` *không* xoá phần tử: key vẫn còn, `count()` không giảm,
  `array_key_exists($k, $a)` vẫn `true`. Chỉ `unset` (hoặc các hàm như `array_pop`, `array_splice`)
  mới xoá.
- `array_pop` và `array_shift` trả `null` khi array rỗng. Nếu array của bạn có thể chứa `null` như
  một giá trị thật thì không phân biệt được "rỗng" với "lấy ra được null"; kiểm tra `count()` trước.

Một chi tiết nhỏ khác giữa `unset` và `array_pop`: sau `array_pop`, bộ đếm key tự động lùi lại nên
`$a[] = ...` dùng lại đúng key vừa bị lấy ra; sau `unset` thì không (mục 2.4).

```php
<?php
declare(strict_types=1);

$p = [1, 2, 3];
array_pop($p);
$p[] = 9;
echo implode(',', array_keys($p)), PHP_EOL;   // in ra: 0,1,2

$u = [1, 2, 3];
unset($u[2]);
$u[] = 9;
echo implode(',', array_keys($u)), PHP_EOL;   // in ra: 0,1,3
```

Xoá ở giữa và dồn lại cho liền thì dùng `array_splice` (mục 7.6). Xoá theo điều kiện thì dùng
`array_filter` (mục 7.3).

### 4.3 Stack, queue và cái giá của array_shift

- *Stack* (ngăn xếp, vào sau ra trước): thêm bằng `$a[] = ...`, lấy bằng `array_pop`. Cả hai đều
  nhanh, không phụ thuộc kích thước array.
- *Queue* (hàng đợi, vào trước ra trước): thêm bằng `$a[] = ...`, lấy bằng `array_shift`. Chạy đúng,
  nhưng `array_shift` phải đánh số lại *toàn bộ* key số còn lại (mã nguồn của nó là một vòng lặp đi
  qua mọi phần tử để dời chúng về đầu). Nghĩa là mỗi lần lấy tốn O(n); lấy hết một hàng đợi n phần
  tử tốn O(n²). Với vài chục phần tử thì không sao, với hàng trăm nghìn phần tử (ví dụ duyệt đồ thị
  bằng BFS) thì rất chậm.

`array_unshift` cũng O(n) vì lý do tương tự. Khi cần queue lớn, dùng `SplQueue`
([Chương 13](13-generator-iterator-spl.md)), hoặc giữ một biến chỉ số `$head` tăng dần thay vì xoá
phần tử đầu.

### 4.4 Tạo nhanh một array có sẵn dữ liệu

```php
<?php
declare(strict_types=1);

echo json_encode(range(1, 5)), PHP_EOL;           // in ra: [1,2,3,4,5]
echo json_encode(range(0, 10, 5)), PHP_EOL;       // in ra: [0,5,10], bước nhảy 5
echo json_encode(range(5, 1)), PHP_EOL;           // in ra: [5,4,3,2,1], tự đi lùi
echo json_encode(range('a', 'e')), PHP_EOL;       // in ra: ["a","b","c","d","e"]

echo json_encode(array_fill(0, 3, 'x')), PHP_EOL;            // in ra: ["x","x","x"]
echo json_encode(array_fill_keys(['a', 'b'], 0)), PHP_EOL;   // in ra: {"a":0,"b":0}
```

`range()` tạo cả array trong bộ nhớ ngay lập tức: đo bằng `memory_get_usage()`, `range(1, 1_000_000)`
chiếm khoảng 16 MiB trên PHP 8.5 (khoảng 32 MiB trên 8.1). Nếu chỉ cần duyệt qua một dãy số lớn thì
dùng vòng `for` hoặc *generator* (Chương 13), không cần tạo array.

---

## 5. Duyệt mảng

### 5.1 foreach by value

`foreach` là cách chính để đi qua mọi phần tử, theo đúng thứ tự trong array. Có hai dạng: chỉ lấy
value, hoặc lấy cả key và value.

```php
<?php
declare(strict_types=1);

$prices = ['tao' => 30000, 'cam' => 25000];

foreach ($prices as $name => $price) {
    echo "{$name}: {$price}", PHP_EOL;
}
// in ra:
// tao: 30000
// cam: 25000

// $price chỉ là bản sao của value: sửa nó không đổi array
foreach ($prices as $name => $price) {
    $price = 0;
}
echo $prices['tao'], PHP_EOL;              // in ra: 30000

// Muốn sửa array thì ghi qua key: cách an toàn để cập nhật tại chỗ
foreach ($prices as $name => $price) {
    $prices[$name] = $price * 2;
}
echo json_encode($prices), PHP_EOL;        // in ra: {"tao":60000,"cam":50000}
```

Ở dạng mặc định (*by value*), mỗi vòng PHP gán value của phần tử hiện tại vào biến `$price`. Biến
này là bản sao, nên gán lại nó không ảnh hưởng gì tới array.

Một hệ quả ít người biết: từ PHP 7, `foreach` by value duyệt trên *bản của array tại lúc bắt đầu
vòng lặp* (migration guide của PHP 7.0: "foreach will now operate on a copy of the array being
iterated rather than the array itself"). Thêm hay xoá phần tử của chính array đó bên trong vòng lặp
không làm thay đổi những gì vòng lặp duyệt qua:

```php
<?php
declare(strict_types=1);

$nums = [1, 2, 3];
foreach ($nums as $i => $n) {
    if ($i === 0) {
        $nums[] = 99;      // thêm vào cuối
        unset($nums[1]);   // xoá phần tử thứ hai
    }
    echo $n, ' ';
}
echo PHP_EOL;                              // in ra: 1 2 3
echo json_encode($nums), PHP_EOL;          // in ra: {"0":1,"2":3,"3":99}
```

Vòng lặp vẫn in `1 2 3`: phần tử 2 đã bị xoá vẫn được duyệt, phần tử 99 mới thêm thì không. Chữ
"copy" ở đây không có nghĩa là tốn bộ nhớ gấp đôi: nhờ copy-on-write (mục 9), PHP chỉ thật sự copy
khi bạn ghi vào array trong lúc đang duyệt.

`foreach` trên một giá trị không phải array hay object (ví dụ `null` vì query không trả gì) chỉ in
Warning "foreach() argument must be of type array|object, null given" rồi bỏ qua vòng lặp.

### 5.2 foreach by reference

Thêm `&` trước biến value thì mỗi vòng, biến đó trở thành *reference* (một tên khác cho cùng ô nhớ)
tới phần tử thật trong array. Ghi vào biến là ghi thẳng vào array:

```php
<?php
declare(strict_types=1);

$a = [1, 2, 3];
foreach ($a as &$v) {
    $v = $v * 10;          // ghi qua reference: sửa thẳng phần tử của $a
}
var_dump($a);
// in ra:
// array(3) {
//   [0]=>
//   int(10)
//   [1]=>
//   int(20)
//   [2]=>
//   &int(30)       <- dấu &: phần tử này vẫn đang dính reference với $v
// }

// Dùng lại tên $v ở vòng sau mà quên unset
foreach ($a as $v) {}
echo json_encode($a), PHP_EOL;   // in ra: [10,20,20]  phần tử cuối bị hỏng!
```

Vì sao phần tử cuối thành 20? Khi vòng lặp thứ nhất kết thúc, `$v` không biến mất: nó vẫn là
reference tới `$a[2]`. Vòng thứ hai là by value, mỗi bước *gán* value hiện tại vào `$v`, tức là ghi
vào `$a[2]`:

| Bước của vòng thứ hai | Lệnh ngầm | `$a` sau bước đó |
|---|---|---|
| Bắt đầu | (`$v` và `$a[2]` là cùng một ô) | `[10, 20, 30]` |
| 1 | `$v = $a[0]`, tức ghi 10 vào `$a[2]` | `[10, 20, 10]` |
| 2 | `$v = $a[1]`, tức ghi 20 vào `$a[2]` | `[10, 20, 20]` |
| 3 | `$v = $a[2]`, gán `$a[2]` cho chính nó | `[10, 20, 20]` |

Kết quả luôn là: phần tử cuối bị thay bằng phần tử kế cuối. Bug này không báo lỗi gì, và thường
nằm cách xa vòng lặp gây ra nó (vòng thứ hai có thể ở cuối hàm, viết bởi người khác).

Cách sửa, theo thứ tự ưu tiên:

1. Tránh `foreach` by reference. Ghi qua key (`$a[$k] = ...` như mục 5.1), hoặc tạo array mới bằng
   `array_map` (mục 7.3). Code dễ đọc hơn, không có trạng thái ẩn.
2. Nếu vẫn dùng `&`, luôn `unset($v);` ngay sau vòng lặp. `unset` chỉ xoá *cái tên* `$v`, cắt liên
   kết; nó không xoá `$a[2]`. Manual cũng khuyên đúng điều này.

```php
<?php
declare(strict_types=1);

$a = [1, 2, 3];
foreach ($a as &$v) {
    $v = $v * 10;
}
unset($v);                       // cắt liên kết giữa $v và $a[2]

foreach ($a as $v) {}
echo json_encode($a), PHP_EOL;   // in ra: [10,20,30]

// by reference duyệt trên array thật: phần tử thêm vào trong lúc duyệt cũng được duyệt tới
$q = [1];
foreach ($q as &$item) {
    echo $item, ' ';
    if ($item < 4) {
        $q[] = $item + 1;
    }
}
unset($item);
echo PHP_EOL;                    // in ra: 1 2 3 4
```

Ví dụ cuối cho thấy khác biệt thứ hai so với by value: by reference duyệt trên chính array, nên phần
tử thêm vào trong lúc duyệt cũng được duyệt tới.

### 5.3 Reference sống sót khi copy array

Bẫy thứ hai nguy hiểm hơn vì nó phá vỡ quy tắc "array được copy theo giá trị". Nếu một *phần tử*
đang là reference (dấu `&` trong `var_dump`), thì khi copy array, phần tử đó vẫn dùng chung giữa bản
gốc và bản copy. Manual trang References gọi hành vi này là "potentially dangerous".

```php
<?php
declare(strict_types=1);

$arr = [1, 2];
$ref = &$arr[0];       // $arr[0] giờ nằm trong một reference set
$copy = $arr;          // copy array bình thường, không có &
$copy[0] = 100;        // tưởng chỉ sửa bản copy...
echo json_encode($arr), PHP_EOL;   // in ra: [100,2]  ...nhưng $arr[0] cũng đổi!

function resetFirst(array $items): void
{
    $items[0] = 0;     // hàm nhận by value, tưởng không ảnh hưởng caller
}
resetFirst($arr);
echo json_encode($arr), PHP_EOL;   // in ra: [0,2]
```

Trong code thật, reference "ẩn" này thường đến từ một `foreach ($arr as &$v)` quên `unset($v)`. Khi
đã `unset` tên còn lại của reference (`unset($ref)` hay `unset($v)`), phần tử lại hành xử bình thường
và các bản copy lại độc lập như mong đợi. Thêm một lý do để làm theo quy tắc ở mục 5.2.

### 5.4 Vòng for với chỉ số

```php
$list = ['a', 'b', 'c'];
for ($i = 0, $n = count($list); $i < $n; $i++) {
    echo $i, ': ', $list[$i], PHP_EOL;
}
```

`for` chỉ đúng khi key của array đúng là 0..n-1 (thường là list). Gặp array có lỗ hoặc key chuỗi, `$list[$i]`
đọc phải key không tồn tại và nhận Warning cộng `null`. Vì vậy với array PHP, `foreach` gần như luôn
là lựa chọn đúng; chỉ dùng `for` khi thật sự cần chỉ số để làm toán (ví dụ so phần tử `$i` với
`$i + 1`), và chỉ sau khi chắc array là list.

Trong code cũ bạn có thể gặp các hàm thao tác *con trỏ nội bộ* (*internal pointer*) của array:
`current()`, `key()`, `next()`, `prev()`, `reset()`, `end()`. Hàm `each()` đã bị xoá ở PHP 8.0.
Từ PHP 7, `foreach` không còn động tới con trỏ này. Code mới hầu như không cần chúng: lấy phần tử
đầu/cuối đã có hàm riêng (mục 7.2).

---

## 6. Destructuring và spread

### 6.1 Destructuring: tách array ra nhiều biến

*Destructuring* (phân rã) là gán nhiều phần tử của một array vào nhiều biến trong một câu lệnh. Có
hai cú pháp tương đương: `[...] = ...` (từ PHP 7.1) và `list(...) = ...` (cũ hơn).

```php
<?php
declare(strict_types=1);

// Lấy theo vị trí (thật ra là theo key 0, 1, 2...)
[$host, $port] = ['localhost', 3306];
echo $host, ':', $port, PHP_EOL;              // in ra: localhost:3306

list($h, $p) = ['127.0.0.1', 5432];           // cú pháp cũ, cùng ý nghĩa
echo $h, ':', $p, PHP_EOL;                    // in ra: 127.0.0.1:5432

// Bỏ qua phần tử bằng dấu phẩy trống
[, , $third] = ['a', 'b', 'c'];
echo $third, PHP_EOL;                         // in ra: c

// Lấy theo key (PHP 7.1+)
['id' => $id, 'email' => $email] = ['id' => 7, 'name' => 'An', 'email' => 'an@example.com'];
echo $id, ' ', $email, PHP_EOL;               // in ra: 7 an@example.com

// Lồng nhau
[$a, [$b, $c]] = [1, [2, 3]];
echo $a + $b + $c, PHP_EOL;                   // in ra: 6

// Đổi chỗ hai biến không cần biến tạm
$x = 1;
$y = 2;
[$x, $y] = [$y, $x];
echo $x, ' ', $y, PHP_EOL;                    // in ra: 2 1

// Hàm trả về "nhiều giá trị" bằng một array, bên gọi tách ra
/** @param list<int> $nums */
function minMax(array $nums): array
{
    return [min($nums), max($nums)];
}
[$min, $max] = minMax([5, 3, 9]);
echo $min, ' ', $max, PHP_EOL;                // in ra: 3 9

// Trong foreach: tách từng dòng ngay tại chỗ
$rows = [['id' => 1, 'name' => 'An'], ['id' => 2, 'name' => 'Binh']];
foreach ($rows as ['id' => $rid, 'name' => $rname]) {
    echo "{$rid}={$rname} ";
}
echo PHP_EOL;                                 // in ra: 1=An 2=Binh
```

Quy tắc cần nhớ:

- Không ghi key thì PHP lấy theo key `0`, `1`, `2`..., *không* theo thứ tự xuất hiện trong array.
- Không được trộn phần tử có key và không có key trong cùng một vế trái.
- Từ PHP 7.3 có thể lấy theo reference: `[&$first] = $arr;` (sửa `$first` là sửa `$arr[0]`). Ít
  dùng, và mang theo mọi rủi ro của reference ở mục 5.
- Toán tử `...` không dùng được ở vế trái (manual: "The spread operator (...) is not supported in
  assignments"), nên không có cú pháp kiểu "lấy phần còn lại".

### 6.2 Bẫy của destructuring

```php
<?php
declare(strict_types=1);

// Bẫy 1: lấy theo KEY 0, 1, không theo thứ tự trong array
[$first, $second] = [1 => 'b', 0 => 'a'];
echo $first, $second, PHP_EOL;                // in ra: ab

// Bẫy 2: list đã lủng lỗ thì key 0 có thể không còn
$evens = array_filter([1, 2, 3, 4], fn(int $n): bool => $n % 2 === 0);  // [1 => 2, 3 => 4]
[$firstEven] = $evens;
// in ra: Warning: Undefined array key 0 in ...
var_dump($firstEven);                         // in ra: NULL

// Bẫy 3: thiếu phần tử
[$u, $v, $w] = [1, 2];
// in ra: Warning: Undefined array key 2 in ...
var_dump($w);                                 // in ra: NULL

// Bẫy 4: vế phải không phải array
[$z] = 42;
// PHP 8.5 in ra: Warning: Cannot use int as array in ...  (PHP 8.4 trở về trước: im lặng)
var_dump($z);                                 // in ra: NULL
```

Bẫy 4 hay gặp khi một hàm "trả array hoặc `false`" thất bại: mọi biến nhận `null` và chương trình
chạy tiếp. Từ PHP 8.5, tách một giá trị không phải array (trừ `null`) thì có Warning; trước đó hoàn
toàn im lặng. Với dữ liệu từ ngoài, kiểm tra `is_array()` và `count()` trước khi tách.

### 6.3 Spread: trải array vào trong array khác

Đặt `...` trước một array (hoặc một object `Traversable` như generator) bên trong `[...]` thì các
phần tử của nó được "trải" ra tại chỗ. Tính năng này có từ PHP 7.4; array có key chuỗi chỉ trải được
từ PHP 8.1 (trước đó ném `Error` "Cannot unpack array with string keys").

```php
<?php
declare(strict_types=1);

$base  = [1, 2];
$extra = [3, 4];
echo json_encode([0, ...$base, ...$extra, 5]), PHP_EOL;   // in ra: [0,1,2,3,4,5]

// Key int bị đánh số lại, giống array_merge
echo json_encode([...[5 => 'a'], ...[5 => 'b']]), PHP_EOL; // in ra: ["a","b"]

// Key chuỗi (PHP 8.1+): bên phải ghi đè bên trái
$defaults = ['timeout' => 30, 'retry' => 3];
$custom   = ['timeout' => 5];
echo json_encode([...$defaults, ...$custom]), PHP_EOL;     // in ra: {"timeout":5,"retry":3}

// Trải một generator cũng được
function gen(): Generator
{
    yield 'x';
    yield 'y';
}
echo json_encode([...gen()]), PHP_EOL;                     // in ra: ["x","y"]
```

Manual nói rõ: trải bằng `...` theo đúng ngữ nghĩa của `array_merge()`: key int bị đánh số lại, key
chuỗi trùng thì cái sau ghi đè cái trước. So sánh đầy đủ với `array_merge` và toán tử `+` ở mục 7.5.

`...` còn dùng trong lời gọi hàm (`sum(...$numbers)`) và trong khai báo tham số (`function
sum(int ...$numbers)`); phần đó thuộc [Chương 08](08-ham.md).

---

## 7. Các hàm mảng thường dùng

PHP 8.5 có gần sáu mươi hàm bắt đầu bằng `array_`, cộng thêm các hàm không có tiền tố (`count`,
`in_array`, họ `sort`...). Không cần thuộc hết. Mục này đi qua những hàm dùng hằng ngày, theo nhóm,
và với mỗi hàm trả lời ba câu hỏi gây bug nhiều nhất: nó *giữ key hay đánh số lại*, nó *so sánh lỏng
hay chặt*, và nó *trả array mới hay sửa array gốc*. Bảng tổng hợp ở mục 7.8.

Một điều cần biết trước: thứ tự tham số của các hàm mảng không nhất quán, do lịch sử để lại.
`array_map($callback, $array)` nhận callback trước, còn `array_filter($array, $callback)` và
`array_reduce($array, $callback)` nhận array trước. Khi không chắc, tra manual hoặc để IDE nhắc.

### 7.1 Đếm và kiểm tra

**`count(Countable|array $value, int $mode = COUNT_NORMAL): int`** trả số phần tử. Với array, PHP lưu sẵn số phần tử nên
`count()` trả ngay, không phải đếm lại (mã nguồn chỉ đọc một trường có sẵn). `COUNT_RECURSIVE` đếm cả
phần tử của các array con. Từ PHP 8.0, `count()` trên giá trị không đếm được (như `null`) ném
`TypeError`, thay vì trả `0` hoặc `1` như trước.

```php
<?php
declare(strict_types=1);

$matrix = [[1, 2], [3, 4, 5]];
echo count($matrix), PHP_EOL;                   // in ra: 2 (chỉ đếm cấp ngoài)
echo count($matrix, COUNT_RECURSIVE), PHP_EOL;  // in ra: 7 (2 array con + 5 số)

try {
    count(null);
} catch (TypeError $e) {
    echo $e->getMessage(), PHP_EOL;
    // in ra: count(): Argument #1 ($value) must be of type Countable|array, null given
}
```

**`in_array(mixed $needle, array $haystack, bool $strict = false): bool`** kiểm tra một *value* có
trong array không.
Mặc định nó so sánh bằng `==` (so sánh lỏng, Chương 04), và `declare(strict_types=1)` không thay đổi
điều đó: `strict_types` chỉ quyết định cách kiểm tra kiểu khi truyền tham số, trả giá trị và gán
property có kiểu; nó không đổi cách các phép so sánh hoạt động.

```php
<?php
declare(strict_types=1);

$roles = ['admin', 'editor'];
var_dump(in_array('admin', $roles, true));     // in ra: bool(true)

// Mặc định in_array so sánh lỏng (==), ngay cả trong file strict_types
var_dump(in_array('1e1', ['10']));             // in ra: bool(true): hai numeric string so như số
var_dump(in_array(null, [0]));                 // in ra: bool(true): null == 0
var_dump(in_array(true, ['khong-lien-quan'])); // in ra: bool(true): true khớp mọi chuỗi truthy
var_dump(in_array('abc', [0]));                // in ra: bool(false)

// Bật strict: so bằng ===
var_dump(in_array('1e1', ['10'], true));       // in ra: bool(false)
var_dump(in_array('7', [7], true));            // in ra: bool(false): khác kiểu
```

Với `in_array('abc', [0])`: trước PHP 8.0, chuỗi không phải số so với `0` bị đổi thành số `0` nên kết
quả là `true`; từ 8.0, số được đổi sang chuỗi rồi so hai chuỗi, nên `false` (manual của `in_array`
ghi rõ thay đổi này). Nhưng như các dòng trên cho thấy, PHP 8 vẫn còn đủ cách để `==` cho kết quả bất
ngờ. Manual khuyên: trừ khi biết chắc kiểu của mọi giá trị, luôn truyền `true` cho `$strict`.

⚠️ Bug kiểm tra quyền kinh điển: `in_array($request['role_id'], $allowedIds)` với `$allowedIds` là
list số nguyên. `role_id` từ request là chuỗi, và khi so lỏng thì `'1.0'`, `'01'`, `' 1'` đều khớp số
`1` (chỉ những chuỗi kiểu `'1abc'` là không còn khớp từ PHP 8). Kiểm tra định dạng input, đổi kiểu rõ
ràng rồi so strict, hoặc dùng `isset` trên một bảng tra (mục 10.2).

**`isset($a[$k])` và `array_key_exists($k, $a)`** đều kiểm tra *key*, khác nhau đúng một điểm: value
là `null`.

```php
<?php
declare(strict_types=1);

$user = ['name' => 'An', 'phone' => null, 'age' => 0];

var_dump(isset($user['phone']));               // in ra: bool(false): key có, nhưng value là null
var_dump(array_key_exists('phone', $user));    // in ra: bool(true)
var_dump(isset($user['email']));               // in ra: bool(false)
var_dump(array_key_exists('email', $user));    // in ra: bool(false)

var_dump(isset($user['age']));                 // in ra: bool(true): 0 không phải null
var_dump(empty($user['age']));                 // in ra: bool(true): 0 là falsy

echo $user['phone'] ?? 'chưa có', PHP_EOL;     // in ra: chưa có
var_dump(isset($user['address']['city']));     // in ra: bool(false), không Warning
```

| | `isset($a['k'])` | `array_key_exists('k', $a)` | `empty($a['k'])` |
|---|---|---|---|
| Key không có | `false` | `false` | `true` |
| Key có, value `null` | `false` | `true` | `true` |
| Key có, value `0`, `''`, `'0'`, `[]`, `false` | `true` | `true` | `true` |
| Key có, value khác | `true` | `true` | `false` |
| Bản chất | Cấu trúc ngôn ngữ, không Warning, đi sâu nhiều cấp được | Hàm, chỉ xét một cấp | Tương đương `!isset($x) \|\| $x == false` |

Chọn thế nào: dùng `isset` (hoặc `??`) trong đa số trường hợp; dùng `array_key_exists` khi `null`
mang nghĩa riêng (ví dụ PATCH request: "gửi `phone: null`" nghĩa là xoá số điện thoại, khác với "không
gửi `phone`"). Cẩn thận với `empty`: chuỗi `'0'` cũng bị coi là rỗng, nên `empty($input['quantity'])`
sẽ từ chối số lượng `'0'` hợp lệ.

**`array_search(mixed $needle, array $haystack, bool $strict = false): int|string|false`** giống
`in_array` nhưng trả về *key* của phần tử đầu tiên tìm thấy, hoặc `false`. Cũng so lỏng nếu không
truyền `true`.

```php
<?php
declare(strict_types=1);

$queue = ['an', 'binh', 'cuong'];
$pos = array_search('an', $queue, true);
var_dump($pos);                                // in ra: int(0)
if (!$pos) {
    echo "Sai: tưởng là không tìm thấy", PHP_EOL;   // dòng này BỊ in ra, vì 0 là falsy
}
if ($pos !== false) {
    echo "Đúng: tìm thấy ở key {$pos}", PHP_EOL;    // in ra: Đúng: tìm thấy ở key 0
}
var_dump(array_search('dung', $queue, true));  // in ra: bool(false)
```

⚠️ Luôn so kết quả của `array_search` với `false` bằng `!==` / `===`. Key `0` (và key `''`) là falsy,
nên `if (!array_search(...))` coi "tìm thấy ở đầu" là "không tìm thấy".

### 7.2 Lấy key, value, phần tử đầu và cuối

```php
<?php
declare(strict_types=1);

$stock = ['pen' => 5, 'book' => 0, 'ruler' => 5];

echo json_encode(array_keys($stock)), PHP_EOL;            // in ra: ["pen","book","ruler"]
echo json_encode(array_values($stock)), PHP_EOL;          // in ra: [5,0,5]
echo json_encode(array_keys($stock, 5, true)), PHP_EOL;   // in ra: ["pen","ruler"]: các key có value === 5

// Phần tử đầu, cuối (không cần biết key là gì)
echo array_key_first($stock), ' ', array_key_last($stock), PHP_EOL;  // in ra: pen ruler (PHP 7.3+)
echo array_first($stock), ' ', array_last($stock), PHP_EOL;          // in ra: 5 5 (PHP 8.5+)
var_dump(array_first([]));                                // in ra: NULL

// array_flip: đổi key thành value và ngược lại
$codes = ['VN', 'US', 'JP'];
echo json_encode(array_flip($codes)), PHP_EOL;            // in ra: {"VN":0,"US":1,"JP":2}
echo json_encode(array_flip(['a' => 1, 'b' => 1])), PHP_EOL;  // in ra: {"1":"b"}: value trùng thì key sau thắng
```

- `array_keys()` trả list các key; nếu truyền thêm value cần tìm thì chỉ trả các key có value đó (so
  lỏng, trừ khi tham số thứ ba là `true`).
- `array_values()` trả list các value, đánh số lại từ 0. Đây là cách chuẩn để "vá lỗ" cho list.
- `array_key_first()` / `array_key_last()` (PHP 7.3) trả key đầu/cuối, `null` nếu array rỗng.
- `array_first()` / `array_last()` (PHP 8.5) trả value đầu/cuối, `null` nếu array rỗng. Trước 8.5
  người ta dùng `reset($a)` / `end($a)`, nhưng RFC của hai hàm mới chỉ ra cách cũ "sai về ngữ nghĩa":
  `reset`/`end` dịch con trỏ nội bộ của array, và nhận tham số by reference nên gọi trên kết quả của
  một hàm thì bị Notice. Code phải chạy được cả trên PHP < 8.5 thì dùng
  `$a === [] ? null : $a[array_key_first($a)]`. Đừng viết `$a[array_key_first($a)] ?? null`: với array
  rỗng, key là `null`, và PHP 8.5 báo Deprecated "Using null as an array offset" kể cả bên trong `??`.
- `array_flip()` đảo key và value. Value phải là `int` hoặc `string` (value kiểu khác bị bỏ qua kèm
  Warning). Công dụng chính: biến một list thành bảng tra để kiểm tra bằng `isset` (mục 10.2).

### 7.3 Biến đổi: array_map, array_filter, array_reduce

Ba hàm này là bộ công cụ "lập trình hàm" của PHP: thay vì viết vòng `foreach` rồi tự đẩy kết quả vào
một array mới, bạn mô tả *phép biến đổi* bằng một callback. Callback thường được viết bằng *arrow
function* `fn(...) => ...` (Chương 08).

```php
<?php
declare(strict_types=1);

$prices = ['pen' => 5000, 'book' => 12000, 'bag' => 0];

// array_map(callback, array): áp callback lên từng value, trả array MỚI
$withTax = array_map(fn(int $p): int => (int) round($p * 1.1), $prices);
echo json_encode($withTax), PHP_EOL;       // in ra: {"pen":5500,"book":13200,"bag":0}  (giữ key)

// array_filter(array, callback): giữ phần tử mà callback trả true, GIỮ KEY
$nonZero = array_filter($prices, fn(int $p): bool => $p > 0);
echo json_encode($nonZero), PHP_EOL;       // in ra: {"pen":5000,"book":12000}

$list = [10, 0, 25, 0, 40];
$filtered = array_filter($list, fn(int $n): bool => $n > 0);
echo json_encode($filtered), PHP_EOL;                 // in ra: {"0":10,"2":25,"4":40}
echo json_encode(array_values($filtered)), PHP_EOL;   // in ra: [10,25,40]

// Lọc theo key, hoặc theo cả value và key
$shortKeys = array_filter($prices, fn(string $k): bool => strlen($k) === 3, ARRAY_FILTER_USE_KEY);
echo json_encode($shortKeys), PHP_EOL;     // in ra: {"pen":5000,"bag":0}
$both = array_filter($prices, fn(int $v, string $k): bool => $v > 0 && $k !== 'pen', ARRAY_FILTER_USE_BOTH);
echo json_encode($both), PHP_EOL;          // in ra: {"book":12000}

// Không truyền callback: bỏ mọi phần tử "rỗng" theo nghĩa của empty(), kể cả '0'
echo json_encode(array_values(array_filter(['a', '', '0', 0, null, 'b', [], false]))), PHP_EOL;  // in ra: ["a","b"]

// array_reduce(array, callback, initial): gộp cả array thành một giá trị
$total = array_reduce($prices, fn(int $carry, int $p): int => $carry + $p, 0);
echo $total, PHP_EOL;                      // in ra: 17000
var_dump(array_reduce([], fn(int $c, int $x): int => $c + $x));   // in ra: NULL (không có initial)

// array_map với nhiều array: callback nhận từng cặp, kết quả đánh số lại
echo json_encode(array_map(fn(string $n, int $q): string => "{$n}x{$q}", ['pen', 'book'], [2, 1])), PHP_EOL;
// in ra: ["penx2","bookx1"]
echo json_encode(array_map(null, [1, 2], ['a', 'b'])), PHP_EOL;  // in ra: [[1,"a"],[2,"b"]] (callback null: "zip")

// array_map chỉ đưa value cho callback. Cần cả key thì truyền array_keys làm array thứ nhất
echo json_encode(array_map(fn(string $k, int $v): string => "{$k}={$v}", array_keys($prices), $prices)), PHP_EOL;
// in ra: ["pen=5000","book=12000","bag=0"]
```

Những điều cần nhớ:

- `array_map` giữ key *khi và chỉ khi* truyền đúng một array (manual: "if and only if exactly one
  array is passed"); từ hai array trở lên, kết quả là list đánh số lại.
- `array_filter` luôn giữ key, nên kết quả trên một list thường bị lủng lỗ. Đây là nguồn chính của
  bug JSON ở mục 3.1. Thói quen tốt: `array_values(array_filter(...))` khi cần list.
- `array_filter` không có callback sẽ bỏ cả `0` và `'0'`. Nếu số 0 là dữ liệu hợp lệ, luôn viết
  callback rõ ràng.
- `array_reduce` không có `initial` thì giá trị khởi đầu là `null`; với callback có kiểu như
  `fn(int $carry, ...)` và một array không rỗng, lần gọi đầu nhận `null` cho tham số `int` nên ném
  `TypeError`. Luôn truyền `initial`.
- ⚠️ Callback được gọi *từ bên trong hàm built-in* không chịu `strict_types` của file bạn (manual:
  "Function calls from within internal functions will not be affected by the strict_types
  declaration"). Trong file strict, `array_map(fn(int $x): int => $x * 2, ['1', '2'])` vẫn chạy và trả
  `[2, 4]` thay vì ném `TypeError`.
- `array_walk($array, $callback)` cũng duyệt từng phần tử nhưng sửa array tại chỗ qua reference
  (callback nhận `&$value, $key`). Ưu tiên `array_map` hoặc `foreach` qua key; lý do như mục 5.2.

So với `foreach`: `array_map`/`array_filter` ngắn và nói rõ ý định, nhưng mỗi lần gọi tạo một array
mới và gọi callback cho từng phần tử. Với logic phức tạp (nhiều nhánh, cần `break` sớm, cần cả key và
value), `foreach` thường dễ đọc hơn. Không có lựa chọn nào "chuẩn" hơn; chọn cái người đọc sau hiểu
nhanh nhất.

### 7.4 Tìm theo điều kiện: array_find, array_find_key, array_any, array_all (PHP 8.4)

Trước PHP 8.4, "tìm phần tử đầu tiên thoả điều kiện" phải viết `foreach` có `break`, hoặc lạm dụng
`array_filter` (duyệt hết array dù đã tìm thấy từ đầu). PHP 8.4 thêm bốn hàm, cùng chữ ký
`(array $array, callable $callback)`, callback nhận `($value, $key)`, và đều *dừng ngay* khi đã có
câu trả lời:

| Hàm | Trả về | Không tìm thấy / array rỗng |
|---|---|---|
| `array_find` | value của phần tử đầu tiên thoả | `null` |
| `array_find_key` | key của phần tử đó | `null` |
| `array_any` | `true` nếu có ít nhất một phần tử thoả | `false` |
| `array_all` | `true` nếu mọi phần tử đều thoả | `true` (array rỗng: "mọi" phần tử đều thoả) |

```php
<?php
declare(strict_types=1);

$users = [
    'u1' => ['name' => 'An',    'age' => 17],
    'u2' => ['name' => 'Binh',  'age' => 25],
    'u3' => ['name' => 'Cuong', 'age' => 30],
];

$isAdult = fn(array $u): bool => $u['age'] >= 18;

echo array_find($users, $isAdult)['name'], PHP_EOL;     // in ra: Binh (value đầu tiên thoả)
echo array_find_key($users, $isAdult), PHP_EOL;         // in ra: u2 (key của nó)
var_dump(array_any($users, $isAdult));                  // in ra: bool(true): có ít nhất một
var_dump(array_all($users, $isAdult));                  // in ra: bool(false): không phải tất cả

// Callback nhận cả key ở tham số thứ hai
var_dump(array_find($users, fn(array $u, string $id): bool => $id === 'u9'));  // in ra: NULL

// Mảng rỗng
var_dump(array_any([], $isAdult), array_all([], $isAdult)); // in ra: bool(false) bool(true)

// Dừng ngay khi có kết quả
$calls = 0;
array_any([1, 2, 3, 4], function (int $n) use (&$calls): bool {
    $calls++;
    return $n === 2;
});
echo $calls, PHP_EOL;                                   // in ra: 2
```

⚠️ `array_find` trả `null` cả khi không tìm thấy lẫn khi tìm thấy một phần tử có value là `null`.
Nếu array có thể chứa `null`, dùng `array_find_key` rồi so với `null`.

### 7.5 Gộp array: array_merge, toán tử +, array_replace, spread

Bốn cách gộp, khác nhau ở cách xử lý key trùng và key số. Đây cũng là một câu hỏi phỏng vấn PHP rất
phổ biến.

| Cách gộp | Key int | Key chuỗi trùng |
|---|---|---|
| `array_merge($a, $b)` | Nối đuôi, đánh số lại từ 0 | Bên phải (`$b`) thắng |
| `[...$a, ...$b]` | Nối đuôi, đánh số lại từ 0 | Bên phải thắng (giống `array_merge`) |
| `$a + $b` (*union*) | Giữ nguyên; key đã có ở `$a` thì bỏ phần tử của `$b` | Bên **trái** thắng |
| `array_replace($a, $b)` | Giữ nguyên; key trùng thì `$b` ghi đè | Bên phải thắng |

```php
<?php
declare(strict_types=1);

// Key chuỗi: array_merge và spread cho bên phải thắng, + cho bên trái thắng
$defaults = ['timeout' => 30, 'retry' => 3];
$custom   = ['timeout' => 5];
echo json_encode(array_merge($defaults, $custom)), PHP_EOL;   // in ra: {"timeout":5,"retry":3}
echo json_encode($custom + $defaults), PHP_EOL;               // in ra: {"timeout":5,"retry":3}
echo json_encode($defaults + $custom), PHP_EOL;               // in ra: {"timeout":30,"retry":3}

// Key int: array_merge nối đuôi và đánh số lại; + bỏ qua key đã có ở bên trái
echo json_encode(array_merge([1, 2], [3, 4, 5])), PHP_EOL;    // in ra: [1,2,3,4,5]
echo json_encode([1, 2] + [3, 4, 5]), PHP_EOL;                // in ra: [1,2,5]  (!)

// Key là ID: array_merge làm mất ID; + và array_replace giữ ID
$a = [101 => 'An', 205 => 'Binh'];
$b = [205 => 'Binh moi', 307 => 'Cuong'];
echo json_encode(array_merge($a, $b)), PHP_EOL;     // in ra: ["An","Binh","Binh moi","Cuong"]
echo json_encode($a + $b), PHP_EOL;                 // in ra: {"101":"An","205":"Binh","307":"Cuong"}
echo json_encode(array_replace($a, $b)), PHP_EOL;   // in ra: {"101":"An","205":"Binh moi","307":"Cuong"}
```

Cách chọn:

- Nối hai list: `array_merge($a, $b)` hoặc `[...$a, ...$b]`. Đừng dùng `+`: `[1, 2] + [3, 4, 5]` cho
  `[1, 2, 5]` vì key 0 và 1 đã có ở bên trái.
- Điền giá trị mặc định cho options: `$options + $defaults` (giữ thứ người dùng truyền, thêm thứ còn
  thiếu), hoặc `array_merge($defaults, $options)` (cùng các cặp key/value khi key là chuỗi, chỉ có
  thể khác thứ tự key).
- Array có key int mang nghĩa (ID): `+` hoặc `array_replace`, tuỳ bên nào cần thắng. Không bao giờ
  dùng `array_merge`.

So sánh hai array (chi tiết toán tử ở [Chương 07](07-toan-tu-dieu-khien.md)): `$a == $b` khi hai array
có cùng các cặp key/value (so value bằng `==`, không quan tâm thứ tự); `$a === $b` khi cùng các cặp
key/value, cùng thứ tự, cùng kiểu. Ví dụ `[1, 2] == [1 => 2, 0 => 1]` là `true` nhưng `===` là `false`.

**`array_combine(array $keys, array $values): array`** ghép hai list thành một bảng tra: phần tử thứ i của `$keys` làm key
cho phần tử thứ i của `$values`. Từ PHP 8.0, hai array khác số phần tử thì ném `ValueError` (trước đó
trả `false` kèm Warning).

```php
echo json_encode(array_combine(['id', 'name'], [7, 'An'])), PHP_EOL;   // in ra: {"id":7,"name":"An"}
array_combine(['id', 'name'], [7]);
// ném ValueError: array_combine(): Argument #1 ($keys) and argument #2 ($values) must have the same number of elements
```

Ứng dụng hay gặp: đọc file CSV, dòng đầu là tên cột: `array_combine($header, $row)` biến mỗi dòng
thành array kết hợp.

### 7.6 Cắt và nối: array_slice, array_splice

Hai hàm tên gần giống nhau nhưng khác hẳn về bản chất:

- `array_slice($array, $offset, $length = null, $preserve_keys = false)`: *đọc* một đoạn, trả array
  mới, array gốc không đổi.
- `array_splice(&$array, $offset, $length = null, $replacement = [])`: *sửa* array gốc (nhận by
  reference): cắt bỏ một đoạn, tuỳ chọn chèn thứ khác vào chỗ đó; trả về phần bị cắt ra.

Với cả hai, `$offset` là *vị trí* (thứ tự 0, 1, 2... trong array), không phải key; số âm tính từ cuối.

```php
<?php
declare(strict_types=1);

$letters = ['a', 'b', 'c', 'd', 'e'];

// array_slice: trả về một đoạn, KHÔNG sửa array gốc
echo json_encode(array_slice($letters, 1, 2)), PHP_EOL;        // in ra: ["b","c"]
echo json_encode(array_slice($letters, -2)), PHP_EOL;          // in ra: ["d","e"]  (2 phần tử cuối)
echo json_encode(array_slice($letters, 1, 2, true)), PHP_EOL;  // in ra: {"1":"b","2":"c"}  (giữ key)

// offset là VỊ TRÍ, không phải key
$scores = [10 => 'x', 20 => 'y', 30 => 'z'];
echo json_encode(array_slice($scores, 1, 1)), PHP_EOL;         // in ra: ["y"]

// Phân trang trong bộ nhớ: trang 2, mỗi trang 2 phần tử
$page = 2;
$perPage = 2;
echo json_encode(array_slice($letters, ($page - 1) * $perPage, $perPage)), PHP_EOL;  // in ra: ["c","d"]

// array_splice: SỬA array gốc, trả về phần bị cắt ra
$removed = array_splice($letters, 1, 2);
echo json_encode($removed), ' ', json_encode($letters), PHP_EOL;   // in ra: ["b","c"] ["a","d","e"]

array_splice($letters, 1, 0, ['X', 'Y']);       // length 0: chỉ chèn, không xoá
echo json_encode($letters), PHP_EOL;            // in ra: ["a","X","Y","d","e"]

array_splice($letters, -1, 1, 'Z');             // thay phần tử cuối
echo json_encode($letters), PHP_EOL;            // in ra: ["a","X","Y","d","Z"]

// Xoá phần tử ở vị trí 1 mà list vẫn liền mạch (khác unset)
$ids = [10, 20, 30];
array_splice($ids, 1, 1);
echo json_encode($ids), PHP_EOL;                // in ra: [10,30]
```

Về key: `array_slice` mặc định đánh số lại key int (truyền `$preserve_keys = true` để giữ), key chuỗi
luôn được giữ. `array_splice` không giữ key int của array gốc, và key của `$replacement` cũng không
được giữ.

Phân trang bằng `array_slice` chỉ hợp lý khi dữ liệu đã nằm sẵn trong bộ nhớ. Với dữ liệu trong
database, phân trang bằng SQL (`LIMIT`/`OFFSET` hoặc keyset) để không phải tải hết về PHP.

### 7.7 Dữ liệu dạng bảng: array_column, array_unique, array_count_values, array_chunk

Kết quả query thường là một list các dòng, mỗi dòng là array kết hợp. Mấy hàm sau xử lý dạng dữ liệu
này rất gọn.

```php
<?php
declare(strict_types=1);

$rows = [
    ['id' => 3, 'email' => 'an@x.vn',    'team' => 'be'],
    ['id' => 5, 'email' => 'binh@x.vn',  'team' => 'fe'],
    ['id' => 9, 'email' => 'cuong@x.vn', 'team' => 'be'],
];

// array_column(rows, column_key, index_key): rút một cột
echo json_encode(array_column($rows, 'email')), PHP_EOL;
// in ra: ["an@x.vn","binh@x.vn","cuong@x.vn"]

echo json_encode(array_column($rows, 'email', 'id')), PHP_EOL;
// in ra: {"3":"an@x.vn","5":"binh@x.vn","9":"cuong@x.vn"}  bảng tra id => email

$byId = array_column($rows, null, 'id');          // column_key null: lấy cả dòng, đánh key theo id
echo $byId[9]['email'], PHP_EOL;                  // in ra: cuong@x.vn

echo json_encode(array_column($rows, 'id', 'team')), PHP_EOL;
// in ra: {"be":9,"fe":5}  index_key trùng: dòng sau ghi đè dòng trước

// array_unique: bỏ value trùng, GIỮ KEY của lần xuất hiện đầu tiên
$tags = ['php', 'sql', 'php', 'go', 'sql'];
echo json_encode(array_unique($tags)), PHP_EOL;                 // in ra: {"0":"php","1":"sql","3":"go"}
echo json_encode(array_values(array_unique($tags))), PHP_EOL;   // in ra: ["php","sql","go"]

// Mặc định so sánh dạng chuỗi: 1, '1', 1.0, true đều thành '1'
var_dump(array_unique([1, '1', 1.0, true]));       // in ra: array(1) { [0]=> int(1) }

// array_count_values: đếm số lần xuất hiện của từng value (value phải là int hoặc string)
echo json_encode(array_count_values($tags)), PHP_EOL;          // in ra: {"php":2,"sql":2,"go":1}

// array_chunk: chia thành các nhóm nhỏ, ví dụ insert vào database theo lô
echo json_encode(array_chunk([1, 2, 3, 4, 5], 2)), PHP_EOL;     // in ra: [[1,2],[3,4],[5]]
```

- `array_column` đọc được cả list các object (lấy property public). Kết quả không giữ key của array
  gốc; muốn key có nghĩa thì truyền `index_key`. Dòng nào thiếu cột cần lấy thì bị bỏ qua, không báo gì.
- `array_column($rows, null, 'id')` là cách nhanh nhất để biến list dòng thành bảng tra theo ID, rồi
  tra `$byId[$id]` trong O(1) thay vì dò cả list.
- `array_unique` mặc định coi hai phần tử bằng nhau khi `(string) $a === (string) $b` (cờ
  `SORT_STRING`). Với array chứa array con, dùng `array_unique($a, SORT_REGULAR)`, vì đổi array sang
  chuỗi chỉ ra chữ `"Array"` kèm Warning.

Họ hàm tập hợp `array_diff` (phần tử có trong array đầu mà không có trong các array sau),
`array_intersect` (phần tử có trong tất cả) cũng so sánh dạng chuỗi và giữ key của array đầu. Bản
`_key` của chúng so theo key, rất tiện để lọc field theo whitelist:

```php
<?php
declare(strict_types=1);

$before = ['php', 'sql', 'go'];
$after  = ['php', 'go', 'rust'];
echo json_encode(array_values(array_diff($after, $before))), PHP_EOL;      // in ra: ["rust"]  (mới thêm)
echo json_encode(array_values(array_diff($before, $after))), PHP_EOL;      // in ra: ["sql"]   (bị bỏ)
echo json_encode(array_values(array_intersect($before, $after))), PHP_EOL; // in ra: ["php","go"] (chung)

// Chỉ giữ những field được phép, bỏ field lạ như is_admin
$input   = ['name' => 'An', 'email' => 'an@x.vn', 'is_admin' => true];
$allowed = ['name' => true, 'email' => true];
echo json_encode(array_intersect_key($input, $allowed)), PHP_EOL;   // in ra: {"name":"An","email":"an@x.vn"}

echo array_sum([1, 2, 3.5]), ' ', max([3, 9, 2]), ' ', min([3, 9, 2]), PHP_EOL;  // in ra: 6.5 9 2
```

### 7.8 Bảng tổng hợp: giữ key, so sánh, sửa tại chỗ

| Hàm | Key của kết quả | Cách so sánh | Sửa array gốc? |
|---|---|---|---|
| `array_values`, `array_keys` | List mới 0..n-1 | `array_keys($a, $v)`: `==`, hoặc `===` nếu tham số 3 là `true` | Không |
| `array_map` (1 array) | Giữ key | | Không |
| `array_map` (từ 2 array) | Đánh số lại | | Không |
| `array_filter` | Giữ key (có lỗ) | Callback quyết định | Không |
| `array_merge`, spread `...` | Key int đánh số lại, key chuỗi giữ | | Không |
| `+`, `array_replace` | Giữ key | | Không |
| `array_slice` | Key int đánh số lại (trừ khi `preserve_keys`), key chuỗi giữ | | Không |
| `array_splice` | Key int đánh số lại | | Có (by reference) |
| `array_unique`, `array_diff`, `array_intersect` | Giữ key | Dạng chuỗi `(string) $a === (string) $b` | Không |
| `array_column` | Key mới (hoặc theo `index_key`) | | Không |
| `in_array`, `array_search` | | `==`, trừ khi tham số 3 là `true` | Không |
| `array_push` | Key mới tính như `$a[] = ...` | | Có |
| `array_pop` | Các key còn lại giữ nguyên | | Có |
| `array_shift`, `array_unshift` | Key int đánh số lại, key chuỗi giữ | | Có |
| Họ `sort` (mục 8) | Tuỳ hàm | Tuỳ cờ | Có |

Laravel bọc hầu hết các hàm này trong class `Illuminate\Support\Collection` với tên và thứ tự tham số
nhất quán (`collect($rows)->filter(...)->map(...)->values()`), nhưng các luật về key vẫn y hệt: ví dụ
`->filter()` cũng giữ key, nên cũng cần `->values()` trước khi trả JSON.

---

## 8. Sắp xếp

### 8.1 Chọn đúng hàm trong họ sort

PHP có cả chục hàm sắp xếp, nhưng chúng chỉ khác nhau ở ba câu hỏi:

1. Sắp theo *value* hay theo *key*?
2. Sau khi sắp, có giữ liên kết `key => value` không, hay bỏ key cũ và đánh số lại 0, 1, 2...?
3. Thứ tự tăng, giảm, hay do bạn tự định nghĩa bằng một hàm so sánh?

| Hàm | Sắp theo | Giữ liên kết key => value | Thứ tự |
|---|---|---|---|
| `sort` | value | Không, đánh số lại | Tăng dần |
| `rsort` | value | Không | Giảm dần |
| `usort` | value | Không | Hàm so sánh của bạn |
| `asort` | value | Có | Tăng dần |
| `arsort` | value | Có | Giảm dần |
| `uasort` | value | Có | Hàm so sánh của bạn |
| `ksort` | key | Có | Tăng dần |
| `krsort` | key | Có | Giảm dần |
| `uksort` | key | Có | Hàm so sánh của bạn |

Mẹo nhớ tên: chữ `a` là *associative* (giữ key), chữ `k` là *key* (sắp theo key), chữ `r` là
*reverse* (giảm dần), chữ `u` là *user-defined* (bạn đưa hàm so sánh).

Mọi hàm trong bảng đều:

- Sửa trực tiếp array bạn truyền vào (tham số by reference), không trả về array mới.
- Trả về `true` (từ PHP 8.2 kiểu trả về được khai báo hẳn là `true`). Vì vậy `$sorted = sort($a);`
  là bug: `$sorted` nhận `true`.
- Ổn định (*stable*) từ PHP 8.0 (mục 8.4).

```php
<?php
declare(strict_types=1);

$scores = ['an' => 7, 'binh' => 9, 'cuong' => 5];

$a = $scores;
sort($a);                                  // sắp theo value, BỎ key cũ
echo json_encode($a), PHP_EOL;             // in ra: [5,7,9]

$b = $scores;
asort($b);                                 // sắp theo value, GIỮ liên kết key => value
echo json_encode($b), PHP_EOL;             // in ra: {"cuong":5,"an":7,"binh":9}

$c = $scores;
arsort($c);                                // như asort nhưng giảm dần
echo json_encode($c), PHP_EOL;             // in ra: {"binh":9,"an":7,"cuong":5}

$d = $scores;
ksort($d);                                 // sắp theo key
echo json_encode($d), PHP_EOL;             // in ra: {"an":7,"binh":9,"cuong":5}

$e = $scores;
krsort($e);                                // theo key, giảm dần
echo json_encode($e), PHP_EOL;             // in ra: {"cuong":5,"binh":9,"an":7}

$f = $scores;
rsort($f);
echo json_encode($f), PHP_EOL;             // in ra: [9,7,5]

// Bẫy: hàm sort sửa tại chỗ và trả về true, không trả array đã sắp
$sorted = sort($a);
var_dump($sorted);                         // in ra: bool(true)
```

Để có bản đã sắp mà vẫn giữ bản gốc, copy trước rồi sắp bản copy (`$b = $scores; asort($b);` như
trên). Nhờ copy-on-write (mục 9), dòng `$b = $scores` chưa copy gì; dữ liệu chỉ thật sự được copy khi
`$b` bị sửa, tức là lúc nó được đưa vào hàm sort.

⚠️ Chọn nhầm `sort` cho array kết hợp là bug hay gặp: key (tên, ID) mất hết, chỉ còn list value.
Cần giữ key thì dùng họ `a` hoặc `k`.

### 8.2 Cờ so sánh: SORT_REGULAR, SORT_STRING, SORT_NATURAL...

Các hàm không có chữ `u` nhận tham số thứ hai `$flags` để chọn cách so sánh:

| Cờ | So sánh thế nào |
|---|---|
| `SORT_REGULAR` (mặc định) | Như toán tử so sánh thông thường (`<`, `>`); numeric string được so như số |
| `SORT_NUMERIC` | Đổi sang số rồi so |
| `SORT_STRING` | So như chuỗi, theo từng byte |
| `SORT_NATURAL` | "Thứ tự tự nhiên": cụm chữ số được so như số (`img2` trước `img10`) |
| `SORT_FLAG_CASE` | Kết hợp với `SORT_STRING` hoặc `SORT_NATURAL` bằng `\|` để không phân biệt hoa thường |
| `SORT_LOCALE_STRING` | So như chuỗi theo locale hiện tại (`setlocale()`) |

```php
<?php
declare(strict_types=1);

$files = ['img12.png', 'img10.png', 'IMG2.png', 'img1.png'];

$x = $files;
sort($x);                                  // so sánh chuỗi theo từng byte
echo implode(' ', $x), PHP_EOL;            // in ra: IMG2.png img1.png img10.png img12.png

$y = $files;
sort($y, SORT_NATURAL | SORT_FLAG_CASE);   // thứ tự tự nhiên, không phân biệt hoa thường
echo implode(' ', $y), PHP_EOL;            // in ra: img1.png IMG2.png img10.png img12.png

$nums = ['10', '9', '2', '1'];
$n1 = $nums;
sort($n1);                                 // SORT_REGULAR: numeric string được so như số
echo implode(' ', $n1), PHP_EOL;           // in ra: 1 2 9 10
$n2 = $nums;
sort($n2, SORT_STRING);                    // ép so như chuỗi
echo implode(' ', $n2), PHP_EOL;           // in ra: 1 10 2 9

$names = ['Bình', 'An', 'Ánh', 'Zung'];
sort($names);
echo implode(' ', $names), PHP_EOL;        // in ra: An Bình Zung Ánh
```

Dòng cuối cho thấy sắp chuỗi mặc định là so *byte*: chữ `Á` trong UTF-8 bắt đầu bằng byte `0xC3`, lớn
hơn mọi chữ cái ASCII, nên "Ánh" đứng sau "Zung". Muốn sắp đúng theo bảng chữ cái tiếng Việt, dùng
class `Collator` của extension `intl`: `(new Collator('vi_VN'))->sort($names);`.

⚠️ Manual của `sort` cảnh báo: sắp array chứa nhiều kiểu lẫn lộn (số, chuỗi số, chuỗi chữ) với
`SORT_REGULAR` có thể cho kết quả không đoán trước được, vì phép so sánh lỏng giữa các kiểu khác nhau
không nhất quán. Chuẩn hoá kiểu trước khi sắp, hoặc chọn cờ rõ ràng.

### 8.3 Tự định nghĩa thứ tự: usort, uasort, uksort

Khi cần sắp theo một field, theo nhiều tiêu chí, hay theo thứ tự nghiệp vụ, bạn đưa vào một *hàm so
sánh* (*comparator*). Hàm nhận hai phần tử `$a`, `$b` và phải trả về một số nguyên:

- âm nếu `$a` phải đứng trước `$b`;
- `0` nếu hai phần tử ngang nhau;
- dương nếu `$a` phải đứng sau `$b`.

Toán tử `<=>` (*spaceship*, Chương 07) trả đúng `-1`, `0`, `1` theo quy ước này, nên comparator gần
như luôn được viết bằng nó.

```php
<?php
declare(strict_types=1);

$products = [
    ['name' => 'pen',   'price' => 5000,  'stock' => 10],
    ['name' => 'book',  'price' => 12000, 'stock' => 0],
    ['name' => 'bag',   'price' => 5000,  'stock' => 3],
    ['name' => 'ruler', 'price' => 3000,  'stock' => 7],
];

// Giá tăng dần
usort($products, fn(array $a, array $b): int => $a['price'] <=> $b['price']);
echo implode(' ', array_column($products, 'name')), PHP_EOL;   // in ra: ruler pen bag book

// Giảm dần: đảo vị trí $a và $b
usort($products, fn(array $a, array $b): int => $b['price'] <=> $a['price']);
echo implode(' ', array_column($products, 'name')), PHP_EOL;   // in ra: book pen bag ruler

// Nhiều tiêu chí: giá tăng dần, cùng giá thì tồn kho giảm dần.
// ?: lấy vế phải khi vế trái là 0 (tức là tiêu chí trước bằng nhau)
usort($products, fn(array $a, array $b): int =>
    $a['price'] <=> $b['price']
    ?: $b['stock'] <=> $a['stock']);
echo implode(' ', array_column($products, 'name')), PHP_EOL;   // in ra: ruler pen bag book

// Cách viết khác: so sánh hai array từng phần tử một, theo thứ tự
usort($products, fn(array $a, array $b): int =>
    [$a['price'], $b['stock']] <=> [$b['price'], $a['stock']]);
echo implode(' ', array_column($products, 'name')), PHP_EOL;   // in ra: ruler pen bag book

// uasort: như usort nhưng giữ key
$byName = array_column($products, null, 'name');
uasort($byName, fn(array $a, array $b): int => $a['stock'] <=> $b['stock']);
echo implode(' ', array_keys($byName)), PHP_EOL;               // in ra: book bag ruler pen

// uksort: sắp theo key, với thứ tự nghiệp vụ không phải bảng chữ cái
$sizes = ['XL' => 4, 'S' => 1, 'M' => 2, 'L' => 3];
$order = ['S' => 0, 'M' => 1, 'L' => 2, 'XL' => 3];
uksort($sizes, fn(string $a, string $b): int => $order[$a] <=> $order[$b]);
echo implode(' ', array_keys($sizes)), PHP_EOL;                // in ra: S M L XL
```

Hai bẫy khi viết comparator:

```php
<?php
declare(strict_types=1);

// Bẫy 1: trả bool (thói quen "a > b" từ ngôn ngữ khác)
$a = [3, 1, 2];
usort($a, fn(int $x, int $y): bool => $x > $y);
// in ra: Deprecated: usort(): Returning bool from comparison function is deprecated,
//        return an integer less than, equal to, or greater than zero in ...
echo json_encode($a), PHP_EOL;        // in ra: [1,2,3]  (vẫn đúng, nhưng chỉ nhờ một cơ chế tạm)

// Bẫy 2: trả hiệu số thực, bị ép về int
$prices = [1.5, 1.2, 1.9];
usort($prices, fn(float $x, float $y): float => $x - $y);
echo json_encode($prices), PHP_EOL;   // in ra: [1.5,1.2,1.9]  không sắp gì cả!

usort($prices, fn(float $x, float $y): int => $x <=> $y);
echo json_encode($prices), PHP_EOL;   // in ra: [1.2,1.5,1.9]
```

- Trả `bool` bị deprecated từ PHP 8.0. RFC về sort ổn định giải thích: sort ổn định cần phân biệt
  "bằng nhau" với "nhỏ hơn", điều một giá trị `bool` không nói được; PHP tạm xoay xở bằng cách gọi lại
  comparator với hai tham số đổi chỗ khi nhận `false`, và cơ chế này được ghi là sẽ bỏ trong tương lai.
- Giá trị trả về không phải int bị ép về int (manual của `usort`: `0.99` và `0.1` đều thành `0`). Hiệu
  `1.5 - 1.2 = 0.3` thành `0`, nghĩa là "bằng nhau", nên array giữ nguyên thứ tự. Luôn dùng `<=>`.

Comparator được gọi rất nhiều lần (cỡ n log n lần với n phần tử). Đừng đặt việc nặng (query database,
gọi API, xử lý chuỗi phức tạp) bên trong nó; tính trước khoá sắp xếp cho từng phần tử rồi mới sắp.

### 8.4 Sắp xếp ổn định (stable) từ PHP 8.0

Một thuật toán sắp xếp là *ổn định* (*stable*) nếu các phần tử được coi là bằng nhau giữ nguyên thứ
tự tương đối như trước khi sắp. Trước PHP 8.0, thứ tự giữa các phần tử bằng nhau là không xác định.
Từ PHP 8.0 (RFC "Make sorting stable"), mọi hàm sort đều ổn định: `sort`, `rsort`, `usort`, `asort`,
`arsort`, `uasort`, `ksort`, `krsort`, `uksort`, `array_multisort`.

Ổn định có ích khi bạn sắp dữ liệu phức tạp chỉ theo một phần của nó:

```php
<?php
declare(strict_types=1);

// Danh sách đã được sắp theo tên từ trước (ví dụ ORDER BY name trong SQL)
$users = [
    ['name' => 'An',    'age' => 30],
    ['name' => 'Binh',  'age' => 25],
    ['name' => 'Cuong', 'age' => 30],
    ['name' => 'Dung',  'age' => 25],
];

// Sắp lại theo tuổi. Sort ổn định: người cùng tuổi giữ nguyên thứ tự cũ (theo tên)
usort($users, fn(array $a, array $b): int => $a['age'] <=> $b['age']);
foreach ($users as $u) {
    echo $u['age'], ' ', $u['name'], PHP_EOL;
}
// in ra:
// 25 Binh
// 25 Dung
// 30 An
// 30 Cuong

$scores = ['c' => 1, 'd' => 1, 'a' => 0, 'b' => 0];
asort($scores);
echo json_encode($scores), PHP_EOL;   // in ra: {"a":0,"b":0,"c":1,"d":1}
```

Ví dụ `asort` cuối lấy từ RFC: với sort ổn định, kết quả *luôn* là `a, b, c, d`; với sort không ổn
định, các kết quả như `b, a, d, c` cũng hợp lệ. Theo RFC, thuật toán nền của PHP vẫn là một biến thể
quicksort lai (vốn không ổn định); tính ổn định đạt được bằng cách nhớ vị trí ban đầu của từng phần tử
và dùng nó làm tiêu chí phụ khi hai phần tử bằng nhau.

Hệ quả thực tế: code chạy trên PHP 7 mà vô tình phụ thuộc vào thứ tự của các phần tử bằng nhau (ví dụ
test so sánh output) có thể cho kết quả khác sau khi nâng lên PHP 8. Ngược lại, từ PHP 8 bạn có thể
yên tâm sắp nhiều lượt: sắp theo tiêu chí phụ trước, rồi sắp theo tiêu chí chính sau.

---

## 9. Array được copy thế nào: copy-on-write

### 9.1 Array là kiểu giá trị

Gán một array cho biến khác, hay truyền nó vào hàm, thì về mặt *ý nghĩa* bên nhận có một bản riêng:
sửa bản này không ảnh hưởng bản kia. Manual: "Array assignment always involves value copying".

```php
<?php
declare(strict_types=1);

$a = [1, 2, 3];
$b = $a;          // $b là bản riêng
$b[] = 4;
echo count($a), ' ', count($b), PHP_EOL;   // in ra: 3 4

function addItem(array $items): array
{
    $items[] = 'new';   // sửa bản của hàm
    return $items;      // muốn caller thấy thay đổi thì trả về
}
$list = ['old'];
$newList = addItem($list);
echo json_encode($list), ' ', json_encode($newList), PHP_EOL;   // in ra: ["old"] ["old","new"]
```

Đây là điểm khác lớn giữa array và object. Biến object chỉ giữ một *handle* trỏ tới object, nên gán
hay truyền object thì hai bên cùng thấy một object ([Chương 09](09-oop-co-ban.md)). Muốn hàm sửa thẳng
array của caller thì phải khai báo tham số by reference (`array &$items`, [Chương 08](08-ham.md)),
nhưng cách được khuyên là trả về array mới như `addItem` ở trên.

Đối chiếu:

| Ngôn ngữ | Gán `b = a` rồi sửa `b` | Ghi chú |
|---|---|---|
| PHP `array` | `a` không đổi | Kiểu giá trị, copy lười (mục 9.2) |
| Java `int[]`, `ArrayList` | `a` đổi theo | Array và collection là object; biến chỉ giữ reference. Muốn bản riêng phải copy tường minh (`clone()`, `new ArrayList<>(a)`) |
| Go array `[3]int` | `a` không đổi | Array của Go là giá trị, gán là copy ngay toàn bộ |
| Go slice `[]int` | `a` thấy thay đổi phần tử | Hai slice dùng chung *backing array* |

### 9.2 Copy-on-write: copy lười

Nếu mỗi lần gán hay truyền tham số PHP đều copy cả array thì truyền một array một triệu phần tử vào
hàm sẽ rất đắt. PHP tránh điều đó bằng *copy-on-write* (COW, "copy khi ghi"):

- Gán `$b = $a` không copy dữ liệu. Hai biến cùng trỏ tới một array, và array đó có một bộ đếm
  *refcount* (số nơi đang dùng chung nó) tăng lên 2.
- Khi có bên *ghi* vào array mà refcount lớn hơn 1, PHP mới tạo bản copy thật cho bên ghi (gọi là
  *tách*, *separation*). Bên còn lại giữ bản cũ.
- Nếu không bên nào ghi, không bao giờ có copy.

```
$a = range(1, 3);
$b = $a;                         $b[] = 0;   (ghi vào $b)

$a ─┐                            $a ───► [1, 2, 3]      refcount = 1
    ├──► [1, 2, 3] refcount = 2
$b ─┘                            $b ───► [1, 2, 3, 0]   refcount = 1 (bản copy mới)
```

Đo bằng `memory_get_usage()` sẽ thấy rõ:

```php
<?php
declare(strict_types=1);

function mib(int $bytes): string
{
    return number_format($bytes / 1024 / 1024, 1) . ' MiB';
}

$a = range(1, 1_000_000);        // một list một triệu số nguyên

$m0 = memory_get_usage();
$b = $a;                         // gán: CHƯA copy, hai biến dùng chung một array
echo 'Sau khi gán:         +', mib(memory_get_usage() - $m0), PHP_EOL;

$m1 = memory_get_usage();
$b[] = 0;                        // ghi lần đầu vào $b: lúc này mới copy
echo 'Sau khi ghi vào $b:  +', mib(memory_get_usage() - $m1), PHP_EOL;

// Truyền vào hàm cũng vậy: chỉ đọc thì không copy, ghi vào tham số thì copy
function readOnly(array $items, int $before): int
{
    array_sum($items);
    return memory_get_usage() - $before;
}
function writeParam(array $items, int $before): int
{
    $items[0] = -1;
    return memory_get_usage() - $before;
}
echo 'Hàm chỉ đọc:         +', mib(readOnly($a, memory_get_usage())), PHP_EOL;
echo 'Hàm ghi vào tham số: +', mib(writeParam($a, memory_get_usage())), PHP_EOL;
echo $a[0], PHP_EOL;             // in ra: 1 (bản của caller không đổi)

// Output minh hoạ (PHP 8.5, 64-bit; chữ số thập phân cuối có thể lệch tuỳ nền tảng):
// Sau khi gán:         +0.0 MiB
// Sau khi ghi vào $b:  +16.1 MiB
// Hàm chỉ đọc:         +0.0 MiB
// Hàm ghi vào tham số: +16.1 MiB
// (PHP 8.1: khoảng 32 MiB thay vì 16 MiB, xem mục 10.3)
```

Hệ quả thực tế:

- Truyền array lớn vào hàm, trả array lớn từ hàm, gán array cho biến khác: rẻ, miễn là không ghi.
- Ghi vào một array đang được dùng chung thì trả giá một lần copy toàn bộ. Trong vòng lặp `foreach`
  by value trên `$a`, ghi vào chính `$a` gây đúng một lần copy như vậy (mục 5.1).
- ⚠️ Dùng `&` để "tránh copy" là hiểu sai. Nhờ COW, truyền by value vốn đã không copy nếu hàm chỉ
  đọc. Còn nếu array đang được dùng chung với biến khác thì lần ghi đầu tiên qua reference vẫn phải
  copy y như bình thường (đo được khoảng 16 MiB như trên). Reference không làm nhanh hơn mà còn có giá:
  `foreach ($a as &$v)` bọc từng phần tử thành một reference và lớp bọc đó ở lại sau vòng lặp. Đo thử
  trên PHP 8.5 với list một triệu số nguyên (số minh hoạ): sau khi vòng lặp kết thúc, ghi qua key
  (`$a[$k] = ...`) không để lại bộ nhớ thêm, còn `foreach` by reference để lại thêm khoảng 30 MiB.
  Dùng `&` khi thật sự cần sửa biến của caller, không dùng để tối ưu.

Cơ chế bên dưới (zval, refcount nằm ở đâu, chính xác khi nào tách) được trình bày ở
[Chương 19](19-ben-trong-engine.md).

---

## 10. Hiệu năng

### 10.1 Độ phức tạp của các thao tác chính

*Độ phức tạp* (ký hiệu big-O) mô tả thời gian chạy tăng thế nào khi số phần tử n tăng. O(1) là gần
như không đổi; O(n) là tăng tỉ lệ với n; O(n log n) là chi phí của các thuật toán sắp xếp.

| Thao tác | Độ phức tạp | Ghi chú |
|---|---|---|
| Đọc, ghi, xoá theo key: `$a[$k]`, `$a[$k] = $v`, `unset($a[$k])` | O(1) trung bình | Nhờ hash table |
| `isset($a[$k])`, `array_key_exists($k, $a)`, `$a[$k] ?? ...` | O(1) trung bình | |
| `$a[] = $v`, `array_push` một phần tử, `array_pop` | O(1) (khấu hao) | Hết chỗ thì vùng nhớ được cấp lại gấp đôi |
| `count($a)` | O(1) | Số phần tử được lưu sẵn |
| `in_array`, `array_search`, `array_keys($a, $v)` | O(n) | Dò tuần tự từ đầu |
| `array_shift`, `array_unshift` | O(n) | Đánh số lại toàn bộ key (mục 4.3) |
| `array_merge`, `array_slice`, `array_map`, `array_filter`, `array_values`... | O(n) | Tạo array mới |
| Họ `sort` | O(n log n) trung bình | Comparator gọi cỡ n log n lần |

"Khấu hao" (*amortized*) nghĩa là: thỉnh thoảng một lần thêm phần tử tốn O(n) vì phải chuyển cả
array sang vùng nhớ lớn gấp đôi, nhưng chia đều cho mọi lần thêm thì mỗi lần vẫn là O(1).

### 10.2 isset trên bảng tra thay cho in_array

Đây là tối ưu đáng nhớ nhất của chương. Câu hỏi "giá trị X có trong danh sách không" có hai cách
trả lời:

- `in_array($x, $list, true)`: dò từ đầu tới cuối, O(n) mỗi lần.
- Biến danh sách thành bảng tra một lần (`$set = array_flip($list)`, value thành key), rồi
  `isset($set[$x])`: O(1) mỗi lần.

Một lần kiểm tra thì khác biệt không đáng kể. Nhưng kiểm tra *trong vòng lặp* thì `in_array` cho tổng
chi phí O(n × m), còn bảng tra chỉ tốn O(n + m):

```php
<?php
declare(strict_types=1);

$allowedIds = range(1, 20_000, 2);           // 10 000 ID lẻ: 1, 3, 5, ...
$requests   = range(1, 20_000);              // 20 000 lần kiểm tra

// Cách 1: in_array trên list, mỗi lần dò tuần tự O(n)
$t = hrtime(true);
$hits = 0;
foreach ($requests as $id) {
    if (in_array($id, $allowedIds, true)) {
        $hits++;
    }
}
$ms1 = (hrtime(true) - $t) / 1e6;

// Cách 2: lật list thành bảng tra MỘT lần, sau đó mỗi lần kiểm tra là O(1)
$t = hrtime(true);
$allowedSet = array_flip($allowedIds);       // [1 => 0, 3 => 1, 5 => 2, ...]
$hits2 = 0;
foreach ($requests as $id) {
    if (isset($allowedSet[$id])) {
        $hits2++;
    }
}
$ms2 = (hrtime(true) - $t) / 1e6;

echo $hits, ' ', $hits2, PHP_EOL;            // in ra: 10000 10000 (cùng kết quả)
printf("in_array: %.1f ms, isset: %.2f ms\n", $ms1, $ms2);
// Output minh hoạ (một lần chạy, con số tuỳ máy):
// in_array: 141.4 ms, isset: 1.12 ms
```

Trong lần đo trên, với 10 000 phần tử, bảng tra đã nhanh hơn khoảng trăm lần, và khoảng cách còn tăng
theo kích thước dữ liệu.
Lưu ý khi dùng `array_flip`: value của list phải là `int` hoặc `string` (mục 7.2), và chuỗi số sẽ bị
đổi thành key int (mục 2.2), nên `isset` sẽ khớp cả `'15'` lẫn `15`.

Cùng ý tưởng cho dữ liệu dạng bảng: thay vì `array_find` hay `foreach` dò từng dòng để tìm theo ID mỗi
lần, dựng `$byId = array_column($rows, null, 'id')` một lần rồi tra `$byId[$id]`.

### 10.3 Bộ nhớ: array PHP không rẻ

Mỗi phần tử của array PHP mang theo nhiều thông tin hơn một ô của mảng C hay Java (ít nhất là kiểu
của value; ở dạng hash còn thêm key và giá trị băm). Tự đo bằng `memory_get_usage()`:

```php
<?php
declare(strict_types=1);

function mib(int $bytes): string
{
    return number_format($bytes / 1024 / 1024, 1) . ' MiB';
}

$m = memory_get_usage();
$packed = [];
for ($i = 0; $i < 1_000_000; $i++) {
    $packed[] = $i;                 // key 0, 1, 2... tăng dần: PHP dùng dạng packed
}
echo 'packed: ', mib(memory_get_usage() - $m), PHP_EOL;   // output minh hoạ (PHP 8.5): packed: 16.1 MiB

$m = memory_get_usage();
$hash = [];
for ($i = 999_999; $i >= 0; $i--) {
    $hash[$i] = $i;                 // key giảm dần: buộc dùng dạng hash
}
echo 'hash:   ', mib(memory_get_usage() - $m), PHP_EOL;   // output minh hoạ (PHP 8.5): hash:   40.0 MiB
```

Kết quả trên các phiên bản (PHP 64-bit, số làm tròn):

| Dạng array (một triệu số nguyên) | PHP 8.1 | PHP 8.2 trở lên |
|---|---|---|
| *Packed* (key 0, 1, 2... thêm theo thứ tự tăng dần) | khoảng 32 MiB | khoảng 16 MiB |
| *Hash* (ví dụ thêm key theo thứ tự giảm dần) | khoảng 40 MiB | khoảng 40 MiB |

Để so sánh: một triệu `int` 4 byte trong `int[]` của Java chỉ chiếm khoảng 3,8 MiB, một triệu `int64`
trong slice của Go khoảng 7,6 MiB.

*Packed array* là dạng tối ưu PHP tự dùng cho list: bỏ hẳn phần hash và key, tra `$a[$i]` bằng cách
tính thẳng vị trí. Từ PHP 8.2 nó chỉ còn tốn khoảng một nửa bộ nhớ so với trước. Chi tiết hai dạng nằm ở
[Chương 19](19-ben-trong-engine.md); điều cần nhớ ở đây là list thật sự (thêm bằng `$a[] = ...`) rẻ hơn
đáng kể so với array có key lộn xộn.

Hệ quả: đọc một bảng database một triệu dòng vào một array, mỗi dòng lại là một array kết hợp với key
chuỗi, có thể tốn hàng trăm MB và chạm `memory_limit` (đo thử trên PHP 8.5, số minh hoạ: 100 000 dòng,
mỗi dòng 5 cột gồm số và chuỗi ngắn, đã chiếm khoảng 45 MiB). Khi chỉ cần xử lý từng phần tử một, dùng
*generator* (`yield`, [Chương 13](13-generator-iterator-spl.md)) hoặc xử lý theo lô
(`array_chunk`, phân trang ở tầng SQL) thay vì nạp tất cả vào một array.

### 10.4 Vài thói quen nhỏ

- Gộp nhiều array: gom vào một list rồi gọi `array_merge(...$chunks)` một lần. Gọi
  `$all = array_merge($all, $chunk)` trong vòng lặp tạo lại toàn bộ `$all` ở mỗi vòng, tổng chi phí
  O(n²). Đo thử với 2 000 nhóm mỗi nhóm 100 phần tử: cách trong vòng lặp tốn khoảng 250 ms, gộp một lần
  chưa tới 1 ms (output minh hoạ, tuỳ máy).
- Queue lớn: không dùng `array_shift` (mục 4.3).
- Lọc rồi đếm: `count(array_filter(...))` tạo một array trung gian; nếu chỉ cần biết "có hay không"
  thì `array_any` (8.4) dừng sớm và không tạo array.
- Đừng tối ưu sớm: với array vài chục phần tử, chọn cách viết dễ đọc nhất. Các quy tắc trên quan trọng
  khi n lên tới hàng nghìn trở lên, hoặc khi thao tác nằm trong vòng lặp nóng.

---

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| `in_array($x, $list)` cho `true` bất ngờ | Mặc định so lỏng `==`, kể cả trong file `strict_types` | Luôn truyền `true` làm tham số thứ ba (cả `array_search`, `array_keys($a, $v)`) |
| `if (!array_search(...))` bỏ sót phần tử đầu | Tìm thấy ở key `0` cũng là falsy | So với `false` bằng `!==` / `===` |
| API trả `{"0":..,"2":..}` thay vì `[...]` | `unset`, `array_filter`, `array_unique` không đánh số lại key, list bị lủng lỗ | `array_values()` trước khi `json_encode` |
| Phần tử cuối bị ghi đè sau hai vòng `foreach` | Biến của `foreach` by reference vẫn trỏ vào phần tử cuối | `unset($v)` ngay sau vòng lặp, tốt hơn là tránh `&` |
| Sửa bản copy mà bản gốc cũng đổi | Phần tử đang là reference được giữ nguyên khi copy array | Không để lại reference; `unset` tên còn lại của reference |
| ID biến mất sau khi gộp | `array_merge` đánh số lại key int | Dùng `+` hoặc `array_replace` |
| `[1, 2] + [3, 4, 5]` ra `[1, 2, 5]` | `+` giữ key bên trái, bỏ key trùng bên phải | Nối list bằng `array_merge` hoặc `[...$a, ...$b]` |
| `TypeError` khi truyền key vào tham số `string` | Key `'15'` đã bị đổi thành int `15` | Ép kiểu rõ ràng `(string) $key` |
| `isset($a['k'])` là `false` dù key có | Value là `null` | `array_key_exists('k', $a)` khi `null` mang nghĩa |
| `empty($input['qty'])` từ chối `'0'` | `'0'` là falsy | Kiểm tra cụ thể: `!isset(...)`, `=== ''` |
| `array_filter($a)` làm mất số 0 | Không callback thì bỏ mọi giá trị "rỗng" | Luôn viết callback rõ ràng |
| Array kết hợp mất key sau khi sắp | Dùng `sort`/`usort` (đánh số lại) | `asort`, `uasort`, `ksort` |
| `$sorted = sort($a)` nhận `true` | Hàm sort sửa tại chỗ, trả `true` | Gọi `sort($a)` rồi dùng `$a` |
| Comparator trả `bool` hoặc hiệu số thực | Deprecated / bị ép về int nên "bằng nhau" | Luôn dùng `<=>` |
| Destructuring ra `null` | Key 0, 1... không tồn tại, hoặc vế phải không phải array | Kiểm tra `is_array`, `count`; `array_values` trước khi tách |
| Chậm dần với dữ liệu lớn | `in_array` hay `array_shift` trong vòng lặp, `array_merge` dồn trong vòng lặp | Bảng tra + `isset`; `SplQueue`; gộp một lần |

## Tóm tắt chương

- Array của PHP là một *ordered map*: tra theo key nhanh (hash table) và giữ thứ tự chèn. Một kiểu
  đóng vai list, map, set, stack, queue.
- Key chỉ là `int` hoặc `string`. Chuỗi số nguyên dạng chuẩn thành int, float bị cắt phần lẻ
  (Deprecated từ 8.1 nếu mất phần lẻ), bool thành 0/1, `null` thành `''` (Deprecated từ 8.5),
  array/object ném `TypeError`.
- *List* là array có key 0..n-1 liên tục (`array_is_list`, 8.1). `unset`, `array_filter`,
  `array_unique` làm list lủng lỗ; `array_values` vá lại. JSON chỉ ra `[...]` khi là list.
- `foreach` by value duyệt trên bản của array lúc bắt đầu; by reference sửa tại chỗ nhưng phải
  `unset` biến sau vòng lặp, và tốt nhất là tránh.
- Destructuring `[$a, $b] = ...` lấy theo key 0, 1 (hoặc key ghi rõ); spread `[...$a]` theo ngữ nghĩa
  `array_merge`.
- Ba câu hỏi cho mọi hàm mảng: giữ key hay đánh số lại, so lỏng hay chặt, trả array mới hay sửa tại
  chỗ. `in_array`/`array_search` mặc định so lỏng; `array_filter` giữ key; `array_merge` đánh số lại
  key int còn `+` giữ key và cho bên trái thắng.
- PHP 8.4 có `array_find`, `array_find_key`, `array_any`, `array_all`; PHP 8.5 có `array_first`,
  `array_last`.
- Họ sort sửa tại chỗ, trả `true`, và ổn định từ PHP 8.0. Comparator trả số nguyên, viết bằng `<=>`.
- Array là kiểu giá trị nhưng copy lười (copy-on-write): gán và truyền vào hàm rẻ, chỉ copy khi ghi.
  `&` không phải công cụ tối ưu.
- `isset` trên bảng tra là O(1), `in_array` là O(n): trong vòng lặp, khác biệt có thể là hàng trăm
  lần.

## Câu hỏi tự kiểm tra

1. Vì sao nói array của PHP là "ordered map"? Hai tính chất nào giúp một kiểu duy nhất đóng được vai
   list, map và set? (mục 1.2)
2. Không chạy code, hãy cho biết `['1' => 'a', '01' => 'b', 1.9 => 'c', true => 'd', null => 'e']` có
   mấy phần tử, mỗi phần tử có key gì (kiểu gì), và PHP 8.5 phát những cảnh báo nào. (mục 2.2)
3. `$a = [5 => 'x']; unset($a[5]); $a[] = 'y';` thì `'y'` nhận key nào? Nếu thay `unset($a[5])` bằng
   `array_pop($a)` thì sao? (mục 2.4, 4.2)
4. Giải thích từng bước vì sao chạy một vòng `foreach` by reference rồi một vòng `foreach` by value
   cùng tên biến lại làm hỏng phần tử cuối. Nêu hai cách sửa và cách nào tốt hơn. (mục 5.2)
5. `isset`, `array_key_exists` và `empty` cho kết quả gì khi key không có, khi value là `null`, khi
   value là `'0'`? Nêu một tình huống bắt buộc phải dùng `array_key_exists`. (mục 7.1)
6. Khi nào `array_map` giữ key và khi nào không? Còn `array_filter`? Điều đó ảnh hưởng thế nào tới JSON
   trả cho client? (mục 3.1, 7.3)
7. Với hai list, với hai array có key chuỗi trùng nhau, và với hai array có key là ID, thì
   `array_merge`, `+`, `array_replace` và spread lần lượt cho kết quả gì? (mục 7.5)
8. "Sort ổn định" nghĩa là gì? Cho một ví dụ mà kết quả có thể khác nhau giữa sort ổn định và không ổn
   định. (mục 8.4)
9. Vì sao `usort($prices, fn(float $x, float $y): float => $x - $y)` có thể không sắp gì cả? (mục 8.3)
10. Gán một array 100 MB sang biến khác có làm tăng bộ nhớ không? Khi nào thì tăng? Vì sao truyền
    `array &$big` vào hàm không phải là một cách tối ưu? (mục 9.2)

## Bài tập

1. **Dự đoán rồi kiểm chứng.** Tạo file `bai1.php` gồm các đoạn: mảng có key `'1'`, `'01'`, `1.5`,
   `true`, `null`; hai vòng `foreach` (by reference rồi by value) trên `[1, 2, 3]`;
   `array_search('a', ['a', 'b'])` đặt trong `if (!...)`; `[1, 2] + [3, 4, 5]`;
   `array_merge([10 => 'x'], [20 => 'y'])`; `json_encode(array_filter([0, 1, 2, 3]))`. Trước khi chạy,
   ghi dự đoán output vào comment cạnh từng dòng. Chạy bằng `php bai1.php` trên PHP 8.4 và 8.5 (ví dụ
   `docker run --rm -v "$PWD":/app -w /app php:8.4-cli php bai1.php`, chạy trong thư mục chứa file), đánh
   dấu chỗ dự đoán sai và giải thích bằng một câu cho mỗi chỗ.

2. **Báo cáo đơn hàng.** Cho một list khoảng 10 đơn hàng, mỗi đơn là array
   `['id' => int, 'customer' => string, 'status' => 'paid'|'cancelled'|'pending', 'total' => int]`.
   Viết các hàm có khai báo kiểu đầy đủ:
   - `revenueByCustomer(array $orders): array` trả về `['tên khách' => tổng tiền]`, chỉ tính đơn
     `paid`;
   - `topCustomers(array $orders, int $n): array` trả về `$n` khách có doanh thu cao nhất, cùng doanh
     thu thì xếp theo tên tăng dần (dùng `<=>`);
   - `cancelledIds(array $orders): string` trả về JSON là một JSON array (`[...]`), không bao giờ là
     object, kể cả khi đơn bị huỷ nằm rải rác;
   - `hasBigOrder(array $orders, int $threshold): bool` viết hai bản: một bằng `array_any` (PHP 8.4+),
     một bằng `foreach` có dừng sớm.
   Viết mỗi hàm theo hai cách (dùng các hàm `array_*` và dùng `foreach`), rồi ghi lại cách nào dễ đọc
   hơn với bạn và vì sao.

3. **Đo in_array và isset.** Sinh list `n` email ngẫu nhiên và `n` lần kiểm tra (một nửa có trong
   list, một nửa không). Đo bằng `hrtime(true)` thời gian của ba cách: `in_array(..., true)`,
   `isset` trên `array_flip`, `array_key_exists` trên `array_flip`, với `n` = 1 000, 10 000, 50 000.
   Lập bảng kết quả, giải thích vì sao thời gian của `in_array` tăng nhanh hơn hẳn hai cách còn lại.
   Đo thêm bộ nhớ của list và của bảng tra bằng `memory_get_usage()`.

4. **groupBy và indexBy.** Viết `groupBy(array $rows, string $key): array` (gom các dòng có cùng giá
   trị cột thành nhóm) và `indexBy(array $rows, string $key): array` (giống
   `array_column($rows, null, $key)`). Xử lý các trường hợp: dòng thiếu cột `$key`, giá trị cột là
   chuỗi số như `'15'`, hai dòng trùng giá trị cột (với `indexBy`). Kiểm tra bằng vài lệnh `assert()`
   và ghi chú: key của kết quả là `int` hay `string` trong từng trường hợp, và vì sao.

## Đọc thêm

- PHP Manual: [Arrays](https://www.php.net/manual/en/language.types.array.php) (key casting,
  destructuring, unpacking), [Array Functions](https://www.php.net/manual/en/ref.array.php),
  [Sorting Arrays](https://www.php.net/manual/en/array.sorting.php),
  [foreach](https://www.php.net/manual/en/control-structures.foreach.php),
  [list()](https://www.php.net/manual/en/function.list.php),
  [Array Operators](https://www.php.net/manual/en/language.operators.array.php),
  [What References Do](https://www.php.net/manual/en/language.references.whatdo.php)
- PHP 7.0 migration, mục "Changes to foreach":
  [Backward incompatible changes](https://www.php.net/manual/en/migration70.incompatible.php)
- RFC: [Make sorting stable](https://wiki.php.net/rfc/stable_sorting) (8.0),
  [Spread Operator in Array Expression](https://wiki.php.net/rfc/spread_operator_for_array) (7.4),
  [Array unpacking with string keys](https://wiki.php.net/rfc/array_unpacking_string_keys) (8.1),
  [array_is_list](https://wiki.php.net/rfc/is_list) (8.1),
  [array_find](https://wiki.php.net/rfc/array_find) (8.4),
  [array_first() and array_last()](https://wiki.php.net/rfc/array_first_last) (8.5),
  [Deprecations for PHP 8.5](https://wiki.php.net/rfc/deprecations_php_8_5) (null làm array offset)
- php-src: [UPGRADING của PHP 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING),
  [ext/standard/array.c](https://github.com/php/php-src/blob/PHP-8.5/ext/standard/array.c) (mã nguồn
  các hàm mảng, ví dụ `array_shift`)
- Nikita Popov, [PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html)
  (cấu trúc array từ PHP 7, nền cho Chương 19)
