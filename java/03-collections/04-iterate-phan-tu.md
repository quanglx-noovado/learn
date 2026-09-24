# Iterate qua các phần tử của một Collection

> Dịch từ [Iterating over the Elements of a Collection](https://dev.java/learn/api/collections-framework/iterating/) — dev.java.

## Dùng pattern for-each

Lựa chọn đơn giản nhất để iterate qua các phần tử của một collection là dùng pattern for-each.

```java
Collection<String> strings = List.of("one", "two", "three");

for (String element: strings) {
    IO.println(element);
}
```

Kết quả:

```text
one
two
three
```

Pattern này rất hiệu quả, miễn là bạn chỉ cần **đọc** các phần tử. Pattern [`Iterator`][Iterator] cho phép **xóa** một số phần tử của collection ngay trong lúc đang iterate. Nếu bạn cần làm việc đó, hãy dùng pattern [`Iterator`][Iterator].

## Dùng Iterator trên một collection

Việc iterate qua phần tử của collection dùng một object đặc biệt: một instance của interface [`Iterator`][Iterator]. Bạn lấy được object [`Iterator`][Iterator] từ bất kỳ phần mở rộng nào của interface [`Collection`][Collection]. Method [`iterator()`][iterator] được định nghĩa trên interface [`Iterable`][Iterable], được [`Collection`][Collection] extends, và được extends tiếp bởi tất cả interface trong cây phân cấp collection.

Iterate bằng object này là quy trình hai bước:

- Trước tiên kiểm tra xem còn phần tử nào cần thăm hay không, bằng method [`hasNext()`][hasNext].
- Rồi tiến tới phần tử tiếp theo bằng method [`next()`][next].

Nếu bạn gọi [`next()`][next] mà collection đã hết phần tử, bạn sẽ nhận [`NoSuchElementException`][NoSuchElementException]. Gọi [`hasNext()`][hasNext] không bắt buộc, nó ở đó để giúp bạn chắc chắn là thật sự còn phần tử tiếp theo.

Pattern như sau:

```java
Collection<String> strings = List.of("one", "two", "three", "four");
for (Iterator<String> iterator = strings.iterator(); iterator.hasNext();) {
    String element = iterator.next();
    if (element.length() == 3) {
        IO.println(element);
    }
}
```

Kết quả:

```text
one
two
```

Interface [`Iterator`][Iterator] có method thứ ba: [`remove()`][remove]. Gọi method này xóa phần tử hiện tại khỏi collection. Tuy nhiên có trường hợp method này không được hỗ trợ, khi đó nó throw [`UnsupportedOperationException`][UnsupportedOperationException]. Khá rõ ràng: gọi [`remove()`][remove] trên một collection immutable thì không thể hoạt động, đó là một trong các trường hợp đó. Các implementation của [`Iterator`][Iterator] mà bạn lấy từ [`ArrayList`][ArrayList], [`LinkedList`][LinkedList] và [`HashSet`][HashSet] đều hỗ trợ thao tác remove này.

## Cập nhật collection trong lúc đang iterate

Nếu bạn sửa nội dung của collection trong lúc đang iterate qua nó, bạn có thể nhận [`ConcurrentModificationException`][ConcurrentModificationException]. Exception này dễ gây bối rối, vì nó cũng được dùng trong concurrent programming. Trong ngữ cảnh Collections Framework, bạn có thể gặp nó mà **không** hề dính tới multithreading.

Đoạn code sau throw [`ConcurrentModificationException`][ConcurrentModificationException]:

```java
Collection<String> strings = new ArrayList<>();
strings.add("one");
strings.add("two");
strings.add("three");

Iterator<String> iterator = strings.iterator();
while (iterator.hasNext()) {

    String element = iterator.next();
    strings.remove(element);
}
```

Nếu điều bạn cần là xóa các phần tử thỏa một tiêu chí cho trước, hãy dùng method [`removeIf()`][removeIf].

## Implement interface Iterable

Giờ khi đã biết iterator là gì trong Collections Framework, bạn có thể tạo một implementation đơn giản của interface [`Iterable`][Iterable].

Giả sử bạn cần tạo một class `Range` mô hình hóa một dải số nguyên giữa hai giới hạn. Tất cả những gì cần làm là iterate từ số đầu tới số cuối.

Bạn có thể implement [`Iterable`][Iterable] bằng một `record` — tính năng được giới thiệu ở Java SE 16:

```java
// lower bound is included, upper bound is excluded
record Range(int start, int end) implements Iterable<Integer> {

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int index = start;

            @Override
            public boolean hasNext() {
                return index < end;
            }

            @Override
            public Integer next() {
                if (index >= end) {
                    throw new NoSuchElementException("" + index);
                }
                int currentIndex = index;
                index++;
                return currentIndex;
            }
        };
    }
}
```

Bạn cũng làm được điều tương tự với một class thường, trong trường hợp ứng dụng của bạn chưa hỗ trợ Java SE 16. Lưu ý code của implementation [`Iterator`][Iterator] là **y hệt**:

```java
class Range implements Iterable<Integer> {

    private final int start;
    private final int end;

    public Range(int start, int end) {
        this.start = start;
        this.end = end;
    }

    @Override
    public Iterator<Integer> iterator() {
        return new Iterator<>() {
            private int index = start;

            @Override
            public boolean hasNext() {
                return index < end;
            }

            @Override
            public Integer next() {
                if (index >= end) {
                    throw new NoSuchElementException("" + index);
                }
                int currentIndex = index;
                index++;
                return currentIndex;
            }
        };
    }
}
```

Trong cả hai trường hợp, bạn dùng được một instance `Range` trong câu lệnh for-each, vì nó implement [`Iterable`][Iterable]:

```java
for (int i : new Range(0, 5)) {
    IO.println("i = " + i);
}
```

Kết quả:

```text
i = 0
i = 1
i = 2
i = 3
i = 4
```

---

**Bài tập**

1. Chạy đoạn code gây `ConcurrentModificationException`, rồi sửa nó theo hai cách: (a) dùng `iterator.remove()`, (b) dùng `removeIf()`. Cách nào bạn thấy rõ ý định hơn?
2. Mở rộng `Range` thành `Range(int start, int end, int step)`. Cạm bẫy: `step` bằng 0 hoặc âm — bạn xử lý thế nào?
3. Đối chiếu với Go: `for i, v := range slice` không có `Iterator` object. Điều đó khiến việc "vừa lặp vừa xóa" trong Go khác Java ra sao?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[Iterable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html
[Iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html
[ArrayList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html
[LinkedList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html
[HashSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashSet.html
[iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#iterator()
[hasNext]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#hasNext()
[next]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#next()
[remove]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html#remove()
[removeIf]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html#removeIf(java.util.function.Predicate)
[NoSuchElementException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html
[UnsupportedOperationException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/UnsupportedOperationException.html
[ConcurrentModificationException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ConcurrentModificationException.html
