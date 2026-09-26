# 25. Kỹ năng phỏng vấn

> [← Mục lục](README.md) · Trọng tâm: CV, kho câu chuyện STAR, từng loại vòng phỏng vấn, **chính sách dùng AI khi phỏng vấn (2026)**, câu hỏi ngược, deal lương trong bối cảnh thị trường Việt Nam.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay gặp.

File gồm hai phần:

1. **Lộ trình kiến thức** (phần chính): ba chặng theo thứ tự một đợt tìm việc: chuẩn bị hồ sơ và
   câu chuyện, luyện từng loại vòng, rồi xử lý trong phòng phỏng vấn và offer. Mỗi module có:
   - **Vì sao cần học**: kỹ năng này giúp gì trong đợt tìm việc và hay bị kiểm tra thế nào.
   - **Học gì**: các khung trả lời và kỹ năng, giải thích bằng lời thường kèm ví dụ tình huống
     thật, và các cạm bẫy ⚠️. Đọc phần này để biết cần học gì, rồi học sâu qua tài liệu ở mục Đọc.
   - **Đọc**: tài liệu gốc.
   - **Nắm chắc khi**: tiêu chí tự kiểm tra. Ở file này đó là **việc chuẩn bị làm được**: viết
     xong, tập xong, bấm giờ được. Chỉ tick khi đã làm xong thật.
2. **Câu hỏi thường gặp** (bonus): câu hỏi behavioral và tình huống, kèm hướng trả lời mong
   đợi, gồm ý phải có, điểm cộng và red flag. Dùng để tập kể, không dùng để học thuộc.

Nhiều ứng viên trượt ở phần này dù đã ôn kỹ kiến thức. Kiến thức giúp bạn qua vòng kỹ thuật;
phần này quyết định bạn có được offer và offer tốt hay không. Câu chuyện về quyết định, giao
hàng, dẫn dắt dành cho senior ở [24-senior-leadership.md](24-senior-leadership.md).

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Tech Interview Handbook](https://www.techinterviewhandbook.org/) | Hướng dẫn miễn phí | Resume, behavioral, câu hỏi ngược, negotiation. **Nguồn chính** của file này |
| [Amazon Leadership Principles](https://www.amazon.jobs/content/en/our-workplace/leadership-principles) | Tài liệu công ty | Bộ tiêu chí behavioral được nhiều công ty bắt chước; dùng để kiểm tra kho câu chuyện có phủ đủ không |
| [Anthropic: Guidance on Candidates' AI Usage](https://www.anthropic.com/candidate-ai-guidance) | Chính sách công ty | Ví dụ chính sách **cấm** AI trong vòng live và take-home, cho phép khi chuẩn bị |
| [Canva: Yes, You Can Use AI in Our Interviews](https://www.canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews/) | Blog kỹ thuật (6/2025) | Ví dụ vòng **yêu cầu** dùng AI coding assistant và cách họ chấm |
| [ITviec: Báo cáo Lương IT](https://itviec.com/bao-cao/luong-it-va-thi-truong-tuyen-dung-it-vietnam) | Báo cáo thị trường | Mặt bằng lương IT Việt Nam theo vị trí, số năm kinh nghiệm |
| [levels.fyi](https://www.levels.fyi/t/software-engineer/locations/vietnam) | Dữ liệu lương tự khai | Lương theo level ở công ty nước ngoài/product có văn phòng tại Việt Nam |
| Glassdoor (glassdoor.com) | Review công ty | Review quy trình phỏng vấn và văn hoá. Mẫu nhỏ ở Việt Nam, đọc có chọn lọc |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Hồ sơ và câu chuyện** | 1.1–1.4 | CV theo kết quả, giới thiệu 1 và 3 phút, kho 6–8 câu chuyện STAR có số liệu | 1 tuần, làm trước khi nộp đơn |
| **2. Từng loại vòng** | 2.1–2.5 | Biết mỗi vòng chấm gì, luyện đúng format; biết chính sách AI của từng công ty | 1–2 tuần, song song với ôn kỹ thuật |
| **3. Trong phòng và sau phỏng vấn** | 3.1–3.4 | Xử lý câu không biết, bị đơ, bị hỏi vặn; câu hỏi ngược; deal lương và so sánh offer | 3–4 ngày, ôn lại trước mỗi buổi |

Chặng 1 là nền cho mọi vòng: vòng behavioral, hiring manager, và cả câu "kể về dự án" ở vòng
kỹ thuật đều lấy chất liệu từ kho câu chuyện. Làm chặng 1 **trước** khi nộp đơn đầu tiên.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Hồ sơ và câu chuyện

#### 1.1 Đọc JD và hiểu quy trình

**Vì sao cần học:** JD là đề bài của cả quy trình tuyển dụng. Đọc kỹ JD cho bạn biết sẽ bị hỏi
gì và cần chuẩn bị câu chuyện nào. Hỏi recruiter về quy trình từ đầu giúp tránh bất ngờ về
format, đặc biệt là chính sách dùng AI, thứ mà năm 2026 mỗi công ty một khác.

**Học gì**

*Phân tích JD*
- *JD* (job description) là bản mô tả công việc mà công ty đăng tuyển.
- Chia các từ khoá trong JD thành ba nhóm:

  | Nhóm | Là gì | Ví dụ |
  |---|---|---|
  | Bắt buộc (must have) | thiếu là dễ bị loại ngay từ vòng lọc hồ sơ | "3+ năm PHP/Laravel", "MySQL" |
  | Cộng điểm (nice to have) | có thì hơn, không có vẫn được | "biết Go", "kinh nghiệm AWS" |
  | Tín hiệu ngầm | không ghi thẳng, nhưng cho biết sẽ bị hỏi gì | "hệ thống hàng triệu người dùng" nghĩa là sẽ hỏi scale và cache. "Fintech" nghĩa là sẽ hỏi transaction, idempotency, bảo mật |

  - *Idempotency* là tính chất gọi một thao tác nhiều lần cho kết quả như gọi một lần, ví dụ bấm
    "thanh toán" hai lần vẫn chỉ trừ tiền một lần.
- Mỗi từ khoá phải ứng với ít nhất một câu bạn trả lời được và, nếu có, một câu chuyện thực tế.

*Từ khoá chưa từng làm*
- Chuẩn bị sẵn câu "em chưa làm thực tế nhưng em hiểu là…", kèm một điểm liên hệ với thứ đã làm.
- Ví dụ: JD có Kafka, bạn chỉ dùng Laravel queue. Điểm liên hệ: retry, xử lý message trùng, thứ
  tự message. Đây là những vấn đề cả hai cùng gặp.

*Hỏi về quy trình*
- *Recruiter* là người của bộ phận tuyển dụng, liên lạc với bạn suốt quy trình.
- Hỏi recruiter trước:
  - có mấy vòng, mỗi vòng bao lâu,
  - làm bài bằng ngôn ngữ gì,
  - có được dùng IDE, Google, **AI** không.
- Đây là câu hỏi bình thường, không bị trừ điểm.
- Đọc review về quy trình phỏng vấn của công ty (Glassdoor, cộng đồng) để biết format. Không đọc
  để học thuộc đề.

*Cách các vòng được chấm*
- Mỗi vòng thường do một người chấm độc lập. Sau đó hội đồng mới gộp kết quả lại.
- ⚠️ Một vòng tệ chưa chắc đã trượt, nhưng đừng giả định vòng sau sẽ "bù" được.

**Đọc**
- Tech Interview Handbook: [Coding interview prep](https://www.techinterviewhandbook.org/coding-interview-prep/) (phần đầu về quy trình)
- Đối chiếu JD với [bản đồ tổng](README.md)

**Nắm chắc khi**
- [ ] Gạch xong 3 JD định nộp thành ba nhóm, mỗi từ khoá "bắt buộc" có một câu chuyện hoặc một module đã ôn đi kèm (bài tập 4)
- [ ] Có sẵn danh sách 5 câu hỏi về quy trình để hỏi recruiter, gồm câu về chính sách dùng AI

#### 1.2 CV, LinkedIn, GitHub

**Vì sao cần học:** CV là thứ người lọc hồ sơ chỉ đọc lướt trước khi quyết định có gọi bạn hay
không. Sau đó nó thành đề cương để người phỏng vấn kỹ thuật hỏi sâu. CV viết theo kết quả giúp
qua vòng lọc. CV chỉ ghi những gì bạn thật sự làm giúp không bị gãy khi bị hỏi.

**Học gì**

*Mỗi gạch đầu dòng là một kết quả*
- Khung: *động từ + việc đã làm + cách làm + kết quả đo được*.
- So sánh:
  - Kém: "Phát triển module báo cáo"
  - Tốt: "Viết lại export báo cáo theo kiểu streaming qua queue, giảm thời gian từ 30s xuống 2s
    và hết lỗi timeout với file 500k dòng"
- Tách dòng tốt theo khung để thấy rõ:

  | Phần | Nội dung |
  |---|---|
  | Động từ | Viết lại |
  | Việc đã làm | export báo cáo |
  | Cách làm | streaming qua queue: chạy ở background job, ghi file từng phần thay vì dựng cả file trong RAM |
  | Kết quả đo được | 30s xuống 2s, hết timeout với file 500k dòng |

- Không có số liệu thật thì dùng quy mô: số người dùng, số request, số bảng, số service, số
  người trong team.
  - Ví dụ: "Thiết kế schema và API cho module kho, phục vụ 40 cửa hàng, 3 dev cùng làm".

*Ghi gì và không ghi gì*
- ⚠️ Mọi công nghệ ghi trong CV đều có thể bị hỏi sâu. Thứ chỉ "đã đụng qua" thì đừng ghi, hoặc
  để ở một mục riêng.
- ⚠️ Không đưa thông tin bảo mật của công ty cũ, ví dụ tên khách hàng nội bộ hay doanh thu.
- ⚠️ Dùng AI để sửa câu chữ thì được, nhưng mọi con số và việc làm phải là thật và bạn giải thích
  được.
  - CV "trơn" do AI viết mà không kể sâu được là *red flag*, tức dấu hiệu khiến người chấm lo ngại.

*Hình thức*
- Dài 1–2 trang.
- Dự án gần nhất và liên quan nhất lên đầu.
- Kỹ năng gom theo nhóm, ví dụ: ngôn ngữ, database, hạ tầng.

*LinkedIn và GitHub*
- Khớp với CV: chức danh, thời gian, dự án.
- 🟡 Có bản tiếng Anh nếu nộp công ty nước ngoài hoặc công ty outsource.

**Đọc**
- Tech Interview Handbook: [Resume](https://www.techinterviewhandbook.org/resume/)

**Nắm chắc khi**
- [ ] Viết lại xong 5 gạch đầu dòng theo khung kết quả, mỗi dòng có một con số hoặc quy mô (bài tập 1)
- [ ] Với mỗi công nghệ trong CV, nói được 2 phút về một lần dùng thật và một cạm bẫy đã gặp

#### 1.3 Giới thiệu bản thân

**Vì sao cần học:** Gần như vòng nào cũng mở đầu bằng "giới thiệu về bản thân". Một phút đầu
đặt khung cho cả buổi: người phỏng vấn thường hỏi tiếp đúng vào thứ bạn vừa nhắc tới. Chuẩn bị
tốt thì bạn tự chọn được chủ đề mình sẽ bị hỏi.

**Học gì**

*Hai phiên bản*

| | Bản 1 phút | Bản 3 phút |
|---|---|---|
| Nội dung | hiện tại làm gì → 1–2 thành tựu nổi bật → vì sao quan tâm vị trí này | như bản 1 phút, thêm bối cảnh dự án, vai trò, công nghệ chính |
| Dùng khi | đầu hầu hết các vòng | khi người phỏng vấn muốn nghe kỹ hơn, thường ở vòng với hiring manager |

- Ví dụ khung bản 1 phút:

  > "Em là backend developer 5 năm, hiện làm PHP/Laravel cho một công ty thương mại điện tử
  > khoảng 200.000 đơn mỗi tháng. Việc em tự hào nhất năm qua là chuyển luồng tạo đơn sang queue,
  > giảm lỗi timeout giờ cao điểm từ 3% xuống gần 0. Em quan tâm vị trí này vì team đang làm hệ
  > thống thanh toán, đúng mảng em muốn đi sâu."

- Thành tựu nhắc trong bản 1 phút nên là thứ bạn **muốn** bị hỏi tiếp, vì câu tiếp theo thường
  sẽ là về nó.
- ⚠️ Đừng đọc lại CV từ năm đầu tiên. Người nghe đã có CV trong tay.

*Câu "vì sao đổi việc"*
- Nói về điều bạn đang tìm kiếm: quy mô hệ thống, lĩnh vực, cơ hội học.
- So sánh:
  - Kém: "Công ty cũ quản lý tệ, sếp không ghi nhận."
  - Tốt: "Em muốn làm hệ thống tải lớn hơn. Vị trí này có bài toán scale mà ở công ty hiện tại em
    chưa có cơ hội làm."
- ⚠️ Không nói xấu công ty cũ. Người nghe sẽ nghĩ sau này bạn cũng nói về họ như vậy.

**Đọc**
- Tech Interview Handbook: [Self introduction](https://www.techinterviewhandbook.org/self-introduction/)

**Nắm chắc khi**
- [ ] Viết xong và bấm giờ bản 1 phút và bản 3 phút, tiếng Việt; 🟡 thêm bản tiếng Anh (bài tập 3)
- [ ] Ghi âm bản 1 phút, nghe lại không có "ờ" kéo dài và không vượt 70 giây

#### 1.4 Kho câu chuyện STAR

**Vì sao cần học:** Vòng behavioral, vòng hiring manager, và cả câu "kể về dự án" ở vòng kỹ thuật
đều cần câu chuyện. Kể ngẫu hứng thường lan man, dùng "chúng tôi" nên không rõ bạn làm gì, và
thiếu kết quả. Có sẵn kho 6–8 câu chuyện có cấu trúc thì trả lời được phần lớn câu behavioral.

**Học gì**

*Khung STAR + Learning*
- *STAR* là khung kể chuyện 4 phần. File này thêm phần thứ năm là Learning.

  | Phần | Nghĩa | Lưu ý |
  |---|---|---|
  | Situation | bối cảnh | 1–2 câu, đủ để hiểu, không kể lịch sử công ty |
  | Task | nhiệm vụ hoặc vấn đề của bạn | 1 câu |
  | **Action** | bạn đã làm gì | **dài nhất**. Dùng "tôi" chứ không phải "chúng tôi" |
  | Result | kết quả | có số liệu |
  | Learning | rút ra điều gì, lần sau làm khác gì | 1–2 câu |

- Ví dụ một câu chuyện "tối ưu hệ thống chậm":
  - S: Trang danh sách đơn của admin mất 8 giây với shop có trên 50.000 đơn.
  - T: Tôi được giao đưa trang này xuống dưới 1 giây trước đợt sale.
  - A: Tôi bật slow query log (log MySQL ghi lại các query chạy lâu) và thấy hai vấn đề:
    - Lỗi N+1: mỗi đơn chạy thêm một query riêng để lấy khách hàng. Tôi sửa bằng eager loading,
      tức lấy hết khách hàng trong một query bằng `with('customer')`.
    - Câu `ORDER BY created_at` không có index phù hợp. Tôi thêm composite index
      `(shop_id, created_at)`. Xem [03-database-sql.md](03-database-sql.md).
  - R: Trang còn 300 ms, đợt sale không có lỗi timeout.
  - L: Sau đó tôi bật `Model::preventLazyLoading()` ở môi trường dev để lỗi N+1 báo ngay khi viết
    code.

*Số lượng và độ sâu*
- Chuẩn bị 6–8 câu chuyện, mỗi câu 2–3 phút khi kể.
- Sẵn sàng bị hỏi sâu 2–3 lớp. Với câu chuyện trên, các lớp có thể là:
  1. "Sao bạn biết là N+1?"
  2. "Vì sao không cache luôn trang đó?"
  3. "Index mới có làm chậm việc ghi đơn không?"

*Các câu chuyện cần có*
- Dự án tự hào nhất, kèm sơ đồ kiến trúc vẽ được trong 2 phút.
- Sự cố production.
- Bất đồng hoặc xung đột.
- Thất bại hoặc mắc lỗi.
- Học nhanh một thứ mới.
- 🟡 Quyết định kỹ thuật có trade-off.
- 🔴 Dẫn dắt hoặc mentor.
- 🔴 Ảnh hưởng tới người không báo cáo cho mình.

*Bảng ánh xạ*
- Một câu chuyện tốt dùng được cho nhiều câu hỏi. Lập bảng ánh xạ để khỏi phải chuẩn bị riêng
  cho từng câu:

  | Câu chuyện | Dùng cho câu hỏi về |
  |---|---|
  | Tối ưu hệ thống chậm | thành tựu, giải quyết vấn đề, kỹ thuật sâu |
  | Sự cố production | áp lực, trách nhiệm, học từ sai lầm |
  | Bất đồng về thiết kế | xung đột, thuyết phục, làm việc nhóm |
  | Deadline gấp | ưu tiên, đánh đổi chất lượng, giao tiếp với product |
  | Học công nghệ mới | tự học, thích nghi |
  | Mentor người mới 🔴 | dẫn dắt, phát triển người khác |

*Câu chuyện sự cố*
- Một sự cố xử lý tốt có giá trị hơn mười tính năng suôn sẻ, vì nó cho thấy cách bạn làm việc
  khi có áp lực.
- Khung 5 bước:
  1. Chuyện gì xảy ra và ảnh hưởng thế nào.
  2. Phát hiện bằng cách nào.
  3. *Root cause* (nguyên nhân gốc). Không dừng ở nguyên nhân bề mặt.
  4. Khắc phục tức thời.
  5. **Phòng ngừa lâu dài**.
- Ví dụ khung: *"Chạy test suite trên máy local, config test không tách DB nên test nối thẳng vào
  DB dev dùng chung. Các lệnh `TRUNCATE` trong test xoá sạch nhiều bảng. Root cause không nằm ở
  câu lệnh tôi gõ: test không có DB riêng, và `setUp()` âm thầm chạy migration. Sau đó tôi đã…"*
- ⚠️ Kể sự cố không đổ lỗi cho người khác, kể cả khi đúng là lỗi của người khác. Tập trung vào
  "hệ thống nào đã cho phép lỗi xảy ra".

*Kiểm tra độ phủ*
- Amazon Leadership Principles là bộ nguyên tắc Amazon dùng để chấm vòng behavioral, ví dụ
  Ownership, Dive Deep, Have Backbone; Disagree and Commit. Nhiều công ty khác hỏi theo các chủ
  đề tương tự.
- Đối chiếu kho câu chuyện với bộ nguyên tắc này. Nguyên tắc nào chưa có câu chuyện là lỗ hổng.

**Đọc**
- Tech Interview Handbook: [Behavioral interview](https://www.techinterviewhandbook.org/behavioral-interview/), [Behavioral interview questions](https://www.techinterviewhandbook.org/behavioral-interview-questions/)
- [Amazon Leadership Principles](https://www.amazon.jobs/content/en/our-workplace/leadership-principles)

**Nắm chắc khi**
- [ ] Viết xong 6 câu chuyện STAR + Learning, mỗi câu kể dưới 3 phút và có ít nhất một con số (bài tập 2)
- [ ] Điền xong bảng ánh xạ câu chuyện → câu hỏi cho cả 6 câu chuyện
- [ ] Nhờ một người hỏi vặn 3 lớp "vì sao" cho câu chuyện sự cố mà bạn vẫn trả lời được bằng chi tiết thật

---

### Chặng 2: Từng loại vòng

#### 2.1 Screening HR, coding test online

**Vì sao cần học:** Mỗi loại vòng chấm một thứ khác nhau. Luyện sai format (ví dụ chỉ giải
LeetCode mà vòng thật là review code) là lãng phí thời gian ôn. HR screening và coding test online
là hai vòng lọc đầu tiên: trượt ở đây thì không có cơ hội thể hiện kiến thức sâu.

**Học gì**

*Các loại vòng*
- Tên gọi cần biết:
  - *HR screening*: cuộc gọi ngắn với recruiter để lọc động lực, mức lương, khả năng giao tiếp.
  - *Coding test online*: bài code làm trên nền tảng chấm tự động, có giới hạn thời gian.
  - *Live coding*: giải bài trực tiếp trong khi người phỏng vấn xem và trao đổi.
  - *Take-home*: bài làm ở nhà, từ vài giờ tới vài ngày.
  - *System design*: thiết kế một hệ thống lớn trên bảng trắng, ví dụ "thiết kế hệ thống rút gọn
    link".
  - *Behavioral*: hỏi về cách bạn đã hành xử trong các tình huống thật.
- Mỗi vòng, người chấm tìm gì:

  | Vòng | Người chấm tìm gì | Chuẩn bị |
  |---|---|---|
  | HR screening | động lực, mức lương, giao tiếp, thời gian đi làm được | "vì sao đổi việc", khoảng lương, giới thiệu 1 phút |
  | Coding test online | code chạy đúng trong thời gian giới hạn | bài easy/medium bấm giờ, quen nền tảng (HackerRank, Codility) |
  | Live coding | cách suy nghĩ, giao tiếp, code sạch, edge case | module 2.2, [21-dsa.md](21-dsa.md) |
  | Take-home | chất lượng như code thật | module 2.3 |
  | Code review/debug | đọc hiểu code người khác, bug, bảo mật, hiệu năng | module 2.3, [20-testing-quality.md](20-testing-quality.md) |
  | Hỏi đáp kỹ thuật | độ sâu, hiểu "vì sao", kinh nghiệm thật | các file 01–23 |
  | System design | phân tích requirement, trade-off, dẫn dắt thảo luận | [16-system-design.md](16-system-design.md) |
  | Behavioral/manager | trách nhiệm, hợp tác, xử lý xung đột, độ chín chắn | kho câu chuyện (1.4) |
  | 🔴 Leadership | tầm ảnh hưởng, ra quyết định, phát triển người khác | [24-senior-leadership.md](24-senior-leadership.md) |

*Coding test online*
1. Đọc hết đề trước khi làm bài nào.
2. Làm bài chắc ăn trước.
3. Trước khi nộp, kiểm tra độ phức tạp của lời giải với kích thước input lớn nhất trong đề.
- ⚠️ Nền tảng chấm bằng *test ẩn* (hidden test), tức bộ test bạn không nhìn thấy. Test ẩn thường
  có edge case (mảng rỗng, số âm, giá trị trùng) và input lớn.
  - Ví dụ: đề cho n tới 10^5 mà lời giải O(n²) thì cần khoảng 10^10 phép tính, chắc chắn quá giờ.
    Big-O xem ở [21-dsa.md](21-dsa.md).

*Làm bài bằng PHP*
- Kiểm tra trước nền tảng hỗ trợ phiên bản PHP nào.
- Quen cách đọc input từ `STDIN`:

  ```php
  <?php
  declare(strict_types=1);

  $n = (int) trim(fgets(STDIN));                                  // dòng 1: số phần tử
  $nums = array_map('intval', explode(' ', trim(fgets(STDIN))));  // dòng 2: dãy số cách nhau bởi dấu cách
  fscanf(STDIN, "%d %d", $a, $b);                                 // dòng 3: hai số nguyên
  ```

  - ⚠️ `fgets` trả về cả ký tự xuống dòng ở cuối, nên luôn `trim` trước khi ép kiểu.

**Đọc**
- Tech Interview Handbook: [Coding interview rubrics](https://www.techinterviewhandbook.org/coding-interview-rubrics/) (người chấm cho điểm theo những gì)

**Nắm chắc khi**
- [ ] Làm xong 2 bài test online giả lập có bấm giờ trên HackerRank hoặc Codility bằng PHP
- [ ] Trả lời được 3 câu HR (vì sao đổi việc, mức lương mong muốn, khi nào đi làm được) mỗi câu dưới 1 phút

#### 2.2 Live coding

**Vì sao cần học:** Live coding chấm cách bạn suy nghĩ và giao tiếp nhiều hơn chấm lời giải
cuối cùng. Nhiều người giải được bài ở nhà nhưng trượt vì im lặng, lao vào code khi chưa hiểu đề,
hoặc cố đi tiếp một hướng sai. Một quy trình cố định giúp bạn không bị cuốn theo áp lực.

**Học gì**

*Quy trình 7 bước*
1. **Nhắc lại đề**. Hỏi về input/output, ràng buộc, kích thước dữ liệu, edge case.
2. **Nêu brute force trước** kèm big-O. *Brute force* là cách giải thẳng, thử mọi khả năng.
   *Big-O* là cách mô tả thời gian chạy tăng thế nào khi input lớn lên.
3. Đề xuất cách tối ưu, **đợi người phỏng vấn đồng ý** rồi mới code.
4. **Vừa code vừa nói**. Im lặng 5 phút là tín hiệu xấu.
5. Code xong **tự chạy tay** với một ví dụ và một edge case.
6. Nêu độ phức tạp cuối cùng và hướng cải thiện.
7. Bị gợi ý thì **đón nhận**, đừng cãi. Tiếp thu gợi ý tốt cũng được chấm điểm.

- Ví dụ 3 bước đầu với đề "tìm hai số trong mảng có tổng bằng k":
  - Bước 1: "Mảng đã sắp xếp chưa? Có số âm không? Không có cặp nào thì trả về gì?"
  - Bước 2: "Cách thẳng là thử mọi cặp, O(n²)."
  - Bước 3: "Nếu dùng một mảng kết hợp lưu các số đã gặp thì chỉ cần duyệt một lần, O(n) thời
    gian và O(n) bộ nhớ. Anh/chị thấy hướng này ổn không?"

*Luyện tập*
- Luyện viết code không có autocomplete: editor trơn hoặc giấy. Nhiều nền tảng phỏng vấn chỉ là
  một khung soạn thảo đơn giản.
- Đặt tên biến tử tế cả khi vội. `$seen` dễ đọc hơn `$a2`.

*Cạm bẫy*
- ⚠️ Đừng tối ưu sớm. Có lời giải đúng trước, rồi mới làm nhanh hơn.
- ⚠️ Đừng im lặng tìm lời giải "hoàn hảo" trong đầu. Người phỏng vấn không chấm được thứ họ không
  nghe thấy.
- Nhận ra đang đi sai hướng thì:
  1. dừng lại,
  2. nói ra,
  3. đổi hướng.
- Cố đi tiếp một hướng sai mới là điểm trừ, không phải việc đổi hướng.

**Đọc**
- Tech Interview Handbook: [Coding interview techniques](https://www.techinterviewhandbook.org/coding-interview-techniques/), [Mock interviews](https://www.techinterviewhandbook.org/mock-interviews/)
- Chi tiết pattern và quy trình làm bài: [21-dsa.md](21-dsa.md) module 1.5

**Nắm chắc khi**
- [ ] Làm xong 3 buổi mock live coding (với bạn hoặc tự ghi hình), nghe lại thấy đủ 7 bước
- [ ] Giải xong một bài medium trong 30 phút trên editor không autocomplete, nói liên tục

#### 2.3 Take-home và vòng code review/debug

**Vì sao cần học:** Take-home được chấm như code thật bạn sẽ viết khi vào làm, nên người chấm
nhìn cả README, test, cấu trúc, commit chứ không chỉ "chạy được". Vòng code review/debug ngày càng
phổ biến vì nó giống công việc hằng ngày của senior, và các lỗi được cài sẵn thường là những lỗi
kinh điển của backend PHP.

**Học gì**

*Take-home: phạm vi và thời gian*
- Hỏi rõ phạm vi và thời gian kỳ vọng trước khi làm.
- ⚠️ Làm quá nhiều chưa chắc được cộng điểm, còn thiếu phần bắt buộc thì chắc chắn bị trừ.

*Take-home: README trước tiên*
- README là thứ người chấm đọc đầu tiên. Cần có:
  - cách chạy bằng một lệnh,
  - giả định đã đặt ra,
  - quyết định thiết kế và trade-off,
  - việc sẽ làm thêm nếu có thời gian,
  - **AI đã dùng vào việc gì**, nếu được phép dùng.
- Ví dụ khung:

  ```markdown
  ## Chạy
  docker compose up   # rồi mở http://localhost:8080

  ## Giả định
  - Mỗi đơn chỉ có một mã giảm giá.

  ## Quyết định và trade-off
  - Dùng queue cho gửi email: request nhanh hơn, đổi lại phải theo dõi failed jobs.

  ## Nếu có thêm thời gian
  - Rate limit cho API tạo đơn.

  ## Dùng AI
  - Sinh khung test ban đầu, tôi viết lại phần assertion.
  ```

*Take-home: chất lượng code*
- Cấu trúc thư mục rõ ràng.
- Xử lý lỗi và validate input.
- Cấu hình qua biến môi trường. ⚠️ Không commit secret (API key, mật khẩu).
- Có test cho logic chính. Người chấm thường mở thư mục test đầu tiên.
- Commit nhỏ, message có ý nghĩa.
- Chuẩn bị giải thích và mở rộng bài ở vòng sau, ví dụ câu "nếu có 1 triệu user thì sao?".

*Vòng code review/debug*
- Đọc code theo thứ tự:
  1. code làm gì,
  2. có đúng không,
  3. lỗi biên và lỗi khi chạy đồng thời,
  4. bảo mật,
  5. hiệu năng,
  6. dễ đọc.
- Các lỗi hay được cài sẵn và dấu hiệu nhận ra trong code PHP:

  | Lỗi | Dấu hiệu |
  |---|---|
  | SQL injection | nối biến thẳng vào chuỗi SQL: `"... WHERE id = $id"` |
  | N+1 | `foreach ($orders as $o) { echo $o->user->name; }` mà không có `with('user')`, mỗi vòng lặp một query |
  | Thiếu transaction | trừ kho và tạo đơn là hai lệnh riêng. Lệnh sau lỗi thì lệnh trước vẫn còn |
  | Race check-then-act | kiểm tra rồi mới làm: `if ($stock > 0) { trừ kho }`. Hai request cùng qua được `if` |
  | Thiếu kiểm tra quyền (IDOR) | `Order::find($request->id)` mà không kiểm tra đơn đó có thuộc user đang đăng nhập |
  | Gọi API không timeout | gọi HTTP ra ngoài mà không đặt timeout. Guzzle mặc định chờ vô hạn |
  | Nuốt exception | `catch (\Exception $e) {}` để trống, lỗi biến mất không dấu vết |
  | Tiền bằng float | `0.1 + 0.2` ra `0.30000000000000004`. Tiền nên lưu bằng số nguyên (đồng, xu) hoặc `DECIMAL` |
  | Sai timezone | lưu giờ theo múi giờ server rồi so với giờ của người dùng ở múi khác |

  - *IDOR* (Insecure Direct Object Reference) là lỗi cho người dùng truy cập dữ liệu của người
    khác chỉ bằng cách đổi id trên URL hoặc request.
- Góp ý theo mức: chặn merge, nên sửa, tuỳ chọn. Mỗi góp ý kèm cách sửa cụ thể.

**Đọc**
- Google eng-practices: [How to do a code review](https://google.github.io/eng-practices/review/reviewer/), [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html)
- Bảo mật và testing: [10-security.md](10-security.md), [20-testing-quality.md](20-testing-quality.md)

**Nắm chắc khi**
- [ ] Có một repo mẫu (Laravel hoặc PHP thuần) với README đúng khung trên, chạy bằng một lệnh, có test
- [ ] Review xong một PR có cài sẵn 5 lỗi trong danh sách trên (tự viết hoặc nhờ bạn viết), tìm đủ trong 20 phút

#### 2.4 Hỏi đáp kỹ thuật, system design, behavioral: khung trả lời

**Vì sao cần học:** Vòng hỏi đáp kỹ thuật thường có nhiều câu ngắn liên tiếp. Không có khung thì
câu trả lời hoặc quá ngắn (chỉ định nghĩa) hoặc lan man. Mỗi dạng câu hỏi có một khung riêng, và
cách senior trả lời khác mid ở chỗ luôn nối về trade-off và kinh nghiệm thật.

**Học gì**

*Câu khái niệm*
- Dạng câu: "Index là gì?", "Transaction là gì?".
- Khung 4 bước:
  1. định nghĩa một câu,
  2. cách hoạt động,
  3. trade-off,
  4. ví dụ thực tế mình đã gặp.
- Ví dụ với "Index là gì?":
  1. "Index là cấu trúc dữ liệu sắp sẵn giá trị của một vài cột để tìm nhanh mà không đọc cả
     bảng."
  2. "InnoDB dùng B+tree, tra một dòng chỉ cần đọc vài page."
  3. "Đổi lại mỗi lần ghi phải cập nhật thêm index, tốn thêm đĩa và RAM."
  4. "Ở dự án cũ em thêm index `(shop_id, created_at)` làm trang đơn hàng từ 8 giây xuống 300 ms."

*Câu so sánh "A khác B thế nào?"*
1. Điểm giống.
2. Khác biệt chính.
3. Khi nào dùng A, khi nào dùng B.
4. Mình đã chọn gì ở dự án và vì sao.

*Câu debug, sự cố*
- Dạng câu: "API đột nhiên chậm, bạn làm gì?".
1. Thu hẹp phạm vi: một endpoint hay tất cả, bắt đầu từ lúc nào, có deploy gì không.
2. Xem số liệu: metric, log, trace.
3. Đặt giả thuyết và kiểm chứng.
4. Giảm thiệt hại trước, sửa gốc sau.
5. Phòng ngừa.

*Câu thiết kế nhỏ*
- Dạng câu: "Thiết kế API đặt hàng".
1. Requirement.
2. Data model.
3. API.
4. Luồng chính.
5. Luồng lỗi: request trùng, timeout, nhiều request đồng thời.
6. Trade-off.

*Behavioral và system design*
- Câu behavioral: STAR + Learning (module 1.4).
- System design: phương pháp ở [16-system-design.md](16-system-design.md).

*Senior trả lời khác mid*

| Câu hỏi | Junior/mid thường trả lời | Senior trả lời |
|---|---|---|
| "Kể về dự án của bạn" | liệt kê tính năng và công nghệ | bối cảnh kinh doanh → vấn đề → quyết định kiến trúc và trade-off → kết quả đo được → làm lại thì đổi gì |
| "Khó khăn lớn nhất?" | một bug khó | một vấn đề nhiều ràng buộc (kỹ thuật, thời gian, con người) và cách cân bằng |
| "Vì sao chọn công nghệ X?" | "vì nó nhanh/phổ biến" | so với lựa chọn khác theo tiêu chí cụ thể, cái giá, điều kiện nào thì đổi |

**Đọc**
- Tech Interview Handbook: [System design](https://www.techinterviewhandbook.org/system-design/)

**Nắm chắc khi**
- [ ] Trả lời thành tiếng xong 5 câu khái niệm từ các file 01–23 theo đúng khung 4 bước, mỗi câu dưới 2 phút
- [ ] Kể xong "dự án tự hào nhất" theo cột Senior của bảng, kèm sơ đồ vẽ trong 2 phút

#### 2.5 Dùng AI trong phỏng vấn (2026)

**Vì sao cần học:** Năm 2026, chính sách dùng AI khi phỏng vấn khác nhau giữa các công ty, và
khác cả giữa các vòng trong cùng một công ty. Dùng AI khi bị cấm có thể khiến bạn bị loại. Còn ở
vòng cho phép dùng, người chấm đánh giá cách bạn làm việc cùng AI, một kỹ năng cần luyện riêng.
Câu "bạn dùng AI trong công việc thế nào" cũng đã thành câu hỏi phổ biến.

**Học gì**

*Hai hướng chính sách*
- Chính sách **khác nhau theo từng công ty, từng vòng**. Có hai hướng:

  | | Cho phép hoặc yêu cầu dùng AI | Cấm dùng AI |
  |---|---|---|
  | Ví dụ | Canva từ 2025 thay vòng CS fundamentals bằng vòng AI-assisted coding cho backend, frontend, ML. Meta thử nghiệm vòng coding có cửa sổ AI tích hợp | nhiều công ty cấm trong live interview và take-home trừ khi được cho phép rõ, ví dụ Anthropic |
  | Dạng đề | bài thực tế lớn hơn: mở rộng codebase có sẵn, debug, thêm tính năng, thay vì bài thuật toán ngắn | bài như truyền thống |
  | Hậu quả khi làm sai | không kiểm chứng được output của AI thì bị đánh giá thấp | một số công ty cảnh báo dùng AI khi bị cấm có thể bị loại khỏi quy trình |

- *AI coding assistant* là công cụ AI hỗ trợ viết code ngay trong editor hoặc terminal.

*Hỏi trước*
- ⚠️ Luôn **hỏi recruiter trước**:
  - vòng nào được dùng,
  - dùng công cụ gì,
  - có phải chia sẻ màn hình không.
- Không rõ thì mặc định là **không** được dùng.

*Khi được dùng: người chấm nhìn gì*
- Người chấm nhìn cách bạn làm việc cùng AI, không nhìn AI giỏi tới đâu:
  1. Tự chia vấn đề và hỏi rõ requirement **trước** khi nhờ AI.
  2. Đưa đủ ngữ cảnh, yêu cầu từng phần nhỏ.
  3. **Kiểm chứng output**: đọc từng diff, chạy test, thử edge case.
  4. Chỉ ra được lỗi trong code AI sinh: sai logic, thiếu xử lý lỗi, lỗ hổng bảo mật, gọi API
     không tồn tại.
  5. **Giải thích được mọi dòng** được giữ lại, và vì sao bỏ phần AI đề xuất sai.
  6. Nói ra khi nào tự viết nhanh hơn là hỏi AI.
- ⚠️ Red flag:
  - dán nguyên đề vào AI, nhận kết quả mà không đọc,
  - không trả lời được "dòng này làm gì".

*Khi bị cấm*
- ⚠️ **Không đọc câu trả lời từ AI** trong phỏng vấn online.
- Rất dễ lộ:
  - mắt nhìn chỗ khác,
  - độ trễ bất thường trước mỗi câu trả lời,
  - câu trả lời trơn tru nhưng không đào sâu được ở câu hỏi tiếp theo,
  - nhiều nền tảng có giám sát.
- Người phỏng vấn giỏi luôn hỏi tiếp 2–3 lớp. Câu trả lời không phải của bạn sẽ gãy ở lớp thứ hai.
- Bị phát hiện là mất cơ hội ở công ty đó, và đó là vi phạm tính trung thực.

*Dùng AI để chuẩn bị*
- Thường được chấp nhận:
  - mock interview,
  - nhờ AI hỏi vặn câu chuyện STAR,
  - review CV: tự viết bản nháp trước, AI chỉ để chỉnh.

*Câu "Bạn dùng AI trong công việc thế nào?"*
- Đây là câu hỏi mới nhưng hay gặp. Câu trả lời tốt có:
  - workflow thật: việc nào dùng, việc nào không,
  - cách kiểm chứng output,
  - giới hạn, ví dụ không đưa code hay dữ liệu khách hàng lên công cụ mà công ty không cho phép,
  - một lần AI sai và bạn phát hiện ra.
- Xem thêm [23-ai-llm-backend.md](23-ai-llm-backend.md).

**Đọc**
- Cách dùng AI khi làm việc và cách kể về nó: [26-ai-assisted-engineering.md](26-ai-assisted-engineering.md)
- Anthropic: [Guidance on Candidates' AI Usage](https://www.anthropic.com/candidate-ai-guidance)
- Canva: [Yes, You Can Use AI in Our Interviews](https://www.canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews/) (đọc phần họ chấm gì)
- Hello Interview: [Meta's AI-Enabled Coding Interview](https://www.hellointerview.com/blog/meta-ai-enabled-coding) (nguồn thứ cấp, mô tả format vòng của Meta)

**Nắm chắc khi**
- [ ] Làm xong một bài "mở rộng codebase có sẵn" 60 phút với AI assistant, vừa làm vừa nói, sau đó giải thích được mọi dòng đã giữ lại
- [ ] Tìm được ít nhất 2 lỗi trong code AI sinh ra ở bài trên và nói được vì sao test chưa bắt được
- [ ] Viết xong câu trả lời 2 phút cho "Bạn dùng AI trong công việc thế nào?", có một ví dụ AI sai
- [ ] Ghi xong chính sách AI của từng công ty đang ứng tuyển (hỏi recruiter hoặc đọc trang tuyển dụng)

---

### Chặng 3: Trong phòng và sau phỏng vấn

#### 3.1 Giao tiếp và tình huống khó

**Vì sao cần học:** Trong phòng phỏng vấn, cách bạn xử lý lúc không biết, lúc bị đơ, lúc bị phản
bác được chấm nhiều như kiến thức. Người phỏng vấn cố tình đẩy tới giới hạn hiểu biết của bạn để
xem bạn phản ứng ra sao. Bịa hay cãi cố ở lúc đó mất điểm nặng hơn nhiều so với nói "em chưa biết".

**Học gì**

*Gặp câu không biết*
- **Đừng bịa.** Người phỏng vấn nhận ra ngay, và bịa mất điểm nặng hơn không biết.
- Nói thật rồi suy luận: *"Phần này em chưa làm thực tế, nhưng theo em hiểu thì… vì X nên có thể
  là Y"*.
- Liên hệ với thứ gần nhất đã làm: *"Em chưa dùng Kafka, nhưng em dùng Laravel queue với Redis,
  nên em hiểu vấn đề retry và idempotent…"*

*Bị đơ*
1. Xin thời gian: *"Cho em 30 giây suy nghĩ"*.
2. Quay về ví dụ nhỏ nhất và giải bằng tay.
3. Qua câu đó rồi thì để nó lại phía sau. Một câu tệ chưa phải là trượt, đừng để nó ảnh hưởng
   câu tiếp theo.

*Bị hỏi vặn hoặc bị phản bác*
- Hỏi vặn thường là để kiểm tra độ sâu, không phải vì bạn sai.
- Phân tích trade-off thay vì khăng khăng: *"Cách của anh/chị tốt hơn khi…, còn cách của em hợp
  khi…"*.
- Nhận ra mình sai thì nói thẳng. Sửa sai nhanh là điểm cộng.

*Người phỏng vấn im lặng*
- Chủ động hỏi: *"Anh/chị muốn em đi sâu phần nào?"*
- Hoặc xác nhận giả định: *"Em đang giả định X, như vậy ổn không?"*

*Cách nói*
- Kết luận trước, giải thích sau: *"Có 3 cách. Thứ nhất…"*.
- Trả lời 1–2 phút rồi dừng, để người phỏng vấn chọn chỗ đào sâu.
- Dùng "em" hoặc "tôi" khi kể việc mình làm, không dùng "chúng em" cho mọi thứ.

*Phỏng vấn online*
- Kiểm tra trước mic, camera, mạng, chia sẻ màn hình.
- Nhìn vào camera khi nói.
- Tắt thông báo.

**Đọc**
- Tech Interview Handbook: [Behavioral interview](https://www.techinterviewhandbook.org/behavioral-interview/) (phần tips khi trả lời)

**Nắm chắc khi**
- [ ] Nhờ người mock hỏi 3 câu bạn không biết; ghi âm và nghe lại thấy không bịa, có suy luận từ thứ đã biết
- [ ] Tập xong một buổi mock mà người hỏi cố tình phản bác thiết kế của bạn, bạn trả lời bằng trade-off chứ không bằng "nhưng mà"

#### 3.2 Câu hỏi ngược cho người phỏng vấn

**Vì sao cần học:** Cuối gần như mọi vòng đều có câu "bạn có câu hỏi gì không". Đây là cơ hội
cuối để ghi điểm, và là lúc duy nhất bạn thu được thông tin thật để quyết có nên nhận offer. Câu
hỏi tốt cho thấy bạn đã tìm hiểu công ty và nghĩ như người sẽ làm việc ở đó.

**Học gì**

*Vì sao phải hỏi*
- "Dạ em không có câu hỏi gì" là bỏ phí cơ hội cuối để ghi điểm và để đánh giá công ty.
- Phỏng vấn là hai chiều: câu trả lời của họ cho bạn biết công việc thật sẽ thế nào (module 3.4).

*Chủ đề nên hỏi*

| Chủ đề | Ví dụ câu hỏi |
|---|---|
| Team | bao nhiêu người, chia vai trò thế nào, báo cáo cho ai |
| Quy trình | từ code xong tới production thế nào, có code review, CI, staging không |
| Kỹ thuật | thách thức lớn nhất 6 tháng tới là gì, tech debt được xử lý ra sao |
| Kỳ vọng | người làm tốt vị trí này sau 3 tháng, 6 tháng trông thế nào |
| Vận hành | có on-call không, sự cố và postmortem được xử lý thế nào |
| Phát triển | lộ trình lên level, đánh giá hiệu suất theo tiêu chí gì |
| Công cụ | team dùng AI coding assistant thế nào, có chính sách gì |

- Nghe cả cách họ trả lời. Ví dụ hỏi về tech debt mà nhận câu "bên anh không có tech debt" thì
  hoặc họ không nhìn thấy, hoặc họ không muốn nói.

*Nên tránh*
- ⚠️ Không hỏi thứ tra Google được trong 1 phút, ví dụ "công ty làm sản phẩm gì".
- Lương và phúc lợi để dành cho vòng HR.

*Góc senior*
- Senior hỏi về cách team ra quyết định và kỳ vọng với vai trò, không chỉ hỏi về phúc lợi.
  - Ví dụ: "Khi có bất đồng về thiết kế giữa hai team thì ai là người quyết?"

**Đọc**
- Tech Interview Handbook: [Final questions](https://www.techinterviewhandbook.org/final-questions/)

**Nắm chắc khi**
- [ ] Viết xong 5 câu hỏi ngược cho một công ty cụ thể, trong đó ít nhất 2 câu chỉ hỏi được sau khi đã đọc về sản phẩm của họ (bài tập 5)

#### 3.3 Lương và offer (thị trường Việt Nam)

**Vì sao cần học:** Chênh lệch vài triệu mỗi tháng lúc deal lương tích lại thành số tiền lớn
qua nhiều năm, vì lần tăng lương sau thường tính trên mức hiện tại. Ở Việt Nam, hai offer cùng
con số "gross" có thể khác nhau nhiều về thu nhập thật, tuỳ bảo hiểm đóng trên mức nào, có tháng
13 không, thử việc thế nào. Không hiểu các khoản này thì dễ chọn sai offer.

**Học gì**

*Tìm mặt bằng lương*
- Tìm mặt bằng lương theo level và thành phố **trước** khi nói chuyện với HR. Các nguồn:
  - báo cáo lương của ITviec,
  - levels.fyi, cho công ty nước ngoài và công ty product có văn phòng ở Việt Nam,
  - hỏi người quen trong ngành.

*Đưa con số*
- Đưa một **khoảng** có cơ sở. Đầu dưới của khoảng là mức bạn thực sự chấp nhận được, vì HR
  thường chọn gần đầu dưới.
- ⚠️ Chưa hiểu rõ phạm vi công việc thì có thể lùi lại: "Em muốn hiểu rõ hơn về vai trò rồi mới
  đưa con số chính xác".
- Bị hỏi lương hiện tại: có thể chuyển sang nói mức mong muốn. Nếu nói thì nói trung thực.

*So sánh offer theo tổng thu nhập*
- *Gross* là lương trước thuế và bảo hiểm. *Net* là số thực nhận sau khi trừ bảo hiểm phần người
  lao động đóng và thuế thu nhập cá nhân (TNCN).
- Các khoản cần so:
  - **Gross hay net**. Tính net theo biểu thuế TNCN và mức giảm trừ gia cảnh hiện hành. Từ kỳ
    tính thuế 2026: 15,5 triệu/tháng cho bản thân, 6,2 triệu/tháng cho mỗi người phụ thuộc.
    - *Giảm trừ gia cảnh* là phần thu nhập không bị tính thuế.
  - **Tháng 13 và thưởng**. Luật không bắt buộc tháng 13, nên hỏi rõ có ghi trong hợp đồng không.
  - **Bảo hiểm đóng trên mức lương nào**.
    - ⚠️ Công ty đóng bảo hiểm trên mức thấp hơn lương thực thì net cao hơn trước mắt, nhưng bạn
      thiệt quyền lợi: thai sản, thất nghiệp, hưu trí đều tính theo mức đóng.
  - **Thử việc**. Bộ luật Lao động 2019 giới hạn thời gian thử việc tối đa 60 ngày với công việc
    cần trình độ cao đẳng trở lên. Lương thử việc ít nhất bằng 85% lương chính thức.
  - **Các khoản khác**:
    - cổ phần hoặc *ESOP* (quyền mua cổ phần của công ty). Hỏi điều kiện *vesting*, tức phải làm
      bao lâu mới được nhận, và cổ phần đó có bán được không,
    - phụ cấp,
    - ngày phép,
    - remote hoặc hybrid,
    - bảo hiểm sức khoẻ riêng.
  - **Hợp đồng với công ty nước ngoài không có pháp nhân ở Việt Nam**: hỏi rõ loại hợp đồng, ai
    đóng bảo hiểm, ai khai thuế.
- Hỏi lộ trình tăng lương và chu kỳ đánh giá.

*Deal*
- Deal lịch sự và có lý do: có offer khác, có kinh nghiệm cụ thể khớp với vị trí.
- ⚠️ Không bịa offer.
- ⚠️ Đã nhận lời thì giữ lời.

**Đọc**
- Tech Interview Handbook: [Understanding compensation](https://www.techinterviewhandbook.org/understanding-compensation/), [Negotiation](https://www.techinterviewhandbook.org/negotiation/), [Ten rules of negotiation](https://www.techinterviewhandbook.org/negotiation-rules/)
- [ITviec: Báo cáo Lương IT & Thị trường tuyển dụng IT Việt Nam](https://itviec.com/bao-cao/luong-it-va-thi-truong-tuyen-dung-it-vietnam)
- [levels.fyi: Software Engineer, Vietnam](https://www.levels.fyi/t/software-engineer/locations/vietnam)

**Nắm chắc khi**
- [ ] Ghi xong khoảng lương mục tiêu có ít nhất 2 nguồn dẫn chứng, và mức tối thiểu bạn nhận
- [ ] Lập xong bảng so sánh offer (gross, net, tháng 13, thưởng, bảo hiểm, thử việc, phép, remote) và điền thử với lương hiện tại
- [ ] Tập nói thành tiếng câu đưa khoảng lương và câu deal lại, mỗi câu dưới 30 giây

#### 3.4 Tâm lý, mock, sau phỏng vấn

**Vì sao cần học:** Kết quả phỏng vấn phụ thuộc nhiều vào trạng thái lúc vào phòng và vào việc
bạn học được gì sau mỗi buổi. Người chuẩn bị kỹ vẫn có thể trượt vì lần phỏng vấn thật đầu tiên
rơi đúng công ty mình muốn nhất. Ghi chép sau mỗi buổi là cách nhanh nhất để buổi sau tốt hơn.

**Học gì**

*Phỏng vấn là hai chiều*
- Bạn cũng đang đánh giá họ: team, quy trình, người quản lý tương lai.
- Nghĩ theo cách này giúp bớt căng thẳng, và giúp bạn hỏi được câu hỏi ngược tốt (module 3.2).

*Mock và thứ tự công ty*
- *Mock interview* là buổi phỏng vấn thử, với bạn bè, đồng nghiệp, hoặc tự ghi hình.
- Mock ít nhất 2–3 lần trước khi phỏng vấn thật.
- Lần phỏng vấn thật đầu tiên thường tệ nhất. Xếp công ty ít quan trọng lên trước để khởi động.

*Trước buổi phỏng vấn*
- Ngủ đủ quan trọng hơn ôn thêm vào đêm cuối.

*Sau buổi phỏng vấn*
- Ghi lại **ngay sau buổi** các câu đã bị hỏi và chỗ trả lời chưa tốt.
- Đây là tài liệu ôn giá trị nhất, và là nguồn để bổ sung bộ checklist này.

*Khi trượt*
- Trượt là dữ liệu, không phải phán quyết về năng lực.
- Xin feedback nếu có thể.
  - ⚠️ Nhiều công ty không được phép đưa feedback chi tiết. Đừng hiểu đó là thiếu tôn trọng.

*Khi có hai offer*
- Công ty bạn thích hơn lại trả thấp hơn:
  1. Nói thẳng với họ là bạn có offer khác.
  2. Nói bạn ưu tiên họ.
  3. Hỏi họ có điều chỉnh được không.

**Đọc**
- Tech Interview Handbook: [Mock interviews](https://www.techinterviewhandbook.org/mock-interviews/)

**Nắm chắc khi**
- [ ] Có file ghi chép sau mỗi buổi phỏng vấn: câu hỏi, chỗ trả lời chưa tốt, module cần ôn lại
- [ ] Xếp xong lịch phỏng vấn với ít nhất 1 công ty "khởi động" trước công ty ưu tiên

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: kể thành tiếng bằng câu chuyện thật của bạn, bấm giờ, rồi đối chiếu với hướng trả
lời. Câu nào không có chất liệu thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Giới thiệu về bản thân.** (1.3)
- Ý phải có: hiện tại làm gì, 1–2 thành tựu có số liệu, vì sao quan tâm vị trí này; dưới 1–2 phút
- Red flag: đọc lại CV theo thứ tự thời gian

**2. Vì sao bạn muốn đổi việc?** (1.3)
- Ý phải có: điều bạn đang tìm kiếm (quy mô hệ thống, lĩnh vực, cơ hội học) và vì sao công ty này có
- Red flag: nói xấu công ty hoặc sếp cũ

**3. Điểm mạnh và điểm yếu của bạn?** (1.4)
- Ý phải có: điểm mạnh có ví dụ; điểm yếu thật, kèm việc đang làm để cải thiện và tiến bộ đã thấy
- Red flag: "em cầu toàn quá" hoặc điểm yếu giả

**4. Bạn học công nghệ mới thế nào?** (1.4)
- Ý phải có: một ví dụ cụ thể, nguồn học (docs gốc, làm dự án nhỏ), thời gian, kết quả áp dụng
- Điểm cộng: cách kiểm chứng mình đã hiểu (viết test, giải thích lại cho người khác); dùng AI để học nhưng kiểm chứng với docs

**5. Vì sao chọn công ty này?** (1.1)
- Ý phải có: chi tiết về sản phẩm, tech stack, bài toán kỹ thuật mà bạn đã tìm hiểu
- Red flag: câu trả lời dùng được cho mọi công ty

### 🟡 Mid

**6. Kể về dự án bạn tự hào nhất.** (1.4, 2.4)
- Ý phải có: bối cảnh kinh doanh, vai trò của bạn, quyết định kỹ thuật và trade-off, kết quả đo được
- Điểm cộng: vẽ sơ đồ trong 2 phút; nói được nếu làm lại thì đổi gì
- Red flag: liệt kê công nghệ; dùng "chúng tôi" suốt nên không rõ bạn làm gì

**7. Kể về một sự cố production bạn từng xử lý.** (1.4)
- Ý phải có: đủ 5 bước (ảnh hưởng, phát hiện, root cause, khắc phục, phòng ngừa)
- Điểm cộng: root cause ở tầng hệ thống; thay đổi quy trình/tooling để cả team không gặp lại
- Red flag: đổ lỗi; dừng ở "em sửa bug"

**8. Kể về một lần bất đồng với đồng nghiệp hoặc lead.** (1.4, 3.1)
- Ý phải có: hiểu lý do của bên kia, dùng dữ liệu hoặc thử nghiệm nhỏ để quyết, kết quả
- Điểm cộng: disagree and commit; một lần bạn là người đổi ý
- Red flag: "em giải thích và bạn ấy đồng ý" mà không có chi tiết

**9. Một lần bạn mắc lỗi và cách xử lý.** (1.4)
- Ý phải có: nhận lỗi rõ ràng, giảm thiệt hại, báo ai và lúc nào, thay đổi gì để không lặp lại
- Red flag: chọn lỗi vô hại để kể; không có bài học

**10. Khi yêu cầu không rõ ràng, bạn làm gì?** (1.4)
- Ý phải có: viết lại yêu cầu, liệt kê trường hợp biên, xác nhận với product, kèm ví dụ thật
- Điểm cộng: phát hiện vấn đề thật của người dùng khác với yêu cầu

**11. Bạn cân bằng tốc độ giao hàng và chất lượng code thế nào?** (1.4)
- Ý phải có: đánh đổi có ý thức và nói ra; ghi tech debt có kế hoạch trả; không lặng lẽ bỏ test
- Điểm cộng: ví dụ deadline gấp có số liệu phạm vi đã cắt. Xem [24-senior-leadership.md](24-senior-leadership.md)

**12. Bạn dùng AI trong công việc thế nào?** (2.5)
- Ý phải có: workflow thật (việc nào dùng, việc nào không), cách kiểm chứng output, giới hạn về bảo mật dữ liệu
- Điểm cộng: một lần AI sai và bạn phát hiện nhờ test/review; số liệu năng suất có cơ sở
- Red flag: "AI viết hết, em chỉ chạy"; hoặc từ chối dùng AI mà không có lý do

**13. Mức lương mong muốn của bạn là bao nhiêu?** (3.3)
- Ý phải có: khoảng có cơ sở (nguồn thị trường, kinh nghiệm), nói rõ gross hay net
- Điểm cộng: hỏi lại cơ cấu thu nhập (thưởng, tháng 13, bảo hiểm) trước khi chốt
- Red flag: đưa một con số không có cơ sở; nói dối lương hiện tại

### 🔴 Senior

**14. Kể về một quyết định kỹ thuật lớn bạn đã dẫn dắt.** (1.4, 2.4)
- Ý phải có: bối cảnh, các phương án, tiêu chí, cái giá, cách đưa quyết định qua các bên, kết quả
- Điểm cộng: design doc/ADR; nhìn lại với thông tin hiện tại. Xem [24-senior-leadership.md](24-senior-leadership.md) module 1.2

**15. Bạn giúp một thành viên yếu trong team tiến bộ thế nào?** (1.4)
- Ý phải có: người cụ thể, nguyên nhân yếu, kế hoạch, kết quả đo được sau vài tháng
- Red flag: "em trả lời khi bạn ấy hỏi"

**16. Kể về một lần bạn thay đổi được cách làm việc của team hoặc tổ chức.** (1.4)
- Ý phải có: vấn đề, cách thuyết phục (dữ liệu, thử nghiệm nhỏ), người phản đối và cách xử lý, số liệu trước/sau
- Red flag: nhờ cấp trên ép

**17. Bạn nói "không" với product hoặc cấp trên thế nào?** (1.4)
- Ý phải có: không từ chối trần trụi, đưa lựa chọn phạm vi/thời gian kèm rủi ro; một ví dụ thật
- Điểm cộng: nói bằng hệ quả kinh doanh; ghi lại quyết định

**18. Tình huống: bị hỏi sâu về một công nghệ ghi trong CV mà bạn chỉ dùng một lần cách đây 2 năm.** (1.2, 3.1)
- Ý phải có: nói thật mức độ đã dùng và bối cảnh; trả lời phần còn nhớ chắc; không bịa
- Điểm cộng: liên hệ sang thứ tương tự đang dùng; sau buổi đó sửa CV

**19. Tình huống: vòng live coding cho phép dùng AI, AI sinh ra lời giải chạy được ngay. Người phỏng vấn hỏi "vì sao đúng?"** (2.5)
- Ý phải có: giải thích được logic và độ phức tạp bằng lời của mình; chỉ ra edge case đã kiểm tra; nói phần nào đã sửa so với bản AI đưa
- Red flag: "AI viết nên em nghĩ là đúng"

**20. Tình huống: có hai offer, công ty bạn thích hơn trả thấp hơn.** (3.3, 3.4)
- Ý phải có: nói thẳng với công ty thích hơn là có offer khác và bạn ưu tiên họ, hỏi có điều chỉnh được không; so sánh bằng tổng thu nhập và cơ hội
- Red flag: bịa offer; nhận lời rồi rút

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
6. **AI-assisted coding**: chọn một repo Laravel nhỏ, đặt đề "thêm tính năng X và sửa một bug
   cài sẵn" trong 60 phút, làm cùng AI assistant, ghi lại: prompt đã dùng, chỗ AI sai, cách bạn
   kiểm chứng. Rồi làm lại một bài tương tự **không** dùng AI và so sánh.
7. **Bảng offer**: lập bảng so sánh theo module 3.3, điền cho công việc hiện tại và một offer
   giả định, tính net cho cả hai.

> Nộp bài vào đây để được review.
