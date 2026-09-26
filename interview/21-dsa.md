# 21. Cấu trúc dữ liệu và thuật toán

> [← Mục lục](README.md) · Trọng tâm: **pattern giải bài easy/medium** và cấu trúc dữ liệu nằm trong DB, cache, queue hằng ngày; làm bài bằng **PHP 8**, đối chiếu Java/Go.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn.

File gồm hai phần:

1. **Lộ trình kiến thức** (phần chính): ba chặng từ nền tới senior. Mỗi module có:
   - **Vì sao cần học**: module này dùng vào việc gì và hay bị hỏi thế nào.
   - **Học gì**: các khái niệm, giải thích bằng lời thường kèm ví dụ, và các cạm bẫy ⚠️. Đọc phần
     này để biết cần học gì, rồi học sâu qua tài liệu ở mục Đọc.
   - **Đọc**: tài liệu gốc.
   - **Nắm chắc khi**: tiêu chí tự kiểm tra. Chỉ tick ô khi làm được điều đó mà không cần nhìn
     tài liệu.
2. **Câu hỏi thường gặp** (bonus): mỗi câu kèm hướng trả lời mong đợi, gồm ý phải có, điểm
   cộng senior và red flag. Dùng để kiểm tra sau khi học, không dùng để học thuộc.

Backend thường hỏi easy đến medium. Mục tiêu là **nhận ra pattern** và **nói được lý do**,
không phải học thuộc lời giải. Senior còn bị hỏi cấu trúc dữ liệu nằm ở đâu trong hệ thống
mình dùng, và bài toán khi dữ liệu không vừa một máy.

> **Luyện code chạy được** ở [`../dsa/`](../dsa/). Hiện mới có binary search
> (`dsa/go/searching/`, `dsa/java/BinarySearch.java`). Bài mới đặt theo quy ước sẵn có:
> Go ở `dsa/go/<chủ đề>/` (một package, kèm `*_test.go` table-driven, chạy `go test ./dsa/go/...`),
> Java ở `dsa/java/<Tên>.java` (test trong `main`, chạy `java dsa/java/<Tên>.java`).
> Cách học mỗi chủ đề (vẽ tay, cài thô, test ca biên, cài lại bằng ngôn ngữ thứ hai) ở
> [`../dsa/README.md`](../dsa/README.md).

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [NeetCode Roadmap](https://neetcode.io/roadmap) | Lộ trình + video | Thứ tự học pattern và danh sách NeetCode 150. **Dùng làm xương sống** để chọn bài |
| LeetCode (leetcode.com) | Nền tảng luyện bài | Nơi làm bài; tên bài trong file này là tên trên LeetCode. Hỗ trợ PHP |
| [Tech Interview Handbook](https://www.techinterviewhandbook.org/) | Hướng dẫn miễn phí | [Study cheatsheet](https://www.techinterviewhandbook.org/algorithms/study-cheatsheet/) theo từng cấu trúc, [Grind 75](https://www.techinterviewhandbook.org/grind75) khi ít thời gian |
| [*Algorithms*, 4th ed.](https://algs4.cs.princeton.edu/home/) (Sedgewick, Wayne) | Sách + site miễn phí | Giải thích từng cấu trúc có hình và code. Chương nào đọc ghi ở từng module |
| *Introduction to Algorithms* (CLRS), 4th ed. (MIT Press 2022) | Sách | Tra cứu khi cần chứng minh hoặc phân tích chặt. Không cần đọc hết |
| [VisuAlgo](https://visualgo.net/en) | Mô phỏng tương tác | Xem thuật toán chạy từng bước: sort, heap, BST, graph, union-find |
| [cp-algorithms](https://cp-algorithms.com/) | Bài viết | Union-find, segment tree, Fenwick, Dijkstra viết gọn và chính xác |
| [PHP SPL Data Structures](https://www.php.net/manual/en/spl.datastructures.php) | Official docs | Cấu trúc có sẵn trong PHP khi làm bài bằng PHP |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.5 | Phân tích Big-O, dùng đúng cấu trúc cơ bản trong PHP, giải easy trong 15 phút theo đúng quy trình | 2 tuần |
| **2. Làm chủ** 🟡 | 2.1–2.8 | Nhận ra pattern từ đề, giải medium trong 25–30 phút vừa code vừa nói | 5–6 tuần |
| **3. Senior** 🔴 | 3.1–3.4 | Nối cấu trúc dữ liệu với DB/cache/queue thật; giải bài "dữ liệu không vừa một máy" | 1–2 tuần |

Nhịp gợi ý cho người đi làm: khoảng 1 giờ mỗi ngày, 8–12 bài mỗi tuần theo thứ tự của NeetCode
Roadmap. Cuối tuần làm lại không nhìn các bài đã sai; bài sai làm lại sau 3 ngày và sau 1 tuần.
Tuần cuối dành cho mock interview (với bạn, hoặc tự ghi âm khi vừa code vừa nói).

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Big-O và ràng buộc đầu vào

**Vì sao cần học:** Sau mỗi lời giải, người phỏng vấn gần như luôn hỏi "độ phức tạp bao
nhiêu, vì sao". Trong công việc, Big-O giúp nhận ra đoạn code PHP chạy ổn với 100 dòng dữ liệu
test nhưng treo khi gặp 100.000 dòng thật, ví dụ `in_array` nằm trong một vòng `foreach`. Đọc
ràng buộc n trong đề còn cho biết ngay cần tìm lời giải cỡ nào.

**Học gì**

*Big-O là gì*
- *Big-O* mô tả thời gian chạy (hoặc bộ nhớ) **tăng nhanh thế nào khi kích thước input n
  tăng**, không phải số giây cụ thể.
  - Ví dụ: một vòng `foreach` qua n phần tử là O(n). Hai vòng lồng nhau, mỗi vòng qua n phần
    tử, là O(n²): n gấp 10 thì thời gian gấp khoảng 100.
- Khi tính thì bỏ hằng số và bỏ bậc thấp:
  - `3n + 5` viết là O(n).
  - `n² + n` viết là O(n²), vì khi n lớn thì n² áp đảo.
- *Time complexity* là độ phức tạp về thời gian. *Space complexity* là bộ nhớ phụ cần thêm,
  ngoài phần chứa input.
- ⚠️ Space tính cả *stack đệ quy*. Mỗi lời gọi đệ quy chưa trả về chiếm một khung trên stack.
  - Ví dụ: DFS trên *cây lệch* (mỗi node chỉ có một con, cây thành một đường thẳng) sâu n
    tầng, nên tốn O(n) bộ nhớ dù không tạo mảng nào.
- Nhiều input thì dùng nhiều biến: duyệt ma trận m×n là O(m·n), không phải O(n²).

*Best, average, worst case*
- Cùng một thuật toán có thể nhanh hay chậm tuỳ input:
  - *Best case*: input thuận lợi nhất.
  - *Average case*: trung bình trên các input thường gặp.
  - *Worst case*: input tệ nhất.
- Hai ví dụ hay bị hỏi:

  | | Average | Worst | Worst xảy ra khi |
  |---|---|---|---|
  | Quick sort | O(n log n) | O(n²) | Pivot luôn là phần tử nhỏ nhất hoặc lớn nhất (module 1.4) |
  | Hash map | O(1) | O(n) | Mọi key dồn vào cùng một chỗ (module 1.2) |

- Phỏng vấn mặc định hỏi worst case. Nói cả average và worst là điểm cộng.

*Hằng số vẫn quan trọng*
- Big-O bỏ hằng số, nhưng trên máy thật hằng số có thể chênh nhau nhiều lần.
- ⚠️ Duyệt array nhanh hơn duyệt linked list dù cùng O(n).
  - Array nằm liền nhau trong bộ nhớ, nên CPU nạp trước cả một khối vào *cache CPU* (bộ nhớ
    rất nhanh nằm cạnh CPU).
  - Các node của linked list nằm rải rác, lần nào cũng phải đi lấy từ RAM chậm hơn nhiều.

*Đọc ràng buộc n để đoán độ phức tạp*
- Ước lượng thô: máy chạy khoảng 10⁷–10⁸ thao tác đơn giản mỗi giây. PHP chậm hơn C++ nhiều
  lần, nên càng phải chọn đúng bậc.
- Đề thường ghi ràng buộc như `1 <= n <= 10^5`. Tra bảng để biết bậc nào chấp nhận được:

  | n cỡ | Chấp nhận được | Gợi ý hướng |
  |---|---|---|
  | ≤ 10–12 | O(n!) | hoán vị, backtracking |
  | ≤ 20–25 | O(2ⁿ) | subset, bitmask DP |
  | ≤ 500 | O(n³) | DP 3 chiều, Floyd–Warshall |
  | ≤ 5·10³ | O(n²) | DP 2 chiều, hai vòng lặp |
  | ≤ 10⁶ | O(n log n) | sort, heap, binary search |
  | ≤ 10⁸ | O(n) | một lượt duyệt, hash, two pointers |
  | lớn hơn | O(log n), O(1) | công thức, binary search |

- Ví dụ: n = 10⁵ thì O(n²) là 10¹⁰ thao tác, quá chậm. Phải tìm hướng O(n log n) hoặc O(n).

*Amortized (🟡)*
- *Amortized* là chi phí trung bình của mỗi thao tác khi tính trên cả một **chuỗi** thao tác.
  Đây không phải xác suất, cũng không phải "thường thì nhanh".
- Ví dụ kinh điển là *dynamic array*, tức mảng tự tăng kích thước (PHP array, Java
  `ArrayList`, Go slice). Khi append:
  1. Mảng còn chỗ trống thì chỉ ghi vào ô kế tiếp: O(1).
  2. Hết chỗ thì cấp vùng nhớ mới lớn gấp đôi (tăng theo **hệ số nhân**), rồi copy toàn bộ
     phần tử cũ sang: O(n) cho riêng lần đó.
  3. Vì mỗi lần gấp đôi, tổng số lần copy qua n lần append là 1 + 2 + 4 + ... + n, nhỏ hơn 2n.
     Chia đều cho n lần append thì mỗi lần trung bình O(1).
- ⚠️ Nếu tăng theo hằng số cộng (mỗi lần thêm 10 ô) thì cứ 10 lần append lại copy toàn bộ.
  Tổng thành O(n²), tức mỗi lần append là O(n).
- ⚠️ Amortized O(1) vẫn có lần chậm. Một lần resize mảng lớn là một *spike latency*: một
  request bỗng chậm hẳn so với các request khác.

**Đọc**
- Algorithms 4th: [1.4 Analysis of Algorithms](https://algs4.cs.princeton.edu/14analysis/)
- [Big-O Cheat Sheet](https://www.bigocheatsheet.com/): bảng độ phức tạp của cấu trúc và sort, in ra để dò
- CLRS ch.3 (Characterizing Running Times) và ch.16 (Amortized Analysis) nếu cần chặt chẽ

**Nắm chắc khi**
- [ ] Phân tích được time và space của lời giải vừa viết, kể cả stack đệ quy
- [ ] Chứng minh bằng lời vì sao n lần append vào dynamic array tổng chi phí là O(n)
- [ ] Nhìn ràng buộc n = 10⁵ nói ngay O(n²) không qua và gợi ý được hướng O(n log n)

#### 1.2 Array, string, hash map/set

**Vì sao cần học:** Hash map là công cụ dùng nhiều nhất trong bài phỏng vấn: rất nhiều bài
O(n²) thành O(n) chỉ nhờ một hash map. Với dev PHP, `array` chính là hash map, nên hiểu nó giúp
tránh các chỗ O(n) ẩn và bug key tự đổi kiểu. Câu hay bị hỏi: "vì sao hash map O(1)" và "khi
nào nó thành O(n)".

**Học gì**

*Array và dynamic array*
- *Array* là dãy ô nhớ nằm liền nhau. Biết chỉ số i là tính ra ngay địa chỉ ô, nên truy cập
  `a[i]` là O(1).
- Chèn hoặc xoá ở giữa là O(n), vì phải dịch mọi phần tử phía sau.
- *Dynamic array* là array tự tăng kích thước khi đầy (module 1.1): Java `ArrayList`, Go slice,
  PHP array dạng *packed* (khi key là 0, 1, 2... liên tục, xem module 2.8).

*Hash table hoạt động thế nào*
1. Có một mảng các ô, mỗi ô gọi là một *bucket*.
2. *Hàm hash* biến key thành một số, ví dụ `hash("alice") = 918273`.
3. Lấy số đó chia lấy dư cho số bucket để ra vị trí: `918273 % 8 = 1`, lưu vào bucket 1.
4. Tra cứu làm lại đúng các bước trên, không phải duyệt cả mảng, nên trung bình O(1).

- *Collision* (va chạm) là khi hai key khác nhau rơi vào cùng một bucket. Có hai cách xử lý:

  | | Chaining | Open addressing |
  |---|---|---|
  | Cách làm | Mỗi bucket giữ một danh sách các phần tử | Bucket đã có phần tử thì dò sang ô khác theo một quy tắc (*probing*, ví dụ ô kế tiếp) |
  | Khi xoá | Xoá khỏi danh sách | Không được để trống ô, phải đặt *tombstone* (dấu "ô này từng có phần tử") để lượt dò sau không dừng sai chỗ |
  | Ví dụ | Java `HashMap` | Go map (Swiss table, module 3.1) |

- *Load factor* = số phần tử / số bucket.
  - Load factor càng cao thì va chạm càng nhiều, tra càng chậm.
  - Vượt ngưỡng thì tạo mảng bucket lớn hơn và tính lại vị trí của mọi phần tử (*resize* và
    *rehash*), tốn O(n) cho lần đó. Java `HashMap` mặc định ngưỡng 0.75.

*Khi hash table thành O(n)*
- ⚠️ Hash kém, hoặc mọi key rơi vào cùng một bucket, thì tra cứu thành duyệt một danh sách dài:
  worst case O(n).
- ⚠️ *Hash flooding* là kiểu tấn công cố tình gửi hàng nghìn key có cùng hash (ví dụ tên các
  field POST), để server tốn O(n²) chỉ để dựng hash table, CPU bị chiếm hết. Hai cách phòng:
  - Hàm hash có *seed* ngẫu nhiên, kẻ tấn công không đoán được key nào sẽ va nhau.
  - Giới hạn số field trong request. PHP có `max_input_vars` vì lý do này.
- Java giảm worst case xuống O(log n) bằng cách đổi bucket quá dài thành cây red-black
  (module 3.1).

*Key mutable*
- ⚠️ Key *mutable* là object sửa được sau khi tạo. Nếu sửa field dùng để tính hash sau khi đã
  put vào map, hash đổi, map tìm ở bucket khác và không thấy lại phần tử.
- Java: override `equals` thì phải override `hashCode`. Hai object bằng nhau theo `equals` phải
  có cùng hash, nếu không map coi chúng là hai key khác nhau.

*Pattern dùng hash map/set*
- Bốn dạng hay gặp:
  - "Đã thấy phần tử này chưa".
  - Đếm tần suất.
  - Tìm cặp có tổng bằng k.
  - Nhóm theo một khoá.
- Ý tưởng chung: đổi O(n²) (so mọi cặp) thành O(n) bằng cách tốn thêm O(n) bộ nhớ.
- Ví dụ đếm tần suất trong PHP:

  ```php
  $count = [];
  foreach ($words as $w) {
      $count[$w] = ($count[$w] ?? 0) + 1;   // tra và cập nhật O(1)
  }
  ```

*String*
- ⚠️ PHP `strlen` và chỉ số `$s[$i]` tính theo **byte**, không theo ký tự. Chữ tiếng Việt có
  dấu chiếm nhiều byte trong UTF-8.
  - Ví dụ: `strlen('Việt')` là 6, còn `mb_strlen('Việt')` là 4.
  - Dùng `mb_strlen`, `mb_str_split` khi làm việc với ký tự.
- Go `len(s)` cũng đếm byte. Muốn duyệt từng ký tự (*rune*) thì dùng `for _, r := range s`.

*Bài luyện*
- Two Sum (E), Contains Duplicate (E), Valid Anagram (E)
- Group Anagrams (M), Top K Frequent Elements (M), Longest Consecutive Sequence (M), Encode and
  Decode Strings (M)

**Đọc**
- Tech Interview Handbook: [Array](https://www.techinterviewhandbook.org/algorithms/array/), [Hash table](https://www.techinterviewhandbook.org/algorithms/hash-table/), [String](https://www.techinterviewhandbook.org/algorithms/string/)
- Algorithms 4th: [3.4 Hash Tables](https://algs4.cs.princeton.edu/34hash/) (separate chaining, linear probing)
- VisuAlgo: [Hash Table](https://visualgo.net/en/hashtable)

**Nắm chắc khi**
- [ ] Vẽ được hash table có chaining và open addressing, chỉ ra khi nào resize
- [ ] Giải thích được vì sao hash map O(1) trung bình nhưng O(n) worst, và cách Java giảm worst xuống O(log n)
- [ ] Giải Two Sum, Group Anagrams, Longest Consecutive Sequence bằng PHP trong 15 phút mỗi bài

#### 1.3 Stack, queue, deque, linked list

**Vì sao cần học:** Queue và stack có mặt trong mọi hệ thống: queue job của Laravel, call stack
khi đọc stack trace. PHP có một bẫy hay gặp là dùng `array_shift` làm queue khiến BFS thành
O(n²). Linked list ít dùng trực tiếp, nhưng là một nửa của LRU cache, và bài linked list kiểm
tra khả năng xử lý con trỏ cẩn thận.

**Học gì**

*Stack, queue, deque*

| Cấu trúc | Nguyên tắc | Dùng vào việc gì |
|---|---|---|
| Stack | *LIFO* (last in, first out: vào sau ra trước), như chồng đĩa | Call stack, undo, parse biểu thức (khớp ngoặc), DFS không đệ quy |
| Queue | *FIFO* (first in, first out: vào trước ra trước), như xếp hàng | BFS, hàng đợi job |
| Deque | *Double-ended queue*: thêm và lấy được ở cả hai đầu | Sliding window maximum (module 2.2), *work stealing* (thread rảnh lấy việc từ cuối hàng đợi của thread khác) |

*Linked list*
- *Linked list* là chuỗi các node, mỗi node giữ một giá trị và con trỏ tới node kế tiếp. Các
  node nằm rải rác trong bộ nhớ.
- *Doubly linked list*: mỗi node có thêm con trỏ về node đứng trước.
- Đặc điểm:
  - Thêm hoặc xoá O(1) khi **đã có sẵn node** ở vị trí đó.
  - Truy cập phần tử thứ i là O(n), vì phải đi từ đầu.
  - Cache kém (module 1.1).
- Doubly linked list là một nửa của LRU cache. Nửa còn lại là hash map (module 2.8).

*Cạm bẫy theo ngôn ngữ*
- ⚠️ Java `LinkedList` hiếm khi nhanh hơn `ArrayList`. Làm stack hoặc queue thì `ArrayDeque`
  tốt hơn.
- ⚠️ PHP `array_shift` và `array_unshift` là O(n). Sau khi lấy phần tử đầu, PHP phải đánh lại
  chỉ số 0, 1, 2... cho mọi phần tử còn lại.
  - Hệ quả: BFS gọi `array_shift` trong vòng lặp là O(n²) ẩn.
  - Cách sửa: dùng `SplQueue`, hoặc giữ một chỉ số đầu hàng `$head` và tăng dần:

  ```php
  $queue = [$start];
  $head = 0;
  while ($head < count($queue)) {
      $node = $queue[$head++];      // O(1), không dịch mảng
      // ... thêm node kề bằng $queue[] = $next;
  }
  ```

*Kỹ thuật với linked list*
- *Dummy head*: tạo một node giả đứng trước node đầu. Nhờ vậy xoá hay chèn ở đầu danh sách
  giống hệt ở giữa, khỏi viết nhánh `if` riêng cho node đầu.
- Con trỏ nhanh/chậm: con chậm đi 1 bước, con nhanh đi 2 bước mỗi lượt.
  - Khi con nhanh tới cuối, con chậm đang ở giữa danh sách.
  - Nếu danh sách có vòng, con nhanh không bao giờ tới cuối mà sẽ đuổi kịp con chậm trong vòng.
- Hai con trỏ cách nhau n bước: cho con thứ nhất đi trước n bước, rồi cả hai cùng đi. Khi con
  đầu tới cuối, con sau đang ở phần tử thứ n tính từ cuối.

*Bài luyện*
- Stack: Valid Parentheses (E), Min Stack (M), Evaluate Reverse Polish Notation (M)
- Linked list: Reverse Linked List (E), Merge Two Sorted Lists (E), Linked List Cycle (E),
  Remove Nth Node From End of List (M), Reorder List (M)

**Đọc**
- Algorithms 4th: [1.3 Bags, Queues, and Stacks](https://algs4.cs.princeton.edu/13stacks/)
- Tech Interview Handbook: [Linked list](https://www.techinterviewhandbook.org/algorithms/linked-list/)
- VisuAlgo: [Linked List, Stack, Queue, Deque](https://visualgo.net/en/list)
- PHP: [SplStack](https://www.php.net/manual/en/class.splstack.php), [SplQueue](https://www.php.net/manual/en/class.splqueue.php), [array_shift](https://www.php.net/manual/en/function.array-shift.php)

**Nắm chắc khi**
- [ ] Viết được đảo linked list bằng vòng lặp và bằng đệ quy, nói space của từng cách
- [ ] Giải thích được vì sao con trỏ nhanh/chậm gặp nhau khi có vòng
- [ ] Chỉ ra được chỗ O(n²) ẩn trong một BFS bằng PHP dùng `array_shift` và sửa được

#### 1.4 Sort và binary search

**Vì sao cần học:** Hiếm khi phải tự viết sort, nhưng câu "merge sort khác quick sort thế nào"
và "stable là gì" rất hay gặp. Stable còn là chuyện thật trong PHP khi sort danh sách theo
nhiều cột. Binary search thì xuất hiện rất nhiều và rất dễ sai biên; biến thể "binary search
trên đáp án" là pattern medium hay gặp.

**Học gì**

*Các thuật toán sort*

| Thuật toán | Average | Worst | Bộ nhớ phụ | Stable |
|---|---|---|---|---|
| Insertion | O(n²) (best O(n)) | O(n²) | O(1) | có |
| Merge | O(n log n) | O(n log n) | O(n) | có |
| Quick | O(n log n) | O(n²) | O(log n) stack | không |
| Heap | O(n log n) | O(n log n) | O(1) | không |
| Counting / Radix | O(n + k) / O(d·(n + k)) | như average | O(n + k) | có |

- *Stable* nghĩa là các phần tử bằng nhau giữ nguyên thứ tự ban đầu. Cần khi sort nhiều lượt.
  - Ví dụ: danh sách đơn đã sort theo ngày. Sort tiếp theo trạng thái bằng sort stable thì
    trong cùng một trạng thái, các đơn vẫn theo thứ tự ngày. Sort không stable thì thứ tự ngày
    bị xáo.
- Merge sort chạy thế nào:
  1. Chia mảng làm đôi.
  2. Sort từng nửa (gọi đệ quy).
  3. Trộn hai nửa đã sort thành một, bằng hai con trỏ.
- Quick sort chạy thế nào:
  1. Chọn một phần tử làm *pivot*.
  2. *Phân hoạch* (partition): dồn phần tử nhỏ hơn pivot sang trái, lớn hơn sang phải.
  3. Gọi đệ quy cho hai bên.
- Giới hạn lý thuyết: sort dựa trên so sánh không thể nhanh hơn O(n log n) ở worst case.
  - Counting sort và radix sort vượt được vì không so sánh, mà đếm trực tiếp theo giá trị.
  - Chỉ dùng được khi miền giá trị nhỏ (k nhỏ), ví dụ tuổi từ 0 tới 150.

*Binary search*
- Tìm trong mảng đã sort: mỗi bước so với phần tử ở giữa rồi bỏ đi một nửa. O(log n).
- Chìa khoá là giữ một *bất biến* (điều luôn đúng sau mỗi vòng lặp) về khoảng đang tìm, và
  không trộn hai kiểu:
  - `[lo, hi]` đóng hai đầu: lặp `while (lo <= hi)`, thu hẹp bằng `hi = mid - 1`.
  - `[lo, hi)` nửa mở: lặp `while (lo < hi)`, thu hẹp bằng `hi = mid`.
- ⚠️ Tính `mid = lo + (hi - lo) / 2` thay cho `(lo + hi) / 2`, để `lo + hi` không bị tràn số
  với int 32-bit.
- ⚠️ Vòng lặp vô hạn: khi còn hai phần tử, `mid` làm tròn xuống bằng `lo`. Nếu nhánh đó gán
  `lo = mid` thì `lo` không bao giờ tăng.
- *lowerBound* là vị trí đầu tiên có giá trị ≥ x.
- *upperBound* là vị trí đầu tiên có giá trị lớn hơn hẳn x.
- Hai hàm này là nền của nhiều bài tìm biên.

*Sort trong thư viện chuẩn (🟡)*

| Hàm | Thuật toán | Stable |
|---|---|---|
| Java `Arrays.sort` với kiểu nguyên thuỷ | Dual-pivot quicksort | không |
| Java `Arrays.sort` với object | TimSort | có |
| Go `slices.Sort` / `sort.Sort` | pdqsort | không. Cần stable thì dùng `slices.SortStableFunc` / `sort.Stable` |
| PHP (`sort`, `usort`...) | | **có, từ PHP 8.0** (trước đó không) |

- ⚠️ Comparator (hàm so sánh hai phần tử) phải nhất quán:
  - Bắc cầu: a < b và b < c thì a < c.
  - Trả 0 khi hai phần tử bằng nhau.
  - Java TimSort gặp comparator sai có thể ném "Comparison method violates its general
    contract".
- PHP: dùng toán tử `<=>` (trả -1, 0 hoặc 1). Comparator trả `bool` đã deprecated từ PHP 8.0.

  ```php
  usort($orders, fn($a, $b) => $a['total'] <=> $b['total']);   // ĐÚNG
  usort($orders, fn($a, $b) => $a['total'] > $b['total']);     // SAI: trả bool, deprecated
  ```

*Binary search trên đáp án (🟡)*
- Dùng khi đề hỏi "giá trị nhỏ nhất sao cho làm được việc X", và đáp án *đơn điệu*: nếu x làm
  được thì mọi giá trị lớn hơn x cũng làm được.
- Cách làm:
  1. Viết hàm `feasible(x)`: trả true nếu với giá trị x thì làm được.
  2. Binary search x trên khoảng đáp án có thể, tìm x nhỏ nhất mà `feasible(x)` là true.
- Ví dụ backend: số queue worker ít nhất để xử lý hết 1 triệu job trong 1 giờ. Nhiều worker
  hơn thì chỉ xong sớm hơn, nên đáp án đơn điệu.

*Bài luyện*
- Binary Search (E), Search Insert Position (E), Find First and Last Position of Element (M)
- Search in Rotated Sorted Array (M), Find Minimum in Rotated Sorted Array (M)
- Trên đáp án: Koko Eating Bananas (M), Capacity To Ship Packages Within D Days (M)

**Đọc**
- Algorithms 4th: [ch.2 Sorting](https://algs4.cs.princeton.edu/20sorting/) (2.1 elementary, 2.2 mergesort, 2.3 quicksort)
- VisuAlgo: [Sorting](https://visualgo.net/en/sorting)
- Tech Interview Handbook: [Sorting and searching](https://www.techinterviewhandbook.org/algorithms/sorting-searching/)
- PHP: [RFC Make sorting stable](https://wiki.php.net/rfc/stable_sorting) (PHP 8.0), [usort](https://www.php.net/manual/en/function.usort.php)
- Go: [package slices](https://pkg.go.dev/slices) (mục `Sort`, `SortStableFunc`)
- Code trong repo: `dsa/go/searching/`, `dsa/java/BinarySearch.java` (có `lowerBound`)

**Nắm chắc khi**
- [ ] Viết merge sort và quick sort từ trí nhớ, nói được worst case của quick sort xảy ra khi nào
- [ ] Viết `lowerBound`/`upperBound` không lỗi biên, chạy test ca rỗng, một phần tử, toàn trùng
- [ ] Giải Koko Eating Bananas và giải thích vì sao đáp án đơn điệu
- [ ] Nói được sort của PHP 8, Java, Go có stable không

#### 1.5 Quy trình làm bài và edge case

**Vì sao cần học:** Người phỏng vấn chấm cách bạn làm việc, không chỉ code chạy đúng. Im lặng
code 20 phút rồi đưa ra lời giải sai thì trượt, dù đã gần đúng. Edge case và cạm bẫy riêng của
PHP là chỗ mất điểm dễ nhất.

**Học gì**

*Quy trình 7 bước*
1. Nhắc lại đề bằng lời của mình. Hỏi: kích thước input, đã sort chưa, có trùng/âm/rỗng không,
   output là gì khi không có đáp án.
2. Chạy tay một ví dụ nhỏ và một edge case.
3. Nói brute force (cách thô, thử mọi khả năng) và độ phức tạp của nó trước. Brute force đúng
   tốt hơn lời giải tối ưu dở dang.
4. Thống nhất hướng với người phỏng vấn rồi mới code.
5. Vừa code vừa nói. Đặt tên biến rõ. Tách hàm phụ.
6. Tự dò lại bằng ví dụ và edge case, sửa lỗi trước khi bị chỉ ra.
7. Nói time/space cuối cùng và hướng cải thiện.

*Checklist edge case*
- Mảng: rỗng, một hoặc hai phần tử, toàn giống nhau, đã sort, sort ngược.
- Số: âm, 0, giá trị cực đại của kiểu.
- Chuỗi: rỗng, khoảng trắng, hoa/thường, Unicode.
- Đáp án: không có đáp án, có nhiều đáp án.
- Cây: cây rỗng, cây lệch.
- Đồ thị: không liên thông (có phần không nối với phần còn lại), có chu trình, *self-loop*
  (cạnh đi từ một node về chính nó).

*Cạm bẫy khi code*
- *Off-by-one*: lệch một đơn vị ở biên.
  - `<` hay `<=`.
  - Độ dài đoạn `[l, r]` là `r - l + 1`.
- *Overflow* (tràn số):
  - Java `int` là 32-bit, tối đa khoảng 2,1 tỷ.
  - Go `int` là 64-bit nhưng vẫn tràn được.
  - ⚠️ **PHP int tràn thì tự thành float**, mất chính xác mà không báo lỗi:

    ```php
    var_dump(PHP_INT_MAX + 1);   // float(9.2233720368547758E+18)
    ```
- Sửa collection khi đang duyệt:
  - Java ném `ConcurrentModificationException`.
  - PHP `foreach` theo giá trị duyệt trên bản gốc lúc bắt đầu. Sửa mảng trong vòng lặp không
    ảnh hưởng lượt duyệt.
- Đệ quy sâu gây *stack overflow* (hết bộ nhớ stack) với cây lệch hoặc n lớn. Chuyển sang vòng
  lặp kèm một stack tự quản.
- Backtracking: thêm tham chiếu thay vì bản sao vào kết quả, về sau mảng tạm bị sửa làm hỏng
  kết quả đã lưu (module 2.6).
- Kỹ năng tâm lý khi làm bài: [25-interview-skills.md](25-interview-skills.md)

**Đọc**
- Tech Interview Handbook: [Coding interview techniques](https://www.techinterviewhandbook.org/coding-interview-techniques/) và [Coding interview cheatsheet](https://www.techinterviewhandbook.org/coding-interview-cheatsheet/)
- PHP: [Integers](https://www.php.net/manual/en/language.types.integer.php) (mục integer overflow), [mb_strlen](https://www.php.net/manual/en/function.mb-strlen.php)

**Nắm chắc khi**
- [ ] Ghi âm một lần giải bài easy, nghe lại thấy có đủ 7 bước và không im lặng quá 1 phút
- [ ] Với mỗi bài đã giải, liệt kê được 5 edge case trước khi chạy test
- [ ] Chỉ ra được 3 cạm bẫy riêng của PHP khi làm bài (int tràn thành float, byte và ký tự, `array_shift`)

---

### Chặng 2: Làm chủ 🟡

Mỗi pattern: **dấu hiệu** nhận ra → **khung** lời giải → bài tiêu biểu. Độ khó (E/M/H) theo
LeetCode. Bài đánh dấu (premium) cần tài khoản trả phí; NeetCode thường có bản tương đương miễn phí.

#### 2.1 Two pointers, sliding window, prefix sum

**Vì sao cần học:** Đây là nhóm pattern gặp nhiều nhất ở bài medium về mảng và chuỗi. Chúng
biến lời giải O(n²) (xét mọi cặp, mọi đoạn) thành O(n). Ngoài phỏng vấn, prefix sum chính là ý
tưởng của bảng tổng tích luỹ, giúp trả báo cáo doanh thu theo khoảng ngày bất kỳ mà không cộng
lại từ đầu.

**Học gì**

*Two pointers*
- Dùng hai chỉ số cùng duyệt mảng, thay cho hai vòng lặp lồng nhau.
- Dấu hiệu: mảng đã sort (hoặc sort được), tìm cặp hay bộ ba, kiểm tra palindrome, gộp hai dãy,
  lọc mảng tại chỗ.
- Hai kiểu:
  - Hai đầu tiến vào nhau: con trái ở đầu, con phải ở cuối. So sánh rồi dịch một trong hai.
    - Ví dụ tìm cặp có tổng k trên mảng đã sort: tổng nhỏ quá thì dịch con trái sang phải,
      lớn quá thì dịch con phải sang trái.
  - Cùng chiều (đọc/ghi): con đọc đi qua mọi phần tử, con ghi chỉ tiến khi giữ lại phần tử.
    Dùng để lọc mảng tại chỗ, không cần mảng phụ.

*Sliding window*
- *Window* (cửa sổ) là một đoạn liên tục `[l, r]` của mảng hoặc chuỗi.
- Dấu hiệu: đoạn con hoặc chuỗi con **liên tục** dài nhất/ngắn nhất thoả một điều kiện.
- Khung:
  1. Tăng `r` để mở rộng cửa sổ, cập nhật trạng thái (ví dụ bảng đếm ký tự).
  2. Nếu cửa sổ vi phạm điều kiện thì tăng `l` để co lại tới khi hợp lệ.
  3. Cập nhật đáp án.
- Mỗi phần tử vào cửa sổ một lần và ra một lần, nên tổng là O(n) dù có vòng `while` bên trong.
- ⚠️ Chỉ đúng khi điều kiện đơn điệu khi co/giãn: mở rộng chỉ làm "tệ hơn", co lại chỉ làm "tốt
  hơn".
  - Mảng có số âm thì thêm phần tử có thể làm tổng giảm, nên không biết lúc nào phải co.
  - Bài tổng có số âm thường phải dùng prefix sum.

*Prefix sum*
- *Prefix sum* là mảng tổng tích luỹ: `pre[i]` là tổng của i phần tử đầu tiên.
  - `pre[0] = 0` và `pre[i+1] = pre[i] + a[i]`.
  - Tổng đoạn `[l, r]` = `pre[r+1] - pre[l]`. Dựng mảng mất O(n), mỗi lần hỏi tổng đoạn O(1).
- Ví dụ: `a = [3, 1, 4, 1]` thì `pre = [0, 3, 4, 8, 9]`. Tổng đoạn `[1, 2]` là
  `pre[3] - pre[1] = 8 - 3 = 5`, đúng bằng `1 + 4`.
- Dấu hiệu: hỏi tổng đoạn nhiều lần, hoặc đếm đoạn con có tổng bằng k (kể cả khi có số âm).
- Kết hợp hash map: tổng một đoạn bằng k nghĩa là hiệu hai prefix bằng k. Dùng hash map đếm số
  lần đã gặp mỗi giá trị prefix trong lúc duyệt.

*Bài luyện*
- Two pointers: Valid Palindrome (E), Two Sum II (M), 3Sum (M), Container With Most Water (M),
  Trapping Rain Water (H)
- Sliding window: Best Time to Buy and Sell Stock (E), Longest Substring Without Repeating
  Characters (M), Longest Repeating Character Replacement (M), Permutation in String (M),
  Minimum Window Substring (H)
- Prefix sum: Range Sum Query - Immutable (E), Subarray Sum Equals K (M), Product of Array
  Except Self (M), Continuous Subarray Sum (M)

**Đọc**
- NeetCode Roadmap: nhánh *Two Pointers*, *Sliding Window*
- Tech Interview Handbook: [Array](https://www.techinterviewhandbook.org/algorithms/array/) (mục techniques: sliding window, two pointers, prefix sum)

**Nắm chắc khi**
- [ ] Đọc đề và nói trong 1 phút nên dùng window hay prefix sum, kèm lý do (có số âm không)
- [ ] Giải 3Sum không trùng bộ ba và giải thích cách bỏ trùng
- [ ] Giải Subarray Sum Equals K và giải thích vì sao sliding window sai ở bài này

#### 2.2 Monotonic stack và deque

**Vì sao cần học:** Pattern này ít gặp hơn, nhưng khi gặp mà chưa biết thì gần như không tự
nghĩ ra kịp trong 30 phút. Nhận ra dấu hiệu là đủ để qua phần lớn bài. Câu hay bị hỏi vặn: vì
sao có vòng `while` lồng trong `for` mà vẫn là O(n).

**Học gì**

*Dấu hiệu*
- "Phần tử lớn hơn (hoặc nhỏ hơn) gần nhất bên trái/bên phải".
- "Max hoặc min của mỗi cửa sổ trượt".

*Monotonic stack*
- *Monotonic stack* là stack mà các phần tử luôn giữ một thứ tự: tăng dần hoặc giảm dần từ đáy
  lên đỉnh.
- Khung:
  1. Duyệt từng phần tử.
  2. Trong khi phần tử mới phá thứ tự của stack thì pop đỉnh ra. **Lúc pop là lúc tìm được đáp
     án cho phần tử bị pop.**
  3. Push phần tử mới.
- Ví dụ tìm phần tử lớn hơn gần nhất bên phải với `[2, 1, 5]`:
  1. Push 2. Stack: `[2]`.
  2. 1 nhỏ hơn 2, không phá thứ tự, push. Stack: `[2, 1]`.
  3. 5 lớn hơn 1: pop 1, đáp án của 1 là 5. 5 lớn hơn 2: pop 2, đáp án của 2 là 5. Push 5.
  4. Hết mảng. 5 còn trong stack, tức không có phần tử lớn hơn bên phải.
- Vì sao O(n): mỗi phần tử được push đúng một lần và pop tối đa một lần. Cộng dồn mọi lượt thì
  vòng `while` chạy không quá n lần.

*Monotonic deque*
- Dùng cho max hoặc min của mỗi cửa sổ trượt.
- Deque giữ các ứng viên theo thứ tự giảm dần, nên đầu deque là max của cửa sổ hiện tại.
- Lưu **chỉ số** chứ không lưu giá trị, để biết phần tử nào ở đầu deque đã trượt ra khỏi cửa sổ.

*Bài luyện*
- Daily Temperatures (M), Next Greater Element I (E), Car Fleet (M)
- Sliding Window Maximum (H), Largest Rectangle in Histogram (H)

**Đọc**
- NeetCode Roadmap: nhánh *Stack*
- Tech Interview Handbook: [Queue](https://www.techinterviewhandbook.org/algorithms/queue/) và [Stack](https://www.techinterviewhandbook.org/algorithms/stack/)

**Nắm chắc khi**
- [ ] Giải thích được vì sao monotonic stack là O(n) dù có vòng `while` lồng trong `for`
- [ ] Giải Sliding Window Maximum bằng deque và nói vì sao lưu chỉ số thay vì giá trị

#### 2.3 Tree: DFS, BFS, BST, trie

**Vì sao cần học:** Cây có mặt khắp backend: index DB là B+tree, danh mục sản phẩm nhiều cấp,
cây comment, cây phân quyền. Bài cây chủ yếu kiểm tra khả năng viết đệ quy đúng. Câu hay hỏi:
validate BST, và vì sao cần cây cân bằng.

**Học gì**

*Thuật ngữ cơ bản*
- *Binary tree* (cây nhị phân): mỗi node có tối đa hai con, trái và phải.
- Node trên cùng là *root* (gốc). Node không có con là *lá*.
- *Chiều cao*: số tầng từ gốc xuống lá xa nhất.

*DFS trên cây*
- *DFS* (depth-first search) đi sâu hết một nhánh rồi mới quay lại nhánh khác. Trên cây thường
  viết bằng đệ quy.
- Khung: hàm đệ quy trả về thông tin của cây con (chiều cao, tổng, có hợp lệ không), rồi node
  cha gộp kết quả của hai con.

  ```php
  function countNodes(?TreeNode $node): int
  {
      if ($node === null) {
          return 0;                        // cây rỗng
      }
      return 1 + countNodes($node->left) + countNodes($node->right);   // gộp ở node cha
  }
  ```

*BFS theo tầng*
- *BFS* (breadth-first search) duyệt hết một tầng rồi mới xuống tầng dưới, dùng queue.
- Khung:
  1. Đưa gốc vào queue.
  2. Mỗi vòng ngoài: đếm số phần tử đang có trong queue (`count($queue)`), đó là số node của
     tầng hiện tại.
  3. Lấy ra đúng số đó, đưa con của chúng vào queue.

*BST*
- *BST* (binary search tree): với mọi node, mọi giá trị ở cây con trái < node < mọi giá trị ở
  cây con phải.
- Duyệt *in-order* (trái, node, phải) cho ra dãy tăng dần.
- ⚠️ Validate BST mà chỉ so node với hai con trực tiếp là sai.
  - Ví dụ: gốc 5, con trái 3, con phải của 3 là 6. Từng cặp cha con đều đúng, nhưng 6 nằm ở cây
    con trái của 5 là sai.
  - Cách đúng: truyền khoảng `(min, max)` hợp lệ từ tổ tiên xuống.
- ⚠️ Chèn dãy đã sort vào BST không cân bằng thì cây thành một đường thẳng như linked list, tìm
  kiếm thành O(n).

*Cây cân bằng*
- *Cây cân bằng* tự xoay lại (*rotation*) khi thêm hoặc xoá để chiều cao luôn là O(log n),
  tránh bẫy ở trên. Không cần cài phần xoay, nhưng cần biết vì sao phải cân bằng.

  | | AVL | Red-black |
  |---|---|---|
  | Mức cân bằng | Chặt | Lỏng: đường dài nhất ≤ 2 lần đường ngắn nhất |
  | Tìm | Nhanh hơn | Chậm hơn một chút |
  | Ghi | Xoay nhiều | Ít xoay hơn |
  | Dùng ở đâu | | Java `TreeMap`, bucket dạng cây của `HashMap`, scheduler của Linux (CFS trước đây; từ kernel 6.6 là EEVDF, vẫn dùng red-black tree) |

*Trie*
- *Trie* (prefix tree): cây mà mỗi cạnh là một ký tự, đường đi từ gốc xuống một node tạo thành
  một prefix.
  - Ví dụ: "cat" và "car" dùng chung nhánh `c → a`, rồi mới tách ra `t` và `r`.
- Tìm theo prefix mất O(L), với L là độ dài chuỗi, không phụ thuộc số từ đã lưu. Dùng cho
  autocomplete (module 3.4).
- ⚠️ Bảng chữ lớn (Unicode, tiếng Việt) thì lưu các con bằng map. Mảng cố định 26 ô chỉ hợp
  với a–z.

*Bài luyện*
- DFS/BFS: Maximum Depth of Binary Tree (E), Invert Binary Tree (E), Diameter of Binary Tree
  (E), Binary Tree Level Order Traversal (M), Lowest Common Ancestor of a Binary Tree (M),
  Binary Tree Maximum Path Sum (H)
- BST: Validate Binary Search Tree (M), Kth Smallest Element in a BST (M)
- Trie: Implement Trie (M), Design Add and Search Words Data Structure (M)

**Đọc**
- Algorithms 4th: [3.2 Binary Search Trees](https://algs4.cs.princeton.edu/32bst/), [3.3 Balanced Search Trees](https://algs4.cs.princeton.edu/33balanced/) (2-3 tree và red-black), [5.2 Tries](https://algs4.cs.princeton.edu/52trie/)
- VisuAlgo: [BST / AVL](https://visualgo.net/en/bst)
- Tech Interview Handbook: [Tree](https://www.techinterviewhandbook.org/algorithms/tree/), [Trie](https://www.techinterviewhandbook.org/algorithms/trie/)
- Linux: [EEVDF Scheduler](https://docs.kernel.org/scheduler/sched-eevdf.html) (đọc đoạn đầu để biết mốc 6.6)

**Nắm chắc khi**
- [ ] Viết được DFS trả về cặp giá trị (ví dụ chiều cao và đường kính) trong một lượt duyệt
- [ ] Viết BFS theo tầng bằng `SplQueue` trong PHP
- [ ] Giải thích được vì sao DB không dùng BST nhị phân làm index (nối sang module 3.1)

#### 2.4 Heap, top-K, interval

**Vì sao cần học:** Heap là cấu trúc đứng sau hàng đợi ưu tiên (job ưu tiên cao chạy trước),
top-K (top sản phẩm bán chạy) và bộ lập lịch. Interval là bài toán backend rất thật: kiểm tra
trùng lịch booking, lịch họp. Câu hay hỏi: vì sao top-K lớn nhất lại dùng min-heap.

**Học gì**

*Heap là gì*
- *Min-heap* là cây nhị phân mà mỗi node nhỏ hơn hoặc bằng các con, nên phần tử nhỏ nhất luôn
  ở gốc. *Max-heap* thì ngược lại.
- Heap là cây *gần đầy*: mọi tầng đều đầy, trừ tầng cuối được lấp từ trái sang. Nhờ vậy lưu
  gọn trong một mảng, không cần con trỏ: con của vị trí i là 2i+1 và 2i+2.
- Độ phức tạp:
  - Push và pop: O(log n), vì chỉ sửa thứ tự dọc một đường từ gốc tới lá.
  - Xem đỉnh: O(1).
  - Build heap từ một mảng có sẵn: O(n), không phải O(n log n).
- *Priority queue* (hàng đợi ưu tiên) là khái niệm "luôn lấy ra phần tử ưu tiên cao nhất". Heap
  là cách cài phổ biến nhất.

*Các pattern với heap*
- Top-K lớn nhất: giữ một **min-heap** kích thước k.
  1. Duyệt từng phần tử, push vào heap.
  2. Heap vượt k phần tử thì pop phần tử nhỏ nhất ra.
  3. Hết dữ liệu thì heap chứa đúng k phần tử lớn nhất.
  - Độ phức tạp O(n log k), bộ nhớ O(k).
- Trung vị của luồng dữ liệu: dùng hai heap, một giữ nửa nhỏ và một giữ nửa lớn.
- Merge K dãy đã sort: heap chứa phần tử đầu của mỗi dãy. Pop phần tử nhỏ nhất ra, đẩy phần tử
  kế tiếp của dãy đó vào. Đây cũng là pha 2 của external sort (module 3.3).

*Heap trong PHP*
- SPL có sẵn `SplMinHeap`, `SplMaxHeap`, `SplPriorityQueue`.
- `SplPriorityQueue` là **max-heap** theo priority: priority lớn ra trước.
- ⚠️ Các phần tử cùng priority trong `SplPriorityQueue` không đảm bảo ra theo thứ tự vào. Cần
  FIFO thì dùng priority dạng mảng `[p, -seq]`, với `seq` là số thứ tự tăng dần mỗi lần insert:

  ```php
  $pq = new SplPriorityQueue();
  $seq = 0;
  $pq->insert('job A', [5, -$seq++]);
  $pq->insert('job B', [5, -$seq++]);   // cùng priority 5, A vào trước nên -seq lớn hơn, ra trước
  ```

*Interval*
- *Interval* là một khoảng `[start, end]`, ví dụ khung giờ đặt phòng.
- Gộp các khoảng chồng nhau: sort theo điểm đầu, rồi quét từ trái sang và gộp dần.
- Đếm số phòng họp cần cùng lúc, có hai cách:
  - Min-heap theo điểm kết thúc (phòng nào trống sớm nhất).
  - Sort riêng mảng điểm đầu và mảng điểm cuối, rồi quét.
- ⚠️ Thống nhất biên đóng hay mở: `[1,2]` và `[2,3]` có tính là chồng nhau không.
- Backend thật là kiểm tra trùng booking. Hai khoảng a và b chồng nhau khi
  `a.start < b.end AND b.start < a.end`:

  ```sql
  SELECT 1 FROM bookings
  WHERE room_id = :room_id
    AND start_at < :new_end
    AND :new_start < end_at
  LIMIT 1;
  ```

*Bài luyện*
- Heap: Last Stone Weight (E), Kth Largest Element in an Array (M), K Closest Points to Origin
  (M), Task Scheduler (M), Merge k Sorted Lists (H), Find Median from Data Stream (H)
- Interval: Merge Intervals (M), Insert Interval (M), Non-overlapping Intervals (M), Meeting
  Rooms II (M, premium)

**Đọc**
- Algorithms 4th: [2.4 Priority Queues](https://algs4.cs.princeton.edu/24pq/)
- VisuAlgo: [Binary Heap](https://visualgo.net/en/heap)
- Tech Interview Handbook: [Heap](https://www.techinterviewhandbook.org/algorithms/heap/), [Interval](https://www.techinterviewhandbook.org/algorithms/interval/)
- PHP: [SplPriorityQueue](https://www.php.net/manual/en/class.splpriorityqueue.php), [SplMinHeap](https://www.php.net/manual/en/class.splminheap.php)

**Nắm chắc khi**
- [ ] Giải thích được vì sao top-K lớn nhất dùng min-heap chứ không phải max-heap
- [ ] Chứng minh bằng lời vì sao build heap là O(n) chứ không phải O(n log n)
- [ ] Giải Find Median from Data Stream bằng `SplMinHeap` + `SplMaxHeap` trong PHP

#### 2.5 Graph: BFS/DFS, topological sort, union-find, shortest path

**Vì sao cần học:** Nhiều bài không trông giống graph (lưới đảo, khoá học phụ thuộc nhau, gộp
tài khoản trùng) nhưng thực chất là graph. Backend dùng graph ở thứ tự chạy migration, DAG job,
phụ thuộc giữa các service. Kỹ năng bị chấm là dựng được graph từ đề bài và chọn đúng thuật
toán.

**Học gì**

*Graph là gì và cách biểu diễn*
- *Graph* gồm các *node* (đỉnh) và các *cạnh* nối chúng. Ký hiệu V là số node, E là số cạnh.
  - Cạnh có thể *có hướng* (A phụ thuộc B) hoặc *vô hướng* (A là bạn của B).
  - Cạnh có thể có *trọng số*: khoảng cách, chi phí, thời gian.
- Ba cách biểu diễn:

  | | Adjacency list | Adjacency matrix | Edge list |
  |---|---|---|---|
  | Là gì | Mỗi node giữ danh sách node kề, PHP: `$adj[$u][] = $v` | Bảng V×V, ô `[u][v]` là 1 nếu có cạnh | Danh sách các bộ `(u, v, w)` |
  | Bộ nhớ | O(V + E) | O(V²) | O(E) |
  | Hợp khi | Đồ thị *thưa* (ít cạnh so với V²), tức hầu hết bài thực tế | Cần kiểm tra "có cạnh u-v không" trong O(1) | Kruskal (thuật toán cây khung nhỏ nhất, cần sort cạnh theo trọng số) |

- Lưới (ma trận ô) là graph ngầm: mỗi ô là một node, nối với các ô kề. Không cần dựng adjacency
  list, chỉ cần mảng hướng (module 2.8).

*BFS và DFS trên graph*
- Khác với cây, graph có thể có vòng. Cần tập `visited` để không đi lại node cũ.
- ⚠️ Đánh dấu `visited` **khi đưa vào queue**, không phải khi lấy ra. Nếu đợi lúc lấy ra mới
  đánh dấu, một node có thể bị nhiều node kề đưa vào queue nhiều lần.
- BFS nhiều nguồn: đưa mọi nguồn vào queue ngay từ đầu, để chúng cùng lan ra một lúc.

*Topological sort*
- *Topological sort* sắp các node của đồ thị có hướng sao cho mọi cạnh `u → v` thì u đứng
  trước v. Chỉ làm được khi đồ thị không có chu trình. Đồ thị như vậy gọi là *DAG* (directed
  acyclic graph).
- Thuật toán Kahn:
  1. Tính *in-degree* (số cạnh đi vào) của mỗi node.
  2. Đưa mọi node có in-degree 0 (không phụ thuộc ai) vào queue.
  3. Lấy một node ra, thêm vào kết quả, giảm in-degree của các node nó trỏ tới. Node nào về 0
     thì đưa vào queue.
  4. Hết queue mà số node đã xử lý < V thì đồ thị có chu trình.
- Backend thật: thứ tự chạy migration, DAG job (Airflow), dependency resolver.

*Union-find*
- *Union-find* (còn gọi là *disjoint set union*, DSU) quản lý các nhóm rời nhau, với hai thao
  tác:
  - `find(x)`: x thuộc nhóm nào (trả về phần tử đại diện của nhóm).
  - `union(x, y)`: gộp nhóm của x và nhóm của y.
- Hai tối ưu giúp mỗi thao tác gần O(1) amortized (chính xác là O(α(n)), với α là hàm tăng cực
  chậm, không quá 4 với mọi n thực tế):
  - *Path compression*: khi `find`, nối thẳng mọi node trên đường đi vào phần tử đại diện.
  - *Union by rank/size*: luôn gắn cây nhỏ vào dưới cây lớn.
- ⚠️ Không tách nhóm được: chỉ có gộp, không có thao tác đưa một phần tử ra khỏi nhóm.
- Dùng khi: gộp tài khoản trùng, đếm số nhóm liên thông, tìm cạnh tạo ra chu trình.

*Shortest path*

| Tình huống | Thuật toán | Độ phức tạp |
|---|---|---|
| Không trọng số | BFS | O(V + E) |
| Trọng số không âm | Dijkstra với min-heap | O((V + E) log V) |
| Có cạnh âm | Bellman-Ford | O(V·E) |
| Mọi cặp node, V nhỏ | Floyd–Warshall | O(V³) |

- Dijkstra chạy thế nào:
  1. Lấy ra node gần nguồn nhất mà chưa chốt, chốt khoảng cách của nó.
  2. Cập nhật khoảng cách của các node kề nếu đi qua node vừa chốt thì ngắn hơn.
  3. Lặp tới khi hết node.
- ⚠️ Dijkstra sai với cạnh âm: node đã chốt thì không xét lại, nhưng một cạnh âm tìm thấy sau
  có thể làm đường tới node đó ngắn hơn.
- ⚠️ Heap của thư viện (kể cả `SplPriorityQueue`) không có *decrease-key* (giảm priority của
  một phần tử đang nằm trong heap). Cách làm:
  - Cứ push thêm một bản mới với khoảng cách mới, để bản cũ nằm lại trong heap.
  - Khi pop ra một bản mà khoảng cách của nó lớn hơn giá trị tốt nhất đã biết thì bỏ qua.

*Bài luyện*
- BFS/DFS: Number of Islands (M), Clone Graph (M), Rotting Oranges (M), Pacific Atlantic Water
  Flow (M), Word Ladder (H)
- Topological sort: Course Schedule (M), Course Schedule II (M), Alien Dictionary (H, premium)
- Union-find: Number of Provinces (M), Redundant Connection (M), Accounts Merge (M)
- Shortest path: Network Delay Time (M), Path With Minimum Effort (M), Cheapest Flights Within
  K Stops (M)

**Đọc**
- Algorithms 4th: [4.1 Undirected Graphs](https://algs4.cs.princeton.edu/40graphs/), [4.2 Directed Graphs](https://algs4.cs.princeton.edu/42digraph/) (topological sort), [1.5 Union-Find](https://algs4.cs.princeton.edu/15uf/), [4.4 Shortest Paths](https://algs4.cs.princeton.edu/44sp/)
- cp-algorithms: [Disjoint Set Union](https://cp-algorithms.com/data_structures/disjoint_set_union.html), [Dijkstra](https://cp-algorithms.com/graph/dijkstra.html), [Topological sort](https://cp-algorithms.com/graph/topological-sort.html)
- VisuAlgo: [DFS/BFS](https://visualgo.net/en/dfsbfs), [Union-Find](https://visualgo.net/en/ufds), [SSSP](https://visualgo.net/en/sssp)
- Tech Interview Handbook: [Graph](https://www.techinterviewhandbook.org/algorithms/graph/)

**Nắm chắc khi**
- [ ] Dựng được graph từ đề dạng chữ (Course Schedule, Accounts Merge) và chọn đúng BFS/DFS/topo/union-find
- [ ] Vẽ được đồ thị 3–4 node có cạnh âm làm Dijkstra ra sai
- [ ] Viết union-find có path compression và union by size trong 10 phút

#### 2.6 Backtracking và greedy

**Vì sao cần học:** Backtracking là cách có hệ thống để liệt kê mọi khả năng (tổ hợp, hoán vị,
cách chia) khi n nhỏ. Greedy cho lời giải ngắn nhưng rất dễ sai, và người phỏng vấn hay hỏi "sao
bạn biết greedy đúng". Hai dạng này còn kiểm tra bạn hiểu copy và tham chiếu của mảng trong
ngôn ngữ mình dùng.

**Học gì**

*Backtracking*
- *Backtracking*: thử một lựa chọn rồi đi tiếp. Khi đi hết, hoặc thấy nhánh này sai, thì quay
  lại bỏ lựa chọn đó và thử lựa chọn khác.
- Dấu hiệu: đề yêu cầu liệt kê mọi tổ hợp, hoán vị hoặc cách chia, và n nhỏ.
- Khung `choose → explore → unchoose`:

  ```
  function backtrack(trạng thái):
      if trạng thái là một đáp án: lưu BẢN SAO của trạng thái; return
      for lựa chọn in các lựa chọn còn lại:
          if lựa chọn chắc chắn không dẫn tới đáp án: continue   // cắt nhánh
          chọn                                                 // choose
          backtrack(trạng thái mới)                            // explore
          bỏ chọn                                              // unchoose
  ```

- *Cắt nhánh* (pruning): dừng sớm nhánh chắc chắn không ra đáp án, ví dụ tổng đã vượt target.
- Bỏ đáp án trùng khi input có phần tử lặp:
  1. Sort input trước.
  2. Ở cùng một tầng đệ quy, bỏ qua phần tử bằng phần tử ngay trước nó.
- ⚠️ Thứ thêm vào kết quả phải là bản sao:
  - PHP array gán là copy (copy-on-write, module 2.8) nên `$result[] = $cur` an toàn.
  - Java/Go phải copy tay: `new ArrayList<>(cur)`, `append([]int{}, cur...)`. Quên copy thì mọi
    phần tử trong kết quả cùng trỏ vào một list, và cuối cùng đều giống nhau.

*Greedy*
- *Greedy* (tham lam): ở mỗi bước chọn cái tốt nhất lúc đó, không bao giờ quay lại xét lại.
- Dấu hiệu: chọn cục bộ tốt nhất mà không cần quay lại, thường sau khi sort.
- Khung:
  1. Đề xuất một tiêu chí chọn.
  2. **Lập luận** vì sao không có lời giải nào tốt hơn. Cách hay dùng là *exchange argument*:
     giả sử có lời giải tối ưu khác cách chọn của mình, chỉ ra có thể đổi dần nó thành lời giải
     greedy mà không tệ đi.
- ⚠️ Không chứng minh được thì thử tìm phản ví dụ. Nhiều bài trông như greedy nhưng phải dùng
  DP, ví dụ Coin Change với mệnh giá bất kỳ.

*Bài luyện*
- Backtracking: Subsets (M), Permutations (M), Combination Sum (M), Generate Parentheses (M),
  Word Search (M), N-Queens (H)
- Greedy: Maximum Subarray (M, Kadane), Jump Game (M), Gas Station (M), Partition Labels (M)

**Đọc**
- NeetCode Roadmap: nhánh *Backtracking*, *Greedy*
- Tech Interview Handbook: [Recursion](https://www.techinterviewhandbook.org/algorithms/recursion/)
- VisuAlgo: [Recursion Tree](https://visualgo.net/en/recursion)

**Nắm chắc khi**
- [ ] Viết Subsets II (có trùng) và giải thích điều kiện bỏ trùng ở cùng tầng
- [ ] Đưa được phản ví dụ cho greedy ở Coin Change với mệnh giá `[1, 3, 4]`, tổng 6

#### 2.7 Dynamic programming

**Vì sao cần học:** DP là chủ đề nhiều người sợ nhất, nhưng ở mức medium chỉ cần khung 4 bước
và vài dạng quen thuộc. Ngoài phỏng vấn, `diff` (và `git diff`) dựa trên LCS, còn gợi ý sửa lỗi
chính tả thường dùng edit distance. Hay bị hỏi: định nghĩa trạng thái là gì, và độ phức tạp.

**Học gì**

*DP là gì và nhận ra thế nào*
- *Dynamic programming* (DP, quy hoạch động): chia bài toán thành các bài toán con, và **lưu
  kết quả** của mỗi bài toán con để không phải tính lại.
  - Ví dụ: Fibonacci đệ quy thô `f(n) = f(n-1) + f(n-2)` tính đi tính lại `f(3)` rất nhiều lần,
    tổng O(2ⁿ). Lưu lại kết quả mỗi `f(i)` thì chỉ còn O(n).
- Dấu hiệu:
  - Đề hỏi **số cách**, **min/max**, hoặc **có/không**.
  - Lựa chọn ở mỗi bước ảnh hưởng tới các bước sau.
  - Viết đệ quy thô thì thấy cùng một bài toán con bị gọi lại nhiều lần.

*Khung 4 bước*
1. Định nghĩa `dp[i]` **bằng lời**, ví dụ "`dp[i]` là chi phí nhỏ nhất để xử lý i job đầu tiên".
2. Viết công thức chuyển: `dp[i]` tính từ các `dp` nhỏ hơn thế nào.
3. Chọn giá trị cơ sở, ví dụ `dp[0]`.
4. Chọn thứ tự tính, sao cho khi tính `dp[i]` thì mọi giá trị nó cần đã có.

- Lộ trình viết lời giải:
  1. Đệ quy thô.
  2. *Memoization* (top-down): đệ quy như cũ, nhưng lưu kết quả vào mảng hoặc map.
  3. *Bottom-up*: vòng lặp điền bảng từ bài nhỏ tới bài lớn, không đệ quy.
  4. Tối ưu bộ nhớ: nếu mỗi hàng chỉ cần hàng trước thì chỉ giữ hàng trước.

*Các dạng hay gặp*
- 1D: trạng thái theo một chỉ số.
- 2D:
  - Lưới: `dp[i][j]` cho ô ở hàng i, cột j.
  - Hai chuỗi: `dp[i][j]` xét i ký tự đầu của chuỗi A và j ký tự đầu của chuỗi B.
- *Knapsack* (bài cái túi): chọn vật bỏ vào túi có dung lượng giới hạn.
  - *0/1 knapsack*: mỗi vật dùng tối đa một lần. Dùng mảng 1D thì duyệt dung lượng **ngược**,
    từ lớn về nhỏ.
  - *Unbounded knapsack*: mỗi vật dùng bao nhiêu lần cũng được, duyệt **xuôi**.
- *LCS* (longest common subsequence, dãy con chung dài nhất):
  - Hai ký tự đang xét bằng nhau: `dp[i][j] = dp[i-1][j-1] + 1`.
  - Khác nhau: `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`.
  - Ứng dụng thật: `diff`.

*Cạm bẫy*
- ⚠️ Độ phức tạp = số trạng thái × chi phí mỗi lần chuyển. Bảng n×n mà mỗi ô lại duyệt thêm n
  phần tử thì là O(n³), không phải O(n²).
- ⚠️ PHP memoization bằng array lồng nhau tốn bộ nhớ hơn nhiều so với C++/Java. Đệ quy sâu thì
  chuyển sang bottom-up.

*Bài luyện*
- 1D: Climbing Stairs (E), House Robber (M), Coin Change (M), Word Break (M), Longest
  Increasing Subsequence (M), Decode Ways (M)
- 2D: Unique Paths (M), Longest Common Subsequence (M), Edit Distance (M)
- Knapsack: Partition Equal Subset Sum (M), Target Sum (M), Coin Change II (M)

**Đọc**
- Tech Interview Handbook: [Dynamic programming](https://www.techinterviewhandbook.org/algorithms/dynamic-programming/)
- NeetCode Roadmap: nhánh *1-D DP*, *2-D DP*
- CLRS ch.14 (Dynamic Programming): rod cutting và LCS
- [MIT 6.006 Spring 2020](https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/): các lecture về dynamic programming (khung SRTBOT)

**Nắm chắc khi**
- [ ] Với 5 bài DP, viết được định nghĩa trạng thái bằng một câu tiếng Việt trước khi code
- [ ] Chuyển Coin Change từ memoization sang bottom-up và nói space trước/sau
- [ ] Giải thích được vì sao 0/1 knapsack mảng 1D phải duyệt ngược

#### 2.8 Bit, matrix, thiết kế cấu trúc dữ liệu, cấu trúc có sẵn trong PHP

**Vì sao cần học:** Module gom các dạng nhỏ nhưng hay gặp. Phần quan trọng nhất với người làm
PHP là cách `array` và SPL hoạt động bên trong: vì sao `in_array` chậm, vì sao key `"1"` thành
`1`, khi nào array bị copy. Đây là câu hay bị hỏi khi bạn chọn làm bài bằng PHP, và cũng là
nguồn bug thật trong code Laravel.

**Học gì**

*Bit manipulation*
- Số nguyên được lưu dưới dạng dãy bit. Các phép `&` (and), `|` (or), `^` (xor), `<<` và `>>`
  (dịch trái, dịch phải) thao tác trực tiếp trên bit.
- Các mẹo hay dùng:
  - `x ^ x = 0` và `x ^ 0 = x`: xor mọi phần tử thì các cặp giống nhau triệt tiêu nhau.
  - `x & (x - 1)` xoá bit 1 thấp nhất. Ví dụ: 12 là `1100`, 11 là `1011`, `12 & 11` là `1000`
    (8).
  - `x & -x` lấy riêng bit 1 thấp nhất. Ví dụ: `12 & -12` là `0100` (4).
  - Kiểm tra bit thứ i: `(x >> i) & 1`.
- ⚠️ Dịch phải số âm:
  - Java có `>>` (giữ bit dấu) và `>>>` (điền 0 vào bên trái).
  - PHP int là 64-bit có dấu, chỉ có `>>` giữ dấu, không có `>>>`.
- Backend:
  - Bit flag quyền: `READ = 1`, `WRITE = 2`, `DELETE = 4`. Kiểm tra bằng
    `($perm & WRITE) !== 0`.
  - *Bitmap*: mỗi bit đại diện cho một user. Redis `SETBIT`/`BITCOUNT` dùng để lưu điểm danh
    hằng ngày, 1 triệu user chỉ tốn khoảng 125 KB mỗi ngày.

*Matrix*
- Dùng mảng hướng `dirs = [[0,1],[1,0],[0,-1],[-1,0]]` để đi sang 4 ô kề bằng một vòng lặp, thay
  cho 4 đoạn `if`.
- Kiểm tra biên trước khi truy cập: `0 <= r < rows` và `0 <= c < cols`.
- Tiết kiệm bộ nhớ: dùng hàng đầu và cột đầu của chính ma trận làm cờ đánh dấu, để chỉ tốn O(1)
  bộ nhớ phụ.

*Thiết kế cấu trúc dữ liệu*
- Dạng bài: yêu cầu mọi thao tác đều O(1) hoặc O(log n). Thường phải ghép hai cấu trúc, mỗi cái
  lo một thao tác.
- *LRU cache* (least recently used: khi đầy thì bỏ phần tử lâu nhất không được dùng):
  - Hash map từ key tới node, để tìm O(1).
  - Doubly linked list giữ thứ tự dùng. Mỗi lần get hoặc put thì chuyển node lên đầu. Đầy thì
    bỏ node cuối. Cả hai việc đều O(1) vì đã có sẵn node trong tay.
  - Java có sẵn `LinkedHashMap` với `accessOrder=true`.
- ⚠️ PHP array giữ thứ tự chèn, nên LRU làm được rất gọn:

  ```php
  unset($cache[$key]);                          // xoá rồi chèn lại để đưa xuống cuối (mới dùng nhất)
  $cache[$key] = $value;
  if (count($cache) > $capacity) {
      unset($cache[array_key_first($cache)]);   // phần tử đầu là lâu nhất không dùng
  }
  ```

  Người phỏng vấn thường vẫn yêu cầu tự cài linked list.

*Array của PHP bên trong*
- PHP `array` là một *ordered hash map*: hash table có nhớ thứ tự chèn. Cùng một kiểu này dùng
  làm list, map, set và stack.
- Khi key là 0 tới n-1 liên tục, PHP dùng *packed array*: không lưu hash, ít bộ nhớ hơn.
- ⚠️ Key tự đổi kiểu:
  - Key string dạng số nguyên (`"1"`) tự chuyển thành int `1`.
  - Key float bị cắt phần thập phân (`1.7` thành `1`), hành vi này deprecated từ PHP 8.1.
- ⚠️ `in_array` là O(n) vì duyệt từng phần tử. Tra thành viên thì dùng key: `isset($set[$k])`
  là O(1).
  - `isset` trả false khi giá trị là `null`. Cần phân biệt "không có key" với "có key nhưng giá
    trị null" thì dùng `array_key_exists`.

  ```php
  $set = array_flip($ids);          // giá trị thành key, dựng một lần O(n)
  if (isset($set[$id])) { /* ... */ }   // O(1) mỗi lần tra
  ```
- ⚠️ *Copy-on-write* (chỉ copy khi ghi):
  1. Gán `$b = $a` hoặc truyền array vào hàm: chưa copy gì, hai biến dùng chung một vùng nhớ.
  2. Khi **sửa** một bên: lúc này PHP mới copy toàn bộ, tốn O(n).
  3. Hệ quả: truyền array lớn vào hàm đệ quy rồi sửa nó trong mỗi lần gọi là O(n²) ẩn. Dùng
     tham chiếu `&` hoặc object.
- ⚠️ `sort` đánh lại key từ 0. Muốn giữ key thì dùng `asort`, `ksort`, `uasort`.
- PHP không có TreeMap (map tự sắp theo key). Cần thì sort key, hoặc tự cài.

*SPL và extension ds*
- *SPL* (Standard PHP Library) có sẵn trong PHP:
  - `SplStack`, `SplQueue`: đều dựa trên `SplDoublyLinkedList`.
  - `SplMinHeap`, `SplMaxHeap`, `SplPriorityQueue` (module 2.4).
  - `SplFixedArray`: mảng kích thước cố định, key chỉ là số nguyên, ít bộ nhớ hơn array.
  - `SplObjectStorage`: set hoặc map với key là object.
- Extension `ds` (php-ds) có `Vector`, `Deque`, `Map`, `Set`, `PriorityQueue`, nhanh và ít bộ
  nhớ hơn, nhưng phải cài qua PECL.
  - ⚠️ Nền tảng phỏng vấn online thường không có, đừng phụ thuộc.
- ⚠️ Đệ quy sâu:
  - PHP không có *tail-call optimization* (tối ưu biến lời gọi đệ quy ở cuối hàm thành vòng
    lặp để không tốn thêm stack).
  - Từ PHP 8.3, vượt `zend.max_allowed_stack_size` thì ném `Error` thay vì segfault.

*Bài luyện*
- Bit: Single Number (E), Number of 1 Bits (E), Counting Bits (E), Missing Number (E), Sum of
  Two Integers (M)
- Matrix: Rotate Image (M), Spiral Matrix (M), Set Matrix Zeroes (M), Valid Sudoku (M)
- Thiết kế: LRU Cache (M), Time Based Key-Value Store (M), LFU Cache (H)

**Đọc**
- Tech Interview Handbook: [Binary](https://www.techinterviewhandbook.org/algorithms/binary/), [Matrix](https://www.techinterviewhandbook.org/algorithms/matrix/)
- PHP: [Arrays](https://www.php.net/manual/en/language.types.array.php) (mục key casts), [SPL Data Structures](https://www.php.net/manual/en/spl.datastructures.php), [SplFixedArray](https://www.php.net/manual/en/class.splfixedarray.php), [SplObjectStorage](https://www.php.net/manual/en/class.splobjectstorage.php), [Data Structures (ds)](https://www.php.net/manual/en/book.ds.php), [php-ds/ext-ds](https://github.com/php-ds/ext-ds)
- Nikita Popov: [PHP's new hashtable implementation](https://www.npopov.com/2014/12/22/PHPs-new-hashtable-implementation.html) (cấu trúc bên trong của array PHP 7+, packed array)

**Nắm chắc khi**
- [ ] Cài LRU cache bằng hash map + doubly linked list tự viết, get/put O(1), có test
- [ ] Giải thích được `$a = $b; $a[] = 1;` tốn bao nhiêu bộ nhớ và khi nào copy xảy ra
- [ ] Đổi một BFS/heap viết bằng array thuần sang SPL và nói độ phức tạp thay đổi thế nào
- [ ] Chỉ ra được kết quả của `$a = ["1" => 'x', 1 => 'y'];` và vì sao

---

### Chặng 3: Senior 🔴

#### 3.1 Cấu trúc dữ liệu bên trong hệ thống thật

**Vì sao cần học:** Senior bị hỏi cấu trúc dữ liệu ở góc "hệ thống bạn dùng hằng ngày làm thế
nào": vì sao index MySQL là B+tree, Redis sorted set dùng gì, Redis bỏ key nào khi đầy bộ nhớ.
Trả lời được chứng tỏ bạn hiểu vì sao hệ thống nhanh hay chậm, không chỉ biết giải bài.

**Học gì**

*Hash table trong runtime*

| Ngôn ngữ | Cài đặt | Điểm đáng nhớ |
|---|---|---|
| Java `HashMap` | Chaining | Bucket quá dài được chuyển sang red-black tree, worst case còn O(log n) |
| Go map | Từ Go 1.24 là *Swiss table*: open addressing theo nhóm, dò cả một nhóm ô cùng lúc | Thứ tự duyệt cố ý ngẫu nhiên, đừng dựa vào thứ tự |
| PHP `array` | Hash table có thứ tự | Giữ thứ tự chèn (module 2.8) |

*B-tree và B+tree*
- *B-tree*: cây mà mỗi node chứa nhiều key và có nhiều con. Mỗi node vừa đúng một *page* đĩa
  (khối DB đọc mỗi lần, InnoDB là 16 KB). Vì mỗi node có hàng trăm con nên cây rất thấp.
- *B+tree*: biến thể chỉ lưu dữ liệu ở lá. Các lá nối với nhau, nên range scan và `ORDER BY`
  chỉ cần đi dọc các lá, rất rẻ.
- Dùng trong InnoDB, PostgreSQL, nhiều file system. Chi tiết ở
  [03-database-sql.md](03-database-sql.md).

*LSM tree*
- *LSM tree* (log-structured merge tree), dùng trong RocksDB, Cassandra. Cách ghi:
  1. Ghi vào *memtable*, một bảng đã sắp xếp nằm trong RAM. Rất nhanh.
  2. Memtable đầy thì *flush*: ghi tuần tự ra đĩa thành một file đã sort.
  3. Chạy nền *compaction*: gộp các file nhỏ thành file lớn, bỏ các bản ghi cũ và đã xoá.
- Khi đọc, một key có thể nằm ở nhiều file. *Bloom filter* (module 3.2) của từng file giúp bỏ
  qua file chắc chắn không chứa key.
- So sánh:

  | | B+tree | LSM tree |
  |---|---|---|
  | Ghi | Sửa tại chỗ trong page, ghi ngẫu nhiên | Ghi tuần tự, rất nhanh |
  | Đọc | Tốt: một đường từ gốc tới lá | Chậm hơn: có thể phải xem nhiều file |
  | Hợp khi | Đọc nhiều | Ghi rất nhiều (log, event, time series) |

- Ba loại *amplification* (khuếch đại) dùng để so sánh hai loại:
  - *Read amplification*: một lần đọc logic tốn bao nhiêu lần đọc đĩa. LSM cao hơn.
  - *Write amplification*: một byte app ghi làm đĩa ghi thật bao nhiêu byte. B+tree ghi cả
    page cho một thay đổi nhỏ; LSM ghi lại dữ liệu nhiều lần qua các lượt compaction.
  - *Space amplification*: dung lượng đĩa thật so với dữ liệu hữu ích. LSM giữ bản cũ tới khi
    compaction dọn.

*Skip list*
- *Skip list*: nhiều tầng linked list chồng lên nhau.
  - Tầng dưới cùng chứa mọi phần tử theo thứ tự.
  - Mỗi tầng trên chứa ngẫu nhiên khoảng một nửa số phần tử của tầng dưới, như làn cao tốc để
    nhảy xa.
- Tìm: đi ở tầng cao nhất tới khi bước tiếp theo sẽ vượt quá, rồi xuống tầng dưới. O(log n) kỳ
  vọng.
- So với cây cân bằng: cài đơn giản hơn, không phải xoay, dễ làm concurrent.
- Redis sorted set dùng skip list kèm hash table (bản nhỏ dùng *listpack*, một dãy byte liền
  nhau rất gọn cho tập ít phần tử). Java có
  `ConcurrentSkipListMap`. Xem [04-nosql-search-storage.md](04-nosql-search-storage.md).

*Radix tree*
- *Radix tree*: trie nén, nhánh nào chỉ có một con thì gộp lại thành một cạnh chứa cả chuỗi.
  - Ví dụ: `/users/` và `/users/:id` dùng chung một cạnh `/users/`.
- Dùng trong router HTTP (httprouter, Gin) để match path, và longest prefix match của bảng định
  tuyến IP.

*LRU trong cache thật*
- Redis dùng LRU/LFU **xấp xỉ** để tiết kiệm bộ nhớ: không giữ linked list cho mọi key, mà khi
  cần bỏ key thì lấy mẫu vài key và bỏ key tệ nhất trong mẫu.
- ⚠️ Một LRU dùng chung cho nhiều thread với một lock chung thành nút cổ chai, vì mỗi lần get
  cũng phải sửa danh sách nên phải lấy lock. Phải chia *shard*: nhiều LRU nhỏ, mỗi cái một lock.
  Xem [11-cache.md](11-cache.md).

*Cấu trúc khác*
- *Segment tree*, *Fenwick tree*: truy vấn tổng đoạn và cập nhật một phần tử, cả hai O(log n).
  - Ít gặp trong phỏng vấn backend.
  - Mảng không đổi thì prefix sum (module 2.1) là đủ.
- Graph trong backend: dependency giữa service/job/migration, cây tổ chức cho phân quyền.

**Đọc**
- DDIA (Kleppmann, số chương theo bản 1) ch.3 *Storage and Retrieval*: hash index, SSTable/LSM, B-tree
- Redis: [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/)
- Go blog: [Faster Go maps with Swiss Tables](https://go.dev/blog/swisstable)
- Java: [HashMap](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/HashMap.html) (phần implementation notes về treeified bin)
- cp-algorithms: [Segment Tree](https://cp-algorithms.com/data_structures/segment_tree.html), [Fenwick Tree](https://cp-algorithms.com/data_structures/fenwick.html) (chỉ đọc nếu còn thời gian)

**Nắm chắc khi**
- [ ] Nói được trong 2 phút vì sao index DB dùng B+tree mà không dùng hash hay BST nhị phân
- [ ] So sánh được B+tree và LSM theo read/write/space amplification
- [ ] Giải thích được vì sao Redis sorted set chọn skip list thay vì cây cân bằng

#### 3.2 Cấu trúc xác suất và consistent hashing

**Vì sao cần học:** Khi dữ liệu lớn, đếm chính xác tốn quá nhiều bộ nhớ. Cấu trúc xác suất đổi
một chút sai số lấy bộ nhớ nhỏ hơn rất nhiều: đếm unique visitor, chống cache penetration.
Consistent hashing là câu kinh điển ở vòng system design khi chia dữ liệu cho nhiều node cache.

**Học gì**

*Bloom filter*
- *Bloom filter* gồm một mảng bit và k hàm hash. Nó chỉ trả lời "chắc chắn không có" hoặc "có
  thể có".
- Cách hoạt động:
  1. Thêm x: tính k hash của x, bật k bit tương ứng lên 1.
  2. Kiểm tra y: tính k hash của y.
     - Có bit nào là 0 thì y chắc chắn chưa từng được thêm.
     - Mọi bit đều là 1 thì chỉ là "có thể có", vì các bit đó có thể do phần tử khác bật.
- ⚠️ Có *false positive* (báo có mà thật ra không), không có *false negative* (báo không mà
  thật ra có).
- ⚠️ Bản cơ bản không xoá được: tắt một bit có thể làm mất phần tử khác dùng chung bit đó.
  *Counting bloom filter* thay mỗi bit bằng một bộ đếm nên xoá được, nhưng tốn bộ nhớ hơn.
- Tỉ lệ false positive phụ thuộc số bit, số hàm hash và số phần tử.
  - Chọn kích thước theo n dự kiến.
  - Khoảng 9.6 bit mỗi phần tử cho tỉ lệ 1%.
- Dùng trong:
  - LSM tree (module 3.1).
  - Chống *cache penetration*: request liên tục hỏi key không tồn tại, lần nào cũng trượt cache
    và đập thẳng vào DB.
  - Kiểm tra nhanh username/URL đã có chưa.

*HyperLogLog*
- *HyperLogLog* đếm xấp xỉ số phần tử khác nhau, với bộ nhớ cố định không phụ thuộc số phần tử.
- Redis: `PFADD`, `PFCOUNT`, `PFMERGE`. Sai số chuẩn 0.81%, tối đa 12KB mỗi key.
- Ví dụ: đếm unique visitor mỗi ngày của từng trang.
  - Set chính xác phải lưu mọi user ID, bộ nhớ tăng theo số user.
  - HyperLogLog luôn tối đa 12KB. `PFMERGE` gộp các ngày thành số của cả tuần.

*Count-Min Sketch*
- *Count-Min Sketch* đếm tần suất xấp xỉ. Nó là một bảng nhỏ gồm vài hàng bộ đếm, mỗi hàng một
  hàm hash.
  - Thêm x: tăng bộ đếm ứng với x ở mỗi hàng.
  - Hỏi tần suất của x: lấy giá trị nhỏ nhất qua các hàng.
- Chỉ đếm dư, không đếm thiếu, vì va chạm chỉ cộng thêm vào bộ đếm.
- Dùng tìm *heavy hitter*: phần tử xuất hiện nhiều nhất trong một luồng lớn, ví dụ IP gọi API
  nhiều nhất.

*Consistent hashing*
- Vấn đề với `hash(key) % N`: thêm hoặc bớt một node thì N đổi, gần như mọi key đổi sang node
  khác. Với cache, đó là gần hết cache bị trượt cùng lúc.
- Cách làm của consistent hashing:
  1. Hash cả node và key lên cùng một vòng tròn số.
  2. Key thuộc node đầu tiên gặp khi đi theo chiều kim đồng hồ.
  3. Thêm một node: chỉ các key nằm giữa node mới và node đứng trước nó chuyển sang node mới,
     khoảng 1/N số key.
- *Virtual node*: mỗi node thật đặt nhiều điểm trên vòng, để key chia đều hơn.
- ⚠️ Redis Cluster **không** dùng vòng consistent hashing. Nó dùng 16384 hash slot cố định, mỗi
  slot được gán cho một node. Xem [14-distributed-systems.md](14-distributed-systems.md).

**Đọc**
- Redis: [HyperLogLog](https://redis.io/docs/latest/develop/data-types/probabilistic/hyperloglogs/), [Bloom filter](https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/), [Count-min sketch](https://redis.io/docs/latest/develop/data-types/probabilistic/count-min-sketch/), [Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/) (mục key distribution model)
- [Bloom filter calculator](https://hur.st/bloomfilter/): nhập n và tỉ lệ false positive để ra số bit và số hash
- DDIA ch.6 *Partitioning*: phần hash partitioning và vì sao không dùng `hash % N`

**Nắm chắc khi**
- [ ] Tính được bộ nhớ bloom filter cho 1 tỷ phần tử với false positive 1% (bài tập 3)
- [ ] Giải thích được vì sao bloom filter không có false negative
- [ ] Vẽ được vòng consistent hashing, thêm một node và chỉ ra key nào di chuyển

#### 3.3 Dữ liệu không vừa một máy

**Vì sao cần học:** Câu dạng "tìm top 10 URL trong file log 1 TB" hay gặp ở vòng senior. Người
phỏng vấn chấm cách chia nhỏ, đánh đổi chính xác lấy bộ nhớ, và việc nhận ra công cụ có sẵn
(DB, Redis, Spark, `sort` của Unix). Trong PHP đây cũng là bài toán thật khi import/export file
CSV lớn mà không vượt `memory_limit`.

**Học gì**

*Top-K trên dữ liệu không vừa RAM*
1. Chia dữ liệu theo `hash(x) % N` thành N file. Cùng một giá trị luôn vào cùng một file, nên
   đếm trong từng file là chính xác.
2. Với từng file (đủ nhỏ để vừa RAM): đếm bằng hash map, lấy top-K bằng min-heap.
3. Gộp N danh sách top-K thành top-K cuối cùng.

- ⚠️ Không thể chia **ngẫu nhiên** rồi gộp top-K của mỗi phần: một phần tử đứng thứ K+1 ở mọi
  phần có thể là top toàn cục khi cộng lại.
- Luồng liên tục (không có file để chia): Count-Min Sketch kèm heap (xấp xỉ), hoặc đếm theo cửa
  sổ thời gian.

*Đếm phần tử khác nhau*
- Chính xác: dùng set, hoặc `COUNT(DISTINCT)` trong hệ *OLAP* (DB chuyên cho truy vấn phân tích
  trên dữ liệu lớn).
- Xấp xỉ: HyperLogLog (module 3.2).
- Hỏi lại yêu cầu: báo cáo tài chính cần chính xác, dashboard chấp nhận sai số 1%.

*Dedup 1 tỷ URL*
- Ước lượng trước: 1 tỷ × ~100 byte ≈ 100GB, không vừa RAM một máy thường.
- Các cách:

  | Cách | Chính xác | Hợp khi |
  |---|---|---|
  | Chia theo hash thành các file vừa RAM, rồi dedup từng file | Có | Xử lý batch |
  | External sort, rồi bỏ các phần tử liền kề trùng nhau | Có | Xử lý batch |
  | Bloom filter | Không: chấp nhận bỏ sót một ít URL mới (false positive làm tưởng đã thấy) | Luồng liên tục, ví dụ crawler |

- Chuẩn hoá URL trước: host hoa/thường, dấu `/` ở cuối, thứ tự query param. Không chuẩn hoá thì
  cùng một trang thành nhiều URL khác nhau.
- Lưu hash 8–16 byte thay cho URL để giảm bộ nhớ.
  - ⚠️ Hash ngắn thì có va chạm: hai URL khác nhau bị coi là trùng.

*External sort*
- *External sort* là sort dữ liệu lớn hơn RAM, dùng đĩa làm chỗ chứa trung gian.
  1. Pha 1: đọc từng khối vừa RAM, sort trong RAM, ghi ra đĩa thành một *run* (file đã sort).
  2. Pha 2: *K-way merge*. Mở K run cùng lúc, dùng min-heap chứa phần tử đầu của mỗi run (như
     module 2.4), lần lượt lấy phần tử nhỏ nhất ra. Đọc và ghi đều có buffer.
  3. Nhiều run quá, không mở cùng lúc được, thì merge nhiều tầng.
- Unix `sort` và DB (`ORDER BY` lớn thì spill ra đĩa) đã làm sẵn việc này.

*Tìm phần tử chung trên nhiều máy*
- *Shuffle*: mỗi máy gửi từng key tới máy số `hash(key) % số_máy`. Cùng một key của hai tập dữ
  liệu sẽ gặp nhau trên cùng một máy và so sánh tại chỗ. Đây là ý tưởng của join trong
  MapReduce/Spark.
- Một tập nhỏ: *broadcast join*, gửi nguyên tập nhỏ tới mọi máy, khỏi phải shuffle tập lớn.
- Gửi bloom filter của tập A sang để lọc tập B trước, bớt dữ liệu phải chuyển qua mạng.
- ⚠️ *Key lệch* (skew): một key chiếm phần lớn dữ liệu làm một máy quá tải. Tách key nóng ra xử
  lý riêng.

*Trong PHP*
- Xử lý file lớn bằng generator (`yield`) và `SplFileObject` đọc từng dòng. Không dùng `file()`
  nạp cả file vào RAM.

  ```php
  function readLines(string $path): Generator
  {
      $file = new SplFileObject($path);
      while (!$file->eof()) {
          yield $file->fgets();      // mỗi lần chỉ giữ một dòng trong RAM
      }
  }
  ```

**Đọc**
- DDIA ch.10 *Batch Processing*: sort-merge join, broadcast join, xử lý key lệch
- Algorithms 4th: [2.4 Priority Queues](https://algs4.cs.princeton.edu/24pq/) (multiway merge)
- Xem thêm [14-distributed-systems.md](14-distributed-systems.md) và [16-system-design.md](16-system-design.md)

**Nắm chắc khi**
- [ ] Trình bày được top-K 1 tỷ phần tử trên máy 4GB RAM, có ước lượng số file và bộ nhớ mỗi bước
- [ ] Giải thích được vì sao chia ngẫu nhiên rồi gộp top-K cho kết quả sai, bằng một phản ví dụ
- [ ] Ước lượng được số run và số tầng merge khi sort 500GB trên máy 16GB RAM

#### 3.4 Nối thuật toán với bài toán backend

**Vì sao cần học:** Đây là chỗ senior thể hiện khác biệt: nghe một yêu cầu nghiệp vụ và nhận
ra bài thuật toán bên trong, rồi chọn giữa tự cài và dùng công cụ có sẵn. Câu hỏi thường ở dạng
mở, như "thiết kế leaderboard" hay "gộp tài khoản trùng".

**Học gì**

*Nhận ra bài thuật toán trong yêu cầu nghiệp vụ*

| Yêu cầu | Cấu trúc hoặc thuật toán | Ghi chú |
|---|---|---|
| Leaderboard, hạng của user | Sorted set (skip list) | Module 3.1 |
| "Username đã tồn tại?", phần lớn là tên chưa có | Bloom filter đặt trước DB | Unique index vẫn là nguồn sự thật |
| Gộp tài khoản trùng qua email/điện thoại/thiết bị | Union-find hoặc connected components | Module 2.5 |
| Autocomplete | Trie, hoặc sorted list + binary search | Quy mô lớn thì dùng search engine (edge n-gram: index sẵn mọi prefix của từ) |
| Workflow có phụ thuộc, phát hiện cấu hình bị vòng | Topological sort | Module 2.5 |
| Rate limiter kiểu sliding window | Sorted set hoặc deque theo thời gian | |
| Kiểm tra trùng lịch | Interval | Module 2.4 |

*Cách trả lời của senior*
1. Hỏi quy mô và mức chính xác cần có.
2. Chọn cấu trúc.
3. Nói cái giá: bộ nhớ, sai số, vận hành.
4. Nói khi nào dùng công cụ có sẵn (DB, Redis, search engine) thay vì tự cài.

- ⚠️ Dữ liệu đã nằm trong DB thì `GROUP BY ... ORDER BY ... LIMIT K` với index phù hợp thường là
  đáp án đầu tiên, không phải tự viết heap:

  ```sql
  SELECT product_id, SUM(qty) AS sold
  FROM order_items
  WHERE created_at >= '2026-09-01'
  GROUP BY product_id
  ORDER BY sold DESC
  LIMIT 10;
  ```

**Đọc**
- Redis: [Sorted sets](https://redis.io/docs/latest/develop/data-types/sorted-sets/) (mục leaderboard, rate limiter)
- [11-cache.md](11-cache.md), [04-nosql-search-storage.md](04-nosql-search-storage.md), [16-system-design.md](16-system-design.md)

**Nắm chắc khi**
- [ ] Với 7 yêu cầu nghiệp vụ ở trên, nói ra cấu trúc dữ liệu và độ phức tạp trong 1 phút mỗi yêu cầu
- [ ] Nêu được một trường hợp chọn công cụ có sẵn tốt hơn tự cài, và lý do vận hành

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Big-O của lời giải bạn vừa viết là gì, vì sao?** (1.1)
- Ý phải có: đếm theo từng vòng lặp và thao tác bên trong; nói cả time và space; tính stack đệ quy
- Điểm cộng: chỉ ra thao tác ẩn có chi phí (`in_array`, `array_shift`, copy array, nối chuỗi trong vòng lặp)
- Red flag: đoán "O(n)" mà không chỉ được dòng nào tạo ra chi phí

**2. Array và linked list khác nhau thế nào? Khi nào dùng cái nào?** (1.2, 1.3)
- Ý phải có: truy cập O(1) so với O(n); chèn/xoá giữa O(n) so với O(1) khi đã có node; array thân thiện cache
- Điểm cộng: trong thực tế array gần như luôn thắng; linked list có giá trị khi ghép với hash map (LRU)

**3. Vì sao hash map là O(1) trung bình nhưng O(n) worst case?** (1.2)
- Ý phải có: hash phân bố đều và load factor được giữ dưới ngưỡng bằng resize; collision dồn vào một bucket thì O(n)
- Điểm cộng: hash flooding và seed ngẫu nhiên; Java treeify bucket còn O(log n); resize là O(n) nên insert chỉ là amortized O(1)
- Red flag: "vì tính hash rồi truy cập thẳng" và dừng ở đó

**4. Merge sort và quick sort khác nhau thế nào? Cái nào stable?** (1.4)
- Ý phải có: merge O(n log n) mọi trường hợp, tốn O(n) bộ nhớ, stable; quick average O(n log n), worst O(n²), in-place, không stable
- Điểm cộng: vì sao thư viện dùng thuật toán lai (TimSort, pdqsort, introsort); PHP 8 sort đã stable

**5. Stack và queue dùng vào việc gì trong thực tế?** (1.3)
- Ý phải có: call stack, undo, parse biểu thức, DFS; BFS, hàng đợi job, buffer
- Điểm cộng (PHP): `array_shift` là O(n), dùng `SplQueue`

**6. Viết binary search. Lỗi hay gặp là gì?** (1.4)
- Ý phải có: chọn một bất biến `[lo, hi]` hoặc `[lo, hi)` và giữ nhất quán; `mid` không tràn
- Điểm cộng: `lowerBound`; binary search trên đáp án với hàm `feasible`
- Red flag: sửa biên bằng cách thử `+1`/`-1` cho tới khi qua test

### 🟡 Mid

**7. Amortized O(1) của dynamic array nghĩa là gì?** (1.1)
- Ý phải có: thỉnh thoảng resize O(n), nhưng tổng n lần append là O(n) nhờ tăng theo hệ số nhân
- Điểm cộng: tăng theo hằng số cộng thì mất tính chất này; spike latency khi resize lớn

**8. Thiết kế LRU cache với get/put O(1).** (2.8)
- Ý phải có: hash map key → node, doubly linked list giữ thứ tự dùng; get chuyển node lên đầu; put đầy thì xoá cuối
- Điểm cộng: `LinkedHashMap` của Java; PHP array có thứ tự; chạy nhiều thread cần lock và chia shard; Redis dùng LRU xấp xỉ
- Red flag: dùng sort theo timestamp mỗi lần evict

**9. Bloom filter là gì? Có false negative không?** (3.2)
- Ý phải có: mảng bit + k hash; chỉ có false positive; không xoá được ở bản cơ bản
- Điểm cộng: tính kích thước theo n và tỉ lệ sai; dùng trong LSM và chống cache penetration

**10. Vì sao Redis sorted set dùng skip list?** (3.1)
- Ý phải có: O(log n) kỳ vọng cho thêm/xoá/tìm; range và rank theo thứ tự; cài đơn giản hơn cây cân bằng
- Điểm cộng: kết hợp hash table để tra score O(1); bản nhỏ dùng listpack

**11. Khi nào BFS, khi nào DFS, khi nào Dijkstra?** (2.5)
- Ý phải có: BFS cho đường ngắn nhất không trọng số và theo tầng; DFS cho duyệt hết, chu trình, backtracking; Dijkstra cho trọng số không âm
- Điểm cộng: vì sao Dijkstra sai với cạnh âm; đánh dấu visited khi push; heap không có decrease-key

**12. Làm sao nhận ra một bài là DP?** (2.7)
- Ý phải có: hỏi số cách/min/max/có-không; bài toán con lặp lại; lựa chọn ảnh hưởng về sau
- Điểm cộng: định nghĩa trạng thái bằng lời trước; độ phức tạp = số trạng thái × chi phí chuyển; phân biệt với greedy bằng phản ví dụ

**13. Tìm phần tử xuất hiện nhiều nhất trong mảng 1 tỷ phần tử không vừa RAM.** (3.3)
- Ý phải có: chia theo hash ra file, đếm từng file, gộp bằng heap
- Điểm cộng: vì sao không chia ngẫu nhiên được; luồng liên tục thì Count-Min Sketch; dữ liệu đã ở DB thì `GROUP BY`
- Red flag: "load hết vào map"

**14. Làm bài bằng PHP: cấu trúc nào có sẵn, cạm bẫy gì?** (2.8)
- Ý phải có: array là ordered hash map; SPL stack/queue/heap/priority queue; `isset` O(1) còn `in_array` O(n); `array_shift` O(n)
- Điểm cộng: copy-on-write và O(n²) ẩn khi sửa array được truyền vào hàm; key `"1"` thành int; `SplPriorityQueue` không FIFO khi cùng priority; ext `ds` không có sẵn

**15. Code chạy đúng ví dụ rồi. Bạn làm gì tiếp?** (1.5)
- Ý phải có: tự dò edge case (rỗng, trùng, âm, overflow), nói time/space, hướng tối ưu, trước khi được hỏi
- Red flag: "Xong rồi ạ"

### 🔴 Senior

**16. Vì sao index DB dùng B+tree, còn nhiều hệ thống ghi nhiều dùng LSM tree?** (3.1)
- Ý phải có: đơn vị đọc là page, B+tree nhiều key mỗi node nên chỉ vài tầng; lá nối nhau cho range scan; LSM biến ghi ngẫu nhiên thành ghi tuần tự
- Điểm cộng: read/write/space amplification; compaction; bloom filter trong LSM; BST nhị phân quá cao

**17. Consistent hashing giải quyết vấn đề gì? Redis Cluster có dùng không?** (3.2)
- Ý phải có: `hash % N` đổi N thì gần hết key di chuyển; vòng hash chỉ di chuyển ~1/N; virtual node
- Điểm cộng: Redis Cluster dùng 16384 slot cố định, di chuyển slot khi resharding
- Red flag: khẳng định Redis Cluster dùng consistent hashing

**18. Đếm số user duy nhất mỗi ngày trên hàng tỷ event.** (3.2, 3.3)
- Ý phải có: hỏi có cần chính xác không; HyperLogLog cho dashboard, vài KB mỗi ngày, gộp theo tuần được
- Điểm cộng: báo cáo tính tiền thì `COUNT(DISTINCT)` trong OLAP; sai số 0.81% của Redis HLL

**19. Sort file log 500GB theo thời gian trên máy 16GB RAM.** (3.3)
- Ý phải có: external sort, run vài GB, K-way merge bằng heap
- Điểm cộng: I/O tuần tự và buffer; merge nhiều tầng; dùng `sort` của Unix hoặc công cụ phân tán nếu làm thường xuyên; log thường gần như đã sort theo thời gian

**20. Tìm phần tử chung giữa hai tập dữ liệu lớn nằm trên nhiều máy.** (3.3)
- Ý phải có: shuffle theo hash key để cùng key về một máy; broadcast join khi một tập nhỏ
- Điểm cộng: bloom filter lọc trước để giảm truyền mạng; xử lý key lệch

**21. Leaderboard realtime cho 10 triệu user, hỏi hạng của user bất kỳ.** (3.4)
- Ý phải có: Redis sorted set, `ZADD`, `ZREVRANK` O(log n); sort trong DB mỗi lần quá đắt
- Điểm cộng: hạng xấp xỉ theo bucket điểm khi quy mô lớn hơn nhiều; xử lý điểm bằng nhau; bền vững dữ liệu khi Redis mất

**22. API "username đã tồn tại" bị gọi rất nhiều, phần lớn là tên chưa có.** (3.2, 3.4)
- Ý phải có: bloom filter trước DB trả "chắc chắn chưa có"; "có thể có" thì hỏi DB; unique index vẫn là nguồn sự thật
- Điểm cộng: rebuild khi dữ liệu vượt n dự kiến; không xoá được khi user đổi tên; race giữa kiểm tra và đăng ký vẫn phải chặn bằng unique index

**23. Tìm các nhóm tài khoản trùng qua email, số điện thoại, thiết bị.** (2.5, 3.4)
- Ý phải có: union-find trên các định danh hoặc connected components; chạy batch
- Điểm cộng: định danh dùng chung (số tổng đài công ty, thiết bị ở quán net) tạo một nhóm khổng lồ, cần loại hoặc đặt ngưỡng

**24. Autocomplete tìm sản phẩm theo prefix.** (2.3, 3.4)
- Ý phải có: trie hoặc sorted list + binary search cho tập nhỏ; quy mô lớn dùng search engine (edge n-gram)
- Điểm cộng: lưu sẵn top-K gợi ý tại mỗi node; tiếng Việt cần chuẩn hoá bỏ dấu; cache prefix ngắn

**25. Workflow gồm các bước phụ thuộc nhau, cần phát hiện cấu hình vòng và chạy song song tối đa.** (2.5, 3.4)
- Ý phải có: topological sort Kahn, còn node chưa xử lý là có vòng
- Điểm cộng: các node cùng lúc có in-degree 0 chạy song song; báo ra chu trình cụ thể cho người cấu hình

---

## Bài tập tự làm

Code đặt trong [`../dsa/`](../dsa/) theo quy ước ở đầu file (Go: `dsa/go/<chủ đề>/` kèm test
table-driven; Java: `dsa/java/<Tên>.java`). Làm bằng PHP thì ghi rõ lệnh chạy.

1. Cài LRU cache bằng hash map + doubly linked list tự viết, bằng Go (ví dụ `dsa/go/lru/`) rồi
   bằng Java (`dsa/java/LRUCache.java`); ghi độ phức tạp từng thao tác. Làm thêm một bản PHP
   dùng array có thứ tự và so sánh hai cách.
2. Với 10 bài trong Chặng 2 bạn chưa làm, chỉ đọc đề và viết ra: pattern nào, vì sao, độ phức
   tạp dự kiến. Sau đó mới giải.
3. Ước lượng bộ nhớ cần để dedup 1 tỷ URL bằng set chính xác và bằng bloom filter với tỉ lệ
   false positive 1%. Trình bày cách tính.
4. Giải thích bằng lời (không code) vì sao Dijkstra sai khi có cạnh âm, kèm một đồ thị 3–4
   node làm phản ví dụ.
5. Viết `topK(stream, k)` cho luồng dữ liệu không biết trước độ dài; nêu độ phức tạp và điều
   gì thay đổi khi dữ liệu không vừa một máy.
6. PHP: viết BFS trên lưới 1000×1000 hai cách, một bằng `array_shift` và một bằng `SplQueue`
   (hoặc chỉ số đầu). Đo thời gian bằng `hrtime(true)` và giải thích chênh lệch.

> Nộp bài vào đây để được review.
