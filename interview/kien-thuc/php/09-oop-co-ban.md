# Chương 09. OOP cơ bản: class và object

> [← Mục lục](README.md) · [← Chương 08: Hàm](08-ham.md) · [Chương 10: OOP nâng cao và các tính năng hiện đại →](10-oop-nang-cao.md)

**Bạn sẽ học được:**

- Class và object là gì, vì sao gom dữ liệu và hành vi vào một chỗ; khai báo class, tạo object bằng
  `new`, dùng property có kiểu và method với `$this`.
- Viết constructor (kể cả *constructor property promotion*) và hiểu destructor chạy lúc nào.
- Kiểm soát truy cập bằng `public`, `protected`, `private`; phân biệt thành viên của object với thành
  viên `static` của class; dùng `self`, `parent`, `static` và hằng class (có kiểu từ PHP 8.3).
- Tổ chức và tái sử dụng code bằng kế thừa, `final`, abstract class, interface và trait; biết khi nào
  chọn cái nào.
- Hiểu object là *handle*: gán không copy, `clone` chỉ copy nông; so sánh object bằng `==`, `===` và
  kiểm tra kiểu bằng `instanceof`.

**Cần biết trước:** [Chương 04](04-kieu-du-lieu.md) (kiểu dữ liệu, khai báo kiểu, `==` và `===`),
[Chương 08](08-ham.md) (khai báo hàm, tham số, kiểu trả về). Vài ví dụ dùng `throw`/`try`/`catch`
để báo lỗi; cơ chế exception được giải thích ở [Chương 12](12-loi-exception.md), ở chương này chỉ
cần hiểu "`throw` dừng hàm và báo lỗi ra ngoài".

## 1. Class và object là gì

### 1.1 Vấn đề: dữ liệu và hành vi nằm rời nhau

Ở các chương trước, khi cần mô tả một "thứ" có nhiều thông tin (một tài khoản ngân hàng, một đơn
hàng), ta dùng array, rồi viết các hàm nhận array đó để xử lý:

```php
<?php
declare(strict_types=1);

// Tài khoản ngân hàng biểu diễn bằng array + hàm rời
$account = ['owner' => 'An', 'balance' => 0];

function deposit(array $account, int $amount): array
{
    $account['balance'] += $amount;
    return $account;
}

$account = deposit($account, 100);
$account['balence'] = 50;      // gõ sai tên key: PHP lặng lẽ tạo key mới
$account['balance'] = -999;    // ai cũng sửa thẳng được, không gì chặn số dư âm

print_r($account);
// in ra:
// Array
// (
//     [owner] => An
//     [balance] => -999
//     [balence] => 50
// )
```

Cách này chạy được, nhưng khi chương trình lớn dần sẽ lộ ra ba vấn đề:

1. Không có gì đảm bảo "hình dạng" của dữ liệu. Gõ sai `balence` thì PHP tạo key mới, không báo gì.
2. Không có gì bảo vệ quy tắc nghiệp vụ. Hàm `deposit()` có kiểm tra kỹ đến đâu thì ai đó vẫn gán
   thẳng `$account['balance'] = -999` được, đi vòng qua mọi kiểm tra.
3. Dữ liệu và các hàm xử lý nó nằm rời nhau. Muốn biết "một tài khoản làm được gì" phải đi tìm mọi
   hàm nhận `array $account` nằm rải rác trong code.

*Lập trình hướng đối tượng* (*object-oriented programming*, OOP) giải quyết bằng cách gom dữ liệu và
các hàm xử lý dữ liệu đó vào cùng một đơn vị gọi là *object*, và để chính đơn vị đó quyết định ai được
chạm vào dữ liệu của nó. Cùng bài toán viết theo kiểu OOP (từng phần cú pháp sẽ được giải thích dần
trong chương):

```php
<?php
declare(strict_types=1);

class BankAccount
{
    private int $balance = 0;          // dữ liệu: chỉ code bên trong class được chạm vào

    public function deposit(int $amount): void   // hành vi: con đường duy nhất để tăng số dư
    {
        if ($amount <= 0) {
            throw new InvalidArgumentException('Số tiền nạp phải dương');
        }
        $this->balance += $amount;
    }

    public function balance(): int
    {
        return $this->balance;
    }
}

$acc = new BankAccount();
$acc->deposit(100);
echo $acc->balance(), "\n";   // in ra: 100

// $acc->balance = -999;      // Error: Cannot access private property BankAccount::$balance
// $acc->deposit(-5);         // InvalidArgumentException: Số tiền nạp phải dương
// $acc->balence = 50;        // PHP 8.2+: Deprecated: Creation of dynamic property BankAccount::$balence is deprecated
```

Cả ba vấn đề đều được xử lý: gán thẳng số dư từ bên ngoài bị chặn bằng `Error`; quy tắc "nạp tiền
phải dương" nằm trong `deposit()` và không có đường nào khác để đổi số dư; gõ sai tên thì từ PHP 8.2
có cảnh báo (mục 2.5). Mọi thứ một tài khoản làm được nằm gọn trong class `BankAccount`.

### 1.2 Class, object, instance

- *Class* (lớp) là một bản mô tả: một kiểu dữ liệu do bạn tự định nghĩa, nói rằng mọi thứ thuộc kiểu
  này có những dữ liệu gì và làm được gì. Hãy hình dung class như bản vẽ thiết kế một ngôi nhà.
- *Object* (đối tượng) là một thứ cụ thể được tạo ra theo bản mô tả đó, có dữ liệu riêng của nó. Từ
  một bản vẽ xây được nhiều ngôi nhà, mỗi nhà có thể sơn một màu.
- *Instance* (thể hiện) là tên gọi khác của object, nhấn mạnh object đó tạo từ class nào: "`$p1` là
  một instance của `Product`". Việc tạo object từ class gọi là *instantiate*.

Bên trong class có ba loại *thành viên* (*member*):

| Thành viên | Là gì | Ví dụ |
|---|---|---|
| *Property* (thuộc tính) | Biến gắn với object (hoặc với class, nếu là `static`), chứa dữ liệu | `public int $price = 0;` |
| *Method* (phương thức) | Hàm khai báo bên trong class, mô tả hành vi | `public function label(): string` |
| *Class constant* (hằng class) | Giá trị cố định gắn với class | `const VAT_PERCENT = 10;` |

```php
<?php
declare(strict_types=1);

class Product                        // từ khoá class + tên class
{
    public string $name = '';        // property
    public int $price = 0;           // property

    public function label(): string  // method
    {
        return $this->name . ': ' . $this->price . 'đ';
    }
}

$p1 = new Product();      // tạo object thứ nhất
$p1->name = 'Bút';        // toán tử -> để truy cập thành viên của object
$p1->price = 5000;

$p2 = new Product();      // object thứ hai, độc lập với $p1
$p2->name = 'Vở';
$p2->price = 12000;

echo $p1->label(), "\n";  // in ra: Bút: 5000đ
echo $p2->label(), "\n";  // in ra: Vở: 12000đ
var_dump($p1);
// in ra:
// object(Product)#1 (2) {
//   ["name"]=>
//   string(4) "Bút"
//   ["price"]=>
//   int(5000)
// }
```

(`string(4)` vì `var_dump` đếm byte: chữ "ú" chiếm 2 byte trong UTF-8, xem [Chương 05](05-chuoi.md).)

```
              class Product   (bản mô tả, chỉ có một)
          ┌─────────────────────────────────┐
          │ property: name, price           │
          │ method:   label()               │
          └────────────────┬────────────────┘
                 new       │       new
          ┌────────────────┴────────────────┐
          ▼                                 ▼
   object #1 (Product)              object #2 (Product)
   name  = "Bút"                    name  = "Vở"
   price = 5000                     price = 12000
```

Mỗi object có bộ property riêng: sửa `$p2->price` không ảnh hưởng `$p1`. Method thì dùng chung, mã
của `label()` chỉ có một bản nằm trong class; khi gọi `$p1->label()`, bên trong method biến `$this`
chính là `$p1` (mục 3). Số `#1`, `#2` mà `var_dump` in ra là mã định danh của object (*object id*),
mỗi object đang sống có một số khác nhau (mục 12).

Bốn ý tưởng thường được gọi là "bốn trụ cột" của OOP, và nơi chúng xuất hiện trong chương này:

| Ý tưởng | Nói đơn giản | Mục |
|---|---|---|
| *Encapsulation* (đóng gói) | Giấu dữ liệu bên trong, chỉ cho thao tác qua method | 5 |
| *Inheritance* (kế thừa) | Class con nhận lại thành viên của class cha | 8 |
| *Polymorphism* (đa hình) | Cùng một lời gọi method, mỗi class phản ứng theo cách của nó | 8, 9, 10 |
| *Abstraction* (trừu tượng hoá) | Làm việc với "cái gì đó làm được X" thay vì một class cụ thể | 9, 10 |

### 1.3 Khai báo class: quy tắc đặt tên

- Cú pháp: từ khoá `class`, tên class, cặp ngoặc `{}` chứa các thành viên.
- Tên class bắt đầu bằng chữ cái hoặc `_`, theo sau là chữ cái, chữ số hoặc `_` (manual đưa biểu thức
  chính quy `^[a-zA-Z_\x80-\xff][a-zA-Z0-9_\x80-\xff]*$`). Không được trùng từ khoá của ngôn ngữ:
  `class List {}` là lỗi cú pháp (`unexpected token "list"`). Từ PHP 8.4, đặt tên class đúng một dấu
  `_` bị deprecated.
- Quy ước cộng đồng (PSR-1, PSR-12): tên class viết *PascalCase* (PSR-1 gọi là *StudlyCaps*): viết
  hoa chữ cái đầu mỗi từ, kể cả từ đầu tiên, như `BankAccount`, `OrderItem`. Method viết
  *camelCase* (`addItem()`), hằng class viết HOA và nối bằng `_` (`MAX_ITEMS`). Mỗi class nằm trong
  một file riêng cùng tên (`BankAccount.php`) để autoloader tìm được ([Chương 11](11-namespace-composer.md)).

⚠️ Tên class **không phân biệt hoa thường**: khai báo `class Product` thì `new product()` vẫn chạy và
tạo object `Product`. Đừng dựa vào điều đó. Khi class chưa được nạp, autoloader (như autoloader
PSR-4 của Composer) đổi tên class bạn viết thành đường dẫn file; trên Linux tên file phân biệt hoa thường nên `product` không khớp
`Product.php`, trong khi trên macOS (hệ file mặc định không phân biệt hoa thường) lại khớp. Kết quả là
code chạy trên máy dev nhưng báo "Class not found" trên server. Luôn viết đúng hoa thường như lúc
khai báo. Ngược lại, tên property và tên biến có phân biệt hoa thường (`$p->Name` khác `$p->name`).

### 1.4 Tạo object bằng `new`

```php
<?php
declare(strict_types=1);

class Product
{
    public string $name = 'Bút';

    public function label(): string
    {
        return 'Sản phẩm: ' . $this->name;
    }
}

$a = new Product();            // cách thông dụng
$b = new Product;              // không truyền gì cho constructor thì bỏ () được, nhưng PSR-12 yêu cầu luôn có ()
$cls = 'Product';
$c = new $cls();               // tên class nằm trong một biến chuỗi
$d = new ('Prod' . 'uct');     // PHP 8.0+: biểu thức bất kỳ, phải bọc trong ngoặc

echo (new Product())->label(), "\n";   // in ra: Sản phẩm: Bút   (mọi phiên bản)
echo new Product()->label(), "\n";     // in ra: Sản phẩm: Bút   (PHP 8.4+; 8.3 trở xuống là Parse error)
var_dump(spl_object_id($a), spl_object_id($b), spl_object_id($c)); // in ra 3 dòng: int(1), int(2), int(3)
```

- `new` cấp phát một object mới, gán giá trị mặc định cho các property, rồi gọi constructor nếu
  class có (mục 4). Mỗi lần `new` là một object khác, dù các property giống hệt nhau.
- `new $cls()`: hữu ích khi tên class chỉ biết lúc chạy (đọc từ config, chọn theo điều kiện). Nếu
  class nằm trong namespace, chuỗi phải là tên đầy đủ kèm namespace ([Chương 11](11-namespace-composer.md)).
- Gọi method ngay trên object vừa tạo: trước PHP 8.4 bắt buộc bọc `(new Product())->label()`. Từ
  8.4 bỏ được cặp ngoặc ngoài, nhưng vẫn phải có `()` sau tên class: `new Product->label()` là lỗi
  cú pháp.
- Bên trong class còn viết được `new self()`, `new static()`, `new parent()` (mục 6).

### 1.5 Biết tên class lúc chạy: `::class` và `get_class()`

```php
<?php
declare(strict_types=1);

class Product {}

$p = new Product();
var_dump(Product::class);   // in ra: string(7) "Product"
var_dump($p::class);        // in ra: string(7) "Product"   (PHP 8.0+, dùng trên object)
var_dump(get_class($p));    // in ra: string(7) "Product"
var_dump(Does\Not\Exist::class); // in ra: string(14) "Does\Not\Exist"
```

- `TênClass::class` trả về tên đầy đủ của class dưới dạng chuỗi. Đây là phép thay thế lúc compile,
  không kiểm tra class có tồn tại (dòng cuối không báo lỗi). Nên dùng thay cho việc gõ tên class
  trong chuỗi `'Product'`: IDE và công cụ đổi tên (refactor) hiểu được `Product::class`, không hiểu
  được chuỗi.
- `$obj::class` (8.0) và `get_class($obj)` trả về tên class của object lúc chạy.

### 1.6 `stdClass`: object không có class riêng

`stdClass` là một class rỗng có sẵn của PHP, cho phép gắn property tuỳ ý vào object. Bạn sẽ gặp nó
khi ép kiểu array sang object, khi `json_decode()` không truyền tham số thứ hai, hoặc khi PDO trả về
dòng dạng object ([Chương 16](16-php-va-database.md)):

```php
<?php
declare(strict_types=1);

$o = (object) ['name' => 'An', 'age' => 20];    // ép array thành stdClass
$o->email = 'an@example.com';                   // stdClass cho phép thêm property tuỳ ý
var_dump($o instanceof stdClass);               // in ra: bool(true)

$j = json_decode('{"id": 7, "tags": ["php", "oop"]}');
echo get_class($j), ' ', $j->id, ' ', $j->tags[1], "\n";   // in ra: stdClass 7 oop
```

- `stdClass` không phải class cha chung của mọi class. PHP không có class gốc chung (khác Java,
  nơi mọi class đều ngầm kế thừa `java.lang.Object`).
- Trong code mới, khi dữ liệu có cấu trúc cố định thì nên khai báo class riêng với property có kiểu.
  `stdClass` không có kiểu, không chặn gõ sai tên, IDE không gợi ý được.

## 2. Property: dữ liệu của object

### 2.1 Khai báo property

Cú pháp đầy đủ của một khai báo property:

```
[visibility] [static] [readonly] [kiểu] $tên [= giá trị mặc định];
   public                           int    $price   = 0;
```

- Phải có ít nhất một từ khoá đứng trước: visibility (`public`, `protected`, `private`, mục 5),
  `static` (mục 6), hoặc `readonly` (PHP 8.1, [Chương 10](10-oop-nang-cao.md)). Viết `int $x;` trần
  trong class là lỗi cú pháp. Từ khoá `var` là cách viết cũ, tương đương `public`; code mới không dùng.
- Không ghi visibility (ví dụ chỉ có `static $count;`) thì property là `public`.
- Kiểu là tuỳ chọn nhưng nên luôn ghi (mục 2.2).
- Giá trị mặc định phải là *biểu thức hằng* (*constant expression*): giá trị tính được ngay lúc
  compile, gồm literal, phép toán giữa chúng, hằng, hằng class và array của những thứ đó. Không
  được gọi hàm, dùng biến, hay `new`.

```php
<?php
declare(strict_types=1);

class Config
{
    const BASE = 3;

    public string $greeting = 'hello ' . 'world';   // hợp lệ: nối hai literal
    public int $sum = 1 + 2;                         // hợp lệ: phép toán trên literal
    public array $flags = [true, false];             // hợp lệ: array literal
    public int $double = self::BASE * 2;             // hợp lệ: dùng hằng class
    public int $intSize = PHP_INT_SIZE;              // hợp lệ: hằng có sẵn

    // public int $now = time();                     // Fatal error: Constant expression contains invalid operations
    // public array $copy = $globalArray;            // Fatal error: Constant expression contains invalid operations
    // public DateTime $at = new DateTime();         // Fatal error: New expressions are not supported in this context
}

$c = new Config();
echo $c->greeting, ' ', $c->sum, ' ', $c->double, "\n";   // in ra: hello world 3 6
```

Muốn giá trị ban đầu tính lúc chạy (thời điểm hiện tại, một object khác) thì gán trong constructor
(mục 4).

### 2.2 Property có kiểu (typed property)

Từ PHP 7.4, property khai báo kiểu được giống tham số hàm: `int`, `string`, `?string`, `array`, tên
class, union type `int|string`... ([Chương 04](04-kieu-du-lieu.md)). Ngoại lệ duy nhất cần nhớ là
`callable`: `public callable $cb;` là Fatal error "cannot have type callable". RFC giải thích lý do:
một giá trị có "gọi được" hay không phụ thuộc vào chỗ đứng (ví dụ `[$this, 'tenMethod']` trỏ tới
một method `private` chỉ gọi được từ trong class), nên PHP không đảm bảo được kiểu khi đọc ra. Dùng kiểu `Closure` thay thế.

Mỗi lần gán, PHP kiểm tra giá trị với kiểu đã khai báo. Quy tắc giống khi truyền tham số: chế độ
`strict_types` của file đang thực hiện phép gán quyết định.

```php
<?php
declare(strict_types=1);

class Product
{
    public int $price = 0;
    public float $weight = 0.0;
}

$p = new Product();
$p->weight = 2;              // int sang float: luôn được phép, kể cả strict mode
var_dump($p->weight);        // in ra: float(2)

try {
    $p->price = '5000';      // strict mode: chuỗi không tự đổi thành int
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
}
// in ra: Cannot assign string to property Product::$price of type int
```

Nếu file thực hiện phép gán không có `declare(strict_types=1)`, PHP thử ép kiểu như với tham số:
`'5000'` thành `5000`, còn `'abc'` thì vẫn `TypeError`. Dù ở chế độ nào, giá trị nằm trong property
luôn đúng kiểu đã khai báo. Đó là lợi ích lớn nhất của typed property: đọc `$p->price` ở bất cứ đâu,
bạn chắc chắn nó là `int`.

Giá trị mặc định sai kiểu bị bắt ngay lúc compile, trước khi chạy dòng nào:

```php
class Bad
{
    public int $x = 'a';
}
// Fatal error: Cannot use string as default value for property Bad::$x of type int
```

### 2.3 Trạng thái uninitialized

Đây là điểm người mới hay vấp nhất. Property **có kiểu** mà **không có giá trị mặc định** thì sau
`new` không mang giá trị `null`, mà ở trạng thái đặc biệt gọi là *uninitialized* (chưa khởi tạo).
Đọc nó trước khi gán thì ném `Error`:

```php
<?php
declare(strict_types=1);

class User
{
    public int $id;                 // có kiểu, không mặc định: uninitialized
    public ?string $nickname;       // nullable nhưng KHÔNG tự thành null: vẫn uninitialized
    public ?string $bio = null;     // muốn mặc định là null thì phải ghi rõ
    public $legacy;                 // không có kiểu: mặc định null (hành vi cũ)
}

$u = new User();
var_dump($u);
// in ra:
// object(User)#1 (2) {
//   ["id"]=>
//   uninitialized(int)
//   ["nickname"]=>
//   uninitialized(?string)
//   ["bio"]=>
//   NULL
//   ["legacy"]=>
//   NULL
// }

try {
    echo $u->nickname;
} catch (Error $e) {
    echo $e->getMessage(), "\n";
}
// in ra: Typed property User::$nickname must not be accessed before initialization

var_dump(isset($u->id));   // in ra: bool(false)   (isset không ném lỗi)
$u->id = 5;
unset($u->id);             // unset đưa property có kiểu về lại trạng thái uninitialized
var_dump(isset($u->id));   // in ra: bool(false)
```

| Khai báo | Ngay sau `new` | Đọc ngay thì sao |
|---|---|---|
| `public $x;` | `null` | Trả `null` |
| `public int $x = 0;` | `0` | Trả `0` |
| `public ?string $x = null;` | `null` | Trả `null` |
| `public int $x;` | uninitialized | `Error` |
| `public ?string $x;` | uninitialized | `Error` |

Vì sao PHP không cho mặc định `null`? Vì `null` không thuộc kiểu `int`; và với kiểu nullable, một giá
trị `null` "tự có" sẽ che mất lỗi quên gán. Thiết kế này buộc lỗi lộ ra sớm, ngay chỗ đọc. Cách dùng
đúng: hoặc ghi giá trị mặc định, hoặc gán trong constructor (mục 4) để sau khi `new` xong, mọi
property đều đã có giá trị.

Để ý `var_dump` ghi `(2)`: nó chỉ đếm các property đã có giá trị.

### 2.4 Truy cập property

- Từ bên ngoài: `$obj->tên`. Không có dấu `$` trước tên property.
- Bên trong method của class: `$this->tên` (mục 3).
- Đọc property không tồn tại: PHP phát `Warning: Undefined property` và trả `null`, chương trình
  vẫn chạy tiếp.
- Nullsafe `$obj?->tên`: nếu `$obj` là `null` thì cả biểu thức là `null` thay vì lỗi
  ([Chương 07](07-toan-tu-dieu-khien.md)).

⚠️ `$obj->$name` (có `$` trước tên) khác hẳn `$obj->name`. Nó nghĩa là "đọc property có tên bằng
giá trị của biến `$name`". Viết nhầm thì PHP không báo lỗi cú pháp mà đọc sai property, hoặc phát
warning khó hiểu.

```php
<?php
declare(strict_types=1);

class Product
{
    public string $name = 'Bút';
    public int $price = 5000;
}

$p = new Product();

$field = 'price';
echo $p->$field, "\n";             // in ra: 5000   (đọc $p->price)
echo $p->{'na' . 'me'}, "\n";      // in ra: Bút    (tên property là một biểu thức, bọc trong {})

var_dump($p->colour);              // Warning: Undefined property: Product::$colour
                                   // in ra: NULL
```

Truy cập property theo tên động như vậy đôi khi hữu ích (map dữ liệu từ array vào object), nhưng làm
mất khả năng kiểm tra của IDE và công cụ phân tích tĩnh. Chỉ dùng khi thật cần.

### 2.5 Dynamic property và vì sao bị deprecated

Gán vào một property chưa khai báo thì PHP tự tạo property đó, chỉ trên đúng object ấy. Gọi là
*dynamic property*. Từ PHP 8.2, việc này phát `Deprecated`:

```php
<?php
declare(strict_types=1);

class Product
{
    public string $name = 'Bút';
}

$p = new Product();
$p->colour = 'đỏ';   // PHP 8.2+: Deprecated: Creation of dynamic property Product::$colour is deprecated
var_dump($p);
// in ra:
// object(Product)#1 (2) {
//   ["name"]=>
//   string(4) "Bút"
//   ["colour"]=>
//   string(5) "đỏ"
// }

#[\AllowDynamicProperties]
class Bag {}

$b = new Bag();
$b->anything = 1;    // không cảnh báo: class đã chủ động cho phép
```

- Lý do deprecated: phần lớn dynamic property là lỗi gõ sai tên (`$this->naem = ...`) mà trước đây
  PHP lặng lẽ chấp nhận. RFC đặt kế hoạch biến việc này thành `Error` ở PHP 9.0.
- Ngoại lệ không bị cảnh báo: `stdClass` và class con của nó; class gắn attribute
  `#[\AllowDynamicProperties]`; class tự xử lý phép gán vào property không tồn tại bằng magic method
  `__set()` (thường đi kèm `__get()` để đọc, [Chương 10](10-oop-nang-cao.md)). Class chỉ có `__get()`
  thì phép gán vẫn tạo dynamic property và vẫn bị cảnh báo.
- Cách đúng là khai báo mọi property; manual khuyên vậy, và nếu class thật sự cần nhận tên property
  tuỳ ý thì nên cài `__get()`/`__set()`. `#[\AllowDynamicProperties]` chủ yếu hữu ích cho code cũ chưa
  kịp sửa.
- Đọc property chưa khai báo thì chưa bao giờ bị deprecated theo nghĩa này: nó vẫn là `Warning` và trả
  `null` như mục 2.4.

## 3. Method và `$this`

### 3.1 Method là hàm nằm trong class

Mọi thứ đã học về hàm ở [Chương 08](08-ham.md) đều dùng được cho method: tham số có kiểu, giá trị
mặc định, named arguments, variadic, kiểu trả về. Khác biệt: method có visibility (không ghi thì là
`public`), được gọi thông qua một object bằng `->`, và bên trong có biến `$this`.

```php
<?php
declare(strict_types=1);

class Cart
{
    private array $items = [];

    public function add(string $name, int $price, int $qty = 1): void
    {
        $this->items[] = ['name' => $name, 'price' => $price, 'qty' => $qty];
    }

    public function total(): int
    {
        $sum = 0;
        foreach ($this->items as $item) {
            $sum += $item['price'] * $item['qty'];
        }
        return $sum;
    }

    public function totalWithVat(int $percent = 10): int
    {
        return intdiv($this->total() * (100 + $percent), 100);   // method gọi method khác qua $this
    }
}

$cart = new Cart();
$cart->add('Bút', 5000, 3);
$cart->add(name: 'Vở', price: 12000);     // named arguments dùng được như hàm thường
echo $cart->total(), "\n";                // in ra: 27000
echo $cart->totalWithVat(), "\n";         // in ra: 29700
```

Giống tên hàm, tên method không phân biệt hoa thường (`$cart->TOTAL()` vẫn chạy), nhưng hãy
luôn gọi đúng như khai báo.

### 3.2 `$this` là gì

`$this` là một *pseudo-variable* (biến giả) mà PHP tự đặt khi method được gọi trên một object: gọi
`$cart->total()` thì bên trong `total()`, `$this` chính là object `$cart`. Gọi trên object khác thì
`$this` là object khác; nhờ vậy cùng một đoạn mã method phục vụ được mọi object của class.

```
$cart->total()
   │
   └──► Cart::total() chạy với $this = object của $cart
              $this->items  →  items của ĐÚNG object $cart
```

- `$this` không gán lại được: `$this = new Cart();` là Fatal error "Cannot re-assign $this".
- `$this` chỉ tồn tại trong method không static được gọi trên một object. Method `static` (mục 6)
  không có `$this`.
- Gọi một method thường theo kiểu static (`Cart::total()`) ném `Error: Non-static method
  Cart::total() cannot be called statically` từ PHP 8.0. Ở PHP 7.x đó chỉ là thông báo Deprecated
  và `$this` không được định nghĩa bên trong.
- Closure viết bên trong method tự động mang theo `$this` của method đó ([Chương 08](08-ham.md)).

⚠️ Bẫy cho người quen Java, C#: PHP không có `this` ngầm. Trong method, `$items` là một biến cục
bộ (chưa gán), không phải property; `total()` là lời gọi hàm toàn cục, không phải method. Phải viết
đủ `$this->items`, `$this->total()`.

```php
<?php
declare(strict_types=1);

class Cart
{
    private array $items = [];

    public function total(): int
    {
        return count($this->items);
    }

    public function brokenCount(): int
    {
        return count($items);   // quên $this->: $items là biến cục bộ chưa có
    }

    public function brokenTotal(): int
    {
        return total();         // quên $this->: gọi hàm toàn cục total()
    }
}

$cart = new Cart();
try {
    $cart->brokenCount();
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
}
// Warning: Undefined variable $items
// in ra: count(): Argument #1 ($value) must be of type Countable|array, null given

try {
    $cart->brokenTotal();
} catch (Error $e) {
    echo $e->getMessage(), "\n";
}
// in ra: Call to undefined function total()
```

### 3.3 Property và method có không gian tên riêng

Property và method được tra cứu ở hai chỗ khác nhau, nên một class có thể có property và method trùng
tên. PHP phân biệt bằng ngữ cảnh: có `()` là gọi method, không có là đọc property. Hệ quả: một
closure cất trong property không gọi được bằng `$obj->prop()`, vì PHP sẽ đi tìm method tên `prop`.

```php
<?php
declare(strict_types=1);

class Formatter
{
    public string $format = 'upper';       // property tên format
    public ?Closure $transform = null;     // property chứa một closure

    public function format(string $s): string   // method cũng tên format: không xung đột
    {
        return '[' . $s . ']';
    }
}

$f = new Formatter();
$f->transform = fn(string $s): string => strtoupper($s);

echo $f->format, "\n";             // in ra: upper   (property)
echo $f->format('hi'), "\n";       // in ra: [hi]    (method)
echo ($f->transform)('hi'), "\n";  // in ra: HI      (gọi closure trong property: bọc ngoặc)

try {
    echo $f->transform('hi');
} catch (Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Call to undefined method Formatter::transform()
}
```

### 3.4 Method trả về `$this`: gọi nối chuỗi (fluent interface)

Method sửa object rồi `return $this` cho phép gọi nối tiếp nhiều method trên cùng một object. Kiểu
này gọi là *fluent interface*. Kiểu trả về nên khai báo là `static` ("object của đúng class đang
được gọi", [Chương 04](04-kieu-du-lieu.md)), để class con kế thừa method vẫn giữ đúng kiểu.

```php
<?php
declare(strict_types=1);

class QueryBuilder
{
    private string $table = '';
    private array $wheres = [];
    private ?int $limit = null;

    public function from(string $table): static
    {
        $this->table = $table;
        return $this;                       // trả về chính object để gọi tiếp
    }

    public function where(string $condition): static
    {
        $this->wheres[] = $condition;
        return $this;
    }

    public function limit(int $n): static
    {
        $this->limit = $n;
        return $this;
    }

    public function toSql(): string
    {
        $sql = 'SELECT * FROM ' . $this->table;
        if ($this->wheres !== []) {
            $sql .= ' WHERE ' . implode(' AND ', $this->wheres);
        }
        if ($this->limit !== null) {
            $sql .= ' LIMIT ' . $this->limit;
        }
        return $sql;
    }
}

echo (new QueryBuilder())
    ->from('users')
    ->where('age >= 18')
    ->where("status = 'active'")
    ->limit(10)
    ->toSql(), "\n";
// in ra: SELECT * FROM users WHERE age >= 18 AND status = 'active' LIMIT 10
```

Query builder của Laravel (`DB::table('users')->where(...)->orderBy(...)->get()`) dùng đúng kiểu này
([Chương 27](27-laravel-database-eloquent.md)). ⚠️ Ví dụ trên ghép chuỗi SQL chỉ để minh hoạ cú pháp;
SQL thật phải dùng prepared statement để tránh SQL injection ([Chương 16](16-php-va-database.md),
[Chương 17](17-bao-mat.md)). Ngoài ra fluent kiểu này sửa chính object: nếu hai nơi cùng giữ một
builder thì nơi này thêm `where` sẽ ảnh hưởng nơi kia (mục 12 giải thích vì sao, và cách tránh bằng
`clone`).

## 4. Constructor và destructor

### 4.1 Constructor: chuẩn bị object ngay lúc tạo

Ở các ví dụ trước, ta `new` xong rồi mới gán từng property từ bên ngoài. Cách đó có hai nhược điểm:
quên gán một property thì object ở trạng thái dở dang (mục 2.3), và không có chỗ nào kiểm tra dữ liệu
đầu vào. *Constructor* (hàm khởi tạo) giải quyết cả hai: đó là method tên `__construct` mà PHP tự
gọi ngay sau khi tạo object, với các đối số bạn đặt trong ngoặc sau tên class.

```php
<?php
declare(strict_types=1);

class Point
{
    public int $x;
    public int $y;

    public function __construct(int $x, int $y = 0)
    {
        $this->x = $x;
        $this->y = $y;
    }
}

$p1 = new Point(4, 5);
$p2 = new Point(4);              // $y lấy mặc định 0
$p3 = new Point(y: 5, x: 4);     // named arguments
echo "$p1->x,$p1->y $p2->x,$p2->y $p3->x,$p3->y\n";   // in ra: 4,5 4,0 4,5

try {
    new Point();                 // thiếu đối số bắt buộc
} catch (ArgumentCountError $e) {
    echo get_class($e), "\n";    // in ra: ArgumentCountError
}
```

```
new Point(4, 5)
  1. cấp phát object, gán giá trị mặc định khai báo ở property (nếu có)
  2. gọi $obj->__construct(4, 5)          ← $this là object vừa tạo
  3. trả object về cho biểu thức new       (constructor ném lỗi thì không có object nào được trả về)
```

Những điều cần biết:

- Constructor là method thường về mặt cú pháp: có tham số kiểu, mặc định, named arguments. Nhưng nó
  không được khai báo kiểu trả về, kể cả `void`: `public function __construct(): void` là Fatal
  error "cannot declare a return type".
- Mỗi class chỉ có một constructor. PHP không có overloading (nhiều constructor khác tham số) như
  Java. Muốn nhiều cách tạo object thì dùng *named constructor* (static method tạo object, mục 6.4).
- Trước PHP 8.0, với class không nằm trong namespace, method trùng tên class
  (`class Point { function Point() {} }`) được coi là constructor kiểu cũ (từ thời PHP 4). Từ 8.0 nó
  chỉ là method bình thường. Luôn dùng `__construct`.
- Class con có constructor riêng thì constructor của class cha không tự chạy; phải gọi
  `parent::__construct(...)` (mục 8.4).
- Nếu constructor ném exception, biểu thức `new` không trả về object nào, và destructor của object dở
  dang đó cũng không chạy.

Constructor là nơi đặt các kiểm tra để object luôn hợp lệ ngay từ lúc sinh ra. Một object
`Email` chỉ tồn tại khi chuỗi bên trong là email; mọi chỗ nhận `Email` không cần kiểm tra lại. Ý tưởng
này gọi là bảo vệ *invariant* (bất biến của object: điều kiện luôn đúng suốt đời object).

### 4.2 Constructor property promotion (PHP 8.0)

Constructor ở mục 4.1 lặp lại mỗi tên ba lần: khai báo property, tham số, dòng gán. Với class có năm
sáu dependency, phần lặp này rất dài và dễ quên một dòng gán. Từ PHP 8.0, đặt từ khoá visibility
trước tham số constructor thì tham số đó được *promote* (nâng cấp) thành property:

```php
// Viết thế này (8.0+)...
class Point
{
    public function __construct(public int $x, public int $y = 0) {}
}

// ...PHP hiểu như thế này
class Point
{
    public int $x;
    public int $y;

    public function __construct(int $x, int $y = 0)
    {
        $this->x = $x;
        $this->y = $y;
    }
}
```

Ví dụ đầy đủ hơn, trộn tham số promote với tham số thường:

```php
<?php
declare(strict_types=1);

class Email
{
    public function __construct(private string $value)
    {
        // Thân constructor chạy SAU khi $this->value đã được gán từ tham số
        if (!str_contains($this->value, '@')) {
            throw new InvalidArgumentException("Email không hợp lệ: {$value}");
        }
        $this->value = strtolower($this->value);
    }

    public function value(): string
    {
        return $this->value;
    }
}

class User
{
    public string $displayName;                   // property khai báo theo cách thường

    public function __construct(
        public readonly int $id,                  // promote (readonly: Chương 10)
        private Email $email,                     // promote
        string $firstName,                        // tham số thường: KHÔNG thành property
        string $lastName,
        public ?string $avatarUrl = null,         // promote, có giá trị mặc định
    ) {
        $this->displayName = $firstName . ' ' . $lastName;
    }

    public function email(): string
    {
        return $this->email->value();
    }
}

$u = new User(1, new Email('An@Example.com'), 'Nguyễn', 'An');
echo $u->id, ' ', $u->displayName, ' ', $u->email(), "\n";   // in ra: 1 Nguyễn An an@example.com
var_dump($u->avatarUrl);                    // in ra: NULL
var_dump(property_exists($u, 'firstName')); // in ra: bool(false)

try {
    new Email('khong-hop-le');
} catch (InvalidArgumentException $e) {
    echo $e->getMessage(), "\n";            // in ra: Email không hợp lệ: khong-hop-le
}
```

Quy tắc của promotion (đều kiểm tra lúc compile, vi phạm là Fatal error):

| Quy tắc | Vi phạm thì |
|---|---|
| Chỉ dùng trong `__construct` không abstract | `Cannot declare promoted property outside a constructor` |
| Cần một modifier: `public`/`protected`/`private`, hoặc chỉ `readonly` (8.1), hoặc chỉ `final` (8.5). Không dùng `var` | Không có modifier thì đó là tham số thường |
| Không trùng với property đã khai báo | `Cannot redeclare T::$p` |
| Không dùng kiểu `callable` (như mọi property) | Fatal error |
| Không dùng cho tham số variadic `...$xs` | `Cannot declare variadic promoted property` |
| Mặc định `null` thì kiểu phải nullable rõ ràng: `public ?DateTime $d = null` | `Cannot use null as default value for parameter $d of type DateTime` |

- Giá trị mặc định của tham số promote chỉ thuộc về tham số, property sinh ra không có giá trị
  mặc định riêng. Không ảnh hưởng gì khi dùng bình thường, vì constructor luôn gán nó.
- Thứ tự chạy: các phép gán promote xảy ra đầu tiên, rồi mới tới các dòng trong thân. Vì thế
  trong thân dùng được cả `$value` (tham số) lẫn `$this->value` (property).
- Nên xuống dòng mỗi tham số và để dấu phẩy cuối (*trailing comma*, hợp lệ từ PHP 8.0) như ví dụ
  `User`: thêm bớt tham số chỉ đổi một dòng trong diff.

### 4.3 Dependency mặc định: `new` trong giá trị mặc định (PHP 8.1)

Mục 2.1 nói giá trị mặc định của property không được dùng `new`. Riêng giá trị mặc định của tham
số thì từ PHP 8.1 được phép `new` (tính năng *new in initializers*). Kết hợp với promotion, ta có
cách gọn để khai báo "dependency có sẵn bản mặc định, nhưng thay được":

```php
<?php
declare(strict_types=1);

class Logger
{
    public function log(string $message): void
    {
        echo "[log] {$message}\n";
    }
}

class OrderService
{
    public function __construct(
        private Logger $logger = new Logger(),   // PHP 8.1+; PHP 8.0 báo Fatal error
    ) {}

    public function place(string $item): void
    {
        $this->logger->log("đặt hàng: {$item}");
    }
}

(new OrderService())->place('Bút');   // in ra: [log] đặt hàng: Bút
```

`new Logger()` chỉ chạy khi người gọi không truyền đối số này. Khi viết test, bạn truyền vào một
logger khác; mục 10 (interface) cho thấy cách làm logger "thay được" một cách đúng nghĩa. Ngoài tham
số, PHP 8.1 còn cho `new` trong giá trị khởi tạo biến `static`, hằng toàn cục và đối số attribute,
nhưng không cho trong property và hằng class.

### 4.4 Destructor: dọn dẹp khi object biến mất

*Destructor* là method `__destruct()` mà PHP tự gọi khi object sắp bị giải phóng. Dùng để trả tài
nguyên mà object đang giữ: đóng file, nhả khoá, xoá file tạm. Destructor không nhận tham số và không
khai báo kiểu trả về được.

Khi nào object bị giải phóng? PHP đếm xem có bao nhiêu chỗ đang giữ object (*reference counting*,
đếm tham chiếu): mỗi biến, phần tử array, property đang trỏ tới object là một chỗ. Khi số đó về 0,
object bị giải phóng ngay lập tức và destructor chạy ngay tại đó. Object còn sống tới cuối
script thì bị huỷ trong giai đoạn kết thúc (*shutdown*), theo thứ tự không đảm bảo.

```php
<?php
declare(strict_types=1);

class TempFile
{
    public function __construct(private string $name)
    {
        echo "tạo {$this->name}\n";
    }

    public function __destruct()
    {
        echo "huỷ {$this->name}\n";
    }
}

function work(): void
{
    $t = new TempFile('C');
    echo "đang dùng C\n";
}   // hết hàm: biến cục bộ $t biến mất, không còn ai giữ C

$a = new TempFile('A');
$a = null;                     // không còn biến nào trỏ tới A: huỷ ngay
echo "sau khi gán null\n";

$b = new TempFile('B');
$b2 = $b;                      // hai biến cùng trỏ tới B
unset($b);                     // còn $b2 giữ: CHƯA huỷ
echo "sau unset(\$b)\n";
unset($b2);                    // không còn ai giữ: huỷ
echo "sau unset(\$b2)\n";

work();
echo "sau work()\n";

$d = new TempFile('D');
echo "hết script\n";           // D bị huỷ trong giai đoạn shutdown, sau dòng này

// in ra:
// tạo A
// huỷ A
// sau khi gán null
// tạo B
// sau unset($b)
// huỷ B
// sau unset($b2)
// tạo C
// đang dùng C
// huỷ C
// sau work()
// tạo D
// hết script
// huỷ D
```

Vì thời điểm huỷ đoán trước được, PHP dùng được kiểu "mở ở constructor, đóng ở destructor" (giống
RAII của C++). Java không làm được vậy: GC của Java dọn object vào lúc không xác định. Những cạm bẫy:

- ⚠️ Class con có `__destruct()` riêng thì destructor của cha không tự chạy, phải gọi
  `parent::__destruct()`. Class con không khai báo thì kế thừa destructor của cha.
- ⚠️ Exception ném ra từ destructor khi object bị huỷ giữa chừng thì bắt được như bình thường, nhưng
  nếu xảy ra trong giai đoạn shutdown thì thành Fatal error. Destructor nên đơn giản, không ném lỗi.
- ⚠️ Object nằm trong *vòng tham chiếu* (A giữ B, B giữ A) thì số đếm không về 0 khi bạn bỏ biến, nên
  destructor bị hoãn tới khi bộ thu gom vòng (*cycle collector*) chạy, có khi tới cuối script
  ([Chương 19](19-ben-trong-engine.md)).
- ⚠️ Destructor chạy lúc shutdown thì HTTP header đã gửi xong, đừng in output hay gửi header ở đó.
- Trong tiến trình sống lâu (queue worker, Laravel Octane) object nằm trong property `static` hoặc
  container sẽ sống tới khi tiến trình dừng, nên destructor của nó cũng chỉ chạy lúc đó
  ([Chương 30](30-laravel-testing-octane-deploy.md)). Tài nguyên quan trọng (transaction, lock) nên
  đóng tường minh bằng `try`/`finally` ([Chương 12](12-loi-exception.md)) thay vì trông vào destructor.

## 5. Visibility: public, protected, private

### 5.1 Encapsulation: vì sao phải giấu

*Encapsulation* (đóng gói) là nguyên tắc: object tự quản lý dữ liệu của nó; bên ngoài chỉ được
thao tác qua một tập method được công bố, gọi là *public API* (giao diện công khai) của class. Lợi ích:

- Bảo vệ invariant. Số dư chỉ đổi qua `deposit()`/`withdraw()` thì quy tắc "không âm" chỉ cần
  kiểm tra ở hai chỗ, và chắc chắn không bị đi vòng (mục 1.1).
- Đổi cài đặt bên trong mà không làm vỡ code gọi. Hôm nay `Cart` lưu item trong array; mai đổi
  sang lưu theo key sản phẩm. Nếu bên ngoài chỉ gọi `add()` và `total()` thì không ai bị ảnh hưởng.
  Nếu bên ngoài đã đọc thẳng `$cart->items`, mọi chỗ đó vỡ.

PHP thực hiện encapsulation bằng ba từ khoá *visibility* (phạm vi truy cập), đặt trước property,
method và hằng class.

### 5.2 Ba mức truy cập

| Truy cập từ | `public` | `protected` | `private` |
|---|---|---|---|
| Code bên trong chính class khai báo | Được | Được | Được |
| Code trong class con (và class cha) | Được | Được | Không |
| Code bên ngoài (hàm thường, file khác, global) | Được | Không | Không |

- Không ghi visibility thì method, property và hằng class đều là `public`.
- "Bên trong class" nghĩa là code nằm trong thân class đó, bất kể đang chạy trên object nào.
- `protected` mở cho cả họ kế thừa. Manual ghi rõ cả class cha cũng truy cập được thành viên
  `protected` mà class con khai báo, vì chúng cùng một cây kế thừa. Trường hợp này hiếm gặp.

```php
<?php
declare(strict_types=1);

class Account
{
    public string $owner = 'An';
    protected int $limit = 1000;
    private int $balance = 0;

    private function audit(): string { return 'audit'; }
    protected function rule(): string { return 'rule'; }

    public function show(): string
    {
        // bên trong class: thấy hết
        return "{$this->owner} {$this->limit} {$this->balance} " . $this->audit() . ' ' . $this->rule();
    }
}

class SavingAccount extends Account   // class con (mục 8)
{
    public function test(): string
    {
        return $this->owner . ' ' . $this->limit . ' ' . $this->rule();   // public, protected: được
    }
}

$a = new Account();
echo $a->show(), "\n";                     // in ra: An 1000 0 audit rule
echo (new SavingAccount())->test(), "\n";  // in ra: An 1000 rule

try { echo $a->limit; }   catch (Error $e) { echo $e->getMessage(), "\n"; }
try { echo $a->balance; } catch (Error $e) { echo $e->getMessage(), "\n"; }
try { $a->audit(); }      catch (Error $e) { echo $e->getMessage(), "\n"; }
try { $a->rule(); }       catch (Error $e) { echo $e->getMessage(), "\n"; }
// in ra:
// Cannot access protected property Account::$limit
// Cannot access private property Account::$balance
// Call to private method Account::audit() from global scope
// Call to protected method Account::rule() from global scope
```

`var_dump` và `print_r` cho thấy visibility của từng property:

```php
<?php
declare(strict_types=1);

class V
{
    public $pub = 1;
    protected $pro = 2;
    private $pri = 3;
}

var_dump(new V());
// in ra:
// object(V)#1 (3) {
//   ["pub"]=>
//   int(1)
//   ["pro":protected]=>
//   int(2)
//   ["pri":"V":private]=>
//   int(3)
// }
```

Property `private` được ghi kèm tên class khai báo nó (`"pri":"V":private`). Chi tiết này giải thích
cạm bẫy ở mục 5.4.

### 5.3 Visibility tính theo class, không theo object

Quy tắc ở mục 5.2 xét code nằm trong class nào, không xét đang đứng ở object nào. Vì vậy một
method của `Money` đọc được property `private` của một object `Money` khác:

```php
<?php
declare(strict_types=1);

class Money
{
    public function __construct(
        private int $amount,
        private string $currency,
    ) {}

    public function equals(Money $other): bool
    {
        // $other là object khác, nhưng code này nằm trong class Money nên đọc được private của nó
        return $this->amount === $other->amount && $this->currency === $other->currency;
    }

    public function add(Money $other): Money
    {
        if ($this->currency !== $other->currency) {
            throw new InvalidArgumentException('Khác loại tiền');
        }
        return new Money($this->amount + $other->amount, $this->currency);
    }
}

$a = new Money(100, 'VND');
$b = new Money(100, 'VND');
var_dump($a->equals($b));   // in ra: bool(true)
var_dump($a->add($b));
// in ra:
// object(Money)#3 (2) {
//   ["amount":"Money":private]=>
//   int(200)
//   ["currency":"Money":private]=>
//   string(3) "VND"
// }
```

Manual giải thích: các object cùng kiểu vốn đã "biết" chi tiết cài đặt của nhau, nên không cần giấu
nhau. Java và C# cũng theo quy tắc này. Nhờ vậy các method như `equals()`, `add()`, `compareTo()`
không phải mở getter công khai chỉ để so sánh.

### 5.4 Cạm bẫy: `private` của class cha "không tồn tại" với class con

Từ góc nhìn của class con, property `private` của cha giống như không có. Đọc nó thì nhận `Warning:
Undefined property`; tệ hơn, ghi vào nó thì PHP tạo một property mới trên object (dynamic
property), còn property thật của cha vẫn nguyên:

```php
<?php
declare(strict_types=1);

class Account
{
    private int $balance = 100;

    public function balance(): int
    {
        return $this->balance;
    }
}

class SavingAccount extends Account
{
    public function addInterest(): void
    {
        $this->balance = 999;     // tưởng là sửa property của cha...
    }
}

$s = new SavingAccount();
$s->addInterest();   // PHP 8.2+: Deprecated: Creation of dynamic property SavingAccount::$balance is deprecated
echo $s->balance(), "\n";   // in ra: 100   (property của cha không đổi)
var_dump($s);
// in ra:
// object(SavingAccount)#1 (2) {
//   ["balance":"Account":private]=>
//   int(100)
//   ["balance"]=>
//   int(999)
// }
```

Object giờ có hai property tên `balance`: một của `Account` (private), một dynamic property mới.
Trước PHP 8.2 chuyện này xảy ra hoàn toàn im lặng. Nếu class con cần đọc hoặc ghi, cha phải khai báo
`protected`, hoặc tốt hơn là cung cấp method `protected`/`public` để con dùng.

Method `private` cũng vậy: class con khai báo method cùng tên thì đó là một method hoàn toàn mới,
không phải override (mục 8.5).

### 5.5 Chọn visibility nào

Quy tắc thực dụng: **bắt đầu với `private`, chỉ nới rộng khi có lý do.**

| Chọn | Khi nào |
|---|---|
| `private` | Mặc định cho property và method trợ giúp nội bộ |
| `protected` | Có chủ đích cho class con dùng hoặc thay đổi (điểm mở rộng, mục 9) |
| `public` | Thuộc public API: thứ bạn cam kết giữ ổn định cho code bên ngoài |

- Mọi thứ `public` là một lời hứa: đổi tên hay xoá nó sẽ làm vỡ code của người khác. `private` thì đổi
  thoải mái.
- `protected` cũng là một dạng lời hứa, với class con. Nhiều đội chọn đánh dấu class `final` (mục 8.6)
  và chỉ dùng `private`/`public`.
- Property `public` cho phép bên ngoài gán giá trị bất kỳ (đúng kiểu) mà không qua kiểm tra nào. Cách
  truyền thống là để property `private` và viết method `getX()`/`setX()`. PHP hiện đại có những cách
  gọn hơn: `readonly` (8.1), *asymmetric visibility* `public private(set)` (8.4) và *property hooks*
  (8.4), tất cả ở [Chương 10](10-oop-nang-cao.md).
- ⚠️ Visibility là công cụ thiết kế, không phải cơ chế bảo mật. Reflection và
  `Closure::bind()` vẫn đọc được `private` ([Chương 08](08-ham.md), [Chương 10](10-oop-nang-cao.md)).
  Đừng coi `private` là nơi cất bí mật.

## 6. Static: thành viên thuộc về class

### 6.1 Static property và static method

Đến giờ mọi property đều là của từng object: mỗi object một bản. Đôi khi ta cần dữ liệu thuộc về
cả class, dùng chung, tồn tại cả khi chưa có object nào: một bộ đếm số vé đã phát, một bảng cấu
hình chung. Đánh dấu thành viên bằng từ khoá `static` thì nó thuộc về class:

```php
<?php
declare(strict_types=1);

class Ticket
{
    private static int $issued = 0;      // static: chỉ một bản, thuộc về class
    public int $number;                  // thường: mỗi object một bản

    public function __construct()
    {
        self::$issued++;                 // truy cập static property: self:: và CÓ dấu $
        $this->number = self::$issued;
    }

    public static function issuedCount(): int   // static method: gọi không cần object
    {
        return self::$issued;
    }

    public static function broken(): int
    {
        return $this->number;            // static method không có $this
    }
}

echo Ticket::issuedCount(), "\n";        // in ra: 0   (chưa có object nào vẫn gọi được)
$t1 = new Ticket();
$t2 = new Ticket();
$t3 = new Ticket();
echo $t1->number, ' ', $t3->number, "\n";   // in ra: 1 3
echo Ticket::issuedCount(), "\n";        // in ra: 3

try {
    Ticket::broken();
} catch (Error $e) {
    echo $e->getMessage(), "\n";         // in ra: Using $this when not in object context
}
```

```
           class Ticket
   ┌──────────────────────────────┐
   │ static $issued = 3           │  ← một ô nhớ duy nhất, gắn với class
   │ static issuedCount()         │
   └──────────────────────────────┘
      ▲            ▲            ▲        (mọi object cùng nhìn thấy $issued)
  object #1     object #2     object #3
  number = 1    number = 2    number = 3   ← mỗi object một ô riêng
```

Quy tắc truy cập:

| Thứ cần dùng | Từ bên ngoài | Từ bên trong class |
|---|---|---|
| Static property | `Ticket::$issued` | `self::$issued`, `static::$issued` |
| Static method | `Ticket::issuedCount()` | `self::issuedCount()`, `static::issuedCount()` |
| Property thường | `$t1->number` | `$this->number` |

- Tên class đặt trong biến cũng dùng được: `$cls = 'Ticket'; $cls::issuedCount();`.
- ⚠️ Static property không đọc được bằng `->`: viết `$this->issued` trong class (hoặc `$obj->x` với
  một static property `public` từ bên ngoài) thì PHP phát `Notice: Accessing static property ... as
  non static` kèm `Warning: Undefined property`, và trả `null`. (Từ bên ngoài, static property
  `private` như `$issued` thì bị chặn trước bởi `Error: Cannot access private property`.)
- Static method thì gọi qua object được (`$t1->issuedCount()`, `$t1::issuedCount()`), nhưng đừng
  làm vậy: người đọc sẽ tưởng method dùng dữ liệu của `$t1`.
- Static method không có `$this` (dùng thì `Error: Using $this when not in object context`). Ngược
  lại, method thường gọi được static method và đọc được static property.
- Gọi method không static theo kiểu `Ticket::method()` thì ném `Error` (mục 3.2).

### 6.2 Toán tử `::` và ba từ khoá `self`, `parent`, `static`

`::` (tên chính thức *Scope Resolution Operator*; manual còn gọi là *Paamayim Nekudotayim*, tiếng
Hebrew nghĩa là "hai dấu hai chấm", cái tên đội Zend đặt từ thời PHP 3) dùng để truy cập thành viên
gắn với class: hằng class, static property, static method, và gọi phiên bản method của class cha.

Bên trong class, thay vì gõ tên class, dùng ba từ khoá:

| Từ khoá | Chỉ class nào | Xác định lúc nào |
|---|---|---|
| `self` | Class chứa dòng code đang viết | Lúc viết code (cố định) |
| `parent` | Class cha của class chứa dòng code | Lúc viết code (cố định) |
| `static` | Class thực sự được gọi lúc chạy (có thể là class con) | Lúc chạy |

```php
<?php
declare(strict_types=1);

class ParentA
{
    public static function create(): static { return new static(); }
    public static function createSelf(): self { return new self(); }
    public static function who(): string { return 'ParentA'; }
    public static function test(): string { return self::who() . ' / ' . static::who(); }
}

class ChildB extends ParentA
{
    public static function who(): string { return 'ChildB'; }
    public static function parentWho(): string { return parent::who(); }
}

echo get_class(ChildB::create()), "\n";      // in ra: ChildB    (new static: class được gọi)
echo get_class(ChildB::createSelf()), "\n";  // in ra: ParentA   (new self: class viết code)
echo ChildB::test(), "\n";                   // in ra: ParentA / ChildB
echo ChildB::parentWho(), "\n";              // in ra: ParentA
```

Cơ chế `static::` có tên là *late static binding* ("gắn class muộn", tức lúc chạy). Eloquent dựa vào
nó: `User::query()` được viết trong class `Model` nhưng tạo query cho `User` nhờ `new static`. Chi
tiết (lời gọi chuyển tiếp, vì sao `new static` nguy hiểm khi class con đổi constructor) ở
[Chương 10](10-oop-nang-cao.md). Trong chương này chỉ cần nhớ: `self` là "class này", `static` là
"class được gọi".

### 6.3 Static và kế thừa: ô nhớ dùng chung

⚠️ Static property khai báo ở class cha được class con **dùng chung cùng một ô nhớ**, trừ khi class
con khai báo lại property đó:

```php
<?php
declare(strict_types=1);

class Model
{
    protected static int $created = 0;

    public function __construct()
    {
        static::$created++;            // static::: ô nhớ của class được new
    }

    public static function created(): int
    {
        return static::$created;
    }
}

class User extends Model {}            // không khai báo lại: DÙNG CHUNG ô nhớ với Model
class Post extends Model
{
    protected static int $created = 0; // khai báo lại: Post có ô nhớ riêng
}

new User();
new User();
new Post();
new Model();

echo Model::created(), ' ', User::created(), ' ', Post::created(), "\n";   // in ra: 3 3 1
```

Người viết có lẽ muốn "mỗi model đếm riêng", nhưng `User` không khai báo lại nên hai lần `new User()`
cộng vào bộ đếm của `Model`. Muốn tách thì class con khai báo lại, hoặc dùng array khoá theo tên class
(`self::$created[static::class]`).

Biến `static` bên trong method ([Chương 08](08-ham.md)) cũng theo quy tắc này từ PHP 8.1: method
kế thừa (không override) dùng chung biến `static` với method của cha. Trước 8.1, class con có bản riêng.

### 6.4 Ứng dụng tốt: named constructor

PHP chỉ có một constructor mỗi class (mục 4.1). Khi object tạo được từ nhiều dạng đầu vào, cách được
manual khuyên dùng là *static creation method*, hay gọi là *named constructor*: các static method có
tên nói rõ ý nghĩa, bên trong gọi `new`. Kết hợp với constructor `private` để buộc mọi người đi qua
chúng:

```php
<?php
declare(strict_types=1);

class Temperature
{
    private function __construct(private float $celsius) {}   // bên ngoài không new trực tiếp được

    public static function fromCelsius(float $c): self
    {
        return new self($c);
    }

    public static function fromFahrenheit(float $f): self
    {
        return new self(($f - 32) * 5 / 9);
    }

    public function celsius(): float
    {
        return $this->celsius;
    }
}

$a = Temperature::fromCelsius(100);
$b = Temperature::fromFahrenheit(212);
var_dump($a->celsius(), $b->celsius());   // in ra 2 dòng: float(100), float(100)

try {
    new Temperature(5);
} catch (Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Call to private Temperature::__construct() from global scope
}
```

So với `new Temperature(212)`, lời gọi `Temperature::fromFahrenheit(212)` không thể bị hiểu nhầm đơn
vị. Bạn sẽ gặp kiểu này khắp nơi: `DateTimeImmutable::createFromFormat()`, `Carbon::parse()`,
`Request::create()` trong Laravel.

### 6.5 Khi nào không nên dùng static

Static property về bản chất là biến toàn cục đội lốt class: ai cũng đọc ghi được (nếu public), sống
suốt tiến trình. Hệ quả:

- ⚠️ Khó test: giá trị test trước để lại ảnh hưởng test sau, phải nhớ reset.
- ⚠️ Rò rỉ dữ liệu giữa các request trong tiến trình sống lâu. Với PHP-FPM thông thường, mỗi request
  bắt đầu lại từ đầu nên static được làm mới. Nhưng với Laravel Octane hay queue worker, một tiến trình
  phục vụ nhiều request/job liên tiếp: lưu "user hiện tại" vào static property là user B có thể thấy dữ
  liệu của user A ([Chương 18](18-fpm-nginx-opcache.md), [Chương 30](30-laravel-testing-octane-deploy.md)).
- ⚠️ Static method gắn cứng tên class vào chỗ gọi (`Mailer::send()`), không thay bằng bản giả khi test
  được. Code có dependency (DB, HTTP, mail) nên là method thường của một object được truyền vào
  (*dependency injection*, [Chương 26](26-laravel-container-provider-facade.md)). Facade của Laravel
  (`Cache::get()`) trông như static nhưng thực ra chuyển lời gọi tới một object trong container, chính
  để giữ được khả năng thay thế đó.

Static hợp lý cho: named constructor, hàm thuần tuý không có dependency (tính toán, định dạng), hằng
và bộ đếm/bộ nhớ đệm nhỏ mà bạn hiểu rõ vòng đời.

## 7. Hằng class (class constant)

### 7.1 Khai báo và truy cập

*Hằng class* là giá trị cố định gắn với class, khai báo bằng `const` bên trong class. Giống hằng toàn
cục ([Chương 03](03-cu-phap-bien-hang.md)), giá trị phải là biểu thức hằng và không đổi được lúc chạy;
khác ở chỗ nó nằm trong "không gian" của class nên không đụng tên với hằng khác, và có visibility.

```php
<?php
declare(strict_types=1);

class Order
{
    const MAX_ITEMS = 50;                       // không ghi visibility: public
    public const VAT_PERCENT = 10;
    protected const PREFIX = 'ORD';
    private const SECRET_SALT = 'x9';
    const LIMITS = ['min' => 1, 'max' => self::MAX_ITEMS];   // dùng được hằng khác trong biểu thức

    public function code(int $id): string
    {
        return self::PREFIX . '-' . $id;        // bên trong class: self::TÊN, không có dấu $
    }
}

echo Order::MAX_ITEMS, "\n";        // in ra: 50
echo Order::LIMITS['max'], "\n";    // in ra: 50
$o = new Order();
echo $o::VAT_PERCENT, "\n";         // in ra: 10   (qua object cũng được)
echo $o->code(7), "\n";             // in ra: ORD-7
$cls = 'Order';
echo $cls::MAX_ITEMS, "\n";         // in ra: 50   (tên class trong biến)

try {
    echo Order::SECRET_SALT;
} catch (Error $e) {
    echo $e->getMessage(), "\n";    // in ra: Cannot access private constant Order::SECRET_SALT
}
```

- Hằng class được cấp phát một lần cho mỗi class, không phải mỗi object.
- Quy ước (PSR-1): tên viết HOA, nối bằng `_`.
- Visibility cho hằng có từ PHP 7.1.
- Truy cập: `TênClass::HẰNG`, `self::HẰNG`, `static::HẰNG`, `parent::HẰNG`, `$obj::HẰNG`.

### 7.2 Hằng và kế thừa: `self::` hay `static::`

Class con được định nghĩa lại (override) hằng của cha. Đây là chỗ sự khác nhau giữa `self` và
`static` (mục 6.2) gây lỗi thật:

```php
<?php
declare(strict_types=1);

class Model
{
    const TABLE = 'models';

    public function tableSelf(): string   { return self::TABLE; }
    public function tableStatic(): string { return static::TABLE; }
}

class User extends Model
{
    const TABLE = 'users';                 // class con định nghĩa lại hằng
}

$u = new User();
echo $u->tableSelf(), "\n";     // in ra: models   (self = Model, nơi viết code)
echo $u->tableStatic(), "\n";   // in ra: users    (static = User, class của object)
```

⚠️ Khi viết class cha với ý định "class con sẽ đặt giá trị riêng cho hằng này", phải đọc bằng
`static::`. Dùng `self::` thì class con đổi hằng cũng vô ích.

Muốn cấm class con định nghĩa lại một hằng, đánh dấu `final` (PHP 8.1):

```php
class Model
{
    final public const VERSION = 2;
}
class Post extends Model
{
    public const VERSION = 3;
}
// Fatal error: Post::VERSION cannot override final constant Model::VERSION
```

### 7.3 Hằng có kiểu (PHP 8.3)

Trước 8.3, hằng class không khai báo được kiểu. Class cha đặt `const TABLE = 'models'` (chuỗi), class
con vẫn override thành `const TABLE = 123` mà không ai báo gì, và code của cha dùng `static::TABLE`
như chuỗi sẽ hỏng ở nơi xa. Từ 8.3, hằng của class, interface, trait và enum khai báo kiểu được:

```php
<?php
declare(strict_types=1);

class Model
{
    public const string TABLE = 'models';
    public const int PER_PAGE = 15;
    public const float RATE = 1;          // int cho hằng float: ngoại lệ duy nhất được chấp nhận
    public const ?array CASTS = null;
}

class User extends Model
{
    public const string TABLE = 'users';  // đổi giá trị: được, vẫn là string
}

var_dump(User::TABLE, Model::RATE);       // in ra 2 dòng: string(5) "users", float(1)
```

Các lỗi được bắt ngay lúc compile:

```php
class Bad
{
    public const string TABLE = 1;
}
// Fatal error: Cannot use int as value for class constant Bad::TABLE of type string

class Post extends Model
{
    public const TABLE = 123;            // bỏ kiểu, hoặc khai báo const int TABLE = 123
}
// Fatal error: Type of Post::TABLE must be compatible with Model::TABLE of type string
```

- Hỗ trợ mọi kiểu trừ `void`, `never`, `callable` (gồm cả union, nullable, `mixed`, tên enum).
- Kiểm tra giá trị luôn theo kiểu chặt, không phụ thuộc `strict_types` (trừ int sang float).
- Khi override, class con phải khai báo kiểu và kiểu đó chỉ được hẹp hơn hoặc bằng của cha (cha
  `mixed`, con `int` được; ngược lại thì không). Lý do: hằng chỉ để đọc, nên người đọc
  `Model::TABLE` vẫn nhận được thứ họ mong đợi.
- Hằng `private` của cha không bị ràng buộc: class con không thấy nó, nên khai báo hằng cùng tên với
  kiểu khác cũng được.
- ⚠️ Cú pháp `const string X` là lỗi parse ở PHP 8.2 trở xuống: cả file không chạy. Thư viện còn hỗ trợ
  8.2 thì chưa dùng được.

### 7.4 Lấy hằng theo tên động (PHP 8.3) và `::class`

Khi tên hằng nằm trong một biến (đọc từ input, từ config), PHP 8.3 cho viết `TênClass::{$tên}`. Bản
cũ hơn phải dùng hàm `constant()`:

```php
<?php
declare(strict_types=1);

class Status
{
    public const string PENDING = 'pending';
    public const string PAID = 'paid';
}

$name = 'PAID';
echo Status::{$name}, "\n";                          // in ra: paid   (PHP 8.3+)
echo constant(Status::class . '::' . $name), "\n";   // in ra: paid   (cách cũ)

try {
    echo Status::{'REFUNDED'};
} catch (Error $e) {
    echo $e->getMessage(), "\n";                     // in ra: Undefined constant Status::REFUNDED
}
```

`TênClass::class` (mục 1.5) trông giống hằng nhưng là cú pháp đặc biệt, không phải hằng bạn khai báo:
nó được thay bằng tên đầy đủ của class ngay lúc compile.

Một nhóm hằng cùng loại như `Status::PENDING`, `Status::PAID` là cách làm trước PHP 8.1. Hằng chỉ là
chuỗi nên hàm nhận `string $status` vẫn chấp nhận `'abc'`. PHP 8.1 có *enum*, một kiểu thực sự mà
giá trị chỉ có thể là một trong các case đã khai báo; đó là lựa chọn tốt hơn cho tập giá trị cố định
([Chương 10](10-oop-nang-cao.md)).

## 8. Kế thừa (inheritance)

### 8.1 `extends`: class con nhận gì từ class cha

*Kế thừa* cho phép một class mới (*class con*, *child class*, *subclass*) được xây trên một class có
sẵn (*class cha*, *parent class*, *base class*) bằng từ khoá `extends`. Class con:

- nhận lại mọi method, property và hằng `public`/`protected` của cha, dùng được như của chính nó;
- thêm được thành viên mới;
- *override* (ghi đè) được method, property và hằng của cha bằng cách khai báo lại cùng tên.

Quan hệ kế thừa nên đọc được thành câu "X là một Y" (*is-a*): `PercentDiscount` là một
`Discount`. Vì vậy ở mọi nơi cần một `Discount`, đưa vào một `PercentDiscount` đều hợp lệ:

```php
<?php
declare(strict_types=1);

class Discount
{
    public function __construct(protected string $code) {}

    public function apply(int $amount): int
    {
        return $amount;                          // mặc định: không giảm
    }

    public function describe(): string
    {
        return "Mã {$this->code}";
    }

    public function summary(int $amount): string
    {
        // $this->apply() chạy bản của class THẬT của object, không nhất thiết là bản viết ở đây
        return $this->describe() . ': ' . $amount . ' -> ' . $this->apply($amount);
    }
}

class PercentDiscount extends Discount
{
    public function __construct(string $code, private int $percent)
    {
        parent::__construct($code);              // phải tự gọi constructor của cha (mục 8.4)
    }

    public function apply(int $amount): int      // override
    {
        return $amount - intdiv($amount * $this->percent, 100);
    }

    public function describe(): string           // override, có dùng lại bản của cha
    {
        return parent::describe() . " (giảm {$this->percent}%)";
    }
}

class FixedDiscount extends Discount
{
    public function __construct(string $code, private int $value)
    {
        parent::__construct($code);
    }

    public function apply(int $amount): int
    {
        return max(0, $amount - $this->value);
    }
}

function checkout(int $amount, Discount $discount): string   // chỉ biết tới Discount
{
    return $discount->summary($amount);
}

echo checkout(200000, new Discount('NONE')), "\n";
echo checkout(200000, new PercentDiscount('SALE10', 10)), "\n";
echo checkout(200000, new FixedDiscount('BOT50K', 50000)), "\n";
// in ra:
// Mã NONE: 200000 -> 200000
// Mã SALE10 (giảm 10%): 200000 -> 180000
// Mã BOT50K: 200000 -> 150000
```

Hai điều quan trọng trong ví dụ:

1. Đa hình (*polymorphism*): `checkout()` chỉ biết kiểu `Discount`, nhưng mỗi object chạy
   `apply()` của class thật của nó. Thêm loại giảm giá mới chỉ cần viết class mới, không sửa
   `checkout()`.
2. Method được chọn lúc chạy theo object (*dynamic dispatch*): `summary()` viết ở `Discount`, gọi
   `$this->apply()`; khi `$this` là `PercentDiscount` thì bản của `PercentDiscount` chạy. Đây là nền
   tảng của mẫu *template method* (mục 9.2).

```
checkout(200000, $d)   với $d là PercentDiscount
   └─ $d->summary()        → tìm trong PercentDiscount: không có → lấy của Discount
        ├─ $this->describe() → tìm trong PercentDiscount: CÓ → chạy bản con
        │     └─ parent::describe() → chạy bản của Discount
        └─ $this->apply()    → tìm trong PercentDiscount: CÓ → chạy bản con
```

Giới hạn: PHP chỉ có kế thừa đơn (*single inheritance*), mỗi class có tối đa một class cha.
`class B extends A, C` là lỗi cú pháp. Muốn một class "thuộc" nhiều loại thì dùng interface (mục 10);
muốn dùng chung code từ nhiều nguồn thì dùng trait (mục 11) hoặc composition.

### 8.2 Override và `parent::`

- Override method: khai báo method cùng tên ở class con. Gọi trên object con thì bản của con chạy, kể
  cả khi lời gọi xuất phát từ code của cha (`$this->apply()` ở trên).
- `parent::tênMethod(...)` gọi bản của cha, vẫn với `$this` hiện tại. PHP không tự gọi bản của
  cha; class con override rồi thì tự quyết định có gọi `parent::` hay không.
- Override property: class con khai báo lại property `public`/`protected` để đổi giá trị mặc định
  hoặc nới visibility (`protected` thành `public`). Kiểu thì phải giữ nguyên (lỗi `Type of B::$x
  must be int (as in class A)`), và không được thu hẹp visibility. Không đổi được giữa property thường
  và `static`, hay giữa thường và `readonly`.

### 8.3 Quy tắc tương thích chữ ký (signature compatibility)

Khi override method, chữ ký (tham số, kiểu, visibility) của bản con phải tương thích với bản cha.
Lý do nằm ở ý tưởng của mục 8.1: code viết cho `Discount` phải chạy đúng khi nhận một
`PercentDiscount`. Nguyên tắc này có tên *Liskov Substitution Principle* (LSP, nguyên lý thay thế
Liskov): object của class con phải thay được cho object của class cha mà không làm hỏng chương trình.

Áp vào chữ ký, ta có các quy tắc (kiểm tra lúc nạp class; vi phạm là Fatal error từ PHP 8.0, trước
đó một số trường hợp chỉ là warning):

| Thay đổi ở class con | Được không | Vì sao |
|---|---|---|
| Thêm tham số tùy chọn ở cuối | Được | Lời gọi cũ vẫn hợp lệ |
| Biến tham số bắt buộc thành tùy chọn | Được | Lời gọi cũ vẫn hợp lệ |
| Thêm tham số bắt buộc | Không | Lời gọi cũ thiếu đối số |
| Bỏ tham số, hoặc biến tùy chọn thành bắt buộc | Không | Lời gọi cũ không còn hợp lệ |
| Kiểu tham số rộng hơn (`int` thành `int\|string`, hoặc bỏ kiểu) | Được | Nhận được mọi thứ cha nhận (*contravariance*) |
| Kiểu tham số hẹp hơn (`int\|string` thành `int`) | Không | Lời gọi truyền `string` theo hợp đồng của cha sẽ hỏng |
| Kiểu trả về hẹp hơn (`?string` thành `string`, `Animal` thành `Dog`) | Được | Người gọi vẫn nhận thứ họ mong đợi (*covariance*) |
| Kiểu trả về rộng hơn (`string` thành `?string`), hoặc bỏ kiểu trả về cha đã khai báo | Không | Người gọi có thể nhận thứ họ không lường trước |
| Visibility rộng hơn (`protected` thành `public`) | Được | |
| Visibility hẹp hơn (`public` thành `protected`) | Không | Code bên ngoài đang gọi được sẽ không gọi được nữa |
| Đổi method thường thành `static` hoặc ngược lại | Không | |

Thông báo lỗi điển hình:

```
Fatal error: Declaration of B::f(int $x): void must be compatible with A::f(int $x = 5): void
Fatal error: Access level to B::f() must be public (as in class A)
Fatal error: Cannot make non static method A::f() static in class B
```

Hai ngoại lệ: constructor và method `private` không bị kiểm tra chữ ký (constructor của con có
thể nhận tham số hoàn toàn khác, thậm chí thu hẹp visibility thành `private`). Riêng constructor
được khai báo `abstract` ở class cha hoặc khai báo trong interface thì vẫn bị kiểm tra như method
thường.

- ⚠️ Đổi tên tham số khi override không phải lỗi chữ ký, nhưng ai gọi bằng named argument theo tên
  của cha (`$obj->f(foo: 1)`) sẽ nhận `Error: Unknown named parameter $foo` khi object là class con.
  Giữ nguyên tên tham số khi override.
- ⚠️ Từ PHP 8.1, method của class và interface có sẵn (built-in) khai báo kiểu trả về "tạm thời"
  (*tentative return type*). Override hoặc implement chúng mà không ghi kiểu trả về tương thích thì
  phát `Deprecated`, ví dụ `class C implements Countable { public function count() {...} }` nhận
  "Return type of C::count() should either be compatible with Countable::count(): int". Cách sửa: ghi
  `: int`. Attribute `#[\ReturnTypeWillChange]` chỉ để tạm tắt cảnh báo cho thư viện cần hỗ trợ PHP cũ.

### 8.4 Constructor trong kế thừa

- Class con không khai báo constructor thì dùng constructor của cha (như mọi method khác). Nếu
  constructor đó là `private` thì code bên ngoài cũng không `new` được class con (`Error: Call to
  private ...::__construct()`).
- Class con có constructor riêng thì constructor của cha **không tự chạy**. Quên
  `parent::__construct()` là lỗi rất hay gặp:

```php
<?php
declare(strict_types=1);

class Notifier
{
    protected array $channels;

    public function __construct(string ...$channels)
    {
        $this->channels = $channels;
    }

    public function channels(): string
    {
        return implode(',', $this->channels);
    }
}

class MailNotifier extends Notifier {}       // không có constructor riêng: dùng của cha

class SlackNotifier extends Notifier
{
    public function __construct(private string $webhook)
    {
        // quên parent::__construct(...)
    }
}

class GoodSlackNotifier extends Notifier
{
    public function __construct(private string $webhook)
    {
        parent::__construct('slack');        // gọi constructor của cha
    }
}

echo (new MailNotifier('mail', 'sms'))->channels(), "\n";                     // in ra: mail,sms
echo (new GoodSlackNotifier('https://hooks.example/abc'))->channels(), "\n";  // in ra: slack

try {
    echo (new SlackNotifier('https://hooks.example/abc'))->channels(), "\n";
} catch (Error $e) {
    echo $e->getMessage(), "\n";
}
// in ra: Typed property Notifier::$channels must not be accessed before initialization
```

Nhờ typed property, lỗi lộ ra ngay ở lần đọc đầu tiên (mục 2.3). Với property không có kiểu, nó im
lặng là `null` và lỗi xuất hiện ở đâu đó xa hơn.

### 8.5 Method `private` không bị override

Method `private` của cha vô hình với class con (mục 5.4). Class con khai báo method `private` cùng tên
thì đó là một method mới, độc lập. Code trong class cha gọi `$this->tên()` vẫn chạy bản của cha:

```php
<?php
declare(strict_types=1);

class Bar
{
    public function test(): void
    {
        $this->testPrivate();
        $this->testPublic();
    }

    public function testPublic(): void
    {
        echo "Bar::testPublic\n";
    }

    private function testPrivate(): void
    {
        echo "Bar::testPrivate\n";
    }
}

class Foo extends Bar
{
    public function testPublic(): void
    {
        echo "Foo::testPublic\n";
    }

    private function testPrivate(): void      // method MỚI, không override Bar::testPrivate
    {
        echo "Foo::testPrivate\n";
    }
}

(new Foo())->test();
// in ra:
// Bar::testPrivate
// Foo::testPublic
```

Từ PHP 8.0, method `private` của cha không áp đặt quy tắc kế thừa nào lên class con (chữ ký, `final`,
`static` tự do), trừ một trường hợp: constructor `private final`. Ghi `final private` cho method thường
thì PHP phát `Warning: Private methods cannot be final as they are never overridden by other classes`.

### 8.6 `final`: cấm kế thừa hoặc cấm override

```php
final class Money {}
class MyMoney extends Money {}
// Fatal error: Class MyMoney cannot extend final class Money

class Discount
{
    final public function code(): string { return 'X'; }
}
class Hacked extends Discount
{
    public function code(): string { return 'Y'; }
}
// Fatal error: Cannot override final method Discount::code()
```

| Đặt `final` lên | Ý nghĩa | Từ |
|---|---|---|
| Class | Không class nào được `extends` | PHP 5 |
| Method | Class con không được override | PHP 5 |
| Hằng class | Class con không được định nghĩa lại (mục 7.2) | PHP 8.1 |
| Property | Class con không được khai báo lại ([Chương 10](10-oop-nang-cao.md)) | PHP 8.4 |

Vì sao nên dùng `final`? Mỗi class mở cho kế thừa là thêm một lời hứa: class con có thể override bất
kỳ method `public`/`protected` nào và phụ thuộc vào cách các method đó gọi nhau bên trong. Sửa class
cha sau này dễ làm vỡ class con mà bạn không biết tới (vấn đề *fragile base class*, lớp cơ sở mỏng
manh). Đánh dấu `final` nói rõ "class này không thiết kế để kế thừa", và cho phép bạn sửa bên trong
thoải mái. Nhiều codebase hiện đại mặc định viết `final class` cho service và value object, chỉ bỏ
`final` khi thật sự thiết kế cho kế thừa.

⚠️ Đánh đổi: PHPUnit không tạo được *mock* (object giả để test) cho class `final`. Cách làm thông
thường là để class `final` implement một interface (mục 10) và mock interface đó
([Chương 21](21-chat-luong-code.md)).

Một công cụ liên quan: attribute `#[\Override]` (PHP 8.3) đặt trước method để khẳng định "method này
override method của cha hoặc interface". Nếu không có method nào như vậy (gõ sai tên, hoặc cha đã đổi
tên method), PHP báo Fatal error ngay lúc nạp class:

```php
class PercentDiscount extends Discount
{
    #[\Override]
    public function aply(int $amount): int   // gõ sai tên apply
    {
        return intdiv($amount * 90, 100);
    }
}
// PHP 8.3+: Fatal error: PercentDiscount::aply() has #[\Override] attribute, but no matching parent method exists
// PHP 8.2 trở xuống: attribute bị bỏ qua, method mồ côi chạy im lặng
```

Chi tiết về attribute ở [Chương 10](10-oop-nang-cao.md).

### 8.7 Khi nào không nên kế thừa

Kế thừa là công cụ mạnh nhưng ràng buộc chặt: class con phụ thuộc vào chi tiết bên trong của cha, và
mỗi class chỉ có một cha. Dấu hiệu dùng sai:

- Câu "X là một Y" nghe gượng (`class OrderService extends Database` chỉ để gọi được `query()`).
- Class con override method của cha để vô hiệu hoá nó (ném lỗi "không hỗ trợ"): vi phạm LSP.
- Cây kế thừa sâu nhiều tầng, muốn hiểu một method phải lần qua bốn năm class.

Thay vào đó thường dùng *composition* (kết hợp): class giữ một object khác trong property và gọi nó
(`OrderService` nhận một `Database` qua constructor). Nguyên tắc "ưu tiên composition hơn kế thừa"
được bàn ở [Chương 10](10-oop-nang-cao.md).

## 9. Abstract class

### 9.1 Class "dở dang" có chủ đích

Ở mục 8.1, class cha `Discount` vẫn tạo object được và có một `apply()` mặc định "không giảm". Nhưng
nhiều khi class cha chỉ là khung chung, tự nó không có nghĩa: "một trình xuất báo cáo" chung chung
thì xuất ra định dạng gì? *Abstract class* (lớp trừu tượng) diễn đạt đúng ý đó:

- Khai báo bằng `abstract class`. Không `new` được: `Error: Cannot instantiate abstract class`.
- Chứa được *abstract method*: chỉ có chữ ký, không có thân, kết thúc bằng `;`. Class con (không
  abstract) bắt buộc phải viết thân cho mọi abstract method.
- Ngoài ra vẫn là class bình thường: có property, constructor, method có thân, hằng.

### 9.2 Mẫu template method

Cách dùng kinh điển của abstract class: class cha viết sẵn trình tự xử lý, để trống vài bước
cho class con điền vào. Mẫu thiết kế này tên là *template method*.

```php
<?php
declare(strict_types=1);

abstract class Exporter
{
    // Khung xử lý chung. final: class con không được đổi thứ tự các bước
    final public function export(array $rows): string
    {
        $out = $this->header(array_keys($rows[0] ?? []));
        foreach ($rows as $row) {
            $out .= $this->row($row);
        }
        return $out . $this->footer(count($rows));
    }

    abstract protected function header(array $columns): string;   // class con BẮT BUỘC viết
    abstract protected function row(array $row): string;

    protected function footer(int $count): string                  // có sẵn, class con override nếu muốn
    {
        return '';
    }
}

final class CsvExporter extends Exporter
{
    protected function header(array $columns): string
    {
        return implode(',', $columns) . "\n";
    }

    protected function row(array $row): string
    {
        return implode(',', $row) . "\n";
    }
}

final class MarkdownExporter extends Exporter
{
    protected function header(array $columns): string
    {
        return '| ' . implode(' | ', $columns) . " |\n|" . str_repeat('---|', count($columns)) . "\n";
    }

    protected function row(array $row): string
    {
        return '| ' . implode(' | ', $row) . " |\n";
    }

    protected function footer(int $count): string
    {
        return "Tổng: {$count} dòng\n";
    }
}

$rows = [['id' => 1, 'name' => 'An'], ['id' => 2, 'name' => 'Bình']];
echo (new CsvExporter())->export($rows);
echo (new MarkdownExporter())->export($rows);
// in ra:
// id,name
// 1,An
// 2,Bình
// | id | name |
// |---|---|
// | 1 | An |
// | 2 | Bình |
// Tổng: 2 dòng

try {
    new Exporter();
} catch (Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Cannot instantiate abstract class Exporter
}
```

Phân vai rõ ràng: `export()` là `final` vì trình tự là phần cha giữ; `header()`, `row()` là abstract vì
mỗi định dạng phải tự viết; `footer()` có bản mặc định, class con override khi cần (gọi là *hook
method*). Các bước để `protected` vì chúng là chi tiết bên trong, bên ngoài chỉ cần gọi `export()`.

### 9.3 Các quy tắc

| Quy tắc | Vi phạm thì (thông báo PHP 8.5, bản cũ diễn đạt hơi khác) |
|---|---|
| Class có abstract method thì chính nó phải `abstract` | `Class A declares abstract method f() and must therefore be declared abstract` |
| Class con không abstract phải viết đủ mọi abstract method | `Class B contains 1 abstract method and must therefore be declared abstract or implement the remaining method (A::g)` |
| Abstract method không có thân | `Abstract function A::f() cannot contain body` |
| Abstract method chỉ là `public` hoặc `protected` | `Abstract function A::f() cannot be declared private` |
| Bản cài đặt ở class con tuân theo quy tắc chữ ký của mục 8.3 | `Declaration of ... must be compatible with ...` |

- Theo mục 8.3, bản cài đặt được nới: abstract `protected function f(int $x): string` có thể được
  viết thành `public function f(int|string $x, int $y = 0): string`.
- Một class abstract có thể không chứa abstract method nào; khi đó `abstract` chỉ để cấm `new` trực
  tiếp.
- Từ PHP 8.4, abstract class khai báo được cả *abstract property* (yêu cầu class con có property đọc
  được và/hoặc ghi được), cú pháp dựa trên property hooks ([Chương 10](10-oop-nang-cao.md)).

Khi nào chọn abstract class, khi nào chọn interface hay trait? Mục 11.7 so sánh cả ba, sau khi bạn
đã biết interface và trait.

## 10. Interface

### 10.1 Interface là một bản hợp đồng

*Interface* (giao diện) liệt kê những method `public` (và từ PHP 8.4, những property) mà một class
phải có, nhưng không nói chúng được cài đặt thế nào. Class cam kết tuân theo bằng `implements`.
Interface trả lời câu hỏi "object này làm được gì", còn class trả lời "nó làm như thế nào".

Manual nêu hai mục đích bổ sung cho nhau:

1. Thay thế lẫn nhau được: nhiều class khác nhau (nhiều cổng thanh toán, nhiều kiểu cache, nhiều
   driver database) cùng implement một interface, nên đổi class này sang class kia không phải sửa code
   đang dùng chúng.
2. Chỉ đòi đúng thứ cần: hàm nhận tham số kiểu interface chỉ quan tâm object "làm được X", không
   quan tâm object đó còn làm gì khác hay thuộc class nào.

### 10.2 Khai báo và implement

```php
<?php
declare(strict_types=1);

interface PaymentGateway
{
    // Chỉ có chữ ký: "ai muốn là một PaymentGateway thì phải có method này"
    public function charge(int $amount, string $orderId): string;   // trả về mã giao dịch
}

final class VnpayGateway implements PaymentGateway
{
    public function charge(int $amount, string $orderId): string
    {
        // Thực tế: gọi API của cổng thanh toán. Ở đây giả lập.
        return 'VNP-' . $orderId;
    }
}

final class FakeGateway implements PaymentGateway
{
    public array $charged = [];

    public function charge(int $amount, string $orderId): string
    {
        $this->charged[] = [$orderId, $amount];   // ghi lại để test kiểm tra
        return 'FAKE-' . $orderId;
    }
}

final class CheckoutService
{
    // Phụ thuộc vào interface, không phụ thuộc class cụ thể
    public function __construct(private PaymentGateway $gateway) {}

    public function pay(string $orderId, int $amount): string
    {
        if ($amount <= 0) {
            throw new InvalidArgumentException('Số tiền phải dương');
        }
        return $this->gateway->charge($amount, $orderId);
    }
}

$prod = new CheckoutService(new VnpayGateway());   // chạy thật
echo $prod->pay('A1', 150000), "\n";               // in ra: VNP-A1

$fake = new FakeGateway();
$test = new CheckoutService($fake);                // trong test: không gọi cổng thanh toán thật
echo $test->pay('A2', 99000), "\n";                // in ra: FAKE-A2
var_dump($fake->charged === [['A2', 99000]]);      // in ra: bool(true)
var_dump($fake instanceof PaymentGateway);         // in ra: bool(true)
```

`CheckoutService` không biết, cũng không cần biết đang dùng cổng nào. Đó là lý do mục 8.6 nói "class
`final` + interface": class cài đặt đóng kín, còn điểm thay thế nằm ở interface. Truyền dependency qua
constructor như thế này gọi là *dependency injection*; service container của Laravel tự động hoá việc
chọn class nào cho interface nào ([Chương 26](26-laravel-container-provider-facade.md)).

Quy tắc của interface:

| Quy tắc | Vi phạm thì (thông báo PHP 8.5, bản cũ diễn đạt hơi khác) |
|---|---|
| Method trong interface phải `public` | `Access type for interface method I::f() must be public` |
| Method trong interface không có thân | `Interface function I::f() cannot contain body` |
| Không có property thường (8.4+ chỉ có property kèm yêu cầu `get`/`set`, mục 10.5) | Fatal error |
| Không `new` được | `Error: Cannot instantiate interface I` |
| Class implement phải có đủ mọi method, đúng quy tắc chữ ký (mục 8.3), và để `public` | `Class C contains 1 abstract method and must therefore be declared abstract or implement the remaining method (I::f)` |
| Interface dùng chung "không gian tên" với class, trait, enum | Không được đặt trùng tên |

- Abstract class được phép implement interface mà chưa viết đủ method; class con cụ thể phải viết
  nốt.
- ⚠️ Giữ đúng tên tham số như trong interface. Đổi tên không phải lỗi chữ ký, nhưng người gọi
  dùng named argument theo tên trong interface sẽ gặp `Error` (giống mục 8.3).
- Interface có thể khai báo constructor, nhưng manual khuyên mạnh là không nên vì làm giảm tính linh
  hoạt: mọi class implement (và cả class con của chúng) bị buộc nhận đúng bộ tham số đó.
- Quy ước đặt tên: PSR dùng hậu tố `Interface` (`LoggerInterface`, `CacheInterface`); Laravel đặt
  interface trong namespace `Contracts` với tên không hậu tố (`Illuminate\Contracts\Cache\Repository`).
  Chọn một kiểu và giữ nhất quán.

### 10.3 Nhiều interface, interface kế thừa interface

Một class chỉ có một class cha nhưng implement được nhiều interface. Một interface `extends` được
nhiều interface khác:

```php
<?php
declare(strict_types=1);

interface HasId
{
    public function id(): int;
}

interface Timestamped
{
    public function createdAt(): string;
}

interface Entity extends HasId, Timestamped    // interface kế thừa nhiều interface
{
    public const string TABLE_PREFIX = 'app_';  // hằng trong interface (mục 10.4)
}

final class Invoice implements Entity, Countable   // class implement nhiều interface
{
    public function __construct(private int $id, private array $lines) {}

    public function id(): int { return $this->id; }
    public function createdAt(): string { return '2026-10-03'; }
    public function count(): int { return count($this->lines); }   // của Countable
}

$inv = new Invoice(7, ['bút', 'vở', 'thước']);
echo $inv->id(), ' ', $inv->createdAt(), ' ', count($inv), "\n";   // in ra: 7 2026-10-03 3
echo Invoice::TABLE_PREFIX, "\n";                                 // in ra: app_
var_dump($inv instanceof HasId, $inv instanceof Entity, $inv instanceof Countable);
// in ra 3 dòng: bool(true), bool(true), bool(true)
```

Nếu hai interface cùng khai báo một method trùng tên, class chỉ viết một method, và method đó phải
tương thích với chữ ký của cả hai (áp dụng covariance/contravariance như mục 8.3).

### 10.4 Hằng trong interface

Interface chứa được hằng, dùng như hằng class (`Entity::TABLE_PREFIX`, `Invoice::TABLE_PREFIX`).
Hằng interface luôn `public`.

- Từ PHP 8.1, class implement (hoặc interface con) được định nghĩa lại hằng của interface, trừ khi
  hằng đó là `final`. PHP 8.0 trở về trước thì không (Fatal error "Cannot inherit previously-inherited
  or override constant").
- Từ PHP 8.3, visibility của hằng khi định nghĩa lại được kiểm tra chặt: hằng interface là `public` nên
  class không được đổi thành `protected` (`Access level to B::B must be public (as in interface A)`).
  PHP 8.1 và 8.2 không kiểm tra điều này.

### 10.5 Property trong interface (PHP 8.4)

Trước PHP 8.4 interface chỉ có method; muốn đòi "object phải có tên" thì phải khai báo `getName()`. Từ
8.4, interface khai báo được property kèm yêu cầu đọc (`get`), ghi (`set`) hoặc cả hai. Yêu cầu chỉ áp
cho truy cập `public`. Class đáp ứng bằng nhiều cách: property `public` thường, property `readonly`
(chỉ với yêu cầu `get`), hoặc property hooks:

```php
<?php
declare(strict_types=1);

interface HasName
{
    public string $name { get; }          // class phải có property $name đọc được từ bên ngoài
}

final class Customer implements HasName
{
    public function __construct(public string $name) {}            // property thường: đạt
}

final class Product implements HasName
{
    public function __construct(public readonly string $name) {}   // readonly: đạt yêu cầu get
}

final class Employee implements HasName
{
    public function __construct(private string $first, private string $last) {}

    public string $name {                                            // property hook (Chương 10)
        get => $this->first . ' ' . $this->last;
    }
}

function greet(HasName $x): string
{
    return 'Xin chào ' . $x->name;
}

echo greet(new Customer('An')), "\n";             // in ra: Xin chào An
echo greet(new Product('Bút bi')), "\n";          // in ra: Xin chào Bút bi
echo greet(new Employee('Trần', 'Bình')), "\n";   // in ra: Xin chào Trần Bình
// PHP 8.3 trở xuống: Parse error ngay dòng khai báo property trong interface
```

Property `private` không đáp ứng được (`Access level to Bad::$name must be public`). Một property mà
interface đòi ghi được (`set`) thì không đáp ứng bằng `readonly`. Cú pháp hook và các chi tiết khác ở
[Chương 10](10-oop-nang-cao.md).

### 10.6 Một số interface có sẵn hay gặp

PHP định nghĩa sẵn nhiều interface; implement chúng thì object của bạn "cắm" được vào các tính năng của
ngôn ngữ:

| Interface | Method phải có | Được gì | Đọc thêm |
|---|---|---|---|
| `Countable` | `count(): int` | Gọi `count($obj)` | |
| `Stringable` | `__toString(): string` | Dùng object như chuỗi; PHP 8.0+ tự gắn interface này cho class có `__toString()` | [Chương 10](10-oop-nang-cao.md) |
| `JsonSerializable` | `jsonSerialize(): mixed` | Quyết định `json_encode($obj)` ra gì | [Chương 14](14-file-json-thoi-gian.md) |
| `IteratorAggregate` | `getIterator(): Traversable` | Duyệt object bằng `foreach` | [Chương 13](13-generator-iterator-spl.md) |
| `ArrayAccess` | `offsetExists`, `offsetGet`, `offsetSet`, `offsetUnset` | Dùng cú pháp `$obj['key']` | |
| `Throwable` | (không tự implement được) | Mọi thứ `throw` được; class của bạn phải `extends Exception` hoặc `Error` | [Chương 12](12-loi-exception.md) |

Nhắc lại cạm bẫy ở mục 8.3: method của `Countable`, `JsonSerializable`, `IteratorAggregate`,
`ArrayAccess` có kiểu trả về "tạm thời" từ PHP 8.1, nên khi implement hãy ghi đủ kiểu trả về như cột
thứ hai, nếu không sẽ nhận `Deprecated`. (`__toString()` là ngoại lệ: thiếu `: string` thì PHP tự thêm,
không cảnh báo; vẫn nên ghi rõ.)

## 11. Trait

### 11.1 Vấn đề: dùng chung code giữa các class không cùng họ

`Post` và `Product` không liên quan gì nhau, nhưng cả hai cần method `slug()` tạo chuỗi cho URL. Các
lựa chọn đã biết đều không ổn:

- Chép code sang cả hai class: sửa một chỗ quên chỗ kia.
- Tạo class cha chung `Sluggable` cho cả hai: sai quan hệ "là một", và dùng mất suất kế thừa duy nhất.
- Interface: chỉ đòi có `slug()`, không mang theo cài đặt nào.

*Trait* giải quyết đúng chỗ này: một khối method (và property, hằng) được chép vào class nào khai
báo `use TênTrait;`, như thể bạn tự gõ chúng vào class đó. Manual gọi đây là kết hợp hành vi "theo
chiều ngang" (*horizontal composition*): đưa thành viên vào class mà không cần quan hệ kế thừa. Trait không tạo
object được (`Error: Cannot instantiate trait`).

### 11.2 Khai báo và dùng trait

```php
<?php
declare(strict_types=1);

trait HasSlug
{
    abstract protected function slugSource(): string;   // class dùng trait PHẢI cung cấp method này

    public function slug(): string
    {
        $s = strtolower(trim($this->slugSource()));
        $s = preg_replace('/[^a-z0-9]+/', '-', $s);
        return trim($s, '-');
    }
}

trait Timestamps
{
    private ?string $createdAt = null;                  // trait mang theo cả property

    public function touch(string $now): void
    {
        $this->createdAt = $now;
    }

    public function createdAt(): ?string
    {
        return $this->createdAt;
    }
}

final class Post
{
    use HasSlug, Timestamps;              // một class dùng được nhiều trait

    public function __construct(private string $title) {}

    protected function slugSource(): string
    {
        return $this->title;
    }
}

final class Product                       // không liên quan gì tới Post
{
    use HasSlug;

    public function __construct(private string $name, private string $sku) {}

    protected function slugSource(): string
    {
        return $this->name . ' ' . $this->sku;
    }
}

$post = new Post('Hello PHP 8.5 World!');
$post->touch('2026-10-03');
echo $post->slug(), ' ', $post->createdAt(), "\n";      // in ra: hello-php-8-5-world 2026-10-03
echo (new Product('Ballpoint Pen', 'BP-01'))->slug(), "\n";   // in ra: ballpoint-pen-bp-01
```

(`slug()` ở đây chỉ xử lý chữ không dấu; chữ có dấu tiếng Việt cần chuyển về không dấu trước, xem
[Chương 05](05-chuoi.md).)

Vì trait được "chép vào" class, mọi thứ trong trait mang nghĩa của class dùng nó:

- `$this` là object của class đó; `self`, `static`, `parent` và `__CLASS__` chỉ class dùng trait (hoặc
  cha của nó). Hằng ma thuật `__TRAIT__` mới cho tên trait.
- Abstract method trong trait (mọi visibility, kể cả `private` từ PHP 8.0) là cách trait nói "tôi cần
  class cung cấp thứ này". Từ 8.0, chữ ký method mà class viết được kiểm tra với chữ ký abstract
  trong trait.
- Trait có thể `use` trait khác, gộp nhiều trait nhỏ thành trait lớn.

### 11.3 Thứ tự ưu tiên khi trùng tên method

Khi class, trait và class cha cùng có một method tên giống nhau:

```
method của chính class  >  method từ trait  >  method kế thừa từ class cha
```

```php
<?php
declare(strict_types=1);

class Base
{
    public function hello(): string { return 'Base'; }
    public function bye(): string { return 'Base bye'; }
}

trait Greets
{
    public function hello(): string
    {
        return 'Trait > ' . parent::hello();   // parent:: là cha của class DÙNG trait
    }

    public function bye(): string { return 'Trait bye'; }

    public function where(): string
    {
        return __CLASS__ . ' / ' . self::class . ' / ' . static::class . ' / ' . __TRAIT__;
    }
}

class Child extends Base
{
    use Greets;

    public function bye(): string { return 'Child bye'; }   // method của class thắng method của trait
}

class GrandChild extends Child {}

$c = new Child();
echo $c->hello(), "\n";                  // in ra: Trait > Base       (trait đè method của cha)
echo $c->bye(), "\n";                    // in ra: Child bye          (class đè trait)
echo $c->where(), "\n";                  // in ra: Child / Child / Child / Greets
echo (new GrandChild())->where(), "\n";  // in ra: Child / Child / GrandChild / Greets
```

PHP 8.5 đổi thời điểm gắn trait: trait được gắn vào class trước class cha (trước đây là sau).
Thứ tự ưu tiên method ở trên không đổi. Khác biệt lộ ra khi trait và class cha cùng khai báo một
property hoặc hằng trùng tên mà định nghĩa khác nhau: PHP 8.4 trở xuống báo Fatal error "define the
same property ... considered incompatible", PHP 8.5 lấy định nghĩa của trait.

### 11.4 Xung đột giữa hai trait: `insteadof` và `as`

Hai trait cùng có method trùng tên mà class dùng cả hai thì PHP báo lỗi ngay khi nạp class:

```
Fatal error: Trait method XinChao::greet has not been applied as Greeter::greet,
because of collision with Hello::greet
```

Bạn phải tự giải quyết trong khối `{}` sau `use`:

```php
<?php
declare(strict_types=1);

trait Hello
{
    public function greet(): string { return 'Hello'; }
}

trait XinChao
{
    public function greet(): string { return 'Xin chào'; }
}

final class Greeter
{
    use Hello, XinChao {
        Hello::greet insteadof XinChao;     // tên greet dùng bản của Hello
        XinChao::greet as greetVi;          // bản của XinChao vẫn gọi được qua tên khác
        Hello::greet as protected hi;       // thêm tên hi, kèm đổi visibility thành protected
    }

    public function both(): string
    {
        return $this->hi() . ' / ' . $this->greetVi();
    }
}

$g = new Greeter();
echo $g->greet(), "\n";     // in ra: Hello
echo $g->greetVi(), "\n";   // in ra: Xin chào
echo $g->both(), "\n";      // in ra: Hello / Xin chào

try {
    $g->hi();
} catch (Error $e) {
    echo $e->getMessage(), "\n";   // in ra: Call to protected method Greeter::hi() from global scope
}
```

- `A::m insteadof B;` chọn bản của `A` cho tên `m`, loại bản của `B`.
- `B::m as tênKhác;` thêm một tên gọi cho bản của `B`. ⚠️ `as` **không đổi tên**: nó thêm tên mới,
  tên cũ vẫn còn (và vẫn có thể xung đột nếu chưa `insteadof`).
- `m as protected;` chỉ đổi visibility; `m as private tênKhác;` vừa thêm tên vừa đặt visibility cho
  tên mới.
- `m as final;` (PHP 8.3) đánh dấu method lấy từ trait là `final` ở class này: class con không override
  được. PHP 8.2 trở xuống báo `Cannot use 'final' as method modifier`.

### 11.5 Static, property và hằng trong trait

**Static method và static property.** Trait khai báo được cả hai; mỗi class dùng trait có bản static
riêng (vì code được chép vào từng class). Có hai điểm phụ thuộc phiên bản:

```php
<?php
declare(strict_types=1);

trait Counts
{
    public static int $count = 0;

    public static function increment(): void
    {
        static::$count++;
    }
}

class Order { use Counts; }
class Invoice { use Counts; }                      // class khác dùng cùng trait: bản static riêng

class BaseRepo { use Counts; }
class UserRepo extends BaseRepo { use Counts; }    // cha và con CÙNG use trait

Order::increment();
Order::increment();
Invoice::increment();
echo Order::$count, ' ', Invoice::$count, "\n";    // in ra: 2 1

BaseRepo::increment();
echo BaseRepo::$count, ' ', UserRepo::$count, "\n";
// PHP 8.3+: in ra 1 0   (con có ô nhớ riêng)
// PHP 8.2:  in ra 1 1   (cha và con dùng chung ô nhớ)
```

- Từ PHP 8.3, class con `use` lại một trait có static property thì được ô nhớ riêng, giống như tự khai
  báo static property đó. Trước 8.3, cha và con dùng chung (giống quy tắc static thường ở mục 6.3).
- Từ PHP 8.1, gọi static method hay đọc static property thẳng trên trait (`Counts::increment()`)
  bị deprecated. Chỉ gọi qua class dùng trait.
- Biến `static` trong method của trait cũng riêng cho từng class dùng trait.

**Property.** Class dùng trait không được khai báo lại property cùng tên, trừ khi khai báo tương
thích hoàn toàn (cùng visibility, kiểu, `readonly`, giá trị khởi tạo). Khác một chút là Fatal error:

```php
trait T { public bool $flag = false; }
class A { use T; public bool $flag = false; }   // giống hệt: được
class B { use T; public bool $flag = true; }    // khác giá trị khởi tạo
// Fatal error: B and T define the same property ($flag) in the composition of B.
// However, the definition differs and is considered incompatible.
```

**Hằng** (PHP 8.2+): trait khai báo được hằng, truy cập qua class dùng trait (`Order::LIMIT`). Đọc
thẳng trên trait (`T::LIMIT`) là `Error: Cannot access trait constant T::LIMIT directly`. Class dùng
trait chỉ khai báo lại hằng cùng tên khi tương thích (cùng visibility, giá trị, `final`).

### 11.6 Trait không phải là kiểu

Đây là khác biệt cốt lõi với interface: trait chỉ là cơ chế chép code, không tạo ra kiểu dữ liệu.

```php
<?php
declare(strict_types=1);

trait HasSlug
{
    public function slug(): string { return 'slug'; }
}

class Post { use HasSlug; }
class Article extends Post {}

var_dump(new Post() instanceof HasSlug);   // in ra: bool(false)

function show(HasSlug $x): string          // khai báo được, nhưng không object nào thoả
{
    return $x->slug();
}

try {
    echo show(new Post());
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
}
// in ra: show(): Argument #1 ($x) must be of type HasSlug, Post given, called in ... on line ...

print_r(class_uses(new Post()));      // in ra: Array ( [HasSlug] => HasSlug )   (rút gọn)
print_r(class_uses(new Article()));   // in ra: Array ( )   KHÔNG tính trait của class cha
```

- Muốn kiểu thì dùng interface. Mẫu phổ biến: interface + trait cài đặt mặc định. Ví dụ PSR-3 có
  cặp `LoggerAwareInterface` (để type hint, `instanceof`) và `LoggerAwareTrait` (cài sẵn
  `setLogger()`); class `implements LoggerAwareInterface` và `use LoggerAwareTrait`.
- `class_uses()` chỉ trả trait mà class dùng trực tiếp, không tính trait của class cha hay trait
  lồng trong trait. Laravel có helper `class_uses_recursive()` cho việc đó.
- Laravel dùng trait rất nhiều: model dùng `SoftDeletes`, `HasFactory`, `Notifiable`; test dùng
  `RefreshDatabase` ([Chương 27](27-laravel-database-eloquent.md), [Chương 30](30-laravel-testing-octane-deploy.md)).

⚠️ Lạm dụng trait là một dạng kế thừa ngầm: method từ đâu tới, property nào của trait nào, trait nào
cần method của trait khác, đều khó lần theo. Trait cũng không thay bằng bản giả khi test được. Khi
trait bắt đầu cần gọi database, HTTP, config, hãy chuyển phần đó thành một class riêng và truyền vào
(composition, [Chương 10](10-oop-nang-cao.md)).

### 11.7 Chọn interface, abstract class hay trait

| | Interface | Abstract class | Trait |
|---|---|---|---|
| Là gì | Hợp đồng: method (8.4+: cả property) phải có | Class dở dang, có cả code chung và chỗ trống | Khối code được chép vào class |
| Có code cài đặt | Không | Có | Có |
| Có state (property mang giá trị) | Không (chỉ hằng; 8.4+ property chỉ là yêu cầu) | Có | Có |
| Tạo object được | Không | Không | Không |
| Là một kiểu (type hint, `instanceof`) | Có | Có | **Không** |
| Một class dùng được mấy cái | Nhiều (`implements A, B`) | Một (`extends`) | Nhiều (`use A, B`) |
| Dùng khi | Nhiều class không liên quan cùng "làm được X"; cần thay thế được khi test | Một họ class chia sẻ khung xử lý và state (template method) | Đoạn code nhỏ, không dependency, lặp ở nhiều class không cùng họ |

Gợi ý quyết định:

1. Cần kiểu để type hint và thay thế (thanh toán, cache, logger)? Bắt đầu bằng interface.
2. Nhiều class cài interface đó chia sẻ hẳn một khung xử lý và dữ liệu? Thêm một abstract
   class implement interface, để các class cụ thể kế thừa.
3. Chỉ cần dùng chung vài method tiện ích giữa các class không cùng họ? Trait, tốt nhất đi kèm
   một interface nếu nơi khác cần kiểm tra kiểu.
4. Phân vân? Thử composition: tách phần dùng chung thành một class riêng và truyền vào.

## 12. Object là handle: gán, truyền tham số và clone

### 12.1 Biến không chứa object, mà chứa handle

Với array, `$b = $a` cho ra một bản độc lập về ngữ nghĩa: sửa `$b` không ảnh hưởng `$a`
([Chương 06](06-mang.md)). Object thì khác hẳn. Biến không chứa chính object; nó chứa một *object
handle* (manual gọi là *object identifier*), một mã số để engine tìm tới object thật nằm ở chỗ khác.
Gán `$b = $a` chỉ copy **cái handle**, nên cả hai biến trỏ tới cùng một object:

```php
<?php
declare(strict_types=1);

class Cart
{
    public array $items = [];
}

// Array: gán là copy (về ngữ nghĩa)
$arr1 = ['bút'];
$arr2 = $arr1;
$arr2[] = 'vở';
echo count($arr1), ' ', count($arr2), "\n";        // in ra: 1 2

// Object: gán là copy cái handle, hai biến cùng trỏ MỘT object
$cart1 = new Cart();
$cart2 = $cart1;
$cart2->items[] = 'vở';
echo count($cart1->items), ' ', count($cart2->items), "\n";   // in ra: 1 1
var_dump($cart1 === $cart2);                                  // in ra: bool(true)
```

```
Array (giá trị)                         Object (handle)
$arr1 ──► ['bút']                       $cart1 ──┐
$arr2 ──► ['bút', 'vở']                          ├──► object #1 Cart { items: ['vở'] }
(hai bản riêng sau khi ghi)             $cart2 ──┘
                                        (mỗi biến giữ một bản copy của handle #1)
```

Số `#1` mà `var_dump` in ra và `spl_object_id($obj)` chính là định danh này. Bên trong engine, object
nằm trong một bảng gọi là *object store*, handle là chỉ số vào bảng đó
([Chương 19](19-ben-trong-engine.md)).

### 12.2 Truyền object vào hàm: "by handle", không phải "by reference"

Câu "trong PHP object được truyền theo tham chiếu" rất phổ biến, và manual có hẳn một trang để đính
chính rằng nó không hoàn toàn đúng. Object được truyền **theo giá trị** như mọi thứ khác, chỉ có
điều giá trị đó là một handle. Khác biệt lộ ra khi hàm gán lại tham số:

```php
<?php
declare(strict_types=1);

class Cart
{
    public array $items = [];
}

function addItem(Cart $c): void
{
    $c->items[] = 'sách';          // sửa object qua handle: người gọi THẤY
}

function replace(Cart $c): void
{
    $c = new Cart();               // gán handle mới cho biến cục bộ: người gọi KHÔNG thấy
    $c->items[] = 'bút';
}

function replaceByRef(Cart &$c): void
{
    $c = new Cart();               // tham chiếu &: đổi luôn biến của người gọi
}

$cart = new Cart();
$alias = $cart;

addItem($cart);
replace($cart);
print_r($cart->items);    // in ra: Array ( [0] => sách )   (rút gọn)

replaceByRef($cart);
print_r($cart->items);    // in ra: Array ( )               $cart giờ là object mới
print_r($alias->items);   // in ra: Array ( [0] => sách )   $alias vẫn giữ object cũ
```

| | Sửa property bên trong hàm | Gán tham số bằng object khác |
|---|---|---|
| `function f(Cart $c)` | Người gọi thấy (cùng object) | Người gọi không thấy (chỉ đổi biến cục bộ) |
| `function f(Cart &$c)` | Người gọi thấy | Người gọi thấy (biến của họ bị đổi) |

Nếu object thật sự truyền theo tham chiếu thì `replace()` đã đổi được `$cart`. Đối chiếu: Java giống
hệt PHP (biến kiểu object giữ một reference, và reference đó được truyền theo giá trị). Go thì khác:
struct được copy khi gán hay truyền; muốn chia sẻ phải dùng pointer `*Cart`. Handle của PHP gần
với pointer của Go hơn là với struct.

### 12.3 Hệ quả thực tế: hai biến, một object

Vì nhiều biến có thể trỏ cùng một object, sửa object ở chỗ này có thể làm hỏng chỗ khác mà bạn không
ngờ. Ví dụ kinh điển là `DateTime`:

```php
<?php
declare(strict_types=1);

$start = new DateTime('2026-10-01');
$end = $start->modify('+7 days');        // modify() SỬA chính object và trả về chính nó
echo $start->format('Y-m-d'), ' ', $end->format('Y-m-d'), "\n";   // in ra: 2026-10-08 2026-10-08
var_dump($start === $end);               // in ra: bool(true)

$start2 = new DateTimeImmutable('2026-10-01');
$end2 = $start2->modify('+7 days');      // Immutable: trả về object MỚI, bản gốc giữ nguyên
echo $start2->format('Y-m-d'), ' ', $end2->format('Y-m-d'), "\n"; // in ra: 2026-10-01 2026-10-08
```

Người viết muốn "ngày kết thúc = ngày bắt đầu + 7", nhưng làm mất luôn ngày bắt đầu. Hai cách phòng:
tạo bản sao trước khi sửa (`clone`, mục 12.4), hoặc thiết kế object bất biến (*immutable*): mọi
method "sửa" đều trả về object mới, như `DateTimeImmutable` (mục 12.6). Query builder fluent ở mục 3.4
có cùng vấn đề: truyền builder cho hai nơi, nơi này thêm `where` thì nơi kia cũng bị.

### 12.4 `clone`: copy nông (shallow copy)

`clone $obj` tạo một object mới cùng class, rồi copy từng property từ object cũ sang. Cách copy
này là *shallow copy* (copy nông):

- Property kiểu int, string, array... được copy như phép gán bình thường: bản sao có giá trị riêng.
- Property chứa object thì chỉ copy handle: bản gốc và bản sao dùng chung object con đó.
- Constructor không chạy khi clone.

```php
<?php
declare(strict_types=1);

class Money
{
    public function __construct(public int $amount) {}
}

class Order
{
    public array $lines = [];

    public function __construct(public Money $total) {}
}

$o1 = new Order(new Money(100));
$o1->lines[] = 'bút';

$o2 = clone $o1;                 // copy nông
$o2->lines[] = 'vở';             // array: bản của $o2 tách riêng, $o1 không đổi
$o2->total->amount = 999;        // object con: $o1 và $o2 DÙNG CHUNG một Money!

echo count($o1->lines), ' ', count($o2->lines), "\n";        // in ra: 1 2
echo $o1->total->amount, ' ', $o2->total->amount, "\n";      // in ra: 999 999
var_dump($o1 === $o2, $o1->total === $o2->total);            // in ra 2 dòng: bool(false), bool(true)
```

```
sau clone:
$o1 ──► Order #1 { lines: ['bút'],      total: ─┐ }
                                                 ├──► Money #2 { amount: 999 }
$o2 ──► Order #3 { lines: ['bút','vở'], total: ─┘ }
         (object mới)                            (object con dùng chung)
```

### 12.5 `__clone()`: tự quyết định copy sâu tới đâu

Nếu class định nghĩa method `__clone()`, PHP gọi nó trên bản sao, ngay sau khi copy nông xong.
Trong đó bạn clone tiếp những object con cần tách riêng (*deep copy*, copy sâu):

```php
<?php
declare(strict_types=1);

class Money
{
    public function __construct(public int $amount) {}
}

class Order
{
    public array $lines = [];

    public function __construct(public Money $total) {}

    public function __clone(): void
    {
        // Chạy trên BẢN SAO ($this là object mới), sau khi PHP đã copy nông xong
        $this->total = clone $this->total;   // tách Money ra bản riêng
    }
}

$o1 = new Order(new Money(100));
$o2 = clone $o1;
$o2->total->amount = 999;
echo $o1->total->amount, ' ', $o2->total->amount, "\n";   // in ra: 100 999
var_dump($o1->total === $o2->total);                      // in ra: bool(false)
```

- Chỉ clone sâu những gì cần. Object con là bất biến (như `DateTimeImmutable`) thì dùng chung vô hại,
  không cần clone.
- Array chứa object: copy array chỉ copy các handle bên trong; muốn tách thì duyệt array và clone từng
  phần tử trong `__clone()`.
- ⚠️ Property đang là reference (`$this->x = &$bien`) thì sau clone vẫn là reference tới cùng
  biến (manual ghi rõ).
- Khai báo `private function __clone()` để cấm clone từ bên ngoài (gặp ở singleton hoặc object giữ tài
  nguyên không nhân đôi được): `clone $obj` ném `Error` "Call to private ... __clone() from global
  scope".
- `__clone()` không nhận tham số. Muốn "bản sao nhưng đổi vài property" (nhất là property `readonly`),
  PHP 8.5 có `clone($obj, ['prop' => giá trị])` (*clone with*), còn PHP 8.3 cho phép gán lại property
  `readonly` bên trong `__clone()`. Cả hai ở [Chương 10](10-oop-nang-cao.md).

### 12.6 Ứng dụng: method "with" trả về bản sao

Mẫu object bất biến: method thay đổi không sửa `$this` mà trả về một bản sao đã sửa. Tên method thường
bắt đầu bằng `with` (*wither*):

```php
<?php
declare(strict_types=1);

final class Discount
{
    public function __construct(private string $code, private int $percent) {}

    public function withPercent(int $percent): self
    {
        $copy = clone $this;          // tạo bản sao, KHÔNG sửa $this
        $copy->percent = $percent;    // gán được vì code nằm trong class Discount (mục 5.3)
        return $copy;
    }

    public function percent(): int
    {
        return $this->percent;
    }
}

$base = new Discount('SALE', 10);
$vip = $base->withPercent(20);
echo $base->percent(), ' ', $vip->percent(), "\n";   // in ra: 10 20
```

Object bất biến chia sẻ thoải mái giữa nhiều nơi mà không sợ bị sửa ngầm, nên rất hợp cho *value
object* (tiền, khoảng thời gian, địa chỉ email). PSR-7 (HTTP message) thiết kế toàn bộ request/response
theo kiểu này: `$request->withHeader(...)` trả về request mới.

## 13. So sánh object và kiểm tra kiểu

### 13.1 `===` và `==` với object

Hai toán tử so sánh ([Chương 04](04-kieu-du-lieu.md)) mang nghĩa riêng khi hai vế là object:

| Toán tử | Đúng khi |
|---|---|
| `$a === $b` | Hai vế là cùng một object (cùng handle) |
| `$a == $b` | Cùng class, và từng property bằng nhau khi so bằng `==` (kể cả property `private`) |

```php
<?php
declare(strict_types=1);

class Point
{
    public function __construct(public int $x, public int $y) {}
}

class Point3D extends Point {}

$a = new Point(1, 2);
$b = new Point(1, 2);
$c = $a;

var_dump($a == $b);                  // in ra: bool(true)    cùng class, property bằng nhau
var_dump($a === $b);                 // in ra: bool(false)   hai object khác nhau
var_dump($a === $c);                 // in ra: bool(true)    cùng một object
var_dump($a == new Point(1, 3));     // in ra: bool(false)
var_dump($a == new Point3D(1, 2));   // in ra: bool(false)   khác class, kể cả class con

class Code
{
    public function __construct(public string $value) {}
}

var_dump(new Code('1e3') == new Code('1000'));   // in ra: bool(true)   vì '1e3' == '1000'
```

Những điều cần nhớ:

- ⚠️ `==` so **từng property bằng `==`**, nên mang theo mọi điều kỳ quặc của so sánh lỏng: hai chuỗi
  số `'1e3'` và `'1000'` được so theo giá trị số và bằng nhau. Với object chứa dữ liệu nghiệp vụ, đừng
  dựa vào `==`; viết method `equals()` so sánh chặt đúng những gì bạn coi là "bằng" (mục 5.3).
- `==` đệ quy vào các object con, nên object lớn so bằng `==` tốn thời gian. Hai object trỏ vòng vào
  nhau (A giữ B, B giữ A) làm phép so sánh đệ quy mãi: PHP dừng với "Nesting level too deep -
  recursive dependency?". Từ PHP 8.4 đó là `Error` bắt được; PHP 8.3 trở về trước là Fatal error.
- Muốn biết "có phải chính nó không" (đã xử lý object này chưa, tìm object trong danh sách) thì dùng
  `===`.

### 13.2 `instanceof`: object này có thuộc kiểu đó không

`$obj instanceof X` trả `true` nếu object là instance của `X`, của một class con của `X`, hoặc của
class implement interface `X`:

```php
<?php
declare(strict_types=1);

interface Shippable {}
class Product {}
class Book extends Product implements Shippable {}
class Ebook extends Product {}

$b = new Book();
var_dump($b instanceof Book);               // in ra: bool(true)    chính class
var_dump($b instanceof Product);            // in ra: bool(true)    class cha
var_dump($b instanceof Shippable);          // in ra: bool(true)    interface
var_dump(new Ebook() instanceof Shippable); // in ra: bool(false)

$cls = 'Product';
var_dump($b instanceof $cls);               // in ra: bool(true)    tên class trong biến chuỗi
var_dump($b instanceof ('Prod' . 'uct'));   // in ra: bool(true)    PHP 8.0+: biểu thức trong ngoặc

$notObject = 'Book';
var_dump($notObject instanceof Book);       // in ra: bool(false)   vế trái không phải object: không lỗi
var_dump(null instanceof Book);             // in ra: bool(false)

var_dump(!($b instanceof Ebook));           // in ra: bool(true)    phủ định: nên bọc ngoặc
```

- `instanceof` có độ ưu tiên cao hơn `!`, nên `!$b instanceof Ebook` cũng được hiểu là
  `!($b instanceof Ebook)` ([Chương 07](07-toan-tu-dieu-khien.md)). Vẫn nên viết ngoặc cho người đọc.
- Trait không phải kiểu: `$obj instanceof TênTrait` luôn `false` (mục 11.6).
- `instanceof` không báo lỗi khi class ở vế phải không tồn tại; nó chỉ trả `false`. Gõ sai tên class
  thì điều kiện âm thầm luôn sai. Dùng `TênClass::class` và IDE/công cụ phân tích tĩnh để bắt lỗi này.

Sau khi kiểm tra `instanceof`, IDE và PHPStan hiểu biến đó mang kiểu gì trong nhánh `if`, nên hay dùng
để thu hẹp kiểu trước khi gọi method riêng của class con. Nhưng nếu thấy mình viết chuỗi
`if ($d instanceof PercentDiscount) ... elseif ($d instanceof FixedDiscount) ...` để chọn cách tính, đó
là dấu hiệu nên để mỗi class tự trả lời bằng một method chung (đa hình, mục 8.1): thêm loại mới chỉ cần
thêm class, không phải đi sửa mọi chuỗi `if`.

### 13.3 Các hàm hỏi thông tin về class

```php
<?php
declare(strict_types=1);

interface Shippable {}
class Product {}
class Book extends Product implements Shippable {}

$b = new Book();
var_dump(get_class($b));                    // in ra: string(4) "Book"
var_dump(get_parent_class($b));             // in ra: string(7) "Product"
var_dump(get_parent_class(new Product()));  // in ra: bool(false)   không có cha
var_dump(is_a($b, 'Product'));              // in ra: bool(true)    giống instanceof
var_dump(is_a('Book', 'Product', allow_string: true)); // in ra: bool(true)  hỏi bằng tên class
var_dump(is_subclass_of($b, 'Book'));       // in ra: bool(false)   chính class không tính
var_dump(is_subclass_of($b, 'Product'));    // in ra: bool(true)
var_dump(is_subclass_of($b, 'Shippable'));  // in ra: bool(true)    interface cũng tính
var_dump(method_exists($b, 'slug'));        // in ra: bool(false)
```

| Hàm | Trả lời câu hỏi |
|---|---|
| `get_class($obj)`, `$obj::class` | Object thuộc class nào |
| `get_parent_class($objHoặcTên)` | Class cha trực tiếp (hoặc `false`) |
| `is_a($x, 'C')` | Như `instanceof`; thêm `allow_string: true` để hỏi bằng tên class |
| `is_subclass_of($x, 'C')` | Là class con (hoặc implement interface `C`), không tính chính `C` |
| `class_implements($x)`, `class_uses($x)` | Danh sách interface / trait (mục 11.6) |
| `method_exists($x, 'm')`, `property_exists($x, 'p')` | Có method / property tên đó không |

Trong code ứng dụng thường chỉ cần `instanceof` và `::class`. Các hàm còn lại hay gặp trong thư viện
và framework, nơi phải làm việc với class chỉ biết tên lúc chạy; công cụ đầy đủ cho việc đó là
Reflection ([Chương 10](10-oop-nang-cao.md)).

## 14. Đối chiếu với Java và Go

| Khái niệm | PHP | Java | Go |
|---|---|---|---|
| Đơn vị OOP | `class` | `class` | `struct` + method gắn vào type; không có class |
| Tạo object | `new Foo(...)` | `new Foo(...)` | Literal `Foo{...}` hoặc hàm `NewFoo(...)` theo quy ước |
| Constructor | Một `__construct` mỗi class; nhiều cách tạo thì dùng named constructor | Nhiều constructor (overloading) | Không có; hàm `NewXxx` |
| Truy cập thành viên trong method | Bắt buộc `$this->` | `this.` có thể bỏ | Receiver đặt tên tuỳ ý (`func (c *Cart) Total()`) |
| Visibility | `public`/`protected`/`private`, theo class | Thêm mức package-private (mặc định) | Theo package: tên viết hoa là exported |
| Kế thừa | Đơn (`extends`) | Đơn (`extends`) | Không có; dùng *embedding* (nhúng struct) |
| Interface | Khai báo tường minh `implements` | Tường minh `implements` | Ngầm định: type có đủ method là thoả |
| Tái dùng code ngang | Trait | Default method trong interface (Java 8+) | Embedding |
| Class gốc chung | Không có | `java.lang.Object` | Không có (`any` là interface rỗng) |
| Gán biến | Object: copy handle; array: copy giá trị | Object: copy reference | Struct: copy giá trị; muốn chia sẻ dùng pointer |
| `==` với object | So từng property (lỏng); `===` là cùng object | `==` là cùng object; `equals()` tự định nghĩa | `==` so từng field (struct so sánh được) |
| Huỷ object | Destructor chạy ngay khi refcount về 0 | GC không xác định thời điểm; dùng try-with-resources | GC; dùng `defer` để dọn dẹp |

Hai khác biệt đáng nhớ nhất khi chuyển qua lại: interface của Go được thoả ngầm (không cần ghi
`implements`), còn PHP và Java phải khai báo; struct của Go được copy khi gán, còn object PHP và Java
được chia sẻ qua handle/reference.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| Viết `$items`, `total()` trong method thay vì `$this->items`, `$this->total()` | PHP không có `this` ngầm: đó là biến cục bộ và hàm toàn cục | Luôn viết `$this->` (mục 3.2) |
| `Typed property ... must not be accessed before initialization` | Property có kiểu, không mặc định thì ở trạng thái uninitialized, kể cả `?string` | Gán trong constructor hoặc ghi mặc định, `?string $x = null` (mục 2.3) |
| Gõ sai tên property khi gán, dữ liệu "biến mất" | PHP tạo dynamic property mới (8.2+ chỉ Deprecated) | Khai báo mọi property; không tắt thông báo deprecated; dùng PHPStan (mục 2.5) |
| Class con có constructor, property của cha chưa có giá trị | Constructor cha không tự chạy | Gọi `parent::__construct(...)` (mục 8.4) |
| Class con gán `$this->x` mà cha vẫn thấy giá trị cũ | `x` là `private` của cha; class con vừa tạo một property mới | Cha mở `protected` hoặc cung cấp method (mục 5.4) |
| `Declaration of ... must be compatible with ...` | Override vi phạm quy tắc chữ ký (LSP) | Chỉ thêm tham số tuỳ chọn, nới kiểu tham số, thu hẹp kiểu trả về (mục 8.3) |
| `Unknown named parameter` khi gọi trên object class con | Class con đổi tên tham số khi override | Giữ nguyên tên tham số của cha/interface (mục 8.3) |
| Class con đổi hằng hay static property nhưng code của cha vẫn dùng giá trị cũ | Code của cha đọc bằng `self::` | Dùng `static::` cho thứ class con được phép đổi (mục 7.2) |
| Bộ đếm static của các class con cộng lẫn vào nhau | Static property của cha được dùng chung nếu con không khai báo lại | Khai báo lại ở class con, hoặc dùng array khoá theo `static::class` (mục 6.3) |
| Dữ liệu user này lộ sang user khác trên Octane/queue worker | Static property sống suốt tiến trình | Không lưu state theo request vào static (mục 6.5) |
| Sửa object ở chỗ này, chỗ khác cũng đổi theo | Gán và truyền object chỉ copy handle | `clone` trước khi sửa, hoặc thiết kế immutable (mục 12) |
| Bản `clone` vẫn dính object con với bản gốc | `clone` là copy nông | Clone object con trong `__clone()` (mục 12.5) |
| `$a == $b` đúng dù dữ liệu "khác" | `==` so từng property bằng so sánh lỏng | Viết `equals()` so sánh chặt; dùng `===` khi cần "cùng object" (mục 13.1) |
| Type hint bằng tên trait, mọi lời gọi đều `TypeError` | Trait không phải kiểu | Tạo interface đi kèm trait (mục 11.6) |
| Chạy tốt trên máy Mac, "Class not found" trên server | Viết sai hoa thường tên class; autoloader tìm file theo đúng tên đã viết, mà hệ file Linux phân biệt hoa thường | Viết đúng tên như khai báo (mục 1.3) |
| `Deprecated: Return type of X::count() should either be compatible with Countable::count(): int` | Từ 8.1 method của interface/class có sẵn có kiểu trả về tạm thời | Ghi đủ kiểu trả về khi implement (mục 8.3) |

## Tóm tắt chương

- Class là bản mô tả kiểu dữ liệu gồm property (dữ liệu), method (hành vi) và hằng; object là một
  thể hiện cụ thể tạo bằng `new`, có bộ property riêng. Trong method, `$this` là object đang được gọi
  và phải viết tường minh.
- Property nên có kiểu. Property có kiểu mà chưa gán thì ở trạng thái uninitialized (đọc là `Error`),
  không phải `null`. Gán vào property chưa khai báo tạo dynamic property, deprecated từ PHP 8.2.
- Constructor `__construct` chuẩn bị object hợp lệ ngay lúc tạo; constructor property promotion (8.0)
  gộp khai báo và gán; `new` trong giá trị mặc định của tham số (8.1) cho dependency mặc định. Destructor
  chạy ngay khi không còn ai giữ object (trừ khi nằm trong vòng tham chiếu).
- `public`/`protected`/`private` thực hiện encapsulation; visibility tính theo class, không theo
  object. Mặc định chọn `private`.
- `static` gắn thành viên với class. `self` là class viết code, `parent` là class cha, `static` là
  class được gọi lúc chạy. Static property dùng chung giữa cha và con nếu con không khai báo lại, và là
  state toàn cục nguy hiểm trong tiến trình sống lâu.
- Hằng class có visibility, `final` (8.1), kiểu (8.3) và lấy theo tên động `C::{$name}` (8.3).
- Kế thừa đơn bằng `extends`; override phải giữ chữ ký tương thích (LSP: tham số nới rộng, kiểu trả
  về thu hẹp, visibility không hẹp lại); constructor cha không tự chạy; method `private` không bị
  override; `final` cấm kế thừa hoặc override.
- Abstract class là khung dở dang có code chung (template method); interface là hợp đồng không có cài
  đặt, một class implement được nhiều cái, từ 8.4 có cả property; trait là code được chép vào class,
  giải quyết xung đột bằng `insteadof`/`as`, và không phải kiểu.
- Biến chứa handle tới object: gán và truyền tham số không copy object (nhưng cũng không phải truyền
  tham chiếu). `clone` là copy nông, `__clone()` để copy sâu phần cần thiết.
- Với object, `===` là "cùng một object", `==` là "cùng class và property bằng nhau theo `==`";
  `instanceof` kiểm tra class, class cha và interface.

## Câu hỏi tự kiểm tra

1. Ngay sau `new`, property `public ?string $note;` mang giá trị gì? Đọc nó thì chuyện gì xảy ra? Còn
   `public $note;` thì sao? (mục 2.3)
2. Vì sao trong class con, câu lệnh `$this->balance = 999;` có thể không làm đổi giá trị mà method của
   class cha trả về? PHP 8.2 trở lên cảnh báo gì trong trường hợp này? (mục 5.4)
3. Class cha có `public function find(int $id): ?Model`. Với từng chữ ký sau ở class con, hợp lệ hay
   không, vì sao: `find(int|string $id): User`, `find(int $id, bool $withTrashed): ?Model`,
   `protected function find(int $id): ?Model`, `find(int $id): Model|false`. (mục 8.3)
4. Viết một ví dụ nhỏ cho thấy `self::TABLE` và `static::TABLE` cho kết quả khác nhau. Khi viết class
   cha cho người khác kế thừa, bạn chọn cái nào và vì sao? (mục 6.2, 7.2)
5. Destructor chạy vào những lúc nào? Nêu một tình huống destructor bị hoãn lâu hơn bạn nghĩ. (mục 4.4)
6. "Object trong PHP được truyền theo tham chiếu": câu này sai ở đâu? Viết một hàm chứng minh. (mục 12.2)
7. Sau `$b = clone $a;`, những property nào của `$b` độc lập với `$a`, những property nào không?
   `__clone()` chạy trên object nào và vào lúc nào? (mục 12.4, 12.5)
8. Vì sao không nên dùng `==` để so sánh hai value object `Money`? Bạn sẽ thay bằng gì? (mục 13.1)
9. So sánh interface, abstract class và trait theo ba tiêu chí: có code cài đặt không, có phải là kiểu
   không, một class dùng được mấy cái. Cho một ví dụ mà trait là lựa chọn đúng và một ví dụ nên dùng
   interface. (mục 11.7)
10. Một static property `$currentUser` chạy đúng trên PHP-FPM nhưng gây lộ dữ liệu trên Laravel Octane.
    Giải thích vì sao. (mục 6.5)

## Bài tập

Mỗi bài là một file PHP chạy bằng `php ten-file.php` (hoặc `docker run --rm -v "$PWD":/app -w /app
php:8.5-cli php ten-file.php`). Luôn có `declare(strict_types=1);` và khai báo kiểu đầy đủ.

1. **Tài khoản ngân hàng có invariant.** Viết class `BankAccount` với số dư `private`, không bao giờ
   âm. Có named constructor `open(string $owner, int $initialDeposit)` (constructor để `private`), các
   method `deposit()`, `withdraw()`, `balance()` và `transferTo(BankAccount $other, int $amount)`
   (gợi ý: `transferTo` được đọc/ghi số dư `private` của `$other`, vì sao?). Vi phạm quy tắc thì ném
   `InvalidArgumentException`. Viết đoạn script thử đủ trường hợp đúng và sai, in kết quả ra màn hình.

2. **Hệ thống gửi thông báo.** Thiết kế:
   - interface `Notifier` với `send(string $to, string $message): bool`;
   - abstract class `BaseNotifier implements Notifier` có `send()` là `final`, chạy theo trình tự
     kiểm tra người nhận (abstract) → định dạng nội dung (có bản mặc định) → gửi (abstract), và đếm số
     lần gửi thành công riêng cho từng class con bằng static property (đọc kỹ mục 6.3 trước khi viết);
   - hai class `final` là `EmailNotifier` và `SmsNotifier`;
   - trait `RecordsHistory` lưu lịch sử tin đã gửi vào một array, dùng trong cả hai class.
   Viết hàm `broadcast(array $notifiers, string $to, string $message)` chỉ biết tới `Notifier`. In số
   lần gửi của từng class để chứng minh hai bộ đếm không lẫn vào nhau.

3. **Clone sâu.** Class `Invoice` chứa một object `Customer` và một array các object `InvoiceLine`.
   Viết `__clone()` để bản sao độc lập hoàn toàn với bản gốc, và method `withCustomer(Customer $c):
   self` trả về bản sao thay vì sửa `$this`. Viết script chứng minh bằng `===` và `spl_object_id()` rằng
   sửa bản sao (đổi tên khách hàng, đổi số lượng một dòng) không ảnh hưởng bản gốc. Sau đó thử xoá
   `__clone()` và quan sát kết quả thay đổi thế nào.

4. **Tính năng theo phiên bản.** Viết một file dùng cùng lúc: hằng có kiểu, `TênClass::{$tên}`,
   `new Foo()->bar()` không ngoặc, property trong interface, và `use T { m as final; }`. Chạy file trên
   `php:8.2-cli`, `php:8.3-cli`, `php:8.4-cli`, `php:8.5-cli` (Docker). Với mỗi bản, ghi lại lỗi đầu
   tiên gặp phải và giải thích vì sao lỗi xuất hiện ở lúc parse/compile chứ không phải lúc chạy tới dòng
   đó.

## Đọc thêm

- PHP Manual, [Classes and Objects](https://www.php.net/manual/en/language.oop5.php) và các trang con:
  [The Basics](https://www.php.net/manual/en/language.oop5.basic.php),
  [Properties](https://www.php.net/manual/en/language.oop5.properties.php),
  [Class Constants](https://www.php.net/manual/en/language.oop5.constants.php),
  [Constructors and Destructors](https://www.php.net/manual/en/language.oop5.decon.php),
  [Visibility](https://www.php.net/manual/en/language.oop5.visibility.php),
  [Object Inheritance](https://www.php.net/manual/en/language.oop5.inheritance.php),
  [Scope Resolution Operator](https://www.php.net/manual/en/language.oop5.paamayim-nekudotayim.php),
  [Static Keyword](https://www.php.net/manual/en/language.oop5.static.php),
  [Class Abstraction](https://www.php.net/manual/en/language.oop5.abstract.php),
  [Object Interfaces](https://www.php.net/manual/en/language.oop5.interfaces.php),
  [Traits](https://www.php.net/manual/en/language.oop5.traits.php),
  [Final Keyword](https://www.php.net/manual/en/language.oop5.final.php),
  [Object Cloning](https://www.php.net/manual/en/language.oop5.cloning.php),
  [Comparing Objects](https://www.php.net/manual/en/language.oop5.object-comparison.php),
  [Objects and references](https://www.php.net/manual/en/language.oop5.references.php),
  [Covariance and Contravariance](https://www.php.net/manual/en/language.oop5.variance.php).
- PHP Manual: [Type Operators (`instanceof`)](https://www.php.net/manual/en/language.operators.type.php),
  [stdClass](https://www.php.net/manual/en/class.stdclass.php),
  [Predefined Interfaces and Classes](https://www.php.net/manual/en/reserved.interfaces.php).
- RFC (đọc phần Proposal):
  [Constructor Property Promotion](https://wiki.php.net/rfc/constructor_promotion),
  [Typed Properties 2.0](https://wiki.php.net/rfc/typed_properties_v2),
  [New in initializers](https://wiki.php.net/rfc/new_in_initializers),
  [Final class constants](https://wiki.php.net/rfc/final_class_const),
  [Constants in traits](https://wiki.php.net/rfc/constants_in_traits),
  [Deprecate dynamic properties](https://wiki.php.net/rfc/deprecate_dynamic_properties),
  [Typed class constants](https://wiki.php.net/rfc/typed_class_constants),
  [Dynamic class constant fetch](https://wiki.php.net/rfc/dynamic_class_constant_fetch),
  [Marking overridden methods (`#[\Override]`)](https://wiki.php.net/rfc/marking_overriden_methods),
  [new without parentheses](https://wiki.php.net/rfc/new_without_parentheses),
  [Property hooks](https://wiki.php.net/rfc/property-hooks) (phần interface properties),
  [Final property promotion](https://wiki.php.net/rfc/final_promotion),
  [Static variable inheritance](https://wiki.php.net/rfc/static_variable_inheritance),
  [Inheritance of private methods](https://wiki.php.net/rfc/inheritance_private_methods),
  [Abstract trait method validation](https://wiki.php.net/rfc/abstract_trait_method_validation).
- php-src `UPGRADING` của từng bản (các mục "Backward Incompatible Changes", "Deprecated
  Functionality", "New Features"): 8.1 (biến static khi kế thừa, gọi static trên trait), 8.3 (static
  property của trait, `as final`, typed class constant), 8.4 (so sánh đệ quy ném `Error`), 8.5 (thứ tự
  gắn trait, promotion cho property `final`).
- [PSR-1](https://www.php-fig.org/psr/psr-1/) và [PSR-12](https://www.php-fig.org/psr/psr-12/): quy ước
  đặt tên class, method, hằng và cách viết khai báo class.
