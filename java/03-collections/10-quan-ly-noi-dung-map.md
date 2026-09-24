# Quản lý nội dung của một Map

> Dịch từ [Managing the Content of a Map](https://dev.java/learn/api/collections-framework/working-with-keys-and-values/) — dev.java.

## Thêm một cặp key-value vào Map

Bạn thêm cặp key/value vào map đơn giản bằng [`put(key, value)`][put]. Nếu key chưa có trong map thì cặp key/value đơn giản được thêm vào. Nếu đã có, value cũ bị thay bằng value mới.

Trong cả hai trường hợp, method [`put()`][put] trả về value **đang** gắn với key đó. Nghĩa là nếu đây là key mới, lời gọi [`put()`][put] sẽ trả về `null`.

Java SE 8 giới thiệu method [`putIfAbsent()`][putIfAbsent]. Method này cũng thêm cặp key/value vào map, nhưng chỉ khi key chưa có **và** không đang gắn với giá trị null. Thoạt đầu điều này có thể gây bối rối: [`putIfAbsent()`][putIfAbsent] **sẽ thay** một giá trị null bằng value mới bạn cung cấp.

Method này rất tiện nếu bạn cần loại bỏ những giá trị null lỗi trong map. Ví dụ, đoạn code sau sẽ fail với [`NullPointerException`][NullPointerException] vì bạn không thể auto-unbox một [`Integer`][Integer] null thành giá trị `int`.

```java
Map<String, Integer> map = new HashMap<>();
map.put("one", 1);
map.put("two", null);
map.put("three", 3);
map.put("four", null);
map.put("five", 5);

for (int value : map.values()) {
    IO.println("value = " + value);
}
```

Nếu nhìn kỹ đoạn code này, bạn sẽ thấy [`map.values()`][values] là một `Collection<Integer>`. Nên iterate qua collection này tạo ra các instance [`Integer`][Integer]. Vì bạn khai báo `value` là `int`, compiler sẽ auto-unbox [`Integer`][Integer] này thành `int`. Cơ chế đó **fail** với [`NullPointerException`][NullPointerException] nếu instance [`Integer`][Integer] là null.

Bạn có thể sửa map này bằng đoạn code sau, thay các giá trị null lỗi bằng giá trị mặc định `-1` để không sinh [`NullPointerException`][NullPointerException] nữa:

```java
Map<String, Integer> map = new HashMap<>();
map.put("one", 1);
map.put("two", null);
map.put("three", 3);
map.put("four", null);
map.put("five", 5);

for (String key : map.keySet()) {
    map.putIfAbsent(key, -1);
}

for (int value : map.values()) {
    IO.println("value = " + value);
}
```

Kết quả — như bạn thấy, map này không còn giá trị null nào:

```text
value = -1
value = 1
value = -1
value = 3
value = 5
```

## Lấy value từ key

Bạn lấy value gắn với một key cho trước đơn giản bằng cách gọi method [`get(key)`][get].

Java SE 8 giới thiệu method [`getOrDefault()`][getOrDefault] nhận một key và một giá trị mặc định, sẽ được trả về nếu key không có trong map.

Xem method này hoạt động:

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

List<String> values = new ArrayList<>();
for (int key = 0; key < 5; key++) {
    values.add(map.getOrDefault(key,"UNDEFINED"));
}

IO.println("values = " + values);
```

Kết quả:

```text
[UNDEFINED, one, two, three, UNDEFINED]
```

Hoặc, nếu bạn đã quen với stream (được trình bày ở phần [Stream API](https://dev.java/learn/api/streams/)):

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

List<String> values =
    IntStream.range(0, 5)
        .mapToObj(key -> map.getOrDefault(key, "UNDEFINED"))
        .collect(Collectors.toList());

IO.println("values = " + values);
```

Kết quả:

```text
values = [UNDEFINED, one, two, three, UNDEFINED]
```

## Xóa một key khỏi Map

Xóa một cặp key/value được thực hiện bằng cách gọi method [`remove(key)`][remove]. Method này trả về value đã gắn với key đó, nên nó có thể trả về `null`.

Việc xóa một cặp key/value một cách "mù quáng" khi bạn không biết value đang gắn với key đó có thể rủi ro. Vì vậy Java SE 8 thêm một overload nhận value làm tham số thứ hai. Lần này, cặp key/value chỉ bị xóa nếu nó **khớp hoàn toàn** cặp key/value trong map.

Method [`remove(key, value)`][remove2] trả về `boolean`, `true` nếu cặp key/value đã bị xóa khỏi map.

Xem hai pattern này trong ví dụ sau:

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

IO.println("Map: " + map);
IO.println("Removing 3: " + map.remove(3));
IO.println("Removing 4: " + map.remove(4));
IO.println("Removing 2 if bound to 'one': " + map.remove(2, "one"));
IO.println("Map: " + map);
```

Kết quả:

```text
Map: {1=one, 2=two, 3=three}
Removing 3: three
Removing 4: null
Removing 2 if bound to 'one': false
Map: {1=one, 2=two}
```

## Kiểm tra sự tồn tại của key hoặc value

Bạn có hai method để kiểm tra sự tồn tại của một key hoặc một value cho trước: [`containsKey(key)`][containsKey] và [`containsValue(value)`][containsValue]. Cả hai trả về `true` nếu map chứa key hoặc value đó.

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

IO.println("Map: " + map);
IO.println("Contains key 3? " + map.containsKey(3));
IO.println("Contains key 4? " + map.containsKey(4));
IO.println("Contains value 'one'? " + map.containsValue("one"));
IO.println("Contains value 'zero'? " + map.containsValue("zero"));
```

Kết quả:

```text
Map: {1=one, 2=two, 3=three}
Contains key 3? true
Contains key 4? false
Contains value 'one'? true
Contains value 'zero'? false
```

## Kiểm tra nội dung của một Map

Interface [`Map`][Map] cũng mang các method trông giống những gì bạn có ở interface [`Collection`][Collection]. Các method này tự giải thích: [`isEmpty()`][isEmpty] trả về `true` với map rỗng, [`size()`][size] trả về số cặp key/value, và [`clear()`][clear] xóa toàn bộ nội dung của map.

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

IO.println("Is empty? " + map.isEmpty());
IO.println("Size:     " + map.size());

map.clear();

IO.println("Is empty? " + map.isEmpty());
IO.println("Size:     " + map.size());
```

Kết quả:

```text
Is empty? false
Size:     3
Is empty? true
Size:     0
```

Cũng có method để thêm nội dung của một map cho trước vào map hiện tại: [`putAll(otherMap)`][putAll]. Nếu một số key có ở cả hai map thì value của `otherMap` sẽ **ghi đè** value của map này.

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

Map<Integer, String> otherMap = new HashMap<>();
otherMap.put(2, "TWO");
otherMap.put(3, "THREE");
otherMap.put(4, "FOUR");

IO.println("Map:       " + map);
IO.println("Other map: " + otherMap);

map.putAll(otherMap);

IO.println("Map:       " + map);
IO.println("Other map: " + otherMap);
```

Kết quả:

```text
Map:       {1=one, 2=two, 3=three}
Other map: {2=TWO, 3=THREE, 4=FOUR}
Map:       {1=one, 2=TWO, 3=THREE, 4=FOUR}
Other map: {2=TWO, 3=THREE, 4=FOUR}
```

## Lấy view trên key, value hoặc entry của một Map

Bạn cũng lấy được các collection khác nhau từ một map:

- [`keySet()`][keySet]: trả về một instance [`Set`][Set] chứa các key được định nghĩa trong map.
- [`entrySet()`][entrySet]: trả về một instance `Set<Map.Entry>` chứa các cặp key/value trong map.
- [`values()`][values]: trả về một instance [`Collection`][Collection] chứa các value có trong map.

Ví dụ sau minh họa ba method này:

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");

Set<Integer> keys = map.keySet();
IO.println("keys = " + keys);
IO.println("Adding 4");
map.put(4, "four");

Collection<String> values = map.values();
IO.println("values = " + values);
IO.println("Adding 5");
map.put(5, "five");
IO.println("values = " + values);

Set<Map.Entry<Integer, String>> entries = map.entrySet();
IO.println("entries = " + entries);
IO.println("Adding 6");
map.put(6, "six");
IO.println("entries = " + entries);
```

Kết quả:

```text
keys = [1, 2, 3]
Adding 4
values = [one, two, three, four]
Adding 5
values = [one, two, three, four, five]
entries = [1=one, 2=two, 3=three, 4=four, 5=five]
Adding 6
entries = [1=one, 2=two, 3=three, 4=four, 5=five, 6=six]
```

Các set này là **view** được hậu thuẫn bởi map hiện tại. Mọi thay đổi trên map đều phản ánh vào các view đó.

### Xóa một key khỏi set các key

Sửa một trong các set này cũng phản ánh vào map: ví dụ, xóa một key khỏi set trả về bởi [`keySet()`][keySet] sẽ xóa cặp key/value tương ứng khỏi map.

```java
Map<Integer, String> map = new HashMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");
map.put(4, "four");
map.put(5, "five");
map.put(6, "six");

IO.println("Map: " + map);
Set<Integer> keys = map.keySet();
IO.println("keys = " + keys);
IO.println("Removing 3");
keys.remove(3);
IO.println("Map: " + map);

Set<Map.Entry<Integer, String>> entries = map.entrySet();
IO.println("entries = " + entries);
IO.println("Removing 4");
entries.remove(Map.entry(4, "four"));
IO.println("Map: " + map);
```

Kết quả:

```text
Map: {1=one, 2=two, 3=three, 4=four, 5=five, 6=six}
keys = [1, 2, 3, 4, 5, 6]
Removing 3
Map: {1=one, 2=two, 4=four, 5=five, 6=six}
entries = [1=one, 2=two, 4=four, 5=five, 6=six]
Removing 4
Map: {1=one, 2=two, 5=five, 6=six}
```

### Xóa một value khỏi collection các value

Xóa một value không đơn giản như vậy, vì một value có thể xuất hiện nhiều lần trong map. Trong trường hợp đó, xóa một value khỏi collection các value chỉ xóa **cặp key/value khớp đầu tiên**.

```java
Map<Integer, String> map =
    Map.ofEntries(
        Map.entry(1, "one"),
        Map.entry(2, "two"),
        Map.entry(3, "three"),
        Map.entry(4, "three")
    );
IO.println("map before = " + map);
map = new HashMap<>(map);
map.values().remove("three");
IO.println("map after  = " + map);
```

Kết quả:

```text
map before = {3=three, 2=two, 1=one, 4=three}
map after  = {1=one, 2=two, 4=three}
```

Như bạn thấy, chỉ cặp key/value đầu tiên bị xóa trong ví dụ này. Bạn cần cẩn thận ở đây, vì nếu implementation bạn chọn là [`HashMap`][HashMap], bạn **không thể biết trước** cặp key/value nào sẽ được tìm thấy.

Tuy nhiên bạn không có quyền dùng mọi thao tác trên các set này. Ví dụ, bạn **không** thể thêm phần tử vào set các key, hay vào collection các value. Nếu thử, bạn sẽ nhận [`UnsupportedOperationException`][UnsupportedOperationException].

Nếu điều bạn cần là iterate qua các cặp key/value của map thì lựa chọn tốt nhất là iterate **trực tiếp trên set các cặp key/value**. Làm vậy hiệu quả hơn nhiều so với iterate trên set các key rồi lấy value tương ứng. Pattern tốt nhất là:

```java
Map<Integer, String> map =
    Map.ofEntries(
        Map.entry(1, "one"),
        Map.entry(2, "two"),
        Map.entry(3, "three"),
        Map.entry(4, "three")
    );

for (Map.Entry<Integer, String> entry : map.entrySet()) {
    IO.println("entry = " + entry);
}
```

Kết quả:

```text
entry = 4=three
entry = 3=three
entry = 2=two
entry = 1=one
```

---

**Bài tập**

1. Đo hiệu năng (thô cũng được): với `HashMap` 1 triệu phần tử, so sánh iterate qua `keySet()` + `get(k)` với iterate qua `entrySet()`. Kết quả khớp với lời khuyên trong bài không?
2. Viết một method xóa an toàn: chỉ xóa key nếu value đúng như bạn mong đợi. Dùng overload `remove(key, value)`. Tình huống thực tế nào cần tới nó? (Gợi ý: nhiều luồng cùng sửa.)
3. `map.values().remove("three")` chỉ xóa một cặp. Viết code xóa **tất cả** các cặp có value là `"three"`.
4. Đối chiếu: PHP `unset($arr['k'])` không trả về value cũ. Việc `remove()` của Java trả về value cũ giúp bạn viết code gì gọn hơn?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[Set]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html
[Map]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html
[HashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashMap.html
[Integer]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Integer.html
[put]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#put(K,V)
[putIfAbsent]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#putIfAbsent(K,V)
[get]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#get(java.lang.Object)
[getOrDefault]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#getOrDefault(java.lang.Object,V)
[remove]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#remove(java.lang.Object)
[remove2]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#remove(java.lang.Object,java.lang.Object)
[containsKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#containsKey(java.lang.Object)
[containsValue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#containsValue(java.lang.Object)
[isEmpty]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#isEmpty()
[size]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#size()
[clear]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#clear()
[putAll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#putAll(java.util.Map)
[keySet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#keySet()
[entrySet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#entrySet()
[values]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#values()
[NullPointerException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/NullPointerException.html
[UnsupportedOperationException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/UnsupportedOperationException.html
