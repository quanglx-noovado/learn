# 20. Testing và chất lượng code

> [← Mục lục](README.md) · Phạm vi: các loại test và chiến lược test, test double, test isolation, flaky test, test những thứ khó, code review, static analysis, tech debt, Git và quy trình làm việc nhóm.
> Ký hiệu: 🟢 junior · 🟡 mid · 🔴 senior · ⚠️ cạm bẫy hay bị hỏi vặn. Không nhãn = level nào cũng cần.

Mục tiêu của file: **nói được** về cách mình đảm bảo chất lượng, dù dự án hiện tại có test
hay không. Người phỏng vấn không chấm số test bạn từng viết; họ chấm việc bạn hiểu test để
làm gì, tốn gì, và khi nào không đáng.

## Bản đồ nhanh

**Chiến lược test**
- [ ] Test pyramid vs testing trophy; vì sao tỉ lệ khác nhau
- [ ] Unit, integration, e2e: mỗi loại kiểm tra cái gì
- [ ] 🟡 Contract test giữa các service (consumer-driven)
- [ ] Smoke test, regression test, 🟡 acceptance test
- [ ] Test những gì: logic nghiệp vụ, edge case, lỗi đã từng xảy ra

**Viết test tốt**
- [ ] Test double: dummy, stub, fake, spy, mock
- [ ] ⚠️ Over-mocking: test kiểm tra lại cách code được viết
- [ ] Test hành vi, không test implementation
- [ ] Cấu trúc Arrange–Act–Assert / Given–When–Then
- [ ] 🟡 Test data: fixture, factory, builder
- [ ] ⚠️ Test isolation: DB riêng, transaction rollback, không nối DB dev/staging dùng chung
- [ ] 🟡 Testcontainers
- [ ] ⚠️ Flaky test: nguyên nhân và cách xử lý

**Test những thứ khó**
- [ ] Thời gian: inject clock
- [ ] Code gọi API ngoài: interface + fake, HTTP stub, sandbox
- [ ] 🟡 Queue/async: test handler riêng, test việc dispatch riêng
- [ ] 🔴 Concurrency: race detector, stress test
- [ ] 🟡 Migration: chạy lên/xuống trên DB thật, dữ liệu có sẵn

**Phương pháp và đo lường**
- [ ] 🟡 TDD: red, green, refactor; ưu nhược
- [ ] 🟡 BDD: Given–When–Then, ngôn ngữ chung với business
- [ ] 🔴 Property-based testing, fuzzing
- [ ] 🔴 Mutation testing
- [ ] Coverage và ⚠️ giới hạn của nó
- [ ] Test trong CI: chạy trước khi merge, nhanh, song song

**Chất lượng code**
- [ ] Code review: review cái gì, cách góp ý, kích thước PR
- [ ] 🟡 Static analysis: PHPStan/Psalm, SpotBugs/SonarQube, go vet/staticcheck/golangci-lint
- [ ] Linter và formatter; chạy tự động, không tranh cãi style trong review
- [ ] 🟡 Tech debt: phân loại, đo, thuyết phục đầu tư trả nợ
- [ ] 🟡 Documentation: README, ADR, runbook, comment "vì sao"
- [ ] Definition of Done

**Git và làm việc nhóm**
- [ ] merge, rebase, squash
- [ ] cherry-pick, revert vs reset, 🟡 reflog
- [ ] 🟡 `git bisect`
- [ ] Giải quyết conflict
- [ ] Git flow vs trunk-based development
- [ ] Commit message: Conventional Commits
- [ ] PR nhỏ; 🟡 feature flag thay cho branch sống lâu
- [ ] Agile/Scrum cơ bản: sprint, ước lượng, retrospective

## Chi tiết

### Chiến lược test

- [ ] **Test pyramid** (nhiều unit, ít integration hơn, ít e2e nhất)
  - Lý do: unit test nhanh, rẻ, chỉ ra đúng chỗ hỏng; e2e chậm, dễ flaky, khi fail khó biết vì sao
  - Giả định ngầm: logic nằm chủ yếu trong code thuần. Đúng với domain phức tạp (tính giá,
    tính lương, rule engine)
- [ ] 🟡 **Testing trophy** (static → unit → integration là phần lớn nhất → e2e)
  - Lập luận: nhiều backend CRUD có ít logic thuần, bug nằm ở chỗ nối: query SQL, mapping,
    validation, serialization. Unit test với DB bị mock bỏ sót đúng những bug đó
  - Integration test ngày nay rẻ hơn trước nhờ container và DB chạy nhanh
  - Kết luận senior: **tỉ lệ phụ thuộc vào chỗ rủi ro nằm ở đâu**, không có hình dạng đúng
    cho mọi dự án

  ```
  Pyramid            Trophy
     /e2e\            [ e2e ]
    /integ.\       [ integration ]   ← phần lớn nhất
   /  unit  \         [ unit ]
                     [ static ]      ← type check, linter
  ```

- [ ] **Các loại test**

  | Loại | Kiểm tra | Tốc độ | Ghi chú |
  |---|---|---|---|
  | Unit | một hàm/class, phụ thuộc thay bằng double | ms | "unit" là một hành vi, không nhất thiết là một class |
  | Integration | code + thành phần thật (DB, cache, queue) | giây | bắt bug SQL, mapping, transaction |
  | E2E | cả hệ thống từ API/UI | chậm | chỉ cho vài luồng quan trọng nhất (đăng ký, thanh toán) |
  | Contract | thoả thuận request/response giữa hai service | nhanh | thay cho e2e xuyên nhiều service |
  | Smoke | hệ thống sống và luồng chính chạy được | nhanh | chạy ngay sau deploy |
  | Regression | lỗi cũ không quay lại | tuỳ | mỗi bug fix kèm một test tái hiện bug |
  | Acceptance | đúng yêu cầu nghiệp vụ | tuỳ | thường viết theo Given–When–Then |

- [ ] 🟡 **Contract test**
  - Consumer ghi lại kỳ vọng (endpoint, field cần dùng), provider chạy kiểm tra kỳ vọng đó
    trong CI của mình. Công cụ hay gặp: Pact, Spring Cloud Contract
  - Giải quyết: provider đổi tên field làm consumer vỡ mà không ai biết cho tới production
  - ⚠️ Contract test không kiểm tra logic nghiệp vụ của provider, chỉ kiểm tra hình dạng giao tiếp
  - Liên quan: versioning API ở [09-api-design.md](09-api-design.md)
- [ ] **Test cái gì trước** khi thời gian có hạn
  - Chỗ mất tiền hoặc mất dữ liệu: thanh toán, tính tiền, phân quyền, migration
  - Logic nhiều nhánh, edge case: rỗng, biên, trùng, số âm, timezone
  - Chỗ từng có bug (regression)
  - ⚠️ Không đáng: getter/setter, code framework đã test, code sắp xoá

### Viết test tốt

- [ ] **Test double** (thuật ngữ của Gerard Meszaros)

  | Loại | Làm gì | Ví dụ |
  |---|---|---|
  | Dummy | chỉ để đủ tham số, không dùng | logger truyền vào nhưng không kiểm tra |
  | Stub | trả giá trị định sẵn | `rateProvider` luôn trả 25000 |
  | Fake | bản cài thật nhưng đơn giản | repository lưu trong map, SMTP ghi ra mảng |
  | Spy | ghi lại cách được gọi để assert sau | đếm số email đã gửi |
  | Mock | được lập trình kỳ vọng trước, fail nếu gọi sai | "phải gọi `charge()` đúng 1 lần với 100000" |

  - Trong đời thường, người ta gọi chung là "mock". Nói được sự khác nhau là điểm cộng,
    nhưng quan trọng hơn là biết **stub cho input, mock/spy cho output có side effect**
- [ ] ⚠️ **Over-mocking**
  - Dấu hiệu: test lặp lại từng dòng implementation (`expects(find)`, `expects(save)`...);
    refactor không đổi hành vi mà hàng chục test đỏ
  - Hậu quả: test chắc chắn pass khi code sai, vì mock trả đúng thứ ta nghĩ là đúng.
    Ví dụ mock repository nên không bao giờ phát hiện query SQL sai
  - Quy tắc thực dụng: mock ở **biên hệ thống** (API ngoài, email, clock, random), dùng thật
    hoặc fake cho những gì mình sở hữu. "Don't mock what you don't own": bọc thư viện
    ngoài bằng interface của mình rồi mock interface đó
- [ ] **Test hành vi, không test implementation**
  - Assert trên kết quả quan sát được: giá trị trả về, trạng thái DB, event được phát, response
  - Không assert trên method private, thứ tự gọi nội bộ, số lần query (trừ khi đó là yêu cầu,
    ví dụ chống N+1)
  - Tên test mô tả hành vi: `refund_fails_when_order_already_refunded`, không phải `testRefund2`
- [ ] **Cấu trúc test**: Arrange–Act–Assert. Một test một hành vi; nhiều assert được nếu
      cùng một hành vi
- [ ] 🟡 **Test data**
  - Fixture tĩnh (file SQL/JSON): dễ đọc nhưng dễ phình và phụ thuộc lẫn nhau giữa test
  - Factory/builder: tạo object hợp lệ mặc định, test chỉ ghi đè field nó quan tâm.
    Laravel model factory, Java builder/Object Mother, Go hàm `newTestOrder(opts...)`
  - ⚠️ Test phụ thuộc dữ liệu do test khác tạo thì chạy riêng lẻ sẽ fail
  - ⚠️ Không dùng bản sao dữ liệu production chưa ẩn danh làm test data (PII, xem
    [10-security.md](10-security.md))
- [ ] ⚠️ **Test isolation**
  - Mỗi test tự chuẩn bị và tự dọn trạng thái; chạy riêng hay chạy theo thứ tự nào cũng pass
  - Cách phổ biến: DB riêng cho test (container, schema riêng, SQLite in-memory nếu chấp nhận
    khác biệt dialect), hoặc bọc mỗi test trong transaction rồi rollback
  - ⚠️ Transaction rollback không che được: code tự mở kết nối khác, job chạy ở worker khác,
    DDL tự commit (MySQL), dữ liệu ghi vào Redis/queue/file
  - ⚠️ **Không bao giờ để test nối vào DB dev/staging dùng chung.** Test hợp lệ thường có
    `TRUNCATE`/`DELETE` để dọn bảng; bootstrap test có thể gọi lệnh cài đặt ngầm chạy
    migration. Trỏ nhầm DB là xoá dữ liệu của cả team và chạy migration chưa review lên DB
    chung. Phòng: cấu hình DB test tường minh trong file config test, và một guard trong
    setUp dừng ngay nếu tên DB không phải DB test
  - Đối chiếu: Laravel `RefreshDatabase`/`DatabaseTransactions`; Spring `@Transactional` trên
    test mặc định rollback; Go tự viết helper mở transaction và `t.Cleanup(rollback)`
- [ ] 🟡 **Testcontainers**
  - Khởi động container DB/Redis/Kafka thật cho test, bỏ đi khi xong. Có thư viện cho Java,
    Go và nhiều ngôn ngữ khác
  - Lợi: test chạy trên đúng engine và phiên bản production, bắt được bug dialect
  - Giá: chậm hơn in-memory, cần Docker trong CI. Giảm bằng cách dùng chung một container
    cho cả suite và cô lập bằng transaction hoặc schema riêng
- [ ] ⚠️ **Flaky test** (lúc pass lúc fail mà code không đổi)

  | Nguyên nhân | Ví dụ | Cách sửa |
  |---|---|---|
  | Thời gian | test chạy lúc 23:59, `now()` sang ngày mới; timezone máy CI khác | inject clock, cố định timezone |
  | Thứ tự | test B dùng dữ liệu test A để lại | cô lập dữ liệu, chạy random order để phát hiện |
  | Mạng | gọi API thật, DNS chậm | stub ở biên, không gọi mạng thật trong unit/integration |
  | Concurrency/async | `sleep(100ms)` rồi assert | chờ theo điều kiện có timeout (polling), không sleep cố định |
  | Thứ tự không xác định | duyệt map, `SELECT` không `ORDER BY` | sort trước khi so sánh |
  | Tài nguyên chung | port cố định, file tạm cùng tên | port ngẫu nhiên, thư mục tạm riêng |

  - ⚠️ Flaky test nguy hiểm hơn không có test: team học cách bấm "re-run" và bỏ qua đỏ thật
  - Xử lý vận hành: theo dõi tỉ lệ flaky, cách ly (quarantine) có hạn chót sửa, không để
    quarantine thành nghĩa địa

### Test những thứ khó

- [ ] **Thời gian**
  - Không gọi `now()` trực tiếp trong logic; nhận clock qua constructor
  - Đối chiếu: Java `java.time.Clock` (`Clock.fixed(...)` trong test); PHP PSR-20
    `ClockInterface`, Carbon `setTestNow()`; Go truyền `func() time.Time` hoặc interface `Clock`
  - Test các ca: cuối tháng, năm nhuận, đổi timezone, token hết hạn đúng biên. Xem
    [22-practical-data.md](22-practical-data.md)

  ```go
  type Service struct{ now func() time.Time }

  func (s *Service) IsExpired(t Token) bool { return s.now().After(t.ExpiresAt) }

  // test: svc := &Service{now: func() time.Time { return fixed }}
  ```

- [ ] **Code gọi API ngoài** (câu hỏi kinh điển: test hàm gọi API thanh toán thế nào?)
  - Tách interface `PaymentGateway`; logic nghiệp vụ test với fake/stub: thành công, bị từ
    chối, timeout, lỗi 5xx, response sai định dạng, gọi trùng (idempotency)
  - Adapter HTTP test riêng với HTTP stub (WireMock, `httptest.Server` của Go, `Http::fake()`
    của Laravel) để kiểm tra request đúng định dạng, header, xử lý mã lỗi
  - Contract/sandbox của provider: chạy ít, ngoài luồng CI chính, vì chậm và không ổn định
  - ⚠️ Không để unit test gọi sandbox thật: chậm, flaky, và có thể bị rate limit
- [ ] 🟡 **Queue/async**
  - Tách hai câu hỏi: "có dispatch đúng job/event không" (fake queue, assert đã push) và
    "handler xử lý đúng không" (gọi handler trực tiếp, đồng bộ)
  - Test handler idempotent: gọi hai lần cùng message, kết quả như một lần
  - Integration với broker thật khi cần kiểm tra retry, DLQ, thứ tự. Xem [12-messaging.md](12-messaging.md)
  - ⚠️ Chờ bằng `sleep` là nguồn flaky số một; dùng polling có timeout
- [ ] 🔴 **Concurrency**
  - Go: `go test -race` bắt data race khi chúng thực sự xảy ra trong lần chạy; ⚠️ không
    chứng minh được là không có race
  - Stress test: nhiều goroutine/thread cùng rút tiền một tài khoản, assert số dư không âm
    và tổng khớp
  - Test lock ở DB: hai transaction thật, kiểm tra một bên bị chặn hoặc bị lỗi đúng như thiết kế
  - Xem [13-concurrency.md](13-concurrency.md)
- [ ] 🟡 **Migration**
  - Chạy migration trên DB cùng engine và phiên bản production, có dữ liệu mẫu (cột NOT NULL
    mới trên bảng đã có dữ liệu là ca hay vỡ)
  - Kiểm tra rollback nếu có down migration; kiểm tra code cũ vẫn chạy với schema mới
    (expand–contract). Xem [03-database-sql.md](03-database-sql.md)
  - 🔴 Bảng lớn: thử trên bản sao kích thước thật để đo thời gian lock

### Phương pháp và đo lường

- [ ] 🟡 **TDD**: viết test fail (red) → code tối thiểu cho pass (green) → refactor
  - Lợi: buộc nghĩ về interface và hành vi trước; code dễ test vì được thiết kế để test;
    có lưới an toàn khi refactor
  - Nhược: chậm lúc đầu; khó khi yêu cầu còn mơ hồ hoặc đang thử nghiệm (spike); dễ sinh
    over-mocking nếu làm máy móc
  - Câu trả lời trung thực được đánh giá cao hơn "tôi luôn TDD": nói rõ khi nào mình dùng
- [ ] 🟡 **BDD**: mô tả hành vi bằng Given–When–Then, viết chung với PO/QA. Công cụ:
      Cucumber, Behat. Giá trị chính là cuộc trao đổi, không phải công cụ
- [ ] 🔴 **Property-based testing**
  - Thay vì vài ví dụ tay, khai báo **tính chất** luôn đúng; thư viện sinh hàng trăm input
    ngẫu nhiên và thu nhỏ (shrink) input làm fail về ca nhỏ nhất
  - Tính chất hay dùng: `decode(encode(x)) == x`; sort xong thì có thứ tự và cùng phần tử;
    tổng tiền chia phần bằng tổng ban đầu; thao tác idempotent
  - Công cụ ví dụ: jqwik (Java), `rapid` (Go), Eris (PHP). Go có sẵn fuzzing trong `go test`
    (`func FuzzXxx(f *testing.F)`) từ Go 1.18
- [ ] 🔴 **Mutation testing**
  - Công cụ sửa code (đổi `>` thành `>=`, bỏ một dòng, đổi `true` thành `false`) rồi chạy
    test. Test vẫn pass nghĩa là mutant "sống": test không kiểm tra hành vi đó
  - Đo chất lượng test tốt hơn coverage. Công cụ: PIT (Java), Infection (PHP); Go có công cụ
    nhưng ít phổ biến
  - Giá: rất chậm; chạy trên module quan trọng hoặc chỉ trên phần code thay đổi
- [ ] **Coverage**
  - Line coverage < branch coverage về độ khắt khe
  - ⚠️ Coverage cao không có nghĩa test tốt: test chạy qua code mà không assert vẫn tính là
    covered. Coverage thấp thì chắc chắn có chỗ chưa test
  - Dùng coverage để **tìm chỗ chưa test**, không dùng làm KPI. Đặt ngưỡng cứng thường sinh
    test rác để đủ số
  - Tốt hơn: không cho coverage của phần code mới/thay đổi giảm
- [ ] **Test trong CI**
  - Mọi PR chạy lint, static analysis, test trước khi được merge (branch protection)
  - Giữ pipeline nhanh: chạy song song, cache dependency, tách suite chậm; pipeline chậm thì
    người ta tìm cách bỏ qua
  - DB/service phụ trong CI là container riêng, dùng xong bỏ. Xem [19-devops-cloud.md](19-devops-cloud.md)
  - ⚠️ Test pass ở máy dev nhưng fail ở CI: khác timezone, locale, thứ tự file, phiên bản

### Chất lượng code

- [ ] **Code review: review cái gì** (theo thứ tự quan trọng)
  1. Đúng yêu cầu chưa, có hiểu đúng bài toán không
  2. Correctness: edge case, xử lý lỗi, concurrency, transaction, idempotency
  3. Bảo mật: input validation, phân quyền, SQL injection, log lộ dữ liệu nhạy cảm
  4. Vận hành: migration an toàn không, có log/metric không, rollback được không
  5. Thiết kế: đặt đúng chỗ, abstraction có cần không, có trùng thứ đã có không
  6. Test: có test cho hành vi mới và cho bug vừa sửa không
  7. Đọc hiểu: tên, cấu trúc. Style để formatter lo
- [ ] **Cách góp ý**
  - Góp ý về code, không về người; hỏi thay vì ra lệnh ("Nếu list rỗng thì sao?")
  - Ghi rõ mức độ: blocking hay `nit:`/gợi ý; khen chỗ tốt
  - Giải thích vì sao, kèm ví dụ hoặc link
  - Bất đồng kéo dài quá hai vòng comment thì nói chuyện trực tiếp
  - Khi bị review: không phòng thủ, trả lời mọi comment, cảm ơn phát hiện lỗi
- [ ] **Kích thước PR**
  - PR nhỏ được review kỹ; PR vài nghìn dòng thường nhận "LGTM" vì không ai đọc nổi
  - Tách: refactor riêng, đổi hành vi riêng; migration riêng; feature flag để merge dần
  - Người viết tự review diff trước, mô tả PR nói rõ vì sao, cách test, rủi ro
- [ ] 🟡 **Static analysis**

  | Ngôn ngữ | Công cụ | Bắt được gì |
  |---|---|---|
  | PHP | PHPStan, Psalm (có level/độ nghiêm) | gọi method không tồn tại, sai kiểu, null chưa kiểm tra |
  | Java | SpotBugs, Error Prone, PMD, SonarQube | null dereference, resource leak, equals/hashCode sai |
  | Go | `go vet`, staticcheck, golangci-lint (gom nhiều linter) | format string sai, copy lock, lỗi bị bỏ qua |

  - Áp vào codebase cũ: bắt đầu level thấp hoặc dùng **baseline** (ghi nhận lỗi cũ, chỉ chặn
    lỗi mới), rồi nâng dần
  - PHP đặc biệt hưởng lợi vì kiểu chỉ được kiểm tra lúc chạy; static analysis gần như là
    compiler thứ hai
- [ ] **Linter và formatter**: gofmt/goimports, PHP-CS-Fixer/Laravel Pint, google-java-format/
      Spotless. Chạy trong pre-commit hoặc CI để review không phải bàn về dấu cách
- [ ] 🟡 **Tech debt**
  - Phân loại theo góc phần tư của Martin Fowler: cố ý hay vô tình × thận trọng hay liều
    ("ship trước, trả nợ sau, biết rõ hậu quả" là cố ý–thận trọng)
  - Loại cụ thể: code, kiến trúc, test, dependency lỗi thời, hạ tầng, tài liệu
  - Chỉ nợ gây đau mới cần trả: code hay sửa và hay có bug. Code xấu nhưng không ai đụng thì
    có thể để yên
  - Thuyết phục đầu tư: nói bằng ngôn ngữ business. Số liệu: thời gian làm một tính năng
    tương tự tăng từ X lên Y, số incident liên quan, thời gian onboard, CVE trong dependency
  - Cách trả: gắn vào tính năng đang làm (boy scout rule), dành tỉ lệ cố định mỗi sprint,
    hoặc dự án riêng có mục tiêu đo được. ⚠️ "Viết lại toàn bộ" hiếm khi là câu trả lời đúng
- [ ] 🟡 **Documentation**
  - README: chạy dự án thế nào, cấu hình gì
  - ADR (Architecture Decision Record): quyết định gì, vì sao, đã cân nhắc phương án nào.
    Giá trị nhất sau một năm khi không ai nhớ lý do
  - Runbook cho vận hành: alert này nghĩa là gì, làm gì
  - Comment giải thích **vì sao**, không lặp lại code làm gì
- [ ] **Definition of Done**: code merge, test, review, tài liệu cập nhật, deploy được,
      có monitoring, feature flag bật/tắt được, PO chấp nhận. Team thống nhất trước để
      "xong" không có nghĩa khác nhau với mỗi người

### Git và làm việc nhóm

- [ ] **merge, rebase, squash**

  ```
  main:    A---B---C              merge:   A---B---C---M      (M có hai cha)
  feature:      \--D---E                         \--D---E-/
                                  rebase:  A---B---C---D'---E' (commit mới, hash mới)
                                  squash:  A---B---C---S      (D+E gộp thành S)
  ```

  - Merge giữ nguyên lịch sử thật; rebase cho lịch sử thẳng; squash gọn nhưng mất commit nhỏ
  - ⚠️ Không rebase nhánh đã push mà người khác đang dùng: rebase viết lại hash, người khác
    phải xử lý lịch sử lệch. Nếu phải force push nhánh của mình thì dùng
    `--force-with-lease` thay vì `--force`
- [ ] **cherry-pick**: chép một commit sang nhánh khác (ví dụ đưa hotfix sang nhánh release).
      ⚠️ Tạo commit mới với hash khác; cherry-pick nhiều dễ quên đồng bộ ngược
- [ ] **revert vs reset**
  - `revert` tạo commit mới đảo ngược thay đổi, không sửa lịch sử: dùng trên nhánh chung
  - `reset` di chuyển nhánh về commit cũ (`--soft` giữ thay đổi đã stage, `--mixed` giữ ở
    working tree, `--hard` bỏ hết): chỉ dùng trên nhánh local chưa chia sẻ
  - ⚠️ Revert một merge commit cần `-m 1` để chỉ định cha chính; merge lại nhánh đó sau này
    sẽ không mang lại các thay đổi đã revert, trừ khi revert cái revert
  - 🟡 `git reflog`: tìm lại commit sau khi reset/rebase nhầm
- [ ] 🟡 **`git bisect`**: tìm nhị phân commit gây lỗi giữa một commit tốt và một commit xấu
  - `git bisect start`, `git bisect bad`, `git bisect good <hash>`, lặp lại đánh dấu
  - `git bisect run <lệnh>` tự động hoá nếu có lệnh trả exit code 0/khác 0
  - n commit cần khoảng log₂(n) bước; hiệu quả khi commit nhỏ và mỗi commit build được
- [ ] **Conflict**: hiểu cả hai phía muốn gì trước khi chọn; hỏi tác giả phía kia khi không
      chắc; chạy lại test sau khi giải. 🟡 `git rerere` nhớ cách đã giải cho lần sau
- [ ] **Branching strategy**

  | | Git flow | Trunk-based |
  |---|---|---|
  | Nhánh | main, develop, feature, release, hotfix | main + nhánh ngắn (vài giờ đến vài ngày) |
  | Hợp với | release theo đợt, nhiều phiên bản song song (app mobile, phần mềm đóng gói) | deploy liên tục, SaaS |
  | Rủi ro | branch sống lâu, merge đau, tích hợp muộn | cần CI tốt, test tốt, feature flag |

- [ ] **Commit message**: Conventional Commits `type(scope): mô tả`, ví dụ
      `feat(order): add partial refund`, `fix: handle empty cart`. `!` hoặc footer
      `BREAKING CHANGE:` cho thay đổi phá tương thích. Lợi: đọc lịch sử nhanh, sinh changelog
      và version tự động. Subject ở thể mệnh lệnh, body giải thích vì sao
- [ ] 🟡 **Feature flag thay cho branch dài**
  - Merge code chưa xong vào main nhưng tắt sau flag: tích hợp sớm, conflict nhỏ
  - Tách deploy khỏi release; bật dần theo % user; tắt nhanh khi có sự cố
  - ⚠️ Flag là nợ: phải xoá sau khi rollout xong; test cả hai trạng thái flag
- [ ] **Agile/Scrum cơ bản**: sprint, planning, daily, review, retrospective; ước lượng bằng
      story point hoặc thời gian. Xem thêm ước lượng ở [24-senior-leadership.md](24-senior-leadership.md)

## Senior trả lời khác gì

| Câu hỏi | Junior/mid | Senior |
|---|---|---|
| Bạn viết loại test nào nhiều nhất? | "Unit test, theo test pyramid." | "Tuỳ chỗ rủi ro. Service tính giá thì unit test dày. Service CRUD thì integration test với DB thật qua container, vì bug nằm ở query và mapping. E2E chỉ cho vài luồng tiền." |
| Coverage bao nhiêu là đủ? | "80%." | "Không đặt một con số làm KPI. Tôi dùng coverage để tìm chỗ chưa test, chặn coverage của code mới không giảm, và thử mutation testing cho module tiền." |
| Test bị flaky thì làm gì? | "Chạy lại." | "Xem nguyên nhân thuộc nhóm nào: thời gian, thứ tự, mạng, async. Quarantine có hạn sửa, đo tỉ lệ flaky, vì team quen bấm re-run thì sẽ bỏ qua cả lỗi thật." |
| Làm sao thuyết phục sếp cho thời gian trả tech debt? | "Code xấu quá, cần refactor." | "Đưa số: tính năng tương tự từng mất 2 ngày giờ mất 2 tuần, 3 incident quý này từ module này. Đề xuất gắn việc trả nợ vào tính năng sắp làm, có mục tiêu đo được." |
| Merge hay rebase? | "Rebase cho đẹp." | "Rebase nhánh cá nhân trước khi mở PR cho lịch sử sạch; squash merge vào main nếu team muốn một commit mỗi PR; không bao giờ viết lại lịch sử nhánh chung. Quan trọng hơn là cả team thống nhất." |

## Tình huống

1. **Test suite mất 40 phút, dev bắt đầu push không chờ CI.**
   - Gợi ý: đo test nào chậm nhất; chạy song song; dùng chung container DB; tách unit và
     integration thành job riêng; đẩy e2e sang sau merge hoặc nightly; cache dependency.
2. **Một dev báo chạy test xong thì bảng trên DB dev của cả team trống trơn.**
   - Gợi ý: test đã nối DB chung; dừng chạy test, khôi phục từ backup; cấu hình DB test
     tường minh; guard trong setUp kiểm tra tên DB; tách credential để user của môi trường
     test không có quyền trên DB dev; rà các lệnh bootstrap có chạy migration ngầm không.
3. **Nhận codebase cũ không có test, cần sửa module thanh toán.**
   - Gợi ý: viết characterization test ghi lại hành vi hiện tại ở mức API/integration trước;
     tìm seam để tách phụ thuộc; sửa nhỏ, mỗi bước có test; không refactor lớn cùng lúc.
4. **PR 3000 dòng, deadline mai, được nhờ review.**
   - Gợi ý: đề nghị tách; nếu không kịp thì ưu tiên review phần rủi ro (migration, tiền,
     phân quyền), ghi rõ phần chưa review, yêu cầu feature flag để tắt được.
5. **Bug production ở hàm tính ngày hết hạn, chỉ xảy ra cuối tháng.**
   - Gợi ý: viết regression test tái hiện với clock cố định ở ngày 31; kiểm tra code gọi
     `now()` trực tiếp; thêm các ca tháng 2, năm nhuận, timezone.
6. **Tìm commit gây chậm API trong 200 commit gần nhất.**
   - Gợi ý: `git bisect` với script đo thời gian trả exit code; khoảng 8 bước.
7. **Team tranh cãi git flow hay trunk-based.**
   - Gợi ý: hỏi tần suất release, có nhiều phiên bản song song không, chất lượng CI, có
     feature flag chưa. Trunk-based cần nền tảng test và flag trước.

## ❓ Câu hỏi hay gặp

🟢
- Unit test và integration test khác nhau thế nào? Bạn viết loại nào nhiều hơn?
- Mock và stub khác nhau thế nào?
- `merge` và `rebase` khác nhau thế nào? Khi nào không nên rebase?
- `revert` và `reset` khác nhau thế nào?
- Khi review code bạn nhìn vào đâu?

🟡
- Bạn test một hàm gọi API thanh toán bên ngoài thế nào?
- Test một hàm phụ thuộc thời gian hiện tại thế nào?
- Vì sao test không được nối vào DB dev dùng chung? Cô lập DB trong test bằng cách nào?
- Nguyên nhân phổ biến của flaky test?
- Coverage 90% có nghĩa là test tốt không?
- TDD có ưu nhược gì? Bạn có dùng không?
- Git flow và trunk-based khác nhau thế nào?
- Contract test giải quyết vấn đề gì?

🔴
- Test pyramid hay testing trophy, chọn thế nào cho một service cụ thể?
- Mutation testing là gì, vì sao tốt hơn coverage?
- Bạn đưa static analysis vào một codebase cũ có hàng nghìn lỗi thế nào?
- Làm sao thuyết phục business đầu tư trả tech debt?
- Test concurrency (ví dụ chống rút tiền hai lần) thế nào?

## Bài tập tự làm

1. Chọn một hàm trong dự án của bạn gọi `now()` trực tiếp. Mô tả cách đổi nó sang inject
   clock và liệt kê 5 ca thời gian cần test.
2. Với một service gửi email khi đơn hàng được thanh toán, liệt kê: phần nào dùng fake,
   phần nào dùng DB thật, phần nào không cần test. Giải thích vì sao.
3. Viết ba tính chất (property) cho hàm chia một khoản tiền thành n phần bằng nhau có làm tròn.
4. Viết một checklist review PR 10 dòng cho team của bạn, sắp theo mức quan trọng.
5. Mô tả cách bạn sẽ đưa PHPStan (hoặc staticcheck/SpotBugs) vào một dự án chưa từng dùng,
   gồm lộ trình nâng level.

> Nộp bài vào đây để được review.
