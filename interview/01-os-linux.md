# 01. Hệ điều hành và Linux

> [← Mục lục](README.md) · Trọng tâm: **Linux trên production** (process, bộ nhớ, I/O, signal, file system, container) nhìn từ góc **PHP-FPM**, đối chiếu Java/Go/Node.
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

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [*Operating Systems: Three Easy Pieces*](https://pages.cs.wisc.edu/~remzi/OSTEP/) (Arpaci-Dusseau) | Sách online miễn phí | Nền lý thuyết: process, scheduling, virtual memory, concurrency, file system. Viết dễ đọc |
| [*Systems Performance*, 2nd ed.](https://www.brendangregg.com/systems-performance-2nd-edition-book.html) (Brendan Gregg, 2020) | Sách | Linux dưới góc vận hành: CPU, memory, disk, network, công cụ quan sát. Sách gối đầu của SRE |
| [Linux man-pages](https://man7.org/linux/man-pages/) và [*The Linux Programming Interface*](https://man7.org/tlpi/) (Kerrisk) | Official docs / Sách | Nguồn chuẩn cho syscall, signal, `/proc`. Khi blog và man page mâu thuẫn, tin man page |
| [Linux kernel docs: Admin Guide](https://docs.kernel.org/admin-guide/cgroup-v2.html) | Official docs | cgroup v2, memory, sysctl, scheduler |
| [Brendan Gregg's site](https://www.brendangregg.com/) | Blog | USE method, flame graph, perf, eBPF, load average |
| [PHP-FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) | Official docs | Process model của PHP-FPM, `pm.*`, timeout, slowlog |
| [BashPitfalls](https://mywiki.wooledge.org/BashPitfalls) | Wiki | Các lỗi shell script hay gặp, kèm cách sửa |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Hiểu process, bộ nhớ, file ở mức dùng được; tự xoay xở trên một máy Linux | 4–5 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.6 | Hiểu mô hình chạy của runtime, I/O, signal, bộ nhớ khi vận hành; sizing được PHP-FPM | 7–9 ngày |
| **3. Senior** 🔴 | 3.1–3.5 | Container, CPU throttling, durability, debug production có phương pháp | 7–9 ngày |

Học theo thứ tự: chặng 2 cần mô hình process và virtual memory của chặng 1, chặng 3 giải thích
vì sao container và production hành xử khác máy dev. Câu hỏi OS ở vòng phỏng vấn senior hiếm khi
là lý thuyết thuần; người phỏng vấn thường hỏi qua một sự cố ("pod bị kill 137", "disk đầy mà
`du` không thấy") rồi đào xuống cơ chế.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Process và thread

**Vì sao cần học:** PHP-FPM chạy mỗi request trong một process riêng, còn Java và Go chạy
nhiều request trong cùng một process. Khác biệt này quyết định cách bạn tính RAM cho server,
vì sao PHP ít gặp race condition trong code, và vì sao cache trong RAM của PHP khó dùng. Câu
"process khác thread thế nào" gần như luôn được hỏi, và thường bị hỏi tiếp "vậy PHP chọn cái
nào, vì sao".

**Học gì**

*Hai khái niệm*
- **Process** là một chương trình đang chạy. Mỗi process có:
  - Vùng nhớ riêng. Process khác không đọc hay ghi vào được. Hệ điều hành đảm bảo điều này bằng
    *virtual memory* (module 1.2).
  - Danh sách file và socket đang mở riêng. Mỗi thứ đang mở được đánh một số nguyên gọi là
    *file descriptor* (fd): 0 là stdin, 1 là stdout, 2 là stderr, các số sau là file hoặc kết
    nối mạng mà chương trình mở.
  - Một mã số gọi là PID.
  - Ví dụ: 50 worker PHP-FPM là 50 process. Biến `$x` ở worker này hoàn toàn không liên quan
    tới worker kia.
- **Thread** là một luồng chạy code bên trong một process. Một process có ít nhất một thread,
  và có thể có nhiều thread.
  - Các thread trong cùng process **dùng chung** vùng nhớ (biến global, object trên heap, code)
    và dùng chung các fd.
  - Mỗi thread chỉ **có riêng** hai thứ. Thứ nhất là *stack*, nơi chứa biến cục bộ của các hàm
    nó đang gọi. Thứ hai là trạng thái CPU (*register*), tức "đang chạy tới dòng lệnh nào".
  - Ví dụ: Tomcat chạy 200 thread trong một process Java. Một biến `static` được cả 200 thread
    nhìn thấy và cùng sửa được.

*So sánh (phần hay bị hỏi nhất)*

| | Process | Thread |
|---|---|---|
| Vùng nhớ | Riêng | Chung với các thread khác trong process |
| Chia sẻ dữ liệu | Khó: phải qua DB, Redis, file, socket, shared memory | Dễ: đọc chung một biến |
| Khi một cái bị crash | Chỉ nó chết, các process khác vẫn chạy | Thường kéo chết cả process, tức mọi thread khác |
| Chi phí tạo | Tốn hơn | Rẻ hơn |
| Rủi ro chính | Tốn RAM, vì mỗi process giữ một bản dữ liệu riêng | Race condition, vì hai thread cùng sửa một biến ([13-concurrency.md](13-concurrency.md)) |

*Khi nào chọn cái nào*
- **Nhiều process** hợp khi:
  - Cần cô lập lỗi: một request lỗi không làm chết request khác.
  - Muốn trả RAM dễ: process chết là toàn bộ RAM của nó được trả lại, nên leak không tích luỹ mãi.
  - Runtime không an toàn khi chạy nhiều thread. PHP là trường hợp này.
- **Nhiều thread** hợp khi:
  - Cần chia sẻ dữ liệu trong RAM, ví dụ connection pool hoặc cache trong process.
  - Cần nhiều luồng chạy song song với chi phí thấp.
- Áp vào PHP-FPM:
  - Mô hình *share-nothing*: mỗi request bắt đầu sạch, không lo race condition trên biến.
  - Cái giá thứ nhất: RAM nhân theo số worker.
  - Cái giá thứ hai: không có connection pool hay cache dùng chung trong RAM. Muốn chia sẻ thì
    phải dùng Redis, APCu hoặc DB.

*Vòng đời của process*
- **Tạo process** bằng hai lời gọi hệ thống (*syscall*):
  - `fork()` tạo một bản sao của process hiện tại.
  - `exec()` thay chương trình đang chạy bằng một chương trình khác.
  - Ví dụ: shell chạy lệnh `ls` bằng cách fork rồi exec `ls`. PHP-FPM master chỉ fork ra các
    worker, không exec.
- **Trạng thái** (cột `STAT` trong `ps aux`):
  - `R` đang chạy, hoặc đang chờ tới lượt dùng CPU.
  - `S` đang ngủ chờ một sự kiện, ví dụ chờ request hay chờ dữ liệu mạng. Đa số process ở
    trạng thái này, và đó là bình thường.
  - `D` đang ngủ và không ngắt được, thường là đang chờ disk hoặc ổ mạng (NFS).
    ⚠️ `kill -9` cũng phải đợi I/O xong mới có tác dụng. Nhiều process `D` là dấu hiệu disk
    đang có vấn đề.
  - `Z` zombie (xem ngay dưới).
  - `T` bị dừng, ví dụ khi bấm Ctrl+Z.
- **Zombie**:
  - Là process con đã chết, nhưng process cha chưa đọc kết quả của nó (bằng `wait()`), nên nó
    vẫn còn một dòng trong bảng process.
  - Zombie không tốn RAM, nhưng giữ một PID. Nhiều quá thì hết PID và không tạo được process mới.
  - ⚠️ `kill -9` một zombie không có tác dụng gì, vì nó đã chết rồi. Phải sửa process cha, hoặc
    kill cha.
- **Orphan** (mồ côi):
  - Là process mà cha chết trước. Nó được PID 1 nhận làm con, và PID 1 có trách nhiệm dọn nó khi
    nó chết.
  - ⚠️ Trong container, PID 1 thường chính là app của bạn. App không biết làm việc dọn dẹp này
    thì zombie tích tụ. Đó là lý do có `tini` và `docker run --init` (module 3.1).

*Đào sâu (🔴, học sau khi đã vững phần trên)*
- Linux thật ra không phân biệt process và thread. Cả hai đều là một *task*, được tạo bằng
  syscall `clone()`. Các cờ truyền vào `clone()` quyết định task mới dùng chung những gì với
  task tạo ra nó:
  - Dùng chung vùng nhớ, fd, ... thì gọi là thread.
  - Không dùng chung gì thì gọi là process.
- Goroutine của Go và virtual thread của Java không phải thread của OS. Runtime tự xếp hàng
  nghìn goroutine hay virtual thread lên một số ít thread OS (module 2.1).

**Đọc**
- OSTEP: chương *Processes*, *Process API*, *Concurrency and Threads*
- man: [clone(2)](https://man7.org/linux/man-pages/man2/clone.2.html) (bảng cờ `CLONE_*`), [fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html), [wait(2)](https://man7.org/linux/man-pages/man2/wait.2.html)
- man: [proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html), mục `/proc/pid/status` và `/proc/pid/stat` (ý nghĩa các ký tự trạng thái)

**Nắm chắc khi**
- [ ] Kể được 4 thứ thread dùng chung và 2 thứ riêng của mỗi thread
- [ ] Tạo được một zombie bằng code nhỏ, thấy nó trong `ps` và giải thích vì sao `kill -9` zombie không có tác dụng
- [ ] Giải thích được vì sao PHP chọn process còn Java/Go chọn thread/goroutine, và cái giá của mỗi bên

#### 1.2 Bộ nhớ cơ bản

**Vì sao cần học:** Mọi câu hỏi "server còn bao nhiêu RAM", "đặt `pm.max_children` bao nhiêu",
"vì sao process Java chiếm 10 GB" đều cần hiểu process dùng bộ nhớ thế nào. Người mới hay đọc sai
`free` và `top` rồi kết luận "hết RAM" khi máy vẫn ổn, hoặc cộng RSS của 50 worker PHP-FPM ra một
con số lớn hơn cả RAM máy. Phỏng vấn thường hỏi "VSZ và RSS khác gì", "stack và heap khác gì".

**Học gì**

*Stack và heap*
- **Stack** là vùng nhớ chứa *frame* của các hàm đang được gọi. Mỗi frame giữ biến cục bộ và
  tham số của một lần gọi hàm.
  - Hàm gọi thì frame được đẩy vào, hàm trả về thì frame bị bỏ đi. Không cần ai dọn.
  - Mỗi thread có một stack riêng (module 1.1), và stack thường nhỏ.
- **Heap** là vùng nhớ cho dữ liệu sống lâu hơn hàm tạo ra nó, ví dụ một object được trả về
  hoặc được lưu vào mảng.
  - Heap phải được giải phóng: hoặc do *garbage collector* (GC, bộ dọn rác tự động của runtime)
    như Java, Go, PHP, hoặc do lập trình viên tự gọi `free()` như C.
- **Tràn stack** xảy ra khi gọi hàm lồng quá sâu, thường là đệ quy không có điểm dừng:
  - Java báo `StackOverflowError`.
  - Go báo `goroutine stack exceeds ...`.
  - C thường chết với *segfault* (truy cập vùng nhớ không được phép).
- Go tự quyết định một biến nằm ở stack hay heap bằng *escape analysis*: nếu biến "thoát" ra
  ngoài hàm (ví dụ trả về con trỏ tới nó) thì phải đưa lên heap.
  - Xem quyết định của compiler bằng `go build -gcflags=-m`.

*Virtual memory: mỗi process tưởng mình có cả bộ nhớ*
- *Virtual memory* (bộ nhớ ảo): mỗi process thấy một dải địa chỉ riêng của nó, không phải địa chỉ
  RAM thật. Hai process cùng dùng địa chỉ `0x1000` nhưng trỏ tới hai chỗ RAM khác nhau.
- Việc dịch địa chỉ ảo sang địa chỉ RAM thật:
  1. Bộ nhớ được chia thành các khối cố định gọi là *page*, thường 4 KB.
  2. Mỗi process có một *page table*: bảng ghi page ảo nào ứng với page RAM thật nào.
  3. Phần cứng *MMU* (Memory Management Unit) trong CPU tra bảng này mỗi lần truy cập bộ nhớ.
- **Cấp phát lười**: khi chương trình xin bộ nhớ, kernel chỉ ghi nhận "đã hứa cho". RAM thật chỉ
  được cấp khi chương trình **chạm vào** (đọc hoặc ghi) page đó lần đầu.
- *Page fault* là lúc process chạm vào một page chưa được map vào RAM, kernel phải can thiệp:
  - *Minor* page fault: dữ liệu đã có trong RAM, chỉ chưa map cho process này. Rẻ.
  - *Major* page fault: phải đọc từ disk hoặc swap. Đắt, chậm hơn hàng nghìn lần.

*Đọc đúng các con số bộ nhớ*

| Chỉ số | Là gì | Có đáng lo khi lớn? |
|---|---|---|
| VSZ (virtual size) | Tổng dải địa chỉ ảo process đã reserve, kể cả phần chưa bao giờ chạm tới | ⚠️ Không. VSZ lớn là bình thường |
| RSS (resident set size) | Phần đang thật sự nằm trong RAM | Có, nhưng đếm cả phần dùng chung |
| PSS (proportional set size) | Như RSS, nhưng phần dùng chung được chia đều cho các process cùng dùng | Là con số đúng để sizing |

- Ví dụ: một process Java có VSZ 10 GB (đã reserve heap tối đa và nhiều vùng khác) nhưng RSS chỉ
  500 MB, vì nó mới chạm vào 500 MB.
- ⚠️ RSS đếm cả *shared memory* (bộ nhớ dùng chung) như OPcache và các thư viện `.so`.
  - Cộng RSS của 50 worker PHP-FPM là đếm trùng phần dùng chung 50 lần.
  - Khi sizing, dùng PSS: xem bằng `smem` hoặc `/proc/<pid>/smaps_rollup`.

*Page cache và lệnh `free`*
- *Page cache*: kernel dùng RAM đang rảnh để giữ nội dung file vừa đọc hoặc ghi, lần sau đọc lại
  khỏi phải chạm disk. Khi app cần RAM, kernel thu hồi phần cache này.
- ⚠️ Vì vậy cột `free` trong `free -h` thường rất nhỏ trên server chạy lâu, và đó là bình thường.
  Nhìn cột `available`: ước lượng RAM app còn dùng được, đã tính cả cache thu hồi được.

*Overcommit*
- *Overcommit*: Linux cho phép tổng bộ nhớ các process xin (`malloc`) vượt quá RAM thật, vì đa số
  chương trình xin nhiều hơn dùng.
- ⚠️ Nếu sau đó các process thật sự chạm vào hết và RAM không đủ, kernel phải giết bớt process.
  Đó là OOM (out of memory, module 2.4).

**Đọc**
- OSTEP: các chương *Address Spaces*, *Paging: Introduction*, *Paging: Faster Translations (TLBs)*, *Swapping: Mechanisms*
- Kernel docs: [Memory Management Concepts](https://docs.kernel.org/admin-guide/mm/concepts.html)
- man: [proc(5)](https://man7.org/linux/man-pages/man5/proc.5.html), mục `/proc/pid/smaps` (RSS, PSS, shared/private)

**Nắm chắc khi**
- [ ] Giải thích được vì sao một process Java có VSZ 10 GB mà RSS chỉ 500 MB
- [ ] Nhìn `free -h` của một server thật và nói được còn bao nhiêu RAM dùng được
- [ ] Đo được PSS và RSS của một worker PHP-FPM, giải thích vì sao hai số khác nhau

#### 1.3 File system và permission

**Vì sao cần học:** Deploy Laravel bằng symlink, lỗi "permission denied" trên `storage/`, disk báo
đầy mà `df` vẫn còn chỗ, xoá log mà disk không giảm: đều là kiến thức file system. Phỏng vấn hay
hỏi qua sự cố ("disk đầy mà `du` không thấy") hoặc hỏi "`chmod 777` sai ở đâu".

**Học gì**

*Inode và tên file*
- *Inode* là bản ghi metadata của một file: owner, quyền, kích thước, các mốc thời gian, và vị trí
  các block dữ liệu trên disk.
- ⚠️ Inode **không** chứa tên file. Tên nằm trong *directory entry*: thư mục thật ra là một danh
  sách các cặp (tên, số inode).
- Mỗi file system có số inode cố định khi tạo. Hệ quả:
  - ⚠️ Lỗi `No space left on device` mà `df -h` vẫn còn trống thì chạy `df -i`. Thường là hết inode
    do hàng triệu file nhỏ, ví dụ session file hoặc cache file của PHP.

*Hard link và symlink*

| | Hard link | Symlink (symbolic link) |
|---|---|---|
| Bản chất | Thêm một tên nữa trỏ tới **cùng inode** | Một file nhỏ chứa **đường dẫn** tới file khác |
| Xoá file gốc | File vẫn còn, vì vẫn còn tên khác trỏ tới inode | Link bị gãy, trỏ vào chỗ không còn gì |
| Vượt sang file system khác | Không | Được |
| Link tới thư mục | Không | Được |

- Deploy kiểu `current -> releases/<timestamp>`: thư mục `current` là symlink trỏ tới bản release
  đang chạy. Đổi bản chạy là đổi symlink.
- Đổi symlink phải *atomic* (hoặc xong hẳn, hoặc chưa bắt đầu, không có lúc nửa vời):
  1. Tạo symlink mới dưới tên tạm: `ln -sfn releases/20260101 current_tmp`.
  2. Đổi tên đè lên `current`: `mv -T current_tmp current`. Lệnh `rename` là atomic.
  - `ln -sfn` trực tiếp lên `current` thì không atomic: nó xoá link cũ rồi tạo link mới, giữa hai
    bước có một khoảnh khắc `current` không tồn tại.
- ⚠️ Đổi symlink xong mà PHP-FPM vẫn chạy code cũ: OPcache và *realpath cache* (cache đường dẫn
  thật sau khi resolve symlink) vẫn giữ đường dẫn tới release cũ.
  - Sửa: dùng `$realpath_root` trong Nginx, và reload FPM sau khi đổi (xem 2.6).

*Permission*
- Mỗi file có 3 nhóm quyền: owner (chủ), group (nhóm), other (mọi người khác). Mỗi nhóm có 3 bit
  `r` (đọc), `w` (ghi), `x` (chạy).
- Viết dạng số: `r=4`, `w=2`, `x=1`, cộng lại cho từng nhóm.
  - `755`: owner được tất cả, người khác được đọc và chạy. Hay dùng cho thư mục và script.
  - `644`: owner đọc ghi, người khác chỉ đọc. Hay dùng cho file thường.
  - `600`: chỉ owner đọc ghi.
- Với thư mục, nghĩa của bit khác đi:
  - `x` là được **đi vào** thư mục (truy cập file bên trong nếu biết tên).
  - `r` là được **liệt kê** tên file bên trong.
- *umask* là mặt nạ quyết định quyền mặc định của file mới tạo, ví dụ umask `022` cho file mới
  quyền `644`.
- ⚠️ `chmod -R 777 storage` để "cho chạy được" là sai: ai trên máy cũng ghi được, kể cả code bị
  chiếm quyền. Cách đúng: `chown` cho user đang chạy PHP-FPM, và cấp quyền tối thiểu.
- Private key SSH phải là `600`, nếu không `ssh` từ chối dùng.
- Ở mức biết tên:
  - *setuid*: file chạy với quyền của owner file thay vì của người gọi (ví dụ `passwd`).
  - *sticky bit*: trên thư mục như `/tmp`, ai cũng tạo được file nhưng chỉ xoá được file của mình.

*Xoá file chỉ là xoá tên*
- `rm` chỉ xoá directory entry. Inode và dữ liệu chỉ bị giải phóng khi không còn tên nào **và**
  không còn process nào đang mở file.
- ⚠️ Xoá một file log lớn mà Nginx hay PHP-FPM vẫn đang mở (vẫn giữ fd) thì `df` không giảm. Tìm
  bằng `lsof +L1` (xem câu 6 ở Phần 2).

**Đọc**
- OSTEP: chương *Files and Directories*
- man: [inode(7)](https://man7.org/linux/man-pages/man7/inode.7.html), [symlink(7)](https://man7.org/linux/man-pages/man7/symlink.7.html), [path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html) (quyền `x` trên thư mục)

**Nắm chắc khi**
- [ ] Tái hiện được: xoá một file đang bị process mở, thấy `df` không giảm, tìm ra bằng `lsof +L1`
- [ ] Viết được lệnh đổi symlink `current` atomic và giải thích vì sao `ln -sfn` trực tiếp không atomic
- [ ] Đặt được quyền đúng cho thư mục `storage/` và `bootstrap/cache/` của Laravel mà không dùng `777`

#### 1.4 Linux thực hành

**Vì sao cần học:** Khi production có sự cố, bạn thường chỉ có một cửa sổ SSH và vài phút. Biết
lệnh nào trả lời câu hỏi nào (ai ăn CPU, RAM còn không, disk đầy ở đâu, port nào đang mở) là kỹ
năng cơ bản. Phỏng vấn hay cho một tình huống rồi hỏi "bạn gõ lệnh gì đầu tiên".

**Học gì**

*Bộ lệnh theo câu hỏi*
- Học lệnh theo câu hỏi mình cần trả lời, không học theo tên lệnh.

| Câu hỏi | Lệnh |
|---|---|
| Process nào ăn CPU/RAM? | `top`/`htop` (bấm `P`, `M`), `ps aux --sort=-%mem \| head` |
| RAM còn bao nhiêu? | `free -h` (cột `available`) |
| Hệ thống nghẽn ở đâu? | `vmstat 1` (cột `r`, `b`, `si/so`, `wa`, `st`) |
| Disk có quá tải? | `iostat -xz 1` (`%util`, `await`) |
| Disk đầy ở đâu? | `df -h`, `df -i`, `du -sh /var/* \| sort -h` |
| Process mở file/socket nào? | `lsof -p <pid>`, `lsof -i :8080` |
| Port nào đang listen? | `ss -ltnp`, `ss -s` |
| Kernel có báo gì? (OOM, disk lỗi) | `dmesg -T`, `journalctl -k` |
| Log của service | `journalctl -u nginx --since "10 min ago" -f` |
| DNS, HTTP | `dig +short`, `curl -v`, `curl -w` với biến thời gian |

- Các cột của `vmstat` cần biết:
  - `r`: số task đang chạy hoặc chờ CPU. `b`: số task đang chờ I/O (trạng thái `D`).
  - `si/so`: swap in/out. Khác 0 liên tục là đang thiếu RAM.
  - `wa`: % thời gian CPU rảnh vì chờ I/O. `st`: *steal*, CPU bị hypervisor lấy cho máy khác
    (module 3.2).
- Cột của `iostat`: `%util` là % thời gian disk bận, `await` là thời gian trung bình một yêu cầu
  I/O phải chờ (ms).

*Xử lý log bằng shell*
- Bộ công cụ: `tail -f` (theo dõi file đang ghi), `grep` (lọc dòng), `awk` (tách cột), `sed` (sửa
  chuỗi), `less` (xem file lớn), và cặp `sort | uniq -c | sort -rn` để đếm và xếp hạng.
- Ví dụ trên access log Nginx:

```bash
# Top 10 IP gọi nhiều nhất trong access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head
# Đếm status 5xx theo phút (log format mặc định của Nginx)
awk '$9 ~ /^5/ {print substr($4, 2, 17)}' access.log | uniq -c
# Đo từng giai đoạn của một request
curl -o /dev/null -s -w 'dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' https://api.example.com/health
```

- Lệnh `curl -w` cuối cùng tách thời gian ra DNS, kết nối TCP, bắt tay TLS, *TTFB* (time to first
  byte, lúc nhận byte đầu tiên của response) và tổng. Nhờ vậy biết chậm ở mạng hay ở server.

*Mạng*
- `curl`, `dig`, `ping`, `traceroute`/`mtr`, `nc`. Chi tiết ở [02-networking.md](02-networking.md).

*SSH*
- Đăng nhập bằng key thay vì mật khẩu, và tắt password login trên server.
- `ssh-agent` giữ key đã mở khoá để không phải nhập passphrase mỗi lần. `~/.ssh/config` lưu sẵn
  host, user, key để gõ `ssh prod` thay vì cả dòng dài.
- *Bastion* (jump host): máy duy nhất mở SSH ra Internet, muốn vào máy nội bộ phải nhảy qua nó.
  - `ssh -J bastion app-server` nhảy qua bastion trong một lệnh.
- *Port forwarding*: mở một cổng trên máy mình, mọi kết nối vào cổng đó được chuyển qua SSH tới
  một máy trong mạng nội bộ.
  - Ví dụ: `ssh -L 3307:db.internal:3306 bastion`, sau đó kết nối MySQL client tới
    `127.0.0.1:3307` là vào được DB private.
- Trên cloud có thể thay bằng SSM Session Manager (AWS), không cần mở port 22.

**Đọc**
- [The Art of Command Line](https://github.com/jlevy/the-art-of-command-line): lướt một lượt, đánh dấu lệnh chưa biết
- man: [ss(8)](https://man7.org/linux/man-pages/man8/ss.8.html), [lsof(8)](https://man7.org/linux/man-pages/man8/lsof.8.html), [vmstat(8)](https://man7.org/linux/man-pages/man8/vmstat.8.html), [iostat(1)](https://man7.org/linux/man-pages/man1/iostat.1.html), [journalctl(1)](https://man7.org/linux/man-pages/man1/journalctl.1.html)
- OpenSSH: [ssh(1)](https://man.openbsd.org/ssh) (mục `-J`, `-L`), [ssh_config(5)](https://man.openbsd.org/ssh_config)

**Nắm chắc khi**
- [ ] Từ một access log Nginx thật, tìm được top IP, top endpoint chậm và số 5xx theo phút chỉ bằng shell
- [ ] Tìm được process đang giữ port 8080 bằng hai cách
- [ ] Mở được tunnel tới MySQL private qua bastion và kết nối bằng client trên máy mình

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Scheduling và mô hình chạy của runtime

**Vì sao cần học:** Module này giải thích vì sao PHP-FPM, Java, Go và Node xử lý đồng thời theo
những cách rất khác nhau, và mỗi cách "nghẽn" ở đâu. Đây là nền để sizing worker, hiểu Octane,
và trả lời câu hỏi kinh điển "Node một thread sao phục vụ được nghìn kết nối" hay "goroutine khác
thread thế nào".

**Học gì**

*Context switch*
- *Context switch*: CPU dừng chạy task này để chạy task khác. Kernel phải:
  1. Lưu register (trạng thái CPU) của task cũ.
  2. Nạp register và chuyển sang stack của task mới.
  3. Nếu task mới thuộc process khác: đổi sang page table của process đó, một phần *TLB* (bộ nhớ
     đệm trong CPU cho việc dịch địa chỉ) bị xoá.
- Chi phí gián tiếp thường lớn hơn chi phí trực tiếp: CPU cache đang chứa dữ liệu của task cũ,
  task mới phải chạy với cache "nguội".
- Hai loại:
  - *Voluntary* (tự nguyện): task tự nhường CPU vì phải chờ I/O hoặc chờ lock.
  - *Involuntary* (bị ép): task hết *time slice* (lượt dùng CPU) và bị scheduler lấy lại CPU.
- Xem bằng `pidstat -w`, hoặc dòng `voluntary_ctxt_switches` trong `/proc/<pid>/status`.

*Scheduler của Linux*
- *Scheduler* là phần kernel quyết định task nào được chạy trên CPU nào, bao lâu.
- Linux dùng scheduler *preemptive*: kernel có thể giật CPU khỏi một task bất cứ lúc nào, task
  không cần tự nhường.
- Thuật toán: CFS, từ kernel 6.6 thay bằng EEVDF. Cả hai chia CPU theo trọng số `nice` (nice cao
  là "nhường nhịn", được ít CPU hơn).
- Lệnh: `nice`/`renice` đổi độ ưu tiên, `taskset` ghim process vào một số core (*CPU affinity*).

*Mô hình thread của runtime*

| Mô hình | Nghĩa | Ví dụ | Điểm yếu |
|---|---|---|---|
| 1:1 | Mỗi thread của ngôn ngữ là một thread OS | Java platform thread | Thread OS tốn tài nguyên, không tạo được hàng trăm nghìn |
| N:1 | Nhiều *green thread* (thread do runtime tự quản) chạy trên một thread OS | Một số runtime cũ | Một green thread block syscall là cả nhóm đứng |
| M:N | M thread của runtime xếp lên N thread OS | Goroutine, Java virtual thread | Runtime phức tạp hơn |

- Kích thước stack:
  - Goroutine khởi đầu 2 KB và tự giãn khi cần.
  - Thread OS mặc định 8 MB (xem bằng `ulimit -s`). Java `-Xss` mặc định 1 MB trên Linux x64.
  - Các con số này là virtual reserve, RSS thực nhỏ hơn nhiều (module 1.2).

*Chọn số worker*
- *CPU-bound* (việc chủ yếu tính toán): số worker ≈ số core. Nhiều hơn chỉ thêm context switch.
- *I/O-bound* (việc chủ yếu chờ DB, mạng): cần nhiều worker hơn số core, vì phần lớn thời gian
  worker ngồi chờ. Hoặc dùng non-blocking I/O (module 2.2).
- Công thức điểm xuất phát: `threads ≈ cores × (1 + wait/compute)`.
  - Ví dụ: 4 core, request chờ 90 ms, tính 10 ms: `4 × (1 + 9) = 40`.
  - ⚠️ Chỉ là điểm xuất phát, sau đó phải đo.

*Bảng so sánh runtime (hay bị hỏi)*

| Runtime | Đơn vị xử lý request | Chặn I/O thì sao | Giới hạn thường gặp |
|---|---|---|---|
| PHP-FPM | 1 process / 1 request | process đứng chờ | `pm.max_children`, RAM mỗi worker |
| Java servlet (Tomcat) | 1 platform thread / request | thread đứng chờ | thread pool (Tomcat `maxThreads` mặc định 200) |
| Java virtual thread | 1 virtual thread / request | runtime unmount, carrier làm việc khác | pinning, pool DB |
| Go `net/http` | 1 goroutine / request | runtime park goroutine, netpoller (epoll) | pool, bộ nhớ |
| Node.js | callback trên 1 event loop | I/O không chặn; CPU nặng chặn tất cả | CPU-bound code, libuv threadpool |

- Giải thích các từ trong bảng:
  - *Carrier thread*: thread OS mà virtual thread đang chạy trên đó. *Unmount*: virtual thread
    đang chờ I/O được gỡ khỏi carrier, để carrier chạy virtual thread khác.
  - *Park*: Go tạm cất goroutine đang chờ sang một bên. *Netpoller* là phần runtime Go dùng
    epoll (module 2.2) để biết khi nào socket có dữ liệu thì đánh thức goroutine.

*Cạm bẫy theo từng runtime*
- Java virtual thread:
  - ⚠️ *Pinning*: virtual thread bị dính chặt vào carrier, không unmount được. Trước JDK 24, block
    bên trong `synchronized` gây pin (JEP 491 sửa ở JDK 24). Native call vẫn pin.
  - ⚠️ Virtual thread không làm DB nhanh hơn. 10.000 virtual thread vẫn tranh nhau 20 connection.
- Go, mô hình *G-M-P*: G là goroutine, M là thread OS, P là "giấy phép chạy code Go", số P bằng
  `GOMAXPROCS`.
  - Khi một M bị block trong syscall, M tách khỏi P để P đi chạy goroutine khác trên M khác.
  - ⚠️ *Goroutine leak*: goroutine chờ một channel mãi mà không ai gửi, không bao giờ kết thúc.
- Node.js:
  - ⚠️ Một vòng lặp CPU nặng, `JSON.parse` một payload lớn, hay một regex *backtracking* (thử lại
    theo cấp số nhân với input xấu) làm cả server đứng, vì chỉ có một event loop.
  - File I/O, DNS `getaddrinfo`, crypto chạy trên *libuv threadpool*, mặc định 4 thread.

*PHP chạy kiểu long-running*
- Octane, Swoole, RoadRunner, FrankenPHP: PHP giữ app trong bộ nhớ giữa các request, không khởi
  tạo lại từ đầu. Mô hình này gần với Java/Go hơn FPM.
- ⚠️ State rò giữa request qua singleton và biến static: request sau thấy dữ liệu của request
  trước, ví dụ user đăng nhập của người khác.

**Đọc**
- OSTEP: chương *Scheduling: Introduction*, *Multi-level Feedback*, *Proportional Share*
- man: [sched(7)](https://man7.org/linux/man-pages/man7/sched.7.html); kernel docs: [EEVDF Scheduler](https://docs.kernel.org/scheduler/sched-eevdf.html)
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444) (mục *Pinning*), [JEP 491](https://openjdk.org/jeps/491)
- Laravel: [Octane](https://laravel.com/docs/octane), mục [Dependency Injection and Octane](https://laravel.com/docs/octane#dependency-injection-and-octane) và [Managing Memory Leaks](https://laravel.com/docs/octane#managing-memory-leaks)
- Đối chiếu concurrency: [13-concurrency.md](13-concurrency.md)

**Nắm chắc khi**
- [ ] Giải thích được vì sao chạy được 100.000 goroutine mà 100.000 thread OS thì không, nêu ít nhất 3 giới hạn
- [ ] Điền được bảng runtime ở trên mà không nhìn, kể cả cột "chặn I/O thì sao"
- [ ] Chỉ ra được 2 đoạn code Laravel chạy đúng trên FPM nhưng rò state trên Octane

#### 2.2 File descriptor và I/O

**Vì sao cần học:** Lỗi `too many open files` là sự cố production rất phổ biến, và gốc thường là
leak chứ không phải thiếu limit. Phần epoll giải thích vì sao Nginx, Redis, Node phục vụ được
hàng chục nghìn kết nối với vài thread, câu hỏi hay gặp khi so sánh PHP-FPM với các runtime khác.

**Học gì**

*File descriptor và giới hạn*
- *File descriptor* (fd, module 1.1) đại diện cho mọi thứ đang mở: file, socket, pipe, cả một
  *epoll instance*.
- Lỗi `too many open files` (mã `EMFILE`): process đã chạm giới hạn số fd, xem bằng `ulimit -n`.
- Mỗi giới hạn có hai mức: *soft limit* (đang áp dụng) và *hard limit* (trần mà soft được phép
  nâng lên).
  - Soft limit mặc định thường là 1024. systemd đặt cho service soft 1024, hard 524288.
- Đặt cho service systemd bằng `LimitNOFILE=` trong unit file.
  - ⚠️ Không phải `/etc/security/limits.conf`. File đó chỉ áp cho phiên đăng nhập (qua PAM), không
    áp cho service do systemd chạy.

*Điều tra fd*
- Đếm fd đang mở: `ls /proc/<pid>/fd | wc -l`.
- Xem chi tiết: `lsof -p <pid>`. Xem limit thật của process: `cat /proc/<pid>/limits`.
- ⚠️ Gốc thường là leak, tăng ulimit chỉ trì hoãn. Các dạng leak hay gặp:
  - Không đóng response body (Go phải gọi `resp.Body.Close()`).
  - Tạo HTTP client mới mỗi request thay vì dùng lại.
  - Socket `CLOSE_WAIT` tích tụ: bên kia đã đóng kết nối nhưng app mình chưa gọi `close()`.

*Ba kiểu I/O*
1. *Blocking*: gọi `read()`, thread đứng chờ tới khi có dữ liệu.
2. *Non-blocking*: gọi `read()`, nếu chưa có dữ liệu thì trả về ngay lỗi `EAGAIN` ("thử lại sau").
3. *Multiplexing*: một thread hỏi kernel "trong đống fd này, cái nào đã sẵn sàng?", rồi chỉ xử lý
   những cái đó.
- Multiplexing là nền của Nginx, Node, Redis, Go netpoller, Netty.

*select, poll, epoll*

| | `select` | `poll` | `epoll` |
|---|---|---|---|
| Giới hạn số fd | `FD_SETSIZE` (thường 1024) | không cố định | không cố định |
| Mỗi lần gọi | truyền lại cả tập, kernel quét O(n) | như select | đăng ký một lần, trả về fd sẵn sàng |
| Phù hợp | ít kết nối | ít kết nối | hàng chục nghìn kết nối |

- Hai chế độ báo của epoll:
  - *Level-triggered* (mặc định): còn dữ liệu chưa đọc là còn báo.
  - *Edge-triggered* (`EPOLLET`): chỉ báo một lần khi trạng thái thay đổi, ví dụ lúc có dữ liệu mới
    tới. ⚠️ Phải đọc tới khi gặp `EAGAIN`. Nếu chỉ đọc một lần rồi quay lại chờ, phần dữ liệu còn
    lại không bao giờ được báo nữa, và kết nối treo.
- Tương đương ở hệ điều hành khác: `kqueue` (BSD, macOS), IOCP (Windows).
- ⚠️ epoll không áp dụng cho file thường: file luôn được coi là "sẵn sàng", nhưng đọc disk vẫn
  block. Đó là lý do Node đẩy file I/O sang threadpool.

*Vì sao event loop phục vụ được hàng nghìn kết nối*
- Không có thread nào ngồi chờ một kết nối cụ thể. Một thread lặp: hỏi epoll, xử lý các fd sẵn
  sàng, hỏi tiếp.
- Mỗi kết nối đang rảnh chỉ tốn vài KB bộ nhớ cho buffer và trạng thái, không tốn một thread hay
  một process.
- So với PHP-FPM: mỗi kết nối đang xử lý chiếm cả một process, kể cả khi process đó chỉ đang chờ.

**Đọc**
- man: [epoll(7)](https://man7.org/linux/man-pages/man7/epoll.7.html) (đọc kỹ mục edge-triggered và Q&A cuối trang), [select(2)](https://man7.org/linux/man-pages/man2/select.2.html)
- systemd: [systemd.exec(5)](https://man7.org/linux/man-pages/man5/systemd.exec.5.html), mục `LimitNOFILE=`
- *Systems Performance*: chương *Operating Systems* (phần I/O models)

**Nắm chắc khi**
- [ ] Viết chương trình mở file không đóng, đặt `ulimit -n` thấp, quan sát lỗi và xác nhận bằng `/proc/<pid>/fd` (bài tập 1)
- [ ] Giải thích được edge-triggered treo thế nào nếu chỉ đọc một lần
- [ ] Phân biệt được "tải thật cần nhiều fd" và "leak fd" chỉ bằng đồ thị số fd theo thời gian

#### 2.3 Signal và graceful shutdown

**Vì sao cần học:** Mỗi lần deploy, scale xuống hay restart pod, process của bạn nhận signal. Xử
lý sai là mất request đang chạy, job queue chạy dở, hoặc log bị mất. PHP-FPM còn hiểu signal khác
Nginx, bẫy rất hay gặp. Phỏng vấn hay hỏi "exit code 137 là gì" và "graceful shutdown làm thế nào".

**Học gì**

*Signal là gì*
- *Signal* là một thông báo nhỏ kernel gửi tới process, ví dụ "hãy dừng", "hãy reload". Process có
  thể cài *handler* (hàm xử lý) để bắt signal, hoặc để hành vi mặc định (thường là chết).
- Các signal cần biết:

| Signal | Số | Bắt được | Dùng thường gặp |
|---|---|---|---|
| `SIGTERM` | 15 | có | xin dừng lịch sự; mặc định của `kill`, `docker stop`, Kubernetes |
| `SIGKILL` | 9 | không | kernel giết ngay |
| `SIGINT` | 2 | có | Ctrl+C |
| `SIGHUP` | 1 | có | terminal đóng; daemon dùng để reload config (Nginx) |
| `SIGQUIT` | 3 | có | JVM in thread dump; Nginx và PHP-FPM graceful stop |
| `SIGUSR1/2` | | có | tuỳ app: reopen log, reload |
| `SIGSEGV` | 11 | | truy cập bộ nhớ sai |

- Process chết vì signal số n thì exit code là 128 + n:
  - `137` = SIGKILL (9). Thường do OOM, hoặc hết grace period mà chưa tự thoát.
  - `143` = SIGTERM (15). `139` = SIGSEGV (11).

*PHP-FPM hiểu signal khác Nginx*
- ⚠️ Với PHP-FPM:
  - `SIGTERM` và `SIGINT` là **dừng ngay**, request đang chạy bị cắt.
  - `SIGQUIT` là graceful stop: chờ request đang chạy xong rồi mới dừng.
  - `SIGUSR1` mở lại file log. `SIGUSR2` graceful reload worker và config.
- Image Docker `php:*-fpm` chính thức đặt `STOPSIGNAL SIGQUIT` vì lý do này.

*Graceful shutdown*
- *Graceful shutdown*: dừng mà không làm hỏng việc đang làm dở. Các bước:
  1. Nhận SIGTERM.
  2. Ngừng nhận việc mới: đóng listener, cho *readiness probe* (kiểm tra "sẵn sàng nhận traffic"
     của Kubernetes) trả về lỗi để load balancer ngừng gửi request.
  3. Làm nốt request hoặc job đang chạy.
  4. Đóng kết nối DB, flush log.
  5. Exit 0.
- Có hạn chót. Hết hạn mà chưa thoát thì bị SIGKILL:
  - `docker stop` chờ 10 giây.
  - Kubernetes chờ `terminationGracePeriodSeconds`, mặc định 30 giây.
- Queue worker: làm nốt job hiện tại, không *ack* (xác nhận đã xử lý xong) job chưa xong.
  - Laravel `queue:work` tự bắt SIGTERM (cần extension `pcntl`) và dừng sau job hiện tại.
  - ⚠️ Job dài hơn grace period vẫn bị kill giữa chừng, nên job phải *idempotent*: chạy lại lần
    nữa không gây hậu quả sai (không trừ tiền hai lần).
- Đối chiếu: Go dùng `signal.NotifyContext` + `http.Server.Shutdown(ctx)`. Spring Boot bật bằng
  `server.shutdown=graceful`.

*Log rotation và signal*
- *Log rotation*: định kỳ đổi tên file log cũ và bắt đầu file mới, để log không lớn mãi. Công cụ
  thường dùng là `logrotate`. Có hai kiểu:
- Kiểu `create` + `postrotate` gửi signal:
  1. logrotate đổi tên `app.log` thành `app.log.1`. App vẫn ghi vào file cũ qua fd đang giữ.
  2. Tạo file `app.log` mới, rỗng.
  3. Gửi signal để app mở lại file theo tên (Nginx `USR1`, PHP-FPM `USR1`).
  - Không mất dòng log nào.
- Kiểu `copytruncate`: dùng **thay cho** việc mở lại file, khi app không biết reopen.
  1. Copy nội dung `app.log` sang `app.log.1`.
  2. Cắt `app.log` về 0 byte. App vẫn ghi tiếp vào cùng file.
  - ⚠️ Dòng log ghi giữa lúc copy và lúc truncate bị mất.
  - ⚠️ App không mở file bằng `O_APPEND` thì ghi tiếp ở vị trí cũ, tạo ra *file sparse* (file có
    một khoảng "lỗ" toàn byte 0 ở đầu).

**Đọc**
- man: [signal(7)](https://man7.org/linux/man-pages/man7/signal.7.html) (bảng action mặc định), [logrotate(8)](https://man7.org/linux/man-pages/man8/logrotate.8.html) (mục `copytruncate`, `postrotate`)
- PHP-FPM: [man page php-fpm(8)](https://github.com/php/php-src/blob/master/sapi/fpm/php-fpm.8.in) (mục *SIGNALS*), [`process_control_timeout`](https://www.php.net/manual/en/install.fpm.configuration.php)
- Kubernetes: [Pod termination](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)
- Laravel: [Queue Workers and Deployment](https://laravel.com/docs/queues#queue-workers-and-deployment), [Job Expirations and Timeouts](https://laravel.com/docs/queues#job-expirations-and-timeouts)
- Chi tiết trong bối cảnh deploy: [19-devops-cloud.md](19-devops-cloud.md)

**Nắm chắc khi**
- [ ] Nói ngay được signal nào cần gửi để PHP-FPM dừng graceful, và điều gì xảy ra nếu gửi SIGTERM
- [ ] Viết được cấu hình logrotate cho log Laravel theo cả hai kiểu, và nói kiểu nào có thể mất log
- [ ] Vẽ được timeline từ lúc Kubernetes xoá pod tới lúc process chết, ghi rõ mốc SIGTERM, grace period, SIGKILL

#### 2.4 Bộ nhớ khi vận hành: swap, OOM, leak

**Vì sao cần học:** "Pod tự nhiên biến mất", "server chậm dần rồi đứng", "queue worker ăn RAM tăng
mãi": ba sự cố này đều là chuyện bộ nhớ khi vận hành. Người làm PHP còn cần biết `memory_limit`
thật ra giới hạn cái gì và tính tổng RAM của PHP-FPM ra sao.

**Học gì**

*Swap*
- *Swap* là vùng trên disk kernel dùng để chứa tạm page RAM ít dùng khi thiếu RAM.
- Swap cứu được một đợt thiếu RAM ngắn. Nhưng swap nhiều thì latency tăng vọt, vì truy cập disk
  chậm hơn RAM rất nhiều. Trạng thái liên tục đẩy page ra vào gọi là *thrashing*.
- Hệ nhạy latency thường tắt swap, hoặc đặt `vm.swappiness` thấp (kernel ít muốn swap hơn).
- ⚠️ Heap JVM bị swap ra disk thì GC phải chạm vào các page đó, gây pause rất dài.
- Kubernetes: swap trên node Linux là tính năng **GA từ v1.34**. Mặc định vẫn `NoSwap`. Bật
  `LimitedSwap` thì pod loại Burstable (pod có memory request thấp hơn limit) được dùng swap
  theo tỉ lệ memory request.

*OOM killer*
- Khi hết RAM (và hết swap), kernel chạy *OOM killer*: chọn process có `oom_score` cao nhất (thường
  là process to nhất) và gửi SIGKILL.
- `oom_score_adj` (từ -1000 tới 1000) chỉnh điểm này. Đặt thấp để bảo vệ sshd, database.
- Tìm dấu vết: `dmesg -T | grep -i -E 'killed process|out of memory'`, hoặc `journalctl -k`.
- ⚠️ Process bị SIGKILL không kịp ghi log gì. App "tự nhiên biến mất" không để lại lỗi thì nghĩ tới
  OOM trước.

*Memory leak khi có GC*
- Có GC vẫn leak được. *Memory leak* ở đây là: object vẫn còn bị tham chiếu nên GC không dọn,
  nhưng chương trình không còn dùng tới nó nữa. Các nguồn hay gặp:
  - Cache hoặc map không có giới hạn kích thước.
  - Listener đăng ký mà không gỡ.
  - Java `ThreadLocal` không gọi `remove()`.
  - Goroutine treo mãi (module 2.1).
  - Collection static cứ thêm vào mãi.
- PHP-FPM ít bị, vì state bị xoá sau mỗi request. Queue worker và Octane chạy lâu nên bị như mọi
  ngôn ngữ khác.
- Giảm thiệt hại bằng cách định kỳ khởi động lại worker:
  - PHP-FPM: `pm.max_requests`.
  - Laravel queue: `queue:work --max-jobs`, `--max-time`, `--memory`.

*RAM của PHP-FPM*
- ⚠️ `memory_limit` áp **cho từng request**, không phải cho cả pool. Đặt `memory_limit = 256M` với
  50 worker không có nghĩa pool dùng tối đa 256 MB.
- Tổng RAM FPM ≈ số worker × PSS mỗi worker + OPcache (tính một lần, vì dùng chung).

*Điều tra leak*
1. Vẽ đồ thị RSS hoặc heap theo thời gian. Leak có dạng bậc thang đi lên, không giảm lại sau GC.
   Cache bình thường tăng tới một ngưỡng rồi dừng.
2. Lấy ảnh chụp heap để xem ai đang giữ bộ nhớ:
   - Java: heap dump bằng `jcmd <pid> GC.heap_dump`.
   - Go: `pprof` heap.
   - Node: heap snapshot.

**Đọc**
- Kernel docs: [sysctl/vm](https://docs.kernel.org/admin-guide/sysctl/vm.html) (mục `swappiness`, `overcommit_memory`, `oom_kill_allocating_task`)
- Kubernetes: [Swap memory management](https://kubernetes.io/docs/concepts/cluster-administration/swap-memory-management/), blog [Tuning Linux Swap for Kubernetes](https://kubernetes.io/blog/2025/08/19/tuning-linux-swap-for-kubernetes-a-deep-dive/)
- PHP: [`memory_limit`](https://www.php.net/manual/en/ini.core.php#ini.memory-limit), [Garbage Collection](https://www.php.net/manual/en/features.gc.php) (refcount và cycle collector)

**Nắm chắc khi**
- [ ] Tìm được dấu vết OOM killer trong `dmesg` trên một máy thật (hoặc tự gây OOM trong container)
- [ ] Lập được bảng sizing PHP-FPM cho server 4 GB (bài tập 5) có tính OPcache, OS, Nginx
- [ ] Phân biệt được leak thật và cache tăng tới ngưỡng rồi dừng, chỉ bằng đồ thị

#### 2.5 systemd, cron, shell script

**Vì sao cần học:** Queue worker, scheduler của Laravel, script deploy và backup đều chạy qua
systemd, cron và shell. Đây là nơi các lỗi âm thầm nhất xảy ra: cron chạy sai giờ, job chạy hai
lần trên hai server, script xoá nhầm cả thư mục gốc. Phỏng vấn hay hỏi "cron của bạn chạy trên 3
server thì sao".

**Học gì**

*systemd*
- *systemd* là process quản lý service trên hầu hết Linux hiện đại: khởi động, restart khi chết,
  gom log.
- Mỗi service mô tả bằng một *unit file*. Điều khiển bằng `systemctl start|stop|reload|status|enable`
  (`enable` là tự chạy khi máy khởi động).
- Các tuỳ chọn hay dùng:
  - `Restart=on-failure`, `RestartSec=`: tự chạy lại khi chết, chờ bao lâu.
  - `User=`: chạy dưới user nào. `LimitNOFILE=`: giới hạn fd (module 2.2).
  - `EnvironmentFile=`: nạp biến môi trường từ file.
  - `TimeoutStopSec=`, `KillSignal=`: chờ dừng bao lâu, gửi signal gì khi dừng (module 2.3).
- Log của service đi về *journald*, xem bằng `journalctl -u <tên>`.
- *systemd timer* là cách hẹn giờ thay cho cron: có log trong journald, và `Persistent=true` chạy
  bù lần bị lỡ khi máy tắt.

*cron và các bẫy*
- Mỗi dòng crontab có 5 trường thời gian: phút, giờ, ngày trong tháng, tháng, thứ trong tuần.
  Sau đó là lệnh.

```bash
# Chạy mỗi 5 phút, không chạy trùng, log đầy đủ
*/5 * * * * flock -n /tmp/report.lock /opt/app/bin/report >> /var/log/report.log 2>&1
```

- ⚠️ Timezone: cron chạy theo timezone của máy hoặc container, thường là UTC.
  - "0h" trên máy UTC là 7h sáng giờ Việt Nam.
  - Ở nơi có *DST* (giờ mùa hè), ngày đổi giờ có job chạy hai lần hoặc không chạy.
- ⚠️ Môi trường: cron chạy với `PATH` tối thiểu, không đọc `.bashrc`, không có biến môi trường của
  app. Dùng đường dẫn tuyệt đối cho mọi lệnh.
- ⚠️ `%` là ký tự đặc biệt trong crontab, phải escape thành `\%`. Hay gặp với `date +%F`.
- ⚠️ Chạy trùng: lần chạy trước chưa xong thì lần sau đã bắt đầu.
  - Chặn bằng `flock -n` (như ví dụ trên), hoặc Laravel `withoutOverlapping()`.
- ⚠️ Nhiều server: mỗi máy chạy cron của nó, nên job chạy N lần.
  - Chỉ định một máy chạy cron, dùng Laravel `onOneServer()`, hoặc Kubernetes CronJob với
    `concurrencyPolicy: Forbid`.
- Output không redirect vào file thì bị mất, hoặc bị gửi mail cho root.
- Job phải idempotent ([12-messaging.md](12-messaging.md)).

*Shell script an toàn*
- Mở đầu script bằng `set -euo pipefail`:
  - `-e`: dừng khi có lệnh lỗi.
  - `-u`: dùng biến chưa khai báo là lỗi.
  - `pipefail`: một lệnh trong pipe lỗi thì cả pipe tính là lỗi.
- Luôn quote biến: `"$file"`. Không quote thì tên file có dấu cách bị tách thành nhiều từ.
- `trap cleanup EXIT`: luôn chạy hàm dọn dẹp khi script kết thúc, kể cả khi lỗi.
- ⚠️ `set -e` không dừng khi lệnh lỗi nằm trong `if`, `&&`, `||`, hay trong hàm được gọi từ các chỗ
  đó.
- ⚠️ `rm -rf "$DIR/"*` khi `DIR` rỗng thành `rm -rf /*`.
  - GNU `rm` mặc định có `--preserve-root` nên từ chối `rm -rf /`, nhưng **không** chặn `/*`.
  - Bảo vệ bằng `"${DIR:?}"` (báo lỗi nếu biến rỗng) và `set -u`.
- Chạy ShellCheck (công cụ phân tích tĩnh cho shell) trước khi commit.

**Đọc**
- man: [systemd.service(5)](https://man7.org/linux/man-pages/man5/systemd.service.5.html) (mục `Restart=`, `Type=`), [systemd.timer(5)](https://man7.org/linux/man-pages/man5/systemd.timer.5.html), [crontab(5)](https://man7.org/linux/man-pages/man5/crontab.5.html), [flock(1)](https://man7.org/linux/man-pages/man1/flock.1.html), [rm(1)](https://man7.org/linux/man-pages/man1/rm.1.html) (`--preserve-root`)
- [BashFAQ/105](https://mywiki.wooledge.org/BashFAQ/105): vì sao `set -e` không làm điều bạn nghĩ
- [ShellCheck](https://www.shellcheck.net/)
- Laravel: [Preventing Task Overlaps](https://laravel.com/docs/scheduling#preventing-task-overlaps), [Running Tasks on One Server](https://laravel.com/docs/scheduling#running-tasks-on-one-server)

**Nắm chắc khi**
- [ ] Viết được unit file cho `queue:work` có restart, giới hạn fd, dừng graceful trong 60 giây
- [ ] Cài được cron chạy 2h sáng giờ Việt Nam trên máy UTC, không chạy trùng (bài tập 3)
- [ ] Chỉ ra được 3 lỗi trong một shell script cho sẵn mà không cần chạy nó

#### 2.6 Tầng PHP: PHP-FPM nhìn từ OS

**Vì sao cần học:** Module riêng cho người làm PHP. Câu hỏi OS với ứng viên PHP gần như luôn đi
qua PHP-FPM. Hầu hết sự cố hiệu năng của app Laravel chạy FPM đều hiện ra ở tầng này:
502/504 khi hết worker, RAM tràn vì `max_children` đặt bừa, request chạy 5 phút dù đã đặt timeout
30 giây, deploy xong vẫn chạy code cũ. Người phỏng vấn ứng viên PHP senior gần như chắc chắn hỏi
cách sizing và cách đọc status của FPM.

**Học gì**

*Process model*
- Một process *master* (chạy root hoặc user riêng) fork ra các *worker*. Mỗi worker xử lý **một
  request một lúc**.
- `pm = static | dynamic | ondemand` quyết định cách master quản lý số worker (chi tiết ở
  [17-performance.md](17-performance.md), module 2.3).
- `pm.max_children` là số worker tối đa, tức trần số request được xử lý đồng thời của pool.
- Share-nothing (module 1.1): mỗi request khởi tạo app từ đầu, không rò state, nhưng trả giá bằng
  thời gian *bootstrap* (nạp framework, config, container) ở mỗi request.
- ⚠️ Khi mọi worker đều bận:
  1. Request mới xếp hàng trong `listen.backlog` (hàng đợi kết nối của socket FPM).
  2. Hàng đợi đầy hoặc chờ quá lâu thì Nginx trả 502 hoặc 504.
  - Một API ngoài chậm có thể chiếm hết worker trong khi CPU vẫn rảnh, vì worker chỉ ngồi chờ.

*Sizing*
- Công thức: `pm.max_children ≈ (RAM dành cho FPM − OPcache) / PSS trung bình mỗi worker`.
  - Ví dụ: 3 GB cho FPM, OPcache 256 MB, mỗi worker PSS 60 MB: `(3072 − 256) / 60 ≈ 46`.
- Đo PSS (module 1.2) dưới tải thật, không đo lúc rảnh. Worker lúc rảnh nhỏ hơn nhiều.
- `pm.max_requests`: worker xử lý đủ N request thì bị thay bằng worker mới, để chặn leak từ
  extension.

*Timeout*
- Chi tiết chuỗi timeout Nginx và FPM ở [02-networking.md](02-networking.md).
- `request_terminate_timeout`: FPM kill worker sau N giây tính theo đồng hồ thật.
- ⚠️ `max_execution_time` trên Linux **không tính** thời gian chờ syscall, stream, query DB. Nó chỉ
  đếm thời gian PHP tự chạy code. Một request treo vì chờ API ngoài có thể vượt xa 30 giây.

*Quan sát*
- `pm.status_path` bật một trang trạng thái, cho biết:
  - Số process đang bận (active) và đang rảnh (idle).
  - `listen queue`: số request đang xếp hàng chờ worker.
  - `max children reached`: số lần pool chạm trần worker.
- `slowlog` + `request_slowlog_timeout`: request chạy quá N giây thì FPM in stack trace PHP của
  nó ra log, cho biết đang kẹt ở dòng nào.

*Signal*
- Xem 2.3: `SIGQUIT` là graceful stop, `SIGUSR2` là graceful reload.

*OPcache nhìn từ OS*
- *OPcache* lưu *bytecode* (code PHP đã được biên dịch sẵn) để không phải biên dịch lại mỗi
  request.
- Bytecode nằm trong shared memory do master tạo trước khi fork, nên mọi worker trong pool dùng
  chung một bản. Kích thước đặt bằng `opcache.memory_consumption`, mặc định 128 MB.
- ⚠️ Hết bộ nhớ OPcache hoặc hết slot `max_accelerated_files` (số file tối đa được cache) thì hiệu
  năng rơi âm thầm, không báo lỗi.
- Production thường đặt `opcache.validate_timestamps=0`: OPcache không kiểm tra file có thay đổi
  không.
  - ⚠️ Vì vậy deploy xong phải reload FPM (hoặc reset OPcache qua FastCGI bằng cachetool), không thì
    vẫn chạy code cũ.
- ⚠️ `opcache_reset()` gọi từ CLI không ảnh hưởng OPcache của FPM. CLI là process khác, có vùng nhớ
  khác.

**Đọc**
- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php), đọc các mục [`pm`](https://www.php.net/manual/en/install.fpm.configuration.php#pm), [`pm.max-children`](https://www.php.net/manual/en/install.fpm.configuration.php#pm.max-children), [`request_terminate_timeout`](https://www.php.net/manual/en/install.fpm.configuration.php#request-terminate-timeout), `pm.status_path`, `slowlog`
- PHP: [`max_execution_time`](https://www.php.net/manual/en/info.configuration.php#ini.max-execution-time) (đọc ghi chú về non-Windows), [OPcache configuration](https://www.php.net/manual/en/opcache.configuration.php) (mục [`validate_timestamps`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.validate-timestamps), [`memory_consumption`](https://www.php.net/manual/en/opcache.configuration.php#ini.opcache.memory-consumption))
- [cachetool](https://github.com/gordalina/cachetool): reset OPcache của FPM từ dòng lệnh
- Chi tiết runtime PHP và Laravel: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Đọc được output của `pm.status_path` và nói pool đang thiếu worker hay worker đang bị chiếm bởi request chậm
- [ ] Giải thích được vì sao `max_execution_time = 30` mà vẫn có request chạy 5 phút
- [ ] Nêu được quy trình deploy Laravel với `validate_timestamps=0` mà không chạy lẫn code cũ và mới

---

### Chặng 3: Senior 🔴

#### 3.1 Container: cgroup, namespace, PID 1

**Vì sao cần học:** Hầu hết app hiện nay chạy trong container, và container làm nhiều thứ hành xử
khác máy thường: pod bị `OOMKilled` dù app "chỉ dùng 70%", `docker stop` chờ đủ 10 giây, zombie
tích tụ. Phỏng vấn senior hay hỏi "container khác VM thế nào" và "exit code 137 trong Kubernetes
thì bạn điều tra ra sao".

**Học gì**

*Container là gì*
- Container là một process bình thường trên máy host, được bọc bởi hai cơ chế của kernel:
  - *cgroup* (control group): **giới hạn tài nguyên** process được dùng, như RAM, CPU, I/O.
  - *namespace*: **giới hạn những gì process nhìn thấy**. Có namespace cho PID (chỉ thấy process
    trong container), mount (file system riêng), network (card mạng riêng), user...
- Khác VM: không có kernel riêng, mọi container dùng chung kernel của host.

*Giới hạn bộ nhớ*
- Vượt `memory.max` (tên giới hạn RAM trong cgroup v2) thì OOM killer chạy bên trong cgroup đó và
  kill process. Kubernetes báo `OOMKilled`, exit code 137.
- ⚠️ Page cache (module 1.2) cũng được tính vào memory của cgroup.
  - Page sạch (chưa sửa) được thu hồi trước khi OOM.
  - *Dirty page* (đã sửa, chưa ghi xuống disk) và *tmpfs* (file system nằm trong RAM) thì khó thu
    hồi.
  - `emptyDir` kiểu memory của Kubernetes là tmpfs, tính vào RAM của pod.

*Runtime có thấy limit của container không*
- JVM: biết mình chạy trong container từ JDK 10 (và 8u191).
  - `-XX:MaxRAMPercentage` mặc định 25%: heap tối đa bằng 25% limit.
  - ⚠️ Ngoài heap, JVM còn dùng Metaspace, thread stack, direct buffer, code cache. Đặt heap bằng
    100% limit là chắc chắn bị OOMKilled.
- Go:
  - `GOMEMLIMIT` (Go 1.19+) cho GC biết ngưỡng bộ nhớ để dọn sớm hơn khi gần chạm.
  - Từ **Go 1.25**, `GOMAXPROCS` mặc định theo CPU limit của cgroup. Bản cũ hơn cần thư viện
    `automaxprocs`.
- PHP-FPM: không tự thấy limit. `pm.max_children` phải tính theo limit của container, không theo
  RAM của node.
- Node: đặt heap bằng `--max-old-space-size`.

*PID 1 trong container*
- Process đầu tiên trong container có PID 1, và PID 1 được kernel đối xử đặc biệt:
  - Signal nào PID 1 không cài handler thì bị **bỏ qua**, không chết như process thường. App không
    cài handler cho SIGTERM thì `docker stop` chờ đủ 10 giây rồi SIGKILL.
  - PID 1 phải *reap* (đọc kết quả và dọn) zombie (module 1.1). App spawn process con (shell,
    headless Chrome) mà không reap thì zombie tích tụ.
- ⚠️ *Shell form* trong Dockerfile như `CMD php artisan ...` hay `CMD npm start`:
  - Docker chạy lệnh qua `sh -c`, nên PID 1 là `sh` (hoặc `npm`), không phải app.
  - `sh` không chuyển SIGTERM cho app, nên app không bao giờ biết mình sắp bị dừng.
  - Sửa: dùng *exec form* `CMD ["php", "artisan", "..."]`, và kết thúc entrypoint script bằng
    `exec "$@"` để app thay thế shell.
- Hoặc dùng một init nhỏ làm PID 1, chuyển signal và reap zombie hộ: `tini`, `dumb-init`,
  `docker run --init`.

```bash
#!/bin/sh
# entrypoint.sh: chuẩn bị xong thì exec để app thay thế shell, trở thành PID 1
set -eu
envsubst < /app/config.tpl > /app/config.yml
exec "$@"
```

**Đọc**
- Kernel docs: [Control Group v2](https://docs.kernel.org/admin-guide/cgroup-v2.html), mục *Memory* (`memory.max`, `memory.high`, `memory.stat`) và *CPU*
- man: [namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html), [pid_namespaces(7)](https://man7.org/linux/man-pages/man7/pid_namespaces.7.html) (mục về init process và signal)
- Docker: [Shell and exec form](https://docs.docker.com/reference/dockerfile/#shell-and-exec-form), [`--init`](https://docs.docker.com/reference/cli/docker/container/run/#init); [tini](https://github.com/krallin/tini) README
- Go blog: [Container-aware GOMAXPROCS](https://go.dev/blog/container-aware-gomaxprocs); [Go GC guide](https://go.dev/doc/gc-guide) (mục memory limit)
- Kubernetes: [Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)

**Nắm chắc khi**
- [ ] Đo được thời gian `docker stop` với shell form và exec form, giải thích khác biệt (bài tập 2)
- [ ] Giải thích được vì sao JVM đặt heap 70% limit vẫn bị OOMKilled, kể được ít nhất 3 vùng nhớ ngoài heap
- [ ] Đọc được `memory.stat` của một cgroup và chỉ ra phần nào là page cache, phần nào là anon

#### 3.2 CPU khi vận hành: load average, steal, throttling

**Vì sao cần học:** "Load 20 là cao hay thấp?", "CPU chỉ 40% mà p99 tăng gấp đôi": các câu này đều
cần đọc đúng chỉ số CPU. Trên cloud và Kubernetes còn có hai nguyên nhân chậm mà máy dev không
bao giờ gặp: CPU steal và CPU throttling. Đây là câu hỏi senior hay dùng để phân biệt người từng
vận hành production thật.

**Học gì**

*Load average*
- *Load average* là ba số trong `uptime` và `top`: trung bình số task đang chạy hoặc chờ chạy,
  trong 1, 5 và 15 phút. Đây là trung bình trượt hàm mũ, số gần đây nặng ký hơn.
- ⚠️ Linux tính cả task ở trạng thái `D` (chờ disk, module 1.1). Vì vậy load cao chưa chắc là do
  CPU.
  - Phân biệt bằng `vmstat`: cột `r` cao là chờ CPU, cột `b` và `wa` cao là chờ I/O. Xem thêm
    `iostat`.
- Phải so với số core:
  - Load 8 trên máy 8 core là vừa đủ. Trên máy 2 core là đang có task xếp hàng.
- Số 1 phút lớn hơn số 15 phút là tải đang tăng.

*CPU steal*
- *CPU steal* (cột `st`): vCPU của máy ảo muốn chạy nhưng *hypervisor* (phần mềm chạy nhiều máy ảo
  trên một máy thật) đang đưa CPU thật cho máy ảo khác.
- `st` cao nghĩa là:
  - Hàng xóm trên cùng máy thật đang ồn.
  - Hoặc instance loại *burstable* (như AWS `t3`) đã hết *CPU credit* và bị hạ tốc.

*CPU throttling trong container*
- Container có CPU limit được kernel giới hạn bằng *CFS bandwidth*: mỗi *period* (mặc định 100 ms)
  container chỉ được dùng một lượng CPU gọi là *quota*.
- Cơ chế:
  1. Limit 0,5 core nghĩa là quota 50 ms CPU trong mỗi period 100 ms.
  2. Container dùng hết 50 ms quota sớm trong period.
  3. Kernel dừng mọi thread của container tới hết period, **dù node còn rảnh**.
  4. Request đang chạy bị treo phần còn lại của period, p99 tăng.
- Xem bằng `nr_throttled` và `throttled_usec` trong file `cpu.stat` của cgroup.
- ⚠️ Runtime tạo nhiều thread hơn limit làm throttle nặng hơn, vì nhiều thread cùng tiêu quota:
  JVM cũ, Go trước 1.25, PHP-FPM có `max_children` lớn.
- Tranh luận "bỏ CPU limit, chỉ giữ CPU request":
  - Được: hết throttle, pod dùng được CPU rảnh của node.
  - Mất: không còn cô lập, một pod ăn CPU làm chậm pod khác trên cùng node.
  - Cần nói được trade-off này, không có đáp án đúng tuyệt đối.

*Phương pháp USE*
- *USE method* (Brendan Gregg): với mỗi tài nguyên (CPU, RAM, disk, network), kiểm tra ba thứ:
  - *Utilization*: bận bao nhiêu phần trăm.
  - *Saturation*: có việc phải xếp hàng chờ không (ví dụ load > số core).
  - *Errors*: có lỗi không.
- Đi lần lượt từng tài nguyên thay vì đoán.

**Đọc**
- Brendan Gregg: [Linux Load Averages: Solving the Mystery](https://www.brendangregg.com/blog/2017-08-08/linux-load-averages.html), [The USE Method](https://www.brendangregg.com/usemethod.html)
- Kernel docs: [CFS Bandwidth Control](https://docs.kernel.org/scheduler/sched-bwc.html)
- *Systems Performance*: chương *CPUs*

**Nắm chắc khi**
- [ ] Chạy một tác vụ CPU nặng và một tác vụ I/O nặng, giải thích các cột của `vmstat`/`iostat` thay đổi thế nào (bài tập 4)
- [ ] Với load 20 trên máy 8 core, nói được 3 hướng nguyên nhân và lệnh để phân biệt
- [ ] Tính được: CPU limit 0,5 core, request tốn 80 ms CPU liên tục, latency tệ nhất là bao nhiêu và vì sao

#### 3.3 I/O nâng cao: fsync, zero-copy, io_uring

**Vì sao cần học:** Module này trả lời "dữ liệu đã ghi thì có chắc còn không khi mất điện", nền để
hiểu cấu hình durability của MySQL và cách ghi file config an toàn. Phần zero-copy và io_uring giải
thích vì sao Nginx, Kafka nhanh và runtime mới đang đi về đâu. Thường xuất hiện ở câu hỏi senior
về database hoặc hệ thống lưu trữ.

**Học gì**

*write() chưa phải là đã ghi xuống disk*
- `write()` trả về thành công khi dữ liệu mới vào page cache (RAM, module 1.2). Mất điện lúc đó là
  mất dữ liệu.
- `fsync(fd)` ép kernel ghi dữ liệu của file xuống thiết bị, và chỉ trả về khi thiết bị báo đã
  ghi xong.
- Database gọi fsync khi commit, trên *redo log* (MySQL) hay *WAL* (Postgres): nhật ký ghi trước để
  khôi phục sau sự cố.
  - Đó là lý do có `innodb_flush_log_at_trx_commit` và `sync_binlog`: đánh đổi giữa an toàn và tốc
    độ ([03-database-sql.md](03-database-sql.md)).
- ⚠️ Disk hoặc controller có write cache không có pin dự phòng có thể "nói dối" rằng fsync đã
  xong. Cloud disk có đảm bảo riêng của nhà cung cấp.

*Ghi file an toàn*
- Ghi đè trực tiếp lên file config: mất điện giữa chừng là file hỏng một nửa. Cách đúng gồm 4 bước:
  1. Ghi nội dung mới vào một file tạm trong cùng thư mục.
  2. `fsync` file tạm, để nội dung chắc chắn nằm trên disk.
  3. `rename` file tạm đè lên file đích. `rename` là atomic trong cùng file system: người đọc chỉ
     thấy file cũ hoặc file mới, không bao giờ thấy nửa vời.
  4. `fsync` thư mục cha, để việc đổi tên (một thay đổi của directory entry) cũng nằm trên disk.

*Zero-copy*
- Gửi một file tĩnh bằng `read` + `write` thì dữ liệu đi: disk → page cache → bộ nhớ của app (user
  space) → kernel → socket. Nó đi qua user space hai lần copy, tốn CPU vô ích.
- *Zero-copy* với `sendfile`: kernel chuyển thẳng từ page cache sang socket, app không chạm vào dữ
  liệu.
- Dùng ở Nginx `sendfile on`, Kafka, Java `FileChannel.transferTo`.
- ⚠️ TLS mã hoá trong user space thì dữ liệu buộc phải đi qua app, mất zero-copy. Trừ khi dùng
  *kTLS* (TLS làm trong kernel).

*io_uring*
- *io_uring* (kernel 5.1+) là giao diện I/O bất đồng bộ mới của Linux:
  - App và kernel dùng chung hai *ring buffer* (hàng đợi vòng): một để app gửi yêu cầu, một để
    kernel trả kết quả. Không cần một syscall cho mỗi thao tác.
  - Kiểu *completion-based*: kernel báo "đã đọc xong, dữ liệu đây", khác epoll chỉ báo "đã sẵn
    sàng, tự đọc đi".
  - Nhờ vậy làm được file I/O bất đồng bộ thật, điều epoll không làm được (module 2.2).
- ⚠️ io_uring có lịch sử nhiều lỗ hổng bảo mật. Nhiều môi trường chặn nó, ví dụ profile
  *seccomp* (bộ lọc syscall được phép gọi) mặc định của Docker và một số nhà cung cấp cloud.
- Backend engineer thường không gọi trực tiếp. Biết để hiểu runtime và database mới dùng gì.

**Đọc**
- man: [fsync(2)](https://man7.org/linux/man-pages/man2/fsync.2.html), [rename(2)](https://man7.org/linux/man-pages/man2/rename.2.html), [sendfile(2)](https://man7.org/linux/man-pages/man2/sendfile.2.html), [io_uring(7)](https://man7.org/linux/man-pages/man7/io_uring.7.html)
- LWN: [Ensuring data reaches disk](https://lwn.net/Articles/457667/)
- Dan Luu: [Files are hard](https://danluu.com/file-consistency/): vì sao ghi file bền vững khó hơn tưởng

**Nắm chắc khi**
- [ ] Viết được đoạn code ghi file config atomic, đủ 4 bước, giải thích bước nào thiếu thì mất gì
- [ ] Vẽ được đường đi của dữ liệu khi gửi file tĩnh có và không có `sendfile`
- [ ] Giải thích được vì sao epoll không giúp gì cho đọc file thường, còn io_uring thì có

#### 3.4 Copy-on-write, fork và huge page

**Vì sao cần học:** Copy-on-write giải thích vì sao 50 worker PHP-FPM không tốn gấp 50 lần RAM, và
vì sao Redis cần gần gấp đôi RAM lúc snapshot. Huge page là cấu hình mà các database đưa ra khuyến
nghị trái ngược nhau, hay bị hỏi khi phỏng vấn về vận hành Redis hay MongoDB.

**Học gì**

*Copy-on-write khi fork*
- *Copy-on-write* (COW): `fork()` không copy RAM của cha sang con ngay.
  1. Cha và con dùng chung mọi page, được đánh dấu chỉ đọc.
  2. Khi một bên ghi vào một page, kernel mới copy riêng page đó cho bên ghi.
  3. Page không ai ghi thì dùng chung mãi.
- PHP-FPM tận dụng điều này: master nạp extension và tạo shared memory cho OPcache trước, rồi mới
  fork. Các worker dùng chung phần không bị ghi.

*Redis và fork*
- Redis chụp snapshot (BGSAVE) hoặc viết lại AOF bằng cách fork: process con ghi dữ liệu ra disk,
  process cha tiếp tục phục vụ.
- ⚠️ Trong lúc snapshot, mỗi page cha ghi vào đều bị copy. Ghi nhiều thì RAM gần gấp đôi.
- Redis khuyến nghị `vm.overcommit_memory=1` để fork không bị kernel từ chối (module 1.2,
  overcommit).

*Huge page*
- Page mặc định 4 KB. *Huge page* là page 2 MB. *Transparent Huge Pages* (THP) là cơ chế kernel tự
  dùng huge page mà app không cần biết.
- Lợi: ít page hơn nên ít *TLB miss* (lần dịch địa chỉ không có sẵn trong bộ đệm của CPU).
- Hại:
  - COW tốn hơn: ghi 1 byte là phải copy cả 2 MB thay vì 4 KB.
  - Kernel gom page thành huge page có thể gây latency spike.
- Redis khuyên tắt THP.
- ⚠️ Khuyến nghị đổi theo phiên bản: MongoDB 8.0 (dùng TCMalloc mới) chuyển sang khuyên **bật** THP.
  Luôn đọc production notes của đúng phiên bản mình chạy.

**Đọc**
- man: [fork(2)](https://man7.org/linux/man-pages/man2/fork.2.html) (mục copy-on-write)
- Kernel docs: [Transparent Hugepage Support](https://docs.kernel.org/admin-guide/mm/transhuge.html)
- Redis: [Administration](https://redis.io/docs/latest/operate/oss_and_stack/management/admin/) (overcommit, THP), [Diagnosing latency](https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/latency/) (mục fork và THP)
- MongoDB: [TCMalloc Performance Optimization](https://www.mongodb.com/docs/manual/administration/tcmalloc-performance/)

**Nắm chắc khi**
- [ ] Giải thích được vì sao Redis 10 GB dữ liệu cần hơn 10 GB RAM khi BGSAVE, và nó phụ thuộc vào gì
- [ ] Nói được tại sao cùng là "THP", Redis khuyên tắt còn MongoDB 8.0 khuyên bật

#### 3.5 Debug production có phương pháp

**Vì sao cần học:** Khi production chậm hoặc treo, người senior được kỳ vọng có một quy trình rõ
ràng thay vì đoán mò hay restart. Phỏng vấn thường đưa một tình huống ("server chậm, bạn SSH vào,
làm gì trong 60 giây đầu") và chấm cách bạn thu hẹp vấn đề.

**Học gì**

*Quy trình 60 giây đầu*
- Chạy lần lượt, mỗi lệnh trả lời một câu hỏi:
  1. `uptime`: load average đang tăng hay giảm.
  2. `dmesg -T | tail`: kernel có báo OOM, lỗi disk không.
  3. `vmstat 1`: chờ CPU, chờ I/O, hay đang swap.
  4. `mpstat -P ALL 1`: có core nào bận 100% một mình không (dấu hiệu việc chỉ chạy một thread).
  5. `pidstat 1`: process nào ăn CPU.
  6. `iostat -xz 1`: disk có quá tải không.
  7. `free -m`: RAM còn bao nhiêu.
  8. `sar -n DEV 1`: lưu lượng mạng.
  9. `sar -n TCP,ETCP 1`: số kết nối TCP mới, retransmit.
  10. `top`: nhìn tổng thể lần cuối.

*Chọn công cụ theo câu hỏi*

| Công cụ | Trả lời câu hỏi | Overhead |
|---|---|---|
| `strace` | Process đang kẹt ở syscall gì, chờ ai | ⚠️ Cao, làm process chậm đi nhiều lần |
| `perf` + flame graph | CPU đang tiêu vào hàm nào | Thấp |
| eBPF (`bpftrace`, BCC tools) | Quan sát bên trong kernel: file nào được mở, I/O chậm bao nhiêu, gói nào bị gửi lại | Thấp, an toàn |

- `strace -p <pid> -f -tt -e trace=network`: theo dõi các syscall mạng của một process, kèm giờ.
  ⚠️ Cẩn thận khi chạy trên production.
- `perf top`, `perf record -g` rồi vẽ *flame graph* (hình tổng hợp các stack, hàm càng rộng càng tốn
  CPU, chi tiết ở [17-performance.md](17-performance.md)).
- *eBPF*: cơ chế chạy chương trình nhỏ, đã được kiểm tra an toàn, bên trong kernel. Một số BCC tool:
  - `execsnoop`: process mới được chạy. `opensnoop`: file được mở.
  - `biolatency`: phân phối latency của disk I/O. `tcpretrans`: gói TCP bị gửi lại.

*Off-CPU: chậm vì chờ*
- *Off-CPU*: thời gian process không chạy trên CPU vì đang chờ lock, I/O, network.
- ⚠️ Request chậm vì chờ thì **không hiện** trên CPU profile. Cần off-CPU analysis hoặc tracing.
- Process ở trạng thái `D` đang chờ gì: xem `/proc/<pid>/stack` (stack trong kernel) và
  `/proc/<pid>/wchan` (hàm kernel nó đang ngủ trong đó).

*Áp vào PHP-FPM*
- `slowlog` cho stack trace PHP của request chậm (module 2.6).
- `strace -p` một worker đang treo để thấy nó đang chờ socket nào, rồi đối chiếu với `lsof` để biết
  socket đó nối tới host nào.

**Đọc**
- Brendan Gregg: [Linux perf examples](https://www.brendangregg.com/perf.html), [eBPF tools](https://www.brendangregg.com/ebpf.html), [Flame Graphs](https://www.brendangregg.com/flamegraphs.html)
- *Systems Performance*: chương *Methodologies* và *Observability Tools*
- man: [strace(1)](https://man7.org/linux/man-pages/man1/strace.1.html), [pidstat(1)](https://man7.org/linux/man-pages/man1/pidstat.1.html)

**Nắm chắc khi**
- [ ] Chạy được checklist 60 giây trên một máy thật và viết một đoạn kết luận máy đang nghẽn ở đâu (hoặc không nghẽn)
- [ ] Dùng `strace` tìm được một worker PHP-FPM đang treo chờ kết nối tới host nào
- [ ] Giải thích được khi nào dùng strace, khi nào dùng perf, khi nào dùng eBPF

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Process và thread khác nhau thế nào? Khi nào chọn multi-process?** (1.1)
- Ý phải có: không gian địa chỉ riêng so với dùng chung heap/fd; thread có stack riêng; process cô lập lỗi tốt hơn, tạo tốn hơn
- Điểm cộng: nối sang hệ quả vận hành: PHP-FPM chọn process nên sizing theo RAM và không lo thread-safety; Java/Go chọn thread nên chia sẻ pool nhưng phải lo race
- Red flag: chỉ nói "thread nhẹ hơn" mà không có hệ quả nào

**2. Stack và heap khác nhau thế nào? Biến cục bộ nằm ở đâu?** (1.2)
- Ý phải có: stack theo frame hàm, tự thu khi ra hàm, mỗi thread một stack; heap cho object sống lâu, do GC thu
- Điểm cộng: escape analysis của Go; tràn stack khi đệ quy sâu ở từng ngôn ngữ

**3. SIGTERM và SIGKILL khác nhau thế nào? Vì sao phải xử lý SIGTERM?** (2.3)
- Ý phải có: SIGTERM bắt được, cho app dọn dẹp; SIGKILL không bắt được; Docker/K8s gửi SIGTERM rồi SIGKILL sau grace period
- Điểm cộng: PHP-FPM coi SIGTERM là dừng ngay, graceful là SIGQUIT; exit code 137/143

**4. Hard link và symlink khác nhau thế nào?** (1.3)
- Ý phải có: cùng inode so với file chứa đường dẫn; xoá gốc thì hard link còn, symlink gãy; hard link không vượt file system
- Điểm cộng: deploy bằng đổi symlink `current`, và bẫy OPcache/realpath cache khi làm vậy

**5. Làm sao tìm process đang chiếm port 8080?** (1.4)
- Ý phải có: `ss -ltnp | grep 8080` hoặc `lsof -i :8080`
- Điểm cộng: cần root để thấy process của user khác; trong container thì phải vào đúng network namespace

**6. Disk báo đầy 100%, `du` cộng lại chỉ ra 40%. Vì sao?** (1.3)
- Ý phải có: file đã xoá nhưng process còn giữ fd; tìm bằng `lsof +L1`; restart/reload process hoặc truncate qua `/proc/<pid>/fd/<n>`
- Điểm cộng: nguyên nhân gốc thường là log bị `rm` thay vì rotate đúng; kiểm tra thêm mount che thư mục và `df -i`

**7. `free` báo còn rất ít RAM trống, có đáng lo không?** (1.2)
- Ý phải có: không, kernel dùng RAM rảnh làm page cache; nhìn `available`
- Red flag: đề xuất `echo 3 > /proc/sys/vm/drop_caches` định kỳ

### 🟡 Mid

**8. Vì sao Go chạy được hàng trăm nghìn goroutine mà Java truyền thống không chạy được hàng trăm nghìn thread?** (2.1)
- Ý phải có: stack goroutine 2 KB tự giãn so với thread OS reserve vài MB; runtime lập lịch M:N trong user space, không qua kernel; giới hạn `threads-max`/`pid_max`
- Điểm cộng: Java virtual thread giờ cũng M:N; pinning; bottleneck chuyển xuống DB pool

**9. Server báo "too many open files". Điều tra thế nào?** (2.2)
- Ý phải có: đếm fd theo thời gian để phân biệt leak và tải thật; `lsof` xem loại fd; sửa leak trước, rồi mới đặt limit đúng chỗ (`LimitNOFILE`)
- Điểm cộng: nhiều `CLOSE_WAIT` là app không đóng connection; thêm metric/alert số fd
- Red flag: "tăng ulimit lên 1 triệu là xong"

**10. Vì sao một event loop phục vụ được hàng nghìn kết nối? Điểm yếu là gì?** (2.2)
- Ý phải có: epoll; không thread nào chờ I/O; kết nối rảnh chỉ tốn vài KB. Điểm yếu: CPU nặng chặn tất cả; file I/O vẫn block
- Điểm cộng: level và edge-triggered; libuv threadpool

**11. Ngôn ngữ có GC vẫn bị memory leak được không? PHP thì sao?** (2.4)
- Ý phải có: có, khi còn tham chiếu mà không dùng; ví dụ cache không giới hạn, listener, static collection
- Điểm cộng: PHP-FPM ít bị vì reset mỗi request, nhưng queue worker và Octane thì bị; `--max-jobs`, `pm.max_requests` là giảm thiệt hại, không phải sửa gốc

**12. Load average là gì? Load 4 trên máy 4 core và máy 1 core khác nhau thế nào?** (3.2)
- Ý phải có: số task chạy hoặc chờ chạy, trung bình trượt; so với số core; Linux tính cả task `D`
- Điểm cộng: dùng `vmstat` để tách CPU, I/O, steal

**13. Viết cron job cần lưu ý gì?** (2.5)
- Ý phải có: timezone, PATH/env tối thiểu, chạy trùng, nhiều server, log output, idempotent
- Điểm cộng: `%` phải escape; systemd timer; `onOneServer()` cần cache store dùng chung

**14. PHP-FPM log `server reached pm.max_children`, Nginx trả 504. Làm gì?** (2.6)
- Ý phải có: xem worker bị chiếm vì request chậm hay thiếu worker thật; `pm.status_path`, slowlog; đặt timeout cho HTTP client, tách việc chậm sang queue
- Điểm cộng: tăng `max_children` chỉ khi RAM đủ (tính theo PSS); `max_execution_time` không tính thời gian chờ I/O nên không cứu được
- Red flag: tăng `max_children` gấp đôi ngay

**15. Deploy Laravel xong mà vẫn chạy code cũ, hoặc lẫn cũ và mới. Vì sao?** (2.6, 1.3)
- Ý phải có: OPcache với `validate_timestamps=0` giữ bytecode cũ; realpath cache giữ đường dẫn symlink cũ; cần reload FPM hoặc reset OPcache qua FastCGI
- Điểm cộng: `$realpath_root` trong Nginx; `opcache_reset()` từ CLI không có tác dụng với FPM

**16. Logrotate xong mà app vẫn ghi vào file cũ đã bị đổi tên. Sửa thế nào?** (2.3)
- Ý phải có: app giữ fd tới inode cũ; hoặc gửi signal cho app mở lại file (`postrotate`), hoặc dùng `copytruncate`
- Điểm cộng: `copytruncate` có thể mất log giữa lúc copy và truncate; với container thì log ra stdout, để runtime lo rotate

### 🔴 Senior

**17. Container bị kill liên tục, exit code 137. Xử lý thế nào?** (3.1, 2.4)
- Ý phải có: 137 = SIGKILL, do OOM hoặc hết grace period; phân biệt bằng `OOMKilled` trong pod status và `dmesg`; xem đồ thị bộ nhớ tăng dần (leak) hay đột biến (request lớn)
- Điểm cộng: runtime có biết limit không (JVM %, `GOMEMLIMIT`, `max_children` của FPM); page cache và tmpfs tính vào cgroup
- Red flag: tăng memory limit mà không tìm nguyên nhân

**18. JVM đặt heap 70% limit vẫn bị OOMKilled. Vì sao?** (3.1)
- Ý phải có: metaspace, thread stack, direct buffer, code cache, GC overhead nằm ngoài heap
- Điểm cộng: Native Memory Tracking (`-XX:NativeMemoryTracking`); đặt `MaxRAMPercentage` hợp lý thay vì `-Xmx` cứng

**19. Vì sao app trong container không tắt khi `docker stop`, phải chờ 10 giây?** (3.1)
- Ý phải có: PID 1 không có handler thì signal bị bỏ qua; shell form làm `sh` là PID 1 và không chuyển signal
- Điểm cộng: exec form, `exec "$@"`, tini; với PHP-FPM còn phải đúng `STOPSIGNAL SIGQUIT`

**20. Sau mỗi lần rollout trên Kubernetes có vài request 502, và pod mất đúng 30 giây mới tắt.** (2.3, 3.1)
- Ý phải có: 30 giây là hết grace period, app không xử lý SIGTERM; 502 vì endpoint chưa bị gỡ khỏi LB mà app đã ngừng nhận
- Điểm cộng: `preStop` sleep ngắn; thứ tự readiness fail → chờ LB → drain; job dài thì checkpoint hoặc trả về queue

**21. Service Go trong container có CPU limit 1 core, node 32 core; p99 cao dù CPU trung bình 50%.** (3.2, 3.1)
- Ý phải có: CPU throttling; kiểm tra `nr_throttled` trong `cpu.stat`; `GOMAXPROCS` có đang bằng 32 không (Go trước 1.25)
- Điểm cộng: trung bình 50% che mất các burst hết quota trong chu kỳ 100 ms; trade-off bỏ CPU limit

**22. Server load average 20, xử lý thế nào?** (3.2, 3.5)
- Ý phải có: load gồm cả task chờ disk; `vmstat 1`: `r` cao là CPU, `b`/`wa` cao là I/O, `st` cao là hypervisor
- Điểm cộng: scale ngang không giúp gì nếu cả cụm cùng chờ một database; USE method

**23. Database đảm bảo dữ liệu đã commit không mất khi mất điện bằng cách nào?** (3.3)
- Ý phải có: ghi log (WAL/redo) và `fsync` trước khi báo commit thành công; page cache không đủ
- Điểm cộng: cấu hình đánh đổi độ bền lấy throughput; write cache không pin nói dối; ghi file an toàn bằng rename

**24. `epoll` khác `select` thế nào? Khi nào `sendfile` không dùng được?** (2.2, 3.3)
- Ý phải có: đăng ký một lần và chỉ trả fd sẵn sàng so với truyền lại và quét cả tập; `sendfile` mất tác dụng khi phải xử lý dữ liệu trong user space (TLS không có kTLS, nén)
- Điểm cộng: edge-triggered; io_uring là completion-based

**25. Cron báo cáo doanh thu ra số sai vào đầu tháng và thỉnh thoảng gửi mail hai lần.** (2.5)
- Ý phải có: timezone làm "hôm qua" lệch ngày; hai lần do nhiều server cùng chạy hoặc lần trước chưa xong
- Điểm cộng: khoá chạy trùng, chỉ định nơi chạy, job idempotent (đánh dấu đã gửi); tính khoảng thời gian theo timezone nghiệp vụ, lưu UTC

**26. API chậm dần sau vài ngày chạy, restart là hết. Điều tra thế nào?** (2.4, 3.5)
- Ý phải có: nghi leak (bộ nhớ, fd, goroutine/thread, connection); đồ thị theo thời gian; heap dump/`pprof` so hai thời điểm
- Điểm cộng: recycle định kỳ là biện pháp tạm, phải có ticket tìm gốc; soak test để tái hiện ([17-performance.md](17-performance.md))

---

## Bài tập tự làm

1. **fd leak.** Viết chương trình nhỏ (Go hoặc PHP CLI) mở file liên tục mà không đóng. Đặt `ulimit -n` thấp, quan sát lỗi, rồi dùng `lsof` và `/proc/<pid>/fd` để xác nhận.
2. **PID 1 và signal.** Viết Dockerfile chạy một app có xử lý SIGTERM:
   - Thử shell form và exec form của `CMD`, đo thời gian `docker stop` từng trường hợp và giải thích khác biệt.
   - Làm lại với image `php:8.4-fpm`: gửi `SIGTERM` và `SIGQUIT` khi đang có request dài chạy, ghi lại request đó có được làm xong không.
3. **Script và cron.** Viết script backup MySQL có `set -euo pipefail`, `trap` dọn file tạm, khoá chạy trùng bằng `flock`, dùng `"${BACKUP_DIR:?}"`, và cài vào cron chạy 2h sáng giờ Việt Nam trên máy dùng UTC.
4. **Đọc số liệu hệ thống.** Trên một máy Linux, chạy một tác vụ đọc disk nặng và một tác vụ CPU nặng. Với mỗi tác vụ, ghi lại `uptime`, `vmstat 1`, `iostat -xz 1` và giải thích các cột thay đổi.
5. **Sizing PHP-FPM.** Lập bảng sizing cho server 4 GB RAM:
   - Đo PSS của worker thật (hoặc giả định 60 MB), tính phần RAM cho OS, Nginx, OPcache.
   - Chọn `pm = static` hoặc `dynamic` và giải thích.
   - Nêu cách bạn biết con số đã đúng sau khi lên production (metric nào, ngưỡng nào).
6. **Logrotate.** Cấu hình logrotate cho `storage/logs/laravel.log` theo hai kiểu `copytruncate` và `create` + signal (nếu app không reopen được thì giải thích vì sao). Viết script ghi log liên tục và kiểm tra kiểu nào làm mất dòng.

> Nộp bài vào đây để được review.
