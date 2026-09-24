# Mở rộng Collection với Set, SortedSet và NavigableSet

> Dịch từ [Extending Collection with Set, SortedSet and NavigableSet](https://dev.java/learn/api/collections-framework/sets/) — dev.java.

## Khám phá interface Set

Interface [`Set`][Set] **không** mang thêm method nào cho interface [`Collection`][Collection]. Implementation chính của [`Set`][Set] mà Collections Framework cho bạn là class [`HashSet`][HashSet]. Bên trong, [`HashSet`][HashSet] bọc một instance của [`HashMap`][HashMap] — class sẽ được nói tới sau — đóng vai trò delegate cho [`HashSet`][HashSet].

Như bạn đã thấy, điều [`Set`][Set] mang lại cho [`Collection`][Collection] là nó **cấm phần tử trùng lặp**. Điều bạn **mất** so với interface [`List`][List] là phần tử của bạn được lưu **không theo thứ tự cụ thể** nào. Rất ít khả năng bạn iterate qua chúng theo đúng thứ tự bạn đã thêm vào set.

Xem ví dụ sau:

```java
List<String> strings = List.of("one", "two", "three", "four", "five", "six");
Set<String> set = new HashSet<>();
set.addAll(strings);
set.forEach(IO::println);
```

Kết quả:

```text
six
four
one
two
three
five
```

Một số implementation của [`Set`][Set] luôn cho bạn cùng một thứ tự khi iterate, nhưng vì điều đó **không được bảo đảm**, code của bạn không nên dựa vào nó.

Nếu bạn muốn iterate theo một thứ tự cụ thể, tái lập được, hãy dùng implementation [`LinkedHashSet`][LinkedHashSet] — nó kết hợp một set với một linked list nội bộ.

## Mở rộng Set với SortedSet

Phần mở rộng đầu tiên của [`Set`][Set] là interface [`SortedSet`][SortedSet]. [`SortedSet`][SortedSet] giữ các phần tử được sắp xếp theo một logic so sánh nhất định. Collections Framework cho bạn một implementation của [`SortedSet`][SortedSet], gọi là [`TreeSet`][TreeSet].

[`TreeSet`][TreeSet] là implementation cần **so sánh** các object nó chứa. Bạn có thể cung cấp một [`Comparator`][Comparator] khi khởi tạo [`TreeSet`][TreeSet], hoặc bạn implement interface [`Comparable`][Comparable] cho các phần tử bạn đưa vào [`TreeSet`][TreeSet]. Nếu bạn làm cả hai, [`Comparator`][Comparator] được ưu tiên.

Interface [`SortedSet`][SortedSet] thêm method mới vào [`Set`][Set]:

- [`first()`][first] và [`last()`][last] trả về phần tử nhỏ nhất và lớn nhất của set.
- [`headSet(toElement)`][headSet] và [`tailSet(fromElement)`][tailSet] trả về các subset chứa những phần tử nhỏ hơn `toElement`, hoặc lớn hơn hay bằng `fromElement`.
- [`subSet(fromElement, toElement)`][subSet] cho bạn subset gồm các phần tử giữa `fromElement` và `toElement`.

`toElement` và `fromElement` **không cần** là phần tử của set chính. Nếu chúng là phần tử của set thì `toElement` **không** được bao gồm trong kết quả, còn `fromElement` **có** — theo quy ước thông thường.

Xem ví dụ sau:

```java
SortedSet<String> strings = new TreeSet<>(Set.of("a", "b", "c", "d", "e", "f"));
SortedSet<String> subSet = strings.subSet("aa", "d");
IO.println("sub set = " + subSet);
```

Kết quả:

```text
sub set = [b, c]
```

Ba subset mà các method này trả về đều là **view** trên set chính. Không có bản copy nào được tạo, nghĩa là mọi thay đổi bạn làm trên các subset này sẽ phản ánh lên set, và ngược lại.

Bạn có thể xóa hoặc thêm phần tử vào set chính thông qua các subset này. Nhưng có một điểm cần ghi nhớ: ba subset này **nhớ giới hạn** mà chúng được tạo ra. Vì lý do nhất quán, việc thêm một phần tử **ngoài giới hạn** thông qua subset là không hợp lệ. Ví dụ, nếu bạn lấy một [`headSet`][headSetSS] và thử thêm một phần tử lớn hơn hay bằng `toElement`, bạn sẽ nhận [`IllegalArgumentException`][IllegalArgumentException].

## Mở rộng SortedSet với NavigableSet

Java SE 6 giới thiệu một phần mở rộng của [`SortedSet`][SortedSet] với nhiều method hơn. Hóa ra class [`TreeSet`][TreeSet] đã được sửa lại để implement [`NavigableSet`][NavigableSet]. Nên bạn dùng **cùng một class** cho cả hai interface.

Một số method được overload bởi [`NavigableSet`][NavigableSet]:

- [`headSet()`][nsHeadSet], [`tailSet()`][nsTailSet] và [`subSet()`][nsSubSet] có thể nhận thêm một tham số `boolean` để chỉ định giới hạn (`toElement` hoặc `fromElement`) có được bao gồm trong subset kết quả hay không.

Các method được thêm mới:

- [`ceiling(element)`][ceiling] và [`floor(element)`][floor] trả về phần tử nhỏ nhất **lớn hơn hoặc bằng**, hoặc phần tử lớn nhất **nhỏ hơn hoặc bằng** `element` cho trước. Nếu không có phần tử nào như vậy thì trả về `null`.
- [`lower(element)`][lower] và [`higher(element)`][higher] trả về phần tử lớn nhất **nhỏ hơn hẳn**, hoặc phần tử nhỏ nhất **lớn hơn hẳn** `element` cho trước. Nếu không có thì trả về `null`.
- [`pollFirst()`][pollFirst] và [`pollLast()`][pollLast] trả về **và xóa** phần tử nhỏ nhất hoặc lớn nhất của set.

Hơn nữa, [`NavigableSet`][NavigableSet] cũng cho phép bạn iterate theo **thứ tự giảm dần**. Có hai cách:

- Gọi [`descendingIterator()`][descendingIterator]: cho bạn một [`Iterator`][Iterator] thường đi qua set theo thứ tự giảm dần.
- Gọi [`descendingSet()`][descendingSet]: bạn nhận về một [`NavigableSet`][NavigableSet] khác, là một **view** trên set này, khiến bạn tưởng như đang có cùng set đó nhưng sắp theo thứ tự đảo.

Ví dụ minh họa:

```java
NavigableSet<String> sortedStrings = new TreeSet<>(Set.of("a", "b", "c", "d", "e", "f"));
IO.println("sorted strings = " + sortedStrings);
NavigableSet<String> reversedStrings = sortedStrings.descendingSet();
IO.println("reversed strings = " + reversedStrings);
```

Kết quả:

```text
sorted strings = [a, b, c, d, e, f]
reversed strings = [f, e, d, c, b, a]
```

---

**Bài tập**

1. Tạo một class `NgonNgu(String ten, int nam)` **không** override `equals`/`hashCode`, đưa hai instance giống hệt nhau vào `HashSet`. Có mấy phần tử? Sau đó override rồi thử lại. Đây là cạm bẫy `Set` số một.
2. Với `TreeSet<NgonNgu>` mà `NgonNgu` không implement `Comparable` và bạn không truyền `Comparator`: exception nào xảy ra, và ở thời điểm nào (compile hay runtime)?
3. Lấy `headSet("d")` từ một `TreeSet<String>` rồi thử `add("z")`. Giải thích exception theo đúng lý do "nhất quán về giới hạn" ở trên.
4. Đối chiếu ba lựa chọn: `HashSet` (không thứ tự), `LinkedHashSet` (thứ tự thêm vào), `TreeSet` (thứ tự sắp xếp). Với mỗi cái, nêu một use case thật.

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[Set]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html
[SortedSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html
[NavigableSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html
[HashSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html
[LinkedHashSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedHashSet.html
[TreeSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html
[HashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashMap.html
[Iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html
[Comparable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html
[Comparator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html
[first]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#first()
[last]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#last()
[headSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#headSet(E)
[tailSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#tailSet(E)
[subSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeSet.html#subSet(E,E)
[headSetSS]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#headSet(E)
[nsHeadSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#headSet(E,boolean)
[nsTailSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#tailSet(E,boolean)
[nsSubSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#subSet(E,boolean,E,boolean)
[ceiling]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#ceiling(E)
[floor]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#floor(E)
[lower]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#lower(E)
[higher]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#higher(E)
[pollFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#pollFirst()
[pollLast]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#pollLast()
[descendingIterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#descendingIterator()
[descendingSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html#descendingSet()
[IllegalArgumentException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalArgumentException.html
