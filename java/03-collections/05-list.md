# Mở rộng Collection với List

> Dịch từ [Extending Collection with List](https://dev.java/learn/api/collections-framework/lists/) — dev.java.

## Khám phá interface List

Nếu bạn nóng lòng muốn thực hành các phép toán list phổ biến nhất trên code thật, hãy nhảy xuống cuối trang: [Thực hành các phép toán trên List](#thực-hành-các-phép-toán-trên-list).

Interface [`List`][List] mang hai chức năng mới cho collection thuần:

- Thứ tự bạn iterate qua các phần tử của một list **luôn giống nhau**, và nó tôn trọng thứ tự các phần tử đã được thêm vào list.
- Các phần tử của list có **index**.

## Chọn implementation cho interface List

Trong khi interface [`Collection`][Collection] không có implementation riêng nào trong Collections Framework (nó dựa vào implementation của các sub-interface), interface [`List`][List] có 2: [`ArrayList`][ArrayList] và [`LinkedList`][LinkedList]. Như bạn có thể đoán, cái đầu được xây trên một array nội bộ, cái sau trên một doubly-linked list.

Cái nào tốt hơn? Nếu bạn không chắc chọn cái nào, lựa chọn tốt nhất của bạn có lẽ là [`ArrayList`][ArrayList].

Những gì đúng về linked list vào thời máy tính mới ra đời ở thập niên 60 giờ không còn đúng nữa. Khả năng của linked list vượt array ở thao tác chèn và xóa bị giảm đi rất nhiều bởi hardware hiện đại, CPU cache và chuyện *pointer chasing*. Iterate qua phần tử của [`ArrayList`][ArrayList] **nhanh hơn nhiều** so với [`LinkedList`][LinkedList], chủ yếu vì pointer chasing và CPU cache miss.

Vẫn có trường hợp linked list nhanh hơn array. Một doubly-linked list truy cập phần tử **đầu** và **cuối** nhanh hơn [`ArrayList`][ArrayList]. Đây là use case chính khiến [`LinkedList`][LinkedList] tốt hơn [`ArrayList`][ArrayList]. Vậy nếu ứng dụng của bạn cần một stack Last In First Out (LIFO, sẽ nói sau trong tutorial này), hoặc một queue chờ First In First Out (FIFO, cũng sẽ nói sau), và không dùng method [`List`][List] nào khác, thì chọn [`LinkedList`][LinkedList] có lẽ tốt hơn [`ArrayList`][ArrayList]. [`ArrayDeque`][ArrayDeque] cũng là một implementation đáng chú ý — nó **không** chấp nhận giá trị null.

Ngược lại, nếu bạn định iterate qua các phần tử, hoặc truy cập chúng ngẫu nhiên theo index, thì [`ArrayList`][ArrayList] có lẽ là cược tốt nhất.

Bạn có thể tìm thảo luận sâu hơn về khác biệt giữa [`ArrayList`][ArrayList] và [`LinkedList`][LinkedList] ở cuối chương này: [Chọn implementation đúng giữa ArrayList và LinkedList](14-arraylist-vs-linkedlist.md).

## Truy cập phần tử bằng index

Interface [`List`][List] thêm vào [`Collection`][Collection] nhiều method làm việc với index.

### Truy cập một object đơn lẻ

- [`add(index, element)`][addIdx]: chèn object cho trước vào vị trí `index`, điều chỉnh index của các phần tử còn lại, nếu có.
- [`get(index)`][get]: trả về object ở `index` cho trước.
- [`set(index, element)`][set]: thay phần tử ở index cho trước bằng phần tử mới.
- [`remove(index)`][removeIdx]: xóa phần tử ở `index` cho trước, điều chỉnh index của các phần tử còn lại.

Gọi các method này chỉ hoạt động với index hợp lệ. Nếu index không hợp lệ, exception [`IndexOutOfBoundsException`][IndexOutOfBoundsException] sẽ được throw.

### Tìm index của một object

Các method [`indexOf(element)`][indexOf] và [`lastIndexOf(element)`][lastIndexOf] trả về index của phần tử cho trước trong list, hoặc -1 nếu không tìm thấy.

### Lấy một SubList

Method [`subList(start, end)`][subList] trả về một list gồm các phần tử giữa index `start` và `end - 1`. Nếu index không hợp lệ, [`IndexOutOfBoundsException`][IndexOutOfBoundsException] sẽ được throw.

Lưu ý là list trả về là một **view** trên list chính. Do đó mọi thao tác sửa đổi trên sublist đều phản ánh lên list chính và ngược lại.

Ví dụ, bạn có thể xóa một đoạn nội dung của list bằng pattern sau:

```java
List<String> strings = new ArrayList<>(List.of("0", "1", "2", "3", "4", "5"));
IO.println(strings);
strings.subList(2, 5).clear();
IO.println(strings);
```

Kết quả:

```text
[0, 1, 2, 3, 4, 5]
[0, 1, 5]
```

### Chèn một collection

Pattern cuối trong danh sách này là chèn một collection vào một index cho trước: [`addAll(int index, Collection collection)`][addAllIdx].

```java
List<String> strings = new ArrayList<>(List.of("0", "1", "5"));
List<String> toBeInserted = List.of("2", "3", "4");
IO.println("Strings: " + strings);
IO.println("To be inserted: " + toBeInserted);
IO.println("Inserting at index 2");
strings.addAll(2, toBeInserted);
IO.println("Strings: " + strings);
```

Kết quả:

```text
Strings: [0, 1, 5]
To be inserted: [2, 3, 4]
Inserting at index 2
Strings: [0, 1, 2, 3, 4, 5]
```

## Sắp xếp các phần tử của một List

Một list giữ phần tử theo một thứ tự đã biết. Đây là khác biệt chính so với collection thuần. Nên việc sắp xếp phần tử của list là hợp lý. Đó là lý do method [`sort()`][sort] được thêm vào interface [`List`][List] ở JDK 8.

Ở Java SE 7 và trước đó, bạn sắp xếp phần tử của [`List`][List] bằng cách gọi [`Collections.sort()`][CollectionsSort] và truyền list vào làm tham số, kèm một comparator nếu cần.

Từ Java SE 8, bạn gọi [`sort()`][sort] trực tiếp trên list và truyền comparator làm tham số. **Không** có overload nào của method này mà không nhận tham số. Gọi nó với comparator là null sẽ giả định rằng phần tử của [`List`][List] implement [`Comparable`][Comparable], và bạn sẽ nhận [`ClassCastException`][ClassCastException] nếu không phải vậy.

Nếu bạn không thích gọi method với tham số null (và bạn đúng!), bạn vẫn có thể gọi nó với [`Comparator.naturalOrder()`][naturalOrder] để đạt cùng kết quả.

## Iterate qua các phần tử của một List

Interface [`List`][List] cho bạn thêm một cách iterate nữa: [`ListIterator`][ListIterator]. Bạn lấy iterator kiểu này bằng cách gọi [`listIterator()`][listIterator]. Bạn có thể gọi method này không tham số, hoặc truyền vào một index nguyên. Trong trường hợp đó, việc iterate sẽ bắt đầu từ index này.

Interface [`ListIterator`][ListIterator] extends [`Iterator`][Iterator] thường mà bạn đã biết. Nó thêm vào vài method:

- [`hasPrevious()`][hasPrevious] và [`previous()`][previous]: để iterate theo thứ tự **giảm dần** thay vì tăng dần.
- [`nextIndex()`][nextIndex] và [`previousIndex()`][previousIndex]: để lấy index của phần tử sẽ được trả về bởi lời gọi [`next()`][liNext] tiếp theo, hoặc lời gọi [`previous()`][previous] tiếp theo.
- [`add(element)`][liAdd]: chèn phần tử cho trước vào list. Nó được chèn ngay **trước** phần tử sẽ được trả về bởi lời gọi [`next()`][liNext] tiếp theo (nếu có), và **sau** phần tử được trả về bởi lời gọi [`previous()`][previous] (nếu có). Nếu list rỗng thì phần tử đơn giản được thêm vào list. Việc chèn này có hai hệ quả. Thứ nhất, lời gọi [`previous()`][previous] tiếp theo sẽ trả về phần tử vừa chèn; lời gọi [`next()`][liNext] tiếp theo không bị ảnh hưởng. Thứ hai, giá trị trả về bởi lời gọi [`nextIndex()`][nextIndex] hoặc [`previousIndex()`][previousIndex] tiếp theo tăng thêm một.
- [`set(element)`][liSet]: cập nhật phần tử cuối cùng được trả về bởi [`next()`][liNext] hoặc [`previous()`][previous]. Nếu chưa method nào trong hai method đó được gọi trên iterator này thì [`IllegalStateException`][IllegalStateException] sẽ được raise.

Xem method [`set()`][liSet] hoạt động:

```java
List<String> numbers = Arrays.asList("one", "two", "three");
for (ListIterator<String> iterator = numbers.listIterator(); iterator.hasNext();) {
    String nextElement = iterator.next();
    if (Objects.equals(nextElement, "two")) {
        iterator.set("2");
    }
}
IO.println("numbers = " + numbers);
```

Kết quả:

```text
numbers = [one, 2, three]
```

## Thực hành các phép toán trên List

### Tạo và điền dữ liệu vào một List

Bạn tạo list và thêm phần tử theo pattern sau. Lưu ý bạn sẽ thấy thêm nhiều pattern nữa trong các ví dụ sau.

```java
List<String> fruits = new ArrayList<>();
fruits.add("apple");
fruits.add("banana");
fruits.add("cherry");
fruits.add("date");
IO.println("Fruits: " + fruits);
```

Kết quả:

```text
Fruits: [apple, banana, cherry, date]
```

### Truy cập phần tử đầu và cuối của một List

List cho bạn truy cập trực tiếp phần tử đầu và cuối.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Accessing the first and last element
IO.println("First element: " + fruits.getFirst());
IO.println("Last element:  " + fruits.getLast());

// Modifying the first and last element
IO.println("Adding apricot at the beginning of the list");
fruits.addFirst("apricot");
IO.println("Adding mango at the end of the list");
fruits.addLast("mango");
IO.println("First element: " + fruits.getFirst());
IO.println("Last element:  " + fruits.getLast());
```

Kết quả:

```text
First element: apple
Last element:  date
Adding apricot at the beginning of the list
Adding mango at the end of the list
First element: apricot
Last element:  mango
```

### Truy cập một phần tử theo index

List cho bạn truy cập phần tử bằng index, như ví dụ sau.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Accessing elements by index
IO.println("Element at index 0: " + fruits.get(0));
IO.println("Element at index 1: " + fruits.get(1));
IO.println("Last element: " + fruits.get(fruits.size() - 1));

// Insert at specific position
fruits.add(1, "blueberry");
IO.println("After inserting blueberry at index 1: " + fruits);

// Replace element
fruits.set(2, "blackberry");
IO.println("After replacing index 2 with blackberry: " + fruits);
```

Kết quả:

```text
Element at index 0: apple
Element at index 1: banana
Last element: date
After inserting blueberry at index 1: [apple, blueberry, banana, cherry, date]
After replacing index 2 with blackberry: [apple, blueberry, blackberry, cherry, date]
```

Nếu phần tử bạn tìm xuất hiện nhiều lần trong list, bạn có thể dùng pattern sau để tìm tất cả.

```java
var fruits = List.of("apple", "banana", "cherry", "banana", "banana", "apricot");

// It gives you the first index
var index = fruits.indexOf("banana");
var nextIndex = 0;
IO.println("First banana is at index " + index);
while (nextIndex != -1) {
   // search again, starting at index + 1
   nextIndex = fruits.subList(index + 1, fruits.size()).indexOf("banana");
   if (nextIndex != -1) {
      index = index + 1 + nextIndex;
      IO.println("Next banana is at index " + index);
   } else {
      IO.println("No more banana");
   }
}
```

Kết quả:

```text
First banana is at index 1
Next banana is at index 3
Next banana is at index 4
No more banana
```

### Làm việc với index của một phần tử

Bạn có thể tìm index của một phần tử cho trước trong list, như ví dụ sau.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Finding indexes
IO.println("Index of 'cherry': " + fruits.indexOf("cherry"));
IO.println("Index of 'grape' (not found): " + fruits.indexOf("grape"));

// Remove elements by index
fruits.remove(0);  // Remove by index
IO.println("After removals: " + fruits);
```

Kết quả:

```text
Index of 'cherry': 2
Index of 'grape' (not found): -1
After removals: [banana, cherry, date]
```

### Làm việc với sublist

Bạn có thể lấy một sublist từ một list. Lưu ý sublist này là một **view có thể sửa đổi** trên list gốc.

```java
var fruits = List.of("apple", "banana", "cherry", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

// Getting a sublist
var middleFruits = fruits.subList(1, 4);
IO.println("Sublist (indices 1-3): " + middleFruits);

// Adding an element in a sublist
middleFruits.add("apricot");
IO.println("Middle fruits: " + middleFruits);
IO.println("A sublist is a modifiable view on the original list");
IO.println("Fruits: " + fruits);

middleFruits.clear();
IO.println("Fruits after clearing the sublist: " + fruits);
```

Kết quả:

```text
Sublist (indices 1-3): [banana, cherry, date]
Middle fruits: [banana, cherry, date, apricot]
A sublist is a modifiable view on the original list
Fruits: [apple, banana, cherry, date, apricot]
Fruits after clearing the sublist: [apple]
```

### Sắp xếp một List

Bạn sắp xếp một list bằng cách truyền vào một [`Comparator`][Comparator].

```java
var fruits = List.of("peach", "plum", "cherry", "apple", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

fruits.sort(Comparator.naturalOrder());
IO.println("Fruits, sorted ascending order: " + fruits);

fruits.sort(Comparator.<String>naturalOrder().reversed());
IO.println("Fruits, sorted descending order: " + fruits);
```

Kết quả:

```text
Fruits, sorted ascending order: [apple, cherry, date, peach, plum]
Fruits, sorted descending order: [plum, peach, date, cherry, apple]
```

### Đảo ngược một List

Bạn có thể xem một list theo thứ tự ngược.

```java
var fruits = List.of("peach", "plum", "cherry", "apple", "date");
// make the list modifiable
fruits = new ArrayList<>(fruits);

IO.println("Original order: " + fruits);
var reversed = fruits.reversed();
IO.println("Reverse order: " + reversed);
IO.println("Adding an apricot at index 2");
fruits.add(2, "apricot");
IO.println("Original order: " + fruits);
IO.println("Reverse order: " + reversed);
```

Kết quả như sau. Nhớ rằng cái mà [`List.reversed()`][reversed] trả về là một **view** trên list gốc.

```text
Original order: [peach, plum, cherry, apple, date]
Reverse order: [date, apple, cherry, plum, peach]
Adding an apricot at index 2
Original order: [peach, plum, apricot, cherry, apple, date]
Reverse order: [date, apple, cherry, apricot, plum, peach]
```

---

**Bài tập**

1. `subList` là view. Viết một ví dụ trong đó bạn *tưởng* mình chỉ sửa sublist nhưng lại làm hỏng list gốc. Đây là cạm bẫy hay gặp khi truyền sublist ra ngoài method.
2. `Arrays.asList("one","two","three")` — thử `add()` vào nó. Giải thích exception bạn nhận được (gợi ý: kích thước cố định, nhưng `set()` lại được).
3. Dùng `ListIterator` viết một method chèn `"và"` trước phần tử cuối của một `List<String>`.
4. Đối chiếu: PHP `array_slice` trả về copy hay view? Điều đó khiến bug ở bài tập 1 khó xảy ra hơn ở PHP như thế nào?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[ArrayList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html
[LinkedList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html
[ArrayDeque]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayDeque.html
[Iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html
[ListIterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html
[Comparable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html
[Comparator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html
[naturalOrder]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html#naturalOrder()
[CollectionsSort]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#sort(java.util.List)
[addIdx]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#add(int,E)
[get]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#get(int)
[set]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#set(int,E)
[removeIdx]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#remove(int)
[indexOf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#indexOf(java.lang.Object)
[lastIndexOf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#lastIndexOf(java.lang.Object)
[subList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#subList(int,int)
[addAllIdx]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#addAll(int,java.util.Collection)
[sort]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#sort(java.util.Comparator)
[listIterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#listIterator()
[reversed]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SequencedCollection.html#reversed()
[hasPrevious]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#hasPrevious()
[previous]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previous()
[liNext]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#next()
[nextIndex]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#nextIndex()
[previousIndex]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#previousIndex()
[liAdd]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#add(E)
[liSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ListIterator.html#set(E)
[IndexOutOfBoundsException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IndexOutOfBoundsException.html
[IllegalStateException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalStateException.html
[ClassCastException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html
