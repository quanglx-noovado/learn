# 21. Cấu trúc dữ liệu và thuật toán

> [← Mục lục](README.md) · Phạm vi: Big-O, cấu trúc dữ liệu và ứng dụng trong backend thật, các pattern giải bài phỏng vấn, quy trình làm bài, bài toán nửa thuật toán nửa hệ thống, lộ trình luyện.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

Backend thường hỏi easy đến medium. Mục tiêu là **nhận ra pattern** và **nói được lý do**,
không phải học thuộc lời giải. Senior còn bị hỏi cấu trúc dữ liệu nằm ở đâu trong DB, cache,
queue mình dùng hằng ngày.

> Luyện code trong repo này: [`../dsa/`](../dsa/) (bản Go có test, bản Java test trong `main`;
> lộ trình và cách học mỗi chủ đề ở [`../dsa/README.md`](../dsa/README.md)).

## Bản đồ nhanh

**Nền tảng**
- [ ] Big-O time và space; phân tích được lời giải của chính mình
- [ ] Best/average/worst case; 🟡 amortized
- [ ] Bảng độ phức tạp cấu trúc dữ liệu
- [ ] Sort: quick, merge, heap, insertion, counting/radix; stable, in-place
- [ ] 🟡 Sort trong thư viện chuẩn PHP/Java/Go dùng thuật toán gì
- [ ] Ràng buộc n → độ phức tạp chấp nhận được

**Cấu trúc dữ liệu**
- [ ] Array, dynamic array
- [ ] Linked list
- [ ] Stack, queue, deque
- [ ] Hash table: collision, load factor, chaining vs open addressing
- [ ] Heap / priority queue
- [ ] BST, 🟡 cây cân bằng (AVL, red-black)
- [ ] 🟡 B-tree/B+tree (index DB)
- [ ] 🟡 Trie
- [ ] Graph: adjacency list vs matrix
- [ ] 🟡 Union-find
- [ ] 🔴 Segment tree, Fenwick tree
- [ ] 🟡 Skip list
- [ ] 🟡 Bloom filter
- [ ] 🟡 LRU cache
- [ ] 🟡 Consistent hashing
- [ ] 🔴 HyperLogLog, Count-Min Sketch

**Pattern**
- [ ] Hash map/set
- [ ] Two pointers
- [ ] Sliding window
- [ ] Prefix sum
- [ ] Stack, 🟡 monotonic stack/queue
- [ ] Binary search, 🟡 binary search trên đáp án
- [ ] Linked list tricks (dummy node, nhanh/chậm)
- [ ] Tree DFS/BFS
- [ ] BST
- [ ] Heap / top-K
- [ ] Graph BFS/DFS
- [ ] 🟡 Topological sort
- [ ] 🟡 Union-find
- [ ] 🟡 Shortest path: BFS, Dijkstra
- [ ] Interval
- [ ] 🟡 Greedy
- [ ] 🟡 Backtracking
- [ ] 🟡 Dynamic programming: 1D, 2D, knapsack, LCS
- [ ] 🟡 Bit manipulation
- [ ] Matrix
- [ ] 🟡 Thiết kế cấu trúc dữ liệu (LRU, Trie)

**Làm bài**
- [ ] Quy trình làm bài trong phỏng vấn
- [ ] Edge case checklist
- [ ] ⚠️ Off-by-one, overflow, sửa collection khi duyệt, đệ quy quá sâu

**Nửa thuật toán nửa hệ thống**
- [ ] 🟡 Top-K trên dữ liệu lớn
- [ ] 🔴 Đếm phần tử khác nhau (HyperLogLog)
- [ ] 🟡 Dedup 1 tỷ URL
- [ ] 🟡 Sort file lớn hơn RAM (external sort)
- [ ] 🔴 Tìm trùng trên nhiều máy

## Chi tiết

### Nền tảng

- [ ] **Big-O**: tốc độ tăng của chi phí khi n tăng, bỏ hằng số và bậc thấp
  - Time và space; space tính cả stack đệ quy (DFS trên cây lệch sâu O(n))
  - Nhiều input thì dùng nhiều biến: duyệt ma trận m×n là O(m·n), không phải O(n²)
  - ⚠️ Hằng số vẫn quan trọng trong thực tế: O(n) duyệt array liên tục thường nhanh hơn
    O(n) duyệt linked list vì cache CPU
- [ ] **Best / average / worst**
  - Quick sort: average O(n log n), worst O(n²) khi pivot tệ
  - Hash map: average O(1), worst O(n) khi mọi key rơi cùng bucket
  - Phỏng vấn mặc định hỏi worst, trừ khi nói rõ; nói cả hai là điểm cộng
- [ ] 🟡 **Amortized**: chi phí trung bình trên một chuỗi thao tác, không phải xác suất
  - Dynamic array append: thỉnh thoảng phải cấp mảng mới gấp đôi và copy O(n), nhưng tổng
    n lần append là O(n) nên mỗi lần O(1) amortized
  - ⚠️ Tăng dung lượng theo hằng số cộng (+10) thay vì nhân thì mất tính chất này, thành O(n) mỗi lần
  - ⚠️ Amortized O(1) vẫn có lần chậm: với hệ thống nhạy latency, một lần resize lớn là một spike
- [ ] **Độ phức tạp cấu trúc dữ liệu**

  | Cấu trúc | Truy cập | Tìm | Thêm | Xoá |
  |---|---|---|---|---|
  | Array/dynamic array | O(1) | O(n) | O(1) cuối (trung bình), O(n) giữa | O(n) |
  | Linked list | O(n) | O(n) | O(1) nếu có sẵn node | O(1) nếu có sẵn node |
  | Hash map | — | O(1) trung bình | O(1) trung bình | O(1) trung bình |
  | Cây nhị phân cân bằng | O(log n) | O(log n) | O(log n) | O(log n) |
  | Heap | O(1) xem min/max | O(n) | O(log n) | O(log n) lấy min/max |
  | Trie | — | O(L) với L là độ dài key | O(L) | O(L) |
  | Union-find | — | ~O(1) amortized (α(n)) | ~O(1) | — |

- [ ] **Sort**

  | Thuật toán | Best | Average | Worst | Bộ nhớ phụ | Stable |
  |---|---|---|---|---|---|
  | Insertion | O(n) | O(n²) | O(n²) | O(1) | có |
  | Merge | O(n log n) | O(n log n) | O(n log n) | O(n) | có |
  | Quick | O(n log n) | O(n log n) | O(n²) | O(log n) stack | không |
  | Heap | O(n log n) | O(n log n) | O(n log n) | O(1) | không |
  | Counting | O(n + k) | O(n + k) | O(n + k) | O(n + k) | có (bản chuẩn) |
  | Radix | O(d·(n + k)) | O(d·(n + k)) | O(d·(n + k)) | O(n + k) | có |

  - Stable: phần tử bằng nhau giữ nguyên thứ tự ban đầu. Quan trọng khi sort nhiều lượt
    (sort theo ngày, rồi sort stable theo trạng thái thì trong cùng trạng thái vẫn theo ngày)
  - Sort so sánh không nhanh hơn O(n log n) trong worst case; counting/radix vượt được vì
    không so sánh, chỉ dùng khi miền giá trị nhỏ
  - Insertion sort nhanh với mảng nhỏ hoặc gần như đã sort; vì vậy các thuật toán lai dùng nó
    cho đoạn nhỏ
  - Phải giải thích được merge sort (chia đôi, sort hai nửa, trộn) và quick sort (chọn pivot,
    phân hoạch, đệ quy)
- [ ] 🟡 **Sort trong thư viện chuẩn**
  - Java: `Arrays.sort` cho kiểu nguyên thuỷ dùng dual-pivot quicksort (không cần stable vì
    không phân biệt được hai số bằng nhau); cho object dùng TimSort (stable)
  - Go: `sort.Sort` và `slices.Sort` dùng pdqsort (không stable); cần stable thì
    `sort.Stable`/`slices.SortStableFunc`
  - PHP: từ PHP 8.0, `sort`/`usort` là stable
  - ⚠️ Comparator phải nhất quán (bắc cầu, trả 0 khi bằng); comparator sai có thể gây kết quả
    sai hoặc exception (Java TimSort có thể ném "Comparison method violates its general contract")
- [ ] **Ràng buộc n → độ phức tạp** (ước lượng thô, giả sử cỡ 10⁷–10⁸ thao tác đơn giản
      mỗi giây; thực tế phụ thuộc ngôn ngữ và hằng số)

  | n cỡ | Độ phức tạp chấp nhận được | Gợi ý hướng |
  |---|---|---|
  | ≤ 10–12 | O(n!) | hoán vị, backtracking |
  | ≤ 20–25 | O(2ⁿ) | subset, bitmask DP |
  | ≤ 500 | O(n³) | DP 3 chiều, Floyd–Warshall |
  | ≤ 5·10³ | O(n²) | DP 2 chiều, hai vòng lặp |
  | ≤ 10⁶ | O(n log n) | sort, heap, binary search |
  | ≤ 10⁸ | O(n) | một lượt duyệt, hash, two pointers |
  | lớn hơn | O(log n), O(1) | công thức, binary search |

  - Đọc ràng buộc trước để đoán hướng: n ≤ 20 gần như chắc là exponential; n = 10⁵ thì O(n²) không qua

### Cấu trúc dữ liệu

- [ ] **Array, dynamic array**
  - Bộ nhớ liên tục: truy cập O(1), thân thiện cache CPU
  - Dynamic array tăng dung lượng theo hệ số nhân. Đối chiếu: Java `ArrayList`, Go slice
    (`append` có thể cấp mảng mới), PHP array (thực chất là ordered hash table, packed array
    khi key là 0..n-1)
  - ⚠️ Go: hai slice cùng trỏ một underlying array, `append` vào một slice có thể ghi đè dữ
    liệu slice kia nếu còn capacity. Xem [07-go.md](07-go.md)
  - Backend: buffer, batch, row trong result set
- [ ] **Linked list**
  - Thêm/xoá O(1) khi đã có node; truy cập O(n); cache kém
  - Doubly linked list là nửa của LRU cache
  - Java `LinkedList` hiếm khi nhanh hơn `ArrayList` trong thực tế; `ArrayDeque` tốt hơn cho
    stack/queue
- [ ] **Stack, queue, deque**
  - Stack (LIFO): call stack, undo, parse biểu thức, duyệt DFS không đệ quy
  - Queue (FIFO): BFS, hàng đợi job; deque: sliding window maximum, work stealing
  - Đối chiếu: Java `ArrayDeque`; Go dùng slice (hoặc `container/list`); PHP `SplStack`,
    `SplQueue`, hoặc array với `array_push`/`array_pop`. ⚠️ `array_shift` trong PHP là O(n)
    vì phải đánh lại chỉ số
- [ ] **Hash table**
  - Hàm hash map key vào bucket; chất lượng hash quyết định phân bố
  - **Collision**: hai key cùng bucket
    - Chaining: mỗi bucket là một danh sách (hoặc cây). Java `HashMap` chuyển bucket từ list
      sang red-black tree khi bucket quá dài để worst case còn O(log n)
    - Open addressing: tìm ô trống khác trong cùng mảng (linear/quadratic probing, double
      hashing). Cache tốt hơn, nhưng xoá phức tạp (cần tombstone) và nhạy với load factor
  - **Load factor** = số phần tử / số bucket. Vượt ngưỡng thì resize và rehash toàn bộ.
    Java `HashMap` mặc định 0.75
  - Go map: từ Go 1.24 cài theo kiểu Swiss table (open addressing theo nhóm); thứ tự duyệt
    cố ý ngẫu nhiên
  - ⚠️ Worst case O(n): hash kém hoặc bị tấn công **hash flooding** (kẻ tấn công gửi nhiều
    key cùng hash). Phòng: hash có seed ngẫu nhiên, giới hạn số field trong request
  - ⚠️ Key mutable: đổi field tham gia hash sau khi put thì không tìm lại được. Java: override
    `equals` phải override `hashCode`
  - Backend: cache in-memory, dedup, đếm, index trong bộ nhớ, Redis hash
- [ ] **Heap / priority queue**
  - Cây nhị phân gần đầy lưu trong mảng; con của i là 2i+1, 2i+2
  - Push/pop O(log n), xem đỉnh O(1), build heap từ mảng O(n)
  - Đối chiếu: Java `PriorityQueue` (min-heap); Go `container/heap` (tự cài interface);
    PHP `SplMinHeap`, `SplPriorityQueue`
  - Backend: scheduler/timer, delay queue, top-K, merge K luồng đã sort, Dijkstra
- [ ] **BST, cây cân bằng**
  - BST: trái < gốc < phải; duyệt in-order ra dãy tăng dần
  - ⚠️ Chèn dãy đã sort vào BST thường thành linked list, O(n) mỗi thao tác
  - 🟡 AVL: cân bằng chặt theo chiều cao, tìm nhanh hơn, xoay nhiều hơn khi ghi
  - 🟡 Red-black: cân bằng lỏng hơn (đường dài nhất không quá 2 lần đường ngắn nhất), ghi ít
    xoay hơn. Dùng trong Java `TreeMap`, bucket cây của `HashMap`, Linux CFS scheduler
  - Không cần cài xoay cây trong phỏng vấn; cần biết vì sao phải cân bằng và cái giá
  - Backend: map có thứ tự, range query trong bộ nhớ
- [ ] 🟡 **B-tree / B+tree**
  - Mỗi node chứa nhiều key, vừa một page đĩa; cây rất thấp nên ít lần đọc đĩa
  - B+tree: dữ liệu (hoặc con trỏ) chỉ ở lá, lá nối với nhau nên range scan nhanh
  - Dùng trong index của MySQL InnoDB, PostgreSQL B-tree index, nhiều file system
  - So với LSM tree (RocksDB, Cassandra): B+tree đọc tốt, LSM ghi tốt
  - Chi tiết index, composite index, leftmost prefix ở [03-database-sql.md](03-database-sql.md)
- [ ] 🟡 **Trie**
  - Cây theo từng ký tự; tìm theo prefix O(L)
  - Radix tree (nén các nhánh một con) tiết kiệm bộ nhớ; nhiều HTTP router (ví dụ httprouter,
    Gin của Go) dùng radix tree để match path
  - Backend: autocomplete, routing, longest prefix match của bảng định tuyến IP
  - ⚠️ Tốn bộ nhớ với bảng chữ lớn (Unicode); dùng map cho con thay vì mảng cố định
- [ ] **Graph**

  | Biểu diễn | Bộ nhớ | Kiểm tra cạnh (u,v) | Duyệt hàng xóm | Hợp với |
  |---|---|---|---|---|
  | Adjacency list | O(V + E) | O(bậc) | O(bậc) | đồ thị thưa (hầu hết bài toán thực tế) |
  | Adjacency matrix | O(V²) | O(1) | O(V) | đồ thị dày, V nhỏ |
  | Edge list | O(E) | O(E) | O(E) | Kruskal, input thô |

  - Lưới (grid) là graph ngầm: mỗi ô nối 4 hoặc 8 ô xung quanh, không cần dựng
  - Backend: dependency giữa service/job/migration, mạng quan hệ, phân quyền theo cây tổ chức
- [ ] 🟡 **Union-find (disjoint set)**
  - `find(x)` tìm đại diện nhóm, `union(a, b)` gộp nhóm
  - Path compression + union by rank/size: gần O(1) amortized (hàm ngược Ackermann α(n))
  - Dùng khi: gộp nhóm dần, đếm thành phần liên thông, phát hiện chu trình trong đồ thị vô
    hướng, Kruskal. Ví dụ: gộp tài khoản trùng theo email/số điện thoại
  - ⚠️ Không hỗ trợ tách nhóm
- [ ] 🔴 **Segment tree, Fenwick tree (BIT)**
  - Truy vấn đoạn (tổng, min, max) và cập nhật điểm đều O(log n)
  - Fenwick gọn hơn, chủ yếu cho prefix sum có cập nhật; segment tree tổng quát hơn (min/max,
    lazy propagation cho cập nhật đoạn)
  - Prefix sum thường đủ nếu mảng không đổi. Ít gặp trong phỏng vấn backend
- [ ] 🟡 **Skip list**
  - Nhiều tầng linked list; tầng trên "nhảy cóc", mỗi node lên tầng trên với xác suất cố định
  - Tìm/thêm/xoá O(log n) kỳ vọng; cài đơn giản hơn cây cân bằng, dễ làm concurrent
  - Redis sorted set (`ZSET`) dùng skip list kết hợp hash table (bản nhỏ dùng encoding gọn
    hơn); vì vậy `ZRANGEBYSCORE`, `ZRANK` nhanh. Java có `ConcurrentSkipListMap`
  - Backend: leaderboard, rate limiter sliding window, hàng đợi theo thời gian. Xem
    [04-nosql-search-storage.md](04-nosql-search-storage.md)
- [ ] 🟡 **Bloom filter**
  - Mảng bit + k hàm hash. Trả lời "chắc chắn không có" hoặc "có thể có"
  - ⚠️ Có false positive, không có false negative; bản cơ bản không xoá được (counting bloom
    filter xoá được, tốn bộ nhớ hơn)
  - Tỉ lệ false positive phụ thuộc số bit, số hash, số phần tử; chọn trước theo n dự kiến
  - Dùng: LSM tree (Cassandra, RocksDB, HBase) bỏ qua file chắc chắn không chứa key; chống
    cache penetration (key không tồn tại); kiểm tra username đã dùng, URL đã crawl
- [ ] 🟡 **LRU cache**
  - Hash map (key → node) + doubly linked list (thứ tự dùng gần nhất); get/put O(1)
  - Java: `LinkedHashMap` với `accessOrder=true` và override `removeEldestEntry`
  - Biến thể: LFU, TTL; Redis dùng LRU/LFU xấp xỉ (lấy mẫu) thay vì chính xác để tiết kiệm
    bộ nhớ. Xem [11-cache.md](11-cache.md)
  - ⚠️ Bản dùng nhiều thread cần lock; một lock chung thành nút cổ chai, phải chia shard
- [ ] 🟡 **Consistent hashing**
  - Node và key đều được hash lên một vòng; key thuộc node đầu tiên theo chiều kim đồng hồ.
    Thêm/bớt một node chỉ di chuyển khoảng 1/N key, thay vì gần như tất cả như `hash % N`
  - Virtual node: mỗi node thật đặt nhiều điểm trên vòng để phân bố đều
  - Dùng: Cassandra, DynamoDB-style store, sharding cache phía client, load balancer sticky
  - ⚠️ Redis Cluster không dùng vòng consistent hashing mà dùng 16384 hash slot cố định gán
    cho node. Xem [14-distributed-systems.md](14-distributed-systems.md)
- [ ] 🔴 **Cấu trúc xác suất khác**
  - HyperLogLog: đếm số phần tử khác nhau xấp xỉ với bộ nhớ cố định nhỏ. Redis `PFADD`/`PFCOUNT`
    (sai số chuẩn khoảng 0.81%, tối đa 12KB mỗi key). Gộp được nhiều HLL (`PFMERGE`)
  - Count-Min Sketch: đếm tần suất xấp xỉ (chỉ đếm dư, không đếm thiếu); dùng cho heavy hitter

### Pattern

Mỗi pattern: dấu hiệu nhận ra → khung lời giải → bài tiêu biểu. Độ khó (E/M/H) theo
LeetCode tại thời điểm viết, có thể thay đổi. Bài đánh dấu (premium) cần tài khoản trả phí;
thường có bản tương đương trên LintCode/NeetCode.

- [ ] **Hash map/set**
  - Dấu hiệu: "đã thấy chưa", đếm tần suất, tìm cặp có tổng/hiệu, nhóm theo khoá
  - Khung: một lượt duyệt, với mỗi phần tử hỏi map điều cần biết rồi cập nhật map. Đổi O(n²)
    thành O(n) bằng O(n) bộ nhớ
  - Bài: Two Sum (E), Contains Duplicate (E), Group Anagrams (M), Top K Frequent Elements (M),
    Longest Consecutive Sequence (M)
- [ ] **Two pointers**
  - Dấu hiệu: mảng đã sort (hoặc sort được), tìm cặp/bộ ba, đảo ngược, palindrome, gộp hai dãy
  - Khung: hai con trỏ hai đầu tiến vào nhau theo so sánh; hoặc con trỏ đọc/ghi cùng chiều để
    lọc tại chỗ
  - Bài: Valid Palindrome (E), Two Sum II (M), 3Sum (M), Container With Most Water (M),
    Trapping Rain Water (H)
- [ ] **Sliding window**
  - Dấu hiệu: đoạn con/chuỗi con **liên tục** dài nhất/ngắn nhất thoả điều kiện
  - Khung: mở rộng phải; khi cửa sổ vi phạm điều kiện thì co trái; cập nhật đáp án. Mỗi phần
    tử vào ra một lần nên O(n). Cửa sổ cố định k thì trượt đều
  - ⚠️ Chỉ đúng khi điều kiện "đơn điệu" khi co/giãn; mảng có số âm với bài tổng thì thường
    phải dùng prefix sum thay vì sliding window
  - Bài: Best Time to Buy and Sell Stock (E), Longest Substring Without Repeating Characters (M),
    Longest Repeating Character Replacement (M), Permutation in String (M),
    Minimum Window Substring (H)
- [ ] **Prefix sum**
  - Dấu hiệu: tổng đoạn nhiều lần; đếm đoạn con có tổng bằng k (kể cả số âm)
  - Khung: `pre[i] = pre[i-1] + a[i]`; tổng đoạn `[l, r] = pre[r+1] - pre[l]`. Kết hợp hash map
    đếm số lần gặp mỗi prefix
  - Bài: Range Sum Query - Immutable (E), Subarray Sum Equals K (M), Product of Array Except
    Self (M), Continuous Subarray Sum (M)
- [ ] **Stack, monotonic stack/queue**
  - Dấu hiệu stack: ngoặc lồng nhau, biểu thức, "hoàn tác". Monotonic stack: "phần tử lớn hơn/
    nhỏ hơn gần nhất bên trái/phải"
  - Khung monotonic stack: duyệt, pop khi phần tử mới phá thứ tự (lúc pop là lúc tìm được đáp
    án cho phần tử bị pop), rồi push. O(n)
  - Monotonic deque: max/min của cửa sổ trượt
  - Bài: Valid Parentheses (E), Min Stack (M), Evaluate Reverse Polish Notation (M),
    Daily Temperatures (M), Sliding Window Maximum (H), Largest Rectangle in Histogram (H)
- [ ] **Binary search**
  - Dấu hiệu: mảng sort, tìm vị trí đầu/cuối, mảng xoay; hoặc **đáp án đơn điệu**: "nhỏ nhất
    sao cho làm được" (nếu x làm được thì mọi y > x cũng làm được)
  - Khung: giữ bất biến rõ ràng cho `[lo, hi)` hoặc `[lo, hi]` và giữ nguyên một kiểu.
    Trên đáp án: nhị phân trên miền giá trị, hàm `feasible(x)` kiểm tra
  - ⚠️ `mid = lo + (hi - lo) / 2` tránh overflow; vòng lặp vô hạn khi `lo = mid` với chia làm tròn xuống
  - Bài: Binary Search (E), Find First and Last Position of Element (M), Search in Rotated
    Sorted Array (M), Find Minimum in Rotated Sorted Array (M), Koko Eating Bananas (M),
    Capacity To Ship Packages Within D Days (M)
  - Repo đã có `lowerBound`: xem [`../dsa/`](../dsa/)
- [ ] **Linked list tricks**
  - Dấu hiệu: đảo, gộp, tìm giữa, phát hiện vòng, xoá phần tử thứ n từ cuối
  - Khung: dummy head để khỏi xử lý riêng node đầu; con trỏ nhanh/chậm (giữa danh sách, vòng);
    hai con trỏ cách nhau n bước
  - Bài: Reverse Linked List (E), Merge Two Sorted Lists (E), Linked List Cycle (E),
    Remove Nth Node From End of List (M), Reorder List (M)
- [ ] **Tree DFS/BFS**
  - Dấu hiệu: cây nhị phân; theo tầng thì BFS, còn lại thường DFS
  - Khung DFS: hàm đệ quy trả về thông tin của cây con (chiều cao, tổng, có hợp lệ không), gộp
    ở node cha. BFS: queue, xử lý theo từng tầng bằng cách lấy `len(queue)` đầu mỗi vòng
  - Bài: Maximum Depth of Binary Tree (E), Invert Binary Tree (E), Diameter of Binary Tree (E),
    Binary Tree Level Order Traversal (M), Lowest Common Ancestor of a Binary Tree (M),
    Binary Tree Maximum Path Sum (H)
- [ ] **BST**
  - Dấu hiệu: đề nói BST; tận dụng in-order tăng dần và cận trên/dưới
  - Khung: DFS truyền khoảng `(min, max)` hợp lệ; hoặc duyệt in-order
  - ⚠️ Validate BST chỉ so node với con trực tiếp là sai; phải so với cả tổ tiên
  - Bài: Search in a BST (E), Validate Binary Search Tree (M), Kth Smallest Element in a BST (M)
- [ ] **Heap / top-K**
  - Dấu hiệu: "k lớn nhất/nhỏ nhất", "k gần nhất", trộn k dãy, trung vị luồng dữ liệu
  - Khung: top-K lớn nhất dùng **min-heap** kích thước k: O(n log k). Trung vị: hai heap
  - Bài: Last Stone Weight (E), Kth Largest Element in an Array (M), K Closest Points to
    Origin (M), Merge k Sorted Lists (H), Find Median from Data Stream (H)
- [ ] **Graph BFS/DFS**
  - Dấu hiệu: đảo, vùng liên thông, lan truyền, lưới, đồ thị ẩn (trạng thái → trạng thái)
  - Khung: tập `visited` đánh dấu **khi đưa vào queue** (không phải khi lấy ra) để tránh thêm trùng.
    BFS nhiều nguồn: đưa mọi nguồn vào queue từ đầu
  - Bài: Number of Islands (M), Clone Graph (M), Rotting Oranges (M), Pacific Atlantic Water
    Flow (M), Word Ladder (H)
- [ ] 🟡 **Topological sort**
  - Dấu hiệu: phụ thuộc, thứ tự thực hiện, "có làm được hết không" (phát hiện chu trình trên
    đồ thị có hướng)
  - Khung Kahn: tính in-degree, đưa node in-degree 0 vào queue, lấy ra thì giảm in-degree hàng
    xóm. Số node xử lý < V nghĩa là có chu trình
  - Backend thật: thứ tự build, thứ tự chạy migration/job trong DAG (ví dụ Airflow), dependency resolver
  - Bài: Course Schedule (M), Course Schedule II (M), Alien Dictionary (H, premium)
- [ ] 🟡 **Union-find**
  - Dấu hiệu: gộp nhóm theo quan hệ tương đương, thành phần liên thông động, cạnh thừa tạo chu trình
  - Bài: Number of Provinces (M), Redundant Connection (M), Accounts Merge (M),
    Number of Connected Components in an Undirected Graph (M, premium)
- [ ] 🟡 **Shortest path**
  - Không trọng số hoặc trọng số bằng nhau: BFS, O(V + E)
  - Trọng số không âm: Dijkstra với min-heap, O((V + E) log V). ⚠️ Sai với cạnh âm
  - Cạnh âm: Bellman-Ford O(V·E); mọi cặp với V nhỏ: Floyd–Warshall O(V³)
  - ⚠️ Dijkstra dùng heap không có decrease-key: cho phép phần tử cũ trong heap, bỏ qua khi pop
    ra mà khoảng cách đã lớn hơn giá trị tốt nhất
  - Bài: Shortest Path in Binary Matrix (M), Network Delay Time (M), Path With Minimum
    Effort (M), Cheapest Flights Within K Stops (M)
- [ ] **Interval**
  - Dấu hiệu: khoảng thời gian, lịch, chồng lấn
  - Khung: sort theo điểm đầu rồi quét gộp; đếm số phòng cần thì sort điểm đầu/cuối riêng hoặc
    min-heap theo điểm cuối
  - ⚠️ Thống nhất biên đóng/mở: `[1,2]` và `[2,3]` có chồng không
  - Backend thật: đặt lịch, kiểm tra trùng booking (trong DB thì là điều kiện
    `a.start < b.end AND b.start < a.end`)
  - Bài: Meeting Rooms (E, premium), Merge Intervals (M), Insert Interval (M),
    Non-overlapping Intervals (M), Meeting Rooms II (M, premium)
- [ ] 🟡 **Greedy**
  - Dấu hiệu: chọn cục bộ tốt nhất mà không cần quay lại; thường sau khi sort
  - Khung: đề xuất tiêu chí chọn, rồi **lập luận** vì sao không có lời giải tốt hơn (exchange argument).
    ⚠️ Không chứng minh được thì thử phản ví dụ; nhiều bài trông như greedy nhưng là DP (Coin Change
    với mệnh giá bất kỳ)
  - Bài: Maximum Subarray (M, Kadane), Jump Game (M), Gas Station (M), Partition Labels (M),
    Task Scheduler (M)
- [ ] 🟡 **Backtracking**
  - Dấu hiệu: liệt kê mọi tổ hợp/hoán vị/cách chia; n nhỏ
  - Khung: `choose → explore → unchoose`; cắt nhánh sớm khi không thể hợp lệ; tránh trùng bằng
    sort + bỏ phần tử giống phần tử trước ở cùng tầng
  - ⚠️ Thêm vào kết quả phải copy mảng hiện tại, không thêm tham chiếu
  - Bài: Subsets (M), Permutations (M), Combination Sum (M), Generate Parentheses (M),
    Word Search (M), N-Queens (H)
- [ ] 🟡 **Dynamic programming**
  - Nhận ra: hỏi **số cách**, **min/max**, hoặc **có/không**; lựa chọn ở mỗi bước ảnh hưởng
    bước sau; đệ quy thô có bài toán con lặp lại
  - Khung 4 bước: định nghĩa trạng thái `dp[i]` bằng lời → công thức chuyển → giá trị cơ sở
    → thứ tự tính. Đi từ đệ quy → memoization → bottom-up → tối ưu bộ nhớ (chỉ giữ hàng trước)
  - 1D: Climbing Stairs (E), House Robber (M), Coin Change (M), Word Break (M),
    Longest Increasing Subsequence (M), Decode Ways (M)
  - 2D (lưới, hai chuỗi): Unique Paths (M), Longest Common Subsequence (M), Edit Distance (M)
  - Knapsack: 0/1 (mỗi món một lần, duyệt dung lượng **ngược** khi dùng mảng 1D) vs unbounded
    (duyệt xuôi). Bài: Partition Equal Subset Sum (M), Target Sum (M), Coin Change II (M)
  - LCS: `dp[i][j]` = LCS của `a[:i]`, `b[:j]`; bằng nhau thì `dp[i-1][j-1] + 1`, khác thì
    max hai hướng. Ứng dụng thật: `diff`, so sánh văn bản
  - ⚠️ Nói được độ phức tạp = số trạng thái × chi phí mỗi chuyển
- [ ] 🟡 **Bit manipulation**
  - Dấu hiệu: "không dùng thêm bộ nhớ", số xuất hiện lẻ lần, tập con với n nhỏ (bitmask)
  - Mẹo: `x ^ x = 0`; `x & (x - 1)` xoá bit 1 thấp nhất; `x & -x` lấy bit 1 thấp nhất;
    kiểm tra bit `(x >> i) & 1`
  - ⚠️ Dịch phải số âm: Java có `>>` (giữ dấu) và `>>>` (điền 0); PHP int 64-bit có dấu
  - Backend thật: bit flag quyền, bitmap (Redis `SETBIT`/`BITCOUNT` cho điểm danh hằng ngày)
  - Bài: Single Number (E), Number of 1 Bits (E), Counting Bits (E), Missing Number (E),
    Sum of Two Integers (M)
- [ ] **Matrix**
  - Dấu hiệu: lưới 2D; xoay, xoắn ốc, đánh dấu tại chỗ
  - Khung: mảng hướng `dirs = [(0,1),(1,0),(0,-1),(-1,0)]`; kiểm tra biên trước khi truy cập;
    dùng chính ma trận hoặc hàng/cột đầu làm cờ để O(1) bộ nhớ
  - Bài: Valid Sudoku (M), Rotate Image (M), Spiral Matrix (M), Set Matrix Zeroes (M),
    Search a 2D Matrix (M)
- [ ] 🟡 **Thiết kế cấu trúc dữ liệu**
  - Dấu hiệu: "thiết kế class với các thao tác O(1)/O(log n)"; thường ghép hai cấu trúc
  - Bài: LRU Cache (M), Implement Trie (M), Design Add and Search Words Data Structure (M),
    Time Based Key-Value Store (M), LFU Cache (H)

### Làm bài trong phỏng vấn

- [ ] **Quy trình**
  1. Nhắc lại đề bằng lời của mình; hỏi input: kích thước, có sort không, có trùng/âm/rỗng,
     kiểu dữ liệu, output khi không có đáp án
  2. Chạy tay một ví dụ nhỏ, thêm một edge case
  3. Nói lời giải brute force và độ phức tạp trước, rồi tối ưu. Brute force đúng tốt hơn tối
     ưu dở dang
  4. Thống nhất hướng với người phỏng vấn trước khi code
  5. Code vừa nói vừa viết; tên biến rõ; tách hàm phụ
  6. Tự dò lại bằng ví dụ, rồi edge case; sửa lỗi trước khi họ chỉ ra
  7. Nói time/space cuối cùng và hướng cải thiện nếu còn
  - Kỹ năng tâm lý khi làm bài ở [25-interview-skills.md](25-interview-skills.md)
- [ ] **Edge case checklist**
  - Rỗng, một phần tử, hai phần tử
  - Tất cả giống nhau, có trùng, đã sort, sort ngược
  - Số âm, số 0, giá trị lớn nhất/nhỏ nhất của kiểu
  - Chuỗi rỗng, khoảng trắng, chữ hoa/thường, Unicode (tiếng Việt có dấu nhiều byte)
  - Không có đáp án, nhiều đáp án
  - Cây rỗng, cây lệch một phía; đồ thị không liên thông, có chu trình, self-loop
- [ ] ⚠️ **Cạm bẫy**
  - Off-by-one: biên vòng lặp `<` hay `<=`, biên nhị phân, độ dài đoạn `r - l + 1`
  - Overflow: tổng/tích vượt int 32-bit (Java `int`); Go `int` là 64-bit trên nền 64-bit
    nhưng vẫn có thể tràn; PHP int tràn thì tự thành float (mất chính xác mà không báo lỗi)
  - Sửa collection khi đang duyệt: Java `ConcurrentModificationException` (dùng `Iterator.remove`);
    Go xoá key map khi `range` thì được nhưng thêm key thì có thể thấy hoặc không; PHP `foreach`
    duyệt trên bản sao trừ khi dùng tham chiếu `&`
  - Đệ quy quá sâu: stack overflow với cây lệch hoặc n lớn; chuyển sang vòng lặp + stack
  - Chia chuỗi theo byte thay vì ký tự: `strlen`/`len` của Go và PHP đếm byte
  - Dùng object/slice làm key hoặc thêm tham chiếu thay vì bản sao vào kết quả
- [ ] **Đối chiếu** công cụ hay dùng khi làm bài

  | | Java | Go | PHP |
  |---|---|---|---|
  | Hash map | `HashMap` | `map[K]V` | array |
  | Set | `HashSet` | `map[K]struct{}` | array key |
  | Stack/queue | `ArrayDeque` | slice | `SplStack`/`SplQueue` |
  | Heap | `PriorityQueue` | `container/heap` | `SplMinHeap`/`SplPriorityQueue` |
  | Map có thứ tự | `TreeMap` | không có sẵn (sort key) | không có sẵn |

### Nửa thuật toán nửa hệ thống

Câu hỏi kiểu "dữ liệu không vừa một máy". Người phỏng vấn chấm cách chia nhỏ, đánh đổi chính
xác lấy bộ nhớ, và việc nhận ra công cụ có sẵn (DB, Redis, Spark, `sort` của Unix).

- [ ] 🟡 **Top-K trên dữ liệu lớn** (ví dụ: phần tử xuất hiện nhiều nhất trong 1 tỷ phần tử không vừa RAM)
  - Chia theo `hash(x) % N` thành N file: cùng giá trị luôn vào cùng file, nên đếm từng file
    trong RAM là chính xác
  - Mỗi file lấy top-K bằng min-heap kích thước k, rồi gộp các top-K
  - Luồng dữ liệu liên tục: Count-Min Sketch + heap (xấp xỉ), hoặc đếm theo cửa sổ thời gian
  - ⚠️ Không thể lấy top-K của mỗi máy chia ngẫu nhiên rồi gộp: một phần tử đứng thứ K+1 ở mọi
    máy có thể là top toàn cục. Chia theo hash mới gộp đúng được
- [ ] 🔴 **Đếm phần tử khác nhau** (số user duy nhất mỗi ngày)
  - Chính xác: set trong bộ nhớ (tốn O(số phần tử)), hoặc `COUNT(DISTINCT)` trong DB/OLAP
  - Xấp xỉ: HyperLogLog, bộ nhớ cố định vài KB, gộp được theo ngày/tuần
  - Hỏi lại yêu cầu: báo cáo tài chính cần chính xác; dashboard traffic thì sai số 1% chấp nhận được
- [ ] 🟡 **Dedup 1 tỷ URL**
  - Ước lượng: 1 tỷ × khoảng 100 byte ≈ 100 GB, không vừa RAM
  - Chính xác: chia theo hash thành các file vừa RAM, dedup từng file bằng set; hoặc external
    sort rồi bỏ phần tử liền kề trùng
  - Xấp xỉ, luồng liên tục (crawler): bloom filter; chấp nhận bỏ sót một ít URL mới do false positive
  - Chuẩn hoá trước khi so sánh (chữ hoa/thường ở host, dấu `/` cuối, thứ tự query param)
  - Lưu hash cố định độ dài (ví dụ 8–16 byte) thay vì URL đầy đủ để giảm bộ nhớ; ⚠️ hash ngắn thì có va chạm
- [ ] 🟡 **Sort file lớn hơn RAM (external sort)**
  - Pha 1: đọc từng khối vừa RAM, sort trong bộ nhớ, ghi ra file tạm (run)
  - Pha 2: K-way merge các run bằng min-heap chứa phần tử đầu của mỗi run; đọc/ghi có buffer
  - Số run quá lớn thì merge nhiều tầng. Chi phí chủ yếu là I/O tuần tự
  - Thực tế: `sort` của Unix đã làm external sort; DB dùng cùng ý tưởng khi `ORDER BY` vượt
    bộ nhớ sort (spill ra đĩa)
- [ ] 🔴 **Tìm trùng trên nhiều máy** (hai tập dữ liệu lớn ở nhiều máy, tìm phần tử chung)
  - Shuffle theo `hash(key) % số_máy`: mọi bản ghi cùng key về cùng máy, mỗi máy so sánh
    cục bộ. Đây là ý tưởng của MapReduce/Spark join
  - Một tập nhỏ: broadcast tập nhỏ tới mọi máy (broadcast join), không cần shuffle tập lớn
  - Gửi bloom filter của tập A sang máy giữ B để lọc trước, giảm dữ liệu truyền qua mạng
  - ⚠️ Key lệch (một key chiếm phần lớn dữ liệu) làm một máy quá tải; tách key nóng ra xử lý riêng
  - Xem [14-distributed-systems.md](14-distributed-systems.md) và [16-system-design.md](16-system-design.md)

### Lộ trình luyện theo tuần

Gợi ý cho người đi làm, khoảng 1 giờ mỗi ngày. Mỗi tuần: học pattern, làm 8–12 bài, cuối tuần
làm lại không nhìn các bài đã sai. Đồng bộ với checklist ở [`../dsa/README.md`](../dsa/README.md).

| Tuần | Nội dung | Mục tiêu |
|---|---|---|
| 1 | Big-O, array, hash map/set, two pointers | Giải easy trong 15 phút, nói được độ phức tạp |
| 2 | Sliding window, prefix sum, stack, monotonic stack | Nhận ra đoạn con liên tục → window/prefix |
| 3 | Binary search (cả trên đáp án), linked list | Viết binary search không lỗi biên |
| 4 | Tree DFS/BFS, BST, heap/top-K | Viết DFS trả thông tin cây con |
| 5 | Graph BFS/DFS, topological sort, union-find, Dijkstra | Dựng graph từ đề, chọn đúng thuật toán |
| 6 | Interval, greedy, backtracking | Lập luận được vì sao greedy đúng |
| 7 | DP 1D, 2D, knapsack, LCS | Định nghĩa trạng thái bằng lời trước khi code |
| 8 | Bit, matrix, thiết kế cấu trúc (LRU, Trie), mock interview | Làm medium trong 25–30 phút, nói liên tục |

- Ôn lặp lại: bài sai đánh dấu, làm lại sau 3 ngày và sau 1 tuần
- Mock interview với bạn hoặc tự ghi âm; tập nói trong lúc code
- Mỗi pattern cài một bản trong [`../dsa/`](../dsa/) bằng hai ngôn ngữ

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Vì sao hash map O(1)? | "Vì tính hash rồi truy cập thẳng." | "O(1) trung bình khi hash phân bố đều và load factor được giữ dưới ngưỡng bằng resize. Worst O(n) khi va chạm, kể cả do tấn công hash flooding; Java chuyển bucket dài sang cây nên worst còn O(log n). Resize là O(n), chỉ amortized O(1)." |
| Top-K phần tử phổ biến nhất? | "Đếm bằng map rồi sort." | "Map + min-heap kích thước K cho O(n log K). Không vừa RAM thì chia theo hash rồi gộp. Luồng liên tục thì Count-Min Sketch + heap, chấp nhận xấp xỉ. Nếu dữ liệu đã ở DB thì `GROUP BY ... ORDER BY ... LIMIT K` với index phù hợp." |
| Đếm user duy nhất mỗi ngày? | "Dùng set." | "Hỏi cần chính xác không. Dashboard thì HyperLogLog trong Redis, vài KB mỗi ngày, gộp theo tuần được. Báo cáo tính tiền thì phải chính xác, làm trong OLAP bằng `COUNT(DISTINCT)`." |
| Vì sao DB dùng B+tree mà không dùng hash hay BST? | "Vì B+tree nhanh." | "Đơn vị đọc là page đĩa; B+tree nhiều key mỗi node nên cây chỉ vài tầng. Lá nối nhau nên range scan và `ORDER BY` rẻ, hash không làm được. BST nhị phân quá cao, mỗi tầng là một lần đọc page." |
| Làm bài xong code chạy đúng ví dụ. | "Xong rồi ạ." | Tự dò edge case (rỗng, trùng, âm, overflow), nói time/space, nói hướng tối ưu hoặc trade-off bộ nhớ, trước khi được hỏi. |

## Tình huống

1. **Cần leaderboard realtime cho 10 triệu user, hỏi hạng của một user bất kỳ.**
   - Gợi ý: Redis sorted set (skip list) cho `ZADD`, `ZREVRANK` O(log n); sort trong DB mỗi
     lần là quá đắt; cân nhắc hạng xấp xỉ theo bucket điểm nếu quy mô lớn hơn nhiều.
2. **API kiểm tra "username đã tồn tại" bị gọi rất nhiều, phần lớn là tên chưa tồn tại.**
   - Gợi ý: bloom filter trước DB để trả "chắc chắn chưa có" nhanh; "có thể có" thì hỏi DB;
     unique index trong DB vẫn là nguồn sự thật; bloom filter phải được rebuild khi dữ liệu lớn lên.
3. **Cần tìm các cặp tài khoản trùng qua email, số điện thoại, thiết bị.**
   - Gợi ý: union-find trên các định danh; hoặc graph connected components; chạy batch; chú ý
     định danh dùng chung (số điện thoại công ty) tạo một nhóm khổng lồ.
4. **Autocomplete tìm kiếm sản phẩm theo prefix.**
   - Gợi ý: trie hoặc sorted list + binary search cho tập nhỏ; quy mô lớn thì search engine
     (edge n-gram); lưu top-K gợi ý tại mỗi node; tiếng Việt cần chuẩn hoá bỏ dấu.
5. **Job chạy các bước có phụ thuộc lẫn nhau, cần phát hiện cấu hình vòng.**
   - Gợi ý: topological sort (Kahn), báo lỗi khi còn node chưa xử lý; chạy song song các node
     cùng lúc có in-degree 0.
6. **Sort log 500 GB theo thời gian trên máy 16 GB RAM.**
   - Gợi ý: external sort, run khoảng vài GB, K-way merge bằng heap; hoặc dùng `sort` của Unix,
     hoặc đẩy vào công cụ phân tán nếu cần lặp lại thường xuyên.

## ❓ Câu hỏi hay gặp

🟢
- Big-O của lời giải bạn vừa viết là gì, vì sao?
- Array và linked list khác nhau thế nào, khi nào dùng cái nào?
- Stack và queue dùng vào việc gì trong thực tế?
- Merge sort và quick sort khác nhau thế nào? Cái nào stable?
- Vì sao hash map là O(1) trung bình nhưng O(n) trong trường hợp xấu nhất?

🟡
- Amortized O(1) của dynamic array nghĩa là gì?
- Thiết kế LRU cache với get/put O(1).
- Bloom filter là gì, có false negative không?
- Vì sao Redis sorted set dùng skip list?
- Khi nào BFS, khi nào DFS, khi nào Dijkstra?
- Làm sao nhận ra một bài là DP?
- Tìm phần tử xuất hiện nhiều nhất trong mảng 1 tỷ phần tử không vừa RAM.

🔴
- Consistent hashing giải quyết vấn đề gì? Redis Cluster có dùng không?
- Đếm số user duy nhất mỗi ngày trên hàng tỷ event.
- Sort một file lớn hơn RAM.
- Tìm phần tử chung giữa hai tập dữ liệu lớn nằm trên nhiều máy.
- Vì sao index DB dùng B+tree, còn nhiều hệ thống ghi nhiều dùng LSM tree?

## Bài tập tự làm

1. Cài LRU cache bằng hash map + doubly linked list trong [`../dsa/`](../dsa/) bằng Go, rồi
   bằng Java; ghi độ phức tạp từng thao tác.
2. Với 10 bài trong mục Pattern bạn chưa làm, chỉ đọc đề và viết ra: pattern nào, vì sao,
   độ phức tạp dự kiến. Sau đó mới giải.
3. Ước lượng bộ nhớ cần để dedup 1 tỷ URL bằng set chính xác và bằng bloom filter với tỉ lệ
   false positive 1%. Trình bày cách tính.
4. Giải thích bằng lời (không code) vì sao Dijkstra sai khi có cạnh âm, kèm một đồ thị 3–4
   node làm phản ví dụ.
5. Viết `topK(stream, k)` cho luồng dữ liệu không biết trước độ dài; nêu độ phức tạp và điều
   gì thay đổi khi dữ liệu không vừa một máy.

> Nộp bài vào đây để được review.
