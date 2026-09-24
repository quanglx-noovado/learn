# Lưu phần tử trong một Collection

> Dịch từ [Storing Elements in a Collection](https://dev.java/learn/api/collections-framework/collection-interface/) — dev.java.

## Khám phá interface Collection

Interface đầu tiên bạn cần biết là [`Collection`][Collection]. Nó mô hình hóa một collection thuần — có thể lưu phần tử và cho bạn nhiều cách khác nhau để lấy chúng ra.

Nếu muốn chạy các ví dụ trong phần này, bạn cần biết cách tạo một collection. Ta chưa nói về class [`ArrayList`][ArrayList], sẽ nói sau.

## Các method xử lý từng phần tử riêng lẻ

Bắt đầu bằng việc lưu và xóa một phần tử khỏi collection. Hai method liên quan là [`add()`][add] và [`remove()`][remove].

- [`add(element)`][add]: thêm một phần tử vào collection. Method này trả về `boolean`, giá trị `false` nếu thao tác thất bại. Khái niệm "thất bại" ở đây khá tinh tế: khi method này return — dù `true` hay `false` — thì phần tử đó **phải** đang ở trong collection. Nghĩa là gọi [`contains()`][contains] với phần tử đó làm tham số phải trả về `true`. Vậy nếu implementation của bạn quyết định **không** thêm một phần tử chưa có trong [`Collection`][Collection] này, bạn nên throw exception. Javadoc của [`add(element)`][add] chỉ rõ những exception bạn nên throw:
  - Nếu implementation của bạn không cho phép sửa đổi (non-modifiable), exception phải là [`UnsupportedOperationException`][UnsupportedOperationException].
  - Nếu nó không cho phép giá trị null, phải là [`NullPointerException`][NullPointerException].
  - Nếu phần tử không thêm được vì sai kiểu, phải throw [`ClassCastException`][ClassCastException].
  - Nếu implementation của bạn từ chối phần tử này dựa trên thuộc tính của nó, bạn nên throw [`IllegalArgumentException`][IllegalArgumentException].
- [`remove(element)`][remove]: xóa phần tử cho trước khỏi collection. Method này cũng trả về `boolean`, vì thao tác có thể thất bại. Ví dụ, remove thất bại khi phần tử cần xóa không có trong collection.

Bạn có thể chạy ví dụ sau. Ở đây bạn tạo một instance của interface [`Collection`][Collection] bằng implementation [`ArrayList`][ArrayList]. Generics được dùng nói cho Java compiler biết bạn muốn lưu các object [`String`][String] trong collection này. [`ArrayList`][ArrayList] không phải implementation duy nhất của [`Collection`][Collection] mà bạn có thể dùng. Chi tiết sau.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
IO.println("strings = " + strings);
strings.remove("one");
IO.println("strings = " + strings);
```

Chạy code trên sẽ in ra:

```text
strings = [one, two]
strings = [two]
```

Bạn kiểm tra sự tồn tại của một phần tử trong collection bằng method [`contains()`][contains]. Lưu ý là bạn kiểm tra được **bất kỳ kiểu** phần tử nào. Ví dụ, kiểm tra sự tồn tại của một object `User` trong một collection chứa [`String`][String] là hợp lệ. Nghe có vẻ lạ, vì không có cơ hội nào để phép kiểm tra này trả về `true`, nhưng compiler cho phép. Nếu bạn dùng IDE để thử code này, IDE có thể cảnh báo. Cũng lưu ý implementation có thể chọn throw [`ClassCastException`][ClassCastException].

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
if (strings.contains("one")) {
    IO.println("one is here");
}
if (!strings.contains("three")) {
    IO.println("three is not here");
}

record User(String name) {}

User rebecca = new User("Rebecca");
if (!strings.contains(rebecca)) {
    IO.println("Rebecca is not here");
}
```

Chạy code này cho ra:

```text
one is here
three is not here
Rebecca is not here
```

## Các method xử lý collection khác

Nhóm method đầu tiên bạn đã thấy cho phép xử lý từng phần tử. Cũng có các method nhận vào một [`Collection`][Collection] khác làm tham số.

Có bốn method như vậy: [`containsAll()`][containsAll], [`addAll()`][addAll], [`removeAll()`][removeAll] và [`retainAll()`][retainAll]. Chúng định nghĩa bốn phép toán cơ bản trên một tập hợp object.

- [`containsAll()`][containsAll]: định nghĩa phép bao hàm (inclusion).
- [`addAll()`][addAll]: định nghĩa phép hợp (union).
- [`removeAll()`][removeAll]: định nghĩa phép bù (complement).
- [`retainAll()`][retainAll]: định nghĩa phép giao (intersection).

Cái đầu rất đơn giản: [`containsAll()`][containsAll] nhận một collection khác làm tham số và trả về `true` nếu **tất cả** phần tử của collection kia đều có trong collection này. Collection truyền vào không nhất thiết cùng kiểu với collection này: hỏi xem một collection [`String`][String] kiểu `Collection<String>` có nằm trong một collection `User` kiểu `Collection<User>` là hợp lệ. Kết quả còn có thể là `true` nếu collection `String` rỗng.

Lưu ý implementation của [`containsAll()`][containsAll] có thể throw exception trong các trường hợp sau:

- [`ClassCastException`][ClassCastException] nếu một phần tử của collection kia không tương thích với collection này.
- [`NullPointerException`][NullPointerException] nếu một phần tử của collection kia là `null` mà collection này không cho phép phần tử `null`.
- Cũng có thể [`NullPointerException`][NullPointerException] nếu bản thân collection kia là `null`.

Ví dụ dùng method này:

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Collection<String> first = new ArrayList<>();
first.add("one");
first.add("two");

Collection<String> second = new ArrayList<>();
second.add("one");
second.add("four");

IO.println("Is first contained in strings? " + strings.containsAll(first));
IO.println("Is second contained in strings? " + strings.containsAll(second));
```

Chạy code này cho ra:

```text
Is first contained in strings? true
Is second contained in strings? false
```

Cái thứ hai là [`addAll()`][addAll]. Nó cho phép thêm tất cả phần tử của một collection cho trước vào collection này. Cũng như method [`add()`][add], việc này có thể thất bại với một số phần tử trong một số trường hợp. Method này trả về `true` nếu collection này **đã bị thay đổi** bởi lời gọi đó. Đây là điểm quan trọng cần hiểu: nhận được `true` **không** có nghĩa là tất cả phần tử của collection kia đã được thêm vào; nó chỉ có nghĩa là ít nhất một phần tử đã được thêm.

Xem [`addAll()`][addAll] hoạt động:

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

Collection<String> first = new ArrayList<>();
first.add("one");
first.add("four");

boolean hasChanged = strings.addAll(first);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Kết quả:

```text
Has strings changed? true
strings = [one, two, three, one, four]
```

Bạn cần biết rằng chạy code này sẽ cho kết quả **khác** nếu bạn đổi implementation của [`Collection`][Collection]. Kết quả trên đúng với [`ArrayList`][ArrayList], nhưng như ví dụ sau cho thấy, với [`HashSet`][HashSet] thì không. Bạn sẽ học thêm về [`Set`][Set] ở bài [Mở rộng Collection với Set, SortedSet và NavigableSet](06-set-sortedset-navigableset.md).

```java
Collection<String> strings = new HashSet<>();
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

Collection<String> first = new ArrayList<>();
first.add("one");
first.add("four");

boolean hasChanged = strings.addAll(first);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Kết quả:

```text
Has strings changed? false
strings = [four, one, two, three]
```

Cái thứ ba là [`removeAll()`][removeAll]. Nó xóa tất cả phần tử của collection này có mặt trong collection kia. Giống như [`contains()`][contains] hay [`remove()`][remove], collection kia có thể được định nghĩa trên kiểu bất kỳ; không cần tương thích với kiểu của collection này.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Collection<String> toBeRemoved = new ArrayList<>();
toBeRemoved.add("one");
toBeRemoved.add("four");

boolean hasChanged = strings.removeAll(toBeRemoved);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Kết quả:

```text
Has strings changed? true
strings = [two, three]
```

Cái cuối là [`retainAll()`][retainAll]. Thao tác này chỉ **giữ lại** những phần tử của collection này có mặt trong collection kia; tất cả phần tử khác bị xóa. Lại một lần nữa, collection kia có thể ở kiểu bất kỳ.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Collection<String> toBeRetained = new ArrayList<>();
toBeRetained.add("one");
toBeRetained.add("four");

boolean hasChanged = strings.retainAll(toBeRetained);

IO.println("Has strings changed? " + hasChanged);
IO.println("strings = " + strings);
```

Kết quả:

```text
Has strings changed? true
strings = [one]
```

## Các method xử lý chính bản thân collection

Nhóm method cuối làm việc với chính collection.

Bạn có hai method để kiểm tra nội dung của collection:

- [`size()`][size]: trả về số phần tử trong collection, dưới dạng `int`.
- [`isEmpty()`][isEmpty]: cho biết collection có rỗng hay không.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
if (!strings.isEmpty()) {
    IO.println("Indeed strings is not empty");
}
IO.println("The number of elements in strings is " + strings.size());
```

Kết quả:

```text
Indeed strings is not empty
The number of elements in strings is 2
```

Bạn cũng có thể xóa sạch nội dung của collection bằng cách gọi [`clear()`][clear] trên nó.

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
IO.println("The number of elements in strings is " + strings.size());
strings.clear();
IO.println("After clearing it, this number is now " + strings.size());
```

Kết quả:

```text
The number of elements in strings is 2
After clearing it, this number is now 0
```

## Lấy array các phần tử của một collection

Dù lưu phần tử trong collection thường hợp lý hơn nhét vào array, vẫn có trường hợp bạn cần lấy chúng ra dưới dạng array.

Interface [`Collection`][Collection] cho bạn ba pattern để làm việc này, dưới dạng ba overload của method [`toArray()`][toArray].

Cái đầu tiên là gọi [`toArray()`][toArray] thuần, không tham số. Nó trả về các phần tử trong một array `Object`.

Đó có thể không phải cái bạn cần. Nếu bạn có `Collection<String>`, có lẽ bạn muốn một array [`String`][String]. Bạn vẫn cast được `Object[]` sang `String[]`, nhưng không có bảo đảm nào rằng phép cast đó không fail ở runtime. Nếu bạn cần type safety, hãy dùng một trong hai method sau:

- [`toArray(T[] a)`][toArrayT] trả về một array kiểu `T`: `T[]`.
- [`toArray(IntFunction<T[]> generator)`][toArrayF] trả về cùng kiểu, với syntax khác.

Khác biệt giữa hai pattern cuối là gì? Đầu tiên là **tính dễ đọc**. Tạo một instance [`IntFunction<T[]>`][IntFunction] thoạt nhìn có vẻ lạ, nhưng viết nó bằng method reference thì cực đơn giản.

Đây là pattern thứ nhất. Ở pattern này, bạn cần truyền vào một array kiểu tương ứng.

```java
Collection<String> strings = new ArrayList<>(); // You have 4 elements in that collection
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

String[] tabString1 = strings.toArray(new String[] {}); // you can pass an empty array
IO.println("Tab string 1: " + Arrays.toString(tabString1));
String[] tabString2 = strings.toArray(new String[4]);   // or an array of the right size
IO.println("Tab string 2: " + Arrays.toString(tabString2));
```

Kết quả:

```text
Tab string 1: [one, two, three, four]
Tab string 2: [one, two, three, four]
```

Array truyền vào có tác dụng gì? Nếu nó đủ lớn để chứa tất cả phần tử của collection thì các phần tử sẽ được copy vào array đó và array đó được trả về. Nếu array còn nhiều chỗ hơn cần thiết, ô đầu tiên không dùng sẽ được đặt thành `null`. Nếu array bạn truyền vào quá nhỏ, một array mới với kích thước đúng chính xác sẽ được tạo để chứa các phần tử.

Pattern này trong thực tế:

```java
Collection<String> strings = List.of("one", "two");

String[] largerTab = {"three", "three", "three", "I", "was", "there"};
IO.println("largerTab = " + Arrays.toString(largerTab));

String[] result = strings.toArray(largerTab);
IO.println("result = " + Arrays.toString(result));

IO.println("Same arrays? " + (result == largerTab));
```

Kết quả:

```text
largerTab = [three, three, three, I, was, there]
result = [one, two, null, I, was, there]
Same arrays? true
```

Bạn thấy array đã được copy vào các ô đầu của array tham số, `null` được thêm ngay sau đó, và các phần tử cuối của array này **không bị đụng tới**. Array trả về chính là array bạn truyền vào, chỉ khác nội dung.

Ví dụ thứ hai, với một array độ dài 0:

```java
Collection<String> strings = List.of("one", "two");

String[] zeroLengthTab = {};
String[] result = strings.toArray(zeroLengthTab);

IO.println("zeroLengthTab = " + Arrays.toString(zeroLengthTab));
IO.println("result = " + Arrays.toString(result));
```

Kết quả:

```text
zeroLengthTab = []
result = [one, two]
```

Trong trường hợp này một array mới đã được tạo.

Pattern thứ hai được viết bằng constructor method reference để implement [`IntFunction<T[]>`][IntFunction]:

```java
Collection<String> strings = new ArrayList<>(); // You have 4 elements in that collection
strings.add("one");
strings.add("two");
strings.add("three");
strings.add("four");

String[] tabString3 = strings.toArray(String[]::new);
IO.println("Tab string 3: " + Arrays.toString(tabString3));
```

Kết quả:

```text
Tab string 3: [one, two, three, four]
```

Trong trường hợp đó, một array độ dài 0 với kiểu đúng được tạo bởi function này, rồi method gọi [`toArray()`][toArray] với array đó làm tham số.

Pattern code này được thêm ở JDK 8 để cải thiện tính dễ đọc của các lời gọi [`toArray()`][toArray].

## Lọc bỏ phần tử của collection bằng một Predicate

Java SE 8 thêm một tính năng mới cho interface [`Collection`][Collection]: khả năng lọc bỏ phần tử bằng một predicate.

Giả sử bạn có `List<String>` và cần xóa tất cả string null, string rỗng và string dài hơn 5 ký tự. Ở Java SE 7 và trước đó, bạn dùng method [`Iterator.remove()`][iterRemove] để làm việc đó, gọi nó trong một câu lệnh `if`. Bạn sẽ thấy pattern này cùng với interface [`Iterator`][Iterator]. Với [`removeIf()`][removeIf], code của bạn đơn giản hơn nhiều:

```java
Predicate<String> isNull = Objects::isNull;
Predicate<String> isEmpty = String::isEmpty;
Predicate<String> isNullOrEmpty = isNull.or(isEmpty);

Collection<String> strings = new ArrayList<>();
strings.add(null);
strings.add("");
strings.add("one");
strings.add("two");
strings.add("");
strings.add("three");
strings.add(null);

IO.println("strings = " + strings);
strings.removeIf(isNullOrEmpty);
IO.println("filtered strings = " + strings);
```

Kết quả:

```text
strings = [null, , one, two, , three, null]
filtered strings = [one, two, three]
```

Lại một lần nữa, dùng method này sẽ cải thiện rất nhiều tính dễ đọc và biểu cảm của code ứng dụng.

## Chọn implementation cho interface Collection

Trong tất cả các ví dụ trên, ta dùng [`ArrayList`][ArrayList] để implement interface [`Collection`][Collection].

Thực tế là: Collections Framework **không** cung cấp implementation trực tiếp cho interface [`Collection`][Collection]. [`ArrayList`][ArrayList] implement [`List`][List], và vì [`List`][List] extends [`Collection`][Collection] nên nó cũng implement [`Collection`][Collection].

Nếu bạn quyết định dùng interface [`Collection`][Collection] để mô hình hóa các collection trong ứng dụng, thì chọn [`ArrayList`][ArrayList] làm implementation mặc định là lựa chọn tốt nhất, trong phần lớn trường hợp. Bạn sẽ thấy thêm thảo luận về việc chọn implementation đúng ở phần sau của tutorial này.

---

**Bài tập**

1. `addAll()` trả về `true` khi "ít nhất một phần tử được thêm". Viết một ví dụ với `HashSet` để chứng minh `true` không đồng nghĩa với "thêm hết".
2. Tự giải thích (bằng lời, không code) vì sao `strings.toArray(largerTab)` lại trả về **cùng** một array. Việc này có thể gây bug gì trong code thật?
3. Viết lại đoạn `removeIf(isNullOrEmpty)` bằng vòng lặp `Iterator` thủ công. So sánh số dòng và độ dễ sai.
4. Đối chiếu: PHP có `array_filter`. Nó sửa array gốc hay trả về array mới? Khác `removeIf` của Java ở điểm nào?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[Set]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html
[ArrayList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html
[HashSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html
[Iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html
[String]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/String.html
[IntFunction]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/function/IntFunction.html
[add]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#add(E)
[remove]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#remove(java.lang.Object)
[contains]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#contains(java.lang.Object)
[containsAll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#containsAll(java.util.Collection)
[addAll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#addAll(java.util.Collection)
[removeAll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeAll(java.util.Collection)
[retainAll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#retainAll(java.util.Collection)
[size]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#size()
[isEmpty]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#isEmpty()
[clear]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#clear()
[toArray]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray()
[toArrayT]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray(T%5B%5D)
[toArrayF]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#toArray(java.util.function.IntFunction)
[removeIf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeIf(java.util.function.Predicate)
[iterRemove]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#remove()
[UnsupportedOperationException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/UnsupportedOperationException.html
[NullPointerException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/NullPointerException.html
[ClassCastException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html
[IllegalArgumentException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalArgumentException.html
