# Lưu trữ dữ liệu bằng Collections Framework

> Dịch từ [Storing Data Using the Collections Framework](https://dev.java/learn/api/collections-framework/intro/) — dev.java.
> Thuật ngữ tiếng Anh được giữ nguyên (collection, map, interface, implementation...).

## Giới thiệu Collections Framework

Collections Framework là API được dùng nhiều nhất trong JDK. Bất kể bạn đang làm ứng dụng gì, gần như chắc chắn tới một lúc nào đó bạn sẽ cần lưu và xử lý dữ liệu trong memory.

Lịch sử của data structure gần như cũng lâu bằng lịch sử của ngành máy tính. Collections Framework chính là bản hiện thực (implementation) của những khái niệm về cách lưu, tổ chức và truy cập dữ liệu trong memory — những khái niệm đã được phát triển từ rất lâu trước khi Java ra đời. Và như bạn sẽ thấy, Collections Framework làm việc đó rất hiệu quả.

Collections Framework xuất hiện lần đầu ở Java SE 2, năm 1998, và từ đó tới nay đã được viết lại hai lần:

- ở Java SE 5, khi generics được thêm vào;
- ở Java 8, khi lambda expression được giới thiệu, cùng với default method trong interface.

Đó là hai bản cập nhật quan trọng nhất của Collections Framework tới thời điểm này. Nhưng thực tế thì gần như mỗi phiên bản JDK đều có thay đổi gì đó cho Collections Framework.

Trong phần này bạn sẽ học những data structure hữu ích nhất mà Collections Framework cung cấp, cùng với các pattern bạn sẽ dùng để xử lý dữ liệu trong ứng dụng của mình.

Điều đầu tiên cần biết: về mặt kỹ thuật, Collections Framework là **một tập hợp các interface** mô hình hóa các cách lưu dữ liệu khác nhau trong các loại container khác nhau. Sau đó framework cung cấp ít nhất một implementation cho mỗi interface. Biết các implementation này quan trọng ngang với biết các interface, và chọn đúng implementation phụ thuộc vào việc bạn cần làm gì với nó.

## Định hướng trong Collections Framework

Số lượng interface và class trong Collections Framework thoạt đầu có thể gây choáng. Đúng là có rất nhiều cấu trúc, cả class lẫn interface. Một số có tên tự giải thích, như [`LinkedList`][LinkedList]; một số mang theo hành vi, như [`ConcurrentHashMap`][ConcurrentHashMap]; một số nghe khá lạ, như [`ConcurrentSkipListMap`][ConcurrentSkipListMap].

Bạn sẽ dùng một số thành phần nhiều hơn hẳn các thành phần khác. Nếu bạn đã quen với Java, chắc bạn đã gặp [`List`][List], [`ArrayList`][ArrayList] và [`Map`][Map]. Tutorial này tập trung vào những cấu trúc được dùng rộng rãi nhất — những cái bạn dùng hằng ngày với vai trò một Java developer, và là những cái bạn cần hiểu rõ nhất.

Dù vậy, bạn vẫn cần có cái nhìn tổng quan về những gì Collections Framework có.

Trước hết, framework gồm **interface** và **implementation**. Chọn đúng interface nghĩa là bạn cần biết mình muốn đưa chức năng gì vào ứng dụng. Nhu cầu của bạn là:

- lưu object rồi iterate qua chúng?
- push object vào một queue rồi pop ra?
- lấy object ra thông qua một key?
- truy cập object theo index?
- sắp xếp chúng?
- ngăn phần tử trùng lặp, hoặc ngăn giá trị null?

Chọn đúng implementation nghĩa là bạn cần biết mình sẽ dùng các chức năng đó như thế nào:

- Truy cập object bằng cách iterate, hay truy cập ngẫu nhiên theo index?
- Các object có được xác định cố định ngay khi ứng dụng khởi động và ít thay đổi trong suốt vòng đời của nó?
- Bạn lưu một lượng lớn object? Bạn có thường xuyên cần kiểm tra sự tồn tại của một object nào đó?
- Cấu trúc bạn dùng có cần được truy cập đồng thời (concurrently)?

Collections Framework có giải pháp phù hợp cho tất cả các bài toán trên.

Có **hai nhóm interface chính** trong Collections Framework: collection và map.

**Collection** là chuyện lưu object và iterate qua chúng. Interface [`Collection`][Collection] là interface gốc của nhóm này. Thực tế [`Collection`][Collection] extends interface [`Iterable`][Iterable], nhưng bản thân `Iterable` không thuộc Collections Framework.

**Map** lưu một object cùng với một key đại diện cho object đó — giống như primary key đại diện cho một record trong database, nếu bạn quen khái niệm này. Đôi khi bạn sẽ nghe nói map lưu các cặp *key/value*, và đó chính xác là điều map làm. Interface [`Map`][Map] là interface gốc của nhóm này.

**Không có quan hệ trực tiếp** nào giữa các interface trong nhánh [`Collection`][Collection] và các interface trong nhánh [`Map`][Map].

Ngoài collection và map, bạn cũng cần biết rằng có các interface mô hình hóa queue và stack nằm trong nhánh [`Collection`][Collection]. Queue và stack thực chất không phải là chuyện iterate qua các object, nhưng vì chúng được đặt trong nhánh `Collection` nên hóa ra bạn vẫn iterate qua chúng được.

Còn một nhánh cuối bạn cần biết là nhánh [`Iterator`][Iterator]. Một iterator là object có thể iterate qua một collection các object, và nó là một phần của Collections Framework.

Vậy là: hai nhóm chính [`Collection`][Collection] và [`Map`][Map], một nhóm con [`Queue`][Queue], và một nhóm phụ [`Iterator`][Iterator].

## Tránh dùng các interface và implementation cũ

Collections Framework chỉ xuất hiện từ Java 2, nghĩa là trước đó cũng đã có "cuộc sống". Cuộc sống đó gồm một số class và interface vẫn còn trong JDK để giữ tương thích ngược (backward compatibility), nhưng bạn **không nên dùng nữa** trong ứng dụng của mình:

- [`Vector`][Vector] và [`Stack`][Stack]. Class [`Vector`][Vector] đã được sửa lại để implement interface [`List`][List]. Nếu bạn dùng vector trong môi trường không concurrent, bạn có thể thay thế an toàn bằng [`ArrayList`][ArrayList]. Class [`Stack`][Stack] extends [`Vector`][Vector] và nên được thay bằng [`ArrayDeque`][ArrayDeque] trong môi trường không concurrent.
- Class [`Vector`][Vector] dùng interface [`Enumeration`][Enumeration] để mô hình hóa iterator của nó. Interface này không nên dùng nữa: interface được ưu tiên hiện nay là [`Iterator`][Iterator].
- [`Hashtable`][Hashtable]: class này đã được sửa lại để implement interface [`Map`][Map]. Nếu bạn dùng nó trong môi trường không concurrent, có thể thay an toàn bằng [`HashMap`][HashMap]. Trong môi trường concurrent, dùng [`ConcurrentHashMap`][ConcurrentHashMap] để thay thế.

## Vì sao chọn collection thay vì array?

Bạn có thể tự hỏi tại sao phải mất công học Collections Framework khi cảm giác là nhét dữ liệu vào một array cũ kỹ là xong việc.

Sự thật là: nếu bạn đã có một giải pháp đơn giản, bạn nắm chắc nó, và nó đáp ứng đúng nhu cầu — thì cứ dùng nó!

Vậy collection làm được gì mà array không làm được?

- Collection theo dõi (track) số phần tử nó đang chứa.
- Dung lượng (capacity) của collection không bị giới hạn: bạn có thể thêm (gần như) bao nhiêu phần tử cũng được.
- Collection có thể kiểm soát phần tử nào được lưu vào. Ví dụ, bạn có thể ngăn không cho thêm phần tử null.
- Collection có thể được truy vấn xem một phần tử cho trước có tồn tại hay không.
- Collection cung cấp các phép toán như giao (intersect) hoặc gộp (merge) với một collection khác.

Đây chỉ là một phần nhỏ những gì collection làm được cho bạn. Thực tế, vì collection là một object và object thì có thể mở rộng, bạn có thể thêm bất kỳ phép toán nào bạn cần lên hầu hết các collection mà JDK cung cấp. Với array thì không làm được điều đó.

---

**Bài tập**

1. Viết một class nhỏ nhận vào `int[]` và trả về một `List<Integer>`, rồi so sánh: với array bạn cần bao nhiêu dòng code để "thêm một phần tử vào giữa"? Với `List` thì bao nhiêu?
2. Tìm trong javadoc: `ArrayList` có method nào cho biết số phần tử? Array dùng gì? Vì sao hai cái tên khác nhau (`size()` vs `length`)?
3. Đối chiếu với Go: Go không có `Collection` interface — slice của Go gần với `ArrayList` hay với array của Java hơn? Vì sao?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[Iterable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Iterable.html
[Iterator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Iterator.html
[List]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/List.html
[Map]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Map.html
[Queue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html
[ArrayList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayList.html
[LinkedList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html
[ArrayDeque]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayDeque.html
[HashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/HashMap.html
[Hashtable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Hashtable.html
[Vector]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Vector.html
[Stack]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html
[Enumeration]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Enumeration.html
[ConcurrentHashMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/ConcurrentHashMap.html
[ConcurrentSkipListMap]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/ConcurrentSkipListMap.html
