# 20. Testing và chất lượng code

> [← Mục lục](README.md) · Trọng tâm: chiến lược test, test double, test isolation, flaky test, test những thứ khó, **testing trong PHP/Laravel** (PHPUnit, Pest, fakes), code review, static analysis, tech debt, Git và quy trình làm việc nhóm.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn.

Mục tiêu của file: **nói được** về cách mình đảm bảo chất lượng, dù dự án hiện tại có test
hay không. Người phỏng vấn không chấm số test bạn từng viết; họ chấm việc bạn hiểu test để
làm gì, tốn gì, và khi nào không đáng.

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
| [*Software Engineering at Google*](https://abseil.io/resources/swe-book) (Winters, Manshreck, Wright) | Sách online miễn phí | Ch.9 code review, ch.11–14 testing (tổng quan, unit, test double, test lớn). Góc nhìn ở quy mô lớn |
| [Martin Fowler: The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) | Bài dài | Các loại test, pyramid, contract test, có ví dụ code |
| *Working Effectively with Legacy Code* (Michael Feathers) | Sách | Seam, characterization test, cách đưa test vào code cũ. Đọc phần I và các chương về seam |
| [Laravel: Testing](https://laravel.com/docs/testing) | Official docs | HTTP test, database test, fakes, mocking, parallel test |
| [PHPUnit Manual](https://docs.phpunit.de/) | Official docs | Bản 13.x hiện tại: attribute, test double, data provider, coverage |
| [Pest docs](https://pestphp.com/docs/installation) | Official docs | Cú pháp Pest, browser testing, mutation testing tích hợp |
| [Pro Git](https://git-scm.com/book/en/v2) | Sách online miễn phí | Branching, rebase, công cụ nâng cao |

---

## Lộ trình tổng

| Chặng | Module | Mục tiêu | Thời gian gợi ý |
|---|---|---|---|
| **1. Nền** 🟢 | 1.1–1.4 | Phân biệt loại test, viết test tốt, dùng Git hằng ngày không sợ, review PR có hệ thống | 3–4 ngày |
| **2. Làm chủ** 🟡 | 2.1–2.6 | Cô lập test và DB, test thứ khó, làm chủ công cụ PHP/Laravel, contract test, static analysis trong CI, Git nâng cao | 6–8 ngày |
| **3. Senior** 🔴 | 3.1–3.4 | Chọn phương pháp, đo chất lượng test thật sự, test concurrency, xử lý legacy và tech debt | 4–5 ngày |

Với senior, câu hỏi testing hiếm khi là "cú pháp mock thế nào". Thường là "chọn chiến lược
test cho service X", "codebase không có test thì bắt đầu từ đâu", "làm sao thuyết phục team".

---

## Phần 1: Lộ trình kiến thức

### Chặng 1: Nền 🟢

#### 1.1 Các loại test và chiến lược

**Vì sao cần học:** Trong dự án Laravel thật, thời gian viết test luôn có hạn, nên câu hỏi thật
là "viết loại test nào, cho chỗ nào". Người phỏng vấn hay mở đầu bằng "unit khác integration thế
nào", rồi hỏi tiếp "vậy với service của bạn, bạn viết loại nào nhiều hơn, vì sao". Trả lời
"theo test pyramid" mà không nói được lý do là điểm trừ.

**Học gì**

*Các loại test*
- Mỗi loại test khác nhau ở chỗ nó kiểm bao nhiêu phần của hệ thống cùng lúc. Kiểm càng nhiều
  thì càng giống thật, nhưng càng chậm và càng khó chỉ ra chỗ hỏng.
- *Unit test* kiểm một hàm hoặc một class. Các thứ nó phụ thuộc (DB, API, mail) được thay bằng
  đồ giả, gọi chung là *test double* (module 1.2).
  - Ví dụ: test hàm `calculateDiscount()` với giỏ hàng tạo sẵn trong code, không đụng DB.
  - "Unit" là một hành vi, không nhất thiết là một class. Một hành vi có thể đi qua 3 class.
- *Integration test* kiểm code của bạn chạy cùng thành phần thật: DB, cache, queue.
  - Ví dụ: gọi repository lưu đơn vào MySQL thật rồi đọc lại.
  - Bắt được bug SQL, bug *mapping* (chuyển dữ liệu giữa dòng DB và object), bug transaction.
- *E2E test* (end-to-end) kiểm cả hệ thống từ ngoài vào, qua API hoặc giao diện, giống người dùng.
- Bảng tóm tắt:

  | Loại | Kiểm tra | Tốc độ | Ghi chú |
  |---|---|---|---|
  | Unit | một hàm/class, phụ thuộc thay bằng double | ms | "unit" là một hành vi, không nhất thiết là một class |
  | Integration | code + thành phần thật (DB, cache, queue) | giây | bắt bug SQL, mapping, transaction |
  | E2E | cả hệ thống từ API/UI | chậm | chỉ cho vài luồng quan trọng nhất (đăng ký, thanh toán) |
  | Contract | thoả thuận request/response giữa hai service | nhanh | thay cho e2e xuyên nhiều service (module 2.4) |
  | Smoke | hệ thống sống và luồng chính chạy được | nhanh | chạy ngay sau deploy |
  | Regression | lỗi cũ không quay lại | tuỳ | mỗi bug fix kèm một test tái hiện bug |
  | Acceptance | đúng yêu cầu nghiệp vụ | tuỳ | thường viết theo Given–When–Then |

- Vài thuật ngữ trong bảng:
  - *Contract test* kiểm hai service vẫn hiểu nhau về định dạng request và response (module 2.4).
  - *Smoke test* là vài kiểm tra nhanh xem hệ thống còn sống không, chạy ngay sau deploy.
  - *Regression test* là test chứng minh một bug cũ không quay lại.
  - *Given–When–Then* là cách viết kịch bản: cho trước trạng thái gì, khi làm gì, thì kết quả
    ra sao (module 3.1).

*Test pyramid*
- *Test pyramid* (kim tự tháp test) là lời khuyên: nhiều unit test nhất, ít integration test hơn,
  ít e2e test nhất.
- Lý do:
  - Unit test nhanh, rẻ, và khi đỏ thì chỉ đúng chỗ hỏng.
  - E2E chậm và dễ *flaky*, tức lúc pass lúc fail dù code không đổi (module 2.1).
- ⚠️ Giả định ngầm của pyramid: logic nằm chủ yếu trong code thuần (tính toán, quy tắc nghiệp vụ),
  nên test code thuần là bắt được phần lớn bug.

*Testing trophy (🟡)*
- *Testing trophy* (chiếc cúp) là mô hình khác, theo thứ tự từ đáy lên: static → unit →
  **integration là phần lớn nhất** → e2e.
  - Tầng *static* là các công cụ đọc code mà không chạy nó, như type check và linter (module 2.5).
- Lập luận:
  1. Backend CRUD (tạo, đọc, sửa, xoá dữ liệu) có ít logic thuần.
  2. Bug thường nằm ở chỗ nối: câu SQL, mapping, validation, *serialization* (chuyển object
     thành JSON và ngược lại).
  3. Nếu mock DB (thay DB bằng đồ giả) thì unit test bỏ sót đúng những bug đó.
- Hai hình so sánh:
  ```
  Pyramid            Trophy
     /e2e\            [ e2e ]
    /integ.\       [ integration ]   ← phần lớn nhất
   /  unit  \         [ unit ]
                     [ static ]      ← type check, linter
  ```
- Kết luận senior: **tỉ lệ phụ thuộc vào chỗ rủi ro nằm ở đâu**, không có hình dạng đúng cho mọi
  dự án.
  - Service tính giá nhiều công thức: nhiều unit test.
  - Service CRUD admin trên Laravel: nhiều integration test (feature test có DB thật).

*Test cái gì trước khi thời gian có hạn*
- Chỗ mất tiền hoặc mất dữ liệu: thanh toán, phân quyền, migration.
- Logic nhiều nhánh và *edge case*, tức các ca ở rìa dễ bị quên:
  - Rỗng, giá trị biên, trùng, số âm, timezone.
- Chỗ từng có bug.
- ⚠️ Không đáng test:
  - Getter và setter.
  - Code của framework, vì framework đã tự test.
  - Code sắp xoá.

**Đọc**
- Martin Fowler: [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html) (đọc hết)
- Kent C. Dodds: [The Testing Trophy and Testing Classifications](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)
- *Software Engineering at Google*: [ch.11 Testing Overview](https://abseil.io/resources/swe-book/html/ch11.html) (phần test size và test scope)

**Nắm chắc khi**
- [ ] Với một service tính giá và một service CRUD admin, chọn được tỉ lệ loại test và bảo vệ lựa chọn
- [ ] Phân loại được 10 test có sẵn trong dự án của mình vào đúng cột của bảng trên
- [ ] Nói được một ca e2e là lựa chọn đúng và một ca e2e là lãng phí

#### 1.2 Viết test tốt

**Vì sao cần học:** Test viết dở còn tệ hơn không có test: refactor một dòng mà đỏ hàng chục
test, hoặc test xanh trong khi code sai. Câu "mock và stub khác nhau thế nào" gần như luôn được
hỏi, và thường bị hỏi tiếp "vậy khi nào bạn mock, khi nào không".

**Học gì**

*Test double: năm loại đồ giả*
- *Test double* là tên chung cho mọi đồ giả thay cho một phụ thuộc thật trong test, giống diễn
  viên đóng thế trong phim. Năm loại dưới đây là thuật ngữ của Gerard Meszaros:

  | Loại | Làm gì | Ví dụ |
  |---|---|---|
  | Dummy | chỉ để đủ tham số, không dùng | logger truyền vào nhưng không kiểm tra |
  | Stub | trả giá trị định sẵn | `rateProvider` luôn trả 25000 |
  | Fake | bản cài thật nhưng đơn giản | repository lưu trong map, `Mail::fake()` |
  | Spy | ghi lại cách được gọi để assert sau | đếm số email đã gửi |
  | Mock | lập trình kỳ vọng trước, fail nếu gọi sai | "phải gọi `charge()` đúng 1 lần với 100000" |

- Quan trọng hơn thuật ngữ: **stub cho input, mock/spy cho output có side effect**.
  - Input là dữ liệu code cần đọc vào, ví dụ tỉ giá. Chỉ cần stub trả sẵn một con số.
  - *Side effect* là tác động ra bên ngoài mà hàm để lại, ví dụ trừ tiền thẻ hay gửi email.
    Muốn biết nó có xảy ra không thì phải dùng mock hoặc spy để kiểm cách được gọi.

*Mock ở đâu*
- ⚠️ *Over-mocking* là mock quá nhiều. Dấu hiệu:
  - Test lặp lại từng dòng *implementation* (cách code được viết bên trong).
  - Refactor không đổi hành vi mà hàng chục test đỏ.
  - Test pass khi code sai, vì mock trả đúng thứ ta nghĩ là đúng. Ví dụ: mock repository thì
    không bao giờ bắt được câu SQL sai.
- Quy tắc thực dụng:
  - Mock ở **biên hệ thống**: API ngoài, email, clock (đồng hồ), random.
  - Dùng đồ thật hoặc fake cho những gì mình sở hữu.
- "Don't mock what you don't own" (đừng mock thứ không phải của mình): bọc thư viện ngoài bằng
  interface của mình, rồi mock interface đó.
  - Ví dụ: không mock thẳng SDK Stripe. Tạo interface `PaymentGateway`, class thật gọi Stripe,
    test thì dùng fake của `PaymentGateway`.

*Test hành vi, không test implementation*
- Assert (khẳng định kết quả) trên những thứ người ngoài nhìn thấy:
  - Giá trị trả về.
  - Trạng thái DB.
  - Event phát ra.
  - Response HTTP.
- Không assert:
  - Method private.
  - Thứ tự gọi nội bộ.
  - Số query, trừ khi đó là yêu cầu, ví dụ test chống N+1 (một vòng lặp chạy thêm một query
    cho mỗi phần tử, [03-database-sql.md](03-database-sql.md)).

*Cấu trúc và đặt tên*
- Tên test mô tả hành vi: `refund_fails_when_order_already_refunded`, không phải `testRefund2`.
- Mỗi test chia ba đoạn, gọi là *Arrange–Act–Assert* (hay Given–When–Then):
  1. Arrange: chuẩn bị dữ liệu.
  2. Act: gọi đúng một hành động.
  3. Assert: kiểm kết quả.
- Một test một hành vi. Nhiều assert vẫn được nếu cùng kiểm một hành vi.

*Test data (🟡)*
- *Fixture tĩnh* là bộ dữ liệu soạn sẵn (file SQL, YAML) nạp cho mọi test.
  - Dễ đọc.
  - Nhưng dễ phình to, và các test ngầm phụ thuộc lẫn nhau vào cùng một bộ dữ liệu.
- *Factory* hoặc *builder* là hàm tạo object hợp lệ với giá trị mặc định. Test chỉ ghi đè field
  nó quan tâm.
  - Laravel: model factory, ví dụ `Order::factory()->create(['status' => 'paid'])`.
  - Java: builder hoặc *Object Mother* (class chuyên sinh object mẫu).
  - Go: `newTestOrder(opts...)`.
- ⚠️ Test phụ thuộc dữ liệu do test khác tạo thì chạy riêng lẻ sẽ fail.
- ⚠️ Không dùng bản sao production chưa ẩn danh làm test data, vì chứa *PII* (thông tin định danh
  cá nhân như tên, số điện thoại, [10-security.md](10-security.md)).

**Đọc**
- Martin Fowler: [Test Double](https://martinfowler.com/bliki/TestDouble.html), [Mocks Aren't Stubs](https://martinfowler.com/articles/mocksArentStubs.html) (classical so với mockist)
- *Software Engineering at Google*: [ch.12 Unit Testing](https://abseil.io/resources/swe-book/html/ch12.html) (test qua public API, test hành vi), [ch.13 Test Doubles](https://abseil.io/resources/swe-book/html/ch13.html) (ưu tiên real > fake > stub/mock)

**Nắm chắc khi**
- [ ] Nhìn một test có 6 `expects()` liên tiếp, chỉ ra được vì sao nó dễ vỡ và viết lại theo hướng kiểm hành vi
- [ ] Giải thích được stub và mock khác nhau bằng một ví dụ trong dự án của mình
- [ ] Viết được factory cho `Order` mà mỗi test chỉ cần ghi đè 1–2 field

#### 1.3 Git cơ bản

**Vì sao cần học:** Ngày nào cũng dùng Git, và các sự cố Git (mất code sau force push, revert
sai trên `main`) thường xảy ra đúng lúc gấp nhất. Câu "merge khác rebase thế nào" và "revert khác
reset thế nào" là câu mở màn phổ biến, và người phỏng vấn hay hỏi vặn "khi nào không được rebase".

**Học gì**

*Merge, rebase, squash*
- Ba cách đưa nhánh `feature` (có commit D, E) vào `main` (đã có thêm commit C):
  ```
  main:    A---B---C              merge:   A---B---C---M      (M có hai cha)
  feature:      \--D---E                         \--D---E-/
                                  rebase:  A---B---C---D'---E' (commit mới, hash mới)
                                  squash:  A---B---C---S      (D+E gộp thành S)
  ```
- *Merge* tạo một *merge commit* M có hai commit cha. Lịch sử giữ đúng như đã xảy ra.
- *Rebase* chép lại D, E lên sau C thành D', E'. Đây là commit mới, có *hash* (mã định danh của
  commit) mới. Lịch sử thành một đường thẳng.
- *Squash* gộp D và E thành một commit S. Lịch sử gọn, nhưng mất các commit nhỏ.
- ⚠️ Không rebase nhánh đã push mà người khác đang dùng.
  - Lý do: rebase đổi hash, nên lịch sử trên máy người khác không còn khớp với lịch sử của bạn.
- Force push (ghi đè nhánh trên remote) nhánh của mình thì dùng `--force-with-lease`.
  - Lệnh này từ chối ghi đè nếu trên remote có commit mà bạn chưa thấy, nên không xoá nhầm
    commit của người khác.

*Cherry-pick*
- *Cherry-pick* chép một commit sang nhánh khác.
  - Ví dụ: chép commit hotfix từ `main` sang nhánh `release`.
- ⚠️ Commit chép sang là commit mới, hash khác.
- ⚠️ Cherry-pick nhiều thì dễ quên đồng bộ ngược giữa các nhánh.

*Revert và reset*
- `revert` tạo một commit mới đảo ngược thay đổi của commit cũ, không sửa lịch sử. Dùng trên
  nhánh chung.
- `reset` kéo nhánh lùi về một commit cũ, tức là viết lại lịch sử. Chỉ dùng trên nhánh local chưa
  chia sẻ. Có ba mode:

  | Mode | Thay đổi của các commit bị bỏ đi nằm ở đâu |
  |---|---|
  | `--soft` | Vẫn còn trong *stage* (vùng đã `git add`) |
  | `--mixed` (mặc định) | Vẫn còn trong *working tree* (file trên đĩa), nhưng chưa `add` |
  | `--hard` | Bỏ hết |

- ⚠️ Revert một merge commit phải thêm `-m 1`, để chỉ rõ giữ phía cha số 1 (thường là `main`).
- ⚠️ Bẫy khi merge lại sau khi revert merge:
  1. Nhánh `feature` được merge vào `main`.
  2. Phát hiện lỗi, revert merge commit đó.
  3. Sửa xong, merge `feature` vào lại.
  4. Git thấy các commit của `feature` đã có trong lịch sử `main` rồi, nên không mang lại những
     thay đổi đã bị revert.

  Muốn lấy lại thì phải revert chính commit revert ("revert cái revert").

*Conflict*
- *Conflict* xảy ra khi hai nhánh cùng sửa một chỗ và Git không tự quyết được giữ bên nào.
- Cách giải:
  1. Hiểu cả hai phía muốn gì trước khi chọn.
  2. Hỏi tác giả phía kia khi không chắc.
  3. Chạy lại test sau khi giải.

*Commit message*
- *Conventional Commits* là quy ước viết dòng đầu commit dạng `type(scope): mô tả`.
  - Ví dụ: `feat(order): add partial refund`, `fix: handle empty cart`.
  - Thay đổi phá tương thích đánh dấu bằng `!` (như `feat!:`) hoặc footer `BREAKING CHANGE:`.
- Dòng đầu (*subject*) viết thể mệnh lệnh ("add", không phải "added").
- Phần thân (*body*) giải thích **vì sao** đổi. Diff đã cho biết đổi gì.
- Lợi ích:
  - Đọc lịch sử nhanh.
  - Sinh *changelog* (danh sách thay đổi mỗi bản) và số version tự động.

**Đọc**
- Pro Git: [Git Branching: Rebasing](https://git-scm.com/book/en/v2/Git-Branching-Rebasing) (đặc biệt mục *The Perils of Rebasing*)
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)

**Nắm chắc khi**
- [ ] Vẽ được đồ thị commit sau merge, rebase, squash của cùng một nhánh
- [ ] Hoàn tác được một commit xấu đã lên `main` mà không viết lại lịch sử
- [ ] Giải thích được vì sao merge lại nhánh đã bị revert không mang code về

#### 1.4 Code review và PR

**Vì sao cần học:** Code review là nơi senior tạo ảnh hưởng lớn nhất lên chất lượng của cả team,
không chỉ code của mình. Câu "khi review bạn nhìn vào đâu" rất hay gặp. Người chỉ nói về đặt tên
và format bị đánh giá là chưa đủ tầm, còn tình huống "PR 3000 dòng, deadline mai" là câu hỏi
senior kinh điển.

**Học gì**

*Review cái gì, theo thứ tự quan trọng*
1. Đúng yêu cầu chưa, có hiểu đúng bài toán không.
2. Correctness (code chạy đúng không):
   - Edge case, xử lý lỗi.
   - Concurrency (nhiều request chạy cùng lúc), transaction.
   - *Idempotency*: gọi hai lần có cho kết quả như một lần không.
3. Bảo mật:
   - Input validation, phân quyền, SQL injection.
   - Log có lộ dữ liệu nhạy cảm không.
4. Vận hành:
   - Migration có an toàn trên bảng lớn không.
   - Có log, metric để theo dõi không.
   - Rollback được không.
5. Thiết kế:
   - Code đặt đúng chỗ chưa.
   - *Abstraction* (lớp trừu tượng như interface, base class) có thật sự cần không.
   - Có trùng với thứ đã có trong codebase không.
6. Test: có test cho hành vi mới và cho bug vừa sửa không.
7. Đọc hiểu: tên, cấu trúc. Style (dấu cách, xuống dòng) để *formatter* (công cụ tự định dạng
   code, module 2.5) lo.

*Cách góp ý*
- Góp ý về code, không về người.
- Hỏi thay vì ra lệnh: "Nếu list rỗng thì sao?" thay cho "Sai rồi, sửa đi".
- Ghi rõ mức độ:
  - *Blocking*: phải sửa mới merge.
  - `nit:` (viết tắt của nitpick): góp ý nhỏ, sửa hay không tuỳ tác giả.
- Giải thích vì sao.
- Khen chỗ tốt.
- Bất đồng quá hai vòng comment thì nói chuyện trực tiếp.

*Khi bị review*
- Không phòng thủ.
- Trả lời mọi comment.
- Cảm ơn khi người review phát hiện lỗi.

*Kích thước PR*
- PR nhỏ được review kỹ. PR vài nghìn dòng thường chỉ nhận "LGTM" (looks good to me), tức gần như
  không ai đọc.
- Cách giữ PR nhỏ:
  - Tách refactor riêng, đổi hành vi riêng, migration riêng.
  - Dùng *feature flag* (công tắc bật tắt tính năng trong code, module 2.6) để merge dần phần
    chưa xong.
- Trước khi nhờ review:
  - Tự review diff của mình trước.
  - Mô tả PR nói rõ vì sao làm, cách test, rủi ro.

*Definition of Done*
- *Definition of Done* là danh sách điều kiện để một việc được coi là xong. Ví dụ:
  - Đã merge, có test, đã review.
  - Tài liệu đã cập nhật.
  - Deploy được, có monitoring.
  - Flag bật tắt được.
  - PO (product owner, người chịu trách nhiệm sản phẩm) chấp nhận.
- Team phải thống nhất danh sách này trước, không phải tới lúc xong mới bàn.

**Đọc**
- [Google Engineering Practices: Code Review](https://google.github.io/eng-practices/review/) (cả hai phần: người review và người viết)
- *Software Engineering at Google*: [ch.9 Code Review](https://abseil.io/resources/swe-book/html/ch09.html)

**Nắm chắc khi**
- [ ] Viết được checklist review 10 dòng cho team mình, sắp theo mức quan trọng (bài tập 4)
- [ ] Viết lại được 3 comment review "cộc" thành dạng câu hỏi có lý do
- [ ] Tách được một PR 1500 dòng thành 3–4 PR có thể merge độc lập

---

### Chặng 2: Làm chủ 🟡

#### 2.1 Test isolation, DB và flaky test

**Vì sao cần học:** Suite test Laravel nào có DB cũng sớm gặp hai vấn đề: test ảnh hưởng lẫn nhau
qua dữ liệu, và test lúc xanh lúc đỏ. Nặng hơn, test trỏ nhầm DB dev dùng chung có thể xoá sạch
dữ liệu của cả team. Người phỏng vấn hay hỏi "cô lập DB trong test thế nào" và "flaky test do đâu",
kèm tình huống sự cố thật.

**Học gì**

*Test isolation là gì*
- *Test isolation* (cô lập test) nghĩa là mỗi test tự chuẩn bị và tự dọn trạng thái của mình.
- Tiêu chí: chạy riêng một test, hay chạy cả suite theo thứ tự nào, đều pass.

*Cách cô lập DB*
- Cách 1: DB riêng cho test. Có ba dạng:
  - Chạy DB trong container.
  - Một schema (database) riêng trên cùng server.
  - SQLite in-memory (DB nằm trong RAM, mất khi process kết thúc), nếu chấp nhận nó khác
    *dialect* (biến thể SQL riêng của từng DB) với MySQL.
- Cách 2: bọc mỗi test trong một transaction rồi rollback khi test xong, nên mọi dòng test ghi
  vào đều biến mất.
- ⚠️ Transaction rollback không dọn được:
  - Dữ liệu ghi qua một kết nối DB khác mà code tự mở, vì transaction chỉ thuộc một kết nối.
  - Job chạy ở worker khác, vì worker dùng kết nối của nó.
  - *DDL* (lệnh đổi cấu trúc như `CREATE TABLE`, `ALTER TABLE`): MySQL tự commit ngay khi chạy DDL.
  - Dữ liệu ghi vào Redis, queue, file.

*Không bao giờ nối vào DB dùng chung*
- ⚠️ **Không bao giờ để test nối vào DB dev hay staging dùng chung.** Chuỗi sự cố:
  1. Test hợp lệ có chạy `TRUNCATE` hoặc `DELETE` để dọn dữ liệu.
  2. Bootstrap của test có thể chạy migration ngầm, ví dụ trait `RefreshDatabase` của Laravel.
  3. Cấu hình trỏ nhầm sang DB dev dùng chung.
  4. Kết quả: xoá dữ liệu của cả team, và chạy migration chưa review lên DB chung.
- Cách phòng:
  - Cấu hình DB test tường minh trong `phpunit.xml` hoặc `.env.testing`.
  - Thêm một *guard* (đoạn kiểm tra chặn) trong `setUp`, dừng ngay nếu tên DB không phải DB test:

    ```php
    protected function setUp(): void
    {
        parent::setUp();
        $db = DB::connection()->getDatabaseName();
        if (! str_contains($db, 'test')) {
            $this->fail("Test đang trỏ vào DB '$db', không phải DB test!");
        }
    }
    ```

    Dùng `str_contains` thay vì so bằng `===`, vì khi chạy `--parallel` Laravel thêm hậu tố
    vào tên DB test cho mỗi process (module 2.3).

*SQLite in-memory và Testcontainers*
- ⚠️ SQLite in-memory làm test nhanh nhưng khác MySQL ở:
  - Kiểu dữ liệu, collation (luật so sánh chuỗi), JSON, lock, `ON DUPLICATE KEY`.
  - Hệ quả: bug chỉ xảy ra trên MySQL lọt qua test.
- 🟡 *Testcontainers* là thư viện tự khởi động container DB, Redis, Kafka thật cho test, rồi bỏ
  đi khi xong.
  - Có cho Java, Go, và PHP (`testcontainers/testcontainers`, PHP 8.1+).
  - Lợi: đúng engine và phiên bản như production.
  - Giá: chậm hơn, và CI phải có Docker.
  - Giảm chi phí: dùng một container cho cả suite, cô lập từng test bằng transaction hoặc schema
    riêng.
- Với Laravel, cách phổ biến hơn là chạy MySQL như một service container trong CI (khối
  `services:` của GitHub Actions), kết hợp `RefreshDatabase`.

*Flaky test*
- ⚠️ *Flaky test* là test lúc pass lúc fail dù code không đổi. Các nguyên nhân thường gặp:

  | Nguyên nhân | Ví dụ | Cách sửa |
  |---|---|---|
  | Thời gian | chạy lúc 23:59, `now()` sang ngày mới; timezone CI khác | inject clock, cố định timezone |
  | Thứ tự | test B dùng dữ liệu test A để lại | cô lập dữ liệu, chạy random order để phát hiện |
  | Mạng | gọi API thật, DNS chậm | stub ở biên, `Http::preventStrayRequests()` |
  | Async | `sleep(100ms)` rồi assert | chờ theo điều kiện có timeout, không sleep cố định |
  | Thứ tự không xác định | duyệt map, `SELECT` không `ORDER BY` | sort trước khi so |
  | Tài nguyên chung | port cố định, file tạm cùng tên, chạy song song cùng DB | port ngẫu nhiên, thư mục tạm riêng, DB riêng mỗi process |

- Giải thích vài cách sửa trong bảng:
  - *Inject clock*: truyền đồng hồ vào code thay vì gọi `now()` trực tiếp, để test cố định được
    thời gian (module 2.2).
  - Chạy test theo *random order* (thứ tự ngẫu nhiên) để lộ ra test nào phụ thuộc test khác.
  - `Http::preventStrayRequests()` của Laravel làm test fail nếu có request HTTP nào chưa được fake.
- ⚠️ Flaky test nguy hiểm hơn không có test:
  - Team quen bấm "re-run" và bỏ qua cả lần đỏ thật.
- Cách quản lý:
  - Theo dõi tỉ lệ flaky.
  - *Quarantine* (cách ly): tạm tách test flaky khỏi luồng chặn merge, nhưng phải có hạn chót sửa.
  - Không để khu quarantine thành nghĩa địa không ai quay lại.

**Đọc**
- Martin Fowler: [Eradicating Non-Determinism in Tests](https://martinfowler.com/articles/nonDeterminism.html)
- Google Testing Blog: [Flaky Tests at Google and How We Mitigate Them](https://testing.googleblog.com/2016/05/flaky-tests-at-google-and-how-we.html)
- [Testcontainers](https://testcontainers.com/) (khái niệm), [Testcontainers for PHP](https://php.testcontainers.org/)
- Laravel: [Resetting the Database After Each Test](https://laravel.com/docs/database-testing#resetting-the-database-after-each-test), [The .env.testing file](https://laravel.com/docs/testing#the-env-testing-environment-file), [Parallel Testing and Databases](https://laravel.com/docs/testing#parallel-testing-and-databases)

**Nắm chắc khi**
- [ ] Viết được guard trong `setUp` chặn test chạy trên DB không phải DB test
- [ ] Chỉ ra được 3 thứ transaction rollback không dọn được trong một test Laravel có queue và Redis
- [ ] Cho một test flaky thật, phân loại được nguyên nhân theo bảng và sửa tận gốc

#### 2.2 Test những thứ khó

**Vì sao cần học:** Phần lớn bug khó chịu nhất trong backend PHP nằm ở những chỗ khó test: thời
gian (bug cuối tháng), API thanh toán bên ngoài, job trong queue, migration. "Bạn test hàm gọi API
thanh toán thế nào?" và "test hàm phụ thuộc thời gian hiện tại thế nào?" là hai câu kinh điển
ở mức mid.

**Học gì**

*Thời gian*
- Không gọi `now()` trực tiếp trong logic. Thay vào đó, nhận một *clock* (object trả về thời gian
  hiện tại) qua constructor. Test truyền vào một clock cố định.
- Công cụ theo ngôn ngữ:
  - PHP: *PSR-20* là chuẩn chung định nghĩa `ClockInterface`. Carbon có `setTestNow()`.
  - Laravel: `$this->travel()`, `$this->travelTo()`, `Date::setTestNow()`.
  - Java: `Clock.fixed(...)`.
  - Go: truyền vào một hàm `func() time.Time`:
    ```go
    type Service struct{ now func() time.Time }

    func (s *Service) IsExpired(t Token) bool { return s.now().After(t.ExpiresAt) }

    // test: svc := &Service{now: func() time.Time { return fixed }}
    ```
- Ca cần test ([22-practical-data.md](22-practical-data.md)):
  - Cuối tháng.
  - Năm nhuận.
  - Đổi timezone.
  - Token hết hạn đúng biên, tức đúng giây hết hạn.

*Code gọi API ngoài*
- Câu kinh điển: test hàm gọi API thanh toán thế nào? Chia thành ba tầng:
  1. Tách một interface `PaymentGateway`. Logic nghiệp vụ test với fake của interface này, cho
     đủ các ca:
     - Thành công.
     - Bị từ chối.
     - Timeout.
     - Lỗi 5xx.
     - Response sai định dạng.
     - Gọi trùng (idempotency).
  2. *Adapter* (class thật gọi HTTP tới provider) test riêng với HTTP stub, tức server giả trả
     response định sẵn: `Http::fake()` của Laravel, WireMock, `httptest.Server` của Go. Kiểm:
     - Request đúng định dạng.
     - Header đúng.
     - Xử lý đúng từng mã lỗi.
  3. Contract test hoặc môi trường *sandbox* (môi trường thử của provider): chạy ít, ngoài luồng
     CI chính.
- ⚠️ Không để unit test gọi sandbox thật.

*Queue và async (🟡)*
- Tách hai câu hỏi:
  - "Có dispatch đúng job không": dùng `Queue::fake()` hoặc `Bus::fake()`, rồi assert job đã được
    đẩy vào queue.
  - "Handler xử lý đúng không": gọi thẳng `handle()` của job, chạy đồng bộ.
- Test handler idempotent: gọi hai lần với cùng message, kết quả phải như gọi một lần.
- Integration test với *broker* (hệ thống queue như RabbitMQ, Kafka) thật khi cần kiểm retry,
  *DLQ* (dead letter queue, nơi chứa message xử lý fail nhiều lần), thứ tự
  ([12-messaging.md](12-messaging.md)).
- ⚠️ Chờ bằng `sleep` là nguồn flaky số một. Dùng *polling có timeout*: kiểm điều kiện lặp lại
  sau mỗi khoảng ngắn, dừng khi đúng hoặc khi quá thời gian tối đa.

*Migration (🟡)*
- Chạy migration trên DB cùng engine và phiên bản với production.
- Có dữ liệu mẫu trong bảng.
  - Ca hay vỡ: thêm cột NOT NULL mới vào bảng đã có dữ liệu.
- Nếu có down migration (hàm `down()` để hoàn tác) thì kiểm cả rollback.
- Kiểm code cũ vẫn chạy được với schema mới. Đây là điều kiện của *expand–contract*: mở rộng
  schema trước, deploy code mới, rồi mới dọn phần cũ ([03-database-sql.md](03-database-sql.md)
  module 3.3).
- 🔴 Bảng lớn: thử trên bản sao có kích thước thật để đo migration khoá bảng bao lâu.

**Đọc**
- PHP-FIG: [PSR-20 Clock](https://www.php-fig.org/psr/psr-20/)
- Laravel: [Mocking: Interacting With Time](https://laravel.com/docs/mocking#interacting-with-time), [HTTP Client: Testing](https://laravel.com/docs/http-client#testing) (mục [Preventing Stray Requests](https://laravel.com/docs/http-client#preventing-stray-requests)), [Queues: Testing](https://laravel.com/docs/queues#testing)

**Nắm chắc khi**
- [ ] Đổi được một hàm gọi `now()` trực tiếp sang inject clock và liệt kê 5 ca thời gian cần test (bài tập 1)
- [ ] Liệt kê được 6 ca cần test cho adapter gọi cổng thanh toán, và ca nào test ở tầng nào
- [ ] Viết được hai test riêng cho "đặt hàng thì dispatch job gửi email" và "job gửi email làm đúng"

#### 2.3 Testing trong PHP và Laravel

**Vì sao cần học:** Đây là bộ công cụ bạn dùng hằng ngày nếu làm Laravel, nên người phỏng vấn
kỳ vọng bạn biết cả cạm bẫy của nó chứ không chỉ cú pháp. Hay gặp: "PHPUnit hay Pest?", "`Event::fake()`
có bẫy gì?", và viết một feature test cho endpoint tạo đơn.

**Học gì**

*PHPUnit*
- *PHPUnit* là framework test chuẩn của PHP. Mỗi năm ra một bản major vào tháng 2.
  - Bản hiện tại: 13.x, cần PHP ≥ 8.4.
  - 12.x (PHP ≥ 8.3) còn được sửa bug tới 02/2027.
- Khai báo thông tin cho test (*metadata*) bằng *attribute* của PHP 8: `#[Test]`,
  `#[DataProvider]`, `#[CoversClass]`.
  - ⚠️ Kiểu cũ ghi trong docblock (`@test`, `@dataProvider`) không còn được hỗ trợ từ PHPUnit 12.
    Nâng cấp mà không đổi thì test bị bỏ qua hoặc lỗi.
- Tạo test double:
  - `createStub()` khi chỉ cần stub.
  - `createMock()` khi cần kỳ vọng về cách được gọi.
- *Data provider*: một hàm trả về nhiều bộ input và kết quả mong đợi, để một test chạy với cả
  bảng dữ liệu.

*Pest*
- *Pest* (bản 4.x) là framework test chạy trên nền PHPUnit, với cú pháp gọn hơn:
  `it('...', fn() => ...)` và `expect($x)->toBe(...)`.
- Tính năng tích hợp sẵn:
  - *Dataset*: tương đương data provider.
  - *Architecture test* bằng `arch()`: kiểm luật cấu trúc code, ví dụ "controller không được gọi
    thẳng model X".
  - `--parallel`: chạy song song.
  - `--shard`: chia suite ra nhiều máy CI.
  - Browser testing bằng Playwright.
  - `--mutate`: mutation testing (module 3.2).

*Mockery*
- *Mockery* là thư viện tạo mock và spy linh hoạt.
- Laravel dùng nó bên dưới, ví dụ `Cache::shouldReceive('get')`.
- Cần gọi `Mockery::close()` cuối mỗi test để kiểm kỳ vọng. Laravel tự gọi cho bạn.

*Helper của Laravel: HTTP và DB*
- HTTP test (gọi route như client thật, trong cùng process):
  - `$this->getJson()`, `postJson()`.
  - `assertStatus`, `assertJsonPath`.
  - `actingAs($user)`: giả lập đã đăng nhập.
- DB:
  - `RefreshDatabase`: migrate một lần mỗi lượt chạy, rồi bọc mỗi test trong transaction.
  - `DatabaseTruncation`: xoá sạch bảng sau mỗi test, không dùng transaction (cần khi test nhiều
    connection, module 3.3).
  - Model factory và seeder để tạo dữ liệu.
  - `assertDatabaseHas`: kiểm DB có dòng khớp điều kiện.
  - `expectsDatabaseQueryCount`: kiểm số query, dùng để chống N+1.

*Fakes của Laravel*
- *Fake* thay một dịch vụ bằng bản giả ghi lại mọi thứ, để assert sau: `Queue::fake`,
  `Bus::fake`, `Event::fake`, `Mail::fake`, `Notification::fake`, `Http::fake`, `Storage::fake`,
  `Process::fake`.
- `Event::fake([OrderPaid::class])` chỉ fake một phần: event `OrderPaid` bị chặn, các event khác
  vẫn chạy thật.
- ⚠️ `Event::fake()` không tham số fake toàn bộ, tắt luôn model event và *observer* (class lắng
  nghe sự kiện `created`, `updated` của model). Code dựa vào observer không chạy, test có thể
  pass sai.
- ⚠️ `Queue::fake()` không chạy job, chỉ ghi lại là đã dispatch. Muốn test cả luồng thì gọi
  `handle()` trực tiếp, hoặc dùng queue driver `sync` (chạy job ngay lập tức) một cách có chủ đích.

*Chạy song song và browser test*
- `php artisan test --parallel`: mỗi process có một DB test riêng.
- Browser test:
  - *Dusk* là công cụ cũ của Laravel, điều khiển Chrome qua ChromeDriver.
  - Laravel docs hiện khuyên dự án mới dùng browser testing của Pest 4.
- PHPStan chạy trong CI là tầng "static" của testing trophy (module 2.5).

**Đọc**
- PHPUnit: [Manual](https://docs.phpunit.de/) (các chương *Writing Tests*, *Test Doubles*, *Attributes*), [Supported Versions](https://phpunit.de/supported-versions.html)
- Pest: [Installation](https://pestphp.com/docs/installation), [Browser Testing](https://pestphp.com/docs/browser-testing), [Pest v4 announcement](https://pestphp.com/docs/pest-v4-is-here-now-with-browser-testing)
- [Mockery docs](https://docs.mockery.io/en/latest/)
- Laravel: [HTTP Tests](https://laravel.com/docs/http-tests), [Database Testing](https://laravel.com/docs/database-testing), [Mocking](https://laravel.com/docs/mocking) (mục [Mocking Facades](https://laravel.com/docs/mocking#mocking-facades)), [Running Tests in Parallel](https://laravel.com/docs/testing#running-tests-in-parallel), [Events: Testing](https://laravel.com/docs/events#testing), [Dusk](https://laravel.com/docs/dusk)
- Góc runtime PHP/Laravel: [05-php-laravel.md](05-php-laravel.md)

**Nắm chắc khi**
- [ ] Viết được feature test cho endpoint tạo đơn: kiểm response, DB, job đã dispatch, email chưa gửi khi thanh toán fail
- [ ] Chỉ ra được một test dùng `Event::fake()` pass sai vì observer không chạy, rồi sửa bằng fake một phần
- [ ] Chạy được suite song song với DB riêng mỗi process và đo thời gian trước/sau

#### 2.4 Contract testing

**Vì sao cần học:** Khi hệ thống tách thành nhiều service (ví dụ app Laravel gọi service thanh
toán của team khác), lỗi hay gặp là bên kia đổi API và bên này vỡ mà không ai biết cho tới
production. Câu hỏi thường là "contract test giải quyết vấn đề gì" và "khi nào không đáng làm".

**Học gì**

*Vấn đề cần giải*
- Hai vai trò:
  - *Provider*: service cung cấp API.
  - *Consumer*: service gọi API đó.
- Ví dụ sự cố: provider đổi tên field `amount` thành `total`. Test của provider vẫn xanh, test
  của consumer (dùng stub) cũng xanh. Consumer vỡ khi lên production.
- E2E xuyên nhiều service bắt được lỗi này, nhưng chậm và flaky. Contract test là cách thay thế.

*Consumer-driven contract*
- Luồng hoạt động:
  1. Consumer viết test mô tả kỳ vọng của mình: gọi endpoint nào, cần những field nào. Chạy test
     sinh ra một file kỳ vọng gọi là **pact**.
  2. Pact được đẩy lên *broker*, một server lưu và chia sẻ pact giữa các team.
  3. Provider, trong CI của mình, tải pact về và chạy *verify*: gọi API thật của mình theo từng
     request trong pact, so response với kỳ vọng.
  4. Verify fail thì provider biết mình sắp làm vỡ consumer, và deploy bị chặn.
- Công cụ:
  - Pact: có `pact-php`, Java, Go, JS...
  - Spring Cloud Contract (hệ Java).
- Cách ngược lại là *provider-driven*: provider công bố schema OpenAPI (file mô tả API), rồi dùng
  công cụ kiểm xem schema mới có còn tương thích với bản cũ không.

*Giới hạn*
- ⚠️ Contract test không kiểm logic nghiệp vụ của provider, chỉ kiểm hình dạng giao tiếp.
- ⚠️ Chỉ đáng công khi có nhiều team, nhiều consumer. Một team sở hữu cả hai đầu thì integration
  test hoặc schema là đủ.
- Liên quan versioning API và *backward compatibility* (bản mới vẫn chạy được với client cũ):
  [09-api-design.md](09-api-design.md).

**Đọc**
- [Pact docs: How Pact works](https://docs.pact.io/getting_started/how_pact_works), [pact-php](https://github.com/pact-foundation/pact-php) (README, ví dụ consumer/provider)
- Martin Fowler: [Contract Test](https://martinfowler.com/bliki/ContractTest.html); phần *Contract Tests* trong [The Practical Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)

**Nắm chắc khi**
- [ ] Vẽ được luồng consumer → pact → broker → provider verify, và chỉ ra bước nào chặn deploy
- [ ] Nói được khi nào contract test không đáng công

#### 2.5 Static analysis, linter và CI

**Vì sao cần học:** Với PHP, static analysis bắt được cả loạt bug mà các ngôn ngữ có compiler tự
bắt, trước khi code chạy. CI là nơi mọi kiểm tra này thành bắt buộc. Câu hỏi senior hay gặp:
"đưa PHPStan vào codebase cũ có hàng nghìn lỗi thế nào" và "test suite chạy 40 phút, dev không
chờ CI nữa, bạn làm gì".

**Học gì**

*Static analysis là gì*
- *Static analysis* (phân tích tĩnh) là công cụ đọc code và tìm lỗi mà không cần chạy code.
- Công cụ theo ngôn ngữ:

  | Ngôn ngữ | Công cụ | Bắt được gì |
  |---|---|---|
  | PHP | PHPStan (level 0–10), Larastan, Psalm | gọi method không tồn tại, sai kiểu, null chưa kiểm, `mixed` lan rộng |
  | Java | SpotBugs, Error Prone, PMD, SonarQube | null dereference, resource leak, equals/hashCode sai |
  | Go | `go vet`, staticcheck, golangci-lint | format string sai, copy lock, lỗi bị bỏ qua |

- Giải thích vài mục trong bảng:
  - *Level* của PHPStan: level càng cao thì luật càng khắt khe.
  - *Larastan* là extension giúp PHPStan hiểu "magic" của Laravel, ví dụ thuộc tính Eloquent
    không được khai báo trong class.
  - `mixed` là kiểu "không biết là gì". Một giá trị `mixed` truyền đi đâu thì chỗ đó cũng mất
    thông tin kiểu.
- PHP đặc biệt hưởng lợi, vì PHP chỉ kiểm kiểu lúc chạy. Static analysis gần như là một
  compiler thứ hai.

*Đưa vào codebase cũ*
- Chạy PHPStan lần đầu trên codebase cũ có thể ra hàng nghìn lỗi. Cách làm:
  1. Bắt đầu ở level thấp, hoặc tạo **baseline**: một file ghi nhận toàn bộ lỗi cũ để tạm bỏ qua.
     Từ đó CI chỉ chặn lỗi mới.
  2. Nâng level dần.
  3. Đo số lỗi trong baseline giảm theo thời gian.
- *Rector* là công cụ tự sửa code hàng loạt, ví dụ nâng lên PHP version hay Laravel version mới.
  - Chạy `--dry-run` (chỉ báo, không sửa) trong CI để chặn code viết kiểu cũ.

*Linter và formatter*
- *Linter* bắt lỗi phong cách và mẫu code dễ sai. *Formatter* tự định dạng code (dấu cách, xuống
  dòng) theo một chuẩn chung.
  - PHP: Laravel Pint, PHP-CS-Fixer.
  - Go: gofmt, goimports.
  - Java: google-java-format, Spotless.
- Chạy trong *pre-commit hook* (script Git chạy trước mỗi commit) hoặc trong CI, để lúc review
  không ai phải bàn chuyện dấu cách.

*Test trong CI*
- Mọi PR phải chạy lint, static analysis, test trước khi merge.
  - Bắt buộc bằng *branch protection*: cài đặt trên GitHub chặn merge vào `main` khi CI chưa xanh.
- Giữ pipeline nhanh:
  - Chạy song song.
  - Cache dependency (thư mục `vendor/`).
  - Tách suite chậm ra job riêng.
  - ⚠️ Pipeline chậm thì người ta tìm cách bỏ qua.
- DB và service phụ chạy trong container riêng, dùng xong bỏ ([19-devops-cloud.md](19-devops-cloud.md)).
- ⚠️ Pass ở máy dev mà fail ở CI, thường do khác:
  - Timezone.
  - *Locale* (thiết lập ngôn ngữ, định dạng số và ngày).
  - Thứ tự file khi liệt kê thư mục.
  - Phiên bản PHP hoặc extension.

**Đọc**
- PHPStan: [Rule Levels](https://phpstan.org/user-guide/rule-levels), [Baseline](https://phpstan.org/user-guide/baseline); [Larastan](https://github.com/larastan/larastan)
- [Rector documentation](https://getrector.com/documentation); Laravel: [Pint](https://laravel.com/docs/pint) (mục [Continuous Integration](https://laravel.com/docs/pint#continuous-integration))
- GitHub: [About protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)

**Nắm chắc khi**
- [ ] Mô tả được lộ trình đưa PHPStan vào dự án chưa từng dùng, gồm baseline và nâng level (bài tập 5)
- [ ] Viết được pipeline CI cho Laravel: Pint, PHPStan, test song song với MySQL service, thời gian dưới 10 phút
- [ ] Giải thích được vì sao level cao bắn lỗi nhiều ở code dùng magic của Eloquent và Larastan giúp gì

#### 2.6 Git nâng cao và quy trình nhóm

**Vì sao cần học:** Các lệnh Git nâng cao cứu bạn trong lúc sự cố: tìm lại code sau khi reset
nhầm, tìm commit gây lỗi trong hàng trăm commit. Chọn branching strategy ảnh hưởng tới tốc độ
release của cả team. Hay bị hỏi: "Git flow hay trunk-based?" và "tìm commit gây chậm API trong
200 commit thế nào".

**Học gì**

*Ba lệnh cứu hộ*
- `git reflog` liệt kê mọi vị trí mà `HEAD` (commit bạn đang đứng) từng trỏ tới trên máy bạn.
  - Dùng để tìm lại commit sau khi `reset --hard` hay rebase nhầm, vì commit chưa bị xoá ngay.
- `git bisect` tìm commit gây lỗi bằng *tìm kiếm nhị phân* (mỗi bước loại một nửa số commit):
  1. `git bisect start`.
  2. `git bisect bad`: đánh dấu commit hiện tại là lỗi.
  3. `git bisect good <hash>`: đánh dấu một commit cũ chắc chắn không lỗi.
  4. Git checkout commit ở giữa. Bạn thử và đánh dấu `good` hoặc `bad`. Lặp lại tới khi còn một
     commit.
- `git bisect run <lệnh>` tự động hoá bước 4: Git chạy lệnh ở mỗi commit, coi *exit code* (mã
  kết thúc của lệnh) 0 là good, khác 0 là bad.
  - n commit cần khoảng log₂(n) bước. Ví dụ 200 commit cần khoảng 8 bước.
  - Hiệu quả khi commit nhỏ và mỗi commit đều build được.
- `git rerere` (reuse recorded resolution) nhớ cách bạn đã giải một conflict, để lần sau gặp lại
  đúng conflict đó thì tự áp dụng.

*Branching strategy*
- *Branching strategy* là quy ước team dùng nhánh thế nào. Hai kiểu chính:
  - *Git flow*: nhiều loại nhánh sống lâu.
  - *Trunk-based*: mọi người merge thường xuyên vào một nhánh chính (trunk).

  | | Git flow | Trunk-based |
  |---|---|---|
  | Nhánh | main, develop, feature, release, hotfix | main + nhánh ngắn (vài giờ tới vài ngày) |
  | Hợp với | release theo đợt, nhiều phiên bản song song (app mobile, phần mềm đóng gói) | deploy liên tục, SaaS |
  | Rủi ro | branch sống lâu, merge đau, tích hợp muộn | cần CI tốt, test tốt, feature flag |

*Feature flag*
- *Feature flag* là một công tắc trong code: `if (Feature::active('new-checkout')) { ... }`. Nó
  thay cho branch sống lâu.
- Lợi ích:
  - Merge code chưa xong vào `main`, nhưng tắt sau flag.
  - Tách *deploy* (đưa code lên server) khỏi *release* (bật tính năng cho người dùng).
  - Bật dần theo % user.
  - Tắt nhanh khi có sự cố, không cần deploy lại.
- ⚠️ Flag là nợ kỹ thuật:
  - Xoá flag sau khi rollout xong.
  - Test cả hai trạng thái bật và tắt.
- Laravel có package *Pennant* cho feature flag.

*Agile và Scrum cơ bản*
- *Scrum* là cách làm việc theo *sprint*, một chu kỳ cố định thường 1 đến 4 tuần.
- Các buổi họp chính:
  - Planning: chọn việc cho sprint.
  - Daily: cập nhật ngắn hằng ngày.
  - Review: demo kết quả cuối sprint.
  - Retrospective: nhìn lại cách làm việc để cải thiện.
- Ước lượng bằng *story point* (điểm độ khó tương đối) hoặc bằng thời gian
  ([24-senior-leadership.md](24-senior-leadership.md)).

**Đọc**
- Git: [git-bisect](https://git-scm.com/docs/git-bisect), [git-reflog](https://git-scm.com/docs/git-reflog), [git-rerere](https://git-scm.com/docs/git-rerere)
- [Trunk Based Development](https://trunkbaseddevelopment.com/); [A successful Git branching model](https://nvie.com/posts/a-successful-git-branching-model/) (bài gốc Git flow, đọc cả ghi chú 2020 của tác giả ở đầu bài); Martin Fowler: [Patterns for Managing Source Code Branches](https://martinfowler.com/articles/branching-patterns.html)
- Martin Fowler: [Feature Toggles](https://martinfowler.com/articles/feature-toggles.html); Laravel: [Pennant](https://laravel.com/docs/pennant)
- [The Scrum Guide](https://scrumguides.org/scrum-guide.html)

**Nắm chắc khi**
- [ ] Dùng được `git bisect run` với một script trả exit code để tìm commit gây lỗi (bài tập 6)
- [ ] Cứu được một nhánh sau khi `reset --hard` nhầm, chỉ bằng reflog
- [ ] Tư vấn được git flow hay trunk-based cho một team cụ thể dựa trên 4 câu hỏi

---

### Chặng 3: Senior 🔴

#### 3.1 TDD, BDD và chọn phương pháp

**Vì sao cần học:** Câu "bạn có dùng TDD không" gần như chắc chắn xuất hiện, và nó kiểm độ trung
thực nhiều hơn kiến thức. Người phỏng vấn muốn nghe bạn dùng khi nào, không dùng khi nào, vì sao.
BDD và test ở quy mô lớn là chủ đề senior khi bàn chiến lược test cho cả hệ thống.

**Học gì**

*TDD*
- *TDD* (test-driven development) là viết test trước khi viết code, theo vòng lặp ba bước:
  1. Red: viết một test mới, chạy thấy fail.
  2. Green: viết code tối thiểu để test pass.
  3. Refactor: dọn code cho sạch, test vẫn phải xanh.
- Lợi:
  - Buộc nghĩ về interface và hành vi trước khi nghĩ cách cài đặt.
  - Code dễ test, vì ngay từ đầu nó được thiết kế để test.
  - Có lưới an toàn khi refactor.
- Nhược:
  - Chậm lúc đầu.
  - Khó khi yêu cầu còn mơ hồ, hoặc đang *spike* (viết code thử nghiệm để tìm hướng, sẽ bỏ đi).
  - Làm máy móc thì dễ sinh over-mocking (module 1.2).
- Câu trả lời trung thực được đánh giá cao hơn "tôi luôn TDD". Hãy nói rõ khi nào mình dùng.
  - Ví dụ: khi sửa bug, viết test tái hiện bug trước. Đây là dạng TDD rẻ nhất.

*BDD*
- *BDD* (behavior-driven development) là mô tả hành vi bằng kịch bản Given–When–Then, viết chung
  với PO và QA (người kiểm thử):
  ```gherkin
  Given giỏ hàng có tổng 400.000đ
  And mã giảm giá "SALE50" chỉ áp dụng cho đơn từ 500.000đ
  When khách nhập mã "SALE50"
  Then hệ thống báo "Đơn chưa đủ điều kiện dùng mã"
  ```
- Công cụ: Cucumber, Behat (PHP). Hai công cụ này biến kịch bản trên thành test chạy được.
- Giá trị chính là cuộc trao đổi giữa dev, PO và QA để hiểu đúng yêu cầu, không phải công cụ.

*Test lớn ở quy mô lớn (🔴)*
- *Hermetic test* (test kín): test tự dựng mọi thứ nó cần, không phụ thuộc service hay dữ liệu
  bên ngoài, nên chạy ở đâu cũng ra cùng kết quả.
- Test trên môi trường giống production (staging).
- Test trong production ([18-reliability-observability.md](18-reliability-observability.md)):
  - *Canary*: đưa bản mới cho một phần nhỏ traffic trước, theo dõi rồi mới mở rộng.
  - *Synthetic monitoring*: script tự động chạy luồng chính (đăng nhập, đặt hàng) trên production
    theo lịch, báo động khi fail.

**Đọc**
- *Software Engineering at Google*: [ch.14 Larger Testing](https://abseil.io/resources/swe-book/html/ch14.html)
- [Cucumber docs](https://cucumber.io/docs/), [Behat docs](https://docs.behat.org/en/latest/)

**Nắm chắc khi**
- [ ] Kể được một lần dùng TDD có lợi và một lần không, kèm lý do
- [ ] Viết được một kịch bản Given–When–Then cho luồng hoàn tiền mà PO đọc hiểu được

#### 3.2 Đo chất lượng test: coverage, mutation, property-based

**Vì sao cần học:** Quản lý hay đặt KPI "coverage 80%" và senior phải giải thích được vì sao con
số đó không nói lên test tốt hay dở. Mutation testing và property-based testing là hai công cụ đo
và tăng chất lượng test thật sự, rất hợp với code tính tiền. Hay bị hỏi: "coverage 90% có nghĩa là
test tốt không?" và "mutation testing là gì".

**Học gì**

*Coverage*
- *Coverage* (độ phủ) là tỉ lệ code được chạy qua khi chạy test. Hai loại chính:
  - *Line coverage*: bao nhiêu dòng đã được chạy.
  - *Branch coverage*: bao nhiêu nhánh (`if` đúng, `if` sai) đã được chạy. Khắt khe hơn line
    coverage.
  - Ví dụ: `if ($vip) { $discount = 10; }` với một test `$vip = true` là 100% line, nhưng chỉ 50%
    branch, vì nhánh `$vip = false` chưa chạy.
- ⚠️ Coverage cao không có nghĩa là test tốt: test chạy qua code mà không assert gì vẫn được tính
  là covered.
- Ngược lại, coverage thấp thì chắc chắn có chỗ chưa test.
- Cách dùng đúng: để **tìm chỗ chưa test**, không làm KPI.
  - ⚠️ Ngưỡng cứng sinh ra test rác, viết chỉ để đủ số.
  - Tốt hơn: không cho coverage của code mới giảm.
- PHP cần extension PCOV hoặc Xdebug để đo coverage.
  - Laravel: `php artisan test --coverage --min=80`.

*Mutation testing*
- *Mutation testing* kiểm xem test có thật sự bắt được lỗi không:
  1. Công cụ tự sửa code một chút, mỗi bản sửa gọi là một *mutant*. Ví dụ: đổi `>` thành `>=`,
     bỏ một dòng, đổi `true` thành `false`.
  2. Chạy test trên từng mutant.
  3. Test fail nghĩa là mutant bị "giết": test đã phát hiện ra thay đổi.
  4. Test vẫn pass nghĩa là mutant "sống": không test nào kiểm hành vi đó.
- Vì vậy mutation testing đo chất lượng test tốt hơn coverage.
- Công cụ:
  - **Infection** (PHP). Chỉ số chính là *MSI* (mutation score indicator), tức tỉ lệ mutant bị giết.
  - `pest --mutate`.
  - PIT (Java).
  - Go có công cụ nhưng ít phổ biến.
- Giá: rất chậm, vì chạy lại test cho từng mutant. Cách giảm:
  - Chỉ chạy trên module quan trọng.
  - Hoặc chỉ trên phần code thay đổi (Infection có `--git-diff-filter`).

*Property-based testing*
- Test thường viết từng ví dụ cụ thể: input 3 thì output 6. *Property-based testing* thay vào đó
  khai báo một **tính chất** luôn đúng với mọi input.
- Thư viện tự sinh hàng trăm input ngẫu nhiên để thử tính chất đó.
- Khi tìm được input làm fail, thư viện *shrink* (thu nhỏ) nó về ca nhỏ nhất vẫn fail, để dễ debug.
- Tính chất hay dùng:
  - `decode(encode(x)) == x`.
  - Sort xong thì các phần tử có thứ tự, và vẫn đúng những phần tử ban đầu.
  - Chia một khoản tiền thành nhiều phần thì tổng các phần bằng tổng ban đầu.
  - Thao tác idempotent: làm hai lần giống làm một lần.
- Công cụ: jqwik (Java), `rapid` (Go), Eris (PHP).
- Go còn có *fuzzing* sẵn trong `go test` từ 1.18 (`func FuzzXxx(f *testing.F)`): tự sinh input
  ngẫu nhiên để tìm input làm code crash hoặc fail.

**Đọc**
- Martin Fowler: [Test Coverage](https://martinfowler.com/bliki/TestCoverage.html)
- [Infection guide](https://infection.github.io/guide/) (phần *Mutators* và *Metrics*: MSI, covered MSI); [Pest mutation testing](https://pestphp.com/docs/mutation-testing); [PIT](https://pitest.org/)
- [Eris](https://github.com/giorgiosironi/eris), [jqwik](https://jqwik.net/), [Go fuzzing](https://go.dev/doc/security/fuzz/)

**Nắm chắc khi**
- [ ] Chạy Infection trên một module tiền, đọc được danh sách mutant sống và viết test giết ít nhất 3 mutant
- [ ] Viết được ba tính chất cho hàm chia tiền thành n phần có làm tròn (bài tập 3)
- [ ] Giải thích được cho quản lý vì sao không đặt KPI coverage 90%

#### 3.3 Test concurrency

**Vì sao cần học:** Bug concurrency (bán quá tồn kho, rút tiền hai lần) là loại bug đắt nhất và
khó tái hiện nhất, vì chỉ xảy ra khi hai request trùng thời điểm. Test thường chạy tuần tự nên
không bao giờ bắt được. Câu "test chống rút tiền hai lần thế nào" là câu senior hay gặp, và bẫy
nằm ở việc dùng `RefreshDatabase`.

**Học gì**

*Race condition và cách làm lộ nó*
- *Race condition* là bug xảy ra khi hai luồng cùng đọc và ghi một dữ liệu, và kết quả phụ thuộc
  vào luồng nào chạy trước ([13-concurrency.md](13-concurrency.md)).
- *Stress test* cho concurrency: cho nhiều goroutine, thread hoặc process cùng thao tác một thứ,
  rồi kiểm *bất biến* (điều luôn phải đúng).
  - Ví dụ: 20 process cùng rút 100.000đ từ một tài khoản có 1.000.000đ. Assert số dư không âm,
    và tổng tiền đã rút cộng số dư còn lại bằng số dư ban đầu.

*Go: race detector*
- `go test -race` bật *race detector*, công cụ phát hiện *data race* (hai goroutine truy cập cùng
  một biến, ít nhất một bên ghi, không có đồng bộ).
- Nó bắt được data race khi chúng thực sự xảy ra trong lần chạy đó.
- ⚠️ Không báo gì không chứng minh được là không có race. Có thể lần chạy đó chỉ chưa đi qua
  đúng thứ tự gây lỗi.

*PHP: race giữa các process*
- PHP không có thread trong một request, nhưng race vẫn xảy ra giữa nhiều worker PHP-FPM hoặc
  nhiều queue worker cùng đụng một dòng DB.
- Cách test: chạy nhiều process thật trên DB thật:
  - `pcntl_fork` để tách process.
  - Pool của `Process` trong Laravel, chạy nhiều lệnh song song.
  - Gửi request song song vào một server test.

*Test lock ở DB*
- Mở hai transaction thật trên hai connection khác nhau, kiểm một bên bị chặn chờ lock hoặc bị
  lỗi đúng như thiết kế.
- ⚠️ `RefreshDatabase` bọc cả test trong một transaction trên một connection:
  - Dữ liệu test tạo ra không bao giờ được commit, nên connection thứ hai không nhìn thấy nó.
  - Vì vậy không mô phỏng được hai connection độc lập tranh nhau lock.
  - Dùng `DatabaseTruncation` hoặc một DB riêng cho loại test này.
- Lý thuyết race, lock, idempotency: [13-concurrency.md](13-concurrency.md).

**Đọc**
- [Go Data Race Detector](https://go.dev/doc/articles/race_detector)
- Laravel: [Processes: Concurrent Processes](https://laravel.com/docs/processes#concurrent-processes)

**Nắm chắc khi**
- [ ] Viết được test chứng minh luồng trừ tồn kho cũ bị bán quá, rồi pass sau khi sửa bằng update có điều kiện
- [ ] Giải thích được vì sao test dùng transaction rollback không thể kiểm được deadlock

#### 3.4 Legacy code, tech debt và documentation

**Vì sao cần học:** Nhiều dự án PHP thực tế là codebase cũ, ít hoặc không có test, chạy phiên bản
PHP hay Laravel đã hết hỗ trợ. Senior được kỳ vọng biết đưa test vào mà không làm vỡ, và thuyết
phục được business đầu tư trả nợ kỹ thuật. Hay bị hỏi: "nhận codebase không có test, cần sửa
module thanh toán, bạn bắt đầu từ đâu", và red flag lớn nhất là trả lời "viết lại từ đầu".

**Học gì**

*Đưa test vào legacy code*
- *Legacy code* ở đây là code không có test, nên sửa gì cũng sợ vỡ.
- *Characterization test* là test ghi lại hành vi **hiện tại** của code, kể cả khi hành vi đó có
  vẻ sai. Mục tiêu là phát hiện khi mình vô tình làm hành vi thay đổi, chưa phải chứng minh code
  đúng.
- *Seam* (đường nối) là chỗ thay được một phụ thuộc mà không phải sửa code xung quanh, ví dụ
  một tham số constructor hay một interface.
- Quy trình:
  1. Viết characterization test ở mức API hoặc integration trước, vì mức này ít phụ thuộc vào
     cấu trúc code bên trong.
  2. Tìm seam để tách phụ thuộc (DB, API ngoài) ra.
  3. Sửa từng bước nhỏ, mỗi bước có test bảo vệ.
  4. Không refactor lớn cùng lúc.

*Tech debt là gì*
- *Tech debt* (nợ kỹ thuật) là những đánh đổi làm nhanh hôm nay, khiến việc thay đổi sau này tốn
  hơn. Giống vay nợ: được tiền ngay, nhưng trả lãi mỗi lần đụng vào.
- Góc phần tư của Martin Fowler chia nợ theo hai trục:

  | | Thận trọng | Liều |
  |---|---|---|
  | Cố ý | "Ship trước, trả sau, biết rõ hậu quả" | "Không có thời gian thiết kế" |
  | Vô tình | "Giờ mới biết lẽ ra nên làm thế nào" | "Layer là gì?" |

  Ví dụ "ship trước, trả sau, biết rõ hậu quả" là nợ cố ý và thận trọng.
- Các loại nợ:
  - Code.
  - Kiến trúc.
  - Test.
  - Dependency lỗi thời, ví dụ PHP hay Laravel đã hết hỗ trợ.
  - Hạ tầng.
  - Tài liệu.

*Trả nợ thế nào*
- Chỉ nợ gây đau mới cần trả: code hay sửa và hay có bug. Code xấu mà không ai đụng thì để yên.
- Thuyết phục bằng ngôn ngữ business:
  - Thời gian làm một tính năng tương tự tăng từ X lên Y.
  - Số incident.
  - Thời gian onboard người mới.
  - *CVE* (lỗ hổng bảo mật đã công bố) trong dependency.
- Ba cách trả:
  - Gắn vào tính năng đang làm: sửa dần chỗ mình đi qua, theo *boy scout rule* ("để lại chỗ cắm
    trại sạch hơn lúc đến").
  - Dành một tỉ lệ cố định mỗi sprint.
  - Một dự án riêng có mục tiêu đo được.
- ⚠️ "Viết lại toàn bộ" hiếm khi đúng. Thay vào đó dùng *strangler fig*: xây phần mới bao quanh
  hệ thống cũ, chuyển dần từng chức năng sang, cho tới khi phần cũ không còn gì để xoá.

*Documentation*
- README: cách chạy dự án.
- *ADR* (architecture decision record): ghi quyết định gì, vì sao, và các phương án đã cân nhắc.
  - Giá trị nhất sau một năm, khi không ai còn nhớ vì sao lại chọn như vậy.
- *Runbook*: alert này nghĩa là gì, khi nhận thì làm gì.
- Comment trong code giải thích **vì sao**, không lặp lại code đang làm gì.

**Đọc**
- *Working Effectively with Legacy Code*: chương về seam và characterization test; Michael Feathers: [Characterization Testing](https://michaelfeathers.silvrback.com/characterization-testing)
- Martin Fowler: [Technical Debt Quadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html), [Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [ADR GitHub organization](https://adr.github.io/) (mẫu ADR)

**Nắm chắc khi**
- [ ] Lập được kế hoạch 4 tuần đưa test vào module thanh toán không có test, mỗi tuần có đầu ra đo được
- [ ] Viết được một đề xuất trả nợ kỹ thuật 1 trang bằng số liệu business
- [ ] Viết được một ADR cho một quyết định thật trong dự án của mình

---

## Phần 2: Câu hỏi thường gặp (bonus)

Cách dùng: tự trả lời thành tiếng trước, sau đó mới đối chiếu với hướng trả lời. Câu nào bị
đơ thì quay lại module ghi trong ngoặc.

### 🟢 Junior

**1. Unit test và integration test khác nhau thế nào? Bạn viết loại nào nhiều hơn?** (1.1)
- Ý phải có: unit cô lập phụ thuộc, nhanh; integration dùng thành phần thật (DB), bắt bug chỗ nối
- Điểm cộng: tỉ lệ tuỳ chỗ rủi ro; service CRUD thì integration nhiều hơn
- Red flag: "unit test theo pyramid" mà không nói được vì sao

**2. Mock và stub khác nhau thế nào?** (1.2)
- Ý phải có: stub trả giá trị định sẵn cho input; mock có kỳ vọng về cách được gọi
- Điểm cộng: stub cho input, mock/spy cho output có side effect; fake như `Mail::fake()`

**3. `merge` và `rebase` khác nhau thế nào? Khi nào không nên rebase?** (1.3)
- Ý phải có: merge commit có hai cha, rebase viết lại commit với hash mới; không rebase nhánh chung đã push
- Điểm cộng: `--force-with-lease`; squash merge; team thống nhất quan trọng hơn chọn cái nào

**4. `revert` và `reset` khác nhau thế nào?** (1.3)
- Ý phải có: revert thêm commit đảo ngược, an toàn trên nhánh chung; reset di chuyển nhánh, chỉ dùng local
- Điểm cộng: ba mode của reset; revert merge commit cần `-m 1`; reflog cứu reset nhầm

**5. Khi review code bạn nhìn vào đâu?** (1.4)
- Ý phải có: đúng yêu cầu, correctness, bảo mật, vận hành, test trước style
- Điểm cộng: cách góp ý có mức độ (`nit:`), PR nhỏ, tự review trước
- Red flag: chỉ nói về đặt tên và format

**6. Viết commit message thế nào cho tốt?** (1.3)
- Ý phải có: subject ngắn thể mệnh lệnh, body giải thích vì sao; Conventional Commits
- Điểm cộng: `BREAKING CHANGE`; sinh changelog tự động; một commit một thay đổi logic

### 🟡 Mid

**7. Bạn test một hàm gọi API thanh toán bên ngoài thế nào?** (2.2)
- Ý phải có: tách interface; logic test với fake cho các ca thành công, từ chối, timeout, 5xx, response sai; adapter test với `Http::fake()`/WireMock
- Điểm cộng: `Http::preventStrayRequests()`; test idempotency khi gọi trùng; sandbox chạy ngoài CI chính
- Red flag: gọi sandbox thật trong unit test

**8. Test một hàm phụ thuộc thời gian hiện tại thế nào?** (2.2)
- Ý phải có: inject clock (PSR-20, Carbon `setTestNow`, `$this->travelTo()`); cố định thời gian trong test
- Điểm cộng: ca cuối tháng, năm nhuận, timezone, đúng biên hết hạn

**9. Vì sao test không được nối vào DB dev dùng chung? Cô lập DB trong test thế nào?** (2.1)
- Ý phải có: test `TRUNCATE`/migrate sẽ xoá dữ liệu của team; DB test tường minh, guard kiểm tên DB, transaction rollback hoặc container
- Điểm cộng: những thứ transaction không dọn được; tách credential; parallel test mỗi process một DB

**10. Nguyên nhân phổ biến của flaky test? Xử lý thế nào?** (2.1)
- Ý phải có: thời gian, thứ tự, mạng, async `sleep`, thứ tự không xác định, tài nguyên chung
- Điểm cộng: quarantine có hạn, đo tỉ lệ flaky, chạy random order để phát hiện phụ thuộc
- Red flag: "chạy lại là được"

**11. Coverage 90% có nghĩa là test tốt không?** (3.2)
- Ý phải có: không; test không assert vẫn tính covered; dùng coverage tìm chỗ chưa test
- Điểm cộng: chặn coverage code mới giảm; mutation testing đo thật hơn

**12. Trong Laravel, `Queue::fake()` và `Event::fake()` có cạm bẫy gì?** (2.3)
- Ý phải có: fake không chạy job/listener; `Event::fake()` toàn bộ tắt cả model event và observer
- Điểm cộng: fake một phần `Event::fake([X::class])`; test handler riêng bằng cách gọi `handle()`; `assertPushed` với callback kiểm payload

**13. PHPUnit hay Pest? Bạn chọn thế nào?** (2.3)
- Ý phải có: Pest chạy trên PHPUnit, khác cú pháp và tính năng tích hợp (arch test, mutate, browser); chọn theo team
- Điểm cộng: PHPUnit 12+ dùng attribute thay annotation; Pest 4 browser testing được Laravel khuyên thay Dusk cho dự án mới

**14. TDD có ưu nhược gì? Bạn có dùng không?** (3.1)
- Ý phải có: thiết kế từ hành vi, lưới an toàn; chậm lúc đầu, khó khi spike
- Điểm cộng: trả lời trung thực, nói rõ khi nào dùng; bug fix viết test tái hiện trước
- Red flag: "luôn luôn TDD 100%" mà không có ví dụ

**15. Git flow và trunk-based khác nhau thế nào?** (2.6)
- Ý phải có: nhiều nhánh sống lâu so với main + nhánh ngắn; hợp release theo đợt so với deploy liên tục
- Điểm cộng: trunk-based cần CI tốt và feature flag; flag là nợ phải xoá

**16. Contract test giải quyết vấn đề gì?** (2.4)
- Ý phải có: provider đổi API làm consumer vỡ mà không biết; consumer ghi kỳ vọng, provider verify trong CI
- Điểm cộng: broker, chặn deploy; không thay test logic; không đáng khi một team sở hữu cả hai đầu

### 🔴 Senior

**17. Test pyramid hay testing trophy, chọn thế nào cho một service cụ thể?** (1.1)
- Ý phải có: nhìn chỗ rủi ro nằm ở đâu: logic thuần hay chỗ nối
- Điểm cộng: ví dụ cụ thể hai service; integration rẻ nhờ container; static analysis là tầng đáy

**18. Mutation testing là gì, vì sao tốt hơn coverage?** (3.2)
- Ý phải có: sửa code thành mutant, test còn pass thì test yếu; đo khả năng phát hiện lỗi chứ không đo dòng chạy qua
- Điểm cộng: Infection/MSI; chạy trên module quan trọng hoặc diff vì chậm

**19. Bạn đưa static analysis vào một codebase cũ có hàng nghìn lỗi thế nào?** (2.5)
- Ý phải có: baseline hoặc level thấp, CI chặn lỗi mới, nâng dần
- Điểm cộng: Larastan cho Laravel; Rector sửa hàng loạt; theo dõi baseline giảm; ưu tiên module hay sửa
- Red flag: bắt cả team sửa hết trong một sprint

**20. Test suite mất 40 phút, dev bắt đầu push không chờ CI.** (2.5)
- Ý phải có: đo test nào chậm nhất; chạy song song; tách unit và integration thành job riêng; cache dependency
- Điểm cộng: dùng chung container DB; `--parallel`/`--shard`; đẩy e2e sang sau merge hoặc nightly; chỉ chạy test bị ảnh hưởng
- Red flag: bỏ bớt test cho nhanh mà không đo

**21. Một dev báo chạy test xong thì bảng trên DB dev của cả team trống trơn.** (2.1)
- Ý phải có: test đã nối DB chung; dừng chạy test, khôi phục từ backup; cấu hình DB test tường minh; guard kiểm tên DB
- Điểm cộng: tách credential để user test không có quyền trên DB dev; rà bootstrap có migrate ngầm; postmortem không đổ lỗi

**22. Nhận codebase cũ không có test, cần sửa module thanh toán.** (3.4)
- Ý phải có: characterization test ở mức API/integration trước; tìm seam; sửa nhỏ, mỗi bước có test
- Điểm cộng: ưu tiên luồng tiền; feature flag cho thay đổi; không refactor lớn cùng lúc
- Red flag: "viết lại từ đầu cho sạch"

**23. PR 3000 dòng, deadline mai, được nhờ review.** (1.4)
- Ý phải có: đề nghị tách; nếu không kịp thì ưu tiên phần rủi ro (migration, tiền, phân quyền), ghi rõ phần chưa review
- Điểm cộng: yêu cầu feature flag để tắt được; đặt quy ước kích thước PR cho lần sau

**24. Bug production ở hàm tính ngày hết hạn, chỉ xảy ra cuối tháng.** (2.2)
- Ý phải có: regression test tái hiện với clock cố định ngày 31; tìm chỗ gọi `now()` trực tiếp
- Điểm cộng: thêm ca tháng 2, năm nhuận, timezone; property-based cho hàm cộng ngày

**25. Tìm commit gây chậm API trong 200 commit gần nhất.** (2.6)
- Ý phải có: `git bisect run` với script đo thời gian trả exit code; khoảng 8 bước
- Điểm cộng: script phải ổn định (đo nhiều lần, ngưỡng rõ); commit nhỏ thì bisect có ích hơn

**26. Test concurrency (ví dụ chống rút tiền hai lần) thế nào?** (3.3)
- Ý phải có: nhiều process/thread thật cùng thao tác trên DB thật, assert bất biến (số dư không âm, tổng khớp)
- Điểm cộng: không dùng transaction rollback cho test này; race detector của Go không chứng minh vắng race

**27. Làm sao thuyết phục business đầu tư trả tech debt?** (3.4)
- Ý phải có: nói bằng số: thời gian làm tính năng tăng, số incident, CVE
- Điểm cộng: gắn trả nợ vào tính năng sắp làm; mục tiêu đo được; chỉ trả nợ ở chỗ gây đau
- Red flag: "code xấu quá, cần refactor"

**28. Team tranh cãi git flow hay trunk-based.** (2.6)
- Ý phải có: hỏi tần suất release, có nhiều phiên bản song song không, chất lượng CI, có feature flag chưa
- Điểm cộng: trunk-based cần nền tảng test và flag trước; chuyển dần, đo lead time

---

## Bài tập tự làm

1. Chọn một hàm trong dự án của bạn gọi `now()` trực tiếp. Mô tả cách đổi nó sang inject
   clock và liệt kê 5 ca thời gian cần test.
2. Với một service gửi email khi đơn hàng được thanh toán, liệt kê: phần nào dùng fake,
   phần nào dùng DB thật, phần nào không cần test. Viết feature test Laravel tương ứng.
3. Viết ba tính chất (property) cho hàm chia một khoản tiền thành n phần bằng nhau có làm tròn.
4. Viết một checklist review PR 10 dòng cho team của bạn, sắp theo mức quan trọng.
5. Mô tả cách bạn sẽ đưa PHPStan + Larastan (hoặc staticcheck/SpotBugs) vào một dự án chưa
   từng dùng, gồm baseline, lộ trình nâng level và cấu hình CI.
6. Tạo một repo nhỏ 30 commit, cố ý đưa bug vào commit thứ 17, rồi tìm nó bằng
   `git bisect run` với một script test. Ghi lại số bước.
7. Chạy Infection (hoặc `pest --mutate`) trên một class có test. Ghi lại MSI, chọn 3 mutant
   sống và giải thích vì sao test hiện tại không giết được chúng.

> Nộp bài vào đây để được review.
