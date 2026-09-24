# Go

Chạy một bài: `go run ./go/01-basics`

## Cách dùng checklist này

Ba mức — **N** (Nền tảng: viết đúng), **V** (Vững: giải thích được cơ chế),
**S** (Senior: nêu được đánh đổi + debug được trên production).
Tick `[x]` khi **giảng lại được mà không mở tài liệu**. Giải thích đầy đủ ở `java/README.md`.

## Lộ trình bài học trong repo

- [x] **01-basics** — biến & zero value, hàm nhiều giá trị trả về, slice/map, struct & method, error là giá trị
- [ ] 02-interface — interface ngầm định, type assertion, bẫy nil interface
- [ ] 03-goroutine — goroutine, `sync` package, race detector
- [ ] 04-channel — channel, `select`, `context`, các pattern concurrency
- [ ] 05-error — wrap lỗi, sentinel error, custom error type
- [ ] 06-generics — type parameter, constraint, khi nào **không** dùng
- [ ] 07-stdlib — `net/http`, `encoding/json`, `database/sql`
- [ ] 08-runtime — scheduler, escape analysis, GC
- [ ] 09-profiling — pprof, trace, benchmark
- [ ] 10-production — graceful shutdown, observability, cấu hình

---

## Checklist ôn tập

### 1. Ngôn ngữ & bộ nhớ

- [ ] **N** — zero value, `:=` vs `var`, con trỏ, `new` vs `make`
- [ ] **N** — struct, method, receiver value vs pointer
- [ ] **V** — **slice là struct 3 trường** (ptr, len, cap): vẽ được ra giấy
- [ ] **V** — vì sao `append` đôi khi sửa mảng gốc, đôi khi không; `s[:0]`, `s[a:b:c]` (full slice expression) dùng làm gì
- [ ] **V** — bẫy slice giữ reference: cắt một phần tử nhỏ từ slice lớn vẫn giữ nguyên mảng lớn trong memory → leak
- [ ] **V** — map: không sắp thứ tự, **không** an toàn khi ghi song song (panic chứ không phải sai âm thầm), không lấy được địa chỉ phần tử
- [ ] **V** — string là byte bất biến; `len(s)` đếm **byte** chứ không phải ký tự; `range` trên string trả rune
- [ ] **V** — receiver value copy toàn bộ struct: khi nào điều đó tốn kém, khi nào lại tốt (tránh alias)
- [ ] **S** — **escape analysis**: khi nào biến lên heap; đọc kết quả bằng `go build -gcflags='-m'`
- [ ] **S** — struct alignment & padding: sắp xếp lại field để struct nhỏ đi (`fieldalignment`)
- [ ] **S** — `defer` tốn bao nhiêu (open-coded defer từ Go 1.14); bẫy `defer` trong vòng lặp
- [ ] **S** — bẫy closure bắt biến vòng lặp (và vì sao Go 1.22 đổi ngữ nghĩa biến vòng `for`)

### 2. Interface & thiết kế kiểu

- [ ] **N** — interface được thỏa mãn **ngầm định**, không cần `implements`
- [ ] **N** — type assertion, type switch
- [ ] **V** — interface value gồm **2 word** (type, value) → **bẫy nil interface**: con trỏ nil bọc trong interface thì `!= nil`
- [ ] **V** — "accept interface, return struct"; định nghĩa interface ở phía **người dùng** chứ không phải phía người cài đặt
- [ ] **V** — interface nhỏ là tốt: `io.Reader`, `io.Writer`, `error`, `fmt.Stringer`
- [ ] **S** — chi phí runtime của interface: itab, dynamic dispatch, cản trở inlining
- [ ] **S** — embedding để composition; vì sao nó **không phải** kế thừa
- [ ] **S** — khi nào dùng generics thay interface, và vì sao generics **không** thay thế được interface

### 3. Error handling

- [ ] **N** — `if err != nil`, `errors.New`, `fmt.Errorf`
- [ ] **V** — wrap bằng `%w`; `errors.Is` (so sánh sentinel) vs `errors.As` (ép về kiểu cụ thể)
- [ ] **V** — sentinel error vs custom error type vs opaque error: chọn cái nào khi nào
- [ ] **V** — `panic`/`recover` chỉ dùng cho lỗi lập trình, **không** dùng thay exception; recover chỉ chạy được trong `defer`
- [ ] **S** — thiết kế error cho một package public: người gọi cần phân biệt được lỗi nào, và bạn cam kết gì về chúng
- [ ] **S** — thêm ngữ cảnh mà không làm lộ chi tiết nội bộ; lỗi có nên mang stack trace không
- [ ] **S** — đối chiếu với exception của Java/PHP: mô hình nào an toàn hơn, cái giá phải trả là gì

### 4. Concurrency — goroutine

- [ ] **N** — `go func()`, `sync.WaitGroup`, `sync.Mutex`
- [ ] **V** — goroutine leak: goroutine chặn mãi trên channel không ai đọc — cách phát hiện (`runtime.NumGoroutine`, pprof goroutine)
- [ ] **V** — "Do not communicate by sharing memory; share memory by communicating" — và khi nào mutex **vẫn** là lựa chọn đúng
- [ ] **V** — `sync.RWMutex`, `sync.Once`, `sync/atomic`, `sync.Pool` (dùng đúng chỗ)
- [ ] **V** — `-race`: cách nó hoạt động, vì sao chỉ bắt được race **thực sự xảy ra** lúc chạy
- [ ] **S** — **GMP scheduler**: goroutine / machine (OS thread) / processor; work stealing; `GOMAXPROCS`
- [ ] **S** — preemption: trước Go 1.14 vòng lặp chặt có thể treo scheduler; giờ preempt bằng tín hiệu
- [ ] **S** — syscall chặn làm gì với P; vì sao goroutine rẻ (stack 2KB, tự lớn lên) so với OS thread
- [ ] **S** — Go memory model: happens-before của channel, mutex, `sync/atomic` — trả lời được "code này có race không" bằng lý thuyết chứ không chỉ bằng `-race`

### 5. Concurrency — channel & pattern

- [ ] **N** — channel có buffer / không buffer; `close`; `for range` trên channel
- [ ] **V** — `select` + `default`; nil channel chặn vĩnh viễn (và dùng điều đó làm gì)
- [ ] **V** — ai được quyền `close` (người gửi), gửi vào channel đã đóng → panic
- [ ] **V** — `context`: hủy tác vụ, timeout, truyền theo cây goroutine; vì sao **không** nhét dữ liệu nghiệp vụ vào context
- [ ] **S** — pattern: worker pool, fan-in/fan-out, pipeline, semaphore bằng buffered channel, `errgroup`
- [ ] **S** — backpressure: hàng đợi unbounded là bom hẹn giờ (giống thread pool của Java)
- [ ] **S** — chọn giữa channel và mutex: channel để **chuyển quyền sở hữu**, mutex để **bảo vệ state**
- [ ] **S** — graceful shutdown đúng: bắt signal → ngừng nhận việc mới → chờ việc đang chạy → timeout cứng

### 6. Generics

- [ ] **N** — type parameter, constraint cơ bản, `any`, `comparable`
- [ ] **V** — constraint bằng union type; type inference tới đâu
- [ ] **V** — GC shape stenciling: Go cài generics ra sao (không phải template C++, cũng không phải erasure Java)
- [ ] **S** — khi nào generics làm code **tệ hơn**; vì sao stdlib Go dùng generics rất dè dặt

### 7. Stdlib & viết service

- [ ] **N** — `net/http` server & client, `encoding/json`, `flag`/`os.Args`
- [ ] **V** — `http.Client` mặc định **không có timeout** → bug production kinh điển; tái dùng client, không tạo mới mỗi request
- [ ] **V** — nhớ `defer resp.Body.Close()` và **đọc hết** body, nếu không sẽ rò connection
- [ ] **V** — `http.Server` timeout: `ReadTimeout`, `WriteTimeout`, `IdleTimeout`; middleware qua `http.Handler`
- [ ] **V** — `database/sql`: pool (`SetMaxOpenConns`, `SetMaxIdleConns`, `SetConnMaxLifetime`), luôn đóng `Rows`
- [ ] **V** — JSON: tag, `omitempty`, con trỏ để phân biệt "không có" với "bằng 0", `json.Decoder` cho stream
- [ ] **S** — `context` xuyên suốt từ HTTP request → DB query để hủy dây chuyền
- [ ] **S** — cấu trúc project: vì sao "standard layout" gây tranh cãi; cắt package theo miền nghiệp vụ, tránh package `utils`
- [ ] **S** — cấu hình & secret, structured logging (`log/slog`), health check, graceful shutdown

### 8. Runtime, GC & hiệu năng

- [ ] **V** — GC của Go: concurrent mark & sweep, **không** nén (non-moving), mục tiêu pause rất ngắn
- [ ] **V** — `GOGC` và `GOMEMLIMIT` (Go 1.19+) điều khiển gì; đánh đổi giữa memory và CPU
- [ ] **V** — allocation là thứ tốn kém: giảm alloc thường hiệu quả hơn tối ưu thuật toán vi mô
- [ ] **S** — đọc `go build -gcflags='-m'` để biết cái gì escape và vì sao
- [ ] **S** — `sync.Pool` giảm áp lực GC — và vì sao dùng sai lại thành nguồn bug
- [ ] **S** — Go trong container: `GOMAXPROCS` không tự đọc CPU limit của cgroup → phải set (hoặc dùng `automaxprocs`)
- [ ] **S** — so sánh với JVM: không cần warm-up, không có JIT, binary tĩnh, khởi động nhanh — đổi lại là gì

### 9. Đo đạc & gỡ lỗi

- [ ] **N** — `go test -bench`, `go vet`, `gofmt`
- [ ] **V** — benchmark đúng cách: `b.N`, `b.ResetTimer`, `-benchmem`; `benchstat` để so sánh có ý nghĩa thống kê
- [ ] **V** — `net/http/pprof`: CPU profile, heap profile, goroutine profile, block/mutex profile
- [ ] **S** — đọc flame graph; phân biệt "chậm do CPU" với "chậm do chờ"
- [ ] **S** — `go tool trace`: nhìn thấy scheduler latency, GC, syscall chặn
- [ ] **S** — quy trình gỡ "service ngốn memory": heap profile → tìm nơi alloc → xem có giữ reference không
- [ ] **S** — `GODEBUG=gctrace=1`, `schedtrace`; công cụ `go tool` nào giải quyết bài toán nào

### 10. Module, build & vận hành

- [ ] **N** — `go.mod`, `go get`, `go mod tidy`
- [ ] **V** — minimal version selection (khác hẳn npm/composer); `go.sum` bảo đảm điều gì
- [ ] **V** — build tag, cross-compile (`GOOS`/`GOARCH`), `-ldflags` để nhúng version
- [ ] **S** — vendoring, replace directive, private module proxy
- [ ] **S** — binary tĩnh & Docker image từ `scratch`/`distroless`; cgo làm hỏng tính tĩnh ra sao
- [ ] **S** — cam kết tương thích ngược của Go, và ý nghĩa với việc nâng version

---

## Điểm khác biệt cần nhớ khi đến từ Java/PHP

- Không có class, không kế thừa. Chỉ struct + method + interface (composition).
- Không exception cho lỗi thường: lỗi là giá trị trả về, phải kiểm tra tay.
- Biến hoặc import khai báo mà không dùng là **lỗi biên dịch**, không phải warning.
- Chữ đầu viết hoa = public (export khỏi package), viết thường = private.
- Interface thỏa mãn ngầm định → package của bạn không cần biết interface tồn tại.
- Không có constructor, không overload, không default parameter — cố tình đơn giản hóa.

## Câu hỏi tự kiểm tra mức senior

1. Vẽ cấu trúc slice. Khi nào `append` sửa mảng gốc? Viết một ví dụ gây bug vì điều đó.
2. Vì sao một con trỏ `nil` gán vào biến interface lại khiến `err != nil` thành `true`?
3. Goroutine leak xảy ra thế nào? Nêu 3 nguyên nhân hay gặp và cách phát hiện trên production.
4. Khi nào dùng channel, khi nào dùng mutex? Cho một ví dụ mà channel là lựa chọn **sai**.
5. `context.WithTimeout` hủy tác vụ bằng cách nào? Nó có **giết** được goroutine đang chạy không?
6. `GOMAXPROCS` trong container mặc định lấy giá trị từ đâu, và vì sao đó là vấn đề?
7. Service tăng dần RSS suốt 3 ngày rồi OOM. Bạn dùng công cụ gì, theo thứ tự nào?
8. `-race` báo sạch có nghĩa là code không có race không? Vì sao?
9. `http.Client` mặc định gây ra sự cố production kiểu gì?
10. So sánh mô hình concurrency của Go với virtual thread của Java: giống và khác chỗ nào?

## Bài tập cho 01-basics

1. Viết `func DemTuXuatHien(s string) map[string]int` đếm số lần mỗi từ xuất hiện.
2. Sửa `timNgonNgu` để nhận thêm tham số năm và trả về mọi ngôn ngữ ra đời năm đó.
3. Thử bỏ một biến không dùng vào `main` — đọc kỹ thông báo lỗi của compiler.
4. Tạo slice 1 triệu phần tử, cắt lấy 3 phần tử rồi giữ lại — chứng minh mảng gốc vẫn chưa được giải phóng.
5. Chạy `go build -gcflags='-m' ./go/01-basics` và giải thích từng dòng "escapes to heap".
