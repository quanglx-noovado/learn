# Chương 13. Generator, iterator và SPL

> [← Mục lục](README.md) · [← Chương 12: Lỗi và exception](12-loi-exception.md) · [Chương 14: File, stream, JSON và thời gian →](14-file-json-thoi-gian.md)

**Bạn sẽ học được:**

- `foreach` làm gì khi gặp một object, và họ interface `Traversable`, `Iterator`, `IteratorAggregate`
  giúp class của bạn tự quyết định "duyệt" nghĩa là gì.
- Viết *generator* bằng `yield`: hàm biết tạm dừng giữa chừng rồi chạy tiếp, nhờ đó xử lý file hay bảng
  dữ liệu rất lớn mà bộ nhớ gần như không đổi.
- `yield from`, `send()`, `throw()`, `getReturn()`: generator như một *coroutine* trao đổi dữ liệu hai
  chiều với code gọi nó.
- Chọn đúng cấu trúc dữ liệu của SPL (`SplStack`, `SplQueue`, `SplPriorityQueue`, `SplFixedArray`,
  `SplObjectStorage`, `ArrayObject`, `ArrayIterator`) thay vì cố nhét mọi thứ vào array.
- *Fiber* (PHP 8.1) là gì, khác generator và khác thread ở đâu, và vì sao nó là công cụ cho tác giả thư
  viện async chứ hiếm khi xuất hiện trong code ứng dụng.

**Cần biết trước:** [Chương 06: Mảng](06-mang.md) (array, key, copy-on-write),
[Chương 07: Toán tử và cấu trúc điều khiển](07-toan-tu-dieu-khien.md) (`foreach`),
[Chương 08: Hàm](08-ham.md) (closure, callable), [Chương 09: OOP cơ bản](09-oop-co-ban.md) (class,
interface) và [Chương 12: Lỗi và exception](12-loi-exception.md) (`try`/`catch`/`finally`).

Cách chạy ví dụ: lưu thành file `.php` rồi chạy `php ten-file.php`. Output ghi trong comment là output
thật trên PHP 8.5, trừ chỗ ghi "output minh hoạ"; chỗ nào khác giữa các bản đều ghi rõ. Máy chưa cài PHP thì dùng Docker, chạy trong thư
mục chứa file:

```bash
docker run --rm -v "$PWD":/app -w /app php:8.5-cli php ten-file.php
```

## 1. Duyệt dữ liệu và ý tưởng iterator

### 1.1 Nhắc lại: `foreach` với array

*Duyệt* (*iterate*) là đi qua lần lượt từng phần tử của một tập hợp. Với array, bạn đã quen `foreach`
([Chương 07](07-toan-tu-dieu-khien.md)):

```php
<?php
declare(strict_types=1);

$prices = ['tea' => 20, 'coffee' => 35];
foreach ($prices as $name => $price) {
    echo "$name: $price\n";
}
// in ra:
// tea: 20
// coffee: 35
```

Array có sẵn mọi phần tử trong bộ nhớ, `foreach` chỉ việc đi từ đầu tới cuối. Cách này đơn giản và đủ
dùng cho phần lớn trường hợp.

### 1.2 Khi array không đủ

Có ba tình huống mà "đưa hết vào một array rồi `foreach`" không ổn:

1. **Dữ liệu quá lớn.** Một file log 5 GB, một bảng có mười triệu dòng. Nạp hết vào array thì chạm
   `memory_limit` (giới hạn bộ nhớ của một request/script PHP) và script chết. Bạn chỉ cần xử lý từng
   dòng một, xong dòng nào bỏ dòng đó.
2. **Dữ liệu sinh ra dần, hoặc không có điểm kết thúc.** Một API trả dữ liệu theo trang: chưa cần trang 3
   thì đừng gọi HTTP lấy trang 3. Một dãy số vô hạn (số nguyên tố, ID tăng dần): không thể có một array
   vô hạn.
3. **Muốn giấu cấu trúc bên trong.** Class `Order` giữ danh sách dòng hàng trong một property `private`.
   Bạn muốn code bên ngoài `foreach ($order as $line)` được, nhưng không muốn trả nguyên array ra ngoài
   để ai cũng sửa được.

Cả ba cùng cần một thứ: một object mà `foreach` hỏi được "phần tử tiếp theo là gì", và object đó tự quyết
định lấy phần tử từ đâu (đọc file, gọi API, tính toán, đọc từ property riêng).

### 1.3 Iterator: một "con trỏ" biết đi tới

*Iterator* là một object đóng vai con trỏ đặt trên một dãy phần tử. Nó trả lời được bốn câu hỏi và làm
được một việc:

- Còn phần tử ở vị trí hiện tại không? (`valid`)
- Phần tử hiện tại là gì? (`current`)
- Key của phần tử hiện tại là gì? (`key`)
- Bước sang phần tử kế tiếp. (`next`)
- Quay về đầu dãy. (`rewind`)

Hình dung một cái bookmark trong cuốn sách: bookmark không chứa cả cuốn sách, nó chỉ biết đang ở trang
nào và lật sang trang sau được. Iterator cũng vậy: nó không bắt buộc phải giữ toàn bộ dữ liệu, chỉ cần
biết lấy phần tử tiếp theo bằng cách nào.

Mô hình này gọi là *pull*: người dùng (vòng `foreach`) chủ động kéo từng phần tử khi cần. Không ai kéo
thì không có gì được tính hay được đọc.

### 1.4 Họ interface duyệt được

PHP mô tả "thứ gì `foreach` được" bằng một nhóm interface có sẵn:

```
                    Traversable
          (interface rỗng, chỉ để đánh dấu: "foreach được")
                 /                      \
           Iterator                 IteratorAggregate
  (object TỰ LÀ con trỏ,           (object là "kho", đưa ra một
   có 5 method)                     Traversable khác qua getIterator())
        |
        +-- Generator          (PHP tự tạo khi gọi hàm có yield, mục 4)
        +-- ArrayIterator, SplDoublyLinkedList, SplHeap... (SPL, mục 8 và 9)
```

- `Traversable` không có method nào. Bạn không implement trực tiếp được nó (mục 3.4), chỉ dùng nó làm
  kiểu khi khai báo tham số: "tôi nhận bất cứ thứ gì `foreach` được, trừ array".
- `iterable` là kiểu gộp `array|Traversable` ([Chương 04](04-kieu-du-lieu.md)): nhận cả array lẫn
  iterator.
- Một object thường (không implement gì) vẫn `foreach` được, nhưng khi đó PHP duyệt các property nhìn
  thấy được từ chỗ gọi ([Chương 07](07-toan-tu-dieu-khien.md)). Cách đó hiếm khi là điều bạn muốn.

Chương này đi lần lượt: `Iterator` (mục 2), `IteratorAggregate` (mục 3), generator (mục 4 tới 7), các
iterator và cấu trúc dữ liệu có sẵn của SPL (mục 8, 9), rồi Fiber (mục 10).

## 2. Interface `Iterator`

### 2.1 Năm method

```php
interface Iterator extends Traversable
{
    public function current(): mixed;   // giá trị ở vị trí hiện tại
    public function key(): mixed;       // key ở vị trí hiện tại
    public function next(): void;       // bước sang vị trí kế
    public function rewind(): void;     // quay về vị trí đầu
    public function valid(): bool;      // vị trí hiện tại có phần tử không
}
```

Class implement `Iterator` phải viết đủ năm method này. Đổi lại, `foreach` dùng được trên object của
class đó và nhận đúng những gì các method trả ra.

### 2.2 `foreach` gọi các method theo thứ tự nào

Cách dễ hiểu nhất là cho mỗi method in tên mình ra. Ví dụ dưới là iterator duyệt dãy số từ `$start`
tới `$end`, không tạo array nào:

```php
<?php
declare(strict_types=1);

final class RangeIterator implements Iterator
{
    private int $current;

    public function __construct(
        private readonly int $start,
        private readonly int $end,
        private readonly int $step = 1,
    ) {
        $this->current = $start;
    }

    public function rewind(): void
    {
        echo "[rewind] ";
        $this->current = $this->start;
    }

    public function valid(): bool
    {
        echo "[valid] ";
        return $this->current <= $this->end;
    }

    public function current(): int
    {
        echo "[current] ";
        return $this->current;
    }

    public function key(): int
    {
        echo "[key] ";
        return intdiv($this->current - $this->start, $this->step);
    }

    public function next(): void
    {
        echo "[next] ";
        $this->current += $this->step;
    }
}

foreach (new RangeIterator(10, 30, 10) as $i => $n) {
    echo "=> $i: $n\n";
}
echo "\n";
// in ra:
// [rewind] [valid] [current] [key] => 0: 10
// [next] [valid] [current] [key] => 1: 20
// [next] [valid] [current] [key] => 2: 30
// [next] [valid]

foreach (new RangeIterator(10, 30, 10) as $n) {   // không lấy key
    echo "=> $n\n";
}
echo "\n";
// in ra:
// [rewind] [valid] [current] => 10
// [next] [valid] [current] => 20
// [next] [valid] [current] => 30
// [next] [valid]
```

Đọc output ta thấy `foreach` thực chất là đoạn code sau:

```php
$it->rewind();                 // 1. quay về đầu (gọi đúng một lần, khi bắt đầu vòng lặp)
while ($it->valid()) {         // 2. còn phần tử không?
    $n = $it->current();       // 3. lấy giá trị
    $i = $it->key();           //    lấy key, CHỈ khi foreach có "$i =>"
    // ... thân vòng lặp ...
    $it->next();               // 4. bước tiếp, rồi quay lại bước 2
}
```

Ba điều rút ra:

- `rewind()` được gọi mỗi lần bắt đầu một vòng `foreach` mới. Nhờ đó cùng một iterator duyệt lại từ đầu
  được (trừ generator, mục 4.6).
- `key()` chỉ được gọi khi bạn viết `foreach ($it as $k => $v)`. Không viết `$k =>` thì PHP không hỏi
  key.
- `valid()` được gọi một lần sau cùng và trả `false` thì vòng lặp dừng. Nếu `valid()` không bao giờ trả
  `false`, vòng lặp chạy mãi (iterator vô hạn là hợp lệ, miễn người dùng tự `break`).

### 2.3 Ví dụ thực tế: duyệt dữ liệu phân trang

Iterator thật sự có ích khi việc lấy phần tử tốn kém. Ví dụ dưới giả lập một API trả danh sách người dùng
theo trang, mỗi trang 2 người. Iterator chỉ tải trang tiếp theo khi đã duyệt hết trang hiện tại:

```php
<?php
declare(strict_types=1);

// Giả lập một API trả dữ liệu theo trang. Thực tế đây là HTTP request hoặc câu SQL có LIMIT.
function fetchPage(int $page): array
{
    echo "  (tải trang $page)\n";
    $all = ['An', 'Bình', 'Chi', 'Dũng', 'Em'];
    return array_slice($all, ($page - 1) * 2, 2);   // mỗi trang 2 phần tử
}

final class PagedUsers implements Iterator
{
    private int $page = 1;
    /** @var list<string> */
    private array $buffer = [];
    private int $index = 0;   // vị trí trong $buffer
    private int $key = 0;     // số thứ tự tính từ đầu

    public function rewind(): void
    {
        $this->page = 1;
        $this->buffer = fetchPage($this->page);
        $this->index = 0;
        $this->key = 0;
    }

    public function valid(): bool
    {
        return $this->index < count($this->buffer);
    }

    public function current(): string
    {
        return $this->buffer[$this->index];
    }

    public function key(): int
    {
        return $this->key;
    }

    public function next(): void
    {
        $this->index++;
        $this->key++;
        if ($this->index >= count($this->buffer) && count($this->buffer) > 0) {
            $this->page++;
            $this->buffer = fetchPage($this->page);   // hết trang hiện tại mới tải trang sau
            $this->index = 0;
        }
    }
}

foreach (new PagedUsers() as $i => $name) {
    echo "$i: $name\n";
    if ($name === 'Chi') {
        break;   // dừng sớm: trang 3 không bao giờ được tải
    }
}
// in ra:
//   (tải trang 1)
// 0: An
// 1: Bình
//   (tải trang 2)
// 2: Chi
```

Code dùng iterator chỉ thấy một vòng `foreach` bình thường. Toàn bộ chuyện "trang", "buffer", "tải khi
cần" nằm gọn trong class. Đây là lợi ích chính của iterator: tách cách lấy dữ liệu khỏi cách dùng dữ
liệu.

Viết đủ năm method và tự giữ trạng thái (`$page`, `$index`, `$key`) như trên khá dài dòng và dễ sai.
Mục 4 sẽ viết lại đúng ví dụ này bằng generator chỉ trong vài dòng.

### 2.4 Cạm bẫy khi tự viết `Iterator`

⚠️ **Thiếu kiểu trả về thì bị `Deprecated`.** Từ PHP 8.1 các method của interface có sẵn mang kiểu trả
về "tạm thời" (*tentative return type*). Implement mà không ghi kiểu, hoặc ghi kiểu không tương thích:

```php
public function current() { return $this->p; }   // thiếu ": mixed" (hoặc kiểu hẹp hơn như ": int")
// Deprecated: Return type of Old::current() should either be compatible with Iterator::current(): mixed,
// or the #[\ReturnTypeWillChange] attribute should be used to temporarily suppress the notice
```

Cách sửa: ghi kiểu trả về. Kiểu hẹp hơn kiểu của interface vẫn hợp lệ (`current(): int` thay cho
`mixed`, vì kiểu trả về được phép hẹp lại khi kế thừa, [Chương 09](09-oop-co-ban.md)). Attribute
`#[\ReturnTypeWillChange]` chỉ dành cho thư viện cần chạy cả trên PHP cũ.

⚠️ **Hai vòng `foreach` lồng nhau trên cùng một `Iterator` dùng chung một vị trí.** Iterator *là* con
trỏ, và chỉ có một con trỏ:

```php
<?php
declare(strict_types=1);

final class Letters implements Iterator
{
    private int $pos = 0;
    /** @param list<string> $items */
    public function __construct(private array $items) {}
    public function rewind(): void { $this->pos = 0; }
    public function valid(): bool { return $this->pos < count($this->items); }
    public function current(): string { return $this->items[$this->pos]; }
    public function key(): int { return $this->pos; }
    public function next(): void { $this->pos++; }
}

$it = new Letters(['a', 'b', 'c']);
foreach ($it as $x) {
    foreach ($it as $y) {
        echo "$x$y ";
    }
}
echo "\n";
// in ra: aa ab ac
// Mong đợi 9 cặp, chỉ được 3: vòng trong rewind rồi chạy hết con trỏ chung,
// khi quay ra vòng ngoài thì valid() đã false.
```

Muốn duyệt lồng nhau hay duyệt song song, dùng `IteratorAggregate` (mục 3), mỗi vòng `foreach` sẽ có
một con trỏ riêng.

⚠️ **Không `foreach` by reference trên iterator được.** Viết `foreach ($it as &$v)` với object
của class tự viết implement `Iterator` ném `Error: An iterator cannot be used with foreach by reference`. Muốn sửa phần tử thì gọi
method của collection, hoặc dùng `ArrayAccess` (mục 3.3).

⚠️ **`valid()` và `current()` nên không có tác dụng phụ.** `foreach` gọi `valid()` mỗi vòng, và code
khác (ví dụ `iterator_to_array`) có thể gọi `current()` nhiều lần ở cùng một vị trí. Nếu `current()`
đọc dòng tiếp theo của file thì mỗi lần gọi trả một dòng khác. Việc "tiến lên" chỉ nên nằm trong `next()`
(và `rewind()` cho phần tử đầu tiên), như cách `PagedUsers` làm.

## 3. Interface `IteratorAggregate`

### 3.1 Tách "kho" khỏi "con trỏ"

Phần lớn class muốn được duyệt là một *kho* chứa dữ liệu: giỏ hàng, danh sách sản phẩm, cây menu. Bắt
kho tự làm con trỏ (implement `Iterator`) gây ra hai vấn đề vừa thấy: phải viết năm method, và chỉ có
một vị trí duyệt dùng chung.

`IteratorAggregate` giải quyết bằng cách tách vai: kho chỉ cần một method trả về một con trỏ mới.

```php
interface IteratorAggregate extends Traversable
{
    public function getIterator(): Traversable;
}
```

Mỗi lần bắt đầu `foreach ($kho as ...)`, PHP gọi `$kho->getIterator()` để lấy một iterator, rồi duyệt
iterator đó theo đúng trình tự ở mục 2.2. Hai vòng `foreach` là hai lần gọi `getIterator()`, nên là hai
con trỏ độc lập.

### 3.2 Cách đơn giản nhất: trả về `ArrayIterator`

Dữ liệu đã nằm trong một array `private` thì bọc nó bằng `ArrayIterator` (một iterator có sẵn của SPL
duyệt qua array, mục 9.7):

```php
<?php
declare(strict_types=1);

final class Letters implements IteratorAggregate
{
    /** @param list<string> $items */
    public function __construct(private array $items) {}

    public function getIterator(): Iterator
    {
        return new ArrayIterator($this->items);
    }
}

$it = new Letters(['a', 'b', 'c']);
foreach ($it as $x) {
    foreach ($it as $y) {
        echo "$x$y ";
    }
}
echo "\n";
// in ra: aa ab ac ba bb bc ca cb cc     (đủ 9 cặp: mỗi foreach có con trỏ riêng)

var_dump($it instanceof Traversable);        // in ra: bool(true)
var_dump($it instanceof Iterator);           // in ra: bool(false)
var_dump($it instanceof IteratorAggregate);  // in ra: bool(true)
```

Kiểu trả về của `getIterator()` trong interface là `Traversable`; khai báo hẹp hơn thành `Iterator`
như trên là hợp lệ và cho người đọc biết rõ hơn.

`getIterator()` cũng có thể trả về một generator, cách này gọn nhất khi cần tính toán trong lúc duyệt
(mục 4.7). Laravel làm đúng như mục này: `Illuminate\Support\Collection` có
`getIterator(): Traversable { return new ArrayIterator($this->items); }`.

### 3.3 Collection hoàn chỉnh: duyệt, đếm, truy cập như array

Một class collection trong thực tế thường implement thêm hai interface quen thuộc từ
[Chương 09](09-oop-co-ban.md):

- `Countable`: method `count(): int`, để gọi `count($obj)`.
- `ArrayAccess`: bốn method `offsetExists`, `offsetGet`, `offsetSet`, `offsetUnset`, để dùng cú pháp
  `$obj[$key]`, `isset($obj[$key])`, `$obj[$key] = ...`, `unset($obj[$key])`.

Ví dụ một danh sách sản phẩm chỉ đọc, key là mã SKU:

```php
<?php
declare(strict_types=1);

final class Product
{
    public function __construct(public readonly string $sku, public readonly int $price) {}
}

/**
 * @implements IteratorAggregate<string, Product>
 * @implements ArrayAccess<string, Product>
 */
final class ProductList implements IteratorAggregate, Countable, ArrayAccess
{
    /** @var array<string, Product> */
    private array $items = [];

    public function __construct(Product ...$products)
    {
        foreach ($products as $p) {
            $this->items[$p->sku] = $p;
        }
    }

    public function getIterator(): Iterator
    {
        return new ArrayIterator($this->items);
    }

    public function count(): int
    {
        return count($this->items);
    }

    public function offsetExists(mixed $offset): bool
    {
        return isset($this->items[$offset]);
    }

    public function offsetGet(mixed $offset): Product
    {
        return $this->items[$offset] ?? throw new OutOfBoundsException("Không có SKU $offset");
    }

    public function offsetSet(mixed $offset, mixed $value): void
    {
        throw new LogicException('ProductList là chỉ đọc');
    }

    public function offsetUnset(mixed $offset): void
    {
        throw new LogicException('ProductList là chỉ đọc');
    }
}

$list = new ProductList(new Product('A1', 100), new Product('B2', 250));

foreach ($list as $sku => $product) {
    echo "$sku: {$product->price}\n";
}
// in ra:
// A1: 100
// B2: 250

echo count($list), "\n";           // in ra: 2
echo $list['B2']->price, "\n";     // in ra: 250
var_dump(isset($list['Z9']));      // in ra: bool(false)

try {
    $list['C3'] = new Product('C3', 1);
} catch (LogicException $e) {
    echo $e->getMessage(), "\n";   // in ra: ProductList là chỉ đọc
}
```

Comment `@implements IteratorAggregate<string, Product>` không ảnh hưởng gì lúc chạy. Nó dành cho công
cụ phân tích tĩnh như PHPStan, Psalm và IDE: nhờ nó, IDE biết `$product` trong vòng `foreach` là
`Product` ([Chương 21](21-chat-luong-code.md)).

⚠️ `ArrayAccess` chỉ cho mượn cú pháp, object vẫn không phải array: các hàm `array_*` như `array_map`,
`array_keys`, `in_array` không nhận nó (ném `TypeError`). Cần array thật thì gọi
`iterator_to_array($list)` (mục 3.4).

### 3.4 `Traversable`, `iterable` và các hàm `iterator_*`

**Khai báo kiểu tham số.** Khi viết một hàm chỉ cần duyệt dữ liệu một lượt, chọn kiểu rộng nhất đủ dùng:

| Kiểu tham số | Nhận được | Dùng khi |
|---|---|---|
| `iterable` | array, mọi `Traversable` (iterator, generator, `IteratorAggregate`) | Chỉ cần `foreach` một lượt. Lựa chọn mặc định |
| `Traversable` | Mọi object `foreach` được, không nhận array | Hiếm khi cần phân biệt với array |
| `Iterator` | Chỉ object tự là con trỏ | Cần gọi `current()`, `next()`... bằng tay |
| `array` | Chỉ array | Cần `count`, truy cập theo key, các hàm `array_*` |

**Không implement trực tiếp `Traversable` được.** Interface này chỉ là "nhãn" mà engine đọc; class của
bạn phải đi qua `Iterator` hoặc `IteratorAggregate`:

```php
final class Bad implements Traversable {}
// Fatal error: Class Bad must implement interface Traversable as part of either Iterator or
// IteratorAggregate
```

**Ba hàm tiện ích** làm việc với mọi thứ duyệt được:

```php
<?php
declare(strict_types=1);

$it = new ArrayIterator(['x' => 1, 'y' => 2, 'z' => 3]);

echo json_encode(iterator_to_array($it)), "\n";          // copy ra array, GIỮ key
// in ra: {"x":1,"y":2,"z":3}

echo json_encode(iterator_to_array($it, false)), "\n";   // bỏ key, đánh số lại 0, 1, 2
// in ra: [1,2,3]

echo iterator_count($it), "\n";            // in ra: 3   (đếm bằng cách duyệt hết)

iterator_apply($it, function () use ($it): bool {
    echo $it->current(), ' ';
    return true;                           // trả false để dừng sớm
}, []);
echo "\n";                                 // in ra: 1 2 3
```

- `iterator_to_array($it, preserve_keys: true)`: tham số thứ hai mặc định `true`. Khi giữ key mà hai
  phần tử trùng key thì phần tử sau ghi đè phần tử trước; đây là bẫy kinh điển với generator (mục 6.2).
- `iterator_count()` đếm bằng cách duyệt từ đầu tới cuối. Manual ghi rõ nó không giữ nguyên vị trí hiện
  tại của iterator. Với generator, đếm xong là generator đã chạy hết, không duyệt lại được.
- `iterator_apply()` hiếm khi cần, một vòng `foreach` dễ đọc hơn.
- Từ PHP 8.2, `iterator_to_array()` và `iterator_count()` nhận cả array (kiểu tham số mở rộng từ
  `Traversable` thành `Traversable|array`). PHP 8.1 trở xuống truyền array vào thì ném `TypeError`.

## 4. Generator: hàm biết tạm dừng

### 4.1 Generator là gì

*Generator* là một hàm có chứa từ khoá `yield`. Nó trông như hàm bình thường nhưng hành xử khác hẳn:

- Gọi hàm generator **không chạy thân hàm**. PHP chỉ tạo và trả về một object thuộc class có sẵn
  `Generator`.
- Object `Generator` là một `Iterator`. Mỗi khi có ai hỏi phần tử tiếp theo (thường là `foreach`), thân
  hàm chạy tiếp cho tới `yield` kế tiếp, đưa giá trị sau `yield` ra ngoài, rồi **tạm dừng** ngay tại đó.
- Lúc tạm dừng, mọi biến cục bộ của hàm vẫn được giữ nguyên. Lần hỏi sau, hàm chạy tiếp từ ngay sau
  `yield` đó, như chưa từng bị ngắt.
- Thân hàm chạy hết (hoặc gặp `return`) thì generator kết thúc, `foreach` dừng.

Manual PHP mô tả: generator cho bạn một cách dễ dàng để viết iterator đơn giản mà không phải viết cả
một class implement `Iterator`. Cách tốt nhất để thấy "tạm dừng" là in ra từng bước:

```php
<?php
declare(strict_types=1);

function countdown(int $from): Generator
{
    echo "  [bắt đầu chạy thân hàm]\n";
    for ($i = $from; $i > 0; $i--) {
        echo "  [trước yield $i]\n";
        yield $i;
        echo "  [sau yield $i]\n";
    }
    echo "  [kết thúc thân hàm]\n";
}

$gen = countdown(3);
echo "Đã gọi countdown(3), nhận về: ", $gen::class, "\n";

foreach ($gen as $n) {
    echo "foreach nhận $n\n";
}
echo "Xong\n";
// in ra:
// Đã gọi countdown(3), nhận về: Generator
//   [bắt đầu chạy thân hàm]
//   [trước yield 3]
// foreach nhận 3
//   [sau yield 3]
//   [trước yield 2]
// foreach nhận 2
//   [sau yield 2]
//   [trước yield 1]
// foreach nhận 1
//   [sau yield 1]
//   [kết thúc thân hàm]
// Xong
```

Để ý dòng đầu tiên: gọi `countdown(3)` xong mà `[bắt đầu chạy thân hàm]` chưa hề in. Thân hàm chỉ bắt
đầu chạy khi `foreach` hỏi phần tử đầu tiên.

### 4.2 Luồng điều khiển chạy qua lại

Với hàm thường, khi gọi hàm thì hàm chạy một mạch tới `return`. Với generator, quyền điều khiển chuyền
qua lại giữa code gọi và thân generator như hai người đánh bóng bàn:

| Bước | Code gọi (`foreach`) | Thân generator | Biến `$i` trong generator |
|---|---|---|---|
| 1 | `countdown(3)`: nhận object `Generator` | Chưa chạy | Chưa có |
| 2 | Bắt đầu `foreach`, hỏi phần tử đầu | Chạy từ đầu tới `yield 3`, dừng | 3 |
| 3 | Nhận 3, chạy thân vòng lặp | Đang dừng | 3 (vẫn giữ) |
| 4 | Hỏi phần tử tiếp | Chạy tiếp từ sau `yield 3`, `$i--`, tới `yield 2`, dừng | 2 |
| 5 | Nhận 2, chạy thân vòng lặp | Đang dừng | 2 |
| 6 | Hỏi phần tử tiếp | Chạy tới `yield 1`, dừng | 1 |
| 7 | Nhận 1, chạy thân vòng lặp | Đang dừng | 1 |
| 8 | Hỏi phần tử tiếp | Chạy tiếp, vòng `for` kết thúc, thân hàm hết | 0 |
| 9 | Không còn phần tử, thoát `foreach` | Đã kết thúc | Đã giải phóng |

Tại mọi thời điểm chỉ có một bên chạy. Không có gì song song ở đây: generator chỉ là một cách sắp xếp lại
thứ tự chạy code trong cùng một luồng.

**Bên trong engine.** Bình thường, mỗi lần gọi hàm, engine tạo một *stack frame* (vùng nhớ giữ tham số,
biến cục bộ, vị trí lệnh đang chạy) trên *VM stack* chung và bỏ nó đi khi hàm return. Generator thì phải
sống lâu hơn lời gọi hàm, nên mã nguồn của php-src (opcode `ZEND_GENERATOR_CREATE`) cấp phát frame của
hàm generator **trên heap** và gắn nó vào object `Generator`. Frame này tồn tại cùng object, nên biến cục
bộ không mất giữa các lần `yield`. Đó cũng là lý do một generator đang dừng tốn bộ nhớ đúng bằng frame của
nó (cộng các giá trị mà biến cục bộ đang giữ), không phụ thuộc nó sẽ sinh ra bao nhiêu phần tử. Chi tiết
engine ở [Chương 19](19-ben-trong-engine.md).

### 4.3 Generator là một `Iterator`

Class `Generator` là `final class Generator implements Iterator`. Nó có đủ năm method của `Iterator` cộng
ba method riêng:

| Method | Làm gì |
|---|---|
| `current(): mixed` | Giá trị của `yield` hiện tại. Nếu generator chưa chạy thì chạy tới `yield` đầu trước |
| `key(): mixed` | Key của `yield` hiện tại |
| `next(): void` | Chạy tiếp tới `yield` kế (tương đương `send(null)`, mục 7) |
| `valid(): bool` | `false` khi generator đã kết thúc |
| `rewind(): void` | Chạy tới `yield` đầu tiên nếu chưa chạy; đã đi quá `yield` đầu thì ném `Exception` |
| `send(mixed $value): mixed` | Đẩy một giá trị vào generator (mục 7) |
| `throw(Throwable $e): mixed` | Ném một exception vào generator tại chỗ nó đang dừng (mục 7) |
| `getReturn(): mixed` | Giá trị của `return` trong generator, sau khi nó đã kết thúc (mục 4.8) |

Có thể điều khiển generator bằng tay thay vì `foreach`:

```php
<?php
declare(strict_types=1);

function abc(): Generator
{
    yield 'a';
    yield 'b';
    yield 'c';
}

$g = abc();
var_dump($g->valid());                       // in ra: bool(true)   (lúc này mới chạy tới yield 'a')
echo $g->key(), ' => ', $g->current(), "\n"; // in ra: 0 => a
$g->next();
echo $g->key(), ' => ', $g->current(), "\n"; // in ra: 1 => b
$g->next();
$g->next();                                  // đi quá yield 'c', thân hàm kết thúc
var_dump($g->valid());                       // in ra: bool(false)
var_dump($g->current());                     // in ra: NULL
```

Object `Generator` chỉ được tạo bằng cách gọi hàm generator. Viết `new Generator()` ném
`Error: The "Generator" class is reserved for internal use and cannot be manually instantiated`.

### 4.4 Key của generator

Mỗi `yield` sinh ra một cặp key và value, giống phần tử của array:

- `yield $value;` thì key tự đánh số 0, 1, 2... như khi thêm vào array bằng `$a[] = ...`.
- `yield $key => $value;` thì tự chọn key.
- `yield;` (không có gì) thì value là `null`, key tự đánh số.

```php
<?php
declare(strict_types=1);

function keys(): Generator
{
    yield 'x';                  // key 0
    yield 'name' => 'An';       // key 'name'
    yield 'y';                  // key 1: bộ đếm tự động không bị key chuỗi ảnh hưởng
    yield 10 => 'z';            // key 10
    yield 'w';                  // key 11: như array, nối tiếp key số lớn nhất
    yield;                      // key 12, value null
}

foreach (keys() as $k => $v) {
    echo var_export($k, true), ' => ', var_export($v, true), "\n";
}
// in ra:
// 0 => 'x'
// 'name' => 'An'
// 1 => 'y'
// 10 => 'z'
// 11 => 'w'
// 12 => NULL
```

Ba điểm generator **khác** array:

- **Key không bị chuẩn hoá.** Trong array, key `'20'` tự thành số nguyên `20`
  ([Chương 06](06-mang.md)). Generator giữ nguyên: `yield '20' => 'd'` cho key là chuỗi `'20'`.
- **Key có thể là bất kỳ kiểu gì**, kể cả array hay object: `yield [1, 2] => 'x'` hợp lệ. `foreach` nhận
  đúng key đó. Array thì không có key kiểu array hay object.
- **Key được phép trùng.** `yield 'a' => 1; yield 'a' => 2;` thì `foreach` nhận đủ cả hai cặp. Chỉ khi
  chuyển sang array bằng `iterator_to_array()` (mặc định giữ key) thì cặp sau ghi đè cặp trước và bạn
  mất dữ liệu (mục 6.2).

### 4.5 Viết lại ví dụ phân trang bằng generator

Nhớ class `PagedUsers` ở mục 2.3 với năm method và bốn property trạng thái. Đây là cùng chức năng viết
bằng generator:

```php
<?php
declare(strict_types=1);

function fetchPage(int $page): array
{
    echo "  (tải trang $page)\n";
    $all = ['An', 'Bình', 'Chi', 'Dũng', 'Em'];
    return array_slice($all, ($page - 1) * 2, 2);
}

/** @return Generator<int, string> */
function pagedUsers(): Generator
{
    $page = 1;
    while (($rows = fetchPage($page)) !== []) {
        foreach ($rows as $name) {
            yield $name;      // key tự tăng 0, 1, 2... xuyên suốt các trang
        }
        $page++;
    }
}

foreach (pagedUsers() as $i => $name) {
    echo "$i: $name\n";
    if ($name === 'Chi') {
        break;
    }
}
// in ra:
//   (tải trang 1)
// 0: An
// 1: Bình
//   (tải trang 2)
// 2: Chi
```

Output giống hệt. Biến `$page` và vị trí trong `$rows` chính là trạng thái mà class `PagedUsers` phải tự
lưu vào property; ở đây chúng chỉ là biến cục bộ, generator tự giữ hộ giữa các lần dừng. Code đọc từ trên
xuống như một vòng lặp bình thường.

Bảng so sánh nhanh:

| | Class implement `Iterator` | Generator |
|---|---|---|
| Lượng code | Năm method, tự quản lý trạng thái | Một hàm |
| Duyệt lại (`rewind`) | Được, nếu bạn viết `rewind()` đúng | Không (mục 4.6) |
| Thêm method khác (`count()`, `seek()`...) | Được | Không, `Generator` là `final` |
| Nhận giá trị từ ngoài vào | Tự thiết kế | Có sẵn `send()` |
| Khi nào chọn | Cần duyệt lại, cần thêm hành vi | Phần lớn trường hợp còn lại |

### 4.6 Generator chỉ duyệt được một lần

Generator là iterator "chỉ đi tới" (*forward-only*). Manual nói rõ: không thể tua lại một generator khi
việc duyệt đã bắt đầu, nên cũng không thể duyệt cùng một generator nhiều lần; muốn duyệt lại thì gọi lại
hàm generator để có object mới.

```php
<?php
declare(strict_types=1);

function abc(): Generator
{
    yield 'a';
    yield 'b';
    return 'xong';
}

$g = abc();
foreach ($g as $v) { echo $v; }
echo "\n";                                   // in ra: ab

try {
    foreach ($g as $v) { echo $v; }          // duyệt lần hai
} catch (Exception $e) {
    echo $e->getMessage(), "\n";             // in ra: Cannot traverse an already closed generator
}

$g2 = abc();
$g2->current();                              // chạy tới yield đầu
$g2->rewind();                               // vẫn đang ở yield đầu: không làm gì, không lỗi
$g2->next();                                 // đi quá yield đầu
try {
    $g2->rewind();
} catch (Exception $e) {
    echo $e->getMessage(), "\n";             // in ra: Cannot rewind a generator that was already run
}
```

Hai lỗi đều là `Exception` thường (không phải class con riêng).

⚠️ Bẫy hay gặp: truyền một generator vào hàm, hàm đó duyệt nó (hoặc gọi `iterator_count()` để "đếm
trước"), rồi code gọi duyệt tiếp và nhận `Exception` hoặc không còn phần tử nào. Ba cách xử lý:

- Gọi lại hàm generator mỗi khi cần duyệt.
- Nhận một *callable trả về generator* thay vì nhận chính generator. Laravel làm vậy:
  `LazyCollection::make(function () { yield ...; })` nhận một hàm generator, và constructor của
  `LazyCollection` ném `InvalidArgumentException` ("Generators should not be passed directly to
  LazyCollection. Instead, pass a generator function.") nếu bạn truyền thẳng một object `Generator`.
- Bọc trong `IteratorAggregate` mà `getIterator()` là generator (mục 4.7): mỗi `foreach` gọi
  `getIterator()` một lần, tức là có generator mới.

### 4.7 `getIterator()` viết bằng generator

Đây là cách gọn nhất để một class "duyệt được": không cần class iterator riêng, không cần `ArrayIterator`,
lại tính toán được ngay trong lúc duyệt.

```php
<?php
declare(strict_types=1);

final class Order implements IteratorAggregate
{
    /** @var array<string, int> sku => số lượng */
    private array $lines = [];

    public function add(string $sku, int $qty): void
    {
        $this->lines[$sku] = ($this->lines[$sku] ?? 0) + $qty;
    }

    /** @return Generator<string, int> */
    public function getIterator(): Generator
    {
        foreach ($this->lines as $sku => $qty) {
            if ($qty > 0) {          // bỏ qua dòng có số lượng 0 ngay trong lúc duyệt
                yield $sku => $qty;
            }
        }
    }
}

$order = new Order();
$order->add('A1', 2);
$order->add('B2', 0);
$order->add('C3', 1);

foreach ($order as $sku => $qty) { echo "$sku x$qty "; }
echo "\n";                                    // in ra: A1 x2 C3 x1
foreach ($order as $sku => $qty) { echo "$sku x$qty "; }
echo "\n";                                    // in ra: A1 x2 C3 x1   (duyệt lại được)
```

### 4.8 `return` trong generator và `getReturn()`

Generator được phép có `return`. Giá trị `return` **không** được `foreach` nhận (nó không phải một phần
tử), mà được lấy riêng bằng `getReturn()` sau khi generator đã kết thúc. Dùng khi generator vừa sinh dữ
liệu vừa muốn báo một kết quả tổng kết, ví dụ số dòng lỗi đã bỏ qua.

```php
<?php
declare(strict_types=1);

/** @return Generator<int, int, mixed, int> */
function validNumbers(array $raw): Generator
{
    $skipped = 0;
    foreach ($raw as $item) {
        if (!is_int($item)) {
            $skipped++;
            continue;
        }
        yield $item;
    }
    return $skipped;
}

$gen = validNumbers([1, 'x', 2, null, 3]);
foreach ($gen as $n) {
    echo $n, ' ';
}
echo "\n";                                     // in ra: 1 2 3
echo "Bỏ qua: ", $gen->getReturn(), "\n";      // in ra: Bỏ qua: 2
```

- Gọi `getReturn()` khi generator chưa kết thúc ném
  `Exception: Cannot get return value of a generator that hasn't returned`.
- Generator kết thúc vì một exception bay ra khỏi thân hàm thì cũng không có giá trị trả về; gọi
  `getReturn()` lúc đó cũng ném exception.
- `return;` không kèm giá trị (hoặc chạy hết thân hàm) thì `getReturn()` trả `null`.
- PHPDoc `Generator<TKey, TValue, TSend, TReturn>` (bốn tham số: kiểu key, kiểu value, kiểu nhận qua
  `send()`, kiểu `return`) là quy ước của PHPStan và Psalm để mô tả đầy đủ một generator.

### 4.9 Khai báo và các dạng generator

**Kiểu trả về.** Hàm generator luôn trả về object `Generator`, nên kiểu trả về khai báo phải là kiểu
chứa được `Generator`: `Generator`, `Iterator`, `Traversable`, `iterable`, `object` hoặc `mixed`. Khai báo kiểu
khác thì lỗi ngay lúc biên dịch:

```php
function bad(): array { yield 1; }
// Fatal error: Generator return type must be a supertype of Generator, array given
```

Nên khai báo `Generator` (cụ thể nhất) cho hàm nội bộ. Với API công khai mà bạn muốn tự do đổi cài đặt
sau này (từ generator sang `ArrayIterator` chẳng hạn), khai báo `iterable` hoặc `Traversable`.

**Có `yield` ở đâu là thành generator ở đó.** Chỉ cần từ khoá `yield` xuất hiện ở bất kỳ chỗ nào trong
thân hàm, kể cả chỗ không bao giờ chạy tới, hàm đó là generator:

```php
<?php
declare(strict_types=1);

function onlyReturn(): Generator
{
    return 1;
    yield;              // không bao giờ chạy tới, nhưng vẫn biến hàm thành generator
}

$g = onlyReturn();
var_dump($g->valid());      // in ra: bool(false)
var_dump($g->getReturn());  // in ra: int(1)
```

**Generator ở mọi dạng hàm.** Method, static method, closure và cả arrow function đều có thể là generator:

```php
<?php
declare(strict_types=1);

final class Box
{
    public static function items(): Generator { yield 7; }
    public function each(): Generator { yield 8; }
}

$closure = function (): Generator { yield 6; };
$arrow = fn() => yield 5;

echo Box::items()->current(), (new Box())->each()->current(), $closure()->current(), $arrow()->current(), "\n";
// in ra: 7865
```

### 4.10 Generator lười: lỗi đến muộn

*Lazy* (lười) là ưu điểm lớn nhất của generator, nhưng nó có một mặt trái: **mọi** code trong thân hàm
đều chạy muộn, kể cả đoạn kiểm tra tham số đặt ở đầu hàm.

```php
<?php
declare(strict_types=1);

function chunked(array $items, int $size): Generator
{
    if ($size < 1) {
        throw new InvalidArgumentException('size phải >= 1');
    }
    foreach (array_chunk($items, $size) as $chunk) {
        yield $chunk;
    }
}

$batches = chunked([1, 2, 3], 0);     // KHÔNG ném gì ở đây
echo "Đã tạo generator, chưa có lỗi\n";
try {
    foreach ($batches as $b) {}       // lỗi chỉ xuất hiện khi bắt đầu duyệt
} catch (InvalidArgumentException $e) {
    echo "Lỗi lúc duyệt: ", $e->getMessage(), "\n";
}
// in ra:
// Đã tạo generator, chưa có lỗi
// Lỗi lúc duyệt: size phải >= 1
```

Hậu quả thực tế: generator được tạo ở controller nhưng chỉ được duyệt sâu trong một job hay một view, lỗi
xuất hiện ở chỗ chẳng liên quan gì tới nơi truyền tham số sai, stack trace khó đọc. Cách sửa: tách làm
hai hàm, hàm ngoài là hàm thường kiểm tra ngay, hàm trong là generator.

```php
<?php
declare(strict_types=1);

function chunkedSafe(array $items, int $size): Generator
{
    if ($size < 1) {
        throw new InvalidArgumentException('size phải >= 1');   // ném ngay khi gọi
    }
    return (function () use ($items, $size): Generator {
        foreach (array_chunk($items, $size) as $chunk) {
            yield $chunk;
        }
    })();
}

try {
    $batches = chunkedSafe([1, 2, 3], 0);
} catch (InvalidArgumentException $e) {
    echo "Lỗi ngay khi gọi: ", $e->getMessage(), "\n";   // in ra: Lỗi ngay khi gọi: size phải >= 1
}
```

`chunkedSafe` không chứa `yield` nên là hàm thường; nó trả về generator do closure bên trong tạo ra.

Lưu ý: **kiểu tham số** thì vẫn được kiểm tra ngay lúc gọi, không lười. Với
`function gen(int $n): Generator`, gọi `gen('5')` dưới `strict_types` ném `TypeError` ngay tại dòng gọi.
Chỉ phần thân hàm mới chạy muộn.

### 4.11 `try`/`finally` trong generator: dọn dẹp tài nguyên

Generator hay giữ tài nguyên: file đang mở, kết nối, lock. Phải đóng chúng kể cả khi người dùng không
duyệt hết (gặp `break`, hoặc exception). Đặt `yield` trong `try` và dọn dẹp trong `finally`. Khi object
generator bị huỷ (không còn biến nào trỏ tới nó) trong lúc đang dừng giữa chừng, PHP chạy các khối
`finally` đang bao quanh điểm dừng.

```php
<?php
declare(strict_types=1);

function resource(): Generator
{
    echo "  mở tài nguyên\n";
    try {
        yield 1;
        yield 2;
        yield 3;
    } finally {
        echo "  đóng tài nguyên\n";
    }
}

echo "A. break sớm, generator tạm:\n";
foreach (resource() as $x) { echo "  nhận $x\n"; break; }
echo "A xong\n";

echo "B. break sớm, generator nằm trong biến:\n";
$g = resource();
foreach ($g as $x) { echo "  nhận $x\n"; break; }
echo "B: sau vòng lặp, \$g vẫn còn sống\n";
unset($g);
echo "B xong\n";

echo "C. exception trong thân foreach:\n";
try {
    foreach (resource() as $x) { throw new RuntimeException('lỗi'); }
} catch (RuntimeException $e) {
    echo "  bắt được: ", $e->getMessage(), "\n";
}
// in ra:
// A. break sớm, generator tạm:
//   mở tài nguyên
//   nhận 1
//   đóng tài nguyên
// A xong
// B. break sớm, generator nằm trong biến:
//   mở tài nguyên
//   nhận 1
// B: sau vòng lặp, $g vẫn còn sống
//   đóng tài nguyên
// B xong
// C. exception trong thân foreach:
//   mở tài nguyên
//   đóng tài nguyên
//   bắt được: lỗi
```

- Trường hợp A: object generator chỉ do `foreach` giữ, thoát vòng lặp là bị huỷ ngay, `finally` chạy
  ngay.
- Trường hợp B: biến `$g` còn giữ generator nên tài nguyên **chưa** được đóng sau `break`. Nó chỉ đóng
  khi `$g` bị `unset`, bị gán giá trị khác, hoặc khi hết hàm hay hết script. Trong worker chạy lâu
  (queue worker, Octane), giữ generator dở dang trong một property là cách rò rỉ file handle.
- Trường hợp C: exception làm generator tạm bị huỷ trên đường đi ra, nên `finally` chạy trước khối
  `catch` bên ngoài.

Nếu chính thân generator ném exception (không bắt bên trong), exception bay ra chỗ code đang gọi
`foreach`/`next()`, và generator chuyển sang trạng thái kết thúc (`valid()` trả `false`).

## 5. Dùng generator để xử lý dữ liệu lớn

### 5.1 Bài toán và con số

Tính tổng các số từ 1 tới một triệu theo hai cách: tạo array bằng `range()` rồi duyệt, và sinh từng số
bằng generator.

```php
<?php
declare(strict_types=1);

$base = memory_get_usage();
$sum = 0;
foreach (range(1, 1_000_000) as $n) {
    $sum += $n;
}
echo round((memory_get_peak_usage() - $base) / 1024 / 1024, 1), " MiB\n";
// output minh hoạ (php-wasm 32-bit, PHP 8.5): 16.1 MiB
```

```php
<?php
declare(strict_types=1);

function numbers(int $n): Generator
{
    for ($i = 1; $i <= $n; $i++) {
        yield $i;
    }
}

$base = memory_get_usage();
$sum = 0;
foreach (numbers(1_000_000) as $n) {
    $sum += $n;
}
echo round((memory_get_peak_usage() - $base) / 1024, 1), " KiB\n";
// output minh hoạ (php-wasm 32-bit, PHP 8.5): 35.6 KiB
```

Chạy hai file riêng (đỉnh bộ nhớ `memory_get_peak_usage()` là của cả script, chạy chung một file thì
số đo thứ hai bị số đo thứ nhất che). Hai con số trên đo bằng một bản PHP biên dịch sang WebAssembly 32-bit
(con trỏ 4 byte), trên máy 64-bit thật sẽ khác đôi chút. Con số cụ thể thay đổi theo bản PHP và nền tảng, điều đáng chú ý
là **xu hướng** khi đổi `1_000_000` thành `10_000_000`:

- Cách `range()` chết luôn với `memory_limit` mặc định `128M`. Output minh hoạ (php-wasm 32-bit):
  `Fatal error: Allowed memory size of 134217728 bytes exhausted (tried to allocate 268435464 bytes)`.
  Array mười triệu số nguyên cần cỡ 256 MiB (số ô được làm tròn lên lũy thừa của 2).
- Cách generator vẫn đứng yên ở đúng con số cũ.

Bộ nhớ của generator không phụ thuộc số phần tử, vì tại mỗi thời điểm chỉ có một phần tử tồn tại.

Quy tắc ngón tay cái: khi dữ liệu chỉ cần **đi qua một lượt** (đọc, biến đổi, ghi đi chỗ khác), đừng gom
nó vào array. Hãy để từng phần tử chảy qua.

### 5.2 Đọc file lớn từng dòng

`file()` hay `file_get_contents()` đọc cả file vào bộ nhớ: file log 5 GB là chết. Đọc từng dòng bằng
`fgets()` và bọc trong generator thì bộ nhớ chỉ giữ một dòng. Chi tiết về file và stream ở
[Chương 14](14-file-json-thoi-gian.md); ở đây chỉ cần khung generator:

```php
<?php
declare(strict_types=1);

/** @return Generator<int, string> số dòng => nội dung dòng */
function readLines(string $path): Generator
{
    $handle = fopen($path, 'rb');
    if ($handle === false) {
        throw new RuntimeException("Không mở được $path");
    }
    try {
        $lineNo = 0;
        while (($line = fgets($handle)) !== false) {
            yield ++$lineNo => rtrim($line, "\r\n");
        }
    } finally {
        fclose($handle);   // chạy cả khi người dùng break sớm hoặc có exception (mục 4.11)
    }
}

// Tạo một file log mẫu để thử
$path = sys_get_temp_dir() . '/app.log';
file_put_contents($path, "INFO khởi động\nERROR mất kết nối DB\nINFO request /home\nERROR timeout\n");

foreach (readLines($path) as $no => $line) {
    if (str_starts_with($line, 'ERROR')) {
        echo "Dòng $no: $line\n";
    }
}
unlink($path);
// in ra:
// Dòng 2: ERROR mất kết nối DB
// Dòng 4: ERROR timeout
```

Lưu ý: kiểm tra `fopen()` và mở file nằm trong thân generator, nên theo mục 4.10 lỗi "không mở được
file" chỉ xuất hiện lúc bắt đầu duyệt. Nếu cần báo lỗi sớm, dùng cách tách hai hàm ở mục 4.10.

### 5.3 Pipeline lười: lọc, biến đổi, lấy n phần tử

`array_filter`, `array_map` làm việc trên array: mỗi bước tạo ra một array mới đầy đủ. Với generator ta
viết được các bước tương tự nhưng lười, mỗi bước nhận một `iterable` và trả về một generator:

```php
<?php
declare(strict_types=1);

function filterLazy(iterable $items, callable $keep): Generator
{
    foreach ($items as $key => $item) {
        if ($keep($item)) {
            yield $key => $item;
        }
    }
}

function mapLazy(iterable $items, callable $fn): Generator
{
    foreach ($items as $key => $item) {
        yield $key => $fn($item);
    }
}

function take(iterable $items, int $n): Generator
{
    if ($n <= 0) {
        return;
    }
    foreach ($items as $key => $item) {
        yield $key => $item;
        if (--$n === 0) {
            return;      // đủ n phần tử thì dừng, không hỏi nguồn thêm phần tử nào
        }
    }
}

function source(): Generator
{
    for ($i = 1; ; $i++) {          // dãy VÔ HẠN 1, 2, 3...
        echo "[sinh $i] ";
        yield $i;
    }
}

$result = take(
    mapLazy(
        filterLazy(source(), function (int $n): bool { echo "[lọc $n] "; return $n % 2 === 0; }),
        function (int $n): int { echo "[nhân $n] "; return $n * 10; },
    ),
    3,
);
echo "Chưa có gì chạy\n";

foreach ($result as $v) {
    echo "=> $v\n";
}
// in ra:
// Chưa có gì chạy
// [sinh 1] [lọc 1] [sinh 2] [lọc 2] [nhân 2] => 20
// [sinh 3] [lọc 3] [sinh 4] [lọc 4] [nhân 4] => 40
// [sinh 5] [lọc 5] [sinh 6] [lọc 6] [nhân 6] => 60
```

Ba điều đáng chú ý trong output:

1. Tạo cả chuỗi `take(mapLazy(filterLazy(source())))` không chạy gì cả.
2. Mỗi phần tử đi **hết cả chuỗi** rồi phần tử sau mới bắt đầu: số 2 được sinh, lọc, nhân, in ra, rồi mới
   tới số 3. Với `array_filter` + `array_map`, toàn bộ phần tử được lọc xong rồi mới bắt đầu nhân.
3. Nguồn là dãy vô hạn mà chương trình vẫn dừng: `take` đủ 3 phần tử thì `return`, không ai hỏi nguồn số
   7 nữa. Với array thì không thể có "array vô hạn".

```
 foreach hỏi ──► take ──► mapLazy ──► filterLazy ──► source
                                                       │ yield 1
                                filterLazy: bỏ ◄───────┘
                                filterLazy hỏi tiếp ──► source
                                                       │ yield 2
               mapLazy ◄──── filterLazy: giữ ◄─────────┘
   take ◄──── mapLazy: 20
 foreach ◄── take: 20
```

Trên PHP 8.5, toán tử pipe `|>` ([Chương 08](08-ham.md)) giúp viết chuỗi này theo thứ tự đọc từ trái
sang phải thay vì lồng từ trong ra ngoài:

```php
$result = source()
    |> (fn(iterable $it) => filterLazy($it, fn(int $n): bool => $n % 2 === 0))
    |> (fn(iterable $it) => mapLazy($it, fn(int $n): int => $n * 10))
    |> (fn(iterable $it) => take($it, 3));

echo implode(', ', iterator_to_array($result, false)), "\n";
// in ra: [sinh 1] [sinh 2] [sinh 3] [sinh 4] [sinh 5] [sinh 6] 20, 40, 60
// (các "[sinh n]" do source() in ra; hai closure lọc/nhân ở đây không in gì)
```

Đây cũng chính là ý tưởng của `LazyCollection` trong Laravel: các method `filter()`, `map()`, `take()`
của nó trả về một `LazyCollection` mới bọc generator, chưa chạy gì cho tới khi bạn duyệt.

### 5.4 Đọc database từng dòng

Cùng khung đó áp dụng cho kết quả query: thay vì `fetchAll()` (trả cả array mọi dòng), lấy từng dòng bằng
`fetch()` và `yield` nó. Ví dụ dưới dùng SQLite trong bộ nhớ để tự chạy được; PDO sẽ được học kỹ ở
[Chương 16](16-php-va-database.md).

```php
<?php
declare(strict_types=1);

/** @return Generator<int, array{id: int, email: string}> */
function users(PDO $pdo): Generator
{
    $stmt = $pdo->query('SELECT id, email FROM users ORDER BY id');
    while (($row = $stmt->fetch(PDO::FETCH_ASSOC)) !== false) {
        yield $row;   // mỗi lần chỉ một dòng nằm trong biến PHP
    }
}

$pdo = new PDO('sqlite::memory:', options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION]);
$pdo->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT NOT NULL)');
$insert = $pdo->prepare('INSERT INTO users (email) VALUES (?)');
foreach (['an@x.vn', 'binh@x.vn', 'chi@x.vn'] as $email) {
    $insert->execute([$email]);
}

foreach (users($pdo) as $row) {
    echo $row['id'], ' ', $row['email'], "\n";
}
// in ra:
// 1 an@x.vn
// 2 binh@x.vn
// 3 chi@x.vn
```

⚠️ **Với MySQL, generator một mình chưa đủ.** Driver MySQL của PHP mặc định dùng *buffered query*: ngay
khi query chạy xong, toàn bộ kết quả được chuyển từ MySQL server về và **nằm trong bộ nhớ của process
PHP**; `fetch()` chỉ đọc từ bộ đệm đó. Manual ghi rõ với `mysqlnd` (driver mặc định), bộ nhớ của cả result
set được tính vào `memory_limit`. Nghĩa là `users()` ở trên chạy với MySQL vẫn giữ cả triệu dòng trong
RAM, chỉ đỡ được phần chuyển mỗi dòng thành array PHP.

Hai hướng xử lý:

- *Unbuffered query*: tắt buffer cho kết nối (`Pdo\Mysql::ATTR_USE_BUFFERED_QUERY => false` từ PHP 8.4;
  hằng cũ `PDO::MYSQL_ATTR_USE_BUFFERED_QUERY` bị deprecated từ 8.5). Dòng được kéo về dần khi `fetch()`.
  Cái giá: chưa đọc hết kết quả thì không chạy được query khác trên cùng kết nối, và không biết trước số
  dòng.
- *Chia lô theo khoá* (*keyset pagination*): mỗi lần query một lô `WHERE id > :lastId ORDER BY id LIMIT
  1000`, generator `yield` từng dòng của lô rồi query lô tiếp. Mỗi query nhỏ, bộ nhớ chỉ giữ một lô. Đây
  là cách an toàn và phổ biến hơn.

Laravel có sẵn cả hai, đều trả về `LazyCollection` dựa trên generator
([Chương 27](27-laravel-database-eloquent.md)):

| Method | Cách lấy dữ liệu | Ghi chú theo tài liệu Laravel |
|---|---|---|
| `cursor()` | Một query duy nhất, mỗi lần dựng một model | Chỉ giữ một model trong bộ nhớ, nhưng vẫn có thể hết bộ nhớ vì PDO đệm toàn bộ kết quả thô; không eager load quan hệ được |
| `lazy()` | Chạy query theo từng lô (chunk) phía sau, trả ra một luồng model phẳng | Dùng khi dữ liệu rất lớn |
| `lazyById()` | Như `lazy()` nhưng lô sau lấy theo `id` lớn hơn model cuối của lô trước | Dùng khi vừa duyệt vừa cập nhật chính cột đang lọc |
| `chunk()`, `chunkById()` | Chạy query theo lô, gọi callback cho mỗi lô | Không trả về `LazyCollection` |

### 5.5 Khi generator không giúp gì

Generator chỉ tiết kiệm bộ nhớ khi bạn **không gom** các phần tử lại. Những việc sau phá vỡ lợi ích đó:

- Gọi `iterator_to_array($gen)`: tạo lại đúng array mà bạn cố tránh.
- `$all[] = $row;` trong vòng `foreach`: cũng là gom lại.
- Sắp xếp, đảo ngược, lấy phần tử cuối, đếm trước rồi mới xử lý: bản chất các việc này cần thấy toàn bộ dữ
  liệu. Hãy đẩy chúng xuống tầng database (`ORDER BY`, `COUNT(*)`) thay vì làm trong PHP.
- Truy cập ngẫu nhiên kiểu "phần tử thứ 500": generator chỉ đi tới, không nhảy cóc được.

Và generator có chi phí: mỗi phần tử đi qua một lần chuyển ngữ cảnh vào ra thân generator. Với vài trăm
phần tử đã nằm sẵn trong array, `foreach` thẳng trên array đơn giản và nhanh hơn. Generator đáng dùng
khi dữ liệu lớn, sinh ra dần, hoặc có thể dừng sớm.

## 6. `yield from`: uỷ quyền cho nguồn khác

### 6.1 Cú pháp và ý nghĩa

`yield from <nguồn>` lần lượt `yield` ra mọi phần tử của nguồn đó, rồi chạy tiếp phần còn lại của
generator ngoài. Nguồn có thể là array, bất kỳ `Traversable` nào, hoặc một generator khác. Nó tương
đương (gần đúng) với:

```php
foreach ($nguon as $k => $v) {
    yield $k => $v;
}
```

nhưng có thêm hai điều mà vòng `foreach` tự viết không có: giá trị của biểu thức `yield from` là giá trị
`return` của generator con, và `send()`/`throw()` từ ngoài được chuyển thẳng vào generator con (mục 7).

```php
<?php
declare(strict_types=1);

function inner(): Generator
{
    yield 3;
    yield 4;
    return 'inner xong';
}

function outer(): Generator
{
    yield 1;
    yield from [2];                       // uỷ quyền cho array
    $r = yield from inner();              // uỷ quyền cho generator, nhận giá trị return của nó
    echo "[inner trả về: $r]\n";
    yield from new ArrayIterator([5]);    // uỷ quyền cho Traversable bất kỳ
    yield 6;
}

foreach (outer() as $k => $v) {
    echo "$k=>$v\n";
}
// in ra:
// 0=>1
// 0=>2
// 0=>3
// 1=>4
// [inner trả về: inner xong]
// 0=>5
// 1=>6
```

Giá trị thì đúng thứ tự 1 tới 6. Nhưng hãy nhìn cột key.

### 6.2 Bẫy: `yield from` giữ nguyên key

`yield from` **không đánh số lại key**: nó chuyển nguyên key của nguồn ra ngoài. Array `[2]` có key 0,
generator `inner()` có key 0 và 1, `ArrayIterator([5])` có key 0. Còn `yield 6` của `outer()` lấy key
tiếp theo từ bộ đếm riêng của `outer()` (đã dùng 0 cho `yield 1`, nên giờ là 1).

`foreach` không quan tâm key trùng. Nhưng `iterator_to_array()` mặc định giữ key, key trùng thì phần tử
sau ghi đè phần tử trước:

```php
var_dump(iterator_to_array(outer()));
// in ra (bỏ dòng [inner trả về...]):
// array(2) {
//   [0]=>
//   int(5)
//   [1]=>
//   int(6)
// }

echo json_encode(iterator_to_array(outer(), false)), "\n";
// in ra (bỏ dòng [inner trả về...]): [1,2,3,4,5,6]
```

Sáu phần tử thành hai, không có lỗi hay cảnh báo nào. Manual có một mục "Caution" riêng cho đúng chuyện
này. Quy tắc: khi gom generator có `yield from` (hoặc có key tự chọn) vào array, luôn cân nhắc
`iterator_to_array($gen, false)`, trừ khi bạn thật sự cần key và biết chắc chúng không trùng.

### 6.3 Ví dụ: duyệt cây đệ quy

`yield from` toả sáng khi duyệt cấu trúc đệ quy (cây danh mục, cây thư mục, cây comment): mỗi lời gọi
đệ quy là một generator, `yield from` nối chúng thành một dòng phẳng.

```php
<?php
declare(strict_types=1);

final class Category
{
    /** @param list<Category> $children */
    public function __construct(
        public readonly string $name,
        public readonly array $children = [],
    ) {}
}

/**
 * Duyệt cây theo chiều sâu, trả về đường dẫn => tên.
 * @return Generator<string, string>
 */
function walk(Category $node, string $prefix = ''): Generator
{
    $path = $prefix === '' ? $node->name : "$prefix > {$node->name}";
    yield $path => $node->name;
    foreach ($node->children as $child) {
        yield from walk($child, $path);   // đệ quy: uỷ quyền cho generator của cây con
    }
}

$tree = new Category('Điện tử', [
    new Category('Điện thoại', [
        new Category('Android'),
        new Category('iPhone'),
    ]),
    new Category('Laptop'),
]);

foreach (walk($tree) as $path => $name) {
    echo $path, "\n";
}
// in ra:
// Điện tử
// Điện tử > Điện thoại
// Điện tử > Điện thoại > Android
// Điện tử > Điện thoại > iPhone
// Điện tử > Laptop
```

Không cần truyền một array kết quả qua các lời gọi đệ quy, không cần gom rồi `array_merge`. Người dùng
`walk()` còn có thể `break` sớm khi tìm thấy thứ cần tìm, phần cây còn lại không bị duyệt.

Ở đây key là đường dẫn, mỗi nút một đường dẫn khác nhau nên không trùng. Nếu đổi thành `yield $node->name`
(key tự đánh số) thì mỗi generator con lại đếm từ 0, và `iterator_to_array(walk($tree))` sẽ mất phần tử
như mục 6.2.

## 7. Generator hai chiều: `send()`, `throw()` và coroutine

### 7.1 `yield` là một biểu thức

Tới giờ dữ liệu chỉ đi một chiều: từ generator ra ngoài. Nhưng `yield` thực ra là một *biểu thức* có
giá trị, và giá trị đó do code bên ngoài quyết định:

```php
$received = yield $outgoing;
```

- `$outgoing` đi **ra**: code gọi nhận được qua `current()` hoặc giá trị trả về của `send()`.
- `$received` đi **vào**: khi generator được đánh thức bằng `$gen->send($x)` thì `yield` có giá trị `$x`.
  Đánh thức bằng `next()` (hoặc bằng `foreach`) thì `yield` có giá trị `null`.

Một generator vừa đưa ra vừa nhận vào như vậy là một *coroutine*: hai đoạn code chạy xen kẽ, chủ động
chuyển quyền điều khiển cho nhau và trao đổi dữ liệu mỗi lần chuyển.

### 7.2 `send()`

Ví dụ đơn giản nhất: generator chỉ nhận vào, không đưa ra gì (`yield` không có giá trị).

```php
<?php
declare(strict_types=1);

function logger(): Generator
{
    echo "[logger sẵn sàng]\n";
    while (true) {
        $message = yield;          // dừng ở đây, chờ ai đó send() một giá trị vào
        echo "LOG: $message\n";
    }
}

$log = logger();
$log->send('khởi động');
$log->send('xử lý đơn #42');
// in ra:
// [logger sẵn sàng]
// LOG: khởi động
// LOG: xử lý đơn #42
```

Vòng `while (true)` không treo chương trình vì mỗi vòng dừng ở `yield`. Generator này chỉ chạy khi có
người `send()`.

Ví dụ hai chiều: tính trung bình cộng dồn. Mỗi lần gửi một số vào, nhận lại trung bình mới.

```php
<?php
declare(strict_types=1);

/** @return Generator<int, float, float, void> */
function runningAverage(): Generator
{
    $sum = 0.0;
    $count = 0;
    $average = 0.0;
    while (true) {
        $value = yield $average;   // đưa trung bình hiện tại RA, nhận số mới VÀO
        $sum += $value;
        $count++;
        $average = $sum / $count;
    }
}

$avg = runningAverage();
echo $avg->current(), "\n";        // in ra: 0    (chạy tới yield đầu, trung bình ban đầu)
echo $avg->send(10.0), "\n";       // in ra: 10
echo $avg->send(20.0), "\n";       // in ra: 15
echo $avg->send(60.0), "\n";       // in ra: 30
```

Trạng thái (`$sum`, `$count`) nằm gọn trong biến cục bộ, không cần class.

**Quy tắc chính xác của `send($x)`**, theo manual:

1. Nếu generator chưa chạy tới `yield` nào, nó được cho chạy tới `yield` đầu tiên trước.
2. Giá trị `$x` trở thành kết quả của biểu thức `yield` hiện tại, và generator chạy tiếp.
3. Generator chạy tới `yield` kế tiếp (hoặc kết thúc). `send()` trả về giá trị của `yield` mới đó (hoặc
   `null` nếu generator đã kết thúc).

Manual nói thêm: nhờ quy tắc 1 mà không cần "mồi" (*prime*) generator bằng `next()` trước khi `send()`
như trong Python. Nhưng quy tắc 1 có một hệ quả dễ bỏ sót:

```php
<?php
declare(strict_types=1);

function trace(): Generator
{
    echo "  bắt đầu\n";
    $a = yield 'y1';
    echo "  nhận a = ", var_export($a, true), "\n";
    $b = yield 'y2';
    echo "  nhận b = ", var_export($b, true), "\n";
    return 'hết';
}

$t = trace();
$r = $t->send('A');      // generator chưa chạy: chạy tới yield 'y1', rồi mới gửi 'A'
echo "send('A') trả về: ", var_export($r, true), "\n";
$r = $t->send('B');
echo "send('B') trả về: ", var_export($r, true), "\n";
echo $t->getReturn(), "\n";
// in ra:
//   bắt đầu
//   nhận a = 'A'
// send('A') trả về: 'y2'
//   nhận b = 'B'
// send('B') trả về: NULL
// hết
```

⚠️ Giá trị `'y1'` của `yield` đầu tiên **không ai nhận được**: `send('A')` chạy qua nó rồi trả về `'y2'`.
Nếu `yield` đầu mang thông tin quan trọng (như trung bình ban đầu ở ví dụ trên), hãy đọc nó bằng
`current()` trước khi `send()` lần đầu.

Còn nếu duyệt generator này bằng `foreach` thì mọi `yield` nhận `null`, vì `foreach` đánh thức generator
bằng `next()`, tương đương `send(null)`:

```php
foreach (trace() as $v) { echo "foreach nhận $v\n"; }
// in ra:
//   bắt đầu
// foreach nhận y1
//   nhận a = NULL
// foreach nhận y2
//   nhận b = NULL
```

### 7.3 `throw()`: ném exception vào trong generator

`$gen->throw($e)` đánh thức generator, nhưng thay vì `yield` trả về một giá trị thì tại đúng chỗ `yield`
đang dừng, exception `$e` bị ném ra. Generator có thể bắt nó bằng `try`/`catch` quanh `yield`:

```php
<?php
declare(strict_types=1);

function worker(): Generator
{
    while (true) {
        try {
            $job = yield;
            echo "  làm job: $job\n";
        } catch (RuntimeException $e) {
            echo "  worker nhận lỗi: ", $e->getMessage(), ", chờ job tiếp\n";
        }
    }
}

$w = worker();
$w->send('gửi mail');
$w->throw(new RuntimeException('job trước bị huỷ'));
$w->send('resize ảnh');
// in ra:
//   làm job: gửi mail
//   worker nhận lỗi: job trước bị huỷ, chờ job tiếp
//   làm job: resize ảnh
```

- Generator không bắt thì exception bay ngược ra chỗ gọi `throw()`, và generator kết thúc (`valid()` trả
  `false`).
- Gọi `throw()` trên generator đã kết thúc thì manual ghi: exception được ném ngay trong ngữ cảnh của
  code gọi.
- Giống `send()`, `throw()` trả về giá trị của `yield` kế tiếp mà generator dừng lại.

### 7.4 `yield from` chuyển tiếp hai chiều

Khi generator ngoài đang ở trong `yield from inner()`, mọi `send()` và `throw()` gửi tới generator ngoài
được chuyển thẳng tới `inner()`. Khi `inner()` `return`, giá trị đó là kết quả của biểu thức `yield from`:

```php
<?php
declare(strict_types=1);

function innerG(): Generator
{
    $x = yield 'inner hỏi';
    echo "  inner nhận $x\n";
    return $x * 2;
}

function outerG(): Generator
{
    $r = yield from innerG();
    echo "  outer nhận return $r\n";
    yield 'outer xong';
}

$o = outerG();
echo $o->current(), "\n";    // in ra: inner hỏi
echo $o->send(21), "\n";
// in ra:
//   inner nhận 21
//   outer nhận return 42
// outer xong
```

Nhờ vậy một coroutine lớn được chia thành nhiều coroutine nhỏ, mỗi cái là một hàm riêng, ghép lại bằng
`yield from` như gọi hàm.

### 7.5 Coroutine và đa nhiệm hợp tác

Ghép các mảnh trên lại, ta tự viết được một bộ lập lịch nhỏ chạy xen kẽ nhiều "task". Mỗi task là một
generator, mỗi `yield` nghĩa là "tôi nhường lượt":

```php
<?php
declare(strict_types=1);

function task(string $name, int $steps): Generator
{
    for ($i = 1; $i <= $steps; $i++) {
        echo "$name bước $i\n";
        yield;
    }
}

/** Bộ lập lịch round-robin: lần lượt cho mỗi task chạy tới yield kế tiếp. */
function runAll(Generator ...$tasks): void
{
    $queue = new SplQueue();       // hàng đợi vào trước ra trước, mục 9.2
    foreach ($tasks as $t) {
        $t->current();             // cho task chạy tới yield đầu tiên
        $queue->enqueue($t);
    }
    while (!$queue->isEmpty()) {
        $t = $queue->dequeue();
        $t->next();                // cho task chạy tiếp tới yield kế
        if ($t->valid()) {
            $queue->enqueue($t);   // chưa xong thì xếp lại cuối hàng
        }
    }
}

runAll(task('A', 3), task('B', 2));
// in ra:
// A bước 1
// B bước 1
// A bước 2
// B bước 2
// A bước 3
```

Đây gọi là *đa nhiệm hợp tác* (*cooperative multitasking*): các task tự nguyện nhường nhau, không ai bị
cưỡng chế dừng. Nếu thay "nhường lượt" bằng "tôi đang chờ socket này có dữ liệu", và bộ lập lịch chỉ đánh
thức task khi socket sẵn sàng, ta có nền móng của lập trình bất đồng bộ (*async*): trong lúc task A chờ
database trả lời, task B được chạy.

Trước PHP 8.1, các thư viện async như AMPHP (bản 2) xây dựng đúng theo cách này, trên generator: code
viết `$response = yield $http->request(...)`, tức là `yield` ra một *promise* (lời hứa về một kết quả
sẽ có sau). Thư viện chờ promise hoàn thành rồi `send()` kết quả vào generator, hoặc `throw()` exception
vào nếu thất bại. Đó chính là `send()` và `throw()` vừa học. Nhưng generator có một giới hạn gốc rễ: **chỉ chính hàm chứa `yield` mới tạm dừng được**. Nếu task gọi hàm
`fetchUser()`, và `fetchUser()` gọi `query()`, và `query()` mới là chỗ phải chờ, thì `query()`,
`fetchUser()` và task đều phải là generator, và mọi chỗ gọi phải đổi thành `yield from` hoặc `yield`.
Chỉ một hàm ở đáy cần chờ là cả chuỗi lời gọi phía trên phải đổi theo. RFC Fibers gọi đây là bài toán
"*What color is your function?*" (hàm của bạn màu gì): hàm async và hàm thường thành hai "màu" không gọi
lẫn nhau tự do được. Fiber ra đời để xoá ranh giới này (mục 10).

## 8. SPL và các iterator có sẵn

### 8.1 SPL là gì

*SPL* (*Standard PHP Library*) là một extension thuộc lõi PHP, có sẵn mà không cần cài thêm. Theo manual,
nó định nghĩa các interface và class để giải các bài toán thường gặp. Các nhóm chính:

| Nhóm | Ví dụ | Học ở đâu |
|---|---|---|
| Interface | `SeekableIterator`, `RecursiveIterator`, `OuterIterator`, `SplObserver`/`SplSubject` | Mục này |
| Cấu trúc dữ liệu | `SplStack`, `SplQueue`, `SplHeap`, `SplPriorityQueue`, `SplFixedArray`, `SplObjectStorage`, `ArrayObject` | Mục 9 |
| Exception | `LogicException`, `RuntimeException`, `InvalidArgumentException`, `OutOfBoundsException`... | [Chương 12](12-loi-exception.md) |
| Iterator | `ArrayIterator`, `LimitIterator`, `CallbackFilterIterator`, `RecursiveIteratorIterator`... | Mục này |
| File | `SplFileInfo`, `SplFileObject`, `DirectoryIterator`, `RecursiveDirectoryIterator` | [Chương 14](14-file-json-thoi-gian.md) |

Ngoài ra SPL có các hàm tiện ích: `iterator_to_array`, `iterator_count`, `iterator_apply` (mục 3.4),
`spl_autoload_register` ([Chương 11](11-namespace-composer.md)), `spl_object_id` và `spl_object_hash`.

### 8.2 Các iterator có sẵn

SPL có sẵn khoảng hai chục class iterator. Phần lớn là iterator *bọc* (*decorator*): nhận một iterator
khác ở constructor và thay đổi cách duyệt nó. Bảng các class hay dùng:

| Class | Làm gì |
|---|---|
| `ArrayIterator` | Duyệt một array (mục 9.7) |
| `IteratorIterator` | Bọc bất kỳ `Traversable` nào thành một `Iterator` đầy đủ |
| `LimitIterator` | Bỏ qua `offset` phần tử đầu, lấy tối đa `limit` phần tử (giống `OFFSET`/`LIMIT` của SQL) |
| `CallbackFilterIterator` | Chỉ giữ phần tử mà callback trả `true` |
| `AppendIterator` | Nối nhiều iterator thành một |
| `InfiniteIterator` | Duyệt hết thì tự quay lại đầu, mãi mãi |
| `NoRewindIterator` | Bỏ qua lời gọi `rewind()` |
| `CachingIterator` | Đọc trước một phần tử, cho biết còn phần tử kế không (`hasNext()`) |
| `RecursiveArrayIterator` + `RecursiveIteratorIterator` | Duyệt phẳng một cấu trúc lồng nhau |
| `RegexIterator` | Lọc theo biểu thức chính quy |

```php
<?php
declare(strict_types=1);

$words = new ArrayIterator(['an', 'bình', 'chi', 'dũng', 'em', 'giang']);

// LimitIterator: bỏ 2 phần tử đầu, lấy tối đa 3 phần tử. Key gốc được giữ nguyên.
foreach (new LimitIterator($words, 2, 3) as $i => $w) {
    echo "$i:$w ";
}
echo "\n";                                    // in ra: 2:chi 3:dũng 4:em

// CallbackFilterIterator: chỉ giữ phần tử thoả điều kiện
$short = new CallbackFilterIterator($words, fn(string $w): bool => strlen($w) <= 2);
echo implode(',', iterator_to_array($short, false)), "\n";   // in ra: an,em

// RecursiveIteratorIterator + RecursiveArrayIterator: duyệt phẳng array lồng nhau, chỉ lấy "lá"
$config = ['db' => ['host' => 'localhost', 'port' => 3306], 'cache' => ['driver' => 'redis']];
foreach (new RecursiveIteratorIterator(new RecursiveArrayIterator($config)) as $key => $value) {
    echo "$key=$value ";
}
echo "\n";                                    // in ra: host=localhost port=3306 driver=redis

// Bọc được cả generator: lấy 3 số đầu của một dãy vô hạn
function naturals(): Generator
{
    for ($i = 1; ; $i++) {
        yield $i;
    }
}
foreach (new LimitIterator(naturals(), 0, 3) as $n) {
    echo $n, ' ';
}
echo "\n";                                    // in ra: 1 2 3

// InfiniteIterator + LimitIterator: lặp vòng một danh sách
$colors = new InfiniteIterator(new ArrayIterator(['đỏ', 'xanh']));
foreach (new LimitIterator($colors, 0, 5) as $c) {
    echo $c, ' ';
}
echo "\n";                                    // in ra: đỏ xanh đỏ xanh đỏ
```

Các class này ra đời từ thời PHP 5, trước khi có generator. Ngày nay phần lớn việc của chúng
(`LimitIterator`, `CallbackFilterIterator`, `AppendIterator`) viết bằng generator ngắn và dễ đọc hơn, như
`take()` và `filterLazy()` ở mục 5.3. Chúng vẫn đáng biết vì bạn sẽ gặp trong code cũ và trong thư viện,
và vì nhóm *recursive* (đặc biệt `RecursiveDirectoryIterator` để duyệt cây thư mục,
[Chương 14](14-file-json-thoi-gian.md)) vẫn rất tiện.

## 9. Cấu trúc dữ liệu SPL

### 9.1 Vì sao không dùng array cho mọi thứ

Array của PHP là một *ordered hash table* đa năng ([Chương 06](06-mang.md)): vừa là list, vừa là map,
vừa giữ thứ tự. Nó đủ tốt cho đa số trường hợp, nhưng có những thao tác nó làm kém hoặc không diễn đạt rõ
ý định:

- Lấy phần tử **đầu** (`array_shift`) tốn O(n) vì phải đánh số lại toàn bộ key: làm hàng đợi lớn bằng
  array rất chậm.
- Luôn lấy phần tử **nhỏ nhất/lớn nhất** trong một tập đang thay đổi: với array phải `sort` lại hoặc quét
  cả mảng mỗi lần.
- Dùng **object làm key**: array không cho phép, key chỉ là int hoặc string.
- Nói rõ ý đồ: một biến kiểu `SplQueue` nói ngay "đây là hàng đợi", còn `array` thì không nói gì.

SPL cung cấp các cấu trúc dữ liệu kinh điển cho đúng những chỗ này. Bảng tổng quan (n là số phần tử):

| Class | Mô hình | Thao tác chính | Chi phí | Dùng khi |
|---|---|---|---|---|
| `SplDoublyLinkedList` | Danh sách liên kết đôi | `push`, `pop`, `shift`, `unshift` | O(1) ở hai đầu; truy cập theo index O(n) | Cơ sở cho stack và queue |
| `SplStack` | Ngăn xếp, vào sau ra trước (LIFO) | `push`, `pop`, `top` | O(1) | Duyệt cây/đồ thị theo chiều sâu, undo |
| `SplQueue` | Hàng đợi, vào trước ra trước (FIFO) | `enqueue`, `dequeue` | O(1) | Duyệt theo chiều rộng (BFS), hàng việc chờ xử lý |
| `SplMinHeap`, `SplMaxHeap`, `SplHeap` | Heap nhị phân | `insert`, `extract`, `top` | `insert`/`extract` O(log n), `top` O(1) | Luôn cần phần tử nhỏ nhất/lớn nhất, top K |
| `SplPriorityQueue` | Hàng đợi ưu tiên (max heap) | `insert($value, $priority)`, `extract` | O(log n) | Việc ưu tiên cao làm trước |
| `SplFixedArray` | Mảng kích thước cố định, index số nguyên | `$a[$i]` | O(1) | Danh sách số rất lớn, biết trước kích thước |
| `SplObjectStorage` | Map/set với key là object | `$s[$obj]` | O(1) trung bình | Gắn dữ liệu vào object, tập object không trùng |
| `ArrayObject` | Array bọc trong object | Như array | Như array | Cần một array được chia sẻ (truyền như object) |

Độ phức tạp ở cột "Chi phí" là tính chất của cấu trúc dữ liệu: manual ghi O(1) cho thao tác ở hai đầu
của danh sách liên kết đôi, và mã nguồn php-src cài heap dạng nhị phân, `SplObjectStorage` dạng hash
table theo id của object. Ý nghĩa O(1), O(log n), O(n) xem lại ở phần DSA của repo này nếu cần.

### 9.2 `SplStack` và `SplQueue`

Cả hai kế thừa `SplDoublyLinkedList`: một chuỗi node, mỗi node giữ giá trị và hai con trỏ tới node trước
và sau. Thêm hay bớt ở hai đầu chỉ là sửa vài con trỏ, không phải dời phần tử nào.

```
 bottom (đầu)                                       top (cuối)
   ┌─────┐      ┌─────┐      ┌─────┐
   │ 'a' │ ◄──► │ 'b' │ ◄──► │ 'c' │
   └─────┘      └─────┘      └─────┘
   ▲                            ▲
   │ shift()/dequeue() lấy ở đây │ push()/enqueue() thêm, pop() lấy ở đây
```

**`SplStack`**: vào sau ra trước.

```php
<?php
declare(strict_types=1);

$stack = new SplStack();
$stack->push('a');
$stack->push('b');
$stack->push('c');

echo $stack->top(), "\n";      // in ra: c   (xem đỉnh, không lấy ra)
echo $stack->pop(), "\n";      // in ra: c   (lấy ra)
echo count($stack), "\n";      // in ra: 2

foreach ($stack as $v) {       // duyệt từ đỉnh xuống: LIFO
    echo $v, ' ';
}
echo "\n";                     // in ra: b a
echo count($stack), "\n";      // in ra: 2   (foreach không lấy phần tử ra)

try {
    (new SplStack())->pop();
} catch (RuntimeException $e) {
    echo $e->getMessage(), "\n";   // in ra: Can't pop from an empty datastructure
}
```

**`SplQueue`**: vào trước ra trước.

```php
<?php
declare(strict_types=1);

$queue = new SplQueue();
$queue->enqueue('x');          // thêm vào cuối (giống push)
$queue->enqueue('y');
$queue[] = 'z';                // cú pháp [] cũng thêm vào cuối

echo $queue->dequeue(), "\n";  // in ra: x   (lấy ở đầu, giống shift)
foreach ($queue as $v) {
    echo $v, ' ';
}
echo "\n";                     // in ra: y z
echo count($queue), "\n";      // in ra: 2

// Muốn foreach vừa duyệt vừa lấy phần tử ra: bật chế độ IT_MODE_DELETE
$queue->setIteratorMode(SplDoublyLinkedList::IT_MODE_DELETE);
foreach ($queue as $v) {
    echo $v, ' ';
}
echo "\n";                     // in ra: y z
echo count($queue), "\n";      // in ra: 0

try {
    $queue->dequeue();
} catch (RuntimeException $e) {
    echo $e->getMessage(), "\n";   // in ra: Can't shift from an empty datastructure
}
```

Vài điểm cần nhớ:

- Lấy từ cấu trúc rỗng (`pop`, `dequeue`, `top`, `bottom`) ném `RuntimeException`, không trả `null` như
  `array_pop([])`. Kiểm tra `isEmpty()` trước, như vòng `while (!$queue->isEmpty())` ở mục 7.5.
- Chiều duyệt của `SplStack` (LIFO) và `SplQueue` (FIFO) bị khoá: gọi `setIteratorMode()` với chiều ngược
  lại ném `RuntimeException: Iterators' LIFO/FIFO modes for SplStack/SplQueue objects are frozen`. Chỉ
  bật/tắt được `IT_MODE_DELETE`, và phải ghép với đúng chiều: với `SplStack` viết
  `IT_MODE_LIFO | IT_MODE_DELETE` (chỉ truyền `IT_MODE_DELETE` nghĩa là chiều FIFO, bị từ chối như trên).
- Chúng implement `ArrayAccess` nên `$stack[0]` chạy được, nhưng truy cập theo index phải đi dọc danh sách
  (O(n)), và với `SplStack` thì index 0 là phần tử ở **đỉnh**. Dùng stack và queue qua các method của
  chúng, đừng dùng như array.

**Vì sao không dùng array cho queue lớn.** `array_shift()` phải đánh số lại toàn bộ key còn lại nên mỗi
lần lấy tốn O(n) ([Chương 06](06-mang.md)), lấy hết n phần tử tốn O(n²). `SplQueue::dequeue()` tốn O(1).
Output minh hoạ (php-wasm 32-bit) với 100 000 phần tử: lấy hết bằng `dequeue()` mất vài mili giây, bằng `array_shift()`
mất vài giây. Con số tuyệt đối trên máy bạn sẽ khác, khoảng cách hàng trăm lần thì không. Ngược lại, mỗi
phần tử của danh sách liên kết là một node cấp phát riêng có thêm hai con trỏ, nên với cùng số phần tử nó
thường không gọn hơn array. Với stack thì array đã đủ tốt: `$a[] = ...` và `array_pop()` đều O(1).

### 9.3 Heap: `SplMinHeap`, `SplMaxHeap`, `SplHeap`

*Heap* là cấu trúc dạng cây, giữ một tính chất: mỗi nút "lớn hơn hoặc bằng" các nút con của nó (theo một
hàm so sánh). Hệ quả: phần tử "lớn nhất" luôn nằm ở gốc, lấy ra tức thì; thêm hoặc lấy một phần tử chỉ cần
sắp xếp lại một nhánh, tốn O(log n). Heap không giữ toàn bộ dữ liệu theo thứ tự, nó chỉ đảm bảo gốc là
phần tử đứng đầu.

```
 SplMinHeap sau khi insert 5, 1, 8, 3:

          1          ← top(): phần tử nhỏ nhất, O(1)
        /   \
       3     8
      /
     5
```

```php
<?php
declare(strict_types=1);

$min = new SplMinHeap();
foreach ([5, 1, 8, 3] as $n) {
    $min->insert($n);
}
echo $min->top(), "\n";                          // in ra: 1
echo $min->extract(), ' ', $min->extract(), "\n"; // in ra: 1 3
echo count($min), "\n";                          // in ra: 2

$max = new SplMaxHeap();
foreach ([5, 1, 8, 3] as $n) {
    $max->insert($n);
}
foreach ($max as $n) {                           // duyệt heap = lấy dần ra theo thứ tự
    echo $n, ' ';
}
echo "\n";                                       // in ra: 8 5 3 1
echo count($max), "\n";                          // in ra: 0   (foreach đã lấy hết!)
```

⚠️ **Duyệt heap là phá huỷ heap.** `foreach` trên `SplHeap` (và `SplPriorityQueue`) lấy từng phần tử ra
khỏi heap. Duyệt xong heap rỗng. Cần giữ lại thì `clone` heap trước khi duyệt.

**Tự định nghĩa thứ tự** bằng cách kế thừa `SplHeap` và viết method `compare($value1, $value2)`. Manual
quy định: trả số dương nếu `$value1` lớn hơn `$value2`, 0 nếu bằng, số âm nếu nhỏ hơn; phần tử "lớn nhất"
theo `compare()` nằm ở đỉnh.

Ví dụ thực tế ghép với generator: tìm 3 đơn hàng giá trị lớn nhất trong một luồng đơn hàng rất dài, mà
bộ nhớ chỉ giữ đúng 3 đơn. Ý tưởng: giữ một heap mà đỉnh là đơn **nhỏ nhất** trong số đang giữ; mỗi khi
heap có hơn 3 đơn thì bỏ đơn ở đỉnh.

```php
<?php
declare(strict_types=1);

/** Heap đơn hàng, đơn có total NHỎ nhất nằm ở đỉnh. */
final class SmallestOrderHeap extends SplHeap
{
    protected function compare(mixed $a, mixed $b): int
    {
        // SplHeap đặt phần tử "lớn hơn" theo compare() lên đỉnh.
        // Đảo chiều so sánh để đơn có total nhỏ nhất được coi là "lớn nhất".
        return $b['total'] <=> $a['total'];
    }
}

/** @return Generator<int, array{id: int, total: int}> */
function orders(): Generator
{
    // Giả lập luồng đơn hàng rất dài (thực tế: đọc từ DB hoặc file, mục 5)
    $totals = [120, 900, 45, 300, 780, 15, 999, 610];
    foreach ($totals as $i => $total) {
        yield ['id' => $i + 1, 'total' => $total];
    }
}

/** Top K đơn có total lớn nhất, bộ nhớ chỉ giữ K + 1 phần tử. */
function topK(iterable $orders, int $k): array
{
    $heap = new SmallestOrderHeap();
    foreach ($orders as $order) {
        $heap->insert($order);
        if (count($heap) > $k) {
            $heap->extract();   // bỏ đơn nhỏ nhất trong K + 1 đơn đang giữ
        }
    }
    $result = [];
    foreach ($heap as $order) {      // lấy dần ra, từ nhỏ tới lớn
        $result[] = $order;
    }
    return array_reverse($result);   // lớn nhất trước
}

foreach (topK(orders(), 3) as $o) {
    echo "#{$o['id']}: {$o['total']}\n";
}
// in ra:
// #7: 999
// #2: 900
// #5: 780
```

Chi phí: O(n log k) thời gian và O(k) bộ nhớ, so với sắp xếp toàn bộ là O(n log n) thời gian và O(n) bộ
nhớ. Với n là mười triệu và k là 10, khác biệt rất lớn.

⚠️ Manual cảnh báo hai điều về `compare()`: không nên để nhiều phần tử bằng nhau trong heap (thứ tự tương
đối của chúng là tuỳ ý), và ném exception trong `compare()` có thể làm heap ở trạng thái hỏng
(*corrupted*), phải gọi `recoverFromCorruption()` mới dùng tiếp được.

### 9.4 `SplPriorityQueue`

Hàng đợi ưu tiên: mỗi phần tử đi kèm một độ ưu tiên (*priority*), `extract()` luôn lấy phần tử có độ ưu
tiên **cao nhất**. Bên trong là một max heap sắp theo priority.

```php
<?php
declare(strict_types=1);

$jobs = new SplPriorityQueue();
$jobs->insert('gửi email marketing', 1);    // insert(giá trị, độ ưu tiên)
$jobs->insert('thanh toán', 10);
$jobs->insert('resize ảnh', 5);

echo count($jobs), "\n";                    // in ra: 3
echo $jobs->top(), "\n";                    // in ra: thanh toán
while (!$jobs->isEmpty()) {
    echo $jobs->extract(), "\n";
}
// in ra:
// thanh toán
// resize ảnh
// gửi email marketing
```

Mặc định `extract()` chỉ trả giá trị. Muốn lấy cả priority thì đổi *extract flag*:

```php
$pq = new SplPriorityQueue();
$pq->setExtractFlags(SplPriorityQueue::EXTR_BOTH);   // EXTR_DATA (mặc định), EXTR_PRIORITY, EXTR_BOTH
$pq->insert('a', 2);
$pq->insert('b', 7);
print_r($pq->extract());
// in ra:
// Array
// (
//     [data] => b
//     [priority] => 7
// )
```

⚠️ **Cùng priority thì không giữ thứ tự thêm vào.** Manual ghi rõ: thứ tự của các phần tử có cùng
priority là không xác định, có thể khác thứ tự đã thêm. Nhiều người tưởng nó là "queue" nên cùng mức thì
FIFO, và sai:

```php
<?php
declare(strict_types=1);

$same = new SplPriorityQueue();
foreach (range(1, 8) as $i) {
    $same->insert("job$i", 5);       // cùng priority 5
}
$out = [];
while (!$same->isEmpty()) {
    $out[] = $same->extract();
}
echo implode(' ', $out), "\n";
// output quan sát được trên PHP 8.5 (không được đảm bảo, bản khác có thể khác):
// job1 job8 job7 job6 job5 job4 job3 job2   (không phải job1..job8)
```

Muốn cùng mức thì vào trước ra trước, dùng priority là một array `[mức ưu tiên, số thứ tự giảm dần]`.
PHP so sánh hai array cùng độ dài từng phần tử một từ trái sang phải ([Chương 07](07-toan-tu-dieu-khien.md)),
nên khi mức ưu tiên bằng nhau thì phần tử thứ hai quyết định:

```php
<?php
declare(strict_types=1);

$stable = new SplPriorityQueue();
$seq = PHP_INT_MAX;                          // giảm dần: thêm trước thì số lớn hơn, ra trước
foreach (range(1, 8) as $i) {
    $stable->insert("job$i", [5, $seq--]);
}
$stable->insert('gấp', [9, $seq--]);
$out = [];
while (!$stable->isEmpty()) {
    $out[] = $stable->extract();
}
echo implode(' ', $out), "\n";
// in ra: gấp job1 job2 job3 job4 job5 job6 job7 job8
```

Như `SplHeap`, duyệt `SplPriorityQueue` bằng `foreach` cũng lấy hết phần tử ra.

Trong ứng dụng web, hàng đợi ưu tiên **trong bộ nhớ** chỉ sống trong một request hoặc một process. Hàng
đợi job thật sự (gửi mail, xử lý ảnh) phải bền vững và chia sẻ giữa nhiều worker, nên dùng queue của
Laravel với Redis hay database ([Chương 29](29-laravel-queue-event-schedule-cache.md)). `SplPriorityQueue`
hợp với thuật toán chạy trong một lần xử lý: Dijkstra, gộp nhiều nguồn đã sắp xếp, lập lịch trong một
worker.

### 9.5 `SplFixedArray`

Mảng có **kích thước cố định** khai báo trước, index chỉ là số nguyên từ 0 tới size - 1. Manual: khác biệt
chính so với array thường là phải tự đổi kích thước và chỉ chấp nhận index số nguyên trong phạm vi; đổi
lại nó tốn ít bộ nhớ hơn.

```php
<?php
declare(strict_types=1);

$a = new SplFixedArray(3);         // 3 ô, ô nào chưa gán là null
var_dump($a[0]);                   // in ra: NULL
$a[0] = 'x';
$a[2] = 'z';
echo $a->getSize(), "\n";          // in ra: 3   (count($a) cũng ra 3)

foreach ($a as $i => $v) {
    echo "$i:", var_export($v, true), ' ';
}
echo "\n";                         // in ra: 0:'x' 1:NULL 2:'z'

try {
    $a[3] = 'w';                   // ngoài phạm vi
} catch (RuntimeException $e) {
    echo get_class($e), ': ', $e->getMessage(), "\n";
    // in ra (8.4+): OutOfBoundsException: Index invalid or out of range
    // in ra (8.3-): RuntimeException: Index invalid or out of range
}

try {
    $a[] = 'v';                    // không có "thêm vào cuối"
} catch (Error $e) {
    echo $e->getMessage(), "\n";   // in ra: [] operator not supported for SplFixedArray
}

$a->setSize(5);                    // đổi kích thước phải gọi tường minh
$a[4] = 'e';
echo json_encode($a->toArray()), "\n";   // in ra: ["x",null,"z",null,"e"]

$b = SplFixedArray::fromArray([3 => 'd', 1 => 'b']);          // giữ index: ô thiếu là null
echo json_encode($b->toArray()), "\n";                        // in ra: [null,"b",null,"d"]
$c = SplFixedArray::fromArray([3 => 'd', 1 => 'b'], false);   // bỏ index, xếp liền nhau
echo json_encode($c->toArray()), "\n";                        // in ra: ["d","b"]
```

Lịch sử thay đổi cần biết (theo manual):

- PHP 8.4: truy cập ngoài phạm vi ném `OutOfBoundsException` thay vì `RuntimeException`. Vì
  `OutOfBoundsException` là class con của `RuntimeException`, code cũ `catch (RuntimeException $e)` vẫn
  bắt được, như ví dụ trên.
- PHP 8.1: index không phải số nguyên (ví dụ `'abc'`) ném `TypeError` thay vì `RuntimeException`. Chuỗi
  số như `'1'` vẫn được hiểu là index 1.
- PHP 8.0: `SplFixedArray` implement `IteratorAggregate` thay vì `Iterator`, nên lồng hai vòng `foreach`
  trên cùng một `SplFixedArray` không còn dùng chung vị trí (mục 2.4).

**Tiết kiệm bao nhiêu bộ nhớ?** Output minh hoạ (php-wasm 32-bit, PHP 8.5; trên máy 64-bit thật con số có
thể chênh, xu hướng thì giống), với n số nguyên:

| n | Array thường (thêm bằng `$arr[] = $i`) | `SplFixedArray` |
|---|---|---|
| 1 000 000 | 16.06 MiB | 15.31 MiB |
| 600 000 | 16.06 MiB | 9.19 MiB |

Từ PHP 8.2, array dạng list (*packed array*) chỉ tốn 16 byte mỗi phần tử, ngang `SplFixedArray`; trên PHP
8.1 cùng array 1 000 000 phần tử đo được 32.06 MiB (cùng môi trường php-wasm). Khác biệt còn lại đến từ việc array cấp chỗ theo lũy
thừa của 2: 600 000 hay 1 000 000 phần tử đều được cấp chỗ cho 1 048 576 phần tử, còn `SplFixedArray` cấp
đúng bằng size. Kết luận thực tế: trên PHP hiện đại, `SplFixedArray` chỉ đáng dùng khi danh sách số
nguyên rất lớn, biết trước kích thước, và bạn đã đo thấy bộ nhớ là vấn đề. Phần lớn thời gian, giảm bộ
nhớ bằng cách không giữ cả danh sách (generator, mục 5) hiệu quả hơn nhiều.

### 9.6 `SplObjectStorage`: object làm key

Array không nhận object làm key. Khi cần "gắn dữ liệu vào từng object" hay "tập hợp các object không
trùng", dùng `SplObjectStorage`. Manual mô tả nó là một map từ object tới dữ liệu, hoặc, nếu bỏ qua phần
dữ liệu, một tập hợp (*set*) object.

Hai object được coi là cùng một key khi chúng là **cùng một instance** (cùng id), không phải khi nội dung
giống nhau.

```php
<?php
declare(strict_types=1);

final class User
{
    public function __construct(public readonly string $name) {}
}

$an = new User('An');
$binh = new User('Bình');
$an2 = new User('An');                 // cùng nội dung với $an nhưng là object KHÁC

// 1. Dùng như map: object => dữ liệu đi kèm
$lastSeen = new SplObjectStorage();
$lastSeen[$an] = '09:00';               // offsetSet
$lastSeen[$binh] = '09:05';
$lastSeen[$an] = '09:10';               // cùng object: ghi đè, không thêm mới
echo count($lastSeen), "\n";            // in ra: 2
echo $lastSeen[$an], "\n";              // in ra: 09:10
var_dump(isset($lastSeen[$an2]));       // in ra: bool(false)   (object khác)

foreach ($lastSeen as $i => $user) {    // foreach: key là số thứ tự, value là OBJECT
    echo "$i: {$user->name} lúc ", $lastSeen[$user], "\n";
}
// in ra:
// 0: An lúc 09:10
// 1: Bình lúc 09:05

// 2. Dùng như set: chỉ quan tâm có hay không
$notified = new SplObjectStorage();
$notified[$an] = null;
$notified[$an] = null;                  // thêm lần nữa: vẫn chỉ một
echo count($notified), "\n";            // in ra: 1
unset($notified[$an]);                  // offsetUnset
echo count($notified), "\n";            // in ra: 0
```

⚠️ **PHP 8.5 deprecate ba method cũ.** Rất nhiều code và tutorial dùng `attach()`, `contains()`,
`detach()`. Từ PHP 8.5 chúng phát `Deprecated` và được thay bằng các method của `ArrayAccess`:

| Cách cũ (deprecated từ 8.5) | Cách mới | Cú pháp tương đương |
|---|---|---|
| `$s->attach($obj, $data)` | `$s->offsetSet($obj, $data)` | `$s[$obj] = $data` |
| `$s->contains($obj)` | `$s->offsetExists($obj)` | `isset($s[$obj])` |
| `$s->detach($obj)` | `$s->offsetUnset($obj)` | `unset($s[$obj])` |

```php
$s = new SplObjectStorage();
$s->attach($an);
// PHP 8.5: Deprecated: Method SplObjectStorage::attach() is deprecated since 8.5,
//          use method SplObjectStorage::offsetSet() instead
// PHP 8.4: không có thông báo
```

Cú pháp `$s[$obj]` chạy trên mọi bản PHP 8, nên viết theo cách mới ngay từ bây giờ.

⚠️ **`SplObjectStorage` giữ object sống.** Nó giữ tham chiếu *mạnh*: object đã nằm trong storage thì không
bị giải phóng dù mọi chỗ khác đã bỏ nó. Nếu mục đích là "gắn thêm dữ liệu vào object mà không kéo dài đời
sống của nó" (cache theo object, metadata), dùng `WeakMap` ([Chương 10](10-oop-nang-cao.md)): khi object
chết, mục tương ứng trong `WeakMap` tự biến mất. Quy tắc chọn:

- Cần tập object và muốn giữ chúng (danh sách observer, tập entity đã xử lý trong một lô): `SplObjectStorage`.
- Cần gắn dữ liệu phụ vào object mà không muốn giữ nó sống: `WeakMap`.

### 9.7 `ArrayObject` và `ArrayIterator`

`ArrayObject` bọc một array trong một object. Nó implement `IteratorAggregate`, `ArrayAccess`, `Countable`
nên dùng gần giống array: `$ao[$k]`, `$ao[] = ...`, `count($ao)`, `foreach`. Điểm khác quan trọng nhất là
**ngữ nghĩa khi gán và truyền**:

```php
<?php
declare(strict_types=1);

function addTagArray(array $tags): void { $tags[] = 'php'; }
function addTagObject(ArrayObject $tags): void { $tags[] = 'php'; }

$a = ['web'];
addTagArray($a);
echo count($a), "\n";          // in ra: 1   (array truyền theo giá trị: hàm sửa bản sao)

$o = new ArrayObject(['web']);
addTagObject($o);
echo count($o), "\n";          // in ra: 2   (object: hàm sửa cùng một object)

// Tạo từ array thì array được chép vào, sửa ArrayObject không ảnh hưởng array gốc
$src = ['x' => 1];
$ao = new ArrayObject($src);
$ao['y'] = 2;
echo json_encode($src), ' ', json_encode($ao->getArrayCopy()), "\n";   // in ra: {"x":1} {"x":1,"y":2}

// Một số method
$ao->append(3);                                       // như $ao[] = 3
$ao->ksort();                                         // có sẵn asort, ksort, uasort, uksort, natsort...
echo json_encode($ao->getArrayCopy()), "\n";          // in ra: {"0":3,"x":1,"y":2}
$old = $ao->exchangeArray(['z' => 9]);                // thay toàn bộ, trả về array cũ
echo json_encode($ao->getArrayCopy()), "\n";          // in ra: {"z":9}
echo get_class($ao->getIterator()), "\n";             // in ra: ArrayIterator

// Cờ ARRAY_AS_PROPS: đọc ghi phần tử như property
$cfg = new ArrayObject(['host' => 'localhost'], ArrayObject::ARRAY_AS_PROPS);
echo $cfg->host, ' ', $cfg['host'], "\n";             // in ra: localhost localhost
$cfg->port = 3306;
echo $cfg['port'], "\n";                              // in ra: 3306
```

Khi nào dùng `ArrayObject`:

- Cần một "array" mà nhiều chỗ cùng sửa được (truyền vào hàm và thấy thay đổi), mà không muốn dùng
  tham chiếu `&` ([Chương 08](08-ham.md)).
- Muốn kế thừa để có một collection có thêm method riêng mà vẫn dùng được cú pháp array.

Nhưng trong code mới, một class collection riêng (mục 3.3) thường rõ ràng hơn: bạn kiểm soát được kiểu
phần tử và API.

⚠️ Bẫy của `ArrayObject`:

- Không phải array: các hàm `array_*` từ chối nó (`TypeError`, mục 3.3). Dùng `getArrayCopy()` khi cần
  array thật.
- `json_encode($ao)` luôn ra JSON **object**, kể cả khi bên trong là list:
  `json_encode(new ArrayObject(['web', 'php']))` cho `{"0":"web","1":"php"}`, không phải
  `["web","php"]`. Gọi `json_encode($ao->getArrayCopy())` nếu cần JSON array.
- PHP 8.5: truyền một **object** (thay vì array) vào constructor của `ArrayObject` hay `ArrayIterator` bị
  deprecated: `Deprecated: ArrayObject::__construct(): Using an object as a backing array for ArrayObject
  is deprecated, as it allows violating class constraints and invariants`. Truyền một enum thì ném
  `InvalidArgumentException: Enums are not compatible with ArrayObject`. Code cũ hay dùng
  `new ArrayObject($someObject)` để duyệt property của object; đừng viết như vậy nữa.

**`ArrayIterator`** là iterator duyệt một array, cũng implement `ArrayAccess`, `Countable` và
`SeekableIterator` (thêm method `seek($position)` nhảy tới vị trí bất kỳ). Bạn đã dùng nó ở mục 3.2: cách
chuẩn để `getIterator()` trả về iterator cho một array `private`. Manual khuyên: muốn duyệt cùng một array
nhiều lần thì dùng `ArrayObject` và để nó tạo `ArrayIterator` mới cho mỗi lần duyệt (chính là mô hình
`IteratorAggregate`).

### 9.8 Chọn cấu trúc nào

| Nhu cầu | Chọn |
|---|---|
| List, map thông thường, vài nghìn phần tử | `array` |
| Stack | `array` (`$a[] =`, `array_pop`) hoặc `SplStack` nếu muốn tên rõ ý |
| Queue có thể lớn (BFS, hàng việc trong một process) | `SplQueue` |
| Luôn lấy nhỏ nhất/lớn nhất, top K, Dijkstra | `SplMinHeap`/`SplMaxHeap`/`SplHeap` |
| Việc có độ ưu tiên trong một process | `SplPriorityQueue` (nhớ bẫy cùng priority) |
| Hàng đợi job bền vững giữa nhiều worker | Không phải SPL: queue của Laravel với Redis/database |
| Object làm key, tập object | `SplObjectStorage` (giữ sống) hoặc `WeakMap` (không giữ) |
| Danh sách số nguyên khổng lồ, kích thước cố định | `SplFixedArray`, sau khi đã đo |
| Dữ liệu lớn chỉ đi qua một lượt | Không cấu trúc nào cả: generator (mục 5) |

Ngoài SPL còn có extension `ds` (cài qua PECL), manual mô tả là các cấu trúc dữ liệu hiệu quả, dùng thay
cho array: `Ds\Vector`, `Ds\Deque`, `Ds\Map`, `Ds\Set`... Nó không có sẵn trong PHP, nên chỉ cân nhắc khi
bạn kiểm soát được môi trường chạy và đã đo thấy cần.

## 10. Fiber (PHP 8.1)

> Lưu ý về ví dụ trong mục này: bản PHP biên dịch sang WebAssembly dùng để kiểm tra các ví dụ của giáo
> trình không hỗ trợ Fiber, nên các ví dụ Fiber **chưa được chạy thử** lúc soạn. Output ghi trong comment
> được suy ra từng bước theo manual, RFC và mã nguồn php-src (các thông báo lỗi chép nguyên văn từ
> `Zend/zend_fibers.c`). Hãy tự chạy lại trên PHP 8.1 trở lên để kiểm chứng.

### 10.1 Bài toán: chờ I/O

Một request cần gọi ba API bên ngoài, mỗi API mất 300 ms. Code PHP thông thường gọi lần lượt:

```
 Process PHP: [gọi API 1 ... chờ 300ms ...][gọi API 2 ... chờ 300ms ...][gọi API 3 ... chờ 300ms ...]
              tổng ~900 ms, phần lớn thời gian CPU ngồi không
```

Trong lúc chờ API 1 trả lời, CPU không làm gì cả. Nếu gửi cả ba request đi rồi chờ đồng thời, tổng chỉ
còn khoảng 300 ms. Làm được việc này trong một process, một luồng, gọi là *concurrency* (đồng thời): nhiều
việc cùng "đang dở", xen kẽ nhau trong lúc chờ. Nó khác *parallelism* (song song): nhiều việc chạy **cùng
một lúc** trên nhiều lõi CPU.

Mục 7.5 đã cho thấy cách làm concurrency bằng coroutine và bộ lập lịch, và giới hạn của generator: chỉ
hàm chứa `yield` mới dừng được, nên cả chuỗi lời gọi phải "nhuộm màu" generator. *Fiber* giải đúng giới
hạn đó.

### 10.2 Fiber là gì

Manual định nghĩa: Fiber là hàm *full-stack* có thể bị ngắt giữa chừng. Fiber có thể tạm dừng **ở bất kỳ
đâu trong call stack**, và dừng cả call stack đó cho tới khi được tiếp tục.

So với generator:

| | Generator | Fiber |
|---|---|---|
| Có từ | PHP 5.5 | PHP 8.1 |
| Dừng ở đâu | Chỉ tại `yield` trong chính hàm generator | `Fiber::suspend()` ở bất kỳ độ sâu nào: hàm con, hàm cháu, cả callback của `array_map` |
| Ảnh hưởng tới chữ ký hàm | Hàm có `yield` phải trả `Generator` | Hàm gọi `Fiber::suspend()` giữ nguyên kiểu trả về |
| Stack | Không có stack riêng (*stackless*), chỉ giữ một frame | Có call stack riêng (C stack và VM stack) |
| Dùng để | Duyệt dữ liệu lười, pipeline | Nền móng cho thư viện async |

Manual nói thẳng: khác generator kiểu *stackless*, mỗi Fiber có call stack riêng, nhờ vậy dừng được bên
trong các lời gọi hàm lồng sâu; hàm khai báo điểm dừng (gọi `Fiber::suspend()`) không phải đổi kiểu trả
về như hàm dùng `yield`.

### 10.3 API

```php
final class Fiber
{
    public function __construct(callable $callback) {}
    public function start(mixed ...$args): mixed {}           // chạy callback tới suspend đầu tiên (hoặc tới hết)
    public function resume(mixed $value = null): mixed {}     // tiếp tục, $value thành kết quả của suspend()
    public function throw(Throwable $exception): mixed {}     // tiếp tục bằng cách ném exception tại suspend()
    public function getReturn(): mixed {}                     // giá trị return của callback
    public function isStarted(): bool {}
    public function isSuspended(): bool {}
    public function isRunning(): bool {}
    public function isTerminated(): bool {}
    public static function suspend(mixed $value = null): mixed {}   // gọi TỪ BÊN TRONG fiber để dừng
    public static function getCurrent(): ?Fiber {}            // fiber đang chạy, null nếu ở code chính
}
```

`start()`, `resume()`, `throw()` đều trả về giá trị mà fiber đưa ra ở lần `suspend()` kế tiếp, hoặc
`null` nếu fiber chạy hết.

Ví dụ cơ bản trong manual:

```php
<?php
declare(strict_types=1);

$fiber = new Fiber(function (): void {
    $value = Fiber::suspend('fiber');
    echo "Value used to resume fiber: ", $value, PHP_EOL;
});

$value = $fiber->start();
echo "Value from fiber suspending: ", $value, PHP_EOL;

$fiber->resume('test');
// output minh hoạ (output ghi trong manual, chưa chạy thử):
// Value from fiber suspending: fiber
// Value used to resume fiber: test
```

Luồng điều khiển của một fiber trao đổi dữ liệu hai chiều:

```php
<?php
declare(strict_types=1);

$fiber = new Fiber(function (string $greeting): string {
    echo "  [fiber] bắt đầu với: $greeting\n";
    $answer = Fiber::suspend('câu hỏi 1');      // dừng, đưa 'câu hỏi 1' ra ngoài
    echo "  [fiber] nhận được: $answer\n";
    $answer2 = Fiber::suspend('câu hỏi 2');
    echo "  [fiber] nhận được: $answer2\n";
    return 'kết quả cuối';
});

$q = $fiber->start('xin chào');                  // tham số của start() truyền vào callback
echo "[main] fiber hỏi: $q\n";
$q = $fiber->resume('trả lời 1');
echo "[main] fiber hỏi: $q\n";
$q = $fiber->resume('trả lời 2');                // fiber chạy tới return
var_dump($q);
var_dump($fiber->isTerminated());
echo "[main] fiber trả về: ", $fiber->getReturn(), "\n";
// output minh hoạ (suy ra theo manual, chưa chạy thử):
//   [fiber] bắt đầu với: xin chào
// [main] fiber hỏi: câu hỏi 1
//   [fiber] nhận được: trả lời 1
// [main] fiber hỏi: câu hỏi 2
//   [fiber] nhận được: trả lời 2
// NULL
// bool(true)
// [main] fiber trả về: kết quả cuối
```

| Bước | Code chính | Fiber | Trạng thái fiber |
|---|---|---|---|
| 1 | `new Fiber(...)` | Chưa chạy | Chưa start |
| 2 | `start('xin chào')`, đứng chờ | Chạy tới `suspend('câu hỏi 1')`, dừng | Suspended |
| 3 | `start()` trả về `'câu hỏi 1'`, in ra | Đang dừng | Suspended |
| 4 | `resume('trả lời 1')`, đứng chờ | `suspend()` trả về `'trả lời 1'`, chạy tới `suspend('câu hỏi 2')` | Suspended |
| 5 | `resume()` trả về `'câu hỏi 2'` | Đang dừng | Suspended |
| 6 | `resume('trả lời 2')`, đứng chờ | Chạy tới `return` | Terminated |
| 7 | `resume()` trả về `null`; `getReturn()` cho `'kết quả cuối'` | Đã kết thúc | Terminated |

Giống generator ở bảng mục 4.2: luôn chỉ một bên chạy, chuyển qua lại tường minh.

### 10.4 Dừng ở bất kỳ độ sâu nào

Điểm mạnh thật sự của Fiber: `Fiber::suspend()` không cần nằm trong hàm của fiber. Nó có thể nằm trong một
hàm thường được gọi lồng nhiều tầng, thậm chí trong callback mà PHP gọi từ bên trong một hàm có sẵn như
`array_map` (manual nêu rõ trường hợp này):

```php
<?php
declare(strict_types=1);

$fiber = new Fiber(function (): array {
    return array_map(function (int $x): int {
        $y = Fiber::suspend($x);        // dừng ngay giữa array_map
        return $x * $y;
    }, [1, 2, 3]);
});

$v = $fiber->start();
while (!$fiber->isTerminated()) {
    echo "fiber đưa ra $v\n";
    $v = $fiber->resume(10);
}
echo implode(',', $fiber->getReturn()), "\n";
// output minh hoạ (suy ra theo manual, chưa chạy thử):
// fiber đưa ra 1
// fiber đưa ra 2
// fiber đưa ra 3
// 10,20,30
```

Với generator thì không làm được: đặt `yield` trong closure truyền cho `array_map` biến closure đó thành
một hàm generator, `array_map` nhận về ba object `Generator` chứ không dừng lại.

Hệ quả cho thiết kế thư viện: một hàm như `$db->query($sql)` có thể bên trong gọi `Fiber::suspend()` để
nhường chỗ trong lúc chờ mạng, còn code gọi nó vẫn viết `$rows = $db->query($sql);` như code đồng bộ bình
thường, không `yield`, không promise. Đó là thứ RFC gọi là xoá ranh giới "màu" giữa hàm đồng bộ và bất
đồng bộ.

### 10.5 Bộ lập lịch nhỏ với Fiber

Viết lại ý tưởng của mục 7.5 bằng Fiber, có thêm "thời gian chờ". Để ví dụ chạy tất định và không phụ
thuộc mạng, ta dùng một đồng hồ ảo tính bằng *tick*; hàm `delay()` giả lập "chờ I/O trong n tick". Một
event loop thật làm giống hệt, chỉ khác là thay đồng hồ ảo bằng thời gian thật và theo dõi socket.

```php
<?php
declare(strict_types=1);

final class Loop
{
    public static int $now = 0;                   // đồng hồ ảo
    /** @var list<array{int, Fiber}> [thời điểm thức dậy, fiber] */
    private array $waiting = [];

    public function spawn(callable $fn): void
    {
        $fiber = new Fiber($fn);
        $this->schedule($fiber, $fiber->start());
    }

    private function schedule(Fiber $fiber, mixed $ticks): void
    {
        if (!$fiber->isTerminated()) {
            $this->waiting[] = [self::$now + $ticks, $fiber];
        }
    }

    public function run(): void
    {
        while ($this->waiting !== []) {
            // lấy fiber cần thức dậy sớm nhất (usort ổn định từ PHP 8.0: bằng nhau thì giữ thứ tự)
            usort($this->waiting, fn(array $a, array $b): int => $a[0] <=> $b[0]);
            [$wakeAt, $fiber] = array_shift($this->waiting);
            self::$now = $wakeAt;
            $this->schedule($fiber, $fiber->resume());
        }
    }
}

// Hàm "chờ I/O": code gọi nó không cần biết nó dùng Fiber
function delay(int $ticks): void
{
    Fiber::suspend($ticks);
}

function task(string $name, array $waits): void
{
    foreach ($waits as $w) {
        echo 't=', Loop::$now, " $name: bắt đầu chờ $w tick\n";
        delay($w);                                // gọi như hàm thường, không yield
    }
    echo 't=', Loop::$now, " $name: xong\n";
}

$loop = new Loop();
$loop->spawn(fn() => task('A', [3, 1]));
$loop->spawn(fn() => task('B', [2, 2]));
$loop->run();
echo 'Tổng: ', Loop::$now, " tick\n";
// output minh hoạ (thứ tự đã kiểm bằng bản mô phỏng dùng generator; bản Fiber chưa chạy thử):
// t=0 A: bắt đầu chờ 3 tick
// t=0 B: bắt đầu chờ 2 tick
// t=2 B: bắt đầu chờ 2 tick
// t=3 A: bắt đầu chờ 1 tick
// t=4 B: xong
// t=4 A: xong
// Tổng: 4 tick
```

Chạy lần lượt thì tổng là 3 + 1 + 2 + 2 = 8 tick; chạy xen kẽ chỉ hết 4 tick, vì thời gian chờ của A và B
chồng lên nhau. So với mục 7.5, `task()` và `delay()` là hàm bình thường trả `void`; chỉ `delay()` ở tầng
đáy biết đến Fiber.

### 10.6 Fiber không phải thread

Đây là chỗ hay hiểu sai nhất.

- **Không chạy song song.** Tại mỗi thời điểm chỉ một fiber chạy. Fiber chỉ đổi lượt khi code gọi
  `suspend()`/`resume()` một cách tường minh: đa nhiệm *hợp tác*, không ai bị ngắt giữa chừng. Một fiber
  chạy vòng lặp tính toán nặng mà không `suspend()` thì mọi fiber khác đứng chờ. Không dùng thêm lõi CPU
  nào.
- **Không tự biến I/O thành non-blocking.** Bên trong fiber gọi `PDO::query()`, `file_get_contents()` hay
  `sleep()` vẫn là lời gọi *blocking* (chặn): cả process đứng chờ, mọi fiber khác cũng đứng. Muốn chờ
  đồng thời phải có hai thứ: một *event loop* (vòng lặp theo dõi nhiều socket cùng lúc, socket nào có dữ
  liệu thì `resume` fiber đang chờ nó, như `Loop` ở trên nhưng với socket thật) và *driver I/O viết riêng*
  cho event loop đó (client HTTP, MySQL, Redis không chặn). Fiber chỉ là cơ chế dừng và tiếp tục.
- **Không có race condition kiểu thread** (hai luồng cùng sửa một biến tại cùng một thời điểm), vì không
  có gì chạy cùng lúc. Nhưng vẫn có lỗi logic do xen kẽ: giữa hai lần `suspend()`, dữ liệu dùng chung có
  thể đã bị fiber khác đổi.

| | Fiber (PHP) | Thread hệ điều hành | Goroutine (Go) | Virtual thread (Java 21) |
|---|---|---|---|---|
| Ai quyết định đổi lượt | Code, tường minh (`suspend`/`resume`) | Hệ điều hành, bất kỳ lúc nào | Runtime của Go | JVM |
| Chạy song song nhiều lõi | Không | Có | Có | Có |
| I/O blocking tự nhường lượt | Không, cần thư viện riêng | Không cần (mỗi thread chặn riêng) | Có | Có, với I/O của JDK |
| Người viết app dùng trực tiếp | Hiếm | Có | Có | Có |

### 10.7 Dùng ở đâu

Fiber là công cụ cho **tác giả thư viện**, người viết ứng dụng gần như không gọi `new Fiber` trực tiếp:

- *Revolt* là event loop cho PHP xây trên Fiber; README của nó ghi PHP 8.1 có sẵn fiber cho đa luồng hợp
  tác (*cooperative multi-threading*). AMPHP bản 3 dùng Revolt và Fiber (RFC Fibers nêu AMPHP v3 là nơi dùng thử đầu tiên). Với AMPHP v3
  bạn viết code trông như đồng bộ, thư viện lo việc dừng và tiếp tục.
- ReactPHP có gói `react/async` cung cấp `await()` dựa trên Fiber.

Còn trong Laravel, khi cần chạy nhiều việc chậm cùng lúc, tài liệu Laravel 13 hướng bạn tới facade
`Concurrency`, và cơ chế của nó **không phải Fiber**: các closure được serialize rồi chạy trong process PHP
con (driver mặc định `process`, ngoài ra có `fork` và `sync`). Đó là song song thật bằng nhiều process.
Gọi nhiều HTTP request cùng lúc thì HTTP client của Laravel có `Http::pool()` (xem tài liệu HTTP client của
Laravel).

Vài chi tiết kỹ thuật:

- Mỗi fiber có C stack riêng (cấp phát bằng `mmap` nếu có, bộ nhớ vật lý chỉ dùng khi cần, theo RFC) và VM
  stack riêng. Kích thước C stack chỉnh bằng ini `fiber.stack_size`; mặc định trong mã nguồn php-src là
  2 MiB trên hệ 64-bit. Hàng nghìn fiber đồng thời là bình thường.
- Fiber chưa chạy xong mà bị huỷ (không còn biến nào giữ) thì các khối `finally` đang dở được chạy, giống
  generator (mục 4.11).
- Trước PHP 8.4 không được chuyển fiber (`suspend`/`resume`) trong lúc đang chạy destructor của object;
  từ 8.4 được phép (manual và UPGRADING 8.4).

### 10.8 Lỗi khi dùng sai: `FiberError`

Dùng fiber sai trạng thái ném `FiberError` (class `final`, kế thừa `Error`). Các thông báo lấy từ mã nguồn
`Zend/zend_fibers.c`:

| Làm gì | Thông báo |
|---|---|
| `start()` lần hai | `Cannot start a fiber that has already been started` |
| `resume()`/`throw()` fiber chưa start, đang chạy hoặc đã xong | `Cannot resume a fiber that is not suspended` |
| `Fiber::suspend()` ở code chính, ngoài mọi fiber | `Cannot suspend outside of a fiber` |
| `getReturn()` khi chưa start | `Cannot get fiber return value: The fiber has not been started` |
| `getReturn()` khi đang dừng | `Cannot get fiber return value: The fiber has not returned` |
| `getReturn()` khi fiber kết thúc vì exception | `Cannot get fiber return value: The fiber threw an exception` |

Exception ném ra trong fiber mà không được bắt thì bay ra khỏi lời gọi `start()`/`resume()`/`throw()` đang
chạy fiber đó, và fiber kết thúc. Ngược lại `$fiber->throw($e)` ném `$e` vào trong fiber, tại chỗ
`Fiber::suspend()` đang dừng, giống `Generator::throw()` ở mục 7.3.

## 11. Đối chiếu với Java, Go, Python

| Khái niệm | PHP | Java | Go | Python |
|---|---|---|---|---|
| Interface duyệt | `Iterator` (`current/key/next/rewind/valid`), `IteratorAggregate` | `Iterator` (`hasNext/next`), `Iterable` (`iterator()`) | Từ Go 1.23: hàm iterator `iter.Seq`, duyệt bằng `for range` | `__iter__`/`__next__`, `StopIteration` |
| Tách kho và con trỏ | `IteratorAggregate::getIterator()` | `Iterable::iterator()` | Hàm trả về `iter.Seq` | `__iter__` trả iterator mới |
| Generator | `yield`, `yield from`, `send()` | Không có trong ngôn ngữ (dùng `Stream` lười) | Không có từ khoá, dùng iterator function hoặc goroutine + channel | `yield`, `yield from`, `send()` (phải mồi bằng `next()` trước) |
| Concurrency trong một process | Fiber + event loop thư viện | Thread, virtual thread | Goroutine | `asyncio` (`async`/`await`) |

Hai điểm đáng nhớ: generator của PHP giống Python nhất (PHP còn không cần "mồi" trước khi `send()`, mục
7.2); và Fiber của PHP gần với "coroutine có stack" hơn là với goroutine, vì không có runtime nào tự lập
lịch hay tự nhường lượt khi gặp I/O.

## Lỗi thường gặp

| Lỗi | Vì sao | Cách tránh |
|---|---|---|
| `Exception: Cannot traverse an already closed generator` | Duyệt generator lần hai | Gọi lại hàm generator, hoặc bọc bằng `IteratorAggregate` (mục 4.6, 4.7) |
| `Exception: Cannot rewind a generator that was already run` | `rewind()` (hoặc `foreach` mới) sau khi generator đã qua `yield` đầu | Như trên |
| Kiểm tra tham số trong generator không báo lỗi lúc gọi | Thân generator chạy lười | Tách hàm thường kiểm tra + generator bên trong (mục 4.10) |
| `iterator_to_array()` mất phần tử | `yield from` hoặc key tự chọn bị trùng, phần tử sau ghi đè | `iterator_to_array($gen, false)` (mục 6.2) |
| Giá trị `yield` đầu tiên biến mất khi dùng `send()` | `send()` trên generator chưa chạy tự chạy tới `yield` đầu rồi bỏ qua nó | Gọi `current()` trước `send()` đầu tiên (mục 7.2) |
| Generator đọc DB vẫn hết bộ nhớ với MySQL | PDO MySQL mặc định buffer toàn bộ kết quả | Unbuffered query hoặc chia lô theo khoá; Laravel `lazy()`/`lazyById()` (mục 5.4) |
| File handle không đóng sau `break` | Generator dở dang vẫn còn biến giữ | `try`/`finally` trong generator, không giữ generator dở dang lâu (mục 4.11) |
| Hai `foreach` lồng nhau trên một `Iterator` chỉ chạy một lượt | Iterator là con trỏ duy nhất | Dùng `IteratorAggregate` (mục 2.4) |
| `Deprecated: Return type of X::current() should either be compatible...` | Thiếu kiểu trả về khi implement interface có sẵn | Ghi đủ kiểu trả về (mục 2.4) |
| `foreach` trên heap/priority queue làm nó rỗng | Duyệt `SplHeap`, `SplPriorityQueue` là lấy ra | `clone` trước khi duyệt (mục 9.3) |
| Cùng priority mà không ra theo thứ tự thêm vào | `SplPriorityQueue` không ổn định | Priority dạng `[mức, số thứ tự giảm dần]` (mục 9.4) |
| `RuntimeException: Can't pop/shift from an empty datastructure` | Lấy từ stack/queue rỗng | Kiểm tra `isEmpty()` trước |
| `Deprecated` với `attach()`/`contains()`/`detach()` trên PHP 8.5 | Ba method bị deprecate | `$s[$obj] = ...`, `isset($s[$obj])`, `unset($s[$obj])` (mục 9.6) |
| `TypeError` khi đưa `ArrayObject` vào `array_map` | Object không phải array | `getArrayCopy()` hoặc `iterator_to_array()` |
| Nghĩ Fiber làm code chạy song song hoặc làm PDO non-blocking | Fiber chỉ là cơ chế dừng/tiếp tục hợp tác | Cần event loop và driver async; trong Laravel dùng `Concurrency`/`Http::pool` (mục 10.6, 10.7) |

## Tóm tắt chương

- `Traversable` đánh dấu thứ `foreach` được; class tự định nghĩa việc duyệt bằng `Iterator` (tự làm con
  trỏ, năm method) hoặc `IteratorAggregate` (trả về iterator mới mỗi lần, nên duyệt lồng nhau được).
- `foreach` trên iterator là `rewind()`, rồi lặp `valid()`, `current()`, `key()` (chỉ khi lấy key), thân
  vòng, `next()`.
- Generator là hàm có `yield`: gọi hàm chỉ tạo object `Generator`, thân hàm chạy lười tới từng `yield`, biến
  cục bộ được giữ giữa các lần dừng. Chỉ duyệt được một lần.
- Dữ liệu lớn chỉ cần đi qua một lượt thì để nó chảy qua generator thay vì gom vào array: bộ nhớ không tăng
  theo số phần tử. Nhớ `try`/`finally` cho tài nguyên, và với MySQL nhớ chuyện buffered query.
- `yield from` uỷ quyền cho array/Traversable/generator khác, giữ nguyên key (cẩn thận `iterator_to_array`)
  và trả về giá trị `return` của generator con.
- `send()`, `throw()` biến generator thành coroutine trao đổi hai chiều; đây là nền của thư viện async
  thời trước PHP 8.1.
- SPL cho cấu trúc dữ liệu đúng việc: `SplQueue` cho hàng đợi lớn, heap và `SplPriorityQueue` cho "luôn
  lấy phần tử đứng đầu" (duyệt là lấy ra, cùng priority không giữ thứ tự), `SplObjectStorage` cho object
  làm key (8.5: dùng cú pháp `[]` thay `attach`/`contains`/`detach`), `SplFixedArray` khi đã đo thấy cần.
- Fiber (8.1) dừng được ở mọi độ sâu của call stack, không đổi chữ ký hàm. Nó không phải thread, không chạy
  song song, không tự làm I/O non-blocking; nó là nền móng cho event loop như Revolt và AMPHP v3.

## Câu hỏi tự kiểm tra

1. `foreach ($it as $v)` (không lấy key) gọi những method nào của một `Iterator`, theo thứ tự nào?
   `key()` có được gọi không? (mục 2.2)
2. Vì sao hai vòng `foreach` lồng nhau trên cùng một object `Iterator` chỉ cho 3 cặp thay vì 9, còn với
   `IteratorAggregate` thì đủ 9? (mục 2.4, 3.1)
3. Gọi một hàm generator thì thân hàm chạy tới đâu? Kiểu tham số được kiểm tra lúc nào? (mục 4.1, 4.10)
4. Một generator vừa `yield` 3 phần tử vừa `return 'xong'`. `foreach` nhận được mấy giá trị, và lấy
   `'xong'` bằng cách nào? Lấy sớm hơn thì sao?
5. Vì sao `iterator_to_array()` của một generator dùng `yield from` có thể ra ít phần tử hơn khi
   `foreach`? (mục 6.2)
6. Gọi `send('A')` ngay trên một generator vừa tạo thì giá trị của `yield` đầu tiên đi đâu?
7. Generator đọc từng dòng kết quả `SELECT` trên MySQL bằng `fetch()` có thật sự giữ bộ nhớ thấp không?
   Vì sao, và sửa thế nào? (mục 5.4)
8. Vì sao duyệt `SplPriorityQueue` hai lần cho kết quả khác nhau? Làm sao để các job cùng priority ra
   theo thứ tự thêm vào?
9. Khi nào chọn `SplObjectStorage`, khi nào chọn `WeakMap`?
10. Fiber khác generator ở điểm gì cốt lõi? Bên trong fiber gọi `sleep(1)` thì các fiber khác có chạy
    được trong một giây đó không? (mục 10.4, 10.6)

## Bài tập

1. **Iterator và IteratorAggregate.** Viết class `Playlist` giữ danh sách bài hát (tên, thời lượng giây),
   implement `IteratorAggregate` và `Countable`. `getIterator()` viết bằng generator, key là số thứ tự bắt
   đầu từ 1. Thêm method `longerThan(int $seconds): Generator` chỉ trả các bài dài hơn ngưỡng. Kiểm tra
   duyệt lồng hai vòng `foreach` cho đủ mọi cặp.
2. **Pipeline lười.** Viết các hàm generator `readCsv(string $path)`, `filterLazy`, `mapLazy`, `take` và
   một hàm `batch(iterable $items, int $size): Generator` trả từng lô `$size` phần tử (lô cuối có thể ít
   hơn). Dùng chúng xử lý một file CSV tự sinh 200 000 dòng (`id,email,amount`): lọc dòng có `amount` lớn
   hơn 500, in ra từng lô 1 000 dòng. In `memory_get_peak_usage()` cuối chương trình, rồi so với cách đọc
   bằng `file()` và `array_filter`.
3. **Cấu trúc dữ liệu SPL.** Cho một lưới ô vuông dạng mảng chuỗi (`#` là tường, `.` là đường đi). Viết
   hàm tìm đường ngắn nhất từ ô trái trên tới ô phải dưới bằng BFS với `SplQueue`. Sau đó gán trọng số cho
   từng ô và viết lại bằng Dijkstra với `SplPriorityQueue` (chú ý: priority càng cao càng ra trước, còn
   Dijkstra cần khoảng cách nhỏ nhất ra trước).
4. **Fiber.** Mở rộng `Loop` ở mục 10.5: thêm hàm `spawn` trả về một object `Task` có method `await()`
   (gọi từ trong một fiber khác, dừng cho tới khi task kia xong và trả về giá trị `return` của nó). Viết
   ví dụ ba task "gọi API" giả lập bằng `delay()` chạy xen kẽ, một task thứ tư chờ cả ba rồi in tổng thời
   gian ảo. Chạy trên PHP 8.1 trở lên.

## Đọc thêm

- PHP manual: [Object Iteration](https://www.php.net/manual/en/language.oop5.iterations.php),
  [Iterator](https://www.php.net/manual/en/class.iterator.php),
  [IteratorAggregate](https://www.php.net/manual/en/class.iteratoraggregate.php),
  [Traversable](https://www.php.net/manual/en/class.traversable.php),
  [iterator_to_array](https://www.php.net/manual/en/function.iterator-to-array.php),
  [iterator_count](https://www.php.net/manual/en/function.iterator-count.php)
- PHP manual: [Generators overview](https://www.php.net/manual/en/language.generators.overview.php),
  [Generator syntax](https://www.php.net/manual/en/language.generators.syntax.php),
  [Generators vs Iterator objects](https://www.php.net/manual/en/language.generators.comparison.php),
  [Generator class](https://www.php.net/manual/en/class.generator.php),
  [Generator::send](https://www.php.net/manual/en/generator.send.php),
  [Generator::throw](https://www.php.net/manual/en/generator.throw.php)
- PHP manual: [SPL](https://www.php.net/manual/en/book.spl.php),
  [SPL Iterators](https://www.php.net/manual/en/spl.iterators.php),
  [SPL Datastructures](https://www.php.net/manual/en/spl.datastructures.php),
  [SplPriorityQueue](https://www.php.net/manual/en/class.splpriorityqueue.php),
  [SplFixedArray](https://www.php.net/manual/en/class.splfixedarray.php),
  [SplObjectStorage](https://www.php.net/manual/en/class.splobjectstorage.php),
  [ArrayObject](https://www.php.net/manual/en/class.arrayobject.php),
  [Buffered and Unbuffered queries](https://www.php.net/manual/en/mysqlinfo.concepts.buffering.php)
- PHP manual: [Fibers](https://www.php.net/manual/en/language.fibers.php),
  [Fiber class](https://www.php.net/manual/en/class.fiber.php); [RFC Fibers](https://wiki.php.net/rfc/fibers)
- [RFC Deprecations for PHP 8.5](https://wiki.php.net/rfc/deprecations_php_8_5) (SplObjectStorage,
  ArrayObject với object); [UPGRADING PHP 8.5](https://github.com/php/php-src/blob/PHP-8.5/UPGRADING),
  [UPGRADING PHP 8.4](https://github.com/php/php-src/blob/PHP-8.4/UPGRADING)
- php-src: [`Zend/zend_generators.c`](https://github.com/php/php-src/blob/PHP-8.5/Zend/zend_generators.c),
  [`Zend/zend_fibers.c`](https://github.com/php/php-src/blob/PHP-8.5/Zend/zend_fibers.c),
  [`ext/spl/spl_heap.c`](https://github.com/php/php-src/blob/PHP-8.5/ext/spl/spl_heap.c)
- Laravel 13: [Collections, Lazy Collections](https://laravel.com/docs/13.x/collections#lazy-collections),
  [Eloquent: chunking, lazy, cursor](https://laravel.com/docs/13.x/eloquent#chunking-results),
  [Concurrency](https://laravel.com/docs/13.x/concurrency)
- Bob Nystrom, [What Color is Your Function?](https://journal.stuffwithstuff.com/2015/02/01/what-color-is-your-function/)
  (bài viết mà RFC Fibers dẫn để giải thích vấn đề)
- [Revolt event loop](https://revolt.run/), [AMPHP](https://amphp.org/)
