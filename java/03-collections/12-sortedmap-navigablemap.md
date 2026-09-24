# Giữ key được sắp xếp với SortedMap và NavigableMap

> Dịch từ [Keeping Keys Sorted with SortedMap and NavigableMap](https://dev.java/learn/api/collections-framework/sorted-maps/) — dev.java.

## Các method mà SortedMap thêm vào

JDK cung cấp hai phần mở rộng của interface [`Map`][Map]: [`SortedMap`][SortedMap] và [`NavigableMap`][NavigableMap]. [`NavigableMap`][NavigableMap] là phần mở rộng của [`SortedMap`][SortedMap]. [`TreeMap`][TreeMap] implement cả hai interface này. Class [`TreeMap`][TreeMap] là một **red-black tree**, một data structure nổi tiếng. JDK cũng cho bạn [`ConcurrentSkipListMap`][ConcurrentSkipListMap], là một implementation thread-safe.

[`SortedMap`][SortedMap] và [`NavigableMap`][NavigableMap] giữ các cặp key/value được sắp theo **key**. Cũng như với [`SortedSet`][SortedSet] và [`NavigableSet`][NavigableSet], bạn cần cung cấp cách so sánh các key này. Có hai giải pháp: hoặc class của key implement [`Comparable`][Comparable], hoặc bạn cung cấp một [`Comparator`][Comparator] cho key khi tạo [`TreeMap`][TreeMap]. Nếu bạn cung cấp [`Comparator`][Comparator], nó sẽ được dùng **kể cả khi** key của bạn đã comparable.

Nếu implementation bạn chọn cho [`SortedMap`][SortedMap] hay [`NavigableMap`][NavigableMap] là [`TreeMap`][TreeMap], bạn có thể cast an toàn set trả về bởi [`keySet()`][keySet] hoặc [`entrySet()`][entrySet] sang [`SortedSet`][SortedSet] hoặc [`NavigableSet`][NavigableSet]. [`NavigableMap`][NavigableMap] có method [`navigableKeySet()`][navigableKeySet] trả về một instance [`NavigableSet`][NavigableSet] mà bạn dùng thay cho [`keySet()`][keySet] thuần. Cả hai method trả về **cùng một object**.

Interface [`SortedMap`][SortedMap] thêm các method sau vào [`Map`][Map]:

- [`firstKey()`][firstKey] và [`lastKey()`][lastKey]: trả về key nhỏ nhất và lớn nhất của map;
- [`headMap(toKey)`][headMap] và [`tailMap(fromKey)`][tailMap]: trả về một [`SortedMap`][SortedMap] mà key nhỏ hơn hẳn `toKey`, hoặc lớn hơn hay bằng `fromKey`;
- [`subMap(fromKey, toKey)`][subMap]: trả về một [`SortedMap`][SortedMap] mà key nhỏ hơn hẳn `toKey`, hoặc lớn hơn hay bằng `fromKey`.

Các map này là instance của [`SortedMap`][SortedMap] và là **view** được hậu thuẫn bởi map gốc. Mọi thay đổi trên map gốc đều thấy được trong các view này. Các view này cập nhật được, với một hạn chế: bạn **không thể** chèn key nằm ngoài giới hạn của map bạn đã tạo.

Xem hành vi này trong ví dụ sau:

```java
SortedMap<Integer, String> map = new TreeMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");
map.put(5, "five");
map.put(6, "six");

SortedMap<Integer, String> headMap = map.headMap(3);
headMap.put(0, "zero"); // this line is ok
headMap.put(4, "four"); // this line throws an IllegalArgumentException
```

## Các method mà NavigableMap thêm vào

### Truy cập key hoặc entry cụ thể

[`NavigableMap`][NavigableMap] thêm nhiều method nữa vào [`SortedMap`][SortedMap]. Nhóm method đầu tiên cho bạn truy cập các key và entry cụ thể trong map.

- [`firstEntry()`][firstEntry] và [`lastEntry()`][lastEntry]: trả về entry nhỏ nhất hoặc lớn nhất của map.
- [`ceilingKey(key)`][ceilingKey], [`ceilingEntry(key)`][ceilingEntry], [`higherKey(key)`][higherKey], [`higherEntry(key)`][higherEntry]: trả về key hoặc entry nhỏ nhất lớn hơn key cho trước. Các method `ceiling` **có thể** trả về key bằng key cho trước, còn key trả về bởi các method `higher` thì **lớn hơn hẳn**.
- [`floorKey(key)`][floorKey], [`floorEntry(key)`][floorEntry], [`lowerKey(key)`][lowerKey], [`lowerEntry(key)`][lowerEntry]: trả về key hoặc entry lớn nhất nhỏ hơn key cho trước. Các method `floor` có thể trả về key bằng key cho trước, còn `lower` thì **nhỏ hơn hẳn**.

### Truy cập map theo kiểu queue

Nhóm thứ hai cho bạn các tính năng kiểu queue:

- [`pollFirstEntry()`][pollFirstEntry]: trả về **và xóa** entry nhỏ nhất.
- [`pollLastEntry()`][pollLastEntry]: trả về và xóa entry lớn nhất.

### Đi qua map theo thứ tự đảo

Nhóm thứ ba đảo map của bạn, như thể nó được xây trên logic so sánh đảo ngược.

- [`navigableKeySet()`][navigableKeySet] là method tiện lợi trả về một [`NavigableSet`][NavigableSet] để bạn không phải cast kết quả của [`keySet()`][keySet].
- [`descendingKeySet()`][descendingKeySet]: trả về một [`NavigableSet`][NavigableSet] được hậu thuẫn bởi map, mà bạn iterate theo thứ tự giảm dần.
- [`descendingMap()`][descendingMap]: trả về một [`NavigableMap`][NavigableMap] với cùng ngữ nghĩa.

Cả hai view đều hỗ trợ xóa phần tử, nhưng bạn **không thể thêm** gì qua chúng.

Ví dụ minh họa:

```java
NavigableMap<Integer, String> map = new TreeMap<>();
map.put(1, "one");
map.put(2, "two");
map.put(3, "three");
map.put(4, "four");
map.put(5, "five");

map.keySet().forEach(key -> IO.print(key + " "));
IO.println();

NavigableSet<Integer> descendingKeys = map.descendingKeySet();
descendingKeys.forEach(key -> IO.print(key + " "));
```

Kết quả:

```text
1 2 3 4 5
5 4 3 2 1
```

### Lấy view kiểu submap

Nhóm method cuối cho bạn truy cập các view trên từng phần của map.

- [`subMap(fromKey, fromInclusive, toKey, toInclusive)`][nmSubMap]: trả về một submap mà bạn tự quyết định có bao gồm các biên hay không.
- [`headMap(toKey, inclusive)`][nmHeadMap]: tương tự cho head map.
- [`tailMap(fromKey, inclusive)`][nmTailMap]: tương tự cho tail map.

Các map này là view trên map gốc, bạn cập nhật được bằng cách xóa hoặc thêm cặp key/value. Nhưng có một hạn chế khi thêm: bạn **không thể** thêm key nằm ngoài giới hạn mà view được tạo ra.

```java
NavigableMap<Integer, String> map = new TreeMap<>();
map.put(2, "two");
map.put(4, "four");
map.put(6, "six");

IO.println("Map: " + map);

NavigableMap<Integer, String> subMap = map.subMap(2, true, 4, true);
IO.println("Submap from 2 to 4: " + subMap);
IO.println("Adding 3");
map.put(3, "three");
IO.println("Submap from 2 to 4: " + subMap);

NavigableMap<Integer, String> headMap = map.headMap(4, true);
IO.println("Headmap starting at 4: " + headMap);
IO.println("Adding 5");
map.put(5, "five");
IO.println("Headmap starting at 4: " + headMap);

NavigableMap<Integer, String> tailMap = map.tailMap(2, true);
IO.println("Tailmap up to 2: " + tailMap);
IO.println("Adding 1");
map.put(1, "one");
IO.println("Tailmap up to 2: " + tailMap);
```

Kết quả:

```text
Map: {2=two, 4=four, 6=six}
Submap from 2 to 4: {2=two, 4=four}
Adding 3
Submap from 2 to 4: {2=two, 3=three, 4=four}
Tailmap starting at 4: {4=four, 6=six}
Adding 5
Tailmap starting at 4: {4=four, 5=five, 6=six}
Headmap up to 2: {2=two}
Adding 1
Headmap up to 2: {1=one, 2=two}
```

> **Ghi chú của người dịch:** trên trang gốc, nhãn `headMap`/`tailMap` trong phần code và trong phần output bị lệch nhau (code in "Headmap starting at 4" nhưng output ghi "Tailmap starting at 4"). Hãy tự chạy lại để tự kiểm chứng: `headMap(4, true)` cho các key **≤ 4**, còn `tailMap(2, true)` cho các key **≥ 2**. Đây là bài học nhỏ: **đừng tin nhãn, hãy tin định nghĩa**.

---

**Bài tập**

1. Với `TreeMap<Integer,String>` chứa key 1, 3, 5: `ceilingKey(3)`, `higherKey(3)`, `floorKey(3)`, `lowerKey(3)` trả về gì? Đoán trước rồi chạy kiểm tra.
2. Dùng `TreeMap` hiện thực bảng tra "điểm → xếp loại": key là ngưỡng điểm, tra bằng `floorEntry(diem)`. Đây là use case kinh điển của `NavigableMap`.
3. Lấy `headMap(3)` rồi `put(4, "four")` — giải thích exception theo ràng buộc "giới hạn của view".
4. Đối chiếu: `TreeMap` là red-black tree (O(log n)), `HashMap` là hash table (O(1) trung bình). Khi nào bạn *chọn* `TreeMap` dù nó chậm hơn?

[Map]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html
[SortedMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedMap.html
[NavigableMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html
[TreeMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/TreeMap.html
[ConcurrentSkipListMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/ConcurrentSkipListMap.html
[SortedSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html
[NavigableSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html
[Comparable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html
[Comparator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html
[keySet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#keySet()
[entrySet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html#entrySet()
[firstKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedMap.html#firstKey()
[lastKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedMap.html#lastKey()
[headMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedMap.html#headMap(K)
[tailMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedMap.html#tailMap(K)
[subMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedMap.html#subMap(K,K)
[firstEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#firstEntry()
[lastEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#lastEntry()
[ceilingKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#ceilingKey(K)
[ceilingEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#ceilingEntry(K)
[higherKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#higherKey(K)
[higherEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#higherEntry(K)
[floorKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#floorKey(K)
[floorEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#floorEntry(K)
[lowerKey]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#lowerKey(K)
[lowerEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#lowerEntry(K)
[pollFirstEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#pollFirstEntry()
[pollLastEntry]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#pollLastEntry()
[navigableKeySet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#navigableKeySet()
[descendingKeySet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#descendingKeySet()
[descendingMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#descendingMap()
[nmSubMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#subMap(K,boolean,K,boolean)
[nmHeadMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#headMap(K,boolean)
[nmTailMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableMap.html#tailMap(K,boolean)
