# DSA — Cấu trúc dữ liệu & Thuật toán

Mỗi thuật toán được cài lại bằng nhiều ngôn ngữ để so sánh cách diễn đạt.

```bash
go test ./dsa/go/... -v          # bản Go, có test
java dsa/java/BinarySearch.java  # bản Java, test trong main
```

## Lộ trình

**Nền tảng**
- [x] Big-O, tìm kiếm nhị phân + `lowerBound` (`go/searching`, `java/BinarySearch.java`)
- [ ] Hai con trỏ, sliding window
- [ ] Sorting: insertion, merge, quick — và vì sao thư viện chuẩn chọn cái nào

**Cấu trúc dữ liệu**
- [ ] Mảng động, linked list
- [ ] Stack, queue, deque
- [ ] Hash table (tự cài để hiểu collision)
- [ ] Cây nhị phân, BST, duyệt cây
- [ ] Heap / priority queue
- [ ] Union-Find, Trie

**Thuật toán**
- [ ] Đệ quy & backtracking
- [ ] Dynamic programming (từ đệ quy → memo → bottom-up)
- [ ] Đồ thị: BFS, DFS, Dijkstra, topological sort
- [ ] Greedy

## Cách học mỗi chủ đề

1. Đọc bài toán, tự vẽ ví dụ nhỏ **bằng tay** trước khi viết code.
2. Cài bản thô, chạy đúng đã.
3. Viết test cho các ca biên: rỗng, 1 phần tử, trùng nhau, không tìm thấy, biên đầu/cuối.
4. Nói ra độ phức tạp thời gian và bộ nhớ, giải thích **vì sao**.
5. Cài lại ở ngôn ngữ thứ hai — chỗ nào thấy khó là chỗ chưa hiểu kỹ.

## Bài tập cho tìm kiếm nhị phân

1. Viết `UpperBound` (chỉ số đầu tiên có `nums[i] > target`) rồi dùng nó đếm số lần target xuất hiện.
2. Tìm chỉ số nhỏ nhất mà `nums[i] >= target` trong mảng **giảm dần**.
3. Áp dụng nhị phân trên đáp án: tìm căn bậc hai nguyên của `n` không dùng `math.Sqrt`.
