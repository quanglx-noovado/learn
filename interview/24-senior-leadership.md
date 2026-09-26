# 24. Kỹ năng senior: ra quyết định, giao hàng, dẫn dắt

> [← Mục lục](README.md) · Trọng tâm: những gì tách senior khỏi mid ngoài kiến thức kỹ thuật: ra quyết định kỹ thuật, giao hàng khi có rủi ro, migration, dẫn dắt sự cố, mentor, ảnh hưởng xuyên team.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay gặp.

File gồm hai phần:

1. **Lộ trình kiến thức** (phần chính): ba chặng theo phạm vi ảnh hưởng, từ quyết định kỹ thuật
   tới giao hàng rồi tới con người. Mỗi module có:
   - **Vì sao cần học**: kỹ năng này dùng vào việc gì và hay bị hỏi thế nào.
   - **Học gì**: các khung tư duy và kỹ năng, giải thích bằng lời thường kèm ví dụ tình huống
     thật, và các cạm bẫy ⚠️. Đọc phần này để biết cần học gì, rồi học sâu qua tài liệu ở mục Đọc.
   - **Đọc**: tài liệu gốc.
   - **Nắm chắc khi**: tiêu chí tự kiểm tra. Ở file này đó là **việc chuẩn bị làm được**: viết
     xong một câu chuyện, một tài liệu, kể được trong thời gian giới hạn. Chỉ tick khi đã làm
     xong thật.
2. **Câu hỏi thường gặp** (bonus): câu hỏi behavioral và tình huống, kèm hướng trả lời mong
   đợi, gồm ý phải có, điểm cộng và red flag. Dùng để tập kể, không dùng để học thuộc.

Với vị trí senior, vòng kỹ thuật chỉ chứng minh bạn **đủ** giỏi. Người phỏng vấn còn hỏi:
người này có tự nhận một vấn đề mơ hồ rồi giao được kết quả không, có làm cả team tốt lên
không. Mọi câu trả lời ở đây phải dựa trên **ví dụ thật** của bạn; khung lý thuyết chỉ giúp
kể cho có cấu trúc. Cách kể STAR và kho câu chuyện ở [25-interview-skills.md](25-interview-skills.md).

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| *The Staff Engineer's Path* (Tanya Reilly, O'Reilly 2022) | Sách | Big picture, thực thi dự án, nâng cả team. Đọc được từ senior, không cần đợi lên staff. Tác giả có [trang tổng hợp về staff engineering](https://www.noidea.dog/staff) |
| [*Staff Engineer*](https://staffeng.com/guides/) (Will Larson, staffeng.com) | Sách + guide miễn phí | Các guide ngắn: chọn việc quan trọng, quản lý chất lượng kỹ thuật, làm việc với cấp trên |
| [*An Elegant Puzzle*](https://lethain.com/elegant-puzzle/) (Will Larson, 2019) | Sách | Migration, tech debt, sizing team; góc nhìn của engineering manager giúp hiểu người phỏng vấn |
| [Google Engineering Practices](https://google.github.io/eng-practices/) | Guide miễn phí | Code review từ hai phía: người review và người gửi CL |
| [ADR (adr.github.io)](https://adr.github.io/) | Tổng hợp | Template và công cụ ghi quyết định kiến trúc |
| [*Accelerate*](https://itrevolution.com/product/accelerate/) (Forsgren, Humble, Kim) và [DORA](https://dora.dev/) | Sách + nghiên cứu | Đo năng lực giao hàng bằng số liệu thay vì cảm tính |
| [The Pragmatic Engineer](https://newsletter.pragmaticengineer.com/) (Gergely Orosz) | Newsletter/blog | Cách các công ty thật làm RFC, on-call, leveling, tuyển dụng |
| [Google SRE Book](https://sre.google/sre-book/postmortem-culture/) | Sách online miễn phí | Postmortem, quản lý sự cố |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Ra quyết định và kỹ thuật** | 1.1–1.5 | Giải thích được mọi quyết định kỹ thuật bằng trade-off; có design doc và ADR thật để kể | 1 tuần |
| **2. Giao hàng và rủi ro** | 2.1–2.5 | Kể được cách chia việc, ước lượng, cắt phạm vi, migration và xử lý sự cố bằng ví dụ có số liệu | 1 tuần |
| **3. Con người và ảnh hưởng** 🔴 | 3.1–3.4 | Kể được câu chuyện mentor, góp ý, thuyết phục team khác, phỏng vấn người khác | 1 tuần |

Thứ tự này đi từ phạm vi hẹp tới rộng: một quyết định → một dự án → nhiều người. Mid thường
có đủ chất liệu cho chặng 1; senior bị đánh giá chủ yếu ở chặng 2 và 3. Trong mỗi module, việc
quan trọng nhất là **viết ra câu chuyện của chính mình**, rồi tập kể thành tiếng.

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Ra quyết định và kỹ thuật

#### 1.1 Senior là gì, ownership

**Vì sao cần học:** Vòng behavioral cho vị trí senior gần như luôn có câu kiểu "vì sao bạn nghĩ
mình đã là senior" hoặc "kể về một việc bạn tự nhận trách nhiệm". Người phỏng vấn không chấm số
năm kinh nghiệm mà chấm phạm vi bạn tự gánh. Hiểu khác biệt giữa các level giúp bạn chọn đúng câu
chuyện để kể, và đọc ra công ty đang tuyển kiểu senior nào.

**Học gì**

*Level khác nhau ở phạm vi, không ở tốc độ code*
- *Level* là bậc nghề nghiệp mà công ty dùng để xếp lương và kỳ vọng: junior, mid, senior, staff...
  Mỗi công ty định nghĩa hơi khác, nhưng thường so theo 5 trục:
  - Phạm vi: bạn chịu trách nhiệm một phần nhỏ hay một phần lớn của hệ thống.
  - Độ mơ hồ (*ambiguity*): việc được giao đã rõ tới đâu khi tới tay bạn.
  - Quyết định: bạn được tự quyết những gì.
  - Tầm ảnh hưởng: những ai được lợi từ việc bạn làm.
  - Khi có sự cố: bạn đứng ở vị trí nào.

  | | Junior | Mid | Senior |
  |---|---|---|---|
  | Phạm vi | một task | một tính năng | một hệ thống/một mảng, xuyên nhiều tính năng |
  | Độ mơ hồ | nhận task đã rõ | tự làm rõ chi tiết tính năng | nhận một **vấn đề** và tự biến nó thành kế hoạch |
  | Quyết định | làm theo thiết kế | thiết kế trong phạm vi tính năng | quyết định kiến trúc, chịu trách nhiệm trade-off dài hạn |
  | Tầm ảnh hưởng | bản thân | bản thân và người review | cả team và các team lân cận |
  | Khi có sự cố | báo lên | tự sửa phần mình | dẫn dắt xử lý, đảm bảo không lặp lại |

- Ví dụ cùng một phàn nàn "trang báo cáo của admin rất chậm":
  - Junior nhận task "thêm index cho bảng `reports`" và làm đúng task đó.
  - Mid tự tìm ra query chậm bằng slow query log (log MySQL ghi lại các query chạy lâu), sửa,
    rồi đo lại.
  - Senior hỏi vì sao mọi trang báo cáo đều chậm, thấy tất cả đang tính trực tiếp trên DB chính,
    đề xuất chuyển báo cáo sang replica (bản sao chỉ đọc của DB) hoặc bảng tổng hợp, chia việc cho team, và đặt alert để
    lần sau team biết trước khách hàng.
- ⚠️ Senior không phải "người code nhanh nhất". Senior làm cả team nhanh hơn:
  - gỡ vướng cho người khác,
  - ra quyết định để team không bị treo,
  - giảm rủi ro trước khi nó thành sự cố,
  - nâng người khác lên.

*Ownership*
- *Ownership* (tinh thần làm chủ) nghĩa là coi **kết quả kinh doanh** của tính năng là việc của
  mình, không chỉ phần code được giao.
- Với người có ownership, "xong việc" không phải là lúc merge:
  - Code đã merge nhưng không ai dùng thì việc chưa xong.
  - Tính năng sập sau 1 tuần thì việc chưa xong.
  - Xong là khi người dùng dùng được, có số liệu cho thấy nó chạy đúng, và team vận hành được.
- Ví dụ hành vi ownership:
  - Sau khi release luồng thanh toán mới, tự mở dashboard theo dõi tỉ lệ lỗi hai ngày đầu, dù
    không ai yêu cầu.
  - Thấy cron job của team khác chạy trùng giờ cao điểm làm DB chậm, báo và đề xuất cách sửa
    thay vì im lặng vì "không phải việc của mình".
- ⚠️ Ownership không có nghĩa là tự làm hết. Bạn nhận trách nhiệm cho kết quả, còn việc cụ thể
  vẫn có thể giao cho người khác.

*Các kiểu vai trò khi lên cao hơn*
- Will Larson chia vai trò staff thành 4 *archetype* (kiểu mẫu). Senior chưa cần đóng vai nào,
  nhưng biết để hiểu công ty đang tuyển kiểu người nào.

  | Archetype | Làm gì chủ yếu | Ví dụ |
  |---|---|---|
  | Tech lead | dẫn dắt kỹ thuật của một team: chia việc, gỡ vướng, giữ hướng | lead 5 dev làm hệ thống đơn hàng |
  | Architect | chịu trách nhiệm hướng kỹ thuật của một mảng lớn, xuyên nhiều team | đặt chuẩn API và cách tách service cho cả công ty |
  | Solver | được cử vào giải quyết vấn đề khó, xong việc này chuyển sang việc khác | kéo lại một dự án migration đang trễ |
  | Right hand | làm cánh tay phải của một lãnh đạo, thay họ xử lý việc của tổ chức | giúp CTO điều phối kế hoạch của nhiều team |

- Áp vào việc chuẩn bị: JD nhấn "dẫn dắt team" thì cần câu chuyện kiểu tech lead. JD nhấn "làm
  việc xuyên team", "định hướng kiến trúc" thì cần câu chuyện kiểu architect.

**Đọc**
- Staff Engineer: [Staff archetypes](https://staffeng.com/guides/staff-archetypes/), [Work on what matters](https://staffeng.com/guides/work-on-what-matters/)
- The Staff Engineer's Path: Part I (*The Big Picture*), ch.1 về vai trò

**Nắm chắc khi**
- [ ] Viết xong một đoạn 5 câu mô tả phạm vi hiện tại của bạn theo 5 dòng của bảng trên, kèm ví dụ cho từng dòng
- [ ] Có một câu chuyện "việc tôi làm không nằm trong task được giao nhưng tôi nhận trách nhiệm", kể trong 2 phút

#### 1.2 Khung trade-off và loại quyết định

**Vì sao cần học:** Câu "vì sao chọn X" xuất hiện ở mọi vòng: hỏi đáp kỹ thuật, system design,
behavioral. Trong công việc, đây cũng là cách bạn bảo vệ một đề xuất như "Laravel queue hay
RabbitMQ", "tách service hay giữ monolith". Ở level senior, người phỏng vấn chấm **cách bạn cân
nhắc**, không chấm bạn chọn đáp án nào.

**Học gì**

*Trade-off là gì*
- *Trade-off* là sự đánh đổi: được cái này thì mất cái kia. Gần như không có lựa chọn kỹ thuật
  nào tốt hơn ở mọi mặt.
  - Ví dụ: cache kết quả query bằng Redis thì trang nhanh hơn, nhưng dữ liệu có thể cũ vài giây
    và có thêm một hệ thống phải vận hành.
- Trả lời "vì sao chọn X" mà chỉ kể ưu điểm của X là dấu hiệu chưa thật sự cân nhắc.

*Khung trade-off 4 bước*
1. Nêu **bài toán và ràng buộc** trước. *Ràng buộc* (constraint) là thứ không đổi được hoặc rất
   khó đổi: quy mô, deadline, kỹ năng team, ngân sách, yêu cầu nhất quán dữ liệu, tuân thủ (quy
   định pháp lý, chuẩn bảo mật mà công ty phải theo).
2. Nêu **ít nhất hai lựa chọn**, kể cả "không làm gì" và "làm đơn giản nhất".
3. So sánh theo tiêu chí cụ thể: độ phức tạp, chi phí vận hành, rủi ro, thời gian làm, khả năng
   đảo ngược, ảnh hưởng tới team khác.
4. Nêu **cái giá** của lựa chọn đã chọn và **điều kiện nào thì sẽ đổi**.

- Ví dụ áp khung cho "gửi email xác nhận đơn hàng":
  1. Ràng buộc: khoảng 5.000 đơn/ngày, team 3 người đều biết Laravel, không có ai chuyên vận hành
     hạ tầng, Redis đã có sẵn.
  2. Ba lựa chọn: gửi ngay trong request, Laravel queue chạy trên Redis, dựng RabbitMQ riêng.
  3. So sánh:

     | | Gửi ngay trong request | Laravel queue + Redis | RabbitMQ riêng |
     |---|---|---|---|
     | Độ phức tạp | thấp nhất | thấp, dùng lại Redis có sẵn | cao, thêm một hệ thống mới |
     | Rủi ro | SMTP chậm thì request tạo đơn chậm theo | job có thể mất nếu Redis mất dữ liệu | thấp nếu cấu hình đúng |
     | Chi phí vận hành | không có | gần như không có | cần người biết vận hành RabbitMQ |

  4. Chọn Laravel queue + Redis. Cái giá: phải theo dõi bảng failed jobs. Sẽ đổi khi có nhiều
     service viết bằng ngôn ngữ khác cùng cần đọc message.
- ⚠️ "Công nghệ này đang hot" hay "công ty lớn đều dùng" không phải lý do.

*Quyết định đảo ngược được và khó đảo ngược*

| | Đảo ngược được | Khó đảo ngược |
|---|---|---|
| Ví dụ | thư viện nội bộ, endpoint nội bộ | schema dữ liệu lõi, API công khai, chọn database, tách microservice, định dạng message |
| Nếu chọn sai | sửa lại trong vài ngày | tốn nhiều tháng, ảnh hưởng người dùng và team khác |
| Cách làm | quyết nhanh, thử rồi sửa | chậm lại, viết design doc (1.4), xin review rộng |

- Đặt thời gian suy nghĩ tương xứng với cái giá khi sai.
- Nhiều quyết định nên đưa ra khi mới có khoảng 70% thông tin. Đây là con số Jeff Bezos nêu: đợi
  tới 90% thì trong đa số trường hợp là đã chậm.
- ⚠️ Bẫy ngược lại: bàn hai tuần cho một quyết định đảo ngược được, ví dụ chọn thư viện xử lý
  ngày giờ cho một service nội bộ.

*Disagree and commit*
- *Disagree and commit* nghĩa là: trong lúc bàn thì được phản đối, nhưng khi đã quyết thì cả
  team làm hết sức cho quyết định đó, kể cả người từng phản đối.
- Ví dụ: bạn muốn dùng PostgreSQL, team chốt MySQL. Sau khi chốt, bạn không làm chậm, không nói
  "tôi đã bảo rồi" khi gặp khó, mà giúp thiết kế schema MySQL tốt nhất có thể.
- ⚠️ Commit không có nghĩa là im lặng. Ghi lại rủi ro bạn đã nêu để cả team xem lại sau.

**Đọc**
- Jeff Bezos: [2016 Letter to Shareholders](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders) (mục high-velocity decision making, disagree and commit)
- Staff Engineer: [Learn to never be wrong](https://staffeng.com/guides/learn-to-never-be-wrong/)

**Nắm chắc khi**
- [ ] Chọn một quyết định kỹ thuật thật trong dự án, viết ra đủ 4 phần của khung trade-off trên nửa trang
- [ ] Liệt kê 3 quyết định trong dự án hiện tại, xếp vào "đảo ngược được" hoặc "khó đảo ngược", và nói bạn đã dành bao lâu cho mỗi cái

#### 1.3 Build vs buy, chọn công nghệ mới

**Vì sao cần học:** Trong dự án PHP, câu hỏi build vs buy xuất hiện liên tục: dùng dịch vụ auth
ngoài hay tự làm login, dùng Amazon SES hay tự dựng mail server, thêm service Go hay giữ Laravel.
Quyết định sai ở đây tốn tiền và công sức nhiều năm. Senior hay bị hỏi "vì sao không tự viết" hoặc
"vì sao lại tự viết", và "tiêu chí chọn công nghệ mới của bạn là gì".

**Học gì**

*Build vs buy là gì*
- *Build* là tự xây. *Buy* là mua hoặc dùng thứ có sẵn: SaaS trả phí, dịch vụ cloud, thư viện
  open source.
- Nên mua/dùng dịch vụ khi thứ đó **không phải năng lực cốt lõi**. *Năng lực cốt lõi* (core
  competency) là phần làm nên giá trị riêng của sản phẩm, thứ khách hàng chọn bạn vì nó.
  - Thường nên mua: email, auth, thanh toán, monitoring.
- Nên tự xây khi:
  - Đó là lợi thế cạnh tranh. Ví dụ: một sàn thương mại điện tử tự xây thuật toán gợi ý sản phẩm.
  - Dịch vụ ngoài không đáp ứng ràng buộc: dữ liệu không được đưa ra ngoài, chi phí quá cao ở
    quy mô lớn, hoặc cần tuỳ biến sâu mà dịch vụ không cho.

*Tính đủ chi phí*
- Chi phí thật gồm ba phần: chi phí làm ban đầu, chi phí vận hành dài hạn, và rủi ro.
- ⚠️ Bẫy hay gặp là chỉ tính chi phí làm ban đầu.
  - Ví dụ: "tự viết hệ thống gửi SMS chỉ mất 2 tuần". Sau đó mỗi tháng tốn vài ngày xử lý nhà
    mạng đổi API, retry, báo cáo gửi lỗi.
- *Vendor lock-in* là bị trói vào một nhà cung cấp: muốn rời đi thì rất tốn, vì code, dữ liệu và
  quy trình đã gắn chặt với họ.
  - Ví dụ: dùng sâu tính năng riêng của một dịch vụ queue trên AWS, muốn chuyển sang cloud khác
    thì phải viết lại toàn bộ phần đó.
  - ⚠️ Lock-in là một chi phí cần đưa vào bảng so sánh, không phải lý do tự động để tự xây.

*Trước khi đưa công nghệ mới vào*
- Trả lời được 4 câu:
  1. Nó giải quyết vấn đề gì mà cái đang có không làm được?
  2. Ai vận hành nó lúc 2 giờ sáng khi nó hỏng?
  3. Team có ai biết nó không?
  4. Cộng đồng và tài liệu của nó thế nào?
- ⚠️ Mỗi công nghệ mới là một thứ phải vận hành, giám sát, nâng cấp và dạy cho người mới.
- *Choose boring technology* là lời khuyên của Dan McKinley: ưu tiên công nghệ "nhàm chán", tức
  đã cũ, ổn định, lỗi và giới hạn đã được biết hết.
  - Ông ví mỗi công ty chỉ có vài "token đổi mới" (innovation token). Hãy tiêu chúng vào chỗ tạo
    ra giá trị riêng, không tiêu vào hạ tầng.
  - Với phần lớn bài toán, đây là quyết định đúng.

*Góc PHP*
- Câu "vì sao vẫn dùng PHP/Laravel" hoặc "có nên thêm Go/Node cho service X" là câu hỏi build vs
  buy ở dạng khác. Trả lời bằng khung trade-off ở 1.2.
- Ví dụ: cần service realtime giữ hàng chục nghìn kết nối websocket.
  - Lựa chọn: Laravel Reverb (websocket server của Laravel), dịch vụ ngoài như Pusher, hoặc một
    service Go riêng.
  - Tiêu chí: chi phí dịch vụ theo số kết nối, team có ai biết Go để vận hành không, tải thực
    tế là bao nhiêu.
  - Đáp án "viết bằng Go vì Go nhanh" mà không nêu ai vận hành là câu trả lời yếu.

**Đọc**
- Dan McKinley: [Choose Boring Technology](https://mcfunley.com/choose-boring-technology) (bài gốc, có bản slide ở [boringtechnology.club](https://boringtechnology.club/))
- The Staff Engineer's Path: ch.2–3 (hiểu bối cảnh và chiến lược kỹ thuật)

**Nắm chắc khi**
- [ ] Viết xong câu chuyện một lần bạn chọn dùng dịch vụ ngoài hoặc tự xây, có con số chi phí hoặc thời gian
- [ ] Trả lời được trong 2 phút "vì sao team bạn chọn stack hiện tại", nêu cả cái giá

#### 1.4 Design doc/RFC và ADR

**Vì sao cần học:** Ở công ty có quy trình tốt, thay đổi lớn phải qua design doc trước khi code.
Người phỏng vấn senior hay hỏi "team bạn ra quyết định kiến trúc thế nào" hoặc "kể một lần tài
liệu thiết kế giúp phát hiện vấn đề sớm". Có design doc và ADR thật để kể là bằng chứng mạnh nhất
cho kỹ năng ra quyết định.

**Học gì**

*Design doc và RFC là gì*
- *Design doc* là tài liệu mô tả cách định làm một thay đổi lớn, viết **trước khi code**, để
  người khác đọc và phản biện.
- *RFC* (Request for Comments) là tên gọi khác ở nhiều công ty. Tên này nhấn mạnh mục đích xin
  góp ý.
- Viết doc để **thu thập phản biện sớm**, khi sửa thiết kế còn rẻ: sửa một đoạn văn thay vì sửa
  một tháng code.
- ⚠️ Doc viết ra để hợp thức hoá quyết định đã có thì người đọc nhận ra ngay, và không ai buồn
  góp ý thật.

*Cấu trúc design doc*
1. Bối cảnh và vấn đề.
2. Mục tiêu và **không phải mục tiêu**. *Non-goals* là những thứ cố ý không làm, viết ra để khỏi
   tranh cãi phạm vi về sau.
   - Ví dụ: "Không hỗ trợ đa tiền tệ trong phiên bản này".
3. Phương án đề xuất.
4. Phương án đã cân nhắc và vì sao loại.
5. Rủi ro và cách giảm.
6. Kế hoạch triển khai và *rollback*, tức cách quay lại trạng thái cũ nếu triển khai gặp sự cố.
7. Câu hỏi còn mở.
- Mục 4 là mục người đọc có kinh nghiệm xem kỹ nhất. Không có phương án nào bị loại nghĩa là
  chưa thật sự cân nhắc.

*Khi nào cần viết*
- ⚠️ Không phải việc gì cũng cần design doc. Việc nhỏ và đảo ngược được thì một đoạn mô tả trong
  ticket là đủ.
- Nên viết khi có một trong các dấu hiệu:
  - quyết định khó đảo ngược (module 1.2),
  - ảnh hưởng tới nhiều team,
  - công việc kéo dài hơn vài tuần.
- Ví dụ:
  - "Thêm cột `note` vào bảng `orders`": không cần doc.
  - "Tách phần thanh toán ra khỏi monolith Laravel": cần doc.

*ADR*
- *ADR* (Architecture Decision Record) là bản ghi ngắn cho **một** quyết định kiến trúc. Mỗi ADR
  gồm: quyết định, bối cảnh, hệ quả, trạng thái (đề xuất, đã chấp nhận, bị thay thế).
- Lưu ADR cạnh code, ví dụ `docs/adr/0003-dung-redis-cho-queue.md`, để người đến sau hiểu vì sao
  hệ thống như hiện nay.
- Khác với design doc:

  | | Design doc | ADR |
  |---|---|---|
  | Độ dài | vài trang | nửa trang tới một trang |
  | Viết lúc nào | trước khi làm, để xin góp ý | khi đã quyết, để ghi lại |
  | Sau khi làm xong | thường không được cập nhật nữa | sống cùng repo. Khi đổi quyết định thì viết ADR mới thay thế ADR cũ |

- Xem thêm ADR trong bối cảnh kiến trúc ở [15-architecture.md](15-architecture.md).

**Đọc**
- Malte Ubl: [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- Pragmatic Engineer: [Companies Using RFCs or Design Docs and Examples of These](https://blog.pragmaticengineer.com/rfcs-and-design-docs/)
- Michael Nygard: [Documenting Architecture Decisions](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) (bài gốc của ADR); [adr.github.io](https://adr.github.io/) và [template của Joel Parker Henderson](https://github.com/joelparkerhenderson/architecture-decision-record)

**Nắm chắc khi**
- [ ] Viết xong một design doc tối đa 2 trang cho một tính năng đã làm, có mục phương án đã loại (bài tập 1)
- [ ] Viết xong 2 ADR cho hai quyết định có thật (bài tập 2)
- [ ] Kể được trong 2 phút một lần design doc giúp phát hiện vấn đề trước khi code

#### 1.5 Chất lượng dài hạn: tech debt, code review, chuẩn hoá, chi phí

**Vì sao cần học:** Câu "bạn xử lý tech debt thế nào khi vẫn phải làm tính năng" gần như chắc
chắn được hỏi ở vòng mid và senior. Trong công việc, senior là người quyết khi nào trả nợ kỹ
thuật, giữ chất lượng code review cho cả team, và ở mức 🔴 thì biết hệ thống đang tốn bao nhiêu
tiền mỗi tháng.

**Học gì**

*Tech debt là gì*
- *Tech debt* (nợ kỹ thuật) là những chỗ code hoặc thiết kế làm tạm, khiến mọi thay đổi về sau
  chậm hơn và rủi ro hơn. Giống vay tiền: được nhanh bây giờ, rồi trả lãi dần về sau.
  - Ví dụ: logic tính giá bị copy vào 4 controller. Mỗi lần đổi chính sách giá phải sửa 4 chỗ,
    và rất dễ sót một chỗ.
- Martin Fowler phân loại theo hai trục, ra 4 ô:

  | | Thận trọng (prudent) | Liều lĩnh (reckless) |
  |---|---|---|
  | Cố ý (deliberate) | "Phải ra mắt trước Tết, ghi lại và sửa sau" | "Không có thời gian viết test đâu" |
  | Vô tình (inadvertent) | "Giờ mới hiểu ra đáng lẽ phải thiết kế thế nào" | không biết mình đang tạo nợ |

- Cộng thêm loại debt do hệ thống thay đổi theo thời gian: code từng đúng, nhưng bối cảnh đã khác.
  - Ví dụ: thiết kế cho 1.000 user, nay có 1 triệu user.

*Ưu tiên và thuyết phục*
- Ưu tiên theo **lãi suất**, tức mỗi lần phải đụng vào khoản debt đó thì tốn thêm bao nhiêu.
  - Debt ở chỗ hay phải sửa, hay gây sự cố thì trả trước.
  - Module không ai đụng tới thì để đó, dù code xấu.
- Thuyết phục bằng số liệu, không bằng cảm giác "code này xấu":
  - thời gian làm tính năng ở module đó,
  - số sự cố,
  - thời gian onboard người mới.
  - Ví dụ: "3 tính năng gần nhất đụng vào module giá mất trung bình 5 ngày thay vì 2, và gây 2
    sự cố tính sai tiền".
- Ba cách trả:
  - Gắn vào tính năng đang làm: để lại code sạch hơn lúc nhận.
  - Dành một tỷ lệ cố định mỗi sprint.
  - Mở dự án riêng.
- Migration (module 2.4) là cách trả debt ở quy mô lớn.

*Code review*
- Code review có ba mục đích: tìm lỗi, chia sẻ kiến thức, giữ nhất quán trong codebase.
- Góp ý phân mức, luôn kèm lý do:
  - chặn merge: phải sửa mới được merge,
  - nên sửa,
  - tuỳ chọn: người viết tự quyết. Google đánh dấu loại này bằng tiền tố "Nit:".
- Để máy làm phần máy làm được, người review tập trung vào logic:
  - Format code: PHP-CS-Fixer hoặc Laravel Pint.
  - *Lint*: kiểm tra code theo các luật đơn giản, ví dụ biến khai báo mà không dùng.
  - *Static analysis* (phân tích tĩnh): đọc code mà không chạy để bắt lỗi kiểu dữ liệu, gọi
    method không tồn tại. Với PHP là PHPStan, hoặc Larastan cho Laravel.
- PR nhỏ thì được review kỹ. Senior làm gương bằng chính PR của mình.
  - ⚠️ PR 2.000 dòng thường chỉ nhận được "LGTM" (looks good to me) mà không ai đọc kỹ.

*Đào sâu (🔴)*
- Chuẩn hoá cho cả team: guideline, template, tooling, CI check.
  - *CI check* là bước kiểm tra chạy tự động mỗi khi mở PR (test, PHPStan, format). PR không đạt
    thì không merge được.
  - Ưu tiên thứ máy kiểm tra được hơn tài liệu. Một dòng trong wiki "nhớ khai báo
    `strict_types`" sẽ bị quên, còn CI check thì không.
- Chi phí hạ tầng:
  - Biết đại khái hệ thống tốn bao nhiêu mỗi tháng và phần nào tốn nhất.
  - Các khoản hay phình:
    - Log và metric *cardinality*: số tổ hợp giá trị nhãn khác nhau của metric. Gắn `user_id`
      làm nhãn là tạo ra hàng triệu chuỗi số liệu, và nhiều dịch vụ monitoring tính tiền theo
      số chuỗi.
    - Dữ liệu không bao giờ xoá: log, file upload, bảng lịch sử.
    - Instance quá cỡ: thuê máy to hơn nhiều so với tải thực tế.
    - *Egress*: phí cho dữ liệu đi ra khỏi cloud, ví dụ người dùng tải file từ S3 về.

**Đọc**
- Martin Fowler: [Technical Debt Quadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html), [Is High Quality Software Worth the Cost?](https://martinfowler.com/articles/is-quality-worth-cost.html)
- Staff Engineer: [Manage technical quality](https://staffeng.com/guides/manage-technical-quality/)
- Will Larson: [Migrations: the sole scalable fix to tech debt](https://lethain.com/migrations/)
- Google eng-practices: [The Standard of Code Review](https://google.github.io/eng-practices/review/reviewer/standard.html), [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html), [Small CLs](https://google.github.io/eng-practices/review/developer/small-cls.html)
- Chất lượng code và test: [20-testing-quality.md](20-testing-quality.md)

**Nắm chắc khi**
- [ ] Lập xong danh sách 5 khoản tech debt của dự án, xếp theo lãi suất, có đoạn thuyết phục bằng hệ quả kinh doanh (bài tập 4)
- [ ] Kể được trong 2 phút một lần bạn đưa một chuẩn/tool vào team và số liệu trước/sau
- [ ] Nói được con số chi phí hạ tầng hằng tháng (ước lượng) của hệ thống đang làm và phần tốn nhất

---

### Chặng 2: Giao hàng và rủi ro

#### 2.1 Chia việc và ước lượng

**Vì sao cần học:** "Bạn ước lượng thế nào, sai thì làm gì" là câu hỏi chuẩn cho mid và senior.
Trong công việc, ước lượng sai rồi báo muộn là lý do phổ biến nhất khiến product mất niềm tin vào
team kỹ thuật. Cách chia việc tốt còn giúp release sớm, phát hiện vấn đề sớm, và luôn có thứ để
giao khi hết thời gian.

**Học gì**

*Chia việc theo lát dọc*
- *Vertical slice* (lát dọc) là cách chia mà mỗi phần giao được là một luồng hoàn chỉnh từ đầu
  đến cuối: DB, API, UI. Cách ngược lại là làm xong cả tầng DB rồi mới làm API rồi mới làm UI.
- Ví dụ tính năng "mã giảm giá":
  - Chia theo tầng (không nên): tuần 1 viết migration cho mọi bảng, tuần 2 viết mọi API, tuần 3
    làm UI. Tới tuần 3 mới biết thiết kế có dùng được không.
  - Chia theo lát dọc:
    1. Lát 1: mã giảm số tiền cố định, áp được khi checkout, chạy từ đầu tới cuối.
    2. Lát 2: thêm mã giảm theo phần trăm.
    3. Lát 3: thêm giới hạn số lần dùng mỗi khách.
- Vì sao tốt hơn: mỗi lát demo và release được, lỗi thiết kế lộ ra từ tuần 1, và nếu hết thời
  gian thì vẫn có thứ giao.

*MVP và làm phần rủi ro trước*
- *MVP* (Minimum Viable Product) là phiên bản nhỏ nhất kiểm chứng được giả định quan trọng nhất.
  - Ví dụ: giả định "khách sẽ dùng mã giảm giá khi checkout". MVP chỉ cần lát 1 ở trên.
- Làm phần rủi ro nhất trước: tích hợp bên thứ ba, phần chưa ai trong team từng làm.
  - Ví dụ: tích hợp một cổng thanh toán mới thì gọi thử API sandbox ngay ngày đầu, trước khi làm
    UI. Nếu API có vấn đề, bạn biết khi còn 3 tuần chứ không phải khi còn 3 ngày.
- *Feature flag* là công tắc bật/tắt một tính năng bằng cấu hình, không cần deploy lại. Dùng để:
  - merge sớm vào nhánh chính khi tính năng chưa xong, lúc đó flag đang tắt,
  - bật dần cho 1%, 10%, rồi 100% người dùng,
  - tắt nhanh khi có lỗi.
  - Laravel có sẵn package Laravel Pennant cho việc này.

*Ước lượng*
1. Chia nhỏ tới mức mỗi phần dưới 1–2 ngày. Phần nào lớn hơn nghĩa là chưa hiểu đủ để ước lượng.
2. Cộng các việc hay bị quên: review, test, migration dữ liệu, tài liệu, deploy, theo dõi sau
   release.
3. Ước lượng theo **khoảng** kèm độ tự tin: "3–5 ngày, phần chưa chắc là API đối tác". Một con số
   duy nhất che mất rủi ro.
4. Cập nhật ngay khi biết thêm. Báo trễ sớm tốt hơn nhiều so với báo muộn.
- Vì sao phải là khoảng: ở đầu dự án, sai số ước lượng rất lớn và chỉ thu hẹp dần khi biết thêm.
  Steve McConnell gọi hình dạng này là *cone of uncertainty* (hình nón bất định).
- ⚠️ Không cam kết ước lượng dưới áp lực trong cuộc họp. Hẹn trả lời sau khi chia việc, ví dụ:
  "Cho em tới chiều mai để chia việc rồi báo con số".
- ⚠️ "Cộng thêm 30% cho chắc" mà không nói được rủi ro nằm ở đâu thì không phải là ước lượng.

**Đọc**
- Martin Fowler / Pete Hodgson: [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html)
- The Staff Engineer's Path: Part II (*Execution*), ch.5 (*Leading Big Projects*)
- *Software Estimation: Demystifying the Black Art* (Steve McConnell): phần về cone of uncertainty, nếu muốn đọc sâu

**Nắm chắc khi**
- [ ] Chia xong một tính năng sắp làm thành các phần dưới 1 ngày, ước lượng theo khoảng, sau khi làm so với thực tế (bài tập 3)
- [ ] Có một câu chuyện ước lượng sai: sai bao nhiêu, phát hiện lúc nào, báo ai, sửa quy trình thế nào; kể trong 2 phút

#### 2.2 Rủi ro, dependency, cắt phạm vi, cập nhật tiến độ

**Vì sao cần học:** Deadline cố định mà không kịp làm hết là tình huống thật gần như tháng nào
cũng gặp, và "deadline cố định, không kịp, bạn làm gì" là câu behavioral kinh điển. Người phỏng
vấn muốn thấy ba thứ: bạn báo sớm, bạn đưa lựa chọn chứ không chỉ từ chối, và bạn không lặng lẽ
cắt chất lượng.

**Học gì**

*Rủi ro*
- *Rủi ro* là điều có thể xảy ra và làm dự án trễ hoặc hỏng. Ghi mỗi rủi ro kèm ba thứ:
  - xác suất xảy ra,
  - ảnh hưởng nếu xảy ra,
  - cách giảm.
- Ví dụ: "API của đối tác vận chuyển chưa có tài liệu. Xác suất trễ: cao. Ảnh hưởng: không giao
  được luồng giao hàng. Cách giảm: gọi thử sandbox trong tuần này, làm mock để frontend không bị
  chặn."

*Dependency*
- *Dependency* là việc bạn phải chờ người khác hoặc team khác làm xong thì mới làm tiếp được.
- Với mỗi dependency:
  - xác nhận sớm,
  - có một người đầu mối cụ thể,
  - có kế hoạch dự phòng nếu họ trễ.
- ⚠️ "Team A nói sẽ làm" chưa phải là xác nhận. Xác nhận là có ngày cụ thể và người cụ thể.

*Cắt phạm vi khi deadline cố định*
- Deadline cố định thì thứ điều chỉnh được là **phạm vi**.
- Đưa lựa chọn thay vì từ chối: "Đúng hạn thì được A và B. Muốn có C thì thêm 1 tuần, hoặc bỏ B."
- Phân vai rõ: product chọn phạm vi, kỹ thuật chịu trách nhiệm ước lượng và rủi ro.
- ⚠️ Không lặng lẽ cắt chất lượng, ví dụ bỏ test hay bỏ xử lý lỗi.
  - Nếu buộc phải đánh đổi thì nói ra, và ghi thành tech debt có kế hoạch trả (module 1.5).
  - Vì sao: phần chất lượng bị cắt ngầm sẽ lộ ra thành sự cố, và lúc đó không ai biết đó là đánh
    đổi đã chấp nhận.

*Cập nhật tiến độ*
- Ngắn, đều đặn, theo ba mục cố định: đã xong, đang làm, rủi ro hoặc cần hỗ trợ.
- Ví dụ một bản cập nhật hằng tuần:

  ```text
  Tuần 12, dự án mã giảm giá
  - Đã xong: lát 1 (giảm số tiền cố định) đã lên production, chưa có lỗi.
  - Đang làm: lát 2 (giảm theo %), dự kiến xong thứ Năm.
  - Rủi ro: team CRM chưa xác nhận API lấy hạng thành viên. Nếu thứ Tư chưa có,
    đề xuất bỏ điều kiện theo hạng thành viên khỏi đợt này.
  ```

- Tin xấu báo sớm, và luôn kèm phương án.

*Nhận ra dự án đi chệch*
- Các tín hiệu:
  - mốc trễ liên tiếp,
  - phạm vi phình dần, tức yêu cầu cứ thêm mà deadline không đổi,
  - dependency chưa ai xác nhận,
  - không ai trả lời được "khi nào xong".
- Thấy tín hiệu thì nói ra sớm, rồi đề xuất cắt phạm vi hoặc đổi kế hoạch.

**Đọc**
- The Staff Engineer's Path: ch.6 (*Why Have We Stopped?*): các lý do dự án bị kẹt và cách gỡ
- Staff Engineer: [Staying aligned with authority](https://staffeng.com/guides/staying-aligned-with-authority/), [Present to executives](https://staffeng.com/guides/present-to-executives/)

**Nắm chắc khi**
- [ ] Viết xong câu chuyện STAR "deadline cố định, tôi cắt phạm vi", có con số phạm vi ban đầu và phạm vi đã giao
- [ ] Viết mẫu một bản cập nhật tiến độ 5 dòng cho dự án đang làm, có mục rủi ro

#### 2.3 Làm việc với product và business

**Vì sao cần học:** Phần lớn việc của backend bắt đầu từ một yêu cầu của product, và yêu cầu
thường mơ hồ. Câu "kể về một lần làm việc với yêu cầu không rõ ràng" có mặt ở hầu hết vòng
behavioral. Senior còn phải giải thích việc kỹ thuật (refactor, nâng cấp) cho người không làm kỹ
thuật để xin được thời gian làm.

**Học gì**

*Hỏi vấn đề trước giải pháp*
- Hỏi "vấn đề người dùng là gì" trước khi hỏi "cần làm tính năng gì". Nhiều khi có cách đơn giản
  hơn nhiều so với yêu cầu ban đầu.
- Ví dụ: product yêu cầu "xuất Excel toàn bộ đơn hàng". Hỏi ra thì kế toán chỉ cần tổng doanh thu
  theo ngày để đối soát. Một trang báo cáo tổng hợp làm nhanh hơn và chạy nhẹ hơn nhiều so với
  export 2 triệu dòng.

*Làm rõ yêu cầu mơ hồ*
1. Viết lại yêu cầu bằng lời của mình.
2. Liệt kê các *trường hợp biên* (edge case), tức tình huống ít gặp nhưng có thật: hết hàng,
   thanh toán lỗi, huỷ giữa chừng.
3. Gửi lại cho người yêu cầu xác nhận.
- Ví dụ với yêu cầu "cho khách đổi địa chỉ giao hàng":
  - Đổi được tới lúc nào?
  - Đơn đã giao cho đơn vị vận chuyển thì sao?
  - Phí ship có tính lại không, và nếu phí tăng thì ai trả?

*Yêu cầu phi chức năng*
- *Yêu cầu chức năng* nói hệ thống làm gì. *Yêu cầu phi chức năng* nói hệ thống làm tốt tới đâu
  và trong điều kiện nào.
- Những thứ product thường quên, kỹ thuật nên tự nêu ra:
  - hiệu năng,
  - bảo mật,
  - dữ liệu cũ,
  - phân quyền,
  - *khả năng quan sát* (observability): có log và metric để biết tính năng chạy đúng hay không.
- Ví dụ về dữ liệu cũ: tính năng mới thêm cột `status` cho bảng khách hàng. Ba năm dữ liệu cũ
  thì `status` là gì? Ai quyết, và backfill thế nào?

*Nói bằng hệ quả kinh doanh*
- Người không làm kỹ thuật quyết định dựa trên tiền, thời gian, và rủi ro với khách hàng. Họ
  không đánh giá được "cache layer" hay "refactor".
- So sánh:
  - Kém: "Cần refactor cache layer."
  - Tốt: "Không làm X thì mỗi đợt khuyến mãi có rủi ro sập 30 phút."

**Đọc**
- Staff Engineer: [Getting in the room](https://staffeng.com/guides/getting-in-the-room/)
- *An Elegant Puzzle*: chương *Tools* (phần planning và metrics)

**Nắm chắc khi**
- [ ] Có một câu chuyện "yêu cầu mơ hồ → tôi làm rõ thế nào → kết quả", kể trong 2 phút
- [ ] Viết lại xong một vấn đề kỹ thuật của dự án thành 3 câu cho người không làm kỹ thuật, có con số hệ quả

#### 2.4 Legacy và migration lớn

**Vì sao cần học:** Dự án PHP lâu năm nào cũng có legacy: code không test, framework cũ, chạy
PHP 5 hoặc 7. Senior được kỳ vọng thay đổi những hệ thống này an toàn, không làm gián đoạn kinh
doanh. "Kể về một migration lớn" là câu hỏi senior phổ biến, và câu tình huống "chuyển bảng 500
triệu dòng không downtime" hay xuất hiện.

**Học gì**

*Làm việc với legacy code*
- *Legacy code* là code đang chạy production nhưng khó thay đổi: không test, không tài liệu,
  người viết đã nghỉ.
- Quy trình:
  1. **Hiểu trước khi sửa**: đọc code, đọc log, dùng `git log -p` (lịch sử thay đổi kèm diff) và
     `git blame` (dòng này ai sửa, lúc nào, trong commit nào).
  2. Viết *characterization test*: test ghi lại hành vi **hiện tại** của code, kể cả hành vi
     trông có vẻ sai. Mục đích không phải kiểm tra đúng sai, mà để biết ngay khi thay đổi của bạn
     làm hành vi khác đi.
  3. Thay đổi từng bước nhỏ, mỗi bước deploy được.
- Ví dụ characterization test:

  ```php
  // Chưa biết hàm này "đúng" phải trả gì, chỉ ghi lại nó đang trả gì
  public function test_phi_ship_hien_tai(): void
  {
      $this->assertSame(30000, calcShipping(weight: 1.5, province: 'HN'));
      $this->assertSame(0, calcShipping(weight: 0.0, province: 'HN')); // có thể là bug, nhưng production đang chạy vậy
  }
  ```

- ⚠️ "Viết lại từ đầu" hiếm khi đúng:
  - Mất các xử lý biên đã tích luỹ nhiều năm, mà không ai còn nhớ vì sao có chúng.
  - Hai hệ thống phải chạy song song rất lâu.
  - Joel Spolsky coi đây là sai lầm chiến lược tệ nhất mà một công ty phần mềm có thể mắc.

*Góc PHP: nâng cấp nhiều major version*
- Nâng PHP/Laravel qua nhiều *major version* (phiên bản lớn, có thay đổi không tương thích, ví
  dụ PHP 7.4 lên 8.3) là câu chuyện migration mà senior PHP hay kể.
- Công cụ:
  - Test: lưới an toàn để biết bản nâng cấp không làm hỏng hành vi.
  - PHPStan: bắt lỗi kiểu dữ liệu và method bị bỏ trước khi chạy.
  - *Rector*: công cụ tự động sửa code theo bộ luật, ví dụ đổi cú pháp cũ sang cú pháp PHP 8.

*Strangler fig (🔴)*
- *Strangler fig* là cách thay hệ thống cũ bằng hệ thống mới từng phần. Tên lấy từ loài cây sung
  mọc bám quanh cây chủ rồi thay thế dần cây chủ.
- Các bước:
  1. Đặt một lớp định tuyến phía trước hệ thống cũ, ví dụ Nginx.
  2. Làm lại một chức năng ở hệ thống mới, rồi cho lớp định tuyến gửi request của chức năng đó
     sang hệ thống mới.
  3. Lặp lại tới khi hệ thống cũ không còn nhận request nào, rồi tắt nó.
- Ví dụ: app PHP thuần cũ. Nginx chuyển `/api/orders/*` sang app Laravel mới, mọi đường dẫn khác
  vẫn về app cũ.

*Đổi nơi lưu dữ liệu (🔴)*
- Các thuật ngữ cần biết:
  - *Dual write*: ứng dụng ghi vào cả nơi cũ và nơi mới.
  - *CDC* (Change Data Capture): đọc log thay đổi của DB cũ (với MySQL là binlog) rồi đẩy thay
    đổi sang nơi mới, ứng dụng không phải ghi hai lần.
  - *Backfill*: chép dữ liệu lịch sử có từ trước sang nơi mới.
  - *Shadow read*: đọc từ cả hai nơi, trả kết quả nơi cũ cho người dùng, còn kết quả nơi mới chỉ
    dùng để so sánh.
- Các bước điển hình:
  1. Ghi song song (dual write) hoặc đồng bộ qua CDC.
  2. Backfill dữ liệu lịch sử.
  3. Shadow read, so sánh kết quả, log chênh lệch.
  4. Chuyển dần lượng đọc sang nơi mới theo tỷ lệ.
  5. Chuyển nguồn ghi chính sang nơi mới.
  6. Giữ đường rollback một thời gian rồi mới tắt hệ thống cũ.
- Mỗi bước có **tiêu chí đi tiếp** và **cách quay lại**.
  - Ví dụ tiêu chí sau bước 3: "chênh lệch shadow read dưới 0,01% trong 7 ngày liên tục".
- ⚠️ Dual write bị lệch khi một bên ghi lỗi: ghi DB cũ thành công, ghi DB mới timeout, hai bên
  khác nhau mà không ai biết. Xem outbox và CDC ở [12-messaging.md](12-messaging.md), thay đổi
  schema online ở [03-database-sql.md](03-database-sql.md).

**Đọc**
- Martin Fowler: [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html), [Patterns of Legacy Displacement](https://martinfowler.com/articles/patterns-legacy-displacement/)
- Stripe: [Online migrations at scale](https://stripe.com/blog/online-migrations) (4 bước dual write → đổi đọc → đổi ghi → dọn)
- Joel Spolsky: [Things You Should Never Do, Part I](https://www.joelonsoftware.com/2000/04/06/things-you-should-never-do-part-i/) (viết lại từ đầu)
- *Working Effectively with Legacy Code* (Michael Feathers): phần characterization test và seam

**Nắm chắc khi**
- [ ] Viết xong kế hoạch migration 6 bước cho một bảng hoặc service có thật trong dự án, mỗi bước có tiêu chí đi tiếp và rollback
- [ ] Có một câu chuyện làm việc với legacy code không test, kể trong 2 phút, nói rõ đã giảm rủi ro thế nào

#### 2.5 Vận hành, sự cố, đo năng lực giao hàng

**Vì sao cần học:** "Kể về một sự cố production bạn từng xử lý" có ở hầu hết vòng behavioral.
Senior được kỳ vọng không chỉ sửa bug mà còn dẫn dắt xử lý sự cố và làm cho nó không lặp lại.
DORA metrics là cách nói về năng lực giao hàng của team bằng số liệu, hay được hỏi ở công ty có
văn hoá DevOps.

**Học gì**

*You build it, you run it*
- Nghĩa là team viết service nào thì vận hành service đó, không ném sang một team vận hành riêng.
- Cụ thể, với mỗi service mình sở hữu cần có:
  - *SLO* (Service Level Objective): mục tiêu chất lượng đo được. Ví dụ: "99,9% request API
    checkout thành công trong mỗi 30 ngày".
  - Dashboard để nhìn tình trạng service.
  - Alert kèm *runbook*: tài liệu từng bước ghi "alert này kêu thì kiểm tra gì, làm gì".
- Chi tiết SLO, alert, on-call: [18-reliability-observability.md](18-reliability-observability.md).

*Postmortem blameless*
- *Postmortem* là tài liệu viết sau sự cố để hiểu chuyện gì đã xảy ra và phòng ngừa lần sau.
- *Blameless* nghĩa là không đổ lỗi cho cá nhân, mà tìm xem hệ thống nào đã cho phép lỗi xảy ra.
  - Vì sao: người sợ bị phạt sẽ giấu thông tin, và lần sau sự cố lặp lại.
- Một postmortem gồm:
  - timeline: chuyện gì xảy ra lúc mấy giờ,
  - ảnh hưởng: bao nhiêu phút, bao nhiêu người dùng,
  - *root cause* (nguyên nhân gốc) ở tầng hệ thống,
  - *action item* (việc cần làm để phòng ngừa), mỗi việc có người nhận và hạn chót, và được theo
    dõi đến khi xong.
- Ví dụ phân biệt nguyên nhân bề mặt và root cause ở tầng hệ thống:
  - Bề mặt: "Dev A chạy migration xoá cột trên production."
  - Tầng hệ thống: "Migration không bắt buộc qua review. CI không chặn lệnh xoá cột. Backup chưa
    bao giờ được thử restore."
- ⚠️ Action item không ai theo dõi thì postmortem vô ích.

*DORA metrics*
- *DORA* (DevOps Research and Assessment) là chương trình nghiên cứu về năng lực giao hàng phần
  mềm, đứng sau sách *Accelerate*. Họ dùng 5 chỉ số:

  | Chỉ số | Đo gì |
  |---|---|
  | Change lead time | từ lúc commit tới lúc thay đổi chạy trên production mất bao lâu |
  | Deployment frequency | bao lâu thì deploy một lần |
  | Change fail rate | tỉ lệ deploy gây lỗi phải xử lý ngay (rollback, hotfix) |
  | Failed deployment recovery time | khi deploy gây lỗi, mất bao lâu để phục hồi |
  | Deployment rework rate | tỉ lệ deploy ngoài kế hoạch, phải làm để sửa sự cố trên production |

- Nghiên cứu của DORA cho thấy tốc độ và ổn định thường đi cùng nhau: team deploy thường xuyên
  với thay đổi nhỏ cũng thường ít lỗi hơn.
- ⚠️ Metric dùng để cải thiện hệ thống, không dùng để xếp hạng cá nhân. Ép theo con số thì người
  ta tối ưu con số.
  - Ví dụ: đặt chỉ tiêu deployment frequency thì team chia nhỏ deploy một cách vô nghĩa cho đủ số.

*Incident commander (🔴)*
- *Incident commander* (IC) là người điều phối khi có sự cố. IC **điều phối**, không tự tay sửa.
- Việc của IC:
  1. Phân vai: ai điều tra, ai giao tiếp (cập nhật cho support, product, khách hàng).
  2. Cập nhật định kỳ, kể cả khi chưa có gì mới.
  3. Quyết định rollback hoặc biện pháp giảm thiệt hại.
- Nguyên tắc: **giảm thiệt hại trước, tìm root cause sau**.
  - Ví dụ: deploy lúc 14:00, tỉ lệ lỗi checkout tăng từ 14:05. Rollback ngay, chưa cần hiểu vì sao.
- ⚠️ Bẫy hay gặp: người giỏi nhất nhảy vào debug, không ai điều phối. Kết quả là không ai báo
  khách hàng, không ai quyết rollback.

**Đọc**
- Google SRE Book: [Managing Incidents](https://sre.google/sre-book/managing-incidents/), [Postmortem Culture](https://sre.google/sre-book/postmortem-culture/); SRE Workbook: [Incident Response](https://sre.google/workbook/incident-response/)
- DORA: [DORA's software delivery metrics](https://dora.dev/guides/dora-metrics/), [Capabilities](https://dora.dev/capabilities/)
- *Accelerate*: Part I (các capability ảnh hưởng tới năng lực giao hàng)

**Nắm chắc khi**
- [ ] Viết xong câu chuyện sự cố theo 5 bước (xảy ra gì, phát hiện, root cause, khắc phục, phòng ngừa), có số phút ảnh hưởng và số user bị ảnh hưởng
- [ ] Viết xong một postmortem mẫu 1 trang cho sự cố đó
- [ ] Nói được ước lượng deployment frequency và change fail rate của team hiện tại

---

### Chặng 3: Con người và ảnh hưởng 🔴

#### 3.1 Mentor, onboarding, giao việc

**Vì sao cần học:** Ở level senior, câu "bạn đã giúp ai tiến bộ" dùng để xem bạn nhân được năng
lực của cả team hay chỉ làm tốt phần mình. Trong công việc, senior ôm hết việc khó sẽ thành nút
thắt, và khi senior nghỉ phép thì team đứng lại.

**Học gì**

*Onboarding*
- *Onboarding* là quá trình đưa người mới tới mức làm được việc.
- Ba thứ cần có:
  - Tài liệu khởi động: cách chạy dự án ở máy local, kiến trúc tổng quan, hỏi ai về việc gì.
  - Người đồng hành (*buddy*): người để hỏi những câu ngại hỏi lead.
  - Task đầu tiên nhỏ và deploy được trong tuần đầu.
- Vì sao task đầu phải deploy được: người mới đi qua cả quy trình (code, review, CI, deploy), lộ
  ra chỗ vướng sớm, và có cảm giác đóng góp thật.
- ⚠️ Người mới mất 3 ngày chỉ để chạy được dự án ở local thì đó là tech debt của team, không phải
  lỗi của họ.

*Mentor bằng câu hỏi*
- *Mentor* là kèm người khác tiến bộ. Cách hiệu quả là đặt câu hỏi để họ tự tìm ra, thay vì đưa
  đáp án.
  - Ví dụ: thấy code kiểm tra tồn kho rồi mới trừ, đừng nói "sai rồi, dùng lock đi". Hãy hỏi: "Em
    nghĩ cách này có vấn đề gì khi có hai request cùng lúc?"
- Vì sao: tự tìm ra thì nhớ lâu, và lần sau họ tự nhận ra các lỗi cùng loại.
- ⚠️ Hỏi không có nghĩa là để họ loay hoay mãi. Khi có sự cố production hay deadline sát, nói
  thẳng cách sửa, giải thích sau.

*Giao việc*
- Giao việc hơi vượt khả năng hiện tại của người đó, kèm hỗ trợ: review thiết kế trước khi code,
  hẹn trao đổi giữa chừng.
- Để người khác làm cả những việc mình làm nhanh hơn, vì đó là cách họ lớn.
  - Ví dụ: bạn sửa lỗi queue trong 1 giờ, junior mất 1 ngày. Lần đầu mất 1 ngày, lần sau họ tự
    làm, và bạn rảnh tay cho việc khác.
- ⚠️ Senior làm hết việc khó thì team không ai lớn lên, và senior thành *nút thắt* (bottleneck):
  mọi việc quan trọng đều phải chờ một người.

*Đo tiến bộ*
- Câu hỏi để đo: người đó giờ tự làm được việc gì mà 3 tháng trước chưa làm được?
- Ví dụ một kết quả kể được trong phỏng vấn: "Sau 3 tháng, bạn ấy tự thiết kế và làm luồng hoàn
  tiền, tôi chỉ review một lần."

**Đọc**
- Staff Engineer: [Create space for others](https://staffeng.com/guides/create-space-for-others/)
- The Staff Engineer's Path: Part III (*Leveling Up*), ch.7 (*You're a Role Model Now*) và ch.8 (*Good Influence at Scale*)

**Nắm chắc khi**
- [ ] Viết xong câu chuyện STAR mentor một người cụ thể, có kết quả đo được (thời gian onboard, việc họ tự làm được sau N tháng)
- [ ] Viết xong một kế hoạch onboarding 2 tuần cho người mới vào team hiện tại

#### 3.2 Góp ý và nhận góp ý

**Vì sao cần học:** Vòng behavioral senior hay có cặp câu "kể về lần bạn đưa một góp ý khó" và
"lần bạn nhận một góp ý khó". Trong công việc, ngày nào bạn cũng góp ý qua code review, và cách
góp ý quyết định team có dám nói thật với nhau không.

**Học gì**

*Đưa góp ý*
- *Góp ý* (feedback) tốt có 4 đặc điểm:
  - Cụ thể: nói về một sự việc, không nói chung chung.
  - Về hành vi và tác động của nó, không về tính cách.
  - Sớm: ngay sau sự việc, khi mọi người còn nhớ rõ.
  - Riêng tư, khi đó là góp ý tiêu cực.
- So sánh:
  - Kém: "Em làm việc thiếu cẩn thận."
  - Tốt: "Tuần này có hai PR em merge khi CI còn đỏ (hành vi). Staging hỏng nửa ngày, QA không
    test được (tác động). Lần sau em đợi CI xanh rồi mới merge nhé."
- ⚠️ Né góp ý khó để giữ hoà khí thì vấn đề to dần, và người đó mất cơ hội sửa.

*Nhận góp ý*
1. Nghe hết, không ngắt lời để giải thích.
2. Hỏi rõ, ví dụ: "Anh cho em một ví dụ cụ thể được không?"
3. Cảm ơn.
4. Rồi mới quyết định làm gì. Nhận góp ý không có nghĩa là phải đồng ý mọi điểm.

*Góp ý trong code review*
- Code review cũng là góp ý. Nói về code, không nói về người.
  - Kém: "Sao em lại viết thế này?"
  - Tốt: "Đoạn này query trong vòng lặp, sẽ thành 101 query khi có 100 đơn. Dùng
    `with('items')` được không?"
- Khi bị phản đối: xét lý do của người kia trước khi giữ quan điểm. Nhiều khi họ đúng.

*Khung Radical Candor*
- *Radical Candor* (sách của Kim Scott) là khung "quan tâm cá nhân + thẳng thắn": quan tâm thật
  tới người đó, và vẫn nói thẳng điều cần nói.
- Thiếu một trong hai vế thì hỏng:
  - Thẳng mà không quan tâm: thành gây hấn.
  - Quan tâm mà không thẳng: thành né góp ý, như cạm bẫy ⚠️ ở trên. Kim Scott gọi đây là
    *ruinous empathy* (sự đồng cảm tai hại).
- Đọc sách nếu muốn đi sâu.

**Đọc**
- Google eng-practices: [Handling pushback in code reviews](https://google.github.io/eng-practices/review/reviewer/pushback.html), [How to write code review comments](https://google.github.io/eng-practices/review/reviewer/comments.html)

**Nắm chắc khi**
- [ ] Có một câu chuyện đưa góp ý khó cho đồng nghiệp và một câu chuyện nhận góp ý khó, mỗi câu kể trong 2 phút, nói rõ thay đổi sau đó

#### 3.3 Đưa quyết định qua nhiều bên, ảnh hưởng khi không có quyền

**Vì sao cần học:** Senior thường cần team khác làm một việc mà mình không có quyền ra lệnh: team
hạ tầng nâng cấp, team mobile đổi API. Câu "thuyết phục team khác" và "bất đồng với manager" rất
hay gặp. Người phỏng vấn tìm dấu hiệu bạn thuyết phục bằng dữ liệu và lợi ích chung, không bằng
ép buộc.

**Học gì**

*Chuẩn bị trước buổi họp*
- Nói chuyện riêng với từng bên trước buổi họp chung. Không để ai bị bất ngờ trong họp.
- Vì sao: người bị bất ngờ trước đám đông thường phản đối để giữ thể diện, kể cả khi ý tưởng tốt.
- Ví dụ: định đề xuất bỏ API v1. Gặp riêng lead mobile trước, hỏi app bản cũ còn bao nhiêu người
  dùng gọi v1, rồi mới đưa đề xuất vào buổi họp chung.

*Gỡ tranh luận bế tắc*
- Tách hai loại bất đồng:

  | | Bất đồng về dữ liệu | Bất đồng về giá trị |
  |---|---|---|
  | Là gì | tranh cãi về một sự thật đo được | hai bên ưu tiên khác nhau |
  | Ví dụ | "MySQL có chịu được 5.000 lượt ghi mỗi giây không?" | "Ưu tiên ra mắt nhanh hay ưu tiên dễ bảo trì?" |
  | Cách gỡ | đo, benchmark | làm rõ ai quyết, dựa trên mục tiêu chung của công ty |

- Tranh luận không đi tới đâu:
  1. Làm thử nghiệm nhỏ: *spike* (làm thử nhanh để trả lời một câu hỏi kỹ thuật, code bỏ đi sau
     đó), prototype, hoặc benchmark.
  2. Đặt thời hạn quyết định.
  3. Xác định ai là người quyết.

*Thuyết phục team khác*
- Dùng lợi ích của chính họ, dữ liệu và prototype.
  - Ví dụ: muốn team payment thêm idempotency key (khoá để một yêu cầu gửi lặp chỉ được xử lý
    một lần). Đừng nói "chuẩn là phải có". Hãy đưa số: "tháng trước 37 đơn bị trừ tiền hai lần
    vì retry, support mất 20 giờ xử lý", kèm một PR mẫu làm sẵn phần khó.
- Xây uy tín bằng cách giúp người khác trước khi cần nhờ họ.
- ⚠️ Thắng tranh luận bằng chức danh hoặc giọng to thì mất sự ủng hộ khi triển khai.

*Bất đồng với manager về ưu tiên*
1. Hiểu bối cảnh họ có mà mình không có: áp lực kinh doanh, cam kết với khách hàng, ngân sách.
2. Đưa dữ liệu và rủi ro.
3. Đề xuất phương án.
4. Đã quyết thì disagree and commit (module 1.2).

**Đọc**
- Staff Engineer: [Staying aligned with authority](https://staffeng.com/guides/staying-aligned-with-authority/), [Getting in the room](https://staffeng.com/guides/getting-in-the-room/)
- The Staff Engineer's Path: ch.3 (*Creating the Big Picture*): viết strategy và đưa nó qua tổ chức
- Bezos: [2016 Letter to Shareholders](https://www.aboutamazon.com/news/company-news/2016-letter-to-shareholders) (disagree and commit)

**Nắm chắc khi**
- [ ] Viết xong câu chuyện STAR thuyết phục một team khác (hoặc người không báo cáo cho bạn) thay đổi cách làm, có kết quả đo được
- [ ] Viết xong câu chuyện bất đồng với lead/manager, nói rõ bạn đã hiểu thêm gì từ phía họ

#### 3.4 Tuyển người

**Vì sao cần học:** Senior thường được mời làm người phỏng vấn. Công ty hỏi "bạn từng tham gia
tuyển người chưa" để xem bạn có góp phần xây team. Ngồi ghế người chấm cũng giúp bạn hiểu người
phỏng vấn mình đang tìm gì.

**Học gì**

*Phỏng vấn theo tiêu chí*
- Thống nhất tiêu chí chấm **trước** khi phỏng vấn. Bảng tiêu chí này thường gọi là *rubric*:
  mỗi tiêu chí có mô tả thế nào là đạt, thế nào là chưa đạt.
  - Ví dụ tiêu chí "thiết kế DB": đạt khi tự đề xuất được index cho query chính và giải thích vì
    sao. Chưa đạt khi chỉ liệt kê được các bảng.
- Biết mỗi câu hỏi đang chấm tiêu chí nào. Câu không gắn với tiêu chí nào thì bỏ.
- Ghi nhận bằng chứng, không ghi cảm tính.
  - Kém: "Bạn này có vẻ giỏi."
  - Tốt: "Tự phát hiện race condition khi hai request cùng trừ kho, đề xuất `SELECT ... FOR
    UPDATE`."

*Viết feedback*
- Viết sao cho người đọc quyết được mà không cần hỏi lại. Một feedback tốt có:
  - kết luận (tuyển hay không, ở level nào),
  - từng tiêu chí kèm bằng chứng,
  - những điểm bạn chưa chắc, để vòng sau hỏi thêm.

*Thiên kiến*
- *Thiên kiến* (bias) là xu hướng đánh giá lệch mà người chấm không nhận ra. Hai loại hay gặp:
  - ⚠️ "Giống mình": chấm cao người học cùng trường, dùng cùng stack, có cùng cách nói chuyện.
  - ⚠️ Ấn tượng 5 phút đầu: đã quyết trong đầu từ lúc chào hỏi, phần còn lại của buổi chỉ tìm
    bằng chứng cho quyết định đó.
- Cách giảm: chấm theo rubric, ghi bằng chứng ngay trong buổi, chấm độc lập trước khi bàn với
  người phỏng vấn khác.

*Dùng cho chính mình*
- Kinh nghiệm phỏng vấn người khác giúp hiểu người phỏng vấn mình đang tìm gì: họ chấm theo tiêu
  chí, và họ cần bằng chứng cụ thể từ câu trả lời của bạn.

**Đọc**
- *An Elegant Puzzle*: chương *Careers* (phần hiring funnel và thiết kế vòng phỏng vấn)
- Tech Interview Handbook: [Coding interview rubrics](https://www.techinterviewhandbook.org/coding-interview-rubrics/) (góc nhìn người chấm)

**Nắm chắc khi**
- [ ] Viết xong bộ tiêu chí chấm cho một vòng phỏng vấn backend mid, mỗi tiêu chí có ví dụ "đạt" và "chưa đạt"
- [ ] Kể được trong 1 phút một lần bạn phỏng vấn hoặc tham gia tuyển người, và điều bạn rút ra

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: kể thành tiếng bằng câu chuyện thật của bạn, bấm giờ 2–3 phút, rồi đối chiếu với
hướng trả lời. Câu nào không có câu chuyện để kể thì quay lại module ghi trong ngoặc và viết
câu chuyện trước.

### 🟢 Junior

**1. Bạn làm gì khi nhận một task mà không hiểu rõ yêu cầu?** (2.3)
- Ý phải có: viết lại yêu cầu bằng lời của mình, hỏi người giao, xác nhận trường hợp biên trước khi code
- Red flag: làm theo cách mình đoán rồi sửa khi bị review

**2. Bạn xử lý góp ý trong code review thế nào?** (3.2)
- Ý phải có: đọc để hiểu lý do, hỏi lại khi không rõ, sửa hoặc giải thích quan điểm bằng lý lẽ
- Điểm cộng: một ví dụ góp ý làm bạn thay đổi cách viết code lâu dài

### 🟡 Mid

**3. Kể về một lần bạn phải làm việc với yêu cầu không rõ ràng.** (2.3)
- Ý phải có: cách làm rõ (viết lại, liệt kê trường hợp biên, prototype), ai tham gia, kết quả
- Điểm cộng: phát hiện ra vấn đề thật của người dùng khác với yêu cầu ban đầu, và đề xuất cách đơn giản hơn

**4. Bạn ước lượng công việc thế nào? Khi ước lượng sai thì làm gì?** (2.1)
- Ý phải có: chia nhỏ, ước lượng theo khoảng, tính các việc hay quên; báo sớm khi lệch kèm phương án
- Điểm cộng: số liệu sai lệch thật và thay đổi cách ước lượng sau đó
- Red flag: "em cộng thêm 30% cho chắc" mà không nói được rủi ro nằm ở đâu

**5. Bạn xử lý tech debt thế nào trong khi vẫn phải làm tính năng?** (1.5)
- Ý phải có: phân loại, ưu tiên theo lãi suất, trả dần gắn với tính năng
- Điểm cộng: số liệu dùng để thuyết phục (thời gian làm tính năng, số sự cố); một khoản debt quyết định **không** trả và lý do
- Red flag: "xin một sprint để refactor" mà không nói được lợi ích

**6. Kể về một sự cố production bạn từng xử lý.** (2.5)
- Ý phải có: ảnh hưởng, cách phát hiện, giảm thiệt hại trước, root cause ở tầng hệ thống, phòng ngừa lâu dài
- Điểm cộng: postmortem blameless, action item được theo đến cùng
- Red flag: đổ lỗi cho người khác; dừng ở nguyên nhân bề mặt

**7. Deadline cố định, không kịp làm hết. Bạn làm gì?** (2.2)
- Ý phải có: báo sớm, đưa lựa chọn phạm vi, để product chọn; không lặng lẽ cắt chất lượng
- Điểm cộng: phần bị cắt được ghi lại và đã làm sau đó

### 🔴 Senior

**8. Kể về quyết định kỹ thuật quan trọng nhất bạn từng đưa ra. Nếu làm lại, bạn có đổi không?** (1.2, 1.4)
- Ý phải có: bối cảnh và ràng buộc, các phương án, tiêu chí, cái giá; nhìn lại với thông tin hiện tại
- Điểm cộng: có design doc/ADR; nói được điều kiện nào thì quyết định đó sai
- Red flag: không có phương án nào khác được cân nhắc; "không đổi gì cả" mà không phân tích

**9. Bạn chọn một công nghệ mới cho team theo tiêu chí gì?** (1.3)
- Ý phải có: vấn đề mà công nghệ hiện tại không giải được, chi phí vận hành, ai vận hành, kỹ năng team
- Điểm cộng: một lần bạn **từ chối** đưa công nghệ mới vào; boring technology
- Red flag: "vì nó nhanh/phổ biến"

**10. Có nên chuyển sang microservices không?** (1.2)
- Ý phải có: hỏi vấn đề đang gặp là gì; xem modular monolith có giải quyết được không; điều kiện tiên quyết (CI/CD, observability, ownership rõ theo team)
- Điểm cộng: đây là quyết định khó đảo ngược nên cần design doc; tách dần theo strangler fig. Xem [15-architecture.md](15-architecture.md)
- Red flag: liệt kê lợi ích của microservices mà không hỏi bối cảnh

**11. Kể về một migration lớn bạn đã tham gia hoặc dẫn dắt.** (2.4)
- Ý phải có: vì sao phải migrate, các bước, tiêu chí đi tiếp và rollback mỗi bước, cách kiểm chứng dữ liệu
- Điểm cộng: shadow read và so sánh chênh lệch; lịch trình cutover; điều đã sai và cách xử lý

**12. Product muốn một tính năng lớn trong 2 tuần, bạn ước lượng 5 tuần.** (2.1, 2.2)
- Ý phải có: chia theo giá trị, đề xuất phần làm được trong 2 tuần; nêu rủi ro nếu ép cả tính năng
- Điểm cộng: product chọn phạm vi, kỹ thuật chịu trách nhiệm ước lượng; phần còn lại có kế hoạch
- Red flag: nhận 2 tuần rồi làm thêm giờ, hoặc từ chối thẳng không có phương án

**13. Hai senior tranh cãi PostgreSQL hay MongoDB cho dự án mới đã hai tuần chưa ngã ngũ. Bạn làm gì?** (3.3)
- Ý phải có: viết tiêu chí quyết định và kiểu truy cập dữ liệu thật; prototype phần dữ liệu khó nhất; đặt hạn và người quyết
- Điểm cộng: ghi ADR; disagree and commit; tách bất đồng dữ liệu khỏi bất đồng giá trị

**14. Bạn được giao module legacy không test, không tài liệu, người viết đã nghỉ, cần thêm tính năng gấp.** (2.4)
- Ý phải có: đọc code và lịch sử git, hỏi người dùng module; characterization test cho phần sắp sửa; thay đổi nhỏ nhất sau feature flag
- Điểm cộng: ghi lại những gì đã hiểu cho người sau
- Red flag: đề xuất viết lại từ đầu

**15. Một junior liên tục mở PR lớn, chất lượng thấp, review mất nhiều thời gian.** (3.1, 3.2)
- Ý phải có: nói chuyện riêng để hiểu nguyên nhân (không biết chia việc, sợ hỏi, bị ép deadline); cùng chia task trước khi code; pair vài lần; đặt kỳ vọng PR nhỏ
- Điểm cộng: đo tiến bộ sau vài tuần; sửa cả quy trình (template PR, giới hạn kích thước) chứ không chỉ sửa người

**16. Bạn thuyết phục một team khác thay đổi cách làm thế nào?** (3.3)
- Ý phải có: hiểu lợi ích và ràng buộc của họ, dữ liệu, prototype, làm phần việc khó giúp họ
- Điểm cộng: đã chấp nhận thay đổi đề xuất của mình theo góp ý của họ
- Red flag: nhờ cấp trên ép

**17. Khi bạn và engineering manager bất đồng về ưu tiên, bạn làm gì?** (3.3)
- Ý phải có: hỏi để hiểu bối cảnh họ có, đưa dữ liệu và rủi ro, đề xuất phương án; đã quyết thì disagree and commit
- Điểm cộng: ghi lại rủi ro đã nêu; nhìn lại sau đó ai đúng và học được gì

**18. Làm sao bạn biết một dự án đang đi chệch hướng, và bạn làm gì?** (2.2)
- Ý phải có: tín hiệu (mốc trễ liên tiếp, phạm vi phình, dependency chưa xác nhận); nói ra sớm, đề xuất cắt phạm vi hoặc đổi kế hoạch
- Điểm cộng: một dự án thật bạn đã kéo lại được, hoặc đề xuất dừng

**19. Bạn giúp một người trong team tiến bộ rõ rệt thế nào?** (3.1)
- Ý phải có: người cụ thể, xuất phát điểm, kế hoạch, việc giao dần lớn hơn, kết quả đo được
- Red flag: "em trả lời khi bạn ấy hỏi"

**20. Cần chuyển bảng `orders` 500 triệu dòng sang database mới không downtime.** (2.4)
- Ý phải có: dual write hoặc CDC, backfill, shadow read so sánh, chuyển dần đọc rồi ghi, giữ rollback
- Điểm cộng: tiêu chí đi tiếp của từng bước; theo dõi chênh lệch; outbox thay cho dual write trực tiếp ([12-messaging.md](12-messaging.md))

---

## Bài tập tự làm

1. **Design doc**: chọn một tính năng bạn đã làm, viết lại thành design doc theo cấu trúc ở
   module 1.4 (tối đa 2 trang), có mục phương án đã loại và lý do.
2. **ADR**: viết 2 ADR cho hai quyết định kỹ thuật có thật trong dự án của bạn.
3. **Ước lượng**: chia một tính năng sắp làm thành các phần dưới 1 ngày, ước lượng theo
   khoảng, đánh dấu phần rủi ro. Sau khi làm xong, so sánh với thực tế.
4. **Tech debt**: liệt kê 5 khoản tech debt trong dự án, xếp theo "lãi suất" và viết một
   đoạn thuyết phục đầu tư trả khoản đứng đầu, dùng hệ quả kinh doanh.
5. **Kế hoạch migration**: viết kế hoạch 6 bước (module 2.4) cho một thay đổi lưu trữ có thật
   hoặc giả định trong dự án, mỗi bước có tiêu chí đi tiếp và rollback.
6. **Câu chuyện senior**: viết 3 câu chuyện theo STAR cho các câu 🔴 ở Phần 2 (gợi ý: 8, 11,
   16), mỗi câu kể dưới 3 phút, có số liệu.

> Nộp bài vào đây để được review.
