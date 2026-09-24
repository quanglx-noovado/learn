# 14. Hệ phân tán

> [← Mục lục](README.md) · Phạm vi: bản chất của hệ phân tán, CAP/PACELC và consistency model, replication, partitioning, consensus, thời gian, distributed transaction, distributed lock, resilience pattern, sinh ID, service discovery, exactly-once.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**Bản chất**
- [ ] 🟢 Fallacies of distributed computing
- [ ] 🟡 Partial failure; "không biết request có thành công không"

**Nhất quán**
- [ ] CAP (giải thích đúng) ⚠️
- [ ] 🟡 PACELC
- [ ] 🟡 Consistency models: linearizable, sequential, causal, eventual, read-your-writes, monotonic reads

**Replication và partitioning**
- [ ] 🟡 Single-leader, multi-leader, leaderless; quorum `R + W > N`
- [ ] 🔴 Conflict resolution: LWW, vector clock, CRDT
- [ ] 🟡 Replication lag và hệ quả
- [ ] 🟡 Partitioning: range vs hash, hot spot
- [ ] 🔴 Consistent hashing, virtual node, rebalancing

**Consensus và thời gian**
- [ ] 🔴 Raft: term, leader election, log replication, quorum
- [ ] 🔴 Split brain; etcd/ZooKeeper dùng để làm gì
- [ ] 🔴 Clock skew, NTP, Lamport clock, vector clock ⚠️

**Transaction và lock**
- [ ] 🟡 2PC và vì sao blocking; 🔴 3PC đại ý
- [ ] 🟡 Saga: orchestration vs choreography, compensating action, không có isolation ⚠️
- [ ] 🟡 Outbox ([12-messaging.md](12-messaging.md))
- [ ] 🔴 TCC
- [ ] 🟡 Distributed lock: Redis `SET NX PX` + Lua; lease; 🔴 fencing token; 🔴 Redlock; lock bằng DB/etcd/ZooKeeper

**Resilience**
- [ ] Timeout ⚠️; retry + exponential backoff + jitter; 🔴 retry budget
- [ ] Idempotency
- [ ] 🟡 Circuit breaker (closed, open, half-open)
- [ ] 🟡 Bulkhead, rate limit, load shedding
- [ ] 🟡 Graceful degradation, fallback
- [ ] 🔴 Hedged requests
- [ ] 🟡 Cascading failure, retry storm; 🔴 metastable failure

**Hạ tầng phân tán**
- [ ] 🟡 ID generation: UUID v4/v7, ULID, Snowflake, DB sequence/segment
- [ ] 🟡 Service discovery, health check (liveness vs readiness)
- [ ] 🔴 Leader election, gossip, membership
- [ ] 🔴 Exactly-once thật sự là gì; end-to-end argument

## Chi tiết

### Bản chất

- [ ] Các giả định sai về hệ phân tán (fallacies), tám điều thường được liệt kê:
      mạng luôn ổn định, độ trễ bằng 0, băng thông vô hạn, mạng an toàn, topology không đổi,
      chỉ có một người quản trị, chi phí truyền tải bằng 0, mạng đồng nhất
  - Mỗi cái là một loại bug: không có timeout (mạng ổn định), gọi API trong vòng lặp N+1
    (độ trễ 0), response 10 MB (băng thông vô hạn), hardcode IP (topology không đổi)
- [ ] 🟡 Partial failure
  - Trong một máy, lỗi thường là "chạy hết" hoặc "chết hết". Trong hệ phân tán, một phần
    chết, một phần chậm, một phần vẫn chạy, và **không phân biệt được** node chết hay chậm
  - Chậm còn tệ hơn chết: node chết thì bị loại nhanh, node chậm giữ connection, thread và
    kéo cả hệ thống chậm theo
- [ ] 🟡 "Không biết request có thành công không"
  - Gửi request, nhận timeout. Ba khả năng: request mất trên đường đi, bên kia xử lý xong
    nhưng response mất, bên kia vẫn đang xử lý. Bên gọi **không thể biết**
  - Hệ quả: retry mù có thể trừ tiền hai lần; không retry có thể mất đơn
  - Cách xử lý: **idempotency key** để retry an toàn; API tra trạng thái (`GET /payments/{key}`)
    trước khi làm lại; đối soát (reconciliation) định kỳ với bên kia
  - Liên quan: bài toán hai vị tướng (two generals) chứng minh không có giao thức nào đảm
    bảo hai bên chắc chắn đồng thuận qua kênh không tin cậy

### Nhất quán

- [ ] **CAP theorem**: khi có network partition, phải chọn giữa consistency và availability
  - Định nghĩa chặt: **C** = linearizability (mọi đọc thấy lần ghi mới nhất như thể chỉ có một
    bản dữ liệu); **A** = mọi request tới node còn sống đều nhận response không lỗi;
    **P** = hệ thống tiếp tục hoạt động dù mạng mất message giữa các node
  - ⚠️ Không phải "chọn 2 trong 3" một cách tuỳ ý; partition luôn có thể xảy ra
  - Nên câu đúng là: **khi partition xảy ra**, node bị tách phải chọn hoặc từ chối phục vụ
    (CP) hoặc phục vụ dữ liệu có thể cũ (AP). Khi không có partition, có thể có cả C và A
  - Ví dụ: hai data center mất kết nối. Hệ thống ngân hàng: DC phụ ngừng nhận giao dịch (CP).
    Giỏ hàng: cả hai DC vẫn nhận thêm hàng, gộp lại sau (AP)
  - ⚠️ Phần lớn DB không thuần CP hay AP; nhiều hệ thống cho chọn theo từng thao tác
    (Cassandra theo consistency level). Nhiều thứ gọi là "CA" (một node Postgres) thực ra chỉ
    là không phân tán. "C" trong CAP khác "C" trong ACID
- [ ] 🟡 PACELC: khi có Partition thì chọn A hoặc C; **Else** (bình thường) chọn giữa
      **L**atency và **C**onsistency
  - Có ích hơn CAP trong thực tế vì partition hiếm, còn đánh đổi độ trễ thì xảy ra mỗi request:
    chờ replica xác nhận (nhất quán, chậm) hay trả lời ngay (nhanh, có thể lệch)
  - Ví dụ: DynamoDB/Cassandra mặc định PA/EL; Spanner, hệ dùng consensus là PC/EC
- [ ] 🟡 Mô hình nhất quán (từ mạnh tới yếu), ví dụ với bài đăng mạng xã hội

  | Model | Đảm bảo | Ví dụ vi phạm |
  |---|---|---|
  | Linearizable | mọi thao tác như xảy ra tức thời tại một điểm giữa lúc gửi và lúc nhận; ai đọc sau khi ghi xong đều thấy | A đổi mật khẩu xong, B đăng nhập bằng mật khẩu cũ vẫn được |
  | Sequential | mọi node thấy cùng một thứ tự, khớp thứ tự của từng client, nhưng không bám theo thời gian thực | — |
  | Causal | thao tác có quan hệ nhân quả được thấy đúng thứ tự; thao tác độc lập có thể thấy khác thứ tự | thấy câu trả lời "đồng ý" trước khi thấy câu hỏi |
  | Read-your-writes | chính mình luôn thấy thứ mình vừa ghi | đăng bài xong F5 thì bài biến mất |
  | Monotonic reads | đã thấy dữ liệu mới thì không bị lùi về dữ liệu cũ | F5 lần 1 thấy comment, lần 2 không thấy (đọc từ replica khác) |
  | Eventual | ngừng ghi thì cuối cùng mọi replica giống nhau; không hứa bao lâu | — |

  - Read-your-writes thực hiện bằng: đọc từ primary trong vài giây sau khi user ghi, hoặc gắn
    version/LSN vào session và chỉ đọc replica đã bắt kịp
  - Monotonic reads: gắn user với một replica cố định (sticky)
  - ⚠️ "Eventual" không có nghĩa là "nhanh". Replication lag có thể lên tới phút khi replica quá tải

### Replication

- [ ] 🟡 Ba kiểu replication

  | | Single-leader | Multi-leader | Leaderless |
  |---|---|---|---|
  | Ghi ở đâu | chỉ leader | nhiều leader (thường mỗi DC một) | bất kỳ node, gửi tới nhiều node |
  | Xung đột ghi | không có | có, phải giải quyết | có, phải giải quyết |
  | Ví dụ | MySQL/Postgres primary–replica, Kafka partition | MySQL multi-source, CouchDB, hệ multi-region | Cassandra, DynamoDB (kiểu Dynamo), Riak |
  | Điểm yếu | leader là nút cổ chai ghi, failover phức tạp | giải quyết xung đột | tính nhất quán khó hiểu |

  - Đồng bộ vs bất đồng bộ: sync thì không mất dữ liệu khi failover nhưng ghi chậm và phụ
    thuộc replica; async thì nhanh nhưng failover có thể **mất ghi đã xác nhận** ⚠️. Semi-sync:
    chờ ít nhất một replica
  - Replication lag gây: read-after-write sai, đọc lùi thời gian, và quyết định sai nếu đọc
    replica rồi ghi primary (kiểm tra tồn kho trên replica)
- [ ] 🟡 Leaderless và quorum
  - N replica, ghi thành công khi W node xác nhận, đọc hỏi R node và lấy bản mới nhất.
    `R + W > N` thì tập đọc và tập ghi giao nhau ít nhất một node
  - Ví dụ `N=3, W=2, R=2`: chịu được một node chết cho cả đọc và ghi
  - Sửa dữ liệu lệch: read repair (đọc thấy bản cũ thì ghi đè), anti-entropy (so sánh nền,
    Merkle tree)
  - ⚠️ `R + W > N` không đảm bảo linearizable: ghi đồng thời, ghi thất bại một phần không
    rollback, sloppy quorum/hinted handoff, đồng hồ lệch với LWW
- [ ] 🔴 Conflict resolution
  - **LWW (last write wins)**: giữ bản có timestamp lớn nhất. Đơn giản nhưng **âm thầm mất
    dữ liệu** khi hai ghi đồng thời, và phụ thuộc đồng hồ ⚠️
  - **Vector clock / version vector** (đại ý): mỗi replica một bộ đếm; so sánh hai vector cho
    biết một bản "xảy ra trước" bản kia hay hai bản **đồng thời**. Đồng thời thì giữ cả hai
    (siblings) cho ứng dụng gộp
  - **CRDT** (đại ý): kiểu dữ liệu được thiết kế để gộp luôn hội tụ, không cần điều phối
    (G-Counter, PN-Counter, OR-Set, LWW-Register). Dùng cho collaborative editing, bộ đếm
    phân tán, giỏ hàng. Giới hạn: không biểu diễn được ràng buộc toàn cục như "số dư không âm"
  - Cách thực dụng: tránh xung đột bằng cách định tuyến mọi ghi của một entity về một leader
    (mỗi user một "home region")

### Partitioning

- [ ] 🟡 Range vs hash

  | | Range | Hash |
  |---|---|---|
  | Chia theo | khoảng giá trị key (`A–F`, `G–M`) | `hash(key)` |
  | Range query | nhanh, cùng partition | phải hỏi mọi partition |
  | Hot spot | dễ: key tăng dần (timestamp) dồn vào partition cuối | phân tán đều hơn |
  | Ví dụ | HBase, Bigtable, TiKV | Cassandra, DynamoDB, Redis Cluster (hash slot) |

  - ⚠️ `hash(key) % N` đổi N là **gần như mọi key đổi chỗ**
  - Hot spot vẫn xảy ra với hash nếu một key quá nóng (người nổi tiếng); giải bằng tách key
    (thêm hậu tố ngẫu nhiên khi ghi, gộp khi đọc), cache riêng cho key nóng
  - Secondary index trên dữ liệu partitioned: local index (query phải scatter-gather) hoặc
    global index (ghi phải cập nhật partition khác, thường bất đồng bộ)
- [ ] 🔴 Consistent hashing: vì sao thêm hoặc bớt node chỉ di chuyển một phần nhỏ dữ liệu
  - Đặt node và key lên cùng một vòng hash; key thuộc về node đầu tiên theo chiều kim đồng hồ.
    Thêm node chỉ lấy key từ node kế bên, trung bình khoảng `1/N` dữ liệu di chuyển

    ```text
            node A
          /        \
     key k1         node B      thêm node D giữa A và B:
         |            |         chỉ các key nằm giữa A và D chuyển từ B sang D
       node C ---- key k2
    ```
  - **Virtual node**: mỗi node vật lý có nhiều điểm trên vòng. Phân bố đều hơn; node chết thì
    tải chia cho nhiều node thay vì dồn cho một node kế bên; node mạnh có nhiều vnode hơn
  - Biến thể: rendezvous hashing, jump hash. Redis Cluster dùng 16384 hash slot cố định (cách
    khác: số partition cố định, chỉ di chuyển partition giữa node)
- [ ] 🟡 Rebalancing
  - Chiến lược: số partition cố định lớn hơn số node (Kafka, Elasticsearch shard, Redis slot);
    partition tự tách khi to (range-based); theo số node
  - ⚠️ Rebalance tự động có thể gây sự cố dây chuyền: node chậm bị tưởng là chết, dữ liệu dồn
    sang node khác làm node đó quá tải. Nhiều hệ thống để con người xác nhận

### Consensus

- [ ] 🔴 Consensus: nhiều node đồng ý về một giá trị (hoặc một chuỗi log) dù có node chết.
      Dùng cho leader election, lưu cấu hình, lock, metadata cluster
- [ ] 🔴 Raft ở mức giải thích được
  - Mỗi node là follower, candidate hoặc leader. Thời gian chia thành **term** đánh số tăng dần;
    mỗi term có tối đa một leader
  - **Leader election**: follower không nhận heartbeat trong election timeout (ngẫu nhiên để
    tránh bầu đồng thời) thì tăng term, thành candidate, xin phiếu. Mỗi node bầu tối đa một
    phiếu mỗi term, và chỉ bầu cho candidate có log **ít nhất mới bằng** mình. Được đa số thì
    thành leader
  - **Log replication**: client gửi lệnh cho leader, leader append vào log, gửi
    `AppendEntries` cho follower. Entry được **commit** khi đa số đã ghi; sau đó mới áp dụng vào
    state machine và trả lời client
  - Node nhận message với term cao hơn thì lùi về follower; leader cũ bị cô lập không commit
    được gì vì không có đa số
  - **Quorum**: cluster `2f + 1` node chịu được `f` node chết. 3 node chịu 1, 5 node chịu 2.
    ⚠️ 4 node vẫn chỉ chịu được 1 (cần 3 phiếu), nên số node chẵn không có lợi
  - Đánh đổi: mỗi ghi cần round-trip tới đa số → độ trễ; không hợp dữ liệu khối lượng lớn,
    chỉ hợp metadata
  - Paxos là thuật toán cùng mục đích, ra đời trước, khó hiểu hơn; Raft được thiết kế để dễ hiểu
- [ ] 🔴 Split brain: hai node cùng nghĩ mình là leader (mạng bị tách, failover tự động dựa
      trên heartbeat). Cả hai nhận ghi → dữ liệu phân kỳ
  - Chống: quorum (phía thiểu số không được làm leader), fencing (tước quyền leader cũ: STONITH,
    fencing token), witness/tiebreaker node
  - ⚠️ Hai data center với mỗi bên một nửa node không bầu được leader khi mất kết nối; cần node
    thứ ba ở vị trí khác
- [ ] 🔴 etcd, ZooKeeper dùng để làm gì
  - Lưu cấu hình và metadata cần nhất quán mạnh (Kubernetes lưu toàn bộ state trong etcd)
  - Leader election, distributed lock (etcd lease, ZooKeeper ephemeral sequential node),
    service discovery, membership
  - Không dùng làm DB ứng dụng: dung lượng nhỏ, ghi đắt

### Thời gian

- [ ] 🔴 Đồng hồ trong hệ phân tán: clock skew, logical clock, vì sao không dựa vào
      timestamp của nhiều máy để sắp thứ tự
  - **Clock skew**: đồng hồ các máy lệch nhau (mili giây tới giây). **NTP** đồng bộ nhưng
    không hoàn hảo, và có thể làm đồng hồ **nhảy lùi**
  - Wall clock (`System.currentTimeMillis`, `time.Now()`) có thể nhảy; đo khoảng thời gian
    phải dùng **monotonic clock** (`System.nanoTime`, Go `time.Now()` có kèm monotonic reading)
  - ⚠️ Máy A ghi lúc 10:00:00.100, máy B ghi sau đó nhưng đồng hồ B chậm 200 ms nên ghi
    10:00:00.000. Sắp theo timestamp thì B "trước" A; LWW sẽ giữ bản sai
  - **Lamport clock**: mỗi node một bộ đếm, tăng mỗi sự kiện, gửi kèm message, nhận thì lấy
    `max(local, received) + 1`. Đảm bảo: A xảy ra trước B thì `L(A) < L(B)`. **Không** đúng
    chiều ngược lại: không phân biệt được "trước" và "đồng thời"
  - **Vector clock**: mỗi node giữ một vector bộ đếm cho mọi node. Phân biệt được nhân quả và
    đồng thời, đổi lại kích thước tăng theo số node
  - 🔴 Google Spanner dùng TrueTime (đồng hồ có khoảng sai số đã biết, dựa trên GPS và đồng hồ
    nguyên tử) và chờ hết khoảng bất định khi commit; hybrid logical clock (HLC) được dùng ở
    CockroachDB
  - Thực dụng: thứ tự trong một entity thì dùng version/sequence do một nơi sinh ra (DB, leader
    partition), không dùng timestamp của nhiều máy

### Distributed transaction

- [ ] 🟡 2PC (two-phase commit)
  - Pha 1 (prepare): coordinator hỏi mọi participant "sẵn sàng commit không?". Participant ghi
    log, giữ khoá, trả "yes/no"
  - Pha 2 (commit/abort): tất cả yes thì commit, một no thì abort
  - **Vì sao blocking**: participant đã trả "yes" thì phải chờ quyết định, **không được tự ý**
    commit hay abort. Coordinator chết lúc đó thì participant giữ khoá vô thời hạn tới khi
    coordinator phục hồi
  - Nhược khác: độ trễ nhiều round-trip, mọi bên phải hỗ trợ giao thức (XA), availability bằng
    tích availability các bên. Ít dùng giữa microservice; vẫn dùng bên trong DB phân tán
- [ ] 🔴 3PC (đại ý): thêm pha pre-commit để participant tự quyết được khi coordinator chết.
      Chỉ đúng với giả định độ trễ mạng có giới hạn; khi có network partition vẫn có thể không
      nhất quán, nên hầu như không dùng trong thực tế
- [ ] 🟡 Saga
  - Chuỗi **transaction cục bộ**, mỗi bước commit ngay; bước sau thất bại thì chạy
    **compensating action** cho các bước trước theo thứ tự ngược
  - Ví dụ đặt vé: `reserve_seat` → `charge_payment` → `add_points`. `charge_payment` lỗi thì
    `release_seat`
  - **Orchestration**: một orchestrator ra lệnh từng bước, giữ trạng thái saga. **Choreography**:
    mỗi service nghe event và làm bước tiếp theo. So sánh ở [12-messaging.md](12-messaging.md)
  - Compensating action là **nghiệp vụ**, không phải rollback: hoàn tiền không xoá được việc đã
    trừ tiền; email đã gửi không thu hồi được (gửi email xin lỗi)
  - ⚠️ **Không có isolation**: giữa các bước, service khác thấy trạng thái trung gian (ghế đã
    giữ nhưng chưa trả tiền). Giảm thiểu: trạng thái pending tường minh (semantic lock), sắp
    bước dễ thất bại lên trước, bước không thể bù (pivot) đặt cuối
  - ⚠️ Compensation cũng có thể thất bại → phải retry tới khi thành công, nên phải idempotent
  - Mỗi bước gửi message nên dùng outbox để không mất bước
  - Workflow engine (Temporal) giảm nhiều công sức cho saga orchestration
- [ ] 🟡 Outbox: ghi dữ liệu và event trong cùng transaction cục bộ. Chi tiết ở
      [12-messaging.md](12-messaging.md)
- [ ] 🔴 TCC (Try–Confirm–Cancel)
  - Try: giữ tài nguyên (đóng băng tiền, giữ chỗ) nhưng chưa dùng. Confirm: dùng thật. Cancel:
    nhả chỗ đã giữ
  - Khác saga: có bước giữ chỗ nên isolation tốt hơn; mỗi service phải cài ba API, cần xử lý
    Cancel đến trước Try (do mạng), Confirm/Cancel gọi nhiều lần (idempotent), và giữ chỗ quá
    hạn tự nhả

### Distributed lock

- [ ] 🟡 Redis `SET NX PX` và giải phóng lock bằng Lua script (kiểm tra đúng chủ lock rồi mới xoá)

  ```bash
  SET lock:order:42 <random_token> NX PX 30000     # chỉ đặt nếu chưa có, hết hạn 30 giây
  ```
  ```lua
  -- release: chỉ xoá nếu đúng token của mình
  if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
  else
    return 0
  end
  ```
  - Vì sao token ngẫu nhiên + Lua: `GET` rồi `DEL` riêng thì giữa hai lệnh lock có thể đã hết hạn
    và thuộc về người khác, ta xoá mất lock của họ
  - Vì sao phải có TTL: process giữ lock chết thì lock tự nhả
- [ ] 🟡 Lease: lock có thời hạn, người giữ phải gia hạn (renew) định kỳ khi còn làm. Redisson có
      watchdog tự gia hạn; etcd có lease với keepalive
- [ ] ⚠️ Lock hết hạn trong khi việc chưa xong; GC pause
  - Process A lấy lock, bị GC pause (hoặc VM bị tạm dừng, mạng chậm) 40 giây. Lock hết hạn,
    B lấy lock. A tỉnh dậy, **vẫn nghĩ mình giữ lock**, ghi đè lên việc của B
  - Kiểm tra "còn giữ lock không" trước khi ghi không giải quyết được: pause có thể xảy ra
    ngay sau khi kiểm tra
- [ ] 🔴 Fencing token
  - Mỗi lần cấp lock kèm một số tăng dần (33, 34...). Mọi ghi xuống storage kèm token; storage
    **từ chối** token nhỏ hơn token lớn nhất đã thấy
  - A (token 33) tỉnh dậy ghi, storage đã thấy 34 của B → từ chối
  - Đòi hỏi storage tham gia kiểm tra (ví dụ `UPDATE ... WHERE last_token < ?`). Redis `SET NX`
    đơn thuần không sinh token tăng dần; etcd (revision) và ZooKeeper (zxid, sequential node) có
- [ ] 🔴 Tranh luận về Redlock
  - Redlock: lấy lock trên đa số trong N (thường 5) Redis master độc lập, trong thời gian nhỏ
    hơn TTL
  - Martin Kleppmann (2016) phản biện: dựa vào giả định về thời gian (clock, pause, độ trễ mạng)
    nên không an toàn cho mục đích **đúng đắn**; không có fencing token. Antirez phản hồi, cho
    rằng các giả định là hợp lý trong thực tế
  - Kết luận thực dụng: phân biệt lock cho **hiệu quả** (tránh làm hai lần việc tốn kém, trùng
    đôi khi chấp nhận được) thì một Redis `SET NX` là đủ; lock cho **đúng đắn** (trùng là sai
    dữ liệu) thì cần consensus (etcd/ZooKeeper) + fencing, hoặc tốt hơn là đẩy ràng buộc xuống DB
- [ ] 🟡 Lock bằng DB, etcd, ZooKeeper
  - DB: `SELECT ... FOR UPDATE` trên dòng lock, advisory lock của Postgres
    (`pg_advisory_lock`), MySQL `GET_LOCK()`. Không thêm hạ tầng, gắn với transaction; ⚠️
    advisory lock theo session dễ rò khi dùng connection pool
  - etcd: lease + revision làm fencing token. ZooKeeper: ephemeral sequential node, node tự mất
    khi session chết, người có số nhỏ nhất giữ lock, người kế tiếp chỉ watch node ngay trước
    (tránh herd effect)

### Resilience

- [ ] **Timeout**: mọi lời gọi ra ngoài phải có timeout (connect timeout và read timeout)
  - ⚠️ Nhiều client HTTP mặc định không có timeout hoặc timeout rất dài → một dependency treo
    làm cạn thread pool
  - Chọn theo p99/p99.9 của dependency, không phải theo cảm giác. **Deadline propagation**:
    truyền thời gian còn lại xuống các lời gọi con (gRPC deadline, `context` trong Go); không
    để service con chạy tiếp khi service cha đã bỏ cuộc
- [ ] Retry có exponential backoff + jitter; ⚠️ retry dồn dập làm sập hệ thống đang yếu
      (retry storm)
  - Chỉ retry lỗi tạm thời (timeout, 503, 429 theo `Retry-After`) và thao tác **idempotent**
  - Backoff: `base × 2^attempt`, có trần. **Jitter** (ngẫu nhiên hoá, ví dụ full jitter
    `random(0, backoff)`) để các client không retry cùng lúc
  - ⚠️ Retry ở nhiều tầng nhân lên: 3 tầng, mỗi tầng 3 lần = 27 request xuống tầng cuối
    cho một request gốc. Chỉ retry ở một tầng (thường gần client nhất hoặc tại chỗ gọi)
- [ ] 🔴 Retry budget: giới hạn retry theo tỉ lệ (ví dụ retry không vượt quá 10% tổng request
      thành công gần đây), thay vì theo số lần mỗi request. Khi dependency chết hẳn, retry tự
      tắt thay vì nhân ba tải
- [ ] Idempotency: điều kiện để retry an toàn. Idempotency key, upsert, unique constraint.
      Xem [09-api-design.md](09-api-design.md) và [13-concurrency.md](13-concurrency.md)
- [ ] 🟡 Circuit breaker: trạng thái closed, open, half-open

  ```text
  CLOSED ──(tỉ lệ lỗi vượt ngưỡng trong cửa sổ)──► OPEN ──(hết thời gian chờ)──► HALF-OPEN
    ▲                                                                              │
    └──────────────(vài request thử thành công)──────── ◄──(thử thất bại)── về OPEN ┘
  ```
  - Closed: gọi bình thường, đếm lỗi. Open: **fail fast** không gọi, trả fallback. Half-open:
    cho vài request thử, thành công thì đóng lại
  - Lợi: bảo vệ dependency đang yếu có thời gian hồi phục, bảo vệ chính mình khỏi chờ timeout
  - ⚠️ Cấu hình sai: cửa sổ quá nhỏ thì bật tắt liên tục; tính cả lỗi 4xx của client làm
    breaker mở oan. Breaker theo từng dependency (và có thể theo từng endpoint)
  - Thư viện: Resilience4j (Java), `sony/gobreaker` (Go); service mesh (Envoy outlier detection)
- [ ] 🟡 Bulkhead: tách tài nguyên (thread pool, connection pool, instance) theo dependency hoặc
      theo loại khách hàng để một phần hỏng không kéo chìm cả tàu. Ví dụ pool riêng cho API
      thanh toán và API gợi ý sản phẩm
- [ ] 🟡 Rate limiting: token bucket, leaky bucket, fixed/sliding window; theo user, IP, API key;
      ở gateway và ở từng service. Chi tiết ở [09-api-design.md](09-api-design.md)
- [ ] 🟡 Load shedding: server quá tải thì **chủ động từ chối** sớm (503) thay vì nhận hết rồi
      chậm tất cả. Ưu tiên theo loại request (thanh toán hơn gợi ý), bỏ request đã chờ trong
      queue quá deadline (client đã bỏ đi rồi)
- [ ] 🟡 Graceful degradation, fallback
  - Tắt tính năng phụ để giữ tính năng chính: trang sản phẩm vẫn hiện khi service review chết
  - Fallback: cache cũ (stale), giá trị mặc định, danh sách phổ biến thay vì cá nhân hoá
  - ⚠️ Fallback ít được chạy nên hay có bug; phải test (chaos testing). Fallback không được gọi
    vào chính dependency đang lỗi
  - Feature flag / kill switch để tắt nhanh
- [ ] 🔴 Hedged requests: gửi request tới một replica, nếu quá p95 chưa có trả lời thì gửi thêm
      tới replica khác, lấy cái về trước, hủy cái còn lại. Cắt tail latency với chi phí thêm vài
      phần trăm tải ("The Tail at Scale", Dean & Barroso). ⚠️ Chỉ cho request idempotent, và
      phải có giới hạn để không nhân đôi tải khi hệ thống chậm toàn bộ
- [ ] 🟡 Cascading failure: một service chậm → service gọi nó giữ thread chờ → cạn thread pool →
      service đó cũng chậm → lan lên trên. Chặn bằng timeout, circuit breaker, bulkhead, load
      shedding
- [ ] 🟡 Retry storm: dependency chậm, mọi client retry cùng lúc làm tải tăng gấp bội, không
      hồi phục được. Chặn bằng backoff + jitter, retry budget, circuit breaker
- [ ] 🔴 Metastable failure: hệ thống bị kích hoạt vào trạng thái xấu (do một sự cố ngắn: deploy,
      cache bị xoá, đỉnh tải) và **tự duy trì trạng thái xấu** ngay cả khi nguyên nhân ban đầu
      đã hết, vì có vòng phản hồi (retry, cache miss dồn DB, timeout làm việc bị làm lại). Hồi
      phục thường cần giảm tải mạnh chủ động (chặn traffic, tắt retry). Ví dụ: cache cluster
      restart, mọi request dồn DB, DB chậm, request timeout rồi retry, cache không bao giờ ấm lại

### Hạ tầng phân tán

- [ ] 🟡 Sinh ID phân tán

  | Loại | Cấu trúc | Sắp theo thời gian | Ghi chú |
  |---|---|---|---|
  | Auto-increment DB | một bộ đếm | có | đơn giản; một điểm sinh; lộ số lượng; khó khi sharding |
  | UUID v4 | 122 bit ngẫu nhiên | không | ⚠️ làm primary key B-tree bị chèn ngẫu nhiên → page split, index phân mảnh |
  | UUID v7 | 48 bit Unix timestamp ms + ngẫu nhiên (RFC 9562) | có | thay thế tốt cho v4 làm primary key |
  | ULID | 48 bit timestamp ms + 80 bit ngẫu nhiên, Crockford base32, 26 ký tự | có | tương tự v7, dạng chuỗi đọc được |
  | Snowflake | 1 bit dấu + 41 bit timestamp ms (từ một epoch riêng) + 10 bit machine id + 12 bit sequence | có | 64 bit, vừa `BIGINT`; 4096 ID/ms/máy |
  | DB segment (Leaf của Meituan) | mỗi service xin một dải `[1000, 2000)` từ DB, cấp trong bộ nhớ | gần đúng | ít gọi DB; ⚠️ restart thì mất phần còn lại của dải (thủng số) |

  - Snowflake: 41 bit timestamp dùng được khoảng 69 năm từ epoch. ⚠️ Đồng hồ nhảy lùi có thể
    sinh ID trùng: phải phát hiện và chờ hoặc báo lỗi. Machine id phải được cấp không trùng
    (config, ZooKeeper, pod ordinal)
  - ⚠️ ID sắp theo thời gian lộ thời điểm tạo; ID tuần tự lộ số lượng và cho phép đoán ID
    (enumeration). ID công khai nên khó đoán, và **không thay** cho kiểm tra quyền
  - ⚠️ ID tuần tự trên hệ thống hash partition có thể tạo hot partition nếu partition theo range
- [ ] 🟡 Service discovery
  - Client-side: client hỏi registry (Consul, Eureka) rồi tự chọn instance và cân bằng tải.
    Server-side: client gọi load balancer/DNS, LB biết instance
  - Kubernetes: Service + DNS nội bộ, kube-proxy; service mesh (Istio/Linkerd) làm ở sidecar
  - ⚠️ DNS cache ở client (JVM từng cache DNS rất lâu) làm gọi tới IP cũ sau khi instance đổi
- [ ] 🟡 Health check
  - **Liveness**: process còn sống không, không thì restart. **Readiness**: sẵn sàng nhận
    traffic không, không thì bỏ khỏi load balancer (đang khởi động, đang drain)
  - ⚠️ Liveness kiểm tra cả DB: DB chậm → mọi pod bị restart cùng lúc → sự cố tệ hơn. Liveness
    chỉ nên kiểm tra chính process; readiness mới xét dependency, và cũng phải cẩn thận
  - Graceful shutdown: nhận SIGTERM → readiness fail → chờ LB rút → xử lý nốt request → thoát
- [ ] 🔴 Leader election: chọn một instance làm việc chỉ được một bên làm (scheduler, consumer
      đơn). Qua etcd/ZooKeeper, Kubernetes Lease, hoặc DB lock. Leader phải chịu được việc
      **mất quyền mà không biết** (dùng lease + fencing như lock)
- [ ] 🔴 Gossip (đại ý): mỗi node định kỳ trao đổi thông tin với vài node ngẫu nhiên, thông tin
      lan ra cả cluster trong khoảng `O(log N)` vòng. Dùng cho membership và phát hiện lỗi
      (SWIM protocol; Consul/Serf, Cassandra, Redis Cluster). Chịu lỗi tốt, không có điểm tập
      trung; đổi lại chỉ eventual
- [ ] 🔴 Membership: biết node nào đang trong cluster, node nào chết. Failure detector không bao
      giờ chắc chắn (chết hay chậm?), phải đánh đổi giữa phát hiện nhanh và báo nhầm
- [ ] 🔴 Exactly-once thật sự là gì
  - Không thể đảm bảo **giao** message đúng một lần qua mạng không tin cậy. Cái làm được là
    **hiệu ứng** đúng một lần: at-least-once delivery + xử lý idempotent (hoặc dedup) =
    effectively-once
  - Kafka EOS là exactly-once trong phạm vi Kafka (đọc, xử lý, ghi Kafka, commit offset atomic).
    Xem [12-messaging.md](12-messaging.md)
  - **End-to-end argument** (Saltzer, Reed, Clark): tính đúng đắn chỉ đảm bảo được ở hai đầu cuối
    của ứng dụng; các tầng giữa (TCP, broker) chỉ giúp tối ưu. TCP đảm bảo không trùng trong một
    connection, nhưng connection đứt và client gửi lại thì server vẫn nhận trùng. Vì vậy
    idempotency key phải đi từ client tới DB cuối cùng

## Senior trả lời khác gì

- **"Giải thích CAP."**
  - Mid: "Chọn 2 trong 3: consistency, availability, partition tolerance. MongoDB là CP,
    Cassandra là AP."
  - Senior: "Partition không phải lựa chọn. Khi mạng bị chia, node bị tách phải hoặc từ chối
    (giữ linearizability) hoặc trả dữ liệu có thể cũ. Lúc bình thường, đánh đổi thực tế là
    latency vs consistency (PACELC), và nhiều hệ thống cho chỉnh theo từng thao tác."
- **"Service A gọi B bị timeout, làm gì?"**
  - Mid: "Retry 3 lần."
  - Senior: "Timeout không có nghĩa là thất bại. Chỉ retry nếu thao tác idempotent hoặc có
    idempotency key; backoff + jitter, retry ở một tầng; có circuit breaker; với thao tác tiền
    thì tra trạng thái trước và có đối soát."
- **"Dùng Redis lock cho việc trừ tiền được không?"**
  - Mid: "Được, `SET NX` rồi `DEL`."
  - Senior: phân biệt lock cho hiệu quả và cho đúng đắn; nêu GC pause và lock hết hạn, fencing
    token; kết luận tính đúng phải nằm ở DB (atomic update, constraint), lock chỉ là tối ưu.
- **"Làm sao đảm bảo nhất quán giữa 3 service đặt vé, thanh toán, điểm thưởng?"**
  - Mid: "Dùng distributed transaction."
  - Senior: giải thích vì sao 2PC không hợp giữa microservice, đề xuất saga orchestration với
    outbox, nêu compensating action cho từng bước, bước pivot, cách xử lý thiếu isolation, và
    đối soát định kỳ làm lưới an toàn.
- **"Chọn UUID hay auto-increment?"**
  - Mid: "UUID vì unique toàn cục."
  - Senior: nêu ảnh hưởng của UUID v4 lên B-tree index, đề xuất UUID v7/ULID/Snowflake, cân
    nhắc lộ số lượng và tính khó đoán, dung lượng index (16 byte vs 8 byte).

## Tình huống

1. *Service A gọi service B bị timeout. B có thể đã xử lý hoặc chưa. Bạn xử lý thế nào?*
   - Gợi ý: idempotency key cho request; retry có backoff chỉ khi B hỗ trợ idempotency; API tra
     trạng thái; đối soát định kỳ; nếu là thao tác không idempotent thì không retry mù.
2. *Đặt vé máy bay, trừ tiền và cộng điểm thưởng nằm ở ba service khác nhau. Làm sao đảm bảo
   tính nhất quán?*
   - Gợi ý: saga orchestration; thứ tự: giữ chỗ (bù: nhả chỗ) → trừ tiền (pivot) → cộng điểm
     (retry tới khi thành công); outbox cho mỗi bước; trạng thái pending hiển thị cho user.
3. *Sau failover MySQL, vài đơn hàng khách đã nhận được xác nhận biến mất.*
   - Gợi ý: replication bất đồng bộ, primary cũ chết trước khi replica nhận binlog. Semi-sync,
     đo replication lag, quy trình failover có kiểm tra lag, và đối soát với log cổng thanh toán.
4. *Service gợi ý sản phẩm chậm làm trang chủ timeout toàn bộ.*
   - Gợi ý: cascading failure. Timeout ngắn cho service phụ, circuit breaker, fallback danh sách
     phổ biến từ cache, bulkhead tách pool, gọi song song và không chặn phần chính.
5. *Sau khi xoá cache toàn cụm để sửa dữ liệu sai, DB quá tải và hệ thống không hồi phục dù
   traffic bình thường.*
   - Gợi ý: metastable failure + cache stampede. Tạm chặn bớt traffic hoặc tắt retry, làm ấm
     cache dần, request coalescing, không xoá cache toàn bộ cùng lúc. Xem [11-cache.md](11-cache.md).
6. *Job đồng bộ chạy trên 3 pod với Redis lock; log cho thấy đôi khi hai pod cùng chạy.*
   - Gợi ý: TTL ngắn hơn thời gian chạy, GC pause, Redis failover mất key (replication bất đồng
     bộ). Gia hạn lease, fencing token ở chỗ ghi, và làm job idempotent.
7. *Sắp xếp log từ 20 máy theo timestamp để điều tra sự cố, thấy response xuất hiện trước request.*
   - Gợi ý: clock skew. Dùng trace id và span cha–con (distributed tracing) để lấy quan hệ nhân
     quả, không dựa vào timestamp giữa các máy.

## ❓ Câu hỏi hay gặp

🟢
- Kể vài giả định sai về hệ phân tán và bug tương ứng.
- Vì sao mọi lời gọi mạng cần timeout?
- Retry với exponential backoff là gì? Vì sao cần jitter?

🟡
- Giải thích CAP theorem bằng một ví dụ thực tế.
- PACELC bổ sung gì cho CAP?
- Eventual consistency và read-your-writes khác nhau thế nào? Làm sao đạt read-your-writes
  khi đọc từ replica?
- Circuit breaker hoạt động thế nào?
- 2PC là gì, vì sao ít dùng giữa microservice?
- Saga là gì? Orchestration và choreography khác nhau thế nào?
- Làm distributed lock bằng Redis thế nào cho đúng?
- Snowflake ID gồm những phần nào? UUID v4 làm primary key có vấn đề gì?
- Liveness và readiness probe khác nhau thế nào?

🔴
- Raft bầu leader và replicate log thế nào? Vì sao cluster nên có số node lẻ?
- Split brain là gì, chống thế nào?
- Fencing token là gì? Vì sao Redlock bị tranh cãi?
- Vì sao không dùng timestamp để sắp thứ tự sự kiện giữa nhiều máy? Lamport clock giải
  quyết được gì và không giải quyết được gì?
- `R + W > N` có đảm bảo đọc luôn thấy ghi mới nhất không?
- Consistent hashing và virtual node giải quyết vấn đề gì?
- Exactly-once có tồn tại không? End-to-end argument nói gì?
- Metastable failure là gì? Cho ví dụ.

## Bài tập tự làm

1. Vẽ sơ đồ trạng thái saga "đặt phòng khách sạn + thanh toán + gửi voucher", liệt kê
   compensating action, bước pivot, và điều gì xảy ra nếu compensation thất bại.
2. Viết pseudo-code cho một HTTP client wrapper có: timeout, retry với full jitter, chỉ retry
   lỗi tạm thời, retry budget, và circuit breaker.
3. Với cluster Cassandra `N=3`, liệt kê các cặp (R, W) và nói với mỗi cặp: chịu được bao nhiêu
   node chết khi đọc, khi ghi, và có `R + W > N` không.
4. Thiết kế bộ sinh ID kiểu Snowflake cho 1.000 pod Kubernetes: cấp machine id thế nào, xử lý
   đồng hồ nhảy lùi thế nào, và chọn epoch ra sao.
5. Mô tả một sự cố cascading failure bạn từng gặp (hoặc tưởng tượng), vẽ chuỗi lan truyền, và
   chỉ ra pattern nào ở mục Resilience sẽ chặn được ở bước nào.

> Nộp bài vào đây để được review.
