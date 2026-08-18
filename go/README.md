# Go

Chạy một bài: `go run ./go/01-basics`

## Lộ trình

- [x] **01-basics** — biến & zero value, hàm nhiều giá trị trả về, slice/map, struct & method, error là giá trị
- [ ] 02-interface — interface ngầm định, type assertion, `io.Reader`/`io.Writer`
- [ ] 03-goroutine — goroutine, `sync.WaitGroup`, race condition, `-race`
- [ ] 04-channel — channel có/không buffer, `select`, `context` để hủy tác vụ
- [ ] 05-testing — table-driven test, benchmark, coverage
- [ ] 06-stdlib — `net/http`, `encoding/json`, viết một HTTP API nhỏ
- [ ] 07-generics — type parameter, constraint

## Điểm khác biệt cần nhớ khi đến từ Java/PHP

- Không có class, không kế thừa. Chỉ có struct + method + interface (composition).
- Không dùng exception cho lỗi thường: lỗi là giá trị trả về, phải kiểm tra tay.
- Biến hoặc import khai báo mà không dùng là **lỗi biên dịch**, không phải warning.
- Chữ đầu viết hoa = public (export ra ngoài package), viết thường = private.

## Bài tập cho 01-basics

1. Viết `func DemTuXuatHien(s string) map[string]int` đếm số lần mỗi từ xuất hiện.
2. Sửa `timNgonNgu` để nhận thêm tham số năm và trả về mọi ngôn ngữ ra đời năm đó.
3. Thử bỏ một biến không dùng vào `main` — đọc kỹ thông báo lỗi của compiler.
