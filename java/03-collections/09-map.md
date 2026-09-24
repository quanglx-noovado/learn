# Dùng Map để lưu cặp key-value

> Dịch từ [Using Maps to Store Key Value Pairs](https://dev.java/learn/api/collections-framework/maps/) — dev.java.

## Giới thiệu cây phân cấp Map

Nếu bạn nóng lòng muốn thực hành các phép toán map phổ biến nhất trên code thật, hãy nhảy xuống cuối trang: [Thực hành các phép toán trên Map](#thực-hành-các-phép-toán-trên-map).

Cấu trúc chính thứ hai mà Collections Framework cung cấp là hiện thực của một data structure rất kinh điển: **hashmap**. Khái niệm này không mới và là nền tảng trong việc tổ chức dữ liệu, dù trong memory hay không. Nó hoạt động ra sao và được hiện thực thế nào trong Collections Framework?

Một hashmap là cấu trúc có khả năng lưu các cặp key-value. Value là object bất kỳ mà ứng dụng của bạn cần xử lý, còn key là thứ có thể **đại diện** cho object đó.

Giả sử bạn cần tạo một ứng dụng xử lý hóa đơn, biểu diễn bởi các instance của class `Invoice`. Khi đó value của bạn là các instance `Invoice`, và key có thể là số hóa đơn. Mỗi hóa đơn có một số, và số đó là duy nhất trong tất cả hóa đơn.

Nói chung, mỗi value được gắn với một key, giống như hóa đơn gắn với số hóa đơn. Nếu bạn có một key, bạn lấy được value. Thường key là một object đơn giản: một chuỗi vài ký tự hoặc một số. Ngược lại, value có thể phức tạp tùy ý. Đó là mục đích của hashmap: bạn thao tác với key, chuyển nó từ phần này sang phần khác của ứng dụng, truyền nó qua network, và khi cần object đầy đủ thì bạn lấy nó ra bằng key.

Trước khi đi vào chi tiết của interface [`Map`][Map], đây là những khái niệm bạn cần nhớ:

- Một hashmap lưu được các cặp key-value.
- Một key đóng vai trò ký hiệu (symbol) cho một value cho trước.
- Key là object đơn giản, value có thể phức tạp tùy ý.
- Key là **duy nhất** trong một hashmap, value **không cần** duy nhất.
- Mọi value lưu trong hashmap phải được gắn với một key; một cặp key-value trong map tạo thành một **entry** của map đó.
- Một key có thể được dùng để lấy value gắn với nó.

Collections Framework cho bạn interface [`Map`][Map] hiện thực khái niệm này, cùng hai phần mở rộng, [`SortedMap`][SortedMap] và [`NavigableMap`][NavigableMap], như hình sau.

![The Map Interface Hierarchy](https://dev.java/assets/images/collections-framework/03_map-hierarchy.png)

Cây phân cấp này rất đơn giản và trông giống cây phân cấp [`Set`][Set] với [`SortedSet`][SortedSet] và [`NavigableSet`][NavigableSet]. Đúng vậy, [`SortedMap`][SortedMap] có cùng loại ngữ nghĩa với [`SortedSet`][SortedSet]: một [`SortedMap`][SortedMap] là map giữ các cặp key-value được sắp theo **key**. Tương tự với [`NavigableMap`][NavigableMap]: các method mà interface này thêm vào cùng loại với những gì [`NavigableSet`][NavigableSet] thêm cho [`SortedSet`][SortedSet].

JDK cho bạn nhiều implementation của interface [`Map`][Map], được dùng rộng rãi nhất là class [`HashMap`][HashMap].

Hai implementation khác:

- [`LinkedHashMap`][LinkedHashMap] là một [`HashMap`][HashMap] có thêm cấu trúc nội bộ để giữ thứ tự các cặp key-value. Iterate qua key hay cặp key-value sẽ theo đúng thứ tự bạn đã thêm chúng vào.
- [`IdentityHashMap`][IdentityHashMap] là một [`Map`][Map] chuyên biệt mà bạn chỉ nên dùng trong những trường hợp rất cụ thể. Implementation này không dành cho việc dùng chung trong ứng dụng. Thay vì dùng [`equals()`][equals] và [`hashCode()`][hashCode] để so sánh các object key, implementation này chỉ so sánh **tham chiếu** tới các key đó bằng toán tử `==`. Dùng thận trọng, chỉ khi bạn chắc đó đúng là cái mình cần.

Có thể bạn đã nghe về **multimap**. Multimap là khái niệm trong đó một key có thể gắn với nhiều value. Khái niệm này **không** được hỗ trợ trực tiếp trong Collections Framework. Tuy nhiên tính năng này hữu ích, và sau trong tutorial này bạn sẽ thấy cách tạo map mà value chính là các list value. Pattern đó cho phép bạn tạo các cấu trúc kiểu multimap.

## Dùng convenience factory method để tạo Map

Như bạn đã thấy, Java SE 9 thêm các method vào interface [`List`][List] và [`Set`][Set] để tạo list và set immutable.

Interface [`Map`][Map] cũng có những method như vậy để tạo map và entry immutable.

Bạn tạo một Map dễ dàng theo pattern sau:

```java
Map<Integer, String> map =
    Map.of(
        1, "one",
        2, "two",
        3, "three"
    );
IO.println("Map: " + map);
```

Kết quả:

```text
Map: {3=three, 1=one, 2=two}
```

Có một lưu ý: bạn chỉ dùng được pattern này nếu có **không quá 10 cặp** key-value.

Nếu nhiều hơn, bạn cần dùng pattern khác:

```java
Map.Entry<Integer, String> e1 = Map.entry(1, "one");
Map.Entry<Integer, String> e2 = Map.entry(2, "two");
Map.Entry<Integer, String> e3 = Map.entry(3, "three");

Map<Integer, String> map = Map.ofEntries(e1, e2, e3);

IO.println("Map: " + map);
```

Kết quả:

```text
Map: {1=one, 2=two, 3=three}
```

Bạn cũng có thể viết pattern này theo cách sau, và dùng static import để tăng tính dễ đọc:

```java
Map<Integer, String> map =
    Map.ofEntries(
        Map.entry(1, "one"),
        Map.entry(2, "two"),
        Map.entry(3, "three")
    );
IO.println("Map: " + map);
```

Kết quả:

```text
Map: {1=one, 2=two, 3=three}
```

Có những hạn chế trên các map và entry tạo bởi các factory method này, giống như với set:

- Map và entry bạn nhận được là object **immutable**.
- Entry null, key null và value null **không** được phép.
- Cố tạo một map với key trùng lặp theo cách này là vô nghĩa, nên như một cảnh báo, bạn sẽ nhận [`IllegalArgumentException`][IllegalArgumentException] ngay lúc tạo map.

## Lưu cặp key/value trong một Map

Quan hệ giữa một key và value gắn với nó theo hai quy tắc đơn giản:

- Một key chỉ có thể gắn với **một** value.
- Một value có thể gắn với **nhiều** key.

Điều này dẫn tới vài hệ quả về nội dung của map:

- Tập tất cả các key không thể có phần tử trùng lặp, nên nó có cấu trúc của một [`Set`][Set].
- Tập tất cả các cặp key/value cũng không thể trùng lặp, nên nó cũng có cấu trúc của một [`Set`][Set].
- Tập tất cả các value **có thể** trùng lặp, nên nó có cấu trúc của một [`Collection`][Collection] thuần.

Từ đó, bạn định nghĩa được các thao tác sau trên một map:

- Đặt (put) một cặp key/value vào map. Việc này có thể thất bại nếu key đã được định nghĩa trong map.
- Lấy (get) một value từ một key.
- Xóa (remove) một key khỏi map, cùng với value của nó.

Bạn cũng định nghĩa được các thao tác kinh điển kiểu set:

- Kiểm tra map có rỗng hay không.
- Lấy số cặp key-value chứa trong map.
- Đưa toàn bộ nội dung của một map khác vào map này.
- Xóa sạch nội dung của map.

Tất cả các thao tác và khái niệm này được hiện thực trong interface [`Map`][Map], cùng một số cái khác mà bạn sẽ thấy sau.

## Khám phá interface Map

Interface [`Map`][Map] là kiểu cơ sở mô hình hóa khái niệm map trong JDK.

Bạn nên **cực kỳ cẩn thận** khi chọn kiểu cho key của map. Nói ngắn gọn: chọn một key mutable không bị cấm, nhưng **nguy hiểm và không được khuyến khích**. Một khi key đã được thêm vào map, thay đổi nó có thể dẫn tới thay đổi giá trị hash code và danh tính của nó. Điều này có thể khiến cặp key-value của bạn **không thể lấy lại được**, hoặc cho bạn một value khác khi truy vấn map. Bạn sẽ thấy điều này sau trong một ví dụ.

[`Map`][Map] định nghĩa một member interface: [`Map.Entry`][MapEntry] để mô hình hóa một cặp key-value. Interface này định nghĩa ba method để truy cập key và value:

- [`getKey()`][getKey]: đọc key;
- [`getValue()`][getValue] và [`setValue(value)`][setValue]: đọc và cập nhật value gắn với key đó.

Các object [`Map.Entry`][MapEntry] bạn lấy từ một map là **view** trên nội dung của map. Do đó sửa value của một entry object sẽ phản ánh vào map và ngược lại. Đây là lý do bạn **không** thể đổi key trong object này: làm vậy có thể làm hỏng map của bạn.

## Thực hành các phép toán trên Map

### Tạo và điền dữ liệu vào một Map

```java
Map<String, Integer> ages = new HashMap<>();
ages.put("Alice", 25);
ages.put("Bob", 30);
ages.put("Carol", 28);
ages.put("David", 35);
IO.println("Size of the map: " + ages.size());
IO.println("Ages: " + ages);
```

Kết quả:

```text
Size of the map: 4
Ages: {Bob=30, Alice=25, David=35, Carol=28}
```

### Lấy value từ key

```java
var ages = Map.of("Alice", 25, "Bob", 30, "Carol", 28, "David", 35);
IO.println("Ages: " + ages);

IO.println("Alice's age: " + ages.get("Alice"));
IO.println("Eve's age: " + ages.get("Eve")); // Returns null
IO.println("Eve's age (with default): " + ages.getOrDefault("Eve", 0));
```

Kết quả:

```text
Ages: {Bob=30, David=35, Carol=28, Alice=25}
Alice's age: 25
Eve's age: null
Eve's age (with default): 0
```

### Kiểm tra key hoặc value có tồn tại

```java
var ages = Map.of("Alice", 25, "Bob", 30, "Carol", 28, "David", 35);
IO.println("Ages: " + ages);

IO.println("Contains Bob as a key? " + ages.containsKey("Bob"));
IO.println("Contains Bob as a value? " + ages.containsValue("Bob"));
IO.println("Contains age 28 as a value? " + ages.containsValue(28));
IO.println("Contains age 28 as a key? " + ages.containsKey(28));
```

Kết quả:

```text
Ages: {Carol=28, David=35, Bob=30, Alice=25}
Contains Bob as a key? true
Contains Bob as a value? false
Contains age 28 as a value? true
Contains age 28 as a key? false
```

### Cập nhật và xóa cặp key/value đã có

Bạn có thể cập nhật value gắn với một key đã có, hoặc chỉ thêm cặp key/value khi key **chưa** có trong map.

```java
var ages = Map.of("Alice", 25, "Bob", 30, "Carol", 28, "David", 35);
// make ages modifiable
ages = new HashMap<>(ages);
IO.println("Ages: " + ages);

var previousValue = ages.put("Alice", 26); // Updates existing key
IO.println("Previous Alice age: " + previousValue);

previousValue = ages.putIfAbsent("Alice", 27); // Only adds if key doesn't exist
IO.println("Previous Alice age: " + previousValue);

previousValue = ages.putIfAbsent("Eve", 22); // Only adds if key doesn't exist
IO.println("Previous Eve age: " + previousValue);
IO.println("Updated map: " + ages);

ages.remove("David");
IO.println("After removing David: " + ages);
```

Kết quả:

```text
Ages: {David=35, Carol=28, Bob=30, Alice=25}
Previous Alice age: 25
Previous Alice age: 26
Previous Eve age: null
Updated map: {David=35, Carol=28, Bob=30, Eve=22, Alice=26}
After removing David: {Carol=28, Bob=30, Eve=22, Alice=26}
```

### Iterate qua key, value và entry

Có ba collection bạn lấy được từ một map:

- Set các key của nó.
- Collection các value của nó.
- Set các cặp key/value của nó, mô hình hóa dưới dạng entry.

```java
var ages = Map.of("Alice", 25, "Bob", 30, "Carol", 28, "David", 35);

var keySet = ages.keySet();
IO.println("Key set: " + keySet);

var values = ages.values();
IO.println("Value collection: " + values);

var entries = ages.entrySet();
IO.println("Entry set: " + entries);
```

Kết quả:

```text
Key set: [Bob, David, Carol, Alice]
Value collection: [30, 35, 28, 25]
Entry set: [Bob=30, David=35, Carol=28, Alice=25]
```

---

**Bài tập**

1. `ages.get("Eve")` trả về `null`. Nhưng nếu bạn gán vào `int age = ages.get("Eve");` thì sao? (Cạm bẫy unboxing → `NullPointerException`.) Sửa lại bằng `getOrDefault`.
2. Tạo một "multimap" `Map<String, List<String>>` gom từ theo chữ cái đầu. Chưa dùng lambda — bài sau sẽ có cách gọn hơn.
3. `put()` trả về value **cũ**. Viết một method `boolean capNhat(Map<String,Integer> m, String k, int v)` trả về `true` nếu key đã tồn tại từ trước.
4. Đối chiếu: `array` của PHP vừa là list vừa là map. Điều đó tiện ở đâu và gây bug ở đâu, so với việc Java tách `List` và `Map`?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[Set]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html
[SortedSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html
[NavigableSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html
[Map]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html
[SortedMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedMap.html
[NavigableMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html
[HashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashMap.html
[LinkedHashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedHashMap.html
[IdentityHashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/IdentityHashMap.html
[MapEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.Entry.html
[getKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.Entry.html#getKey()
[getValue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.Entry.html#getValue()
[setValue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.Entry.html#setValue(V)
[equals]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Object.html#equals(java.lang.Object)
[hashCode]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Object.html#hashCode()
[IllegalArgumentException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalArgumentException.html
