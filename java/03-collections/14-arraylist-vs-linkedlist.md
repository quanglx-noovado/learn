# Chọn implementation đúng giữa ArrayList và LinkedList

> Dịch từ [Choosing the Right Implementation Between ArrayList and LinkedList](https://dev.java/learn/api/collections-framework/arraylist-vs-linkedlist/) — dev.java.
> Mọi số đo benchmark trong bài là của máy tác giả. Đừng coi chúng là con số tuyệt đối — hãy tự đo trên môi trường của bạn.

## Giới thiệu

Collections Framework cho bạn hai implementation của interface [`List`][List]: [`ArrayList`][ArrayList] và [`LinkedList`][LinkedList]. Có cái nào tốt hơn cái nào không? Bạn nên chọn cái nào trong ứng dụng của mình?

Phần này đi qua khác biệt của cả hai implementation. Bạn sẽ thấy hiệu năng của các thao tác chúng cung cấp, và sẽ đo **memory footprint** của chúng. Cuối cùng bạn sẽ đưa ra được lựa chọn đúng cho use case của mình.

## Độ phức tạp thuật toán (algorithm complexity)

### Độ phức tạp của một số thao tác list phổ biến

Điểm khởi đầu của mọi cuộc tranh luận bạn thấy khắp nơi về khác biệt giữa list dựa trên array và linked list là **algorithm complexity**, đo bằng ký hiệu *O(n)*. Độ phức tạp của các thao tác khác nhau mà interface [`List`][List] cung cấp phụ thuộc vào implementation bạn dùng, và thường được mô tả là *O(1)*, *O(n)* hoặc thậm chí *O(ln(n))*.

Hãy so sánh độ phức tạp này cho ba thao tác cơ bản:

- **Lấy một phần tử** từ list. Và vì có khác biệt, hãy so sánh việc lấy phần tử ở đầu list, cuối list, và giữa list.
- **Iterate** qua các phần tử của list. Lại nữa, bạn có (ít nhất) hai pattern: iterate bằng index, hoặc bằng [`Iterator`][Iterator].
- **Chèn một phần tử**. Và lần nữa, vì có khác biệt, hãy so sánh việc chèn ở đầu list, giữa list, và cuối list — dù cái cuối không thật sự là "chèn".

Ta sẽ không so sánh việc thay thế một phần tử bằng phần tử khác, vì nó thực chất giống với việc đọc phần tử bạn muốn thay.

Đây là độ phức tạp của tất cả các thao tác trên, như bạn tìm thấy trong bất kỳ sách hay nào về data structure:

| Thao tác | ArrayList | LinkedList |
|---|---|---|
| Đọc phần tử đầu | O(1) | O(1) |
| Đọc phần tử cuối | O(1) | O(1) |
| Đọc phần tử giữa | O(1) | O(n) |
| Thêm vào cuối | O(1) | O(1) |
| Chèn vào đầu | O(n) | O(1) |
| Chèn vào giữa | O(n) | O(n) |

Nhìn thì ổn cả, và không có nhiều khác biệt: [`LinkedList`][LinkedList] là *O(n)* ở hai thao tác — đọc giữa và chèn giữa.

Có hai điểm đáng lưu ý về các thao tác này.

**Thứ nhất:** đọc phần tử cuối là *O(1)* trên [`LinkedList`][LinkedList] vì implementation này mang một tham chiếu **trực tiếp** tới phần tử cuối của list.

**Thứ hai:** các thao tác trên [`ArrayList`][ArrayList] **không giống** các thao tác trên [`LinkedList`][LinkedList]. Với [`ArrayList`][ArrayList], thao tác là **di chuyển một array kích thước *n*** từ chỗ này sang chỗ khác; còn với [`LinkedList`][LinkedList], thao tác là **đi theo *n* tham chiếu** để tìm phần tử bạn cần. Ta cần đo chính xác chi phí của hai thao tác này.

### Algorithm complexity thực sự nghĩa là gì?

Ký hiệu *O(n)* nghĩa là: **vượt qua một ngưỡng nào đó**, thời gian thuật toán của bạn cần để xử lý dữ liệu tỉ lệ với lượng dữ liệu (*n*). Nói đơn giản, nếu lượng dữ liệu bạn xử lý ở trên ngưỡng đó, nhân đôi lượng dữ liệu cũng nhân đôi thời gian xử lý. Với độ phức tạp *O(1)*, thuật toán của bạn không phụ thuộc vào lượng dữ liệu. Điều đó hợp lý: đọc phần tử đầu tiên của list không phụ thuộc vào kích thước list.

Vậy ký hiệu *O(n)* thực chất cho bạn **hành vi tiệm cận (asymptotic)** của thuật toán. Điểm quan trọng của định nghĩa trên là *vượt qua một ngưỡng nào đó*. Ngưỡng đó là bao nhiêu, và nó so với lượng dữ liệu bạn xử lý trong ứng dụng thì thế nào?

Giả sử bạn chạy một thuật toán trên dữ liệu nào đó. Và bạn biết số phép toán thuật toán đó thực hiện đúng bằng *a\*n + b*. Giả sử *a = 10* và *b = 1*. Khi đó nếu bạn xử lý từ 10 phần tử trở lên, việc giả định thuật toán chạy trong *n* cho bạn sai số dưới 1%. Nhưng nếu *a = 1* và *b = 10* thì nói rằng thuật toán chạy trong *n* chỉ đúng khi xử lý từ 1_000 phần tử trở lên. Ngưỡng của bạn là 10 ở ví dụ đầu, và 1_000 ở ví dụ sau.

Ý là: biết độ phức tạp là *O(n)* thì hay, nhưng bạn cần biết nhiều hơn. Nó áp dụng vào use case của bạn thế nào? Ngưỡng cho ứng dụng của bạn là bao nhiêu? Rõ ràng nếu ngưỡng là 1_000 mà bạn xử lý 100 phần tử mỗi lần thì công thức đó **không** áp dụng cho use case của bạn.

Class [`LinkedList`][LinkedList] và [`ArrayList`][ArrayList] đều implement interface [`List`][List], nhưng implementation của chúng khác nhau, thậm chí dẫn tới những khác biệt tinh vi về hành vi.

Có những cơ chế ẩn bên trong ảnh hưởng tới hiệu năng, vượt xa khỏi algorithm complexity đơn thuần. Phần còn lại của bài sẽ đi qua tất cả, để giúp bạn ra quyết định có căn cứ về implementation nên dùng.

## Đọc phần tử từ một List

Hãy tạo benchmark đầu tiên, gồm việc đọc phần tử từ một list:

- phần tử đầu,
- rồi phần tử cuối,
- rồi phần tử ở giữa.

Vì ta kỳ vọng kết quả khác nhau khi kích thước list thay đổi, ta sẽ chạy benchmark với các kích thước khác nhau.

Lưu ý mọi benchmark trên trang này được thực hiện bằng [JMH](https://github.com/openjdk/jmh) — công cụ duy nhất bạn nên dùng để đo hiệu năng một cách đáng tin cậy.

### Đọc phần tử đầu và cuối của một List

Code chạy benchmark trông như sau. Ta chạy cho cả [`ArrayList`][ArrayList] và [`LinkedList`][LinkedList], với các kích thước list khác nhau. Kết quả được truyền vào JMH blackhole để chắc rằng không có tối ưu hóa nào của JVM bị kích hoạt làm phép đo trở nên vô nghĩa.

```java
List<Integer> ints = ...; // varies in size

int LAST = ints.size() - 1;
int MIDDLE = ints.size()/2;

// 1st bench
ints.get(0);

// 2nd bench
ints.get(LAST);

// 3rd bench
ints.get(MIDDLE);
```

Bạn có thể so sánh các con số trên trang này **với nhau**, vì tất cả benchmark đều chạy trên cùng một máy. Dù vậy, rất ít khả năng bạn nhận được đúng những con số này trên máy mình. Chúng tôi khuyến khích bạn tự benchmark chính xác những phép tính bạn cần làm trong ứng dụng, trên một máy và trong ngữ cảnh càng gần môi trường production càng tốt.

Kết quả cho thao tác *đọc phần tử đầu*:

```text
ArrayList     SIZE  Score   Error  Units
Read first      10  1.181 ± 0.022  ns/op
Read first     100  1.200 ± 0.041  ns/op
Read first    1000  1.167 ± 0.009  ns/op
Read first   10000  1.174 ± 0.014  ns/op
```

```text
LinkedList    SIZE  Score   Error  Units
Read first      10  1.127 ± 0.030  ns/op
Read first     100  1.107 ± 0.008  ns/op
Read first    1000  1.121 ± 0.016  ns/op
Read first   10000  1.119 ± 0.014  ns/op
```

Như bạn thấy, kết quả giống nhau ở cả hai implementation, và không phụ thuộc kích thước list — đúng như kỳ vọng.

Kết quả cho thao tác *đọc phần tử cuối*:

```text
ArrayList     SIZE  Score   Error  Units
Read last       10  1.248 ± 0.020  ns/op
Read last      100  1.232 ± 0.035  ns/op
Read last     1000  1.240 ± 0.019  ns/op
Read last    10000  1.254 ± 0.040  ns/op
```

```text
LinkedList    SIZE  Score   Error  Units
Read last       10  1.493 ± 0.040  ns/op
Read last      100  1.467 ± 0.019  ns/op
Read last     1000  1.475 ± 0.019  ns/op
Read last    10000  1.484 ± 0.042  ns/op
```

Kết quả này hơi khác một chút, cho thấy [`LinkedList`][LinkedList] mất hiệu năng chút ít. Khác biệt rất nhỏ, chỉ một phần của nanosecond, và không thật sự đáng kể.

### Đọc phần tử giữa của một List

Tình hình khác hẳn khi bạn cố chạm tới giữa list.

```text
ArrayList     SIZE  Score   Error  Units
Read middle     10  1.571 ± 0.055  ns/op
Read middle    100  1.616 ± 0.073  ns/op
Read middle   1000  1.543 ± 0.018  ns/op
Read middle  10000  1.537 ± 0.010  ns/op
```

```text
LinkedList    SIZE     Score     Error  Units
Read middle     10     3.211 ±   0.023  ns/op
Read middle    100    31.118 ±   0.321  ns/op
Read middle   1000   566.079 ±   8.696  ns/op
Read middle  10000  7836.099 ± 902.666  ns/op
```

Như bạn thấy, chạm tới phần tử giữa của một array gần như bằng với chạm tới phần tử cuối, và không phụ thuộc kích thước array — ít nhất với các kích thước đang test.

Với [`LinkedList`][LinkedList] thì khác. Chạm tới phần tử giữa **đắt**, và phụ thuộc vào số phần tử trong list. Việc chạm tới phần tử cuối nhanh bằng phần tử đầu là do implementation [`LinkedList`][LinkedList] có tham chiếu trực tiếp tới node đầu và node cuối của linked list nội bộ.

Để hiểu vì sao chạm tới phần tử giữa lại đắt, bạn cần tính tới cấu trúc của một linked list như nó được hiện thực trong class [`LinkedList`][LinkedList].

![The internal structure of a LinkedList](https://dev.java/assets/images/collections-framework/04_Linked-list-structure.png)

Bản hiện thực linked list của Java là một tập các object `Node`, trong đó một `Node` chứa **ba** tham chiếu: một tới node kế tiếp, một tới node trước đó, và một tới object mà node này mang. Vậy nó thực chất là một **doubly linked list**. Thêm nữa, class [`LinkedList`][LinkedList] chứa hai tham chiếu khác: một tới node đầu và một tới node cuối. Nên chạm tới node đầu hay cuối thì nhanh. Ngược lại, đọc node giữa thì không nhanh vậy, vì implementation cần đọc tất cả tham chiếu `next` cho tới khi đến node nó cần. Đó chính là điều bạn quan sát được trên benchmark: đọc phần tử giữa của [`LinkedList`][LinkedList] tốn kém, và càng tốn kém hơn khi list càng lớn.

Lưu ý rằng đọc node giữa là **trường hợp xấu nhất**. Vì có tham chiếu tới node đầu và cuối, implementation luôn chọn đường đi **ngắn nhất** tới phần tử nó cần chạm.

Sự suy giảm hiệu năng này là do hiệu ứng **pointer chasing**. Như bạn biết, đọc tham chiếu kích hoạt việc nạp vùng memory được tham chiếu vào CPU cache. Nếu vùng memory bạn cần đọc đã ở đó thì tốt, bạn có nó ngay. Nếu không, đó gọi là **cache miss** — bạn phải đi lấy nó, và việc đó mất thời gian.

Bạn quan sát được điều này bằng cách tạo linked list theo một cách đặc biệt. Trong benchmark vừa chạy, linked list được tạo bằng đoạn code sau, dùng một stream:

```java
var ints =
IntStream.range(0, LIST_SIZE)
         .boxed()
         .collect(Collectors.toCollection(LinkedList::new));
```

Rất có thể, vì ta không ở trong một ứng dụng thật, tất cả object node của linked list này thực tế được lưu **gần nhau** trong memory. Nên khi bạn đọc tham chiếu `next` từ một node, rất có thể tham chiếu đó đã có trong cache, vì nó được nạp cùng với node hiện tại.

Hãy tưởng tượng một cách khác để tạo linked list, đảm bảo tất cả node bị **cô lập** khỏi nhau trong memory. Ở ví dụ sau, ta tạo một số lượng object node nằm giữa hai object node của list dùng cho benchmark. Và ta giữ một tham chiếu tới list này trong suốt benchmark để đảm bảo garbage collector không di chuyển object của ta trong memory. Rồi ta chạy benchmark nhiều lần với các giá trị `SPARSE_INDEX` khác nhau.

```java
var ints = new LinkedList<>();
var intsOther = new LinkedList<>();
for (int i = 0; i < LIST_SIZE; i++) {
    ints.add(i);
    for (int k = 0; k < SPARSE_INDEX; k++) {
        intsOther.add(k);
    }
}
```

Kết quả:

```text
LinkedList   SIZE  SPARSE    Score    Error  Units
Read middle  1000       0  561.428 ±  4.853  ns/op
Read middle  1000       1  602.401 ± 17.126  ns/op
Read middle  1000      10  944.997 ± 31.920  ns/op
Read middle  1000     100 1509.282 ± 28.749  ns/op
```

Đúng vậy, pointer chasing làm hỏng hiệu năng đọc giá trị ngẫu nhiên trong [`LinkedList`][LinkedList]. Như bạn thấy, một linked list với node phân bố ngẫu nhiên trong memory **chậm gấp ba lần** so với cùng linked list đó với node lưu liên tục nhau. Và rất có thể trong một ứng dụng liên tục thêm/xóa phần tử khỏi linked list, đây chính là tình huống bạn đang ở trong.

## Iterate qua các phần tử của một List

### Iterate bằng index và bằng Iterator

Iterate qua phần tử của list có thể hiện thực bằng hai pattern. Cái đầu là cách kinh điển của Collections Framework, dùng [`Iterator`][Iterator]. Cái thứ hai là dùng index để truy cập từng phần tử. Như bạn có thể đoán, iterate qua các node của [`LinkedList`][LinkedList] sẽ chịu ảnh hưởng của pointer chasing, vì đi tới node kế tiếp chính là đi theo một tham chiếu.

Hai pattern dùng cho benchmark này như sau. Đầu tiên, cái dùng index:

```java
var ints = ...; // LinkedList or ArrayList
for (var index = 0; index < ints.size(); index++) {
   var v = ints.get(index);
   // pass v to the blackhole
}
```

Và thứ hai, cái dùng [`Iterator`][Iterator]. Lưu ý ở ví dụ sau, dùng pattern *for-each*, compiler tạo một iterator cho bạn trong byte code:

```java
for (var v: ints) {
   // pass v to the blackhole
}
```

Với [`ArrayList`][ArrayList], hai pattern gần như tương đương. Dùng index đắt hơn một chút, vì bạn phải quản lý index đó. Có thể bạn thắc mắc vì sao tăng một `int` lại đắt hơn việc phải quản lý một iterator. Hóa ra pattern *for-each* **không** phơi iterator ra trong source code của bạn, nên nó không thể dùng cho việc gì khác ngoài iterate qua list này. Khi tối ưu code, JIT compiler có thể thấy điều đó, và trong một số trường hợp có thể tối ưu đoạn code này, **tránh việc tạo iterator**. Bạn có được code nhanh hơn nhiều, vì không object nào thật sự được tạo hay quản lý.

```text
ArrayList         SIZE    Score   Error Units
Iterate iterator  1000    1.447 ± 0.024 us/op
Iterate index     1000    1.986 ± 0.045 us/op
```

Với [`LinkedList`][LinkedList] thì khác. Dùng iterator đắt hơn trường hợp [`ArrayList`][ArrayList], chủ yếu do pointer chasing. Ở trường hợp [`ArrayList`][ArrayList], tất cả những gì bạn cần làm là cộng một offset vào một địa chỉ trên heap để tới một phần tử; còn trong [`LinkedList`][LinkedList], bạn phải đi theo một tham chiếu, có lẽ kèm một cache miss nếu node kế tiếp không có ở đó.

Dùng index thì **cực kỳ tốn kém**, và thực ra là một pattern khá ngớ ngẩn. Iterate bằng index nghĩa là bắt đầu từ đầu list và di chuyển từ node này sang node khác *index* lần, **cho từng phần tử** của list. Độ phức tạp của việc iterate này là *O(n²)*. **Đừng bao giờ** dùng pattern này trên một [`LinkedList`][LinkedList]. Nó mất khoảng nửa millisecond để iterate qua một linked list 1000 phần tử, trong khi với iterator chỉ mất 4 microsecond.

```text
LinkedList        SIZE    Score   Error Units
Iterate iterator  1000    4.950 ± 0.116 us/op
Iterate index     1000  584.889 ± 4.396 us/op
```

### Iterate trên một bản copy của LinkedList

Iterate trên [`LinkedList`][LinkedList] đắt gấp đôi so với [`ArrayList`][ArrayList]. Nên có thể bạn thắc mắc liệu **copy** [`LinkedList`][LinkedList] sang một list dựa trên array trước khi iterate có hiệu quả hơn không. Tất nhiên việc này tốn memory, và bạn có thể gặp vấn đề nếu list bị sửa trong lúc bạn iterate, nhưng cũng đáng xem hiệu năng.

Xét pattern sau và chạy benchmark:

```java
var ints =
   IntStream.range(0, 1_000)
            .boxed()
            .collection(Collection.toCollection(LinkedList::new));

var copyOfInts = ints.stream().toList();
for (var v: copyOfInts) {
   // pass v to the blackhole
}
```

Kết quả như dưới. Như bạn thấy, với một list 1000 phần tử, việc copy list tiêu tốn 4% thời gian iterate qua các phần tử của nó. Nên nếu bạn chịu được chi phí memory và cần iterate nhiều lần, hoặc truy cập ngẫu nhiên nhiều lần, thì việc copy linked list sang list dựa trên array **hoàn vốn rất nhanh**.

Lưu ý ta dùng pattern [`Stream.toList()`][streamToList] để tạo list này. Thứ nhất, nó tạo một list unmodifiable; thứ hai, nó dùng một tối ưu để tạo sẵn array với kích thước đúng ngay từ đầu, thay vì tăng array dần khi thêm phần tử — cái mà [`ArrayList`][ArrayList] và [`Collectors.toList()`][collectorsToList] đang làm.

```text
LinkedList           SIZE  ITERATION    Score    Error  Units
toList then iterate  1000          1    5.182 ±  0.347  us/op
toList then iterate  1000         10   14.031 ±  0.793  us/op
toList then iterate  1000        100  100.104 ±  7.422  us/op
```

Tới đây, dữ liệu cho thấy một điều quan trọng: **pointer chasing và cache miss có thể giết hiệu năng của bạn**. Điều này ảnh hưởng tới mọi data structure dựa trên tham chiếu: linked list tất nhiên, mà còn trie tree, binary tree, red-black tree, skip list, và ở mức độ thấp hơn là hash map.

## Chèn phần tử vào một List

Linked list nổi tiếng với hiệu năng tuyệt vời khi chèn một phần tử vào vị trí ngẫu nhiên. Chèn chỉ là chuyển tham chiếu *next* của node trước tới node bạn cần chèn, và tương tự cho tham chiếu *previous* của node sau. Việc này trông có vẻ khá rẻ. Ngoại trừ chuyện, để làm được vậy, bạn cần **truy cập** node trước và node sau. Và bạn đã thấy ở ví dụ trước rằng việc đó rất đắt.

Ngược lại, chèn một phần tử vào list dựa trên array trông phức tạp hơn. Bạn cần dịch phần bên phải của array sang phải một ô để tạo chỗ cho phần tử muốn chèn. Việc di chuyển nội dung array nghe như không hề rẻ.

![Inserting an Element in a Array](https://dev.java/assets/images/collections-framework/05_Inserting-ArrayList.png)

Và nhân đây, **xóa** một phần tử cũng vậy. Với linked list bạn cần sắp lại pointer của hai node; với array bạn cần copy một phần array sang trái.

Hai thuật toán khác nhau, đoán cái nào nhanh hơn không dễ, nên hãy đo hiệu năng.

### Chèn phần tử vào LinkedList

Xét ba trường hợp: chèn vào đầu list, vào giữa, và vào cuối. Chèn vào cuối thì giống thêm phần tử vào list hơn.

Ta kỳ vọng như sau. Vì [`LinkedList`][LinkedList] có tham chiếu trực tiếp tới node đầu và cuối của chuỗi, ta không nên thấy nhiều khác biệt giữa chèn vào đầu và vào cuối, và nó không nên phụ thuộc kích thước list. Ngược lại, chèn vào giữa sẽ đắt hơn, và chi phí đó tăng theo kích thước list.

Đây là điều ta quan sát được với chèn vào đầu. Khác biệt khi kích thước list tăng không đáng kể.

```text
LinkedList      SIZE    Score    Error  Units
Insert first      10    7.002  ± 0.306  ns/op
Insert first     100    7.126  ± 0.424  ns/op
Insert first    1000    7.561  ± 0.371  ns/op
Insert first   10000    7.738  ± 0.614  ns/op
```

Và tương tự với thêm phần tử vào cuối. Khác biệt so với chèn vào đầu vẫn còn đó, và vẫn rất nhỏ.

```text
LinkedList      SIZE    Score    Error  Units
Adding            10    9.135  ± 0.137  ns/op
Adding           100    9.076  ± 0.082  ns/op
Adding          1000    9.795  ± 0.399  ns/op
Adding         10000    9.549  ± 0.202  ns/op
```

Chèn vào giữa theo index thì đắt hơn nhiều, và chi phí này tăng với list lớn hơn. Cái giá bạn trả để chạm tới các phần tử giữa là cao. Phép đo này thực hiện với một linked list **thưa (sparse)**, tức là các phần tử node không được lưu liên tục trong memory.

```text
LinkedList      SIZE      Score     Error  Units
Insert middle     10     10.641 ±   0.679  ns/op
Insert middle    100     49.122 ±   1.808  ns/op
Insert middle   1000    584.870 ±   6.925  ns/op
Insert middle  10000  46157.961 ± 379.327  ns/op
```

### Chèn phần tử vào ArrayList

Có thể bạn nghĩ chèn một phần tử chỉ là dịch một phần array sang phải một ô. Nhưng có một trường hợp khác bạn cần tính tới: việc **resize** array đó. Bạn không thể thêm phần tử vào một array đã đầy. Điều [`ArrayList`][ArrayList] làm trong trường hợp đó là copy toàn bộ array sang một array lớn hơn, rồi thêm phần tử của bạn. Kích thước array mới được tính từ kích thước array hiện tại. Hiện nay nó tăng với hệ số **1.5**. Nên nếu bạn liên tục thêm phần tử trong một vòng lặp, thao tác tăng này càng ngày càng ít xảy ra.

Vậy hãy xét hai tình huống: chèn vào một array còn chỗ cho phần tử mới, và tình huống array đã đầy.

Khi array còn chỗ, mọi thứ diễn ra như kỳ vọng. Chèn vào vị trí cuối — tức là thêm một phần tử — gần như không phụ thuộc kích thước array. Sự tăng thời gian tính toán có lẽ do một cache miss để chạm tới cuối array khi nó trở nên quá lớn. Nhưng không có khác biệt đáng kể giữa [`ArrayList`][ArrayList] kích thước 1_000 và 10_000. Chèn vào giữa đắt hơn do phải copy phần còn lại của array để chèn được phần tử. Như bạn đoán, nếu bạn chèn vào **đầu** — thao tác đắt nhất — việc di chuyển array đắt hơn, đơn giản vì bạn di chuyển gấp đôi số phần tử.

```text
ArrayList  SIZE    Score    Error  Units
Adding       10    2.215  ± 0.053  ns/op
Adding      100    2.184  ± 0.027  ns/op
Adding     1000    5.607  ± 0.856  ns/op
Adding    10000    5.240  ± 0.777  ns/op
```

```text
ArrayList        SIZE    Score     Error  Units
Insert middle     10   23.708  ±  0.370  ns/op
Insert middle    100   25.399  ±  0.241  ns/op
Insert middle   1000   56.061  ±  0.840  ns/op
Insert middle  10000  294.457  ±  4.689  ns/op
```

```text
ArrayList       SIZE    Score    Error  Units
Insert first     10   22.380  ±  0.266  ns/op
Insert first    100   26.929  ±  0.385  ns/op
Insert first   1000   78.958  ±  1.429  ns/op
Insert first  10000  717.892  ±  9.242  ns/op
```

Khi array **không** còn chỗ, implementation của [`ArrayList`][ArrayList] copy array nội bộ sang một array lớn hơn. Thao tác này không bị kích hoạt trong các benchmark trước, nhưng bạn dễ dàng tạo một benchmark khác với array đã đầy để đo tác động của việc resize.

So sánh các benchmark đầu với cùng benchmark trên một array lớn hơn cho bạn thấy cái giá của việc cấp phát array mới và copy array hiện tại sang array mới. Như kỳ vọng, nó phụ thuộc kích thước array, và khá đắt. May là nó **không xảy ra thường xuyên**. Số lần resize tăng **dưới tuyến tính** (sub-linearly), hệ số tăng giảm dần theo mỗi lần resize. Điều này nhắc bạn rằng bất cứ khi nào có thể tạo array với kích thước đúng ngay từ đầu, hãy làm vậy để tiết kiệm việc cấp phát lại.

```text
ArrayList                  SIZE       Score    Error  Units
Adding in a full array      10      19.300 ±    2.953  ns/op
Adding in a full array     100      45.488 ±    3.922  ns/op
Adding in a full array    1000     432.351 ±   46.055  ns/op
Adding in a full array   10000    4140.668 ±  329.160  ns/op
```

Vì chi phí cấp phát lại cao hơn nhiều chi phí chèn, bạn có thể kỳ vọng thấy rất ít khác biệt giữa chèn vào giữa hay vào đầu list. Đúng như hai benchmark sau:

```text
ArrayList                        SIZE     Score    Error  Units
Insert middle in a full array     10    39.334 ±    1.588  ns/op
Insert middle in a full array    100    61.037 ±    2.130  ns/op
Insert middle in a full array   1000   451.471 ±   27.247  ns/op
Insert middle in a full array  10000  4638.632 ±  360.694  ns/op
```

```text
ArrayList                       SIZE     Score     Error  Units
Insert first in a full array     10    28.288 ±    0.656  ns/op
Insert first in a full array    100    52.935 ±    2.457  ns/op
Insert first in a full array   1000   452.179 ±   37.434  ns/op
Insert first in a full array  10000  4762.783 ±  133.468  ns/op
```

## So sánh việc chèn giữa LinkedList và ArrayList

Như bạn thấy, [`ArrayList`][ArrayList] **thắng** [`LinkedList`][LinkedList] ở mọi thao tác trừ một. Điều này có thể bất ngờ, vì từ góc nhìn thuật toán, [`LinkedList`][LinkedList] trông tốt hơn, đặc biệt ở thao tác chèn. Nhưng vì thuật toán hiệu quả đó chạy trên hardware khiến pointer chasing rất đắt, overhead này trở nên chiếm ưu thế và làm nó không hiệu quả.

Có hai lý do [`LinkedList`][LinkedList] tốt hơn [`ArrayList`][ArrayList] ở việc chèn vào **đầu** list. [`LinkedList`][LinkedList] có hai lợi thế:

- thời gian chèn **không phụ thuộc** kích thước list,
- vì có tham chiếu trực tiếp tới phần tử đầu, pointer chasing chỉ có thể xảy ra **nhiều nhất một lần**.

Thêm nữa, nó không phụ thuộc vào cách bạn đã thêm phần tử vào [`LinkedList`][LinkedList]. Việc node bị phân bố ngẫu nhiên trong heap memory không ảnh hưởng. Điều tương tự với việc thêm phần tử vào **cuối** list. Hiệu năng gần như bằng nhau, vì trong trường hợp đó [`ArrayList`][ArrayList] không cần di chuyển phần tử nào của array nội bộ. Thao tác cuối này không nhanh bằng [`ArrayList`][ArrayList], nhưng nó **dự đoán được**. Nếu implementation [`ArrayList`][ArrayList] quyết định đã đến lúc tăng array nội bộ, cú đánh vào hiệu năng có thể rất lớn.

Dù cái giá của một lần cấp phát lại là cao, vì nó xảy ra hiếm, tác động lên hiệu năng ứng dụng của bạn được **trung bình hóa**. Nhớ rằng bạn có thể (và nên!) tạo [`ArrayList`][ArrayList] với kích thước đúng bất cứ khi nào có thể. Nhìn chung, **sai** khi cho rằng cái giá của việc cấp phát lại là lý luận đáng kể để chọn [`LinkedList`][LinkedList] thay vì [`ArrayList`][ArrayList].

Vậy có hai use case mà [`LinkedList`][LinkedList] đáng chú ý, và hoạt động tốt hơn hoặc gần bằng [`ArrayList`][ArrayList]: thao tác ở **đầu** hoặc **cuối** list. Thao tác đó có thể là đọc, chèn, hoặc xóa — cái mà thực chất tốn bằng chèn.

Và đúng vậy, [`LinkedList`][LinkedList] là implementation stack hay queue rất tốt. Còn với list thông thường thì không tốt lắm. Chúng gần như luôn bị [`ArrayList`][ArrayList] vượt qua.

## Phân tích mức tiêu thụ memory của LinkedList và ArrayList

[`ArrayList`][ArrayList] và [`LinkedList`][LinkedList] hoạt động thế nào về mặt memory? Đây là câu hỏi khó, vì các JVM khác nhau có thể quản lý memory khác nhau, và một JVM đơn lẻ có thể có chiến lược khác nhau tùy lượng memory nó đang chạy trong đó.

Ta dùng công cụ OpenJDK [`JOL`](https://github.com/openjdk/jol) để đo memory mà các implementation này tiêu thụ.

Nói chung, lưu một lượng object cho trước trong [`LinkedList`][LinkedList] cần **nhiều memory hơn** lưu cùng số object đó trong [`ArrayList`][ArrayList]. Trong phần lớn trường hợp là nhiều **rất nhiều**. Có lý do rõ ràng cho việc đó: mỗi tham chiếu trong [`LinkedList`][LinkedList] được lưu trong một object `Node`, mà object đó còn lưu hai tham chiếu khác — một tới `Node` trước và một tới `Node` sau. Việc này thường cần **24 byte**, vì bạn phải cộng thêm header của object `Node`. Bạn có thể xem class `Node` trong class `LinkedList`; đó là một private class và không có JavaDoc.

Mức tiêu thụ memory chính xác có thể thay đổi tùy ứng dụng. Nếu ứng dụng của bạn dùng dưới 32GB, con số này phần lớn thời gian là chính xác. Ví dụ, với 1000 object, một [`LinkedList`][LinkedList] sẽ tiêu thụ hơn 24kB memory một chút, trong khi một [`ArrayList`][ArrayList] chỉ tiêu thụ hơi dưới 5kB.

Tuy vậy có một trường hợp lưu object trong [`ArrayList`][ArrayList] lại đắt hơn. Nếu bạn chỉ có **một** object để lưu, thì [`ArrayList`][ArrayList] bạn tạo có thể bọc một array kích thước 10 — phụ thuộc vào cách bạn đã tạo [`ArrayList`][ArrayList]. Và trong trường hợp đó, [`ArrayList`][ArrayList] của bạn tiêu thụ nhiều memory hơn [`LinkedList`][LinkedList]: 80 byte so với 56 byte.

Nên nếu bạn có nhiều list một phần tử, bạn có thể gặp vấn đề tiêu thụ memory. Nói cách khác: nếu bạn có một ứng dụng tạo nhiều array list, và bạn gặp vấn đề memory bất thường, hãy điều tra chính xác hơn xem các array list của bạn đang giữ bao nhiêu object. Có thể bạn đang tạo những array list gần như rỗng, tiêu thụ rất nhiều memory không dùng tới.

Mức tiêu thụ memory chính xác của một [`ArrayList`][ArrayList] một phần tử thực ra phụ thuộc vào cách bạn tạo nó. Đây là các pattern khác nhau và kết quả:

```java
var intsV1 = new ArrayList<Integer>();
intsV1.add(1); // wraps an array of size 10

var intsV2 = new ArrayList<Integer>();
intsV2.addAll(List.of(1)); // wraps an array of size 10

var intsV3 = new ArrayList<Integer>(List.of(1)); // wraps an array of size 1
```

Nếu bạn ở trong trường hợp đó, bạn vẫn có nhiều giải pháp. Dùng [`LinkedList`][LinkedList] là một; nhưng có lẽ bạn cũng dùng được một trong các implementation non-modifiable lấy từ các method [`List.of()`][ListOf]. Chúng hiệu quả hơn cả [`ArrayList`][ArrayList] lẫn [`LinkedList`][LinkedList] về memory: chỉ **26 byte** cho một phần tử. Nhưng bạn cần nhớ chúng là unmodifiable.

Một điểm cuối về tiêu thụ memory. Vì cách nó hoạt động, [`LinkedList`][LinkedList] **luôn** dùng đúng số phần tử nó cần mang. Không có node rỗng nào trong [`LinkedList`][LinkedList]. Ngược lại, [`ArrayList`][ArrayList] tự động tăng khi array nội bộ đầy.

Hóa ra **không có cơ chế nào** trong [`ArrayList`][ArrayList] tự động **thu nhỏ** array này. Nên nếu ứng dụng của bạn xóa nhiều phần tử khỏi [`ArrayList`][ArrayList], bạn có thể tới tình huống array nội bộ lớn — vì nó từng cần lớn ở thời điểm nào đó — nhưng giờ gần như rỗng, tiêu thụ memory vô ích.

Thực tế, [`ArrayList`][ArrayList] giữ một array được copy sang array lớn hơn khi nó đầy. Nhưng array này **không bao giờ** được copy sang array nhỏ hơn nếu nó trở nên gần rỗng. Nên nếu bạn gặp vấn đề memory, đây rõ ràng cũng là điểm bạn cần điều tra.

May là có method [`ArrayList.trimToSize()`][trimToSize] cắt capacity của array nội bộ về đúng size của list. Nhân đây, nếu bạn gọi [`ArrayList.trimToSize()`][trimToSize] trên một [`ArrayList`][ArrayList] một phần tử, nó sẽ trở nên **nhỏ hơn** một [`LinkedList`][LinkedList] một phần tử. Bạn sẽ tiết kiệm memory ngay lập tức khi gọi method này, nhưng cũng sẽ phải cho list tăng lại lần tới khi thêm phần tử.

|  | Memory cho 1 phần tử |
|---|---|
| ArrayList | 76 byte |
| ArrayList | 44 byte (sau `trimToSize()`) |
| LinkedList | 56 byte |
| List.of() | 26 byte |

|  | Memory cho 1_000 phần tử |
|---|---|
| ArrayList | 4_976 byte |
| LinkedList | 24_032 byte |

Như bạn thấy, dù [`ArrayList`][ArrayList] có thể đang quản lý một array không được dùng hết, nó vẫn dùng **ít memory hơn nhiều** so với [`LinkedList`][LinkedList] tương ứng. Việc quản lý các object node tiêu thụ 24 byte cho mỗi object, nhiều hơn hẳn việc quản lý một array rỗng một phần. Trường hợp xấu nhất là khi [`ArrayList`][ArrayList] phải cấp phát lại. Trong lúc đó, [`ArrayList`][ArrayList] có **hai** array: cái cũ và cái mới lớn hơn. Ngay cả trong trường hợp này, [`ArrayList`][ArrayList] vẫn tiêu thụ ít memory hơn [`LinkedList`][LinkedList]. Nên nếu memory là vấn đề trong ứng dụng của bạn, [`ArrayList`][ArrayList] **luôn** là lựa chọn tốt nhất.

### Bạn lưu được bao nhiêu phần tử trong một heap cho trước?

Giả sử vì lý do nào đó, ứng dụng của bạn liên tục thêm phần tử vào một list. Hãy so sánh số phần tử bạn quản lý được với [`ArrayList`][ArrayList] và [`LinkedList`][LinkedList] trong một heap memory kích thước *H*. Ta chỉ quan tâm tới memory tiêu thụ bởi bản thân list, không phải kích thước các object bạn lưu.

[`LinkedList`][LinkedList] cần một object node cho mỗi phần tử, kích thước 24 byte. Nên phép tính đơn giản: bạn lưu được tối đa *H*/24 phần tử.

Với [`ArrayList`][ArrayList], tình hình phức tạp hơn chút. Nếu array nội bộ của [`ArrayList`][ArrayList] đầy thì bạn lưu được *H*/4 phần tử. Nhưng có thể một phần array không được dùng, nên trung bình có thể ít hơn. Nếu bạn vừa cấp phát lại array thì 33% của nó không được dùng, nên trung bình bạn dùng khoảng 6 byte mỗi object. Vậy trong một ứng dụng liên tục thêm phần tử vào list, [`ArrayList`][ArrayList] hiệu quả hơn [`LinkedList`][LinkedList] với hệ số **từ 4 đến 6 lần**.

Trường hợp xấu nhất là khi [`ArrayList`][ArrayList] đang cấp phát lại. Không có lãng phí ở đây: array cũ của bạn đầy. Nhưng trong quá trình đó, [`ArrayList`][ArrayList] có tham chiếu tới một array đầy, cộng thêm một array kích thước 1.5\**N*. Nên trong quá trình đó [`ArrayList`][ArrayList] tiêu thụ 10 byte mỗi object. Ngay cả trong trường hợp xấu nhất này, [`ArrayList`][ArrayList] vẫn hiệu quả hơn [`LinkedList`][LinkedList] với hệ số 2.4.

Với một kích thước heap cho trước, [`ArrayList`][ArrayList] **luôn** lưu được nhiều phần tử hơn [`LinkedList`][LinkedList], kể cả trong lúc cấp phát lại. Có thể tới 6 lần nhiều hơn.

## Vậy nên chọn implementation nào?

[`ArrayList`][ArrayList] là một implementation tốt, vượt [`LinkedList`][LinkedList] ở gần như mọi thao tác list kinh điển — ít nhất là khi cái bạn cần là một list thông thường. Dù implementation [`LinkedList`][LinkedList] được hiện thực với thuật toán tốt hơn, nó là cấu trúc dựa trên pointer, chịu ảnh hưởng của pointer chasing. Nên iterate thì đắt, lấy phần tử theo index thì đắt, và điều đó tác động tới mọi thao tác kinh điển: chèn, thay thế, xóa. Dù bản thân các thao tác đó tốn ít hơn trên [`LinkedList`][LinkedList] so với [`ArrayList`][ArrayList], hiệu năng bị giết bởi việc **truy cập được đúng phần tử** thì rất đắt, do pointer chasing.

[`ArrayList`][ArrayList] không giỏi chèn, vì thao tác [`System.arraycopy()`][arraycopy], nhưng vẫn phần lớn tốt hơn [`LinkedList`][LinkedList]. Việc cấp phát lại của [`ArrayList`][ArrayList] là thao tác khá đắt, nhưng rất ít khi dùng, và bạn có thể tránh được nếu biết cần lưu bao nhiêu phần tử. Bạn tránh được resize bằng cách tạo [`ArrayList`][ArrayList] đủ lớn để chứa mọi object bạn cần, ngay từ đầu.

Có **một** trường hợp [`LinkedList`][LinkedList] tốt hơn [`ArrayList`][ArrayList]: khi bạn cần truy cập phần tử **đầu** hoặc **cuối** của list, dù để đọc, thay thế, hay chèn. Tức là khi cái bạn cần thực ra là một **stack** hoặc **queue**, không phải list thông thường. Và nhân đây, [`LinkedList`][LinkedList] đúng là implement [`Queue`][Queue]. Lưu ý [`LinkedList`][LinkedList] cũng implement [`Deque`][Deque]. Nếu cái bạn cần là một double-ended queue ([`Deque`][Deque]) thì bạn nên ưu tiên implementation [`ArrayDeque`][ArrayDeque].

Về memory, bạn cần nhớ [`LinkedList`][LinkedList] tiêu thụ nhiều memory hơn [`ArrayList`][ArrayList] rất nhiều. Có một ngoại lệ: một [`LinkedList`][LinkedList] một phần tử có thể tiêu thụ ít memory hơn một [`ArrayList`][ArrayList] một phần tử, trong trường hợp [`ArrayList`][ArrayList] đó thực chất bọc một array kích thước 10. Bạn sửa được tình huống này bằng [`List.of()`][ListOf], hoặc bằng cách gọi [`ArrayList.trimToSize()`][trimToSize].

Trong trường hợp bạn cần các list mang ít phần tử, và bạn chạy ứng dụng trong môi trường hạn chế memory, việc tạo một [`ArrayList`][ArrayList] với initial capacity là 2 hoạt động tốt. Nó chỉ chiếm 48 byte để lưu 0, 1 hoặc 2 phần tử. Nếu bạn tiếp tục thêm phần tử, nó mở array lên 3, rồi 4, rồi 6 phần tử (tương ứng 56, 56 và 64 byte tổng). Nó nhỏ hơn [`LinkedList`][LinkedList] ở **mọi** size khác 0. Nó còn nhỏ hơn cả [`ArrayList`][ArrayList] capacity mặc định cho tới khi bạn tới size 9; và bằng size với [`ArrayList`][ArrayList] đã trim cho tới size 7.

Bạn thấy điều đó ở bảng sau, thu được theo quy trình:

- Tạo một list: `new ArrayList<>(2)`, `new LinkedList<>()`, `new ArrayList<>()`, và `new ArrayList<>().trimToSize()`.
- Kiểm tra mức tiêu thụ memory ban đầu.
- Liên tục thêm phần tử từng cái một, rồi trim list cuối, và kiểm tra mức tiêu thụ memory.

| Số phần tử | ArrayList(2) | LinkedList | ArrayList mặc định | ArrayList mặc định đã trim |
|---|---|---|---|---|
| 0 | 40 | 32 | 40 | 40 |
| 1 | 48 | 56 | 80 | 48 |
| 2 | 48 | 80 | 80 | 48 |
| 3 | 56 | 104 | 80 | 56 |
| 4 | 56 | 128 | 80 | 56 |
| 5 | 64 | 152 | 80 | 64 |
| 6 | 64 | 176 | 80 | 64 |
| 7 | 80 | 200 | 80 | 72 |
| 8 | 80 | 224 | 80 | 72 |
| 9 | 80 | 248 | 80 | 80 |
| 10 | 96 | 272 | 80 | 80 |

Một điều cuối cần nhớ: [`ArrayList`][ArrayList] **không bao giờ tự co lại**. Gọi thao tác remove, hay thao tác clear, không copy array nội bộ sang array nhỏ hơn. Bạn sửa tình huống này bằng cách gọi [`ArrayList.trimToSize()`][trimToSize], nó kích hoạt việc copy array nội bộ sang một array nhỏ hơn.

---

## Tóm lại (bản rút gọn để nhớ)

- **Mặc định dùng `ArrayList`.** Đúng gần như mọi lúc.
- Chỉ chọn `LinkedList` khi bạn thực sự cần **stack/queue** — và khi đó `ArrayDeque` thường còn tốt hơn.
- **Đừng bao giờ** iterate `LinkedList` bằng index — đó là *O(n²)*.
- Biết trước số phần tử? Tạo `new ArrayList<>(n)` để tránh reallocation.
- `ArrayList` không tự co — xóa nhiều phần tử thì gọi `trimToSize()`.
- Bài học lớn nhất: **big-O không phải toàn bộ câu chuyện**. Hardware (CPU cache, pointer chasing) có thể đảo ngược kết luận trên giấy.

---

**Bài tập**

1. Tự viết benchmark thô (dùng `System.nanoTime()`, chạy nhiều lần, bỏ vài lần đầu để JIT warm up) so sánh iterate `ArrayList` vs `LinkedList` 100_000 phần tử. Kết quả có cùng *hướng* với bài không?
2. Chứng minh bằng code rằng iterate `LinkedList` bằng index là *O(n²)*: đo với n = 1_000, 2_000, 4_000 và xem thời gian tăng theo hệ số bao nhiêu.
3. `new ArrayList<>()` rồi `add(1)` bọc array size 10, còn `new ArrayList<>(List.of(1))` bọc array size 1. Đọc source của `ArrayList` trong JDK để tự xác nhận. (Gợi ý: `DEFAULT_CAPACITY`, `EMPTY_ELEMENTDATA`.)
4. Đối chiếu với Go: `append` vào slice cũng nhân đôi capacity. Go không có `LinkedList` trong stdlib (chỉ `container/list`). Theo bạn, vì sao thiết kế Go lại "nghèo" hơn ở điểm này — và đó là thiếu sót hay là quan điểm?

[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[ArrayList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html
[LinkedList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html
[ArrayDeque]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayDeque.html
[Queue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html
[Deque]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html
[Iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html
[ListOf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#of(E...)
[trimToSize]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html#trimToSize()
[streamToList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/Stream.html#toList()
[collectorsToList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/stream/Collectors.html#toList()
[arraycopy]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/System.html#arraycopy(java.lang.Object,int,java.lang.Object,int,int)
