# 18. Reliability và observability

> [← Mục lục](README.md) · Trọng tâm: **SLO và error budget, log/metric/trace, alerting, xử lý sự cố** cho hệ thống PHP-FPM/Laravel; đối chiếu Java/Go khi có ích.
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
| [Google SRE books](https://sre.google/books/) (*Site Reliability Engineering* và *The Site Reliability Workbook*) | Sách online miễn phí | Nguồn gốc của SLO, error budget, burn rate alert, on-call, postmortem. Workbook thực hành hơn, nên đọc trước |
| [OpenTelemetry docs](https://opentelemetry.io/docs/concepts/) | Official docs | Trace, span, context propagation, sampling, Collector |
| [Prometheus docs](https://prometheus.io/docs/concepts/metric_types/) | Official docs | Loại metric, đặt tên, histogram, alerting rule |
| *Observability Engineering* (Majors, Fong-Jones, Miranda; O'Reilly 2022) | Sách | Observability khác monitoring ở đâu, event có nhiều chiều, SLO-based alerting |
| [Amazon Builders' Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | Blog kỹ thuật | Timeout, retry, health check, load shedding từ kinh nghiệm vận hành của AWS |
| [AWS: Disaster Recovery of Workloads](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html) | Whitepaper | Các mức DR, RPO/RTO |
| [PagerDuty Incident Response](https://response.pagerduty.com/) | Tài liệu mở | Quy trình sự cố, vai trò, giao tiếp; viết rất cụ thể, dùng được làm mẫu |
| [Laravel docs: Logging](https://laravel.com/docs/logging) và [Context](https://laravel.com/docs/context) | Official docs | Log có context trong Laravel, truyền context sang queue job |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Nói đúng SLI/SLO/SLA, viết health check đúng, log có cấu trúc, biết xử lý sự cố theo thứ tự | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.8 | Dùng error budget, thiết kế metric và trace, alert không gây mệt, backup đúng, quan sát được PHP-FPM và queue | 8–10 ngày |
| **3. Senior** 🔴 | 3.1–3.6 | Burn rate alert, kiểm soát chi phí observability, thiết kế DR, điều phối sự cố lớn, chaos engineering | 7–9 ngày |

Học theo thứ tự: chặng 2 cần hiểu SLI ở chặng 1 để thiết kế metric và alert, chặng 3 cần error
budget và metric của chặng 2 để làm burn rate alert. Phần sự cố (1.4, 2.8, 3.4) nên học kèm
việc viết lại một sự cố thật của chính mình, vì câu "kể một sự cố bạn đã xử lý" gần như luôn
xuất hiện.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 SLI, SLO, SLA

**Vì sao cần học:** SLO là ngôn ngữ chung để dev, ops và product cùng trả lời câu "hệ thống đã
đủ ổn định chưa". Error budget và burn rate alert ở các module sau đều xây trên nó. Câu mở đầu
kinh điển là "SLI, SLO, SLA khác nhau thế nào", và thường bị hỏi tiếp "SLO của hệ thống bạn là
gì, đo ở đâu".

**Học gì**

*Ba khái niệm*
- *SLI* (Service Level Indicator) là một con số đo một khía cạnh chất lượng mà người dùng cảm
  nhận được.
  - Ví dụ: tỉ lệ request thành công, tỉ lệ request trả về dưới 300 ms.
- *SLO* (Service Level Objective) là mục tiêu nội bộ đặt cho một SLI trong một cửa sổ thời gian.
  - Ví dụ: "99,9% request đăng nhập thành công, tính trong 30 ngày gần nhất".
- *SLA* (Service Level Agreement) là cam kết trong hợp đồng với khách hàng. Vi phạm thì phải phạt
  hoặc đền bù, ví dụ hoàn một phần tiền.

| | SLI | SLO | SLA |
|---|---|---|---|
| Là gì | Số đo | Mục tiêu nội bộ cho số đo | Cam kết hợp đồng |
| Ví dụ | Tỉ lệ request không lỗi | 99,9% trong 30 ngày | 99,5% trong tháng, không đạt thì hoàn 10% phí |
| Ai quan tâm | Kỹ thuật | Team kỹ thuật và product | Khách hàng, kinh doanh, pháp lý |
| Vi phạm thì sao | | Team ưu tiên sửa độ ổn định | Mất tiền, mất uy tín |

- SLA nên lỏng hơn SLO để có vùng đệm. Vi phạm SLO là tín hiệu nội bộ để sửa, trước khi chạm tới
  mức phải đền tiền.

*Chọn SLI thế nào*
- Chọn theo góc người dùng. Đo ở load balancer (LB), API gateway hoặc phía client, không đo CPU
  server.
  - Vì sao: CPU 95% mà người dùng vẫn thấy nhanh thì không có vấn đề. CPU 20% mà mọi request trả
    500 thì có vấn đề lớn.
- Viết SLI dạng tỉ lệ `sự kiện tốt / tổng sự kiện`, để luôn nằm trong khoảng 0–100%. Các loại hay
  dùng:
  - Availability: tỉ lệ request không trả 5xx.
  - Latency: tỉ lệ request nhanh hơn một ngưỡng, ví dụ dưới 300 ms.
  - Freshness, cho pipeline dữ liệu: tỉ lệ dữ liệu được cập nhật trong vòng N phút.
  - Correctness: tỉ lệ kết quả đúng.
- Mỗi *user journey* quan trọng một SLO. User journey là một việc người dùng muốn làm trọn vẹn,
  như đăng nhập hay thanh toán.
  - Không cần SLO cho mọi endpoint.

*Mục tiêu bao nhiêu là đủ*
- ⚠️ 100% không phải mục tiêu.
  - Chi phí tăng vô hạn khi tiến gần 100%.
  - Người dùng không phân biệt được 99,99% với 100%, vì mạng 4G hay wifi của chính họ còn hỏng
    thường xuyên hơn.
- Con số cần thuộc. Cách tính: `(1 − SLO) × 43.200 phút` (30 ngày).

  | SLO | Downtime cho phép trong 30 ngày |
  |---|---|
  | 99,9% | ≈ 43 phút |
  | 99,95% | ≈ 22 phút |
  | 99,99% | ≈ 4,3 phút |

**Đọc**
- SRE book: [Service Level Objectives](https://sre.google/sre-book/service-level-objectives/), [Embracing Risk](https://sre.google/sre-book/embracing-risk/)
- SRE Workbook: [Implementing SLOs](https://sre.google/workbook/implementing-slos/) (phần chọn SLI và bảng SLI theo loại hệ thống)

**Nắm chắc khi**
- [ ] Viết được 3 SLO cho hệ thống đang làm, mỗi SLO ghi rõ SLI, nơi đo, cửa sổ, mục tiêu
- [ ] Tính nhẩm được downtime cho phép của 99,9% và 99,99% trong một tháng
- [ ] Giải thích được vì sao SLI "CPU < 80%" là SLI tồi

#### 1.2 Redundancy và health check

**Vì sao cần học:** Hệ thống chỉ chịu được hỏng hóc khi mọi thành phần có bản dự phòng, và khi
LB biết bản nào còn dùng được. Health check viết sai là nguyên nhân phổ biến biến một sự cố nhỏ
thành sập toàn bộ. "Liveness khác readiness thế nào" gần như luôn được hỏi khi nói tới
Kubernetes.

**Học gì**

*Redundancy và failure domain*
- *Redundancy* (dư thừa) nghĩa là mỗi thành phần có ít nhất hai bản. Một bản chết thì bản kia
  gánh.
- Hai bản phải nằm ở hai *failure domain* khác nhau. Failure domain là phạm vi những thứ hỏng cùng
  lúc vì chung một nguyên nhân:
  - Cùng máy.
  - Cùng rack: chung nguồn điện, chung switch.
  - Cùng AZ (*availability zone*): một cụm datacenter độc lập trong một region của cloud.
- Ví dụ: hai container PHP chạy trên cùng một VM không phải dự phòng cho trường hợp VM đó chết.

*SPOF*
- *SPOF* (single point of failure) là thành phần mà nó hỏng thì cả hệ thống hỏng. Những SPOF hay
  gặp:
  - DB primary.
  - LB.
  - Redis dùng cho session, cache hoặc queue.
  - Cron server chạy trên một máy duy nhất.
  - DNS.
  - Chứng chỉ TLS hết hạn.
  - Một người duy nhất biết vận hành hệ thống.
- ⚠️ Hai mục cuối không phải máy chủ nhưng vẫn là SPOF, và hay bị quên khi liệt kê.

*Liveness và readiness*
- *Health check* là endpoint mà LB hoặc *orchestrator* (chương trình quản lý container, như
  Kubernetes) gọi định kỳ để biết instance còn dùng được không. Có hai loại với hai câu hỏi khác
  nhau:

| | Liveness | Readiness |
|---|---|---|
| Hỏi gì | Process còn sống, không bị kẹt (ví dụ *deadlock*: hai luồng chờ nhau mãi) | Sẵn sàng nhận traffic chưa: đã warm-up, đã kết nối xong |
| Fail thì | Restart | Bỏ khỏi LB, không restart |
| Nên kiểm tra | Chỉ chính process | Thứ bắt buộc và riêng của instance |

*Hai bẫy kinh điển*
- ⚠️ **Liveness kiểm tra DB.** Chuỗi sự cố:
  1. DB chậm một chút, ví dụ 5 giây.
  2. Liveness của mọi pod cùng timeout.
  3. Mọi pod bị restart cùng lúc.
  4. Trong lúc restart không pod nào phục vụ. Một lần DB chậm vài giây thành cả service sập vài
     phút.

  Liveness chỉ kiểm tra chính process.
- ⚠️ **Readiness kiểm tra sâu mọi dependency.** Chuỗi sự cố:
  1. Một dependency phụ chết, ví dụ service gửi email.
  2. Mọi instance cùng báo "not ready".
  3. LB không còn instance nào để gửi request, nên mất toàn bộ service, kể cả những trang không cần
     gửi email.

  Readiness chỉ kiểm tra thứ bắt buộc và riêng của instance.

*Viết endpoint health*
- Rẻ: không chạy query nặng.
- Không cần auth.
- Không log mỗi lần gọi. Endpoint bị gọi vài giây một lần, log sẽ ngập.
- Laravel 11+ có sẵn route `/up`.
- Chi tiết probe trên Kubernetes ở [19-devops-cloud.md](19-devops-cloud.md).

**Đọc**
- [Amazon Builders' Library: Implementing health checks](https://aws.amazon.com/builders-library/implementing-health-checks/): đọc hết, có phần "fail open" khi mọi instance cùng báo hỏng
- Kubernetes: [Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
- Laravel: [The Health Route](https://laravel.com/docs/deployment#the-health-route)

**Nắm chắc khi**
- [ ] Liệt kê được 5 SPOF trong hệ thống mình đang làm, kể cả SPOF không phải máy chủ
- [ ] Kể được từng bước vì sao liveness gọi DB biến một lần DB chậm 5 giây thành outage vài phút

#### 1.3 Log có cấu trúc

**Vì sao cần học:** Khi có sự cố, log là nơi đầu tiên để tìm "vì sao". Log dạng chuỗi tự do thì
chỉ grep được, không lọc được theo user hay theo request. Hay bị hỏi: log có cấu trúc là gì,
correlation id dùng làm gì, và những gì không được ghi vào log.

**Học gì**

*Structured log*
- Log dạng chuỗi tự do trông như sau. Muốn lọc mọi lỗi của user 42 thì phải viết regex:

  ```
  [2026-09-25 10:00:01] production.ERROR: Payment failed for user 42 after 1200ms
  ```
- *Structured log* ghi mỗi dòng là một object JSON với các field có tên:

  ```json
  {"level":"error","msg":"payment failed","request_id":"a1b2c3","user_id":42,"duration_ms":1200}
  ```
  - Hệ thống log lọc và tổng hợp trực tiếp theo field: mọi dòng có `user_id = 42`, trung bình
    `duration_ms` theo giờ.

*Log level*

| Level | Dùng khi | Ví dụ |
|---|---|---|
| `DEBUG` | Chỉ ở môi trường dev | Giá trị biến trung gian |
| `INFO` | Sự kiện nghiệp vụ bình thường | Đơn hàng được tạo |
| `WARN` | Bất thường nhưng tự xử lý được | Retry lần 2 mới thành công |
| `ERROR` | Thao tác thất bại, cần người chú ý | Gọi cổng thanh toán lỗi |

- ⚠️ Log `ERROR` cho lỗi validate của người dùng (nhập sai định dạng email) làm nhiễu alert. Đó là
  hành vi bình thường, không phải lỗi hệ thống.
- Log "failed" không có id, không có lý do là log vô dụng.

*Correlation id*
- *Correlation id* (hay *request id*) là một chuỗi ngẫu nhiên đại diện cho một request, gắn vào mọi
  dòng log của request đó.
- Cách làm:
  1. Sinh ở *edge* (LB, gateway hoặc middleware đầu tiên), hoặc nhận từ header nếu service phía
     trước đã gửi.
  2. Gắn vào mọi log trong request.
  3. Truyền tiếp qua header khi gọi service khác, và qua payload khi đẩy job vào message queue.
- Kết quả: tìm một id là thấy toàn bộ hành trình của request, qua nhiều service và cả queue worker.

*Log đi đâu*
- App chỉ ghi ra stdout/stderr. Một *agent* (chương trình thu gom chạy cạnh app, như Fluent Bit)
  đọc và gửi về hệ thống log. Đây là một nguyên tắc của 12-factor app.
  - Vì sao: app không phải lo xoay vòng file hay đầy đĩa, và container bị xoá thì file log bên
    trong cũng mất theo.

*Không được log gì*
- ⚠️ Không log *PII* (thông tin định danh cá nhân) và secret:
  - Mật khẩu, token, header `Authorization`.
  - Số thẻ, OTP.
  - CCCD và giấy tờ tuỳ thân.
- Mask ở tầng logger bằng danh sách field cấm, không trông vào từng dev tự nhớ
  ([10-security.md](10-security.md)).

*Đối chiếu Java/Go*

| Ngôn ngữ | Thư viện | Gắn context cho mọi log |
|---|---|---|
| PHP | Monolog | Processor, `Log::withContext()` (module 2.7) |
| Java | SLF4J + Logback/Log4j2 | *MDC* (Mapped Diagnostic Context): map key-value gắn theo thread |
| Go | `log/slog` (thư viện chuẩn từ Go 1.21) | `logger.With(...)` |

**Đọc**
- Laravel: [Logging](https://laravel.com/docs/logging) (mục [Contextual Information](https://laravel.com/docs/logging#contextual-information)), [Context](https://laravel.com/docs/context)
- [Monolog](https://github.com/Seldaek/monolog): README, phần formatter và processor
- OpenTelemetry: [Logs](https://opentelemetry.io/docs/concepts/signals/logs/) (cách gắn trace id vào log)

**Nắm chắc khi**
- [ ] Viết được middleware sinh/nhận request id và gắn vào mọi log của request (bài tập 2)
- [ ] Lấy một dòng log thật trong project, chỉ ra thiếu field gì để debug được mà không cần hỏi người viết

#### 1.4 Quy trình sự cố cơ bản

**Vì sao cần học:** "Production lỗi, bạn làm gì" và "kể một sự cố bạn đã xử lý" gần như luôn
xuất hiện. Người phỏng vấn nghe thứ tự ưu tiên của bạn: cứu hệ thống trước, hay lao vào tìm
nguyên nhân trước.

**Học gì**

*Các bước xử lý sự cố*
1. Phát hiện: alert kêu, hoặc người dùng báo.
2. Phân loại: ảnh hưởng bao nhiêu người, mức nghiêm trọng (SEV, module 3.4), mở kênh sự cố.
3. Giảm thiệt hại (*mitigate*).
4. Khắc phục.
5. Đóng sự cố.
6. Viết postmortem (module 2.8).

*Mitigate trước, root cause sau*
- *Mitigate* là đưa hệ thống về trạng thái chạy được, dù chưa hiểu vì sao hỏng. *Root cause* là
  nguyên nhân gốc.
- Điều tra sâu khi đã hết "chảy máu". Mỗi phút ngồi debug khi hệ thống còn sập là một phút người
  dùng bị ảnh hưởng.
- Có deploy hoặc đổi config gần thời điểm sự cố bắt đầu → **rollback** là hành động đầu tiên hợp
  lý, kể cả khi chưa chắc đó là nguyên nhân.
  - Vì sao: rollback nhanh và rẻ. Nếu rollback không hết lỗi, bạn cũng đã loại được một khả năng.
- Các cách mitigate khác:
  - Tắt feature flag.
  - Chuyển traffic sang nơi khác.
  - Scale thêm.
  - Chặn nguồn tải xấu, ví dụ một IP hay một client gọi quá nhiều.

*Giữ bằng chứng*
- Nếu kịp, lưu bằng chứng trước khi restart:
  - Log.
  - *Heap dump*: ảnh chụp bộ nhớ của process.
  - *Thread dump*: ảnh chụp từng thread đang làm gì.
- Không để việc này kéo dài sự cố.

*Khi rollback không cứu được*
- ⚠️ Migration không tương thích ngược đã chạy thì rollback code không giúp gì.
  - Ví dụ: migration đã xoá cột mà code cũ còn đọc. Rollback về code cũ thì code cũ lỗi ngay.
  - Đó là lý do migration phải theo kiểu expand/contract: thêm trước, xoá sau, qua nhiều lần
    deploy ([19-devops-cloud.md](19-devops-cloud.md), module 3.3).

*Câu chuyện sự cố của chính mình*
- Chuẩn bị trước, gồm năm phần:
  - Chuyện gì xảy ra.
  - Phát hiện thế nào.
  - Root cause.
  - Khắc phục tức thời.
  - Phòng ngừa lâu dài.
- Cách kể: [25-interview-skills.md](25-interview-skills.md).

**Đọc**
- SRE book: [Managing Incidents](https://sre.google/sre-book/managing-incidents/)
- [PagerDuty Incident Response](https://response.pagerduty.com/): phần *Before*, *During an Incident*

**Nắm chắc khi**
- [ ] Kể được 15 phút đầu của sự cố "500 hàng loạt ngay sau deploy" theo đúng thứ tự
- [ ] Kể được một sự cố thật của mình trong 3 phút, có phần phòng ngừa lâu dài

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Error budget

**Vì sao cần học:** Error budget biến SLO thành công cụ ra quyết định: khi nào được deploy mạnh
tay, khi nào phải dừng để sửa độ ổn định. Câu "làm sao cân bằng tốc độ ra tính năng và độ ổn
định" hay được hỏi ở mức mid trở lên, và error budget là câu trả lời chuẩn.

**Học gì**

*Error budget là gì*
- *Error budget* = 1 − SLO, tức phần "được phép hỏng" trong kỳ.
- Ví dụ: SLO 99,9% trong 30 ngày thì budget là 0,1%, tức khoảng 43 phút downtime, hoặc 0,1% số
  request được phép lỗi.
- Hai cách tính:
  - Theo request, cho hệ thống nhiều traffic. Ví dụ 10 triệu request một tháng thì được lỗi 10.000
    request.
  - Theo thời gian, cho hệ thống ít traffic, nơi vài request lỗi đã là một tỉ lệ lớn.

*Dùng budget để ra quyết định*
- Còn budget → được deploy, thử nghiệm, chấp nhận rủi ro.
- Hết budget → đóng băng tính năng mới, dồn sức cho reliability.
- Giá trị lớn nhất: biến tranh cãi "dev muốn nhanh, ops muốn ổn định" thành một con số chung mà
  hai bên đã thống nhất từ trước.

*Error budget policy*
- Là văn bản ghi trước:
  - Ai quyết định.
  - Hết budget thì dừng những gì.
  - Ngoại lệ nào được phép, ví dụ bản vá bảo mật.
- ⚠️ Policy phải được lãnh đạo đồng ý trước. Không thì hết budget vẫn bị ép ra tính năng, và
  budget chỉ còn là một con số trên dashboard.

**Đọc**
- SRE Workbook: [Example Error Budget Policy](https://sre.google/workbook/error-budget-policy/)
- SRE book: [Embracing Risk](https://sre.google/sre-book/embracing-risk/) (phần *Motivation for Error Budgets*)

**Nắm chắc khi**
- [ ] Viết được error budget policy một trang: ai quyết định, hết budget thì dừng gì, ngoại lệ nào
- [ ] Tính được còn bao nhiêu budget khi tháng này đã có một sự cố 20 phút và 0,03% request lỗi rải rác

#### 2.2 Metric

**Vì sao cần học:** Metric là thứ vẽ dashboard và kích hoạt alert. Chọn sai loại metric thì số
liệu sai, đặt sai label thì có thể làm sập chính hệ thống monitoring. Hay bị hỏi: counter, gauge,
histogram khác nhau thế nào, RED và USE là gì, vì sao không dùng `user_id` làm label.

**Học gì**

*Metric, label và time series*
- *Metric* là một con số được đo lặp lại theo thời gian, ví dụ tổng số request, số job đang chờ
  trong queue.
- Metric có thể kèm *label* (nhãn) để chia nhỏ:

  ```
  http_requests_total{route="/orders/{id}", status="500"}
  ```
- Mỗi tổ hợp giá trị label là một *time series* riêng, tức một dãy điểm theo thời gian. Chúng được
  lưu trong *TSDB* (time series database), ví dụ Prometheus.
- *Percentile*: p99 = 300 ms nghĩa là 99% request nhanh hơn 300 ms.

*Bốn loại metric của Prometheus*

| Loại | Là gì | Ví dụ | Lưu ý |
|---|---|---|---|
| Counter | Chỉ tăng, reset về 0 khi process restart | `http_requests_total` | Luôn dùng `rate()`/`increase()`, không nhìn giá trị tuyệt đối |
| Gauge | Lên xuống tự do | `queue_depth`, `db_pool_in_use` | |
| Histogram | Đếm số lần quan sát rơi vào từng *bucket* (khoảng giá trị, ví dụ ≤ 100 ms, ≤ 300 ms) | `http_request_duration_seconds` | Tính percentile bằng `histogram_quantile()`, **gộp được** giữa instance |
| Summary | Tính sẵn quantile ngay phía client | | ⚠️ Không gộp được giữa instance |

- Vì sao summary không gộp được: không thể lấy trung bình p99 của 3 instance để ra p99 chung.
  Histogram chỉ là các bộ đếm, nên cộng bộ đếm của các instance lại là ra histogram chung.
- Chọn bucket histogram quanh ngưỡng SLO. Bucket quá thô (ví dụ chỉ có 100 ms và 1 s) thì
  percentile tính ra sai.

*Cardinality*
- *Cardinality* của một metric là số time series của nó, bằng số tổ hợp giá trị label.
  - Ví dụ: 20 route × 5 status × 10 instance = 1.000 series. Thêm label `user_id` với 100.000 user
    thì thành 100 triệu series.
- ⚠️ Label có quá nhiều giá trị làm nổ cardinality:
  - `user_id`, `order_id`.
  - URL chứa id, như `/orders/12345`.
  - Message lỗi.

  Kết quả là hàng triệu series, TSDB tốn RAM và sập.
- Cách sửa: dùng route template (`/orders/{id}`), đưa id vào log hoặc trace.

*Chọn đo gì: RED, USE, four golden signals*

| Phương pháp | Áp cho | Gồm |
|---|---|---|
| **RED** | Service (API, web) | Rate (số request/giây), Errors (số lỗi/giây), Duration (thời gian xử lý) |
| **USE** | Tài nguyên (CPU, đĩa, connection pool, queue) | Utilization (mức đang dùng), Saturation (lượng việc đang phải chờ), Errors |
| **Four golden signals** (Google SRE) | Service | Latency, traffic, errors, saturation |

- Ví dụ USE cho queue worker: utilization là số worker đang bận trên tổng số worker, saturation là
  số job đang chờ.

*Hai bẫy khi đọc latency*
- ⚠️ Tách latency của request lỗi và request thành công. Request lỗi thường trả rất nhanh (ví dụ
  500 ngay khi DB từ chối kết nối), kéo latency chung xuống, trông "đẹp" giả.
- ⚠️ Trung bình che giấu đuôi.
  - Ví dụ: 99 request mất 50 ms và 1 request mất 10 giây. Trung bình khoảng 150 ms, trông ổn,
    nhưng 1% người dùng phải chờ 10 giây.
  - Nhìn p95/p99 ([17-performance.md](17-performance.md)).

*Pull và push*
- Pull: Prometheus định kỳ gọi endpoint `/metrics` của app để lấy số. Việc này gọi là *scrape*.
- Push: app tự đẩy số đi. Dùng cho job ngắn, chết trước khi kịp bị scrape:
  - Pushgateway của Prometheus.
  - OTLP push (giao thức của OpenTelemetry, module 2.3).

**Đọc**
- Prometheus: [Metric types](https://prometheus.io/docs/concepts/metric_types/), [Histograms and summaries](https://prometheus.io/docs/practices/histograms/), [Metric and label naming](https://prometheus.io/docs/practices/naming/), [Instrumentation](https://prometheus.io/docs/practices/instrumentation/) (có mục cardinality)
- SRE book: [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) (four golden signals)
- Brendan Gregg: [The USE Method](https://www.brendangregg.com/usemethod.html)
- Grafana: [The RED Method](https://grafana.com/blog/2018/08/02/the-red-method-how-to-instrument-your-services/)

**Nắm chắc khi**
- [ ] Viết được PromQL cho tỉ lệ lỗi 5xx và p99 latency theo route trong 5 phút
- [ ] Nhìn danh sách label của một metric, chỉ ra label nào gây nổ cardinality và sửa được
- [ ] Liệt kê được metric RED cho API và USE cho queue worker của hệ thống mình (bài tập 5)

#### 2.3 Tracing và OpenTelemetry

**Vì sao cần học:** Một request đặt hàng có thể đi qua API, DB, Redis, queue, worker và vài
service khác. Khi nó chậm, metric chỉ nói "chậm", còn log thì rải rác nhiều nơi. Trace cho thấy
chậm ở chặng nào. Hay bị hỏi: trace id được truyền qua các service thế nào, và chỗ nào hay làm
đứt trace.

**Học gì**

*Trace và span*
- *Span* là một đơn vị công việc, ví dụ một HTTP call hay một query DB. Mỗi span có:
  - Thời điểm bắt đầu và thời lượng.
  - *Attribute*: các cặp key-value mô tả, ví dụ `http.route`.
  - Trạng thái: ok hoặc lỗi.
- *Trace* là cây các span của cùng một request. Mọi span trong trace chung một *trace id*, và mỗi
  span biết span cha của nó.

  ```
  POST /orders                     320 ms
  ├── SELECT products               12 ms
  ├── INSERT orders                  8 ms
  └── HTTP POST payment-gateway    280 ms   ← chậm ở đây
  ```

*Context propagation*
- *Context propagation* là truyền trace id và span id cha qua ranh giới service, để service phía sau
  nối span của nó vào đúng cây.
- Qua HTTP: dùng chuẩn W3C Trace Context, header `traceparent`.

  ```
  traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
               │  │                                │                └ cờ sampled (01 = có ghi lại)
               │  │                                └ span id cha
               │  └ trace id
               └ version
  ```
- Qua message queue: đặt vào header hoặc payload của message.
- ⚠️ Chỉ một chỗ quên propagate là trace bị đứt thành nhiều mảnh. Chỗ hay quên:
  - Go: goroutine mới không được truyền `context`.
  - Java: công việc đẩy sang thread pool.
  - PHP: queue job.

*OpenTelemetry*
- *OpenTelemetry* (OTel) là bộ chuẩn mở để thu trace, metric và log. Gồm:
  - API: giao diện để code gọi khi tạo span.
  - SDK: phần cài đặt, xử lý và gửi dữ liệu đi.
  - Auto-instrumentation: tự tạo span cho framework, DB driver, HTTP client mà không cần sửa code.
  - Collector: chương trình trung gian nhận dữ liệu, xử lý, rồi gửi tới backend.
- Gửi được tới nhiều backend (Jaeger, Tempo, Datadog...), nên tránh bị khoá vào một vendor.
- *Semantic conventions*: tên attribute chuẩn (`http.request.method`, `http.route`...) để dashboard
  và công cụ dùng chung được.

*Ba tín hiệu bổ trợ nhau*

| Tín hiệu | Trả lời câu hỏi |
|---|---|
| Metric | **Có** vấn đề không |
| Trace | Vấn đề **ở đâu** |
| Log | **Vì sao** |

- Cách nối chúng với nhau:
  - Gắn `trace_id` vào mọi dòng log.
  - *Exemplar*: trace id mẫu đính kèm vào một điểm metric, để từ đồ thị bấm sang được trace.
- Luồng điều tra:
  1. Alert kêu từ metric.
  2. Mở dashboard.
  3. Từ exemplar, mở trace mẫu của một request lỗi.
  4. Tìm span lỗi, ví dụ span DB.
  5. Xem log có cùng trace id để biết vì sao.

*Error tracking*
- Công cụ như Sentry gom các exception giống nhau thành một nhóm, kèm stack trace và *release*
  (phiên bản code sinh ra lỗi).
- Nhờ vậy biết một lỗi mới xuất hiện từ lần deploy nào.

**Đọc**
- OpenTelemetry: [Traces](https://opentelemetry.io/docs/concepts/signals/traces/), [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/), [Collector](https://opentelemetry.io/docs/collector/), [Semantic conventions](https://opentelemetry.io/docs/specs/semconv/) (lướt)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/): phần định dạng header `traceparent`
- Grafana: [Exemplars](https://grafana.com/docs/grafana/latest/fundamentals/exemplars/)

**Nắm chắc khi**
- [ ] Đọc được một header `traceparent` và chỉ ra trace id, span id cha, cờ sampled
- [ ] Vẽ được trace của request "đặt hàng" đi qua API → DB → queue → worker, chỉ ra chỗ dễ bị đứt trace
- [ ] Kể được luồng điều tra từ alert tới dòng log gây lỗi mà không cần grep toàn bộ log

#### 2.4 Alerting và on-call

**Vì sao cần học:** Alert quyết định ai bị đánh thức lúc 3 giờ sáng. Alert tồi hoặc để lọt sự
cố, hoặc làm team kiệt sức rồi bỏ qua mọi alert. Hay bị hỏi: vì sao alert theo triệu chứng chứ
không theo nguyên nhân, và xử lý thế nào khi alert kêu quá nhiều.

**Học gì**

*Page khi nào*
- *Page* là alert gọi người dậy ngay (điện thoại, SMS). Khác với *ticket*, là việc làm trong giờ
  hành chính.
- Page khi **người dùng bị ảnh hưởng**, tức theo triệu chứng:
  - Tỉ lệ lỗi hoặc latency vượt SLO.
  - Burn rate cao (module 3.1).
  - Không đặt được đơn.
- Nguyên nhân (CPU 90%, một pod restart) chỉ nên là dashboard hoặc ticket.
  - Ngoại lệ: nguyên nhân chắc chắn dẫn tới sự cố. Ví dụ đĩa sẽ đầy trong 4 giờ, dự báo bằng hàm
    `predict_linear` của Prometheus.
- Mỗi page phải thoả cả ba điều:
  - Cần hành động ngay.
  - Người nhận làm được gì đó.
  - Có runbook.

*Alert fatigue*
- ⚠️ *Alert fatigue*: alert báo quá nhiều hoặc hay báo sai → mọi người bỏ qua → alert thật bị lọt.
- Cách chữa:
  - Xoá hoặc hạ cấp alert không dẫn tới hành động nào.
  - Gom nhóm: một sự cố chỉ một page, không phải 50.
  - Thêm `for: 5m`, nghĩa là điều kiện phải đúng liên tục 5 phút mới báo, để bỏ nhiễu ngắn.
  - Review alert định kỳ theo số lần kích hoạt và số lần có hành động.

*Runbook*
- *Runbook* là tài liệu hướng dẫn xử lý một alert cụ thể. Gồm:
  - Ý nghĩa của alert.
  - Ảnh hưởng tới người dùng.
  - Dashboard cần xem.
  - Bước chẩn đoán.
  - Bước giảm thiệt hại.
  - Escalate cho ai.
- Bước nào lặp lại nhiều lần thì tự động hoá.

*On-call*
- *Rotation*: lịch trực luân phiên, gồm primary (người nhận đầu tiên) và secondary (dự phòng).
- *Escalation* tự động: primary không *ack* (xác nhận đã nhận) trong N phút thì hệ thống gọi người
  tiếp theo.
- Handover đầu ca: bàn giao những việc đang dở.
- Giữ on-call bền vững:
  - Giới hạn số page mỗi ca.
  - Bù giờ.
  - Không để một người on-call triền miên.

*Công cụ*
- *Alertmanager* (đi kèm Prometheus) nhận alert rồi:
  - Route: gửi tới đúng team.
  - Group: gom các alert liên quan thành một.
  - Silence: tắt tạm, ví dụ khi đang bảo trì.
  - Inhibit: khi một alert lớn đang kêu thì chặn các alert con do nó gây ra.
- Từ Alertmanager đẩy sang công cụ on-call: PagerDuty, incident.io, Grafana Cloud IRM, Jira Service
  Management.
- ⚠️ Opsgenie đã ngừng bán mới từ 06/2025 và tắt hẳn ngày 05/04/2027. Atlassian chuyển tính năng
  sang Jira Service Management.
- ⚠️ Grafana OnCall OSS vào chế độ maintenance từ 03/2025 và bị archive 03/2026. Grafana phát triển
  tiếp trong Grafana Cloud IRM.

**Đọc**
- SRE book: [Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/) (phần *Symptoms Versus Causes*), [Being On-Call](https://sre.google/sre-book/being-on-call/)
- SRE Workbook: [On-Call](https://sre.google/workbook/on-call/)
- Prometheus: [Alerting best practices](https://prometheus.io/docs/practices/alerting/), [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)
- Thông báo của vendor: [Grafana OnCall OSS maintenance mode](https://grafana.com/blog/grafana-oncall-maintenance-mode/), [Opsgenie migration](https://www.atlassian.com/software/opsgenie/migration)

**Nắm chắc khi**
- [ ] Phân loại được 10 alert hiện có của team thành: page, ticket, xoá
- [ ] Viết được runbook cho alert "5xx của API thanh toán > 2% trong 5 phút" (bài tập 4)
- [ ] Viết được một alert rule Prometheus có `for:` và label severity, giải thích vì sao chọn ngưỡng đó

#### 2.5 High availability và graceful degradation

**Vì sao cần học:** Câu thiết kế nào rồi cũng dẫn tới "nếu X chết thì sao". Cần biết failover
hoạt động thế nào và nó có thể làm mất gì, và làm sao để một dependency phụ chết không kéo sập cả
hệ thống. Với PHP-FPM, một API bên ngoài bỗng chậm là kịch bản sập kinh điển.

**Học gì**

*Failover tự động và thủ công*
- *Failover* là chuyển sang bản dự phòng khi bản chính hỏng.

| | Tự động | Thủ công |
|---|---|---|
| Tốc độ | Nhanh | Chậm, phải chờ người |
| Rủi ro chính | Failover nhầm, gây split-brain | Ít nhầm hơn |
| Cần gì | Cơ chế chống split-brain | Runbook và diễn tập |
| Hợp với | Thành phần stateless, cache | DB quan trọng |

- *Split-brain*: hai node cùng nghĩ mình là primary và cùng nhận ghi. Dữ liệu hai bên lệch nhau và
  rất khó gộp lại.
  - Ví dụ: mạng giữa hai AZ đứt tạm thời. Replica tưởng primary đã chết nên tự lên làm primary,
    trong khi primary cũ vẫn đang nhận ghi từ app ở AZ của nó.
- Chống split-brain ([14-distributed-systems.md](14-distributed-systems.md)):
  - *Quorum/consensus*: cần đa số node đồng ý mới bầu được leader. Bên thiểu số biết mình không
    được ghi.
  - *Fencing*: chặn hẳn node cũ.
    - STONITH ("shoot the other node in the head"): tắt nguồn node cũ.
    - Fencing token: một số tăng dần cấp cho mỗi leader. Storage từ chối lệnh ghi mang token cũ.

*Cái giá của failover*
- ⚠️ Failover DB dùng replication async có thể **mất dữ liệu** chưa kịp sao chép (RPO > 0, module
  2.6).
  - Async nghĩa là primary báo commit xong mà không chờ replica nhận được.
- ⚠️ Client phải kết nối lại đúng chỗ mới. Những thứ còn giữ địa chỉ cũ:
  - DNS TTL: resolver còn cache IP cũ tới khi hết TTL.
  - Connection pool giữ kết nối cũ.
  - JVM cache kết quả DNS.
  - Persistent connection của PHP.

*Multi-AZ*
- App chạy ở ít nhất 2 AZ, đứng sau LB.
- DB có standby ở AZ khác.
- Đủ capacity để mất một AZ vẫn chịu được.
  - Ví dụ: chạy 3 AZ thì 2 AZ còn lại phải gánh được 100% tải, tức mỗi AZ phải gánh được 50%.

*Cascading failure*
- *Cascading failure* (sự cố lan truyền) là khi một phần hỏng kéo các phần khác hỏng theo.
- *Little's law*: số request đang xử lý cùng lúc = tốc độ request đến × thời gian xử lý mỗi
  request.
- Chuỗi kinh điển với PHP-FPM:
  1. API vận chuyển bình thường trả trong 200 ms, bỗng chậm lên 30 giây.
  2. Mỗi worker PHP-FPM gọi API đó bị giữ 30 giây.
  3. Với 50 request/giây, lúc bình thường cần 50 × 0,2 = 10 worker. Giờ cần 50 × 30 = 1.500
     worker, trong khi pool chỉ có vài chục.
  4. Pool cạn. Mọi request khác, kể cả trang chủ không hề gọi API vận chuyển, phải xếp hàng rồi
     timeout.

*Graceful degradation*
- *Graceful degradation*: dependency phụ chết thì hệ thống vẫn chạy, chỉ với chức năng giảm bớt.
  - Tắt tính năng phụ, ví dụ khung gợi ý sản phẩm.
  - Trả dữ liệu cache cũ.
  - *Kill switch* bằng feature flag: công tắc tắt tính năng ngay, không cần deploy.
- Các cơ chế bảo vệ, chi tiết ở [14-distributed-systems.md](14-distributed-systems.md):
  - Timeout.
  - Retry có backoff + jitter: chờ tăng dần giữa các lần thử, cộng thêm một khoảng ngẫu nhiên để
    các client không retry cùng lúc.
  - *Circuit breaker*: lỗi nhiều thì ngừng gọi dependency một lúc.
  - *Bulkhead*: chia tài nguyên riêng cho từng dependency, để một cái chậm không ăn hết tài nguyên.
  - Rate limit.
  - *Load shedding*: chủ động từ chối bớt request khi quá tải.

**Đọc**
- SRE book: [Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)
- Amazon Builders' Library: [Timeouts, retries and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/), [Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)
- SRE Workbook: [Managing Load](https://sre.google/workbook/managing-load/)

**Nắm chắc khi**
- [ ] Giải thích được bằng Little's law vì sao API vận chuyển chậm từ 200 ms lên 30 giây làm sập cả trang chủ
- [ ] Liệt kê được tính năng nào của hệ thống mình tắt được khi dependency phụ chết, và cơ chế tắt

#### 2.6 Backup, RPO và RTO

**Vì sao cần học:** Backup là lớp bảo vệ cuối cùng trước xoá nhầm, ransomware và bug làm hỏng
dữ liệu. "Replica có phải backup không" và "RPO/RTO của hệ thống bạn là bao nhiêu" rất hay gặp.
Trả lời bằng con số đo được khác hẳn trả lời bằng con số mong muốn.

**Học gì**

*RPO và RTO*

| | RPO (Recovery Point Objective) | RTO (Recovery Time Objective) |
|---|---|---|
| Nghĩa | Mất tối đa bao nhiêu **dữ liệu**, tính theo thời gian | Mất tối đa bao lâu để **khôi phục dịch vụ** |
| Ví dụ | Chỉ backup mỗi đêm thì có thể mất tới 24 giờ dữ liệu | Restore mất 3 giờ thì RTO ít nhất 3 giờ |

- Cả hai càng nhỏ càng đắt.

*Các cách backup*
- Full: sao toàn bộ.
- Incremental: chỉ phần thay đổi từ lần backup gần nhất.
- Differential: phần thay đổi từ lần full gần nhất.
- Snapshot đĩa.
- *PITR* (point-in-time recovery): khôi phục về một thời điểm bất kỳ, bằng backup cộng với log thay
  đổi (WAL của Postgres, binlog của MySQL) ([03-database-sql.md](03-database-sql.md)).
  - Ví dụ: lỡ `DROP TABLE` lúc 14:05 thì restore về 14:04:59.

*Để backup sống sót*
- Quy tắc 3-2-1: 3 bản, trên 2 loại phương tiện, 1 bản ở nơi khác.
- Backup ở **tài khoản hoặc region khác**, và không xoá được bằng cùng credential.
  - Dùng *immutable backup* hoặc *object lock*: không ai xoá được trước khi hết hạn giữ.
  - Chống ransomware, và chống cả chính mình xoá nhầm.
- Mã hoá backup, kiểm soát ai được restore.

*Hai bẫy*
- ⚠️ **Backup chưa từng restore thử = chưa có backup.**
  - Restore thử tự động định kỳ.
  - Đo thời gian restore, vì đó là một phần của RTO.
- ⚠️ Replication không phải backup: `DROP TABLE` được sao chép sang replica ngay lập tức.

**Đọc**
- [AWS: Disaster Recovery of Workloads](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html): phần định nghĩa RPO/RTO
- MySQL PITR: xem module 3.5 của [03-database-sql.md](03-database-sql.md)

**Nắm chắc khi**
- [ ] Nói được RPO và RTO thực tế (không phải mong muốn) của hệ thống mình, và dựa vào số đo nào
- [ ] Kể được cách một kẻ tấn công có quyền admin tài khoản cloud vẫn không xoá được backup

#### 2.7 Tầng PHP: quan sát PHP-FPM và Laravel

**Vì sao cần học:** Module riêng cho người làm PHP. Mô hình *shared-nothing* của PHP-FPM (mỗi
request chạy trong một worker, không giữ gì lại sau request) làm nhiều thứ khác với Java/Go:
không có process sống lâu để giữ counter trong RAM, và worker là tài nguyên hữu hạn. Câu "APM báo
nhanh mà người dùng thấy chậm" là câu đặc trưng của hệ thống PHP.

**Học gì**

*PHP-FPM là tài nguyên cần đo theo USE*
- PHP-FPM có một *master* process và một pool worker, tối đa `pm.max_children` worker. Mỗi worker
  xử lý một request một lúc.
- Bật `pm.status_path` để có trang trạng thái:
  - active/idle processes: số worker đang bận và đang rảnh.
  - `listen queue`: số request đang chờ vì hết worker.
  - `max children reached`: số lần pool chạm trần.
  - Xuất ra Prometheus bằng php-fpm_exporter.
- ⚠️ `max children reached` tăng và `listen queue` > 0 là tín hiệu saturation. Request đang xếp
  hàng trước khi PHP chạy, nên APM không thấy phần chờ này.
  - *APM* (application performance monitoring) là công cụ đo chạy bên trong code. Nó chỉ bắt đầu
    đo khi PHP đã nhận request.
  - Ví dụ: Nginx nhận request, chờ 4,8 giây mới có worker rảnh, PHP chạy 200 ms. APM báo 200 ms,
    người dùng thấy 5 giây.
- Các setting khác của FPM:
  - `ping.path`: endpoint health check của FPM.
  - `request_slowlog_timeout` + `slowlog`: request chạy quá N giây thì in stack trace ra file
    slowlog.
  - `request_terminate_timeout`: giết request treo.
- ⚠️ `request_terminate_timeout` khác `max_execution_time` của PHP. Trên Linux, `max_execution_time`
  không tính thời gian chờ I/O (query DB, HTTP call). Request chờ API ngoài 60 giây vẫn không bị nó
  giết.

*Metric trong PHP*
- Mỗi request xong là state bị xoá sạch, nên counter không sống qua request.
- Cách làm:
  - Client Prometheus lưu counter ở APCu (bộ nhớ chia sẻ giữa các worker trên cùng máy) hoặc
    Redis.
  - Hoặc đẩy metric đi qua OTel hay StatsD.
- Đối chiếu: Java/Go có process sống lâu nên giữ metric trong RAM và expose `/metrics` trực tiếp.

*Log*
- Monolog với `JsonFormatter`, ghi ra `stderr` trong container.
- Thêm context cho log:
  - `Log::withContext()`: gắn field vào mọi log sau đó của channel hiện tại.
  - `Log::shareContext()`: gắn cho mọi channel.
  - `Context` facade (Laravel 11+): tự gắn vào log và **đi theo queue job** được dispatch.
- ⚠️ Làm mất stack trace:

  ```php
  catch (\Throwable $e) {
      Log::error($e->getMessage());                        // SAI: chỉ còn message
      Log::error('payment failed', ['exception' => $e]);   // ĐÚNG: có stack trace
  }
  ```

*Trace và error tracking*
- OpenTelemetry PHP: extension `opentelemetry` + gói auto-instrumentation cho Laravel, PDO, HTTP
  client.
- Truyền `traceparent` qua HTTP client và vào payload của job.
- Sentry cho Laravel: gắn release và user id, không gắn PII.

*Công cụ trong hệ Laravel*

| Công cụ | Dùng để | Lưu ý |
|---|---|---|
| Telescope | Xem chi tiết từng request, query, job khi debug | ⚠️ Chỉ dev/staging, ghi DB nặng |
| Pulse | Dashboard hiệu năng tự host | |
| Nightwatch | Giám sát dạng SaaS của Laravel | |
| Horizon | Quản lý và xem metric của queue Redis | |

*Queue và cron*
- Queue: alert theo **thời gian chờ** của job, tức tuổi của job cũ nhất đang chờ, không chỉ theo độ
  dài queue.
  - Vì sao: 10.000 job nhỏ xử lý hết trong 10 giây thì không sao. 50 job mà job cũ nhất đã chờ 30
    phút mới là vấn đề.
- Theo dõi thêm: `failed_jobs`, worker chết, job chạy quá timeout.
- Cron/scheduler: job không chạy thì không sinh ra log lỗi nào. Dùng *heartbeat* (còn gọi là
  *dead man's switch*):
  1. Job gửi một ping tới dịch vụ giám sát mỗi khi chạy xong.
  2. Dịch vụ không nhận được ping đúng hạn thì alert.

**Đọc**
- PHP: [FPM configuration](https://www.php.net/manual/en/install.fpm.configuration.php) (mục [pm.status_path](https://www.php.net/manual/en/install.fpm.configuration.php#pm.status-path), [ping.path](https://www.php.net/manual/en/install.fpm.configuration.php#ping.path), [request_slowlog_timeout](https://www.php.net/manual/en/install.fpm.configuration.php#request-slowlog-timeout))
- [php-fpm_exporter](https://github.com/hipages/php-fpm_exporter), [prometheus_client_php](https://github.com/PromPHP/prometheus_client_php) (phần storage adapter)
- OpenTelemetry: [PHP](https://opentelemetry.io/docs/languages/php/), [PHP zero-code instrumentation](https://opentelemetry.io/docs/zero-code/php/)
- Laravel: [Context](https://laravel.com/docs/context), [Pulse](https://laravel.com/docs/pulse), [Telescope](https://laravel.com/docs/telescope), [Horizon](https://laravel.com/docs/horizon)
- [Sentry for Laravel](https://docs.sentry.io/platforms/php/guides/laravel/)
- Runtime PHP-FPM: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Bật được status page của FPM, đọc được từng field và nói field nào dùng để alert
- [ ] Gắn được request id vào log của cả request HTTP lẫn queue job mà nó dispatch
- [ ] Giải thích được vì sao APM báo p99 = 200 ms trong khi người dùng thấy 5 giây, khi `listen queue` đang cao
- [ ] Thiết kế được alert cho queue: metric nào, ngưỡng nào, vì sao không dùng độ dài queue

#### 2.8 Postmortem

**Vì sao cần học:** Postmortem biến một sự cố thành bài học để nó không lặp lại. Ở mức senior,
bạn được kỳ vọng dẫn postmortem và viết action item thật sự có tác dụng. Hay bị hỏi: blameless là
gì, postmortem gồm những phần nào, 5 whys có hạn chế gì.

**Học gì**

*Blameless*
- *Postmortem* là bản phân tích viết sau sự cố.
- *Blameless* (không đổ lỗi): hỏi "hệ thống hay quy trình nào đã cho phép lỗi này xảy ra", không hỏi
  "ai làm sai".
  - Vì sao: người sợ bị phạt sẽ giấu thông tin, và lần sau không ai kể thật.
  - Ví dụ: thay vì "dev A chạy nhầm lệnh xoá trên production", hỏi "vì sao một lệnh xoá production
    chạy được mà không cần xác nhận".
- Viết cho mọi SEV1/SEV2, và cho *near-miss* (suýt thành sự cố) đáng học.

*Các phần của một postmortem*
- Tóm tắt.
- Ảnh hưởng: số user, số đơn, tiền, error budget đã tiêu.
- Timeline.
- Root cause và các yếu tố góp phần.
- Phát hiện bằng cách nào.
- Cái gì làm tốt, cái gì chưa tốt, chỗ nào là may mắn.
- Action items.

*5 whys*
- Hỏi "vì sao" lặp lại để đi từ triệu chứng tới nguyên nhân nằm ở hệ thống. Ví dụ:
  1. Vì sao API lỗi? Vì DB hết connection.
  2. Vì sao hết connection? Vì một query chạy 30 giây giữ connection.
  3. Vì sao query chậm? Vì thiếu index trên cột mới thêm.
  4. Vì sao thiếu index mà không ai phát hiện? Vì staging chỉ có 1.000 dòng.
  5. Vì sao? Vì không có bước kiểm tra query plan trên dữ liệu cỡ thật.
- ⚠️ Dễ đi theo một nhánh duy nhất, trong khi sự cố thật thường có nhiều yếu tố góp phần.
- ⚠️ Dừng ở "con người bất cẩn" là dừng quá sớm.

*Action item*
- Cụ thể, có owner, có hạn, có ticket. "Cẩn thận hơn" không phải action item.
- Ưu tiên theo loại:
  - Phát hiện sớm hơn, ví dụ thêm alert.
  - Giảm thiệt hại: kill switch, rollback nhanh.
  - Phòng ngừa: guardrail tự động, test.
- Theo dõi tỉ lệ hoàn thành action item. Không làm thì sự cố lặp lại.

**Đọc**
- SRE book: [Postmortem Culture](https://sre.google/sre-book/postmortem-culture/); SRE Workbook: [Postmortem Culture](https://sre.google/workbook/postmortem-culture/) (có ví dụ postmortem tốt và tồi)
- Atlassian: [Blameless postmortems](https://www.atlassian.com/incident-management/postmortem/blameless)
- [danluu/post-mortems](https://github.com/danluu/post-mortems): tuyển tập postmortem công khai, đọc 5–10 bài

**Nắm chắc khi**
- [ ] Viết được postmortem cho một sự cố thật, có 5 whys và ít nhất 3 action item cụ thể (bài tập 3)
- [ ] Đọc một postmortem công khai và chỉ ra action item nào yếu, vì sao

---

### Chặng 3: Senior 🔴

#### 3.1 Burn rate alert

**Vì sao cần học:** Đây là cách alert theo SLO mà Google SRE khuyến nghị, và là câu hỏi phân
biệt senior với mid. Nó giải quyết cùng lúc hai vấn đề của alert theo ngưỡng: page vì lỗi lặt vặt,
và page quá muộn khi có sự cố thật.

**Học gì**

*Vì sao không alert thẳng trên tỉ lệ lỗi*
- Alert kiểu "tỉ lệ lỗi > 0,1% trong 5 phút" thì quá nhạy: vài phút lỗi nhỏ đã page, dù chỉ tiêu
  một phần rất nhỏ budget.
- Tăng cửa sổ lên, ví dụ 1 ngày, thì quá chậm: sự cố lớn chạy cả tiếng mới báo.

*Burn rate là gì*
- *Burn rate* là tốc độ tiêu error budget so với tốc độ đều đặn.
  - Burn rate 1: tiêu hết budget đúng vào cuối kỳ.
  - Burn rate 10: hết budget sau 1/10 kỳ, tức 3 ngày nếu kỳ là 30 ngày.
- Cách tính: `burn rate = phần budget đã tiêu / (độ dài cửa sổ / độ dài kỳ)`.
  - Ví dụ: tiêu 2% budget trong 1 giờ, kỳ 30 ngày = 720 giờ. Burn rate = 0,02 / (1/720) = 14,4.
- Cách tính tương đương: `burn rate = tỉ lệ lỗi / (1 − SLO)`.
  - Ví dụ: SLO 99,9%, tỉ lệ lỗi hiện tại 1,44%. Burn rate = 0,0144 / 0,001 = 14,4.

*Multi-window, multi-burn-rate*
- Theo SRE Workbook, kỳ 30 ngày:

  | Tiêu bao nhiêu budget | Trong | Burn rate | Hành động |
  |---|---|---|---|
  | 2% | 1 giờ | 14,4 | Page |
  | 5% | 6 giờ | 6 | Page |
  | 10% | 3 ngày | 1 | Ticket |

- Mỗi điều kiện có thêm một cửa sổ ngắn, khoảng 1/12 cửa sổ dài (ví dụ 5 phút cho cửa sổ 1 giờ).
  Alert chỉ kêu khi cả hai cửa sổ cùng vượt ngưỡng.
  - Vì sao: khi sự cố đã hết, cửa sổ 1 giờ vẫn còn cao thêm một lúc, nhưng cửa sổ 5 phút xuống
    ngay. Nhờ vậy alert tắt nhanh khi đã hồi phục.

*Service ít traffic*
- ⚠️ Vài request lỗi đã là một tỉ lệ lớn. Ví dụ 20 request một giờ, 1 request lỗi là 5%.
- Cách xử lý:
  - *Synthetic traffic*: tự bắn request giả đều đặn để có đủ mẫu.
  - Gộp nhiều service nhỏ vào một SLO.
  - Dùng SLO theo thời gian thay vì theo request.

**Đọc**
- SRE Workbook: [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/): **đọc hết**, đi qua 6 cách alert từ tồi tới tốt

**Nắm chắc khi**
- [ ] Tự tính được burn rate 14,4 từ "2% budget trong 1 giờ, kỳ 30 ngày"
- [ ] Viết được cặp alert rule Prometheus cho cửa sổ 1h/5m và giải thích vai trò của cửa sổ ngắn

#### 3.2 Chi phí và sampling của observability

**Vì sao cần học:** Chi phí observability tăng theo traffic, và có thể thành một khoản lớn trong
hoá đơn. Senior cần biết khoản nào đắt, và giảm chi phí thế nào mà vẫn điều tra được sự cố. Hay
bị hỏi: head-based và tail-based sampling khác nhau thế nào.

**Học gì**

*Log*
- Log là một trong những khoản observability đắt nhất, vì trả tiền ba lần:
  - Ingest: nhận dữ liệu vào.
  - Index: đánh chỉ mục để tìm được.
  - Lưu trữ.
- Cách giảm:
  - *Retention* theo tầng: giữ ngắn ở kho tìm nhanh, lâu hơn thì chuyển sang kho rẻ.
  - Không log body lớn.
  - Bỏ log debug ở production.
  - *Log sampling*: log mọi lỗi, chỉ giữ một phần log thành công khi traffic lớn.
  - Rate limit log lặp: cùng một lỗi lặp hàng nghìn lần mỗi phút thì chỉ ghi một phần.

*Trace sampling*
- *Sampling* nghĩa là chỉ giữ lại một phần trace.

| | Head-based | Tail-based |
|---|---|---|
| Quyết định lúc | Ngay đầu request, ví dụ giữ ngẫu nhiên 1% | Sau khi request xong |
| Ưu điểm | Rẻ | Giữ được mọi trace lỗi hoặc chậm |
| Nhược điểm | Có thể bỏ mất request lỗi hiếm | Tốn tài nguyên ở Collector, cần mọi span của một trace về cùng một Collector |

- Vì sao tail-based cần cùng Collector: nó quyết định dựa trên toàn bộ trace (có span nào lỗi
  không), nên phải nhìn thấy mọi span của trace đó.

*Metric*
- Chi phí tỉ lệ với số series.
- Cardinality (module 2.2) là khoản khó thấy nhất, vì chỉ một label mới có thể nhân số series lên
  hàng nghìn lần.

*Chọn backend log*

| | Loki | Elasticsearch |
|---|---|---|
| Index gì | Chỉ index label | Index nội dung |
| Chi phí | Rẻ | Đắt hơn |
| Tìm full-text | Chậm hơn | Nhanh |

*Hướng mới*
- *Continuous profiling* (Pyroscope, Parca): liên tục ghi lại hàm nào tốn CPU hay RAM trên
  production. Được coi như tín hiệu thứ tư, bên cạnh metric, trace, log.
- *Wide event*: observability như event có nhiều chiều. Thay vì nhiều dòng log rời, ghi một event
  mỗi request với rất nhiều field (user, route, gói dịch vụ, thời gian từng bước...).
  - Nhờ vậy hỏi được cả những câu chưa từng nghĩ tới lúc viết code, ví dụ "user gói Pro có chậm
    hơn user gói Free không".

**Đọc**
- OpenTelemetry: [Sampling](https://opentelemetry.io/docs/concepts/sampling/)
- Grafana Loki: [Label best practices](https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/)
- *Observability Engineering*: các chương về structured event và sampling

**Nắm chắc khi**
- [ ] Ước lượng được chi phí log mỗi tháng của hệ thống mình (GB/ngày × retention) và nêu 3 cách giảm
- [ ] Thiết kế được chính sách tail sampling: giữ gì, bỏ gì, và vì sao

#### 3.3 Disaster recovery và DR drill

**Vì sao cần học:** *DR* (disaster recovery) trả lời câu "cả region cloud hoặc cả datacenter mất
thì sao". Senior được hỏi chọn mức DR cho một yêu cầu RPO/RTO cụ thể và bảo vệ được chi phí. Kế
hoạch DR trên giấy mà chưa diễn tập thường hỏng đúng lúc cần.

**Học gì**

*Bốn mức DR*
- Đi từ trên xuống: chi phí tăng dần, RPO/RTO giảm dần.

| Mức | Cách làm | RPO/RTO |
|---|---|---|
| Backup & restore | Chỉ có backup ở region khác, dựng lại từ đầu khi cần | Giờ tới ngày |
| Pilot light | Dữ liệu replicate liên tục sang region DR, hạ tầng tối thiểu, app tắt | Chục phút tới giờ |
| Warm standby | Một bản thu nhỏ chạy đầy đủ, scale lên khi cần | Phút |
| Multi-site active-active | Nhiều region cùng phục vụ | Gần 0, đắt nhất |

- "Pilot light" là ngọn lửa mồi của bếp gas: chỉ phần cốt lõi (dữ liệu) luôn cháy, phần còn lại
  bật lên khi cần.
- Active-active khó về consistency: hai region cùng nhận ghi thì phải xử lý xung đột ghi.
- *IaC* (infrastructure as code: hạ tầng mô tả bằng code, như Terraform) là điều kiện để dựng lại
  nhanh ([19-devops-cloud.md](19-devops-cloud.md)).

*DR drill*
- Một buổi diễn tập thật gồm:
  1. Restore DB vào một môi trường riêng.
  2. Failover sang region DR.
  3. Đo RTO/RPO thật.
  4. Ghi lại bước thủ công, lỗi trong runbook, quyền còn thiếu.
- ⚠️ Kế hoạch chưa diễn tập hay hỏng ở những chỗ nhỏ:
  - Credential hết hạn.
  - DNS TTL dài.
  - Quota ở region DR thấp.
  - Phụ thuộc ẩn vào region chính. Ví dụ PSP (cổng thanh toán) chỉ whitelist IP của region chính,
    hoặc secret chỉ có ở một region.

**Đọc**
- [AWS: Disaster Recovery options in the cloud](https://docs.aws.amazon.com/whitepapers/latest/disaster-recovery-workloads-on-aws/disaster-recovery-options-in-the-cloud.html): đọc hết, có hình từng mức

**Nắm chắc khi**
- [ ] Chọn được mức DR cho hệ thống thanh toán RPO 1 phút, RTO 30 phút và bảo vệ được chi phí
- [ ] Viết được checklist một buổi DR drill, kể cả tiêu chí "đạt"

#### 3.4 Điều phối sự cố lớn

**Vì sao cần học:** Sự cố lớn thường thất bại vì hỗn loạn nhiều hơn vì thiếu kỹ năng debug: năm
người cùng sửa một chỗ, không ai báo khách, không ai ghi lại đã làm gì. Senior được kỳ vọng biết
vai trò incident commander và cách giao tiếp trong sự cố.

**Học gì**

*Mức SEV*
- Mỗi công ty tự định nghĩa. Một cách phổ biến:

| Mức | Nghĩa |
|---|---|
| SEV1 | Dịch vụ chính ngừng, hoặc mất hay rò dữ liệu |
| SEV2 | Tính năng quan trọng hỏng, có workaround |
| SEV3 | Ảnh hưởng nhỏ |

- Nghi ngờ thì chọn mức cao hơn. Hạ mức sau thì dễ, gọi thêm người muộn thì mất thời gian.

*Vai trò*

| Vai | Làm gì |
|---|---|
| **Incident commander (IC)** | Điều phối, ra quyết định, không tự tay debug |
| Operations/tech lead | Điều tra và thực hiện thay đổi |
| Communications lead | Báo nội bộ, cập nhật status page, hỗ trợ bộ phận chăm sóc khách |
| Scribe | Ghi timeline: thời điểm, quyết định, lệnh đã chạy |

- Sự cố nhỏ: một người kiêm nhiều vai.
- Sự cố lớn: tách vai, để người debug không bị hỏi liên tục.

*Giao tiếp*
- Một kênh chung cho sự cố.
- Cập nhật định kỳ, ví dụ 30 phút một lần, kể cả khi chưa có gì mới.
- Mỗi bản cập nhật gồm:
  - Ảnh hưởng hiện tại.
  - Đang làm gì.
  - Lần cập nhật sau lúc nào.
- *Status page* (trang công khai báo tình trạng dịch vụ): nói thật, không đổ lỗi, không hứa thời
  gian khi chưa chắc.
- Sự cố bảo mật hoặc rò dữ liệu có thêm nghĩa vụ pháp lý và thông báo
  ([10-security.md](10-security.md)).

**Đọc**
- [PagerDuty Incident Response](https://response.pagerduty.com/): phần vai trò (*Incident Commander*, *Scribe*...) và *Being an Incident Commander*
- SRE Workbook: [Incident Response](https://sre.google/workbook/incident-response/)
- [Atlassian Incident Management Handbook](https://www.atlassian.com/incident-management/handbook)
- [incident.io guide](https://incident.io/guide)

**Nắm chắc khi**
- [ ] Viết được một bản cập nhật sự cố cho khách hàng và một bản cho nội bộ, cùng một sự cố
- [ ] Nói được IC làm gì trong 10 phút đầu, và khi nào IC phải chuyển giao vai

#### 3.5 Resilience testing

**Vì sao cần học:** Chỉ biết chắc hệ thống chịu được lỗi khi đã thử gây ra lỗi đó. Hay bị hỏi
"bắt đầu chaos engineering thế nào cho an toàn", và red flag là trả lời như thể cứ tắt bừa server
production.

**Học gì**

*Chaos engineering là gì*
- *Chaos engineering* là chủ động gây lỗi có kiểm soát để kiểm chứng một giả thuyết dạng "hệ thống
  chịu được X".
- Các lỗi hay thử:
  - Giết instance.
  - Thêm latency.
  - Dependency trả lỗi.
  - Đầy đĩa.
  - Mất một AZ.

*Quy trình*
1. Xác định *steady state*: trạng thái bình thường đo được, ví dụ tỉ lệ đặt hàng thành công 99,5%.
2. Đặt giả thuyết, ví dụ "mất một node Redis thì steady state không đổi".
3. Chạy thí nghiệm với **blast radius nhỏ**. Blast radius là phạm vi bị ảnh hưởng: ít người dùng,
   ít instance.
4. Quan sát.
5. Mở rộng dần.

- Điều kiện an toàn:
  - Có nút dừng khẩn cấp.
  - Bắt đầu ở staging. Chỉ lên production khi observability và rollback đã tốt.

*Công cụ*
- Chaos Monkey: giết instance ngẫu nhiên.
- Chaos Mesh, LitmusChaos: gây lỗi trên Kubernetes.
- AWS Fault Injection Service.
- Toxiproxy: proxy đứng giữa app và dependency để giả lập mạng xấu khi test (thêm latency, cắt kết
  nối).

*Game day*
- Buổi diễn tập có kế hoạch, cả team tham gia.
- Giả lập sự cố: region chết, DB failover, khoá credential.
- Thực hành quy trình incident, kiểm tra runbook và alert.
- Kết quả là một danh sách lỗ hổng cần sửa.

**Đọc**
- [Principles of Chaos Engineering](https://principlesofchaos.org/)
- [Toxiproxy](https://github.com/Shopify/toxiproxy): README, thử với Redis/MySQL local
- [AWS Fault Injection Service](https://aws.amazon.com/fis/)

**Nắm chắc khi**
- [ ] Thiết kế được thí nghiệm chaos đầu tiên cho hệ thống mình: giả thuyết, blast radius, tiêu chí dừng
- [ ] Dùng Toxiproxy thêm 5 giây latency vào Redis và quan sát app hành xử thế nào

#### 3.6 Công cụ và kiến trúc observability stack

**Vì sao cần học:** Senior thường phải chọn hoặc sắp xếp lại stack observability: tự host hay
SaaS, dùng vendor nào. Quyết định sai tốn tiền nhiều năm, hoặc buộc phải migrate khi vendor ngừng
sản phẩm.

**Học gì**

*Bảng công cụ*

| Nhu cầu | Mã nguồn mở / tự host | SaaS |
|---|---|---|
| Metric + dashboard | Prometheus + Grafana; VictoriaMetrics, Thanos/Mimir cho quy mô lớn | Datadog, New Relic, Grafana Cloud |
| Log | ELK/EFK (Elasticsearch/OpenSearch + Logstash/Fluentd/Fluent Bit + Kibana), Loki | Datadog Logs, CloudWatch Logs |
| Tracing | Jaeger, Grafana Tempo, Zipkin; OpenTelemetry Collector | Datadog APM, New Relic, Honeycomb |
| Error tracking | Sentry (tự host được) | Sentry, Bugsnag, Rollbar |
| Alert, on-call | Alertmanager | PagerDuty, incident.io, Grafana Cloud IRM, Jira Service Management |
| Uptime / synthetic | Blackbox exporter | Pingdom, Checkly, Datadog Synthetics |

*OTel Collector làm lớp trung gian*
- App gửi mọi tín hiệu tới Collector, Collector gửi tiếp tới backend. Lợi ích:
  - Đổi backend không phải sửa app.
  - Lọc PII ở một chỗ.
  - Sampling tập trung.
- Hai cách triển khai:
  - Agent: Collector chạy cạnh app, trên từng node.
  - Gateway: một cụm Collector tập trung nhận từ nhiều nơi.

*Giám sát chính hệ thống giám sát*
- ⚠️ Monitoring chạy chung hạ tầng với hệ thống được giám sát thì sập cùng lúc, và không ai được
  báo. Cần:
  - Ít nhất một kiểm tra từ bên ngoài: *synthetic check*, tức một dịch vụ ở nơi khác gọi thử vào
    hệ thống như người dùng.
  - Alert cho chính hệ thống alert: *watchdog*, một alert được thiết kế luôn kêu. Khi nó ngừng tới
    nơi nhận thì biết đường alert đã hỏng.
- ⚠️ Chọn vendor on-call thì xem cả vòng đời sản phẩm (ví dụ Opsgenie, Grafana OnCall OSS ở module
  2.4).

**Đọc**
- OpenTelemetry: [Collector](https://opentelemetry.io/docs/collector/) (phần deployment pattern: agent và gateway)
- Prometheus: [Alertmanager](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Grafana Cloud IRM](https://grafana.com/docs/grafana-cloud/alerting-and-irm/irm/)

**Nắm chắc khi**
- [ ] Vẽ được observability stack cho một hệ thống Laravel 10 service: app → Collector → backend, alert → on-call
- [ ] Nói được hệ thống sẽ biết thế nào nếu chính Prometheus hoặc Alertmanager chết

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. SLI, SLO, SLA khác nhau thế nào?** (1.1)
- Ý phải có: số đo, mục tiêu nội bộ, cam kết hợp đồng có phạt; SLA lỏng hơn SLO
- Điểm cộng: SLI đo từ góc người dùng; ví dụ cụ thể có cửa sổ thời gian
- Red flag: "SLA là uptime server"

**2. Liveness và readiness probe khác nhau thế nào?** (1.2)
- Ý phải có: fail liveness thì restart, fail readiness thì bỏ khỏi LB; liveness không kiểm tra dependency
- Điểm cộng: kịch bản DB chậm làm restart hàng loạt; startup probe cho app khởi động chậm

**3. Log có cấu trúc là gì? Correlation id dùng để làm gì?** (1.3)
- Ý phải có: log JSON có field; một id đi theo request qua mọi service và queue để lần theo
- Điểm cộng: gắn trace id vào log; mask PII ở tầng logger

**4. Production trả 500 hàng loạt ngay sau deploy. 15 phút đầu bạn làm gì?** (1.4)
- Ý phải có: xác nhận ảnh hưởng qua dashboard; mở kênh sự cố; rollback trước, debug sau; cập nhật định kỳ
- Điểm cộng: rollback không hết lỗi thì xét config, migration, hạ tầng; sau đó hỏi vì sao canary/test không bắt được
- Red flag: SSH vào production sửa code trực tiếp

**5. Những gì không được ghi vào log?** (1.3)
- Ý phải có: mật khẩu, token, header `Authorization`, số thẻ, OTP, giấy tờ tuỳ thân
- Điểm cộng: mask bằng processor chung; log của LLM prompt cũng chứa PII ([23-ai-llm-backend.md](23-ai-llm-backend.md))

**6. Replica có phải là backup không?** (2.6)
- Ý phải có: không, lệnh xoá nhầm được sao chép ngay; cần backup + PITR
- Điểm cộng: backup phải restore thử; backup ở tài khoản khác, immutable

### 🟡 Mid

**7. Error budget là gì, dùng thế nào?** (2.1)
- Ý phải có: 1 − SLO; còn budget thì được mạo hiểm, hết thì đóng băng tính năng
- Điểm cộng: policy phải được lãnh đạo ký trước; tính theo request hoặc theo thời gian
- Red flag: coi error budget là chỉ tiêu phải "tiêu hết"

**8. RPO và RTO là gì? Cho ví dụ.** (2.6)
- Ý phải có: lượng dữ liệu chấp nhận mất, thời gian chấp nhận ngừng; ví dụ gắn với nghiệp vụ
- Điểm cộng: thời gian restore đo được là một phần RTO; RPO phụ thuộc replication lag

**9. Counter, gauge, histogram khác nhau thế nào? Vì sao không dùng `user_id` làm label?** (2.2)
- Ý phải có: định nghĩa ba loại; `rate()` trên counter; histogram gộp được giữa instance; cardinality nổ
- Điểm cộng: summary không gộp được; route template thay URL thật; id đưa vào trace/log

**10. RED và USE là gì?** (2.2)
- Ý phải có: RED cho service, USE cho tài nguyên; ví dụ cụ thể cho mỗi cái
- Điểm cộng: áp USE cho PHP-FPM pool và DB connection pool

**11. Trace id được truyền qua các service thế nào?** (2.3)
- Ý phải có: header `traceparent` (W3C), SDK tự inject/extract; qua queue thì đặt vào message
- Điểm cộng: chỗ hay đứt trace (goroutine, thread pool, job); OTel Collector

**12. Vì sao nên alert theo triệu chứng, không theo nguyên nhân?** (2.4)
- Ý phải có: người dùng không bị ảnh hưởng thì không cần đánh thức ai; nguyên nhân thì nhiều và hay báo sai
- Điểm cộng: ngoại lệ là nguyên nhân chắc chắn dẫn tới sự cố (đĩa sắp đầy); alert fatigue

**13. Alert kêu 50 lần mỗi đêm, team bắt đầu tắt tiếng điện thoại. Làm gì?** (2.4)
- Ý phải có: thống kê alert nào kêu nhiều và có hành động không; xoá hoặc hạ thành ticket; gom nhóm; thêm `for:`
- Điểm cộng: chuyển sang burn rate alert; mục tiêu số page mỗi ca; review alert hằng tuần
- Red flag: tăng ngưỡng cho tất cả mà không phân tích

**14. APM báo p99 200 ms nhưng người dùng than trang chậm 5 giây. Vì sao?** (2.7)
- Ý phải có: thời gian chờ trước khi vào PHP không nằm trong APM; FPM hết worker, `listen queue` cao
- Điểm cộng: đo latency ở LB/Nginx; `max children reached`; dependency chậm giữ worker
- Red flag: tin APM tuyệt đối

**15. Postmortem blameless là gì? Gồm những phần nào?** (2.8)
- Ý phải có: tìm yếu tố hệ thống, không tìm người; các phần chính; action item có owner và hạn
- Điểm cộng: 5 whys và hạn chế của nó; theo dõi tỉ lệ hoàn thành action item

**16. Kể một sự cố bạn đã xử lý.** (1.4, 2.8)
- Ý phải có: ảnh hưởng, phát hiện, root cause không dừng ở bề mặt, khắc phục, phòng ngừa lâu dài
- Điểm cộng: có số liệu; nói được mình làm gì khác nếu gặp lại
- Red flag: đổ lỗi cho người khác; không có phần phòng ngừa

**17. Một cron job quan trọng không chạy ba ngày mà không ai biết. Thiết kế giám sát thế nào?** (2.7)
- Ý phải có: không có lỗi thì không có log; cần heartbeat, alert khi không nhận được tín hiệu
- Điểm cộng: `onOneServer()`/lock để không chạy trùng; đo cả thời gian chạy và số bản ghi xử lý

### 🔴 Senior

**18. Burn rate alert hoạt động thế nào?** (3.1)
- Ý phải có: tốc độ tiêu budget; nhiều cửa sổ; ví dụ 14,4 trong 1 giờ; cửa sổ ngắn để tắt nhanh
- Điểm cộng: tự tính được con số; vấn đề service ít traffic

**19. So sánh các mức DR: backup & restore, pilot light, warm standby, active-active.** (3.3)
- Ý phải có: bốn mức với RPO/RTO và chi phí tương ứng
- Điểm cộng: active-active khó ở consistency và xử lý xung đột ghi; DR drill; phụ thuộc ẩn vào region chính

**20. Head-based và tail-based sampling khác nhau thế nào?** (3.2)
- Ý phải có: quyết định ở đầu so với ở cuối; đánh đổi chi phí và khả năng giữ trace lỗi
- Điểm cộng: tail sampling cần gom mọi span của trace về một Collector; kết hợp cả hai

**21. Split-brain là gì, chống thế nào?** (2.5)
- Ý phải có: hai node cùng nghĩ mình là primary và cùng nhận ghi; quorum, fencing
- Điểm cộng: fencing token; khi nào chọn failover thủ công

**22. Một dependency ngoài chậm từ 200 ms lên 30 giây kéo sập cả hệ thống, kể cả trang không liên quan. Vì sao, phòng thế nào?** (2.5)
- Ý phải có: worker/connection bị giữ, pool cạn theo Little's law; timeout, circuit breaker, bulkhead
- Điểm cộng: gọi qua queue nếu không cần kết quả ngay; fallback; alert theo latency của dependency; với PHP-FPM mọi worker là chung một pool nên bulkhead phải làm bằng pool FPM riêng hoặc tách service

**23. Thiết kế DR cho hệ thống thanh toán: RPO 1 phút, RTO 30 phút.** (3.3)
- Ý phải có: backup & restore không đạt; warm standby ở region khác, replication liên tục, giám sát lag dưới 1 phút
- Điểm cộng: runbook failover, DNS TTL thấp, IaC, diễn tập đo RTO thật; PSP có whitelist IP region chính không
- Red flag: không hỏi chi phí và tần suất diễn tập

**24. DB đầy đĩa, ghi bắt đầu lỗi. Làm gì?** (1.4, 2.4)
- Ý phải có: mitigate bằng tăng dung lượng hoặc dọn thứ an toàn (binlog đã backup và replica không cần, log, bảng tạm); không xoá file dữ liệu bừa bãi
- Điểm cộng: nguyên nhân hay gặp (bảng log phình, replication slot bị bỏ quên, transaction dài); alert `predict_linear`

**25. Service bị OOM kill mỗi 2–3 ngày. Xử lý thế nào?** (2.2)
- Ý phải có: mitigate bằng rolling restart có kiểm soát; alert theo xu hướng memory; so memory với các deploy
- Điểm cộng: heap dump/profile hai thời điểm; với PHP worker sống lâu (queue, Octane) dùng `--max-jobs`/`--memory` như biện pháp tạm ([17-performance.md](17-performance.md))

**26. Vai trò incident commander là gì?** (3.4)
- Ý phải có: điều phối, quyết định, không tự debug; giữ nhịp cập nhật
- Điểm cộng: tách vai comms và scribe; chuyển giao IC khi sự cố kéo dài

**27. Chaos engineering bắt đầu thế nào cho an toàn?** (3.5)
- Ý phải có: steady state, giả thuyết, blast radius nhỏ, nút dừng; bắt đầu ở staging
- Điểm cộng: điều kiện tiên quyết là observability và rollback tốt; game day
- Red flag: "tắt ngẫu nhiên server production xem sao"

**28. Bạn chọn stack observability và on-call thế nào cho một công ty 30 kỹ sư?** (3.6)
- Ý phải có: đánh đổi tự host và SaaS theo chi phí, người vận hành, dữ liệu nhạy cảm; OTel để không khoá vendor
- Điểm cộng: xét vòng đời sản phẩm (Opsgenie đóng cửa, Grafana OnCall OSS archive); kiểm tra từ bên ngoài; chi phí log là khoản lớn nhất

---

## Bài tập tự làm

1. Định nghĩa 3 SLO cho một hệ thống bạn đang làm (một user journey mỗi SLO): SLI, cách đo, mục tiêu, error budget mỗi tháng, error budget policy, và cặp burn rate alert cho SLO quan trọng nhất.
2. Viết middleware (PHP, Java hoặc Go) sinh hoặc nhận request id từ header, gắn vào mọi log dạng JSON và truyền sang HTTP call tiếp theo. Bản PHP: dùng `Context` của Laravel hoặc Monolog processor, và chứng minh request id xuất hiện trong log của queue job được dispatch.
3. Viết postmortem cho một sự cố thật bạn từng gặp (hoặc sự cố xoá DB dev do test chạy `TRUNCATE`), có timeline, 5 whys và ít nhất 3 action item cụ thể có owner và hạn.
4. Viết runbook cho alert "tỉ lệ lỗi 5xx của API thanh toán > 2% trong 5 phút": ý nghĩa, ảnh hưởng, dashboard, bước chẩn đoán, bước giảm thiệt hại, escalate cho ai.
5. Liệt kê metric Prometheus cần có cho một queue worker Laravel (tên metric, loại, label) và chỉ ra label nào sẽ gây vấn đề cardinality. Nói rõ bạn lưu metric ở đâu khi mỗi process PHP không giữ state.
6. Bật status page của PHP-FPM trên máy local, dùng `ab` hoặc `wrk` bắn tải vượt `pm.max_children`, ghi lại `listen queue` và `max children reached` thay đổi thế nào, và so với latency đo từ phía client.

> Nộp bài vào đây để được review.
