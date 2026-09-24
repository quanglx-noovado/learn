# Làm quen với cây phân cấp Collection

> Dịch từ [Getting to Know the Collection Hierarchy](https://dev.java/learn/api/collections-framework/organization/) — dev.java.

## Đừng bị mất phương hướng trong cây phân cấp Collection

Collections Framework được chia thành nhiều cây phân cấp (hierarchy) interface và class. Cái đầu tiên bạn cần hiểu là cây phân cấp của interface `Collection`.

![The Collection Interface Hierarchy](https://dev.java/assets/images/collections-framework/01_interfaces-hierarchy.png)

Lưu ý là một số interface đã bị bỏ bớt trong hình, bạn sẽ gặp chúng sau.

## Interface Iterable

Interface đầu tiên của cây phân cấp này là [`Iterable`][Iterable], và thực ra nó **không** thuộc Collections Framework. Vẫn đáng nhắc tới ở đây vì nó là super interface của [`Collection`][Collection], và do đó là của tất cả interface trong cây phân cấp này.

[`Iterable`][Iterable] được thêm vào từ Java SE 5 (2004). Một object implement [`Iterable`][Iterable] là object mà bạn có thể iterate qua. Nó được thêm vào ở Java SE 5 cùng với pattern code *for each*.

Có thể bạn đã quen với cách iterate qua các phần tử của một [`Collection`][Collection] như sau:

```java
Collection<String> collection = new ArrayList<>();
collection.add("Duke");
collection.add("loves");
collection.add("Java");

for (String element: collection) {
    IO.println(element);
}
```

Chạy đoạn code này cho kết quả:

```text
Duke
loves
Java
```

Có thể bạn đã biết rằng bạn iterate được qua bất kỳ collection nào theo pattern này, hoặc qua bất kỳ array nào. Hóa ra là **bất kỳ** instance của [`Iterable`][Iterable] đều dùng được ở đây.

Implement interface [`Iterable`][Iterable] rất dễ: tất cả những gì bạn cần làm là cung cấp một instance của một interface khác — [`Iterator`][Iterator] — mà bạn sẽ thấy ở phần sau.

## Lưu phần tử trong container với interface Collection

Tất cả các interface còn lại đều là chuyện lưu phần tử trong container.

Hai interface [`List`][List] và [`Set`][Set] cùng chia sẻ một hành vi chung, được mô hình hóa bởi interface [`Collection`][Collection]. Interface [`Collection`][Collection] mô hình hóa nhiều phép toán trên container chứa phần tử. Chưa đi vào chi tiết kỹ thuật (chưa!), đây là những gì bạn làm được với một [`Collection`][Collection]:

- thêm hoặc xóa phần tử;
- kiểm tra sự tồn tại của một phần tử cho trước;
- hỏi số phần tử đang chứa, hoặc collection này có rỗng hay không;
- xóa sạch nội dung.

Vì một [`Collection`][Collection] là một tập hợp các phần tử, interface [`Collection`][Collection] cũng định nghĩa các phép toán tập hợp:

- kiểm tra một tập có nằm trong tập khác (inclusion);
- hợp (union);
- giao (intersection);
- phần bù (complement).

Cuối cùng, [`Collection`][Collection] cũng mô hình hóa các cách truy cập phần tử khác nhau:

- bạn có thể iterate qua các phần tử của collection, thông qua một iterator;
- bạn có thể tạo một stream trên các phần tử đó, và stream này có thể chạy song song (parallel).

Tất nhiên tất cả các phép toán này cũng có ở [`List`][List] và [`Set`][Set]. Có thể ai đó sẽ hỏi: vậy khác biệt giữa một instance [`Collection`][Collection] thuần và một instance [`Set`][Set] hay [`List`][List] là gì?

## Mở rộng Collection thành List

Khác biệt giữa một [`List`][List] và một [`Collection`][Collection] là: [`List`][List] **ghi nhớ thứ tự** các phần tử đã được thêm vào.

Hệ quả đầu tiên: nếu bạn iterate qua các phần tử của một list, phần tử đầu tiên bạn nhận được là phần tử được thêm vào đầu tiên. Rồi tới phần tử thứ hai, và tiếp tục cho tới khi hết. Vậy thứ tự iterate luôn giống nhau, và được quyết định bởi thứ tự thêm vào. Bạn **không** có bảo đảm này với một [`Collection`][Collection] thuần, cũng không có với [`Set`][Set].

Hóa ra một số implementation của [`Set`][Set] trong Collections Framework tình cờ luôn iterate theo cùng một thứ tự. Đó có thể chỉ là hiệu ứng tình cờ. Trừ khi bạn dùng một implementation của [`Set`][Set] có bảo đảm thứ tự gặp phần tử (encounter order) ổn định, code của bạn **không nên** dựa vào hành vi này.

Hệ quả thứ hai, có lẽ không rõ ràng như cái đầu, là các phần tử của list có **index**. Hỏi một collection phần tử *đầu tiên* của nó là gì thì vô nghĩa. Hỏi một list phần tử đầu tiên thì có nghĩa, vì list ghi nhớ điều đó.

Các index đó được xử lý ra sao? Lại một lần nữa: đó là trách nhiệm của implementation. Vai trò đầu tiên của một interface là **đặc tả hành vi**, không phải nói implementation phải làm thế nào để đạt được hành vi đó.

Như bạn sẽ thấy, interface [`List`][List] thêm các phép toán mới vào [`Collection`][Collection]. Vì phần tử của list có index, bạn có thể làm những việc sau với index đó:

- lấy phần tử ở một index cụ thể, hoặc xóa nó;
- chèn một phần tử, hoặc thay thế một phần tử ở một vị trí cụ thể;
- lấy một dải (range) phần tử giữa hai index.

## Mở rộng Collection thành Set

Khác biệt giữa một [`Set`][Set] và một [`Collection`][Collection] là: bạn **không thể có phần tử trùng lặp** trong [`Set`][Set]. Bạn có thể có nhiều instance của cùng một class mà bằng nhau (equal) trong một [`Collection`][Collection], hoặc thậm chí cùng một instance xuất hiện nhiều lần. Điều đó không được phép trong [`Set`][Set]. Việc này được đảm bảo thế nào là trách nhiệm của implementation, bạn sẽ thấy sau trong tutorial này.

Một trong các hệ quả của hành vi này: **thêm một phần tử vào [`Set`][Set] có thể thất bại**.

Rồi bạn có thể tự hỏi: liệu có container nào vừa ngăn trùng lặp, vừa cho phần tử có index? Câu trả lời không đơn giản. Collections Framework cho bạn một implementation của [`Set`][Set] mà bạn sẽ luôn iterate theo cùng một thứ tự, nhưng các phần tử đó **không có index**, nên class này không implement [`List`][List].

Khác biệt hành vi này không mang lại phép toán mới nào cho interface [`Set`][Set].

## Sắp xếp phần tử của Set với SortedSet và NavigableSet

Interface [`Set`][Set] có hai phần mở rộng: [`SortedSet`][SortedSet] và [`NavigableSet`][NavigableSet].

Interface [`SortedSet`][SortedSet] giữ các phần tử được sắp theo thứ tự tăng dần. Lại một lần nữa, việc đảm bảo điều đó là trách nhiệm của implementation, như bạn sẽ thấy sau.

Để sắp xếp được, [`SortedSet`][SortedSet] cần **so sánh** các phần tử của bạn. Làm sao nó làm được? Java định nghĩa hai cơ chế chuẩn cho việc này:

- Phần tử của bạn implement interface [`Comparable`][Comparable] và cung cấp method [`compareTo()`][compareTo];
- Bạn đưa một [`Comparator`][Comparator] cho [`SortedSet`][SortedSet] để nó so sánh giúp.

Ngay cả khi phần tử của bạn đã là [`Comparable`][Comparable], bạn vẫn có thể đưa một [`Comparator`][Comparator] khi tạo [`SortedSet`][SortedSet]. Việc này hữu ích khi bạn cần sắp xếp theo một thứ tự khác với thứ tự đã hiện thực trong [`compareTo()`][compareTo].

**Khác biệt giữa *sorting* (sắp xếp) và *ordering* (giữ thứ tự) là gì?** Một [`List`][List] giữ phần tử theo thứ tự chúng được thêm vào, còn một [`SortedSet`][SortedSet] giữ chúng đã được sắp. *Sorting* nghĩa là phần tử đầu tiên bạn gặp khi đi qua set sẽ là phần tử nhỏ nhất, theo một logic so sánh cho trước. *Ordering* nghĩa là thứ tự bạn thêm phần tử vào list được giữ nguyên suốt vòng đời của list đó. Nên phần tử đầu tiên bạn gặp khi đi qua list là phần tử được thêm vào đầu tiên.

[`SortedSet`][SortedSet] thêm vài phép toán vào [`Set`][Set]. Đây là những gì bạn làm được với một [`SortedSet`][SortedSet]:

- Lấy phần tử nhỏ nhất của set bằng method [`first()`][first] và [`getFirst()`][getFirst].
- Lấy phần tử lớn nhất của set bằng method [`last()`][last] và [`getLast()`][getLast].
- Trích ra một [`headSet`][headSet] và một [`tailSet`][tailSet] gồm tất cả phần tử nhỏ hơn, hoặc lớn hơn hay bằng, một phần tử cho trước.

Iterate qua các phần tử của [`SortedSet`][SortedSet] sẽ đi từ phần tử nhỏ nhất tới lớn nhất.

[`NavigableSet`][NavigableSet] không thay đổi hành vi của [`SortedSet`][SortedSet]. Nó thêm vài phép toán rất hữu ích lên [`SortedSet`][SortedSet], trong đó có khả năng iterate theo thứ tự giảm dần. Bạn sẽ thấy chi tiết hơn sau.

---

**Bài tập**

1. Tự viết một class `DemNguoc implements Iterable<Integer>` đếm từ N về 1, rồi dùng nó trong `for each`. (Gợi ý: cần trả về một `Iterator<Integer>`.)
2. Cho một `TreeSet<String>` và một `ArrayList<String>` cùng nhận 5 chuỗi theo thứ tự lộn xộn. In ra và giải thích khác biệt *sorting* vs *ordering* bằng chính output của bạn.
3. Đối chiếu: Go không có interface `Set`. Nếu cần một set trong Go, người ta thường dùng gì? Điểm nào của Java `Set` mà cách làm trong Go không có?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[Iterable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html
[Iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html
[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[Set]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Set.html
[SortedSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html
[NavigableSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NavigableSet.html
[Comparable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html
[Comparator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html
[compareTo]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html#compareTo(T)
[first]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#first()
[getFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#getFirst()
[last]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#last()
[getLast]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#getLast()
[headSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#headSet(E)
[tailSet]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/SortedSet.html#tailSet(E)
