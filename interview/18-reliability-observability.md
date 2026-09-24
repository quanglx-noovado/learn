# 18. Reliability và observability

> [← Mục lục](README.md) · Phạm vi: SLI/SLO/SLA và error budget, high availability, disaster recovery, observability (log, metric, trace), alerting và on-call, quản lý sự cố và postmortem, resilience testing, công cụ phổ biến.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

## Bản đồ nhanh

**SLI, SLO, SLA**
- [ ] 🟢 SLI, SLO, SLA khác nhau thế nào
- [ ] 🟡 Chọn SLI tốt (theo trải nghiệm người dùng)
- [ ] 🟡 Error budget và dùng nó để quyết định deploy
- [ ] 🔴 Burn rate alert

**High availability**
- [ ] 🟢 Redundancy, loại bỏ SPOF
- [ ] 🟡 Failover (tự động vs thủ công), split-brain
- [ ] 🟢 Health check: liveness vs readiness; ⚠️ health check sâu
- [ ] 🟡 Multi-AZ
- [ ] 🟡 Graceful degradation, timeout, retry, circuit breaker, bulkhead (chi tiết ở [14](14-distributed-systems.md))

**Disaster recovery**
- [ ] 🟡 RPO, RTO
- [ ] 🟡 Backup strategy: full/incremental, PITR, 3-2-1, backup ngoài tài khoản
- [ ] ⚠️ Backup chưa restore thử = chưa có backup
- [ ] 🔴 Các mức DR: backup & restore, pilot light, warm standby, active-active
- [ ] 🔴 DR drill

**Observability**
- [ ] 🟢 Ba trụ cột: log, metric, trace; monitoring vs observability
- [ ] 🟢 Log có cấu trúc, log level, correlation/request id
- [ ] 🟡 Log sampling, chi phí; ⚠️ không log PII/secret
- [ ] 🟡 Metric: counter, gauge, histogram (summary)
- [ ] ⚠️ Cardinality của label
- [ ] 🟡 RED, USE, four golden signals
- [ ] 🟡 Tracing: OpenTelemetry, span, trace id, context propagation
- [ ] 🔴 Trace sampling: head-based vs tail-based
- [ ] 🟡 Ba cái bổ trợ nhau thế nào (exemplar, trace id trong log)

**Alerting và on-call**
- [ ] 🟢 Alert theo triệu chứng, không theo nguyên nhân
- [ ] ⚠️ Alert fatigue
- [ ] 🟡 Runbook
- [ ] 🟡 On-call: rotation, escalation, handover

**Incident management**
- [ ] 🟢 Quy trình: phát hiện → phân loại → giảm thiệt hại → khắc phục → postmortem
- [ ] 🟡 Mức độ nghiêm trọng (SEV)
- [ ] 🔴 Incident commander và các vai trò
- [ ] 🟡 Giao tiếp trong sự cố (nội bộ, khách hàng, status page)
- [ ] 🟢 Mitigate trước, root cause sau; rollback
- [ ] 🟡 Postmortem blameless, template, 5 whys, action items
- [ ] 🟢 Chuẩn bị câu chuyện sự cố của chính mình

**Resilience testing**
- [ ] 🔴 Chaos engineering (đại ý)
- [ ] 🔴 Game day

**Công cụ**
- [ ] 🟢 Prometheus + Grafana, ELK/Loki, Jaeger/Tempo, Sentry, Datadog/New Relic

## Chi tiết

### SLI, SLO, SLA

- [ ] **Định nghĩa** 🟢

  | | Là gì | Ví dụ | Ai quan tâm |
  |---|---|---|---|
  | SLI (indicator) | Số đo một khía cạnh chất lượng | Tỉ lệ request thành công; tỉ lệ request < 300 ms | Kỹ sư |
  | SLO (objective) | Mục tiêu nội bộ cho SLI trong một khoảng thời gian | 99,9% request thành công trong 30 ngày | Team, product |
  | SLA (agreement) | Cam kết hợp đồng với khách, có phạt/đền bù | 99,5%/tháng, vi phạm hoàn 10% phí | Khách hàng, pháp lý |

  - SLA nên lỏng hơn SLO để có vùng đệm; SLO chặt hơn để phát hiện sớm
- [ ] **Chọn SLI tốt** 🟡
  - Đo từ góc người dùng: tốt nhất ở LB/gateway hoặc client, không phải CPU server
  - Dạng tỉ lệ: `số sự kiện tốt / tổng số sự kiện`. Availability (non-5xx), latency (tỉ lệ dưới ngưỡng), freshness (dữ liệu cập nhật trong N phút) cho pipeline, correctness
  - Mỗi user journey quan trọng (đăng nhập, thanh toán) một SLO; không cần SLO cho mọi endpoint
  - ⚠️ 100% không phải mục tiêu: đắt vô hạn, và người dùng không phân biệt được với 99,99% vì mạng của họ còn kém hơn
- [ ] **Error budget** 🟡
  - Budget = 1 − SLO. SLO 99,9% trong 30 ngày → được phép "hỏng" 0,1% ≈ 43 phút downtime (hoặc 0,1% request lỗi)
  - Dùng để quyết định:
    - Còn budget → được deploy, thử nghiệm, chấp nhận rủi ro
    - Hết budget → đóng băng tính năng mới, dồn sức cho reliability tới khi hồi phục
  - Biến tranh cãi "dev muốn nhanh, ops muốn ổn định" thành con số chung mà hai bên đã đồng ý
  - ⚠️ Error budget policy phải được lãnh đạo đồng ý trước; không thì hết budget vẫn bị ép ra tính năng
- [ ] **Burn rate alert** 🔴
  - Burn rate = tốc độ tiêu budget so với tốc độ "đều đặn". Burn rate 1 = tiêu hết đúng vào cuối kỳ
  - Alert theo nhiều cửa sổ: ví dụ burn rate 14,4 trong 1 giờ (tiêu 2% budget của kỳ 30 ngày trong 1 giờ) → page ngay; burn rate thấp kéo dài nhiều giờ → tạo ticket
  - Kết hợp cửa sổ dài và cửa sổ ngắn để vừa chắc chắn vừa tắt alert nhanh khi đã hồi phục (theo Google SRE Workbook)

### High availability

- [ ] **Redundancy và SPOF** 🟢: mọi thành phần có ít nhất hai bản ở hai failure domain khác nhau (máy, rack, AZ). Liệt kê SPOF: DB primary, LB, Redis, cron server, DNS, chứng chỉ TLS hết hạn, một người duy nhất biết vận hành
- [ ] **Failover** 🟡
  - Tự động: nhanh, nhưng rủi ro failover nhầm (mạng chập chờn → promote replica trong khi primary vẫn sống → **split-brain**, hai nơi cùng nhận ghi)
  - Chống split-brain: quorum/consensus (cần đa số để bầu leader), fencing (chặn primary cũ ghi: STONITH, fencing token)
  - Thủ công: an toàn hơn cho DB quan trọng nhưng chậm; cần runbook và diễn tập
  - Failover DB async replication có thể **mất dữ liệu** chưa kịp sao chép (RPO > 0)
  - ⚠️ Client phải kết nối lại đúng chỗ mới: DNS TTL, connection pool giữ kết nối cũ, cache DNS trong JVM
- [ ] **Health check** 🟢
  - **Liveness**: process còn sống không (không deadlock). Fail → restart
  - **Readiness**: sẵn sàng nhận traffic chưa (đã warm-up, đã kết nối DB). Fail → bỏ khỏi load balancer, không restart
  - ⚠️ Liveness kiểm tra DB: DB chậm một chút → mọi pod bị restart cùng lúc → sập toàn bộ. Liveness chỉ nên kiểm tra chính process
  - ⚠️ Readiness kiểm tra sâu mọi dependency: một dependency phụ chết → mọi instance "not ready" → mất toàn bộ service. Chỉ kiểm tra dependency bắt buộc
  - Chi tiết probe trên Kubernetes ở [19-devops-cloud.md](19-devops-cloud.md)
- [ ] **Multi-AZ** 🟡: app chạy ở ≥ 2 AZ sau load balancer; DB có standby ở AZ khác (ví dụ RDS Multi-AZ); đủ capacity để mất một AZ vẫn chịu được tải
- [ ] **Graceful degradation** 🟡: dependency phụ chết thì tắt tính năng phụ (gợi ý sản phẩm, đánh giá) thay vì cả trang lỗi; trả dữ liệu cache cũ; kill switch bằng feature flag
- [ ] Timeout, retry có backoff + jitter, circuit breaker, bulkhead, rate limit, load shedding — chi tiết ở [14-distributed-systems.md](14-distributed-systems.md)

### Disaster recovery

- [ ] **RPO và RTO** 🟡
  - RPO (Recovery Point Objective): mất tối đa bao nhiêu **dữ liệu** tính theo thời gian (RPO 5 phút = chấp nhận mất 5 phút dữ liệu cuối)
  - RTO (Recovery Time Objective): mất tối đa bao lâu để **khôi phục dịch vụ**
  - Mỗi hệ thống một mức khác nhau theo giá trị nghiệp vụ; RPO/RTO càng nhỏ càng đắt
- [ ] **Backup strategy** 🟡
  - Full + incremental/differential; snapshot đĩa; **PITR** (point-in-time recovery) bằng backup + WAL/binlog để khôi phục tới một thời điểm (ví dụ ngay trước câu `DELETE` lỡ tay)
  - Quy tắc 3-2-1: 3 bản, 2 loại phương tiện, 1 bản ở nơi khác
  - Backup ở **tài khoản/region khác**, không xoá được bởi cùng credential (immutable/object lock) — chống ransomware và chống chính mình xoá nhầm
  - Mã hoá backup; kiểm soát ai được restore
  - ⚠️ **Backup chưa từng restore thử = chưa có backup.** Kiểm tra restore định kỳ tự động, đo thời gian restore (đó chính là một phần RTO)
  - ⚠️ Replication không phải backup: `DROP TABLE` được sao chép sang replica ngay lập tức
- [ ] **Các mức DR** 🔴 (thứ tự tăng chi phí, giảm RPO/RTO)

  | Mức | Cách làm | RTO/RPO | Chi phí |
  |---|---|---|---|
  | Backup & restore | Chỉ có backup ở region khác; khi thảm hoạ thì dựng lại từ đầu | Giờ tới ngày | Thấp nhất |
  | Pilot light | Dữ liệu được replicate sang region DR; hạ tầng cốt lõi tối thiểu, app tắt; khi cần thì bật và scale | Chục phút tới giờ | Thấp |
  | Warm standby | Bản thu nhỏ đang chạy đầy đủ ở region DR; khi cần thì scale lên và chuyển traffic | Phút | Trung bình |
  | Multi-site active-active | Nhiều region cùng phục vụ | Gần 0 (tuỳ replication) | Cao nhất; khó về consistency |

  - Hạ tầng dạng code (IaC) là điều kiện để dựng lại nhanh — xem [19-devops-cloud.md](19-devops-cloud.md)
- [ ] **DR drill** 🔴
  - Diễn tập định kỳ: restore DB từ backup vào môi trường riêng, failover sang region DR, đo RTO/RPO thật
  - Ghi lại mọi bước thủ công, lỗi trong runbook, quyền truy cập thiếu; sửa và lặp lại
  - ⚠️ Kế hoạch DR chưa diễn tập thường hỏng ở chỗ nhỏ: credential hết hạn, DNS TTL dài, quota ở region DR thấp, phụ thuộc ẩn vào region chính

### Observability

- [ ] **Monitoring vs observability** 🟢
  - Monitoring: theo dõi những gì đã biết trước sẽ hỏng (dashboard, alert)
  - Observability: hỏi được những câu **chưa từng nghĩ tới** từ dữ liệu hệ thống phát ra ("vì sao chỉ khách hàng X ở Android bản 5.2 bị chậm?")
  - Ba trụ cột: log, metric, trace
- [ ] **Log** 🟢
  - **Structured log** (JSON): field có tên để lọc/tổng hợp (`level`, `msg`, `request_id`, `user_id`, `duration_ms`), không phải chuỗi tự do phải regex
  - Log level: `DEBUG` (dev), `INFO` (sự kiện nghiệp vụ bình thường), `WARN` (bất thường tự xử lý được), `ERROR` (thao tác thất bại, cần chú ý). ⚠️ Log `ERROR` cho lỗi validate của người dùng làm nhiễu alert
  - **Correlation/request id**: sinh ở edge (hoặc nhận từ header), gắn vào mọi log, truyền qua mọi service gọi tiếp và qua message queue → lần theo một request qua nhiều service
  - Log ra stdout, agent thu gom (12-factor)
  - 🟡 **Sampling**: log mọi lỗi, sample log thành công ở traffic lớn; giới hạn log lặp (rate limit log)
  - 🟡 **Chi phí**: log là một trong những khoản observability đắt nhất (ingest + index + lưu). Retention theo tầng; không log body request lớn; bỏ log debug ở production
  - ⚠️ **Không log PII và secret**: mật khẩu, token, số thẻ, OTP, CMND/CCCD, header `Authorization`. Mask ở tầng logger (có danh sách field cấm), không trông vào từng dev nhớ — xem [10-security.md](10-security.md)
  - Log ghi kèm context đủ để hiểu: log "failed" không có id, không có lý do là log vô dụng
  - **Đối chiếu:** PHP Monolog (Laravel `Log::withContext()`), Java SLF4J + Logback/Log4j2 với MDC, Go `log/slog` (thư viện chuẩn từ Go 1.21)
- [ ] **Metric** 🟡
  - Loại (theo Prometheus):

  | Loại | Là gì | Ví dụ | Cách dùng |
  |---|---|---|---|
  | Counter | Chỉ tăng (reset khi restart) | `http_requests_total` | Luôn dùng `rate()`/`increase()`, không nhìn giá trị tuyệt đối |
  | Gauge | Lên xuống | `memory_bytes`, `queue_depth`, `db_pool_in_use` | Nhìn trực tiếp |
  | Histogram | Đếm theo bucket | `http_request_duration_seconds` | Tính percentile phía server bằng `histogram_quantile()`, **gộp được** giữa các instance |
  | Summary | Tính quantile phía client | | ⚠️ Quantile không gộp được giữa instance |

  - ⚠️ **Cardinality**: mỗi tổ hợp giá trị label là một time series. Label `user_id`, `order_id`, URL đầy đủ có id (`/orders/12345`), message lỗi → hàng triệu series, TSDB tốn RAM và sập. Dùng route template (`/orders/{id}`), đưa id vào log/trace thay vì metric
  - Chọn bucket histogram quanh ngưỡng SLO (bucket quá thô thì percentile tính ra thiếu chính xác)
- [ ] **RED, USE, golden signals** 🟡
  - **RED** (cho service/endpoint): Rate, Errors, Duration
  - **USE** (cho tài nguyên: CPU, đĩa, pool, queue): Utilization, Saturation, Errors
  - **Four golden signals** (Google SRE): latency, traffic, errors, saturation
  - ⚠️ Latency của request lỗi và request thành công nên tách riêng: lỗi trả nhanh làm latency trung bình "đẹp" giả
- [ ] **Tracing** 🟡
  - Trace = cây các **span**; mỗi span là một đơn vị công việc (một HTTP call, một query) có thời điểm bắt đầu, thời lượng, attribute, trạng thái. Mọi span chung một **trace id**
  - **Context propagation**: truyền trace id + span id cha qua ranh giới service. Chuẩn W3C Trace Context (header `traceparent`); qua message queue thì đặt vào header của message
  - **OpenTelemetry**: chuẩn mở gồm API, SDK, auto-instrumentation và Collector; gửi được tới nhiều backend (Jaeger, Tempo, Datadog...). Tránh khoá vào một vendor
  - ⚠️ Một chỗ quên propagate (thread pool, goroutine mới không truyền `context`, job queue) → trace bị đứt thành nhiều mảnh
  - 🔴 **Sampling**: head-based (quyết định ngay đầu request, ví dụ giữ 1%, rẻ nhưng có thể bỏ mất request lỗi hiếm) vs tail-based (thu hết rồi quyết định sau khi request xong: giữ mọi trace lỗi/chậm, tốn tài nguyên ở collector)
- [ ] **Ba cái bổ trợ nhau** 🟡
  - Metric: **có** vấn đề không, từ khi nào, lớn cỡ nào (rẻ, tổng hợp, dùng cho alert)
  - Trace: vấn đề **ở đâu** trong chuỗi service (span nào chậm)
  - Log: **vì sao** (chi tiết lỗi, tham số)
  - Luồng điều tra điển hình: alert từ metric → mở dashboard, thấy endpoint lỗi tăng → exemplar/trace mẫu của request lỗi → span DB lỗi → log có cùng trace id cho thấy message lỗi
  - Gắn `trace_id` vào mọi log; exemplar đính trace id vào điểm metric
  - Thêm: error tracking (Sentry) gom exception theo nhóm, kèm stack trace và release; continuous profiling (Pyroscope, Parca) là "trụ cột thứ tư" đang phổ biến

### Alerting và on-call

- [ ] **Alert theo triệu chứng** 🟢
  - Page khi **người dùng bị ảnh hưởng**: tỉ lệ lỗi, latency vượt SLO, burn rate cao, không đặt được đơn
  - Nguyên nhân (CPU 90%, một pod restart) chỉ nên là dashboard hoặc ticket, trừ khi chắc chắn dẫn tới sự cố (đĩa sẽ đầy trong 4 giờ)
  - Mỗi alert page phải: cần hành động ngay, có người làm được gì đó, có runbook
- [ ] **Alert fatigue** ⚠️: cảnh báo quá nhiều hoặc hay báo sai → mọi người bỏ qua, và alert thật bị lọt
  - Chữa: xoá/hạ cấp alert không dẫn tới hành động; gom nhóm (một sự cố một page, không 200 page); ngưỡng theo thời gian (`for: 5m`) để bỏ nhiễu; review alert định kỳ theo số lần kích hoạt và số lần có hành động
- [ ] **Runbook** 🟡: mỗi alert link tới tài liệu: ý nghĩa, ảnh hưởng, dashboard cần xem, bước chẩn đoán, bước giảm thiệt hại, ai để escalate. Bước lặp lại nhiều nên tự động hoá
- [ ] **On-call** 🟡
  - Rotation (primary + secondary), escalation tự động nếu không ack trong N phút
  - Handover đầu ca: sự cố đang mở, thay đổi rủi ro sắp diễn ra
  - Bền vững: số page mỗi ca có giới hạn, bù giờ, không để một người on-call triền miên
  - Công cụ: PagerDuty, Opsgenie, Grafana OnCall

### Incident management

- [ ] **Quy trình** 🟢
  1. **Phát hiện**: alert, người dùng báo, đồng nghiệp thấy
  2. **Phân loại**: ảnh hưởng bao nhiêu người, tính năng gì → mức SEV; mở kênh sự cố
  3. **Giảm thiệt hại (mitigate)**: rollback, tắt feature flag, chuyển traffic, scale, chặn nguồn tải xấu
  4. **Khắc phục**: sửa gốc khi đã ổn định
  5. **Đóng sự cố**, theo dõi thêm một thời gian
  6. **Postmortem** và action items
- [ ] **Mức độ nghiêm trọng** 🟡 (mỗi công ty định nghĩa riêng, ví dụ)
  - SEV1: dịch vụ chính ngừng hoặc mất/rò dữ liệu, nhiều khách bị ảnh hưởng → mọi người liên quan vào ngay, thông báo khách
  - SEV2: tính năng quan trọng hỏng hoặc suy giảm rõ, có workaround
  - SEV3: ảnh hưởng nhỏ, xử lý trong giờ làm việc
  - Nâng/hạ mức khi có thông tin mới; nghi ngờ thì chọn mức cao hơn
- [ ] **Vai trò** 🔴
  - **Incident commander (IC)**: điều phối, quyết định, không tự tay debug. Giữ nhịp: ai làm gì, cập nhật lúc nào
  - Operations/tech lead: điều tra và thực hiện thay đổi
  - Communications lead: cập nhật nội bộ, status page, bộ phận hỗ trợ khách hàng
  - Scribe: ghi timeline (thời điểm, quyết định, lệnh đã chạy) — nguyên liệu cho postmortem
  - Sự cố nhỏ một người kiêm nhiều vai; sự cố lớn tách vai để người debug không bị hỏi han liên tục
- [ ] **Giao tiếp** 🟡
  - Một kênh chung duy nhất cho sự cố; cập nhật định kỳ (ví dụ mỗi 30 phút) kể cả khi "chưa có gì mới"
  - Nội dung cập nhật: ảnh hưởng hiện tại, đang làm gì, lần cập nhật tiếp theo lúc nào
  - Status page cho khách: nói thật, không đổ lỗi, không hứa thời gian khi chưa chắc
- [ ] **Mitigate trước, root cause sau** 🟢
  - Ưu tiên đưa hệ thống về trạng thái chạy được; điều tra sâu khi đã hết chảy máu
  - Có deploy/thay đổi config gần thời điểm bắt đầu → **rollback** là hành động đầu tiên hợp lý, kể cả khi chưa chắc đó là nguyên nhân
  - Giữ bằng chứng trước khi restart nếu kịp (heap dump, log, thread dump) — nhưng không để việc giữ bằng chứng kéo dài sự cố
  - ⚠️ Rollback không phải lúc nào cũng được: migration DB đã chạy không tương thích ngược → đây là lý do migration phải expand/contract — xem [19-devops-cloud.md](19-devops-cloud.md)
- [ ] **Postmortem blameless** 🟡
  - Hỏi "hệ thống/quy trình nào đã cho phép lỗi này xảy ra", không hỏi "ai làm sai". Người sợ bị phạt sẽ giấu thông tin
  - Viết cho mọi SEV1/SEV2 và cho near-miss đáng học
  - Template:

  ```markdown
  # Postmortem: <tiêu đề> (SEV2, 2026-09-10)
  ## Tóm tắt           — 2-3 câu: chuyện gì, ảnh hưởng, đã khắc phục thế nào
  ## Ảnh hưởng          — bao nhiêu user/đơn/tiền, thời lượng, SLO/error budget tiêu tốn
  ## Timeline           — mốc giờ: bắt đầu, phát hiện, mitigate, hồi phục (UTC hoặc ghi rõ múi giờ)
  ## Root cause         — nguyên nhân gốc và các yếu tố góp phần
  ## Phát hiện          — ta biết bằng cách nào, có thể biết sớm hơn không
  ## Cái gì làm tốt / cái gì chưa tốt / chỗ nào may mắn
  ## Action items       — việc, owner, hạn, mức ưu tiên, link ticket
  ```
- [ ] **5 whys** 🟡: hỏi "vì sao" lặp lại để đi từ triệu chứng tới nguyên nhân hệ thống
  - Ví dụ: DB dev bị xoá sạch → vì test chạy `TRUNCATE` → vì test nối vào DB dev dùng chung → vì config test không khai báo DB riêng → vì không có quy ước/cơ chế bắt buộc cô lập môi trường test → action: CI chặn test nếu DB không phải DB test, tách credential
  - ⚠️ Hạn chế: dễ đi theo một nhánh duy nhất; sự cố thật thường có nhiều yếu tố góp phần. Kết hợp với vẽ các yếu tố góp phần
  - ⚠️ Dừng ở "con người bất cẩn" là dừng quá sớm
- [ ] **Action items** 🟡
  - Cụ thể, có owner, có hạn, có ticket. "Cẩn thận hơn" không phải action item
  - Ưu tiên theo loại: phát hiện sớm hơn (alert), giảm thiệt hại (kill switch, rollback nhanh), phòng ngừa (guardrail tự động, test)
  - Theo dõi tỉ lệ hoàn thành; action item không làm thì sự cố lặp lại
- [ ] **Câu chuyện sự cố của chính mình** 🟢 — phỏng vấn rất hay hỏi. Khung:
  1. Chuyện gì đã xảy ra và ảnh hưởng thế nào
  2. Phát hiện ra bằng cách nào
  3. Điều tra ra root cause ra sao (đừng dừng ở nguyên nhân bề mặt)
  4. Khắc phục tức thời
  5. **Phòng ngừa lâu dài**: đã thay đổi quy trình, cấu hình hoặc tooling gì
  - Chi tiết cách kể ở [25-interview-skills.md](25-interview-skills.md)

### Resilience testing

- [ ] **Chaos engineering** 🔴 (đại ý)
  - Chủ động gây lỗi có kiểm soát để kiểm chứng giả thuyết "hệ thống chịu được X": giết instance, thêm latency mạng, làm một dependency trả lỗi, đầy đĩa, mất một AZ
  - Quy trình: định nghĩa steady state (metric bình thường) → giả thuyết → thí nghiệm với **blast radius nhỏ** (một phần trăm traffic, một instance) → quan sát → mở rộng dần
  - Có nút dừng khẩn cấp; bắt đầu ở staging, lên production khi observability và rollback đã tốt
  - Công cụ: Chaos Monkey (Netflix), Chaos Mesh, LitmusChaos, AWS Fault Injection Service, Toxiproxy (giả lập mạng xấu khi test)
- [ ] **Game day** 🔴: buổi diễn tập có kế hoạch, cả team cùng tham gia: giả lập sự cố (region chết, DB failover, khoá hết credential), thực hành quy trình incident, kiểm tra runbook và alert. Kết quả là danh sách lỗ hổng cần sửa

### Công cụ

| Nhu cầu | Mã nguồn mở / tự host | SaaS |
|---|---|---|
| Metric + dashboard | Prometheus + Grafana (VictoriaMetrics, Thanos/Mimir cho quy mô lớn, lưu lâu) | Datadog, New Relic, Grafana Cloud |
| Log | ELK/EFK (Elasticsearch/OpenSearch + Logstash/Fluentd/Fluent Bit + Kibana), Loki | Datadog Logs, CloudWatch Logs |
| Tracing | Jaeger, Grafana Tempo, Zipkin; OpenTelemetry Collector | Datadog APM, New Relic, Honeycomb |
| Error tracking | Sentry (tự host được) | Sentry, Bugsnag, Rollbar |
| Alert, on-call | Alertmanager, Grafana OnCall | PagerDuty, Opsgenie |
| Uptime / synthetic | Blackbox exporter | Pingdom, Checkly, Datadog Synthetics |

- Loki chỉ index label (rẻ, query full-text chậm hơn); Elasticsearch index nội dung (tìm nhanh, đắt hơn)
- Prometheus pull metric theo chu kỳ scrape; job ngắn hạn dùng Pushgateway hoặc OTLP push
- ⚠️ Hệ thống monitoring chạy chung hạ tầng với hệ thống được giám sát → sập cùng lúc. Cần ít nhất một kiểm tra từ bên ngoài (synthetic check)

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Production 500 hàng loạt, bạn làm gì? | "Xem log để tìm bug" | Đánh giá ảnh hưởng, mở kênh sự cố, kiểm tra thay đổi gần nhất và rollback trước; giao tiếp; tìm root cause sau khi ổn định; postmortem |
| Bạn giám sát service thế nào? | "Có dashboard CPU, RAM" | SLO theo user journey, RED cho service, USE cho tài nguyên, alert theo burn rate, trace id trong log, runbook cho từng alert |
| Có backup không? | "Có, chạy hằng ngày" | RPO/RTO bao nhiêu, PITR, backup ở tài khoản khác và immutable, restore thử tự động định kỳ, đo thời gian restore |
| 99,99% có được không? | "Được, thêm server" | 4,3 phút/tháng nên phải failover tự động và deploy an toàn; tính dependency; đưa ra error budget policy; hỏi nghiệp vụ có thật cần không |
| Postmortem để làm gì? | "Tìm người gây lỗi" | Blameless, tìm yếu tố hệ thống, action item có owner và hạn, chia sẻ bài học, theo dõi tỉ lệ hoàn thành |
| Log thế nào cho tốt? | "Log nhiều cho chắc" | Structured, có correlation id, level đúng, không PII, sampling, kiểm soát chi phí; biết khi nào dùng metric/trace thay vì log |

## Tình huống

1. **Production đột nhiên trả lỗi 500 hàng loạt ngay sau deploy. 15 phút đầu tiên bạn làm gì?**
   - Gợi ý: xác nhận ảnh hưởng qua dashboard (tỉ lệ lỗi, endpoint nào, mọi instance hay một phần); báo trong kênh sự cố, nhận hoặc chỉ định IC
   - Deploy vừa xong → rollback ngay (hoặc tắt feature flag), không debug trên production trước
   - Nếu rollback không hết lỗi: thay đổi khác (config, migration, dependency, hạ tầng)? Xem Sentry/log theo trace id
   - Cập nhật định kỳ; sau khi ổn định: postmortem, và vì sao canary/test không bắt được

2. **DB đầy đĩa, ghi bắt đầu lỗi.**
   - Gợi ý: mitigate: tăng dung lượng đĩa nếu cloud cho phép (thường là online), dọn thứ an toàn để xoá (binlog/WAL cũ đã backup, log, bảng tạm)
   - ⚠️ Không xoá file dữ liệu/WAL bừa bãi; không xoá binlog mà replica còn cần
   - Tìm nguyên nhân: bảng tăng bất thường (log table, job ghi lặp), replication slot bị bỏ quên giữ WAL (PostgreSQL), transaction dài chặn dọn dẹp
   - Phòng ngừa: alert dự báo "đĩa đầy trong N giờ" (`predict_linear` trong Prometheus), retention/partition cho bảng lớn, autoscaling storage

3. **Memory leak từ từ: service bị OOM kill mỗi 2–3 ngày.**
   - Gợi ý: mitigate tạm bằng restart có kiểm soát (rolling) trước khi chạm ngưỡng; alert theo xu hướng memory
   - Điều tra: xem memory có tăng từ một deploy cụ thể không; heap dump/profile so sánh hai thời điểm; số goroutine/thread, số connection mở
   - Xem thêm ở [17-performance.md](17-performance.md)

4. **Một dependency bên ngoài (API vận chuyển) chậm từ 200 ms lên 30 giây, kéo sập cả hệ thống, kể cả các trang không liên quan.**
   - Gợi ý: cơ chế sập: thread/worker/connection bị giữ chờ 30 giây → Little's law → pool cạn → mọi request khác không còn worker
   - Mitigate: tắt tính năng qua flag, giảm timeout, circuit breaker mở để fail nhanh
   - Phòng ngừa: timeout hợp lý cho mọi lời gọi ra ngoài, circuit breaker, bulkhead (pool riêng cho dependency này), gọi bất đồng bộ qua queue nếu không cần kết quả ngay, fallback (giá vận chuyển ước tính)
   - Alert theo latency của dependency, không chỉ theo lỗi

5. **Alert kêu 50 lần mỗi đêm, team bắt đầu tắt tiếng điện thoại.**
   - Gợi ý: thống kê alert nào kêu nhiều, alert nào có hành động; xoá hoặc hạ thành ticket; chuyển sang alert theo triệu chứng/burn rate; gom nhóm; thêm `for:`
   - Đặt mục tiêu số page mỗi ca; review alert trong họp tuần

6. **Được giao thiết kế DR cho hệ thống thanh toán: RPO 1 phút, RTO 30 phút.**
   - Gợi ý: backup & restore không đạt RTO 30 phút ở dữ liệu lớn; cần warm standby ở region khác với replication liên tục
   - RPO 1 phút → replication async lag phải được giám sát dưới 1 phút
   - Runbook failover, DNS TTL thấp, IaC, diễn tập định kỳ và đo RTO thật; kiểm tra phụ thuộc bên ngoài (PSP có whitelist IP region chính?)

## ❓ Câu hỏi hay gặp

🟢
- SLI, SLO, SLA khác nhau thế nào?
- Liveness và readiness probe khác nhau thế nào?
- Log có cấu trúc là gì? Correlation id dùng để làm gì?
- Production đột nhiên trả lỗi 500 hàng loạt. 15 phút đầu tiên bạn làm gì?

🟡
- Error budget là gì, dùng thế nào?
- RPO và RTO là gì? Cho ví dụ.
- Counter, gauge, histogram khác nhau thế nào? Vì sao không dùng `user_id` làm label?
- RED và USE là gì?
- Trace id được truyền qua các service thế nào?
- Vì sao nên alert theo triệu chứng?
- Postmortem blameless là gì? Viết gồm những phần nào?
- Kể một sự cố bạn đã xử lý.

🔴
- Burn rate alert hoạt động thế nào?
- So sánh các mức DR: pilot light, warm standby, active-active.
- Head-based và tail-based sampling khác nhau thế nào?
- Split-brain là gì, chống thế nào?
- Một dependency chậm kéo sập toàn hệ thống: vì sao, phòng thế nào?
- Vai trò incident commander là gì?
- Chaos engineering bắt đầu thế nào cho an toàn?

## Bài tập tự làm

1. Định nghĩa 3 SLO cho một hệ thống bạn đang làm (một user journey mỗi SLO): SLI, cách đo, mục tiêu, error budget mỗi tháng, và error budget policy.
2. Viết middleware (PHP, Java hoặc Go) sinh hoặc nhận request id từ header, gắn vào mọi log dạng JSON và truyền sang HTTP call tiếp theo.
3. Viết postmortem theo template ở trên cho một sự cố thật bạn từng gặp (hoặc sự cố xoá DB dev do test), có 5 whys và ít nhất 3 action items cụ thể.
4. Viết runbook cho alert "tỉ lệ lỗi 5xx của API thanh toán > 2% trong 5 phút".
5. Liệt kê metric Prometheus cần có cho một queue worker (tên metric, loại, label) và chỉ ra label nào sẽ gây vấn đề cardinality.

> Nộp bài vào đây để được review.
