# 25. Kỹ năng phỏng vấn

> [← Mục lục](README.md) · Phạm vi: các vòng phỏng vấn, CV, kho câu chuyện, câu hỏi hành vi,
> tâm lý trong phòng phỏng vấn, deal lương, và những phần hay bị xem nhẹ.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay gặp. Không nhãn = level nào cũng cần.

Nhiều ứng viên trượt ở phần này dù đã ôn kỹ kiến thức. Kiến thức giúp bạn qua vòng kỹ
thuật; phần này quyết định bạn có được offer và offer tốt hay không.

---

## Bản đồ nhanh

**Hiểu quy trình**
- [ ] Biết công ty có những vòng nào và mỗi vòng chấm điểm cái gì
- [ ] Đọc JD và gạch ra từ khoá, đối chiếu với [bản đồ tổng](README.md)

**Hồ sơ**
- [ ] CV viết theo kết quả, không theo nhiệm vụ
- [ ] Mọi thứ trong CV đều nói sâu được
- [ ] LinkedIn/GitHub khớp với CV
- [ ] Giới thiệu bản thân 1 phút và 3 phút (tiếng Việt và 🟡 tiếng Anh)

**Kho câu chuyện**
- [ ] Câu chuyện dự án tự hào nhất, kèm sơ đồ kiến trúc vẽ trong 2 phút
- [ ] Câu chuyện sự cố production
- [ ] Câu chuyện bất đồng/xung đột
- [ ] Câu chuyện thất bại/mắc lỗi
- [ ] Câu chuyện học nhanh một thứ mới
- [ ] 🟡 Câu chuyện ra một quyết định kỹ thuật có trade-off
- [ ] 🔴 Câu chuyện dẫn dắt/mentor, ảnh hưởng tới người không báo cáo cho mình

**Từng loại vòng**
- [ ] Screening với HR/recruiter
- [ ] Bài test online/coding test có giới hạn thời gian
- [ ] Live coding
- [ ] Take-home assignment
- [ ] Vòng code review/debug code có sẵn
- [ ] Vòng kiến thức kỹ thuật (hỏi đáp)
- [ ] 🟡 Vòng system design
- [ ] Vòng behavioral/culture fit/hiring manager
- [ ] 🔴 Vòng leadership/cross-team (với senior, staff)

**Trong phòng phỏng vấn**
- [ ] Khung trả lời cho từng loại câu hỏi
- [ ] Cách xử lý khi không biết
- [ ] Cách xử lý khi bị đơ
- [ ] Cách xử lý khi bị hỏi vặn hoặc không đồng ý
- [ ] Câu hỏi ngược cho người phỏng vấn

**Sau phỏng vấn**
- [ ] Ghi lại câu hỏi
- [ ] Deal lương, so sánh offer
- [ ] Xử lý khi trượt

---

## Chi tiết

### Các vòng phỏng vấn và cách chấm

| Vòng | Người chấm tìm gì | Chuẩn bị |
|---|---|---|
| HR screening | động lực, mức lương, khả năng giao tiếp, thời gian đi làm được | câu "vì sao đổi việc", khoảng lương, giới thiệu 1 phút |
| Coding test online | code chạy đúng trong thời gian giới hạn | luyện bài easy/medium có bấm giờ, quen nền tảng (HackerRank, Codility) |
| Live coding | cách suy nghĩ, giao tiếp, code sạch, xử lý edge case | nói to khi giải, xem [21-dsa.md](21-dsa.md) |
| Take-home | chất lượng như code thật: cấu trúc, README, xử lý lỗi, commit | đọc mục take-home bên dưới |
| Code review/debug | đọc hiểu code người khác, nhìn ra bug, bảo mật, hiệu năng | luyện đọc PR, xem [20-testing-quality.md](20-testing-quality.md) |
| Hỏi đáp kỹ thuật | độ sâu, hiểu "vì sao", kinh nghiệm thực tế | các file 01–23 |
| System design | phân tích requirement, trade-off, dẫn dắt cuộc thảo luận | [16-system-design.md](16-system-design.md) |
| Behavioral/manager | trách nhiệm, hợp tác, cách xử lý xung đột, độ chín chắn | kho câu chuyện |
| 🔴 Leadership | tầm ảnh hưởng, ra quyết định, phát triển người khác | [24-senior-leadership.md](24-senior-leadership.md) |

- [ ] Hỏi recruiter trước: có mấy vòng, mỗi vòng bao lâu, dùng ngôn ngữ gì, có được dùng
      IDE/Google không. Đây là câu hỏi bình thường, không bị trừ điểm
- [ ] ⚠️ Mỗi vòng thường do một người khác chấm độc lập. Một vòng tệ chưa chắc đã trượt,
      nhưng đừng giả định vòng sau "bù" được

### Đọc JD
- [ ] Chia JD thành: **bắt buộc** (must have), **cộng điểm** (nice to have), và **tín hiệu
      ngầm** (ví dụ "hệ thống hàng triệu người dùng" nghĩa là sẽ hỏi scale và cache;
      "fintech" nghĩa là sẽ hỏi transaction, idempotency, bảo mật)
- [ ] Mỗi từ khoá trong JD phải tương ứng với ít nhất một câu bạn trả lời được và, nếu có,
      một câu chuyện thực tế
- [ ] Từ khoá bạn chưa từng làm: chuẩn bị câu "em chưa làm thực tế nhưng em hiểu là…" và
      một điểm liên hệ với thứ bạn đã làm

### CV
- [ ] Mỗi gạch đầu dòng là một **kết quả**: *động từ + việc đã làm + cách làm + kết quả đo được*
  - Kém: "Phát triển module báo cáo"
  - Tốt: "Viết lại export báo cáo theo kiểu streaming qua queue, giảm thời gian từ 30s
    xuống 2s và hết lỗi timeout với file 500k dòng"
- [ ] Không có số liệu thật thì dùng quy mô: số người dùng, số request, số bảng, số service,
      số người trong team
- [ ] ⚠️ Mọi công nghệ ghi trong CV đều có thể bị hỏi sâu. "Đã đụng qua" thì đừng ghi,
      hoặc ghi ở mục riêng "có biết"
- [ ] 1–2 trang, dự án gần nhất và liên quan nhất lên đầu; mục kỹ năng gom theo nhóm
- [ ] ⚠️ Không đưa thông tin bảo mật của công ty cũ (tên khách hàng nội bộ, số doanh thu)
- [ ] 🟡 Chuẩn bị bản tiếng Anh nếu ứng tuyển công ty nước ngoài hoặc outsource

### Giới thiệu bản thân
- [ ] Bản 1 phút: hiện tại làm gì → 1–2 thành tựu nổi bật → vì sao quan tâm vị trí này
- [ ] Bản 3 phút: thêm bối cảnh dự án, vai trò, công nghệ chính
- [ ] ⚠️ Đừng đọc lại CV từ năm đầu tiên. Người nghe đã có CV rồi

### Kho câu chuyện (story bank)
Chuẩn bị 6–8 câu chuyện, mỗi câu dùng được cho nhiều câu hỏi khác nhau.

- [ ] Viết theo khung **STAR**: Situation, Task, **Action** (dài nhất, dùng "tôi" chứ
      không phải "chúng tôi"), Result (có số liệu), cộng thêm **Learning** (bài học rút ra)
- [ ] Mỗi câu chuyện dài 2–3 phút khi kể; sẵn sàng bị hỏi sâu 2–3 lớp
- [ ] Bảng ánh xạ để một câu chuyện phục vụ nhiều câu hỏi:

  | Câu chuyện | Dùng cho câu hỏi về |
  |---|---|
  | Tối ưu hệ thống chậm | thành tựu, giải quyết vấn đề, kỹ thuật sâu |
  | Sự cố production | áp lực, trách nhiệm, học từ sai lầm |
  | Bất đồng về thiết kế | xung đột, thuyết phục, làm việc nhóm |
  | Deadline gấp | ưu tiên, đánh đổi chất lượng, giao tiếp với product |
  | Học công nghệ mới | tự học, thích nghi |
  | Mentor người mới 🔴 | dẫn dắt, phát triển người khác |

**Câu chuyện sự cố**: một sự cố được xử lý tốt có giá trị hơn mười tính năng suôn sẻ, vì
nó cho thấy bạn có trách nhiệm, biết điều tra và biết học từ lỗi. Khung:
1. Chuyện gì đã xảy ra và ảnh hưởng thế nào
2. Phát hiện ra bằng cách nào
3. Điều tra ra root cause ra sao (đừng dừng ở nguyên nhân bề mặt)
4. Khắc phục tức thời
5. **Phòng ngừa lâu dài**: đã thay đổi quy trình, cấu hình hoặc tooling gì

> Ví dụ khung: *"Chạy test suite trên máy local, nhưng config test không tách DB nên test
> nối thẳng vào DB dev dùng chung. Các lệnh `TRUNCATE` trong test xoá sạch nhiều bảng.
> Root cause không nằm ở câu lệnh tôi gõ: test không có DB riêng, và `setUp()` âm thầm chạy
> migration. Sau đó tôi đã…"*. Câu chuyện kiểu này cho thấy bạn hiểu hệ thống sâu.

- [ ] ⚠️ Kể sự cố mà không đổ lỗi cho người khác, kể cả khi đúng là lỗi của người khác.
      Tập trung vào "hệ thống nào đã cho phép lỗi xảy ra"

### Câu hỏi hành vi hay gặp
- [ ] Kể về dự án bạn tự hào nhất
- [ ] Khó khăn kỹ thuật lớn nhất bạn từng gặp
- [ ] Một lần bạn mắc lỗi và cách xử lý
- [ ] Bất đồng với đồng nghiệp hoặc lead thì làm gì
- [ ] Deadline gấp, phải đánh đổi chất lượng thì làm gì
- [ ] Nhận yêu cầu mơ hồ từ product thì làm gì
- [ ] Học một công nghệ mới trong thời gian ngắn như thế nào
- [ ] Vì sao rời công ty cũ? ⚠️ **Không** nói xấu công ty cũ; nói về điều bạn đang tìm kiếm
- [ ] Vì sao chọn công ty này? Phải tìm hiểu sản phẩm và tech stack trước
- [ ] Điểm mạnh/điểm yếu: điểm yếu phải thật, kèm việc bạn đang làm để cải thiện
- [ ] Mục tiêu trong 2–3 năm tới
- [ ] 🟡 Một quyết định kỹ thuật bạn đã đưa ra mà sau này thấy sai
- [ ] 🔴 Một lần bạn thay đổi cách làm của cả team
- [ ] 🔴 Một lần bạn phải nói "không" với product hoặc cấp trên

### Khung trả lời theo loại câu hỏi

**Câu hỏi khái niệm** (ví dụ: "Index là gì?")
> Định nghĩa một câu → cách hoạt động → trade-off → ví dụ thực tế mình đã gặp.

**Câu hỏi "A khác B thế nào?"**
> Điểm giống → điểm khác chính → khi nào dùng A, khi nào dùng B → mình đã chọn gì ở dự án
> và vì sao.

**Câu hỏi debug/sự cố** (ví dụ: "API đột nhiên chậm")
> Thu hẹp phạm vi (chậm hết hay một endpoint, từ lúc nào, có deploy gì không) → xem số liệu
> (metric, log, trace) → đưa giả thuyết và kiểm chứng → giảm thiệt hại trước, sửa gốc sau →
> phòng ngừa.

**Câu hỏi thiết kế nhỏ** (ví dụ: "Thiết kế API đặt hàng")
> Hỏi requirement → data model → API → luồng chính → luồng lỗi (trùng, timeout, đồng thời)
> → trade-off.

**Câu hỏi hành vi**
> STAR + Learning.

**Câu hỏi system design**: xem phương pháp trong [16-system-design.md](16-system-design.md).

### Live coding
1. **Nhắc lại đề** bằng lời của mình; hỏi rõ input/output, ràng buộc, kích thước dữ liệu,
   edge case.
2. **Nêu lời giải brute force trước** kèm big-O. Có lời giải chạy được còn hơn không có gì.
3. Đề xuất cách tối ưu, **đợi người phỏng vấn đồng ý** rồi mới code.
4. **Vừa code vừa nói** mình đang làm gì. Im lặng 5 phút là tín hiệu xấu.
5. Code xong thì **tự chạy tay** với một ví dụ và các edge case.
6. Nêu độ phức tạp cuối cùng và hướng cải thiện nếu có thêm thời gian.
7. Bị gợi ý thì **đón nhận**, đừng cãi. Tiếp thu gợi ý tốt cũng được chấm điểm.

- [ ] Luyện viết code không có autocomplete (editor trơn hoặc giấy)
- [ ] Đặt tên biến tử tế ngay cả khi đang vội
- [ ] ⚠️ Đừng tối ưu sớm; đừng im lặng tìm lời giải "hoàn hảo" trong đầu

### Take-home assignment
- [ ] Hỏi rõ phạm vi và thời gian kỳ vọng; ⚠️ làm quá nhiều chưa chắc được cộng điểm,
      nhưng làm thiếu phần bắt buộc thì chắc chắn bị trừ
- [ ] **README trước tiên**: cách chạy bằng một lệnh, giả định đã đặt ra, quyết định thiết
      kế và trade-off, những gì sẽ làm thêm nếu có thời gian. Người chấm đọc README trước code
- [ ] Cấu trúc thư mục rõ, xử lý lỗi và validate input, cấu hình qua biến môi trường,
      không commit secret
- [ ] Có test cho phần logic chính (người chấm thường tìm thư mục test đầu tiên)
- [ ] Commit nhỏ, có ý nghĩa; không phải một commit "done"
- [ ] Chuẩn bị giải thích và mở rộng bài của mình ở vòng sau ("nếu có 1 triệu user thì sao?")

### Vòng code review/debug
- [ ] Đọc theo thứ tự: code làm gì → đúng không → lỗi biên và đồng thời → bảo mật →
      hiệu năng → dễ đọc/dễ bảo trì
- [ ] Những lỗi hay được cài sẵn trong đề: SQL injection, N+1, thiếu transaction, race
      condition check-then-act, không kiểm tra quyền (IDOR), không có timeout khi gọi API,
      nuốt exception, so sánh tiền bằng float, xử lý timezone sai
- [ ] Góp ý theo mức độ: lỗi chặn merge, nên sửa, tuỳ chọn; đề xuất cách sửa cụ thể

### Trong phòng phỏng vấn

**Khi gặp câu không biết**
- **Đừng bịa.** Người phỏng vấn nhận ra ngay, và bịa mất điểm nặng hơn không biết.
- Nói thật rồi suy luận tiếp: *"Phần này em chưa làm thực tế, nhưng theo em hiểu thì…
  vì X nên có thể là Y."* Người phỏng vấn đánh giá cách bạn suy nghĩ, không chỉ đáp án.
- Liên hệ với thứ gần nhất bạn biết: *"Em chưa dùng Kafka, nhưng em dùng Laravel queue
  với Redis, nên em hiểu vấn đề retry và idempotent…"*

**Khi bị đơ hoặc hoảng**
- Hít một hơi rồi nói: *"Cho em 30 giây suy nghĩ."* Đây là yêu cầu hoàn toàn bình thường.
- Quay về ví dụ nhỏ nhất, giải bằng tay trên giấy và tìm quy luật từ đó.
- Một câu làm tệ chưa phải là trượt. Điều quan trọng là **không để nó ảnh hưởng tới câu sau**.

**Khi bị hỏi vặn hoặc không đồng ý**
- Hỏi vặn thường là để kiểm tra độ sâu, không phải vì bạn sai. Giữ bình tĩnh, giải thích lý do.
- Nếu người phỏng vấn đưa góc nhìn khác, phân tích trade-off thay vì khăng khăng:
  *"Cách của anh/chị tốt hơn khi…, còn cách của em hợp khi…"*
- Nếu bạn nhận ra mình sai: nói thẳng "em nghĩ lại thì chỗ này em sai, vì…". Sửa sai nhanh
  là điểm cộng.

**Giao tiếp**
- Trả lời **có cấu trúc**: kết luận trước, giải thích sau. Ví dụ: *"Có 3 cách. Thứ nhất…"*
- Trả lời 1–2 phút rồi dừng, để người phỏng vấn tự đào sâu. Đừng độc thoại 10 phút.
- Dùng "em/tôi" khi kể việc mình làm; "chúng tôi" làm người nghe không biết bạn làm gì.
- Phỏng vấn online: kiểm tra mic, camera, mạng, chia sẻ màn hình từ trước; nhìn vào camera
  khi nói; tắt thông báo.

### Câu hỏi ngược cho người phỏng vấn
Trả lời "Dạ em không có câu hỏi gì" là bỏ phí cơ hội cuối để ghi điểm và để đánh giá công ty.

- [ ] Về team: bao nhiêu người, chia vai trò thế nào, ai là người mình báo cáo trực tiếp
- [ ] Về quy trình: từ lúc code xong đến production diễn ra thế nào, có code review, CI,
      môi trường staging không
- [ ] Về kỹ thuật: thách thức kỹ thuật lớn nhất trong 6 tháng tới; tech debt xử lý ra sao
- [ ] Về kỳ vọng: một người làm tốt vị trí này sau 3 tháng/6 tháng trông như thế nào
- [ ] Về vận hành: có on-call không, sự cố production được xử lý và postmortem thế nào
- [ ] Về phát triển: lộ trình lên level, đánh giá hiệu suất theo tiêu chí gì
- [ ] ⚠️ Không hỏi những thứ tra Google được trong 1 phút; câu về lương và phúc lợi để cho
      vòng HR

### Tâm lý trước và sau
- Phỏng vấn là **hai chiều**: bạn cũng đang đánh giá họ. Nghĩ như vậy thì bớt áp lực.
- Mock interview ít nhất 2–3 lần. Lần phỏng vấn thật đầu tiên thường là lần tệ nhất, nên
  xếp các công ty ít quan trọng lên trước để khởi động.
- Ngủ đủ giấc quan trọng hơn ôn thêm vào đêm cuối.
- Ghi lại **ngay sau buổi phỏng vấn** các câu đã bị hỏi và chỗ trả lời chưa tốt. Đây là tài
  liệu ôn giá trị nhất, và là nguồn để bổ sung vào bộ checklist này.
- Trượt là dữ liệu, không phải phán quyết về năng lực. Xin feedback nếu có thể.

### Lương và offer
- [ ] Tìm hiểu mặt bằng lương theo level và thành phố trước khi nói chuyện với HR
- [ ] Đưa ra một **khoảng** có cơ sở, đầu dưới là mức bạn thực sự chấp nhận được
- [ ] ⚠️ Chưa hiểu rõ phạm vi công việc thì có thể lùi câu trả lời: "Em muốn hiểu rõ hơn về
      vai trò rồi mới đưa con số chính xác"
- [ ] So sánh offer theo tổng thu nhập: lương gross/net, tháng 13, thưởng, bảo hiểm đóng
      trên mức lương nào, cổ phần, phụ cấp, ngày phép, remote, thời gian thử việc và lương thử việc
- [ ] Hỏi về lộ trình tăng lương và chu kỳ đánh giá
- [ ] Deal lịch sự, có lý do (offer khác, kinh nghiệm cụ thể); đã nhận lời thì giữ lời

---

## Senior trả lời khác gì

| Câu hỏi | Junior/mid thường trả lời | Senior trả lời |
|---|---|---|
| "Kể về dự án của bạn" | liệt kê tính năng và công nghệ | bối cảnh kinh doanh → vấn đề → quyết định kiến trúc và trade-off → kết quả đo được → nếu làm lại thì đổi gì |
| "Khó khăn lớn nhất?" | một bug khó | một vấn đề có nhiều ràng buộc (kỹ thuật, thời gian, con người) và cách cân bằng chúng |
| "Bất đồng với đồng nghiệp?" | "em giải thích và bạn ấy đồng ý" | tìm hiểu lý do của bên kia, dùng dữ liệu hoặc thử nghiệm nhỏ để quyết định, "disagree and commit" khi cần |
| "Vì sao chọn công nghệ X?" | "vì nó nhanh/phổ biến" | so với các lựa chọn khác theo tiêu chí cụ thể, cái giá phải trả, và điều kiện nào thì sẽ đổi |
| "Bạn có câu hỏi gì không?" | hỏi về phúc lợi | hỏi về thách thức kỹ thuật, cách team ra quyết định, kỳ vọng với vai trò |

---

## Tình huống

1. *Người phỏng vấn hỏi về một công nghệ ghi trong CV mà bạn chỉ dùng một lần cách đây 2 năm.*
   - Nói thật mức độ đã dùng và bối cảnh; trả lời phần mình còn nhớ chắc.
   - Rút kinh nghiệm: sửa CV, hoặc ôn lại trước buổi sau.

2. *Live coding được 15 phút, bạn nhận ra hướng giải đang đi sai.*
   - Dừng lại và nói ra: "Em thấy cách này không xử lý được trường hợp X, em đổi sang Y."
   - Nhận ra sai và đổi hướng sớm là điểm cộng; cố đi tiếp hướng sai mới là điểm trừ.

3. *Người phỏng vấn im lặng, không gợi ý gì, bạn không biết mình đúng hay sai.*
   - Chủ động hỏi: "Anh/chị muốn em đi sâu vào phần nào?" hoặc "Em đang giả định X, như vậy
     có ổn không?"

4. *HR hỏi mức lương hiện tại.*
   - Có thể chuyển sang mức mong muốn: "Em mong muốn trong khoảng A–B cho vị trí này, dựa
     trên…". Nếu nói lương hiện tại thì nói trung thực.

5. *Bạn có hai offer, công ty bạn thích hơn trả thấp hơn.*
   - Nói thẳng với công ty bạn thích: có offer khác, bạn ưu tiên họ, hỏi họ có điều chỉnh
     được không. Không bịa offer.

---

## ❓ Câu hỏi hay gặp

🟢
- Giới thiệu về bản thân.
- Vì sao bạn muốn đổi việc?
- Điểm mạnh và điểm yếu của bạn?
- Bạn học công nghệ mới thế nào?

🟡
- Kể về một sự cố production bạn từng xử lý.
- Kể về một lần bất đồng với đồng nghiệp.
- Khi yêu cầu không rõ ràng, bạn làm gì?
- Bạn cân bằng giữa tốc độ giao hàng và chất lượng code thế nào?

🔴
- Kể về một quyết định kỹ thuật lớn bạn đã dẫn dắt.
- Bạn giúp một thành viên yếu trong team tiến bộ thế nào?
- Kể về một lần bạn thay đổi được cách làm việc của team hoặc tổ chức.
- Bạn nói "không" với product/cấp trên thế nào?

---

## Bài tập tự làm

1. **Viết CV lại**: chọn 5 gạch đầu dòng hiện tại trong CV, viết lại theo khung *động từ +
   việc + cách làm + kết quả đo được*.
2. **Kho câu chuyện**: viết 6 câu chuyện theo STAR + Learning, điền bảng ánh xạ câu chuyện →
   câu hỏi. Đọc to và bấm giờ, mục tiêu dưới 3 phút mỗi câu.
3. **Giới thiệu bản thân**: viết bản 1 phút và bản 3 phút; 🟡 làm thêm bản tiếng Anh.
4. **Phân tích JD**: lấy 3 JD bạn định nộp, gạch từ khoá thành ba nhóm (bắt buộc, cộng điểm,
   tín hiệu ngầm) và đối chiếu với [bản đồ tổng](README.md).
5. **Câu hỏi ngược**: viết 5 câu hỏi ngược cho một công ty cụ thể bạn định nộp.

> Nộp bài vào đây để được review.
