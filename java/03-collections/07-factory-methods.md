# Tạo và xử lý dữ liệu với các factory method của Collections

> Dịch từ [Creating and Processing Data with the Collections Factory Methods](https://dev.java/learn/api/collections-framework/factory-methods/) — dev.java.

## Tạo collection không thể sửa đổi (unmodifiable)

Java SE 9 thêm một nhóm factory method vào interface [`List`][List] và [`Set`][Set] để tạo list và set. Pattern rất đơn giản: chỉ cần gọi static method [`List.of()`][ListOf] hoặc [`Set.of()`][SetOf], truyền vào các phần tử, thế là xong.

```java
List<String> stringList = List.of("one", "two", "three");
IO.println("String list: " + stringList);
Set<String> stringSet = Set.of("one", "two", "three");
IO.println("String set : " + stringSet);
```

Kết quả:

```text
String list: [one, two, three]
String set : [one, three, two]
```

Có mấy điểm đáng lưu ý:

- Implementation bạn nhận về **có thể khác nhau** tùy theo số phần tử bạn đưa vào list hay set. Không cái nào là [`ArrayList`][ArrayList] hay [`HashSet`][HashSet]; code của bạn không nên dựa vào bất cứ gì ngoài interface [`List`][List] và [`Set`][Set] cơ bản.
- Cả list và set bạn nhận được đều là cấu trúc **unmodifiable**. Bạn không thể thêm hay sửa phần tử trong chúng, và không thể sửa các phần tử đó. Nếu bản thân các object trong cấu trúc là mutable, bạn vẫn thay đổi được nội dung của chúng.
- Các cấu trúc này **không chấp nhận giá trị null**. Nếu bạn thử thêm `null` vào một list/set như vậy, bạn sẽ nhận exception.
- Interface [`Set`][Set] không cho phép trùng lặp: đó là bản chất của set. Vì việc tạo một set với giá trị trùng lặp là vô nghĩa, người ta cho rằng viết code như vậy là bug. Nên bạn sẽ nhận exception nếu thử.
- Các implementation bạn nhận được đều [`Serializable`][Serializable].

Các method `of()` này thường được gọi là *convenience factory methods for collections*.

## Lấy một bản copy unmodifiable của collection

Nối tiếp thành công của các convenience factory method, Java SE 10 thêm một nhóm method nữa để tạo **bản copy unmodifiable** của collection.

Có hai method: [`List.copyOf()`][ListCopyOf] và [`Set.copyOf()`][SetCopyOf]. Cả hai theo cùng một pattern:

```java
Collection<String> strings = Arrays.asList("one", "two", "three");

List<String> list = List.copyOf(strings);
IO.println("List: "  + list);
Set<String> set   = Set.copyOf(strings);
IO.println("Set:  "  + set);
```

Kết quả:

```text
List: [one, two, three]
Set:  [two, one, three]
```

Trong mọi trường hợp, collection bạn cần copy **không được** null và **không được** chứa phần tử null nào. Nếu collection này có phần tử trùng lặp, chỉ một trong số đó được giữ lại trong trường hợp [`Set.copyOf()`][SetCopyOf].

Cái bạn nhận về là một **bản copy** unmodifiable của collection truyền vào. Nên việc sửa đổi collection gốc sẽ **không** phản ánh vào list/set bạn nhận được.

Không implementation nào trong số đó chấp nhận giá trị `null`. Nếu bạn thử copy một collection có giá trị `null`, bạn sẽ nhận [`NullPointerException`][NullPointerException].

## Bọc một array trong một List

Collections Framework có một class tên [`Arrays`][Arrays] với khoảng 200 method để xử lý array. Phần lớn hiện thực các thuật toán khác nhau trên array như sort, merge, search, và không được nói tới trong phần này.

Nhưng có một method đáng nhắc tới: [`Arrays.asList()`][asList]. Method này nhận một vararg làm tham số và trả về một [`List`][List] gồm các phần tử bạn truyền vào, giữ nguyên thứ tự. Method này không thuộc nhóm *convenience factory methods for collections* nhưng vẫn rất hữu ích.

[`List`][List] này hoạt động như một **wrapper trên một array**, và hành xử theo đúng cách của array — điều này thoạt đầu có thể gây bối rối. Một khi bạn đã đặt kích thước cho array, bạn không thể đổi nó. Nghĩa là bạn không thể thêm phần tử vào một array đã có, cũng không thể xóa phần tử khỏi nó. Tất cả những gì bạn làm được là **thay thế** một phần tử bằng một phần tử khác, có thể là null.

[`List`][List] bạn nhận được khi gọi [`Arrays.asList()`][asList] làm đúng như vậy:

- Nếu bạn thử thêm hoặc xóa phần tử, bạn sẽ nhận [`UnsupportedOperationException`][UnsupportedOperationException], dù bạn làm trực tiếp hay qua iterator.
- Thay thế phần tử đã có thì **được**.

Vậy list này không phải unmodifiable, nhưng có hạn chế về cách bạn thay đổi nó.

## Dùng factory class Collections để xử lý một collection

Collections Framework còn có một factory class nữa: [`Collections`][Collections], với một loạt method để thao tác collection và nội dung của chúng. Class này có khoảng 70 method, xem từng cái một sẽ rất mệt, nên ta chỉ trình bày một phần.

### Trích min hoặc max từ một collection

Class [`Collections`][Collections] cho bạn hai method: [`min()`][min] và [`max()`][max]. Cả hai nhận collection làm tham số để trích min/max. Cả hai đều có overload nhận thêm một comparator.

Nếu không có comparator được cung cấp thì phần tử của collection **phải** implement [`Comparable`][Comparable]. Nếu không, [`ClassCastException`][ClassCastException] sẽ được raise. Nếu có comparator, nó sẽ được dùng để lấy min/max, dù phần tử có comparable hay không.

Lấy min/max của một collection rỗng bằng method này sẽ raise [`NoSuchElementException`][NoSuchElementException].

### Tìm một sublist trong một list

Hai method định vị một sublist cho trước trong một list lớn hơn:

- [`indexOfSubList(List<?> source, List<?> target)`][indexOfSubList]: trả về index đầu tiên của phần tử đầu tiên của list `target` trong list `source`, hoặc -1 nếu không tồn tại;
- [`lastIndexOfSubList(List<?> source, List<?> target)`][lastIndexOfSubList]: trả về index cuối cùng trong số đó.

### Thay đổi thứ tự phần tử của một list

Nhiều method có thể thay đổi thứ tự phần tử của một list:

- [`sort()`][CollSort] sắp xếp list **tại chỗ** (in place). Method này có thể nhận một comparator. Như thường lệ, nếu không có comparator thì phần tử của list phải comparable. Từ Java SE 8, bạn nên ưu tiên method [`sort()`][ListSort] của interface [`List`][List].
- [`shuffle()`][shuffle] xáo trộn ngẫu nhiên các phần tử của list. Bạn có thể cung cấp instance [`Random`][Random] của mình nếu cần một phép xáo trộn ngẫu nhiên **lặp lại được**.
- [`rotate()`][rotate] xoay các phần tử của list. Sau một phép xoay, phần tử ở index 0 sẽ nằm ở index 1, và tiếp tục như vậy. Phần tử cuối sẽ được chuyển lên đầu list. Bạn có thể kết hợp [`subList()`][subList] và [`rotate()`][rotate] để xóa một phần tử ở index cho trước và chèn nó vào chỗ khác trong list:

```java
List<String> strings = Arrays.asList("0", "1", "2", "3", "4");
IO.println(strings);
int fromIndex = 1;
int toIndex = 4;
Collections.rotate(strings.subList(fromIndex, toIndex), -1);
IO.println(strings);
```

Kết quả:

```text
[0, 1, 2, 3, 4]
[0, 2, 3, 1, 4]
```

Phần tử ở index `fromIndex` đã bị lấy ra khỏi chỗ của nó, list được tổ chức lại tương ứng, và phần tử đó được chèn vào index `toIndex - 1`.

- [`reverse()`][reverse]: đảo thứ tự phần tử của list.
- [`swap()`][swap]: đổi chỗ hai phần tử trong list.

### Bọc một collection trong một collection unmodifiable

Factory class [`Collections`][Collections] cho bạn nhiều method để tạo wrapper unmodifiable cho collection hay map của bạn. Nội dung của cấu trúc **không bị nhân bản**; cái bạn nhận được là một wrapper quanh cấu trúc gốc. Mọi cố gắng sửa đổi nó sẽ raise exception.

Tất cả các method này bắt đầu bằng `unmodifiable`, theo sau là tên kiểu cấu trúc. Ví dụ, để tạo wrapper unmodifiable cho một list:

```java
List<String> strings = Arrays.asList("0", "1", "2", "3", "4");
IO.println("Strings: " + strings);
List<String> unmodifiableStrings = Collections.unmodifiableList(strings);
IO.println("Unmodifiable strings: " + strings);
```

Kết quả:

```text
Strings: [0, 1, 2, 3, 4]
Unmodifiable strings: [0, 1, 2, 3, 4]
```

Một lời cảnh báo: bạn không sửa được collection mà các factory method này trả về. Nhưng wrapper này được **hậu thuẫn (backed)** bởi collection bạn đã truyền vào. Nên nếu collection đó modifiable và bạn sửa nó, thay đổi đó **sẽ phản ánh** vào wrapper. Xem đoạn code sau:

```java
List<String> strings = new ArrayList<>(Arrays.asList("0", "1", "2", "3", "4"));
List<String> unmodifiableStrings = Collections.unmodifiableList(strings);
IO.println(unmodifiableStrings);
strings.add("5");
IO.println(unmodifiableStrings);
```

Kết quả:

```text
[0, 1, 2, 3, 4]
[0, 1, 2, 3, 4, 5]
```

Nếu bạn định tạo một collection unmodifiable theo pattern này, **copy phòng thủ (defensive copy)** trước có thể là biện pháp an toàn.

### Bọc một collection trong một collection synchronized

Cũng như bạn tạo được wrapper unmodifiable cho map và collection, factory class [`Collections`][Collections] có thể tạo wrapper **synchronized** cho chúng. Quy ước đặt tên giống như với unmodifiable: các method có tên `synchronized` theo sau là [`Collection`][Collection], [`List`][List], [`Set`][Set], v.v.

Có hai điều bắt buộc phải tuân theo:

- Mọi truy cập tới collection của bạn **phải** đi qua wrapper bạn nhận được.
- Việc đi qua collection bằng iterator hoặc stream phải được synchronize **bởi code gọi**, trên chính list đó.

Không tuân theo các quy tắc này sẽ khiến code của bạn phơi ra race condition.

Việc synchronize collection bằng các factory method của [`Collections`][Collections] có thể không phải lựa chọn tốt nhất. Framework Java Util Concurrent (package [`java.util.concurrent`][juc]) có những giải pháp tốt hơn.

---

**Bài tập**

1. `List.of("a", null)` — chạy thử. Exception gì? So sánh với `Arrays.asList("a", null)`. Vì sao hai cái khác nhau?
2. Chứng minh bằng code rằng `Collections.unmodifiableList` **không** bảo vệ bạn nếu bạn còn giữ tham chiếu tới list gốc. Rồi viết lại theo cách an toàn bằng `List.copyOf`.
3. `List.of(...)` trả về "unmodifiable" nhưng nếu phần tử là object mutable thì sao? Viết ví dụ chứng minh nội dung vẫn thay đổi được.
4. Đối chiếu: Go không có "unmodifiable slice". Người viết library Go bảo vệ dữ liệu bằng cách nào? (Gợi ý: copy khi trả về.)

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[Set]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html
[ArrayList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html
[HashSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html
[Arrays]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Arrays.html
[Collections]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html
[Comparable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html
[Random]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Random.html
[Serializable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/io/Serializable.html
[juc]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/package-summary.html
[ListOf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#of(E...)
[SetOf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html#of(E...)
[ListCopyOf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#copyOf(java.util.Collection)
[SetCopyOf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html#copyOf(java.util.Collection)
[asList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Arrays.html#asList(T...)
[min]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#min(java.util.Collection)
[max]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#max(java.util.Collection)
[indexOfSubList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#indexOfSubList(java.util.List,java.util.List)
[lastIndexOfSubList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#lastIndexOfSubList(java.util.List,java.util.List)
[CollSort]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#sort(java.util.List)
[ListSort]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#sort(java.util.Comparator)
[shuffle]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#shuffle(java.util.List)
[rotate]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#rotate(java.util.List,int)
[subList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html#subList(int,int)
[reverse]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#reverse(java.util.List)
[swap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collections.html#swap(java.util.List,int,int)
[NullPointerException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/NullPointerException.html
[UnsupportedOperationException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/UnsupportedOperationException.html
[ClassCastException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html
[NoSuchElementException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html
