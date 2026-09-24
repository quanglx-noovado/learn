# 01. Hệ điều hành và Linux

> [← Mục lục](README.md) · Phạm vi: process/thread, bộ nhớ, I/O, signal, file system, và Linux
> thực hành để vận hành, debug backend trên production.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Process, thread, scheduling**
- [ ] 🟢 Process và thread: cái gì dùng chung, cái gì riêng
- [ ] 🟢 Khi nào multi-process, khi nào multi-thread
- [ ] 🟡 Context switch: vì sao tốn, voluntary và involuntary
- [ ] 🟡 Thread OS, green thread, coroutine; mô hình 1:1, N:1, M:N
- [ ] 🟡 Scheduler của Linux ở mức đại ý: time slice, preemption, nice, CPU affinity
- [ ] 🟢 Mô hình chạy: PHP-FPM, Java thread-per-request, virtual thread, goroutine, Node event loop
- [ ] 🔴 CPU-bound và I/O-bound; vì sao số worker tối ưu khác nhau
- [ ] 🟡 Trạng thái process: R, S, D, Z, T; zombie và orphan

**Bộ nhớ**
- [ ] 🟢 Stack và heap
- [ ] 🟡 Virtual memory, paging, page fault (minor/major), RSS và VSZ
- [ ] 🟡 Page cache: vì sao "free" thấp không có nghĩa là thiếu RAM
- [ ] 🟡 Swap và vì sao server thường tắt/giảm swap
- [ ] 🟡 OOM killer, `oom_score_adj`
- [ ] 🔴 cgroup memory limit trong container; runtime (JVM, Go) có nhìn thấy limit không
- [ ] 🟡 Memory leak trong ngôn ngữ có GC
- [ ] 🔴 Copy-on-write khi `fork()` (PHP-FPM, Redis BGSAVE)

**I/O**
- [ ] 🟢 File descriptor, `too many open files`, `ulimit`
- [ ] 🟡 Blocking, non-blocking, I/O multiplexing
- [ ] 🟡 `select`/`poll`/`epoll`; level-triggered và edge-triggered
- [ ] 🔴 io_uring
- [ ] 🔴 Zero-copy, `sendfile`

**Signal và vòng đời process**
- [ ] 🟢 SIGTERM, SIGKILL, SIGINT, SIGHUP; cái nào bắt được
- [ ] 🟡 Graceful shutdown
- [ ] 🔴 PID 1 trong container: signal, zombie, `tini`
- [ ] 🟡 Exit code: 137, 143, 139

**File system**
- [ ] 🟢 Inode; hard link và soft link
- [ ] 🟢 Permission: `rwx`, owner/group/other, `chmod`/`chown`, umask
- [ ] 🟡 Xoá file đang mở: disk không được giải phóng
- [ ] 🔴 `fsync`, durability, ghi file an toàn bằng rename
- [ ] 🟡 Disk đầy vì inode chứ không phải dung lượng

**Linux thực hành**
- [ ] 🟢 Process và tài nguyên: `ps`, `top`/`htop`, `free`, `vmstat`, `iostat`, `df`/`du`
- [ ] 🟡 `lsof`, `ss`/`netstat`, `strace`, `dmesg`, `journalctl`
- [ ] 🟢 Log: `tail -f`, `grep`, `awk`, `sed`, `less`, `sort | uniq -c`
- [ ] 🟢 Mạng: `curl`, `dig`, `ping`, `traceroute`/`mtr`, `nc`
- [ ] 🟡 Load average nghĩa là gì
- [ ] 🔴 CPU steal, CPU throttling trong container
- [ ] 🟡 systemd: unit, restart policy, `journalctl -u`
- [ ] 🟡 cron và các cạm bẫy: timezone, biến môi trường, chạy trùng
- [ ] 🟢 ssh: key, `~/.ssh/config`, port forwarding, bastion
- [ ] 🟡 Shell script: `set -euo pipefail`, quote biến, `trap`

## Chi tiết

### Process, thread, scheduling

- [ ] Process và thread 🟢
  - Process có không gian địa chỉ riêng, bảng file descriptor riêng. Các thread trong cùng
    process dùng chung heap, code, file descriptor, nhưng mỗi thread có stack và register riêng
  - Tạo process tốn hơn tạo thread; process cô lập tốt hơn: một process crash (segfault)
    không kéo theo process khác, một thread crash thường kéo cả process
  - Multi-process khi cần cô lập lỗi, dễ quản lý bộ nhớ (process chết là trả hết RAM),
    hoặc runtime không thread-safe (PHP). Multi-thread khi cần chia sẻ state nhanh, ít overhead
  - Trên Linux, thread và process đều là "task" tạo bằng `clone()`, khác nhau ở cờ chia sẻ gì
- [ ] Context switch 🟡
  - Kernel lưu register, program counter, chuyển stack; nếu đổi process thì đổi luôn bảng
    page (TLB bị flush một phần). Chi phí gián tiếp lớn hơn: CPU cache bị "nguội"
  - Voluntary: thread tự nhường vì chờ I/O, lock. Involuntary: hết time slice, bị preempt.
    Xem bằng `pidstat -w` hoặc `/proc/<pid>/status` (`voluntary_ctxt_switches`)
  - ⚠️ Quá nhiều thread cho việc CPU-bound → thời gian đổ vào context switch thay vì làm việc
- [ ] Thread OS, green thread, coroutine 🟡
  - **1:1**: mỗi thread ngôn ngữ là một thread OS (Java platform thread, C pthread)
  - **N:1**: nhiều green thread trên một thread OS; một cái block syscall là cả nhóm đứng
  - **M:N**: runtime ghép M thread nhẹ lên N thread OS. Goroutine, Java virtual thread
    (Java 21) đều là M:N, do runtime lập lịch, không phải kernel
  - Coroutine: hàm có thể tạm dừng và tiếp tục; cooperative (tự nhường ở điểm `await`/`yield`)
  - Stack goroutine khởi đầu nhỏ (2 KB ở các bản Go gần đây) và tự giãn; stack thread OS mặc
    định trên Linux thường 8 MB (theo `ulimit -s`), Java `-Xss` mặc định cỡ 1 MB (kiểm tra lại
    theo phiên bản bạn dùng). Đây là virtual memory reserve, RSS thực tế nhỏ hơn
  - Vì vậy chạy được hàng trăm nghìn goroutine, còn hàng trăm nghìn thread OS sẽ vướng bộ nhớ,
    giới hạn `threads-max`/`pid_max`, và chi phí context switch của kernel
- [ ] Scheduler Linux đại ý 🟡
  - Preemptive: kernel chia time slice, cắt ngang thread đang chạy. CFS (và EEVDF từ kernel 6.6)
    cố chia CPU công bằng theo trọng số `nice`
  - `nice`/`renice` đổi ưu tiên; `taskset` ghim CPU (CPU affinity)
- [ ] Trạng thái process 🟡
  - `R` running/runnable, `S` sleep chờ sự kiện (bị ngắt được), `D` uninterruptible sleep
    (thường chờ disk/NFS, không kill được kể cả SIGKILL cho tới khi I/O xong), `Z` zombie,
    `T` stopped
  - Zombie: process con đã chết nhưng cha chưa `wait()` để lấy exit code. Không tốn RAM,
    nhưng chiếm PID. Orphan: cha chết trước, con được PID 1 (hoặc subreaper) nhận nuôi
- [ ] CPU-bound và I/O-bound 🔴
  - CPU-bound: số worker ≈ số core; thêm nữa chỉ tăng context switch
  - I/O-bound: worker phần lớn thời gian chờ, nên cần nhiều hơn số core, hoặc dùng mô hình
    non-blocking/thread nhẹ
  - Công thức kinh điển: threads ≈ cores × (1 + wait_time / compute_time). Chỉ là điểm xuất
    phát, phải đo

**Mô hình chạy của từng runtime**

| Runtime | Đơn vị xử lý request | Chặn I/O thì sao | Giới hạn thường gặp |
|---|---|---|---|
| PHP-FPM | 1 process / 1 request | process đó đứng chờ | `pm.max_children`, RAM mỗi worker |
| Java servlet (Tomcat) | 1 platform thread / request | thread đứng chờ | thread pool (Tomcat mặc định 200, kiểm tra lại) |
| Java virtual thread | 1 virtual thread / request | runtime unmount, carrier thread làm việc khác | pinning, connection pool DB |
| Go `net/http` | 1 goroutine / request | runtime park goroutine, dùng netpoller (epoll) | connection pool, bộ nhớ |
| Node.js | callback/promise trên 1 event loop | I/O không chặn; CPU nặng thì chặn tất cả | CPU-bound code, libuv threadpool |

- [ ] PHP-FPM 🟢
  - Master process quản lý pool worker. `pm = static | dynamic | ondemand`; `pm.max_children`
    là trần số request đồng thời
  - Mỗi request khởi tạo app từ đầu (share-nothing), nên không rò state giữa request, nhưng tốn
    bootstrap. OPcache giữ bytecode trong shared memory
  - Sizing: `pm.max_children ≈ RAM dành cho FPM / RSS trung bình mỗi worker`
  - `pm.max_requests` recycle worker định kỳ để chặn leak; `request_terminate_timeout` giết
    request treo
  - ⚠️ Hết worker → Nginx xếp hàng rồi trả 502/504. Một API ngoài chậm có thể chiếm hết worker
  - Octane/Swoole/RoadRunner/FrankenPHP giữ app trong bộ nhớ: nhanh hơn nhưng phải cẩn thận
    state rò giữa request (singleton, static)
- [ ] Java thread-per-request và virtual thread 🟡
  - Platform thread là 1:1 với thread OS; thread pool giới hạn số request đồng thời
  - Virtual thread (JDK 21): khi block I/O, virtual thread được unmount khỏi carrier thread
  - ⚠️ Pinning: trước JDK 24, block bên trong `synchronized` giữ luôn carrier thread
    (JEP 491 sửa ở JDK 24). Native call vẫn pin
  - ⚠️ Virtual thread không làm DB nhanh hơn: 10.000 virtual thread vẫn tranh 20 connection
    trong pool. Bottleneck chuyển xuống tài nguyên phía sau
  - Không pool virtual thread; muốn giới hạn đồng thời thì dùng `Semaphore`
- [ ] Goroutine 🟡
  - Scheduler G-M-P: G (goroutine), M (thread OS), P (processor logic, số lượng = `GOMAXPROCS`)
  - Work stealing giữa các P; syscall block thì M bị tách khỏi P, P lấy M khác chạy tiếp
  - ⚠️ Goroutine leak: goroutine chờ channel mãi không ai gửi → giữ bộ nhớ vĩnh viễn
- [ ] Node event loop 🟢
  - Một thread JS chạy event loop; I/O mạng dùng epoll/kqueue qua libuv; file I/O, DNS
    (`getaddrinfo`), crypto chạy trên libuv threadpool (mặc định 4, `UV_THREADPOOL_SIZE`)
  - ⚠️ Một vòng lặp CPU nặng, `JSON.parse` payload lớn, regex backtracking → toàn bộ server đứng
  - Scale bằng nhiều process (cluster, PM2, nhiều pod) hoặc worker_threads
- **Đối chiếu:** PHP cô lập bằng process, Java/Go chia sẻ bộ nhớ trong process nên phải lo
  thread-safety (xem [13-concurrency.md](13-concurrency.md)), Node tránh race trên JS nhưng
  không tránh được race giữa các request async đan xen

### Bộ nhớ

- [ ] Stack và heap 🟢
  - Stack: biến cục bộ, frame hàm; cấp/thu tự động khi vào/ra hàm; nhỏ, mỗi thread một stack.
    Tràn stack (đệ quy sâu) → `StackOverflowError` (Java), `goroutine stack exceeds` (Go),
    segfault (C)
  - Heap: object sống lâu hơn hàm; GC (Java, Go, PHP refcount + cycle collector) hoặc lập trình
    viên giải phóng
  - Go: escape analysis quyết định biến nằm stack hay heap (`go build -gcflags=-m`)
- [ ] Virtual memory và paging 🟡
  - Mỗi process thấy một dải địa chỉ ảo riêng; MMU dịch địa chỉ ảo → vật lý qua page table,
    theo đơn vị page (thường 4 KB)
  - Lợi ích: cô lập process, cấp phát lười (chỉ có RAM thật khi chạm vào), map file vào bộ nhớ
    (`mmap`), chia sẻ thư viện
  - Page fault: minor (page có trong RAM, chỉ chưa map), major (phải đọc từ disk/swap, chậm)
  - VSZ: tổng virtual đã reserve. RSS: phần đang nằm trong RAM. ⚠️ Đừng hoảng vì VSZ lớn
  - Overcommit: Linux cho `malloc` nhiều hơn RAM thực, tới khi chạm vào mà hết RAM thì OOM
- [ ] Page cache 🟡
  - Kernel dùng RAM rảnh để cache nội dung file. Đọc file lần hai nhanh vì đã ở page cache
  - `free -h`: nhìn cột `available`, không nhìn `free`. RAM "free" thấp là bình thường
  - Write cũng đi qua page cache (dirty page), kernel flush sau → liên quan tới `fsync`
  - Database (PostgreSQL) dựa vào page cache của OS; MySQL InnoDB có buffer pool riêng và
    thường dùng `O_DIRECT`
- [ ] Swap 🟡
  - Đẩy page ít dùng ra disk để giải phóng RAM. Cứu được một đợt thiếu RAM ngắn, nhưng
    swap nhiều làm latency tăng vọt (thrashing)
  - Nhiều hệ thống latency-sensitive tắt swap hoặc để `vm.swappiness` thấp. Kubernetes lâu nay
    yêu cầu tắt swap trên node (hỗ trợ swap đang dần được thêm, kiểm tra lại theo phiên bản)
  - ⚠️ JVM heap bị swap ra → GC phải chạm vào page trên disk → pause rất dài
- [ ] OOM killer 🟡
  - Khi hết RAM (và swap), kernel chọn process có `oom_score` cao nhất để kill (SIGKILL)
  - Dấu vết: `dmesg -T | grep -i -E 'killed process|out of memory'`, `journalctl -k`
  - `oom_score_adj` (-1000 tới 1000) để bảo vệ process quan trọng (sshd, database)
  - ⚠️ Process bị SIGKILL không log được gì. App "tự nhiên biến mất" → nghĩ tới OOM trước
- [ ] cgroup memory limit trong container 🔴
  - Container là process bình thường bị giới hạn bằng cgroup (tài nguyên) và namespace (tầm nhìn)
  - Vượt `memory.max` (cgroup v2) → OOM killer trong cgroup kill process; Kubernetes báo
    `OOMKilled`, exit code 137
  - ⚠️ Page cache cũng được tính vào memory của cgroup (kernel sẽ thu hồi page cache sạch trước
    khi OOM, nhưng dirty page và tmpfs thì không dễ thu hồi). File ghi vào `emptyDir` kiểu
    memory/tmpfs tính vào RAM
  - JVM: từ JDK 10 (và 8u191) nhận biết container; `-XX:MaxRAMPercentage` mặc định 25% RAM.
    ⚠️ Heap chỉ là một phần: metaspace, thread stack, direct buffer, code cache cũng tốn RAM →
    đặt heap bằng 100% limit là bị OOMKilled
  - Go: GC không biết limit; dùng `GOMEMLIMIT` (Go 1.19+) để GC chạy tích cực hơn gần ngưỡng.
    `GOMAXPROCS` mặc định theo cgroup CPU limit từ Go 1.25 (kiểm tra lại); bản cũ hơn thì
    dùng `automaxprocs`
  - PHP-FPM: tổng RAM = số worker × RSS mỗi worker; `memory_limit` của PHP là theo request
  - Node: `--max-old-space-size` cho V8 heap
- [ ] Memory leak khi có GC 🟢
  - GC chỉ thu object không còn ai tham chiếu. Leak = vẫn còn tham chiếu nhưng không dùng nữa
  - Ví dụ: cache/map không giới hạn, listener không gỡ, `ThreadLocal` không `remove()` trong
    thread pool, goroutine treo giữ biến, closure giữ object lớn, static collection
  - PHP-FPM ít bị vì process reset sau mỗi request; long-running PHP (queue worker, Octane)
    thì bị như mọi ngôn ngữ khác
  - Điều tra: đồ thị RSS/heap theo thời gian (tăng bậc thang, không về lại sau GC), heap dump
    (`jmap`, `jcmd GC.heap_dump`), `pprof` heap (Go), heap snapshot (Node)
- [ ] Copy-on-write khi fork 🔴
  - `fork()` không copy RAM ngay; cha và con chia sẻ page, chỉ copy page nào bị ghi
  - Redis BGSAVE fork để snapshot: nếu ghi nhiều trong lúc snapshot, RAM có thể gần gấp đôi
  - Transparent Huge Pages làm COW tốn hơn; Redis, MongoDB khuyên tắt THP (kiểm tra lại
    khuyến nghị theo phiên bản)

### I/O

- [ ] File descriptor 🟢
  - Số nguyên đại diện cho file, socket, pipe, epoll instance... trong bảng của process
  - `too many open files` (EMFILE): chạm `ulimit -n` của process. Mặc định soft limit thường
    1024 trên nhiều distro (kiểm tra lại)
  - Điều tra: `ls /proc/<pid>/fd | wc -l`, `lsof -p <pid>`, `cat /proc/<pid>/limits`
  - ⚠️ Nguyên nhân gốc thường là leak: không đóng response body (Go `resp.Body.Close()`),
    không đóng connection, tạo HTTP client mới mỗi request. Tăng ulimit chỉ trì hoãn
  - Giới hạn cho service systemd đặt bằng `LimitNOFILE=`, không phải `/etc/security/limits.conf`
    (file đó áp cho login session qua PAM)
- [ ] Blocking, non-blocking, multiplexing 🟡
  - Blocking: `read()` chờ tới khi có dữ liệu, thread đứng yên
  - Non-blocking: `read()` trả ngay `EAGAIN` nếu chưa có dữ liệu
  - Multiplexing: một thread hỏi kernel "trong N fd này, fd nào sẵn sàng?" rồi chỉ xử lý fd đó.
    Đây là nền của Nginx, Node, Redis, Go netpoller, Netty
  - Vì sao event loop phục vụ được hàng nghìn kết nối: không thread nào ngồi chờ I/O; chi phí
    mỗi kết nối rảnh chỉ là vài KB bộ nhớ
- [ ] `select` / `poll` / `epoll` 🟡

| | `select` | `poll` | `epoll` |
|---|---|---|---|
| Giới hạn số fd | `FD_SETSIZE` (thường 1024) | không cố định | không cố định |
| Mỗi lần gọi | truyền lại cả tập fd, kernel quét O(n) | như select | đăng ký một lần, trả về fd sẵn sàng |
| Phù hợp | ít kết nối | ít kết nối | hàng chục nghìn kết nối |

  - Level-triggered (mặc định): còn dữ liệu là còn báo. Edge-triggered (`EPOLLET`): chỉ báo khi
    trạng thái đổi → phải đọc tới `EAGAIN`, không thì treo
  - Tương đương: `kqueue` (BSD/macOS), IOCP (Windows)
  - ⚠️ epoll không áp dụng cho file thường: file luôn "sẵn sàng", đọc disk vẫn block → đó là
    lý do Node đẩy file I/O sang threadpool
- [ ] io_uring 🔴
  - Interface async của Linux (kernel 5.1+): hai ring buffer chia sẻ giữa user và kernel
    (submission queue, completion queue); nộp nhiều thao tác mà không cần syscall mỗi thao tác
  - Khác epoll: epoll báo "sẵn sàng để đọc", io_uring báo "đã đọc xong" (completion-based),
    và hỗ trợ cả file I/O thật sự async
  - ⚠️ Lịch sử có nhiều lỗ hổng bảo mật; một số môi trường (seccomp mặc định của container
    runtime, một số nhà cung cấp) chặn io_uring (kiểm tra lại môi trường bạn dùng)
  - Backend engineer thường không gọi trực tiếp; biết để hiểu các runtime/DB mới đang dùng gì
- [ ] Zero-copy, `sendfile` 🔴
  - Gửi file thường: disk → page cache → buffer user (`read`) → socket buffer (`write`) → NIC.
    Hai lần copy qua user space, hai lần chuyển context
  - `sendfile(out_fd, in_fd, ...)`: kernel chuyển thẳng từ page cache sang socket, không qua user
  - Dùng ở: Nginx `sendfile on`, Kafka gửi log segment cho consumer, Java `FileChannel.transferTo`
  - ⚠️ Nếu cần mã hoá TLS trong user space thì mất zero-copy (trừ khi dùng kTLS)
  - Ý tổng quát: dữ liệu càng ít đi qua user space, càng ít copy, càng nhanh

### Signal và vòng đời process

- [ ] Các signal hay gặp 🟢

| Signal | Số | Bắt được | Ý nghĩa thường dùng |
|---|---|---|---|
| `SIGTERM` | 15 | có | xin dừng lịch sự; mặc định của `kill`, `docker stop`, Kubernetes |
| `SIGKILL` | 9 | không | kernel giết ngay, không dọn dẹp được |
| `SIGINT` | 2 | có | Ctrl+C |
| `SIGHUP` | 1 | có | terminal đóng; daemon thường dùng để reload config (Nginx) |
| `SIGQUIT` | 3 | có | JVM in thread dump; Nginx/PHP-FPM graceful stop |
| `SIGUSR1/2` | | có | tuỳ app: reopen log, reload |
| `SIGSEGV` | 11 | | truy cập bộ nhớ sai |

  - Exit code 128 + n = chết vì signal n: `137` = SIGKILL (thường OOM hoặc hết grace period),
    `143` = SIGTERM, `139` = SIGSEGV
- [ ] Graceful shutdown 🟡
  - Nhận SIGTERM → ngừng nhận việc mới (đóng listener, báo readiness fail) → xử lý nốt request
    đang chạy, job đang làm → đóng connection DB, flush log/metric → exit 0
  - Phải xong trước deadline: `docker stop` mặc định chờ 10 giây, Kubernetes
    `terminationGracePeriodSeconds` mặc định 30 giây, sau đó SIGKILL
  - Queue worker: làm nốt message hiện tại rồi dừng, không ack message chưa làm xong
  - Go: `signal.NotifyContext` + `http.Server.Shutdown(ctx)`. Java Spring Boot:
    `server.shutdown=graceful`. Laravel queue worker: tự xử lý SIGTERM, dừng sau job hiện tại
  - Chi tiết trong bối cảnh deploy: [19-devops-cloud.md](19-devops-cloud.md)
- [ ] PID 1 trong container 🔴
  - Process chạy với PID 1 được kernel đối xử đặc biệt: signal không có handler thì bị bỏ qua
    (không áp dụng mặc định "SIGTERM = chết"). App không cài handler → `docker stop` chờ đủ 10
    giây rồi SIGKILL
  - PID 1 phải reap zombie (gọi `wait()` cho con mồ côi). App không làm việc này → zombie tích tụ
    nếu app spawn process con (chạy shell command, headless Chrome...)
  - ⚠️ `CMD npm start` hoặc shell form `CMD php artisan ...` → PID 1 là `sh`/`npm`, không
    chuyển SIGTERM cho app. Dùng exec form `CMD ["node", "server.js"]`, và `exec "$@"` ở
    cuối entrypoint script
  - Giải pháp: init nhỏ như `tini`, `dumb-init` (`docker run --init` dùng tini) làm PID 1,
    chuyển signal và reap zombie

```bash
#!/bin/sh
# entrypoint.sh: chuẩn bị xong thì exec để app thay thế shell, trở thành PID 1
set -eu
envsubst < /app/config.tpl > /app/config.yml
exec "$@"
```

### File system

- [ ] Inode 🟢
  - Inode lưu metadata (owner, permission, size, timestamp, vị trí block) nhưng không lưu tên.
    Tên file nằm trong directory entry trỏ tới inode
  - ⚠️ `No space left on device` nhưng `df -h` còn trống → xem `df -i`: hết inode do hàng triệu
    file nhỏ (session file, cache file)
- [ ] Hard link và soft link 🟢
  - Hard link: thêm một tên trỏ vào cùng inode; xoá tên gốc file vẫn còn; không vượt file system,
    không link thư mục
  - Soft (symbolic) link: file riêng chứa đường dẫn; trỏ được qua file system; gốc mất thì link
    gãy
  - Ứng dụng: deploy kiểu `current -> releases/2026...` rồi đổi symlink để chuyển phiên bản
    (Capistrano, Deployer). Đổi symlink atomic bằng `ln -sfn` tạm rồi `mv -T`
- [ ] Permission 🟢
  - `rwx` cho owner/group/other; số bát phân `755`, `644`, `600`
  - Với thư mục: `x` là được đi vào, `r` là được liệt kê
  - umask quyết định quyền mặc định khi tạo file
  - ⚠️ Lỗi kinh điển: `chmod -R 777 storage` cho "chạy được". Đúng ra: chown cho user chạy
    PHP-FPM/app, quyền tối thiểu. Private key SSH phải `600`
  - setuid, sticky bit (`/tmp`) ở mức biết tên
- [ ] Xoá file đang mở 🟡
  - `rm` chỉ xoá tên; inode còn khi còn process giữ fd → disk không giải phóng
  - Tìm: `lsof +L1` hoặc `lsof | grep deleted`. Xử lý: restart/reload process, hoặc truncate
    qua `/proc/<pid>/fd/<n>`
  - Liên quan: log rotate phải báo app mở lại file (`copytruncate` hoặc gửi signal)
- [ ] `fsync` và durability 🔴
  - `write()` trả về khi dữ liệu mới vào page cache. Mất điện lúc đó là mất
  - `fsync(fd)` ép xuống thiết bị. Database gọi fsync khi commit (WAL/redo log); đây là lý do
    commit có chi phí và là lý do có cấu hình như `innodb_flush_log_at_trx_commit`,
    `synchronous_commit`
  - Ghi file an toàn: ghi vào file tạm → `fsync` file tạm → `rename` đè file đích (rename
    atomic trong cùng file system) → `fsync` thư mục cha để tên mới bền vững
  - ⚠️ Disk/controller có write cache không có pin có thể nói dối về fsync; cloud disk có SLA riêng

### Linux thực hành để debug production

- [ ] Bộ lệnh theo câu hỏi 🟢

| Câu hỏi | Lệnh |
|---|---|
| Process nào ăn CPU/RAM? | `top`/`htop` (bấm `P`, `M`), `ps aux --sort=-%mem \| head` |
| RAM còn bao nhiêu? | `free -h` (xem `available`) |
| Hệ thống đang nghẽn ở đâu? | `vmstat 1` (cột `r`, `b`, `si/so`, `wa`, `st`) |
| Disk có đang quá tải? | `iostat -xz 1` (`%util`, `await`) |
| Disk đầy ở đâu? | `df -h`, `df -i`, `du -sh /var/* \| sort -h` |
| Process mở file/socket nào? | `lsof -p <pid>`, `lsof -i :8080` |
| Port nào đang listen, bao nhiêu kết nối? | `ss -ltnp`, `ss -s`, `ss -tan state time-wait \| wc -l` |
| Process đang kẹt ở syscall gì? | `strace -p <pid> -f -tt -e trace=network` |
| Kernel có báo gì không? (OOM, disk lỗi) | `dmesg -T`, `journalctl -k` |
| Log của service | `journalctl -u nginx --since "10 min ago" -f` |
| DNS có phân giải đúng không? | `dig +short api.example.com`, `dig @8.8.8.8 ...` |
| Endpoint trả gì, chậm ở bước nào? | `curl -v`, `curl -w` với các biến thời gian |

  - ⚠️ `strace` làm process chậm đi nhiều; cẩn thận trên production. `perf`, eBPF (`bpftrace`,
    BCC tools) nhẹ hơn cho profiling 🔴

```bash
# Top 10 IP gọi nhiều nhất trong access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head
# Đếm status code 5xx theo phút (log format mặc định của Nginx)
awk '$9 ~ /^5/ {print substr($4, 2, 17)}' access.log | uniq -c
# Đo từng giai đoạn của một request
curl -o /dev/null -s -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://api.example.com/health
```

- [ ] Load average 🟡
  - Ba số: trung bình trượt (hàm mũ) trong 1, 5, 15 phút của số task đang chạy hoặc chờ chạy
  - Trên Linux còn tính cả task ở trạng thái `D` (chờ disk) → load cao chưa chắc là CPU; phải
    xem `vmstat` (`wa`) và `iostat`
  - So với số core: load 8 trên máy 8 core là vừa đủ; trên máy 2 core là đang xếp hàng
  - Xu hướng: 1 phút > 15 phút là đang tăng
- [ ] CPU steal và throttling 🔴
  - `st` trong `top`/`vmstat`: thời gian vCPU muốn chạy nhưng hypervisor đưa CPU vật lý cho
    máy khác. Cao → hàng xóm ồn, hoặc instance loại burstable hết CPU credit
  - Container có CPU limit: cgroup dùng CFS quota; hết quota trong một chu kỳ thì bị throttle
    dù node còn rảnh → latency p99 tăng. Xem `nr_throttled` trong `cpu.stat` của cgroup
  - ⚠️ Runtime nhìn thấy số core của node chứ không phải limit (JVM cũ, Go trước khi container-
    aware) → tạo quá nhiều thread GC/worker → throttle nặng hơn
- [ ] systemd 🟡
  - Unit file khai báo cách chạy service; `systemctl start|stop|restart|reload|status`,
    `systemctl enable` để chạy khi boot
  - `Restart=on-failure`, `RestartSec=`, `User=`, `LimitNOFILE=`, `Environment=`/`EnvironmentFile=`
  - Log gom về journald: `journalctl -u app -f`
  - systemd timer là lựa chọn thay cron: có log, có `Persistent=true` chạy bù khi máy tắt

```ini
[Service]
User=app
ExecStart=/opt/app/bin/server
Restart=on-failure
LimitNOFILE=65535
EnvironmentFile=/etc/app/env
TimeoutStopSec=30
```

- [ ] cron và cạm bẫy 🟡
  - Cú pháp 5 trường: phút, giờ, ngày, tháng, thứ
  - ⚠️ **Timezone**: cron chạy theo timezone của máy/container (thường UTC). "Chạy lúc 0h" là
    0h UTC = 7h sáng giờ Việt Nam. Ngày đổi giờ mùa hè (nơi có DST) job có thể chạy hai lần
    hoặc không chạy
  - ⚠️ **Môi trường**: cron chạy với `PATH` tối thiểu, không đọc `.bashrc`, không có biến môi
    trường của app → dùng đường dẫn tuyệt đối, nạp env rõ ràng
  - ⚠️ `%` trong crontab là ký tự đặc biệt (xuống dòng), phải escape `\%` (hay gặp với `date +%F`)
  - ⚠️ **Chạy trùng**: job lần trước chưa xong, lần sau đã bắt đầu → dùng `flock -n`, hoặc
    lock phân tán (Laravel `withoutOverlapping()` dùng cache lock)
  - ⚠️ **Nhiều server**: mỗi máy chạy cron một lần → job chạy N lần. Chỉ định một máy, hoặc
    `onOneServer()`, hoặc Kubernetes CronJob với `concurrencyPolicy: Forbid`
  - Output không redirect sẽ bị gửi mail/mất; luôn log ra file hoặc stdout có thu thập
  - Job phải idempotent vì có thể chạy lại. Chi tiết về batch job: [12-messaging.md](12-messaging.md)

```bash
# Chạy mỗi 5 phút, không chạy trùng, log đầy đủ
*/5 * * * * flock -n /tmp/report.lock /opt/app/bin/report >> /var/log/report.log 2>&1
```

- [ ] ssh 🟢
  - Đăng nhập bằng key, tắt password login; `ssh-agent`; `~/.ssh/config` đặt alias, user, key
  - Bastion/jump host: `ssh -J bastion app-server`
  - Port forwarding: `ssh -L 5433:db.internal:5432 bastion` để truy cập DB private từ máy mình
  - 🟡 Trên cloud hiện đại có thể thay ssh bằng SSM Session Manager (AWS) hoặc tương đương,
    không cần mở port 22
- [ ] Shell scripting cơ bản 🟡
  - `set -e`: lệnh lỗi là dừng. `set -u`: dùng biến chưa định nghĩa là lỗi. `set -o pipefail`:
    pipeline lỗi nếu bất kỳ lệnh nào lỗi (mặc định chỉ lấy exit code lệnh cuối)
  - Luôn quote biến: `"$file"`. Không quote thì tên có dấu cách bị tách thành nhiều đối số
  - `trap cleanup EXIT` để dọn file tạm dù script lỗi
  - ⚠️ `set -e` có ngoại lệ: không dừng khi lệnh lỗi nằm trong `if`, `&&`, `||`
  - ⚠️ `rm -rf "$DIR/"` với `DIR` rỗng thành `rm -rf /` → `set -u` và `${DIR:?}` bảo vệ

```bash
#!/usr/bin/env bash
set -euo pipefail
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
backup_dir="${1:?cần truyền thư mục backup}"
pg_dump "$DATABASE_URL" | gzip > "$tmp/db.sql.gz"
mv "$tmp/db.sql.gz" "$backup_dir/db-$(date +%F).sql.gz"
```

## Senior trả lời khác gì

**"Process và thread khác nhau thế nào?"**
- Mid: process có bộ nhớ riêng, thread dùng chung bộ nhớ, thread nhẹ hơn.
- Senior: thêm hệ quả vận hành. PHP-FPM chọn process để cô lập và không lo thread-safety, trả
  giá bằng RAM mỗi worker nên sizing theo RAM. Java/Go chọn thread/goroutine để chia sẻ pool
  connection và cache trong process, trả giá bằng race condition và leak sống lâu. Nói được
  khi nào đổi: việc CPU nặng trong Node thì tách sang worker process.

**"Container bị kill liên tục, exit code 137."**
- Mid: tăng memory limit.
- Senior: 137 là SIGKILL, có thể do OOM hoặc hết grace period; phân biệt bằng `OOMKilled` trong
  pod status và `dmesg`. Nếu OOM: xem đồ thị bộ nhớ tăng dần (leak) hay đột biến (request lớn);
  kiểm tra runtime có biết limit không (JVM heap %, `GOMEMLIMIT`), phần ngoài heap. Tăng limit
  chỉ sau khi hiểu nguyên nhân.

**"Server load average 20, xử lý thế nào?"**
- Mid: CPU cao, scale thêm máy.
- Senior: load trên Linux gồm cả task chờ disk. Xem `vmstat 1`: `r` cao là thiếu CPU, `b` và
  `wa` cao là I/O, `st` cao là hypervisor. Mỗi hướng có cách xử lý khác nhau; scale ngang không
  giúp gì nếu cả cụm cùng chờ một database.

**"Too many open files."**
- Mid: tăng `ulimit`.
- Senior: đếm fd theo thời gian để biết leak hay tải thật; `lsof` xem loại fd (socket tới đâu,
  trạng thái `CLOSE_WAIT` nhiều là app không đóng connection). Sửa leak, rồi mới đặt limit hợp
  lý qua `LimitNOFILE` hoặc cấu hình container, và thêm metric/alert số fd.

**"Làm sao dừng service an toàn khi deploy?"**
- Mid: gửi SIGTERM rồi chờ.
- Senior: nói cả chuỗi: app có handler SIGTERM không, có phải PID 1 không (exec form, tini),
  thứ tự tắt (readiness fail trước, chờ LB ngừng gửi, rồi drain), deadline so với grace period,
  job dài thì làm sao (checkpoint, trả message về queue).

## Tình huống

1. **API chậm dần sau vài ngày chạy, restart là hết.**
   - Gợi ý:
     - Nghi leak: bộ nhớ (GC chạy liên tục), fd, goroutine/thread, connection
     - Đồ thị RSS, số fd, số goroutine/thread theo thời gian
     - Heap dump / `pprof` so sánh hai thời điểm
     - Tạm thời: recycle định kỳ (`pm.max_requests`, restart theo lịch) trong lúc tìm gốc

2. **Disk báo đầy 100%, `du` cộng lại chỉ ra 40%.**
   - Gợi ý:
     - File đã xoá nhưng process còn giữ fd: `lsof +L1`
     - Thường là log bị `rm` thay vì rotate đúng cách
     - Kiểm tra thêm mount khác che thư mục, và `df -i` cho inode

3. **Sau khi deploy trên Kubernetes, mỗi lần rollout có vài request 502, và pod mất đúng 30 giây
   mới tắt.**
   - Gợi ý:
     - 30 giây = hết grace period → app không nhận/không xử lý SIGTERM (PID 1 là shell?)
     - 502 lúc tắt: endpoint chưa bị gỡ khỏi LB mà app đã đóng listener → `preStop` sleep ngắn
     - Kiểm tra exec form, entrypoint có `exec`, app có graceful shutdown

4. **Cron báo cáo doanh thu hằng ngày ra số sai vào đầu tháng, và thỉnh thoảng gửi mail hai lần.**
   - Gợi ý:
     - Timezone: job chạy theo UTC, "hôm qua" bị lệch ngày so với giờ Việt Nam
     - Chạy hai lần: có hai server cùng chạy cron, hoặc lần trước chưa xong
     - Khoá chạy trùng, chỉ định một nơi chạy, job idempotent (đánh dấu đã gửi)

5. **Service Go trong container có CPU limit 1 core, node 32 core; p99 latency cao bất thường dù
   CPU usage trung bình chỉ 50%.**
   - Gợi ý:
     - CPU throttling: xem `nr_throttled` trong `cpu.stat`
     - `GOMAXPROCS` có đang bằng 32 không (phiên bản Go, `automaxprocs`)
     - Cân nhắc bỏ CPU limit, chỉ giữ request (có tranh luận, nói được trade-off)

6. **PHP-FPM log `server reached pm.max_children`, Nginx trả 504.**
   - Gợi ý:
     - Worker bị chiếm vì request chậm (API ngoài, query chậm), không phải vì thiếu worker
     - Slow log của FPM (`request_slowlog_timeout`) để biết kẹt ở đâu
     - Đặt timeout cho HTTP client, tách việc chậm sang queue; tăng `max_children` chỉ khi RAM đủ

## ❓ Câu hỏi hay gặp

🟢
- Process và thread khác nhau thế nào? Khi nào dùng multi-process thay vì multi-thread?
- Stack và heap khác nhau thế nào? Biến cục bộ nằm ở đâu?
- SIGTERM và SIGKILL khác nhau thế nào? Vì sao nên xử lý SIGTERM?
- Hard link và soft link khác nhau thế nào?
- Làm sao tìm process đang chiếm port 8080?

🟡
- Vì sao Go chạy được hàng trăm nghìn goroutine còn Java truyền thống thì không chạy được hàng
  trăm nghìn thread?
- Server báo "too many open files", bạn điều tra thế nào?
- Vì sao một event loop phục vụ được hàng nghìn kết nối? Điểm yếu của nó là gì?
- Ngôn ngữ có GC vẫn bị memory leak được không? Cho ví dụ.
- `free` báo còn rất ít RAM trống, có đáng lo không?
- Load average là gì? Load 4 trên máy 4 core và trên máy 1 core khác nhau thế nào?
- Viết cron cần lưu ý những gì?

🔴
- Container bị OOMKilled dù heap JVM chỉ đặt 70% limit. Vì sao?
- Vì sao app trong container không tắt khi `docker stop`, phải chờ 10 giây?
- `epoll` khác `select` thế nào? Level-triggered và edge-triggered?
- `sendfile` giúp gì? Khi nào không dùng được?
- Database đảm bảo dữ liệu đã commit không mất khi mất điện bằng cách nào?
- Virtual thread có làm hệ thống nhanh hơn không? Giới hạn của nó là gì?
- CPU steal và CPU throttling là gì, ảnh hưởng tới latency thế nào?

## Bài tập tự làm

1. Viết một chương trình nhỏ (Go hoặc ngôn ngữ bạn dùng) mở file liên tục mà không đóng. Dùng
   `ulimit -n` đặt thấp, quan sát lỗi, rồi dùng `lsof` và `/proc/<pid>/fd` để xác nhận.
2. Viết Dockerfile chạy một app có xử lý SIGTERM. Thử cả shell form và exec form của `CMD`, đo
   thời gian `docker stop` trong từng trường hợp và giải thích khác biệt.
3. Viết script backup database có `set -euo pipefail`, `trap` dọn file tạm, khoá chạy trùng bằng
   `flock`, và cài vào cron chạy 2h sáng giờ Việt Nam trên một máy dùng UTC.
4. Trên một máy Linux, chạy một tác vụ đọc disk nặng và một tác vụ CPU nặng. Với mỗi tác vụ,
   ghi lại `uptime`, `vmstat 1`, `iostat -xz 1` và giải thích các cột thay đổi.
5. Lập bảng sizing PHP-FPM cho server 4 GB RAM với worker trung bình 60 MB, có tính phần RAM
   cho OS, Nginx và OPcache. Giải thích vì sao bạn chọn `pm = static` hoặc `dynamic`.

> Nộp bài vào đây để được review.
