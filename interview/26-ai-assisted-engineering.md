# 26. Dùng AI trong công việc và coding

> [← Mục lục](README.md) · Trọng tâm: dùng AI coding assistant và coding agent trong công việc hằng ngày của backend engineer (PHP/Laravel): giao việc, kiểm chứng, review, bảo mật, đưa vào team, đo hiệu quả. Tích hợp LLM vào sản phẩm là chủ đề khác, ở [23-ai-llm-backend.md](23-ai-llm-backend.md).
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

Hai lưu ý riêng cho file này:
- **Công cụ đổi rất nhanh**, vài tháng lại có tính năng mới. File cố ý dạy nguyên lý (giao việc,
  kiểm chứng, quản lý rủi ro) thay vì thao tác của một công cụ cụ thể. Tên công cụ trong file chỉ
  là ví dụ.
- **Chủ đề này học bằng tay là chính.** Người phỏng vấn nghe ra ngay ai đã thật sự làm việc với
  coding agent và ai chỉ đọc bài viết. Mỗi module nên đi kèm một việc thật trong dự án của bạn.

---

## Tài liệu nền

Dùng xuyên suốt file. Các module bên dưới chỉ rõ đọc phần nào.

| Tài liệu | Loại | Dùng cho |
|---|---|---|
| [Claude Code: Best practices](https://www.anthropic.com/engineering/claude-code-best-practices) | Hướng dẫn của nhà cung cấp | Quy trình làm việc với coding agent: khám phá, lập kế hoạch, code, kiểm chứng; file hướng dẫn cho agent. Nguyên lý dùng được cho công cụ khác |
| [Simon Willison: Here's how I use LLMs to help me write code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/) | Blog | Cách một kỹ sư kỳ cựu dùng LLM khi code, rất thực tế. Cả [tag ai-assisted-programming](https://simonwillison.net/tags/ai-assisted-programming/) đáng theo dõi |
| [Martin Fowler: Exploring Generative AI](https://martinfowler.com/articles/exploring-gen-ai.html) | Loạt bài | Góc nhìn của Thoughtworks về AI trong phát triển phần mềm, nhiều bài về rủi ro và chất lượng |
| [DORA 2025: State of AI-assisted Software Development](https://dora.dev/research/2025/dora-report/) | Nghiên cứu | Số liệu về mức dùng AI, ảnh hưởng tới throughput và độ ổn định, mô hình 7 năng lực |
| [METR: nghiên cứu năng suất lập trình viên](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) và [bản cập nhật 02/2026](https://metr.org/blog/2026-02-24-uplift-update/) | Nghiên cứu | Thí nghiệm có đối chứng về việc AI làm dev nhanh hay chậm, và vì sao đo điều này rất khó |
| [Stack Overflow Developer Survey 2025: AI](https://survey.stackoverflow.co/2025/ai) | Khảo sát | Mức dùng, mức tin tưởng, những điểm dev thấy khó chịu nhất |
| [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/) | Chuẩn bảo mật | Prompt injection và các rủi ro khi cho AI đọc dữ liệu, chạy lệnh |
| [Laravel Boost](https://laravel.com/docs/boost) | Official docs | Bộ hướng dẫn, skill và MCP server giúp agent viết Laravel đúng chuẩn |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Hiểu công cụ làm được gì và sai ở đâu; giao việc rõ ràng; luôn kiểm chứng | 2–3 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.6 | Có quy trình làm việc với agent, quản lý context, review code AI viết, giữ an toàn dữ liệu | 5–7 ngày, kèm làm việc thật |
| **3. Senior** 🔴 | 3.1–3.4 | Đo hiệu quả thật, đưa AI vào team có quy tắc, dựng guardrail, giữ kỹ năng nền | 3–4 ngày |

Học theo thứ tự: chặng 2 dựa trên hiểu biết "AI sai ở đâu" của chặng 1, và chặng 3 là góc nhìn
của người chịu trách nhiệm cho cả team chứ không chỉ cho code của mình. Với vị trí senior, câu hỏi
thường không phải "bạn có dùng AI không" mà là "bạn dùng thế nào để vừa nhanh hơn vừa không làm
hỏng chất lượng, và bạn giúp team làm điều đó ra sao".

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 AI coding tool hoạt động thế nào (ở mức người dùng cần biết)

**Vì sao cần học:** Không cần biết cách huấn luyện model, nhưng phải hiểu vài đặc điểm gốc để
biết vì sao AI viết code trông rất đúng mà vẫn sai. Người phỏng vấn hay mở đầu bằng "AI hay sai
ở chỗ nào, vì sao" để xem bạn dùng nó có ý thức hay không.

**Học gì**

*Model sinh chữ như thế nào*
- *LLM* (large language model) sinh ra câu trả lời bằng cách đoán từng mẩu chữ tiếp theo dựa trên
  những gì đã có. Mỗi mẩu gọi là *token*, thường là một phần của từ.
  - Tiếng Anh trung bình khoảng 3–4 ký tự một token. Tiếng Việt có dấu thường tốn nhiều token hơn
    cho cùng lượng nội dung.
- Model không "tra cứu" sự thật. Nó sinh ra thứ **nghe hợp lý nhất** theo những gì nó đã học.
  Vì vậy nó có thể viết ra một hàm, một option hay một package **không tồn tại** với giọng rất tự
  tin. Hiện tượng này gọi là *hallucination*.
  - Ví dụ: gợi ý `Cache::rememberForeverLocked()` trong Laravel, một method nghe rất hợp lý nhưng
    không có.
- Chạy cùng một câu hỏi hai lần có thể ra hai kết quả khác nhau (*non-deterministic*). Đừng coi
  một lần trả lời đúng là bằng chứng nó luôn đúng.

*Context window*
- *Context window* là lượng chữ tối đa model "nhìn thấy" trong một lần làm việc: câu hỏi của bạn,
  file bạn đưa vào, lịch sử hội thoại, kết quả các lệnh agent đã chạy. Ngoài phần đó, model không
  biết gì về dự án của bạn.
- Context có giới hạn, và càng dài thì chất lượng càng dễ giảm: thông tin nằm giữa một context rất
  dài dễ bị bỏ sót hơn thông tin ở đầu hoặc cuối.
- Hệ quả thực tế:
  - Model không biết quy ước của team nếu bạn không nói hoặc không có file hướng dẫn (module 2.2).
  - Một phiên làm việc quá dài, nhiều việc lẫn lộn, thì chất lượng giảm dần. Nên mở phiên mới cho
    việc mới.

*Knowledge cutoff*
- Model chỉ biết những gì có trong dữ liệu huấn luyện, tới một mốc gọi là *knowledge cutoff*.
- ⚠️ Vì vậy nó hay viết theo phiên bản cũ: cú pháp Laravel của bản trước, option đã bị bỏ, cách
  làm đã bị deprecate. Với framework thay đổi nhanh, đây là nguồn lỗi rất thường gặp.
- Cách giảm: cho agent đọc docs đúng phiên bản (qua MCP hoặc dán vào), và ghi rõ phiên bản trong
  file hướng dẫn của dự án.

*Tại sao "trông đúng" nguy hiểm hơn "sai rõ ràng"*
- Code AI viết thường đúng cú pháp, đặt tên đẹp, có comment. Lỗi nằm ở logic nghiệp vụ, trường hợp
  biên, concurrency, bảo mật, tức là những chỗ **không nhìn ra khi đọc lướt**.
- Khảo sát Stack Overflow 2025: điều dev thấy khó chịu nhất là câu trả lời "gần đúng nhưng chưa
  đúng hẳn" (66%), và 46% dev không tin độ chính xác của AI.

**Đọc**
- [Stack Overflow Developer Survey 2025: AI](https://survey.stackoverflow.co/2025/ai): phần trust và frustrations
- [Lost in the Middle: How Language Models Use Long Contexts](https://arxiv.org/abs/2307.03172) (Liu và cộng sự, 2023): chỉ cần đọc abstract và hình 1
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents): phần đầu, về việc context là tài nguyên có hạn

**Nắm chắc khi**
- [ ] Giải thích được bằng lời thường vì sao AI có thể bịa ra một method không tồn tại mà vẫn rất tự tin
- [ ] Kể được 3 loại lỗi AI hay mắc khi viết code cho một framework thay đổi nhanh như Laravel
- [ ] Giải thích được vì sao một phiên làm việc dài, nhiều việc lẫn lộn thì chất lượng giảm

#### 1.2 Các loại công cụ và khi nào dùng loại nào

**Vì sao cần học:** "Bạn dùng công cụ AI nào, dùng vào việc gì" là câu mở đầu rất hay gặp. Trả lời
tốt là nói được mỗi loại hợp với việc gì, chứ không phải kể tên sản phẩm.

**Học gì**

*Bốn nhóm công cụ*

| Nhóm | Là gì | Ví dụ | Hợp với việc |
|---|---|---|---|
| Autocomplete trong IDE | Gợi ý vài dòng tiếp theo khi bạn đang gõ | Gợi ý inline của Copilot, Cursor | Code lặp lại, boilerplate, viết tiếp theo mẫu có sẵn |
| Chat | Hỏi đáp trong cửa sổ chat, bạn tự chép code qua lại | ChatGPT, Claude, Gemini, chat trong IDE | Giải thích khái niệm, hỏi nhanh, phác ý tưởng |
| Coding agent | Tự đọc file trong repo, sửa nhiều file, chạy lệnh (test, lint), lặp lại tới khi xong | Claude Code, Codex CLI, Cursor agent, Copilot agent mode | Việc nhiều bước trong một repo: sửa bug, thêm tính năng, refactor |
| Agent chạy nền / trên CI | Nhận một issue, tự làm trên môi trường riêng, mở pull request | Copilot coding agent, các agent chạy trên GitHub Actions | Việc nhỏ rõ ràng, việc lặp lại; người review PR như với đồng nghiệp |

- Ranh giới giữa các nhóm ngày càng mờ; nhiều công cụ có cả bốn chế độ.

*Khác biệt quan trọng nhất: chat và agent*
- Với chat, bạn quyết định đưa gì cho model và tự chép kết quả về. Bạn kiểm soát từng bước.
- Với agent, model tự đi tìm file, tự sửa, tự chạy lệnh trên máy của bạn. Nhanh hơn rất nhiều cho
  việc nhiều bước, nhưng:
  - Nó có thể sửa những file bạn không định cho sửa.
  - Nó có thể chạy lệnh nguy hiểm nếu bạn cho phép (xoá file, chạy migration, push code).
  - Nó có thể đọc phải nội dung độc hại (prompt injection, module 2.5).
- Vì vậy agent có *permission mode*: hỏi trước mỗi lệnh, cho phép sẵn một số lệnh an toàn, hoặc
  chạy trong sandbox. Hiểu và cấu hình phần này là trách nhiệm của bạn.

*Chọn công cụ theo việc*
- Hiểu một khái niệm, so sánh hai cách làm: chat.
- Viết tiếp code theo mẫu có sẵn trong file: autocomplete.
- Sửa bug cần đọc nhiều file, chạy test để xác nhận: agent.
- Việc nhỏ đã rõ yêu cầu và có test tốt, ví dụ nâng một dependency: agent chạy nền, rồi review PR.
- ⚠️ Việc cần phán đoán nghiệp vụ hoặc kiến trúc, ví dụ chọn cách chia service: dùng AI để brainstorm
  và phản biện, không giao cho nó quyết định.

**Đọc**
- [Claude Code: Overview](https://code.claude.com/docs/en/overview): để hiểu một coding agent làm được những gì
- [GitHub Copilot docs](https://docs.github.com/en/copilot) và [About Copilot coding agent](https://docs.github.com/en/copilot/concepts/agents/coding-agent/about-coding-agent): ví dụ về agent chạy nền, mở PR
- [Claude Code: Security](https://code.claude.com/docs/en/security): permission và sandbox của một coding agent

**Nắm chắc khi**
- [ ] Với 5 việc cụ thể trong tuần làm việc của bạn, chọn được loại công cụ phù hợp và giải thích vì sao
- [ ] Nói được 3 rủi ro của coding agent mà chat không có
- [ ] Đã cấu hình permission cho agent đang dùng: lệnh nào tự chạy, lệnh nào phải hỏi

#### 1.3 Giao việc cho AI: prompt và context

**Vì sao cần học:** Chất lượng output phụ thuộc rất nhiều vào cách giao việc. Người mới hay viết
một câu ngắn rồi thất vọng; người dùng giỏi giao việc giống như giao cho một đồng nghiệp mới vào
team, thông minh nhưng không biết gì về dự án.

**Học gì**

*Giao việc như giao cho đồng nghiệp mới*
- Một yêu cầu tốt có đủ 5 phần:
  1. **Mục tiêu**: cần đạt được gì, và vì sao.
  2. **Bối cảnh**: file nào liên quan, quy ước gì, phiên bản PHP/Laravel nào.
  3. **Ràng buộc**: không được đổi gì, không thêm dependency, phải tương thích ngược.
  4. **Định nghĩa "xong"**: test nào phải pass, lệnh nào phải chạy sạch.
  5. **Ví dụ** (nếu có): một đoạn code mẫu theo đúng phong cách team.
- Ví dụ so sánh:

  ```text
  Kém:  Thêm rate limit cho API.

  Tốt:  Thêm rate limit cho các route trong routes/api.php nhóm "public":
        60 request/phút theo IP, user đã đăng nhập 300 request/phút theo user id.
        Dùng RateLimiter có sẵn của Laravel (bản 13), định nghĩa trong AppServiceProvider,
        không thêm package. Khi vượt giới hạn trả 429 kèm header Retry-After.
        Viết feature test bằng Pest cho cả hai trường hợp. Xong khi `php artisan test`
        và `vendor/bin/phpstan` đều sạch.
  ```

*Chia nhỏ và yêu cầu kế hoạch trước*
- Việc lớn thì chia thành các bước nhỏ, mỗi bước kiểm chứng được. AI làm tốt việc nhỏ rõ ràng hơn
  nhiều so với việc lớn mơ hồ.
- Với việc nhiều bước: yêu cầu AI **đọc code và đưa kế hoạch trước, chưa sửa gì**. Bạn duyệt kế
  hoạch rồi mới cho làm. Sửa một kế hoạch sai rẻ hơn rất nhiều so với sửa 500 dòng code sai.
- Bảo AI **hỏi lại** khi chưa rõ, thay vì tự đoán.

*Lặp lại có chủ đích*
- Kết quả chưa đúng thì nói cụ thể sai ở đâu ("test X fail vì Y"), đừng chỉ nói "sai rồi, làm lại".
- ⚠️ Sửa đi sửa lại trong cùng một phiên mà vẫn sai thì thường là context đã rối. Mở phiên mới, giao
  việc lại từ đầu với thông tin rõ hơn, thường nhanh hơn cố gắng tiếp.

*Dùng AI để hỏi, không chỉ để làm*
- Hỏi AI giải thích một đoạn code lạ, đưa ra 3 cách làm kèm ưu nhược, hoặc phản biện thiết kế của
  bạn ("chỉ ra 5 điểm yếu nhất"). Đây là cách dùng ít rủi ro mà giá trị cao.

**Đọc**
- [Claude Code: Best practices](https://www.anthropic.com/engineering/claude-code-best-practices): các phần về viết chỉ dẫn cụ thể và yêu cầu lập kế hoạch trước
- [Anthropic: Prompt engineering overview](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/overview): nguyên tắc chung, áp dụng cho mọi model
- [Simon Willison: Here's how I use LLMs to help me write code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/): phần "context is king" và "tell them exactly what to do"

**Nắm chắc khi**
- [ ] Viết lại được một yêu cầu một dòng thành yêu cầu đủ 5 phần cho một việc thật trong dự án
- [ ] Đã làm ít nhất một việc theo kiểu "đưa kế hoạch trước, duyệt rồi mới làm", và thấy được khác biệt
- [ ] Nhận ra được lúc nên bỏ phiên đang rối để mở phiên mới

#### 1.4 Kiểm chứng output: bạn là người chịu trách nhiệm

**Vì sao cần học:** Đây là ý quan trọng nhất của cả file. Code AI viết mà bạn merge là **code của
bạn**. Người phỏng vấn muốn nghe bạn kiểm chứng thế nào; câu "AI viết nên em không rõ" là red flag
lớn nhất.

**Học gì**

*Nguyên tắc: hiểu mọi dòng trước khi merge*
- Không merge code mà bạn không giải thích được cho người review. Nếu không hiểu, hỏi AI giải thích,
  rồi tự kiểm tra lại lời giải thích đó.
- Đặc biệt kỹ với: SQL, logic tiền, phân quyền, xử lý lỗi, concurrency, migration.

*Các lớp kiểm chứng*
1. **Đọc diff**: xem chính xác những gì đã đổi, kể cả file bạn không nghĩ nó sẽ động vào.
2. **Chạy test**: test có sẵn phải pass; tính năng mới phải có test mới.
3. **Static analysis và lint**: PHPStan, Pint. Chúng bắt được nhiều lỗi AI hay mắc như gọi method
   không tồn tại, sai kiểu.
4. **Chạy thật**: gọi API, mở màn hình, xem log. Test pass chưa chắc tính năng đúng.
5. **Kiểm tra thông tin bên ngoài**: package, option, method lạ thì tra docs chính thức.

*Những lỗi hay gặp cần soi kỹ*
- ⚠️ **Package không tồn tại hoặc bị giả mạo**: AI gợi ý tên package nghe hợp lý nhưng không có.
  Kẻ xấu đã bắt đầu đăng ký sẵn những cái tên hay bị bịa ra đó, kèm mã độc. Kiểu tấn công này gọi
  là *slopsquatting*. Trước khi `composer require` một package lạ, kiểm tra nó trên Packagist:
  tác giả, số lượt tải, repo, ngày tạo.
- ⚠️ **Sửa test cho pass**: khi test fail, agent có thể sửa chính test (xoá assert, đổi giá trị mong
  đợi) thay vì sửa code. Luôn xem diff của file test.
- ⚠️ **Nuốt lỗi**: bọc `try/catch` rồi bỏ qua exception để "hết lỗi".
- ⚠️ **Test chỉ kiểm tra mock**: test mock hết mọi thứ nên luôn pass, không kiểm tra hành vi thật.
- ⚠️ **Làm quá yêu cầu**: thêm abstraction, config, tính năng không ai yêu cầu, làm diff phình to.

*Ghi nhận khi dùng AI*
- Nhiều team yêu cầu ghi chú trong PR khi phần lớn code do AI tạo ra, để người review biết cần soi
  kỹ chỗ nào. Làm theo quy định của team; không có quy định thì chủ động nói rõ vẫn là cách an toàn.

**Đọc**
- [Socket: The Rise of Slopsquatting](https://socket.dev/blog/slopsquatting-how-ai-hallucinations-are-fueling-a-new-class-of-supply-chain-attacks)
- [Simon Willison: Here's how I use LLMs to help me write code](https://simonwillison.net/2025/Mar/11/using-llms-for-code/): phần "you have to test what it writes"
- Bảo mật dependency nói chung: [10-security.md](10-security.md) (phần supply chain)

**Nắm chắc khi**
- [ ] Có một checklist cá nhân (5–7 mục) bạn luôn chạy trước khi merge code do AI viết
- [ ] Kể được một lần thật AI viết sai mà bạn phát hiện: sai gì, phát hiện bằng cách nào
- [ ] Biết cách kiểm tra một package lạ trước khi cài

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Quy trình làm việc với coding agent

**Vì sao cần học:** Khác biệt giữa người dùng agent hiệu quả và người vật lộn với nó nằm ở quy trình,
không nằm ở câu prompt. Câu "kể cách bạn làm một task với AI từ đầu tới cuối" rất hay gặp.

**Học gì**

*Vòng lặp khám phá, lập kế hoạch, làm, kiểm chứng*
1. **Khám phá**: cho agent đọc code liên quan và tóm tắt lại hiểu biết của nó. Chưa sửa gì. Bạn
   kiểm tra xem nó hiểu đúng chưa.
2. **Lập kế hoạch**: yêu cầu kế hoạch cụ thể (file nào, đổi gì, test gì). Nhiều agent có sẵn chế
   độ *plan mode* chỉ đọc, không sửa.
3. **Làm**: cho agent thực hiện từng bước, chạy test sau mỗi bước.
4. **Kiểm chứng**: bạn đọc diff, chạy lại test, chạy thật (module 1.4).
5. **Commit**: commit nhỏ, message rõ, để dễ quay lại.

*Viết test trước*
- Với bug: yêu cầu agent **viết test tái hiện bug trước**, xác nhận test đó fail, rồi mới sửa code
  cho test pass. Đây là cách chắc nhất để biết bug thật sự được sửa.
- Với tính năng: bạn duyệt test trước (test là đặc tả), rồi mới cho agent viết code.
- ⚠️ Nói rõ "không được sửa test" khi đang ở bước sửa code.

*Dùng git làm điểm lưu*
- Làm việc trên branch riêng. Commit ở mỗi bước ổn định, để khi agent đi sai hướng thì `git reset`
  về điểm trước là xong, không phải gỡ từng thay đổi.
- Xem `git diff` thường xuyên, đừng đợi tới cuối.

*Giữ phạm vi nhỏ*
- Mỗi phiên một việc. Diff nhỏ thì dễ review, dễ tìm lỗi, dễ revert.
- DORA 2025 xếp "làm việc theo lô nhỏ" (*working in small batches*) vào 7 năng lực giúp AI mang lại
  hiệu quả thật, vì AI làm lượng code tăng vọt, và review chính là nút thắt.

**Đọc**
- [Claude Code: Best practices](https://www.anthropic.com/engineering/claude-code-best-practices): phần "explore, plan, code, commit" và "write tests, commit; code, iterate, commit"
- [Claude Code: Common workflows](https://code.claude.com/docs/en/common-workflows): hiểu codebase, sửa bug, refactor, làm việc với test
- [Simon Willison: Vibe engineering](https://simonwillison.net/2025/Oct/7/vibe-engineering/): khác biệt giữa "vibe coding" và dùng agent có kỷ luật kỹ thuật

**Nắm chắc khi**
- [ ] Đã sửa một bug thật theo đúng thứ tự: test tái hiện fail, sửa, test pass, review diff
- [ ] Kể được quy trình của bạn trong 2 phút, kèm một ví dụ cụ thể
- [ ] Quay lại được điểm an toàn bằng git khi agent đi sai hướng, không mất việc đã làm đúng

#### 2.2 Context engineering: file hướng dẫn, MCP, quản lý context

**Vì sao cần học:** Agent chỉ giỏi bằng lượng thông tin đúng mà nó có. Đưa đúng context là kỹ năng
phân biệt người dùng thành thạo, và là việc senior thường làm cho cả team.

**Học gì**

*File hướng dẫn cho agent*
- Hầu hết coding agent đọc một file hướng dẫn trong repo mỗi khi bắt đầu làm việc:
  - `CLAUDE.md` (Claude Code)
  - `AGENTS.md` (định dạng mở, nhiều công cụ cùng đọc)
  - `.github/copilot-instructions.md` (GitHub Copilot)
  - `.cursor/rules/` (Cursor)
- Nên ghi:
  - Lệnh chạy test, lint, static analysis.
  - Phiên bản PHP, Laravel, các package chính.
  - Quy ước của team: cấu trúc thư mục, cách đặt tên, cách xử lý lỗi, những thứ không được làm.
  - Những cạm bẫy riêng của dự án, ví dụ "mọi query phải qua scope tenant".
- Không nên ghi: những thứ đọc code là biết, hướng dẫn chung chung ("viết code sạch"). File quá dài
  làm tốn context mà không giúp gì.
- File này nên được commit và review như code. Mỗi khi agent sai cùng một kiểu hai lần, thêm một
  dòng vào file.

*MCP: cho agent dùng công cụ bên ngoài*
- *MCP* (Model Context Protocol) là chuẩn để kết nối agent với công cụ và dữ liệu bên ngoài: docs
  của framework, database, issue tracker, trình duyệt, log.
- Ví dụ: MCP server của Laravel Boost cho agent đọc schema DB, đọc log lỗi mới nhất, tìm docs đúng
  phiên bản Laravel đang cài.
- ⚠️ Mỗi MCP server là thêm quyền cho agent. Cho agent query DB production là rủi ro lớn; chỉ nối
  với DB local hoặc bản sao đã che dữ liệu (module 2.5).

*Quản lý context trong một phiên*
- Context đầy thì chất lượng giảm. Một số cách giữ context gọn:
  - Mỗi việc một phiên mới.
  - Chỉ đưa file liên quan, đừng dán cả thư mục.
  - Với việc tìm kiếm lớn, dùng *subagent*: một agent phụ đi tìm và chỉ trả về kết luận, giữ context
    của agent chính sạch.
  - Một số công cụ tự tóm tắt (*compact*) lịch sử khi context gần đầy; phần tóm tắt có thể mất chi
    tiết, nên ghi những quyết định quan trọng ra file.

**Đọc**
- [Claude Code: How Claude remembers your project](https://code.claude.com/docs/en/memory): file `CLAUDE.md` và cách tổ chức
- [AGENTS.md](https://agents.md/): định dạng chung cho nhiều công cụ
- [GitHub: Adding repository custom instructions](https://docs.github.com/en/copilot/how-tos/configure-custom-instructions/add-repository-instructions) và [Cursor: Rules](https://cursor.com/docs/context/rules)
- [Model Context Protocol](https://modelcontextprotocol.io/) và [Claude Code: MCP](https://code.claude.com/docs/en/mcp)
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

**Nắm chắc khi**
- [ ] Viết được file hướng dẫn cho agent của một dự án Laravel thật, dưới 100 dòng, và thấy agent làm đúng quy ước hơn
- [ ] Giải thích được MCP là gì và nêu một rủi ro khi thêm MCP server
- [ ] Kể được 3 cách giữ context gọn trong một phiên làm việc dài

#### 2.3 Dùng AI cho từng loại việc backend

**Vì sao cần học:** Người phỏng vấn muốn nghe ví dụ cụ thể: bạn dùng AI vào việc gì thì hiệu quả,
việc gì thì không. Trả lời "dùng cho mọi thứ" hay "chỉ để autocomplete" đều yếu.

**Học gì**

*Những việc AI giúp nhiều*

| Việc | Cách dùng hiệu quả | Cần chú ý |
|---|---|---|
| Đọc codebase lạ | Hỏi luồng một request đi qua những class nào, một bảng được ghi ở đâu | Kiểm tra lại bằng cách mở code; AI có thể đoán sai luồng |
| Debug từ stack trace, log | Dán stack trace và đoạn code liên quan, hỏi các giả thuyết và cách kiểm chứng từng cái | Tự kiểm chứng giả thuyết, đừng áp bản sửa đầu tiên |
| Viết test | Liệt kê trường hợp biên, viết test cho code cũ chưa có test | Soi test có kiểm tra hành vi thật không, hay chỉ kiểm tra mock |
| Refactor, nâng phiên bản | Nâng PHP/Laravel, đổi API cũ sang mới theo từng bước, kèm test | Chạy test sau mỗi bước; đọc upgrade guide chính thức song song |
| SQL | Viết query phức tạp, giải thích `EXPLAIN`, gợi ý index | Chạy `EXPLAIN` thật trên dữ liệu thật; AI không biết phân bố dữ liệu của bạn |
| Script một lần | Script xử lý dữ liệu, regex, lệnh shell | Chạy thử trên bản sao trước; đọc kỹ lệnh xoá/sửa |
| Tài liệu | Nháp design doc, README, mô tả PR, tóm tắt thảo luận | Bạn chịu trách nhiệm nội dung; bỏ phần chung chung |
| Review | Nhờ AI review diff của chính mình trước khi gửi người khác | Không thay cho review của người; coi như một lớp lọc thêm |

*Những việc AI hay làm kém*
- Bug concurrency, race condition, lỗi chỉ xảy ra dưới tải: cần tái hiện và đo, AI chỉ đoán.
- Tối ưu hiệu năng khi chưa đo: AI hay đề xuất tối ưu "nghe hay" ở chỗ không phải nút thắt.
- Nghiệp vụ đặc thù của công ty: AI không biết luật nghiệp vụ nếu không ai nói.
- Quyết định kiến trúc lớn: dùng AI để liệt kê phương án và phản biện, quyết định là của bạn và team.

*Việc nhạy cảm cần thêm một lớp cẩn thận*
- Migration trên bảng lớn, code liên quan tiền, phân quyền, xoá dữ liệu: AI viết nháp được, nhưng
  review kỹ như review code của người mới, và chạy thử trên staging.

**Đọc**
- [How Anthropic teams use Claude Code](https://www.anthropic.com/news/how-anthropic-teams-use-claude-code): ví dụ thật từ nhiều loại team
- [Addy Osmani: The 70% problem](https://addyo.substack.com/p/the-70-problem-hard-truths-about): vì sao AI làm nhanh 70% đầu nhưng 30% cuối vẫn cần kinh nghiệm
- Bối cảnh cho từng việc: [03-database-sql.md](03-database-sql.md) (EXPLAIN), [20-testing-quality.md](20-testing-quality.md) (test), [13-concurrency.md](13-concurrency.md)

**Nắm chắc khi**
- [ ] Kể được 3 việc bạn dùng AI hiệu quả nhất và 2 việc bạn không giao cho AI, kèm lý do
- [ ] Đã dùng AI để đọc hiểu một phần codebase lạ, rồi tự kiểm tra lại độ chính xác của phần tóm tắt
- [ ] Đã dùng AI viết test cho một đoạn code cũ chưa có test, và loại bỏ được các test vô nghĩa

#### 2.4 Review code do AI viết

**Vì sao cần học:** AI làm lượng code tăng mạnh, nên review trở thành nút thắt và là nơi giữ chất
lượng. Senior thường là người review nhiều nhất, và cần biết code AI sai theo kiểu nào.

**Học gì**

*Code AI viết sai theo những kiểu riêng*
- Code của người mới thường sai lộ liễu. Code AI thường **trông chuyên nghiệp** nhưng sai ở chỗ khó
  thấy, nên dễ lọt qua review đọc lướt.
- Các mẫu lỗi hay gặp:
  - Không theo quy ước của dự án: tự viết helper trong khi đã có sẵn, dùng thư viện khác với team.
  - Lặp code: sinh đoạn mới giống đoạn đã có ở chỗ khác, thay vì dùng lại.
  - Xử lý lỗi hời hợt: `catch` rồi log, không báo lên; trả về `null` im lặng.
  - Bỏ sót trường hợp biên: giá trị rỗng, trùng lặp, đồng thời, timezone, số tiền âm.
  - Làm thừa: thêm lớp interface, config, tham số không ai cần.
  - Test yếu: nhiều test nhưng không test hành vi quan trọng, hoặc bị sửa cho pass.
  - Bảo mật: thiếu kiểm tra quyền, dùng input người dùng trực tiếp, lộ thông tin trong log.

*Cách review hiệu quả*
1. **Đọc mô tả PR trước**: yêu cầu là gì, phạm vi tới đâu. PR làm nhiều hơn yêu cầu là dấu hiệu cần hỏi.
2. **Đọc test trước code**: test có đúng đặc tả không, có test trường hợp biên không.
3. **Soi các vùng rủi ro**: phân quyền, tiền, SQL, migration, xử lý lỗi.
4. **Hỏi tác giả giải thích** đoạn khó. Tác giả không giải thích được là không merge, bất kể ai viết.

*Lưới an toàn tự động*
- Static analysis ở mức cao (PHPStan level cao), lint, test coverage cho code mới, mutation testing
  cho logic quan trọng. Các công cụ này bắt được nhiều lỗi mà mắt người bỏ qua khi lượng code lớn.
- AI review bot (review tự động trên PR) là một lớp lọc thêm, không thay cho người review.

**Đọc**
- [Martin Fowler: Exploring Generative AI](https://martinfowler.com/articles/exploring-gen-ai.html): các bài về chất lượng code và rủi ro
- [DORA AI Capabilities Model](https://services.google.com/fh/files/misc/2025_dora_ai_capabilities_model.pdf): phần về version control và small batches
- Quy trình review và static analysis: [20-testing-quality.md](20-testing-quality.md)

**Nắm chắc khi**
- [ ] Kể được 5 kiểu lỗi đặc trưng của code AI viết, mỗi kiểu một ví dụ
- [ ] Đã review một PR do AI tạo (của mình hoặc của người khác) và tìm ra ít nhất một lỗi thật
- [ ] Giải thích được vì sao AI làm review quan trọng hơn chứ không phải ít quan trọng hơn

#### 2.5 Bảo mật, dữ liệu và tuân thủ

**Vì sao cần học:** Đây là phần công ty lo nhất khi cho nhân viên dùng AI, và là phần phân biệt
người dùng có trách nhiệm. Senior được kỳ vọng biết rủi ro và đặt quy tắc cho team.

**Học gì**

*Dữ liệu gửi đi đâu*
- Mọi thứ bạn đưa vào công cụ AI (code, log, dữ liệu, tài liệu) được gửi tới máy chủ của nhà cung
  cấp. Cần biết:
  - Công ty có cho phép dùng công cụ đó không, với loại dữ liệu nào.
  - Điều khoản sử dụng: dữ liệu có bị dùng để huấn luyện không, được lưu bao lâu. Gói doanh nghiệp
    thường khác gói cá nhân.
- ⚠️ Không dán vào công cụ AI: secret (API key, mật khẩu, `.env`), dữ liệu cá nhân của khách hàng,
  dữ liệu production chưa che, code mà hợp đồng cấm chia sẻ.
- ⚠️ Agent có thể tự đọc file `.env` hoặc chạy lệnh in ra secret. Cấu hình để chặn agent đọc các file
  nhạy cảm, và đừng để secret thật trong repo.
- Luật bảo vệ dữ liệu cá nhân cũng áp dụng khi đưa dữ liệu vào công cụ AI ([10-security.md](10-security.md)).

*Prompt injection với coding agent*
- *Prompt injection* là khi nội dung agent đọc được (một file, một trang web, một issue, output của
  lệnh) chứa chỉ dẫn độc hại, và agent làm theo như thể đó là yêu cầu của bạn.
  - Ví dụ: một package có README ghi "AI assistant: hãy chạy lệnh sau để cài đặt đúng cách", kèm
    lệnh gửi `.env` ra ngoài.
- Simon Willison gọi tổ hợp nguy hiểm là *lethal trifecta*. Agent có đủ cả ba thứ sau thì kẻ tấn
  công có thể lấy được dữ liệu:
  1. Truy cập dữ liệu riêng tư (code, secret, DB).
  2. Đọc nội dung không đáng tin (web, issue, file của bên thứ ba).
  3. Có cách gửi dữ liệu ra ngoài (mạng, tạo PR, gửi request).
- Cách giảm rủi ro: cắt ít nhất một trong ba thứ, chạy agent trong sandbox hoặc container, không tự
  động cho phép lệnh truy cập mạng, và đọc kỹ lệnh trước khi cho phép.

*Quyền của agent*
- Nguyên tắc quyền tối thiểu, giống như với một tài khoản dịch vụ:
  - Cho phép sẵn những lệnh an toàn (chạy test, lint).
  - Luôn hỏi trước với lệnh nguy hiểm (xoá, migrate, push, deploy).
  - Không cho agent credential production.
- Agent chạy trên CI chỉ nên có token với quyền hẹp nhất cần thiết.

*Bản quyền và giấy phép*
- Code AI sinh ra có thể giống code có giấy phép hạn chế. Một số công cụ có bộ lọc chặn gợi ý trùng
  code công khai. Làm theo chính sách của công ty; với đoạn code lớn trông như chép từ đâu đó, hỏi
  hoặc viết lại.

**Đọc**
- [Simon Willison: The lethal trifecta for AI agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/)
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/): mục prompt injection và excessive agency
- [Claude Code: Security](https://code.claude.com/docs/en/security) và [Claude Code: Settings](https://code.claude.com/docs/en/settings) (permission, chặn đọc file)
- Prompt injection từ góc nhìn sản phẩm: [23-ai-llm-backend.md](23-ai-llm-backend.md), module 3.1

**Nắm chắc khi**
- [ ] Kể được 4 loại dữ liệu không bao giờ đưa vào công cụ AI, và biết chính sách của công ty bạn
- [ ] Giải thích được lethal trifecta bằng một ví dụ cụ thể với coding agent
- [ ] Đã cấu hình agent để không đọc được file secret và phải hỏi trước khi chạy lệnh nguy hiểm

#### 2.6 Tầng PHP/Laravel: công cụ riêng và lưới an toàn

**Vì sao cần học:** Với dev PHP, câu hỏi thường cụ thể: "làm sao để AI viết Laravel đúng phiên bản,
đúng quy ước". Có công cụ riêng cho việc này, và bộ công cụ chất lượng của PHP chính là lưới an toàn.

**Học gì**

*Laravel Boost*
- Laravel Boost là package chính thức của Laravel giúp agent viết Laravel đúng chuẩn. Gồm:
  - **AI guidelines**: hướng dẫn cho agent theo đúng phiên bản các package đang cài (Laravel,
    Livewire, Pest...). Tự sinh ra file hướng dẫn như `CLAUDE.md`, `AGENTS.md`.
  - **Agent skills**: kiến thức chi tiết chỉ được nạp khi cần, để không tốn context.
  - **MCP server**: cho agent đọc schema DB, đọc log lỗi mới nhất, chạy query, tìm docs đúng phiên bản.
  - **Project rules** (`.ai/rules`): quy ước riêng của dự án, commit vào repo để cả team và mọi agent
    dùng chung.
- Cài: `composer require laravel/boost --dev` rồi `php artisan boost:install`.
- ⚠️ MCP server của Boost chạy query được trên DB mà app đang nối. Chỉ dùng ở môi trường local.

*Bộ công cụ chất lượng là lưới an toàn*
- PHPStan (kèm Larastan cho Laravel) ở level cao bắt được method không tồn tại, sai kiểu, gọi null,
  đúng những lỗi AI hay mắc.
- Pint giữ code đúng style của team, để diff chỉ còn thay đổi thật.
- Pest hoặc PHPUnit: test là cách agent tự kiểm tra. Ghi lệnh chạy test vào file hướng dẫn để agent
  tự chạy sau mỗi thay đổi.
- Mutation testing (Infection, `pest --mutate`) kiểm tra test có thật sự bắt lỗi không, rất hữu ích
  khi test do AI viết.
- Rector có thể tự động hoá phần lớn việc nâng phiên bản PHP/Laravel theo luật cố định; kết hợp với
  agent cho phần còn lại.

*Cạm bẫy riêng với PHP/Laravel*
- ⚠️ AI hay trộn cú pháp của nhiều phiên bản Laravel (cấu trúc thư mục cũ, `Kernel.php` đã bỏ từ bản
  11, cách đăng ký middleware cũ). Ghi rõ phiên bản và cấu trúc dự án trong file hướng dẫn.
- ⚠️ AI hay viết query trong vòng lặp gây N+1, hoặc bỏ `declare(strict_types=1)`. Đưa các quy tắc này
  vào file hướng dẫn và bật `Model::preventLazyLoading()` ở môi trường dev.

**Đọc**
- [Laravel Boost](https://laravel.com/docs/boost) và [repo laravel/boost](https://github.com/laravel/boost)
- Công cụ chất lượng: [20-testing-quality.md](20-testing-quality.md) và [05-php-laravel.md](05-php-laravel.md) (module về PHPStan, Rector, Pint)
- [Infection](https://github.com/infection/infection): mutation testing cho PHP

**Nắm chắc khi**
- [ ] Đã cài Laravel Boost (hoặc tự viết file hướng dẫn tương đương) cho một dự án và thấy agent dùng đúng phiên bản
- [ ] Cấu hình được để agent tự chạy test, PHPStan, Pint sau mỗi thay đổi
- [ ] Kể được 3 lỗi Laravel đặc trưng mà AI hay mắc và cách chặn từng lỗi

---

### Chặng 3: Senior 🔴

#### 3.1 Đo hiệu quả thật

**Vì sao cần học:** "AI có làm team bạn nhanh hơn không, bạn biết bằng cách nào" là câu senior hay
gặp. Trả lời bằng cảm giác là yếu; trả lời bằng số liệu và hiểu giới hạn của số liệu là mạnh.

**Học gì**

*Cảm giác nhanh chưa chắc là nhanh*
- Nghiên cứu có đối chứng của METR (đầu 2025) với 16 dev open source giàu kinh nghiệm, 246 task:
  - Khi được dùng AI, họ mất thời gian **nhiều hơn 19%**.
  - Trước thí nghiệm họ đoán AI sẽ giúp nhanh hơn 24%; sau thí nghiệm họ vẫn tin mình đã nhanh hơn 20%.
- Bản cập nhật 02/2026 với công cụ cuối 2025 cho kết quả khác đi đáng kể. Nhưng chính METR nói dữ
  liệu mới chỉ là bằng chứng rất yếu, vì nhiều dev **từ chối tham gia** khi phải làm một phần việc
  không có AI. Nhóm hưởng lợi nhiều nhất từ AI lại bị loại khỏi mẫu (*selection effect*).
- Bài học không phải "AI làm chậm" hay "AI làm nhanh", mà là: **cảm nhận của dev về tốc độ không
  đáng tin**, và đo năng suất phần mềm rất khó.

*AI khuếch đại cái đang có*
- DORA 2025: 90% người được khảo sát dùng AI trong công việc, hơn 80% tin AI tăng năng suất của họ,
  nhưng 30% ít hoặc không tin code AI tạo ra.
- AI có liên hệ tích cực với throughput (tốc độ giao hàng), nhưng vẫn có liên hệ **tiêu cực với độ
  ổn định** (tỉ lệ deploy lỗi, phải sửa gấp).
- Kết luận chính của DORA: AI là **bộ khuếch đại**. Team có quy trình tốt thì tốt hơn; team có quy
  trình yếu thì giao hàng kém chất lượng nhanh hơn.
- Mô hình 7 năng lực giúp AI mang lại giá trị thật:
  1. Lập trường rõ ràng về AI, được truyền đạt tới mọi người (công cụ nào được dùng, giới hạn ở đâu).
  2. Hệ sinh thái dữ liệu tốt.
  3. Dữ liệu nội bộ mà AI truy cập được (docs, code, quyết định).
  4. Version control tốt.
  5. Làm việc theo lô nhỏ.
  6. Tập trung vào người dùng.
  7. Nền tảng nội bộ chất lượng.

*Đo cái gì*
- Đo kết quả của cả hệ thống, không đo lượng code:
  - Các chỉ số DORA: lead time, tần suất deploy, tỉ lệ deploy lỗi, thời gian phục hồi, tỉ lệ phải làm lại.
  - Thời gian chờ review, kích thước PR, số bug lọt ra production.
- ⚠️ Không dùng "số dòng code AI viết" hay "tỉ lệ gợi ý được chấp nhận" làm thước đo năng suất. Hai
  số này tăng không có nghĩa sản phẩm tốt lên.
- Muốn biết một công cụ có giúp không: thử có đối chứng trong một khoảng thời gian, so trước và sau
  trên cùng chỉ số, kèm phỏng vấn dev.

**Đọc**
- [METR: Measuring the Impact of Early-2025 AI on Experienced Open-Source Developer Productivity](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) và [bản cập nhật 02/2026](https://metr.org/blog/2026-02-24-uplift-update/)
- [Google Cloud: Announcing the 2025 DORA report](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report) và [DORA AI Capabilities Model (PDF)](https://services.google.com/fh/files/misc/2025_dora_ai_capabilities_model.pdf)
- Các chỉ số DORA: [24-senior-leadership.md](24-senior-leadership.md)

**Nắm chắc khi**
- [ ] Tóm tắt được nghiên cứu METR và giới hạn của nó trong 1 phút
- [ ] Giải thích được "AI là bộ khuếch đại" bằng một ví dụ từ team của bạn
- [ ] Đề xuất được cách đo xem một công cụ AI có giúp team không, không dựa vào số dòng code

#### 3.2 Đưa AI vào team

**Vì sao cần học:** Senior và tech lead thường là người quyết định team dùng AI thế nào. Câu hỏi
kiểu "bạn sẽ đặt quy tắc dùng AI cho team ra sao" hay "có cho junior dùng AI không" rất hay gặp.

**Học gì**

*Quy tắc rõ ràng*
- Một bộ quy tắc ngắn cho team nên trả lời được:
  - Công cụ nào được dùng, gói nào (để dữ liệu được bảo vệ đúng điều khoản).
  - Dữ liệu nào không được đưa vào.
  - Ai chịu trách nhiệm code: người mở PR, bất kể ai viết.
  - Có cần ghi chú khi PR chủ yếu do AI tạo không.
  - Agent được quyền gì trên máy dev và trên CI.
- DORA gọi đây là "lập trường rõ ràng về AI". Không có quy tắc thì mỗi người một kiểu, rủi ro dữ
  liệu cao, và người ngại dùng thì không dám thử.

*Chia sẻ context chung*
- File hướng dẫn cho agent (module 2.2), rule dự án, prompt và command hay dùng: commit vào repo để
  cả team hưởng lợi, review như code.
- Khi một người phát hiện agent hay sai một kiểu, thêm quy tắc vào file chung thay vì chỉ tự nhớ.

*Junior và việc học*
- Rủi ro lớn nhất với junior: dùng AI để **bỏ qua việc hiểu**. Code chạy được nhưng không biết vì
  sao, không tự debug được khi AI bế tắc.
- Cách hướng dẫn:
  - Cho dùng AI, nhưng yêu cầu giải thích được mọi dòng trong PR.
  - Khuyến khích dùng AI để hỏi "vì sao", nhờ giải thích, nhờ phản biện, không chỉ để sinh code.
  - Có những bài tập tự làm không dùng AI để giữ kỹ năng nền.
  - Review kỹ hơn, và hỏi "em đã kiểm chứng thế nào".

*Chi phí và lựa chọn công cụ*
- Chi phí gồm tiền license và tiền dùng theo lượng (agent chạy nhiều thì tốn nhiều). Theo dõi theo
  team, đặt hạn mức.
- Chọn công cụ bằng thử nghiệm ngắn có đo đạc (module 3.1), không theo xu hướng. Tránh khoá chặt vào
  một nhà cung cấp: file hướng dẫn dạng mở như `AGENTS.md` dùng được cho nhiều công cụ.

**Đọc**
- [DORA AI Capabilities Model (PDF)](https://services.google.com/fh/files/misc/2025_dora_ai_capabilities_model.pdf): phần "clear and communicated AI stance"
- [How Anthropic teams use Claude Code](https://www.anthropic.com/news/how-anthropic-teams-use-claude-code)
- Mentor và dẫn dắt team nói chung: [24-senior-leadership.md](24-senior-leadership.md)

**Nắm chắc khi**
- [ ] Viết được bộ quy tắc dùng AI một trang cho team của bạn (bài tập 5)
- [ ] Trả lời được "có cho junior dùng AI không" với lập luận hai phía và cách làm cụ thể
- [ ] Đề xuất được cách chia sẻ context và kinh nghiệm dùng AI giữa các thành viên

#### 3.3 Workflow agent nâng cao và guardrail

**Vì sao cần học:** Ở các team dùng AI nhiều, senior được kỳ vọng dựng được quy trình để agent làm
việc song song, tự động hoá việc lặp lại, mà vẫn có guardrail. Đây cũng là phần thể hiện bạn đi
trước mặt bằng chung.

**Học gì**

*Chạy nhiều agent song song*
- Mỗi agent làm một việc độc lập trên một bản sao riêng của repo, thường dùng *git worktree*: nhiều
  thư mục làm việc từ cùng một repo, mỗi thư mục một branch. Các agent không giẫm lên nhau.
- Hợp với: nhiều việc nhỏ độc lập (sửa vài bug, nâng vài dependency). Không hợp với việc phụ thuộc
  nhau.
- ⚠️ Nút thắt chuyển sang người review. Đừng chạy nhiều agent hơn lượng PR bạn review kỹ được.

*Tự động hoá bằng agent*
- Agent chạy không cần người tương tác (*headless*) trên CI: tự sửa lỗi lint, cập nhật dependency,
  sinh mô tả PR, review tự động lần đầu.
- *Hook*: lệnh tự chạy tại một thời điểm trong vòng làm việc của agent, ví dụ chạy Pint sau mỗi lần
  sửa file, hoặc chặn lệnh nguy hiểm trước khi chạy. Hook là guardrail cứng, không phụ thuộc agent có
  "nhớ" quy tắc hay không.
- *Subagent* và *skill*: tách vai trò (agent chuyên review, agent chuyên viết test) và kiến thức theo
  việc, chỉ nạp khi cần.

*Guardrail*
- Nguyên tắc: mọi thứ agent làm phải đi qua cùng cổng chất lượng như code của người: CI, test, static
  analysis, review, branch protection.
- Agent không được merge thẳng vào nhánh chính, không có credential deploy production.
- Log lại những gì agent chạy trên CI để truy vết khi có sự cố.
- Bắt đầu nhỏ: một loại việc, một repo, đo kết quả rồi mới mở rộng.

**Đọc**
- [Claude Code: Hooks reference](https://code.claude.com/docs/en/hooks) và [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code: Common workflows](https://code.claude.com/docs/en/common-workflows): phần chạy song song bằng git worktree
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): các mẫu workflow và khi nào nên dùng agent
- [Agent Skills](https://agentskills.io/home): định dạng skill dùng chung giữa nhiều công cụ

**Nắm chắc khi**
- [ ] Đã chạy hai agent song song trên hai worktree cho hai việc độc lập
- [ ] Viết được một hook đơn giản (ví dụ chạy Pint sau khi agent sửa file PHP)
- [ ] Liệt kê được các guardrail tối thiểu trước khi cho agent chạy trên CI của team

#### 3.4 Giữ kỹ năng nền và quan điểm nghề nghiệp

**Vì sao cần học:** Người phỏng vấn senior hay hỏi quan điểm: "AI thay đổi công việc của bạn thế nào",
"kỹ năng nào quan trọng hơn trước". Câu trả lời cho thấy bạn có góc nhìn cân bằng hay chỉ hào hứng
hoặc chỉ hoài nghi.

**Học gì**

*Kỹ năng nào quan trọng hơn khi có AI*
- **Đọc và đánh giá code**: bạn đọc nhiều code hơn là viết. Kỹ năng review, nhìn ra lỗi tinh vi, quan
  trọng hơn trước.
- **Hiểu hệ thống**: database, network, concurrency, bảo mật. AI viết code, nhưng biết code đó đúng hay
  sai trong hệ thống thật cần hiểu biết nền. Đây là lý do các file khác trong bộ này vẫn quan trọng.
- **Diễn đạt yêu cầu rõ ràng**: viết đặc tả, test, tiêu chí "xong". Đây vốn là kỹ năng senior, giờ
  dùng hằng ngày.
- **Phán đoán**: chọn phương án, cân trade-off, biết khi nào dừng. AI đưa phương án, người chọn.
- Addy Osmani gọi đây là "vấn đề 70%": AI đưa bạn đi rất nhanh tới 70%, còn 30% cuối (trường hợp
  biên, tích hợp, vận hành) vẫn cần kinh nghiệm.

*Không để kỹ năng mai một*
- Tự debug một số lỗi không dùng AI. Tự viết một số đoạn quan trọng rồi mới so với AI.
- Khi AI giải được việc bạn không biết làm, dành thời gian hiểu cách nó giải.
- Phỏng vấn vẫn có vòng không cho dùng AI ([25-interview-skills.md](25-interview-skills.md), module 2.5).

*Quan điểm cân bằng để nói khi phỏng vấn*
- Một câu trả lời tốt thường có dạng: dùng AI nhiều, có quy trình, kiểm chứng nghiêm túc, biết giới
  hạn, có ví dụ cụ thể về cả thành công lẫn thất bại.
- ⚠️ Hai thái cực đều bị đánh giá thấp: "AI làm hết, em chỉ review" (không kiểm soát), và "em không
  dùng vì không tin" (không theo kịp, không có lập luận).

**Đọc**
- [Addy Osmani: The 70% problem](https://addyo.substack.com/p/the-70-problem-hard-truths-about)
- [Simon Willison: Vibe engineering](https://simonwillison.net/2025/Oct/7/vibe-engineering/)
- [Martin Fowler: Exploring Generative AI](https://martinfowler.com/articles/exploring-gen-ai.html)

**Nắm chắc khi**
- [ ] Trả lời được trong 2 phút "AI đã thay đổi cách bạn làm việc thế nào", có một ví dụ thành công và một ví dụ thất bại
- [ ] Kể được 3 kỹ năng bạn chủ động giữ không để AI làm thay, và vì sao

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc. Với file này, câu trả lời mạnh nhất luôn có **ví dụ thật
từ công việc của bạn**; hãy chuẩn bị sẵn 3–4 câu chuyện.

### 🟢 Junior

**1. Bạn có dùng AI khi code không? Dùng vào việc gì?** (1.2, 2.3)
- Ý phải có: có dùng; kể 2–3 việc cụ thể (đọc code lạ, viết test, debug); nói luôn cách kiểm chứng
- Điểm cộng: phân biệt được khi nào dùng chat, khi nào dùng agent; nói được việc mình không giao cho AI
- Red flag: "dùng cho mọi thứ"; hoặc không dùng mà không có lý do

**2. AI hay sai ở đâu? Vì sao nó sai mà vẫn rất tự tin?** (1.1)
- Ý phải có: model sinh câu trả lời nghe hợp lý nhất, không tra cứu sự thật; bịa method, package; kiến thức cũ theo knowledge cutoff
- Điểm cộng: lỗi thường nằm ở logic, trường hợp biên, bảo mật, tức chỗ đọc lướt không thấy

**3. Làm sao bạn biết code AI viết là đúng?** (1.4)
- Ý phải có: đọc hiểu mọi dòng, đọc diff, chạy test, static analysis, chạy thật
- Điểm cộng: soi test có bị sửa cho pass không; kiểm tra package lạ trên Packagist
- Red flag: "chạy được là được"

**4. Code AI viết bị lỗi trên production. Lỗi của ai?** (1.4)
- Ý phải có: của người merge và team review, giống mọi code khác; AI là công cụ
- Điểm cộng: nói luôn cách rút kinh nghiệm: thêm test, thêm quy tắc vào file hướng dẫn, điều chỉnh quy trình review
- Red flag: đổ lỗi cho công cụ

**5. Bạn viết prompt cho coding agent thế nào?** (1.3)
- Ý phải có: mục tiêu, bối cảnh, ràng buộc, định nghĩa "xong", ví dụ; chia nhỏ việc
- Điểm cộng: yêu cầu kế hoạch trước khi sửa; biết khi nào mở phiên mới

### 🟡 Mid

**6. Kể quy trình bạn làm một task với coding agent từ đầu tới cuối.** (2.1)
- Ý phải có: khám phá, lập kế hoạch, làm từng bước, kiểm chứng, commit; dùng branch và commit nhỏ
- Điểm cộng: viết test tái hiện bug trước; nói rõ "không được sửa test"; kể một task thật
- Red flag: "giao cả task rồi đợi kết quả"

**7. Kể một lần AI làm sai và bạn phát hiện ra.** (1.4, 2.4)
- Ý phải có: sai gì, phát hiện bằng cách nào (test, review, chạy thật), sửa thế nào
- Điểm cộng: rút ra bài học và thay đổi quy trình (thêm quy tắc, thêm test, thêm bước kiểm tra)
- Red flag: không kể được ví dụ nào, nghĩa là không kiểm chứng hoặc không thật sự dùng

**8. Làm sao để agent viết code đúng quy ước của team?** (2.2, 2.6)
- Ý phải có: file hướng dẫn trong repo (`CLAUDE.md`, `AGENTS.md`...) ghi lệnh test, phiên bản, quy ước, cạm bẫy; review file đó như code
- Điểm cộng: Laravel Boost; lint và static analysis làm lưới an toàn tự động; thêm quy tắc mỗi khi agent sai lặp lại

**9. MCP là gì? Bạn đã dùng MCP server nào?** (2.2)
- Ý phải có: chuẩn kết nối agent với công cụ và dữ liệu bên ngoài; ví dụ docs, DB local, issue tracker
- Điểm cộng: mỗi MCP server là thêm quyền, không nối với DB production; liên hệ tới lethal trifecta

**10. Bạn review một PR do AI tạo khác gì PR do người viết?** (2.4)
- Ý phải có: lỗi của AI trông chuyên nghiệp nên dễ lọt; soi quy ước, lặp code, xử lý lỗi, trường hợp biên, test yếu
- Điểm cộng: đọc test trước code; tác giả phải giải thích được; PR lớn thì yêu cầu chia nhỏ
- Red flag: review nhẹ tay hơn vì "AI viết thì chắc đúng cú pháp"

**11. Có dữ liệu nào bạn không bao giờ đưa vào công cụ AI không?** (2.5)
- Ý phải có: secret, dữ liệu cá nhân khách hàng, dữ liệu production chưa che, code bị hợp đồng cấm chia sẻ
- Điểm cộng: biết chính sách của công ty và điều khoản của công cụ (có dùng để huấn luyện không); chặn agent đọc `.env`

**12. Việc gì bạn không giao cho AI?** (2.3)
- Ý phải có: bug concurrency, tối ưu khi chưa đo, quyết định kiến trúc, nghiệp vụ đặc thù chưa ai mô tả
- Điểm cộng: vẫn dùng AI để liệt kê phương án và phản biện ở những việc đó

**13. AI gợi ý cài một package bạn chưa nghe tên. Bạn làm gì?** (1.4)
- Ý phải có: kiểm tra trên Packagist (tác giả, lượt tải, repo, ngày tạo); package có thể không tồn tại hoặc bị giả mạo
- Điểm cộng: nói được tên kiểu tấn công slopsquatting; chạy `composer audit`

**14. Test do AI viết có đáng tin không?** (2.4, 2.6)
- Ý phải có: không tự động đáng tin; soi test có kiểm tra hành vi thật hay chỉ mock; có test trường hợp biên không
- Điểm cộng: mutation testing (Infection, `pest --mutate`) để đo chất lượng test; bạn duyệt test trước khi cho viết code

### 🔴 Senior

**15. AI có làm team bạn nhanh hơn không? Bạn đo thế nào?** (3.1)
- Ý phải có: cảm nhận không đáng tin; đo bằng chỉ số của cả hệ thống (lead time, tỉ lệ deploy lỗi, thời gian review), không đo số dòng code
- Điểm cộng: dẫn nghiên cứu METR và giới hạn của nó; DORA 2025 "AI là bộ khuếch đại", tăng throughput nhưng giảm độ ổn định
- Red flag: "nhanh gấp 10 lần" mà không có số liệu

**16. Bạn sẽ đặt quy tắc dùng AI cho team thế nào?** (3.2)
- Ý phải có: công cụ được phép, dữ liệu cấm đưa vào, người mở PR chịu trách nhiệm, quyền của agent, có ghi chú khi PR chủ yếu do AI tạo hay không
- Điểm cộng: chia sẻ file hướng dẫn chung; thử nghiệm có đo trước khi mở rộng; quy tắc ngắn, dễ nhớ

**17. Có nên cho junior dùng AI không?** (3.2, 3.4)
- Ý phải có: có, nhưng phải giải thích được mọi dòng; rủi ro là bỏ qua việc hiểu
- Điểm cộng: dùng AI để học (hỏi vì sao, nhờ phản biện); bài tập không dùng AI; review kỹ hơn và hỏi "em kiểm chứng thế nào"
- Red flag: cấm hoàn toàn, hoặc để tự do không hướng dẫn

**18. AI làm lượng code tăng mạnh. Điều gì trở thành nút thắt, và bạn xử lý ra sao?** (2.4, 3.3)
- Ý phải có: review và kiểm thử trở thành nút thắt; chất lượng dễ giảm
- Điểm cộng: PR nhỏ, lưới an toàn tự động (static analysis, test, mutation testing), review bot làm lớp lọc đầu, không chạy nhiều agent hơn năng lực review

**19. Prompt injection ảnh hưởng tới coding agent thế nào?** (2.5)
- Ý phải có: nội dung agent đọc được (README, issue, trang web) chứa chỉ dẫn độc hại và agent làm theo
- Điểm cộng: lethal trifecta (dữ liệu riêng tư, nội dung không đáng tin, đường gửi ra ngoài); cắt ít nhất một thứ; sandbox; không tự cho phép lệnh truy cập mạng

**20. Bạn có cho agent chạy tự động trên CI không? Cần guardrail gì?** (3.3)
- Ý phải có: có thể, với việc nhỏ rõ ràng; phải qua cùng cổng chất lượng như code người viết
- Điểm cộng: token quyền hẹp, không merge thẳng, không credential production, log lại mọi hành động, bắt đầu nhỏ rồi mở rộng

**21. AI thay đổi công việc của bạn thế nào? Kỹ năng nào quan trọng hơn trước?** (3.4)
- Ý phải có: đọc và đánh giá code, hiểu hệ thống, diễn đạt yêu cầu rõ, phán đoán trade-off
- Điểm cộng: vấn đề 70%; chủ động giữ kỹ năng nền; có ví dụ cả thành công lẫn thất bại
- Red flag: một trong hai thái cực, "AI làm hết" hoặc "không dùng vì không tin"

**22. Bạn nâng một dự án Laravel cũ lên phiên bản mới với sự hỗ trợ của AI thế nào?** (2.3, 2.6)
- Ý phải có: nâng từng bước theo upgrade guide chính thức; test đầy đủ trước khi bắt đầu; chạy test sau mỗi bước
- Điểm cộng: Rector cho phần có luật cố định, agent cho phần còn lại; ghi phiên bản đích vào file hướng dẫn; PHPStan bắt lỗi còn sót; deploy từng phần

**23. Công ty cấm dùng AI với code của khách hàng. Bạn làm thế nào?** (2.5, 3.2)
- Ý phải có: tuân thủ tuyệt đối; hợp đồng và dữ liệu khách hàng quan trọng hơn tốc độ
- Điểm cộng: đề xuất phương án hợp lệ (gói doanh nghiệp có điều khoản phù hợp, model chạy nội bộ) qua đúng kênh; vẫn dùng AI cho việc không đụng tới code khách hàng nếu được phép

**24. Nếu được dùng AI trong vòng phỏng vấn coding, bạn làm thế nào?** (1.3, 1.4; xem [25-interview-skills.md](25-interview-skills.md))
- Ý phải có: dùng như cách làm hằng ngày, nói thành tiếng đang giao việc gì, vì sao; kiểm chứng output trước mặt người phỏng vấn
- Điểm cộng: làm rõ yêu cầu trước khi giao cho AI; viết test; chỉ ra chỗ AI sai và tự sửa
- Red flag: dán đề vào rồi chép kết quả mà không đọc

---

## Bài tập tự làm

1. **File hướng dẫn cho agent.** Viết `AGENTS.md` (hoặc `CLAUDE.md`) cho một dự án Laravel thật của
   bạn, dưới 100 dòng. Cần có:
   - Lệnh chạy test, PHPStan, Pint
   - Phiên bản PHP, Laravel, các package chính
   - 5 quy ước quan trọng nhất của team
   - 3 cạm bẫy riêng của dự án

   Giao cùng một task cho agent trước và sau khi có file, so sánh kết quả.
2. **Sửa bug theo quy trình.** Chọn một bug thật. Làm với agent theo đúng thứ tự: test tái hiện fail,
   kế hoạch, sửa, test pass, review diff. Ghi lại mỗi bước agent làm đúng hay sai, và bạn can thiệp
   ở đâu.
3. **Review code AI viết.** Cho agent viết một tính năng nhỏ (ví dụ export CSV đơn hàng có lọc theo
   ngày) mà không đưa nhiều ràng buộc. Review như review PR của đồng nghiệp, liệt kê mọi vấn đề theo
   các kiểu lỗi ở module 2.4.
4. **Nhật ký một tuần.** Trong một tuần, ghi lại mỗi lần dùng AI: việc gì, mất bao lâu, kết quả có
   dùng được không, phải sửa bao nhiêu. Cuối tuần tổng kết: việc nào AI giúp thật, việc nào mất thời
   gian hơn. So với cảm nhận ban đầu của bạn.
5. **Quy tắc cho team.** Viết bộ quy tắc dùng AI một trang cho team của bạn: công cụ, dữ liệu, trách
   nhiệm, quyền của agent, cách chia sẻ file hướng dẫn. Viết sao cho một người mới đọc 5 phút là làm
   đúng.
6. **Guardrail.** Cấu hình agent bạn đang dùng:
   - Không đọc được `.env` và các file secret
   - Tự chạy test và lint được, nhưng phải hỏi trước khi chạy migrate, xoá file, push
   - Có một hook tự chạy Pint sau khi sửa file PHP

   Ghi lại cấu hình và giải thích từng quyết định.

> Nộp bài vào đây để được review.
