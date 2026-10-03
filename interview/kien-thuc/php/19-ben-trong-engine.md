# Chương 19. Bên trong Zend Engine

> [← Mục lục](README.md) · [← Chương 18: PHP-FPM, Nginx và OPcache trên production](18-fpm-nginx-opcache.md) · [Chương 20: Hiệu năng và profiling →](20-hieu-nang.md)

**Bạn sẽ học được:**

- Một giá trị PHP thực sự trông thế nào trong bộ nhớ (*zval*), kiểu nào nằm gọn trong zval, kiểu nào
  nằm riêng và có bộ đếm tham chiếu (*refcount*).
- Cơ chế *copy-on-write* và *separation*: vì sao gán hay truyền một array lớn gần như miễn phí, lúc
  nào thì engine thật sự copy, và reference `&` được cài đặt ra sao (và vì sao nó không làm code nhanh
  hơn).
- Cấu trúc bên trong của string (*zend_string*, *interned string*), array (*HashTable*, packed array
  và hash array) và object (*object store*, *object handle*).
- PHP giải phóng bộ nhớ thế nào: refcount cộng với *cycle collector*; đọc `gc_status()`, dùng
  `gc_collect_cycles()`; ý nghĩa thật của `memory_limit` và `memory_get_usage(true/false)`.
- Nhìn lại quá trình compile thành opcode bằng con mắt của engine, và JIT: chế độ tracing và function,
  JIT mới dựa trên IR từ PHP 8.4.

**Cần biết trước:** [Chương 02](02-php-chay-nhu-the-nao.md) (opcode, Zend VM, OPcache),
[Chương 04](04-kieu-du-lieu.md) (các kiểu dữ liệu), [Chương 06](06-mang.md) (array, copy-on-write nhìn
từ bên ngoài), [Chương 08](08-ham.md) (truyền tham số, reference `&`), [Chương 09](09-oop-co-ban.md)
(object, destructor, object là handle). Mục JIT sẽ dễ hơn nếu đã đọc
[Chương 18](18-fpm-nginx-opcache.md) về OPcache.

Mọi ví dụ PHP trong chương là file hoàn chỉnh (hoặc đoạn ngắn có thể dán vào một file như vậy). Chạy
bằng `php ten-file.php`, hoặc không cần cài gì: `docker run --rm -it php:8.5-cli php -a` rồi dán code
vào. Output ghi trong comment đã được chạy thật trên PHP 8.5, trừ chỗ ghi "output minh hoạ". Các
ví dụ đo bộ nhớ được chạy trên một bản PHP 32-bit (php-wasm) nên được ghi là output minh hoạ; con trỏ
ở đó 4 byte thay vì 8. Chỗ nào ghi "tính cho máy 64-bit" thì con số đã được tính lại theo kích thước
struct trong php-src; số đo trên máy bạn vẫn có thể lệch chút ít, hãy tự chạy lại. Đoạn mã C
trích từ mã nguồn php-src nhánh `PHP-8.5`, đã lược bớt những trường không cần cho bài; chú thích tiếng
Việt là của giáo trình. Các con số kích thước tính bằng byte là cho máy 64-bit (x86-64, ARM64), loại
máy chạy PHP gần như duy nhất hiện nay.

---

## 1. Vì sao phải nhìn vào bên trong engine

### 1.1 Zend Engine là gì

Chương trình `php` mà bạn cài vào máy được viết bằng ngôn ngữ C. Phần lõi của nó, thứ biên dịch code
PHP thành opcode, chạy opcode, quản lý biến, bộ nhớ, array và object, tên là *Zend Engine*. Tên
"Zend" ghép từ tên hai tác giả viết lại lõi PHP năm 1999 là Zeev Suraski và Andi Gutmans
([Chương 01](01-php-la-gi.md)). PHP 7.0 đi kèm Zend Engine 3.0, bản viết lại lớn nhất về cách lưu giá
trị trong bộ nhớ; các bản PHP 8.x vẫn giữ thiết kế đó và chỉ cải tiến thêm. Vì vậy hầu hết những gì
chương này mô tả đúng cho PHP 7.0 trở đi; chỗ nào khác giữa các phiên bản sẽ ghi rõ.

Trong kho mã nguồn `php-src` trên GitHub, Zend Engine nằm ở thư mục `Zend/`. Vài file sẽ được nhắc tới
nhiều lần:

| File | Chứa gì |
|---|---|
| `Zend/zend_types.h` | Định nghĩa zval, string, array, object, reference |
| `Zend/zend_hash.c` | Cài đặt HashTable (array) |
| `Zend/zend_gc.c` | Cycle collector |
| `Zend/zend_alloc.c` | Bộ cấp phát bộ nhớ riêng của PHP (Zend MM) |
| `Zend/zend_objects_API.c` | Object store |
| `Zend/zend_vm_def.h` | Handler của từng opcode |
| `ext/opcache/jit/` | JIT |

Bạn không cần biết C để đọc chương này. Mỗi đoạn mã C chỉ để bạn thấy "nó có thật", và luôn có giải
thích bằng lời ngay sau.

### 1.2 Biết bên trong để làm gì

Người viết PHP hằng ngày không gọi trực tiếp thứ gì ở tầng này. Nhưng rất nhiều câu hỏi thực tế chỉ
trả lời được khi hiểu nó:

- Truyền một array một triệu phần tử vào hàm có tốn một triệu lần copy không? Vì sao `memory_get_usage()`
  không đổi khi gán, nhưng tăng vọt khi sửa một phần tử?
- Viết `function f(array &$data)` cho "đỡ copy" có đúng không?
- Vì sao một list một triệu số nguyên tốn khoảng 16 MiB, còn cùng dữ liệu đó với key lộn xộn tốn
  khoảng 40 MiB?
- Vì sao destructor của object thường chạy ngay khi bỏ biến, nhưng có lúc chạy rất muộn?
- Queue worker chạy vài giờ thì RAM cứ tăng, trong khi code "không có gì giữ lại". Bắt đầu tìm ở
  đâu?
- `memory_limit = 128M` giới hạn chính xác cái gì? Vì sao `memory_get_usage()` báo 20 MB mà `top` báo
  process dùng 80 MB?
- Bật JIT có làm app Laravel nhanh lên không?

Đây cũng là nhóm câu hỏi phân biệt người dùng PHP lâu năm với người hiểu PHP, nên rất hay gặp khi
phỏng vấn vị trí senior.

### 1.3 Công cụ để tự quan sát

Chương này cố gắng để bạn tự thấy mọi điều được nói, thay vì phải tin. Các công cụ:

| Công cụ | Cho thấy gì | Mục |
|---|---|---|
| `debug_zval_dump()` | Kiểu, refcount, string có interned không, array có packed không (PHP 8.4+) | 2, 3, 5, 6 |
| `memory_get_usage()`, `memory_get_peak_usage()` | Bộ nhớ engine đang cấp cho script | 6, 9 |
| `spl_object_id()`, `var_dump()` | Handle của object | 7 |
| `gc_status()`, `gc_collect_cycles()` | Hoạt động của cycle collector | 8 |
| `opcache.opt_debug_level` | Opcode sau khi compile | 10 |
| `opcache_get_status()` | Trạng thái OPcache và JIT | 11 |
| Mã nguồn php-src | Mọi thứ còn lại | Cả chương |

⚠️ Những con số mà các công cụ này in ra phụ thuộc vào chi tiết cài đặt (phiên bản PHP, OPcache bật
hay tắt, có extension debug nào không). Dùng chúng để học và để so sánh tương đối, đừng viết code
production dựa vào một giá trị refcount cụ thể.

---

## 2. zval: mọi giá trị PHP trông thế nào trong bộ nhớ

### 2.1 Bài toán: một biến có thể chứa bất cứ thứ gì

Trong C, Java hay Go, kiểu của biến được biết lúc biên dịch: biến `int` luôn là 8 byte số nguyên,
compiler biết chính xác phải đọc và cộng nó thế nào. PHP thì khác. Cùng một biến `$x` lúc này chứa
số, lúc sau chứa chuỗi, lúc sau nữa chứa array ([Chương 04](04-kieu-du-lieu.md)). Engine viết bằng C
nên phải có một kiểu C duy nhất đủ sức chứa **mọi** giá trị PHP, kèm theo thông tin "giá trị này đang
là kiểu gì" để biết phải xử lý nó ra sao.

Kiểu C đó tên là *zval* (viết tắt của "Zend value"). Mọi chỗ chứa giá trị trong PHP đều là một zval:
một biến, một tham số, một phần tử array, một property của object, một hằng số, giá trị trả về của
hàm.

### 2.2 Cấu trúc của zval

Định nghĩa trong `Zend/zend_types.h` (lược bớt):

```c
typedef union _zend_value {
    zend_long         lval;     /* int: số nằm thẳng ở đây */
    double            dval;     /* float: số nằm thẳng ở đây */
    zend_refcounted  *counted;  /* các trường còn lại đều là CON TRỎ */
    zend_string      *str;      /*   tới một vùng nhớ khác */
    zend_array       *arr;
    zend_object      *obj;
    zend_resource    *res;
    zend_reference   *ref;
    ...
} zend_value;

struct _zval_struct {
    zend_value value;           /* 8 byte */
    union {
        uint32_t type_info;     /* 4 byte: type (1 byte) + type_flags (1 byte) + 2 byte phụ */
        ...
    } u1;
    union {
        uint32_t next;          /* 4 byte, mỗi chỗ dùng một kiểu: chuỗi va chạm trong hash, */
        uint32_t fe_pos;        /* vị trí của foreach, số dòng của nút AST, ... */
        ...
    } u2;
};
```

Vẽ ra:

```
zval: 16 byte
+--------------------------------+--------+------------+---------+----------------------+
| value (8 byte)                 | type   | type_flags | (2 byte)| u2 (4 byte)          |
| một số int, một số float,      | 1 byte | 1 byte     |         | dùng tuỳ ngữ cảnh    |
| hoặc một con trỏ               |<------ u1.type_info (4 byte) ->|                      |
+--------------------------------+--------------------------------+----------------------+
```

Đọc từng phần:

- `value` là một *union*: một vùng nhớ 8 byte mà nhiều trường cùng dùng chung, tại một thời điểm chỉ
  một trường có nghĩa. Nếu giá trị là int thì 8 byte đó là con số; nếu là float thì là số thực; nếu là
  string thì là địa chỉ của một `zend_string` nằm ở chỗ khác.
- `type` cho biết trường nào của union đang có nghĩa. Không có `type` thì 8 byte kia chỉ là một dãy
  bit vô nghĩa.
- `type_flags` là vài bit tóm tắt tính chất của kiểu, dùng để engine quyết định nhanh (mục 2.5).
- `u2` có mặt vì một lý do rất thực dụng: 8 byte `value` cộng 4 byte `u1` là 12 byte, nhưng trên máy
  64-bit, struct chứa trường 8 byte được căn lề (*padding*) lên bội số của 8, tức 16 byte. 4 byte thừa
  ra đằng nào cũng tốn, nên engine đặt tên cho nó và dùng vào việc riêng của từng ngữ cảnh. Ví dụ khi
  zval nằm trong array dạng hash, `u2.next` nối các phần tử bị trùng ô hash (mục 6.3).

Kích thước 16 byte này là con số nên nhớ: nó là chi phí tối thiểu của mọi giá trị PHP.

### 2.3 Các type

Giá trị của `type` (PHP 8.5):

| Hằng | Số | Ý nghĩa |
|---|---|---|
| `IS_UNDEF` | 0 | "Chưa có giá trị": biến chưa gán, đã `unset`, ô trống trong array |
| `IS_NULL` | 1 | `null` |
| `IS_FALSE` | 2 | `false` |
| `IS_TRUE` | 3 | `true` |
| `IS_LONG` | 4 | `int` (tên lịch sử: kiểu `long` của C) |
| `IS_DOUBLE` | 5 | `float` |
| `IS_STRING` | 6 | `string` |
| `IS_ARRAY` | 7 | `array` |
| `IS_OBJECT` | 8 | `object` |
| `IS_RESOURCE` | 9 | `resource` |
| `IS_REFERENCE` | 10 | Một reference tạo bởi `&` (mục 4) |

Vài điểm đáng chú ý:

- `bool` không có type `IS_BOOL`. Hai giá trị `true` và `false` là hai type khác nhau, nên giá trị
  nằm luôn trong type, phần `value` không dùng tới. Kiểm tra `$x === true` chỉ cần nhìn type.
- `IS_UNDEF` không phải kiểu mà người dùng PHP nhìn thấy. Nó là cách engine đánh dấu "ô này trống"
  mà không cần cấp phát gì. Khi bạn đọc một biến chưa gán, engine thấy `IS_UNDEF`, phát warning
  "Undefined variable" và trả về `null` cho biểu thức.
- `IS_REFERENCE` cũng không phải kiểu userland: `gettype()` không bao giờ trả về "reference". Engine
  luôn "đi xuyên" qua reference để lấy giá trị bên trong trước khi làm gì đó với nó.
- Ngoài danh sách trên còn vài type chỉ dùng nội bộ (`IS_INDIRECT`, `IS_PTR`, `IS_CONSTANT_AST`...),
  không bao giờ xuất hiện trong biến của bạn.

### 2.4 Zval nằm ở đâu

Một chi tiết thiết kế quan trọng của PHP 7 trở đi: zval **không được cấp phát riêng lẻ**. Nó được
nhúng thẳng vào chỗ chứa nó:

- Biến cục bộ của một hàm là một ô zval trong *call frame* của lần gọi hàm đó (một mảng zval liền
  nhau, [Chương 02](02-php-chay-nhu-the-nao.md) mục 2.6).
- Phần tử array là một zval nằm trong vùng dữ liệu của array (mục 6).
- Property đã khai báo của object là một zval nằm ngay trong khối nhớ của object (mục 7).
- Hằng số trong code (literal `42`, `'abc'`) là zval nằm trong bảng hằng của op_array.

Vì vậy tạo một biến int mới không phải "xin bộ nhớ": nó chỉ là ghi 16 byte vào một ô đã có sẵn. PHP 5
làm khác: mỗi zval được cấp phát riêng trên heap, kèm theo thông tin phụ, đó là một trong những lý do
chính khiến PHP 7 nhanh và tiết kiệm bộ nhớ hơn hẳn PHP 5 (mục 6.6 có số đo).

### 2.5 Hai nhóm giá trị: nằm trong zval và nằm ngoài zval

8 byte của `value` chứa vừa một int (8 byte) hoặc một float (8 byte, chuẩn IEEE 754). `null`, `true`,
`false` thì không cần chỗ nào ngoài type. Bốn kiểu này nằm **trọn trong zval**.

String, array, object thì không thể nhét vào 8 byte. Chúng nằm ở một vùng nhớ riêng trên heap, và zval
chỉ giữ con trỏ tới vùng đó:

```
$n = 42;                         $s = str_repeat('ab', 3);

zval của $n                      zval của $s                  zend_string (vùng nhớ riêng)
+-------------+                  +-------------+              +---------------------------+
| value: 42   |                  | value: ─────┼────────────> | refcount: 1               |
| type: LONG  |                  | type: STRING|              | len: 6, "ababab"          |
+-------------+                  +-------------+              +---------------------------+
```

Mọi vùng nhớ riêng như vậy (string, array, object, resource, reference) đều mở đầu bằng cùng một
*header* 8 byte:

```c
typedef struct _zend_refcounted_h {
    uint32_t refcount;              /* bao nhiêu chỗ đang trỏ tới vùng nhớ này */
    union {
        uint32_t type_info;         /* loại vùng nhớ, vài cờ, và thông tin cho GC */
    } u;
} zend_refcounted_h;
```

- `refcount` là bộ đếm tham chiếu: có bao nhiêu zval đang trỏ tới vùng nhớ này. Mục 3 nói kỹ.
- `type_info` gồm 4 bit loại, 6 bit cờ (ví dụ cờ *immutable*: "đừng bao giờ sửa refcount của tôi") và
  22 bit còn lại dành cho cycle collector ghi vị trí trong *root buffer* và "màu" đánh dấu (mục 8).

Điểm mấu chốt của thiết kế PHP 7: **refcount nằm ở giá trị lớn, không nằm ở zval**. Hai biến cùng
trỏ một array là hai zval 16 byte riêng biệt, cùng mang một con trỏ, và refcount của array là 2. Ở
PHP 5 thì ngược lại: refcount nằm trên zval, và một zval được nhiều biến dùng chung.

### 2.6 Refcounted, collectable và immutable

Hai tính chất được ghi thành bit trong `type_flags` của zval, để engine kiểm tra bằng một phép AND
thay vì phải đọc giá trị:

- *Refcounted*: giá trị có refcount, nên khi copy zval phải tăng refcount, khi bỏ zval phải giảm
  refcount (và giải phóng nếu về 0).
- *Collectable*: giá trị có thể chứa giá trị khác, nên có thể nằm trong một vòng tham chiếu; cycle
  collector phải để ý tới nó (mục 8).

| Kiểu PHP | Nằm ở đâu | Refcounted | Collectable | Ghi chú |
|---|---|---|---|---|
| `null`, `bool`, `int`, `float` | Trong zval | Không | Không | Copy là copy 16 byte |
| `string` thường | `zend_string` | Có | Không | String không chứa được giá trị khác nên không tạo vòng |
| `string` interned | `zend_string` dùng chung | Không | Không | Mục 5.3 |
| `array` thường | `zend_array` | Có | Có | |
| `array` immutable | `zend_array` dùng chung | Không | Không | Array rỗng hằng, array literal trong bộ nhớ của OPcache |
| `object` | `zend_object` | Có | Có | |
| `resource` | `zend_resource` | Có | Không | File, socket... |
| reference | `zend_reference` | Có | Có | GC nhìn vào giá trị bên trong reference |

Vì string và array lúc thì refcounted, lúc thì không, engine không quyết định theo type mà theo bit
trong từng zval. Giá trị *immutable* (bất biến) là giá trị được đánh dấu không bao giờ đổi và không
bao giờ bị giải phóng giữa chừng: engine dùng lại nó ở bất kỳ đâu mà không cần tăng giảm refcount.
Nguồn chính của giá trị immutable:

1. Array rỗng viết trong code: `$x = [];` cho `$x` trỏ tới một array rỗng hằng duy nhất của engine
   (`zend_empty_array`), không cấp phát gì cho tới khi bạn thêm phần tử đầu tiên. (Array rỗng do hàm
   trả về, ví dụ `array_filter()` không giữ lại gì, thì thường là array thường, có refcount.)
2. Interned string (mục 5.3).
3. Khi bật OPcache: string và array literal của script được lưu trong *shared memory* (vùng nhớ dùng
   chung giữa các process PHP-FPM). Nhiều process cùng đọc một vùng nhớ thì không thể để process nào
   ghi refcount vào đó, nên chúng phải immutable.

### 2.7 Tự xem bằng debug_zval_dump()

`debug_zval_dump()` giống `var_dump()` nhưng in thêm thông tin của engine: refcount, string có
interned không, và từ PHP 8.4 là array có packed không.

```php
<?php
declare(strict_types=1);

$n = 42;
debug_zval_dump($n);      // in ra: int(42)
$f = 1.5;
debug_zval_dump($f);      // in ra: float(1.5)
$b = true;
debug_zval_dump($b);      // in ra: bool(true)

$s = 'hello';
debug_zval_dump($s);      // in ra: string(5) "hello" interned
$t = str_repeat('ab', 3);
debug_zval_dump($t);      // in ra: string(6) "ababab" refcount(2)

$e = [];
debug_zval_dump($e);      // in ra: array(0) interned {}   (viết gọn trên một dòng)
$a = range(1, 3);
debug_zval_dump($a);      // in ra: array(3) packed refcount(2){ ... }

$o = new stdClass();
debug_zval_dump($o);      // in ra: object(stdClass)#1 (0) refcount(2){ }
```

Cách đọc:

- `int`, `float`, `bool` không có refcount: chúng nằm trong zval, không có gì để đếm.
- `'hello'` là literal trong code nên được *intern* lúc compile (mục 5.3): không có refcount, in chữ
  `interned`.
- `str_repeat()` tạo string mới lúc chạy: refcounted. Vì sao là 2 trong khi chỉ có một biến `$t`?
  Vì `debug_zval_dump()` nhận tham số **theo giá trị**, nên trong lúc hàm chạy, chính tham số của nó
  cũng đang trỏ tới string đó. Con số luôn cao hơn số chỗ dùng thật của bạn 1 đơn vị. Manual của hàm
  này nói rõ điều đó.
- Array rỗng in chữ `interned` vì nó là array rỗng hằng immutable (mục 2.6): `debug_zval_dump()` dùng
  chung chữ `interned` cho mọi giá trị immutable.
- `packed` là dạng tối ưu của array cho list (mục 6.5). PHP 8.3 trở về trước không in chữ này.

⚠️ Đừng thí nghiệm refcount bằng array literal kiểu `$x = [1, 2, 3];`. Khi OPcache tắt (mặc định với
CLI), op_array cũng giữ một tham chiếu tới literal đó, nên `debug_zval_dump($x)` in `refcount(3)`
dù bạn chỉ có một biến. Khi OPcache bật, literal lại thành immutable và in `interned`. Dùng giá trị
tạo lúc chạy như `range()`, `str_repeat()` để con số dễ đoán.

### 2.8 Đối chiếu Java và Go

| | PHP | Java | Go |
|---|---|---|---|
| Biến biết kiểu lúc nào | Lúc chạy, kiểu nằm trong zval | Lúc biên dịch | Lúc biên dịch |
| Số nguyên nằm ở đâu | Trong zval 16 byte | `int` 4 byte nằm thẳng trong biến hay field; `Integer` là object trên heap | `int` 8 byte nằm thẳng trong biến |
| Giá trị "động" | Mọi giá trị | `Object`: biến giữ reference, object mang header chứa thông tin class | `interface{}`/`any`: 2 word (con trỏ kiểu và con trỏ dữ liệu) |

Zval của PHP gần với `any` của Go nhất: cả hai mang "kiểu" đi kèm "giá trị". Khác biệt là PHP dùng nó
cho mọi thứ, còn Go chỉ dùng khi bạn chủ động khai báo `any`.

---

## 3. Refcount và copy-on-write

### 3.1 Refcount tăng, giảm khi nào

*Reference counting* (đếm tham chiếu) là cơ chế quản lý bộ nhớ chính của PHP. Mỗi giá trị refcounted
(string thường, array thường, object, resource, reference) mang một con số `refcount` trong header:
số zval đang trỏ tới nó.

Refcount **tăng** khi có thêm một chỗ trỏ tới giá trị:

- Gán sang biến khác: `$b = $a;`
- Truyền vào hàm theo giá trị: `f($a)` (tham số `$param` là một zval mới trỏ cùng giá trị).
- Đặt vào array hay property: `$list[] = $a;`, `$obj->data = $a;`
- Closure bắt biến bằng `use ($a)`.
- `foreach ($a as $v)` giữ thêm một tham chiếu tới array trong suốt vòng lặp (mục 3.4).

Refcount **giảm** khi một chỗ thôi trỏ tới giá trị:

- Biến bị gán đè: `$a = null;` hay `$a = 'khác';`
- `unset($a);`
- Hàm kết thúc: mọi biến cục bộ và tham số bị huỷ.
- Phần tử bị xoá khỏi array, hoặc cả array chứa nó bị giải phóng.

Khi refcount **về 0**, engine giải phóng giá trị **ngay tại chỗ**, không đợi ai. Với object, điều đó
có nghĩa `__destruct()` chạy ngay lúc đó ([Chương 09](09-oop-co-ban.md) mục 4.4 có ví dụ đầy đủ). Giải
phóng có tính dây chuyền: giải phóng một array thì engine giảm refcount của từng phần tử bên trong, phần
tử nào về 0 thì cũng được giải phóng, cứ thế lan xuống.

Hai câu hỏi thường gặp:

- Int và float thì sao? Chúng không có refcount. `$b = $a` với `$a = 42` chỉ copy 16 byte zval, và
  hai biến hoàn toàn độc lập. Không có gì để chia sẻ, cũng không có gì để giải phóng.
- Refcount có chặn được mọi leak không? Không. Một nhóm giá trị trỏ vòng vào nhau sẽ không bao giờ về 0
  dù không còn ai dùng. Đó là việc của cycle collector (mục 8).

### 3.2 Copy-on-write: chia sẻ khi gán, copy khi ghi

Về ngữ nghĩa, array và string của PHP là *kiểu giá trị*: `$b = $a` cho `$b` một bản "của riêng nó",
sửa `$b` không ảnh hưởng `$a` ([Chương 06](06-mang.md) mục 9). Nếu engine làm đúng như lời đó, mỗi lần
gán hay truyền tham số phải copy toàn bộ dữ liệu, rất tốn.

*Copy-on-write* (COW, "copy khi ghi") là cách engine giữ đúng ngữ nghĩa giá trị mà không trả giá đó:

1. Gán hoặc truyền: chỉ copy zval 16 byte và tăng refcount. Hai biến cùng trỏ một vùng dữ liệu.
2. Đọc: không có gì xảy ra, ai đọc cũng thấy cùng dữ liệu, đúng như mong đợi.
3. Ghi: trước khi ghi, engine kiểm tra refcount. Nếu bằng 1 (chỉ mình biến này dùng), ghi thẳng vào.
   Nếu lớn hơn 1, engine copy dữ liệu ra một bản mới chỉ cho biến đang ghi, giảm refcount của bản cũ,
   rồi mới ghi vào bản mới. Bước này gọi là *separation* (tách).

Theo dõi refcount qua từng bước bằng `debug_zval_dump()`:

```php
<?php
declare(strict_types=1);

function f(array $param): void
{
    debug_zval_dump($param);   // (3)
    $param[] = 4;
    debug_zval_dump($param);   // (4)
}

$a = range(1, 3);
debug_zval_dump($a);           // (1)
$b = $a;
debug_zval_dump($a);           // (2)
f($a);
debug_zval_dump($a);           // (5)
$b[] = 99;
debug_zval_dump($a);           // (6)
debug_zval_dump($b);           // (7)

// in ra (chỉ giữ dòng đầu của mỗi lần dump):
// array(3) packed refcount(2){     (1)
// array(3) packed refcount(3){     (2)
// array(3) packed refcount(4){     (3)
// array(4) packed refcount(2){     (4)
// array(3) packed refcount(3){     (5)
// array(3) packed refcount(2){     (6)
// array(4) packed refcount(2){     (7)
```

Nhớ trừ 1 cho chính tham số của `debug_zval_dump()`:

| Bước | Refcount thật | Ai đang trỏ tới array `[1,2,3]` | Chuyện gì xảy ra |
|---|---|---|---|
| (1) | 1 | `$a` | `range()` tạo array mới |
| (2) | 2 | `$a`, `$b` | Gán: không copy, chỉ tăng refcount |
| (3) | 3 | `$a`, `$b`, `$param` | Truyền tham số: cũng chỉ tăng refcount |
| (4) | 1 (bản mới) | `$param` trỏ bản mới `[1,2,3,4]` | Ghi khi refcount 3 > 1: separation. Bản cũ còn 2 |
| (5) | 2 | `$a`, `$b` | Hàm kết thúc: `$param` bị huỷ, bản `[1,2,3,4]` về 0 và được giải phóng |
| (6) | 1 | `$a` | `$b[] = 99` khi refcount 2: separation, `$b` sang bản mới |
| (7) | 1 | `$b` trỏ bản `[1,2,3,99]` | |

```
sau (2)                               sau (4), đang ở trong f()

$a ──┐                                $a ──┐
     ├──> [1,2,3] refcount=2               ├──> [1,2,3]   refcount=2
$b ──┘                                $b ──┘
                                      $param ──> [1,2,3,4] refcount=1   (bản copy)
```

Quan sát quan trọng: trong cả chuỗi trên, dữ liệu chỉ bị copy hai lần, đúng hai lần có ghi vào một
array đang được chia sẻ. Bao nhiêu lần gán, truyền, đọc cũng không tốn gì. [Chương 06](06-mang.md) mục
9.2 đo bằng `memory_get_usage()` với array một triệu phần tử: gán thêm 0 MiB, ghi lần đầu thêm khoảng
16 MiB.

### 3.3 Separation xảy ra ở đâu, copy những gì

Mỗi opcode ghi vào array (gán phần tử `$a[k] = v`, thêm `$a[] = v`, `unset($a[k])`...) đều gọi một
đoạn kiểm tra trước khi ghi. Trong php-src đó là macro `SEPARATE_ARRAY` (lược bớt):

```c
#define SEPARATE_ARRAY(zv) do {
    zend_array *_arr = Z_ARR_P(zv);
    if (GC_REFCOUNT(_arr) > 1) {            /* đang được chia sẻ? */
        ZVAL_ARR(zv, zend_array_dup(_arr)); /* copy ra bản mới cho zval này */
        GC_TRY_DELREF(_arr);                /* bản cũ bớt một người dùng */
    }
} while (0)
```

Handler của opcode `ASSIGN_DIM` (gán vào một phần tử) gọi macro này trước khi ghi. Các hàm nhận array theo
reference như `sort()`, `array_push()`, `shuffle()` cũng phải tách trước khi sửa nếu array đang được
chia sẻ.

`zend_array_dup()` copy **một tầng**: nó cấp phát vùng dữ liệu mới cho array ngoài cùng và copy các
zval phần tử. Phần tử nào là giá trị refcounted (string, array con, object) thì chỉ được tăng refcount,
không bị copy sâu. Nên khi bạn ghi vào một array nhiều tầng, chỉ những tầng nằm trên đường ghi mới bị
tách:

```php
<?php
declare(strict_types=1);

$data = [
    'users'  => range(1, 1000),
    'orders' => range(1, 1000),
];
$copy = $data;               // chưa copy gì
$copy['users'][] = 1001;     // ghi vào tầng thứ hai

debug_zval_dump($data);
debug_zval_dump($copy);

// in ra (bỏ các phần tử số):
// array(2) refcount(2){
//   ["users"]=>
//   array(1000) packed refcount(1){ ... }
//   ["orders"]=>
//   array(1000) packed refcount(2){ ... }
// }
// array(2) refcount(2){
//   ["users"]=>
//   array(1001) packed refcount(1){ ... }
//   ["orders"]=>
//   array(1000) packed refcount(2){ ... }
// }
```

(Array con được in đúng refcount thật, không cộng 1, vì chúng không đi qua tham số của
`debug_zval_dump()`.)

```
$data ──> [ users: ───> [1..1000]     refcount=1
            orders: ──┐
          ]           ├─> [1..1000]   refcount=2   (vẫn dùng chung)
$copy ──> [ orders: ──┘
            users: ───> [1..1001]     refcount=1   (bản tách ra)
          ]
```

Lệnh `$copy['users'][] = 1001` đã: tách array ngoài (`$copy` có 2 người dùng), rồi tách array
`users` bên trong (sau khi tách tầng ngoài, `users` có 2 người dùng), rồi mới thêm phần tử. Array
`orders` không bị đụng tới nên vẫn dùng chung. Chi phí của một lần ghi tỉ lệ với kích thước các tầng
bị tách, không phải kích thước toàn bộ cây dữ liệu.

### 3.4 Những chỗ COW hay gặp trong code thật

**`foreach` theo giá trị.** `foreach ($a as $v)` giữ thêm một tham chiếu tới array trong suốt vòng
lặp. Ghi vào `$a` bên trong vòng lặp làm `$a` tách ra bản mới, còn vòng lặp tiếp tục duyệt bản cũ:

```php
<?php
declare(strict_types=1);

$a = range(1, 3);
foreach ($a as $i => $v) {
    if ($i === 0) {
        debug_zval_dump($a);     // in ra: array(3) packed refcount(3){ ... }  ($a, foreach, tham số)
        $a[] = $v * 10;          // refcount > 1: tách
        debug_zval_dump($a);     // in ra: array(4) packed refcount(2){ ... }  bản mới
    }
}
echo implode(',', $a), "\n";     // in ra: 1,2,3,10   vòng lặp không thấy phần tử mới
```

Đây là lý do "sửa array trong khi đang `foreach` nó" an toàn trong PHP (khác Java, nơi sửa
`ArrayList` khi đang duyệt ném `ConcurrentModificationException`), và cũng là lý do bạn phải trả một
lần copy nếu làm vậy.

**Trả array từ hàm.** `return $local;` chỉ chuyển zval ra ngoài; biến cục bộ bị huỷ ngay sau đó nên
refcount vẫn là 1. Không có copy nào, dù array lớn tới đâu. Hàm "nhận array, trả array mới" là kiểu
viết vừa rõ ràng vừa rẻ.

**Nối chuỗi.** String cũng COW. Với `$s .= 'y'`, engine gọi `zend_string_extend()`: nếu string không
phải interned và refcount bằng 1, nó nới vùng nhớ hiện có (realloc) rồi ghi thêm vào cuối; ngược lại nó
cấp phát string mới và copy nội dung cũ sang. Vì vậy nối chuỗi trong vòng lặp vào một biến mà không ai
khác giữ là rẻ. Nhưng nếu biến đó đang được chia sẻ (ví dụ vừa được đưa vào một array), lần nối đầu
tiên phải copy toàn bộ chuỗi.

**Hàm nhận tham số theo reference.** `sort($a)` khi `$a` đang chia sẻ với `$b` thì phải tách, vì sắp
xếp xong `$b` không được thấy thay đổi. Đây là một lần copy toàn bộ array, dễ bị bỏ sót khi đo hiệu
năng:

```php
<?php
declare(strict_types=1);

// Output minh hoạ, tính cho máy 64-bit từ kích thước struct trong php-src (zval 16 byte, Bucket 32,
// zend_reference 32; khối lớn làm tròn theo trang 4 KiB). Chạy trên php-wasm 32-bit, số 16 in thành 16.1.

$mib = static fn (int $bytes): string => round($bytes / 1048576, 1) . ' MiB';

$a = range(1, 1_000_000);
$b = $a;                         // $a và $b chia sẻ
$m = memory_get_usage();
sort($a);                        // phải tách trước khi sắp xếp
echo $mib(memory_get_usage() - $m), "\n";   // in ra: 16 MiB

$c = range(1, 1_000_000);        // không ai chia sẻ
$m = memory_get_usage();
sort($c);                        // không phải tách: sort xong, bộ nhớ như cũ
echo $mib(memory_get_usage() - $m), "\n";   // in ra: 0 MiB

$s = str_repeat('a', 1_000_000);
$list = [$s];                    // string giờ có refcount 2
$m = memory_get_usage();
$s .= 'b';                       // không nới tại chỗ được: copy cả chuỗi
echo $mib(memory_get_usage() - $m), "\n";   // in ra: 1 MiB
```

### 3.5 Object không có copy-on-write

Object cũng refcounted, nhưng không có bước "tách khi ghi". `$o2 = $o1` copy zval (trỏ cùng
`zend_object`) và tăng refcount; sửa property qua `$o2` thì `$o1` thấy ngay, vì cả hai cùng trỏ một
object. Đây không phải thiếu sót mà là ngữ nghĩa cố ý: object có *danh tính* (identity), hai biến cùng
trỏ một object là chuyện bình thường. Muốn bản riêng thì phải `clone` tường minh. Cách engine tổ chức
object ở mục 7.

| | Array, string | Object |
|---|---|---|
| Gán `$b = $a` | Tăng refcount, chia sẻ dữ liệu | Tăng refcount, chia sẻ object |
| Ghi qua `$b` | Tách nếu refcount > 1, `$a` không đổi | Ghi thẳng vào object chung, `$a` thấy |
| Muốn bản riêng | Không cần làm gì | `clone $a` (copy nông) |

---

## 4. Reference `&` bên trong engine

### 4.1 Nhắc lại: reference là gì

*Reference* (tham chiếu) trong PHP là hai (hoặc nhiều) tên cùng chỉ vào **một ô chứa giá trị**. Ghi
qua tên nào thì mọi tên đều thấy ([Chương 08](08-ham.md) mục 8). Reference khác hẳn khái niệm con
trỏ hay "reference" của Java: không có phép tính địa chỉ, không có "reference tới reference". Manual
PHP mô tả nó giống *hard link* trong hệ thống file Unix: hai tên file cùng trỏ một nội dung.

Câu hỏi của chương này là: "một ô chứa giá trị mà nhiều tên cùng dùng" được cài đặt thế nào, khi zval
vốn được nhúng thẳng vào từng biến?

### 4.2 zend_reference: một chiếc hộp có refcount

Engine giải quyết bằng một lớp gián tiếp. Khi bạn viết `$r = &$a;`:

1. Nếu `$a` chưa phải reference, engine cấp phát một `zend_reference`, chuyển giá trị hiện tại của
   `$a` vào trong nó, rồi đổi zval của `$a` thành type `IS_REFERENCE` trỏ tới chiếc hộp đó.
2. Zval của `$r` cũng thành `IS_REFERENCE` trỏ cùng hộp, và refcount của hộp tăng lên 2.

```c
struct _zend_reference {
    zend_refcounted_h              gc;      /* refcount: bao nhiêu tên đang dùng chung hộp này */
    zval                           val;     /* giá trị thật nằm ở đây */
    zend_property_info_source_list sources; /* typed property nào đang giữ hộp này (mục dưới) */
};
```

```
$a = range(1, 3);                       $r = &$a;

$a ──> [1,2,3] refcount=1               $a ──┐
                                             ├──> zend_reference refcount=2
                                        $r ──┘      val: ──> [1,2,3] refcount=1
```

Mọi thao tác trên `$a` hay `$r` giờ phải đi qua thêm một bước: đọc zval của biến, thấy
`IS_REFERENCE`, đi vào hộp, rồi mới tới giá trị thật. Ghi qua `$r` là ghi vào `val` trong hộp, nên `$a`
thấy ngay.

Trường `sources` có từ PHP 7.4, khi có typed property. Nếu bạn lấy reference tới một property có kiểu,
engine ghi nhớ property đó trong hộp để mọi lần ghi qua reference vẫn bị kiểm tra kiểu:

```php
<?php
declare(strict_types=1);

final class Counter
{
    public int $value = 0;
}

$c = new Counter();
$r = &$c->value;       // reference tới một typed property
$r = 5;
echo $c->value, "\n";  // in ra: 5
try {
    $r = 'năm';
} catch (TypeError $e) {
    echo $e->getMessage(), "\n";
    // in ra: Cannot assign string to reference held by property Counter::$value of type int
}
```

Khi bạn `unset($r)`, refcount của hộp giảm về 1. `$a` vẫn là `IS_REFERENCE` trỏ tới hộp có refcount 1,
và engine coi nó như biến thường (`var_dump` chỉ in dấu `&` trước phần tử array khi hộp có refcount
lớn hơn 1).

### 4.3 Reference và copy-on-write sống chung thế nào

Chiếc hộp có refcount riêng, và giá trị bên trong hộp cũng có refcount riêng. Hai bộ đếm này độc lập,
và đây là điểm PHP 7 làm tốt hơn hẳn PHP 5:

```php
<?php
declare(strict_types=1);

// Output minh hoạ, tính cho máy 64-bit từ kích thước struct trong php-src (zval 16 byte, Bucket 32,
// zend_reference 32; khối lớn làm tròn theo trang 4 KiB). Chạy trên php-wasm 32-bit, số 16 in thành 16.1.

$mib = static fn (int $bytes): string => round($bytes / 1048576, 1) . ' MiB';

function total(array $items): int   // nhận theo giá trị
{
    return count($items);
}

function addOne(array &$items): void // nhận theo reference
{
    $items[] = 1;
}

$a = range(1, 1_000_000);
$r = &$a;                            // $a và $r là một reference

$m = memory_get_usage();
total($a);                           // truyền biến đang là reference vào hàm nhận by value
echo $mib(memory_get_usage() - $m), "\n";   // in ra: 0 MiB

$b = $a;                             // $b chia sẻ ARRAY nằm trong hộp
$m = memory_get_usage();
addOne($a);                          // ghi qua reference, nhưng array đang chia sẻ với $b
echo $mib(memory_get_usage() - $m), "\n";   // in ra: 16 MiB
echo count($a), ' ', count($r), ' ', count($b), "\n";   // in ra: 1000001 1000001 1000000
```

- Truyền `$a` (đang là reference) vào hàm nhận by value: tham số chỉ nhận một zval trỏ tới **array**
  bên trong hộp và tăng refcount của array. Không copy gì.
- `$b = $a`: `$b` không tham gia reference. Nó nhận một zval trỏ tới array bên trong hộp, array giờ có
  refcount 2.
- Ghi qua reference (`addOne($a)`): ghi qua hộp thì không cần tách hộp, vì cả `$a` và `$r` phải thấy
  thay đổi. Nhưng array bên trong có refcount 2 (hộp và `$b`), nên vẫn phải tách array như mọi lần ghi
  khác. `$b` giữ bản cũ.

```
sau $b = $a                                     sau addOne($a)

$a ──┐                                          $a ──┐
     ├──> hộp rc=2 ──> [1..1000000] rc=2             ├──> hộp rc=2 ──> [1..1000001] rc=1 (bản mới)
$r ──┘                       ^                  $r ──┘
$b ──────────────────────────┘                  $b ──────────────────> [1..1000000] rc=1
```

Ở PHP 5, cờ "là reference" nằm trên chính zval chứa giá trị, nên một giá trị không thể vừa thuộc một
reference vừa được chia sẻ với biến thường. Truyền một biến reference vào hàm by value (như `count($r)`)
buộc engine copy toàn bộ array. Rất nhiều lời khuyên cũ kiểu "đừng trộn reference với array lớn" bắt
nguồn từ hành vi đó; PHP 7 trở đi không còn.

### 4.4 Reference nằm trong array

Phần tử array cũng là zval, nên cũng có thể là `IS_REFERENCE`. Khi đó copy array (lúc tách) chỉ copy
zval của phần tử, tức copy con trỏ tới hộp và tăng refcount của hộp. Hai array khác nhau nhưng phần tử
đó **vẫn dùng chung một hộp**. Đây chính là cơ chế đằng sau bẫy "reference sống sót khi copy array" ở
[Chương 06](06-mang.md) mục 5.3:

```php
<?php
declare(strict_types=1);

$arr = [1, 2];
$ref = &$arr[0];       // phần tử 0 thành reference, hộp refcount 2
$copy = $arr;          // chia sẻ array
$copy[0] = 100;        // tách array ngoài; zval phần tử 0 được copy, tức copy con trỏ tới hộp
echo json_encode($arr), "\n";   // in ra: [100,2]   $arr bị sửa theo!

debug_zval_dump($arr);
// in ra:
// array(2) packed refcount(2){
//   [0]=>
//   reference refcount(3) {      hộp có 3 người dùng: $arr[0], $ref, $copy[0]
//     int(100)
//   }
//   [1]=>
//   int(2)
// }
```

Engine có một chi tiết làm bẫy này bớt nguy hiểm: khi tách array, phần tử nào là reference có refcount
bằng 1 (không còn tên nào khác dùng chung) sẽ được "gỡ hộp", bản copy nhận giá trị trơn. Vì thế
`unset($ref)` **trước khi** copy là đủ để các bản copy độc lập:

```php
<?php
declare(strict_types=1);

$arr = [1, 2];
$ref = &$arr[0];
unset($ref);           // hộp còn refcount 1
debug_zval_dump($arr); // in ra: ... [0]=> reference refcount(1) { int(1) } ...  (vẫn là hộp)
$copy = $arr;
$copy[0] = 100;        // khi tách, hộp refcount 1 được gỡ: $copy[0] là int thường
echo json_encode($arr), "\n";   // in ra: [1,2]
```

⚠️ Nhưng nếu bản copy đã được tạo **trong lúc** reference còn sống, thì `unset($ref)` sau đó không cứu
được: hộp vẫn còn ít nhất hai người dùng (phần tử của bản gốc và của bản copy), và hai array vẫn dính
nhau ở phần tử đó. Quy tắc an toàn vẫn là của chương 06: `unset` biến reference ngay sau khi dùng xong.

### 4.5 Vì sao `&` không làm code nhanh hơn

Lời khuyên "truyền array bằng `&` cho đỡ copy" là hiểu sai, và giờ bạn có đủ dữ kiện để thấy vì sao:

1. Truyền by value vốn đã không copy (mục 3.2). `&` không tiết kiệm được gì ở bước truyền.
2. Nếu array đang được chia sẻ với biến khác, ghi qua reference **vẫn phải tách** (mục 4.3).
3. Mỗi lần truy cập qua reference tốn thêm một bước đi vào hộp. Engine và optimizer cũng phải giả định
   giá trị có thể bị đổi qua một tên khác, nên bỏ qua một số tối ưu.
4. Tạo reference tốn bộ nhớ: mỗi hộp `zend_reference` là 32 byte (8 header + 16 zval + 8 `sources`).
   `foreach ($xs as &$x)` bọc **từng phần tử** vào một hộp, và các hộp ở lại sau vòng lặp:

```php
<?php
declare(strict_types=1);

// Output minh hoạ, tính cho máy 64-bit từ kích thước struct trong php-src (zval 16 byte, Bucket 32,
// zend_reference 32; khối lớn làm tròn theo trang 4 KiB).

$xs = range(1, 1_000_000);
$m = memory_get_usage();
foreach ($xs as &$x) {}           // không làm gì, chỉ duyệt by reference
unset($x);
echo round((memory_get_usage() - $m) / 1048576, 1), " MiB\n";   // in ra: 30.5 MiB
```

30,5 MiB đúng bằng một triệu hộp 32 byte. Vòng lặp "không làm gì" đã tăng gấp ba bộ nhớ của array
(16 MiB ban đầu).

Kết luận: dùng `&` khi bạn **thật sự muốn** hàm sửa biến của phía gọi (như `sort()` làm), hoặc khi cần
sửa tại chỗ một cấu trúc lồng sâu. Đừng dùng `&` như một mẹo tối ưu.

---

## 5. String bên trong: zend_string và interned string

### 5.1 Cấu trúc zend_string

Mọi string PHP là một `zend_string`:

```c
struct _zend_string {
    zend_refcounted_h gc;     /* 8 byte: refcount + cờ (interned, persistent...) */
    zend_ulong        h;      /* 8 byte: hash của nội dung, 0 nghĩa là chưa tính */
    size_t            len;    /* 8 byte: độ dài tính bằng byte */
    char              val[1]; /* nội dung bắt đầu ở đây, kéo dài len byte, cộng 1 byte '\0' */
};
```

```
zend_string của "hello" (một khối nhớ liền)
+-----------+-----------+-----------+---+---+---+---+---+----+
| gc (8)    | h (8)     | len=5 (8) | h | e | l | l | o | \0 |
+-----------+-----------+-----------+---+---+---+---+---+----+
 <-------- header 24 byte --------->  <---- len + 1 byte ---->
```

Những hệ quả bạn đã gặp ở [Chương 05](05-chuoi.md) giờ có lời giải thích:

- **Header và nội dung nằm trong cùng một khối cấp phát.** Mảng `val[1]` ở cuối struct là kỹ thuật
  "struct hack" của C: cấp phát `24 + len + 1` byte (làm tròn lên bội số của 8), phần sau header chính
  là nội dung. Một lần cấp phát cho cả string, không có con trỏ phụ.
- **`strlen()` là O(1)** vì độ dài được lưu sẵn trong `len`, không phải đếm tới `\0` như C.
- **String PHP là binary-safe**: chứa được byte `\0` ở giữa, vì engine dựa vào `len` chứ không dựa
  vào ký tự kết thúc. Byte `\0` cuối chỉ để tiện khi đưa string cho hàm C.
- **String là dãy byte**, không có khái niệm encoding: `len` đếm byte, không đếm ký tự. Đó là lý do
  `strlen('việt')` khác `mb_strlen('việt')`.
- **Hash được cache trong `h`.** Lần đầu string được dùng làm key array, engine tính hash (thuật toán
  DJBX33A, "times 33 with addition" của Daniel J. Bernstein) và ghi vào `h`. Các lần tra cứu sau với
  cùng string đó không phải tính lại. Engine luôn bật bit cao nhất của hash, nên hash thật không bao
  giờ bằng 0, và 0 dùng được để đánh dấu "chưa tính".

Chi phí: một string ngắn như `"hello"` tốn 24 + 5 + 1 = 30 byte, làm tròn thành 32 byte, cộng zval
16 byte trỏ tới nó. Một array 100.000 dòng mỗi dòng vài cột string, như kết quả một query, tốn nhiều
bộ nhớ hơn bạn tưởng chính vì những header này.

### 5.2 Nhiều biến, một string

Nhờ refcount nằm trong header, một `zend_string` có thể đồng thời là giá trị của nhiều biến, là phần
tử của array, là key của array, mà không phải copy. Ví dụ đưa một string vào làm key:
`$index[$name] = true;` chỉ cần ghi con trỏ tới `zend_string` của `$name` vào bucket và tăng refcount.
(Ở PHP 5, string không có header refcount riêng, nên key của array thường phải là một bản copy.)

### 5.3 Interned string

*Interned string* là string được lưu **đúng một bản** cho mỗi nội dung, trong một bảng tra cứu riêng,
và không đếm refcount (cờ `IS_STR_INTERNED`). Ai cần string có nội dung đó thì dùng chung bản duy nhất
này.

Những string được intern:

1. **Lúc compile**: literal string trong code (`'status'`, `"SELECT ..."`), tên biến, tên hàm, tên
   class, tên property, tên hằng. Compiler tra bảng interned: có sẵn nội dung đó thì dùng lại, chưa có
   thì thêm vào.
2. **String rỗng và mọi string một byte** (256 giá trị có thể có): engine tạo sẵn lúc khởi động. Vì vậy
   `$s[0]` hay `(string) 7` không bao giờ cấp phát.
3. **Tên có sẵn của PHP** (hàm, class, hằng của engine và extension): intern lúc khởi động process.

Còn string tạo **lúc chạy** (nối chuỗi, `implode()`, đọc file, kết quả query, `json_decode()`...) là
string thường, refcounted.

```php
<?php
declare(strict_types=1);

$a = 'status';                    // literal: interned lúc compile
$b = 'sta' . 'tus';               // hai literal nối nhau: compiler tính sẵn thành 'status'
$c = implode('', ['sta', 'tus']); // tạo lúc chạy
$d = $c[0];                       // string một byte
$e = (string) 7;
debug_zval_dump($a, $b, $c, $d, $e);
var_dump($a === $c);

// in ra (CLI, OPcache tắt):
// string(6) "status" interned
// string(6) "status" interned
// string(6) "status" refcount(2)
// string(1) "s" interned
// string(1) "7" interned
// bool(true)
```

`$a` và `$c` có cùng nội dung và `===` trả `true`, nhưng bên trong là hai `zend_string` khác nhau: một
interned, một thường. Nếu chạy cùng file khi bật OPcache, `$c` cũng hiện `interned`: optimizer của
OPcache tính sẵn lúc compile một số hàm khi mọi tham số là hằng (các hàm được đánh dấu an toàn để làm
vậy, `implode()` là một trong số đó), nên `$c` thực chất thành một literal.

Interned string mang lại ba lợi ích:

- **Tiết kiệm bộ nhớ**: key `'status'` xuất hiện trong mười nghìn array literal thì vẫn chỉ có một
  string.
- **So sánh nhanh**: hàm so sánh string của engine thử so **con trỏ** trước. Hai interned string cùng
  nội dung luôn là cùng một con trỏ, nên tra key interned trong array thường khớp ngay mà không phải
  so từng byte.
- **Không tốn công đếm**: không tăng giảm refcount mỗi lần gán, không bao giờ phải giải phóng giữa
  chừng.

Interned string sống bao lâu:

| Loại | Sống tới khi nào |
|---|---|
| Tạo lúc khởi động process (tên có sẵn, string một byte) | Process tắt (*permanent*) |
| Tạo lúc compile, **không có OPcache** | Hết request: bảng interned của request bị huỷ cùng mọi thứ khác |
| Tạo lúc compile, **có OPcache** | Nằm trong shared memory của OPcache, dùng chung mọi worker FPM, tới khi OPcache bị reset |

### 5.4 Interned string và OPcache

Khi OPcache lưu một script đã compile vào shared memory, mọi string của script (literal, tên, key của
array literal) được chuyển vào một vùng riêng gọi là *interned strings buffer*. Kích thước vùng này do
`opcache.interned_strings_buffer` quy định, đơn vị megabyte, mặc định 8. Từ PHP 8.4, giá trị tối đa
trên máy 64-bit là 32767 (trước đó 4095).

Vùng này đầy thì OPcache ghi cảnh báo "Interned string buffer overflow" vào log, và string mới không
được đưa vào shared memory nữa: mỗi worker phải giữ bản riêng, mất một phần lợi ích. Ứng dụng
framework có nhiều package có thể cần nhiều hơn 8 MB, nên đừng đoán: kiểm tra bằng
`opcache_get_status()`:

```php
<?php
declare(strict_types=1);

$status = opcache_get_status(false);
if ($status !== false) {
    print_r($status['interned_strings_usage']);
}

// output minh hoạ (bật OPcache, một script nhỏ):
// Array
// (
//     [buffer_size] => 8388608
//     [used_memory] => 2459096
//     [free_memory] => 5929512
//     [number_of_strings] => 8402
// )
```

`used_memory` không bằng 0 dù script rất nhỏ vì tên hàm, class có sẵn của PHP cũng được đưa vào vùng
này. Cách chọn giá trị cho production nằm ở [Chương 18](18-fpm-nginx-opcache.md).

---

## 6. Array bên trong: HashTable

### 6.1 Một cấu trúc cho mọi vai trò

Array của PHP đóng vai list, map, set, stack, queue ([Chương 06](06-mang.md)). Để làm được vậy,
cấu trúc bên dưới phải đáp ứng cùng lúc:

1. Key là `int` hoặc `string`, tra theo key nhanh (trung bình O(1)).
2. Nhớ **thứ tự chèn**: `foreach` trả phần tử theo đúng thứ tự đã thêm, kể cả với key string.
3. Duyệt tuần tự nhanh.
4. Với list thuần (key 0, 1, 2...), càng gọn càng tốt.

Cài đặt trong engine là `zend_array`, còn có tên khác là `HashTable` (hai tên cho cùng một struct).
Nó có hai "dạng": *hash array* dạng tổng quát, và *packed array* dạng tối ưu cho list.

### 6.2 Struct zend_array

```c
struct _zend_array {
    zend_refcounted_h gc;        /* refcount, cờ immutable... */
    union { uint32_t flags; } u; /* có cờ HASH_FLAG_PACKED, HASH_FLAG_UNINITIALIZED... */
    uint32_t  nTableMask;        /* dùng để tính ô hash (mục 6.3) */
    union {
        uint32_t *arHash;        /* phần hash nằm NGAY TRƯỚC vùng dữ liệu */
        Bucket   *arData;        /* hash array: mảng Bucket */
        zval     *arPacked;      /* packed array (PHP 8.2+): mảng zval trơn */
    };
    uint32_t  nNumUsed;          /* số ô đã dùng trong vùng dữ liệu, tính cả ô đã bị unset */
    uint32_t  nNumOfElements;    /* số phần tử thật: count() trả số này */
    uint32_t  nTableSize;        /* dung lượng: luỹ thừa của 2, tối thiểu 8 */
    uint32_t  nInternalPointer;  /* con trỏ nội bộ cho current(), next()... */
    zend_long nNextFreeElement;  /* key int tiếp theo cho $a[] = ... */
    dtor_func_t pDestructor;     /* hàm huỷ phần tử */
};                               /* 56 byte trên máy 64-bit */

typedef struct _Bucket {
    zval         val;            /* 16 byte: giá trị, zval nhúng thẳng */
    zend_ulong   h;              /* 8 byte: hash của key string, hoặc chính key int */
    zend_string *key;            /* 8 byte: con trỏ tới key string, NULL nếu key là int */
} Bucket;                        /* 32 byte */
```

Header 56 byte là chi phí cố định của mọi array. Phần lớn bộ nhớ nằm ở vùng dữ liệu mà `arData` trỏ
tới, được cấp phát thành **một khối liền**: phần hash ở đầu, mảng Bucket ngay sau.

### 6.3 Hash array: tra key thế nào

```
            phần hash: 2 x nTableSize ô uint32           vùng dữ liệu: Bucket theo THỨ TỰ CHÈN
            (đánh chỉ số âm, nằm trước arData)            arData
            +----+----+----+----+----+-- ... --+          +--------------------------------------+
  ô hash -> | -1 |  2 | -1 |  0 | -1 |   ...   |     [0]  | key="id"    h=...  val=int(7)        |
            +----+-|--+----+-|--+----+-- ... --+     [1]  | key="name"  h=...  val=string        |
                   |         |                       [2]  | key="email" h=...  val=string  next=1 |
                   |         +-------------------->  [0]  +--------------------------------------+
                   +------------------------------>  [2] ──(val.u2.next)──> [1]   chuỗi va chạm
            -1 = ô trống (HT_INVALID_IDX)
```

Tra `$user['name']`:

1. Lấy hash của key `'name'`: đã cache sẵn trong `zend_string->h` (mục 5.1), chưa có thì tính.
2. Tính ô hash: `h | nTableMask`. `nTableMask` là số âm `-(2 × nTableSize)`, nên phép OR này giữ lại
   vài bit thấp của hash và cho ra một chỉ số âm trong phần hash. Đây là cách tính "hash modulo kích
   thước" bằng một phép OR, không cần phép chia.
3. Ô hash chứa chỉ số của bucket **đầu tiên** trong chuỗi va chạm của ô đó (hoặc -1 nếu trống).
4. So bucket đó: nếu con trỏ key trùng con trỏ key cần tìm (hai interned string giống nhau, mục 5.3),
   khớp ngay. Nếu không, so `h` rồi so nội dung key.
5. Không khớp thì theo `val.u2.next` (4 byte "thừa" của zval, mục 2.2) sang bucket kế trong chuỗi, lặp
   tới khi hết chuỗi.

Thêm một phần tử key mới: bucket mới luôn được đặt ở ô kế tiếp của vùng dữ liệu (`arData[nNumUsed]`,
rồi `nNumUsed` tăng 1), sau đó được gắn vào **đầu** chuỗi va chạm của ô hash tương ứng.

Phần hash có số ô gấp đôi số bucket (từ PHP 7.3; trước đó bằng nhau), giúp giảm va chạm. Key
int dùng chính giá trị key làm `h`, không cần tính hash.

### 6.4 Thứ tự chèn, foreach và ô bị unset

Thứ tự chèn có được "miễn phí": bucket được thêm tuần tự vào `arData`, nên vị trí trong mảng chính là
thứ tự chèn. `foreach` chỉ việc đi dọc `arData` từ 0 tới `nNumUsed`. Đó là một lượt quét bộ nhớ liền
nhau, rất hợp với cache của CPU.

`unset($a['name'])` không dời các bucket phía sau (dời thì tốn O(n)). Engine gỡ bucket khỏi chuỗi va
chạm, đánh dấu zval của nó là `IS_UNDEF` (một "bia mộ", *tombstone*), và giảm `nNumOfElements`.
`nNumUsed` giữ nguyên (trừ khi bucket bị xoá nằm ở cuối), `foreach` nhảy qua các ô `IS_UNDEF`.

Khi vùng dữ liệu đầy (`nNumUsed` chạm `nTableSize`) và cần thêm phần tử, engine chọn một trong hai:

- Nếu số ô bia mộ đủ nhiều (cụ thể: `nNumUsed > nNumOfElements + nNumOfElements / 32`), nó **dồn**
  các bucket còn sống lên đầu, không tăng dung lượng.
- Nếu không, nó **nhân đôi** `nTableSize`, cấp phát vùng mới, copy bucket sang, rồi tính lại phần
  hash.

⚠️ Dung lượng của array không bao giờ tự giảm. Array một triệu phần tử bị `unset` dần còn mười phần
tử vẫn giữ nguyên vùng nhớ cũ:

```php
<?php
declare(strict_types=1);

// Output minh hoạ, tính cho máy 64-bit từ kích thước struct trong php-src (zval 16 byte, Bucket 32,
// zend_reference 32; khối lớn làm tròn theo trang 4 KiB). Chạy trên php-wasm 32-bit, số 16 in thành 16.1.

$mib = static fn (int $bytes): string => round($bytes / 1048576, 1) . ' MiB';

$base = memory_get_usage();
$a = range(1, 1_000_000);
echo $mib(memory_get_usage() - $base), "\n";   // in ra: 16 MiB

for ($i = 0; $i < 999_990; $i++) {
    unset($a[$i]);
}
echo count($a), ' phần tử, ', $mib(memory_get_usage() - $base), "\n";   // in ra: 10 phần tử, 16 MiB

$a = array_values($a);                         // tạo array mới vừa khít, array cũ bị giải phóng
echo $mib(memory_get_usage() - $base), "\n";   // in ra: 0 MiB
```

Trong script web ngắn, chuyện này không đáng lo. Trong một worker sống lâu dùng array làm hàng đợi
hay cache, nó giải thích vì sao bộ nhớ không giảm dù số phần tử đã giảm.

### 6.5 Packed array: dạng tối ưu cho list

Khi mọi key là int và được thêm theo thứ tự **tăng dần**, key chính là vị trí trong vùng dữ liệu. Không
cần phần hash, không cần lưu key. Đó là *packed array*:

- Tra `$a[5]` là tính thẳng địa chỉ ô thứ 5, không hash, không chuỗi va chạm.
- Từ PHP 8.2, packed array bỏ luôn `Bucket` và lưu thẳng một mảng zval (`arPacked`), vì `h` luôn bằng
  vị trí và `key` luôn là NULL: mỗi phần tử còn 16 byte thay vì 32.

```
packed array range(10, 13), PHP 8.2+

arPacked                                            không có phần hash (chỉ 2 ô -1 cố định)
+-------------+-------------+-------------+-------------+-------- ... ---------+
| int(10)     | int(11)     | int(12)     | int(13)     | (trống tới nTableSize)|
+-------------+-------------+-------------+-------------+-------- ... ---------+
  [0] 16 byte   [1]           [2]           [3]
```

"Tăng dần" không có nghĩa là liền nhau. Packed array chấp nhận lỗ hổng (ô `IS_UNDEF`) nếu chúng không
quá thưa. Quy tắc cụ thể nằm trong `zend_hash.c`; kết quả thực nghiệm dưới đây cho cảm giác:

```php
<?php
declare(strict_types=1);

function kind(array $a): string
{
    ob_start();
    debug_zval_dump($a);
    $first = strtok((string) ob_get_clean(), "\n");
    return str_contains($first, 'packed') ? 'packed' : 'hash';
}

$list = [];
for ($i = 0; $i < 5; $i++) { $list[] = $i; }
echo kind($list), "\n";      // in ra: packed   thêm bằng $a[] = ...

$a = [];
$a[5] = 'x';
echo kind($a), "\n";         // in ra: packed   key đầu tiên nhỏ (< 8): vẫn packed, có lỗ 0..4

$b = [];
$b[100] = 'x';
echo kind($b), "\n";         // in ra: hash     key đầu tiên quá xa

$c = range(0, 9);
$c[1000] = 1;
echo kind($c), "\n";         // in ra: hash     nhảy cóc quá xa

$d = range(0, 9);
unset($d[3]);
echo kind($d), "\n";         // in ra: packed   unset chỉ để lại lỗ
$d[3] = 'lại';
echo kind($d), "\n";         // in ra: hash     lấp lại lỗ thì thứ tự chèn không còn khớp vị trí

$rev = [];
$rev[2] = 'c';
$rev[1] = 'b';
echo kind($rev), "\n";       // in ra: hash     key giảm dần

$f = range(0, 9);
$f['x'] = 1;
echo kind($f), "\n";         // in ra: hash     có key string
unset($f['x']);
echo kind($f), "\n";         // in ra: hash     không tự quay về packed
echo kind(array_values($f)), "\n";   // in ra: packed   array_values() tạo list mới
echo kind(json_decode('[1,2,3]', true)), "\n";   // in ra: packed
```

Hai trường hợp đáng chú ý:

- `$d[3] = 'lại'` sau khi unset: vị trí 3 nằm giữa array, nhưng về thứ tự chèn thì phần tử này là mới
  nhất, phải đứng **sau** phần tử 9 khi `foreach`. Packed array không biểu diễn được điều đó (vị trí
  chính là thứ tự), nên engine chuyển sang hash. Tương tự cho key giảm dần.
- Chuyển từ packed sang hash là một chiều. Muốn quay lại packed, tạo array mới bằng `array_values()`.

### 6.6 Mỗi phần tử tốn bao nhiêu bộ nhớ

Tính trên máy 64-bit, chưa kể dữ liệu mà zval trỏ tới (string, array con, object):

| Dạng | Byte mỗi phần tử | Từ đâu ra |
|---|---|---|
| Packed, PHP 8.2+ | 16 | Một zval |
| Packed, PHP 7.0 tới 8.1 | 32 | Một Bucket (dù `h` và `key` vô dụng) |
| Hash, PHP 7.3+ | 40 | Bucket 32 + 2 ô hash × 4 byte |
| Hash, PHP 7.0 tới 7.2 | 36 | Bucket 32 + 1 ô hash × 4 byte |
| PHP 5.x | khoảng 144 | Theo bài phân tích của Nikita Popov (link ở Đọc thêm) |

Dung lượng luôn là luỹ thừa của 2, nên một triệu phần tử chiếm 2^20 = 1.048.576 ô: packed là
2^20 × 16 byte = 16 MiB, hash là 2^20 × 40 byte = 40 MiB. Khớp với các con số đo ở
[Chương 06](06-mang.md) mục 10.3. Với key string, còn phải cộng thêm chính các string key:

```php
<?php
declare(strict_types=1);

// Output minh hoạ, tính cho máy 64-bit từ kích thước struct trong php-src (zval 16 byte, Bucket 32,
// zend_reference 32; khối lớn làm tròn theo trang 4 KiB).

$base = memory_get_usage();
$h = [];
for ($i = 0; $i < 1_000_000; $i++) {
    $h['k' . $i] = $i;
}
echo round((memory_get_usage() - $base) / 1048576, 1), " MiB\n";   // in ra: 70.5 MiB
```

40 MiB cho phần hash array, cộng khoảng một triệu `zend_string` 32 byte (24 header + tối đa 7 ký tự +
1 byte `\0`, làm tròn lên 32) là 30,5 MiB.

Vì sao PHP 7 tiết kiệm bộ nhớ hơn PHP 5 nhiều như vậy? Nikita Popov, trong bài phân tích HashTable mới
của PHP 7, đo `range(1, 100000)` trên máy 64-bit: 13,97 MiB ở PHP 5.6 và 4,00 MiB ở PHP 7.0. Các nguồn
tiết kiệm chính:

1. Zval không còn cấp phát riêng từng cái (mỗi lần cấp phát lại tốn thêm header của bộ cấp phát), mà
   nhúng thẳng vào bucket.
2. Bucket cũng không cấp phát riêng: cả mảng bucket là một khối liền.
3. PHP 5 giữ thứ tự chèn và chuỗi va chạm bằng hai danh sách liên kết đôi, tốn bốn con trỏ mỗi phần tử.
   PHP 7 giữ thứ tự bằng vị trí trong mảng (không tốn gì), và chuỗi va chạm là danh sách liên kết
   đơn bằng chỉ số 32-bit cất trong `u2` sẵn có của zval.
4. Int, float, bool không còn refcount và thông tin GC đi kèm.

Từ PHP 8.2, packed array giảm thêm một nửa, nên cùng `range(1, 100000)` chỉ còn khoảng 2 MiB
(2^17 ô × 16 byte).

### 6.7 Hệ quả thực tế

- **List thật sự rẻ hơn map.** Dữ liệu dạng danh sách nên được xây bằng `$a[] = ...`; tránh key int lộn
  xộn nếu không cần.
- **`array_values()` sau `array_filter()`** nếu bạn cần một list thật: ngoài việc cho key liền nhau
  (quan trọng khi `json_encode` ra JSON array), nó còn tạo array mới có dung lượng vừa với số phần
  tử.
- **`unset` không thu nhỏ array.** Cần thu nhỏ thì tạo array mới.
- **`array_shift()` là O(n)**: nó phải đánh số lại toàn bộ key int còn lại. Hàng đợi lớn nên dùng
  `SplQueue` hoặc giữ chỉ số đầu hàng ([Chương 06](06-mang.md) mục 4.3).
- **Object có property khai báo gọn hơn array kết hợp** cùng số trường, vì không cần Bucket và hash
  (mục 7.4).

---

## 7. Object bên trong: object store và handle

### 7.1 Struct zend_object

```c
struct _zend_object {
    zend_refcounted_h gc;                 /* 8 byte: refcount, cờ (đã gọi destructor chưa...) */
    uint32_t          handle;             /* số thứ tự trong object store */
    uint32_t          extra_flags;
    zend_class_entry *ce;                 /* con trỏ tới class của object */
    const zend_object_handlers *handlers; /* bảng hàm xử lý các thao tác trên object */
    HashTable        *properties;         /* bảng property dạng hash: NULL cho tới khi cần */
    zval              properties_table[1];/* property đã khai báo nằm liền ở đây, mỗi cái 16 byte */
};
```

Phần cố định là 40 byte trên máy 64-bit, theo sau là một zval 16 byte cho **mỗi property đã khai báo**
trong class (kể cả property kế thừa từ class cha). Object của class có 5 property là một khối
40 + 5 × 16 = 120 byte, cấp phát một lần.

### 7.2 Object store: bảng mọi object đang sống

Mỗi request có một *object store*: một mảng con trỏ tới mọi object đang sống, nằm trong biến toàn cục
của engine (`EG(objects_store)`).

```
object store (một mảng, mỗi ô 8 byte)
+-------+--------+--------+--------+--------+-----
|  [0]  |  [1]   |  [2]   |  [3]   |  [4]   | ...
| không |   ─────┼──> zend_object (Cart)    |
| dùng  |        |  ô trống: thuộc "danh sách ô trống", chờ object mới
+-------+--------+--------+--------+--------+-----
                     |        └──> zend_object (User)
                     └──> ...
```

- Khi `new` một object, engine cấp phát `zend_object`, rồi đặt con trỏ tới nó vào một ô của object
  store. Chỉ số của ô đó chính là *handle* của object, ghi vào trường `handle`. Ô số 0 không dùng, nên
  handle bắt đầu từ 1.
- Đây chính là số `#1`, `#2` mà `var_dump()` in ra và `spl_object_id()` trả về
  ([Chương 09](09-oop-co-ban.md) mục 12).
- Khi object bị giải phóng, ô của nó được trả vào *danh sách ô trống*. Object tạo sau đó **dùng lại**
  ô trống gần nhất, nên handle được tái sử dụng:

```php
<?php
declare(strict_types=1);

$a = new stdClass();
$b = new stdClass();
echo spl_object_id($a), ' ', spl_object_id($b), "\n";   // in ra: 1 2
unset($a);                      // object #1 bị giải phóng, ô 1 thành ô trống
$c = new stdClass();
echo spl_object_id($c), "\n";   // in ra: 1   dùng lại ô trống
$d = new stdClass();
echo spl_object_id($d), "\n";   // in ra: 3
```

⚠️ Hệ quả: `spl_object_id()` chỉ duy nhất **trong số các object đang sống cùng lúc**. Dùng nó làm key
cho một cache sống lâu hơn object là sai: object cũ chết, object mới nhận lại đúng id đó và đọc nhầm
dữ liệu của object cũ. Muốn gắn dữ liệu vào object mà không giữ object sống, dùng `WeakMap`
([Chương 10](10-oop-nang-cao.md) mục 12).

Object store còn có một việc quan trọng lúc kết thúc request: engine duyệt nó để gọi destructor cho
những object còn sống, rồi giải phóng chúng (mục 7.5).

### 7.3 Vì sao object là handle

Zval của một biến object (type `IS_OBJECT`) chứa con trỏ tới `zend_object`. Gán `$b = $a` là copy zval
đó và tăng refcount của object, đúng như với array. Khác biệt duy nhất nằm ở bước ghi: không có
separation (mục 3.5). Vì vậy hai biến cùng trỏ một object, sửa qua biến nào cũng là sửa object đó.

Tên gọi "handle" và câu "object được truyền theo handle" đến từ PHP 5, khi zval của object chứa số
handle (kèm bảng handler) chứ không chứa con trỏ tới object, và engine phải tra object store để tìm
object. Từ PHP 7, zval chứa thẳng con trỏ (bớt một bước tra), còn số handle vẫn được giữ trong
`zend_object` để in ra, làm id, và để object store quản lý. Về ngữ nghĩa thì không có gì đổi: biến giữ một "tay nắm" tới object chứ không giữ chính
object.

```
$a = new Cart();  $b = $a;

zval $a ──┐
          ├──> zend_object  refcount=2, handle=1, ce=Cart
zval $b ──┘        properties_table: [ items: zval ──> array ]
                         ^
object store [1] ────────┘   (store giữ con trỏ, KHÔNG tính vào refcount)
```

Object store không tăng refcount: nó chỉ là sổ ghi chép. Object được giải phóng khi refcount từ các
zval về 0, giống mọi giá trị khác.

### 7.4 Property khai báo nằm trong slot, không nằm trong hash

Property khai báo trong class (kể cả property promoted trong constructor) được compiler gán một vị trí
cố định, gọi là *slot*, trong `properties_table`. Truy cập `$obj->x` không cần tra bảng hash theo tên:
opcode biết (và cache lại sau lần chạy đầu) rằng `x` nằm ở slot số mấy, rồi đọc thẳng ô đó.

Bảng `properties` dạng hash (con trỏ `properties` trong struct) chỉ được tạo khi cần:

- Khi thêm *dynamic property* (property không khai báo, deprecated từ PHP 8.2,
  [Chương 09](09-oop-co-ban.md) mục 2.5).
- Khi một thao tác cần nhìn object như một bảng tên-giá trị, ví dụ `foreach` trên object,
  `get_object_vars()`, `var_dump()`. Bảng tạo ra trỏ vào các slot sẵn có chứ không copy giá trị, và
  ở lại với object từ đó.

Hệ quả bộ nhớ: object có property khai báo gọn hơn array kết hợp có cùng số trường. Tính trên máy
64-bit cho 5 trường int:

| Cách lưu | Gồm | Byte (đã làm tròn theo bộ cấp phát) |
|---|---|---|
| Object `Point` 5 property | 40 + 5 × 16 = 120 | 128 |
| Array `['id' => .., 'x' => .., ...]` | Header 56 + vùng dữ liệu 8 bucket × 32 + 16 ô hash × 4 = 320 | 56 + 320 = 376 |

Array kết hợp tốn gần gấp ba, chưa kể object còn được kiểm tra kiểu từng property. Đây là một lý do
(ngoài lý do thiết kế) để dùng DTO hay value object thay cho array kết hợp khi xử lý lượng lớn bản
ghi. Bạn có thể tự đo:

```php
<?php
declare(strict_types=1);

final class Point
{
    public function __construct(
        public int $id,
        public int $x,
        public int $y,
        public int $z,
        public int $w,
    ) {}
}

$n = 100_000;
$base = memory_get_usage();
$objs = [];
for ($i = 0; $i < $n; $i++) {
    $objs[] = new Point($i, $i, $i, $i, $i);
}
$perObj = (memory_get_usage() - $base) / $n;
unset($objs);

$base = memory_get_usage();
$arrs = [];
for ($i = 0; $i < $n; $i++) {
    $arrs[] = ['id' => $i, 'x' => $i, 'y' => $i, 'z' => $i, 'w' => $i];
}
$perArr = (memory_get_usage() - $base) / $n;
printf("object: %.0f byte, array: %.0f byte\n", $perObj, $perArr);
// Không ghi output: con số phụ thuộc kiến trúc máy. Mỗi con số gồm cả phần của array
// $objs/$arrs bên ngoài (khoảng 21 byte mỗi phần tử) và ô trong object store (với object).
// Theo tính toán từ kích thước struct, trên máy 64-bit array kết hợp tốn khoảng 2,5 lần object.
```

### 7.5 Object handler và vòng đời object

Trường `handlers` trỏ tới một bảng con trỏ hàm C (`zend_object_handlers`): đọc property, ghi property,
gọi method, so sánh, clone, ép kiểu, đếm phần tử, liệt kê property cho GC, giải phóng... Object của
class viết bằng PHP dùng bảng mặc định (`std_object_handlers`). Class có sẵn viết bằng C thay một số
mục trong bảng để có hành vi đặc biệt: đó là cách `ArrayObject` cho dùng cú pháp `[]`, `Closure` gọi
được như hàm, hay `DateTime` so sánh được bằng `<` và `>`.

Vòng đời một object:

1. `new`: cấp phát `zend_object`, khởi tạo các slot property bằng giá trị mặc định, đăng ký vào object
   store, gọi constructor.
2. Sống: refcount tăng giảm theo số zval trỏ tới nó.
3. Refcount về 0: engine gọi `__destruct()` (nếu có), rồi giải phóng property (giảm refcount từng giá
   trị con), rồi giải phóng khối nhớ và trả ô object store vào danh sách ô trống.
4. Nếu object vẫn còn sống khi request kết thúc: engine dọn các biến toàn cục (biến nào là chỗ giữ duy
   nhất của một object thì object đó được huỷ luôn), rồi duyệt object store gọi destructor cho mọi
   object còn lại, rồi giải phóng tất cả. Đừng viết code dựa vào thứ tự gọi
   destructor ở giai đoạn này ([Chương 09](09-oop-co-ban.md) mục 4.4).

Bước 3 cần refcount về 0. Nếu object nằm trong một vòng tham chiếu, bước 3 không tự xảy ra: đó là chủ
đề của mục tiếp theo.

---

## 8. Garbage collection: refcount và cycle collector

### 8.1 Hai cơ chế, hai việc

*Garbage collection* (GC, thu gom rác) là việc tự động giải phóng bộ nhớ của những giá trị không còn
ai dùng, để lập trình viên không phải tự `free` như trong C. PHP dùng hai cơ chế bổ sung cho nhau:

1. **Reference counting** (mục 3.1): làm phần lớn công việc. Refcount về 0 là giải phóng ngay.
2. **Cycle collector** (bộ thu gom vòng): chỉ để xử lý một trường hợp refcount không tự giải quyết
   được, là *vòng tham chiếu*.

Khi nói "GC của PHP" người ta thường nói tới cái thứ hai, vì nó là thứ có ini, có hàm điều khiển, có
số liệu thống kê.

### 8.2 Vòng tham chiếu: chỗ refcount bó tay

*Vòng tham chiếu* (*reference cycle*) là một nhóm giá trị trỏ vòng vào nhau. Mỗi phần tử trong vòng
luôn có refcount ít nhất 1 (vì phần tử khác trong vòng trỏ tới nó), kể cả khi chương trình không còn
đường nào để với tới cả nhóm:

```php
<?php
declare(strict_types=1);

final class Conn
{
    public ?Conn $peer = null;

    public function __construct(private string $name)
    {
    }

    public function __destruct()
    {
        echo "đóng {$this->name}\n";
    }
}

$x = new Conn('X');
unset($x);                       // không có vòng: refcount về 0, destructor chạy ngay
echo "sau unset(\$x)\n";

$a = new Conn('A');
$b = new Conn('B');
$a->peer = $b;
$b->peer = $a;                   // vòng A <-> B
unset($a, $b);                   // mỗi object còn refcount 1: KHÔNG được giải phóng
echo "sau unset(\$a, \$b)\n";
$n = gc_collect_cycles();       // chạy cycle collector ngay
echo "dọn được $n giá trị\n";
echo "hết script\n";

// in ra:
// đóng X
// sau unset($x)
// sau unset($a, $b)
// đóng A
// đóng B
// dọn được 2 giá trị
// hết script
```

```
trước unset:                              sau unset:

$a ──> [A rc=2] ──peer──┐                 [A rc=1] ──peer──┐
          ^             v                    ^             v
          └──peer── [B rc=2] <── $b          └──peer── [B rc=1]

                                          không biến nào trỏ vào, nhưng refcount không về 0
```

Nếu không gọi `gc_collect_cycles()`, A và B nằm đó cho tới khi cycle collector tự chạy (mục 8.4) hoặc
tới cuối request. ⚠️ Nghĩa là destructor của object nằm trong vòng **không chạy lúc bạn nghĩ**. Nếu
destructor đóng kết nối hay nhả khoá, hành vi sẽ khác hẳn mong đợi; hãy đóng tài nguyên quan trọng
tường minh ([Chương 09](09-oop-co-ban.md) mục 4.4).

Vòng hay gặp trong code thật:

- Cây có con trỏ ngược: node con giữ `$parent`, node cha giữ mảng `$children`.
- Quan hệ hai chiều giữa object: model cha giữ danh sách model con, mỗi model con giữ lại model cha.
- Closure tạo trong method tự bắt `$this`, rồi được gán vào property của chính object đó:
  `$this->handler = function () { ... };` (object giữ closure, closure giữ object).
- Array chứa reference tới chính nó: `$x = []; $x[] = &$x;`.

Chỉ array và object mới tạo được vòng (string, int, resource không chứa được giá trị khác), nên cycle
collector chỉ quan tâm tới hai loại này.

### 8.3 Thuật toán: thử trừ các cạnh nội bộ

Cycle collector của PHP (có từ PHP 5.3) dựa trên thuật toán đồng bộ trong bài báo "Concurrent Cycle
Collection in Reference Counted Systems" của David F. Bacon và V.T. Rajan. Nó dựa trên hai quan sát:

1. Refcount **tăng** thì giá trị đang được dùng, không thể thành rác. Refcount **về 0** thì đã được giải
   phóng xong. Vậy rác dạng vòng chỉ có thể sinh ra ở thời điểm refcount **giảm nhưng chưa về 0**.
2. Trong một vòng rác, nếu trừ đi các tham chiếu *nội bộ* (từ phần tử này sang phần tử khác trong
   nhóm), refcount của mọi phần tử về 0. Phần tử nào vẫn còn lớn hơn 0 sau khi trừ là đang được ai đó
   **bên ngoài** nhóm giữ, nên còn sống, và mọi thứ nó trỏ tới cũng còn sống.

Từ đó, cơ chế gồm các bước:

**Bước A, ghi nhận nghi phạm.** Mỗi khi refcount của một array hoặc object giảm mà chưa về 0, engine
ghi giá trị đó vào *root buffer* (bộ đệm gốc) và tô màu *tím* (purple: "có thể là gốc của một vòng").
Mỗi giá trị chỉ vào buffer một lần (vị trí trong buffer và màu được ghi vào phần GC của header, mục
2.5).
Nếu sau đó giá trị bị giải phóng bình thường, nó được gỡ khỏi buffer.

**Bước B, thử trừ (mark grey).** Khi buffer chạm ngưỡng, thuật toán duyệt theo chiều sâu từ từng
root. Với mỗi giá trị gặp được, nó trừ 1 refcount cho mỗi cạnh trỏ tới giá trị đó từ trong nhóm đang
duyệt, và tô *xám* để không xử lý hai lần.

**Bước C, phân loại (scan).** Duyệt lại từ từng root:
- Giá trị có refcount (sau khi trừ) bằng 0: chỉ được giữ sống bởi các cạnh nội bộ. Tô *trắng*: rác.
- Giá trị có refcount lớn hơn 0: có chỗ bên ngoài đang giữ. Tô *đen* và **cộng trả lại** refcount cho
  nó và mọi thứ nó với tới, vì những thứ đó cũng còn sống.

**Bước D, dọn (collect white).** Giải phóng mọi giá trị trắng. Nếu trong đám rác có object có
`__destruct()`, engine gọi các destructor trước, rồi chạy lại thuật toán thêm một lượt trước khi giải
phóng chúng: destructor có thể "hồi sinh" object (ví dụ gán `$this` vào một biến toàn cục), và object
được hồi sinh thì không được giải phóng.

```
Màu trong mã nguồn zend_gc.c:
  PURPLE  nghi phạm, đang nằm trong root buffer
  GREY    đã thử trừ refcount
  WHITE   rác, sẽ bị giải phóng
  BLACK   còn sống (màu mặc định)
```

Áp vào ví dụ A, B ở mục 8.2: `unset($a, $b)` làm refcount của A và B giảm từ 2 xuống 1, cả hai vào root
buffer. Bước B trừ cạnh A→B và B→A: cả hai về 0. Bước C thấy 0, tô trắng. Bước D gọi hai destructor và
giải phóng cả hai. Hàm trả về 2.

Giả sử thay vì `unset($b)`, biến `$b` vẫn còn. Khi đó ở bước B, B về 1 (vẫn còn `$b` trỏ vào), bước C
tô B đen và cộng trả refcount cho A (vì B trỏ tới A): không có gì bị dọn. Đúng như mong đợi.

### 8.4 Khi nào cycle collector chạy

Collector không chạy theo thời gian mà theo **số root trong buffer**. Hằng số trong `Zend/zend_gc.c`
(viết lại từ PHP 7.3, vẫn dùng ở 8.5):

| Hằng số | Giá trị | Ý nghĩa |
|---|---|---|
| `GC_THRESHOLD_DEFAULT` | 10.000 (+1 ô dành riêng) | Ngưỡng ban đầu: đủ chừng này root thì collector tự chạy |
| `GC_THRESHOLD_TRIGGER` | 100 | Một lần chạy dọn được ít hơn 100 giá trị bị coi là "chạy phí công" |
| `GC_THRESHOLD_STEP` | 10.000 | Mỗi lần chạy phí công, ngưỡng tăng thêm chừng này; chạy hiệu quả thì giảm dần về mặc định |
| `GC_THRESHOLD_MAX` | 1.000.000.000 | Trần của ngưỡng |
| `GC_DEFAULT_BUF_SIZE` | 16.384 | Kích thước root buffer ban đầu; buffer tự nới khi cần |

Ngưỡng tự điều chỉnh để tránh ca xấu nhất: ứng dụng giữ hàng trăm nghìn object **còn sống thật** (ví dụ
ORM nạp rất nhiều entity). Chúng liên tục vào buffer mỗi khi refcount giảm, collector chạy, duyệt hết,
không dọn được gì, rồi lặp lại. Tăng ngưỡng giảm số lần chạy vô ích đó.

Manual PHP vẫn mô tả root buffer là "10.000 root cố định"; đó là mô tả từ thời PHP 5.3. Từ PHP 7.3,
buffer nới được và ngưỡng thay đổi như bảng trên.

⚠️ Chi phí một lần chạy tỉ lệ với **số giá trị với tới được từ các root**, không chỉ số root. Một root
trỏ vào một cây object khổng lồ còn sống vẫn làm collector duyệt cả cây. Đây là lý do script tạo rất
nhiều object sống (import dữ liệu lớn chẳng hạn) đôi khi thấy thời gian GC đáng kể trong profiler.

### 8.5 Điều khiển và quan sát

| Hàm hoặc ini | Làm gì |
|---|---|
| `zend.enable_gc` (ini, mặc định bật) | Bật/tắt việc collector tự chạy khi chạm ngưỡng |
| `gc_enable()`, `gc_disable()`, `gc_enabled()` | Như ini nhưng đổi lúc chạy |
| `gc_collect_cycles(): int` | Chạy collector ngay, trả về số giá trị đã dọn. Chạy được cả khi GC đang tắt |
| `gc_status(): array` | Số liệu: `runs`, `collected`, `threshold`, `roots`; từ PHP 8.3 thêm `running`, `protected`, `full`, `buffer_size`, `application_time`, `collector_time`, `destructor_time`, `free_time` |
| `gc_mem_caches(): int` | Bảo bộ cấp phát trả các khối nhớ đang rảnh về hệ điều hành (mục 9.4) |

⚠️ Tắt GC không tắt việc ghi root: refcount giảm thì giá trị vẫn vào buffer, và buffer tiếp tục nới
ra. Tắt lâu thì cả buffer lẫn các vòng rác cùng phình. Ở giới hạn tối đa của buffer (rất lớn, hiếm khi
chạm tới), PHP phát warning "GC buffer overflow (GC disabled)" và thôi ghi nhận root mới.

Thí nghiệm: tạo nhiều vòng rác, một lần tắt GC, một lần bật.

```php
<?php
declare(strict_types=1);

final class Node
{
    public ?Node $peer = null;
    /** @var list<int> */
    public array $payload = [];
}

function makeGarbageCycles(int $n): void
{
    for ($i = 0; $i < $n; $i++) {
        $a = new Node();
        $b = new Node();
        $a->peer = $b;
        $b->peer = $a;               // vòng a <-> b
        $a->payload = range(1, 50);
    }   // vòng sau gán đè $a, $b (và hết hàm thì huỷ $a, $b): cặp cũ thành rác vòng
}

function mib(int $bytes): string
{
    return round($bytes / 1048576, 1) . ' MiB';
}

// Lượt 1: tắt GC tự động
gc_disable();
$base = memory_get_usage();
makeGarbageCycles(20_000);
echo 'GC tắt, bộ nhớ thêm: ', mib(memory_get_usage() - $base), "\n";
echo 'roots: ', gc_status()['roots'], "\n";
echo 'gc_collect_cycles(): ', gc_collect_cycles(), "\n";
echo 'sau khi dọn: ', mib(memory_get_usage() - $base), "\n";

// Lượt 2: bật GC
gc_enable();
$before = gc_status();
$base = memory_get_usage();
makeGarbageCycles(20_000);
$after = gc_status();
echo 'GC bật, bộ nhớ thêm: ', mib(memory_get_usage() - $base), "\n";
echo 'số lần GC tự chạy: ', $after['runs'] - $before['runs'], "\n";
echo 'đã dọn: ', $after['collected'] - $before['collected'], "\n";
echo 'roots còn trong buffer: ', $after['roots'], "\n";

// output minh hoạ (php-wasm 32-bit, PHP 8.5). Các con số MiB trên máy 64-bit sẽ lệch chút ít vì
// zend_object lớn hơn (con trỏ 8 byte); các con số đếm (roots, runs, collected) thì giống nhau:
// GC tắt, bộ nhớ thêm: 28.2 MiB
// roots: 40000
// gc_collect_cycles(): 60000
// sau khi dọn: 0.2 MiB
// GC bật, bộ nhớ thêm: 7 MiB
// số lần GC tự chạy: 3
// đã dọn: 45000
// roots còn trong buffer: 10000
```

Đọc kết quả:

- 20.000 cặp tạo ra 40.000 root: mỗi object vào buffer một lần, lúc biến `$a` hoặc `$b` thôi trỏ vào
  nó (refcount giảm từ 2 xuống 1).
- `gc_collect_cycles()` dọn 60.000 giá trị: 40.000 object cộng 20.000 array `payload` nằm trong chúng.
  Array con cũng đi theo vì nó chỉ được giữ bởi object trắng.
- Khi bật GC, collector tự chạy mỗi khi buffer đủ 10.000 root: 3 lần cho 30.000 root đầu, dọn
  15.000 cặp (45.000 giá trị). 10.000 root cuối chưa chạm ngưỡng nên vẫn nằm chờ, và 7 MiB kia chính
  là 5.000 cặp tương ứng. Bộ nhớ dao động răng cưa quanh một mức cố định thay vì tăng tuyến tính.

### 8.6 Khi nào bạn phải quan tâm

- **PHP-FPM, request ngắn**: gần như không. Hết request, engine huỷ toàn bộ bộ nhớ của request, có vòng
  hay không cũng vậy ([Chương 02](02-php-chay-nhu-the-nao.md) mục 7).
- **Process sống lâu** (queue worker, Laravel Octane, daemon, script import chạy hàng giờ): vòng rác
  tích qua hàng nghìn job. Collector rồi sẽ dọn chúng, nhưng vào lúc không đoán trước, và trong lúc
  chờ thì bộ nhớ cao hơn cần thiết. Những gì **không phải rác** (dữ liệu bị giữ trong biến `static`,
  container, cache trong array) thì collector không bao giờ dọn: đó mới là leak thật. Cách tìm và
  phòng ở [Chương 20](20-hieu-nang.md) và [Chương 30](30-laravel-testing-octane-deploy.md).
- **Phá vòng chủ động** khi bạn biết chắc một cấu trúc vòng đã hết dùng: gán `null` cho cạnh ngược
  (`$child->parent = null`) trước khi bỏ, để refcount làm việc thay cho collector.
- **Cache theo object**: dùng `WeakMap` để không giữ object sống ([Chương 10](10-oop-nang-cao.md)
  mục 12).
- Mẫu cho đoạn code cực nhạy độ trễ: `gc_collect_cycles(); gc_disable();` trước đoạn đó, `gc_enable();`
  sau. Đừng tắt GC cả process.

### 8.7 Đối chiếu Java và Go

| | PHP | Java (HotSpot) | Go |
|---|---|---|---|
| Cơ chế chính | Refcount + cycle collector | Tracing GC chia thế hệ (G1 mặc định, ngoài ra ZGC...) | Tracing GC concurrent mark-sweep, không chia thế hệ |
| Giải phóng khi nào | Ngay khi refcount về 0; vòng thì khi collector chạy | Khi GC chạy | Khi GC chạy |
| Chi phí rải ở đâu | Mỗi phép gán tăng/giảm refcount; collector duyệt các root nghi vấn | Pause (ngắn với G1, ZGC), cần chỉnh heap | CPU chạy song song, pause rất ngắn; chỉnh bằng `GOGC`, `GOMEMLIMIT` |
| Destructor | `__destruct` chạy đúng lúc refcount về 0 (trừ khi trong vòng) | Không có; `finalize()` deprecated, dùng try-with-resources | Không có; dùng `defer` |
| Vòng tham chiếu | Cần collector riêng | Không phải vấn đề | Không phải vấn đề |

*Tracing GC* (Java, Go) không đếm gì lúc gán. Định kỳ nó đi từ các *root* (biến trên stack, biến toàn
cục) lần theo mọi con trỏ, đánh dấu những gì còn với tới được, rồi dọn phần còn lại. Vòng tham chiếu
không làm khó nó, nhưng thời điểm giải phóng thì không đoán trước được. PHP chọn refcount vì mô hình
request ngắn: giải phóng tức thì và destructor đúng lúc rất có giá trị, còn vòng rác hiếm và bị xoá
sạch khi request kết thúc. Cái giá chỉ lộ ra khi PHP chạy như process sống lâu.

---

## 9. Bộ nhớ: Zend MM, memory_limit và memory_get_usage

### 9.1 Zend MM: bộ cấp phát riêng của PHP

Mọi string, array, object tạo trong một request được cấp phát qua *Zend Memory Manager* (Zend MM, file
`Zend/zend_alloc.c`), không gọi thẳng `malloc` của hệ điều hành. Lý do: chương trình PHP cấp phát và
giải phóng rất nhiều khối nhỏ (zend_string 32 byte, object 128 byte...), và một allocator chuyên cho
kiểu tải này nhanh hơn nhiều; đồng thời engine đếm được chính xác bộ nhớ của request để áp
`memory_limit`, và cuối request vứt cả khối một lần.

Cách Zend MM tổ chức (hằng số trong `Zend/zend_alloc_sizes.h`):

```
Hệ điều hành
   │  xin theo chunk 2 MiB (mmap)
   v
chunk 2 MiB = 512 trang × 4 KiB
   ├── trang đầu: thông tin quản lý chunk
   ├── vài trang chia thành ô 32 byte   (khối nhỏ: 30 cỡ cố định, từ 8 tới 3072 byte)
   ├── vài trang chia thành ô 128 byte
   └── một dãy trang liền cho khối "large" (trên 3072 byte, dưới cỡ một chunk)

khối "huge" (lớn hơn 2 MiB trừ 4 KiB): xin thẳng hệ điều hành, trả ngay khi giải phóng
```

- *Small* (8 tới 3072 byte): làm tròn lên một trong 30 cỡ cố định (8, 16, 24, 32, 40, 48, 56, 64, 80,
  96, 112, 128, 160...). Mỗi cỡ có các trang riêng chia sẵn thành ô bằng nhau. Đây là lý do mục 5.1 và
  7.4 nói "làm tròn theo bộ cấp phát": string 30 byte thực tế chiếm ô 32 byte.
- *Large* (trên 3072 byte tới dưới 2 MiB): một dãy trang 4 KiB liền nhau trong một chunk.
- *Huge* (từ cỡ một chunk trở lên): xin riêng từ hệ điều hành, giải phóng là trả lại ngay.

Biến môi trường `USE_ZEND_ALLOC=0` bắt PHP dùng `malloc` của hệ thống thay cho Zend MM; chỉ dùng khi
debug bộ nhớ bằng công cụ như valgrind.

### 9.2 memory_get_usage(): false và true

```php
<?php
declare(strict_types=1);

function mib(int $bytes): string
{
    return round($bytes / 1048576, 2) . ' MiB';
}

echo 'đầu script: ', mib(memory_get_usage()), ' / ', mib(memory_get_usage(true)), "\n";
$s = str_repeat('x', 100);
echo 'thêm 100 byte: ', mib(memory_get_usage()), ' / ', mib(memory_get_usage(true)), "\n";
$big = str_repeat('x', 5 * 1048576);
echo 'thêm 5 MiB: ', mib(memory_get_usage()), ' / ', mib(memory_get_usage(true)), "\n";
unset($big);
echo 'unset: ', mib(memory_get_usage()), ' / ', mib(memory_get_usage(true)), "\n";
echo 'đỉnh: ', mib(memory_get_peak_usage()), "\n";
memory_reset_peak_usage();
echo 'đỉnh sau reset: ', mib(memory_get_peak_usage()), "\n";

// output minh hoạ (php-wasm 32-bit, PHP 8.5; trên máy bạn con số đầu script sẽ khác):
// đầu script: 0.44 MiB / 2 MiB
// thêm 100 byte: 0.44 MiB / 2 MiB
// thêm 5 MiB: 5.5 MiB / 7.06 MiB
// unset: 0.44 MiB / 2 MiB
// đỉnh: 5.5 MiB
// đỉnh sau reset: 0.44 MiB
```

| Hàm | Đo gì |
|---|---|
| `memory_get_usage()` (hay `false`) | Tổng kích thước các khối Zend MM **đang cấp** cho script (đã làm tròn theo cỡ ô) |
| `memory_get_usage(true)` | Tổng bộ nhớ Zend MM **đã xin** từ hệ điều hành: các chunk 2 MiB và khối huge, kể cả phần đang rảnh |
| `memory_get_peak_usage()`, `(true)` | Mức cao nhất của hai con số trên từ đầu request |
| `memory_reset_peak_usage()` (PHP 8.2) | Đặt lại mức đỉnh về mức hiện tại, để đo đỉnh của từng đoạn code |

Trong ví dụ: con số `true` nhảy theo bậc 2 MiB (một chunk), string 100 byte không làm nó đổi vì vừa
chỗ trống trong chunk hiện có. String 5 MiB là khối huge: xin riêng, và trả lại hệ điều hành ngay khi
`unset`, nên cả hai con số đều về như cũ.

### 9.3 memory_limit

`memory_limit` (mặc định `128M`, `-1` là không giới hạn, đổi được bằng `ini_set()`) giới hạn con số
`memory_get_usage(true)`: mỗi khi Zend MM cần xin thêm chunk hay khối huge mà vượt giới hạn, nó thử
trả bớt các chunk đang cache, nếu vẫn không đủ thì dừng script bằng fatal error:

```
Fatal error: Allowed memory size of 16777216 bytes exhausted (tried to allocate 20480 bytes) in ... on line 23
```

- Con số đầu là giới hạn (16M = 16.777.216 byte), con số sau là kích thước lần xin **cuối cùng**, lần
  làm tràn. Nó thường nhỏ và không cho biết thủ phạm thật: thủ phạm là thứ đã chiếm phần lớn bộ nhớ
  trước đó (một array khổng lồ, một vòng lặp tích luỹ).
- Đây là fatal error, không phải exception: `try`/`catch` không bắt được ([Chương 12](12-loi-exception.md)).
  PHP 8.5 có thể in kèm stack trace cho fatal error (ini mới `fatal_error_backtraces`, mặc định bật),
  giúp biết đoạn code đang chạy.
- PHP 8.5 thêm ini `max_memory_limit` (chỉ đặt lúc khởi động, mặc định `-1`): trần cho `memory_limit`.
  Code gọi `ini_set('memory_limit', ...)` vượt trần sẽ nhận warning và bị ép về trần.
- Chữa đúng cách là giảm lượng dữ liệu giữ cùng lúc (xử lý theo lô, generator,
  [Chương 13](13-generator-iterator-spl.md)), không phải tăng `memory_limit` mãi.

### 9.4 Những điều hay bị hiểu sai

- **`memory_get_usage()` không phải RSS** (bộ nhớ hệ điều hành thấy process dùng, cột RES của `top`).
  Manual nói rõ: bộ nhớ mà extension tự `malloc` và bộ nhớ persistent không được tính, kể cả với
  `true`. Ngoài ra còn binary PHP, thư viện, shared memory của OPcache. RSS luôn lớn hơn, thường nhiều.
- **Giải phóng giá trị không có nghĩa trả RAM cho hệ điều hành.** Zend MM giữ lại các chunk rảnh để
  dùng lại, và một chunk chỉ trả được khi toàn bộ 2 MiB của nó rảnh; vài object nhỏ còn sống rải rác
  là đủ giữ cả chunk (*phân mảnh*). `gc_mem_caches()` yêu cầu trả các chunk đang rảnh, trả về số byte
  đã trả.
- Vì vậy process sống lâu (worker FPM, queue worker) thường giữ RSS ở mức đỉnh của request/job nặng
  nhất từng chạy. Cơ chế "khởi động lại định kỳ" như `pm.max_requests` của FPM
  ([Chương 18](18-fpm-nginx-opcache.md)) hay `--max-jobs`, `--memory` của queue worker Laravel
  ([Chương 29](29-laravel-queue-event-schedule-cache.md)) tồn tại chính vì điều này.

---

## 10. Compile và opcode, nhìn bằng con mắt engine

### 10.1 Nhắc lại

[Chương 02](02-php-chay-nhu-the-nao.md) mục 2 đã đi qua cả hành trình: lexer cắt mã nguồn thành token,
parser dựng AST, compiler sinh *opcode* vào các *op_array* (một cho code ngoài hàm, một cho mỗi hàm),
rồi Zend VM chạy từng opcode bằng handler C của nó. Mục này không lặp lại, mà dùng opcode để nối những
gì bạn vừa học (zval, refcount, separation, reference) với code bạn viết.

### 10.2 Toán hạng của opcode là các ô zval

Một opcode có tối đa hai toán hạng và một ô kết quả. Mỗi toán hạng thuộc một trong các loại:

| Loại | Trong output | Là gì |
|---|---|---|
| `CONST` | `int(4)`, `string("range")` | Hằng nằm trong bảng literal của op_array |
| `CV` | `CV0($a)` | *Compiled variable*: biến của bạn, đã được đánh số lúc compile |
| `TMP_VAR` | `T9` | Ô tạm cho kết quả trung gian của biểu thức |
| `VAR` | `V3` | Ô tạm có thể chứa reference hoặc kết quả lời gọi hàm |
| `UNUSED` | (không in) | Không dùng toán hạng này |

CV, TMP và VAR đều là các ô zval 16 byte nằm liền nhau trong call frame (mục 2.4). Dòng
`; (lines=16, args=0, vars=3, tmps=7)` cho biết frame cần 3 ô CV và 7 ô tạm.

Vì biến cục bộ đã thành chỉ số (`CV0`, `CV1`), đọc `$a` là đọc thẳng một ô trong frame, không tra
tên. Bảng tên-biến (*symbol table*) chỉ được dựng ra khi code cần tra biến theo tên lúc chạy: biến
biến `$$name`, `compact()`, `extract()`, `get_defined_vars()`. Code dùng các tính năng đó vừa khó đọc
vừa làm engine tốn thêm việc.

### 10.3 Thấy copy-on-write trong opcode

```php
<?php
declare(strict_types=1);

$a = range(1, 3);
$b = $a;
$b[] = 4;
$r = &$a;
$r[0] = 9;
unset($b[1]);
echo count($a), "\n";
```

Dump opcode (cách chạy như [Chương 02](02-php-chay-nhu-the-nao.md) mục 2.5, chạy ở thư mục chứa file):

```bash
php -d opcache.enable_cli=1 -d opcache.file_update_protection=0 \
    -d opcache.opt_debug_level=0x10000 cow.php
```

```
0000 INIT_FCALL 2 80 string("range")
0001 SEND_VAL int(1) 1
0002 SEND_VAL int(3) 2
0003 V3 = DO_ICALL
0004 ASSIGN CV0($a) V3
0005 ASSIGN CV1($b) CV0($a)
0006 ASSIGN_DIM CV1($b) NEXT
0007 OP_DATA int(4)
0008 ASSIGN_REF CV2($r) CV0($a)
0009 ASSIGN_DIM CV2($r) int(0)
0010 OP_DATA int(9)
0011 UNSET_DIM CV1($b) int(1)
0012 T9 = COUNT CV0($a)
0013 ECHO T9
0014 ECHO string("\n")
0015 RETURN int(1)
```

(Output minh hoạ từ php-wasm 32-bit, đã bỏ phần đầu; con số kích thước frame `80` của `INIT_FCALL` trên
máy 64-bit sẽ khác.)

Đối chiếu với các mục trước:

| Opcode | Dòng PHP | Việc của engine |
|---|---|---|
| `0004 ASSIGN` | `$a = range(1, 3)` | Chuyển zval kết quả vào ô `$a` |
| `0005 ASSIGN` | `$b = $a` | Copy zval, tăng refcount của array lên 2. Không copy dữ liệu (mục 3.2) |
| `0006 ASSIGN_DIM` + `OP_DATA` | `$b[] = 4` | Ghi vào phần tử: `SEPARATE_ARRAY`, refcount 2 nên tách (mục 3.3). Giá trị ghi nằm ở opcode phụ `OP_DATA` vì một opcode chỉ có hai toán hạng |
| `0008 ASSIGN_REF` | `$r = &$a` | Bọc giá trị của `$a` vào `zend_reference`, `$a` và `$r` cùng trỏ hộp (mục 4.2) |
| `0009 ASSIGN_DIM` | `$r[0] = 9` | Đi vào hộp; array bên trong có refcount 1 nên ghi thẳng |
| `0011 UNSET_DIM` | `unset($b[1])` | Cũng là thao tác ghi: tách nếu cần, rồi để lại bia mộ (mục 6.4) |
| `0012 COUNT` | `count($a)` | Compiler thay lời gọi `count()` bằng opcode riêng ([Chương 02](02-php-chay-nhu-the-nao.md) mục 2.6) |

Thói quen hữu ích: khi băn khoăn "dòng này có copy không", nhìn opcode để biết đó là thao tác đọc hay
ghi, rồi áp quy tắc separation.

### 10.4 Các công cụ xem opcode khác

- `opcache.opt_debug_level`: `0x10000` là opcode ngay sau compile, `0x20000` là sau khi optimizer của
  OPcache chạy. Có sẵn, không cần cài gì; output ra *stderr*.
- `phpdbg`, trình debug đi kèm PHP (nhiều bản đóng gói tách nó thành gói riêng): `phpdbg -p* file.php`
  in opcode của cả file (kể cả hàm và class) rồi thoát; `-p` chỉ in phần code chính,
  `-p=ten_ham` in một hàm.
- VLD (*Vulcan Logic Dumper*): extension PECL, phải cài thêm. Trước khi có `opt_debug_level`, đây là
  công cụ phổ biến nhất để xem opcode.

Các công cụ này để học và để hiểu. Chúng không phải công cụ đo hiệu năng; muốn biết code chậm ở đâu,
dùng profiler ([Chương 20](20-hieu-nang.md)).

---

## 11. JIT: từ opcode tới mã máy

### 11.1 JIT là gì và nằm ở đâu

Zend VM chạy mỗi opcode bằng cách nhảy tới handler C của nó; handler đọc toán hạng từ các ô zval,
kiểm tra type (vì biến PHP có thể là bất cứ gì), làm việc, rồi nhảy tới opcode kế tiếp. Với vòng lặp
tính toán chặt, chi phí "lấy lệnh, kiểm tra type, nhảy" này chiếm phần lớn thời gian.

*JIT* (*Just-In-Time compiler*, có từ PHP 8.0) dịch opcode của đoạn code chạy nhiều sang **mã máy** của
CPU (x86-64, AArch64) ngay trong lúc chạy. Khi JIT biết chắc, hoặc đoán và kiểm tra, rằng một biến luôn
là `int` hay `float`, nó sinh mã máy giữ giá trị trong thanh ghi CPU và bỏ hẳn các bước kiểm tra type.

Vài điều cần biết về vị trí của nó:

- JIT là một phần của OPcache: không có OPcache thì không có JIT. Nó dùng chính thông tin kiểu mà
  optimizer của OPcache suy luận được.
- Mã máy được lưu trong một vùng của shared memory OPcache có kích thước `opcache.jit_buffer_size`, nên
  được dùng chung giữa mọi worker PHP-FPM và sống qua các request.
- Từ PHP 8.4, nếu JIT được bật mà khởi tạo thất bại thì PHP dừng với fatal error lúc khởi động. Extension
  ghi đè hàm thực thi của VM (`zend_execute_ex`, thường là debugger hay profiler) làm JIT tự tắt kèm
  warning "JIT is incompatible with third party extensions that override zend_execute_ex(). JIT
  disabled."

### 11.2 Hai chế độ: tracing và function

| | `tracing` | `function` |
|---|---|---|
| Đơn vị compile | *Trace*: một đường chạy thực tế qua code (một vòng lặp, một chuỗi lời gọi) | Nguyên cả hàm |
| Thông tin kiểu | Kiểu **quan sát được lúc chạy**, kèm *guard* kiểm tra | Chỉ kiểu suy luận tĩnh được |
| Mã CRTO tương ứng | 1254 | 1205 |
| Manual | "Recommended for most users" | |

Tracing JIT hoạt động theo các bước:

1. VM chạy bình thường và đếm ở đầu vòng lặp, đầu hàm.
2. Bộ đếm chạm ngưỡng: vòng lặp chạy `opcache.jit_hot_loop` lần (mặc định 61 từ PHP 8.5, trước đó 64),
   hàm được gọi `opcache.jit_hot_func` lần (mặc định 127). VM ghi lại một trace: đúng dãy opcode vừa
   chạy cùng kiểu thực tế của từng biến.
3. JIT compile trace thành mã máy, chèn *guard* ở những chỗ dựa trên giả định ("`$i` là int").
4. Lần sau chạy thẳng mã máy. Guard sai (ví dụ `$i` bỗng thành float) thì thoát về VM qua một *side
   exit*.
5. Side exit nào xảy ra nhiều (`opcache.jit_hot_side_exit`, mặc định 8 lần) thì được compile thành
   *side trace* riêng cho nhánh đó.

`opcache.jit` nhận bốn giá trị chữ: `disable` (tắt hẳn, không bật lại lúc chạy được), `off` (tắt, bật
lại được lúc chạy), `tracing` hoặc `on`, và `function`. Ngoài ra nó nhận một số 4 chữ số *CRTO* cho
người cần chỉnh sâu: C là tối ưu theo CPU (ví dụ dùng AVX), R là cấp phát thanh ghi, T là khi nào
compile (trigger), O là mức tối ưu. `tracing` tương đương 1254, `function` tương đương 1205.

### 11.3 PHP 8.4: JIT mới trên IR, và công tắc đổi chỗ

PHP 8.4 có hai thay đổi riêng rẽ về JIT, hay bị nhập làm một.

**JIT viết lại trên IR framework** (RFC "A new JIT implementation based on IR Framework" của Dmitry
Stogov, đã được chấp nhận):

- JIT của 8.0 tới 8.3 sinh mã máy **trực tiếp** từ opcode, với backend riêng cho x86 và cho AArch64
  (AArch64 thêm từ 8.1); sửa một tính năng phải sửa assembler ở cả hai.
- JIT mới dựng một *IR* (*Intermediate Representation*, biểu diễn trung gian) từ opcode, rồi giao cho IR
  framework làm tối ưu không phụ thuộc máy, cấp phát thanh ghi, sắp lịch lệnh và sinh mã. Chỉ còn một
  backend.
- Theo RFC: cùng tập tính năng như JIT cũ; mã sinh ra nhanh hơn khoảng 5 tới 10% và nhỏ hơn trên
  benchmark tổng hợp (`bench.php`, `micro_bench.php`), còn tốc độ ứng dụng thực tế không đổi. Tốc độ
  compile của tracing JIT gần như cũ, function JIT compile chậm hơn tới 4 lần.
- Không có thay đổi gì với code PHP của bạn.

**Đổi giá trị mặc định của ini** (manual OPcache):

| | Trước 8.4 | Từ 8.4 |
|---|---|---|
| `opcache.jit` | `tracing` | `disable` |
| `opcache.jit_buffer_size` | `0` | `64M` |
| Cách bật JIT | Đặt `jit_buffer_size` khác 0 | Đặt `opcache.jit=tracing` (hoặc `function`) |

JIT **tắt theo mặc định ở cả hai thời kỳ**; chỉ có công tắc là đổi chỗ. ⚠️ Mang cấu hình cũ (chỉ đặt
`opcache.jit_buffer_size=128M`) lên 8.4 thì JIT vẫn tắt mà không báo gì.

```ini
; php.ini, PHP 8.4+
opcache.enable=1
opcache.jit=tracing
opcache.jit_buffer_size=64M
```

Kiểm tra JIT có thật sự chạy (chạy trong terminal, máy có PHP 8.4+):

```bash
php -d opcache.enable_cli=1 -d opcache.jit=tracing \
    -r 'var_dump(opcache_get_status()["jit"]["on"] ?? null);'
# in bool(true) nếu JIT đang chạy
```

Mục `jit` của `opcache_get_status()` còn có `buffer_size` và `buffer_free`: buffer đầy thì code nóng
mới không được compile nữa. Trong PHP-FPM, gọi hàm này từ một trang nội bộ vì CLI có OPcache riêng.

### 11.4 JIT giúp được gì

JIT chỉ tăng tốc phần **thời gian CPU chạy code PHP**:

- Code *CPU-bound* (thời gian chủ yếu là tính toán bằng PHP thuần: xử lý ảnh, parser, thuật toán số
  học, mô phỏng) được lợi rõ.
- Web app điển hình là *I/O-bound*: phần lớn thời gian một request là chờ MySQL, Redis, HTTP. Phần CPU
  còn lại thì nhiều trong hàm C có sẵn (`array_*`, PDO, `json_encode`, `preg_*`), vốn đã là mã máy.
  Trang phát hành PHP 8.0 trên php.net cũng ghi: JIT nhanh hơn nhiều lần trên benchmark tổng hợp, còn
  ứng dụng web điển hình thì ngang PHP 7.4 ([Chương 02](02-php-chay-nhu-the-nao.md) mục 2.6).

Vì vậy với app Laravel, câu trả lời đúng là "đo trước khi bật". Cách đo và các con số cụ thể ở
[Chương 20](20-hieu-nang.md); cấu hình production ở [Chương 18](18-fpm-nginx-opcache.md).

### 11.5 Đối chiếu Java

JVM HotSpot cũng thông dịch bytecode trước, đếm độ nóng rồi JIT (phân tầng C1, C2), và cũng cần
*warm-up*. Nhưng JIT là lý do chính Java nhanh; bỏ JIT đi Java chậm hơn rất nhiều. PHP thì ngược lại:
không có JIT vẫn đã nhanh nhờ OPcache và VM tối ưu, nên phần lợi thêm nhỏ hơn. Và trong PHP-FPM, mã máy
JIT sống qua các request, nhưng trạng thái của ứng dụng (container, config, route của Laravel) vẫn dựng
lại mỗi request; chi phí đó JIT không xoá được.

---

## Lỗi thường gặp

| Lỗi | Vì sao sai | Cách đúng |
|---|---|---|
| Truyền array bằng `&` "cho đỡ copy" | Truyền by value vốn không copy (COW); `&` còn thêm gián tiếp và vẫn phải tách nếu array đang chia sẻ (mục 4.5) | Nhận by value, trả array mới; chỉ dùng `&` khi thật sự muốn sửa biến của caller |
| `foreach ($a as &$v)` trên array lớn chỉ để đọc | Bọc từng phần tử vào `zend_reference` 32 byte, ở lại sau vòng lặp (mục 4.5) | Duyệt by value; cần sửa thì ghi qua key `$a[$k] = ...` |
| Kết luận từ refcount của array literal | Literal có thể được op_array giữ thêm hoặc là immutable khi có OPcache (mục 2.7) | Thí nghiệm bằng giá trị tạo lúc chạy (`range()`, `str_repeat()`), nhớ trừ 1 cho tham số của `debug_zval_dump()` |
| Nghĩ `unset` phần tử sẽ giảm bộ nhớ của array | Chỉ để lại bia mộ; dung lượng không giảm (mục 6.4) | Tạo array mới (`array_values()`, copy sang biến mới) khi cần thu nhỏ |
| Dùng `spl_object_id()` làm key cache lâu dài | Handle được tái sử dụng khi object chết (mục 7.2) | `WeakMap` |
| Trông vào `__destruct` để đóng tài nguyên khi object có thể nằm trong vòng | Destructor bị hoãn tới khi cycle collector chạy (mục 8.2) | Đóng tường minh bằng `try`/`finally`, hoặc phá vòng trước khi bỏ |
| `gc_disable()` cả process cho "nhanh" | Root buffer và rác vòng phình mãi (mục 8.5) | Chỉ tắt quanh đoạn ngắn nhạy độ trễ, bật lại ngay |
| So `memory_get_usage()` với RSS của process | Không tính bộ nhớ extension tự cấp phát, OPcache, binary; Zend MM giữ lại chunk rảnh (mục 9.4) | Dùng `memory_get_usage()` để so tương đối trong script; theo dõi RSS bằng công cụ hệ điều hành |
| Tăng `memory_limit` mỗi khi gặp "Allowed memory size exhausted" | Che giấu việc giữ quá nhiều dữ liệu cùng lúc (mục 9.3) | Xử lý theo lô, generator; đo đỉnh bằng `memory_get_peak_usage()` |
| Lên PHP 8.4 với cấu hình JIT cũ và tưởng JIT đang chạy | Từ 8.4, `opcache.jit` mặc định `disable` (mục 11.3) | Đặt `opcache.jit=tracing`, kiểm tra `opcache_get_status()['jit']['on']` |

## Tóm tắt chương

- Mọi giá trị PHP là một zval 16 byte: 8 byte value, 4 byte type info, 4 byte dùng theo ngữ cảnh. `null`,
  `bool`, `int`, `float` nằm trọn trong zval; string, array, object, resource, reference nằm riêng, mở
  đầu bằng header chứa refcount.
- Zval được nhúng thẳng vào chỗ chứa (call frame, bucket, slot property), không cấp phát riêng. Refcount
  nằm ở giá trị lớn, không ở zval.
- Refcount về 0 là giải phóng ngay, destructor chạy ngay. Copy-on-write: gán, truyền chỉ tăng refcount;
  ghi khi refcount lớn hơn 1 thì tách, và chỉ tách một tầng.
- Reference là một hộp `zend_reference` có refcount riêng; array bên trong vẫn COW bình thường. `&`
  không làm nhanh hơn, còn tốn thêm bộ nhớ.
- `zend_string` lưu độ dài và cache hash; interned string là một bản duy nhất cho mỗi literal và tên,
  không refcount, nằm trong shared memory khi có OPcache (`opcache.interned_strings_buffer`).
- Array là HashTable giữ thứ tự chèn bằng vị trí bucket. Packed array (key int tăng dần) bỏ phần hash, từ
  PHP 8.2 chỉ 16 byte mỗi phần tử; hash array 40 byte. `unset` để lại bia mộ, dung lượng không giảm.
- Object nằm trong object store, handle là chỉ số ô và được tái sử dụng. Property khai báo nằm trong
  slot, nên object gọn hơn array kết hợp. Object không COW.
- Cycle collector dọn vòng tham chiếu: array/object bị giảm refcount vào root buffer, chạm ngưỡng (mặc
  định 10.000) thì thử trừ cạnh nội bộ để tìm rác. Ngưỡng tự điều chỉnh từ 7.3.
- `memory_get_usage()` là bộ nhớ Zend MM đang cấp, `(true)` là bộ nhớ đã xin từ OS và là thứ
  `memory_limit` so sánh; cả hai đều không phải RSS.
- JIT (8.0+, thuộc OPcache) dịch opcode nóng sang mã máy; `tracing` là chế độ khuyến nghị. 8.4 viết lại
  JIT trên IR và đổi công tắc: phải đặt `opcache.jit=tracing`. Lợi lớn cho code CPU-bound, gần như
  không cho web app I/O-bound.

## Câu hỏi tự kiểm tra

1. Vì sao `bool` không có type `IS_BOOL` trong zval? Kiểu nào nằm trọn trong zval, kiểu nào không?
2. `debug_zval_dump($x)` in `refcount(2)` trong khi bạn chỉ có một biến `$x`. Giải thích. Và vì sao
   với `$x = [1, 2, 3]` con số có thể còn cao hơn? (mục 2.7)
3. Cho `$data` là array hai tầng, `$copy = $data; $copy['a'][] = 1;`. Những array nào bị copy, những
   array nào vẫn dùng chung? (mục 3.3)
4. Hàm `function f(array &$items)` chỉ đọc `$items` có nhanh hơn `function f(array $items)` không?
   Nếu trong hàm có ghi vào `$items` và caller đang chia sẻ array đó với biến khác thì sao? (mục 4.3)
5. Vì sao sửa `$copy[0]` lại làm đổi `$arr[0]` sau `$ref = &$arr[0]; $copy = $arr;`? Vì sao
   `unset($ref)` trước khi copy thì không còn hiện tượng đó?
6. Interned string là gì? Một string đọc từ database có phải interned không? Khi nào cần tăng
   `opcache.interned_strings_buffer`?
7. Mô tả các bước tra `$a['name']` trong một hash array. Vì sao `foreach` trả phần tử đúng thứ tự chèn?
8. Kể ba thao tác làm một packed array chuyển thành hash array. Vì sao lấp lại một lỗ đã `unset` lại
   buộc phải chuyển? (mục 6.5)
9. Vì sao refcount một mình không dọn được vòng tham chiếu? Cycle collector biết một nhóm object là rác
   bằng cách nào?
10. `memory_get_usage()` báo 20 MB nhưng `top` báo process PHP-FPM dùng 90 MB. Kể các lý do có thể. Con
    số nào được so với `memory_limit`?

## Bài tập

1. **Nhật ký refcount.** Viết script tạo một array bằng `range()`, rồi lần lượt: gán cho biến khác,
   truyền vào một hàm chỉ đọc, truyền vào một hàm có ghi, đưa vào một array khác, `unset` từng biến.
   Sau mỗi bước gọi `debug_zval_dump()` và ghi vào comment refcount thật (đã trừ 1) cùng lời giải thích.
   Dùng `memory_get_usage()` để chỉ ra chính xác bước nào có copy.
2. **Packed hay hash.** Dùng hàm `kind()` ở mục 6.5, viết ít nhất 8 thí nghiệm của riêng bạn (ví dụ
   `array_merge` hai list, `array_slice` có và không giữ key, `sort`, `array_reverse`, `array_unique`,
   `json_decode` một JSON object). Dự đoán trước kết quả, chạy, rồi giải thích những chỗ đoán sai. Đo
   thêm bộ nhớ của một triệu phần tử cho hai trường hợp đáng chú ý nhất.
3. **Săn rò rỉ vòng.** Viết một class `TreeNode` có `$parent` và `array $children`. Viết hàm dựng cây
   1.000 node rồi bỏ đi, gọi 200 lần trong vòng lặp với GC tắt, in `memory_get_usage()` và
   `gc_status()['roots']` sau mỗi 50 lần. Sau đó sửa code theo hai cách: (a) bật GC, (b) giữ GC tắt
   nhưng thêm method `detach()` phá vòng trước khi bỏ cây. So sánh bộ nhớ, `runs`, `collected` của các
   phương án và viết vài dòng kết luận.
4. **Object hay array.** Đọc 100.000 dòng dữ liệu giả (sinh bằng vòng lặp) thành ba dạng: array kết hợp,
   object `stdClass` (dynamic property), object của một class có property khai báo kiểu. Đo bộ nhớ từng
   dạng và giải thích kết quả bằng kiến thức ở mục 6 và 7. Gợi ý: nhớ rằng thêm property vào
   `stdClass` cần bảng hash.

## Đọc thêm

- PHP Manual: [Garbage Collection](https://www.php.net/manual/en/features.gc.php),
  [Reference Counting Basics](https://www.php.net/manual/en/features.gc.refcounting-basics.php),
  [Collecting Cycles](https://www.php.net/manual/en/features.gc.collecting-cycles.php),
  [What References Are](https://www.php.net/manual/en/language.references.whatare.php),
  [debug_zval_dump](https://www.php.net/manual/en/function.debug-zval-dump.php),
  [gc_status](https://www.php.net/manual/en/function.gc-status.php),
  [memory_get_usage](https://www.php.net/manual/en/function.memory-get-usage.php),
  [Core php.ini directives](https://www.php.net/manual/en/ini.core.php) (`memory_limit`, `max_memory_limit`),
  [OPcache runtime configuration](https://www.php.net/manual/en/opcache.configuration.php)
  (`interned_strings_buffer`, `opt_debug_level`, `opcache.jit`, `jit_buffer_size`, `jit_hot_*`),
  [History of PHP](https://www.php.net/manual/en/history.php.php)
- RFC: [JIT](https://wiki.php.net/rfc/jit),
  [A new JIT implementation based on IR Framework](https://wiki.php.net/rfc/jit-ir)
- php-src nhánh [PHP-8.5](https://github.com/php/php-src/tree/PHP-8.5): `Zend/zend_types.h` (zval,
  zend_string, zend_array, zend_object, zend_reference), `Zend/zend_hash.c` (`zend_array_dup`, resize,
  packed), `Zend/zend_string.h` (`zend_string_extend`, hash DJBX33A), `Zend/zend_gc.c` (màu, ngưỡng,
  root buffer), `Zend/zend_alloc.c` và `Zend/zend_alloc_sizes.h` (Zend MM), `Zend/zend_objects_API.c`
  (object store), `Zend/Optimizer/sccp.c` (tính sẵn hàm lúc compile), `UPGRADING` (thay đổi ini của 8.5)
- [PHP Internals Book](https://www.phpinternalsbook.com/php7/zvals.html): phần zval, memory management,
  zend_string, hashtable
- Nikita Popov: [Internal value representation in PHP 7, part 1](https://www.npopov.com/2015/05/05/Internal-value-representation-in-PHP-7-part-1.html),
  [part 2](https://www.npopov.com/2015/06/19/Internal-value-representation-in-PHP-7-part-2.html),
  [PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html)
- David F. Bacon, V.T. Rajan: "Concurrent Cycle Collection in Reference Counted Systems" (ECOOP 2001),
  bài báo gốc của thuật toán cycle collector
