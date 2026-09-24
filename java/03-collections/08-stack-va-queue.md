# Lưu phần tử trong Stack và Queue

> Dịch từ [Storing Elements in Stacks and Queues](https://dev.java/learn/api/collections-framework/stacks-queues/) — dev.java.

## Định hướng trong cây phân cấp Queue

Java SE 5 thêm một interface mới vào Collections Framework: interface [`Queue`][Queue], được mở rộng tiếp ở Java SE 6 bởi interface [`Deque`][Deque]. Interface [`Queue`][Queue] là phần mở rộng của interface [`Collection`][Collection].

![The Queue Interface Hierarchy](https://dev.java/assets/images/collections-framework/02_queue-hierarchy.png)

## Push, pop và peek

Stack và queue là các data structure kinh điển trong ngành máy tính. Stack còn được gọi là LIFO stack, LIFO nghĩa là Last In, First Out (vào sau, ra trước). Queue được biết tới là FIFO: First In, First Out (vào trước, ra trước).

Các cấu trúc này rất đơn giản và cho bạn ba thao tác chính:

- *push(element)*: thêm một phần tử vào queue hoặc stack.
- *pop()*: lấy một phần tử ra khỏi **stack**, tức là phần tử được thêm vào **gần nhất**.
- *poll()*: lấy một phần tử ra khỏi **queue**, tức là phần tử được thêm vào **lâu nhất**.
- *peek()*: cho bạn xem phần tử mà bạn sẽ nhận được với *pop()* hoặc *poll()*, nhưng **không** lấy nó ra khỏi queue/stack.

Có hai lý do giải thích sự thành công của các cấu trúc này. Thứ nhất là sự **đơn giản**: ngay cả ở những ngày đầu của ngành máy tính, hiện thực chúng cũng đã dễ. Thứ hai là **tính hữu dụng**: rất nhiều thuật toán dùng stack trong phần hiện thực của mình.

## Mô hình hóa queue và stack

Collections Framework cho bạn hai interface để mô hình hóa queue và stack:

- interface [`Queue`][Queue] mô hình hóa một queue;
- interface [`Deque`][Deque] mô hình hóa một **double ended queue** (từ đó có cái tên). Bạn có thể push, pop, poll và peek phần tử ở **cả đuôi lẫn đầu** của một [`Deque`][Deque], khiến nó vừa là queue vừa là stack.

Stack và queue cũng được dùng rộng rãi trong concurrent programming. Các interface này được mở rộng tiếp bởi các interface khác, thêm những method hữu ích cho lĩnh vực đó: [`BlockingQueue`][BlockingQueue], [`BlockingDeque`][BlockingDeque] và [`TransferQueue`][TransferQueue] — nằm ở giao điểm giữa Collections Framework và concurrent programming trong Java, ngoài phạm vi tutorial này.

Cả [`Queue`][Queue] và [`Deque`][Deque] đều thêm hành vi cho ba thao tác cơ bản này để xử lý hai trường hợp biên (corner case):

- Queue có thể **đầy** và không nhận thêm phần tử được nữa.
- Queue có thể **rỗng** và không trả về phần tử nào cho thao tác *pop*, *poll* hay *peek*.

Câu hỏi cần trả lời là: implementation nên hành xử thế nào trong hai trường hợp đó?

## Mô hình hóa FIFO queue với Queue

Interface [`Queue`][Queue] cho bạn hai cách xử lý các trường hợp biên này: **throw exception**, hoặc **trả về một giá trị đặc biệt**.

Bảng các method mà [`Queue`][Queue] cung cấp:

| Thao tác | Method | Hành vi khi queue đầy hoặc rỗng |
|---|---|---|
| push | [`add(element)`][qAdd] | throw [`IllegalStateException`][IllegalStateException] |
| | [`offer(element)`][qOffer] | trả về `false` |
| poll | [`remove()`][qRemove] | throw [`NoSuchElementException`][NoSuchElementException] |
| | [`poll()`][qPoll] | trả về `null` |
| peek | [`element()`][qElement] | throw [`NoSuchElementException`][NoSuchElementException] |
| | [`peek()`][qPeek] | trả về `null` |

## Mô hình hóa LIFO stack và FIFO queue với Deque

Java SE 6 thêm interface [`Deque`][Deque] như một phần mở rộng của [`Queue`][Queue]. Tất nhiên các method định nghĩa trong [`Queue`][Queue] vẫn dùng được ở [`Deque`][Deque], nhưng [`Deque`][Deque] mang tới một **quy ước đặt tên mới**. Nên các method đó được nhân đôi trong [`Deque`][Deque] theo quy ước mới này.

Bảng các method định nghĩa trong [`Deque`][Deque] cho thao tác FIFO:

| Thao tác FIFO | Method | Hành vi khi queue đầy hoặc rỗng |
|---|---|---|
| push | [`addLast(element)`][dAddLast] | throw [`IllegalStateException`][IllegalStateException] |
| | [`offerLast(element)`][dOfferLast] | trả về `false` |
| poll | [`removeFirst()`][dRemoveFirst] | throw [`NoSuchElementException`][NoSuchElementException] |
| | [`pollFirst()`][dPollFirst] | trả về `null` |
| peek | [`getFirst()`][dGetFirst] | throw [`NoSuchElementException`][NoSuchElementException] |
| | [`peekFirst()`][dPeekFirst] | trả về `null` |

Và bảng các method định nghĩa trong [`Deque`][Deque] cho thao tác LIFO:

| Thao tác LIFO | Method | Hành vi khi queue đầy hoặc rỗng |
|---|---|---|
| push | [`addFirst(element)`][dAddFirst] | throw [`IllegalStateException`][IllegalStateException] |
| | [`offerFirst(element)`][dOfferFirst] | trả về `false` |
| pop | [`removeFirst()`][dRemoveFirst] | throw [`NoSuchElementException`][NoSuchElementException] |
| | [`pollFirst()`][dPollFirst] | trả về `null` |
| peek | [`getFirst()`][dGetFirst] | throw [`NoSuchElementException`][NoSuchElementException] |
| | [`peekFirst()`][dPeekFirst] | trả về `null` |

Quy ước đặt tên của [`Deque`][Deque] rất trực tiếp và giống với quy ước trong interface [`Queue`][Queue]. Có một khác biệt: thao tác peek được đặt tên [`getFirst()`][dGetFirst] và [`getLast()`][dGetLast] trong [`Deque`][Deque], còn trong [`Queue`][Queue] thì là [`element()`][qElement].

Hơn nữa, [`Deque`][Deque] cũng định nghĩa các method mà bạn mong đợi ở bất kỳ class queue hay stack nào:

- [`push(element)`][dPush]: thêm `element` cho trước vào **đầu** double ended queue. Method này throw [`IllegalStateException`][IllegalStateException] nếu deque không nhận được phần tử.
- [`pop()`][dPop]: xóa và trả về phần tử ở đầu deque. Method này throw [`NoSuchElementException`][NoSuchElementException] nếu không có phần tử nào để pop.
- [`poll()`][dPoll]: làm cùng việc đó ở đầu deque. Method này trả về `null` nếu không có phần tử nào để poll.
- [`peek()`][dPeek]: cho bạn xem phần tử ở đầu deque. Method này trả về `null` nếu không có phần tử nào để peek.

## Các implementation của Queue và Deque

Collections Framework cho bạn ba implementation của [`Queue`][Queue] và [`Deque`][Deque], ngoài phạm vi concurrent programming:

- [`ArrayDeque`][ArrayDeque]: implement cả hai. Implementation này được hậu thuẫn bởi một array. Capacity của class này **tự động tăng** khi phần tử được thêm vào. Nên implementation này luôn chấp nhận phần tử mới.
- [`LinkedList`][LinkedList]: cũng implement cả hai. Implementation này được hậu thuẫn bởi một linked list, khiến việc truy cập phần tử đầu và cuối rất hiệu quả. [`LinkedList`][LinkedList] luôn chấp nhận phần tử mới.
- [`PriorityQueue`][PriorityQueue]: chỉ implement [`Queue`][Queue]. Queue này dựa trên một **priority heap** giữ các phần tử được sắp theo thứ tự tự nhiên hoặc theo thứ tự do một [`Comparator`][Comparator] chỉ định. Đầu của queue này **luôn** là phần tử nhỏ nhất theo thứ tự đã chỉ định. Capacity tự động tăng khi thêm phần tử. Chèn object không implement [`Comparable`][Comparable] sẽ throw [`ClassCastException`][ClassCastException].

## Tránh xa class Stack

Có thể bạn thấy hấp dẫn khi dùng class [`Stack`][Stack] mà JDK cung cấp. Class này đơn giản để dùng và dễ hiểu. Nó có đúng ba method mong đợi: [`push(element)`][sPush], [`pop()`][sPop] và [`peek()`][sPeek], và thấy class này trong code khiến code hoàn toàn dễ đọc.

Hóa ra class này là phần mở rộng của class [`Vector`][Vector]. Vào thời trước khi Collections Framework ra đời, [`Vector`][Vector] là lựa chọn tốt nhất để làm việc với list. Dù [`Vector`][Vector] không bị deprecated, việc dùng nó **không được khuyến khích**. Việc dùng class [`Stack`][Stack] cũng vậy.

Class [`Vector`][Vector] là thread safe, và [`Stack`][Stack] cũng thế. Nếu bạn không cần thread safety, bạn có thể thay thế an toàn bằng [`Deque`][Deque] và [`ArrayDeque`][ArrayDeque]. Nếu bạn cần một stack thread-safe, hãy tìm hiểu các implementation của interface [`BlockingQueue`][BlockingQueue].

---

**Bài tập**

1. Dùng `ArrayDeque` viết một hàm kiểm tra dấu ngoặc cân bằng trong chuỗi `"({[]})"`. Đây là bài tập stack kinh điển.
2. Với `ArrayDeque` (capacity tự tăng), `add()` và `offer()` khác nhau ở đâu **trong thực tế**? Khi nào khác biệt đó mới quan trọng?
3. Dùng `PriorityQueue<String>` với `Comparator.comparingInt(String::length)` và kiểm tra: phần tử ở đầu queue là gì? Thứ tự khi bạn `forEach` có phải thứ tự sắp xếp không? (Cạm bẫy: **không**.)
4. Đối chiếu: Go làm stack bằng slice (`append` / `s[:len(s)-1]`). Ưu/nhược so với `Deque` của Java?

[Collection]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Collection.html
[Queue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html
[Deque]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html
[ArrayDeque]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/ArrayDeque.html
[LinkedList]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/LinkedList.html
[PriorityQueue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/PriorityQueue.html
[Stack]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html
[Vector]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Vector.html
[Comparable]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/Comparable.html
[Comparator]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Comparator.html
[BlockingQueue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/BlockingQueue.html
[BlockingDeque]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/BlockingDeque.html
[TransferQueue]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/concurrent/TransferQueue.html
[qAdd]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#add(E)
[qOffer]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#offer(E)
[qRemove]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#remove()
[qPoll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#poll()
[qElement]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#element()
[qPeek]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Queue.html#peek()
[dAddLast]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#addLast(E)
[dOfferLast]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#offerLast(E)
[dAddFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#addFirst(E)
[dOfferFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#offerFirst(E)
[dRemoveFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#removeFirst()
[dPollFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#pollFirst()
[dGetFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#getFirst()
[dGetLast]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#getLast()
[dPeekFirst]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#peekFirst()
[dPush]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#push(E)
[dPop]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#pop()
[dPoll]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#poll()
[dPeek]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Deque.html#peek()
[sPush]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html#push(E)
[sPop]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html#pop()
[sPeek]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/Stack.html#peek()
[IllegalStateException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/IllegalStateException.html
[NoSuchElementException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/util/NoSuchElementException.html
[ClassCastException]: https://docs.oracle.com/en/java/javase/26/docs/api/java.base/java/lang/ClassCastException.html
