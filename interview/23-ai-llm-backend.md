# 23. Tích hợp AI/LLM vào backend

> [← Mục lục](README.md) · Phạm vi: gọi LLM API từ backend, structured output và tool calling, RAG và vector search, agent/workflow, bảo mật, vận hành và đánh giá chất lượng.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

Chủ đề này xuất hiện ngày càng nhiều trong JD backend. **Phần lớn chỉ bị hỏi khi JD có nhắc
AI/LLM**; nếu không, nắm mục "Gọi LLM API" và "Bảo mật" là đủ. Người phỏng vấn backend không
hỏi cách train model; họ hỏi cách đưa một dependency **chậm, đắt, không tất định, và có thể
bị thao túng qua input** vào hệ thống production mà vẫn an toàn.

Tên model, giá, giới hạn context, rate limit của từng provider thay đổi rất nhanh nên không
ghi ở đây. Khi trả lời phỏng vấn, nói ở mức nguyên lý và nói "tôi sẽ kiểm tra tài liệu hiện
hành của provider".

## Bản đồ nhanh

**Gọi LLM API**
- [ ] 🟡 LLM là dependency ngoài: chậm, đắt, không tất định, có thể lỗi
- [ ] 🟡 Streaming qua SSE; cấu hình proxy không buffer
- [ ] 🟡 Timeout dài, không block request thread; async job cho tác vụ dài
- [ ] 🟡 Retry có backoff, lỗi nào retry được; rate limit/quota
- [ ] 🟡 Chi phí theo token (input, output); giới hạn và theo dõi chi phí
- [ ] 🟡 Caching: prompt caching phía provider, cache kết quả phía mình
- [ ] 🟡 Chọn model theo chi phí/độ trễ/chất lượng; routing
- [ ] 🟡 Fallback khi provider lỗi; lớp gateway/adapter

**Output có cấu trúc**
- [ ] 🟡 Structured output (JSON theo schema)
- [ ] 🟡 Tool calling / function calling ở mức khái niệm
- [ ] ⚠️ Không tin output LLM: validate như input từ user

**RAG**
- [ ] 🟡 Luồng RAG: ingest → chunk → embed → index → retrieve → generate
- [ ] 🟡 Chunking: kích thước, overlap, theo cấu trúc tài liệu
- [ ] 🟡 Embedding và độ đo tương đồng (cosine, dot product, L2)
- [ ] 🟡 Vector search: pgvector, vector DB; 🔴 ANN, HNSW, IVF đại ý
- [ ] 🟡 Hybrid search (BM25 + vector), 🔴 rerank
- [ ] 🟡 Cập nhật index khi dữ liệu đổi; đổi model embedding thì phải embed lại
- [ ] 🔴 Đánh giá chất lượng retrieval và câu trả lời

**Agent/workflow**
- [ ] 🟡 Vòng lặp tool: model gọi tool, backend thực thi, trả kết quả
- [ ] 🟡 Workflow cố định vs agent tự quyết
- [ ] ⚠️ Giới hạn số bước, thời gian, chi phí
- [ ] 🟡 Human-in-the-loop cho hành động có hậu quả
- [ ] ⚠️ Idempotency của tool có side effect

**Bảo mật**
- [ ] ⚠️ Prompt injection trực tiếp và gián tiếp
- [ ] ⚠️ Rò rỉ dữ liệu, system prompt, dữ liệu của user khác
- [ ] ⚠️ PII gửi ra provider bên ngoài
- [ ] ⚠️ Phân quyền dữ liệu trong RAG
- [ ] ⚠️ Output LLM gây XSS/SQLi/command injection
- [ ] 🟡 Tool với quyền tối thiểu

**Vận hành**
- [ ] 🟡 Log/trace prompt và response; vấn đề PII và retention
- [ ] 🔴 Eval: offline test set, LLM-as-judge, regression khi đổi prompt/model
- [ ] 🟡 Theo dõi chất lượng, chi phí, latency (time to first token)
- [ ] 🟡 Version prompt như code

## Chi tiết

### Gọi LLM API từ backend

- [ ] 🟡 **Tư duy gốc**: LLM API là một dependency HTTP ngoài có bốn tính chất khó chịu
  - Chậm: vài giây đến hàng chục giây, tuỳ độ dài output
  - Đắt: tính tiền theo token input và output, output thường đắt hơn
  - Không tất định: cùng input có thể ra output khác
  - Bị điều khiển bởi dữ liệu: nội dung input có thể thay đổi hành vi (prompt injection)
  - Mọi kỹ thuật dưới đây là các pattern quen thuộc của backend (timeout, retry, circuit
    breaker, cache, queue, validate) áp vào bốn tính chất đó
- [ ] 🟡 **Streaming (SSE)**
  - Provider trả token dần; backend chuyển tiếp cho client qua Server-Sent Events
    (`Content-Type: text/event-stream`) hoặc WebSocket
  - Lợi: người dùng thấy chữ sau vài trăm ms thay vì chờ toàn bộ; metric quan trọng là
    **time to first token**
  - ⚠️ Reverse proxy buffer response thì stream thành một cục ở cuối. Nginx: tắt
    `proxy_buffering` cho route đó hoặc trả header `X-Accel-Buffering: no`; tăng
    `proxy_read_timeout`. Xem [02-networking.md](02-networking.md)
  - ⚠️ Client ngắt kết nối giữa chừng: phải huỷ request tới provider (context cancellation
    trong Go, abort stream) để không trả tiền cho token không ai đọc
  - ⚠️ Validate/lọc output khi đang stream khó hơn: nội dung đã gửi thì không rút lại được.
    Với output cần kiểm duyệt chặt, cân nhắc không stream hoặc stream sau khi kiểm từng đoạn
- [ ] 🟡 **Timeout và không block request thread**
  - Timeout phải dài hơn API thường nhưng vẫn phải có; tách connect timeout và tổng thời gian
  - PHP-FPM mỗi request chiếm một worker: nhiều request LLM chờ 30 giây là cạn pool, cả site
    đứng. Java thread-per-request tương tự (virtual thread giảm vấn đề này). Go goroutine rẻ
    hơn nhưng vẫn cần giới hạn số request đồng thời tới provider
  - Tác vụ dài (tóm tắt tài liệu, xử lý batch): đưa vào queue, trả `202 Accepted` + job id,
    client poll hoặc nhận webhook/SSE khi xong. Xem [12-messaging.md](12-messaging.md)
- [ ] 🟡 **Retry, rate limit, quota**
  - Retry được: timeout, 429, 5xx, provider quá tải. Không retry: 400 (request sai), lỗi vượt
    context, bị từ chối vì nội dung
  - Exponential backoff + jitter; tôn trọng header `Retry-After` nếu có
  - ⚠️ Retry request đắt nhân chi phí; đặt giới hạn số lần và ngân sách retry
  - Rate limit của provider tính theo request và theo token mỗi phút; nhiều service dùng
    chung một API key thì cần một lớp điều phối chung (token bucket tập trung, queue)
  - Phía mình: quota mỗi user/tenant để một user không đốt ngân sách của cả hệ thống. Xem
    [17-performance.md](17-performance.md)
- [ ] 🟡 **Chi phí**
  - Chi phí ≈ token input × đơn giá input + token output × đơn giá output
  - Giảm: prompt ngắn gọn, chỉ đưa context cần thiết (RAG lấy ít chunk mà đúng), giới hạn
    `max tokens` output, dùng model nhỏ cho việc dễ, batch API cho việc không gấp (nếu provider hỗ trợ)
  - Theo dõi: chi phí theo feature, theo tenant, theo ngày; cảnh báo khi vượt ngưỡng
  - ⚠️ Lịch sử hội thoại gửi lại mỗi lượt: hội thoại dài thì chi phí mỗi lượt tăng dần. Cắt
    bớt hoặc tóm tắt lịch sử
- [ ] 🟡 **Caching**
  - Prompt caching phía provider: phần đầu prompt giống nhau giữa các request (system prompt,
    tài liệu dài) được cache, giảm chi phí và latency. Đặt phần **cố định lên đầu**, phần thay
    đổi xuống cuối để tận dụng
  - Cache kết quả phía mình: key là hash của (model, prompt đã chuẩn hoá, tham số). Hợp với
    việc tất định hoặc gần tất định: phân loại, trích xuất, embedding của cùng một văn bản
  - ⚠️ Cache theo nghĩa (semantic cache: câu hỏi gần giống thì trả câu trả lời cũ) dễ trả sai
    ngữ cảnh; và ⚠️ cache không được trộn dữ liệu giữa user có quyền khác nhau
  - Chi tiết cache ở [11-cache.md](11-cache.md)
- [ ] 🟡 **Chọn model và routing**
  - Trục đánh đổi: chất lượng, latency, chi phí, độ dài context
  - Routing: việc đơn giản (phân loại, trích field) dùng model nhỏ; việc khó mới dùng model lớn.
    Có thể thử model nhỏ trước, không đạt tiêu chí thì chuyển lên
  - Quyết định dựa trên eval set của chính mình, không dựa trên benchmark chung
- [ ] 🟡 **Fallback và lớp adapter**
  - Bọc provider sau interface của mình (ví dụ `Completion`), giống bọc payment gateway. Đổi
    provider/model không phải sửa nghiệp vụ; test được bằng fake
  - Fallback: provider chính lỗi thì chuyển model/provider phụ, hoặc giảm chức năng (tắt
    tính năng AI, trả kết quả không AI). Circuit breaker để không dồn request vào provider đang chết
  - ⚠️ Prompt tối ưu cho model A chưa chắc tốt với model B; fallback phải được eval trước
  - Xem circuit breaker, graceful degradation ở [18-reliability-observability.md](18-reliability-observability.md)

### Structured output và tool calling

- [ ] 🟡 **Structured output**
  - Yêu cầu model trả JSON theo schema thay vì văn bản tự do; nhiều provider có chế độ ép
    output theo JSON schema
  - Dùng cho: trích xuất thông tin (hoá đơn, CV), phân loại, sinh tham số cho hệ thống khác
  - ⚠️ Dù có chế độ ép schema, vẫn parse và validate phía mình: kiểu, enum, khoảng giá trị,
    field bắt buộc, logic nghiệp vụ (tổng tiền có khớp các dòng không)
- [ ] 🟡 **Tool calling / function calling**
  - Backend khai báo danh sách tool (tên, mô tả, JSON schema tham số). Model **không tự chạy
    gì**; nó trả về "muốn gọi tool X với tham số Y". Backend quyết định có chạy không, chạy,
    rồi gửi kết quả lại cho model
  - Nghĩa là quyền thực thi nằm hoàn toàn ở backend: đây là chỗ kiểm quyền, validate, giới hạn
  - Mô tả tool rõ ràng quan trọng như tên hàm tốt: model chọn tool dựa vào mô tả
- [ ] ⚠️ **Không tin output LLM**
  - Coi output như input từ một user không tin cậy: validate, escape, kiểm quyền
  - Model có thể bịa (hallucinate) ID, URL, số liệu, tên hàm không tồn tại
  - Tham số tool do model sinh phải qua cùng lớp validation và authorization như request từ
    API công khai; user hiện tại không có quyền thì tool cũng không có quyền
  - Chuẩn bị cho output hỏng: JSON không parse được, thiếu field, bị cắt vì chạm giới hạn
    token. Có nhánh xử lý: retry có giới hạn, trả lỗi rõ ràng, hoặc fallback

### RAG (Retrieval-Augmented Generation)

- [ ] 🟡 **Luồng**

  ```
  Ingest:  tài liệu → làm sạch → chunk → embedding → lưu (vector + text + metadata, ACL)
  Query:   câu hỏi → (viết lại câu hỏi) → embedding → tìm top-K chunk (lọc theo quyền)
           → (rerank) → ghép vào prompt → LLM trả lời, kèm trích dẫn nguồn
  ```

  - Vì sao RAG thay vì nhồi hết vào prompt: context có giới hạn, chi phí theo token, dữ liệu
    thay đổi thường xuyên, cần trích dẫn nguồn và cần lọc theo quyền
  - Vì sao RAG thay vì fine-tune để thêm kiến thức: cập nhật dữ liệu chỉ cần re-index; xoá
    được dữ liệu; kiểm soát quyền theo từng tài liệu
- [ ] 🟡 **Chunking**
  - Chunk quá lớn: nhiều nhiễu, tốn token, embedding "loãng". Quá nhỏ: mất ngữ cảnh, câu trả
    lời thiếu
  - Chia theo cấu trúc (heading, đoạn, mục của hợp đồng, hàm trong code) tốt hơn cắt theo số
    ký tự; overlap một phần giữa các chunk để không cắt ngang ý
  - Gắn metadata: nguồn, tiêu đề mục, ngày cập nhật, tenant, ACL. Metadata dùng để lọc và trích dẫn
  - ⚠️ Bảng, PDF scan, tài liệu nhiều cột: khâu trích xuất text thường là nơi chất lượng hỏng
    đầu tiên
- [ ] 🟡 **Embedding**
  - Model embedding biến văn bản thành vector; văn bản gần nghĩa thì vector gần nhau
  - Độ đo: cosine similarity, dot product (bằng cosine nếu vector đã chuẩn hoá), L2
  - ⚠️ Vector của hai model embedding khác nhau không so sánh được. Đổi model thì phải embed
    lại toàn bộ; lưu tên/phiên bản model cạnh mỗi vector
  - ⚠️ Kiểm tra model embedding có hỗ trợ tốt tiếng Việt không trước khi chọn
- [ ] 🟡 **Vector search**
  - Tìm chính xác (so với mọi vector) là O(n·d); không chịu được khi n lớn. Nên dùng **ANN**
    (approximate nearest neighbor): nhanh hơn nhiều, đổi lại có thể bỏ sót vài kết quả gần nhất
  - 🔴 HNSW: đồ thị nhiều tầng, tìm bằng cách đi tham lam từ tầng thưa xuống tầng dày. Recall
    cao, query nhanh, tốn RAM, build chậm hơn. Có tham số đánh đổi recall lấy tốc độ
  - 🔴 IVF: chia vector thành cụm, chỉ tìm trong vài cụm gần nhất; nhẹ hơn, recall phụ thuộc
    số cụm được quét
  - Lựa chọn lưu trữ:
    - pgvector (extension PostgreSQL, có index HNSW và IVFFlat): dữ liệu và vector cùng một
      DB, join và lọc bằng SQL, transaction chung. Hợp khi quy mô vừa và đã dùng Postgres
    - Vector DB chuyên dụng hoặc search engine có vector: quy mô lớn, nhiều tính năng tìm kiếm;
      đổi lại thêm một hệ thống phải đồng bộ và vận hành
    - Xem [04-nosql-search-storage.md](04-nosql-search-storage.md)
  - ⚠️ Lọc metadata kết hợp ANN: lọc sau khi lấy top-K có thể còn quá ít kết quả; cần hệ thống
    hỗ trợ lọc trong lúc tìm, hoặc lấy K lớn hơn
- [ ] 🟡 **Hybrid search và rerank**
  - Vector search giỏi tìm theo nghĩa nhưng kém với mã sản phẩm, tên riêng, số hợp đồng, từ
    hiếm. BM25 (full-text) làm tốt việc đó
  - Hybrid: chạy cả hai rồi gộp thứ hạng, ví dụ Reciprocal Rank Fusion (RRF) cộng điểm theo
    thứ hạng thay vì theo điểm số thô (hai loại điểm không cùng thang)
  - 🔴 Rerank: lấy nhiều ứng viên (vài chục), dùng model rerank (cross-encoder) chấm lại độ
    liên quan với câu hỏi, giữ vài chunk tốt nhất. Chất lượng tốt hơn, thêm latency và chi phí
- [ ] 🟡 **Cập nhật index khi dữ liệu đổi**
  - Tài liệu thêm/sửa/xoá phải phản ánh vào index: dùng event (outbox, CDC) hoặc job đồng bộ
    định kỳ theo `updated_at`. Xem [12-messaging.md](12-messaging.md)
  - Sửa tài liệu thì xoá chunk cũ theo document id rồi thêm chunk mới; embed lại chỉ phần đổi
    nếu hash nội dung khác
  - ⚠️ Xoá tài liệu (hoặc user yêu cầu xoá dữ liệu cá nhân) mà quên xoá vector thì dữ liệu
    vẫn xuất hiện trong câu trả lời
  - ⚠️ Quyền đổi (user bị rút quyền, tài liệu chuyển sang private) cũng phải cập nhật metadata ACL
  - Re-index toàn bộ (đổi model embedding, đổi cách chunk): build index mới song song rồi
    chuyển đổi, như đổi alias trong search engine
- [ ] 🔴 **Đánh giá chất lượng RAG**
  - Tách hai tầng: retrieval (có lấy đúng chunk không: recall@K, MRR trên bộ câu hỏi có đáp án
    biết trước) và generation (câu trả lời có đúng, có bám nguồn, có bịa không)
  - Câu trả lời sai thường do retrieval sai, không phải do model; đo retrieval trước
  - Yêu cầu trích dẫn nguồn giúp user kiểm tra và giúp phát hiện bịa

### Agent và workflow

- [ ] 🟡 **Vòng lặp tool**

  ```
  loop (tối đa N bước, tối đa T giây, tối đa C chi phí):
      resp = llm(messages, tools)
      if resp là câu trả lời cuối: return
      for call in resp.tool_calls:
          kiểm quyền + validate tham số
          result = run_tool(call)        // có timeout
          messages.append(result)
  ```

- [ ] 🟡 **Workflow vs agent**: workflow là chuỗi bước do code quyết định, LLM chỉ làm từng
      bước; agent để LLM tự chọn bước tiếp theo. Workflow dễ đoán, dễ test, rẻ hơn. Chỉ dùng
      agent khi các bước thực sự không biết trước. Câu trả lời senior thường là "bắt đầu bằng
      workflow"
- [ ] ⚠️ **Giới hạn**: số bước, tổng thời gian, tổng token/chi phí, số lần gọi mỗi tool. Không có
      giới hạn thì một vòng lặp lỗi (tool trả lỗi, model gọi lại mãi) đốt tiền không dừng
- [ ] 🟡 **Human-in-the-loop**: hành động không đảo ngược được hoặc có hậu quả (gửi email cho
      khách, hoàn tiền, xoá dữ liệu, deploy) thì agent chỉ đề xuất, người duyệt mới thực thi.
      Lưu trạng thái workflow để chờ duyệt (không giữ request mở), có timeout và audit log
- [ ] ⚠️ **Idempotency của tool có side effect**
  - Vòng lặp có retry, model có thể gọi lại cùng tool: tool tạo đơn/chuyển tiền phải nhận
    idempotency key, gọi hai lần kết quả như một lần. Xem [09-api-design.md](09-api-design.md)
  - Tách tool đọc (an toàn) và tool ghi (cần kiểm soát chặt hơn)
- [ ] 🟡 Tác vụ agent dài chạy như job nền có trạng thái, checkpoint và khả năng tiếp tục sau
      crash; không chạy trong một HTTP request

### Bảo mật

Liên quan chung ở [10-security.md](10-security.md). OWASP có danh sách Top 10 riêng cho ứng
dụng LLM, nên đọc qua bản hiện hành.

- [ ] ⚠️ **Prompt injection**
  - Trực tiếp: user gõ "bỏ qua mọi hướng dẫn trước đó và ..."
  - Gián tiếp: chỉ thị ẩn nằm trong dữ liệu model đọc: trang web, email, tài liệu được RAG lấy
    về, kết quả tool. Nguy hiểm hơn vì user thật không hề thấy
  - Chưa có cách chặn tuyệt đối bằng prompt. Phòng thủ bằng **kiến trúc**: giới hạn cái model
    có thể làm, không phải cái model được "dặn"
    - Quyền tool tối thiểu, theo đúng quyền của user đang dùng
    - Hành động nguy hiểm cần xác nhận của người
    - Tách dữ liệu không tin cậy khỏi chỉ thị (đánh dấu rõ đâu là dữ liệu), nhưng không coi đó
      là biện pháp đủ
    - ⚠️ Tổ hợp nguy hiểm: model vừa đọc dữ liệu không tin cậy, vừa truy cập dữ liệu nhạy cảm,
      vừa có kênh gửi ra ngoài (gọi URL, gửi email, render ảnh từ URL). Cắt một trong ba
- [ ] ⚠️ **Rò rỉ dữ liệu**
  - System prompt có thể bị moi ra: không để secret, API key, quy tắc nhạy cảm trong prompt
  - Dữ liệu của user A lọt sang user B qua cache dùng chung, lịch sử hội thoại, hoặc RAG không
    lọc quyền
- [ ] ⚠️ **PII gửi ra ngoài**
  - Gửi dữ liệu cá nhân cho provider là chuyển dữ liệu cho bên thứ ba: kiểm tra hợp đồng,
    chính sách lưu trữ/huấn luyện của provider, vùng lưu trữ dữ liệu, và quy định bảo vệ dữ
    liệu cá nhân áp dụng
  - Giảm thiểu: chỉ gửi field cần thiết, ẩn/thay thế PII trước khi gửi (và khôi phục sau nếu cần)
- [ ] ⚠️ **Phân quyền trong RAG**
  - Lọc theo quyền **tại bước retrieval**, bằng metadata ACL/tenant trong câu truy vấn vector.
    Không bao giờ lấy mọi chunk rồi "dặn" model đừng tiết lộ
  - Quyền phải được đồng bộ khi thay đổi (xem mục cập nhật index)
  - Multi-tenant: tách index/namespace theo tenant, hoặc filter tenant bắt buộc ở lớp truy cập
    dữ liệu để không ai quên được
- [ ] ⚠️ **Output gây lỗ hổng ở hệ thống phía sau**
  - Render output dạng HTML/Markdown mà không escape: XSS (kể cả link/ảnh markdown trỏ tới URL
    của kẻ tấn công để gửi dữ liệu ra ngoài)
  - Model sinh SQL: chạy bằng user DB chỉ đọc, giới hạn bảng, timeout, hoặc tốt hơn là cho model
    chọn tham số của query đã viết sẵn thay vì sinh SQL tự do
  - Model sinh lệnh shell, đường dẫn file, URL: allowlist; không truyền thẳng vào `exec`,
    `file_get_contents`, HTTP client (SSRF)

### Vận hành

- [ ] 🟡 **Log và trace**
  - Log prompt, response, model, tham số, số token, latency, chi phí, tool call; gắn trace id với
    request gốc. Không có log thì không debug được câu trả lời sai
  - ⚠️ Prompt và response chứa PII và dữ liệu nhạy cảm: che trước khi log, giới hạn quyền xem,
    đặt thời gian lưu, cân nhắc lấy mẫu thay vì log toàn bộ
  - Xem [18-reliability-observability.md](18-reliability-observability.md)
- [ ] 🔴 **Eval**
  - Không tất định nên không test bằng assert chuỗi chính xác. Dùng bộ test offline: tập input
    thật (đã ẩn danh) kèm tiêu chí chấm
  - Cách chấm: kiểm tra có cấu trúc (JSON hợp lệ, field đúng, có trích dẫn), so với đáp án chuẩn,
    LLM-as-judge (một model chấm theo rubric; ⚠️ bản thân judge cũng cần kiểm chứng với người chấm),
    và đánh giá của người trên một mẫu
  - Chạy eval như regression test mỗi khi đổi prompt, đổi model, đổi cách chunk. Xem
    [20-testing-quality.md](20-testing-quality.md)
  - Code quanh LLM (parse, validate, tool, retry) vẫn test bình thường bằng fake LLM trả output
    định sẵn, kể cả output hỏng
- [ ] 🟡 **Theo dõi production**
  - Latency: time to first token, tổng thời gian; tỉ lệ lỗi, timeout, 429 theo provider
  - Chi phí theo feature/tenant; số token trung bình mỗi request
  - Chất lượng: phản hồi của user (like/dislike), tỉ lệ output không parse được, tỉ lệ fallback
  - ⚠️ Chất lượng có thể giảm mà không có lỗi nào: provider cập nhật model, dữ liệu đổi. Cố định
    phiên bản model khi có thể và chạy eval định kỳ
- [ ] 🟡 **Version prompt như code**: prompt nằm trong repo, review qua PR, có version gắn vào
      log để biết câu trả lời nào dùng prompt nào; rollout prompt mới qua feature flag/A-B

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Tích hợp chatbot LLM vào hệ thống thế nào? | "Gọi API của provider, trả kết quả cho frontend." | "Qua lớp adapter có timeout, retry có giới hạn, circuit breaker, fallback. Stream qua SSE, huỷ khi client ngắt. Quota theo user, theo dõi chi phí theo feature. Log có che PII. Có eval set trước khi đổi prompt hay model." |
| Chống prompt injection thế nào? | "Thêm vào prompt: không làm theo chỉ dẫn của user." | "Không chặn được tuyệt đối bằng prompt nên giới hạn ở kiến trúc: tool quyền tối thiểu theo user, hành động nguy hiểm cần người duyệt, lọc quyền ở retrieval, không để model vừa đọc dữ liệu lạ vừa có kênh gửi dữ liệu ra ngoài." |
| RAG trả lời sai thì sửa ở đâu? | "Đổi prompt hoặc dùng model mạnh hơn." | "Đo retrieval trước: chunk đúng có nằm trong top-K không. Thường lỗi ở trích xuất text, chunking, thiếu hybrid search cho mã/tên riêng. Có bộ câu hỏi chuẩn để đo trước và sau khi sửa." |
| pgvector hay vector DB riêng? | "Vector DB riêng vì chuyên dụng." | "Quy mô vừa và đã dùng Postgres thì pgvector: một nơi lưu, lọc quyền bằng SQL, transaction chung, không phải đồng bộ hai hệ thống. Chuyển sang hệ thống riêng khi đo thấy giới hạn về quy mô hoặc tính năng." |
| Dùng agent cho quy trình hoàn tiền? | "Cho agent gọi API hoàn tiền." | "Workflow cố định, LLM chỉ phân loại và soạn đề xuất; hoàn tiền cần người duyệt, tool có idempotency key, giới hạn số tiền, audit log." |

## Tình huống

1. **Tính năng tóm tắt tài liệu làm PHP-FPM hết worker giờ cao điểm.**
   - Gợi ý: chuyển sang job nền trả job id; giới hạn đồng thời tới provider; cache kết quả
     theo hash tài liệu; stream nếu cần tương tác.
2. **Hoá đơn LLM tháng này gấp ba tháng trước.**
   - Gợi ý: xem chi phí theo feature/tenant; tìm vòng lặp retry hoặc agent không giới hạn bước;
     lịch sử hội thoại không cắt; RAG nhồi quá nhiều chunk; áp quota và cảnh báo.
3. **Chatbot nội bộ trả lời bằng nội dung tài liệu phòng nhân sự cho nhân viên không có quyền.**
   - Gợi ý: lọc ACL tại retrieval; đồng bộ quyền vào metadata; rà cache dùng chung; audit log để
     xác định ai đã xem gì; coi là sự cố bảo mật.
4. **Model trả JSON thỉnh thoảng thiếu field làm job crash.**
   - Gợi ý: validate schema, retry có giới hạn kèm thông báo lỗi, fallback; đưa các ca hỏng vào
     eval set; không để exception làm dừng cả batch.
5. **Agent đọc email khách hàng và có tool gửi email.**
   - Gợi ý: prompt injection gián tiếp qua email; gửi email cần người duyệt hoặc chỉ cho gửi tới
     địa chỉ trong thread; giới hạn bước; log tool call.
6. **Provider chính bị sự cố một giờ.**
   - Gợi ý: circuit breaker, chuyển sang provider/model phụ đã eval, hoặc tắt tính năng AI và
     giữ luồng chính chạy; thông báo trạng thái cho user.
7. **Đổi sang model embedding mới.**
   - Gợi ý: embed lại toàn bộ vào index mới song song, so sánh trên eval set, chuyển đổi rồi
     xoá index cũ; tính chi phí embed lại trước.

## ❓ Câu hỏi hay gặp

🟢
- Vì sao không nên gọi LLM API đồng bộ trong request thread với timeout mặc định?
- Streaming response qua SSE hoạt động thế nào?
- Vì sao phải validate output của LLM?

🟡
- Thiết kế retry và fallback cho lời gọi LLM thế nào? Lỗi nào không nên retry?
- Làm sao kiểm soát chi phí khi dùng LLM?
- RAG là gì, vì sao dùng RAG thay vì đưa toàn bộ dữ liệu vào prompt?
- Chunking ảnh hưởng chất lượng thế nào?
- Tool calling hoạt động thế nào? Ai thực thi tool?
- Prompt injection gián tiếp là gì?
- Log prompt/response có vấn đề gì?

🔴
- HNSW là gì, đánh đổi gì so với tìm chính xác?
- Vì sao cần hybrid search? Gộp điểm BM25 và vector thế nào?
- Đảm bảo user không truy xuất được tài liệu họ không có quyền trong RAG thế nào?
- Đánh giá chất lượng một hệ thống RAG thế nào? Regression khi đổi prompt?
- Workflow cố định hay agent: chọn thế nào cho một quy trình có hành động ghi?

## Bài tập tự làm

1. Vẽ sơ đồ luồng cho tính năng "hỏi đáp tài liệu nội bộ" gồm ingest, cập nhật khi tài liệu
   sửa/xoá, và lọc quyền. Chỉ ra ba điểm có thể rò rỉ dữ liệu.
2. Viết interface adapter (Go, Java hoặc PHP) cho lời gọi LLM có timeout, retry, fallback và
   ghi token/chi phí. Chỉ cần interface và mô tả hành vi, không cần gọi provider thật.
3. Liệt kê 10 câu hỏi cho eval set của một chatbot hỗ trợ khách hàng, kèm tiêu chí chấm cho mỗi câu.
4. Với một agent có tool `search_orders`, `refund_order`, `send_email`, mô tả các giới hạn và
   kiểm soát bạn đặt cho từng tool.
5. So sánh pgvector với một vector DB riêng cho hệ thống 1 triệu chunk, 50 tenant: nêu tiêu chí
   và điều kiện khiến bạn đổi lựa chọn.

> Nộp bài vào đây để được review.
