# 03 — Collections Framework

Bản dịch tiếng Việt của loạt bài [The Collections Framework](https://dev.java/learn/api/collections-framework/)
trên dev.java. 14 bài, mỗi URL con một file.

| # | Bài | Nội dung chính |
|---|-----|----------------|
| 01 | [Giới thiệu Collections Framework](01-gioi-thieu.md) | Vì sao chọn collection thay vì array; các class cũ cần tránh |
| 02 | [Cây phân cấp Collection](02-cay-phan-cap-collection.md) | `Iterable` → `Collection` → `List`/`Set`/`SortedSet`/`NavigableSet` |
| 03 | [Lưu phần tử trong Collection](03-luu-phan-tu-trong-collection.md) | `add`/`remove`/`contains`, phép toán tập hợp, `toArray`, `removeIf` |
| 04 | [Iterate qua phần tử](04-iterate-phan-tu.md) | for-each, `Iterator`, `ConcurrentModificationException`, tự implement `Iterable` |
| 05 | [List](05-list.md) | index, `subList` (là view!), `sort`, `ListIterator` |
| 06 | [Set, SortedSet, NavigableSet](06-set-sortedset-navigableset.md) | `HashSet`/`LinkedHashSet`/`TreeSet`, `ceiling`/`floor`, `descendingSet` |
| 07 | [Factory methods](07-factory-methods.md) | `List.of`, `copyOf`, `Arrays.asList`, class `Collections` |
| 08 | [Stack và Queue](08-stack-va-queue.md) | `Queue`/`Deque`, `add` vs `offer`, `ArrayDeque`, tránh class `Stack` |
| 09 | [Map](09-map.md) | `Map.of`, `Map.Entry`, key/value, các implementation |
| 10 | [Quản lý nội dung Map](10-quan-ly-noi-dung-map.md) | `putIfAbsent`, `getOrDefault`, `keySet`/`values`/`entrySet` là view |
| 11 | [Map và lambda](11-map-va-lambda.md) | `forEach`, `replaceAll`, `compute*`, `merge` |
| 12 | [SortedMap và NavigableMap](12-sortedmap-navigablemap.md) | `TreeMap`, `floorEntry`, submap view |
| 13 | [Chọn key immutable](13-chon-key-immutable.md) | Antipattern key mutable; `HashSet` thực chất là `HashMap` |
| 14 | [ArrayList vs LinkedList](14-arraylist-vs-linkedlist.md) | Benchmark, pointer chasing, memory; **vì sao big-O chưa đủ** |

## Đọc theo thứ tự nào?

- **Cần dùng ngay:** 05 (List) → 09 (Map) → 11 (Map + lambda). Ba bài này phủ 90% code hằng ngày.
- **Muốn hiểu gốc:** đọc tuần tự 01 → 14.
- **Hai bài dễ bị bỏ qua nhưng quan trọng nhất:** 13 (key immutable) và 14 (chọn implementation).

## Cạm bẫy được nhắc lại nhiều lần trong loạt bài này

1. **View, không phải copy.** `subList`, `keySet`, `values`, `entrySet`, `headMap`, `descendingSet`
   đều là view trên cấu trúc gốc. Sửa view là sửa gốc.
2. **`equals`/`hashCode` là bắt buộc** nếu object của bạn làm key của `Map` hoặc phần tử của `Set`.
3. **Đừng mutate** object sau khi đã dùng nó làm key hoặc đưa vào `Set` → mất dữ liệu (bài 13).
4. **Unboxing `null`** → `NullPointerException`. `map.get(k)` trả `null`; đừng gán thẳng vào `int`.
5. **`ArrayList` là mặc định đúng.** Đừng chọn `LinkedList` vì big-O trên giấy (bài 14).

## Lưu ý về code trong bài

Các ví dụ dùng `IO.println(...)` theo đúng bản gốc dev.java (API của JDK mới, dùng trong
file class ẩn danh). Với JDK cũ hơn hãy thay bằng `System.out.println(...)`.

Repo này **chưa cài JDK** (xem `CLAUDE.md`) nên code trong loạt bài chưa được chạy thử.
Cài bằng `brew install openjdk` rồi tự chạy lại các ví dụ — đó cũng chính là bài tập tốt nhất.
