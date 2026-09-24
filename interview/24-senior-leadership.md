# 24. Kỹ năng senior: ra quyết định, dẫn dắt, giao hàng

> [← Mục lục](README.md) · Phạm vi: những gì tách senior khỏi mid ngoài kiến thức kỹ thuật —
> ra quyết định kỹ thuật, ước lượng, giao hàng, làm việc với product, quản lý tech debt,
> migration hệ thống cũ, mentor, dẫn dắt sự cố, ảnh hưởng xuyên team.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay gặp. Không nhãn = level nào cũng cần.

Với vị trí senior, vòng kỹ thuật chỉ chứng minh bạn **đủ** giỏi. Người phỏng vấn còn hỏi:
người này có tự nhận một vấn đề mơ hồ rồi giao được kết quả không, có làm cả team tốt lên
không. File này là để trả lời được những câu đó bằng ví dụ thật.

---

## Bản đồ nhanh

**Senior là gì**
- [ ] Nói được sự khác nhau giữa junior, mid, senior theo phạm vi, độ mơ hồ, tầm ảnh hưởng
- [ ] Ownership: chịu trách nhiệm kết quả, không chỉ chịu trách nhiệm phần code của mình

**Ra quyết định kỹ thuật**
- [ ] Khung phân tích trade-off
- [ ] Quyết định đảo ngược được và không đảo ngược được
- [ ] Build vs buy vs dùng mã nguồn mở
- [ ] Chọn công nghệ mới (và khi nào không nên)
- [ ] Viết design doc/RFC, ADR
- [ ] 🔴 Đưa một quyết định qua nhiều bên có ý kiến khác nhau

**Giao hàng**
- [ ] Chia việc: vertical slice, MVP, milestone
- [ ] Ước lượng và truyền đạt độ bất định
- [ ] Quản lý rủi ro và dependency
- [ ] Nói "không", cắt phạm vi, thương lượng deadline
- [ ] Cập nhật tiến độ cho stakeholder

**Làm việc với product và business**
- [ ] Dịch yêu cầu kinh doanh thành yêu cầu kỹ thuật và ngược lại
- [ ] Làm rõ yêu cầu mơ hồ
- [ ] Giải thích vấn đề kỹ thuật cho người không làm kỹ thuật

**Chất lượng dài hạn**
- [ ] Quản lý tech debt: phân loại, ưu tiên, thuyết phục đầu tư
- [ ] Văn hoá code review
- [ ] 🔴 Chuẩn hoá (guideline, template, tooling) cho cả team
- [ ] Nhận thức về chi phí hạ tầng

**Hệ thống cũ và migration**
- [ ] Làm việc với legacy code
- [ ] 🔴 Migration lớn: strangler fig, dual write, backfill, shadow traffic, cutover, rollback

**Vận hành**
- [ ] Ownership vận hành: SLO, on-call, runbook
- [ ] 🔴 Dẫn dắt xử lý sự cố (incident commander), postmortem

**Con người**
- [ ] Mentor, onboarding người mới
- [ ] Giao việc và phát triển người khác
- [ ] Góp ý và nhận góp ý
- [ ] 🔴 Ảnh hưởng khi không có quyền (influence without authority)
- [ ] 🔴 Phỏng vấn tuyển người

---

## Chi tiết

### Senior là gì

| | Junior | Mid | Senior |
|---|---|---|---|
| Phạm vi | một task | một tính năng | một hệ thống/một mảng, xuyên nhiều tính năng |
| Độ mơ hồ | nhận task đã rõ | tự làm rõ chi tiết của tính năng | nhận một **vấn đề** và tự biến nó thành kế hoạch |
| Quyết định | làm theo thiết kế | thiết kế trong phạm vi tính năng | quyết định kiến trúc, chịu trách nhiệm trade-off dài hạn |
| Tầm ảnh hưởng | bản thân | bản thân và người review | cả team, và các team lân cận |
| Khi có sự cố | báo lên | tự sửa phần mình | dẫn dắt xử lý, đảm bảo không lặp lại |

- [ ] Ownership nghĩa là: kết quả kinh doanh của tính năng là việc của mình. Code đã merge
      nhưng tính năng không ai dùng, hoặc sập sau 1 tuần, thì việc chưa xong
- [ ] ⚠️ Senior không phải là "code nhanh nhất". Senior làm team nhanh hơn: gỡ vướng, ra
      quyết định, giảm rủi ro, nâng người khác lên

### Ra quyết định kỹ thuật

**Khung trade-off**, dùng được cho mọi câu "vì sao chọn X":
- [ ] Nêu **bài toán và ràng buộc** trước: quy mô, deadline, kỹ năng của team, ngân sách,
      yêu cầu nhất quán dữ liệu, yêu cầu tuân thủ
- [ ] Nêu **ít nhất hai lựa chọn**, kể cả lựa chọn "không làm gì" hoặc "làm đơn giản nhất"
- [ ] So sánh theo tiêu chí cụ thể: độ phức tạp, chi phí vận hành, rủi ro, thời gian làm,
      khả năng đảo ngược, ảnh hưởng tới team khác
- [ ] Nêu **cái giá** của lựa chọn đã chọn, và **điều kiện nào thì sẽ đổi**
- [ ] ⚠️ "Công nghệ này đang hot" hay "công ty lớn đều dùng" không phải lý do

**Quyết định đảo ngược được và không đảo ngược được**
- [ ] Đảo ngược được (đổi thư viện nội bộ, tên endpoint nội bộ): quyết nhanh, thử rồi sửa
- [ ] Khó đảo ngược (schema dữ liệu lõi, API công khai, chọn database, tách microservice,
      định dạng message): chậm lại, viết design doc, xin review rộng
- [ ] Senior biết đặt thời gian suy nghĩ tương xứng với cái giá khi sai

**Build vs buy**
- [ ] Mua/dùng dịch vụ khi không phải năng lực cốt lõi (email, auth, thanh toán, monitoring)
- [ ] Tự xây khi là lợi thế cạnh tranh, hoặc dịch vụ ngoài không đáp ứng ràng buộc
      (dữ liệu, chi phí ở quy mô lớn, tuỳ biến)
- [ ] ⚠️ Tính cả chi phí vận hành dài hạn, không chỉ chi phí làm ban đầu; và rủi ro
      phụ thuộc nhà cung cấp (vendor lock-in)

**Chọn công nghệ mới**
- [ ] Câu hỏi cần trả lời: giải quyết vấn đề gì mà cái đang có không làm được? Ai vận hành
      nó lúc 2 giờ sáng? Team có ai biết không? Cộng đồng và tài liệu thế nào?
- [ ] ⚠️ Mỗi công nghệ mới là một thứ phải vận hành, giám sát, nâng cấp và dạy cho người mới.
      "Chọn công nghệ nhàm chán" (boring technology) thường là quyết định đúng

**Design doc/RFC**
- [ ] Cấu trúc điển hình: bối cảnh và vấn đề → mục tiêu và **không phải mục tiêu**
      (non-goals) → phương án đề xuất → các phương án đã cân nhắc và vì sao loại →
      rủi ro và cách giảm → kế hoạch triển khai và rollback → câu hỏi còn mở
- [ ] Viết doc để **thu thập phản biện sớm**, không phải để hợp thức hoá quyết định đã có
- [ ] ADR (Architecture Decision Record): ghi ngắn quyết định, bối cảnh, hệ quả; để người
      đến sau hiểu vì sao hệ thống như hiện nay. Xem [15-architecture.md](15-architecture.md)

**🔴 Đưa quyết định qua nhiều bên**
- [ ] Nói chuyện riêng với từng bên liên quan trước buổi họp chung
- [ ] Tách phần bất đồng về dữ liệu (đo được) khỏi phần bất đồng về giá trị (ưu tiên khác nhau)
- [ ] Dùng thử nghiệm nhỏ (spike, prototype, benchmark) khi tranh luận không đi tới đâu
- [ ] "Disagree and commit": khi đã quyết, cả team làm hết sức cho quyết định đó, kể cả người
      từng phản đối

### Giao hàng

**Chia việc**
- [ ] **Vertical slice**: mỗi phần giao được là một luồng hoàn chỉnh từ đầu đến cuối (dù nhỏ),
      thay vì làm xong toàn bộ tầng DB rồi mới làm API rồi mới làm UI
- [ ] MVP: phiên bản nhỏ nhất kiểm chứng được giả định quan trọng nhất
- [ ] Làm phần rủi ro nhất trước (tích hợp bên thứ ba, phần chưa ai làm bao giờ)
- [ ] Feature flag để merge sớm, bật dần, tắt nhanh khi có vấn đề

**Ước lượng**
- [ ] Chia nhỏ tới mức mỗi phần dưới 1–2 ngày thì ước lượng mới đáng tin
- [ ] Ước lượng theo **khoảng** và kèm độ tự tin: "3–5 ngày, phần chưa chắc là API của bên
      đối tác". Một con số duy nhất che mất rủi ro
- [ ] Nhớ các việc hay bị quên: review, test, migration dữ liệu, tài liệu, deploy, theo dõi
      sau khi release, xử lý phản hồi
- [ ] Cập nhật ước lượng ngay khi biết thêm thông tin; báo trễ sớm tốt hơn nhiều so với báo muộn
- [ ] ⚠️ Không cam kết ước lượng dưới áp lực trong cuộc họp; hẹn trả lời sau khi chia việc

**Rủi ro và dependency**
- [ ] Liệt kê rủi ro kèm xác suất, ảnh hưởng và cách giảm
- [ ] Dependency vào team khác: xác nhận sớm, có người đầu mối, có kế hoạch dự phòng

**Nói "không" và cắt phạm vi**
- [ ] Khi deadline cố định, thứ điều chỉnh được là phạm vi. Đưa lựa chọn thay vì từ chối:
      "Đúng hạn thì được A và B; muốn có C thì cần thêm 1 tuần, hoặc bỏ B"
- [ ] ⚠️ Không lặng lẽ cắt chất lượng (bỏ test, bỏ xử lý lỗi) để kịp deadline. Nếu phải đánh
      đổi thì nói ra, ghi thành tech debt có kế hoạch trả

**Cập nhật tiến độ**
- [ ] Ngắn, đều đặn, theo định dạng: đã xong, đang làm, rủi ro/cần hỗ trợ
- [ ] Tin xấu báo sớm, kèm phương án

### Làm việc với product và business
- [ ] Hỏi "vấn đề người dùng là gì" trước khi hỏi "cần làm tính năng gì". Nhiều khi có cách
      đơn giản hơn nhiều để giải quyết vấn đề đó
- [ ] Làm rõ yêu cầu mơ hồ: viết lại yêu cầu bằng lời của mình, liệt kê các trường hợp biên
      (hết hàng, thanh toán lỗi, người dùng huỷ giữa chừng), xác nhận lại
- [ ] Nêu yêu cầu phi chức năng mà product thường không nghĩ tới: hiệu năng, bảo mật,
      dữ liệu cũ, quyền truy cập, khả năng quan sát
- [ ] Giải thích cho người không làm kỹ thuật bằng hệ quả kinh doanh: "nếu không làm X thì
      mỗi đợt khuyến mãi có rủi ro sập 30 phút", thay vì "cần refactor cache layer"

### Chất lượng dài hạn

**Tech debt**
- [ ] Phân loại: cố ý và thận trọng ("ra mắt trước, sửa sau, đã ghi lại"), cố ý và liều lĩnh,
      vô tình (do chưa biết cách tốt hơn), và debt do hệ thống thay đổi theo thời gian
- [ ] Ưu tiên theo **lãi suất**: debt nằm ở chỗ hay phải sửa, hay gây sự cố thì trả trước;
      debt ở module không ai đụng tới thì để đó
- [ ] Thuyết phục đầu tư trả nợ bằng số liệu: thời gian làm tính năng ở module đó, số sự cố,
      thời gian onboard người mới
- [ ] Cách trả: gắn vào tính năng đang làm (quy tắc hướng đạo sinh: để lại code sạch hơn lúc
      nhận), dành một tỷ lệ cố định mỗi sprint, hoặc dự án riêng khi cần

**Code review**
- [ ] Mục tiêu: tìm lỗi, chia sẻ kiến thức, giữ tính nhất quán; không phải để thể hiện
- [ ] Góp ý phân mức độ (chặn merge, nên sửa, tuỳ chọn), kèm lý do và gợi ý
- [ ] Tự động hoá những gì máy làm được (format, lint, static analysis) để review tập trung
      vào thiết kế và logic
- [ ] PR nhỏ; senior làm gương bằng PR của chính mình

**Chi phí**
- [ ] 🔴 Biết đại khái hệ thống tốn bao nhiêu tiền mỗi tháng và phần nào tốn nhất
- [ ] Nhận ra các khoản hay phình: log và metric quá nhiều (cardinality), dữ liệu không bao
      giờ xoá, instance quá cỡ, egress bandwidth

### Legacy và migration

**Làm việc với legacy code**
- [ ] Hiểu trước khi sửa: đọc code, đọc log, đọc lịch sử git (`git log -p`, `git blame`) để
      hiểu vì sao nó được viết như vậy
- [ ] Viết characterization test (test ghi lại hành vi hiện tại) trước khi refactor phần rủi ro
- [ ] Thay đổi từng bước nhỏ, mỗi bước deploy được
- [ ] ⚠️ "Viết lại từ đầu" hiếm khi là lựa chọn đúng: mất các xử lý biên mà code cũ đã tích
      luỹ qua nhiều năm, và hai hệ thống phải chạy song song rất lâu

**🔴 Migration lớn** (đổi database, tách service, đổi hệ thống thanh toán):
- [ ] **Strangler fig**: đặt một lớp định tuyến phía trước, chuyển dần từng phần chức năng
      sang hệ thống mới, cho tới khi hệ thống cũ không còn gì
- [ ] Các bước điển hình khi đổi nơi lưu dữ liệu:
  1. Ghi song song vào cả cũ và mới (dual write), hoặc đồng bộ qua CDC
  2. Backfill dữ liệu lịch sử
  3. Đọc song song (shadow read) và so sánh kết quả, ghi log chênh lệch
  4. Chuyển dần lượng đọc sang hệ thống mới theo tỷ lệ
  5. Chuyển nguồn ghi chính
  6. Giữ đường rollback một thời gian, rồi mới tắt hệ thống cũ
- [ ] Mỗi bước phải có tiêu chí đi tiếp và cách quay lại
- [ ] ⚠️ Dual write có vấn đề nhất quán khi một bên ghi lỗi; xem outbox và CDC ở
      [12-messaging.md](12-messaging.md)

### Vận hành
- [ ] Ownership vận hành: team viết ra thì team vận hành ("you build it, you run it")
- [ ] SLO cho service mình sở hữu, dashboard, alert có runbook
- [ ] 🔴 Incident commander: điều phối chứ không tự tay sửa; phân vai (người điều tra, người
      giao tiếp), cập nhật định kỳ cho các bên, quyết định rollback. Xem
      [18-reliability-observability.md](18-reliability-observability.md)
- [ ] Postmortem blameless, action item có người nhận và hạn chót, theo dõi đến khi xong

### Con người

**Mentor và onboarding**
- [ ] Onboarding: tài liệu khởi động, người đồng hành, task đầu tiên nhỏ và deploy được trong
      tuần đầu
- [ ] Mentor bằng câu hỏi thay vì đưa đáp án: "Em nghĩ cách này có vấn đề gì khi có hai
      request cùng lúc?"
- [ ] Giao việc hơi vượt khả năng một chút, kèm hỗ trợ; để người khác làm những việc mình làm
      nhanh hơn, vì đó là cách họ lớn
- [ ] ⚠️ Senior làm hết việc khó thì team không ai lớn lên, và senior trở thành nút thắt

**Góp ý**
- [ ] Góp ý cụ thể, về hành vi và tác động, sớm, riêng tư khi là góp ý tiêu cực
- [ ] Nhận góp ý: nghe hết, hỏi rõ, cảm ơn, rồi mới quyết định làm gì với nó

**🔴 Ảnh hưởng khi không có quyền**
- [ ] Thuyết phục team khác bằng lợi ích của chính họ, dữ liệu và prototype
- [ ] Xây uy tín bằng việc giúp đỡ trước khi cần nhờ

**🔴 Tuyển người**
- [ ] Phỏng vấn theo tiêu chí thống nhất trước; ghi nhận bằng chứng, không ghi cảm tính
- [ ] Biết mình đang chấm cái gì ở mỗi câu hỏi. Kinh nghiệm phỏng vấn người khác cũng giúp
      bạn hiểu người phỏng vấn mình đang tìm gì

---

## Senior trả lời khác gì

| Câu hỏi | Mid thường trả lời | Senior trả lời |
|---|---|---|
| "Khi nào xong?" | "Thứ Sáu ạ" | "3–5 ngày. Phần chưa chắc là API đối tác; em sẽ xác nhận trong hôm nay và cập nhật lại" |
| "Có nên chuyển sang microservices không?" | liệt kê lợi ích của microservices | hỏi vấn đề đang gặp là gì, xem modular monolith có giải quyết được không, nêu điều kiện tiên quyết (CI/CD, observability, team) |
| "Xử lý tech debt thế nào?" | "dành thời gian refactor" | phân loại, ưu tiên theo chỗ gây đau nhiều nhất, số liệu để thuyết phục, cách trả dần gắn với tính năng |
| "Kể về sự cố" | sửa bug như thế nào | phát hiện ra sao, giảm thiệt hại thế nào, root cause ở tầng hệ thống, thay đổi gì để cả team không gặp lại |
| "Bạn giúp người mới thế nào?" | "trả lời câu hỏi khi họ hỏi" | kế hoạch onboarding, task đầu tiên, review có hướng dẫn, dần giao việc lớn hơn, đo tiến bộ |

---

## Tình huống

1. *Product muốn một tính năng lớn trong 2 tuần, bạn ước lượng mất 5 tuần.*
   - Chia tính năng thành các phần theo giá trị; đề xuất phần nào làm được trong 2 tuần.
   - Nêu rủi ro nếu ép cả tính năng vào 2 tuần (chất lượng, sự cố).
   - Để product chọn phạm vi, kỹ thuật chịu trách nhiệm ước lượng.

2. *Hai senior trong team tranh cãi giữa PostgreSQL và MongoDB cho dự án mới, đã hai tuần chưa ngã ngũ.*
   - Viết ra tiêu chí quyết định và kiểu truy cập dữ liệu thật của dự án.
   - Làm prototype nhỏ với phần dữ liệu khó nhất nếu cần.
   - Đặt thời hạn quyết định; người có trách nhiệm quyết; ghi ADR; disagree and commit.

3. *Bạn được giao một module legacy không có test, không có tài liệu, người viết đã nghỉ, và cần thêm tính năng gấp.*
   - Đọc code và lịch sử git để hiểu luồng chính; hỏi những người dùng module đó.
   - Viết characterization test cho phần sắp sửa.
   - Thêm tính năng với thay đổi nhỏ nhất, sau feature flag; ghi lại những gì đã hiểu.

4. *Một junior trong team liên tục mở PR lớn, chất lượng thấp, review mất nhiều thời gian.*
   - Nói chuyện riêng để hiểu nguyên nhân (không biết cách chia việc, sợ hỏi, bị ép deadline).
   - Cùng chia task trước khi code; pair programming vài lần; đặt kỳ vọng PR nhỏ.

5. *Bạn cần chuyển bảng `orders` 500 triệu dòng sang database mới mà không downtime.*
   - Dùng các bước migration ở trên: dual write/CDC, backfill, shadow read so sánh,
     chuyển dần, giữ rollback.
   - Nêu tiêu chí đi tiếp của từng bước, cách theo dõi chênh lệch dữ liệu.

---

## ❓ Câu hỏi hay gặp

🟡
- Kể về một lần bạn phải làm việc với yêu cầu không rõ ràng.
- Bạn ước lượng công việc thế nào? Khi ước lượng sai thì làm gì?
- Bạn xử lý tech debt thế nào trong khi vẫn phải làm tính năng?

🔴
- Kể về quyết định kỹ thuật quan trọng nhất bạn từng đưa ra. Nếu làm lại, bạn có đổi không?
- Bạn chọn một công nghệ mới cho team theo tiêu chí gì?
- Kể về một migration lớn bạn đã tham gia hoặc dẫn dắt.
- Bạn thuyết phục một team khác thay đổi cách làm thế nào?
- Bạn giúp một người trong team tiến bộ rõ rệt thế nào?
- Khi bạn và engineering manager bất đồng về ưu tiên, bạn làm gì?
- Làm sao bạn biết một dự án đang đi chệch hướng, và bạn làm gì?

---

## Bài tập tự làm

1. **Design doc**: chọn một tính năng bạn đã làm, viết lại thành design doc theo cấu trúc ở
   trên (tối đa 2 trang), có mục phương án đã loại và lý do.
2. **ADR**: viết 2 ADR cho hai quyết định kỹ thuật có thật trong dự án của bạn.
3. **Ước lượng**: chia một tính năng sắp làm thành các phần dưới 1 ngày, ước lượng theo
   khoảng, đánh dấu phần rủi ro. Sau khi làm xong, so sánh với thực tế.
4. **Tech debt**: liệt kê 5 khoản tech debt trong dự án, xếp theo "lãi suất" và viết một
   đoạn thuyết phục đầu tư trả khoản đứng đầu, dùng hệ quả kinh doanh.
5. **Câu chuyện senior**: viết 3 câu chuyện theo STAR cho các câu hỏi 🔴 ở trên.

> Nộp bài vào đây để được review.
